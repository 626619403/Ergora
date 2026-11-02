"""The public v2.2 reference stays byte-identical during extraction."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


DATA = Path(__file__).parent / "data"
ROOT = DATA / "reference"
TEMPLATES = ("repository-governance", "large-change", "training-optimization")


def info() -> dict:
    manifest = json.loads((DATA / "reference-manifest.json").read_text(encoding="utf-8"))
    return {
        "version": manifest["version"],
        "path": str(ROOT.resolve()),
        "source_zip_sha256": manifest["source_zip_sha256"],
        "files": len(manifest["files"]),
        "installer": str((ROOT / "install-from-report.sh").resolve()),
        "runtime_started": False,
    }


def verify() -> dict:
    manifest = json.loads((DATA / "reference-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Reference file missing or symlinked: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Reference file differs from the public distribution: {relative}")
    return {"status": "PASS", **info()}


def copy_template(kind: str, destination: Path) -> dict:
    if kind not in TEMPLATES:
        raise ValueError(f"Unknown template: {kind}")
    if destination.exists():
        raise ValueError("Choose a new destination to preserve existing project files")
    source = ROOT / "platform/templates" / kind
    shutil.copytree(source, destination)
    (destination / "agent-contract.json").write_text(json.dumps(agent_contract(kind), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"template": kind, "destination": str(destination.resolve())}


def agent_contract(kind: str) -> dict:
    """Role requirements supplement templates; concrete agents live in project bindings."""
    if kind not in TEMPLATES:
        raise ValueError(f"Unknown template: {kind}")
    if kind == "training-optimization":
        return json.loads((DATA / "training-agents.json").read_text(encoding="utf-8"))
    directory = ROOT / "platform/upstream/platform/task-types" / kind
    profile = json.loads((directory / "profile.json").read_text(encoding="utf-8"))
    roles = json.loads((ROOT / "platform/templates" / kind / "roles.json").read_text(encoding="utf-8"))["roles"]
    selected = {}
    for stage in ("inventory", "plan", "work", "review"):
        role = profile["roles"][stage]
        selected[role] = {**roles[role], "artifacts": [name for name in profile["artifacts_by_stage"][stage]
                                                      if name not in ("behavior-baseline", "test-results")]}
    return {"schema_version": 1, "template": kind, "engine": profile["engine"],
            "agents": selected, "trusted_stages": ["integrate", "verify"],
            "acceptance": {"required_checks": profile["required_checks"], "artifacts_by_stage": profile["artifacts_by_stage"]}}


def template_details(kind: str) -> dict:
    """Read editable template inputs without exposing the frozen directory layout."""
    if kind not in TEMPLATES:
        raise ValueError("Unknown template")
    directory = ROOT / "platform/templates" / kind
    contract = agent_contract(kind)
    if kind == "training-optimization":
        return {"kind": kind, "agents": contract,
                "files": {**{path.name: path.read_text(encoding="utf-8") for path in sorted(directory.iterdir()) if path.is_file()},
                          "agent-contract.json": json.dumps(contract, ensure_ascii=False, indent=2)}}
    return {"kind": kind, "agents": contract,
            "input": json.loads((directory / "input.json").read_text(encoding="utf-8"))}


def executor(installation: Path, home: Path, request: Path | None = None):
    if sys.platform != "linux":
        raise ValueError("The formal reference executor requires Linux; use WSL2 and a trusted Linux container")
    installation = installation.expanduser().resolve(strict=True)
    manifest = json.loads((DATA / "reference-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        if relative.startswith(("platform/local/", "platform/upstream/platform/")) and relative.endswith(".py"):
            file = installation / relative.removeprefix("platform/")
            if not file.is_file() or file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Unsupported reference runtime identity: {relative}")
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from . import reference_executor
    return reference_executor.main(home, request)


def workflow(arguments: list[str]) -> int:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(Path(__file__).parent.parent), str(ROOT / "platform/upstream/platform")))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    return subprocess.call(
        [sys.executable, "-P", "-S", "-c", "from ergora.reference import _compiler_main;_compiler_main()", *arguments],
        env=environment,
    )


def _read_windows_contract(path, limit=1_048_576):
    """Keep the frozen compiler's bounded, no-follow read boundary on Windows."""
    import ctypes
    import msvcrt
    import stat
    from dev_platform.contracts import need

    path = Path(path).absolute()
    need(not any(p.lstat().st_file_attributes & 0x400 for p in (path, *path.parents)),
         "Symlinked or reparsed contract path is forbidden")
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = ctypes.c_void_p
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                               handle, ctypes.c_uint32, ctypes.c_uint32, handle]
    api.CreateFileW.restype = handle
    api.GetFileInformationByHandleEx.argtypes = [handle, ctypes.c_int, handle, ctypes.c_uint32]
    api.GetFileInformationByHandleEx.restype = ctypes.c_int
    api.CloseHandle.argtypes = [handle]
    api.CloseHandle.restype = ctypes.c_int
    # Open the final reparse point itself; sharing only reads prevents concurrent edits.
    native = api.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
    if native == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = (ctypes.c_uint32 * 2)()
        if not api.GetFileInformationByHandleEx(native, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        need(not attributes[0] & 0x400, "Symlinked or reparsed contract path is forbidden")
        fd = msvcrt.open_osfhandle(native, os.O_RDONLY | os.O_BINARY)
        native = None  # The CRT stream now owns the handle.
        with os.fdopen(fd, "rb") as stream:
            need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Contract must be a regular file")
            raw = stream.read(limit + 1)
        need(len(raw) <= limit, "Contract exceeds size limit")
        return raw
    finally:
        if native is not None:
            api.CloseHandle(native)


def _compiler_main():
    from dev_platform import adapter, portable

    if os.name == "nt":
        portable._read_bytes = _read_windows_contract
        adapter.read_raw = _read_windows_contract
    try:
        portable.main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit("BLOCKED: " + str(error))


def validate_input(kind: str, task_input: dict) -> dict:
    if kind not in ("repository-governance", "large-change"):
        raise ValueError("DAG editing supports repository-governance and large-change")
    example = ROOT / "platform/upstream/platform/task-types" / kind / "examples/request.json"
    request = json.loads(example.read_text(encoding="utf-8"))
    request["input"] = task_input
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "platform/upstream/platform"), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    script = "import json,sys;from dev_platform.contracts import make_spec;make_spec(json.load(sys.stdin));print('PASS')"
    result = subprocess.run([sys.executable, "-P", "-S", "-c", script], input=json.dumps(request),
                            capture_output=True, text=True, env=environment, timeout=10, encoding="utf-8")
    if result.returncode:
        raise ValueError(result.stderr.strip().splitlines()[-1])
    return {"status": "PASS", "task_type": kind,
            "input_sha256": hashlib.sha256(json.dumps(task_input, sort_keys=True).encode()).hexdigest()}
