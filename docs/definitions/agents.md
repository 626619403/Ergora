# Create and revise specialist Agent definitions

English · [Documentation](../README.md) · [简体中文](../zh-CN/definitions/agents.md)

An Agent definition bundle stores one specialist's roles, specialties, backend, initial instructions, context and Skill resources. One backend can have several complementary definitions; one definition can later serve multiple templates. The current entry points provide static checking, import, inspection and sharing. Importing a bundle does not run its commands or scripts.

Project-role calls use [role bindings](../agents/backends.md#project-selection-and-standalone-calls). [Workflow definitions](workflows/compose.md) can reference Agent definitions, preview the complete ancestor chain and explicitly invoke a pinned leaf through `composition run-input`. Formal six-stage tasks can [freeze a review composition](../development/preparation.md#freeze-a-review-composition-for-a-formal-task), running one reviewer or several nested read-only reviewers in sequence or parallel with an explicit all-join. [work-units-v2](workflows/contracts.md#specialist-writers-and-original-work-units) can also assign complementary implementation specialists to the original work units, followed by overall review. The original v1 protocol and sealed tasks retain their contracts. See the [workflow guide](workflows/permissions.md#complete-inheritance-and-conflicts) for other role topologies.

## Current availability and runtime limits

Definition import, static graph preview and a saved manifest do not establish backend installation, authentication, model capability or permission to execute. Skills and context accumulate through the complete structural ancestor chain, while each child’s permissions must stay within its parent and project grant. A new definition or binding does not rewrite a task’s frozen backend, resources or contract; recover an existing task using its original identity.

Bundled specialists explicitly select Codex `gpt-6.2-sol`: planning, contract design and kernel candidate design use `max`. A reusable development Agent declaring planner uses the same Agent-level `max` minimum in its inspector and implementer roles. Long implementation definitions without a planner role use at least `xhigh`; review and pure documentation definitions use at least `high`. The optional `invocation_minimum` fixes the model and minimum `reasoning_effort`. A higher effort on that model is allowed; a lower or absent effort, absent model, or another uncomparable backend/model fails invocation and formal-task validation. An explicitly scoped short implementation definition can declare `medium`; there is no separate bundled short-change template. General custom definitions can omit a minimum. Requests and actual native behavior remain separate evidence; planner/automatic selection is unimplemented.

Restricted composition calls ignore ambient user configuration. For a custom provider, supply the original inference configuration through `--codex-config ./inference.toml`, retaining environment credential references. Templates store no provider or private path. The explicit model/effort overrides those settings while retaining provider configuration. Omitting `--backend` inherits the template binding; selecting the same backend retains its unspecified fields.

Formal execution keeps the original six stages and the [supported review/work-unit contracts](workflows/contracts.md); a static graph does not make arbitrary role topologies or generalized Repeat executable. Current [design-policy registration](../projects/registration.md#current-limits-of-design-policy-registration) remains storage-only with execution unsupported. Inspection-only [source-journal records](../development/design-and-approval.md#store-complete-design-sources-and-reported-answers) do not grant execution; finite training controllers require [explicit authorization](../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization). These boundaries do not expand when importing a definition or selecting a backend.

## Built-in specialists

`ergora composition install-preset large-change` imports the domain's separate specialists and complete child workflows together. See [built-in domain compositions](workflows/compose.md#use-bundled-domain-compositions) for governance, development and training entry points. These definitions ship in the wheel; initial instructions and Skills describe their specialties. Different instances can still select different backends, and templates compose them through exact references. To change a default specialist, first export it, update the content and version, then publish a new root along the parent references. Existing versions are not overwritten. Import does not prove specialist effectiveness or backend inference availability.

The web console's “Agent 与组合库” (Agent and composition library) can import these compositions before a project is registered, select an exact Agent version, and show its canonical document, complete own resources and bundle-file identities. See the [page instructions](workflows/compose.md#browse-and-preview-definitions-in-the-page). The default backend is a request; successful import does not establish authentication. Downloading definition JSON saves only the `agent.json` document. Use `export` below for a complete portable bundle with Skill attachments. When a child workflow references the Agent, select and preview that workflow to inspect all ancestor resources and the assembled instructions for the instance.

## Use the existing examples

After installing Ergora, run these commands from the repository root without registering a project or starting services:

```bash
ergora agent definition check examples/agents/kernel-implementer
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/architecture-reviewer
ergora agent definition list --role reviewer
ergora agent definition list --specialty cuda
ergora agent definition show architecture-reviewer 1.0.0 --material
ergora agent definition export architecture-reviewer 1.0.0 ./shared-architecture-reviewer
```

`check` does not create or migrate State; add `--material` to inspect the complete required reading. `import` copies the bundle into persistent State, so the source directory can later be removed. `show` revalidates content on every read. `export` writes only to a new directory; the result can be imported in another environment that preserves the original file bytes and executable-bit semantics. Examples live in the repository's [examples/agents](../../examples/agents) directory, rather than separately installed system Skills. Wheel-only users can obtain example bundles from that directory.

The [kernel implementer](../../examples/agents/kernel-implementer/agent.json) focuses on CUDA/Triton and measurement; the [architecture reviewer](../../examples/agents/architecture-reviewer/agent.json) focuses on responsibilities and dependencies. Both currently default to Codex to demonstrate different specialists on the same backend. Formal review admission prefers a backend different from the implementer's by default; a same-backend fallback requires a recorded reason, and strict diversity can also be required. The example prompts and Skills are starting points without a model-effectiveness evaluation.

## Create and modify definitions

A bundle must contain `agent.json`, using [schema v1](../../src/ergora/data/schemas/agent-definition-v1.json). Only JSON is currently accepted. Use UTF-8; a BOM is accepted. Definition fields are:

|Field|Purpose and constraints|
|---|---|
|`schema_version`|Strict integer `1`; unknown versions are rejected.|
|`id` / `version`|Lowercase kebab ID and `MAJOR.MINOR.PATCH` version. Reads require an exact version; there is no implicit latest.|
|`description`|Describes the specialist's purpose.|
|`roles`|Existing roles the specialist can fill; each reuses backend capability validation.|
|`specialties`|Specialty tags for `list --specialty`; they neither grant permissions nor prove model capability.|
|`backend`|An existing tool binding, reusing component configuration. It does not probe availability, install or authenticate a backend.|
|`invocation_minimum`|Optional model/effort floor, such as `{"model":"gpt-6.2-sol","reasoning_effort":"high"}`. Both the default backend and actual overrides must satisfy it.|
|`resources`|An ordered resource list with unique logical IDs and exactly one `instructions` resource.|

Every `resources` entry has `id`, `kind` and `path`. `instructions` and `context` point to nonempty text files and require `sha256`. A `skill` points to a complete directory with a valid `SKILL.md` and requires `digest`; its directory name must match the frontmatter name. The digest includes every Skill file. Material inspection returns the complete `SKILL.md` instructions; scripts and other on-demand resources remain files.

AgentDefinition v1 stores no permission fields. The containing Workflow node and every structural ancestor constrain the same specialist's permissions in each composition instance. Adding specialist material does not change those permissions. To bring new specialist resources into an existing composition, [publish along the complete dependency chain](workflows/revisions.md#publish-resource-revisions-through-the-complete-dependency-chain), then pin the new root and input. See [task MCP](workflows/leaf-calls.md#verify-complete-attachment-reads) for actual attachment reads.

Multiple instances at different paths can reference the same Agent definition. The path distinguishes invocation identity; the complete ref pins their shared specialty, instructions and default backend. Each instance can explicitly override its backend at supported invocation entry points. Review responsibility belongs to the Workflow Agent node that references it. If a nested template needs a different responsibility, publish the corresponding child-template revision first; the parent Workflow reference cannot carry an override field. See [repeated instances, responsibilities and backend selection](workflows/revisions.md#repeated-instances-responsibilities-and-backend-selection).

After editing an example, refresh resource digests and run `check`. This Python example refreshes local digests; replace `my-agent` with your directory:

```python
import hashlib
import json
from pathlib import Path
from ergora.storage.assets import digest_tree

root = Path("my-agent")
definition = json.loads((root / "agent.json").read_text(encoding="utf-8-sig"))
for resource in definition["resources"]:
    path = root / resource["path"]
    if resource["kind"] == "skill":
        resource["digest"] = digest_tree(path)[0]
    else:
        resource["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
(root / "agent.json").write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
```

One `id/version` can identify only one content set. Importing an identical bundle is idempotent; changes to a registered version are rejected, so increment the version before importing. Changes to backend binding fields such as the model, JSON formatting, newlines and script executable bits all change the bundle digest. The digest covers every ordinary file, including undeclared attachments. Empty directories and modification times do not participate in identity.

POSIX and Windows have different executable-bit semantics. Copying a Skill with executable resources across systems can cause a digest mismatch and explicit rejection; portable paths do not guarantee preserved executable bits. For portability, explicitly create and verify a new version and digest suitable for the target system. Executable bits are not silently dropped, and registered identities are not rewritten. State backups still support restoration only on the original platform.

## Derive a new version from a pinned original bundle

When changing only the canonical document, retain every original bundle file and submit a complete new `agent.json` directly. First use `show` to obtain the original version's `digest` and `definition`. Save `definition` separately as `new-agent.json`, then edit the version and any roles, specialties or backend fields. Replace `BASE_DIGEST` below with the original bundle digest:

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --check
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json
```

`--check` checks the candidate without registering a version; omitting it publishes the version. The response contains the candidate `digest`, canonical document, file/resource identities, pinned `base` and `published`, without a temporary directory. Without resource arguments, only `agent.json` is rewritten using UTF-8, sorted keys, two-space indentation and a final newline. Original instructions, context, Skill attachments, undeclared files and empty directories are copied completely. Resource declarations must still match the actual files. To change file contents, use [resource revision](resources.md#revise-complete-resource-files) or export/edit/check/import. The canonical document can be supplied as JSON or read as YAML with `--format yaml`; the library still stores canonical JSON.

A mismatched original digest is rejected; the new document still undergoes current role/backend contract checks. Different contents cannot be published under the same ID/version; an identical request can be retried. The original version is always retained. `check` does not reserve a version, so concurrent publication can still cause a subsequent version conflict. Derivation does not run or authenticate a backend or modify workflows and tasks referencing the original version. See [workflow revisions](workflows/revisions.md#revision-sharing-and-recovery) for updating references.

Local HTTP entry points use the same owner as the CLI: `POST /api/agent-definitions/{id}/{version}/revisions/check` checks only; `POST /api/agent-definitions/{id}/{version}/revisions` publishes. The JSON request is `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`, with the original 64-character lowercase digest and the complete new document. Both retain the complete original bundle without creating tasks, approvals or execution sessions.

## Edit a specialist Agent in the console

Run `ergora serve`, open “Agent 与组合库” (Agent and composition library), and import a built-in composition or select an exact version of an existing Agent. In “字段编辑” (field editing), increment the version, edit its description, roles, specialties and backend request, then click “应用字段文本” (apply field text). The basic backend request selector fills configuration only. Models and options must still meet the selected tool's contract; a successful selection does not establish installation or authentication.

You can also select a complete Agent instance path from the [published nested graph](workflows/revisions.md#view-published-nested-relationships), then choose “打开所选精确定义” (open the selected exact definition). This pins the original ID/version/digest. Instances referencing the same Agent open the same immutable definition. Instance permissions and input bindings belong to the structural parent workflow; edit them through “打开结构父定义” (open the structural parent definition). The graph matches specialties against the exact Agent index, without substituting the latest version.

Search the graph by responsibility, specialty, backend or complete path, for example `reviewer codex`. Search retains unmatched structure. A result button can expand structural ancestors and locate the instance. The complete instance table also lets you directly select leaves inside collapsed structures and inspect every inherited material. A missing specialty index is shown explicitly; unknown capability cannot be treated as present. Collapse/search changes only the page display, without changing Agent authority or the selected backend.

The workflow page can also [compare two published compositions](workflows/revisions.md#compare-two-published-compositions), checking each instance's exact Agent reference, backend, role, permissions and complete inherited materials. Resource content and source versions are shown separately; changing a version alone does not establish changed Skill content. Comparison does not modify an independent Agent definition or editing buffer. Fields absent from preview, such as description and specialties, still require opening the exact definition.

You can also edit “定义 JSON 原文” (definition JSON source) or “定义 YAML 原文” (definition YAML source). Explicitly apply the source before “检查定义候选” (check definition candidate); only a successful check enables “发布新定义版本” (publish a new definition version). Unapplied fields, JSON and YAML are retained separately. Apply or discard each first; another representation cannot overwrite unresolved source text. Formatting changes alone do not regenerate the other format. If a semantic change requires replacing other custom source text, the console first prompts you to download it and explicitly confirm synchronization. Complex JSON within fields also rejects duplicate keys.

After success, keep the exact publication receipt. “以已发布版本继续编辑” (continue editing from the published version) selects a new base while retaining the original session. If a response is lost, do not change the base or document and present it as the original request. Explicitly retry with the same base and document to reconcile it. Checks do not reserve versions; publication can still encounter a version conflict, which never overwrites an existing version.

Browser buffers are isolated by control directory, kind, original ID/version/digest and tab. After a refresh, select the original version again to restore the buffer. A buffer is not a persistent definition. Recovery uses the shared converter to verify applied JSON/YAML semantics while retaining invalid unapplied text. A damaged buffer can be downloaded raw, retried for verification or explicitly cleared. Storage-quota exhaustion is shown with an option to download the current editing buffer. Before closing the tab or changing machines, publish or separately save a download. Browser history retains at most 50 entries and evicts older snapshots toward a 4 MiB budget, including complete resource-operation bytes. The newest snapshot is retained even when it alone exceeds that budget; history starts again after refresh.

YAML uses the JSON data model: object keys must be strings; duplicate keys, aliases, cycles and custom tags are rejected. Quote ambiguous strings such as dates. Conversion allows at most 64 levels and 100,000 values, including mapping keys; the total HTTP request limit is 4 MB. JSON/YAML are editing representations and do not execute their content. Publication still stores canonical JSON in a complete resource bundle. See [console resource editing](resources.md#edit-resources-and-attachments-in-the-console) for file operations. Larger changes can still use [CLI resource revision](resources.md#revise-complete-resource-files) or export/edit/check/import. Downloading a single document excludes attachments; export the complete bundle to share a definition.

## Historical assets and current admission

For stored bundles, `show/list/export` checks versioned structure and complete content; backup/recovery also checks recursive workflow references. Both are independent of currently selectable roles/backends. If an upgrade removes a tool or tightens configuration rules, complete old materials can still be read and exported. Missing files, tampering and identity drift still fail; historical content is never rewritten automatically.

`list --role` can filter historical role tags even after a role leaves the current runtime catalog. `check/import` also enforces the current role and backend contracts, including renewed admission when importing an identical bundle. Workflow `preview` uses current admission for referenced Agents. A successful historical read therefore does not establish current backend availability or execution authority; an exported old bundle may also fail reimport under current rules. To use an alternative tool, publish an explicit new Agent version and a new workflow version referencing it. Existing versions are not modified.


After static workflow preview, the console can explicitly save the current root and every Agent/Skill attachment as a complete manifest, or `composition freeze-manifest` can bind the original preview digest. Formal admission for different backends and writer trust are still checked at task handoff. See [persistent complete bundles](workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory).

The formal task page can [select a backend for each composition instance](workflows/compose.md#select-a-composition-on-the-formal-task-page), without changing this Agent's default request or other instances referencing it. Reviewers follow the exact definition by default. Writable implementers require an explicit backend/execution-boundary override and a reason. Backend forms share the component schema with project bindings. A selection does not establish authentication or support for that execution mode; formal task preview rechecks the original contract.

Continue: [Revise and read complete definition resources](resources.md) · [Compose and freeze a workflow](workflows/compose.md).
