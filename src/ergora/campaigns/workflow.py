"""Temporal runtime for the original record-only campaign and its deadline."""

import asyncio
from datetime import timedelta
import signal
import time

from temporalio import workflow
from temporalio.api.common.v1 import WorkflowExecution, WorkflowType
from temporalio.api.enums.v1 import ContinueAsNewInitiator, UpdateWorkflowExecutionLifecycleStage
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.update.v1 import Input, Meta, Request, WaitPolicy
from temporalio.api.workflowservice.v1 import StartWorkflowExecutionRequest, UpdateWorkflowExecutionRequest
from temporalio.client import (
    Client, WorkflowContinuedAsNewError, WorkflowExecutionStatus, WorkflowFailureError, WorkflowQueryFailedError,
    WorkflowQueryRejectedError,
)
from temporalio.common import QueryRejectCondition, RetryPolicy, WorkflowIDConflictPolicy, WorkflowIDReusePolicy
from temporalio.converter import WorkflowSerializationContext
from temporalio.exceptions import ActivityError, ApplicationError
from temporalio.service import RPCError, RPCStatusCode
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from ergora.campaigns.records import (
        ATTEMPT_MEMO, OPENING_MEMO, READBACK_ACTIVITY, READBACK_ALREADY_ADMITTED, READBACK_CLEANUP_SECONDS,
        RECIPIENT_ACTIVITY, WORKFLOW_TYPE,
        check_receipt, checked_readback, fixed_task_state, fixed_tasks, has_pending_checks, identity, manual_wake_source,
        readback_grant, readback_id, readback_ready_tasks, readback_result, readback_task, recipient_task,
        require_check_receipt, require_rollover_receipt, require_stop_receipt, restore_rollover, rollover_checkpoint,
        rollover_task, same_check_observation,
        sha256, stop_intent, update_receipt, validate_check_command, validate_rollover_command,
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
                         'waiting_receipt_sha256': self.readback['waiting_receipt_sha256']}

    async def _one_readback(self, task):
        task_id = task['task_id']
        await workflow.wait_condition(lambda: task_id in self.check_waits or task_id in self.check_receipts)
        shared = task.get('wake_on_observe') is True
        if self.stop_decision is not None or task_id not in self.check_waits or (task_id in self.check_receipts and not shared):
            return
        grant = readback_grant(self.opening, workflow.info().run_id, task, self.check_waits[task_id])
        activity_id = readback_id(grant)
        self.readback = {'status': 'armed', 'activity_id': activity_id,
                         'waiting_receipt_sha256': grant['waiting_receipt_sha256']}
        delay = grant['due_at'] - workflow.time()
        if delay > 0:
            await workflow.sleep(delay)
        remaining = grant['deadline_at'] - workflow.time()
        if shared:
            await self._run_shared_intake(task, grant, activity_id, remaining)
            return
        if self.stop_decision is not None:
            self._readback_unknown('campaign_closed')
        elif task_id in self.check_receipts:
            self._readback_unknown('task_already_observed')
        elif remaining <= READBACK_CLEANUP_SECONDS:
            self._readback_unknown('read_window_expired')
        else:
            await self._observe_readback(task, grant, activity_id, remaining)
        if 'recipient' in task and self.readback['status'] == 'available':
            await self._deliver_recipient(task, self.readback)

    async def _run_shared_intake(self, task, grant, activity_id, remaining):
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
                await self._deliver_recipient(task, self.ready_source)
            if read is not None:
                await read
        finally:
            if read is not None and not read.done():
                read.cancel()
                await asyncio.gather(read, return_exceptions=True)

    async def _observe_readback(self, task, grant, activity_id, remaining):
        self.readback['status'] = 'scheduled'
        try:
            result = await workflow.execute_activity(READBACK_ACTIVITY, grant, activity_id=activity_id,
                schedule_to_close_timeout=timedelta(seconds=remaining), start_to_close_timeout=timedelta(seconds=remaining),
                heartbeat_timeout=timedelta(seconds=min(2, remaining)), retry_policy=RetryPolicy(maximum_attempts=1),
                cancellation_type=workflow.ActivityCancellationType.TRY_CANCEL, result_type=dict)
        except ActivityError:
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
            evidence, job = readback_result(self.opening, task, activity_id, result)
        except (KeyError, TypeError, ValueError):
            self._readback_unknown('original_read_unavailable')
            return
        if job['status'] != 'succeeded':
            self._readback_unknown('original_still_pending')
            return
        self.readback = {**self.readback, 'status': 'available', 'observation_sha256': evidence,
                         'receipt_sha256': job['receipt_sha256'], 'fixed_results_sha256': job['fixed_results_sha256'],
                         'reader_cleanup_sha256': result['reader_cleanup_sha256']}
        if task.get('wake_on_observe') is True:
            if self.ready_source is None:
                self.ready_source = self.readback
            elif not same_check_observation(self.ready_source, self.readback):
                self._readback_unknown('contradictory_evidence')

    async def _deliver_recipient(self, task, source):
        intent = wake_intent(self.opening, workflow.info().run_id, task, source)
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
        task = fixed_tasks(self.opening)[receipt['task_id']]
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
    grant = readback_grant(opening, handle.run_id, task, check_receipt(timer_wait)) if timer_wait is not None else None
    activity_id = readback_id(grant) if grant is not None else None
    activity_events = []
    schedule_ids = set()
    wake_events = []
    wake_ids = set()
    recipient = recipient_task(opening)
    converter = client.data_converter.with_context(WorkflowSerializationContext(client.namespace, handle.id))
    async for event in handle.fetch_history_events(rpc_timeout=RPC_TIMEOUT):
        await _read_update_event(converter, event, entries, CHECK_UPDATE, require_check_receipt)
        if recipient is not None and len(wake_events) < 4:
            if (event.HasField('activity_task_scheduled_event_attributes')
                    and event.activity_task_scheduled_event_attributes.activity_type.name == RECIPIENT_ACTIVITY):
                wake_ids.add(event.event_id)
                wake_events.append(event)
            else:
                for kind in ('started', 'completed', 'failed', 'timed_out', 'canceled'):
                    field = f'activity_task_{kind}_event_attributes'
                    if event.HasField(field) and getattr(event, field).scheduled_event_id in wake_ids:
                        wake_events.append(event)
                        break
        # Keep at most one schedule, start and completion, plus one event to detect a duplicate.
        if activity_id is None or len(activity_events) == 4:
            continue
        if event.HasField('activity_task_scheduled_event_attributes'):
            if event.activity_task_scheduled_event_attributes.activity_id == activity_id:
                schedule_ids.add(event.event_id)
                activity_events.append(event)
        elif (event.HasField('activity_task_started_event_attributes')
              and event.activity_task_started_event_attributes.scheduled_event_id in schedule_ids
              or event.HasField('activity_task_completed_event_attributes')
              and event.activity_task_completed_event_attributes.scheduled_event_id in schedule_ids):
            activity_events.append(event)
    updates = {}
    for update_id, entry in entries.items():
        if entry.get('receipt') is not None or entry.get('failed'):
            updates[update_id] = {'accepted_event_id': entry['accepted_event_id'],
                                  'completed_event_id': entry['completed_event_id'],
                                  'receipt': entry['receipt'],
                                  'status': 'failed' if entry.get('failed') else 'verified'}
    completion = None
    if timer_wait is not None and entries[timer_wait['attempt']['update_id']].get('receipt') is not None:
        completion = await _readback_completion(converter, activity_events, opening, task, grant, activity_id)
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
    wake = None
    if wake_events:
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
            keys = ('activity_id', 'waiting_receipt_sha256', 'observation_sha256', 'receipt_sha256',
                    'fixed_results_sha256', 'reader_cleanup_sha256')
            source = {'status': 'available', **{key: completion[key] for key in keys}}
            ready = next(event for event in activity_events if event.event_id == completion['completed_event_id'])
        intent = wake_intent(opening, handle.run_id, recipient, source)
        wake = await _read_recipient_history(converter, wake_events, opening, intent, ready)
        if claimed.get('kind') != 'manual_update':
            completion['recipient'] = wake
    return updates, completion, wake


def _recipient_timing(events):
    observed = {}
    stamps = {}
    for name, event in events.items():
        if event.HasField('event_time') and 0 <= event.event_time.nanos < 1_000_000_000:
            seconds, nanos = event.event_time.seconds, event.event_time.nanos
            observed[name] = {'event_id': event.event_id, 'seconds': seconds, 'nanos': nanos}
            stamps[name] = seconds * 1_000_000_000 + nanos
    intervals = {}
    for before, after in (('ready', 'scheduled'), ('scheduled', 'worker_started'),
                          ('worker_started', 'delivery_terminal')):
        start, end = stamps.get(before), stamps.get(after)
        intervals[f'{before}_to_{after}'] = (
            end - start if start is not None and end is not None and end >= start else None)
    return {'clock': 'temporal_history', 'events': observed, 'intervals_ns': intervals}


async def _read_recipient_history(converter, events, opening, intent, readback_completed):
    event = events[0]
    scheduled = event.activity_task_scheduled_event_attributes
    values = await converter.decode(scheduled.input.payloads)
    if (len(events) > 3 or event.event_id <= readback_completed.event_id or scheduled.activity_id != intent['wake_id']
            or scheduled.task_queue.name != opening['task_queue'] or scheduled.retry_policy.maximum_attempts != 1
            or values != [intent]):
        raise ValueError('Campaign recipient History differs from the exact original wake intent')
    result = {'intent': intent, 'status': 'scheduled', 'scheduled_event_id': event.event_id}
    timing_events = {'ready': readback_completed, 'scheduled': event}
    start_id = None
    terminals = []
    for following in events[1:]:
        if following.HasField('activity_task_started_event_attributes'):
            if start_id is not None or following.activity_task_started_event_attributes.attempt != 1:
                raise ValueError('Campaign recipient History has a different original attempt')
            start_id = following.event_id
            result.update(status='unknown', started_event_id=start_id)
            timing_events['worker_started'] = following
            continue
        if following.HasField('activity_task_completed_event_attributes'):
            done = following.activity_task_completed_event_attributes
            if start_id is None or done.started_event_id != start_id:
                raise ValueError('Campaign recipient completion lacks its original start')
            replies = await converter.decode(done.result.payloads)
            if (len(replies) != 1 or not isinstance(replies[0], dict)
                    or replies[0].get('status') not in ('observed', 'blocked', 'unknown')):
                raise ValueError('Campaign original recipient completion has an invalid outcome')
            result.update(status=replies[0]['status'], completed_event_id=following.event_id, outcome=replies[0])
        elif following.HasField('activity_task_scheduled_event_attributes'):
            raise ValueError('Campaign recipient History scheduled a second delivery')
        else:
            result.update(status='unknown', completed_event_id=following.event_id)
        terminals.append((following, start_id))
    if len(terminals) == 1:
        terminal, original_start_id = terminals[0]
        if original_start_id == start_id and terminal.event_id > (start_id or event.event_id):
            for kind in ('completed', 'failed', 'timed_out', 'canceled'):
                field = f'activity_task_{kind}_event_attributes'
                if terminal.HasField(field) and getattr(terminal, field).started_event_id == (start_id or 0):
                    timing_events['delivery_terminal'] = terminal
                    break
    result['timing'] = _recipient_timing(timing_events)
    return result


async def _readback_completion(converter, events, opening, task, grant, activity_id):
    scheduled_id = started_id = completed = None
    for event in events:
        if event.HasField('activity_task_scheduled_event_attributes'):
            scheduled = event.activity_task_scheduled_event_attributes
            values = await converter.decode(scheduled.input.payloads)
            if (scheduled_id is not None or scheduled.activity_type.name != READBACK_ACTIVITY
                    or scheduled.task_queue.name != opening['task_queue'] or scheduled.retry_policy.maximum_attempts != 1
                    or identity(values) != identity([grant])):
                raise ValueError('Campaign readback Activity differs from its original grant')
            scheduled_id = event.event_id
        elif event.HasField('activity_task_started_event_attributes'):
            started = event.activity_task_started_event_attributes
            if started.scheduled_event_id == scheduled_id:
                if started_id is not None or started.attempt != 1:
                    raise ValueError('Campaign readback differs from its original Activity attempt')
                started_id = event.event_id
        elif event.HasField('activity_task_completed_event_attributes'):
            result_event = event.activity_task_completed_event_attributes
            if result_event.scheduled_event_id == scheduled_id:
                if completed is not None or started_id is None or result_event.started_event_id != started_id:
                    raise ValueError('Campaign readback completion does not bind its original Activity attempt')
                completed = event
    if completed is None:
        return None
    values = await converter.decode(completed.activity_task_completed_event_attributes.result.payloads)
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ValueError('Campaign original readback Activity has an invalid result')
    result = values[0]
    try:
        evidence, job = readback_result(opening, task, activity_id, result)
    except (KeyError, TypeError) as error:
        raise ValueError('Campaign original readback Activity has an invalid result') from error
    if job['status'] != 'succeeded':
        return None
    return {'task_id': task['task_id'], 'activity_id': activity_id,
            'waiting_receipt_sha256': grant['waiting_receipt_sha256'],
            'scheduled_event_id': scheduled_id, 'completed_event_id': completed.event_id,
            'receipt_sha256': job['receipt_sha256'], 'fixed_results_sha256': job['fixed_results_sha256'],
            'observation_sha256': evidence, 'reader_cleanup_sha256': result['reader_cleanup_sha256']}


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
            values = await converter.decode(request.input.args.payloads)
            if ('accepted_event_id' in entry or request.meta.update_id != selected.protocol_instance_id
                    or request.input.name != update_name or identity(values) != identity([entry['command']])):
                raise ValueError('Campaign original History has a changed or duplicate Update')
            entry['accepted_event_id'] = event.event_id
    elif event.HasField('workflow_execution_update_completed_event_attributes'):
        completed = event.workflow_execution_update_completed_event_attributes
        entry = entries.get(completed.meta.update_id)
        if entry is not None:
            if completed.accepted_event_id != entry.get('accepted_event_id') or 'completed_event_id' in entry:
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
        if event.event_id != 1 or not event.HasField('workflow_execution_started_event_attributes'):
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
    if last is None or not last.HasField('workflow_execution_continued_as_new_event_attributes'):
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
        extra['tasks'] = {task_id: {**task, 'eligible': active and task['status'] in ('ready', 'waiting_job')}
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
        if readback_task(opening) is not None:
            from ergora.campaigns.readback import FixedCheckReadback

            activities = [FixedCheckReadback(files, opening, attempt, handle.run_id).read]
        if recipient_task(opening) is not None:
            from ergora.campaigns.recipient import CodexRecipient

            activities.append(CodexRecipient(files, opening, attempt, handle.run_id).deliver)
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
