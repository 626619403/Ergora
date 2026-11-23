"""Inspect closed-run evidence and explicitly reconcile its original ingress claim."""

import asyncio
from contextlib import closing
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys

from ergora.development.runtime.submission import _Submission
from ergora.storage.state import file_lock
from ergora.development.envelopes import outcome_reference_state, wire_limit


class _UnconfirmedRelease(ValueError):
    """Current ingress storage could not prove the original release."""


def _checkpointed_ledger_identity(path: Path) -> tuple:
    if any(os.path.lexists(path.with_name(path.name + suffix)) for suffix in ('-wal', '-journal')):
        raise _UnconfirmedRelease('Original ingress ledger has a WAL or journal. Readiness requires a stable checkpoint')
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class _Inspection:
    def __init__(self, payload: dict, submission=None):
        self.payload = payload
        self.submission = submission or _Submission(payload)
        self.creation = self.submission.creation
        self.intent, self.run_id = self.submission.submitted()
        self.spec, self.sha = self.submission.spec, self.creation.sha
        if payload.get('run_id', self.run_id) != self.run_id:
            raise ValueError('External evidence must pin the original submitted run ID')
        self.adapter = self.creation.file_adapter(self.submission.input)

    async def jobs(self, handle, converter, temporal_status: str, *, usage: dict | None = None) -> dict:
        from dev_platform.adapter import identifier

        terminal = {'COMPLETED': 'completed', 'FAILED': 'failed', 'CANCELED': 'canceled',
                    'TERMINATED': 'terminated', 'TIMED_OUT': 'timed_out'}.get(temporal_status)
        jobs, next_event_id, first, last = {}, 1, None, None
        async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
            if (event.event_id != next_event_id
                    or next_event_id == 1 and not event.HasField('workflow_execution_started_event_attributes')):
                raise ValueError('External evidence requires the complete original run history')
            next_event_id += 1
            if usage is not None:
                if first is None:
                    first = event
                usage['events'] += 1
                usage['recorded_activity_starts'] += int(event.HasField('activity_task_started_event_attributes'))
                usage['signal_events'] += int(event.HasField('workflow_execution_signaled_event_attributes'))
            last = event
            if not event.HasField('activity_task_scheduled_event_attributes'):
                continue
            if usage is not None:
                usage['scheduled_activities'] += 1
            scheduled = event.activity_task_scheduled_event_attributes
            if scheduled.activity_type.name != self.submission.input.submit_activity:
                continue
            if len(scheduled.input.payloads) != 1:
                raise ValueError('Original submit history has no single context')
            values = await converter.decode(scheduled.input.payloads, [dict])
            if len(values) != 1 or not isinstance(values[0], dict):
                raise ValueError('Original submit history has no single context')
            context = values[0]
            if (context.get('request_sha256') != self.spec['request_sha256']
                    or not self.submission.input.matches_context(context) or not isinstance(context['stage'], str)):
                raise ValueError('Original history job context differs from the recorded task spec')
            job_id = identifier(context['job_id'])
            job = {'task_id': self.creation.task_id, 'job_id': job_id, 'job_sha256': self.sha(context), 'context': context}
            if job_id in jobs:
                if jobs[job_id]['job_sha256'] != job['job_sha256']:
                    raise ValueError('Original history contains conflicting contexts for the same job')
                jobs[job_id]['history_event_ids'].append(event.event_id)
            else:
                jobs[job_id] = {**job, 'history_event_ids': [event.event_id]}
        if last is None or terminal is not None and not last.HasField('workflow_execution_' + terminal + '_event_attributes'):
            raise ValueError('External evidence history lacks its original terminal event')
        if usage is not None:
            has_times = first.HasField('event_time') and last.HasField('event_time')
            seconds = ((last.event_time.ToNanoseconds() - first.event_time.ToNanoseconds()) / 1_000_000_000
                       if has_times else None)
            usage.update(dev_submit_events=sum(len(job['history_event_ids']) for job in jobs.values()),
                         unique_jobs=len(jobs),
                         workflow_span={'state': 'not_recorded' if seconds is None else
                                        'invalid_timestamps' if seconds < 0 else 'recorded',
                             'source': 'original_run_history', 'start_event_id': first.event_id,
                             'close_event_id': last.event_id,
                             'started_at': first.event_time.ToJsonString() if first.HasField('event_time') else None,
                             'closed_at': last.event_time.ToJsonString() if last.HasField('event_time') else None,
                             'value': seconds if seconds is not None and seconds >= 0 else None, 'unit': 'seconds'})
        return jobs

    async def files(self, jobs: dict, *, include_receipts: bool = False) -> dict:
        from dev_platform.adapter import identifier

        actual = set()
        for key in ('requests', 'receipts'):
            folder = self.adapter.path(key, self.creation.task_id)
            try:
                with os.scandir(folder) as entries:
                    actual.update(identifier(entry.name[:-5]) for entry in entries if entry.name.endswith('.json'))
            except FileNotFoundError:
                continue
        unexpected = sorted(actual - jobs.keys())
        observations, unresolved = [], set(unexpected)
        for job_id, job in sorted(jobs.items()):
            path = self.adapter.path('requests', self.creation.task_id + '/' + job_id + '.json')
            try:
                envelope = self.adapter.read_job(path)
            except FileNotFoundError:
                envelope = None
            expected = {'schema_version': 1, 'job_id': job_id, 'job_sha256': job['job_sha256'], 'context': job['context']}
            if envelope is not None and self.sha(envelope) != self.sha(expected):
                raise ValueError('External request envelope conflicts with its original history job')
            observation = {'job_id': job_id, 'stage': job['context']['stage'], 'job_sha256': job['job_sha256'],
                           'request_state': 'matches' if envelope is not None else 'missing',
                           'receipt_state': 'missing', 'receipt_sha256': None}
            receipt = None
            try:
                receipt = await self.adapter.poll(job)
                if receipt is not None:
                    observation.update(receipt_state=receipt['state'], receipt_sha256=self.sha(receipt))
            except (OSError, ValueError, TypeError) as error:
                observation.update(receipt_state='invalid', receipt_error=str(error)[:1500])
            if envelope is None or observation['receipt_state'] in ('missing', 'invalid'):
                unresolved.add(job_id)
            if include_receipts:
                observation.update(history_event_ids=job['history_event_ids'],
                                   receipt=receipt if observation['receipt_state'] not in ('missing', 'invalid') else None)
            observations.append(observation)
        fence_path = self.adapter.path('fences', self.creation.task_id + '.json')
        fence = self.creation.optional(fence_path)
        expected_fence = {'schema_version': 1, 'task_id': self.creation.task_id, 'request_sha256': self.spec['request_sha256']}
        if fence is not None and self.sha(fence) != self.sha(expected_fence):
            raise ValueError('External fence conflicts with the original task request')
        return {'jobs': observations, 'unexpected_jobs': unexpected, 'unresolved_jobs': sorted(unresolved),
                'fence': {'state': 'matches' if fence is not None else 'not_recorded',
                          'sha256': self.sha(fence) if fence is not None else None},
                'external_confirmed': fence is not None and not unresolved}

    async def observe(self, *, allow_running=False, usage=None, include_receipts=False) -> tuple[dict, dict]:
        handle, description, converter = await self.submission.lookup_run(self.intent, self.run_id)
        temporal_status = description.status.name
        running = temporal_status == 'RUNNING'
        if (not (allow_running and running)
                and temporal_status not in ('COMPLETED', 'FAILED', 'CANCELED', 'TERMINATED', 'TIMED_OUT')):
            raise ValueError('External evidence inspection requires the original closed run without a successor')
        _, latest, _ = await self.submission.lookup_run(self.intent)
        if latest.run_id != self.run_id:
            raise ValueError('Workflow now has a different run; its external task scope requires separate reconciliation')
        outcome = None
        if temporal_status == 'COMPLETED':
            outcome = await handle.result(follow_runs=False, rpc_timeout=timedelta(seconds=20))
            if (not isinstance(outcome, dict) or outcome.get('task_id') != self.creation.task_id
                    or outcome.get('request_sha256') != self.spec['request_sha256']):
                raise ValueError('Original closed outcome differs from the recorded task request')
        status = None
        if running:
            status = await handle.query('status', rpc_timeout=timedelta(seconds=20))
            if (status['request_sha256'] != self.spec['request_sha256']
                    or status['admission_sha256'] != self.submission.input.document['sha256']):
                raise ValueError('Runtime status differs from the original task admission')
        jobs = await self.jobs(handle, converter, temporal_status, usage=usage)
        result = {'schema_version': 1, 'project': self.creation.project['id'],
                'project_revision': self.creation.project['revision'], 'task_id': self.creation.task_id,
                'workflow_id': self.intent['workflow_id'], 'run_id': self.run_id, 'runtime_status': 'queried',
                'terminal': not running, 'temporal_status': temporal_status, 'original_outcome': outcome,
                'history_jobs_sha256': self.sha([{'job_id': key, 'job_sha256': value['job_sha256']}
                                               for key, value in sorted(jobs.items())]),
                **await self.files(jobs, include_receipts=include_receipts),
                'lease_released_by_operation': False, 'execution_success': None}
        if running:
            result.update(external_confirmed=False, phase=status['phase'], pending_plan_sha256=status['plan_sha256']
                          if status['phase'] == 'AWAITING_PLAN_APPROVAL' else None)
        return result, jobs

    async def run(self) -> dict:
        indexed = self.payload['operation'] in ('inspect-index', 'export-handoff')
        usage = {'events': 0, 'scheduled_activities': 0, 'recorded_activity_starts': 0, 'signal_events': 0} if indexed else None
        result, _ = await self.observe(usage=usage, include_receipts=indexed)
        outcome = result['original_outcome']
        if indexed:
            response_limit = wire_limit(self.submission.input.document)
            selection = self.submission.creation_record['files']['agent-bindings.json']
            profile = self.spec['profile']
            usage.update(source='original_run_history', configured_work_units=len(self.spec['request']['input']['work_units']))
            usage.update({name: {'state': 'not_recorded', 'value': None, 'unit': unit, 'source': None}
                          for name, unit in (('model_calls', 'calls'), ('tokens', 'tokens'), ('cost', 'currency'))})
            usage['cost']['currency'] = None
            for job in result['jobs']:
                job['outcome_reference_state'] = outcome_reference_state(outcome, job)
            result.update(read_only=True, index_type='original-task-evidence',
                request_sha256=self.spec['request_sha256'], profile_sha256=self.spec['profile_sha256'],
                contract={'spec': self.spec, 'spec_sha256': self.sha(self.spec),
                          'creation_sha256': self.intent['creation_sha256'],
                          'submission_sha256': self.sha(self.intent), 'agent_bindings': selection,
                          'agent_bindings_sha256': self.sha(selection), **self.submission.input.evidence_contract()},
                original_outcome_sha256=self.sha(outcome) if outcome is not None else None,
                budget={'source': 'frozen_task_spec.profile', 'profile_sha256': self.spec['profile_sha256'],
                        'scope': 'workflow_admission_and_waiting', 'limits': profile['limits'],
                        **{key: profile[key] for key in ('stage_timeout_seconds', 'approval_timeout_seconds', 'poll_seconds')}},
                usage=usage,
                published_evidence='verified' if not result['unresolved_jobs'] else 'incomplete',
                context_snapshots={key: {'state': 'not_recorded'} for key in
                                   ('evaluations', 'skills', 'memories', 'source_adoptions')},
                artifact_limit_bytes=16_777_216, response_limit_bytes=response_limit)
            self.creation.check_size(result, response_limit, 'Task evidence index')
        if self.payload['operation'] == 'export-handoff':
            from dev_platform.adapter import read_raw
            import ergora.development.handoff as handoff

            def read_artifact(artifact):
                return read_raw(self.adapter.path('artifacts', artifact['path']), handoff.BLOB_LIMIT)

            return handoff.create(result, read_artifact, Path(self.payload['output']))
        return result


class _Reconciliation:
    def __init__(self, payload: dict, inspection=None):
        self.payload = payload
        self.inspection = inspection or _Inspection(payload)
        self.creation = self.inspection.creation
        self.core, self.sha = self.creation.core, self.creation.sha
        self.claim_path = self.creation.path('tasks/' + self.creation.task_id + '/cli-ingress.json')
        self.claim = {'tracker': self.inspection.spec['request']['tracker'], 'owner': 'local-cli',
                      'task_id': self.creation.task_id, 'spec_sha256': self.sha(self.inspection.spec)}
        self.check_claim()
        prefix = 'ergora/task-reconciliations/' + self.creation.task_id
        self.intent_path = self.creation.path(prefix + '.intent.json')
        self.attempt_path = self.creation.path(prefix + '.attempt.json')
        self.evidence_path = self.creation.path(prefix + '.evidence.json')
        self.result_path = self.creation.path(prefix + '.result.json')

    def check_claim(self) -> None:
        if self.sha(self.creation.document(self.claim_path)) != self.sha(self.claim):
            raise ValueError('Reconciliation ingress ownership differs from the original local task claim')

    def record(self, revision: int) -> dict:
        return {**self.inspection.submission.expected, 'operation': 'reconcile', 'project_revision': revision,
                'submission_sha256': self.sha(self.inspection.intent), 'run_id': self.inspection.run_id,
                'claim': self.claim}

    def load(self) -> dict | None:
        intent = self.creation.optional(self.intent_path)
        if intent is None:
            if any(path.exists() for path in (self.attempt_path, self.evidence_path, self.result_path)):
                raise ValueError('Reconciliation records have no original intent')
        elif (type(intent.get('project_revision')) is not int or intent['project_revision'] < 1
              or self.sha(intent) != self.sha(self.record(intent['project_revision']))):
            raise ValueError('Reconciliation intent conflicts with its original submission, run or claim')
        return intent

    def checkpoint(self, intent: dict, observation: dict) -> dict:
        status, outcome = observation['temporal_status'], observation['original_outcome']
        if status not in ('COMPLETED', 'FAILED', 'CANCELED', 'TERMINATED', 'TIMED_OUT'):
            raise ValueError('Reconciliation checkpoint requires the original closed run')
        if status == 'COMPLETED':
            if (not isinstance(outcome, dict) or outcome.get('task_id') != self.creation.task_id
                    or outcome.get('request_sha256') != self.inspection.spec['request_sha256']):
                raise ValueError('Reconciliation checkpoint has a different original outcome')
        elif outcome is not None:
            raise ValueError('Reconciliation checkpoint invents an outcome for a non-completed run')
        digest = observation['history_jobs_sha256']
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Reconciliation checkpoint requires its history job digest')
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'workflow_id': intent['workflow_id'],
                'run_id': intent['run_id'], 'temporal_status': status, 'original_outcome': outcome,
                'history_jobs_sha256': digest}

    def evidence(self, attempt: dict, observation: dict) -> dict:
        from dev_platform.adapter import identifier

        if (observation['external_confirmed'] is not True or observation['unresolved_jobs'] != []
                or observation['unexpected_jobs'] != []):
            raise ValueError('Reconciliation evidence requires all original external jobs to be confirmed')
        fence = {'schema_version': 1, 'task_id': self.creation.task_id,
                 'request_sha256': self.inspection.spec['request_sha256']}
        if observation['fence'] != {'state': 'matches', 'sha256': self.sha(fence)}:
            raise ValueError('Reconciliation evidence has no matching original fence')
        jobs = observation['jobs']
        if not isinstance(jobs, list):
            raise ValueError('Reconciliation evidence jobs must be a list')
        identities = []
        for job in jobs:
            if (set(job) != {'job_id', 'stage', 'job_sha256', 'request_state', 'receipt_state', 'receipt_sha256'}
                    or not isinstance(job['stage'], str) or job['request_state'] != 'matches'
                    or job['receipt_state'] not in ('SUCCEEDED', 'FAILED', 'CANCELLED')
                    or any(not isinstance(job[key], str) or not re.fullmatch('[0-9a-f]{64}', job[key])
                           for key in ('job_sha256', 'receipt_sha256'))):
                raise ValueError('Reconciliation evidence contains an unconfirmed job')
            identities.append({'job_id': identifier(job['job_id']), 'job_sha256': job['job_sha256']})
        if (len({job['job_id'] for job in identities}) != len(identities)
                or self.sha(sorted(identities, key=lambda job: job['job_id'])) != attempt['history_jobs_sha256']):
            raise ValueError('Reconciliation evidence differs from its complete original history jobs')
        return {**attempt, 'jobs': jobs, 'fence': observation['fence'], 'unexpected_jobs': [],
                'unresolved_jobs': [], 'external_confirmed': True}

    def receipt(self, intent: dict, evidence: dict) -> dict:
        outcome = evidence['original_outcome']
        native_release = outcome is not None and (outcome.get('status') == 'REVIEW_READY' or
                         outcome.get('status') == 'BLOCKED' and isinstance(outcome.get('fence'), dict)
                         and outcome['fence'].get('confirmed') is True)
        # Native export/result may have released this exact claim already. Keep
        # its immutable evidence digest whenever the original release applies.
        return {'schema_version': 1, 'intent_sha256': self.sha(intent), 'evidence_sha256': self.sha(evidence),
                'release_evidence_sha256': self.sha(outcome) if native_release else self.sha(evidence),
                'lease_released': True}

    def status(self, intent: dict | None) -> dict:
        result = {'project': self.creation.project['id'], 'project_revision': self.creation.project['revision'],
                  'task_id': self.creation.task_id, 'run_id': self.inspection.run_id,
                  'runtime_status': 'not_queried', 'execution_success': None, 'lease_released': None,
                  'external_confirmed': None}
        if intent is None:
            return {**result, 'status': 'not_recorded'}
        receipt = self.creation.optional(self.result_path)
        evidence = self.creation.optional(self.evidence_path)
        attempt = self.creation.optional(self.attempt_path)
        if attempt is not None and self.sha(attempt) != self.sha(self.checkpoint(intent, attempt)):
            raise ValueError('Reconciliation checkpoint conflicts with its original intent')
        if evidence is not None:
            if attempt is None or self.sha(evidence) != self.sha(self.evidence(attempt, evidence)):
                raise ValueError('Reconciliation evidence conflicts with its original checkpoint')
        if receipt is not None:
            if evidence is None or self.sha(receipt) != self.sha(self.receipt(intent, evidence)):
                raise ValueError('Reconciliation result conflicts with its saved cleanup evidence')
        return {**result, 'status': 'reconciled' if receipt is not None else 'confirmed' if evidence is not None
                else 'unknown' if attempt is not None else 'prepared',
                'workflow_id': intent['workflow_id'], 'intent_sha256': self.sha(intent),
                'attempt_saved': attempt is not None, 'evidence_saved': evidence is not None,
                'result_saved': receipt is not None, 'external_confirmed': True if evidence is not None else None,
                'original_outcome': attempt['original_outcome'] if attempt is not None else None,
                'temporal_status': attempt['temporal_status'] if attempt is not None else None,
                'lease_released': True if receipt is not None else None,
                'evidence_sha256': self.sha(evidence) if evidence is not None else None,
                'release_evidence_sha256': receipt['release_evidence_sha256'] if receipt is not None else None}

    def release_checkpoint(self, observation=None, *, check_ledger=False) -> tuple[str, dict | None]:
        """Join the original release record to current closure evidence when supplied."""
        intent = self.load()
        status = self.status(intent)
        if status['status'] != 'reconciled':
            return status['status'], None
        if observation is not None:
            evidence = self.evidence(self.checkpoint(intent, observation), observation)
            if self.sha(evidence) != status['evidence_sha256']:
                raise ValueError('Original external evidence differs from its durable reconciliation')
        if check_ledger:
            self.require_released_claim(status['release_evidence_sha256'])
        checkpoint = self.creation.document(self.evidence_path)
        if self.sha(checkpoint) != status['evidence_sha256']:
            raise ValueError('Original durable reconciliation changed during release inspection')
        plan = next((job for job in checkpoint['jobs'] if job['stage'] == 'plan'
                     and job['receipt_state'] == 'SUCCEEDED'), None)
        return status['status'], {key: status[key] for key in ('evidence_sha256', 'release_evidence_sha256')} | {
            'history_jobs_sha256': checkpoint['history_jobs_sha256'],
            'plan_receipt_sha256': plan['receipt_sha256'] if plan else None}

    def require_released_claim(self, evidence_sha256: str, *, checkpointed=False) -> None:
        from dev_platform.ingress import _identity

        resource, claim_id = _identity(**self.claim)
        path = self.creation.path('ingress/leases.sqlite3')
        try:
            coordinator_uid = os.getuid()
            parent = path.parent.lstat()
            if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != coordinator_uid or parent.st_mode & 0o022:
                raise _UnconfirmedRelease(
                    'Original ingress directory must be owned by the coordinator with group/world writes disabled')
            info = path.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != coordinator_uid or info.st_mode & 0o077:
                raise _UnconfirmedRelease('Original ingress ledger must remain a private regular file')
            # A preview cannot create SQLite sidecars or checkpoint somebody
            # else's WAL. Only a stable checkpointed file supports that read.
            # Preparation can use the native ledger's current WAL view.
            before = _checkpointed_ledger_identity(path) if checkpointed else None
            access = '?mode=ro&immutable=1' if checkpointed else '?mode=rw'
            with closing(sqlite3.connect(path.as_uri() + access, uri=True, timeout=5)) as db:
                db.execute('PRAGMA query_only=ON')
                row = db.execute('SELECT c.resource, c.owner, c.task_id, c.spec_sha256, '
                                 'c.released_at, c.evidence_digest, a.claim_id FROM claims c '
                                 'LEFT JOIN active a ON a.claim_id=c.claim_id WHERE c.claim_id=?', (claim_id,)).fetchone()
            if checkpointed and before != _checkpointed_ledger_identity(path):
                raise _UnconfirmedRelease('Original ingress ledger changed during the read-only checkpoint')
        except (OSError, sqlite3.Error) as error:
            raise _UnconfirmedRelease('Original ingress release could not be verified') from error
        if (row is None or row[:4] != (resource, self.claim['owner'], self.claim['task_id'], self.claim['spec_sha256'])
                or row[4] is None or row[5] != evidence_sha256 or row[6] is not None):
            raise _UnconfirmedRelease('Original ingress claim has no matching durable release')

    def amendment_binding(self, closure: dict) -> dict:
        submission = self.inspection.submission
        return _amendment_origin(submission) | {'run_id': self.inspection.run_id,
                                                'submission_sha256': self.sha(self.inspection.intent), **closure}

    async def reconcile(self, intent: dict) -> dict:
        from dev_platform.ingress import IngressLeases

        before = await self.inspection.run()
        if before['unexpected_jobs']:
            raise ValueError('Unexpected external jobs are outside the original run; preserve its task scope')
        attempt = self.checkpoint(intent, before)
        self.creation.check_size(attempt, 1_048_576, 'reconciliation checkpoint')
        self.core.write(self.attempt_path, attempt)
        # Repeating the same immutable fence is safe after a lost response. Its
        # directory-only confirmation is deliberately ignored in favor of b1.
        await self.inspection.adapter.fence({'task_id': self.creation.task_id,
                                             'request_sha256': self.inspection.spec['request_sha256']})
        after = await self.inspection.run()
        if self.sha(attempt) != self.sha(self.checkpoint(intent, after)):
            raise ValueError('Original history or outcome changed during external reconciliation')
        if after['external_confirmed'] is not True:
            if self.evidence_path.exists():
                raise ValueError('Saved cleanup evidence is no longer confirmed; the lease cannot be released')
            return {**self.status(intent), 'runtime_status': 'queried', 'external_confirmed': False,
                    'unresolved_jobs': after['unresolved_jobs'], 'unexpected_jobs': after['unexpected_jobs'],
                    'instruction': 'Preserve the original intent and obtain trusted terminal receipts before resume-reconcile'}
        evidence = self.evidence(attempt, after)
        self.creation.check_size(evidence, 1_048_576, 'reconciliation evidence')
        self.core.write(self.evidence_path, evidence)
        self.check_claim()
        ledger_path = self.creation.path('ingress/leases.sqlite3')
        if not ledger_path.is_file():
            raise ValueError('Original ingress ledger is missing; cleanup evidence cannot create ownership')
        receipt = self.receipt(intent, evidence)
        with closing(IngressLeases(ledger_path)) as leases:
            leases.release(**intent['claim'], evidence_digest=receipt['release_evidence_sha256'])
        self.core.write(self.result_path, receipt)
        return self.status(intent)

    async def run(self) -> dict:
        operation = self.payload['operation']
        if operation == 'status':
            return self.status(self.load())
        preparing = operation in ('prepare', 'prepare-resume')
        with file_lock(self.creation.lock_path, blocking=not preparing):
            intent = self.load()
            if operation == 'prepare':
                if intent is not None:
                    return {'created': False, 'reconciliation': self.status(intent)}
                intent = self.record(self.creation.project['revision'])
                self.core.write(self.intent_path, intent)
                return {'created': True, 'reconciliation': self.status(intent)}
            if intent is None or self.payload['intent_sha256'] != self.sha(intent):
                raise ValueError('Reconciliation recovery requires the exact original intent digest')
            status = self.status(intent)
            if operation == 'prepare-resume' or status['status'] == 'reconciled':
                return status
            if operation not in ('dispatch', 'resume'):
                raise ValueError('Unsupported task reconciliation operation')
            return await self.reconcile(intent)


def _amendment_origin(submission) -> dict:
    document = submission.input.document
    return {'task_id': submission.creation.task_id, 'workflow_id': submission.expected['workflow_id'],
            'creation_sha256': submission.expected['creation_sha256'],
            'request_sha256': submission.spec['request_sha256'], 'admission_sha256': document['sha256'],
            'budget_sha256': document['budget']['instance']['sha256']}


def _amendment_jobs(inspection, observed, history) -> tuple[dict, dict]:
    jobs = {row['stage']: row for row in observed['jobs']}
    if len(jobs) != len(observed['jobs']):
        raise ValueError('Original history has conflicting job IDs for a stage')
    units = {}
    for unit in inspection.spec['request']['input']['work_units']:
        job = jobs.get('work:' + unit['id'])
        if job is None:
            units[unit['id']] = {'state': 'unscheduled' if observed['terminal'] else 'not_observed'}
        else:
            terminal = job['request_state'] == 'matches' and job['receipt_sha256'] is not None
            unsound = (observed['terminal'] or job['request_state'] != 'matches' or job['receipt_state'] == 'invalid')
            units[unit['id']] = {**job, 'state': 'terminal' if terminal else 'unresolved' if unsound else 'submitted'}
    if observed['unexpected_jobs']:
        units = {key: ({'state': 'unavailable'} if row['state'] in ('unscheduled', 'not_observed') else row)
                 for key, row in units.items()}
    plan = jobs.get('plan')
    if plan is None or plan['request_state'] != 'matches' or plan['receipt_state'] != 'SUCCEEDED':
        return units, {'state': 'unavailable'}
    digest = plan['receipt_sha256']
    accepted = any(jobs[entry['context']['stage']]['request_state'] == 'matches'
                   and approved.get('plan_sha256') == digest
                   and inspection.sha(approved.get('receipt')) == digest
                   and bool(approved.get('approval', {}).get('approval_sha256'))
                   for entry in history.values() if (approved := entry['context'].get('approved_plan')))
    return units, {'receipt_sha256': digest, 'job_id': plan['job_id'],
                   'state': 'accepted' if accepted else 'pending' if observed.get('pending_plan_sha256') == digest
                   else 'published'}


async def _amendment_checkpoint(payload: dict) -> dict:
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    submission = _Submission(payload)
    submission.prepare()
    if submission.input.version != 12:
        raise ValueError('Plan amendments require an original budgeted native task')
    origin = _amendment_origin(submission)
    status = submission.status(submission.load())
    result = {'origin': {**origin, 'run_id': status['run_id'], 'submission_sha256': status.get('intent_sha256')},
              'original_definition': submission.creation_record['definition'],
              'original_budget_id': submission.input.document['budget']['instance']['id'],
              'original_required_checks': submission.spec['profile']['required_checks'],
              'submission_status': status['status'], 'runtime_status': 'not_queried', 'closure': None,
              'plan': {'state': 'unavailable'}, 'work': {unit['id']: {'state': 'unavailable'}
                  for unit in submission.spec['request']['input']['work_units']}}
    if status['status'] != 'submitted':
        return {**result, 'next_action': status['next_action']}
    inspection = _Inspection(payload, submission)
    try:
        observed, history = await inspection.observe(allow_running=True)
    except RuntimeNotFound:
        return {**result, 'runtime_status': 'not_found', 'next_action': 'read_original_run'}
    except RPCError as error:
        return {**result, 'runtime_status': 'unavailable', 'runtime_error': error.status.name,
                'next_action': 'read_original_run'}
    work, plan = _amendment_jobs(inspection, observed, history)
    result.update(runtime_status='queried', work=work, plan=plan, **{key: observed[key] for key in (
        'terminal', 'temporal_status', 'original_outcome', 'fence', 'external_confirmed', 'unexpected_jobs', 'unresolved_jobs')})
    if not observed['terminal']:
        return {**result, 'phase': observed['phase'], 'next_action': 'request_original_cancellation'}
    owner = _Reconciliation(payload, inspection)
    reconciliation, closure = owner.release_checkpoint(observed if observed['external_confirmed'] else None)
    result['reconciliation_status'] = reconciliation
    if not observed['external_confirmed'] or closure is None:
        return {**result, 'next_action': 'inspect_original_cleanup' if reconciliation == 'reconciled'
                else 'reconcile_original_run'}
    try:
        owner.require_released_claim(closure['release_evidence_sha256'],
                                     checkpointed=payload.get('checkpointed_release', True))
    except _UnconfirmedRelease as error:
        return {**result, 'release_status': 'unconfirmed', 'release_error': str(error),
                'next_action': 'inspect_original_release'}
    return {**result, 'release_status': 'confirmed', 'closure': owner.amendment_binding(closure),
            'next_action': 'prepare_successor'}


async def _amendment_release(payload: dict) -> dict:
    """Recheck the local release during the successor's final write reservation."""
    owner = _Reconciliation(payload)
    if owner.inspection.submission.input.version != 12:
        raise ValueError('Amendment requires the current budgeted native task')
    _, closure = owner.release_checkpoint(check_ledger=True)
    return {'issue_id': owner.claim['tracker']['issue_id'],
            'closure': owner.amendment_binding(closure) if closure is not None else None}


def main() -> None:
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        operation = payload['operation']
        if operation not in ('status', 'prepare', 'prepare-resume', 'inspect-amendment-release'):
            os.environ.update(environment())
        if operation == 'inspect-amendment':
            action = _amendment_checkpoint(payload)
        elif operation == 'inspect-amendment-release':
            action = _amendment_release(payload)
        else:
            owner = _Inspection(payload) if operation in ('inspect', 'inspect-index', 'export-handoff') else _Reconciliation(payload)
            action = owner.run()
        result = asyncio.run(asyncio.wait_for(action, payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        message = ('Task handoff timed out; inspect the output file before collecting again' if operation == 'export-handoff' else
                   'Task evidence index query timed out; no fence or lease was changed' if operation == 'inspect-index' else
                   'External evidence query timed out; no fence or lease was changed' if operation == 'inspect' else
                   'Amendment checkpoint query timed out; original closure is unverified'
                   if operation in ('inspect-amendment', 'inspect-amendment-release') else
                   'Reconciliation timed out; inspect task reconciliation and resume its original intent')
        raise SystemExit('BLOCKED: ' + message) from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original external-evidence run was not found') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: External evidence RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
