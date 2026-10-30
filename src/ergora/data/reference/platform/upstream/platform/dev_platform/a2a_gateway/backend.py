"""The A2A transport knows this small backend port, not workflow implementation details."""
from typing import Protocol


class Backend(Protocol):
    async def start(self, spec: dict) -> str: ...
    async def lookup(self, spec: dict, run_id: str | None = None) -> str | None: ...
    async def poll(self, spec: dict, run_id: str) -> dict: ...
    async def cancel(self, spec: dict, run_id: str, reason: str) -> None: ...


class TemporalBackend:
    def __init__(self, client, queue):
        from ..runtime import DevelopmentTransport
        self.transport = DevelopmentTransport(client, queue)

    async def start(self, spec):
        return await self.transport.start(spec)

    async def lookup(self, spec, run_id=None):
        from ..runtime import RuntimeNotFound
        try:
            _, description = await self.transport.lookup(spec, run_id)
            return description.run_id
        except RuntimeNotFound:
            return None

    async def poll(self, spec, run_id):
        return await self.transport.poll(spec, run_id)

    async def cancel(self, spec, run_id, reason):
        await self.transport.cancel(spec, run_id, reason)
