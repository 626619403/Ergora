# Backend runtime options: native controls and Ergora exposure

English · [简体中文](2026-11-16-backend-runtime-options.zh-CN.md)

Read-only research, 2026-11-16. Product baseline: `c540939d3b3f38f3851b0de965c9cd0f969eea77`; documentation HEAD when inspected: `04af2344239306cb00458e89f81258093235f049`. This report proposes configuration work; it does not add or certify a feature.

## Findings

Useful options beyond model/effort exist. The first candidates are Codex service tier and response verbosity, Claude finite turn/estimated-cost limits, and an explicit DeepSeek SDK reasoning/output-limit contract. Context/compaction, provider retry behavior and session changes need separate treatment because they affect retained material, cost or recovery. Keep backend-specific semantics and validate the actual selected model/client. ([C1], [A1], [D1], [E1])

The user's four selection modes are **fixed / preset / planner / automatic**. Ergora currently supports explicit binding values and existing defaults. A reusable tuning preset, planner proposal and automatic task-based selection are future work; the repository's workflow presets and native CLI profiles do not implement those modes. Their design belongs to the [reasoning/parallelism plan](../plans/2026-11-16-agent-reasoning-and-parallelism.md). ChatGPT accessed through Codex/provider configuration is not another registered `AgentBackend`. ([E1], [E2])

## Evidence and terminology

The installed programs reported `codex-cli 0.167.1` and `Claude Code 2.1.312`. Only `--version`, `--help` and `codex exec --help` were invoked. Official pages were fetched on the research date; public upstream sources use the exact pins already declared by Ergora. Documentation, local help, source construction and an actual model call establish different things. A missing help flag is not automatically unsupported: Claude's official CLI reference explicitly says its help is incomplete. No model, login, installation, private configuration or credential/environment snapshot was read or run. ([A1], [E2])

Ergora's `native` mode still launches a **non-interactive subprocess**: `codex exec` or `claude --print`. It does not mean an interactive terminal session. `text-only` and `task-mcp` are restricted composition modes; the latter exposes fixed authorized resources. `workspace-task-mcp` is the explicit trusted Linux Codex workspace mode. Formal task execution also includes frozen input, the original executor/Temporal lifecycle and candidate-bound checks; a native CLI feature alone does not implement that contract. ([E1], [E3], [E4])

|Backend|Currently exposed configuration|Admitted surface and relevant boundary|
|---|---|---|
|Codex|`model`, `reasoning_effort`, `sandbox`|Native, restricted text/MCP, and trusted workspace-MCP. Internal/reference `codex_config` is a separate path, with a restrictive filter for composition calls|
|Claude Code|`model`, `effort`|Native and restricted text/MCP; restricted turns are currently fixed by the adapter. No workspace-MCP implementation|
|DeepSeek Harness|`python`, `model`, `base_url`, `api_key_env`, `api`, `context_window`, `max_tokens`|Pinned SDK/runtime `0.2.2rc2`; Linux read-only text/MCP leaves. No native/workspace mode; one explicitly authorized standalone MCP continuation has its own frozen source contract|
|mini-swe-agent|`python`, `model`, `step_limit`, `cost_limit`|Pinned implementation-role Linux/native driver. No restricted composition mode|
|ForgeKernel|`checkout`, `python`, `task`|A kernel support-layer campaign, not an AgentBackend. Local delivery only; native task/global configuration remains a separate source of controls|
|Structured `command`|`argv`, optional `stage-json-v1` and declared `capabilities`|Native subprocess; structured formal stages require that protocol and the role's capabilities. Arbitrary argv is not admission to a restricted mode|

The table is derived from the current component schemas, adapter mode lists and actual drivers, not inferred from upstream marketing. Unknown properties are rejected by these binding schemas. ([E1], [E2], [E5], [E6], [E7], [E8])

## Codex: candidates and current behavior

Codex officially supports config overrides and native profiles. Ergora's reference path can supply a TOML file internally. In restricted modes, `_options` retains only `model`, `model_provider`, `model_reasoning_effort`, `service_tier` and a narrow provider transport/credential-reference subset. It then forces its tool/resource restrictions. Additional native argv is rejected in those modes. Ordinary project/definition bindings do not expose an arbitrary config dictionary. ([C1], [C2], [E1], [E3])

|Control|Native semantics|Current Ergora exposure and consequence|
|---|---|---|
|Model and effort|`model`, `model_reasoning_effort`; supported effort names depend on the active model/client|Already explicit binding fields. The binding's effort overrides that key from the supplied reference TOML. Omission preserves existing defaults; schema acceptance does not prove provider acceptance. ([C1], [E1])|
|Service tier|`service_tier`; `fast` maps to request tier `priority`, with other advertised tiers model-dependent|Already retained from a supplied internal/reference config in restricted calls; no binding/UI field. Strong candidate for an explicit optional field. Availability, latency and pricing require provider/account evidence; it is independent of effort. ([C1], [E1])|
|Response verbosity|`model_verbosity` uses `low/medium/high` where supported; the config reference describes a Responses-model verbosity control|No binding field; removed by the restricted-config filter. Native/reference config can carry it. It adjusts desired response detail, not a hard token/cost ceiling. Admit per model rather than applying it to every provider. ([C1], [E1])|
|Reasoning summary|`model_reasoning_summary` chooses summary presentation|Not exposed in bindings or retained in restricted config. It is separate from reasoning depth and is not a complete internal reasoning transcript. ([C1], [E1])|
|Context and compaction|`model_context_window`, `model_auto_compact_token_limit` and its scope control context sizing/when compaction starts|Native config surface; filtered out of restricted calls. Configuring a number does not enlarge a provider's actual context. Compaction can change later model-visible history; preserve the original frozen material and record this policy if admitted. ([C1], [E1])|
|Tool-output bounds|`tool_output_token_limit` and per-MCP-tool output limits concern tool results|Not an overall response token cap. Restricted MCP currently has its original fixed transport/tool contract; do not relabel these as final-answer length. ([C1], [E1])|
|Provider retries and stream idle timeout|Provider-specific `request_max_retries`, `stream_max_retries`, `stream_idle_timeout_ms`|Not retained by the restricted provider whitelist. Changing them affects latency/attempts; the existing outer wall budget still owns total time. Inference retries do not authorize replaying a task/job start. ([C1], [E1], [E3])|
|Parallelism|Native agent thread controls are independent of workflow DAG concurrency|Restricted calls disable native multi-agent behavior. Do not use native thread settings to bypass the workflow's concurrency/resource permissions. ([C1], [E1])|
|Profiles and sessions|Native `--profile` supplies a config layer; `resume/fork` manage native session identity|Ergora uses `--ephemeral`; native session resumption is not its formal task recovery API. A CLI profile can include much more than tuning and is not an Ergora frozen tuning preset. ([C2], [C3], [E1])|

No documented universal Codex CLI `temperature`, `top_p`, per-run dollar cap or general maximum-agent-turn flag was established by the inspected CLI/config references. Do not infer them from similarly named Responses API parameters. The current wall timeout and formal budget are existing Ergora controls, not native dollar/turn limits. ([C1], [C2], [E3])

## Claude Code: candidates and current behavior

The adapter always uses `--print` and `--no-session-persistence`. Text-only also adds `--safe-mode`, which disables workflows. ([A1], [E1]) Restricted calls suppress user/project/local setting sources, select explicit tools and a strict MCP configuration, and set `--max-turns 3` for text-only or `24` with task MCP. MCP mode also uses `--bare`; its authentication/runtime conditions differ from an ordinary interactive login. There is no current generic Claude argument/settings passthrough. ([A7], [E1])

|Control|Native semantics/version evidence|Current Ergora exposure and consequence|
|---|---|---|
|Model and effort|`--model`, `--effort`; the documented set includes `low/medium/high/xhigh/max/ultracode`, subject to model/account limits|Already explicit binding fields. Local help lists the ordinary levels but not every documented special value; help alone does not establish that value's runtime availability. ([A1], [A2], [E1], [E2])|
|Effective effort and caps|`CLAUDE_CODE_EFFORT_LEVEL` outranks `--effort`; `maxEffortLevel` caps the result. Per-model caps require v2.1.267+|A requested binding value need not equal applied effort. Above-cap warnings go to debug logs in JSON/stream-JSON runs, so the current structured result does not by itself prove applied effort. No environment values were inspected. ([A2], [A3], [A6])|
|`ultracode`|The flag requests `xhigh` plus the ultracode behavior; v2.1.203+ and model/account eligibility apply|Do not place it on a portable numeric effort ladder or translate it to Codex `ultra`. In the current text-only mode, the documented native `--effort ultracode` behavior has ultracode off and effort up to `xhigh`, subject to native precedence and caps; actual application was not tested. Record separate requested/resolved/native-observed facts. ([A1], [A2], [E1])|
|Fast mode|`fastMode`/`--settings` and `/fast` provide native speed/cost behavior on eligible models/accounts; print-mode support is documented from v2.1.205|Not exposed by the adapter. An explicit typed fast-mode option is a possible later addition; arbitrary settings would also admit unrelated behavior. It is not the Codex service-tier string under another spelling. ([A4], [E1])|
|Maximum turns|`--max-turns` limits agentic turns in print mode; without it the native default is unbounded. Queued stream-JSON input can begin another turn with a fresh limit|Already fixed at 3/24 in restricted modes, not user-configurable; native mode does not add this flag. A user limit must preserve mode/resource completeness and the outer task budget. Hitting the limit cannot be treated as a valid finished review. ([A1], [E1])|
|Estimated API spend|`--max-budget-usd`, print-only; v2.1.217+ for documented subagent enforcement|Not exposed. Client estimates can differ from a bill and overshoot the cap; restored earlier-run totals do not count toward the new invocation's cap. Useful as an additional bound, never the cross-recovery authoritative budget. ([A1], [A5])|
|Output tokens|`CLAUDE_CODE_MAX_OUTPUT_TOKENS` limits most requests; native model caps may reduce it and it changes context headroom|No explicit binding field; the process may inherit an operator environment. This is not verified per-call freeze/observation. A later adapter-specific field must record requested/capped/unknown values without collecting secret environment snapshots. ([A3], [E3])|
|Thinking-token budget|`MAX_THINKING_TOKENS` concerns older fixed-budget thinking behavior; adaptive models ignore positive token counts under their documented conditions|Not a universal effort replacement or an extra independent reasoning allowance. Keep this a model-specific advanced option, not a portable slider. ([A2], [A3], [A5])|
|Compaction|`--autocompact`, `autoCompactWindow`, per-model settings and `CLAUDE_CODE_AUTO_COMPACT_WINDOW` have native precedence; CLI flag support v2.1.221+|Not exposed. Model/context limits and environment precedence must be represented; changing compaction affects history and reproducibility. ([A1], [A2], [A3])|
|Timeouts|`API_TIMEOUT_MS` bounds individual response-header/request waits; Bash timeout variables bound tool commands|These are not the complete model invocation's wall budget or proof of stopped descendants. Preserve the original process owner and formal cancellation/recovery. ([A3], [E3])|
|Fallback models|`--fallback-model` can select another model on overload/unavailability|Not added by Ergora. It changes actual model identity and potentially cost/quality; requires an explicit frozen fallback policy and receipt semantics before adoption. Never silently downgrade an unknown effort/model. ([A1], [A2], [E1])|
|Output style, parallel agents and resume|Native settings/flags can change role instructions, subagent behavior, tools or session identity|These are not response-length tuning. Current adapters retain their prescribed schema/tool controls and disabled session persistence; formal recovery is through the original task owner. ([A1], [A6], [E1], [E3])|

The inspected Claude CLI does not establish generic CLI `temperature`/`top_p` tuning. API or SDK request parameters are not automatically `claude --print` options. An operator's ambient native configuration is also not an explicit, frozen Ergora field. ([A1], [A3], [E1])

## Other integrated tools

|Tool|What the pinned upstream actually offers|Current integration and smallest relevant owner|
|---|---|---|
|DeepSeek Harness|The SDK initialization accepts optional route-owned `reasoning_effort` and per-request `max_tokens`, in addition to provider/model. Unsupported effort is rejected before a prompt; request timeouts do not bound subsequent activity|Current binding exposes `context_window`/`max_tokens`, but the driver writes them as model-registry `contextWindow`/`maxTokens` and does not pass the optional SDK initialization controls. Establish registry capacity versus per-request cap semantics before claiming a hard request cap. Candidate work belongs in the DeepSeek binding/driver and original frozen call/continuation contract. ([D1], [D2], [D3], [E2], [E5])|
|DeepSeek provider route|The pinned pi-ai adapter declares model-specific reasoning levels, compatibility and retry behavior. `off` can omit the wire parameter and leave gateway defaults active. SDK profiles, homes and patches also select tools and persistence|Ergora fixes `sdk-minimal`, removes native shell/file tools, disables retries/reconnect in its selected route and permits only fixed task MCP when requested. Do not expose arbitrary profiles/patches or import headless/full-SDK features as this adapter's support. Service priority/sampling compatibility needs that exact route's proof. ([D1], [D2], [D4], [E5])|
|mini-swe-agent|Pinned `AgentConfig` has step/cost/wall-time limits; the LiteLLM model has provider-specific `model_kwargs`, cost tracking and retry behavior|Ergora already exposes steps (default 30) and reported USD cost (default 3); cost is checked before the next model query and one query can exceed the remainder. The driver supplies outer timeout as wall time and fixes `model_kwargs` to `drop_params=True`. No user sampling/effort passthrough exists. Future typed provider controls belong in this driver/schema; silently dropped unsupported parameters would defeat an “applied” claim. ([M1], [M2], [E2], [E6])|
|ForgeKernel|At the pinned commit, native task/global TOML controls teacher/student backend/provider/model/effort/turn timeout, loop hours, maximum meta rounds and reference-generation hours|These are already native task-file controls, not new project Agent fields. Ergora binds paths, checks the exact source and hashes three global config files per campaign. Keep a new option tied to native campaign/config identity and original recovery; the native judge remains candidate-generation evidence. Owner: `kernel` plus the existing Forge driver. ([F1], [F2], [F3], [E7], [E8])|
|`command`|Its argv may select options of the chosen executable; there is no universal model/provider contract|Already configurable argv; plain text or `stage-json-v1` stdin with structured output as required. New semantics must be documented by that actual command, preserving `Invocation` timeout/schema/capabilities. This is not a shortcut around restricted-backend admission. ([E1], [E3])|

The mini and Forge sources are pinned to `04d809ceab9df28f9adaed044884180159172930` and `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`; DeepSeek sources use `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`, matching the existing `0.2.2rc2` integration. Newer upstream features cannot inherit this admission. ([E2], [M3])

## Recommended order

|Priority|Reviewable candidate|Acceptance boundary before product claims|
|---|---|---|
|P0|Requested/resolved/native-observed option records for existing model/effort, with backend/client/model support evidence|Keep omitted/default values distinct, record precedence/cap/unknown, freeze the resolved request before dispatch, preserve original input/results on recovery. Read an effective value only from a defined native source; never infer it from argv or a successful outer JSON envelope|
|P1|Explicit optional Codex service tier, then verbosity/summary presentation|Reuse `CodexBackend._options` and binding metadata. Per-mode allowlisting, real selected-model acceptance and original output/schema/cancellation checks; no generic config expansion|
|P1|Explicit Claude turn limit and estimated-spend cap|Reuse the adapter's print-mode flags. Preserve existing mode ceilings/completeness until separately admitted, report truncation/limit failure, and prove cross-task/recovery budgets remain with their original owner|
|P1|DeepSeek route reasoning and output-limit semantics|Reuse the pinned SDK's existing initialization contract. Verify supported levels/caps on the exact route and preserve frozen patch/source/continuation compatibility; do not claim registry metadata alone enforces a request limit|
|P2|Claude fast mode and output-token bound; backend-specific context/compaction and inference retry controls|Version/model/account evidence, explicit environment/setting precedence without secret capture, bounded total time/cost and preserved original source material|
|P3|Fallback models, native subagents/session persistence, unrestricted provider kwargs or cross-backend sampling|Separate identity/resource/recovery design and independent admission. These should not arrive as incidental tuning fields|

These are recommendations, not a field list to implement mechanically. Put each implementation's configuration and argument/SDK mapping in its current backend/driver. Reuse the component metadata, existing binding/definition/manifest freeze, common `Invocation` and process/runtime owners. Add shared behavior only when actual consumers need it; do not put a new name-based dispatch tree in the scheduler. ([E1], [E2], [E3], [E4])

## Fixed, preset, planner and automatic modes

The three future modes can select concrete options while retaining the same execution contract. A **fixed** selection requests specific supported values; omission retains the existing default. A **preset** should resolve a versioned group of concrete backend/model options. A **planner** may propose supported values and give reasons before the approval/freeze boundary. **Automatic** selection needs an explicit bounded policy, observable inputs and a recorded concrete result. None of these grants tools, network, shell access, more concurrency or a larger parent budget.

Keep user request, policy/preset revision, resolved backend/model/options, native applied observations, and unknown/unavailable reasons distinct. Do not silently reinterpret unknown native values, map `ultracode` to a portable rank, replace models or lower effort to get a run started. Native environment/organization precedence may still change the applied result; if it cannot be observed, report unknown. Current tasks must keep their frozen original selection rather than reevaluating an updated preset or policy during recovery. This is a design recommendation, not a claim that such fields or four modes already exist. ([A2], [A3], [E1], [E3], [E4])

## Validation and limits

Twenty official documentation/public upstream source pages and one domain-scoped search response were fetched; five local version/help reads succeeded. Private source/CLI captures, full SHA256 manifests and retrieval errors are retained under ignored `.ergora/checks/backend-runtime-options/`. The search connector was unavailable; HTTPS official-domain search/page retrieval supplied the evidence. Failed raw paths and Markdown shortcuts were replaced with successful authoritative pages, and were not used as evidence.

The two files pass strict UTF-8, reciprocal/relative links, closed fences, whitespace and scoped `git diff --check`. All 28 source definitions and 112 citation uses per language, inline control names/values, table structure and heading counts match. Every official/upstream citation maps to a successful fetched source, and each pinned Ergora file exists at the recorded commit. The earlier 12-file documentation batch remains byte-for-byte frozen. These structural checks do not replace independent semantic review, which is pending.

The research checked source mappings and fetched documentation only. It did not inspect actual accounts, quotas, secrets, environment values or private config; it did not run models, install dependencies, launch services, test billing/performance, exercise native caps/fallback/compaction, verify provider acceptance or change the product/index. Real calls, supported-model discovery and independent implementation review remain necessary for each later candidate. The bilingual documents are research artifacts and do not replace the current [Agent guide](../AGENT_BACKENDS.md) or original product acceptance.

## Source register

C1–C3 are the actual official pages reached after the `developers.openai.com` documentation redirects. A1–A7 are official Claude Code pages. D/M/F references are immutable public upstream files. E references pin the inspected Ergora product. Each table cites the sources owning its claims.

[C1]: https://learn.chatgpt.com/docs/config-file/config-reference
[C2]: https://learn.chatgpt.com/docs/developer-commands?surface=cli
[C3]: https://learn.chatgpt.com/docs/non-interactive-mode
[A1]: https://code.claude.com/docs/en/cli-reference
[A2]: https://code.claude.com/docs/en/model-config
[A3]: https://code.claude.com/docs/en/env-vars
[A4]: https://code.claude.com/docs/en/fast-mode
[A5]: https://code.claude.com/docs/en/costs
[A6]: https://code.claude.com/docs/en/settings-reference
[A7]: https://code.claude.com/docs/en/settings
[D1]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md
[D2]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/llm-pi-ai/README.md
[D3]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py
[D4]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/headless/README.md
[M1]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py
[M2]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/models/litellm_model.py
[M3]: https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/README.md
[F1]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/README.md
[F2]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/task.py
[F3]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/launch.py
[E1]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agent_backends.py
[E2]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/components.json
[E3]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agents.py
[E4]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/agent_runs.py
[E5]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/deepseek.py
[E6]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/mini.py
[E7]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/kernel.py
[E8]: https://github.com/626619403/Ergora/blob/c540939d3b3f38f3851b0de965c9cd0f969eea77/src/ergora/data/drivers/forge.py
