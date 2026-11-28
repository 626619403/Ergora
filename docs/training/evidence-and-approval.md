# Read training evidence and approve exact results

English · [Documentation](../README.md)

Read original archives and observations with their exact digests. [Execution and stopping](execution.md) have their own records; readable evidence or approval delivery does not establish execution, measurement acceptance or adoption.

## Read archived evidence and original integration tickets

`show` displays original job/gate; `evidence` additionally reads content-addressed archives bound to the same project and manifest, without Temporal SDK or running services:

```bash
ergora training evidence my-project EXPERIMENT_ID
ergora training evidence my-project EXPERIMENT_ID \
  --artifact checks/forward.json --evidence-sha256 EVIDENCE_SHA256 \
  --offset 0 --limit 12000
# screen先读索引，路径取report.artifacts，摘要取screen.result_sha256
ergora training evidence my-project SCREEN_EXPERIMENT_ID
ergora training evidence my-project SCREEN_EXPERIMENT_ID \
  --artifact checks/finite.json --screen-result-sha256 SCREEN_RESULT_SHA256 \
  --offset 0 --limit 12000
```

With existing typed screen originals, the result contains `archive_status:no_accepted_archive`, `recorded_gate_report:null` and `screen={result_sha256,report,cleanup}`. `screen_status` is complete or cleanup_unavailable; the latter means original stop evidence is incomplete, so existing reports cannot replace cleanup. Without typed originals it is not_recorded/screen:null. Reports retain actual scope/checks/resources/decision and raw index. Full archives still use `evidence_sha256`; screen originals accept only `screen_result_sha256` matching this screen's `screen.result_sha256`. Digest kinds are mutually exclusive. Python `training.application.evidence` uses the same keywords. Without artifact, read only the index and pass no digest. Window/capacity rules match full-original reading below.

First check complete gate, original `evidence.json` and byte SHA, archived `gate-result.json`, manifest/baseline/comparator digests and current-baseline applicability. No gate or a failed gate returns `archive_status: no_accepted_archive`, creating no archive or approval. Passed gates with incomplete/conflicting records fail explicitly. Archived gate JSON is checked against the job's archive_report; SHA-bearing evidence/manifest/baseline/comparator are checked by original bytes. Existing original local `integration-ticket` is read against complete project/binding/evidence. `automatic_merge: false` does not mean actual revalidation completed, current receipts remain valid or Temporal terminal state was confirmed.

`archive.evidence.artifacts` preserves original paths and declared digests. `artifact_content_status: not_read` explicitly means all file content has not been checked. Select one artifact and this complete evidence SHA; the entry point reads the entire file, verifies original SHA, then returns a Unicode-character window of UTF-8 text. Continue at `next_offset`. Each JSON is limited to 1MiB, selected artifacts to 16MiB, returned windows to 65,536 characters and total response to 8MiB. Oversize/binary/NUL/digest drift/symlink/out-of-bounds inputs are explicitly rejected, never truncated and called complete. Large/binary profiles use original indexed locations and appropriate tools, without decoding through this text entry point.

HTTP also uses `GET /api/projects/{project}/training/{experiment}/evidence`, with optional `artifact / evidence_sha256 / screen_result_sha256 / offset / limit` and the CLI's digest-type/mutual-exclusion rules. This sends no RPC, reruns no comparator/runner, generates no owner receipt and neither approves nor adopts. It checks saved material identities for human review. Real quality, author trust, current approval eligibility and actual integration effects still require their original independent processes. Exact owner approval CLI/HTTP follows next; graphical steps appear below.

Python `training.application.baseline_reference(state, project_id, experiment_id, evidence_sha256=...)` reads all indexed artifacts, transitive references, original managed chain and stop facts of an exact accepted archive, returning immutable `reference`, `reference_sha256` and `anchor_sha256`. Its inventory covers original archive and execution-bound originals. The current-registration authentication guard retains first identity and rechecks at the end of the same bounded read, outside immutable index/hash. It does not reinterpret original evidence using current baseline head, runner configuration or integration tickets; fence presence and absence are both confirmed at the end. Original receipts/environment reports retain full raw digests; derived receipts retain code inventory/commit/entrypoint and actual environment identity, omitting original checkout/interpreter installation locations. Limits are 16MiB per item, 256 items, 64MiB complete inventory, 1MiB per metadata file and 8MiB complete response. Oversize, missing files or original drift fail explicitly. This and `evidence` use the current package's SDK-free reader, preserving registration, control-home and canonical-path checks. Missing selected native installation does not withhold history. Original-registration recovery is unsupported in these two entry points. Without baseline-specific actual oracle, original source manifest or stop confirmation, complete inventory remains readable with each dimension explicitly unavailable. Generic candidate checks, full gate PASS and historical timing cannot certify baseline quality.

To consume a reference in managed full, freeze the sole `baseline_reference={experiment_id,evidence_sha256,reference_sha256}` in the experiment manifest. The selected driver must declare `baseline-reference-v1` and implement `baseline_reference_read(context, request, reference)` and `baseline_reference_record(context, request, output)`. The first declares five fixed invariants, legal batch/chunk/parallel differences and target-oracle applicability in the same context; core syncs and reads back `baseline-reference-read.json` before admitting original run. The second only collects already-executed baseline actual outputs, independent oracle/expected, environment and window reports; core binds original source/execution into the archive. Resource metric/unit/aggregation must be nonempty text; scope is nonempty text or a bounded finite JSON object. Malformed data is rejected, while valid unknown units explicitly become unavailable. Baseline quality, historical timing and resources are separate. Measured resources exceeding declared softlimit retain their report and become resources.invalid; quality/historical timing remain readable according to their own evidence. Current-candidate quality still follows the original full contract. Both arms execute real independent AB/BA each time; historical windows never fill new pairs, and baseline is never automatically adopted or advanced. Reading, callbacks and collection all use the original clock and unique reaper.

### Read a retained local archive after unsuccessful execution

Use `ergora training evidence my-project EXPERIMENT_ID --retained-archive` when the original managed full job wrote a passing local gate before later execution failed. The original Job request, start, managed attempt and saved reap record select the scope. The fixed report supplies the original manifest and content address. A saved `FAILED` or `CANCELLED` result keeps its original state. A missing native result stays null and requires an unsuccessful executor observation. The view reports the saved process status and return code without inferring the failure cause or live state.

`retained_archive.status: verified` covers the archived evidence, gate report, original archive output, manifest, baseline and comparator bytes plus every original indexed artifact. The leading JSON in the original archive output must match the gate's complete archive report. The reader confirms the bound records and file bytes again before returning. Limits are 256 artifacts, 16 MiB per artifact and 64 MiB for the complete read. Incomplete ownership, missing material, capacity overflow or source drift return `unavailable` with the reason.

New managed full launches require a tracking checkpoint. Before returning a passing local gate, the archive command synchronizes the verified, indexed primary evidence and its published directory entries. The original executor then saves the checkpoint before calling the native MLflow exporter. It binds the raw managed attempt, original clock, gate, archive output and evidence digests. A missing required checkpoint leaves the retained archive unavailable. The retained archive view reports `returned` with the tracking run ID or `raised` with the local error type. A verified checkpoint with no saved outcome remains `unknown`. Earlier launches without this requirement report `not_recorded`. The observation makes no current provider-state or retry authorization claim.

If MLflow reports an existing Run bound to the manifest, including a soft-deleted Run, the ordinary exporter refuses before making any additional provider writes. Reconcile earlier or uncertain writes against the original Run and obtain separate authorization before retrying. For new executions, prepare native sources that match the selected Ergora application's descriptor. In-flight executions keep their original application and native source pairing. Verified historical retained archives remain readable through the same evidence command. [Prepare matching native sources](prepare-experiments.md#prepare-versioned-native-sources)

A managed archive process must return a passing durable report or a matching evaluated negative comparator result before tracking can start. A timeout, signal or missing process outcome leaves the original archive failure for inspection. A verified negative result preserves its ordinary failed gate and tracking record, with no passing archive or tracking checkpoint.

Once `retained_archive.status` is `verified`, rerun `ergora training evidence my-project EXPERIMENT_ID --retained-archive` with `--artifact INDEXED_PATH --evidence-sha256 RETAINED_EVIDENCE_SHA256`. Take the path from `retained_archive.archive.evidence.artifacts` and the digest from `retained_archive.archive.evidence_sha256`. Use the same UTF-8 text window rules with `--offset` and `--limit`, and continue at `artifact.next_offset`. The response adds the top-level `artifact` window and retains the original native result state, tracking status, fence observation and `archive_status: no_accepted_archive`. An unavailable archive, unindexed path, mismatched digest or corrupt artifact fails explicitly.

On the same GET, combine `retained_archive=true` with `artifact`, `evidence_sha256`, `offset` and `limit`. Python `training.application.evidence` takes the same keywords with `retained_archive=True`. Retained archive observation reads only saved local files. Exporter calls, launch, retry and resource release remain with their original owners. The original accepted archive remains the input to baseline references, approval and round advancement.

#### Observe selected effects on the original MLflow Run

For a verified retained archive with `tracking.status` equal to `raised` or `unknown`, use the original registered Linux environment and an independently observed original MLflow Run ID. Take both SHA-256 values from the retained archive response. A manifest match alone cannot supply the Run ID.

```bash
ergora training tracking-observe my-project EXPERIMENT_ID \
  --evidence-sha256 RETAINED_EVIDENCE_SHA256 \
  --tracking-attempt-sha256 ORIGINAL_TRACKING_ATTEMPT_SHA256 \
  --mlflow-run-id ORIGINAL_MLFLOW_RUN_ID \
  --metric gate_passed --artifact INDEXED_PATH
```

The command uses the original loopback MLflow route. It verifies the pinned Run against the original experiment, manifest, commits and Job tags. A foreign, mismatched, inactive or ambiguous selection returns the corresponding status without fetching effects. The bound response shows up to 256 rows for the selected original metric, including the step, timestamp and value of each row and the number matching the frozen value at step zero. A larger history fails explicitly. The selected artifact read verifies up to 16 MiB under the pinned Run's local artifact route and reports its current digest and whether it matches the archived bytes.

The metric rows and current artifact are separate observations. Matching rows do not identify which attempt wrote them, and matching artifact bytes can survive multiple uploads. Missing data does not rule out an earlier write. Every observation leaves retry authorization false.

## Multi-round evidence index

First select this project's existing original experiments with `ergora training list my-project`. This entry point collects original records only; it neither runs experiments nor advances baselines. Collection uses the original training entry point, requiring a registered training project and `ergora[temporal]`; it connects to neither Temporal nor models. Offline index reads need only the core installation.

Write the first-round selection to `round-1.json`:

```json
{
  "schema_version": 1,
  "rounds": [{
    "experiment_id": "exp-001",
    "change": "本轮实际变化；只作操作者注释，不能代替原证据",
    "next_bottleneck": "未知；等待原报告支持后再选择下一干预"
  }]
}
```

```bash
ergora training rounds-create my-project --definition round-1.json --directory ./rounds-1
ergora training rounds-read ./rounds-1
```

Output `sha256` pins the complete `rounds.json`. Write the second selection in another same-format `round-2.json` using existing `exp-002`. Replace `PREVIOUS_INDEX_SHA256` below with the first step's actual output, then explicitly append in a new directory:

```bash
ergora training rounds-create my-project --definition round-2.json --directory ./rounds-2 \
  --previous ./rounds-1 --previous-sha256 PREVIOUS_INDEX_SHA256
ergora training rounds-read ./rounds-2 --sha256 NEW_INDEX_SHA256
```

Old rounds' original observations and predecessor identities remain complete, without recollection/overwrite. One original experiment cannot count twice as two rounds. Initial `initial_anchor` is separate from each round's `comparison`: its `baseline_commit` is the actual comparison reference and `candidate_commit` is this round's candidate, both from original manifests. The current original registry supports no implicit baseline advancement; the first index version accepts only the same original baseline/workload and registered project. Current baseline matching remains separately recorded through original observations; the index cannot turn historical mismatch into approval eligibility.

Each round retains original `inspect`/`evidence`/`submission` JSON values, original file SHAs and archive index. Original approval-delivery records are read only after submission. Failures, gate rejection, nonacceptance, pending and unknown remain. Approval delivery does not establish current authorization, and multiple collected observations are no live atomic snapshot. Binding, gate or read-original identity conflicts reject publication; different observations cannot be assembled into a success conclusion.

`change`/`next_bottleneck` always remain unverified annotations outside gates. Offline reads check the entire expected SHA, round contents and predecessor links, without service connections, statistical reevaluation or provenance authentication. Original logs, large traces and artifact content stay in original storage. The index replaces no backup and does not mean all artifacts were read. Each index is limited to 32 rounds/10MB; overflow fails explicitly without truncation. Extensions overwrite neither old nor existing target directories. See the [original JSON schema](../../src/ergora/data/schemas/training-rounds-v1.json).

Kernel experts still assess through the common proposal path. The index neither skips them nor starts the next round, adopts candidates, rewrites thresholds or calculates cumulative gains automatically. Bounded automatic loops and cross-baseline migration require their own contracts.

## Exact owner approval and delivery recovery

First read original archived evidence, explicitly confirming project revision, complete original `submission` run ID and complete evidence SHA:

```bash
ergora training approve my-project EXPERIMENT_ID --revision REVISION \
  --run-id RUN_ID --evidence-sha256 EVIDENCE_SHA256 --confirm
ergora training approval my-project EXPERIMENT_ID
ergora training resume-approve my-project EXPERIMENT_ID --revision REVISION \
  --intent-sha256 ORIGINAL_INTENT_SHA256 --confirm
```

The caller makes an owner decision as the current Linux user; the local trusted-project/current-user boundary still applies, without team multi-user authentication. Original approval CLI checks AWAITING_RELEASE, binding and evidence, then creates a private owner receipt. Original release client sends it; original adapter decides authorization and local integration-revalidation ticket. Application records `ergora/training-approvals/EXPERIMENT_ID.*.json` must be retained with original `training/approvals/`, start/job/archive and Temporal history.

`prepared` means original intent saved, potentially with an original receipt but not yet sent. Explicit recovery preserves original bytes and expiry without renewal. `owner_receipt_status: unknown` means the original receipt-creation attempt is saved without a ready fact; if originals are missing, recovery refuses regeneration and the owner must reconcile. `unknown` means attempt saved with unconfirmed delivery. Recovery only checks complete release signals in pinned original-run history; absent signals remain unknown without resending. `requested` means send ack or full history match and proves delivery only, with `authorization_status: not_evaluated`. It does not mean original owner acceptance, ticket creation, real integration success or candidate adoption. Verify later facts separately through original `status` and `evidence`. `approval` needs no SDK/service and exits 0 on successful reads. `approve`/`resume-approve` exits 0 only for requested, 1 for other record states; input/runtime errors use general exit 2.

Each experiment has only one approval intent through this entry point; changing request IDs cannot bypass unknown. Before first send, sources/baseline must remain intact and no fence may exist. Expired/revoked/nonprivate/drifted original receipts are preserved and rejected, without automatic renewal or approval of different evidence. Another human decision first requires explicit original-owner reconciliation; this entry point never automatically overwrites. Do not delete checkpoints or change experiment IDs to bypass it. Post-send recovery does not require changed/deleted manifest, runner, baseline or archive still to exist, and does not send a new signal because of their absence.

HTTP reuses the same use case: `GET .../training/{experiment}/approval`; `POST .../approve` (`revision / run_id / evidence_sha256 / confirm: true / timeout`); `POST .../resume-approve` (`revision / intent_sha256 / confirm: true / timeout`), with timeout 1–60 seconds. Native Windows reads saved local records; approval/recovery use registered Linux/WSL2 environments.

## Review evidence and approve in the console

In “训练实验”, select “查看原件” for the original experiment, then “证据审阅与 owner 批准”. The page reads original archives and local approval records only after clicks; it never automatically queries runtime or approves.

1. Click “读取原归档证据”, expand complete gate, binding, evidence, manifest, baseline and digests, and check current baseline. Artifact indexes do not establish body verification. Expand the text window, select original path, paste this complete evidence SHA and enter character offset/limit before reading. Continue with “读取下一证据窗口”; binary/oversized materials use original indexes and appropriate tools.
2. Click “读取本地批准记录”. With no intent and a readable current archive, verify complete original run ID and evidence SHA, fill confirmation and click “确认 owner 批准”. Rereading evidence rebuilds confirmation fields; finish reading before filling confirmation. Approval appears only on Linux/WSL2.
3. For existing `prepared` or `unknown`, confirm original intent SHA and click “恢复原批准意图”. With an existing send attempt, recovery only queries pinned original-run history. Existing intents can be independently read/recovered even if original experiment details or current archive are unreadable. Unknown credential creation and unknown signal delivery are shown separately.
4. Without a reply, first click “读取原批准记录恢复”, then explicitly act on the original intent; the page never retries automatically. `requested` means delivery only. Read original runtime and ticket, then use “前往正式任务页” to manually bind original candidate/evidence and complete project integration revalidation. This button creates no task, ticket, merge or adoption.

After switching experiment/project, explicitly reread the corresponding materials. Panel controls are disabled during sending. In-flight reads of the same evidence can complete; changing selection/window discards old body text.

Continue: [Create a formal development task](../development/tasks.md) · [Write reports from original evidence](../review/evidence-reports.md).
