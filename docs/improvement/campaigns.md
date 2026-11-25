# Record a finite optimization campaign

English · [Documentation](../README.md)

The local Unix operator can record the goal, acceptance criteria, baseline commit, evidence format and absolute expiry of a campaign. The original Temporal workflow records the passage of that deadline. This entry point grants no execution permissions. Expert actions and experiment jobs use their own execution and authorization paths.

Use an existing published project and explicitly bind its scheduler to the selected trusted Temporal service. Install the existing `ergora[temporal]` extra for `create`, `worker`, `stop` and online `status`. The operation uses the protected control home's owner and the CLI process's effective UID. This is local-process assurance. The current scheduler uses the configured address and namespace and relies on the selected service's access controls. [Project registration](../projects/registration.md) · [Configure Temporal](research-and-schedules.md)

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
