# c1d M1b schema3 storage birth：独立设计审查

2026-11-16。Reviewer：fresh-context 独立代理 `cycle_v3_birth_design_review`；未参与方案编写或 M1a 实施。本片采用 `maintainable-project-delivery` 的 independent-review brief，以及 `ergora-codebase-quality` 的 repository-style、module-design、test-seams。仅作静态设计审查，本报告是唯一写入。

**需求轴 approve／阻断0；维护性轴 approve／阻断0。** 结论仅认可将 M1b 明确修订为内部显式 schema3 出生、历史读取和本地 controller intent 准备的完整小片；不是原父计划全部出生／V2 接线已经完成，也不是产品或测试通过。未发现所查设计范围内可达的新执行绕过。下列 D1 是非阻断的调用顺序表述修正。是否接纳这项阶段修订及更新活动计划由主控记录；本审不自行改变冻结父合同，不开放 ordinal1。

## 准确对象与原始约束

|对象|独立核得身份|
|---|---|
|[M1b 草案](../plans/2026-11-16-training-cycle-v3-birth.md)|8,157B；raw SHA256 `6e2b8552ac140cb1fe87f45e1cc02390cf8fbddf32ae4dbe2d180e5467b084d7`|
|[已审 wire](../plans/2026-11-16-training-cycle-measurement-wire.md)|raw SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|主树最初源码基线|`refactor/architecture-foundations`，`fa2fd17620192ac1341a72f1050dc37faaee623f`|
|基线 `training_cycles.py`|raw SHA256 `07215a1b1b1876c462333154ef834ef73f2a3b6020703270bfb3395c084f5972`|
|基线 `training_execution_protocol.py`|raw SHA256 `b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|基线 `reference_training_runtime.py`|raw SHA256 `1183a95c53a9550789983e245676a46637b5de748ddf32eb0ec5df9def46458a`|
|基线 `reference_training_budget.py`|raw SHA256 `d002c88e79bc3d856c86415511d307636d4a11698168ece6100e18824b149d4e`|
|基线 `reference_training_worker.py`|raw SHA256 `7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`|

先读根、源码和 tests 的 AGENTS，PLAN 当前检查点、组件变更协议、原始 measurement-and-index 计划及 wire 全部相关合同，再核实际 owner/caller/fixture。已读 c1c 最终独立审查与首轮交付；其准确最终源码、安装、现场和资源证据只保留原认证范围，没有用它认证 schema3。最初 Git 状态已有他人的 PLAN／c1c 文档和未跟踪 M1a／M1b 文档，均未修改。

审查期间共享主树切至 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`。已用 `git show fa2fd176…:<path>` 重新固定相关版本分支和 native 调用顺序，并核两提交差异仅为 M1a 的 protocol／rounds／evidence tests 三文件。这里记录这种变动以免混淆行号；未读取 M1a 的审查结论作为本片批准，也没有认证该提交。实施前仍须重核实际已接纳的 M1a 字节与新的产品基线。

原始要求是保留六阶段、祖先资源和原权限、candidate-bound evidence、原 accepted archive/gate 与 baseline；unknown 只对账、不重授效果；各轮共用一个不可续原 BOOT 预算。schema1/2 和 c1c 历史永久只首轮。最终只有新 schema3／正式 V2 在 accepted evidence、完整前缀和最后 native gates 均通过后才能续轮。当前小片不实现接受、collect、最后前驱准入或 V2，不把这些必要后继职责改成可选项。

## 真实可达边界

|入口／原源码证据（行号按 fa2fd176）|设计判断与本片停点|
|---|---|
|`training_cycles.authorize_controller:493 → _authorize:501`；`_authorization:223`、`_controller:246`|原 writer 已拥有唯一 ID、完整 input／project／registration、clock、link/fsync、ready 与丢回复恢复。增加精确 `program_version` 选择比另设 writer 更小；省略／int1 保持 schema2，int2 才是 schema3，bool 拒绝。碰撞必须比精确 schema，而非旧的 boolean controller 判断。|
|`_load:255`、`_status:314`、`CycleAdmission:544`、`prepare_controller:400`|schema3 可复用普通空父锁、不可逆 stop、严格原 intent 和 submission reader。ready 的覆盖仍为 `execution_authorized=false`。历史 map 仅核固定键、digest 形状及完整授权 SHA；当前 source 漂移不能让 status 丢失原记录。准备／恢复 intent 则比较原四项 source，并消费原预算。|
|`_claim_controller:444 → _controller_ready:436`|schema3 在后者拒绝，故直接调用原 claim 也不能发布新 attempt。仅限制正常 H 不足以覆盖这个内部原发布入口；计划已列出此门。|
|worker `_cycle_operation:486`；protocol `validate_cycle_operation:229`|原 validator 的冷 `inspect` 在 snapshot/schema2 校验前返回，随后 H 会实际装载授权。只保留 schema2 snapshot 门不能关闭 schema3 冷 H。计划在 H 装载及精确授权 SHA 后、activity binding／SDK／各 mode 分派之前拒绝 schema3，覆盖真实绕过分支；本地 stop 仍由原 storage API 提供。|
|`training_cycles.start:386 → training.start → _prepare_submission → budgets.prepare_binding → require_active → BudgetedStart.source:258`|原 prepare binding 在发布候选 intent 前即核 source。schema3 source 门放在 manual/controller 选择前，能同时关闭 omitted-controller 的手工路径及 controller 路径；submission 无须再认识一种授权版本。|
|worker `BudgetAdapter.create_job_if_absent/lookup_job:1139`|手工旧分支允许返回已经存在的 job；只有 absent job 才在原锁内走 budget source。因此本片应保留已有只读／幂等返回语义，对 schema3 不得产生新 job。计划没有理由全局改写旧 native adapter。|
|`Execution.check/current`、protocol `validate_context:975`、`native_main:1024` 与原 native admission patch|原 execution 在 actor 选择／RPC前消费 context。native 的 callback 也在 executor 写 started、managed attempt/ack 或运行 runner 前消费 context。schema3 在 context 的 manual/controller 分派前明确拒绝，可以关闭训练效果；外层调用顺序的文档精度见 D1。|
|`_controller_owner:1844 → cycle_start_source:383 → validate_cycle_operation`|root 启动入口仍经原 schema2 snapshot 与 operation-v1，不能由新本地 schema3 intent 获得 root／capability。保留原 owner schema1/2 和 25-key capability 的精确合同正确；授权 schema3 不意味着 owner schema3。|
|runtime `_controller_history:69`／`lookup_controller_submission:89` 与 worker `_dispatch_controller:866`|一个封闭 protocol→type 函数有 runtime、worker 两个实际生产文件消费者。按精确 protocol 选择名字，保留 input／memo／queue 和 fixed first/original run／attempt1 的原认证，无须 stub class 或注册。对 v2 仅可做 read-only 身份认证；生产 H 和 claim 已关闭，映射本身不使 V2 可运行。|

这些关闭点各保护不同的外部入口／持久分支，并非重复堆叠同一正常路径校验。它们允许本片完整交付一个可读、可停止、可准备但不可执行的新存储身份；不要求将 M1c/M2/M3/M5/M6 偷渡进本片。旧 `successor_not_enabled`、v1 类及旧活动的 command 语义必须原样保留。

## D1 — P3，非阻断：native 外层 permission 分支的描述不准确

位置：[M1b 第53行](../plans/2026-11-16-training-cycle-v3-birth.md#L53)，关联第65行验证。

草案说保留 schema2 分支，并由 source/context “preventing … parent-permission skip”。实际 `native_main:1084` 是 `validate_context(...) if schema_version == 2 else None`；schema3 会先选 `None`／`nullcontext()`，再进入 `process(..., admit=admit)`。它随后由 `admit:1041` 的无条件 `validate_context` 拒绝。原 native patch 在 callback 之后才进入 binding／started／runner 逻辑，故没有据此发现训练执行绕过；已存在 result 的原幂等返回还可能在 callback 之前发生，不能误报成重新执行。

最小修正：把表述改为“schema3 在 executor admission callback 的 context 校验处、任何训练 admission 效果前拒绝；外层 schema2 permission 分支保持原状”。实施验证沿现有 native／execution fixture 走一次真实 `native_main → process → admit`，断言无新 started／attempt／ack／runner 效果，并保留已有 result 的旧读取语义。单独调用 `validate_context` 只能证明 validator，不能认证 callback 接线。无需新 helper、framework 或额外产品 gate，也不要求在本片接通 schema3 的父 permission。

## 来源、恢复与维护性

四路径 inventory 与已批准 wire 一致。`training_rounds.create → training.approval → reference_training_release(operation='status')` 是第四项的实际读取依赖；这不授予 release。固定路径 tuple 属协议 owner，capture 私有地留在 cycles，使用原普通／无链接／有界 reader，对包根原字节计算 raw SHA；不需要导入 evidence／release／rounds 模块或新增模块。

此四项在授权时冻结；原25项 `GATE_SOURCES` 是原 candidate owner capability 的来源；包内 `reference.ROOT` 的283参考与所选 native installation 又是两种核验对象。不能把四项说成出生即冻结全部执行代码，亦不能把原 installation 核验说成 ROOT 核验。计划已明确区分这些身份，并把执行 source／ROOT 前后及最后 gate 留给 M2/M5，合理。

原 `_authorize` 的已有行为允许尚未 ready 的完整授权继续原 admission 检查，但不重开 clock、不替换已保留 ID；已 ready 的重试则只恢复原持久记录。新版本必须沿这一区别：外部 input 被删后可重试完整保存的 ID；坏／缺原 authorization 或 cycle 不能重新生成；当前 source 比较不是重新 capture；显式2重试不能退成默认1。草案在这些点可实施，未要求不必要的通用迁移、可变 current-round 或第二账本。

## 验证接缝与尚缺证据

已静态检查现有 `tests/test_training_submission.py` 的 `cycle_selection/controller_admission/historical_execution/controller_dispatch`，`tests/test_training_cycle_controller.py` 的出生／mode 碰撞、lock／ready fsync、intent 恢复、source／manual binding 和 SDK dispatch 接缝，以及 `tests/fixtures/training_controller_service.py`。后者使用真实 SDK DataConverter/protobuf 和固定 service double，适合验证 v2 type/input/queue/memo 与错 v1 type 的 read-only 认证；不代表真实 Temporal server。现有 SDK runtime 测试还有有界 child Replayer／取消 eviction 接缝，无需新测试文件或 CI 分组。

实施须保存 schema1/2 的完整 raw input/auth/ready/intent/attempt/receipt 与重试后对比，不能只比较 SHA 字段或少量新 schema3 字段。source drift 用 reader seam 替换，保留真实固定路径校验；fault 需覆盖 ID 保留后不换 clock/source、ready 已 link 后目录 fsync 失败、intent 准备／恢复受原预算与 stop 限制。关键拒绝检查应观察原 fixture 的 SDK call logs 和实际 native 文件，而非仅断言报错文字。D1 所述真实 callback 入口应补入第4项的具体执行范围。

c1c 的 retained 原件已由交付／终审定位；本审还只读核得 `.ergora/checks/cw-live-r1/first-positive-r5/history.json` raw SHA256 `dc7d9587823941f0f7a99d0a6f2c6a366d58ddbd7d50f695f48cc7c87fbd47c8`，其 `replay.json` SHA256 `622d99c00b397de6946713b289099741887189db838a219ace04a80f0e848474`。这只是确认可定位的历史输入，未重放它，也未逐份认证所有成功／取消／失败原 history。M1b 实施时须实际定位各所用原件并记录自己的 v1 replay 结果；不可把本审或 c1c 原 replay 直接转记为新产品通过。

**未执行：任何 M1b 源码／测试实现、测试、服务、安装、网络、模型、训练或 replay；未 commit/push。** M1c 完整编码、M2 接受/source/ROOT、M3 collect/durability、M5 最后前驱/native gate、M6 实际 V2／活动／注册／连续预算、M7/M8 新安装与真实两轮／恢复／收尾均仍缺本片自己的实现和证据。当前审查不认证其中任何一项，不认证训练质量或 successor 权利。

## D1 同片限范围复核

2026-11-16。原独立 reviewer 仅复核上述表述／验证义务修订，不重复扩审。已独立重核 [M1b 修订稿](../plans/2026-11-16-training-cycle-v3-birth.md) raw SHA256 为 `b2edb47f9227fd37d0499bdba82f9146f304937671b9bbe13ece1f5402dcd6e0`。原稿 `6e2b8552…` 及其审查身份保留。

第53行现在准确说明 schema3 跳过 native 外层 schema2 专用 parent permission，实际由 executor `admit → validate_context` 在 started／attempt／ack／runner 效果之前拒绝；第65行明确必须沿原 executor fixture 的真实 callback 入口核拒绝与效果缺席，不能只测 helper 或声称外层分支运行。**D1 关闭，无新增 finding。** 这只是准确描述原调用顺序和明确已有测试接缝，不新增 framework、产品 gate 或 schema3 执行能力。

头部记录主控接受内部 storage-only 阶段修订，并分别标识原设计基线 `fa2fd176…` 与 M1a 后实施基线 `bd479050…`；本复核不替代 M1a 自身审查或未来 M1b 实施审查。主控接纳阶段修订不表示接受／前缀／native 最后 gate 或正式 V2 等后继责任已完成。

**修订稿最终静态设计结论：需求轴 approve／开放0；维护性轴 approve／开放0。** 仅覆盖上述内部 schema3 出生／读取／本地 intent 的 bounded slice，全部实现与运行证据仍待。复核只读修订文本并追加本节；未运行测试、服务、安装、网络、训练或 replay，未改产品／测试／计划，未 commit/push。对新报告执行 `git diff --no-index --check /dev/null <report>` 无空白诊断；新文件差异状态不表述为 exit0。
