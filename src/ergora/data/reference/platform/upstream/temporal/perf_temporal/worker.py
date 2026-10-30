import asyncio
from temporalio.worker import Worker
from .activities import Activities
from .adapter import load_adapter
from .connection import connect, task_queue
from .workflow import ExperimentWorkflow


async def main() -> None:
    adapter = load_adapter()  # Fail before connecting if no real runner adapter exists.
    client = await connect()
    async with Worker(
        client, task_queue=task_queue(), workflows=[ExperimentWorkflow],
        activities=Activities(adapter).registered(),
        max_concurrent_activities=8,
    ):
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
