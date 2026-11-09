"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

import asyncio
from contextlib import AsyncExitStack
import json

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities
    from dev_platform.adapter import FileAdapter, ContractViolation
    from dev_platform.workflow import DevelopmentWorkflow, StopWork
    from ergora import task_envelopes


class CompositionAdapter(FileAdapter):
    """Publish only a complete v2 admission matching its execution projection."""

    async def submit(self, context):
        try:
            spec, composition = task_envelopes.unwrap(context['admission'])
            if composition is None or not task_envelopes.matches_context(spec, context):
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

    def __init__(self):
        super().__init__()
        self.admission = None

    @workflow.query
    def status(self) -> dict:
        return {**super().status(), "admission_sha256": self.admission["sha256"] if self.admission else None}

    async def call(self, name, value, result_type=dict):
        # Only a version-aware worker may publish composition requests. A legacy
        # worker on the same queue must never turn these into single-agent jobs.
        operation = task_envelopes.COMPOSITION_SUBMIT if name == 'dev_submit' else name
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
        if stage != 'review' or len(self.admission['composition']['members']) == 1:
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
            aggregate = {'schema_version': 1, 'kind': 'composition-review-aggregate', 'decision': 'approve',
                'candidate_sha': expected_sha, 'admission_sha256': self.admission['sha256'],
                'review_instance': composition['review_instance'],
                'members': {path: {'stage': 'review:' + path, 'job_id': receipt['job_id'],
                    'job_sha256': receipt['job_sha256'], 'receipt_sha256': task_envelopes.identity(receipt)}
                    for path, receipt in zip(members, receipts)}}
            self.results['review'] = aggregate
            return aggregate
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    @workflow.run
    async def run(self, document: dict) -> dict:
        try:
            spec, composition = task_envelopes.unwrap(document)
            if composition is None:
                raise ValueError("The composition workflow requires a v2 formal admission envelope")
        except (ValueError, TypeError, KeyError) as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        self.admission = document
        outcome = await super().run(spec)
        return {**outcome, "admission_sha256": document["sha256"]}
