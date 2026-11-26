# 诊断与修复

简体中文 · [English](../../operations/services.md) · [文档目录](../../README.zh-CN.md)

`ergora tools doctor PROJECT` 按有效绑定显示安装、版本、认证、连接、任务前置条件和修复指引，附项目修订及配置摘要。默认只做本地安装检查，不连接外部服务，也不调用模型。`ergora tools doctor PROJECT --probe --timeout 5` 主动检查原生 CLI 版本、Codex 凭据状态及 ReMe/Temporal 的 TCP 可达性；`--timeout` 为全部主动探测共用的 1–30 秒预算，本地安装检查及进程清理另计。工具绑定页也有同一主动探测入口，API 为 `POST /api/projects/PROJECT/doctor`，正文 `{"timeout":5}`，沿用本地写请求头 `X-Ergora-Request: 1`。

`credentials_present` 只表示 CLI/环境有凭据，不证明账号、额度或模型可用；`tcp_reachable` 只证明传输可达，不证明服务协议、授权、命名空间或 worker 就绪。`not_checked`、`not_confirmed`、超时和预算耗尽均不能当作通过。自定义命令不会被 doctor 执行，Claude/mini/GEPA/Forge 的认证及真实任务仍需按修复指引显式验收；Forge 版本必须符合固定提交。`task_availability: available` 仅表示 SQLite/手动操作等本地前置条件可用，不是正式六阶段验收。原始探测输出不返回、不持久保留，只返回版本号或状态。

## 服务停止后的读取与恢复

已完成统一登记和完整执行环境安装时，服务是否运行与持久回执是否存在分别判断。完整正式执行使用Linux/WSL2；Windows控制面及可选工具的范围见[Windows手册](../../install/windows.md#choose-an-execution-environment)。

|要读取或执行的内容|需要运行的服务|事实边界|
|---|---|---|
|原合同、创建/提交/批准/取消/对账/导出记录|无需启动执行服务|读取持久文件；历史回执不证明当前Git分支、外部进程或实时运行状态|
|已闭合原run状态/结果，原事件及job回执/文本材料|Temporal；无需启动worker/executor|固定原run及证据摘要；事件/job读取也适用于运行中原run，材料还要求原可信产物目录可读|
|闭合run的证据索引、预算事实与交接包收集|Temporal、登记的Linux/WSL2完整运行时及原材料；无需worker/executor|原run闭合且无后继，沿原合同/回执核材料；连接失败不返回部分完整索引或交接包|
|已保存交接包的`handoff verify`|无需在线服务、控制库或Temporal SDK|Windows/Linux基础安装可离线核包内字节及声明的身份；来源认证、完整history与候选复验另核|
|运行中原run的阶段/状态查询|Temporal及可响应workflow query的worker|`task status`在RUNNING时调用workflow query；只有Temporal在线可能查询失败|
|继续正式阶段及真实Agent调用|Temporal、对应worker/executor及所选工具认证|投递回执与实际完成分别核查；启动服务不会自动补发未知操作|
|显式服务启动/退出和日志|Linux/WSL2完整参考安装及Supervisor|由统一入口管理本执行目录所属栈；共享目录的项目共享服务|

关闭浏览器或重启HTTP后，重新选择原项目/任务并读取原记录即可恢复；清空会话选择也不会删除后端意图。run输入可从持久submission回填，批准/取消仍需保留原decision/request ID。原运行服务不可达时页面明确显示查询失败，本地回执仍可独立读取。不要把连接失败当作未提交，不换task ID重跑。检查已有闭合运行只需显式启动Temporal；恢复执行前另核所需worker、executor、工具与原意图状态，步骤见[显式服务管理](#显式服务管理)。

## 旧参考 CLI 与统一入口

统一`ergora task`从所登记参考环境读取Temporal配置，旧`agentflow task`从当前shell读取连接。本机loopback开发服务的旧命令可显式设置：

```bash
export TEMPORAL_ADDRESS=127.0.0.1:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_LOCAL_DEV=1
```

LOCAL_DEV仅适用于loopback开发服务，其他服务按自己的认证配置连接。两种入口的任务归属不同；旧任务保持原配置/STATE和原CLI，不能通过统一命令隐式接管。Supervisor管理也是按执行state区分，停当前共享栈会影响其所有项目。

## 显式服务管理

Linux/WSL2 中，先安装、初始化参考运行环境并完成[统一项目注册](../../projects/registration.md)。`ergora services` 使用登记的 execution 目录及参考环境中的 Supervisor，不需要系统服务权限。一个执行状态目录是一套共享服务栈，可能服务多个项目；停止会影响该栈的在途任务。以下 `--revision 1` 应替换为 `project show` 的当前修订：

```bash
ergora services status my-project
ergora services start my-project temporal worker --revision 1 --timeout 30
ergora services logs my-project worker --bytes 8192
ergora services stop my-project worker temporal --revision 1 --confirm --timeout 30
ergora services shutdown my-project --revision 1 --confirm --timeout 30
```

可选服务为 `temporal`、`mlflow`、`worker`、`executor`、`a2a`、`training-worker`、`training-budget-worker`、`training-cycle-worker`，只启动列出的服务，不自动补依赖或启动研究。v7来源任务可用`ergora services start my-project temporal worker executor --revision 1 --timeout 30`显式启动其原六阶段所需服务；旧v1–v6的安装级doctor另要求本地A2A监听，可显式加上`a2a`，MLflow按观测需要另启。托管 executor 使用同一 Ergora 控制目录的选择式执行器。Supervisor 的 `RUNNING` 仅代表进程状态，服务协议、worker/队列、模型与任务仍分别验收。停止和 shutdown 必须确认；1–60 秒的控制等待时限从注册预检后计算。`outcome: unconfirmed` 表示操作可能继续进行，应查状态对账；未确认 STOPPED 前不重启，CLI 对失败/未确认返回非零。

首次 start 在执行状态目录下创建 `ergora-services/`，记录控制目录归属、独立 socket 及配置，复制原 Supervisor 程序定义并关闭全部 autostart，原 ini 保持不变。原 Supervisor socket 仍存在时拒绝接管：先通过原 `agentflow services stop` 停止并核对原栈，再使用新入口；陈旧 socket/PID 也需先对账。注册投影漂移、控制目录归属冲突或过长 Unix socket 路径会明确报错，后者应选择较短的持久 execution state 目录。软件升级前先 shutdown 托管栈，升级后按原参数显式启动。

`training-cycle-worker`的普通／stop queue各有独立活动槽；它与budget服务使用不同PID，提供四个活动消费者。集成范围、显式启动和70秒停止观察见[训练手册](../../training/controllers.md#integration-entry-point-for-the-independent-cycle-service)；同一worker承载有限V2／V3候选控制器；使用[显式控制器授权与提交命令](../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization)，启动服务本身不授执行权。

单个 Campaign 的 Worker 由对应任务的专用服务管理。服务状态分别报告本机进程和原注册队列的轮询证据。[管理一个 Campaign Worker](../../improvement/campaigns.md#manage-one-campaign-worker)

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

页面和 CLI 共用持久业务状态；修订冲突时刷新后再保存。Agent 调用的 `succeeded` 不是正式任务验收或审查通过。默认参考执行器保持原配置；需要角色选择作用于正式任务时显式启用桥接，见 [Agent 选择与正式执行手册](../../agents/backends.md)。

## 远程访问、恢复与维护

服务只监听 loopback。远程电脑使用 SSH 转发，然后打开本机 `http://127.0.0.1:8977`：

```bash
ssh -L 8977:127.0.0.1:8977 user@server
```

本地接口要求同源与自定义请求头，并校验 Host；它使用当前用户权限，面向可信项目。团队身份、公网服务和每 Agent 的 OS 隔离需要单独接入。容器内无法使用 namespace 沙箱时，不会为让调用成功而自动取消 Agent 自身的 sandbox。

应用在前台运行；Linux / WSL2 可用 Supervisor 管理 `ergora serve` 及各项目的 `ergora research worker PROJECT`，Windows 原生先使用前台终端。安装不自动后台执行任务、调用模型或启动研究。停止写入后备份完整 `ERGORA_HOME` 以及业务 Git 仓库；恢复时核对仓库实际路径和工具登录。记忆删除不会清除独立备份及过去归档的调用输入。

开发和换机继续工作时，先读 [PLAN.md](../../PLAN.md)、当前活动切片的 `docs/delivery/` 记录，再检查分支、`git status` 与最近提交。测试默认不调用付费模型；外部服务和 GPU 的效果验收单独记录。
