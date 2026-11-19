<a id="专长-agent-定义库"></a>
# Specialist Agent definition library

English · [简体中文](zh-CN/AGENT_DEFINITIONS.md)

An Agent definition bundle stores one specialist's roles, specialties, backend, initial instructions, context and Skill resources. One backend can have several complementary definitions; one definition can later serve multiple templates. The current entry points provide static checking, import, inspection and sharing. Importing a bundle does not run its commands or scripts.

Project-role calls use [role bindings](AGENT_BACKENDS.md#项目选择与独立调用). [Workflow definitions](WORKFLOW_DEFINITIONS.md) can reference Agent definitions, preview the complete ancestor chain and explicitly invoke a pinned leaf through `composition run-input`. Formal six-stage tasks can [freeze a review composition](USAGE.md#为正式任务冻结审查组合), running one reviewer or several nested read-only reviewers in sequence or parallel with an explicit all-join. [work-units-v2](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元) can also assign complementary implementation specialists to the original work units, followed by overall review. The original v1 protocol and sealed tasks retain their contracts. See the [implementation plan](plans/2026-11-08-agent-composition.md) for other role topologies.

## Current availability and runtime limits

Definition import, static graph preview and a saved manifest do not establish backend installation, authentication, model capability or permission to execute. Skills and context accumulate through the complete structural ancestor chain, while each child’s permissions must stay within its parent and project grant. A new definition or binding does not rewrite a task’s frozen backend, resources or contract; recover an existing task using its original identity.

Bundled specialists explicitly select Codex `gpt-6.1-sol`: planning, contract design and kernel candidate design use `max`. A reusable development Agent declaring planner uses the same Agent-level `max` minimum in its inspector and implementer roles. Long implementation definitions without a planner role use at least `xhigh`; review and pure documentation definitions use at least `high`. The optional `invocation_minimum` fixes the model and minimum `reasoning_effort`. A higher effort on that model is allowed; a lower or absent effort, absent model, or another uncomparable backend/model fails invocation and formal-task validation. An explicitly scoped short implementation definition can declare `medium`; there is no separate bundled short-change template. General custom definitions can omit a minimum. Requests and actual native behavior remain separate evidence; planner/automatic selection is unimplemented.

Restricted composition calls ignore ambient user configuration. For a custom provider, supply the original inference configuration through `--codex-config ./inference.toml`, retaining environment credential references. Templates store no provider or private path. The explicit model/effort overrides those settings while retaining provider configuration. Omitting `--backend` inherits the template binding; selecting the same backend retains its unspecified fields.

Formal execution keeps the original six stages and the supported review/work-unit contracts described above; a static graph does not make arbitrary role topologies or generalized Repeat executable. Current [design-policy registration](PROJECTS.md#current-limits-of-design-policy-registration) remains storage-only with execution unsupported. The isolated source-journal first draft is unreleased, and schema3 training effects remain disabled. These boundaries do not expand when importing a definition or selecting a backend.

<a id="内置专家"></a>
## Built-in specialists

`ergora composition install-preset large-change` imports the domain's separate specialists and complete child workflows together. See [built-in domain compositions](WORKFLOW_DEFINITIONS.md#使用内置领域组合) for governance, development and training entry points. These definitions ship in the wheel; initial instructions and Skills describe their specialties. Different instances can still select different backends, and templates compose them through exact references. To change a default specialist, first export it, update the content and version, then publish a new root along the parent references. Existing versions are not overwritten. Import does not prove specialist effectiveness or backend inference availability.

The web console's “Agent 与组合库” (Agent and composition library) can import these compositions before a project is registered, select an exact Agent version, and show its canonical document, complete own resources and bundle-file identities. See the [page instructions](USAGE.md#在页面浏览与预览定义). The default backend is a request; successful import does not establish authentication. Downloading definition JSON saves only the `agent.json` document. Use `export` below for a complete portable bundle with Skill attachments. When a child workflow references the Agent, select and preview that workflow to inspect all ancestor resources and the assembled instructions for the instance.

<a id="使用已有示例"></a>
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

`check` does not create or migrate State; add `--material` to inspect the complete required reading. `import` copies the bundle into persistent State, so the source directory can later be removed. `show` revalidates content on every read. `export` writes only to a new directory; the result can be imported in another environment that preserves the original file bytes and executable-bit semantics. Examples live in the repository's [examples/agents](../examples/agents/) directory, rather than separately installed system Skills. Wheel-only users can obtain example bundles from that directory.

The [kernel implementer](../examples/agents/kernel-implementer/agent.json) focuses on CUDA/Triton and measurement; the [architecture reviewer](../examples/agents/architecture-reviewer/agent.json) focuses on responsibilities and dependencies. Both currently default to Codex to demonstrate different specialists on the same backend. Formal review admission prefers a backend different from the implementer's by default; a same-backend fallback requires a recorded reason, and strict diversity can also be required. The example prompts and Skills are starting points without a model-effectiveness evaluation.

<a id="创建与修改定义"></a>
## Create and modify definitions

A bundle must contain `agent.json`, using [schema v1](../src/ergora/data/schemas/agent-definition-v1.json). Only JSON is currently accepted. Use UTF-8; a BOM is accepted. Definition fields are:

|Field|Purpose and constraints|
|---|---|
|`schema_version`|Strict integer `1`; unknown versions are rejected.|
|`id` / `version`|Lowercase kebab ID and `MAJOR.MINOR.PATCH` version. Reads require an exact version; there is no implicit latest.|
|`description`|Describes the specialist's purpose.|
|`roles`|Existing roles the specialist can fill; each reuses backend capability validation.|
|`specialties`|Specialty tags for `list --specialty`; they neither grant permissions nor prove model capability.|
|`backend`|An existing tool binding, reusing component configuration. It does not probe availability, install or authenticate a backend.|
|`invocation_minimum`|Optional model/effort floor, such as `{"model":"gpt-6.1-sol","reasoning_effort":"high"}`. Both the default backend and actual overrides must satisfy it.|
|`resources`|An ordered resource list with unique logical IDs and exactly one `instructions` resource.|

Every `resources` entry has `id`, `kind` and `path`. `instructions` and `context` point to nonempty text files and require `sha256`. A `skill` points to a complete directory with a valid `SKILL.md` and requires `digest`; its directory name must match the frontmatter name. The digest includes every Skill file. Material inspection returns the complete `SKILL.md` instructions; scripts and other on-demand resources remain files.

AgentDefinition v1 stores no permission fields. The containing Workflow node and every structural ancestor constrain the same specialist's permissions in each composition instance. Adding specialist material does not change those permissions. To bring new specialist resources into an existing composition, [publish along the complete dependency chain](WORKFLOW_DEFINITIONS.md#沿完整依赖链发布资源修订), then pin the new root and input. See [task MCP](WORKFLOW_DEFINITIONS.md#核验完整附件读取) for actual attachment reads.

Multiple instances at different paths can reference the same Agent definition. The path distinguishes invocation identity; the complete ref pins their shared specialty, instructions and default backend. Each instance can explicitly override its backend at supported invocation entry points. Review responsibility belongs to the Workflow Agent node that references it. If a nested template needs a different responsibility, publish the corresponding child-template revision first; the parent Workflow reference cannot carry an override field. See [repeated instances, responsibilities and backend selection](WORKFLOW_DEFINITIONS.md#重复实例职责和后端选择).

After editing an example, refresh resource digests and run `check`. This Python example refreshes local digests; replace `my-agent` with your directory:

```python
import hashlib
import json
from pathlib import Path
from ergora.skill_assets import digest_tree

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

<a id="从固定原包派生新版本"></a>
## Derive a new version from a pinned original bundle

When changing only the canonical document, retain every original bundle file and submit a complete new `agent.json` directly. First use `show` to obtain the original version's `digest` and `definition`. Save `definition` separately as `new-agent.json`, then edit the version and any roles, specialties or backend fields. Replace `BASE_DIGEST` below with the original bundle digest:

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --check
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json
```

`--check` checks the candidate without registering a version; omitting it publishes the version. The response contains the candidate `digest`, canonical document, file/resource identities, pinned `base` and `published`, without a temporary directory. Without resource arguments, only `agent.json` is rewritten using UTF-8, sorted keys, two-space indentation and a final newline. Original instructions, context, Skill attachments, undeclared files and empty directories are copied completely. Resource declarations must still match the actual files. To change file contents, use resource revision below or export/edit/check/import. The canonical document can be supplied as JSON or read as YAML with `--format yaml`; the library still stores canonical JSON.

A mismatched original digest is rejected; the new document still undergoes current role/backend contract checks. Different contents cannot be published under the same ID/version; an identical request can be retried. The original version is always retained. `check` does not reserve a version, so concurrent publication can still cause a subsequent version conflict. Derivation does not run or authenticate a backend or modify workflows and tasks referencing the original version. See [workflow revisions](WORKFLOW_DEFINITIONS.md#修订分享与恢复) for updating references.

Local HTTP entry points use the same owner as the CLI: `POST /api/agent-definitions/{id}/{version}/revisions/check` checks only; `POST /api/agent-definitions/{id}/{version}/revisions` publishes. The JSON request is `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`, with the original 64-character lowercase digest and the complete new document. Both retain the complete original bundle without creating tasks, approvals or execution sessions.

<a id="修订完整资源文件"></a>
## Revise complete resource files

The CLI can write complete files, explicitly delete files or add empty directories on top of a pinned original bundle. Prepare a new canonical document and an operations directory first. Unedited files retain their original bytes. This example extends `architecture-reviewer 1.0.0` above with a context resource:

The output files below must use UTF-8. In Windows PowerShell 5.1, replace `> 文件.json` with `| Set-Content -Encoding UTF8 文件.json`; see the [Windows guide](WINDOWS.md#agent-安装与认证) for input encoding.

```bash
ergora agent definition show architecture-reviewer 1.0.0 > base-agent.json
```

Run this Python to save the original bundle digest and create `resource-changes/changes.json`, complete content files and the new document. If the version already exists, use a new unpublished version. Resource paths are relative to the entire definition bundle. Initially give new declarations a valid placeholder digest; preview returns the actual digest:

```python
import json
from pathlib import Path

base = json.loads(Path("base-agent.json").read_text(encoding="utf-8-sig"))
definition = base["definition"]
definition["version"] = "1.0.1"
definition["resources"].append({"id": "project-context", "kind": "context",
    "path": "context/project.md", "sha256": "0" * 64})
root = Path("resource-changes")
(root / "files/context").mkdir(parents=True, exist_ok=True)
(root / "files/context/project.md").write_text("Project context: keep complete evidence.\n", encoding="utf-8")
(root / "changes.json").write_text(json.dumps({"schema_version": 1, "operations": [
    {"op": "write", "path": "context/project.md"},
    {"op": "mkdir", "path": "references/empty"}]}), encoding="utf-8")
Path("new-agent.json").write_text(json.dumps(definition, ensure_ascii=False), encoding="utf-8")
print(base["digest"])  # 替换下面的 BASE_DIGEST
```

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --preview-resources > resource-preview.json
```

Preview performs full admission without publishing. Inspect the response's `changes`, `directory_changes`, suggested `definition` and `candidate`. Save the suggested document to `new-agent.json`:

```python
import json
from pathlib import Path

preview = json.loads(Path("resource-preview.json").read_text(encoding="utf-8-sig"))
Path("new-agent.json").write_text(json.dumps(preview["definition"], ensure_ascii=False), encoding="utf-8")
```

After confirming the changes, explicitly accept the candidate using the saved preview, then check and publish:

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --accept-candidate ./resource-preview.json
```

`candidate` contains both the complete bundle `digest` and the complete sorted `directories`. Changes to the document, ordinary attachments, executable bits or directories require a new preview and acceptance; the final check does not refresh resource digests automatically. Preview neither reserves a version nor grants project approval. The same candidate can be retried explicitly. If an existing object with the same digest has different directories, resource publication explicitly rejects it: increment the version and preview again. It does not add missing directories to the old object. Resource declarations and permissions are managed separately; adding a Skill grants no tool or network authority.

An operations directory's `write` bytes come from `files/<path>`; source-file executable bits are not used, and the manifest must not also specify `content_base64`. When `executable_bits` is omitted, existing files retain their bits and new files use zero. If needed, specify an integer subset of `0o111`; a platform that cannot implement it rejects the operation. Ordinary attachments can be binary or empty files. Files declared as instructions/context must still be nonempty UTF-8, and a Skill still requires a complete tree and valid frontmatter.

`{"op":"delete","path":"old.bin"}` deletes only an existing ordinary file. If a resource declaration still references it, explicitly remove that declaration in the new document. Files absent from the manifest remain unchanged. `mkdir` and `write` create missing parent directories automatically; `mkdir` can retain an existing directory. Duplicate operations, case collisions and ancestor/descendant overlaps are rejected, such as mkdir `new` together with write `new/a.md`; a write alone creates the parent directory. Canonical `agent.json` and `workflow.json` go only through the document entry point. There is no recursive deletion, rename or implicit directory replacement.

The HTTP equivalent is `POST .../revisions/preview-resources`, with `base_digest`, the complete `definition` and `resource_changes:{"schema_version":1,"operations":[...]}` in the body. A write entry carries complete `content_base64` instead of a local directory. Supply the preview's suggested document and `candidate` as the final body's `definition` and `accepted_candidate`, together with the same `resource_changes`, to the original `/revisions/check` and `/revisions` endpoints. The local same-origin rule and `X-Ergora-Request: 1` still apply. The total HTTP request limit is `4_000_000` bytes including base64; use the CLI for larger changes. The CLI operations directory, including its manifest, is limited to 10 MB/500 files/500 directories. The final bundle must also meet the original 10 MB/500 files/500 directories/32-level limits, with at most 10 MB of written bytes and 1,500 operations. Model authentication and background task services are not required.

<a id="读取固定版本文件"></a>
## Read files from a pinned version

```bash
ergora agent definition file architecture-reviewer 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

Take the file path from that version's `show` response under `files`; historical reading does not require the backend to remain callable today. The response includes the whole-file SHA, executable bits, size, byte offset, `content_base64`, `next_offset` and `complete`. Read consecutive windows using `next_offset` until null. Only a response containing all bytes starting at zero has `complete:true`; the last page of a later window cannot replace the entire file on its own. Offsets count bytes, so UTF-8 characters can cross page boundaries. Merge all bytes before strict decoding. Each page is 1–65536 bytes; empty files can also be read completely. Ordinary undeclared attachments are readable, while paths outside the bundle or absent from its file inventory are rejected.

HTTP uses `POST /api/agent-definitions/{id}/{version}/files/read` with body `{"base_digest":"...","path":"instructions.md","offset":0,"limit":65536}`. This entry point reads only, without executing attachments or creating resource sessions. Use `export` to share the complete bundle.

<a id="在页面编辑专长-agent"></a>
## Edit a specialist Agent in the console

Run `ergora serve`, open “Agent 与组合库” (Agent and composition library), and import a built-in composition or select an exact version of an existing Agent. In “字段编辑” (field editing), increment the version, edit its description, roles, specialties and backend request, then click “应用字段文本” (apply field text). The basic backend request selector fills configuration only. Models and options must still meet the selected tool's contract; a successful selection does not establish installation or authentication.

You can also select a complete Agent instance path from the [published nested graph](WORKFLOW_DEFINITIONS.md#查看已发布嵌套关系图), then choose “打开所选精确定义” (open the selected exact definition). This pins the original ID/version/digest. Instances referencing the same Agent open the same immutable definition. Instance permissions and input bindings belong to the structural parent workflow; edit them through “打开结构父定义” (open the structural parent definition). The graph matches specialties against the exact Agent index, without substituting the latest version.

Search the graph by responsibility, specialty, backend or complete path, for example `reviewer codex`. Search retains unmatched structure. A result button can expand structural ancestors and locate the instance. The complete instance table also lets you directly select leaves inside collapsed structures and inspect every inherited material. A missing specialty index is shown explicitly; unknown capability cannot be treated as present. Collapse/search changes only the page display, without changing Agent authority or the selected backend.

The workflow page can also [compare two published compositions](WORKFLOW_DEFINITIONS.md#比较两个已发布组合), checking each instance's exact Agent reference, backend, role, permissions and complete inherited materials. Resource content and source versions are shown separately; changing a version alone does not establish changed Skill content. Comparison does not modify an independent Agent definition or editing buffer. Fields absent from preview, such as description and specialties, still require opening the exact definition.

You can also edit “定义 JSON 原文” (definition JSON source) or “定义 YAML 原文” (definition YAML source). Explicitly apply the source before “检查定义候选” (check definition candidate); only a successful check enables “发布新定义版本” (publish a new definition version). Unapplied fields, JSON and YAML are retained separately. Apply or discard each first; another representation cannot overwrite unresolved source text. Formatting changes alone do not regenerate the other format. If a semantic change requires replacing other custom source text, the console first prompts you to download it and explicitly confirm synchronization. Complex JSON within fields also rejects duplicate keys.

After success, keep the exact publication receipt. “以已发布版本继续编辑” (continue editing from the published version) selects a new base while retaining the original session. If a response is lost, do not change the base or document and present it as the original request. Explicitly retry with the same base and document to reconcile it. Checks do not reserve versions; publication can still encounter a version conflict, which never overwrites an existing version.

Browser buffers are isolated by control directory, kind, original ID/version/digest and tab. After a refresh, select the original version again to restore the buffer. A buffer is not a persistent definition. Recovery uses the shared converter to verify applied JSON/YAML semantics while retaining invalid unapplied text. A damaged buffer can be downloaded raw, retried for verification or explicitly cleared. Storage-quota exhaustion is shown with an option to download the current editing buffer. Before closing the tab or changing machines, publish or separately save a download. Browser history retains at most 50 entries and evicts older snapshots toward a 4 MiB budget, including complete resource-operation bytes. The newest snapshot is retained even when it alone exceeds that budget; history starts again after refresh.

YAML uses the JSON data model: object keys must be strings; duplicate keys, aliases, cycles and custom tags are rejected. Quote ambiguous strings such as dates. Conversion allows at most 64 levels and 100,000 values, including mapping keys; the total HTTP request limit is 4 MB. JSON/YAML are editing representations and do not execute their content. Publication still stores canonical JSON in a complete resource bundle. See the resource-editing steps below for file operations in the console. Larger changes can still use CLI resource revision above or export/edit/check/import. Downloading a single document excludes attachments; export the complete bundle to share a definition.

<a id="在页面编辑资源与附件"></a>
## Edit resources and attachments in the console

Use “资源与附件编辑” (resource and attachment editing) for the same exact version. Every change remains relative to the original bundle shown on the page and does not rewrite it.

1. Increment and apply the version in the fields. To declare a new resource, use JSON/YAML `resources` to add `id/kind/path` and a valid 64-character placeholder digest: instructions/context uses `sha256`, and a Skill uses `digest`. Apply the document first. Ordinary attachments need no declaration. When deleting a still-declared file, explicitly remove or update its declaration too.
2. Expand “原包文件：完整读取与下载” (original bundle files: complete reading and download) to read a complete text into a draft or download the original bytes. Reads use consecutive bounded windows; editing becomes available after merging and verifying the whole-file SHA, preserving any UTF-8 BOM. Invalid UTF-8 remains binary. Canonical JSON is still edited only through the document entry point.
3. Enter a bundle-relative path and choose a complete write, explicit file deletion or empty-directory addition. Enter complete text or upload one complete file. Upload preserves bytes, with explicit conversion to text when confirmed as UTF-8. Leave executable bits blank to retain the original; new files default to zero. If needed, enter an octal value such as `100`, with each digit restricted to 0 or 1. Executable bits are not inferred from an uploaded file.
4. Click “暂存文件操作” (stage file operation). The list is the complete working set relative to the original bundle; later additions retain previously adopted operations. Staging the same exact path explicitly replaces that entry. Removing an entry restores the original bundle's behavior for that path. Use “编辑操作” (edit operation) in the operations list for already modified files; the original file list always reads the old base. Add a Skill's complete tree file by file. Omitting a file does not imply deletion. Write/mkdir creates parents automatically; do not add overlapping parent-directory operations.
5. After finishing file drafts, click “预览资源候选” (preview resource candidate), inspect file/directory changes and the suggested document, then click “采用资源摘要” (adopt resource digests). Preview does not apply or publish anything. Adoption records the document, complete operations and accepted identity together in one history entry, asking for confirmation before regenerating custom JSON/YAML formatting. Then check the definition candidate and, after a successful check, explicitly publish a new definition version.

Unapplied fields/source/file drafts/operations block checking and publishing an old snapshot. Any document or resource change invalidates the last check, preview and acceptance. A second edit requires a new preview and adoption. Undo/redo restores the applied document, complete operations and accepted identity together, but still requires a new check. Unapplied content does not enter applied history.

Refresh can restore applied and unapplied buffers, rechecking both applied document representations and complete bytes; previews and checks are not reused. Older buffers without resources can be restored. Damaged buffers retain a raw download and refuse publication. Browser-quota exhaustion is shown explicitly. “下载定义编辑缓冲” (download definition editing buffer) includes all applied/unapplied documents and operation bytes, excluding unedited original-bundle files, so it is not an independent complete bundle. Publish or save a download before closing the tab or changing machines. Use CLI `export` separately for a complete bundle.

A complete operation set allows at most 1,500 entries and 10,000,000 decoded written bytes, subtracting the replaced entry's bytes. Exceeding the limit is rejected before reading/encoding and retaining new bytes, preserving the original set and draft. The total HTTP request limit is 4,000,000 bytes including base64. For larger changes, retain the buffer and use CLI `--resources`; the console does not automatically split or resend requests. Page reads and uploads neither start an Agent nor grant tool permissions.

<a id="资源和存储边界"></a>
## Resource and storage boundaries

Resource paths must be portable bundle-relative paths using `/`. Absolute paths, `..`, backslashes, Windows reserved names/streams and case collisions are rejected. Bundles cannot contain `.git`, symlinks, reparse points or special files, and are limited to 10 MB, 500 files, 500 directories and 32 directory levels. Missing resource digests, content mismatches or invalid Skill frontmatter fail before import.

The current schema rejects unsupported MCP, permission and budget fields. Existing sandbox fields in backend bindings still use the original tool contract. Static import does not establish a working sandbox or permission approval. Do not put credential values in shareable bundles. Backend authentication continues through its existing login or environment variables.

The library lives under persistent State's `agent-definitions/`: `index.json` maps exact IDs/versions to bundle digests, while `objects/<摘要>/` stores complete bundles. It uses `ERGORA_HOME`, `--home` and platform defaults; see the [installation guide](USAGE.md). Import validates and stages the complete tree, then serializes publication with the existing file lock. The first object and index become visible as one complete library. Incremental objects finish before an atomic index update. Interrupted imports can be retried. A published library without its index, or a missing or modified registered object, refuses automatic replacement. Damaged content is not treated as a repairable cache.

The existing [offline backup and recovery](USAGE.md#升级与持久数据) commands save the entire library. Backup verification rechecks index references, definition identities and every resource digest. Recovery still requires the original platform, original State path and stopped writers. A backup preserves resource identities without authenticating bundle authors or establishing trustworthy material.

<a id="历史资产与当前准入"></a>
## Historical assets and current admission

For stored bundles, `show/list/export` checks versioned structure and complete content; backup/recovery also checks recursive workflow references. Both are independent of currently selectable roles/backends. If an upgrade removes a tool or tightens configuration rules, complete old materials can still be read and exported. Missing files, tampering and identity drift still fail; historical content is never rewritten automatically.

`list --role` can filter historical role tags even after a role leaves the current runtime catalog. `check/import` also enforces the current role and backend contracts, including renewed admission when importing an identical bundle. Workflow `preview` uses current admission for referenced Agents. A successful historical read therefore does not establish current backend availability or execution authority; an exported old bundle may also fail reimport under current rules. To use an alternative tool, publish an explicit new Agent version and a new workflow version referencing it. Existing versions are not modified.


After static workflow preview, the console can explicitly save the current root and every Agent/Skill attachment as a complete manifest, or `composition freeze-manifest` can bind the original preview digest. Formal admission for different backends and writer trust are still checked at task handoff. See [persistent complete bundles](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录).

The formal task page can [select a backend for each composition instance](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合), without changing this Agent's default request or other instances referencing it. Reviewers follow the exact definition by default. Writable implementers require an explicit backend/execution-boundary override and a reason. Backend forms share the component schema with project bindings. A selection does not establish authentication or support for that execution mode; formal task preview rechecks the original contract.
