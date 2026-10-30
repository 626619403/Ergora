"""Two ingress adapters must share one issue owner until safe completion."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from test_development_bridge import dev_fixture
from test_bridge import FakeTracker, FakeTransport
from common import atomic, load_config, read, read_bytes, request_spec, digest, Blocked
from bridge import Bridge, admit, reconcile
from dev_platform.contracts import canonical_sha
from dev_platform.ingress import IngressLeases, OwnershipError


class SharedIngressBridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c, self.r, self.path, self.cfg = dev_fixture(self.root)
        self.c["shared_ingress_db"] = str(self.root / "shared" / "leases.sqlite3")
        atomic(self.cfg, self.c); self.c = load_config(self.cfg)
        self.transport = FakeTransport(); self.tracker = FakeTracker()
        self.bridge = Bridge(self.c, self.transport, self.tracker)
        self.other = IngressLeases(self.c["shared_ingress_db"])

    def tearDown(self):
        self.bridge.close(); self.other.close(); self.tmp.cleanup()

    def grant(self): admit(self.c, self.path, "trusted-ci", time.time() + 3600)

    def other_claim(self):
        self.other.acquire(self.r["tracker"], "a2a:caller", "remote-task", "e" * 64)

    async def test_a2a_owner_blocks_bridge_before_start(self):
        self.other_claim(); self.grant()
        self.assertTrue(await self.bridge.tick())
        self.assertEqual(self.transport.starts, 0)
        self.assertEqual(self.bridge.db.execute("SELECT count(*) FROM runs").fetchone()[0], 0)

    async def test_unknown_cancellation_keeps_shared_owner(self):
        self.grant(); self.transport.finished = True; self.transport.phase = "CANCEL_UNCONFIRMED"
        self.assertEqual(await self.bridge.tick(), [])
        with self.assertRaises(OwnershipError): self.other_claim()
        self.bridge.close(); self.bridge = Bridge(self.c, self.transport, self.tracker)
        with self.assertRaises(OwnershipError): self.other_claim()

    async def test_review_ready_releases_only_after_safe_record(self):
        self.grant(); self.transport.finished = True; self.transport.phase = "REVIEW_READY"
        self.assertEqual(await self.bridge.tick(), [])
        self.assertEqual(self.bridge.db.execute("SELECT phase FROM runs").fetchone()[0], "DELIVERED")
        self.other_claim()
        # Re-delivery of an earlier safe receipt cannot release the new owner.
        self.assertEqual(await self.bridge.tick(), [])
        self.other.assert_held(self.r["tracker"], "a2a:caller", "remote-task", "e" * 64)

    async def test_crash_after_terminal_commit_retries_release(self):
        self.grant(); self.transport.finished = True; self.transport.phase = "REVIEW_READY"
        with patch.object(self.bridge.leases, "release", side_effect=OSError("interrupted")):
            self.assertTrue(await self.bridge.tick())
        receipt = read(Path(self.c["receipts"]) / (self.r["task_id"] + ".json"))
        self.assertTrue(receipt["safe_to_rework"])
        with self.assertRaises(OwnershipError): self.other_claim()
        self.bridge.close(); self.bridge = Bridge(self.c, self.transport, self.tracker)
        self.assertEqual(await self.bridge.tick(), [])
        self.other_claim()

    async def test_reconcile_releases_exact_terminal_owner(self):
        self.grant(); self.transport.finished = True; self.transport.phase = "NEEDS_RECONCILIATION"
        self.assertEqual(await self.bridge.tick(), [])
        evidence = {"schema_version": 1, "task_id": self.r["task_id"], "issue_id": "7",
                    "request_sha256": digest(read_bytes(self.path)), "workflow_id": "dev-task/" + self.r["task_id"],
                    "run_id": "run-one", "all_external_work_stopped": True, "operator": "trusted-owner",
                    "evidence_uri": "https://evidence.example/cleanup/7", "evidence_sha256": "f" * 64,
                    "confirmed_at": time.time()}
        evidence_path = self.root / "cleanup.json"; atomic(evidence_path, evidence)
        self.assertIn("RECONCILED", reconcile(self.c, self.r["task_id"], evidence_path))
        self.other_claim()

    async def test_orphaned_preinsert_claim_recovered_by_exact_intake(self):
        self.grant()
        self.other.acquire(self.r["tracker"], self.bridge.lease_owner, self.r["task_id"], canonical_sha(request_spec(self.r)))
        self.assertEqual(await self.bridge.tick(), [])
        self.assertEqual(self.transport.starts, 1)

    async def test_active_legacy_ledger_must_drain_before_enable(self):
        with tempfile.TemporaryDirectory() as tmp:
            c, r, path, cfg = dev_fixture(Path(tmp)); admit(c, path, "trusted-ci", time.time() + 3600)
            legacy = Bridge(c, FakeTransport(), FakeTracker())
            try: self.assertEqual(await legacy.tick(), [])
            finally: legacy.close()
            c["shared_ingress_db"] = str(Path(tmp) / "shared" / "leases.sqlite3")
            with self.assertRaisesRegex(Blocked, "Drain/reconcile"):
                Bridge(c, FakeTransport(), FakeTracker())

    async def test_shared_mode_cannot_be_disabled_for_running_task(self):
        self.grant(); self.assertEqual(await self.bridge.tick(), [])
        c = dict(self.c); c.pop("shared_ingress_db")
        with self.assertRaisesRegex(Blocked, "cannot be disabled"):
            Bridge(c, FakeTransport(), FakeTracker())

    def test_config_cannot_put_shared_db_in_agent_root(self):
        c = dict(self.c, shared_ingress_db=str(Path(self.c["outbox"]) / "leases.sqlite3"))
        atomic(self.cfg, c)
        with self.assertRaises(Blocked): load_config(self.cfg)


if __name__ == "__main__": unittest.main()
