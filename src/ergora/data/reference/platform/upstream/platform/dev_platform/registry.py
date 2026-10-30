"""Explicit allowlisted task profiles from the trusted installed platform.

Deploy this directory read-only outside candidate workspaces. A digest detects
drift; it does not authenticate an attacker-writable platform installation.
"""
import copy
import hashlib
import json
from pathlib import Path

from .contracts import (ContractError, SLUG, canonical_sha, need, validate_profile,
                        validate_spec, validate_task)


TASK_ROOT = Path(__file__).resolve().parent.parent / "task-types"


def _read_json(path):
    need(path.is_file() and not path.is_symlink(), "Missing or symlinked trusted registry file")
    need(path.stat().st_size <= 1024 * 1024, "Registry JSON exceeds 1 MiB")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def load_profile(task_type, task_version=1):
    need(type(task_type) is str and SLUG.fullmatch(task_type), "Invalid task type")
    need(type(task_version) is int and task_version >= 1, "Invalid task version")
    root = TASK_ROOT.resolve()
    registry = _read_json(root / "registry.json")
    need(type(registry) is dict and set(registry) == {"schema_version", "types"} and
         registry["schema_version"] == 1 and type(registry["types"]) is dict, "Invalid task registry")
    versions = registry["types"].get(task_type)
    need(type(versions) is dict and str(task_version) in versions, "Task type/version is not registered")
    relative = versions[str(task_version)]
    need(type(relative) is str and relative and not Path(relative).is_absolute(), "Invalid profile registration")
    need(".." not in Path(relative).parts, "Profile registration escapes trusted root")
    lexical = root / relative
    need(not any(parent.is_symlink() for parent in [lexical, *lexical.parents] if parent != root.parent),
         "Trusted profile paths cannot be symlinked")
    path = lexical.resolve()
    need(path.is_relative_to(root), "Profile registration escapes trusted root")
    profile = validate_profile(_read_json(path))
    need(profile["task_type"] == task_type and profile["task_version"] == task_version,
         "Registered profile identity differs from requested type/version")
    for name, expected in profile["template_files"].items():
        source = path.parent / name
        need(source.is_file() and not source.is_symlink() and source.stat().st_size <= 1024 * 1024,
             "Missing, oversized or symlinked trusted template file: " + name)
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        need(actual == expected, "Template contents changed without a new pinned profile: " + name)
    return copy.deepcopy(profile)


def profile_digest(profile):
    return canonical_sha(validate_profile(profile))


def registered_types():
    """Discover only explicit, validated trusted registrations; never scan plugins."""
    registry = _read_json(TASK_ROOT / "registry.json")
    need(type(registry) is dict and set(registry) == {"schema_version", "types"} and
         registry["schema_version"] == 1 and type(registry["types"]) is dict, "Invalid task registry")
    result=[]
    for name, versions in registry["types"].items():
        need(type(versions) is dict and bool(versions), "Registered type requires versions")
        for version in versions:
            need(type(version) is str and version.isdecimal() and str(int(version))==version, "Invalid registered version")
            load_profile(name, int(version))
        result.append(name)
    return sorted(result)


def make_spec(request):
    validate_task(request)
    profile = load_profile(request["task_type"], request["task_version"])
    spec = {"request": copy.deepcopy(request), "profile": profile,
            "request_sha256": canonical_sha(request), "profile_sha256": profile_digest(profile)}
    return validate_spec(spec)
