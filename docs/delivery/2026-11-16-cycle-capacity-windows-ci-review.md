# Cycle-capacity Windows CI test-scope review

2026-11-16. Fresh-context independent reviewer: `cycle_capacity_windows_ci_review`. This review covers the smallest test-scope correction for the six new failures in the published candidate's Windows CI. It does not certify a corrected Windows run.

## Verdicts

|Axis|Verdict|
|---|---|
|Requirement compliance|**Approve within the inspected source scope; no open findings.** The six unsupported native-operation nodes are skipped off Linux, while the portable request-rejection case and generic SDK failure-converter coverage remain enabled.|
|Maintainability|**Approve within the inspected source scope; no findings.** The guards use the existing test owner and platform convention without introducing helpers, dependencies, configuration, or production branches.|

There are no blocking source findings. Publication acceptance remains pending the corrected candidate's own applicable CI, including actual Windows execution.

## Inspected candidate and contract

The read-only source tree was `.ergora/worktrees/cycle-capacity-windows-ci-r1`, branch `fix/cycle-capacity-windows-ci-r1`, at baseline HEAD `7fc42177db11fbfe4c9adb33342ecb5da4ed0434`. The candidate was uncommitted and contained exactly three added lines in `tests/test_training_runtime.py`, with no untracked files. Product source remains the reviewed joint product `6cec589f404b17f4828a70807d5e33d89fad3fa0`.

The reviewer recomputed and matched the frozen identities in `.ergora/checks/cycle-capacity-windows-ci/r1/source-freeze.json`:

|Object|SHA256|
|---|---|
|Baseline test file|`be4d9f5c7aef55b297ee7eb206042f0aed7e378b5bfca951003c90e62255f086`|
|Candidate test file|`f98c4049945c7471d5996aa89bc71870cb19623ad817864d83cb7e66e3cc26d2`|
|Full-index candidate patch|`770aca436a5a0a9c2beeea90d7a07c55c0214c83f4909b0fa5d74bf1a8dca4ca`|

The live patch equals the frozen `source.patch`. Apart from the platform guards, existing case logic, assertions, parameter values, fixtures, production source, CI selection, and budgets are unchanged. The raw requirements preserve Linux/WSL2-only native budget-clock and S/H operation support, cross-platform optional SDK conversion/failure behavior, visible unsupported-operation failures, the six-stage contract, candidate-bound evidence, and existing runtime behavior. Native Windows support and unrelated test quarantine are outside this slice.

## Source reasoning

- At `tests/test_training_runtime.py:424`, the conditional skip excludes only `inspection`, `operation`, and `cancel` on non-Linux platforms. These cases supply a valid workflow protocol and must construct `_CycleOperation` before their substituted `run` can execute. The original `control_home='/'` fails Windows absolute-path validation in `training_execution_protocol.validate_cycle_activity_request`; valid native construction also reaches the Linux-only boot clock in `_CycleOperation.__init__`. Replacing the leaf `run` does not remove these dependencies. The `request` case supplies an invalid protocol and is rejected before that path/native boundary, so it remains portable and enabled.
- At `tests/test_training_runtime.py:1577`, the assembled-envelope test is marked non-Linux skip. It calls the real `budget_clock.authorize`, and its real operation constructors retain native clock dependencies. Its platform condition matches `budget_clock._clock` and the neighboring native-operation tests. Linux and WSL2 retain all three boundary-size cases and their complete assembled-measurement/operation assertions.
- The separate final-saved-Failure test's three size cases and whole-default-error-tree test's five cases remain unmarked. Together with the portable request case, these retain nine relevant SDK cases off Linux. There is no module-wide skip, altered failure converter, fake OS/native support, widened timeout, or changed capacity limit.

## Evidence checked

The reviewer inspected the actual argv/environment records, stdout/stderr, JUnit results, diagnostic plugin, and runner under `.ergora/checks/cycle-capacity-windows-ci/r1/`.

|Recorded check|Observed result|JUnit / runner time|
|---|---|---|
|Baseline file, local Windows-dependency replay|6 failed, 9 passed; exactly the original six node IDs|4.299 s / 6.120 s|
|Candidate file, same dependency replay|9 passed, 6 skipped|1.635 s / 2.650 s|
|Candidate file, actual Linux dependencies|15 passed|2.026 s / 2.946 s|

The command records preserve equal before/after test hashes for each run, return codes, pytest PID/start ticks, and absence after wait. They select the same four existing test functions and their 15 parameterized nodes. Explicit `PYTHONPATH` selects candidate source while using an existing SDK environment; these are source checks, not a new wheel installation.

The diagnostic plugin targets the test module's imported `sys`, `budget_clock.sys`, and `training_execution_protocol.Path` to exercise Windows path validation and the real non-Linux clock guard. It leaves the host OS and SDK unchanged. Its before/after result proves this dependency/scope correction locally; it is not actual Windows execution.

The original official failure remains intact: [Portability run 43833234533](https://github.com/626619403/Ergora/actions/runs/43833234533), attempt 1, full head `7fc42177db11fbfe4c9adb33342ecb5da4ed0434`, seven successful jobs and failed Windows job `133183447980`. Under `.ergora/checks/design-capacity-integration/publication-r1/`, the inspected `jobs-terminal-api-response.json`, `jobs-terminal-summary.json`, and `windows-annotations-response.json` confirm application regression **6 failed, 1283 passed, 1145 skipped, 16 subtests passed in 1367.19 s**, with subsequent PowerShell installer and artifact upload steps successful. The annotations identify all six failed nodes and three original-absolute-control-directory rejections. Earlier API quota failures remain separate observation evidence.

Reviewer checks were read-only source/caller and artifact inspection, Git scope/history checks, hash comparison, test AST parsing, and `git diff --check`. No tests, models, installs, services, commits, pushes, or external operations were run by this reviewer. Applicable root/tests instructions, component-change protocol, delivery/plan, independent-review guidance, and Ergora repository/test-seam guidance were read.

One documentation observation was resolved during review: the delivery initially grouped the distinct wrapper assertion failures together and still described the completed probe as preparation. The documentation owner corrected the three failure descriptions and recorded the observed path/clock causes. The reviewer reread the corrected [delivery](2026-11-16-cycle-capacity-windows-ci.md); no open issue remains from that observation.

## Remaining acceptance

Ordinary integration/publication must retain this exact test scope and bind the resulting full candidate OID to its own CI. A successful corrected Windows job is still required; the local replay, Linux result, original successful installer step, earlier wheel checks, and older candidates' green CI do not establish it. No native Windows execution capability or broader training/service acceptance is added by this review.
