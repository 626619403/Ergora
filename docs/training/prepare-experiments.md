# Prepare an exact training experiment

English · [Documentation](../README.md)

## Prepare versioned native sources

On Linux/WSL2, use installed Ergora and Git to explicitly select versioned sources in a persistent directory that does not yet exist. The current training source is `training-executor-admission-v3`; it preserves original admission behavior and leaves SDK imports at the actual CLI-use boundary:

```bash
ergora reference prepare-training \
  --protocol training-executor-admission-v3 \
  --directory "$HOME/.local/share/ergora/native/training-admission"
```

Success returns `status=source_prepared` and normalized `installation`. This only copies validated current sources and syncs the descriptor; `dependencies_installed`, `runtime_started` and `execution_authorized` are all false. It creates no control project, experiment or service and runs no runner. Existing directories are never overwritten. Interrupted preparation leaves the directory for inspection; choose another new directory to retry.

The new source preserves original Git, the two-arm runner, Sandbox, archives, MLflow and result handling, adding only a narrow admission seam inside the original `executor.lock`. Reentry is rejected when `started.json` exists without a result. Manual calls without the hook cannot take over managed tasks under `managed-execution/`. Existing results are still returned read-only and cannot retroactively establish managed stop. Current sources check the complete platform files and fixed descriptor; empty, damaged, linked or tampered declarations are rejected directly. Source code, examples and validation inventories track the current implementation; public HTML/zip records only the original provenance.

Preparation only copies current sources and syncs declarations; it installs no dependencies, grants no execution authority and enables no automatic multi-round loop. Native admission and trusted configuration drivers do not depend on the Temporal SDK; actual `run-local`/`approve` control-plane operations still require their original dependencies. Training installations must match the current descriptor; existing runs remain constrained by their complete source, owner, original clock and single launch fixed at creation.

Dependencies still belong to that native installation's own `.venv` and pinned `requirements.lock`; base Ergora or the `temporal` extra does not replace them. Source preparation does not initialize these dependencies. Satisfy the [current native provisioning gate](../install/linux.md#prepare-the-formal-reference-runtime), selected dependencies/services and explicit trusted-container boundary. The original reference manual describes its own distribution and does not provision a current compatible installation. [Managed execution](execution.md#explicit-managed-execution-and-offline-stop-observation) requires a separate new state directory and the same protocol for all participating executors; it cannot take over old started records or live old owners. Template proposals and kernel experts only advise; execution still requires the original budget and explicit confirmation. Finite-candidate controllers are [authorized and submitted separately](controllers.md#start-a-local-training-budget-and-recover-original-authorization).

## Preview and initialize a baseline

First register a real Git project selecting `training-optimization` and its reference installation, then fill the template's `baseline.json`. `commit` must be a complete existing commit in that repository, and configuration/workload digests must be real. Registration does not establish that these measurements or quality checks passed.

```bash
ergora training baseline-preview my-project --baseline ./training-task/baseline.json
# 核对返回的完整 baseline、project_revision 和 baseline_sha256
ergora training init-baseline my-project --baseline ./training-task/baseline.json \
  --revision REVISION --baseline-sha256 PREVIEW_BASELINE_CONTENT_SHA256
ergora training list my-project
```

The console's “训练实验” → “当前基线” → “预览与初始化基线” supports the same flow: paste complete JSON, preview, check complete materials and project revision, then paste the preview's content SHA and confirm. Editing JSON or switching projects invalidates the old preview. CLI, page, `POST /api/projects/{project}/training/baseline-preview` (`baseline` object) and `POST .../init-baseline` (plus `revision / baseline_sha256`) share the application entry point.

The content SHA is computed from canonical JSON of the complete object, retaining extra explanatory fields while ignoring key order and formatting. Use the preview value, not the file's `sha256sum`. The receipt's `current_baseline_file_sha256` is instead the original file's byte SHA. CLI raw input and native serialized files are each limited to 1MiB; HTTP retains the console's existing 4MB request limit, and the parsed baseline must also meet the native 1MiB limit. Preview and initialization require no Temporal SDK, service or GPU. Actual atomic initialization uses the original perfctl lock and supports Linux/WSL2 only; native Windows supports preview.

Preview `not_initialized` means no original baseline exists, `already_initialized` means complete identical content exists, and `conflict` means different content. Successful initialization returns `initialized` or `already_initialized` with CLI exit 0; errors/conflicts exit nonzero. If an initialization response is lost, reread the list, preview the same JSON and explicitly retry. Published identical files retain their original bytes; no additional baseline is created and differing content is not overwritten. An existing different baseline requires a reviewed migration; this entry point offers no replacement.

## Preview and register a trusted runner

Fill in the training template's `runner-template.example.json` in the Linux/WSL2 control environment. Preview and registration require no Temporal SDK, service or GPU. A runner is a per-experiment command authorized by a trusted operator. Registration saves argv without running it; subsequent native `run-local` replaces its `{manifest}`/`{output}` placeholders at execution.

```bash
ergora training runner-preview my-project --runner ./training-task/runner-template.example.json
# 核对完整规范化 runner、project_revision 和 runner_sha256
ergora training register-runner my-project --runner ./training-task/runner-template.example.json \
  --revision REVISION --runner-sha256 PREVIEW_RUNNER_CONTENT_SHA256
```

`project` must be the currently registered project and `repo` must point to its Git root; receipts show the resolved canonical path. Original `agentflow training runner-add` registration logic validates fields/argv/timeouts. `schema_version` must be integer 2; the exact seven fields include `configuration_readback`; timeout is 1–82800 seconds. Ordinary full commands set `configuration_readback` to null. Preview runs the original registrar only in an isolated subprocess with a temporary configuration directory, leaving real configuration untouched. After confirmation the original registrar immutably writes real `training-runners/RUNNER_ID.json`. IDs are globally unique in a shared configuration directory; include project name and version in the ID.

Trusted configuration drivers use non-null `configuration_readback`, fixing `training-configuration-driver-v1`, a reviewed Git source reference, the `source-bytes` material role, observation scheme and required `prepared_json_format` (null or `json-v1`), `baseline_reference_protocol` (null or `baseline-reference-v1`) and `screen` capability declarations. `screen:null` means full only; screening declares `{"protocol":"training-screen-v1","scheme":"project-screen-v1"}` and also `baseline-reference-v1`. The command must contain exactly three argv: absolute Python, `{configuration_driver}`, `{configuration_request}`. The source implements `prepare(request)`, `describe(context)` and `run(context, request, output)`. After construction and two observations, the same context executes the manifest-selected operation, consuming authorization through the original managed entry point; manual run-local grants this driver no execution authority. Inputs are selected only by manifest `configuration_inputs`: `{kind:"git-source",path:"<checkout相对普通文件>"}`, or a prepared-json descriptor generated by the original preparation owner. Declarations must match actual source support; callback names cannot be used to probe capabilities. Passing the interface does not establish that an adapter exists for an arbitrary target training framework.

The console's “训练实验” → “可信 runner” → “预览与登记 runner” provides the same flow. HTTP uses `POST /api/projects/{project}/training/runner-preview` (`runner` object) and `POST .../register-runner` (plus `revision / runner_sha256`). Editing or switching projects invalidates old previews. Confirmed content SHA and original file byte SHA appear separately. CLI original and native serialized files are each limited to 1MiB; HTTP retains the existing 4MB envelope.

Preview states are `not_registered / already_registered / conflict`; successful confirmation returns `registered / already_registered`. Identical-content retries preserve original file bytes; the same ID with different content is rejected, and changing commands requires a new reviewed ID. IDs belonging to other projects are rejected without revealing their commands. After a lost receipt, preview identical JSON again, read the current original and explicitly confirm retry. Registration neither submits experiments nor approves training contracts. Continue with experiment preparation below.

## Prepare exact experiments and recover partial publication

Fill in complete real `experiment.json` reviewed by the project owner, after registering the trusted runner and baseline. Experiment IDs are globally unique in shared execution state; include the project name. Existing native experiments remain visible through `list / show`. These CLI/HTTP entry points work on Linux/WSL2 without the Temporal SDK or running services. Preparation does not run runners, submit workflows or approve performance results; it does not change `contract_approved` to true for you.

```bash
ergora training experiment-preview my-project --experiment ./training-task/experiment.json \
  --runner my-project-training-v1 --max-run-seconds 25200
# 核对完整plan、三目标文件、baseline／runner、project_revision及preview_sha256
ergora training prepare my-project --experiment ./training-task/experiment.json \
  --runner my-project-training-v1 --max-run-seconds 25200 \
  --revision REVISION --preview-sha256 PREVIEW_SHA256
ergora training preparation my-project EXPERIMENT_ID
```

Omit `--max-run-seconds` to use the original owner's default window. Explicit values are 60–86400 seconds and must cover the runner timeout; 0/False does not mean omitted. The original CLI draft and each native file are limited to 1MiB; the complete recovery intent is limited to 16MiB. Oversized inputs fail visibly. Preview invokes original prepare in temporary configuration/state directories, binding the real Git commit, baseline and comparator. Spec URIs map back to registered real manifest paths; manifest byte binding retains the original owner's result. Preview writes no real execution directory.

Confirmation first saves the original intent immutably, syncs the formal intent file and directory chain to the registered state root and checks the same inode/original-byte readback. Only then does original prepare publish formal outputs; these are not one atomic transaction. Ordinary full/Git inputs still have three outputs: global manifest, project manifest and spec. Prepared-json adds two original raw configurations. `preparation` requires no SDK or service; states are `not_recorded / intent_saved / partially_prepared / prepared / conflict / native_files_without_intent`. `prepared` means the same original intent and all outputs are synced and read back consistently. Reading that state confirms existing originals' durability under the original lock; it neither fills files nor changes IDs. Directory-sync/readback failure cannot return prepared. Canonical content-confirmation `preview_sha256` and original-intent `intent_sha256` identify the same frozen object. Each published file's byte SHA is listed separately; file `sha256sum` cannot replace the intent digest.

If a request fails or its receipt is lost, first read the preparation record for the original experiment ID. Repeating identical `prepare` syncs and checks the same original intent and current existing files, without automatically filling missing files. Confirm recovery using the original intent SHA and current project revision:

```bash
ergora training resume-prepare my-project EXPERIMENT_ID \
  --revision CURRENT_REVISION --intent-sha256 ORIGINAL_INTENT_SHA256
ergora training show my-project EXPERIMENT_ID
```

Recovery rechecks original source bytes, registration identity, exact file plan and existing content before the original owner fills missing outputs; differing content is never overwritten. Explicit recovery rejects existing job/fence/start records even if all outputs are complete. In that case `preparation` or identical `prepare` can still confirm existing originals and read preparation state. Source drift, existing job/fence/start records, or old native files without this tool's intent require checking original records first. This entry point does not automatically take over, clean up or retry with another ID. Original intents reside in registered execution state under `ergora/training-preparations/`; there is no second experiment database.

HTTP uses `POST /api/projects/{project}/training/experiment-preview`, with `experiment / runner_template_id / max_run_seconds` (omitted or null allowed); `POST .../prepare` adds `revision / preview_sha256`. Read with `GET .../training/{experiment_id}/preparation`; recover with `POST .../training/{experiment_id}/resume-prepare` containing `revision / intent_sha256`. These share the CLI application entry point. On the training page, expand “预览与准备实验” under “准备实验”, supply complete experiment JSON, a registered runner ID and optional window, preview the complete publication plan, then paste the preview SHA to confirm. After preparation view the original experiment; submission still requires separate confirmation in its details.

After request failure or reopening the page, expand “读取与恢复原准备记录” and enter the original experiment ID to read each file's facts. `intent_saved / partially_prepared` displays the complete original intent and per-file states; paste the original intent SHA to explicitly recover. `conflict / native_files_without_intent` offers no overwrite/takeover action. Editing inputs or switching projects invalidates old previews and late receipts. The panel is disabled during sending to prevent double clicks. Fully prepared only means originals are durable and consistent; it does not mean start occurred, training succeeded or adoption was approved.

## Choose full or lightweight screen

Every current experiment manifest must explicitly specify `execution`: full verification is `{"operation":"full-verify"}`; lightweight screening is `training-screen-v1`, with its screen plan in `execution.plan`. The first round still freezes model algorithm, architecture, size, precision and training objective, retaining original checks_required, quality_required and complete performance_policy. Screen covers only source-declared low-cost checks and candidate windows; it grants no full_verified, accepted, controller execution or release.

First obtain an exact selector through [baseline reference reading](evidence-and-approval.md#read-archived-evidence-and-original-integration-tickets), and register a trusted source supporting the same scheme. Merge this fragment into a complete experiment. Replace SHA placeholders with real identities; the selected source must support the scheme, counts, thresholds and input plan. Example values are not default policy:

```json
{
  "configuration_inputs": {"kind": "git-source", "path": "training/config.json"},
  "baseline_reference": {"experiment_id": "baseline-measurement",
    "evidence_sha256": "BASELINE_EVIDENCE_SHA256", "reference_sha256": "BASELINE_REFERENCE_SHA256"},
  "execution": {"operation": "training-screen-v1", "plan": {
    "scheme": "project-screen-v1", "requested_tier": "screened",
    "verification_experiment_id": "trial-a-full",
    "input_plan": {"scheme": "project-input-v1", "sha256": "INPUT_PLAN_SHA256"},
    "window": {"unit": "source_samples", "minimum_work": 256, "maximum_work": 256,
      "warmup_maximum_work": 0, "maximum_windows": 1, "maximum_seconds": 30},
    "checks": [
      {"id": "finite", "kind": "finite", "contract_sha256": "FINITE_SOURCE_SHA256", "source_entrypoint": "checks/finite.py"},
      {"id": "behavior", "kind": "behavior", "contract_sha256": "BEHAVIOR_SOURCE_SHA256", "source_entrypoint": "checks/behavior.py"}
    ],
    "resources": [],
    "screening": {"target": "throughput", "minimum_improvement_fraction": 0.03,
      "noise_fraction": 0.02, "comparison_scheme": "project-comparison-v1"}
  }}
}
```

`verification_experiment_id` links another full-verification ID; the field itself neither prepares nor authorizes that experiment. Each candidate is frozen separately and these IDs must differ within one manual selection. input_plan binds input/initialization/order; seed alone is insufficient. window.unit is source_samples or source_tokens. Both check kinds are required; contract_sha256 is the original byte SHA of a regular file in the same reviewed source inventory. The trusted source supplies expected values and tolerances. comparison_scheme must match the applicability relation of its reference projection. Declare metric/unit/scope/aggregation/required/limit according to actual source support. Optional missing measurements explicitly become NOT_RUN; missing required measurements block completion. Device capacity cannot replace a peak measurement.

The source additionally implements `screen(context, request, output, *, record_first_failure) -> report_data`, reusing the same context as prepare/describe/baseline_reference_read. It runs only frozen candidate windows, without a baseline training arm or baseline_reference_record. Any reduction in object construction/model residency requires separate evidence. report_data contains `workload / windows / checks / checks_not_run / resources / artifacts / reasons`; original references use regular relative paths as `{path,sha256,bytes}`. See [screen-report validation](../../src/ergora/training/runtime/evidence.py) for complete raw fields. Core derives throughput, tier and decision from actual valid work and positive finite elapsed time. On the first finite/behavior FAIL identified, the source stops adding training work/windows and synchronously calls `record_first_failure`, whose payload contains `check_id / rank / phase / window_id / work_index / observation_order / diagnostic_refs`. Confirm the original first failure is durable before necessary record handling or propagating exceptions. Put nonfinite diagnostics in raw text; do not write NaN JSON or overwrite them with later exceptions.

Use the same `experiment-preview → prepare` flow above. Pass prepared JSON materials per experiment as `configuration_materials` through the API below; omit draft `configuration_inputs` so the original owner generates it, retaining each complete configuration and verification ID. Then run through schema1 authorization, explicit cycle-start and managed execute under the [original manual budget](controllers.md#start-a-local-training-budget-and-recover-original-authorization). Candidates must share operation and screen contract; do not mix full and screen or differing resource policies. The original clock covers construction, reference reading, checks and cleanup. window.maximum_seconds accepts 1–86400 seconds including fractions within that range; 0.5 seconds is rejected before preparation, although actual measured elapsed time may be less than 1 second. Runner or original remaining budget can cut off sooner. Less than 1 second remaining before the request process or final work yields blocked; time is not rounded up and the clock is not restarted.

Complete checks can produce `SCREEN_COMPLETED`; proven finite/behavior failure or required-resource limit breach produces `SCREEN_REJECTED`/tier none. A missing currently required oracle, invalid raw data or runtime exception remains FAILED; fences follow CANCELLED. If the reference inventory is fully readable but baseline quality/provenance/timing evidence is missing, completed checks may reach screened, while performance is unavailable and inconclusive. promising is only a directional judgment under frozen exploration policy. Subsequent full verification must be separately prepared, executed and reviewed; it does not automatically advance the baseline, deep verification, negative/skip cycles or per-round profiling.

## Feed bounded JSON configuration materials into managed execution

`training search-preview/search-prepare/search-read` generates complete candidate configurations from complete baseline UTF-8 and finite scalar variations, preserving the original candidate code commit/six-stage export provenance. Request fields are in bundled `data/schemas/training-search-v1.json`. First-round fixed items follow the preceding section; valid batch/chunk/parallel/library changes must still satisfy project workload and the complete quality contract.

```bash
ergora training search-preview my-project --request ./search-request.json
ergora training search-prepare my-project --request ./search-request.json \
  --revision REVISION --preview-sha256 PREVIEW_SHA256 --directory ./search-inputs
ergora training search-read ./search-inputs --sha256 SEARCH_JSON_RAW_SHA256
```

The selected runner must declare a non-null trusted configuration driver and `prepared_json_format="json-v1"`. Missing or mismatched declarations show configuration execution unavailable before package publication/the first native preparation intent; the driver is not imported to probe support. Sync and read back the complete package before publishing each candidate's two materials, two manifests and spec through its original preparation intent. Configuration copies are fixed under registered state at `training/configurations/EXPERIMENT_ID/{baseline,candidate}.json`. The sole manifest descriptor records kind/format and both paths/raw SHAs/bytes. API `preview_experiment/prepare_experiment` receives complete `{format:"json-v1",baseline:{utf8,sha256},candidate:{utf8,sha256}}` through keyword `configuration_materials`; it does not reconstruct configurations from observation snapshots or pickle. Ordinary experiment entry points default to null.

Preparation grants no execution authority, starts no clock and runs no automatic loop. The operator still uses returned original experiment IDs/manifest SHAs with the [original cycle authorization and start](controllers.md#start-a-local-training-budget-and-recover-original-authorization), then [explicit managed execution](execution.md#explicit-managed-execution-and-offline-stop-observation) to consume materials. Original three-key performance policy, attempt/unknown reconciliation and reaper remain unchanged. The wrapper constructs/observes in one opaque context, freezes a receipt, then rechecks original raw/source/fence/clock before first work. The original full evidence archive retains both raw inputs actually consumed and the receipt. Raw SHA, canonical snapshot SHA and adapter semantic identity have distinct meanings. Only passing the actual original gate supplies complete evidence within its stated scope; JSON capability declarations establish no GEAct/MoE, GPU, quality or gain claims.

`search-read` checks only the frozen package, without reading current source/native state, creating State or requiring the Temporal SDK. Lost replies/partial publication recover through the same package and original intent/ID. No repair occurs after job/submission/fence exists; lost original intents are not recreated from the package. Baseline references and typed screens use their respective entry points in this guide. Negative/skip cycles and automatic adoption remain subsequent work.

Continue: [Submit, execute and recover a training experiment](execution.md) · [Authorize and supervise a finite training controller](controllers.md).
