"""Deliver original result and assignment wake intents to their authorized local recipients."""

import asyncio
from contextlib import ExitStack
import time

from temporalio import activity

from ergora.agents import runs
from ergora.campaigns.records import (
    ASSIGNMENT_ATTEMPT, ASSIGNMENT_REFUSAL, RECIPIENT_ACTIVITY, assignment_task, identity, recipient_task,
    training_assignment_task, training_readback_task,
)
from ergora.campaigns.recipient_gate import (
    TRAINING_PENDING_UNAVAILABLE, RecipientBlocked, RecipientGate,
    assignment_refusal, assignment_wait, attempt_record, manual_commands,
    stopped_receipt, verify_wake_intent,
)
from ergora.storage.state import State


class CodexRecipient:
    def __init__(self, files, opening, start, run_id, *, read_wake_history):
        self.files, self.opening, self.start, self.run_id = files, opening, start, run_id
        self.read_wake_history = read_wake_history

    def _first_slot(self, state, gate, held):
        first = recipient_task(self.opening)['recipient']
        while True:
            gate.require_open()
            try:
                return held.enter_context(runs.released_campaign_slot(state, self.files.project,
                    first['session_id'], first['parent_run_id'], self.opening['recipient_binding']))
            except BlockingIOError:
                time.sleep(min(.05, max(0.0, gate.remaining())))

    def _next_slot(self, state, result, held):
        claim = self.files._read(ASSIGNMENT_ATTEMPT)
        if claim is None:
            return {'status': 'unclaimed'}
        assigned = RecipientGate(self.files, self.opening, self.start, result, claim)
        native = runs.campaign_recipient_receipt(state, assigned)
        if native['dispatch'] == 'unrecorded' and assignment_refusal(self.files, claim) is not None:
            return {'status': 'refused', 'attempt_sha256': identity(claim)}
        if not stopped_receipt(native):
            return None
        try:
            return held.enter_context(runs.released_campaign_slot(state, self.files.project,
                assigned.declaration['session_id'], native['run_id'], assigned.binding, require_latest=False))
        except (BlockingIOError, FileNotFoundError):
            return None

    def _claim(self, state, result, attempt, name, independent, declaration):
        files, opening, start = self.files, self.opening, self.start
        gate = RecipientGate(files, opening, start, result, attempt, sealing=True)
        training = training_assignment_task(opening) if independent else None
        with ExitStack() as held:
            if independent:
                attempt['slot_release'] = self._first_slot(state, gate, held)
            while True:
                admission = gate.admission() if training is None else gate.training_pending_admission(state)
                with admission as pending:
                    if files._read(name) is not None:
                        return None, False
                    if independent and files._read('recipient-attempt') is not None:
                        raise RecipientBlocked('assignment_already_resumed')
                    if assignment_task(opening) is not None and not independent:
                        attempt['slot_release'] = self._next_slot(state, result, held)
                    if attempt.get('slot_release') is not None or assignment_task(opening) is None:
                        gate = RecipientGate(files, opening, start, result, attempt)
                        if assignment_task(opening) is not None:
                            try:
                                gate.require_authority(state)
                            except ValueError as error:
                                authority_error = error
                                break
                        if training is not None and not pending:
                            raise RecipientBlocked(TRAINING_PENDING_UNAVAILABLE)
                        files.write(name, attempt, before_publish=gate.require_open)
                        return gate, False
                time.sleep(min(.15, max(0.0, gate.remaining())))
        # Observe the selected native slot only after dropping the claim and prior-slot locks.
        if runs.campaign_preclaim_revoked(state, gate, declaration):
            return gate, True
        raise authority_error

    def _deliver(self, intent):
        files, opening, start, run_id = self.files, self.opening, self.start, self.run_id
        task = recipient_task(opening)
        assigned = assignment_task(opening)
        independent = assigned is not None and intent.get('task_id') == assigned['task_id']
        if independent:
            task = assigned
        verify_wake_intent(files, opening, start, run_id, task, intent)
        current, current_start, result = files.load()
        if current != opening or current_start != start:
            raise ValueError('Original Campaign and start attempt changed before recipient delivery')
        recipient = task['recipient']
        state = State(files.home)
        selection = (state, files.project, recipient['session_id'], recipient['parent_run_id'], recipient['intent_id'])
        original = runs.continuation_receipt(*selection)
        name = ASSIGNMENT_ATTEMPT if independent else 'recipient-attempt'
        prior = files._read(name)
        if prior is not None:
            gate = RecipientGate(files, opening, start, result, prior)
            if gate.intent != intent or prior['native_run_id'] != original['run_id']:
                raise ValueError('Saved Campaign delivery belongs to a different original wake')
            reserved = runs.campaign_recipient_receipt(state, gate)
            observed = reserved['dispatch'] not in ('unrecorded', 'incomplete')
            return {'status': 'observed' if observed else 'unknown', 'native_run_id': original['run_id']}
        if original['dispatch'] != 'unrecorded':
            return {'status': 'blocked', 'native_run_id': original['run_id'], 'reason': 'original_native_intent_occupied'}
        attempt = None
        try:
            attempt = attempt_record(intent, original['run_id'])
            gate, preclaim_revoked = self._claim(state, result, attempt, name, independent, recipient)
            if gate is None:
                return {'status': 'unknown', 'native_run_id': original['run_id']}
            if preclaim_revoked:
                raise runs._SessionAuthorityRevoked('Original Campaign expert permission generation changed')
            runs.continue_session(state, files.project, recipient['session_id'], recipient['parent_run_id'],
                                  recipient['prompt'], expected_revision=opening['project_revision'],
                                  intent_id=recipient['intent_id'], timeout=recipient['timeout_seconds'],
                                  wait_for_slot=True, campaign_recipient=gate.reference)
        except (RecipientBlocked, runs._SessionSlotTimeout, runs._SessionAuthorityRevoked) as error:
            if runs.continuation_receipt(*selection)['dispatch'] != 'unrecorded':
                return {'status': 'unknown', 'native_run_id': original['run_id']}
            if isinstance(error, runs._SessionAuthorityRevoked):
                reason = gate.blocker() or 'recipient_authority_revoked'
            elif isinstance(error, runs._SessionSlotTimeout):
                reason = 'session_slot_timeout'
            else:
                reason = str(error)
            if independent and attempt is not None and files._read(ASSIGNMENT_ATTEMPT) == attempt:
                files.write(ASSIGNMENT_REFUSAL, {'attempt_sha256': identity(attempt), 'reason': reason})
            return {'status': 'blocked', 'native_run_id': original['run_id'], 'reason': reason}
        outcome = runs.campaign_recipient_receipt(state, gate)
        observed = outcome['dispatch'] not in ('unrecorded', 'incomplete')
        return {'status': 'observed' if observed else 'unknown', 'native_run_id': outcome['run_id']}

    async def _deliver_verified(self, intent):
        opening = self.opening
        task = recipient_task(opening)
        assigned = assignment_task(opening)
        independent = assigned is not None and intent.get('task_id') == assigned['task_id']
        manual = intent['source'].get('kind') == 'manual_update'
        training = training_readback_task(task)
        fixed_recovery = not training and 'recovery_activity_id' in intent['source']
        if independent:
            training = training_assignment_task(opening) is not None
            commands = () if training else (assignment_wait(self.files, opening, self.start, self.run_id),)
            wake = await self.read_wake_history(commands, independent=True)
            if wake is None or wake.get('intent') != intent:
                if training:
                    raise ValueError('Campaign independent task lacks its verified original training wait and schedule')
                raise ValueError('Campaign independent task lacks its verified original waiting Update and schedule')
        elif manual or training or fixed_recovery:
            if manual:
                commands = manual_commands(self.files, opening, self.start, self.run_id, task)
            elif fixed_recovery:
                waiting = self.files.load_check(opening, self.start, self.run_id, task, waiting=True)
                if waiting is None:
                    raise ValueError('Campaign fixed-check recovery delivery lacks its protected waiting attempt')
                commands = (waiting,)
            else:
                commands = ()
            wake = await self.read_wake_history(commands)
            if wake is None or wake['intent'] != intent:
                raise ValueError('Campaign manual delivery lacks its verified original Update and schedule' if manual
                                 else 'Campaign recipient delivery lacks its verified original result and schedule')
            if fixed_recovery:
                accepted, completed, scheduled = (wake.get(key) for key in (
                    'waiting_accepted_event_id', 'waiting_completed_event_id', 'scheduled_event_id'))
                if (not all(type(event_id) is int for event_id in (accepted, completed, scheduled))
                        or not 0 < accepted < completed < scheduled):
                    raise ValueError('Campaign fixed-check recovery delivery lacks its verified original waiting Update')
        return await asyncio.to_thread(self._deliver, intent)

    @activity.defn(name=RECIPIENT_ACTIVITY)
    async def deliver(self, intent: dict) -> dict:
        info = activity.info()
        if (info.attempt != 1 or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_id != intent.get('wake_id') or not isinstance(intent.get('source'), dict)):
            raise ValueError('Recipient Activity must be the original scheduled delivery attempt')
        # The native subprocess owns execution and STOP after the reservation, even if this Worker exits.
        owner = asyncio.create_task(self._deliver_verified(intent))
        try:
            while not owner.done():
                activity.heartbeat(info.activity_id)
                await asyncio.wait((owner,), timeout=.15)
        except asyncio.CancelledError:
            while not owner.done():
                try:
                    await asyncio.shield(owner)
                except asyncio.CancelledError:
                    continue
            owner.result()
            raise
        return owner.result()
