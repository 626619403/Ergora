# WA5-S2：来源 journal 独立设计审查

2026-11-16。审查者：fresh-context agent `/root/design_s2_proposal_review_r2`。本轮从原始要求、仓库规则和实际 owner 开始独立检查；没有接收或继承此前被中断审查的结论。本轮唯一写入为本报告。

|审查轴|结论|范围|
|---|---|---|
|需求符合性|**approve；开放 finding 0**|固定 proposal 的 inspection-only 存取合同、原文恢复、唯一链、权限边界及待执行验收。|
|可维护性|**approve；开放 finding 0**|实际 caller、原 owner、应用／native 依赖分界、配置关系和真实故障接缝。|

这是设计门的静态结论。S2 尚无实现、源码测试、新安装、真实服务或自然人验收；不能据此声明 source journal 已可用、设计已批准或 F/J/G 已完成。没有需要先修改 proposal 才能开始本片实现的实证 finding。

## 固定输入与源码身份

|输入|本轮实际核对|
|---|---|
|完整受审 proposal|[2026-11-16-design-source-journal-s2.md](../plans/2026-11-16-design-source-journal-s2.md)，197 行，SHA256 `fdf2c8a8bebac116a0b1a56556a4fcc1f3493e3fd93c2b2c1f3f87d65c185c0e`；开始及写报告前 SHA 同一。|
|原始要求|[workflow-evidence-and-human-gates](../plans/2026-11-15-workflow-evidence-and-human-gates.md)，SHA256 `3d5ed4f8f080b7b4099eaa998c2d9a5c767e6d7953b21ecd72b3f6e6d2763040`；[D1–D4 原答复](2026-11-16-workflow-design-decisions.md)，SHA256 `f4890512a56b7010b7ca4ca9b40aefa8a366a5b25f4ebe4d0e7fb73c73f37b68`。|
|详细设计与已审拆片|完整读取 [WA5 详细设计](../plans/2026-11-16-design-knowledge-gates.md)，SHA256 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`；读取[拆片](../plans/2026-11-16-design-gates-registration-and-journal.md)，SHA256 `bde47bee749ff973901beeebc6f148316b3ea2d2635e191ac5804942e142f984`，特别是 S2、第 4–5 节及验收矩阵，并读其[原设计审查和 r2 处置](2026-11-16-design-gates-registration-and-journal-design-review.md)。旧审通过只作其原范围依据。|
|proposal 原源码基线|Git 实核 `c540939d3b3f38f3851b0de965c9cd0f969eea77`；src tree `88b9ca4a1a3ab40e578b852465d8425ad9b2f0d2`，tests tree `11ca981bcc4e7b4c5de7d21dfdb9a3ba6098e64b`，与 proposal 第 9 行一致。|
|本轮兼容性检查产品|准确联合产品 `6cec589f404b17f4828a70807d5e33d89fad3fa0`；固定集成树为 clean。src tree `004f08569e146c3cc3eaae0a7f4abaec15fc577f`，tests tree `c5034f1191636ea93ebcdb0fc657c68eea23a325`。检查了从 c540939 到此产品的 source/test 差异，并定向阅读最终 S1 的变更。|
|共享主树变化|开始 HEAD 为 `fc632ad91cd4847f541607710e96164d351bdebc`，已有主控 docs 修改／新增文件；审查期间主控形成 docs-only `7fc42177db11fbfe4c9adb33342ecb5da4ed0434`。结束前实核 src/tests tree 均与 6cec589 同一，proposal 字节未变。本报告不归属或覆盖这些主控文档变更。|
|已接纳 S1 的证据边界|阅读[S1 交付](2026-11-16-design-policy-registration.md)中的最终修正／合入状态及[联合交付](2026-11-16-design-capacity-integration.md)；后者记录新安装 32 passed／135.20 秒。这是其已有报告事实，本轮未重跑，也未独立认证原运行或转授给 S2。|
|协作／质量规则|根、`src/ergora`、`tests` AGENTS、当前 PLAN、[组件协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 及 independent-review，`ergora-codebase-quality` 的 module-design、test-seams、repository-style。`pyproject.toml` 的实际依赖／pytest／包资源配置也已读；未套用其他仓库的 lint 或测试规则。|

实际源码检查的范围为：`tasks.py` 的 `_project/_definition/_budget_project/plan/approve/resume_approve/_native_prepare`；`reference.py` 的 `task_plan/task_approval/_task_operation`；`reference_task_approval.py` 全部 `_read_design/_plan/_Approval/main`；`reference_task_submission.py` 的原 submission、expected、submitted、lookup_run、memo 和恢复；`reference_task_creation.py` 的构造、安全读取、check_registration、validate_record、published、status、publish；`reference_creation_process.py` 的两个实际进程入口；`state.py` 的 writer fence、file_lock、State 构造／读取；`registrations.py` 的 saved／published 原件和首次登记边界；最终 `reference_executor.py` 的 `_admit_project/Executor/process`；纯 `task_design.py`、`contracts.py`、已发布 task-design schema／a1 profile；原参考 `adapter.safe_file/read_raw/publish` 和 `core.slug/write`；CLI 的 task 路由、HTTP 的现 plan/approve caller。读取现 `test_task_plan.py`、`test_task_approval.py` 与 `fixtures/task_approval_client.py` 的相关 fixture 和跨进程／恢复用例，未执行它们。

上述 S2 直接复用的 `reference`、approval／creation／submission／cancellation／creation-process、contracts、冻结参考资源、task-design schema／a1 profile及原 plan/approval 测试，在 c540939→6cec589 的定向 Git 比较中没有变更。源码检查没有发现已实施的 S2 source-kind 协议；proposal 中的函数和资源仍是拟议产物。

## 需求符合性：实际故障路径与设计处置

|可达场景／位置|检查结论与最小实施边界|
|---|---|
|首次保存必须绑定实际 pending seed|proposal [第 25–30 行](../plans/2026-11-16-design-source-journal-s2.md#L25)、[第 109 行](../plans/2026-11-16-design-source-journal-s2.md#L109)沿真实 `_plan`。现 [approval 第 75 行](../../src/ergora/reference_task_approval.py#L75)先核原 submitted；其后核原 run memo／history、plan envelope、SUCCEEDED receipt、canonical receipt SHA和 artifact raw bytes。首次在线观察与锁内本地重读分开，未声称二者与 Temporal 原子化；已有 anchor 的本地恢复不重新查询服务，身份漂移仍拒绝。|
|两轮完整来源和原答复不能被摘要代替|[第 59–75 行](../plans/2026-11-16-design-source-journal-s2.md#L59)要求完整 packet／response及每件准确 UTF-8 text、raw SHA、bytes、media保存在 intent；packet 与 material revision分开。seed→publish→response→publish→response保留每轮正文，response不改 packet状态／不跨版自动继承；完整读回的 bodies表去重但不截断。原文、canonical packet、seed receipt和 source tail的摘要职责分明。|
|body-file已删、正文后/result前进程退出|[第 111–114 行](../plans/2026-11-16-design-source-journal-s2.md#L111)先固定完整 intent，后按同 intent发布正文／packet，最后 result。恢复不重读原 body-file、不重取当前配置、actor或时间；缺本操作 managed body可由原 intent显式重建，冲突内容不覆盖。result已存在仍核原件，避免成功早退遮蔽丢件／损坏。|
|新 ID抢占同 parent／schema1同 ID|[第 47 行](../plans/2026-11-16-design-source-journal-s2.md#L47)、[第 95–101 行](../plans/2026-11-16-design-source-journal-s2.md#L95)给出同一 operation命名空间、显式 schema2/kind、唯一 parent与下一序号的 pending占有；未完成尾部只许原 ID恢复。现 [_Approval.load](../../src/ergora/reference_task_approval.py#L186)本就按完整 schema1意图核身份，不能把它改成宽松读取 source。新 source reader也须先分版本，坏件／分叉不可跳过。历史同 ID重提返回自己的已核原记录，而非另选当前 head。|
|GET不应建锁、修件或声称持久|现 [file_lock 第 128 行](../../src/ergora/state.py#L128)以 `a+b`打开，不能直接用于新增 GET。[第 103 行](../plans/2026-11-16-design-source-journal-s2.md#L103)明确改为只读打开已经存在的原 creation lock，no-follow、普通文件、fd/path dev/inode核对和同 inode共享锁；缺失／替换／锁忙返回读不可用。GET不fsync、不补件、不连本地 source不需要的服务；旧在线 plan查询仍保留。要求快照整个 execution state/config文件名及字节，能观察偷偷建文件的问题。|
|直接公开 source callable绕过应用校验|现 [reference.task_approval 第 752 行](../../src/ergora/reference.py#L752)的 a1修正把 inspect-plan送到同应用校验，说明此风险确有公开 callable。[第 55、109、120、136 行](../plans/2026-11-16-design-source-journal-s2.md#L55)及其继承的拆片第 93–94 行要求提交先经过应用完整结构校验，所有 source公共读写结果再经应用校验才返回。实施时必须让直接 `reference` mutation入口同样遵守提交前校验，不能仅在 `tasks`校验或写后才验结果。native只核原件、领域关系和安全IO，不导入／复制jsonschema，不接受 `validated:true`作为授权。这个结论是对原合同的核对，不增加新的 native validator。|
|材料完整被误当 owner处理／执行权|[第 17、32、73–75、134、176–178 行](../plans/2026-11-16-design-source-journal-s2.md#L73)固定 local-process-only、reported metadata和 `ready:false`；owner-channel请求在intent前 unavailable。supplied事实不等于Q/K被有权处理。source_chain仅是 committed tail SHA，未冒称 J的materials SHA或批准binding；S2没有 resolution、seal、withdraw、definition8/input12、scheduler或新执行入口。|
|坏件和缺部署能力被包装成同一种成功|结构／正文／parent／binding损坏明确 blocked/unknown；原安装不可用和登记漂移不猜 fallback；缺可信人类通道明确 unavailable。`runtime_status:not_queried`不声称旧 run仍 pending。已有 result可见和本次写调用实际确认 durable分别报告；GET不根据持久布尔重造证明。|
|旧批准、取消、预算和冻结任务被来源提交改变|[第 19、101、112、168 行](../plans/2026-11-16-design-source-journal-s2.md#L101)保留schema1旧语义，没有因 source pending而增加旧 approve seal。现 [_Approval.run](../../src/ergora/reference_task_approval.py#L274)的 attempt-before-send／原run对账与 [_Cancellation](../../src/ergora/reference_task_cancellation.py#L16)继续原owner。source只作本地IO，不写旧receipt/signal/fence/spec/creation/clock，不重领预算。旧v1可以按原合同执行；S2也明确不声称旧work强制消费新讨论。|

未发现需求遗漏需要纠正。D1–D4最终闭环中的可信决定、冻结policy、完整权威materials、seal／withdraw停止尾部及G1/G2仍在明确后继，不会被当前存取切片的通过替代。

## 可维护性：owner、容量与最终 S1

来源目录扫描、唯一链、raw publisher及同 ID恢复留在 `reference_task_approval`是合适的：它们隐藏原 creation/submission/run身份、同任务锁、不可变文件和恢复义务。现 publisher只接JSON，[adapter 第 74–87 行](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py#L74)和 [core 第 33–53 行](../../src/ergora/data/reference/platform/local/agent_platform/core.py#L33)都只fsync临时文件；新增私有 raw publisher和实际 source use site的同现存文件／父目录确认有具体职责。无需改冻结283参考、全局publisher、Executor.artifact或抽journal基类。JSON intent/result仍与原不可变出版合同一致；完整intent的上限须传给实际读取者，不能落回 `_Creation.optional`默认1MiB。

`tasks`负责真实应用用例与短 revision reservation，`reference`负责所选进程和结构校验边界，native负责原件及持久状态，CLI负责文件解析和展示。当前真实首个消费者就是CLI，不借未来HTTP／G1/G2凑复用。新schema和容量资源按协议／配置角色有必要；未见只转发一次的service、空adapter、通用事件平台或第二状态库。现项目为平铺Python包，`contracts.StrictValidator`已足够，`pyproject.toml`也支持新增 data资源；没有新依赖理由。

容量合同[第 87–89 行](../plans/2026-11-16-design-source-journal-s2.md#L87)没有把建议默认之间的倍数变成算法。首次可逐项收紧且冻结完整profile/SHA；有效关系必须容纳原seed及至少一条完整操作；每件artifact、完整intent、包含pending的实际journal raw bytes／操作数、packet revision和最终完整公共JSON分别受限。新操作在intent前计算加入后的完整公开视图，连同 `task plan`原seed materials及应用最终输出一起计量。因JSON转义、历史packet或正文重复使最终编码变大时，不能只加body长度或使用native临时handoff大小代替；实际 prospective大小决定拒绝。较小合法配置不必保证始终写满64条，按该配置在首个达到上限的操作前零增量拒绝即可。这足以支持有效非默认配置，不需把上限锁死到例子或扩分页。

DB／网络分工有真实依据：[tasks._native_prepare](../../src/ergora/tasks.py#L589)持 `BEGIN IMMEDIATE`等待native本地prepare；当前 [approval 第 282 行](../../src/ergora/reference_task_approval.py#L282)已经为prepare使用非阻塞creation lock。proposal把首次在线seed观察移到该事务之前，commit／resume移到事务之后；本地prepare内只允许有界原件检查。source仍与原approval／cancel使用同creation lock，未新增有权决定或取消控制器；不能通过新增路径把 `environment()`或connect带回本地阶段。

最终 S1的实质变更与本proposal兼容。实际 [task_design.require_execution_support](../../src/ergora/task_design.py#L10)由 `tasks._definition/_budget_project`及受管executor的两个preclaim入口调用；source reader不会经过这些新任务／业务准入。最终 [registration._prepare](../../src/ergora/registrations.py#L197)拒绝已有登记v1→v2，保留原四投影与旧creation／submission恢复要求，S2未申请更新登记或导入policy。State6只改变writer fence，不增加source存储表；schema1 v1 source任务仍走上述未变的 `_Creation.published/_Submission.submitted`。因此 proposal第12行的“S1待闭合”应按原日期的历史事实读取，当前接续实施须固定6cec589或后继准确源码；不能把这次兼容性审查写成旧c540939证据已经rebase验收。也不能为了使新v2项目产生seed而绕过已完成S1的拒执行guard。

没有可维护性finding需要最小纠正；实施者仍须按上述实际owner和冻结接口交付，不能用最终S1的已过安装替代新source路径的验收。

## 待执行验收是否能观察真实故障

proposal第9节选的接缝足够，且明确保留其限制：现 [test_task_plan 第 425 行](../../tests/test_task_plan.py#L425)在真实 `reference` launcher、所选解释器、main、原submission和 `_plan`后仅替换服务connect；它使用 `-B -S`和显式拒绝jsonschema。相反，[test_task_approval 第 31–34 行](../../tests/test_task_approval.py#L31)替换main命令体，适合保护原schema1恢复，但单独通过不能证明新增native入口和依赖。S2要求扩前者，并在真实tasks／CLI、原文件链、新State／新进程读回和原main上观察新增行为，而非只向helper传正确对象。

需要实现阶段取得的证据仍包括：完整两轮逐字节读回；删除／改写body-file后同ID恢复；至少一次正文后/result前的真实子进程退出；跨进程pending竞争和schema1同ID冲突；GET前后完整文件快照及只读锁；坏链不跳过；非默认有效容量的M−1/M/M＋1及aggregate零增量拒绝；各公开source入口的应用校验／内部handoff去除；持久确认失败和同ID复核；无packet及旧schema1 attempt/unknown恢复。应使用相同新候选的新非editable安装再次走真实CLI和所选native，不把源码hook测试、旧wheel、SDK叶替身或前代CI当新安装通过。无需为设计文档跑产品测试，或为S2重跑无变化训练／GPU。

## 实际检查与限制

本轮只执行本地 `git`身份／status／diff／worktree、`rg`、分段源码和文档读取、SHA256和行数检查；没有产品测试、probe、模型、服务、安装、网络、训练、GPU、commit或push，没有读取凭据／环境快照。未验证任何真实ACL、人类身份、Temporal生产部署、进程断电耐久性或将来S2代码。共享主树的原有改动由主控处理；本报告完成后只检查自身链接／空白、proposal SHA和写入范围，PLAN及slice交付状态由主控更新。

六个指定反例逐项回溯如下：**“恢复必须重读body-file”**由完整intent及不收新body-file的resume合同排除（第62、112–114、129行；待正文后真实退出验）；**“GET用a+b开锁”**由既存锁O_RDONLY／同inode共享锁排除（第103行；待文件快照和实际native行为验）；**“同parent pending被新ID绕过”**由pending占唯一parent且仅原ID恢复排除（第99、111行；待真实并发验）；**“公开source callable绕应用schema”**由继承的提交前应用校验、所有reference公共结果同校验且去handoff排除（第109、136行及拆片第93–94行；待直接公开入口及真实native拒jsonschema验）；**“source链被误当权威materials”**由tail SHA与J materials／a1 inspection明确分名、readiness及执行capability保持false排除（第97、134、177行）；**“schema1旧批准被悄悄seal”**由保留原approval语义且明确S2不加seal排除（第19、101、168行；待原approval与source交错兼容验）。这些是设计已规定的结果，六项均未被本轮声称取得S2运行通过。
