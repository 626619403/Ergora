import configparser
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import xmlrpc.client

import pytest

from ergora import reference, registrations, services
from ergora.state import State


def wait_for_fixture_log(runtime):
    deadline = time.monotonic() + 5
    path = runtime / "logs/temporal.log"
    while time.monotonic() < deadline:
        if path.exists():
            with path.open("rb") as stream:
                if b"fixture service ready" in stream.read(256):
                    return
        time.sleep(.05)
    raise AssertionError("The controlled service did not write its readiness marker")


@pytest.fixture
def stack():
    if sys.platform != "linux":
        pytest.skip("Supervisor services run in Linux/WSL2")
    pytest.importorskip("supervisor")
    # Unix socket paths have a platform byte limit; no persistent user data is stored here.
    with tempfile.TemporaryDirectory(prefix="ergora-svc-") as temporary:
        root = Path(temporary)
        installation = root / "installation with space 项目"
        for part in ("local", "upstream/platform"):
            shutil.copytree(reference.ROOT / "platform" / part, installation / part)
        binary = installation / ".venv/bin"
        binary.mkdir(parents=True)
        (binary / "python").symlink_to(sys.executable)
        (binary / "supervisord").symlink_to(Path(sys.executable).parent / "supervisord")
        runtime, config = root / "runtime", root / "config"
        (runtime / "logs").mkdir(parents=True)
        config.mkdir()
        (config / "supervisor.d").mkdir()
        (config / "platform.json").write_text('{"execution_enabled": false}', encoding="utf-8")
        env = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(config), AGENTFLOW_STATE_DIR=str(runtime),
                   PYTHONPATH=str(installation / "local"))
        subprocess.run([sys.executable, "-c", "from agent_platform.setup import supervisor_config; supervisor_config()"], env=env, check=True)
        for path in (config / "supervisor.d").glob("*.ini"):
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(path)
            for section in parser.sections():
                parser[section].update(startsecs="0", stopwaitsecs="1", autorestart="false")
            with path.open("w", encoding="utf-8") as stream:
                parser.write(stream)
        (installation / "bin").mkdir()
        program = installation / "bin/temporal"
        program.write_text(f"#!{sys.executable}\n" + '''import os,signal,time
from pathlib import Path
root=Path(os.environ['AGENTFLOW_STATE_DIR'])
(root/'temporal.started').write_text(str(os.getpid()))
signal.signal(signal.SIGTERM,signal.SIG_IGN if (root/'ignore-term').exists() else lambda *_: exit(0))
print('fixture service ready',flush=True)
while True: time.sleep(.1)
''', encoding="utf-8")
        program.chmod(0o700)
        repo = root / "repo"
        repo.mkdir()
        env = dict(os.environ, GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.test",
                   GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.test")
        for argv in (["init"], ["-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "baseline"]):
            subprocess.run(["git", "-C", str(repo), *argv], env=env, check=True, capture_output=True)
        state = State(root / "control")
        definition = {"schema_version": 1, "id": "demo", "repo": str(repo), "templates": ["repository-governance"],
                      "execution": {"installation": str(installation), "config_directory": str(config), "state_directory": str(runtime)},
                      "tracker": {"kind": "local", "project": "local/demo"}, "allowed_paths": ["src"],
                      "checks": {key: [sys.executable, "-c", "pass"] for key in ("behavior", "architecture", "knowledge")},
                      "scope_policy": {"schema_version": 1, "protected_paths": [".git"]}}
        registrations.register(state, definition, 0)
        try:
            yield state, runtime, config
        finally:
            folder = runtime / "ergora-services"
            if (folder / "s.sock").exists():
                try:
                    services._rpc(folder / "s.sock", "shutdown")
                except xmlrpc.client.Fault as error:
                    if error.faultCode != 6:  # Supervisor has already entered SHUTDOWN_STATE.
                        raise
                deadline = time.monotonic() + 10
                while (folder / "s.sock").exists() and time.monotonic() < deadline:
                    time.sleep(.1)
                assert not (folder / "s.sock").exists(), "Fixture Supervisor did not stop"


def test_selected_start_is_idempotent_and_does_not_autostart_other_programs(stack):
    state, runtime, config = stack
    original = (config / "supervisord.ini").read_bytes()
    result = services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    assert result["outcome"] == "confirmed" and result["task_readiness"] == "not_checked"
    states = {p["name"]: p for p in result["services"]}
    assert states["temporal"]["statename"] == "RUNNING"
    assert all(p["statename"] == "STOPPED" for name, p in states.items() if name != "temporal")
    again = services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    assert next(p for p in again["services"] if p["name"] == "temporal")["pid"] == states["temporal"]["pid"]
    assert (config / "supervisord.ini").read_bytes() == original
    stopped = services.control(state, "demo", "stop", ["temporal"], 1, confirm=True, timeout=5)
    assert stopped["outcome"] == "confirmed"
    assert next(p for p in stopped["services"] if p["name"] == "temporal")["statename"] == "STOPPED"
    assert services.control(state, "demo", "shutdown", [], 1, confirm=True, timeout=5)["outcome"] == "confirmed"


def test_logs_are_bounded_and_return_native_cursor_for_large_files(stack):
    state, runtime, _ = stack
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    # Sparse large file distinguishes seeking from loading the entire log.
    path = runtime / "logs/temporal.log"
    with path.open("r+b") as stream:
        tail = b"end of large fixture log\n"
        stream.seek(64 * 1024 * 1024 - 128)
        stream.write(b"x" * (128 - len(tail)) + tail)
    first = services.logs(state, "demo", "temporal", limit=128)
    assert len(first["text"].encode()) <= 128 and first["text"].endswith("end of large fixture log\n")
    assert first["overflow"] is True
    with path.open("ab") as stream:
        stream.write(b"next chunk\n")
    following = services.logs(state, "demo", "temporal", offset=first["next_offset"], limit=128)
    assert following["text"] == "next chunk\n" and following["next_offset"] > first["next_offset"]
    assert services.logs(state, "demo", "temporal", offset=following["next_offset"], limit=128)["text"] == ""
    path.write_text("rotated log\n", encoding="utf-8")
    rotated = services.logs(state, "demo", "temporal", offset=following["next_offset"], limit=128)
    assert rotated["rotated"] is True and rotated["text"] == "rotated log\n"


def test_shutdown_reconciles_a_daemon_already_shutting_down(stack):
    state, runtime, _ = stack
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    services._rpc(runtime / "ergora-services/s.sock", "shutdown")
    result = services.control(state, "demo", "shutdown", [], 1, confirm=True, timeout=5)
    assert result["outcome"] == "confirmed" and result["daemon"] == "not_running"


def test_non_utf8_bytes_are_visible_with_replacement(stack):
    state, runtime, _ = stack
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    with (runtime / "logs/temporal.log").open("ab") as stream:
        stream.write(b"\xffbinary log bytes")
    assert "\ufffdbinary log bytes" in services.logs(state, "demo", "temporal")["text"]


def test_utf8_default_window_and_partial_append_keep_character_boundaries(stack):
    state, runtime, _ = stack
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    path = runtime / "logs/temporal.log"
    path.write_text("文" * 4000, encoding="utf-8")
    report = services.logs(state, "demo", "temporal")
    assert report["text"] == "文" * 2730 and report["next_offset"] == 12000
    assert report["bytes_read"] == 8192 and report["pending_bytes"] == 0
    with path.open("ab") as stream:
        stream.write("中".encode("utf-8")[:2])
    partial = services.logs(state, "demo", "temporal", offset=12000, limit=4)
    assert partial["text"] == "" and partial["pending_bytes"] == 2 and partial["next_offset"] == 12000
    with path.open("ab") as stream:
        stream.write("中".encode("utf-8")[2:])
    complete = services.logs(state, "demo", "temporal", offset=partial["next_offset"], limit=4)
    assert complete["text"] == "中" and complete["next_offset"] == 12003
    with path.open("ab") as stream:
        stream.write("文".encode("utf-8") + "😀".encode("utf-8")[:1])
    first = services.logs(state, "demo", "temporal", offset=12003, limit=4)
    assert first["text"] == "文" and first["pending_bytes"] == 1 and first["next_offset"] == 12006
    with path.open("ab") as stream:
        stream.write("😀".encode("utf-8")[1:])
    second = services.logs(state, "demo", "temporal", offset=first["next_offset"], limit=4)
    assert second["text"] == "😀" and second["pending_bytes"] == 0 and second["next_offset"] == 12010
    overflow = services.logs(state, "demo", "temporal", offset=12003, limit=4)
    assert overflow["overflow"] is True and overflow["text"] == "😀" and overflow["next_offset"] == 12010


def test_nonregular_native_log_cannot_block_reader(stack):
    state, runtime, _ = stack
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    path = runtime / "logs/temporal.log"
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(ValueError, match="regular native file"):
        services.logs(state, "demo", "temporal")


def test_stop_retry_waits_for_real_stopping_process(stack, monkeypatch):
    state, runtime, config = stack
    (runtime / "ignore-term").touch()
    path = config / "supervisor.d/temporal.ini"
    path.write_text(path.read_text().replace("stopwaitsecs = 1", "stopwaitsecs = 3"))
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    wait_for_fixture_log(runtime)
    original = services._rpc
    calls = []
    def rpc(path, method, *args, **kwargs):
        if method == "stopProcess":
            calls.append(method)
        return original(path, method, *args, **kwargs)
    monkeypatch.setattr(services, "_rpc", rpc)
    first = services.control(state, "demo", "stop", ["temporal"], 1, confirm=True, timeout=1)
    assert first["outcome"] == "unconfirmed"
    assert next(p for p in first["services"] if p["name"] == "temporal")["statename"] == "STOPPING"
    second = services.control(state, "demo", "stop", ["temporal"], 1, confirm=True, timeout=5)
    assert second["outcome"] == "confirmed" and calls == ["stopProcess"]


def test_mutations_require_revision_confirmation_and_consistent_registration(stack):
    state, _, config = stack
    with pytest.raises(ValueError, match="confirmation"):
        services.control(state, "demo", "stop", ["temporal"], 1)
    with pytest.raises(ValueError, match="revision"):
        services.control(state, "demo", "start", ["temporal"], 0)
    with pytest.raises(ValueError, match="revision"):
        services.control(state, "demo", "start", ["temporal"], 1.0)
    with pytest.raises(ValueError, match="explicit distinct"):
        services.control(state, "demo", "start", [], 1)
    path = config / "projects/demo.json"
    path.write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="registration files differ"):
        services.control(state, "demo", "start", ["temporal"], 1)


def test_legacy_stack_and_wrong_control_owner_are_not_taken_over(stack):
    state, runtime, _ = stack
    legacy = runtime / "supervisor.sock"
    legacy.touch()
    with pytest.raises(ValueError, match="original Supervisor"):
        services.control(state, "demo", "start", ["temporal"], 1)
    with pytest.raises(ValueError, match="original Supervisor"):
        services.control(state, "demo", "stop", ["temporal"], 1, confirm=True)
    assert services.status(state, "demo")["legacy_socket_present"] is True
    legacy.unlink()
    folder = runtime / "ergora-services"
    (folder / "owner.json").write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="different control"):
        services.control(state, "demo", "start", ["temporal"], 1)


def test_stale_pid_and_stopping_service_are_not_treated_as_restartable(stack, monkeypatch):
    state, runtime, _ = stack
    folder = runtime / "ergora-services"
    folder.mkdir()
    (folder / "supervisord.pid").write_text("123", encoding="utf-8")
    result = services.control(state, "demo", "start", ["temporal"], 1, timeout=1)
    assert result["outcome"] == "unconfirmed"
    (folder / "supervisord.pid").unlink()
    services.control(state, "demo", "start", ["temporal"], 1, timeout=5)
    original = services._snapshot
    def stopping(folder):
        result = original(folder)
        for item in result["services"]:
            if item["name"] == "temporal":
                item["statename"] = "STOPPING"
        return result
    monkeypatch.setattr(services, "_snapshot", stopping)
    with pytest.raises(ValueError, match="Stop is not confirmed"):
        services.control(state, "demo", "start", ["temporal"], 1)
    stopped = services.control(state, "demo", "stop", ["temporal"], 1, confirm=True, timeout=1)
    assert stopped["outcome"] == "unconfirmed"


def test_absent_selected_program_does_not_partially_start_other_selection(stack):
    state, runtime, config = stack
    (config / "supervisor.d/mlflow.ini").unlink()
    with pytest.raises(ValueError, match="absent"):
        services.control(state, "demo", "start", ["temporal", "mlflow"], 1, timeout=5)
    assert all(item["statename"] == "STOPPED" for item in services.status(state, "demo")["services"])
    assert not (runtime / "temporal.started").exists()


def test_api_and_cli_share_status_and_protected_mutations(stack):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from ergora.web import create_app
    state, _, _ = stack
    client = TestClient(create_app(state.root), base_url="http://127.0.0.1")
    uri = "/api/projects/demo/services"
    assert client.get(uri).json() == services.status(state, "demo")
    body = {"action": "start", "names": ["temporal"], "revision": 1, "timeout": 5}
    assert client.post(uri, json=body).status_code == 403
    result = client.post(uri, json=body, headers={"X-Ergora-Request": "1"})
    assert result.status_code == 200 and result.json()["outcome"] == "confirmed"
    response = client.get(uri + "/temporal/logs?limit=1024")
    assert response.status_code == 200 and response.json()["requested_bytes"] == 1024
    observed = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "services", "status", "demo"], capture_output=True, text=True, timeout=10)
    assert observed.returncode == 0, observed.stderr
    assert json.loads(observed.stdout) == services.status(state, "demo")


@pytest.mark.skipif(sys.platform == "linux", reason="Native unsupported-platform check")
def test_native_windows_reports_wsl_requirement(tmp_path):
    with pytest.raises(ValueError, match="WSL2"):
        services.status(State(tmp_path), "unused")


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_text_window_rejects_sizes_smaller_than_a_utf8_character(tmp_path, limit):
    with pytest.raises(ValueError, match="4–65536"):
        services.logs(State(tmp_path), "unused", "temporal", limit=limit)


@pytest.mark.skipif(sys.platform != "linux", reason="Unix Supervisor transport")
def test_lost_mutating_rpc_response_is_not_automatically_replayed():
    with tempfile.TemporaryDirectory(prefix="ergora-rpc-") as temporary:
        path = Path(temporary) / "s.sock"
        with socket.socket(socket.AF_UNIX) as server:
            server.bind(str(path))
            server.listen()
            server.settimeout(.5)
            received = []
            def consume():
                while True:
                    try:
                        connection, _ = server.accept()
                    except TimeoutError:
                        return
                    with connection, connection.makefile("rb") as stream:
                        length = 0
                        while line := stream.readline():
                            if line == b"\r\n":
                                break
                            if line.lower().startswith(b"content-length:"):
                                length = int(line.split(b":", 1)[1])
                        received.append(stream.read(length))
                        # The request reached the server, but its response is lost.
            worker = threading.Thread(target=consume)
            worker.start()
            try:
                with pytest.raises(http.client.RemoteDisconnected):
                    services._rpc(path, "startProcess", "temporal", False, timeout=.2)
            finally:
                worker.join(timeout=2)
            assert not worker.is_alive() and len(received) == 1
