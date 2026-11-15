# c1d M0 wire：独立设计审查

日期：2026-11-16。审查对象为 [M0 wire 草案](../plans/2026-11-16-training-cycle-measurement-wire.md)，35,560 bytes，raw SHA256 `988ee80088df07c58c5294c61c8ab2ab369b3cd151d8fd44b54503066a00fb75`。本 reviewer 为本片新的独立上下文，未参与草案编写；使用 `maintainable-project-delivery` 的 independent-review brief 及 `ergora-codebase-quality` 的 repository-style／module-design／test-seams 进行静态审查。

**需求轴 request-changes／M0 闭合阻断1；维护性轴 approve／阻断0。** 需求结论针对“可固定并进入实施的严格 M0 合同”：完整 observation 的容量／最终编码尚未定义，不能把本草案登记为 M0 已闭合。草案准确披露了这一点，本审不将其改写为产品已经发生的故障。除该已披露缺口外，在所查源码与设计范围内未发现新的前驱绕过、旧历史自动升级或必须增加第二 owner 的问题。另有1项非阻断文档事实修正。没有产品实现或运行验收结论，不开放 ordinal1。

**同片复审更新：修订稿 `ae421196…` 的严格 wire 设计需求／维护性两轴 approve／开放0，R1与D1已由文档修订关闭，详见文末。** 上述原稿身份、原 request-changes 和其依据作为历史结论保留。新的设计通过不表示 c1c 终审、M1c 编码接缝或 M0 全部实施前置已经通过。

## 原始约束与调查身份

核对的原始要求是：同一新出生同意顺序消费1..32个既有候选；各轮保留原 manifest、baseline、执行链、accepted archive、数值／质量要求与完整索引。只有原 native SUCCEEDED、固定子 run 的允许 phase/outcome、原 archive gate pass 与真实 durable stopped 齐全才可续。所有轮共用不可续的原 BOOT 预算，attempt-before-send、丢回复只读对账、父 stop／source／project 最后 gate 和 native 的依赖隔离保持。旧 schema1/2 与 c1c 历史永远 ordinal0；安装新代码不得升级旧 ID。六阶段、祖先资源／权限、283参考和原 gate 不变，不 release／approve／迁 baseline。

已读根与源码 AGENTS、[PLAN](../PLAN.md)、[组件变更协议](../architecture/component-change-protocols.md)、[主设计](../plans/2026-11-16-training-cycle-measurement-and-index.md)及其[独立设计审查](2026-11-16-training-cycle-measurement-design-review.md)。实际主树分支 `refactor/architecture-foundations`，HEAD `df436606a7f080da494a781f86235b0e55064e65`。已有他人的 PLAN／c1c／Windows 文档差异和未跟踪交付文件，均未修改。

另只读 c1c 专属工作树，HEAD `fa78747d6c6ca62935fe6a44aa6db143c362baad`。独立核得实际 worker raw SHA `7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`，runtime tests raw SHA `4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`，与审查 brief／草案身份一致。主树邻接源码用于核持久格式及 source owner，c1c worker 用于核正式类、facts、活动 wrapper 和 S/H caller；没有混成一个已固定的 c1d 产品身份。

父任务提供的新安装53、原 W7 history replay及 W1 CPU／W2 pre-start/pre-request／W3 restart／W4 outage各自现场结果只保留其原范围；本审没有重跑或认证这些结果。c1c 的最终固定源码、W7 和完整终审仍是上游在途前置，不能登记为通过。

## Findings

### R1 — P1：完整 observation 尚无确定的读取与序列化容量合同，M0 不能冻结

位置：[草案第179行](../plans/2026-11-16-training-cycle-measurement-wire.md#L179)、第181行及第225行。

草案把 `observation.json` 固定为 runtime/native/execution/evidence 完整原结果的组合，并让 acceptance 的 `{path,sha256,bytes}` 成为后继 intent 与 native 本地 gate 的实际输入；但明确未固定该文件的合计上界与最终编码。真实边界并不统一：[evidence.main](../../src/ergora/reference_training_evidence.py#L131) 的响应上界为8MiB；[ExecutionRecords.load/observe](../../src/ergora/training_execution_protocol.py#L838) 的各记录／intent有1MiB和16MiB等不同读取界，`observe` 又返回 owner、records 和完整 raw inventory；runtime/native 的字符串也不能由固定字段数推出总字节数。原32KiB stdout/frame与10MB index均不能直接作为这个新组合文件的上界。

可达情形是各原 reader 都成功，但组合观察大于实现者沿用的默认 `read_raw` 1MiB，或者写端与后继／native读端选择不同编码和界。其后果可以是合法首轮已发布 durable index，后继无法重新认证原 observation而永久 unknown；若实现为绕过容量而省略原字段，又会破坏已承诺的完整绑定。当前文档没有授权截断，因此这不是已证实的越权漏洞，而是严格 wire 尚不可实施的明确缺口。

最小修正：在原单文件方案中固定一种完整编码和一个显式合计字节界，列清组合中每项的实际原 reader／字段来源、是否重复保存、写端与所有读端共用的界及超界行为；超界保留完整未发送原件并不给后继。该界可以保守拒绝较大的合法原观察，不要求扩大原产品容量。若必须改为多个固定文件，先修订 ref shape 与完整摘要绑定，再复审；不要在实施时新增隐式附件或 reader。静态容量核对属于 M0 修订，真实大值、边界和丢回复验证仍归后续实现验收，不能在本次审查补填为通过。

### D1 — P3，非阻断：原 operation identity 实际为10字段

位置：[草案第208行](../plans/2026-11-16-training-cycle-measurement-wire.md#L208)。

草案称 identity“仍原11字段集合”。真实 [protocol.validate_cycle_operation](../../src/ergora/training_execution_protocol.py#L229) 和 c1c `_CycleOperation.__init__` 均为10字段：`protocol,operation_id,mode,control_home,project,cycle_id,input_sha256,authorization_sha256,ordinal,parent`。`activity_context` 是 payload 字段，不在 identity 中。

最小修正是改为“原10字段集合”并直接列出原集合或指向其 owner。不要为了符合文档计数新增字段或升级旧 frame identity。这是严格 wire 文档的事实修正，不构成当前产品故障或新的架构阻断。

## 四项重点的独立判断

|问题|实际 caller／源码证据|结论与实施边界|
|---|---|---|
|measurement source 从三项增至四项|[rounds.create](../../src/ergora/training_rounds.py#L116) 对 submitted 调 `training.approval`；[training.approval](../../src/ergora/training.py#L180) 经 `reference.training_release(...,'status',...)` 装载 [release._Release](../../src/ergora/reference_training_release.py#L26)，其 `run/status/load` 参与完整索引观察。|第四项是真实生产依赖，接受其加入 schema3 的固定 inventory。它不表示 release 被授权：原 `status` 在锁／writer和 dispatch 分支之前返回，不创建 receipt、不 signal。它与原25项不同时间出生，不能宣称全部代码都在授权时冻结；草案已正确区分。未发现还需另建可配置 source registry 的理由。|
|包内 ROOT 的283核验|[reference._training_reader](../../src/ergora/reference.py#L444) 给 `training.inspect` 子进程设置包内 ROOT 的 PYTHONPATH；[validate_installation](../../src/ergora/reference.py#L132) 仅核所选 installation，不能证明 ROOT 当前字节。[reference.verify](../../src/ergora/reference.py#L37) 已能沿原 manifest 核283项；manifest本身已在 GATE_SOURCES 内。|新增 ROOT 核验义务必要且可用原 owner 完成。H接受前后及native最后gate应消费同一已pin manifest身份；选定安装的原核验仍独立保留。`reference`现有模块依赖不要求 State/jsonschema/SDK，未见因此必须新建 verifier 的静态障碍。实际耗时、原window终止、安装及native入口仍未验；不得修改283原字节来方便校验。|
|未知 H operation_id 时认证 collect 恢复|[runtime.lookup_controller/_controller_history](../../src/ergora/reference_training_runtime.py#L47) 已提供固定父run、memo、完整started input及 `fetch_history_events`／DataConverter的真实接缝，但当前只读取started首事件，没有 collect Scheduled认证。|新接缝可留在现有runtime/history owner，无需新增publication或attempt账本。原collect ID、ordinal、queue、type、完整request均可从固定run及确定性规则定位；reconcile可以写自己的原operation观察，不能重新create index或声称知道旧H ID。实现须有界扫描所需原history并计算实际事件/字节，精确解码单个完整request，检查同ID的全部Schedule而非遇到首个匹配就返回；出现缺失、重复、错request/queue/run、decode失败或界耗尽均unknown且不返还机会。Scheduled只证明原机会被消耗，不证明H已开始、已发布或已durable；后者仍由当前只读重核现存artifact和四事实。真实SDK事件/decode及丢completion反例尚待，静态可行性不替代该证据。|
|纯 rounds 内容校验提取|[rounds._check](../../src/ergora/training_rounds.py#L46) 先做contracts/schema，再核pretty SHA、原native绑定、anchor和prefix；其模块顶层引入 training/State，native不能直接导入。protocol已有native与budget/execution/worker不同生产caller。|把schema之后的纯内容检查及所需pretty编码／comparison／anchor算法集中到已pin protocol是恰当的最小提取方向。rounds仍先做原schema验证；native仅对H已schema验证并按raw SHA冻结的同字节索引使用纯内容算法。不移动contracts/schema/State，不复制archive接受／比较器，不建trusted reader或新模块。具体diff、原离线read/create行为和隔离import接缝仍须单片验证；本审未认证未存在的实现。|

上述source与ROOT两项新增义务在本次静态审查范围内获得设计认可，不继承为实现或现场通过；它们无需继续仅因“原审只列三项”而等待同一设计问题的重复审查。若修订再引入接受权依赖、变更ref shape或复制archive语义，则超出本结论。

## 其余闭合性与维护性

schema3显式出生、缺省仍schema2、新workflow ID前缀／queue／`TrainingCycleWorkflowV2`／七个v3活动，能够隔离c1c已有活动v2与旧类的command含义。保留旧类、旧精确validator及ordinal0 guard，不用patch或当前文件决定旧history的后继权，符合旧历史永不升级要求。schema1/2读取、actor、context、root/phase、runtime type及dispatch的实际分支确实需要逐个接通；草案第193行列明此面，不能实施时统一放宽为 `>=2`。

前驱 `{prefix,acceptance}` 只引用完整原观察，避免正文递归膨胀；以固定路径／raw SHA、真实run/input/memo/job、五execution记录及完整raw库存、evidence.files、原索引和递归原intent共同绑定，未将低覆盖index独立变成许可。status与outcome字段符合真实模型：Status有evidence_sha，Outcome没有，后者应绑定原gate-report URI。新摘要使用canonical值，round SHA沿原pretty编码，职责区分正确。原主设计要求对 `training_rounds.create` 实际重采得到的最后一轮 native观察做最终交叉核对继续有效，不能用create前的一份正面evidence替代。

collect私有组合、fd/inode durability和只读恢复留在原worker；archive语义留在evidence、索引公开合同留在rounds、原最后准入留在protocol/budget/execution/native。各新增职责有实际caller与失效路径，未见应增加manager、service、可变current-round表或第二reader的理由。将 `reference.verify` 直接接原最后gate比复制manifest walker更小，也保持原安装和包内ROOT两种身份的区别。

容量边界中，32KiB必须核完整DataConverter Payloads（含metadata）及完整S/H frame，不能只量typed facts；stop的2+2N完整operations、同时inline的facts/acceptance、context和所有identity/reason都计入。草案允许任何必要投影超界后保守拒绝且保留原件，因此固定shape本身不构成可装下的承诺。32轮、256 ordinary commands/轮与8000events/8MiB是分别先到即停的界，不能相乘推出32轮必能完成。R1只要求给新的磁盘观察文件同样确定的合同，不要求提高任何旧上限。

共享BOOT、D_work/D_total只缩、ordinal切换不cold、唯一start/request/collect机会、unknown不重授effect、父stop／source／project／clock在原锁和最后动作复核，以及保留前轮release窗口，均在草案中有明确责任落点。没有发现授权approve/release、改baseline、改原gate或把CPU控制合同冒作真实训练质量的设计分支。新SDK topology、默认sandbox、真实取消/收尾与最后gate仍需要自己的实现证据。

## 尚待证据与审查限度

R1修订并复核后，M0严格合同才可能冻结；c1c最终固定源码和现场终审仍是独立前置。本次认可source扩展、ROOT核验与纯提取的设计方向，不认证M1a纯提取diff、history认证实现或任一多轮产品。后续按草案M1–M8验证旧历史／新出生、四事实交错、完整prefix、同artifact持久恢复、最后gate绕过、完整编码容量、实际V2 CPU两轮、新安装/history replay及所有自建资源收尾。

本次仅执行只读文本／Git身份／SHA调查，并创建本报告；未运行测试、服务、安装、网络、模型、训练或产品程序，没有commit/push，未修改设计、产品、测试、PLAN或他人交付。审查结论限于上述准确草案与邻接源码的静态设计判断。

## R1／D1 同片修订复审

日期：2026-11-16。由原独立 reviewer 复审同一设计 slice；没有承担作者实现或形成新的产品片。准确对象仍为 [M0 wire 文档](../plans/2026-11-16-training-cycle-measurement-wire.md)，现为48,324 bytes，独立重核 raw SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`。原稿35,560 bytes／`988ee800…`及本报告的原需求 request-changes 保留，不以本次结论倒改历史。

**修订后需求轴 approve／开放0；维护性轴 approve／开放0，仅限严格 wire 的静态设计。** R1和D1关闭，未发现修订引入的新增阻断项。c1c最终固定源码和真实终审仍在途；M1c、history decode、纯提取及新产品均未执行，本结论不开放 ordinal1，也不声称 M0 的上游前置已闭合。

|原项／修订位置|复审证据与处置|
|---|---|
|R1：第181–195行，完整 observation 容量与编码|已固定原严格单文件 shape、完整 compact UTF-8 JSON＋恰一个LF，raw SHA与bytes均包括LF；单文件准入界明确为10,000,000B。protocol持有一个共享常量，rounds公开常量保留alias，worker/native各读端显式 `read_raw(path,M)`；禁止默认1MiB、读短前缀、重新编码后比raw或实施时拆附件。来源表准确区分原execution intent的16MiB读取界与observe并不复制该intent正文，也承认直接SDK runtime值没有由字段数推出的本地大小保证。现在无需从各组件上界猜一个新的写读界，R1的原不闭合条件已消除。|
|R1：第193–195行，超过M和部分写入|超M仍保留完整原材料但不产生合法ref／acceptance／ready；写入失败或deadline终止只保留已有材料并unknown，不宣称完整。合界文件须同文件同步、同inode/raw重读，后继先核ref.bytes、实际字节数、raw SHA与严格语义。允许保守拒绝某些原reader本来可表达的大观察，符合原R1最小修正；没有通过裁减原evidence/files或原chain来换准入。关闭R1不意味着新10MB写读实现已通过边界验证。|
|R1相关外层：第197–214行|逐个最终owner明确核完整Workflow request/query/outcome、H request、H stdout（含LF）、S result frame（全identity和 `_stdout_ref`）、SDK完整result及Payloads metadata。H stdout合界不代表包装frame合界；SDK facts合界不代表operations／acceptance聚合后合界。失败frame本身也须再核，仍过界则不发result，保留原件并unknown／容量失败。原stopped控制帧的65536B与业务result的32768B分别保留，没有靠提高旧上限或新增附件容纳聚合。|
|D1：第241行|已列出原10字段集合，并明确activity_context属于payload；与真实protocol validator及c1c `_CycleOperation.__init__`一致。没有为满足文档计数增加产品字段，关闭D1。|

本次重新沿真实 c1c `cycle_operation_main`、`frame`、`_CycleOperation`、`_cycle_capacity`、Workflow `_capacity/_ordinary/_stop/status/run` 和 `_dispatch_controller` 核了上述落点。当前源码的dispatch并无本次提出的完整input/memo检查，`frame`降格容量失败后也没有第二次检查；修订把它们明确写为**新版本在原owner的实施义务**，没有误称旧代码已具备。`perf_temporal.connection.connect` 确实未指定自定义DataConverter或codec，故Workflow局部payload converter与实际连接完整Payloads对应的设计前提有源码依据；安装时仍须核实际对应关系，未来自定义codec不在本结论内。

修订没有增设sidecar或第二持久owner：仍是同一operation的 `helper/observation.json` 加原rounds artifact与原chain文件；新共享数值常量在已pin protocol内，有rounds、worker与native这些实际消费者，不引入配置／新模块。原evidence、archive及比较器语义仍归原owner。四项source、ROOT283核验、前驱递归和纯内容提取方向的首轮设计判断保持。

超过M、外层编码超32KiB或completion丢失均不产生已确认prefix，已消耗的start/request/collect机会不返还。恢复仍只定位确定性原index，重新认证原件并在自己的operation保存新观察；即使之后得到更小的完整观察，也不能再次create index、改旧intent predecessor、换目录或续BOOT预算。该只读恢复可以形成新的完整认证结果，但不构成新的发布机会。第218行真实Scheduled-event认证接缝依然待实施／真实decode验证，首轮关于固定run、完整有界扫描和精确唯一Schedule／完整request的要求继续有效。

第252行新增M1c将真实整文件M−1/M/M+1、各原reader成功但合计超M、H包装frame超界、SDK完整聚合和metadata超界、N32 stop及query/signal/outcome列为后续实施证据，未填任何通过结果。c1c新W7 prefill及最终现场仍是父任务的在途工作，本次没有核它们的运行终态，也不据此前53项／旧history replay代填。

复审只读完整修订文本、相关源码与PLAN／Git身份，并在本报告追加记录；未修改设计、产品、测试或PLAN，未运行产品、测试、服务、网络、安装、模型或训练，没有commit/push。静态 `git diff --no-index --check` 对该新文档无空白诊断；新文件比较返回差异状态，不能称其exit0。复审对象SHA及字节数如上，结论不外推到未来产品diff或文档再修订。
