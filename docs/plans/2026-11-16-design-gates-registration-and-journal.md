# WA5 后继：登记、原源记录与运行双门的实施拆片

2026-11-16。**r2 实施拆片修订；针对新 fresh 设计审的 R1–R3 补齐边界，尚待同片复核；没有本计划的源码、安装或运行验收。** 本文细化[已审 WA5 r2](2026-11-16-design-knowledge-gates.md)的第 8 节，不重新讨论 [D1–D4](../delivery/2026-11-16-workflow-design-decisions.md)。r2 固定 SHA256 为 `5360d993ee7851f81237151f9ed2e5aba7a9f1f7dbf501f88e33dd18b61faa54`；其静态两轴 approve 不给本文、a1 修正版或后继实现转授通过。主控需把本文的实质拆片及旧 creation 耦合交新的 fresh 设计审查，再按片实施。

只读主树基线为 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`，分支 `refactor/architecture-foundations`。M5/native 已普通集成；其自己的公开 CI 本次未观察，不做网络代查或重试。并行 M6 的隔离表达片仍只表达 closed 效果，本计划不改它、不借其结果认证设计关卡。

**先决件 A：a1 的最终修正版。** [a1 交付](../delivery/2026-11-16-design-packet-inspection.md)的隔离基线为 `562394c839e9353e4f889a0b03e749ca32783936`；当前 r2 候选已把完整 schema 校验移到应用 `reference.task_plan`，原生 `_read_design` 返回安全、有界、完整的读取事实。本文只读取这一候选来核接口，不修改其隔离树。后继必须以主控最终冻结、安装、自身模板、独立复核后的准确修正版作为依赖，不能借 r1 wheel/118 或尚未闭合的 r2 为通过。无 packet 的旧结果继续保持；a1 的 inspection profile、packet 自报 owner、`inspection_sha256` 均不成为可信 policy、owner 或执行材料绑定。

## 1. 已固定的行为与当前身份边界

框架开发、结构重构和重要算法／数据／权限／验收变化先调研、设计并由单 owner 反复决定；最低题是项目与模板的并集，有理由的逐项 waiver 才能降低要求；新 revision 的受审材料重新明确批准，沉默不批准。继续采用原 plan、一次原批准、六阶段、原预算、原 journal 和原 cancel/fence。可信检查、一般 Repeat／混合画布是后继；训练并行不被本片接管。

当前用户没有宿主权限，coding agent 与 owner 共用当前 UID。源码中的 `_Approval.actor()` 只有 `unix:<uid>:<getpass>`；它识别进程操作者，不能证明自然人。`FileAdapter` 文档把文件系统 ACL 作为权威，但构造中的 `trusted_receipts:true` 只是声明，源码没有据此验证 coding agent 不可写。HTTP 同源头、TTY、页面按钮、`confirm:true`、JSON `human/role/actor`、同 UID 的私有目录或 chmod 都不能提升这一 assurance。

因此当前安装的新设计可信动作必须明确返回 **`human_channel_unavailable`**，包括 owner resolution、降低最低要求、适用范围豁免、最终 approve，以及以可信 owner 决定身份提交的 reject/withdraw。普通原 cancel 安全入口及旧任务合同仍保留；不得因为新身份检查而取消安全停止能力。Agent 建议、完整原文、`reported-human` 答复可保存，但不能闭合问题或生成可运行批准。状态应分别显示材料完整、知识供给、问题处理、actor assurance、批准投递、Workflow 接受、实际停止；不能把这些压成 `ready:true`。

这不阻塞代码开发：

|工作／证据|可以完成的范围|不能冒称|
|---|---|---|
|源码与新非 editable 安装|格式、持久身份、迁移、safe I/O、材料链、拒绝准入、恢复与进程竞态；当前安装的 unavailable 负例|可信人类已经批准，或新 profile 已可生产执行|
|可控 fixture|在原 owner／adapter／process 接缝内构造受保护通道事实，验证记录来源、两门一致性及正反路径；明确替换哪一叶|同 UID 环境获得了 OS 隔离；用测试 monkeypatch 或 JSON 字段启用真实批准|
|生产正向部署前置|复用原受保护本地 owner terminal／可信 receipt 发布边界；实际证明 coding agent 不能写或替换 receipt、journal、可信配置及其父目录，也不能以 owner 身份执行该发布路径；worker 只消费这些原件|仅检查一个目录 mode、UID 字符串、`trusted_receipts` 或本机配置布尔即可认证自然人|

最小建议沿原 terminal/receipt-volume 边界实现；当前 API／页面只有进程身份，不新增浏览器直接批准能力。不设计 SSO、签名服务或另一个身份账本。真实部署不能证明上述边界时仍 unavailable，保留材料导出／原 ID；不要求用户绕审批、清空历史、换项目 ID或扩大宿主权限。生产正向旅程单列为部署前置；代码片可以按其实际范围闭合。

## 2. 真实 owner、caller 与持久耦合

下表是主树观察，a1 修正版的不同处单独注明。函数落点用于交给实施者查原接口；后继冻结时重核行号与准确版本。

|owner／真实调用|当前接口与不变量|实施义务|
|---|---|---|
|[registrations](../../src/ergora/registrations.py#L145) `_prepare/register/_reserve/_finish/status/published_project`；CLI `project register/import/resume`、HTTP `register_project` 调用它|只有 registration 输入 v1；`_prepare` 去掉输入 `schema_version` 后保存 `registration.definition`，嵌套 `registration.schema_version` 仍为 1。原 intent 先落文件，再占 SQLite revision，再投影原生四文件，最后 result；`published_project` 明确只接受 v1。|v2 必须留下可恢复的版本判别，不能仅让 schema validator 接受新字段。冻结 policy 进原 definition/digest/intent，原四文件格式不变；status 是真实读消费者。已有四投影的 canonical 内容不可覆盖；仅增加 policy 也改变 marker，故 S1 不升级任何已登记 v1，空项目同样不豁免。|
|[State](../../src/ergora/state.py#L105) `_schema_v5/_MIGRATIONS/State.connect`；projects/bindings、任务、训练、web/CLI、executor/preparation 都是实际消费者|schema5，所有领域表以注册函数和触发器 fencing；已打开的旧连接也可能存活。`State.connect` 还核精确 `user_version`，旧 v5 服务连只读也会报不兼容。|schema6 只换原表 writer fences，不建讨论／任务表。迁移影响整个 control home，不能当成一个 registration JSON 的局部变更；正在运行的旧服务、准备 owner、executor、训练 owner 都需纳入迁移窗口。|
|[tasks](../../src/ergora/tasks.py#L37) `_definition/_budget_project/preview/create/prepare` → [creation process](../../src/ergora/reference_creation_process.py#L15)|definition1–7；5–7 在独立原生准备 owner 中先固定预算，再编译。应用结构校验已有 `contracts`。`_budget_project` 是预算授权前的真实准入点。|项目要求新设计时，必须在这两条创建路径的原预算／intent 前阻止旧 definition 降级；不能只拦新 CLI。scope 未能可信确定时不能由 Agent 自报 small-fix 放行。|
|[creation](../../src/ergora/reference_task_creation.py#L106) `compile/validate_record/published/publish/preparation/budget_run`；submission、executor 均消费|creation intent 固定 registration SHA、execution、project revision、definition 和七个原生文件。`validate_record` 比较**当前** registration SHA；`check_registration` 比较当前四文件；预算 prepare 也固定同一 registration。恢复不是脱离当前 registration 的历史读取。|新增 v8 时检查所有版本集合、可选 context、budget、native、inventory context 和容量，不只改 `wrap`。跨登记恢复须从精确旧原件取得原 registration，不能拿当前 head 补。|
|[submission](../../src/ergora/reference_task_submission.py#L29) `prepare/submitted/load` → approval/cancel|调用 `creation.published()`，expected 再绑定 creation SHA、spec SHA、registration SHA、execution 和原 run。unknown 保留原 ID。|registration 切换会传递到批准／取消，不是只有 create 受影响；不能把旧 submission 重绑新登记。|
|[task_envelopes](../../src/ergora/task_envelopes.py#L347) `wrap/unwrap/summary/issue_inventory_context` → [WorkflowInput factory](../../src/ergora/reference_inputs.py#L454)|admission 最大 v11；工厂拥有 queue、request root、adapter、SDK Workflow、job 和预算行为。`workers/request_roots` 只枚举 execution-enabled 实现。|v12 是最终正式版本；只在原工厂选择，不加上层 version==12 分派链。资料／schema／任务／admission 是不同版本轴。|
|[approval owner](../../src/ergora/reference_task_approval.py#L18) `_plan/_Approval`；`tasks.plan/approve/resume_approve` → [reference](../../src/ergora/reference.py#L745) `_task_operation`|原 history→envelope→receipt→完整材料；原 journal 为 `ergora/task-approvals/<task>/<decision>.*.json`。schema1 intent、receipt、attempt-before-signal、同 run 对账；`requested` 不等于接受。|材料提交／封存／决定在此 owner 内，不能另建 discussion DB 或 journal 基类。a1 r2 的完整 schema 校验在 `reference.task_plan` 应用返回边界；原生只读完整事实。|
|[adapter / Workflow](../../src/ergora/reference_workflows.py#L461) 与原 [approval](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/workflow.py#L120)|`DevelopmentWorkflow.approval` 传给 authorize 的 context **没有 admission**。批准后原 run 持局部 seed plan，`approved_plan.approval` 可携新 binding。|G1 必须从本版 request root 的唯一原 plan envelope 取得冻结 policy，并核其 seed receipt SHA 等于等待中的 plan；不能信 receipt 或 packet 自报宽 policy。不得复制六阶段 run 或重跑同 stage ID。|
|[executor](../../src/ergora/reference_executor.py#L35) `__init__/model/_declared_results/_composition_request`|`input.require_job_owner` 在原构造／claim 之前；`model` 使用 `agents.result_schema`，`stage_material()` 同时用于新材料与 saved formal-call 恢复比较；`_declared_results` 当前只传原 profile 声明的结果。|S1须在原business claim前对新登记v2拒绝旧输入；后继G2、typed packet schema、完整最终材料和恢复必须接实际 use sites。额外 design-packet 不加入声明传播就会在 work/review 丢掉；只改页面无效。|
|[BudgetedJob](../../src/ergora/reference_job_lifecycle.py#L117) `supervise/own/reconcile` → [processes.run](../../src/ergora/processes.py#L140)|body 与 collection 用同一原预算／原 attempt；停止见证后才 terminal。当前 should_stop 检查与 Popen 之间没有与 fence 共享的锁。|撤回最后准入要落在真实 Popen；collection/cleanup 不被业务 gate 阻断。unknown attempt 不再执行 body，不续 clock。|
|[cancellation](../../src/ergora/reference_task_cancellation.py#L18) `_Cancellation.run/dispatch/reconcile`|自己持 creation lock；首次 signal 前 attempt；已有 attempt 只对账。原 FileAdapter fence 只覆盖已枚举请求的 terminal，不证明进程子树停止。|父 withdraw result 后的尾部必须继续，远程 cancel 之前释放父 creation/admission 锁；不得把 requested 或 fence confirmed 写成实际 stopped。|

**必须解决的旧 creation 耦合。** 对同一个项目仅增加 design policy，原 registration digest／marker 就变化。旧 creation 仍持原 SHA，`_Creation.validate_record/published` 会拒绝；submission、approve、cancel 也受影响。State6 的 writer fence 不会解决这一文件耦合。当前没有“旧任务恢复自动豁免”实现，本文也不声称有。

最小 storage 首片只允许**真正首次统一登记**：没有既存 registration 或原生四投影。已有 control project 但从未登记，仍须沿原注册合同证明该首次登记边界；不能把已有 v1 的“无任务”当作可升级证明。原 `registration_io/_registration_main` 对已有四投影的不同 canonical 内容报 immutable conflict；新增 policy 改变 marker，不能为 S1 添加覆盖原件的例外。所有既存 v1→v2（包括空项目）在原登记 intent／reservation／native 发布前显式拒绝，原控制文档、journals、四投影零增量。同 ID／同完整意图的首次 v2 中断恢复沿原 resume，不当作新登记或升级。

这一限制是 S1 的迁移边界，不是旧项目永久不能升级。F 在实际升级前必须给出一份独立、可验收的原生 marker／四投影迁移合同：固定精确旧／新登记原件与 digest、发布／中断／恢复顺序、旧 creation/prepare/submission 的历史登记选择与当前四文件核验，以及外部 config/state 的一致恢复。仅找到旧 registration journal 不能使当前 `check_registration` 自动接受它。未完成此前，既存项目保持原版本，不清空历史、换 ID、重写 intent、忽略 registration SHA 或换当前 head。

## 3. 顺序：先交真实 storage 片，执行只在完整闭合后开放

建议将原 a2/b1 的实施工作拆成以下顺序。S1、满足真实读写消费者的 S2 可以独立交付；F/J/G 是同一个最小可执行闭环的实施分区，不能把其中一个局部 helper 通过写成 a2 或 b1 已完成。若格式分区没有独立的 storage/read consumer，直接留在闭环内，不能为凑片创建空类、临时 profile 或另一套 state machine。

|顺序|小片／明确依赖|独立可验结果与关闭条件|
|---|---|---|
|A|a1 最终修正版，先完整闭合并固定|真实应用→所选 native 解释器读 packet；schema 留应用；inspection-only。无 packet 旧结果不变。本文不替它结片。|
|S1：最小下一片|registration2＋State6＋原 status 读回＋新任务降级拒绝；依赖 A 的最终格式边界|能登记、恢复、完整读回冻结 policy，旧 writer 被阻止；新设计项目创建尚不受支持时在原预算／intent 前明确拒绝。**不注册可执行 v12，不产生设计批准，不改模板默认。** 仅按上述真正首次登记 eligibility。受管 executor 在 claim 前拒绝该 v2 项目的旧 spec/job；原 standalone stack 的停用／隔离是部署前置。|
|S2：原源记录 storage|依赖 A；与 S1 接最终版本合同。原 approval owner 内 publish-design／record-response／operation/read/resume，读完整源链；最小 CLI 调同 tasks 用例|同 ID／原正文恢复、两轮完整原文和 parent SHA 可读；Agent／reported-human 不闭合 Q，未冻结 policy 的旧 admission 仍 inspection-only。原 task plan / design read 是真实消费者。没有真实入口与读回就不能把“存了文件”算单片交付。|
|F：最终出生与恢复|依赖 S1；definition8/admission12 完整冻结、初始 packet 生产和原材料传播；原生 marker／四投影迁移、外部根一致恢复及原项目跨 registration 恢复|各格式／原件／budget/context 的真实 creation 和离线读取可核。若独立交付 storage-only，必须有真实 creation/read consumer、显式拒绝所有 submission/dispatch/job，worker 与 request-root 枚举排除它，且不得留下假的 Workflow/adapter 实现。否则连同 J/G 交付。|
|J：b1 最小权威源链|依赖 F 冻结 policy/owner；复用 S2 的同一原 journal。owner assurance、逐题处理、完整材料身份、prepared seal／废弃、reject/withdraw 原尾部|真正 frozen policy 与 committed source 产生同一 materials SHA；无可信通道明确 unavailable。两轮、并发、封存与撤回原 operation 恢复可核；尚无 G1/G2 完整接受时不开放 v12。|
|G：a2 原双门与最后启动|依赖 J；G1 authorize、G2 adapter/executor、完整 work/review 材料、原 budget 和 admission 短锁|绕 API／原 signal／旧 receipt／旧 binding 仍拒绝；合法受控 fixture 能由原完整链进入同一 work。只有 F＋J＋G 全闭合并有实际可用 owner 通道时才开放最终新 profile；当前环境继续 unavailable。|
|交互与真实部署|同一 tasks 用例扩 HTTP／console，再做有真实隔离通道的小型旅程|统一能力、材料 SHA、原 ID 与 unknown；页面不持第二权威。无可信部署的当前环境只可验负例／导出，不假称真实人类正向旅程完成。|

S2 允许在有 a1 packet 的旧任务下保存来源，唯一效果是讨论材料可审、可恢复；没有 frozen design policy/owner 时不能形成权威 resolution、seal 或 runtime readiness。后继新 task 引用这些原文时是来源复用，必须以新 creation/admission/seed 重新绑定，不继承旧自报 owner。无 packet 的旧 plan 和普通 schema1 批准路径不增加本功能字段或要求。

F 的可执行支持必须使用最终 v12／definition8，不能先注册一个能跑旧批准的 v12，再补 journal 或 G2。禁止把 a1 `inspection_only/runtime_enforced` 布尔翻转成执行 policy；其已发布字节保持。S1 保存的是正式设计 policy 的配置／要求及 SHA，status 可用它展示最低项和拒绝旧创建；它不授予身份或执行权。需要随包发布执行 companion 时使用明确独立、最终的资源身份，待完整闭环核验，不能给临时 profile 验收后偷换内容。

### 3.1 S1 的具体实施交接

真实修改 owner 是 `registrations.py`、`state.py`、`tasks.py`、`reference_executor.py`、`data/schemas/project-registration-v2.json`，以及这些行为的原测试；只有实际 caller 需要才扩 `reference.py` 的原 registration/native 观察。CLI/HTTP 已向 `registrations.register` 传完整 definition，无需另建服务。

1. 应用 `contracts.validate` 依据显式输入版本选 v1/v2 schema。v2 加完整 `design_policy`：policy/profile 原对象与 canonical SHA、owner 来源要求、适用类别、最低 Q/K、容量／时效。最低项 namespace 和并集、同 ID 异内容冲突由 registration/domain owner 核，不由后者覆盖。`owner_id` 和 `required_actor_assurance` 是要求，不是已证实身份。
2. 建议嵌套 `registration.schema_version:2` 保留持久判别，项目 document schema1、原 registration journal 的 source/before/after 容器不必另开版本；新 reader 按嵌套版本选择定义 schema。`_prepare` 当前删除输入版本，必须一并修 `published_project/_finish/resume/status`，防止恢复把 v2 重建为 v1。实际字段随冻结 schema 固定，不添加第二 registration 文件权威。
3. policy 进入原 definition SHA、marker definition SHA、原 intent/result；原 scope/policy/project 三个 native 投影及四文件布局保持原合同。`status` 返回冻结 policy 身份、版本和当前 unavailable/未支持能力，不能只说文件 matches 就称可执行。
4. `_definition` 与 `_budget_project` 两条出生路径在原预算授权、prepare/create intent 前消费项目 policy。新受管任务不得降选 definition1–7；缺可信 applicability 分类时保守拒绝，不能 Agent 自动判小修。恢复入口不是新出生，不用该 guard 改旧任务合同；本首片尚无既存任务跨 v2 升级。

   同一拒降级也接本版 `reference_executor.process → Executor` 的**原 business claim／prepare／副作用之前**：从实际 native project 与原 State/登记绑定取得权威 v2 policy，即使输入来自旧 request root、`composition=None` 或旧 native CLI 的合法 spec/job，也不能执行新业务。不要仅在未来 v12 的 Input hook 或 API 拦截，不复制 application schema 到 native。沿现原构造的项目查找／共同准入位置做最小调整，保持旧 v1 项目与其原 frozen selection／恢复；无可信原登记不能靠 payload 自报小修、旧任务或无 policy 获豁免。S1 不支持 v2 既存旧任务豁免；F 后继只凭精确旧 creation/prepare/registration binding 增加它。

   原 standalone worker/executor 不加载上述本版 guard，不能由 S1 宣称受控。v2 发布／启用前，部署者须沿原 service owner 确认旧 stack 已停止或隔离；原 `services` 的 legacy socket 拒绝可复用，但不是所有独立进程均已停止的证明。无法确认时不部署执行 stack，只验隔离 control home 的存储／拒绝路径；不改283参考，不替其他 owner 停训练。
5. State6 沿 `_schema_v5` 的语义迁移模式为原所有领域表更换 triggers，不改表布局／历史 JSON；原 migration 事务、预升级 backup、完整 restore 沿用。v2→v1 或无可信 owner 的 policy 降低不能成为默认注册覆盖路径。S1 未实现这类权威变更时显式不可用，不能悄悄丢字段。
6. 源／安装验收在隔离 control home，禁止顺手迁移用户当前运行 home。真正部署前先盘点并协调所有旧 web/CLI scheduler、native preparation/executor、训练 owner 对 State 的使用，停止新写入并让已授权生命周期安全收尾；`.schema.lock` 不替代这一步。不得为 WA5 停掉另 owner 的训练。旧连接 fencing 的失败可能影响结果／清理，必须在受控 fixture 观察，不拿线上试。
7. 明确三种恢复：State6 失败只承诺原 DB 事务回滚；原 offline backup/restore 只恢复其 inventory 内的 **control home**；v2 发布后的跨根部署回退／软件降级尚未支持。State 自动迁移前 backup 更只覆盖 DB，不能当整机快照。外部 `execution.config_directory/state_directory`、marker、receipts/fences/journals 不自动在原包内；保留迁移后原件用于同版本恢复，不能把旧 control home 还原后称外部 v2 投影也已还原。不得手改 `user_version`、删 trigger、用 v5 writer 写 v2 policy，或覆盖原 fence。外部 config/state 协调快照、精确原登记与四投影的恢复顺序、中断与失败行为与 F 的 marker 迁移一起单独设计；S1 不扩通用 backup 服务。

   失败迁移须原 schema5 与原行字节保持，成功迁移的旧 writer（含先打开连接）写失败；合法新 client 的旧 v1 项目、任务及普通批准／取消仍按原合同。原 backup 回归保持，并明确外部目录未入 inventory 的实际范围；只有未来实际执行完整 v2 发布→多根恢复→status/creation/停止一致性后，才能报告部署回退通过。

S1 不需要新 ABC、plugin、policy service 或通用 registry；单用途的 version 选择／eligibility 留在 registration owner。真实 consumer 为 status／原恢复、tasks 新生准入与受管executor pre-claim拒降级，不能把未实现的 G1/G2 列成已存在 caller。

## 4. 应用 schema 与原 native 依赖必须保持分界

`reference._task_operation` 使用注册安装的 `.venv/bin/python -P`；creation 使用 `-P -S` 的独立进程。原 native `requirements.lock` 固定 127 项，没有 jsonschema。后继不得改该锁／283 参考来补依赖，也不得在 native 复制 JSON Schema validator。

- 应用入口使用现 `contracts.StrictValidator` 校验外来 registration、definition、packet/profile、response/resolution/operation 结构；按真实版本和配置上限校验。读返回也在应用发布公共结果前校验，a1 的内部 `design_read` 不透出为已验证能力。先做规范 JSON／UTF-8／finite 输入处理，禁止客户端 actor/role 等字段。
- native approval/creation/adapter 只用标准库原 frozen-record identity 与领域规则、安全路径及受限读取。源提交必须先经过应用完整结构校验，再由原 owner 在锁内核原件与准确字节并 commit；不接受传输 `validated:true`、孤立 ready 文件或 packet 自称可信。
- G1/G2 在无 jsonschema 的原 native 路径验证受保护 committed 原记录、完整 SHA、冻结 policy、seed、owner binding、seal、撤回及预算，复用纯 `task_design` 的就绪／身份规则。它们不能因为 API 查过而省略检查。遇到未提交、缺原件、格式／身份损坏即拒绝，不把不可信的初始 packet 直接变成 approved 链。
- 新共享纯函数须有届时真实的 application、authorize、executor 消费；文件 IO／锁／SDK 仍在原 owner。单 caller 的源链扫描、取消尾部留 `reference_task_approval`，不抽通用事件平台。需要少量结构 guard 是为安全读取和拒绝损坏记录，不是再实现 schema。

验证至少保留 a1 修正版的**应用→注册所选解释器→真实 main→原 _Submission/_plan→安全文件读→应用 schema** 接缝；受控服务叶可替换，不能把整个 `_task_operation`、main 或 `_Submission` 换掉后宣称原 native 依赖通过。source 导入与安装导入、SDK fixture、原锁真实环境分别记账。

## 5. J 必须一次具备的原 journal 最小不变量

这些是不开放临时可执行 v12 的原因。S2 可先交无权限升级的材料存取；有权 resolution／approve 前，下列最小合同必须全部存在。

|不变量|原 owner 内的最小落实／可观察失败|
|---|---|
|唯一源与提交点|仍是 `ergora/task-approvals/<task>/<operation_id>.intent/result.json`，源正文仍在原 artifacts/design 树。source operation schema2 与旧 approval schema1 显式区分；同 ID 不能换类型／正文／run／seed／parent。正文先不可变发布，最后 result commit；未 commit 正文不改变 ready。仅批准／取消有 attempt 和原 signal。|
|完整原文、两种 revision|packet revision 与 material revision 分开，seed receipt 不含自身 SHA。packet 内容、完整 Markdown／HTML 原件、Q/K、原 answer、resolution、来源状态、验收及 policy 都入精确 materials identity；不能用 a1 inspection SHA 或报告单文件 SHA 代替。typed ID、报告 media type、source body 字节均沿 a1 已修规则。|
|唯一链与有界读取|从已知该 task 目录的 committed 记录按序号／前版 SHA 重建；配置记录数、聚合 bytes、revision 上限，不按 mtime 取最新，不修补分叉／缺件。GET 不落记录、发 signal 或自动恢复。损坏、同序号分叉、body 不可读给精确 unknown/blocked；没有第二 mutable head／current-approved 权威。|
|权威与就绪|project＋template 最低项并集固定在 admission；Q1 回答不消除 Q2。denied/conflicting/stale/reference_only 不自动 supplied/waive。resolution 逐 ID 保留原要求、理由、条件／期限及真正 actor；reported-human 原文不会升级。未冻结 policy 或当前 channel unavailable 时保留缺项，不产生批准。|
|seal 与废弃|原 approve schema2 intent 从 prepared 起封存精确链。未 attempt 时只有明确 owner request-revision 才能追加废弃；旧 intent／receipt 保留，dispatch/resume 核失效并拒绝。attempt 后 unknown 先原 run/history 对账，不能换 decision ID 或开新 head 绕过。final approve 后不能同 run 改受审材料并复用旧 work ID；需 withdraw/stop 后新 task 的新授权。|
|原预算与冻结执行字段|所有等待、讨论、恢复用原 clock/work cutoff/approval timeout，不重开准备、不续 receipt、不多领 model slot。baseline/starting SHA、manifest、路径、work unit IDs/依赖、权限、预算等改动返回具体 `requires_new_task`；不能在 source 提交里重写原 spec/composition。过期后读回仍保留历史事实，不能因当前 freshness 重写旧决定。|
|锁与副作用|本地源提交沿 creation lock，project revision reservation 只包有界准备；不持控制 DB 等网络。source／approve／request-revision 串行，seal 后迟到 source 失败。原 signal 的 attempt-before-send 保持；ack 只叫 requested，Workflow query/history 才能判断 accepted。unknown 不自动重发。|

safe I/O 复用原 `safe_file/read_raw/publish/_Creation.document`，按规范相对路径、普通非 symlink/reparse 文件、无跟随、有界 UTF-8 完整读，引用只来自固定 roots。先核 source ID 唯一再做 IO，不能覆盖第一份观察。明确区分 raw file SHA、canonical JSON SHA、manifest tree digest。容量超限失败或拆任务，不能截断后批准。需要对 commit/fence 宣称持久时，须同步并重读同一现存文件与父目录；原 `publish` 只 fsync 临时文件，不能据它宣称 link 所在目录已持久。只为新保证在原 owner 的实际 use site 补持久确认，不全局改写冻结 publisher。

### 5.1 reject／withdraw 的同一操作尾部

父 schema2 intent 在本地决定提交前固定原 project/revision、run、seed/materials/approval、actor/reason、唯一原 cancel 子 request ID 及完整预期 payload／SHA。已保存父 result **仅表示 decision committed**。

1. 同 ID mutation 或显式 `design resume` 从同一父 intent 继续；GET 只报告 `decision_committed` 与 `stop_effects`，不能因父 result 已有就早退。
2. creation→admission 短锁下发布原 `fences/<task>.json`，核 task/request 完整原字节，同文件及父目录同步、重读；冲突／损坏不修，不造第二 stop 文件。可见未证持久时保守阻断新 body，公开 durability unknown；完成该原 fence 确认才报告撤回线性化点。
3. 释放外层 creation/admission 锁后，才进入原 `_Cancellation` prepare/resume（它自行取同 creation lock）。子 intent 必须等于父固定 payload／SHA；不能读取当前 head 重算 actor/reason/run，也不换子 ID。原件漂移而不能恢复时保留 fence、明确 unknown/blocked。
4. 子尚无 attempt 时显式 resume 可以首次 send；有 attempt 只原 reconcile，丢回复不再发。沿原 cancel result/closed/history 读回，不启动第二取消控制器。决定、fence、cancel intent、attempt 任一后崩溃都能从同一父 ID/intent SHA 定位唯一尾部。
5. 停止显示动态读原 fence、原 cancel 原件、job supervisor/reaping 见证；不另写权威 `stopped:true`。已经在 fence 前准入的 stage 仍属在途子树，必须实际停止／回收；requested、ack、终态 Workflow 或可枚举 job receipt 均不能单独证明全部后代已停。

## 6. F／G 的完整生产接线

F 固定 definition8 与 admission12：原 six-stage＋完整 budget，selected context 仍可选，不能强迫选 memory/Skill 才能设计。完整设计 policy／SHA、单 owner 要求、可信 applicability 引用从原 registration 和完整模板取得，不能从待审 packet、当前 project head 或 approve JSON 取得。原 creation/prepare/journal 版本各自保留判别，原 spec/request v2／native profile 不改；`task_envelopes` 验 frozen manifest/budget/context/design 关系，最终 factory 才拥有新 queue/request root/adapter/workflow。首次 plan 额外产 dict 型 `design-packet`；原三份字符串 artifact 保持。初始 committed source 绑定唯一 seed，不重跑 plan stage。

跨 registration 的后继恢复须先给真实实现方案与反例：新出生可固定原 registration operation/完整 intent SHA；旧 creation 没有该新引用时只能核同 control home 下的精确旧 published 原件与其原 project/revision/SHA/四投影，不得补写旧文件。若发现多个可匹配原件或原件不可达，拒绝并保留旧状态，不猜最新。旧读取、submission/approval/cancel/reconcile、budget preparation、executor `task_creation(...,'published')` 都是实际消费者；不能只让 `tasks.show` 过关就宣布迁移完成。这项验收未完成时，S1 eligibility 限制继续，不能更新有历史项目来试。

G1 沿原 `tasks.approve → reference.task_approval → _Approval → approve_plan → dev_authorize_plan`；新入口显式 materials SHA，不隐式替人选当前材料。prepare 不就绪／无可信 actor 时 approve intent、owner receipt、attempt、signal 计数都不增加。schema2 intent 绑定原材料及通道，原 schema1 plan-approval receipt 只加 design_binding，由原完整 receipt SHA 覆盖。

真正 `DesignAdapter.authorize` 不能假设 context 带 admission：从可信构造的原 state 根和 v12 request root，以 task＋原 stage 算法取得唯一 plan envelope，核 envelope/context/admission/job 的完整身份；由其 frozen admission 取 policy/owner，再核 seed receipt SUCCEEDED、原 artifacts 和 canonical receipt SHA 与 authorize 的 plan SHA 同一。读同 committed 源链、seal、binding、预算／fence，最后才调原 `super().authorize`，返回相同 binding 进入 `approved_plan.approval`。内部自洽但换宽 policy／owner 必须失败。

G2 同时接三处实际行为：

- adapter `validate_submission` 在 work/integrate/verify/review 发布前核同 approved binding、封存、撤回、预算／fence；绕应用直接原 signal 也不能发布错误 work。
- executor `input.require_job_owner(envelope)` 在原 Executor claim／prepare／业务动作前核同完整链；不能只核原 schema1 receipt 必需字段。结果 schema 扩展和新增 artifact 声明由原 input 合同提供，`model/_declared_results/_composition_request` 的真实 use sites 消费；完整最终 packet、有效原答复／resolution、验收与来源状态进入实际 work/review leaf，saved formal-call 恢复比较也包含它们，不能只递 SHA/当前链接。原 producer 对完整 approved_plan 的比较继续。
- `BudgetedJob.supervise('body')` 经现 input 的窄 `job_start_guard` 把同任务 `.admission.lock`、原 fence/binding 最后检查传给 `processes.run`；只包停止检查到真正 Popen，启动后释放。锁序 creation→admission，启动 guard 不回取 creation；原 budget 再核，collection/cleanup 不受业务 gate 阻断。旧 input 用无附加 guard，保留原退出／reaping。该参数只有原 supervisor 一个真实 caller，理由是 Popen owner 拥有原子启动区间，不抽 generic hook/plugin。

只有这些真实 caller 都消费最终合同，才注册／启用最终 v12。当前安装仍须因 human channel unavailable 拒绝可信批准，不能用 full gate 代码已存在推断通道已可用。

## 7. 逐片客观接缝与验收账本

下面是**待执行**验收，不是本次结果。沿既有测试文件／fixture 扩必要反例，不新开重复 CI job，不为每字段复制同义矩阵；参数采用至少一个非默认有效配置并核关系。

|片／真正风险|最小原接缝与必须观察|证据限度|
|---|---|---|
|S1 版本／writer／恢复|`test_registrations.py` 原 register/status/resume/完整 published journal＋`test_state_migrations.py`、`test_state_backups.py`：首次v2 policy 原字节/SHA和原四文件；v1恢复保持；已有空v1及有旧creation的v2升级均在intent前拒绝，原控制／journal／四投影零增量；schema5已开连接写拒绝；迁移失败事务回滚／control-home backup范围、外部根未入inventory明确。`test_task_creation.py`／`test_task_budget.py` 两条路径拒降级，预算与 intent 增量 0；原 `test_composition_executor.py` 保留真实process/Executor pre-claim，用原合法legacy spec/job的新v2项目拒绝与旧v1对照，claim／body／model／可信命令starts=0。|源与安装分别验；fixture 不迁移当前运行 home，不证明旧服务在线升级／standalone停用或跨根部署回退安全。|
|S2 源提交／原文恢复|`test_task_plan.py`＋`test_task_approval.py` 原实际 native 主边界：两轮全文、同 ID 同字节、不同字节冲突、正文后/result前中断、GET 无写；超限不截断、重复 ID、危险路径／非普通文件、report media type；Agent／reported-human Q/K 不闭合。|原 approval fixture 会替换整段 main argv，适合旧恢复保护，不能单独证明新 native 依赖／actor。新跨进程例只替换无关服务叶，保留 main/_Submission/原文件链。|
|F 冻结／旧登记耦合|`test_task_creation.py`、`test_task_budget.py`、`test_task_inputs.py`、`test_composition_runtime.py`：v8→v12原 budget/context/design 同一；改 frozen 执行字段 requires_new_task；精确旧 published registration 与旧 creation/prepare/submission 连续恢复，错／缺原件拒绝；两 project 互不阻塞。|storage-only若交付，直接 start/dispatch/raw job 均不能发新工作；不把 shape 通过写成正式 Workflow 正向。|
|J 权威／seal／unknown|原 approval/plan/native seam：Q1/Q2分离，最低并集与有理由 waiver，缺 frozen policy／同UID/config human unavailable；prepare/source/request-revision并发只有一条链；prepared失效不能resume；attempt丢回复只查同run完整signal、不重发、不续期。|身份替身只认证取 actor 的位置和拒绝行为；真正 protected terminal/ACL 另验。|
|G1 原真实加载|`test_composition_runtime.py` 原 `approval→dev_authorize_plan→adapter`：从实际 plan envelope 取 policy；换宽 policy／owner、错 seed／root、无 binding、旧 receipt、withdraw 全拒绝；受控合法 binding 接受。|只给 pure helper 传正确 policy 或断言 API 报错不覆盖 G1。|
|G2 消费／恢复|`test_composition_executor.py`、`test_composition_invocations.py` 原 Executor/claim/正式调用：直接旧批准／错 binding 的 work body/model/可信命令 starts=0；合法受控链的 work/review 实际完整材料与批准 SHA相同；重启沿原 formal-call，不多领invocation。|源码字符串／mock execute 返回不认证实际输入；真正服务与模型另列。|
|withdraw 尾部／最后spawn|`test_task_cancellation.py`＋`test_budget_jobs.py`＋`test_processes.py`：父result/fence前、fence/cancel-intent前、cancel-attempt后真实中断，同父ID恢复原子ID；外层锁释放；fence前已准入子树实际回收，fence后新body starts=0；停止未知明确显示。|JSON写成功不是撤回生效／实际停止；须真实锁与进程，不借旧stop helper pass。|
|旧行为／原资源|受影响原 v1–11、普通批准／取消、无packet plan、schema1 journal/完整history、283参考字节／执行位、原127锁及旧manifest保持；State6新client在旧v1项目的实际 operations 按范围复验。|不重跑无变化训练/GPU；M5/M6、旧wheel、旧CI通过不转授。|

每个可独立交付片固定准确 source/diff/完整输入；源码检查完成后构建新的非 editable core/SDK，核实际 site-packages、完整包／资源／依赖身份，再沿相同真实入口验安装。依既有授权运行自身原结构模板、新 fresh 需求／维护性审查；原失败保持。版本／fixture/源码、安装、真实原锁 native、SDK受控、真实服务、真实人类通道、发布及候选自己的 CI 逐项记账。只读文档检查不产生任何实现通过。

当前环境可真实验 `human_channel_unavailable` 及完整材料导出；真实人类正向旅程等待可证明的原 protected terminal/receipt-volume 部署。到时以普通 CPU 小仓库、原总预算，验必要知识精确提问→两轮原答复/修订→明确最终批准→真实 work 收到完整材料；另验 reject/withdraw/丢回复恢复。不借 Agent 自动写“用户已同意”或模型 verdict 关闭该前置。

## 8. 本次范围与交接

本次只读根/src/tests AGENTS、PLAN、组件协议、maintainable-project-delivery、ergora-codebase-quality 的 module-design/test-seams、D1–D4、已审 r2、a1 交付及其当前必要接口，以及表中真实源码／现测试。只运行必要读取和轻量 Git；没有测试、安装、服务、网络、模型、训练、源码编辑或提交，没有读 shell 配置、inference 配置、环境快照或凭据。唯一写入为本文件；PLAN／delivery 由主控统一更新。

**最小下一片是 S1**：先等待 a1 最终修正版准确闭合，以新的 fresh 设计审确认本拆片，交付 registration2/State6 的真实 storage/status/恢复与新任务拒绝降级；只在真正首次登记验；所有已登记v1含空项目均拒绝升级，受管executor同时pre-claim拒旧输入。control-home恢复与外部投影回退分列，不开放执行。既存项目跨登记恢复、可信 owner 部署、b1 最小权威源链与撤回尾部、a2 G1/G2/Popen 最后准入都是明确后继；任何一项未验不能冒称旧任务恢复豁免或新设计关卡已可运行。

## 9. 新 fresh 设计审的同片修订

[独立设计审](../delivery/2026-11-16-design-gates-registration-and-journal-design-review.md)原三项 finding 保留。r2最小处理：R1明确首次登记，拒绝所有已有v1升级，不新建marker覆盖接口；R2把现有受管executor的legacy实际准入纳入S1，在claim前拒绝，原standalone stack切换单列部署义务；R3把DB事务／control-home恢复与外部根部署回退分开，后者连同F的marker迁移另给完整合同。上文owner、顺序、S1步骤与矩阵已同步。修订只是设计，不表明实现或旧项目迁移已通过；待原reviewer同片复核，A最终闭合仍独立核。
