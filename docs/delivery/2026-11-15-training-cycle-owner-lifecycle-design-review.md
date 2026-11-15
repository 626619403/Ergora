# c1b1：子预算 owner 生命周期独立设计审查

**最新状态：r2 设计需求／可维护性两轴 approve，开放 0／0；R1、R2 仅在设计层关闭。** 详见文末 r2 复核；原 r1 发现及其原件保持，产品尚未实施／验收。

日期：2026-11-15。审查者为 fresh-context 独立 reviewer `/root/training_cycle_owner_design_audit`；未继承实施会话。审查仅只读源码、固定设计及既有私有原件，本次唯一写入为本文。

**设计结论：需求符合性 request changes（R1、R2）；可维护性 request changes（R2）。** 生命周期拆分有实际必要，窄的 `to_thread(Popen)` 方向可继续采用，原唯一 prepare 也足以承载一次、失效后不恢复的启动 offer，无需第二份 launch 账本。实施前须补清确认后取消的责任，以及恢复路径和共享窗口的具体合同。以下是准备稿的设计缺口，未声称已观察到新增产品 bug。产品尚未实施，真实预算 owner、跨 worker 重启及取消验收均待后继。

## 固定范围与核验身份

源码基线与读取时 HEAD 均为 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `refactor/architecture-foundations`。审查权威输入为私有 `.ergora/checks/training-cycle-owner-boundary/design-scope-r1.json`、`design-snapshot-r1/` 六份完整文档及 `design-tracked-r1.diff`；本页涉及设计的行号均指该 r1 快照。

已逐字核六份快照的字节数／SHA256与 manifest 相同：`docs/PLAN.md`，本片[计划](../plans/2026-11-15-training-cycle-owner-lifecycle.md)／[交付](2026-11-15-training-cycle-owner-lifecycle.md)，父[workflow 计划](../plans/2026-11-15-training-cycle-workflow.md)／[交付](2026-11-15-training-cycle-workflow.md)，及[SDK 边界研究](../research/2026-11-15-training-cycle-sdk-boundary.md)。主计划 SHA256 为 `b94b4ba2517ec25fd6b14dd3b7264dfe9203df5be6e997d0cbedf03ceb1e8913`，研究最终 SHA256 为 `5b357985d75066b77f21ec8ed9442eee691f5a602b6f159e369c51f3f6f9bdf2`。核验当时六份当前正文与快照一致；随后主树 PLAN 的并行任务记账不改变本次 r1 输入或结论。

同时读取根、`src/ergora`、`tests` 的 AGENTS，组件的执行／证据与检查协议，maintainable-project-delivery 的 independent-review，以及 ergora-codebase-quality 的 module-design、test-seams、repository-style。沿[原 controller 合同](../plans/2026-11-15-training-cycle-controller-contracts.md)核实际调用：`training._submission` → `reference.training_submission/_training_process` → `_Submission.run/dispatch` → `BudgetedStart.ensure_owner/own`；并核 `_CycleOperation`、`cycle_operation_main`、mode validator、`Execution.drive`、原 phase supervisor 和 `processes.run(supervised=True)`。

本轮只读比较确认产品路径相对基线零 diff；283 个 tracked reference 文件及 `GATE_SOURCES` 原 25 个 key 保持。固定范围 manifest 记录 203 个本地链接、缺失 0；该计数属于准备方静态记录，本 reviewer 另核了本文所引用文件。其他在途审查状态文档不纳入本片设计范围。c1a2 远端仍属原发布队列，本次未查询或认证其远端发布／CI。

## Findings

### R1 · P1：owner 确认之后、子 start 完成之前的取消责任未定义

位置：本片计划第 39–41 行；原 controller 合同第 4 节要求活动取消执行精确本地 stop。实际边界见 [submission](../../src/ergora/reference_training_submission.py) 第 214–261 行及 [worker](../../src/ergora/reference_training_worker.py) 第 136–150 行。

准备稿明确“确认前取消”要保留 spawn、先收尾 S-H，再精确 TERM／wait 根；又明确成功 start 后取消退出观察不得 kill 已确认根。但 owner 确认发生在 dispatch-H 和 SDK start 之前。可达场景是：确认 H 已返回完整 owner，dispatch-H 正在 lookup、attempt fsync 或等待 start 回复，此时活动被取消。稿件未明确此时仍由谁通知原根，也未定义何时从“本次未完成调用负责收尾”切换为“预算根按原 total 自持”。

若以 `owner_confirmed` 为豁免条件，只停止短 H／取消 poll task，独立兄弟根仍可能运行至 compute 尽，已发送 RPC 也可晚到；若这同时被用作总 controller 取消的全部处理，则缺少原本要求的停止通知。若为补洞而在任意 observer cancellation 都 TERM 根，则成功交接后 worker 正常 loop 收尾也会误停应跨重启存活的 owner。原 `_CycleOperation.run` 只拥有它自己的 S-H，无法自动决定新增兄弟根应当自持还是接收整个 cycle 的停止请求。

最小行动：在原 worker 的该次调用内明确交接点及取消触发的区别。可以选择“收到同一完整 owner 确认即交接”：交接前失败／取消仍先收尾实际 S-H，再向精确原根 TERM 并保留真实等待与 unknown；交接后普通单操作取消／worker teardown 只收尾 S-H 或停止观察，根按原 total 自持。但总 controller 取消／用户 stop 必须另走原独立 b2b 用例的父 veto、精确 owner 通知、排空和执行链观察，不能仅取消普通活动，也不能将该后继消费者记为已经交付。确认回复丢失仍按未交接处理，不再次 spawn。进程崩溃无法补做通知时仍只按原身份／clock 对账。不得为此新增持久 running／handoff 账本，也不得统一取消此前已接受的轮次。

最小验证：沿真实 orchestrator，在 owner 确认之后分别卡住 dispatch lookup、attempt 同步及 SDK start 回复，区分普通单操作取消与总 stop，核实际 H 回收、是否应当发送的精确通知、原根／原子树的独立停止事实及 attempt 不重发；另在已交接后关闭真实父 loop／解释器，核同一预算根继续按原 clock 存活。仅验证确认前取消不能关闭本 finding。

### R2 · P1：已有活 owner 且没有 start attempt 时，恢复动作与一次窗口的封套未闭合

位置：本片计划第 35、37、39–43 行。实际接口见 [training](../../src/ergora/training.py) 第 270–305 行、[submission](../../src/ergora/reference_training_submission.py) 第 331–369 行、[worker](../../src/ergora/reference_training_worker.py) 第 30–53 行及 [protocol](../../src/ergora/training_execution_protocol.py) 第 170–269 行。

稿件一方面允许“已有确认 owner 则使用该 owner”，另一方面称 worker 重启后“只查”原 owner／start／receipt；没有说明下列具体状态属于哪一边：prepare 成功、根已确认，进程在写 child attempt 前退出。原 `_Submission.run('resume')` 在没有 attempt 时会进入 `dispatch`，不是只读恢复；`training._submission` 的 prepare-resume／resume 组合保留同样行为。直接复用该入口会把观察恢复变成新副作用。

同时，现 `_CycleOperation` 每次构造都会为普通 mode 生成新的 bootstrap，identity 不含完整 controller，ordinal 仅允许 notify／observe，validator 也不认识本片所需阶段。故“多 H 与根传送共享同一窗口”不能由现接口自然保证。prepare 耗尽接近 control timeout、确认和 dispatch 各自新建 operation 时，若仅扩 mode 列表，可能得到多个 control 窗口；重启再走原 resume 则有相同风险。原 compute／total 仍不续期，不能替代本次 control 截止。

最小行动：实施前在原协议 owner 固定一张本片 mode／字段／结果表及恢复动作表。明确已有活 owner、无 attempt 的状态：同一次仍活调用只有携带最初窗口才能接续 dispatch；失联后的只读恢复不得意外调用原 resume 的无 attempt 分支，若选择其他策略须明确其原授权与窗口依据。首次调用持有一个权威 window，后续 H 和根传送消费它，不能由各阶段构造器重算。表中同时固定完整 controller／ordinal、唯一 offer 对原请求身份及 parent 的绑定、确认阶段对新 spawn 的完整 PID／start_ticks／boot 与原 owner 记录的对应，以及 confirmed／new-offer／unknown 各自必需字段；不要求反复回传已由原请求持有的同一值。缺字段不得退化为原手工 launcher。

这只需现有 worker 私有编排及 stdlib validator 的窄分支，不需新的通用操作框架、进程 host 或持久账本。原 schema1 行为与既有 mode 封套应直接保持。

最小验证：沿原接缝分别恢复“intent 有／owner 无”“owner 活／attempt 无”“attempt 有／receipt 无”，观察实际 SDK start 次数及是否发生 Popen；制造 prepare、确认、dispatch 的累计延迟，验证它们只消耗最初窗口；重复调用、进程重启与迟到确认均不得获得新 offer 或借阶段重建窗口。确认与 dispatch 之间替换／损坏／结束原 owner 时，最后点仍拒绝且不补启。

## 必要性、职责与证据判断

|问题|独立判断|
|---|---|
|为何需要改进程归属|必要。原短 H 调用 start 后，长期根仍是 S 的后代；原 `processes.run` 第 155、182–194 行设置 subreaper 并回收剩余后代。`start_new_session` 不改变祖先关系。把根置为 S 的兄弟可保留原唯一 reaper，不能给 reaper 加豁免。|
|唯一 `created=True` 是否足够|对准备稿选择的 fail-closed 一次 offer 足够。原 `.lock` 内只有首次 immutable intent 发布者得到 true；原 core.write 同步文件后 link，补原目录 fsync 后才能发完整回复。并发后到者、丢回复、部分回复或创建失败均不再发 offer，代价是允许留下永远未启动的 intent。无需另建 launch.request／状态账本；日志不得反过来授启动权。|
|启动失败与重启|不恢复 offer 是安全且清楚的取舍。已确认根只沿同一 owner／原记录观察；owner 缺失、损坏、变身份或 final 不允许 Popen。已有根无 attempt 的副作用恢复须按 R2 明确。|
|existing-only 的位置|必须在实际 `_Submission.dispatch` 调用 `ensure_owner` 的最后路径落实；早前 H 的一次 alive 结果不能代替它。原 attempt 前后 `require_active(owner=True)`、父共享许可与固定 RUNNING history gate 仍需保留。|
|线程与隔离|窄线程仅创建 OS 进程可接受，返回的是 Popen；预算、State、业务文件／锁及原阶段执行仍在原进程边界。不能把它解释为业务线程隔离。SDK 父 loop 不装载 State、不打开业务日志、不重建配置。|
|职责与抽象|从 `training._submission` 提取原短 prepare 阶段、预算 owner 自持初始化／日志、worker 持一次 spawn 和公开 pipe 句柄，方向内聚。当前没有新增公共文件／框架或重复账本的必要性；R2 的合同应留在已 pin 的 owner，勿由多个活动各自拼装。|
|性能判断|没有新的性能收益主张可验收。非阻塞 pipe／poll 与一次 OS 创建线程能避免把整个训练寿命放进 default executor；不得使用长期 `to_thread(wait/communicate)`。有限候选与一次 offer 已提供容量边界，不需要为此新增调度层。|

仍须保留一个明确限制：Popen 自身尚未返回时，shield 只能保留 future，不能中断 OS 创建；正常 Runner 收尾会等待 default executor。既有惰性测试只覆盖创建已完成后的退出，不能证明启动卡住时正常服务重启仍有界。本轮不把该已记录限制视作“线程承载业务”的问题，也不要求推测性的 launcher 框架；后继须用实际 pending-thread 接缝核晚到句柄、窗口已尽后的拒绝与收尾，并准确限定正常退出保证。

## 实证核对与测试价值

本 reviewer 读取并重算了既有原件摘要，没有重跑探针或产品 suite：

- 实际安装 reaper r2 的脚本 SHA256 `c7a8331e17284133b9d83957eecbeb0b59a3d8db92266fb6157c70e3c3b8ba9a`，结果 SHA256 `9cfc63071d72c867fbb8ca05ac180231ed9789450371fe0cf6d9805667ab4df3`。记录 0.581511 秒：H 的惰性 session 后代已失活；兄弟惰性根在另一次 S 收尾后仍活，最终 TERM／wait `-15`。r1 的 proc 消失观察错误与未启动兄弟 case 的原失败保留。
- stdlib lifecycle r2 的脚本／结果 SHA256 分别为 `1efc8567fb698ddde471b5e06bb58daa8a355bd2b9c9686b3450a1c4c01e560a`／`05635ba5a1adad2019852d196dc59db5f5e8b2283f7315cd7f6a513598429ffe`。六 case 共 1.468694 秒、无 probe_error；async 与 Popen 根在各自正常退出或父 SIGKILL 后均仍活，六根最终 TERM／wait `-15` 且 proc 消失。async transport 的 close／析构有 kill、无公开 detach；本机 ThreadedChildWatcher 的存活观察不能反写为“必 kill”或通用保证。
- r1 pidfd 包装缺席的恢复 JSON SHA256 `8f288612c501403f697427a86b0780932d6b4008cbe7b09e305d796728218b24`；原身份 TERM 后 proc 消失。恢复者不是父进程，原件未称执行 wait。
- SDK r4 `probe.py` SHA256 `6870ceb0bcd9cdd1b4b7590a33c31c31fd9b0a88b6ce17b4e0f0150d2e9a2af6` 与原结果一致：SDK 1.34.0、公共标准 sandbox 的本地准备／activation；两 Worker 的 Python 构造替换 bridge create，connect 为 0、Worker.run 未调用。core 原件确认 SDK 缺席且原 worker 可导入。它们不能认证真实 queue／stop 配额。生命周期索引记录的七份产品 source SHA 均与本次读取一致。

本片产品检查应复用 `tests/test_training_submission.py` 的 `cycle_selection`／`controller_admission`／service 和既有 cycle-operation／budget fixture，保留真正的 `BudgetedStart.own`、owner 锁和原 S-H reaper。现有 cancellation 测试第 3102 行只拦截原 async S spawn，不能替代新 to_thread 根启动的 pending-handle 检查。新增价值在真实序列：跨多个 H、确认前后取消、回复丢失、并发、父正常退出／崩溃、同一原 clock 和 owner 最后收尾；只验 argv、mode 字面量或 helper 返回字段没有这些保护。

本轮未安装、启服务、训练、提交、推送或运行昂贵 suite。静态摘要与源码检查不构成 b1.1–b1.4 通过。R1／R2 关闭后仍须新的独立产品审查；c1b2 两个真实服务进程和 normal／stop 配额必须先于自动派发，c1d 的 accepted archive／实际 phase／durable stopped／完整 rounds 门槛保持。原六阶段、出生同意、不可续期 clock、非归还 start／native launch、原证据与人工 release、283 冻结、source key 集合、唯一 reaper 及 kernel 专家 v3 均不能由本设计审查替代或放宽。

## r2 复核：2026-11-15

同一独立 reviewer 复核修正，范围为私有 `design-scope-r2.json`、`design-snapshot-r2/` 七份完整文档与 `design-tracked-r2.diff`，源码仍为 `f00bfdfd15173ceb0e961681679d6d3d62254bed`。本轮只修改本文，不补写产品。七份快照的字节数／SHA256逐一匹配 manifest，读取时正文均与快照相同。主计划 SHA256 `2c4f92d625623937afe408fb70e2eae80e4fc704cd8ecdd952cabc505afb9fc2`，交付 SHA256 `76d199ab4dcf3f1f804ec3b4614dff3ee489aea04b27748ae1c6748008c01bec`；研究仍为原最终 SHA。r1 报告完整原件已以 SHA256 `3def78c2d8d4583c3e6565c2e51f777cf045878362b737c8d8d27bf964fd5bdb` 保存在 r2 快照，本页前述发现保留为历史结果。

**r2 设计结论：需求符合性 approve；可维护性 approve；开放需求／维护性 finding 为 0／0。** 在本次具体设计范围内未发现新增阻断项，可以按计划进入 b1.1 实施。该结论只关闭设计合同缺口，不认证现有源码已经提供新 mode、schema2 existing-only 或跨调用生命周期。

|原 finding|r2 原文与实际 caller 的复核|处置|
|---|---|---|
|R1 交接／取消责任|主计划第 41–42 行以调用方收到完整匹配确认作为交接点，明确确认丢回复仍未交接；此前先收尾 S-H 再精确 TERM／真实 wait 根，此后普通活动异常／取消／unknown及正常 loop 收尾只清理本次 S-H。总 controller 取消／用户 stop 单独调用原 b2b veto／逐 owner 通知／drain／执行链观察，并明确 c1c 消费者尚不存在。实际 `stop_live_controller` 第 350–379 行已有独立 writer、drain 与逐目标分支；普通 `_CycleOperation.run` 不会被当成该总停止过程。确认后 lookup／attempt 同步／SDK 回复三窗口列入验收。|设计层关闭。完整确认即交接是可行的责任选择，不能把总 stop 的剩余义务转成普通 task cancellation 或提前宣称已交付。|
|R2 恢复／共享窗口封套|主计划第 46–61 行固定四个新 mode 的 start_context、完整 controller／ordinal、root request／环境／确认记录以及结果必需字段；首 prepare 的 id／parent／bootstrap 是该次调用权威。后续 H、root bootstrap 与原 submission 最后点重读原 operation 请求核完整来源及同一窗口。第 63–72 行明确新调用遇活 owner 无 attempt 仅观察；有 attempt 时直接调用原 reconcile，不进入原 `_Submission.run` 第 366–369 行可能 dispatch 的 resume 分支。原 start_workflow 前置 lookup及 attempt 同步之后也校验最初窗口。|设计层关闭。现 constructor 每阶段重算窗口及原 resume 的副作用分支均被明确迁移，不能直接沿用旧默认行为。|

复用原 operation 的既存 `request.json` 作为完整来源校验，未增加第二份启动／交接账本；它不恢复 `created=True` 的一次内存 offer。root 的新协议是原 budget 入口的窄初始化合同，初始化日志和环境仍归 budget owner；应用＋选定 native PYTHONPATH 明确保留。新增普通操作校验不被套到之后 budget worker／native 的独立生命周期，也不改变 schema1。当前职责划分与依赖方向可在既有已 pin 文件内承载，无需新增通用 host 或调度抽象。

本轮重新检查全部七文档的 218 个本地链接，缺失 0；`git diff` 对产品路径仍为空，283 个 tracked reference 文件及 `GATE_SOURCES` 原 key 集合保持。PLAN 新增 BR1／BR2 并行排期只作独立任务记账，不纳入 c1b 产品结论。未重跑原 SDK／stdlib／reaper probe，未运行产品 suite或安装。

后继产品验收仍须观察真实行为：新 validator 对旧／新封套的边界；唯一 offer 的并发／丢回复；晚到 Popen 句柄在窗口已尽后的拒绝与真实收尾；多 H 累计消费同一窗口；确认后普通取消与总 stop 的区别；无 attempt／有 attempt 恢复的实际 Popen／SDK 次数；schema2 最后点 existing-only；真实原 owner 同一 PID／start_ticks／boot／clock 跨 S-H 及父正常退出／崩溃存活，最后仍沿原阶段与唯一 reaper 收尾。创建本身卡住时 default executor 退出不保证有界，是明确保留的支持限制。core／SDK 非 editable 安装、源码身份、283／依赖、SDK-free 读取及新的独立产品审查仍待 b1.4；真实双服务／stop 配额仍待 c1b2，自动派发和后继轮门槛不提前开放。

## 固定本地提交身份核验：2026-11-15

本追加保留此前 r1／r2 审查全文为不变的 19,038B 前缀，SHA256 `e5e986722e5039a2811f48be603f96f1c7b8461a484da66edb6160e8bc39ecc0`；它与本次固定提交中的报告字节完全相同。原 r1 准备稿及 r2 快照继续保留各自身份。

同一 reviewer 直接读取 Git 对象、`design-local-commit-r1.json`、`design-final-r3.json`／`design-final-r3/` 和 `design-commit-r1.stdout/.stderr`。当前分支为 `refactor/architecture-foundations`，固定提交为 **`4d060ae8609424cc2f6f5f0b44393da7e2ba03f7`**，唯一父提交为 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，tree 为 `1fcb49ffd706d7be6be0862adc56a186cd26c10f`。实际完整变更范围恰为 manifest 的 13 份 docs 文件；其记录 blob ID 与提交 tree、核验时 index 逐一相同，提交原始字节／SHA256／字节数与最终快照、核验时工作树均一致。

本片主计划相对已审 r2 仅将 b1.0 状态改为已获独立设计 approve；交付追加对应闭合记录，PLAN 同步该状态。主计划的 mode／交接／窗口／恢复合同没有改变，b1.1–b1.4 仍明确未实施。研究与父 workflow 文档保持已核正文。提交中的原 c1a2／b2b0／b2b 审查报告只追加各自固定提交／发布／准确 CI 的状态记录；本轮核其差异范围与完整字节，没有重复认证这些片的远端原件或继承其产品结论。新增 BR1／BR2 计划／交付及 WA1–WA5 计划属于独立任务排期，明确未合入、待审计／讨论或待验，未把未来能力写成本片已支持。

从父提交到固定提交，全部非 docs 路径零差异；283 个 tracked reference 文件和原 `GATE_SOURCES` key 集合保持。直接检查提交十三份文档的 229 个本地链接，缺失 0；提交 diff 空白检查通过。本轮没有重跑探针、产品 suite、安装、服务或训练，没有提交或推送；本次唯一变更是报告末尾的身份追加。

**固定本地提交的需求符合性／可维护性两轴均 approve，开放 0／0。** 该结论确认已审 r2 设计与固定提交的同一性，允许以准确 `4d060ae` 作为 b1.1 实施基线；R1／R2 仍只在设计层关闭。普通发布仍在原队列，本候选自己的远端发布／准确 CI 未获本轮结论；实际预算 owner、取消／重启／恢复、新安装、独立服务与配额等产品验收继续待后继，不由本次文档提交替代。
