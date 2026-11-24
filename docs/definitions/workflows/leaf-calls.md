# Invoke and inspect one frozen workflow leaf

English · [Documentation](../../README.md) · [简体中文](../../zh-CN/definitions/workflows/leaf-calls.md)

## Prepare complete single-leaf input

Use an exact instance path to prepare an independently verifiable input bundle. First complete the [kernel-delivery dependency imports](compose.md#run-the-example). Run these commands from the source checkout containing [the illustrative grant](../../../examples/composition/preview-grant.json), or replace that grant path with your own explicitly reviewed file. Create your UTF-8 task file `review-task.txt`, then run:

```bash
ergora composition prepare kernel-delivery 1.0.0 root/review/structure/review --grant examples/composition/preview-grant.json --task review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
ergora composition verify-input ./prepared-review
ergora composition verify-input ./prepared-review --material
```

Preparation still checks current Agent admission. It neither calls models, executes predecessors/ports nor approves workflows. Operators explicitly supply the task; to send execution results to a reviewer, for example, supply the corresponding task materials yourself rather than treating this bundle as verified automatic data flow.

Input contains `request.json`, complete `composition.json`, original `task.txt`, complete `prompt.txt` and every exactly referenced package in `assets/`. Skill-directory scripts/attachments are saved together; complete resource bodies still load root→leaf. `verify-input --material` recompiles the bundled static composition and checks the complete user prompt. It remains usable after source State deletion, without depending on the current backend catalog. Verification executes neither Skills nor backends.

`max-prompt-bytes` must be 1–1,000,000, counting UTF-8 bytes of the complete user prompt; excess is refused without truncation. This does not establish model-token capacity or room for additional backend system prompts. The complete input bundle allows at most 10MB/500 files, 1000 directories and 48 levels, checked during copying too; failure publishes no partial bundle. Save only to a new directory outside immutable definition libraries. Atomic no-overwrite publication supports Linux (requiring renameat2) and Windows, failing explicitly when unsupported. Whole-tree consistency is checked before/after verification; keep input directories stable, as this does not isolate processes belonging to the same user. The input digest covers task, composition, prompt and every asset; it establishes content consistency without authenticating authors or granting execution. Definition-package limits on cross-platform executable bits and same-platform byte preservation also apply.

Input metadata uses [composition-input v1](../../../src/ergora/data/schemas/composition-input-v1.json), retaining referenced Agent v1 and Workflow v1/v2 formats inside the bundle. Actual calls pass admission again through the separate entry below.

## Call a prepared leaf

First [register the project](../../projects/registration.md) and install/authenticate the selected [Agent CLI](../../agents/configuration.md#install-and-authenticate-agent-clis). `prepared-review` is the complete input bundle prepared above:

```bash
ergora composition run-input my-project ./prepared-review --timeout 300
ergora composition run-input my-project ./prepared-review --backend codex --backend-reason "Selected Codex for this call" --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --backend claude-code --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

The exact leaf definition supplies the default backend; `--backend` and `--model` override this call only. Choose a model again when switching backends rather than retaining another backend's model name. Prefer different execution/review backends; when Claude is unavailable, explicitly select Codex/ChatGPT and record why with `--backend-reason`. Failure does not silently retry another backend. Timeout is 1–3600 seconds; exit 0 means success, 1 means model failure/timeout/startup configuration or structural error, and 2 means input-bundle or mode-admission error.

Alternatively, configure the [DeepSeek Harness read-only backend](../../agents/deepseek-harness.md#deepseek-harness-read-only-leaf-backend) in the exact leaf definition, retaining the full interpreter, model, API service and credential-variable reference; avoid an incomplete `--backend` override. It supports the two read-only modes in this section. Native workspace execution, formal-task recovery and persistent sessions remain unsupported for this backend. Persistent project sessions follow the [supported Codex session contract](../../agents/deepseek-harness.md#project-native-development-sessions).

The default mode is `text-only`. Complete ancestor instructions, context, Skill `SKILL.md` bodies and the original task enter the model. Skill attachments remain in the snapshot, but this mode has no file/command/Web/MCP tools and cannot read other materials by path or edit the project. Include candidate code and required evidence in the task body for review. Leaves requesting write, shell or tool-network permissions are refused before invocation; the example implementation leaf, for instance, cannot run through this mode. Native structured-response or interactive tools may remain.

Runs use a new empty cwd, native CLI rule/tool-disabling options and independent sessions. These constrain model tools without providing OS/network isolation; they do not isolate user processes or model-service communication itself. Backends lacking required options fail explicitly. Codex can receive explicit reasoning configuration through `--codex-config`: only model/provider/reasoning effort/service tier and provider fields such as URL and credential environment-variable references are consumed. Tool, MCP, Skill, approval and sandbox settings there do not override this mode. Omit the file when using native Codex login; Claude uses native authentication or corresponding environment variables. Do not put credentials in definitions or task bodies.

Each run saves a completely verified input copy, a new empty working directory, complete prompt, actual argv, stdout/stderr and structured results under State's `runs/`, reusing existing Agent run lists/output and complete backups. Records bind input digest, project revision, requested/actual binding and override reasons. Run lists include only resource identities/provenance; inspect complete bodies as needed against the returned `input_path` with `composition verify-input --material`. Read the returned `result` file for `summary` and `artifacts.response`; reviewers additionally provide `approve/request-changes`. Process success and review approval are evaluated separately.

Operators supply single-leaf tasks; graph predecessors and ports do not execute. The original input remains `execution_authorized: false`, and this call creates no formal candidate/approval. Formal serial/parallel scheduling, candidates and approvals use the [formal review](contracts.md#data-ports-for-formal-read-only-review) and [work-unit](contracts.md#specialist-writers-and-original-work-units) contracts.

## Read an original composition run by exact ID

`agent runs` lists only the latest 100 records; `agent output` provides bounded stdout/stderr. To obtain an original composition run's complete input and structured result, use its exact ID:

```bash
ergora composition inspect-run my-project RUN_ID > ./original-run.json
ergora --home /path/to/control-directory composition inspect-run my-project RUN_ID \
  --max-result-bytes 16777216 > ./original-run.json
```

This reads the original record by project/ID and the complete input, invocation prompt and result in its original `runs/` slot under the current control directory. It requires no source repository, backend program, authentication or network. After copying the complete control directory, historical metadata's absolute paths remain unchanged, while reading uses the original slot under the new directory. Do not copy only the database and discard run files. Ordinary old `agent run` still uses `agent output`; this complete reader targets original composition runs such as `composition run-input`.

Returned `run` preserves original status and actual backend/reason. `input.available` verifies complete input against its original digest/request/prompt identity; `prompt.available` independently verifies the original invocation prompt's SHA/byte count against its record. When input is also verifiable, the frozen prompt is compared byte for byte and `prompt.input_compared: true` is set. Unverifiable input leaves this false without preventing preservation of invocation-prompt identity that still matches its record. `result.available` verifies the complete original result SHA and reads its JSON, placing the body in `result.document` without truncating it to a stdout preview. Default result capacity is 8,388,608B; excess explicitly reports unverifiable and can be reread with a larger positive integer capacity. Original saved content remains unchanged.

For a collected text-only graph leaf on Linux/WSL2, `process_start` can report the historical direct child's PID, start ticks and boot ID. The reader checks the receipt against the original run, project revision, instance, frozen preview, saved input and invocation prompt. Check `process_start.state` for unavailable evidence. The process identity describes the original launch.

Each missing item, identity mismatch or excess gets its corresponding `error`; other verifiable materials and the original run status remain visible. Successful observation reads return 0; scripts must inspect each `available` and `run.status`, rather than treating exit 0 as completed review. This reader neither reruns current backend/schema admission nor upgrades historical results to formal approval; downstream reports interpret advice through the trusted reviewer contract.

Original invocation prompts come from shared backend storage at `protocol/prompt.txt`. Actual transport may use stdin or backend request files, so this observation cannot certify stdin delivery for every backend. Read original native history through the [backend guide](../../agents/backends.md). Preserve and reconcile failures/unknowns first rather than automatically resending model calls.

## Inspect capabilities and permissions before invocation

Before actually invoking a model, check the same input, backend and mode:

```bash
ergora composition check-input my-project ./prepared-review
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend claude-code --backend-reason "Independent review backend"
```

This command shares current admission with `run-input`. The result's `policy.permission_ceilings` lists the complete structural permission chain from supplied grant through root to leaf; `requested_permissions` is the leaf request, and `context.resources` retains every ancestor/self resource source. Read paths are permission ceilings; listing workspace does not automatically supply project-file tools. Support for complete inline materials and fixed attachments is displayed separately; text-only does not claim readable attachments.

`policy.capabilities` divides support into `enforced` (mechanisms implemented by trusted CLI/task-URI services), `advisory` (requests/prompts without enforcement guarantees) and `unsupported` (no corresponding capability). Codex actually sends a read-only request without claiming host isolation; Claude disables native tools without additionally requesting an OS sandbox. Task MCP provides only list/read for fixed declared materials; live workspace access, writes, shell, tool-network origins and external MCP remain unsupported. Infrastructure inference HTTP, stdio processes and log/state writes still exist.

This is an implementation contract and current admission report; it starts no server/model, creates no run and checks neither CLI version nor authentication. With Codex's `--codex-config`, check/run share reasoning-field parsing; unreadable files, invalid TOML, invalid provider tables or unencodable fields are refused before run creation. It does not verify provider acceptance, model availability or adequate capacity; Claude ignores this Codex-specific option. Task-mcp checks only Linux and top-level SDK presence; actual SDK compatibility/connection is preflighted at runtime. A successful check is not formal approval, and `formal_execution_authorized` remains false. Actual execution reruns admission and saves the same `policy` structure rather than treating an earlier check as an authorization token.

## Read fixed attachments through task MCP

On Linux/WSL2, install the optional dependency in the same Python environment that runs Ergora. From the repository root:

```bash
python -m pip install '.[task-mcp]'
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend claude-code --timeout 300
```

This mode retains complete inlining of ancestor instructions, context and Skill guidance, additionally providing the model with the `ergora_task` service's `list` and `read` tools. Use `list` to inspect virtual URIs, then `read` for this leaf's and all structural ancestors' declared materials/Skill attachments. Ordinary bodies expose only declared files; Skills expose their complete frozen directories. Sibling templates, undeclared neighboring files, the entire input asset library and live project files remain unavailable. Materials do not execute as programs; write, shell and tool-network requests are still refused before invocation.

Each call produces a separate [task-mcp-scope v1](../../../src/ergora/data/schemas/task-mcp-scope-v1.json), retaining original bytes, digests and provenance. Limits are 10MB/500 files and 16MB for the complete serialized scope; excess is refused. After verifying scope, the service queries memory only and never treats model-supplied URIs as host paths. Fixed-resource reads on Linux use non-link-following file descriptors at every level, refusing symlinks/hardlinks/special files. On Windows, this new mode currently gives Linux/WSL2 guidance; existing Windows features remain available.

`list(path="",offset=0,max_entries=100)` pages authorized URIs, with up to about 64KiB of entry metadata per page; `read(path,offset=0,max_bytes=65536)` pages bytes. Responses include file size, SHA256 and `next_offset`; decodable chunks use UTF-8, while binary chunks or encoding-boundary splits explicitly use base64. Follow `next_offset` for complete content instead of treating one tool response as a whole directory or file.

### Verify complete attachment reads

When a task requires complete inspection at every level, explicitly require it in the task file: page through every URI, then read each from offset 0 to `next_offset:null`, including all ancestor instructions/context, every Skill's `SKILL.md` and every referenced attachment. If a UTF-8 window splits a multibyte character and returns base64, reread the same offset with smaller `max_bytes`, then advance through successful text pages. Handle actual binary attachments as complete base64 bytes without executing them. Empty directories remain in the complete bundle without becoming readable files; ordinary undeclared attachments do not automatically enter task scope.

Neither successful execution nor final `approve` proves complete attachment reading. Compare frozen input, `task_mcp.scope` URI/size/SHA/provenance and actual list/read responses in this call's native events. Successful pages for every file should continuously cover original bytes; retain failed/repeated windows. Scope records available materials; native read records show which bytes the model actually requested in this call. Prepared input remains usable after the source library moves; verify and retain both source library and complete input first to avoid deleting the only copy.

MCP configuration is generated for this call only. Codex selects only this server's two tools; native MCP resource discovery/response or interactive entries may remain. The service registers no additional resources/templates/prompts. Claude uses `--bare --restricted`, empty native tools and strict explicit MCP; bare mode uses only its supported API-environment authentication without reading ordinary OAuth/keychain credentials. Users requiring OAuth login can continue using text-only or set backend-supported API environment variables for this mode; credentials need not enter definitions, scope or chat. Backends do not automatically share model names or authentication.

The run record's `task_mcp` contains frozen scope identity, preflight results and this call's native connection receipt. Preflight and native receipts are separate; the latter requires an actual SDK-successful `tools/list` for this scope with exactly list/read tools. Old handshakes and newer handshake-free requests record their actual protocol and `handshake_observed` separately. Missing actual service receipts fail the run even when final model JSON succeeds. Scope/receipts follow complete State backups, while run lists retain only summaries; this provides no OS isolation or expanded template/project authorization.

Execution also checks task-MCP transport errors already reported by this native backend. Even if the model later reconnects and returns a valid result, this run remains failed with original stdout retained. Server-side domain refusals such as unknown resources or invalid URIs allow correction and continuation; they do not equal connection failure. In this mode, Claude saves original stream-json events and extracts the final structured result; ordinary native/text-only output handling remains unchanged. This check provides no continuous heartbeat and cannot detect silent disconnection without later calls or native error events.

Continue: [Select and invoke Agent backends](../../agents/backends.md) · [Inherited resources, permissions and static budgets](permissions.md).
