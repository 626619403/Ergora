# 定义和数据流

简体中文 · [English](../../../definitions/workflows/contracts.md) · [文档目录](../../../README.zh-CN.md)

包入口是 `workflow.json`，格式见 [schema v1](../../../../src/ergora/data/schemas/workflow-definition-v1.json) 和 [schema v2](../../../../src/ergora/data/schemas/workflow-definition-v2.json)。只接受 JSON，UTF-8 可带 BOM；重复 JSON key 和未知字段拒绝。包树与资源遵循[Agent包](../resources.md#资源和存储边界)的摘要、路径、大小、目录限制及同平台恢复合同。

|字段|消费者与含义|
|---|---|
|`schema_version`、`id`、`version`、`description`|版本库与CLI展示；格式版本为严格整数1或2，小写 kebab ID、数字三段精确版本，无隐式 latest。|
|`resources`|有序本地 instructions/context/Skill；可以为空。复用 Agent 的资源格式和完整摘要检查。|
|`inputs`|输入端口名称数组；静态检查映射，正式`dag-v1`按冻结绑定投影根task或已完成前驱的具名输出。|
|`outputs`|输出端口→来源绑定，来源为自身输入或本图节点输出。|
|`nodes`|Agent引用、Workflow引用、all-join；决定结构实例和本地图。|
|`permissions`|本工作流的请求/子级上限；整条结构祖先链与项目grant检查。|
|`limits`|本子树的深度、实例、并发和完整静态材料上限；根与项目总限额覆盖全部子树。|

Agent／Workflow引用必须有 `kind`、`id`、`version`、`digest`。`digest` 是整个包树身份，可从 `check/import/show` 得到；不是 JSON 单文件的 SHA。每个节点有本图内唯一 `id`、显式 `depends_on`。Agent节点另有 `role`、`permissions` 和恰好一个 `task` 输入，其结果端口固定为 `result`；角色必须由目标Agent支持。Workflow节点的输入／输出由精确目标版本声明。

`{"input":"task"}` 传递一个工作流输入的完整值。`{"node":"implement","output":"result"}` 传递直接依赖节点的一个完整具名输出。引用本身不会添加依赖。静态检查在执行前解析引用，端口值在运行期间消费。

独立 Workflow v2 中，Agent 或子工作流的输入可用 `{"fields":{"request":{"input":"task"},"analysis":{"node":"analyze","output":"result"}}}` 组装一个对象。每个字段使用一个普通绑定，字段名遵循端口命名规则且不得重复，字段数为 1 至 32。所有引用的节点都须列入 `depends_on`。独立图从原输入和已完成输出组装对象，并在预留后继 Agent 前检查完整输入与提示词上限。显式单叶调用仍由调用者提供完整任务。

`{"id":"gather","join":"all","depends_on":["structure","correctness","test-value"]}` 声明汇合，输出 `result` 的目标语义为每个依赖分支的全部具名输出映射。汇合是等待所有列出分支的数据屏障。正式只读并行审查要求根输出指向覆盖全部叶子的显式all-join；原可信运行器核每个必需分支的候选、会话与收据后才生成聚合引用。静态all-join本身不是多数票或人工批准。

## 必需与建议审查的静态声明

WorkflowDefinition v2 在每个 `role: reviewer` 的 Agent 节点上要求显式 `review_requirement: required` 或 `advisory`。这是工作流实例的职责，同一专家可以在不同节点承担不同职责；AgentDefinition 仍使用 v1。其他角色、子工作流引用及 join 不接受该字段。要改变嵌套审查叶子的职责，保存新的子定义版本并沿父链更新精确引用。权限、Skill 与上下文继承规则保持。

例如 [review-requirements](../../../../examples/composition/review-requirements/workflow.json) 把结构审查设为必需、测试价值审查设为建议：

```bash
ergora composition check examples/composition/review-requirements
ergora composition import examples/composition/review-requirements
ergora composition preview review-requirements 1.0.0 --grant examples/composition/preview-grant.json
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
```

先导入本手册开头的结构审查者与测试价值审查者即可。预览在各叶子显示声明；只要递归引用中包含 v2 定义，`composition-preview.schema_version` 就为 2，完整包和备份保留原身份。全 v1 组合保持原预览版本及字节，历史成员不会被活动模板降级。

正式开发可使用此组合，配置方式见[冻结审查组合](../../development/preparation.md#为正式任务冻结审查组合)。组合至少包含一名必需审查者；所有必需和建议分支都必须完成。新职责图的选定输出必须指向覆盖全部成员的显式all-join，即使只有一个成员也相同；旧v1单叶图保持原运行合同。可信运行器核对同一候选、独立会话、完整产物和实际模型意见后，才允许建议 `request-changes` 随原 finding 一起进入汇合。其原回执保持 `FAILED`，汇合记录职责与意见；必需请求修改、运行失败、缺失、超时、合同破坏或未确认清理仍阻塞。单独 `run-input` 调用选定叶子，不聚合工作流或产生正式批准。

## 正式只读审查的数据端口

[serial-review](../../../../examples/composition/serial-review/workflow.json) 复用三份独立子模板：先完成结构审查，再并行运行正确性与测试价值审查，最后显式all-join。导入本手册开头的专家与三份子模板后：

```bash
ergora composition import examples/composition/serial-review
ergora composition prepare-manifest serial-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./serial-review-manifest
ergora composition verify-manifest ./serial-review-manifest
```

在用户任务定义v2的`composition`中显式设置`review_protocol: "dag-v1"`并填写这份manifest的路径和digest，再按[正式任务顺序](../../development/tasks.md#正式任务的操作顺序与恢复)预览、创建、启动和批准计划。保存的正式信封为v4，使用独立queue/request-root；没有该字段的任务保持原v2/v3合同，不自动升级。它仍是原六阶段中的review，不另外执行inventory、计划或verify。所有成员是只读reviewer，至少一名required；执行者分配暂不在此入口内。

结构parent决定祖先资源和权限，`depends_on`只决定先后，`inputs/outputs`决定具体数据来源。只有控制依赖的审查意见仍进入最终聚合，但不会自动成为下游的提示或Skill。嵌套Workflow必须等其全部节点完成才发布具名输出；它可以有多输出。选定review子树只有一个终结输出，投影链终点必须为显式all-join，完成依赖的传递覆盖须包含每名审查者（包括串行上游）。

每个输入用`bindings`映射到`task`或稳定的`实例路径#端口`；`values`表保存唯一值，join的值引用每个直接依赖的全部具名输出，重复模板实例保留各自路径。模型实际输入中的`review_inputs.results`为所有被绑定的审查来源提供原stage、回执与摘要、全部原产物正文；原request/context/receipt/claim、候选和实际读取SHA在调用前核验。建议request-changes可以流入下游，保留FAILED原件；运行失败不能提供合格端口值。

动态端口与前驱正文完整内联到实际prompt；task-mcp仍只开放本叶结构祖先及自身的固定资源，不自动开放兄弟或前驱的宿主文件。全部祖先材料与前驱原产物共同计入1,000,000字节完整输入限额。共享表避免相同join值递归展开，但不同审计产物内部的正文仍可能重复，因此长审计链可能提前超限；此时明确停止，不截断或省略材料。跨成员会话隔离、祖先并发限额、取消、未知对账与原history恢复沿原运行所有者处理。

## 专长执行者与原工作单元

[specialist-work](../../../../examples/composition/specialist-work/workflow.json) 把实现和验证交给两份独立专家定义，前者完成后把原产物交给后者；[specialist-delivery](../../../../examples/composition/specialist-delivery/workflow.json) 再将工作汇合接到三份并行审查。它们仍复用原六阶段：只运行一次inventory、plan与owner批准，执行原work units，再integrate、可信verify和review。

先按本手册开头导入三种审查专家及子模板，再导入实现专家与新组合：

```bash
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/validation-implementer
ergora composition import examples/composition/specialist-work
ergora composition import examples/composition/specialist-delivery
ergora composition prepare-manifest specialist-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./specialist-delivery-manifest
ergora composition verify-manifest ./specialist-delivery-manifest
```

使用 task-definition-v2，在原`composition`选项中加入：

```json
{
  "review_protocol": "dag-v1",
  "review_instance": "root/review",
  "mode": "task-mcp",
  "execution": {
    "protocol": "work-units-v2",
    "instance": "root/work",
    "assignments": {
      "implementation": "root/work/implementation",
      "validation": "root/work/validation"
    },
    "mode": "workspace-task-mcp"
  }
}
```

保留实际`manifest`路径及`manifest_digest`。`assignments`的键必须与原`input.work_units[].id`逐一对应；本例validation单元须依赖implementation。每份所选work叶子对应一个unit，相同专家可用不同实例路径复用；静态图与原units的传递先后关系必须相等。两子树互不交叠且覆盖图中全部Agent，work子树也须有覆盖全部叶子的显式非空all-join；遗漏成员或添加另一份运行顺序会拒绝。

`backend_overrides`可为所有实际writer和reviewer分别选择后端、模型及原因。首版workspace模式支持Linux/WSL2上的Codex，并要求为每个writer显式选择`{"tool":"codex","sandbox":"current-container"}`；外层项目还须按[可信执行配置](../../agents/formal-execution.md#可选的正式六阶段执行桥接)确认当前容器。示例Agent定义保留普通Codex绑定，未经这次明确选择不会自动降低隔离要求。新workspace模式不支持Claude/任意命令/mini-swe-agent，选用时会提前拒绝；它们既有模式不变。审查可选不同后端，`prefer-distinct`同后端时须填写明确回退原因；多样性比较全部实际writer，而非项目默认实现者。

work的权限链完整继承和收窄；每个原unit的所有路径必须完整落在其有效write范围（逻辑路径前缀`workspace/`）内。原独立checkout、依赖commit合并、路径gate、确定性检查、取消fence及可信commit继续由Executor拥有。Agent不能提交或移动HEAD；不合格结果不进入后继。所有writer同时服从原unit并发、执行器容量与整条结构祖先限额。

`work-units-v2`发布正式信封v6，使用独立的`composition-v6`队列和请求根；页面新建执行组合选择此协议。仍可在任务JSON中显式选择`work-units-v1`，发布原v5合同。已创建的任务保留其原版本，不因工具升级改写。`composition check-input/run-input`仍只读；准备一个输入包不能授权可写调用。workspace原生工具可操作当前用户的文件，权限路径由提示和最终Git gate约束，不提供过程中每一次文件访问或网络出口的强制隔离；固定任务MCP仍只提供本叶及祖先的声明资料。需要强隔离或外部MCP时请使用另有实际支持的执行环境，不能将此模式当作该能力。Windows既有安装、定义和兼容读取保持，新写路径用WSL2。

实际工作输入包含全部祖先指令、上下文、Skill正文/附件入口和批准计划。v6的`stage-artifacts-v1`传递全部声明阶段产物与可信检查/意见：profile的`artifacts_by_stage`，work的可信`test-results`、verify的可信`check-results`，receipt的所有checks引用，以及review的可信`composition-review-decision`。这些正文完整内联；模型summary不是此合同承诺的产物。日志、旧prompt、MCP审计等完整原件留在原receipt索引、`task evidence`和离线handoff中，不再次作为下游结果递归复制。保留索引不代表下游已读审计全文。

v6的`work_inputs.results`用实例路径保存端口来源和直接工作依赖的并集，`dependencies`给出unit ID→实例路径映射；同一来源只交付一次。没有绑定数据端口的控制依赖仍交付其声明产物/可信检查，祖先Skill不因控制边增加。review仍接收原plan/verification和绑定来源。v2–v5保留原全部产物内联合同，长审计链仍可能超预算；新任务应选v2协议，不修改旧任务来消除失败记录。

原request/context/admission、实际binding/session、claim、formal-call/invocation/selection、全部receipt产物字节及Git祖先关系仍核验；v6不内联的审计也不能被篡改。work端口不当作审查意见，review意见仍由可信读取器验证。进入review前仍强制integrate/verify、最终候选与原批准计划。v5/v6以摘要引用已完整保存的admission，原manifest和完整祖先资源保持。1,000,000字节完整输入上限不提高；声明产物或祖先材料真正超限仍在调用前拒绝，不截断。

原attempt/monitor/unknown与取消恢复规则保持。已完成原调用及提交后、回执发布前的恢复复用同一job/context与监控产物；HEAD已变化时，必须核对原Executor在首次HEAD门禁之后保存的完整调用证据，缺失或不符会拒绝并要求对账。无可靠外部结果时保持未知，不重新派发写Agent或换ID。运行后可用`agent runs`和正式`task evidence`查看原调用及产物，按原任务导出离线handoff。

## 盘点与规划的完整材料

当前使用 [task-definition schema8](../../../../src/ergora/data/schemas/task-definition-v8.json)，生成正式input12。inventory与plan各选择只读工作流子树及canonical coordinator；原六阶段owner按冻结祖先并发上限执行就绪专家，将完整原前驱交协调者，等待owner批准同一canonical plan，并保留可信检查、候选身份与清理合同。

先导入专长工作及并行审查依赖，再导入当前准备组和native父包：

```bash
ergora agent definition import examples/composition/agents/development-preparer
ergora composition import examples/composition/preparation-inventory
ergora composition import examples/composition/preparation-plan
ergora composition import examples/composition/preparation-guide
ergora composition import examples/composition/prepared-delivery
ergora composition import examples/composition/native-development
ergora composition prepare-manifest native-development 1.1.0 --grant examples/composition/preview-grant.json --directory ./native-development-manifest
```

完整schema8还包含budget、原work／review选择及单个native调用，准备部分为：

```json
{"native":{"protocol":"six-stage-v1","instance":"root/development"},
 "preparation":{"protocol":"preparation-dag-v1",
   "inventory":{"instance":"root/development/preparation/inventory","coordinator":"root/development/preparation/inventory/coordinator"},
   "plan":{"instance":"root/development/preparation/plan","coordinator":"root/development/preparation/plan/coordinator"},
   "mode":"task-mcp","repository_paths":["src"]}}
```

这只是`composition`内的字段。成员按inspector／planner角色运行；每位planner获得原canonical inventory，协调者汇合完整成果。选择、所需Skill读取、实际后端能力、原预算及正式调用身份继续由原owner验证；静态预览不证明实际执行。完整字段与当前示例见[同源材料指南](../../../definitions/workflows/contracts.md#complete-inventory-and-planning-materials)。
