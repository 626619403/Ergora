# Authorize and supervise a finite training controller

English · [Documentation](../README.md)

Start from [prepared original experiments](prepare-experiments.md). This page authorizes a finite frozen selection and its original budget; [single-experiment execution](execution.md) and [evidence acceptance](evidence-and-approval.md) remain separate.

## Freeze finite candidates and budget policy

On Linux/WSL2, save 1–32 prepared, not-yet-submitted original experiments as one complete [schema2 input](../../src/ergora/data/schemas/training-cycle-v2.json). The example selects full execution; bounded screen search additionally freezes its prepared search, diagnostics, analyst and supported CPU-resource selections. First obtain each experiment's complete manifest SHA with `training show`. Replace the two placeholders below with their respective 64-character lowercase SHAs and save as `cycle-request.json`. Experiment IDs must also match prepared originals:

```json
{
  "schema_version": 2,
  "execution_scope": "ordered-selected-native-once",
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
ergora training cycle-authorize-controller my-project controlled-cycle-01 --directory "$HOME/ergora-inputs/cycle-01" --sha256 EXACT_CYCLE_SHA256 --revision REVISION --confirm --execute-selected
ergora training cycle-controller-prepare my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256 --revision REVISION
ergora training cycle-controller-submit my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256
ergora training cycle-controller-status my-project controlled-cycle-01 --authorization-sha256 EXACT_AUTHORIZATION_SHA256
```

For an unattended local handoff of one cycle authorized against the current runtime source, run `cycle-controller-submit` with `--wait-ready`. The caller waits for the original durable ready record, prepares the same controller intent and submits it through its bound queue. Keep an authorized process available to run this command while supervisor turns are inactive. The original computation window bounds the wait. A visible stop or unavailable admission reports its original status and reason. After a lost reply or a restart, repeat the exact waiting command to reconcile a saved attempt. The original controller worker and executor own their independent runtime and resource evidence.

Current controller consent is schema5; the input explicitly freezes either the strong full-accepted chain or `bounded-screen-profile-skip`. There is one current workflow/worker interface and no `--program-version` selector. Manual schema1 remains a separate explicit mode. Old schema2/3/4 records retain read-only evidence scope; they are not upgraded, replayed or given a renewed clock. Preparation, queues, execution, reconciliation and cleanup share the original deadline. Status is read-only, lost replies inspect the same original identities, and a stop veto alone does not certify executor cleanup.

## Bounded CPU search and per-round diagnostics

This source implements the D1 contract; full D1 runtime, service/model, matching and real-gain acceptance remain separate gates. Current search and cycle inputs use schema2. Search preparation derives distinct screen and full IDs per logical candidate and freezes both real preparations, source/config/reference/policy relationships and the complete source materials. Prepared full roles do not grant D1 full execution. Logical candidates remain bounded by the original family projection and capacities.

D1 birth explicitly grants only selected screen, profile and no-effect known-failure skip operations. Only complete authenticated `SCREEN_COMPLETED` or `SCREEN_REJECTED` trials with their required diagnostics and cleanup can advance. Ordinary failure/OOM/cancellation, partial results, wrong provenance or unknown cleanup stop new births and retain the original IDs for reconciliation. A skip is atomic with the earliest start/native opportunity and reuses original qualified negative evidence; it creates no work, checks, capture or analyst call.

CPU contract C is an operator-admitted source/input conformance contract. A is the original exact-preview preparation acceptance, not an effect grant; preview-body and confirmation-bearing intent hashes differ. Existing missing C/A/FD facts are not backfilled. Ordinary valid C/A and local data scope may remain allocation-unsupported; matching requires independent genuine subject/namespace/root/ancestor/window proof on both sides. Unsupported matching is visible, and automatic GPU modes without real lease/guard wiring remain unavailable.

Recovery reuses the original captured CPU-context references and complete source identity; missing or changed originals cannot be replaced by new observations or clocks. The [training execution contract](../architecture/execution/training.md#original-training-budget-submission-and-deadline-owner) describes the owner, durable reference and saved-data boundaries.

Profiling uses a distinct source-owned diagnostic window and fixed strict reader; profiled values do not enter unprofiled timing or independent full pairs. Capture, derivation and synchronization share the original runner/work cap. Required missing/unknown/readback failure blocks continuation. Optional unavailable/not-run needs its actual reason; first-failure cases cannot obtain another free capture. One fixed read-only analyst opportunity belongs to the baseline and each executed screen; skips use historical diagnostics only. Durable attempt precedes a model opportunity, and lost replies inspect that same run with original process/MCP cleanup.

Status separates sequence, skipped, screen-executed, promising and full-accepted counts. Known complete-prefix budget/stop cutoffs may be partial; unresolved effects take precedence as needs-reconciliation. D1 keeps verified-gain/full-accepted counts at zero and does not promote a baseline, reorder/extend the frozen space or claim target GPU/model quality. Source, package, controlled ports, real services and actual experiment results retain separate evidence scopes.


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

`training-cycle-worker` serves the one current controller interface from the application environment and the selected native installation. It remains separate from the budget worker. The existing normal queue is `ergora-training-cycle-v3` and the stop queue is `ergora-training-cycle-stop-v3`; these are opaque current identities, not version-selection options.

```bash
ergora services start my-project temporal training-budget-worker training-cycle-worker --revision REVISION --timeout 60
ergora services status my-project
ergora services logs my-project training-cycle-worker --bytes 4096
```

| Current activity name | Role |
| --- | --- |
| `ergora.training_cycle.start.v4` | Consume only the frozen current candidate opportunity. |
| `ergora.training_cycle.reconcile.v4` | Observe that original opportunity after a lost reply. |
| `ergora.training_cycle.request-execution-or-observe.v4` | Request or observe the original managed execution. |
| `ergora.training_cycle.observe-candidate.v4` | Read the original candidate facts. |
| `ergora.training_cycle.collect-round.v4` | Collect the original full/trial evidence and fixed diagnostics. |
| `ergora.training_cycle.reconcile-round.v4` | Reconcile that same collection operation. |
| `ergora.training_cycle.stop.v4` | Publish the original stop veto, drain permits and observe cleanup. |

Business input cannot self-assert workflow/run/namespace/attempt authority; SDK-owned context and original complete bindings remain required. Controller birth is schema5, while `cycle-authorize` remains the manual schema1 entry. Starting a service creates no experiment or runner. Historical records do not dispatch an old runtime through this worker.

Controller operations reference the complete original `cycle.json` and `authorization.json` by raw byte count and SHA, retaining the original clock/policy and selected count for supervision. The authorization content SHA remains distinct from its raw file SHA. Full roles, source pins and ordered candidate identities stay in those original files; changed or missing originals cannot grant new work. Known input bulk that cannot fit a required control or root envelope is rejected before the first budget clock. Future SDK metadata, owner/predecessor facts and operator stop text still pass their actual complete 32KiB checks; selecting 32 candidates does not waive those limits.

Activity results retain original operation identity and byte-count/SHA references to verified stdout. If complete originals cannot be obtained, a complete inline unknown is saved. The 32KiB limit includes SDK metadata; overflow fails explicitly. Stop notification, durable stop, drained parent permission and execution-subtree stop are reported separately. Service shutdown first stops ordinary claiming and waits for real resource cleanup, then closes stop. Fully handed-off budget roots continue their original deadline responsibility. Stop an entire cycle through its complete original stop protocol.

```bash
ergora services stop my-project training-cycle-worker --revision REVISION --confirm --timeout 60
```

Supervisor allows the cycle service 70 seconds for stop observation. CLI control waits at most 60 seconds and may first return `unconfirmed`. Continue checking `services status` and logs, preserving original operation materials. Forced kill or PID disappearance is only an OS fact; actual business stop still requires the original stop chain. After application upgrades or when an old daemon lacks new programs, explicitly stop/shutdown the managed stack through [service management](../operations/services.md#manage-services-explicitly), then start it with the new application environment. New commands do not silently reload a running old daemon. Local Supervisor requires Linux/WSL2.

Continue: [Submit, execute and recover a training experiment](execution.md) · [Read training evidence and approve exact results](evidence-and-approval.md).
