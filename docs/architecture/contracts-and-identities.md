# 结构合同与内容身份

共享结构按 JSON Schema Draft 2020-12 描述，核心由 `ergora.contracts` 使用 `jsonschema==4.24.0` 校验。业务 API 接收和保留普通 Python JSON 值；校验不转换类型、不写入 schema 的 default、不经 Pydantic dump 重新编码。下表包含R2以来已接入的版本，当前调用关系见[架构导航](current.md)。格式版本、定义的语义版本、项目revision和内容摘要分别标识不同事实，不能互相替代。

## 当前格式和责任

|输入 / 结果|结构来源与版本|业务责任|
|---|---|---|
|内置层与组件目录|`data/components.json`，目录 `schema_version: 1`；configuration 按 Draft 2020-12 解释|`components` 负责内置目录/显示投影；不运行外部插件|
|角色与支持工具绑定|上述 configuration；绑定沿用现有无独立版本的 `{tool, ...}` 格式，位于 project v1|`bindings`委托实际所有者：`agents`核角色/能力、`kernel`核原生路径、`issue_backends`核tracker连接，其余支持层核schema及ReMe URL/变量名；共用结构校验|
|指定工单观察|`data/schemas/issue-observation-v1.json`；与task／request版本分开|`issue_backends`验证原生响应与完整原字节摘要；`issues.show`补固定项目修订／配置摘要和观察时间。source含完整API base／namespace／number或iid，issue另存native ID；文本为context_only，show不持久入表、不派工。ETag／更新时间不是写CAS|
|工单快照与显式上下文关联|`issue_sources.validate_snapshot / issue_snapshots / issues._LINK`为本域严格v1记录；SQLite schema v2的两专属表|snapshot SHA对完整观察去掉observed_at及当次tracker binding做UTF8 canonical JSON摘要；首次观察时间另存。link固定snapshot SHA、task ID及原creation intent／compiled SHA；`created_revision`是项目修订，`operator_asserted_context`不授予执行。离线备份核记录／列／摘要／引用，不解析当前凭据或原execution目录|
|Agent 结构化结果|`agents.result_schema` 生成所选模板角色的必需 artifacts 和审查 decision；命令信封沿用 `stage-json-v1`|`agents.validate_result` 使用同一份 schema 验证实际输出，非空白 summary/artifacts 和拒绝额外字段保持；进程成功不是正式验收|
|静态Agent定义包|`data/schemas/agent-definition-v1.json`，严格整数版本1；索引由定义库所有者校验|`agent_definitions`核职能/后端、包内资源与精确版本；备份核索引→对象→资源，不新建DB表或运行准入|
|静态工作流定义包与预览|`workflow-definition-v1.json / workflow-definition-v2.json`；预览v1/v2，grant仍v1|v2增加实例必需／建议审查职责；`workflow_definitions`核精确引用、端口／有界DAG、完整祖先资料／权限及预算。preview版本为所展开定义的最高版本，仍`executable:false`；`definition_bundles`逐包发布，不授执行权|
|完整静态manifest、叶子输入与MCP scope|`composition-manifest-v1.json / composition-input-v1.json / task-mcp-scope-v1.json`|完整包树与已接受preview固定，含精确资料与来源；`workflow_definitions`拥有冻结／核验，`agent_runs`拥有调用准入，`task_mcp`只交付本次固定资源；静态`execution_authorized:false`不随包导出改变|
|用户正式任务定义|`task-definition-v1.json / task-definition-v2.json / task-definition-v3.json`|`tasks`拥有项目／revision及有效绑定；v2另选完整manifest、review子图、逐叶override和work分配，v3另选精确工单snapshot SHA并要求work-units-v2；creation3仍原七文件，创建不是提交。task-definition版本不等于正式信封版本|
|正式任务spec／组合信封|原生v1 spec保持原形状；`task_envelopes`校验v2–v7信封，原`legacy_spec`为兼容六阶段投影|v2完整组合，v3审查职责，v4显式dag-v1，v5 work-units-v1，v6 work-units-v2，v7新增完整issue_source且保留v6材料语义。`reference_inputs`局部映射选择原版本queue／request根／workflow及准入报告；v1–v6保留原doctor，v7仅检查冻结所选依赖与必要本地条件，原task_action仍拥有策略／claim／提交。旧身份／history不自动迁移，完整信封参与准入／恢复，unknown只查原ID／memo|
|正式执行材料|`reference_executor`发布`formal-work-materials / formal-review-materials`；旧材料v1，正式信封v6/v7使用材料v2／`artifact_protocol:stage-artifacts-v1`|v6/v7逐件核审计原件，只内联完整声明阶段产物、可信检查与意见，不递归复制前代prompt；完整祖先资料和原预算仍核验。v7另外在work/review材料交付完整issue_source；材料v2与WorkflowDefinition-v2没有版本继承关系|
|离线任务交接|`task-handoff-v1` ZIP：manifest与去重blob；`handoff`受限校验|收集沿原证据所有者；v7追加完整contract.original_input及canonical SHA，核来源／冻结配置／原outcome admission SHA，仍受索引和manifest 1MiB限制；基础包经纯task_envelopes.unwrap／issue_sources校验，可离线核内部字节及声明关系，不认证来源或推断执行成功，不替代控制面／执行目录备份|
|评价输入|`data/schemas/evaluation-manifest-v1.json`|`evaluation.register` 负责版本、case 安全 ID/唯一性/三个 split、可信文件解析和指纹；不允许额外顶层/case 字段|
|evaluator 响应|`data/schemas/evaluation-result-v1.json`，结果本身不新增版本字段|`evaluation.evaluate` 要求有限 score/cost、bool passed、string feedback；沿用旧行为接受并忽略附加上游字段，预算和候选绑定仍由评价所有者负责|
|离线控制面备份|`data/schemas/state-backup-v1.json`，严格整数版本 1|`backups` 负责库/文件/Skill/来源身份核对及同平台原 home 恢复；CLI state 入口不先创建或迁移 State|
|完整项目注册与旧注册导入|`data/schemas/project-registration-v1.json`；导入spec及旧项目格式从其属性复用结构，版本均严格整数1|`registrations`拥有Git根、角色能力、检查、修订及意图/resume；reference拥有投影路径、原scope/路径校验与不覆盖发布。每份投影最多1MiB，旧源要求原runtime可读取的UTF8|
|CLI JSON 文件 / Web body|CLI 沿用 `utf-8-sig`（接受 UTF-8 BOM）；Web 继续使用原 Pydantic 传输 DTO|业务绑定/评价都走相同函数；传输错误仍由各入口解释。Agent/evaluator stdout 沿用严格 UTF-8 JSON，不自动剥 BOM|
|冻结 reference 编译 / 请求 / 回执 / 训练合同|原 `dev_platform` / `agent_platform` 版本与验证器|不修改冻结 schema、可信检查、批准权限或 canonical 编码；训练 prepare / worker 不启动实际训练|
|Skill metadata / 资产、记忆、研究和持久文档|沿用各领域现有格式及 schema_version|目录/修订/来源和领域状态由原模块负责；R2 不为旧 DB 强加重写。DB 迁移与旧客户端隔离由 R3 单独实施|

结构错误为 `CONTEXT at /field/0: REASON`；路径使用 JSON Pointer，`/` 和 `~` 分别编码为 `~1`、`~0`。缺失字段或额外字段的结构错误指向所属对象，并在原因中列出字段。业务错误继续给出具体原因，不假装 URL、文件可用性或评分判断都是 schema 规则。

`integer` 要求 Python `type(value) is int`，拒绝 bool 与 `1.0`；也与 `number` 使用同一有限数判定，防止范围关键词因两种类型判定不一致而跳过巨大整数。各字段独立声明范围；工单的原生 ID 与项目修订只有正数下限，不假定它们有小范围上限。`number` 保持 int/float 且可由原 `math.isfinite` 判断为有限的值，拒绝 bool、NaN、Infinity，以及超出该数值表示范围的巨大整数；后者转成可读的 ValueError，不让 OverflowError 中断用例。各字段范围来自原实现（例如 mini step 1–1000、cost >0 且 ≤100）。这比 JSON Schema 对“数学整数”的默认判定严格，外部校验器还须遵循这些领域语义。

评价版本号的旧检查使用 `== 1`，实际接受 `1` / `1.0` / `true`；R2 保留该兼容行为，其他版本仍拒绝。新文档和生成器始终写整数 `1`。如后续要求严格版本类型，须单独版本化迁移；本节点不静默改写旧输入或摘要。内置目录的未知版本仍由现有加载边界拒绝。

## 身份算法

|身份|当前实现和编码|不能替换成另一算法的原因|
|---|---|---|
|评价 manifest|`evaluation.manifest_sha256`：`json.dumps(sort_keys=True, ensure_ascii=False, allow_nan=False)` 后 UTF-8 / SHA-256，保留默认空格|原 `_sha` 仅改为语义名称；旧评价 suite 的摘要和候选证据须保持|
|reference canonical JSON|冻结 `dev_platform.contracts.canonical_sha` / adapter sha：排序、UTF-8、不转义 Unicode、紧凑分隔符、拒绝 NaN|原编译、request、profile、批准及回执使用此身份，不与评价摘要合并|
|Skill 目录|`skills.digest_tree`：排序相对路径；逐文件内容 SHA 和 executable bits；文件清单沿用原排序 JSON编码再 SHA-256|脚本执行位与内容共同构成资产；不能只 hash SKILL.md 或把不同换行/字节归一化|
|静态Agent包|共享`asset_trees.digest_tree`，使用原Skill目录算法，包含agent.json及所有普通附件；文件资源另核原字节SHA256，Skill核完整目录摘要|精确ID/版本指向固定包摘要，不通过JSON重编码合并不同包，也不把资源可读性当成权限/运行证据|
|静态Workflow包/预览|包沿原Skill树算法；预览为排序、UTF8、不转义Unicode、紧凑JSON/SHA256，不含自身preview_sha256|包含精确根/全部引用、结构路径、图/端口、完整静态材料、来源/拼装摘要、权限、显式grant和限额；不含未来端口值，不是正式运行manifest|
|Agent 结果 / prompt / 文件产物|原所有者对实际固定字节计算 SHA；结果沿用排序、保留 Unicode 的 JSON|是不同用途的实际内容身份，不做统一的“自动标准化”|
|离线备份清单|`backups.verify` 对 manifest.json 原 UTF-8 字节 SHA-256；文件清单各自记录实际字节、大小和文件模式|清单身份绑定这一份快照；不重写其中引用的旧 Skill / 评价 / 正式证据摘要|
|项目登记、投影与导入预览|排序、UTF8、不转义Unicode、紧凑分隔符、拒绝NaN的JSON/SHA256；登记摘要绑定id/repo/规范化定义，预览另绑定control_home/revision/绑定/差异/源SHA及投影摘要|bindings仅由项目顶层拥有；旧文件SHA另按原字节计算，空白变化也使导入预览失效；不重编码旧文件以制造一致性|
|工单响应|成功单GET完整原响应字节的SHA256；ETag和原updated_at另保留，不重编码响应来计算同一摘要|响应空白／字段顺序变化也会改变SHA；观察时间与配置身份另存，不能由内容摘要推导任务授权、事件去重或原子写入版本|

A2 的固定向量、两种 compiled/request/profile 身份、Skill 执行位和合成旧状态继续作为回归依据。R2 只把测试中的私有 `_sha` 调用迁到实际语义名称，未改任何身份夹具。

## 增加或调整字段

已有驱动的配置结构在组件 configuration 修改，表单、目录与核心结构校验随软件包一起生效。跨字段的角色能力、凭据、可信文件和批准规则仍在责任模块实现；增加描述不会产生新的 SDK 适配。测试应验证真实输入/失败路径、CLI/API 一致性和必要的旧身份，而不是只将同一份描述抄成另一份断言。

引入新的格式版本或改变摘要编码须设计迁移、旧客户端访问与回退，不能以 schema default、DTO coercion 或数据重新 dump 代替。基础包只新增 schema 栈，Web / GEPA / Temporal 等仍是可选依赖；实际跨平台分发结果记录于 [R2 交付记录](../delivery/2026-11-02-schemas.md)。
