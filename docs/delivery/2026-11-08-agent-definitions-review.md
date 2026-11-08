# AC3a：Agent 定义包独立审查

日期：2026-11-08。状态：初审 request-changes，三项 P2 待修正复核。基线 `deace5b51681338d66bbfbe31ddeff0e114e10dc`，分支 `refactor/architecture-foundations`，初审对象为未提交工作树。

## 范围与方法

先读 `AGENTS.md`、总计划当前检查点、AI Hero skill 索引和 `code-review` / `codebase-design`，再读原始要求、AC3a 出口、ADR0004/0005 和实现。规范与规格分别由新的独立上下文审查；汇总者另外检查发布、备份和发行身份。作者交付记录在独立源码结论形成后才读取，不把前片或作者结果当成本片结论。

原始要求为职能、专长、后端分离，同后端可有多个专家，Agent 作为长期保存、可分享的独立定义/资源包，随后供模板组合。精确出口见[AC3a 行](../plans/2026-11-08-agent-composition.md)：版本化 schema、少量互补定义、提示/资源与内容定址导入，未知版本/越界资源/缺摘要拒绝，导入不执行，备份恢复后版本/摘要/引用可核，每字段有实际消费者。MCP/权限实际装载、祖先强继承、运行冻结、成员和嵌套执行属于后续切片，不作为本片遗漏；保留六阶段、283 冻结文件和旧数据。

完整范围按 `.ergora/checks/ac3a-definitions/review-scope.json`：10 份 tracked 差异和14份新增文件。固定点已解析，HEAD 等于该基线、无新增提交，因此使用 `git diff <baseline> --` 配合逐份读取新文件，而非把空的 commit diff 当作无变化。全部24份初审文件与清单哈希一致。阅读了所有新增源码、schema、示例、测试、公开手册及必要的 `agents`、后端、Skill、State、备份与CLI调用者。

## Standards

以下保留独立规范轴结论，链接和格式略作整理。

**R-1 / P2，硬要求违反：新增遍历限额使旧 Skill 无法读取。** [asset_trees.py](../../src/ergora/asset_trees.py) 初版26–29行新增“500目录／32层”限制，经 [skill_assets.py](../../src/ergora/skill_assets.py) 初版13行同时作用于既有 Skill；`skill_assets.get` 和 `backups._check_assets` 因此拒绝原本合法的持久资产，违反[总计划](../PLAN.md)的“旧数据兼容”要求及兼容基线保护意图。只读内存探针使用有效 `SKILL.md` 加501个空目录：baseline 算法成功，新算法报 `Skill bundle exceeds 500 directories / depth 32`。建议将新增限额限定于定义包，为旧 Skill 保留原读取语义，并补回归覆盖。

**Smell 判断：未发现其他需单列的问题。** 共享树身份有两个真实消费者；职能／后端校验复用原所有者；导入前与暂存后的重验保护不同生命周期点，不宜作为 Duplicated Code 删除。对象先发布、索引最后替换及引用恢复职责集中在定义库。

规范轴独立检查两示例材料及旧算法摘要一致、schema合法、283冻结文件PASS；未运行pytest、wheel或Windows检查。

汇总者补充同轴发现：

**R-3 / P2，可移植包合同部分实现：空目录绕过路径和大小写检查。** [inspect_bundle](../../src/ergora/agent_definitions.py) 初版51–58行只从普通文件清单推导路径前缀；共享树遍历未把目录清单交给该检查。与[公开手册](../AGENT_DEFINITIONS.md)“拒绝Windows保留名称/流和大小写冲突”的包合同不符。在已安装 wheel 上复制合法示例，再分别加入空 `NUL/`、空 `Upper/` 与 `upper/`，或空 `Case/` 加普通附件 `case`，`check` 全部接受。后者无法在Windows按原树保真复制；前两者甚至保持与原包相同的内容摘要。空目录不参与摘要是已说明的设计，但被实际复制的目录仍应参加可移植路径及碰撞检查。该探针在Linux完成，未运行原生Windows。

## Spec

以下保留独立规格轴结论，链接和格式略作整理。

发现两项真实缺陷，均属“实现不正确”：

- **R-1 / P2：共享目录限制破坏旧 Skill 读取与恢复。** 规格要求“保留……既有兼容、……证据和恢复”（[AC计划](../plans/2026-11-08-agent-composition.md)）。`asset_trees.digest_tree` 新增500目录/32层限制，同时替换所有旧Skill消费者。baseline 可合法导入的Skill，只要含501个空目录或33层目录，升级后即被 `skill_assets.get` 和备份验证拒绝，内容与摘要无需发生变化。新Agent包限制应避免隐式改变旧资产合同。
- **R-2 / P2：缺失索引同时被当作初始化和损坏，破坏完整备份与引用保留。** AC3a要求“复用……State完整备份”“定义版本/资源摘要与引用……保持可核”。[import_bundle](../../src/ergora/agent_definitions.py) 初版128行先建立对象目录；首次复制失败后没有索引，`verify_store` 却强制读取索引，使未登记任何定义的原State也无法备份。反方向，已有两份定义时删除索引，再导入其中一份，初版138–139行将缺失索引视为空库，静默重建单条引用，另一份定义从列表与备份语义核验中消失。

未另发现明确AC3a缺项；未发现超出切片的运行实现。所有新增字段均有静态消费者，文档明确后续装载、权限、继承和冻结尚未接入。规格轴完整阅读新增源码/schema/examples/tests及必要调用者，未读作者交付记录；使用既有Python3.11环境和显式 `PYTHONPATH=src` 检查示例材料，未推断wheel验收通过。

汇总者另外在新wheel安装中独立复现了R-2两个方向：首次 `copytree` 模拟抛 `OSError` 后，`definitions` 与离线 `backups.create` 均因缺失 `index.json` 抛 `FileNotFoundError`；已导入两份定义后只移除索引，再导入其一，列表从2条变为1条且调用成功。两个方向应由同一个明确的库初始化/发布合同修正，不能仅把缺失索引一律当空库。

## 实际验证与限制

独立读取原日志：首轮源码82 passed / 2 skipped；扩大源码134 passed / 8 skipped / 1条既有Starlette弃用warning。源码通过依赖显式 `PYTHONPATH=src`；其Python为前片独立venv中的3.11。跳过为2项原生Windows junction及6项未显式指定固定SDK的测试。

发行安装日志显示新venv安装 `[dev,web,temporal,gepa]` 成功；包内五文件日志最终为113 passed / 2 skipped / 同一条既有warning。该回归是作者执行、审查者读取日志，未重复计为独立重跑。

汇总者使用新wheel的Python3.11、移除 `PYTHONPATH`，独立核查并实测：

- 导入模块确实来自隔离安装；356份源码、wheel与安装文件集合及字节哈希全部一致。
- 原283冻结文件均与基线相同，安装内 `reference.verify` 为PASS，未启动runtime。
- wheel SHA256为 `8d9b9c8478eec1cc76bfd6509ac8942a7484f1112fd59943509b682e097aa195`。
- R-2和R-3探针仅使用自动清理的临时State/包，未改源码、既有State或服务。R-1的baseline/new算法对比由规范轴只读内存探针完成。

未执行模型、GPU、MCP、权限强制、祖先继承、多成员或工作流运行；未验原生Windows；当前未有本片精确提交、CI或远端终结。后续修正须重新固定源码/包身份并核实际证据，初版身份与通过结果不替代修正后的验收。

## 处置状态

作者已收到R-1/R-2/R-3并提出修正：限制只施于新Agent包；完整目录清单参加可移植检查；首次完整库在State根下私有暂存后由根级锁整体发布，既有库缺索引拒绝。此处仅记作者计划，尚未复核或关闭finding。

规范轴2项P2（R-1、R-3），规格轴2项P2（R-1、R-2）；各轴最严重均为P2，共3个独立问题。当前切片应完成修正及同片复核后再交付。

## r2：同片源码修正复核

复核范围由 `.ergora/checks/ac3a-definitions/review-r2-scope.json` 固定24份文件，明确排除本共享报告；全部哈希匹配，分支和基线未变、实现仍未提交。重新阅读修改的源码、真实调用者、回归与公开合同，后读作者新增记录；原始发现和初版证据保留。

### Standards

独立规范轴结论：**R-1、R-3修正复核通过，可关闭；未发现新增硬规则违规或需单列的smell。**

共享 `inventory_tree` 保留遍历与身份所有权，旧 `digest_tree` interface 不施加新目录数/深度限制；定义包入口显式启用500/32，并检查完整目录清单中的空目录。兼容包装入口及首库／增量发布分支各有实际职责，未形成冗余校验控制流。

该轴独立只读检查24项身份，对既有测试资产运行真实 `skill_assets.get`（只读SQLite连接）：534个目录、最大33层仍可读取，当前摘要与baseline原算法一致；对其既有备份执行 `backups.verify` 得到 `verified`、`skills=1`。四项目录路径负例均拒绝，包括保留名称、空目录大小写和目录／文件冲突；两示例摘要保持。未重跑pytest、创建备份或检查新wheel。

### Spec

独立规格轴结论：**R-1、R-2关闭，未发现新增Spec缺陷。**

R-1的500/32限额仅由Agent检查入口启用，旧Skill的读取及备份不再因新Agent包约束而拒绝。R-2的首库在State私有暂存目录完成对象、索引后，持根级锁整体发布；首复制或首索引失败不暴露半初始化库。既有库必须读取现存索引，丢索引拒绝导入；增量索引失败保留旧索引，完整遗留对象复验后可幂等重试。读者通过目录整体发布或索引原子替换观察完整版本。

该轴独立核24项哈希和diff检查；以现有Python3.11.15、显式 `PYTHONPATH=src` 重新验证源码测试产生的首复制失败、首索引失败、增量索引失败和恢复备份，定义计数0/0/1/2全部通过。已核作者98 passed / 2 skipped日志及相关测试；未独立重跑完整测试、Windows或新wheel验收。

### 汇总者独立发布探针

使用前片Python3.11环境，显式 `PYTHONPATH=src`，只在自动清理的临时State中执行：

- 首次对象移动后、首索引替换后、完整库移动后分别让子进程真实 `os._exit`，退出码71/72/73；重试前列表分别为0/0/1份定义，各自离线备份均可核，重试后恰好一份完整定义。
- 增量对象移动后、增量索引替换后分别 `os._exit`，退出码74/75；重试前列表分别为1/2份定义，旧版本文档保持，离线备份可核，重试后两份精确版本完整。
- 四个不同定义并发首次导入后，列表和离线备份均为四份，无丢引用。

作者四文件源码回归实际日志为98 passed / 2项原生Windows junction跳过，47.45秒；未混加初版计数。r2源码下三项finding均关闭，本轮两轴均无新增问题。新wheel构建/重装、用户追加的Ergora自身模板实际审查、精确提交/CI与远端尚待单独证据，本节不预认其通过。

## r2：最终本地发行与自身模板审查

2026-11-08 16:06:36 UTC续核。受保护生产、测试和示例文件仍匹配r2清单；只追加的文档状态不计为实现变化。原R-1/R-2/R-3关闭结论保持，无新增阻断finding。

独立读取默认隔离构建、重装和四suite包回归原日志：构建/安装成功，包回归98 passed / 2项原生Windows junction跳过，44.92秒。然后使用最终隔离安装的Python3.11、移除 `PYTHONPATH`，重新计算所有实际字节：356份源码、wheel、安装文件集合及哈希完全相同，283冻结文件逐份与基线相同，安装内 `reference.verify` 为PASS。最终wheel SHA256为 `7ba41fe2246106c14a901ca684a453466c41f72522bf45a37ababe4a757a3859`；不以初版wheel替代该结果。

对最终包14次CLI旅程，独立核脚本、保留的逐次命令/退出码和全部原始JSON输出：全为exit0，两个定义可导入和筛选，全文前后完全相同，导出内容及幂等再导入摘要一致，备份/验证/原home恢复的清单摘要一致。再用安装内公开读取入口重验恢复后的两份定义、原State与恢复State的索引原字节，以及安装内 `backups.verify`，均保持两条精确引用。没有重复执行模型或把日志读取计为重跑98项测试。

### 用户追加的自身模板实际审查

原先在途的Claude调用现已实际完成。独立核验 `.ergora/checks/ac3a-definitions/self-review/` 下的CLI命令、请求、协议prompt/schema、原生stdout、实际result、CLI结果及只读SQLite持久回执：

- 真实入口为 `ergora agent run`，角色 `reviewer`，模板 `repository-governance`，绑定 `claude-code`；run ID为 `80909b859a2642ee93c8d4342fe9e4a8`。
- 进程returncode和CLI退出码均0，持久status为 `succeeded`；原生 `structured_output` 与正式解析result一致，满足模板的 `review-report`、`handoff`及decision schema，decision为 `approve`。
- result原字节SHA256为 `35521b7e6e91488346b9bc178aac05420af0fc76d8a5885657fcc32e07932b32`，与CLI及持久记录一致。实际协议prompt的SHA与运行记录一致，其前缀与原始请求精确一致；保护清单摘要 `4ff26be1fd1ad2c244c282198cf3a190b62471300ccea277828af8e93c887eaa` 和全部生产/测试/示例哈希保持。
- 自审输入含原始AC3a要求、完整保护清单、tracked差异、验证结果和显式加入的架构专家正文；它审的是未提交快照，未自动加载AgentDefinition，也未实施祖先继承。生产者采用Codex、此审查采用Claude Code；不同后端本身不证明模型错误独立。

已读完整原始review-report与handoff：没有blocking finding，确认三项原P2修正；保留以下非阻断建议，不能把 `approve` 简化成“没有任何意见”：

- **S1 / P3：既有定义读取/备份仍调用当前目录的职能与后端准入校验。** 当前catalog未变，此候选不存在已知失效触发；将来收窄catalog可能使原字节完整的定义不可读。应在AC3b/c或第一次catalog收窄前明确版本/迁移和完整性核验与新准入的关系；本片不为尚不存在的变更增加新框架。
- **S2 / P3：跨POSIX/Windows分享受执行位语义限制。** 原Skill身份必须保留执行位；不同OS不能保证这些位保真，包会明确摘要不匹配。建议公开手册说明该限制；该原始建议未做原生Windows实测，本地只核了算法和跨平台描述的范围。
- **S3 / P4：缺失Skill目录错误可更清楚；同名Skill的后续装载规则、定义内sandbox请求的授权归属留AC3b；文件及目录fsync可按项目持久性合同另议。** 当前缺失会可见失败，同名定义资源尚未装载，静态导入不构成权限批准；未发现当前可达的错误通过。进程退出探针不提供断电保证。

新增[自身仓库审查用法](../AGENT_BACKENDS.md#用-ergora-审查自己的仓库)与实际CLI及 `agent_runs` / 后端行为一致；区分进程成功、结构合法、decision和正式workflow验收，明确专家材料需显式加入。该用户要求已获真实成功回执，独立fresh-context审查保持独立记录。精确候选普通提交/推送、必要CI及即时远端终结仍未核验，不标完整AC3a交付完成。

随后核对作者的逐项处置：S2已补公开手册的跨系统执行位限制，保留原Skill身份算法；S1和S3的后续准入/冲突/错误语义职责分别记账，不为本片扩写执行能力。新保存的[完整自审报告](2026-11-09-ac3a-self-review.md)、[结构化result](evidence/2026-11-09-ac3a-self-review-result.json)及[身份记录](evidence/2026-11-09-ac3a-self-review-identity.json)已独立核验：result原字节与真实运行相同，请求和实际交付prompt摘要均匹配，报告及handoff完整保留，16项受保护文件仍匹配。独立只读重跑文档脚本得到16份文档、294个本地链接、43条CLI parser全部通过，`git diff --check`通过；该计数对应此段追加前的检查。最终本地发行及用户追加的实际模板审查可通过，尚待精确提交/CI/远端终结。

## 精确本地候选对象核对

2026-11-08 16:11:38 UTC独立核验候选 `03ae7520c657773e7083cb24b8ef7ce9e77433a6`，唯一父提交为原基线 `deace5b51681338d66bbfbe31ddeff0e114e10dc`。该提交恰好包含final-scope清单的28份变更文件；逐份 `git show <candidate>:<path>` 的原字节哈希与清单和当时工作树全部一致，核验时工作树干净。生产/测试/示例仍为通过r2源码、最终包和实际自身审查的原内容。

候选Git对象内的自身审查result仍为原始 `35521b7e…932b32` 字节，身份记录的16份保护文件逐项匹配，模型报告和handoff原文均完整保留。AC3b已明确任何catalog收紧前完成历史完整性/当前准入分离，AC3d已明确同名Skill的实际加载冲突，公开手册的执行位限制也在候选内。状态归档未将静态定义库或普通reviewer调用写成正式运行支持。

本轮独立只读静态复核为16份文档、297个链接、43条CLI parser全部通过；精确基线→候选的diff检查通过。无新增finding。普通推送进行中，尚未核精确远端及该候选必要CI；此节不提前关闭完整交付。该追加本身属于后续审查归档，不改变已固定候选内容。

## 同片终结：官方CI与即时远端

2026-11-08 16:31:03.527783 UTC，独立重新GET GitHub官方run和两份job页面，未以作者缓存摘要代替实时读取：[Portability 42498512673](https://github.com/626619403/Ergora/actions/runs/42498512673)明确绑定完整候选 `03ae7520c657773e7083cb24b8ef7ce9e77433a6`、正确workflow及Success状态。官方job完整批次为size200、totalCount2、hasMore=false；两项均completed/success。

|精确job|必要步骤与结果|
|---|---|
|[Ubuntu 3.11 / 128785966185](https://github.com/626619403/Ergora/actions/runs/42498512673/job/128785966185)|Build and install wheel、Packaged reference identity、Native application regression均success。|
|[Windows 3.12 / 128785966430](https://github.com/626619403/Ergora/actions/runs/42498512673/job/128785966430)|上述三项及Windows PowerShell 5.1 installer and upgrade均success。|

每个必要步骤均有completed标记，日志URL均包含同一完整候选及各自精确job ID，无failure/cancelled/timed_out步骤。另读候选内workflow，确认回归确实选择全部 `tests`、适用reference测试及Windows安装升级检查；未把后续别的候选CI替代本片。原本地未做原生Windows检查的事实保留，新增通过范围来自此官方Windows job；不扩展为模型、GPU、权限或后续组合能力验收。

2026-11-08 16:31:05.455580 UTC，独立执行只读 `git ls-remote`，沿既有内存SSH配置引用、未打印敏感字段，exit0；`refs/heads/refactor/architecture-foundations`即时远端SHA为 `03ae7520c657773e7083cb24b8ef7ce9e77433a6`，与精确候选一致。普通push记录为16:10:22 UTC exit0，远端从唯一父基线前进至该候选；本次实时核验独立于该历史记录。

终结时工作树的生产、测试、示例对候选无差异；后续仅AC3a审查/状态归档及明确未实现的下一片准备文档，不属于该实现候选，不递归触发新实现审查。三项P2保持关闭，原失败、初版与修后实际检查分别保留，无新增finding。完整AC3a现可关闭；尚未实现的AC3d/3b/3c/4能力仍按原计划验收。
