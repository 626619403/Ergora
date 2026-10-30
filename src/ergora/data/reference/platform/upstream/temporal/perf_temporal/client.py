"""Operator/development CLI. Production agents should use an authenticated gateway.

Never hand an unrestricted namespace API key to an implementation agent.
"""
import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
from temporalio.common import RetryPolicy, WorkflowIDReusePolicy, WorkflowIDConflictPolicy
from .connection import connect, task_queue
from .models import Binding, Experiment, ReleaseRequest, CancelRequest, workflow_id
from .workflow import ExperimentWorkflow


def load_experiment(path: str) -> Experiment:
    data = json.loads(Path(path).read_text())
    data["binding"] = Binding(**data["binding"])
    experiment = Experiment(**data)
    experiment.validate()
    return experiment


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "status", "result", "release", "cancel"])
    parser.add_argument("spec", help="JSON Experiment envelope; manifest_sha hashes referenced bytes")
    parser.add_argument("--receipt-id")
    parser.add_argument("--evidence-sha")
    parser.add_argument("--reason")
    args = parser.parse_args()
    experiment = load_experiment(args.spec)
    client = await connect()
    wid = workflow_id(experiment.binding)
    handle = client.get_workflow_handle_for(ExperimentWorkflow.run, wid)
    if args.action == "start":
        # Fail duplicate starts instead of hiding a conflicting manifest or resetting work.
        handle = await client.start_workflow(
            ExperimentWorkflow.run, experiment, id=wid, task_queue=task_queue(),
            id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
            id_conflict_policy=WorkflowIDConflictPolicy.FAIL,
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
        print(json.dumps({"workflow_id": handle.id, "run_id": handle.result_run_id}))
        return
    status = await handle.query(ExperimentWorkflow.status)
    if status.binding != experiment.binding:
        raise ValueError("Existing workflow binding differs from supplied spec")
    if args.action == "status":
        print(json.dumps(asdict(status), indent=2))
    elif args.action == "result":
        print(json.dumps(asdict(await handle.result()), indent=2))
    elif args.action == "release":
        if not args.receipt_id or not args.evidence_sha:
            parser.error("release requires --receipt-id and --evidence-sha")
        await handle.signal(ExperimentWorkflow.request_release,
                            ReleaseRequest(experiment.binding, args.evidence_sha, args.receipt_id))
        print("Release signal sent; this is not proof of authorization or task creation. Query status.")
    elif args.action == "cancel":
        if not args.reason:
            parser.error("cancel requires --reason")
        await handle.signal(ExperimentWorkflow.request_cancel,
                            CancelRequest(experiment.binding, args.reason))
        print("Cancellation requested. Wait for result; CANCEL_UNCONFIRMED needs operator action.")


if __name__ == "__main__":
    asyncio.run(main())
