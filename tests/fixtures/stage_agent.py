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
if '"stage": "work:' in prompt:
    Path("src/new.py").write_text("VALUE = 42\n")
result = {"summary": mode, "artifacts": {name: mode + ": " + name for name in schema["properties"]["artifacts"]["required"]}}
if "decision" in schema["required"]:
    result["decision"] = "approve"
    # Same-group background work must stop before the formal read-only check.
    subprocess.Popen([sys.executable, "-c", "import time;from pathlib import Path;time.sleep(1);Path('src/late-review.py').write_text('LATE = True\\n')"],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if "--output-last-message" in sys.argv:
    Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text(json.dumps(result))
    print(json.dumps({"type": "fixture.process.finished"}))
else:
    print(json.dumps(result))
