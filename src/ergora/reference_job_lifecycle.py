"""Original job publication, with a dedicated owner for budgeted native jobs.

The owner uses the existing process supervisor and jobs ledger. A child may
produce pending evidence, but no terminal proves stopping until all owned
processes have been reaped. An uncertain attempt is never executed again.
"""

from abc import ABC, abstractmethod
from contextlib import closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from agent_platform import executor as original
from agent_platform.core import Blocked, CONFIG, ROOT, STATE, UPSTREAM, read, require, slug, write
from dev_platform.adapter import FileAdapter, MAX_RECEIPT_BYTES, identifier, publish, read_raw
from dev_platform.contracts import canonical_sha

from . import processes, reference_budget


class Job(ABC):
    def __init__(self, path: Path, home: Path, document: dict):
        self.path, self.home, self.document = path.resolve(), home, document
        self.envelope = read(self.path)
        self.context = self.envelope['context']
        self.task_id = slug(self.context['spec']['request']['task_id'])
        self.job_id = identifier(self.envelope['job_id'])
        require(self.envelope['job_sha256'] == original.sha(self.context)
                and self.job_id == self.context['job_id']
                and self.job_id == self.task_id + '-' + canonical_sha({'stage': self.context['stage']})[:24],
                'Cannot bind job lifecycle to this envelope')
        self.terminal = STATE / 'receipts' / self.task_id / (self.job_id + '.json')
        self.adapter = FileAdapter(read(CONFIG / 'adapter.json'))

    @abstractmethod
    def run(self) -> dict:
        """Execute or observe the original job, never renew its authorization."""

    def record_terminal(self, receipt: dict) -> dict:
        with closing(original.ledger()) as db, db:
            db.execute('UPDATE jobs SET state=? WHERE id=?', (receipt['state'], self.job_id))
        return receipt


class DirectJob(Job):
    def __init__(self, path: Path, home: Path, document: dict, body):
        super().__init__(path, home, document)
        self.body = body

    def run(self) -> dict:
        receipt = self.body(self.envelope, self.home)
        self.adapter.verify_receipt(self.envelope, receipt)
        publish(self.terminal, receipt)
        return self.record_terminal(receipt)


class BudgetedJob(Job):
    def __init__(self, path: Path, home: Path, document: dict):
        super().__init__(path, home, document)
        self.instance = document['budget']['instance']
        self.folder = STATE / 'workspaces' / self.task_id / 'jobs' / self.job_id / 'budget'
        self.identity = {'schema_version': 1, 'job_id': self.job_id,
            'job_sha256': self.envelope['job_sha256'], 'admission_sha256': document['sha256'],
            'budget_sha256': self.instance['sha256']}

    def run(self) -> dict:
        # This wait keeps the original installation's active job slot occupied,
        # including during slow safety cleanup. A caller disappearing does not
        # terminate the independent owner or renew its work deadline.
        original.claim(self.job_id, self.envelope['job_sha256'])
        with closing(original.ledger()) as db, db:
            # Persist the reservation before an independent owner can exist.
            # Unknown attempts keep it; only record_terminal releases it.
            db.execute("UPDATE jobs SET state='OWNED' WHERE id=? AND state='RUNNING'", (self.job_id,))
        environment = dict(os.environ, AGENTFLOW_CONFIG_DIR=str(CONFIG), AGENTFLOW_STATE_DIR=str(STATE),
            PYTHONPATH=os.pathsep.join(map(str, (Path(__file__).parent.parent,
                ROOT / 'local', UPSTREAM / 'platform'))))
        observation = self.folder / 'observations' / uuid.uuid4().hex
        observation.mkdir(parents=True, mode=0o700)
        with (observation / 'stdout.json').open('x') as out, (observation / 'stderr.txt').open('x') as err:
            result = subprocess.run([sys.executable, '-P', '-c',
                'from ergora.reference_job_lifecycle import main;main()'],
                input=json.dumps({'request': str(self.path), 'home': str(self.home), **self.identity}),
                stdout=out, stderr=err, text=True, encoding='utf-8', env=environment, start_new_session=True)
        if result.returncode:
            raise Blocked('Budget job owner has no confirmed terminal; inspect ' + str(observation))
        outcome = json.loads(read_raw(observation / 'stdout.json', MAX_RECEIPT_BYTES))
        if outcome.get('status') == 'unknown':
            raise Blocked(outcome['detail'])
        return outcome

    def remaining(self, *, cleanup=False) -> float:
        return reference_budget.remaining(self.instance, cleanup=cleanup)

    def unknown(self) -> dict:
        return {'status': 'unknown', 'job_id': self.job_id, 'budget_sha256': self.instance['sha256'],
                'detail': 'Original job attempt has no confirmed stopping witness; do not execute it again. Inspect '
                          + str(self.folder)}

    def failure(self, detail: str) -> dict:
        receipt = {'schema_version': 1, 'job_id': self.job_id, 'job_sha256': self.envelope['job_sha256'],
            'state': 'CANCELLED', 'actor': {'id': 'budget-job-owner', 'session_id': self.session,
                'role': self.context['spec']['profile']['roles'][self.context['stage'].split(':', 1)[0]],
                'kind': 'ci'},
            'candidate_sha': self.context['spec']['request']['repository']['starting_sha'],
            'artifacts': [], 'checks': [], 'detail': detail}
        return self.adapter.verify_receipt(self.envelope, receipt)

    def supervise(self, phase: str, command: list[str], payload: dict, lock, *, cleanup=False) -> dict:
        def stopped():
            if not cleanup and (self.cancelled or (STATE / 'fences' / (self.task_id + '.json')).exists()):
                return True
            try:
                return self.remaining(cleanup=cleanup) <= 0
            except ValueError:
                # A clock/host discontinuity cannot authorize more work.
                return True

        environment = dict(os.environ, ERGORA_REFERENCE_JOB_OWNER=str(self.folder),
                           ERGORA_REFERENCE_JOB_LOCK_FD=str(lock.fileno()))
        return processes.run(command, self.home, self.folder / phase, self.instance['policy']['wall_seconds'],
            json.dumps(payload), environment, supervised=True, lock_fd=lock.fileno(), stop_requested=stopped)

    def own(self) -> dict:
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.folder / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.cancelled = False
            self.session = original.claim(self.job_id, self.envelope['job_sha256'])
            attempt = self.folder / 'attempt.json'
            if attempt.exists():
                require(read(attempt) == self.identity, 'Original budget job identity changed')
                return self.reconcile()
            require(not self.terminal.exists(), 'Budget owner cannot adopt an independently published terminal')
            write(attempt, self.identity)
            ticks = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
            write(self.folder / 'owner.json', {**self.identity, 'pid': os.getpid(), 'start_ticks': ticks,
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
            def cancel(signum, frame):
                self.cancelled = True

            signal.signal(signal.SIGTERM, cancel)
            pending = self.folder / 'pending.json'
            body = self.supervise('body', [sys.executable, '-P', '-c',
                'from ergora.reference_executor import pending_job;pending_job()'],
                {'request': str(self.path), 'home': str(self.home), 'pending': str(pending)}, lock)
            # A returned pending receipt is not evidence that descendants have
            # stopped. run(supervised=True) returns only after their reaping.
            write(self.folder / 'stopped.json', {**self.identity, 'body': body, 'cleanup_confirmed': True})
            receipt = None
            if body['status'] == 'succeeded':
                collected = self.supervise('collection', [sys.executable, '-P', '-c',
                    'from ergora.reference_job_lifecycle import collect;collect()'],
                    {'request': str(self.path), 'pending': str(pending), 'output': str(self.folder / 'collected.json')},
                    lock, cleanup=True)
                write(self.folder / 'collection-stopped.json', {**self.identity, 'collection': collected,
                                                               'cleanup_confirmed': True})
                if collected['status'] == 'succeeded':
                    receipt = json.loads(read_raw(self.folder / 'collected.json', MAX_RECEIPT_BYTES))
            if receipt is None:
                receipt = self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained')
            return self.finalize(receipt)

    def finalize(self, receipt: dict) -> dict:
        # Hashing was supervised after the business tree stopped. Fallbacks
        # were verified by failure(), without rereading large artifacts here.
        while True:
            candidate = self.folder / 'candidates' / (canonical_sha(receipt) + '.json')
            publish(candidate, receipt)
            try:
                remaining, clock_error = self.remaining(cleanup=True), None
            except ValueError as error:
                remaining, clock_error = None, str(error)
            cancelled = self.cancelled or (STATE / 'fences' / (self.task_id + '.json')).exists()
            if receipt['state'] == 'SUCCEEDED' and (remaining is None or remaining <= 0 or cancelled):
                receipt = self.failure('Original total budget expired or cancellation was observed before terminal publication')
                continue
            outcome = {**self.identity, 'cleanup_confirmed': True,
                'candidate_sha256': hashlib.sha256(read_raw(candidate)).hexdigest(),
                'candidate_file': candidate.relative_to(self.folder).as_posix(),
                'recorded_at': datetime.now(timezone.utc).isoformat(),
                'remaining_seconds': remaining,
                'overrun_seconds': max(0, -remaining) if remaining is not None else None,
                'clock_error': clock_error, 'cancel_requested': cancelled}
            write(self.folder / 'finalizations' / (uuid.uuid4().hex + '.json'), outcome)
            if receipt['state'] == 'SUCCEEDED':
                # Observation persistence consumes the same authorization. A
                # slow fsync can only change success to a failure candidate.
                try:
                    reference_budget.require_remaining(self.instance, cleanup=True)
                    authorized = not self.cancelled and not (STATE / 'fences' / (self.task_id + '.json')).exists()
                except ValueError:
                    authorized = False
                if not authorized:
                    receipt = self.failure('Original total budget expired or cancellation was observed before terminal publication')
                    continue
            self.terminal.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(candidate, self.terminal)
            except FileExistsError:
                require(read_raw(self.terminal) == read_raw(candidate), 'Budget terminal publication conflicts with original evidence')
            return self.record_terminal(receipt)

    def reconcile(self) -> dict:
        if not (self.folder / 'stopped.json').exists():
            return self.unknown()
        stopped = read(self.folder / 'stopped.json')
        require(all(stopped[key] == value for key, value in self.identity.items())
                and stopped['cleanup_confirmed'] is True, 'Original stopping witness changed')
        if self.terminal.exists():
            raw = read_raw(self.terminal, MAX_RECEIPT_BYTES)
            # The single owner may have been interrupted after linking its
            # late fallback but before updating the original jobs ledger.
            candidate = self.folder / 'candidates' / (canonical_sha(json.loads(raw)) + '.json')
            require(candidate.exists() and read_raw(candidate) == raw,
                    'Published budget receipt has no original finalized candidate')
            return self.record_terminal(json.loads(raw))
        # Resume finalization from a confirmed collection, never its body or
        # an uncertain collection attempt. All original phase evidence stays.
        collection = self.folder / 'collection-stopped.json'
        if stopped['body']['status'] != 'succeeded':
            return self.finalize(self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained'))
        if not collection.exists():
            return self.unknown()
        record = read(collection)
        require(all(record[key] == value for key, value in self.identity.items())
                and record['cleanup_confirmed'] is True, 'Original collection stopping witness changed')
        if record['collection']['status'] != 'succeeded':
            return self.finalize(self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained'))
        self.cancelled = any(read(path)['cancel_requested'] for path in (self.folder / 'finalizations').glob('*.json'))
        return self.finalize(json.loads(read_raw(self.folder / 'collected.json', MAX_RECEIPT_BYTES)))


def require_owner(document: dict, envelope: dict | None = None) -> Path:
    require('ERGORA_REFERENCE_JOB_OWNER' in os.environ, 'Budget executor requires its original dedicated owner')
    folder = Path(os.environ.get('ERGORA_REFERENCE_JOB_OWNER', '/nonexistent-budget-owner'))
    owner = read(folder / 'owner.json')
    parent = os.getppid()
    require(owner['pid'] == parent and owner['budget_sha256'] == document['budget']['instance']['sha256']
            and owner['admission_sha256'] == document['sha256'], 'Budget executor requires its original dedicated owner')
    if envelope is not None:
        require(owner['job_id'] == envelope['job_id'] and owner['job_sha256'] == envelope['job_sha256'],
                'Budget executor differs from its original owned job')
    actual_ticks = Path(f'/proc/{parent}/stat').read_text().rsplit(')', 1)[1].split()[19]
    require(actual_ticks == owner['start_ticks']
            and owner['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'Original job owner process identity changed')
    fd = int(os.environ['ERGORA_REFERENCE_JOB_LOCK_FD'])
    actual, expected = os.fstat(fd), (folder / 'lock').stat()
    require((actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino), 'Budget worker lost its original job lock')
    return folder


def claim_model(document: dict, stage: str, member: str | None) -> None:
    folder = require_owner(document)
    owner = read(folder / 'owner.json')
    task_id = document['legacy_spec']['request']['task_id']
    require(owner['job_id'] == task_id + '-' + canonical_sha({'stage': stage})[:24],
            'Model stage differs from its original owned job')
    require(document['budget']['slots'].get(stage) == member and member is not None,
            'Model stage does not match its reserved budget slot')
    instance = document['budget']['instance']
    reference_budget.require_remaining(instance)
    path = folder / 'model-attempt.json'
    require(not path.exists(), 'Original model slot already has a launch attempt; it cannot be executed again')
    write(path, {'budget_sha256': instance['sha256'], 'job_id': owner['job_id'],
                 'job_sha256': owner['job_sha256'], 'stage': stage, 'member': member})
    reference_budget.require_remaining(instance)


def collect() -> None:
    payload = json.load(sys.stdin)
    envelope = read(Path(payload['request']))
    receipt = json.loads(read_raw(Path(payload['pending']), MAX_RECEIPT_BYTES))
    FileAdapter(read(CONFIG / 'adapter.json')).verify_receipt(envelope, receipt)
    publish(Path(payload['output']), receipt)


def main() -> None:
    payload = json.load(sys.stdin)
    path, home = Path(payload['request']), Path(payload['home'])
    envelope = read(path)
    task_id = slug(envelope['context']['spec']['request']['task_id'])
    document = read(STATE / 'tasks' / task_id / 'task.spec.json')
    job = BudgetedJob(path, home, document)
    require(all(payload[key] == value for key, value in job.identity.items()), 'Budget owner received a different original job')
    print(json.dumps(job.own(), ensure_ascii=False, allow_nan=False))
