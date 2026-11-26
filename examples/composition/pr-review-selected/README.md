# Explicit engineering review selection

This example selects five required reviewers for a process/concurrency change with performance implications: the existing structure, correctness and test-value branches, plus performance and resource lifecycle. The bundled `engineering-review` default remains the three core branches. Select specialists with facts before preview/freeze; there is no automatic diff classifier. Dependency, security and measurement are installed options and do not run unless selected. Missing evidence is `blocked`, not automatically `not-applicable`.

The revision uses the existing `ergora-delivery-review@1.2.7` base, digest `5eb05a0f3b48757108ec078323828c5252e6664a6cccdad7e3514161a9d581a5`. It publishes `ergora-selected-engineering-review@1.0.7`, digest `250ab99fb8db86e232abcbf11550e32183e418a6c5934f37acc3bfcb67fb0fbb`. The standard revision contains references only; inherited instructions and Skills remain in their original bundles. Old library objects and frozen tasks retain their identities.

From the repository root, use an explicit definition-library home. Every command below uses that same home:

```bash
ergora --home ./review-home composition install-preset engineering-review
ergora --home ./review-home composition revise ergora-delivery-review 1.2.7 \
  --base-digest 5eb05a0f3b48757108ec078323828c5252e6664a6cccdad7e3514161a9d581a5 \
  --document examples/composition/pr-review-selected/root.revision.example.json
ergora --home ./review-home composition prepare-manifest ergora-selected-engineering-review 1.0.7 \
  --grant examples/composition/pr-review-selected/grant.json --directory ./selected-review-manifest
```

Save the returned manifest `digest`. The exact member paths are `root/structure/review`, `root/correctness/review`, `root/test-value/review`, `root/performance` and `root/resource-lifecycle`. They consume the same root task independently and all feed the existing all-join. The grant is readonly: read workspace/definitions, write none, shell false and network none. Performance keeps its existing `gpt-6.2-sol/max` minimum because it also serves planning; the other reviewers require at least `gpt-6.2-sol/high`.

Assign reviewers by the applicable review scope and evidence needed for this change. The formal graph can schedule ready reviewers under the approved ancestor concurrency caps. The explicit source loop below invokes them sequentially.

For an independent PR/MR source, first prepare the complete local or external source as described in [LOCAL_REVIEW](../../../docs/review/materials.md), including requirements, exact base/head/diff-base, all changes and explicit callers/configuration/protocols/check originals. Then prepare and call each leaf explicitly. The following is the full five-member invocation list; replace source/manifest digests and the backend reason with their actual values. Project registration does not collect or fetch source objects.

```bash
ergora --home ./review-home project add review-project --repo /path/to/repository
for instance in root/structure/review root/correctness/review root/test-value/review root/performance root/resource-lifecycle; do
  name=${instance//\//-}
  ergora --home ./review-home review prepare-input ./candidate-source \
    --source-kind local --source-sha256 PACKET_SHA256 \
    --manifest ./selected-review-manifest --manifest-digest MANIFEST_DIGEST \
    --instance "$instance" --max-prompt-bytes 1000000 --directory "./inputs/$name"
  ergora --home ./review-home composition check-input review-project "./inputs/$name" --mode task-mcp
  ergora --home ./review-home composition run-input review-project "./inputs/$name" \
    --mode task-mcp --backend codex --backend-reason 'Actual available backend selected for this independent review' --timeout 600
done
```

Use `--source-kind external --source-sha256 SOURCE_SHA256` for the complete external source directory. Check each receipt before continuing. Failed or unknown calls require reading/reconciling the original run; do not rerun this loop to fill missing results. `task-mcp` supplies fixed inherited Skill attachments; its SDK/backend availability and supported operations must pass real admission. A text-only result does not prove attachments were read. These readonly reviewers cannot execute checks, collect profiles, install dependencies, scan secrets or write remote reviews.

Record each returned run ID under its exact member path in `review-runs.json`, then read the originals and produce the complete report:

```bash
ergora --home ./review-home composition inspect-run review-project EXACT_RUN_ID --max-result-bytes 8388608
ergora --home ./review-home review report review-project ./candidate-source \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./selected-review-manifest --manifest-digest MANIFEST_DIGEST \
  --runs ./review-runs.json --format markdown > ./selected-review-report.md
```

This source entry invokes one leaf at a time; the report requires all five exact original runs, retains missing/failed/unknown evidence and minority opposition, and never executes the graph. In formal six-stage development, reference this selected review under the existing delivery root, then freeze the full development manifest and use the original `dag-v1` review stage. That owner schedules the five members under ancestor concurrency and the original total budget, accounts for five fixed review slots, and waits for all required terminal results. A source manifest alone does not create a formal task or candidate approval.

The coordinator reads every full response and separately records tool decision/coverage and compliance with the inherited current-stage/goal scope, necessary requirements/standards axes, deferred criteria with reasons, evidence gaps and follow-up contract. A schema-valid nonempty response or approve is not evidence that the necessary current-stage scope was covered. See [supervisor handoff](supervisor-handoff.example.md) for two batches accepted while earlier work remains pending. The handoff is a readable work list, not a new backend or dispatch API.
