"""Fixed native workflow compiler and input validation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

from .._paths import IMPORT_ROOT
from .files import _read_windows_contract
from .resources import ROOT


def workflow(arguments: list[str]) -> int:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(IMPORT_ROOT), str(ROOT / "platform/upstream/platform")))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    return subprocess.call(
        [sys.executable, "-P", "-S", "-c", "from ergora.native.compiler import _compiler_main;_compiler_main()", *arguments],
        env=environment,
    )


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
