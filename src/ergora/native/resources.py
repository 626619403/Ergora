"""Current reference resources and exact native source preparation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from .._paths import DATA_ROOT


DATA = DATA_ROOT
ROOT = DATA / "reference"
TRAINING_PROTOCOL = "training-executor-admission-v3"
TRAINING_PROTOCOLS = (TRAINING_PROTOCOL,)
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
            raise ValueError(f"Reference file differs from its resource manifest: {relative}")
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


def _training_descriptor(raw: bytes) -> dict:
    """Select only an exact bundled declaration, including its original bytes."""
    message = "Unsupported or incomplete native runtime descriptor"
    if len(raw) > 65_536:
        raise ValueError(message)
    try:
        declared = json.loads(raw)
        protocol = declared['protocol_id']
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(message) from error
    if protocol != TRAINING_PROTOCOL:
        raise ValueError(message)
    if raw != (DATA / "native-runtime" / (protocol + ".json")).read_bytes():
        raise ValueError(message)
    return declared


def _installed_training_descriptor(installation: Path, manifest_sha256: str) -> dict | None:
    """Read one bounded current declaration without following links."""
    import stat

    descriptor = installation / "ergora-native-runtime.json"
    try:
        details = descriptor.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(details.st_mode):
        raise ValueError("Native runtime descriptor must be an ordinary file without symlinks")
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(descriptor, flags), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Native runtime descriptor must be an ordinary file")
        raw = stream.read(65_537)
    protocol = _training_descriptor(raw)
    if protocol['reference_manifest_sha256'] != manifest_sha256:
        raise ValueError("Native runtime protocol belongs to another reference manifest")
    return protocol


def _validate_installation_files(installation: Path, manifest: dict, *, complete: bool) -> None:
    prefixes = ("platform/local/", "platform/upstream/platform/")
    for relative, expected in manifest["files"].items():
        selected = (relative.startswith("platform/") if complete else
                    relative.startswith(prefixes) and relative.endswith(".py"))
        if selected:
            file = installation / relative.removeprefix("platform/")
            if (not file.is_file() or file.is_symlink()
                    or hashlib.sha256(file.read_bytes()).hexdigest() != expected):
                raise ValueError(f"Unsupported reference runtime identity: {relative}")


def validate_installation(installation: Path, *, training: bool = False) -> Path:
    installation = installation.expanduser().resolve(strict=True)
    raw = (DATA / "reference-manifest.json").read_bytes()
    descriptor = _installed_training_descriptor(installation, hashlib.sha256(raw).hexdigest())
    if training and descriptor is None:
        raise ValueError('Training installation requires its current native runtime descriptor')
    _validate_installation_files(installation, json.loads(raw), complete=descriptor is not None)
    return installation


def prepare_training(directory: Path, *, protocol: str) -> dict:
    """Prepare current native source without dependencies or execution."""
    if sys.platform != "linux":
        raise ValueError("Native training source preparation requires Linux; use WSL2")
    if protocol not in TRAINING_PROTOCOLS:
        raise ValueError("Unsupported native training source protocol")
    verify()
    manifest_raw = (DATA / "reference-manifest.json").read_bytes()
    metadata = (DATA / "native-runtime" / (protocol + ".json")).read_bytes()
    declared = _training_descriptor(metadata)
    if (declared['protocol_id'] != protocol
            or hashlib.sha256(manifest_raw).hexdigest() != declared['reference_manifest_sha256']):
        raise ValueError("Bundled native training source identity changed")
    directory = directory.expanduser().absolute()
    directory.mkdir(parents=True)
    descriptor = directory / "ergora-native-runtime.json"
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Declare the incomplete source before copying any executable files.
        with descriptor.open('xb') as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory_fd)
        manifest = json.loads(manifest_raw)
        for relative in manifest['files']:
            if relative.startswith('platform/'):
                target = directory / relative.removeprefix('platform/')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
        _validate_installation_files(directory, manifest, complete=True)
        with descriptor.open('wb') as stream:
            stream.write(metadata)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    installation = validate_installation(directory, training=True)
    return {'status': 'source_prepared', 'protocol': protocol, 'installation': str(installation),
            'dependencies_installed': False, 'runtime_started': False, 'execution_authorized': False}
