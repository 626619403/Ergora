"""Optional Temporal schedules; source observation remains in the application layer."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import re

from temporalio import activity, workflow
from temporalio.client import (Client, Schedule, ScheduleActionStartWorkflow, ScheduleIntervalSpec,
                               ScheduleOverlapPolicy, SchedulePolicy, ScheduleSpec, ScheduleState)
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from . import research
    from .state import State


@workflow.defn(name="ErgoraSourceObservation")
class SourceObservation:
    @workflow.run
    async def run(self, request: dict) -> dict:
        request = {**request, "run_id": workflow.info().run_id.replace("-", "")}
        result = await workflow.execute_activity(
            "ergora_observe_sources", request,
            start_to_close_timeout=timedelta(seconds=request["timeout"] + 45),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        if result["status"] != "succeeded":
            from temporalio.exceptions import ApplicationError

            raise ApplicationError(f"Source observation ended {result['status']}", non_retryable=True)
        return result


class ResearchActivities:
    def __init__(self, state: State, project_id: str):
        self.state = state
        self.project_id = project_id

    @activity.defn(name="ergora_observe_sources")
    def observe(self, request: dict) -> dict:
        if request["project"] != self.project_id:
            raise ValueError("Research worker is bound to a different project")
        return research.run(self.state, request["project"], request["urls"], request["max_bytes"],
                            request["timeout"], request["allow_private"], request["run_id"])


def _binding(state: State, project_id: str) -> dict:
    binding = state.project(project_id)["bindings"].get("scheduler", {"tool": "manual"})
    if binding["tool"] != "temporal":
        raise ValueError("Select the temporal scheduler first")
    return binding


async def create(state: State, project_id: str, name: str, urls: list[str], interval_seconds: int,
                 max_bytes: int = 1_000_000, timeout: int = 30, allow_private: bool = False) -> dict:
    binding = _binding(state, project_id)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name) or not 60 <= interval_seconds <= 31_536_000:
        raise ValueError("Schedule requires a safe name and interval of 60–31536000 seconds")
    research.validate_request(urls, max_bytes, timeout)
    for url in urls:
        research.validate_url(url, allow_private)
    client = await Client.connect(binding["address"], namespace=binding["namespace"])
    schedule_id = f"ergora-research:{project_id}:{name}"
    payload = {"project": project_id, "urls": urls, "max_bytes": max_bytes, "timeout": timeout, "allow_private": allow_private}
    await client.create_schedule(schedule_id, Schedule(
        action=ScheduleActionStartWorkflow(SourceObservation.run, payload,
            id=schedule_id, task_queue=binding["task_queue"], execution_timeout=timedelta(seconds=timeout + 120)),
        spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=timedelta(seconds=interval_seconds))]),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP, catchup_window=timedelta(minutes=1), pause_on_failure=True),
        state=ScheduleState(paused=True, note="Created paused; verify sources, budgets and worker before enabling"),
    ))
    return {"id": schedule_id, "paused": True, "address": binding["address"], "namespace": binding["namespace"]}


async def control(state: State, project_id: str, name: str, operation: str) -> dict:
    binding = _binding(state, project_id)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Invalid schedule name")
    client = await Client.connect(binding["address"], namespace=binding["namespace"])
    schedule_id = f"ergora-research:{project_id}:{name}"
    handle = client.get_schedule_handle(schedule_id)
    if operation == "pause":
        await handle.pause(note="Paused by Ergora operator")
    elif operation == "resume":
        await handle.unpause(note="Enabled by Ergora operator")
    elif operation == "trigger":
        await handle.trigger(overlap=ScheduleOverlapPolicy.SKIP)
    elif operation == "delete":
        await handle.delete()
        return {"id": schedule_id, "deleted": True}
    elif operation != "status":
        raise ValueError("Unsupported schedule operation")
    description = await handle.describe()
    return {"id": schedule_id, "paused": description.schedule.state.paused,
            "actions": description.info.num_actions, "running_actions": len(description.info.running_actions)}


async def serve(state: State, project_id: str):
    binding = _binding(state, project_id)
    client = await Client.connect(binding["address"], namespace=binding["namespace"])
    activities = ResearchActivities(state, project_id)
    with ThreadPoolExecutor(max_workers=2) as executor:
        worker = Worker(client, task_queue=binding["task_queue"], workflows=[SourceObservation],
                        activities=[activities.observe], activity_executor=executor, max_concurrent_activities=2,
                        graceful_shutdown_timeout=timedelta(seconds=330))
        await worker.run()
