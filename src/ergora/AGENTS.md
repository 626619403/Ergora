# Source changes

Before changing an implementation or its configuration, read the [component change protocols](../../docs/architecture/component-change-protocols.md#choose-the-actual-change-point) and locate the semantic owner in the [module map](../../docs/architecture/module-map.md). Follow the real configuration, construction, caller, result, and recovery path before editing.

- Agent backends and issue providers: [agents and external sources](../../docs/architecture/component-change-protocols.md#agents-and-external-sources). Each implementation family owns its contract, construction, and local registration.
- Definitions, Skills, MCP, presets, and complete assets: [definitions and complete resources](../../docs/architecture/component-change-protocols.md#definitions-and-complete-resources).
- Project configuration, schemas, SQLite, and immutable storage: [configuration and persistent formats](../../docs/architecture/component-change-protocols.md#configuration-and-persistent-formats).
- Development or training operations, native processes, budgets, source identity, and evidence: [execution and evidence](../../docs/architecture/component-change-protocols.md#execution-and-evidence).
- Memory, evaluation, research, retrospective proposals, and optional kernel tools: [improvement and optional tools](../../docs/architecture/component-change-protocols.md#improvement-and-optional-tools).
- CLI, HTTP, and console resources: [interaction entry points](../../docs/architecture/component-change-protocols.md#interaction-entry-points). Installation and checks: [scripts and checks](../../docs/architecture/component-change-protocols.md#scripts-and-checks).

Package initializers stay empty so isolated readers can import their owners without application state or optional SDKs. The private `_paths` owner supplies the one package, import, and data root. Source relocations must update actual subprocess entrypoints, explicit source coverage, package discovery, and resource identity together; saved records retain their original identities. Detailed obligations and checks remain in the protocols above.
