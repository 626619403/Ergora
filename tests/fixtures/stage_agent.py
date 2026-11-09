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
if '--model' in sys.argv and sys.argv[sys.argv.index('--model') + 1] in ('fixture-timeout', 'fixture-cancel'):
    Path('review-ready').touch()
    child = "import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(2);Path('late-review').touch()"
    subprocess.Popen([sys.executable, '-c', child], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(40)
    raise SystemExit(2)
if '"stage": "work:' in prompt:
    Path("src/new.py").write_text("VALUE = 42\n")
    if 'fixture-delete-base-only' in prompt:
        Path('src/removed.txt').unlink()
result = {"summary": mode, "artifacts": {name: mode + ": " + name for name in schema["properties"]["artifacts"]["required"]}}
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
