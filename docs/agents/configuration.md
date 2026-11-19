# Configure and authenticate Agents

English · [Documentation](../README.md) · [简体中文](../zh-CN/agents/configuration.md)

## Install and authenticate Agent CLIs

The control-plane installer does not install model CLIs. Default roles invoke `codex` from PATH; selecting Claude Code invokes `claude`. On Linux, you can save the official installer first and then execute it:

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://chatgpt.com/codex/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/codex.sh"
sh "$HOME/.local/share/ergora-tools/installers/codex.sh"
export PATH="$HOME/.local/bin:$PATH"
codex --version
codex
```

During the first interactive `codex` session, choose account or API authentication. See the [official OpenAI installation instructions](https://learn.chatgpt.com/docs/codex/cli) and [authentication instructions](https://learn.chatgpt.com/docs/auth). Standalone role invocations use Codex's own configuration; configure the formal reference model through the [native configuration step](#configure-formal-reference-execution) below. The reference model configurator uses native Codex authentication when only `--model MODEL` is supplied; custom API providers can specify `--base-url` and an optional `--env-key` reference. A missing fixed API-key variable does not block a backend that can authenticate itself. Provider requirements still apply, and actual authentication failures remain task failures. Start services with the intended HOME/CODEX_HOME; Ergora does not log in or copy login state.

Claude Code is optional. Install it according to the [official setup instructions](https://code.claude.com/docs/en/setup):

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://claude.ai/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
bash "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
export PATH="$HOME/.local/bin:$PATH"
claude --version
claude
```

Complete [Claude authentication](https://code.claude.com/docs/en/authentication) during the first interactive session. The standalone installers above do not require Node.js; if you use npm or another installation method, follow its official dependency requirements. Confirm that the commands are available in the same shell that starts Ergora, then run `ergora tools doctor PROJECT` and execute an explicit small task. Installation/version checks do not establish authentication or acceptance of a model task. See the [Agent guide](backends.md) for the pinned-source installation, model and device requirements of mini-swe-agent and ForgeKernel.

## Configure formal reference execution

First satisfy the [current native provisioning/source-identity gate](../install/linux.md#prepare-the-formal-reference-runtime). The commands below apply only to that separately provisioned current installation, with initialized native configuration. Replace `/PATH/TO/CURRENT_NATIVE` with its actual registered path. The frozen v2.2 HTML bootstrap has different authentication behavior and does not acquire this current path through a link. Select a model supported by the current Codex backend; this native-auth path requires no fixed API-key variable:

```bash
python3 "/PATH/TO/CURRENT_NATIVE/bootstrap/configure-model.py" \
  --model YOUR_SUPPORTED_MODEL_ID
```

For an explicitly selected custom Responses provider, supply its real URL and optional credential-variable reference:

```bash
python3 "/PATH/TO/CURRENT_NATIVE/bootstrap/configure-model.py" \
  --model YOUR_SUPPORTED_MODEL_ID \
  --base-url https://YOUR_PROVIDER/v1 \
  --env-key YOUR_PROVIDER_KEY
```

`--env-key` is optional and accepts a variable name rather than its secret value. The configurator reports `authentication: not_checked`; writing configuration proves no login, connectivity or successful model task. Use the intended HOME/CODEX_HOME for the processes that start the runtime. Provider requirements and actual authentication failures remain visible. Configure before starting selected services, or explicitly restart the relevant stopped/owned services after a change; the configurator does not do this automatically.

## Your first project and tool choices

“New project” at the upper right of the page registers an existing Git repository; GitHub/GitLab is not required. Select each layer separately on the tool bindings page:

|Layer|Available implementations|Actual consumers|
|---|---|---|
|Inventory / planning / implementation / review and training proposal roles|Codex, Claude Code, custom protocol; implementation can also use mini-swe-agent|Standalone invocations and the optional six-stage bridge|
|Native kernel generation|Manual, ForgeKernel|Local native campaigns; independent trusted revalidation is separate|
|Memory|SQLite, ReMe HTTP|Save, revise, retrieve, synchronize|
|Skill optimization|Manual import, GEPA + JSON proposer|Bounded candidate search and evidence recording|
|Source material|Explicit URL|Bounded observation, snapshots and review|
|Research scheduling|Manual, Temporal Schedule|CLI worker / Schedule|
|Project issues|Local manual, GitHub, GitLab|Read sources through CLI/HTTP, freeze snapshots, explicitly comment on exported candidates; GitHub can add one existing candidate label by native ID|

Authenticate using each tool's login or environment variables. Configuration stores only credential variable names; do not enter secrets on the page. Select models separately for Codex and Claude Code; both implementation and review default to Codex. Custom commands receive prompts on stdin and start through argv, without shell concatenation. Installed, connected, authenticated and accepted through a task are distinct states.

## Effective bindings and run snapshots

`ergora project config PROJECT_ID` and `GET /api/projects/PROJECT_ID/configuration` return the same read-only result. `project show` still returns the saved original document. A lightweight project's effective view uses `schema_version: 1`, `resolution_version: 1` and `scope: project-bindings`. A unified registered project uses `scope: registered-project` and includes the normalized definition, digest and publication status in `registration`, covering templates, execution directories and checks/policies. Template inputs, tool-internal defaults, authentication and service connections remain owned by their respective entry points. See [project definitions](../projects/registration.md) for unified registration, read-only preview/explicit import of legacy registrations and recovery commands.

`project` contains ID, Git root and current revision. Each `layers` entry has `binding`, `source` and `validation`. Source `project` identifies a saved field. `inherited` means an old project missing a role inherits `bindings.implementer`. `legacy-default` means a missing support layer uses a fixed compatibility default: memory=sqlite, research=urls, other support layers=manual. New projects still save the complete recommended bindings in effect at creation.

`sha256` is computed after removing itself, using UTF-8 JSON with sorted keys, compact separators, preserved Unicode and nonfinite numbers refused. It identifies this view's content and cannot replace evidence digests for formal tasks, artifacts or trusted checks. View validation invokes no tools. Invalid inheritance reports the exact layer error; explicitly save a compatible binding. Check authentication and availability separately through doctor.

A standalone Agent call saves this view as `configuration` in its run record before starting the tool, retaining original `binding/project_revision`. Formal tasks created through the primary entry point freeze the view at creation. Older creation paths add it to `agent-bindings.json` when first using the optional executor. Later project or recommended-default changes do not update in-flight tasks. Older tasks without the extra field continue using their original binding snapshot, without fabricating historical provenance; old run records are not rewritten. Actual Skill/memory context is recorded separately in invocation records. This snapshot does not claim to freeze all external tools' internal behavior.

Continue: [Register a project](../projects/registration.md) · [Select and invoke Agent backends](backends.md).
