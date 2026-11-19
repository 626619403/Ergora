# Run ForgeKernel native candidates

English · [Documentation](../README.md) · [简体中文](../zh-CN/agents/forgekernel.md)

## ForgeKernel native candidates

```bash
bash scripts/install-agent.sh forgekernel
```

Default source is `~/.local/share/ergora-tools/forgekernel`. Installation pins its version without installing CUDA/PyTorch, logging into Claude or starting GPU work. Configure native tasks/local devices using the [official instructions](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78), then bind:

```json
{
  "tool": "forgekernel",
  "checkout": "/YOUR_HOME/.local/share/ergora-tools/forgekernel",
  "python": "/YOUR_HOME/.local/share/ergora-tools/forgekernel/.venv/bin/python",
  "task": "/YOUR_HOME/projects/my-project/kernel-task"
}
```

```bash
ergora project bind my-project kernel --binding kernel.json --revision CURRENT_REVISION
ergora kernel plan my-project
ergora kernel prepare my-project
ergora kernel list my-project
ergora kernel status my-project CAMPAIGN_ID
ergora kernel run my-project CAMPAIGN_ID --timeout 3600
```

The same operations appear in “Workflow design → Training optimization experiments → Native kernel candidates”. `plan` checks/displays the native plan; `prepare` only creates/freezes a native campaign. `run` invokes models/GPU and explicitly continues that same campaign; `status` checks native state. The Ergora-ID/native-directory mapping is persistent. Changing current project bindings does not alter existing campaigns.

The pinned version supports only Claude backend; Codex login cannot substitute for it. This adapter version supports local delivery only and explicitly refuses SSH delivery. Timeout/interruption may leave native child jobs; record `outcome_unknown` without claiming remote/GPU cancellation. Check native directories and stopped old jobs first. To continue, supply `--reconcile-reason '实际核对依据'`, also available in the page. With uncertain creation, first use status to reconcile that ID's native directory rather than creating a replacement campaign.

Pinned-source checks cover both `src/forgekernel` and actually used `scripts`. Modified, deleted or untracked files relative to Git HEAD make doctor report `version=unsupported` and refuse operations before starting the native driver. Put custom wrappers outside the checkout. Pinned-source checks do not guarantee external Python dependencies, CLI binaries, environment or OS isolation.

In addition to native task snapshots, campaigns freeze SHAs for models.toml, loop.toml and backends.toml. Later configuration drift explicitly refuses execution; restore matching configuration. Do not edit shared defaults during a run. Backups/machine moves must retain tool source, these configurations and campaigns together. Reports and actual best/kernel.py or best/kernel.cu identities are saved. `native_finished` describes generator completion only; `native_failed` retains upstream failure. After selecting a candidate commit, continue with training-template manifests, trusted runners, correctness/quality and paired performance evidence, then manual release bound to evidence SHA. ForgeKernel's internal judge, target_met or report prose is not perfctl PASS. GPU/model quality requires independent workload acceptance.

Backend extensions use the shared `AgentBackend` contract and local mapping in `agents/backends.py`. Each implementation owns its commands, result extraction, specialized configuration and diagnostics. Public configuration schemas/capabilities remain declared only in `components.json`. `agents`, formal stages and doctor reuse those implementations; `processes` owns process monitoring/cancellation. See [current architecture](../architecture/module-map.md#agent-backend-integration) for integration/call paths. New specialist definitions, template members and nested resource inheritance follow the [workflow guide](../definitions/workflows/permissions.md#complete-inheritance-and-conflicts).

Continue: [Start a training optimization trial](../training/overview.md) · [Read training evidence and approve exact results](../training/evidence-and-approval.md).
