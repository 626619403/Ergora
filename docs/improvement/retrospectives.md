# Generate source-bound retrospective candidates

English · [Documentation](../README.md) · [简体中文](../zh-CN/improvement/retrospectives.md)

## Propose a correction to one project document

Use this explicit path when a behavioral correction should become a persistent project rule or lesson. Select one existing Markdown file in the registered project's repository, such as its `AGENTS.md`. Ordinary documentation edits already authorized by a development task keep that task's contract. Imported chat text is reported source material. Eligible ordinary [project-native sessions](../operations/services.md#project-native-sessions) can also suggest a concrete change during their existing turn, with a project opt-out; the same exact operator application gate follows.

Install the read-only proposal preset, then prepare its complete manifest and grant through the [manifest steps](../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory). The root is `ergora-document-correction 1.0.1`, with leaf `root/propose`, Codex `gpt-6.2-sol` high, empty write/network permissions and shell disabled. Installing/preparing a manifest makes no model call.

```bash
ergora composition install-preset document-correction
ergora retrospective prepare-document my-project --document AGENTS.md --correction ./correction.txt --source "Explicit operator correction" --revision PROJECT_REVISION --manifest ./correction-manifest --instance root/propose --directory ./correction-input --max-prompt-bytes 500000
ergora composition run-input my-project ./correction-input --mode text-only --timeout 240
```

`correction.txt` contains the complete UTF-8 correction. Preparation freezes its original bytes, the full current document and governing ancestor rules, repository/HEAD, project revision and original control authority. Uncommitted document content is retained as the before image. `--max-material-bytes` bounds complete correction/document/rule bytes and the replacement; the complete prompt has the separately supplied limit. Oversized, nontext, linked or outside-project targets fail without truncation. Model invocation is the separate explicit `run-input`; missing backend support fails visibly. A one-off or unsupported correction can yield `candidate:null` without a document write.

Use the original input digest and invocation receipt's result path/SHA to create a complete host-computed preview:

```bash
ergora retrospective preview-document my-project ./correction-input ORIGINAL_RESULT --revision PROJECT_REVISION --input-digest INPUT_DIGEST --result-sha256 RESULT_SHA > ./document-preview.json
```

Read `change.before`, `change.after` and `change.diff`, together with the lesson, applicability and `scope`. They contain the full original/replacement text and exact file identities, including original line endings, BOM, final-newline state and mode. `check-document INPUT RESULT --input-digest DIGEST --result-sha256 SHA` computes the same inspection offline; only `preview-document` at the original control home seals an actionable candidate. Neither operation changes the project document or grants consent. Candidate/source text saying that a user agrees is not consent.

A completed eligible native response supplies this complete object as `correction_suggestion.preview`, without a second model call or a separate generation confirmation. Save that preview object rather than the entire Agent record when using the commands below. Its native request/result identities remain genuine native sources; it is not a composition result or a handoff. Ordinary status reads carry only an immutable candidate reference. The console fetches/renders the full body once per selected candidate and refreshes current action status independently. Missing, unsupported or malformed suggestions create no automatic follow-up call.

After reviewing that exact preview, submit a separate explicit decision using its `candidate_digest`, `change.before.sha256` and `scope_sha256`:

```bash
ergora retrospective apply-document my-project ./document-preview.json --revision PROJECT_REVISION --candidate-digest CANDIDATE_DIGEST --base-sha256 BASE_SHA --scope-sha256 SCOPE_SHA --confirm
ergora retrospective document-status my-project ./document-preview.json
```

Apply supports local Linux/WSL regular files with synchronization/replacement support; preview/status report actual apply availability. This is an explicit same-user operator boundary, not protected-human authentication or OS isolation. Cooperating Ergora writers share the repository mutex. External editors ignoring that mutex can race filesystem replacement; pause such editing during application.

The host rechecks original input/result bytes, project revision, repository/HEAD, governing rules, path/inode/mode and before bytes immediately before replacement. Drift refuses the old candidate: prepare again from current content, inspect the new full diff and confirm that new identity. To decline or withdraw an unattempted candidate:

```bash
ergora retrospective withdraw-document my-project ./document-preview.json --reason "Do not persist this lesson"
```

To edit or supersede a proposal, prepare a fresh one with `--parent-preview ./document-preview.json`, retain its original outcome/authority reference, then obtain and inspect a complete new replacement. The direct parent's original outcome/history is checked again under its lock at final application. A changed parent requires fresh preparation, preview and consent; an explicitly shown unresolved parent remains unknown. Acceptance of the old candidate is never copied. Memory saving, active Skill adoption and code changes remain separate actions.

Keep the complete original input directory, result, preview and control home. A preview belongs to its host-issued original slot and control-root/database identities: another `--home`, a copied/missing slot or a restored replacement authority cannot consume it. Backup/history inspection retains its existing behavior; migrating old preview consumption is unsupported. Reopen status under the original home. Status reports the original receipt separately from current file observations. A consumed/interrupted attempt without sufficient receipt remains `unknown`; neither status nor repeating apply resends it. Preserve its original records and any captured staged-file evidence. A new superseding proposal must show that unresolved history and requires its own exact decision.

The original slot retains a durable record of consumption before issuing a decision. Lost issued records produce unknown/unavailable history rather than renewed readiness; a missing consumption record cannot be rebuilt from a saved preview. Manually replacing every journal file with a mutually consistent earlier snapshot under the same authority is outside this cooperative boundary and is unsupported. Use the complete backup/restore contract; restored identities cannot consume old previews.

## Select complete offline evidence for a retrospective

The basic installation can also read the complete original index without the control database or online services:

```bash
ergora handoff read ./task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

First check the original `job_id`, receipt and artifact `name` in `index.jobs`, then save the explicit selection as a JSON file, for example:

```json
[{"job_id":"JOB_ID","name":"ARTIFACT_NAME"}]
```

```bash
ergora handoff read ./task-handoff.zip --selection ./selection.json --sha256 EXPECTED_PACKET_SHA256 > ./retrospective-evidence.json
```

Select at most 32 items. Each returns its complete UTF-8 body, original job/receipt/artifact identities and byte count, retaining the complete original index, package/manifest/index digests, original failures, cancellation and unknown costs. Select identically named artifacts from different jobs separately. Omitting selection reads only the index, without prefetching bodies. The complete package is still verified first; bodies come from those same verified bytes, without reopening the source path, extracting or executing the ZIP. Nontext, NUL, missing/duplicate selections or a final canonical JSON result over 1 MiB are explicitly refused; no truncation or partial success is returned. Normal indented CLI output can be larger; a complete Agent input still faces its original capacity admission.

The output is version-1 plain JSON of kind `ergora-handoff-selection`; `sha256` hashes the other fields as canonical UTF-8 JSON with sorted keys and no extra spaces. It can be the explicit material input to the original `composition prepare --task`. The original `execution_success: null`, `origin_authenticated: false` and package-verification scope remain. It does not update memory or active Skills; retrospective proposals, independent evaluation and explicit adoption are subsequent operations.

In the page, select “Retrospective improvement”, enter the handoff-package path on the console machine and the full-package SHA checked at download, then “Read handoff index”. Its project ID must match the current project. Nothing is selected by default. Select by original job/material name, then “Read complete selected materials” to display all original text, provenance and selection identity. Download CLI-compatible `selected-artifacts.json` and complete `retrospective-evidence.json`. The latter's internal sha256 remains the canonical identity above, distinct from the JSON file's byte digest. Changing sources or rereading the index invalidates the old selection. Successful rereading clears selections; a failed read retains input and failure status. The original owner refuses binary, NUL and complete over-capacity results; windows or truncation cannot bypass it. Candidate preparation, read-only model invocation and result export each require explicit submission. [Trusted evaluation and explicit adoption](skills-and-evaluation.md) follow separately.

## Prepare complete retrospective input in the page

The “Prepare retrospective candidate input” form becomes available only after complete selected materials have been read in “Retrospective improvement”. Choose Skill, project memory or workflow improvement. For a Skill, “Read current baseline” and explicitly select an active head. For memory, explicitly select a valid revision or “New memory”. For workflows, also enter the complete target manifest, its digest and a new version for the target root. This and the candidate author's manifest are separate inputs.

Enter the improvement objective, saved complete author-manifest path, author instance, new input directory and complete-prompt byte limit, then “Save complete candidate input”. The required three presets and author manifests are described under each direction below. The server rechecks the baseline, evidence and complete permissions/resources/capacity; it does not overwrite an existing directory. Successful saving produces only the complete original input. Use the separate operations on this page for explicit invocation/inspection/export; [trusted evaluation and adoption](skills-and-evaluation.md) remain a separate step.

If preparation fails, a reply is lost or the page has changed, retain the original submitted directory and explicitly read that path in “Reread saved input”. This checks the complete original input/request/inherited materials and owning project. It does not rebuild from a new form or automatically prepare again. A later invalid source head or memory does not rewrite saved input; a new preparation uses currently valid sources. Carry the entire input directory to another machine, rather than just the JSON returned by the page. The original `ergora composition verify-input INPUT_DIRECTORY --material` verifies the complete directory offline; actual `run-input` rechecks current backend admission.

## Explicitly invoke a frozen read-only leaf in the page

Both “Tool bindings” and “Retrospective improvement” offer “Invoke frozen read-only leaf”. Enter the complete input directory on the console machine and its original digest. Choose the backend requested by the frozen definition, or explicitly specify a backend/model/reason and optional Codex reasoning-configuration path, then “Check current read-only admission”. The page shows the original role, requested and actual backend, all material identities and permission limits. This check is a current observation and runs again before invocation; changes to input/backend require another check.

After confirming, enter the timeout and explicitly submit one call. Fields are locked during execution; the page does not automatically resend or continue it. Closing a window, changing pages or a network error does not mean the original call stopped. Reopen the window and explicitly “Read original invocation records”, matching the latest 100 original records by input digest, backend and start time. The result's status is the original run status: HTTP success can still have stored failed/timed_out. Use the result file and SHA for the complete result; diagnostics have a bounded display.

When opened from “Retrospective improvement”, a successful original record can “Use in original-result inspection”, copying the saved run-snapshot directory, input digest, result path and SHA. Check its direction, then explicitly inspect and export. Prepare the subsequent reviewer input separately from the complete checked JSON below; it is not passed automatically. For custom definitions without a model minimum, prefer different author and reviewer backends and record a reason for fallback; bundled leaves retain their declared minimum. This entry supports only text-only read-only leaves. Tool restrictions provide no OS isolation or authorization for formal tasks, evaluation or adoption. A general input's task body has no common project field; selecting a project assigns this run's ownership. Retrospective inspection separately checks its original project declaration.

## Inspect results and export complete candidates in the page

In “Retrospective improvement” → “Inspect result and export candidate”, choose the result's direction and enter the complete original input directory/digest and original Agent result file/SHA256, then explicitly inspect. Verify input digest through input rereading above or the original `composition verify-input`; the original model-invocation receipt supplies the result file and SHA. This uses original sources in frozen input, independently of the current evidence selection above.

Inspection displays the complete original request and Agent reply and downloads complete `retrospective-checked.json`. Its digest corresponds to the original input/result/candidate; the downloaded JSON file's digest is separate. Changed sources require another inspection. A null candidate needs no export. Otherwise review the complete candidate first, enter a new export directory and explicitly submit. A Skill directory's final name must equal the candidate name.

Export rechecks the project/input/result/candidate identities selected in that submission, then atomically saves complete files and executable bits. Existing directories are not overwritten, and exporting inside frozen input is refused. On failure or a lost reply, retain the previous directory and do not automatically resend. Inspect an existing target with each direction's original CLI below; do not delete it to force a retry. Export does not import, evaluate or adopt. Continue through the separate explicit operations below.

## Generate a provenance-bound Skill retrospective candidate

Start with a registered project, verifiable handoff package and baseline Skill already imported into that project. `ergora skill list my-project` returns the current `active` name, digest and revision. A first import establishes a baseline, without measuring an improvement. Select complete provenance with the selection JSON above and write a UTF-8 `objective.txt` describing the intended improvement.

```bash
ergora composition install-preset retrospective
```

The new composition root is `ergora-skill-retrospective 1.0.2`, with read-only author `root/propose` and subsequent reviewer `root/review`, both using Codex gpt-6.2-sol high. Prepare this root's manifest directory through the [complete manifest steps](../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory). The grant must explicitly permit reading `workspace`/`definitions`, empty write/network and shell=false, and provide the root's required limits. Import, manifest creation and the preparation below send no model requests.

```bash
ergora retrospective prepare my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --skill SKILL_NAME --digest BASELINE_DIGEST --head-revision HEAD_REVISION --objective ./objective.txt --manifest ./retrospective-manifest --instance root/propose --directory ./retrospective-author-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-author-input --backend codex --mode text-only --timeout 240
```

Preparation checks the complete original provenance and current active Skill in the same project, freezing all UTF-8 files and executable bits, exact digest/head revision, original failures/unknown costs, objective and response schema. Original Skill files total at most 1 MiB; the complete prompt has its own supplied limit. Over-capacity input is explicitly refused: reduce explicit selections or use a smaller Skill, without truncating reference materials. Prepared input retains its original snapshot; new preparation rechecks the current head. prepare/check target read-only leaves returning proposal JSON; a custom leaf and supported backend can also be selected.

The invocation receipt supplies the original `result` file path and `result_sha256`. Retain them, then inspect that original result:

```bash
ergora retrospective check ./retrospective-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./retrospective-checked.json
ergora composition prepare-from-manifest ./retrospective-manifest root/review --task ./retrospective-checked.json --directory ./retrospective-review-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

The author's ordinary `artifacts.response` must be JSON matching the frozen proposal_schema, including the corresponding provenance SHA, baseline digest/revision, exact selected-material references, negative results, costs/uncertainties and complete standard Skill-file suggestions. With insufficient evidence, it can return `candidate:null`. Inspection returns the complete original request and Agent result, checking portable paths, metadata, directory-content identity and references. It operates offline without creating State, and remains possible if the source package or original Skill is later lost. `quality_evaluated:false`, `adoption_authorized:false` and `origin_authenticated:false` remain explicit: structural linkage is not quality evidence.

check reads at most 8 MiB of the original result, allowing nested JSON escaping of complete files in the response string. The reviewer explicitly receives the complete checked JSON through the original composition preparation command above. This preset's review leaf returns a textual review; do not call retrospective check on it. The complete subsequent prompt must independently pass the original capacity gate. Offline inspection of a large result does not mean it fits any subsequent prompt. Static depends_on does not execute ports automatically. Bundled authors and reviewers use separate Codex sessions satisfying the definition minimum. Supply trusted provider configuration and environment credential references in the example inference.toml. Other backend examples apply to custom definitions without this minimum and still require actual admission; same-backend sessions do not establish different-backend validation. If inspection or a model call fails, retain the original input, run and reply before proceeding, without automatic resubmission. Original Agent records remain authoritative for invocation facts.

With a nonnull candidate and its full content reviewed, take `candidate_digest` from check and explicitly export to a new directory whose final name equals the Skill name:

```bash
ergora retrospective export ./retrospective-author-input AUTHOR_RESULT ./candidates/SKILL_NAME --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST
ergora skill import my-project ./candidates/SKILL_NAME --hypothesis '填写可检验的改进假设'
```

Export rechecks original input and both explicit digests, saving complete original file bytes and executable bits. It does not execute files, create State, query live sources, import or adopt. Existing targets, targets inside frozen input, unpreservable identities and results without a candidate are refused; publication does not replace an empty directory that appears concurrently. Failure removes only this operation's private staging and retains existing targets. On a lost reply, retain original input/result/candidate digest and inspect the existing target; do not overwrite or delete it to bypass refusal. An explicit import must return the selected candidate's digest. With a baseline already present, import only registers the candidate and leaves the active head unchanged.

Use a maintainer-prepared trusted evaluator and suite to evaluate baseline and candidate with the same suite. A model proposal's evaluation_plan or self-reported score is not a trusted suite:

```bash
ergora evaluation register my-project ./evaluation.json
ergora evaluation run my-project BASELINE_DIGEST --suite SUITE_DIGEST
ergora evaluation run my-project CANDIDATE_DIGEST --suite SUITE_DIGEST
ergora evaluation compare my-project BASELINE_RUN_ID CANDIDATE_RUN_ID
ergora skill adopt my-project --baseline-run BASELINE_RUN_ID --candidate-run CANDIDATE_RUN_ID --revision HEAD_REVISION --reason '填写审阅评价证据后的采用理由'
ergora skill rollback my-project SKILL_NAME BASELINE_DIGEST --revision ADOPTED_HEAD_REVISION --reason '填写回退理由'
```

Fill the placeholders with the exact suite digest/run IDs returned by register and both runs. compare's eligible flag, complete trusted evidence, current head and explicit reason together determine adoption. A changed head causes the original adoption to refuse; choose the current baseline and evaluate again rather than changing only revision to force an old result. rollback uses the head revision after adoption, appending history without deleting candidates or old evaluations. A null candidate requires no export or fabricated improvement. See [Skill candidate evaluation and adoption](skills-and-evaluation.md#skill-candidates-evaluation-and-adoption) for the complete suite contract.

## Generate a provenance-bound memory retrospective candidate

Prepare memory suggestions using the same project's complete handoff package and selection. Install `memory-retrospective`, then use the [manifest steps](../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory) to pin root `ergora-memory-retrospective 1.0.3` into `memory-retrospective-manifest`. Its `root/propose` and `root/review` both default to Codex gpt-6.2-sol high. Permissions and explicit invocation follow the preceding steps; all leaves read all ancestor materials.

```bash
ergora composition install-preset memory-retrospective
ergora memory catalog my-project
ergora retrospective prepare-memory my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --memory-id MEMORY_ID --revision MEMORY_REVISION --objective ./objective.txt --manifest ./memory-retrospective-manifest --instance root/propose --directory ./memory-author-input --max-prompt-bytes 500000
ergora composition run-input my-project ./memory-author-input --backend codex --mode text-only --timeout 240
```

A correction must select an exact currently valid ID/revision from catalog. Stale, expired, deleted or other-project records are refused. For a new-memory suggestion, replace `--memory-id MEMORY_ID --revision MEMORY_REVISION` with `--new-memory`; its baseline is explicitly null with revision 0. prepare first verifies complete original evidence, then observes the canonical record and freezes its complete body, provenance, expiry and observation time. That observation does not guarantee future validity. The original prompt capacity is checked separately; over-capacity input explicitly fails without truncating the complete body.

After obtaining the author's original `result` and `result_sha256` receipt, inspect it offline and pass complete checked JSON to the original review leaf:

```bash
ergora retrospective check-memory ./memory-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./memory-checked.json
ergora composition prepare-from-manifest ./memory-retrospective-manifest root/review --task ./memory-checked.json --directory ./memory-review-input --max-prompt-bytes 500000
ergora composition run-input my-project ./memory-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

The author supplies a complete candidate body (at most 100000 characters), hypothesis, applicability and validation plan under the frozen schema, or returns null. Original failures, unknown costs and exact material references for each observation remain. The model cannot choose provenance, expiry or revision. check's `save` contains only the complete body usable by the original memory interface, fixed provenance derived from package SHA and selection SHA, and original ID/expected_revision. candidate_digest binds complete save content and baseline identity. Offline inspection creates no State, queries no live memory and authenticates no source author; it establishes neither current validity nor quality improvement. The original result limit is 8 MiB, and the complete review prompt has a separate capacity check. If the backend is unavailable, retain the original invocation facts; any explicit override must still satisfy the selected definition minimum.

After reviewing a nonnull candidate's original evidence and validation plan, explicitly export:

```bash
ergora retrospective export-memory ./memory-author-input AUTHOR_RESULT ./candidates/project-memory --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST
```

The new directory contains complete original UTF-8 `memory.txt` bytes and `receipt.json`; the command also returns the receipt. Use its `save.source.uri`, `save.source.revision`, `save.memory_id` and `save.expected_revision` in the original save command below. The project must equal receipt.project. `memory save --text` preserves original newlines and all Unicode characters, including an initial U+FEFF; manually written input does not automatically lose that character either. Directory publication refuses existing targets or locations inside frozen input. It does not automatically save, change original memory or update the ReMe projection. On a lost reply, check the original directory/receipt and text SHA before proceeding, without overwriting or exporting again.

Alternatively, choose “Long-term memory” for the same project in the console. For new candidates use “Add memory”. For corrections, first check the original ID/revision in the receipt, then choose “Correct” on that record. Select exported `memory.txt` in “Body UTF-8 file”: it takes precedence over the text box and preserves the complete BOM and newlines. Fill the source URI and revision from the receipt, explicitly check expiry, then save. Invalid UTF-8 leaves the form open with an error. Manual text-box edits use browser newlines; an unedited existing body retains its original string.

After saving, the window shows this submission and original returned record. Explicitly use “Refresh” at the upper right to read new state. History displays complete bodies/provenance and expiry. Select one original revision to restore explicitly; restoration appends a revision and retains that history entry's expiry. On a correction conflict or abnormal reply, refresh and check the original directory, ID and revision before deciding to reopen the form. The request may already have executed; the page does not resend automatically. Deletion clears all historical bodies/provenance irreversibly. Projection synchronization and rebuilding require explicit submission in separate forms; configured backend ownership still determines remote visibility.

```bash
ergora memory save my-project --text ./candidates/project-memory/memory.txt --source SOURCE_URI --source-revision SOURCE_REVISION --id MEMORY_ID --revision MEMORY_REVISION
ergora memory history my-project MEMORY_ID
ergora memory restore my-project MEMORY_ID --from-revision BASELINE_REVISION --revision CURRENT_REVISION
```

For new memory, omit `--id` and `--revision` and use the new ID returned by the original save. Omitting expiry parameters in a correction retains the existing expiry through its original owner. Even if memory expired after candidate generation, saving does not renew it or make it recallable. Renewing expiry requires a separate explicit choice in the original save. A changed or deleted original revision refuses stale saving; select a new baseline. If a save reply is uncertain, check catalog/history first, especially before any retry that would create new memory. Restoration appends the original revision with its expiry; deleted content cannot be restored. This path has no Skill-style trusted-suite adoption gate: model approval reviews the proposal only. Validation and explicit writing remain separate. Workflow candidates follow the original definition-revision contract separately.

## Generate a provenance-bound workflow retrospective candidate

Install `workflow-retrospective`, then follow the [complete manifest steps](../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory) to save root `ergora-workflow-retrospective 1.0.2` into `workflow-retrospective-manifest`. Separately save complete `target-manifest` for the root to improve, retaining the complete digest from its original check. The first is the author/reviewer graph; the second is the target graph. Prepare handoff, selection and objective through the [Skill-candidate steps](#generate-a-provenance-bound-skill-retrospective-candidate), all from the same project.

```bash
ergora composition install-preset workflow-retrospective
ergora retrospective prepare-workflow my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --target-manifest ./target-manifest --target-digest TARGET_MANIFEST_DIGEST --next-version 1.0.1 --objective ./objective.txt --manifest ./workflow-retrospective-manifest --instance root/propose --directory ./workflow-author-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-author-input --backend codex --mode text-only --timeout 240
```

`--next-version` must name an unused immutable root version; existing versions cannot be overwritten. The target package's complete recursive definitions, resource bodies, executable bits and directories, including empty directories, are frozen. Files total at most 1 MiB. Binary, NUL or over-limit content is refused without truncation. target-digest uses the original manifest's file/executable-bit identity; frozen baseline.digest additionally binds complete directories. The export receipt retains both identities and directories. Once preparation succeeds, loss of target sources does not prevent offline inspection. Total prompt capacity remains separate; set `--max-prompt-bytes` for the actual backend's limits.

```bash
ergora retrospective check-workflow ./workflow-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./workflow-checked.json
ergora composition prepare-from-manifest ./workflow-retrospective-manifest root/review --task ./workflow-checked.json --directory ./workflow-review-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

Author and reviewer read complete ancestor materials and predecessors. Backend selection/failure preservation follows Skill candidates above; static dependencies do not execute ports automatically. Inspection permits `candidate:null`. Otherwise it checks original preview, complete resources, graph and original grant, writing only in an automatically cleaned private temporary directory without reading/writing active State. The first version permits only root description, NUL-free UTF-8 content in already-declared resources and extra dependency edges. It preserves original nodes/references/ports/permissions/review requirements and existing dependencies. Change those structures through original manual version revisions.

After checking complete `revision_preview` and provenance, explicitly select the `candidate_digest` returned by check. A missing candidate cannot be exported.

```bash
ergora retrospective export-workflow ./workflow-author-input AUTHOR_RESULT ./candidates/workflow-root --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST > ./workflow-export-receipt.json
ergora composition check ./candidates/workflow-root
ergora composition import ./candidates/workflow-root
```

The export directory must be new and preserves the complete root bundle and reference identities. Save the stdout receipt separately; no extra receipt is inserted into the directory to contaminate package identity. Another machine must first have the same subdefinitions; original import checks dependencies and ID/version conflicts. After importing, prepare a manifest for the new version through the original steps and explicitly select it. For rollback, select the original root/manifest again; old runs always retain old snapshots. Export, model approval and graph admission do not establish quality/performance evaluation or authorize adoption. Effect comparisons still require the same trusted workload and independent validation.

Continue: [Evaluate and adopt Skill candidates](skills-and-evaluation.md) · [Manage project memory and optional ReMe](memory.md) · [Revise and share exact workflow versions](../definitions/workflows/revisions.md).
