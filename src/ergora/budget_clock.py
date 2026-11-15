"""Same-boot UTC and elapsed deadlines shared by task and training budgets."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys
import time


FIELDS = ('authorized_at', 'deadline_at', 'boot_id', 'boottime_ns')


def _clock() -> tuple[str, int]:
    if sys.platform != 'linux':
        raise ValueError('Budgeted native operations require Linux; use WSL2')
    return (Path('/proc/sys/kernel/random/boot_id').read_text(encoding='ascii').strip(),
            time.clock_gettime_ns(time.CLOCK_BOOTTIME))


def authorize(wall_seconds: int) -> dict:
    started = datetime.now(timezone.utc)
    boot_id, ticks = _clock()
    try:
        deadline = started + timedelta(seconds=wall_seconds)
    except OverflowError as error:
        raise ValueError('Budget duration exceeds the representable UTC deadline') from error
    return {'authorized_at': started.isoformat(), 'deadline_at': deadline.isoformat(),
            'boot_id': boot_id, 'boottime_ns': ticks}


def validate(instance: dict, wall_seconds: int) -> None:
    """Validate clock fields within the caller's complete immutable authorization."""
    if (not isinstance(instance.get('boot_id'), str)
            or re.fullmatch('[0-9a-f-]{36}', instance['boot_id']) is None
            or type(instance.get('boottime_ns')) is not int or instance['boottime_ns'] < 0):
        raise ValueError('Invalid immutable budget clock')
    try:
        started = datetime.fromisoformat(instance['authorized_at'])
        deadline = datetime.fromisoformat(instance['deadline_at'])
        if (started.utcoffset() != timedelta(0) or deadline.utcoffset() != timedelta(0)
                or started.isoformat() != instance['authorized_at'] or deadline.isoformat() != instance['deadline_at']
                or deadline != started + timedelta(seconds=wall_seconds)):
            raise ValueError('Budget timestamps differ from the original policy')
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError('Invalid budget timestamps') from error


def remaining(instance: dict, wall_seconds: int, reserve_seconds: int = 0) -> float:
    """Observe validated clock fields conservatively; never mutate or renew them."""
    boot_id, ticks = _clock()
    if boot_id != instance['boot_id']:
        raise ValueError('Budget recovery across boot or host is unsupported; original authorization is retained')
    monotonic_elapsed = (ticks - instance['boottime_ns']) / 1_000_000_000
    utc_elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(instance['authorized_at'])).total_seconds()
    if monotonic_elapsed < 0 or utc_elapsed < 0 or abs(monotonic_elapsed - utc_elapsed) > 5:
        raise ValueError('Budget clock discontinuity; original authorization cannot be renewed')
    return wall_seconds - max(monotonic_elapsed, utc_elapsed) - reserve_seconds
