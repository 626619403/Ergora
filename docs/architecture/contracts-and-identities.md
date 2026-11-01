# 结构合同与内容身份

R2 的所有权说明。共享结构按 JSON Schema Draft 2020-12 描述，核心由 `ergora.contracts` 使用 `jsonschema==4.24.0` 校验。业务 API 接收和保留普通 Python JSON 值；校验不转换类型、不写入 schema 的 default、不经 Pydantic dump 重新编码。

## 当前格式和责任

|输入 / 结果|结构来源与版本|业务责任|
|---|---|---|
|内置层与组件目录|`data/components.json`，目录 `schema_version: 1`；configuration 按 Draft 2020-12 解释|`components` 负责内置目录/显示投影；不运行外部插件|
|角色与支持工具绑定|上述 configuration；绑定沿用现有无独立版本的 `{tool, ...}` 格式，位于 project v1|`agents` 负责角色/能力；`tools` 负责支持层与 ReMe URL/变量名；`kernel` 负责原生绝对路径；三者调用同一结构校验|
|Agent 结构化结果|`agents.result_schema` 生成所选模板角色的必需 artifacts 和审查 decision；命令信封沿用 `stage-json-v1`|`agents.validate_result` 使用同一份 schema 验证实际输出，非空白 summary/artifacts 和拒绝额外字段保持；进程成功不是正式验收|
|评价输入|`data/schemas/evaluation-manifest-v1.json`|`evaluation.register` 负责版本、case 安全 ID/唯一性/三个 split、可信文件解析和指纹；不允许额外顶层/case 字段|
|evaluator 响应|`data/schemas/evaluation-result-v1.json`，结果本身不新增版本字段|`evaluation.evaluate` 要求有限 score/cost、bool passed、string feedback；沿用旧行为接受并忽略附加上游字段，预算和候选绑定仍由评价所有者负责|
|CLI JSON 文件 / Web body|CLI 沿用 `utf-8-sig`（接受 UTF-8 BOM）；Web 继续使用原 Pydantic 传输 DTO|业务绑定/评价都走相同函数；传输错误仍由各入口解释。Agent/evaluator stdout 沿用严格 UTF-8 JSON，不自动剥 BOM|
|冻结 reference 编译 / 请求 / 回执 / 训练合同|原 `dev_platform` / `agent_platform` 版本与验证器|不修改冻结 schema、可信检查、批准权限或 canonical 编码；训练 prepare / worker 不启动实际训练|
|Skill metadata / 资产、记忆、研究和持久文档|沿用各领域现有格式及 schema_version|目录/修订/来源和领域状态由原模块负责；R2 不为旧 DB 强加重写。DB 迁移与旧客户端隔离由 R3 单独实施|

结构错误为 `CONTEXT at /field/0: REASON`；路径使用 JSON Pointer，`/` 和 `~` 分别编码为 `~1`、`~0`。缺失字段或额外字段的结构错误指向所属对象，并在原因中列出字段。业务错误继续给出具体原因，不假装 URL、文件可用性或评分判断都是 schema 规则。

`integer` 要求 Python `type(value) is int`，拒绝 bool 与 `1.0`；也与 `number` 使用同一有限数判定，防止范围关键词因两种类型判定不一致而跳过巨大整数。当前所有 integer 字段都有小范围上限，这保持原有字段的接受集合。`number` 保持 int/float 且可由原 `math.isfinite` 判断为有限的值，拒绝 bool、NaN、Infinity，以及超出该数值表示范围的巨大整数；后者转成可读的 ValueError，不让 OverflowError 中断用例。各字段范围来自原实现（例如 mini step 1–1000、cost >0 且 ≤100）。这比 JSON Schema 对“数学整数”的默认判定严格，外部校验器还须遵循这些领域语义。

评价版本号的旧检查使用 `== 1`，实际接受 `1` / `1.0` / `true`；R2 保留该兼容行为，其他版本仍拒绝。新文档和生成器始终写整数 `1`。如后续要求严格版本类型，须单独版本化迁移；本节点不静默改写旧输入或摘要。内置目录的未知版本仍由现有加载边界拒绝。

## 身份算法

|身份|当前实现和编码|不能替换成另一算法的原因|
|---|---|---|
|评价 manifest|`evaluation.manifest_sha256`：`json.dumps(sort_keys=True, ensure_ascii=False, allow_nan=False)` 后 UTF-8 / SHA-256，保留默认空格|原 `_sha` 仅改为语义名称；旧评价 suite 的摘要和候选证据须保持|
|reference canonical JSON|冻结 `dev_platform.contracts.canonical_sha` / adapter sha：排序、UTF-8、不转义 Unicode、紧凑分隔符、拒绝 NaN|原编译、request、profile、批准及回执使用此身份，不与评价摘要合并|
|Skill 目录|`skills.digest_tree`：排序相对路径；逐文件内容 SHA 和 executable bits；文件清单沿用原排序 JSON编码再 SHA-256|脚本执行位与内容共同构成资产；不能只 hash SKILL.md 或把不同换行/字节归一化|
|Agent 结果 / prompt / 文件产物|原所有者对实际固定字节计算 SHA；结果沿用排序、保留 Unicode 的 JSON|是不同用途的实际内容身份，不做统一的“自动标准化”|

A2 的固定向量、两种 compiled/request/profile 身份、Skill 执行位和合成旧状态继续作为回归依据。R2 只把测试中的私有 `_sha` 调用迁到实际语义名称，未改任何身份夹具。

## 增加或调整字段

已有驱动的配置结构在组件 configuration 修改，表单、目录与核心结构校验随软件包一起生效。跨字段的角色能力、凭据、可信文件和批准规则仍在责任模块实现；增加描述不会产生新的 SDK 适配。测试应验证真实输入/失败路径、CLI/API 一致性和必要的旧身份，而不是只将同一份描述抄成另一份断言。

引入新的格式版本或改变摘要编码须设计迁移、旧客户端访问与回退，不能以 schema default、DTO coercion 或数据重新 dump 代替。基础包只新增 schema 栈，Web / GEPA / Temporal 等仍是可选依赖；实际跨平台分发结果记录于 [R2 交付记录](../delivery/2026-11-02-schemas.md)。
