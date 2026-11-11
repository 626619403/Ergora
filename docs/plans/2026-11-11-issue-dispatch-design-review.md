# F7b.1 独立设计审查：来源合同与窄准入

日期：2026-11-11。审查者：fresh-context 独立设计审查 Agent；未继承 B0 reviewer 对话，未读作者 preparation 笔记，未启动其他 Agent。源码基线为 `3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`，分支 `refactor/architecture-foundations`。输入为原始需求、[AGENTS](../../AGENTS.md)、[PLAN](../PLAN.md)及尚未实现的 [B1 计划](2026-11-11-issue-dispatch.md)。B0 状态回写、新计划和本报告均属文档工作；未将 B0 的关联当作新正式来源。

**结论／建议：选择新版本 WorkflowInput，首片限显式 `work-units-v2` 组合。建议 definition／creation v3、envelope v7，复用 v6 六阶段和材料协议。** creation-only 方案按现源码不能满足原始执行输入与实际资料交付要求。B1b 应连带合法的轻量 Input／Adapter／Workflow 注册与资料路径，start 暂沿原广 doctor；B1c 再窄化新版本准入并验真实运行。这避免为分片增加临时注册表、不可构造 worker 或下一片删除的开关。

需求设计结论：有条件可实施；现计划仍须明确以下合同才能关闭 B1a。可维护性结论：现有所有者足够，不需要通用 wrapper/plugin 框架或第二套调度／claim。**本报告是设计审查，不是新产品实现、B1b 最终独立 review、Agent 消费证明或 B0 精确 CI 终核。**

## 1. 两方案的源码可行性

|方案|已核事实|取舍|
|---|---|---|
|新 WorkflowInput／definition|[reference_inputs](../../src/ergora/reference_inputs.py):13–70、199–234 已拥有原始 `document`、legacy `spec`、queue、request root、worker、adapter、activity 和 `start`。`VerifiedSpecClient` 在[运行读取](../../src/ergora/reference_task_runtime.py):43–58 核完整原始 JSON 后才给 native transport 投影。|推荐。新增具体输入继承 `StageResultsInput`；新 workflow 继承 `StageResultsWorkflow`，只改变明确版本身份和来源语义，不复制调度。|
|新 creation，委托原 inner v6|[creation](../../src/ergora/reference_task_creation.py):111–158 的完整 record 会进入 creation SHA，再经 [submission](../../src/ergora/reference_task_submission.py):39–44、149、185–190 绑定 memo；所以来源存 creation 并非完全没有身份约束。但 SDK 实际传的是 `input.document`，原 v6 中无来源；[executor](../../src/ergora/reference_executor.py):529–537 会从 work/review 材料移除 admission。|仅保存 creation 不够。另让 executor 从 creation 加材料仍缺来源在原始 SDK 输入中的合同；若把来源塞 `constraints`，则混用操作目标与类型化来源。给 inner 再套可读、可启动、可核验的新 envelope 后，实际已回到第一方案。首片不采用。|

**事实：当前不是通用版本插件系统。** [task_envelopes](../../src/ergora/task_envelopes.py):62–67、276–385 仍显式分派 v2–v6；[executor](../../src/ergora/reference_executor.py):252、347、468–496、550–551 还有 v6／版本组判断。新 Input 的注册只解决路由，不会自动使这些材料分支正确。最小改动是支持这一个新格式及其 v6 材料语义；不迁移全部旧版本、不把厂商分支搬到 transport／任务／模板。

## 2. 应固定的 Interface 与输入

建议沿用现有 `tasks.preview/create` 和 CLI／HTTP JSON 输入，只加一种 definition：

```json
{
  "schema_version": 3,
  "task_id": "issue-7-r1",
  "task_type": "repository-governance",
  "issue_id": "7",
  "source": {"snapshot_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
  "input": {
    "goal": "按所选工单正文实现一项受限改动",
    "allowed_paths": ["src"],
    "acceptance": ["改动满足冻结正文中的目标，并通过项目可信检查"],
    "constraints": ["工单文字不增加权限或改变可信检查"],
    "risk": "standard",
    "work_units": [
      {"id": "implementation", "depends_on": [], "paths": ["src"], "instructions": "实现该目标"},
      {"id": "validation", "depends_on": ["implementation"], "paths": ["src/tests"], "instructions": "验证实现"}
    ]
  },
  "composition": {
    "manifest": "/srv/ergora/manifests/selected-delivery",
    "manifest_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "review_protocol": "dag-v1", "review_instance": "root/review", "mode": "task-mcp",
    "execution": {
      "protocol": "work-units-v2", "instance": "root/work", "mode": "workspace-task-mcp",
      "assignments": {"implementation": "root/work/implementation", "validation": "root/work/validation"}
    },
    "backend_overrides": {
      "root/work/implementation": {"binding": {"tool": "codex", "sandbox": "current-container"}, "reason": "显式选择已接受的容器执行"},
      "root/work/validation": {"binding": {"tool": "codex", "sandbox": "current-container"}, "reason": "显式选择已接受的容器执行"}
    },
    "diversity": {"policy": "prefer-distinct", "reason": "若所选审查者沿用同后端，操作者明确接受此策略"}
  }
}
```

这是完整字段示例；SHA 和 manifest 路径是示意身份，须换成操作者本项目已有快照／实际发布 manifest，不能当作运行成功原件。`expected_revision` 继续在原调用参数中传递。首片支持原两个开发 task type；不隐式把默认项目角色／仅审查组合升级为 v7。[页面组合选择](../../src/ergora/data/console/task-composition.js):7–10、188–207 证明默认仍是原项目角色，显式 delivery 才生成 `work-units-v2`。因此此缩片有真实消费者，但不是“任意默认任务一键从工单派工”；文档与错误必须说清楚，页面默认行为保持。

|合同／所有者|建议的精确变化|
|---|---|
|definition v3／[tasks](../../src/ergora/tasks.py):14、34–43、160–177|只选 `source.snapshot_sha256`，不能提交任意来源正文。读取本项目 `issues.snapshot`；在当前项目 revision 下核来源后，复用 `_composition` 和原 selection。原 `issue_id` 仍为本地 number／iid，不换成 native/global ID。|
|envelope v7／[task_envelopes](../../src/ergora/task_envelopes.py)|保留 `legacy_spec`、`composition`、完整内容 SHA，新增 `issue_source`，携 B0 的完整 `{schema_version, sha256, first_observed_at, payload}`。payload 包含观察正文、原配置／绑定、API 身份、native ID、响应 SHA／ETag／updated_at；`context_only:true` 保持，来源不变授权。完整 envelope SHA 覆盖来源；B0 canonical SHA 仍只核 payload，`first_observed_at` 不冒充其一部分。|
|creation v3／[reference_task_creation](../../src/ergora/reference_task_creation.py):109–158、170–195、241|仍恰好原七文件；正文只在 `task.spec.json` 的新 envelope 中，definition 留 selector。增加 v3 的明确校验和读回，不修改旧 record。核 selector＝snapshot SHA、snapshot 项目＝本项目、来源＝legacy tracker 的 provider／namespace／local ID，以及来源与冻结执行配置身份一致。原 `compiled.json.spec` 仍等于 legacy projection。|
|来源数据 Module／建议 `issue_sources.py`|纯标准库，集中 canonical identity、快照读取合同和来源身份归一化。真实生产调用者是 `issues._snapshot`、`task_envelopes`；API 默认值／URL 规则若迁入，由 `issue_backends` 也调用同一所有者。不要复制一套 B0 格式校验或默认 host 表；也不要实现通用 JSON Schema 引擎。|

**事实／约束：** [issues](../../src/ergora/issues.py):75–86 的现有持久读取经 `issue_backends` 和 `contracts` 导入 `jsonschema`；[creation 子进程](../../src/ergora/reference_creation_process.py):24–30 明确使用 `-S`。因此 native 不能直接 import `issues`／`issue_backends` 复用。抽出的纯来源 Module 必须保持 B0 严格类型、内容 SHA、来源／绑定一致性和可离线读取；不能把 schema 移走后减弱旧读取。JSON Schema 可继续作为公开格式投影，格式规则应只有一个运行所有者。

**事实／建议：** [effective_configuration](../../src/ergora/projects.py):46–65 当前保留原 binding，并未补全缺省 `api_url`；[IssueBackend](../../src/ergora/issue_backends.py):28–40 目前用实现自身默认 API、`rstrip('/')` 和 URL 检查。应用应通过同一个纯来源函数解析规范身份，不能声称已有归一化字段，也不能改写原 configuration SHA 的含义。至少比较 `{provider, api_url, project}`，其中 API path 也属于身份。原 registration 只有 `{kind, project}`，只能核 provider／namespace，不能证明 host。

建议的时间语义：新 preview/create 要求 snapshot 的来源等于当前绑定的规范来源，并匹配登记项目；snapshot 的捕获配置 SHA／revision 可以旧于本次执行配置，只要来源相同。仅换 Agent、token 环境变量引用或其他无关配置不能使旧正文失效；换 API host／path、provider、namespace 或 local ID 必须拒绝此次新创建。创建后从其冻结 record 读取来源，不再查 snapshot head／当前 token／远端。来源更新不改旧任务或批准；未知 dispatch 恢复也不重新选来源。原 registration drift 拒绝仍保留，不在此片顺带重做旧恢复规则。

native ID 的可证范围须明确：它是 B0 捕获所得并由选定 snapshot SHA 绑定；改其值而保留所选 SHA 必须失败。离线没有第二个远端权威可证明一个重新伪造并重算所有摘要的 native ID 真伪，不能把 checksum 称为服务器认证。

## 3. 完整调用链与资料交付

```text
CLI / HTTP -> tasks.preview/create(definition3, expected_revision)
  -> issues.snapshot(本项目精确SHA) -> 规范来源匹配 + 原_composition/selection
  -> reference_creation_process.task_creation(-S)
  -> _Creation.compile/validate_record/publish(creation3、原七文件、envelope7)
  -> execution_input -> 新SourceInput(StageResultsInput)
  -> _Submission.prepare / 原任务锁 / 原submission intent
  -> cli.task_action: doctor -> task policy / trusted checks -> connect -> 原claim
  -> CheckpointedTransport: lookup -> attempt-before-send
  -> VerifiedSpecClient.start -> 新SourceWorkflow(完整envelope7、原memo)
  -> 新SourceAdapter + 原WorkDeliveryActivities -> 新request root
  -> reference_executor -> 本次work/review materials.issue_source
  -> 原固定祖先资料 / process monitor / 已选Agent Adapter
  -> 原approval / evidence / reconciliation / handoff所有者
```

新增具体 Input 应有 `.composition-v7` queue、`requests-composition-v7` root、可构造的 v7 workflow／adapter，保留 v6 `WORK_SUBMIT`／`WORK_POLL` activity 协议即可：不同 queue 已隔开，`submit_activity`、adapter root 与 evidence 的真实调用必须一致。无需为了版本号再复制一对 activity。[workers](../../src/ergora/reference_inputs.py):217–228 会遍历全部注册类，[worker bootstrap](../../src/ergora/reference_worker.py):56–60 会构造全部 worker；占位 `workflow_type()` 抛异常会破坏旧 worker，不能作为离线分片手段。

**必须补实际交付：** [executor](../../src/ergora/reference_executor.py):477–501、529–537 的 v6 work/review materials 只有投影后的 context／root_task。新增 `issue_source` 必须在这里从已核完整新输入加入本次材料，不能只依赖 context 的 admission 曾经存在。inventory／plan 的原 context 可携完整 admission；work/review 则携一次明确来源和其 SHA。完整正文属于任务数据，不进入 structural instructions、权限、可信 checks 或 MCP grant。原 Skill/context 祖先读取与父权限检查继续由原 manifest/input 所有者完成；无需把工单加入 MCP 工具权限。

v7 必须保持 `_declared_results`、`_work_ports`、`_composition_request` 的 v6 named-source／`stage-artifacts-v1` 语义。每个当前调用交付其所需完整来源即可，不把前次 `composition-materials`、prompt、admission 文件树再次当作下一阶段声明产物递归传入。原 author/session、候选 SHA、批准 receipt、工作单元分配、只读 review 和整合／验证流程保持。

**离线交接还有缺口：** [evidence index](../../src/ergora/reference_task_reconciliation.py):169–181 的 `contract.spec` 是 `self.spec` 的 legacy 投影；[handoff](../../src/ergora/handoff.py):33–43 也只核这份投影。新增来源不会自动进入可验证的 handoff 合同。B1a 必须选择具体来源投影：建议让完整来源成为 receipt 绑定的原产物，index 加 source SHA／artifact reference／admission SHA，handoff blob 携原字节并经共同来源读取合同核验；复用原 receipt/artifact/packet 所有者，不建来源账本。直接把完整 original_input 放 index 也能表达，但须接受其与 manifest 合计触发原 1 MiB 上限；不能只加一个未检查的 source 字段却声称离线来源已验证。旧 packet 的可读范围保持。

## 4. 准入与恢复：需要先固定的决策

**事实：** [native cli](../../src/ergora/data/reference/platform/local/agent_platform/cli.py):21–41 的顺序为读取 spec、doctor、policy／可信 checks、connect、claim、runtime.start。[doctor](../../src/ergora/data/reference/platform/local/agent_platform/doctor.py):18–19 会无条件取 A2A、MLflow、LangGraph 等包版本，缺包可直接抛错；其 ready 条件还要求 Codex、A2A 监听等。不能只从 ready 条件删一个服务，便宣称解除了未选依赖。

建议 B1c 在已核精确 creation 的**专用 submission 进程**中，让 Input 的共同 Interface 提供 admission report：旧 Input 调原 report；新 Input 检查自身实际执行依赖，临时替换 `doctor.report`，与现有 transport／task_spec 覆盖一起在 `finally` 恢复。返回完整检查事实；不是恒真 ready，也不是来自工单／普通文件的 marker。继续调用原 `cli.task_action`，不复制其 policy/checks/connect/claim。

新版本所需依赖应按真实角色选择：inventory inspector、plan planner、实际 work leaves、实际 review leaves；integrate／verify 是原可信执行。冻结 selection 里的默认 implementer／reviewer 在这些阶段未被选中时，不应被当作必需运行后端。复用 AgentBackend 的模式／策略／程序可用检查、所选 native 配置和 `task_mcp.check_available`；不是只验证 binding schema。保留 accepted current-container probe、原 execution_enabled、实际 Git／进程执行条件。Temporal 的真实 connect 仍在原位置；worker queue／executor 实际可用的证据须单列。包已安装、token 有值或配置标志，不证明模型认证／配额、worker 正在 poll 或 Agent 成功。

|恢复窗口|必须保留的行为|
|---|---|
|preview 后配置或 snapshot 内容改变|重新编译 SHA 不匹配，拒绝发布；create 仍持原项目写保留。source 身份而非无关配置修订决定 snapshot 是否仍可选。|
|creation intent 已存、部分七文件未发布／丢响应|原 intent 先于文件、task spec 最后暴露；resume 原 record，不重新抓取／重新选择来源，不覆盖冲突。|
|连接失败，尚无 attempt|保持 prepared；原 claim 可能已写的窗口仍按原 idempotent acquire 和原任务锁恢复。不能因来源有效就认定尚无 run。|
|claim 已持有、lookup 发现原 run／start 竞争|原 rejection，不能收养外部 run、自动释放占用或换 task ID 绕过。|
|attempt 已存、发送前后中断|保持 unknown；resume 仅按原 workflow ID lookup，完整原始输入与 memo 都匹配才保存 run receipt；NOT_FOUND 仍不能重发。|
|Agent／token／当前绑定变化后恢复|读取冻结 source／selection；不重写旧来源。不为只读 lookup 增加模型、tracker 或新准入依赖；原 registration drift 合同保持。|

原 claim 兼容不可变化：[IngressLeases](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/ingress.py):28–46 只接受 `{kind, project, issue_id}`，namespace casefold，跨 host 同 namespace 保守冲突；[native claim](../../src/ergora/data/reference/platform/local/agent_platform/ingress.py):7–14 仍用 `canonical_sha(legacy_spec)`、`local-cli` 和原数据库。**完整来源／原输入 SHA 与 claim projection SHA 是不同身份，各守用途。** 不把 API host 或 envelope SHA 塞进旧 claim，不新建 host-specific 数据库；否则旧入口竞争、release 和已存 claim 的恢复会分裂。

## 5. 原预算及实测反例

已核的限制不是同一个数：[creation](../../src/ergora/reference_task_creation.py):13–16、120–140 为单文件 1,048,576 B／intent 16 MiB；[stage context](../../src/ergora/reference_workflows.py):63–68 为 compact JSON 1,000,000 B；[最终组合 prompt](../../src/ergora/workflow_definitions.py):380–398 为祖先 prompt＋本次任务完整 UTF-8、上限 1,000,000 B；固定 manifest 和 [task MCP](../../src/ergora/task_mcp.py):50–84 还有各自材料／scope 限制。均保持原值。

已运行的只读纯内存设计探针在忽略目录 `.ergora/checks/f7-dispatch-design/readonly_probe.py`，原结果为同目录 `readonly_probe.result.json`。这是**非产品、合成 reader 形状／size-only v7**，不经过应用 graph admission，不是可提交的完整 B0/v7 实现：

- `python -S -B` 实际导入现有 creation／envelope／input reader；合成 v1–v6 均成功返回其原 queue／request root，未导入 jsonschema、Temporal、MCP。随后 import `issues` 明确失败 `No module named 'jsonschema'`。
- size-only 候选正文 345,579 个“中”（1,036,737 B），实际 `Creation.check_size` 接受 pretty spec 的 1,048,575 B；加入 legacy spec 与正常 context 外壳后 compact stage context 为 1,047,845 B，已超限。现 reader 明确拒绝该 v7，未称其已支持。
- 原 `_key` 对 namespace 大小写产生同一个 claim key，增加 `api_url` 明确报 `Invalid tracker identity`；未创建 claim DB。

建议在 preview／publish 前用同一来源材料组装逻辑拒绝**已知必然**超限的静态部分，并给出具体材料／stage 和实测 UTF-8 字节；不能只验 definition 或七文件。动态产物／候选 diff 在编译时未知，仍须在原阶段准备时按完整材料明确拒绝，不能承诺 preview 已证明整次运行一定适配。实现验收需有 ASCII、中文／多字节、恰好 limit／多一编码字符、祖先材料＋来源合计、以及后续产物增长的反例；不得截断、摘要、加预算或把字符数当字节数。

## 6. 最小实现片与 B1a 退出证据

推荐 B1b 包含：definition3＋纯来源合同＋creation3／envelope7、合法 Input／Adapter／Workflow 注册、原 executor 完整来源材料、离线 evidence/handoff 来源投影，以及原 CLI／HTTP preview/create/resume/read 旅程。start 继续调用原 doctor，不增加临时阻断类或 `worker_enabled` 开关；此片记录“离线发布验收、原广准入保留、窄准入未实现、实际 Agent 消费尚未验证”。如果要求第一片发布即证明无 A2A／MLflow 可正式 start，则合并 B1b/c；不能用离线验收替代这一要求。

增改文件应局限如下；新 Module 的真实调用者如上，无额外 facade：

|所有者|最小职责|
|---|---|
|`issue_sources.py`、`issues.py`、`issue_backends.py`|纯来源格式／归一化共享；B0 字节和读回语义保持，读取不访问凭据。|
|`tasks.py`、新 task-definition schema|选择快照、当前 source 匹配、原 preview SHA；CLI/HTTP 不复制厂商逻辑。|
|`task_envelopes.py`、`reference_task_creation.py`|新不可变身份、原七文件／限制和恢复；旧版本不隐式升级。|
|`reference_inputs.py`、`reference_workflows.py`、`reference_executor.py`|真实版本注册、完整 context／材料和 v6 declared-results 行为；复用全部调度／活动／monitor。|
|`reference_task_reconciliation.py`、`handoff.py`及确需的格式投影|来源原字节／SHA 的证据与离线核验；原 packet 限制及旧合同保持。|
|`reference_task_submission.py`＋Input 运行方法（B1c）|作用域内真实依赖 report；原 intent／attempt／memo／claim 顺序不变。`reference_task_runtime`、approval/evidence/events 等优先仅通过已有 Interface 消费，不加另一版本分派表。|
|已有相关测试、CLI/HTTP样例和本片文档|复用 creation/submission locks、composition transport/workers、work agents、handoff 夹具，不新建同构 CI。|

关闭 B1a 前，计划／交付记录仍需明确落下四项：

1. 确定上述字段、唯一纯来源读取所有者、同来源旧配置快照／来源切换／已发布任务恢复的时间语义，以及新定义支持范围；将上例的示意身份换成验收将使用的精确来源／manifest，并记录新输入。
2. 固定 v7 queue/root/activity、全部受影响的 v6 材料判断及 evidence/handoff 来源合同；确认 worker 可构造、旧 v1–v6 类保持，不以 registry 登记替运行证明。
3. 固定各预算的校验时机、完整资料传输位置和错误；处理本报告反例，区分静态可预拒绝与动态阶段超限。
4. 固定 B1b 的原广准入过渡范围、B1c 实际依赖矩阵、上述 durable windows 和旧入口竞争验法；不能凭 source 字段／link 跳过 doctor。

后续实现仍需自己的证据：新安装包及真实 CLI／HTTP离线读取（删除 tracker token）、错误 host／namespace／local ID／native ID／SHA、来源切换与无关 binding 修订、creation 部分发布／冲突、合法 worker 构造及旧输入恢复；B1c 的真实新原始 payload、全六阶段／精确 owner 批准／candidate、选定实例完整祖先和来源读取原件、原 ID start／竞争／attempt 后丢响应／memo 错配／unknown lookup、证据与 handoff 读回。所选后端不可用／缺 runtime 应明确失败，无关 A2A／MLflow 缺失应不阻断新入口。再做真实自身模板与新的完整独立两轴 review，才可关闭实现片。

本轮仅只读源码及相邻调用、检查现有 fixture 结构、运行上述便宜纯内存探针，并写本报告／忽略目录原件。未安装、联网、认证、运行模型、整仓测试、改源码、提交或启动服务；没有对 B0 CI、SDK worker 构造／历史 replay、真实 Agent 字节读取、Windows 新格式或新版本恢复作通过声明。上述未验事项是实现验收责任，不是本设计报告已完成的工作。
