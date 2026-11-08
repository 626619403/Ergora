# 可组合工作流定义

工作流包把精确版本的专家或子工作流组合成有界 DAG。可以单独使用结构审查模板，也可以把结构、正确性、测试价值三个模板并行组合，再串接执行模板。结构父链决定继承；工作依赖只通过具名端口传递数据。

当前 `composition` 命令交付静态检查、不可覆盖的版本库和完整预览。预览不调用模型、不启动调度器、不修改项目配置，也不授予执行权限。正式开发仍按[六阶段流程](USAGE.md#正式任务的操作顺序与恢复)执行。实际资源装载、批准链和 Temporal 嵌套执行沿[AC计划](plans/2026-11-08-agent-composition.md)继续接入。

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

示例 Agent 使用 Codex 与 Claude Code，预览只显示请求的后端，不检查安装或认证，不承诺模型效果或错误相互独立。改变后端应创建新的 Agent 版本、更新引用摘要并沿引用链发布新版本；实际调用仍使用现有[Agent入口](AGENT_BACKENDS.md)。

## 定义和数据流

包入口是 `workflow.json`，格式见[schema v1](../src/ergora/data/schemas/workflow-definition-v1.json)。只接受 JSON，UTF-8 可带 BOM；重复 JSON key 和未知字段拒绝。包树与资源遵循[Agent包](AGENT_DEFINITIONS.md#资源和存储边界)的摘要、路径、大小、目录限制及同平台恢复合同。

|字段|消费者与含义|
|---|---|
|`schema_version`、`id`、`version`、`description`|版本库与CLI展示；严格整数1、小写 kebab ID、数字三段精确版本，无隐式 latest。|
|`resources`|有序本地 instructions/context/Skill；可以为空。复用 Agent 的资源格式和完整摘要检查。|
|`inputs`|输入端口名称数组，值在实际调用时提供；当前只检查映射，没有生成的运行态正文。|
|`outputs`|输出端口→来源绑定，来源为自身输入或本图节点输出。|
|`nodes`|Agent引用、Workflow引用、all-join；决定结构实例和本地图。|
|`permissions`|本工作流的请求/子级上限；整条结构祖先链与项目grant检查。|
|`limits`|本子树的深度、实例、并发和完整静态材料上限；根与项目总限额覆盖全部子树。|

Agent／Workflow引用必须有 `kind`、`id`、`version`、`digest`。`digest` 是整个包树身份，可从 `check/import/show` 得到；不是 JSON 单文件的 SHA。每个节点有本图内唯一 `id`、显式 `depends_on`。Agent节点另有 `role`、`permissions` 和恰好一个 `task` 输入，其结果端口固定为 `result`；角色必须由目标Agent支持。Workflow节点的输入／输出由精确目标版本声明。

绑定只能是 `{"input":"task"}` 或 `{"node":"implement","output":"result"}`。节点引用另一节点的结果时，必须将它列为直接依赖；不会由引用隐式添加依赖。没有 Python 表达式、任意脚本或循环。端口值是待执行阶段消费的不透明数据，静态检查不证明候选、审查 decision 或领域产物可信。

`{"id":"gather","join":"all","depends_on":["structure","correctness","test-value"]}` 声明汇合，输出 `result` 的目标语义为每个依赖分支的全部具名输出映射。汇合是等待所有列出分支的数据屏障；必需审查的可信批准／失败聚合由后续运行合同负责，不能将 all-join 当作多数票或自动批准。

## 完整继承与冲突

每个叶子按 root→parent→自身的顺序拼装全部祖先 Skill 指令与上下文，以及各层初始指令。组合模板本身不额外调用模型。预览给出每份正文、内容身份、全部来源、完整拼装正文和 SHA；Skill 的必读正文是 `SKILL.md`，目录里的脚本和其他附件仍属于按需资源。

相同逻辑资源ID对应不同内容或种类会拒绝。同名Skill按实际frontmatter加载名称检查，不同树拒绝；同名同树可合并，但保留全部逻辑ID与来源，并检查每个来源都可读。不会用最后写入覆盖祖先。兄弟和前驱的Skill不会成为继承材料，前驱只有端口数据；重复引用不共享可变会话。

静态材料完整交付预览不证明模型理解、遵从或已实际读到。未来实际调用还须固定原实例的端口值，再检查完整输入容量并证明实际装载；不足时拒绝，不静默截断。

## 权限路径和预算

预览grant文件使用 schema 中 `$defs/grant`：`schema_version: 1`，以及完整 `permissions` 和 `limits`。示例 [preview-grant.json](../examples/composition/preview-grant.json) 供演示，操作者应按自己的项目收窄；它目前只是显式静态输入，没有与项目配置或正式批准相连。

|权限字段|精确语义|
|---|---|
|`read`|可读逻辑子树数组，如 `workspace/src`、`definitions/agent/architecture-reviewer/1.0.0`；`definitions`代表整个定义资产库。|
|`write`|可写工作区子树数组，如 `workspace/src`；不能向定义库声明写权，写权不隐式授予读权。|
|`shell`|是否请求运行子进程；Skill脚本不凭其存在获得此权。|
|`network`|精确规范 HTTP(S) origin 数组，如 `https://api.example.com`；主机须为小写ASCII DNS名（国际域名使用punycode）或IP字面量，IPv6使用压缩形式，默认端口省略；不接受路径、凭据、查询、fragment、空白或通配符。|

路径使用 `/`，按大小写敏感的路径段包含判断，不能用 `workspace/src` 授予 `workspace/src-other`，也不接受 `..`、宿主机绝对路径或 glob。逻辑 `workspace` 预留给待执行的项目工作区；`definitions/{agent,workflow}/ID/VERSION/path` 表示精确包资源。它们不是当前操作系统挂载点，不会由预览自动创建或强制执行。

根请求必须在grant内；子工作流的请求不得越父级；Agent节点不得越所属工作流。每一层都检查，因此传递地满足全部祖先。每个必读资源的全部来源路径必须在当前实例的read内，Skill需要整个目录可读；收窄后读不到祖先材料会失败，不会丢弃材料或偷偷提权。预览中的 `backend_request.sandbox` 只是后端请求，不能覆盖此链，更不证明OS隔离。真实 `enforced/advisory/unsupported` 装载矩阵留给后续准入。

`limits` 四项都必填，拒绝布尔、浮点与超出支持范围的数值：

|字段|计数与支持上限|
|---|---|
|`depth`|根深度为1，每个结构节点再加1；每个子树重新从1计其局部深度，但所有祖先及项目深度仍同时检查。最大16。|
|`instances`|包括根、每次Workflow引用、每个Agent和all-join，重复引用逐次计数；每子树及全局共同约束。最大512。|
|`concurrency`|各结构作用域的共享并发配额，叶子预览列出全部作用域；未来调度不能把子级配额相乘突破根上限。最大64。当前不调度任务。|
|`material_bytes`|所有叶子完整静态prompt的UTF-8字节总量，包含来源标记，重复调用分别计算；每子树和全局共同约束。最大1,000,000。未含未来端口值。|

这些是有限静态格式的硬上限，不是性能、模型容量或任意并发可运行的承诺。使用更小的项目或子树限额可在编译时拒绝超限组合。

## 修订、分享与恢复

父／子可同时计划提权或追加资源：先生成新的子定义版本，逐层更新父引用与权限，再发布新的根版本，最后用新的项目grant检查整棵链。只改子级会失败；根仍越项目上限也会失败。单定义导入通过原子完整对象及索引发布，完整根修订由其精确递归引用固定；这里没有跨定义事务或项目采用动作。旧根和旧版本保持原内容，不读取新的活动头替代。

库保存在 State 的 `workflow-definitions/index.json` 与 `objects/<digest>/`，与Agent库分开，代码共用 `definition_bundles`。既有 `ERGORA_HOME`、`--home` 和平台默认目录继续适用；没有新DB表。`export` 只导出当前包，分享完整组合时还需按依赖顺序分享／导入其引用的每个包；不是单根自包含发行。

原[离线完整备份](USAGE.md#升级与持久数据)保存两个库。验证不仅核索引和对象，还递归核工作流引用、资源、图和静态合同；原平台、原State路径与停止写入者的恢复要求不变。库损坏不会自动覆盖成新证据。正式运行manifest的冻结／批准、取消／恢复和独立审查身份沿后续AC3c/4接入，不由静态预览替代。

历史 `show/list/export` 与备份/恢复不要求引用的后端仍在当前catalog中；它们继续核完整静态结构及内容。新 `import`（包括相同内容的重复导入）与 `preview` 另外核每份Agent定义的当前角色/后端合同，不会因旧版本曾经导入就跳过准入。单包 `check` 只核本地图与资源，仍不访问依赖库。历史可读与当前可用的区别见[Agent手册](AGENT_DEFINITIONS.md#历史资产与当前准入)。

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

当前格式为[composition-input v1](../src/ergora/data/schemas/composition-input-v1.json)，不改变原Agent/Workflow格式。实际后端装载、任务MCP及调用准入在后续AC3b.2b/3/4完成后接入；新运行仍须按当时规则重新准入。
