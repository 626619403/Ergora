"""THROWAWAY Linux process-seam experiment; no Ergora budget implementation.

Run with an installed Ergora Python: python process-probe-prototype.py NEW_DIRECTORY
Only the supplied new scratch directory and this experiment's descendants are used.
"""

from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)
guardian = root / 'guardian-prototype.py'
guardian.write_text('''
import json,signal,sys,time
from pathlib import Path
from ergora import processes
request=Path(sys.argv[1]);out=Path(sys.argv[2])
budget=json.loads(request.read_bytes())
remaining=budget['work_deadline']-time.time()
result={'budget_id':budget['id'],'started_at':budget['started_at'],
        'deadline':budget['deadline'],'remaining_at_entry':remaining,'launch_attempted':False}
if remaining>0:
    def cancel(signum,frame): processes.cancel_supervised()
    signal.signal(signal.SIGALRM,cancel)
    signal.signal(signal.SIGTERM,cancel)
    signal.setitimer(signal.ITIMER_REAL,remaining)
    result['launch_attempted']=True
    try:
        result.update(processes.run([sys.executable,str(request.parent/'stage-prototype.py'),str(request.parent)],
            request.parent,out,max(1,int(remaining)),supervised=True))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
else:
    result['status']='exhausted-before-launch'
result['finished_at']=time.time()
result.pop('output',None)
print(json.dumps(result),flush=True)
'''.lstrip())


def identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'start_ticks': fields[19], 'state': fields[0]}
    except FileNotFoundError:
        return None


def descendants(pid, observed):
    record = identity(pid)
    if record is None:
        return
    observed[(pid, record['start_ticks'])] = record
    try:
        children = Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
    except FileNotFoundError:
        return
    for child in children:
        descendants(int(child), observed)


def run_guardian(folder, attempt):
    observed = {}
    manual_cleanup = []
    begin = time.monotonic()
    with (folder / (attempt + '.stdout')).open('xb') as stdout, (folder / (attempt + '.stderr')).open('xb') as stderr:
        process = subprocess.Popen([sys.executable, str(guardian), str(folder / 'budget-prototype.json'),
            str(folder / attempt)], stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            while process.poll() is None:
                descendants(process.pid, observed)
                if time.monotonic() - begin > 12:
                    raise TimeoutError('Prototype guardian exceeded its independent observation limit')
                time.sleep(.02)
            process.wait()
        finally:
            # Only identities sampled from our own guardian tree are eligible.
            for (pid, start), record in observed.items():
                current = identity(pid)
                if current is not None and current['start_ticks'] == start and current['state'] != 'Z':
                    manual_cleanup.append(current)
                    os.kill(pid, signal.SIGKILL)
            process.wait(timeout=5)
    assert process.returncode == 0, (folder / (attempt + '.stderr')).read_text()
    live = []
    for (pid, start), record in observed.items():
        current = identity(pid)
        if current is not None and current['start_ticks'] == start and current['state'] != 'Z':
            live.append(current)
    result = json.loads((folder / (attempt + '.stdout')).read_bytes())
    result.update(observation_seconds=time.monotonic() - begin, observed_processes=list(observed.values()),
                  live_after_observation=live, manual_cleanup=manual_cleanup)
    return result


results = []
for name in ('detached-child', 'blocked-lock', 'expired-before-entry'):
    folder = root / name
    folder.mkdir()
    started = time.time()
    wall, reserve, preparation_delay = (1.0, .3, 1.1) if name == 'expired-before-entry' else (3.2, 1.0, .8)
    budget = {'started_at': started, 'deadline': started + wall, 'work_deadline': started + wall - reserve,
              'wall_seconds': wall, 'cleanup_seconds': reserve}
    budget['id'] = hashlib.sha256(json.dumps(budget, sort_keys=True).encode()).hexdigest()
    request = folder / 'budget-prototype.json'
    request.write_text(json.dumps(budget, indent=2) + '\n')
    request_sha = hashlib.sha256(request.read_bytes()).hexdigest()
    stage = '''
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
folder=Path(sys.argv[1])
(folder/'stage-entered.json').write_text(json.dumps({'pid':os.getpid(),'at':time.time()}))
'''.lstrip()
    if name == 'detached-child':
        stage += '''
child=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)'],start_new_session=True)
(folder/'detached-child.json').write_text(json.dumps({'pid':child.pid,'at':time.time()}))
time.sleep(30)
'''
    else:
        stage += '''
with (folder/'blocked.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    (folder/'lock-acquired.json').write_text('{}')
    time.sleep(30)
'''
    (folder / 'stage-prototype.py').write_text(stage)
    with (folder / 'blocked.lock').open('a') as lock:
        if name == 'blocked-lock':
            fcntl.flock(lock, fcntl.LOCK_EX)
        time.sleep(preparation_delay)
        result = run_guardian(folder, 'first')
        again = run_guardian(folder, 'observe-original-budget')
    elapsed = result['finished_at'] - started
    assert hashlib.sha256(request.read_bytes()).hexdigest() == request_sha
    assert result['budget_id'] == again['budget_id'] == budget['id']
    assert result['deadline'] == again['deadline'] == budget['deadline']
    assert not result['live_after_observation'] and not again['live_after_observation']
    assert not result['manual_cleanup'] and not again['manual_cleanup'], 'Guardian left owned processes for the observer to stop'
    if name == 'expired-before-entry':
        assert result['status'] == 'exhausted-before-launch' and not result['launch_attempted']
        assert not (folder / 'stage-entered.json').exists()
    else:
        assert result['status'] == 'cancelled' and result['launch_attempted'] and elapsed < wall
        assert (folder / 'stage-entered.json').exists()
        if name == 'blocked-lock':
            assert not (folder / 'lock-acquired.json').exists()
        else:
            child_pid = json.loads((folder / 'detached-child.json').read_bytes())['pid']
            assert any(item['pid'] == child_pid for item in result['observed_processes'])
    assert again['status'] == 'exhausted-before-launch' and not again['launch_attempted']
    results.append({'case': name, 'budget': budget, 'preparation_delay_seconds': preparation_delay,
        'total_elapsed_to_first_return_seconds': elapsed, 'first': result, 'same_budget_again': again})

report = {'at': datetime.now(timezone.utc).isoformat(), 'cases': results,
    'scope': 'Throwaway real Linux subprocess/lock/subreaper experiment using existing processes.run supervised implementation. '
             'A prototype timer requests cancellation at one fixed absolute cutoff after an intentional preparation delay. '
             'No product task prepare/create/submission/Temporal/budget slot or Git command executed; no hard-real-time, '
             'uninterruptible-I/O, bounded cleanup failure, arbitrary daemon or complete native workflow acceptance claim.'}
(root / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'cases': [{'case': item['case'], 'elapsed': round(item['total_elapsed_to_first_return_seconds'], 3),
    'status': item['first']['status'], 'sampled_processes': len(item['first']['observed_processes']),
    'repeat_launched': item['same_budget_again']['launch_attempted'],
    'live': item['first']['live_after_observation']} for item in results], 'scope': report['scope']}), flush=True)
