# Manage project memory and shared cases

English · [Documentation](../README.md) · [简体中文](../zh-CN/improvement/memory.md)

## Project memory

The default `{"tool":"sqlite"}` is a persistent baseline requiring no service, supporting memory, sources, revisions, corrections, and retrieval. For example:

```bash
ergora memory save my-project --text note.md --source git:docs/design.md --source-revision COMMIT_SHA
ergora memory list my-project
ergora memory search my-project 'deployment port'
ergora memory history my-project MEMORY_ID
ergora memory save my-project --id MEMORY_ID --revision 1 --text corrected.md --source git:docs/design.md --source-revision NEW_COMMIT
ergora memory restore my-project MEMORY_ID --from-revision 1 --revision 2
ergora memory delete my-project MEMORY_ID --revision 3
ergora memory sync my-project
```

The SQLite baseline retrieves by word containment; it provides neither embeddings nor automatic fact extraction. Deletion clears historical text and sources in the application while retaining a deletion marker; handle independent backups separately. Stop writes before backing up the complete `ERGORA_HOME`; using that directory on a new device restores project configuration, memory, and evidence. If project paths change, register a project appropriate to the new device instead of treating an unknown path as the original checkout.

### Optional ReMe

ReMe is a separate service, not a default Python dependency. Supported interfaces follow a [fixed official commit](https://github.com/agentscope-ai/ReMe/tree/1e51e0dc1b1effe60f7ee425298f3b6f8ef4cbd9). Install that version in a separate Python 3.11+ environment to avoid affecting Ergora and existing training dependencies:

```bash
python3 -m venv "$HOME/.local/share/ergora-reme-venv"
"$HOME/.local/share/ergora-reme-venv/bin/pip" install 'reme-ai[core] @ git+https://github.com/agentscope-ai/ReMe.git@1e51e0dc1b1effe60f7ee425298f3b6f8ef4cbd9'
"$HOME/.local/share/ergora-reme-venv/bin/reme" start workspace_dir="$HOME/.local/share/ergora-reme/my-project" service.port=2333
```

ReMe installation and service operation require separate acceptance in the target environment. Dependencies and resource requirements follow the pinned version; basic BM25 / file operations require no model key, while automatic extraction needs ReMe model configuration. Use a separate workspace / service instance for each project requiring isolation.

Save the following JSON as `memory-binding.json`, then save the binding with the current project revision:

```json
{"tool":"reme","endpoint":"http://127.0.0.1:2333"}
```

```bash
ergora project bind my-project memory --binding memory-binding.json --revision CURRENT_REVISION
ergora memory sync my-project
ergora memory search my-project 'deployment port'
```

For gateway authentication, add `"token_env":"REME_TOKEN"`; its value comes only from the runtime process environment. Selecting this backend sends valid project memory to the configured service; sources and revisions remain local. Synchronization preserves retry markers and explicitly reports response failures; writing a service file does not mean asynchronous indexing is already searchable. Switching backends does not delete old projections, and later synchronization continues maintaining registered projections. After deletion, run `memory sync` and confirm responses from all original endpoints. Project path filtering in a shared ReMe service is not multi-tenant identity isolation.

This round verified protocol fixtures and local semantics; it did not run complete ReMe / automatic hooks or claim that memory improves model quality.

After a ReMe workspace is cleared or rebuilt by migration at the same endpoint, run `ergora memory sync my-project --rebuild` to rewrite valid projections; ordinary synchronization relies on the last write confirmation and sends changes only. After rotating credential variables, save the new binding and synchronize once before revoking the old variable; mirrors retain the new variable name so deletions can still propagate after switching back to local storage. Retrieval uses the official `search_filter.paths` to restrict candidates before limits, then rechecks returned paths against current local text.

## Memory expiry and retrieval

Memory can have a timezone-qualified ISO 8601 expiry saved as UTC. Once the server's observation time reaches expiry, it leaves new retrievals. Expiry retains the body and history. By default `memory list`, dashboard and `memory search` return only valid current revisions. `memory catalog` or `GET /api/projects/PROJECT_ID/memory-catalog` explicitly reads all states, original records and `observed_at` for review; it is not automatic recall. The observation is a single instant, after which expiry may occur.

```bash
ergora memory save my-project --text observation.md --source git:docs/design.md --source-revision COMMIT_SHA --expires-at 2027-01-01T00:00:00+08:00
ergora memory list my-project
ergora memory catalog my-project
ergora memory search my-project "性能基线"
# A correction without expiry keeps the latest revision's expiry.
ergora memory save my-project --text correction.md --source git:docs/design.md --source-revision NEW_COMMIT_SHA --id MEMORY_ID --revision CURRENT_REVISION
# Explicitly remove expiry; alternatively use --expires-at for a new time.
ergora memory save my-project --text correction.md --source git:docs/design.md --source-revision NEW_COMMIT_SHA --id MEMORY_ID --revision CURRENT_REVISION --no-expiry
```

The original HTTP save interface `POST /api/projects/PROJECT_ID/memories` accepts optional `expires_at`. Omission retains the original expiry for corrections and means no expiry for new records. Explicit `null` removes expiry. A new time creates a new revision and still checks the original revision. Restoring history copies that revision's expiry, including expired times; restoration does not renew it. Deletion clears all historical bodies/provenance irreversibly under the original rules. Archived inputs and independent backups remain separate.

ReMe synchronization removes expired/deleted projections without requiring a timer. After remote retrieval, local validity and revision are rechecked, dropping hits that expired, were deleted or were corrected in flight. Remote bodies never become canonical. Watcher delays still affect remote index cleanup, so instantaneous deletion is not guaranteed; explicitly synchronize or rebuild when needed.

The current database is schema v6. Upgrading does not rewrite old memories and first saves an original-database backup. **Stop old CLI tasks, the console and workers before upgrading them together and explicitly restarting.** Reopened old clients refuse the new version, while original triggers reject already-open old writers. SQLite cannot revoke materials or caches an old reader already fetched. New and old processes must not share one home concurrently. Rollback requires the complete pre-upgrade offline backup at the original home; retain new-version data separately.

## Shared local case library

Use the installed `ergora` command from any workspace. Pass the same absolute path to an existing local directory with `--library`. Shared commands use that directory's `cases/` tree independently of project registration, `ERGORA_HOME` and ReMe.

```bash
ergora memory shared search 'Task MCP requires the optional dependency' --library "$case_library" \
  --technology ergora-task-mcp --environment linux --version 0.2.0
ergora memory shared show task-mcp-missing-sdk --library "$case_library" \
  --revision 1 --sha256 SHA256_FROM_SEARCH \
  --technology ergora-task-mcp --environment linux --version 0.2.0
```

Search returns up to five current matches by default and accepts `--limit` from 1 to 20. A match includes the ID, revision, SHA-256 of the complete Markdown, status, sources, and a title, signature or excerpt bounded to 512 UTF-8 bytes. A complete error signature in the query ranks ahead of title and alias matches. With `--project`, `--technology`, `--environment` or `--version`, `applicability_match` reports `matched`, `incompatible` or `unknown` and lists the mismatched or missing facts. Project, technology and environment labels are case-insensitive. Versions are exact strings. An `unresolved` case records an open question and a next diagnostic.

Both reads return JSON on standard output. `show` returns the current metadata in `record` and the exact Markdown in `markdown`, with a 65,536-byte file limit. Provide both `--revision` and `--sha256` to verify a search selection. Search returns an empty `results` array when no eligible case matches. An unknown case or a stale pinned read produces exit code 2 and a diagnostic on standard error. Expiry and withdrawal remove the case from new search. In those states an unpinned `show` reports the current metadata with `markdown: null`, and a pinned `show` refuses the selection.

### Publish a reviewed case

Keep drafts outside the library's `cases/` tree. Each draft is a UTF-8 Markdown file. Put JSON front matter between lines containing `---`. Provide the stable lowercase ID, revision, title, aliases or error signatures, applicability, status, sources, and `expires_at`. Applicability specifies a project or technology, an environment and a nonempty list of exact versions. Each source has a shareable `uri` and a pinned `revision`. The library treats source references such as `git:docs/design.md` and HTTPS URLs as text. Use a timestamp with a timezone for expiry or `null` for an unlimited lifetime. Record the symptom, cause or open question, resolution or next diagnostic, and verification in the body. [Example case](../../tests/fixtures/shared-task-mcp-missing.md)

Record the SHA-256 of the complete Markdown at draft review. The publisher checks it against the bytes it will publish.

```bash
ergora memory shared publish ./reviewed-case.md --library "$case_library" --expected-revision 0 \
  --sha256 REVIEWED_SHA256
```

The first publication initializes `cases/` in the selected directory. Start a new case at revision 1 and use `--expected-revision 0`. For a correction or withdrawal, keep the same ID, advance the draft by one revision, and provide the current revision as `--expected-revision`. Use status `verified`, `unresolved` or `withdrawn`. One locked publisher exposes each complete revision as `cases/ID/REVISION/case.md`. If publication is interrupted, check the current revision and digest before retrying. Preserve the complete shared library directory in an offline backup while publication is stopped, separately from any `ERGORA_HOME` backup.

Continue with [Carry a retrospective into the next task](workflow.md) or [Prepare a task's frozen composition](../development/preparation.md).
