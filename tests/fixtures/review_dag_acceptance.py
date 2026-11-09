"""Exercise the real executor inside the original workflow, after its five prior stages."""

import asyncio
from datetime import datetime, timezone
import hashlib
import json

from ergora import agent_runs, task_envelopes, workflow_definitions


async def exercise(root, mode, app, activities, installation, state, runtime, requests, dependencies, candidate):
    from agent_platform import executor as original
    from agent_platform.core import read, write
    from dev_platform.workflow import StopWork
    from ergora.reference_executor import Executor, process
    from temporalio import workflow

    workflow.now = lambda: datetime.now(timezone.utc)
    jobs, receipts = {}, {}
    changed = False

    async def call(name, value, result_type=dict):
        nonlocal changed
        if name == 'dev_submit':
            path = value['stage'].removeprefix('review:')
            if path != 'root/review' and not changed:
                changed = True
                first = receipts['root/review']
                if mode == 'artifact':
                    (runtime / 'artifacts' / first['artifacts'][0]['path']).write_bytes(b'Changed source body')
                elif mode == 'receipt':
                    replaced = {**first, 'candidate_sha': 'f' * 40}
                    write(runtime / 'receipts/task-1' / (first['job_id'] + '.json'), replaced, replace=True)
                elif mode == 'request':
                    source = requests / 'task-1' / (first['job_id'] + '.json')
                    replaced = read(source)
                    replaced['context']['expected_candidate_sha'] = 'f' * 40
                    write(source, replaced, replace=True)
                elif mode == 'claim':
                    with original.ledger() as db, db:
                        db.execute('UPDATE jobs SET session=? WHERE id=?', ('different-session', first['job_id']))
                elif mode == 'binding':
                    value['review_ports']['ports']['bindings']['task'] = 'task'
            job = await activities.submit(value)
            jobs[path] = job
            # The scanner owns a single process-wide lock, then dispatches this
            # original handler to its thread pool. Do not start two scanners.
            receipt = await asyncio.to_thread(process, requests / 'task-1' / (job['job_id'] + '.json'), state.root)
            receipts[path] = receipt
            return job
        assert name == 'dev_poll'
        return await activities.poll(value)

    app.call = call
    try:
        aggregate = await app.stage('review', candidate, dependencies=dependencies)
    except StopWork:
        assert mode != 'full'
        rejected = [receipt for path, receipt in receipts.items() if path != 'root/review' and receipt['state'] == 'FAILED']
        assert rejected and 'review' not in app.results and not app.active_stages
        for receipt in rejected:
            protocol = runtime / 'workspaces/task-1/jobs' / receipt['job_id'] / 'selected-agent'
            assert not (protocol / 'request.json').exists()
            assert 'composition-review-decision' not in {item['name'] for item in receipt['artifacts']}
        if mode == 'capacity':
            assert any('size limit' in receipt['detail'] or 'input byte limit' in receipt['detail'] for receipt in rejected)
            assert len(receipts) < len(app.admission['composition']['members'])
        return {'mode': mode, 'before_model': True, 'state': 'FAILED'}
    assert mode == 'full' and set(aggregate['members']) == set(receipts)
    assert aggregate['members']['root/review']['decision'] == 'request-changes'
    assert receipts['root/review']['state'] == 'FAILED' and app.cancel_reason is None
    first = receipts['root/review']
    for path in ('root/review-1', 'root/review-2'):
        protocol = runtime / 'workspaces/task-1/jobs' / receipts[path]['job_id'] / 'selected-agent'
        materials = read(protocol / 'materials.json')
        source = materials['review_inputs']['results']['root/review']
        assert source['receipt'] == first and source['receipt_sha256'] == task_envelopes.identity(first)
        assert source['artifacts'] == {item['name']: (runtime / 'artifacts' / item['path']).read_text() for item in first['artifacts']}
        prepared = workflow_definitions.inspect_input(protocol / 'input', material=True)
        task = (protocol / 'input/task.txt').read_text()
        assert json.loads(task.splitlines()[-1]) == materials and prepared['prompt'].endswith(task)
        assert all(item['text'] in prepared['prompt'] for item in next(
            leaf for leaf in prepared['composition']['instances'] if leaf['path'] == path)['resources'])
    path = 'root/review-1'
    job = jobs[path]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for parent in (requests, runtime / 'receipts')
              for p in (parent / 'task-1').glob('*.json')}
    count = len(agent_runs.runs(state, 'demo'))
    receipt = Executor(read(requests / 'task-1' / (job['job_id'] + '.json')), state.root).execute()
    assert receipt == receipts[path] and len(agent_runs.runs(state, 'demo')) == count
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in before.items())
    assert (runtime / 'tasks/task-1/task.spec.json').read_bytes()
    return {'mode': mode, 'complete_artifacts': True, 'ancestor_materials': True, 'recovery_preserved': True}
