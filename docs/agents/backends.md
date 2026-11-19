# Select and invoke Agent backends

English · [Documentation](../README.md) · [简体中文](../zh-CN/agents/backends.md)

See the [specialist Agent definition library](../definitions/agents.md) for shareable specialist recipes and the [workflow invocation guide](../definitions/workflows/leaf-calls.md#call-a-prepared-leaf) for restricted single-leaf calls with complete ancestor materials. Project-role bindings and formal six-stage execution retain this guide's entry points.

Templates save objectives, roles, capabilities, artifacts and acceptance requirements; projects save concrete tools. `ergora templates copy` adds `agent-contract.json` alongside the original files without changing frozen reference contracts. Inspect roles:

```bash
ergora templates agents repository-governance
ergora templates agents large-change
ergora templates agents training-optimization
```

Governance and large development provide inspector / planner / implementer / reviewer roles. The executor still owns integrate, verify and trusted work test-results. Training provides experiment-planner / performance-analyst / kernel-tuner, producing proposals, analysis and candidate descriptions respectively. Select native kernel-generation tools in the separate `kernel` layer.

See [Agent CLI installation](configuration.md#install-and-authenticate-agent-clis) for initial Codex / Claude Code installation, authentication and official entry points. These steps assume the selected command is available on the PATH of the shell starting Ergora.

After binding, run `ergora tools doctor PROJECT`. Explicit version/credential/TCP probes use `--probe --timeout 5`; see [diagnostics](../operations/services.md#diagnose-and-repair) for each result, budgets and repair entry points. Existing Codex credentials and a successful actual model task are separate facts, neither automatically granting Agent acceptance.

A Linux unified project can explicitly start selected `temporal/worker/executor/a2a` services through [service management](../operations/services.md#manage-services-explicitly). Services start only when selected. Stopping requires confirmation and actual status observation; the original running stack is not taken over automatically. The managed executor uses frozen role snapshots in this control directory. Use `ergora task list PROJECT` / `task show PROJECT TASK_ID` to [read existing formal tasks' frozen contracts](../development/tasks.md#read-formal-task-contracts), without inferring live Temporal state. The primary entry also [previews, creates and recovers tasks](../development/tasks.md#preview-and-create-formal-tasks), freezing role configuration at creation. `task status` provides [native runtime observations](../development/run-and-recover.md#query-formal-task-run-status). Use the [unified submission/recovery entry](../development/run-and-recover.md#submit-formal-tasks-and-recover-unknown-results), [exact-plan approval](../development/design-and-approval.md#approve-an-exact-plan-and-recover-delivery), [original-run cancellation](../development/run-and-recover.md#request-cancellation-and-recover-unknown-delivery) and [exact-candidate export](../development/evidence-and-export.md#export-an-exact-candidate-and-recover-its-receipt). Tasks born through the legacy entry retain this guide's reference commands.

`control`, `development` and `research` are control-plane SDK [installation profiles](../install/linux.md#choose-an-installation-profile), without installing or selecting a particular Agent. Configure Codex/Claude through [Agent configuration](configuration.md); [mini-swe-agent](#mini-swe-agent) and [ForgeKernel](forgekernel.md) require their own pinned-source environments. Changing profile does not modify existing project bindings.

See the [Windows guide](../install/windows.md#install-and-authenticate-agents) for native installation/authentication. Native role calls support Codex, Claude Code and explicit program/interpreter `.exe` files; `.cmd` / `.bat` launchers are explicitly refused. The mini Bash driver, ForgeKernel and formal six-stage bridge require WSL2/Linux; the formal reference executor additionally needs a trusted Linux container. Keep Codex's native sandbox on Windows; the Linux `current-container` selection is unavailable there.

## Project selection and standalone calls

Select a tool for each role in the console's “Tool bindings”, or use JSON:

```json
{"tool":"codex","model":"YOUR_MODEL_ID"}
```

```bash
ergora project show my-project
ergora project bind my-project planner --binding planner.json --revision CURRENT_REVISION
ergora agent run my-project planner --prompt plan-request.md --template repository-governance
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

`--template` requires the role's actual structured artifacts; omitting it retains ordinary text invocation. Neither grants formal acceptance. Codex uses the role's default CLI sandbox. If the system cannot provide that sandbox, explicitly set `"sandbox":"current-container"` only after accepting the current container/user boundary. There is no automatic downgrade. Claude Code owns its authentication; its review/proposal roles use Read/Grep/Glob with session persistence and extra MCP configuration disabled. Codex remains the default reviewer.

### Set reasoning effort for each Agent

Add `reasoning_effort` to a Codex binding or `effort` to a Claude Code binding, for example:

```json
{"tool":"codex","model":"YOUR_MODEL_ID","reasoning_effort":"high"}
```

```json
{"tool":"claude-code","model":"YOUR_MODEL_ID","effort":"medium"}
```

Set project roles in “Tool bindings” or `project bind`; set specialist instances in their `agent.json.backend` or the formal task's `composition.backend_overrides[实例路径].binding`. Formal tasks freeze the complete configuration. Changing project bindings or publishing an Agent version does not rewrite existing tasks. Parallel review branches can select separate backends, models and effort, following the original DAG and ancestor concurrency quotas.

Codex choices are `low/medium/high/xhigh/max/ultra`; an explicit binding overrides `model_reasoning_effort` from `--codex-config`. Claude choices are `low/medium/high/xhigh/max/ultracode`, projected as native `--effort`. Omitting a field retains the CLI's existing settings; other backends do not expose these fields. Availability depends on the selected model, CLI, account and service. Ergora records explicit requests without estimating or promising equal computation across backends. Claude organization policies may cap effective effort; in JSON mode, relevant warnings may appear only in native debug logs. Requested effort alone does not establish applied effort.

See [official Codex configuration](https://developers.openai.com/codex/config-reference/), [Claude CLI flags](https://code.claude.com/docs/en/cli-reference#cli-flags) and [Claude model configuration](https://code.claude.com/docs/en/model-config). Binding validation refuses unsupported fields. Whether an accepted field works at the model still needs an actual invocation.

### Current configuration evidence and pending capabilities

Keep three facts separate: the requested level in a binding/frozen configuration; the arguments/configuration projected to the native CLI; and native/model behavior actually observed. Codex projects `reasoning_effort` to `-c model_reasoning_effort=...`; Claude projects `effort` to `--effort`. Those arguments establish a CLI request, not an applied model level or a verified provider request. Without native evidence, applied effort remains unknown. Do not infer it from process success, structured output or an accepted binding.

Only explicit binding values and existing defaults are implemented. Unified fixed/preset/planner/automatic selection and its configuration/freeze contract remain future work. Existing workflow presets and native CLI profiles do not implement tuning presets or automatic selection. Model/effort fallback and larger budgets require their own explicit policy; do not silently change them. Claude text-only adds `--safe-mode`; the documented native behavior disables workflows, so an `ultracode` request does not establish an active ultracode workflow. Native precedence/caps and actual application remain separate. See the [backend guide](#set-reasoning-effort-for-each-agent).

DeepSeek's current `context_window`/`max_tokens` populate SDK model-registry capacity descriptions; this is not a verified per-request hard token cap. Retain the original per-call wall-time, reported-cost and continuation semantics rather than treating different native controls as a common budget guarantee.

Backend selection does not enable new design gates or training effects. Current schema2 design-policy registration remains [storage-only with execution unsupported](../projects/registration.md#current-limits-of-design-policy-registration). Inspection-only [source-journal records](../development/design-and-approval.md#store-complete-design-sources-and-reported-answers) do not supply trusted owner approval. Finite training controllers use their [explicit authorization contract](../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization). Existing schema1 task contracts retain their original scope.

### Review a repository using Ergora

Register this or another repository as a review project and select an available reviewer backend different from the actual author's. For example, write `reviewer.json` as `{"tool":"claude-code"}`, then run:

```bash
ergora project add self-review --repo /PATH/TO/REPOSITORY
ergora project show self-review
ergora project bind self-review reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run self-review reviewer --prompt review-request.md --template repository-governance --timeout 900
ergora agent runs self-review
ergora agent output self-review RUN_ID
```

In `review-request.md`, give original requirements and the exact candidate SHA. For uncommitted work, separately list complete changes, new files and digests. Supply actual validation commands/results and unverified scope, and specify read-only inspection boundaries. If specialist instructions are needed, obtain them with `show --material` in the [definition library](../definitions/agents.md) and explicitly include them. Definitions/inherited resources are not loaded automatically here. Backends retain their own login/environment; do not include keys in the request.

Allow read methods the selected backend actually has. Codex typically inspects source with read-only shell commands; Claude can use Read/Grep/Glob. Do not forbid all commands while listing only another backend's proprietary tools. Alternatively attach complete new-file contents and check input digests. Recheck material readability after changing backend. A request-changes result caused by inability to inspect is not a confirmed source defect.

This template requires `review-report`, `handoff` and explicit `approve/request-changes`. Inspect original structured results/digests in run records and resolve each finding. Process success, structural validity and review approval need separate checks. Failure/timeout is not a pass. Retain reasons for same-backend fallback. A standalone independent call produces no formal workflow approval or trusted acceptance.

### Custom commands

An ordinary `{"tool":"command","argv":["/path/to/program"]}` continues receiving plain stdin text. Formal stages or `--template` calls require:

```json
{
  "tool": "command",
  "argv": ["/path/to/agent-wrapper"],
  "protocol": "stage-json-v1",
  "capabilities": ["repository-read", "plan-write"]
}
```

stdin is `{schema_version, role, prompt, result_schema}`. stdout must contain only one JSON object matching result_schema; write diagnostics to stderr. The schema requires summary and required artifacts, plus explicit approve / request-changes for review. Declared capabilities must cover the role's requirements. They declare compatibility, without proving tool quality or isolation. Execute commands through argv; templates embed no commands.

### mini-swe-agent

```bash
bash scripts/install-agent.sh mini-swe-agent
```

Pinned source and its independent venv default to `~/.local/share/ergora-tools/mini-swe-agent/`. Put that Python's absolute path in the implementation-role binding:

```json
{
  "tool": "mini-swe-agent",
  "python": "/YOUR_HOME/.local/share/ergora-tools/mini-swe-agent/.venv/bin/python",
  "model": "YOUR_PROVIDER/YOUR_MODEL",
  "step_limit": 30,
  "cost_limit": 3.0
}
```

The provider's environment variables supply authentication. mini supports implementation, without serving as a read-only independent reviewer. Its driver uses native LiteLLM tool-call models and consistent Bash tool instructions, retaining the trajectory. On completion it writes final text to the submission file in the run archive, then uses the prompted command to submit the body to the same structural validation. Empty submission fails. Shell actions remain in the outer monitor's process group under the overall task timeout; one action can consume all remaining time. Costs use upstream reports. One API request may exceed the remaining budget; this is not a prepaid-spend ceiling. Installation and CPU SDK checks do not establish model quality.

## Maintain built-in component descriptions

`src/ergora/data/components.json` supplies built-in roles/tool descriptions at catalog `schema_version: 1`. Roles save capability requirements, display information and recommended bindings for new projects. Components save implemented driver names, capabilities, operations, platforms, probe methods, configuration fields and installation sources. `ergora tools list` and Web bootstrap return these descriptions; binding forms are generated from their fields. ForgeKernel/mini installers also read pinned sources/commits from this file.

To reuse the existing `command` driver, add a packaged component with `implementation: "command"`, matching `tool.const` and existing configuration fields. Templates/pages need no vendor-specific branch. Rebuild/install to apply the change. The same implementation still checks ordinary commands, `stage-json-v1`, role capabilities and trusted acceptance. Actual drivers, cleanup and new operation semantics require code adaptation/contract acceptance; adding a description does not support a new SDK automatically.

Forms currently support string, number, integer, array and enum. `x-ergora-*` fields supply only form enum labels, platform defaults, project task-queue defaults and input steps. Descriptions are not injected into saved bindings/run snapshots and do not change Agent runtime defaults. Core structural validation uses the same configuration JSON Schema; business owners retain role, path, URL and trusted-gate checks. See [contracts and identities](../architecture/contracts/formats.md) for types, error paths and compatibility. The catalog loads no user Python plugins or key values.

See [fixed attachment reads through task MCP](../definitions/workflows/leaf-calls.md#read-fixed-attachments-through-task-mcp) for independent composition leaves' default text-only and optional task-mcp modes. The latter reads only selected leaf/ancestor fixed resources, without ambient tools. Native tool lists, Claude bare-authentication differences and Linux support follow that mode's contract. Ordinary agent run/formal stages do not adopt it automatically.

Before independent composition calls, use `composition check-input` to inspect [capabilities and permission chains](../definitions/workflows/leaf-calls.md#inspect-capabilities-and-permissions-before-invocation). The report combines current backend contracts with original admission. It probes no authentication and starts no services. An actual call repeats admission and saves a policy with the same structure. A new restricted backend must implement composition_policy rather than merely declare a mode name.

## Writable calls for specialist work instances

Formal `work-units-v1` maps each original unit to a frozen implementer instance; see [specialist executors and original work units](../definitions/workflows/contracts.md#specialist-writers-and-original-work-units) for configuration/support. workspace-task-mcp reuses the same backend Interface, fixed resource service, native process supervision and call records. Codex explicitly enables workspace shell/file tools while disabling ambient rules, Skills, plugins, hooks, web and implicit sub-Agents. Reasoning configuration still consumes only whitelisted fields. Policy separately records native tool configuration and the absence of OS/network isolation; permission instructions are not enforced isolation.

Invocation evidence includes original formal-call, complete input snapshot/prompt, actual argv/cwd/stdin SHA, native MCP receipts, structured result and final original work receipt. The trusted Executor owns commits/deterministic checks. This workspace mode currently supports only explicitly selected current-container Codex/Linux/WSL2. Claude retains supported read-only review modes; unverified new writable compositions are refused. Changing mode on an old independent read-only entry cannot grant write authority.

## Implementation and review

Bind `{"tool":"codex","model":"MODEL_ID"}` or `{"tool":"claude-code","model":"MODEL_ID"}`. Omit the model field to use the tool's own configuration; authentication uses the tool's environment / login. For a custom tool, use `{"tool":"command","argv":["/path/to/tool","arg"]}`: the prompt is stdin, the working directory is the registered project root, and no shell concatenation is used. Relative executable paths resolve against the project root.

`ergora agent run` starts an independent process each time. Codex uses ephemeral sessions, and reviewers **default** to a read-only sandbox; saved bindings can explicitly override this with another supported sandbox. On Linux, `current-container` uses the current trusted container and user permissions. Before invocation, use `ergora project config PROJECT` to check the reviewer's effective binding and its source; invocation records also preserve that binding and a configuration snapshot. Claude reviewers restrict built-in read tools and use a strictly empty MCP configuration. These restrictions still depend on tool implementation and the actual user / container environment; they do not prove operating-system isolation. The new entry point does not automatically remove the sandbox to make execution succeed.

Ordinary `agent run` invokes tools in the registered project directory without the formal workflow's outer checkout / before-and-after HEAD monitoring. The formal six stages additionally check that read-only stages did not modify the candidate workspace and verify candidate and independent review evidence. Assess independent processes, backend read-only settings, formal candidate gates, and operating-system isolation separately; none proves the others.

Exit codes, timeouts, and SIGINT cancellation are retained; same-process-group descendants are cleaned up when the command ends. Tools must run as controlled foreground commands. A running record left after machine failure is not a reliable recovery terminal state and requires operator reconciliation; formal workflow recovery uses the reference Temporal implementation. A succeeded return proves only a successful command exit, not formal code review approval.

Continue: [Configure and authenticate Agents](configuration.md) · [Invoke and inspect one frozen workflow leaf](../definitions/workflows/leaf-calls.md).
