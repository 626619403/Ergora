"""Explicit Temporal inputs; composition extends the frozen six-stage workflow."""

import asyncio
from contextlib import AsyncExitStack
from datetime import datetime, timedelta
import json
import hashlib

from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from dev_platform.activities import Activities
    from dev_platform.adapter import FileAdapter, ContractViolation, identifier, sha
    from dev_platform.adapter import read_raw
    from dev_platform.workflow import DevelopmentWorkflow, RETRY, StopWork
    from ergora.development import budget as reference_budget
    from ergora.development import envelopes as task_envelopes
    from ergora.development.runtime.review_opinions import review_observation
    from ergora.development.dags import preparation_stages
    from ergora.development import verification


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
        if len(content) > task_envelopes.context_limit(self.admission):
            raise StopWork("Complete composition stage context exceeds its wire byte limit; split the task")
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
                              allow_nan=False).encode('utf-8')) > task_envelopes.context_limit(self.admission):
                raise StopWork('Complete review DAG context exceeds its wire byte limit; split the task')
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

    def original_job(self, job: dict) -> dict:
        if 'context' not in job:
            try:
                relative = identifier(job['task_id']) + '/' + identifier(job['job_id']) + '.json'
                envelope = self.adapter.read_job(self.adapter.path('requests', relative))
                context = envelope['context']
                reference = {'task_id': context['task_id'], 'job_id': context['job_id'], 'job_sha256': sha(context)}
                expected = {'schema_version': 1, 'job_id': reference['job_id'],
                            'job_sha256': reference['job_sha256'], 'context': context}
                if job != reference or sha(envelope) != sha(expected):
                    raise ContractViolation('Poll reference differs from the trusted original job envelope')
                job = {**reference, 'context': context}
            except (ContractViolation, KeyError, TypeError, ValueError) as error:
                raise ApplicationError(str(error), type='ContractViolation', non_retryable=True) from error
        return job

    @activity.defn(name=task_envelopes.WORK_POLL)
    async def poll(self, job: dict) -> dict | None:
        return await super().poll(self.original_job(job))


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
                              allow_nan=False).encode('utf-8')) > task_envelopes.context_limit(self.admission):
                raise StopWork('Complete work stage context exceeds its wire byte limit; split the task')
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


class PreparationDAGAdapter(StageResultsAdapter):
    envelope_version = 12
    context_limit_bytes = task_envelopes.WIRE_LIMIT
    job_limit_bytes = task_envelopes.WIRE_LIMIT

    def validate_submission(self, context):
        super().validate_submission(context)
        try:
            reference_budget.require_remaining(context['admission']['budget']['instance'])
        except ValueError as error:
            raise ContractViolation(str(error)) from error


class PreparationDAGActivities(WorkDeliveryActivities):
    context_limit_bytes = task_envelopes.WIRE_LIMIT

    @activity.defn(name=task_envelopes.WORK_POLL)
    async def poll(self, job: dict) -> dict | None:
        job = self.original_job(job)
        context = job['context']
        preparation = context['admission']['composition']['preparation']
        member = preparation_stages(preparation).get(context['stage'])
        specialist = member is not None and context['stage'] != 'inventory' and (
            member in task_envelopes.preparation_dags(context['admission']['composition'])['inventory']['dag'].members)
        try:
            if specialist:
                async with asyncio.timeout(20):
                    result = await self.adapter.poll(job)
            else:
                result = await super().poll(job)
            if (context['stage'] == 'verify' and result is not None and result['state'] == 'SUCCEEDED'
                    and 'verification' in context['admission']):
                selected = [item for item in result['artifacts'] if item['name'] == 'check-results']
                if len(selected) != 1:
                    raise ContractViolation('Fixed verify requires its complete check-results artifact')
                item = selected[0]
                raw = read_raw(self.adapter.path('artifacts', item['path']), verification.ARTIFACT_BYTES)
                if hashlib.sha256(raw).hexdigest() != item['sha256']:
                    raise ContractViolation('Fixed check-results artifact changed')
                state = self.adapter.roots['receipts'].parent
                subject = verification.job_subject(context['admission'], job, state)
                verification.read_report(raw, context['admission']['verification'], subject,
                    process_root=state / 'processes')
            if member is None or result is None or result['state'] != 'SUCCEEDED':
                return result
            selected = preparation['members'][member]
            actor, names = result['actor'], {item['name'] for item in result['artifacts']}
            if (actor['id'] != selected['binding']['tool'] + ':' + selected['role']
                    or actor['role'] != selected['role'] or actor['kind'] != 'agent'
                    or actor['session_id'] in context['author_sessions']
                    or result['candidate_sha'] != context['expected_candidate_sha']
                    or any(check['status'] != 'pass' for check in result['checks'])):
                raise ContractViolation('Preparation result differs from its selected actor, independent session or candidate')
            if specialist:
                if 'inventory' not in names or names & {'behavior-baseline', 'preparation-sources'}:
                    raise ContractViolation('Preparation inspector specialist must provide only its declared inventory result')
            elif context['stage'] in ('inventory', 'plan') and 'preparation-sources' not in names:
                raise ContractViolation('Canonical preparation result is missing its trusted sources')
            return result
        except (ContractViolation, KeyError, TypeError, ValueError) as error:
            raise ApplicationError(str(error), type='ContractViolation', non_retryable=True) from error


@workflow.defn(name='ErgoraCompositionWorkflowV12')
class PreparationDAGWorkflow(StageResultsWorkflow):
    """Run frozen preparation DAGs inside the original budget and six stages."""

    envelope_version = 12

    def source_stage(self, path):
        stages = {member: stage for stage, member in
                  preparation_stages(self.admission['composition']['preparation']).items()}
        return stages[path] if path in stages else super().source_stage(path)

    def context(self, stage, expected_sha=None, unit=None, dependencies=None):
        context = super().context(stage, expected_sha, unit, dependencies)
        composition = self.admission['composition']
        member = preparation_stages(composition['preparation']).get(stage)
        if member is not None:
            group = next(group for group in task_envelopes.preparation_dags(composition).values()
                         if member in group['dag'].members)
            ports = group['dag'].input_ports(member)
            context['preparation_ports'] = {'schema_version': 1, 'kind': 'formal-preparation-ports',
                'member': member, 'ports': ports,
                'producers': {path: self.results[self.source_stage(path)] for path in ports['sources']}}
            if len(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                              allow_nan=False).encode('utf-8')) > task_envelopes.context_limit(self.admission):
                raise StopWork('Complete preparation DAG context exceeds its wire byte limit; split the task')
        return context

    async def stage(self, stage, expected_sha=None, unit=None, dependencies=None):
        if stage not in ('inventory', 'plan'):
            return await super().stage(stage, expected_sha, unit, dependencies)
        group = task_envelopes.preparation_dags(self.admission['composition'])[stage]
        dag = group['dag']
        scopes = {scope['path']: asyncio.Semaphore(scope['limit'])
                  for leaf in dag.members.values() for scope in leaf['concurrency_scopes']}
        remaining, completed, running = set(dag.members), set(), {}
        sessions = set(self.authors()[1])

        async def prepare(path):
            async with AsyncExitStack() as stack:
                for scope in reversed(dag.members[path]['concurrency_scopes']):
                    await stack.enter_async_context(scopes[scope['path']])
                # The coordinator owns the original bare stage. Call the parent
                # leaf operation directly so it cannot recursively start a group.
                return await super(PreparationDAGWorkflow, self).stage(
                    self.source_stage(path), expected_sha, unit, dependencies)

        try:
            while remaining or running:
                if self.cancel_reason:
                    raise StopWork(self.cancel_reason)
                for path in sorted(remaining):
                    if set(dag.predecessors[path]) <= completed:
                        running[path] = asyncio.create_task(prepare(path))
                        remaining.remove(path)
                await workflow.wait(running.values(), return_when=asyncio.FIRST_COMPLETED)
                for path in sorted(list(running)):
                    if running[path].done():
                        receipt = await running.pop(path)
                        if self.cancel_reason:
                            raise StopWork(self.cancel_reason)
                        session = receipt['actor']['session_id']
                        if session in sessions:
                            raise StopWork('Preparation instances require distinct original sessions')
                        sessions.add(session)
                        completed.add(path)
            return self.results[stage]
        finally:
            for task in running.values():
                task.cancel()
            if running:
                await asyncio.gather(*running.values(), return_exceptions=True)

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
            result['native_invocation'] = self.admission['composition']['native']
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
        if name == 'dev_poll':
            # Keep full material in the original immutable request, outside the
            # repeatedly recorded poll payload.
            value = {key: value[key] for key in ('task_id', 'job_id', 'job_sha256')}
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
        return {**outcome, 'native_invocation': self.admission['composition']['native'],
            'budget': {'id': instance['id'], 'sha256': instance['sha256'],
            'deadline_at': instance['deadline_at'], 'utc_observed_at': workflow.now().isoformat(),
            'work_exhausted': self.remaining() <= 0,
            'utc_overrun_seconds': max(0, -self.remaining(cleanup=True))}}
