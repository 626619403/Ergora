"""Exercise the formal work queue through its original Temporal run."""

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from ergora.configuration import projects
from ergora.definitions import workflows
from ergora.development import application as tasks, envelopes
from ergora.development.inputs import execution_input
from ergora.interfaces import cli
from test_registrations import installation, registration
from test_task_budget import budget_creation, budget_graph
from test_task_creation import creation_project
from test_work_agents import work_creation, work_graph
from test_workflow_definitions import ref, write_bundle


pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Formal task operations use Linux/WSL2')


@pytest.fixture
def priority_creation(budget_creation, budget_graph, tmp_path):
    state, registered, definition = budget_creation
    library, grant, parent, _, _, _ = budget_graph
    work = deepcopy(workflows.library(library.root).get('specialist-work', '1.0.0')['definition'])
    leaf = work['nodes'][0]
    work['id'] = 'priority-work'
    work['limits']['concurrency'] = 1
    work['nodes'] = [{**leaf, 'id': key} for key in ('a', 'b', 'c', 'd')]
    work['nodes'][2].update(depends_on=['b'], inputs={'task': {'node': 'b', 'output': 'result'}})
    work['nodes'].append({'id': 'done', 'join': 'all', 'depends_on': ['a', 'b', 'c', 'd']})
    saved = workflows.import_bundle(library, write_bundle(tmp_path / 'priority-work', work))

    for name, child in (('prepared-delivery', 'work'), (parent['definition']['id'], 'development')):
        source = workflows.library(library.root).get(name, '1.1.0')['definition']
        document = deepcopy(source)
        document['version'] = '1.1.1'
        next(node for node in document['nodes'] if node['id'] == child)['ref'] = ref(saved, 'workflow')
        folder = tmp_path / ('priority-' + name)
        shutil.copytree(tmp_path / name, folder)
        saved = workflows.import_bundle(library, write_bundle(folder, document))

    manifest = workflows.prepare_manifest(library.root, parent['definition']['id'], '1.1.1',
                                          grant, tmp_path / 'priority-manifest')
    selection = definition['composition']
    binding = next(iter(selection['backend_overrides'].values()))
    assignments = {key: 'root/development/work/' + key for key in ('a', 'b', 'c', 'd')}
    selection.update(manifest=manifest['path'], manifest_digest=manifest['digest'],
                     backend_overrides={path: binding for path in assignments.values()})
    selection['execution']['assignments'] = assignments
    definition['input']['work_units'] = [
        {'id': key, 'depends_on': ['b'] if key == 'c' else [], 'paths': ['src/' + key], 'instructions': 'Fixture'}
        for key in assignments]
    interpreter = Path(registered['execution']['installation']) / '.venv'
    if not interpreter.exists():
        interpreter.symlink_to(sys.prefix, target_is_directory=True)
    return state, registered, definition


def test_work_priority_respects_original_dependencies_and_stop(priority_creation, monkeypatch):
    pytest.importorskip('temporalio')
    from temporalio import workflow
    from temporalio.exceptions import ApplicationError

    state, registered, definition = priority_creation
    monkeypatch.syspath_prepend(str(Path(registered['execution']['installation']) / 'upstream/platform'))
    from dev_platform.workflow import StopWork

    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    selected = execution_input(tasks.preview(state, 'demo', definition, 1)['files']['task.spec.json'])
    run = selected.workflow_type()()
    run.spec, run.admission, run.phase = selected.spec, selected.document, 'IMPLEMENTING'
    run.plan_sha256 = 'a' * 64
    run.approved_plan = {'plan_sha256': run.plan_sha256}
    instance = selected.document['budget']['instance']
    cutoff = datetime.fromisoformat(instance['deadline_at']) - timedelta(seconds=instance['policy']['cleanup_seconds'])
    current_time = cutoff - timedelta(seconds=1)
    monkeypatch.setattr(workflow, 'now', lambda: current_time)
    monkeypatch.setattr(workflow, 'info', lambda: SimpleNamespace(run_id='original'))
    started = asyncio.Queue()
    gates = {key: asyncio.Event() for key in ('a', 'b', 'c', 'd')}

    def prioritize(unit, decision, *, revision=1):
        monkeypatch.setattr(workflow, 'current_update_info',
                            lambda: SimpleNamespace(id='ergora-work-priority/' + decision))
        return run.prioritize_work_unit({'decision_id': decision, 'work_unit_id': unit, 'run_id': 'original',
            'request_sha256': run.spec['request_sha256'], 'admission_sha256': run.admission['sha256'],
            'plan_sha256': run.plan_sha256, 'project_revision': revision})

    async def stage(stage, expected_sha=None, unit=None, dependencies=None):
        key = unit['id']
        assert dependencies == {}
        await started.put(key)
        await gates[key].wait()
        receipt = {'actor': {'session_id': key}}
        run.results[stage] = receipt
        return receipt

    async def exercise():
        nonlocal current_time
        run.stage = stage
        scheduler = asyncio.create_task(run.units())
        try:
            assert await asyncio.wait_for(started.get(), 2) == 'a'
            assert prioritize('a', 'already-dispatched')['status'] == 'rejected'
            for invalid in (True, '1', 0, -1):
                with pytest.raises(ApplicationError, match='Invalid work-priority request'):
                    prioritize('c', 'invalid-revision', revision=invalid)
            current_time = cutoff
            assert 'cutoff' in prioritize('d', 'cutoff')['reason']
            current_time -= timedelta(seconds=1)
            assert prioritize('c', 'waiting')['status'] == 'applied'
            assert started.empty()
            gates['a'].set()
            assert await asyncio.wait_for(started.get(), 2) == 'b'
            assert prioritize('d', 'next-ready')['status'] == 'applied'
            assert started.empty()
            gates['b'].set()
            assert await asyncio.wait_for(started.get(), 2) == 'd'
            run.request_cancel({'request_sha256': run.spec['request_sha256'], 'reason': 'Control test'})
            assert 'Cancellation' in prioritize('c', 'after-cancel')['reason']
            gates['d'].set()
            with pytest.raises(StopWork, match='Control test'):
                await asyncio.wait_for(scheduler, 2)
            assert started.empty()
        finally:
            scheduler.cancel()
            await asyncio.gather(scheduler, return_exceptions=True)

    asyncio.run(exercise())


@pytest.mark.skipif(not os.environ.get('ERGORA_TEST_TEMPORAL_BIN'), reason='Requires the optional local Temporal CLI')
@pytest.mark.parametrize('steer', [False, True], ids=['original-order', 'prioritize'])
def test_original_run_applies_and_recovers_pending_priority(priority_creation, tmp_path, monkeypatch, capsys, steer):
    pytest.importorskip('temporalio')
    binary = os.environ['ERGORA_TEST_TEMPORAL_BIN']
    from ergora.development.runtime.worker import _ErgoraPackage
    from temporalio import activity
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Replayer, Worker

    state, registered, definition = priority_creation
    monkeypatch.syspath_prepend(str(Path(registered['execution']['installation']) / 'upstream/platform'))
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    selected = execution_input(preview['files']['task.spec.json'])
    work = asyncio.Queue()
    gates = {unit['id']: asyncio.Event() for unit in selected.spec['request']['input']['work_units']}
    contexts = {}
    plan_approval = []
    sends = tmp_path / 'update-sends'
    racing, release_race = tmp_path / 'racing', tmp_path / 'release-race'

    @activity.defn(name='dev_validate')
    async def validate(spec):
        assert spec == selected.spec
        return {}

    @activity.defn(name=envelopes.WORK_SUBMIT)
    async def submit(context):
        job = {key: context[key] for key in ('task_id', 'job_id')}
        assert context['job_id'] not in contexts and context['admission'] == selected.document
        contexts[context['job_id']] = context
        if context['stage'].startswith('work:'):
            await work.put(context['unit']['id'])
        return {**job, 'job_sha256': envelopes.identity(context)}

    @activity.defn(name=envelopes.WORK_POLL)
    async def poll(job):
        context = contexts[job['job_id']]
        stage = context['stage']
        assert job['job_sha256'] == envelopes.identity(context)
        if stage.startswith('work:'):
            await gates[context['unit']['id']].wait()
        receipt = {**job, 'state': 'SUCCEEDED', 'actor': {'id': stage, 'session_id': job['job_id']},
                   'candidate_sha': selected.spec['request']['repository']['starting_sha']}
        return {'receipt': receipt, 'review_decision': 'approve'} if stage.startswith('review:') else receipt

    @activity.defn(name='dev_authorize_plan')
    async def authorize(context):
        plan_approval.append(context)
        return {'receipt_id': context['receipt_id']}

    @activity.defn(name='dev_fence')
    async def fence(context):
        return {'confirmed': True}

    async def exercise():
        async with await WorkflowEnvironment.start_local(dev_server_existing_path=binary,
                dev_server_database_filename=str(tmp_path / 'temporal.sqlite'), dev_server_log_level='error') as service:
            address = service.client.service_client.config.target_host
            original_run = subprocess.run

            def run_native(argv, **kwargs):
                if isinstance(argv[-1], str) and argv[-1].startswith('from ergora.development.runtime.'):
                    command = argv[-1]
                    if any(name in command for name in ('.submission', '.approval', '.work_priority')):
                        setup = f"""
import asyncio
from pathlib import Path
from dev_platform import connection
from temporalio.client import Client, WorkflowHandle, WorkflowUpdateRPCTimeoutOrCancelledError
async def connect():
    return await Client.connect({address!r})
connection.connect = connect
from ergora.development.inputs import PreparationDAGInput
PreparationDAGInput.admission_report = lambda *args: {{'ready_for_real_tasks': True}}
execute = WorkflowHandle.execute_update
async def execute_update(self, *args, **kwargs):
    if kwargs['id'].endswith('/interrupted'):
        raise WorkflowUpdateRPCTimeoutOrCancelledError()
    if kwargs['id'].endswith('/racing'):
        Path({str(racing)!r}).touch()
        async with asyncio.timeout(6):
            while not Path({str(release_race)!r}).exists():
                await asyncio.sleep(.025)
    with Path({str(sends)!r}).open('a') as stream:
        print(kwargs['id'], file=stream)
    result = await execute(self, *args, **kwargs)
    if kwargs['id'].endswith('/lost-reply'):
        raise WorkflowUpdateRPCTimeoutOrCancelledError()
    return result
WorkflowHandle.execute_update = execute_update
"""
                        argv = [*argv[:-1], setup + command]
                return original_run(argv, **kwargs)

            monkeypatch.setattr(subprocess, 'run', run_native)
            finder = _ErgoraPackage()
            sys.meta_path.insert(0, finder)
            try:
                async with Worker(service.client, task_queue=selected.task_queue('development-tasks'),
                        workflows=[selected.workflow_type()], activities=[validate, submit, poll, authorize, fence]):
                    submitted = await asyncio.to_thread(tasks.start, state, 'demo', definition['task_id'], 1,
                                                        created['intent_sha256'])
                    assert submitted['status'] == 'submitted'
                    run_id = submitted['run_id']
                    handle = service.client.get_workflow_handle(submitted['workflow_id'], run_id=run_id)
                    async with asyncio.timeout(5):
                        while (current := await handle.query('status'))['phase'] != 'AWAITING_PLAN_APPROVAL':
                            await asyncio.sleep(.05)
                    plan = current['plan_sha256']
                    if steer:
                        before_approval = await asyncio.to_thread(tasks.prioritize_work_unit, state, 'demo',
                            definition['task_id'], 'c', 1, run_id=run_id, plan_sha256=plan,
                            decision_id='before-approval', confirm=True)
                        assert before_approval['status'] == 'rejected' and not before_approval['attempt_saved']
                    assert (await asyncio.to_thread(tasks.approve, state, 'demo', definition['task_id'], 'owner', 1,
                                run_id=run_id, plan_sha256=plan, confirm=True))['status'] == 'requested'

                    async def prioritize(unit, decision, *, plan_sha256=plan, revision=1):
                        return await asyncio.to_thread(cli.main, ['--home', str(state.root), 'task', 'prioritize-work',
                            'demo', definition['task_id'], unit, '--revision', str(revision), '--run-id', run_id,
                            '--plan-sha256', plan_sha256, '--decision-id', decision, '--confirm'])

                    async def priority_outcome(decision, *, timeout=20):
                        args = ['--home', str(state.root), 'task', 'work-priority', 'demo', definition['task_id'],
                                decision, '--run-id', run_id, '--timeout', str(timeout)]
                        assert await asyncio.to_thread(cli.main, args) == 0
                        return json.loads(capsys.readouterr().out)

                    assert await asyncio.wait_for(work.get(), 5) == 'a'
                    if steer:
                        info = (await handle.query('status'))['work_priority']
                        assert info == {'available': True, 'unavailable_reason': None,
                            'pending_work_unit_ids': ['b', 'c', 'd'], 'preferred_work_unit_id': None}
                        assert await prioritize('a', 'already-dispatched') == 1
                        rejected = json.loads(capsys.readouterr().out)
                        assert rejected['status'] == 'rejected' and not rejected['attempt_saved']
                        assert await prioritize('c', 'wrong-plan', plan_sha256='0' * 64) == 1
                        assert json.loads(capsys.readouterr().out)['status'] == 'rejected'
                        assert await prioritize('c', 'wrong-revision', revision=2) == 2
                        assert 'Project revision changed' in capsys.readouterr().err
                        assert await prioritize('d', 'interrupted') == 1
                        notice = json.loads(capsys.readouterr().out)
                        assert notice['status'] == 'unknown' and notice['attempt_saved']
                        assert (await priority_outcome('interrupted', timeout=2))['status'] == 'unknown'
                        assert await prioritize('c', 'waiting-on-b') == 0
                        assert json.loads(capsys.readouterr().out)['status'] == 'applied'
                    gates['a'].set()
                    assert await asyncio.wait_for(work.get(), 5) == 'b'

                    if steer:
                        assert await prioritize('d', 'lost-reply') == 1
                        uncertain = json.loads(capsys.readouterr().out)
                        assert uncertain['status'] == 'unknown' and uncertain['attempt_saved']
                        recovered = await priority_outcome('lost-reply')
                        assert recovered['status'] == 'applied' and recovered['run_id'] == run_id
                        assert recovered['command_sha256'] == uncertain['command_sha256']
                        assert await prioritize('d', 'lost-reply') == 0
                        assert json.loads(capsys.readouterr().out) == recovered
                        assert await prioritize('c', 'lost-reply') == 2
                        assert 'already bound to a different command' in capsys.readouterr().err
                        assert sends.read_text().splitlines() == [
                            'ergora-work-priority/waiting-on-b', 'ergora-work-priority/lost-reply']
                        late = asyncio.create_task(prioritize('d', 'racing'))
                        async with asyncio.timeout(6):
                            while not racing.exists():
                                await asyncio.sleep(.025)
                    gates['b'].set()
                    for key in (('d', 'c') if steer else ('c', 'd')):
                        assert await asyncio.wait_for(work.get(), 5) == key
                        if steer and key == 'd':
                            release_race.touch()
                            assert await late == 1
                            denied = json.loads(capsys.readouterr().out)
                            assert denied['status'] == 'rejected' and denied['attempt_saved']
                            assert (await priority_outcome('racing')) == denied
                        gates[key].set()
                    result = await asyncio.wait_for(handle.result(follow_runs=False), 8)
                    assert result['status'] == 'REVIEW_READY'
                    assert result['plan_sha256'] == plan and len(plan_approval) == 1
                    assert result['budget']['sha256'] == selected.document['budget']['instance']['sha256']
                    if steer:
                        assert (await priority_outcome('lost-reply')) == recovered
                        attempt_path = (Path(registered['execution']['state_directory']) / 'ergora/task-submissions'
                                        / (definition['task_id'] + '.priority-lost-reply.attempt.json'))
                        original_attempt = attempt_path.read_bytes()
                        changed = json.loads(original_attempt)
                        assert changed['command']['project_revision'] == recovered['project_revision'] == 1
                        changed['command']['project_revision'] = 123
                        attempt_path.write_text(json.dumps(changed), encoding='utf-8')
                        try:
                            with pytest.raises(ValueError, match='Temporal Update outcome differs'):
                                await asyncio.to_thread(tasks.work_priority, state, 'demo', definition['task_id'],
                                                        'lost-reply', run_id=run_id)
                        finally:
                            attempt_path.write_bytes(original_attempt)
                        project = projects.bind(state, 'demo', 'reviewer', {'tool': 'codex', 'model': 'later-model'}, 1)
                        assert project['revision'] == 2
                        assert (await priority_outcome('lost-reply')) == recovered
                        assert sends.read_text().splitlines() == [
                            'ergora-work-priority/waiting-on-b', 'ergora-work-priority/lost-reply',
                            'ergora-work-priority/racing']
                    integration = next(context for context in contexts.values() if context['stage'] == 'integrate')
                    assert set(integration['dependencies']) == {'work:a', 'work:b', 'work:c', 'work:d'}
                    history = await handle.fetch_history()
                    completed_updates = [event.workflow_execution_update_completed_event_attributes.meta.update_id
                                         for event in history.events
                                         if event.HasField('workflow_execution_update_completed_event_attributes')]
                    assert completed_updates == (sends.read_text().splitlines() if steer else [])
                (tmp_path / 'history.json').write_text(history.to_json(), encoding='utf-8')
                await asyncio.wait_for(Replayer(workflows=[selected.workflow_type()]).replay_workflow(history), 10)
            finally:
                sys.meta_path.remove(finder)

    asyncio.run(exercise())
