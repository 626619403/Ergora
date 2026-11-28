"""Original job publication, with a dedicated owner for budgeted native jobs.

The owner uses the existing process supervisor and jobs ledger. A child may
produce pending evidence, but no terminal proves stopping until all owned
processes have been reaped. An uncertain attempt is never executed again.
"""

from abc import ABC, abstractmethod
from contextlib import closing, nullcontext
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

from agent_platform import executor as original
from agent_platform.core import Blocked, CONFIG, ROOT, STATE, UPSTREAM, git, read, require, settings, slug, write
from agent_platform.process_job import candidate_check_gate
from dev_platform.adapter import FileAdapter, MAX_RECEIPT_BYTES, identifier, publish, read_raw
from dev_platform.contracts import canonical_sha

from ergora.runtime import processes
from ergora.development import budget as reference_budget
from ergora.development import envelopes as task_envelopes
from ergora.development import verification
from ergora.development.runtime import fixed_checks
from ergora._paths import IMPORT_ROOT


class Job(ABC):
    def __init__(self, path: Path, home: Path, document: dict):
        envelope = task_envelopes.decode_job(read_raw(path.resolve(), task_envelopes.WIRE_LIMIT))
        self.bind(path, home, document, envelope, envelope['context']['spec']['request']['task_id'])

    def bind(self, path: Path, home: Path, document: dict, envelope: dict, task_id: str) -> None:
        self.path, self.home, self.document = path.resolve(), home, document
        self.envelope = envelope
        self.context = envelope['context']
        self.task_id = slug(task_id)
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
        instance = document['budget']['instance']
        self.bind_budget(instance, instance['policy']['wall_seconds'],
                         fixed_verification='verification' in document and self.context['stage'] == 'verify')

    def bind_budget(self, instance: dict, wall_seconds: int, *, fixed_verification: bool,
                    workspace: Path | None = None, fence: Path | None = None) -> None:
        self.instance = instance
        self.wall_seconds = wall_seconds
        self.fixed_verification = fixed_verification
        self.folder = (workspace or STATE / 'workspaces' / self.task_id / 'jobs' / self.job_id) / 'budget'
        self.fence = fence or STATE / 'fences' / (self.task_id + '.json')
        self.identity = {'schema_version': 1, 'job_id': self.job_id,
            'job_sha256': self.envelope['job_sha256'], 'admission_sha256': self.document['sha256'],
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
            PYTHONPATH=os.pathsep.join(map(str, (IMPORT_ROOT,
                ROOT / 'local', UPSTREAM / 'platform'))))
        observation = self.folder / 'observations' / uuid.uuid4().hex
        observation.mkdir(parents=True, mode=0o700)
        with (observation / 'stdout.json').open('x') as out, (observation / 'stderr.txt').open('x') as err:
            result = subprocess.run([sys.executable, '-P', '-c',
                'from ergora.development.runtime.jobs import main;main()'],
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

    def unknown(self, *, nested=False) -> dict:
        if nested:
            return {'status': 'unknown', 'job_id': self.job_id, 'budget_sha256': self.instance['sha256'],
                    'outer_cleanup_confirmed': True,
                    'detail': 'Original fixed process outcome unknown despite confirmed outer cleanup; '
                              'do not execute it again. Inspect ' + str(self.folder)}
        return {'status': 'unknown', 'job_id': self.job_id, 'budget_sha256': self.instance['sha256'],
                'detail': 'Original job attempt has no confirmed stopping witness; do not execute it again. Inspect '
                          + str(self.folder)}

    def unconfirmed_checks(self) -> bool:
        """Nested process outcomes and outer subtree cleanup are separate facts."""
        if not self.fixed_verification:
            return False
        for folder in (STATE / 'processes').glob('af-oracle-' + self.identity['job_sha256'] + '-*'):
            try:
                request = json.loads(read_raw(folder / 'request.json'))
            except FileNotFoundError:
                # The original writer creates its directory before linking a
                # request. No launch evidence means this publication stopped
                # before a monitor could submit a command.
                if not any(os.path.lexists(folder / name) for name in ('runner.log', 'lock', 'started.json', 'pid.json', 'terminal.json')):
                    continue
                return True
            except (OSError, ValueError, TypeError):
                return True
            try:
                binding = request['binding']
                subject = binding['subject']
                terminal = json.loads(read_raw(folder / 'terminal.json'))
                confirmed = (binding['kind'] == 'fixed-text-verification-process-v1'
                    and all(subject[key] == self.identity[key] for key in ('job_id', 'job_sha256', 'admission_sha256'))
                    and terminal['name'] == request['name'] == folder.name
                    and canonical_sha(terminal['binding']) == canonical_sha(binding)
                    and terminal['request_sha256'] == canonical_sha(request)
                    and type(terminal['returncode']) is int)
            except (OSError, ValueError, KeyError, TypeError):
                confirmed = False
            if not confirmed:
                return True
        return False

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
            if not cleanup and (self.cancelled or self.fence.exists()):
                return True
            if not cleanup and self.fixed_verification:
                cutoff = read(self.folder / 'owner.json')['verification_deadline']
                if (cutoff['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                        or time.monotonic() >= cutoff['monotonic']):
                    return True
            try:
                return self.remaining(cleanup=cleanup) <= 0
            except ValueError:
                # A clock/host discontinuity cannot authorize more work.
                return True

        environment = dict(os.environ, ERGORA_REFERENCE_JOB_OWNER=str(self.folder),
                           ERGORA_REFERENCE_JOB_LOCK_FD=str(lock.fileno()))
        return processes.run(command, self.home, self.folder / phase, self.wall_seconds,
            json.dumps(payload), environment, supervised=True, lock_fd=lock.fileno(), stop_requested=stopped)

    def own(self) -> dict:
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.folder / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            stage_started = time.monotonic()
            self.cancelled = False
            self.session = original.claim(self.job_id, self.envelope['job_sha256'])
            attempt = self.folder / 'attempt.json'
            if attempt.exists():
                require(read(attempt) == self.identity, 'Original budget job identity changed')
                return self.reconcile(lock)
            disposition = self.start_attempt(attempt, stage_started)
            if disposition is not None:
                return disposition
            def cancel(signum, frame):
                self.cancelled = True

            signal.signal(signal.SIGTERM, cancel)
            pending = self.folder / 'pending.json'
            body = self.supervise('body', [sys.executable, '-P', '-c',
                'from ergora.development.runtime.executor import pending_job;pending_job()'],
                {'request': str(self.path), 'home': str(self.home), 'pending': str(pending)}, lock)
            # A returned pending receipt is not evidence that descendants have
            # stopped. run(supervised=True) returns only after their reaping.
            write(self.folder / 'stopped.json', {**self.identity, 'body': body, 'cleanup_confirmed': True})
            if self.unconfirmed_checks():
                return self.unknown(nested=True)
            receipt = None
            if body['status'] == 'succeeded':
                receipt = self.collect_pending(lock)
            if receipt is None:
                receipt = self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained')
            return self.finalize(receipt)

    def start_attempt(self, attempt: Path, stage_started: float) -> dict | None:
        require(not self.terminal.exists(), 'Budget owner cannot adopt an independently published terminal')
        write(attempt, self.identity)
        write(self.folder / 'owner.json', self.owner_record(stage_started))
        return None

    def owner_record(self, stage_started: float) -> dict:
        ticks = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
        boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        record = {**self.identity, 'pid': os.getpid(), 'start_ticks': ticks, 'boot_id': boot_id}
        if self.fixed_verification:
            task_sampled = time.monotonic()
            remaining = self.remaining()
            record['verification_deadline'] = {'monotonic': min(stage_started + settings()['stage_walltime_seconds'],
                                                               task_sampled + remaining), 'boot_id': boot_id}
        return record

    def collect_pending(self, lock) -> dict | None:
        collected = self.supervise('collection', [sys.executable, '-P', '-c',
            'from ergora.development.runtime.jobs import collect;collect()'],
            {'request': str(self.path), 'pending': str(self.folder / 'pending.json'),
             'output': str(self.folder / 'collected.json')}, lock, cleanup=True)
        write(self.folder / 'collection-stopped.json', {**self.identity, 'collection': collected,
                                                       'cleanup_confirmed': True})
        if collected['status'] == 'succeeded':
            return json.loads(read_raw(self.folder / 'collected.json', MAX_RECEIPT_BYTES))

    def terminal_gate(self):
        return nullcontext()

    def finalize(self, receipt: dict, *, cleanup_confirmed: bool | None = True) -> dict:
        # Hashing was supervised after the business tree stopped. Fallbacks
        # were verified by failure(), without rereading large artifacts here.
        while True:
            candidate = self.folder / 'candidates' / (canonical_sha(receipt) + '.json')
            publish(candidate, receipt)
            if cleanup_confirmed is None:
                require(receipt['state'] == 'CANCELLED', 'A no-body disposition cannot publish success')
                remaining, clock_error = None, receipt['detail']
            else:
                try:
                    remaining, clock_error = self.remaining(cleanup=True), None
                except ValueError as error:
                    remaining, clock_error = None, str(error)
            cancelled = self.cancelled or self.fence.exists()
            if receipt['state'] == 'SUCCEEDED' and (remaining is None or remaining <= 0 or cancelled):
                receipt = self.failure('Original total budget expired or cancellation was observed before terminal publication')
                continue
            outcome = {**self.identity, 'cleanup_confirmed': cleanup_confirmed,
                'candidate_sha256': hashlib.sha256(read_raw(candidate)).hexdigest(),
                'candidate_file': candidate.relative_to(self.folder).as_posix(),
                'recorded_at': datetime.now(timezone.utc).isoformat(),
                'remaining_seconds': remaining,
                'overrun_seconds': max(0, -remaining) if remaining is not None else None,
                'clock_error': clock_error, 'cancel_requested': cancelled}
            write(self.folder / 'finalizations' / (uuid.uuid4().hex + '.json'), outcome)
            self.terminal.parent.mkdir(parents=True, exist_ok=True)
            with self.terminal_gate():
                if receipt['state'] == 'SUCCEEDED':
                    # Recheck the original allowance after durable preparation, under
                    # the same gate that accepts a scoped stop.
                    try:
                        authorized = self.remaining(cleanup=True) > 0 and not self.cancelled and not self.fence.exists()
                    except ValueError:
                        authorized = False
                    if not authorized:
                        receipt = self.failure('Original total budget expired or cancellation was observed before terminal publication')
                        continue
                try:
                    os.link(candidate, self.terminal)
                except FileExistsError:
                    require(read_raw(self.terminal) == read_raw(candidate), 'Budget terminal publication conflicts with original evidence')
            return self.record_terminal(receipt)

    def read_published_terminal(self) -> dict:
        raw = read_raw(self.terminal, MAX_RECEIPT_BYTES)
        receipt = json.loads(raw)
        candidate = self.folder / 'candidates' / (canonical_sha(receipt) + '.json')
        require(candidate.exists() and read_raw(candidate) == raw,
                'Published budget receipt has no original finalized candidate')
        return receipt

    def reconcile(self, lock) -> dict:
        if not (self.folder / 'stopped.json').exists():
            return self.unknown()
        stopped = read(self.folder / 'stopped.json')
        require(all(stopped[key] == value for key, value in self.identity.items())
                and stopped['cleanup_confirmed'] is True, 'Original stopping witness changed')
        if self.unconfirmed_checks():
            return self.unknown(nested=True)
        if self.terminal.exists():
            # The single owner may have been interrupted after linking its
            # late fallback but before updating the original jobs ledger.
            return self.record_terminal(self.read_published_terminal())
        # Resume finalization from a confirmed collection, never its body or
        # an uncertain collection attempt. All original phase evidence stays.
        collection = self.folder / 'collection-stopped.json'
        if stopped['body']['status'] != 'succeeded':
            return self.finalize(self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained'))
        if not collection.exists():
            # If nested outcomes arrived after the outer tree stopped, collect
            # its complete saved pending receipt once. An existing collection
            # directory is an original attempt and cannot be executed again.
            if (self.fixed_verification
                    and not (self.folder / 'collection').exists() and (self.folder / 'pending.json').exists()):
                receipt = self.collect_pending(lock)
                return self.finalize(receipt if receipt is not None else
                    self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained'))
            return self.unknown()
        record = read(collection)
        require(all(record[key] == value for key, value in self.identity.items())
                and record['cleanup_confirmed'] is True, 'Original collection stopping witness changed')
        if record['collection']['status'] != 'succeeded':
            return self.finalize(self.failure('Budget work stopped or evidence collection was not confirmed; pending evidence retained'))
        self.cancelled = any(read(path)['cancel_requested'] for path in (self.folder / 'finalizations').glob('*.json'))
        return self.finalize(json.loads(read_raw(self.folder / 'collected.json', MAX_RECEIPT_BYTES)))


class CandidateCheckJob(BudgetedJob):
    def __init__(self, path: Path, home: Path, envelope: dict):
        adapter = fixed_checks.check_adapter()
        admission = fixed_checks.authorized(adapter, envelope)
        context = envelope['context']
        relative = verification.fixed_check_receipt_name(envelope['job_id'])
        require(path == adapter.path('requests', relative), 'Candidate check job was moved from its original request')
        require(str(home) == admission['control_home'], 'Candidate check job belongs to another control directory')
        self.bind(path, home, admission, envelope, context['task_id'])
        self.adapter = adapter
        self.terminal = adapter.path('receipts', relative)
        self.workspace = fixed_checks.check_workspace(context)
        self.bind_budget(admission['budget'], admission['request']['wall_seconds'], fixed_verification=True,
                         workspace=self.workspace, fence=adapter.path('fences', self.task_id + '.json'))

    def remaining(self, *, cleanup=False) -> float:
        return fixed_checks.work_remaining(self.document, cleanup=cleanup)

    def terminal_gate(self):
        return candidate_check_gate(self.fence)

    def start_attempt(self, attempt: Path, stage_started: float) -> dict | None:
        disposition = self.folder / 'not-started.json'
        if disposition.exists():
            receipt = self.read_not_started()
            require(receipt['actor']['session_id'] == self.session, 'Unstarted check differs from its original job session')
            if self.terminal.exists():
                require(self.read_published_terminal() == receipt, 'Unstarted check terminal differs from its original disposition')
                return self.record_terminal(receipt)
            return self.finalize(receipt, cleanup_confirmed=None)

        require(not self.terminal.exists(), 'Budget owner cannot adopt an independently published terminal')
        try:
            record = self.owner_record(stage_started)
        except (OSError, ValueError) as error:
            receipt = self.failure('Candidate check could not admit a body under its original clock: ' + str(error)[:1300])
            publish(disposition, {**self.identity, 'body_started': False, 'receipt': receipt})
            return self.finalize(self.read_not_started(), cleanup_confirmed=None)
        write(attempt, self.identity)
        write(self.folder / 'owner.json', record)
        return None

    def read_not_started(self) -> dict:
        witness = fixed_checks.read_record(self.folder / 'not-started.json')
        receipt = witness['receipt']
        require(witness == {**self.identity, 'body_started': False, 'receipt': receipt}
                and receipt['state'] == 'CANCELLED' and not receipt['artifacts'] and not receipt['checks']
                and not any((self.folder / name).exists() for name in
                            ('attempt.json', 'owner.json', 'body', 'pending.json', 'stopped.json'))
                and not any((STATE / 'processes').glob('af-oracle-' + self.identity['job_sha256'] + '-*')),
                'Candidate check no-body disposition conflicts with original evidence')
        self.adapter.verify_receipt(self.envelope, receipt)
        fixed_checks.validate_receipt(self.adapter, self.envelope, receipt)
        return receipt

    def _receipt(self, state: str, detail: str, *, artifacts=(), checks=()):
        return {'schema_version': 1, 'job_id': self.job_id, 'job_sha256': self.envelope['job_sha256'],
                'state': state, 'actor': {'id': 'local-ci', 'kind': 'ci', 'role': 'fixed-checker', 'session_id': self.session},
                'candidate_sha': self.document['request']['candidate_sha'], 'artifacts': list(artifacts),
                'checks': list(checks), 'detail': detail}

    def failure(self, detail: str) -> dict:
        return self.adapter.verify_receipt(self.envelope, self._receipt('CANCELLED', detail))

    def execute(self) -> dict:
        from agent_platform.sandbox import Sandbox
        from ergora.storage.git import GitMaterials
        from ergora.storage.state import State
        from ergora.training.materials import read_raw as read_fixed_raw

        folder = require_budget_owner(self.document['sha256'], self.instance['sha256'], self.envelope)
        require(folder == self.folder, 'Candidate check differs from its original workspace owner')
        owner = fixed_checks.read_record(folder / 'owner.json')
        deadline = owner['verification_deadline']
        self.session = original.claim(self.job_id, self.envelope['job_sha256'])

        def remaining():
            require(not self.fence.exists() and deadline['boot_id'] == self.instance['boot_id']
                    and min(self.remaining(), deadline['monotonic'] - time.monotonic()) > 0,
                    'Candidate check stopped or original work allowance expired')

        try:
            remaining()
            project = State(self.home).project(self.document['project'])
            fixed_checks.check_project(project, self.home, self.document)
            sandbox = Sandbox()
            require(sandbox.probe()['available'], 'Candidate check requires the registered current-container trust boundary')
            candidate = self.document['request']['candidate_sha']
            repository = Path(self.document['repo'])
            materials = GitMaterials(repository, git='/usr/bin/git', scratch=self.workspace)
            require(materials.read('cat-file', '-t', candidate).strip() == b'commit', 'Candidate is not an original local Git commit')
            checkout, scratch, mirror = (self.workspace / name for name in ('checkout', 'output', 'repo.git'))
            scratch.mkdir(mode=0o700)
            remaining()
            git(self.workspace, 'init', '--bare', str(mirror))
            remaining()
            git(mirror, '-c', 'protocol.allow=never', '-c', 'protocol.file.allow=always', 'fetch',
                '--no-tags', '--no-write-fetch-head', str(repository), candidate)
            remaining()
            git(mirror, 'worktree', 'add', '--detach', str(checkout), candidate)
            remaining()
            subject = fixed_checks.check_subject(self.envelope)
            report = {'schema_version': 1, 'kind': 'fixed-candidate-check-results', 'candidate_sha': candidate}
            report['verification'] = fixed_checks.run_fixed_checks(self.document['verification'], subject, report,
                checkout=checkout, scratch=scratch, materials=materials, sandbox=sandbox,
                fence=self.fence, mirror=mirror, deadline=deadline, require_remaining=remaining)
            verification.validate_fixed_report(report, self.document['verification'], subject, process_root=STATE / 'processes',
                                               workspace=self.workspace, fence=self.fence, require_pass=False)
            remaining()
            relative = f'{self.task_id}/{self.job_id}/fixed-check-results.json'
            publish(self.adapter.path('artifacts', relative), report)
            raw = read_fixed_raw(self.adapter.path('artifacts', relative), verification.ARTIFACT_BYTES)
            artifact = {'name': 'fixed-check-results', 'path': relative, 'sha256': hashlib.sha256(raw).hexdigest()}
            passed = report['verification']['passed']
            return self._receipt('SUCCEEDED' if passed else 'FAILED', 'Independent registered fixed checks completed',
                                 artifacts=[artifact], checks=fixed_checks.check_rows(report['verification']['checks']))
        except (Blocked, OSError, ValueError, KeyError, TypeError) as error:
            return self._receipt('CANCELLED' if self.fence.exists() else 'FAILED', str(error)[:1500])


def require_owner(document: dict, envelope: dict | None = None) -> Path:
    return require_budget_owner(document['sha256'], document['budget']['instance']['sha256'], envelope)


def require_budget_owner(admission_sha256: str, budget_sha256: str, envelope: dict | None) -> Path:
    require('ERGORA_REFERENCE_JOB_OWNER' in os.environ, 'Budget executor requires its original dedicated owner')
    folder = Path(os.environ.get('ERGORA_REFERENCE_JOB_OWNER', '/nonexistent-budget-owner'))
    owner = read(folder / 'owner.json')
    parent = os.getppid()
    require(owner['pid'] == parent and owner['budget_sha256'] == budget_sha256
            and owner['admission_sha256'] == admission_sha256, 'Budget executor requires its original dedicated owner')
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
    envelope = task_envelopes.decode_job(read_raw(Path(payload['request']), task_envelopes.WIRE_LIMIT))
    receipt = json.loads(read_raw(Path(payload['pending']), MAX_RECEIPT_BYTES))
    if envelope['context'].get('kind') == task_envelopes.FIXED_CANDIDATE_CHECK:
        adapter = fixed_checks.check_adapter()
        adapter.verify_receipt(envelope, receipt)
        fixed_checks.validate_receipt(adapter, envelope, receipt)
    else:
        FileAdapter(read(CONFIG / 'adapter.json')).verify_receipt(envelope, receipt)
    publish(Path(payload['output']), receipt)


def main() -> None:
    payload = json.load(sys.stdin)
    path, home = Path(payload['request']), Path(payload['home'])
    envelope = task_envelopes.decode_job(read_raw(path, task_envelopes.WIRE_LIMIT))
    if envelope['context'].get('kind') == task_envelopes.FIXED_CANDIDATE_CHECK:
        job = CandidateCheckJob(path, home, envelope)
    else:
        task_id = slug(envelope['context']['spec']['request']['task_id'])
        document = task_envelopes.decode_admission(read_raw(
            STATE / 'tasks' / task_id / 'task.spec.json', task_envelopes.WIRE_LIMIT))
        job = BudgetedJob(path, home, document)
    require(all(payload[key] == value for key, value in job.identity.items()), 'Budget owner received a different original job')
    print(json.dumps(job.own(), ensure_ascii=False, allow_nan=False))
