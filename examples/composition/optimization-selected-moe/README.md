# Stage-specific MoE experts through the original six stages

This current example selects a fixed MoE dispatcher/overlap workload. A single ordinary parent invokes `root/development`, whose original six-stage owner runs inventory and plan groups, waits for exact owner plan approval, and retains work, trusted integrate/verify and independent final review. It does not choose among the sixteen optimization directions and three support roles automatically or execute training experiments.

[publication.json](publication.json) pins every current revision base, published reference and policy file. The policy source is pinned by `policy_source`. Its complete two Skills and environment record are added to the development ancestor through the existing resource-preview, accepted-candidate and revise interface. The source tree contains one policy copy. Stored immutable revisions preserve their original bytes and executable bits.

The exact current root is declared by `published.root` in [publication.json](publication.json); the publisher verifies and emits that immutable ID, version and digest.

```text
root/development
├─preparation/inventory
│ ├─flow, profile, dispatcher, overlap  inspector; independent
│ └─coordinator                       inspector; consumes all four
├─preparation/plan
│ ├─design, dispatcher, overlap        planner; independent
│ ├─kernel                            planner; consumes all three
│ └─coordinator                       planner; consumes all four
├─work
│ ├─contract → server, client → integration-tests
└─review
  ├─structure/review, correctness/review, test-value/review
  └─measurement/review                 four required independent reviewers
```

Every listed path is prefixed by `root/development/`; there are 18 model leaves. Every leaf inherits the same complete policy resources from the development ancestor. Inventory specialists use supplied source/profile/oracle evidence; only its canonical coordinator owns the original trusted baseline checks. Every planner receives the complete canonical inventory. Kernel assessment is required and can report an evidence-backed no-change decision. Its full original result reaches the canonical plan, approved-plan material reader and final measurement review. The canonical coordinators are actual model calls and do not approve their own plans.

The inherited policy retains one owner per direction and aims for 4–8 active experts according to the latest trusted profile. Dispatcher selection and MoE overlap remain two different optimization directions and retain their two experts; profiling is an evidence-support role. Four ready inventory calls, or four reviewers, do not by themselves establish four active optimization directions. Planning initially has three ready calls, and work has at most two independent writers; eighteen total slots are not four active direction owners. Select any necessary complementary direction assignments in an exact task revision before freezing and preserve the original stage handoffs, required reviews and actual slot/budget accounting. Report the actual distinct-direction count and any dependency, tool, resource or concurrency blocker; narrowed concurrency1/2 also permits fewer than four.

Preparation and review remain readonly with no shell or network. The original four work leaves retain their declared writable shell capability and explicit trusted-container requirement; all leaves have no network grant. Planner definitions request and require `gpt-6.2-sol/max`; flow inspection and final measurement review retain high. The inherited [specialist execution policy](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#specialist-execution-and-supervision) delegates experiments within assigned resources, budgets and actual tool grants. This example supplies planning and development capabilities; actual iGS submission, GPU execution and measured gains require their original execution tools and evidence.

The inherited [profile-driven handoff policy](../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#profile-driven-direction-selection-and-handoff) selects relevant directions from current trusted profile evidence. When a direction's agreed tasks, paired measurements and cleanup are complete, a later priority uses the next direction's different owner and complete original evidence/budget handoff. This fixed example does not change its frozen members or execute a dynamic loop; any later direction selection needs an exact revision before freeze and original admission.

To publish the fixed example into an explicit isolated library, use the current installed Ergora and run from this checkout:

```bash
python examples/composition/optimization-selected-moe/publish.py --home ./moe-example-control
```

[publish.py](publish.py) imports the current dependency closure, checks the exact policy source, applies the six fixed revision documents through `DefinitionLibrary`, previews and explicitly accepts the complete resource candidate, verifies the published refs, then freezes the manifest. It prints the actual root and manifest path/digest. Repeating it retains immutable identities; conflicting versions fail visibly. It performs no model, service, training or GPU operation.

Copy [task.example.json](task.example.json), replace its placeholders and illustrative scope/work split with the real registered project contract, and use the printed manifest path/digest. It is current task-definition schema8, producing formal input12. Preparation selects two `{instance, coordinator}` groups with `preparation-dag-v1`; native selection is `root/development`. The 18-slot authorization includes every preparation, work and review leaf. The 1,000,000-byte static material ceiling and concurrency4 are explicit in [grant.json](grant.json) and the structural wrappers; the project may narrow concurrency to1/2. Oversized complete materials fail without truncation or grant expansion.

Use the original `task prepare → preview → create` sequence with both returned SHAs, followed by original start, owner plan approval, cancellation and recovery. Material reading, queues, human waiting, models, checks and cleanup consume the one original clock. Unknown attempts are reconciled under their original identity. The fixed graph is a development/optimization-planning example; actual training/search/profile collection and business-quality acceptance remain with their original authorized owners. Independent `prepare-from-manifest`/`run-input` still invokes one leaf and requires caller-supplied complete predecessor material.
