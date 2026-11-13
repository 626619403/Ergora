"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

import asyncio
from contextlib import AsyncExitStack
from datetime import datetime, timedelta
import json

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities
    from dev_platform.adapter import FileAdapter, ContractViolation
    from dev_platform.workflow import DevelopmentWorkflow, RETRY, StopWork
    from ergora import reference_budget, task_envelopes
    from ergora.reference_review_opinions import review_observation


class CompositionAdapter(FileAdapter):
    """Publish only a complete v2 admission matching its execution projection."""

    envelope_version = 2

    def validate_submission(self, context):
        try:
            spec, composition = task_envelopes.unwrap(context['admission'])
            if (composition is None or context['admission']['schema_version'] != self.envelope_version
                    or not task_envelopes.matches_context(spec, context)):
                raise ValueError('Composition context differs from its complete admission')
        except (ValueError, TypeError, KeyError) as error:
            raise ContractViolation(str(error)) from error

    async def submit(self, context):
        self.validate_submission(context)
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
    complete_inventory_context = False
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
        if stage == 'inventory' and self.complete_inventory_context:
            try:
                return task_envelopes.issue_inventory_context(self.admission, expected_sha)
            except ValueError as error:
                raise StopWork(str(error)) from error
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
        outcome = await self.run_spec(spec)
        return {**outcome, "admission_sha256": document["sha256"]}

    async def run_spec(self, spec: dict) -> dict:
        return await super().run(spec)

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
            return review_observation(self.adapter, job, receipt)
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


class ReviewDAGAdapter(ReviewRequirementsAdapter):
    envelope_version = 4


class ReviewDAGActivities(ReviewRequirementsActivities):
    @activity.defn(name=task_envelopes.DAG_SUBMIT)
    async def submit(self, context: dict) -> dict:
        return await super().submit(context)

    @activity.defn(name=task_envelopes.DAG_POLL)
    async def poll(self, job: dict) -> dict | None:
        return await super().poll(job)


@workflow.defn(name='ErgoraCompositionWorkflowV4')
class ReviewDAGWorkflow(ReviewRequirementsWorkflow):
    """Schedule original leaf stages when their frozen control predecessors finish."""

    envelope_version = 4
    operations = {'dev_submit': task_envelopes.DAG_SUBMIT, 'dev_poll': task_envelopes.DAG_POLL}

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        context = super().context(stage, expected_sha, unit, dependencies)
        if stage.startswith('review:'):
            composition = self.admission['composition']
            dag = task_envelopes.review_dag(composition)
            ports = dag.input_ports(stage.removeprefix('review:'))
            context['review_ports'] = {'schema_version': 1, 'kind': 'formal-review-ports', 'ports': ports,
                'producers': {path: self.results[self.source_stage(path)] for path in ports['sources']}}
            if len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                              allow_nan=False).encode('utf-8')) > 1_000_000:
                raise StopWork('Complete review DAG context exceeds 1,000,000 bytes; split the task')
        return context

    def source_stage(self, path):
        return 'review:' + path

    async def stage(self, stage, expected_sha=None, unit=None, dependencies=None):
        if stage != 'review':
            return await super().stage(stage, expected_sha, unit, dependencies)
        composition = self.admission['composition']
        dag = task_envelopes.review_dag(composition)
        scopes = {scope['path']: asyncio.Semaphore(scope['limit'])
                  for leaf in dag.members.values() for scope in leaf['concurrency_scopes']}
        remaining, completed, running, sessions = set(dag.members), set(), {}, set()

        async def review(path):
            async with AsyncExitStack() as stack:
                for scope in reversed(dag.members[path]['concurrency_scopes']):
                    await stack.enter_async_context(scopes[scope['path']])
                return await self.stage('review:' + path, expected_sha, unit, dependencies)

        try:
            while remaining or running:
                if self.cancel_reason:
                    raise StopWork(self.cancel_reason)
                for path in sorted(remaining):
                    if set(dag.predecessors[path]) <= completed:
                        running[path] = asyncio.create_task(review(path))
                        remaining.remove(path)
                await workflow.wait(running.values(), return_when=asyncio.FIRST_COMPLETED)
                for path in sorted(list(running)):
                    if running[path].done():
                        receipt = await running.pop(path)
                        if self.cancel_reason:
                            raise StopWork(self.cancel_reason)
                        session = receipt['actor']['session_id']
                        if session in sessions:
                            raise StopWork('Composition reviewers must use distinct independent sessions')
                        sessions.add(session)
                        completed.add(path)
            aggregate = self._aggregate(expected_sha, dag.members,
                [self.results['review:' + path] for path in dag.members])
            self.results['review'] = aggregate
            return aggregate
        finally:
            for task in running.values():
                task.cancel()
            if running:
                await asyncio.gather(*running.values(), return_exceptions=True)

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class WorkDeliveryAdapter(ReviewDAGAdapter):
    envelope_version = 5


class WorkDeliveryActivities(ReviewDAGActivities):
    @activity.defn(name=task_envelopes.WORK_SUBMIT)
    async def submit(self, context: dict) -> dict:
        return await super().submit(context)

    @activity.defn(name=task_envelopes.WORK_POLL)
    async def poll(self, job: dict) -> dict | None:
        return await super().poll(job)


@workflow.defn(name='ErgoraCompositionWorkflowV5')
class WorkDeliveryWorkflow(ReviewDAGWorkflow):
    """Extend original unit scheduling with frozen ownership and ancestor limits."""

    envelope_version = 5
    operations = {'dev_submit': task_envelopes.WORK_SUBMIT, 'dev_poll': task_envelopes.WORK_POLL}

    def source_stage(self, path):
        execution = self.admission['composition']['execution']
        units = {member: unit for unit, member in execution['assignments'].items()}
        return 'work:' + units[path] if path in units else super().source_stage(path)

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        context = super().context(stage, expected_sha, unit, dependencies)
        if stage.startswith('work:'):
            delivery = task_envelopes.work_delivery(self.admission['composition'], self.spec)
            member = delivery.assignments[unit['id']]
            ports = delivery.work.input_ports(member)
            context['work_ports'] = {'schema_version': 1, 'kind': 'formal-work-ports', 'member': member,
                'ports': ports, 'producers': {path: self.results[self.source_stage(path)] for path in ports['sources']}}
            if len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                              allow_nan=False).encode('utf-8')) > 1_000_000:
                raise StopWork('Complete work stage context exceeds 1,000,000 bytes; split the task')
        return context

    async def units(self):
        # The original unit IDs, dependency commits and running tasks remain the
        # schedule. Scope counts derive from those tasks, never another ledger.
        delivery = task_envelopes.work_delivery(self.admission['composition'], self.spec)
        remaining = {unit['id']: unit for unit in self.spec['request']['input']['work_units']}
        completed, running, sessions = set(), {}, set()
        concurrency = self.spec['profile']['limits']['max_parallel_units']
        scopes = {key: delivery.work.members[path]['concurrency_scopes'] for key, path in delivery.assignments.items()}
        try:
            while remaining or running:
                if self.cancel_reason:
                    raise StopWork(self.cancel_reason)
                used = {}
                for key in running:
                    for scope in scopes[key]:
                        used[scope['path']] = used.get(scope['path'], 0) + 1
                for key in sorted(list(remaining)):
                    unit = remaining[key]
                    if (len(running) >= concurrency or not set(unit['depends_on']) <= completed
                            or any(used.get(scope['path'], 0) >= scope['limit'] for scope in scopes[key])):
                        continue
                    dependencies = {parent: self.results['work:' + parent] for parent in unit['depends_on']}
                    running[key] = asyncio.create_task(self.stage('work:' + key, unit=unit, dependencies=dependencies))
                    del remaining[key]
                    for scope in scopes[key]:
                        used[scope['path']] = used.get(scope['path'], 0) + 1
                if not running:
                    raise StopWork('No runnable original work unit under its frozen limits')
                await workflow.wait(running.values(), return_when=asyncio.FIRST_COMPLETED)
                for key in sorted(list(running)):
                    if running[key].done():
                        receipt = await running.pop(key)
                        if self.cancel_reason:
                            raise StopWork(self.cancel_reason)
                        session = receipt['actor']['session_id']
                        if session in sessions:
                            raise StopWork('Work instances require distinct original sessions')
                        sessions.add(session)
                        completed.add(key)
        finally:
            for task in running.values():
                task.cancel()
            if running:
                await asyncio.gather(*running.values(), return_exceptions=True)

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class StageResultsAdapter(WorkDeliveryAdapter):
    envelope_version = 6


@workflow.defn(name='ErgoraCompositionWorkflowV6')
class StageResultsWorkflow(WorkDeliveryWorkflow):
    """The same original schedule, with explicitly versioned stage-result inputs."""

    envelope_version = 6

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class IssueSourceAdapter(StageResultsAdapter):
    envelope_version = 7


@workflow.defn(name='ErgoraCompositionWorkflowV7')
class IssueSourceWorkflow(StageResultsWorkflow):
    """Retain the original schedule and its complete source-bearing admission."""

    envelope_version = 7

    complete_inventory_context = True

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class FullStageMaterialsAdapter(StageResultsAdapter):
    envelope_version = 8


@workflow.defn(name='ErgoraCompositionWorkflowV8')
class FullStageMaterialsWorkflow(StageResultsWorkflow):
    """Select complete preparation materials within the original six-stage run."""

    envelope_version = 8

    complete_inventory_context = True

    @workflow.run
    async def run(self, document: dict) -> dict:
        return await self._run_document(document)


class BudgetedAdapter(FullStageMaterialsAdapter):
    envelope_version = 9

    def validate_submission(self, context):
        super().validate_submission(context)
        try:
            reference_budget.require_remaining(context['admission']['budget']['instance'])
        except ValueError as error:
            raise ContractViolation(str(error)) from error


@workflow.defn(name='ErgoraCompositionWorkflowV9')
class BudgetedWorkflow(FullStageMaterialsWorkflow):
    """Bound the original orchestration, including waits outside stage polling."""

    envelope_version = 9

    def remaining(self, *, cleanup=False):
        instance = self.admission['budget']['instance']
        deadline = datetime.fromisoformat(instance['deadline_at'])
        if not cleanup:
            deadline -= timedelta(seconds=instance['policy']['cleanup_seconds'])
        return (deadline - workflow.now()).total_seconds()

    @workflow.query
    def status(self) -> dict:
        result = super().status()
        if self.admission is not None:
            instance = self.admission['budget']['instance']
            result['budget'] = {key: instance[key] for key in ('id', 'sha256', 'authorized_at', 'deadline_at')}
        return result

    async def call(self, name, value, result_type=dict):
        cleanup = name == 'dev_fence'
        remaining = self.remaining(cleanup=cleanup)
        if not cleanup and remaining <= 0:
            raise StopWork('Original budget work cutoff reached')
        # A fence is safety work, never a fresh business grant. If even its
        # reserve elapsed, the bounded attempt may remain unconfirmed; the job
        # owner still owns its independent stop and cleanup.
        timeout = max(.001, remaining)
        return await workflow.execute_activity(self.operations.get(name, name), value, result_type=result_type,
            start_to_close_timeout=timedelta(seconds=min(30, timeout)),
            schedule_to_close_timeout=timedelta(seconds=min(180, timeout)), retry_policy=RETRY)

    async def stop(self, reason):
        if self.remaining() <= 0 and not self.cancel_reason:
            self.cancel_reason = 'Original budget work cutoff reached'
        return await super().stop(self.cancel_reason or reason)

    async def run_spec(self, spec: dict) -> dict:
        remaining = self.remaining()
        if remaining <= 0:
            # Let the original run initialize the task and take its ordinary
            # StopWork -> fence path before the first control activity.
            return await super().run_spec(spec)
        pending = asyncio.create_task(super().run_spec(spec))
        try:
            try:
                await workflow.wait_condition(pending.done, timeout=timedelta(seconds=remaining))
            except asyncio.TimeoutError:
                self.cancel_reason = self.cancel_reason or 'Original budget work cutoff reached'
                if not pending.done() and self.phase != 'FENCING':
                    pending.cancel()
            outcome = await pending
            if outcome['status'] == 'REVIEW_READY' and self.remaining() <= 0:
                return await self.stop('Original budget work cutoff reached')
            return outcome
        except asyncio.CancelledError:
            if not pending.done() and self.phase != 'FENCING':
                pending.cancel()
            return await asyncio.shield(pending)
        finally:
            if not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)

    @workflow.run
    async def run(self, document: dict) -> dict:
        outcome = await self._run_document(document)
        instance = self.admission['budget']['instance']
        return {**outcome, 'budget': {'id': instance['id'], 'sha256': instance['sha256'],
            'deadline_at': instance['deadline_at'], 'utc_observed_at': workflow.now().isoformat(),
            'work_exhausted': self.remaining() <= 0,
            'utc_overrun_seconds': max(0, -self.remaining(cleanup=True))}}


class NativeSixStageAdapter(BudgetedAdapter):
    envelope_version = 10


@workflow.defn(name='ErgoraCompositionWorkflowV10')
class NativeSixStageWorkflow(BudgetedWorkflow):
    """Project the parent call onto the same task, run and candidate evidence."""

    envelope_version = 10

    @workflow.query
    def status(self) -> dict:
        result = super().status()
        if self.admission is not None:
            result['native_invocation'] = self.admission['composition']['native']
        return result

    @workflow.run
    async def run(self, document: dict) -> dict:
        outcome = await super().run(document)
        return {**outcome, 'native_invocation': self.admission['composition']['native']}
