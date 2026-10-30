from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .core import STATE, write


def isolation_report() -> dict:
    tests = {}
    with tempfile.TemporaryDirectory(prefix='agentflow-sandbox-check-') as directory:
        root = Path(directory)
        workspace, outside, config = [root / x for x in ('workspace', 'outside', 'codex')]
        for path in (workspace, outside, config): path.mkdir()
        (outside / 'marker').write_text('sandbox probe')
        (config / 'config.toml').write_text('default_permissions="probe"\n[permissions.probe.filesystem]\n"/"="read"\n":workspace_roots"="write"\n'
            + json.dumps(str(outside)) + '="deny"\n[permissions.probe.network]\nenabled=false\n')
        code = ('from pathlib import Path\nimport json\nr={}\n'
                f'outside=Path({str(outside)!r})\n'
                'for k,p in [("inside",Path("marker")),("outside",outside/"new")]:\n'
                ' try:p.write_text("probe");r[k]="allowed"\n except OSError:r[k]="denied"\n'
                'try:(outside/"marker").read_text();r["read_outside"]="allowed"\nexcept OSError:r["read_outside"]="denied"\n'
                'print(json.dumps(r))\n')
        cases = {'system-bwrap': ['bwrap', '--ro-bind', '/', '/', '--', '/bin/true'],
                 'codex-bwrap': ['codex', 'sandbox', '-P', 'probe', '-C', str(workspace), '--', '/usr/bin/python3', '-c', code],
                 'codex-legacy-landlock': ['codex', 'sandbox', '--enable', 'use_legacy_landlock', '-P', 'probe',
                                         '-C', str(workspace), '--', '/usr/bin/python3', '-c', code],
                 'podman': ['podman', 'info', '--format', 'json']}
        for name, command in cases.items():
            if not shutil.which(command[0]):
                tests[name] = {'status': 'not-installed'}
                continue
            result = subprocess.run(command, env={**os.environ, 'CODEX_HOME': str(config)},
                                    capture_output=True, text=True, timeout=20)
            passed = result.returncode == 0
            if name.startswith('codex-') and passed:
                passed = json.loads(result.stdout.strip().splitlines()[-1]) == {
                    'inside': 'allowed', 'outside': 'denied', 'read_outside': 'denied'}
            tests[name] = {'status': 'passed' if passed else 'unavailable', 'returncode': result.returncode,
                           'stderr': result.stderr[-2500:]}
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(444, 0, 0, 1)
    result = {'tests': tests, 'landlock_kernel_abi': abi,
              'selected_backend': 'current-container', 'inner_mount_isolation_required': False}
    write(STATE / 'isolation-report.json', result, replace=True)
    return result
