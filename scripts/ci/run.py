"""Run the installed-product CI selection, retaining progress before termination."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', default='all', help='Configured Linux group index or all')
    parser.add_argument('--output', required=True, type=Path, help='Fresh result directory')
    parser.add_argument('--collect-only', action='store_true', help='Record coverage without running tests')
    options = parser.parse_args()
    directory = options.output.resolve()
    directory.mkdir(parents=True)
    root = Path(__file__).resolve().parents[2]
    reference = root / 'src/ergora/data/reference/platform/upstream/platform'
    suites = ['tests', str(reference / 'tests/test_contracts.py')]
    paths = [str(Path(__file__).resolve().parent)]
    if sys.platform == 'linux':
        paths.append(str(reference))
        suites += [str(reference / 'tests/test_portable.py'),
                   str(reference / 'tests/test_workflow.py') + '::AdapterTests',
                   str(reference / 'tests/test_runtime.py')]
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(paths),
                       PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    command = [sys.executable, '-u', '-m', 'pytest', '-p', 'pytest_phases',
               '-c', str(root / 'pyproject.toml'),
               '--ci-results', str(directory), '-v', '--tb=short', '--durations=20',
               '-o', 'faulthandler_timeout=90', '--junitxml=' + str(directory / 'junit.xml')]
    if options.group != 'all':
        command += ['--ci-group', options.group]
    if options.collect_only:
        command.append('--collect-only')
    command += suites
    request = {'argv': command, 'cwd': str(root), 'group': options.group,
               'scope': 'Installed-product suite; reference imports and CI plugin only on PYTHONPATH'}
    (directory / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    started = time.monotonic()
    tail = ''
    with (directory / 'stdout.txt').open('x', encoding='utf-8', buffering=1) as log:
        with subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding='utf-8') as process:
            for line in process.stdout:
                log.write(line)
                print(line, end='', flush=True)
                tail = (tail + line)[-3500:]
                if line.startswith('FAILED '):
                    detail = line.rstrip()[:3000].replace('%', '%25')
                    print(f'::error title=Failed test::{detail}', flush=True)
            returncode = process.wait()
    result = {'returncode': returncode, 'seconds': time.monotonic() - started}
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    if returncode:
        details = tail.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::error title=Native regression::{details}', flush=True)
    return returncode


if __name__ == '__main__':
    raise SystemExit(main())
