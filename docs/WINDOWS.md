# Windows 安装与使用

Ergora 0.2 提供原生 Windows CLI 和本地图形控制台，与 Linux 使用同一套项目、角色、模板和评价代码。建议使用更新后的 Windows 11 x64、Python 3.11+ 和 Git for Windows；Windows 10 也可按以下步骤安装，实际兼容性需结合所选 Agent 与系统策略确认。持续集成在 Windows runner 上验证应用与 PowerShell 安装器，不代表已完成每种模型或 GPU 的效果验收。

## 选择运行方式

|能力|Windows 原生|WSL2 / Linux|
|---|---|---|
|CLI、网页、项目注册与分层工具选择|支持|支持|
|三个模板的复制、角色合同、工作单元 DAG 与输入编译|支持|支持|
|Codex / Claude Code 独立角色调用|原生 `.exe`，认证由各工具完成|Linux CLI|
|自定义 Agent、evaluator、GEPA proposer|原生程序或显式解释器；使用 argv 和 UTF-8 stdin|Linux 程序|
|SQLite 记忆、Skill 版本、评价、采用和回退|支持|支持|
|ReMe HTTP、GEPA、有界资料观察、Temporal SDK / worker|可选接入；远端服务另外配置|可选接入|
|mini-swe-agent Bash 驱动、ForgeKernel 原生 campaign|使用 WSL2|支持 Linux 驱动，设备与模型另行准备|
|六阶段正式执行桥接、Supervisor、MLflow / Symphony / A2A 参考部署|使用 WSL2 内的 Linux 环境|完整参考执行器还需要显式启用可信 Linux 容器|

原生安装不会部署完整参考服务。查看、设计模板与运行一个角色，并不产生正式任务验收。旧 [单文件 HTML](distribution/multi-agent-development-platform.html) 仍是冻结的 Linux v2.2 发行；Windows 版本从本仓库安装。

## 安装控制面

已有 Python 3.11+、Git 时，在普通 PowerShell 中执行。以下使用 Windows 功能分支，合并或发布后可改用相应版本：

```powershell
New-Item -ItemType Directory -Force "$HOME\source" | Out-Null
git clone --branch main https://github.com/626619403/Ergora.git "$HOME\source\Ergora"
Set-Location "$HOME\source\Ergora"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -AddToPath
& "$env:LOCALAPPDATA\Ergora\bin\ergora.exe" --version
& "$env:LOCALAPPDATA\Ergora\bin\ergora.exe" serve
```

打开 `http://127.0.0.1:8977`。控制台资源随包提供，无需 Node 或前端构建。`-AddToPath` 将命令目录加入当前用户 PATH，新终端可直接使用 `ergora`；已有终端用上述绝对路径。命令中的 ExecutionPolicy 仅作用于这次 PowerShell 进程；组织策略仍可能要求使用签名脚本或由管理员部署。

空环境先从 GitHub 下载 [源码 ZIP](https://github.com/626619403/Ergora/archive/refs/heads/main.zip)，解压到用户的持久目录，在包含 `pyproject.toml` 的目录打开 PowerShell：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -InstallPrerequisites -AddToPath
```

该选项使用已有的 `winget` 为当前用户安装缺失的 Python 3.12 和 Git，并接受相应软件包协议；不需要修改系统 PATH。没有 winget 时，按 [App Installer / winget 官方说明](https://learn.microsoft.com/en-us/windows/package-manager/winget/) 安装它，或手动安装 [Python](https://www.python.org/downloads/windows/) 和 [Git](https://git-scm.com/downloads/win)，重新打开终端后运行安装器。只有在软件源和设备策略允许用户范围安装时，这条路径才无需管理员权限。

可选参数：

```powershell
.\scripts\install.ps1 -WithGepa -WithTemporal -AddToPath
# 指定已有的解释器及独立安装目录
.\scripts\install.ps1 -Python 'C:\Path\To\python.exe' -InstallRoot "$HOME\Apps\Ergora" -BinDir "$HOME\bin"
```

默认目录：

|内容|路径|
|---|---|
|应用虚拟环境|`%LOCALAPPDATA%\Ergora\app\venv`|
|原生命令与安装归属记录|`%LOCALAPPDATA%\Ergora\bin\ergora.exe`、`ergora-install.json`|
|项目配置、SQLite、记忆、候选、运行归档|`%LOCALAPPDATA%\Ergora\data`|

`ERGORA_INSTALL_ROOT`、`ERGORA_BIN_DIR`、`ERGORA_PYTHON` 可代替同名安装参数。运行数据位置独立于安装位置，可在启动前设置 `$env:ERGORA_HOME = "$HOME\ErgoraData"`，或使用 `ergora --home PATH ...`。安装器不启动后台服务、不登录 Agent、不调用模型、不运行训练。

开发者也可以自行 `py -3 -m venv .venv`，再用 `.\.venv\Scripts\python.exe -m pip install '.[dev,web,gepa,temporal]'` 和 `.\.venv\Scripts\ergora.exe serve`；无需激活脚本。

## Agent 安装与认证

默认实现与审查均为 Codex。按 [OpenAI 官方 CLI 安装说明](https://learn.chatgpt.com/docs/codex/cli) 安装 Windows 原生 CLI，在首次 `codex` 交互中完成账号或 API 认证。Windows 沙箱的版本、权限及设备要求见 [官方 Windows sandbox 文档](https://learn.chatgpt.com/docs/windows/windows-sandbox)。保持 Codex 原生 sandbox；Linux 的 `current-container` 选项不能用于 Windows。

Claude Code 是可选角色实现，按 [官方 Windows 安装与 Git Bash 要求](https://code.claude.com/docs/en/setup) 安装并完成其自身认证。Ergora 不代理账号登录，也不把密钥写入项目 JSON 或仓库。

在启动 Ergora 的同一终端检查：

```powershell
Get-Command codex.exe
codex.exe --version
# 选择 Claude Code 时
Get-Command claude.exe
claude.exe --version
```

Ergora 优先查找同名 `.exe`；Agent / evaluator / proposer 的 `.cmd`、`.bat` 入口会明确拒绝，避免 Windows 隐式 shell 改写参数。npm 生成的命令若只有 batch shim，请使用工具的原生安装；自定义脚本通过明确的解释器启动，例如 `{"tool":"command","argv":["C:\\Python312\\python.exe","C:\\Agents\\review.py"]}`。相对脚本参数以业务项目为工作目录。完整结构化协议见 [Agent 手册](AGENT_BACKENDS.md) 与 [工具接入手册](INTEGRATIONS.md)。

命令输入、归档及自有文本文件使用 UTF-8；CLI 的绑定 JSON、评价 manifest、提示、记忆正文和 Skill frontmatter 接受 UTF-8 BOM。PowerShell 5.1 的 `Set-Content -Encoding UTF8` 可用于这些输入。原合同编译器的外部 JSON 建议使用无 BOM 的 UTF-8，以保持冻结参考实现的兼容性。

## 首个项目

先建立自己的 Git 仓库；工单仍属于该项目，无需统一管理仓库：

```powershell
git init "$HOME\source\my-project"
ergora project add my-project --repo "$HOME\source\my-project"
ergora templates copy repository-governance "$HOME\source\my-project\workflow-governance"
ergora tools doctor my-project
ergora serve
```

网页中按角色选择工具，保存带来源的记忆，导入 Skill，或编辑模板工作单元。页面与 CLI 共用状态。绑定配置中的修订号以 `ergora project show my-project` 的实际输出为准：

```powershell
'{"tool":"codex"}' | Set-Content -Encoding UTF8 reviewer.json
'Review the repository and summarize risks.' | Set-Content -Encoding UTF8 review-request.md
ergora project show my-project
ergora project bind my-project reviewer --binding reviewer.json --revision 1
ergora agent run my-project reviewer --prompt review-request.md --timeout 300
ergora agent runs my-project
```

最后一条调用会使用已认证的模型，可能产生费用；首次操作也可只使用页面配置与 `doctor`。成功调用仅表示进程与所需输出结构通过，不等于正式流程的候选验收。详细页面操作见 [日常使用手册](USAGE.md#页面操作)，训练边界见 [训练手册](TRAINING.md)。

Windows 命令与资料抓取使用 Job Object 管理生命周期：超时、取消或控制器关闭时停止其本地后代。它不限制该用户的文件、网络访问，不提供每 Agent 的安全沙箱；远程 API 请求和外部计算服务的取消仍由对应服务负责。应用以普通用户、可信项目方式运行。CLI 前台任务可用 Ctrl+C；资料观察也可从页面请求取消并核对终态。

## WSL2 完整流程

需要完整参考执行器或 Linux 工具时，按 [Microsoft WSL 安装说明](https://learn.microsoft.com/en-us/windows/wsl/install) 在宿主 Windows 启用 WSL2。这通常需要管理员启用系统组件和重启；无宿主权限时请让管理员预先提供 WSL2，或使用已有 Linux 主机。

在 WSL2 的 Linux home 内重新 clone 并按 [Linux 安装手册](USAGE.md#从空环境安装) 安装。完整参考发行仍要求其支持的可信 Linux 容器；仅进入 WSL2 不会通过容器准入，也不会自动启用执行。参考发行部署、Docker 与执行准入步骤见两本随包参考手册。

Windows 与 WSL2 分别安装解释器、Agent 和依赖，分别注册业务仓库路径。不要复制虚拟环境或共享同一份正在写入的 SQLite 状态目录；跨系统迁移需停止写入、保留备份、重新核对绝对路径与工具绑定。Skill 文件的执行位和换行可能影响摘要，跨系统重新导入与评价，不能直接沿用旧机器证据。GPU 训练仍取决于主机驱动、WSL GPU 支持及所选工具要求。

## 升级、备份与卸载

停止控制台和在途任务，在源码目录切换到所需已发布提交，再运行相同安装命令与相同目录参数。安装器会核对已有入口的归属、解释器路径和 SHA，拒绝覆盖其他软件或被修改的入口；出现冲突时保留原文件，选择新的 `-BinDir`。同一源码可重复安装，项目状态保留在独立 data 目录。

停止写入后备份完整 `ERGORA_HOME`（默认 data）、业务 Git 仓库及外部工具配置。换机后重新安装应用并核对每个项目路径和登录状态。恢复与删除的语义见 [日常使用手册](USAGE.md#远程访问恢复与维护)。

控制面提供离线完整备份入口，不要求管理员权限。在停止控制台、worker 与其他工作并对账外部作业后：

```powershell
ergora state info
ergora state backup "$HOME\Ergora-backups\snapshot-001" --offline
ergora state verify-backup "$HOME\Ergora-backups\snapshot-001"
```

需要恢复时，先按 `state info` 返回的 home 路径将当前目录移到另一个持久位置保留，再运行 `ergora state restore "$HOME\Ergora-backups\snapshot-001" --offline`。如果使用自定义 home，写为 `ergora --home ORIGINAL_HOME state restore ...`。目标必须不存在，且与清单记录的 Windows 原 home 一致；工具不会改写绝对路径或跨 Windows / WSL2 转换 Skill 身份。详细文件清单、数据库版本及恢复边界见 [升级与恢复说明](architecture/state-migrations.md#离线完整备份与恢复)。

卸载时停止前台进程，删除应用目录与属于此次安装的 `ergora.exe` / `ergora-install.json`；从用户 PATH 移除对应 bin 项。data 目录是独立资产，按是否保留历史自行处理。不要把整个 `%LOCALAPPDATA%\Ergora` 当作只有可重建程序的目录直接删除。
