# 为正式任务冻结审查组合

简体中文 · [English](../../development/preparation.md) · [文档目录](../../README.zh-CN.md)

原`schema_version: 1`继续使用四角色绑定和完整六阶段。新`schema_version: 2`冻结完整组合包及每成员后端，支持预览、创建、发布恢复、启动和原运行状态查询。正式审查支持单个只读reviewer，或多个嵌套只读审查分支通过显式all-join汇合。每个叶子的输入必须沿全部结构祖先直接映射到根task，且沿途没有前驱依赖。其他合法静态组合仍可保存和查看，提交前会明确拒绝未支持的形状。使用本版Ergora管理的worker和executor；旧运行器不支持新信封。

先按[完整组合包说明](../../definitions/workflows/compose.md#save-and-share-a-complete-composition)准备manifest，并用`verify-manifest`取得其`digest`。在原任务定义中将`schema_version`改为2，增加下列`composition`字段，其他输入保持原模板格式：

```json
{
  "manifest": "/absolute/path/to/review-manifest",
  "manifest_digest": "REPLACE_WITH_THE_VERIFIED_DIGEST",
  "review_instance": "root",
  "mode": "task-mcp",
  "backend_overrides": {
    "root/review": {
      "binding": {"tool": "codex"},
      "reason": "Claude不可用，选择已配置的Codex/ChatGPT"
    }
  },
  "diversity": {
    "policy": "prefer-distinct",
    "reason": "当前只有Codex可用，接受执行和审查共享后端"
  }
}
```

此例用于`structure-review`包；其他包应填写其真实成员路径。`manifest`是运行CLI或HTTP服务的机器上的本地路径，推荐绝对路径。首次只接受单`task`输入且不依赖未执行外部节点的review工作流子树，所有叶子必须是只读reviewer。`mode`可选`text-only`或`task-mcp`，保存能力合同不证明CLI、认证、SDK或服务已经可用。

使用三专长并行审查时，先按[示例导入顺序](../../definitions/workflows/compose.md#run-the-example)导入三个专家与四个审查工作流，然后准备总审查包：

```bash
ergora composition prepare-manifest parallel-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./parallel-review-manifest
ergora composition verify-manifest ./parallel-review-manifest
```

在任务的`composition`中使用该目录与返回的digest，`review_instance`仍为`root`。成员路径分别是`root/structure/review`（结构，默认Codex）、`root/correctness/review`（正确性，默认Claude Code）与`root/test-value/review`（测试/CI价值，默认Codex）。需要覆盖后端时，将上例`backend_overrides`的key换成对应路径；可同时覆盖多个成员。每份定义保留自身声明的Skill和初始指令，并完整继承根和所属子模板材料。

三个审查者检查同一精确候选、原验证报告与批准计划，分别保存job、工作区、调用及收据；并发受共享项目和祖先模板限额约束。此例所有分支都是必需审查，任一请求修改、失败、超时、缺失或复用作者/其他审查会话均不通过。全部通过后，原outcome的`review`为`composition-review-aggregate`，逐成员保存原stage/job/收据摘要；它不是额外的模型或人工批准。`task evidence`和交接包可继续读取这些独立原件。worker重启后从原history继续，不重派已经发布的相同job；取消及未知外部作业仍沿原fence/对账流程处理。

需要建议审查时，导入[review-requirements示例](../../definitions/workflows/contracts.md#static-required-and-advisory-review-declarations)，然后准备其完整包：

```bash
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
ergora composition verify-manifest ./review-requirements-manifest
```

继续使用`schema_version: 2`任务定义，将manifest与digest换成本次结果；成员路径为`root/structure`（必需）和`root/test-value`（建议）。职责由WorkflowDefinition v2的节点实例声明，至少一名必需审查者，不能用后端覆盖改变。混合树中的旧v1审查叶子仍为必需。创建后保存为正式信封v3；这是运行协议版本，与用户任务定义和工作流定义的版本分别管理。

所有分支仍须完成并进入显式all-join；这种新职责图即使只有一名审查者也须声明汇合，输出直接转发task或叶子result不获正式运行支持。旧v1图的单叶行为保持。建议成员的合格`request-changes`保留原`FAILED`回执及finding，可信聚合v2逐成员记录`review_requirement`、`decision`和原收据引用；只在必需成员全部批准且其他合同满足时到达`REVIEW_READY`。建议成员的进程失败、候选不符、证据缺失、会话复用、超时或取消仍阻塞并沿原fence/对账处理。原始意见不会因汇合而被改为批准。

需要先结构审查、再并行进行正确性和测试价值审查时，导入[serial-review](../../definitions/workflows/contracts.md#data-ports-for-formal-read-only-review)，准备其完整manifest，并在同一任务定义的`composition`里增加：

```json
"review_protocol": "dag-v1"
```

将manifest路径和digest换成本次结果，成员路径仍为`root/structure/review`、`root/correctness/review`、`root/test-value/review`，后端覆盖仍按这些路径填写。这个明确选择保存为正式信封v4；没有字段的旧任务仍使用原v2/v3。前驱完成后，下游才获得其全部原产物，独立就绪分支受祖先限额调度；只配置depends_on而没有端口绑定时不会自动传入前驱正文。三个结构父模板的Skill、MCP和权限不会通过数据箭头互相继承。所选review子树须为单task输入、单终结输出，终点是完整传递覆盖的显式all-join；支持嵌套多具名输出，所有叶子仍为只读reviewer。

不提供覆盖时使用定义指定的后端；覆盖按实例路径逐个选择并记录原因。`prefer-distinct`为默认策略，与implementer同后端时必须填写`diversity.reason`；`require-distinct`直接拒绝相同后端，`allow-same`允许。同后端判断比较工具实现，不代表不同工具的模型错误互相独立。密钥继续由环境变量或受保护的本机认证提供，不写入定义。

使用[预览/创建命令与 API](tasks.md#预览与创建正式任务)，再按[正式任务顺序](tasks.md#正式任务的操作顺序与恢复)使用`task start/submission/resume-start/status/plan/approve`。预览的`files.task.spec.json`是显式版本化信封，其`legacy_spec`保存未改的原六阶段投影。`composition.manifest`携带完整文件字节与可执行位，信封SHA同时绑定静态图、祖先材料、成员、政策和多样性决定。创建后移除源manifest或修改活动库/项目绑定，不影响保存的原意图和发布恢复；`runtime_supported`只表示当前运行桥支持该静态形状；它不检查认证、模型、SDK或服务就绪，不代表运行成功。

组合任务按正式信封版本使用独立的composition-v2、composition-v3或composition-v4队列与请求目录，六阶段、计划批准、候选验证及收据仍由原有所有者处理。旧worker不能接管更新版本；升级时停止旧worker/executor并由本版`services`重启，保留原history与状态目录。每阶段绑定完整原信封；状态和恢复核对原Temporal输入，不能用相同legacy投影替换不同manifest。审查调用保存完整祖先材料、原模板指令、批准计划和验证产物，以及任务与叶子共同读取范围内的base/candidate源码和diff。源码、依赖摘要、调用及结果均绑定同一候选；原monitor继续负责超时和取消。只读工具配置不等于操作系统隔离。组合任务的取消也核完整原信封，沿同一`cancel/cancellation/resume-cancel`和原signal恢复；`requested`仍只是投递事实，外部终态与租约按原`external-status/reconcile`核对，清理后保留原outcome。

完整组合包导出仍支持10 MB/500文件。正式 wire、上下文、普通文件和总量限制取决于实际输入合同。统一使用[当前合同与限制参考（英文）](../../architecture/contracts/formats.md#supported-task-routes-and-material-limits)；独立叶和静态资源限制仍各自独立。保存与备份范围仍是登记执行状态目录中的任务七份合同、完整意图及结果回执；单独备份控制库不包含它们。原v4只读DAG及v5工作组合的前驱全部原产物完整内联，长审计链仍可能超预算。`kernel-delivery`仍只能静态预览，不能把manifest当作全部节点已执行。

需要将实现专家分配到原工作单元，再承接总审查时，按[专长执行者配置](../../definitions/workflows/contracts.md#specialist-writers-and-original-work-units)选择`execution.protocol: work-units-v2`；用户任务定义仍为schema-v2，正式信封为v6。页面“完整manifest · 组合执行与审查”使用此协议。v6完整传递声明阶段产物、可信检查与审查意见，执行审计留原receipt/evidence/handoff并继续逐件核验，避免下游递归复制旧提示；控制依赖未绑定端口时也保留结果。祖先资源、批准、候选及原恢复门禁保持；旧`work-units-v1`/v5任务不自动迁移。升级worker/executor后才能接收新v6队列，完整执行仍要求Linux/WSL2和显式可信容器。

## 为盘点和规划选择模板 Agent

当前使用 [task-definition schema8](../../../src/ergora/data/schemas/task-definition-v8.json)／正式input12。[完整材料配置](../../definitions/workflows/contracts.md#complete-inventory-and-planning-materials)让inventory和plan各选择只读工作流子树及canonical coordinator；成员按原祖先并发上限执行，协调者消费完整原前驱成果。每位planner收到原canonical inventory，只有inventory协调者执行可信baseline检查。

图形向导、CLI与HTTP共用此合同；单成员组也使用同一表示。准备、工作和审查完整覆盖全部叶，Skill读取、来源绑定、原owner计划批准与候选证据仍需满足。实际图例见[18叶MoE示例](../../../examples/composition/optimization-selected-moe/README.md)，静态准备不启动训练或采集profile。

## 一次授权的预算准备

Linux／WSL2使用同一schema8，在定义中显式选择native实例和preparation DAG，并填写`budget`，例如`{"wall_seconds":3600,"cleanup_seconds":60,"model_invocations":16}`。清理预留包含在总额内；模型启动槽上限须覆盖所选inventory、plan、work和review全部调用，不等于后端内部API请求或费用。

```bash
ergora task prepare my-project --definition task-definition.json --revision 1
ergora task preparation my-project TASK_ID
ergora task preview my-project --definition task-definition.json --revision 1
ergora task create my-project --definition task-definition.json --revision 1 --prepare-sha256 PREPARE_SHA --preview-sha256 PREVIEW_SHA
```

首次prepare在读取安装和材料前保存唯一预算。丢回执后读取原TASK_ID，不重开时钟；仅在`status: prepared`后预览和创建，并确认prepare与preview两个原摘要。创建后沿原`task start/submission/resume-start/status/plan/approve`执行；当前worker／executor消费`.composition-v12`队列和`requests-composition-v12`请求根。材料读取、排队、人工批准、恢复、模型／可信命令及收尾均消耗同一期限；重启不续时。已移除的preparation input8–11须由原安装完成、取消或对账，本安装明确报告unsupported。

`unknown`表示原attempt或清理尚未确认，失败／耗尽不发表可用准备成果。先核原身份与停止证据，不自动重跑body、重发或删除job账本释放名额。工作截止后不再新增工作；总额耗尽仍未确认停止时保留unknown／CANCEL_UNCONFIRMED，晚结果不能发表过期SUCCEEDED。完整状态、HTTP字段、备份与恢复边界见[同源当前预算指南](../../development/preparation.md#prepare-under-a-single-budget-authorization)。

## 将六阶段作为一个子模板调用

同一schema8／input12用`composition.native`将普通父模板内的一次调用绑定到原六阶段。先按[示例依赖顺序](../../../examples/composition/README.md)导入准备、工作及审查包，再导入[native-development](../../../examples/composition/native-development/workflow.json)并生成完整manifest。保留实际父manifest的path／digest、预算与mode，在`composition`中设置：

```json
{"native":{"protocol":"six-stage-v1","instance":"root/development"},
 "review_instance":"root/development/review"}
```

其他必需字段见[当前schema8](../../../src/ergora/data/schemas/task-definition-v8.json)。`execution.instance`为`root/development/work`，work unit指向其真实Agent叶；`preparation.inventory/plan`用`{instance, coordinator}`选择各子树，协调者路径追加`/coordinator`。后端覆盖使用完整实际路径，权限不能超过祖先。

沿同一`prepare → preview → create → start`顺序确认原摘要与原计划。祖先只包含该native调用并直接转发task／result；work和review为其直接子模板，inventory／plan可有结构包装。第二native、额外父分支或任意混合外层图未获此合同支持。完整选择与恢复义务见[当前native指南](../../development/preparation.md#invoke-the-six-stages-as-a-subtemplate)。

## 为正式任务选择项目记忆与活动 Skill

同一[task-definition schema8](../../../src/ergora/data/schemas/task-definition-v8.json)／input12支持可选context。先以`ergora memory catalog PROJECT`读取有效记忆id／revision，用`ergora skill list PROJECT`读取活动Skill名称／digest／revision；保留`schema_version: 8`并附加实际身份：

```json
{"context":{"root_version":"1.0.1",
 "memories":[{"id":"MEMORY_ID","revision":2}],
 "skills":[{"name":"your-skill","digest":"ACTIVE_SHA256","revision":1}]}}
```

选择与完整原资料在首次准备时冻结；恢复读取原冻结输入，不热换活动head或撤销历史任务。候选生成、可信评价、明确采用／回退和新任务冻结是不同操作，见[完整改进旅程](../../improvement/workflow.md)及[当前context合同](../../development/preparation.md#select-project-memories-and-active-skills-for-a-formal-task)。

## 使用重构配方

`refactoring`把行为保持重构交给原`large-change`六阶段所有者。默认依次安排资料盘点、计划及原owner批准；重构执行者完成`rewrite`后，兼容性专家在集成了前驱的候选上完成`compatibility`；原可信integrate／verify之后，结构、正确性和测试价值三个必需reviewer并行审查。

```bash
ergora composition install-preset refactoring
ergora composition prepare-manifest ergora-refactoring-template 1.3.3 \
  --grant examples/composition/refactoring/grant.json \
  --directory ./refactoring-manifest
```

示例位于仓库[refactoring目录](../../../examples/composition/refactoring/README.md)；wheel中已含全部Agent和子模板，使用自己的grant时无需examples。将[task.example.json](../../../examples/composition/refactoring/task.example.json)复制成任务定义，填写真实工单、task ID、baseline、manifest路径／摘要及项目内实际模块／caller；同时核完整资料范围、行为不变量、迁移和隔离回退检查。随后沿原`task prepare → preview → create`的双摘要确认与start／计划批准流程。有效JSON或prepare成功只证明合同可装配，行为保持由实际检查和审查证据支持。

全部内置专家使用Codex gpt-6.1-sol：规划max，跨文件重构xhigh，兼容验证与独立审查high。完整`backend_overrides`须保留满足定义最低线的model／reasoning_effort；writer仍需明确选择current-container。`prefer-distinct`同后端选择须记录`diversity.reason`，`require-distinct`继续拒绝同后端。兼容性工作单元不替代独立最终审查。

父模板直接包含标准[`ergora-codebase-quality`](../../../src/ergora/data/presets/workflows/ergora-refactoring-template/skills/ergora-codebase-quality/SKILL.md)，所有后代继承完整Skill，依目标仓库适用规范、配置、真实调用者和测试接缝工作。原任务／预算／候选身份及恢复owner保持；安装和静态preview不批准业务迁移。

重构执行者、结构审查者、正确性与测试价值审查者、兼容验证者的定义和组合均由本仓库维护；工程指导借鉴[Agent定义](../../definitions/agents.md#built-in-specialists)，并保留各来源许可。它们是独立可版本化的专长配置，Codex／Claude Code是实际运行后端。选一个后端不等于导入该工具的全部私有提示、Skill或调度框架；后端能力及资料完整读取按[Agent手册](../../agents/backends.md)分别核验。

只想在独立项目调用中使用 Skill 时，可从本仓库 checkout 根执行下列命令，先登记真实 `my-project`：

```bash
ergora skill import my-project \
  src/ergora/data/presets/workflows/ergora-refactoring-template/skills/ergora-codebase-quality
```

独立 `agent run --skill ergora-codebase-quality` 消费项目当前采用版本；这与模板内固定的 Skill 是两个明确选择。首次同名 import 成为初始 baseline，后续候选仍需[评价与采用](../../improvement/skills-and-evaluation.md#skill-candidates-evaluation-and-adoption)。项目 import 或编辑宿主 Skill 不会修改冻结模板；正式任务换资料须选择新版本与 manifest。
