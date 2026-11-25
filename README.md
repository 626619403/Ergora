# Ergora

English · [简体中文](README.zh-CN.md)

**Multi-agent collaboration contracts and a reference runtime for repository development and training experiments.**

Ergora connects task goals, roles, permitted changes, human decisions, parallel work, trusted checks, independent review and original execution evidence. Each business project keeps its own Git repository and issue namespace; tasks export their own candidate branches.

The `ergora` CLI and local console manage projects, Agent and Workflow definitions, formal tasks, evidence and improvement candidates. Formal development uses the existing six-stage Linux reference runtime. [Documentation](docs/README.md) is organized by task; the [current plan](docs/PLAN.md) records the active delivery and remaining boundaries.

## Quick start

Use Git, Python 3.11+ and venv/pip on Linux. Clone into a directory that does not already exist:

```bash
git clone --branch main \
  https://github.com/626619403/Ergora.git "$HOME/Ergora"
cd "$HOME/Ergora"
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"

ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset refactoring
ergora serve
```

Open `http://127.0.0.1:8977` on the serving machine. The packaged console needs no Node build or runtime CDN. Native Windows uses the [PowerShell installation guide](docs/install/windows.md); full formal execution requires Linux/WSL2 and an explicitly trusted container.

The default `control` profile installs the web control plane. `development` adds the Temporal SDK; `research` also adds GEPA. [Installation](docs/install/linux.md) covers profiles and offline wheels. Profiles do not authenticate Agents, start services or run training. Pin a complete Git commit when reproducing an acceptance record; the package version alone does not identify equivalent source.

## Choose a task

|Goal|Start here|
|---|---|
|Govern a repository, develop a large change or refactor behavior|[Bundled template journeys](docs/development/templates.md)|
|Create a formal development task|[Frozen preparation](docs/development/preparation.md), then [task preview and creation](docs/development/tasks.md)|
|Define specialists or a nested workflow|[Agent definitions](docs/definitions/agents.md) and [workflow composition](docs/definitions/workflows/compose.md)|
|Collect and review exact PR/MR material|[Review material](docs/review/materials.md), then [explicit reviewers and aggregation](docs/review/invoke-and-aggregate.md)|
|Prepare and execute training experiments|[Training overview](docs/training/overview.md)|
|Record or stop a finite local campaign plan|[Campaign operator guide](docs/improvement/campaigns.md)|
|Write a report from original evidence|[Evidence reports](docs/review/evidence-reports.md)|
|Use a retrospective in a later task|[Improvement workflow](docs/improvement/workflow.md)|
|Move or recover the local task stack|[Joint backup and recovery](docs/operations/backup-recovery.md)|

Before a formal run, [configure and authenticate the selected backend](docs/agents/configuration.md), [register a committed business repository and trusted checks](docs/projects/registration.md), and prepare the complete template manifest. Native backend login and optional custom API-provider configuration follow their actual supported paths; Ergora does not log in or copy account state.

## Formal development

The six stages remain inventory → plan → work → integrate → verify → review. Read the complete plan and approve its exact SHA through [plan approval](docs/development/design-and-approval.md). The original trusted checks and independent reviews bind the candidate; an Agent's success message does not grant formal acceptance.

[Submission, status and recovery](docs/development/run-and-recover.md) retain original task/run/intent identities. An uncertain external result requires reconciliation. Cancellation delivery alone does not prove processes stopped. [Evidence and export](docs/development/evidence-and-export.md) produce a local candidate branch for maintainer inspection; export does not merge or push it.

Definitions accumulate ancestor Skills and context while narrowing permissions down the structural parent chain. A valid definition or saved manifest does not execute a graph. The [workflow contracts](docs/definitions/workflows/contracts.md) and [permission rules](docs/definitions/workflows/permissions.md) explain supported projections and limits.

## Current scope

Use the development version for small trials on one machine with trusted projects. Linux and native Windows support the control plane; the [Windows guide](docs/install/windows.md) identifies execution boundaries. The reference executor uses the current trusted container and Unix user, without per-Agent operating-system isolation.

Training proposals, kernel suggestions and evidence indexes do not establish actual training quality or performance. Explicitly authorized [finite controllers](docs/training/controllers.md) use frozen candidates under one original budget. Adaptive candidate generation, automatic per-round profiling, general Repeat and unsupported mixed graphs retain their separate implementation and acceptance requirements.

Backend availability, supported modes, authentication, actual execution and business quality are separate facts. Unsupported operations fail visibly. Source checks, wheel installation, real services, model behavior, GPU results and a candidate's [GitHub Actions](https://github.com/626619403/Ergora/actions) retain their own evidence.

## Understand and extend

Start with the [architecture](docs/architecture/current.md), [source ownership map](docs/architecture/module-map.md) and [component change protocols](docs/architecture/component-change-protocols.md). [Format contracts](docs/architecture/contracts/formats.md) and [content identities](docs/architecture/contracts/identities.md) describe distinct persisted inputs and digests. Contributors read the root [cooperation rules](AGENTS.md) and [current plan](docs/PLAN.md).

The [frozen v2.2 reference HTML distribution (Chinese)](docs/distribution/multi-agent-development-platform.html) retains its original Linux deployment and training scope. It does not acquire later control-plane features through this link. The separate [editor comparison example](examples/editor-comparison/README.md) has its own Node build requirements.

Apache-2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE) and [third-party notices](THIRD_PARTY_NOTICES.md).
