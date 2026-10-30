# S8 independent review: large development changes

Reviewer: fresh-context `/root/s8_development_review`, 2026-10-31. Project boundary: this repository and its `docs/`. No implementation edits, installs, commits, pushes, paid models, or GPU calls were performed. Only this report and disposable isolated review fixtures were written.

## Verdict

- **Requirement compliance: changes required.** Native mini-swe-agent is advertised as a compatible implementation backend, but the real prompt, model action parser, and structured completion contract do not agree. The new UI also has a reproduced asynchronous project-context defect.
- **Maintainability: changes required at the integration boundaries.** The chosen ownership is otherwise sound: `agents.py` has real independent-call and formal-stage consumers; the SDK driver needs its separate interpreter; the reference bridge inherits the existing lifecycle instead of duplicating its stage algorithm. Normalize native protocols and availability failures inside their owners, and guard the UI result after every relevant asynchronous boundary.

The four findings below block an S8 pass in this scope. Other reviewers own governance-specific and native training campaign lifecycle findings.

## Scope and inspected identity

Raw requirements: research suitable agents for all three existing templates; separate agent implementation from template semantics; add usable replacements or supplements while preserving the six-stage workflow; select tools per role/layer through CLI and GUI. For this direction, inspect native adapters, actual mini SDK/budgets/timeout, structured commands, frozen selections, Git/check/approval/candidate-bound independent review, and new UI async behavior.

Baseline: `3b52365fe56d79c7b467a73e369b5a42c2b5afc9`, branch `feat/evolution-console`. The baseline only tracks the research distribution; nearly all implementation files are untracked, so this review read their raw contents rather than treating `git diff` as the full change. The table identifies the initial source reviewed and the byte-identical non-editable wheel used for the targeted tests. Author fixes began during the final report preparation; this initial verdict does not certify those later bytes.

|File|Initial SHA-256|
|---|---|
|`src/ergora/agents.py`|`6ab86427c5a097ef831c4b8a7f414b12d94fa22ac59d354c9465ae731354ed9f`|
|`src/ergora/stage_driver.py`|`4948198d0c504a8e7b021ac1957d77895f6ccc0dcfb27a0c15b9110e0ff6cfeb`|
|`src/ergora/reference_executor.py`|`d87c1ec1d466913a8e72daf67438b4228a5d06c3288bbdfabbc8ed7f48cea5ae`|
|`src/ergora/data/drivers/mini.py`|`4f47393b3bb46a20bb24b38889e132bbc6f470953c1518e698877aa5904e55ed`|
|`src/ergora/reference.py`|`97c38b28280eee0afe0d00a84528868f50fb85022bc46ee79f61c318b5154ffb`|
|`src/ergora/tools.py`|`a45860e7f9e711dd24903d8924c4edfd246f8ab1506b24fdd477d4d3168699bf`|
|`src/ergora/projects.py`|`9976114db0284312e7c6c9de6a21d08ac61c6ffcc651d4db160d76851a63cab1`|
|`src/ergora/processes.py`|`de2141524d555a1ea43648eee8014afef2464dcb362c8fd9f1818df5c35f8f58`|
|`src/ergora/cli.py`|`72ecbc4c5c6dca6054a785e821aeb73624179986c5a32b02c068940b59a7e632`|
|`src/ergora/web.py`|`c3b3c5809d4f3d593eaaa2324f9bf93d88b355359920582dc0b017dd3080dd0b`|
|`src/ergora/data/console/app.js`|`bfe67419c7c6907d9691f3ed11919dfd0981655052f4b23af75c1aae8eef19c9`|

Also inspected: `AGENTS.md`, `docs/PLAN.md`, the S8 delivery record, `docs/AGENT_BACKENDS.md`, the new research report/source manifest, `scripts/install-agent.sh`, the five targeted test files below and their three protocol/SDK fixtures, and neighboring frozen executor/core/sandbox/process-monitor, workflow/adapter/contracts, large-change profile/roles, and pinned mini-swe-agent 2.4.6 SDK code. Existing S0–S6 implementation was examined as a dependency, not re-reviewed as a new slice. Native Forge internals were left to the training reviewer.

## Findings

### D1 — High: the mini prompt requests text actions that its actual model rejects

Location: `src/ergora/data/drivers/mini.py:33` and `:37`.

The driver loads the `agent` section of upstream `config/default.yaml` unchanged. Its system template requires exactly one fenced `mswea_bash_command` block. The call to `get_model(config={"model_name": ...})` instead selects the real `LitellmModel`, whose request supplies `BASH_TOOL` and whose parser accepts tool calls. A model response following the supplied text-action instructions has no tool calls and raises `FormatError`; repeated compliance consumes the format-error/step/cost budget without running the requested implementation.

This was checked without a remote model: instantiate the real default model, inspect the real loaded system template, and pass a text-only/no-tool-call response to its actual action parser. Result: `LitellmModel`, text-block instruction present, `FormatError`. The existing SDK test replaces `get_model` with `DeterministicModel` and injects pre-parsed actions, so it bypasses this contract.

Minimal correction: select a tool-call-compatible native config/model pair, or explicitly select the text-action model class. Preserve the model-specific system/action instructions when adding Ergora requirements. Add a deterministic test through the production model parser rather than only injecting already parsed actions.

### D2 — High: mini's prescribed completion produces no structured stage evidence

Location: `src/ergora/data/drivers/mini.py:33` and `:43`; consumer `src/ergora/agents.py:166`.

The same unchanged instance template tells the agent to finish with standalone `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`, without another command. The real environment strips that marker and returns the subsequent stdout as `submission`; this prescribed action therefore produces an empty submission. The driver treats `Submitted` as success and prints the empty value. Formal stages and `agent run --template large-change` then require JSON artifacts, so a native completion following its rendered instructions fails normalization even after successful code changes.

Reproduced with actual `DefaultAgent`, `ManagedLocalEnvironment`, and upstream `DeterministicModel` executing exactly that rendered completion instruction: native process exit `0`, stdout `"\n"`, trajectory `submission == ""`, then `JSONDecodeError` at structured consumption. The existing acceptance fixture instead supplies marker plus hand-written JSON in one command, a completion recipe absent from and contradictory to the rendered prompt.

Minimal correction: give the native driver the structured schema and an explicit, consistent native submission recipe that includes the required result after the marker, or use a dedicated validated result file owned by the adapter. Replace the conflicting completion instructions. Test the schema-bound path using a fixture that follows the real rendered prompt and verify the resulting artifact JSON reaches the existing consumer.

### D3 — Medium: a timed-out optional interpreter probe disables the dashboard

Location: `src/ergora/agents.py:90`; caller `src/ergora/web.py:160`.

`available()` runs mini's configured Python with a five-second timeout but does not handle `subprocess.TimeoutExpired`. A slow interpreter startup is an accepted binding and is reachable with environment initialization or a Python launcher. Its timeout escapes `tools.doctor()`; every project dashboard calls that function, so the optional agent makes the entire dashboard fail with HTTP 500 and prevents correcting its binding through the console.

Reproduced in an isolated project with an executable interpreter fixture that sleeps eight seconds: binding succeeds, `tools.doctor()` raises `TimeoutExpired`. Missing modules already produce an unavailable result, so the timeout should be represented at the same per-layer boundary.

Minimal correction: convert probe timeout/execution failure into the selected layer's explicit unavailable/error result, keeping the rest of the dashboard usable. Add a targeted doctor/API regression with a bounded failing interpreter fixture.

### D4 — Medium: a late kernel result can open under a different project

Location: `src/ergora/data/console/app.js:1915`–`:1917`.

`kernelPanel.invoke()` checks the project, awaits `refresh(data.project.id)`, and then opens its modal unconditionally. If the user switches projects during that refresh, the refresh's own sequence check correctly discards the stale response, but the invocation continues and opens the old project's result in the new project. The unconditional modal can also replace a newer dialog opened while the operation was pending.

Reproduced in an independent Chromium profile and independent loopback console with two disposable projects: delay the real post-result bootstrap response, switch `review-one` to `review-two`, finish the new dashboard, then release the old response. Observed current heading `review-two` and a newly opened kernel record with `project: "review-one"`. Only the kernel operation result was mocked deterministically; bootstrap, dashboards, module code, DOM actions, and the delayed response were real. No Forge/model/GPU job ran.

Minimal correction: capture request/view/dialog ownership and recheck it after the awaited refresh before opening a result. A project check only before the await is insufficient. Cover both project switching during refresh and a newer dialog opening before completion.

## Checks and limits

- Targeted non-editable-wheel command: `ERGORA_MINI_TEST_PYTHON=<installed-mini-python> .venv-dev/bin/python -m pytest -q tests/test_agents.py tests/test_reference_executor.py tests/test_projects_tools.py tests/test_reference.py tests/test_web.py` — **31 passed, 1 skipped**, one existing TestClient/httpx deprecation warning, 31.39 s. The skipped test requires the separately enabled Forge checkout/Python; no other targeted tests were skipped.
- Python 3.11.15, Ergora 0.1.0; all eleven implementation hashes above matched the installed package before these tests. The tests include actual mini SDK/shell trajectory and timeout cleanup, four complete six-stage protocol cases through original FileAdapter/Activities, frozen binding behavior, candidate and exact plan approval evidence, and 283-file frozen reference identity.
- Independently traced the inherited preparation, trusted commands, commit, scope gate, approval, candidate verification, receipt publication, cancellation fence, and unknown-process recovery paths. No additional finding in those inspected paths. The four six-stage tests use protocol fixtures and direct Activities; they are not independent Temporal service restart or paid-agent acceptance.
- Independently reproduced D1/D2 with pinned native SDK objects and shell only; D3 with a disposable interpreter; D4 in actual isolated Chromium through CDP. Cached Playwright CLI was unavailable offline, so the existing Chromium binary was controlled directly; no installation occurred. Review service and browser were stopped afterwards.
- Did not rerun the author's full 103-test/Temporal service campaign, native Forge campaign checks, model authentication, model-quality comparisons, GPU performance, SSH delivery, or remote cancellation. Their recorded results and explicit limitations remain author evidence, not independent checks from this review.
- No quality ranking or performance superiority was inferred from the protocol fixtures or upstream README claims. Native mini model quality and actual paid Codex/Claude execution remain unverified.

Re-review is required after D1–D4 are fixed, using the affected native-protocol, availability, browser race, and six-stage regressions. The separate training review remains a dependency for the overall S8 verdict.

## Independent re-review after D1–D4 fixes

Same reviewer, 2026-10-31; this is the same-slice fix review. **This section supersedes the initial verdict for the fixed identity below.** Baseline/branch remain `3b52365fe56d79c7b467a73e369b5a42c2b5afc9` / `feat/evolution-console`; implementation remains uncommitted. Re-read the current plan, delivery record, fixes, affected tests/fixtures, and neighboring Codex-path/child-cleanup changes. No implementation edits or installs were performed.

- **Requirement compliance: pass within the reviewed large-change/S8 integration scope.** D1–D4 are closed. The verified claims remain interface, native CPU protocol, and existing evidence-contract compatibility; paid-model quality, performance superiority, and GPU acceptance are not claimed.
- **Maintainability: pass within this scope.** Native action/completion behavior now has an explicit owner and consistent instructions, probe failures stay within optional availability, and UI result ownership is checked on both sides of the refresh. The bridge still delegates stage algorithms and trusted evidence to the frozen executor. No new blocking finding in the inspected fixes.

### Fixed source identity

All eleven implementation files in the initial table were compared against the installed non-editable Ergora 0.1.0 wheel before re-running tests: every byte comparison matched. Six retain the initial hashes (`reference_executor.py`, `reference.py`, `tools.py`, `projects.py`, `cli.py`, `web.py`). The changed identities, rechecked after verification, are:

|File|Re-review SHA-256|
|---|---|
|`src/ergora/agents.py`|`e2b35edaaecc0517894edf86208bba33c7153640dc3df69839295a47c684ee9a`|
|`src/ergora/stage_driver.py`|`79742381e30f81152a7dd76fcd24ef0259772d658b916634d90fd3ea009ce421`|
|`src/ergora/data/drivers/mini.py`|`0e18665f061fcb0006da97580b750297efa1ae9b2f0afa53cb5a6793ed3327be`|
|`src/ergora/processes.py`|`4684542f406a88c31265a5b075784f511aa5259908a634e665e103f78643b85f`|
|`src/ergora/data/console/app.js`|`7f3f5e900f2ff3a4ff1c11359b6af31d286782761969e02f4b36fda0b1447684`|

Relevant revised test identities: `tests/test_agents.py` = `783b182f11c7e13de22d917629313d58d75a4d9cd87d2212bf1ac8f56aa303e2`; `tests/test_web.py` = `455520491eb4342ba8702b46b56f43a85450729c49db2f8f6b541e5c0caf1e4e`; `tests/fixtures/mini_acceptance.py` = `5a304a7f05594180326b89118167b53252a89ba6b92f2cef6a6aa2edf061ae88`; `tests/fixtures/reference_acceptance.py` = `ebe01896396d643f37c3f0f7a348a22b098e0709e7d4626f119873040273297b`; `tests/fixtures/stage_agent.py` = `c6e38414c22a2220ad0c83a8a2e0ec56b1ee5e383af3d36b2007437244f0e33a`.

### Finding dispositions and independent checks

- **D1 closed — `mini.py:36` and `:53`.** The driver now provides tool-call-compatible instructions and explicitly selects the real LiteLLM model class. It no longer imports the contradictory upstream text-action configuration. The revised test stubs only `litellm.completion`, letting the production model factory, cost calculation, action parser, DefaultAgent, and real shell run.
- **D2 closed — `mini.py:32`, `:41`, and `:59`.** The rendered task supplies an output file outside the checkout and an exact native completion command that emits marker plus file contents. Empty/marker-only submission returns failure. Independently invoked the production `agents.invoke()` structured path with the actual home-installed mini SDK and a separate local completion stub following the rendered file path and command: real `LitellmModel`, two calls, shell-created candidate, status `succeeded`, and normalized `large-change` implementer artifacts. Repeated the old marker-only action through the same real factory/parser: one call, native exit `1`, status `failed`, no accepted artifact result. No remote model request occurred.
- **D3 closed — `agents.py:90`.** Interpreter execution and timeout failures return unavailable. The targeted API regression uses an actual eight-second startup fixture, receives a usable dashboard with only that layer unavailable, and successfully saves the corrected binding.
- **D4 closed — `app.js:1911` and `:1929`.** The invocation captures request order, workflow epoch, project/tab, and modal ownership, then checks them before and after refresh. Repeated the original counterexample in another independent Chromium profile with another disposable console on an OS-assigned loopback port: delayed the real post-result bootstrap response, completed a project switch, released the old response, and verified no stale modal opened. Also independently passed a newer modal, newer template, out-of-order operation results, and normal unchanged-view result display. Kernel result bodies were deterministic local fixtures; all bootstrap/dashboard responses, module/DOM behavior, and delayed refreshes were real. No Forge/model/GPU action ran. The review browser and service were stopped afterwards.

Command: `ERGORA_MINI_TEST_PYTHON=<home-installed-mini-python> .venv-dev/bin/python -m pytest -q tests/test_agents.py tests/test_reference_executor.py tests/test_projects_tools.py tests/test_reference.py tests/test_web.py` — **33 passed, 3 skipped**, one existing TestClient/httpx deprecation warning, 51.70 s. All three skips are Forge-only tests because this reviewer did not enable its separate checkout/Python. Native mini complete/timeout/empty cases, the slow-probe API case, all four six-stage command/Codex protocol cases, template copying, binding freezing, and frozen reference identity ran. The six-stage fixtures now also test the exact configured Codex executable and absence of late reviewer writes after supervised child cleanup.

The initial limits still apply. The author's 107-test/36-subtest run with actual Temporal and native Forge CPU evidence was inspected as recorded evidence, not independently repeated here. No paid Codex/Claude/mini quality comparison, GPU performance, remote process cancellation, or independent Temporal restart campaign was added. The separate governance and training re-reviews remain responsible for their own findings and acceptance scope.
