# 私有真实 fault harness 独立静态审查

日期：2026-11-16。Reviewer：独立 fresh-context agent `cycle_live_harness_review`。范围是私有 W2 post-return completion fault、W5 原 H flock 下的 stop/cancel、W7 实际 server history 容量故障的准备代码及文末新增 extra/helper；不认证未来现场结果、产品完成或训练质量。初审需求符合性与可维护性均为 **request changes**；原范围 r3、新增范围 r5 静态复核两轴均 **approve，开放 0**，准确身份与限制见文末。

## 身份、范围与检查

读取项目 `AGENTS.md`、`docs/PLAN.md`、首轮计划的 W2/W5/W7 合同、私有 harness README，并采用 maintainable-project-delivery 与 ergora-codebase-quality 的独立审查／test-seam 规则。审查时主树为 `refactor/architecture-foundations`、HEAD `df43660`；主树已有 PLAN 和现场记录改动，reviewer 未覆盖这些改动。

审查文件位于 ignored 私有目录 `.ergora/checks/cw1/fault-harness/`：

|文件|本轮 raw SHA256|
|---|---|
|`service_wrapper.py`|`f5f7156034530e60fbbc40649a40f9f9825c1e3635a96e00c2e2890b8f1285ac`|
|`fault_operation.py`|`30e547b0c2448744fc6c3e7d0865c37ea6cf42da55d029d1df88b3ad8643a2cf`|
|`service_control.py`|`c71f1d0ec6aadab39942dbbece89f3f4422399f4e265b25a259c0f0548cac5b2`|
|`drive_fault.py`|`ce46401b81f9b93ac1b28cd7d3d4bd4b03d57d73f004293e441cfbddb9e2fdb9`|
|补充 `prepare_negative.py`|`bd3246277e6f7bdf60d5decf8a54a9a2717c1f4d873da79ef3c12df9c54616b4`|

安装 worker raw SHA256 确认为 `187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`；原始消费者验收 seam 确认为 `3562e3edf92d49ace7f9ccfe9ae010b8252d506dac0f28252852372f2b9ac4e9`。只读核查安装 worker、services owner、submission/execution owners 与 native adapter；五个脚本经 `ast.parse`，未导入或执行 harness。未运行服务、网络、runner、Workflow、Replayer、产品回归，未提交 Git。以下行号只对应上表身份。

## Findings

### H1 / P1：原 service stop/start 不会装载新 wrapper

位置：`service_control.py:11–15` 与 README 的执行命令。

该脚本只在调用进程中替换 `reference.training_cycle_worker_command`。原安装 `services.control` 仅当 Supervisor daemon 为 `not_running` 时调用 `_prepare` 生成命令（`services.py:200–201`）；既有 daemon 的 start 仅调用 `startProcess`（`:228–231`）。只读现存 managed 配置的 cycle command 也确实是原 `cycle_main`，没有 wrapper。故在当前已有 daemon 的现场，README 所列 stop/start 只会重启原 worker，三个故障均不会注入；服务 RUNNING 不代表 hook 已生效。逐 case 更换 settings 路径也不会更新 daemon 内存里的命令。

最小处置：删除或硬拒绝该脚本的 wrapper `start` 入口，README 不再提供失效命令。root 已决定以原 owner 显式 stop **仅** cycle worker，核实 STOPPED／原完整身份退出后，在独立前台 session 直接启动同安装解释器的 wrapper，并由 root 管理其完整身份和退出；不修改活 Supervisor 配置，不为注入故障重启基础服务。该替代的必要条件见后文；修改后须复核，未在本轮执行。

### H2 / P1：finally 中的采集失败遮蔽主故障，并跳过剩余原件

位置：`drive_fault.py:226–257, 282–285`。

主流程异常后，`describe`／cancel 清理自身仍可抛错。无条件 finally 又依次 fetch history、describe、Replayer、decode、snapshot、inspect，再执行 acceptance checks。可达例子是 W7 超时未达阈值，随后 replay 失败或连接不可用：原 timing miss 会被新错误覆盖，后续 activity audit、原链快照和 native-after 全部缺失。即便 replay 成功，finally 的 control-check 异常也会替换首个故障。`failure.txt` 虽可保留先前 traceback，不能弥补采集被提前截断。

最小处置：保留主异常；清理与各类证据采集分别记录阶段、异常和未完成项，允许独立可做的 raw snapshot／events／history／status 继续采集。先保留 raw history 再 replay，replay 错误单列；有主异常时最终重新抛主异常，无主异常时才以审计失败结束。原件路径不存在、容量异常、decode 不完整保持 failed/pending，不能吞错为通过。释放自己 flock 的路径须先于可失败的收尾采集，并保留 root 最终资源审计责任。

### H3 / P1：W5 缺失退出 marker 会变成通过，且未检查 stop 实际进入

位置：`drive_fault.py:195–214, 269–276`。

当前核心判断为 `bool(stop) and (not exits or scheduled_time <= min(exits))`。若 normal adapter 仍在 cleanup、worker 已失联，或退出 marker 未写出，`not exits` 会让 check 为 true。代码只等待 stop **scheduled**，随后释放锁，未核 stop adapter-enter；因此无法区分“独立 stop 已开始运行”与“只有排队记录，直到 normal 清理后才进入”。README 已要求增强检查，但实际代码没有实现。marker 缺失既不能证明先后关系，更不能证明资源停止。

最小处置：缺失 normal adapter-exit 保留 pending/failed；保留同原 activity、run、process 的进入／退出事件。分别输出实际 history 中 schedule 先于 normal exit，以及 stop adapter-enter 先于 normal exit 的证据；后一项缺失或反序不得冒作独立 worker 及时运行通过。必要时在原窗口内等待 stop enter 再释放自己 flock，超窗保持失败，不能延长原产品 allowance。完整 S/H／reaper／后代／root 的实际终止与 wait 仍由 root 外部 sampler 和原资源记录核验。

### H4 / P2：重复 stop/cancel 的实际命中窗口未被记录或验收

位置：`drive_fault.py:184–194, 207–209`。

两次 `signal`／`cancel` RPC 是顺序调用，但没有每次发起／应答时间、结果或第二次调用时的 normal 状态证据。第一次取消后 S/reaper 可以先完成 H 清理，第二次才返回；现有 checks 仍通过，从而将普通幂等重复调用写成“阻塞期间重复取消”。两次 SDK cancel 也不能推断为两个独立的 server cancel-requested history event，server 可合并已请求的取消。

最小处置：记录两次真实 RPC 的发起／返回及异常；signal 以实际两份 signal history 绑定原 input，cancel 则明确两次实际 API 请求与 server 可见事件的区别。用原 adapter 生命周期与外部完整 H 身份采样证明第二次请求时原 normal 仍未清理完成。若没有这个机会，保存原记录但该子项 pending，不能加长或重置产品预算以制造机会。root 可在现场补齐这些原始观测；仅靠当前 driver 输出不足以验收此项。

### H5 / P2：原链快照未包含 native job 自身的 raw records

位置：`drive_fault.py:52–69`。

这里 `training/jobs/<experiment>/managed-execution` 的 **experiment ID 路径正确**：实际 native `job_folder(experiment_id)` 与安装 `ExecutionRecords` 都这样定位，`job_id=local-perf-<experiment>` 是记录字段，不能据此把目录改成 job ID。缺口是只 glob managed-execution 子目录，遗漏其父目录里的实际 native `request.json`、`started.json`、`result.json` 等，以及本实验 fence／negative-result。`native-before/after` 的解析值及 SHA 清单不能代替这些 raw 原件的保留。

最小处置：为同一明确 experiment 的 native job 父目录及其 managed 链保留完整 JSON 原件，再明确保存该实验 fence／negative-result；缺失记录保留“缺失”观测，不能制造记录。W2 的 intent/attempt/receipt、request/launch/attempt/ack/stopped 的数量和 SHA／root身份比较应基于实际原链，最终由 root 给出逐项判定。若 root 另做完整 raw 留存，本项可按那个准确证据处置，无需扩展为全目录扫描。

## 可以静态确认的 seam 与剩余条件

W2：wrapper 确实先 `await` 原 adapter，完整序列化返回，再以显式 retryable ApplicationError 代替 SDK completion；正式 Workflow 原配置是 maximum_attempts=1。它验证 post-return completion fault，不是物理网络丢包，也不包含 prepublication/request-absent 矩阵。原 adapter 返回 unknown 或尚未 publication 也能触发 marker，故 marker 不能代替实际 effect 原链。现场还须从真实 history 证明选中 effect 仅一次，原后续 observe／reconcile 真实发生，且原 intent／attempt／receipt／root／执行链不重复；当前几个计数布尔值不足以单独认证。

W5：原 seam 通过 `runpy` 复用，S/H 算法及 `processes.run`、reaper 保持。共享 flock 只在精确 authorization 路径、精确 v2 activity type、`request-execution-candidate` mode 的原 `_read_bytes` 上注入。start、初次 inspect、stop 的读取不受该注入阻塞；driver 的 exclusive flock 与 H shared flock 是真实内核锁。这建立可达的阻塞点，未建立任何资源已停止的证明。`CANCELED` 与业务 stop／durable／drain／executor proof 必须分列。

W7：发送的是实际编码总量小于 32 KiB 的 malformed signal Payloads；真实 signal handler 拒绝其形状，不产生合法 stop intent。driver 读取实际 Describe 的 history_size_bytes，最多 384 次／16 并发，原 result 仍保持完整；原 schedule-to-close 开始时间加有限 hold deadline 不重置 allowance。阈值必须在这个真实窗口内达到，并从后续实际 stop request 验证 reason=`history_capacity_limit`，没有第二个 ordinary command。静态不能保证原 cold10s 中的吞吐或 SDK/server 更新时序；超时保持 pending。README 描述的 later-observe/prefill 变体尚未实现，不能视为已准入 fallback。W7 也不覆盖第256／257次 ordinary command 的另一验收项。

补充 prepare 脚本只调用原 registration、baseline、runner、prepare、inspect 接口，没有 authorize／submit／execute 或服务调用；新 runner 只 bounded sleep 后 exit23，不产 evidence。它在新隔离私有 repo 创建源码提交，case IDs／目录已存在则拒绝覆盖，不复用 positive-r2/r3 原件。复用 materials 的 hash/contract 不构成新训练或质量证据；这里未运行 preparation，也未认证其未来产物。

## root 直启替代的最小前置与收尾

1. 原 service owner 显式 stop cycle worker，保留结果并核原完整身份退出；基础服务保持 root 现有控制。严禁两个 worker 同时消费原 normal／stop queue。
2. 以原安装解释器、原 installation、原 AGENTFLOW_CONFIG_DIR／AGENTFLOW_STATE_DIR 在独立前台 session 启动 wrapper；原 `cycle_main`、正式类默认 sandbox、normal／stop 两 worker 和原 budgets 保持。启动前原 artifacts 子目录不存在，原 settings／IDs 已冻结；driver 只在提交前原子补齐绑定。
3. 保存实际 bootstrap 的 worker 路径/SHA、完整进程身份、命令和本 case settings identity。bootstrap 未出现或与原身份不同则拒绝提交；不以进程 RUNNING 代替 hook 装载。
4. 每个 case 使用新 experiment/cycle，顺序执行。外部 sampler 按完整身份跟踪直启 wrapper、S/H、后代和 root/reaper；采样与 markers／原记录互相核对。marker 只代表代码经过该点。
5. root 显式向该 wrapper 的完整身份 SIGTERM 并等待，逐项确认自身 formal/native Workflow 终态及资源清理，下一 case 才能启动。最终原 owner restore 或统一 shutdown 另记；本私有前台 launcher 不冒称由 Supervisor 管理。

原实施者修 H1–H3 后须提交准确脚本身份作静态复核；H4/H5 需代码补齐或 root 给出具体独立原证据处置。本轮只有审查报告写入，不更改产品／harness。root 负责在 PLAN 与现场交付中登记此阻断和后继状态。

## 同片修正复核 r2

准确核得新 raw SHA256：`service_wrapper.py=8658d70ba791b35829e8860676bc95c513435c24b3a32bd41f1ed2e7f919a559`，`service_control.py=61105e7a207952c72a7e655f0ab93e240e7e0257a5424610fb820c19313c10a7`，`drive_fault.py=c333242ecd3485fdbe5ffaf5e735446bb0bcbdc1ec291832a799e0569c9ba520`，`README.md=7c75361651f1d9f82ccd7b93d17f70bc1f2b03a154b423ee092395def533bcbf`；原 seam adapter 不变。五个原脚本及目录内 sampler 的 AST 均可解析；未导入或执行它们。

H1 已关闭：helper 硬拒绝 stop／原 cycle worker 之外的操作，README 已改 root 前台直启与 bootstrap 身份核查，不再声称重启原 managed worker 能载入 wrapper。H3 已关闭：W5 绑定原 operation request、精确 run/activity/worker 与完整 H 身份，在原 allowance 内等 stop enter 再解锁，缺 exit／enter／H 样本返回 null 或 false，严格只接受所有 check 为 true。H4 已关闭为静态可用的观测：两次 RPC 有发起／应答、结果和前后原 H 身份／normal exit 样本，第二次没有未清理窗口不能通过；signal 绑定两份原输入，cancel 区分 API 重复与 server 事件合并。真实时序与资源停止仍待 root 实测。H5 已关闭：快照纳入精确 experiment 的 native job 父目录及 managed JSON、fence／negative，并明确记录预期原件 absent；未错误改用 job ID 目录。

H2 的外层修正有效：先释放 flock，各 collector 独立保存错误，raw history／audit／native 原件先于独立 replay，末尾重抛主异常。但仍有一条原 finding 的窄子路径，位于新 `drive_fault.py:293–296`：`handle.result()` 抛错后，在进入外层 main 捕获前直接写 `result-exception.json` 再 await describe；诊断写入或 describe 再抛错仍会替换 result 的首因。原实施者的静态自查也指出同一子路径。最小修正是先保留 result exception 与 traceback，把诊断写入及 describe 分别当作次级采集；除确证允许的 canceled 终态之外重抛原 result exception。次级失败另记，不能靠其成功才能保留原错。

r2 两轴仍为 **request changes**，仅 H2 该窄子路径开放；其余 H1/H3/H4/H5 在本轮静态范围关闭。root 报告已准备五份全新负例、原 cycle worker STOPPED、其他三服务 RUNNING 且 sampler 已运行，reviewer 没有执行或认证这些现场状态，尚无 wrapper／fault 运行结果。修正该子路径后复核准确新 SHA，再由 root 继续现场。

## 同片窄修正复核 r3

新 `drive_fault.py` raw SHA256 确认为 `ca6fa0ab31e1422439abeb48ea33a2e61880625e4e8e133c89fa319f10172e7f`，其余 r2 身份不变。仅核 H2 的窄修正与其错误汇入路径，未重审或执行现场矩阵：`:293–308` 先保留原 result exception／traceback，诊断写入和 describe 的次级错误独立收集；仅 `w5-cancel` 且实际 describe 确认为 canceled 时接受预期取消，其他情况重抛原错。`:386` 将次级错误汇入统一 collection report 及失败判定，不会静默略过。新 driver AST 可解析。

H2 已关闭；r3 需求符合性与可维护性两轴均 **approve，开放 0**，只表示上述私有 harness 在静态范围具备继续实际验收的条件。root 另报告首个 wrapper bootstrap 正确但尚未投递 driver；reviewer 未运行或认证 bootstrap、任何 Workflow／runner、history 阈值／时序或资源终止。W2 原链、W5 实际重复机会及独立 stop／完整资源 wait、W7 原窗口真实 server 阈值仍各自待 root 的实际原件验收。

## 新增 extra 场景静态审查 r4

原 r3 五文件及其结论保持。另读两份未执行的新增私有脚本：`service_wrapper_extra.py` raw SHA256 `a8a20e49dbeb8a56a51854d4007dbf77c7b14880706b7963f939075e8c43c2c5`，`drive_extra.py` raw SHA256 `0a092740d67b3638321992379bd6836427714786e95ca65f71a301c91cd2ba36`。按 root 请求轻量检查 `probe_signals.py=20f75733d8002b01753d5e24a81411667bb55dd1430fba8f59a0cf9d2ecd6bb7` 与 `root_case.py=56ea193f1aa619ece1450b2291adaeff02f552e97098452a8dc95a9215e26989`。四文件 AST 可解析，未运行。root 报告前两份 W2 与 signal probe 已真实通过、开始 W5；本 reviewer 没有据此认证这些现场结果。

### H6 / P2：新 stable/outage marker 先暴露文件再写内容

位置：`service_wrapper_extra.py:75–83, 101–116`，`drive_extra.py:185–187`。

wrapper 用 `marker.open('x')` 创建可见文件后才写 JSON；独立进程的 driver 只等 exists 成立便立即 read/decode。可达的跨进程调度会让 driver 读到空或半份 JSON，在真实稳定点已命中时错误退出并进入 cancel 收尾，破坏 W3/W4/W8 的实际窗口。最小修正：写完整私有临时文件并 close 后原子 replace 发布 marker，保留新 case 不覆盖旧原件约束；亦可在 driver 内仅对短暂 partial JSON 作原窗口内重读，但原子发布更简单。不能通过重置产品 deadline 处理此竞态。该项阻断 extra marker 场景的可靠验收，原 r3 文件未受此 finding 影响。

### H7 / P1：root finish 的身份检查与 os.kill 之间未绑定 PID

位置：`root_case.py:69–80`。

helper 先 `processes.identity(pid)` 比较，之后直接 `os.kill(pid, SIGTERM)`；两步之间进程退出且 PID 被复用时，会向不属于本 case 的进程发信号。项目已有 `processes.notify_identity(expected, signum)`，用 pidfd 先绑定 PID 再复核完整身份并发送，正是这个边界的原接口。最小修正为使用该接口；退出／身份变化／通知失败分别保留不确定或已退出观测，不扩大进程搜索范围。root 仍须对原 wrapper 与全部资源真实 wait；`requested_not_yet_waited` 只是信号请求记录。此项阻断下一次继续使用旧 finish 发信号，不推断过去已发生误杀。

### 新场景边界与 root 必须补齐的实际证据

W2 pre：选中 action 在 `await invoke` 之前抛显式 SDK failure，不返回 facts；driver 绑定实际 failed activity、后续 observe、原 request/launch/attempt absent，pre-start 还查 candidate intent/attempt absent。这是调用前失败矩阵，不冒称 fsync 后物理丢包。异常直接由外层主异常 owner 捕获，未重现 H2 的嵌套 result 诊断覆盖问题。

W3：driver 不重新 authorize／submit，handle 的 run_id 固定；wrapper 在真实原 request 返回后保存完整结果并制造明确 post-return failure。检查重启前后实际 bootstrap 的不同完整身份与安装 worker/source/argv/c/s 相同，真实 history 的原 request failed 与重启后 observe；stable snapshot 与最终原件供同链比较。root 必须实际停旧完整身份并 wait 后再启，保留同一 authorization 原字节／BOOT clock、work deadline 和候选 owner／intent／attempt／receipt 的比较；脚本当前部分 SHA check 与“不同 bootstrap”不能单独证明实际停止或 A/D 未刷新。该责任已由 driver scope 明确留给 root，不能把 control-check 全 true 等同 W3 完整验收。

W4：只在真实非 cold observe 返回完整 dual-QUEUED、尚无 managed request 且原 work 正数后 hold；hold 截止仍按原 scheduled_time 与原 SDK window。driver 不控制服务、不重新授权，最终要求原 BOOT work 非正、无 request command、无 managed publication 且真实 stop reason 是 work_budget_exhausted。root 必须在 marker 原 deadline 之前由原 owner 实际停 Temporal，保留停／启原件与时刻，确认停至原 work 耗尽才恢复；否则原 result 正常返回后仍可能及时发 request，这是场景未命中，不能改预算补成通过。新 wall90/cleanup60/control30 必须在该新 case authorize 之前冻结。当前代码只为该实际 outage 提供 seam 和控制检查，未认证 outage 已发生，也不覆盖 W4 所有 A+w／R+w 边界。

W8：原 stop adapter 先真实返回并完整保存，随后显式 `cycle_activity_capacity_exceeded` 非重试错误；真实 history failure、正式消费者 failed/needs_reconciliation 与未证明字段 null 分列。它是容量类型的消费者桥接，不是 actual stop aggregate overflow；实际 N32 封套超限仍属于先前真实证据。本次不扩大或继承那个现场认证。

signal probe 只在原固定 w2-request run 做实际 signals/query/history，确认 malformed／foreign／完整 Payloads 容量拒绝以及首个合法 reason 的单一 stop；query/outcome 逐项要求未证明字段存在且 null，replay／资源收尾由原 driver/root 另管。静态读取未发现需要为这个 handler scope 阻断的新问题；未复验其实际输出。

r4 对 **新增 extra/helper 范围** 两轴 request changes，开放 H6/H7；原 r3 approve 保持原身份和原范围。只修上述两点后给新身份同片复核；marker 通过绝不能代替资源停止证明。

r4 后继窄复核：`root_case.py` 新 raw SHA256 `2c4d74813897bde0ca2d95ecfc4367884a0a31e7485cfc84f0e96f4a2efdfc7c` 已核为使用原 `processes.notify_identity(expected, SIGTERM)`，AST 可解析，H7 关闭。通知请求仍不是资源退出证明。root 报告历史几次终止保留当时实际方法与实际 wait，不追认它们使用过 pidfd；reviewer 未复验这些历史现场。新增范围当前仅 H6 marker 原子发布待修。

## 新增范围窄修正复核 r5

`service_wrapper_extra.py` 新 raw SHA256 确认为 `870b88aeaa353173919dff56d8ac4792b37aadeac5e31fed1300d472328e77f3`，`drive_extra.py` 仍为 `0a092740d67b3638321992379bd6836427714786e95ca65f71a301c91cd2ba36`。仅核 H6：`:81–84, 116–119` 两个 marker 均改为同目录临时文件 `open('x')`、完整写入并 close，再 replace 原子发布；原 deadline、真实结果与故障模式保持。新 wrapper AST 可解析，H6 关闭。这里没有要求 crash-durable marker；它仍仅用于 harness 观测，不是产品 stop proof。

新增 extra/helper 范围 r5 需求符合性与可维护性两轴均 **approve，开放 0**；原 r3 五文件结论保持。本轮未重审全矩阵、未执行任何现场，root 另报 W5 signal 真实通过与 cancel 在途不作为本 reviewer 的运行认证。后继仍按各场景的实际原件、原预算、完整身份 wait 与最终资源审计分别验收。

## root 定时动作工具窄审查 r6

仅只读审查新增 `root_interrupt.py`，raw SHA256 确认为 `5598d0535455cbf3d551bef859f1c53c8af9ec959a10322e94b09b4c039d4c36`，AST 可解析；没有运行工具、服务或任何现场。需求符合性／可维护性两轴 **approve，开放 0**，限这个 root 定时动作边界。

W3：marker 绑定当前 configured Workflow 与原 controller receipt 的固定 run；保存原 authorization/cycle/controller 与当时存在的 managed records。旧 wrapper 通知使用原 pidfd 完整身份接口，等待 absent／已退出 zombie／原身份已替换后才创建新 child，不把等待旧非子进程身份等同它原 exec session 的实际 wait。新 child 用相同安装解释器与原 installation/settings/c/s，核新旧 bootstrap 的安装来源／完整 argv／环境一致；不重建 authorization，不重新 submit。新 child 的 Popen handle 由该工具保留并实际 wait，root 后续须按记录的完整身份通知它，原旧 exec session wait 仍单列。

W4：只通过原 services owner 操作明确的 `temporal`，先要求它实际 RUNNING；原 marker finite deadline 前开始 stop，stop 返回 confirmed 及原完整身份退出也必须赶上同 deadline，错过直接失败。之后只采样原 authorization BOOT clock 与原 cycle policy，等 work 非正，同时要求总余量保留大于30秒的 restore 窗口，才正常恢复。该30秒是 harness 的原 owner RPC恢复上界，不给产品授权或 work 续期。原 snapshot 的 SHA 前后比较保留原件；新增 records 仍由 extra driver/root 最终原链审计核查。

异常／收尾：进入可能已送达的 stop 前即设置 restore_needed；任何主错误保存 exception/traceback，finally 以原 owner 尝试 restore。恢复过程的报告写入错误不会阻止实际恢复调用；restore／child通知／child实际wait／log关闭的次级错误另记，末尾优先重抛主错。只通知 marker 绑定的旧 wrapper 与自己持有 Popen 的新 child，没有 broad process discovery/kill。自身报告错误可导致失败，不被改写为动作成功；restore 未确认保持 failed，交 root 后续原 owner 对账。

此工具仍不能证明 W3/W4 场景实际命中、不能代替真实 source/clock/chain、history replay 与所有 S/H/reaper/root 的最终 wait。root 另报 W7 真实场景出现 SDK ordinary pre-canceled WAIT handle eviction 挂起，正在诊断和最小产品修正；r6 不认证该诊断或修正，更不允许借此工具绕过缺陷或将旧包现场结果转移到未来新包。
