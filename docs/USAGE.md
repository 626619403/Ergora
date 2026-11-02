# 安装与日常使用

Ergora 提供 Linux / Windows 本地 CLI 与图形控制面，并保留 v2.2 的完整六阶段 Linux 参考发行。控制面可以先独立使用；项目工具、工单、服务和实验环境按需接入。Windows 的 PowerShell 安装、Agent 与 WSL2 范围见 [Windows 手册](WINDOWS.md)。已实现的能力和实际验收范围见 [计划与进度](PLAN.md)。

## 从空环境安装

基础环境为 Linux、Git、Python 3.11+、venv / pip。Ubuntu 24.04 可以先安装系统基础包：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv
git clone --branch main https://github.com/626619403/Ergora.git
cd Ergora
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
ergora serve
```

在服务所在机器打开 `http://127.0.0.1:8977`。网页资源和图组件随 Python 包安装，不需要 Node、运行时 CDN 或前端构建。安装脚本把应用放在 `~/.local/share/ergora-app/venv`，命令放在 `~/.local/bin/ergora`；运行数据默认放在独立的 `~/.local/share/ergora/`，可用 `ERGORA_HOME` 或全局 `--home` 指定持久目录。容器应持久化这些目录及业务仓库。

已经有 Python 时也可以在自己的环境安装：

```bash
python3 -m venv .venv
.venv/bin/pip install '.[web]'
.venv/bin/ergora serve
```

### 选择安装组合

默认组合为`control`。可在源码目录运行`bash scripts/install.sh --profile development`或`--profile research`；Windows使用`-Profile`，见[Windows手册](WINDOWS.md)。

|组合|安装的SDK|另需配置|
|---|---|---|
|`control`|Web控制台|所选Agent CLI及认证；本地项目可先用SQLite与手动操作|
|`development`|Web、Temporal|完整六阶段需Linux/WSL2参考运行时、服务及Agent|
|`research`|Web、Temporal、GEPA|评价器、提案器、所选资料/实验服务；GPU工具按任务安装|

安装后运行`ergora tools profiles`查看同源配方；本地API为`GET /api/installation-profiles`。该描述是安装配方，实际状态另看`ergora tools doctor PROJECT`及任务验收。安装组合不启动服务、登录模型或执行训练。SDK存在不代表服务可连接、工具已认证或效果已经验证。

原有`--with-gepa`、`--with-temporal`仍可使用，按集合添加到所选组合，例如`bash scripts/install.sh --profile development --with-gepa`。在同一目录重跑安装器可升级或补装；改回较小组合不会自动卸载已装SDK。源码特性尚未发布时，先切换到维护者提供的功能分支。

### 准备离线依赖

在联网环境为目标OS、Python版本和架构准备全部构建/运行wheel，再在同类环境安装。以下命令在源码目录执行，缓存目录可自行指定：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/wheels"
python3 -m pip wheel --wheel-dir "$HOME/.local/share/ergora-tools/wheels" \
  '.[web,temporal,gepa]' setuptools wheel
PIP_NO_INDEX=1 PIP_FIND_LINKS="$HOME/.local/share/ergora-tools/wheels" \
  bash scripts/install.sh --profile research
```

安装器继续通过pip读取本地源码和缓存。缺少兼容wheel或构建依赖时，pip会明确失败，补齐缓存后重试。离线缓存不包含外部Agent、参考服务二进制、系统包或模型；它们按各自说明另行准备。Windows也使用pip的`PIP_NO_INDEX`/`PIP_FIND_LINKS`环境变量及适合Windows的wheel。

## 升级与持久数据

升级前停止控制台、worker、执行器和其他 CLI 工作，确认在途任务状态，并备份完整持久目录及业务仓库。首次打开旧控制面数据库时会事务化升级，自动保存升级前的数据库快照；这个快照不包含 Skill、来源和运行文件，不能代替完整备份。新版本数据库拒绝旧程序写入，回退需要恢复匹配的数据库和文件，而不是仅切换代码。具体版本、错误处理和回退步骤见 [数据库升级说明](architecture/state-migrations.md)。

已有数据时，可以在停止相关工作后运行（Windows PowerShell 路径示例见 [Windows 手册](WINDOWS.md#升级备份与卸载)）：

```bash
ergora state info
ergora state backup "$HOME/ergora-backups/snapshot-001" --offline
ergora state verify-backup "$HOME/ergora-backups/snapshot-001"
```

备份目录必须是数据 home 以外的新目录。工具保存数据库一致快照、普通文件、文件模式和空目录，核对 Skill / 来源快照的领域身份，并返回清单 SHA。它不会先升级旧库；没有数据的 `state info` 也不会创建数据库。`--offline` 表示你已停止写入，工具不替你停止服务或外部作业。

恢复前先把现有 home 移到其他位置保留，再执行 `ergora state restore BACKUP_DIRECTORY --offline`；自定义 home 使用全局 `ergora --home ORIGINAL_HOME state restore ...`。首版要求同平台、原 home，目标必须不存在；验证、复制及再次核对成功后才发布目录，不覆盖已有目标。它保留 JSON 中的绝对路径与证据摘要。业务仓库和外部服务另行恢复并对账，ReMe 可用 `ergora memory sync PROJECT --rebuild` 重建检索投影。

## 安装与认证 Agent CLI

控制面安装器不安装模型 CLI。默认角色调用 PATH 中的 `codex`；选择 Claude Code 时调用 `claude`。Linux 可先保存官方安装器，再执行：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://chatgpt.com/codex/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/codex.sh"
sh "$HOME/.local/share/ergora-tools/installers/codex.sh"
export PATH="$HOME/.local/bin:$PATH"
codex --version
codex
```

在 `codex` 首次交互中选择账号或 API 认证，详见 [OpenAI 官方安装说明](https://learn.chatgpt.com/docs/codex/cli) 与 [认证说明](https://learn.chatgpt.com/docs/auth)。独立角色调用沿用 Codex 自己的配置；正式参考执行器的模型配置另按下文参考手册处理。

Claude Code 为可选工具，按 [官方安装说明](https://code.claude.com/docs/en/setup) 安装：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://claude.ai/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
bash "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
export PATH="$HOME/.local/bin:$PATH"
claude --version
claude
```

在首次交互中完成 [Claude 认证](https://code.claude.com/docs/en/authentication)。上述独立安装器不要求 Node.js；使用 npm 等其他安装方式时以官方依赖要求为准。确认命令在启动 Ergora 的同一 shell 中可用后，再执行 `ergora tools doctor PROJECT` 并运行一个明确的小任务。安装/版本检查不等于认证或模型任务验收；mini-swe-agent 与 ForgeKernel 的固定源码安装、模型和设备要求见 [Agent 手册](AGENT_BACKENDS.md)。

## 首个项目与工具选择

页面右上角“新建项目”注册已有 Git 仓库，不要求 GitHub / GitLab。工具绑定页分别选择：

|层|可选实现|实际消费者|
|---|---|---|
|盘点 / 规划 / 实现 / 审查及训练提案角色|Codex、Claude Code、自定义协议；实现也可 mini-swe-agent|独立调用与可选六阶段桥接|
|原生 Kernel 生成|手动、ForgeKernel|本地原生 campaign；独立可信复验另行进行|
|记忆|SQLite、ReMe HTTP|保存、修订、检索、同步|
|Skill 优化|手动导入、GEPA + JSON 提案器|有界候选搜索与证据记录|
|资料来源|明确 URL|有界观察、快照和审阅|
|研究调度|手动、Temporal Schedule|CLI worker / Schedule|

认证使用工具自己的登录或环境变量。配置只保存凭据变量名，不在网页填写密钥。Codex 和 Claude Code 分别选择模型；默认实现与审查均为 Codex。自定义命令接收 stdin 提示，以 argv 启动，不经 shell 拼接。已安装、已连通、已认证和已通过任务验收是不同状态。

### 诊断与修复

`ergora tools doctor PROJECT` 按有效绑定显示安装、版本、认证、连接、任务前置条件和修复指引，附项目修订及配置摘要。默认只做本地安装检查，不连接外部服务，也不调用模型。`ergora tools doctor PROJECT --probe --timeout 5` 主动检查原生 CLI 版本、Codex 凭据状态及 ReMe/Temporal 的 TCP 可达性；`--timeout` 为全部主动探测共用的 1–30 秒预算，本地安装检查及进程清理另计。工具绑定页也有同一主动探测入口，API 为 `POST /api/projects/PROJECT/doctor`，正文 `{"timeout":5}`，沿用本地写请求头 `X-Ergora-Request: 1`。

`credentials_present` 只表示 CLI/环境有凭据，不证明账号、额度或模型可用；`tcp_reachable` 只证明传输可达，不证明服务协议、授权、命名空间或 worker 就绪。`not_checked`、`not_confirmed`、超时和预算耗尽均不能当作通过。自定义命令不会被 doctor 执行，Claude/mini/GEPA/Forge 的认证及真实任务仍需按修复指引显式验收；Forge 版本必须符合固定提交。`task_availability: available` 仅表示 SQLite/手动操作等本地前置条件可用，不是正式六阶段验收。原始探测输出不返回、不持久保留，只返回版本号或状态。

等价 CLI：

```bash
ergora project add my-project --repo "$HOME/projects/my-project"
ergora project show my-project
ergora project config my-project
ergora tools list
ergora tools doctor my-project
# JSON 示例：{"tool":"codex","model":"YOUR_MODEL_ID"}
ergora project bind my-project reviewer --binding reviewer.json --revision CURRENT_REVISION
ergora agent run my-project reviewer --prompt review-request.md --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

页面和 CLI 共用持久业务状态；修订冲突时刷新后再保存。Agent 调用的 `succeeded` 不是正式任务验收或审查通过。默认参考执行器保持原配置；需要角色选择作用于正式任务时显式启用桥接，见 [Agent 选择与正式执行手册](AGENT_BACKENDS.md)。

## 有效绑定与运行快照

`ergora project config PROJECT_ID` 与 `GET /api/projects/PROJECT_ID/configuration` 返回同一份只读结果。`project show`仍返回保存的原文档。轻量项目的有效视图使用`schema_version: 1`、`resolution_version: 1`和`scope: project-bindings`。统一注册项目使用`scope: registered-project`，并附`registration`中的规范化定义、摘要和发布状态；它包含模板、执行目录及检查/策略。模板输入、工具内部默认值、认证和服务连接仍由各自入口管理。统一注册、旧注册只读预览/显式导入及恢复命令见[项目定义手册](PROJECTS.md)。

`project` 包含 ID、Git 根和当前 revision；`layers` 中每层含 `binding`、`source`、`validation`。来源 `project` 指向已保存字段，`inherited` 表示旧项目缺角色时继承 `bindings.implementer`，`legacy-default` 表示缺支持层时使用固定兼容默认：memory=sqlite、research=urls，其余支持层=manual。创建新项目仍保存当时的完整推荐绑定。

`sha256` 是去掉自身字段后，对 UTF-8、排序键、紧凑分隔符、保留 Unicode 且拒绝非有限数字的 JSON 计算的 SHA-256。它标识此视图内容，不能替代正式任务、产物或可信检查的证据摘要。视图校验不调用工具；无效继承显示具体层错误，需显式保存兼容绑定；认证与可用性另看 doctor。

独立Agent调用在启动工具前将该视图保存到运行记录的`configuration`，并沿用原`binding/project_revision`；新正式任务在首次接入可选执行器时把它加入`agent-bindings.json`。之后修改项目或推荐默认不会更新在途任务。旧任务没有此附加字段时继续读取原绑定快照，不补造历史来源；旧运行记录也不回写。Skill/记忆实际上下文仍单独保存在调用记录，当前快照不声明冻结所有外部工具内部行为。

## 页面操作

1. **项目总览**展示真实记忆、Skill、资料提案和工具调用。可单次启动所选角色，并附带活动 Skill、项目记忆检索及可选模板产物要求。记录中可预览标准 / 诊断输出，每路最多 64 KiB；完整文件保留在持久运行归档。固定六阶段图是协议说明，不是伪造的任务状态。
2. **长期记忆**保存正文、来源 URI 和来源版本。更正创建新修订；历史可恢复为新修订。删除会清空该记忆全部历史正文及来源；需要同步 ReMe 的删除时另行执行同步并核对结果。检索使用当前绑定的后端。
3. **Skill 演进**导入完整标准目录，首个版本建立初始基线。后续导入成为候选。先比较文件 / 文本差异，注册可信评价集，再运行双方评价和比较。达到门禁后填写采用理由；曾经活动的版本可填写理由回退。GEPA 只搜索候选，不自动采用。
4. **资料观察**填写 URL、总字节及时间预算。内容变化产生待核对提案；显示的正文仅是文本。审阅不自动写入记忆或修改 Skill。执行时可以刷新列表并请求取消，随后确认实际终态。异常退出的未决传输可能保守耗尽预算，需要明确创建新的观察任务。
5. **工作流设计**提供治理和大型开发的工作单元 DAG，编辑依赖、路径和说明，或载入完整 JSON。服务端调用原合同编译器拒绝环、冲突和非法范围。保存是持久草稿；下载 `input.json` 后继续走参考任务冻结和执行。训练模板提供 workload / experiment 等文件预览和下载，完整目录可从 CLI 复制。

详细 evaluator / proposer JSON 协议、来源快照、ReMe 与 Temporal 配置见 [工具接入手册](INTEGRATIONS.md)。

## 三个模板与正式任务

```bash
ergora templates list
ergora templates copy repository-governance ./governance-task
ergora templates copy large-change ./development-task
ergora templates copy training-optimization ./training-task
ergora workflow --help
ergora reference verify
ergora reference info
```

复制目标必须是新目录。模板定义任务与证据要求；示例中的 PASS、SHA 和指标不构成任何真实结果。治理与大型开发沿用 `inventory → plan → work → integrate → verify → review`；计划批准和最终证据仍由完整参考运行时处理。

需要 Temporal、MLflow、Symphony、A2A、Supervisor 和完整执行器时，使用 [单文件安装发行](distribution/multi-agent-development-platform.html)，或随包参考入口提供的安装器。HTML 内嵌完整安装脚本、源码 ZIP、三个模板和两本完整参考手册。其部署基础为 Ubuntu 24.04 / Linux x86_64，安装需要联网及目标系统内的包管理权限。

- [完整部署与日常使用参考手册](../src/ergora/data/reference/platform/README.zh-CN.md)
- [完整训练优化参考手册](../src/ergora/data/reference/platform/docs/TRAINING.md)
- [新入口的训练说明](TRAINING.md)

这些冻结参考文件保持 v2.2 内容身份，便于校验；本手册和接入手册说明新的控制面能力。它们不会自动回写旧 HTML 内嵌包。 使用本地参考任务 CLI 前，还需在当前 shell 配置 Temporal 连接，见 [首个开发任务](../README.md#首个开发任务)。

## 远程访问、恢复与维护

服务只监听 loopback。远程电脑使用 SSH 转发，然后打开本机 `http://127.0.0.1:8977`：

```bash
ssh -L 8977:127.0.0.1:8977 user@server
```

本地接口要求同源与自定义请求头，并校验 Host；它使用当前用户权限，面向可信项目。团队身份、公网服务和每 Agent 的 OS 隔离需要单独接入。容器内无法使用 namespace 沙箱时，不会为让调用成功而自动取消 Agent 自身的 sandbox。

应用在前台运行；Linux / WSL2 可用 Supervisor 管理 `ergora serve` 及各项目的 `ergora research worker PROJECT`，Windows 原生先使用前台终端。安装不自动后台执行任务、调用模型或启动研究。停止写入后备份完整 `ERGORA_HOME` 以及业务 Git 仓库；恢复时核对仓库实际路径和工具登录。记忆删除不会清除独立备份及过去归档的调用输入。

开发和换机继续工作时，先读 [PLAN.md](PLAN.md)、当前活动切片的 `docs/delivery/` 记录，再检查分支、`git status` 与最近提交。测试默认不调用付费模型；外部服务和 GPU 的效果验收单独记录。
