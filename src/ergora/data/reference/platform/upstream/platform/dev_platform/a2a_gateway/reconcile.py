"""Trusted operator reconciliation after independently confirming external cleanup.

The operator attestation is not self-authenticating JSON. Keep this command and
its credentials outside agent access. The backend must also prove the exact
Temporal run is terminal; a timeout or NotFound is not a cleanup proof.
"""
from datetime import datetime, timezone
import json
import re
from urllib.parse import urlsplit

from ..contracts import canonical_sha, need, SHA256


async def reconcile(store, backend, leases, a2a_task_id, proof):
    fields = {'schema_version', 'a2a_task_id', 'task_id', 'compiled_sha256', 'request_sha256',
              'workflow_id', 'run_id', 'all_external_work_stopped', 'operator', 'evidence_sha256',
              'evidence_uri', 'confirmed_at'}
    need(type(proof) is dict and set(proof) == fields, 'Invalid cleanup proof fields')
    need(type(proof['schema_version']) is int and proof['schema_version'] == 1, 'Invalid cleanup proof version')
    row = store.db.execute('SELECT * FROM tasks WHERE id=?', (a2a_task_id,)).fetchone()
    need(row is not None, 'Unknown A2A task'); row = dict(row)
    compiled = store.compiled(row); spec = compiled['spec']
    expected = {'a2a_task_id': row['id'], 'task_id': row['domain_id'], 'compiled_sha256': row['digest'],
                'request_sha256': spec['request_sha256'], 'workflow_id': 'dev-task/' + row['domain_id']}
    need(all(proof[k] == v for k, v in expected.items()), 'Cleanup proof is bound to another task/input')
    need(type(proof['run_id']) is str and 0 < len(proof['run_id']) <= 200, 'Exact runtime run ID required')
    need(row['run_id'] in (None, proof['run_id']), 'Cleanup proof run mismatch')
    need(proof['all_external_work_stopped'] is True, 'External stop must be independently confirmed')
    need(type(proof['operator']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,199}', proof['operator']), 'Operator identity required')
    need(type(proof['evidence_sha256']) is str and SHA256.fullmatch(proof['evidence_sha256']), 'Full cleanup evidence digest required')
    uri = urlsplit(proof['evidence_uri'])
    need(uri.scheme == 'https' and uri.hostname and not uri.username and not uri.password and not uri.query and not uri.fragment,
         'Use a credential-free HTTPS evidence URL without query/fragment')
    confirmed = datetime.fromisoformat(proof['confirmed_at'].replace('Z', '+00:00'))
    need(confirmed.tzinfo is not None, 'Cleanup time must include timezone')
    age = (datetime.now(timezone.utc) - confirmed).total_seconds()
    need(0 <= age <= 86400, 'Cleanup confirmation must be from the last 24 hours')
    digest = canonical_sha(proof)
    store.db.execute('CREATE TABLE IF NOT EXISTS reconciliations (task_id TEXT PRIMARY KEY, digest TEXT NOT NULL, proof TEXT NOT NULL, original_snapshot TEXT)')
    old = store.db.execute('SELECT * FROM reconciliations WHERE task_id=?', (row['id'],)).fetchone()
    owner = store.lease_owner(row['principal']); tracker = spec['request']['tracker']; spec_digest = canonical_sha(spec)
    if old:
        need(old['digest'] == digest, 'Reconciliation proof is immutable')
        snapshot = json.loads(row['snapshot'])
        leases.release(tracker, owner, row['domain_id'], spec_digest, canonical_sha(snapshot))
        store.update(row['id'], phase='RELEASED')
        return {'status': 'RECONCILED', 'a2a_task_id': row['id'], 'safe_to_rework': True}
    need(not row['safe_terminal'], 'Task is already safely terminal')
    need(row['phase'] != 'NEW', 'Unsubmitted tasks use CancelTask, not runtime reconciliation')
    leases.assert_held(tracker, owner, row['domain_id'], spec_digest)
    actual_run = await backend.lookup(spec, proof['run_id'])
    need(actual_run == proof['run_id'], 'Exact original workflow run could not be verified')
    status = await backend.poll(spec, actual_run)
    need(status.get('run_id') == actual_run and status.get('terminal') is True, 'Workflow must be proven terminal before external cleanup can release ownership')
    snapshot = {'run_id': actual_run, 'terminal': True, 'phase': 'BLOCKED', 'outcome': {
        'status': 'BLOCKED', 'task_id': row['domain_id'], 'request_sha256': spec['request_sha256'],
        'detail': 'Operator confirmed external cleanup after terminal runtime; original outcome retained in reconciliation audit.',
        'fence': {'confirmed': True, 'operator_cleanup_sha256': digest}}}
    with store.transaction():
        store.db.execute('INSERT INTO reconciliations VALUES(?,?,?,?)',
                         (row['id'], digest, json.dumps(proof, sort_keys=True, separators=(',', ':')), row['snapshot']))
        store.update(row['id'], phase='TERMINAL', run_id=actual_run, snapshot=snapshot, safe_terminal=1)
    leases.release(tracker, owner, row['domain_id'], spec_digest, canonical_sha(snapshot))
    store.update(row['id'], phase='RELEASED')
    return {'status': 'RECONCILED', 'a2a_task_id': row['id'], 'safe_to_rework': True}
