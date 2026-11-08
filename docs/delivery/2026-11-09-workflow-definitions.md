# AC3d：工作流定义与静态继承编译

日期：2026-11-09。状态：WD1–5实现、修正后本地验证、新独立复审和自身r3真实审查通过；WD6精确交付待完成。正式基线 `9bb84c6437bd4b38f928defcaad0ec678fa24a5e`，工作树开始时干净，分支保持 `refactor/architecture-foundations`。前片生产基线为完整AC3a候选 `03ae7520c657773e7083cb24b8ef7ce9e77433a6`，其双OS CI及16:31:05 UTC独立远端终结均通过，不替代本片证据。

## 目标与边界

用户要求可复用子模板、串并行和显式all-join；每个实例完整继承当前结构路径所有祖先的Skill指令及上下文，资源只增不减；权限不得越过父级、任一祖先或项目上限；父子可在同一新修订共同调整，旧修订不变。依据[ADR0005](../architecture/decisions/0005-composable-workflows.md)，本片先交付静态定义与可验证编译，不启动第二套调度器，不将配置可保存称为已能运行。

AC3b负责实际权限/Skill/MCP装载及历史完整性与当前准入分离；AC3c负责批准链内递归manifest；AC4负责成员、可信审查聚合和Temporal嵌套执行；AC5负责画布。本片不绕过六阶段、候选绑定或原283冻结文件。跨OS执行位和备份平台限制沿AC3a。

## 需要固定的实现合同

- 工作流以版本化数据包保存，节点引用精确Agent或子工作流版本及内容身份；重复引用生成不同结构路径实例。定义引用与工作依赖分开，前驱/兄弟不成为继承祖先。
- 明确具名输入/输出及绑定；串行由依赖表达，无依赖的就绪分支可并行；汇合节点显式列出全部必需分支。静态编译拒绝未知端口、引用环、图环及无法解析的身份。
- 按root→leaf合并有序资源、保留全部来源；相同逻辑ID但不同内容拒绝，按实际加载名称处理同名Skill冲突。叶子预览返回完整必读材料及身份；不以目录路径或摘要代替正文。
- 权限使用有明确语义的路径范围/访问模式和工具/网络请求，不能用无作用的能力标签假充隔离。静态整链校验与adapter真实enforced/advisory/unsupported分开；编译结果不构成执行授权。资源新增仍须落在整条授权链内，子级收窄后无法读取祖先必读材料则拒绝。
- 根约束展开深度、节点数、全局并发及静态材料大小；嵌套不能倍增突破。动态父结果及最终模型容量在后续调用前再次检查，不声称现在已冻结未来材料。
- 新修订固定整棵引用树；修改父子定义后，编译新根一次核全部链，旧根及已有版本不改。项目真正采用修订及批准语义沿AC3b/c，不在本片增加未核对sidecar。

复用方向：两种定义包的完整资源检查与原子版本库现在有真实共同消费者，可抽出共有所有者，保留`agent_definitions`全部公开入口及既有磁盘布局；Agent后端仍归`agents/agent_backends`。共享存储不应接管角色、图或权限语义，也不引入全局插件注册表。新CLI不能重载已有`workflow`原样转发的兼容行为。

## 可验收步骤

- [x] WD1：固定schema/CLI及字段消费者，确定权限路径语义、具名端口和引用规则；列明当前静态范围与后续准入边界。实现合同如下，后续检查与审查仍待完成。
- [x] WD2：实现WorkflowDefinition包/版本库和共享资源/发布机制，验证旧Agent包、Skill与备份兼容；缺失或漂移引用明确拒绝。
- [x] WD3：实现静态DAG递归展开、稳定实例身份、完整祖先材料、资源冲突、整链权限及全局预算检查。
- [x] WD4：提供少量串并行/汇合示例与真实CLI预览；验证共同父子修订、新旧根分离、重复引用和依赖非继承。
- [x] WD5：受影响合同、非editable包/冻结身份、备份恢复；Ergora自身reviewer实际调用，新的fresh-context独立审查及finding处置。
- [ ] WD6：更新通用手册/架构/计划，普通精确提交推送、必要双OS CI和同片远端终结。

恢复时先读总计划、AC表及Git实际状态。以上是实施合同和验收清单，不是已实现证明；每一步完成后记录实际结果，不能沿用AC3a的通过替代本片验证。

## WD1固定合同

- 新命令使用`composition check/import/list/show/export/preview`，不改`workflow`兼容转发。包入口为`workflow.json`，仅JSON，沿Agent同一可移植路径/完整树身份/版本不可覆盖规则；分别存`workflow-definitions/`，共享代码只管资源与版本发布。
- 节点是Agent引用、Workflow引用或`join: all`。引用必须含kind、ID、精确版本、包digest。Agent节点选择定义允许的role，采用固定`task`输入与`result`输出合同；Workflow节点端口来自被引用定义。绑定只有工作流输入或显式直接前驱的具名输出，不执行表达式。all-join明确列depends_on，输出每个分支的具名结果映射；不是多数票批准。
- 权限是静态请求/上限，字段为`read`、`write`的可移植逻辑子树路径、`shell`布尔与`network`精确HTTP(S) origin清单。逻辑挂载只含`workspace[/path]`和`definitions/{agent,workflow}/ID/VERSION[/path]`；`definitions`可授整个只读资产库，禁止向定义库声明写权。路径按段包含，不支持glob、绝对宿主机路径或大小写折叠授权。每层请求必须为父级子集，根还需满足显式grant文件；没有环境权限推断。完整继承的每个资源来源都必须在叶子的read范围，Skill要求其整个目录可读。后端sandbox只在预览列为请求，不当作授权或OS隔离证明。
- 工作流声明depth/instances/concurrency/material_bytes四项limits，grant同时提供总上限。所有结构实例（含根/工作流/汇合）都计数；每条祖先链与每个子树分别检查，根预算覆盖全部子树，未来执行使用共享根并发配额，不能乘法扩张。静态材料预算计每叶子的完整拼装UTF-8正文及来源标记，重复调用分别计费；未生成的端口值不冒称已冻结或已满足模型容量。
- 预览输出稳定root/node路径、父链、局部依赖/端口、完整叶子正文/来源/摘要、有效权限及并发作用域。相同资源ID异内容/种类拒绝；同名Skill异树拒绝；同名同树合并时保留所有逻辑ID与来源，逐来源检查权限。前驱/兄弟不参与继承。
- 导入先核本地包及现存精确依赖；原子发布仅指单定义版本。完整根修订通过固定全部递归引用与预览身份表达，新父子版本可依赖顺序导入，再发布新根；旧根仍固定旧引用。项目采用、正式批准、运行冻结/装载与Temporal执行依次归AC3b/c/4，不由本片预览授予。

现有共享候选：Agent定义的完整包检查/资源读取与不可变版本库将由两种定义共同消费；`asset_trees`保留旧Skill身份与接受集合。新增图与权限语义留在workflow所有者，不下沉到存储或模板后端。无新依赖、DB表、可信评分或CI作业计划。

## 本地实现与第一轮检查

实现已完成WD2–WD4：新增`definition_bundles`共享完整包/资源检查及原子不可变版本库，保留Agent公开入口、原存储路径/身份；`workflow_definitions`拥有图/端口/递归解析、完整祖先材料和逐来源权限、全局/子树预算。`composition` CLI接入，备份增加递归交叉引用校验。未增加依赖、DB表或CI作业，未改冻结283文件。

新增两个示例专家、三个单项审查子模板、并行总审查和kernel串行根模板，共10个展开实例；[使用手册](../WORKFLOW_DEFINITIONS.md)给出安装后完整操作及实际限制。Codex/Claude只是静态binding请求，不冒称这些图已经调用模型。

已实测：共享重构后既有四套相关源码100 passed/2 skipped；新工作流初跑34 passed/1 failed，失败是测试对`backups.restore`既有root/backup参数次序写反，已纠正。之后五套相关源码135 passed/2 skipped（两项原生Windows junction本地跳过），有一条既有FastAPI测试客户端弃用警告。日志分别位于忽略的`.ergora/checks/ac3d-workflows/wd2-source-tests.log`、`wd3-source-tests.log`、`r1-source-tests.log`。此后仅移除无消费者的私有_count参数，下一实际包验收会重新覆盖。

下一WD5：新的fresh-context两轴审查、非editable包与完整CLI备份恢复旅程、最终源码/包/冻结身份、Ergora自身模板真实reviewer。WD6提交/双OS CI/独立远端均未开始，不能登记完整AC3d完成。

WD5发行本地进度：扩大至9套相关源码177 passed/8 skipped（Python3.11.15）；新的Python3.12.3非editable wheel同9套177 passed/8 skipped。两Windows junction与六固定SDK跳过分别保留，不称已验Windows/SDK运行。359份源码/wheel/安装文件逐字一致、原283冻结文件逐一对基线保持；初版wheel SHA256 `1a4064c15efecde47567042e7fcf7e6f7f18f1898686064e25987dac3f59c3c0`。原旧env首次构建因缺wheel失败，保留r1-build.log；新env安装构建依赖后成功，未修改项目依赖。

26次真实CLI均得到预期退出：两类check及缺库preview不创建State，4Agent/5Workflow导入、列表/全文/10实例预览、独立子图预览、导出/幂等、完整备份/校验/原路径恢复、恢复后完整预览相同、旧reference verify；数据库仍v1/16表且0 Agent运行。根预览静态prompt总量13,213字节，身份`fcf1279f5d3bacd0056c5662b75d4d6a2eb9f36731daddb29628d08731dbd455`。实际模型审查是另一个独立State中的既有agent run，不与此静态CLI旅程混合。

限定性能测量：Python3.12.3安装包、同一进程顺序、warm OS缓存，每种5次；1/10/50相同子图分支分别展开4/22/102实例，中位13.7/19.9/53.8ms，静态prompt3,434/34,340/171,860字节。另一次tracemalloc峰值约4.50/4.51/4.56MB。测的是静态预览，不是调度/模型吞吐或正式容量承诺。原始独立样本保留r1-preview-performance.json。

新的fresh-context评审已核34文件身份并独立跑四套115通过/2跳过、283文件基线一致；完整两轴结论待回执。Ergora自身repository-governance reviewer已用Claude Code实际启动，尚未返回，不预记approve。源码未在审查期间修改。

## 审查发现与r2修正

fresh-context两轴的[原始报告](2026-11-09-workflow-definitions-review.md)保留：Standards通过、ST-1 P3非阻断（schema版本规则重复）；Spec request changes，SP-1/SP-2 P2（不完整定义授权前缀、通配符/空白origin）。两者均由独立者端到端复现，原177项通过不能覆盖它们。已修正：除裸definitions外必须完整kind/合法ID/精确版本；网络须为规范DNS/IP origin，省略默认端口，拒绝无效authority。新增8项拒绝合同同时覆盖定义和显式grant，并补合法精确版本/DNS/IPv4/IPv6兼容。ST-1改引用到根version规则，删除重复定义；尚待最终检查和同片复审，不预记关闭。

Ergora自身模板r1真实Claude reviewer于2026-11-08 17:07:55 UTC完成，run `8841724392044f9d9f060cae38782abb`，CLI/后端均exit0、status succeeded、decision approve；保护源码未变，结果SHA `0e9308413550bc5a69245afe9a251d1699524b1feaf7f8a341c5b36d2e0b1cd0`。原样[结果](evidence/2026-11-09-ac3d-self-review-r1-result.json)与[身份](evidence/2026-11-09-ac3d-self-review-r1-identity.json)随Git保留；这是旧r1快照的独立普通调用，不是最终源码批准，也不覆盖独立者SP-1/2发现。下一在修正后快照再调用自身reviewer。

自身模板建议S1已采纳：ADR0005首部明确静态实现与未来运行分开；S2保留局部构造（常规读取与带递归准入的import inspector不同），目前实测无性能缺陷，不为一个可选参数增加工厂控制；S3共享JSON诊断采用Definition标签，未承诺错误消息文本稳定；S4同包加载名检查沿完整import/preview所有者，已有同名异树拒绝合同，不新增镜像测试；S5 kernel例子需要write/shell表达执行节点，保留显式grant与手册收窄说明；S6全部并发scope的共享最小上限归AC4d，已在计划。实际成功构建日志为r1-build-final.log；报告已补177/8及26CLI，原失败日志不删。

WD5 r2本地复核：受影响源码与最终非editable包各144 passed/2 skipped（同前两项原生Windows跳过），成功构建r2-build.log、安装r2-install.log、26CLI r2-cli-journey.json均通过。最终359/283身份通过，wheel SHA256 `fa3bc27cf5cfc73f6f6412f6ba20cc220af380fd2b9eef80353bf326a3a33ccf`。恢复后根完整预览仍fcf1279…d455，旧/新State的定义身份保持；本轮备份manifest `f372c82f6f042b2d8ccf4c841d62d5eda1e1722f16e07a8da577e7e87c4718bf`。原样本与当前样本不混加，9套177/8是r1扩大回归，5套144/2才是修正后相关检查。

[可分享本地身份](evidence/2026-11-09-ac3d-local-identity.json)包含精确生产/测试/示例文件、最终wheel、CLI及有限性能原样本，不携带本机路径或凭据。r2相同条件4/22/102实例的5样本中位16.2/23.6/52.4ms，单独tracemalloc峰值约4.50/4.51/4.56MB；数值只属于静态编译。新的同片独立者已复验非法输入及合法兼容、核最终包/恢复库并报告关闭SP-1/2与ST-1，正式追加报告进行中；r2自身模板实际调用仍待回执，不能将其写作通过。

自身r2回执：Claude run `2fad7f1f057545de95a706d44f7a157e`在600秒超时，原生returncode -9；按用户授权回退Codex，run `f5b368d0b4ab4679be5f907151c4e980`于17:26:57 UTC正常返回structured request-changes。其报告明确“只读到tracked diff，任务禁止shell且限定Claude Read/Grep/Glob，无法检查新文件”，未建立源码finding。原样[结果](evidence/2026-11-09-ac3d-self-review-r2-result.json)/[身份](evidence/2026-11-09-ac3d-self-review-r2-identity.json)保留，不将它称为通过。该限制来自本次审查任务文本，不是Codex原生错误或仓库实现缺陷。

r3只修正自身审查输入：继续使用Ergora repository-governance reviewer和Codex回退，允许限定的只读仓库命令，显式附入四份关键新文件全文并核输入SHA；不重启已超时Claude，不修改生产/测试/示例。源码仍是r2最终包已验身份，独立两轴结论保持其实际范围。r3待返回及真实协议验证。

## WD5最终自身审查

r3 Codex run `5abc348026a94c20a367199479c2cfcd`于2026-11-08 17:36:20 UTC完成，CLI/原生returncode均0、succeeded、decision approve，无新增finding或建议。原样[结果](evidence/2026-11-09-ac3d-self-review-r3-result.json)及[核验身份](evidence/2026-11-09-ac3d-self-review-r3-identity.json)保留，结果SHA256 `b0ec8904661ed4f28bfc5cab8bf7e98a48104420a178d485e5a6222664783883`。2026-11-08 17:39:53 UTC核实际SQLite回执、原始结果逐字、25项保护文件与输入manifest一致；实际交付prompt包含任务全文及模板role合同，共125,097字节，SHA256 `68f0436d675b70c03f6c2e4cf49656d21345d9404fbb53d5aae239c028cdcd4c`。任务文本自身SHA与附加合同后的SHA分别保存，未推断默认模型身份。

审查者确实读取了源码，但报告声明git diff/log及独立hash命令遇沙箱挂载错误，身份判断依赖提供的manifest及证据；主代理已独立核保护文件和实际协议身份。该普通只读调用没有运行项目测试，不能替代fresh-context两轴独立复核、正式工作流批准或后端OS隔离。r1、r2失败/限制原记录不改；WD5完成，下一WD6完整scope、普通提交/推送、精确双OS CI及同片独立远端终结。
