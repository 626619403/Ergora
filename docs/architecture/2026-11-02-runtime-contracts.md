# R5：当前运行契约与平台责任

日期：2026-11-02。这是当前实现的调用约定和能力边界，源码身份为 `f9a9b743be1b5bde352d212b75c47358d5d73e9a`。验证及未验项见 [R5 交付记录](../delivery/2026-11-02-runtime-contracts.md)；后续能力按 [实施计划](../plans/2026-11-01-all-in-one.md) 单独验收。

## 运行结果与产物归属

已有共用原语是 [processes.run](../../src/ergora/processes.py)，生产消费者为 agents、evaluation、optimization 和 kernel。成功返回时的字段为：

|字段 / 文件|现有含义|调用者责任|
|---|---|---|
|`status`|进程层的 `succeeded / failed / timed_out / cancelled`|领域可以收紧或转换含义；不能据退出零判定候选通过|
|`returncode`|原进程退出码，未启动的受监督取消可为 `null`|取消 / 超时保留原码，不用它覆盖已确认的中断状态|
|`output`|本地输出目录路径|不是可移植的导出 URI，也不是产物内容身份|
|`stdin.txt / stdout.txt / stderr.txt`|UTF-8 输入及命令输出|命令本身必须遵守协议编码；进程创建 / 资源清理异常可能直接抛出，不保证总能返回上述摘要|

输出目录必须是新目录。公共进程结果没有原生任务 ID、候选验收、费用或通用恢复承诺。领域记录保存这些事实：

|所有者|现有记录 / 引用|成功、取消及恢复的实际含义|
|---|---|---|
|[agents](../../src/ergora/agents.py)、[agent_runs](../../src/ergora/agent_runs.py)|独立运行 ID、项目 / 修订、冻结 binding、prompt SHA、Skill / recall 快照、结构化 `result / result_sha256`|有 schema 时还须验证结构；此成功仍不是正式阶段证据通过。独立调用是同步模式，没有持久后台取消 / 恢复 API；硬退出可留 `running`|
|[evaluation](../../src/ergora/evaluation.py)|评价 ID、候选 digest、固定 suite digest、逐 case 进程结果、评分 / `passed` / 自报成本|整套进程 / 结构检查成功后仍要经 `compare` 资格检查与 Skill 采用用例；评价 `succeeded` 不等于采用|
|[optimization](../../src/ergora/optimization.py)|优化 ID、父候选、提案 / 评价与预算记录|GEPA 只产生候选；不移动活动 Skill 头。取消和墙钟限制不扩展为后台任务能力|
|[research](../../src/ergora/research.py)|研究 ID、冻结 request、来源快照 SHA、提案、累计 / 保留字节及耗时 checkpoint|`cancel` 只登记请求；worker 确认后才 `cancelled`。同 ID 只恢复同项目同请求，未知在途流量保留预算，不能重新获得完整额度|
|[kernel](../../src/ergora/kernel.py)|Ergora 运行 ID、冻结 binding / 全局配置身份、campaign 路径、原生记录及各 operation 的进程证据|`prepared / observed / native_finished / native_failed` 保留原生含义；`prepare/run` 中断或输出不可信为 `outcome_unknown`，须对账；campaign 完成仍只是候选|
|[reference_executor](../../src/ergora/reference_executor.py) 与冻结 reference|正式任务 / 工作单元 / process submission、terminal / ledger、候选 SHA、可信检查、回执、精确批准|状态由原执行链拥有；取消请求与停止确认、批准与执行、阶段完成与最终结果不可合并。既有工作流恢复继续沿原 ID / 引擎对账|

CLI / Web 现在读取各域记录，没有实际消费者需要另一份通用 Run 文档。F3–F5 接入正式任务、统一导航及证据引用时，应从这些权威记录投影；统一展示字段不能替换 native state，也不能把未知成本写成零。

## 生命周期矩阵

表中是现有实现范围，不能把一种模式的保证推给另一种模式。所有命令都在当前用户信任边界内运行。

|模式 / 所有者|正常完成、超时、取消|控制器退出与限制|
|---|---|---|
|Linux 普通命令 / `processes.run(supervised=False)`|新 session / 进程组；finally 杀同组后代。`communicate` 超时为 `timed_out`，捕获到 `KeyboardInterrupt` 为 `cancelled`，结束前等待直接进程|控制器被 SIGKILL 后 finally 不执行，没有自动清理保证；默认 SIGTERM 也不具备自定义取消契约。主动逃离进程组的程序不在此清理保证内|
|Linux 正式阶段 / `process_job` → `stage_driver` → `processes.run(supervised=True)`|保留外层 monitor 的进程组；专用单任务 stage_driver 用 subreaper 收养 / 杀掉 / 回收后代。SIGTERM 仅设置取消标志，清理不可被该信号打断。deadline、取消 fence、TERM/KILL 升级由原 monitor / timeout 负责|`processes` 内的全局取消标志只供专用 stage_driver，不是多任务状态。不能把普通命令的 `communicate(timeout)` 搬进来。monitor 被杀后的即时整树停止不在本轮测试保证内；已提交但无 terminal 的作业拒绝自动重跑|
|Linux 资料抓取 / `research._download`、`_fetch_source`|spawn 网络子进程；父进程检查总墙钟 / 字节预算、取消和进度，finally kill / join；子进程设置 SIGALRM|子进程在网络操作前设置 parent-death SIGKILL 并核对父 PID；父硬退出不允许无界网络工作。checkpoint 对未知流量 / 时间保守记账，不能因文件大小可读就视为已确认传输|
|Windows 普通命令 / `processes._run_windows` + `windows_job.Job`|受信 gate 进程先 assign Job，收到 stdin 后才启动真实命令；定期返回 Python 处理 Ctrl+C。超时 / 取消 / 正常结束均 TerminateJobObject，确认 active=0 后 CloseHandle|控制器独占非继承 Job 句柄，死亡触发 kill-on-close；assign 失败先杀 gate，不启动命令。清理失败抛出异常，不能报告为已停止|
|Windows 资料抓取 / `research` + 同一个 `Job`|Event gate 在 assign 前阻止网络；父进程沿研究预算与取消协议 kill / join，Job 负责后代生命周期|共享 Job 的死亡处理，不共享命令 stdin 协议；不能把研究预算 / checkpoint 挪入 Job|

Windows 原生支持普通 Agent / evaluator 等可用工具及资料观察；supervised reference、mini Linux/bash driver、Forge 原生 campaign 仍要求 Linux / WSL2。Windows `.cmd / .bat` Agent launcher 被明确拒绝，须选择原生 `.exe` 或显式解释器。

## 不确定结果不能被压平

Forge `prepare/run` 的进程非成功、JSON 缺失或异常不证明原生任务没有产生副作用。kernel 保存 `outcome_unknown` 和 `requires_reconciliation`；后续失败的 status 查询不能清除该标志。再运行须明确 reconcile reason，且不能因为项目绑定已变化就换掉在途 campaign 的冻结 binding。`native_finished` 仍须项目正确性 / 性能独立评价。

研究取消保持“请求 → worker 确认”的差别。正式工作流对停止未确认保留未知结果并拒绝无证据的自动重提。普通独立调用没有这些持久控制能力，不显示为可恢复任务。

这些规则分别由实际业务所有者维护。既有 `processes.run` 共用结果与 Windows Job 已提供有真实消费者的复用；命令、受监督阶段和网络抓取的通信 / 预算 / 死亡语义不一致。R5 因此保留现有代码，不新增基类、转发层、通用终止状态机或第二套调度器。

## 验证位置及后续责任

|边界|现有验收入口|证据性质|
|---|---|---|
|普通命令 UTF-8、正常 / 超时后代清理、Windows Job death / Ctrl+C / gate|[test_processes.py](../../tests/test_processes.py)、[test_projects_tools.py](../../tests/test_projects_tools.py)|本轮 Linux 命令实跑；真实 Windows 使用相同源码身份的既有两 OS CI，不以模拟代替|
|正式六阶段及受监督信号窗口|[test_reference_executor.py](../../tests/test_reference_executor.py) 及其 fixture|本轮在隔离目录调用原执行器 / adapter 的确定性命令；不等于再次运行 Temporal 服务的端到端旅程|
|资料预算、取消、硬退出后恢复|[test_research.py](../../tests/test_research.py)|本地 HTTP 进程与持久记录实跑；未选择的 Temporal 调度集成明确跳过|
|固定 Forge / mini SDK|[test_agents.py](../../tests/test_agents.py)|显式选择 SDK，CPU / 本地响应 fixture；不是模型或 GPU 效果结论，未运行真实 campaign 的模型执行及取消竞态|
|普通 Linux controller 硬退出差异|交付记录中的一次性子进程探针|隔离受信进程实测并主动清理；不是新增“应遗留孤儿”的永久测试或产品承诺|

R6 收拢 reference 访问边界；F3/F4 负责正式任务查询 / 控制和持久运行视图；F5 负责跨域证据与成本引用；D3 负责真实文件 / 网络隔离验收。进程组、Job、目录、worktree 均不提供本文件未声明的访问隔离。
