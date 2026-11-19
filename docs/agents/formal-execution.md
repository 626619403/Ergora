# Connect the formal six-stage backend bridge

English · [Documentation](../README.md) · [简体中文](../zh-CN/agents/formal-execution.md)

Configure the [selected Agent backend](configuration.md) first. This optional bridge uses the existing six-stage owner; it does not add a graph scheduler or new approval authority.

## Optional formal six-stage execution bridge

The default `agentflow` executor retains v2.2 behavior. To apply project-role selections to formal tasks, first install the reference runtime and configure models/trusted execution boundaries. Then [register a unified project](../projects/registration.md) with Git root, roles, templates and trusted checks together, and run `ergora reference executor --project PROJECT_ID`. The old two-registration approach remains compatible; identically named projects must use the same Git root. Enable this only for new tasks, without switching an already-started reference task midway.

Preview an existing reference project with `ergora project import-reference import.json --revision N`, review differences/file identities, then explicitly adopt with `--apply --preview-sha256 SHA`. Compatible old files retain original bytes, with before/after project and provenance records saved. It neither migrates in-flight tasks nor imports model keys. See [project definitions](../projects/registration.md#explicit-import-of-an-existing-registration) for the complete spec and recovery commands.

Stop the original executor first, retaining Temporal, worker and other services:

```bash
"$HOME/multi-agent-platform/.venv/bin/supervisorctl" \
  -c "$HOME/.config/multi-agent-platform/supervisord.ini" stop executor
ergora reference executor --installation "$HOME/multi-agent-platform"
```

The command listens in the foreground to the original FileAdapter queue under the same executor lock, preserving original task creation, approval, cancellation, recovery and export commands. Add `--request /ABSOLUTE/PATH/envelope.json` to process exactly one published envelope. The executor verifies reference Python source identities and refuses unadapted versions.

When first processing a new task, save selected role tools/project revision in `agent-bindings.json` inside the original persistent task directory. Recovery retains that selection. Implementer and reviewer use distinct role identities, fresh sessions, exact candidate commits and original workspace-change checks. Before a formal stage ends, clean up/reap descendants, then execute the original monitor's read-only change checks using the exact configured reference Codex executable path. The reference monitor still reconciles unknown external-process outcomes. Missing capabilities, invalid result structure, command failure or read-only-stage changes cannot pass. Agent `model-log` and `agent-selection` accompany original receipt evidence.

Bridge model stages verify this task's saved `compiled.json` and stage contract, load complete template instructions from that snapshot and record their digest in `agent-selection`. Missing, changed or other-task snapshots explicitly fail, without substituting the active package. Deleting source packages does not change existing tasks' instructions; installation-profile drift is still refused under original rules. This is Ergora bridge behavior; direct `agentflow` retains original v2.2 behavior.

The unified entry's [external-evidence query](../development/evidence-and-export.md#check-external-job-evidence-for-a-closed-run) matches dev_submit entries in complete original-run history against trusted FileAdapter requests/receipts individually. Every known job remains unresolved even with a missing request. External confirmation is refused when the correct fence is missing, extra requests/orphan receipts exist, receipts are invalid or artifact digests are wrong. A read-only query changes no original outcome, publishes no fence and releases no lease. External termination evidence and six-stage quality outcomes remain separate. A normal REVIEW_READY also does not automatically release an issue lease when its workflow closes: export follows the original rules, or use [normal task closure](../development/run-and-recover.md#close-after-normal-task-completion) when not exporting yet. To write a fence and release the exact original claim, explicitly use [reconcile/reconciliation/resume-reconcile](../development/run-and-recover.md#explicitly-reconcile-terminal-state-and-release-issue-leases). It saves original outcome and independent cleanup evidence, retains original CANCEL_UNCONFIRMED and refuses release with missing evidence.

After an original v7 provenance task exports its exact candidate, follow [candidate comments](../projects/candidate-actions.md#post-an-issue-comment-for-an-exported-candidate) to prepare/confirm a neutral GitHub/GitLab comment. That action separately saves intent/native receipt and reuses original task identity without changing backend, approval or export results. GitHub [native-ID label addition](../projects/candidate-actions.md#add-a-github-label-for-an-exported-candidate) reuses that writeback lifecycle. GitLab labels explicitly report unsupported. Selecting a tracker does not implicitly alter Agent authorization.

New records also save the effective `configuration` view, including each layer's source, validation, project revision and content digest. Read current values through `ergora project config PROJECT_ID`. Older tasks without this extra field retain their original binding snapshot, without reconstructing historical configuration. See [effective bindings and run snapshots](configuration.md#effective-bindings-and-run-snapshots) for its scope versus standalone-call context.

For long-running unified projects, prefer `ergora services start PROJECT temporal worker executor a2a --revision N` to manage the selected stack without hand-editing ini. The following applies only to legacy deployments retaining original Supervisor: in `~/.config/multi-agent-platform/supervisor.d/executor.ini`, change the program's `command` to the absolute Ergora executable plus `reference executor --installation ...`, retaining stopasgroup/killasgroup. Run supervisorctl `reread` / `update`. Reference-distribution initialization may regenerate this file; check after upgrading. Do not run old and new executors together.

The bridge retains Codex TOML/API variables from reference configuration. The reference monitor's credential whitelist does not forward arbitrary shell variables. Other providers may use their own persistent login or the reference `credentials.json` 0600 credential mapping. Templates, bindings and repositories store only credential-variable names/metadata. Standalone active-Skill/memory options do not automatically rewrite formal-task context.

Continue: [Configure and authenticate Agents](configuration.md) · [Create a formal development task](../development/tasks.md).
