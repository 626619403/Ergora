# Evaluate and adopt Skill candidates

English · [Documentation](../README.md)

## Skill candidates, evaluation, and adoption

Import directories follow [Agent Skills](https://agentskills.io/specification): `my-skill/SKILL.md`, with YAML frontmatter containing `name: my-skill` and `description`; scripts, references, and resources are addressed with the complete directory. Import rejects symlinks / `.git`, with limits of 500 files / 10 MB. The first import of a name is an explicit initial baseline; later imports create candidates without replacing the active version.

Import verifies a complete copy before publishing and registering it; concurrent or interrupted retries for the same project and version remain idempotent. Unregistered partial trees can be recovered from verified sources. If a registered version is missing or modified, import and reads reject using or overwriting it; restore from a trusted backup and recheck evidence. Reimporting does not repair registered evidence.

```bash
ergora skill import my-project ./my-skill
ergora skill list my-project
# 修改独立来源目录，再导入候选
ergora skill import my-project ./my-skill --hypothesis '一个可检验的改进假设'
ergora evaluation register my-project evaluation.json
ergora evaluation run my-project BASELINE_DIGEST --suite SUITE_DIGEST
ergora evaluation run my-project CANDIDATE_DIGEST --suite SUITE_DIGEST
ergora evaluation compare my-project BASELINE_RUN_ID CANDIDATE_RUN_ID
ergora skill adopt my-project --baseline-run BASELINE_RUN_ID --candidate-run CANDIDATE_RUN_ID --revision 1 --reason '已审阅实际证据'
ergora skill rollback my-project my-skill BASELINE_DIGEST --revision 2 --reason '记录回退原因'
```

The project maintainer supplies `evaluation.json`; the example structure follows. Fill in data, commands, and thresholds for the actual task:

```json
{
  "schema_version": 1,
  "evaluator_argv": ["python3", "evaluate-skill.py"],
  "evaluator_files": ["evaluate-skill.py"],
  "timeout_seconds": 60,
  "minimum_gain": 0.05,
  "max_reported_cost": 2,
  "cases": [
    {"id":"train-1","split":"train","input":{"task":"填写构造任务"}},
    {"id":"validation-1","split":"validation","input":{"task":"填写迭代评价任务"}},
    {"id":"holdout-1","split":"holdout","input":{"task":"填写独立保留任务"}}
  ]
}
```

Register separate cases for train, validation and holdout. The same JSON input cannot appear in different splits, even under different IDs, with reordered keys or with equivalent number representations such as `1` and `1.0`. Assign the same optional `lineage` label to related inputs derived from one original run or example and keep those cases in one split. The maintainer still owns source independence and exposure records. Saved overlapping suites and runs remain readable for diagnosis, while a new GEPA search or Skill adoption requires a disjoint suite.

The trusted evaluator reads `{"skill_dir":"版本目录","case":具体input,"budget":{...}}` from stdin, runs in an independent working directory, and returns one JSON object on stdout with exit code zero. A scored response looks like `{"score":0.8,"passed":true,"cost":0.01,"feedback":"具体执行反馈"}`. The score must be 0–1 and the cost a nonnegative finite number. `passed` denotes actual project correctness checks, which the candidate cannot self-declare. A measured wrong answer can receive a score of zero and `passed: false`.

An evaluator that completed its own work and cleanup but could not produce a score can return `{"outcome":"unevaluable","cost":0.01,"feedback":"Unable to grade the answer"}`. When the suite pins an execution identity, the response can also include `execution_identity`. Use a finite nonnegative cost when known and `null` when unknown. The case record keeps `outcome` separately from the original process `status` and `returncode`. The run stops with `failed`, or `budget_exhausted` if the reported cost crosses the limit. It supplies no grade to GEPA or to the comparison and adoption gates. Startup failures, nonzero exits, timeouts, and invalid stdout supply no trusted report.

For a model-backed comparison, the suite can pin `execution_identity` with `provider`, `model`, and `cost_unit`. The trusted evaluator returns the same fields from its observed execution and accounting. A missing or different identity stops the run and withholds the grade. The case keeps the observed identity and valid reported cost. The aggregate includes that cost only when the report uses the suite's unit. Pair comparison checks the pinned identity on every successful case. Provider billing and model identity still depend on the underlying evidence supplied by the trusted evaluator.

stderr can contain diagnostics. `evaluator_files` declares scoring source and dependency files to fix. Their SHAs and the interpreter's SHA are recorded. The maintainer still pins and revalidates other environment, data, and imported dependencies.

`budget` exposes the limits effective for this case:

| Field | Meaning |
|---|---|
| `deadline_monotonic` | Absolute `time.monotonic()` deadline on the same host: the earlier of this case's suite timeout and the original search deadline. |
| `remaining_seconds` | Time left when the request was assembled; setup and input delivery consume this snapshot. Use the absolute deadline to avoid renewing it. |
| `remaining_reported_cost` | Suite/search reported-cost remainder after completed results. Costs arrive after calls and can exceed this amount. |
| `remaining_batch_calls` | Current and later case slots in this evaluation batch, including this case. Each case dispatch invokes the evaluator once. |
| `unreserved_metric_calls` | GEPA case slots outside its already-reserved batch; `null` for standalone evaluation. These future slots are not granted to the current evaluator. |

The process owner checks the deadline after input/setup writes, before launching the command, and keeps the same deadline while waiting. On Windows the gated child also receives this deadline and checks after reading and encoding its complete input, immediately before command admission. A cooperative evaluator must reserve time inside that deadline for scoring and its own confirmed cleanup. Monotonic deadlines are local process coordination values, not portable timestamps or renewable recovery budgets. These case counters do not count or authorize nested provider/model calls or retries; a trusted evaluator owns any separately authorized finite inner invocation. Ordinary process-group cleanup does not establish cleanup of an evaluator that starts independent process groups; nested supervised execution must retain its original stop/reaper owner. Timeout, interruption and missing results never authorize a replacement call.

The suite fixes evaluation cases, command, thresholds, and file identities; existing files in argv are also fingerprinted automatically to avoid undeclared scoring entry points. After changing scoring files, register a new suite and rerun both sides. Candidate directory contents and executable bits are identity-checked before and after evaluation, during comparison, and at adoption. Adoption requires complete evaluations of both sides, candidate correctness passing, validation reaching minimum_gain, no holdout regression, and a matching current active baseline / revision. Partial train / validation search records cannot replace complete evaluation. A final holdout can be checked before adoption; repeatedly inspecting it and tuning against it contaminates independence, so maintainers should refresh holdout cases periodically.

`suite.json` archives the frozen manifest for a full-suite run. A subset run archives the selected cases in registered order and marks the snapshot with `partial: true` and the full registered `suite_digest`. The snapshot records the batch inputs. An early stop can leave selected cases unentered. The run record lists attempted cases and their outcomes.

Comparison and adoption read the original full-suite snapshot and the saved evaluator request and response for each completed case. They check the case order and split, the Skill version and case input sent to the evaluator, and the returned scores and correctness. New runs record SHA-256 digests of the exact request and response bytes. Historical records remain inspectable when an archive is missing or inconsistent. Comparison withholds eligibility when it cannot verify the original evaluation. Rechecking never calls the evaluator.

Costs come from tool reports. `reported_cost_complete` is true when every entered operation has reported a known cost and the total is representable. A valid unevaluable result with a known cost contributes its full amount. An explicit `null` leaves `reported_cost` at the accepted subtotal and sets completeness to false. Historical records lacking this field retain their original data and have unrecorded completeness. Comparison and adoption keep their existing quality gates.

The original record is marked incomplete before evaluator/proposer entry, and each accepted full cost is persisted before further work. Unknown reports halt later calls; interruption does not authorize a replacement or renewed clock. Exceeding a reported-cost budget preserves the full overshoot and stops later calls. Complete reported coverage does not authenticate actual provider billing, inner usage, model identity or a hard ceiling; combine actual cost control with provider quotas. Process outputs, failures, and inputs are saved in private run directories; deleting memory does not retroactively rewrite archived task inputs or independent backups.

### Optional GEPA

Install `.[gepa]` to enable the pinned `gepa==0.1.4` engine; the default optimizer layer `{"tool":"manual"}` uses manual imports and the same evaluation / adoption process. Example GEPA binding:

```json
{"tool":"gepa","proposer_argv":["python3","/absolute/path/propose-skill.py"]}
```

```bash
ergora project bind my-project optimizer --binding optimizer-binding.json --revision CURRENT_PROJECT_REVISION
ergora skill optimize my-project --baseline BASELINE_DIGEST --suite SUITE_DIGEST --objective '一个可衡量的改进目标' --max-evaluations 20 --max-proposals 5 --timeout 300
ergora skill optimizations my-project
```

Proposal commands may connect any model / agent but must follow the JSON stdin/stdout protocol. stdin contains `candidate.skill` (complete SKILL.md), `feedback`, `components`, and `objective`; stdout is `{"skill":"完整新版 SKILL.md","cost":0.01}`. The real SDK performs GEPA search / selection; the command only generates text. Other files retain the baseline, and the project owns source and model configuration. Relative command paths resolve against the project root without a shell; authentication uses the command environment.

For a suite with a pinned execution identity, the GEPA proposal request also provides `response.cost_unit`. The proposer includes that exact unit as `cost_unit` in its response so evaluation and proposal costs share one budget.

The search interface sends train and validation materials. Access to registered suites and archived data still follows filesystem permissions, including access by other processes under the same Unix user. Search reserves each batch's distinct metric cases before evaluation; a partially completed batch retains its complete reservation. Proposal attempts are counted before dispatch, and fractional remaining time is preserved. Search enforces these metric-call / proposal counts, per-call and total time limits, and reported-cost constraints. Internal errors and budget termination retain status; search does not adopt automatically, change scoring, or execute candidate-supplied scripts. Candidates still require complete evaluation and manual adoption. Current validation uses real GEPA with deterministic local subprocesses; it establishes no real model effect or generalization benefit.

### Use in later tool calls

```bash
ergora agent run my-project implementer --prompt task.md --skill my-skill --recall '相关项目约定'
ergora skill export my-project ADOPTED_DIGEST ./export/my-skill
```

`--skill` reads the complete currently adopted version of that name; `--recall` uses the current project memory backend. Run records save the actual skill digest, memory revisions, and prompt digest; archived inputs allow checking their actual consumption. After rollback, the next invocation reads the restored active version. Export chooses a new directory with the same name without overwriting existing project files; maintainers can install it into project `.agents/skills/` following host conventions. These operations change neither the reference six-stage executor nor global host configuration.

Continue: [Carry a retrospective into the next task](workflow.md) · [Prepare a task's frozen composition](../development/preparation.md).
