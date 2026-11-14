import json
from pathlib import Path
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


@pytest.fixture
def memory_retrospective(memories, tmp_path):
    from ergora import handoff, workflow_definitions as workflows
    from test_handoff import evidence, text_evidence

    index, blobs = text_evidence(evidence.__wrapped__(), ['A failed source observation; cost was not recorded.\r\n'])
    index['project'] = 'alpha'
    packet = tmp_path / 'source.zip'
    collected = handoff.create(index, lambda artifact: blobs[artifact['sha256']], packet)
    installed = workflows.install_preset(memories, 'memory-retrospective')
    root = workflows.get(memories, installed['root']['id'], installed['root']['version'])['definition']
    manifest = workflows.prepare_manifest(memories.root, root['id'], root['version'],
        {'schema_version': 1, 'permissions': root['permissions'], 'limits': root['limits']}, tmp_path / 'manifest')
    record = memory.save(memories, 'alpha', '保留原始限定和完整项目知识。\r\n' * 500,
                         {'uri': 'manual:project', 'revision': 'r1'}, expires_at='2099-01-01T00:00:00Z')
    return memories, packet, record, {
        'packet_sha256': collected['sha256'], 'memory_id': record['id'], 'revision': record['revision'],
        'objective': 'Preserve original uncertainty in useful future project knowledge.',
        'manifest': Path(manifest['path']), 'instance': 'root/propose', 'destination': tmp_path / 'input',
        'max_prompt_bytes': 300000}


def memory_proposal(input_path, result_path, text):
    task = json.loads((input_path / 'task.txt').read_bytes())
    artifact = task['evidence']['artifacts'][0]
    proposal = {'schema_version': 1, 'evidence_sha256': task['evidence']['sha256'],
        'baseline_digest': task['baseline']['digest'],
        'observations': [{'claim': 'The source records one failed observation.', 'uncertainty': 'General applicability is unmeasured.',
            'citations': [{'job_id': artifact['job_id'], 'name': artifact['artifact']['name'], 'sha256': artifact['artifact']['sha256']}]}],
        'negative_results': ['Original failure retained.'], 'cost_and_uncertainty': 'Original cost unknown; no measured gain.',
        'candidate': None if text is None else {'text': text, 'hypothesis': 'Qualified knowledge may generalize better.',
            'applicability': 'This project and the stated source limitations.', 'evaluation_plan': 'Check a distinct holdout observation.'}}
    result_path.write_bytes(json.dumps({'summary': 'Source-bound proposal.', 'artifacts': {'response': json.dumps(proposal)}}).encode())
    return proposal


@pytest.mark.parametrize('creating', [False, True])
def test_memory_retrospective_exports_full_offline_text_for_original_save_and_restore(memory_retrospective, tmp_path, capsys, creating):
    import hashlib
    from ergora import cli, retrospectives, workflow_definitions as workflows

    state, packet, record, options = memory_retrospective
    if creating:
        options.update(memory_id=None, revision=0)
    before = memory.catalog(state, 'alpha')
    prepared = retrospectives.prepare_memory(state, 'alpha', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    frozen = workflows.inspect_input(options['destination'], material=True)
    task = json.loads((options['destination'] / 'task.txt').read_bytes())
    assert task['baseline']['record'] == (None if creating else record)
    assert task['evidence']['artifacts'][0]['text'].endswith('\r\n')
    for leaf in (item for item in frozen['composition']['instances'] if item['kind'] == 'agent'):
        assert all(resource['text'] in leaf['prompt'] for resource in leaf['resources'])
        assert not leaf['permissions']['write'] and not leaf['permissions']['shell'] and not leaf['permissions']['network']
    text = '\ufeff' + record['text'] + '这只是原观察；适用性和成本仍待验证。\r\n'
    result = tmp_path / 'result.json'
    memory_proposal(options['destination'], result, text)
    sha = hashlib.sha256(result.read_bytes()).hexdigest()
    packet.unlink()
    shutil.rmtree(options['manifest'])
    readback = retrospectives.inspect_input(options['destination'], project_id='alpha')
    assert readback['digest'] == prepared['digest'] and readback['retrospective_request'] == task
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'check-memory', str(options['destination']), str(result),
                     '--result-sha256', sha]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked['input_digest'] == prepared['digest'] and not unused.exists()
    assert retrospectives.check_memory(options['destination'], result, project_id='alpha', input_digest=prepared['digest']) == checked
    assert checked['save']['source'] == {'uri': 'ergora-handoff:sha256:' + options['packet_sha256'],
                                       'revision': task['evidence']['sha256']}
    target = tmp_path / 'candidate'
    receipt = retrospectives.export_memory(options['destination'], result, target, result_sha256=sha,
                                           candidate_digest=checked['candidate_digest'], project_id='alpha', input_digest=prepared['digest'])
    assert (target / 'memory.txt').read_bytes() == text.encode('utf-8')
    assert json.loads((target / 'receipt.json').read_bytes()) == receipt
    assert memory.catalog(state, 'alpha')['records'] == before['records']
    save_args = ['--home', str(state.root), 'memory', 'save', 'alpha', '--text', str(target / 'memory.txt'),
                 '--source', checked['save']['source']['uri'], '--source-revision', checked['save']['source']['revision']]
    if not creating:
        save_args.extend(['--id', record['id'], '--revision', str(record['revision'])])
    assert cli.main(save_args) == 0
    saved = json.loads(capsys.readouterr().out)
    assert saved['text'] == text and saved['source'] == checked['save']['source']
    if creating:
        assert saved['revision'] == 1 and 'expires_at' not in saved and saved['id'] != record['id']
    else:
        assert saved['expires_at'] == record['expires_at']
        with pytest.raises(ValueError, match='revision changed'):
            memory.save(state, 'alpha', **checked['save'])
        restored = memory.restore(state, 'alpha', record['id'], record['revision'], saved['revision'])
        assert restored['text'] == record['text'] and restored['expires_at'] == record['expires_at']
    assert retrospectives.check_memory(options['destination'], result) == checked


@pytest.mark.parametrize('change', ['revision', 'deleted', 'expired'])
def test_memory_retrospective_observes_current_validity_after_source_io(memory_retrospective, monkeypatch, change):
    from ergora import handoff, retrospectives

    state, packet, record, options = memory_retrospective
    original = handoff.evidence

    def reading(*args, **kwargs):
        selected = original(*args, **kwargs)
        if change == 'revision':
            memory.save(state, 'alpha', 'A newer observation.', record['source'], record['id'], record['revision'])
        elif change == 'deleted':
            memory.delete(state, 'alpha', record['id'], record['revision'])
        else:
            monkeypatch.setattr(memory, 'now', lambda: record['expires_at'])
        return selected

    monkeypatch.setattr(handoff, 'evidence', reading)
    with pytest.raises(ValueError, match='changed, expired or was deleted'):
        retrospectives.prepare_memory(state, 'alpha', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    assert not options['destination'].exists()


@pytest.mark.parametrize('change,reason', [
    ('baseline', 'frozen source or baseline'), ('citation', 'citation is absent'),
    ('expiry', 'Retrospective proposal at /candidate'), ('source', 'Retrospective proposal at /candidate'),
    ('oversize', 'Retrospective proposal at /candidate'),
])
def test_memory_retrospective_rejects_misbound_or_authority_changing_results(memory_retrospective, tmp_path, capsys, change, reason):
    from ergora import cli, retrospectives

    state, packet, record, options = memory_retrospective
    retrospectives.prepare_memory(state, 'alpha', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    proposal = memory_proposal(options['destination'], result, 'A qualified proposed observation.')
    if change == 'baseline':
        proposal['baseline_digest'] = '0' * 64
    elif change == 'citation':
        proposal['observations'][0]['citations'][0]['sha256'] = '0' * 64
    elif change == 'expiry':
        proposal['candidate']['expires_at'] = None
    elif change == 'source':
        proposal['candidate']['source'] = record['source']
    else:
        proposal['candidate']['text'] = 'a' * 100001
    outer = json.loads(result.read_bytes())
    outer['artifacts']['response'] = json.dumps(proposal)
    result.write_bytes(json.dumps(outer).encode())
    unused = tmp_path / 'unused-state'
    assert cli.main(['--home', str(unused), 'retrospective', 'check-memory', str(options['destination']), str(result)]) == 2
    captured = capsys.readouterr()
    assert not captured.out and reason in captured.err and not unused.exists()
    assert memory.history(state, 'alpha', record['id']) == [record]


def test_memory_retrospective_null_and_explicit_export_selection_cannot_overwrite_input_or_target(memory_retrospective, tmp_path):
    import hashlib
    from ergora import retrospectives, workflow_definitions as workflows

    state, packet, record, options = memory_retrospective
    prepared = retrospectives.prepare_memory(state, 'alpha', packet, [{'job_id': 'job-1', 'name': 'record'}], **options)
    result = tmp_path / 'result.json'
    target = tmp_path / 'candidate'
    memory_proposal(options['destination'], result, None)
    sha = hashlib.sha256(result.read_bytes()).hexdigest()
    assert retrospectives.check_memory(options['destination'], result)['candidate_digest'] is None
    with pytest.raises(ValueError, match='no memory candidate'):
        retrospectives.export_memory(options['destination'], result, target, result_sha256=sha, candidate_digest='0' * 64)
    memory_proposal(options['destination'], result, 'The source supports only a qualified observation.')
    sha = hashlib.sha256(result.read_bytes()).hexdigest()
    checked = retrospectives.check_memory(options['destination'], result)
    for result_sha, digest, destination, reason in [
        ('0' * 64, checked['candidate_digest'], target, 'original bytes'),
        (sha, '0' * 64, target, 'explicitly selected'),
        (sha, checked['candidate_digest'], options['destination'] / 'candidate', 'frozen input'),
    ]:
        with pytest.raises(ValueError, match=reason):
            retrospectives.export_memory(options['destination'], result, destination,
                                         result_sha256=result_sha, candidate_digest=digest)
    target.mkdir()
    (target / 'preserve.txt').write_bytes(b'keep original\r\n')
    with pytest.raises(ValueError, match='new retrospective export'):
        retrospectives.export_memory(options['destination'], result, target,
                                     result_sha256=sha, candidate_digest=checked['candidate_digest'])
    assert {p.name: p.read_bytes() for p in target.iterdir()} == {'preserve.txt': b'keep original\r\n'}
    assert workflows.inspect_input(options['destination'])['digest'] == prepared['digest']
    assert memory.history(state, 'alpha', record['id']) == [record]
    assert not list(tmp_path.glob('.retrospective-memory-*'))
