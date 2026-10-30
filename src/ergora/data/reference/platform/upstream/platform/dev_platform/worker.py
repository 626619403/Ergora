"""Run on the trusted cloud control-plane host, separate from Codex executors."""
import asyncio
from temporalio.worker import Worker
from .activities import Activities
from .adapter import load_adapter
from .connection import connect, task_queue
from .workflow import DevelopmentWorkflow


async def main():
    adapter = load_adapter()  # Fail closed before connecting; no fake executor default.
    client = await connect()
    async with Worker(client, task_queue=task_queue(), workflows=[DevelopmentWorkflow],
                      activities=Activities(adapter).registered(), max_concurrent_activities=16):
        await asyncio.Event().wait()


if __name__ == "__main__": asyncio.run(main())
