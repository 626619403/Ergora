"""Complete preparation through the original stage owners; no Temporal service/model."""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

from ergora import agent_runs, reference, workflow_definitions as workflows
from ergora.asset_trees import digest_tree


def prepare_graph(root, state, examples):
    source = root / 'preparation-guide'
    shutil.copytree(examples / 'composition/preparation-guide', source)
    attachment = source / 'skills/preparation-evidence/references/coverage.md'
    attachment.write_bytes(attachment.read_bytes() + b'Complete attachment range.\n' * 3000)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['version'] = '1.0.1'
    document['resources'][-1]['digest'] = digest_tree(source / 'skills/preparation-evidence')[0]
    (source / 'workflow.json').write_text(json.dumps(document))
    preparation = workflows.import_bundle(state, source)
    source = root / 'prepared-delivery'
    shutil.copytree(examples / 'composition/prepared-delivery', source)
    document = json.loads((source / 'workflow.json').read_bytes())
    document['version'] = '1.0.1'
    document['nodes'][0]['ref'].update(version='1.0.1', digest=preparation['digest'])
    (source / 'workflow.json').write_text(json.dumps(document))
    workflows.import_bundle(state, source)
    return document['id'], document['version']


async def exercise(root, case, app, activities, adapter, installation, state, runtime, requests, records):
    from agent_platform.core import read, write
    from dev_platform.adapter import sha
    from dev_platform.workflow import StopWork
    from temporalio import workflow
    from work_delivery_acceptance import exercise as original_work

    workflow.now = lambda: datetime.now(timezone.utc)

    async def call(name, value, result_type=dict):
        if name == 'dev_submit':
            job = await activities.submit(value)
            request = requests / 'task-1' / (job['job_id'] + '.json')
            # Exercise the same subprocess/installed driver as the public CLI.
            records[value['stage']] = await asyncio.to_thread(reference.executor, installation, state.root, request)
            return job
        assert name == 'dev_poll'
        return await activities.poll(value)

    app.call = call
    starting = app.spec['request']['repository']['starting_sha']
    for stage in ('inventory', 'plan'):
        if stage == 'plan' and case == 'source-artifact':
            item = next(item for item in records['inventory']['artifacts'] if item['name'] not in {
                'composition-call', 'composition-materials', 'composition-prompt', 'composition-invocation',
                'composition-mcp-scope', 'composition-mcp-audit', 'composition-resource-coverage', 'agent-selection', 'model-log'})
            (runtime / 'artifacts' / item['path']).write_bytes(b'Tampered original inventory')
        try:
            receipt = await app.stage(stage, starting,
                dependencies={'inventory': records['inventory']} if stage == 'plan' else {})
        except StopWork:
            assert (stage == 'inventory' and case == 'unread') or (stage == 'plan' and case in ('capacity', 'source-artifact'))
            failed = records[stage]
            assert failed['state'] == 'FAILED' and len(agent_runs.runs(state, 'demo')) == 1
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
        assert {source['instance'] for resource in leaf['resources'] for source in resource['sources']} == {
            '/'.join(parts[:index]) for index in range(1, len(parts) + 1)}
        assert (prepared['prompt'].encode() == (folder / 'input/prompt.txt').read_bytes()
                == (Path(invocation['output']) / 'stdin.txt').read_bytes())
        files = materials['repository']['starting']['files']
        assert materials['repository']['starting']['commit'] == starting
        for name, text in (('src/base.py', 'VALUE = 1\r\n'), ('AGENTS.md', 'Exact repository instructions.\r\n')):
            assert materials['repository']['blobs'][files[name]['git_object']]['text'] == text
        artifact = next(item for item in receipt['artifacts'] if item['name'] == 'composition-resource-coverage')
        coverage = read(runtime / 'artifacts' / artifact['path'])['attachments']
        assert any(item['covered_bytes'] > 65536 for item in coverage.values())
        assert 'approved_plan' not in materials['context']
        if case == 'issue-source':
            assert materials['issue_source'] == app.admission['issue_source']
        if stage == 'plan':
            artifacts = materials['dependency_artifacts']['inventory']
            names = set(app.spec['profile']['artifacts_by_stage']['inventory'])
            assert artifacts.keys() == names
            assert any(len(text) > 60000 and text.endswith('Complete inventory tail beyond the legacy truncation.\n')
                       for text in artifacts.values())
            for item in records['inventory']['artifacts']:
                if item['name'] in artifacts:
                    assert artifacts[item['name']] == (runtime / 'artifacts' / item['path']).read_bytes().decode('utf-8')
    plan = records['plan']
    plan_sha = sha(plan)
    write(runtime / 'approvals/fixture-approval.json', {'schema_version': 1, 'kind': 'plan-approval',
        'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'], 'profile_sha256': app.spec['profile_sha256'],
        'plan_sha256': plan_sha, 'decision': 'approve', 'principal_type': 'human', 'actor_id': 'fixture-maintainer',
        'role': 'maintainer', 'expires_at': time.time() + 3600, 'revoked': False})
    authorization = await adapter.authorize({'task_id': 'task-1', 'request_sha256': app.spec['request_sha256'],
        'profile_sha256': app.spec['profile_sha256'], 'plan_sha256': plan_sha, 'receipt_id': 'fixture-approval'})
    app.approved_plan = {'plan_sha256': plan_sha, 'receipt': plan, 'approval': authorization}
    result = await original_work(root, 'materials-issue-source' if case == 'issue-source' else 'materials', app, activities,
        installation, state, runtime, requests, records)
    if case in ('budget', 'context'):
        instance = app.admission['budget']['instance']
        owners = [runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'budget' for receipt in records.values()]
        attempts = [read(owner / 'model-attempt.json') for owner in owners if (owner / 'model-attempt.json').exists()]
        assert len(owners) == 9 and len(attempts) == len(app.admission['budget']['slots']) == 7
        assert {item['budget_sha256'] for item in attempts} == {instance['sha256']}
        assert {item['stage'] for item in attempts} == set(app.admission['budget']['slots'])
        assert all(read(owner / 'stopped.json')['cleanup_confirmed'] is True
                   and read(owner / 'collection-stopped.json')['cleanup_confirmed'] is True for owner in owners)
        result.update(budget_job_owners=len(owners), original_model_slot_attempts=len(attempts))
    if case == 'context':
        from ergora import memory, skill_assets, task_envelopes

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
    return {**result, 'case': case, 'complete_preparation': True}
