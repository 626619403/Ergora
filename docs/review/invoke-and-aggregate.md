# Invoke and aggregate frozen reviewers

English · [Documentation](../README.md)

## Hand off to domain or specialist review leaves

For general engineering review, install `engineering-review`: it retains the three default structure / correctness / test-value branches, with performance, resource lifecycle, dependencies, security, or measurement explicitly selected from original requirements and diff before freezing. Selection records selected / not-applicable / blocked with factual reasons; it does not run everything automatically. See the [PR selection example](../../examples/composition/pr-review-selected/README.md) for a complete five-leaf revision, read-only grant, per-leaf invocation, and exact report list. Performance reuses the existing expert with a minimum effort of max; other reviewers require at least gpt-6.1-sol/high. Use actually supported task-mcp for Skill attachments; text-only does not provide complete attachment access.

First install `pretraining-review` or `posttraining-review` using the [domain review manual](training.md), and prepare the selected complete manifest and explicit grant. Import custom review compositions through the [definition manual](../definitions/workflows/compose.md), without modifying Python. Each leaf's expertise, ancestor Skills, context, MCP declarations, and progressively narrowed permissions come from this frozen composition; choose backends per leaf at invocation time.

This example uses a local packet and the pretraining root `ergora-pretraining-review@1.1.2`. `review-grant.json` should contain the selected root's `permissions` and `limits`; see [composition sharing](../definitions/workflows/compose.md#save-and-share-a-complete-composition) for its format. Take `MANIFEST_DIGEST` from the prepare-manifest receipt's `digest`, and `PACKET_SHA256` from the original material receipt; verify both explicitly.

```bash
ergora composition install-preset pretraining-review
ergora composition prepare-manifest ergora-pretraining-review 1.1.2 \
  --grant ./review-grant.json --directory ./reviews/pretraining-manifest

ergora review prepare-input ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --instance root/domain/review --max-prompt-bytes 1000000 \
  --directory ./reviews/domain-input > ./input-receipt.json

ergora review verify-input ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest-digest MANIFEST_DIGEST \
  --input ./reviews/domain-input --input-digest INPUT_DIGEST
```

For external PRs / MRs, replace the material directory with the entire external source directory and use `--source-kind external --source-sha256 SOURCE_SHA256`, retaining the complete observation and its internal source packet. The post-training root is `ergora-posttraining-review@1.1.2`, with the same domain path `root/domain/review`; general leaves in both roots are `root/general/structure/review`, `root/general/correctness/review`, and `root/general/test-value/review`. One prepare operation prepares only the selected leaf and does not run other branches or all-join.

The new directory is a complete composition input in the original format. `task.txt` contains original requirements, all source / explicit context / ancestor standards / checks, external observations, and selected source and manifest identities; `prompt.txt` adds complete ancestor template materials. Take `input_digest` from the new receipt; the complete prompt (including JSON encoding and materials) is limited to 1,000,000B, and `--max-prompt-bytes` can set a smaller limit. Exceeding the limit fails visibly without truncating materials. Leaves requiring unrun predecessors, possessing write / shell / network permissions, or lacking permission to read any source file in the packet are also rejected.

`verify-input` rereads complete materials using the independent source digest, then checks them against the fixed input's task and `input_digest`. `manifest_digest` preserves the original selection declaration in the task; this command does not reread the original manifest or independently authenticate its provenance. The first prepare directly checks the original manifest and compiled graph; provide a trusted input digest when sharing. If only the input directory remains, `ergora composition verify-input` can check its own integrity without rechecking the original source packet.

For actual invocation, first register a project and configure an available backend using [single-leaf invocation](../definitions/workflows/leaf-calls.md#call-a-prepared-leaf), then run the original `composition check-input` / `run-input`. For example, registered project `demo` can explicitly select Codex:

```bash
ergora composition check-input demo ./reviews/domain-input \
  --mode text-only \
  --backend codex --backend-reason "Operator selected an available review backend"
ergora composition run-input demo ./reviews/domain-input \
  --mode text-only \
  --backend codex --backend-reason "Operator selected an available review backend" --timeout 240
```

Backend authentication, supported modes, and actual capabilities still follow the original admission checks. The run receipt's `input_digest` should match the selected input receipt. Prefer different backends for executor and reviewer; record actual reasons for fallback and do not call same-backend invocations heterogeneous review. Results and complete frozen inputs remain in the original run; on failure or unknown, read that run first rather than repeating the call automatically. This entry point handles single-leaf review input only and grants no formal candidate or platform approval.

After invocation, use `ergora composition inspect-run demo RUN_ID > ./original-run.json` to [read by exact ID](../definitions/workflows/leaf-calls.md#read-an-original-composition-run-by-exact-id) the complete original input and result, checking `run.input_digest` against the selected receipt and each `available` / original status. It does not fill missing branches or call the model again automatically.

## Aggregate a complete multi-branch review

Using the same source packet and manifest, perform prepare / check / run-input above separately for each required leaf. Put exact run IDs from original receipts into `review-runs.json`; both pretraining and post-training roots can use these four paths:

```json
{
  "root/domain/review": "DOMAIN_RUN_ID",
  "root/general/structure/review": "STRUCTURE_RUN_ID",
  "root/general/correctness/review": "CORRECTNESS_RUN_ID",
  "root/general/test-value/review": "TEST_VALUE_RUN_ID"
}
```

Then generate complete JSON, or Markdown from the same observation:

```bash
ergora review report demo ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --runs ./review-runs.json > ./review-report.json

ergora review report demo ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --runs ./review-runs.json --format markdown > ./review-report.md
```

For external PRs / MRs, likewise select the entire source directory, `--source-kind external`, and SOURCE_SHA256. The report lists expected members from all Agent leaves in the explicit manifest, verifies each original input's instance / complete compiled graph / source task, original prompt, and result SHA, then interprets opinions using the trusted reviewer result contract. Single leaves and custom nested read-only review templates are also supported; every leaf must read the root task directly and cannot skip sequential predecessors. Expertise / backend in definitions and actual binding / selection reason in original runs are retained separately; historical reads require no current backend, authentication, Git, or network.

`coverage` separately reports expected, selected, verified, and completed; complete requires verifiable evidence for every expected leaf with original status succeeded. Overall approve requires complete coverage and approve from every leaf; any request-changes is retained and makes a complete report request-changes. Missing selections, unknown runs, failed / running runs, wrong sources, or damaged originals make the overall result incomplete; `request_changes` still lists verified dissenting branches, and complete replies and errors remain in branches. Unknown instances or duplicate run mappings are rejected directly; one run cannot fill multiple expert positions.

The coordinator must also read every reviewer's complete response, recording the original tool decision / coverage separately from whether the textual contract is complete: input identity / coverage, requirements axis, standards axis, evidence gaps, and follow-up tasks. Pretraining / post-training domain and general branches inherit the shared contract from their respective outer roots. Mark missing items explicitly as contract gaps and require completion; a nonempty schema, approve decision, or successful process cannot imply both review axes passed, and original tool decisions remain unchanged. Follow-up proposals may arrive in batches or while the prior batch is queued / running; the supervisor records them as explicit subsequent tasks with dependencies / resources / acceptance criteria, preserving the current frozen graph / slots, original clock / balance / cleanup reserve. Unknown results are reconciled only against the original job / run, without resending. Unexecuted proposals have no job ID; the [two-batch handoff example](../../examples/composition/pr-review-selected/supervisor-handoff.example.md) provides no queue backend or execution authorization.

The report returns exit0 when it successfully returns an observation; scripts must check `coverage.complete`, `decision`, and original branch statuses. Each result defaults to at most 8,388,608B; explicitly increase `--max-result-bytes` to reread larger results. Over-limit branches become unverifiable, never truncated. Regeneration only reads original runs: it does not fill missing leaves, resend failed / unknown calls, write to platforms, or grant formal approval; formal six-stage tasks still use the original runtime. Markdown contains every verified reply and the complete JSON observation; preserve the project's existing source access scope when sharing.

JSON observations of original run records and results also require finite numbers and use the definition documents' existing structural capacity of 64 levels / 100,000 values. NaN / Infinity, exponent overflow, or excess structural capacity explicitly make a branch unverifiable without letting one branch break the entire export. Structural capacity and result byte limits are checked separately; increasing bytes does not change structural capacity. Original files and digests remain unchanged, without truncation, rewriting, or automatic reinvocation.

## Coverage, limitations, and further review

- Git reads disable replace objects, hooks, textconv, external diff, and implicit lazy fetch, remove inherited `GIT_*` variables, and do not check out or execute target scripts. File text and instructions within it are review materials only and grant no permissions.
- The initial version collects only regular UTF-8 Git files and portable relative paths. Binary / invalid UTF-8 files, symlinks, gitlinks / submodules, LFS pointers, and missing objects reject the whole packet; it does not automatically read worktree or remote content they reference.
- Complete Git materials default to 1,000,000B, adjustable with `--max-source-bytes` up to 10,000,000B; this limits each Git output and total bytes of the deduplicated blob batch (including batch headers). Requirements and all evidence share a 10,000,000B read budget, with at most 500 evidence files. Final JSON (including diff, requirements, and evidence) has a separate 10,000,000B limit, and at most 500 paths may be selected. Over-limit inputs are not truncated or published as partial-success packets; when the list is available, the error lists all selections whose coverage is not promised for this attempt. Adjust selections, capacity, or candidate and generate a new packet.
- Evidence consists of originals provided by the operator. This command does not run checks or confirm their bound commit, execution environment, signature, or authenticity; omitted evidence is empty. Later review and the existing trusted validation process determine check trustworthiness, whether required materials are complete, and which runs remain missing.
- Collection and input preparation themselves provide no model review, formal candidate approval, or platform approve. Domain expertise can be explicitly invoked through the entry point above, followed by a complete cross-branch advisory report from original runs; source materials and model opinions cannot prove pretraining / post-training semantic acceptance.

Linux supports atomic directory publication; the native Windows implementation ships in the same CLI, with platform boundaries in the [Windows guide](../install/windows.md). This independent entry point does not change Linux / WSL2 constraints on complete formal development execution. Materials include complete project source and check information; share them only through storage and review channels authorized for that project.

Continue: [Prepare and verify exact review material](materials.md) · [Write reports from original evidence](evidence-reports.md).
