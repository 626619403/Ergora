"""Local operator entry points for one immutable campaign plan and original start."""

import asyncio
from pathlib import Path
import time
from uuid import uuid4

from ergora.campaigns.records import (
    WORKFLOW_TYPE, CampaignFiles, attempt_document, identity, read_plan, result_document, sha256, uuid_text,
    worker_queue, workflow_id,
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


async def _read_original(runtime, output, opening, attempt, run_id, *, client=None, read_state=False):
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
    observed = {**output, 'status': 'observed', 'run_id': description.run_id, 'remote_status': 'original_observed',
                'temporal_status': description.status.name}
    if read_state:
        try:
            async with asyncio.timeout(runtime.RPC_SECONDS):
                observed.update(await runtime.runtime_status(handle, description, opening))
        except (TimeoutError, runtime.RPCError):
            observed['workflow_state_status'] = 'unavailable'
    return observed


async def status(state: State, project: str, campaign: str, *, online: bool = False) -> dict:
    """Read the saved evidence, optionally observing the verified original Workflow on the saved route."""
    files = CampaignFiles(state.root, project, campaign)
    opening, attempt, result = files.load()
    output = _snapshot(files, opening, attempt, result)
    if opening is not None:
        _verify_registration(state, opening)
    if online and attempt is not None:
        runtime = _temporal()
        return await _read_original(runtime, output, opening, attempt, output['run_id'], read_state=True)
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
                files.write('intent', opening)
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
                files.write('attempt', attempt)
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
            files.write('result', result_document(opening, attempt, observed['run_id']))
        return {**observed, 'status': 'created' if attempted_here and acknowledged_run else 'observed',
                'result_saved': True}


async def worker(state: State, project: str, campaign: str) -> dict:
    """Run a foreground worker for an already verified original campaign."""
    files = CampaignFiles(state.root, project, campaign)
    opening, attempt, result = files.load()
    if attempt is None:
        raise ValueError('Campaign worker requires a saved original start attempt')
    _verify_registration(state, opening)
    runtime = _temporal()
    output = _snapshot(files, opening, attempt, result)
    try:
        async with asyncio.timeout(runtime.RPC_SECONDS):
            client = await runtime.connect(opening)
            handle, description = await runtime.original(client, opening, attempt, output['run_id'])
    except runtime.RPCError as error:
        raise ValueError(f'Cannot verify original campaign for worker: {error.status.name}') from error
    except (TimeoutError, ConnectionError) as error:
        raise ValueError('Cannot connect to or verify the original campaign for worker') from error
    observed = {**output, 'status': 'observed', 'run_id': description.run_id, 'remote_status': 'original_observed'}
    if description.status != runtime.WorkflowExecutionStatus.RUNNING:
        try:
            async with asyncio.timeout(runtime.RPC_SECONDS):
                return {**observed, **await runtime.runtime_status(handle, description, opening),
                        'worker_status': 'already_closed'}
        except (TimeoutError, runtime.RPCError) as error:
            raise ValueError('Original closure evidence remains unavailable') from error
    try:
        worker_status = await runtime.run_worker(client, handle, opening)
    except (TimeoutError, runtime.RPCError) as error:
        raise ValueError('Campaign worker exited without observing original closure') from error
    if worker_status == 'closed':
        return {**await _read_original(runtime, observed, opening, attempt, description.run_id,
                                       client=client, read_state=True), 'worker_status': worker_status}
    return {**observed, 'worker_status': worker_status}
