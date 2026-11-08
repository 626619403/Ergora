"""Native SDK worker bootstrap for both versioned six-stage protocols."""

import asyncio
from contextlib import AsyncExitStack
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder
import os
from pathlib import Path
import signal
import sys

from . import reference


class _ErgoraPackage(MetaPathFinder):
    """Let the SDK sandbox reload this package without foreign dependencies."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'ergora':
            return PathFinder.find_spec(fullname, [str(Path(__file__).parent.parent)])
        return None


async def _serve() -> None:
    from dev_platform.adapter import load_adapter
    from dev_platform.connection import connect, task_queue
    from .reference_workflows import workers

    config = load_adapter().config
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stopped.set)

    async def connected():
        # Supervisor starts Temporal and this process together. Bound startup
        # retries while letting SIGTERM cancel an in-progress connection.
        async with asyncio.timeout(60):
            while True:
                try:
                    return await connect()
                except (RuntimeError, OSError):
                    await asyncio.sleep(1)

    try:
        connecting = asyncio.create_task(connected())
        stopping = asyncio.create_task(stopped.wait())
        try:
            await asyncio.wait((connecting, stopping), return_when=asyncio.FIRST_COMPLETED)
            if stopped.is_set():
                return
            client = connecting.result()
        finally:
            for pending in (connecting, stopping):
                pending.cancel()
            await asyncio.gather(connecting, stopping, return_exceptions=True)
        async with AsyncExitStack() as lifetime:
            for worker in workers(client, task_queue(), config):
                if stopped.is_set():
                    break
                await lifetime.enter_async_context(worker)
            await stopped.wait()
    finally:
        loop.remove_signal_handler(signal.SIGTERM)


def main(installation: str) -> None:
    """Load selected native modules only in this dedicated service process."""
    root = reference.validate_installation(Path(installation))
    sys.path[:0] = [str(root / 'local'), str(root / 'upstream/platform')]
    from agent_platform.core import environment

    os.environ.update(environment())
    package = _ErgoraPackage()
    sys.meta_path.insert(0, package)
    try:
        asyncio.run(_serve())
    finally:
        sys.meta_path.remove(package)
