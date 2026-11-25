"""Local operator entry points for one immutable campaign plan and original start."""

import asyncio
from pathlib import Path
from threading import Event
import time
from uuid import uuid4

from ergora.campaigns.records import (
    FIXED_TASK_UPDATE_PREFIX, PENDING_JOB_STATES, WORKFLOW_TYPE, CampaignFiles, attempt_document, check_intent,
    check_record_name, fixed_tasks, identity,
    original_check_evidence, read_plan, result_document, sha256, stop_intent, update_attempt, uuid_text, worker_queue,
    workflow_id,
)
from ergora.configuration import projects, registrations
from ergora.storage.state import State, file_lock


def _temporal():
    try:
        from ergora.campaigns import workflow
    except ModuleNotFoundError as error:
        if error.name != 'temporalio':
            raise
        raise ValueError('Online campaign operations require the existing ergora[temporal] extra') from error
    return workflow


def _selection(state, project, revision):
    if project['revision'] != revision:
        raise ValueError('Project revision changed; use the original approved revision before dispatch')
    config = projects.effective_configuration(project)
    scheduler = config['layers']['scheduler']
    if scheduler['source']['kind'] != 'project' or scheduler['binding']['tool'] != 'temporal':
        raise ValueError('Campaign creation requires an explicitly bound Temporal scheduler')
    if not scheduler['validation']['valid']:
        raise ValueError(scheduler['validation']['error'])
    return {'registration': registrations.publication_identity(state, project),
            'configuration_sha256': config['sha256'], 'scheduler': scheduler['binding']}


def _opening(files, revision, plan, plan_sha, selection):
    creation_id = str(uuid4())
    return {'schema_version': 1, 'mode': 'record_only', 'control_home': str(files.home), 'project': files.project,
            'project_revision': revision, 'campaign': files.campaign, 'actor': files.actor, 'plan': plan,
            'plan_sha256': plan_sha, 'plan_document_sha256': identity(plan), 'creation_id': creation_id,
            'task_queue': worker_queue(files.project, files.campaign, selection['scheduler'], creation_id),
            'workflow_id': workflow_id(files.project, files.campaign), 'workflow_type': WORKFLOW_TYPE, **selection}


def _verify_registration(state, opening):
    selected = opening['registration']
    original = registrations.published_project(state.root, opening['project'], selected['operation_id'],
                                               selected['intent_sha256'])
    if original['registration']['sha256'] != selected['sha256'] or original['revision'] > opening['project_revision']:
        raise ValueError('Campaign original registration identity differs')


def _future(opening):
    remaining = opening['plan']['limits']['expires_at'] - time.time()
    if remaining <= 0:
        raise ValueError('Original campaign plan expiry has passed')
    return remaining


def _snapshot(files, opening, attempt, result):
    state = {'schema_version': 1, 'project': files.project, 'campaign': files.campaign,
             'mode': 'record_only', 'actor_assurance': files.actor['assurance'], 'execution_authorized': False,
             'remote_status': 'not_requested', 'workflow_state_status': 'not_observed', 'run_id': None}
    if opening is None:
        return {**state, 'status': 'not_recorded'}
    outcome = 'recorded' if result else 'unknown' if attempt else 'prepared'
    return {**state, 'status': outcome, 'project_revision': opening['project_revision'],
            'operator_euid': opening['actor']['euid'], 'registration_sha256': opening['registration']['sha256'],
            'configuration_sha256': opening['configuration_sha256'], 'plan': opening['plan'],
            'plan_sha256': opening['plan_sha256'], 'plan_document_sha256': opening['plan_document_sha256'],
            'opening_sha256': identity(opening), 'attempt_sha256': identity(attempt) if attempt else None,
            'result_saved': result is not None, 'scheduler': opening['scheduler'], 'task_queue': opening['task_queue'],
            'workflow_id': opening['workflow_id'], 'run_id': result['run_id'] if result else None}


def _stop_snapshot(records):
    intent, attempt, result = records
    phase = 'recorded' if result else 'unknown' if attempt else 'prepared' if intent else 'not_recorded'
    return {'status': phase, 'result_saved': result is not None, 'remote_status': 'not_requested', 'retryable': False,
            'update_id': attempt['update_id'] if attempt else None, 'receipt': result['receipt'] if result else None}


async def _observe(runtime, output, client, handle, description, opening, stop_records, read_state):
    observed = {**output, 'status': 'observed', 'run_id': description.run_id, 'remote_status': 'original_observed',
                'temporal_status': description.status.name}
    stop_receipt = None
    if stop_records is not None:
        intent, attempt, _ = stop_records
        if attempt is not None:
            command = {'intent': intent, 'attempt': attempt}
            try:
                async with asyncio.timeout(runtime.RPC_SECONDS):
                    stop_receipt = await runtime.read_stop(client, handle, command)
            except (TimeoutError, runtime.RPCError):
                observed['stop'] = {**output['stop'], 'remote_status': 'unavailable'}
            else:
                if stop_receipt is None:
                    observed['stop'] = {**output['stop'], 'remote_status': 'not_found'}
                elif output['stop']['receipt'] is not None and output['stop']['receipt'] != stop_receipt:
                    raise ValueError('Campaign stop record and original History differ')
                else:
                    observed['stop'] = {**output['stop'], 'status': 'observed', 'remote_status': 'observed',
                                        'receipt': stop_receipt}
    if read_state:
        try:
            async with asyncio.timeout(runtime.RPC_SECONDS):
                observed.update(await runtime.runtime_status(handle, description, opening, stop_receipt,
                                                           start_attempt_sha256=output['attempt_sha256']))
                saved_stop = observed.get('stop', {}).get('receipt')
                if saved_stop is not None and saved_stop['decision'] == 'accepted':
                    for task in observed.get('tasks', {}).values():
                        task['eligible'] = False
        except (TimeoutError, runtime.RPCError):
            observed['workflow_state_status'] = 'unavailable'
    return observed


async def _read_original(runtime, output, opening, attempt, run_id, *, client=None, read_state=False, stop_records=None):
    try:
        async with asyncio.timeout(runtime.RPC_SECONDS):
            if client is None:
                client = await runtime.connect(opening)
            handle, description = await runtime.original(client, opening, attempt, run_id)
    except runtime.RPCError as error:
        if error.status == runtime.RPCStatusCode.NOT_FOUND:
            return {**output, 'remote_status': 'original_not_found'}
        return {**output, 'remote_status': 'unavailable', 'remote_error': error.status.name}
    except (TimeoutError, ConnectionError):
        return {**output, 'remote_status': 'unavailable', 'remote_error': 'connection_or_lookup'}
    return await _observe(runtime, output, client, handle, description, opening, stop_records, read_state)


async def status(state: State, project: str, campaign: str, *, online: bool = False) -> dict:
    """Read the saved evidence, optionally observing the verified original Workflow on the saved route."""
    files = CampaignFiles(state.root, project, campaign)
    opening, attempt, result = files.load()
    stop_records = (None, None, None)
    if opening is not None:
        _verify_registration(state, opening)
    if attempt is not None:
        # A concurrent writer may start and stop after a prepared-only snapshot.
        stop_records = files.load_stop(opening, attempt, result)
    output = {**_snapshot(files, opening, attempt, result), 'stop': _stop_snapshot(stop_records)}
    if online and attempt is not None:
        run_id = stop_records[0]['run_id'] if stop_records[0] is not None else output['run_id']
        output = await _read_original(_temporal(), output, opening, attempt, run_id, read_state=True,
                                      stop_records=stop_records)
        for task in output.get('tasks', {}).values():
            if task['receipt'] is None:
                command = files.load_check(opening, attempt, output['run_id'], task)
                if command is None and task['source'].get('pending') is True and task['waiting_receipt'] is None:
                    command = files.load_check(opening, attempt, output['run_id'], task, waiting=True)
                if command is not None:
                    task.update(eligible=False, attempt_status='unknown', update_id=command['attempt']['update_id'])
    return output


async def create(state: State, project: str, campaign: str, path: Path, revision: int, plan_sha: str,
                 *, confirm: bool) -> dict:
    """Save one original dispatch before its bounded Start RPC; repeats only reconcile it."""
    if confirm is not True or type(revision) is not int or revision < 1 or not sha256(plan_sha):
        raise ValueError('Campaign creation requires --confirm, a positive --revision and a lowercase --plan-sha256')
    files = CampaignFiles(state.root, project, campaign)
    plan = read_plan(path, plan_sha)
    runtime = _temporal()
    opening, _, _ = files.load()
    if opening is None:
        # Reject unsupported or stale authorization before creating the campaign namespace.
        preview = _opening(files, revision, plan, plan_sha, _selection(state, state.project(project), revision))
        _future(preview)
    files.ensure_directory()
    with file_lock(files.lock, blocking=False):
        opening, attempt, result = files.load()
        if opening is None:
            with State(state.root).connect() as db:
                db.execute('BEGIN IMMEDIATE')
                opening = _opening(files, revision, plan, plan_sha, _selection(state, state.project(project), revision))
                _future(opening)
                files.write('start-intent', opening)
        elif (opening['project_revision'] != revision or opening['plan_sha256'] != plan_sha
              or opening['plan_document_sha256'] != identity(plan)):
            raise ValueError('Campaign ID already binds a different original plan or project revision')
        _verify_registration(state, opening)
        output = _snapshot(files, opening, attempt, result)
        client = None
        acknowledged_run = output['run_id']
        attempted_here = attempt is None
        if attempted_here:
            try:
                async with asyncio.timeout(min(runtime.RPC_SECONDS, _future(opening))):
                    client = await runtime.connect(opening)
            except (TimeoutError, ConnectionError, runtime.RPCError):
                return {**output, 'remote_status': 'unavailable', 'remote_error': 'connection_before_attempt'}
            with State(state.root).connect() as db:
                db.execute('BEGIN IMMEDIATE')
                selected = _selection(state, state.project(project), revision)
                if any(opening[key] != value for key, value in selected.items()):
                    raise ValueError('Original project registration or scheduler changed before attempt')
                _future(opening)
                attempt = attempt_document(opening, str(uuid4()))
                files.write('start-attempt', attempt)
            output = _snapshot(files, opening, attempt, None)
            remaining = opening['plan']['limits']['expires_at'] - time.time()
            if remaining <= 0:
                return {**output, 'remote_status': 'unavailable', 'remote_error': 'expiry_after_dispatch_checkpoint'}
            try:
                async with asyncio.timeout(min(runtime.RPC_SECONDS, remaining)):
                    received_run = await runtime.start(client, opening, attempt)
                    if uuid_text(received_run):
                        acknowledged_run = received_run
            except (TimeoutError, ConnectionError, runtime.RPCError):
                # An interrupted or ambiguous Start may already have been accepted. Never resend it.
                pass
        observed = await _read_original(runtime, output, opening, attempt, acknowledged_run, client=client)
        if observed['remote_status'] != 'original_observed':
            return observed
        if result is None:
            files.write('start-result', result_document(opening, attempt, observed['run_id']))
        return {**observed, 'status': 'created' if attempted_here and acknowledged_run else 'observed',
                'result_saved': True}


async def stop(state: State, project: str, campaign: str, *, confirm: bool) -> dict:
    """Request one stop on the original Run. A saved attempt only permits readback."""
    if confirm is not True:
        raise ValueError('Campaign stop requires explicit --confirm')
    files = CampaignFiles(state.root, project, campaign)
    _, start_attempt, _ = files.load()
    if start_attempt is None:
        raise ValueError('Campaign stop requires a saved original start attempt')
    runtime = _temporal()
    files.ensure_directory()
    with file_lock(files.lock, blocking=False):
        opening, start_attempt, start_result = files.load()
        _verify_registration(state, opening)
        records = files.load_stop(opening, start_attempt, start_result)
        intent, attempt, result = records
        output = {**_snapshot(files, opening, start_attempt, start_result), 'stop': _stop_snapshot(records)}
        run_id = intent['run_id'] if intent else output['run_id']
        try:
            async with asyncio.timeout(runtime.RPC_SECONDS):
                client = await runtime.connect(opening)
                handle, description = await runtime.original(client, opening, start_attempt, run_id)
        except runtime.RPCError as error:
            remote_status = 'original_not_found' if error.status == runtime.RPCStatusCode.NOT_FOUND else 'unavailable'
            return {**output, 'remote_status': remote_status, 'remote_error': error.status.name}
        except (TimeoutError, ConnectionError):
            return {**output, 'remote_status': 'unavailable', 'remote_error': 'connection_or_lookup'}
        if attempt is None and description.status == runtime.WorkflowExecutionStatus.RUNNING:
            if not await runtime.stop_supported(handle, opening):
                output['stop'].update(remote_status='worker_unavailable', retryable=True)
                return await _observe(runtime, output, client, handle, description, opening, records, False)
            if intent is None:
                intent = stop_intent(opening, identity(start_attempt), description.run_id)
                files.write('stop-intent', intent)
            attempt = update_attempt(intent, 'ergora-campaign-stop:' + str(uuid4()))
            files.write('stop-attempt', attempt)
            command = {'intent': intent, 'attempt': attempt}
            try:
                async with asyncio.timeout(runtime.RPC_SECONDS):
                    receipt = await runtime.send_stop(client, command)
            except (TimeoutError, ConnectionError, runtime.RPCError):
                receipt = None
            if receipt is not None:
                result = {'receipt': receipt}
                files.write('stop-result', result)
            records = (intent, attempt, result)
            output['stop'] = _stop_snapshot(records)
            observed = await _read_original(runtime, output, opening, start_attempt, description.run_id, client=client,
                                            read_state=True, stop_records=records)
        else:
            observed = await _observe(runtime, output, client, handle, description, opening, records, True)
        if result is None and observed['stop']['receipt'] is not None:
            files.write('stop-result', {'receipt': observed['stop']['receipt']})
            observed['stop']['result_saved'] = True
        return observed


async def _check_run(runtime, opening, attempt, run_id, client=None):
    try:
        async with asyncio.timeout(runtime.RPC_SECONDS):
            if client is None:
                client = await runtime.connect(opening)
            handle, description = await runtime.original(client, opening, attempt, run_id)
    except runtime.RPCError as error:
        raise ValueError(f'Cannot verify original campaign for task observation: {error.status.name}') from error
    except (TimeoutError, ConnectionError) as error:
        raise ValueError('Cannot connect to or verify the original campaign for task observation') from error
    return client, handle, description


def _require_check_window(expires_at):
    if time.time() >= expires_at:
        raise ValueError('Campaign no longer admits original task observations')


async def _require_ready_check(runtime, handle, description, opening, attempt, task_id):
    expires_at = opening['plan']['limits']['expires_at']
    if description.status != runtime.WorkflowExecutionStatus.RUNNING:
        raise ValueError('Campaign no longer admits original task observations')
    _require_check_window(expires_at)
    view = await runtime.runtime_status(handle, description, opening, start_attempt_sha256=identity(attempt))
    _require_check_window(expires_at)
    if 'tasks' not in view:
        raise ValueError('Original campaign task Worker is unavailable')
    task = view['tasks'][task_id]
    if task['status'] not in ('ready', 'waiting_job'):
        raise ValueError('Campaign task requires readiness and original observations for all dependencies')
    if not task['eligible']:
        raise ValueError('Campaign no longer admits original task observations')
    return task


def _require_check_project(state, opening):
    project = state.project(opening['project'])
    selected = _selection(state, project, opening['project_revision'])
    if any(opening[key] != value for key, value in selected.items()):
        raise ValueError('Original project registration or scheduler changed before task observation')
    return project


async def _read_check(runtime, client, handle, command):
    try:
        async with asyncio.timeout(runtime.RPC_SECONDS):
            return await runtime.read_check(client, handle, command)
    except (TimeoutError, runtime.RPCError):
        return None


def _check_response(opening, task, command, receipt):
    intent, attempt = command['intent'], command['attempt']
    return {'status': receipt['decision'] if receipt is not None else 'unknown', 'run_id': intent['run_id'],
            'workflow_id': opening['workflow_id'], 'project': opening['project'], 'campaign': opening['campaign'],
            'task_id': task['task_id'], 'campaign_project_revision': opening['project_revision'],
            'job_project_revision': task['source']['project_revision'], 'update_id': attempt['update_id'],
            'receipt': receipt}


async def _read_original_check(state, project, source, expires_at, stop_requested):
    """Own the bounded native reader until its subprocess returns or is reaped."""
    from ergora.development.application import candidate_check_status

    monotonic_start = time.monotonic()
    remaining = expires_at - time.time()
    if remaining <= 0:
        raise ValueError('Campaign no longer admits original task observations')
    deadline = monotonic_start + remaining
    cancelled = Event()

    def read():
        try:
            return candidate_check_status(state, project, source['operation_id'], job_sha256=source['job_sha256'],
                verify_pending=source.get('pending') is True, deadline=deadline,
                stop_requested=lambda: cancelled.is_set() or stop_requested())
        except KeyboardInterrupt:
            raise ValueError('Original fixed-check observation was cancelled') from None
        except TimeoutError:
            raise ValueError('Original fixed-check observation reached its deadline') from None

    reader = asyncio.create_task(asyncio.to_thread(read))
    try:
        return await asyncio.shield(reader)
    except asyncio.CancelledError:
        cancelled.set()
        reaped = asyncio.gather(reader, return_exceptions=True)
        while not reaped.done():
            try:
                await asyncio.shield(reaped)
            except asyncio.CancelledError:
                continue
        raise


async def observe_check(state: State, project: str, campaign: str, task_id: str, *, confirm: bool) -> dict:
    """Record one already-authorized original Job observation as the trusted local operator."""
    if confirm is not True:
        raise ValueError('Campaign task observation requires explicit --confirm')
    files = CampaignFiles(state.root, project, campaign)
    opening, attempt, result = files.load()
    if attempt is None:
        raise ValueError('Campaign task observation requires a saved original start attempt')
    _verify_registration(state, opening)
    task = fixed_tasks(opening).get(task_id)
    if task is None:
        raise ValueError('Campaign task is absent from the original frozen plan')
    runtime = _temporal()
    client, handle, description = await _check_run(runtime, opening, attempt, result['run_id'] if result else None)
    run_id = description.run_id
    command = files.load_check(opening, attempt, run_id, task)
    if command is not None:
        return _check_response(opening, task, command, await _read_check(runtime, client, handle, command))
    source = task['source']
    pending = source.get('pending') is True
    waiting_command = files.load_check(opening, attempt, run_id, task, waiting=True) if pending else None
    waiting_receipt = None
    expires_at = opening['plan']['limits']['expires_at']
    if waiting_command is not None:
        waiting_receipt = await _read_check(runtime, client, handle, waiting_command)
        if (waiting_receipt is None or description.status != runtime.WorkflowExecutionStatus.RUNNING
                or time.time() >= expires_at):
            return _check_response(opening, task, waiting_command, waiting_receipt)

    _require_check_project(state, opening)
    view = await _require_ready_check(runtime, handle, description, opening, attempt, task_id)
    if waiting_command is None and view.get('waiting_receipt') is not None:
        raise ValueError('Campaign original waiting task attempt is missing')
    def stopped():
        _, _, saved_stop = files.load_stop(opening, attempt, result)
        return saved_stop is not None and saved_stop['receipt']['decision'] == 'accepted'

    status = await _read_original_check(state, project, source, expires_at, stopped)
    evidence_sha256, job = original_check_evidence(opening, task, status)
    waiting = job is not None and job['status'] in PENDING_JOB_STATES
    if waiting and waiting_receipt is not None:
        return _check_response(opening, task, waiting_command, waiting_receipt)

    files.ensure_directory()
    with file_lock(files.lock, blocking=False):
        client, handle, description = await _check_run(runtime, opening, attempt, run_id, client)
        command = files.load_check(opening, attempt, run_id, task)
        if command is not None:
            return _check_response(opening, task, command, await _read_check(runtime, client, handle, command))
        current_wait = files.load_check(opening, attempt, run_id, task, waiting=True) if pending else None
        if waiting_command is not None and current_wait != waiting_command:
            raise ValueError('Campaign original waiting task attempt changed')
        if current_wait is not None and waiting_command is None:
            waiting_receipt = await _read_check(runtime, client, handle, current_wait)
        if current_wait is not None and (waiting_receipt is None or waiting):
            return _check_response(opening, task, current_wait, waiting_receipt)
        view = await _require_ready_check(runtime, handle, description, opening, attempt, task_id)
        if current_wait is None and view.get('waiting_receipt') is not None:
            raise ValueError('Campaign original waiting task attempt is missing')
        if waiting_receipt is not None:
            job = {**job, 'waiting_receipt_sha256': identity(waiting_receipt)}
        intent = check_intent(opening, identity(attempt), run_id, task_id, evidence_sha256, job=job)
        command = {'intent': intent, 'attempt': update_attempt(intent, FIXED_TASK_UPDATE_PREFIX + str(uuid4()))}
        with State(state.root).connect() as db:
            db.execute('BEGIN IMMEDIATE')
            _require_check_window(expires_at)
            _require_check_project(state, opening)
            if stopped():
                raise ValueError('Campaign no longer admits original task observations')
            files.write(check_record_name(task_id, waiting=waiting), command,
                        before_publish=lambda: _require_check_window(expires_at))
        receipt = None
        remaining = expires_at - time.time()
        if remaining > 0:
            try:
                async with asyncio.timeout(min(runtime.RPC_SECONDS, remaining)):
                    receipt = await runtime.send_check(client, command, expires_at=expires_at)
            except (TimeoutError, ConnectionError, runtime.RPCError):
                pass
        if receipt is None:
            receipt = await _read_check(runtime, client, handle, command)
        return _check_response(opening, task, command, receipt)


async def worker(state: State, project: str, campaign: str) -> dict:
    """Run a foreground worker for an already verified original campaign."""
    files = CampaignFiles(state.root, project, campaign)
    opening, attempt, result = files.load()
    if attempt is None:
        raise ValueError('Campaign worker requires a saved original start attempt')
    _verify_registration(state, opening)
    runtime = _temporal()
    stop_records = files.load_stop(opening, attempt, result)
    output = {**_snapshot(files, opening, attempt, result), 'stop': _stop_snapshot(stop_records)}
    run_id = stop_records[0]['run_id'] if stop_records[0] is not None else output['run_id']
    try:
        async with asyncio.timeout(runtime.RPC_SECONDS):
            client = await runtime.connect(opening)
            handle, description = await runtime.original(client, opening, attempt, run_id)
    except runtime.RPCError as error:
        raise ValueError(f'Cannot verify original campaign for worker: {error.status.name}') from error
    except (TimeoutError, ConnectionError) as error:
        raise ValueError('Cannot connect to or verify the original campaign for worker') from error
    observed = {**output, 'status': 'observed', 'run_id': description.run_id, 'remote_status': 'original_observed'}
    if description.status != runtime.WorkflowExecutionStatus.RUNNING:
        # A concurrent stop can close the run during the first remote observation.
        stop_records = files.load_stop(opening, attempt, result)
        output['stop'] = _stop_snapshot(stop_records)
        return {**await _observe(runtime, output, client, handle, description, opening, stop_records, True),
                'worker_status': 'already_closed'}
    try:
        worker_status = await runtime.run_worker(client, handle, opening, files, attempt)
    except (TimeoutError, runtime.RPCError) as error:
        raise ValueError('Campaign worker exited without observing original closure') from error
    if worker_status == 'closed':
        stop_records = files.load_stop(opening, attempt, result)
        observed['stop'] = _stop_snapshot(stop_records)
        return {**await _read_original(runtime, observed, opening, attempt, description.run_id, client=client,
                                       read_state=True, stop_records=stop_records), 'worker_status': worker_status}
    return {**observed, 'worker_status': worker_status}
