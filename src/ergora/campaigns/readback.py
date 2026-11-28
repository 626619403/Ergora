"""Own one independently guarded native read for a frozen Campaign task."""

import asyncio
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import time

from temporalio import activity
from temporalio.exceptions import ApplicationError

from ergora.campaigns.records import (
    FIXED_CHECK_RECOVERY_ACTIVITY, FULL_RESULT_RECOVERY_ACTIVITY, FULL_RESULT_REOBSERVATION_ACTIVITY,
    READBACK_ACTIVITY, READBACK_CLEANUP_SECONDS, RELEASE_RECOVERY_ACTIVITY,
    TRAINING_GPU_RELEASE_ACTIVITY, TRAINING_READBACK_ACTIVITY, TRAINING_SCREEN_ACTIVITY,
    CampaignFiles, check_receipt, identity, readback_activity, readback_grant, readback_id, readback_task,
    readback_followup_activity, receipt_recovery_activity, receipt_recovery_id, reobservation_id, reobservation_task,
    require_check_project, training_readback_action, training_readback_task, verify_registration,
)
from ergora.runtime import action_observations, processes
from ergora.storage.state import State, file_lock


class CampaignReadback:
    def __init__(self, files, opening, start_attempt, run_id):
        self.files = files
        self.opening = opening
        self.start_attempt = start_attempt
        self.run_id = run_id

    @activity.defn(name=READBACK_ACTIVITY)
    async def read(self, grant: dict) -> dict:
        return await self._read(grant)

    @activity.defn(name=TRAINING_READBACK_ACTIVITY)
    async def read_training_result(self, grant: dict) -> dict:
        return await self._read(grant)

    @activity.defn(name=TRAINING_SCREEN_ACTIVITY)
    async def read_training_screen(self, grant: dict) -> dict:
        return await self._read(grant)

    @activity.defn(name=TRAINING_GPU_RELEASE_ACTIVITY)
    async def read_training_gpu_release(self, grant: dict) -> dict:
        return await self._read(grant)

    def activity_for(self, task):
        return {READBACK_ACTIVITY: self.read, TRAINING_READBACK_ACTIVITY: self.read_training_result,
                TRAINING_SCREEN_ACTIVITY: self.read_training_screen,
                TRAINING_GPU_RELEASE_ACTIVITY: self.read_training_gpu_release}[readback_activity(task)]

    @activity.defn(name=FIXED_CHECK_RECOVERY_ACTIVITY)
    async def recover_fixed_check(self, grant: dict) -> dict:
        return self._recover_receipt(grant)

    @activity.defn(name=RELEASE_RECOVERY_ACTIVITY)
    async def recover_release(self, grant: dict) -> dict:
        return self._recover_receipt(grant)

    @activity.defn(name=FULL_RESULT_RECOVERY_ACTIVITY)
    async def recover_full_result(self, grant: dict) -> dict:
        return self._recover_receipt(grant)

    @activity.defn(name=FULL_RESULT_REOBSERVATION_ACTIVITY)
    async def reobserve(self, grant: dict) -> dict:
        return await self._read(grant, reobservation=True)

    def recovery_activity_for(self, task):
        return {FIXED_CHECK_RECOVERY_ACTIVITY: self.recover_fixed_check,
                RELEASE_RECOVERY_ACTIVITY: self.recover_release,
                FULL_RESULT_RECOVERY_ACTIVITY: self.recover_full_result,
                FULL_RESULT_REOBSERVATION_ACTIVITY: self.reobserve}.get(readback_followup_activity(task))

    def _recover_receipt(self, grant):
        from ergora.campaigns.recipient_gate import verified_receipt_recovery

        info = activity.info()
        task = readback_task(self.opening)
        recovery = receipt_recovery_activity(task)
        fixed = recovery == FIXED_CHECK_RECOVERY_ACTIVITY
        waiting = self.files.load_check(self.opening, self.start_attempt, self.run_id, task, waiting=True) if fixed else None
        if (recovery is None or info.activity_type != recovery or info.attempt != 1
                or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_id != receipt_recovery_id(grant) or (fixed and waiting is None)
                or grant != readback_grant(self.opening, self.run_id, task, check_receipt(waiting) if waiting else None)):
            raise ValueError('Campaign recovery requires its selected original read')

        def require_open(work_cutoff=None):
            opening, start, result = self.files.load()
            if opening != self.opening or start != self.start_attempt or result is None or result['run_id'] != self.run_id:
                raise ValueError('Campaign original start changed before receipt recovery')
            stop, _, _ = self.files.load_stop(opening, start, result)
            if (stop is not None or self.files._read('readback-cancel') is not None
                    or not grant['due_at'] <= time.time() < grant['deadline_at'] - READBACK_CLEANUP_SECONDS
                    or work_cutoff is not None and time.monotonic() >= work_cutoff):
                raise ValueError('Campaign receipt recovery no longer admits the original receipt')

        require_open()
        require_check_project(State(self.files.home, read_only=True), self.opening)
        _, reply, guard, model = verified_receipt_recovery(self.files, self.opening, self.start_attempt, self.run_id, task)
        strict = recovery != RELEASE_RECOVERY_ACTIVITY
        _require_original_read_exits(guard, model, strict=strict)
        require_open(guard['work_cutoff_monotonic'] if strict else None)
        return reply

    async def _admit_reobservation(self, grant, packet):
        from ergora.campaigns.recipient_gate import verified_interrupted_read

        interruption, original_guard, _ = verified_interrupted_read(self.files, grant)
        wall_cutoff = grant['deadline_at'] - READBACK_CLEANUP_SECONDS
        work_cutoff = original_guard['work_cutoff_monotonic']

        def require_window():
            wall = time.time()
            remaining = min(wall_cutoff - wall, work_cutoff - time.monotonic())
            if wall < grant['due_at'] or remaining <= 0:
                raise ValueError('Campaign re-observation reached its original work cutoff')
            if any(self.files._read(name) is not None for name in
                   ('stop-intent', 'readback-cancel', 'recipient-attempt')):
                raise ValueError('Campaign re-observation no longer admits the original read')
            return remaining

        with ExitStack() as claim:
            while True:
                require_window()
                try:
                    claim.enter_context(file_lock(self.files.lock, blocking=False))
                except BlockingIOError:
                    activity.heartbeat(packet['activity_id'])
                    await asyncio.sleep(min(.15, require_window()))
                else:
                    break
            opening, start, result = self.files.load()
            if opening != self.opening or start != self.start_attempt or result is None or result['run_id'] != self.run_id:
                raise ValueError('Campaign re-observation differs from the original opening and Run')
            stop, _, _ = self.files.load_stop(opening, start, result)
            if (stop is not None or self.files._read('readback-cancel') is not None
                    or self.files._read('recipient-attempt') is not None):
                raise ValueError('Campaign re-observation no longer admits the original read')
            current, guard, model = verified_interrupted_read(self.files, grant)
            if current != interruption:
                raise ValueError('Campaign re-observation proof changed while waiting for its original lock')
            _require_original_read_exits(guard, model, strict=True, exact_generation=True)

            require_window()
            self.files.write('reobservation-attempt', {**packet, 'interruption_sha256': interruption},
                             before_publish=require_window)
            return interruption

    async def _read(self, grant, *, reobservation=False):
        info = activity.info()
        task = readback_task(self.opening)
        training = training_readback_task(task)
        waiting = None if training else self.files.load_check(
            self.opening, self.start_attempt, self.run_id, task, waiting=True)
        expected_id = reobservation_id(grant) if reobservation else readback_id(grant)
        expected_type = FULL_RESULT_REOBSERVATION_ACTIVITY if reobservation else readback_activity(task)
        if (info.attempt != 1 or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_type != expected_type or (reobservation and not reobservation_task(task))
                or info.activity_id != expected_id or (waiting is None and not training)
                or grant != readback_grant(self.opening, self.run_id, task, check_receipt(waiting) if waiting else None)
                or not grant['due_at'] <= time.time() < grant['deadline_at'] - READBACK_CLEANUP_SECONDS):
            message = ('Training readback does not bind the original task grant' if training else
                       'Fixed-check readback does not bind the current original wait')
            raise ApplicationError(message, non_retryable=True)
        # Exclusive publication also refuses any second host admission of this original Activity.
        prefix = 'reobservation' if reobservation else 'readback'
        packet = {'grant': grant, 'activity_id': info.activity_id, 'worker': processes.identity(os.getpid())}
        if reobservation:
            interruption = await self._admit_reobservation(grant, packet)
        else:
            self.files.write('readback-attempt', packet)
        spawning = asyncio.create_task(asyncio.create_subprocess_exec(
            sys.executable, '-P', '-m', 'ergora.campaigns.readback', str(self.files.home),
            self.files.project, self.files.campaign, *(('reobservation',) if reobservation else ()),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, start_new_session=True))
        waiter = None
        try:
            child = await asyncio.shield(spawning)
            waiter = asyncio.create_task(child.wait())
            while not waiter.done():
                activity.heartbeat(info.activity_id)
                await asyncio.wait((waiter,), timeout=.15)
        except asyncio.CancelledError:
            write_error = None
            try:
                self.files.write(f'{prefix}-cancel', {'activity_id': info.activity_id})
            except OSError as error:
                write_error = error
            if waiter is None:
                async def wait_for_guard():
                    guard = await spawning
                    return await guard.wait()

                waiter = asyncio.create_task(wait_for_guard())
            # A failed record write or later cancellation cannot transfer guard ownership.
            try:
                while not waiter.done():
                    try:
                        await asyncio.shield(waiter)
                    except asyncio.CancelledError:
                        continue
                waiter.result()
            except (Exception, asyncio.CancelledError) as error:
                if write_error is not None:
                    raise write_error from error
                raise
            if write_error is not None:
                raise write_error
            raise
        result = self.files._read(f'{prefix}-result')
        cleanup = self.files._read(f'{prefix}-cleanup')
        if (child.returncode != 0 or result is None or result['activity_id'] != info.activity_id
                or cleanup is None or cleanup['activity_id'] != info.activity_id
                or result['reader_cleanup_sha256'] != identity(cleanup)):
            raise ApplicationError('Original training readback result is unavailable' if training else
                                   'Original fixed-check readback result is unavailable', non_retryable=True)
        if reobservation:
            return {'reobservation_activity_id': info.activity_id,
                    'reobservation_interruption_sha256': interruption, 'reobserved_result': result}
        return result


def _require_original_read_exits(guard, model, *, strict, exact_generation=False):
    boot = processes.identity(os.getpid())['boot_id']
    for role, saved in (('worker', guard['worker']), ('guard', guard['guard']), ('reader', model)):
        if (not isinstance(saved, dict) or saved.keys() != {'pid', 'start_ticks', 'boot_id'}
                or not isinstance(saved['start_ticks'], str)
                or not saved['start_ticks'].isdigit() or type(saved['pid']) is not int or saved['pid'] <= 0
                or saved['boot_id'] != boot):
            raise ValueError('Campaign receipt recovery cannot verify the original process identity')
        ticks = saved['start_ticks']
        if strict and (not ticks.isascii() or (ticks != '0' and ticks.startswith('0'))):
            raise ValueError('Campaign receipt recovery cannot verify the original process identity')
        try:
            exited = False
            if strict and role == 'worker':
                process_state, original_process = processes.observe_process(saved['pid'])
                exited = process_state in ('Z', 'X', 'x')
            else:
                original_process = processes.identity(saved['pid'])
        except FileNotFoundError:
            continue
        if exact_generation and original_process != saved:
            raise ValueError('Campaign re-observation cannot verify a changed original process generation')
        if original_process == saved and not exited:
            raise ValueError('Campaign receipt recovery requires the original processes to have exited')


def _guard(home, project, campaign, prefix='readback'):
    from ergora.native.resources import validate_installation

    state = State(Path(home), read_only=True)
    files = CampaignFiles(state.root, project, campaign)
    if prefix not in ('readback', 'reobservation'):
        raise ValueError('Campaign guard requires an original read or re-observation')
    reobservation = prefix == 'reobservation'
    request = files._read(f'{prefix}-attempt')
    grant, worker, activity_id = request['grant'], request['worker'], request['activity_id']
    if processes.identity(os.getppid()) != worker:
        raise ValueError('Original Campaign Worker is unavailable before guard admission')
    sampled = time.monotonic()
    remaining = grant['deadline_at'] - time.time()
    deadline = sampled + remaining
    work_cutoff = deadline - READBACK_CLEANUP_SECONDS
    if reobservation:
        from ergora.campaigns.recipient_gate import verified_interrupted_read

        interruption, original_guard, _ = verified_interrupted_read(files, grant)
        if request.get('interruption_sha256') != interruption:
            raise ValueError('Campaign re-observation guard lost its original interruption proof')
        deadline = min(deadline, original_guard['deadline_monotonic'])
        work_cutoff = min(work_cutoff, original_guard['work_cutoff_monotonic'])
    guard = processes.identity(os.getpid())
    files.write(f'{prefix}-guard', {'activity_id': activity_id, 'worker': worker, 'guard': guard,
                                   'deadline_monotonic': deadline, 'work_cutoff_monotonic': work_cutoff})
    opening, attempt, result = files.load()
    task = readback_task(opening)
    run_id = grant['run_id']
    if result is not None and result['run_id'] != run_id:
        raise ValueError('Readback guard does not bind the original start')
    training = training_readback_task(task)
    fenced_publication = training or receipt_recovery_activity(task) == FIXED_CHECK_RECOVERY_ACTIVITY
    waiting = None if training else files.load_check(opening, attempt, run_id, task, waiting=True)
    if ((waiting is None and not training) or (training and result is None)
            or grant != readback_grant(opening, run_id, task, check_receipt(waiting) if waiting else None)
            or (reobservation and not reobservation_task(task))
            or activity_id != (reobservation_id(grant) if reobservation else readback_id(grant))):
        raise ValueError('Readback guard does not bind the original training grant' if training else
                         'Readback guard does not bind the original wait')
    verify_registration(state, opening)
    selected = require_check_project(state, opening)
    validate_installation(Path(selected['registration']['definition']['execution']['installation']), **({'training': True} if training else {}))

    def stopped():
        if time.time() >= grant['deadline_at'] - READBACK_CLEANUP_SECONDS:
            return True
        try:
            if processes.identity(worker['pid']) != worker:
                return True
        except (OSError, ValueError):
            return True
        cancel = files._read(f'{prefix}-cancel')
        if cancel == {'activity_id': activity_id} or (reobservation and files._read('readback-cancel') is not None):
            return True
        intent, _, stop = files.load_stop(opening, attempt, result)
        return intent is not None if fenced_publication else stop is not None and stop['receipt']['decision'] == 'accepted'

    def save_cleanup(receipt):
        files.write(f'{prefix}-cleanup', {'activity_id': activity_id, 'receipt': receipt,
                                         'reaped_at_monotonic': time.monotonic()})

    source = task['source']
    if training:
        action = training_readback_action(task)
    else:
        action = action_observations.FixedCheckStatus(source['operation_id'], source['job_sha256'], verify_pending=True)
    status = action_observations.observe(action, selected, state.root, deadline=work_cutoff,
                                         stop_requested=stopped, supervised_cleanup=save_cleanup)
    cleanup = files._read(f'{prefix}-cleanup')
    if (cleanup is None or cleanup['receipt']['owner'] != guard or not cleanup['receipt']['model_waited']
            or cleanup['receipt']['remaining_children'] or stopped()):
        raise ValueError('Original training reader cleanup is unavailable' if training else
                         'Original fixed-check reader cleanup is unavailable')
    observed = {'activity_id': activity_id, 'observation': status, 'reader_cleanup_sha256': identity(cleanup)}
    if fenced_publication:
        _publish_guarded_result(files, observed, work_cutoff, stopped, record=f'{prefix}-result')
    else:
        files.write('readback-result', observed)


def _publish_guarded_result(files, observed, work_cutoff, stopped, *, record='readback-result'):
    def require_window():
        if time.monotonic() >= work_cutoff:
            raise TimeoutError('Original Campaign readback result reached its publication cutoff')
        if stopped():
            raise ValueError('Original Campaign no longer admits the readback result')

    with ExitStack() as claim:
        while True:
            require_window()
            try:
                claim.enter_context(file_lock(files.lock, blocking=False))
            except BlockingIOError:
                time.sleep(min(.025, max(0, work_cutoff - time.monotonic())))
            else:
                break
        require_window()
        files.write(record, observed, before_publish=require_window)


if __name__ == '__main__':
    try:
        _guard(*sys.argv[1:])
    except (KeyboardInterrupt, OSError, ValueError, TimeoutError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
