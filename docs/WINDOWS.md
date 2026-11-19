<a id="windows-安装与使用"></a>
# Install and use Ergora on Windows

English · [简体中文](zh-CN/WINDOWS.md)

Ergora 0.2 provides a native Windows CLI and local graphical console using the same project, role, template and evaluation code as Linux. An updated Windows 11 x64 system, Python 3.11+ and Git for Windows are recommended. Windows 10 can also follow these installation steps; compatibility depends on the selected Agent and device policies. CI runs application and PowerShell installer checks on a Windows runner; it does not establish model or GPU quality for every configuration.

<a id="选择运行方式"></a>
## Choose an execution environment

|Capability|Native Windows|WSL2 / Linux|
|---|---|---|
|CLI, web console, project registration and layered tool selection|Supported|Supported|
|Copying the three templates, role contracts, work-unit DAGs and input compilation|Supported|Supported|
|Standalone Agent / nested Workflow definitions, complete resource revisions, preview / manifest / composition graph|Static editing, validation and sharing supported; complete packages can be exported|Supported; runtime admission remains separate|
|Fixed-task MCP, a composition leaf with Skill attachments, and formal v6 execution|Use WSL2/Linux; native scope creation explicitly refuses the operation|Task MCP needs its optional SDK in the same interpreter; complete execution also needs the reference runtime and a trusted container|
|Offline handoff-package verification|Supported by the basic CLI; no online service or SDK required|Supported|
|Collecting a closed original run's evidence index, budget and handoff|Use the Ergora entry point inside WSL2/Linux|Requires a registered complete reference runtime, Temporal and original materials|
|Standalone Codex / Claude Code role calls|Native `.exe`; each tool owns authentication|Linux CLI|
|Custom Agents, evaluators and GEPA proposers|Native programs or explicit interpreters; argv and UTF-8 stdin|Linux programs|
|SQLite memory, Skill versions, evaluation, adoption and rollback|Supported|Supported|
|ReMe HTTP, GEPA, bounded source observation, Temporal SDK / worker|Optional integrations; configure remote services separately|Optional integrations|
|mini-swe-agent Bash driver, native ForgeKernel campaigns|Use WSL2|Linux driver supported; prepare devices and models separately|
|Formal six-stage execution bridge, Supervisor, MLflow / Symphony / A2A reference deployment|Use the Linux environment inside WSL2|The complete reference executor additionally requires an explicitly enabled trusted Linux container|

A native installation does not deploy the complete reference services. Viewing or designing templates and running one role do not produce formal-task acceptance. The old [single-file HTML distribution](distribution/multi-agent-development-platform.html) remains the frozen Linux v2.2 release; install the Windows version from this repository.

Structural inheritance, serial/parallel dependencies, named ports and per-leaf default backends in the Agent and composition library are cross-platform static data. Importing or freezing does not start an Agent. Native backend calls through ordinary `agent run` differ from a composition leaf's `task-mcp` mode: the latter reads its fixed scope through Linux no-follow file descriptors. Installing the MCP SDK or authenticating a model on Windows does not remove that platform restriction. See the [three-template walkthrough](TEMPLATE_WALKTHROUGHS.md) for complete ancestor Skill reading and the page's v6 creation sequence; run its Linux steps inside WSL2. Windows CI covers its explicitly selected installation/application checks; it does not establish WSL2, both-backend or GPU execution results.

<a id="安装控制面"></a>
## Install the control plane

With Python 3.11+ and Git already installed, run the following in an ordinary PowerShell session. The capabilities described here ship on `main`. The clone and empty-environment ZIP instructions select that branch. In an existing clone, select `main` or pin the full commit required by the acceptance record, then run the installer. Identical package versions do not imply identical source.

```powershell
New-Item -ItemType Directory -Force "$HOME\source" | Out-Null
git clone --branch main https://github.com/626619403/Ergora.git "$HOME\source\Ergora"
Set-Location "$HOME\source\Ergora"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -AddToPath
& "$env:LOCALAPPDATA\Ergora\bin\ergora.exe" --version
& "$env:LOCALAPPDATA\Ergora\bin\ergora.exe" serve
```

Open `http://127.0.0.1:8977`. The console assets ship in the package; Node and a frontend build are unnecessary. `-AddToPath` adds the command directory to the current user's PATH. New terminals can use `ergora` directly; existing terminals can use the absolute path above. ExecutionPolicy in this command applies only to that PowerShell process. Organization policies may still require signed scripts or administrator deployment.

In an empty environment, download the [source ZIP for the same branch](https://github.com/626619403/Ergora/archive/refs/heads/main.zip), extract it to a persistent user directory, and open PowerShell in the directory containing `pyproject.toml`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -InstallPrerequisites -AddToPath
```

This option uses an existing `winget` to install missing Python 3.12 and Git for the current user and accepts the corresponding package agreements. It does not require changing the system PATH. If winget is unavailable, follow the [official App Installer / winget instructions](https://learn.microsoft.com/en-us/windows/package-manager/winget/), or install [Python](https://www.python.org/downloads/windows/) and [Git](https://git-scm.com/downloads/win) manually, open a new terminal and run the installer. This path avoids administrator privileges only when the software sources and device policies allow user-scope installation.

Optional arguments:

```powershell
.\scripts\install.ps1 -Profile research -AddToPath
# Legacy switches still add SDKs to the selected profile.
.\scripts\install.ps1 -WithGepa -WithTemporal -AddToPath
# Select an existing interpreter and separate installation directories.
.\scripts\install.ps1 -Python 'C:\Path\To\python.exe' -InstallRoot "$HOME\Apps\Ergora" -BinDir "$HOME\bin"
```

`-Profile` aliases `-InstallationProfile`; the choices are `control` (default), `development` and `research`. Both platforms consume the same [installation profiles](USAGE.md#选择安装组合). They install SDKs; complete six-stage execution remains on Linux/WSL2. Rerunning the installer preserves the separate data directory. Returning to a smaller profile does not uninstall existing SDKs. After installation, use `ergora tools profiles` to inspect the recipes; check authentication, connections and task prerequisites separately.

Default directories:

|Content|Path|
|---|---|
|Application virtual environment|`%LOCALAPPDATA%\Ergora\app\venv`|
|Native command and installation ownership record|`%LOCALAPPDATA%\Ergora\bin\ergora.exe`, `ergora-install.json`|
|Project configuration, SQLite, memory, candidates and run archives|`%LOCALAPPDATA%\Ergora\data`|

`ERGORA_INSTALL_ROOT`, `ERGORA_BIN_DIR` and `ERGORA_PYTHON` can replace the corresponding installer arguments. Runtime data has a location independent of the installation. Set `$env:ERGORA_HOME = "$HOME\ErgoraData"` before starting, or use `ergora --home PATH ...`. The installer does not start background services, log in to Agents, invoke models or run training.

Developers can instead create an environment with `py -3 -m venv .venv`, then use `.\.venv\Scripts\python.exe -m pip install '.[dev,web,gepa,temporal]'` and `.\.venv\Scripts\ergora.exe serve`. Activating a script is unnecessary.

<a id="agent-安装与认证"></a>
## Install and authenticate Agents

Codex is the default implementation and review backend. Install its native Windows CLI following the [official OpenAI CLI instructions](https://learn.chatgpt.com/docs/codex/cli), then complete account or API authentication during the first interactive `codex` session. See the [official Windows sandbox documentation](https://learn.chatgpt.com/docs/windows/windows-sandbox) for version, permission and device requirements. Keep the native Codex sandbox; the Linux `current-container` option cannot be used on Windows.

Claude Code is an optional role implementation. Follow its [official Windows installation and Git Bash requirements](https://code.claude.com/docs/en/setup), and complete its own authentication. Ergora does not proxy account login or write keys to project JSON or the repository.

Check in the same terminal that will start Ergora:

```powershell
Get-Command codex.exe
codex.exe --version
# When selecting Claude Code:
Get-Command claude.exe
claude.exe --version
```

Ergora prefers the matching `.exe`. It explicitly refuses `.cmd` and `.bat` entry points for Agents, evaluators and proposers to prevent Windows' implicit shell from rewriting arguments. If an npm command only supplies a batch shim, use the tool's native installer. Start custom scripts through an explicit interpreter, for example `{"tool":"command","argv":["C:\\Python312\\python.exe","C:\\Agents\\review.py"]}`. Relative script arguments resolve from the business project's working directory. See the [Agent guide](AGENT_BACKENDS.md) and [integration guide](INTEGRATIONS.md) for the complete structured protocol.

Command input, archives and application-owned text files use UTF-8. The CLI accepts a UTF-8 BOM for binding JSON, evaluation manifests, prompts, memory bodies and Skill frontmatter. PowerShell 5.1's `Set-Content -Encoding UTF8` can write these inputs. Use UTF-8 without a BOM for external JSON consumed by the original contract compiler to retain compatibility with the frozen reference implementation.

<a id="首个项目"></a>
## Create a first project

Create your own Git repository first. Issues remain in that project; a central management repository is unnecessary:

```powershell
git init "$HOME\source\my-project"
ergora project add my-project --repo "$HOME\source\my-project"
ergora templates copy repository-governance "$HOME\source\my-project\workflow-governance"
ergora tools doctor my-project
ergora serve
```

In the web console, select tools by role, save memory with provenance, import Skills or edit template work units. The pages and CLI share state. Use the actual revision from `ergora project show my-project` in binding changes:

```powershell
'{"tool":"codex"}' | Set-Content -Encoding UTF8 reviewer.json
'Review the repository and summarize risks.' | Set-Content -Encoding UTF8 review-request.md
ergora project show my-project
ergora project bind my-project reviewer --binding reviewer.json --revision 1
ergora agent run my-project reviewer --prompt review-request.md --timeout 300
ergora agent runs my-project
```

`agent run` uses the authenticated model and may incur charges. For a first inspection, the configuration pages and `doctor` are sufficient. A successful call establishes that the process and required output structure passed; it is not candidate acceptance for the formal workflow. See [daily page operations](USAGE.md#页面操作) and the [training guide](TRAINING.md) for the respective steps and boundaries.

On Windows, commands and source fetching use a Job Object to manage their lifecycle. Timeout, cancellation or controller shutdown stops their local descendants. It does not restrict that user's file or network access or provide a security sandbox for each Agent. Corresponding services remain responsible for cancelling remote API requests and external compute. Run the application as an ordinary user with trusted projects. Use Ctrl+C for foreground CLI tasks. Source observation can also be cancelled from the page; check its terminal state.

Local `training submission` / `training cancellation` commands can read saved operation records on native Windows without the Temporal SDK. `training baseline-preview` previews the complete baseline; actual `init-baseline` uses the original fcntl lock and requires Linux/WSL2. Neither requires an SDK or service; see [baseline initialization](TRAINING.md#预览与初始化基线). `training runner-preview / register-runner` uses the original registrar and requires Linux/WSL2 with `ergora[temporal]`, without a service; see [trusted runner registration](TRAINING.md#预览与登记可信-runner). `training experiment-preview / prepare / resume-prepare` also requires Linux/WSL2 and `ergora[temporal]`. Although `training preparation` does not require the SDK, its current entry point remains Linux/WSL2-only; see [experiment preparation and recovery](TRAINING.md#精确准备实验与恢复部分发布). Actual `training start` / `resume-start` / `cancel` / `resume-cancel` and the original-executor observation in `stop-status` use Linux/WSL2. Windows Job Objects do not manage those remote or training jobs. See [training cancellation and stop observations](TRAINING.md#取消原运行与分别观察停止事实) for the steps and result semantics.

<a id="接收交接包并离线核对"></a>
## Receive and verify a handoff package offline

Save the sender's exported ZIP and an independently obtained expected SHA on this machine, then run in PowerShell:

```powershell
ergora handoff verify .\task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

The basic installation can verify the package without starting the console, Temporal or a model, and without extracting or executing the materials. `verified` means the packaged bytes match the declared relationships among contracts, receipts and materials. It does not authenticate the source or infer successful execution; the original cancellation result remains unchanged. A digest carried by the package itself does not prove provenance. Verify candidate code and original history separately. See the [handoff guide](USAGE.md#收集与离线核对交接包) for the format, limits and Linux-side collection.

<a id="wsl2-完整流程"></a>
## Run the complete workflow in WSL2

Local Supervisor management through `ergora services status/start/stop/logs/shutdown` runs on Linux/WSL2. Native Windows explicitly returns WSL2 guidance. Installing the control plane or Temporal SDK does not start these services; see [explicit service management](USAGE.md#显式服务管理).

When the complete reference executor or Linux tools are needed, enable WSL2 on the Windows host using [Microsoft's WSL installation instructions](https://learn.microsoft.com/en-us/windows/wsl/install). This usually requires an administrator to enable system components and restart the host. Without host privileges, ask an administrator to provide WSL2 or use an existing Linux machine.

Clone the repository again inside the WSL2 Linux home and follow the [Linux installation guide](USAGE.md#从空环境安装). The complete reference distribution still requires its supported trusted Linux container. Entering WSL2 alone does not satisfy container admission or automatically enable execution. See the two packaged reference manuals for deployment, Docker and execution admission steps.

Install interpreters, Agents and dependencies separately on Windows and WSL2, and register each platform's business-repository paths separately. Do not copy virtual environments or share one SQLite state directory between active writers. Stop writers and retain backups before migrating across systems, then recheck absolute paths and tool bindings. Skill executable bits and line endings may affect their digests. Reimport and evaluate Skills on the new system; do not reuse old-machine evidence directly. GPU training still depends on host drivers, WSL GPU support and the selected tools' requirements.

<a id="升级备份与卸载"></a>
## Upgrade, back up and uninstall

Stop the console and in-flight tasks, select the desired published source commit, then rerun the same installation command with the same directory arguments. The installer checks the existing entry point's ownership, interpreter path and SHA. It refuses to overwrite another application's or a modified entry point. Preserve conflicting files and choose a new `-BinDir`. The same source can be installed repeatedly; project state remains in the separate data directory.

After stopping writers, back up the complete `ERGORA_HOME` (the default data directory), business Git repositories and external tool configuration. Reinstall the application on the new machine, then check every project path and login. See [recovery and maintenance](USAGE.md#远程访问恢复与维护) for restore and deletion semantics.

Registering a new project at a new path, importing exact templates and choosing role backends is [rebuilding a new environment](USAGE.md#换机与新项目重建). Continuing historical tasks requires the same platform, original absolute home and matching state. A control-plane backup does not include external execution CONFIG/STATE, Temporal, business Git or authentication. The current database schema is 6, migrated in order when the application formally opens it; package version 0.2.0 does not distinguish source or data versions. Before rolling back, preserve the upgraded state, then restore the matching old application and old backup. Do not lower user_version or only switch Git code. Use the [coordinated recovery guide](BACKUP_RECOVERY.md) for a complete Linux/WSL2 stack. Windows application CI does not establish recovery of active workflows.

The control plane offers complete offline backups without administrator privileges. Stop the console, workers and other work, and reconcile external jobs first:

```powershell
ergora state info
ergora state backup "$HOME\Ergora-backups\snapshot-001" --offline
ergora state verify-backup "$HOME\Ergora-backups\snapshot-001"
```

To restore, first use the home path from `state info` to move the current directory to another persistent location and preserve it. Then run `ergora state restore "$HOME\Ergora-backups\snapshot-001" --offline`. With a custom home, use `ergora --home ORIGINAL_HOME state restore ...`. The destination must not exist and must match the original Windows home recorded in the manifest. The tool does not rewrite absolute paths or convert Skill identities between Windows and WSL2. See [offline backup and recovery](architecture/state-migrations.md#离线完整备份与恢复) for the full file list, database versions and restore boundaries.

To uninstall, stop foreground processes and delete the application directory and this installation's `ergora.exe` / `ergora-install.json`. Remove the corresponding bin entry from the user PATH. The data directory is a separate asset; decide explicitly whether to retain its history. Do not delete the entire `%LOCALAPPDATA%\Ergora` as though it contained only reproducible program files.
