# Revise and read complete definition resources

English · [Documentation](../README.md) · [简体中文](../zh-CN/definitions/resources.md)

Use the exact original ID, version and digest from [Agent definitions](agents.md). Workflow callers reuse this complete-resource contract and add their own [dependency publication order](workflows/revisions.md).

## Revise complete resource files

The CLI can write complete files, explicitly delete files or add empty directories on top of a pinned original bundle. Prepare a new canonical document and an operations directory first. Unedited files retain their original bytes. This example extends the [`architecture-reviewer 1.0.0` definition example](agents.md#create-and-modify-definitions) with a context resource:

The output files below must use UTF-8. In Windows PowerShell 5.1, replace `> 文件.json` with `| Set-Content -Encoding UTF8 文件.json`; see the [Windows guide](../install/windows.md#install-and-authenticate-agents) for input encoding.

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

## Read files from a pinned version

```bash
ergora agent definition file architecture-reviewer 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

Take the file path from that version's `show` response under `files`; historical reading does not require the backend to remain callable today. The response includes the whole-file SHA, executable bits, size, byte offset, `content_base64`, `next_offset` and `complete`. Read consecutive windows using `next_offset` until null. Only a response containing all bytes starting at zero has `complete:true`; the last page of a later window cannot replace the entire file on its own. Offsets count bytes, so UTF-8 characters can cross page boundaries. Merge all bytes before strict decoding. Each page is 1–65536 bytes; empty files can also be read completely. Ordinary undeclared attachments are readable, while paths outside the bundle or absent from its file inventory are rejected.

HTTP uses `POST /api/agent-definitions/{id}/{version}/files/read` with body `{"base_digest":"...","path":"instructions.md","offset":0,"limit":65536}`. This entry point reads only, without executing attachments or creating resource sessions. Use `export` to share the complete bundle.

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

## Resource and storage boundaries

Resource paths must be portable bundle-relative paths using `/`. Absolute paths, `..`, backslashes, Windows reserved names/streams and case collisions are rejected. Bundles cannot contain `.git`, symlinks, reparse points or special files, and are limited to 10 MB, 500 files, 500 directories and 32 directory levels. Missing resource digests, content mismatches or invalid Skill frontmatter fail before import.

The current schema rejects unsupported MCP, permission and budget fields. Existing sandbox fields in backend bindings still use the original tool contract. Static import does not establish a working sandbox or permission approval. Do not put credential values in shareable bundles. Backend authentication continues through its existing login or environment variables.

The library lives under persistent State's `agent-definitions/`: `index.json` maps exact IDs/versions to bundle digests, while `objects/<摘要>/` stores complete bundles. It uses `ERGORA_HOME`, `--home` and platform defaults; see the [installation guide](../install/linux.md). Import validates and stages the complete tree, then serializes publication with the existing file lock. The first object and index become visible as one complete library. Incremental objects finish before an atomic index update. Interrupted imports can be retried. A published library without its index, or a missing or modified registered object, refuses automatic replacement. Damaged content is not treated as a repairable cache.

The existing [offline backup and recovery](../install/upgrades.md#upgrades-and-persistent-data) commands save the entire library. Backup verification rechecks index references, definition identities and every resource digest. Recovery still requires the original platform, original State path and stopped writers. A backup preserves resource identities without authenticating bundle authors or establishing trustworthy material.

Continue: [Create and revise specialist Agent definitions](agents.md) · [Revise and share exact workflow versions](workflows/revisions.md).
