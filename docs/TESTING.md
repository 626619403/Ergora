# Maintain tests and interpret CI evidence

English · [简体中文](zh-CN/TESTING.md) · [Documentation](README.md)

<a id="测试维护"></a>

Use Python 3.11+ from the repository root. For routine checks, install `.[dev,web,gepa,temporal,task-mcp]` and run `python -m pytest tests`. Real Temporal checks require an isolated service set through `ERGORA_TEMPORAL_TEST_ADDRESS`. Existing tests retain skips when that service or an optional capability is unavailable.

CI checks the installed wheel. To reproduce this boundary in an independent virtual environment, install `build`, run `python -m build --wheel`, then install the generated wheel from `dist/` with the `dev,web,gepa,temporal,task-mcp` extras. Use a non-editable installation and keep `src/` out of `PYTHONPATH`. Then run:

```bash
python -m ergora reference verify
python scripts/ci/run.py --collect-only --output .ergora/checks/collect-all
python scripts/ci/run.py --group 0 --collect-only --output .ergora/checks/collect-group-0
python scripts/ci/run.py --group 0 --output .ergora/checks/run-group-0
```

Use a new result directory for every command. The runner rejects an existing directory so old logs cannot be mistaken for a new result. Omitting `--group`, or using `all`, selects the platform's full scope. On Windows, use `all`; native PowerShell 5.1 installation/upgrade checks run separately in CI. Linux covers `tests`, frozen-reference contracts, portable, workflow `AdapterTests` and runtime; Windows covers `tests` and contracts. The runner adds only its observation plugin and Linux reference import path to `PYTHONPATH`; the application still imports from the current interpreter's installed wheel.

Linux groups use the explicit [file list](../scripts/ci/linux-groups.json), with every test file registered once. Add new files to a group and update moved paths there. The plugin collects the full scope before selecting the requested group, rejecting unregistered files, duplicate assignments, missing paths, invalid groups and empty selections. Whole-file execution preserves intra-file fixture/case order; groups use independent runners. After `--collect-only` for all groups, verify that their `collected.nodeids` union equals the full collection and that intersections are empty. The number of groups alone does not establish complete coverage.

GitHub Actions derives its matrix from the same JSON. Each group builds/installs a wheel and checks reference identity; Linux jobs have a 20-minute limit, while the Windows `all` job has a 40-minute limit. Before rebalancing groups, use actual phase durations to assess the slowest complete file and installation/upload headroom. Do not hide timeouts by deleting failure/recovery checks.

Result directories retain `request.json`, complete `stdout.txt`, `phases.jsonl`, JUnit and, after normal runner completion, `result.json`. JSONL immediately records full/selected nodeids, phase starts, setup/call/teardown outcomes, durations/failure bodies, collection skips/failures and session termination. Subtests have a different `report_type` from their parent case; their durations are already included in parent phases and must not be summed again. Normal pytest exit 0 establishes that selection's pass. `--collect-only` establishes collection/selection only.

An interruption can leave no session `finish`, JUnit or runner result. The last phase start identifies in-flight scope; it does not prove deadlock. CI attempts to upload written files with `always()`, but a hard job deadline or lost runner can prevent upload. Preserve missing originals, cancellation and incomplete outcomes at their actual scope. Invoke observations through `python -m pytest`; do not call `pytest.main()` at the top level of a custom driver, where spawn could rerun it.
