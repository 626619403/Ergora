"""ForgeKernel campaigns remain native; Ergora records project ownership and evidence."""

import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from . import processes
from .state import State, now


FORGE_COMMIT = "5030503d3ff71851aa34c14b9caf13ebfa9d9a78"


def validate_binding(binding: dict) -> None:
    if binding.get("tool") == "manual":
        if set(binding) != {"tool"}:
            raise ValueError("manual kernel binding has no options")
        return
    if binding.get("tool") != "forgekernel" or set(binding) - {"tool", "checkout", "python", "task"}:
        raise ValueError("Kernel tool must be manual or forgekernel")
    for name in ("checkout", "python", "task"):
        if not isinstance(binding.get(name), str) or not binding[name].strip() or "\0" in binding[name]:
            raise ValueError(f"ForgeKernel requires {name}")
        if not Path(binding[name]).expanduser().is_absolute():
            raise ValueError(f"ForgeKernel {name} must be an absolute path")


def available(binding: dict) -> dict:
    if binding["tool"] == "manual":
        return {"installed": True, "version": "not_applicable"}
    try:
        checkout = Path(binding["checkout"]).expanduser().resolve(strict=True)
        commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        result = subprocess.run([str(Path(binding["python"]).expanduser()), "-c",
            "from forgekernel.paths import repo_root;print(repo_root())"], capture_output=True, text=True, timeout=5)
        installed = result.returncode == 0 and Path(result.stdout.strip()).resolve() == checkout
        return {"installed": installed, "version": "pinned" if commit == FORGE_COMMIT else "unsupported", "commit": commit}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"installed": False, "version": "not_checked"}


def _store(state: State, project_id: str, document: dict) -> dict:
    with state.connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS kernel_runs (id TEXT PRIMARY KEY, project TEXT, document TEXT)")
        db.execute("INSERT OR REPLACE INTO kernel_runs VALUES (?, ?, ?)", (document["id"], project_id, json.dumps(document)))
    return document


def listing(state: State, project_id: str) -> list[dict]:
    state.project(project_id)
    with state.connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS kernel_runs (id TEXT PRIMARY KEY, project TEXT, document TEXT)")
        return [json.loads(row[0]) for row in db.execute("SELECT document FROM kernel_runs WHERE project=? ORDER BY rowid DESC", (project_id,))]


def get(state: State, project_id: str, run_id: str) -> dict:
    for document in listing(state, project_id):
        if document["id"] == run_id:
            return document
    raise ValueError("Unknown kernel campaign in this project")


def _call(state: State, project_id: str, document: dict, action: str, timeout: int, reconcile_reason: str | None = None) -> dict:
    if not 1 <= timeout <= 86400:
        raise ValueError("Kernel timeout must be 1–86400 seconds")
    folder = state.root / "kernel" / document["id"]
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (folder / "lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("A kernel operation is already active; inspect the same campaign") from error
        # Reload after taking the lock; another caller may have just completed.
        document = get(state, project_id, document["id"])
        if (document.get("requires_reconciliation") or document["status"] in ("running", "outcome_unknown") or
                document.get("native", {}).get("native_record", {}).get("status") == "running"):
            document["requires_reconciliation"] = True
        binding = document["binding"]
        checkout = Path(binding["checkout"]).expanduser().resolve(strict=True)
        source = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if source != FORGE_COMMIT:
            raise ValueError(f"ForgeKernel adapter requires fixed commit {FORGE_COMMIT}")
        if subprocess.run(["git", "-C", str(checkout), "diff", "--quiet", "HEAD", "--", "src/forgekernel"], check=False).returncode:
            raise ValueError("ForgeKernel source differs from the pinned adapter version")
        if action == "run" and not document.get("campaign"):
            raise ValueError("Prepare a campaign or reconcile it with status before running")
        if action == "run" and (document.get("requires_reconciliation") or document["status"] in ("running", "outcome_unknown") or
                                document.get("native", {}).get("native_record", {}).get("status") == "running"):
            if not isinstance(reconcile_reason, str) or not reconcile_reason.strip():
                raise ValueError("Previous native outcome is uncertain; confirm old jobs have stopped and provide a reconcile reason before continuing")
            document.setdefault("reconciliations", []).append({"reason": reconcile_reason, "at": now()})
            document["requires_reconciliation"] = False
        operation = uuid.uuid4().hex
        request = {"action": action, "checkout": str(checkout), "task": str(Path(binding["task"]).expanduser().resolve()),
                   "campaign": document.get("campaign"), "native_root": str(folder / "native"),
                   "global_config_sha256": document.get("global_config_sha256")}
        request_path = folder / f"{operation}.json"
        request_path.write_text(json.dumps(request))
        document.update(status="running", last_action=action, updated=now())
        _store(state, project_id, document)
        try:
            result = processes.run([binding["python"], str(Path(__file__).parent / "data/drivers/forge.py"), str(request_path)],
                                   checkout, folder / operation, timeout, lock_fd=lock.fileno())
            evidence = {"action": action, **result}
            with (Path(result["output"]) / "stderr.txt").open("rb") as diagnostics:
                evidence["stderr_preview"] = diagnostics.read(4096).decode("utf-8", errors="replace")
            if result["status"] == "succeeded":
                native = json.loads((Path(result["output"]) / "stdout.txt").read_text())
                document.update(campaign=native.get("campaign"), native=native,
                                status="prepared" if action == "prepare" else "observed" if action in ("status", "plan") else "native_finished")
                if native.get("native_returncode", 0) != 0:
                    document["status"] = "native_failed"
                evidence["native"] = native
            else:
                document["status"] = "outcome_unknown" if action in ("run", "prepare") else result["status"]
                if document["status"] == "outcome_unknown":
                    document["requires_reconciliation"] = True
            document.setdefault("operations", []).append(evidence)
        except (OSError, ValueError) as error:
            document.update(status="outcome_unknown" if action in ("run", "prepare") else "failed", error=str(error))
            if document["status"] == "outcome_unknown":
                document["requires_reconciliation"] = True
        document["updated"] = now()
        return _store(state, project_id, document)


def create(state: State, project_id: str, action: str = "plan", timeout: int = 30) -> dict:
    if action not in ("plan", "prepare"):
        raise ValueError("Create supports plan or prepare")
    project = state.project(project_id)
    binding = project["bindings"].get("kernel", {"tool": "manual"})
    validate_binding(binding)
    if binding["tool"] != "forgekernel":
        raise ValueError("Bind the kernel layer to ForgeKernel before using native campaigns")
    document = {"schema_version": 1, "id": uuid.uuid4().hex, "project": project_id, "binding": binding,
                "project_revision": project["revision"], "started": now(), "status": "created",
                "acceptance": "candidate-only; requires independent project correctness/performance evaluation"}
    _store(state, project_id, document)
    try:
        checkout = Path(binding["checkout"]).expanduser().resolve(strict=True)
        document["global_config_sha256"] = {name: hashlib.sha256((checkout / "global_config" / name).read_bytes()).hexdigest()
                                             for name in ("models.toml", "loop.toml", "backends.toml")}
        _store(state, project_id, document)
        return _call(state, project_id, document, action, timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        document.update(status="failed", error=str(error), updated=now())
        return _store(state, project_id, document)


def operate(state: State, project_id: str, run_id: str, action: str, timeout: int = 30, reconcile_reason: str | None = None) -> dict:
    if action not in ("run", "status"):
        raise ValueError("Existing campaigns support run or status")
    return _call(state, project_id, get(state, project_id, run_id), action, timeout, reconcile_reason)
