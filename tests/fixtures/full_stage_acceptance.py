"""Complete preparation through the original stage owners; no Temporal service/model."""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import ergora
import ergora.agents.runs as agent_runs
import ergora.definitions.workflows as workflows
from ergora.development import plan_methods
from ergora.development.envelopes import preparation_dags
from ergora.storage.assets import digest_tree


def prepare_graph(root, state, examples, *, concurrency=2):
    """Publish current preparation groups through the real definition library."""
    source = root / 'preparation-guide'
    shutil.copytree(examples / 'composition/preparation-guide', source)
    attachment = source / 'skills/preparation-evidence/references/coverage.md'
    attachment.write_bytes(attachment.read_bytes() + b'Complete attachment range.\n' * 3000)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['resources'][-1]['digest'] = digest_tree(source / 'skills/preparation-evidence')[0]
    for node in document['nodes']:
        group = root / ('preparation-' + node['id'])
        shutil.copytree(examples / 'composition' / group.name, group)
        definition = json.loads((group / 'workflow.json').read_bytes())
        definition['limits']['concurrency'] = concurrency
        (group / 'workflow.json').write_text(json.dumps(definition))
        saved = workflows.import_bundle(state, group)
        node['ref'].update(version=definition['version'], digest=saved['digest'])
    (source / 'workflow.json').write_text(json.dumps(document))
    saved = workflows.import_bundle(state, source)
    for name in ('prepared-delivery', 'native-development'):
        source = root / name
        shutil.copytree(examples / 'composition' / name, source)
        document = json.loads((source / 'workflow.json').read_bytes())
        document['nodes'][0]['ref'].update(version='1.1.0', digest=saved['digest'])
        (source / 'workflow.json').write_text(json.dumps(document))
        saved = workflows.import_bundle(state, source)
    return document['id'], document['version']


async def _stop_executor(daemon, requests, runtime):
    # Each original owner publishes only after reaping its own tree. Drain all
    # submitted jobs before stopping this fixture-owned dispatcher process.
    deadline = time.monotonic() + 45
    while any(not (runtime / 'receipts' / path.parent.name / path.name).exists()
              for path in requests.glob('*/*.json')):
        assert daemon.poll() is None, 'Fixture dispatcher exited before original job drain'
        assert time.monotonic() < deadline, 'Original submitted jobs did not reach terminal receipts'
        await asyncio.sleep(.05)
    if daemon.poll() is None:
        daemon.send_signal(signal.SIGINT)
    await asyncio.to_thread(daemon.wait, timeout=15)


def _preparation_rendezvous(case, app, state, runtime):
    if case not in {'full', 'context', 'owner-source-artifact', 'issue-source', 'development-specialists', 'method-addendum'}:
        return None
    groups = preparation_dags(app.admission['composition'])
    names = ('server', 'client') if case == 'development-specialists' else ('expert-a', 'expert-b')
    selected = {}
    for stage, group in groups.items():
        dag = group['dag']
        prefix = app.admission['composition']['preparation'][stage]['instance']
        peers = [prefix + '/' + name for name in names]
        assert set(peers) <= dag.members.keys()

        def ancestors(path):
            found, pending = set(), list(dag.predecessors[path])
            while pending:
                parent = pending.pop()
                if parent not in found:
                    found.add(parent)
                    pending.extend(dag.predecessors[parent])
            return found

        assert peers[0] not in ancestors(peers[1]) and peers[1] not in ancestors(peers[0])
        scopes = [{scope['path']: scope['limit'] for scope in dag.members[peer]['concurrency_scopes']} for peer in peers]
        assert all(min(scopes[0][path], scopes[1][path]) >= 2 for path in scopes[0].keys() & scopes[1].keys())
        selected[stage] = {'members': peers}
    configured = {'kind': 'fixture-preparation-rendezvous', 'control_home': str(state.root),
                  'runtime': str(runtime), 'groups': selected}
    path = state.root / 'fixture-preparation-rendezvous.json'
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(configured, sort_keys=True) + '\n')
    return configured


async def exercise(root, case, app, activities, adapter, installation, state, runtime, requests, records):
    rendezvous = _preparation_rendezvous(case, app, state, runtime)
    code = ('from pathlib import Path;from ergora.native.commands import executor;executor(Path('
            + repr(str(installation)) + '),Path(' + repr(str(state.root)) + '))')
    with (root / 'preparation-dispatcher.log').open('wb') as log:
        daemon = subprocess.Popen([sys.executable, '-P', '-c', code], stdout=log, stderr=subprocess.STDOUT)
        try:
            return await _exercise(root, case, app, activities, adapter, installation, state,
                                   runtime, requests, records, daemon, rendezvous)
        finally:
            if daemon.poll() is None:
                await _stop_executor(daemon, requests, runtime)


async def _exercise(root, case, app, activities, adapter, installation, state, runtime, requests, records, daemon, rendezvous):
    from agent_platform.core import read, write
    from dev_platform.adapter import sha
    from dev_platform.workflow import StopWork
    from temporalio import workflow
    from work_delivery_acceptance import exercise as original_work

    workflow.now = lambda: datetime.now(timezone.utc)
    workflow.wait = asyncio.wait
    selected = case == 'development-specialists'

    async def call(name, value, result_type=dict):
        if name == 'dev_submit':
            job = await activities.submit(value)
            return job
        assert name == 'dev_poll'
        async with asyncio.timeout(45):
            while (receipt := await activities.poll(value)) is None:
                assert daemon.poll() is None, 'Fixture dispatcher exited before receipt collection'
                await asyncio.sleep(.03)
        records[value['context']['stage']] = receipt
        return receipt

    app.call = call
    starting = app.spec['request']['repository']['starting_sha']
    for stage in ('inventory', 'plan'):
        if stage == 'plan' and case == 'source-artifact':
            item = next(item for item in records['inventory']['artifacts'] if item['name'] not in {
                'composition-call', 'composition-materials', 'composition-prompt', 'composition-invocation',
                'composition-mcp-scope', 'composition-mcp-audit', 'composition-resource-coverage', 'agent-selection', 'model-log'})
            (runtime / 'artifacts' / item['path']).write_bytes(b'Tampered original inventory')
        if stage == 'plan' and case == 'source-claim':
            from agent_platform import executor as native

            with native.ledger() as db, db:
                db.execute('UPDATE jobs SET session=? WHERE id=?', ('different-original-session', records['inventory']['job_id']))
        dependencies = {'inventory': records['inventory']} if stage == 'plan' else {}
        if stage == 'plan' and case == 'source-receipt':
            member = app.admission['composition']['preparation']['inventory']['instance'] + '/expert-a'
            dependencies = {'inventory': records[app.source_stage(member)]}
        try:
            receipt = await app.stage(stage, starting, dependencies=dependencies)
        except StopWork:
            assert (stage == 'inventory' and case in ('unread', 'capacity')) or (stage == 'plan' and case in ('source-artifact', 'source-claim', 'source-receipt'))
            failed = next(receipt for receipt in records.values() if receipt['state'] == 'FAILED')
            assert failed['state'] == 'FAILED' and agent_runs.runs(state, 'demo')
            if case == 'unread':
                assert 'not completely read' in failed['detail']
            else:
                assert not (runtime / 'workspaces/task-1/jobs' / failed['job_id'] / 'selected-agent/request.json').exists()
            return {'case': case, 'original_owners': True, 'failed_before_successor': True, 'detail': failed['detail']}
        folder = runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent'
        materials = read(folder / 'materials.json')
        call_record = read(folder / 'formal-call.json')
        invocation = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'output/selected-agent/invocation.json')
        prepared = workflows.inspect_input(folder / 'input', material=True)
        leaf = next(node for node in prepared['composition']['instances'] if node['path'] == call_record['member'])
        assert invocation['status'] == 'succeeded' and invocation['binding'] == call_record['selection']['binding']
        assert all(resource['text'] in prepared['prompt'] for resource in leaf['resources'])
        parts = call_record['member'].split('/')
        origins = {source['instance'] for resource in leaf['resources'] for source in resource['sources']}
        assert origins <= {'/'.join(parts[:index]) for index in range(1, len(parts) + 1)}
        assert {'root', 'root/development', 'root/development/preparation', call_record['member']} <= origins
        assert (prepared['prompt'].encode() == (folder / 'input/prompt.txt').read_bytes()
                == (Path(invocation['output']) / 'stdin.txt').read_bytes())
        files = materials['repository']['starting']['files']
        assert materials['repository']['starting']['commit'] == starting
        for name, text in (('src/base.py', 'VALUE = 1\r\n'), ('AGENTS.md', 'Exact repository instructions.\r\n')):
            assert materials['repository']['blobs'][files[name]['git_object']]['text'] == text
        artifact = next(item for item in receipt['artifacts'] if item['name'] == 'composition-resource-coverage')
        coverage = read(runtime / 'artifacts' / artifact['path'])['attachments']
        if not selected:
            assert any(item['covered_bytes'] > 65536 for item in coverage.values())
        assert 'approved_plan' not in materials['context']
        if case == 'issue-source':
            assert materials['issue_source'] == app.admission['issue_source']
        if stage == 'plan':
            if selected:
                group = app.admission['composition']['preparation']['plan']
                assert set(materials['preparation_inputs']['results']) == {
                    group['instance'] + '/' + name for name in ('contract', 'server', 'client', 'validation')}
                for source in materials['preparation_inputs']['results'].values():
                    assert source['artifacts'] == {item['name']: (runtime / 'artifacts' / item['path']).read_text()
                        for item in source['receipt']['artifacts'] if item['name'] in ('execution-plan', 'ownership-map', 'rollback-plan')}
            else:
                specialist = next(value for path, value in materials['preparation_inputs']['results'].items()
                                  if path.endswith('/expert-a'))
                assert any(len(text.encode('utf-8')) > 60000 and text.endswith('Complete planner original tail: kernel 原文，未截断。\r\n')
                           for text in specialist['artifacts'].values())
            artifacts = materials['dependency_artifacts']['inventory']
            names = set(app.spec['profile']['artifacts_by_stage']['inventory'])
            assert artifacts.keys() == names | {'preparation-sources'}
            if not selected:
                assert any(len(text) > 60000 and text.endswith('Complete inventory tail beyond the legacy truncation.\n')
                           for text in artifacts.values())
            for item in records['inventory']['artifacts']:
                if item['name'] in artifacts:
                    assert artifacts[item['name']] == (runtime / 'artifacts' / item['path']).read_bytes().decode('utf-8')
    assert [stage for stage, receipt in records.items()
            if any(item['name'] == 'behavior-baseline' for item in receipt['artifacts'])] == ['inventory']
    model_intervals = {}
    for stage in ('inventory', 'plan'):
        intervals = []
        for name in (('contract', 'server', 'client', 'validation') if selected else ('expert-a', 'expert-b')):
            member = app.admission['composition']['preparation'][stage]['instance'] + '/' + name
            receipt = records[app.source_stage(member)]
            result = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'output/selected-agent/result.json')
            intervals.append(json.loads(result['summary']))
        overlap = any(max(first['model_started_ns'], second['model_started_ns']) < min(first['model_finished_ns'], second['model_finished_ns'])
                      for index, first in enumerate(intervals) for second in intervals[index + 1:])
        if selected and stage == 'plan':
            contract = intervals[0]
            assert all(contract['model_finished_ns'] <= item['model_started_ns'] for item in intervals[1:3])
        if rendezvous is not None:
            peers = rendezvous['groups'][stage]['members']
            folder = state.root / 'fixture-preparation-rendezvous' / stage
            release = read(folder / 'release.json')
            assert release['stage'] == stage and release['members'] == peers
            assert set(release['ready']) == set(peers)
            for peer in peers:
                ready = read(folder / (peer.rsplit('/', 1)[-1] + '.ready.json'))
                receipt = records[app.source_stage(peer)]
                assert release['ready'][peer] == ready and ready['member'] == peer and ready['stage'] == stage
                assert ready['job_id'] == receipt['job_id']
                result = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'output/selected-agent/result.json')
                timing = json.loads(result['summary'])
                assert timing['model_started_ns'] <= ready['ready_at_ns'] <= release['released_at_ns'] <= timing['model_finished_ns']
                assert timing['model_finished_ns'] < ready['deadline_at'] * 1e9
        assert overlap is (case != 'serial')
        model_intervals[stage] = intervals
        receipt = records[stage]
        artifact = next(item for item in receipt['artifacts'] if item['name'] == 'preparation-sources')
        sources = read(runtime / 'artifacts' / artifact['path'])
        group = app.admission['composition']['preparation'][stage]
        assert len(sources['members']) == (5 if selected else 3) and sources['member'] == group['coordinator']
        assert sources['members'][group['coordinator']]['receipt_sha256'] is None
        for path, row in sources['members'].items():
            assert row['receipt_sha256'] == (None if path == group['coordinator'] else sha(records[row['stage']]))
            for output in row['outputs'].values():
                assert output['text'].encode('utf-8') == (runtime / 'artifacts' / output['ref']['path']).read_bytes()
        if stage == 'plan':
            assert sources['inventory']['receipt'] == records['inventory']
            assert sources['inventory']['receipt_sha256'] == sha(records['inventory'])
            assert sources['inventory']['source_artifact']['name'] == 'preparation-sources'
    await _stop_executor(daemon, requests, runtime)
    plan = records['plan']
    plan_sha = sha(plan)
    if case == 'owner-source-artifact':
        source = records['plan:' + app.admission['composition']['preparation']['plan']['instance'] + '/expert-a']
        artifact = next(item for item in source['artifacts'] if item['name'] == 'execution-plan')
        (runtime / 'artifacts' / artifact['path']).write_bytes(b'Changed after canonical plan publication')
    # The material reader runs in its native isolated process. This boundary
    # check supplies a controlled history label; it does not query a service.
    context = read(requests / 'task-1' / (plan['job_id'] + '.json'))['context']
    payload = {'project': state.project('demo'), 'control_home': str(state.root), 'task_id': 'task-1'}
    code = ("import json,sys;from ergora.development.runtime.submission import _Submission;"
            "from ergora.development.runtime.approval import _plan_materials;"
            "p=json.load(sys.stdin);s=_Submission(p['payload']);s.prepare();"
            "print(json.dumps(_plan_materials(s,{'workflow_id':'controlled-material-reader'},"
            "'controlled-run',p['context'],1,p['plan_sha256'])))")
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join((str(Path(ergora.__file__).parent.parent),
        str(installation / 'local'), str(installation / 'upstream/platform'))))
    inspected = await asyncio.to_thread(subprocess.run, [sys.executable, '-P', '-c', code],
        input=json.dumps({'payload': payload, 'context': context, 'plan_sha256': plan_sha}),
        capture_output=True, text=True, env=environment, timeout=30)
    (root / 'plan-material-reader.stdout.json').write_text(inspected.stdout)
    (root / 'plan-material-reader.stderr.txt').write_text(inspected.stderr)
    if case == 'owner-source-artifact':
        assert inspected.returncode and 'Preparation source bytes differ' in inspected.stderr
        assert not (runtime / 'approvals/fixture-approval.json').exists()
        return {'case': case, 'original_owners': True, 'failed_before_approval': True}
    assert inspected.returncode == 0, inspected.stderr
    material = json.loads(inspected.stdout)
    trusted = next(item for item in material['materials'] if item['name'] == 'preparation-sources')
    assert material['plan_sha256'] == plan_sha and json.loads(trusted['text'])['inventory']['receipt'] == records['inventory']
    method = (plan_methods.addendum(app.admission, 'controlled-method-run', plan_sha,
                {'implementation': 'Use the existing fixture parser.\r\n原始方法。\n'}) if case == 'method-addendum' else None)
    approved_sha = plan_methods.approval_digest(method) if method is not None else plan_sha
    bound_method = {'method_addendum': method} if method is not None else {}
    write(runtime / 'approvals/fixture-approval.json', {'schema_version': 1, 'kind': 'plan-approval',
        'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'], 'profile_sha256': app.spec['profile_sha256'],
        'plan_sha256': approved_sha, 'decision': 'approve', 'principal_type': 'human',
        'actor_id': 'fixture-owner' if method is not None else 'fixture-maintainer',
        'role': 'owner' if method is not None else 'maintainer', 'expires_at': time.time() + 3600, 'revoked': False,
        **bound_method})
    authorization = await adapter.authorize({'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'],
        'profile_sha256': app.spec['profile_sha256'], 'plan_sha256': approved_sha, 'receipt_id': 'fixture-approval',
        **bound_method})
    if method is not None:
        app.plan_sha256 = plan_sha
    app.approved_plan = {'plan_sha256': plan_sha, 'receipt': plan, 'approval': authorization}
    work_case = ('fixed-good' if case.startswith('fixed-candidate-check') else case if case.startswith('fixed-') else
                 'materials-specialists' if selected else 'materials-issue-source' if case == 'issue-source' else 'materials')
    result = await original_work(root, work_case, app, activities, installation, state, runtime, requests, records)
    if case == 'fixed-bad' or case.startswith('fixed-review-'):
        assert result['fixed_rejected' if case == 'fixed-bad' else 'review_rejected']
        if case == 'fixed-bad':
            assert not any(stage.startswith('review') for stage in records)
        return {**result, 'case': case}
    for stage, receipt in records.items():
        if not stage.startswith('review:'):
            continue
        materials = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent/materials.json')
        plan_sources = materials['dependency_artifacts']['plan']['preparation-sources']
        assert plan_sources == trusted['text']
        if selected:
            assert len(json.loads(plan_sources)['members']) == 5
        else:
            original = json.loads(plan_sources)['members'][app.admission['composition']['preparation']['plan']['instance'] + '/expert-a']
            assert any(output['bytes'] > 60000 and output['text'].endswith('Complete planner original tail: kernel 原文，未截断。\r\n')
                       for output in original['outputs'].values())
    if method is not None:
        hashes = {'approval_plan_sha256': approved_sha, 'method_addendum_sha256': sha(method)}
        work_method = {**hashes, 'original_plan_sha256': plan_sha, 'methods': method['methods']}
        review_method = {**hashes, 'method_addendum': method}
        consuming = []
        for stage, receipt in records.items():
            if not stage.startswith(('work:', 'review:')):
                continue
            job = runtime / 'workspaces/task-1/jobs' / receipt['job_id']
            materials = read(job / 'selected-agent/materials.json')
            payload = json.loads((job / 'selected-agent/input/task.txt').read_text().splitlines()[-1])
            invocation = read(job / 'output/selected-agent/invocation.json')
            assert payload == materials
            assert (Path(invocation['output']) / 'stdin.txt').read_bytes() == (job / 'selected-agent/input/prompt.txt').read_bytes()
            scoped = stage == 'work:implementation' or stage.startswith('review:')
            observed = materials.get('approved_plan_methods')
            if stage.startswith('review:'):
                assert observed == review_method
                assert sha(observed['method_addendum']) == observed['method_addendum_sha256']
                assert plan_methods.approval_digest(observed['method_addendum']) == observed['approval_plan_sha256']
            else:
                assert observed == (work_method if scoped else None)
            projected = materials['context']['approved_plan']['approval']
            assert projected['method_addendum_sha256'] == sha(method) and 'method_addendum' not in projected
            if scoped:
                consuming.append(stage)
        assert 'work:implementation' in consuming and any(stage.startswith('review:') for stage in consuming)
        result['method_material_consumers'] = sorted(consuming)
    if 'budget' in app.admission:
        instance = app.admission['budget']['instance']
        owners = [runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'budget' for receipt in records.values()]
        attempts = [read(owner / 'model-attempt.json') for owner in owners if (owner / 'model-attempt.json').exists()]
        assert len(owners) == len(app.admission['budget']['slots']) + 2
        assert len(attempts) == len(app.admission['budget']['slots']) == (17 if selected else 11)
        assert {item['budget_sha256'] for item in attempts} == {instance['sha256']}
        assert {item['stage'] for item in attempts} == set(app.admission['budget']['slots'])
        assert all(read(owner / 'stopped.json')['cleanup_confirmed'] is True
                   and read(owner / 'collection-stopped.json')['cleanup_confirmed'] is True for owner in owners)
        result.update(budget_job_owners=len(owners), original_model_slot_attempts=len(attempts))
        if selected:
            result.update(actual_selected_graph=True, source_input_version=app.admission['schema_version'],
                actual_manifest=app.admission['composition']['manifest'],
                selected_preparation=app.admission['composition']['preparation'],
                original_slot_and_clock=instance, original_server_reply_reconciled=True,
                all_job_owners_cleanup_confirmed=True)
    if case == 'context':
        import ergora.improvement.memory as memory
        import ergora.definitions.skills as skill_assets
        from ergora.development import envelopes as task_envelopes

        frozen = task_envelopes.selected_context(app.admission)
        assert memory.records(state, 'demo') == []
        assert skill_assets.versions(state, 'demo')['active'][0]['revision'] == 2
        calls = []
        for stage, receipt in records.items():
            if stage in ('integrate', 'verify'):
                continue
            folder = runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent'
            invocation = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'output/selected-agent/invocation.json')
            prepared = workflows.inspect_input(folder / 'input', material=True)
            materials = read(folder / 'materials.json')
            assert materials['selected_context'] == app.admission['context']
            assert frozen['memories'][0]['text'] in prepared['prompt']
            assert prepared['prompt'].encode() == (Path(invocation['output']) / 'stdin.txt').read_bytes()
            artifact = next(item for item in receipt['artifacts'] if item['name'] == 'composition-resource-coverage')
            coverage = read(runtime / 'artifacts' / artifact['path'])['attachments']
            selected = [item for uri, item in coverage.items() if '/selected-context/skills/' in uri]
            assert selected and all(item['covered_bytes'] == item['size'] for item in selected)
            calls.append(stage)
        assert len(calls) == len(app.admission['budget']['slots'])
        result.update(selected_context_calls=calls, canonical_changed_after_intent=True,
                      original_input_sha256=task_envelopes.identity(app.admission))
    if case.startswith('fixed-candidate-check'):
        result['independent_check'] = await _candidate_check(
            root, state, runtime, app.spec, result['candidate'], records,
            gated=case.startswith('fixed-candidate-check-graph'), recoverable=case.endswith('-recoverable'),
            wait_recovery=case.endswith('-wait-recoverable'))
    return {**result, 'case': case, 'complete_preparation': True, 'model_intervals': model_intervals}


async def _candidate_check(root, state, runtime, spec, candidate, records, *, gated=False,
                           recoverable=False, wait_recovery=False):
    """Recheck a real formal candidate and fence a live checker by its original job."""
    from types import SimpleNamespace

    from agent_platform.core import read, write
    from temporalio.client import WorkflowExecutionStatus
    from ergora.development import verification
    from ergora.development.review import packets, requests
    from ergora.development.runtime.export import _Export
    from ergora.development.runtime.submission import _Submission
    from ergora.runtime import processes

    project = state.project('demo')
    original = {'project': project, 'control_home': str(state.root), 'task_id': 'task-1'}
    submission = _Submission(original)
    submission.prepare()
    run_id = 'controlled-candidate-check-origin'
    write(submission.intent_path, submission.expected)
    write(submission.attempt_path, submission.attempt(submission.expected))
    write(submission.result_path, submission.receipt(submission.expected, run_id))
    export = {**original, 'run_id': run_id, 'candidate_sha': candidate, 'branch': 'fixture-export'}
    prepared = await _Export({**export, 'operation': 'prepare'}).run()
    exporter = _Export({**export, 'operation': 'dispatch', 'intent_sha256': prepared['export']['intent_sha256']})
    base = spec['request']['repository']['base_sha']
    verify = records['verify']
    assert verify['state'] == 'SUCCEEDED' and all(receipt['state'] == 'SUCCEEDED'
                                                 for stage, receipt in records.items() if stage.startswith('review:'))

    async def lookup(saved, selected):
        assert saved == submission.expected and selected == run_id

        async def result(*, follow_runs, rpc_timeout):
            assert follow_runs is False
            return {'status': 'REVIEW_READY', 'task_id': 'task-1', 'task_type': spec['request']['task_type'],
                    'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
                    'base_sha': base, 'candidate_sha': candidate}

        return SimpleNamespace(result=result), SimpleNamespace(status=WorkflowExecutionStatus.COMPLETED), None

    exporter.submission.lookup_run = lookup
    exported = await exporter.run()
    assert exported['status'] == 'exported' and exported['candidate_sha'] == candidate

    installed = workflows.install_preset(state, 'engineering-review')
    ref, = (item for item in installed['workflows'] if item['id'] == 'ergora-correctness-review')
    selected = workflows.get(state, ref['id'], ref['version'])['definition']
    wrapper = root / 'candidate-check-wrapper'
    wrapper.mkdir()
    definition = {'schema_version': 2, 'id': 'candidate-check-wrapper', 'version': '1.0.0',
        'description': 'Review one exported candidate.', 'resources': [],
        'permissions': selected['permissions'], 'limits': selected['limits'], 'inputs': ['task'],
        'nodes': [{'id': 'correctness', 'ref': {key: ref[key] for key in ('kind', 'id', 'version', 'digest')},
                   'depends_on': [], 'inputs': {'task': {'input': 'task'}}}],
        'outputs': {'result': {'node': 'correctness', 'output': 'result'}}}
    if gated:
        definition['inputs'].append('check')
        definition['nodes'][0]['depends_on'].append('verify')
        definition['nodes'].insert(0, {'id': 'verify', 'operation': 'verify-fixed-check', 'depends_on': [],
                                       'inputs': {'source': {'input': 'check'}}})
        definition['outputs']['proof'] = {'node': 'verify', 'output': 'result'}
    write(wrapper / 'workflow.json', definition)
    workflows.import_bundle(state, wrapper)
    manifest = workflows.prepare_manifest(state.root, 'candidate-check-wrapper', '1.0.0',
        {'schema_version': 1, 'permissions': selected['permissions'], 'limits': selected['limits']}, root / 'check-manifest')
    requirements, packet = root / 'check-requirements.md', root / 'check-packet'
    requirements.write_text('Review the exact exported fixture candidate.', encoding='utf-8')
    material = packets.prepare(Path(project['repo']), repository_id='fixture/local', base=base, head=candidate,
                               requirements=requirements, destination=packet)
    instance = 'root/correctness/review'
    if not gated:
        input_record = requests.prepare(packet, source_kind='local', source_sha256=material['packet_sha256'],
            manifest=Path(manifest['path']), manifest_digest=manifest['digest'], instance=instance,
            destination=root / 'candidate-review-input', max_prompt_bytes=100_000)
        assert input_record['execution_authorized'] is False
    source = {'task_id': 'task-1', 'run_id': run_id, 'candidate_sha': candidate,
              'export_intent_sha256': exported['intent_sha256'],
              'verification_sha256': verification.snapshot(project)['sha256'],
              'packet': str(packet), 'packet_sha256': material['packet_sha256'],
              'manifest': manifest['path'], 'manifest_digest': manifest['digest'], 'instance': instance,
              'wall_seconds': 70, 'cleanup_seconds': 8}
    source_path = root / 'candidate-check.json'
    source_raw = (json.dumps(source, ensure_ascii=False) + '\r\n').encode('utf-8')
    source_path.write_bytes(source_raw)
    source_sha = hashlib.sha256(source_raw).hexdigest()
    cli = [sys.executable, '-P', '-c', 'from ergora.interfaces.cli import main;raise SystemExit(main())', '--home', str(state.root)]
    command = ['task', 'candidate-check', 'demo']
    options = ['--request', str(source_path), '--revision', str(project['revision']), '--request-sha256', source_sha]
    original_approvals = {path.name: path.read_bytes() for path in (runtime / 'approvals').glob('*.json')}
    original_runs = agent_runs.runs(state, 'demo')

    async def call(*args, code=0):
        result = await asyncio.to_thread(subprocess.run, [*cli, *args], capture_output=True, text=True, timeout=30)
        assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def locations(queued):
        kind = 'fixed-candidate-check'
        job_id = queued['job_id']
        scope = job_id.rsplit('-', 1)[0]
        request = runtime / 'requests' / kind / scope / (job_id + '.json')
        permit = runtime / 'approvals' / kind / (scope + '.json')
        workspace = runtime / 'workspaces' / kind / scope / 'jobs' / job_id
        return request, permit, workspace

    assert 'explicit operator confirmation' in await call(*command, 'pass-check', *options, code=2)
    assert not list((runtime / 'approvals/fixed-candidate-check').glob('*.json'))
    queued = await call(*command, 'pass-check', *options, '--confirm')
    request, permit, workspace = locations(queued)
    original_permit, original_request = permit.read_bytes(), request.read_bytes()
    admission = read(permit)
    assert admission['request_text'].encode('utf-8') == source_raw and queued['request_file_sha256'] == source_sha
    assert 'approved_plan' not in read(request)['context'] and 'policy' not in admission['budget']
    assert await call(*command, 'pass-check', *options, '--confirm') == queued
    changed = root / 'candidate-check-changed.json'
    changed.write_bytes(source_raw + b' ')
    changed_options = ['--request', str(changed), '--revision', str(project['revision']), '--request-sha256']
    assert 'bytes differ' in await call(*command, 'pass-check', *changed_options, source_sha, '--confirm', code=2)
    changed_sha = hashlib.sha256(changed.read_bytes()).hexdigest()
    assert 'different original authorization' in await call(*command, 'pass-check', *changed_options, changed_sha, '--confirm', code=2)
    assert permit.read_bytes() == original_permit and request.read_bytes() == original_request

    executor = ['reference', 'executor', '--project', 'demo', '--request']
    receipt = await call(*executor, str(request))
    passed = await call('task', 'candidate-check-status', 'demo', 'pass-check', '--job-sha256', queued['job_sha256'])
    assert receipt['state'] == 'SUCCEEDED' and passed['status'] == 'succeeded' and passed['cleanup_confirmed']
    assert passed['fixed_check_ids'] == ['configuration-integrity', 'follow-up']
    assert await call(*command, 'pass-check', *options, '--confirm') == passed
    assert permit.read_bytes() == original_permit and request.read_bytes() == original_request
    assert not (workspace / 'budget/model-attempt.json').exists()
    formal_artifact = next(item for item in verify['artifacts'] if item['name'] == 'check-results')
    scoped = read(runtime / 'artifacts/fixed-candidate-check' / receipt['artifacts'][0]['path'])
    formal = read(runtime / 'artifacts' / formal_artifact['path'])
    assert set(scoped) == {'schema_version', 'kind', 'candidate_sha', 'verification'}
    assert formal['candidate_sha'] == scoped['candidate_sha'] == candidate
    for ident, observed in scoped['verification']['checks'].items():
        expected = formal['verification']['checks'][ident]
        assert observed['input']['repository'] == expected['input']['repository']
        assert observed['input']['cases'] == expected['input']['cases']
        assert observed['input']['subject']['check_sha256'] == expected['input']['subject']['check_sha256']
        assert observed['process']['name'] != expected['process']['name']
        assert observed['observations'] == expected['observations']

    queued = await call(*command, 'stop-check', *options, '--confirm')
    request, _, workspace = locations(queued)
    (root / 'hold-candidate-check').write_text(queued['job_sha256'], encoding='utf-8')
    stop = ['task', 'candidate-check-stop', 'demo', 'stop-check', '--job-sha256', queued['job_sha256'], '--confirm']
    native = runtime / 'processes'
    owner = workspace / 'budget'
    with (root / 'live-check.stdout').open('wb') as out, (root / 'live-check.stderr').open('wb') as err:
        live = subprocess.Popen([*cli, *executor, str(request)], stdout=out, stderr=err)
        try:
            async with asyncio.timeout(12):
                while True:
                    markers = list(root.glob('checker-start-*.json'))
                    monitors = list(native.glob('af-oracle-' + queued['job_sha256'] + '-*'))
                    if markers and monitors and (monitors[0] / 'pid.json').exists():
                        break
                    assert live.poll() is None, 'Original check exited before its live witness'
                    await asyncio.sleep(.01)
            marker, = markers
            monitor, = monitors
            checker = read(marker)
            assert processes.identity(checker['pid']) == checker
            started = read(monitor / 'started.json')
            subject = started['binding']['subject']
            assert subject['job_sha256'] == queued['job_sha256'] and subject['check_id'] == 'configuration-integrity'
            monitor_identity = processes.identity(started['monitor_pid'])
            command_identity = read(monitor / 'pid.json')
            assert processes.identity(command_identity['pid']) == command_identity
            assert len({item['pid'] for item in (checker, monitor_identity, command_identity)}) == 3
            request_bytes, started_bytes = (monitor / 'request.json').read_bytes(), (monitor / 'started.json').read_bytes()
            assert (await call(*stop))['stop_requested']
        finally:
            if live.poll() is None and not (runtime / 'fences/fixed-candidate-check' / (request.parent.name + '.json')).exists():
                await call(*stop)
            await asyncio.to_thread(live.wait, 35)

    finished = await call('task', 'candidate-check-status', 'demo', 'stop-check')
    assert finished['stop_requested'] and finished['status'] in ('cancelled', 'unknown')
    assert finished['status'] == ('unknown' if live.returncode == 2 else 'cancelled') and live.returncode in (1, 2)
    stopped = read(owner / 'stopped.json')
    assert stopped['cleanup_confirmed'] is True and stopped['job_sha256'] == queued['job_sha256']
    if finished['status'] == 'cancelled':
        assert finished['cleanup_confirmed'] is True
    else:
        assert finished['outer_cleanup_confirmed'] is True and finished['cleanup_confirmed'] is None
    identities = [checker, monitor_identity, command_identity]
    for original_identity in identities:
        try:
            observed = processes.identity(original_identity['pid'])
        except (OSError, ValueError):
            continue
        assert observed != original_identity, 'Original checker or monitor remains alive'
    assert not list(workspace.glob('output/*/observations.json'))
    assert await call(*command, 'stop-check', *options, '--confirm') == finished
    await call(*executor, str(request), code=live.returncode)
    assert (monitor / 'request.json').read_bytes() == request_bytes
    assert (monitor / 'started.json').read_bytes() == started_bytes
    assert list(root.glob('checker-start-*.json')) == [marker]
    assert list(native.glob('af-oracle-' + queued['job_sha256'] + '-*')) == [monitor]
    assert not (runtime / 'fences/task-1.json').exists()
    assert agent_runs.runs(state, 'demo') == original_runs
    assert {path.name: path.read_bytes() for path in (runtime / 'approvals').glob('*.json')} == original_approvals
    result = {'same_observations': True, 'passing_receipt': passed, 'stop': finished, 'original_starts': 1,
              'stopped_identities': identities, 'outer_cleanup_confirmed': stopped['cleanup_confirmed'],
              'native_started_sha256': hashlib.sha256(started_bytes).hexdigest(), 'request_file_sha256': source_sha,
              'owner_stopped_sha256': hashlib.sha256((owner / 'stopped.json').read_bytes()).hexdigest()}
    if gated:
        async def authorize_wait():
            queued = await call(*command, 'wait-check', *options, '--confirm')
            return queued, *locations(queued)

        async def execute_wait(request):
            return await call(*executor, str(request))

        result['graph'] = await _candidate_check_graph(
            root, state, runtime, packet, material['packet_sha256'], manifest, passed, finished,
            call, authorize_wait, execute_wait, recoverable=recoverable, wait_recovery=wait_recovery)
    return result


async def _candidate_check_graph(root, state, runtime, packet, packet_digest, manifest, passed, stopped, call,
                                 authorize_wait, execute_wait, *, recoverable=False, wait_recovery=False):
    """The graph reads actual native evidence before its one controlled reviewer."""
    from contextlib import redirect_stdout, redirect_stderr
    from concurrent.futures import ThreadPoolExecutor
    from copy import deepcopy
    import io
    from threading import Event
    from unittest.mock import patch

    from ergora.agents import backends
    from ergora.development.dags import require_formal_nodes
    from ergora.development.route_errors import RouteBlocked
    from ergora.interfaces.cli import main
    from ergora.runtime import processes

    task = await call('review', 'prepare-graph-task', str(packet), '--source-sha256', packet_digest,
                      '--manifest', manifest['path'], '--manifest-digest', manifest['digest'])
    assert task['execution_authorized'] is False and task['instance'] == 'root/correctness/review'
    compiled = workflows.inspect_manifest(Path(manifest['path']), material=True)['composition']
    try:
        require_formal_nodes(compiled)
    except RouteBlocked as error:
        assert error.instance == 'root/verify'
    else:
        raise AssertionError('Formal route admitted a standalone review gate')
    direct_task = root / 'direct-review-task.txt'
    direct_task.write_text('Unbound review', encoding='utf-8')
    assert 'gated graph' in await call('composition', 'prepare-from-manifest', manifest['path'], task['instance'],
                                     '--task', str(direct_task), '--max-prompt-bytes', '30000',
                                     '--directory', str(root / 'direct-review'), code=2)
    keys = ('operation_id', 'request_file_sha256', 'job_sha256', 'candidate_sha', 'receipt_sha256', 'fixed_results_sha256')
    inputs = {'task': task['task'], 'check': {key: passed[key] for key in keys}}
    original_namespaces = ['approvals', 'requests', 'receipts', 'fences', 'workspaces', 'artifacts']

    def check_records():
        dirs = [runtime / name / 'fixed-candidate-check' for name in original_namespaces]
        dirs.append(runtime / 'processes')
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for directory in dirs for path in directory.rglob('*') if path.is_file() and not path.is_symlink()}

    before, before_runs = check_records(), agent_runs.runs(state, 'demo')
    reviewer_code = '''import json,sys
from pathlib import Path
value = json.loads(sys.stdin.read().split('Workflow task port (JSON value):\\n')[-1])
with Path(sys.argv[2]).open('a', encoding='utf-8') as log:
    log.write(json.dumps(value) + '\\n')
Path(sys.argv[1]).write_text(json.dumps({'summary':'Exact candidate reviewed','decision':'approve',
    'artifacts':{'response':'Controlled advisory review'}}), encoding='utf-8')
'''
    calls = root / 'graph-reviewer-calls.jsonl'
    code = root / 'graph-reviewer.py'
    code.write_text(reviewer_code, encoding='utf-8')
    if recoverable:
        original, start_wait = passed, None
        if wait_recovery:
            original, request, permit, workspace = await authorize_wait()
            assert original['status'] == 'queued' and original['receipt_sha256'] is None
            original_request, original_permit = request.read_bytes(), permit.read_bytes()
            inputs['check'] = {**{key: original[key] for key in keys[:4]}, 'wait_seconds': 45}

            async def start_wait(observed):
                assert observed == {key: original[key] for key in ('status', 'job_id', 'job_sha256', 'request_file_sha256')}
                assert not (workspace / 'budget/attempt.json').exists()
                receipt = await execute_wait(request)
                assert receipt['state'] == 'SUCCEEDED' and receipt['job_id'] == original['job_id']
                assert request.read_bytes() == original_request and permit.read_bytes() == original_permit
                return receipt

        job_id = original['job_id']
        terminal = runtime / 'receipts/fixed-candidate-check' / job_id.rsplit('-', 1)[0] / (job_id + '.json')
        return await _recover_fixed_graph(root, state, manifest, inputs, code, calls, check_records, terminal,
                                          start_wait=start_wait)
    original_command = backends.CodexBackend.command
    native_run, lifetimes = processes.run, []
    read_entry = 'from ergora.development.runtime.candidate_checks import main;main()'

    def controlled_command(backend, request):
        argv, prompt = original_command(backend, request)
        assert argv[argv.index('--sandbox') + 1] == 'read-only'
        return [sys.executable, str(code), argv[argv.index('--output-last-message') + 1], str(calls)], prompt

    def graph(name, values, expected, *, pending=None):
        serialized, directory = root / (name + '.inputs.json'), root / (name + '-graph')
        serialized.write_text(json.dumps(values), encoding='utf-8')
        stdout, stderr = io.StringIO(), io.StringIO()

        def observe_run(argv, *args, **kwargs):
            lifetimes.append((argv[-1], kwargs.get('deadline'), kwargs.get('stop_requested')))
            if pending is not None and argv[-1] == read_entry:
                # Signal the fixture only after the real proof child has read the original queued Job.
                probe = f'''from pathlib import Path
from ergora.development.runtime import candidate_checks
observe = candidate_checks._observe
marker = Path({str(pending)!r})
async def observed(*args, **kwargs):
    original = await observe(*args, **kwargs)
    if original['status'] == 'queued' and not marker.exists():
        temporary = marker.with_suffix('.pending')
        temporary.write_text(original['job_sha256'], encoding='utf-8')
        temporary.replace(marker)
    return original
candidate_checks._observe = observed
candidate_checks.main()
'''
                argv = [*argv[:-1], probe]
            return native_run(argv, *args, **kwargs)

        with redirect_stdout(stdout), redirect_stderr(stderr), patch.object(backends.CodexBackend, 'command', controlled_command), \
             patch.object(backends.CodexBackend, 'check_invocation', lambda self: None), patch.object(processes, 'run', observe_run):
            status = main(['--home', str(state.root), 'composition', 'run-graph', 'demo', manifest['path'],
                           '--inputs', str(serialized), '--manifest-digest', manifest['digest'],
                           '--directory', str(directory), '--max-prompt-bytes', '100000', '--timeout', '15'])
        assert status == expected, (stdout.getvalue(), stderr.getvalue())
        return json.loads(stdout.getvalue()), directory

    good, directory = graph('bound', inputs, 0)
    proof = good['outputs']['proof']
    assert all(proof[key] == value for key, value in inputs['check'].items())
    assert proof['task_sha256'] == task['task_sha256'] and proof['instance'] == task['instance']
    assert proof['packet_sha256'] == packet_digest and proof['manifest_digest'] == manifest['digest']
    assert good['verification_reads'][0]['evidence'] == proof and not good['formal_execution_authorized']
    assert json.loads(calls.read_bytes()) == inputs['task']
    native_read, reviewer = lifetimes
    assert native_read[0] == read_entry
    assert native_read[1] == reviewer[1] and native_read[2] == reviewer[2] and callable(native_read[2])
    leaf, = good['leaves']
    assert leaf['instance'] == task['instance'] and leaf['status'] == 'succeeded'
    reviewed = agent_runs.inspect_run(state, 'demo', leaf['run_id'])['run']
    assert reviewed['role'] == 'reviewer' and reviewed['formal_execution_authorized'] is False
    for operation in ('check-input', 'run-input'):
        refused = await call('composition', operation, 'demo', str(directory / 'input-1'),
                             '--input-digest', leaf['input_digest'], code=2)
        assert 'requires its gated graph coordinator' in refused
    inspect = ['composition', 'inspect-graph', 'demo', str(directory), '--manifest-digest', manifest['digest']]
    inspected = await call(*inspect)
    assert inspected['verification_reads'][0]['recorded_evidence']['fixed_results_sha256'] == passed['fixed_results_sha256']
    saved_graph = directory / 'run.json'
    original_graph = saved_graph.read_bytes()
    try:
        for revision in (good['project_revision'] + 1, float(good['project_revision'])):
            changed = deepcopy(good)
            changed['verification_reads'][0]['evidence']['project_revision'] = revision
            saved_graph.write_text(json.dumps(changed), encoding='utf-8')
            observed = await call(*inspect)
            readback, = observed['verification_reads']
            assert readback['recorded_evidence']['state'] == 'mismatch'
            assert readback['original_receipt']['state'] == 'not_queried'
            assert observed['agent_attempts'][0]['original_run']['result']['state'] == 'available'
    finally:
        saved_graph.write_bytes(original_graph)

    cases = []
    def blocked(name, values, message):
        reviewer_bytes = calls.read_bytes()
        run, _ = graph(name, values, 1)
        assert run['status'] == 'failed' and message in run['error']
        assert run['leaves'] == [] and calls.read_bytes() == reviewer_bytes
        cases.append(name)

    changed = deepcopy(inputs)
    changed['task']['material']['packet']['requirements']['text'] += ' substituted'
    blocked('wrong-requirements', changed, 'root task differs')
    changed = deepcopy(inputs)
    changed['task']['material']['packet']['repository']['head'] = '0' * 40
    blocked('wrong-head', changed, 'root task differs')
    changed = deepcopy(inputs)
    changed['task']['source_sha256'] = '2' * 64
    blocked('wrong-task-packet', changed, 'Graph packet differs')
    changed = deepcopy(inputs)
    changed['check']['receipt_sha256'] = '1' * 64
    blocked('wrong-receipt', changed, 'locator differs')
    packet_path = packet / 'packet.json'
    raw = packet_path.read_bytes()
    try:
        packet_path.write_bytes(raw + b' ')
        blocked('changed-packet', inputs, 'packet differs from expected SHA256')
    finally:
        packet_path.write_bytes(raw)
    job_id = passed['job_id']
    terminal = runtime / 'receipts/fixed-candidate-check' / job_id.rsplit('-', 1)[0] / (job_id + '.json')
    raw = terminal.read_bytes()
    try:
        terminal.unlink()
        blocked('missing-receipt', inputs, 'completed passing original fixed check')
    finally:
        terminal.write_bytes(raw)
    changed = deepcopy(inputs)
    changed['check'] = {key: stopped.get(key) or '0' * 64 for key in keys}
    blocked('nonpassing-original', changed, 'completed passing original fixed check')
    assert check_records() == before and len(agent_runs.runs(state, 'demo')) == len(before_runs) + 1

    queued, request, permit, workspace = await authorize_wait()
    assert queued['status'] == 'queued' and queued['receipt_sha256'] is None
    original_request, original_permit = request.read_bytes(), permit.read_bytes()
    queued_records, reviewer_bytes = check_records(), calls.read_bytes()
    source = {key: queued[key] for key in keys[:4]}
    wait_inputs = {'task': task['task'], 'check': {**source, 'wait_seconds': 10}}

    def while_queued(name, expected, action):
        marker = root / (name + '.reader-queued')
        ended = Event()

        def observe_pending():
            while not marker.exists():
                assert not ended.wait(.01), 'Graph exited before observing the queued Job'
            assert marker.read_text(encoding='utf-8') == queued['job_sha256']
            return action()

        with ThreadPoolExecutor(max_workers=1) as pool:
            owner = pool.submit(observe_pending)
            try:
                result, directory = graph(name, wait_inputs, expected, pending=marker)
            finally:
                ended.set()
            return result, directory, owner.result()

    expiry_marker = root / 'wait-expired.reader-queued'
    short_wait = {'task': task['task'], 'check': {**source, 'wait_seconds': 3}}
    timed_out, _ = graph('wait-expired', short_wait, 1, pending=expiry_marker)
    assert expiry_marker.read_text(encoding='utf-8') == queued['job_sha256']
    cancelled, _, _ = while_queued('wait-stopped', 1, lambda: os.kill(os.getpid(), signal.SIGINT))
    for result, status, locator in ((timed_out, 'timed_out', short_wait['check']),
                                    (cancelled, 'cancelled', wait_inputs['check'])):
        assert result['status'] == status and result['leaves'] == [] and 'outputs' not in result
        readback, = result['verification_reads']
        assert readback['source'] == locator and readback['status'] == status and 'evidence' not in readback
    assert check_records() == queued_records and calls.read_bytes() == reviewer_bytes
    assert not (workspace / 'budget/attempt.json').exists()

    wrong = {'task': task['task'], 'check': {**wait_inputs['check'], 'request_file_sha256': '1' * 64}}
    wrong_locator, _ = graph('wait-wrong-locator', wrong, 1)
    assert wrong_locator['status'] == 'failed' and not wrong_locator['leaves'] and 'outputs' not in wrong_locator
    assert 'locator differs' in wrong_locator['error']
    assert check_records() == queued_records and calls.read_bytes() == reviewer_bytes

    def run_original_check():
        assert check_records() == queued_records and not (workspace / 'budget/attempt.json').exists()
        receipt = asyncio.run(execute_wait(request))
        assert receipt['state'] == 'SUCCEEDED'
        return receipt, check_records()

    waited, waiting_directory, (original_receipt, finished_records) = while_queued('wait-succeeded', 0, run_original_check)
    status = await call('task', 'candidate-check-status', 'demo', queued['operation_id'], '--job-sha256', queued['job_sha256'])
    wait_proof = waited['outputs']['proof']
    assert waited['status'] == 'succeeded' and status['cleanup_confirmed'] is True and not status['stop_requested']
    assert all(wait_proof[key] == value for key, value in wait_inputs['check'].items())
    assert all(wait_proof[key] == status[key] for key in (*keys, 'job_id', 'authorization_sha256', 'verification_sha256'))
    assert wait_proof['task_sha256'] == task['task_sha256'] and wait_proof['instance'] == task['instance']
    assert wait_proof['packet_sha256'] == packet_digest and wait_proof['manifest_digest'] == manifest['digest']
    proof_read, = waited['verification_reads']
    assert proof_read['status'] == 'validated' and proof_read['source'] == wait_inputs['check'] and proof_read['evidence'] == wait_proof
    assert waited == json.loads((waiting_directory / 'run.json').read_bytes())
    inspected_wait = await call('composition', 'inspect-graph', 'demo', str(waiting_directory),
                                '--manifest-digest', manifest['digest'])
    recorded_wait, = inspected_wait['verification_reads']
    assert recorded_wait['locator'] == wait_inputs['check'] and recorded_wait['original_receipt']['state'] == 'not_queried'
    assert recorded_wait['recorded_evidence'] == {'state': 'recorded', **{key: wait_proof[key] for key in keys[4:]}}
    leaf, = waited['leaves']
    reviewed = agent_runs.inspect_run(state, 'demo', leaf['run_id'])
    assert leaf['status'] == 'succeeded' and leaf['instance'] == task['instance']
    assert reviewed['input']['digest'] == leaf['input_digest'] and reviewed['result']['sha256'] == leaf['result_sha256']
    assert [json.loads(line) for line in calls.read_bytes()[len(reviewer_bytes):].splitlines()] == [inputs['task']]
    attempt = json.loads((workspace / 'budget/attempt.json').read_bytes())
    assert attempt['job_sha256'] == queued['job_sha256'] and attempt['job_id'] == queued['job_id']
    assert not (runtime / 'fences/fixed-candidate-check' / (request.parent.name + '.json')).exists()
    assert len(list((runtime / 'processes').glob('af-oracle-' + queued['job_sha256'] + '-*'))) == len(status['fixed_check_ids'])
    assert request.read_bytes() == original_request and permit.read_bytes() == original_permit
    assert original_receipt['artifacts'][0]['sha256'] == wait_proof['fixed_results_sha256']
    assert check_records() == finished_records

    before_project = state.project('demo')
    revised = await call('project', 'correction-suggestions', 'demo', '--enabled', 'false',
                         '--revision', str(before_project['revision']))
    assert revised['revision'] == before_project['revision'] + 1
    assert revised['registration']['sha256'] == before_project['registration']['sha256']
    historical = await call('task', 'candidate-check-status', 'demo', passed['operation_id'],
                            '--job-sha256', passed['job_sha256'])
    assert historical == passed and historical['project_revision'] == before_project['revision']
    blocked('stale-project-revision', inputs, 'Graph project revision differs')
    stale = json.loads((root / 'stale-project-revision-graph/run.json').read_bytes())
    assert stale['project_revision'] == revised['revision']

    assert check_records() == finished_records and len(agent_runs.runs(state, 'demo')) == len(before_runs) + 2
    return {'review_calls': 1, 'proof_matches': True, 'original_check_records_unchanged': True, 'blocked_before_review': cases,
            'historical_check_revision': historical['project_revision'], 'revised_project_revision': revised['revision'],
            'wait': {'timed_out': timed_out['status'], 'stopped': cancelled['status'], 'wrong_locator': wrong_locator['status'],
                     'proof': wait_proof, 'reviewer_run_id': leaf['run_id'], 'original_native_effects_only': True}}


async def _recover_fixed_graph(root, state, manifest, inputs, model, calls, check_records, terminal, *, start_wait=None):
    """Interrupt only the graph coordinator and prove that native Job evidence is reread."""
    from copy import deepcopy
    from ergora.agents import native_sources
    from ergora.runtime import processes

    coordinator = r'''
import json
import os
from pathlib import Path
import signal
import sys
import time

from ergora.agents import backends, graphs
from ergora.interfaces.cli import main
from ergora.runtime import processes

phase, marker, transport, model, calls = sys.argv[1:6]
marker = Path(marker)
transport = Path(transport)
command = backends.CodexBackend.command
def reviewer(backend, request):
    argv, prompt = command(backend, request)
    assert argv[argv.index('--sandbox') + 1] == 'read-only'
    return [sys.executable, model, argv[argv.index('--output-last-message') + 1], calls], prompt
backends.CodexBackend.command = reviewer
backends.CodexBackend.check_invocation = lambda self: None

run = processes.run
def original_read(argv, *args, **kwargs):
    if argv[-1] == 'from ergora.development.runtime.candidate_checks import main;main()':
        owner = (transport.with_suffix('') / '.owner.lock').stat(follow_symlinks=False)
        inherited = os.fstat(kwargs['lock_fd'])
        assert (owner.st_dev, owner.st_ino) == (inherited.st_dev, inherited.st_ino)
        request = json.loads(args[3])
        source = request['source']
        with transport.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'deadline': kwargs['deadline'], 'operation': sys.argv[9],
                                     'at': time.monotonic(), 'source': source,
                                     'owner': [owner.st_dev, owner.st_ino]}) + '\n')
        if phase == 'complete' and 'wait_seconds' in source:
            queued = transport.with_suffix('.queued')
            probe = f"""
from pathlib import Path
import json
from ergora.development.runtime import candidate_checks
observe = candidate_checks._observe
marker = Path({str(queued)!r})
async def observe_queued(*args, **kwargs):
    result = await observe(*args, **kwargs)
    if result['status'] == 'queued' and not marker.exists():
        pending = marker.with_suffix('.queued-pending')
        pending.write_text(json.dumps({{key: result[key] for key in
            ('status', 'job_id', 'job_sha256', 'request_file_sha256')}}), encoding='utf-8')
        pending.replace(marker)
    return result
candidate_checks._observe = observe_queued
"""
            argv = [*argv[:-1], probe + argv[-1]]
    return run(argv, *args, **kwargs)
processes.run = original_read

def hold():
    staged = marker.with_suffix('.pending')
    staged.write_text(json.dumps(processes.identity(os.getpid())), encoding='utf-8')
    staged.replace(marker)
    signal.pause()
    raise AssertionError('Fixture should terminate the original coordinator')

if phase == 'incomplete':
    save = graphs._GraphRun.save
    def after_attempt(self):
        save(self)
        reads = self.receipt.get('verification_reads', ())
        if reads and reads[-1]['status'] == 'attempted':
            assert not self.receipt['leaves']
            hold()
    graphs._GraphRun.save = after_attempt
elif phase == 'proof':
    dispatch = graphs._GraphRun.dispatch_leaf
    def before_review(self, executor, node, task):
        assert node['path'] == 'root/correctness/review'
        assert self.receipt['verification_reads'][0]['status'] == 'validated'
        assert not self.receipt['leaves']
        hold()
        return dispatch(self, executor, node, task)
    graphs._GraphRun.dispatch_leaf = before_review
elif phase in ('complete', 'prepared'):
    persist = graphs._write_recovery_record
    def after_completion(directory, name, record, **kwargs):
        persist(directory, name, record, **kwargs)
        if name == 'verification-complete.json':
            if phase == 'complete':
                hold()
            marker.with_suffix('.stale').write_bytes((directory / 'run.json').read_bytes())
    graphs._write_recovery_record = after_completion
    if phase == 'prepared':
        admit = graphs._GraphRun.check_leaf_admission
        def before_reservation(self):
            settled = admit(self)
            if (self.directory / 'input-1').is_dir() and not self.receipt['leaves']:
                hold()
            return settled
        graphs._GraphRun.check_leaf_admission = before_reservation
elif phase == 'review-complete':
    collect = graphs._GraphRun.collect_finished
    def before_graph_outcome(self):
        if self.running and any(future.done() and future.result()['status'] == 'succeeded'
                                for future in self.running):
            hold()
        return collect(self)
    graphs._GraphRun.collect_finished = before_graph_outcome

raise SystemExit(main(sys.argv[6:]))
'''
    waiting = start_wait is not None
    executed = None
    before, before_runs = check_records(), agent_runs.runs(state, 'demo')
    ledger = terminal.parents[3] / 'executor.sqlite3'
    ledger_before = ledger.read_bytes()

    def ready_marker(directory, phase):
        return directory.with_suffix('.' + phase + '.ready')

    def command(directory, phase, *args):
        return [sys.executable, '-P', '-c', coordinator, phase, str(ready_marker(directory, phase)),
                str(directory.with_suffix('.native-reads')), str(model), str(calls),
                '--home', str(state.root), 'composition', *args]

    def reads(directory):
        path = directory.with_suffix('.native-reads')
        return [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []

    async def interrupt(name, phase, *, values=None):
        nonlocal executed, before, ledger_before
        directory = root / name
        values = inputs if values is None else values
        if phase == 'review-complete':
            argv = command(directory, phase, 'resume-graph', 'demo', str(directory), '--manifest-digest', manifest['digest'])
        else:
            serialized = directory.with_suffix('.inputs.json')
            serialized.write_text(json.dumps(values), encoding='utf-8')
            argv = command(directory, phase, 'run-graph', 'demo', manifest['path'], '--manifest-digest', manifest['digest'],
                           '--inputs', str(serialized), '--directory', str(directory), '--max-prompt-bytes', '100000',
                           '--timeout', '55', '--recoverable')
        marker = ready_marker(directory, phase)
        stderr_path = directory.with_suffix('.' + phase + '.stderr')
        with directory.with_suffix('.' + phase + '.stdout').open('wb') as stdout, stderr_path.open('wb') as stderr:
            process = subprocess.Popen(argv, stdout=stdout, stderr=stderr)
            try:
                async with asyncio.timeout(15):
                    if phase == 'complete' and waiting:
                        queued = directory.with_suffix('.queued')
                        while not queued.exists():
                            assert process.poll() is None and not marker.exists(), stderr_path.read_text(encoding='utf-8')
                            await asyncio.sleep(.01)
                        assert check_records() == before and ledger.read_bytes() == ledger_before
                        assert not calls.exists() and executed is None
                        executed = await start_wait(json.loads(queued.read_bytes()))
                        before, ledger_before = check_records(), ledger.read_bytes()
                    while not marker.exists():
                        assert process.poll() is None, stderr_path.read_text(encoding='utf-8')
                        await asyncio.sleep(.01)
                assert json.loads(marker.read_bytes()) == processes.identity(process.pid)
                receipt = json.loads((directory / 'run.json').read_bytes())
                assert receipt['status'] == 'incomplete'
                if phase == 'review-complete':
                    assert len(receipt['leaves']) == 1 and calls.exists()
                else:
                    assert not receipt['leaves'] and not calls.exists()
                assert (directory / 'input-1').exists() == (phase in ('prepared', 'review-complete'))
            finally:
                if process.poll() is None:
                    if marker.exists():
                        process.kill()
                    else:
                        process.terminate()
                try:
                    await asyncio.to_thread(process.wait, 25)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait, 5)
        assert process.returncode == -signal.SIGKILL
        read, = receipt['verification_reads']
        assert read['source'] == values['check']
        attempt = json.loads((directory / 'verification-attempt.json').read_bytes())
        assert read['attempt_sha256'] == native_sources.sha(attempt)
        assert attempt['source'] == values['check'] and attempt['mode'] == ('wait' if waiting else 'completed')
        assert attempt['recovery_sha256'] == receipt['recovery_sha256']
        assert (directory / 'verification-complete.json').exists() == (phase != 'incomplete')
        return directory, receipt

    async def resume(directory):
        argv = command(directory, 'resume', 'resume-graph', 'demo', str(directory), '--manifest-digest', manifest['digest'])
        return await asyncio.to_thread(subprocess.run, argv, capture_output=True, text=True, timeout=20)

    refused = []

    async def blocked(name, directory, diagnostic, *, expect_read=False):
        receipt = directory / 'run.json'
        authority = directory / 'recovery.json'
        original_receipt, original_authority = receipt.read_bytes(), authority.read_bytes()
        before_reads = reads(directory)
        prior_calls = calls.read_bytes() if calls.exists() else None
        prior_runs = agent_runs.runs(state, 'demo')
        witnesses = {path: path.read_bytes() for path in directory.glob('verification-*.json')}
        prepared = directory / 'input-1'
        prior_input = workflows.inspect_input(prepared)['digest'] if prepared.exists() else None
        completed = await resume(directory)
        assert completed.returncode == 2 and diagnostic in completed.stderr.lower(), completed.stderr
        assert receipt.read_bytes() == original_receipt and authority.read_bytes() == original_authority
        assert (workflows.inspect_input(prepared)['digest'] if prepared.exists() else None) == prior_input
        assert {path: path.read_bytes() for path in directory.glob('verification-*.json')} == witnesses
        assert not (directory / 'reservation-1.json').exists() and agent_runs.runs(state, 'demo') == prior_runs
        assert (calls.read_bytes() if calls.exists() else None) == prior_calls
        assert len(reads(directory)) == len(before_reads) + int(expect_read)
        refused.append(name)

    incomplete, pending = await interrupt('incomplete-fixed-proof', 'incomplete')
    assert pending['verification_reads'][0]['status'] == 'attempted' and not reads(incomplete)
    await blocked('incomplete', incomplete, 'original completed fixed-check proof')
    if not waiting:
        expired, _ = await interrupt('expired-fixed-proof', 'proof')
        altered, saved = await interrupt('altered-fixed-proof', 'proof')
        saved_receipt = altered / 'run.json'
        raw = saved_receipt.read_bytes()
        changed = deepcopy(saved)
        changed['verification_reads'][0]['evidence']['fixed_results_sha256'] = '0' * 64
        try:
            saved_receipt.write_text(json.dumps(changed), encoding='utf-8')
            await blocked('altered-proof', altered, 'verification progress differs')
        finally:
            saved_receipt.write_bytes(raw)

        prepared, _ = await interrupt('prepared-fixed-proof', 'prepared')
        saved_receipt = prepared / 'run.json'
        raw = saved_receipt.read_bytes()
        earlier = ready_marker(prepared, 'prepared').with_suffix('.stale').read_bytes()
        assert json.loads(earlier)['verification_reads'][0]['status'] == 'attempted'
        try:
            saved_receipt.write_bytes(earlier)
            await blocked('stale-with-prepared-input', prepared, 'attempted with dependent work already recorded')
        finally:
            saved_receipt.write_bytes(raw)

    ready, saved = await interrupt('saved-fixed-proof', 'complete')
    if waiting:
        short = {'task': inputs['task'], 'check': {**inputs['check'], 'wait_seconds': 5}}
        expired, _ = await interrupt('expired-fixed-proof', 'proof', values=short)
    attempted, = saved['verification_reads']
    assert attempted['status'] == 'attempted' and 'evidence' not in attempted
    attempt = json.loads((ready / 'verification-attempt.json').read_bytes())
    completion = json.loads((ready / 'verification-complete.json').read_bytes())
    evidence = completion['evidence']
    evidence_bytes = json.dumps(evidence, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    assert completion['attempt_sha256'] == attempted['attempt_sha256'] == native_sources.sha(attempt)
    assert completion['evidence_sha256'] == hashlib.sha256(evidence_bytes).hexdigest()
    assert attempt['started_monotonic_ns'] <= completion['validated_monotonic_ns'] < attempt['deadline_monotonic_ns']
    for key, value in inputs['check'].items():
        assert evidence[key] == value
    original_deadline, = reads(ready)
    assert original_deadline['deadline'] == attempt['deadline_monotonic_ns'] / 1_000_000_000
    if waiting:
        captured = {key: evidence[key] for key in ('receipt_sha256', 'fixed_results_sha256')}
        assert captured == {'receipt_sha256': native_sources.sha(executed),
                            'fixed_results_sha256': executed['artifacts'][0]['sha256']}
        # The pending graph progress has no completion hash yet. A changed
        # output identity with a valid proof digest must fail the native reread.
        complete_path = ready / 'verification-complete.json'
        saved_completion = complete_path.read_bytes()
        reordered = dict(evidence)
        reordered['wait_seconds'] = reordered.pop('wait_seconds')
        assert reordered == evidence and list(reordered) != list(evidence)
        altered_proofs = (
            ('changed-terminal-identity', {**evidence, 'receipt_sha256': '0' * 64}, 'locator differs'),
            ('reordered-proof', reordered, 'original native proof differs from the saved fixed-check proof'),
        )
        for name, changed_evidence, diagnostic in altered_proofs:
            changed_bytes = json.dumps(changed_evidence, ensure_ascii=False, allow_nan=False,
                                       separators=(',', ':')).encode('utf-8')
            assert changed_bytes != evidence_bytes
            try:
                complete_path.write_text(json.dumps({**completion, 'evidence': changed_evidence,
                                                      'evidence_sha256': hashlib.sha256(changed_bytes).hexdigest()}),
                                         encoding='utf-8')
                await blocked(name, ready, diagnostic, expect_read=True)
            finally:
                complete_path.write_bytes(saved_completion)
    else:
        raw_terminal = terminal.read_bytes()
        try:
            terminal.unlink()
            await blocked('missing-native-receipt', ready, 'completed passing original fixed check', expect_read=True)
        finally:
            terminal.write_bytes(raw_terminal)
    assert check_records() == before and ledger.read_bytes() == ledger_before

    authority = (ready / 'recovery.json').read_bytes()
    fixed_files = {path: path.read_bytes() for path in ready.glob('verification-*.json')}
    _, after_review = await interrupt(ready.name, 'review-complete')
    proof, = after_review['verification_reads']
    assert proof == {**attempted, 'status': 'validated', 'evidence': evidence,
                     'completion_sha256': native_sources.sha(completion)}
    original_leaf, = after_review['leaves']
    assert original_leaf['status'] == 'attempted'
    reviewer = agent_runs.inspect_run(state, 'demo', original_leaf['run_id'])
    assert reviewer['run']['status'] == 'succeeded' and reviewer['result']['available']
    assert reviewer['input']['digest'] == original_leaf['input_digest']
    reviewer_calls = calls.read_bytes()

    resumed = await resume(ready)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    result = json.loads(resumed.stdout)
    assert result['status'] == 'succeeded' and result['verification_reads'] == [proof]
    actual_proof = json.dumps(result['outputs']['proof'], ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    assert actual_proof == evidence_bytes
    leaf, = result['leaves']
    assert leaf['instance'] == 'root/correctness/review' and leaf['status'] == 'succeeded'
    assert leaf['run_id'] == original_leaf['run_id'] and leaf['result_sha256'] == reviewer['result']['sha256']
    assert agent_runs.inspect_run(state, 'demo', leaf['run_id']) == reviewer
    assert reviewer['run']['role'] == 'reviewer' and reviewer['run']['formal_execution_authorized'] is False
    assert json.loads(reviewer_calls) == inputs['task'] and calls.read_bytes() == reviewer_calls
    assert len(agent_runs.runs(state, 'demo')) == len(before_runs) + 1
    assert (ready / 'recovery.json').read_bytes() == authority
    assert {path: path.read_bytes() for path in ready.glob('verification-*.json')} == fixed_files
    observations = reads(ready)
    assert len(observations) == (5 if waiting else 4) and all(item['deadline'] == original_deadline['deadline']
                                          and item['owner'] == original_deadline['owner'] for item in observations)
    assert observations[0]['source'] == inputs['check']
    if waiting:
        completed_locator = {key: value for key, value in inputs['check'].items() if key != 'wait_seconds'}
        assert observations[1]['source'] == {**completed_locator, **captured, 'receipt_sha256': '0' * 64}
        for read in observations[2:]:
            assert read['source'] == {**completed_locator, **captured}
            assert read['deadline'] - read['at'] > 20

    read_deadline = reads(expired)[0]['deadline']
    graph_deadline = json.loads((expired / 'recovery.json').read_bytes())['deadline_monotonic_ns'] / 1_000_000_000
    assert read_deadline < graph_deadline
    await asyncio.sleep(max(0, read_deadline - time.monotonic()) + .02)
    assert time.monotonic() < graph_deadline
    await blocked('expired-read', expired, 'original fixed-check read deadline expired')
    assert len(agent_runs.runs(state, 'demo')) == len(before_runs) + 1
    assert check_records() == before and ledger.read_bytes() == ledger_before
    return {'reused_proof': True, 'native_records_unchanged': True, 'reviewer_calls': 1, 'refused': refused,
            'read_deadline': original_deadline['deadline'], 'reviewer_run_id': leaf['run_id'],
            'original_reviewer_reused': True, 'original_wait_observed': waiting and executed is not None}
