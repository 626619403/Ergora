# Record a finite optimization campaign

English · [Documentation](../README.md)

The local Unix operator can record the goal, acceptance criteria, baseline commit, evidence format and absolute expiry of a campaign. The original Temporal workflow records the passage of that deadline. This entry point grants no execution permissions. Expert actions and experiment jobs use their own execution and authorization paths.

Use an existing published project and explicitly bind its scheduler to the selected trusted Temporal service. Install the existing `ergora[temporal]` extra for `create`, `worker`, `stop`, `observe-check` and online `status`. The operation uses the protected control home's owner and the CLI process's effective UID. This is local-process assurance. The current scheduler uses the configured address and namespace and relies on the selected service's access controls. [Project registration](../projects/registration.md) · [Configure Temporal](research-and-schedules.md)

Save a UTF-8 JSON file with these fields. Set `baseline_commit` to the full Git object ID you intend to use and replace `expires_at` with a future integer UTC Unix second.

```json
{
  "schema_version": 1,
  "goal": "Compare the candidate against the recorded baseline",
  "acceptance": "Record the exact candidate and matching verification result",
  "baseline_commit": "0123456789abcdef0123456789abcdef01234567",
  "evidence_format": "Candidate digest and original verification receipt",
  "limits": {"expires_at": 1795590000}
}
```

Run the create command with the current published project's revision and the SHA-256 of the exact approved file bytes. The response reports the original Workflow and first Run, the plan SHA-256 and the saved scheduler. Use the same `--home` for all campaign commands.

```bash
ergora campaign create my-project first-plan campaign.json \
  --revision PROJECT_REVISION --plan-sha256 PLAN_FILE_SHA256 --confirm

ergora campaign worker my-project first-plan
```

The worker runs in the foreground on the campaign's dedicated queue and exits after the original run closes. If you interrupt it, run the worker command again to process the original workflow. When Temporal accepts the start before a worker is ready, the first worker processes the original deadline. It can also close an original run after the deadline has passed.

```bash
ergora campaign status my-project first-plan
ergora campaign status my-project first-plan --online
```

Offline status reads the saved start and stop evidence without the SDK. Online status verifies the original start History and reports the Temporal run and any observed workflow state separately. A running workflow may have state unavailable while its worker is offline. The expiry phase is reported when the original completion can be verified.

After an uncertain start, read `status --online` and repeat `create` with the same project, campaign, exact plan bytes, revision and digest to save the verified original start. Once the dispatch attempt is saved, repeated `create` observes the same original start even if the current project scheduler changed. An unavailable service or missing original History leaves that attempt uncertain.

## Stop the original campaign plan

Use the same local Unix operator and control home. The confirmed stop binds one request to the saved scheduler and original first Run.

Before submitting STOP on an open plan, run the current `ergora campaign worker` on the original campaign queue. If an older worker lacks the STOP handler, shut it down normally before starting the current worker.

```bash
ergora campaign stop my-project first-plan --confirm
ergora campaign status my-project first-plan --online
```

An unavailable Worker check returns exit 1 with `stop.remote_status: worker_unavailable` and `stop.retryable: true` before saving a new stop intent or attempt. Retry the same command once the current worker is running.

After a lost reply, read online status and repeat the same stop command to reconcile the saved attempt and save its verified decision. Once an attempt exists, `stop.retryable` is `false` and the command observes the original `stop.update_id`. An unavailable service or missing decision leaves that attempt uncertain. An already closed Run at preflight returns its original terminal status.

Read `stop.status` for progress and `stop.receipt.decision` for the verified Update outcome. `accepted` records the original Workflow's decision to stop, and `expired` records that the original deadline took effect. The command can return exit 0 for an accepted receipt before closure is verified. Use online `temporal_status` and `workflow_state.phase` to check the original terminal outcome. This stop applies to the campaign plan. Agent, Job and resource lifecycle remain with their execution owners.

## Record an original fixed check for a task

Before creation, a plan can include one to eight tasks in `tasks`. Each task declares a unique `task_id`, a list of distinct task IDs in `depends_on` and an exact fixed-check `source`. Dependencies stay within the frozen plan and form an acyclic graph.

For this example, start with a `campaign.json` that has a future expiry. Save the `task candidate-check-status` JSON for two original Jobs under the same project and protected control home as `baseline-check.json` and `candidate-check.json`. Use already authorized, successful checks with confirmed cleanup and `stop_requested: false`. The source retains the original Job's `project_revision`, which can differ from the campaign's project revision. [Original fixed-check status](../development/run-and-recover.md#run-registered-fixed-checks-on-an-exported-candidate)

```bash
python3 - <<'PY'
import json
from pathlib import Path

fields = (
    "operation_id", "request_file_sha256", "job_sha256", "candidate_sha",
    "receipt_sha256", "fixed_results_sha256", "project_revision", "job_id",
    "authorization_sha256", "verification_sha256",
)

def source(path):
    status = json.loads(Path(path).read_text(encoding="utf-8"))
    return {field: status[field] for field in fields}

plan = json.loads(Path("campaign.json").read_text(encoding="utf-8"))
plan["tasks"] = [
    {"task_id": "verify-baseline", "depends_on": [], "source": source("baseline-check.json")},
    {"task_id": "verify-candidate", "depends_on": ["verify-baseline"], "source": source("candidate-check.json")},
]
with Path("campaign-with-checks.json").open("x", encoding="utf-8") as output:
    json.dump(plan, output, indent=2)
    output.write("\n")
PY
```

Use the create command above with the new campaign ID `fixed-check-plan`, the current project revision and the SHA-256 of the exact `campaign-with-checks.json` bytes. Run the current worker on that campaign's original queue.

```bash
ergora campaign observe-check my-project fixed-check-plan verify-baseline --confirm
ergora campaign status my-project fixed-check-plan --online
```

Online status reports `tasks` by ID. Confirm `verify-baseline` is `observed` and `verify-candidate` has `status: ready` and `eligible: true` before submitting the dependent observation.

```bash
ergora campaign observe-check my-project fixed-check-plan verify-candidate --confirm
```

`observe-check` verifies the original passing Job, cleanup and source identities before recording the observation. Its result reports `campaign_project_revision` and `job_project_revision` separately. After an uncertain reply, read online status and repeat the same command to reconcile the saved `update_id`. When task state is available, a saved unresolved attempt shows `attempt_status: unknown` and `eligible: false`. STOP and expiry close admission for new observations. The original receipts remain readable, including by reconciliation of a saved attempt. The fixed-check executor retains Job ownership and authority.

### Observe an original check that is still pending

Before freezing the plan, read the already authorized Job with `task candidate-check-status` under the same project and protected control home. Use the source fields from the example above, set `source.pending` to `true` and omit `receipt_sha256` and `fixed_results_sha256`. Copy the other eight fields exactly. If you need to configure the campaign scheduler, do so before authorizing a Job that has yet to launch. Preserve the original Job's project revision through launch.

Use the same confirmed `observe-check` command once the task's dependencies are observed. A verified `queued` or `attempted` Job yields `status: waiting_job`. An original executor rejection blocks this observation, even when the historical Job status still reports `queued` or `attempted`. Dependent tasks wait for `observed`. Repeat the command to check again. While the Job is still pending, the command returns its saved waiting receipt and `update_id`. A passing original Job with confirmed cleanup yields `status: observed` in a terminal Update. Its `receipt.job` contains the original `receipt_sha256` and `fixed_results_sha256`, plus `waiting_receipt_sha256` when a waiting receipt preceded it. A Job that has already passed at first observation can go directly to `observed`. Online task status retains the first `waiting_receipt` alongside any terminal `receipt`.

After an uncertain reply, repeat the same command to read the saved stage's original `update_id`. An unresolved attempt stays in readback. A fresh Job status read is bounded by the campaign's original deadline. A locally saved, accepted STOP or operator cancellation interrupts and reaps the local status reader. STOP and the original deadline close admission for new waiting and terminal observations. Use online campaign status for saved receipts and `task candidate-check-status` for the original Job's later outcome and cleanup. The original executor retains Job control. Any resource release requires evidence from the original resource owner.

### Allow one timed readback of a waiting check

To opt in, add `"readback": {"due_at": DUE, "deadline_at": DEADLINE}` to one task in the frozen plan with `"pending": true` in its `source`. Use positive integer Unix seconds with `due_at < deadline_at <= limits.expires_at`. Run the current Linux campaign Worker on the original queue and control home. The first accepted `waiting_job` receipt arms one read of that exact Job. If `due_at` is still in the future, one Timer waits for it. When `due_at` has arrived and the original window still leaves time for cleanup, the Workflow schedules the Activity immediately without starting a Timer. Worker replacement preserves the original window and single attempt. A direct terminal observation leaves the timer unarmed.

Online status reports `readback_observation` for the opted-in task. It starts at `not_armed`. `armed` identifies a bound waiting receipt and `scheduled` identifies an Activity request. `available` links `activity_id` and `waiting_receipt_sha256` to the original `receipt_sha256`, `fixed_results_sha256`, `observation_sha256` and `reader_cleanup_sha256`. `unknown` gives the reason, such as an unavailable or still-pending original read, a closed campaign or an already observed task.

Use a confirmed `observe-check` to verify the original Job, record its passing terminal receipt and make dependents eligible. Reader cleanup covers the local status reader. Read any late Job outcome through the original fixed-check status and obtain resource release evidence from the original resource owner.
