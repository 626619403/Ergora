import asyncio
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import pytest

from ergora import projects, research
from ergora.state import State


@pytest.fixture
def source_project(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    projects.create(state, "other", repo)
    source = {"text": "<h1>Version one</h1><script>never execute this</script>"}
    started, release = threading.Event(), threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            source["requests"] = source.get("requests", 0) + 1
            if self.path == "/short-body":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b"short")
                self.close_connection = True
                return
            if self.path == "/broken":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                self.wfile.write(b"A\r\nabc")
                self.wfile.flush()
                self.close_connection = True
                return
            if self.path == "/slow-headers":
                started.set()
                try:
                    self.wfile.write(b"HTTP/1.1 200 OK\r\n")
                    for index in range(12):
                        self.wfile.write(f"X-Wait-{index}: 1\r\n".encode())
                        self.wfile.flush()
                        time.sleep(.25)
                    self.wfile.write(b"Content-Type: text/plain\r\nContent-Length: 2\r\n\r\nok")
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path == "/large-redirect":
                self.send_response(302)
                self.send_header("Location", "/tiny")
                self.send_header("Content-Length", "100000")
                self.end_headers()
                try:
                    self.wfile.write(b"x")
                    self.wfile.flush()
                    release.wait(timeout=3)
                    self.wfile.write(b"x" * 99999)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/page")
                self.end_headers()
                return
            body = ("x" * 1000 if self.path == "/big" else "ok" if self.path == "/tiny" else source["text"]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.path == "/slow":
                self.wfile.write(body[:1])
                self.wfile.flush()
                started.set()
                release.wait(timeout=5)
                try:
                    self.wfile.write(body[1:])
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, f"http://127.0.0.1:{server.server_port}", source, started, release
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join()


def test_sources_are_snapshotted_deduplicated_scoped_and_reviewed(source_project):
    state, base, source, _, _ = source_project
    initial = research.run(state, "demo", [base + "/page"], allow_private=True, run_id="first")
    assert initial["status"] == "succeeded" and initial["results"][0]["changed"]
    assert research.run(state, "demo", [base + "/page"], allow_private=True, run_id="first") == initial
    with pytest.raises(ValueError, match="different frozen request"):
        research.run(state, "demo", [base + "/big"], allow_private=True, run_id="first")
    unchanged = research.run(state, "demo", [base + "/page"], allow_private=True)
    assert not unchanged["results"][0]["changed"]
    source["text"] = "<p>Version two</p>"
    changed = research.run(state, "demo", [base + "/page"], allow_private=True)
    assert changed["results"][0]["sha"] != initial["results"][0]["sha"]
    pid = initial["results"][0]["proposal"]
    item = research.proposal(State(state.root), "demo", pid)
    assert "Version one" in item["text"] and "never execute" not in item["text"]
    assert research.listing(state, "other")["proposals"] == []
    with pytest.raises(ValueError, match="Unknown research proposal"):
        research.proposal(state, "other", pid)
    research.review(state, "demo", pid, "reviewed", 1, "Checked against official release")
    with pytest.raises(ValueError, match="revision changed"):
        research.review(state, "demo", pid, "dismissed", 1, "stale")
    (state.root / "sources" / "demo" / f"{item['sha']}.raw").write_text("tampered")
    with pytest.raises(ValueError, match="snapshot changed"):
        research.proposal(state, "demo", pid)


def test_url_and_byte_boundaries_fail_visibly(source_project):
    state, base, _, _, _ = source_project
    blocked = research.run(state, "demo", [base + "/page"])
    assert blocked["status"] == "failed" and "Private" in blocked["error"]
    oversized = research.run(state, "demo", [base + "/big"], max_bytes=10, allow_private=True)
    assert oversized["status"] == "failed" and "byte budget" in oversized["error"]
    assert oversized["bytes"] == 11
    assert research.listing(state, "demo")["proposals"] == []
    redirected = research.run(state, "demo", [base + "/redirect"], allow_private=True)
    assert redirected["status"] == "succeeded" and redirected["results"][0]["final_url"].endswith("/page")
    invalid = research.run(state, "demo", ["file:///etc/passwd"])
    assert invalid["status"] == "failed"


def test_cancellation_is_a_request_until_worker_acknowledges(source_project):
    state, base, _, started, release = source_project
    with ThreadPoolExecutor() as executor:
        future = executor.submit(research.run, state, "demo", [base + "/slow"], 1000, 10, True, "cancel-test")
        assert started.wait(timeout=3)
        requested = research.cancel(state, "demo", "cancel-test")
        assert requested["cancel_requested"] and requested["status"] == "running"
        release.set()
        result = future.result(timeout=5)
    assert result["status"] == "cancelled"
    assert research.get(State(state.root), "demo", "cancel-test")["status"] == "cancelled"


def test_protocol_failure_has_a_persisted_terminal_outcome(source_project):
    state, base, _, _, _ = source_project
    result = research.run(state, "demo", [base + "/broken"], allow_private=True)
    assert result["status"] == "failed" and result["finished"]
    assert research.get(State(state.root), "demo", result["id"])["status"] == "failed"
    short = research.run(state, "demo", [base + "/short-body"], allow_private=True)
    assert short["status"] == "failed" and "Incomplete source" in short["error"]
    assert short["bytes"] == 5 and not short["results"]


def test_wall_deadline_covers_headers_and_redirect_body_is_not_drained(source_project):
    state, base, _, _, release = source_project
    started = time.monotonic()
    slow = research.run(state, "demo", [base + "/slow-headers"], timeout=1, allow_private=True)
    assert slow["status"] == "timed_out" and time.monotonic() - started < 1.8
    started = time.monotonic()
    redirected = research.run(state, "demo", [base + "/large-redirect"], max_bytes=10, timeout=2, allow_private=True)
    release.set()
    assert redirected["status"] == "succeeded" and redirected["bytes"] == 2
    assert time.monotonic() - started < 1.8


def test_cancellation_interrupts_response_headers(source_project):
    state, base, _, started, _ = source_project
    with ThreadPoolExecutor() as executor:
        future = executor.submit(research.run, state, "demo", [base + "/slow-headers"], 1000, 10, True, "cancel-headers")
        assert started.wait(timeout=3)
        requested_at = time.monotonic()
        research.cancel(state, "demo", "cancel-headers")
        assert future.result(timeout=2)["status"] == "cancelled"
        assert time.monotonic() - requested_at < 1


def test_controller_crash_before_body_retains_uncertain_time_budget(source_project):
    state, base, _, started, _ = source_project
    code = 'from ergora import research; from ergora.state import State; import sys; research.run(State(sys.argv[1]),"demo",[sys.argv[2]],timeout=1,allow_private=True,run_id="header-crash")'
    child = subprocess.Popen([sys.executable, "-c", code, str(state.root), base + "/slow-headers"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert started.wait(timeout=3)
    finally:
        child.kill()
        child.communicate(timeout=3)
    time.sleep(1.1)
    resumed = research.run(State(state.root), "demo", [base + "/slow-headers"], timeout=1, allow_private=True, run_id="header-crash")
    assert resumed["status"] == "timed_out" and resumed["elapsed_seconds"] >= 1


def test_controller_crash_does_not_spend_unconfirmed_transfer_budget_twice(source_project):
    state, base, source, started, release = source_project
    code = 'from ergora import research; from ergora.state import State; import sys; research.run(State(sys.argv[1]),"demo",[sys.argv[2]],max_bytes=100,timeout=10,allow_private=True,run_id="body-crash")'
    child = subprocess.Popen([sys.executable, "-c", code, str(state.root), base + "/slow"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert started.wait(timeout=3)
    finally:
        child.kill()
        child.communicate(timeout=3)
    release.set()
    requests = source["requests"]
    resumed = research.run(State(state.root), "demo", [base + "/slow"], max_bytes=100, timeout=10, allow_private=True, run_id="body-crash")
    assert resumed["status"] == "failed" and resumed["reserved_bytes"] > 0
    assert resumed["bytes"] + resumed["reserved_bytes"] >= 100
    assert source["requests"] == requests and not resumed["results"]


def test_next_observation_repairs_an_incomplete_snapshot(source_project):
    state, base, _, _, _ = source_project
    first = research.run(state, "demo", [base + "/page"], allow_private=True)
    snapshot = state.root / "sources" / "demo" / (first["results"][0]["sha"] + ".raw")
    snapshot.write_bytes(b"part")
    observed = research.run(State(state.root), "demo", [base + "/page"], allow_private=True)
    assert observed["status"] == "succeeded" and not observed["results"][0]["changed"]
    assert "Version one" in research.proposal(state, "demo", first["results"][0]["proposal"])["text"]


def test_controller_crash_at_atomic_snapshot_rename_can_resume(source_project):
    state, base, _, _, _ = source_project
    code = '''import os,sys
from pathlib import Path
from ergora import research
from ergora.state import State
original=Path.replace
def crash_after_rename(path,target):
 result=original(path,target)
 if path.suffix==".part": os._exit(19)
 return result
Path.replace=crash_after_rename
research.run(State(Path(sys.argv[1])),"demo",[sys.argv[2]],allow_private=True,run_id="rename-crash")
'''
    child = subprocess.run([sys.executable, "-c", code, str(state.root), base + "/page"], capture_output=True, text=True, timeout=10)
    assert child.returncode == 19, child.stderr
    assert research.get(state, "demo", "rename-crash")["status"] == "running"
    resumed = research.run(state, "demo", [base + "/page"], allow_private=True, run_id="rename-crash")
    assert resumed["status"] == "succeeded"
    assert "Version one" in research.proposal(state, "demo", resumed["results"][0]["proposal"])["text"]


@pytest.mark.skipif(not os.environ.get("ERGORA_TEMPORAL_TEST_ADDRESS"), reason="requires an explicitly selected isolated Temporal server")
def test_real_temporal_schedule_trigger_and_worker(source_project):
    pytest.importorskip("temporalio")
    from temporalio.client import Client
    from temporalio.worker import Worker
    from ergora import scheduling

    state, base, _, _, _ = source_project
    address = os.environ["ERGORA_TEMPORAL_TEST_ADDRESS"]
    queue = "ergora-test-" + uuid.uuid4().hex
    projects.bind(state, "demo", "scheduler", {"tool": "temporal", "address": address, "namespace": "default", "task_queue": queue}, 1)

    async def check():
        client = await Client.connect(address)
        activities = scheduling.ResearchActivities(state, "demo")
        with ThreadPoolExecutor(max_workers=2) as executor:
            async with Worker(client, task_queue=queue, workflows=[scheduling.SourceObservation],
                              activities=[activities.observe], activity_executor=executor):
                name = "acceptance-" + uuid.uuid4().hex[:12]
                created = await scheduling.create(state, "demo", name, [base + "/page"], 86400, timeout=5, allow_private=True)
                try:
                    with pytest.raises(ValueError, match="unique URLs"):
                        await scheduling.create(state, "demo", "duplicate", [base + "/page", base + "/page"], 86400, allow_private=True)
                    assert created["paused"] is True
                    await scheduling.control(state, "demo", name, "trigger")
                    for _ in range(100):
                        status = await scheduling.control(state, "demo", name, "status")
                        runs = research.listing(state, "demo")["runs"]
                        if runs and runs[0]["status"] == "succeeded" and not status["running_actions"]:
                            break
                        await asyncio.sleep(.1)
                    assert runs[0]["status"] == "succeeded" and status["actions"] >= 1
                    assert not (await scheduling.control(state, "demo", name, "resume"))["paused"]
                    assert (await scheduling.control(state, "demo", name, "pause"))["paused"]
                    for project_id in ("p", "p-a"):
                        projects.create(state, project_id, Path(state.project("demo")["repo"]))
                        projects.bind(state, project_id, "scheduler", state.project("demo")["bindings"]["scheduler"], 1)
                    suffix = uuid.uuid4().hex[:12]
                    first = await scheduling.create(state, "p", "a-b-" + suffix, [base + "/page"], 86400, allow_private=True)
                    second = await scheduling.create(state, "p-a", "b-" + suffix, [base + "/page"], 86400, allow_private=True)
                    assert first["id"] != second["id"]
                    await scheduling.control(state, "p", "a-b-" + suffix, "delete")
                    assert (await scheduling.control(state, "p-a", "b-" + suffix, "status"))["paused"]
                    await scheduling.control(state, "p-a", "b-" + suffix, "delete")
                finally:
                    await scheduling.control(state, "demo", name, "delete")

    asyncio.run(check())
