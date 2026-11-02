"""Read the original Temporal runtime in a project-specific process."""

import asyncio
import json
import os
import sys


async def _status(payload: dict) -> dict:
    from dev_platform.connection import connect, task_queue
    from dev_platform.runtime import DevelopmentTransport, RuntimeNotFound
    from dev_platform.workflow import workflow_id

    spec = payload['spec']
    identity = {'workflow_id': workflow_id(spec), 'run_id': payload['run_id']}
    runtime = DevelopmentTransport(await connect(), task_queue())
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
