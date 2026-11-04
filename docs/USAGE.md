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

### 正式任务的操作顺序与恢复

首次使用按[README完整旅程](../README.md#首个开发任务)和[项目定义](PROJECTS.md)准备真实Git基线、可信检查与已认证角色，然后使用下列顺序。正式开发需要所登记Linux/WSL2完整执行器；页面中的工作流草稿尚不等于已创建的正式任务。

```text
project register → 选择角色/核revision → services start所选栈
→ task preview → 审阅摘要 → task create → task start
→ inventory/plan → status固定原run → 审阅实际计划 → approve精确plan
→ work/integrate/verify/review → 原outcome
→ REVIEW_READY：审阅精确candidate/检查/review → export本地分支 → 独立复验/人工合入
→ 阻塞或取消：核原run闭合 → external-status → 明确reconcile → 按原intent恢复
```

保存task ID、创建/提交intent SHA和原workflow/run ID；所有写命令使用当前项目revision，批准另带稳定decision ID及精确plan SHA，取消带稳定request ID。HTTP 200、CLI 0或requested是对应操作回执，六阶段是否通过由原outcome和候选证据决定。页面关闭或CLI进程结束后，可用同一`--home`和登记的执行目录继续查询；不得复用task ID绕过旧记录。

|中断位置|先读|允许的下一步|
|---|---|---|
|任务合同发布|`task creation PROJECT TASK`|以原intent SHA运行resume-create；冲突文件先核对|
|提交结果不明|`task submission PROJECT TASK`|resume-start核原spec/memo/run；unknown只查询，不重新提交|
|批准或取消投递不明|`task approval PROJECT TASK DECISION` / `task cancellation PROJECT TASK REQUEST`|resume-approve/resume-cancel核原操作SHA与history；无匹配信号保持未知|
|闭合但外部未确认|`task status --run-id`及`task external-status --run-id`|保留原结果/请求/回执/产物/fence；明确reconcile，未完成则resume-reconcile|
|候选导出中断|`task export-status PROJECT TASK`|resume-export核原结果和实际ref；unknown不重fetch或复活已删分支|

备份必须联合保存控制`ERGORA_HOME`、登记的CONFIG/STATE、业务Git仓库、Temporal持久数据及实际工具认证；控制SQLite备份不包含原任务/history/候选/租约。执行STATE中的`tasks/`、`ergora/task-*`、requests/receipts/artifacts/approvals/fences、workspaces、进程记录及ledger均属于恢复证据。先停止相关写者并核在途外部作业，再按[备份说明](#升级与持久数据)操作。

### 服务停止后的读取与恢复

已完成统一登记和完整执行环境安装时，服务是否运行与持久回执是否存在分别判断。完整正式执行使用Linux/WSL2；Windows控制面及可选工具的范围见[Windows手册](WINDOWS.md#选择运行方式)。

|要读取或执行的内容|需要运行的服务|事实边界|
|---|---|---|
|原合同、创建/提交/批准/取消/对账/导出记录|无需启动执行服务|读取持久文件；历史回执不证明当前Git分支、外部进程或实时运行状态|
|已闭合原run状态/结果，原事件及job回执/文本材料|Temporal；无需启动worker/executor|固定原run及证据摘要；事件/job读取也适用于运行中原run，材料还要求原可信产物目录可读|
|运行中原run的阶段/状态查询|Temporal及可响应workflow query的worker|`task status`在RUNNING时调用workflow query；只有Temporal在线可能查询失败|
|继续正式阶段及真实Agent调用|Temporal、对应worker/executor及所选工具认证|投递回执与实际完成分别核查；启动服务不会自动补发未知操作|
|显式服务启动/退出和日志|Linux/WSL2完整参考安装及Supervisor|由统一入口管理本执行目录所属栈；共享目录的项目共享服务|

关闭浏览器或重启HTTP后，重新选择原项目/任务并读取原记录即可恢复；清空会话选择也不会删除后端意图。run输入可从持久submission回填，批准/取消仍需保留原decision/request ID。原运行服务不可达时页面明确显示查询失败，本地回执仍可独立读取。不要把连接失败当作未提交，不换task ID重跑。检查已有闭合运行只需显式启动Temporal；恢复执行前另核所需worker、executor、工具与原意图状态，步骤见[显式服务管理](#显式服务管理)。

### 旧参考 CLI 与统一入口

统一`ergora task`从所登记参考环境读取Temporal配置，旧`agentflow task`从当前shell读取连接。本机loopback开发服务的旧命令可显式设置：

```bash
export TEMPORAL_ADDRESS=127.0.0.1:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_LOCAL_DEV=1
```

LOCAL_DEV仅适用于loopback开发服务，其他服务按自己的认证配置连接。两种入口的任务归属不同；旧任务保持原配置/STATE和原CLI，不能通过统一命令隐式接管。Supervisor管理也是按执行state区分，停当前共享栈会影响其所有项目。

### 正式任务页面

选择已统一注册的项目后，从左侧“正式任务”或项目总览的“查看正式任务”进入。列表按有界游标分页，本页没有匹配项仍可能有下一页；无法读取的记录和无效合同会单独显示。详情展示任务自己的冻结输入、角色快照、工作单元和本地提交回执，不从当前项目绑定补写历史，也不把合同存在或submitted当作执行通过。

“原生运行”默认使用已保存选择或提交回执中的原run ID，点击“读取原运行”后才连接所登记Temporal。结果保留REVIEW_READY、BLOCKED、CANCEL_UNCONFIRMED、NEEDS_RECONCILIATION等原事实；not_found和查询失败分别显示。切换任务/项目、修改run ID或离开页面后，旧响应不会覆盖当前选择。刷新或在同一浏览器标签页返回控制台时保留项目、页面、任务和run选择，执行状态重新查询。关闭标签页后的保留取决于浏览器自身的会话恢复。

点击“预览与创建”，选择项目已登记的开发模板，载入模板输入或兼容的已保存草稿。填写新任务ID、工单编号或本地标识，并编辑完整输入JSON；可指定起始提交，留空使用登记基线。服务端预览展示修订、冻结角色、完整文件与摘要；修改字段或来源后旧确认立即失效。审阅后点击“确认创建冻结合同”，只发布合同，不自动提交运行。训练优化仍使用独立入口。

创建请求发出前，浏览器会把原任务ID保存为本项目的任务选择。回复失败或丢失时表单锁定，先“按原ID读取创建记录”；也可随时从页面顶部按ID查询。重载后合同尚未完整发布时，详情错误中仍保留原ID和查询入口。`pending`展示原意图摘要与冻结修订，明确确认恢复时沿原内容发布；项目后续绑定变化不替换旧角色。`published`显示冻结合同已发布，`not_recorded`不接管旧任务，`conflict`保留冲突文件且不提供覆盖按钮。页面不自动重发创建、换ID或启动执行。

任务详情的“检查提交与恢复”会重新读取创建与本地提交记录。完整发布且无提交记录时，可审阅冻结合同、角色、当前修订和摘要后“确认提交此冻结任务”；`prepared`或`unknown`只提供原意图的明确恢复，后端决定继续尚未派发的提交，或查询已经不确定的派发。`not_found`仍是未知，页面不重发start；归属`rejected`不提供覆盖入口。回复失败时先重新读取原记录，不能据此更换ID。`submitted`保存原run选择，点击“查看原任务与运行”后再单独读取运行状态；提交回执不代表六阶段完成。

原run查询到`AWAITING_PLAN_APPROVAL`时，点击“审阅计划与批准”读取完整execution-plan、ownership-map及rollback-plan和精确回执身份。材料读取失败时没有批准入口。审阅后填写稳定的“决策 ID（用于恢复）”（例如`owner-one`），先“读取批准记录”；仅该ID尚无记录时提供“确认批准此计划”。确认固定本次材料的run/plan SHA，并在服务端再次校验当前状态。保留此ID，不用新ID绕过未知投递。

任务详情另有“按原 ID 检查批准记录”，不要求当前仍在等待计划。浏览器会按项目/任务保留最近的decision选择；选择已清空或换设备时，手工输入原ID仍可取回后端记录。`prepared`可“确认恢复原批准意图”，`unknown`只“确认核对原批准信号”，`requested`仅展示投递事实且不再提供投递按钮。若当前材料工作区查到既有decision，需单独查看原记录，不以当前材料覆盖旧决策。回复失败时先重新读取原记录；重载不会自动批准。实际采用和执行进度需返回原任务再次“读取原运行”。

原run仍运行时，可点击“请求取消此运行”，填写稳定的“取消请求 ID（用于恢复）”并先“读取取消记录”；仅该ID未记录时提供原因输入和“确认请求取消此运行”。服务端固定原run并再次核对状态。任务详情另有“按原 ID 检查取消记录”：`prepared`明确恢复原取消意图，`unknown`只核对原信号，`requested`/`already_closed`不提供再次投递。原原因与意图不可被当前编辑覆盖；`already_closed`表示发送前原run已闭合、没有新信号。

保留原取消请求ID；回复丢失后先读原记录，浏览器选择清空后可手工输入原ID恢复查询。取消是协作请求，`requested`不是停止确认。返回原任务再次“读取原运行”核阶段和终态；外部作业清理与租约释放另行对账。

原run已闭合时，可点击“外部证据与对账”，只读查看该原run的job、请求/回执/产物校验结果、fence和原结果；读取不会改变执行屏障或租约。即使某些作业已有终态，也须检查`external_confirmed`，不能从workflow闭合或取消投递推断清理完成。

同一工作区读取原对账记录；仅在本轮外部证据读取成功、记录为`not_recorded`时提供“确认外部对账并释放原租约”。操作会重验原run，建立或复用同一fence，在外部作业全部确认后释放原claim。任务详情另有“检查原对账记录与恢复”，只读取本地持久记录；`prepared/unknown/confirmed`可“确认恢复原对账意图”，固定原intent SHA，不使用当前编辑的run替换。`confirmed`尚未保存租约释放回执，只有`reconciled`表示原租约释放及回执已保存；后者不再提供写操作。

回复丢失后重载或重新选择原任务，再读原对账记录；无须创建新的对账ID。实时外部证据与历史对账回执分别读取。原`CANCEL_UNCONFIRMED`结果保持，清理完成不表示开发成功。外部读取失败时不能发起新对账，已保存的原意图仍可单独查看和明确恢复。

原run闭合且结果为`REVIEW_READY`时，可点击“导出精确候选”。页面固定本次原run/完整candidate SHA，先读取原导出记录；仅`not_recorded`提供目标本地分支输入和“确认导出此候选至本地分支”。分支是否合法及原候选能否导出由服务端Git/原结果检查，页面不替换已有分支，也不checkout、merge或推送。

任务详情另有“检查原导出记录与恢复”，只读取本地记录，不查询Temporal或当前Git ref。`prepared`可“确认恢复原导出意图”，可能首次创建已保存目标；`unknown`可“确认核对原导出分支”，仅核对原分支，`branch_not_found`保持未知，不重新创建。恢复固定原intent SHA，repo/run/candidate/branch均不可更换。`exported`只展示历史回执和原租约释放事实，不证明当前ref仍正确，也不表示开发成功或已合并。回复丢失后重新选择原任务读取同一记录，无须重发导出；维护者在采用前仍需复验实际分支及证据。

未统一注册时显示登记指引；服务不可用时仍可查看本地合同。关闭弹窗或页面不会撤销已经发出的操作，关闭页面也不取消外部任务；终态不等于外部作业已确认清理。浏览器仅保存选择，创建/执行事实每次从服务端读取。

### 读取正式任务合同

先完成[统一项目注册](PROJECTS.md)，执行目录已有的开发任务可直接从主入口读取：

```bash
ergora task list my-project --limit 50
ergora task show my-project TASK_ID
```

同源API为 `GET /api/projects/ID/tasks?limit=50&after=CURSOR` 和 `GET /api/projects/ID/tasks/TASK_ID`。默认每页校验50个候选目录项，可设1–100；原样使用返回的不透明ASCII游标 `next_after` 继续，直到其为null；游标不是任务ID或文件路径。每页流式枚举全部目录名再选取候选窗口，因此枚举时间随任务数增加；`inspected_entries`只计该页校验项数。其他项目或损坏目录可能产生空页，仍应沿游标前进。`items`只包含匹配该项目/Git根/tracker并通过合同结构与摘要校验的任务；归属已确认但合同损坏的条目进入 `errors`，不能判断归属的条目只计入 `unreadable_count`。

详情返回原始spec、冻结项目、可选的 `agent_bindings` 及其文件SHA256。`project_revision`是当前控制项目修订，冻结绑定中的 `project_revision`属于创建或首次执行时的快照。`runtime_status: not_queried`表示没有访问Temporal；本地文件存在不代表任务开始、完成或验收通过。合同查询不安装SDK、启动服务、提交任务或写回旧记录；统一创建/提交的任务使用下文的明确批准、取消与导出入口，旧入口任务继续按[正式执行手册](AGENT_BACKENDS.md)管理。Linux/Windows均可读取本机可访问的执行目录，完整六阶段执行需要Linux/WSL2。

### 预览与创建正式任务

统一注册项目可在无Temporal/Web SDK的基础安装中编译和保存两个开发模板。先保存 `task-definition.json`；`input` 使用模板的原始输入格式，具体字段和DAG仍由原编译器校验：

```json
{
  "schema_version": 1,
  "task_id": "example-change",
  "task_type": "repository-governance",
  "issue_id": "1",
  "input": {
    "goal": "检查并整理 src 内的模块边界",
    "allowed_paths": ["src"],
    "acceptance": ["保持已有行为和可信检查"],
    "constraints": [],
    "risk": "standard",
    "work_units": [{"id": "inspect", "depends_on": [], "paths": ["src"], "instructions": "完成边界整理"}]
  }
}
```

模板可选 `repository-governance` 或 `large-change`，必须已在项目登记；大型开发按原模板设置其风险与输入。可选 `starting_sha` 是40位小写Git提交SHA，默认使用登记的基线。将以下修订替换为 `project show` 的当前值：

```bash
ergora task preview my-project --definition task-definition.json --revision 1
# 审阅返回的 files 中完整 spec、可信策略、冻结项目及 agent-bindings。
# 用本次输出的 preview_sha256 替换 PREVIEW_SHA：
ergora task create my-project --definition task-definition.json --revision 1 --preview-sha256 PREVIEW_SHA
ergora task creation my-project example-change
# 发生中断时，用 creation 中的 intent_sha256 和当前项目修订恢复：
ergora task resume-create my-project example-change --revision 1 --intent-sha256 INTENT_SHA
```

preview只在自动清理的临时目录调用原编译器，不写真实任务目录。摘要绑定控制目录、项目修订、登记身份、全部编译合同和角色快照；定义或绑定变化后必须重新审阅预览。create在任何原生任务文件发布前先保存完整意图，然后不可变发布七份合同，最后保存结果回执；相同请求可以幂等重试。任务ID在同一执行状态目录全局唯一，没有本工具意图的旧任务不能通过create或resume-create接管。

`creation.status` 为 `not_recorded / pending / published / conflict`，只描述本地文件发布。`runtime_status: not_queried` 和 `execution_started_by_operation: false` 表示本次操作未查询或启动工作流，不能据此推断该任务的实际运行状态。合同逐文件最多1MiB；意图上限16MiB。比较使用原生规范JSON内容摘要，保留等价既有文件的字节。意图及回执位于登记的执行状态目录 `ergora/task-creations/TASK_ID.intent.json` 与 `.result.json`，必须连同原任务目录保留；Ergora控制库的单独备份不包含执行状态目录。

发生中断先查creation，再以明确的原意图摘要恢复；恢复不重新编译，项目绑定改变后仍保留原角色快照。冲突文件保留并报错，不自动覆盖或重建历史。项目配置投影或执行目录发生漂移需要先修复原登记；切换执行目录不会自动迁移旧任务。写操作串行保留项目修订并非阻塞取得同ID文件锁，任务正忙时明确返回busy；单次原生进程预算30秒；超时后先查询原意图，不自动重试。

对应API为 `POST /api/projects/ID/tasks/preview`（`definition/revision`）、`POST /api/projects/ID/tasks`（加`preview_sha256`）、`GET .../tasks/TASK_ID/creation`、`POST .../tasks/TASK_ID/resume-create`（`revision/intent_sha256`）；写请求沿用本地同源限制及 `X-Ergora-Request: 1`。预览与创建支持Linux/Windows本地文件合同；完整六阶段执行仍使用Linux/WSL2和[正式执行手册](AGENT_BACKENDS.md)。

### 查询正式任务运行状态

安装development组合或 `ergora[temporal]`，并准备所登记的参考运行时。通过CLI或 `GET /api/projects/ID/tasks/TASK_ID/status?run_id=RUN_ID&timeout=20` 只读查询原生运行事实：

```bash
ergora task status my-project TASK_ID --timeout 20
# 后续查询固定前次返回的原生run_id：
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

该操作先验证本地任务的项目归属和spec，再由所登记安装中的原DevelopmentTransport核对Temporal的原始启动输入。`runtime_status: queried`附原生workflow/run ID、phase及status或outcome；未提供run ID时先解析当前workflow并返回其确定的run ID，后续可固定这个ID。只有原生NOT_FOUND返回 `runtime_status: not_found`，不附伪造phase；连接、认证、超时、原始输入碰撞等均报错，不能当作未启动。查询不提交、批准、取消或释放工单租约，不写入任务状态。

`terminal: true`只表示Temporal运行已闭合；outcome仍可能是CANCEL_UNCONFIRMED，或phase为NEEDS_RECONCILIATION，均须沿原ID对账。该入口使用登记的参考环境连接规则（目前是本机127.0.0.1:7233/default），项目scheduler绑定的地址/队列只用于资料研究调度。1–60秒timeout约束网络查询；子进程另留5秒启动/回收预算，本地合同预检和安装身份检查另计。SDK缺失会明确提示，不自动安装或从本地COMPILED/服务RUNNING推断运行状态。完整六阶段执行仍使用Linux/WSL2。

### 分段读取原运行事件

对统一创建且已保存原提交回执的任务，固定该回执的run ID，读取事件元数据：

```bash
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --timeout 20
# 仅在需要继续时，将上次返回的next_after原样传入：
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --after CURSOR --timeout 20
```

同源只读API为`GET /api/projects/ID/tasks/TASK_ID/events?run_id=RUN_ID&limit=20&after=CURSOR&timeout=20`，首次省略after。该入口使用上述Linux/WSL2参考运行时和原提交/spec/memo验证，不跟随其他run。返回事件ID、类型、时间和适用的activity/scheduled_event/signal关联字段，不返回原始输入、prompt、result或payload；事件投影不解码payload，原身份验证仍需解码启动spec。`read_only: true`、`execution_success: null`明确这只是事实片段。没有原生run时返回`runtime_status: not_found`；连接、超时、错误归属或游标错误明确失败，不自动重试或重发任务。

原验证完成后每次读取一个事件SDK物理页、返回最多limit条（1–100，默认20），不是保证每次填满limit；整个请求另有原运行describe及启动前缀读取，不等于一次RPC。Temporal的物理页大小是建议值，可能超出请求条数；游标保留该页未读位置，下一次先继续剩余内容。`next_after`是绑定原提交/run的只读导航信息，不是授权或完整history证明，不能跨run使用。显示limit可以调整；SDK页大小保持原游标的值。总JSON响应最多1 MiB；SDK接收物理页的网络内存不受此响应上限约束。timeout为1–60秒墙钟预算，父进程另留5秒启动/回收，预检另计。

`has_more`表示已知还有未读内容，`at_current_end`只表示读至本次可见尾部。RUNNING即使暂时无新事件仍保留next_after，稍后由用户显式读取；终态读至尾部才返回null。事件片段不证明六阶段完成、候选通过或外部进程已停；继续通过原status/outcome和外部对账核实这些事实。

网页在正式任务中先“读取原运行”，再点击“读取原运行事件”。打开时读取第一批，之后每次点击最多读取20条，不自动轮询或重试。页面显示累计读取数及最近200条；关联字段超过256个Unicode字符时显示省略号，完整元数据可沿CLI/API读取。运行中到达当前尾部仍可手动“读取新增事件”；终态读完后按钮停用。读取失败保留本次已读片段和原位置，明确点击重试才继续。关闭重开后从第一批读取；切换项目、任务或run后旧回复失效。显示记录只是本次观察，不作为持久证据或完整历史证明。

### 读取原job回执与文本证据

从上述原事件中选择Activity类型为`dev_submit`的`ACTIVITY_TASK_SCHEDULED`事件ID（不是activity ID或completed事件ID），先读取job目录。以下42只是示例，请使用实际ID：

```bash
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --timeout 20
# 从返回receipt.artifacts选择名称，保留本次receipt_sha256；不要传本地路径
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --artifact model-log --receipt-sha256 RECEIPT_SHA --offset 0 --limit 8192 --timeout 20
```

API为`GET /api/projects/ID/tasks/TASK_ID/jobs/42?run_id=RUN_ID&timeout=20`；文本窗口再带`artifact=model-log&receipt_sha256=RECEIPT_SHA&offset=0&limit=8192`。沿返回`artifact.next_offset`手动继续，null表示该文本的末尾。offset/limit以Unicode字符计数，不是UTF-8字节；每窗默认8192、最多16384字符，保留原全文的SHA、字节数及字符数。回执变化或产物字节变化时明确失败，不能拼接成同一份日志。产物名称只从所选原job回执匹配，不解析用户传入的路径。

该读取仍固定统一任务原提交/run/spec/memo，按连续history前缀核到所选调度事件，只解码该事件的原context，再核原请求envelope与可信目录发布的回执。支持事件ID1–10000；更后的事件明确拒绝，不能据此判断没有job。RUNNING和闭合原run均可读；`runtime_status: not_found`表示当前原history未知，`receipt_status: missing`表示尚无可验证的已发布回执。没有回执时不提供日志，也不将请求目录存在当作执行完成。

`receipt_status: published`只表示原job的当前发布回执通过本机可信文件适配器核对，`workflow_receipt_accepted: null`与`execution_success: null`保留未知。即使回执state为SUCCEEDED，也要通过原运行status/outcome、候选检查与外部对账核实际采用、开发结果及清理事实。此功能不改原意图、回执、claim或Git引用，不提交、重发或自动重试。

沿原生适配器每份产物最多16 MiB；先核完整摘要，再严格解码所选UTF-8全文、拒绝NUL，之后返回窗口。缺失、损坏、非UTF-8、NUL、超限或不安全路径均明确失败。每次核回执会重读其全部产物摘要，所选文本还需完整读取/解码；窗口和1 MiB JSON响应上限不代表SDK物理页或总文件读取/内存的上限，没有隐藏缓存。timeout为1–60秒；协程内网络受20秒RPC及请求预算约束，同步文件读取由父进程timeout+5秒最终回收。本入口使用现有Linux/WSL2参考运行时；基础Web本身不需Temporal SDK，原生查询需要所登记完整执行环境及其SDK。环境不完整时按工具诊断页配置，不自动安装或启动服务。

网页中先读取原运行及其事件，在Activity为`dev_submit`的调度行点击“原job证据”。弹窗读取该原run/事件的job目录，展示原回执、候选及摘要；缺失或失败时可手动重新读取。选择回执中的材料不会发起文本请求，点击“读取所选材料第一段”后才读取8192字符窗口，再手动读取下一段。每次固定首次回执SHA，页面只保留当前窗口及完整产物摘要。材料错误或原运行未知时保留已读窗口和原偏移，可“重试原位置”；回执变化时关闭并重新核目录，不能拼接旧窗口。切换材料清空窗口并归零，末尾停止；关闭重开不恢复文本、不后台轮询。编辑run、切任务/项目、替换弹窗或离开页面后，先前请求的迟到回复失效。

### 提交正式任务与恢复未知结果

在Linux/WSL2安装完整参考运行时并初始化所登记的配置，使用该运行时的`.venv/bin/python`执行准入。控制面无需安装全部执行依赖；实际提交仍须通过原doctor、可信检查和工单租约，所选服务及模型须就绪。此入口仅接受通过统一入口完整创建的任务，保留其原spec和角色快照。

```bash
# CREATION_SHA取自task creation的intent_sha256；修订取自project show。
ergora task start my-project TASK_ID --revision 1 --creation-sha256 CREATION_SHA --timeout 20
ergora task submission my-project TASK_ID
# 中断后先读submission，再用其原intent_sha256和当前项目修订显式恢复：
ergora task resume-start my-project TASK_ID --revision 1 --intent-sha256 SUBMISSION_SHA --timeout 20
```

`submission`仅检查本地提交记录，不连接Temporal。`status: submitted`表示保存了原workflow/run ID回执，`execution_success: null`不代表六阶段成功；运行进度用`task status --run-id RUN_ID`查询。重复start只返回原本地记录，不重发提交。`not_recorded`表示没有提交意图，`prepared`表示已有意图但尚无派发检查点，`unknown`表示检查点已保存而原调用结果未知，`rejected`表示发现不属于本次提交的既有run并保留了拒绝记录。变更命令仅在submitted时返回CLI成功。

先保存不可变意图，再走原准入/claim；实际start之前保存attempt，最后保存原生回执。prepared可通过明确resume重走准入、复用同一租约；unknown只能沿原workflow ID查询原始输入并补回执，即使NOT_FOUND也不能重发。检查点写入后、实际RPC前崩溃也保留unknown，需人工对账。发现既有run时拒绝接管，后续历史消失也不会自动重新开始。原start在Temporal memo中关联本次提交意图摘要，未知恢复还会核对该标记；没有或不同的标记不能被采用为本次提交。提交竞争返回AlreadyStarted会持久拒绝，不采用其他入口的run。原始输入按规范JSON摘要精确比较，true/1/1.0不混淆。原始输入不一致、RPC失败、合同/登记漂移均明确报错，不换任务ID绕过未知状态，不释放租约。已保存回执的重复操作继续返回原run ID。

意图、派发检查点、回执及适用的所有权拒绝记录位于执行状态目录`ergora/task-submissions/TASK_ID.{intent,attempt,result,rejection}.json`，必须与创建记录、任务目录和原运行状态一起保留。准备阶段在当前项目修订保留下非阻塞取得原同ID锁，仅保存意图；随后释放控制库写锁，网络阶段只持原任务锁。1–60秒timeout分别约束准备和网络阶段，父进程各另留5秒启动/回收，预检另计。超时只回收提交客户端，实际Agent由持久执行器拥有，不能据此判断已停机。完整环境缺失时明确报错；不自动启动服务或修改执行权限。

API：`POST .../tasks/TASK_ID/start`正文为`revision/creation_sha256/timeout`，`GET .../tasks/TASK_ID/submission`，`POST .../tasks/TASK_ID/resume-start`正文为`revision/intent_sha256/timeout`；写请求沿用同源保护及`X-Ergora-Request: 1`。同任务并发准备或创建/恢复创建遇活跃任务锁时及时报busy；并发读取也可能取得prepared/unknown快照；无需等待另一请求完成才返回。操作结束后读取submission及当前项目修订，再决定是否明确resume；重复start不隐式重试未派发准入，unknown不重发。其他项目不会因本次网络等待而被持续占用控制库写锁。HTTP成功响应仍须检查status，unknown/rejected不能当作提交成功。

### 读取待批计划材料

仅适用于统一创建且已保存原提交回执的任务，运行环境与提交入口相同。先用`task status --run-id RUN_ID`查询原状态，取得`AWAITING_PLAN_APPROVAL`的实际plan SHA，再读取对应材料：

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 PLAN_SHA --timeout 20
```

`plan`核对原提交run/spec/memo、当前待批phase与所选plan SHA，从原history定位plan job并核对请求envelope和已接受receipt。plan SHA是整个回执的规范JSON摘要，不是execution-plan文件摘要。`materials`按冻结profile返回完整UTF-8文本及各自的`name/sha256/bytes`；两个开发模板均提供execution-plan、ownership-map和rollback-plan。响应同时保留原run、请求、profile、回执及history事件身份，供审阅工作单元、范围、风险与回退措施。

每份材料最多256 KiB，总JSON响应最多1 MiB；缺材料、摘要不符、非UTF-8、路径不安全或超限时拒绝读取，不截断成貌似完整的计划。`--timeout`为1–60秒，父进程另留5秒启动/回收，本地预检另计。此操作不持控制库写锁、不创建decision或owner回执、不发信号。返回值是读取时快照；批准前仍由服务端再次核对原运行当前状态。

API：GET `.../tasks/TASK_ID/plan?run_id=RUN_ID&plan_sha256=PLAN_SHA&timeout=20`。网页“审阅计划与批准”使用同一入口。网络失败或计划已不再待批时，沿原ID重新查询status，不创建替代任务。

### 批准精确计划与恢复投递

先按上节读取并审阅完整材料，再用当前项目修订、原run ID及该plan SHA明确批准：

```bash
ergora task approve my-project TASK_ID --decision-id owner-one --revision 1 --run-id RUN_ID --plan-sha256 PLAN_SHA --confirm --timeout 20
ergora task approval my-project TASK_ID owner-one
# 中断后先读approval，再用原intent_sha256和当前项目修订恢复：
ergora task resume-approve my-project TASK_ID owner-one --revision 1 --intent-sha256 APPROVAL_SHA --confirm --timeout 20
```

decision ID是本次owner决策的稳定标识。重复同ID只读取原记录，不重发、不修改plan或延长24小时有效期。计划更新、原决策过期或撤销后，应审阅当前计划并使用新decision ID明确作出新决策。原角色快照不随项目绑定变化；此本地入口使用当前Linux用户作为owner actor，不提供团队身份认证。

`approval`只读本地记录，不连接Temporal。状态为`not_recorded / prepared / unknown / requested`：prepared尚无信号检查点，可明确恢复；unknown已保存attempt，恢复只能在原run的分页history中核对精确request/plan/receipt，不重发。未找到信号或原run不可用时保留未知，应继续沿原ID对账。owner回执被撤销或更改时原意图不再可派发。

`requested`只说明SDK已应答信号，或原history有对应事件；`approval_accepted: null`、`execution_success: null`不是批准采用或六阶段成功。工作流仍按原授权规则检查owner/expiry/revocation/精确计划，用`task status --run-id RUN_ID`核对实际进度。CLI变更仅在requested时返回0；HTTP成功响应也须检查status。

审批操作记录位于执行状态目录`ergora/task-approvals/TASK_ID/DECISION_ID.{intent,attempt,result}.json`，原owner回执在`approvals/owner-UUID.json`；必须与原任务、创建和提交记录一起保留。准备意图时保留项目revision且非阻塞获取原任务锁；网络阶段已释放控制库写锁，只持同任务锁。准备和网络各有1–60秒预算，父进程各另留5秒，本地预检另计；超时后先读记录再决定恢复。

API：GET/POST `.../tasks/TASK_ID/approvals/DECISION_ID`，POST正文为`revision/run_id/plan_sha256/confirm/timeout`；POST同路径`/resume`正文为`revision/intent_sha256/confirm/timeout`。`confirm`必须为true；写请求沿用同源保护及`X-Ergora-Request: 1`。旧参考入口创建/启动的任务继续由原CLI管理，本入口不会采用旧运行。

### 请求取消与恢复未知投递

统一创建且已保存原提交回执的任务，可固定原run请求协作取消。与批准入口相同，使用当前项目修订、稳定请求ID和明确确认；原因非空且最多1000字符：

```bash
ergora task cancel my-project TASK_ID --request-id stop-one --revision 1 --run-id RUN_ID --reason 'Owner requested stop' --confirm --timeout 20
ergora task cancellation my-project TASK_ID stop-one
# 中断后先读cancellation，用其原intent_sha256恢复同一请求：
ergora task resume-cancel my-project TASK_ID stop-one --revision 1 --intent-sha256 CANCELLATION_SHA --confirm --timeout 20
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

`cancellation`只检查本地记录，不连接Temporal。`prepared`尚无派发检查点，明确恢复可继续原cancel；`unknown`已有检查点但投递未确认，只能沿原run history核对包含本次操作SHA的完整signal，不能凭相同原因认领其他请求，也不会重发。重复同ID保留原原因/actor，不生成第二个请求；不要用换ID来绕过未知，先核原运行和外部作业事实。

`requested`和`cancel_requested: true`仅表示signal已应答或原history有对应事件。`already_closed`表示原run在本次检查时已闭合，`cancel_requested: false`、`signal_delivery: not_sent`明确本次没有新信号；重复读取是已保存事实，不是新的实时查询。两种状态的CLI变更返回0，仍须核对状态字段。`cancellation_confirmed: null`和`execution_success: null`不表示已停机；用`task status --run-id`核对原phase/outcome。CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION要继续按原fence和外部作业对账，不能删ledger、terminate或自动释放未确认租约。

意图/attempt/result位于执行状态目录`ergora/task-cancellations/TASK_ID/REQUEST_ID.*.json`，须与原任务、创建及提交记录保留。准备阶段在当前revision下非阻塞获取原任务锁，远程阶段已释放控制库写锁；每阶段1–60秒预算，父进程各另留5秒，本地预检另计。Windows使用已登记Linux/WSL2完整运行时；该本地入口不是团队权限系统。

API为GET/POST `.../tasks/TASK_ID/cancellations/REQUEST_ID`，POST正文`revision/run_id/reason/confirm/timeout`；POST同路径`/resume`使用`revision/intent_sha256/confirm/timeout`。严格确认必须为true，写请求沿用同源保护及`X-Ergora-Request: 1`。旧入口任务仍由原CLI管理。

### 核对闭合运行的外部作业证据

统一创建并保存原提交回执的任务，可用固定的原run读取完整历史、原作业请求、可信终态回执和已有fence：

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
```

API：`GET /api/projects/PROJECT_ID/tasks/TASK_ID/external-status?run_id=RUN_ID&timeout=20`。原run必须已闭合，且仍是该workflow ID的最新run；不支持continued-as-new或其他后续run。使用登记Linux/WSL2完整运行时，预算1–60秒，父进程另留5秒，本地合同预检另计。

`original_outcome`保留原工作流结果；失败、取消、终止或超时的Temporal run没有结果时为null。`jobs`逐项列出原历史job、请求与回执状态及摘要；`unresolved_jobs`包含缺少请求、缺少或损坏回执以及额外请求/孤立回执。错误根、冲突请求、错误fence或不完整历史会明确拒绝。只支持登记执行状态目录下的requests/receipts/artifacts/approvals/fences布局。

仅在完整历史对应的全部请求和可信终态回执均匹配、没有额外作业且已有正确fence时，`external_confirmed`为true。requests和receipts两类job目录均参与检查；无法绑定原history的孤立回执不支持确认。FAILED/CANCELLED回执也是外部作业终止证据，不能据此推断开发成功。这是可信文件协议的当前快照，依赖执行器按原协议发布回执和遵守fence，不代替操作系统进程检查。缺目录不会把已知历史job变成零作业通过。

查询不保存本工具运行记录、不发布fence或释放租约，`lease_released_by_operation: false`、`execution_success: null`。CLI返回0只表示查询成功，务必检查external_confirmed和未决项。未确认时保留原任务、运行目录及租约，先沿原ID补齐证据。

### 显式终态对账与工单租约释放

原运行闭合后，使用当前项目修订和固定原run明确授权fence及外部清理核对：

```bash
ergora task reconcile my-project TASK_ID --revision 1 --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
# 中断或补齐原可信回执后，使用上条返回的原intent_sha256恢复：
ergora task resume-reconcile my-project TASK_ID --revision 1 --intent-sha256 RECONCILIATION_SHA --confirm --timeout 20
```

只接管本控制目录统一创建、保存原提交回执且保留原`local-cli`工单归属的任务。对账前后都核原run仍是当前run、完整原history及登记adapter目录；额外请求/孤立回执会阻止接管该scope。发布原不可变fence后，须逐一确认所有历史job的原请求、可信终态回执及哈希产物；缺失/损坏证据保持unknown并保留租约。可信执行器仍须遵守fence和独立walltime；这份文件协议证据不能代替系统进程扫描。所有协调者必须保持task ID不可复用，不能在协议外为同task启动新run。

`reconciliation`只读本地记录，不查远端、不发布fence或释放租约。`prepared`尚未保存写前检查点；`unknown`已保存原outcome/history身份但没有完整清理证据；`confirmed`已保存清理证据但释放回执尚未保存；只有`reconciled`表示租约已按精确原claim释放且回执已保存。恢复会重验原事实，按同一fence/证据摘要幂等推进。重复reconcile返回已保存状态，明确resume-reconcile才继续未完成操作。已完成回执是历史事实，实时外部状态继续使用external-status。

`original_outcome`保持真实原结果：即使原结果是CANCEL_UNCONFIRMED，本次确认清理也不会把它改成BLOCKED或开发成功。`execution_success: null`不推断候选是否通过。原native release适用时保留原outcome摘要，其余闭合清理使用独立清理evidence摘要，不能手改owner/ledger或删证据绕过冲突。CLI变更只在reconciled时返回0；HTTP成功也须检查status。

API：GET `.../tasks/TASK_ID/reconciliation`、POST `.../tasks/TASK_ID/reconcile`（`revision/run_id/confirm/timeout`）、POST `.../tasks/TASK_ID/resume-reconcile`（`revision/intent_sha256/confirm/timeout`）。confirm严格为true，写请求沿用同源保护及`X-Ergora-Request: 1`。Linux/WSL2使用登记完整运行时；每阶段1–60秒，父进程另留5秒，本地预检另计。原任务锁保护同task，远程阶段不持控制库写锁。

执行状态目录`ergora/task-reconciliations/TASK_ID.{intent,attempt,evidence,result}.json`须与原任务/创建/提交、请求/回执/产物/fence及`ingress/leases.sqlite3`一起备份。证据或数据库丢失时保留未知，不通过新建ledger重建所有权。

### 导出精确候选与恢复回执

仅适用于统一创建且已保存提交回执的任务。先用`task status --run-id RUN_ID`核对原运行已完成且outcome为`REVIEW_READY`，审阅其确切candidate与可信检查/独立审查证据，然后明确指定本地目标分支：

```bash
ergora task export my-project TASK_ID --revision 1 --run-id RUN_ID --candidate-sha CANDIDATE_SHA --branch agent/TASK_ID --confirm --timeout 20
ergora task export-status my-project TASK_ID
# 中断后先查export-status，以原intent_sha256和当前项目修订恢复：
ergora task resume-export my-project TASK_ID --revision 1 --intent-sha256 EXPORT_SHA --confirm --timeout 20
```

一个任务保存一个不可变导出目标。重复export只返回原记录，不能更换run、candidate或branch。`prepared`表示尚无写前检查点，可明确resume继续；`unknown`表示已保存原结果摘要，恢复只核对原run/outcome及实际分支，不能重新fetch或创建。分支不存在时返回`unknown/branch_not_found`，避免复活人工删除的分支；保持原记录并人工对账。已有分支指向不同commit、原结果变化或记录冲突均明确拒绝。

Git只抓取对象，不写FETCH_HEAD，不checkout、merge或推送。目标分支通过Git条件事务创建；已有正确candidate可接受，其他已有分支和符号引用保持。确认分支后沿原规则释放适用工单租约，写原格式`tasks/TASK_ID/export.json`及本工具回执。`exported`表示已保存该导出事实，`checked_out: false`、`merged: false`，后续仍须按项目策略审查合入。重复终态读取不会实时核查之后的人工分支修改。

`export-status`只读本地记录，不连接Temporal或释放租约。意图、写前检查点和回执位于执行状态目录`ergora/task-exports/TASK_ID.{intent,attempt,result}.json`，须与原创建、提交、任务、工作区及租约记录一起备份；不能只备份控制库。准备时严格核当前revision/confirm并非阻塞取原任务锁，网络/Git阶段已释放控制库写锁。每阶段1–60秒预算，父进程另留5秒，预检另计；超时后先读记录，实际是否写入仍以原分支和检查点对账。Linux/WSL2使用登记的完整运行时，旧入口导出不隐式接管。

API：GET/POST `.../tasks/TASK_ID/export`，POST正文为`revision/run_id/candidate_sha/branch/confirm/timeout`；POST同路径`/resume`使用`revision/intent_sha256/confirm/timeout`。写请求沿用同源保护及`X-Ergora-Request: 1`，confirm必须为true。CLI变更只在exported时返回0，HTTP成功也须检查status。

### 显式服务管理

Linux/WSL2 中，先安装、初始化参考运行环境并完成[统一项目注册](PROJECTS.md)。`ergora services` 使用登记的 execution 目录及参考环境中的 Supervisor，不需要系统服务权限。一个执行状态目录是一套共享服务栈，可能服务多个项目；停止会影响该栈的在途任务。以下 `--revision 1` 应替换为 `project show` 的当前修订：

```bash
ergora services status my-project
ergora services start my-project temporal worker --revision 1 --timeout 30
ergora services logs my-project worker --bytes 8192
ergora services stop my-project worker temporal --revision 1 --confirm --timeout 30
ergora services shutdown my-project --revision 1 --confirm --timeout 30
```

可选服务为 `temporal`、`mlflow`、`worker`、`executor`、`a2a`、`training-worker`，只启动列出的服务，不自动补依赖或启动研究。正式开发需要显式启动 `executor` 并完成原执行准入；托管 executor 使用同一 Ergora 控制目录的选择式执行器。Supervisor 的 `RUNNING` 仅代表进程状态，服务协议、worker/队列、模型与任务仍分别验收。停止和 shutdown 必须确认；1–60 秒的控制等待时限从注册预检后计算。`outcome: unconfirmed` 表示操作可能继续进行，应查状态对账；未确认 STOPPED 前不重启，CLI 对失败/未确认返回非零。

首次 start 在执行状态目录下创建 `ergora-services/`，记录控制目录归属、独立 socket 及配置，复制原 Supervisor 程序定义并关闭全部 autostart，原 ini 保持不变。原 Supervisor socket 仍存在时拒绝接管：先通过原 `agentflow services stop` 停止并核对原栈，再使用新入口；陈旧 socket/PID 也需先对账。注册投影漂移、控制目录归属冲突或过长 Unix socket 路径会明确报错，后者应选择较短的持久 execution state 目录。软件升级前先 shutdown 托管栈，升级后按原参数显式启动。

日志默认原生字节窗口为 8192，可设 4–65536（至少容纳一个 UTF-8 字符）；使用返回的 `next_offset` 作为下次 `--offset`。`overflow` 表示中间内容超过窗口，`rotated` 表示当前文件长度小于游标、窗口已重置，需结合原生日志核对。通过 Supervisor 查询实际日志路径后，只对普通文件进行有界读取，不完整加载大文件。`limit` 限制原始读取字节数，文本/JSON响应大小可能因替换字符或转义而增加。合法 UTF-8 边界会保留；不完整后缀的 `pending_bytes` 尚不计入 `next_offset`，后续追加后用原游标继续；非法字节显示替换字符。

同源 API：`GET /api/projects/ID/services`；`POST` 同路径，正文 `{"action":"start","names":["temporal"],"revision":1,"timeout":30}`；停止加 `"confirm":true`，shutdown 的 names 为空。写请求沿用 `X-Ergora-Request: 1`。`GET /api/projects/ID/services/NAME/logs?limit=8192&offset=0&stderr=false` 返回有界文本与游标。Windows 原生支持控制台，但本地 Supervisor 管理需要 WSL2/Linux。

等价项目/Agent CLI：

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

独立Agent调用在启动工具前将该视图保存到运行记录的`configuration`，并沿用原`binding/project_revision`；通过主入口创建的正式任务在创建时冻结该视图；旧创建方式在首次接入可选执行器时把它加入`agent-bindings.json`。之后修改项目或推荐默认不会更新在途任务。旧任务没有此附加字段时继续读取原绑定快照，不补造历史来源；旧运行记录也不回写。Skill/记忆实际上下文仍单独保存在调用记录，当前快照不声明冻结所有外部工具内部行为。

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
