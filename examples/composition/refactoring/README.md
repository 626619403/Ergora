# Refactoring through the original six-stage owner

`refactoring` is an optional composition preset. Its formal task type is `large-change`; it forwards one selected six-stage instance through the existing task lifecycle. The default work units are `rewrite → compatibility`, followed by the existing independent structure, correctness and test-value reviews. Trusted integration, verification, plan approval, candidate identity and unknown recovery retain their original owners.

This example requires a registered Linux/WSL2 project with the original execution installation and task-MCP support. Installing or previewing the preset does not run a model or approve a plan. Workspace writers use the explicitly selected trusted current-container mode; its documented advisory scope limits remain. See the [formal lifecycle](../../../docs/USAGE.md) and [composition contract](../../../docs/WORKFLOW_DEFINITIONS.md).

1. Import the bundled definitions and prepare a complete static manifest under an explicit grant:

   ```bash
   ergora composition install-preset refactoring
   ergora composition prepare-manifest ergora-refactoring-template 1.2.1 \
     --grant examples/composition/refactoring/grant.json \
     --directory ./refactoring-manifest
   ```

   Complete when the returned manifest path and digest identify the exact root and all its dependencies. The supplied grant requests workspace writes and shell for the work stage; use a project-appropriate ceiling. Every child remains within its structural ancestor ceilings.

2. Copy `task.example.json` to a task file. Replace its manifest path/digest, issue, task ID and exact baseline SHA. Replace `src/example` and the illustrative caller contract with your actual module, callers, invariants, allowed paths, compatibility combinations, migration order and rollback checks. Keep preparation repository paths sufficient for all unit paths. Set the budget for preparation, waiting, work and cleanup.

   Complete when every claimed invariant and caller has a baseline source or an explicit evidence gap. The placeholder SHA and digest intentionally fail validation until replaced; filling valid JSON alone does not establish behavior preservation. Inventory exposes missing evidence and the owner decides whether to approve the exact plan.

3. Use the existing `ergora task prepare`, `preview` and dual-digest `create` sequence described in the formal lifecycle, then the original start and plan-approval operations. Keep the original task/run when observing, cancelling or reconciling an unknown result. Complete when the original evidence identifies the actual final candidate, executed checks, migration and rollback results and all unverified conditions.

The two writers and three reviewers are defaults. Use the existing definition revision and exact-reference mechanisms to change their number, expertise or dependencies, and update original work-unit assignments accordingly. One writer must cover each original unit; preparation selects one inspector coordinator group and one planner coordinator group through the same preparation-DAG shape. Original task/profile and material limits apply.

All specialists select Codex gpt-6.1-sol: preparation/planning max, refactoring xhigh, compatibility validation and final review high. `backend_overrides` supplies complete bindings satisfying those minimums; the example also selects current-container for writers. Same-backend review retains separate sessions and the declared `diversity.reason`; `require-distinct` rejects it. Actual provider configuration and environment credential references come from the operator's inference configuration, outside the template.

The parent includes repository conventions, real caller and test-seam guidance through its complete inherited Skill. Recover a started task through its original task/run identity.
