"""Bounded native project registration inspection and publication."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

from .._paths import IMPORT_ROOT
from .files import _read_windows_contract
from .resources import ROOT


def registration_paths(project_id: str) -> tuple[str, ...]:
    # Project ID is validated by the project owner before crossing this boundary.
    return (f"ergora/registrations/{project_id}.json", f"policies/{project_id}/scope.json",
            f"policies/{project_id}/execution.json", f"projects/{project_id}.json")


def registration_io(execution: dict, project_id: str, *, files: dict | None = None,
                    publish: bool = False, paths: list | None = None, scope: dict | None = None,
                    source_sha256: dict | None = None) -> dict:
    """Inspect or publish only project registration files, using fixed reference code.

    Separate processes avoid import-time CONFIG/STATE leaking between Web projects.
    Reads exclude credentials and runtime settings; publication never replaces files.
    """
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
                       AGENTFLOW_CONFIG_DIR=execution["config_directory"],
                       AGENTFLOW_STATE_DIR=execution["state_directory"])
    environment["PYTHONPATH"] = os.pathsep.join(map(str, (
        IMPORT_ROOT, ROOT / "platform/local", ROOT / "platform/upstream/platform")))
    result = subprocess.run([sys.executable, "-P", "-S", "-c",
                             "from ergora.native.registration import _registration_main;_registration_main()"],
                            input=json.dumps({"id": project_id, "files": files, "publish": publish,
                                              "paths": paths, "scope": scope, "source_sha256": source_sha256}, allow_nan=False),
                            capture_output=True, text=True, encoding="utf-8", env=environment, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.strip().splitlines()[-1])
    return json.loads(result.stdout)


def _registration_main():
    from agent_platform.core import CONFIG, Blocked, slug, write
    from dev_platform import adapter
    from dev_platform.contracts import _paths, canonical_sha
    from harness.git_scope import validate_policy

    try:
        payload = json.load(sys.stdin)
        project_id = slug(payload["id"])
        if os.name == "nt":
            adapter.read_raw = _read_windows_contract
        if payload["paths"] is not None:
            _paths(payload["paths"], "allowed_paths")
            validate_policy(payload["scope"])
        root = CONFIG.resolve()

        def inspect(relative):
            path = adapter.safe_file(root, relative)
            try:
                raw = adapter.read_raw(path)
            except FileNotFoundError:
                return None
            return {"document": json.loads(raw.decode("utf-8")), "sha256": hashlib.sha256(raw).hexdigest()}

        observed = {relative: inspect(relative) for relative in registration_paths(project_id)}
        for relative, expected in (payload["source_sha256"] or {}).items():
            if observed[relative] is None or observed[relative]["sha256"] != expected:
                raise ValueError(f"Legacy source bytes changed since the approved preview: {relative}")
        other_projects = []
        directory = adapter.safe_file(root, "projects")
        for path in sorted(directory.glob("*.json")):
            if path.name != project_id + ".json" and not path.name.endswith(".symphony.json"):
                other_projects.append(inspect("projects/" + path.name)["document"])
        files = payload["files"]
        if files is not None:
            if set(files) != set(observed):
                raise ValueError("Registration must contain exactly the project, policies and ownership files")
            tracker = files[f"projects/{project_id}.json"]["tracker"]
            if any(project["tracker"] == tracker for project in other_projects):
                raise ValueError("Another reference project already owns this tracker")
            for relative, expected in files.items():
                current = observed[relative]
                if current is None:
                    encoded = (json.dumps(expected, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
                    if len(encoded) > 1_048_576:
                        raise ValueError(f"Registration file exceeds 1 MiB read limit: {relative}")
                elif canonical_sha(current["document"]) != canonical_sha(expected):
                    raise ValueError(f"Immutable registration conflict: {relative}")
            if payload["publish"]:
                # Ownership/policies first; make the runnable project visible last.
                for relative in registration_paths(project_id):
                    write(adapter.safe_file(root, relative), files[relative])
        print(json.dumps({"files": observed, "other_projects": other_projects}, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit("BLOCKED: " + str(error))
