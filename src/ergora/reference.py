"""Current reference resources and exact native source preparation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from tempfile import TemporaryDirectory

from . import processes
from .reference_creation_process import task_creation


DATA = Path(__file__).parent / "data"
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


def executor(installation: Path, home: Path, request: Path | None = None):
    if sys.platform != "linux":
        raise ValueError("The formal reference executor requires Linux; use WSL2 and a trusted Linux container")
    installation = validate_installation(installation)
    sys.path[:0] = [str(installation / "local"), str(installation / "upstream/platform")]
    from . import reference_executor
    return reference_executor.main(home, request)


def worker_command(installation: Path, *, module: str = 'reference_worker', entrypoint: str = 'main') -> list[str]:
    """Run versioned workers with the selected native SDK and this package's code."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(Path(__file__).parent.parent)!r});'
                 'import ergora;sys.path.pop(0);'
                 f'from ergora.{module} import {entrypoint};{entrypoint}({str(installation)!r})')
    return [str(installation / '.venv/bin/python'), '-P', '-c', bootstrap]


def training_budget_worker_command(installation: Path) -> list[str]:
    """Budget readers use this application's dependencies and optional Temporal SDK."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(Path(__file__).parent.parent)!r});'
                 f'from ergora.reference_training_worker import main;main({str(installation)!r})')
    return [sys.executable, '-P', '-c', bootstrap]


def training_cycle_worker_command(installation: Path) -> list[str]:
    """Cycle readers use the application's SDK in their own service process."""
    bootstrap = (f'import sys;sys.path.insert(0,{str(Path(__file__).parent.parent)!r});'
                 f'from ergora.reference_training_worker import cycle_main;cycle_main({str(installation)!r})')
    return [sys.executable, '-P', '-c', bootstrap]


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


def training_files(project: dict, *, experiment_id: str | None = None, limit: int = 50,
                   after: str | None = None) -> dict:
    """Observe the frozen native registry in a separate, SDK-free process."""
    return _training_reader(project, 'from ergora.reference import _training_files_main;_training_files_main()',
                            {'project': project['id'], 'repo': project['repo'],
                             'experiment_id': experiment_id, 'limit': limit, 'after': after})


def _training_reader_request(state_directory, config_directory, payload):
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=config_directory, AGENTFLOW_STATE_DIR=state_directory)
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, ROOT / 'platform/local', ROOT / 'platform/upstream/platform',
        ROOT / 'platform/upstream/temporal', ROOT / 'platform/upstream')))
    raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(raw) > 16 * 1_048_576:
        raise ValueError('capacity_exceeded: complete training reader request')
    return environment, raw


def _training_reader_response(raw, stderr, returncode):
    from .training_execution_protocol import decode

    if returncode:
        lines = stderr.decode('utf-8', errors='replace').strip().splitlines()
        raise ValueError(lines[-1] if lines else f'Training record reader exited with status {returncode}')
    return decode(raw)


def _stop_training_reader(process):
    try:
        process.kill()
    except ProcessLookupError:
        pass  # The original wait must still confirm the concurrent exit.


def _training_reader(project: dict, entrypoint: str, payload: dict, *, timeout: int = 30) -> dict:
    """A synchronous caller owns its actual child/wait until reap, even after T."""
    import selectors

    started = time.monotonic()
    deadline = started + timeout
    read_deadline = deadline - min(5, timeout / 4)
    execution = project['registration']['definition']['execution']
    environment, encoded = _training_reader_request(execution['state_directory'], execution['config_directory'], payload)
    if timeout <= 0:
        raise ValueError('Training record reader has no remaining allowance')
    process, selected = None, None
    stdout, stderr, offset, failure = bytearray(), bytearray(), 0, None
    pumps = []
    try:
        process = subprocess.Popen([sys.executable, '-P', '-S', '-c', entrypoint], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
        selected = selectors.DefaultSelector()
        if os.name == 'nt':
            # Windows does not select anonymous pipes. These synchronous pipe
            # pumps do no business-file I/O and remain owned/joined by this call.
            import threading
            problems, pumps = [], []
            def pump(stream, target, limit):
                try:
                    while chunk := stream.read(65_536):
                        if len(target) + len(chunk) > limit:
                            problems.append(ValueError('capacity_exceeded: complete training reader response'))
                        else:
                            target.extend(chunk)
                except OSError as error:
                    problems.append(error)
            def send():
                nonlocal offset
                try:
                    for start in range(0, len(encoded), 65_536):
                        offset += process.stdin.write(encoded[start:start + 65_536])
                        process.stdin.flush()
                except (OSError, ValueError) as error:
                    problems.append(error)
                finally:
                    process.stdin.close()
            pumps = [threading.Thread(target=send), threading.Thread(target=pump, args=(process.stdout, stdout, 8_388_608)),
                     threading.Thread(target=pump, args=(process.stderr, stderr, 65_536))]
            for pump_thread in pumps:
                pump_thread.start()
            while any(pump_thread.is_alive() for pump_thread in pumps) or process.poll() is None:
                if problems:
                    raise problems[0]
                remaining = read_deadline-time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Training record reader timed out; native execution state was not queried')
                threading.Event().wait(min(.05, remaining))
        else:
            for stream, event in ((process.stdin, selectors.EVENT_WRITE), (process.stdout, selectors.EVENT_READ), (process.stderr, selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                selected.register(stream, event)
            while selected.get_map() or process.poll() is None:
                remaining = read_deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Training record reader timed out; native execution state was not queried')
                for key, event in selected.select(min(.05, remaining)):
                    stream = key.fileobj
                    try:
                        if event == selectors.EVENT_WRITE:
                            offset += os.write(stream.fileno(), encoded[offset:offset + 65_536])
                            if offset == len(encoded):
                                selected.unregister(stream)
                                stream.close()
                        else:
                            chunk = os.read(stream.fileno(), 65_536)
                            if not chunk:
                                selected.unregister(stream)
                                stream.close()
                            else:
                                target, limit = (stdout, 8_388_608) if stream is process.stdout else (stderr, 65_536)
                                if len(target) + len(chunk) > limit:
                                    raise ValueError('capacity_exceeded: complete training reader response')
                                target.extend(chunk)
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        selected.unregister(stream)
                        stream.close()
        if offset != len(encoded) or time.monotonic() > read_deadline:
            raise TimeoutError('Training record reader timed out or did not consume its complete request')
    except BaseException as error:
        if process is None:
            raise
        failure = error
    finally:
        if process is not None:
            # Stop initiation and actual wait retain the same child across interrupts.
            # If the OS delays reap, this call remains cleanup_incomplete past T.
            while True:
                try:
                    try:
                        if process.poll() is None:
                            _stop_training_reader(process)
                    except OSError as error:
                        if not isinstance(failure, (KeyboardInterrupt, SystemExit)):
                            failure = error
                    process.wait()
                    break
                except KeyboardInterrupt as error:
                    if not isinstance(failure, KeyboardInterrupt):
                        failure = error
        for pump_thread in pumps:
            while pump_thread.is_alive():
                try:
                    pump_thread.join()
                except KeyboardInterrupt:
                    failure = failure or KeyboardInterrupt()
        if selected is not None:
            selected.close()
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if not stream.closed:
                    stream.close()
    elapsed = time.monotonic() - started
    if failure is not None:
        detail = f'; reader elapsed={elapsed:.6f}s T={timeout}s overrun={max(0, elapsed-timeout):.6f}s returncode={process.returncode}'
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure
        raise ValueError(str(failure) + detail) from failure
    result = _training_reader_response(bytes(stdout), bytes(stderr), process.returncode)
    if time.monotonic() > deadline:
        raise ValueError(f'Training record reader timed out during decoding; elapsed={time.monotonic()-started:.6f}s overrun={time.monotonic()-deadline:.6f}s returncode={process.returncode}')
    return result


async def _training_reader_async(state_directory, config_directory, operation, job, *, resources, timeout=20):
    """Await bounded pipes only; the adapter retains every child and actual wait."""
    import asyncio

    started = time.monotonic()
    timeout = min(20, timeout)
    deadline = started + timeout
    read_deadline = deadline - min(5, timeout / 4)
    if timeout <= 0 or any(item.get('unconfirmed') for item in resources.values()):
        raise ValueError('reader_cleanup_unconfirmed or original reader allowance exhausted')
    environment, encoded = _training_reader_request(state_directory, config_directory,
        {'operation': operation, 'state_directory': state_directory, 'config_directory': config_directory, 'job': job})
    spawning = asyncio.create_task(asyncio.create_subprocess_exec(sys.executable, '-P', '-S', '-c',
        'from ergora.reference_training_evidence import main;main()', stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=environment))
    spawning_key = id(spawning)
    resource = {'process': None, 'spawn': spawning, 'unconfirmed': False, 'draining': None}
    resources[spawning_key] = resource
    try:
        process = await asyncio.wait_for(asyncio.shield(spawning), max(.001, read_deadline-time.monotonic()))
    except BaseException as error:
        async def reap_spawn():
            child = await spawning
            resource['process'] = child
            _stop_training_reader(child)
            # No request bytes were sent; this fixed child cannot do work.
            await child.communicate()
        resource['draining'] = asyncio.create_task(reap_spawn())
        while not resource['draining'].done() and time.monotonic() < deadline:
            try:
                await asyncio.wait_for(asyncio.shield(resource['draining']), max(.001, deadline-time.monotonic()))
            except asyncio.CancelledError:
                continue
            except TimeoutError:
                break
        if resource['draining'].done():
            resources.pop(spawning_key, None)
            await resource['draining']
            raise error
        resource['unconfirmed'] = True
        raise ValueError('reader_cleanup_unconfirmed: original child creation/wait retained') from error
    resources.pop(spawning_key)
    overflow = asyncio.get_running_loop().create_future()
    stdout, stderr = bytearray(), bytearray()

    async def read_pipe(stream, target, limit):
        while chunk := await stream.read(65_536):
            if len(target) + len(chunk) > limit:
                if not overflow.done():
                    overflow.set_result('capacity_exceeded: complete training reader response')
            else:
                target.extend(chunk)

    async def write_pipe():
        try:
            for offset in range(0, len(encoded), 65_536):
                process.stdin.write(encoded[offset:offset + 65_536])
                await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    wait = asyncio.create_task(process.wait())
    tasks = [asyncio.create_task(write_pipe()), asyncio.create_task(read_pipe(process.stdout, stdout, 8_388_608)),
             asyncio.create_task(read_pipe(process.stderr, stderr, 65_536))]
    draining = asyncio.gather(wait, *tasks, return_exceptions=True)
    resource = {'process': process, 'wait': wait, 'draining': draining, 'unconfirmed': False}
    resources[process.pid] = resource
    failure = None
    try:
        done, _ = await asyncio.wait((draining, overflow), timeout=max(0, read_deadline-time.monotonic()), return_when=asyncio.FIRST_COMPLETED)
        if overflow in done:
            raise ValueError(overflow.result())
        if draining not in done or time.monotonic() > read_deadline:
            raise TimeoutError('Training record reader timed out')
        outcomes = await draining
        if any(isinstance(item, BaseException) for item in outcomes):
            raise ValueError('Training reader pipe or actual wait failed')
    except BaseException as error:
        failure = error
    finally:
        overflow.cancel()
        if not draining.done() and process.returncode is None:
            _stop_training_reader(process)
        while not draining.done() and time.monotonic() < deadline:
            try:
                await asyncio.wait_for(asyncio.shield(draining), max(.001, deadline-time.monotonic()))
            except asyncio.CancelledError as error:
                failure = failure or error
            except TimeoutError:
                break
        if draining.done() and process.returncode is not None:
            resources.pop(process.pid, None)
        else:
            resource['unconfirmed'] = True
    if resource['unconfirmed']:
        raise ValueError(f'reader_cleanup_unconfirmed: pid={process.pid} returncode={process.returncode}')
    if failure is not None:
        if isinstance(failure, asyncio.CancelledError):
            raise failure
        raise ValueError(str(failure)) from failure
    result = _training_reader_response(bytes(stdout), bytes(stderr), process.returncode)
    if time.monotonic() > deadline:
        raise ValueError(f'Training record reader timed out during decoding; returncode={process.returncode}')
    return result


async def _close_training_readers(resources):
    """Drain the adapter's original resources before its loop may be closed."""
    import asyncio

    for pid, item in list(resources.items()):
        while item['draining'] is None:
            try:
                await asyncio.sleep(.01)
            except asyncio.CancelledError:
                continue
        if item['process'] is not None and item['process'].returncode is None:
            _stop_training_reader(item['process'])
        while not item['draining'].done():
            try:
                await asyncio.shield(item['draining'])
            except asyncio.CancelledError:
                continue
        await item['draining']
        resources.pop(pid, None)


def training_execution(project: dict, home: Path, operation: str, payload: dict, *, timeout: int = 20) -> dict:
    if operation == 'request':
        if sys.platform != 'linux':
            raise ValueError('Managed training execution requires Linux; use WSL2 and a trusted Linux container')
        return _training_process(project, 'worker', {'project': project, 'control_home': str(home),
            'operation': operation, **payload}, timeout, sdk=True, entrypoint='execution_main')
    entrypoint = 'from ergora.training_execution_protocol import inspect_main;inspect_main()'
    selection = {'project': project, 'control_home': str(home), **payload}
    observed = _training_reader(project, entrypoint, {**selection, 'operation': 'inspect'})
    # A current installation check cannot withhold the already-read history.
    try:
        sources = _training_reader(project, entrypoint, {**selection, 'operation': 'sources'}, timeout=5)
    except (OSError, ValueError) as error:
        sources = {'status': 'unavailable_or_changed', 'reason': str(error)}
    return {**observed, 'current_sources': sources}


def training_runtime_status(project: dict, spec: dict, *, run_id: str | None, timeout: int) -> dict:
    """Explicitly query the native training workflow, pinned to its original input."""
    return _training_process(project, 'runtime', {'spec': spec, 'run_id': run_id}, timeout, sdk=True)


def training_setup(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Preview or publish native baseline/runner configuration without starting work."""
    runner = operation in ('preview-runner', 'register-runner')
    if (operation == 'init-baseline' or runner) and sys.platform != 'linux':
        raise ValueError('Native training initialization and runner registration require Linux; use the registered runtime in WSL2')
    return _training_process(project, 'setup', {'project': project, 'control_home': str(home),
                             'operation': operation, **payload}, 20, sdk=False)


def training_preparation(project: dict, home: Path, operation: str, payload: dict) -> dict:
    """Prepare native files locally; their original intent remains explicitly recoverable."""
    if sys.platform != 'linux':
        raise ValueError('Native training preparation requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'preparation', {'project': project, 'control_home': str(home),
                             'operation': operation, **payload}, 20, sdk=False)


def training_submission(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Enter the selected training owner with durable submission checkpoints."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training submission requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'submission', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout, sdk=operation in ('dispatch', 'resume', 'fence'))


def training_evidence(project: dict, home: Path, payload: dict) -> dict:
    """Read the original archive without the optional SDK, services or release side effects."""
    if project.get('_original_registration') is not None:
        raise ValueError('Training evidence does not support registration recovery')
    return _training_reader(project, 'from ergora.reference_training_evidence import main;main()',
                            {'project': project, 'control_home': str(home), **payload}, timeout=20)


def training_release(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Checkpoint a native owner decision without creating a second approval authority."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training approval requires Linux; use the registered runtime in WSL2')
    return _training_process(project, 'release', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout, sdk=operation in ('dispatch', 'resume'))


def training_cancellation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Keep training cancellation delivery and native stop observations with their owners."""
    if operation != 'status' and sys.platform != 'linux':
        raise ValueError('Native training cancellation and executor observation require Linux; use WSL2')
    return _training_process(project, 'cancellation', {'project': project, 'control_home': str(home),
                              'operation': operation, **payload}, timeout,
                             sdk=operation in ('dispatch', 'resume', 'stop-status'))


def _training_process(project: dict, module: str, payload: dict, timeout: int, *, sdk: bool,
                      entrypoint: str = 'main') -> dict:
    recovery = project.get('_original_registration')
    if recovery is not None and module not in ('submission', 'cancellation'):
        raise ValueError('Original registration recovery is limited to submission reconciliation, cancellation and local fencing')
    if sdk and importlib.util.find_spec('temporalio') is None:
        raise ValueError('Training runtime operations require the optional Temporal SDK; install ergora[temporal] in this environment')
    execution = project['registration']['definition']['execution']
    installation = validate_installation(Path(execution['installation']), training=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                       AGENTFLOW_CONFIG_DIR=execution['config_directory'],
                       AGENTFLOW_STATE_DIR=execution['state_directory'])
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        Path(__file__).parent.parent, installation / 'local', installation / 'upstream/platform',
        installation / 'upstream/temporal', installation / 'upstream')))
    # Submission preflight invokes native Git. Keep that entire process group
    # under the existing owner, including timeout and interrupted-call cleanup.
    with TemporaryDirectory(prefix='ergora-training-operation-') as temporary:
        output = Path(temporary) / 'process'
        result = processes.run([sys.executable, '-P', '-c',
                               f'from ergora.reference_training_{module} import {entrypoint};{entrypoint}()'],
                              Path.cwd(), output, timeout + 5,
                              stdin=json.dumps({**payload, 'timeout': timeout}, allow_nan=False), env=environment)
        if result['status'] in ('timed_out', 'cancelled'):
            if module == 'submission' and payload['operation'] == 'fence':
                raise ValueError('Local training fence process timed out or stopped and its fence may already exist; repeat the same binding confirmation, execution stop remains unknown')
            raise ValueError('Training runtime process timed out or stopped; inspect the original intent/run, execution state remains unknown')
        if result['returncode']:
            lines = (output / 'stderr.txt').read_text(encoding='utf-8').strip().splitlines()
            raise ValueError(lines[-1] if lines else f'Training runtime process exited with status {result["returncode"]}')
        return json.loads((output / 'stdout.txt').read_text(encoding='utf-8'))


def _validate_training_baseline(baseline: dict) -> None:
    import perfctl

    perfctl.ident(baseline.get('baseline_id'))
    perfctl.commit(baseline.get('commit'), 'commit')
    for key in ('config_sha256', 'workload_fingerprint'):
        perfctl.sha(baseline.get(key), key)


def _training_records(payload: dict) -> dict:
    import base64
    from dataclasses import asdict
    import heapq
    from agent_platform.core import CONFIG, STATE, Blocked, slug
    from dev_platform import adapter
    from perf_temporal.models import Binding, Experiment
    import perfctl
    from .training_materials import read_raw

    project_id = slug(payload['project'])
    root, config = STATE.resolve(), CONFIG.resolve()
    prefix = 'training/projects/' + project_id + '/perf/'
    if os.name == 'nt':
        adapter.read_raw = _read_windows_contract
    files = {}

    def document(relative, *, optional=False, configuration=False):
        storage = config if configuration else root
        path = adapter.safe_file(storage, relative)
        if optional and not path.exists():
            return None
        raw = read_raw(path)
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('Training JSON must be an object: ' + relative)
        files[('config/' if configuration else 'state/') + relative] = hashlib.sha256(raw).hexdigest()
        return value

    baseline = document(prefix + 'baseline.json', optional=True)
    if baseline is not None:
        _validate_training_baseline(baseline)
    baseline_files = dict(files)

    def inspect(ident, *, detail=False):
        slug(ident)
        files.clear()
        manifest = document(prefix + 'experiments/' + ident + '/manifest.json')
        perfctl.validate(manifest)
        if manifest['experiment_id'] != ident or manifest['local_project'] != project_id:
            raise ValueError('Experiment does not belong to this project and native directory')
        registered_sha = files['state/' + prefix + 'experiments/' + ident + '/manifest.json']
        frozen = document('training/manifests/' + ident + '.json')
        if files['state/training/manifests/' + ident + '.json'] != registered_sha:
            raise ValueError('Frozen manifest bytes differ from the project registry')
        binding = Binding(ident, registered_sha, manifest['candidate_commit'], manifest['baseline_commit'])
        if frozen['candidate_sha'] != binding.candidate_sha or frozen['baseline_sha'] != binding.baseline_sha:
            raise ValueError('Manifest commit aliases differ from the original binding')
        spec = document('training/specs/' + ident + '.json')
        experiment = Experiment(**{**spec, 'binding': Binding(**spec['binding'])})
        experiment.validate()
        manifest_path = adapter.safe_file(root, 'training/manifests/' + ident + '.json')
        if (experiment.binding != binding or experiment.manifest_uri != manifest_path.as_uri()
                or experiment.max_run_seconds != manifest['max_run_seconds']):
            raise ValueError('Experiment spec differs from its frozen manifest binding')
        baseline_error = None
        if baseline is None:
            baseline_error = 'Baseline is not present in the selected registry'
        else:
            try:
                perfctl.baseline_ok(manifest, baseline)
            except perfctl.Invalid as error:
                baseline_error = str(error)
        job_prefix = 'training/jobs/' + ident + '/'
        request = document(job_prefix + 'request.json', optional=True)
        runner_id = slug(manifest['runner_template_id'])
        runner = document('training-runners/' + runner_id + '.json', optional=True, configuration=True)
        if runner is None and request is None:
            raise ValueError('Cannot verify experiment Git repository: current runner and original job request are both missing')

        def check_runner(value):
            if (value['runner_template_id'] != runner_id or value['project'] != project_id
                    or value['repo'] != payload['repo']):
                raise ValueError('Runner does not belong to the selected project and Git repository')

        if runner is not None:
            check_runner(runner)
        if request is not None:
            if request['experiment'] != spec or request['job_id'] != 'local-perf-' + ident:
                raise ValueError('Native job request differs from the original experiment')
            check_runner(request['runner'])
        started = document(job_prefix + 'started.json', optional=True)
        result = document(job_prefix + 'result.json', optional=True)
        fence = document('training/fences/' + ident + '.json', optional=True)
        negative = document('training/negative-results/' + ident + '.json', optional=True) if detail else None
        for value in (started, result, fence, negative):
            if value is not None and value['binding'] != asdict(binding):
                raise ValueError('Training record belongs to another immutable binding')
        for value in (started, result):
            if value is not None and (request is None or value['job_id'] != request['job_id']):
                raise ValueError('Training job result has no matching original request')
        from ergora.training_materials import input_descriptor, read_materials

        inputs = input_descriptor(manifest)
        for arm, raw_material in read_materials(root, manifest).items():
            files['state/' + inputs[arm]['path']] = hashlib.sha256(raw_material).hexdigest()
        gate = None
        gate_ref = result.get('gate') if result is not None else None
        if gate_ref is not None:
            expected = adapter.safe_file(root, job_prefix + 'gate-report.json')
            if gate_ref['report'] != str(expected):
                raise ValueError('Gate report is outside the original experiment job')
            gate = document(job_prefix + 'gate-report.json')
            if files['state/' + job_prefix + 'gate-report.json'] != gate_ref['report_sha256']:
                raise ValueError('Gate report bytes differ from the original result SHA')
            if gate['binding'] != asdict(binding) or gate['manifest_sha256'] != binding.manifest_sha:
                raise ValueError('Gate report belongs to another experiment manifest')
        screen_ref = result.get('screen') if result is not None else None
        screen_report = None
        if screen_ref is not None:
            screen_name = job_prefix + 'run-output/screen-result.json'
            expected = adapter.safe_file(root, screen_name)
            if screen_ref['report'] != str(expected):
                raise ValueError('Screen report is outside its original experiment job')
            screen_report = document(screen_name)
            if (files['state/' + screen_name] != screen_ref['report_sha256']
                    or screen_report['binding'] != asdict(binding) or gate_ref is not None
                    or manifest.get('execution', {}).get('operation') != 'training-screen-v1'):
                raise ValueError('Screen result raw, operation or binding changed')
        item = {'experiment_id': ident, 'binding': asdict(binding), 'track': manifest['track'],
                'baseline_id': manifest['baseline_id'], 'workload_fingerprint': manifest['workload_fingerprint'],
                'baseline_matches': baseline_error is None, 'baseline_error': baseline_error,
                'max_run_seconds': experiment.max_run_seconds, 'runtime_status': 'not_queried',
                'job_id': request['job_id'] if request else None, 'started_recorded': started is not None,
                'recorded_result_state': result['state'] if result else None, 'fence_recorded': fence is not None,
                'execution': manifest.get('execution', {'operation': 'full-verify'}), 'screen_ref': screen_ref,
                'recorded_screen': {'result_sha256': screen_ref['report_sha256'], 'decision': screen_report['decision'],
                    'achieved_quality_tier': screen_report['achieved_quality_tier']} if screen_report else None,
                'recorded_gate': {'passed': gate['passed'], 'evidence_sha256': gate['evidence_sha256'],
                                  'report_sha256': gate_ref['report_sha256'],
                                  'mlflow_run_id': gate_ref['mlflow_run_id']} if gate else None,
                'files': dict(files)}
        if detail:
            item.update(manifest=manifest, spec=spec, current_runner=runner, job_request=request,
                        started=started, result=result, gate_report=gate, screen_report=screen_report, fence=fence, negative_result=negative)
        return item

    result = {'baseline': baseline, 'baseline_files': baseline_files, 'runtime_status': 'not_queried'}
    if payload['experiment_id'] is not None:
        result['experiment'] = inspect(payload['experiment_id'], detail=True)
    else:
        after = payload['after']
        if after is not None:
            if not isinstance(after, str) or len(after) > 2048:
                raise ValueError('Invalid experiment directory cursor')
            after = os.fsdecode(base64.b64decode(after.encode('ascii'), altchars=b'-_', validate=True))
        directory = adapter.safe_file(root, prefix + 'experiments')
        if directory.exists():
            with os.scandir(directory) as entries:
                names = heapq.nsmallest(payload['limit'] + 1, (entry.name for entry in entries
                    if not entry.name.startswith('.') and (after is None or entry.name > after)))
        else:
            names = []
        count = min(len(names), payload['limit'])
        result.update(items=[], errors=[], inspected_entries=count,
                      next_after=base64.urlsafe_b64encode(os.fsencode(names[count - 1])).decode('ascii')
                      if len(names) > count else None)
        for name in names[:count]:
            try:
                result['items'].append(inspect(name))
            except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
                result['errors'].append({'experiment_id': name, 'error': str(error)})
    return result


def _training_files_main():
    from agent_platform.core import Blocked

    try:
        result = _training_records(json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))


def task_submission(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the registered full runtime for native admission and its local journal."""
    return _task_operation(project, home, 'submission', operation, payload, timeout)


def task_approval(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Use the same native lifecycle for exact owner decisions and signal recovery."""
    if operation.startswith('source-'):
        return task_design_source(project, home, operation, payload, timeout=timeout)
    if operation == 'inspect-plan':
        return task_plan(project, home, payload, timeout=timeout)
    return _task_operation(project, home, 'approval', operation, payload, timeout)


def task_plan(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Inspect the pending plan through the existing native approval boundary."""
    result = _task_operation(project, home, 'approval', 'inspect-plan', payload, timeout)
    return _checked_design_result(result)


def _checked_design_result(result: dict) -> dict:
    if 'design_read' not in result:
        if 'design_source_read' in result or 'design_source_validation' in result:
            raise ValueError('Design source handoff has no complete original design binding')
        return result
    # The registered native interpreter owns SDK/file reads, while the
    # application owns jsonschema. Never expose an unvalidated native handoff.
    from .contracts import validate

    read = result.pop('design_read')
    schema = json.loads((DATA / 'schemas/task-design-v1.json').read_text(encoding='utf-8'))
    profile, packet = read['profile'], read['packet']
    validate(profile, {'$defs': schema['$defs'], '$ref': '#/$defs/profile'}, 'Design inspection profile')
    limits = profile['limits']
    _validate_design_packet(packet, profile, schema)
    maximum = limits['inspection_bytes']
    if 'design_source_read' in result:
        _validate_source_read(result, schema, profile)
        maximum = result['design_source_read']['storage_profile']['limits']['inspection_bytes']
    result = _design_public_result({**result, 'design_read': read})
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > maximum:
        raise ValueError('Design inspection exceeds its creation read limit')
    return result


def _validate_design_packet(packet, profile, schema):
    from .contracts import validate

    limits = profile['limits']
    properties = {**schema['properties'], **{name: {**schema['properties'][name], 'maxItems': limits[name]}
                  for name in ('source_records', 'questions', 'knowledge_requirements')},
                  'revision': {**schema['properties']['revision'], 'maximum': limits['revisions']}}
    validate(packet, {**schema, 'properties': properties}, 'Design packet')


def validate_design_source_submission(value, operation, design_schema=None, profile=None):
    from .contracts import validate

    design_schema = design_schema or json.loads((DATA / 'schemas/task-design-v1.json').read_text())
    profile = profile or json.loads((DATA / 'design-profiles/framework-development-v1.json').read_text())
    source_schema = json.loads((DATA / 'schemas/task-design-source-v1.json').read_text())
    definitions = {**design_schema['$defs'], **source_schema['$defs']}
    if isinstance(value, dict) and set(value) & {'recorded_by', 'recorded_at', 'actor', 'recorded_actor', 'principal_type', 'role', 'attestation'}:
        raise ValueError('human_channel_unavailable: source submissions cannot provide recorder/owner evidence')
    if isinstance(value, dict) and isinstance(value.get('response'), dict):
        response = value['response']
        if response.get('origin') == 'owner-channel' or set(response) & {'recorded_by', 'recorded_at', 'actor', 'principal_type', 'role', 'attestation'}:
            raise ValueError('human_channel_unavailable: source responses cannot supply trusted/recorded actor evidence')
    branch = {'publish-design': 'publish', 'record-response': 'respond'}.get(operation)
    if branch is None:
        raise ValueError('Unsupported design source submission operation')
    validate(value, {'$defs': definitions, '$ref': '#/$defs/' + branch}, 'Design source submission')
    storage = json.loads((DATA / 'design-profiles/design-source-storage-v1.json').read_text())
    for name, limit in value.get('storage_limits', {}).items():
        if limit > storage['limits'][name]:
            raise ValueError('Design source storage limits may only tighten the built-in profile')
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(raw) > storage['limits']['intent_bytes']:
        raise ValueError('Complete source submission exceeds its source intent limit')
    if branch == 'publish':
        _validate_design_packet(value['packet'], profile, design_schema)
        for body in value['bodies']:
            validate({key: body[key] for key in ('path', 'sha256', 'bytes', 'media_type')},
                     {'$defs': design_schema['$defs'], '$ref': '#/$defs/body_ref'}, 'Design source body')
            encoded = body['text'].encode('utf-8')
            if len(encoded) != body['bytes'] or hashlib.sha256(encoded).hexdigest() != body['sha256']:
                raise ValueError('Design source body bytes/SHA differ from its original text')


def _validate_source_read(result, schema, profile):
    from .contracts import validate

    view, validation = result['design_source_read'], result['design_source_validation']
    source_schema = json.loads((DATA / 'schemas/task-design-source-v1.json').read_text())
    definitions = {**schema['$defs'], **source_schema['$defs']}
    validate(view, {'$defs': definitions, '$ref': '#/$defs/journal_view'}, 'Complete design source view')
    validate(validation, {'$defs': definitions, '$ref': '#/$defs/validation_handoff'}, 'Design source validation handoff')
    storage = json.loads((DATA / 'design-profiles/design-source-storage-v1.json').read_text())
    saved = view['storage_profile']
    from .task_envelopes import identity

    if view['source_storage_profile_sha256'] != identity(saved):
        raise ValueError('Saved design source storage profile digest differs from its complete object')
    if set(saved) != set(storage) or any(saved[key] != storage[key] for key in ('schema_version', 'kind', 'id')):
        raise ValueError('Unsupported saved design source storage profile')
    if set(saved['limits']) != set(storage['limits']):
        raise ValueError('Unsupported saved design source storage limit fields')
    for name, value in saved['limits'].items():
        if type(value) is not int or not 0 < value <= storage['limits'][name]:
            raise ValueError('Invalid saved design source storage limit: ' + name)
    if (type(view['material_revision']) is not int or view['material_revision'] < 1
            or not isinstance(view['records'], list) or not isinstance(view['pending'], list)
            or len(view['records']) + len(view['pending']) > saved['limits']['operations']):
        raise ValueError('Invalid complete source journal sequence/count')
    identifiers = [item['operation_id'] for item in validation['inputs']]
    if len(set(identifiers)) != len(identifiers) or len(identifiers) != len(view['records']) + len(view['pending']):
        raise ValueError('Incomplete or duplicate source validation records')
    for record in validation['inputs']:
        validate_design_source_submission(record['submission'], record['operation'], schema, profile)
        if record['response'] is not None:
            if record['response']['origin'] not in ('agent', 'reported-human'):
                raise ValueError('human_channel_unavailable: saved source response cannot authenticate an owner')
            validate(record['response'], {'$defs': schema['$defs'], '$ref': '#/$defs/response'}, 'Saved design response')
    _validate_design_packet(view['current_packet'], profile, schema)
    for record in view['records']:
        if record['packet'] is not None:
            _validate_design_packet(record['packet'], profile, schema)
        if record['response'] is not None:
            validate(record['response'], {'$defs': schema['$defs'], '$ref': '#/$defs/response'}, 'Saved design response')
    for body in view['bodies']:
        validate({key: body[key] for key in ('path', 'sha256', 'bytes', 'media_type')},
                 {'$defs': schema['$defs'], '$ref': '#/$defs/body_ref'}, 'Saved source body')
        encoded = body['text'].encode('utf-8')
        if len(encoded) != body['bytes'] or hashlib.sha256(encoded).hexdigest() != body['sha256']:
            raise ValueError('Saved source text differs from its raw-byte identity')


def _source_request_payload(operation: str, payload: dict, *, local_prepare: bool = False) -> None:
    from .contracts import validate

    common = {'task_id': {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$'},
        'operation_id': {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$'},
        'run_id': {'type': 'string', 'minLength': 1, 'maxLength': 128},
        **{name: {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
           for name in ('plan_sha256', 'parent_record_sha256', 'intent_sha256')},
        'source_operation': {'enum': ['publish-design', 'record-response']},
        'source': {'type': 'object'}, 'preflight': {'type': 'object'}}
    fields = {'source-inspect': ('task_id', 'run_id', 'plan_sha256'),
        'source-status': ('task_id', 'operation_id'),
        'source-prepare': ('task_id', 'operation_id', 'source_operation', 'source',
                           'parent_record_sha256', 'run_id', 'plan_sha256'),
        'source-prepare-resume': ('task_id', 'operation_id', 'intent_sha256'),
        'source-commit': ('task_id', 'operation_id', 'intent_sha256'),
        'source-resume': ('task_id', 'operation_id', 'intent_sha256')}.get(operation)
    if fields is None:
        raise ValueError('Unsupported design source operation')
    if local_prepare and operation == 'source-prepare':
        fields = (*fields, 'preflight')
    validate(payload, {'type': 'object', 'additionalProperties': False, 'required': list(fields),
                       'properties': {key: common[key] for key in fields}}, 'Design source operation payload')
    if 'run_id' in payload and payload['run_id'].strip() != payload['run_id']:
        raise ValueError('Design source run ID must retain its original bytes')


def _prepare_design_source(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Local revision-reservation phase; only checked tasks orchestration supplies preflight."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Design source timeout must be 1–60 seconds')
    if operation not in ('source-prepare', 'source-prepare-resume'):
        raise ValueError('Unsupported local source preparation')
    _source_request_payload(operation, payload, local_prepare=True)
    if operation == 'source-prepare':
        validate_design_source_submission(payload['source'], payload['source_operation'])
    result = _task_operation(project, home, 'approval', operation, payload, timeout)
    if operation == 'source-prepare':
        return {**result, 'source': _checked_design_result(result['source'])}
    return _checked_design_result(result)


def task_design_source(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Public source operations own their observation and cannot replace transport headers."""
    if type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('Design source timeout must be 1–60 seconds')
    _source_request_payload(operation, payload)
    if operation == 'source-prepare':
        validate_design_source_submission(payload['source'], payload['source_operation'])
        preflight = task_design_source(project, home, 'source-inspect',
            {key: payload[key] for key in ('task_id', 'run_id', 'plan_sha256')}, timeout=timeout)
        return _prepare_design_source(project, home, operation, {**payload, 'preflight': preflight}, timeout=timeout)
    if operation in ('source-commit', 'source-resume'):
        prepared = _task_operation(project, home, 'approval', 'source-prepare-resume', payload, timeout)
        inventory = prepared['design_source_validation']['inventory_sha256']
        _checked_design_result(prepared)
        payload = {**payload, 'source_inventory_sha256': inventory}
    result = _task_operation(project, home, 'approval', operation, payload, timeout)
    return _checked_design_result(result)



def _design_view(read: dict, plan_sha256: str, source=None) -> dict:
    from .task_design import inspect_packet
    from .task_envelopes import identity

    profile, packet = read['profile'], read['packet']
    inspection = inspect_packet(packet, profile, read['expected'], read['sources'], read['work_unit_ids'])
    snapshot = {'seed_plan_sha256': plan_sha256, 'packet_content_sha256': identity(packet),
                'design_profile_sha256': identity(profile), 'sources': inspection['sources']}
    design = {**snapshot, 'inspection_sha256': identity(snapshot), 'packet': packet,
        **inspection, 'inspection_only': True, 'runtime_enforced': False,
        'profile': {'source': 'built-in-companion-profile', 'frozen_for_task': False, 'document': profile},
        'binding_assurance': {'checked_original_fields': list(read['expected']),
                              'manifest_bound': 'manifest_digest' in read['expected'],
                              'work_unit_mapping_checked': read['work_unit_ids'] is not None,
                              'previous_revision_chain_checked': False,
                              'freshness_basis': 'packet-declared-observation'},
        'actor_assurance': {'status': 'unavailable', 'owner_binding': 'not_frozen_in_original_admission'},
        'capabilities': {'approve_design': False, 'resolve_questions': False, 'execute': False}}
    if source is not None:
        facts = dict(read['sources'])
        bodies = {item['path']: item for item in source['bodies']}
        for record in source['current_packet']['source_records']:
            if record['access'] == 'reference_only':
                facts[record['id']] = {'status': 'reference_only'}
            elif record['body']['path'] in bodies:
                body = bodies[record['body']['path']]
                facts[record['id']] = {'status': 'read', 'sha256': body['sha256'], 'bytes': body['bytes']}
        design['source_journal'] = {**source, 'current_inspection': inspect_packet(source['current_packet'],
            profile, read['expected'], facts, read['work_unit_ids'])}
    return design


def _design_public_result(result: dict) -> dict:
    repair = result.get('design_source_validation', {}).get('repair_required', [])
    if repair:
        return {key: value for key, value in {**result, 'source_repair_required': repair,
            'inspection_only': True, 'runtime_enforced': False}.items()
            if key not in ('design_read', 'design_source_read', 'design_source_validation', 'materials', 'receipt')}
    public = {key: value for key, value in result.items()
              if key not in ('design_read', 'design_source_read', 'design_source_validation')}
    if 'design_read' in result:
        public['design'] = _design_view(result['design_read'], result['plan_sha256'], result.get('design_source_read'))
    return public



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


def task_handoff(project: dict, home: Path, payload: dict, *, timeout: int) -> dict:
    """Collect original published evidence into the explicitly selected new file."""
    return _task_operation(project, home, 'reconciliation', 'export-handoff', payload, timeout)


def task_reconciliation(project: dict, home: Path, operation: str, payload: dict, *, timeout: int) -> dict:
    """Reconcile the original closed run through its durable native boundary."""
    return _task_operation(project, home, 'reconciliation', operation, payload, timeout)


def _task_operation(project: dict, home: Path, component: str, operation: str, payload: dict, timeout: int) -> dict:
    inspection = {'inspect-plan': 'Plan', 'inspect-events': 'Task event', 'inspect-job': 'Job evidence',
                  'inspect-index': 'Task evidence index', 'export-handoff': 'Task handoff'}.get(operation)
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
                                input=json.dumps({**payload, 'project': project, 'control_home': str(home),
                                                  'operation': operation, 'timeout': timeout}, allow_nan=False),
                                capture_output=True, text=True, encoding='utf-8', env=environment, timeout=timeout + 5)
    except subprocess.TimeoutExpired as error:
        if operation.startswith('source-'):
            raise ValueError('Design source process timed out; inspect saved source state before recovering this operation') from error
        if operation == 'export-handoff':
            raise ValueError('Task handoff process timed out; inspect the output file before collecting again') from error
        if inspection:
            raise ValueError(inspection + ' inspection process timed out; query the original run before inspecting again') from error
        raise ValueError(f'Task {component} process timed out; inspect task {component} and resume its original intent') from error
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        detail = lines[-1] if lines else f'Native {component} process exited with status {result.returncode}'
        if operation.startswith('source-'):
            raise ValueError(detail + '; inspect task design operation before recovering its original intent')
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
    from . import task_envelopes

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
            envelope = spec
            spec, composition = task_envelopes.unwrap(envelope)
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
            if composition is not None:
                item['composition'] = task_envelopes.summary(envelope)
            if detail:
                snapshot = adapter.safe_file(root, 'tasks/' + task_id + '/agent-bindings.json')
                bindings, bindings_sha = document(task_id, 'agent-bindings.json') if snapshot.exists() else (None, None)
                if bindings is not None and bindings.get('reference_project') != payload['project']:
                    raise ValueError('Frozen agent snapshot project mismatch')
                item.update(spec=spec, frozen_project=project, agent_bindings=bindings,
                            agent_bindings_file_sha256=bindings_sha)
                if composition is not None:
                    item['admission_envelope'] = envelope
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
