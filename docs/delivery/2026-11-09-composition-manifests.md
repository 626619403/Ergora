# AC3c：组合清单与正式任务身份

日期：2026-11-09。状态：AC3c.1完整完成：539163e精确候选、最终发行/新独立复审/真实自身再审、双OS CI42526062730及独立远端终结均通过；后续正式身份切片各自验收。本片依赖AC3b.4；不把静态组合或独立单叶调用登记为正式批准。

## 原始要求与已有事实

用户要求可复用嵌套模板、完整祖先Skill/上下文继承、逐级权限上限、不同职能/专长/后端及可恢复的串并行工作流。创建/批准必须冻结实际定义和授权，修改活动库不得改变已批准任务。沿[ADR0004](../architecture/decisions/0004-agent-composition.md)和[ADR0005](../architecture/decisions/0005-composable-workflows.md)实施，保留既有六阶段和可信检查。

现有`workflow_definitions`已拥有有界展开、完整材料、精确引用、原子完整输入发布及历史完整性核验；`agent_runs`提供独立调用的当前准入与后端能力合同。正式任务当前只接受task-definition-v1，`tasks._definition`冻结四角色binding；`reference_task_creation._Creation`发布七份原生文件，其意图/回执被提交和批准链共同核对。Temporal原输入及`DevelopmentWorkflow.context`仍只有冻结legacy spec；不能向旧spec偷加字段。

`_Submission.expected`已经绑定creation摘要，远端memo绑定submission摘要；`_Approval`又绑定原submission/run及原计划回执。这个链可复用，但不能仅把一个新JSON放进任务目录就声称运行已固定组合。执行端还必须核对同一个清单，任务原始输入/作业上下文/实际调用均需带相应身份。

## 下一批可验收切片

- **AC3c.1：完整静态组合包。** 在既有工作流所有者扩展可独立核验的manifest包：根引用、递归精确版本、全图/稳定实例路径、全部祖先资源及内容身份、grant/逐级权限、预算和运行态端口装配规则。完整资产只复制一次；复用原资产树、定义库和不覆盖原子发布。CLI是实际消费者，后续正式创建/执行消费同一格式。新格式明确静态材料，不凭空冻结未来父结果，不表示已经获得执行批准。历史读取不依赖当前后端catalog，新准入另验。验收包括原资产库改变/移除后独立重验、完整备份恢复、未引用资产/缺文件/摘要/权限/容量拒绝及中断不发布残包。避免复制一套输入包核验器。
- **AC3c.2：正式创建与版本化admission envelope。** 新task-definition版本显式选择组合包及本次后端/策略，旧v1逐字保持。创建预览/持久意图固定清单和静态资源摘要，保留原revision和恢复协议。制定明确的新运行信封：legacy spec为原六阶段投影，manifest摘要/内容身份为额外执行合同；提交历史、memo和查询对账必须核该信封。原生创建过程当前使用`-S`隔离子进程，不得隐式引入依赖站点包；语义准入放在已有应用所有者、子进程仍核原始摘要和完整发布身份。没有对应运行支持前，提交须明确拒绝新能力，不能让新任务静默走旧单binding执行。
- **AC3c.3：批准、派发与调用前身份核验。** 复用原Temporal持久调度和六阶段。通过版本化workflow入口/执行桥在原始输入、作业上下文、原计划回执及实际Agent请求间传递同一manifest身份；原v1工作流按原ID读取/恢复。新worker需显式注册新入口，旧worker不可冒称支持。动态父材料按原实例/产物及摘要装配为新调用快照，继承全文进入实际prompt，超容量拒绝；真实schema与实际CLI能力均重新准入。执行者可用的写入仍按原可信阶段/单写所有者核定，不能从当前只读task-mcp推导任意写能力。
- **AC3c.4：发行与恢复出口。** 新旧两种任务经过非editable包及备份恢复；真实候选/计划批准、篡改拒绝、相同任务并发/中断、原run对账均留证据。每片用新的独立审查上下文，大项再用Ergora自身模板真实审查。普通精确推送并核必要双OS CI，未测平台/模式分列。AC4再接多成员、同候选全必需审查聚合和有界子工作流；不在本片并行发明第二调度器。

## 所有权与兼容约束

静态图/完整包继续归`workflow_definitions`，定义/资源和完整树使用`definition_bundles`/`asset_trees`；当前后端合同归`agent_backends`，独立调用准入归`agent_runs`。正式创建/提交/批准各沿已有用例与专用reference桥，新的Temporal信封只在实际需要的运行桥实现，不将整个旧engine复制到新文件。

清单的布局/显示名不影响执行身份；原始资源正文、版本/摘要、权限、后端选择、策略与预算影响身份。凭据只引用环境变量/受保护配置，不将密钥、全局机器路径或活动版本指针放进可分享清单。每个新增函数在实现记录列出真实CLI/用例/执行消费者；只有一个消费者的流程留在该所有者，避免为了未来复用新增通用registry或空类。

实现前先按当前Git状态核本记录。以上是待实现合同；具体验收和源码身份在对应子片追加，不借用AC3b独立调用/CI作为正式运行证据。

## AC3c.1 实施检查点

基线`582b16a4fba75a7e52f5d2f8287499de21ad9cf4`，分支`refactor/architecture-foundations`，开始时只有本准备文档未提交。前片已普通推送、远端一致，自身CI待验。本片先实现完整静态清单，不接正式提交或调用。

- [x] CM1：版本化manifest schema及原完整输入核验/发布所有者的最小复用。
- [x] CM2：CLI prepare-manifest / verify-manifest及公开使用说明，保持无模型/服务副作用和历史完整性。
- [x] CM3：独立于源库的完整嵌套/祖先资源、备份恢复、篡改/多余资产拒绝及发布中断；旧完整输入回归。
- [x] CM4：非editable包/真实CLI、新fresh-context审查、工具自身真实模板审查和普通精确交付/必要CI。

静态manifest字段只包含根精确引用、grant、完整图摘要及未授权标识；图内已有稳定实例、端口装配来源、全部资源/提示/权限/预算。未来正式准入再冻结实际后端policy与运行信封。两个格式沿同一完整资产核验/发布路径，临时目录仍在目标父目录下清理，不将运行数据保存到系统tmp。

## CM1–CM3 实现与源码验证

新增composition-manifest-v1数据格式和三条CLI：prepare-manifest、verify-manifest、prepare-from-manifest。完整图与全部精确资产可携带，接收者独立核验后重新当前准入，生成同一原叶子输入格式；不建立State、模型或服务。历史核验不依赖源库或当前catalog。父运行态产物仍未生成，静态包不授予正式执行许可。

原workflow_definitions中两种snapshot共用_inspect_snapshot完整树/图/文件集合核验，以及_prepare_bundle精确复制/容量/不覆盖原子发布；原prepare_input/inspect_input接口及产出格式保持。_publish_input私有名称改为_publish_bundle，原竞态/清理测试只调整对应私有hook和暂存前缀。没有增加新Python模块、调度器、依赖或数据库表。_manifest_fields归本格式所有者，由生成与完整重建核验共同消费；新增两个私有共用流程各有原叶子与完整图两个真实生产用例。三条CLI消费对应公共接口，from-manifest再消费完整核验及原输入发布。

原工作流/独立调用/任务MCP三套129源码检查通过，16.92秒；新增8个清单案例通过，0.93秒。随后增加从包生成输入与当前准入拒绝，清单及既有架构套17通过，1.26秒。清单案例包括重复嵌套实例、全部祖先Skill及资源顺序、整包/State离线备份恢复、原库移除后无State核验及叶子输入、当前catalog拒绝、六类篡改/多余资产和复制中断无残包。以上轮次不同，分别记录。新非editable包、真实CLI和fresh-context独立审查待验；前片候选CI不作本片证据。

## CM4 发行与实际入口

Python3.12非editable包的工作流、清单、独立调用、任务MCP及架构五套146 passed/零skip，22.86秒；363源/wheel/安装文件一致，283冻结参考身份不变，wheel SHA256 `69536cbb08347466d2a233673f34c9da7a085e36799677a77c1176e48b3ec2d3`。真实CLI16次通过：四专家/五工作流导入、完整10实例组合准备/核验、移除整个原State后再次核验/选定叶子准备/输入核验、未知叶子与覆盖拒绝；旧AC3b.4完整输入摘要在新核验器下保持。源库移除后的静态命令没有重建State，没有调用模型或服务。初轮六Markdown/249链接/75parser及diff通过，最终随审查报告再核。

新独立审查和自身真实structure-review进行中。自身审查先创建完整静态manifest，删除其原始Agent/Workflow定义库，再从该包准备输入并通过原check/run及任务MCP调用Codex/ChatGPT；固定所供应六文件/差异身份、包和原始回执，结果未到不标通过。正式批准/嵌套执行仍在AC3c.2/3和AC4，不由本次静态→受限单叶调用推导。

## 自身审查与修正

R1真实Codex/ChatGPT自身structure-review通过task-MCP完整读取54,818字节附件，120.91秒返回request-changes：prepare-from-manifest允许目标目录落入源manifest内部，发布导致原完整树出现undeclared文件。两例新回归在未改R1非editable包均因DID NOT RAISE失败；原红例、wheel和回执保留。最小修正归原from-manifest所有者，在创建目标父目录和暂存之前比较resolved source/destination包含关系，明确拒绝。两个路径变体各核拒绝后无新目录、原digest及完整核验保持；源码清单10项通过。R2使用独立新安装目录，保留R1可复现，363/283身份通过，wheel SHA256 `cd52801bda47ad5c44753a8e432549c58c40a7e1b8c0ff2562b7d85279bdcdf9`；五套回归、同片复核及真实再审进行中。一次选错两个suite名的exit4/零执行已保留排除，不记通过。

R2最终本地五套148 passed/零skip（19.54秒），363/283身份保持。真实自身structure-review再次通过任务MCP完整读取55,711字节，123.89秒返回approve；先从完整manifest准备、移除原定义库、再生成完整叶子输入，实际check/run的policy、输入/prompt/SQLite及完整原生材料一致。[身份](evidence/2026-11-09-ac3c1-self-review-identity.json)及[结构结果](evidence/2026-11-09-ac3c1-self-review-result.json)随Git保留。该审查只覆盖供应的六文件/差异，不代替整个仓库测试或独立fresh-context审查。R1 request-changes原回执保留，R2同片独立复核及精确交付待收口。下一正式信封准备独立于本候选。

## 本地独立出口

[fresh-context两轴及协调审查](2026-11-09-composition-manifests-review.md)在R2均通过，CM-SP1关闭，无新增finding。独立新包五种内部/深层/..及symlink别名输出均在写前拒绝，源整树和digest保持；外部输出成功。12文件最终快照、363包身份和283冻结身份重核通过；原生R1/R2附件54,818/55,711字节均完整读取到next_offset=null，输入/prompt/结构结果及只读SQLite原回执独立一致。原R1失败与R2通过保留各自范围，未重复调用模型。下一普通提交/自身双OS CI及同片即时远端终结；CM4只待远端部分。

AC3c.1终结：原独立者核精确539163e的19个Git对象、363包/283冻结身份、完整两作业列表与七项必要CI步骤success，21:50:52 UTC即时只读远端同完整SHA；原P2关闭、无新增finding。详见[原审查报告](2026-11-09-composition-manifests-review.md)。本次仅状态归档，不改变已验证生产身份。
