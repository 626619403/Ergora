# Upgrade or rebuild a persistent installation

English · [Documentation](../README.md) · [简体中文](../zh-CN/install/upgrades.md)

## Upgrades and persistent data

Before upgrading, stop the console, workers, executors and other CLI work, check in-flight task status, and back up the complete persistent directories and business repository. Opening an old control-plane database for the first time upgrades it transactionally and automatically saves a pre-upgrade database snapshot. That snapshot excludes Skills, sources and run files and cannot replace a complete backup. Newer databases reject writes from older applications; rollback requires restoring matching database and files as well as the code. See [Database upgrades](../architecture/state-migrations.md) for specific versions, error handling and rollback steps.

If data already exists, stop the relevant work before running the following commands (see the [Windows guide](windows.md#upgrade-back-up-and-uninstall) for PowerShell path examples):

```bash
ergora state info
ergora state backup "$HOME/ergora-backups/snapshot-001" --offline
ergora state verify-backup "$HOME/ergora-backups/snapshot-001"
```

The backup directory must be a new directory outside the data home. The tool saves a consistent database snapshot, regular files, file modes and empty directories, checks the domain identities of Skill/source snapshots, and returns a manifest SHA. It does not upgrade an old database first; `state info` also does not create a database when no data exists. `--offline` means that you have stopped writers; the tool does not stop services or external jobs for you.

Before restoring, move the existing home elsewhere to retain it, then run `ergora state restore BACKUP_DIRECTORY --offline`; for a custom home, use the global option in `ergora --home ORIGINAL_HOME state restore ...`. The first version requires the same platform and original home, and the target must not exist. It publishes the directory only after verification, copying and a second successful check, without overwriting an existing target. It preserves absolute paths and evidence digests in JSON. Restore and reconcile business repositories and external services separately; ReMe can rebuild its retrieval projection with `ergora memory sync PROJECT --rebuild`.

Installation and data versions are managed separately. The current database schema is 6; even if two applications both report 0.2.0, retain the full source commit, installation profile, interpreter and dependency versions. Keep a copy of both the application and data from before the upgrade: update the application by rerunning the original installer from the selected pinned source; for rollback, use a compatible old application and its corresponding complete state backup. If the new version has produced data, save that state separately first so the old snapshot is not the only copy. The complete application directory may contain interpreter links; a venv directory cannot simply be moved to a new path and reused.

## Move to another machine or rebuild a new project

On the new machine, reinstall from the same branch or pinned commit and prepare Python, Git, Agent authentication and optional services for the selected platform. Use persistent locations for source, application, control home and business Git. Configure the installation locations with `ERGORA_INSTALL_ROOT`/`ERGORA_BIN_DIR`, and runtime data separately with `ERGORA_HOME` or the global `--home` option. If the new environment only needs the control plane, the complete reference stack is not required.

For a new project, follow the [template getting-started journey](../development/templates.md) to register the actual repository path again, select backends, import the exact preset and prepare grants/a complete manifest. The same definition package can retain its version and content digest; the project revision, configuration containing absolute paths and invocation input belong to this new environment. Share the complete definition package and any exact dependencies it needs. Preview JSON downloaded from the page cannot replace the complete manifest. Supply credentials again through tool login or an external environment; configuration stores only variable names.

To continue a historical formal task, follow the [joint backup guide](../operations/backup-recovery.md) to restore the control home, external CONFIG/STATE, compatible application, Temporal database and business Git/worktrees on the same platform at their original absolute paths. Then check the original task/run, candidate, approvals and external jobs. `state backup` covers only the control home; creating a new project or running register again does not restore the original run identity. Acceptance of a local rollback with matching application/state also does not establish recovery of an active workflow across machines. Install Windows and WSL2 separately; do not share an SQLite database being written to or copy a venv between them.

After changing the service's control home, fully reload the page before reading the current project and original operation records. Existing page forms have no guarantee of continued use across a server restart; browser cache stores selections and cannot replace server-side intents and receipts.
