"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
import hashlib
import json
import re

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities, require
    from dev_platform.adapter import FileAdapter, ContractViolation, read_raw
    from dev_platform.workflow import DevelopmentWorkflow, StopWork
    from ergora import task_envelopes


class CompositionAdapter(FileAdapter):
    """Publish only a complete v2 admission matching its execution projection."""

    envelope_version = 2

    async def submit(self, context):
        try:
            spec, composition = task_envelopes.unwrap(context['admission'])
            if (composition is None or context['admission']['schema_version'] != self.envelope_version
                    or not task_envelopes.matches_context(spec, context)):
                raise ValueError('Composition context differs from its complete admission')
        except (ValueError, TypeError, KeyError) as error:
            raise ContractViolation(str(error)) from error
        return await super().submit(context)


class CompositionActivities(Activities):
    @activity.defn(name=task_envelopes.COMPOSITION_SUBMIT)
    async def submit(self, context: dict) -> dict:
        return await super().submit(context)


@workflow.defn(name="ErgoraCompositionWorkflowV2")
class CompositionDevelopmentWorkflow(DevelopmentWorkflow):
    """Keep the original scheduler while binding every stage to its admission."""

    envelope_version = 2
    group_single_review = False
    operations = {'dev_submit': task_envelopes.COMPOSITION_SUBMIT}

    def __init__(self):
        super().__init__()
        self.admission = None

    @workflow.query
    def status(self) -> dict:
        return {**super().status(), "admission_sha256": self.admission["sha256"] if self.admission else None}

    async def call(self, name, value, result_type=dict):
        # Only a version-aware worker may publish composition requests. A legacy
        # worker on the same queue must never turn these into single-agent jobs.
        operation = self.operations.get(name, name)
        return await super().call(operation, value, result_type)

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        context = {**super().context(stage, expected_sha, unit, dependencies), "admission": self.admission}
        content = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(content) > 1_000_000:
            raise StopWork("Complete composition stage context exceeds 1,000,000 bytes; split the task")
        return context

    def authors(self):
        receipts = [value for stage, value in self.results.items()
                    if stage not in {'verify', 'review'} and not stage.startswith('review:') and 'actor' in value]
        return (sorted({value['actor']['id'] for value in receipts}),
                sorted({value['actor']['session_id'] for value in receipts}))

    async def stage(self, stage, expected_sha=None, unit=None, dependencies=None):
        if stage != 'review' or (len(self.admission['composition']['members']) == 1 and not self.group_single_review):
            return await super().stage(stage, expected_sha, unit, dependencies)
        composition = self.admission['composition']
        members = task_envelopes.review_members(composition)
        scopes = {scope['path']: asyncio.Semaphore(scope['limit'])
                  for leaf in members.values() for scope in leaf['concurrency_scopes']}

        async def review(path):
            async with AsyncExitStack() as stack:
                # A branch waiting for its subtree must not reserve ancestor
                # capacity that an independent sibling can already use.
                for scope in reversed(members[path]['concurrency_scopes']):
                    await stack.enter_async_context(scopes[scope['path']])
                return await self.stage('review:' + path, expected_sha, unit, dependencies)

        tasks = [asyncio.create_task(review(path)) for path in members]
        try:
            receipts = await asyncio.gather(*tasks)
            sessions = [receipt['actor']['session_id'] for receipt in receipts]
            if len(set(sessions)) != len(sessions):
                raise StopWork('Composition reviewers must use distinct independent sessions')
            aggregate = self._aggregate(expected_sha, members, receipts)
            self.results['review'] = aggregate
            return aggregate
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def _aggregate(self, candidate, members, receipts):
        return {'schema_version': 1, 'kind': 'composition-review-aggregate', 'decision': 'approve',
            'candidate_sha': candidate, 'admission_sha256': self.admission['sha256'],
            'review_instance': self.admission['composition']['review_instance'],
            'members': {path: {'stage': 'review:' + path, 'job_id': receipt['job_id'],
                'job_sha256': receipt['job_sha256'], 'receipt_sha256': task_envelopes.identity(receipt)}
                for path, receipt in zip(members, receipts)}}

    async def _run_document(self, document: dict) -> dict:
        try:
            spec, composition = task_envelopes.unwrap(document)
            if composition is None or document['schema_version'] != self.envelope_version:
                raise ValueError(f"The composition workflow requires a v{self.envelope_version} formal admission envelope")
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        self.admission = document
        outcome = await super().run(spec)
        return {**outcome, "admission_sha256": document["sha256"]}

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class ReviewRequirementsAdapter(CompositionAdapter):
    envelope_version = 3


class ReviewRequirementsActivities(CompositionActivities):
    @activity.defn(name=task_envelopes.REQUIREMENTS_SUBMIT)
    async def submit(self, context: dict) -> dict:
        return await super().submit(context)

    @activity.defn(name=task_envelopes.REQUIREMENTS_POLL)
    async def poll(self, job: dict) -> dict | None:
        if not job['context']['stage'].startswith('review:'):
            return await super().poll(job)
        try:
            async with asyncio.timeout(20):
                receipt = await self.adapter.poll(job)
            if receipt is None:
                return None
            # FileAdapter has verified terminal structure, job identity and every
            # artifact's bytes. A failed process alone is never a review opinion.
            artifacts = {item['name']: item for item in receipt['artifacts']}
            if 'composition-review-decision' not in artifacts:
                require(receipt['state'] != 'SUCCEEDED', 'Successful review is missing its trusted decision')
                return {'receipt': receipt, 'review_decision': None}

            def document(name):
                item = artifacts[name]
                raw = read_raw(self.adapter.path('artifacts', item['path']), 16_777_216)
                require(hashlib.sha256(raw).hexdigest() == item['sha256'], 'Review opinion artifact changed while reading')
                return json.loads(raw)

            decision = document('composition-review-decision')
            context = job['context']
            actor = receipt['actor']
            expected = {'schema_version': 1, 'kind': 'formal-review-decision',
                'job_id': job['job_id'], 'job_sha256': job['job_sha256'],
                'candidate_sha': context['expected_candidate_sha']}
            require(isinstance(decision, dict) and type(decision.get('schema_version')) is int
                    and set(decision) == expected.keys() | {'decision', 'result_sha256'}
                    and all(decision[key] == value for key, value in expected.items()), 'Review decision binding mismatch')
            require(decision['decision'] in ('approve', 'request-changes'), 'Invalid trusted review opinion')
            require(isinstance(decision['result_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', decision['result_sha256']),
                    'Invalid model result digest in trusted review opinion')
            approved = decision['decision'] == 'approve'
            require(receipt['state'] == ('SUCCEEDED' if approved else 'FAILED'), 'Review opinion differs from its original terminal state')
            require(actor['role'] == 'reviewer' and actor['kind'] == 'agent', 'Unexpected review executor role/kind')
            require(receipt['candidate_sha'] == context['expected_candidate_sha'], 'Review opinion candidate mismatch')
            require(actor['id'] not in context['author_ids'] and actor['session_id'] not in context['author_sessions'],
                    'Review opinion requires an independent principal and session')
            required = set(context['spec']['profile']['artifacts_by_stage']['review'])
            require(required <= artifacts.keys(), 'Missing required review artifacts')
            checks = {check['id']: check['status'] for check in receipt.get('checks', [])}
            require(checks.get('independent-review') == ('pass' if approved else 'fail')
                    and all(status == 'pass' for name, status in checks.items() if name != 'independent-review'),
                    'Review checks differ from the trusted opinion')
            invocation = document('composition-invocation')
            require(invocation['status'] == 'succeeded' and invocation['result_sha256'] == decision['result_sha256'],
                    'Review opinion differs from the actual successful model result')
            return {'receipt': receipt, 'review_decision': decision['decision']}
        except (ContractViolation, KeyError, TypeError, ValueError) as error:
            raise ApplicationError(str(error), type='ContractViolation', non_retryable=True) from error


@workflow.defn(name='ErgoraCompositionWorkflowV3')
class ReviewRequirementsWorkflow(CompositionDevelopmentWorkflow):
    envelope_version = 3
    group_single_review = True
    operations = {'dev_submit': task_envelopes.REQUIREMENTS_SUBMIT, 'dev_poll': task_envelopes.REQUIREMENTS_POLL}

    def __init__(self):
        super().__init__()
        self.review_decisions = {}

    async def stage(self, stage, expected_sha=None, unit=None, dependencies=None):
        if not stage.startswith('review:'):
            return await super().stage(stage, expected_sha, unit, dependencies)
        if self.cancel_reason:
            raise StopWork(self.cancel_reason)
        path = stage.removeprefix('review:')
        requirement = self.admission['composition']['members'][path]['review_requirement']
        self.active_stages.append(stage)
        try:
            job = await self.call('dev_submit', self.context(stage, expected_sha, unit, dependencies))
            deadline = workflow.now() + timedelta(seconds=self.spec['profile']['stage_timeout_seconds'])
            while True:
                if self.cancel_reason:
                    raise StopWork(self.cancel_reason)
                observation = await self.call('dev_poll', job, dict | None)
                if observation is not None:
                    receipt, decision = observation['receipt'], observation['review_decision']
                    if decision is None or (requirement == 'required' and decision != 'approve'):
                        self.cancel_reason = 'Stage ' + stage + ' ended as ' + receipt['state']
                        raise StopWork(self.cancel_reason)
                    self.results[stage] = receipt
                    self.review_decisions[path] = decision
                    return receipt
                remaining = (deadline - workflow.now()).total_seconds()
                if remaining <= 0:
                    self.cancel_reason = 'Stage deadline exceeded: ' + stage
                    raise StopWork(self.cancel_reason)
                try:
                    await workflow.wait_condition(lambda: self.cancel_reason is not None,
                        timeout=timedelta(seconds=min(self.spec['profile']['poll_seconds'], remaining)))
                except asyncio.TimeoutError:
                    pass
        finally:
            self.active_stages.remove(stage)

    def _aggregate(self, candidate, members, receipts):
        aggregate = super()._aggregate(candidate, members, receipts)
        aggregate['schema_version'] = 2
        for path, reference in aggregate['members'].items():
            reference.update(review_requirement=self.admission['composition']['members'][path]['review_requirement'],
                             decision=self.review_decisions[path])
        return aggregate

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)
