import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import shutil
import subprocess
import sys
import threading

import pytest

from ergora import memory, projects
from ergora.state import State


@pytest.fixture
def memories(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    for project in ("alpha", "beta"):
        projects.create(state, project, repo)
    return state


def test_memory_scope_corrections_deletion_and_backup_restore(memories, tmp_path):
    state = memories
    source = {"uri": "git:docs/design.md", "revision": "commit-one"}
    first = memory.save(state, "alpha", "Use port 8000", source)
    assert memory.search(State(state.root), "alpha", "8000")["results"][0]["source"] == source
    child = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "memory", "search", "alpha", "8000"],
                           check=True, capture_output=True, text=True)
    assert json.loads(child.stdout)["results"][0]["id"] == first["id"]
    assert memory.search(state, "beta", "8000")["results"] == []
    second = memory.save(state, "alpha", "Use port 9000", {**source, "revision": "commit-two"}, first["id"], 1)
    assert memory.search(state, "alpha", "8000")["results"] == []
    with pytest.raises(ValueError, match="revision changed"):
        memory.save(state, "alpha", "stale edit", source, first["id"], 1)
    memory.restore(state, "alpha", first["id"], 1, 2)
    assert memory.search(state, "alpha", "8000")["results"]
    backup = tmp_path / "backup"
    shutil.copytree(state.root, backup)
    assert memory.search(State(backup), "alpha", "8000")["results"]
    memory.delete(state, "alpha", first["id"], 3)
    assert memory.records(state, "alpha") == []
    assert all(not v["text"] and not v["source"] for v in memory.history(state, "alpha", first["id"]))
    with pytest.raises(ValueError, match="cannot be restored"):
        memory.restore(state, "alpha", first["id"], 1, 4)
    with pytest.raises(ValueError, match="Unknown memory"):
        memory.history(state, "beta", first["id"])


def test_expiry_boundary_corrections_and_restoration_preserve_limits(memories, monkeypatch):
    state = memories
    clock = {"now": "2030-04-01T02:00:00+00:00"}
    monkeypatch.setattr(memory, "now", lambda: clock["now"])
    source = {"uri": "manual:measurement", "revision": "fixed-source"}
    permanent = memory.save(state, "alpha", "permanent observation", source)
    bounded = memory.save(state, "alpha", "bounded observation", source,
                          expires_at="2030-04-01T10:30:00+08:00")
    assert "expires_at" not in permanent
    assert bounded["expires_at"] == "2030-04-01T02:30:00+00:00"
    assert len(memory.search(state, "alpha", "observation")["results"]) == 2
    clock["now"] = bounded["expires_at"]
    assert memory.search(state, "alpha", "observation")["results"] == [permanent]
    catalog = memory.catalog(state, "alpha")
    assert catalog["observed_at"] == clock["now"]
    assert catalog["records"][0] == {"record": bounded, "validity": "expired"}
    assert memory.history(state, "alpha", bounded["id"]) == [bounded]
    corrected = memory.save(state, "alpha", "corrected observation", source, bounded["id"], 1)
    assert corrected["expires_at"] == bounded["expires_at"]
    assert memory.records(state, "alpha") == [permanent]
    with pytest.raises(ValueError, match="timezone"):
        memory.save(state, "alpha", "invalid limit", source, bounded["id"], 2,
                    expires_at="2030-04-01T03:00:00")
    assert len(memory.history(state, "alpha", bounded["id"])) == 2
    unlimited = memory.save(state, "alpha", "explicitly renewed", source, bounded["id"], 2, expires_at=None)
    assert "expires_at" not in unlimited and unlimited in memory.records(state, "alpha")
    restored = memory.restore(state, "alpha", bounded["id"], 1, 3)
    assert restored["expires_at"] == bounded["expires_at"] and restored["text"] == bounded["text"]
    assert memory.records(state, "alpha") == [permanent]
    memory.delete(state, "alpha", bounded["id"], 4)
    assert memory.catalog(state, "alpha")["records"][0]["validity"] == "deleted"
    with pytest.raises(ValueError, match="cannot be restored"):
        memory.restore(state, "alpha", bounded["id"], 1, 5)


def test_reme_revalidates_inflight_results_and_cleans_expired_mirrors(memories, monkeypatch):
    state = memories
    clock = {"now": "2030-04-01T02:00:00+00:00"}
    monkeypatch.setattr(memory, "now", lambda: clock["now"])
    projects.bind(state, "alpha", "memory", {"tool": "reme", "endpoint": "http://reme.invalid"}, 1)
    source = {"uri": "manual:measurement", "revision": "fixed-source"}
    bounded = memory.save(state, "alpha", "expiring observation", source, expires_at="2030-04-01T02:30:00Z")
    deleted = memory.save(state, "alpha", "deleted observation", source)
    corrected = memory.save(state, "alpha", "old observation", source)
    files, calls = {}, []

    def remote(binding, operation, payload):
        calls.append((operation, payload))
        if operation == "write":
            files[payload["path"]] = payload["content"]
        elif operation == "delete":
            files.pop(payload["path"], None)
        else:
            # Local state changes while the remote request is in flight.
            clock["now"] = bounded["expires_at"]
            memory.delete(state, "alpha", deleted["id"], 1)
            memory.save(state, "alpha", "new observation", source, corrected["id"], 1)
            return {"success": True, "metadata": {"results": [
                {"path": path, "text": "untrusted remote text"} for path in [*files, "digest/ergora/beta/foreign.md"]]}}
        return {"success": True, "metadata": {}}

    monkeypatch.setattr(memory, "_job", remote)
    result = memory.search(state, "alpha", "observation")
    assert result["observed_at"] == clock["now"] and result["results"] == []
    assert len(files) == 3
    assert memory.sync(state, "alpha")["changes_acknowledged"] == 3
    assert files == {f"digest/ergora/alpha/{corrected['id']}.md": "new observation"}
    assert len([operation for operation, _ in calls if operation == "delete"]) == 2
    assert memory.sync(state, "alpha")["changes_acknowledged"] == 0


def test_reme_protocol_sync_filters_scope_and_propagates_deletion(memories, monkeypatch):
    calls, files = [], {}
    fail = {"search": False}
    auth = {"expected": "Bearer old-fixture-token"}
    monkeypatch.setenv("OLD_REME_FIXTURE", "old-fixture-token")
    monkeypatch.setenv("NEW_REME_FIXTURE", "new-fixture-token")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, body))
            result = {"success": True, "answer": "", "metadata": {}}
            if self.headers.get("Authorization") != auth["expected"]:
                result["success"] = False
            elif self.path == "/write":
                files[body["path"]] = body["content"]
            elif self.path == "/delete":
                files.pop(body["path"], None)
            elif self.path == "/search":
                result["success"] = not fail["search"]
                paths = ["digest/ergora/beta/foreign.md", *files]
                allowed = body["search_filter"]["paths"]
                result["metadata"]["results"] = [{"path": p, "text": "untrusted remote text"}
                                                    for p in paths if p in allowed][:body["limit"]]
                result["metadata"]["results"].append({"path": "digest/ergora/beta/foreign.md", "text": "foreign"})
            data = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = memories
        endpoint = f"http://127.0.0.1:{server.server_port}"
        projects.bind(state, "alpha", "memory", {"tool": "reme", "endpoint": endpoint, "token_env": "OLD_REME_FIXTURE"}, 1)
        doc = memory.save(state, "alpha", "canonical source", {"uri": "manual:note", "revision": "r1"})
        result = memory.search(state, "alpha", "source", limit=1)
        assert result["backend"] == "reme" and result["results"] == [doc]
        assert calls[0][0] == "/write"
        files.clear()
        assert memory.sync(state, "alpha")["changes_acknowledged"] == 0
        assert memory.sync(state, "alpha", rebuild=True)["changes_acknowledged"] == 1
        assert memory.search(state, "alpha", "source", limit=1)["results"] == [doc]
        fail["search"] = True
        with pytest.raises(ValueError, match="ReMe search failed"):
            memory.search(state, "alpha", "source")
        fail["search"] = False
        projects.bind(state, "alpha", "memory", {"tool": "reme", "endpoint": endpoint, "token_env": "NEW_REME_FIXTURE"}, 2)
        memory.sync(state, "alpha")
        auth["expected"] = "Bearer new-fixture-token"
        monkeypatch.delenv("OLD_REME_FIXTURE")
        projects.bind(state, "alpha", "memory", {"tool": "sqlite"}, 3)
        memory.delete(state, "alpha", doc["id"], 1)
        assert memory.search(state, "alpha", "source")["results"] == []
        memory.sync(state, "alpha")
        assert files == {} and any(path == "/delete" for path, _ in calls)
        assert memory.sync(state, "alpha")["changes_acknowledged"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
