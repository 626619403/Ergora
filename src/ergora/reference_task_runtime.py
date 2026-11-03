"""Read the original Temporal runtime in a project-specific process."""

import asyncio
from datetime import timedelta
import json
import os
import sys
from types import SimpleNamespace


async def find_signal_event(handle, converter, signal_name: str, payload: dict) -> int | None:
    """Stream the original run's history and match the complete signal payload."""
    from dev_platform.contracts import canonical_sha

    async for event in handle.fetch_history_events(page_size=100, rpc_timeout=timedelta(seconds=20)):
        if not event.HasField('workflow_execution_signaled_event_attributes'):
            continue
        signal = event.workflow_execution_signaled_event_attributes
        if signal.signal_name != signal_name:
            continue
        values = await converter.decode(signal.input.payloads, [dict])
        if canonical_sha(values) == canonical_sha([payload]):
            return event.event_id
    return None


class VerifiedSpecClient:
    """Keep native lookup's history read while requiring exact original JSON."""

    def __init__(self, client, spec: dict):
        self.original = client
        self.spec = spec
        # The description returned by the SDK keeps its own real converter;
        # only the transport's explicit original-input decode uses this port.
        self.data_converter = SimpleNamespace(decode=self.decode_spec)

    def __getattr__(self, name):
        return getattr(self.original, name)

    async def decode_spec(self, *args, **kwargs):
        from dev_platform.contracts import canonical_sha

        values = await self.original.data_converter.decode(*args, **kwargs)
        if canonical_sha(values) != canonical_sha([self.spec]):
            raise ValueError('Workflow ID collision: original task spec differs in JSON identity')
        return values


async def _status(payload: dict) -> dict:
    from dev_platform.connection import connect, task_queue
    from dev_platform.runtime import DevelopmentTransport, RuntimeNotFound
    from dev_platform.workflow import workflow_id

    spec = payload['spec']
    identity = {'workflow_id': workflow_id(spec), 'run_id': payload['run_id']}
    runtime = DevelopmentTransport(VerifiedSpecClient(await connect(), spec), task_queue())
    try:
        observed = await runtime.poll(spec, payload['run_id'])
    except RuntimeNotFound:
        return {**identity, 'runtime_status': 'not_found'}
    return {**identity, **observed, 'runtime_status': 'queried'}


def main() -> None:
    """Query only: no ingress changes, workflow submission, signal or ledger writes."""
    from agent_platform.core import Blocked, environment
    from temporalio.service import RPCError

    try:
        payload = json.load(sys.stdin)
        # Use the same connection environment as the selected native runtime.
        os.environ.update(environment())
        result = asyncio.run(asyncio.wait_for(_status(payload), payload['timeout']))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except TimeoutError as error:
        raise SystemExit('BLOCKED: Task runtime query timed out; execution state remains unknown') from error
    except RPCError as error:
        raise SystemExit('BLOCKED: Task runtime query RPC failed: ' + error.status.name) from error
    except (OSError, ValueError, KeyError, TypeError, Blocked) as error:
        raise SystemExit('BLOCKED: ' + str(error))
