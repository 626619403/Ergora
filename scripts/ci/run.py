"""Run the installed-product CI selection, retaining progress before termination."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time


_FILETIME_EPOCH = 116444736000000000
_EVENT_FIELDS = ('ProcessId', 'ProcessCreationTime', 'AppPath', 'AppName', 'AppVersion',
                 'ModuleName', 'ModuleVersion', 'ExceptionCode', 'FaultingOffset')
_EVENT_QUERY = r'''
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    $from = [DateTime]::FromFileTimeUtc(__START__).ToString('o')
    $to = [DateTime]::FromFileTimeUtc(__END__).ToString('o')
    $xpath = "*[System[Provider[@Name='Application Error'] and EventID=1000 and TimeCreated[@SystemTime >= '$from' and @SystemTime <= '$to']] and EventData[__PID_FILTER__]]"
    $records = @()
    foreach ($event in @(Microsoft.PowerShell.Diagnostics\Get-WinEvent -LogName Application -FilterXPath $xpath -MaxEvents 5 -ErrorAction Stop)) {
        $xml = [xml]$event.ToXml()
        $row = [ordered]@{provider=$xml.GetElementsByTagName('Provider')[0].GetAttribute('Name'); event_id=[int]$xml.GetElementsByTagName('EventID')[0].InnerText; event_time=$xml.GetElementsByTagName('TimeCreated')[0].GetAttribute('SystemTime')}
        foreach ($name in @('ProcessId','ProcessCreationTime','AppPath','AppName','AppVersion','ModuleName','ModuleVersion','ExceptionCode','FaultingOffset')) {
            $nodes = @($xml.GetElementsByTagName('Data') | Where-Object {$_.GetAttribute('Name') -eq $name})
            if ($nodes.Count -ne 1) { throw "Unsupported event field: $name" }
            $text = [string]$nodes[0].InnerText
            if ($text.Length -gt 1024) { throw "Oversize event field: $name" }
            if ($name -eq 'ModuleName' -and [string]::IsNullOrWhiteSpace($text)) { throw 'Missing fault module' }
            $row[$name] = $text
        }
        $records += $row
    }
    $json = [ordered]@{status='ok';records=@($records)} | ConvertTo-Json -Compress -Depth 4
    if ([Text.Encoding]::UTF8.GetByteCount($json) -gt 131072) { throw 'Oversize event response' }
    [Console]::WriteLine($json)
} catch {
    $message = [string]$_.Exception.Message
    if ($message.Length -gt 512) { $message = $message.Substring(0,512) }
    [Console]::WriteLine(([ordered]@{status='unknown';reason=$message} | ConvertTo-Json -Compress))
    exit 1
}
'''


def _windows_number(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:0[xX][0-9a-fA-F]{1,16}|[0-9]{1,20})', value):
        raise ValueError('Unsupported Windows integer field')
    return int(value, 16 if value.lower().startswith('0x') else 10)


def _event_filetime(value):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,7}))?Z', value)
    if not match:
        raise ValueError('Unsupported event UTC time')
    date = datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    return int(date.timestamp()) * 10000000 + int((match[2] or '').ljust(7, '0')) + _FILETIME_EPOCH


def _parse_windows_events(payload, binding):
    if not isinstance(payload, dict) or payload.get('status') != 'ok':
        raise ValueError('Query did not return supported event data')
    records = payload.get('records')
    if not isinstance(records, list) or len(records) > 5:
        raise ValueError('Unsupported event count')
    for row in records:
        if (not isinstance(row, dict) or set(row) != {*_EVENT_FIELDS, 'provider', 'event_id', 'event_time'}
                or row['provider'] != 'Application Error' or type(row['event_id']) is not int
                or row['event_id'] != 1000
                or any(not isinstance(row[key], str) or len(row[key]) > 1024 for key in (*_EVENT_FIELDS, 'event_time'))
                or not row['ModuleName'].strip()):
            raise ValueError('Unsupported event schema')
        if (not binding['launch_start_filetime'] <= _event_filetime(row['event_time']) <= binding['reaped_filetime']
                or _windows_number(row['ProcessId']) != binding['pid']
                or not binding['launch_start_filetime'] <= _windows_number(row['ProcessCreationTime']) <= binding['launch_end_filetime']
                or ntpath.normcase(ntpath.normpath(row['AppPath'])) != ntpath.normcase(ntpath.normpath(binding['executable']))
                or ntpath.normcase(row['AppName']) != ntpath.normcase(ntpath.basename(binding['executable']))
                or not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{8}', row['ExceptionCode'])
                or int(row['ExceptionCode'].removeprefix('0x').removeprefix('0X'), 16) != binding['returncode'] & 0xffffffff
                or not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]{1,16}', row['FaultingOffset'])):
            raise ValueError('Event does not match the original child lifetime, identity or status')
    return records


def _windows_crash_events(directory, binding, executable):
    observation = {'status': 'unknown', 'reason': 'identity-unavailable', 'binding': dict(binding),
                   'operation': 'Application Error/EventID1000 read', 'tool_available': None,
                   'owner_invoked': False, 'cleanup_confirmed': None, 'records': []}
    deadline = time.monotonic() + 5
    try:
        with (directory / 'phases.jsonl').open('rb') as stream:
            first = stream.readline(8193)
        if len(first) > 8192 or not first.endswith(b'\n'):
            raise ValueError('Incomplete or oversize original identity')
        identity = json.loads(first)
        if (not isinstance(identity, dict) or identity.get('event') != 'identity'
                or type(identity.get('pid')) is not int or identity['pid'] != binding['pid']
                or any(not isinstance(identity.get(key), str) or not 0 < len(identity[key]) <= 2048
                       or '\0' in identity[key] for key in ('python', 'executable'))
                or not ntpath.isabs(identity['executable'])
                or ntpath.normcase(ntpath.normpath(identity['executable'])) != ntpath.normcase(ntpath.normpath(executable))
                or not binding['launch_start_filetime'] <= binding['launch_end_filetime'] <= binding['reaped_filetime']):
            raise ValueError('Original identity or UTC lifetime does not match')
        binding = observation['binding'] = {**binding, 'python': identity['python'], 'executable': identity['executable']}
        tool = shutil.which('powershell.exe')
        observation['tool_available'] = tool is not None
        if tool is None:
            observation['reason'] = 'powershell-unavailable'
            return observation
        forms = {str(binding['pid']), hex(binding['pid']), hex(binding['pid']).upper(),
                 f"0x{binding['pid']:X}", f"0x{binding['pid']:08x}", f"0x{binding['pid']:08X}"}
        predicate = ' or '.join(f"Data[@Name='ProcessId']='{value}'" for value in sorted(forms))
        script = (_EVENT_QUERY.replace('__START__', str(binding['launch_start_filetime']))
                  .replace('__END__', str(binding['reaped_filetime'])).replace('__PID_FILTER__', predicate))
        argv = [tool, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', script]
        (directory / 'windows-crash-events-request.json').write_text(json.dumps({'binding': binding, 'argv': argv}, indent=2) + '\n')
        from ergora.runtime import processes
        observation['owner_invoked'], observation['cleanup_confirmed'] = True, False
        owner = processes.run(argv, directory, directory / 'windows-crash-query', 5,
                              deadline=deadline, command_record=directory / 'windows-crash-query/command.json')
        observation['owner_result'] = owner
        if (not isinstance(owner, dict) or owner.get('status') not in ('succeeded', 'failed', 'timed_out', 'cancelled')
                or (owner.get('returncode') is not None and type(owner['returncode']) is not int)):
            raise ValueError('Unsupported query-owner result; cleanup unconfirmed')
        observation['cleanup_confirmed'] = True
        raw = {}
        for name in ('stdout', 'stderr'):
            path = directory / f'windows-crash-query/{name}.txt'
            with path.open('rb') as stream:
                data = stream.read(131073)
            size = path.stat().st_size
            observation[name] = {'bytes': size, 'complete_read': size <= 131072,
                                 'sha256': hashlib.sha256(data).hexdigest() if size <= 131072 else None}
            if size > 131072:
                raise ValueError('Oversize query output; complete original bytes retained')
            raw[name] = data
        if owner['status'] != 'succeeded' or owner['returncode'] != 0:
            observation['reason'] = 'query-' + owner['status']
            try:
                failure = json.loads(raw['stdout'].decode('utf-8-sig'))
                if isinstance(failure, dict) and failure.get('status') == 'unknown' and isinstance(failure.get('reason'), str):
                    observation['reason'] += ': ' + failure['reason'][:512]
            except (ValueError, UnicodeError):
                pass
            return observation
        records = _parse_windows_events(json.loads(raw['stdout'].decode('utf-8-sig')), binding)
        observation.update(status='matched' if records else 'unknown',
                           reason='original-child-events' if records else 'no-matching-events', records=records)
    except (Exception, KeyboardInterrupt) as error:
        observation['reason'] = type(error).__name__ + ': ' + str(error)[:512]
        for name in ('stdout', 'stderr'):
            path = directory / f'windows-crash-query/{name}.txt'
            if name not in observation and path.is_file():
                with path.open('rb') as stream:
                    data = stream.read(131073)
                size = path.stat().st_size
                observation[name] = {'bytes': size, 'complete_read': size <= 131072,
                                     'sha256': hashlib.sha256(data).hexdigest() if size <= 131072 else None}
    return observation


def _report_windows_crash_events(directory, binding, executable, output):
    try:
        observation = _windows_crash_events(directory, binding, executable)
        (directory / 'windows-crash-events.json').write_text(json.dumps(observation, indent=2) + '\n')
        summary = {key: observation[key] for key in ('status', 'reason', 'tool_available', 'owner_invoked', 'cleanup_confirmed')}
        summary['reason'] = summary['reason'][:160]
        summary['pid'], summary['record_count'] = binding['pid'], len(observation['records'])
        summary['records'] = observation['records']
        for key in ('python', 'executable'):
            if key in observation['binding']:
                summary[key] = observation['binding'][key][:160]
        def encode(value):
            return json.dumps(value, ensure_ascii=True).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        detail = encode(summary)
        if len(detail) > 3000:
            summary['records'] = observation['records'][:1]
            summary['complete_observation_in_artifact'] = True
            for key in ('reason', 'python', 'executable'):
                if key in summary:
                    summary[key] = summary[key][:64]
            detail = encode(summary)
            if len(detail) > 3000:
                summary['records'] = []
                detail = encode(summary)
        output(f'::notice title=Windows crash event observation::{detail}', annotation=True)
    except (Exception, KeyboardInterrupt):
        # An optional observation must never replace the original child outcome.
        try:
            output('::notice title=Windows crash event observation::{"status":"unknown","reason":"observation-write-failed"}', annotation=True)
        except (Exception, KeyboardInterrupt):
            pass


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
        launch_start = time.time_ns() // 100 + _FILETIME_EPOCH
        with subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, encoding='utf-8') as process:
            launch_end = time.time_ns() // 100 + _FILETIME_EPOCH
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
                reaped = time.time_ns() // 100 + _FILETIME_EPOCH
            finally:
                stop.set()
                monitor.join()
    result = {'returncode': returncode, 'seconds': time.monotonic() - started}
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    if returncode:
        diagnostics.report(output)
        details = tail.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        output(f'::error title=Native regression::{details}', annotation=True)
        if sys.platform == 'win32' and (returncode & 0xc0000000) == 0xc0000000:
            _report_windows_crash_events(directory, {
                'pid': process.pid, 'returncode': returncode, 'launch_start_filetime': launch_start,
                'launch_end_filetime': launch_end, 'reaped_filetime': reaped}, command[0], output)
    return returncode


if __name__ == '__main__':
    raise SystemExit(main())
