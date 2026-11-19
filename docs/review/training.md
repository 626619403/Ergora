# Review pretraining and posttraining code

English · [Documentation](../README.md)

`pretraining-review` and `posttraining-review` each add a domain expert alongside the existing structure, correctness, and test-value reviewers. Both roots are read-only, have four required leaves and explicit all-join, and give the domain expert its own child template. They reuse the existing definitions, permission inheritance, backends, and formal ReviewDAG; they do not install another trainer or review service.

These are Ergora reviewer recipes based on fixed Bridge / slime methods. Sources and specific adaptations accompany the complete Skill; see the [current guide](../../src/ergora/data/presets/agents/ergora-pretraining-reviewer/skills/ergora-pretraining-review/SKILL.md) for upstream implementation identities. They are not official NVIDIA / slime Agents and do not indicate GPU, numerical, distributed, or convergence acceptance. Check the actual scope of conclusions under [interpreting results](#interpreting-results).

## Select experts and backends

|Preset / root|Domain leaf|Primary focus|
|---|---|---|
|`pretraining-review` / `ergora-pretraining-review`|`root/domain/review` → `ergora-pretraining-reviewer`|Effective tokens and loss / mask, accumulation / update clocks, precision, mesh / collective operations, state and recovery|
|`posttraining-review` / `ergora-posttraining-review`|`root/domain/review` → `ergora-posttraining-reviewer`|Actual SFT / preference / RL algorithm, samples / groups / feedback / mask, policy / reference / reward, versions / asynchronous recovery|

Both roots also include `root/general/structure/review`, `root/general/correctness/review`, and `root/general/test-value/review`. Both outer roots give all general and domain leaves complete originals, the requirements / standards review axes, coverage gaps, and the follow-up task handoff contract. Domain and general are siblings; domain does not inherit general's materials. The coordinator must read complete replies; a nonempty schema or approve decision cannot supply missing evidence, and actual results and tool decisions remain unchanged. Follow-up proposals can be submitted in batches or added before the previous batch finishes; the supervisor handles them under original dependencies / resources / budgets, preserving the current frozen graph, original clock, and reconciliation against the original job for unknown results.

To add engineering specialties, follow the [PR selection example](../../examples/composition/pr-review-selected/README.md): publish a delivery-review revision first, then place its exact reference in this root's general node and increment the outer version. Preserve the domain branch and complete inputs to both branches; results from another manifest cannot stand in for a joint review. Each instance inherits materials and permission ceilings from its own structural ancestors; the domain expert's Skill belongs to its own Agent definition. To change expertise, export and derive a new version, then reference it from a new root using the [definition manual](../definitions/workflows/compose.md); retain original versions and tasks in progress.

The default is Codex gpt-6.1-sol high; per-instance overrides must meet the [definition minimums](../definitions/agents.md). Prefer different backends for executor and reviewer; when falling back to the same backend, record the reason, independent sessions, and coverage. Agreement among models cannot replace trusted checks.

Prepare a manifest with the complete `root` reference returned by the corresponding installation. The root's shared [review backend Skill](../../src/ergora/data/presets/workflows/ergora-pretraining-review/skills/ergora-review-backends/SKILL.md) is inherited by all four leaves and distinguishes Ergora structured calls, native Codex / Claude Code commands, public plugins / custom CI, and vendor-hosted review. Selecting a backend or installing a preset does not automatically install CLIs, enable subscription services, or publish PR / MR comments.

## Prepare complete local input

First use the [local review packet manual](materials.md) to save original requirements, exact base / head, all changes, and explicit callers / configuration / original checks, then verify the packet. Prefer its [source-bound entry point](invoke-and-aggregate.md#hand-off-to-domain-or-specialist-review-leaves), binding complete local / external sources to the selected manifest and review leaf; it does not run the remaining branches automatically. The general composition input method remains below: pass the complete `review read` output as the task, not just a receipt, author summary, or diff.

```bash
ergora review read ./candidate-packet --sha256 PACKET_SHA256 > ./review-task.json
ergora composition install-preset pretraining-review
```

The Python below reads the original root's permissions / limits from the current library to generate a new manifest, without prefilled machine paths or credentials. For post-training, change the preset name to `posttraining-review`.

```python
from pathlib import Path
from ergora.definitions import workflows
from ergora.storage.state import State

state = State()
selected = workflows.install_preset(state, "pretraining-review")
root = workflows.get(state, selected["root"]["id"], selected["root"]["version"])["definition"]
grant = {"schema_version": 1, "permissions": root["permissions"], "limits": root["limits"]}
workflows.prepare_manifest(state.root, root["id"], root["version"], grant, Path("pretraining-review-manifest"))
```

After registering a project for the repository, explicitly prepare and invoke one domain leaf. This example uses Codex; choose `claude-code` if Claude authentication is already available. Supply the actual selection reason for `--backend-reason`.

```bash
ergora project add training-review --repo /path/to/project
ergora composition prepare-from-manifest ./pretraining-review-manifest root/domain/review \
  --task ./review-task.json --directory ./domain-review-input --max-prompt-bytes 1000000
ergora composition check-input training-review ./domain-review-input --backend codex --mode text-only
ergora composition run-input training-review ./domain-review-input --backend codex \
  --backend-reason 'Use the configured review backend in an independent session' --mode text-only --timeout 600
```

Complete inputs exceeding the limit are rejected; adjust selected materials / budgets and prepare again. Do not silently extract a summary and call it complete. `text-only` puts the declared complete resources in the prompt and provides no arbitrary shell, filesystem, or network tools. The returned record contains the original run / input digest / result path; the result's response retains findings and coverage gaps.

An independent `run-input` **invokes only the specified leaf**; the root's all-join does not automatically run the other three branches. For complementary opinions, prepare the same complete task separately for the three general paths and explicitly invoke each, preserving every result and any missing branches. Runs prepared through the source-bound entry point can use the [complete multi-branch report](invoke-and-aggregate.md#aggregate-a-complete-multi-branch-review): explicitly select sources / manifest and the original run IDs for all four instances to generate JSON / Markdown. Missing leaves / failures remain incomplete, and every verified objection is retained. Tasks from the general composition input method lack that source-binding contract and cannot automatically stand in for a source report. Formal development tasks can instead select the entire root using the existing `review_protocol: dag-v1`, letting the original six stages execute the four branches and all-join while preserving exact candidates, required branches, approvals, and recovery; see the [original template walkthrough](../development/templates.md).

## Generate CPU contract examples in one step

From a source checkout containing this script, run it with an interpreter that has Ergora installed:

```bash
python examples/review/training_domains.py --directory ./training-review-demo
```

The directory must not exist. The script only creates two new example Git repositories, executes **CPU arithmetic functions written in this script**, saves manually derived oracles and base / regression / valid commits, and generates four exact review packets:

- `pretraining/regression-packet`: microbatch means with unequal effective token counts change the all-token mean objective; `valid-packet` changes grouping while retaining the same objective.
- `posttraining/regression-packet`: losing the mask for fixed response-token contributions lets prompt / padding enter the objective; `valid-packet` changes the values, positions, and counts of masked items while retaining the response objective.

`examples.json` contains complete commits, scalar results, packet receipts, and SHA256 values; each packet includes original requirements, complete source / callers / configuration / standards, and original checks. Review each using read / prepare / run-input above. The examples involve no model / data downloads, GPU, real training, PPO / GRPO implementation, or multi-GPU proof; they check input delivery and these specific arithmetic issues, not an overall detection rate. The packet collector itself still does not execute project checks.

## Interpreting results

A confirmed issue should include a commit / source location, a reachable scenario under the actual configuration, consequences, and a minimal correction; list assumptions, missing materials, and unrun checks separately. Pretraining review should prevent silent changes to averaging or update clocks; post-training review should identify the algorithm before checking sample / weight / feedback relationships. Current results follow the original reviewer's `approve / request-changes` contract, retaining coverage and gaps in the response; independent external review opinions do not publish platform reviews, merge branches, or grant adoption authority.

Continue: [Prepare and verify exact review material](materials.md) · [Invoke and aggregate frozen reviewers](invoke-and-aggregate.md).
