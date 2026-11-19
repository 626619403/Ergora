"""Deterministic process fixture, not a model or a performance result."""

import json
import math
import os
import subprocess
import time
from pathlib import Path
import sys


def _preparation_rendezvous(payload, raw_prompt, schema):
    """Hold only declared independent fixture peers inside their original monitor window."""
    protocol = Path(sys.argv[sys.argv.index('--output-schema') + 1]).resolve().parent
    result = Path(sys.argv[sys.argv.index('--output-last-message') + 1]).resolve()
    assert result.parent == protocol and protocol.parent.name == 'runs'
    control = protocol.parent.parent
    metadata = control / 'fixture-preparation-rendezvous.json'
    if not metadata.exists():
        return
    configured = json.loads(metadata.read_bytes())
    assert configured['kind'] == 'fixture-preparation-rendezvous' and configured['control_home'] == str(control)
    context = payload['context']
    stage, separator, member = context['stage'].partition(':')
    group = configured['groups'].get(stage)
    if not separator or group is None or member not in group['members']:
        return
    peers = group['members']
    assert len(peers) == len(set(peers)) == 2
    runtime = Path(configured['runtime'])
    folder = control / 'fixture-preparation-rendezvous' / stage
    folder.mkdir(parents=True, exist_ok=True)

    def original(peer, job_id):
        job = runtime / 'workspaces' / context['task_id'] / 'jobs' / job_id
        request_path = job / 'selected-agent/request.json'
        request = json.loads(request_path.read_bytes())
        formal = json.loads((job / 'selected-agent/formal-call.json').read_bytes())
        materials = json.loads((job / 'selected-agent/materials.json').read_bytes())
        assert formal['member'] == peer and materials['context']['stage'] == stage + ':' + peer
        assert materials['context']['job_id'] == job_id and materials['context']['task_id'] == context['task_id']
        assert request['composition']['home'] == str(control)
        assert request['cwd'] == str(job / 'checkout') and request['output'] == str(job / 'output/selected-agent')
        process = runtime / 'processes' / ('af-' + job_id + '-selected')
        declared = json.loads((process / 'request.json').read_bytes())
        started = json.loads((process / 'started.json').read_bytes())
        assert declared['name'] == started['name'] == 'af-' + job_id + '-selected'
        assert declared['protocol'] == str(job / 'selected-agent')
        assert declared['command'] == started['command'] and declared['command'][-1] == str(request_path)
        assert declared['timeout'] == request['timeout']
        deadline = started['time'] + request['timeout']
        assert math.isfinite(deadline) and request['timeout'] > 0
        if peer == member:
            assert materials == payload and request['schema'] == schema
            assert (protocol / 'prompt.txt').read_text() == raw_prompt
        return deadline

    def check_deadline(deadline):
        if time.time() >= deadline:
            raise TimeoutError('[fixture-preparation-rendezvous] original native deadline expired')

    def publish(path, value, expires):
        temporary = path.with_name('.' + path.name + '.' + str(os.getpid()))
        try:
            with temporary.open('xb') as stream:
                stream.write((json.dumps(value, sort_keys=True) + '\n').encode())
                stream.flush()
                os.fsync(stream.fileno())
            check_deadline(expires)
            try:
                os.link(temporary, path)
                return True
            except FileExistsError:
                return False
        finally:
            temporary.unlink(missing_ok=True)

    deadline = original(member, context['job_id'])
    check_deadline(deadline)
    ready = {'stage': stage, 'member': member, 'job_id': context['job_id'],
             'deadline_at': deadline, 'ready_at_ns': time.time_ns()}
    assert publish(folder / (member.rsplit('/', 1)[-1] + '.ready.json'), ready, deadline), 'Duplicate fixture peer readiness'
    release_path = folder / 'release.json'
    while True:
        check_deadline(deadline)
        ready_records = {}
        for peer in peers:
            path = folder / (peer.rsplit('/', 1)[-1] + '.ready.json')
            if not path.exists():
                break
            record = json.loads(path.read_bytes())
            assert record['stage'] == stage and record['member'] == peer
            peer_deadline = original(peer, record['job_id'])
            assert record['deadline_at'] == peer_deadline and record['ready_at_ns'] < peer_deadline * 1e9
            check_deadline(peer_deadline)
            ready_records[peer] = record
        if len(ready_records) == len(peers):
            check_deadline(deadline)
            release = {'stage': stage, 'members': peers, 'ready': ready_records, 'released_at_ns': time.time_ns()}
            assert release['released_at_ns'] < min(row['deadline_at'] for row in ready_records.values()) * 1e9
            publish(release_path, release, min(row['deadline_at'] for row in ready_records.values()))
            if release_path.exists():
                release = json.loads(release_path.read_bytes())
                assert release['stage'] == stage and release['members'] == peers and release['ready'] == ready_records
                assert release['released_at_ns'] < min(row['deadline_at'] for row in ready_records.values()) * 1e9
                for peer, record in ready_records.items():
                    check_deadline(original(peer, record['job_id']))
                check_deadline(original(member, context['job_id']))
                return
        time.sleep(min(.01, max(0, deadline - time.time())))


model_started_ns = time.time_ns()
raw = sys.stdin.read()
if "--wait-for-cancellation" in sys.argv:
    ready, late = sys.argv[-2:]
    child = "import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path(" + repr(ready) + ").touch();time.sleep(2);Path(" + repr(late) + ").touch()"
    subprocess.Popen([sys.executable, "-c", child], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(30)
    raise SystemExit(2)
if "--output-schema" in sys.argv:
    schema = json.loads(Path(sys.argv[sys.argv.index("--output-schema") + 1]).read_text())
    prompt = raw
    mode = "native-cli-fixture"
else:
    envelope = json.loads(raw)
    schema = envelope["result_schema"]
    prompt = envelope["prompt"]
    mode = "command-fixture"
if 'fixture-mutate' in sys.argv:
    (Path(sys.argv[sys.argv.index('--fixture-checkout') + 1]) / 'src/base.py').write_text('MUTATED = True\n')
if '--model' in sys.argv and sys.argv[sys.argv.index('--model') + 1] in ('fixture-timeout', 'fixture-cancel'):
    Path('review-ready').touch()
    child = "import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(2);Path('late-review').touch()"
    subprocess.Popen([sys.executable, '-c', child], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(40)
    raise SystemExit(2)
review_mcp = ('"kind": "formal-review-materials"' in prompt
              and any(value.startswith('mcp_servers.ergora_task.') for value in sys.argv))
if ('"selected_context": {' in prompt or '"kind": "formal-preparation-materials"' in prompt or review_mcp
        or ('decision' not in schema['required'] and '"kind": "formal-work-materials"' in prompt)):
    import asyncio
    import ergora.agents.mcp as task_mcp

    settings = {sys.argv[index + 1].split('=', 1)[0]: json.loads(sys.argv[index + 1].split('=', 1)[1])
                for index, value in enumerate(sys.argv) if value == '-c'}
    server = {key.removeprefix('mcp_servers.ergora_task.'): value for key, value in settings.items()
              if key.startswith('mcp_servers.ergora_task.')}
    server = {key: value for key, value in server.items() if key in ('command', 'args', 'env')}
    if review_mcp or '"selected_context": {' in prompt or ('"kind": "formal-preparation-materials"' in prompt and 'fixture-unread-inventory' not in sys.argv):
        import runpy

        read_all = runpy.run_path(str(Path(__file__).with_name('full_stage_resources.py')))['read_all']
        asyncio.run(read_all(server))
    else:
        asyncio.run(task_mcp.probe(server, Path(sys.argv[sys.argv.index('--output-last-message') + 1]).with_name('fixture-mcp.stderr')))
    payload = json.loads(prompt.splitlines()[-1])
    if payload['kind'] == 'formal-preparation-materials':
        _preparation_rendezvous(payload, raw, schema)
    if payload['kind'] == 'formal-work-materials':
        unit = payload['context']['unit']
        if 'fixture-shared-contract' in unit['instructions']:
            if unit['id'] in ('server', 'client', 'integration-tests'):
                assert Path('src/contract.py').read_text() == 'VALUE = 42\n'
            if unit['id'] == 'integration-tests':
                assert all(Path('src/' + name + '.py').read_text() == 'VALUE = 42\n' for name in ('server', 'client'))
            if unit['id'] in ('server', 'client'):
                time.sleep(.3)
        target = Path(unit['paths'][0]); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('VALUE = 42\n')
        if 'fixture-work-scope' in unit['instructions']:
            Path('src/outside.py').write_text('OUTSIDE = True\n')
        if 'fixture-work-commit' in unit['instructions']:
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Unauthorized agent commit'], check=True, capture_output=True)
elif 'decision' not in schema['required'] and '"stage": "work:' in prompt:
    Path("src/new.py").write_text("VALUE = 42\n")
    if 'fixture-delete-base-only' in prompt:
        Path('src/removed.txt').unlink()
result = {"summary": mode, "artifacts": {name: mode + ": " + name for name in schema["properties"]["artifacts"]["required"]}}
if any(model in sys.argv for model in ('fixture-complete-inventory', 'fixture-capacity-inventory')):
    name = next(iter(result['artifacts']))
    result['artifacts'][name] = ('I' * (1100000 if 'fixture-capacity-inventory' in sys.argv else 75000)
                                + '\nComplete inventory tail beyond the legacy truncation.\n')
if 'fixture-complete-plan' in sys.argv:
    name = next(iter(result['artifacts']))
    result['artifacts'][name] = 'K' * 75000 + '\nComplete planner original tail: kernel 原文，未截断。\r\n'
if any(kind in prompt for kind in ('"kind": "formal-preparation-materials"', '"kind": "formal-work-materials"')):
    result['summary'] = json.dumps({'fixture': mode, 'model_started_ns': model_started_ns,
                                   'model_finished_ns': time.time_ns()})
if "decision" in schema["required"]:
    result["decision"] = "request-changes" if "fixture-reject" in sys.argv else "approve"
    if '--fixture-auth-only' not in sys.argv:
        # Same-group background work must stop before the formal read-only check.
        subprocess.Popen([sys.executable, "-c", "import time;from pathlib import Path;time.sleep(1);Path('src/late-review.py').write_text('LATE = True\\n')"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if "--output-last-message" in sys.argv:
    Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text(json.dumps(result))
    print(json.dumps({"type": "fixture.process.finished"}))
else:
    print(json.dumps(result))
