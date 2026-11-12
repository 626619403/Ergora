# D0／X1–X3 独立事实与设计审查

日期：2026-11-12。评审者：新的 Codex 独立 Agent，任务身份 `/root/specialist_adoption_review`；fresh context，未继承作者实现对话，未参与候选研究或实现。收到原始要求、固定基线、七文件清单／实际差异及真实验证范围后，先读要求、差异和仓库约束，再读作者说明、相关消费者及固定来源原件。遵循 [AGENTS](../../AGENTS.md)、`maintainable-project-delivery` 的 independent-review 规范及 `codebase-design`。

## 精确范围

产品基线为 `5ab6d350024de8515487d0bedb3b950be60ac867`，本片 Git 基线／所审 HEAD 为 `9abbb6448cf42548f598e53faa342e261671b354`。本片只改七份 Markdown，没有产品、测试、CI 或依赖变更；产品相关路径与产品基线没有差异。审查工作树的实际完整内容，包括交付记录中未暂存的静态检查说明；全部字节与私有 `d0-review-input.json` 一致。

|所审文件|字节|SHA256|
|---|---:|---|
|[PLAN](../PLAN.md)|29641|`f37317891c2823ddec2db1a39905a0e560106c8da4cce8490c2e35465ba7a692`|
|[分片计划](../plans/2026-11-12-specialist-template-refresh.md)|11199|`9a13bfe6a78a7c1df1be47a24e6aadb6b20656ec72088ccb185b00256a8cdc23`|
|[交付记录](2026-11-12-specialist-template-refresh.md)|13839|`761b7b175e466cdf21c50769c8c4c98e4f1e1acdd31dc2fa8a3659180520c8cc`|
|[D0 采用矩阵](../research/2026-11-12-specialist-adoption.md)|21572|`65cb011a300b99d7f0504f657390e172bf7767cf1ece384d253e531ac70192a6`|
|[X1 架构／系统](../research/2026-11-12-horizontal-architecture-agents.md)|42741|`f32e30df1573d913e6133b5aaf6eaa9d77de3c84437fab61ce2cb0e57e08a4f7`|
|[X2 kernel／端到端](../research/2026-11-12-horizontal-kernel-agents.md)|43449|`b8394b3dae7fb596c1a515fa949b2e320e3ade7af795b77a6859f71b346084c2`|
|[X3 诊断／实验](../research/2026-11-12-horizontal-experiment-agents.md)|44851|`2a4e28117f8b6f3e8c27fddee2c13c7837bd43dba7a753383a2a4b5ddb282c17`|

重新生成的这七文件 `git diff --binary HEAD` 与所给 `d0-review-tracked.diff` 逐字相同，SHA256 均为 `277724bbd8ed6d7414e105156b88d62c42d3d8d3bae073ba66382c37e2dec8eb`。本报告为另行授权的评审记录，不属于上表候选。R1–R10 用作已有纵向依据，未重做全市场搜索或重新审查其全部事实；U1/U2 的既有安装验收保持原范围。

## 两轴结论

|轴|结论|开放 finding|
|---|---|---:|
|Spec：原始要求与本片出口|通过本片文档范围。纵向之后的横向关系、采用形态、真实消费者优先序及 D1 拆分可支持下一片设计。|0|
|Standards：所有权、复用与可维护性|通过本片文档范围。复用既有运行与证据所有者，没有新增调度器、正式账本、执行 DSL 或无人消费的插件接口。|0|

本片范围内没有已证实的 P0–P3 finding，故没有需要作者修复或处置的阻塞项。此结论不授予任何新 native 模式运行准入，也不关闭 D1–D3 或整个专家模板重整任务。

## 事实与设计核对依据

|核对面|原件／实际消费者与判断|
|---|---|
|X1 联合架构搜索|抽核固定 ModelOpt 的剪枝入口、TP／ETP 限制和 Puzzletron runtime／部署说明；nnScaler 的 `1f1b`、pipeline solver 与指定 recompute 模块；Aceso 的超显存优先和动作效应；Galvatron 的 Hydra 输入、2.4.1 依赖、CP 默认、搜索／checkpoint 路径；Unity 的 `RuntimeOnlyCostEstimator`、budget 和 PCG／mapping 输出；FT-Agent 多个 `APIBackend` 会话。原件支持报告区分结构、运行和代码架构，以及按真实 runtime 条件适配的决定。确定性 solver 未被冒充 LLM 专家。|
|X2 内部流程与接缝|抽核 Forge 旧 pin 的 `RealBackend.run_agent`、每 turn policy、独立 goal 路径及 `FK_CLAUDE_BIN`；GEAK 实际 `kernel_lane.js` 路由、统一 `runAgent` 和默认 CLI 权限；Fuser composer 的未 verify 成功路径、2400 秒自测及 KernelAgent 默认追加测试；AKG 的逐文件／总量截断、Skill top-k、compact／fast 调用和 workflow timeout 放大。支持将四套系统保留为完整流程候选，当前不宣布全会话继承、父权限或完整取消已满足。CLI wrapper 仍仅为待验证接缝。|
|X3 搜索与恢复|抽核 AIDE search policy、反馈抽取 metric、实际模型默认、无总上限 backoff、共享 workspace、解释器 PID 清理及新建 Journal 入口；Optuna 5.1.0.dev、每 process 的试次数、objective 边界 timeout、heartbeat 与 retry；Tune 配置、restore、ASHA 缺字段行为及剩余预算反序列化。原件支持报告的候选隔离、硬预算及原作业对账限制；没有把 study／journal／Tuner 恢复升级为训练 checkpoint 恢复。|
|论文与收益口径|对照 Unity 官方会议页、AIDE holdout 协议／表格、Forge／GEAK／robust-kbench 已归档论文文本的核心陈述。报告均保留作者实验条件，区分旧论文与当前实现，并明确没有在 Ergora 复现。未读 PDF 正文的部分没有借来授予收益或功能。|
|定义、资料和父权限|[AgentDefinition](../../src/ergora/agent_definitions.py)、[WorkflowDefinition](../../src/ergora/workflow_definitions.py) 及两份 schema 支持多 roles／specialties、精确重复引用、结构父链资料累加和静态权限检查；节点选定一个受支持 role。`agent_runs` 的逐调用准入与固定 task-MCP 不构成任意外部 endpoint 或完整 native 内部会话合同。D0 对标签、后端、职责、数据交接与权限来源的区分一致。|
|正式运行及唯一所有者|核 [WorkflowInput](../../src/ergora/reference_inputs.py)、[原 workflow](../../src/ergora/reference_workflows.py)、[tasks](../../src/ergora/tasks.py)、[Executor](../../src/ergora/reference_executor.py)、[WorkDelivery](../../src/ergora/review_dags.py) 和 [kernel](../../src/ergora/kernel.py)。当前正式投影只覆盖原 work／review，六阶段不能因静态嵌套直接被调用；Forge 仅有原 campaign 操作且不接父资料。D0 选择六阶段为首通用消费者、Forge 为首 kernel 消费者，与这些缺口相容。|
|评价与实验所有者|核 [GEPA](../../src/ergora/optimization.py)、[评价](../../src/ergora/evaluation.py) 及冻结训练 runner／perfctl／compare_runs 的相关调用。报告准确保留文本资产用途、原 candidate 门禁、MLflow 观测投影和固定样本比较器的统计限制；Optuna 仅在真实 runner 内条件消费建议，没有新设搜索或恢复控制面。|

技术方向与职责为多对多关系；同一精确定义可在不同实例与模板复用，每次实际会话／后端／权限／结果分别保留。执行与审查优先异构，以及 Claude 不可用时明确回退 Codex 的约束均有保留；不同后端未被写成错误统计独立的证明。串行局部、并行隔离候选及原生内循环各有范围，组合产生新候选并重新评价，没有从单项收益相乘推出整模收益。

已接受的当前 Docker／可信项目边界继续成立，允许 Agent 访问当前用户文件，不需要宿主权限或重新取得这项授权。上表的静态权限链与声明限制不证明 OS 隔离。现有[调用前能力矩阵](../WORKFLOW_DEFINITIONS.md#调用前查看能力与权限)仍区分 `enforced`、`advisory`、`unsupported`；新 native 模式须诚实报告实际保证。对某个新模式无法满足的严格父上限标 unsupported，不等于把已授权的旧 trusted 模式判成未授权。所审文档没有宣称更强 OS 隔离，也没有新增宿主权限／反复审批前置条件。

## D1 尚待验收的责任

这些是 D0 已明确留下的实现责任，不是本片开放 finding：

- D1a 要在真实消费者上固定输入版本及投影。当前 WorkDelivery 要求 work／review 覆盖全部 Agent leaves；不能直接向旧正式图添加 inspector／planner。Executor 目前仅 work／review 走完整 composition 调用，inventory／plan 仍用旧提示路径，部分依赖正文有切片。设计须列清这些缺口并保留旧版本，D1b 再证明全阶段父资料与实际权限／后端能力。
- D1b／D1c 要沿原 WorkflowInput／Executor／任务意图建立总预算、完整材料和单实例调用消费者，原 task／run、批准、取消及 unknown 仍由原所有者判断。当前没有通用父总墙钟／API 预算消费者；研究合同或新增 schema 不可当作实现证据。
- D1d 要沿真实 CLI 核每次实际内部调用、候选证据、原 ID 恢复和清理。首片仅支持所验单实例；多实例并行 native 流程、任意混合图、Forge 全会话、外部 MCP 与真实训练／GPU／多节点收益仍各自待后续片，不能借本次审查关闭。

## 实际检查与限制

- 独立重算七文件字节／SHA、完整差异身份，以及三来源目录索引中 1531 项原件／索引／派生／必要产品输入的字节／SHA，均一致：X1 inventory 1401、X2 新取／派生 52、复用 27、必要本地产品 6、X3 HTTP 45。另核 X2 三件仅有 receipt 的失败获取记录存在。此为完整性核对；没有声称逐行语义审查全部 1531 项。首次私有核验脚本误把无 raw 的 404 receipt 当正文，修正后将其分开登记，原错误说明保留。
- 独立检查七候选的 179 个本地链接目标及 `git diff --check HEAD`，均通过；加入本报告后再次检查八文件、198 个本地目标、六个已加载秘密值及公开路径，issue0，本报告全文无尾随空白且末尾换行。未验证锚点、Mermaid 渲染或外部 URL。作者 `checkpoint-3-static-r1/result.json` 保持其原字节范围，未将旧交付记录 SHA 授给之后的说明更新；最终交付应重新冻结实际文档身份。
- 私有核验原件在 `.ergora/checks/specialist-template-refresh/d0-independent-review/`。本报告只写所属项目文档，没有改候选／产品、安装依赖、发起网络读取、调用模型／GPU、运行旧产品 CI、提交／推送或发送 SaaS 消息。

当前可进入 D1a 的具体设计与立片；产品运行验收及最终完整文档候选的收口仍由相应片完成。

## 同片补核：D1a 明细与进度增量

2026-11-12，由同一独立评审者做有界补核。新增范围为 [D1 六阶段消费者计划](../plans/2026-11-12-six-stage-native-consumer.md)，以及 PLAN、上层计划、交付记录、D0 对首轮审查和下一片的记录更新；没有重新运行横向来源完整性检查或重新审查未变的三份 X 报告。Git／产品基线同首轮，产品、测试、CI、依赖及 283 冻结参考文件未变。

补核的八份作者文档全部与私有 `d0-review-input-r2.json` 的实际字节／SHA 一致；其中变更或新增的五件身份如下。X1–X3 三件维持首轮表内完整 SHA，不以状态记录更新重新授予其运行能力。

|文件|字节|本轮 SHA256|
|---|---:|---|
|PLAN|29821|`34b9ec74d4f2db9726383ac889cd89f90840831fafc924ddb100dd351493ee88`|
|专家模板重整计划|11314|`97b0caf52a6d0d3fc0d60ccc66a97de4b7e0b0fdddc2938a9515d965ea4df5d8`|
|专家模板重整交付记录|14908|`3e8644e08cc1a49cd57175fcf9ce04ed3e8878812ff82b1af165405fc50093e3`|
|D0 采用矩阵|21778|`062f3d4c1f09479d442e1b37bcd0e66b3844237f9a837f0b1726b0d4cb75bd7f`|
|D1 六阶段消费者计划|9892|`c0bfd248eda0b0c3863994b97ad198604ba359cff50d541ba566fd8e9e5458f6`|

这八件作者文档的实际完整 `git diff --binary HEAD` 与 `d0-review-followup-author.diff` 逐字相同，两者 SHA256 均为 `45030ea9ab8bf204acf9ec5656addc8541bb29cce82c226a7d733959af1ec01e`。上表是补核输入身份，后续纯进度收口应另记其最终身份；不覆盖首轮身份或声称原判词自动审过之后的内容。

|轴|补核结论|开放 finding|
|---|---|---:|
|Spec|通过 D1a 设计及记录增量范围，与 D0 的依赖、单实例范围和旧对象保持一致。|0|
|Standards|通过设计范围；选中实际 task 消费者，保留原版本、运行、批准和进程所有者，切片没有引入额外调度或无消费者抽象。|0|

没有新增阻塞或需修复的语义 finding。上层计划 X1–X3 行的旧“待独立审查”文字可随本次补核完成一并同步；这是进度收口，不改变已审采用决定或产品合同。

必要源码抽核支持以下判断：

- 原 `tasks.preview/create/start` 经过原创建／提交意图，`VerifiedSpecClient` 核完整原输入身份后经版本化 WorkflowInput 启动。首片继续 client start、父实例只关联原权威，符合唯一所有者；目前没有需要增设 Temporal parent／child 层的真实消费者。
- Executor 的前阶段旧路径、60k 依赖切片和 WorkDelivery 全叶覆盖限制仍存在。B1 显式新增全阶段投影、受限前阶段输入及完整 Git blob 消费者，要求完整或拒绝，并保留旧 schema／queue／request-root 语义，符合 D0 的全阶段父合同。review 专用 collector 没有被直接当作通用 inventory 工具；结果 schema 也没有被误写成已有可信 patch 应用者。
- task-MCP 的 audit 记录 method／tool／success 及 scope／协议元数据，当前不记录 read 的 URI／offset／实际返回范围；native 核验以成功 tools/list 为就绪证据。新计划正确区分就绪、完整资源、连续字节交付与模型理解；新增读取审计或完整 transcript 的工作有实际消费者。
- `workspace-task-mcp` 的 read／write／egress 仍为 trusted current-container 下的 advisory 保证。新计划明确保留这项已接受边界、原 Git 门禁和旧 writer，不要求宿主权限；更强严格上限仅在选中的新模式无法实施时 unsupported，没有倒推旧模式未授权。
- B2 只承诺实现总墙钟及已知模型 invocation 数量，明确一次 CLI 不等于一次 provider API，token／费用等无实际计量的严格维度 unsupported。首次授权 prepare、队列及 owner 等待计时、恢复不重领额度和 unknown／停止分开均有明确验收面；当前尚无该聚合预算消费者，计划没有提前宣称存在。

B1 材料、B2 总预算、C 单实例原生消费、D 实际旅程的先后和可独立出口一致；B1 不关闭预算或嵌套，C／D 完成前不发布可执行子模板。多 native、任意混合图、外部数据依赖、远端和 GPU 收益仍保持未支持／待后续。D1a 可记录设计补核完成，下一实现出口为 B1，之后仍各自需要同候选行为检查及新的独立产品评审。

本次独立重算八作者文档身份、完整差异和 201 个本地目标，Git whitespace 通过，产品相关路径相对产品基线无差异。原件为私有 `d0-independent-review/followup-r2-identity-static.json`；作者 `checkpoint-3-static-r2/result.json` 的九文件／220 本地目标／六秘密值检查保持其补核前身份。加入本补核后独立检查九文件、221 个本地目标及六秘密值，issue0，本报告无尾随空白且末尾换行；之后纯进度收口仍需冻结其实际最终身份。不验锚点、外部 URL、Mermaid 或任何产品运行；没有新网络、安装、模型／GPU、旧 CI 或发布操作。
