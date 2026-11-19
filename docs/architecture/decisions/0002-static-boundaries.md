# ADR 0002: Static dependency protection and the R8 exit

English · [Documentation](../../README.md)

Date: 2026-11-02. This ADR records the static boundary decision; see the [architecture](../module-map.md#modules-and-dependencies) and [component protocols](../component-change-protocols.md) for current owners and checks.

## Problem and choice

R1–R7 centralized components/schema/DDL, separated assets/adoption from invocation use cases, established the reference boundary, and split the frontend. Subsequent feature additions need timely detection of reverse imports and new cycles, without freezing the structure through a complete import allowlist for every file.

|Alternative|Capabilities and costs|Conclusion|
|---|---|---|
|[Import Linter](https://import-linter.readthedocs.io/)|Mature declarative layers/forbidden/independence contracts, with Grimp graph construction; the evaluated PyPI 2.15 (Python >=3.10) requires Click, Grimp, Rich, and typing-extensions, adding development dependencies/configuration and a command|Reevaluate when multiple packages/external SDK layer contracts or complex indirect dependency rules arise; do not install in this round|
|Existing pytest + `ast` / `graphlib`|A few rules for the current 27 top-level files and function-local imports, with no new dependencies/commands; covers only syntactically explicit imports|Adopt in `tests/test_architecture_boundaries.py`, running with the existing Linux/Windows regressions|
|Repository-wide strict Ruff/Pyright or a new general plugin/graph analyzer|Addresses different problems and expands into historical style, types, and third-party code; cannot replace actual runtime acceptance|Exclude from this round; do not format frozen/third-party files|

The standard-library check has only test consumers and introduces no production “architecture framework” or general parsing command. Two pytest fixtures read the actual installed package and derive local import edges, with no persistent graph index. Continue using existing dynamic compatibility/runtime tests; do not copy another implementation of old API behavior.

## Constraints and failure scenarios

1. The owned top-level import graph must be acyclic. Include function-local imports to prevent evaluation from reimporting adoption use cases or the invocation layer from depending back on the facade; `graphlib` reports the actual cycle.
2. `components / contracts / state / windows_job` must not import application modules; `processes` may consume only `windows_job`. These are current foundational responsibility boundaries. New project/scoring/HTTP behavior belongs in upper layers, not foundational modules.
3. Other owned modules must not import `cli / web / __main__`, except for the entry points themselves. CLI may load Web lazily; business logic must not require the transport stack or obtain shared rules from entry points.
4. Explicit imports of `agent_platform / dev_platform` and modules under the packaged `ergora.data.reference` are allowed only in `reference / reference_executor`. Check ordinary `import`, absolute/relative `from`, and function-local imports; frozen directories can be imported as namespace packages, so checking only original top-level package names is insufficient. Other callers use existing resource/compilation interfaces or use cases, preventing HTTP/asset code from directly manipulating original globals/ledgers.

These rules allow upper layers to combine existing domain modules freely, without a repository-wide per-file allowlist. Before changing foundational responsibilities, update the ADR and actual consumers, then validate behavior; adding allowlist entries is not a solution to coupling. No subpackages were added. If packages are split later, update package discovery/resource acceptance and extend this check to the corresponding package graph, so new source does not silently fall outside protection.

## Checks and limitations

```bash
python -m pytest -q tests/test_architecture_boundaries.py
```

The test locates the package under test through `ergora.__file__`; CI first installs a non-editable wheel, so it also constrains the actually installed code. For direct source development, explicitly select the corresponding interpreter or `PYTHONPATH=src` to avoid accidentally checking an old installation.

Static checks do not parse Python in strings, `importlib` dynamic module names, JS, subprocess commands, implicit attribute access, or runtime configuration, and do not prove permissions/cancellation/recovery/model effectiveness. The dedicated compilation/dynamic execution bridge in `reference`, SDK drivers, frontend ES modules, package resource identities, and platform lifecycles are validated by existing tests and real probes respectively. R8 injects reverse imports and cycles into isolated installed copies and records actual rejection results; do not add a self-mirroring test framework to the product or CI.

R8 changes no runtime code, defaults, evidence digests, or SQLite schema, and introduces no data migration or new synchronous dual writer. The existing two project configuration entry points remain explicit; one-way effective configuration belongs to F1, and formal tasks/pages belong to F3/F4. Reverting this node reverts only its documentation/test commit; it cannot downgrade data already migrated by R3.
