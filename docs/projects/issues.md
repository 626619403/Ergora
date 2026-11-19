# Read and freeze project issue context

English · [Documentation](../README.md) · [简体中文](../zh-CN/projects/issues.md)

## Read project issue context

An ordinary project can read an explicit issue without installing the reference executor, starting services or configuring a model. First register the business Git repository with `project add`, then save a tracker binding; configure the project namespace and API address separately. The file below contains only a variable name. Set the environment variable's value in the same environment that starts the CLI/Web service.

```json
{
  "tool": "gitlab",
  "project": "team/subgroup/repository",
  "api_url": "https://gitlab.com/api/v4",
  "token_env": "GITLAB_TOKEN"
}
```

Save it as `tracker.json`, then run:

```bash
ergora project show PROJECT
ergora project bind PROJECT tracker --binding tracker.json --revision 1
ergora issue show PROJECT 7
```

For `--revision`, use the current value returned by `project show`. A GitHub binding uses `"tool":"github"` and `"project":"owner/repository"`, with API default `https://api.github.com`. The REST version is pinned to `2022-11-28` by default; use `api_version` to explicitly choose a supported date version. GitLab defaults to `https://gitlab.com/api/v4` and supports complete subgroup paths. Self-hosted APIs must use HTTPS; HTTP is supported only for loopback. Public issues can be read anonymously by omitting `token_env`; if a variable name is configured but its environment value is absent, the operation fails visibly. Unknown fields and credentials in URLs are rejected; the interface does not follow redirects.

The `issue show` argument is a GitHub repository issue number or a GitLab project issue iid; the response records the global native ID separately. It returns the complete title/body/labels, native state and update time, ETag if present, raw response SHA256, API address/namespace, project revision/configuration digest and the time of this observation. The body remains text, marked `context_only:true`. `show` does not save it; use `capture` below for persistence. It does not scan remote lists, read comments, dispatch work or write back. ETags, update times and digests are observation clues; they provide neither write CAS nor task approval.

The HTTP endpoint is `GET /api/projects/PROJECT/issues/7` and shares the CLI use case. The existing tool bindings page displays tracker configuration according to its schema. See [Reading on the page](#read-and-save-issues-on-the-page) for the issue page; observe lists continue according to the plan. Formally registered projects can read only their registered kind/namespace. Changing the source binding creates a new project revision without changing old tasks or reference registrations. Formal registration does not yet include the API host; later dispatch across hosts must have its identity approved separately and cannot directly reuse an old claim.

Only ordinary GitHub issues/GitLab project issues are accepted. GitHub PRs, GitLab non-issue types and incompatible responses are rejected explicitly. Each operation makes one GET with a 20-second socket I/O timeout and a 1 MiB complete-response limit, with no automatic retry. This is not a 20-second wall-time guarantee for the entire call. Authentication, unavailability, redirect, size-limit and truncation failures are not disguised as empty issues. See the [integration guide](#project-issue-sources) for detailed interface tradeoffs and the unverified self-hosted scope.

## Save issues and link task context

`capture` explicitly reads and saves one complete, immutable issue context. Reading a saved snapshot later does not require a working current tracker or credentials; use the same control directory `--home` for all commands. Check the current project revision first, then run:

```bash
ergora issue capture PROJECT 7 --revision 2
ergora issue snapshots PROJECT --limit 20
ergora issue snapshot PROJECT SNAPSHOT_SHA
```

capture returns `snapshot.sha256`, `snapshot.first_observed_at` and this call's `observed_at`. The SHA binds the complete observation and the tracker configuration used for it, including the API base address, namespace, issue number/iid, native ID, body, response digest and project revision; configuration stores only the credential variable name. The first-save time is excluded from the content SHA. Rereading identical content/configuration returns the original snapshot; an issue update produces a new snapshot. Changing configuration during the GET still saves an observation explicitly marked with the original revision. The raw HTTP response body is not saved; `response.sha256` is only its byte digest.

To link a snapshot to an existing task, first publish the contract through the original `task preview → task create` flow, then use `task creation PROJECT TASK` to read its `intent_sha256`. Explicitly provide that SHA, the snapshot SHA, task ID and reason for the link:

```bash
ergora issue link-task PROJECT SNAPSHOT_SHA TASK --creation-sha256 CREATION_SHA --revision 2 --reason "本次工作参考的来源"
ergora issue links PROJECT --snapshot SNAPSHOT_SHA --limit 20
ergora issue links PROJECT --task TASK --limit 20
```

A snapshot can link to multiple tasks, and a task can explicitly link to later snapshots. Repeating the same relationship returns its original reason/time even if the original request's project revision is stale. A new relationship still requires the current project revision, a published target creation and an exact SHA match. For pending, use the original resume-create flow first; for conflict, check the original files first. `created_revision` is the project revision at creation. Use a new task ID for a new work version under the original contract. Old task inputs/approvals are not rewritten, linking does not start a task, and it does not automatically make a running Agent read the material. The output's `operator_asserted_context / context_only / execution_authorized:false` describes an operator-asserted context relationship. The old formal source has no API host, so the link cannot prove native source ownership or replace dispatch admission.

Both lists return bounded metadata only; read complete bodies through individual snapshots. `--limit` is 1–100. If `next_cursor` is nonempty, pass it unchanged to `--after` and keep the same project/filters. Content added during pagination that sorts before the cursor requires rereading from the first page. This query discovers saved records; it is neither a fixed view nor dispatch deduplication. If a capture response is lost, query the local list; another capture may observe updated content.

HTTP and CLI share the same use cases. POST retains local Origin and `X-Ergora-Request: 1` protection:

|Operation|HTTP endpoint/body|
|---|---|
|Save|`POST /api/projects/PROJECT/issues/7/snapshots`, `{"revision":2}`|
|Snapshot metadata list|`GET /api/projects/PROJECT/issue-snapshots?limit=20&after=CURSOR`|
|Complete snapshot|`GET /api/projects/PROJECT/issue-snapshots/SNAPSHOT_SHA`|
|Link|`POST /api/projects/PROJECT/issue-links`, `{"snapshot_sha256":"…","task_id":"TASK","creation_sha256":"…","revision":2,"reason":"…"}`|
|Link list|`GET /api/projects/PROJECT/issue-links?task_id=TASK&snapshot_sha256=SNAPSHOT_SHA&limit=20`; both filters are optional, and `after` is supported|

Snapshots and links are stored in the control plane's SQLite database and included in complete offline backup/restoration through the existing `state backup / verify-backup / restore` flow. The current database uses schema v6. Before upgrading, stop old processes and keep a backup of the old database; old clients cannot write to the new database. See [Expiry and upgrade notes](../improvement/memory.md#memory-expiry-and-retrieval). Complete backups still require stopped writers, the same platform and the original home. Save external execution directories separately; context links cannot reconstruct tasks. Source dispatch is described next, candidate comments under [Writeback](candidate-actions.md#post-an-issue-comment-for-an-exported-candidate), and source reading on the page in the next section. The remaining issue action pages are delivered in slices under the [integration guide](#project-issue-sources).

## Read and save issues on the page

After selecting the current project's GitHub or GitLab source under “Tool bindings,” open “Issue sources,” enter an issue number/iid and click “Read current issue.” Reading the platform requires an explicit click; entering the page reads only the local snapshot list. The title, complete body, native ID, API source, project revision and response digest appear as text, and you can expand the complete record.

“Reread and save snapshot” reads the platform again and saves using the project revision currently held by the page. Platform content may have changed, so check the returned complete snapshot. Saving does not create or start a task, or send comments, labels or PRs/MRs. If the project revision changes, click “Refresh” at the top before operating. If saving is unconfirmed, use “Reread list” first to check; a failed response does not establish that nothing was saved.

History contains at most 20 entries per page. “Previous page/Next page” follows the original cursor, and “View snapshot” reads the complete snapshot offline. The list sorts by content digest; new content may appear on earlier pages, so reread the first page when needed. Historical snapshots retain their source at the time and remain readable if the project changes to another source or manual. They do not represent current platform content or the current tool binding. manual disables external issue reads. Bodies do not execute HTML/Markdown, and issue text cannot expand Agent permissions. “Prepare formal task from this snapshot” on a saved snapshot opens the existing formal task form; the page carries this project's digest temporarily. After refreshing, reenter from the snapshot or paste the SHA yourself. The source page itself handles reading only; use the CLI below for candidate actions.

## Create a source task from an issue snapshot

Page entry: view a saved snapshot in “Issue sources,” click “Prepare formal task from this snapshot,” then “Preview and create from selected snapshot.” You can also manually enter the optional source SHA under “Preview and create” in “Formal tasks.” Click “Read source snapshot” to read and check the complete body and source offline; the issue number is then fixed. After changing the digest, you must read it again; “Clear source selection” restores the entry without a source. A failed source read does not automatically fall back to a task without a source.

Select a registered development template and edit the complete input. Under “Agent source for this task,” choose “Complete manifest · composed execution and review.” Follow [Formal composition selection](../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page) to verify the package, assign work units, choose each leaf's backend and select execution trust. The preview displays the source SHA and complete frozen files; review them and explicitly create the task. The server rechecks the current binding, registered source and project revision. Readable historical snapshots are not proof that creation is currently allowed. Preview and creation do not connect to the issue platform, start Agents or write back to issues; submit the run separately. If creation is unknown, read/recover under the original ID without recapturing or resending with a different ID.

To freeze the issue body for a new task, use `task-definition-v3`. It supports governance and major-change templates and requires explicit `work-units-v2` execution/review composition. First follow [Specialist executor configuration](../definitions/workflows/contracts.md#specialist-writers-and-original-work-units) to prepare a complete `task-definition.json` containing the actual manifest, digest, work assignments and per-instance backends. Then save the snapshot and replace the project, number and revision in the following commands with current values:

```bash
ergora issue capture my-project 7 --revision 2 > issue-capture.json
python - <<'PY'
import json
from pathlib import Path
definition = json.loads(Path('task-definition.json').read_text(encoding='utf-8'))
saved = json.loads(Path('issue-capture.json').read_text(encoding='utf-8'))['snapshot']
definition.update(schema_version=3, task_id='issue-7-r1',
    issue_id=saved['payload']['observation']['source']['issue_id'],
    source={'snapshot_sha256': saved['sha256']})
Path('issue-task.json').write_text(json.dumps(definition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
ergora task preview my-project --definition issue-task.json --revision 2
# Check the complete issue_source, project configuration, specialists and permissions in files/task.spec.json, then use this preview digest:
ergora task create my-project --definition issue-task.json --revision 2 --preview-sha256 PREVIEW_SHA
ergora task creation my-project issue-7-r1
ergora task show my-project issue-7-r1
```

The snapshot and current execution configuration must belong to the same project, provider, complete API address and namespace, with matching number/iid. If the source is unchanged, changing Agents or the token variable reference after capture does not force a new issue read; the capture revision and this creation revision are saved separately. Reading a saved snapshot and previewing do not require an online tracker or token, but still require a registered project and the selected complete composition. After changing the API host/path or project, capture again; do not infer source identity from a web URL or old registration without a host.

New creations use creation3/formal envelope v7. The complete source enters the original execution input and each work/review material set; the existing composition still controls ancestor Skills and permissions. After publication, the task no longer depends on that snapshot in the control database, the current binding or the external body. `resume-create` recovers using the original intent SHA without reselecting the source. If an issue update requires another piece of work, use a new task ID and preview; old tasks, approvals and B0 context links remain intact.

Source tasks are admitted according to their frozen selections: checks cover only the actual inventory/plan roles, work/review leaf programs and configuration, the selected MCP mode, and the existing Git, timeout, Python and confirmed execution conditions in the current container. A2A, MLflow, LangGraph and unselected default implementer/reviewer roles are not required dependencies for this entry. Explicitly start `temporal worker executor` first, then start according to [Formal submission](../development/run-and-recover.md#submit-formal-tasks-and-recover-unknown-results). Trusted checks, policy, Temporal connectivity and shared issue claims retain the existing flow. Program availability does not establish authentication, quota or worker readiness; an actual failure retains the specific dependency and original submission status. Unknown recovery only queries the original ID without resending or repeating admission due to current tool changes. Old v1–v6 retain the original installation-level doctor.

Install this version and restart its worker/executor before accepting the v7 queue; check original invocation materials and receipts for actual Agent consumption. Existing limits remain: 1 MiB per file, 1,000,000 bytes each for stage/prompt, and limits on all ancestor materials and dynamic artifacts. Static content certain to exceed limits is rejected at preview; later artifacts exceeding limits are rejected in their original stage, with no implicit summary. v7 evidence/handoff retains the complete `contract.original_input` and checks the source/original admission SHA; the combined total remains subject to the original 1 MiB index and package-manifest limits. Old v1–v6 and old handoff packages are not migrated.

## Project issue sources

At the tracker layer, `manual` retains the local process; `github` / `gitlab` use their respective Adapters for explicit repository numbers / project iids. Configuration uses existing project bindings and schema forms, with shared domain use cases for CLI / HTTP. API host and namespace enter the observation identity; credentials retain only `token_env` references. Ordinary issue reads / snapshots and offline context require no reference runtime or background service; formal source tasks and candidate operations additionally require the original v7 creation / export identity. See [issue configuration and commands](#read-project-issue-context).

New implementations in this family follow the existing `IssueBackend` Interface. The family owns native paths, headers, identities, and field projections, registers in its family mapping, and adds a component description; upper use cases do not dispatch by vendor. Native issue reads, repository / exact ref and specified review reads, and comment operations each have actual contracts. Unimplemented operations explicitly reject requests; registering a component description does not make them available. Labels are an optional native capability; strict append on GitLab currently remains unsupported.

Current capabilities include ordinary issue reads / immutable snapshots / offline lists and task-context association, v7 source tasks, original candidate-neutral comments and explicit GitHub single-label writeback, read-only local / remote ref checks, and local immutable associations to existing PRs / MRs in the same repository. Formats are owned respectively by [issue-observation-v1](../../src/ergora/data/schemas/issue-observation-v1.json), the original task contract, the writeback owner, and [candidate-review-context-v1](../../src/ergora/data/schemas/candidate-review-context-v1.json); they do not share a remote-success marker. Association confirms neither the original attempt nor approval; unknown does not trigger resending, and current observations / ETags cannot serve as write CAS. There is no automatic issue intake, remote issue search / listing, or PR / MR creation / merging. Existing Symphony retains its configuration and behavior; see the [user manual](#read-and-save-issues-on-the-page) for page operations.

Continue: [Create a formal development task](../development/tasks.md) · [Observe and write back an exact candidate](candidate-actions.md).
