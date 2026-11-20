"""Run the installed-product CI selection, retaining progress before termination."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time


class _PythonDiagnostics:
    """Keep bounded original report starts and separately observed current threads."""

    header = re.compile(r'(?:(?!(?:Fatal Python error: |Windows fatal exception: |Timeout \())'
                        r'[^\r\n]*?::[^\s\[]+(?:\[[^\r\n]*\])? )?'
                        r'(?P<report>Fatal Python error: [^\r\n]+|Windows fatal exception: [^\r\n]+'
                        r'|Timeout \(\d+:\d{2}:\d{2}(?:\.\d+)?\)!)\r?\n?$')
    thread = re.compile(r'(?:Current thread|Thread) 0x[0-9a-fA-F]+ '
                        r'\(most recent call first\):\s*$')

    def __init__(self):
        self.excerpts = {}
        self.active = None
        self.current_thread = False

    def observe(self, line):
        # A header ends the physical line; node-ID suffixes and quoted frames do not.
        match = None if line.startswith('  File "') else self.header.fullmatch(line)
        if match:
            kind = 'timeout' if match['report'].startswith('Timeout (') else 'fatal'
            self.current_thread = False
            if kind in self.excerpts and self.excerpts[kind]['thread_observed']:
                self.active = None
                return
            self.active = self.excerpts[kind] = {
                'start': '', 'current_thread': '', 'thread_observed': False}
            # Pytest's pending verbose row may precede the report on this same line.
            line = line[match.start('report'):]
        if self.active is None:
            return
        thread = self.thread.fullmatch(line)
        if thread:
            self.active['thread_observed'] = True
        elif (not match and not self.active['thread_observed'] and line.strip()
              and not line.startswith('Python runtime state:')):
            # Quoted headers in test IDs or ordinary output are not tracebacks.
            self.active = None
            return
        self.active['start'] = (self.active['start'] + line)[:2000]
        if line.startswith('Current thread 0x') and not self.active['current_thread']:
            self.current_thread = True
        elif line.startswith('Thread 0x') or not line.strip():
            self.current_thread = False
        if self.current_thread:
            self.active['current_thread'] = (self.active['current_thread'] + line)[:2000]

    def report(self, output):
        def escaped(text):
            return text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')

        for excerpt in self.excerpts.values():
            if not excerpt['thread_observed']:
                continue
            detail = escaped(excerpt['start'])[:2000]
            current = excerpt['current_thread']
            if current and current not in excerpt['start']:
                detail += '%0A[Observed current-thread excerpt]%0A' + escaped(current)[:1400]
            output(f'::error title=Python diagnostic excerpt::{detail}', annotation=True)


def _last_phase(path):
    try:
        with path.open('rb') as stream:
            size = stream.seek(0, os.SEEK_END)
            start = max(0, size - 65536)
            stream.seek(start)
            tail = stream.read(65536)
    except OSError:
        return None
    if start:
        tail = tail.partition(b'\n')[2]
    for line in reversed(tail.split(b'\n')[:-1]):
        try:
            row = json.loads(line)
        except (ValueError, UnicodeError, RecursionError):
            continue
        if isinstance(row, dict) and isinstance(row.get('event'), str):
            return {key: row[key] for key in
                    ('event', 'when', 'outcome', 'elapsed', 'seconds', 'exitstatus', 'nodeid')
                    if key in row}
    return None


def _stdout_writer():
    stream = sys.stdout
    lock = threading.Lock()
    line_start = True

    def emit(text, *, annotation=False):
        nonlocal line_start
        with lock:
            if annotation:
                text = ('' if line_start else '\n') + text + '\n'
            stream.write(text)
            stream.flush()
            if text:
                line_start = text.endswith('\n')

    return emit


def _phase_notice(process, path, started, final, output):
    row = _last_phase(path)
    detail = json.dumps({
        'observation': 'final' if final else 'periodic',
        'parent_elapsed_seconds': time.monotonic() - started,
        'owned_child_returncode': process.poll(),
        'last_observed_complete_row': row,
    }, ensure_ascii=True)
    detail = detail.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')[:3000]
    output(f'::notice title=CI phase observation::{detail}', annotation=True)


def _monitor_phases(process, path, started, stop, output, *,
                    offsets=(300, 600, 900, 1200, 1500, 1800, 2100, 2280), poll_interval=1):
    notices = 0
    while not stop.wait(poll_interval):
        if process.poll() is not None:
            break
        if notices < len(offsets) and time.monotonic() - started >= offsets[notices]:
            _phase_notice(process, path, started, final=False, output=output)
            notices += 1
    _phase_notice(process, path, started, final=True, output=output)


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
    diagnostics = _PythonDiagnostics()
    output = _stdout_writer()
    with (directory / 'stdout.txt').open('x', encoding='utf-8', buffering=1) as log:
        with subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding='utf-8') as process:
            stop = threading.Event()
            monitor = threading.Thread(target=_monitor_phases,
                                       args=(process, directory / 'phases.jsonl', started, stop, output),
                                       name='ergora-ci-phase-monitor')
            monitor.start()
            try:
                for line in process.stdout:
                    log.write(line)
                    output(line)
                    tail = (tail + line)[-3500:]
                    diagnostics.observe(line)
                    if line.startswith('FAILED '):
                        detail = line.rstrip()[:3000].replace('%', '%25')
                        output(f'::error title=Failed test::{detail}', annotation=True)
                returncode = process.wait()
            finally:
                stop.set()
                monitor.join()
    result = {'returncode': returncode, 'seconds': time.monotonic() - started}
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    if returncode:
        diagnostics.report(output)
        details = tail.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        output(f'::error title=Native regression::{details}', annotation=True)
    return returncode


if __name__ == '__main__':
    raise SystemExit(main())
