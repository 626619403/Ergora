"""Explicit local service operations; Supervisor owns process lifetime and logs."""

import codecs
import configparser
import glob
import http.client
import io
import json
import os
from pathlib import Path
import shlex
import socket
import stat
import subprocess
import sys
import tempfile
import time
import xmlrpc.client
from xml.parsers.expat import ExpatError

from . import reference, registrations
from .state import State, file_lock


NAMES = ("temporal", "mlflow", "worker", "executor", "a2a", "training-worker")
_COMMUNICATION_ERRORS = (OSError, http.client.HTTPException, xmlrpc.client.ProtocolError, xmlrpc.client.ResponseError, ExpatError)
_STOPPED = {"STOPPED", "EXITED", "FATAL"}


class _UnixConnection(http.client.HTTPConnection):
    def __init__(self, path: Path, timeout: float):
        super().__init__("localhost", timeout=timeout)
        self.path = str(path)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


class _UnixTransport(xmlrpc.client.Transport):
    def __init__(self, path: Path, timeout: float):
        super().__init__()
        self.path, self.timeout = path, timeout

    def make_connection(self, host):
        self._connection = host, _UnixConnection(self.path, self.timeout)
        return self._connection[1]

    def request(self, host, handler, request_body, verbose=False):
        # The stdlib retries a lost response once, which can replay a mutating RPC.
        return self.single_request(host, handler, request_body, verbose)


def _rpc(path: Path, method: str, *args, timeout: float = 1):
    with xmlrpc.client.ServerProxy("http://localhost/RPC2", transport=_UnixTransport(path, timeout)) as proxy:
        return getattr(proxy.supervisor, method)(*args)


def _context(state: State, project_id: str) -> tuple[dict, dict, Path]:
    if sys.platform != "linux":
        raise ValueError("Local Supervisor service management requires Linux; use WSL2")
    project = state.project(project_id)
    registration = project.get("registration")
    if not registration or registration["status"] != "published":
        raise ValueError("Services require a published unified project registration")
    execution = registration["definition"]["execution"]
    reference.validate_installation(Path(execution["installation"]))
    return project, execution, Path(execution["state_directory"]) / "ergora-services"


def _snapshot(folder: Path) -> dict:
    path = folder / "s.sock"
    if not path.exists():
        return {"daemon": "unconfirmed" if (folder / "supervisord.pid").exists() else "not_running", "services": []}
    try:
        processes = _rpc(path, "getAllProcessInfo")
        return {"daemon": "running", "services": [
            {key: item[key] for key in ("name", "statename", "pid", "exitstatus", "start", "stop")}
            for item in processes if item["name"] in NAMES]}
    except xmlrpc.client.Fault as error:
        return {"daemon": "stopping" if error.faultCode == 6 else "unconfirmed", "services": []}
    except _COMMUNICATION_ERRORS:
        return {"daemon": "unconfirmed", "services": [],
                "remediation": "The socket exists but Supervisor did not answer; reconcile its process before restarting. Do not remove a live socket."}


def status(state: State, project_id: str) -> dict:
    project, execution, folder = _context(state, project_id)
    return {"project": project_id, "project_revision": project["revision"], "execution": execution,
            "scope": "ergora-managed-stack", "shared_stack": True,
            "legacy_socket_present": (Path(execution["state_directory"]) / "supervisor.sock").exists(),
            "task_readiness": "not_checked", **_snapshot(folder)}


def _write(path: Path, content: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _prepare(state: State, execution: dict, folder: Path, identity: dict) -> Path:
    owner = folder / "owner.json"
    path = folder / "s.sock"
    if len(os.fsencode(path)) > 107:
        raise ValueError("Supervisor Unix socket path is too long; use a shorter persistent execution state_directory")
    configuration = Path(execution["config_directory"])
    original = configuration / "supervisord.ini"
    parser = configparser.ConfigParser(interpolation=None)
    with original.open(encoding="utf-8") as stream:
        parser.read_file(stream)
    if parser.has_section("include"):
        for pattern in shlex.split(parser["include"]["files"]):
            parser.read(sorted(glob.glob(str(configuration / pattern))), encoding="utf-8")
    output = configparser.ConfigParser(interpolation=None)
    for section in ("supervisord", "unix_http_server", "rpcinterface:supervisor", "supervisorctl"):
        if section not in parser:
            raise ValueError(f"Reference Supervisor configuration is incomplete: {section}; initialize the selected reference config directory first")
        output[section] = dict(parser[section])
    if Path(parser["unix_http_server"]["file"]).resolve() != Path(execution["state_directory"]) / "supervisor.sock":
        raise ValueError("Reference Supervisor configuration belongs to another state directory; initialize the selected execution configuration first")
    output["supervisord"].update(logfile=str(folder / "supervisord.log"), pidfile=str(folder / "supervisord.pid"), nodaemon="false")
    output["unix_http_server"].update(file=str(path), chmod="0700")
    output["supervisorctl"]["serverurl"] = "unix://" + str(path)
    for name in NAMES:
        section = "program:" + name
        if section not in parser:
            continue
        output[section] = dict(parser[section])
        output[section]["autostart"] = "false"
        command = [str(Path(execution["installation"]) / ".venv/bin/python"), "-m", "agent_platform.service", name]
        if name == "executor":
            command = [sys.executable, "-m", "ergora", "--home", str(state.root), "reference", "executor",
                       "--installation", execution["installation"]]
        elif name == "worker":
            command = reference.worker_command(Path(execution["installation"]))
        output[section]["command"] = shlex.join(command).replace("%", "%%")
        output[section]["directory"] = execution["installation"]
    content = io.StringIO()
    output.write(content)
    _write(folder / "supervisord.ini", content.getvalue())
    _write(owner, json.dumps(identity, ensure_ascii=False, indent=2) + "\n")
    return folder / "supervisord.ini"


def control(state: State, project_id: str, action: str, names: list[str], revision: int,
            *, confirm: bool = False, timeout: int = 30) -> dict:
    if action not in ("start", "stop", "shutdown"):
        raise ValueError("Service action must be start, stop or shutdown")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60:
        raise ValueError("Service timeout must be 1–60 seconds")
    if action in ("stop", "shutdown") and confirm is not True:
        raise ValueError("Stopping services can interrupt tasks; provide explicit confirmation")
    if (action == "shutdown" and names) or (action != "shutdown" and (not names or len(set(names)) != len(names) or any(n not in NAMES for n in names))):
        raise ValueError(f"Choose explicit distinct service names from {NAMES}; shutdown accepts no names")
    project, execution, folder = _context(state, project_id)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision != project["revision"]:
        raise ValueError("Project revision changed; reload before managing services")
    publication = registrations.status(state, project_id)
    if not publication["consistent"]:
        raise ValueError("Project registration files differ; reconcile publication before managing services")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with file_lock(folder / "lock", blocking=False):
        # Recheck under the service lock; project binding updates can occur independently.
        if state.project(project_id)["revision"] != revision:
            raise ValueError("Project revision changed; reload before managing services")
        if (Path(execution["state_directory"]) / "supervisor.sock").exists():
            raise ValueError("An original Supervisor socket exists. Stop and reconcile that stack with its original agentflow services stop before using the managed stack; no services were taken over")
        identity = {"schema_version": 1, "control_directory": str(state.root), "execution": execution}
        owner = folder / "owner.json"
        if owner.exists() and json.loads(owner.read_text(encoding="utf-8")) != identity:
            raise ValueError("This service stack belongs to a different control directory or execution configuration")
        deadline = time.monotonic() + timeout
        before = _snapshot(folder)
        if before["daemon"] == "running" and not owner.exists():
            raise ValueError("Managed socket has no ownership record; reconcile the existing daemon before managing services")
        if before["daemon"] == "unconfirmed" or (before["daemon"] == "stopping" and action != "shutdown"):
            return {"project": project_id, "action": action, "outcome": "unconfirmed", **before}
        if before["daemon"] == "not_running" and action != "start":
            return {"project": project_id, "action": action, "outcome": "confirmed", **before}
        if before["daemon"] == "not_running":
            config = _prepare(state, execution, folder, identity)
            environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=execution["config_directory"],
                               AGENTFLOW_STATE_DIR=execution["state_directory"])
            environment["PYTHONPATH"] = os.pathsep.join(map(str, (
                Path(execution["installation"]) / "local", Path(execution["installation"]) / "upstream/platform",
                Path(execution["installation"]) / "upstream/temporal", Path(execution["installation"]) / "upstream")))
            try:
                launched = subprocess.run([str(Path(execution["installation"]) / ".venv/bin/supervisord"), "-c", str(config)],
                                          env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                          timeout=max(.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                return {"project": project_id, "action": action, "outcome": "unconfirmed", **_snapshot(folder)}
            if launched.returncode:
                raise ValueError("Supervisor did not start; inspect the managed supervisord.log and installed Supervisor package")
        path = folder / "s.sock"
        try:
            if action == "shutdown" and before["daemon"] != "stopping":
                _rpc(path, "shutdown")
            elif action != "shutdown":
                current = {item["name"]: item["statename"] for item in _snapshot(folder)["services"]}
                for name in names:
                    if name not in current:
                        raise ValueError(f"Selected service is absent from the reference Supervisor config: {name}")
                    if action == "start" and current[name] == "STOPPING":
                        raise ValueError("Stop is not confirmed; wait for STOPPED before starting again")
                for name in names:
                    if (action == "start" and current[name] not in {"RUNNING", "STARTING", "BACKOFF"}) or (action == "stop" and current[name] not in _STOPPED | {"STOPPING"}):
                        _rpc(path, "startProcess" if action == "start" else "stopProcess", name, False,
                             timeout=max(.01, min(1, deadline - time.monotonic())))
            while time.monotonic() < deadline:
                observed = _snapshot(folder)
                statuses = {item["name"]: item["statename"] for item in observed["services"]}
                confirmed = observed["daemon"] == "not_running" if action == "shutdown" else (
                    observed["daemon"] == "running" and all(statuses.get(name) == "RUNNING" if action == "start"
                                                            else statuses.get(name) in _STOPPED for name in names))
                if confirmed:
                    return {"project": project_id, "action": action, "selected": names, "outcome": "confirmed",
                            "task_readiness": "not_checked", **observed}
                if action == "start" and any(statuses.get(name) == "FATAL" for name in names):
                    return {"project": project_id, "action": action, "selected": names, "outcome": "failed",
                            "task_readiness": "not_checked", **observed}
                time.sleep(.1)
        except _COMMUNICATION_ERRORS:
            pass  # A request may have reached Supervisor; only observation can confirm it.
        except xmlrpc.client.Fault as error:
            raise ValueError(f"Supervisor rejected the service operation (fault {error.faultCode})") from error
        return {"project": project_id, "action": action, "selected": names, "outcome": "unconfirmed",
                "task_readiness": "not_checked", **_snapshot(folder)}


def logs(state: State, project_id: str, name: str, *, offset: int = 0,
         limit: int = 8192, stderr: bool = False) -> dict:
    if name not in NAMES or isinstance(limit, bool) or not isinstance(limit, int) or not 4 <= limit <= 65536:
        raise ValueError("Choose a supported service and a text log window of 4–65536 bytes")
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 2**63 - 1:
        raise ValueError("Log offset must be a nonnegative 64-bit file offset")
    _, _, folder = _context(state, project_id)
    try:
        process = _rpc(folder / "s.sock", "getProcessInfo", name)
        filename = process["stderr_logfile" if stderr else "stdout_logfile"]
        if not filename:
            raise ValueError("The selected service has no native log file")
        # Supervisor decodes its RPC byte slices before returning them, which can split UTF-8.
        # Query its path, then perform one bounded local read instead.
        descriptor = os.open(filename, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("Service logs require a regular native file")
            size = stream.seek(0, os.SEEK_END)
            rotated = offset > size
            start = 0 if rotated else offset
            overflow = size - start > limit
            if overflow:
                start = size - limit
            stream.seek(start)
            raw = stream.read(limit)
        read_bytes = len(raw)
        if start:
            prefix = 0
            while prefix < min(3, len(raw)) and raw[prefix] & 0xC0 == 0x80:
                prefix += 1
            start += prefix
            raw = raw[prefix:]
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        text = decoder.decode(raw, final=False)
        pending = len(decoder.getstate()[0])
        following = start + len(raw) - pending
    except (*_COMMUNICATION_ERRORS, xmlrpc.client.Fault) as error:
        raise ValueError("Service log is unavailable; inspect managed services status and the native log file") from error
    return {"project": project_id, "service": name, "stream": "stderr" if stderr else "stdout",
            "text": text, "next_offset": following, "overflow": overflow, "rotated": rotated,
            "requested_bytes": limit, "bytes_read": read_bytes, "pending_bytes": pending}
