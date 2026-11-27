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
    FULL_RESULT_RECOVERY_ACTIVITY, READBACK_ACTIVITY, READBACK_CLEANUP_SECONDS, RELEASE_RECOVERY_ACTIVITY,
    TRAINING_GPU_RELEASE_ACTIVITY, TRAINING_READBACK_ACTIVITY, TRAINING_SCREEN_ACTIVITY,
    CampaignFiles, check_receipt, identity, readback_activity, readback_grant, readback_id, readback_task,
    receipt_recovery_activity, receipt_recovery_id, require_check_project, training_readback_action, training_readback_task,
    verify_registration,
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

    @activity.defn(name=RELEASE_RECOVERY_ACTIVITY)
    async def recover_release(self, grant: dict) -> dict:
        return self._recover_receipt(grant)

    @activity.defn(name=FULL_RESULT_RECOVERY_ACTIVITY)
    async def recover_full_result(self, grant: dict) -> dict:
        return self._recover_receipt(grant)

    def recovery_activity_for(self, task):
        return {RELEASE_RECOVERY_ACTIVITY: self.recover_release,
                FULL_RESULT_RECOVERY_ACTIVITY: self.recover_full_result}.get(receipt_recovery_activity(task))

    def _recover_receipt(self, grant):
        from ergora.campaigns.recipient_gate import verified_receipt_recovery

        info = activity.info()
        task = readback_task(self.opening)
        recovery = receipt_recovery_activity(task)
        if (recovery is None or info.activity_type != recovery or info.attempt != 1
                or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_id != receipt_recovery_id(grant)
                or grant != readback_grant(self.opening, self.run_id, task, None)):
            raise ValueError('Campaign recovery requires its selected original training read')

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
        full_result = recovery == FULL_RESULT_RECOVERY_ACTIVITY
        boot = processes.identity(os.getpid())['boot_id']
        for role, saved in (('worker', guard['worker']), ('guard', guard['guard']), ('reader', model)):
            if (not isinstance(saved, dict) or saved.keys() != {'pid', 'start_ticks', 'boot_id'}
                    or not isinstance(saved['start_ticks'], str)
                    or not saved['start_ticks'].isdigit() or type(saved['pid']) is not int or saved['pid'] <= 0
                    or saved['boot_id'] != boot):
                raise ValueError('Campaign receipt recovery cannot verify the original process identity')
            ticks = saved['start_ticks']
            if full_result and (not ticks.isascii() or (ticks != '0' and ticks.startswith('0'))):
                raise ValueError('Campaign receipt recovery cannot verify the original process identity')
            try:
                if full_result and role == 'worker':
                    process_state, original_process = processes.observe_process(saved['pid'])
                    if process_state in ('Z', 'X', 'x'):
                        continue
                else:
                    original_process = processes.identity(saved['pid'])
            except FileNotFoundError:
                continue
            if original_process == saved:
                raise ValueError('Campaign receipt recovery requires the original processes to have exited')
        require_open(guard['work_cutoff_monotonic'] if full_result else None)
        return reply

    async def _read(self, grant):
        info = activity.info()
        task = readback_task(self.opening)
        training = training_readback_task(task)
        waiting = None if training else self.files.load_check(
            self.opening, self.start_attempt, self.run_id, task, waiting=True)
        if (info.attempt != 1 or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_type != readback_activity(task)
                or info.activity_id != readback_id(grant) or (waiting is None and not training)
                or grant != readback_grant(self.opening, self.run_id, task, check_receipt(waiting) if waiting else None)
                or not grant['due_at'] <= time.time() < grant['deadline_at'] - READBACK_CLEANUP_SECONDS):
            message = ('Training readback does not bind the original task grant' if training else
                       'Fixed-check readback does not bind the current original wait')
            raise ApplicationError(message, non_retryable=True)
        # Exclusive publication also refuses any second host admission of this original Activity.
        self.files.write('readback-attempt', {'grant': grant, 'activity_id': info.activity_id,
            'worker': processes.identity(os.getpid())})
        spawning = asyncio.create_task(asyncio.create_subprocess_exec(
            sys.executable, '-P', '-m', 'ergora.campaigns.readback', str(self.files.home),
            self.files.project, self.files.campaign, stdin=asyncio.subprocess.DEVNULL,
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
                self.files.write('readback-cancel', {'activity_id': info.activity_id})
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
        result = self.files._read('readback-result')
        cleanup = self.files._read('readback-cleanup')
        if (child.returncode != 0 or result is None or result['activity_id'] != info.activity_id
                or cleanup is None or cleanup['activity_id'] != info.activity_id
                or result['reader_cleanup_sha256'] != identity(cleanup)):
            raise ApplicationError('Original training readback result is unavailable' if training else
                                   'Original fixed-check readback result is unavailable', non_retryable=True)
        return result


def _guard(home, project, campaign):
    from ergora.native.resources import validate_installation

    state = State(Path(home), read_only=True)
    files = CampaignFiles(state.root, project, campaign)
    request = files._read('readback-attempt')
    grant, worker, activity_id = request['grant'], request['worker'], request['activity_id']
    if processes.identity(os.getppid()) != worker:
        raise ValueError('Original Campaign Worker is unavailable before guard admission')
    sampled = time.monotonic()
    remaining = grant['deadline_at'] - time.time()
    deadline = sampled + remaining
    work_cutoff = deadline - READBACK_CLEANUP_SECONDS
    guard = processes.identity(os.getpid())
    files.write('readback-guard', {'activity_id': activity_id, 'worker': worker, 'guard': guard,
                                  'deadline_monotonic': deadline, 'work_cutoff_monotonic': work_cutoff})
    opening, attempt, result = files.load()
    task = readback_task(opening)
    run_id = grant['run_id']
    if result is not None and result['run_id'] != run_id:
        raise ValueError('Readback guard does not bind the original start')
    training = training_readback_task(task)
    waiting = None if training else files.load_check(opening, attempt, run_id, task, waiting=True)
    if ((waiting is None and not training) or (training and result is None)
            or grant != readback_grant(opening, run_id, task, check_receipt(waiting) if waiting else None)
            or activity_id != readback_id(grant)):
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
        cancel = files._read('readback-cancel')
        if cancel == {'activity_id': activity_id}:
            return True
        intent, _, stop = files.load_stop(opening, attempt, result)
        return intent is not None if training else stop is not None and stop['receipt']['decision'] == 'accepted'

    def save_cleanup(receipt):
        files.write('readback-cleanup', {'activity_id': activity_id, 'receipt': receipt,
                                        'reaped_at_monotonic': time.monotonic()})

    source = task['source']
    if training:
        action = training_readback_action(task)
    else:
        action = action_observations.FixedCheckStatus(source['operation_id'], source['job_sha256'], verify_pending=True)
    status = action_observations.observe(action, selected, state.root, deadline=work_cutoff,
                                         stop_requested=stopped, supervised_cleanup=save_cleanup)
    cleanup = files._read('readback-cleanup')
    if (cleanup is None or cleanup['receipt']['owner'] != guard or not cleanup['receipt']['model_waited']
            or cleanup['receipt']['remaining_children'] or stopped()):
        raise ValueError('Original training reader cleanup is unavailable' if training else
                         'Original fixed-check reader cleanup is unavailable')
    observed = {'activity_id': activity_id, 'observation': status, 'reader_cleanup_sha256': identity(cleanup)}
    if training:
        _publish_training_result(files, observed, work_cutoff, stopped)
    else:
        files.write('readback-result', observed)


def _publish_training_result(files, observed, work_cutoff, stopped):
    def require_window():
        if time.monotonic() >= work_cutoff:
            raise TimeoutError('Original Campaign training result reached its publication cutoff')
        if stopped():
            raise ValueError('Original Campaign no longer admits the training result')

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
        files.write('readback-result', observed, before_publish=require_window)


if __name__ == '__main__':
    try:
        _guard(*sys.argv[1:])
    except (KeyboardInterrupt, OSError, ValueError, TimeoutError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
