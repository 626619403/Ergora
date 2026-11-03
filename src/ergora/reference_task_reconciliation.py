"""Inspect original-run history and trusted external evidence without publishing it."""

import asyncio
from datetime import timedelta
import json
import os
import sys

from .reference_task_submission import _Submission


class _Inspection:
    def __init__(self, payload: dict):
        self.payload = payload
        self.submission = _Submission(payload)
        self.creation = self.submission.creation
        self.intent, self.run_id = self.submission.submitted()
        self.spec, self.sha = self.submission.spec, self.creation.sha
        if payload['run_id'] != self.run_id:
            raise ValueError('External evidence must pin the original submitted run ID')
        from dev_platform.adapter import FileAdapter

        config = self.creation.document(self.creation.safe_path(self.creation.config, 'adapter.json'))
        self.adapter = FileAdapter(config)
        expected = {name: self.creation.path(name) for name in ('requests', 'receipts', 'artifacts', 'approvals', 'fences')}
        if self.adapter.roots != expected:
            raise ValueError('External evidence adapter roots differ from the registered execution state')

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


def main() -> None:
    from agent_platform.core import Blocked, environment
    from dev_platform.runtime import RuntimeNotFound
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_Inspection(payload).run(), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: External evidence query timed out; no fence or lease was changed') from error
    except RuntimeNotFound as error:
        raise SystemExit('BLOCKED: Original external-evidence run was not found') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: External evidence RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, ImportError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
