# c1d M6：正式 V2／SDK-v3 runtime 独立设计审查

2026-11-16。Reviewer：fresh-context 独立代理 `cycle_v2_runtime_design_review`，未参与设计或产品实现。按 maintainable-project-delivery 的 independent-review brief，以及 ergora-codebase-quality 的 module-design／test-seams 审查。唯一写入是本报告。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|**approve，仅限所审静态分期设计**|0|
|结构／维护性|**approve，仅限所审静态分期设计**|0|

在下述原件与静态检查范围内，没有形成需要修改方案的可达缺陷。批准的是封闭版本接线、有限循环 producer、原 owner／最后 gate 和分期验收设计；不是产品实现、完整 M1c、服务拓扑运行通过或执行开放。正式 V2／v3、ordinal1、真实 CPU 两轮均未由本审确认存在或通过。父留存最终产品、M5 实施和准确联合候选仍各自是前置。

## 原始要求与对象身份

审查输入为根提供的原始任务要求及已接纳的测量／wire／容量／M2／parent／M5 合同。要求是真实、有限、多轮的优化控制：保留原 baseline／candidate、每轮原结果、数值／质量约束和独立审查；继续使用原六阶段、kernel 总提案路径、可嵌套模板和不同 backend 的原接口。祖先资料完整继承且权限收窄，人工采用／release、candidate-bound evidence、批准、不可续预算、attempt-before-send、unknown-only 对账、唯一效果机会和资源收尾不能削弱。这里不审议 WA4 未答复的产品决定。

主树 `refactor/architecture-foundations`，HEAD 为 `a0d533d13b4aae9441e3b6b920b27c2534353b87`；已导入的内部 M2/M3 产品为 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，导入提交 `c6cfafb0b556c0cd36cf6f541e95ac4b15d3b254`。进入时主树已有他人的 PLAN、M2／parent 交付文档变化和 parent 源审报告；未覆盖或把它们算作本片产品 diff。

|实际读取原件|独立核得的 raw SHA256|
|---|---|
|[本次设计](../plans/2026-11-16-training-cycle-v2-runtime.md)，34,787B|`c228041efb586f3f0e929e20695106d779ca56b4d2ce544d27f67d457bd305da`|
|[measurement/index](../plans/2026-11-16-training-cycle-measurement-and-index.md)|`4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d`|
|[严格 wire](../plans/2026-11-16-training-cycle-measurement-wire.md)|`ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|[容量分期](../plans/2026-11-16-training-cycle-measurement-capacity.md)|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|[M2/M3](../plans/2026-11-16-training-cycle-measurement-acceptance.md)|`2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`|
|[父请求留存](../plans/2026-11-16-training-cycle-parent-request-retention.md)|`bf35924d01b665470fe5ba216f9e9e450162390498cff44dcdd5eb5ddb39bafe`|
|[M5 最后 gate](../plans/2026-11-16-training-cycle-predecessor-native-gates.md)|`8d5f84b36357a6f9ec6e524a1dc7d7af4e6ed22a6ae69e9b7ff8e32cba521044`|

读取了上述各片的独立设计审／复审，以及 M2 [固定产品最终源级／安装终核](2026-11-16-training-cycle-measurement-acceptance-source-review.md)，保留原 finding／失败和后续有限复核的区别。本审没有重验其私有运行原件或继承其测试成绩。另读根／src／tests AGENTS、PLAN、组件变更协议、原 runtime-consumers 与 bounded-cycle 需求背景。

必要源码实际 SHA：worker `522b9cf4a0db51cea6e4722e6136e005a825114ac1deee1f7e7dadc3b4292651`；runtime `280cf8699ee1b22577b85171835779369d922391c01e884bb46921b2547c7314`；protocol `a0b29a9412b2ab1b31341873e8cbeb24da0af5529ec40e541b5dd68c811e220a`；cycles `0a96a1c14ede76510e7480299e0958d36296ba0e5895a63743e311d1a03ff110`。budget／execution／submission 也独立重算，与方案列明的 `1fde5981…`／`f6b4a1ab…`／`9c775643…` 相同。没有进入 parent 隔离树审其新实现或把文档进度变化当作其终核。

## 需求判断与实际可达边界

- **版本隔离完整。** 方案第54–68行明确新类、两队列、七活动、request／envelope／outcome 和 operation 的封闭选择；旧类／旧 command／schema1/2／owner 原件保持。当前 protocol 的 operation 选择仍按 measurement mode 区分新旧，当前 SDK wrapper 仍只注册旧六活动；方案明确指出这个实际缺口，并要求 cold、candidate、stop、本地 controller mode 全部接新版本，不能仅注册 collect 或把 `==2` 改成 `>=2`。core 可选 SDK 和顶层可重导入类的职责延续原 owner。
- **存在真正 producer 的交付目标。** 第78–86行要求 V2 实际调度并消费 typed facts，而非用保存的 index 推进。真实 N／common／出生 sources 固定，start／request／collect 在 command 前各占一次；collect 未开始、丢 completion 或目标缺失也不退机会，reconcile 永远 existing-only。现有 runtime `authenticate_round_collection:126` 已沿固定父 run 完整扫描 scheduled events、真实 converter decode、唯一 collect/current command 和8000 events／8MiB界；这证明已有可复用实现位置，不能证明正式 V2 history 已运行。
- **前驱和结果保留闭合。** consume 先核完整容量／shape和原身份，prefix／acceptance 同次正面才推进；后继 intent 保存原 predecessor，后续重观察不能换绑。M5 负责经原 intent 逐层核全 prefix、原 observation 和完整 evidence／ExecutionRecords 库存；最新摘要不能替代早轮原件。原 baseline、质量 gate 和人工 release 窗口保持，循环不自行生成新候选、改变收益标准或采用结果。
- **最后 gate 和出生 pin 没有被合并成虚假证明。** 第114–124行逐一落到 submission attempt 同步后、registry absent 分支、execution publish 同步后、native executor callback attempt／ack 各阶段，以及 collect 最后 RPC／index reader 后。与实际 budget、Execution、submission、native callback 的所有权一致。四项 measurement 在 schema3 授权出生，25项 capability／manifest 在原 owner 出生；方案没有把 ready 当25项 pin 或给 ordinal0 补造尚不存在的 owner manifest。ROOT283、所选安装、source、stop／clock 仍须在实际最后动作复核。
- **开放次序没有借内部通过跨级。** 第124、132–149行要求先保留显式关闭，M5／完整 M1c／版本接线齐全后在一个隔离候选逐点换成真实条件，冻结后验正向 CPU 两轮、安装、模板与 fresh 终审再接纳。不能以早期 schema3 拒绝代验晚处 reader／attempt／ack，也不能以手构 source、服务替身或 helper accepted 结果代替真实父 Workflow。

## SDK／容量／服务可行性核对

除项目源码，静态读取了现存 `.venv-dev` 的 Temporal Python SDK **1.34.0** 源文件与 METADATA；没有 import／启动 SDK。这只是本机可读依赖的能力调查，不是未来固定安装或 server 身份证明。

|关键设计|实际库／owner证据|仍必须完成的真实验收|
|---|---|---|
|同 cycle 进程四个 versioned Worker、两份业务配额|当前 `_serve_cycle:2123` 已持有 normal／stop 两 Worker 及有序实际 task cleanup；SDK Worker 可按 queue 注册 workflow／activity，拥有活动并发参数。共享局部许可可留在同 owner，不要求第二调度器|两 normal 共一个许可、两 stop 共另一个，许可持到 operation／peer cleanup；混合版本、等待许可时取消、fatal／loop teardown和有序 shutdown 必须由真实注册服务验证。四个 SDK 各1槽本身不能证明业务总量仍为2|
|等待许可不续 SDK／BOOT 窗口|SDK `activity.Info:110–118` 提供 scheduled/current-attempt scheduled／started 时间与 schedule-to-close、start-to-close timeout；原 `_CycleOperation` 支持传入固定 bootstrap|第72行要求的等待前固定 window、拿到许可后不重造、与 SDK 两个截止和原 budget 取 min 必须真正接线；不能仅依赖 server timeout 通知或本地 semaphore sleep 证明 H 的本地窗口正确|
|实际 task 收尾|SDK `_worker.py:784–800,865–927` 说明 run/shutdown 等待活动完成；当前 `_CycleOperation.run` shield 原 task并保留管道／wait，stop fan-out finally 等 peer|这不提供70秒内必回收的保证；进程不可中断 I/O、SIGKILL／服务管理器强停与 server terminate仍必须分别记 unknown／实际身份，不能称 durable stopped|
|完整 Payloads／Memo／query／signal／outcome|现有 `_cycle_capacity` 使用实际 DataConverter 和完整 Payloads，旧 Workflow 用绑定 payload converter；dispatch 确实还缺完整 input/Memo gate，旧 consume 确实缺 received-envelope 整体重核|方案第96–104行明确补到实际 dispatch／invoke／V2出口；metadata、完整接受投影、全部 stop 分支和真实 Memo protobuf必须实测。默认 converter 的对应关系不能推导任意 codec保证|
|完整 Failure|SDK `_activity.py:350–459` 在 activity wrapper 退出后再次 `encode_failure`；默认 `_failure_converter.py:137–155` 从实际异常加入 traceback、cause／context，再编码 details|第102行的“固定小 ApplicationError”本身不足以证明最终 Failure合界。方案已明确要求完整最终 protobuf／实际 server记录，并在需要 SDK错误出口适配时先复审、未完成则不闭合；本审没有把局部预编码或小 message认证为成功|
|每个10MB消费者|protocol `read_round_observation:352` 已显式用 ARTIFACT_LIMIT；当前 H collect／previous读取有真实 owner。budget.source／validate_context仍显式拒 schema3，native后续读端尚不能借此验收|第110–112行要求真实 H／CycleAdmission／budget／Execution／native外层与 callback各到原reader，合法>1MiB及M−1/M/M+1经真实入口；完整 index／observation 的严格 bytes／raw SHA／LF和全链绑定不能靠helper通过替代|

上述未验项是方案保留的 mandatory gate，不是本审新增 finding 或准许降低的合同。特别是当前 worker 只有 measurement 两 mode 的内部 operation-v2，父留存最终产品也只覆盖其限定模式；第106行明确要求新增 cold／start／request／stop mode 与诊断控制 validator 同片接齐后才关闭完整 M1c。没有依据称当前 parent 实现已经替正式 v3 的所有 producer留存成功。

## 维护性判断

新 Workflow 类的必要性来自 SDK 顶层重导入与旧 history 隔离，不是为版本另造通用继承层。实际 caller 仍为 services 命令构造→cycle worker，worker→原 S/H，H→原 submission／runtime／evidence／rounds，以及 budget／execution／native 的最后执行边界。计划没有给 CLI／页面增加另一套状态机或新服务。

共同前驱／source算法放在已有 stdlib protocol，调用者确在 budget、execution、worker 等不同生产文件；SDK／State／archive编排留 worker，native不引入 SDK／State／jsonschema。继续复用 rounds、evidence／comparator、reference.verify 和原 fd／sync／reaper，未发现复制 archive reader、manifest walker、无消费者 proof／ledger或虚构复用的设计。共享 semaphore只隐藏原服务的并发／清理义务，不需要 manager或持久许可表。

第157行指定的现有 fixtures 能保留真实 S/H、锁、fd、callback 和 converter；第133–147行又明确要求默认 sandbox／真实 eviction／replay、丢回复、预算及完整进程身份。这能观察本片的真实静默失效，验收不止于 parser／helper。不同 backend／祖先模板的现有接口没有在 runtime层新增具体实现分派；此设计也没有据此声称新 V2 已经验过任意 backend或训练框架。

## 检查限制与后继

执行的检查仅为静态文本／Git／长度／SHA／相对链接及报告 whitespace核对。未执行 tests、probe、SDK import、history replay、安装、网络、模型、服务或训练，未修改 source／tests／计划／他人报告，未 commit／push。没有审查完整 parent产品 diff、M5实现或真实运行库存；没有 GPU／训练质量／性能收益结论。

下一步可按原方案先闭合 parent固定产品与 M5-G/R，再以准确联合基线进入 V1最小实现。完整 M1c、四poller真实生命周期、所有最后gate可达反例和固定安装 CPU两轮均继续开放；每片以自己的固定差异和实际证据做 fresh审查。本报告只关闭本次静态设计审查，不关闭任何产品／运行门禁。
