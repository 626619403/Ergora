# Back up and recover the local task stack

English · [简体中文](zh-CN/BACKUP_RECOVERY.md) · [Documentation](README.md)

<a id="本地任务栈的备份与恢复"></a>

Complete task recovery requires the control home, execution configuration/state, Temporal database and business Git repositories from the same offline window. `ergora state backup` covers only the control home. It does not back up execution data registered elsewhere or stop services. This recipe combines the existing control backup commands with GNU tar on Linux.

<a id="先确定范围并停止写入"></a>
## Identify the scope and stop writers

Set `CONTROL` below to the original data home's actual absolute path. Run `ergora --home "$CONTROL" project show PROJECT` and record the project revision, repository, and `registration.definition.execution` fields `installation`, `config_directory` and `state_directory`. Include every project sharing that stack. Separately record the Ergora source/version, Python/dependency versions, tool versions and available authentication methods. Manage credentials privately; keep them out of Git and public reports.

Inspect each original task/run with `ergora --home "$CONTROL" task status PROJECT TASK --run-id ORIGINAL_RUN`. `ergora --home "$CONTROL" task external-status PROJECT TASK --run-id ORIGINAL_RUN` accepts only a closed original run; use it to inspect unresolved external jobs. For running or unknown tasks, retain the original intent and follow cancellation/recovery. A failed external query does not prove a stopped job. Stopping services does not release leases or establish that external jobs ended. Preserve `CANCEL_UNCONFIRMED` and unknown; use the [cancellation/reconciliation instructions](USAGE.md#请求取消与恢复未知投递) when needed. Stop the console, research workers, training and all other writers, then use the [public services interface](USAGE.md#显式服务管理) to stop only the stack covered by this backup.

Replace these variables with the actual registered absolute paths. This example assumes disjoint directories; enumerate every directory for multiple projects/stacks and remove overlaps. Keep the backup outside those directories and outside temporary storage subject to cleanup.

```bash
CONTROL="$HOME/.local/share/ergora"
CONFIG="$HOME/ergora-local/config"
STATE="$HOME/ergora-local/state"
INSTALLATION="$HOME/ergora-local/installation"
REPO="$HOME/project/my-project"
BACKUP="$HOME/ergora-backups/snapshot-001"
```

|Location|Required recovery content|
|---|---|
|Control home|Control SQLite, project registration/history, Skill/Agent/Workflow assets, source and invocation snapshots; `state backup` checks its manifest and domain identities|
|`CONFIG`|Complete project, adapter, permission, backend and service configuration; preserve private configuration and authentication references|
|`STATE`|`tasks/`, `ergora/task-*` intents/attempts/receipts/reconciliation, original request roots/receipts/artifacts/approvals/fences, all ledgers, Temporal database/sidecars, workspaces, mirrors, process records and logs|
|Business Git repository|Complete `.git` and working tree, including uncommitted files; a remote or `git bundle --all` alone cannot preserve all runtime workspaces|
|Execution installation and dependencies|Compatible reference/Ergora, original interpreter/venv and tool binaries; symbolic links preserve the link, so save their targets separately or ensure restoration at the original paths|

Git worktrees may refer to a mirror in the original `STATE` through absolute paths. Include other repositories, external Git directories, LFS objects and tool runtime data according to the actual dependencies. Do not dereference links and replace the original workspace structure while backing up.

<a id="生成并核对离线副本"></a>
## Create and verify the offline copy

After confirming services and external jobs have stopped, run these commands in one terminal. GNU tar preserves files, file/directory modes, directories and symbolic-link targets; Linux does not use symbolic-link mode bits to authorize access. This recipe does not promise ACL/extended-attribute preservation, cross-platform recovery or a consistent online multi-database snapshot.

```bash
umask 077
mkdir -p "$(dirname "$BACKUP")"
mkdir "$BACKUP"
ergora --home "$CONTROL" state backup "$BACKUP/control" --offline
ergora --home "$CONTROL" state verify-backup "$BACKUP/control"

tar --create --preserve-permissions --file "$BACKUP/execution.tar" \
  --directory / -- "${CONFIG#/}" "${STATE#/}" \
  "${INSTALLATION#/}" "${REPO#/}"
tar --compare --file "$BACKUP/execution.tar" --directory /
(cd "$BACKUP" && sha256sum execution.tar > execution.tar.sha256)
```

Stop on any failure. Do not move original directories or claim a usable backup afterward. `tar --compare` compares the archive with the current original directories; do not restart writers before it. Keep the control command's manifest SHA, and retain the archive SHA plus directory/version inventory in a trusted location. Digests verify transfer integrity; they do not authenticate the backup's origin. Treat backups containing credentials as private files.

<a id="在同平台原路径恢复"></a>
## Restore on the same platform at the original paths

Verify the originals and archive, then move each existing `CONTROL`, `CONFIG`, `STATE`, `INSTALLATION` and `REPO` to a newly created retention location. Preserve all original directories; restoration targets must not exist. A new machine still requires the original absolute paths and matching runtime dependencies: JSON paths are not rewritten. Check symbolic-link interpreter/tool targets and versions first. Do not use `project register` to recreate original tasks or replace missing ownership records with a new ledger.

```bash
ergora --home "$CONTROL" state verify-backup "$BACKUP/control"
(cd "$BACKUP" && sha256sum --check execution.tar.sha256)
```

After preserving the original directories and confirming that every target is absent:

```bash
ergora --home "$CONTROL" state restore "$BACKUP/control" --offline
tar --extract --preserve-permissions --keep-old-files \
  --file "$BACKUP/execution.tar" --directory /
tar --compare --file "$BACKUP/execution.tar" --directory /
```

Extract only a trusted archive you just verified, into paths writable by your current user. `--keep-old-files` fails on an existing file; a failed extraction may leave partial files. Keep services stopped, preserve that state and identify missing items before proceeding. The control-home interface stages, rechecks and publishes without overwriting; it does not make the external tar extraction transactional.

Before startup, inspect project registrations and complete task envelopes, original creation/submission/cancellation/reconciliation records, request/receipt/artifact digests, original owner approvals and leases. Check original candidate SHAs, refs and uncommitted state in every business repository, mirror and worktree; use the original database tools to check SQLite integrity. Logical data and task identities should remain intact; physical database pages or logs after startup may differ.

Start Temporal first with `ergora --home "$CONTROL" services start PROJECT temporal --revision N`, then explicitly start the required workers/other services using the same home. Query every original task/run. Repeating the original `ergora --home "$CONTROL" task start ...` with the same project, task, revision and creation SHA should return the same original run through its submission record rather than create another task. Reconcile unconfirmed external state before further effects. Recovery does not rewrite original outcomes, candidates, approvals or claims. Reopen writers only after checks; never run the retained old stack and restored stack together.

Native Windows control homes can use the [Windows backup commands](WINDOWS.md#升级备份与卸载). The GNU tar/Supervisor full-stack recipe here is for Linux/WSL2. Remote Temporal, MLflow, ReMe, issue systems and path-changing migration require their own recovery procedures and separate acceptance. Explicitly rebuild ReMe's retrieval projection from the control database using the [daily-use guide](USAGE.md#升级与持久数据).
