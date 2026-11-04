"""Inspect closed-run evidence and explicitly reconcile its original ingress claim."""

import asyncio
from contextlib import closing
from datetime import timedelta
import json
import os
import re
import sys

from .reference_task_submission import _Submission
from .state import file_lock


class _Inspection:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.intent, self.run_id = self.submission.submitted()
        self.spec, self.sha = self.submission.spec, self.creation.sha
        if payload.get('run_id', self.run_id) != self.run_id:
            raise ValueError('External evidence must pin the original submitted run ID')
        self.adapter = self.creation.file_adapter()

    async def jobs(self, handle, converter, temporal_status: str) -> dict:
        from dev_platform.adapter import identifier

        terminal = {'COMPLETED': 'completed', 'FAILED': 'failed', 'CANCELED': 'canceled',
                    'TERMINATED': 'terminated', 'TIMED_OUT': 'timed_out'}[temporal_status]
        terminal_field = 'workflow_execution_' + terminal + '_event_attributes'
        jobs, next_event_id, last = {}, 1, None
        async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
            if (event.event_id != next_event_id
                    or next_event_id == 1 and not event.HasField('workflow_execution_started_event_attributes')):
                raise ValueError('External evidence requires the complete original run history')
            next_event_id += 1
            last = event
            if not event.HasField('activity_task_scheduled_event_attributes'):
                continue
            scheduled = event.activity_task_scheduled_event_attributes
            if scheduled.activity_type.name != 'dev_submit':
                continue
            if len(scheduled.input.payloads) != 1:
                raise ValueError('Original dev_submit history has no single context')
            values = await converter.decode(scheduled.input.payloads, [dict])
            if len(values) != 1 or not isinstance(values[0], dict):
                raise ValueError('Original dev_submit history has no single context')
            context = values[0]
            expected = {'task_id': self.creation.task_id, 'request_sha256': self.spec['request_sha256'],
                        'profile_sha256': self.spec['profile_sha256']}
            if (any(context.get(key) != value for key, value in expected.items())
                    or self.sha(context['spec']) != self.sha(self.spec) or not isinstance(context['stage'], str)):
                raise ValueError('Original history job context differs from the recorded task spec')
            job_id = identifier(context['job_id'])
            job = {'task_id': self.creation.task_id, 'job_id': job_id, 'job_sha256': self.sha(context), 'context': context}
            if job_id in jobs and self.sha(jobs[job_id]) != self.sha(job):
                raise ValueError('Original history contains conflicting contexts for the same job')
            jobs[job_id] = job
        if last is None or not last.HasField(terminal_field):
            raise ValueError('External evidence history lacks its original terminal event')
        return jobs

    async def files(self, jobs: dict) -> dict:
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
            envelope = self.creation.optional(path)
            expected = {'schema_version': 1, 'job_id': job_id, 'job_sha256': job['job_sha256'], 'context': job['context']}
            if envelope is not None and self.sha(envelope) != self.sha(expected):
                raise ValueError('External request envelope conflicts with its original history job')
            observation = {'job_id': job_id, 'stage': job['context']['stage'], 'job_sha256': job['job_sha256'],
                           'request_state': 'matches' if envelope is not None else 'missing',
                           'receipt_state': 'missing', 'receipt_sha256': None}
            try:
                receipt = await self.adapter.poll(job)
                if receipt is not None:
                    observation.update(receipt_state=receipt['state'], receipt_sha256=self.sha(receipt))
            except (OSError, ValueError, TypeError) as error:
                observation.update(receipt_state='invalid', receipt_error=str(error)[:1500])
            if envelope is None or observation['receipt_state'] in ('missing', 'invalid'):
                unresolved.add(job_id)
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

    async def run(self) -> dict:
        handle, description, converter = await self.submission.lookup_run(self.intent, self.run_id)
        temporal_status = description.status.name
        if temporal_status not in ('COMPLETED', 'FAILED', 'CANCELED', 'TERMINATED', 'TIMED_OUT'):
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
        jobs = await self.jobs(handle, converter, temporal_status)
        return {'schema_version': 1, 'project': self.creation.project['id'],
                'project_revision': self.creation.project['revision'], 'task_id': self.creation.task_id,
                'workflow_id': self.intent['workflow_id'], 'run_id': self.run_id, 'runtime_status': 'queried',
                'terminal': True, 'temporal_status': temporal_status, 'original_outcome': outcome,
                'history_jobs_sha256': self.sha([{'job_id': key, 'job_sha256': value['job_sha256']}
                                               for key, value in sorted(jobs.items())]),
                **await self.files(jobs), 'lease_released_by_operation': False, 'execution_success': None}


class _Reconciliation:
    def __init__(self, payload: dict):
        self.payload = payload
        self.inspection = _Inspection(payload)
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


def main() -> None:
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        operation = payload['operation']
        if operation not in ('status', 'prepare', 'prepare-resume'):
            os.environ.update(environment())
        owner = _Inspection(payload) if operation == 'inspect' else _Reconciliation(payload)
        result = asyncio.run(asyncio.wait_for(owner.run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        message = ('External evidence query timed out; no fence or lease was changed' if operation == 'inspect' else
                   'Reconciliation timed out; inspect task reconciliation and resume its original intent')
        raise SystemExit('BLOCKED: ' + message) from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original external-evidence run was not found') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: External evidence RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
