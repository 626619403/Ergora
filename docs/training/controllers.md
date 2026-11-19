# Authorize and supervise a finite training controller

English · [Documentation](../README.md)

Start from [prepared original experiments](prepare-experiments.md). This page authorizes a finite frozen selection and its original budget; [single-experiment execution](execution.md) and [evidence acceptance](evidence-and-approval.md) remain separate.

## Freeze finite candidates and budget policy

On Linux/WSL2, save 1–32 prepared, not-yet-submitted original experiments as one complete input. First obtain each experiment's complete manifest SHA with `training show`. Replace the two placeholders below with their respective 64-character lowercase SHAs and save as `cycle-request.json`. Experiment IDs must also match prepared originals:

```json
{
  "schema_version": 1,
  "budget": {"wall_seconds": 900, "cleanup_seconds": 170, "control_timeout_seconds": 7},
  "candidates": [
    {"experiment_id": "trial-a", "manifest_sha256": "REPLACE_WITH_TRIAL_A_SHA256", "change": "解除已定位的重复计算", "next_bottleneck": "测量后重新确认"},
    {"experiment_id": "trial-b", "manifest_sha256": "REPLACE_WITH_TRIAL_B_SHA256", "change": "优化同一合同下的另一个候选", "next_bottleneck": "保留本轮原始证据"}
  ]
}
```

```bash
ergora training cycle-create my-project --definition cycle-request.json --directory "$HOME/ergora-inputs/cycle-01"
ergora training cycle-read "$HOME/ergora-inputs/cycle-01" --sha256 EXACT_CYCLE_SHA256
```

`cycle-create` read-only uses original registration and `check-start`, saving a complete project/registration snapshot, all candidate observations and policy, and returning the SHA of the entire `cycle.json`. It never overwrites an existing directory. Candidate order is fixed; the trial limit is the list length. Experiments cannot repeat or have prepared/unknown/submitted/rejected intents already. All candidates must share the initial baseline, workload, data/initial-state/environment/validation contract, quality requirements and comparison policy. Each candidate, track and allowed_changes remains complete. If contracts differ, correct the real selection rather than silently lowering thresholds.

All three budget values are strict integers. Cleanup is included in total wall time, with `1≤cleanup_seconds<wall_seconds`. `control_timeout_seconds` is a 1–60 second upper bound on the original use-case timeout; budget submission checks or terminates calls within the original remaining phase. It is not a hard deadline for the entire use case. `cycle-create` itself starts neither budget nor controller. Explicit authorization and submission must follow the original input. This budget provides no cost or GPU-hour metering.

Offline `cycle-read` needs no project, SDK, service or keys. It verifies the selected complete SHA, version and internal binding, retaining original observations in full. `coverage` explicitly describes saved local observations: runtime not queried, provenance not authenticated, execution not authorized and budget not started. Old ready fields do not establish current admission. Files are limited to 10,000,000 UTF-8 bytes and 64 levels/100000 values; oversized inputs are rejected, not truncated. Inputs retain original home/registration/execution paths and can be read offline across machines. Execution requires rechecking identities in the original supported environment; the file is neither active-run migration nor new start authorization.

## Start a local training budget and recover original authorization

In the original Linux/WSL2 environment and control directory, start a nonrenewable local budget for this finite input. First confirm current revision with `project show my-project`, then choose a project-unique cycle ID and explicitly confirm:

```bash
ergora training cycle-authorize my-project cycle-01 --directory "$HOME/ergora-inputs/cycle-01" --sha256 EXACT_CYCLE_SHA256 --revision REVISION --confirm
ergora training cycle-status my-project cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256
```

`EXACT_CYCLE_SHA256` is the complete file SHA returned by `cycle-create`. `EXACT_AUTHORIZATION_SHA256` is the authorization result's `authorization_sha256`, pinning canonical content of the selected original authorization; this latter option can be omitted. Authorization first checks this home's original registration journal and matching published result, complete project and execution ownership. It then saves original input and a one-time UTC/boot/CLOCK_BOOTTIME instant before checking all candidates' complete current admission. Records reside at `CONTROL_HOME/training-cycles/PROJECT/CYCLE_ID/`. File/directory persistence, all checks, interrupted waits and recovery consume the same deadline. Cleanup reserve is inside total wall time; no further admission is allowed once `work_remaining_seconds` reaches zero.

`status=ready` means only that all local admission matches original input and computation budget remained at observation; `coverage.execution_authorized` remains `false`. This creates no submission intent, workflow or job, starts no runner and provides no automatic stop protection for original manual `run-local`. `cycle-start` below explicitly binds original submission, after which `execute` selects managed computation. Local ready itself grants no run permission and represents no performance result.

After interruption or lost replies, repeat **the same authorization command**. The same ID first reads locally saved complete input, original authorization and ready; it does not require the external input directory still to exist and never restarts timing. With missing ready it rechecks all candidates only within original remaining time. The same ID bound to a different input SHA is rejected. Do not delete authorization or change IDs to bypass original allowance. `cycle-status` checks original sources, complete records, current project and clocks, without live admission, Temporal queries or keys. Existing ready still requires flushing the original directory after releasing the original lock and checking remaining time, to complete the same visible record after lost replies/directory-fsync failure. Original bytes stay unchanged; failed flush shows unknown. A busy original lock remains pending/exhausted; ready still being persisted cannot count as complete. The `temporal` extra is unnecessary.

`pending` means original authorization is saved but complete admission is unfinished; `exhausted` means the computation deadline passed; `project-changed` means the complete current project differs from the original revision. `unknown` gives specific cross-boot/host, discontinuous-clock or missing-clock-source reasons. The latter three cannot advance; originals remain. Missing/corrupt registration, input or ready, linked/special files, duplicate keys or nonfinite JSON fail explicitly, without fabricating records or reauthorizing. Original input retains the original 10MB/tree contract; authorization and ready are each limited to 1MiB. Across machines, `cycle-read` can read offline input; migrating a running authorization is currently unsupported.

To execute the complete finite selection, explicitly choose controller mode at a new cycle ID's creation and confirm the entire original selection. Existing manual authorization cannot be upgraded or its budget restarted:

```bash
ergora training cycle-authorize-controller my-project controlled-cycle-01 --directory "$HOME/ergora-inputs/cycle-01" --sha256 EXACT_CYCLE_SHA256 --revision REVISION --confirm --execute-selected --program-version 2
ergora training cycle-controller-prepare my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256 --revision REVISION
ergora training cycle-controller-submit my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256
ergora training cycle-controller-status my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256
```

`--program-version` freezes the selected controller version; CLI defaults to 2 and supports 1/2/3. Finite V2/V3 workflows execute candidates in frozen order within the original budget and read original measurements. The budget begins at first authorization; preparation, queueing, execution, recovery and cleanup share the same deadline. Stop, measurement acceptance and trusted evidence approval remain distinct facts. `status` only reads original local records. After a lost submission response, `cycle-controller-reconcile` observes the original workflow with the same identity without resending. `cycle-controller-stop --reason REASON` publishes a stop veto; that record alone cannot prove executor-subtree reaping. This does not dynamically generate candidates, extend the frozen list, automatically adopt results or provide automatic per-round profiling.

## Submit within the original budget and supervise deadlines continuously

For one experiment in an authorized selection, use the original Linux/WSL2 environment and control directory within the same system boot:

```bash
python -m pip install 'ergora[temporal]'
ergora services start my-project temporal training-budget-worker --revision REVISION --timeout 30
ergora training cycle-start my-project cycle-01 trial-a --authorization-sha256 EXACT_AUTHORIZATION_SHA256 --revision REVISION
ergora training submission my-project trial-a
```

`training-budget-worker` is an optional independent service using application Python with Ergora and the Temporal extra installed. It consumes only `ergora-training-budget-v1`, checking complete original authorization, current project, original Experiment, live owner and computation deadline under the native registry lock before writing a request. Original `training-worker` and the old queue continue independently. If the budget worker is absent, requests remain in the new queue while the deadline owner still establishes the original fence; there is no old-queue fallback. Supervisor `RUNNING` only means the service process is alive; `submission.status=submitted` only means an original control-plane run ID was obtained.

`cycle-start` saves an immutable intent and budget reference through original `training start`, then confirms an independent supervisor process before the first attempt. The original attempt consumes that experiment's one-time start slot; failure, lost replies, NOT_FOUND, cancellation, changing cycles or restarting never returns it. Subsequent ordinary start/resume for the same intent automatically preserves budget binding; existing unbudgeted intents cannot be taken over. Unbound old start and manual run-local gain no automatic protection.

Whether the call has returned or submission RPC is still in flight, the owner independently retains deadline responsibility. On computation expiry, original-project drift or catchable cancellation, it uses complete original binding to establish a local fence within original cleanup reserve, then reconciles the original run using a stable cancellation ID. Its supervised helpers bound blocking probes, registry locks or directory sync. If sources disappear, previously verified cache can still attempt the same fence; it cannot extend authorization. Matching requests not yet created are rejected by the fence. Completed native results retain original evidence and human release flow.

When reading `submission.budget`, distinguish `authorization_status`, `owner_status`, `final` and `local_fence`. `unknown` means some completion cannot be confirmed; it is no resend permission. Once the owner ends, original observation can complete directory sync/binding recheck of the same visible fence whose sync failed. Original final, clock and attempt bytes remain; neither owner restart nor new start publication occurs. SIGKILL, lost owner identity, cross-boot or missing originals cause no automatic restart/takeover. Historical stop results for new managed execution are in `budget.final.execution` and `budget.final.executor_stop_confirmed`; durable stop observation of the current original chain uses [original-chain observation](execution.md#explicit-managed-execution-and-offline-stop-observation). Old control observations with `executor_stop_confirmed=null`, fence creation or cancellation delivery do not establish training stopped.

New owners use dedicated supervisors for monitor, fence, cleanup and publish, preventing one phase from reaping another phase's subprocesses. `final.phases` retains phase IDs, business states, supervisor return codes and `stopped` observations. `stopped=true` only means that phase's helper subtree was actually reaped. Earlier unknown phases remain unknown even if a later fence succeeds. Final records use bounded 2MiB reads/writes; helpers and ordinary records remain limited to 1MiB. Original results are never truncated to fit extra phase metadata.

Cleanup reserve also includes these processes' startup, sync and control-plane call time. Insufficient reserve may leave only the same fence and no final. Safety cleanup already started waits for completion; OS reaping delays can exceed the total deadline, so it is no hard real-time guarantee. `overrun_seconds` records overrun already incurred when that final observation formed. No new phase starts after expiry; expired phases return unknown. Upgrades preserve running old owners' identities and capabilities; new owners use the new implementation at creation.

Recover with the original intent's complete SHA, without changing cycle or experiment IDs:

```bash
ergora training resume-start my-project trial-a --revision REVISION --intent-sha256 EXACT_START_INTENT_SHA256
ergora services logs my-project training-budget-worker --bytes 4096
```

This provides budgeted submission and continuous control responsibility for one candidate. Managed computation on the manual per-candidate path still requires the next explicit selection. Finite controllers consume execution consent explicitly frozen at creation. GPU/quality/performance gains still require separate acceptance.

## Integration entry point for the independent cycle service

`training-cycle-worker` provides four real Temporal activity consumers for controller integration, using the application environment's `ergora[temporal]` and registered native project installation. It and `training-budget-worker` have separate processes and event loops. Ordinary queue `ergora-training-cycle-v1` and stop queue `ergora-training-cycle-stop-v1` each have one activity slot. Check current project revision before explicitly starting required services:

```bash
ergora services start my-project temporal training-budget-worker training-cycle-worker --revision REVISION --timeout 60
ergora services status my-project
ergora services logs my-project training-cycle-worker --bytes 4096
```

|Activity|Purpose|
|---|---|
|`ergora.training_cycle.inspect.v1`|Authenticate the same original controller run and observe original authorization/facts.|
|`ergora.training_cycle.start.v1`|Consume ordinal 0's one opportunity from original schema2 creation consent; existing intents/retries only reconcile.|
|`ergora.training_cycle.reconcile.v1`|Read existing original candidates without regranting start.|
|`ergora.training_cycle.stop.v1`|Independently publish stop, drain parent permission, notify each original owner and observe execution chains, retaining every branch in full.|

Business input `workflow_input` contains only `protocol`, `control_home`, `project`, `cycle_id`, `input_sha256`, `authorization_sha256`; candidate actions add ordinal and stop adds reason. The SDK supplies actual Workflow/run/namespace/attempt, authenticated through the original supervised helper; business input cannot self-declare those privileges. Integrators must follow original schema2 authorization and intent→attempt→pinned run receipt protocol. Ordinary `cycle-authorize` remains the manual budget entry point. These schema2 activities preserve their original integration contract. The same worker also hosts finite V2/V3 controllers executing frozen original candidates through [explicit authorization and submission](#start-a-local-training-budget-and-recover-original-authorization). Measurement acceptance and stop facts are separate. Starting services itself creates no experiment or runner execution.

Activity results retain original operation identity and byte-count/SHA references to verified stdout. If complete originals cannot be obtained, a complete inline unknown is saved. The 32KiB limit includes SDK metadata; overflow fails explicitly. Stop notification, durable stop, drained parent permission and execution-subtree stop are reported separately. Service shutdown first stops ordinary claiming and waits for real resource cleanup, then closes stop. Fully handed-off budget roots continue their original deadline responsibility. Stop an entire cycle through its complete original stop protocol.

```bash
ergora services stop my-project training-cycle-worker --revision REVISION --confirm --timeout 60
```

Supervisor allows the cycle service 70 seconds for stop observation. CLI control waits at most 60 seconds and may first return `unconfirmed`. Continue checking `services status` and logs, preserving original operation materials. Forced kill or PID disappearance is only an OS fact; actual business stop still requires the original stop chain. After application upgrades or when an old daemon lacks new programs, explicitly stop/shutdown the managed stack through [service management](../operations/services.md#manage-services-explicitly), then start it with the new application environment. New commands do not silently reload a running old daemon. Local Supervisor requires Linux/WSL2.

Continue: [Submit, execute and recover a training experiment](execution.md) · [Read training evidence and approve exact results](evidence-and-approval.md).
