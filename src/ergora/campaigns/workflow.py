"""Temporal runtime for the original record-only campaign and its deadline."""

import asyncio
from datetime import timedelta
import signal
import time

from temporalio import workflow
from temporalio.api.common.v1 import WorkflowExecution, WorkflowType
from temporalio.api.enums.v1 import ContinueAsNewInitiator, EventType, TimeoutType, UpdateWorkflowExecutionLifecycleStage
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.update.v1 import Input, Meta, Request, WaitPolicy
from temporalio.api.workflowservice.v1 import StartWorkflowExecutionRequest, UpdateWorkflowExecutionRequest
from temporalio.client import (
    Client, WorkflowContinuedAsNewError, WorkflowExecutionStatus, WorkflowFailureError, WorkflowQueryFailedError,
    WorkflowQueryRejectedError,
)
from temporalio.common import QueryRejectCondition, RetryPolicy, WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.converter import WorkflowSerializationContext
from temporalio.exceptions import ActivityError, ApplicationError, TimeoutError as ActivityTimeoutError
from temporalio.exceptions import TimeoutType as ActivityTimeoutType
from temporalio.service import RPCError, RPCStatusCode
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from ergora.campaigns.records import (
        ATTEMPT_MEMO, OPENING_MEMO, READBACK_ALREADY_ADMITTED, READBACK_CLEANUP_SECONDS,
        RECIPIENT_ACTIVITY, TRAINING_RESULT_SOURCE, WORKFLOW_TYPE,
        assignment_intent, assignment_task, check_receipt, checked_readback, fixed_task_state, has_pending_checks,
        identity, manual_wake_source,
        readback_activity, readback_grant, readback_id, readback_proof, readback_ready_tasks, readback_reference,
        readback_followup_activity, readback_followup_id, readback_followup_result, readback_result, readback_task,
        recipient_task, reobservation_task,
        tasks_by_id, training_readback_task,
        require_check_receipt, require_rollover_receipt, require_stop_receipt, restore_rollover, rollover_checkpoint,
        rollover_task, same_check_observation,
        safe_id, sha256, stop_intent, update_receipt, validate_check_command, validate_rollover_command,
        validate_stop_attempt, uuid_text, wake_intent,
    )


RPC_SECONDS = 10
RPC_TIMEOUT = timedelta(seconds=RPC_SECONDS)
STOP_UPDATE = 'ergora_campaign_stop'
CHECK_UPDATE = 'ergora_campaign_observe_check'
ROLLOVER_UPDATE = 'ergora_campaign_rollover'
UPDATE_COMPLETED = UpdateWorkflowExecutionLifecycleStage.UPDATE_WORKFLOW_EXECUTION_LIFECYCLE_STAGE_COMPLETED


def record_state(opening, run_id, phase):
    return {'phase': phase, 'opening_sha256': identity(opening), 'workflow_id': opening['workflow_id'],
            'run_id': run_id, 'expires_at': opening['plan']['limits']['expires_at']}


@workflow.defn(name=WORKFLOW_TYPE)
class Campaign:
    @workflow.init
    def __init__(self, opening: dict, checkpoint: dict | None = None):
        self.opening = opening
        self.stop_decision = None
        self.rollover_command = None
        self.expiry_timer = None
        self.check_receipts = {}
        self.check_waits = {}
        self.ready_source = None
        self.readback = {'status': 'not_armed'} if readback_task(opening) is not None else None
        info = workflow.info()
        start_sha = workflow.memo_value(ATTEMPT_MEMO, default=None)
        if (info.workflow_id != opening['workflow_id'] or info.namespace != opening['scheduler']['namespace']
                or workflow.memo_value(OPENING_MEMO, default=None) != identity(opening) or not sha256(start_sha)):
            raise ApplicationError('Campaign worker input does not match the original start', non_retryable=True)
        if info.run_id == info.first_execution_run_id:
            if checkpoint is not None:
                raise ApplicationError('Campaign original first Run cannot restore a rollover checkpoint', non_retryable=True)
        else:
            if info.continued_run_id != info.first_execution_run_id:
                raise ApplicationError('Campaign successor does not continue its original first Run', non_retryable=True)
            try:
                self.check_waits = restore_rollover(opening, start_sha, info.first_execution_run_id, checkpoint)
            except (ValueError, TypeError, KeyError) as error:
                raise ApplicationError(str(error), non_retryable=True) from error

    @workflow.run
    async def run(self, opening: dict, checkpoint: dict | None = None) -> dict:
        task = readback_task(opening)
        readback = asyncio.create_task(self._one_readback(task)) if task is not None else None
        try:
            remaining = opening['plan']['limits']['expires_at'] - workflow.time()
            if remaining > 0 and self.stop_decision is None and self.rollover_command is None:
                self.expiry_timer = asyncio.create_task(workflow.sleep(remaining))
                try:
                    await self.expiry_timer
                except asyncio.CancelledError:
                    if self.stop_decision is None and self.rollover_command is None:
                        raise
        finally:
            if readback is not None:
                readback.cancel()
                await asyncio.gather(readback, return_exceptions=True)
                if self.readback['status'] in ('armed', 'scheduled'):
                    self._readback_unknown('campaign_closed')
        if self.rollover_command is not None:
            await workflow.wait_condition(workflow.all_handlers_finished)
            task = rollover_task(opening)
            start_sha = workflow.memo_value(ATTEMPT_MEMO)
            handoff = rollover_checkpoint(opening, start_sha, workflow.info().run_id,
                                          self.check_waits[task['task_id']], self.rollover_command)
            workflow.continue_as_new(args=[opening, handoff],
                                     memo={OPENING_MEMO: identity(opening), ATTEMPT_MEMO: start_sha})
        if self.stop_decision is not None:
            await workflow.wait_condition(workflow.all_handlers_finished)
            return {**self._state('stopped'), 'stop_receipt_sha256': identity(self.stop_decision)}
        return self._state('expired')

    def _readback_unknown(self, reason):
        self.readback = {'status': 'unknown', 'reason': reason, 'activity_id': self.readback['activity_id'],
                         **readback_reference(self.readback)}

    async def _one_readback(self, task):
        task_id = task['task_id']
        training = training_readback_task(task)
        if not training:
            await workflow.wait_condition(lambda: task_id in self.check_waits or task_id in self.check_receipts)
        shared = task.get('wake_on_observe') is True
        if (self.stop_decision is not None or (not training and task_id not in self.check_waits)
                or (task_id in self.check_receipts and not shared)):
            return
        grant = readback_grant(self.opening, workflow.info().run_id, task, self.check_waits.get(task_id))
        activity_id = readback_id(grant)
        self.readback = {'status': 'armed', 'activity_id': activity_id, **readback_reference(grant)}
        assigned = None
        if assignment_task(self.opening) is not None:
            intent = assignment_intent(self.opening, workflow.info().run_id, self.check_waits[task_id])
            assigned = asyncio.create_task(self._deliver_recipient(intent))
        try:
            await self._time_readback(task, grant, activity_id, shared, assigned)
            if assigned is not None:
                await assigned
        finally:
            if assigned is not None and not assigned.done():
                assigned.cancel()
                await asyncio.gather(assigned, return_exceptions=True)

    async def _time_readback(self, task, grant, activity_id, shared, assigned):
        delay = grant['due_at'] - workflow.time()
        if delay > 0:
            await workflow.sleep(delay)
        remaining = grant['deadline_at'] - workflow.time()
        if shared:
            await self._run_shared_intake(task, grant, activity_id, remaining, assigned)
            return
        if self.stop_decision is not None:
            self._readback_unknown('campaign_closed')
        elif task['task_id'] in self.check_receipts:
            self._readback_unknown('task_already_observed')
        elif remaining <= READBACK_CLEANUP_SECONDS:
            self._readback_unknown('read_window_expired')
        else:
            await self._observe_readback(task, grant, activity_id, remaining)
        if 'recipient' in task and self.readback['status'] == 'available':
            await self._deliver_result(task, self.readback, assigned)

    async def _run_shared_intake(self, task, grant, activity_id, remaining, assigned):
        if self.stop_decision is not None:
            self._readback_unknown('campaign_closed')
            return
        read = None
        if self.ready_source is not None:
            self._readback_unknown('task_already_observed')
        elif remaining > READBACK_CLEANUP_SECONDS:
            read = asyncio.create_task(self._observe_readback(task, grant, activity_id, remaining))
        else:
            self._readback_unknown('read_window_expired')
        try:
            if self.ready_source is None and remaining > 0:
                try:
                    await workflow.wait_condition(lambda: self.ready_source is not None, timeout=remaining)
                except asyncio.TimeoutError:
                    if self.readback['status'] == 'scheduled':
                        self._readback_unknown('read_window_expired')
                    return
            if self.ready_source is not None and self.stop_decision is None and workflow.time() < grant['deadline_at']:
                await self._deliver_result(task, self.ready_source, assigned)
            if read is not None:
                await read
        finally:
            if read is not None and not read.done():
                read.cancel()
                await asyncio.gather(read, return_exceptions=True)

    async def _observe_readback(self, task, grant, activity_id, remaining):
        self.readback['status'] = 'scheduled'
        recovery = {}
        result_activity_id = activity_id
        try:
            result = await workflow.execute_activity(readback_activity(task), grant, activity_id=activity_id,
                schedule_to_close_timeout=timedelta(seconds=remaining), start_to_close_timeout=timedelta(seconds=remaining),
                heartbeat_timeout=timedelta(seconds=min(2, remaining)), retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL, result_type=dict)
        except ActivityError as error:
            cause = error.cause
            remaining = grant['deadline_at'] - workflow.time()
            recovery_activity = readback_followup_activity(task)
            reobservation = reobservation_task(task)
            if (recovery_activity is None or self.stop_decision is not None
                    or not isinstance(cause, ActivityTimeoutError) or cause.type != ActivityTimeoutType.HEARTBEAT
                    or reobservation and (error.activity_id != activity_id or error.activity_type != readback_activity(task)
                                         or not 0 < error.scheduled_event_id < error.started_event_id)
                    or remaining <= READBACK_CLEANUP_SECONDS):
                self._readback_unknown('original_read_unavailable')
                return
            try:
                followup_options = {'heartbeat_timeout': timedelta(seconds=min(2, remaining))} if reobservation else {}
                reply = await workflow.execute_activity(recovery_activity, grant, activity_id=readback_followup_id(task, grant),
                    schedule_to_close_timeout=timedelta(seconds=remaining),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                    cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL, result_type=dict, **followup_options)
                recovery, result, result_activity_id = readback_followup_result(task, grant, reply)
            except (ActivityError, ValueError):
                self._readback_unknown('original_read_unavailable')
                return
        if self.stop_decision is not None:
            self._readback_unknown('campaign_closed')
            return
        if workflow.time() >= grant['deadline_at']:
            self._readback_unknown('read_window_expired')
            return
        if task['task_id'] in self.check_receipts and task.get('wake_on_observe') is not True:
            self._readback_unknown('task_already_observed')
            return
        try:
            evidence, job = readback_result(self.opening, task, result_activity_id, result)
        except (KeyError, TypeError, ValueError):
            self._readback_unknown('original_read_unavailable')
            return
        if job['status'] != 'succeeded':
            self._readback_unknown('original_still_pending')
            return
        self.readback = {**self.readback, 'status': 'available', **readback_proof(evidence, job, result), **recovery}
        if task.get('wake_on_observe') is True:
            if self.ready_source is None:
                self.ready_source = self.readback
            elif not same_check_observation(self.ready_source, self.readback):
                self._readback_unknown('contradictory_evidence')

    async def _deliver_result(self, task, source, assigned):
        if assigned is not None:
            await assigned
        await self._deliver_recipient(wake_intent(self.opening, workflow.info().run_id, task, source))

    async def _deliver_recipient(self, intent):
        allowance = intent['expires_at'] - workflow.time()
        if allowance > 0 and self.stop_decision is None:
            try:
                await workflow.execute_activity(RECIPIENT_ACTIVITY, intent, activity_id=intent['wake_id'],
                    schedule_to_close_timeout=timedelta(seconds=allowance),
                    start_to_close_timeout=timedelta(seconds=allowance),
                    heartbeat_timeout=timedelta(seconds=min(3, allowance)), retry_policy=RetryPolicy(maximum_attempts=1),
                    cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL, result_type=dict)
            except ActivityError:
                # The original native attempt, if published, is observed independently and never replayed.
                pass

    def _state(self, phase):
        result = record_state(self.opening, workflow.info().run_id, phase)
        if 'tasks' in self.opening['plan']:
            result['check_receipts'] = self.check_receipts.copy()
        if has_pending_checks(self.opening):
            result['check_waits'] = self.check_waits.copy()
        if self.readback is not None:
            result['timer_readback'] = self.readback.copy()
        return result

    @workflow.update(name=CHECK_UPDATE)
    def observe_check(self, command: dict) -> dict:
        receipt = check_receipt(command)
        waiting = receipt['decision'] == 'waiting_job'
        receipts = self.check_waits if waiting else self.check_receipts
        previous = receipts.get(receipt['task_id'])
        if previous is not None:
            if previous != receipt:
                raise ApplicationError('Campaign task already has different original evidence', non_retryable=True)
            return previous
        task = tasks_by_id(self.opening)[receipt['task_id']]
        if (self.stop_decision is not None or self.rollover_command is not None
                or workflow.time() >= self.opening['plan']['limits']['expires_at']):
            raise ApplicationError('Campaign no longer admits new task observations', non_retryable=True)
        automatic = readback_ready_tasks(readback_task(self.opening), self.readback or {})
        if not set(task['depends_on']) <= self.check_receipts.keys() | automatic:
            raise ApplicationError('Campaign task dependencies lack an original observation', non_retryable=True)
        if waiting and receipt['task_id'] in self.check_receipts:
            raise ApplicationError('Campaign task already has original terminal evidence', non_retryable=True)
        if not waiting and 'job' in receipt:
            prior_wait = self.check_waits.get(receipt['task_id'])
            if receipt['job'].get('waiting_receipt_sha256') != (identity(prior_wait) if prior_wait is not None else None):
                raise ApplicationError('Campaign terminal check differs from its original waiting receipt', non_retryable=True)
            if receipt['task_id'] in automatic:
                if not same_check_observation(
                        self.readback, {'observation_sha256': receipt['observation_sha256'], **receipt['job']}):
                    raise ApplicationError('Campaign original fixed-check observations contradict each other', non_retryable=True)
                raise ApplicationError('Campaign already admitted its original guarded result',
                                       type=READBACK_ALREADY_ADMITTED, non_retryable=True)
            if (task.get('wake_on_observe') is True and prior_wait is not None
                    and workflow.time() < task['readback']['deadline_at']):
                self.ready_source = manual_wake_source(task, prior_wait, receipt)
        receipts[receipt['task_id']] = receipt
        return receipt

    @observe_check.validator
    def validate_observe_check(self, command: dict):
        try:
            validate_check_command(self.opening, workflow.memo_value(ATTEMPT_MEMO), workflow.info().run_id, command)
            if workflow.current_update_info().id != command['attempt']['update_id']:
                raise ValueError('Campaign check does not bind its original Update ID')
        except ValueError as error:
            raise ApplicationError(str(error), non_retryable=True) from error

    @workflow.update(name=ROLLOVER_UPDATE)
    def rollover(self, command: dict) -> dict:
        intent, attempt = command['intent'], command['attempt']
        if self.rollover_command is None:
            self.rollover_command = command
            if self.expiry_timer is not None:
                self.expiry_timer.cancel()
        return update_receipt(intent, attempt, 'committed')

    @rollover.validator
    def validate_rollover(self, command: dict):
        info = workflow.info()
        try:
            validate_rollover_command(self.opening, workflow.memo_value(ATTEMPT_MEMO), info.run_id, command)
            if (info.run_id != info.first_execution_run_id or self.stop_decision is not None
                    or workflow.time() >= self.opening['plan']['limits']['expires_at']
                    or self.check_receipts or workflow.current_update_info().id != command['attempt']['update_id']
                    or (self.rollover_command is not None and self.rollover_command != command)):
                raise ValueError('Campaign rollover no longer admits a new decision')
            task = rollover_task(self.opening)
            wait = self.check_waits.get(task['task_id'])
            if wait is None or identity(wait) != command['intent']['waiting_receipt_sha256']:
                raise ValueError('Campaign rollover requires its exact original waiting receipt')
        except ValueError as error:
            raise ApplicationError(str(error), non_retryable=True) from error

    @workflow.update(name=STOP_UPDATE)
    def stop(self, command: dict) -> dict:
        intent, attempt = command['intent'], command['attempt']
        if self.stop_decision is not None:
            if self.stop_decision['attempt_sha256'] != identity(attempt):
                raise ApplicationError('Campaign already has a different stop decision', non_retryable=True)
            return self.stop_decision
        if workflow.time() >= self.opening['plan']['limits']['expires_at']:
            return update_receipt(intent, attempt, 'expired')
        self.stop_decision = update_receipt(intent, attempt, 'accepted')
        if self.expiry_timer is not None:
            self.expiry_timer.cancel()
        return self.stop_decision

    @stop.validator
    def validate_stop(self, command: dict):
        info = workflow.info()
        expected = stop_intent(self.opening, workflow.memo_value(ATTEMPT_MEMO), info.run_id)
        try:
            if self.rollover_command is not None:
                raise ValueError('Campaign first Run is closing for its original rollover')
            if (not isinstance(command, dict) or command.keys() != {'intent', 'attempt'}
                    or identity(command['intent']) != identity(expected) or not isinstance(command['attempt'], dict)):
                raise ValueError('Campaign stop does not bind its original opening and first Run')
            validate_stop_attempt(expected, command['attempt'])
            if (workflow.current_update_info().id != command['attempt']['update_id']
                    or (self.stop_decision is not None
                        and self.stop_decision['attempt_sha256'] != identity(command['attempt']))):
                raise ValueError('Campaign stop does not bind its original Update attempt')
        except ValueError as error:
            raise ApplicationError(str(error), non_retryable=True) from error

    @workflow.query
    def state(self) -> dict:
        result = self._state('waiting_for_expiry')
        if 'tasks' in self.opening['plan']:
            result['check_admission_open'] = self.stop_decision is None and self.rollover_command is None
        return result

    @workflow.query(name='ergora_campaign_stop_capability')
    def stop_capability(self) -> dict:
        return record_state(self.opening, workflow.info().run_id, 'stop_supported')

    @workflow.query(name='ergora_campaign_rollover_capability')
    def rollover_capability(self) -> dict:
        return record_state(self.opening, workflow.info().run_id, 'rollover_supported')


async def connect(opening):
    scheduler = opening['scheduler']
    try:
        return await Client.connect(scheduler['address'], namespace=scheduler['namespace'])
    except (OSError, RuntimeError) as error:
        raise ConnectionError('Original Temporal connection failed') from error


def memo(opening, attempt):
    return {OPENING_MEMO: identity(opening), ATTEMPT_MEMO: identity(attempt)}


async def start(client, opening, attempt):
    namespace = opening['scheduler']['namespace']
    if client.namespace != namespace:
        raise ValueError('Temporal client does not use the original campaign namespace')
    request = StartWorkflowExecutionRequest(
        namespace=namespace, workflow_id=opening['workflow_id'], workflow_type=WorkflowType(name=WORKFLOW_TYPE),
        task_queue=TaskQueue(name=opening['task_queue']), identity=client.identity,
        request_id=attempt['attempt_id'], workflow_id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
        workflow_id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
    )
    converter = client.data_converter.with_context(WorkflowSerializationContext(namespace, request.workflow_id))
    request.input.payloads.extend(await converter.encode([opening]))
    for key, digest in memo(opening, attempt).items():
        request.memo.fields[key].CopyFrom((await converter.encode([digest]))[0])
    # Client.start_workflow always enables SDK transport retries. The saved
    # attempt permits one Start send, then original-History reconciliation.
    response = await client.workflow_service.start_workflow_execution(request, retry=False, timeout=RPC_TIMEOUT)
    if response.started:
        return response.first_execution_run_id or response.run_id
    return None


async def _supports_update(handle, opening, query, phase):
    try:
        async with asyncio.timeout(2):
            observed = await handle.query(query, reject_condition=QueryRejectCondition.NOT_OPEN,
                                          rpc_timeout=timedelta(seconds=2))
    except (RPCError, TimeoutError, WorkflowQueryFailedError, WorkflowQueryRejectedError):
        return False
    require_state(observed, opening, handle.run_id, phase)
    return True


async def stop_supported(handle, opening):
    return await _supports_update(handle, opening, Campaign.stop_capability, 'stop_supported')


async def rollover_supported(handle, opening):
    return await _supports_update(handle, opening, Campaign.rollover_capability, 'rollover_supported')


async def send_stop(client, command, *, first_run_id=None):
    return await _send_update(client, command, STOP_UPDATE, require_stop_receipt, first_run_id=first_run_id)


async def send_check(client, command, *, expires_at, first_run_id=None):
    return await _send_update(client, command, CHECK_UPDATE, require_check_receipt, expires_at=expires_at,
                              first_run_id=first_run_id)


async def send_rollover(client, command, *, expires_at):
    return await _send_update(client, command, ROLLOVER_UPDATE, require_rollover_receipt, expires_at=expires_at)


async def _send_update(client, command, update_name, require_receipt, *, expires_at=None, first_run_id=None):
    intent, attempt = command['intent'], command['attempt']
    run = WorkflowExecution(workflow_id=intent['workflow_id'], run_id=intent['run_id'])
    converter = client.data_converter.with_context(WorkflowSerializationContext(client.namespace, run.workflow_id))
    request = UpdateWorkflowExecutionRequest(
        namespace=client.namespace, workflow_execution=run, first_execution_run_id=first_run_id or run.run_id,
        wait_policy=WaitPolicy(lifecycle_stage=UPDATE_COMPLETED),
        request=Request(meta=Meta(update_id=attempt['update_id'], identity=client.identity),
                        input=Input(name=update_name)),
    )
    request.request.input.args.payloads.extend(await converter.encode([command]))
    timeout = RPC_TIMEOUT
    if expires_at is not None:
        remaining = expires_at - time.time()
        if remaining <= 0:
            return None
        timeout = timedelta(seconds=min(RPC_SECONDS, remaining))
        if not timeout:
            return None
    response = await client.workflow_service.update_workflow_execution(request, retry=False, timeout=timeout)
    if (response.stage != UPDATE_COMPLETED or response.update_ref.workflow_execution != run
            or response.update_ref.update_id != attempt['update_id'] or not response.outcome.HasField('success')):
        return None
    try:
        return await _update_outcome(converter, command, response.outcome, require_receipt)
    except (ValueError, RuntimeError):
        # A mismatched acknowledgement cannot witness a decision. Read the
        # original History with the same attempt ID instead.
        return None


async def _update_outcome(converter, command, outcome, require_receipt):
    if not outcome.HasField('success'):
        return None
    value = await converter.decode(outcome.success.payloads)
    if len(value) != 1:
        raise ValueError('Original campaign Update has an invalid result')
    return require_receipt(command['intent'], command['attempt'], value[0])


async def read_stop(client, handle, command):
    return await _read_update(client, handle, command, STOP_UPDATE, require_stop_receipt)


async def read_check(client, handle, command):
    return await _read_update(client, handle, command, CHECK_UPDATE, require_check_receipt)


class FollowupHistoryConflict(ValueError):
    """A contradictory follow-up after verification of the original terminal."""

    def __init__(self, error, original_terminal):
        super().__init__(str(error))
        self.verified_original_terminal = original_terminal


class WakeHistoryConflict(ValueError):
    """A contradictory wake after verification of its independent read evidence."""

    def __init__(self, error, verified_before_wake, assignment=None):
        super().__init__(str(error))
        self.verified_before_wake = verified_before_wake
        self.assignment = assignment


async def read_task_history(client, handle, opening, commands):
    """Read saved task Updates and the opted-in Activity from one pinned History."""
    entries = {}
    for command in commands:
        entry = _update_entry(handle, command)
        update_id = command['attempt']['update_id']
        if update_id in entries:
            raise ValueError('Saved campaign task attempts share an original Update ID')
        entries[update_id] = entry
    task = readback_task(opening)
    timer_wait = next((command for command in commands if task is not None
                       and command['intent']['task_id'] == task['task_id']
                       and command['intent']['operation'] == 'wait_check'), None)
    training = training_readback_task(task)
    full_result = training and task['source']['kind'] == TRAINING_RESULT_SOURCE
    waiting = check_receipt(timer_wait) if timer_wait is not None else None
    wait_entry = entries[timer_wait['attempt']['update_id']] if timer_wait is not None else None
    grant = readback_grant(opening, handle.run_id, task, waiting) if training or waiting is not None else None
    activity_id = readback_id(grant) if grant is not None else None
    recovery_id = readback_followup_id(task, grant) if readback_followup_activity(task) is not None else None
    recovery_events = []
    recovery_ids = set()
    recovery_cancel_requests = []
    activity_events = []
    cancel_requests = []
    schedule_ids = set()
    wake_events = []
    assignment_events = []
    recipient_schedules = {}
    recipient = recipient_task(opening)
    assigned = assignment_task(opening) is not None
    converter = client.data_converter.with_context(WorkflowSerializationContext(client.namespace, handle.id))
    async for event in handle.fetch_history_events(rpc_timeout=RPC_TIMEOUT):
        await _read_update_event(converter, event, entries, CHECK_UPDATE, require_check_receipt)
        if recipient is not None:
            _collect_recipient_event(event, assigned, wake_events, assignment_events, recipient_schedules)
        if recovery_id is not None and len(recovery_events) < 4:
            if (event.HasField('activity_task_scheduled_event_attributes')
                    and event.activity_task_scheduled_event_attributes.activity_id == recovery_id):
                recovery_ids.add(event.event_id)
                recovery_events.append(event)
            else:
                for kind in ('started', 'completed', 'timed_out', 'failed', 'canceled'):
                    field = f'activity_task_{kind}_event_attributes'
                    if event.HasField(field) and getattr(event, field).scheduled_event_id in recovery_ids:
                        recovery_events.append(event)
                        break
        if full_result and event.HasField('activity_task_cancel_requested_event_attributes'):
            cancelled_schedule_id = event.activity_task_cancel_requested_event_attributes.scheduled_event_id
            if cancelled_schedule_id in recovery_ids and len(recovery_cancel_requests) < 2:
                recovery_cancel_requests.append(event)
            if cancelled_schedule_id in schedule_ids:
                if len(cancel_requests) < 2:
                    cancel_requests.append(event)
                continue
        # Keep one original Activity and a sentinel event to detect duplicates.
        if activity_id is None or len(activity_events) == 4:
            continue
        if event.HasField('activity_task_scheduled_event_attributes'):
            if event.activity_task_scheduled_event_attributes.activity_id == activity_id:
                schedule_ids.add(event.event_id)
                activity_events.append(event)
        elif (event.HasField('activity_task_started_event_attributes')
              and event.activity_task_started_event_attributes.scheduled_event_id in schedule_ids
              or event.HasField('activity_task_completed_event_attributes')
              and event.activity_task_completed_event_attributes.scheduled_event_id in schedule_ids
              or (full_result or recovery_id is not None) and event.HasField('activity_task_timed_out_event_attributes')
              and event.activity_task_timed_out_event_attributes.scheduled_event_id in schedule_ids
              or full_result and event.HasField('activity_task_failed_event_attributes')
              and event.activity_task_failed_event_attributes.scheduled_event_id in schedule_ids
              or full_result and event.HasField('activity_task_canceled_event_attributes')
              and event.activity_task_canceled_event_attributes.scheduled_event_id in schedule_ids):
            activity_events.append(event)
    updates = {}
    for update_id, entry in entries.items():
        if entry.get('receipt') is not None or entry.get('failed'):
            updates[update_id] = {'accepted_event_id': entry['accepted_event_id'],
                                  'completed_event_id': entry['completed_event_id'],
                                  'receipt': entry['receipt'],
                                  'status': 'failed' if entry.get('failed') else 'verified'}
    completion = readback_terminal = followup_terminal = None
    if training or (wait_entry is not None and wait_entry.get('receipt') is not None):
        completion, readback_terminal = await _readback_history(
            converter, activity_events, opening, task, grant, activity_id, cancel_requests)
    if recovery_events:
        if completion is not None:
            raise ValueError('Campaign receipt recovery conflicts with an original Activity completion')
        try:
            completion, followup_terminal = await _readback_followup_history(
                converter, activity_events, recovery_events, opening, task, grant, activity_id,
                include_terminal=full_result, cancel_requests=recovery_cancel_requests)
        except ValueError as error:
            if readback_terminal is None:
                raise
            raise FollowupHistoryConflict(error, readback_terminal) from error
    for update_id, entry in entries.items():
        event = entry.get('completed_event')
        if event is None or not entry['failed']:
            continue
        failure = event.workflow_execution_update_completed_event_attributes.outcome.failure
        kind = failure.application_failure_info
        if kind.type != READBACK_ALREADY_ADMITTED or not kind.non_retryable:
            continue
        late = check_receipt(entry['command'])
        waiting = entries[timer_wait['attempt']['update_id']].get('receipt') if timer_wait is not None else None
        source = manual_wake_source(task, waiting, late) if task is not None else {}
        if (completion is None or completion['completed_event_id'] >= entry['completed_event_id']
                or not same_check_observation(completion, source)):
            raise ValueError('Campaign readback refusal lacks its earlier identical guarded result')
        updates[update_id]['reason'] = READBACK_ALREADY_ADMITTED
    assignment = None
    if assignment_events:
        try:
            if wait_entry is None or wait_entry.get('receipt') is None:
                raise ValueError('Campaign independent task History lacks its verified original waiting Update')
            intent = assignment_intent(opening, handle.run_id, wait_entry['receipt'])
            assignment = await _read_recipient_history(converter, assignment_events, opening, intent,
                                                       wait_entry['completed_event'])
            assignment.update(waiting_accepted_event_id=wait_entry['accepted_event_id'],
                              waiting_completed_event_id=wait_entry['completed_event_id'])
        except ValueError as error:
            assignment = {'status': 'contradictory', 'error': str(error)}
    wake = None
    if wake_events:
        try:
            scheduled = wake_events[0].activity_task_scheduled_event_attributes
            values = await converter.decode(scheduled.input.payloads)
            if len(values) != 1 or not isinstance(values[0], dict) or not isinstance(values[0].get('source'), dict):
                raise ValueError('Campaign recipient History has an invalid original source')
            claimed = values[0]['source']
            if claimed.get('kind') == 'manual_update':
                if timer_wait is None or not isinstance(claimed.get('update_id'), str):
                    raise ValueError('Campaign recipient History lacks its original wait and terminal Update')
                preceding = entries[timer_wait['attempt']['update_id']]
                terminal = entries.get(claimed['update_id'], {})
                source = manual_wake_source(recipient, preceding.get('receipt'), terminal.get('receipt'))
                ready = terminal['completed_event']
                if preceding['completed_event_id'] >= ready.event_id:
                    raise ValueError('Campaign recipient terminal Update preceded its original wait')
            else:
                if completion is None:
                    raise ValueError('Campaign recipient History lacks its original passing readback')
                # The original wake intent binds the receipt fields saved at dispatch.
                source = {'status': 'available', **{key: value for key, value in completion.items()
                          if key not in ('task_id', 'scheduled_event_id', 'completed_event_id', 'timing', 'recovery_history')}}
                recovery_history = completion.get('recovery_history')
                if recovery_history is None:
                    ready = next(event for event in activity_events if event.event_id == completion['completed_event_id'])
                else:
                    ready = next(event for event in recovery_events if event.event_id == recovery_history['completed_event_id'])
            intent = wake_intent(opening, handle.run_id, recipient, source)
            wake = await _read_recipient_history(converter, wake_events, opening, intent, ready)
            if claimed.get('kind') != 'manual_update':
                completion['recipient'] = wake
        except ValueError as error:
            raise WakeHistoryConflict(error, (updates, completion, readback_terminal, followup_terminal),
                                      assignment) from error
    return updates, completion, wake, readback_terminal, followup_terminal, assignment


def _collect_recipient_event(event, assigned, wake_events, assignment_events, schedules):
    if event.HasField('activity_task_scheduled_event_attributes'):
        scheduled = event.activity_task_scheduled_event_attributes
        if assigned and scheduled.activity_id.startswith('codex-assignment:'):
            events = assignment_events
        elif scheduled.activity_type.name == RECIPIENT_ACTIVITY:
            events = wake_events
        else:
            return
        if len(events) < 4:
            schedules[event.event_id] = events
            events.append(event)
        return
    for kind in ('started', 'completed', 'failed', 'timed_out', 'canceled'):
        field = f'activity_task_{kind}_event_attributes'
        if event.HasField(field):
            events = schedules.get(getattr(event, field).scheduled_event_id)
            if events is not None and len(events) < 4:
                events.append(event)
            return


def _history_timestamp_ns(event):
    if not event.HasField('event_time'):
        return None
    seconds, nanos = event.event_time.seconds, event.event_time.nanos
    # Protobuf Timestamp covers years 0001 through 9999 with nonnegative nanos.
    if not (-62_135_596_800 <= seconds <= 253_402_300_799 and 0 <= nanos < 1_000_000_000):
        return None
    return seconds * 1_000_000_000 + nanos


def _history_timing(events, pairs):
    observed = {}
    stamps = {}
    for name, event in events.items():
        stamp = _history_timestamp_ns(event)
        if stamp is None:
            continue
        stamps[name] = stamp
        seconds, nanos = divmod(stamp, 1_000_000_000)
        observed[name] = {'event_id': event.event_id, 'seconds': seconds, 'nanos': nanos}
    intervals = {}
    for before, after in pairs:
        start, end = stamps.get(before), stamps.get(after)
        intervals[f'{before}_to_{after}'] = (
            end - start if start is not None and end is not None and end >= start else None)
    return {'clock': 'temporal_history', 'events': observed, 'intervals_ns': intervals}


async def _read_recipient_history(converter, events, opening, intent, readback_completed):
    event = events[0]
    scheduled = event.activity_task_scheduled_event_attributes
    values = await converter.decode(scheduled.input.payloads)
    if (len(events) > 3 or event.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
            or not 0 < readback_completed.event_id < event.event_id
            or scheduled.activity_id != intent['wake_id'] or scheduled.activity_type.name != RECIPIENT_ACTIVITY
            or scheduled.task_queue.name != opening['task_queue'] or scheduled.retry_policy.maximum_attempts != 1
            or values != [intent]):
        raise ValueError('Campaign recipient History differs from the exact original wake intent')
    result = {'intent': intent, 'status': 'scheduled', 'scheduled_event_id': event.event_id}
    timing_events = {'ready': readback_completed, 'scheduled': event}
    start_id = None
    terminals = []
    for following in events[1:]:
        if following.HasField('activity_task_started_event_attributes'):
            started = following.activity_task_started_event_attributes
            if (start_id is not None or following.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED
                    or following.event_id <= event.event_id or started.scheduled_event_id != event.event_id
                    or started.attempt != 1):
                raise ValueError('Campaign recipient History has a different original attempt')
            start_id = following.event_id
            result.update(status='unknown', started_event_id=start_id)
            timing_events['worker_started'] = following
            continue
        if following.HasField('activity_task_completed_event_attributes'):
            done = following.activity_task_completed_event_attributes
            if (start_id is None or following.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED
                    or following.event_id <= start_id or done.scheduled_event_id != event.event_id
                    or done.started_event_id != start_id):
                raise ValueError('Campaign recipient completion lacks its original start')
            replies = await converter.decode(done.result.payloads)
            if (len(replies) != 1 or not isinstance(replies[0], dict)
                    or replies[0].get('status') not in ('observed', 'blocked', 'unknown')):
                raise ValueError('Campaign original recipient completion has an invalid outcome')
            result.update(status=replies[0]['status'], completed_event_id=following.event_id, outcome=replies[0])
        elif following.HasField('activity_task_scheduled_event_attributes'):
            raise ValueError('Campaign recipient History scheduled a second delivery')
        else:
            result['status'] = 'unknown'
        terminals.append((following, start_id))
    if len(terminals) == 1:
        terminal, original_start_id = terminals[0]
        if original_start_id == start_id and terminal.event_id > (start_id or event.event_id):
            for kind in ('completed', 'failed', 'timed_out', 'canceled'):
                field = f'activity_task_{kind}_event_attributes'
                if terminal.HasField(field):
                    attributes = getattr(terminal, field)
                    if (terminal.event_type == EventType.Value('EVENT_TYPE_ACTIVITY_TASK_' + kind.upper())
                            and attributes.scheduled_event_id == event.event_id
                            and attributes.started_event_id == (start_id or 0)
                            and (kind != 'failed' or start_id is not None)):
                        result['completed_event_id'] = terminal.event_id
                        if kind != 'completed':
                            result['terminal_status'] = 'cancelled' if kind == 'canceled' else kind
                        timing_events['delivery_terminal'] = terminal
                    break
    result['timing'] = _history_timing(timing_events, (
        ('ready', 'scheduled'), ('scheduled', 'worker_started'), ('worker_started', 'delivery_terminal')))
    return result


def _readback_terminal(task, grant, activity_id, ancestry, event, kind, attributes, cancel_requests):
    scheduled = ancestry['scheduled']
    started = ancestry.get('worker_started')
    scheduled_id, started_id = scheduled.event_id, started.event_id if started is not None else None
    if (scheduled.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
            or started is not None and started.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED
            or event.event_type != EventType.Value('EVENT_TYPE_ACTIVITY_TASK_' + kind.upper())):
        raise ValueError('Campaign readback History event type differs from its Activity attributes')
    if (scheduled_id <= 0 or event.event_id <= (started_id or scheduled_id)
            or attributes.started_event_id != (started_id or 0) or (kind == 'failed' and started_id is None)):
        raise ValueError('Campaign readback terminal event does not bind its original Activity attempt')
    result = {'status': 'cancelled' if kind == 'canceled' else kind, 'run_id': grant['run_id'],
              'task_id': task['task_id'], 'activity_id': activity_id, **readback_reference(grant),
              'scheduled_event_id': scheduled_id, 'started_event_id': started_id, 'terminal_event_id': event.event_id}
    if kind == 'failed' and attributes.failure.HasField('application_failure_info'):
        application = attributes.failure.application_failure_info
        result['cause'] = {'kind': 'application', 'non_retryable': application.non_retryable}
        if safe_id(application.type):
            result['cause']['type'] = application.type
    elif kind == 'timed_out':
        timeout = attributes.failure.timeout_failure_info.timeout_type
        if (started_id is None and timeout not in (TimeoutType.TIMEOUT_TYPE_SCHEDULE_TO_CLOSE,
                                                    TimeoutType.TIMEOUT_TYPE_SCHEDULE_TO_START)
                or started_id is not None and timeout == TimeoutType.TIMEOUT_TYPE_SCHEDULE_TO_START):
            raise ValueError('Campaign readback timeout contradicts its original Activity start')
        if timeout in (TimeoutType.TIMEOUT_TYPE_START_TO_CLOSE, TimeoutType.TIMEOUT_TYPE_SCHEDULE_TO_CLOSE,
                       TimeoutType.TIMEOUT_TYPE_SCHEDULE_TO_START, TimeoutType.TIMEOUT_TYPE_HEARTBEAT):
            result['cause'] = {'kind': 'timeout', 'type': TimeoutType.Name(timeout).removeprefix('TIMEOUT_TYPE_')}
    elif kind == 'canceled':
        if len(cancel_requests) != 1:
            raise ValueError('Campaign readback cancellation lacks one original Activity cancel request')
        cancel_requested, = cancel_requests
        if (cancel_requested.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_CANCEL_REQUESTED
                or not scheduled_id < cancel_requested.event_id < event.event_id
                or attributes.latest_cancel_requested_event_id != cancel_requested.event_id
                or cancel_requested.activity_task_cancel_requested_event_attributes.scheduled_event_id != scheduled_id):
            raise ValueError('Campaign readback cancellation lacks its original Activity cancel request')
        result['cancel_requested_event_id'] = cancel_requested.event_id
    return result


async def _readback_history(converter, events, opening, task, grant, activity_id, cancel_requests):
    scheduled_id = started_id = completed = None
    terminal = None
    full_result = task['source'].get('kind') == TRAINING_RESULT_SOURCE
    timing_events = {}
    for event in events:
        if event.HasField('activity_task_scheduled_event_attributes'):
            scheduled = event.activity_task_scheduled_event_attributes
            values = await converter.decode(scheduled.input.payloads)
            if (scheduled_id is not None or event.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
                    or event.event_id <= 0 or scheduled.activity_type.name != readback_activity(task)
                    or scheduled.task_queue.name != opening['task_queue'] or scheduled.retry_policy.maximum_attempts != 1
                    or identity(values) != identity([grant])):
                raise ValueError('Campaign readback Activity differs from its original grant')
            scheduled_id = event.event_id
            timing_events['scheduled'] = event
        elif event.HasField('activity_task_started_event_attributes'):
            started = event.activity_task_started_event_attributes
            if started.scheduled_event_id == scheduled_id:
                if (started_id is not None or started.attempt != 1
                        or event.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED
                        or event.event_id <= scheduled_id):
                    raise ValueError('Campaign readback differs from its original Activity attempt')
                started_id = event.event_id
                timing_events['worker_started'] = event
        elif event.HasField('activity_task_completed_event_attributes'):
            result_event = event.activity_task_completed_event_attributes
            if result_event.scheduled_event_id == scheduled_id:
                if (completed is not None or started_id is None
                        or event.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED
                        or event.event_id <= started_id or result_event.started_event_id != started_id):
                    raise ValueError('Campaign readback completion does not bind its original Activity attempt')
                completed = event
        elif full_result:
            for kind in ('failed', 'timed_out', 'canceled'):
                field = f'activity_task_{kind}_event_attributes'
                if event.HasField(field):
                    attributes = getattr(event, field)
                    if attributes.scheduled_event_id == scheduled_id:
                        if terminal is not None:
                            raise ValueError('Campaign readback History has multiple original terminal events')
                        terminal = _readback_terminal(
                            task, grant, activity_id, timing_events, event, kind, attributes, cancel_requests)
                    break
    if terminal is not None:
        if completed is not None or terminal['started_event_id'] != started_id:
            raise ValueError('Campaign readback History has conflicting original Activity events')
        return None, terminal
    if completed is None:
        return None, None
    completion_ns = _history_timestamp_ns(completed)
    if completion_ns is not None and completion_ns >= grant['deadline_at'] * 1_000_000_000:
        raise ValueError('Campaign readback completion reached its original cutoff')
    values = await converter.decode(completed.activity_task_completed_event_attributes.result.payloads)
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ValueError('Campaign original readback Activity has an invalid result')
    result = values[0]
    try:
        evidence, job = readback_result(opening, task, activity_id, result)
    except (KeyError, TypeError) as error:
        raise ValueError('Campaign original readback Activity has an invalid result') from error
    if job['status'] != 'succeeded':
        return None, None
    timing_events['completed'] = completed
    timing = _history_timing(timing_events, (('scheduled', 'worker_started'), ('worker_started', 'completed')))
    return {'task_id': task['task_id'], 'activity_id': activity_id, **readback_reference(grant),
            'scheduled_event_id': scheduled_id, 'completed_event_id': completed.event_id,
            **readback_proof(evidence, job, result), **({'timing': timing} if timing['events'] else {})}, None


async def _readback_followup_history(converter, original, events, opening, task, grant, activity_id, *,
                                     include_terminal, cancel_requests=()):
    if len(original) != 3 or not 1 <= len(events) <= 3:
        raise ValueError('Campaign receipt recovery requires one original timed-out Activity')
    original_schedule, original_start, timeout = original
    original_started = original_start.activity_task_started_event_attributes
    failed = timeout.activity_task_timed_out_event_attributes
    if (not original_schedule.HasField('activity_task_scheduled_event_attributes')
            or not original_start.HasField('activity_task_started_event_attributes')
            or not timeout.HasField('activity_task_timed_out_event_attributes')
            or original_schedule.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
            or original_start.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED
            or timeout.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_TIMED_OUT
            or not 0 < original_schedule.event_id < original_start.event_id < timeout.event_id
            or original_started.scheduled_event_id != original_schedule.event_id or original_started.attempt != 1
            or failed.scheduled_event_id != original_schedule.event_id or failed.started_event_id != original_start.event_id
            or failed.failure.timeout_failure_info.timeout_type != TimeoutType.TIMEOUT_TYPE_HEARTBEAT):
        raise ValueError('Campaign receipt recovery lacks an exact original heartbeat timeout')
    sequence, *subsequent = events
    scheduled = sequence.activity_task_scheduled_event_attributes
    if (not sequence.HasField('activity_task_scheduled_event_attributes')
            or sequence.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
            or sequence.event_id <= timeout.event_id or scheduled.activity_type.name != readback_followup_activity(task)
            or scheduled.task_queue.name != opening['task_queue'] or scheduled.retry_policy.maximum_attempts != 1
            or scheduled.activity_id != readback_followup_id(task, grant)
            or identity(await converter.decode(scheduled.input.payloads)) != identity([grant])):
        raise ValueError('Campaign receipt recovery differs from the authorized original read')
    if not include_terminal and (len(events) < 3 or not events[-1].HasField('activity_task_completed_event_attributes')):
        return None, None
    start = None
    if subsequent and subsequent[0].HasField('activity_task_started_event_attributes'):
        start = subsequent.pop(0)
        started = start.activity_task_started_event_attributes
        if (start.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED or start.event_id <= sequence.event_id
                or started.scheduled_event_id != sequence.event_id or started.attempt != 1):
            raise ValueError('Campaign receipt recovery completion differs from its original attempt or cutoff')
    if not subsequent:
        return None, None
    if len(subsequent) != 1:
        raise ValueError('Campaign follow-up History has conflicting original Activity events')
    finished, = subsequent
    if not finished.HasField('activity_task_completed_event_attributes'):
        for kind in ('failed', 'timed_out', 'canceled'):
            field = f'activity_task_{kind}_event_attributes'
            if finished.HasField(field):
                attrs = getattr(finished, field)
                if attrs.scheduled_event_id != sequence.event_id:
                    break
                ancestry = {'scheduled': sequence, 'worker_started': start}
                terminal = _readback_terminal(
                    task, grant, scheduled.activity_id, ancestry, finished, kind, attrs, cancel_requests)
                return None, {**terminal, 'activity_type': scheduled.activity_type.name,
                              'original_timeout_event_id': timeout.event_id}
        raise ValueError('Campaign follow-up History has conflicting original Activity events')
    terminal = finished.activity_task_completed_event_attributes
    completion_ns = _history_timestamp_ns(finished)
    if (start is None or finished.event_type != EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED
            or finished.event_id <= start.event_id
            or terminal.scheduled_event_id != sequence.event_id or terminal.started_event_id != start.event_id
            or completion_ns is None or completion_ns >= grant['deadline_at'] * 1_000_000_000):
        raise ValueError('Campaign receipt recovery completion differs from its original attempt or cutoff')
    replies = await converter.decode(terminal.result.payloads)
    if len(replies) != 1:
        raise ValueError('Campaign receipt recovery has an invalid original result')
    try:
        recovery, result, result_activity_id = readback_followup_result(task, grant, replies[0])
        evidence, job = readback_result(opening, task, result_activity_id, result)
    except (KeyError, TypeError) as error:
        raise ValueError('Campaign receipt recovery has an invalid original result') from error
    return {'task_id': task['task_id'], 'activity_id': activity_id, **readback_reference(grant),
            'scheduled_event_id': original_schedule.event_id, **readback_proof(evidence, job, result), **recovery,
            'recovery_history': {'original_timeout_event_id': timeout.event_id, 'scheduled_event_id': sequence.event_id,
                                 'started_event_id': start.event_id, 'completed_event_id': finished.event_id}}, None


def _update_entry(handle, command):
    intent = command['intent']
    if handle.id != intent['workflow_id'] or handle.run_id != intent['run_id']:
        raise ValueError('Campaign Update readback cannot follow another run')
    return {'command': command}


async def _read_update_event(converter, event, entries, update_name, require_receipt):
    if event.HasField('workflow_execution_update_accepted_event_attributes'):
        selected = event.workflow_execution_update_accepted_event_attributes
        entry = entries.get(selected.protocol_instance_id)
        if entry is not None:
            request = selected.accepted_request
            if (event.event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_ACCEPTED or event.event_id <= 0
                    or 'accepted_event_id' in entry or request.meta.update_id != selected.protocol_instance_id
                    or request.input.name != update_name
                    or identity(await converter.decode(request.input.args.payloads)) != identity([entry['command']])):
                raise ValueError('Campaign original History has a changed or duplicate Update')
            entry['accepted_event_id'] = event.event_id
    elif event.HasField('workflow_execution_update_completed_event_attributes'):
        completed = event.workflow_execution_update_completed_event_attributes
        entry = entries.get(completed.meta.update_id)
        if entry is not None:
            accepted_id = entry.get('accepted_event_id')
            if (event.event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_UPDATE_COMPLETED
                    or accepted_id is None or not 0 < accepted_id < event.event_id
                    or completed.accepted_event_id != accepted_id or 'completed_event_id' in entry):
                raise ValueError('Campaign completion does not bind its original accepted Update')
            entry['completed_event_id'] = event.event_id
            entry['completed_event'] = event
            entry['receipt'] = await _update_outcome(converter, entry['command'], completed.outcome, require_receipt)
            entry['failed'] = completed.outcome.HasField('failure')


async def _read_update(client, handle, command, update_name, require_receipt):
    """Read the exact accepted and completed Update pair in the pinned original History."""
    entry = _update_entry(handle, command)
    entries = {command['attempt']['update_id']: entry}
    converter = client.data_converter.with_context(WorkflowSerializationContext(client.namespace, handle.id))
    async for event in handle.fetch_history_events(rpc_timeout=RPC_TIMEOUT):
        await _read_update_event(converter, event, entries, update_name, require_receipt)
        if 'completed_event_id' in entry:
            return entry['receipt']
    return None


async def original(client, opening, attempt, run_id):
    """Verify the first start event on a pinned run, without following resets or successors."""
    if client.namespace != opening['scheduler']['namespace']:
        raise ValueError('Temporal client does not use the original campaign namespace')
    handle = client.get_workflow_handle(opening['workflow_id'], run_id=run_id)
    description = await handle.describe(rpc_timeout=RPC_TIMEOUT)
    first = description.raw_description.workflow_execution_info.first_run_id
    if first != description.run_id or (run_id is not None and description.run_id != run_id):
        raise ValueError('Campaign observation did not select its original first run')
    run_id = description.run_id
    handle = client.get_workflow_handle(opening['workflow_id'], run_id=run_id)
    expected_memo = memo(opening, attempt)
    if description.id != opening['workflow_id'] or await description.memo() != expected_memo:
        raise ValueError('Campaign workflow ID or original dispatch memo differs')
    async for event in handle.fetch_history_events(page_size=1, rpc_timeout=RPC_TIMEOUT):
        if (event.event_id != 1 or event.event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED
                or not event.HasField('workflow_execution_started_event_attributes')):
            break
        started = event.workflow_execution_started_event_attributes
        if (started.workflow_type.name != WORKFLOW_TYPE or started.task_queue.name != opening['task_queue']
                or started.first_execution_run_id != run_id or started.original_execution_run_id != run_id
                or started.continued_execution_run_id or started.initiator != 0 or started.attempt != 1):
            raise ValueError('Campaign History type, queue or first start differs')
        if set(started.memo.fields) != set(expected_memo):
            raise ValueError('Campaign History does not have its original dispatch memo')
        for key, digest in expected_memo.items():
            if await client.data_converter.decode([started.memo.fields[key]], [str]) != [digest]:
                raise ValueError('Campaign History dispatch memo differs')
        values = await client.data_converter.decode(started.input.payloads)
        if len(values) != 1 or not isinstance(values[0], dict) or identity(values[0]) != identity(opening):
            raise ValueError('Campaign History complete plan input differs')
        return handle, description
    raise ValueError('Campaign original start History is missing its first event')


async def current(client, files, opening, attempt, first_run_id):
    handle, description = await original(client, opening, attempt, first_run_id)
    task = rollover_task(opening)
    if task is None or description.status != WorkflowExecutionStatus.CONTINUED_AS_NEW:
        return handle, description, None
    command = files.load_rollover(opening, attempt, handle.run_id)
    waiting = files.load_check(opening, attempt, handle.run_id, task, waiting=True)
    return await rollover_successor(client, handle, opening, attempt, waiting, command)


async def rollover_successor(client, first, opening, attempt, waiting_command, rollover_command):
    if waiting_command is None or rollover_command is None:
        raise ValueError('Campaign predecessor lacks its saved waiting or rollover command')
    start_sha = identity(attempt)
    validate_rollover_command(opening, start_sha, first.run_id, rollover_command)
    converter = client.data_converter.with_context(WorkflowSerializationContext(client.namespace, first.id))
    commands = {CHECK_UPDATE: (waiting_command, require_check_receipt),
                ROLLOVER_UPDATE: (rollover_command, require_rollover_receipt)}
    entries = {name: {command['attempt']['update_id']: _update_entry(first, command)}
               for name, (command, _) in commands.items()}
    last = None
    async for event in first.fetch_history_events(rpc_timeout=RPC_TIMEOUT):
        if event.HasField('workflow_execution_update_accepted_event_attributes'):
            accepted = event.workflow_execution_update_accepted_event_attributes
            name = accepted.accepted_request.input.name
            if name in (CHECK_UPDATE, STOP_UPDATE, ROLLOVER_UPDATE) and (
                    name not in entries or accepted.protocol_instance_id not in entries[name]):
                raise ValueError('Campaign predecessor contains another accepted task or control command')
        for name, (_, require_receipt) in commands.items():
            await _read_update_event(converter, event, entries[name], name, require_receipt)
        last = event
    if (last is None or last.event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_CONTINUED_AS_NEW
            or not last.HasField('workflow_execution_continued_as_new_event_attributes')):
        raise ValueError('Campaign predecessor lacks its native rollover close event')
    waiting, = entries[CHECK_UPDATE].values()
    committed, = entries[ROLLOVER_UPDATE].values()
    if (waiting.get('receipt') is None or committed.get('receipt') is None
            or not waiting['accepted_event_id'] < waiting['completed_event_id'] < committed['accepted_event_id']
            < committed['completed_event_id'] < last.event_id):
        raise ValueError('Campaign rollover lacks its exact ordered predecessor Update decisions')
    close = last.workflow_execution_continued_as_new_event_attributes
    successor_id = close.new_execution_run_id
    if (not uuid_text(successor_id) or successor_id == first.run_id or close.workflow_type.name != WORKFLOW_TYPE
            or close.task_queue.name != opening['task_queue']
            or close.initiator not in (ContinueAsNewInitiator.CONTINUE_AS_NEW_INITIATOR_UNSPECIFIED,
                                       ContinueAsNewInitiator.CONTINUE_AS_NEW_INITIATOR_WORKFLOW)):
        raise ValueError('Campaign predecessor rollover link differs from its original route')
    checkpoint = rollover_checkpoint(opening, start_sha, first.run_id, waiting['receipt'], rollover_command)
    restore_rollover(opening, start_sha, first.run_id, checkpoint)
    if identity(await converter.decode(close.input.payloads)) != identity([opening, checkpoint]):
        raise ValueError('Campaign predecessor rollover carried a different checkpoint')
    for key, digest in memo(opening, attempt).items():
        if key not in close.memo.fields or await converter.decode([close.memo.fields[key]]) != [digest]:
            raise ValueError('Campaign predecessor rollover dispatch memo differs')
    if set(close.memo.fields) != set(memo(opening, attempt)):
        raise ValueError('Campaign predecessor rollover has unexpected dispatch memo fields')
    current = client.get_workflow_handle(first.id, run_id=successor_id)
    description = await current.describe(rpc_timeout=RPC_TIMEOUT)
    if (description.run_id != successor_id or description.id != first.id
            or description.raw_description.workflow_execution_info.first_run_id != first.run_id
            or description.status == WorkflowExecutionStatus.CONTINUED_AS_NEW):
        raise ValueError('Campaign observation did not select its one original rollover successor')
    first_event = await anext(current.fetch_history_events(page_size=1, rpc_timeout=RPC_TIMEOUT), None)
    if (first_event is None or first_event.event_id != 1
            or first_event.event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED
            or not first_event.HasField('workflow_execution_started_event_attributes')):
        raise ValueError('Campaign rollover successor lacks its native start event')
    started = first_event.workflow_execution_started_event_attributes
    if (started.workflow_id != first.id or started.continued_execution_run_id != first.run_id
            or started.first_execution_run_id != first.run_id or started.original_execution_run_id != successor_id
            or started.attempt != 1 or started.initiator != ContinueAsNewInitiator.CONTINUE_AS_NEW_INITIATOR_WORKFLOW
            or started.workflow_type.name != WORKFLOW_TYPE or started.task_queue.name != opening['task_queue']
            or started.memo != close.memo or started.input != close.input):
        raise ValueError('Campaign rollover successor start differs from its verified predecessor')
    return current, description, checkpoint


def require_state(observed, opening, run_id, phase):
    if identity(observed) != identity(record_state(opening, run_id, phase)):
        raise ValueError('Campaign Workflow state differs from the original plan or run')
    return observed


async def runtime_status(handle, description, opening, stop=None, *, start_attempt_sha256=None, rollover=None):
    temporal_status = description.status
    if temporal_status == WorkflowExecutionStatus.RUNNING:
        try:
            async with asyncio.timeout(2):
                observed = await handle.query(Campaign.state, rpc_timeout=timedelta(seconds=2))
        except (RPCError, TimeoutError, WorkflowQueryFailedError, WorkflowQueryRejectedError):
            return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
        if 'tasks' in opening['plan'] and (not isinstance(observed, dict) or 'check_receipts' not in observed):
            return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
        expected = record_state(opening, description.run_id, 'waiting_for_expiry')
        return _observed_state(observed, expected, opening, start_attempt_sha256, temporal_status, stop=stop, rollover=rollover)
    if temporal_status == WorkflowExecutionStatus.COMPLETED:
        observed = await handle.result(follow_runs=False, rpc_timeout=RPC_TIMEOUT)
        if isinstance(observed, dict) and observed.get('phase') == 'stopped':
            if stop is None or stop['decision'] != 'accepted':
                return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
            expected = {**record_state(opening, description.run_id, 'stopped'), 'stop_receipt_sha256': identity(stop)}
        else:
            if stop is not None and stop['decision'] == 'accepted':
                raise ValueError('Campaign completion does not reflect its original stop decision')
            if description.close_time is None or description.close_time.timestamp() < opening['plan']['limits']['expires_at']:
                raise ValueError('Campaign Workflow completion preceded its original expiry')
            expected = record_state(opening, description.run_id, 'expired')
        return _observed_state(observed, expected, opening, start_attempt_sha256, temporal_status, rollover=rollover)
    return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}


def _observed_state(observed, expected, opening, start_attempt_sha256, temporal_status, *, stop=None, rollover=None):
    extra = {}
    if 'tasks' in opening['plan'] and isinstance(observed, dict) and 'check_receipts' in observed:
        observed = dict(observed)
        if has_pending_checks(opening) and not isinstance(observed.get('check_waits'), dict):
            return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
        waits = observed.pop('check_waits') if has_pending_checks(opening) else None
        waiting_run = None
        if rollover is not None:
            waiting = rollover['waiting_receipt']
            if waits != {waiting['task_id']: waiting}:
                raise ValueError('Campaign successor state differs from its verified predecessor wait')
            waiting_run = rollover['predecessor_run_id']
        selected = readback_task(opening)
        readback = (checked_readback(opening, expected['run_id'], waits, observed.pop('timer_readback', None))
                    if selected is not None else None)
        tasks = fixed_task_state(opening, start_attempt_sha256, expected['run_id'], observed.pop('check_receipts'),
                                 waits, waiting_run=waiting_run, readback=readback)
        active = False
        if temporal_status == WorkflowExecutionStatus.RUNNING:
            admitting = observed.pop('check_admission_open', None)
            if type(admitting) is not bool:
                return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
            active = (admitting and time.time() < expected['expires_at']
                      and (stop is None or stop['decision'] != 'accepted'))
        if selected is not None:
            tasks[selected['task_id']]['readback_observation'] = readback
        extra['tasks'] = {task_id: {**task, 'eligible': active and not training_readback_task(task) and task['status'] in ('ready', 'waiting_job')}
                          for task_id, task in tasks.items()}
    elif 'tasks' in opening['plan']:
        return {'temporal_status': temporal_status.name, 'workflow_state_status': 'unavailable'}
    if identity(observed) != identity(expected):
        raise ValueError('Campaign Workflow state differs from the original plan or run')
    return {'temporal_status': temporal_status.name, 'workflow_state_status': 'observed', 'workflow_state': observed, **extra}


async def run_worker(client, handle, opening, files, attempt, *, poller_identity=None, next_run=None):
    """Poll only the saved queue until the original run closes, or the foreground worker stops."""
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    previous = signal.getsignal(signal.SIGTERM)
    if previous is not None:
        signal.signal(signal.SIGTERM, lambda *_: loop.call_soon_threadsafe(stopped.set))

    async def wait_for_completion():
        # Only a bounded final poll is needed if the operator starts a worker after expiry.
        after_expiry = max(0, opening['plan']['limits']['expires_at'] - time.time())
        selected = handle
        async with asyncio.timeout(after_expiry + RPC_SECONDS):
            while True:
                try:
                    return await selected.result(follow_runs=False)
                except WorkflowContinuedAsNewError:
                    if next_run is None or selected.run_id != handle.run_id:
                        raise
                    selected = await next_run(selected)


    try:
        activities = []
        task = readback_task(opening)
        if task is not None:
            from ergora.campaigns.readback import CampaignReadback

            reader = CampaignReadback(files, opening, attempt, handle.run_id)
            activities.append(reader.activity_for(task))
            recovery = reader.recovery_activity_for(task)
            if recovery is not None:
                activities.append(recovery)
        if recipient_task(opening) is not None:
            from ergora.campaigns.recipient import CodexRecipient

            async def read_wake_history(commands, *, independent=False):
                async with asyncio.timeout(RPC_SECONDS):
                    history_client = await connect(opening)
                    original = history_client.get_workflow_handle(opening['workflow_id'], run_id=handle.run_id)
                    try:
                        _, _, wake, _, _, assignment = await read_task_history(history_client, original, opening, commands)
                    except WakeHistoryConflict as error:
                        if not independent:
                            raise
                        assignment = error.assignment
                return assignment if independent else wake

            activities.append(CodexRecipient(
                files, opening, attempt, handle.run_id, read_wake_history=read_wake_history).deliver)
        worker = Worker(client, task_queue=opening['task_queue'], workflows=[Campaign], activities=activities,
                        identity=poller_identity,
                        graceful_shutdown_timeout=timedelta(seconds=READBACK_CLEANUP_SECONDS if activities else 0))
        async with worker:
            closing = asyncio.create_task(wait_for_completion())
            stopping = asyncio.create_task(stopped.wait())
            try:
                await asyncio.wait((closing, stopping), return_when=asyncio.FIRST_COMPLETED)
                if closing.done():
                    try:
                        closing.result()
                    except (WorkflowFailureError, WorkflowContinuedAsNewError):
                        # The caller reads this pinned run again and reports its actual terminal status.
                        pass
                    return 'closed'
                return 'interrupted'
            finally:
                for task in (closing, stopping):
                    task.cancel()
                await asyncio.gather(closing, stopping, return_exceptions=True)
    finally:
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)
