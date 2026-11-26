# Revise and share exact workflow versions

English · [Documentation](../../README.md) · [简体中文](../../zh-CN/definitions/workflows/revisions.md)

## Revision, sharing and recovery

To change only the standard workflow document, use `show` to obtain the exact original version's `digest` and `definition`, save `definition` alone as `new-workflow.json`, and change its version, nodes or dependency references. Replace `BASE_DIGEST` with the original package digest:

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json
```

`--check` does not publish a version; omitting it publishes through the existing library. Both copy the complete original package; without resource arguments, only `workflow.json` is rewritten as UTF-8 with sorted keys, two-space indentation and a final newline. Responses include candidate identity, fixed `base` and `published`. Instructions, context, complete Skill trees, undeclared files and empty directories are retained. Change resources through resource revision below or export/edit/check/import. This entry accepts a complete JSON document or YAML with `--format yaml`; page operations follow below.

Unlike single-package `composition check`, `revise --check` resolves complete recursive dependencies using the current library and checks backend/role admission, inheritance, permissions, resources, ports and budgets. Dependencies must already be published with exactly matching digests. It uses no project grant and does not approve execution; preview the entire chain with an explicit grant after publication. Original-digest mismatch or current admission failure is refused; different content cannot be published at the same version, and the original remains unchanged. Checking reserves no version, so concurrent version conflicts may prevent publication; identical publication can be retried.

HTTP `POST /api/workflow-definitions/{id}/{version}/revisions/check` and `/api/workflow-definitions/{id}/{version}/revisions` check and publish respectively, with JSON `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}` (the original package's 64-character lowercase digest and complete new document). CLI and HTTP share candidate digests and existing validation; neither starts models, services or tasks.

### Measure a draft against its selected roots

Add `--impact ./selected-roots.json` to `composition revise --check` or `--preview-resources` before publishing a shared Workflow revision. Pass the same selection as `impact` on the Workflow HTTP check or resource-preview route. Supply up to 16 exact published root references and the grant for each. For example, use the root returned from the cross-end publisher or selected MoE publisher and the grant you intend to check.

```json
{
  "schema_version": 1,
  "roots": [{
    "ref": {"kind": "workflow", "id": "ergora-cross-end-template", "version": "1.0.0", "digest": "ROOT_DIGEST"},
    "grant": {
      "schema_version": 1,
      "permissions": {"read": ["workspace", "definitions"], "write": ["workspace"], "shell": true, "network": []},
      "limits": {"depth": 8, "instances": 128, "concurrency": 4, "material_bytes": 262144}
    }
  }]
}
```

The report binds the checked draft digest to the selected exact roots and grants. It compares each verified baseline with a projection that substitutes the draft at its old exact references. An unavailable input is `unverified`, and a root that does not contain the base is `unaffected`. The report covers the selected roots only. Review the dependency-first parent list for each pinned reference and affected site. Only the direct replacement has a new exact digest. Parent versions and digests come from their later explicit revisions, which can affect the final rendered provenance bytes.

Each leaf includes its inline resource bytes and rendered charges, with the separator charged to the resource that follows it. Each scope gives observed material bytes, the unchanged limit and remaining bytes. On failure the compiler stops at the original check. An incomplete scope gives a partial charge. A material failure includes the first over-limit scope and the attempted leaf. The CLI returns 1 for blocked or unverified analysis with the report still available as JSON.

When the baseline hits a material cap, the report still checks the draft under that same cap. Compare total charges only when both traversals complete. Affected paths retain verified substitution sites. Leaf coverage marks measured and attempted leaves, as well as known draft leaves the projection failed to reach. Missing paths are confirmed absent only after a complete traversal and otherwise remain unverified.

Use the normal accepted-candidate command to publish each desired version. The report creates no stored version, parent revision, canonical composition preview or manifest. A resource preview can still return the exact candidate token when the draft passes its own check and a selected parent projection fails. Publish a new root only after checking the proposed reference chain and its actual grant.

Resource operations follow the same contract as [Agent resource revision](../resources.md#revise-complete-resource-files). Prepare `resource-changes/changes.json`, `files/<包相对路径>` (package-relative path), and complete `new-workflow.json` (with valid placeholder digests for new declarations). Preview first, review and save the suggested response document as `new-workflow.json`, then explicitly accept, check and publish:

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --preview-resources > resource-preview.json
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json
ergora composition file kernel-delivery 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

Explicit operations derive binary attachments, complete Skill trees, executable bits and empty directories within the same package; unchanged content is retained. Take filenames from the original package's `show` response `files`; windows are returned as base64, and you must follow `next_offset` and combine every byte. HTTP uses `POST /api/workflow-definitions/{id}/{version}/revisions/preview-resources` and `/files/read`; requests and final `resource_changes/accepted_candidate` fields match Agents. Preview, checking and publication all perform complete recursive admission; historical file reads do not require a currently available backend. Complete candidate acceptance binds ordinary attachments and every directory; changing documents or operations requires a new preview. Preview neither elevates permissions nor approves execution. The page's “Resource and attachment editing” can read/upload complete files, stage operations and explicitly accept resource digests; use the CLI or full export/edit for larger changes. See [revise workflow resources on the page](#revise-workflow-resources-on-the-page).

Parents/children can jointly plan permission increases or additional resources: create new child-definition versions, update parent references/permissions level by level, publish a new root, then check the whole chain with the new project grant. Changing children alone fails, as does a root still exceeding project ceilings. Single-definition import publishes a complete object and index atomically; exact recursive references fix the complete root revision. This provides neither a cross-definition transaction nor project adoption. Old roots and versions retain their original content rather than substituting new active heads.

Joint revision is not a cross-library atomic transaction. Interruption or parent-check failure leaves earlier independent child versions visible; old roots, frozen manifests, task inputs and approvals keep their exact references. After repair, continue from the unfinished parent instead of automatically substituting the “latest version”.

### Publish resource revisions through the complete dependency chain

For the governance composition's structure reviewer, publication order is Agent `ergora-structure-reviewer` → `ergora-structure-review` → `ergora-delivery-review` → `ergora-governance-delivery` → root `ergora-governance-template@1.1.8`. Large changes use the same inner definitions through `ergora-large-change-delivery` → root `ergora-large-change-template@1.1.10`; the training proposal's measurement chain is Agent `ergora-measurement-reviewer` → `ergora-measurement-review` → `ergora-training-proposal`. At every level, update the parent reference with the exact version and digest from the dependency's publication receipt.

1. Save a complete manifest and required leaf inputs from the old root, retaining the original version as a comparison. Preserve existing `resources` when adding materials at each level; Skills must include their entry point, all referenced files and necessary empty directories. Ordinary undeclared attachments may also remain in the package.
2. Starting with the Agent, raise each changed package's version and follow resource preview, explicit acceptance, checking and publication above. In the parent, set `nodes[].ref` to the newly published child's complete `kind/id/version/digest`, then publish the parent, root last. Checks refuse unpublished new dependencies or mismatched digests; do not invent predicted digests or edit old indexes.
3. Fully `export` each package; import frozen dependencies into the receiving library before their parents. Copying a root package alone does not provide a complete composition. For one-step sharing, run `prepare-manifest` with the new root and share the entire directory.
4. Preview the new root with an explicit grant. Check the target leaf's complete ancestor provenance, original/additional materials, permission chain and budgets, then prepare new input from the new manifest. Old frozen input still points to old materials; publishing a new root does not update it.

Resource revision does not automatically adopt definitions for projects, elevate permissions or execute anything. Training templates retain their proposal/material-review entry points; real training and adoption must pass their own experiment gates.

### Regenerate bundled optimization proposals

In a source checkout, edit the shared graph or the direction's declared expert, role, instruction digest and version in the [proposal generator](../../../scripts/generate-optimization-proposals.py). The 18 common graphs and the low-precision graph use the same builder. Low precision adds its kernel assessment before measurement. Each proposal retains its own `instructions.md`.

Run `python scripts/generate-optimization-proposals.py` to check the catalog, instruction digests and exact `workflow.json` bytes. For an intentional revision, set a higher version for each affected proposal and use `python scripts/generate-optimization-proposals.py --write`. Inspect the generated diff and use the [original dependency-chain procedure](#publish-resource-revisions-through-the-complete-dependency-chain) for publication and downstream pins.

### Jointly revise parent and child permissions

Permission declarations belong to Workflows and their Agent nodes. The governance composition's structure-review leaf requires checking four levels: `root` → `root/review` → `root/review/structure` → `root/review/structure/review`. Large changes use the same review chain, while training proposals' measurement chain has one fewer level. Raising only the innermost Agent-node request is still refused by its owning Workflow; merely publishing a child workflow and replacing the parent reference still leaves the parent refusing an out-of-bounds child.

|Operation order|Explicit changes required in the new revision|
|---|---|
|Innermost Workflow|Raise the selected Agent node's request and this Workflow's ceilings, check, then publish a new version.|
|Each parent Workflow|Reference the newly published child's exact version/digest and raise this parent's ceilings; check and publish, root last.|
|New-root preview|Supply an explicit grant covering the new root; the old grant still refuses it. Check unselected branches, all ancestor materials, budgets and ports.|
|Actual invocation|Prepare input from the new manifest, then use `check-input` for the selected mode/backend; static declarations add no backend capabilities.|

For example, the reserved domain `https://joint-revision.example.invalid` can check complete containment of `network` sets; this validates declarations only, so do not request the domain. Current public `text-only` and `task-mcp` calls support no tool network requests. Even when the new root/grant pass static checks, these modes' `check-input` and `run-input` still refuse before registering a run or calling a model. Other execution capabilities require a specifically supported execution entry point and project authorization.

### Repeated instances, responsibilities and backend selection

To reuse a subtemplate, in the parent's `nodes`, reference the same complete ref with different `id` values, connecting every branch requiring a join to explicit `all`. For example, `structure` and `structure-extra` can reference the same structure-review version, producing leaves at `root/review/structure/review` and `root/review/structure-extra/review`. Frozen assets save one copy of the same definition; each reference still counts instances, complete-material bytes and scope budgets separately, with its own structural provenance paths.

Two instances of the same exact subtemplate have identical internal responsibility declarations. To make one advisory, publish a new subtemplate version with its Agent node's `review_requirement` changed to `advisory`, then reference it from the parent; Workflow-reference nodes have no responsibility-override field. Independent Agent definitions and per-leaf call backend overrides own backend selection; responsibility changes cannot switch models. Run `check-input --backend codex` or `--backend claude-code` for each leaf to check current configuration/mode admission. This checks neither authentication, actual reasoning nor independence of model errors.

The library lives in State's `workflow-definitions/index.json` and `objects/<digest>/`, separate from the Agent library but sharing `definition_bundles` code. Existing `ERGORA_HOME`, `--home` and platform defaults still apply, with no new DB table. `export` exports only the current package; complete composition sharing also requires sharing/importing each referenced package in dependency order. A single root is not a self-contained distribution.

The original [complete offline backup](../../install/upgrades.md#upgrades-and-persistent-data) saves both libraries. Verification checks indexes and objects plus recursive workflow references, resources, graphs and static contracts; recovery still requires the original platform, original State path and stopped writers. Library corruption is not automatically overwritten as new evidence. Explicit task definition v2 can [freeze a complete review composition](../../development/preparation.md#freeze-a-review-composition-for-a-formal-task), running read-only reviewers or nested serial/parallel review through the original six stages with required/advisory responsibilities. Old v2/v3 review requires every leaf to map directly to the root task through its structural ancestors without predecessor dependencies. Explicit dag-v1 v4 uses [named ports](contracts.md#data-ports-for-formal-read-only-review); v5 with work-units-v1 and v6 with work-units-v2 use [specialist writer assignments](contracts.md#specialist-writers-and-original-work-units). Original owners retain formal approval and candidate evidence. A listed runtime_supported value describes static shape support only, without proving backend/service availability.

Historical `show/list/export` and backup/recovery do not require referenced backends to remain in the current catalog; they still check complete static structure and content. New `import` (including repeated import of identical content) and `preview` additionally check every Agent definition's current role/backend contract rather than skipping admission because a version was imported previously. Single-package `check` still checks local graphs/resources without accessing dependency libraries. See the [Agent guide](../agents.md#historical-assets-and-current-admission) for historical readability versus current availability.

## Revise workflows on the page

Select an exact workflow version in “Agent and composition library”. The field form supports a new version, description, root inputs/outputs, permissions and budgets; “Edit instance” selects an Agent, subworkflow or all-join to change exact references, roles, review responsibilities, predecessor dependencies, input bindings and instance permissions. Modify an Agent's backend request in its independent definition, then update this reference to the published new version/digest. Old v1 is not automatically upgraded to v2; complex documents can still be explicitly edited in JSON/YAML.

After adding an instance, select it and complete its actual ports, dependencies and permissions. Renaming synchronizes dependencies/named bindings; deletion requires fixing remaining port references. Intermediate documents may temporarily violate execution contracts, with the raw-document entry still available for repairs. The original library's “Check definition candidate” and publication checks determine complete-graph validity, ancestor permissions, resource conflicts and budgets.

Use “Apply field text” or apply JSON/YAML → “Check definition candidate” → “Publish new definition version”. The three editor buffers, raw-text synchronization confirmation, bounded history, recovery and download rules match the [Agent editor](../agents.md#edit-a-specialist-agent-in-the-console). The page provides no cross-library transaction: publish Agents/subworkflows first, then update/publish parents and finally the new root. A failed parent does not undo published child versions, change old roots or alter in-flight tasks.

For a new template, choose “New template” in the library and select an exact starter graph. The bundled six-stage development graph is preselected. Choose another bundled graph or any exact saved Workflow when its structure fits your task. Enter a destination ID and version to open an independent draft. Selecting the same source and destination can continue that draft. To save an already edited graph under a different template ID, choose “Set save-as target”. Check the candidate and choose “Save as template” to publish. Open the exact saved version to preview or freeze a complete manifest. The CLI uses `composition revise` with the destination `id` and `version` in the draft and the original ID, version and digest as the base. Graph saving uses the definition library. Formal task creation separately checks the selected execution route.

Add the exact published subworkflow for each reusable step your graph needs. For example, a source-analysis graph can add `ergora-development-inventory` as a predecessor and retain its own analysis and join. An execution route checks the resulting graph. Candidate integration, trusted checks and approval still have their own formal execution contracts.

The library page holds no project grant; saving root permissions is not approval. After publication, preview and freeze tasks with an explicit grant. See the [workflow guide](#view-published-nested-relationships) for formal-task handoff implementation scope.

### View published nested relationships

Select an exact workflow version, confirm “Static preview ceilings JSON” and click “Preview complete composition”. Nested boxes represent structural parents/children, dashed arrows predecessor dependencies, and blue solid lines/named input-output ports data bindings. Data edges neither pass Skills nor grant permissions; the graph does not indicate that Agents have run. Repeated references to a subtemplate still appear at distinct full instance paths.

Click a graph instance or a keyboard-accessible button in the instance table to inspect complete permissions, budget/usage, ports, responsibilities and backend requests. Agent details include every ancestor resource and complete prompt body; expertise comes only from that exact Agent version. Click “Open selected exact definition” to modify its independent definition; edit instance permissions, dependencies and bindings through “Open structural parent definition”, which also owns join edits. Navigation preserves original editor buffers without automatically publishing or adopting newer versions.

The graph always comes from the labeled **published version and preview digest**; it excludes unpublished document/resource drafts. Dragging, zooming, “Locate selected instance” and “Rearrange composition graph” change display only. The tab retains layout by control directory and exact root version, and refresh rearranges it. Changing the grant clears the old graph and requires explicit preview again. If the graph component fails to load, the instance table and complete details remain available; “Dependency and named data relationships” provides a text table. Download complete data as `composition-preview.json`.

Click “Collapse FULL_PATH” in the instance table, or select a subworkflow and “Collapse selected subworkflow”. Each instance collapses independently; other instances of the same ref are unaffected, and the root stays expanded. Collapse/expand rearranges the view using the original hierarchy, hiding internal nodes/edges while retaining complete instance/relationship tables. Cross-group edges are labeled “Summary”, retaining original types/named bindings; click an edge or relationship-table ID to inspect complete original endpoints. A collapsed box introduces no execution or inheritance relationship. “Expand all subworkflows” clears all collapsed states.

“Find instances (path, responsibility, expertise, backend)” matches literal case-insensitive terms, requiring every term to match. For example, `reviewer codex` finds reviewer instances using Codex. Expertise/declared roles come only from Agent-index entries matching complete ID/version/digest; missing metadata is reported without selecting latest. Search highlights matches while retaining unmatched structure/relationships; matches inside collapsed groups are marked on their boxes. “Expand ancestors and locate”, previous/next match buttons and “Locate selected instance” expand structural ancestors and locate the original instance; selecting a hidden leaf in the instance table opens complete details without expanding it. Query, collapsed state, selection and layout live only in this page session, isolated by control directory/complete root ref and reset on refresh.

### Compare two published compositions

1. Under “Exact subworkflow version”, select the original root version. Draft edits do not participate in comparison.
2. Under “Preview entire nested composition”, check “Static preview ceilings JSON”, then select “Comparison target (published exact version)”. The target can be another workflow in the library; the list explicitly shows ID, version and digest without using latest.
3. Click “Compare two published versions”. Each exact version passes through the original preview entry using the same explicit grant. Either version exceeding permissions, missing references or failing compatibility displays the original refusal, without widening permissions or generating a partially successful diff. If greater permissions are needed, inspect and explicitly change the shared ceilings before retrying.
4. Under “Exact comparison of two published compositions”, inspect counts and per-path results for added, removed, changed and identical instances. Click a full path to compare permissions, responsibilities, backends, budgets, dependencies, named ports and other facts field by field, and expand both complete original instances to read all resources, provenance and assembled prompts; table buttons also support keyboard use.
5. Download before/after preview JSON separately to retain complete originals. Comparison neither publishes definitions, applies drafts nor changes the editing baseline. Switching roots or control directories clears the current comparison. Changing the target or grant requires another explicit comparison; late responses cannot restore previous results.

Object-key order creates no differences; arrays retain order, without inferring equivalence from reordered permission/dependency declarations. Comparison pairs by full instance path and retains every repeated instance of an exact Agent/workflow. Renaming appears as deletion of an old path/addition of a new one, without guessing renames. Resource content identity/order, provenance/declarations and assembled-prompt identity are displayed separately. A source-definition version change alone can alter prompt digest/byte usage without establishing changed Skill bodies. Digests reflect only compiled facts in the original preview; open exact definitions to verify non-preview fields such as Agent descriptions/expertise. See [task-page selection](compose.md#select-a-composition-on-the-formal-task-page) for formal execution handoff and its supported handoff contract.

## Revise workflow resources on the page

Select an exact subworkflow version in “Agent and composition library” and use “Resource and attachment editing”. Complete reads/binary uploads, explicit write/delete/mkdir, diff previews and digest acceptance share the [Agent resource steps](../resources.md#edit-resources-and-attachments-in-the-console) session contract. Apply the document with a higher version and resource declarations first, then stage file operations, preview/accept, check and explicitly publish. Continue later additions from the complete accepted operation set; original packages and old manifests remain unchanged.

Document, operations and acceptance identity undo/redo together; unapplied drafts remain separate. Unapplied content or stale digest acceptance prevents publishing an old snapshot. Recheck after refreshing; damaged/quota-exceeding buffers can download complete working bytes, excluding unedited original packages. HTTP's total limit including base64 is 4,000,000 bytes; use CLI `composition revise --resources` for larger changes. This creates no separate server draft store or automatic upload session. The current page revises only the selected definition; joint parent/child permission increases and new-root references still require explicit new versions. Adding Skills/context expands no execution permissions.

Continue: [Revise and read complete definition resources](../resources.md) · [Compose and freeze a workflow](compose.md).
