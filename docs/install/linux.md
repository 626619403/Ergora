# Install on Linux or WSL2

English · [Documentation](../README.md) · [简体中文](../zh-CN/install/linux.md)

Ergora provides a local CLI and graphical control plane for Linux / Windows, while retaining the complete six-stage Linux reference distribution from v2.2. You can use the control plane on its own first, then connect project tools, issues, services and experiment environments as needed. See the [Windows guide](windows.md) for PowerShell installation, Agents and WSL2 support. See [Plan and progress](../PLAN.md) for implemented capabilities and the scope actually accepted.

When choosing a template for the first time, follow the [three-template getting-started journey](../development/templates.md) to assemble specialists, choose a backend for each instance, create through the v6 page, recover with the original ID and prepare training proposals. Then return to this guide for specific commands.

If you already have a local candidate, you can start with an [exact PR/MR review package](../review/materials.md): freeze complete Git objects, original requirements, explicit callers and ancestor rules without registering a project or logging into a model. You can also use `review collect` to bind an explicit GitHub/GitLab source through read-only access, then verify the package offline. Automatic domain review and posting feedback remotely are implemented separately.

## Install in a clean environment

The basic requirements are Linux, Git, Python 3.11+ and venv / pip. On Ubuntu 24.04, you can install the system prerequisites first:

This guide uses the `main` branch, which includes the current composition and execution features. In an existing clone, select `main`, or pin the full commit from the acceptance record you need, before running the installer from that source. An identical package version alone does not establish source identity.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv
git clone --branch main https://github.com/626619403/Ergora.git
cd Ergora
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
ergora serve
```

Open `http://127.0.0.1:8977` on the machine running the service. Web assets and graph components ship in the Python package; Node, a runtime CDN and a frontend build are not required. The installer places the application in `~/.local/share/ergora-app/venv` and the command in `~/.local/bin/ergora`. Runtime data defaults to the separate `~/.local/share/ergora/` directory; use `ERGORA_HOME` or the global `--home` option to select a persistent directory. Containers should persist these directories and the business repository.

If Python is already available, you can also install into your own environment:

```bash
python3 -m venv .venv
.venv/bin/pip install '.[web]'
.venv/bin/ergora serve
```

### Choose an installation profile

The default profile is `control`. From the source directory, run `bash scripts/install.sh --profile development` or `--profile research`; on Windows, use `-Profile`, as described in the [Windows guide](windows.md).

|Profile|Installed SDKs|Additional setup|
|---|---|---|
|`control`|Web console|The selected Agent CLI and authentication; local projects can start with SQLite and manual operations|
|`development`|Web, Temporal|The complete six-stage flow requires the Linux/WSL2 reference runtime, services and Agents|
|`research`|Web, Temporal, GEPA|Evaluators, proposers and selected source/experiment services; install GPU tools for the task as needed|

After installation, run `ergora tools profiles` to view recipes from the same source; the local API is `GET /api/installation-profiles`. These descriptions are installation recipes. Check `ergora tools doctor PROJECT` and task acceptance separately for actual status. Installation profiles do not start services, log into models or run training. An installed SDK does not establish service connectivity, tool authentication or validated results.

The existing `--with-gepa` and `--with-temporal` options remain available and add dependencies to the selected profile as a set, for example `bash scripts/install.sh --profile development --with-gepa`. Rerun the installer in the same directory to upgrade or add packages; switching back to a smaller profile does not automatically uninstall SDKs. If a source feature has not been released, first switch to the feature branch supplied by the maintainer.

### Prepare offline dependencies

In a connected environment, prepare all build/runtime wheels for the target OS, Python version and architecture, then install in a matching environment. Run the following commands from the source directory; you may choose a different cache directory:

```bash
mkdir -p "$HOME/.local/share/ergora-tools/wheels"
python3 -m pip wheel --wheel-dir "$HOME/.local/share/ergora-tools/wheels" \
  '.[web,temporal,gepa]' setuptools wheel
PIP_NO_INDEX=1 PIP_FIND_LINKS="$HOME/.local/share/ergora-tools/wheels" \
  bash scripts/install.sh --profile research
```

The installer still uses pip to read the local source and cache. If a compatible wheel or build dependency is missing, pip fails visibly; complete the cache and retry. The offline cache does not include external Agents, reference-service binaries, system packages or models; prepare them separately according to their instructions. Windows also uses pip's `PIP_NO_INDEX`/`PIP_FIND_LINKS` environment variables and wheels built for Windows.

## Prepare the formal reference runtime

The control-plane installer does not provision the full native execution stack. Current execution needs a separately provisioned installation whose local/upstream sources match the current package's validation contract, with its selected Python/SDK/tool dependencies and configuration/state initialized. Registration, trusted-container acceptance and actual service/backend availability remain separate prerequisites.

The supported current source-preparation command is:

```bash
ergora reference prepare-training --directory "$HOME/ergora-native/current-source" \
  --protocol training-executor-admission-v3
```

This materializes a new current training-native source tree and descriptor, verifies its complete source identity, and reports `dependencies_installed: false`, `runtime_started: false` and `execution_authorized: false`. It does not create a complete native environment, initialize all configuration/services or install every bootstrap prerequisite. The Ergora CLI exposes no general current-native provisioning command; source preparation alone is not a runnable installation. Missing or mismatched prerequisites fail the actual admission checks rather than falling back to older sources.

Use [current native model configuration](../agents/configuration.md#configure-formal-reference-execution) only after the selected current installation is provisioned. [Project registration](../projects/registration.md), [selected service control](../operations/services.md) and task admission check their own real prerequisites. A successful control-plane install or resource verification does not certify that environment, authentication, model execution or process stopping.

The [frozen v2.2 HTML distribution (Chinese)](../distribution/multi-agent-development-platform.html) is an independent original-scope archive with its own installer and authentication behavior. Exporting/running that historical installer does not produce the current source fingerprints or acquire current native-auth support. Follow its original manual for that frozen distribution; do not chain its bootstrap into the current instructions above.

Continue: [Configure and authenticate Agents](../agents/configuration.md) · [Register a project](../projects/registration.md).
