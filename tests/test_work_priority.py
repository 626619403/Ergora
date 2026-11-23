"""Exercise the formal work queue through its original Temporal run."""

import asyncio
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
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
def test_checkpoint_amendment_starts_one_reapproved_successor(priority_creation, tmp_path, monkeypatch, capsys):
    pytest.importorskip('temporalio')
    from ergora.development.runtime.creation_process import task_creation, task_preparation
    from ergora.development.runtime.worker import _ErgoraPackage
    from temporalio import activity
    from temporalio.testing import WorkflowEnvironment
    from temporalio.worker import Worker

    state, registered, definition = priority_creation
    runtime = Path(registered['execution']['state_directory'])
    install = Path(registered['execution']['installation'])
    monkeypatch.syspath_prepend(str(install / 'upstream/platform'))
    from dev_platform.adapter import publish
    from dev_platform.ingress import IngressLeases

    task_id = definition['task_id']
    definition['budget']['wall_seconds'] = 180
    assert tasks.prepare(state, 'demo', definition, 1)['status'] == 'prepared'
    preview = tasks.preview(state, 'demo', definition, 1)
    created = tasks.create(state, 'demo', definition, 1, preview['preview_sha256'], prepare_sha256=preview['prepare_sha256'])
    selected = execution_input(preview['files']['task.spec.json'])
    baseline = selected.spec['request']['repository']['starting_sha']
    successor_commit = subprocess.run(['git', '-C', registered['repo'], '-c', 'user.name=Fixture',
        '-c', 'user.email=fixture@example.test', 'commit-tree', baseline + '^{tree}', '-p', baseline,
        '-m', 'Controlled successor candidate'], check=True, capture_output=True, text=True).stdout.strip()
    config = {key: str(runtime / key) for key in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
    config['trusted_receipts'] = True
    (Path(registered['execution']['config_directory']) / 'adapter.json').write_text(json.dumps(config), encoding='utf-8')
    activities = selected.activities(config)
    revised = deepcopy(definition)
    revised['task_id'] = 'revised-task'
    revised['input']['goal'] = 'Extend the original behavior to empty requests.'
    revised['input']['acceptance'] = ['Empty requests return the specified validation error.']
    revised['input']['work_units'][0]['instructions'] = 'Handle empty requests before ordinary parsing.'
    change = 'Owner requires an explicit validation error for empty requests.'
    proposed = tmp_path / 'revised.json'
    proposed.write_text(json.dumps(revised), encoding='utf-8')
    observed_work = asyncio.Queue()
    contexts = {}

    def terminal(context, status='SUCCEEDED'):
        stage = context['stage']
        group = stage.split(':')[0]
        role = context['spec']['profile']['roles'][group]
        artifacts = []
        names = list(context['spec']['profile']['artifacts_by_stage'][group])
        if stage == 'plan':
            names.append('preparation-sources')
        for name in names:
            relative = f"{context['task_id']}/{context['job_id']}/{name}.txt"
            text = f'Controlled {stage} evidence for {context["task_id"]}.\n'.encode()
            if name == 'execution-plan':
                text = json.dumps(context['spec']['request']['input']).encode()
            elif name == 'preparation-sources':
                text = json.dumps({'kind': 'formal-preparation-sources', 'stage': stage,
                    'member': context['preparation_ports']['member'], 'request_sha256': context['request_sha256'],
                    'profile_sha256': context['profile_sha256'], 'admission_sha256': context['admission']['sha256'],
                    'members': {}, 'inventory': {'outputs': {}}}).encode()
            path = activities.adapter.path('artifacts', relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text)
            artifacts.append({'name': name, 'path': relative, 'sha256': hashlib.sha256(text).hexdigest()})
        changed = context['task_id'] == 'revised-task' and group in ('work', 'integrate', 'verify', 'review')
        receipt = {'schema_version': 1, 'job_id': context['job_id'], 'job_sha256': envelopes.identity(context),
                   'state': status, 'actor': {'kind': 'ci' if stage in ('integrate', 'verify') else 'agent',
                       'role': role, 'id': stage, 'session_id': context['job_id']},
                   'candidate_sha': successor_commit if changed else baseline,
                   'checks': [], 'artifacts': artifacts}
        activities.adapter.verify_receipt(receipt, receipt)
        publish(activities.adapter.path('receipts', f"{context['task_id']}/{context['job_id']}.json"), receipt)
        return receipt

    @activity.defn(name='dev_validate')
    async def validate(spec):
        return {'validated': True}

    @activity.defn(name=envelopes.WORK_SUBMIT)
    async def submit(context):
        job = await activities.submit(context)
        contexts[context['job_id']] = context
        if context['stage'].startswith('work:'):
            await observed_work.put(context)
        if (context['task_id'], context['stage']) != (task_id, 'work:b'):
            terminal(context)
        return job

    @activity.defn(name=envelopes.WORK_POLL)
    async def poll(job):
        context = contexts[job['job_id']]
        receipt = await activities.adapter.poll({**job, 'context': context})
        return {'receipt': receipt, 'review_decision': 'approve'} if context['stage'].startswith('review:') else receipt

    async def exercise():
        async with await WorkflowEnvironment.start_local(dev_server_existing_path=os.environ['ERGORA_TEST_TEMPORAL_BIN'],
                dev_server_database_filename=str(tmp_path / 'temporal.sqlite'), dev_server_log_level='error') as service:
            address = service.client.service_client.config.target_host
            lost_reply = tmp_path / 'lost-successor-start'
            start_calls = tmp_path / 'native-starts'
            pause = tmp_path / 'pause-checkpoint'
            reached = tmp_path / 'checkpoint-entered'
            release = tmp_path / 'checkpoint-release'
            setup = f"""
import asyncio
from pathlib import Path
from dev_platform import connection
from temporalio.client import Client
from ergora.development.inputs import PreparationDAGInput
PreparationDAGInput.admission_report = lambda *args: {{'ready_for_real_tasks': True}}
async def connect():
    if Path({str(pause)!r}).exists():
        Path({str(pause)!r}).unlink()
        Path({str(reached)!r}).touch()
        async with asyncio.timeout(8):
            while not Path({str(release)!r}).exists():
                await asyncio.sleep(.025)
    return await Client.connect({address!r})
connection.connect = connect
original_start = Client.start_workflow
async def start(self, *args, **kwargs):
    result = await original_start(self, *args, **kwargs)
    with Path({str(start_calls)!r}).open('a') as stream:
        print(kwargs['id'], file=stream)
    if kwargs['id'] == 'dev-task/revised-task' and Path({str(lost_reply)!r}).exists():
        raise ValueError('Controlled loss after the real native start')
    return result
Client.start_workflow = start
"""
            # The native preparation child also enters the registered runtime.
            # Inject at the disposable fixture interpreter, leaving all
            # manifest-verified reference Python files alone.
            interpreter = install / '.venv'
            original_venv = interpreter.readlink()
            interpreter.unlink()
            wrapper = interpreter / 'bin/python'
            wrapper.parent.mkdir(parents=True)
            wrapper.write_text(f"#!{sys.executable}\nimport os, sys\nargs = sys.argv[1:]\n"
                               f"if args[:2] == ['-P', '-c']:\n    args[2] = {setup!r} + args[2]\n"
                               "os.execv(sys.executable, [sys.executable, *args])\n", encoding='utf-8')
            wrapper.chmod(0o700)
            finder = _ErgoraPackage()
            sys.meta_path.insert(0, finder)
            try:
                async with Worker(service.client, task_queue=selected.task_queue('development-tasks'),
                        workflows=[selected.workflow_type()], activities=[validate, submit, poll, activities.authorize, activities.fence]):
                    first = await asyncio.to_thread(tasks.start, state, 'demo', task_id, 1, created['intent_sha256'])
                    run_id = first['run_id']
                    handle = service.client.get_workflow_handle(first['workflow_id'], run_id=run_id)

                    async def await_plan(workflow):
                        async with asyncio.timeout(8):
                            while (current := await workflow.query('status'))['phase'] != 'AWAITING_PLAN_APPROVAL':
                                await asyncio.sleep(.05)
                            return current['plan_sha256']

                    async def amend(exit_code, revision=1):
                        args = ['--home', str(state.root), 'task', 'preview-amendment', 'demo', task_id,
                            '--revision', str(revision), '--run-id', run_id, '--definition', str(proposed), '--change', change]
                        assert await asyncio.to_thread(cli.main, args) == exit_code
                        return json.loads(capsys.readouterr().out)

                    old_plan = await await_plan(handle)
                    original_submission = runtime / 'ergora/task-submissions' / f'{task_id}.result.json'
                    original_submission.unlink()
                    unknown = await amend(1)
                    assert unknown['checkpoint']['submission_status'] == 'unknown' and unknown['successor_definition'] is None
                    assert all(row['original_work']['state'] == 'unavailable' for row in unknown['delta']['work_units'].values())
                    recovered = await asyncio.to_thread(tasks.resume_start, state, 'demo', task_id, 1, first['intent_sha256'])
                    assert recovered['run_id'] == run_id
                    pending = await amend(1)
                    assert pending['checkpoint']['plan'] == {'state': 'pending', 'receipt_sha256': old_plan,
                                                               'job_id': pending['checkpoint']['plan']['job_id']}
                    assert pending['successor_definition'] is None and pending['read_only'] is True
                    assert all(row['original_work']['state'] == 'not_observed' for row in pending['delta']['work_units'].values())
                    assert (await asyncio.to_thread(tasks.approve, state, 'demo', task_id, 'first-owner', 1,
                        run_id=run_id, plan_sha256=old_plan, confirm=True))['status'] == 'requested'
                    assert (await asyncio.wait_for(observed_work.get(), 8))['stage'] == 'work:a'
                    stalled = await asyncio.wait_for(observed_work.get(), 8)
                    assert stalled['stage'] == 'work:b'
                    running = await amend(1)
                    assert running['checkpoint']['plan']['state'] == 'accepted'
                    assert running['delta']['work_units']['a']['original_work']['state'] == 'terminal'
                    assert running['delta']['work_units']['b']['original_work']['state'] == 'submitted'
                    assert running['delta']['work_units']['a']['after']['instructions'] == revised['input']['work_units'][0]['instructions']
                    assert (await asyncio.to_thread(tasks.preparation, state, 'demo', 'revised-task'))['status'] == 'not_recorded'

                    assert (await asyncio.to_thread(tasks.cancel, state, 'demo', task_id, 'owner-stop', 1,
                        run_id=run_id, reason=change, confirm=True))['status'] == 'requested'
                    result = await asyncio.wait_for(handle.result(), 10)
                    assert result['status'] == 'CANCEL_UNCONFIRMED'
                    unresolved = await amend(1)
                    assert unresolved['delta']['work_units']['b']['original_work']['state'] == 'unresolved'
                    assert unresolved['successor_definition'] is None
                    terminal(stalled, 'CANCELLED')
                    assert (await amend(1))['checkpoint']['next_action'] == 'reconcile_original_run'
                    released = await asyncio.to_thread(tasks.reconcile, state, 'demo', task_id, 1, run_id=run_id, confirm=True)
                    assert released['status'] == 'reconciled'

                    immutable = {file: file.read_bytes() for file in runtime.rglob('*.json')}
                    lease_path = runtime / 'ingress/leases.sqlite3'
                    lease_contents = lease_path.read_bytes()
                    ready = await amend(0)
                    linked = ready['successor_definition']
                    assert ready['checkpoint']['release_status'] == 'confirmed'
                    assert envelopes.identity(linked) == ready['successor_definition_sha256']
                    assert linked['amendment']['predecessor']['plan_receipt_sha256'] == old_plan
                    assert linked['amendment']['predecessor']['evidence_sha256'] == released['evidence_sha256']
                    assert linked['amendment']['predecessor']['run_id'] == run_id
                    assert all(path.read_bytes() == body for path, body in immutable.items())
                    assert lease_path.read_bytes() == lease_contents
                    assert list(lease_path.parent.glob('leases.sqlite3*')) == [lease_path]

                    async def reject(candidate, pattern, raw=False):
                        with pytest.raises(ValueError, match=pattern):
                            if raw:
                                await asyncio.to_thread(task_preparation, state.project('demo'), state.root, 'prepare',
                                                        {'definition': candidate})
                            else:
                                await asyncio.to_thread(tasks.prepare, state, 'demo', candidate, 1)
                        assert (await asyncio.to_thread(tasks.preparation, state, 'demo', 'revised-task'))['status'] == 'not_recorded'

                    ingress = lease_path.parent
                    original_mode = stat.S_IMODE(ingress.stat().st_mode)
                    try:
                        for shared_mode in (0o770, 0o707):
                            ingress.chmod(shared_mode)
                            blocked = await amend(1)
                            assert blocked['checkpoint']['release_status'] == 'unconfirmed'
                            assert blocked['successor_definition'] is None
                            message = 'Original ingress directory must be owned by the coordinator'
                            assert message in blocked['checkpoint']['release_error']
                            await reject(linked, message, raw=True)
                            assert lease_path.read_bytes() == lease_contents
                            assert list(ingress.iterdir()) == [lease_path]
                    finally:
                        ingress.chmod(original_mode)
                    assert (await amend(0))['successor_definition'] == linked

                    release_record = runtime / 'ergora/task-reconciliations' / f'{task_id}.result.json'
                    release_record.unlink()
                    assert (await amend(1))['checkpoint']['reconciliation_status'] == 'confirmed'
                    await reject(linked, 'confirmed original closure and durable release', raw=True)
                    assert (await asyncio.to_thread(tasks.resume_reconcile, state, 'demo', task_id, 1,
                        released['intent_sha256'], confirm=True))['status'] == 'reconciled'
                    old_receipt = activities.adapter.path('receipts', f"{task_id}/{stalled['job_id']}.json")
                    old_receipt.write_text('{}', encoding='utf-8')
                    try:
                        await reject(linked, 'confirmed original closure and durable release')
                    finally:
                        old_receipt.write_bytes(immutable[old_receipt])
                    absent = tmp_path / 'leased-evidence-offline'
                    lease_path.rename(absent)
                    try:
                        missing = await amend(1)
                        assert missing['checkpoint']['release_status'] == 'unconfirmed'
                        assert missing['successor_definition'] is None and not lease_path.exists()
                    finally:
                        absent.rename(lease_path)
                    with closing(sqlite3.connect(lease_path)) as db:
                        with db:
                            db.execute('UPDATE claims SET evidence_digest=?', ('0' * 64,))
                        before = {path: path.read_bytes() for path in lease_path.parent.glob('leases.sqlite3*')}
                        assert lease_path.with_name(lease_path.name + '-wal') in before
                        active_wal = await amend(1)
                        assert active_wal['checkpoint']['release_status'] == 'unconfirmed'
                        assert 'WAL' in active_wal['checkpoint']['release_error']
                        assert active_wal['successor_definition'] is None
                        assert {path: path.read_bytes() for path in lease_path.parent.glob('leases.sqlite3*')} == before
                    try:
                        mismatch = await amend(1)
                        assert mismatch['checkpoint']['release_status'] == 'unconfirmed'
                        assert 'no matching durable release' in mismatch['checkpoint']['release_error']
                        assert mismatch['successor_definition'] is None
                        await reject(linked, 'no matching durable release', raw=True)
                    finally:
                        with closing(sqlite3.connect(lease_path)) as db, db:
                            db.execute('UPDATE claims SET evidence_digest=?', (released['release_evidence_sha256'],))

                    stale = deepcopy(linked)
                    stale['input']['goal'] += ' Unpreviewed change.'
                    await reject(stale, 'Successor definition changed')
                    no_op = {**definition, 'task_id': revised['task_id'],
                             'budget': {**definition['budget'], 'wall_seconds': definition['budget']['wall_seconds'] + 1}}
                    no_op['amendment'] = {**linked['amendment'], 'definition_sha256': envelopes.identity(no_op)}
                    await reject(no_op, 'requires a substantive change', raw=True)
                    wrong_issue = {**revised, 'issue_id': '2'}
                    wrong_issue['amendment'] = {**linked['amendment'], 'definition_sha256': envelopes.identity(wrong_issue)}
                    await reject(wrong_issue, 'keep the original native issue', raw=True)
                    predecessor = linked['amendment']['predecessor']
                    await reject({**linked, 'amendment': {**linked['amendment'], 'predecessor': {
                        **predecessor, 'run_id': '00000000-0000-0000-0000-000000000001'}}}, 'original submitted run', raw=True)
                    with pytest.raises(ValueError, match='original preparation owner'):
                        await asyncio.to_thread(task_creation, state.project('demo'), state.root, 'create',
                                                {'definition': linked})
                    pause.touch()
                    racing = asyncio.create_task(asyncio.to_thread(tasks.prepare, state, 'demo', linked, 1))
                    try:
                        async with asyncio.timeout(8):
                            while not reached.exists():
                                await asyncio.sleep(.025)
                        await asyncio.to_thread(projects.bind, state, 'demo', 'memory', {'tool': 'sqlite'}, 1)
                    finally:
                        release.touch()
                    with pytest.raises(ValueError, match='Project revision changed before successor authorization'):
                        await racing
                    assert (await asyncio.to_thread(tasks.preparation, state, 'demo', 'revised-task'))['status'] == 'not_recorded'
                    linked = (await amend(0, revision=2))['successor_definition']
                    assert (await asyncio.to_thread(tasks.prepare, state, 'demo', linked, 2))['status'] == 'prepared'
                    successor = await asyncio.to_thread(tasks.preview, state, 'demo', linked, 2)
                    published = await asyncio.to_thread(tasks.create, state, 'demo', linked, 2, successor['preview_sha256'],
                                                        prepare_sha256=successor['prepare_sha256'])
                    successor_input = execution_input(successor['files']['task.spec.json'])
                    assert published['amendment'] == linked['amendment']
                    assert successor_input.version == selected.version
                    assert successor_input.document['budget']['instance']['id'] != selected.document['budget']['instance']['id']
                    assert successor_input.document['budget']['instance']['scope']['definition_sha256'] == envelopes.identity(linked)

                    claim = {'tracker': successor_input.spec['request']['tracker'], 'owner': 'local-cli',
                             'task_id': 'other-task', 'spec_sha256': 'a' * 64}
                    leases = IngressLeases(lease_path)
                    try:
                        leases.acquire(**claim)
                        with pytest.raises(ValueError, match='Another ingress task owns this issue'):
                            await asyncio.to_thread(tasks.start, state, 'demo', 'revised-task', 2, published['intent_sha256'])
                        attempted = await asyncio.to_thread(tasks.submission, state, 'demo', 'revised-task')
                        assert attempted['status'] == 'prepared' and not attempted['attempt_saved']
                        leases.release(**claim, evidence_digest='b' * 64)
                    finally:
                        leases.close()
                    lost_reply.touch()
                    with pytest.raises(ValueError, match='Controlled loss after the real native start'):
                        await asyncio.to_thread(tasks.resume_start, state, 'demo', 'revised-task', 2, attempted['intent_sha256'])
                    assert (await asyncio.to_thread(tasks.submission, state, 'demo', 'revised-task'))['status'] == 'unknown'
                    second = await asyncio.to_thread(tasks.resume_start, state, 'demo', 'revised-task', 2, attempted['intent_sha256'])
                    second_handle = service.client.get_workflow_handle(second['workflow_id'], run_id=second['run_id'])
                    new_plan = await await_plan(second_handle)
                    assert old_plan != new_plan and run_id != second['run_id'] and observed_work.empty()
                    materials = await asyncio.to_thread(tasks.plan, state, 'demo', 'revised-task', run_id=second['run_id'],
                                                        plan_sha256=new_plan)
                    read_plan = next(item for item in materials['materials'] if item['name'] == 'execution-plan')
                    assert json.loads(read_plan['text']) == revised['input']
                    with pytest.raises(ValueError, match='exact plan currently awaiting'):
                        await asyncio.to_thread(tasks.approve, state, 'demo', 'revised-task', 'stale-owner', 2,
                                                run_id=second['run_id'], plan_sha256=old_plan, confirm=True)
                    assert (await asyncio.to_thread(tasks.approve, state, 'demo', 'revised-task', 'new-owner', 2,
                        run_id=second['run_id'], plan_sha256=new_plan, confirm=True))['status'] == 'requested'
                    first_new_work = await asyncio.wait_for(observed_work.get(), 8)
                    assert first_new_work['spec']['request']['input'] == revised['input']
                    assert first_new_work['unit']['instructions'] == revised['input']['work_units'][0]['instructions']
                    assert first_new_work['approved_plan']['plan_sha256'] == new_plan
                    outcome = await asyncio.wait_for(second_handle.result(), 16)
                    assert outcome['status'] == 'REVIEW_READY' and outcome['candidate_sha'] == successor_commit
                    assert {context['expected_candidate_sha'] for context in contexts.values()
                            if context['task_id'] == 'revised-task' and context['stage'].split(':')[0] in ('verify', 'review')} == {outcome['candidate_sha']}
                    assert start_calls.read_text().splitlines() == [first['workflow_id'], second['workflow_id']]
                    assert all(path.read_bytes() == body for path, body in immutable.items())
            finally:
                sys.meta_path.remove(finder)
                shutil.rmtree(interpreter)
                interpreter.symlink_to(original_venv, target_is_directory=True)

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
