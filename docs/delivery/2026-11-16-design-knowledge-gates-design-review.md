# WA5a／WA5b：设计与必要知识关卡独立设计审查

2026-11-16。审查者：fresh-context agent `/root/wa5_design_fresh_review`，同片复核仍由本 reviewer 执行。本片只审设计及验收接缝，只新增／更新本报告；没有修改产品、测试、模板、CI、原参考、PLAN 或其他交付。没有运行测试、安装、服务、网络、模型或训练，没有读取凭据。

**当前 r2 需求符合性：approve；可维护性：approve；开放 finding：0。** 首稿的 request-changes、R1／R2 原 finding 保留于第 2 节，r2 定向复核及关闭依据见第 5 节。原 owner、版本隔离和共享纯合同的方向可保留。这里没有发现或声称已实测的现产品绕过；新 runtime 尚未实施，本文不授予任何 task／candidate 执行权。

## 1. 固定输入与审查身份

|输入|本次核对|
|---|---|
|当前 r2 完整设计|[2026-11-16-design-knowledge-gates.md](../plans/2026-11-16-design-knowledge-gates.md)，265 行／55,534B，SHA256 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`。|
|首稿身份|238 行／48,196B，SHA256 `85e56e7096667ff44f3ef9441b6f5b85084b5431fe8ab37466068bba4ce6eb4a`；首轮结论为需求 request-changes、维护性 approve。|
|源码基线|设计声明 `debf6f96ed02620d22adc0ac6385c72641b3d53b`；本次实际 HEAD `562394c839e9353e4f889a0b03e749ca32783936`，二者 `src` Git tree 均为 `4065d54f8155b5b1db2a94bc558b7d670c09c604`，提交间差异均为 docs。|
|原始要求与用户决定|完整读取[原始要求](../plans/2026-11-15-workflow-evidence-and-human-gates.md)、[WA4](../plans/2026-11-15-workflow-design-and-execution-evolution.md)、[D1–D4 原答复](2026-11-16-workflow-design-decisions.md)，以及设计开头所链 WA1／WA2／WA3 三份审计。D1–D4 是已确认方向，不是运行材料批准；本报告不重开这些产品问题。|
|适用规则|根、src、tests 的 AGENTS；[组件协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 及 independent-review；`ergora-codebase-quality` 的 module-design／test-seams。|
|并行工作|开始时另有 M5/native 交付及 `scripts/ci/linux-groups.json` 的在途差异与新报告；全部保持只读，不借用其未验结果认证本设计。|

直接核了 `tasks`、`reference`、`reference_creation_process`、`reference_task_creation`、`task_envelopes`、`reference_inputs`、`reference_workflows`、`reference_task_approval`、`reference_task_cancellation`、`reference_executor`、`reference_job_lifecycle`、`processes`、`registrations`、`state` 的相关生产路径，以及原 DevelopmentWorkflow／Activities／FileAdapter／Executor／registry 和 CLI／HTTP／console 入口。测试仅静态阅读相关 fixture 和断言，不将历史通过转记为本轮结果。

## 2. 首稿 finding，r2 已关闭

本节保留首轮审查的事实、风险与最小纠正；以下设计行号是首稿行号，当前修订的准确位置及处置见第 5 节，不能将本节的历史描述当成 r2 仍存在的缺口。

### R1／P1：G1 缺少取得冻结 design policy 的具体可信数据路径

位置：[设计第 129 行](../plans/2026-11-16-design-knowledge-gates.md#L129)，关联第 41、115、126、170–173 行。

设计要求 `DesignAdapter.authorize` 在原 authorize 内独立核完整材料、ready、owner、seal、失效和原预算，同时让 `DesignWorkflow` 只注册新类型、继承原 run。但原 [DevelopmentWorkflow.approval 第 133 行](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/workflow.py#L133) 交给 `dev_authorize_plan` 的 context 只有 `task_id/request_sha256/profile_sha256/plan_sha256/receipt_id`；它没有 admission、design profile、owner policy 或 budget。原 [Activities.authorize](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/activities.py#L73) 原样传给 adapter，原 [FileAdapter.authorize](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py#L170) 只读所指 receipt。现 adapter 的配置也只声明原五个可信 root。

因此，按列出的继承接法，G1 并不会自动得到 v12 冻结 policy。可达情形是：原 plan admission 中 Q1 必答，但所指 receipt／packet 自报另一份更宽 policy 或 owner binding；只校验这些材料彼此的摘要不足以证明它们等于原 admission。反过来，一律因缺 admission 拒绝也会使合法新任务无法通过 G1。G2 已承诺从 published input 再核，可阻止后续业务，但它不能替 G1 证明这次批准是在同一冻结要求下被接受。

最小纠正：在设计中明确一个原件加载合同及其调用者。例如由 v12 adapter 从**本版本 requests root 中固定 plan job ID**读原 envelope，再核 task/request/profile、job context SHA、seed receipt SHA和完整 admission identity，取得冻结 design profile／owner／budget；同样明确 journal／seal 的可信 root 和读取权限。也可选择在自有 v12 Workflow 的最窄控制调用处补上已冻结 admission，但不能从 approval JSON 的自报字段或当前项目 head 推导它。保留原 run、原 plan receipt 和纯就绪规则，不需要复制六阶段或新服务。

验收补充：经真正的 `approval → dev_authorize_plan → DesignAdapter` 调用，构造“receipt／packet 内部自洽，但 design policy 或 owner 与原 plan envelope 不同”的反例；G1 必须拒绝，合法原件必须可接受。单独向 `validate_packet` 传入正确 policy 的 helper 测试看不到这条缺失路径。测试仍属受控 activity/native 接缝，真实服务另验。

### R2／P1：本地决定 commit 后、fence／cancel 前的恢复没有闭合

位置：[设计第 107 行](../plans/2026-11-16-design-knowledge-gates.md#L107)，关联第 148–150、160、201 行。

§5.1 把 reject／withdraw 列为同一组 operation，并规定不可变 `.result.json` 发布才构成本地提交、同 ID 同完整内容只读回原结果；§6 又要求本地决定后写原 fence，再关联原 cancellation intent／发送 cancel。尚未规定这项 stop 副作用的固定 child request ID／完整 intent binding、各持久步骤的顺序，以及已存在本地 result 时 `resume` 怎样继续未完成的尾部。

可达窗口是：withdraw 决定及本地 result 已写，进程在 fence 或 cancellation intent 写入前退出。按当前“同 ID 只读回结果”规则，重复请求只能读到决定；原 cancellation owner 此时没有 intent 可供恢复。不能把“本地已记录 withdraw”当成原 fence 已持久可见，也不能用新 operation ID 补发来回避旧操作。G2 可以压制尚未准入的后继，但已准入的 stage 不会仅因 journal 文本而被原 `stop_requested` 观察：该 [原 supervisor](../../src/ergora/reference_job_lifecycle.py#L117) 读取的是原 fence、取消和预算。在原剩余预算内，在途业务可能继续。

原 [_Cancellation.run](../../src/ergora/reference_task_cancellation.py#L143) 本身也会取得同一个 creation lock，且 attempt 后只对账。因此不能在持有该锁时再嵌套调用其完整入口；“释放 admission lock 后发 cancel”尚不足以说明这个交接。

最小纠正：在原 design operation intent 内固定对应的原 cancel request ID／run／reason／身份引用；区分“本地决定已提交”和“停止副作用的观测状态”。明确同 ID／同 intent 的 resume 即使看到本地 result，仍检查并继续缺失的原 fence／cancel 准备步骤；沿原取消 intent／attempt／result 推导 stop 状态，attempt 后只对账，不另建停止控制器。固定 creation→admission 的锁序，并在原 cancellation 入口重新取锁前释放外层 creation lock，或复用原 owner 内明确不重复取锁的最窄局部步骤。只有 fence 持久可见才能报告本设计定义的撤回线性化点，实际停止仍需原 reaping 见证。

验收补充：在“本地 result 后、fence 前”和“fence 后、原 cancel intent／attempt 前”分别中断；用同 operation ID／原 intent 恢复，原 fence 必须保持、cancel 只能沿一个固定请求前进。再覆盖 cancel attempt 后丢回复不重发，并用原实际 process fixture观察在途 stage 停止。这是 design journal→原 cancellation→job supervisor 的跨 owner 风险，不能仅测 source publish 崩溃或各自已有的取消恢复。

## 3. 其余设计核对与维护性结论

|方面|静态结论与边界|
|---|---|
|需求与范围|设计覆盖调研采用、详细方案、规范／取舍、客观验收、实施顺序、必要公司资料、逐题原答复及明确例外；ready 与 approved、产品方向与运行批准分开。沉默／页面关闭不产生批准。没有把一般 Repeat、可信非 Agent 节点或训练后继隐含实施。|
|seed／revision／材料|原 plan 一次执行、job ID 按 stage 固定、run 持局部 plan 的事实核对成立。packet 不含承载它的 receipt SHA，最终材料再绑定 seed，避免把 receipt 自身纳入其产物摘要。答复／resolution／来源与正文分轴版本化，完整材料变化重批，批准后改材料走新授权 task 的保守规则已明确。实际 schema／序列化仍未实现。|
|版本／旧 writer|definition8、input12、companion profile 与 native profile 各轴分开；`_INPUTS` 是实际工厂，旧路径无需新具体类型分派。State6 只换 writer fence 有真实持久语义理由；旧 journal／文件需要各自版本读取，SQLite 迁移不能代替它们。具体兼容与备份恢复待实现证据。|
|真实材料消费者|Executor 在原构造中先 `require_job_owner`，原 work/review producer比较完整 approved_plan；`_composition_request` 和 saved formal-call 有真实材料／恢复接缝。设计已点名需要扩结果 schema及 `_declared_results`，不能仅改页面或落 journal。新完整正文投递及容量尚未证明。|
|进程停止|原 `processes.run` 的 should_stop 与 Popen 之间确无共享锁；方案没有假称已具原子准入。stage body 短锁、共享原 fence、旧 input 空 guard、保留 collection／cleanup、在途子树用原 supervisor／reaper，责任位置合理。R2 闭合后仍需实际并发／回收证据。|
|可信 human|原 Unix actor 和 confirm 不能证明自然人；HTTP 请求头也不能。方案要求报告 assurance，并在 Agent 能写 receipt 卷或共享无隔离身份时保持 v12 关闭，符合原 FileAdapter 的 ACL 信任前提。这里没有验证任何部署 ACL、组织身份或真实 owner 通道。|
|抽象与文件归属|`task_design` 计划隐藏三个真实批准／执行消费者都要承担的引用、例外及就绪规则；本地链提交仍在原 approval owner。Input 的构造／材料／job guard 方法是已有多版本契约的扩展，process 可选 guard 位于真实 Popen owner。没有单 caller 通用平台、第二调度器或万能服务的必要性。|
|测试价值|计划优先原 task／composition／budget／process fixture，明确受控 SDK与真实服务、源码与安装、测试替身与真实权限的差别，方向合适。`test_task_approval` 的 SDK fixture和 composition executor 的原 subprocess fixture是真接缝；console 现有静态断言不认证 DOM交互，最终小旅程仍须真实观察。补 R1／R2 两项后不需为本设计文档新增测试框架或昂贵测试。|

可维护性 approve 只针对这份设计的 owner／依赖／抽象／验证分片方向，不代表实现质量已过。首稿 R1／R2 的需求缺口现已按第 5 节关闭；两项纠正属于技术合同补齐，不需要用户重答 D1–D4。若后继引入新的产品取舍或扩大授权，仍需按原规则明确记录。

## 4. 本次检查与后续证据

实际执行仅为本地只读命令：Git status／HEAD／基线文件列表与 `src` tree 比较、设计 SHA／行数／字节数、`rg` 定位及分段源码／文档阅读；报告完成时检查本报告相对链接及空白。没有运行设计表中任何产品验收。

本报告未验证：任何 v12 schema／writer migration／source journal 的实现；G1/G2 的真实阻断；完整 packet 及全部正文在原容量内的投递；新非 editable 包；原模板真实调用；Temporal 服务重启／丢回复；stage 启动与撤回竞态；实际后代回收；真实 owner 权限隔离及两轮人类旅程。新模板默认、公开交互、发布及候选自己的 CI 也仍是后续各片责任。

## 5. r2 同片定向复核

复核输入为上表 r2 完整设计，HEAD／`src` tree 与首轮同一。直接重读 §5.1、§5.3.1、§6.1 及相邻 G2／锁序／验收描述，并再次对照原 FileAdapter 的 roots／verify_receipt／publish／fence、DevelopmentWorkflow 的 authorize context、Input factory，以及 `_Cancellation.record/load/run/dispatch/reconcile`。没有以作者的修订说明替代源码核对，没有运行产品验收。

|Finding|r2 处置与独立核对|结论|
|---|---|---|
|R1／G1 冻结 policy 来源|[§5.3.1](../plans/2026-11-16-design-knowledge-gates.md#L134) 明确原 authorize context 不带 admission，按可信配置／注册布局选择 v12 requests root，再按原 stage 算法取得固定 plan envelope；由 job context SHA、完整 v12 admission、request/profile 和原 seed receipt 共同绑定实际等待的 plan。冻结 design policy／owner／budget 只从这份 admission 取，材料与源链逐项比较；journal／锁从同一受信 state 布局推导，缺 ACL／身份隔离继续关闭。原文件与 factory 足以承载这条读取路径，无需修改原 run。新增真正 activity 中宽 policy／owner 替换反例，能观察首轮指出的风险。|关闭，设计合同足够；实际装载、容量、权限及拒绝效果仍待实现验收。|
|R2／决定提交后的停止尾部|[§5.1](../plans/2026-11-16-design-knowledge-gates.md#L109) 排除 stop operation 的提前读回；[§6.1](../plans/2026-11-16-design-knowledge-gates.md#L177) 在父 intent 内固定唯一原 cancel ID／完整 child record／SHA，避免反向摘要循环。即使本地 result 已存在，同 ID mutation／resume 仍继续 fence 和原 cancel；GET 只读。先持久确认原 fence，再释放 admission 与 creation 外锁，由原 cancellation 自行取锁；完整 child 原件核对、actor 漂移时保留 fence、attempt 后只 reconcile，与现 owner 的机制相容。原 publish 仅 fsync 临时文件的限制已明确，新增同文件／父目录持久确认，不冒称实际进程已停。两处跨 owner 崩溃窗口及实际 process／锁交接验收已纳入。|关闭，设计合同足够；实际 fsync、并发、取消恢复及 reaping 仍待实现验收。|

本轮没有新增范围内 finding。当前需求与维护性两轴 approve、开放 0；这是静态设计及验收方案的结论，完整未验范围仍以第 4 节为准。后继由主控按实际授权确定实现片；本报告不批准实现、运行任务或发布。
