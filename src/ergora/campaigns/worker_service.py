"""Manage the original Campaign Worker with the registered local Supervisor."""

import asyncio
from contextlib import ExitStack, contextmanager, nullcontext
from functools import partial
import os
from pathlib import Path
import sys

from ergora.campaigns.records import identity
from ergora.operations import services
from ergora.runtime import processes
from ergora.storage.state import file_lock


def _binding(files, opening, attempt, result, registration):
    return {
        'schema_version': 1, 'scope': 'campaign-worker', 'control_home': str(files.home),
        'project': files.project, 'campaign': files.campaign, 'opening_sha256': identity(opening),
        'start_attempt_sha256': identity(attempt), 'run_id': result['run_id'],
        'scheduler': opening['scheduler'], 'task_queue': opening['task_queue'],
        'installation': registration['registration']['definition']['execution']['installation'],
    }


def _worker(view):
    return next((item for item in view['services'] if item['name'] == services.CAMPAIGN_WORKER), None)


def _service_folder(files):
    folder = files.directory / 'svc'
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError('Campaign Worker service requires its original directory')
    return folder


def _poller(opening, process):
    return 'ergora-campaign-' + identity({'task_queue': opening['task_queue'], 'process': process})


@contextmanager
def polling_owner(files, opening, attempt, result, registration):
    """Hold one local polling claim for the lifetime of a foreground or managed Worker."""
    lease = files.directory / '.worker.lock'
    if sys.platform != 'linux':
        with file_lock(lease, blocking=False):
            yield None
        return
    folder = _service_folder(files)
    binding = _binding(files, opening, attempt, result, registration) if result is not None else None
    worker = _worker(services.campaign_worker_status(folder, binding))
    if worker is not None and worker['pid'] == os.getpid():
        with file_lock(lease, blocking=False):
            yield _poller(opening, processes.identity(os.getpid()))
        return
    with ExitStack() as claim:
        with file_lock(files.directory / '.worker-control.lock', blocking=False):
            if services.campaign_worker_status(folder, binding)['daemon'] != 'not_running':
                raise ValueError('The managed service owns the original Campaign Worker queue')
            claim.enter_context(file_lock(lease, blocking=False))
        yield None


async def _original_run_status(runtime, files, opening, attempt, run_id):
    async with asyncio.timeout(runtime.RPC_SECONDS):
        client = await runtime.connect(opening)
        _, run, _ = await runtime.current(client, files, opening, attempt, run_id)
    return run.status


async def _require_open(runtime, files, opening, attempt, run_id):
    try:
        status = await _original_run_status(runtime, files, opening, attempt, run_id)
    except (runtime.RPCError, TimeoutError, ConnectionError) as error:
        raise ValueError('Cannot verify the original Campaign before starting its managed Worker') from error
    if status != runtime.WorkflowExecutionStatus.RUNNING:
        raise ValueError('The original Campaign Run has closed')


@contextmanager
def _admit_start(files, opening, attempt, result, runtime):
    with ExitStack() as owner:
        try:
            owner.enter_context(file_lock(files.lock, blocking=False))
        except BlockingIOError as error:
            raise ValueError('Reconcile the current original Campaign operation before starting its managed Worker') from error
        asyncio.run(_require_open(runtime, files, opening, attempt, result['run_id']))
        _, stop_attempt, stop_result = files.load_stop(opening, attempt, result)
        if stop_result is not None:
            raise ValueError('The original Campaign STOP closed Worker start admission')
        if stop_attempt is not None:
            raise ValueError('Reconcile the original Campaign STOP attempt before starting its managed Worker')
        yield


def _stop_requires_worker(files, opening, attempt, result, temporal):
    # Original STOP may be in flight after the operator lost its reply.
    stop_intent, _, _ = files.load_stop(opening, attempt, result)
    if stop_intent is None:
        return False
    try:
        runtime = temporal()
    except ValueError:
        return True
    try:
        status = asyncio.run(_original_run_status(runtime, files, opening, attempt, result['run_id']))
    except (runtime.RPCError, TimeoutError, ConnectionError):
        return True
    execution = runtime.WorkflowExecutionStatus
    return status not in (execution.COMPLETED, execution.FAILED, execution.CANCELED,
                          execution.TERMINATED, execution.CONTINUED_AS_NEW, execution.TIMED_OUT)


def _control(files, folder, binding, opening, attempt, result, action, timeout, temporal):
    with ExitStack() as owner:
        try:
            owner.enter_context(file_lock(files.directory / '.worker-control.lock', blocking=False))
        except BlockingIOError:
            return {'outcome': 'unconfirmed', 'reason': 'worker_control_busy'}
        if action == 'start':
            admit_start = partial(_admit_start, files, opening, attempt, result, temporal())
            with admit_start():
                if services.campaign_worker_status(folder, binding)['daemon'] == 'not_running':
                    try:
                        with file_lock(files.directory / '.worker.lock', blocking=False):
                            pass
                    except BlockingIOError as error:
                        raise ValueError('Stop the original foreground Campaign Worker before starting the managed service') from error
        else:
            admit_start = nullcontext
            try:
                owner.enter_context(file_lock(files.lock, blocking=False))
            except BlockingIOError:
                return {'outcome': 'unconfirmed', 'reason': 'campaign_control_busy'}
            if _stop_requires_worker(files, opening, attempt, result, temporal):
                return {'outcome': 'unconfirmed', 'reason': 'campaign_stop_unresolved'}
        return services.control_campaign_worker(folder, binding, action, timeout=timeout, admit_start=admit_start)


def _generation(worker):
    if worker is None or worker['statename'] != 'RUNNING':
        return 'unavailable', None
    if type(worker['pid']) is not int or worker['pid'] < 1:
        return 'unknown', None
    try:
        state, identity = processes.observe_process(worker['pid'])
    except (FileNotFoundError, ProcessLookupError):
        return 'exited', None
    except PermissionError:
        return 'unknown', None
    if state in ('T', 't'):
        return 'suspended', identity
    if state in ('Z', 'X', 'x'):
        return 'exited', identity
    return 'live', identity


async def _original_queue(runtime, files, opening, attempt, run_id, live_poller):
    from datetime import timedelta
    from temporalio.api.enums.v1 import TaskQueueType
    from temporalio.api.taskqueue.v1 import TaskQueue
    from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest

    async with asyncio.timeout(runtime.RPC_SECONDS):
        client = await runtime.connect(opening)
        handle, run, successor = await runtime.current(client, files, opening, attempt, run_id)
        observed = await client.workflow_service.describe_task_queue(DescribeTaskQueueRequest(
            namespace=client.namespace, task_queue=TaskQueue(name=opening['task_queue']),
            task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW),
            retry=False, timeout=timedelta(seconds=runtime.RPC_SECONDS))
        pollers = [poller.identity for poller in observed.pollers]
        responsive = (run.status == runtime.WorkflowExecutionStatus.RUNNING and live_poller in pollers
                      and await runtime.stop_supported(handle, opening))
    return run.status, pollers, responsive, handle.run_id if successor is not None else None


async def _health(files, folder, binding, opening, attempt, result, temporal):
    local = services.campaign_worker_status(folder, binding)
    before_state, before = _generation(_worker(local))
    expected = _poller(opening, before) if before is not None else None
    queue = {'task_queue': opening['task_queue'], 'scheduler': opening['scheduler'], 'status': 'unavailable',
             'managed_polling': 'unavailable', 'managed_poller_report': 'unavailable'}
    try:
        runtime = temporal()
    except ValueError as error:
        queue['reason'] = str(error)
        observation = None
    else:
        try:
            observation = await _original_queue(runtime, files, opening, attempt, result['run_id'],
                                                expected if before_state == 'live' else None)
        except (runtime.RPCError, TimeoutError, ConnectionError):
            observation = None
            queue['reason'] = 'original_queue_unavailable'
    local = services.campaign_worker_status(folder, binding)
    worker = _worker(local)
    after_state, after = _generation(worker)
    queue['process_state'] = 'unknown' if local['daemon'] == 'unconfirmed' else after_state
    if queue['process_state'] in ('suspended', 'unknown'):
        queue['managed_polling'] = queue['process_state']
    if observation is not None:
        run_status, pollers, responsive, current_run_id = observation
        if current_run_id is not None:
            queue['current_run_id'] = current_run_id
        queue.update(status='observed', temporal_status=run_status.name, poller_count=len(pollers))
        same_generation = before is not None and after == before
        if same_generation:
            queue['managed_poller_report'] = 'reported' if expected in pollers else 'not_reported'
        _, stop_attempt, stop_result = files.load_stop(opening, attempt, result)
        if run_status != runtime.WorkflowExecutionStatus.RUNNING:
            queue['managed_polling'] = 'closed'
        elif stop_result is not None:
            queue['managed_polling'] = 'stopping'
        elif stop_attempt is not None:
            queue['managed_polling'] = 'unknown'
        elif same_generation and after_state == 'live' and responsive:
            queue['managed_polling'] = 'observed'
    return local['daemon'], worker, queue


async def manage(files, opening, attempt, result, registration, action, *, confirm, timeout, temporal):
    if sys.platform != 'linux':
        raise ValueError('Managed Campaign Worker service requires Linux or WSL2')
    if action not in ('start', 'status', 'stop'):
        raise ValueError('Choose start, status, or stop for the managed Campaign Worker')
    if action == 'stop' and confirm is not True:
        raise ValueError('Managed Campaign Worker stop requires explicit --confirm')
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Service timeout must be 1–60 seconds')
    folder, binding = _service_folder(files), _binding(files, opening, attempt, result, registration)
    operation = None
    if action != 'status':
        operation = await asyncio.to_thread(_control, files, folder, binding, opening, attempt, result,
                                            action, timeout, temporal)
    daemon, worker, queue = await _health(files, folder, binding, opening, attempt, result, temporal)
    output = {'project': files.project, 'campaign': files.campaign, 'run_id': result['run_id'],
              'start_attempt_id': attempt['attempt_id'], 'action': action, 'outcome': 'observed',
              'daemon': daemon, 'worker': worker, 'queue': queue}
    if operation is not None:
        output['outcome'] = output['control_outcome'] = operation['outcome']
        if 'reason' in operation:
            output['control_reason'] = operation['reason']
    if action == 'start' and output['outcome'] == 'confirmed':
        if queue['managed_polling'] == 'closed':
            output['outcome'] = 'closed'
        elif queue['managed_polling'] != 'observed':
            output['outcome'] = 'unconfirmed'
    return output
