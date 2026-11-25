"""Own one independently guarded native status read for a frozen Campaign wait."""

import asyncio
import os
from pathlib import Path
import sys
import time

from temporalio import activity
from temporalio.exceptions import ApplicationError

from ergora.campaigns.records import (
    READBACK_ACTIVITY, READBACK_CLEANUP_SECONDS, CampaignFiles, check_receipt, identity,
    readback_grant, readback_id, readback_task, require_check_project, verify_registration,
)
from ergora.runtime import processes
from ergora.storage.state import State


class FixedCheckReadback:
    def __init__(self, files, opening, start_attempt, run_id):
        self.files = files
        self.opening = opening
        self.start_attempt = start_attempt
        self.run_id = run_id

    @activity.defn(name=READBACK_ACTIVITY)
    async def read(self, grant: dict) -> dict:
        info = activity.info()
        task = readback_task(self.opening)
        waiting = self.files.load_check(self.opening, self.start_attempt, self.run_id, task, waiting=True)
        if (info.attempt != 1 or info.workflow_id != self.opening['workflow_id'] or info.workflow_run_id != self.run_id
                or info.activity_id != readback_id(grant) or waiting is None
                or grant != readback_grant(self.opening, self.run_id, task, check_receipt(waiting))
                or not grant['due_at'] <= time.time() < grant['deadline_at'] - READBACK_CLEANUP_SECONDS):
            raise ApplicationError('Fixed-check readback does not bind the current original wait', non_retryable=True)
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
            self.files.write('readback-cancel', {'activity_id': info.activity_id})
            if waiter is None:
                child = await asyncio.shield(spawning)
                waiter = asyncio.create_task(child.wait())
            await asyncio.shield(waiter)
            raise
        result = self.files._read('readback-result')
        cleanup = self.files._read('readback-cleanup')
        if (child.returncode != 0 or result is None or result['activity_id'] != info.activity_id
                or cleanup is None or cleanup['activity_id'] != info.activity_id
                or result['reader_cleanup_sha256'] != identity(cleanup)):
            raise ApplicationError('Original fixed-check readback result is unavailable', non_retryable=True)
        return result


def _guard(home, project, campaign):
    from ergora.development.application import _candidate_check_status_request
    from ergora.development.native import task_fixed_candidate_check
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
    waiting = files.load_check(opening, attempt, run_id, task, waiting=True)
    if waiting is None or grant != readback_grant(opening, run_id, task, check_receipt(waiting)) or activity_id != readback_id(grant):
        raise ValueError('Readback guard does not bind the original wait')
    verify_registration(state, opening)
    selected = require_check_project(state, opening)
    validate_installation(Path(selected['registration']['definition']['execution']['installation']))

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
        _, _, stop = files.load_stop(opening, attempt, result)
        return stop is not None and stop['receipt']['decision'] == 'accepted'

    def save_cleanup(receipt):
        files.write('readback-cleanup', {'activity_id': activity_id, 'receipt': receipt,
                                        'reaped_at_monotonic': time.monotonic()})

    source = task['source']
    payload = _candidate_check_status_request(source['operation_id'], source['job_sha256'], True)
    status = task_fixed_candidate_check(selected, state.root, 'status-fixed-check', payload,
                                        deadline=work_cutoff, stop_requested=stopped, supervised_cleanup=save_cleanup)
    cleanup = files._read('readback-cleanup')
    if (cleanup is None or cleanup['receipt']['owner'] != guard or not cleanup['receipt']['model_waited']
            or cleanup['receipt']['remaining_children'] or stopped()):
        raise ValueError('Original fixed-check reader cleanup is unavailable')
    files.write('readback-result', {'activity_id': activity_id, 'observation': status,
                                    'reader_cleanup_sha256': identity(cleanup)})


if __name__ == '__main__':
    try:
        _guard(*sys.argv[1:])
    except (KeyboardInterrupt, OSError, ValueError, TimeoutError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
