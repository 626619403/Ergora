# WA5a／WA5b：设计、必要知识与原批准关卡的实施设计

2026-11-16；**仅设计，未实施，未开放新关卡**。本稿待新的 fresh-context 独立设计审查；它不是任何 task／candidate 的批准。读取时基线为 `debf6f96ed02620d22adc0ac6385c72641b3d53b`，分支 `refactor/architecture-foundations`。工作区已有 M5／native 依赖隔离及交付记录的并行差异；本片只新增本文件，不接纳那些未完成差异为 WA5 的验证。后继实施重新固定基线与实际 diff，不能沿用本稿的源码身份作运行验收。

权威输入为[原始需求](2026-11-15-workflow-evidence-and-human-gates.md)、[WA4详细方案](2026-11-15-workflow-design-and-execution-evolution.md)、[WA1研究复用审计](../delivery/2026-11-15-workflow-research-reuse-audit.md)、[WA2运行能力审计](../delivery/2026-11-15-workflow-runtime-capabilities-audit.md)、[WA3设计知识审计](../delivery/2026-11-15-workflow-design-knowledge-audit.md)，以及用户刚明确的[D1–D4](../delivery/2026-11-16-workflow-design-decisions.md)。旧方案里“待用户回答”的三项已由该决定记录覆盖；没有因此批准本实现方案或任何运行材料。

本稿r2技术修订补齐[首轮独立设计审查](../delivery/2026-11-16-design-knowledge-gates-design-review.md)的R1／R2：G1从原plan请求取得冻结policy、拒绝／撤回的固定原cancel子请求与崩溃恢复。首稿48,196B／SHA256 `85e56e7096667ff44f3ef9441b6f5b85084b5431fe8ab37466068bba4ce6eb4a`及其request-changes保持原范围；r2待同片复核。没有新产品决定，没有实施或运行验收。

## 1. 已决定的产品行为与本片边界

- 框架开发、结构重构、重要算法／数据／权限／验收变化，在新 profile 内强制完整设计。普通小修按项目规则。旧 profile／manifest／冻结任务维持原合同。
- 一个任务 owner 决策。项目和模板给最低必答项，owner 可追加；免答、降低要求、接受有边界假设必须有 owner 的明确原记录。Agent 可以提出资料请求、问题、方案和修订，不能替人闭合它们。
- 设计正文修改产生新 revision。新材料没有旧批准；重要变化必须重批。第一版采用更容易核验的保守规则：任何受审正文／typed 字段／答案或来源引用变化都需新 revision 和新 approve；只有根据相同原字节重新渲染 HTML／折叠布局不构成材料变化。没有由 Agent 主观判断“非重大”来延续批准的分支。
- 实施顺序为 WA5a/b → 可信脚本／测试节点 → 一般 Repeat／混合画布；已授权训练循环并行收尾。WA5 不新增调度器、一般 registry、第二批准账本或 LangGraph 引擎，不改 283 份冻结参考原件，不把训练候选 release 变成设计批准。

机器只校验**已声明**的必要项、来源身份、答复和决定之间的关系。它不能证明所有公司知识均已发现，不能判断设计是否合理，也不能证明人已经理解；这些仍由真实 owner 阅读完整材料并明确决定。`ready:true` 不是 `approved:true`。本文、D1–D4、模型 approve、聊天总结或后端原生 review 都不能成为运行批准。

## 2. 当前生产接缝：先固定事实

|现有 owner／真实路径|观察到的合同|本设计的约束|
|---|---|---|
|[tasks.py](../../src/ergora/tasks.py) `_definition`、`_budget_project`、`prepare/create` → [reference_creation_process.py](../../src/ergora/reference_creation_process.py) → [reference_task_creation.py](../../src/ergora/reference_task_creation.py) `_Creation.compile/load`|TaskDefinition 最大 v7。v5–7 已先授权总预算、监督准备，再冻结原 spec、完整 composition、bindings、来源和 creation intent。|从新 definition v8 出生；不写回旧 task.spec.json，不让上传设计改变原 request／预算。|
|[task_envelopes.py](../../src/ergora/task_envelopes.py) `wrap/unwrap` → [reference_inputs.py](../../src/ergora/reference_inputs.py) `execution_input/_INPUTS`|formal admission 最大 v11；WorkflowDefinition v1/v2、TaskDefinition v7、原 request v2 是不同版本轴。`WorkflowInput` 拥有 workflow、queue、request root、adapter、job 和模型预算的构造合同。|新增 input12 在原局部 `_INPUTS` 注册。传输和 executor 不增加按具体类型的分派链。原版本1–11保持。|
|[reference_workflows.py](../../src/ergora/reference_workflows.py) Composition→Budgeted→NativeSixStage→SelectedContext|v9 的 `remaining/call/run_spec/stop` 持原预算；v10/v11仍走原六阶段。|v12继承此执行／预算；只扩原 plan 关卡和准入，保持六阶段。|
|[原 DevelopmentWorkflow](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/workflow.py) `run/approval/context`|`inventory → plan → approval → units → integrate → verify → review`。`plan_sha256` 是完整 plan receipt 的 canonical SHA；job ID 按 task+stage 固定。`run` 在 approval 后还持局部 `plan` 变量。|不能在 `approval()` 中重跑同一 plan stage、换 `results['plan']` 就宣称整个 run 换了 plan。也不能复制一份六阶段 run 来解决设计修订。|
|[reference_task_approval.py](../../src/ergora/reference_task_approval.py) `_plan/_Approval`|完整原 history→plan job→request envelope→receipt→原字节；每项262,144B、聚合1,048,576B。journal在 `ergora/task-approvals/<task>/<decision>.*.json`，attempt-before-signal；unknown沿原 history，不补发。|完整读取、审批和设计修改都归这个 owner；材料摘要和原 journal 不另造。|
|[原 FileAdapter](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py) `authorize`、[原 Executor](../../src/ergora/data/reference/platform/local/agent_platform/executor.py) `__init__`|原 authorize 核 schema1 plan-approval 的要求字段、可信 human/owner、期限和 non-revoked；允许额外字段，摘要绑定完整 receipt。Executor核 approved receipt、批准SHA／revoked后才 claim。|保留原 plan SHA 和授权器；新 receipt 可附设计绑定。v12不能仅凭原 schema1必需字段放行。|
|[reference_executor.py](../../src/ergora/reference_executor.py) `_declared_results/_preparation_results/_composition_request/model`|plan取得完整 inventory；正式叶保存 schema、输入、prompt、result和原资源。`_composition_context`保留 approved_plan，work/review生产者核完整 approved_plan同一。|最终设计必须进入真实 work和review材料，不能只加批准页面或藏在journal；保留源身份／独立session。|
|[reference_job_lifecycle.py](../../src/ergora/reference_job_lifecycle.py) `BudgetedJob.own/supervise/finalize`|原budget attempt、同次进程监督、fence、停止见证及terminal owner；unknown不重执body。|撤回走原停止；准入拒绝与进程已停是两个观察，不混写。|
|[State](../../src/ergora/state.py)、[registrations](../../src/ergora/registrations.py)|SQLite schema5；项目registration文档在原projects表。注册发布已有intent／revision／原生四文件；没有正式task表或讨论表。|新项目策略语义若持久进project，需writer fence迁移；不为设计问答新建task/approval表。|
|[CLI](../../src/ergora/cli.py)、[HTTP](../../src/ergora/web.py)、[console/tasks.js](../../src/ergora/data/console/tasks.js)|同 `tasks.plan/approve/resume_approve/cancel` 用例；页面approvalDialog读全材料、保留ID／迟到响应代际，unknown不自动重试。当前同源请求头不是人类身份鉴权。|领域状态只一份；页面不得提交 `principal_type:'human'` 来生成可信人类身份。|

现成库足够：原 `contracts.StrictValidator`／jsonschema处理结构，`task_envelopes.identity`／原 canonical SHA处理JSON，hashlib处理原字节，原safe_file/read_raw/publish处理可信文件，State/file_lock处理事务及锁，Temporal处理原计时／signal/history，原processes处理停止。无新依赖。原 registry 的 load_profile 按 task_type/task_version读取冻结目录，原Executor还会重核；故本片**不把新字段塞进旧native profile或替换load_profile**。

## 3. 版本与项目规则：companion profile，而非改写旧profile

提出四条显式版本轴：

|格式／资源|新版本内容与消费者|旧缺省／恢复|
|---|---|---|
|`project-registration-v2.json`（拟新文件）|保留v1字段，加 `design_policy`：完整profile对象及SHA、单owner来源约束、适用change kinds、项目最低问题、项目附加必要资料、容量与时效策略。`registrations._prepare/publication_files`冻结到原registration intent与project document。|v1不自动启用。v2注册是显式项目修订；原native四文件结构不变，既有registration marker的definition SHA自然包含v2策略。|
|`task-definition-v8.json`（拟新文件）|基于v6的完整six-stage与budget；可选v7同合同的selected context。必需 `design:{protocol:'design-knowledge-v1', profile_sha256, change_kinds, owner_id, applicability_record}`。`applicability_record`是可信owner对范围的明确记录引用，模型分类仅作建议。|不改变1–7语义。不把选了memory/Skill作为启用新关卡的必要条件。强制新profile的v2项目拒绝为新受管任务降选旧definition；旧已出生任务的恢复豁免沿原creation身份。|
|formal admission v12、`ErgoraCompositionWorkflowV12`|原spec/composition/budget＋可选原context/issue_source＋完整 `design_profile`、SHA和owner/applicability binding。queue `.composition-v12`、request root `-composition-v12`；在原input factory注册。|v1–11工作者和目录保留；旧writer不认识12则显式拒绝，不按v11猜读。原selected context仍首次冻结、恢复读原资料。|
|`task-design-v1.json`（拟新文件，含$defs）＋`data/design-profiles/framework-development-v1.json`（拟新文件）|typed packet、知识项、问题、答复、处理决定、binding和source record的结构；profile固定最低设计章节／问题类／认可actor assurance和容量等变项。新模板版本携带其最低项，通过原完整manifest读入。|文件位于自有data，283参考不动。profile不执行命令、不扩权限、不替代native profile。API同时报告 `profile_sha256`（旧）与 `design_profile_sha256`（新），不混名。|

`design_policy` 的项目最低项与所选完整模板里的最低项取并集，ID含来源namespace；同ID异内容是配置冲突，不能后者覆盖前者。owner追加项也进同一包，降低最低项只能通过有权owner的逐ID明确例外，原要求与理由仍可读。模板更新不能回改项目冻结policy或历史manifest；新任务需匹配新digest。

范围先由可信owner声明；机器不声称从diff可靠判断“重要算法变化”。框架／结构重构／重要算法、数据、权限、验收的类别是profile的可配置集合；普通修复是否也强制由项目策略定。若项目不允许可信范围分类而希望全部开发均强制，可在同一策略将支持task_type全部纳入，无需改执行器。适用性缺记录或冲突时阻断新task，不由模型填 `small-fix` 绕过。

State拟升schema6：仅替原各表writer fences，不新增表；原因是v2 project含旧writer不能理解的必答／owner语义，不能让旧客户端写掉。沿现成migration backup／事务回滚；升级失败保持schema5原件。新client读v1项目维持旧合同；降级client可读其所支持原备份，不能继续写已迁移DB。任务、approval journals和设计材料文件版本另行检查，SQLite迁移不重写它们。

## 4. 材料协议：原plan为seed，设计revision为完整受审材料

### 4.1 只产生一次原plan

plan仍只执行一次并产生原 `execution-plan/ownership-map/rollback-plan`，额外产生 `design-packet` artifact。新input在原Executor生成结果schema处把`artifacts.design-packet`声明为task-design-v1的JSON对象并列入required；原三件仍为字符串。原`artifact(name, content)`本来支持dict并保存JSON，因此无需另做字符串内嵌JSON协议。正文缺字段／只有“BLOCKED”不会被当成ready。原native profile仍要求原三件，v12 adapter／plan reader再要求并验证这一额外artifact。

原plan receipt SHA保持为 `seed_plan_sha256`，API兼容字段 `plan_sha256`仍指它。后续设计修改是该seed之下的完整packet revision，**不重跑plan job、不换原receipt、不改变spec、work_units或原stage ID**。最终批准同时绑定seed及精确最新材料。原六阶段run在局部持有seed plan没有错误；work/review的实际方案另由同一approved_plan中的design binding补齐。

第一版要求packet与冻结request的一致性：baseline、starting commit、原manifest、allowed paths、work unit IDs／依赖、预算／权限上限只能精确引用原值；设计可以细化接口、算法方案、验收说明和有权答复，不能偷偷改变这些执行字段。若讨论要求变更冻结字段，返回 `requires_new_task`及字段路径，保留讨论，原任务cancel/fence；显式新task重新授权／批准。不支持同run改work DAG或延长预算。

### 4.2 Packet的具体字段

所有JSON对象封闭字段、ID唯一、引用必须存在；SHA不含对象自身的sha字段。以下为字段合同，不是已经发布的schema：

|字段组|必需内容|
|---|---|
|身份|`schema_version:1, kind:'task-design-packet', task_id, request_sha256, profile_sha256, admission_sha256, manifest_digest, seed_plan_job_sha256, design_profile_sha256, owner_id, revision, previous_packet_sha256`；revision1前版为null。packet从不包含承载它的receipt SHA；最终inspection才把seed receipt加入材料快照，避免循环摘要。|
|目标与方向|原要求逐ID、问题／当前行为、明确目标、非目标、范围、与owner方向决定的引用；不把预算耗尽写成达标。|
|调研与知识|`research_adoption[]`逐来源→方法→适用范围→现有／拟议消费者→验证／未采用理由；`knowledge_requirements[]`见下节。引用已有研究原件，不重新联网堆来源。|
|现有结构|真实入口／caller→owner→原接口、状态和资源寿命；原事实／推论／未知分开；现成库和组件替代方案。|
|方案与规范|完整详细修改方案、可比较选项／代价、风格／项目规范依据、模块接口、每个新file/function的真正caller与归属、删除／复用选择。单caller优先现owner；不为“复用”编造wrapper。|
|数据与恢复|版本、持久字段、兼容／迁移／旧writer、失败／取消／unknown／恢复、资源收尾、回退／回滚边界。无变更须写具体依据并由owner处理对应最低题，不能空字符串代替。|
|实施顺序|与冻结work_units的逐ID映射、依赖、共享文件owner、逐片可验收行为、邻片前置与未开放能力。|
|验收|`acceptance_criteria[]`：requirement IDs、固定输入／环境约束、检查ID／版本／已注册可信argv引用或明确human判断、预期关系／数值容忍度／oracle、原件引用格式、失败／unknown条件、成本／权限／停止owner；配置有效范围内关系优先，不锁死示例默认。|
|讨论|完整 `questions[]`、逐轮变化与撰写时未决列表；有效原answer/resolution集合属于下述材料快照，不能只存模型摘要。|
|展示原件|完整Markdown报告以及可选HTML的**原字节引用／SHA／bytes**；typed字段与报告对应section ID。HTML仅从相同受审原字节生成时属展示；人工编辑报告内容即新revision。|

为免循环身份，区分 `packet_content_sha256`（内容，绑定原plan job SHA）、`materials_sha256`（seed receipt SHA＋完整packet SHA＋有效答复／resolution/source record SHAs＋验收SHA＋policy SHA），以及原 `plan_sha256`。材料快照另含单调的`material_revision`和前快照SHA：设计正文改动增加packet revision；答复／resolution／来源提交至少增加material revision。final binding绑定这些身份；不能用报告单文件SHA代替完整材料身份，也不能将原字节SHA、canonical JSON和完整资源树digest混为同一算法。报告不反向内嵌包含自身的packet摘要。

所有需审文本实际可读；来源只给可访问且授权的引用时，要注明 `reference_only`，不得声称已读取其全文。必需内容不可访问则形成精确缺项。秘密／未授权公司全文不复制到公开报告或任意模型history；owner可提供授权摘要并明确其适用范围，记录摘要自身内容身份，不能假称是原公司文档全文。

### 4.3 问题、知识与原答复

`Question`：`id, introduced_revision, requirement_ids, body, why_required, basis_refs, options[{id, consequence}], affected_sections, required_by[], owner_id`。允许确实没有有意义多选的问题，以自由答复形式给出所需事实／格式；最低问题至少覆盖设计／取舍、风格／规范、可操作客观验收、方向／非目标、拆片顺序，以及被声明必要的公司资料。最低项由profile／项目配置给定，不能删题来让统计归零。

`KnowledgeRequirement`：`id, missing_information, why_needed, affected_question_ids, affected_acceptance_ids, allowed_source_types, access_scope_ref, supplied_refs[], status, freshness_rule, conflict_refs[]`。status为 `missing/supplied/denied/conflicting/stale`；`supplied`仅表示原件已经提供且身份可核，仍要有owner处理其决策含义。没有时效要求可显式 `freshness_rule:null`；有要求时按配置和冻结观察时点／版本核，不统一硬编码“七天有效”。权限不足、来源冲突、文件摘要漂移分别报告，不擅自扩大检索范围。

`Response`：`id, question_ids, packet_content_sha256, exact_text_ref, choice_ids, source_refs, authored_by, recorded_by, origin, recorded_at, supersedes_response_id`。人工原文与模型整理分开保存；`origin:'reported-human'`或Agent转述不是可信human event。owner可将用户实际原答复经可信通道录入并明确attest其原文／范围；不能由正文里一句“用户已同意”升级身份。

`Resolution`：`id, target_ids, packet_content_sha256, response_ids, action, rationale, conditions, expiry_or_null, actor_binding`。action为 `answered/waive/accept_assumption/reduce_requirement/request_information`；后者不闭合缺项。免答／降级保留原最低要求、受影响范围与理由；不覆盖原题。拒绝提供资料不等于waive。跨revision沿用答案仅在问题、必要来源、受影响语义摘要不变且owner明确携带该resolution时成立；新材料的最终批准仍必需。

## 5. 一个journal与两道最终检查

### 5.1 原approval owner内的追加记录

不新增数据库或独立审批服务。扩展 `reference_task_approval` 的同一任务journal：新记录采用schema2，旧schema1逐字解释；源材料正文放原artifacts树。建议的实际布局为：

```text
artifacts/<task>/design/<packet_content_sha256>/packet.json
artifacts/<task>/design/<packet_content_sha256>/report.md
artifacts/<task>/design/<content_sha256>/<answer-or-source-body>
ergora/task-approvals/<task>/<operation_id>.intent.json
                                      .attempt.json   # 仅外部signal副作用
                                      .result.json
approvals/<receipt_id>.json                           # 原可信receipt卷
```

新operation类型为 `publish-design/record-response/resolve/request-revision/reject/withdraw/approve`。本地材料提交沿原task creation lock与project revision检查；intent固定operation、原run、seed、parent record SHA、正文摘要及recorded actor。正文先安全发布，最后不可变result发布才构成本地源记录提交；崩溃留下未提交正文不产生继续权。相同operation ID／不同内容拒绝；普通材料提交相同ID完整内容只读回原结果。**reject／withdraw的本地result只表示决定已提交，不能跳过尚未完成的原fence／cancel尾部**；同ID mutation／显式resume依§6.1继续同一尾部，GET始终只读。局部函数留在现owner，绝不抽通用journal基类。

只遍历该任务已知受限journal目录，按前版SHA／序号重建唯一材料链；无可变 `current-approved` 表或另一个head权威。profile配置总记录数／字节／revision上限；重复序号、分叉、损坏／缺前件产生精确unknown／blocked，不能“取最新mtime”修复。派生当前视图可缓存但总能由原记录重建，不能仅凭缓存授权。

本地source record提交不要求多发Temporal signal；它是受审材料，不驱动第二进度状态机。只有原approve和原cancel产生原生副作用。这样没有“signal已ack但讨论事件是否采用”的另一套恢复机制。页面分别显示 `material_revision` 与原runtime `AWAITING_PLAN_APPROVAL`，不会把前者写成第七执行阶段。

### 5.2 单owner与可信actor

沿原 `_Approval.actor()`／Unix操作者来源、FileAdapter可信receipt卷及ACL边界，不接受传输正文指定actor/role/principal_type。profile保存单owner的可信binding和所需assurance；项目／模板最低项、scope、source格式均不能授新身份。

现有Unix UID和`confirm:true`只能证明调用操作者，不能证明键盘后是自然人。同源／`X-Ergora-Request`只防跨站，当前web进程身份也不能冒充浏览器使用者。**第一片必须显式报告assurance**：若coding agent能写同一receipt卷或与owner共享不受限身份，当前安装不能证明可信人类决定，v12返回 `human_channel_unavailable`，保持新gate关闭。沿原部署合同，需要receipt卷对coding agent不可写，由真正owner的受保护本地终端／已有可信发布通道写入；并没有声称仓库已有组织SSO或签名认证。

因此普通CLI/API可读材料、登记Agent建议／reported-human原文、准备操作意图；可信human resolution／最终approve只能由已配置可用的owner通道完成。UI只消费服务端核定actor与assurance；没有此能力时显示精确缺口并导出完整待审材料／原ID，不能把按钮、JSON `human`或模型调用当替代。若后继需要浏览器直接批准，先独立交付真实身份通道；不在WA5偷偷造认证平台，也不降低本profile的身份要求。

### 5.3 G1：原最终plan批准

原 `tasks.approve → reference.task_approval → _Approval.prepare/dispatch → approve_plan → dev_authorize_plan`不更换。v12的同一次明确approve同时表达“我批准此完整设计材料和此原plan”；不额外要求人连点两个同义批准。

1. `tasks.plan/_plan`核原seed receipt及所有完整材料，返回 `materials_sha256, packet_revision, design_profile_sha256, readiness{ready, blockers[]}, actor_assurance`。blocker含稳定ID／JSON路径、原因、影响决定／验收、可做的补资料／答复操作。
2. `_Approval.prepare`对v12先检查就绪、owner身份、当前唯一revision／parent、期限和原budget。未就绪不落approve intent／receipt／attempt，不发批准signal；保留已提交设计与问答。旧入口不带materials SHA不得为v12隐式补当前值。
3. 准备的schema2 intent固定材料SHA和owner通道，原decision ID不可重绑。**从有approve intent起封存该材料链**：publish／respond／resolve不能越过prepared/unknown批准另立新head。未attempt的prepared批准若要修订，owner用request-revision追加明确废弃记录；旧intent保持，dispatch/resume必须看到失效并拒绝。attempt后的unknown先对账，不能靠新ID绕过。
4. 原 `approvals/<owner-id>.json`仍是schema1 `kind:'plan-approval'`，保留原必需字段并追加 `design_binding:{schema_version:1, protocol, seed_plan_sha256, packet_content_sha256, materials_sha256, acceptance_sha256, effective_records_sha256, design_profile_sha256, owner_binding}`。这是原receipt的完整SHA覆盖内容，不是第二份approve。新增的非approve记录不可冒用plan-approval种类。
5. 原signal仍是原request／plan／receipt_id，attempt仍在send前。v12 adapter在原authorize内读取绑定的完整材料与源链、核ready／owner／seal／失效，再调用原 `super().authorize(context)`；返回原receipt evidence加 `design_binding`。原Workflow接受后将它存入原 `results['plan-approval']`，随后原run把它放进 `approved_plan.approval`，无需换局部plan或复制run。
6. 本地`requested`仍只证明投递。只有原Workflow query/history的接受状态可报告 `approval_accepted:true`；不从信号存在推定被采用。超过原批准等待／budget期限走原stop/fence，沉默没有approve。

#### 5.3.1 G1取得冻结policy的原件路径

原 `DevelopmentWorkflow.approval`传给`dev_authorize_plan`的context确实**没有admission**，不能从该context直接假定已有design profile。v12在`DesignAdapter.authorize`内增加一个本域只读加载步骤，仍由原Activities调用，不复制run或向批准JSON索取policy：

1. `DesignInput.adapter(config)`先按既有input合同选择本版requests root。原可信adapter配置的receipts／artifacts／approvals／fences维持原注册state的四个同名根；其共同state根及v12 requests兄弟目录是配置／登记验证所得，不能取packet或receipt内的路径。新adapter在构造时核这些布局与普通非symlink目录；从该固定state根定位现有`ergora/task-approvals/<task>`与原creation锁，不新增第六个可由正文指定的root。该journal卷须与receipt卷一样对coding agent不可写；实际ACL／owner通道不满足时本profile仍关闭。
2. 从context的原task ID和原固定算法 `task_id + '-' + canonical_sha({'stage':'plan'})[:24]`得到唯一plan job ID，只读本版requests root下`<task>/<job>.json`。核envelope schema／job ID／job context SHA，context的task／request／native profile与收到的authorize context精确同一，stage为plan；由原 `execution_input(envelope.context.admission)`解出合法v12、完整spec／admission／预算／manifest身份，且其 `matches_context`与实际plan job精确一致。冻结design profile、最低项、owner、适用性与预算只能来自这份原admission；不是来自当前project head、批准JSON或待审packet的自报字段。
3. 用同一job读原receipts root的plan receipt，沿原verify_receipt核完整job、SUCCEEDED及原artifact，完整canonical receipt SHA必须等于authorize context的`plan_sha256`。因此该原envelope的policy同时绑定实际Workflow等待的seed，不能把另一份内部自洽packet／receipt接到它上面。读取源链、seal和最终`design_binding`后，还要逐项比较这些材料与此冻结admission、owner及seed；任何policy／owner替换、缺原件、版本或root不符均拒绝。
4. G1读取与G2复用同一 `task_design`纯领域规则；原文件读取／trusted roots归adapter，完整history原件核验仍归`reference_task_approval._plan`。授权API与实际activity均各从自己的原权威取得同一冻结材料，不因前者检查过而省略G1。新资料读完后再核原budget／fence／seal，最后才执行原`super().authorize(context)`并返回同binding。没有网络重检或新批准账本。

这项加载有真实adapter和executor／approval消费者，具体私有方法留在原owner；不抽通用“从context查任务”服务。验收须经真正 `approval → dev_authorize_plan → DesignAdapter` 接缝：原plan envelope要求Q1，receipt／packet内部自洽但换宽policy或换owner时G1拒绝，原合法绑定可接受。只向纯helper传入正确policy不覆盖这个风险。

### 5.4 G2：原work及后继实际准入

第二道必须在真正消费者存在，不能仅靠G1/API：

- v12 `DesignAdapter.validate_submission`在原work/integrate/verify/review发布前核同一approved_plan.design_binding、原seal、源链无withdraw／废弃、原预算／fence。没有binding、旧receipt、旧材料、缺必要项，即使直接向Temporal送原approve signal，也不能发布新的work envelope。
- executor仍由 `execution_input(...).require_job_owner(envelope)`核原job owner；v12在此复用相同设计检查，随后才原Executor claim、prepare及业务动作。`reference_executor._composition_request`把**完整最终packet、有效原答复、验收和来源状态**放入真实叶input并记录内容SHA；review／恢复同样读原冻结材料，不能只递digest或当前head链接。G1之后文件漂移或receipt卷缺失会显式失败。
- `DesignInput`可复用原`stage_material`／`require_job_owner`扩展点；静态admission材料与最终approved材料分开，后者从context的精确binding读。需要扩展签名时只在真实Executor两个use sites增加领域调用，不让上层以version==12堆类型分派。结果schema扩展同理归input契约。
- 原producer比较完整approved_plan保留，所以错设计的work不能被review/integration当作同一次生产结果。预算job重启只回收原attempt，不因设计源记录或新模型输出重领invocation。

final approve之后材料链封存。第一版不支持同run重新批准并重用已执行work IDs；若需要修改任一受审材料，先withdraw／cancel原run、核真实fence及在途资源，显式新task携带旧设计来源形成新revision并重新批准。新task不是旧clock续期或预算余额重置：其新授权必须另有真实owner决定，不能自动出生。这样保持旧结果和原journal，也避免“只换后续设计、前面代码仍属旧设计”的混合候选。

## 6. 修订、拒绝、撤回、unknown与竞态

|输入／中断|持久事实与准入|原恢复／停止|
|---|---|---|
|`request-revision`，尚无approve attempt|追加绑定当前材料的owner决定／理由／待改ID；失效未attempt的prepared批准；旧正文／答案不覆盖。可提交新packet及完整previous SHA。|仍在原AWAITING_PLAN_APPROVAL；approval deadline与总budget均不续。下一次approve要新ID和新materials SHA。|
|普通source／answer提交两次|同ID同字节返回同原记录；同ID不同字节／前版冲突拒绝。只回答Q1不能使Q2消失。|本地无signal副作用，不制造attempt；崩溃按原intent/result补齐同一提交，不更换作者或正文。|
|`reject`|保存明确owner反对及理由；不写approve receipt。|同操作关联原cancellation intent并走`request_cancel`、fence；公开状态保留decision=reject与runtime停止结果两维。|
|`withdraw`，批准前／后|追加对精确approve／材料的withdraw record，旧receipt保持原字节；不直接改`revoked`破坏原intent一致性。先持久禁止后继的原fence，再请求原cancel。|在途进程仍须原budget supervisor、fence与实际reaping见证；unknown／CANCEL_UNCONFIRMED不能显示“已经停止”。恢复只查原cancel和原资源。|
|无答复／关闭页面／owner离线|材料缺项及原期限保持；不会出现隐式处理或approve。|达到原approval等待或work cutoff后原stop/fence；页面关闭不撤销已发动作，需继续处理用原ID查询。|
|批准attempt前后失联|prepared可显式恢复首次send；attempt已落但无result为unknown；不换decision ID、不延receipt期限。|原 `find_signal_event`核同run完整signal；找不到保持unknown；signal存在仍需查询是否被采用。|
|source修改与approve并发|同creation.lock串行；approve intent封存链；迟到source要求先明确request-revision。phase竞争产生requested不代表接受。|Workflow仍核原phase/request/plan/receipt。失效prepared不可复发；已unknown只对账。|
|withdraw与work并发|withdraw生效的线性化点是原可信fence持久可见；v12 adapter及最后stage body启动准入读取同fence。若业务stage在该点前已准入，记录其原事实，内部后代属于在途子树，不能宣称撤回能倒退执行。|按下段在原job/process owner补短锁内最终准入；不能用静态检查替代并发效果证据，也不承诺已有stage内的所有OS spawn瞬间消失。|
|损坏／丢源件、历史任务、过期资料|binding指定原字节不可验证则blocked／unknown，不拿当前memory/head补齐。历史读取按其原版本展示，不让今日freshness否定已经发生的旧事实。|新approve准入按当时配置规则；恢复仅观察原决定，不续期、不重新检索、不重发。|
|批准后发现新必要知识或重要改动|不能在封存设计上偷偷新增答案后继续work；保留新缺口与owner request-revision／withdraw。|原任务停止，新任务新授权／批准；已有候选不可借新设计获得追认。|

撤回的“先fence后cancel”复用原 `FileAdapter.fence`：其确认范围是可枚举请求的terminal receipts，不等同于完整进程子树已停。原`processes.run`目前在Popen前调用should_stop，但检查和Popen之间没有与fence共享的锁；本轮静态已确认这一接缝，不能假称原实现已有线性化保证。

v12拟在同任务增加**仅作同步的**`ergora/task-approvals/<task>/.admission.lock`。`DesignAdapter.fence`与withdraw发布原fence时持此短锁；`BudgetedJob.supervise('body')`经input的窄`job_start_guard`合同，将同锁／原fence／精确binding最后检查传给现`processes.run`，只包住停止检查和实际Popen，启动后立即释放。旧input返回nullcontext，collection／cleanup不受业务停止阻断；不持整个job的锁等待人工决定。`processes.run`所需的新可选start-guard参数只有原job supervisor这一真实caller，理由是拥有实际Popen的现模块必须隐藏检查与启动的原子区间，不抽通用hook框架。锁顺序固定为creation lock→admission lock；启动guard不回取creation lock，撤回的远程cancel在释放admission lock后发送。

补充原fence对应的操作SHA引用可以留在withdraw journal；不得增加旁路stop文件／第二停止控制器。已准入stage的实际停止由原supervisor、fence及reaping见证负责；原attempt不重用。a-2的work双门和b-1的撤回必须同时包含这个真正接缝后才能开放，不以单次“撤回记录写成功”替代。

### 6.1 reject／withdraw的固定停止尾部与同ID恢复

本地决定和停止观测是不同事实。design operation intent在首次提交前固定一个原cancel子请求：`request_id = 'design-stop-' + canonical_sha({task_id, request_sha256, run_id, operation_id, kind})[:40]`，并保存原`_Cancellation.record`完整预期值及其SHA，包含原submission／run、project revision、原actor和固定reason。此子record不反向引用父intent SHA，避免循环；父intent本身完整绑定子record，journal不能换子ID、reason或当前run。原reason的1000字符合同按源决定的精确值验证，不截断后声称相同决定。

持久次序和恢复入口如下，全部沿原owner，无第二停止状态机：

1. 持creation lock，核原intent／单owner／材料；在intent中冻结上述子请求，发布本地决定result。result只含原决定及固定binding，不含“已停止”承诺。崩溃于此后，即使result存在，同ID mutation／`design resume`仍须继续步骤2；纯GET返回`decision_committed:true, stop_effects:pending`及原ID，不产生副作用。
2. 按creation→admission顺序持短锁，发布**原task fence**，验证已有fence是相同task/request原字节，沿现filesystem读写接缝确认同一普通文件及目录持久性后释放admission锁。原FileAdapter.publish只同步临时文件，不能据此假称目录已持久；v12的这个确认需实际fsync／重读原fence及父目录。相同fence可重复确认；冲突／损坏不修补，不删旧fence，不写替代stop文件。可见而尚未证实持久时，后继仍保守拒绝，公开显示持久性unknown。只有完成这一步才报告定义的撤回线性化点。
3. **释放外层creation lock后**进入原 `_Cancellation`准备／恢复入口，它自行取得同一creation lock，不在锁内嵌套调用其完整`run`。原child intent不存在时，只以父intent固定原payload准备唯一子请求，再核实际child完整SHA等于预期；若已存在，必须精确相同。不从当前project head重算原actor／reason／run／批准，也不换新子ID。原件或权限漂移使原恢复不可能时，保留原fence并明确blocked／unknown，不能重置身份。新的task创建不能自动移除这个fence。
4. child尚无attempt时，显式resume可以沿原取消owner发送其首次signal；attempt已存在则只走原`reconcile`，丢回复不重发。已有ack／history／closed result按原cancel状态读回。若决定result后、fence后、cancel intent后或attempt后中断，同一个父operation和其原intent SHA都能定位这个唯一尾部；不会因“本地result已存在”提前返回。普通source提交无需这个尾部，也不增加attempt。
5. 状态动态读原fence、child cancellation intent／attempt／result与原job supervisor／reaping见证，分别给出决定、fence可见／持久、signal delivery和实际停止；不另写可变的`stopped:true`权威缓存。原budget仍只用原clock，恢复不续时。在途stage在原fence有效前准入的事实保留；fence确认后仍需原supervisor实际退出，`requested`或journal存在不能认证停止。

验收沿现task cancellation与实际process fixture，在“本地result后／fence前”和“fence后／cancel intent前”真实中断，再以同operation ID／原intent恢复；固定子ID／原record身份不变，fence持续拒绝新body。再验cancel attempt后丢回复仅对账、在途子树真实回收、外层锁释放后原cancel能取锁，无新run／重新授权。这里新增的是跨owner恢复合同；已有source publish或独立cancel helper通过不能代替它。

## 7. 函数与文件落点：每项都有实际消费者

下列均为**拟议变更**；不表示文件／函数已经存在。名字在实施时可随原owner收敛，不能为满足清单增加空wrapper。

|落点|最小变化／真正caller|现成可复用与职责理由|
|---|---|---|
|新 `task_design.py`|纯合同 `validate_packet/readiness/materials_identity`，及受限字节加载后的领域一致性检查。生产caller为 `reference_task_approval`（源提交／G1）、`reference_workflows.DesignAdapter`（原authorize／submit）、`reference_inputs.DesignInput`（G2）；`tasks`仅消费其结果。|模块只import标准库；公开输入的schema结构用application原contracts校验，native的`-S`creation路径只读冻结对象并核原摘要／领域关系，不顶层import jsonschema/SDK。文件safe read由caller原adapter负责。该模块隐藏引用／例外规则，不持State/Temporal/client，不做generic registry。三个真实生产caller使共享规则有必要。|
|现 `reference_task_approval.py`|扩`_plan`读取revision与缺项；同owner内的局部source提交／chain读取／resolution方法；`_Approval`schema2 intent／design_binding／seal／废弃／resume。|原锁、项目revision、actor、receipt、attempt／history均保留。单caller的源链私有算法留本文件，不抽“事件平台”。|
|现 `reference_inputs.py`|`DesignInput(NativeSixStageInput)` version12；原`adapter/workflow_type/stage_material/require_job_owner`实现；需要时加窄 `model_result_schema(stage, base)`／最终stage材料契约，旧实现返回原schema/空增量。|真实caller是`reference_executor.model/_composition_request`及job入口；框架构造方法单caller也有明确多实现接口职责。可选selected context复用原函数，不强制每个任务选择memory。|
|现 `reference_workflows.py`|`DesignAdapter(SelectedContextAdapter)` version12，authorize／validate_submission；`DesignWorkflow(SelectedContextWorkflow)`只注册新类型／继承原run；status可带设计能力，source当前态由原use case合并。|原activities可持adapter注册，无需新Activities类；原BudgetedWorkflow与DevelopmentWorkflow不复制、不改283。|
|现 `reference_executor.py`|在原模型schema构造、材料装配和原job admission三个use sites调用input合同。保留_declared_results对design-packet的完整传播和原artifact验证。|原agents.result_schema、_review_artifacts、compile_input、saved formal-call恢复继续用；不让Agent自己维护“已读”标志。|
|现 `reference_job_lifecycle.py`、`processes.py`|BudgetedJob.supervise('body')取得input的`job_start_guard`，现run的可选guard仅包住原Popen；v12 fence持同短锁。|复用原stop_requested／supervised process／原fence；不建新进程控制器。旧input为nullcontext，原行为与cleanup保持。|
|现 `tasks.py`、`reference.py`|TaskDefinition8准入；`tasks.design`只读；源提交／答复／resolve／design-decision在原`_decision_prepare`或局部用例下调用同native approval组件，不新起控制进程族。approve增加显式材料SHA；旧signature／旧tasks不变。|真实caller为CLI与HTTP两个生产文件。现 `_task_operation`的inspection错误映射补相应读操作；不持DB事务等网络。|
|现 `task_envelopes.py`、`reference_task_creation.py`、`reference_creation_process.py`|wrap/unwrap12、完整设计profile冻结／校验、definition8和budget/context版本校验；published/恢复沿原creation记录。|沿原intent/files／supervised preparation；可选context不重新访问活动head。原request schema2/native spec和283保持。|
|现 `registrations.py`、`state.py`，新registration-v2 schema|项目最低项／owner policy与State6 fence；注册原intent和四文件保持原投影。|实际caller是既有project register/import/resume；不新增设计配置存储服务。|
|新task-design-v1、task-definition-v8 schemas、companion profile|分别供结构校验、公开准入和用户可审配置；不是运行类。|协议层配置接口按角色评估，不要求虚构多个运行caller；容量／必答／时效／actor要求保存在profile，不散落API/JS常量。|
|新模板版本（最后）|先发布`ergora-refactoring-template@1.2.0`的完整新包和对应preset；框架开发沿已存在的large-change组合明确新增支持版本，不能把只读training proposal改成执行模板。|原presets.json完整索引、asset_trees和manifest来源；先核当前实际版本再确定未占用目录名。旧1.0/1.1和freeze身份不动。|
|现CLI／HTTP／console（后续交互片）|只解析输入／调用同tasks用例并呈现能力；见下节。|没有页面局部审批状态机、new scheduler或第二数据库。|

上述函数不能在一个“万能服务”持有State、source检索、Temporal与所有执行器。删除task_design模块会使三个批准／执行消费者各自理解完整引用和就绪规则，因此它有明确深模块职责；删除单次wrapper而caller不承担新义务的wrapper则不应添加。

## 8. 可独立验收的小片与次序

|小片|具体产物／先后关系|本片可声明的完成边界|
|---|---|---|
|WA5a-1，最小首片|task-design-v1 schema＋companion profile，原plan reader读完整packet并返回精确缺项；在原owner实现纯就绪规则，沿现fixture覆盖真实seed/job/receipt/字节。**不注册v12可执行输入、不写批准、不改模板默认。**|有可审机器合同和完整材料读取；缺Q／K可客观观察。它不是已实现执行关卡。这个首片最小且不会抢M5/native运行owner。|
|WA5a-2，原runtime双门|在a-1上交付registration2/State6、definition8/input12、初始packet生产与完整传播、G1/G2同binding／预算；仅在可信owner通道实际可用的隔离安装启用新profile。|结构合法但缺知识／必答时，真实approve和work均阻断；直接旧批准也无work。旧任务与283同一。新执行能力必须到本片真实验证后才可声明。|
|WA5b-1，讨论与决定源合同|原journal支持多轮完整packet、原answer、owner处理、request-revision和prepared废弃；拒绝／撤回关联原cancel/fence；封存后新材料要求新task。|两轮真实原记录离线读回，旧材料／旧决定不可越过；同ID／unknown恢复、原预算和并发不重发。部署缺可信身份时仍保持v12 gate关闭。|
|WA5b-2，CLI／HTTP|同一tasks用例的读写薄入口，完整错误结构和材料导出；真实owner通道缺失时写human操作明确不可用。|CLI和HTTP对同材料给同缺项／同ID恢复；没有UI“human”可绕过的路径。只验本地操作者时明确记录其assurance限制。|
|WA5b-3，页面及小型真实旅程|扩tasks.js原approvalDialog展示全部设计／问题／必要资料／原答案／处理理由／历史和最终binding，受能力控制的动作；真实隔离owner旅程。|新选项代际／迟到响应保持，unknown无自动重试；真实人读明确材料后批准至work，再另任务拒绝／撤回／恢复。此后才更新新preset默认选择。|

a-2依赖b-1中的最小源记录提交／封存不变量，实施时可先抽出该最小部分；不能为了“先验a”开放一个无法撤回、无法记录有效答案的临时profile。a-1可先独立交付且执行保持关闭；a-2和b-1各自文档／独审可以分开，**完整写准入必须等两者闭合**。配置／存储／安装／受控SDK／真实服务／真实人类／发布分别记账，不用其中一种替另一种。

每个完整实现片沿原交付规则：固定准确source/diff→适用原反例和修后→新非editable core/SDK与完整包身份／283保持→自身原模板→fresh需求／维护性审查→按既有授权整合／发布。当前只写设计，不运行这些步骤。M5/native依赖隔离继续独立；WA5不得改它的私有checks、原参考或借其未验结果认证自己。

### 8.1 CLI／HTTP／页面的具体交接合同

先在原task命令下增加`design`子组：`inspect/publish/respond/resolve/decide/operation/resume`。前三类文本写入通过`--body-file`读取完整UTF-8原件；所有mutation都带原project revision、run ID、seed plan SHA、parent material SHA和稳定operation ID，owner决定还需明确confirm及服务端可用的可信通道。`decide`只接受request-revision/reject/withdraw；最终approve沿既有`task approve`，对v12增加必需的`--materials-sha256`。恢复沿原intent SHA，不重新读取body文件或替换当前head。

HTTP使用现`/api/projects/{project}/tasks/{task}`前缀：`GET /design`（固定run/seed，可选读取历史material SHA）、`POST /design/operations/{operation_id}`（kind及typed内容／完整正文）、`GET /design/operations/{operation_id}`、`POST /design/operations/{operation_id}/resume`。四者调用同tasks用例，再进现reference approval组件；不另起design server。现`POST /approvals/{decision_id}`仅对v12增加materials SHA，现`/resume`仍只接受原intent。禁止body中的actor/principal/role字段；HTTP模型用strict类型、封闭字段、原同源／请求头规则。只读也报告真实可用能力，缺trusted owner channel不能被status200包装成可批准。

统一返回原操作状态加`design:{seed_plan_sha256, packet_revision, material_revision, materials_sha256, readiness, actor_assurance, capabilities, current_decision, records[]}`；`records[]`只索引正文，完整受审内容沿原plan inspection的大小上限读取。超限必须精确失败／要求拆任务，不能截断正文后批准；profile可配置上限不得超过现传输安全上限。`approval_accepted`与`execution_success`继续独立，不随设计ready改变。

页面沿原approvalDialog读当前完整packet、原报告、每题选项／代价、必要资料及权限缺口、原答案和owner处理理由；显式展示当前版本与正在看的历史版本，历史不能批准。按钮只消费capabilities，不持有当前有效决定的权威。已读状态只作页面交互条件，最终服务端仍核完整SHA与可信actor。迟到响应沿已有project/detail/run/reading代际失效；关闭页面不等于withdraw，unknown只提供按原ID读取／恢复。

## 9. 最小必要验证接缝与客观反例

这里是后继需实现的验收合同，**本轮没有运行其中任何一项**。优先扩现有文件及fixture，不新开重复CI job，不用只测helper取代跨边界风险。

|风险／反例|真正可观察结果|现成最小接缝／限度|
|---|---|---|
|原WA3“BLOCKED但字符串非空”合法plan|v12 plan inspection给Q/K精确ID；approve intent/receipt/signal计数均不增加；work请求0。旧profile仍按旧合同读取。|`test_task_plan.py`＋`test_task_approval.py`原SDK fixture和原receipt字节；这部分是受控native链，不能称真实Temporal。|
|绕过API直接原approve signal／旧schema1 receipt|G1 adapter拒缺design_binding；即便伪造Workflow输入或旧context，G2在真实executor业务动作前拒绝，模型/可信命令启动0。|`test_composition_runtime.py`原workflow/activity fixture＋`test_composition_executor.py`实际Executor/原claim；不能只断言API报错。|
|Q1已答而Q2仍缺、K1 denied/conflicting/stale、Agent自waive|保留原状态，返回未决ID；Agent或reported-human resolution不能改变ready；owner逐ID例外保留原最低项与原因后才可ready，仍未approved。|原plan/approval fixture调用整个source提交→读取→approve；schema helper仅补引用边界，不额外复制同一逻辑矩阵。|
|两轮真实讨论、改设计但旧approve|revision1/2、原文／来源和前版SHA全可读；旧prepared废弃；旧intent恢复拒绝；新材料必须新明确批准。|`test_task_approval.py`＋`test_task_inputs.py`原已保存creation/journal；一次集成场景覆盖，避免每字段做同义测试。|
|换baseline／manifest／work_units／路径／预算|返回具体字段及requires_new_task；原spec／预算authorization／deadline／model claims不变。|`test_task_creation.py`、`test_task_budget.py`真实冻结原件；配置用至少一个非默认有效值检查关系，不写死24单元／4并发。|
|来源正文、报告、答复或验收换字节|完整材料SHA变化、旧绑定失败；缺全文不伪装已读；执行器收到的原input文本和SHA与owner所批同一。|`test_task_plan.py`＋`test_composition_invocations.py`／executor原formal-call material；原大文本读容量边界只取必要M−1/M/M+1。|
|publish写后崩溃／批准attempt前后丢回执|本地未commit正文不变ready；same ID同bytes恢复；外部unknown只查原run完整signal，历史不存在不重发、不换owner、不续receipt。|`test_task_approval.py`既有interruption fixture扩新字段，保留原普通批准恢复保护。|
|request-revision与approve竞争|唯一锁序，一个材料链被seal；迟到提交拒绝；ack不假称accepted。|原approval并发线程fixture，保留其他project可写、不持DB等网络的断言。|
|withdraw与work真正spawn竞争|fence在前则新stage body starts0；stage已准入则保存原attempt并实际停止／回收，停止未确认显示unknown；恢复不重新执行。|原`test_task_cancellation.py`、`test_budget_jobs.py`／`test_task_budget.py`和`test_processes.py`原process fixture。必须实际进程/锁边界，单测JSON不足。|
|旧任务／writer／backup|原1–11任务journal／完整history字节不变可读；新profile不让schema5 writer删除项目最低项；State6失败回滚与备份可恢复。|`test_state_migrations.py`、`test_state_backups.py`、`test_task_inputs.py`。只跑受影响范围，不重跑无变化训练／GPU。|
|伪human与入口一致性|客户端actor/role/human字段无效；当前无可信human channel时CLI/HTTP都阻断；受保护owner通道才产生最终receipt，Agent正文不升级身份。|`test_task_approval.py`原CLI/API seam＋`test_web.py`能力来源；测试替身只能验证取actor位置，真实权限分离必须另验。|
|新页面读A迟到覆盖已选B|原detail/run/reading generation使A失效；不能批准当前未完整读的B，unknown不自动重试。|现`test_definition_console.py`／`test_web.py`已有console／HTTP接缝先核是否实际执行DOM；不能用JS源码字符串断言认证交互，必要真实浏览器旅程另验，纯文字不跑模型。|

新profile最终需要一场真实小型原六阶段旅程：同一原预算下生成完整设计，明确缺必要公司决定→准确提问→两轮owner原答复／修改→明确最终approve→work实际收到完整材料；另以最小任务验reject／withdraw／原run丢应答恢复。场景可用CPU和普通小仓库，不要求训练／GPU；不能借产品方向文档或Agent自动填入“用户同意”完成该旅程。成本／权限由此旅程的具体授权固定，本文不提前发批准。

## 10. 审查交接、未决与本轮验证范围

本设计不再新增D1–D4产品问题。保守的“全部受审材料变化重批”、冻结执行字段变化走新task、无可信人类通道保持新gate关闭，是对已确认原则的可核验实施规则；若未来需要同run重规划／多人决策／浏览器组织身份，另立真实消费者和方案，不能作为本片隐含支持。

实现前还要核的技术点为：a-2最终字段／字节大小在原Temporal与plan inspection上限内；上述stage body短锁到原native在途子树停止的实际效果；部署的receipt ACL／owner通道确实隔离coding agent。它们是需要证据的实现／安装前置，不是让用户重新回答已决定方向。任何一项未闭合，明确保留相应gate关闭；不能用 `trusted_receipts:true`布尔或纯-S协议检查代替实际权限／完整hook验证。

本轮实际完成静态阅读：根／src／tests AGENTS、总PLAN、组件协议、maintainable-project-delivery及independent-review、ergora-codebase-quality的module-design/test-seams；固定需求／决定／三审计；上述原Task／Workflow／adapter／Executor／input／State／CLI／HTTP／console及现测试源码。没有运行tests、probes、安装、服务、网络、模型或训练，没有读取／输出环境变量值，没有递归扫描私有checks，没有commit/push。本文件唯一获准写入；PLAN与delivery由主控按当前并行任务事实单独更新。

后继fresh设计审查的输入：原始需求、D1–D4及上述五份固定依据；本稿完整原文／SHA；基线debf6f9与真正实施前source identity；仅设计事实、没有运行通过记录；审查者只读必要源码并写主控明确授权的项目docs审查文件。特别检查seed与revision身份无循环、原run未被旁路、G1/G2没有单边放行、actor没有从UI制造、unknown不重发、撤回未假称资源已停、无单caller通用层。**设计审查通过后，主控再授权／开始具体实现片；本稿不开放任何gate。**
