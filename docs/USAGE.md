<a id="安装与日常使用"></a>
# Installation and daily use

English · [简体中文](zh-CN/USAGE.md)

Ergora provides a local CLI and graphical control plane for Linux / Windows, while retaining the complete six-stage Linux reference distribution from v2.2. You can use the control plane on its own first, then connect project tools, issues, services and experiment environments as needed. See the [Windows guide](WINDOWS.md) for PowerShell installation, Agents and WSL2 support. See [Plan and progress](PLAN.md) for implemented capabilities and the scope actually accepted.

When choosing a template for the first time, follow the [three-template getting-started journey](TEMPLATE_WALKTHROUGHS.md) to assemble specialists, choose a backend for each instance, create through the v6 page, recover with the original ID and prepare training proposals. Then return to this guide for specific commands.

If you already have a local candidate, you can start with an [exact PR/MR review package](LOCAL_REVIEW.md): freeze complete Git objects, original requirements, explicit callers and ancestor rules without registering a project or logging into a model. You can also use `review collect` to bind an explicit GitHub/GitLab source through read-only access, then verify the package offline. Automatic domain review and posting feedback remotely are implemented separately.

## Current design-workflow availability

A first unified registration can store a schema2 design policy and its effective digests. It reports `execution_supported: false` and `human_channel_unavailable`; schema2 task creation and managed native execution refuse `design_policy_execution_unsupported`. Existing registrations cannot be upgraded, replaced or downgraded through that entry. See [the current registration boundary](PROJECTS.md#current-limits-of-design-policy-registration). These records provide policy storage, without executable design approval. Design source-journal storage and trusted owner/material/gate handling remain under implementation in [PLAN](PLAN.md); plans and research do not establish delivered support. Existing schema1 task contracts remain in force.

Per-Agent explicit reasoning fields can request a level supported by the selected backend/model. Unified fixed/preset/planner/automatic selection and its configuration/freeze contract remain future work. A requested level does not establish the native level actually used, or authorize a model switch, hidden downgrade or larger budget.

<a id="从空环境安装"></a>
## Install in a clean environment

The basic requirements are Linux, Git, Python 3.11+ and venv / pip. On Ubuntu 24.04, you can install the system prerequisites first:

This guide uses the `refactor/architecture-foundations` development branch, which includes the current composition and execution features. The clone command below selects that branch explicitly. In an existing clone, select the same branch, or pin the full commit from the acceptance record you need, before running the installer from that source. Do not treat `main` or an identical package version as proof of identical features or source identity.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv
git clone --branch refactor/architecture-foundations https://github.com/626619403/Ergora.git
cd Ergora
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
ergora serve
```

Open `http://127.0.0.1:8977` on the machine running the service. Web assets and graph components ship in the Python package; Node, a runtime CDN and a frontend build are not required. The installer places the application in `~/.local/share/ergora-app/venv` and the command in `~/.local/bin/ergora`. Runtime data defaults to the separate `~/.local/share/ergora/` directory; use `ERGORA_HOME` or the global `--home` option to select a persistent directory. Containers should persist these directories and the business repository.

If Python is already available, you can also install into your own environment:

```bash
python3 -m venv .venv
.venv/bin/pip install '.[web]'
.venv/bin/ergora serve
```

<a id="选择安装组合"></a>
### Choose an installation profile

The default profile is `control`. From the source directory, run `bash scripts/install.sh --profile development` or `--profile research`; on Windows, use `-Profile`, as described in the [Windows guide](WINDOWS.md).

|Profile|Installed SDKs|Additional setup|
|---|---|---|
|`control`|Web console|The selected Agent CLI and authentication; local projects can start with SQLite and manual operations|
|`development`|Web, Temporal|The complete six-stage flow requires the Linux/WSL2 reference runtime, services and Agents|
|`research`|Web, Temporal, GEPA|Evaluators, proposers and selected source/experiment services; install GPU tools for the task as needed|

After installation, run `ergora tools profiles` to view recipes from the same source; the local API is `GET /api/installation-profiles`. These descriptions are installation recipes. Check `ergora tools doctor PROJECT` and task acceptance separately for actual status. Installation profiles do not start services, log into models or run training. An installed SDK does not establish service connectivity, tool authentication or validated results.

The existing `--with-gepa` and `--with-temporal` options remain available and add dependencies to the selected profile as a set, for example `bash scripts/install.sh --profile development --with-gepa`. Rerun the installer in the same directory to upgrade or add packages; switching back to a smaller profile does not automatically uninstall SDKs. If a source feature has not been released, first switch to the feature branch supplied by the maintainer.

<a id="准备离线依赖"></a>
### Prepare offline dependencies

In a connected environment, prepare all build/runtime wheels for the target OS, Python version and architecture, then install in a matching environment. Run the following commands from the source directory; you may choose a different cache directory:

```bash
mkdir -p "$HOME/.local/share/ergora-tools/wheels"
python3 -m pip wheel --wheel-dir "$HOME/.local/share/ergora-tools/wheels" \
  '.[web,temporal,gepa]' setuptools wheel
PIP_NO_INDEX=1 PIP_FIND_LINKS="$HOME/.local/share/ergora-tools/wheels" \
  bash scripts/install.sh --profile research
```

The installer still uses pip to read the local source and cache. If a compatible wheel or build dependency is missing, pip fails visibly; complete the cache and retry. The offline cache does not include external Agents, reference-service binaries, system packages or models; prepare them separately according to their instructions. Windows also uses pip's `PIP_NO_INDEX`/`PIP_FIND_LINKS` environment variables and wheels built for Windows.

<a id="升级与持久数据"></a>
## Upgrades and persistent data

Before upgrading, stop the console, workers, executors and other CLI work, check in-flight task status, and back up the complete persistent directories and business repository. Opening an old control-plane database for the first time upgrades it transactionally and automatically saves a pre-upgrade database snapshot. That snapshot excludes Skills, sources and run files and cannot replace a complete backup. Newer databases reject writes from older applications; rollback requires restoring matching database and files as well as the code. See [Database upgrades](architecture/state-migrations.md) for specific versions, error handling and rollback steps.

If data already exists, stop the relevant work before running the following commands (see the [Windows guide](WINDOWS.md#升级备份与卸载) for PowerShell path examples):

```bash
ergora state info
ergora state backup "$HOME/ergora-backups/snapshot-001" --offline
ergora state verify-backup "$HOME/ergora-backups/snapshot-001"
```

The backup directory must be a new directory outside the data home. The tool saves a consistent database snapshot, regular files, file modes and empty directories, checks the domain identities of Skill/source snapshots, and returns a manifest SHA. It does not upgrade an old database first; `state info` also does not create a database when no data exists. `--offline` means that you have stopped writers; the tool does not stop services or external jobs for you.

Before restoring, move the existing home elsewhere to retain it, then run `ergora state restore BACKUP_DIRECTORY --offline`; for a custom home, use the global option in `ergora --home ORIGINAL_HOME state restore ...`. The first version requires the same platform and original home, and the target must not exist. It publishes the directory only after verification, copying and a second successful check, without overwriting an existing target. It preserves absolute paths and evidence digests in JSON. Restore and reconcile business repositories and external services separately; ReMe can rebuild its retrieval projection with `ergora memory sync PROJECT --rebuild`.

Installation and data versions are managed separately. The current database schema is 6; even if two applications both report 0.2.0, retain the full source commit, installation profile, interpreter and dependency versions. Keep a copy of both the application and data from before the upgrade: update the application by rerunning the original installer from the selected pinned source; for rollback, use a compatible old application and its corresponding complete state backup. If the new version has produced data, save that state separately first so the old snapshot is not the only copy. The complete application directory may contain interpreter links; a venv directory cannot simply be moved to a new path and reused.

<a id="换机与新项目重建"></a>
## Move to another machine or rebuild a new project

On the new machine, reinstall from the same branch or pinned commit and prepare Python, Git, Agent authentication and optional services for the selected platform. Use persistent locations for source, application, control home and business Git. Configure the installation locations with `ERGORA_INSTALL_ROOT`/`ERGORA_BIN_DIR`, and runtime data separately with `ERGORA_HOME` or the global `--home` option. If the new environment only needs the control plane, the complete reference stack is not required.

For a new project, follow the [template getting-started journey](TEMPLATE_WALKTHROUGHS.md) to register the actual repository path again, select backends, import the exact preset and prepare grants/a complete manifest. The same definition package can retain its version and content digest; the project revision, configuration containing absolute paths and invocation input belong to this new environment. Share the complete definition package and any exact dependencies it needs. Preview JSON downloaded from the page cannot replace the complete manifest. Supply credentials again through tool login or an external environment; configuration stores only variable names.

To continue a historical formal task, follow the [joint backup guide](BACKUP_RECOVERY.md) to restore the control home, external CONFIG/STATE, compatible application, Temporal database and business Git/worktrees on the same platform at their original absolute paths. Then check the original task/run, candidate, approvals and external jobs. `state backup` covers only the control home; creating a new project or running register again does not restore the original run identity. Acceptance of a local rollback with matching application/state also does not establish recovery of an active workflow across machines. Install Windows and WSL2 separately; do not share an SQLite database being written to or copy a venv between them.

After changing the service's control home, fully reload the page before reading the current project and original operation records. Existing page forms have no guarantee of continued use across a server restart; browser cache stores selections and cannot replace server-side intents and receipts.

<a id="安装与认证-agent-cli"></a>
## Install and authenticate Agent CLIs

The control-plane installer does not install model CLIs. Default roles invoke `codex` from PATH; selecting Claude Code invokes `claude`. On Linux, you can save the official installer first and then execute it:

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://chatgpt.com/codex/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/codex.sh"
sh "$HOME/.local/share/ergora-tools/installers/codex.sh"
export PATH="$HOME/.local/bin:$PATH"
codex --version
codex
```

During the first interactive `codex` session, choose account or API authentication. See the [official OpenAI installation instructions](https://learn.chatgpt.com/docs/codex/cli) and [authentication instructions](https://learn.chatgpt.com/docs/auth). Standalone role invocations use Codex's own configuration; configure the model for the formal reference executor separately according to the reference guide below.

Claude Code is optional. Install it according to the [official setup instructions](https://code.claude.com/docs/en/setup):

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://claude.ai/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
bash "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
export PATH="$HOME/.local/bin:$PATH"
claude --version
claude
```

Complete [Claude authentication](https://code.claude.com/docs/en/authentication) during the first interactive session. The standalone installers above do not require Node.js; if you use npm or another installation method, follow its official dependency requirements. Confirm that the commands are available in the same shell that starts Ergora, then run `ergora tools doctor PROJECT` and execute an explicit small task. Installation/version checks do not establish authentication or acceptance of a model task. See the [Agent guide](AGENT_BACKENDS.md) for the pinned-source installation, model and device requirements of mini-swe-agent and ForgeKernel.

<a id="首个项目与工具选择"></a>
## Your first project and tool choices

“New project” at the upper right of the page registers an existing Git repository; GitHub/GitLab is not required. Select each layer separately on the tool bindings page:

|Layer|Available implementations|Actual consumers|
|---|---|---|
|Inventory / planning / implementation / review and training proposal roles|Codex, Claude Code, custom protocol; implementation can also use mini-swe-agent|Standalone invocations and the optional six-stage bridge|
|Native kernel generation|Manual, ForgeKernel|Local native campaigns; independent trusted revalidation is separate|
|Memory|SQLite, ReMe HTTP|Save, revise, retrieve, synchronize|
|Skill optimization|Manual import, GEPA + JSON proposer|Bounded candidate search and evidence recording|
|Source material|Explicit URL|Bounded observation, snapshots and review|
|Research scheduling|Manual, Temporal Schedule|CLI worker / Schedule|
|Project issues|Local manual, GitHub, GitLab|Read sources through CLI/HTTP, freeze snapshots, explicitly comment on exported candidates; GitHub can add one existing candidate label by native ID|

Authenticate using each tool's login or environment variables. Configuration stores only credential variable names; do not enter secrets on the page. Select models separately for Codex and Claude Code; both implementation and review default to Codex. Custom commands receive prompts on stdin and start through argv, without shell concatenation. Installed, connected, authenticated and accepted through a task are distinct states.

<a id="读取项目工单上下文"></a>
### Read project issue context

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

The HTTP endpoint is `GET /api/projects/PROJECT/issues/7` and shares the CLI use case. The existing tool bindings page displays tracker configuration according to its schema. See [Reading on the page](#在页面读取与保存工单) for the issue page; observe lists continue according to the plan. Formally registered projects can read only their registered kind/namespace. Changing the source binding creates a new project revision without changing old tasks or reference registrations. Formal registration does not yet include the API host; later dispatch across hosts must have its identity approved separately and cannot directly reuse an old claim.

Only ordinary GitHub issues/GitLab project issues are accepted. GitHub PRs, GitLab non-issue types and incompatible responses are rejected explicitly. Each operation makes one GET with a 20-second socket I/O timeout and a 1 MiB complete-response limit, with no automatic retry. This is not a 20-second wall-time guarantee for the entire call. Authentication, unavailability, redirect, size-limit and truncation failures are not disguised as empty issues. See the [issue integration research](research/2026-11-11-project-trackers.md) for detailed interface tradeoffs and the unverified self-hosted scope.

<a id="保存工单与关联任务上下文"></a>
### Save issues and link task context

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

Snapshots and links are stored in the control plane's SQLite database and included in complete offline backup/restoration through the existing `state backup / verify-backup / restore` flow. The current database uses schema v6. Before upgrading, stop old processes and keep a backup of the old database; old clients cannot write to the new database. See [Expiry and upgrade notes](#记忆有效期与检索). Complete backups still require stopped writers, the same platform and the original home. Save external execution directories separately; context links cannot reconstruct tasks. Source dispatch is described next, candidate comments under [Writeback](#为已导出的候选发布工单评论), and source reading on the page in the next section. The remaining issue action pages are delivered in slices under the [F7 plan](plans/2026-11-11-project-trackers.md).

<a id="在页面读取与保存工单"></a>
### Read and save issues on the page

After selecting the current project's GitHub or GitLab source under “Tool bindings,” open “Issue sources,” enter an issue number/iid and click “Read current issue.” Reading the platform requires an explicit click; entering the page reads only the local snapshot list. The title, complete body, native ID, API source, project revision and response digest appear as text, and you can expand the complete record.

“Reread and save snapshot” reads the platform again and saves using the project revision currently held by the page. Platform content may have changed, so check the returned complete snapshot. Saving does not create or start a task, or send comments, labels or PRs/MRs. If the project revision changes, click “Refresh” at the top before operating. If saving is unconfirmed, use “Reread list” first to check; a failed response does not establish that nothing was saved.

History contains at most 20 entries per page. “Previous page/Next page” follows the original cursor, and “View snapshot” reads the complete snapshot offline. The list sorts by content digest; new content may appear on earlier pages, so reread the first page when needed. Historical snapshots retain their source at the time and remain readable if the project changes to another source or manual. They do not represent current platform content or the current tool binding. manual disables external issue reads. Bodies do not execute HTML/Markdown, and issue text cannot expand Agent permissions. “Prepare formal task from this snapshot” on a saved snapshot opens the existing formal task form; the page carries this project's digest temporarily. After refreshing, reenter from the snapshot or paste the SHA yourself. The source page itself handles reading only; use the CLI below for candidate actions.

<a id="从工单快照创建来源任务"></a>
### Create a source task from an issue snapshot

Page entry: view a saved snapshot in “Issue sources,” click “Prepare formal task from this snapshot,” then “Preview and create from selected snapshot.” You can also manually enter the optional source SHA under “Preview and create” in “Formal tasks.” Click “Read source snapshot” to read and check the complete body and source offline; the issue number is then fixed. After changing the digest, you must read it again; “Clear source selection” restores the entry without a source. A failed source read does not automatically fall back to a task without a source.

Select a registered development template and edit the complete input. Under “Agent source for this task,” choose “Complete manifest · composed execution and review.” Follow [Formal composition selection](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合) to verify the package, assign work units, choose each leaf's backend and select execution trust. The preview displays the source SHA and complete frozen files; review them and explicitly create the task. The server rechecks the current binding, registered source and project revision. Readable historical snapshots are not proof that creation is currently allowed. Preview and creation do not connect to the issue platform, start Agents or write back to issues; submit the run separately. If creation is unknown, read/recover under the original ID without recapturing or resending with a different ID.

To freeze the issue body for a new task, use `task-definition-v3`. It supports governance and major-change templates and requires explicit `work-units-v2` execution/review composition. First follow [Specialist executor configuration](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元) to prepare a complete `task-definition.json` containing the actual manifest, digest, work assignments and per-instance backends. Then save the snapshot and replace the project, number and revision in the following commands with current values:

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

Source tasks are admitted according to their frozen selections: checks cover only the actual inventory/plan roles, work/review leaf programs and configuration, the selected MCP mode, and the existing Git, timeout, Python and confirmed execution conditions in the current container. A2A, MLflow, LangGraph and unselected default implementer/reviewer roles are not required dependencies for this entry. Explicitly start `temporal worker executor` first, then start according to [Formal submission](#提交正式任务与恢复未知结果). Trusted checks, policy, Temporal connectivity and shared issue claims retain the existing flow. Program availability does not establish authentication, quota or worker readiness; an actual failure retains the specific dependency and original submission status. Unknown recovery only queries the original ID without resending or repeating admission due to current tool changes. Old v1–v6 retain the original installation-level doctor.

Install this version and restart its worker/executor before accepting the v7 queue; check original invocation materials and receipts for actual Agent consumption. Existing limits remain: 1 MiB per file, 1,000,000 bytes each for stage/prompt, and limits on all ancestor materials and dynamic artifacts. Static content certain to exceed limits is rejected at preview; later artifacts exceeding limits are rejected in their original stage, with no implicit summary. v7 evidence/handoff retains the complete `contract.original_input` and checks the source/original admission SHA; the combined total remains subject to the original 1 MiB index and package-manifest limits. Old v1–v6 and old handoff packages are not migrated.

<a id="为已导出的候选发布工单评论"></a>
### Post an issue comment for an exported candidate

After a source task reaches `REVIEW_READY`, follow [Candidate export](#导出精确候选与恢复回执) to export the exact run and candidate first. Then read the current project revision and prepare a fixed, neutral comment. The tracker binding must contain an external `token_env`; its account must be able to read `/user` and the target issue and create a GitHub issue comment or GitLab issue note. Put credential values only in the environment that starts the CLI/Web service. No new SDK is required.

```bash
ergora project show PROJECT
ergora issue writeback-prepare PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA
# Check the complete returned intent: source, actor_id, original task/run/candidate/export, body and intent_sha256.
ergora issue writeback-send PROJECT INTENT_SHA --revision REVISION --confirm
ergora issue writeback-status PROJECT INTENT_SHA
```

prepare only reads identities and saves locally; it does not post a comment. send posts only the saved body and cannot rewrite it at send time. The fixed body includes the candidate and local export branch, does not copy issue instructions, and does not claim a remote branch or merge is complete. A source/task/run/candidate operation has only one intent. Preparing again returns the original record; a new request ID cannot bypass it. After unrelated Agent configuration revisions, you may use the current revision, but the original tracker binding, source and export identity must remain unchanged. Changes to the binding or sending account reject unsent intents. If the project revision changes during sending, the final confirmation cannot be saved and the original attempt remains unknown; sending again with a new revision does not resend it.

`acknowledged` means the body, author and native target in the complete 201 response to the single POST were checked and the result was saved successfully. send returns exit code 0 only in this state; HTTP callers must also check the business status. `prepared` means no attempt has been saved yet. The attempt is committed before POST. Any subsequent lost/incomplete response or interruption leaves `unknown`, including the interruption window in which nothing may yet have been sent; another send does not resend it. status reads locally and does not access the tracker.

If the remote result is unknown, explicitly observe a current comment or one list page:

```bash
ergora issue writeback-observe PROJECT INTENT_SHA --comment-id COMMENT_ID
ergora issue writeback-observe PROJECT INTENT_SHA --page 1
```

Each list page contains at most 100 entries. Continue manually using the returned `next_page`, at most one page per call. Matching the marker, complete body and author establishes only currently visible facts. Copying, editing, deletion or an empty page cannot prove that the original request succeeded or was never sent. Observation does not promote unknown to acknowledged, alter old receipts or open a retry slot. If manual handling is needed, check remote facts first and retain the original unknown record; do not create another task to disguise a retry of the same request.

CLI and HTTP share the same use cases. POST retains Origin and `X-Ergora-Request: 1` protection:

|Operation|HTTP endpoint/body|
|---|---|
|Prepare|`POST /api/projects/PROJECT/issue-writebacks`, `{"revision":2,"task_id":"TASK","run_id":"RUN_ID","candidate_sha":"…"}`|
|Offline status|`GET /api/projects/PROJECT/issue-writebacks/INTENT_SHA`|
|Send|`POST .../issue-writebacks/INTENT_SHA/send`, `{"revision":2,"confirm":true}`|
|Observe|`POST .../issue-writebacks/INTENT_SHA/observe`, `{"comment_id":"71"}` or `{"page":1}`|

Each HTTP request has a 20-second socket I/O timeout and a 1 MiB complete-response limit, with no redirects or automatic write retry. prepare and send also each read actor and target identities, so the total operation may exceed 20 seconds. GitLab supports ordinary issue notes; successful responses must explicitly contain boolean `system` and `internal` fields, and incompatible responses leave unknown. Validate compatibility with actual service versions/proxies in your own test project. Intents, attempts, receipts and observations are included in the existing control-plane offline backup; save formal task and export directories separately. This entry creates only one neutral comment. GitHub labels are covered next; PR/MR and dedicated issue pages are delivered in later slices.

<a id="为已导出的候选追加-github-标签"></a>
### Add a GitHub label for an exported candidate

After the same original v7 source task is exported, you can separately prepare one label that already exists in the repository. First create a suitable ordinary label, such as `candidate-exported`, in your own GitHub project, and give the tracker's external `token_env` account the corresponding read/label-write permissions. Preparation only reads and saves; it sends no mutation. The presence of credentials or a readable actor does not establish label-write permission.

```bash
ergora issue writeback-label-prepare PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --label-name candidate-exported
# Check the returned label_name, native_target, complete operation and intent_sha256, then confirm this digest.
ergora issue writeback-send PROJECT INTENT_SHA --revision REVISION --confirm
ergora issue writeback-status PROJECT INTENT_SHA
ergora issue writeback-observe PROJECT INTENT_SHA
# For the next page, explicitly use the preceding page_info.end_cursor; fetch only one page at a time.
ergora issue writeback-observe PROJECT INTENT_SHA --cursor OPAQUE_CURSOR
```

The original REST reads map the frozen issue number/native ID, repository and label to GraphQL IDs returned by the service. Sending includes only one `labelIds` and the original `labelableId`: it does not write by name, create a label, send the complete label set, or remove/replace other labels. Names containing spaces, commas, quotation marks or Unicode are saved unchanged without splitting or normalization. GitHub.com uses same-origin `/graphql`; Enterprise REST `/api/v3` maps to same-origin `/api/graphql`. Unknown paths or incompatible schemas/permissions fail visibly without falling back to name-based REST writes. This path derivation does not establish testing of arbitrary Enterprise versions.

Each source/creation/run/exported candidate has only one label-addition slot. The operand is frozen at first preparation. Preparing the same name again returns the original intent; changing the name is rejected and cannot bypass an existing attempt. Label and comment actions each have their own original intent and share the same persistent lifecycle. Before sending, recheck the original task/export, current actor, binding and native target. Rename, deletion/recreation or binding changes reject unsent intents. For unrelated Agent revisions, you may provide the current revision; saving the result still checks the same original attempt and current expected revision. Preflight is not server-side CAS; target metadata may change after reading.

`acknowledged` requires the complete original 200 response to the single mutation, no GraphQL errors, matching echoed values and original Issue/repository, **the one page selected in the original response actually containing the original label ID, name and owning repository**, and a saved result. `clientMutationId` checks only the echo; it is not a server-side idempotency key. If the target is absent from the first 100 entries, data is nullable/partial, data and errors coexist, the response is lost/truncated or saving the result fails, the state remains `unknown`. Once an attempt is saved, it is not resent. A target match in the original response can confirm it without paging through other labels; it does not establish that this operation added the label for the first time.

observe uses a read-only GraphQL query to read one page of the current original Issue. `membership_in_page` describes only `present` or `not_seen` on that page; not seeing a label does not establish its absence. Even a unique current match, manual removal or an empty query page neither confirms nor resends the original attempt. `--comment-id` and nondefault `--page` apply to comments, not labels; label pagination uses an opaque cursor.

The HTTP preparation endpoint is `POST /api/projects/PROJECT/issue-label-writebacks`. Its body contains comment prepare's `revision/task_id/run_id/candidate_sha` plus `label_name`. status/send/observe use the shared `issue-writebacks/INTENT_SHA` endpoints from the preceding section; label observe takes `{}` or `{"cursor":"…"}`. Same-origin and `X-Ergora-Request: 1` requirements still apply. Label prepare and the first send each read the actor plus the issue/repository/label. After the first send's reads, there is at most one mutation. status is offline; observe reads the actor and makes one query, with no background scan. Each request retains the 1 MiB complete-response limit and 20-second socket I/O timeout; the total wall time is not guaranteed to be 20 seconds.

GitLab label actions are explicitly unsupported at present; ordinary issue comments are available. Without a complete target-deployment/response contract and concurrency guarantees for scoped rename, the tool does not automatically substitute `add_labels`. Label operations may trigger platform events, notifications and external automation; silence is not guaranteed. Labels grant no approval authority and do not establish remote publication, merging or issue completion. Validate actual service versions and account write permissions in your own test project; default acceptance uses loopback fixtures only.

<a id="在页面准备发送与观察工单回写"></a>
### Prepare, send and observe issue writebacks on the page

Open “Formal tasks” and select “Prepare issue writeback” in the export record of the original v7 source task. Choose a neutral comment or one existing GitHub label, then click “Confirm preparation of local writeback intent.” The page fixes the original task/run/candidate and current revision, and locks the action and fields after preparation. Label names are saved unchanged. This step only reads identities and saves a local intent; it does not post an issue action. If the preparation response is lost, explicitly use “Recover original preparation request.” An existing slot returns the original intent; without a record, this may perform the first read/save. Do not use another label or task to bypass the original slot.

Check the returned intent SHA, target issue, account, candidate and complete fixed comment or native label request. Only `prepared` displays a separate send confirmation; check the verification box before confirming a comment or label addition to the original issue. Sending uses the project revision displayed on the page. If it is stale, refresh the project and reread by the original SHA without changing the intent. An HTTP success still requires checking business status. `unknown` offers no resend; `acknowledged` means only that the original receipt was checked and saved. If the send response fails, use “Read original intent status offline” first; closing the dialog does not cancel the operation.

“Read issue writeback by SHA” at the top of “Formal tasks” does not require a registered project or readable original task files. Enter the original intent SHA to read only this project's saved intent/attempt/result and latest observation, without an online platform, token or unchanged current tracker binding. Reading does not send or observe automatically. Sending/observing still requires the actual dependencies checked by the original owner. Returning an existing record from preparation guarantees neither that this invocation performed no identity reads nor that the latest observation is included.

In the retrieved record, explicitly choose the observation scope: one native comment ID or one comment list page, or one opaque label cursor (blank for the first page). Each call reads only one resource/page and saves the current observation; the complete result retains `next_page` or `page_info.end_cursor` for manual continuation. Matches, empty pages, deletion and label presence do not confirm the original attempt, promote `unknown` or open retries. Editing query conditions marks the old observation as stale and removes the original send confirmation. Explicitly observe or reread offline, then check the newly returned complete record. After editing the SHA, closing/replacing the dialog or switching task/run/project/view, late responses cannot restore the old send entry. All bodies and original records are displayed as safe text.

<a id="核对候选与当前远端分支"></a>
### Check the candidate and current remote branches

After exporting the original v7 source task, you can read the current head and base branches in the original source repository. The head name is fixed to the original export branch; specify base explicitly. The tool does not infer the original task baseline from the current default branch.

```bash
ergora issue candidate-observe PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --base-branch main
```

The output lists the original export receipt, current local ref/complete candidate and base commits, and the remote repository's native ID and two exact refs separately. Under `comparisons`, `local_export_ref_matches_candidate`, `head_matches_candidate` and `base_matches_task_base` represent these three comparisons. If the current local branch has moved or remote base has advanced, the original receipt and frozen base remain unchanged and the comparison returns false. If the local branch was deleted, its local comparison is null. If a remote ref returns 404, its comparison is null and `resolution` is `not_found_or_not_visible`. A 404 cannot distinguish nonexistence from lack of visibility and cannot authorize automatic creation.

Local Git reads use the original Linux/WSL2 formal execution environment. This entry requires Git 2.43 or newer and enforces `GIT_NO_LAZY_FETCH=1` and `GIT_NO_REPLACE_OBJECTS=1`; unknown/older versions are rejected explicitly. The original task, submission, export record and original candidate/base commit objects must still exist; replacement objects from `refs/replace` cannot pass the checks. Reading does not require Temporal online. Missing promisor objects fail directly without implicitly fetching objects, updating refs or releasing claims. These read-only options do not affect the original explicit export fetch. GitHub reads the repository and exact refs through singular `git/ref/heads/...`; GitLab reads the project's native ID first, then two branches by numeric ID, fully encoding branch names containing slashes. All three platform requests are GETs, without redirects or retries, each with a 1 MiB complete-response limit and 20-second socket I/O timeout. The combined wall time of three reads and local operations is not guaranteed to be 20 seconds. Changes to the original source binding are rejected; unrelated Agent settings can use the current revision. If the project revision changes during reading, the operation refuses to return results for the old selection. Observations are not persisted.

These are current facts obtained separately. They cannot detect ABA between reads or prove who pushed, whether an original attempt succeeded, or whether head/base were unchanged at execution time. The repository native ID is the identity read now under the original source namespace; the original issue snapshot did not freeze the repository native ID at creation. This observation cannot rule out history such as namespace deletion and reuse. The target is not changed based on local origin or a returned URL. Repository responses retain only necessary allowlisted fields and do not return temporary clone tokens.

The HTTP endpoint for the same query is `POST /api/projects/PROJECT/candidate-observations`, with body `revision/task_id/run_id/candidate_sha/base_branch`; same-origin and `X-Ergora-Request: 1` are still required. POST is a local query entry here; the provider receives only GETs. The command does not push branches, create/link PRs/MRs, write comments/labels, approve or merge. `execution_authorized` and `proves_original_attempt` are always false. After confirming equal current content, follow your project's publication and human review process.

In the console, select the original formal task and click “Check original export record and recover.” If an original v7 source task's record is `exported`, you can open “Observe current candidate branches.” The page fixes the original task/run/candidate/export branch and this project's current revision. Enter “Remote target branch (base)” and click “Explicitly query current branches” to invoke the query above; opening and editing do not access the platform. Results display original targets, current reads, three-state comparisons and each remote response's time/digest separately. Expand complete JSON as safe text.

Changing the target branch immediately invalidates the old observation. An old in-flight response cannot overwrite a new selection, a closed/reopened dialog or another project/task. Failures display the current error clearly. Querying again requires an explicit click; there is no polling or automatic retry. Reading does not require Temporal online, but still needs the original execution environment/Git and source credentials described above. Historical exports remain unchanged. Existing PR/MR links and comments/labels continue through their respective CLI entries.

<a id="关联已有-prmr-与候选"></a>
### Link an existing PR/MR to the candidate

After creating a PR/MR on your own project platform, you can link its explicit repository PR number/project MR iid to the complete exported candidate of the original v7 task. The first link requires the original local export ref, remote head ref and review head still to point to that candidate. The head name must be the original export branch, and the base name must be explicitly provided. Only the same source repository/project is supported; forks, other repositories, search-based guesses and arbitrary URLs are unsupported. The Linux/WSL2 Git checks from the preceding section apply, without requiring Temporal online.

```bash
ergora issue review-link PROJECT TASK --revision REVISION --run-id RUN_ID --candidate-sha CANDIDATE_SHA --base-branch main --review-number 11 --reason '此资源用于审查原候选'
ergora issue review-link-show PROJECT SAVED_SHA256
```

The first returned `record` contains immutable `sha256` and `scope_sha256`, complete source/task/run/candidate/export identities, current repository and review native IDs, complete title/body, author/state/draft, and each read's digest and time. It saves `operator_asserted_review_context`, with `context_only=true`, `execution_authorized=false` and `proves_original_attempt=false`. It neither confirms original comment/label attempts, clears unknown, grants approval nor proves Ergora created the resource. The original issue native ID must also match the source snapshot. The original snapshot did not freeze the historical repository ID, so not all cases of namespace reuse can be excluded.

The original task base, current remote base tip and PR response's `base.sha` are retained separately. Saving is allowed if current base has advanced; `base_matches_task_base=false` does not rewrite the original baseline. GitLab's `diff_refs` may be null or empty, indicating that version information is not ready. A nonempty `base_sha` is the merge-base and `start_sha` is the target commit of that diff version; neither is the current target tip. `diff_version_head_matches_candidate` is projected separately as true/false/null without overriding the MR's `sha`. state/draft are saved as observed; closed or merged resources must still meet the current-ref requirements above.

An original candidate slot can save only one review. Calling again with the same target/base returns the original `record`, `already_saved=true` and `fresh_observations=false`, ignoring a new reason; when the entry finds the original record, it does not reread the platform. If two first requests run concurrently, the later saver may already have read the platform, but ultimately returns the original record saved first. `fresh_observations=false` describes only the returned material and cannot prove no read occurred in this invocation. A different number or base conflicts explicitly and cannot overwrite the record. `review-link-show` needs only the saved control-plane record and works offline without a token, original task files, Git or a still-visible platform. This record is included in schema v4 backups; load and backup check the same identity contract. External execution directories still need separate backups.

The HTTP save endpoint is `POST /api/projects/PROJECT/candidate-review-links`, with body `revision/task_id/run_id/candidate_sha/base_branch/review_number/reason`, protected by same-origin checks and `X-Ergora-Request: 1`. Offline reading uses `GET /api/projects/PROJECT/candidate-review-links/SAVED_SHA256`. A normal first link makes five bounded GETs to the provider without holding an SQLite write lock. Each has a 1 MiB complete-response limit, 20-second socket I/O timeout and no redirects/retries. The complete canonical link also has a separate 1 MiB limit; oversized content is rejected without truncation. Total wall time is not guaranteed to be 20 seconds. The reads form neither a shared snapshot nor CAS and cannot detect ABA; provider GETs may compute internal derived objects. Saving locally requests no platform business mutation and does not push or create/edit/merge PRs/MRs. The source page can read and save complete issues; candidate action pages continue under the [F7 plan](plans/2026-11-11-project-trackers.md).

In the console, open “Link existing PR/MR” through “Check original export record and recover” on the original v7 exported task. Explicitly enter the base, PR number/MR iid and reason, then “Confirm saving existing PR/MR link.” The fields are fixed on first send. If the response fails, retain the original request and click “Recover original link request.” This is more than a read-only status operation: it returns an existing original record, but if none exists it may reread the platform and save the local record for the first time. There is no automatic retry. To change an initial selection, close and fill in the form again; the backend still rejects overwriting an original candidate slot that already holds another target.

Retain the record SHA after saving. “Read PR/MR link by SHA” at the top of the formal task page reads directly offline even if the original task directory is unreadable, the project is not yet registered or the current tracker has changed bindings; it reads only this project's records. You can also read back by SHA at the bottom of the link dialog. The body and complete JSON are displayed as safe text, with each base/diff fact retained separately. Editing the SHA, closing/reopening or switching project/view invalidates old responses. The original record and its then-current already_saved/fresh_observations do not represent current remote state.

<a id="诊断与修复"></a>
### Diagnose and repair

`ergora tools doctor PROJECT` uses effective bindings to show installation, version, authentication, connectivity, task prerequisites and repair guidance, with the project revision and configuration digest. By default, it checks local installation only, without connecting to external services or calling models. `ergora tools doctor PROJECT --probe --timeout 5` actively checks native CLI versions, Codex credential status and ReMe/Temporal TCP reachability. `--timeout` is a shared 1–30 second budget for all active probes; local installation checks and process cleanup are counted separately. The tool bindings page provides the same active probe entry. Its API is `POST /api/projects/PROJECT/doctor`, with body `{"timeout":5}` and the existing local write-request header `X-Ergora-Request: 1`.

`credentials_present` means only that credentials exist in the CLI/environment; it does not establish account, quota or model availability. `tcp_reachable` establishes only transport reachability, not service protocol, authorization, namespace or worker readiness. `not_checked`, `not_confirmed`, timeouts and exhausted budgets cannot count as passing. doctor does not execute custom commands. Claude/mini/GEPA/Forge authentication and real tasks still need explicit acceptance according to the repair guidance; the Forge version must match the pinned commit. `task_availability: available` means only that local prerequisites such as SQLite/manual operations are available, rather than formal six-stage acceptance. Raw probe output is neither returned nor persisted; only version numbers or status are returned.

<a id="正式任务的操作顺序与恢复"></a>
### Formal task sequence and recovery

For first use, follow the [complete README journey](../README.md#首个开发任务) and [Project definitions](PROJECTS.md) to prepare a real Git baseline, trusted checks and authenticated roles, then use the sequence below. Formal development requires the registered complete Linux/WSL2 executor. A workflow draft on the page is not yet a created formal task.

```text
project register → select roles/check revision → services start for the selected stack
→ task preview → review digest → task create → task start
→ inventory/plan → status pinned to original run → review actual plan → approve exact plan
→ work/integrate/verify/review → original outcome
→ REVIEW_READY: review exact candidate/checks/review → export local branch and check lease receipt → independent revalidation/human merge
   Defer export: external-status → explicit reconcile (original result/candidate retained)
→ Blocked or canceled: confirm original run is closed → external-status → explicit reconcile → recover using original intent
```

The formal task page also supports [selecting a saved complete composition](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合): replace only review, or choose execution and review subflows and assign specialist instances and per-leaf backends to each work unit. First read the complete package matching the original preview digest, then preview and explicitly create. Users explicitly choose writable trust and cross-backend policies; failures display the original owner's error.

Retain the task ID, creation/submission intent SHA and original workflow/run IDs. All write commands use the current project revision. Approval also requires a stable decision ID and exact plan SHA; cancellation requires a stable request ID. HTTP 200, CLI 0 or requested is a receipt for the corresponding operation. The original outcome and candidate evidence determine whether the six stages passed. After closing the page or ending the CLI process, continue queries with the same `--home` and registered execution directory. Do not reuse task IDs to bypass old records.

|Interruption point|Read first|Allowed next step|
|---|---|---|
|Task contract publication|`task creation PROJECT TASK`|Run resume-create with the original intent SHA; check conflicting files first|
|Unknown submission result|`task submission PROJECT TASK`|resume-start checks the original spec/memo/run; unknown permits queries only, without resubmission|
|Unknown approval/cancellation delivery|`task approval PROJECT TASK DECISION` / `task cancellation PROJECT TASK REQUEST`|resume-approve/resume-cancel checks the original operation SHA and history; without a matching signal, it remains unknown|
|Closed but externally unconfirmed|`task status --run-id` and `task external-status --run-id`|Retain original result/requests/receipts/artifacts/fence; explicitly reconcile, then resume-reconcile if incomplete|
|Interrupted candidate export|`task export-status PROJECT TASK`|resume-export checks the original result and actual ref; unknown does not refetch or revive deleted branches|

A joint backup must retain the control `ERGORA_HOME`, registered CONFIG/STATE, business Git repositories, Temporal persistent data and actual tool authentication. A control SQLite backup excludes original tasks/history/candidates/leases. `tasks/`, `ergora/task-*`, requests/receipts/artifacts/approvals/fences, workspaces, process records and ledger in execution STATE are all recovery evidence. Stop the relevant writers and check in-flight external jobs first, then follow the [backup instructions](#升级与持久数据). See the [Joint backup and recovery guide](BACKUP_RECOVERY.md) for complete offline steps on the same platform at original paths, and checks before starting.

<a id="服务停止后的读取与恢复"></a>
### Read and recover after services stop

Once unified registration and installation of the complete execution environment are finished, assess running services and existing persistent receipts separately. Complete formal execution uses Linux/WSL2. See the [Windows guide](WINDOWS.md#选择运行方式) for the scope of the Windows control plane and optional tools.

|What to read or execute|Services that must be running|Factual boundary|
|---|---|---|
|Original contract and creation/submission/approval/cancellation/reconciliation/export records|No execution services required|Reads persistent files; historical receipts do not establish current Git branches, external processes or live run status|
|Closed original run's status/result, original events and job receipts/text materials|Temporal; no worker/executor required|Pins the original run and evidence digests; event/job reads also apply to a running original run, while materials additionally require a readable original trusted artifact directory|
|Evidence index, budget facts and handoff collection for a closed run|Temporal, registered complete Linux/WSL2 runtime and original materials; no worker/executor required|The original run must be closed without a successor; checks materials against original contracts/receipts; connection failure does not return a partial index or handoff package presented as complete|
|`handoff verify` for a saved handoff package|No online service, control database or Temporal SDK required|Basic Windows/Linux installations can verify package bytes and declared identities offline; source authentication, complete history and candidate revalidation require separate checks|
|Stage/status queries for a running original run|Temporal and a worker able to answer workflow queries|`task status` uses a workflow query when RUNNING; a query may fail with only Temporal online|
|Continue formal stages and real Agent calls|Temporal, corresponding worker/executor and authentication for selected tools|Check delivery receipts and actual completion separately; starting services does not automatically resend unknown operations|
|Explicit service start/exit and logs|Complete Linux/WSL2 reference installation and Supervisor|The unified entry manages the stack belonging to this execution directory; projects sharing a directory share services|

After closing the browser or restarting HTTP, select the original project/task again and read the original records to recover. Clearing session selections does not delete backend intents. Run input can be refilled from persistent submission; retain the original decision/request IDs for approval/cancellation. If the original run service is unreachable, the page explicitly shows query failure; local receipts remain independently readable. Do not treat connection failure as an unsubmitted task or rerun with a different task ID. To inspect an existing closed run, explicitly start only Temporal. Before resuming execution, separately check the required worker, executor, tools and original intent status. See [Explicit service management](#显式服务管理) for the steps.

<a id="旧参考-cli-与统一入口"></a>
### Legacy reference CLI and unified entry

The unified `ergora task` reads Temporal configuration from the registered reference environment; legacy `agentflow task` reads its connection from the current shell. For a loopback development service on the local machine, explicitly set the following for legacy commands:

```bash
export TEMPORAL_ADDRESS=127.0.0.1:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_LOCAL_DEV=1
```

LOCAL_DEV applies only to loopback development services; connect to other services with their own authentication configuration. Task ownership differs between the two entries. Legacy tasks retain their original configuration/STATE and CLI and cannot be implicitly taken over through unified commands. Supervisor management also distinguishes execution states; stopping the current shared stack affects all its projects.

<a id="正式任务页面"></a>
### Formal task page

After selecting a project registered through the unified entry point, open “Formal tasks” from the left sidebar or “View formal tasks” from the project overview. The list uses bounded cursor pagination; a page with no matches may still have a next page. Unreadable records and invalid contracts appear separately. Task details show the task's own frozen input, role snapshot, work units and local submission receipt. They do not fill in history from the current project bindings or treat an existing contract or submitted state as successful execution.

“Native run” defaults to the original run ID from the saved selection or submission receipt. It connects to the registered Temporal instance only after you click “Read original run.” The result preserves original facts such as REVIEW_READY, BLOCKED, CANCEL_UNCONFIRMED and NEEDS_RECONCILIATION; not_found and query failures appear separately. After you switch tasks/projects, edit the run ID or leave the page, an old response cannot overwrite the current selection. Refreshing or returning to the console in the same browser tab preserves the project, page, task and run selections, while execution status is queried again. Retention after closing the tab depends on the browser's own session recovery.

Click “Preview and create,” select a development template registered for the project, and load the template input or a compatible saved draft. Enter a new task ID, issue number or local identifier, and edit the complete input JSON. You can specify a starting commit; leave it blank to use the registered baseline. The server preview shows the revision, frozen roles, complete files and digests. Changing any field or source immediately invalidates the previous confirmation. After reviewing, click “Confirm creation of frozen contract.” This publishes the contract without automatically submitting a run. Training optimization continues to use its separate entry point.

Before sending a creation request, the browser saves the original task ID as the project's task selection. If the response fails or is lost, the form locks; first use “Read creation record by original ID.” You can also query by ID at the top of the page at any time. If the contract has not been fully published after a reload, the details error still retains the original ID and query entry point. `pending` shows the original intent digest and frozen revision; explicitly confirming recovery publishes the original content. Later project binding changes do not replace the old roles. `published` shows that the frozen contract has been published, `not_recorded` does not take over old tasks, and `conflict` preserves conflicting files without offering an overwrite button. The page does not automatically resend creation, change the ID or start execution.

“Check submission and recovery” in task details rereads the creation and local submission records. If publication is complete and no submission record exists, you can review the frozen contract, roles, current revision and digest, then select “Confirm submission of this frozen task.” `prepared` or `unknown` offers only explicit recovery of the original intent. The backend decides whether to continue a submission that has not been dispatched or query a dispatch whose result is already uncertain. `not_found` remains unknown; the page does not resend start. An ownership `rejected` state provides no override entry point. If the response fails, reread the original record first; this does not justify changing the ID. `submitted` saves the original run selection. Click “View original task and run,” then read the run status separately; a submission receipt does not mean the six stages are complete.

When the original run query returns `AWAITING_PLAN_APPROVAL`, click “Review plan and approve” to read the complete execution-plan, ownership-map and rollback-plan, together with the exact receipt identity. No approval entry point is available if material reading fails. After reviewing, enter a stable “Decision ID (for recovery),” such as `owner-one`, and first select “Read approval record.” “Confirm approval of this plan” is offered only if that ID has no record. Confirmation binds the run/plan SHA of these materials, and the server checks the current state again. Keep this ID; do not use a new ID to bypass unknown delivery.

Task details also provide “Check approval record by original ID,” which does not require the task to still be awaiting a plan. The browser retains the latest decision selection per project/task. If the selection is cleared or you change devices, entering the original ID manually still retrieves the backend record. `prepared` allows “Confirm recovery of original approval intent”; `unknown` allows only “Confirm reconciliation of original approval signal”; `requested` displays delivery facts and offers no further delivery button. If the current materials workspace finds an existing decision, inspect its original record separately; current materials do not overwrite the old decision. If the response fails, reread the original record first. Reloading does not automatically approve anything. Return to the original task and select “Read original run” again to check actual acceptance and execution progress.

While the original run is still running, click “Request cancellation of this run,” enter a stable “Cancellation request ID (for recovery),” and first select “Read cancellation record.” A reason field and “Confirm cancellation request for this run” are offered only if that ID has no record. The server fixes the original run and checks its state again. Task details also provide “Check cancellation record by original ID”: `prepared` explicitly recovers the original cancellation intent, `unknown` only reconciles the original signal, and `requested`/`already_closed` offers no redelivery. Current edits cannot overwrite the original reason or intent. `already_closed` means the original run was closed before sending and no new signal was sent.

Keep the original cancellation request ID. After a lost response, read the original record first. If the browser selection has been cleared, enter the original ID manually to resume querying. Cancellation is a cooperative request; `requested` does not confirm a stop. Return to the original task and select “Read original run” again to check the phase and terminal state. Reconcile external job cleanup and lease release separately.

Once the original run is closed, click “External evidence and reconciliation” for a read-only view of that run's jobs, request/receipt/artifact verification results, fence and original outcome. Reading does not change the execution fence or lease. Even if some jobs already have terminal states, check `external_confirmed`; workflow closure or cancellation delivery does not establish completed cleanup.

Read the original reconciliation record in the same workspace. “Confirm external reconciliation and release original lease” is offered only when the current external evidence read succeeds and the record is `not_recorded`. The operation rechecks the original run, creates or reuses the same fence, and releases the original claim after all external jobs are confirmed. Task details also provide “Check original reconciliation record and recovery,” which reads only local persistent records. `prepared/unknown/confirmed` allows “Confirm recovery of original reconciliation intent,” binding the original intent SHA without replacing it with the currently edited run. `confirmed` has not yet saved a lease-release receipt; only `reconciled` means that the original lease release and receipt have been saved. The latter offers no further write operation.

After a lost response, reload or reselect the original task, then read its original reconciliation record. No new reconciliation ID is needed. Live external evidence and historical reconciliation receipts are read separately. The original `CANCEL_UNCONFIRMED` outcome remains; completed cleanup does not mean development succeeded. Failed external evidence reading prevents a new reconciliation, but an already saved original intent can still be inspected separately and explicitly recovered.

When the original run is closed with a `REVIEW_READY` outcome, click “Export exact candidate.” The page fixes the original run/full candidate SHA for this operation and first reads the original export record. Only `not_recorded` offers a target local branch field and “Confirm export of this candidate to a local branch.” Server-side Git/original-outcome checks decide whether the branch is valid and the original candidate can be exported. The page does not replace existing branches, checkout, merge or push.

Task details also provide “Check original export record and recovery,” which reads only local records without querying Temporal or current Git refs. `prepared` allows “Confirm recovery of original export intent” and may create the saved target for the first time. `unknown` allows “Confirm reconciliation of original export branch” and only checks the original branch; `branch_not_found` remains unknown and does not recreate it. Recovery binds the original intent SHA; repo/run/candidate/branch cannot change. `exported` displays only the historical receipt and original lease-release facts. It does not prove that the current ref is still correct, that development succeeded or that the change was merged. After a lost response, reselect the original task and read the same record without resending the export. Maintainers must still recheck the actual branch and evidence before adoption.

Projects not registered through the unified entry point show registration guidance. Local contracts remain viewable when the service is unavailable. Closing a dialog or page does not revoke an operation already sent, and closing the page does not cancel external tasks. A terminal state does not mean external job cleanup has been confirmed. The browser saves only selections; creation/execution facts are read from the server each time.

<a id="读取正式任务合同"></a>
### Read formal task contracts

First complete [unified project registration](PROJECTS.md). You can read existing development tasks in the execution directory directly from the main entry point:

```bash
ergora task list my-project --limit 50
ergora task show my-project TASK_ID
```

The same-origin APIs are `GET /api/projects/ID/tasks?limit=50&after=CURSOR` and `GET /api/projects/ID/tasks/TASK_ID`. Each page validates 50 candidate directory entries by default, configurable from 1–100. Pass the returned opaque ASCII cursor `next_after` unchanged to continue until it is null; the cursor is neither a task ID nor a file path. Each page streams all directory names before selecting its candidate window, so enumeration time grows with the number of tasks. `inspected_entries` counts only the entries validated on that page. Other projects or damaged directories may produce empty pages; continue following the cursor. `items` contains only tasks matching the project/Git root/tracker and passing contract structure and digest checks. Entries with confirmed ownership but damaged contracts go into `errors`; entries whose ownership cannot be determined are counted only in `unreadable_count`.

Details return the original spec, frozen project, optional `agent_bindings` and their file SHA256 values. `project_revision` is the current control-project revision; `project_revision` in frozen bindings belongs to the snapshot taken at creation or first execution. `runtime_status: not_queried` means Temporal was not accessed. Existing local files do not mean a task has started, completed or passed acceptance. Contract queries do not install the SDK, start services, submit tasks or write back to old records. Tasks created/submitted through the unified entry point use the explicit approval, cancellation and export entry points below. Tasks from the old entry point continue to be managed according to the [formal execution guide](AGENT_BACKENDS.md). Linux and Windows can both read locally accessible execution directories; full six-stage execution requires Linux/WSL2.

<a id="预览与创建正式任务"></a>
### Preview and create formal tasks

Projects registered through the unified entry point can compile and save both development templates with a base installation, without Temporal/Web SDKs. First save `task-definition.json`. `input` uses the template's original input format; the original compiler still validates its fields and DAG:

```json
{
  "schema_version": 1,
  "task_id": "example-change",
  "task_type": "repository-governance",
  "issue_id": "1",
  "input": {
    "goal": "检查并整理 src 内的模块边界",
    "allowed_paths": ["src"],
    "acceptance": ["保持已有行为和可信检查"],
    "constraints": [],
    "risk": "standard",
    "work_units": [{"id": "inspect", "depends_on": [], "paths": ["src"], "instructions": "完成边界整理"}]
  }
}
```

Choose `repository-governance` or `large-change`; the template must already be registered for the project. For large development tasks, set the risk and input according to the original template. The optional `starting_sha` is a 40-character lowercase Git commit SHA and defaults to the registered baseline. Replace the revision below with the current value from `project show`:

```bash
ergora task preview my-project --definition task-definition.json --revision 1
# Review the complete spec, trusted policy, frozen project and agent-bindings returned in files.
# Replace PREVIEW_SHA with preview_sha256 from this output:
ergora task create my-project --definition task-definition.json --revision 1 --preview-sha256 PREVIEW_SHA
ergora task creation my-project example-change
# After an interruption, recover with intent_sha256 from creation and the current project revision:
ergora task resume-create my-project example-change --revision 1 --intent-sha256 INTENT_SHA
```

preview invokes the original compiler only in an automatically cleaned temporary directory, without writing to the real task directory. The digest binds the control directory, project revision, registered identity, all compiled contracts and role snapshot. Review a new preview whenever the definition or bindings change. Before publishing any native task file, create saves the complete intent, then publishes seven immutable contracts and finally saves the result receipt. The same request can be retried idempotently. Task IDs are globally unique within an execution-state directory; create and resume-create cannot take over an old task without this tool's intent.

`creation.status` is `not_recorded / pending / published / conflict` and describes only local file publication. `runtime_status: not_queried` and `execution_started_by_operation: false` mean this operation neither queried nor started a workflow; they do not establish the task's actual runtime state. Each contract file is limited to 1 MiB; the intent limit is 16 MiB. Comparison uses native canonical JSON content digests and preserves the bytes of equivalent existing files. Intents and receipts are stored in the registered execution-state directory as `ergora/task-creations/TASK_ID.intent.json` and `.result.json`. Keep them with the original task directory; a backup of the Ergora control database alone does not include the execution-state directory.

After an interruption, query creation first, then explicitly recover using the original intent digest. Recovery does not recompile and retains the original role snapshot even after project bindings change. Conflicting files are preserved and reported as errors; history is not automatically overwritten or recreated. If the project configuration projection or execution directory has drifted, repair the original registration first. Switching execution directories does not automatically migrate old tasks. Write operations serialize while retaining the project revision and acquire a same-ID file lock without blocking. A busy task explicitly returns busy. The budget for one native process is 30 seconds; after a timeout, query the original intent first without automatically retrying.

The corresponding APIs are `POST /api/projects/ID/tasks/preview` (`definition/revision`), `POST /api/projects/ID/tasks` (adding `preview_sha256`), `GET .../tasks/TASK_ID/creation` and `POST .../tasks/TASK_ID/resume-create` (`revision/intent_sha256`). Write requests retain the local same-origin restrictions and `X-Ergora-Request: 1`. Preview and creation support local file contracts on Linux/Windows. Full six-stage execution still uses Linux/WSL2 and the [formal execution guide](AGENT_BACKENDS.md).

<a id="为正式任务冻结审查组合"></a>
### Freeze a review composition for a formal task

The original `schema_version: 1` continues to use four-role bindings and the complete six stages. The new `schema_version: 2` freezes the complete composition bundle and each member's backend, supporting preview, creation, publication recovery, start and original-run status queries. Formal review supports a single read-only reviewer or multiple nested read-only review branches joined through an explicit all-join. Each leaf's input must map directly to the root task through every structural ancestor, with no predecessor dependencies along the path. Other valid static compositions can still be saved and inspected, but unsupported shapes are explicitly rejected before submission. Use the worker and executor managed by this Ergora version; old runners do not support the new envelope.

First prepare a manifest according to the [complete composition bundle instructions](WORKFLOW_DEFINITIONS.md#保存和分享完整组合), and use `verify-manifest` to obtain its `digest`. Change `schema_version` to 2 in the original task definition and add the following `composition` field, keeping the other inputs in the original template format:

```json
{
  "manifest": "/absolute/path/to/review-manifest",
  "manifest_digest": "REPLACE_WITH_THE_VERIFIED_DIGEST",
  "review_instance": "root",
  "mode": "task-mcp",
  "backend_overrides": {
    "root/review": {
      "binding": {"tool": "codex"},
      "reason": "Claude不可用，选择已配置的Codex/ChatGPT"
    }
  },
  "diversity": {
    "policy": "prefer-distinct",
    "reason": "当前只有Codex可用，接受执行和审查共享后端"
  }
}
```

This example is for the `structure-review` bundle; use the actual member paths for other bundles. `manifest` is a local path on the machine running the CLI or HTTP service; an absolute path is recommended. The initial supported shape accepts only a review-workflow subtree with one `task` input and no dependencies on unexecuted external nodes. All leaves must be read-only reviewers. `mode` can be `text-only` or `task-mcp`. Saving a capability contract does not prove that the CLI, authentication, SDK or services are available.

For parallel review by three specialties, first import the three specialists and four review workflows in the [example import order](WORKFLOW_DEFINITIONS.md#运行示例), then prepare the overall review bundle:

```bash
ergora composition prepare-manifest parallel-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./parallel-review-manifest
ergora composition verify-manifest ./parallel-review-manifest
```

Use that directory and the returned digest in the task's `composition`; `review_instance` remains `root`. The member paths are `root/structure/review` (structure, Codex by default), `root/correctness/review` (correctness, Claude Code by default) and `root/test-value/review` (test/CI value, Codex by default). To override a backend, replace a `backend_overrides` key in the example above with the corresponding path. Multiple members can be overridden together. Each definition retains its own declared Skills and initial instructions and fully inherits materials from the root and its containing subtemplates.

The three reviewers inspect the same exact candidate, original validation report and approved plan, saving separate jobs, workspaces, invocations and receipts. Concurrency is constrained by the shared project and ancestor-template limits. Every branch in this example is a required review. Any request for changes, failure, timeout, missing review, or reuse of the author's or another review session prevents approval. After all pass, the original outcome's `review` is `composition-review-aggregate`, retaining each member's original stage/job/receipt digest. It is not an additional model or human approval. `task evidence` and handoff packets can still read these separate originals. After a worker restart, execution continues from the original history without redispatching the same published job. Cancellation and unknown external jobs still follow the original fence/reconciliation process.

For advisory review, import the [review-requirements example](WORKFLOW_DEFINITIONS.md#必需与建议审查的静态声明), then prepare its complete bundle:

```bash
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
ergora composition verify-manifest ./review-requirements-manifest
```

Continue using a `schema_version: 2` task definition, replacing the manifest and digest with these results. The member paths are `root/structure` (required) and `root/test-value` (advisory). Responsibilities are declared by node instances in WorkflowDefinition v2, with at least one required reviewer; backend overrides cannot change them. Old v1 review leaves in a mixed tree remain required. Creation saves a formal v3 envelope. This runtime protocol version is managed separately from the user task-definition and workflow-definition versions.

All branches must still finish and enter an explicit all-join. This new responsibility graph must declare a join even with only one reviewer; directly forwarding task or a leaf result as the output is unsupported for formal execution. Old v1 graphs retain their single-leaf behavior. An advisory member's valid `request-changes` retains its original `FAILED` receipt and findings. Trusted aggregation v2 records each member's `review_requirement`, `decision` and original receipt reference. The task reaches `REVIEW_READY` only when every required member approves and the other contracts are satisfied. An advisory member's process failure, candidate mismatch, missing evidence, session reuse, timeout or cancellation still blocks the task and follows the original fence/reconciliation process. Joining does not turn original opinions into approvals.

To run structure review first, followed by parallel correctness and test-value reviews, import [serial-review](WORKFLOW_DEFINITIONS.md#正式只读审查的数据端口), prepare its complete manifest, and add the following to `composition` in the same task definition:

```json
"review_protocol": "dag-v1"
```

Replace the manifest path and digest with these results. Member paths remain `root/structure/review`, `root/correctness/review` and `root/test-value/review`; use those paths for backend overrides too. This explicit selection is saved as a formal v4 envelope; old tasks without the field continue using their original v2/v3. Downstream nodes receive all original predecessor artifacts only after the predecessors finish, while independently ready branches are scheduled within ancestor limits. Configuring depends_on alone without port bindings does not automatically pass predecessor bodies. Skills, MCP and permissions from the three structural parent templates do not inherit across data arrows. The selected review subtree must have one task input and one terminal output, with an explicit all-join at the endpoint providing full transitive coverage. Nested multiple named outputs are supported; all leaves remain read-only reviewers.

Without overrides, the backend specified by the definition is used. Overrides select individual instance paths and record a reason. `prefer-distinct` is the default policy and requires `diversity.reason` when the backend matches the implementer's; `require-distinct` rejects matching backends outright, while `allow-same` permits them. Backend equality compares tool implementations; different tools do not imply independent model errors. Credentials continue to come from environment variables or protected local authentication and are not written into definitions.

Use the same preview/create commands and APIs as in the previous section, then follow the [formal task sequence](#正式任务的操作顺序与恢复) with `task start/submission/resume-start/status/plan/approve`. The preview's `files.task.spec.json` is an explicitly versioned envelope whose `legacy_spec` retains the unchanged original six-stage projection. `composition.manifest` carries complete file bytes and executable bits. The envelope SHA also binds the static graph, ancestor materials, members, policies and diversity decisions. Removing the source manifest or changing the active library/project bindings after creation does not affect the saved original intent or publication recovery. `runtime_supported` means only that the current runtime bridge supports that static shape; it does not check authentication, models, SDK or service readiness and does not mean execution succeeded.

Composition tasks use separate composition-v2, composition-v3 or composition-v4 queues and request directories according to their formal envelope version. The original owners still handle the six stages, plan approval, candidate verification and receipts. Old workers cannot take over newer versions. During an upgrade, stop the old worker/executor and restart them through this version's `services`, preserving the original history and state directories. Each stage binds the complete original envelope. Status and recovery check the original Temporal input; the same legacy projection cannot substitute for a different manifest. Review invocations save the complete ancestor materials, original template instructions, approved plan and verification artifacts, together with base/candidate source and diff within the shared read scope of the task and leaf. Source, dependency digests, invocations and results all bind to the same candidate. The original monitor continues to own timeout and cancellation. Read-only tool configuration does not provide operating-system isolation. Cancellation of composition tasks also checks the complete original envelope and follows the same `cancel/cancellation/resume-cancel` and original-signal recovery. `requested` still denotes only delivery; external terminal states and leases are checked through the original `external-status/reconcile`, preserving the original outcome after cleanup.

Complete composition bundle exports still support 10 MB/500 files. Inline envelopes for formal tasks retain the original 1 MiB per-file and 16 MiB total intent limits, including base64 and complete bodies in the graph. The original stage context and each member's complete review input each have a 1,000,000-byte limit. Dynamic source, dependency bodies and all ancestor prompts count together, with explicit rejection above the limit. The save and backup scope remains the task's seven contracts, complete intent and result receipt in the registered execution-state directory. A control-database-only backup does not include them. Original v4 read-only DAGs and v5 work compositions inline all original predecessor artifacts in full, so long audit chains may still exceed the budget. `kernel-delivery` still supports only static preview; a manifest does not establish that all nodes have executed.

To assign implementation specialists to the original work units, followed by overall review, select `execution.protocol: work-units-v2` according to the [specialist executor configuration](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元). The user task definition remains schema-v2 and the formal envelope is v6. The page's “Complete manifest · composition execution and review” uses this protocol. v6 passes declared stage artifacts, trusted checks and review comments in full. Execution audits stay in the original receipt/evidence/handoff and continue to be verified individually, avoiding recursive copying of old prompts downstream. Results are also retained for control dependencies without port bindings. Ancestor resources, approval, candidate identity and original recovery gates remain intact. Old `work-units-v1`/v5 tasks do not migrate automatically. New v6 queues require an upgraded worker/executor, and full execution still requires Linux/WSL2 and an explicitly trusted container.

<a id="为盘点和规划选择模板-agent"></a>
### Select template Agents for inventory and planning

[Complete material configuration](WORKFLOW_DEFINITIONS.md#盘点与规划的完整材料) uses task-definition v4/formal input v8, also binding inventory and plan to exact leaf instances, separate backends and all structural ancestor materials. Run through the original `task preview/create/start`; owner approval and the trusted candidate process remain intact. The CLI and API accept complete definitions. The current graphical task wizard can configure preparation stages through the budgeted native entry point (definition6/input10); standalone definition4/input8 is still accessed through the CLI/API.

Select the required `preparation.repository_paths` to include the source/configuration needed for the task. Applicable `AGENTS.md` files are also constrained by the read limit. Choose task-mcp when Skills have attachments; the first two stages have no shell/write/arbitrary-repository tools. Insufficient capacity, incomplete attachment reading or changes to the original inventory artifacts fail the corresponding stage rather than truncating it into success. An optional issue `source` is frozen under the original snapshot contract and enters the four types of model stage. All run identities and recovery remain with the original task owners.

Install and restart the new worker/executor to consume the v8 queue. Like v7, admission follows the actual frozen backends and local execution conditions. Start the required services explicitly with `temporal worker executor`. v8 retains the original stage time limits. For a unified budget starting from preparation, explicitly choose the v5 definition/input9 in the next section. For selecting a single instance within an ordinary parent template, see “Invoke the six stages as a subtemplate” below.

<a id="一次授权的预算准备"></a>
### Prepare under a single budget authorization

On Linux/WSL2, use task-definition v5 to give the original six stages a single authorized total budget. In the v4 definition above, change `schema_version` to `5` and add `budget`, for example `{"wall_seconds":3600,"cleanup_seconds":60,"model_invocations":16}`. The cleanup reserve is included in the total. The invocation limit covers inventory, plan, each work unit and each reviewer (including advisory reviews), and should at least cover these known slots. It counts model-launch slots, not the backend's internal API requests, tokens or cost.

```bash
ergora task prepare my-project --definition task-definition.json --revision 1
ergora task preparation my-project TASK_ID
ergora task preview my-project --definition task-definition.json --revision 1
ergora task create my-project --definition task-definition.json --revision 1 --prepare-sha256 PREPARE_SHA --preview-sha256 PREVIEW_SHA
```

The first prepare saves the single budget before reading the installation or materials. For repeated calls or a lost receipt, continue reading the original TASK_ID without resetting the start time. Preview and create only after prepare reports `status: prepared`. preview reads the complete frozen results, including the two SHAs to confirm; elapsed time does not change their bodies. create no longer publishes after expiry. A saved intent continues through the original `creation/resume-create` without recompiling materials. Preparation binds the project revision and registered identity; changes cannot turn the old authorization into a new budget.

`authorized` means the budget is saved but the body has not started. `unknown` means the original attempt or cleanup is still unconfirmed. `failed/exhausted` does not publish usable preparation results. Check `budget_status` and the original private output. Failure or uncertainty does not automatically rerun the body; reconcile the original identity first. A new independent authorization needs a new task ID. A single observation exceeding 30 seconds returns unknown and retains the original cleanup process without extending business time. `prepared` proves only that preparation finished. After creation, use the original `task start/submission/resume-start/status/plan/approve`. Upgrade and restart this version's worker/executor to consume the `.composition-v9` queue and `requests-composition-v9` request root, and explicitly start the required stack according to [service management](#显式服务管理). The budget starts at the first prepare. Material reading, queueing, human approval, retries, waiting for concurrency slots, model/trusted commands, result collection and process cleanup all consume the same authorization; restarting does not extend it. Prepare services and authentication before authorizing the actual task. Existing v1–v8 runs retain their original contracts.

The work deadline is the total minus the cleanup reserve. Once reached, no new work starts and cleanup follows the original fence. If the total is exhausted before stopping is confirmed, the original unknown/CANCEL_UNCONFIRMED remains. A late result with confirmed stopping can only become a failed terminal state; it cannot publish an expired SUCCEEDED. One Agent CLI invocation does not equal one provider API call, and a reserved slot does not establish an actual launch. The input budget and the original outcome's `budget` retain the original identity, deadlines and observed facts; they are neither a bill nor a kernel-level hard real-time guarantee.

A first start that expires before sending creates no new run. If an attempt already exists, `resume-start` only queries the original workflow/run and complete input without resending, even if the new configuration disables execution. During execution, restarting the Executor continues counting OWNED occupancy in the original jobs ledger. Occupied slots for live or unknown original jobs are not refunded when a Future or Temporal run ends. If a formal receipt is linked but the ledger update is lost, the daemon only reconciles the original terminal state without rerunning the body. Unknown occupancy may block the installation-level `max_parallel_jobs`. Preserve the original request, attempt, owner and stop/collection witnesses and investigate. Do not delete the ledger or manually change terminal states to free slots. This limit differs from a single task's ancestor concurrency constraints and does not establish a project-wide quota across tasks.

This v5 entry point remains an original six-stage formal task. Use the next section's v6 definition when one parent template references one six-stage instance. Multiple native instances or scheduling arbitrary mixed outer graphs still require later contracts.

The APIs are `POST .../tasks/prepare` (`definition/revision`), `GET .../tasks/TASK_ID/preparation` and the original preview/create. v5 create additionally passes `prepare_sha256`; write requests retain same-origin protection and `X-Ergora-Request: 1`. Backups must retain both `ergora/task-creations` in the registered execution state and `operations/task-preparations` in the control directory. A control-database-only backup does not include all materials. New work refuses recovery across boots/hosts or when UTC and monotonic clocks differ substantially; static contracts remain readable.

<a id="将六阶段作为一个子模板调用"></a>
### Invoke the six stages as a subtemplate

task-definition v6/formal input v10 adds `composition.native` to the budget contract above, binding one invocation inside an ordinary parent template to the original six-stage task. The [native-development](../examples/composition/native-development/workflow.json) example references [prepared-delivery](../examples/composition/prepared-delivery/workflow.json). First import the preparation, work and review bundles in the [example dependency order](../examples/composition/README.md), then import the parent bundle and generate a complete manifest.

Keep the v5 input, budget and mode, change `schema_version` to `6`, use the parent manifest's actual path/digest, and move the selection paths into that instance:

```json
{"native":{"protocol":"six-stage-v1","instance":"root/development"},
 "review_instance":"root/development/review"}
```

Write both fields above inside `composition`; see the [v6 schema](../src/ergora/data/schemas/task-definition-v6.json) for the other required fields. The corresponding `execution.instance` is `root/development/work`, with each unit assigned to its actual Agent leaf. `preparation.inventory/plan` are `root/development/preparation/inventory` and `root/development/preparation/plan`. `backend_overrides` also uses the new complete paths. You must still explicitly choose the trusted writer boundary and follow the execution/review backend-diversity policy.

Follow the same `task prepare → preview → create → start` sequence. create still confirms both prepare and preview digests, followed by approval of the original plan. After upgrading and restarting the worker/executor, use the `.composition-v10` queue and `requests-composition-v10` request root; old-version queues and history remain intact. The original task creation record's `composition.native` saves the exact parent-definition chain. `native_invocation` in the original status and terminal outcome projects the same invocation. Task/run/candidate identity, approval, cancellation, unknown recovery and evidence remain with the original owners.

The initial supported shape requires ancestors to contain only this invocation and directly forward task and result. work and review must be direct subtemplates of the selected six-stage instance; inventory/planning may have their own structural wrappers. Preparation rejects additional parent branches, a second instance, unexecuted external inputs or control dependencies. Internal work/review still supports the existing sequential/parallel DAGs; this does not authorize execution of arbitrary outer graphs. The graphical task wizard can select the native six stages following the [page composition steps](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合), explicitly authorize preparation, then preview and create definition6/input10. The CLI/HTTP can still submit complete definitions.

<a id="为正式任务选择项目记忆与活动-skill"></a>
### Select project memories and active Skills for a formal task

For the combined sequence from retrospective candidates through separate adoption to freezing a new task, see the [complete improvement journey](IMPROVEMENT_WORKFLOW.md).

On Linux/WSL2, use [task-definition v7](../src/ergora/data/schemas/task-definition-v7.json)/formal input v11 on top of the native six-stage definition above. First run `ergora memory catalog PROJECT` to inspect the `id`/`revision` of currently valid memories, and `ergora skill list PROJECT` for the `name`/`digest`/`revision` of active heads. Change the user definition's `schema_version` to `7`, append the following field and replace the example identities:

```json
{
  "context": {
    "root_version": "1.0.1",
    "memories": [{"id": "MEMORY_ID", "revision": 2}],
    "skills": [{"name": "your-skill", "digest": "ACTIVE_SHA256", "revision": 1}]
  }
}
```

At least one of the two lists must be nonempty. Only the project's latest currently valid memory revisions and the exact heads of currently active Skills are accepted. An initially imported baseline can be selected, but that does not establish measured improvement. `root_version` is the new version of the selected manifest's root definition and must differ from the original root. The system retains the same root ID, all member paths, original permissions and limits, adding only source context and complete Skill directories. The derived bundle is frozen with this task and does not change active Skills or the global definition library. Skill attachments require the corresponding instance's `task-mcp`/`workspace-task-mcp` mode. A read scope that does not cover the new root resource URI, conflicting content for a same-name Skill, or insufficient capacity causes explicit rejection. To change permissions, first follow the original parent/child definition revision process, then select a new manifest.

Use the original `task prepare → preview → create → start`; create still explicitly confirms both prepare and preview digests. The preview's `files["task.spec.json"].context` gives the selected identities. `composition.manifest` carries the complete sources and files. `task_envelopes.selected_context` supports offline checks of the original bodies, sources, expiry and Skill attachment identities. Each graph leaf's `material_bytes` and each scope's `usage`/`limits` show static capacity. Dynamic repository content, predecessor results and complete prompts are still checked at the actual stage; static headroom does not guarantee future success.

Old selections cannot be published for the first time after a correction, deletion, expiry or active-head change. Interrupted recovery with a complete saved creation intent uses the original snapshot, including materials that subsequently became invalid. `task creation` checks the original intent; `task resume-create` recovers by its SHA without reselecting materials or extending the budget. Archived input is run evidence. Deleting canonical memories does not remove frozen tasks or independent backups. The new protocol registers the `.composition-v11` queue and `requests-composition-v11` request root; upgrade and restart the worker/executor before using them. The CLI and HTTP share this contract.

In “Formal tasks → Preview and create,” select the native six stages and read the complete manifest. “Material sources for this task” defaults to inheriting only template materials. To add project materials, select “Inherit template and append project materials,” enter the exact new derived-root version, click “Read current material catalog,” then explicitly select memories and active Skills. The page shows complete memory bodies/sources/expiry, unselectable states and exact Skill heads. Expired and deleted records cannot be selected. Refreshing the catalog clears selections; after a failed read, a successful reread is required before use. The catalog is only an observed snapshot; original admission checks it again. Next explicitly authorize preparation, inspect frozen sources and complete files, then confirm creation with both digests. The authorization-input download includes the complete context selection. All existing ancestor materials are still inherited, and the page offers no operation to remove ancestor resources or expand permissions. The lightweight read-only `GET /api/projects/PROJECT_ID/skills/heads` returns only current active heads without invoking tool diagnostics.

<a id="使用重构配方"></a>
### Use the refactoring recipe

`refactoring` delegates behavior-preserving refactoring to the original `large-change` six-stage owner. By default, material inventory, planning and original owner approval run first. After the refactoring implementer finishes `rewrite`, the compatibility specialist performs `compatibility` on a candidate integrating its predecessor. After the original trusted integrate/verify stages, three required reviewers inspect structure, correctness and test value in parallel.

```bash
ergora composition install-preset refactoring
ergora composition prepare-manifest ergora-refactoring-template 1.0.0 \
  --grant examples/composition/refactoring/grant.json \
  --directory ./refactoring-manifest
```

The example is in the repository's [refactoring directory](../examples/composition/refactoring/README.md). The wheel contains all Agents and subtemplates; examples are unnecessary when using your own grant. Copy [task.example.json](../examples/composition/refactoring/task.example.json) into a task definition and enter the real issue, task ID, baseline, manifest path/digest and actual project modules/callers. Also check the complete material scope, behavior invariants, migration and isolated rollback checks. Then follow the original `task prepare → preview → create` sequence with two-digest confirmation, followed by start/plan approval. Valid JSON or successful prepare proves only that the contract can be assembled. Actual checks and review evidence support behavior preservation.

By default, preparation and writers use Codex, and reviewers use Claude Code. Each instance can use the original `backend_overrides` to select another actually supported backend. When Claude is unavailable, fill in per-leaf overrides and `diversity.reason` according to the [diversity policy](#为正式任务冻结审查组合). Independent sessions on the same backend retain the actual fallback reason. The compatibility executor has its own writable work unit; its checks do not replace the final three independent reviewers. If changing the default division of work, revise the exact subtemplates and original units mapping together. The original task/profile and material limits still apply.

The new recipe does not rewrite old versions or in-flight tasks. To revert the selection for a new task, reselect the old exact bundle/manifest and prepare it. Observe, cancel or reconcile an already started task using its original task/run.

To give every role guidance on repository conventions, module dependencies and real testing seams, explicitly select `refactoring-quality`:

```bash
ergora composition install-preset refactoring-quality
ergora composition prepare-manifest ergora-refactoring-template 1.1.0 \
  --grant examples/composition/refactoring/grant.json \
  --directory ./refactoring-quality-manifest
```

It adds only the standard [`ergora-codebase-quality`](../src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/skills/ergora-codebase-quality/SKILL.md) to the parent template; all descendants inherit the complete Skill bundle. The atomic workflows, instance paths, permissions, budget, backends and task example follow the configuration above. Enter the new manifest path/digest into your new task. Installation does not upgrade old 1.0.0 or frozen tasks. Roles follow the target repository's applicable conventions and configuration rather than applying another training framework's formatting rules.

The definitions and compositions for the refactoring implementer, structure reviewer, correctness and test-value reviewers, and compatibility validator are maintained in this repository. Engineering guidance draws on [documented Skills and upstream research](research/2026-11-14-local-engineering-skills.md), retaining each source's license. They are independently versionable specialty configurations; Codex/Claude Code are the actual runtime backends. Selecting a backend does not import all of that tool's private prompts, Skills or scheduling framework. Check backend capabilities and complete material reading separately according to the [Agent guide](AGENT_BACKENDS.md).

To use the Skill only in a standalone project invocation, run the following command from this repository's checkout root after registering the real `my-project`:

```bash
ergora skill import my-project \
  src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/skills/ergora-codebase-quality
```

Standalone `agent run --skill ergora-codebase-quality` consumes the project's currently adopted version. This and the template's fixed Skill are two explicit choices. The first same-name import becomes the initial baseline; subsequent candidates still require [evaluation and adoption](INTEGRATIONS.md#skill-候选评价与采用). Importing into a project or editing a host Skill does not change a frozen template. Changing materials for a formal task requires selecting a new version and manifest.

<a id="查询正式任务运行状态"></a>
### Query formal task run status

Install the development profile or `ergora[temporal]`, and prepare the registered reference runtime. Use the CLI or `GET /api/projects/ID/tasks/TASK_ID/status?run_id=RUN_ID&timeout=20` for read-only native-run facts:

```bash
ergora task status my-project TASK_ID --timeout 20
# Pin subsequent queries to the native run_id returned by the previous query:
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

This operation first validates the local task's project ownership and spec, then uses the original DevelopmentTransport in the registered installation to check Temporal's original start input. `runtime_status: queried` includes the native workflow/run ID, phase and status or outcome. If no run ID is supplied, it first resolves the current workflow and returns its concrete run ID, which can be pinned for subsequent queries. Only a native NOT_FOUND returns `runtime_status: not_found`, without an invented phase. Connection, authentication, timeout and original-input collision failures are errors and cannot be treated as “not started.” The query does not submit, approve, cancel or release an issue lease, and does not write task state.

`terminal: true` means only that the Temporal run is closed. Its outcome may still be CANCEL_UNCONFIRMED, or its phase NEEDS_RECONCILIATION; both require reconciliation under the original ID. This entry point uses the registered reference environment's connection rules (currently local 127.0.0.1:7233/default). The project scheduler binding's address/queue is used only for material-research scheduling. A 1–60-second timeout constrains the network query. The child process receives an additional 5 seconds for startup/reaping; local contract prechecks and installation identity checks are separate. Missing SDKs produce an explicit message. They are not installed automatically, and runtime state is not inferred from local COMPILED or service RUNNING states. Full six-stage execution still uses Linux/WSL2.

<a id="分段读取原运行事件"></a>
### Read original-run events in pages

For a task created through the unified entry point with its original submission receipt saved, pin that receipt's run ID and read event metadata:

```bash
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --timeout 20
# Only when continuing, pass the previously returned next_after unchanged:
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --after CURSOR --timeout 20
```

The same-origin read-only API is `GET /api/projects/ID/tasks/TASK_ID/events?run_id=RUN_ID&limit=20&after=CURSOR&timeout=20`; omit after on the first call. This entry point uses the Linux/WSL2 reference runtime and original submission/spec/memo validation described above, without following another run. It returns event IDs, types, timestamps and applicable activity/scheduled_event/signal association fields, without original input, prompts, results or payloads. Event projection does not decode payloads, although original-identity validation still needs to decode the start spec. `read_only: true` and `execution_success: null` make clear that this is only a fragment of facts. If the native run does not exist, it returns `runtime_status: not_found`. Connection, timeout, wrong-ownership and cursor errors fail explicitly without automatic retries or task resubmission.

After original-identity validation, each call reads one physical SDK event page and returns at most limit entries (1–100, default 20); it does not guarantee filling the limit. The overall request also describes the original run and reads its start prefix, so it is not a single RPC. Temporal's physical page size is advisory and may exceed the requested count. The cursor retains the unread position in that page, and the next call first continues through its remaining entries. `next_after` is read-only navigation bound to the original submission/run, not authorization or proof of complete history, and cannot be used across runs. The display limit can change; the SDK page size retains the original cursor's value. The total JSON response is limited to 1 MiB; that response limit does not constrain network memory used by SDK physical-page reception. timeout is a 1–60-second wall-clock budget. The parent process provides another 5 seconds for startup/reaping; prechecks are separate.

`has_more` means unread content is known to remain; `at_current_end` means only that reading has reached the currently visible end. A RUNNING run retains next_after even when no new events are currently available, so the user can explicitly read later. Only a terminal run read through its end returns null. Event fragments do not prove six-stage completion, candidate acceptance or stopped external processes; verify those facts through the original status/outcome and external reconciliation.

On the formal task page, first select “Read original run,” then “Read original-run events.” Opening reads the first batch; each subsequent click reads at most 20 entries, without automatic polling or retry. The page shows the cumulative read count and the latest 200 entries. Association fields exceeding 256 Unicode characters show an ellipsis; read complete metadata through the CLI/API. At the current end of a running run, you can still manually select “Read new events.” The button is disabled after a terminal run has been fully read. A failed read preserves the fragments already read in this session and the original position; continuing requires an explicit retry click. Closing and reopening starts from the first batch. Switching project, task or run invalidates old responses. Displayed records are only this session's observations, not persistent evidence or proof of complete history.

<a id="读取原job回执与文本证据"></a>
### Read original job receipts and text evidence

From the original events above, for Activity type `dev_submit`, select an `ACTIVITY_TASK_SCHEDULED` event ID (not an activity ID or completed-event ID), then read the job catalog first. 42 below is only an example; use the actual ID:

```bash
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --timeout 20
# Select a name from the returned receipt.artifacts and retain this receipt_sha256; do not pass a local path
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --artifact model-log --receipt-sha256 RECEIPT_SHA --offset 0 --limit 8192 --timeout 20
```

The API is `GET /api/projects/ID/tasks/TASK_ID/jobs/42?run_id=RUN_ID&timeout=20`. Add `artifact=model-log&receipt_sha256=RECEIPT_SHA&offset=0&limit=8192` for a text window. Continue manually with the returned `artifact.next_offset`; null marks the end of that text. offset/limit count Unicode characters, not UTF-8 bytes. A window defaults to 8192 characters and allows at most 16384, retaining the SHA, byte count and character count of the complete original text. A changed receipt or changed artifact bytes causes an explicit failure, preventing fragments from being combined as one log. Artifact names match only entries in the selected original job receipt; user-supplied paths are not parsed.

This read still pins the unified task's original submission/run/spec/memo. It checks a contiguous history prefix through the selected scheduled event, decodes only that event's original context, then checks the original request envelope and receipt published in the trusted directory. Event IDs 1–10000 are supported. Later events are explicitly rejected; this does not establish that no job exists. Both RUNNING and closed original runs can be read. `runtime_status: not_found` means the original history is currently unknown; `receipt_status: missing` means there is no verifiable published receipt yet. Without a receipt, no log is offered, and an existing request directory is not treated as completed execution.

`receipt_status: published` means only that the original job's currently published receipt passes checks through the local trusted file adapter. `workflow_receipt_accepted: null` and `execution_success: null` preserve uncertainty. Even if the receipt state is SUCCEEDED, use original-run status/outcome, candidate checks and external reconciliation to verify actual acceptance, development results and cleanup facts. This feature does not change original intents, receipts, claims or Git refs, and does not submit, resend or automatically retry.

The native adapter allows at most 16 MiB per artifact. It checks the complete digest first, strictly decodes the selected full UTF-8 text and rejects NUL, then returns the window. Missing, damaged, non-UTF-8, NUL-containing, oversized or unsafe-path artifacts fail explicitly. Each receipt check rereads the digests of all its artifacts; the selected text also requires a complete read/decode. The window and 1 MiB JSON response limits do not limit SDK physical pages or total file reading/memory, and there is no hidden cache. timeout is 1–60 seconds. Network operations inside the coroutine are constrained by a 20-second RPC limit and the request budget; synchronous file reads are finally reaped by the parent process at timeout+5 seconds. This entry point uses the existing Linux/WSL2 reference runtime. The base Web application itself does not require the Temporal SDK, but native queries need the registered complete execution environment and its SDK. If the environment is incomplete, configure it according to the tool-diagnostics page; nothing is installed and no services are started automatically.

On the page, first read the original run and its events, then click “Original job evidence” on a scheduled-event row whose Activity is `dev_submit`. The dialog reads that original run/event's job catalog and shows the original receipt, candidate and digests. Missing or failed reads can be retried manually. Selecting a material from the receipt does not issue a text request. Only clicking “Read first segment of selected material” reads an 8192-character window; read the next segment manually. Each read pins the first receipt SHA, and the page retains only the current window and full artifact digest. Material errors or an unknown original run preserve the read window and original offset, allowing “Retry original position.” If the receipt changes, close the dialog and recheck the catalog; old windows cannot be stitched together. Switching materials clears the window and resets the offset to zero; reading stops at the end. Closing and reopening restores no text and performs no background polling. Editing the run, switching task/project, replacing the dialog or leaving the page invalidates late responses from previous requests.

<a id="提交正式任务与恢复未知结果"></a>
### Submit formal tasks and recover unknown results

On Linux/WSL2, install the reference runtime's required dependencies and initialize the registered configuration. Admission uses that runtime's `.venv/bin/python`. The control plane need not install all execution dependencies. v1–v6 use the original installation-level doctor; v7 source tasks check actual dependencies according to the [frozen selection](#从工单快照创建来源任务). Actual submission still checks trusted checks, policies and issue occupancy; selected services and models must be ready. This entry point accepts only tasks fully created through the unified entry point and retains their original spec and role snapshot.

```bash
# CREATION_SHA comes from task creation's intent_sha256; obtain the revision from project show.
ergora task start my-project TASK_ID --revision 1 --creation-sha256 CREATION_SHA --timeout 20
ergora task submission my-project TASK_ID
# After an interruption, read submission first, then explicitly recover with its original intent_sha256 and the current project revision:
ergora task resume-start my-project TASK_ID --revision 1 --intent-sha256 SUBMISSION_SHA --timeout 20
```

`submission` checks only the local submission record without connecting to Temporal. `status: submitted` means the original workflow/run ID receipt is saved; `execution_success: null` does not mean the six stages succeeded. Query progress with `task status --run-id RUN_ID`. Repeated start returns only the original local record without resubmitting. `not_recorded` means no submission intent exists. `prepared` means an intent exists but no dispatch checkpoint has been saved. `unknown` means the checkpoint is saved but the original call's result is unknown. `rejected` means an existing run not belonging to this submission was found and the rejection record preserved. A mutation command reports CLI success only for submitted.

The immutable intent is saved first, followed by original admission/claim. An attempt is saved before the actual start, and the native receipt is saved last. prepared can repeat admission through an explicit resume while reusing the same lease. unknown can only query original input under the original workflow ID and fill in the receipt; even NOT_FOUND does not permit resending. A crash after writing the checkpoint but before the actual RPC also retains unknown and requires manual reconciliation. An existing run is rejected rather than taken over; later disappearance of its history does not automatically restart it. The original start associates this submission-intent digest in Temporal memo, and unknown recovery also checks that marker. Missing or different markers prevent adoption as this submission. An AlreadyStarted response from a submission race is persistently rejected without adopting another entry point's run. Original input is compared exactly by canonical JSON digest, distinguishing true/1/1.0. Original-input mismatch, RPC failure and contract/registration drift all cause explicit errors. Do not change the task ID to bypass an unknown state, and do not release the lease. Repeated operations with an already saved receipt continue returning the original run ID.

The intent, dispatch checkpoint, receipt and any applicable ownership-rejection record are stored in the execution-state directory at `ergora/task-submissions/TASK_ID.{intent,attempt,result,rejection}.json`. Keep them with creation records, the task directory and original run state. The preparation stage retains the current project revision and acquires the original same-ID lock without blocking, saving only the intent. It then releases the control-database write lock; the network stage holds only the original task lock. The 1–60-second timeout applies separately to preparation and network stages. The parent process provides each with another 5 seconds for startup/reaping; prechecks are separate. A timeout reaps only the submission client. The persistent executor owns actual Agents, so a client timeout does not establish a stop. An incomplete environment fails explicitly without automatically starting services or changing execution permissions.

APIs: `POST .../tasks/TASK_ID/start` with body `revision/creation_sha256/timeout`, `GET .../tasks/TASK_ID/submission`, and `POST .../tasks/TASK_ID/resume-start` with body `revision/intent_sha256/timeout`. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Concurrent preparation or creation/resume-create for the same task returns busy promptly when its task lock is active. Concurrent reads may observe prepared/unknown snapshots without waiting for the other request to finish. After the operation, read submission and the current project revision before deciding whether to explicitly resume. Repeating start does not implicitly retry undispatched admission, and unknown does not resend. Other projects do not have the control-database write lock continuously occupied by this network wait. Even an HTTP success response requires checking status; unknown/rejected cannot be treated as successful submission.

<a id="读取待批计划材料"></a>
### Read plan materials awaiting approval

This applies only to tasks created through the unified entry point with their original submission receipt saved, using the same runtime environment as submission. First query the original state with `task status --run-id RUN_ID`, obtain the actual plan SHA from `AWAITING_PLAN_APPROVAL`, then read its materials:

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 PLAN_SHA --timeout 20
```

`plan` checks the original submission run/spec/memo, the current awaiting-approval phase and selected plan SHA. It locates the plan job in the original history and checks the request envelope and accepted receipt. The plan SHA is the canonical JSON digest of the entire receipt, not the execution-plan file digest. `materials` returns complete UTF-8 text and each material's `name/sha256/bytes` according to the frozen profile. Both development templates provide execution-plan, ownership-map and rollback-plan. The response also retains the original run, request, profile, receipt and history-event identities for reviewing work units, scope, risks and rollback measures.

Each material is limited to 256 KiB, and the total JSON response to 1 MiB. Missing materials, digest mismatch, non-UTF-8, unsafe paths or exceeded limits reject the read instead of truncating it into an apparently complete plan. `--timeout` is 1–60 seconds. The parent process provides another 5 seconds for startup/reaping; local prechecks are separate. This operation holds no control-database write lock, creates no decision or owner receipt, and sends no signal. The result is a snapshot at read time; the server checks the original run's current state again before approval.

API: GET `.../tasks/TASK_ID/plan?run_id=RUN_ID&plan_sha256=PLAN_SHA&timeout=20`. The page's “Review plan and approve” uses the same entry point. After a network failure or when the plan is no longer awaiting approval, query status again using the original ID without creating a replacement task.

<a id="批准精确计划与恢复投递"></a>
### Approve an exact plan and recover delivery

First read and review the complete materials as described above, then explicitly approve using the current project revision, original run ID and that plan SHA:

```bash
ergora task approve my-project TASK_ID --decision-id owner-one --revision 1 --run-id RUN_ID --plan-sha256 PLAN_SHA --confirm --timeout 20
ergora task approval my-project TASK_ID owner-one
# After an interruption, read approval first, then recover with the original intent_sha256 and current project revision:
ergora task resume-approve my-project TASK_ID owner-one --revision 1 --intent-sha256 APPROVAL_SHA --confirm --timeout 20
```

The decision ID is the stable identifier for this owner decision. Repeating the same ID only reads the original record; it does not resend, change the plan or extend the 24-hour validity period. After a plan update, expiry or revocation of the original decision, review the current plan and explicitly make a new decision with a new decision ID. Project binding changes do not alter the original role snapshot. This local entry point uses the current Linux user as the owner actor and does not provide team authentication.

`approval` reads only local records without connecting to Temporal. States are `not_recorded / prepared / unknown / requested`. prepared has no signal checkpoint yet and can be explicitly recovered. unknown has a saved attempt; recovery can only check the exact request/plan/receipt in the original run's paginated history without resending. If the signal is not found or the original run is unavailable, the result remains unknown; continue reconciliation under the original ID. Revoking or changing the owner receipt makes the original intent no longer dispatchable.

`requested` means only that the SDK acknowledged the signal or that the original history contains a corresponding event. `approval_accepted: null` and `execution_success: null` do not mean approval was accepted or the six stages succeeded. The workflow still checks owner/expiry/revocation/exact plan under the original authorization rules. Use `task status --run-id RUN_ID` to check actual progress. CLI mutations return 0 only for requested; even HTTP success responses require checking status.

Approval operation records are stored in the execution-state directory at `ergora/task-approvals/TASK_ID/DECISION_ID.{intent,attempt,result}.json`; the original owner receipt is at `approvals/owner-UUID.json`. Keep them with the original task, creation and submission records. Intent preparation retains the project revision and acquires the original task lock without blocking. The network stage releases the control-database write lock and holds only the same-task lock. Preparation and network each have a 1–60-second budget. The parent process adds 5 seconds for each; local prechecks are separate. After a timeout, read the records before deciding whether to recover.

API: GET/POST `.../tasks/TASK_ID/approvals/DECISION_ID`. The POST body is `revision/run_id/plan_sha256/confirm/timeout`; POST to the same path's `/resume` uses `revision/intent_sha256/confirm/timeout`. `confirm` must be true. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Tasks created/started through the old reference entry point remain managed by the original CLI; this entry point does not adopt old runs.

<a id="请求取消与恢复未知投递"></a>
### Request cancellation and recover unknown delivery

Tasks created through the unified entry point with their original submission receipt saved can request cooperative cancellation pinned to the original run. As with approval, use the current project revision, a stable request ID and explicit confirmation. The reason must be nonempty and at most 1000 characters:

```bash
ergora task cancel my-project TASK_ID --request-id stop-one --revision 1 --run-id RUN_ID --reason 'Owner requested stop' --confirm --timeout 20
ergora task cancellation my-project TASK_ID stop-one
# After an interruption, read cancellation first and recover the same request with its original intent_sha256:
ergora task resume-cancel my-project TASK_ID stop-one --revision 1 --intent-sha256 CANCELLATION_SHA --confirm --timeout 20
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

`cancellation` checks only local records without connecting to Temporal. `prepared` has no dispatch checkpoint yet, so explicit recovery can continue the original cancel. `unknown` has a checkpoint but unconfirmed delivery; it can only check the complete signal containing this operation's SHA in the original run history. It cannot claim another request merely because the reason matches, and does not resend. Repeating the same ID retains the original reason/actor without generating a second request. Do not change the ID to bypass uncertainty; first check original-run and external-job facts.

`requested` and `cancel_requested: true` mean only that the signal was acknowledged or the original history has a corresponding event. `already_closed` means the original run was closed when checked for this operation; `cancel_requested: false` and `signal_delivery: not_sent` explicitly mean no new signal was sent. Repeated reads return saved facts rather than a new live query. CLI mutations return 0 for either state, but the status fields must still be checked. `cancellation_confirmed: null` and `execution_success: null` do not establish stopped execution. Use `task status --run-id` to check the original phase/outcome. Continue reconciling CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION with the original fence and external jobs; do not delete the ledger, terminate, or automatically release unconfirmed leases.

Intent/attempt/result records are stored in the execution-state directory at `ergora/task-cancellations/TASK_ID/REQUEST_ID.*.json`. Keep them with the original task, creation and submission records. Preparation acquires the original task lock without blocking under the current revision. The remote stage releases the control-database write lock. Each stage has a 1–60-second budget, with another 5 seconds from the parent process for each; local prechecks are separate. Windows uses the registered complete Linux/WSL2 runtime. This local entry point is not a team permissions system.

The API is GET/POST `.../tasks/TASK_ID/cancellations/REQUEST_ID`. The POST body is `revision/run_id/reason/confirm/timeout`; POST to the same path's `/resume` uses `revision/intent_sha256/confirm/timeout`. Strict confirmation must be true. Write requests retain same-origin protection and `X-Ergora-Request: 1`. Tasks from the old entry point remain managed by the original CLI.

<a id="读取闭合运行的证据索引"></a>
### Read the evidence index of a closed run

For tasks created through the unified entry point with their original submission receipt saved, read evidence references together after the original run is closed with no successor run:

```bash
ergora task evidence my-project TASK_ID --run-id RUN_ID --timeout 20
```

API: `GET /api/projects/PROJECT_ID/tasks/TASK_ID/evidence?run_id=RUN_ID&timeout=20`. Use the registered complete Linux/WSL2 runtime. The query budget is 1–60 seconds, with another 5 seconds from the parent process; local contract prechecks are separate. Timeout, oversized responses or wrong ownership cause explicit failure rather than returning a partial index presented as complete.

`contract` fixes the original creation/submission digests, spec and Agent-binding snapshot. `original_outcome` and its digest preserve the original result. `jobs` lists original scheduled-event IDs, context digests, request/receipt states and complete checked receipts. Receipts include the actor, candidate, checks and material name/path/SHA, without material bodies. For bodies, use the [original-job reading entry point](#读取原job回执与文本证据) with the listed scheduled event.

`published_evidence: verified` means only that all original requests/published receipts and artifact bytes in this check match completely. It does not mean checks passed, independent review approved or the task can be merged; `execution_success` remains null. Only verification/review receipts explicitly saved in the original outcome are compared individually with their corresponding jobs, with `outcome_reference_state` showing `matches/differs/unavailable`. Other stages show `not_recorded`; existing files do not establish acceptance. Missing or damaged receipts/artifacts make `published_evidence` `incomplete`. Wrong requests, fences, roots or history are explicitly rejected. External cleanup is described separately by `external_confirmed/fence/unresolved_jobs`. A normal task can have complete materials without a fence; a cancelled task still retains its original CANCEL_UNCONFIRMED.

The index response is limited to 1 MiB, but still scans the complete original history and uses FileAdapter to read and check every artifact (up to 16 MiB each). It does not limit total I/O or total memory to 1 MiB. Results describe current material observations; later reads must verify again. Evaluation sets, Skills, memories and source-adoption snapshots in `context_snapshots` are `not_recorded` if the original task did not record them. Current configuration does not fill in history. The query does not start services, execute models, write fences, release leases or change Git refs.

The `budget` field still projects the same frozen profile's `limits`, stage waits, human-approval wait and polling interval, with the original profile SHA and `workflow_admission_and_waiting` scope. `max_parallel_units` constrains work-unit scheduling; it is not a global concurrency limit for all external processes. Stage deadlines are established after the original dev_submit returns and checked after polls with empty receipts. They do not guarantee hard external-process deadlines and are not total task-duration or cost limits. The historical executor's separate walltime cannot be reconstructed from current configuration. v9's unified authorization is separately stored in `contract.original_input.budget`, and runtime observations in `original_outcome.budget`. Do not treat the old profile projection as that persistent authorization or as actual model-invocation billing.

`usage` lists event counts from the complete original history: activity schedules, actually recorded activity-starts, signals, dev_submit events and distinct jobs. It also gives the number of work units in the frozen request. The SDK merges some retry history, so these counts cannot establish all retries, model invocations or billing. `workflow_span` calculates seconds from the original first/final event Timestamps and includes event references. It includes queueing, human waits, concurrency and service downtime; it is neither model runtime nor the sum of job durations. Missing timestamps produce `not_recorded`; reversed timestamps produce `invalid_timestamps` with a null value. Only a real zero span yields 0. Without structured usage sources verified against original jobs, `model_calls/tokens/cost` are all `not_recorded/value: null`, and cost currency and source are also null. They are not automatically estimated from material text or current pricing.

<a id="收集与离线核对交接包"></a>
### Collect and verify handoff packets offline

When the original run is closed and the index above has complete materials, explicitly collect them into a new local file. Use the registered complete Linux/WSL2 runtime without starting a worker or rerunning an agent:

```bash
ergora task handoff my-project TASK_ID --run-id RUN_ID --output ./task-handoff.zip --timeout 20
```

Collection reads only artifacts referenced by the original index and receipts. It does not scan the environment, credentials, arbitrary user directories or the whole repository. Missing/damaged materials or additional jobs cause collection to be rejected. Original business failure or cancellation does not prevent handing off complete materials and is not rewritten as success. A temporary file in the same directory is completed and then published with create-only semantics, refusing to overwrite an existing target; a local filesystem supporting hard links is required. Ordinary exceptions clean up temporary files. After forced process termination, first inspect the target and `.ergora-handoff-*` remnants in the same directory, and confirm that no collection process is still running before handling them. The query budget is 1–60 seconds, plus 5 seconds from the parent process. A timeout does not guarantee that the file has not been published. Check an existing target first rather than blindly overwriting it.

Recipients need only the base `ergora` installation and can run on native Windows or Linux without a control database, SDK or online services:

```bash
ergora handoff verify ./task-handoff.zip
ergora handoff verify ./task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

The optional `--sha256` accepts an independently obtained 64-character lowercase hexadecimal digest of the complete packet. A match gives `external_sha256: matches`; omitting it gives `not_recorded`. Success outputs `status: verified`, packet/manifest digests, project/original-run/candidate references and the original outcome. `verification_scope: packet_bytes_and_declared_internal_identities` proves only that the packet's bytes, digests and declared spec/request/profile/binding, job/receipt/material relationships match. `origin_authenticated: false` and `execution_success: null` remain unchanged. The packet does not carry complete creation/submission intents, service history, context or Git objects; their SHAs are only references. Offline verification cannot authenticate the original executor, verify history counts or review independence, replay execution or recheck candidate code. An external SHA does not itself constitute a signature or source authentication.

v1 uses standard ZIP_STORED, UTF-8 JSON, SHA256 and a public [versioned schema](../src/ergora/data/schemas/task-handoff-v1.json), containing only `manifest.json` and digest-deduplicated `blobs/SHA256`. Limits are 1 MiB for the manifest, 16 MiB per blob, 64 MiB total deduplicated materials, 4096 members and 72 MiB for the complete packet. Duplicate, extra, missing, noncanonical-path, linked, encrypted or compressed members are explicitly rejected. Verification reads members directly without extracting or executing them. These limits do not constrain ZIP-library peak memory or the original index's complete-history/per-artifact reading costs to 1 MiB. Handoff packets support material review; they do not replace a combined backup of the original execution directory, Git and lease database. Operators separately choose local output paths and transmission.

HTTP clients can explicitly `POST /api/projects/PROJECT_ID/tasks/TASK_ID/handoff` with JSON body `{"run_id":"RUN_ID","timeout":20}`. Same-origin protection and `X-Ergora-Request: 1` still apply. Additional fields such as server source/output paths are not accepted. Success returns `application/zip` with the fixed attachment name `ergora-handoff.zip`; `X-Ergora-Handoff-SHA256` is the whole-packet digest of this response's bytes. The server invokes the same collection use case in a private temporary directory, reads the packet back within limits and checks its SHA, cleans the temporary directory, then sends the response. Ordinary failures also clean up, without starting services or changing the original task. The client chooses the download location and must avoid overwriting local files that need to be kept. This entry point buffers up to 72 MiB of packet bytes and has additional memory costs; it is not a streaming download. Remnants from forced process termination are handled operationally. The response digest supports comparison of this download and is not a signature. Obtain any independently expected SHA through a separate trusted channel.

<a id="完整选择离线证据用于复盘"></a>
### Select complete offline evidence for a retrospective

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

In the page, select “Retrospective improvement”, enter the handoff-package path on the console machine and the full-package SHA checked at download, then “Read handoff index”. Its project ID must match the current project. Nothing is selected by default. Select by original job/material name, then “Read complete selected materials” to display all original text, provenance and selection identity. Download CLI-compatible `selected-artifacts.json` and complete `retrospective-evidence.json`. The latter's internal sha256 remains the canonical identity above, distinct from the JSON file's byte digest. Changing sources or rereading the index invalidates the old selection. Successful rereading clears selections; a failed read retains input and failure status. The original owner refuses binary, NUL and complete over-capacity results; windows or truncation cannot bypass it. Candidate preparation, read-only model invocation and result export each require explicit submission. Evaluation and adoption follow below.

<a id="在页面准备完整复盘输入"></a>
### Prepare complete retrospective input in the page

The “Prepare retrospective candidate input” form becomes available only after complete selected materials have been read in “Retrospective improvement”. Choose Skill, project memory or workflow improvement. For a Skill, “Read current baseline” and explicitly select an active head. For memory, explicitly select a valid revision or “New memory”. For workflows, also enter the complete target manifest, its digest and a new version for the target root. This and the candidate author's manifest are separate inputs.

Enter the improvement objective, saved complete author-manifest path, author instance, new input directory and complete-prompt byte limit, then “Save complete candidate input”. The required three presets and author manifests are described under each direction below. The server rechecks the baseline, evidence and complete permissions/resources/capacity; it does not overwrite an existing directory. Successful saving produces only the complete original input. Invoke the model, inspect its original result, export, evaluate and adopt through their separate explicit operations below.

If preparation fails, a reply is lost or the page has changed, retain the original submitted directory and explicitly read that path in “Reread saved input”. This checks the complete original input/request/inherited materials and owning project. It does not rebuild from a new form or automatically prepare again. A later invalid source head or memory does not rewrite saved input; a new preparation uses currently valid sources. Carry the entire input directory to another machine, rather than just the JSON returned by the page. The original `ergora composition verify-input INPUT_DIRECTORY --material` verifies the complete directory offline; actual `run-input` rechecks current backend admission.

<a id="在页面明确调用冻结的只读叶"></a>
### Explicitly invoke a frozen read-only leaf in the page

Both “Tool bindings” and “Retrospective improvement” offer “Invoke frozen read-only leaf”. Enter the complete input directory on the console machine and its original digest. Choose the backend requested by the frozen definition, or explicitly specify a backend/model/reason and optional Codex reasoning-configuration path, then “Check current read-only admission”. The page shows the original role, requested and actual backend, all material identities and permission limits. This check is a current observation and runs again before invocation; changes to input/backend require another check.

After confirming, enter the timeout and explicitly submit one call. Fields are locked during execution; the page does not automatically resend or continue it. Closing a window, changing pages or a network error does not mean the original call stopped. Reopen the window and explicitly “Read original invocation records”, matching the latest 100 original records by input digest, backend and start time. The result's status is the original run status: HTTP success can still have stored failed/timed_out. Use the result file and SHA for the complete result; diagnostics have a bounded display.

When opened from “Retrospective improvement”, a successful original record can “Use in original-result inspection”, copying the saved run-snapshot directory, input digest, result path and SHA. Check its direction, then explicitly inspect and export. Prepare the subsequent reviewer input separately from the complete checked JSON below; it is not passed automatically. Prefer different author and reviewer backends and record a reason for fallback. This entry supports only text-only read-only leaves. Tool restrictions provide no OS isolation or authorization for formal tasks, evaluation or adoption. A general input's task body has no common project field; selecting a project assigns this run's ownership. Retrospective inspection separately checks its original project declaration.

<a id="在页面检查结果并导出完整候选"></a>
### Inspect results and export complete candidates in the page

In “Retrospective improvement” → “Inspect result and export candidate”, choose the result's direction and enter the complete original input directory/digest and original Agent result file/SHA256, then explicitly inspect. Verify input digest through input rereading above or the original `composition verify-input`; the original model-invocation receipt supplies the result file and SHA. This uses original sources in frozen input, independently of the current evidence selection above.

Inspection displays the complete original request and Agent reply and downloads complete `retrospective-checked.json`. Its digest corresponds to the original input/result/candidate; the downloaded JSON file's digest is separate. Changed sources require another inspection. A null candidate needs no export. Otherwise review the complete candidate first, enter a new export directory and explicitly submit. A Skill directory's final name must equal the candidate name.

Export rechecks the project/input/result/candidate identities selected in that submission, then atomically saves complete files and executable bits. Existing directories are not overwritten, and exporting inside frozen input is refused. On failure or a lost reply, retain the previous directory and do not automatically resend. Inspect an existing target with each direction's original CLI below; do not delete it to force a retry. Export does not import, evaluate or adopt. Continue through the separate explicit operations below.

<a id="生成来源绑定的skill复盘候选"></a>
### Generate a provenance-bound Skill retrospective candidate

Start with a registered project, verifiable handoff package and baseline Skill already imported into that project. `ergora skill list my-project` returns the current `active` name, digest and revision. A first import establishes a baseline, without measuring an improvement. Select complete provenance with the selection JSON above and write a UTF-8 `objective.txt` describing the intended improvement.

```bash
ergora composition install-preset retrospective
```

The new composition root is `ergora-skill-retrospective 1.0.0`, with read-only author `root/propose` and subsequent reviewer `root/review`, defaulting to Codex and Claude Code respectively. Prepare this root's manifest directory through the [complete manifest steps](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录). The grant must explicitly permit reading `workspace`/`definitions`, empty write/network and shell=false, and provide the root's required limits. Import, manifest creation and the preparation below send no model requests.

```bash
ergora retrospective prepare my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --skill SKILL_NAME --digest BASELINE_DIGEST --head-revision HEAD_REVISION --objective ./objective.txt --manifest ./retrospective-manifest --instance root/propose --directory ./retrospective-author-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-author-input --backend codex --mode text-only --timeout 240
```

Preparation checks the complete original provenance and current active Skill in the same project, freezing all UTF-8 files and executable bits, exact digest/head revision, original failures/unknown costs, objective and response schema. Original Skill files total at most 1 MiB; the complete prompt has its own supplied limit. Over-capacity input is explicitly refused: reduce explicit selections or use a smaller Skill, without truncating reference materials. Prepared input retains its original snapshot; new preparation rechecks the current head. prepare/check target read-only leaves returning proposal JSON; a custom leaf and supported backend can also be selected.

The invocation receipt supplies the original `result` file path and `result_sha256`. Retain them, then inspect that original result:

```bash
ergora retrospective check ./retrospective-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./retrospective-checked.json
ergora composition prepare-from-manifest ./retrospective-manifest root/review --task ./retrospective-checked.json --directory ./retrospective-review-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-review-input --backend claude-code --mode text-only --timeout 600
```

The author's ordinary `artifacts.response` must be JSON matching the frozen proposal_schema, including the corresponding provenance SHA, baseline digest/revision, exact selected-material references, negative results, costs/uncertainties and complete standard Skill-file suggestions. With insufficient evidence, it can return `candidate:null`. Inspection returns the complete original request and Agent result, checking portable paths, metadata, directory-content identity and references. It operates offline without creating State, and remains possible if the source package or original Skill is later lost. `quality_evaluated:false`, `adoption_authorized:false` and `origin_authenticated:false` remain explicit: structural linkage is not quality evidence.

check reads at most 8 MiB of the original result, allowing nested JSON escaping of complete files in the response string. The reviewer explicitly receives the complete checked JSON through the original composition preparation command above. This preset's review leaf returns a textual review; do not call retrospective check on it. The complete subsequent prompt must independently pass the original capacity gate. Offline inspection of a large result does not mean it fits any subsequent prompt. Static depends_on does not execute ports automatically. Choose other supported backends through the original `composition run-input`, preferably separating author and reviewer. If Claude is unavailable, explicitly select Codex and record `--backend-reason`; same-backend fallback is not different-backend success. If inspection or a model call fails, retain the original input, run and reply before proceeding, without automatic resubmission. Original Agent records remain authoritative for invocation facts.

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

Fill the placeholders with the exact suite digest/run IDs returned by register and both runs. compare's eligible flag, complete trusted evidence, current head and explicit reason together determine adoption. A changed head causes the original adoption to refuse; choose the current baseline and evaluate again rather than changing only revision to force an old result. rollback uses the head revision after adoption, appending history without deleting candidates or old evaluations. A null candidate requires no export or fabricated improvement. See [Skill candidate evaluation and adoption](INTEGRATIONS.md#skill-候选评价与采用) for the complete suite contract.

<a id="生成来源绑定的记忆复盘候选"></a>
### Generate a provenance-bound memory retrospective candidate

Prepare memory suggestions using the same project's complete handoff package and selection. Install `memory-retrospective`, then use the [manifest steps](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录) to pin root `ergora-memory-retrospective 1.0.0` into `memory-retrospective-manifest`. Its `root/propose` and `root/review` default to Codex and Claude respectively. Permissions and explicit invocation follow the preceding steps; all leaves read all ancestor materials.

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
ergora composition run-input my-project ./memory-review-input --backend claude-code --mode text-only --timeout 600
```

The author supplies a complete candidate body (at most 100000 characters), hypothesis, applicability and validation plan under the frozen schema, or returns null. Original failures, unknown costs and exact material references for each observation remain. The model cannot choose provenance, expiry or revision. check's `save` contains only the complete body usable by the original memory interface, fixed provenance derived from package SHA and selection SHA, and original ID/expected_revision. candidate_digest binds complete save content and baseline identity. Offline inspection creates no State, queries no live memory and authenticates no source author; it establishes neither current validity nor quality improvement. The original result limit is 8 MiB, and the complete review prompt has a separate capacity check. If a backend is unavailable, use the explicit fallback and reason from the preceding section.

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

<a id="网页证据预算与交接"></a>
### Web evidence, budgets and handoff

For a formal task, first “Read original run”, then select “Evidence, budget and handoff” on the closed original run. Opening the window does not request an index or materials. “Read evidence index” checks original materials together and displays the original outcome, completeness, external-protocol confirmation and lease facts. Budget and usage retain original sources and units. Unrecorded model calls, tokens and costs remain unknown; an actual zero remains zero. Frozen waiting limits are not process or cost limits. Missing context relationships are not backfilled from current configuration.

The original job directory displays 20 entries per page. “Original job receipts and materials” reuses the original receipt window; select and explicitly read text there. Indexes, complete contracts and material content are displayed as text. Failed rereading retains the previous observation and marks failure. Closing and reopening starts empty, without automatic polling, retries or body prefetching.

“Collect and download handoff package” needs no prior index read. The page calls the POST interface above, checks actual response bytes and digest headers, then gives the bytes to the browser for saving. A success message does not prove a file reached disk; check browser downloads and the save location. The page displays full-package SHA, bytes and an `ergora handoff verify` command. Independently verify provenance, original outcome and candidate. Both server and browser buffer package bytes; download is not streaming. Failure does not trigger this download; any older download information describes only a previous operation.

Closing/replacing the window, editing the run or switching task/project prevents late indexes from updating the page and late packages from triggering a download. It does not revoke a read-only collection the server has already sent. A busy window prevents concurrent reads/downloads. These operations do not automatically start services, workers or models, publish a fence, release a lease, approve a candidate or rewrite the original cancellation result.

<a id="核对闭合运行的外部作业证据"></a>
### Check external-job evidence for a closed run

For a task created through the unified entry point with its original submission receipt saved, use the fixed original run to read complete history, original job requests, trusted terminal receipts and an existing fence:

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
```

API: `GET /api/projects/PROJECT_ID/tasks/TASK_ID/external-status?run_id=RUN_ID&timeout=20`. The original run must be closed and still the latest run of that workflow ID; continued-as-new and other subsequent runs are unsupported. Use the registered complete Linux/WSL2 runtime. The budget is 1–60 seconds, with another 5 seconds for the parent process and separate local contract preflight.

`original_outcome` retains the original workflow outcome; it is null when a failed, cancelled, terminated or timed-out Temporal run has no result. `jobs` lists original-history jobs with request/receipt status and digests. `unresolved_jobs` includes missing requests, missing or damaged receipts, extra requests and orphan receipts. Wrong roots, conflicting requests, wrong fences or incomplete history are explicitly refused. Only the requests/receipts/artifacts/approvals/fences layout inside the registered execution-state directory is supported.

`external_confirmed` is true only when every request and trusted terminal receipt matches complete history, no extra job exists and the correct fence is already present. Both requests and receipts job directories are checked. An orphan receipt that cannot bind to original history cannot be confirmed. FAILED/CANCELLED receipts also establish external-job termination; they do not establish successful development. This is a current snapshot of a trusted-file protocol, relying on the executor to publish receipts and honor fences under the original protocol. It does not replace OS process checks. A missing directory cannot turn known historical jobs into a zero-job pass.

The query saves no tool-run record, publishes no fence and releases no lease: `lease_released_by_operation: false`, `execution_success: null`. CLI exit 0 means only that the query succeeded; inspect external_confirmed and unresolved entries. If unconfirmed, retain the original task, run directory and lease, and complete evidence using the original IDs first.

<a id="正常任务完成后的关闭"></a>
### Close after normal task completion

`REVIEW_READY` means the original candidate passed the workflow's required validation and review. Closing a workflow does not automatically release an issue lease. To adopt the candidate, explicitly [export it](#导出精确候选与恢复回执) and check the receipt; that entry releases applicable leases under the original rules. If not exporting yet or only ending this task, first check evidence and explicitly reconcile:

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
ergora task reconcile my-project TASK_ID --revision CURRENT_REVISION --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
```

First confirm that the original run is closed, original jobs and trusted terminal receipts/artifacts are complete, and no extra or unresolved job remains. Without the correct fence, an initial read-only external_confirmed check may still be false; it publishes no fence and releases no lease. Only explicit reconcile establishes the original execution fence, rechecks facts and releases the exact claim. Missing evidence remains unknown. Verify stopped external processes through the actual executor; trusted-file receipts cannot replace OS checks.

Reconciliation retains normal REVIEW_READY and the exact candidate, without merging or deleting branches. The same candidate can still be exported explicitly afterward. Only reconciled means this lease release and receipt have been saved; recover interruptions through the original intent below. Downloading a handoff package, closing browser/HTTP or stopping services does not release a lease. Before stopping a shared stack, check its projects' in-flight tasks and external jobs individually, then [manage services](#显式服务管理) to exit and back up persistent directories.

<a id="显式终态对账与工单租约释放"></a>
### Explicitly reconcile terminal state and release issue leases

After the original run closes, use the current project revision and fixed original run to explicitly authorize the fence and external-cleanup checks:

```bash
ergora task reconcile my-project TASK_ID --revision 1 --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
# After interruption or completing original trusted receipts, resume with the original intent_sha256 returned above:
ergora task resume-reconcile my-project TASK_ID --revision 1 --intent-sha256 RECONCILIATION_SHA --confirm --timeout 20
```

This only takes responsibility for tasks created through this control directory's unified entry point, with original submission receipts and original `local-cli` issue ownership retained. Before and after reconciliation, verify the original run is still current, complete original history and the registered adapter directory. Extra requests/orphan receipts block taking over that scope. After publishing the original immutable fence, confirm every historical job's original request, trusted terminal receipt and hashed artifacts. Missing/damaged evidence remains unknown and retains the lease. Trusted executors must still honor fences and independent walltime. This file-protocol evidence does not replace a system process scan. All coordinators must keep task IDs nonreusable and must not start a new run for the same task outside the protocol.

`reconciliation` reads only local records, without querying remotely, publishing a fence or releasing a lease. `prepared` has no saved write-ahead checkpoint. `unknown` has saved original outcome/history identities but incomplete cleanup evidence. `confirmed` has saved cleanup evidence but no saved release receipt. Only `reconciled` means the lease was released for the exact original claim and its receipt saved. Recovery revalidates original facts and advances idempotently with the same fence/evidence digests. Repeating reconcile returns saved state; only explicit resume-reconcile continues an unfinished operation. A completed receipt is historical fact; use external-status for live external state.

`original_outcome` retains the actual original result. Even if it was CANCEL_UNCONFIRMED, confirmed cleanup does not change it to BLOCKED or successful development. `execution_success: null` makes no claim about candidate acceptance. Preserve the original outcome digest when native release applies; other closed-run cleanup uses a separate cleanup-evidence digest. Do not manually edit owners/ledgers or delete evidence to bypass conflicts. A mutating CLI returns 0 only for reconciled; HTTP success also requires checking status.

API: GET `.../tasks/TASK_ID/reconciliation`, POST `.../tasks/TASK_ID/reconcile` (`revision/run_id/confirm/timeout`), POST `.../tasks/TASK_ID/resume-reconcile` (`revision/intent_sha256/confirm/timeout`). confirm must be exactly true. Mutations retain same-origin protection and `X-Ergora-Request: 1`. Linux/WSL2 uses the registered complete runtime. Each stage allows 1–60 seconds, with another 5 for the parent and separate local preflight. The original task lock protects that task; remote phases hold no control-database write lock.

Back up execution-state files `ergora/task-reconciliations/TASK_ID.{intent,attempt,evidence,result}.json` together with the original task/creation/submission, requests/receipts/artifacts/fence and `ingress/leases.sqlite3`. Missing evidence or a database retains unknown state; a new ledger must not reconstruct ownership.

<a id="导出精确候选与恢复回执"></a>
### Export an exact candidate and recover its receipt

This applies only to unified-entry tasks with saved submission receipts. First use `task status --run-id RUN_ID` to confirm the original run finished with outcome `REVIEW_READY`. Review its exact candidate and trusted-check/independent-review evidence, then explicitly specify a local target branch:

```bash
ergora task export my-project TASK_ID --revision 1 --run-id RUN_ID --candidate-sha CANDIDATE_SHA --branch agent/TASK_ID --confirm --timeout 20
ergora task export-status my-project TASK_ID
# After interruption, read export-status first; resume with original intent_sha256 and current project revision:
ergora task resume-export my-project TASK_ID --revision 1 --intent-sha256 EXPORT_SHA --confirm --timeout 20
```

One task saves one immutable export target. Repeated export returns its original record, without changing run, candidate or branch. `prepared` means no write-ahead checkpoint exists; explicit resume can continue. `unknown` means the original result digest was saved; recovery only checks the original run/outcome and actual branch, without refetching or creating it. A missing branch returns `unknown/branch_not_found`, avoiding resurrection of a manually deleted branch. Retain the original record and reconcile manually. An existing branch pointing elsewhere, changed original result or conflicting record is explicitly refused.

Git fetches objects without writing FETCH_HEAD, checking out, merging or pushing. A Git conditional transaction creates the target branch. An existing exact-candidate branch is accepted; other branches and symbolic refs remain unchanged. After confirming the branch, release applicable issue leases through the original rules and save the original `tasks/TASK_ID/export.json` format and this tool's receipt. `exported` means that export fact has been saved, with `checked_out: false`, `merged: false`; later review and integration follow project policy. Reading a repeated terminal result does not live-check subsequent manual branch edits.

`export-status` reads only local records, without connecting to Temporal or releasing leases. Intent, write-ahead checkpoint and receipt live at `ergora/task-exports/TASK_ID.{intent,attempt,result}.json` in execution state. Back them up together with original creation, submission, task, workspace and lease records; a control database alone is insufficient. Preparation strictly checks current revision/confirm and acquires the original task lock nonblockingly. Network/Git phases release the control-database write lock. Each stage has 1–60 seconds, another 5 for the parent and separate preflight. After timeout, read records first and reconcile actual writes through original branches/checkpoints. Linux/WSL2 uses the registered complete runtime; exports through the old entry point are not implicitly taken over.

API: GET/POST `.../tasks/TASK_ID/export`; POST body is `revision/run_id/candidate_sha/branch/confirm/timeout`. POST `/resume` under that same path uses `revision/intent_sha256/confirm/timeout`. Mutations retain same-origin protection and `X-Ergora-Request: 1`; confirm must be true. A mutating CLI returns 0 only for exported; HTTP success also requires checking status.

<a id="显式服务管理"></a>
### Manage services explicitly

On Linux/WSL2, first install and initialize the reference runtime and complete [unified project registration](PROJECTS.md). `ergora services` uses registered execution directories and Supervisor in the reference environment without system-service privileges. One execution-state directory is a shared service stack that may serve multiple projects; stopping it affects that stack's in-flight tasks. Replace `--revision 1` below with the current revision from `project show`:

```bash
ergora services status my-project
ergora services start my-project temporal worker --revision 1 --timeout 30
ergora services logs my-project worker --bytes 8192
ergora services stop my-project worker temporal --revision 1 --confirm --timeout 30
ergora services shutdown my-project --revision 1 --confirm --timeout 30
```

The selectable services are `temporal`, `mlflow`, `worker`, `executor`, `a2a`, `training-worker`, `training-budget-worker` and `training-cycle-worker`. Only listed services start; dependencies or research do not start automatically. For a v7 provenance task, explicitly start the original six-stage services with `ergora services start my-project temporal worker executor --revision 1 --timeout 30`. Older v1–v6 installation-level doctor checks additionally require a local A2A listener, so explicitly add `a2a` when needed. Start MLflow separately for observation. The managed executor uses this same Ergora control directory's selective executor. Supervisor `RUNNING` is only process status; service protocols, worker/queues, models and tasks have separate acceptance. stop and shutdown require confirmation. Their 1–60-second control-wait budget starts after registration preflight. `outcome: unconfirmed` means the operation may continue; query status and reconcile. Do not restart until STOPPED is confirmed. Failed/unconfirmed operations return a nonzero CLI status.

The first start creates `ergora-services/` under execution state, recording control-directory ownership, a separate socket and configuration. It copies the original Supervisor program definitions with all autostart disabled; the original ini remains unchanged. An existing original Supervisor socket prevents takeover. First stop and check the original stack with `agentflow services stop`, then use the new entry point. Stale sockets/PIDs also require reconciliation. Registration-projection drift, conflicting control-directory ownership or an overly long Unix socket path explicitly fails; for the last case choose a shorter persistent execution-state directory. Before upgrading software, shutdown the managed stack; explicitly restart it with original arguments after upgrading.

The normal and stop queues of `training-cycle-worker` have separate activity slots. Its PID is separate from the budget service, providing four activity consumers. See [the integrated cycle-service entry](TRAINING.md#独立循环服务的集成入口) for integration scope, explicit start and 70-second stop observation. The complete top-level workflow and automatic multiple rounds have separate delivery.

The default native log-byte window is 8192; select 4–65536 bytes, enough for at least one UTF-8 character. Use returned `next_offset` as the next `--offset`. `overflow` means intervening content exceeded the window. `rotated` means the current file is shorter than the cursor and the window reset; check original logs as well. After querying the actual log path from Supervisor, read only a bounded window of an ordinary file, without loading a large file completely. `limit` constrains raw read bytes; text/JSON output may grow through replacement characters or escaping. Valid UTF-8 boundaries are retained. An incomplete suffix's `pending_bytes` is not yet included in `next_offset`; continue with the original cursor after more bytes arrive. Invalid bytes use replacement characters.

Same-origin API: `GET /api/projects/ID/services`; `POST` at the same path with body `{"action":"start","names":["temporal"],"revision":1,"timeout":30}`. Add `"confirm":true` for stop; shutdown uses empty names. Mutations retain `X-Ergora-Request: 1`. `GET /api/projects/ID/services/NAME/logs?limit=8192&offset=0&stderr=false` returns bounded text and a cursor. Native Windows supports the console, while local Supervisor management requires WSL2/Linux.

Equivalent project/Agent CLI:

```bash
ergora project add my-project --repo "$HOME/projects/my-project"
ergora project show my-project
ergora project config my-project
ergora tools list
ergora tools doctor my-project
# JSON example:{"tool":"codex","model":"YOUR_MODEL_ID"}
ergora project bind my-project reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run my-project reviewer --prompt review-request.md --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

Pages and CLI share persistent business state. Refresh before saving after revision conflicts. An Agent call's `succeeded` is not formal-task acceptance or review approval. The default reference executor retains its original configuration. Explicitly enable bridging when selected role tools should affect formal tasks; see [Agent selection and formal execution](AGENT_BACKENDS.md).

<a id="有效绑定与运行快照"></a>
## Effective bindings and run snapshots

`ergora project config PROJECT_ID` and `GET /api/projects/PROJECT_ID/configuration` return the same read-only result. `project show` still returns the saved original document. A lightweight project's effective view uses `schema_version: 1`, `resolution_version: 1` and `scope: project-bindings`. A unified registered project uses `scope: registered-project` and includes the normalized definition, digest and publication status in `registration`, covering templates, execution directories and checks/policies. Template inputs, tool-internal defaults, authentication and service connections remain owned by their respective entry points. See [project definitions](PROJECTS.md) for unified registration, read-only preview/explicit import of legacy registrations and recovery commands.

`project` contains ID, Git root and current revision. Each `layers` entry has `binding`, `source` and `validation`. Source `project` identifies a saved field. `inherited` means an old project missing a role inherits `bindings.implementer`. `legacy-default` means a missing support layer uses a fixed compatibility default: memory=sqlite, research=urls, other support layers=manual. New projects still save the complete recommended bindings in effect at creation.

`sha256` is computed after removing itself, using UTF-8 JSON with sorted keys, compact separators, preserved Unicode and nonfinite numbers refused. It identifies this view's content and cannot replace evidence digests for formal tasks, artifacts or trusted checks. View validation invokes no tools. Invalid inheritance reports the exact layer error; explicitly save a compatible binding. Check authentication and availability separately through doctor.

A standalone Agent call saves this view as `configuration` in its run record before starting the tool, retaining original `binding/project_revision`. Formal tasks created through the primary entry point freeze the view at creation. Older creation paths add it to `agent-bindings.json` when first using the optional executor. Later project or recommended-default changes do not update in-flight tasks. Older tasks without the extra field continue using their original binding snapshot, without fabricating historical provenance; old run records are not rewritten. Actual Skill/memory context is recorded separately in invocation records. This snapshot does not claim to freeze all external tools' internal behavior.

<a id="记忆有效期与检索"></a>
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

<a id="页面操作"></a>
## Use the pages

1. **Project overview** shows actual memory, Skills, source proposals and tool calls. Invoke a selected role once, optionally including active Skills, project-memory retrieval and template artifact requirements. Records preview stdout/diagnostics up to 64 KiB per stream; complete files remain in persistent run archives. The fixed six-stage diagram describes the protocol, without inventing task state.
2. **Long-term memory** saves bodies, source URI/revision and optional expiry. A UTF-8 body file preserves a candidate's original text. Corrections prefill original expiry; explicitly clearing it removes expiry. Unedited bodies retain original newlines. The default view shows valid snapshots only. “Read all states” displays expired/deleted records and the server's observation time. An empty query rereads the valid list. History restoration selects one original revision and appends a restored revision with original expiry; deletion is irreversible. Save/restore/delete/projection synchronization show complete receipts only in the submitting form; explicitly refresh afterward to read state. On an abnormal reply, check the original record first. See [candidate saving](#生成来源绑定的记忆复盘候选) and [expiry](#记忆有效期与检索).
3. **Skill evolution** imports complete standard directories. The first version establishes an initial baseline; subsequent imports are candidates. Compare file/text differences, register a trusted suite, run both evaluations and compare. After passing the gate, give an adoption reason. A formerly active version can be restored with a rollback reason. GEPA searches candidates without automatically adopting them.
4. **Source observation** takes URLs and total byte/time budgets. Changed content creates proposals for review; bodies display as text. Reviewing does not automatically write memory or alter Skills. Refresh the list during execution, request cancellation and confirm the actual terminal state. An unresolved transfer after abnormal exit may conservatively exhaust the budget, requiring an explicitly created new observation task.
5. **Workflow design** provides governance and large-development work-unit DAGs. Edit dependencies, paths and descriptions, or load complete JSON. The server uses the original contract compiler to reject cycles, conflicts and invalid scopes. Saving produces a persistent draft. After downloading `input.json`, continue through reference-task freezing and execution. The training template previews/downloads workload/experiment files; copy complete directories through the CLI.

The Skill page accepts [complete directories exported from retrospective candidates](#生成来源绑定的skill复盘候选). In “Import directory”, enter its path on the console machine and check the complete response. Close the window and use “Refresh” at the upper right to read registered versions. Select baseline, candidate and a maintainer-registered trusted suite, and explicitly run each evaluation. Both buttons share a project/control-directory-specific in-flight lock in this window. Switching tabs or refreshing within the page does not release it. Complete original records display the submitted digest/suite and each case result. After refreshing, select those exact two run IDs, then “Compare evaluation evidence”. Changes to version, suite or run remove old comparison/adoption forms and require another comparison. Current version/suite selection supplies the next evaluation only. Adoption consumes the two selected original evaluation records and displayed head revision; review actual identities in the complete comparison.

eligible only means the original evaluation gate passed. After reviewing complete evidence/head revision and entering a reason, explicitly “Adopt candidate”. The server rechecks suite, provenance and concurrent head. After the original result, explicitly refresh and check active revision/version lists. To roll back, choose “Roll back to this version” beside a formerly active version, check digest/revision and submit a reason, then refresh and read back. Import, completed evaluation, a passed gate, adoption and rollback keep their separate semantics.

After import, suite registration, adoption, rollback or GEPA submission, the current form becomes a complete request/result receipt without automatic resubmission or window closing. On an abnormal evaluation/write reply, first refresh and check original evaluations, versions and history. An uncertain evaluation reply keeps this window's project evaluation locked; after checking, explicitly select “Original records checked; allow a new evaluation”. Reloading the browser discards temporary UI locks, while the original request may still execute: check original records first. Replies may be lost after an operation executed. After leaving the original page or closing/replacing the window, late replies do not open windows, notify or refresh a later page. Original operations may still finish; return to the original project to read their records. Receipts are not stored across page reloads; use persistent original records and the CLI to reconcile.

<a id="编辑工作单元草稿"></a>
### Edit work-unit drafts

After loading a governance or large-development template, edit unit ID, dependencies, writable paths and task description in the form, then “Update unit draft”. Alternatively edit complete JSON and “Validate and load JSON”. Unapplied form and JSON text remain separate; neither directly overwrites unapplied text in the other. While unapplied text exists, save/download/add/delete/undo are disabled. Switch units to continue editing or explicitly discard the corresponding text. The original contract compiler validates JSON and final saves; graphical operations cannot grant extra permissions.

Renaming updates dependency references. Add/delete/form-apply/JSON-apply support undo/redo. History retains up to 50 snapshots totaling 4 MiB on this page, evicting oldest snapshots when over budget. If one input alone exceeds the budget, only that current input remains. Reopening preserves the current buffer and rebuilds history. Drag positions, zoom and viewport are saved separately from task JSON; “Rearrange” changes display only.

After changing draft ID, save as a new draft. To modify an existing draft, open it from “Saved drafts” first. The page uses only the loaded target revision or one returned by this session's save receipt, without automatically adopting revisions from a refreshed list. On conflict, retain edits, copy/download anything to preserve, then explicitly reload. Typing during saving retains newer text; a late reply records only the original submitted snapshot's save fact.

Browser buffers are separate by control directory and project. Editing can continue across page/project switches and refreshes. Retention after closing a browser depends on session-restore settings; explicitly “Save draft” for long-term storage. A browser-storage quota warning means retain the page and copy unfinished text, including invalid JSON. For a damaged buffer, use “Download raw buffer” and “Explicitly clear browser buffer”; preserve the original before clearing. Loading a template or saved draft asks before replacing unsaved changes. Editing, saving and downloading do not start formal tasks automatically.

See [integrations](INTEGRATIONS.md) for complete evaluator/proposer JSON protocols, source snapshots and ReMe/Temporal configuration.

<a id="三个模板与正式任务"></a>
## The three templates and formal tasks

```bash
ergora templates list
ergora templates copy repository-governance ./governance-task
ergora templates copy large-change ./development-task
ergora templates copy training-optimization ./training-task
ergora workflow --help
ergora reference verify
ergora reference info
```

The copy destination must be new. Templates define task and evidence requirements. Example PASS values, SHAs and metrics are not actual results. Governance and large development retain `inventory → plan → work → integrate → verify → review`; the complete reference runtime still owns plan approval and final evidence.

For Temporal, MLflow, Symphony, A2A, Supervisor and the complete executor, use the [single-file installation distribution](distribution/multi-agent-development-platform.html) or installer supplied through packaged reference entry points. The HTML embeds complete install scripts, source ZIP, three templates and two complete reference manuals. It targets Ubuntu 24.04 / Linux x86_64; installation requires network access and package-manager privileges inside the target system.

- [Complete deployment and daily-use reference](../src/ergora/data/reference/platform/README.zh-CN.md)
- [Complete training-optimization reference](../src/ergora/data/reference/platform/docs/TRAINING.md)
- [Training through the new entry point](TRAINING.md)

These frozen reference files retain v2.2 content identity for verification. This guide and the integration guide describe new control-plane capabilities; they do not rewrite the old HTML's embedded package. Configure Temporal in the current shell before using the local reference-task CLI; see [a first development task](../README.md#首个开发任务).

<a id="远程访问恢复与维护"></a>
## Remote access, recovery and maintenance

The service listens on loopback only. From another machine, use SSH forwarding and open local `http://127.0.0.1:8977`:

```bash
ssh -L 8977:127.0.0.1:8977 user@server
```

Local interfaces require the same origin and custom request header and validate Host. They operate with current-user permissions for trusted projects. Team identity, public hosting and per-Agent OS isolation require separate integrations. If a container cannot provide a namespace sandbox, the application does not automatically disable an Agent's sandbox to make invocation succeed.

The application runs in the foreground. On Linux/WSL2, Supervisor can manage `ergora serve` and each project's `ergora research worker PROJECT`; start with foreground terminals on native Windows. Installation does not automatically execute background tasks, invoke models or start research. After stopping writers, back up complete `ERGORA_HOME` and business Git repositories. During restoration, check actual repository paths and tool logins. Deleting memory does not clear independent backups or past archived invocation inputs.

When developing or resuming on another machine, read [PLAN.md](PLAN.md) and the active slice's `docs/delivery/` record, then check branch, `git status` and recent commits. Default tests do not call paid models; acceptance of external services and GPU results is recorded separately.

<a id="可嵌套工作流定义"></a>
## Nested workflow definitions

The basic installation uses `ergora composition` to inspect, import, share and preview versioned Agent/subworkflow DAGs. A leaf preview includes all ancestor static materials, permission chains, named ports and global budgets. See [workflow composition](WORKFLOW_DEFINITIONS.md) for examples, operation sequence and scope. Static preview starts no Agent; formal execution retains the original six-stage approval workflow.

<a id="在页面浏览与预览定义"></a>
### Browse and preview definitions in the page

Start `ergora serve` and open “Agent and composition library” without first registering a project. These libraries belong to the current persistent control directory; switching projects does not change them.

1. Explicitly import a desired composition under “Built-in domain compositions”. Reimporting the same version retains the same identity. Governance, large development and training proposals can be imported independently.
2. Select an exact version in the Agent/subworkflow list. Details display the standard definition, complete own resources, package-file identities and default-backend request. Share complete Skill-attachment packages with CLI `export`; the page's downloaded “Definition JSON” contains only the definition body and cannot replace a complete package.
3. After selecting a workflow, inspect “Static preview limits JSON”, then “Preview complete composition”. Initial values come from the root definition; edits affect this static validation only and grant no project permissions. Errors appear on the page while edited text remains available.
4. Select an instance in the published nested graph, or use the instance-table buttons by keyboard, to inspect complete ancestor resources, sources, permissions, ports, budgets and assembly hints. Nested boxes, dashed dependencies and blue named data represent three relationships. Full paths distinguish repeated references. “Open selected exact definition” and “Open structural parent definition” return to the corresponding editor. Download exact preview JSON for inspection/comparison.
5. After review, “Save current preview as complete manifest” saves this root and every definition/Skill attachment to persistent control storage. Returned `path` and `digest` can be formal-task definition inputs. Saving creates or starts no task. On a lost reply, first “Read saved package by current digest”. If the source library is unavailable, independently verify with `ergora composition show-manifest PREVIEW_SHA256`; see the [complete steps](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录).

Import does not install/authenticate backends or start tasks/services. Preview backend fields are requests; actual calls still require capability admission and authentication. After choosing an exact version, edit fields or JSON/YAML in “Edit definition and derive new version”, then explicitly apply, check and publish a revision. Original attachments and old versions remain. See [Agent editing](AGENT_DEFINITIONS.md#在页面编辑专长-agent) and [workflow revisions](WORKFLOW_DEFINITIONS.md#在页面修订工作流) for complete steps and browser-buffer limits. The graph shows published versions; drafts do not enter automatically. Collapse subworkflows independently, search by responsibility/specialty/backend and expand ancestors to locate results. Summary edges trace back to complete original endpoints. Layout/collapse/search are separate from contracts and reset on refresh; the table remains available if graphical components are missing. See the [relationship graph](WORKFLOW_DEFINITIONS.md#查看已发布嵌套关系图). With a comparison target selected, [compare two published compositions](WORKFLOW_DEFINITIONS.md#比较两个已发布组合) using the same explicit limits, checking reference/permission/material differences per path and downloading both complete previews. Save a complete manifest here, then [select it on the task page](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合) to read the original digest, assign work units and set per-instance backends. The native six-stage entry also configures inventory/planning Agents and budget; explicitly authorize preparation before previewing and creating. Original project-role entry points remain available.

Use [CLI resource revisions](AGENT_DEFINITIONS.md#修订完整资源文件) to modify instructions/context, complete Skill directories and ordinary attachments: pin the original package, preview complete differences and suggested digest, explicitly accept that same candidate, then check/publish a version. Both definition kinds share this contract. Binary files, executable bits and empty directories remain explicit; historical files support byte-window reads. The page's “Resource and attachment editing” can also read/upload complete files, stage operations, preview differences and explicitly accept the digest before check/publish; see the [page resource steps](AGENT_DEFINITIONS.md#在页面编辑资源与附件). Bodies, operations and accepted identity enter history together. Unapplied bytes remain separate; a downloaded editing buffer excludes unedited original package content.

When changing nested compositions, follow the [dependency-chain steps](WORKFLOW_DEFINITIONS.md#沿完整依赖链发布资源修订): publish specialists/subworkflows before the new root. Prepare new input from that root; old snapshots retain old materials. To establish that attachments actually reached the model, check this invocation's original list/read evidence through [complete-read verification](WORKFLOW_DEFINITIONS.md#核验完整附件读取).

<a id="导入领域专家组合"></a>
## Import domain-specialist compositions

The basic installation includes default specialist/subworkflow packages for governance, large development and training proposals. Run `ergora composition presets` to inspect actual scope and `ergora composition install-preset large-change` to import every exact dependency. See [built-in domain compositions](WORKFLOW_DEFINITIONS.md#使用内置领域组合) for details, node relationships, independent backend selection and sharing. Static import chooses no trusted container, starts no services and approves no task. Formal development follows the original task workflow above; training proposals and [trusted experiment execution](TRAINING.md) remain separate.

For parent/child permission changes, follow [joint revisions](WORKFLOW_DEFINITIONS.md#联合修订父子权限), publishing versions from inner definitions to root, then provide an explicit grant and check actual invocation capabilities. Parallel instances of the same specialist need distinct node IDs and a complete all-join. Different review responsibilities require a new subtemplate version; see [repeated instances and backend selection](WORKFLOW_DEFINITIONS.md#重复实例职责和后端选择).

<a id="在页面导入完整工作流目录"></a>
### Import a complete workflow directory in the page

In “Agent and composition library”, select “Import workflow directory”. Enter the directory on the console machine containing `workflow.json` and all own resources; a retrospective export directory from the next section is suitable. Check the displayed control directory and explicitly submit. The library is shared in this control directory without depending on the current project. The receipt contains original ID/version/digest, definition and resource-file identities. Retain it, close the window, “Refresh definition library” on this page, then select the receipt's exact version. The global “Refresh” at the top does not reread the definition list.

Identical content/version retains the same identity. Different content at the same version is refused; select a new version. Import publishes only this root package, so import Agent/subworkflow dependencies beforehand. Original import/preview checks complete references, ancestor resources and permissions. After selecting a new version, preview under the original limits above and explicitly save a new manifest. To roll back, select the original version/manifest again; old tasks retain original materials. Import does not automatically select a new version, preview, save or execute.

An abnormal request may have executed. First refresh the library and select original ID/version to check its digest, or read its original package with `ergora composition show WORKFLOW_ID VERSION --material`. Do not delete original records to force retries. After closing the window or leaving its source page, late replies do not manipulate subsequent windows. Reopening requires checking original records again. The HTTP equivalent is `POST /api/workflow-definitions/import` with `{"directory":"/path/to/workflow-bundle"}`, retaining same-origin protection and `X-Ergora-Request: 1`.

<a id="生成来源绑定的工作流复盘候选"></a>
### Generate a provenance-bound workflow retrospective candidate

Install `workflow-retrospective`, then follow the [complete manifest steps](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录) to save root `ergora-workflow-retrospective 1.0.0` into `workflow-retrospective-manifest`. Separately save complete `target-manifest` for the root to improve, retaining the complete digest from its original check. The first is the author/reviewer graph; the second is the target graph. Prepare handoff, selection and objective through the [Skill-candidate steps](#生成来源绑定的skill复盘候选), all from the same project.

```bash
ergora composition install-preset workflow-retrospective
ergora retrospective prepare-workflow my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --target-manifest ./target-manifest --target-digest TARGET_MANIFEST_DIGEST --next-version 1.0.1 --objective ./objective.txt --manifest ./workflow-retrospective-manifest --instance root/propose --directory ./workflow-author-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-author-input --backend codex --mode text-only --timeout 240
```

`--next-version` must name an unused immutable root version; existing versions cannot be overwritten. The target package's complete recursive definitions, resource bodies, executable bits and directories, including empty directories, are frozen. Files total at most 1 MiB. Binary, NUL or over-limit content is refused without truncation. target-digest uses the original manifest's file/executable-bit identity; frozen baseline.digest additionally binds complete directories. The export receipt retains both identities and directories. Once preparation succeeds, loss of target sources does not prevent offline inspection. Total prompt capacity remains separate; set `--max-prompt-bytes` for the actual backend's limits.

```bash
ergora retrospective check-workflow ./workflow-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./workflow-checked.json
ergora composition prepare-from-manifest ./workflow-retrospective-manifest root/review --task ./workflow-checked.json --directory ./workflow-review-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-review-input --backend claude-code --mode text-only --timeout 600
```

Author and reviewer read complete ancestor materials and predecessors. Backend selection/failure preservation follows Skill candidates above; static dependencies do not execute ports automatically. Inspection permits `candidate:null`. Otherwise it checks original preview, complete resources, graph and original grant, writing only in an automatically cleaned private temporary directory without reading/writing active State. The first version permits only root description, NUL-free UTF-8 content in already-declared resources and extra dependency edges. It preserves original nodes/references/ports/permissions/review requirements and existing dependencies. Change those structures through original manual version revisions.

After checking complete `revision_preview` and provenance, explicitly select the `candidate_digest` returned by check. A missing candidate cannot be exported.

```bash
ergora retrospective export-workflow ./workflow-author-input AUTHOR_RESULT ./candidates/workflow-root --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST > ./workflow-export-receipt.json
ergora composition check ./candidates/workflow-root
ergora composition import ./candidates/workflow-root
```

The export directory must be new and preserves the complete root bundle and reference identities. Save the stdout receipt separately; no extra receipt is inserted into the directory to contaminate package identity. Another machine must first have the same subdefinitions; original import checks dependencies and ID/version conflicts. After importing, prepare a manifest for the new version through the original steps and explicitly select it. For rollback, select the original root/manifest again; old runs always retain old snapshots. Export, model approval and graph admission do not establish quality/performance evaluation or authorize adoption. Effect comparisons still require the same trusted workload and independent validation.
