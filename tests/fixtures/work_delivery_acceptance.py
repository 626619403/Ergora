"""Original stage owners exercised with real processes and deterministic CLI protocols."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

import ergora
import ergora.definitions.agents as agent_definitions
import ergora.agents.runs as agent_runs
import ergora.definitions.workflows as workflows


def prepare(root, state, task_input, kind, examples, mode):
    if mode == 'composition-work-materials-development-specialists':
        import runpy
        import subprocess

        example = examples / 'composition/development-specialists'
        published = runpy.run_path(str(example / 'publish.py'))['publish'](state, example, version='1.0.0')
        definition = json.loads((example / 'task.example.json').read_bytes())
        definition.update(task_id='task-1', issue_id='1', starting_sha=subprocess.check_output(
            ['git', '-C', str(root / 'repo'), 'rev-parse', 'HEAD'], text=True).strip())
        definition['input'].update(allowed_paths=['src'])
        for unit in definition['input']['work_units']:
            unit['paths'] = ['src/' + unit['id'] + '.py']
            unit['instructions'] += ' fixture-shared-contract'
        definition['composition']['preparation']['repository_paths'] = ['src']
        definition['composition'].update(manifest=published['manifest']['path'], manifest_digest=published['manifest']['digest'])
        definition['budget'].update(wall_seconds=300, cleanup_seconds=15)
        return definition
    for path in (examples / 'agents/kernel-implementer', examples / 'agents/validation-implementer',
                 examples / 'agents/architecture-reviewer', *sorted((examples / 'composition/agents').iterdir())):
        agent_definitions.import_bundle(state, path)
    for name in ('structure-review', 'correctness-review', 'test-value-review', 'parallel-review', 'specialist-work', 'specialist-delivery'):
        workflows.import_bundle(state, examples / 'composition' / name)
    version = '1.0.0'
    if mode == 'composition-work-results':
        # A shared contract fans out, then joins. Client is a control dependency
        # without a data binding, which must still deliver its original result.
        version = '1.0.1'
        folder = root / 'expanded-work'
        workflows.export(state, 'specialist-work', '1.0.0', folder)
        document = json.loads((folder / 'workflow.json').read_bytes())
        implementation, validation, done = document['nodes']
        branches = []
        for identity in ('server', 'client'):
            branch = deepcopy(validation)
            branch['id'] = identity
            branches.append(branch)
        validation = deepcopy(validation)
        validation.update(depends_on=['server', 'client'], inputs={'task': {'node': 'server', 'output': 'result'}})
        document.update(version=version, nodes=[implementation, *branches, validation, done])
        (folder / 'workflow.json').write_text(json.dumps(document))
        saved = workflows.import_bundle(state, folder)
        folder = root / 'advisory-structure'
        workflows.export(state, 'structure-review', '1.0.0', folder)
        document = json.loads((folder / 'workflow.json').read_bytes())
        document.update(schema_version=2, version=version)
        document['nodes'][0]['review_requirement'] = 'advisory'
        document['nodes'].append({'id': 'done', 'join': 'all', 'depends_on': ['review']})
        document['outputs']['findings'] = {'node': 'done', 'output': 'result'}
        (folder / 'workflow.json').write_text(json.dumps(document))
        structure = workflows.import_bundle(state, folder)
        folder = root / 'serial-review'
        workflows.export(state, 'parallel-review', '1.0.0', folder)
        document = json.loads((examples / 'composition/serial-review/workflow.json').read_bytes())
        document.update(schema_version=2, version=version, resources=[])
        document['nodes'][0]['ref'].update(version=version, digest=structure['digest'])
        (folder / 'workflow.json').write_text(json.dumps(document))
        serial = workflows.import_bundle(state, folder)
        folder = root / 'expanded-delivery'
        workflows.export(state, 'specialist-delivery', '1.0.0', folder)
        document = json.loads((folder / 'workflow.json').read_bytes())
        document['version'] = version
        document['nodes'][0]['ref'].update(version=version, digest=saved['digest'])
        document['nodes'][1]['ref'].update(id='serial-review', version=version, digest=serial['digest'])
        (folder / 'workflow.json').write_text(json.dumps(document))
        workflows.import_bundle(state, folder)
    grant = json.loads((examples / 'composition/preview-grant.json').read_bytes())
    if mode.startswith('composition-work-materials-'):
        from full_stage_acceptance import prepare_graph

        identity, version = prepare_graph(root, state, examples, concurrency=1 if mode.endswith('-serial') else 2)
    else:
        identity = 'specialist-delivery'
    manifest = workflows.prepare_manifest(state.root, identity, version, grant, root / 'manifest')
    task_input['work_units'] = [
        {'id': 'implementation', 'depends_on': [], 'paths': ['src/new.py'], 'instructions': 'Implement the fixture'},
        {'id': 'validation', 'depends_on': ['implementation'], 'paths': ['src/validation.py'], 'instructions': 'Validate the fixture'}]
    if mode == 'composition-work-results':
        task_input['work_units'][1:1] = [
            {'id': identity, 'depends_on': ['implementation'], 'paths': ['src/' + identity + '.py'], 'instructions': 'Implement the fixture'}
            for identity in ('server', 'client')]
        task_input['work_units'][-1]['depends_on'] = ['server', 'client']
    if mode.endswith('-scope') or mode.endswith('-commit'):
        task_input['work_units'][0]['instructions'] += ' fixture-work-' + mode.rsplit('-', 1)[1]
    if mode.endswith('-recovery-tamper'):
        task_input['work_units'][0]['instructions'] += ' fixture-work-commit'
    definition = {'schema_version': 2, 'task_id': 'task-1', 'task_type': kind, 'issue_id': '1', 'input': task_input,
        'composition': {'manifest': manifest['path'], 'manifest_digest': manifest['digest'], 'review_protocol': 'dag-v1',
            'review_instance': 'root/review', 'mode': 'text-only', 'diversity': {'policy': 'allow-same'},
            'execution': {'protocol': 'work-units-v2' if mode.startswith(('composition-work-results', 'composition-work-materials-')) or mode == 'composition-work-issue-source' else 'work-units-v1',
                'instance': 'root/work', 'mode': 'workspace-task-mcp',
                'assignments': {unit['id']: 'root/work/' + unit['id'] for unit in task_input['work_units']}},
            'backend_overrides': {path: {'binding': {'tool': 'codex', 'sandbox': 'current-container'},
                                        'reason': 'Explicit trusted-container protocol acceptance'}
                                  for path in (*('root/work/' + unit['id'] for unit in task_input['work_units']),
                                               'root/review/structure/review', 'root/review/correctness/review',
                                               'root/review/test-value/review')}}}
    if mode == 'composition-work-results':
        definition['composition']['backend_overrides']['root/review/structure/review']['binding']['model'] = 'fixture-reject'
    if mode in ('composition-work-issue-source', 'composition-work-materials-issue-source'):
        from unittest.mock import patch
        import ergora.issues.backends as issue_backends
        import ergora.issues.application as issues
        import ergora.configuration.projects as projects

        revision = state.project('demo')['revision']
        projects.bind(state, 'demo', 'tracker', {'tool': 'github', 'project': 'fixtures/demo'}, revision)
        # Synthetic observation: this protocol fixture never contacts a tracker
        # or model. The independent issue tests exercise real loopback capture.
        observation = {'schema_version': 1, 'source': {'provider': 'github', 'api_url': 'https://api.github.com',
            'project': 'fixtures/demo', 'issue_id': '1'}, 'issue': {'native_id': 9001, 'title': 'Source protocol fixture',
            'body': '完整来源必须进入每个执行与审查实例。\nNo additional permissions.\n', 'state': 'open',
            'labels': ['fixture'], 'web_url': 'https://github.com/fixtures/demo/issues/1', 'updated_at': '2026-01-01T00:00:00Z'},
            'response': {'sha256': hashlib.sha256(b'synthetic-fixture-response').hexdigest(), 'etag': None}, 'context_only': True}
        with patch.object(issue_backends.GitHubBackend, 'read', return_value=observation):
            saved = issues.capture(state, 'demo', '1', revision + 1)['snapshot']
        definition.update(schema_version=3, source={'snapshot_sha256': saved['sha256']})
    if mode.startswith('composition-work-materials-'):
        definition.update(schema_version=8, budget={'wall_seconds': 300, 'cleanup_seconds': 15, 'model_invocations': 11})
        option = definition['composition']
        def nested(path):
            return 'root/development/' + path.removeprefix('root/')
        option['review_instance'] = nested(option['review_instance'])
        option['execution']['instance'] = nested(option['execution']['instance'])
        option['execution']['assignments'] = {key: nested(path) for key, path in option['execution']['assignments'].items()}
        option['backend_overrides'] = {nested(path): value for path, value in option['backend_overrides'].items()}
        option.update(native={'protocol': 'six-stage-v1', 'instance': 'root/development'},
            preparation={'protocol': 'preparation-dag-v1', 'mode': 'task-mcp', 'repository_paths': ['src'],
                **{stage: {'instance': 'root/development/preparation/' + stage,
                           'coordinator': 'root/development/preparation/' + stage + '/coordinator'}
                   for stage in ('inventory', 'plan')}})
        model = ('fixture-unread-inventory' if mode.endswith('-unread') else
                 'fixture-capacity-inventory' if mode.endswith('-capacity') else 'fixture-complete-inventory')
        for name in ('expert-a', 'coordinator'):
            option['backend_overrides']['root/development/preparation/inventory/' + name] = {
                'binding': {'tool': 'codex', 'model': model}, 'reason': 'Deterministic complete-material protocol fixture'}
        option['backend_overrides']['root/development/preparation/plan/expert-a'] = {
            'binding': {'tool': 'codex', 'model': 'fixture-complete-plan'},
            'reason': 'Complete planner original reaches the trusted plan and final measurement materials'}
        if mode.endswith('-context'):
            option['mode'] = 'task-mcp'
            import ergora.improvement.memory as memory
            import ergora.definitions.skills as skill_assets

            record = memory.save(state, 'demo', 'Frozen explicit context survives canonical deletion.',
                                 {'uri': 'repo://selected-memory', 'revision': 'fixture-v1'})
            source = root / 'selected-context-evidence'
            (source / 'references').mkdir(parents=True)
            (source / 'SKILL.md').write_text('---\nname: selected-context-evidence\ndescription: Selected full material fixture\n---\nRead references/complete.md completely.\n')
            (source / 'references/complete.md').write_bytes(b'Explicit selected Skill attachment.\n' * 2100)
            skill = skill_assets.import_bundle(state, 'demo', source)
            definition['context'] = {'root_version': '1.1.1',
                'memories': [{'id': record['id'], 'revision': record['revision']}],
                'skills': [{'name': skill['name'], 'digest': skill['digest'], 'revision': 1}]}
    return definition


async def exercise(root, case, app, activities, installation, state, runtime, requests, records):
    from agent_platform import executor as native
    from agent_platform.core import read
    from dev_platform.workflow import StopWork
    from ergora.development.runtime.executor import Executor, process
    from temporalio import workflow

    workflow.now = lambda: datetime.now(timezone.utc)
    selected = case == 'materials-specialists'
    jobs = {}

    async def call(name, value, result_type=dict):
        if name == 'dev_submit':
            stage = value['stage']
            if stage == 'work:validation' and 'source-' in case:
                first = records['work:implementation']
                if case.endswith('source-artifact'):
                    artifact = (next(item for item in first['artifacts'] if item['name'] == 'composition-prompt')
                                if case.startswith('results') else first['artifacts'][0])
                    (runtime / 'artifacts' / artifact['path']).write_bytes(b'Changed original work material')
                else:
                    with native.ledger() as db, db:
                        db.execute('UPDATE jobs SET session=? WHERE id=?', ('different-original-session', first['job_id']))
            job = await activities.submit(value)
            jobs[stage] = job
            path = requests / 'task-1' / (job['job_id'] + '.json')
            if stage == 'work:implementation' and case in ('recovery-commit', 'recovery-tamper'):
                # Crash after the actual monitored model self-commits but before
                # the trusted caller can perform its first HEAD/path gates.
                class BeforeHeadGate(BaseException):
                    pass

                executor = Executor(read(path), state.root)
                original_run = executor.sandbox.run

                def crash_after_model(name, *args, **kwargs):
                    code = original_run(name, *args, **kwargs)
                    if name.endswith('-selected'):
                        assert code == 0
                        raise BeforeHeadGate
                    return code

                executor.sandbox.run = crash_after_model
                try:
                    await asyncio.to_thread(executor.execute)
                except BeforeHeadGate:
                    pass
                else:
                    raise AssertionError('The injected pre-gate crash was not reached')
                count = len(agent_runs.runs(state, 'demo'))
                if case == 'recovery-tamper':
                    selection = runtime / 'artifacts/task-1' / job['job_id'] / 'agent-selection.json'
                    request = read(executor.scratch.parent / 'selected-agent/request.json')
                    selection.write_text(json.dumps({'role': 'implementer', 'binding': request['binding'],
                        'project_revision': executor.selection['project_revision'],
                        'prompt_sha256': request['prompt_sha256'],
                        'template_instructions_sha256': executor.spec['profile']['template_files']['instructions.md'],
                        'result_sha256': '0' * 64}))
                receipt = await asyncio.to_thread(process, path, state.root)
                assert receipt['state'] == 'FAILED', receipt
                assert len(agent_runs.runs(state, 'demo')) == count
            elif stage == 'work:implementation' and case == 'recovery':
                # Actual model/check/commit completed, but original receipt was
                # not yet published. Recover that same monitored invocation.
                first = await asyncio.to_thread(Executor(read(path), state.root).execute)
                assert first['state'] == 'SUCCEEDED', first
                count = len(agent_runs.runs(state, 'demo'))
                second = await asyncio.to_thread(Executor(read(path), state.root).execute)
                assert first == second and len(agent_runs.runs(state, 'demo')) == count
                receipt = await asyncio.to_thread(process, path, state.root)
                assert receipt == first
            elif selected and stage == 'work:server':
                # Drop the completed original reply, then reconcile the same job;
                # a second process observation must not claim another model slot.
                first = await asyncio.to_thread(process, path, state.root)
                invocation = read(runtime / 'workspaces/task-1/jobs' / job['job_id'] / 'output/selected-agent/invocation.json')
                receipt = await asyncio.to_thread(process, path, state.root)
                assert receipt == first
                assert len([run for run in agent_runs.runs(state, 'demo')
                            if run.get('input_digest') == invocation['input_digest']]) == 1
            else:
                receipt = await asyncio.to_thread(process, path, state.root)
            records[stage] = receipt
            return job
        assert name == 'dev_poll'
        return await activities.poll(value)

    app.call = call
    try:
        await app.units()
    except StopWork:
        assert case in ('source-artifact', 'source-claim', 'scope', 'commit', 'recovery-commit', 'recovery-tamper', 'results-source-artifact'), (case, records)
        stage = 'work:validation' if 'source-' in case else 'work:implementation'
        receipt = records[stage]
        assert receipt['state'] == 'FAILED' and not app.active_stages
        if 'source-' in case:
            assert not (runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent/request.json').exists()
        elif case == 'scope':
            assert 'outside approved unit' in receipt['detail']
        elif case.startswith('recovery-'):
            assert 'post-gate' in receipt['detail']
        else:
            assert 'only the trusted Executor may commit' in receipt['detail']
        return {'case': case, 'original_owners': True, 'failed_before_successor': True, 'detail': receipt['detail']}
    assert case in ('full', 'recovery', 'results', 'issue-source', 'materials', 'materials-issue-source', 'materials-specialists')
    work_stages = ['work:' + unit['id'] for unit in app.spec['request']['input']['work_units']]
    for stage in work_stages:
        receipt = records[stage]
        assert receipt['state'] == 'SUCCEEDED'
        folder = runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent'
        prepared = workflows.inspect_input(folder / 'input', material=True)
        materials = read(folder / 'materials.json')
        assert json.loads((folder / 'input/task.txt').read_text().splitlines()[-1]) == materials
        assert materials['root_task'] == app.spec['request']
        if 'issue-source' in case:
            assert materials['issue_source'] == app.admission['issue_source']
            assert json.loads((folder / 'input/task.txt').read_text().splitlines()[-1])['issue_source'] == app.admission['issue_source']
            assert materials['artifact_protocol'] == 'stage-artifacts-v1'
        assert materials['effective_write_paths'] == materials['context']['unit']['paths']
        leaf = next(item for item in prepared['composition']['instances'] if item['path'] == read(folder / 'formal-call.json')['member'])
        assert all(resource['text'] in prepared['prompt'] for resource in leaf['resources'])
        assert any(item['name'] == 'composition-native-command' for item in receipt['artifacts'])
        if selected and stage == 'work:integration-tests':
            inputs = materials['work_inputs']
            prefix = app.admission['composition']['execution']['instance'] + '/'
            assert set(inputs['results']) == {prefix + 'server', prefix + 'client'}
            assert inputs['dependencies'] == {'server': prefix + 'server', 'client': prefix + 'client'}
            for identity, source in inputs['results'].items():
                assert source['receipt'] == records['work:' + identity.rsplit('/', 1)[1]]
                assert source['artifacts'] == {item['name']: (runtime / 'artifacts' / item['path']).read_text()
                    for item in source['receipt']['artifacts'] if item['name'] in ('change-summary', 'test-results')}
        if stage.endswith('validation'):
            if case == 'results':
                sources = materials['work_inputs']
                assert sources['ports']['sources'] == ['root/work/server']
                assert sources['dependencies'] == {'server': 'root/work/server', 'client': 'root/work/client'}
                assert set(sources['results']) == {'root/work/server', 'root/work/client'}
                assert set(materials['dependency_artifacts']) == {'plan'}
                for identity, source in sources['results'].items():
                    assert source['receipt'] == records['work:' + identity.rsplit('/', 1)[1]]
                    assert set(source['artifacts']) == {'change-summary', 'test-results'}
                    assert source['artifacts'] == {item['name']: (runtime / 'artifacts' / item['path']).read_text()
                                                   for item in source['receipt']['artifacts'] if item['name'] in source['artifacts']}
            elif case == 'issue-source' or case.startswith('materials'):
                source = materials['work_inputs']['results'][app.admission['composition']['execution']['assignments']['implementation']]
                assert source['receipt'] == records['work:implementation']
                assert set(source['artifacts']) == {'change-summary', 'test-results'}
                assert 'composition-materials' not in source['artifacts']
            else:
                source = materials['work_inputs']['results']['root/work/implementation']
                assert source['receipt'] == records['work:implementation']
                assert source['artifacts'] == {item['name']: (runtime / 'artifacts' / item['path']).read_text()
                                               for item in source['receipt']['artifacts']}
    integration = await app.stage('integrate', dependencies={key: value for key, value in records.items() if key.startswith('work:')})
    candidate = integration['candidate_sha']
    verify = await app.stage('verify', candidate, dependencies={'integration': integration})
    review = await app.stage('review', candidate, dependencies={'verification': verify, 'plan': records['plan']})
    assert review['decision'] == 'approve' and len(review['members']) == 3
    for path in review['members']:
        receipt = records['review:' + path]
        folder = runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent'
        materials = read(folder / 'materials.json')
        assert materials['root_task'] == app.spec['request']
        if 'issue-source' in case:
            assert materials['issue_source'] == app.admission['issue_source']
            prepared = workflows.inspect_input(folder / 'input', material=True)
            assert json.loads((folder / 'input/task.txt').read_text().splitlines()[-1])['issue_source'] == app.admission['issue_source']
            assert materials['artifact_protocol'] == 'stage-artifacts-v1'
        if case != 'results' or path == 'root/review/structure/review':
            assert materials['review_inputs']['results'][app.admission['composition']['execution']['assignments']['integration-tests' if selected else 'validation']]['receipt'] == records['work:integration-tests' if selected else 'work:validation']
        else:
            source = materials['review_inputs']['results']['root/review/structure/review']
            assert source['receipt'] == records['review:root/review/structure/review']
            assert source['receipt']['state'] == 'FAILED'
            assert set(source['artifacts']) == {'review-report', 'handoff', 'composition-review-decision'}
            assert json.loads(source['artifacts']['composition-review-decision'])['decision'] == 'request-changes'
        assert set(materials['dependency_artifacts']) == {'verification', 'plan'}
        assert materials['candidate_sha'] == candidate
    before = len(agent_runs.runs(state, 'demo'))
    for stage in work_stages:
        receipt = records[stage]
        path = requests / 'task-1' / (receipt['job_id'] + '.json')
        if 'budget' in app.admission:
            assert await asyncio.to_thread(process, path, state.root) == receipt
        else:
            assert Executor(read(path), state.root).execute() == receipt
    assert len(agent_runs.runs(state, 'demo')) == before == len(work_stages) + 3 + len(app.admission['composition'].get('preparation', {}).get('members', {}))
    assert len({receipt['actor']['session_id'] for receipt in records.values()}) == len(records)
    if selected:
        intervals = {}
        for unit in app.spec['request']['input']['work_units']:
            receipt = records['work:' + unit['id']]
            output = read(runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'output/selected-agent/result.json')
            intervals[unit['id']] = json.loads(output['summary'])
        assert max(intervals[name]['model_started_ns'] for name in ('server', 'client')) < min(
            intervals[name]['model_finished_ns'] for name in ('server', 'client'))
        assert intervals['contract']['model_finished_ns'] <= min(intervals[name]['model_started_ns'] for name in ('server', 'client'))
        assert max(intervals[name]['model_finished_ns'] for name in ('server', 'client')) <= intervals['integration-tests']['model_started_ns']
    return {'case': case, 'original_owners': True, 'candidate': candidate, 'work_calls': len(work_stages), 'review_calls': 3,
            'complete_sources': True, 'original_call_recovery': True}
