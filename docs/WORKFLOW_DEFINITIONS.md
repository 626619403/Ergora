# 可组合工作流定义

工作流包把精确版本的专家或子工作流组合成有界 DAG。可以单独使用结构审查模板，也可以把结构、正确性、测试价值三个模板并行组合，再串接执行模板。结构父链决定继承；工作依赖只通过具名端口传递数据。

`composition` 提供静态检查、不可覆盖的版本库、完整预览、可携带的静态组合包与显式单叶调用。预览不调用模型；`run-input` 可将准备好的输入交给所选后端。正式开发按[六阶段流程](USAGE.md#正式任务的操作顺序与恢复)执行，审查阶段可运行嵌套的只读串并行分支并作显式all-join汇合，具体配置见[正式审查组合](USAGE.md#为正式任务冻结审查组合)。只读审查的数据端口见[正式DAG协议](#正式只读审查的数据端口)；专长执行者分配使用下文的[work-units-v2协议](#专长执行者与原工作单元)。

Web控制台的“Agent 与组合库”复用同一版本库、导入和preview用例，无需先注册项目。选择精确工作流版本，检查根声明初始化的静态上限后明确预览，即可查看每个实例的结构父链、先行依赖、具名端口、完整资源来源及装配提示；详见[页面操作](USAGE.md#在页面浏览与预览定义)。静态上限不构成项目授权，后端字段仅为请求。页面下载的定义JSON和预览JSON用于阅读与比较；分享完整资源和精确依赖应使用下文`export`、`prepare-manifest`或[固定当前预览](#固定当前预览到持久控制目录)。标准正文可在页面[明确修订](#在页面修订工作流)；嵌套画布与正式交接见[后续计划](plans/2026-11-09-composition-console.md)。

## 使用内置领域组合

仅安装wheel即可导入默认专家及其全部子工作流，不需要先下载仓库examples，也不调用模型或启动服务：

```bash
ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset large-change
ergora composition install-preset training-optimization
ergora composition show ergora-large-change-delivery 1.0.0 --material
ergora agent definition show ergora-server-implementer 1.0.0 --material
```

`presets`只读发行内容，不创建State。`install-preset`沿依赖顺序导入精确版本；重复执行保持同一身份，已有同ID/version的不同内容会拒绝。各定义分别原子发布，整套安装不是跨库事务；中断后可重试。安装不改变项目绑定或权限，不安装/认证Agent CLI，也不授予执行或批准权限。新默认库的权威资源在 [data/presets](../src/ergora/data/presets/presets.json)，可以沿原export/new-version/import流程替换专家及子模板；已有examples的身份保持。

|组合|根ID（当前版本1.0.0）|默认关系与使用范围|
|---|---|---|
|repository-governance|`ergora-governance-delivery`|知识地图、架构回归两个专家并行，再经可信integrate/verify接三审查；默认work-units-v2／正式v6|
|large-change|`ergora-large-change-delivery`|接口合同 → 服务端与客户端并行 → 集成/兼容验证 → 三审查；默认work-units-v2／正式v6|
|training-optimization|`ergora-training-proposal`|实验设计与性能分析 → kernel候选设计 → 测量复现审查；完整静态组合及可独立调用的只读提案叶|

开发组合共用 `ergora-delivery-review`，它引用结构、正确性、测试价值三份可单独使用的子模板。每份专家有独立初始指令、专长和Skill，沿自己的结构父链完整装载资料。开发writer默认Codex，reviewer默认Claude Code；支持的后端可以逐实例明确覆盖。实际可用性和认证仍由调用准入核验；同后端回退需遵守所选多样性政策并记录原因。

在明确的preview grant下，按[完整组合分享](#保存和分享完整组合)执行`prepare-manifest`，把上面的根ID/版本换入即可。开发正式选择沿[work-units-v2](#专长执行者与原工作单元)，使用`root/work`和`root/review`；unit ID直接映射同名叶子，例如`contract`→`root/work/contract`。原`templates copy`取得的领域input包含对应unit ID、路径和依赖；改变原units关系时，应同时修订对应工作子模板。workspace写调用仍要求每个writer显式选择可信current-container；导入组合不会自动选择此边界。

训练组合的`root/analysis/design`、`root/analysis/profile`、`root/kernel`和`root/measurement/review`可按[单叶调用](#调用一个准备好的叶子)使用；操作者需要在任务文件中提供完整workload、baseline和相应前驱输出。独立`run-input`不执行图前驱。生成的提案/代码文本及模型review不是实验结果或采用批准，真实CPU/GPU、Forge候选和测量仍按[训练手册](TRAINING.md)使用原可信runner/gate。目录中的`runtime`只描述本发行支持的使用范围，不表示后端、服务或硬件已经就绪。

## 运行示例

先按[使用手册](USAGE.md)安装基础 Ergora；这些命令不需要模型密钥、Web、工单或 Temporal 服务。示例文件在仓库 [examples/composition](../examples/composition/README.md)。在仓库根执行，导入依赖后再导入引用它的工作流：

```bash
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/architecture-reviewer
ergora agent definition import examples/composition/agents/correctness-reviewer
ergora agent definition import examples/composition/agents/test-value-reviewer
ergora composition check examples/composition/parallel-review --material
ergora composition import examples/composition/structure-review
ergora composition import examples/composition/correctness-review
ergora composition import examples/composition/test-value-review
ergora composition import examples/composition/parallel-review
ergora composition import examples/composition/kernel-delivery
ergora composition list
ergora composition show kernel-delivery 1.0.0 --material
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
ergora composition export kernel-delivery 1.0.0 ./shared-kernel-delivery
```

`check` 检查单包的 schema、资源、路径和本地图；不解析库中依赖，也不创建 State。`import` 还解析完整依赖树并检查端口、继承、权限与本定义预算；引用缺失或摘要漂移会失败。`preview` 额外使用明确提供的项目授权上限，读取库但不创建或迁移 State。`show` 展示本包材料；预览里的叶子 `resources` 和 `prompt` 才包含整条祖先链的完整静态材料。

示例展开成10个实例：一个根、一个执行 Agent、一个总审查工作流、三个审查子工作流、三个审查 Agent 和一个 all-join。`root/implement` 在 `root/review` 前完成；总审查内三支就绪分支可并行，`root/review/gather` 等待全部三支。相同子工作流可引用多次，每次产生不同路径实例。

示例 Agent 使用 Codex 与 Claude Code，预览只显示请求的后端，不检查安装或认证，不承诺模型效果或错误相互独立。持久改变后端需创建新Agent版本并更新沿途引用；单叶调用也支持明确记录的本次覆盖。项目角色调用另见[Agent入口](AGENT_BACKENDS.md)。

## 保存和分享完整组合

导入示例后，可以把根工作流及全部递归依赖一起保存：

```bash
ergora composition prepare-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest --material
```

分享整个输出目录，接收者安装基础Ergora后即可运行`verify-manifest`，无需先导入同一组定义、建立项目或启动服务。包内的`manifest.json`记录根精确版本、所供grant和完整图摘要；`composition.json`保存全部稳定实例、具名端口、依赖/汇合关系、祖先资源来源、完整静态提示、权限与预算；`assets/`带有全部精确引用的定义、Skill目录及上下文。重复引用只复制一份定义，实例状态仍按各自路径区分。

核验会从包内资源重建完整图并逐字核对身份，拒绝缺失、篡改、多余文件或未引用定义；它不依赖原始库位置或当前后端catalog。新准备仍检查当前定义准入，目录已存在时不覆盖。与单叶输入共用完整资产/容量检查和原子发布，超出10 MB或500文件的完整包明确拒绝。

需要使用其中的叶子时，准备UTF-8任务文件后直接从完整包生成输入：

```bash
ergora composition prepare-from-manifest ./kernel-delivery-manifest root/review/structure/review --task ./review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
```

这一步会重新检查当前定义准入及整图身份；旧包能核验不代表现在还能调用。生成的输入沿后文`check-input`/`run-input`使用，不执行图前驱或端口，也不会创建State或依赖接收者的原始定义库。

这是完整**静态**材料，`execution_authorized`为false；它没有操作者任务正文、未来父结果、候选批准或运行会话。正式任务仍须经过创建、原owner批准和运行准入，当前支持形状见[正式审查组合](USAGE.md#为正式任务冻结审查组合)。若希望State的完整备份同时保存该包，将输出目录放在自己的State数据目录下；否则单独保存/复制整个包，不能只留下`manifest.json`。`--material`会返回所有叶子的完整静态材料，省略该参数时只返回身份与清单。

### 固定当前预览到持久控制目录

在页面的“Agent 与组合库”中，先预览精确工作流及显式上限，再点击“保存当前预览为完整 manifest”。页面保存的是当前所选根，编辑缓冲和比较目标不包含在内。成功结果给出完整包绝对路径、`digest`及原`preview_sha256`；正式任务定义使用此`path`与`digest`。页面的“下载 composition-preview.json”仍只用于查看，不能代替完整目录。

CLI使用相同用例，必须明确提交已检查的预览摘要：

```bash
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
# 将上一步实际返回的 preview_sha256 填入，不使用示例占位符创建任务。
ergora composition freeze-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --preview-sha256 PREVIEW_SHA256
ergora composition show-manifest PREVIEW_SHA256 --material
```

完整包位于当前控制目录的`composition-manifests/PREVIEW_SHA256/`，沿原`--home`/`ERGORA_HOME`及平台默认持久目录；控制目录完整备份也会包含它。首次保存重新执行原准入并核预览摘要，上限或定义身份变化须重新审阅。相同摘要重试会核验原完整包，不覆盖已有目录；违反原完整核验的文件/定义/材料身份会明确拒绝。空目录正常复制保留，但沿原摘要合同不计入digest，稳定增删空目录不会改变身份。

保存回复丢失时，先保留原摘要并用“按当前摘要读取已保存包”或`show-manifest`查询；刷新后可重新预览同一精确版本及上限再读。读取不要求源库或当前后端可用，可独立执行`show-manifest`或`verify-manifest`，不能把历史可读等同当前可执行。HTTP对应`POST /api/composition/manifests`（原preview请求另加`preview_sha256`）、`GET /api/composition/manifests/PREVIEW_SHA256?material=true`；写入仍要求本地同源与原请求头。保存不创建项目、任务、批准或Agent调用。

## 在正式任务页面选择组合

先完成[项目登记](PROJECTS.md)，再打开“正式任务”→“预览与创建”。原“项目角色”入口保持使用项目绑定，不自动套用定义库中的组合。

1. 载入已登记开发模板或兼容草稿，填写任务ID、工单和完整输入。选择“本任务 Agent 来源”：仅组合审查，或组合执行与审查。训练优化仍使用独立入口。
2. 粘贴前文保存包返回的`manifest.preview_sha256`，点“读取完整 manifest”。此摘要不是manifest目录digest；页面从当前控制目录读取并核原完整包，再显示根身份和manifest digest。读取历史包不等于允许今天的正式调用。
3. 选择完整实例路径的审查子流程。执行与审查组合还要选执行子流程，点击“从当前输入载入工作单元”，逐个选择对应执行Agent。内置开发组合通常为`root/work`和`root/review`；单元ID对应同名work叶子。修改work子流程后重新载入分配；载入失败保留旧输入及分配，原任务预览会核全部unit和依赖。
4. 审查者可沿用精确定义的后端请求；覆盖时选择后端、配置模型等字段并写明理由。执行者须逐一显式覆盖；可写模式沿原后端合同要求可信Linux绑定，目前由Codex的“执行边界”选择“已信任的当前容器 / 用户”。页面不会从静态定义自动选择这一信任。认证仍由外部工具配置提供，不在此填写密钥。其他后端或不支持的模式会由服务端明确拒绝。
5. 默认优先不同执行/审查后端；同后端回退须填写策略说明。可明确要求不同后端或允许相同后端，仍沿原diversity合同。不同名称或不同模型选择本身不证明独立错误概率。
6. 点“预览冻结合同”，审阅服务端完整冻结文件与每成员binding/policy，再“确认创建冻结合同”。创建只发布合同，不启动、批准或执行。后续按[正式操作顺序](USAGE.md#正式任务的操作顺序与恢复)启动及批准原计划。

字段变化使旧任务预览失效，迟到manifest或预览回复不能恢复旧选择。读取/预览失败保留输入；创建发出后锁定原合同。创建回复丢失时按页面保留的原任务ID只读查询原创建记录，再决定是否恢复，不能换ID重发。组合、后端覆盖和理由只属于本次冻结任务，不修改模板或项目默认绑定；各祖先资料、权限和candidate/批准仍由原所有者核验。当前表单随对话框关闭而释放，关闭前另存任务输入；定义库中的完整manifest仍持久保存。

## 定义和数据流

包入口是 `workflow.json`，格式见 [schema v1](../src/ergora/data/schemas/workflow-definition-v1.json) 和 [schema v2](../src/ergora/data/schemas/workflow-definition-v2.json)。只接受 JSON，UTF-8 可带 BOM；重复 JSON key 和未知字段拒绝。包树与资源遵循[Agent包](AGENT_DEFINITIONS.md#资源和存储边界)的摘要、路径、大小、目录限制及同平台恢复合同。

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

绑定只能是 `{"input":"task"}` 或 `{"node":"implement","output":"result"}`。节点引用另一节点的结果时，必须将它列为直接依赖；不会由引用隐式添加依赖。没有 Python 表达式、任意脚本或循环。端口值是待执行阶段消费的不透明数据，静态检查不证明候选、审查 decision 或领域产物可信。

`{"id":"gather","join":"all","depends_on":["structure","correctness","test-value"]}` 声明汇合，输出 `result` 的目标语义为每个依赖分支的全部具名输出映射。汇合是等待所有列出分支的数据屏障。正式只读并行审查要求根输出指向覆盖全部叶子的显式all-join；原可信运行器核每个必需分支的候选、会话与收据后才生成聚合引用。静态all-join本身不是多数票或人工批准。

## 必需与建议审查的静态声明

WorkflowDefinition v2 在每个 `role: reviewer` 的 Agent 节点上要求显式 `review_requirement: required` 或 `advisory`。这是工作流实例的职责，同一专家可以在不同节点承担不同职责；AgentDefinition 仍使用 v1。其他角色、子工作流引用及 join 不接受该字段。要改变嵌套审查叶子的职责，保存新的子定义版本并沿父链更新精确引用。权限、Skill 与上下文继承规则保持。

例如 [review-requirements](../examples/composition/review-requirements/workflow.json) 把结构审查设为必需、测试价值审查设为建议：

```bash
ergora composition check examples/composition/review-requirements
ergora composition import examples/composition/review-requirements
ergora composition preview review-requirements 1.0.0 --grant examples/composition/preview-grant.json
ergora composition prepare-manifest review-requirements 1.0.0 --grant examples/composition/preview-grant.json --directory ./review-requirements-manifest
```

先导入本手册开头的结构审查者与测试价值审查者即可。预览在各叶子显示声明；只要递归引用中包含 v2 定义，`composition-preview.schema_version` 就为 2，完整包和备份保留原身份。全 v1 组合保持原预览版本及字节，历史成员不会被活动模板降级。

正式开发可使用此组合，配置方式见[冻结审查组合](USAGE.md#为正式任务冻结审查组合)。组合至少包含一名必需审查者；所有必需和建议分支都必须完成。新职责图的选定输出必须指向覆盖全部成员的显式all-join，即使只有一个成员也相同；旧v1单叶图保持原运行合同。可信运行器核对同一候选、独立会话、完整产物和实际模型意见后，才允许建议 `request-changes` 随原 finding 一起进入汇合。其原回执保持 `FAILED`，汇合记录职责与意见；必需请求修改、运行失败、缺失、超时、合同破坏或未确认清理仍阻塞。单独 `run-input` 调用选定叶子，不聚合工作流或产生正式批准。

## 正式只读审查的数据端口

[serial-review](../examples/composition/serial-review/workflow.json) 复用三份独立子模板：先完成结构审查，再并行运行正确性与测试价值审查，最后显式all-join。导入本手册开头的专家与三份子模板后：

```bash
ergora composition import examples/composition/serial-review
ergora composition prepare-manifest serial-review 1.0.0 --grant examples/composition/preview-grant.json --directory ./serial-review-manifest
ergora composition verify-manifest ./serial-review-manifest
```

在用户任务定义v2的`composition`中显式设置`review_protocol: "dag-v1"`并填写这份manifest的路径和digest，再按[正式任务顺序](USAGE.md#正式任务的操作顺序与恢复)预览、创建、启动和批准计划。保存的正式信封为v4，使用独立queue/request-root；没有该字段的任务保持原v2/v3合同，不自动升级。它仍是原六阶段中的review，不另外执行inventory、计划或verify。所有成员是只读reviewer，至少一名required；执行者分配暂不在此入口内。

结构parent决定祖先资源和权限，`depends_on`只决定先后，`inputs/outputs`决定具体数据来源。只有控制依赖的审查意见仍进入最终聚合，但不会自动成为下游的提示或Skill。嵌套Workflow必须等其全部节点完成才发布具名输出；它可以有多输出。选定review子树只有一个终结输出，投影链终点必须为显式all-join，完成依赖的传递覆盖须包含每名审查者（包括串行上游）。

每个输入用`bindings`映射到`task`或稳定的`实例路径#端口`；`values`表保存唯一值，join的值引用每个直接依赖的全部具名输出，重复模板实例保留各自路径。模型实际输入中的`review_inputs.results`为所有被绑定的审查来源提供原stage、回执与摘要、全部原产物正文；原request/context/receipt/claim、候选和实际读取SHA在调用前核验。建议request-changes可以流入下游，保留FAILED原件；运行失败不能提供合格端口值。

动态端口与前驱正文完整内联到实际prompt；task-mcp仍只开放本叶结构祖先及自身的固定资源，不自动开放兄弟或前驱的宿主文件。全部祖先材料与前驱原产物共同计入1,000,000字节完整输入限额。共享表避免相同join值递归展开，但不同审计产物内部的正文仍可能重复，因此长审计链可能提前超限；此时明确停止，不截断或省略材料。跨成员会话隔离、祖先并发限额、取消、未知对账与原history恢复沿原运行所有者处理。

## 专长执行者与原工作单元

[specialist-work](../examples/composition/specialist-work/workflow.json) 把实现和验证交给两份独立专家定义，前者完成后把原产物交给后者；[specialist-delivery](../examples/composition/specialist-delivery/workflow.json) 再将工作汇合接到三份并行审查。它们仍复用原六阶段：只运行一次inventory、plan与owner批准，执行原work units，再integrate、可信verify和review。

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

`backend_overrides`可为所有实际writer和reviewer分别选择后端、模型及原因。首版workspace模式支持Linux/WSL2上的Codex，并要求为每个writer显式选择`{"tool":"codex","sandbox":"current-container"}`；外层项目还须按[可信执行配置](AGENT_BACKENDS.md#可选的正式六阶段执行桥接)确认当前容器。示例Agent定义保留普通Codex绑定，未经这次明确选择不会自动降低隔离要求。新workspace模式不支持Claude/任意命令/mini-swe-agent，选用时会提前拒绝；它们既有模式不变。审查可选不同后端，`prefer-distinct`同后端时须填写明确回退原因；多样性比较全部实际writer，而非项目默认实现者。

work的权限链完整继承和收窄；每个原unit的所有路径必须完整落在其有效write范围（逻辑路径前缀`workspace/`）内。原独立checkout、依赖commit合并、路径gate、确定性检查、取消fence及可信commit继续由Executor拥有。Agent不能提交或移动HEAD；不合格结果不进入后继。所有writer同时服从原unit并发、执行器容量与整条结构祖先限额。

`work-units-v2`发布正式信封v6，使用独立的`composition-v6`队列和请求根；页面新建执行组合选择此协议。仍可在任务JSON中显式选择`work-units-v1`，发布原v5合同。已创建的任务保留其原版本，不因工具升级改写。`composition check-input/run-input`仍只读；准备一个输入包不能授权可写调用。workspace原生工具可操作当前用户的文件，权限路径由提示和最终Git gate约束，不提供过程中每一次文件访问或网络出口的强制隔离；固定任务MCP仍只提供本叶及祖先的声明资料。需要强隔离或外部MCP时请使用另有实际支持的执行环境，不能将此模式当作该能力。Windows既有安装、定义和兼容读取保持，新写路径用WSL2。

实际工作输入包含全部祖先指令、上下文、Skill正文/附件入口和批准计划。v6的`stage-artifacts-v1`传递全部声明阶段产物与可信检查/意见：profile的`artifacts_by_stage`，work的可信`test-results`、verify的可信`check-results`，receipt的所有checks引用，以及review的可信`composition-review-decision`。这些正文完整内联；模型summary不是此合同承诺的产物。日志、旧prompt、MCP审计等完整原件留在原receipt索引、`task evidence`和离线handoff中，不再次作为下游结果递归复制。保留索引不代表下游已读审计全文。

v6的`work_inputs.results`用实例路径保存端口来源和直接工作依赖的并集，`dependencies`给出unit ID→实例路径映射；同一来源只交付一次。没有绑定数据端口的控制依赖仍交付其声明产物/可信检查，祖先Skill不因控制边增加。review仍接收原plan/verification和绑定来源。v2–v5保留原全部产物内联合同，长审计链仍可能超预算；新任务应选v2协议，不修改旧任务来消除失败记录。

原request/context/admission、实际binding/session、claim、formal-call/invocation/selection、全部receipt产物字节及Git祖先关系仍核验；v6不内联的审计也不能被篡改。work端口不当作审查意见，review意见仍由可信读取器验证。进入review前仍强制integrate/verify、最终候选与原批准计划。v5/v6以摘要引用已完整保存的admission，原manifest和完整祖先资源保持。1,000,000字节完整输入上限不提高；声明产物或祖先材料真正超限仍在调用前拒绝，不截断。

原attempt/monitor/unknown与取消恢复规则保持。已完成原调用及提交后、回执发布前的恢复复用同一job/context与监控产物；HEAD已变化时，必须核对原Executor在首次HEAD门禁之后保存的完整调用证据，缺失或不符会拒绝并要求对账。无可靠外部结果时保持未知，不重新派发写Agent或换ID。运行后可用`agent runs`和正式`task evidence`查看原调用及产物，按原任务导出离线handoff。

## 盘点与规划的完整材料

要让前两阶段也使用精确的 Agent 定义与完整结构资料，选择 [task-definition v4](../src/ergora/data/schemas/task-definition-v4.json)。它生成正式输入 v8：`preparation-v1` 选择各一个 inspector／planner，后接既有 `work-units-v2` 与 `dag-v1`。原 Temporal 六阶段继续安排顺序、等待 owner 计划批准、运行可信检查和提交；这不是通用图运行或可执行的原生嵌套节点。

在完成上一节 specialist-delivery 的依赖导入后，导入准备专家及新的示例根：

```bash
ergora agent definition import examples/composition/agents/development-preparer
ergora composition import examples/composition/preparation-guide
ergora composition import examples/composition/prepared-delivery
ergora composition prepare-manifest prepared-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./prepared-delivery-manifest
ergora composition verify-manifest ./prepared-delivery-manifest
```

在上一节的完整任务定义中，把 `schema_version` 改为 `4`，将 `composition.manifest / manifest_digest` 换为此次实际结果，保留 `execution.protocol: "work-units-v2"`，并加入：

```json
{
  "preparation": {
    "protocol": "preparation-v1",
    "inventory": "root/preparation/inventory",
    "plan": "root/preparation/plan",
    "mode": "task-mcp",
    "repository_paths": ["src"]
  }
}
```

`preparation` 是 `composition` 内的字段，不是完整任务定义。两个实例可引用同一份多职能 Agent，也可使用不同精确定义；实际调用的角色分别为 inspector 和 planner。逐实例 `backend_overrides` 也覆盖它们，例如 `root/preparation/plan` 可单独选择支持受限调用的其他后端，记录 `binding` 与原因。执行／审查优先选择不同后端；不能用改变职责或覆盖后端绕过父权限。

`repository_paths` 是从原 starting commit 读取的相对路径前缀，必须覆盖原 work unit 路径。`["."]` 表示整个起始仓库；也可额外选择根配置和说明，例如 `["src", "pyproject.toml", "README.md"]`。可信读取器附上这些路径适用的祖先 `AGENTS.md`，每个实际文件仍须在该准备叶的 read 上限内。必要说明超出权限时，父子共同修订后再发布；文件为二进制、特殊 Git 类型或完整输入超限时整份拒绝，不静默排除。应按任务需要明确纳入构建／模型配置等其他资料。

两个准备叶只能直接映射结构根 task，叶及其祖先不能依赖尚未执行的外部节点。inventory→plan 的结果由原六阶段合同传递；示例 `preparation-guide` 的两个静态叶没有另建调度关系。准备、work 与 review 必须恰好覆盖全部 Agent 叶，不可遗漏、重复或把 inspector 假装成 implementer。其他阶段的兄弟结果不会成为继承权限。

inventory 和 plan 实际走只读叶调用、新空工作目录和原进程监控。完整 root→leaf 指令、上下文、SKILL.md、固定开发模板、原任务及精确 Git 文本进入完整 prompt。plan 另核原 inventory 请求、成功 receipt、session、后端及产物身份，取得全部声明产物与可信 baseline；超过旧 60k 截断位置的内容仍完整交付。模型不获得任意仓库读取或 shell 工具。原 writer 继续使用明确可信 current-container；read/write/egress 中标为 advisory 的能力没有变为 OS 隔离。

v8 中，只要选中结构链有未内联 Skill 附件，text-only 就在创建前拒绝；使用 task-mcp。模型必须完整读取必要附件，实际成功服务响应记录 URI、SHA、大小、offset 和返回字节数。原 Executor 在接受阶段结果前核连续覆盖，握手／list 成功或模型自称已读不能替代。完整正文已在 prompt 内，无须为了满足附件门禁再次读取同一正文。此证据证明字节交付，不证明模型理解。

继续使用原 `task preview/create/start`，原计划批准及候选证据入口不变。v4 也可加入与 v3 相同的可选 `source: {"snapshot_sha256": "实际快照摘要"}`，完整来源进入全部选中阶段，并保存在原 input／evidence／handoff。升级并重启 worker／executor 后才能接收 `.composition-v8` 队列；按冻结选择只检查实际依赖。图形任务向导仍生成 v6，v8 通过 CLI／共用 API 提交完整定义。

此v8合同保留原阶段时限。需要材料准备、队列、人工等待、执行和收尾共用总预算时，显式使用[task-definition v5／input9](USAGE.md#一次授权的预算准备)：先prepare、确认两个摘要创建，再沿原start／批准／取消／恢复入口运行。v9拥有独立队列及专用job owner，静态图本身不授予执行权。六阶段可引用原生实例与最终完整旅程仍按其后续合同验收。旧定义／input、已冻结manifest和history不自动迁移。

## 完整继承与冲突

每个叶子按 root→parent→自身的顺序拼装全部祖先 Skill 指令与上下文，以及各层初始指令。组合模板本身不额外调用模型。预览给出每份正文、内容身份、全部来源、完整拼装正文和 SHA；Skill 的必读正文是 `SKILL.md`，目录里的脚本和其他附件仍属于按需资源。

相同逻辑资源ID对应不同内容或种类会拒绝。同名Skill按实际frontmatter加载名称检查，不同树拒绝；同名同树可合并，但保留全部逻辑ID与来源，并检查每个来源都可读。不会用最后写入覆盖祖先。兄弟和前驱的Skill不会成为继承材料，前驱只有端口数据；重复引用不共享可变会话。

静态材料完整交付预览不证明模型理解、遵从或已实际读到。实际调用固定原实例和本次任务正文，再检查完整输入容量并保留装载证据；不足时拒绝，不静默截断。正式`dag-v1`按其封存版本加入明确绑定的前驱产物（v6为上述声明产物与可信检查/意见）；单独`run-input`仍只调用一个叶子。

## 权限路径和预算

预览grant文件使用 schema 中 `$defs/grant`：`schema_version: 1`，以及完整 `permissions` 和 `limits`。示例 [preview-grant.json](../examples/composition/preview-grant.json) 供演示，操作者应按自己的项目收窄；它目前只是显式静态输入，没有与项目配置或正式批准相连。

|权限字段|精确语义|
|---|---|
|`read`|可读逻辑子树数组，如 `workspace/src`、`definitions/agent/architecture-reviewer/1.0.0`；`definitions`代表整个定义资产库。|
|`write`|可写工作区子树数组，如 `workspace/src`；不能向定义库声明写权，写权不隐式授予读权。|
|`shell`|是否请求运行子进程；Skill脚本不凭其存在获得此权。|
|`network`|精确规范 HTTP(S) origin 数组，如 `https://api.example.com`；主机须为小写ASCII DNS名（国际域名使用punycode）或IP字面量，IPv6使用压缩形式，默认端口省略；不接受路径、凭据、查询、fragment、空白或通配符。|

路径使用 `/`，按大小写敏感的路径段包含判断，不能用 `workspace/src` 授予 `workspace/src-other`，也不接受 `..`、宿主机绝对路径或 glob。逻辑 `workspace` 预留给待执行的项目工作区；`definitions/{agent,workflow}/ID/VERSION/path` 表示精确包资源。它们不是当前操作系统挂载点，不会由预览自动创建或强制执行。

根请求必须在grant内；子工作流的请求不得越父级；Agent节点不得越所属工作流。每一层都检查，因此传递地满足全部祖先。每个必读资源的全部来源路径必须在当前实例的read内，Skill需要整个目录可读；收窄后读不到祖先材料会失败，不会丢弃材料或偷偷提权。预览中的 `backend_request.sandbox` 只是后端请求，不能覆盖此链，更不证明OS隔离。真实 `enforced/advisory/unsupported` 装载矩阵见[调用前能力检查](#调用前查看能力与权限)。

`limits` 四项都必填，拒绝布尔、浮点与超出支持范围的数值：

|字段|计数与支持上限|
|---|---|
|`depth`|根深度为1，每个结构节点再加1；每个子树重新从1计其局部深度，但所有祖先及项目深度仍同时检查。最大16。|
|`instances`|包括根、每次Workflow引用、每个Agent和all-join，重复引用逐次计数；每子树及全局共同约束。最大512。|
|`concurrency`|各结构作用域的共享并发配额，叶子预览列出全部作用域。正式并行审查同时遵守项目和全部祖先作用域上限，等待窄子树的分支不占用祖先配额。最大64；独立叶子调用不调度整图。|
|`material_bytes`|所有叶子完整静态prompt的UTF-8字节总量，包含来源标记，重复调用分别计算；每子树和全局共同约束。最大1,000,000。未含未来端口值。|

这些是有限静态格式的硬上限，不是性能、模型容量或任意并发可运行的承诺。使用更小的项目或子树限额可在编译时拒绝超限组合。

## 修订、分享与恢复

只修改工作流标准正文时，先用 `show` 取得精确原版本的 `digest` 和 `definition`，将 `definition` 单独保存为 `new-workflow.json`，调整版本、节点或依赖引用。将 `BASE_DIGEST` 替换为原包摘要：

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json
```

`--check` 不发布版本；省略时才沿原库发布。两者都会复制完整原包；没有资源参数时只用 UTF-8、排序键、两空格缩进和末尾换行重写 `workflow.json`，返回候选身份、固定 `base` 和 `published`。指令、上下文、完整 Skill 树、未声明文件及空目录保持。资源文件修改可使用下文的资源修订或 export/edit/check/import；此入口接受完整 JSON 正文，也可用 `--format yaml` 读取 YAML；页面操作见下文。

与单包 `composition check` 不同，`revise --check` 使用当前库解析完整递归依赖并检查后端/职能准入、继承、权限、资源、端口与预算；依赖必须已经发布且摘要精确匹配。它不使用项目 grant，也不代表运行批准；发布后用明确的 grant 预览整棵链。原摘要不符或当前准入失败会拒绝；同版本不同内容不能发布，原版本不变。检查不预留版本，发布可能因并发版本冲突失败；完全相同的发布可重试。

HTTP 的 `POST /api/workflow-definitions/{id}/{version}/revisions/check` 与 `/api/workflow-definitions/{id}/{version}/revisions` 分别检查、发布，JSON 为 `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`。CLI 与 HTTP 共用候选摘要及原有校验，均不启动模型、服务或任务。

资源操作沿[Agent资源修订](AGENT_DEFINITIONS.md#修订完整资源文件)的同一合同。准备 `resource-changes/changes.json`、`files/<包相对路径>` 和完整 `new-workflow.json`（新声明用合法占位摘要），先预览，审阅后保存响应中的建议正文到 `new-workflow.json`，再明确接受、检查、发布：

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --preview-resources > resource-preview.json
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json
ergora composition file kernel-delivery 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

同一包内的二进制附件、完整Skill树、执行位及空目录按明确操作派生；未改内容保持。文件名取自原包 `show` 的 `files`，窗口以base64返回，须按 `next_offset` 读取并合并全部字节。HTTP 为 `POST /api/workflow-definitions/{id}/{version}/revisions/preview-resources` 和 `/files/read`；请求及最终 `resource_changes/accepted_candidate` 字段与Agent一致。预览、检查、发布都执行完整递归准入；历史文件读取不要求今天后端可用。完整候选接受绑定普通附件与全部目录，正文或操作改变须重新预览；预览不提升权限、不批准执行。页面可在“资源与附件编辑”中完整读取或上传文件、暂存操作并明确采用资源摘要；较大变更使用CLI或完整导出修改，步骤见[在页面修订工作流资源](#在页面修订工作流资源)。

父／子可同时计划提权或追加资源：先生成新的子定义版本，逐层更新父引用与权限，再发布新的根版本，最后用新的项目grant检查整棵链。只改子级会失败；根仍越项目上限也会失败。单定义导入通过原子完整对象及索引发布，完整根修订由其精确递归引用固定；这里没有跨定义事务或项目采用动作。旧根和旧版本保持原内容，不读取新的活动头替代。

联合修订不是跨库原子事务。中断或父级检查失败时，先前发布的独立子版本仍可见；旧根、已冻结 manifest、任务输入及审批保持原精确引用。修复后从尚未完成的父级继续，不以“最新版本”自动替换旧引用。

### 沿完整依赖链发布资源修订

以治理组合的结构审查者为例，依赖发布顺序为：Agent `ergora-structure-reviewer` → `ergora-structure-review` → `ergora-delivery-review` → 根 `ergora-governance-delivery`。大型修改使用相同内层定义并承接 `ergora-large-change-delivery`；训练提案的测量链为 Agent `ergora-measurement-reviewer` → `ergora-measurement-review` → `ergora-training-proposal`。版本和摘要均从自己的发布回执取得。

1. 从旧根先保存完整 manifest 和所需叶子输入，保留原版本作为对照。各层追加资料时保留原 `resources`；Skill 要包含入口、全部引用文件及所需空目录，普通未声明附件也可保留在包内。
2. 从 Agent 开始，为每个修改包提高版本，沿上面的资源预览、明确接受、检查、发布步骤操作。父级的 `nodes[].ref` 使用刚发布子级的完整 `kind/id/version/digest`，再发布父级，根最后发布。新依赖尚未发布或摘要不符时检查会拒绝；不要填预测摘要或改旧索引。
3. 每个包可以完整 `export`，在接收库先导入固定依赖、再导入其父包。只复制根包不能代替完整组合；需要一次分享时，用新根执行 `prepare-manifest`，分享整个目录。
4. 用明确 grant 预览新根，核对目标叶子的全部祖先来源、原资料及新增资料、权限链和预算，再从新 manifest 准备新输入。已冻结的旧输入仍指向旧材料；发布新根不会更新它。

资源修订没有自动项目采用、权限提升或执行动作。训练模板继续使用提案和材料审查入口；真实训练与采用须走各自的实验门禁。

### 联合修订父子权限

权限声明属于 Workflow 和其 Agent 节点。以治理组合的结构审查叶子为例，需要检查四层：`root` → `root/review` → `root/review/structure` → `root/review/structure/review`。大型修改使用同样的审查链，训练提案的测量链少一层。只提高最内层 Agent 节点请求时，其所属 Workflow 仍会拒绝；只发布新子工作流再替换父引用时，父工作流仍会拒绝越界的新子级。

|操作顺序|新修订要明确修改的内容|
|---|---|
|最内层 Workflow|提高所选 Agent 节点的请求和本 Workflow 的上限，检查后发布新版本。|
|每层父 Workflow|引用刚发布子级的精确版本/摘要，同时提高自己的上限；检查后发布，根最后。|
|新根的预览|给出覆盖新根的明确 grant；旧 grant 仍拒绝。核对未选分支、全部祖先材料、预算和端口。|
|实际调用|从新 manifest 准备输入，再用 `check-input` 核所选模式/后端；静态声明不会增加后端能力。|

例如，可以用保留域名 `https://joint-revision.example.invalid` 检查 `network` 集合的完整包含关系；这只验证声明，不应请求该域名。当前公开 `text-only` 和 `task-mcp` 调用均不支持工具网络请求，即使新根与 grant 静态校验通过，这两种模式的 `check-input` 和 `run-input` 仍在登记运行/调用模型前拒绝。需要其他执行能力时，应使用明确支持它的执行入口及项目授权。

### 重复实例、职责和后端选择

要重复使用同一个子模板，在父 `nodes` 中使用不同 `id` 引用相同完整 ref，并把所有需汇合的分支接入显式 `all`。例如 `structure` 和 `structure-extra` 可以引用同一个结构审查版本，叶子路径分别为 `root/review/structure/review` 和 `root/review/structure-extra/review`。冻结资产只保存一份相同定义；每次引用仍独立计算实例数、完整材料字节及作用域预算，来源保留各自结构路径。

同一精确子模板的两个实例具有相同的内部职责声明。若其中一个应为建议审查，应另发子模板新版本，修改其 Agent 节点的 `review_requirement` 为 `advisory`，再由父引用它；Workflow 引用节点没有职责覆盖字段。独立 Agent 定义及逐叶调用的后端覆盖各自负责后端选择，不能通过改职责字段更换模型。对每个叶子分别运行 `check-input --backend codex` 或 `--backend claude-code` 可检查当前配置/模式准入；结果不检查认证、实际推理或不同模型的错误独立性。

库保存在 State 的 `workflow-definitions/index.json` 与 `objects/<digest>/`，与Agent库分开，代码共用 `definition_bundles`。既有 `ERGORA_HOME`、`--home` 和平台默认目录继续适用；没有新DB表。`export` 只导出当前包，分享完整组合时还需按依赖顺序分享／导入其引用的每个包；不是单根自包含发行。

原[离线完整备份](USAGE.md#升级与持久数据)保存两个库。验证不仅核索引和对象，还递归核工作流引用、资源、图和静态合同；原平台、原State路径与停止写入者的恢复要求不变。库损坏不会自动覆盖成新证据。可使用显式v2任务定义[冻结完整审查组合](USAGE.md#为正式任务冻结审查组合)，沿原六阶段启动只读reviewer或嵌套串并行审查，可分别声明必需/建议职责。旧v2/v3审查要求每叶沿结构祖先直接映射根task且没有前驱依赖；显式dag-v1的v4使用[具名端口](#正式只读审查的数据端口)，增加work-units-v1的v5和work-units-v2的v6使用[专长执行者分配](#专长执行者与原工作单元)。正式批准和候选证据保留原所有者。列表中的runtime_supported只表示静态形状支持，不证明后端或服务可用。

历史 `show/list/export` 与备份/恢复不要求引用的后端仍在当前catalog中；它们继续核完整静态结构及内容。新 `import`（包括相同内容的重复导入）与 `preview` 另外核每份Agent定义的当前角色/后端合同，不会因旧版本曾经导入就跳过准入。单包 `check` 只核本地图与资源，仍不访问依赖库。历史可读与当前可用的区别见[Agent手册](AGENT_DEFINITIONS.md#历史资产与当前准入)。

## 在页面修订工作流

在“Agent 与组合库”选择工作流精确版本。字段表单支持新版本、描述、根输入/输出、权限和预算；“编辑实例”可选择 Agent、子工作流或 all-join，调整精确引用、职能、审查职责、先行依赖、输入绑定与实例权限。Agent 的后端请求在其独立定义中修改，再将这里的引用更新为已发布的新版本和摘要。旧 v1 不会自动升级为 v2；复杂正文仍可用 JSON/YAML 明确编辑。

增加实例后选择它并补齐实际端口、依赖和权限。重命名会同步依赖与具名绑定；删除实例后须修正剩余端口引用。中间正文可以暂时不符合执行合同，原文入口继续可用于修复；完整图、祖先权限、资源冲突及预算由“检查定义候选”和发布时的原库检查决定。

按“应用字段文本”或应用 JSON/YAML → “检查定义候选” → “发布新定义版本”操作。三个编辑缓冲、原文同步确认、有限历史、恢复与下载规则与[Agent 编辑器](AGENT_DEFINITIONS.md#在页面编辑专长-agent)相同。页面不提供跨库事务：先发布 Agent/子工作流，再更新并发布父级，最后发布新根。失败的父级不会撤销已发布子版本，也不会修改旧根或在途任务。

库级页面不持有项目 grant；保存根权限不是批准。发布后仍须用明确 grant 预览和冻结任务。正式任务交接的实现范围见[计划](plans/2026-11-09-composition-console.md)。

### 查看已发布嵌套关系图

选择精确工作流版本，确认“静态预览上限 JSON”，点击“预览完整组合”。嵌套框表示结构父子关系，虚线箭头表示先行依赖，蓝色实线及具名入/出端口表示数据绑定。数据线不会传递Skill或授予权限，图也不表示Agent已经运行。同一子模板引用多次仍以不同完整实例路径展示。

点击图中实例，或用下方实例表中的按钮（支持键盘），查看其完整权限、预算/usage、端口、职责及后端请求。Agent详情包含所有祖先资源及完整提示正文；专长只取该精确Agent版本。点击“打开所选精确定义”修改其独立定义；实例权限、依赖及绑定在“打开结构父定义”中编辑，join也从父定义编辑。跳转会保留原编辑缓冲，不自动发布或采用较新版本。

图始终来自标出的**已发布版本和preview摘要**，不会反映尚未发布的正文或资源草稿。拖动、缩放、“定位所选实例”和“重排组合图”只调整显示；同一标签页按控制目录和精确根版本保留布局，刷新后重新排布。修改grant会清除旧图，须重新显式预览。图组件未加载时可用实例表和完整详情；“依赖与具名数据关系表”提供文本关系。完整数据可下载`composition-preview.json`。

在实例表点击“折叠 完整路径”，或选中子工作流后点击“折叠所选子工作流”。每个实例独立折叠，相同ref的其他实例不受影响；根保持展开。折叠/展开按原层级重排当前视图，组内节点与边在图中隐藏，完整实例/关系表仍保留。跨组连线标为“摘要”，原类型和具名绑定保持；点击连线或关系表的ID可查看原始完整端点。图中折叠框不代表新的执行或继承关系。“展开所有子工作流”清除当前折叠状态。

“查找实例（路径、职责、专长、后端）”按字面词项匹配，不区分大小写，多个词项需同时命中。例如输入`reviewer codex`可查使用Codex的审查实例。专长与声明职能只从完整id/版本/摘要匹配的Agent索引读取，缺少元数据时明确说明，不采用latest。查找只高亮，未匹配的结构与关系继续显示；折叠组内的匹配在外框标记。结果按钮“展开祖先并定位”、前后匹配按钮及“定位所选实例”会展开其结构祖先并定位原实例；选择实例表中的隐藏叶子则直接查看完整详情，保留折叠。查询、折叠、选择和布局只存本页会话，按控制目录/完整根ref隔离，刷新重置。

### 比较两个已发布组合

1. 从“子工作流精确版本”选择比较前的根版本。编辑中的草稿不会参加比较。
2. 在“预览整个嵌套组合”核对“静态预览上限 JSON”，然后选择“比较目标（已发布精确版本）”。目标可以是库中另一个工作流；列表明确显示ID、版本和摘要，不使用latest。
3. 点击“比较两个已发布版本”。两份精确版本分别通过原预览入口，并使用同一份显式grant。任一版本越权、引用缺失或不兼容时显示原拒绝，不扩大权限，不生成部分成功的差异。若需要提高权限，请自行核对并明确修改共同上限后重试。
4. 在“两个已发布组合的精确比较”查看新增、删除、变化、相同的实例数量和逐路径结果。点击完整路径可逐字段对照权限、职责、后端、预算、依赖、具名端口等事实，并展开两个版本的完整原实例，查看所有资源、来源和装配提示；键盘也可操作表格按钮。
5. 分别下载比较前/后preview JSON保存完整原件。比较不会发布定义、应用草稿或改变编辑基准；切换根版本或控制目录会清除当前比较。更换目标或修改grant后须重新显式比较，迟到回复不会恢复旧结果。

对象的键顺序不会制造差异；数组保持原顺序，不把重新排列的权限/依赖声明推断为等价。比较按完整实例路径配对，同一精确Agent/工作流的重复实例各自保留；改名表现为旧路径删除、新路径新增，不猜测重命名。资源内容身份及顺序、资源来源与声明、装配提示身份分别展示：仅来源定义版本变化也可能改变提示摘要及字节用量，不能据此声称Skill正文变化。摘要只反映原preview包含的编译事实；Agent描述、专长等非preview字段须打开精确定义核对。正式执行交接见[任务页面选择](#在正式任务页面选择组合)，验收进度见[C5计划](plans/2026-11-10-composition-handoff.md)。

## 准备完整的单叶输入

用精确实例路径准备一个可独立核验的输入包。先完成上面的定义导入；自行创建UTF-8任务文件 `review-task.txt`，再执行：

```bash
ergora composition prepare kernel-delivery 1.0.0 root/review/structure/review --grant examples/composition/preview-grant.json --task review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
ergora composition verify-input ./prepared-review
ergora composition verify-input ./prepared-review --material
```

准备操作仍检查当前Agent准入；它不调用模型、不执行前驱/端口，也不批准工作流。任务由操作者明确提供；例如把执行结果交给审查者时，操作者需要自行提供对应的任务材料，不能把此输入包当作已验证的自动数据流。

输入包含 `request.json`、完整 `composition.json`、原始 `task.txt`、完整 `prompt.txt` 和 `assets/` 中所有精确引用包。Skill目录的脚本和附件一并保存；资源正文仍按root→leaf完整装载。`verify-input --material`会重编译包内静态组合并核完整user prompt，源State删除后仍可使用，不依赖当前后端catalog。核验不会执行Skill或后端。

`max-prompt-bytes`必须为1–1,000,000，计完整user prompt的UTF-8字节，超过就拒绝，不截断。它不证明模型token容量或后端额外系统提示能容纳。整个输入包最多10MB/500文件、1000目录和48层，复制过程中也检查；失败不发布半包。只能保存到新目录，且不能写进不可变定义库。原子不覆盖发布支持Linux（需要renameat2）与Windows；不支持时明确失败。核验前后会检查整树一致，操作者应保持输入目录稳定；此检查不隔离同用户进程。输入包摘要包括任务、组合、提示和所有资产；它证明内容一致性，不认证作者或授予执行权限。跨平台执行位及同平台保持字节的限制与定义包相同。

输入元数据使用 [composition-input v1](../src/ergora/data/schemas/composition-input-v1.json)，包内保留所引用 Agent v1 及 Workflow v1/v2 的原格式。实际调用按下面的独立入口重新准入。

## 调用一个准备好的叶子

先[注册项目](PROJECTS.md)，并安装、认证所选的[Agent CLI](USAGE.md#安装与认证-agent-cli)。`prepared-review`沿用上面准备的完整输入包：

```bash
ergora composition run-input my-project ./prepared-review --timeout 300
ergora composition run-input my-project ./prepared-review --backend codex --backend-reason "Selected Codex for this call" --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --backend claude-code --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

默认采用叶子精确定义的后端；`--backend`和`--model`仅覆盖本次调用。跨后端时重新选择model，不沿用另一后端的model名。执行/审查应尽量选择不同后端；Claude不可用时可显式选Codex/ChatGPT，并用`--backend-reason`记录原因。不会在失败后暗中重试另一后端。超时为1–3600秒；成功返回0，模型失败/超时/启动配置或结构错误返回1，输入包或模式准入错误返回2。

也可在叶子精确定义中配置[DeepSeek Harness只读后端](AGENT_BACKENDS.md#deepseek-harness-只读叶后端)，保留完整解释器、模型、API服务与凭据变量引用；调用时不使用不完整的`--backend`覆盖。仅支持本节两种只读模式，原生workspace执行与会话恢复未准入。

默认模式为 `text-only`。完整祖先指令、上下文、Skill的`SKILL.md`和原任务进入模型；Skill附件仍保存在快照中，但本模式没有文件/命令/网页/MCP工具，不能按路径读取其他资料或编辑项目。提供审查任务时应把候选代码及必要证据放入任务正文。请求write、shell或工具network权限的叶子会在调用前拒绝；例如示例执行叶子不能通过本模式运行。原生结构化响应工具或交互工具可能保留。

运行使用新空cwd、原生CLI的规则/工具关闭选项和独立会话。它们约束模型可使用的工具，不提供OS/网络隔离；用户进程及模型服务本身的通信不受此模式隔离。后端不支持所需选项时明确失败。Codex可通过`--codex-config`显式提供推理配置：只消费model/provider/推理强度/service tier及provider的URL、凭据环境变量引用等字段；其中的工具、MCP、Skill、审批和sandbox设置不会覆盖此模式。使用Codex原生登录时可省略该文件；Claude使用原生认证或对应环境变量。不要把密钥写进定义或任务正文。

每次运行在State的`runs/`下保存经过完整核验的输入副本、新空工作目录、完整prompt、实际argv、stdout/stderr和结构化结果，复用原Agent运行列表/输出及完整备份。记录绑定输入摘要、项目修订、请求/实际binding和覆盖原因。运行列表只带资源身份及来源，完整正文可对返回的`input_path`使用`composition verify-input --material`按需核读。读取返回的`result`文件可查看`summary`、`artifacts.response`；审查者另有`approve/request-changes`。进程成功和审查approve分别判断。

单叶调用的任务由操作者提供，图前驱和端口没有执行；原输入仍为`execution_authorized: false`，本次调用也不创建正式候选/批准。正式串行/并行调度及候选、批准使用上文的[正式审查](#正式只读审查的数据端口)和[工作单元](#专长执行者与原工作单元)入口。


## 在页面修订工作流资源

在“Agent 与组合库”选择子工作流精确版本，使用“资源与附件编辑”。其完整读取/二进制上传、明确write/delete/mkdir、差异预览和摘要采用与[Agent资源步骤](AGENT_DEFINITIONS.md#在页面编辑资源与附件)共用同一会话合同。先应用提高版本及资源声明的正文，再暂存文件操作、预览并采用，最后检查和明确发布。后续追加从已采用的完整操作集合继续；原包与旧manifest不变。

正文、操作和接受身份共同撤销/重做，未应用草稿独立保留；有未应用内容或摘要接受过期时不能发布旧快照。刷新后重新检查，损坏/quota缓冲可下载完整工作字节，下载不含未编辑原包。HTTP含base64总上限4,000,000字节，较大变更沿CLI `composition revise --resources`；不会创建另一套服务器草稿或自动上传会话。当前页只修订所选定义，父子共同提权与新根引用仍需各自明确新版本；新增Skill/上下文不会扩大执行权限。

## 调用前查看能力与权限

在实际调用前，可以先检查同一输入、后端及模式：

```bash
ergora composition check-input my-project ./prepared-review
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend claude-code --backend-reason "Independent review backend"
```

该命令和`run-input`共用当前准入。结果的`policy.permission_ceilings`按所供grant、root到leaf列出整条结构权限链，`requested_permissions`是叶子请求，`context.resources`保留全部祖先/自身资源来源。read路径是许可上限；列出workspace不会自动提供项目文件工具。完整内联材料和固定附件的支持分别展示，text-only不会声称附件可读。

`policy.capabilities`把支持范围分为`enforced`（可信CLI/任务URI服务实现的机制）、`advisory`（请求/提示，未提供强制保证）及`unsupported`（没有对应能力）。Codex实际传read-only请求，但不因此宣称宿主隔离；Claude关闭native工具，没有额外请求OS sandbox。任务MCP只提供固定声明资料的list/read；实时workspace、写、shell、工具network origin及外部MCP继续不支持。基础设施推理HTTP、stdio进程、日志/状态写入仍存在。

这是实现合同和本次准入报告，不启动server/模型、不创建运行，也不检查CLI版本或认证。使用Codex的`--codex-config`时，检查和运行共用推理字段解析；文件不可读、无效TOML、不合法provider表或不能编码的字段在建立运行前拒绝。它不验证提供商是否接受配置、模型是否可用或容量是否足够；Claude忽略该Codex专用选项。task-mcp只检查Linux及SDK顶层存在，真正SDK兼容/连接在运行时预检。检查成功不等于正式批准，`formal_execution_authorized`仍为false。实际运行重新执行准入并保存同结构`policy`，不会把先前检查结果当成授权票据。

## 通过任务 MCP 读取固定附件

在Linux/WSL2中，用运行Ergora的同一个Python环境安装可选依赖。仓库根下执行：

```bash
python -m pip install '.[task-mcp]'
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend claude-code --timeout 300
```

此模式保持完整祖先指令、上下文和Skill说明的内联交付，另向模型提供`ergora_task`服务的`list`、`read`工具。先`list`查看虚拟URI，再`read`读取本叶子全部结构祖先及自身声明的资料和Skill附件。普通正文仅开放声明的文件；Skill开放其固定完整目录。它不开放兄弟模板、未声明的同目录文件、整个输入资产库或项目实时文件。资料不作为可执行程序运行；写、shell及工具network请求继续在调用前拒绝。

每次调用生成独立的[task-mcp-scope v1](../src/ergora/data/schemas/task-mcp-scope-v1.json)，保存原始字节、摘要及来源，最多10MB/500文件，完整序列化scope最多16MB；超限拒绝。服务核验scope后只查询内存，不把模型提供的URI当作宿主路径。Linux的固定资源读取逐级使用不跟随链接的文件描述符，拒绝symlink/hardlink/特殊文件；当前Windows新模式会给出Linux/WSL2指引，既有Windows功能继续可用。

`list(path="",offset=0,max_entries=100)`按授权URI分页，每页条目元数据最多约64KiB；`read(path,offset=0,max_bytes=65536)`按字节分页。返回文件大小、SHA256和`next_offset`；可解码块为UTF-8，二进制或跨编码边界为明确base64。继续请求`next_offset`可取得完整内容，不以一次工具响应代表整个目录或文件。

### 核验完整附件读取

若任务要求完整检查每层资料，在任务文件中明确要求：分页列出全部 URI，再逐个从 offset 0 读到 `next_offset:null`，包括所有祖先 instructions/context、每个 Skill 的 `SKILL.md` 和全部引用附件。UTF-8 文本若因窗口切开多字节字符而返回 base64，可在同一 offset 缩小 `max_bytes` 后重读，再按成功文本页推进；真正的二进制附件按完整 base64 字节处理，不运行。空目录保存在完整包中，不会成为可读文件；普通未声明附件也不会自动进入任务 scope。

运行成功及最终 `approve` 都不证明附件读全。核验时比对冻结输入、`task_mcp.scope` 的 URI/大小/SHA/来源，以及本次原生事件里的实际 list/read 回复；各文件的成功页应连续覆盖原字节，保留失败或重复窗口。scope 保存的是可用材料，原生读取记录才说明本次模型实际请求过哪些字节。准备好的输入可在源库移走后使用；应先核验并保留源库及完整输入，避免误删唯一副本。

MCP配置只在本次调用生成。Codex只选择该server的两工具，native MCP资源发现/响应或交互入口可能保留；服务不注册额外resources/templates/prompts。Claude使用`--bare --restricted`、空native工具及strict显式MCP；bare模式只使用其支持的API环境认证，不读取常规OAuth/keychain。需要OAuth登录的用户可继续使用text-only，或为该模式设置后端支持的API环境变量；无需把密钥放入定义、scope或聊天。不同后端不会自动共享模型名或认证。

运行记录的`task_mcp`包含固定scope身份、预检结果和本次native连接回执。预检与native回执分开；后者必须是该scope的实际SDK成功`tools/list`且工具恰为list/read。旧握手及新版无握手请求分别记录实际协议和`handshake_observed`；没有真实服务回执时，即使最终模型JSON成功也登记失败。scope与回执跟随State完整备份，运行列表继续只显示摘要；这不提供OS隔离，也不扩张模板或项目授权。

运行还检查本次原生后端已经报告的任务MCP传输错误：即使模型随后重连并返回合格结果，该次运行仍记为failed，保留原始stdout。未知资源或非法URI等服务端领域拒绝允许模型纠正后继续；它们不等于连接失效。Claude在此模式保存stream-json原始事件并提取最终结构结果，普通native/text-only输出处理保持。此检查不提供持续heartbeat，不能检测没有后续调用且无原生错误事件的静默失联。
