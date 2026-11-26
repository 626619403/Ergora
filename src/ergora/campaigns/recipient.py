"""Deliver one original successful timed readback to its authorized local Codex recipient."""

import asyncio

from temporalio import activity

from ergora.agents import runs
from ergora.campaigns.records import RECIPIENT_ACTIVITY, recipient_task, training_result_task
from ergora.campaigns.recipient_gate import (
    RecipientBlocked, RecipientGate, attempt_record, manual_commands, verify_wake_intent,
)
from ergora.storage.state import State


class CodexRecipient:
    def __init__(self, files, opening, start, run_id, *, read_wake_history):
        self.files, self.opening, self.start, self.run_id = files, opening, start, run_id
        self.read_wake_history = read_wake_history

    def _deliver(self, intent):
        files, opening, start, run_id = self.files, self.opening, self.start, self.run_id
        task = recipient_task(opening)
        verify_wake_intent(files, opening, start, run_id, task, intent)
        current, current_start, result = files.load()
        if current != opening or current_start != start:
            raise ValueError('Original Campaign and start attempt changed before recipient delivery')
        recipient = task['recipient']
        state = State(files.home)
        selection = (state, files.project, recipient['session_id'], recipient['parent_run_id'], recipient['intent_id'])
        original = runs.continuation_receipt(*selection)
        prior = files._read('recipient-attempt')
        if prior is not None:
            gate = RecipientGate(files, opening, start, result, prior)
            if gate.intent != intent or prior['native_run_id'] != original['run_id']:
                raise ValueError('Saved Campaign delivery belongs to a different original wake')
            recorded = original['run']
            observed = (recorded is not None and recorded['submitted'] == gate.submission()
                        and original['dispatch'] not in ('unrecorded', 'incomplete'))
            return {'status': 'observed' if observed else 'unknown', 'native_run_id': original['run_id']}
        if original['dispatch'] != 'unrecorded':
            return {'status': 'blocked', 'native_run_id': original['run_id'], 'reason': 'original_native_intent_occupied'}
        try:
            attempt = attempt_record(intent, original['run_id'])
            gate = RecipientGate(files, opening, start, result, attempt)
            with gate.admission():
                if files._read('recipient-attempt') is not None:
                    return {'status': 'unknown', 'native_run_id': original['run_id']}
                files.write('recipient-attempt', attempt, before_publish=gate.require_open)
            runs.continue_session(state, files.project, recipient['session_id'], recipient['parent_run_id'],
                                  recipient['prompt'], expected_revision=opening['project_revision'],
                                  intent_id=recipient['intent_id'], timeout=recipient['timeout_seconds'],
                                  wait_for_slot=True, campaign_recipient=gate.reference)
        except (RecipientBlocked, runs._SessionSlotTimeout) as error:
            if runs.continuation_receipt(*selection)['dispatch'] != 'unrecorded':
                return {'status': 'unknown', 'native_run_id': original['run_id']}
            reason = 'session_slot_timeout' if isinstance(error, runs._SessionSlotTimeout) else str(error)
            return {'status': 'blocked', 'native_run_id': original['run_id'], 'reason': reason}
        outcome = runs.continuation_receipt(*selection)
        return {'status': 'observed', 'native_run_id': outcome['run_id']}

    async def _deliver_verified(self, intent):
        opening = self.opening
        task = recipient_task(opening)
        manual = intent['source'].get('kind') == 'manual_update'
        if manual or training_result_task(task):
            commands = manual_commands(self.files, opening, self.start, self.run_id, task) if manual else ()
            wake = await self.read_wake_history(commands)
            if wake is None or wake['intent'] != intent:
                raise ValueError('Campaign manual delivery lacks its verified original Update and schedule' if manual
                                 else 'Campaign training delivery lacks its verified original result and schedule')
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
