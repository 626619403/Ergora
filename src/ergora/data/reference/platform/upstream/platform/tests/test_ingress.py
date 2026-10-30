"""Ownership is shared across entrances and survives process restart."""
import concurrent.futures
import os
from pathlib import Path
import tempfile
import unittest

from dev_platform.ingress import IngressLeases, OwnershipError


class IngressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "private" / "ingress.sqlite"
        self.tracker = {"kind": "github", "project": "org/repo", "issue_id": "7"}
        self.lease = IngressLeases(self.path)
        self.args = (self.tracker, "symphony:one", "task-1", "a" * 64)

    def tearDown(self):
        self.lease.close()
        self.tmp.cleanup()

    def test_restart_preserves_owner_and_rejects_second_ingress(self):
        self.lease.acquire(*self.args)
        other = IngressLeases(self.path)
        try:
            other.acquire(*self.args)
            with self.assertRaisesRegex(OwnershipError, "Another ingress"):
                other.acquire(self.tracker, "a2a:caller", "task-2", "b" * 64)
        finally:
            other.close()

    def test_immutable_id_cannot_change_hash(self):
        self.lease.acquire(*self.args)
        with self.assertRaisesRegex(OwnershipError, "hash differs"):
            self.lease.acquire(*self.args[:-1], "b" * 64)

    def test_release_idempotency_cannot_release_next_owner(self):
        self.lease.acquire(*self.args)
        self.lease.release(*self.args, "e" * 64)
        next_args = (self.tracker, "a2a:caller", "task-2", "b" * 64)
        self.lease.acquire(*next_args)
        self.lease.release(*self.args, "e" * 64)
        self.lease.assert_held(*next_args)
        with self.assertRaisesRegex(OwnershipError, "evidence differs"):
            self.lease.release(*self.args, "f" * 64)
        with self.assertRaisesRegex(OwnershipError, "cannot reopen"):
            self.lease.acquire(*self.args)
        self.assertEqual(self.lease.db.execute("SELECT count(*) FROM claims").fetchone()[0], 2)

    def test_missing_or_wrong_claim_cannot_release(self):
        with self.assertRaises(OwnershipError): self.lease.release(*self.args, "e" * 64)
        self.lease.acquire(*self.args)
        with self.assertRaises(OwnershipError):
            self.lease.release(self.tracker, "a2a:caller", "task-1", "a" * 64, "e" * 64)
        self.lease.assert_held(*self.args)

    def test_assert_held_does_not_create_permission(self):
        with self.assertRaises(OwnershipError): self.lease.assert_held(*self.args)
        self.lease.acquire(*self.args)
        self.lease.release(*self.args, "e" * 64)
        with self.assertRaises(OwnershipError): self.lease.assert_held(*self.args)

    def test_case_variant_cannot_bypass_github_claim(self):
        self.lease.acquire(*self.args)
        with self.assertRaises(OwnershipError):
            self.lease.acquire({**self.tracker, "project": "Org/Repo"}, "a2a:caller", "task-2", "b" * 64)

    def test_different_issue_has_independent_ownership(self):
        self.lease.acquire(*self.args)
        self.lease.acquire({**self.tracker, "issue_id": "8"}, "a2a:caller", "task-2", "b" * 64)

    def test_concurrent_claims_have_exactly_one_winner(self):
        def claim(index):
            connection = IngressLeases(self.path)
            try:
                connection.acquire(self.tracker, "ingress:" + str(index), "task-" + str(index), "a" * 64)
                return True
            except OwnershipError:
                return False
            finally:
                connection.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(claim, range(4)))
        self.assertEqual(outcomes.count(True), 1)

    def test_unsafe_paths_rejected(self):
        with self.assertRaises(OwnershipError): IngressLeases("relative.sqlite")
        link = Path(self.tmp.name) / "link"
        link.symlink_to(self.path)
        with self.assertRaises(OwnershipError): IngressLeases(link)
        public = Path(self.tmp.name) / "public"; public.mkdir(); public.chmod(0o777)
        with self.assertRaises(OwnershipError): IngressLeases(public / "db.sqlite")

    def test_database_permissions_are_private(self):
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__": unittest.main()
