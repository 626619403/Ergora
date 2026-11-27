# Inspect and control registered services

English · [Documentation](../README.md) · [简体中文](../zh-CN/operations/services.md)

## Diagnose and repair

`ergora tools doctor PROJECT` uses effective bindings to show installation, version, authentication, connectivity, task prerequisites and repair guidance, with the project revision and configuration digest. By default, it checks local installation only, without connecting to external services or calling models. `ergora tools doctor PROJECT --probe --timeout 5` actively checks native CLI versions, Codex credential status and ReMe/Temporal TCP reachability. `--timeout` is a shared 1–30 second budget for all active probes; local installation checks and process cleanup are counted separately. The tool bindings page provides the same active probe entry. Its API is `POST /api/projects/PROJECT/doctor`, with body `{"timeout":5}` and the existing local write-request header `X-Ergora-Request: 1`.

`credentials_present` means only that credentials exist in the CLI/environment; it does not establish account, quota or model availability. `tcp_reachable` establishes only transport reachability, not service protocol, authorization, namespace or worker readiness. `not_checked`, `not_confirmed`, timeouts and exhausted budgets cannot count as passing. doctor does not execute custom commands. Claude/mini/GEPA/Forge authentication and real tasks still need explicit acceptance according to the repair guidance; the Forge version must match the pinned commit. `task_availability: available` means only that local prerequisites such as SQLite/manual operations are available, rather than formal six-stage acceptance. Raw probe output is neither returned nor persisted; only version numbers or status are returned.

## Read and recover after services stop

Once unified registration and installation of the complete execution environment are finished, assess running services and existing persistent receipts separately. Complete formal execution uses Linux/WSL2. See the [Windows guide](../install/windows.md#choose-an-execution-environment) for the scope of the Windows control plane and optional tools.

|What to read or execute|Services that must be running|Factual boundary|
|---|---|---|
|Original contract and creation/submission/approval/cancellation/reconciliation/export records|No execution services required|Reads persistent files; historical receipts do not establish current Git branches, external processes or live run status|
|Closed original run's status/result, original events and job receipts/text materials|Temporal; no worker/executor required|Pins the original run and evidence digests; event/job reads also apply to a running original run, while materials additionally require a readable original trusted artifact directory|
|Evidence index, budget facts and handoff collection for a closed run|Temporal, registered complete Linux/WSL2 runtime and original materials; no worker/executor required|The original run must be closed without a successor; checks materials against original contracts/receipts; connection failure does not return a partial index or handoff package presented as complete|
|`handoff verify` for a saved handoff package|No online service, control database or Temporal SDK required|Basic Windows/Linux installations can verify package bytes and declared identities offline; source authentication, complete history and candidate revalidation require separate checks|
|Stage/status queries for a running original run|Temporal and a worker able to answer workflow queries|`task status` uses a workflow query when RUNNING; a query may fail with only Temporal online|
|Continue formal stages and real Agent calls|Temporal, corresponding worker/executor and authentication for selected tools|Check delivery receipts and actual completion separately; starting services does not automatically resend unknown operations|
|Explicit service start/exit and logs|Complete Linux/WSL2 reference installation and Supervisor|The unified entry manages the stack belonging to this execution directory; projects sharing a directory share services|

After closing the browser or restarting HTTP, select the original project/task again and read the original records to recover. Clearing session selections does not delete backend intents. Run input can be refilled from persistent submission; retain the original decision/request IDs for approval/cancellation. If the original run service is unreachable, the page explicitly shows query failure; local receipts remain independently readable. Do not treat connection failure as an unsubmitted task or rerun with a different task ID. To inspect an existing closed run, explicitly start only Temporal. Before resuming execution, separately check the required worker, executor, tools and original intent status. See [Explicit service management](#manage-services-explicitly) for the steps.

## Legacy reference CLI and unified entry

The unified `ergora task` reads Temporal configuration from the registered reference environment; legacy `agentflow task` reads its connection from the current shell. For a loopback development service on the local machine, explicitly set the following for legacy commands:

```bash
export TEMPORAL_ADDRESS=127.0.0.1:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_LOCAL_DEV=1
```

LOCAL_DEV applies only to loopback development services; connect to other services with their own authentication configuration. Task ownership differs between the two entries. Legacy tasks retain their original configuration/STATE and CLI and cannot be implicitly taken over through unified commands. Supervisor management also distinguishes execution states; stopping the current shared stack affects all its projects.

## Manage services explicitly

On Linux/WSL2, first install and initialize the reference runtime and complete [unified project registration](../projects/registration.md). `ergora services` uses registered execution directories and Supervisor in the reference environment without system-service privileges. One execution-state directory is a shared service stack that may serve multiple projects; stopping it affects that stack's in-flight tasks. Replace `--revision 1` below with the current revision from `project show`:

```bash
ergora services status my-project
ergora services start my-project temporal worker --revision 1 --timeout 30
ergora services logs my-project worker --bytes 8192
ergora services stop my-project worker temporal --revision 1 --confirm --timeout 30
ergora services shutdown my-project --revision 1 --confirm --timeout 30
```

The selectable services are `temporal`, `mlflow`, `worker`, `executor`, `a2a`, `training-worker`, `training-budget-worker` and `training-cycle-worker`. Only listed services start; dependencies or research do not start automatically. For a v7 provenance task, explicitly start the original six-stage services with `ergora services start my-project temporal worker executor --revision 1 --timeout 30`. Older v1–v6 installation-level doctor checks additionally require a local A2A listener, so explicitly add `a2a` when needed. Start MLflow separately for observation. The managed executor uses this same Ergora control directory's selective executor. Supervisor `RUNNING` is only process status; service protocols, worker/queues, models and tasks have separate acceptance. stop and shutdown require confirmation. Their 1–60-second control-wait budget starts after registration preflight. `outcome: unconfirmed` means the operation may continue; query status and reconcile. Do not restart until STOPPED is confirmed. Failed/unconfirmed operations return a nonzero CLI status.

The first start creates `ergora-services/` under execution state, recording control-directory ownership, a separate socket and configuration. It copies the original Supervisor program definitions with all autostart disabled; the original ini remains unchanged. An existing original Supervisor socket prevents takeover. First stop and check the original stack with `agentflow services stop`, then use the new entry point. Stale sockets/PIDs also require reconciliation. Registration-projection drift and conflicting control-directory ownership cause explicit failures. If a new Supervisor daemon's temporary Unix socket path leaves too little room for its PID suffix, choose a shorter persistent execution-state directory. Before upgrading software, shutdown the managed stack; explicitly restart it with original arguments after upgrading.

The normal and stop queues of `training-cycle-worker` have separate activity slots. Its PID is separate from the budget service, providing four activity consumers. See [the integrated cycle-service entry](../training/controllers.md#integration-entry-point-for-the-independent-cycle-service) for integration scope, explicit start and 70-second stop observation. The same worker hosts the finite V2/V3 selected-candidate controller; use the [explicit controller authorization and submission commands](../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization). Starting services does not authorize execution.

Use the separate Campaign service command for one original Campaign queue. It uses the same Supervisor control path and reports that queue's polling independently of process state. [Manage one Campaign Worker](../improvement/campaigns.md#manage-one-campaign-worker)

The default native log-byte window is 8192; select 4–65536 bytes, enough for at least one UTF-8 character. Use returned `next_offset` as the next `--offset`. `overflow` means intervening content exceeded the window. `rotated` means the current file is shorter than the cursor and the window reset; check original logs as well. After querying the actual log path from Supervisor, read only a bounded window of an ordinary file, without loading a large file completely. `limit` constrains raw read bytes; text/JSON output may grow through replacement characters or escaping. Valid UTF-8 boundaries are retained. An incomplete suffix's `pending_bytes` is not yet included in `next_offset`; continue with the original cursor after more bytes arrive. Invalid bytes use replacement characters.

Same-origin API: `GET /api/projects/ID/services`; `POST` at the same path with body `{"action":"start","names":["temporal"],"revision":1,"timeout":30}`. Add `"confirm":true` for stop; shutdown uses empty names. Mutations retain `X-Ergora-Request: 1`. `GET /api/projects/ID/services/NAME/logs?limit=8192&offset=0&stderr=false` returns bounded text and a cursor. Native Windows supports the console, while local Supervisor management requires WSL2/Linux.

Equivalent project/Agent CLI:

```bash
ergora project add my-project --repo "$HOME/projects/my-project"
ergora project show my-project
ergora project config my-project
ergora tools list
ergora tools doctor my-project
# JSON example:{"tool":"codex","model":"YOUR_MODEL_ID"}
ergora project bind my-project reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run my-project reviewer --prompt review-request.md --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```


### Project native sessions
To keep an ordinary native development conversation, open “项目会话 / 运行 Agent” on the project overview. Select a historical session and enter the next prompt. The view shows the original role, repository, backend, sandbox, model and continuation availability. A new session chooses its role, optional template artifacts, Skills, memory query and trusted native configuration once. Subsequent turns use the frozen settings and materials. This path retains the role's native workspace permissions and does not create a formal Task or candidate approval. The persistent interface selects Codex on Linux/WSL2; unsupported configurations fail visibly. Actual native execution and resume must be validated with the selected CLI and provider.

```bash
ergora agent run my-project implementer --prompt develop.md --session-intent BIRTH_INTENT --revision CURRENT_REVISION --codex-config native.toml
ergora agent sessions my-project
ergora agent sessions my-project --intent BIRTH_INTENT
ergora agent session my-project SESSION_ID
ergora agent continue my-project SESSION_ID --parent LATEST_RUN_ID --prompt next.md --revision CURRENT_REVISION --intent TURN_INTENT
ergora agent continuation-receipt my-project SESSION_ID --parent LATEST_RUN_ID --intent TURN_INTENT
ergora agent stop my-project SESSION_ID --run EXACT_RUN_ID --intent STOP_INTENT
```

Choose a stable, unique intent for each explicit operation. List and inspect pages accept `--after` and `--limit`; follow their `next_after` manually. After a lost response, retain the original intent and inspect the exact original session/turn before submitting any new work. `agent sessions --intent` observes the original birth intent without invoking an Agent. The console retains unresolved requests in this browser tab's session storage and offers “观察原操作”; it never automatically resends them. `stop_requested`, notification delivery and confirmed process cleanup are separate facts. A turn can continue only when the domain reports `can_continue`; changed configuration or missing cleanup evidence remains visibly blocked. Normal source and HEAD edits are part of development.

Use `agent continue --wait-for-slot --timeout SECONDS` to wait in the foreground when the selected parent still holds the session slot. The wait and the new turn share the timeout. The command reconciles an already reserved intent at entry and after acquiring the slot. Supply the current project revision for a new turn. The original session retains its frozen context across updates to unrelated bindings. An effective change to its role binding, project registration, or correction-suggestion policy requires a new session, including when a changed setting is later restored. Each admitted turn records its selected project revision. Keep the caller running for the wait, and use the exact continuation receipt to reconcile an interrupted call or inspect a concurrent reservation.

For a continuation, the receipt command and Console read one exact original turn using its session, parent and intent. `dispatch` reports `unrecorded` when neither the request packet nor the reservation is visible, `reserved` when the original reservation exists, `attempted` when the original dispatch attempt exists, and `accepted` when its supervision process has accepted the request. An accepted receipt can be read after the process exits. Missing or damaged dispatch evidence is reported as `incomplete` with its reason. An original request packet with no verified reservation reports `incomplete` and `run: null`. The Console keeps that intent pending. Further submission of that intent is refused while the partial evidence persists. A recorded `run` independently reports live or final outcome evidence, or an unknown outcome. An `unrecorded` response can race the original request, so retain the original intent and observe again. The read-only endpoint is `GET /api/projects/ID/agent-sessions/SESSION_ID/continuations/TURN_INTENT?parent_run_id=LATEST_RUN_ID`.

On Linux/WSL2 the same receipt separately reports `native_start`. A successful local child launch records the original immutable request and owner. `running` means the original child identity is live at readback. `started` preserves verified historical launch evidence. `unrecorded` denotes no saved start receipt, including historical turns. A damaged or failed receipt reports `incomplete` while the original dispatch and outcome remain independently readable. Evidence publication runs separately from native cleanup and shares the original stop and deadline. These fields concern the local native Agent process.

The same HTTP operations are `GET /api/projects/ID/agent-sessions` (optional `intent_id`, `after`, `limit`), `GET /api/projects/ID/agent-sessions/SESSION_ID`, and POST `.../continue` or `.../stop`. A continue body contains only `parent_run_id`, `prompt`, `expected_revision`, `intent_id` and optional `timeout`. A stop body contains `run_id` and `intent_id`. Starting a persistent session uses the existing `POST .../agent-runs` with `session_intent`, `expected_revision` and a one-time `codex_config` source. Mutations retain the same-origin and `X-Ergora-Request: 1` contract. Existing single-use run/output history remains readable.

New eligible plain-text native sessions suggest reusable corrections by default. The console shows the effective project preference, whether it comes from the default or an explicit setting, and each original turn's actual availability or unsupported reason. Suggestions use the existing project `AGENTS.md` and the original model turn; template and six-stage outputs retain their own contracts and use the [manual document-correction workflow](../improvement/retrospectives.md). Native workspace permissions still apply; this feature does not isolate arbitrary file writes or grant approval for other document changes.

To opt out for new sessions, save the preference in the session console, or run:

```bash
ergora project config my-project
ergora project correction-suggestions my-project --enabled false --revision CURRENT_REVISION
```

Changing the preference advances the project revision and invalidates the original native session authority. Reload the project and start a new session to use the new setting. `PUT /api/projects/ID/correction-suggestions` accepts exactly `enabled` (a JSON boolean) and `revision` (the current integer revision). The effective configuration reports `correction_suggestions.enabled` and `correction_suggestions.source` (`default` or `project`).

When the original reply contains a valid suggestion, the console immediately shows the project, source, target, lesson, applicability, complete before/after text, full diff and exact scope. **Apply exact project change** submits one explicit confirmation of that preview. **Use only for this task / dismiss** withdraws it without changing the target. A model's approval text cannot substitute for this operator action. A missing, malformed, stale or unsupported suggestion shows its actual reason and creates no follow-up model call.

`GET /api/projects/ID/document-corrections/PROPOSAL_ID` reads lightweight original status and the candidate digest, with no preview body. `GET .../preview?candidate_digest=SHA256` reads the exact sealed preview only when the supplied digest matches. Completed native POST replies already include the full preview; opening an older turn fetches it automatically once for the selected project, control directory, selection generation and candidate digest. Subsequent status reads reuse that immutable body while refreshing current availability and decision status. The body cache never grants apply authority.

POST `.../apply` accepts exactly `revision`, `candidate_digest`, `base_sha256`, `scope_sha256` and the JSON boolean `confirm`; it resolves and verifies the original preview on the host. POST `.../withdraw` accepts only a nonempty `reason`. After a lost decision reply, retain that proposal ID and read its lightweight original status. The console keeps the pending decision in this tab and disables resending it. GET, refresh and status reads never prepare a proposal, invoke a model, apply a change or repair an unknown result.

Pages and CLI share persistent business state. Refresh before saving after revision conflicts. An Agent call's `succeeded` is not formal-task acceptance or review approval. The default reference executor retains its original configuration. Explicitly enable bridging when selected role tools should affect formal tasks; see [Agent selection and formal execution](../agents/backends.md).

## Remote access, recovery and maintenance

The service listens on loopback only. From another machine, use SSH forwarding and open local `http://127.0.0.1:8977`:

```bash
ssh -L 8977:127.0.0.1:8977 user@server
```

Local interfaces require the same origin and custom request header and validate Host. They operate with current-user permissions for trusted projects. Team identity, public hosting and per-Agent OS isolation require separate integrations. If a container cannot provide a namespace sandbox, the application does not automatically disable an Agent's sandbox to make invocation succeed.

The application runs in the foreground. On Linux/WSL2, Supervisor can manage `ergora serve` and each project's `ergora research worker PROJECT`; start with foreground terminals on native Windows. Installation does not automatically execute background tasks, invoke models or start research. After stopping writers, back up complete `ERGORA_HOME` and business Git repositories. During restoration, check actual repository paths and tool logins. Deleting memory does not clear independent backups or past archived invocation inputs.

When developing or resuming on another machine, read [PLAN.md](../PLAN.md) and the active slice's `docs/delivery/` record, then check branch, `git status` and recent commits. Default tests do not call paid models; acceptance of external services and GPU results is recorded separately.

Continue: [Back up and restore the local task stack](backup-recovery.md) · [Submit, observe and recover a development task](../development/run-and-recover.md).
