"""Deterministic process fixture, not a model or a performance result."""

import json
import subprocess
import time
from pathlib import Path
import sys


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
if '"kind": "formal-preparation-materials"' in prompt or ('decision' not in schema['required'] and '"kind": "formal-work-materials"' in prompt):
    import asyncio
    from ergora import task_mcp

    settings = {sys.argv[index + 1].split('=', 1)[0]: json.loads(sys.argv[index + 1].split('=', 1)[1])
                for index, value in enumerate(sys.argv) if value == '-c'}
    server = {key.removeprefix('mcp_servers.ergora_task.'): value for key, value in settings.items()
              if key.startswith('mcp_servers.ergora_task.')}
    server = {key: value for key, value in server.items() if key in ('command', 'args', 'env')}
    if '"kind": "formal-preparation-materials"' in prompt and 'fixture-unread-inventory' not in sys.argv:
        import runpy

        read_all = runpy.run_path(str(Path(__file__).with_name('full_stage_resources.py')))['read_all']
        asyncio.run(read_all(server))
    else:
        asyncio.run(task_mcp.probe(server, Path(sys.argv[sys.argv.index('--output-last-message') + 1]).with_name('fixture-mcp.stderr')))
    payload = json.loads(prompt.splitlines()[-1])
    if payload['kind'] == 'formal-work-materials':
        unit = payload['context']['unit']
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
if "decision" in schema["required"]:
    result["decision"] = "request-changes" if "fixture-reject" in sys.argv else "approve"
    # Same-group background work must stop before the formal read-only check.
    subprocess.Popen([sys.executable, "-c", "import time;from pathlib import Path;time.sleep(1);Path('src/late-review.py').write_text('LATE = True\\n')"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if "--output-last-message" in sys.argv:
    Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text(json.dumps(result))
    print(json.dumps({"type": "fixture.process.finished"}))
else:
    print(json.dumps(result))
