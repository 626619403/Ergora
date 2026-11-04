"""The public v2.2 reference stays byte-identical during extraction."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


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


def validate_installation(installation: Path) -> Path:
    installation = installation.expanduser().resolve(strict=True)
    manifest = json.loads((DATA / "reference-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        if relative.startswith(("platform/local/", "platform/upstream/platform/")) and relative.endswith(".py"):
            file = installation / relative.removeprefix("platform/")
            if not file.is_file() or file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Unsupported reference runtime identity: {relative}")
    return installation


def executor(installation: Path, home: Path, request: Path | None = None):
    if sys.platform != "linux":
        raise ValueError("The formal reference executor requires Linux; use WSL2 and a trusted Linux container")
    installation = validate_installation(installation)
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from . import reference_executor
    return reference_executor.main(home, request)


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
        Path(__file__).parent.parent, ROOT / "platform/local", ROOT / "platform/upstream/platform")))
    result = subprocess.run([sys.executable, "-P", "-S", "-c",
                             "from ergora.reference import _registration_main;_registration_main()"],
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


def task_files(project: dict, *, task_id: str | None = None, limit: int = 50,
               after: str | None = None) -> dict:
    """Read native task files in a dedicated process; no optional SDK is loaded."""
    execution = project['registration']['definition']['execution']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, ROOT / 'platform/local', ROOT / 'platform/upstream/platform')))
    try:
        result = subprocess.run([sys.executable, '-P', '-S', '-c',
                                 'from ergora.reference import _task_files_main;_task_files_main()'],
                                input=json.dumps({'project': project['id'], 'repo': project['repo'],
                                                  'tracker': project['registration']['definition']['tracker'],
                                                  'task_id': task_id, 'limit': limit, 'after': after}),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task contract reader timed out; inspect the selected execution storage before retrying') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task contract reader exited with status {result.returncode}')
    return json.loads(result.stdout)


def task_creation(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Isolate native compilation and recoverable file publication from application globals."""
    execution = project['registration']['definition']['execution']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, ROOT / 'platform/local', ROOT / 'platform/upstream/platform')))
    try:
        # The caller owns temporary storage so timeout/forced child termination
        # still removes compiled materials after subprocess.run reaps the child.
        with TemporaryDirectory(prefix='ergora-task-compile-') as directory:
            environment['AGENTFLOW_STATE_DIR'] = directory
            result = subprocess.run([sys.executable, '-P', '-S', '-c',
                                     'from ergora.reference_task_creation import main;main()'],
                                    input=json.dumps({'project': project, 'control_home': str(home),
                                                      'operation': operation, **payload}, allow_nan=False),
                                    capture_output=True, text=True, encoding='utf-8', env=environment, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task creation timed out; inspect task creation status and resume the original intent') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task creation process exited with status {result.returncode}; inspect creation status')
    return json.loads(result.stdout)


def task_runtime_status(project: dict, spec: dict, *, run_id: str | None, timeout: int) -> dict:
    """Query the installed native transport without loading its globals into Web/CLI."""
    if importlib.util.find_spec('temporalio') is None:
        raise ValueError('Task runtime queries require the optional Temporal SDK; install ergora[temporal] in this environment')
    execution = project['registration']['definition']['execution']
    installation = Path(execution['installation'])
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, installation / 'local', installation / 'upstream/platform')))
    try:
        result = subprocess.run([sys.executable, '-P', '-c',
                                 'from ergora.reference_task_runtime import main;main()'],
                                input=json.dumps({'spec': spec, 'run_id': run_id, 'timeout': timeout}, allow_nan=False),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=timeout + 5)
    except subprocess.TimeoutExpired as error:
        raise ValueError('Task runtime query process timed out; execution state remains unknown') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Task runtime query process exited with status {result.returncode}')
    return json.loads(result.stdout)


def task_submission(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the registered full runtime for native admission and its local journal."""
    return _task_operation(project, home, 'submission', operation, payload, timeout)


def task_approval(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the same native lifecycle for exact owner decisions and signal recovery."""
    return _task_operation(project, home, 'approval', operation, payload, timeout)


def task_plan(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Inspect the pending plan through the existing native approval boundary."""
    return _task_operation(project, home, 'approval', 'inspect-plan', payload, timeout)


def task_events(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Read bounded original-run metadata through its native query entry."""
    return _task_operation(project, home, 'events', 'inspect-events', payload, timeout)


def task_job(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Read the original scheduled job's trusted receipt and bounded text evidence."""
    return _task_operation(project, home, 'evidence', 'inspect-job', payload, timeout)


def task_cancellation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the native cancellation guard and preserve signal delivery uncertainty."""
    return _task_operation(project, home, 'cancellation', operation, payload, timeout)


def task_export(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Export the original run's candidate through its recoverable native boundary."""
    return _task_operation(project, home, 'export', operation, payload, timeout)


def task_external_status(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Inspect original-run external evidence through the registered native process."""
    return _task_operation(project, home, 'reconciliation', 'inspect', payload, timeout)


def task_evidence(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Index the closed original run's contracts and verified published evidence."""
    return _task_operation(project, home, 'reconciliation', 'inspect-index', payload, timeout)


def task_reconciliation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Reconcile the original closed run through its durable native boundary."""
    return _task_operation(project, home, 'reconciliation', operation, payload, timeout)


def _task_operation(project: dict, home: Path, component: str, operation: str, payload: dict, timeout: int) -> dict:
    inspection = {'inspect-plan': 'Plan', 'inspect-events': 'Task event', 'inspect-job': 'Job evidence',
                  'inspect-index': 'Task evidence index'}.get(operation)
    if sys.platform != 'linux':
        raise ValueError(f'Formal task {component} requires Linux; use the registered Linux runtime in WSL2')
    execution = project['registration']['definition']['execution']
    installation = Path(execution['installation'])
    interpreter = installation / '.venv/bin/python'
    if not interpreter.is_file():
        raise ValueError(f'Selected reference runtime is incomplete; install its full Linux environment before task {component}')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, installation / 'local', installation / 'upstream/platform')))
    try:
        result = subprocess.run([str(interpreter), '-P', '-c',
                                 f'from ergora.reference_task_{component} import main;main()'],
                                input=json.dumps({'project': project, 'control_home': str(home), 'operation': operation,
                                                  'timeout': timeout, **payload}, allow_nan=False),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=timeout + 5)
    except subprocess.TimeoutExpired as error:
        if inspection:
            raise ValueError(inspection + ' inspection process timed out; query the original run before inspecting again') from error
        raise ValueError(f'Task {component} process timed out; inspect task {component} and resume its original intent') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        detail = lines[-1] if lines else f'Native {component} process exited with status {result.returncode}'
        if inspection:
            raise ValueError(detail)
        raise ValueError(detail + f'; inspect task {component} before any recovery')
    return json.loads(result.stdout)


def _task_files_main():
    import base64
    import heapq
    from agent_platform.core import STATE, Blocked, slug
    from dev_platform import adapter
    from dev_platform.contracts import validate_spec

    try:
        payload = json.load(sys.stdin)
        slug(payload['project'])
        if payload['task_id'] is not None:
            slug(payload['task_id'])
        after = payload['after']
        if after is not None:
            if not isinstance(after, str) or len(after) > 2048:
                raise ValueError('Invalid task directory cursor')
            try:
                after = os.fsdecode(base64.b64decode(after.encode('ascii'), altchars=b'-_', validate=True))
            except ValueError as error:
                raise ValueError('Invalid task directory cursor') from error
        if os.name == 'nt':
            adapter.read_raw = _read_windows_contract
        root = STATE.resolve()
        directory = adapter.safe_file(root, 'tasks')

        def document(task_id, filename):
            path = adapter.safe_file(root, 'tasks/' + slug(task_id) + '/' + filename)
            if not path.is_file():
                raise ValueError('Task contract must be an existing regular file: ' + filename)
            raw = adapter.read_raw(path)
            try:
                value = json.loads(raw.decode('utf-8'))
            except ValueError as error:
                raise ValueError('Invalid task JSON: ' + filename) from error
            if not isinstance(value, dict):
                raise ValueError('Task JSON must be an object: ' + filename)
            if filename == 'project.json' and not all(isinstance(value.get(key), str) and value[key]
                                                      for key in ('name', 'repo')):
                raise ValueError('Task project ownership fields are missing or invalid')
            return value, hashlib.sha256(raw).hexdigest()

        def owns(project):
            return (project.get('name') == payload['project']
                    and project.get('repo') == payload['repo'])

        def inspect(task_id, project, *, detail=False):
            if not owns(project):
                raise ValueError('Task does not belong to the selected project and Git repository')
            spec, file_sha = document(task_id, 'task.spec.json')
            validate_spec(spec)
            request = spec['request']
            if request['task_id'] != task_id:
                raise ValueError('Task ID differs from its native directory')
            if (project.get('tracker') != payload['tracker']
                    or {key: request['tracker'][key] for key in ('kind', 'project')} != payload['tracker']):
                raise ValueError('Task tracker differs from the selected project')
            if request['repository']['base_sha'] != project.get('base_sha'):
                raise ValueError('Task baseline differs from its frozen project')
            item = {'task_id': task_id, 'task_type': request['task_type'],
                    'goal': request['input']['goal'][:200], 'tracker': request['tracker'],
                    'request_sha256': spec['request_sha256'], 'profile_sha256': spec['profile_sha256'],
                    'spec_file_sha256': file_sha, 'runtime_status': 'not_queried'}
            if detail:
                snapshot = adapter.safe_file(root, 'tasks/' + task_id + '/agent-bindings.json')
                bindings, bindings_sha = document(task_id, 'agent-bindings.json') if snapshot.exists() else (None, None)
                if bindings is not None and bindings.get('reference_project') != payload['project']:
                    raise ValueError('Frozen agent snapshot project mismatch')
                item.update(spec=spec, frozen_project=project, agent_bindings=bindings,
                            agent_bindings_file_sha256=bindings_sha)
            return item

        if payload['task_id'] is not None:
            project, _ = document(payload['task_id'], 'project.json')
            result = inspect(payload['task_id'], project, detail=True)
        else:
            # Bound both resident candidate names and per-page file reads. A cursor
            # advances across scanned entries even when they belong to other projects.
            if directory.exists():
                with os.scandir(directory) as entries:
                    names = heapq.nsmallest(payload['limit'] + 1, (entry.name for entry in entries
                        if not entry.name.startswith('.') and (after is None or entry.name > after)))
            else:
                names = []
            result = {'items': [], 'errors': [], 'unreadable_count': 0, 'inspected_entries': min(len(names), payload['limit']),
                      'next_after': base64.urlsafe_b64encode(os.fsencode(names[payload['limit'] - 1])).decode('ascii') if len(names) > payload['limit'] else None,
                      'runtime_status': 'not_queried'}
            for name in names[:payload['limit']]:
                try:
                    project, _ = document(name, 'project.json')
                except (OSError, ValueError, Blocked):
                    result['unreadable_count'] += 1
                    continue
                if not owns(project):
                    continue
                try:
                    result['items'].append(inspect(name, project))
                except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
                    result['errors'].append({'task_id': name, 'error': str(error)})
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
