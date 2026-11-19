"""Complete preparation through the original stage owners; no Temporal service/model."""

import asyncio
from datetime import datetime, timezone
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
    if case not in {'full', 'context', 'owner-source-artifact', 'issue-source', 'development-specialists'}:
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
    write(runtime / 'approvals/fixture-approval.json', {'schema_version': 1, 'kind': 'plan-approval',
        'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'], 'profile_sha256': app.spec['profile_sha256'],
        'plan_sha256': plan_sha, 'decision': 'approve', 'principal_type': 'human', 'actor_id': 'fixture-maintainer',
        'role': 'maintainer', 'expires_at': time.time() + 3600, 'revoked': False})
    authorization = await adapter.authorize({'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'],
        'profile_sha256': app.spec['profile_sha256'], 'plan_sha256': plan_sha, 'receipt_id': 'fixture-approval'})
    app.approved_plan = {'plan_sha256': plan_sha, 'receipt': plan, 'approval': authorization}
    result = await original_work(root, 'materials-specialists' if selected else ('materials-issue-source' if case == 'issue-source' else 'materials'), app, activities,
        installation, state, runtime, requests, records)
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
    return {**result, 'case': case, 'complete_preparation': True, 'model_intervals': model_intervals}
