"""Versioned native activities retain trusted file semantics on distinct queues."""

import asyncio
from copy import deepcopy
from pathlib import Path
import signal
import sys
from types import SimpleNamespace

import pytest

pytest.importorskip('temporalio')

from ergora import reference, task_envelopes
from test_composition_runtime import original_input, composed_creation, creation_project, installation, registration


@pytest.mark.skipif(sys.platform != 'linux', reason='Native FileAdapter file semantics require Linux/WSL2')
@pytest.mark.parametrize('version', [1, 2])
def test_each_version_publishes_and_fences_only_its_own_requests(original_input, tmp_path, version):
    from dev_platform.adapter import publish, read_json
    from ergora.reference_workflows import execution_input
    from temporalio.exceptions import ApplicationError

    document = original_input if version == 2 else original_input['legacy_spec']
    selected = execution_input(document)
    config = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    config['trusted_receipts'] = True
    activities = selected.activities(config)
    workflow_type = selected.workflow_type()
    workflow = workflow_type()
    workflow.spec = selected.spec
    if version == 2:
        workflow.admission = document
    context = workflow.context('plan', selected.spec['request']['repository']['starting_sha'])
    job = asyncio.run(activities.submit(context))
    expected = tmp_path / ('requests-composition-v2' if version == 2 else 'requests') / context['task_id'] / (context['job_id'] + '.json')
    assert read_json(expected)['context'] == context
    other = tmp_path / ('requests' if version == 2 else 'requests-composition-v2')
    assert not other.exists()
    assert asyncio.run(activities.poll(job)) is None
    fence = {'task_id': context['task_id'], 'request_sha256': context['request_sha256']}
    pending = asyncio.run(activities.fence(fence))
    assert pending['confirmed'] is False and pending['unresolved_jobs'] == [context['job_id']]
    receipt = {'schema_version': 1, 'job_id': job['job_id'], 'job_sha256': job['job_sha256'], 'state': 'CANCELLED',
        'actor': {'id': 'trusted-executor', 'session_id': 'isolated-session', 'kind': 'agent', 'role': selected.spec['profile']['roles']['plan']},
        'candidate_sha': context['expected_candidate_sha'], 'artifacts': [], 'checks': []}
    publish(tmp_path / 'receipts' / context['task_id'] / (context['job_id'] + '.json'), receipt)
    assert asyncio.run(activities.poll(job)) == receipt
    assert asyncio.run(activities.fence(fence))['confirmed'] is True
    with pytest.raises(ApplicationError, match='fenced'):
        asyncio.run(activities.submit(context))


@pytest.mark.parametrize('admission', ['legacy', 'different-projection', 'missing', 'task-id', 'profile-sha'])
def test_composition_activity_rejects_wrong_admission_before_publication(original_input, tmp_path, admission):
    from ergora.reference_workflows import execution_input
    from temporalio.exceptions import ApplicationError

    selected = execution_input(original_input)
    workflow_type = selected.workflow_type()
    workflow = workflow_type()
    workflow.spec, workflow.admission = selected.spec, original_input
    context = workflow.context('plan', selected.spec['request']['repository']['starting_sha'])
    if admission == 'legacy':
        context['admission'] = selected.spec
    elif admission == 'missing':
        del context['admission']
    elif admission == 'task-id':
        context['task_id'] = 'another-task'
    elif admission == 'profile-sha':
        context['profile_sha256'] = '0' * 64
    else:
        other = deepcopy(selected.spec)
        other['request_sha256'] = '0' * 64
        context['admission'] = task_envelopes.wrap(other, original_input['composition'])
    config = {name: str(tmp_path / name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    activities = selected.activities({**config, 'trusted_receipts': True})
    with pytest.raises(ApplicationError) as rejected:
        asyncio.run(activities.submit(context))
    assert rejected.value.type == 'ContractViolation' and rejected.value.non_retryable
    assert not Path(config['requests']).exists() and not (tmp_path / 'requests-composition-v2').exists()


@pytest.mark.parametrize('stop_at', ['connection', 'first-worker', 'shutdown'])
def test_stop_covers_connection_worker_entry_and_shutdown(monkeypatch, stop_at):
    monkeypatch.syspath_prepend(str(reference.ROOT / 'platform/upstream/platform'))
    from dev_platform import adapter, connection
    from ergora import reference_worker, reference_workflows

    events, handlers = [], {}

    async def exercise():
        loop = asyncio.get_running_loop()

        def install(sig, handler):
            handlers[sig] = handler
            events.append('handler-installed')

        def remove(sig):
            del handlers[sig]
            events.append('handler-removed')

        async def connect():
            if stop_at == 'connection':
                handlers[signal.SIGTERM]()
                try:
                    await asyncio.Event().wait()
                finally:
                    events.append('connection-closed')
            return object()

        class Worker:
            def __init__(self, name):
                self.name = name

            async def __aenter__(self):
                events.append('enter-' + self.name)
                if stop_at == 'first-worker':
                    handlers[signal.SIGTERM]()
                else:
                    loop.call_soon(lambda: handlers[signal.SIGTERM]())
                return self

            async def __aexit__(self, *args):
                handlers[signal.SIGTERM]()
                events.append('exit-' + self.name)

        monkeypatch.setattr(loop, 'add_signal_handler', install)
        monkeypatch.setattr(loop, 'remove_signal_handler', remove)
        monkeypatch.setattr(adapter, 'load_adapter', lambda: SimpleNamespace(config={}))
        monkeypatch.setattr(connection, 'connect', connect)
        monkeypatch.setattr(reference_workflows, 'workers', lambda *args: [Worker('one'), Worker('two')])
        await asyncio.wait_for(reference_worker._serve(), 2)

    asyncio.run(exercise())
    assert events[0] == 'handler-installed' and events[-1] == 'handler-removed'
    if stop_at == 'connection':
        assert 'connection-closed' in events and not any(event.startswith('enter-') for event in events)
    elif stop_at == 'first-worker':
        assert 'exit-one' in events and 'enter-two' not in events
    else:
        assert events.index('exit-two') < events.index('exit-one') < events.index('handler-removed')
