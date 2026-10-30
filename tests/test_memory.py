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
