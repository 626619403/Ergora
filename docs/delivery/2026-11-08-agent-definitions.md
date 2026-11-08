# AC3a：专长 Agent 定义包

日期：2026-11-08开始，2026-11-09续。状态：完整完成。候选03ae752的本地/最终包、独立复审、自身模板真实审查、普通推送、自身双OS CI及16:31:05 UTC同片独立即时远端终结均通过，三项P2关闭。基线 `deace5b51681338d66bbfbe31ddeff0e114e10dc`，分支 `refactor/architecture-foundations`。

## 本片合同与所有者

用户要求职能、专长与后端分开，同一后端可以提供多个互补专家；定义可以独立保存、分享和复用。AC3a交付静态Agent库，不改变项目绑定、正式六阶段或已有运行。嵌套、祖先资源/权限、MCP实际装载、成员分配及运行冻结分别留给AC3d、AC3b/c和AC4。配置可导入不等于可运行。

定义包采用 `agent.json`（schema_version=1）和相对资源文件。字段只包含当前有消费者的ID、版本、说明、职能、专长、后端和资源；暂不接受尚未执行的MCP/权限/预算字段。后端结构和职能能力沿 `agents.validate_binding` 核对，不复制组件schema。资源区分一份初始指令、上下文和Agent Skills目录；文件须有SHA256，Skill须有原完整树摘要。检查/查看读取完整文本，但导入不执行脚本、不连接服务、不调用模型。

`agent_definitions`拥有检查、内容定址导入、精确版本读取、筛选及导出。库位于State下的 `agent-definitions/`，用原子索引引用完整发布的不可变对象，不新建数据库表、活动版本指针或调度器。同ID/版本内容不可覆盖，修改必须新版本。CLI是公共消费者，备份所有者另核全部索引→对象→资源引用；导出包可再次导入。

树身份复用Skill原算法（排序文件路径、SHA256和可执行位），抽出共享的树检查所有者，维持既有正常Skill摘要。新增定义包需要在遍历前拒绝符号链接、Windows reparse point和特殊文件；沿原10 MB/500文件限制，并约束目录数量/深度，防止尚未读文件就无限遍历。备份复用同一链接判断，仍保留自己的全State库存合同。

## 验收与未验范围

需验少量互补示例、同后端多定义、版本不可覆盖、未知schema/职能/后端及越界/缺摘要/篡改拒绝、无执行、幂等/完整发布、导出再导入、备份恢复后精确身份和引用保持。检查现有Skill/备份/Agent/架构合同；构建非editable包，核新包文件及原283冻结身份，再请新的fresh-context独立审查者，普通提交推送并核精确CI和远端。

未验证模型质量、MCP、权限强制、继承、工作流运行/恢复、GPU和专业技能效果；静态专家示例不是效果评价。临时构建和证据保存在本仓库忽略目录 `.ergora/checks/ac3a-definitions/`，不使用清理风险目录。

## 实现与源码验证

已实现 `agent_definitions`、schema v1和 `agent definition check/import/list/show/export`；`check`不实例化State。`asset_trees`拥有原Skill摘要及遍历前链接/特殊文件拒绝；保留`skill_assets.digest_tree`和`skills.digest_tree`入口。两份自有示例均用Codex，分别提供kernel实现/测量和架构审查材料，证明定义不等于后端；未复制第三方Skill或声称效果。手册、当前架构和身份说明同步静态范围。

首轮源码选择定义/Skill/备份/架构四文件，82 passed、2 skipped、49.15秒。之后补资源基数/Skill缺摘要/无效frontmatter、重复JSON、大小写路径、树限额检查并完善CLI和路径实现。扩大到定义/Skill/备份/架构/状态迁移/schema/原Agent七文件，显式 `PYTHONPATH=src` 使用既有独立Python环境：134 passed、8 skipped、67.26秒。跳过为两项原生Windows junction和六项未显式指定固定Forge/mini SDK；保留一条既有Starlette测试客户端弃用warning，不在本片变更依赖。两个轮次分开记账，不混加。

实际源码命令为 `python -m pytest -q --tb=short --basetemp=… tests/test_agent_definitions.py tests/test_skills_evaluation.py tests/test_state_backups.py tests/test_architecture_boundaries.py tests/test_state_migrations.py tests/test_schema_contracts.py tests/test_agents.py`，源码选择依靠显式环境变量；原日志在本片忽略证据目录。覆盖导入无执行、原子重试/引用最后发布、并发幂等、版本不可覆盖、导出再导入、损坏拒绝、恢复身份及旧Agent/Skill兼容。

默认隔离wheel构建exit0，新的独立venv正在安装该包及dev/web/Temporal/GEPA。包内行为、源码/包/安装身份、独立审查、精确提交/CI及远端均待完成；不从源码通过推断这些出口。下一交给新的fresh-context评审者检查原始合同、当前全部差异及实际证据。

初版发行后续实际通过：wheel `8d9b9c8478eec1cc76bfd6509ac8942a7484f1112fd59943509b682e097aa195`，新venv安装exit0，356源码/wheel/安装文件与283冻结身份及公开verify一致；包内五文件113 passed、2原生Windows junction跳过、同一弃用warning，55.79秒。另14次真实包内CLI串起两定义导入/筛选/全文查看/导出、离线备份/核验/原路径恢复和幂等再导入，全文、精确版本和索引字节均保持。此段证据属于初版，不替代下述修正后验收。

## 独立发现与修正

已完整阅读[fresh-context独立报告](2026-11-08-agent-definitions-review.md)。采纳三项P2：R-1新目录限额错误传播到旧Skill；R-2首导入失败留下无索引库且既有索引丢失被误当初始化；R-3空目录未参加portable/大小写检查。初版通过检查与真实失败原样保留，不提前关闭finding。

修正后共享遍历返回完整目录清单；Agent包才启用500目录/32层限制，旧Skill接口保留目录接受集合。所有目录（包括空目录）和文件都核可移植路径及大小写。首个库在State根下私有暂存完整对象和索引，经根级文件锁整体rename发布；既有库必须有索引，缺失明确失败。增量发布仍对象先完成、引用最后替换，可验证复用未引用完整对象。

补充公开入口回归：旧Skill的501空目录和33层树仍可get/完整备份；首复制/首索引失败后可列空库及备份；增量索引失败保留旧引用且重试成功；既有双定义索引丢失时禁止静默重建；空保留目录、空目录大小写及目录/附件冲突拒绝。修正后四文件源码98 passed、2原生Windows junction跳过、47.45秒。新最终包及同片复核待完成。

用户追加每大项使用Ergora自身审查模板检查本仓库，已纳入后续验收：优先与执行者不同后端，以实际`agent run ... reviewer --template ...`调用和原始结构化回执为证。当前模型环境引用已存在，不需复制密钥。准备在本片修正后先试跑；此检查不替代新的独立评审，也不把静态定义库冒称运行/继承已接入。

修正后发行实际完成：默认隔离构建和新venv重装exit0，最终wheel `7ba41fe2246106c14a901ca684a453466c41f72522bf45a37ababe4a757a3859`，356源码/wheel/安装及283冻结身份、公开verify通过。移除PYTHONPATH运行四受影响suite：98 passed、2原生Windows junction跳过、44.92秒。最终包另跑14次真实CLI旅程，全文/精确版本/索引及备份清单摘要恢复后保持；未增加DB表或更换schema v1。

同片独立源码复核通过，R-1/R-2/R-3关闭，无新增finding。独立者另测五个真实`os._exit`窗口：首次对象/索引/库发布后分别只见0/0/1定义，增量对象/索引后分别只见1/2；每种旧引用、离线备份和重试均成立，另4份不同定义并发首导入无丢引用。最终包证据已交同一独立者核验，未用源码复核代替发行出口。

2026-11-08 15:58:02 UTC实际由最终包`ergora agent run`启动Claude Code reviewer，使用`repository-governance`审查合同，输入包含原始AC3a要求、源码清单/摘要、tracked差异、真实验证及显式选入的架构专家材料；原始结果仍在运行，未登记通过。此时不修改受保护生产/测试/示例文件，完成后再次核身份。手册另加入通用的自身模板审查用法，不含本机凭据。

## 自身模板真实结果与建议处置

同一调用在16:01:36 UTC完成，run `80909b859a2642ee93c8d4342fe9e4a8`，真实CLI exit0、后端returncode0、status succeeded、结构化decision approve。已核实际交付prompt/schema、result SHA和受保护源码身份未变；原始回执SHA256 `35521b7e6e91488346b9bc178aac05420af0fc76d8a5885657fcc32e07932b32`。[模型报告及handoff](2026-11-09-ac3a-self-review.md)、[原始结构化回执](evidence/2026-11-09-ac3a-self-review-result.json)和[输入/输出身份](evidence/2026-11-09-ac3a-self-review-identity.json)随Git保存。不同harness不证明底层模型错误独立，普通独立调用不产生正式workflow批准。

同片独立者另外核最终356/283与wheel身份，逐项重验14CLI输出和恢复索引/两引用，并核真实自身模板调用、原生structured_output、prompt与result身份，均通过。自身审查未运行测试，未核当时尚在途的最终包回归；98包实测来自作者日志及独立核验，两个范围分别记账。

|建议|处置及边界|
|---|---|
|S1：历史资产完整性与当前catalog准入耦合|纳入AC3b/c，任何角色/catalog收紧前先拆分完整性读取与新准入，明确旧版本读取/备份策略；本片catalog未改，不扩大重构。|
|S2：跨OS执行位语义会改变摘要|已补通用手册：分享须保持字节/执行位，跨系统移植显式新版本；不改变原Skill摘要。|
|S3a：缺Skill目录错误可更友好|现有OSError由CLI转为可见失败，不重复添加上层判空；在AC3b资源装载错误投影时一并考虑。|
|S3b：同名Skill需加载规则|纳入AC3d/3b资源冲突策略，按实际native命名规则解析；静态包现可保存，不声称已经可加载。|
|S3c：索引可选fsync|本片证明进程退出/重试合同，不新增掉电持久性保证；沿既有原子替换实践，后续持久性升级需统一规格与实测。|
|S3d：定义中的sandbox请求归属|纳入AC3b整链授权，定义binding不构成权限批准，不得越过项目或祖先上限。|

过程中两次只读核验辅助命令分别因相对路径`as_uri`和误用系统Python缺包失败，均纠正后才登记通过；未改生产代码、未作为通过证据。下一固定最终scope/静态、普通提交推送及自身精确双OS CI/远端终结，再进入AC3d。

## 精确候选交付

普通候选 `03ae7520c657773e7083cb24b8ef7ce9e77433a6`，唯一父deace5b，28文件；16文档297链接/43parser及diff check通过。普通push exit0，2026-11-08 16:10:22 UTC远端同完整SHA。独立者16:11:38 UTC核候选Git对象、完整28文件/身份/回执及当时干净工作树，均通过。后续只追加本项归档，不改变生产/测试/示例身份。

自身[CI42498512673](https://github.com/626619403/Ergora/actions/runs/42498512673)首轮官方观察In progress，两job为Ubuntu128785966185及Windows128785966430；已核run绑定完整03ae752及完整批次`hasMore=false`，尚未登记必要步骤成功。下一双OS完成证据及同片独立即时远端终结，AC3a尚不标完整完成。

后续官方观察Success，主代理精确核验exit0：Ubuntu三个必要步骤、Windows四个必要步骤全部success，run/job/步骤日志URL与completed标记绑定完整03ae752。原在途观察另留副本，未把Ubuntu跳过的Windows安装步骤当必要项。已交同片独立者实际GET官方证据并即时核远端；其终结前仍不登记完整AC3a完成。下一AC3d已有[准备记录](2026-11-09-workflow-definitions.md)，仅列合同/验收，尚无实现或继承运行证明。

## 最终完成与下一项

同一独立者16:31:03 UTC实际GET官方run、两job及完整batch200/total2/hasMore=false，核必要步骤及完整候选日志身份均通过；16:31:05 UTC实际只读ls-remote精确同完整03ae752，未有新增finding。工作树生产/测试/示例与候选无差异；此后只归档完成状态/下一计划，不递归审查或重复无变化的行为检查。

完整AC3a关闭。初版134源码/113包、修后98源码/98包、两轮各14CLI、最终356/283、三项P2及自身模板S1–S3处置分别保留，未混加或延伸到未验维度。下一[AC3d](2026-11-09-workflow-definitions.md)实施工作流包、静态展开与强继承；新片使用新的fresh-context审查者，原reviewer不当作下一片新独立上下文。MCP/权限真实执行、递归manifest、多成员/嵌套运行与页面仍待后续切片。
