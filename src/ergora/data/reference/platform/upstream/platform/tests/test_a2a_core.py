"""Admission, recovery, ownership and trusted cleanup invariants."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

try:
    import a2a
    import httpx
    import uvicorn
except ImportError:
    raise unittest.SkipTest('Install platform/requirements-a2a.txt to run A2A tests')

from dev_platform.a2a_gateway.store import Store, strict_loads
from dev_platform.a2a_gateway.service import Gateway
from dev_platform.a2a_gateway.reconcile import reconcile
from dev_platform.contracts import canonical_sha
from dev_platform.ingress import IngressLeases
from test_a2a_http import compiled_fixture, FakeBackend


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'tasks.sqlite3')
        self.compiled = compiled_fixture('admission-task')
        self.expires = time.time() + 3600

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def test_frozen_admission_idempotency_and_conflict(self):
        first = self.store.admit(self.compiled, 'alice', self.expires)
        self.assertEqual(first, self.store.admit(self.compiled, 'alice', self.expires))
        with self.assertRaises(ValueError):
            self.store.admit(self.compiled, 'bob', self.expires)
        with self.assertRaises(ValueError):
            self.store.admit(self.compiled, 'alice', self.expires + 1)

    def test_expired_future_and_naive_expiry_rejected(self):
        for expiry in [time.time() - 1, time.time() + 8 * 86400, '2026-11-01T00:00:00']:
            with self.subTest(expiry=expiry), self.assertRaises(ValueError):
                self.store.admit(self.compiled, 'alice', expiry)

    def test_tampered_compiled_envelope_rejected(self):
        bad = copy.deepcopy(self.compiled); bad['spec']['request']['input']['goal'] = 'changed'
        with self.assertRaises(ValueError):
            self.store.admit(bad, 'alice', self.expires)

    def test_unknown_owner_and_reused_message_are_rejected(self):
        ref = self.store.admit(self.compiled, 'alice', self.expires)
        with self.assertRaises(ValueError): self.store.claim(ref, 'bob', 'm')
        row, _ = self.store.claim(ref, 'alice', 'm')
        with self.assertRaises(ValueError): self.store.claim(ref, 'alice', 'm', context_id=row['context_id'])
        self.assertIsNone(self.store.owned(row['id'], 'bob'))

    def test_initial_admission_checks_current_registry_but_recovery_uses_snapshot(self):
        with patch('dev_platform.registry.load_profile', side_effect=ValueError('Registry is unavailable')):
            with self.assertRaises(ValueError):
                self.store.admit(self.compiled, 'alice', self.expires)
        ref = self.store.admit(self.compiled, 'alice', self.expires)
        with patch('dev_platform.registry.load_profile', side_effect=ValueError('Registry changed after admission')):
            self.assertEqual(ref, self.store.admit(self.compiled, 'alice', self.expires))
            row, _ = self.store.claim(ref, 'alice', 'frozen-snapshot')
            self.assertEqual(self.compiled, self.store.compiled(row))

    def test_duplicate_json_and_nonfinite_rejected(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(ValueError): strict_loads(raw)

    def test_second_server_process_lock_rejected(self):
        self.store.acquire_server_lock()
        second = Store(self.root / 'tasks.sqlite3')
        try:
            with self.assertRaises(ValueError): second.acquire_server_lock()
        finally:
            second.close()

    def test_active_issue_cannot_be_reclaimed_by_new_task(self):
        ref = self.store.admit(self.compiled, 'alice', self.expires)
        self.store.claim(ref, 'alice', 'm1')
        second = compiled_fixture('second-task')
        other = self.store.admit(second, 'alice', self.expires)
        with self.assertRaises(ValueError): self.store.claim(other, 'alice', 'm2')


class ReconciliationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'tasks.sqlite3'); self.leases = IngressLeases(self.root / 'ingress.sqlite3')
        self.backend = FakeBackend(); self.compiled = compiled_fixture('reconcile-task')
        self.spec = self.compiled['spec']; self.ref = self.store.admit(self.compiled, 'alice', time.time() + 3600)
        self.gateway = Gateway(self.store, self.backend, self.leases)
        self.row, _ = self.store.claim(self.ref, 'alice', 'm')
        self.row = await self.gateway.refresh(self.row, allow_start=True)

    async def asyncTearDown(self):
        self.store.close(); self.leases.close(); self.tmp.cleanup()

    def proof(self):
        return {'schema_version': 1, 'a2a_task_id': self.row['id'], 'task_id': self.ref['task_id'],
                'compiled_sha256': self.ref['compiled_sha256'], 'request_sha256': self.spec['request_sha256'],
                'workflow_id': 'dev-task/' + self.ref['task_id'], 'run_id': self.row['run_id'],
                'all_external_work_stopped': True, 'operator': 'maintainer', 'evidence_sha256': 'e' * 64,
                'evidence_uri': 'https://evidence.example.com/cleanup/1',
                'confirmed_at': datetime.now(timezone.utc).isoformat()}

    async def test_live_workflow_cleanup_cannot_release(self):
        with self.assertRaises(ValueError):
            await reconcile(self.store, self.backend, self.leases, self.row['id'], self.proof())
        self.leases.assert_held(self.spec['request']['tracker'], self.store.lease_owner('alice'), self.ref['task_id'], canonical_sha(self.spec))

    async def test_terminal_cleanup_releases_only_exact_binding_and_is_replayable(self):
        self.backend.phase(self.spec, 'CANCEL_UNCONFIRMED', terminal=True, fence={'confirmed': False})
        proof = self.proof(); changed = {**proof, 'compiled_sha256': 'f' * 64}
        with self.assertRaises(ValueError):
            await reconcile(self.store, self.backend, self.leases, self.row['id'], changed)
        result = await reconcile(self.store, self.backend, self.leases, self.row['id'], proof)
        self.assertTrue(result['safe_to_rework'])
        self.assertEqual(result, await reconcile(self.store, self.backend, self.leases, self.row['id'], proof))
        changed = {**proof, 'evidence_sha256': 'd' * 64}
        with self.assertRaises(ValueError):
            await reconcile(self.store, self.backend, self.leases, self.row['id'], changed)
        self.assertEqual(self.store.owned(self.row['id'], 'alice')['phase'], 'RELEASED')
        with self.assertRaises(ValueError):
            self.leases.assert_held(self.spec['request']['tracker'], self.store.lease_owner('alice'), self.ref['task_id'], canonical_sha(self.spec))

    async def test_cleanup_without_backend_run_proof_fails_closed(self):
        self.backend.runs.clear()
        with self.assertRaises(ValueError):
            await reconcile(self.store, self.backend, self.leases, self.row['id'], self.proof())
        self.assertFalse(self.store.owned(self.row['id'], 'alice')['safe_terminal'])

    async def test_credential_bearing_evidence_url_rejected(self):
        for uri in ['http://evidence.example.com/x', 'https://user:secret@evidence.example.com/x', 'https://evidence.example.com/x?token=s']:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                await reconcile(self.store, self.backend, self.leases, self.row['id'], {**self.proof(), 'evidence_uri': uri})

    async def test_lost_lease_blocks_all_backend_operations(self):
        original = self.backend.runs[self.ref['task_id']]
        self.leases.release(self.spec['request']['tracker'], self.store.lease_owner('alice'), self.ref['task_id'], canonical_sha(self.spec), 'c' * 64)
        self.store.update(self.row['id'], cancel_requested=1)
        row = await self.gateway.refresh(self.store.owned(self.row['id'], 'alice'))
        self.assertEqual(json.loads(row['snapshot'])['phase'], 'LEASE_UNCONFIRMED')
        self.assertFalse(self.backend.cancels)
        self.assertEqual(self.backend.runs[self.ref['task_id']], original)

    async def test_expiry_during_lease_acquire_prevents_start(self):
        compiled = compiled_fixture('expiry-race-task', issue_id='8')
        ref = self.store.admit(compiled, 'alice', time.time() + 3600)
        row, _ = self.store.claim(ref, 'alice', 'expiry-race')
        with patch.object(self.store, 'admission_expired', side_effect=[False, True]):
            result = await self.gateway.refresh(row, allow_start=True)
        self.assertTrue(result['safe_terminal'])
        self.assertEqual(self.backend.starts, [self.ref['task_id']])
        self.assertTrue(json.loads(result['snapshot'])['outcome']['fence']['no_runtime_start'])

    async def test_new_empty_ledger_same_path_cannot_adopt_prior_live_claim(self):
        original_owner = self.store.lease_owner('alice')
        path = self.store.path
        self.store.close()
        path.unlink()
        self.store = Store(path)
        self.assertNotEqual(original_owner, self.store.lease_owner('alice'))
        ref = self.store.admit(self.compiled, 'alice', time.time() + 3600)
        row, _ = self.store.claim(ref, 'alice', 'replacement-ledger')
        self.store.update(row['id'], cancel_requested=1)
        gateway = Gateway(self.store, self.backend, self.leases)
        result = await gateway.refresh(self.store.owned(row['id'], 'alice'), allow_start=True)
        self.assertFalse(result['safe_terminal'])
        self.assertEqual(self.backend.starts, [self.ref['task_id']])
        self.leases.assert_held(self.spec['request']['tracker'], original_owner,
                                self.ref['task_id'], canonical_sha(self.spec))
