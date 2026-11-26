"""Pause an actual publication or the original executor's locked callback."""

import os
import json
from pathlib import Path
import sys
import time


def pause():
    marker = Path(os.environ['ERGORA_TEST_TRAINING_CONTROLLER_MARKER'])
    marker.touch()
    while not marker.with_suffix('.release').exists():
        time.sleep(.01)


def install():
    import ergora.training.execution_protocol as protocol

    boundary = os.environ['ERGORA_TEST_TRAINING_CONTROLLER_PAUSE']
    if boundary == 'executor-lock':
        from agent_platform import training_executor

        process = training_executor.process
        def locked_process(folder, *, admit, **kwargs):
            def locked_admit(job, record):
                pause()
                return admit(job, record)
            return process(folder, admit=locked_admit, **kwargs)
        training_executor.process = locked_process
    else:
        fault = os.environ.get('ERGORA_TEST_NATIVE_BOUNDARY_FAULT')
        if fault == 'parent-work':
            read_raw = protocol.read_raw
            def blocked_parent_read(path, *args, **kwargs):
                raw = read_raw(path, *args, **kwargs)
                caller = sys._getframe(3)
                if (Path(path).name == 'authorization.json' and caller.f_code.co_name == 'active'
                        and caller.f_locals.get('ack') is not None):
                    pause()
                    from datetime import timedelta
                    context = caller.f_locals['context']
                    clock, policy = context['authorization']['clock'], context['policy']
                    original_clock, original_datetime = protocol.budget_clock._clock, protocol.budget_clock.datetime
                    _, ticks = original_clock()
                    shift = max(0, clock['boottime_ns'] + (
                        policy['wall_seconds'] - policy['cleanup_seconds'] + 1) * 1_000_000_000 - ticks)
                    def shifted_clock():
                        boot, current = original_clock()
                        return boot, current + shift
                    class ShiftedDateTime(original_datetime):
                        @classmethod
                        def now(cls, tz=None):
                            return original_datetime.now(tz) + timedelta(seconds=shift / 1_000_000_000)
                    protocol.budget_clock._clock = shifted_clock
                    protocol.budget_clock.datetime = ShiftedDateTime
                    Path(os.environ['ERGORA_TEST_TRAINING_CONTROLLER_MARKER']).with_suffix('.clock').write_text(
                        json.dumps({'clock': clock, 'boot_id': shifted_clock()[0],
                            'work_remaining': protocol.budget_clock.remaining(
                                clock, policy['wall_seconds'], policy['cleanup_seconds']),
                            'total_remaining': protocol.budget_clock.remaining(clock, policy['wall_seconds'])}))
                return raw
            protocol.read_raw = blocked_parent_read
        publish = protocol.publish
        def paused_publish(path, value, root):
            publish(path, value, root)
            if path.name == boundary + '.json' and fault != 'parent-work':
                pause()
                if os.environ.get('ERGORA_TEST_NATIVE_BOUNDARY_FAULT') == 'clock':
                    from datetime import timedelta
                    original = protocol.budget_clock.datetime
                    class DriftedDateTime(original):
                        @classmethod
                        def now(cls, tz=None):
                            return original.now(tz) + timedelta(seconds=10)
                    protocol.budget_clock.datetime = DriftedDateTime
        protocol.publish = paused_publish
