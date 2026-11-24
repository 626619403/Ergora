# 修订、分享与恢复

简体中文 · [English](../../../definitions/workflows/revisions.md) · [文档目录](../../../README.zh-CN.md)

只修改工作流标准正文时，先用 `show` 取得精确原版本的 `digest` 和 `definition`，将 `definition` 单独保存为 `new-workflow.json`，调整版本、节点或依赖引用。将 `BASE_DIGEST` 替换为原包摘要：

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json
```

`--check` 不发布版本；省略时才沿原库发布。两者都会复制完整原包；没有资源参数时只用 UTF-8、排序键、两空格缩进和末尾换行重写 `workflow.json`，返回候选身份、固定 `base` 和 `published`。指令、上下文、完整 Skill 树、未声明文件及空目录保持。资源文件修改可使用下文的资源修订或 export/edit/check/import；此入口接受完整 JSON 正文，也可用 `--format yaml` 读取 YAML；页面操作见下文。

与单包 `composition check` 不同，`revise --check` 使用当前库解析完整递归依赖并检查后端/职能准入、继承、权限、资源、端口与预算；依赖必须已经发布且摘要精确匹配。它不使用项目 grant，也不代表运行批准；发布后用明确的 grant 预览整棵链。原摘要不符或当前准入失败会拒绝；同版本不同内容不能发布，原版本不变。检查不预留版本，发布可能因并发版本冲突失败；完全相同的发布可重试。

HTTP 的 `POST /api/workflow-definitions/{id}/{version}/revisions/check` 与 `/api/workflow-definitions/{id}/{version}/revisions` 分别检查、发布，JSON 为 `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`。CLI 与 HTTP 共用候选摘要及原有校验，均不启动模型、服务或任务。

资源操作沿[Agent资源修订](../resources.md#修订完整资源文件)的同一合同。准备 `resource-changes/changes.json`、`files/<包相对路径>` 和完整 `new-workflow.json`（新声明用合法占位摘要），先预览，审阅后保存响应中的建议正文到 `new-workflow.json`，再明确接受、检查、发布：

```bash
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --preview-resources > resource-preview.json
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora composition revise kernel-delivery 1.0.0 --base-digest BASE_DIGEST --document ./new-workflow.json --resources ./resource-changes --accept-candidate ./resource-preview.json
ergora composition file kernel-delivery 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

同一包内的二进制附件、完整Skill树、执行位及空目录按明确操作派生；未改内容保持。文件名取自原包 `show` 的 `files`，窗口以base64返回，须按 `next_offset` 读取并合并全部字节。HTTP 为 `POST /api/workflow-definitions/{id}/{version}/revisions/preview-resources` 和 `/files/read`；请求及最终 `resource_changes/accepted_candidate` 字段与Agent一致。预览、检查、发布都执行完整递归准入；历史文件读取不要求今天后端可用。完整候选接受绑定普通附件与全部目录，正文或操作改变须重新预览；预览不提升权限、不批准执行。页面可在“资源与附件编辑”中完整读取或上传文件、暂存操作并明确采用资源摘要；较大变更使用CLI或完整导出修改，步骤见[在页面修订工作流资源](#在页面修订工作流资源)。

父／子可同时计划提权或追加资源：先生成新的子定义版本，逐层更新父引用与权限，再发布新的根版本，最后用新的项目grant检查整棵链。只改子级会失败；根仍越项目上限也会失败。单定义导入通过原子完整对象及索引发布，完整根修订由其精确递归引用固定；这里没有跨定义事务或项目采用动作。旧根和旧版本保持原内容，不读取新的活动头替代。

联合修订不是跨库原子事务。中断或父级检查失败时，先前发布的独立子版本仍可见；旧根、已冻结 manifest、任务输入及审批保持原精确引用。修复后从尚未完成的父级继续，不以“最新版本”自动替换旧引用。

## 沿完整依赖链发布资源修订

以治理组合的结构审查者为例，依赖发布顺序为：Agent `ergora-structure-reviewer` → `ergora-structure-review` → `ergora-delivery-review` → 根 `ergora-governance-delivery`。大型修改使用相同内层定义并承接 `ergora-large-change-delivery`；训练提案的测量链为 Agent `ergora-measurement-reviewer` → `ergora-measurement-review` → `ergora-training-proposal`。版本和摘要均从自己的发布回执取得。

1. 从旧根先保存完整 manifest 和所需叶子输入，保留原版本作为对照。各层追加资料时保留原 `resources`；Skill 要包含入口、全部引用文件及所需空目录，普通未声明附件也可保留在包内。
2. 从 Agent 开始，为每个修改包提高版本，沿上面的资源预览、明确接受、检查、发布步骤操作。父级的 `nodes[].ref` 使用刚发布子级的完整 `kind/id/version/digest`，再发布父级，根最后发布。新依赖尚未发布或摘要不符时检查会拒绝；不要填预测摘要或改旧索引。
3. 每个包可以完整 `export`，在接收库先导入固定依赖、再导入其父包。只复制根包不能代替完整组合；需要一次分享时，用新根执行 `prepare-manifest`，分享整个目录。
4. 用明确 grant 预览新根，核对目标叶子的全部祖先来源、原资料及新增资料、权限链和预算，再从新 manifest 准备新输入。已冻结的旧输入仍指向旧材料；发布新根不会更新它。

资源修订没有自动项目采用、权限提升或执行动作。训练模板继续使用提案和材料审查入口；真实训练与采用须走各自的实验门禁。

## 联合修订父子权限

权限声明属于 Workflow 和其 Agent 节点。以治理组合的结构审查叶子为例，需要检查四层：`root` → `root/review` → `root/review/structure` → `root/review/structure/review`。大型修改使用同样的审查链，训练提案的测量链少一层。只提高最内层 Agent 节点请求时，其所属 Workflow 仍会拒绝；只发布新子工作流再替换父引用时，父工作流仍会拒绝越界的新子级。

|操作顺序|新修订要明确修改的内容|
|---|---|
|最内层 Workflow|提高所选 Agent 节点的请求和本 Workflow 的上限，检查后发布新版本。|
|每层父 Workflow|引用刚发布子级的精确版本/摘要，同时提高自己的上限；检查后发布，根最后。|
|新根的预览|给出覆盖新根的明确 grant；旧 grant 仍拒绝。核对未选分支、全部祖先材料、预算和端口。|
|实际调用|从新 manifest 准备输入，再用 `check-input` 核所选模式/后端；静态声明不会增加后端能力。|

例如，可以用保留域名 `https://joint-revision.example.invalid` 检查 `network` 集合的完整包含关系；这只验证声明，不应请求该域名。当前公开 `text-only` 和 `task-mcp` 调用均不支持工具网络请求，即使新根与 grant 静态校验通过，这两种模式的 `check-input` 和 `run-input` 仍在登记运行/调用模型前拒绝。需要其他执行能力时，应使用明确支持它的执行入口及项目授权。

## 重复实例、职责和后端选择

要重复使用同一个子模板，在父 `nodes` 中使用不同 `id` 引用相同完整 ref，并把所有需汇合的分支接入显式 `all`。例如 `structure` 和 `structure-extra` 可以引用同一个结构审查版本，叶子路径分别为 `root/review/structure/review` 和 `root/review/structure-extra/review`。冻结资产只保存一份相同定义；每次引用仍独立计算实例数、完整材料字节及作用域预算，来源保留各自结构路径。

同一精确子模板的两个实例具有相同的内部职责声明。若其中一个应为建议审查，应另发子模板新版本，修改其 Agent 节点的 `review_requirement` 为 `advisory`，再由父引用它；Workflow 引用节点没有职责覆盖字段。独立 Agent 定义及逐叶调用的后端覆盖各自负责后端选择，不能通过改职责字段更换模型。对每个叶子分别运行 `check-input --backend codex` 或 `--backend claude-code` 可检查当前配置/模式准入；结果不检查认证、实际推理或不同模型的错误独立性。

库保存在 State 的 `workflow-definitions/index.json` 与 `objects/<digest>/`，与Agent库分开，代码共用 `definition_bundles`。既有 `ERGORA_HOME`、`--home` 和平台默认目录继续适用；没有新DB表。`export` 只导出当前包，分享完整组合时还需按依赖顺序分享／导入其引用的每个包；不是单根自包含发行。

原[离线完整备份](../../install/upgrades.md#升级与持久数据)保存两个库。验证不仅核索引和对象，还递归核工作流引用、资源、图和静态合同；原平台、原State路径与停止写入者的恢复要求不变。库损坏不会自动覆盖成新证据。可使用显式v2任务定义[冻结完整审查组合](../../development/preparation.md#为正式任务冻结审查组合)，沿原六阶段启动只读reviewer或嵌套串并行审查，可分别声明必需/建议职责。旧v2/v3审查要求每叶沿结构祖先直接映射根task且没有前驱依赖；显式dag-v1的v4使用[具名端口](contracts.md#正式只读审查的数据端口)，增加work-units-v1的v5和work-units-v2的v6使用[专长执行者分配](contracts.md#专长执行者与原工作单元)。正式批准和候选证据保留原所有者。列表中的runtime_supported只表示静态形状支持，不证明后端或服务可用。

历史 `show/list/export` 与备份/恢复不要求引用的后端仍在当前catalog中；它们继续核完整静态结构及内容。新 `import`（包括相同内容的重复导入）与 `preview` 另外核每份Agent定义的当前角色/后端合同，不会因旧版本曾经导入就跳过准入。单包 `check` 只核本地图与资源，仍不访问依赖库。历史可读与当前可用的区别见[Agent手册](../agents.md#历史资产与当前准入)。

## 在页面修订工作流

新建模板时，在库中点击“新建模板”，选择精确的起点流程图。默认选中六阶段开发图，也可改选其他内置图或库中任一已保存图。填写目标 ID 和版本即可打开独立草稿。再次选择同一起点与目标可以继续其原草稿。保存手头已编辑的图可直接点击“设置另存目标”。检查候选并明确另存后才发布模板。打开精确版本即可预览图或保存完整 manifest。CLI 使用 `composition revise`，在草稿正文中填写目标 `id` 和 `version`，仍以原 ID、版本和摘要为基准。图结构由定义库保存，正式任务创建时单独校验运行路径。

在“Agent 与组合库”选择工作流精确版本。字段表单支持新版本、描述、根输入/输出、权限和预算；“编辑实例”可选择 Agent、子工作流或 all-join，调整精确引用、职能、审查职责、先行依赖、输入绑定与实例权限。Agent 的后端请求在其独立定义中修改，再将这里的引用更新为已发布的新版本和摘要。旧 v1 不会自动升级为 v2；复杂正文仍可用 JSON/YAML 明确编辑。

增加实例后选择它并补齐实际端口、依赖和权限。重命名会同步依赖与具名绑定；删除实例后须修正剩余端口引用。中间正文可以暂时不符合执行合同，原文入口继续可用于修复；完整图、祖先权限、资源冲突及预算由“检查定义候选”和发布时的原库检查决定。

按“应用字段文本”或应用 JSON/YAML → “检查定义候选” → “发布新定义版本”操作。三个编辑缓冲、原文同步确认、有限历史、恢复与下载规则与[Agent 编辑器](../agents.md#在页面编辑专长-agent)相同。页面不提供跨库事务：先发布 Agent/子工作流，再更新并发布父级，最后发布新根。失败的父级不会撤销已发布子版本，也不会修改旧根或在途任务。

库级页面不持有项目 grant；保存根权限不是批准。发布后仍须用明确 grant 预览和冻结任务。正式任务交接的实现范围见[工作流指南](../../../definitions/workflows/revisions.md#view-published-nested-relationships)。

按需要插入独立的精确子工作流。例如分析模板可以把 `ergora-development-inventory` 加在分析节点前，再沿用自己的分析和汇合。执行时会检查实际图；候选集成、可信验证和审批仍各自沿用正式执行契约。

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

对象的键顺序不会制造差异；数组保持原顺序，不把重新排列的权限/依赖声明推断为等价。比较按完整实例路径配对，同一精确Agent/工作流的重复实例各自保留；改名表现为旧路径删除、新路径新增，不猜测重命名。资源内容身份及顺序、资源来源与声明、装配提示身份分别展示：仅来源定义版本变化也可能改变提示摘要及字节用量，不能据此声称Skill正文变化。摘要只反映原preview包含的编译事实；Agent描述、专长等非preview字段须打开精确定义核对。正式执行交接见[任务页面选择](compose.md#在正式任务页面选择组合)；支持的交接合同见[工作流指南](../../../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)。

## 在页面修订工作流资源

在“Agent 与组合库”选择子工作流精确版本，使用“资源与附件编辑”。其完整读取/二进制上传、明确write/delete/mkdir、差异预览和摘要采用与[Agent资源步骤](../resources.md#在页面编辑资源与附件)共用同一会话合同。先应用提高版本及资源声明的正文，再暂存文件操作、预览并采用，最后检查和明确发布。后续追加从已采用的完整操作集合继续；原包与旧manifest不变。

正文、操作和接受身份共同撤销/重做，未应用草稿独立保留；有未应用内容或摘要接受过期时不能发布旧快照。刷新后重新检查，损坏/quota缓冲可下载完整工作字节，下载不含未编辑原包。HTTP含base64总上限4,000,000字节，较大变更沿CLI `composition revise --resources`；不会创建另一套服务器草稿或自动上传会话。当前页只修订所选定义，父子共同提权与新根引用仍需各自明确新版本；新增Skill/上下文不会扩大执行权限。
