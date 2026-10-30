"""Trusted file-exchange adapter for cloud-hosted executors, not an agent executor.

Only the worker writes requests; authenticated CI/operator processes publish receipts,
artifacts and approvals. The filesystem ACL is the authority. JSON identities alone
are not authentication. Every external executor must deduplicate job_id, enforce an
independent walltime, and honor task fences before any side effect.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import time
from typing import Protocol


class AdapterNotConfigured(RuntimeError): pass
class ContractViolation(ValueError): pass
class ApprovalRejected(ValueError): pass


def require(ok, message):
    if not ok:
        raise ContractViolation(message)


MAX_RECEIPT_BYTES = 32_768
MAX_CONTEXT_BYTES = 1_000_000


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,159}", value), "Invalid identifier")
    return value


def safe_file(root, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative, "Invalid relative path")
    p = PurePosixPath(relative)
    require(not p.is_absolute() and all(x not in ("", ".", "..") for x in relative.split("/")), "Noncanonical artifact path")
    target = root / relative
    require(target.resolve().is_relative_to(root), "Path escapes trusted root")
    # Reject symlinks even if they point back inside the root.
    for parent in [target, *target.parents]:
        if parent == root: break
        require(not parent.is_symlink(), "Symlinks are not accepted")
    return target


def read_raw(path, limit=1_048_576):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Expected regular file")
        data = stream.read(limit + 1)
    require(len(data) <= limit, "File exceeds size limit")
    return data


def read_json(path):
    return json.loads(read_raw(path))


def publish(path, value):
    """Create immutable complete JSON. Retrying equal bytes is idempotent."""
    raw = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            require(read_raw(path) == raw, "Immutable publication conflicts with existing bytes")
    finally:
        Path(temporary).unlink(missing_ok=True)


class DevelopmentAdapter(Protocol):
    async def submit(self, context: dict) -> dict: ...
    async def poll(self, job: dict) -> dict | None: ...
    async def authorize(self, context: dict) -> dict: ...
    async def fence(self, context: dict) -> dict: ...


class FileAdapter:
    """Bounded operations on trusted mounted directories; no shell execution."""
    def __init__(self, config: dict):
        self.config = dict(config)
        keys = ("requests", "receipts", "artifacts", "approvals", "fences")
        self.roots = {}
        for key in keys:
            value = config.get(key)
            require(isinstance(value, str) and Path(value).is_absolute(), key + " must be absolute")
            root = Path(value)
            require(not root.is_symlink(), key + " root cannot be a symlink")
            self.roots[key] = root.resolve()
        for a, first in self.roots.items():
            for b, second in self.roots.items():
                if a != b:
                    require(not first.is_relative_to(second), "Adapter roots must be disjoint")
        # Explicit acknowledgment helps avoid accidentally sharing these volumes with Codex.
        require(config.get("trusted_receipts") is True, "Receipt/approval volumes must be trusted and inaccessible to coding agents")

    def path(self, key, relative):
        return safe_file(self.roots[key], relative)

    async def submit(self, context):
        require(len(canonical(context)) <= MAX_CONTEXT_BYTES, "Stage context exceeds 1,000,000 bytes; put long content in artifacts and split the task")
        task_id = identifier(context["task_id"])
        job_id = identifier(context["job_id"])
        fence = self.path("fences", task_id + ".json")
        require(not fence.exists(), "Task is fenced; no additional stage may be submitted")
        envelope = {"schema_version": 1, "job_id": job_id, "job_sha256": sha(context), "context": context}
        publish(self.path("requests", task_id + "/" + job_id + ".json"), envelope)
        # A fence racing this write is safe only because the executor checks the fence.
        require(not fence.exists(), "Task fenced during stage publication; executor must suppress it")
        return {"task_id": task_id, "job_id": job_id, "job_sha256": envelope["job_sha256"], "context": context}

    def verify_receipt(self, job, receipt):
        require(isinstance(receipt, dict) and type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1, "Receipt schema mismatch")
        require(len(canonical(receipt)) <= MAX_RECEIPT_BYTES, "Receipt metadata exceeds 32 KiB; store long logs in artifacts")
        require(set(receipt) <= {"schema_version", "job_id", "job_sha256", "state", "actor", "candidate_sha", "artifacts", "checks", "detail"}, "Unexpected receipt fields; store evidence in artifacts")
        require(receipt.get("job_id") == job["job_id"] and receipt.get("job_sha256") == job["job_sha256"], "Receipt is bound to another job/context")
        require(receipt.get("state") in {"SUCCEEDED", "FAILED", "CANCELLED"}, "Only terminal receipts may be published")
        require("detail" not in receipt or isinstance(receipt["detail"], str), "Receipt detail must be a string")
        actor = receipt.get("actor", {})
        require(isinstance(actor, dict), "Actor must be an object")
        for field in ("id", "session_id", "role", "kind"):
            require(isinstance(actor.get(field), str) and bool(actor[field].strip()), "Trusted actor identity missing: " + field)
        require(actor["kind"] in {"agent", "ci", "human"}, "Invalid actor kind")
        require(isinstance(receipt.get("candidate_sha"), str) and re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", receipt["candidate_sha"]), "Candidate full commit required")
        artifacts = receipt.get("artifacts")
        require(isinstance(artifacts, list) and len(artifacts) <= 100, "Artifact list missing or oversized")
        names = set()
        for artifact in artifacts:
            require(isinstance(artifact, dict), "Invalid artifact")
            name = artifact.get("name")
            require(isinstance(name, str) and name and name not in names, "Duplicate/empty artifact name")
            names.add(name)
            require(isinstance(artifact.get("sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", artifact["sha256"]), "Invalid artifact digest")
            raw = read_raw(self.path("artifacts", artifact.get("path")), 16_777_216)
            require(hashlib.sha256(raw).hexdigest() == artifact["sha256"], "Artifact bytes do not match receipt digest")
        checks = receipt.get("checks", [])
        require(isinstance(checks, list) and len(checks) <= 100, "checks must be a list of at most 100 entries")
        seen = set()
        for check in checks:
            require(isinstance(check, dict) and isinstance(check.get("id"), str) and bool(check["id"].strip()) and check["id"] not in seen, "Duplicate/invalid check ID")
            seen.add(check["id"])
            require(check.get("status") in {"pass", "fail"}, "Checks cannot be skipped or unknown")
            require(check.get("artifact") in names, "Each check must point to an existing hashed artifact")
        return receipt

    async def poll(self, job):
        path = self.path("receipts", job["task_id"] + "/" + job["job_id"] + ".json")
        if not path.exists(): return None
        return self.verify_receipt(job, read_json(path))

    async def authorize(self, context):
        receipt_id = identifier(context["receipt_id"])
        try:
            approval = read_json(self.path("approvals", receipt_id + ".json"))
            expected = {"schema_version": 1, "kind": "plan-approval", "task_id": context["task_id"],
                        "request_sha256": context["request_sha256"], "profile_sha256": context["profile_sha256"],
                        "plan_sha256": context["plan_sha256"], "decision": "approve", "principal_type": "human"}
            for key, value in expected.items():
                require(approval.get(key) == value, "Approval scope mismatch: " + key)
            require(isinstance(approval.get("actor_id"), str) and approval["actor_id"].strip(), "Human identity required")
            require(approval.get("role") in {"owner", "maintainer"}, "Plan approver must be owner or maintainer")
            require(type(approval.get("expires_at")) in {int, float} and math.isfinite(approval["expires_at"]) and time.time() < approval["expires_at"] <= time.time() + 604800, "Approval expired")
            require(approval.get("revoked") is False, "Approval missing explicit non-revoked state")
            return {"receipt_id": receipt_id, "approval_sha256": sha(approval), "actor_id": approval["actor_id"]}
        except (OSError, ValueError, TypeError) as error:
            raise ApprovalRejected(str(error)) from error

    async def fence(self, context):
        task_id = identifier(context["task_id"])
        value = {"schema_version": 1, "task_id": task_id, "request_sha256": context["request_sha256"]}
        publish(self.path("fences", task_id + ".json"), value)
        unresolved = []
        folder = self.path("requests", task_id)
        if folder.exists():
            for path in sorted(folder.glob("*.json")):
                envelope = read_json(path)
                require(envelope["context"]["request_sha256"] == context["request_sha256"], "Task ID collision during fence")
                job = {"task_id": task_id, "job_id": envelope["job_id"], "job_sha256": envelope["job_sha256"], "context": envelope["context"]}
                try: receipt = await self.poll(job)
                except (OSError, ValueError): receipt = None
                if receipt is None: unresolved.append(job["job_id"])
        return {"fenced": True, "confirmed": not unresolved, "unresolved_jobs": unresolved}


def load_adapter():
    path = os.environ.get("DEV_ADAPTER_CONFIG")
    if not path:
        raise AdapterNotConfigured("Set DEV_ADAPTER_CONFIG to a trusted file-adapter config; no executor or fake approval verifier is selected by default")
    return FileAdapter(read_json(Path(path)))


def main():
    parser = argparse.ArgumentParser(description="Trusted CI/operator receipt publisher; never expose to coding agents")
    parser.add_argument("--config", required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    receipt = sub.add_parser("publish-receipt"); receipt.add_argument("job"); receipt.add_argument("receipt")
    approval = sub.add_parser("publish-approval"); approval.add_argument("receipt_id"); approval.add_argument("approval")
    args = parser.parse_args(); adapter = FileAdapter(read_json(Path(args.config)))
    if args.action == "publish-receipt":
        envelope = read_json(Path(args.job)); context = envelope["context"]
        require(envelope["job_sha256"] == sha(context), "Job context hash mismatch")
        trusted = read_json(adapter.path("requests", identifier(context["task_id"]) + "/" + identifier(envelope["job_id"]) + ".json"))
        require(envelope == trusted, "Job differs from trusted published request")
        job = {"task_id": context["task_id"], "job_id": envelope["job_id"], "job_sha256": envelope["job_sha256"], "context": context}
        value = read_json(Path(args.receipt)); adapter.verify_receipt(job, value)
        publish(adapter.path("receipts", job["task_id"] + "/" + job["job_id"] + ".json"), value)
    else:
        value = read_json(Path(args.approval))
        require(value.get("kind") == "plan-approval", "Only plan approval receipts are accepted")
        publish(adapter.path("approvals", identifier(args.receipt_id) + ".json"), value)
    print("Published immutable receipt. Workflow validation determines acceptance.")


if __name__ == "__main__": main()
