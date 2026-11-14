# 组件变更协议

本页供修改Ergora仓库的Agent和维护者使用。先按根[合作规则](../../AGENTS.md)恢复当前计划，再选择下表对应的组件。用户安装／操作仍以[使用手册](../USAGE.md)及各领域手册为准；本页不重列命令参数。

## 选择实际变更点

|要改变的东西|先读的owner与真实消费者|本页分支|
|---|---|---|
|某角色调用哪个模型／CLI|`components`、`bindings`、`agent_backends`，消费者`agents`／`agent_runs`|[Agent和外部来源](#agent和外部来源)|
|工单平台和原PR／MR关联|`issue_backends`、`issue_sources`，消费者`issues`／`issue_writebacks`|[Agent和外部来源](#agent和外部来源)|
|角色、专长、嵌套模板、Skill／MCP／上下文|`agent_definitions`、`workflow_definitions`、`definition_bundles`、`task_mcp`|[定义和完整资源](#定义和完整资源)|
|项目配置、持久格式或迁移|`projects`、`registrations`、`contracts`、`state`；消费者为相应领域用例|[配置和持久格式](#配置和持久格式)|
|正式任务／训练的运行、批准、取消、恢复或结果|`tasks`／`training`及相应`reference_*`；原`WorkflowInput`／Temporal／job owner|[执行和证据](#执行和证据)|
|记忆、Skill、评价、搜索或复盘|`memory`、`skill_assets`、`evaluation`、`optimization`、`research`、`retrospectives`|[改进和可选工具](#改进和可选工具)|
|命令行、HTTP或页面交互|`cli`、`web`和`data/console`，调用上表用例|[交互入口](#交互入口)|
|安装、升级、平台脚本或验证|`scripts`、`tests`和显式CI分组|[脚本和检查](#脚本和检查)|

新增／调整／删除前，找到一次真实的“配置→构造→调用→结果→恢复”路径；记录变更的可观察行为、调用者和已有替代接口。把具体实现的配置、初始化与特有行为留在其owner。已有共同契约足够时直接实现它；存在真实可替换实现而没有契约时，再给本族设计构造和执行接口。普通数据分支、数学分支和一个实际扩展函数不因此需要ABC。新文件应隐藏具体调用义务，不能只把一次调用套一层转发。

对行为不变的整理，保持配置、持久格式、失败和恢复语义；算法或能力扩展另立可验收片。删除先迁移真实消费者，明确旧版本／历史记录如何读取，删除失效分派与测试，不增加只为拒绝已删除接口的兼容分支。每个guard须对应外部输入、持久身份、资源或并发的可达失败，由真正拥有该不变量的边界处理。

## Agent和外部来源

Agent后端的共同接口在[AgentBackend](../../src/ergora/agent_backends.py)，本文件的`_BACKENDS`与`for_binding`负责选择；[agents](../../src/ergora/agents.py)调用同一接口，负责结果schema与进程结果。扩展一个实际后端时：

1. 实现原生命令、stdin、结果提取、诊断及实际支持的模式；如支持归档或续接，按接口补原会话身份和资源恢复。用[CommandBackend](../../src/ergora/agent_backends.py)的`stage-json-v1`已能完成需求时，先用已有可配置命令入口。
2. 在本族工厂注册，并按需在[组件目录](../../src/ergora/data/components.json)声明配置／角色能力和平台支持；可选SDK仍放extra或独立工具环境。`agents`、任务调度、CLI和页面继续调用共同接口，不再按新后端名字加一套执行分派。
3. 用已有[Agent测试](../../tests/test_agents.py)的实际构造／协议接缝验证所改模式，覆盖真实失败而非只断言argv字面量。`available`、凭据存在、模式准入、真实调用和业务验收分别记录；不支持的模式明确失败。异后端审查是优先策略，回退保留实际原因。

工单来源使用[IssueBackend](../../src/ergora/issue_backends.py)及其本族工厂；[来源身份](../../src/ergora/issue_sources.py)拥有API base、仓库namespace和number／iid的归一规则。原始ID、仓库内编号和完整文本不能互换或截断。沿[工单接缝](../../tests/test_project_issues.py)验证分页、漂移、原生响应和可达错误；任意外部PR／MR采集当前仍是独立待办，不能用已有候选关联冒充它。

只读采集与外部写入分别处理。新增评论／标签动作由[issue_writebacks](../../src/ergora/issue_writebacks.py)的本域动作契约持有，原intent／attempt／receipt及unknown对账保持；平台协议仍在IssueBackend。没有明确写入需求和既有授权时，只实现本地报告，不默认发表评论、approve或merge。

## 定义和完整资源

定义／schema／preset分别在`data/presets`、`data/schemas`，库与编译在[定义owner](../../src/ergora/workflow_definitions.py)和[完整包owner](../../src/ergora/definition_bundles.py)。只调整角色、专长、已有后端选择、图的串并行关系、Skill和上下文时，优先使用[定义编辑／修订](../AGENT_DEFINITIONS.md)与[工作流组合](../WORKFLOW_DEFINITIONS.md)，无需修改Python。

已发布ID／版本／摘要和manifest是不可变合同。改动产生明确新包版本，并更新新根引用／catalog；保留旧包、旧runtime路由与旧冻结输入。完整包含正文、Skill的全部文件、普通附件、目录和执行位，按原preview／accepted candidate／publish核身份。复用`DefinitionLibrary`与`asset_trees`，不再实现另一套复制／摘要／发布器。

子实例读所有祖先的Skill和上下文，权限逐级收窄；增加资料不产生工具或网络授权。追加资源需要提高权限时，同时调整必要父级和子级并重新预览，不能绕过父模板。重名Skill、路径、附件及容量由原编译和资源owner验证。仓库`AGENTS.md`只指导源码协作，不会自动变成模板的runtime grant、MCP或资源。

新增preset沿[既有冻结／安装回归](../../tests/test_presets.py)保护旧定义与新包完整性；编译变化沿[组合测试](../../tests/test_workflow_definitions.py)验证实际继承／引用／图消费者。单叶`prepare/run-input`不会自动运行前驱或收集端口；只有正式runtime明确支持的图形才能声明可执行。普通提案不变成正式候选批准。

## 配置和持久格式

[components](../../src/ergora/components.py)读取组件元数据；[bindings](../../src/ergora/bindings.py)核本族绑定，[projects](../../src/ergora/projects.py)拥有项目修订；正式项目登记与原配置投影由[registrations](../../src/ergora/registrations.py)持有。新增可配置变项需说明默认／旧缺省语义和实际读取者，不能为了测试把有效配置锁成某个默认值。

结构校验使用[contracts](../../src/ergora/contracts.py)及相应版本schema，跨字段、内容身份和生命周期约束留在本域owner。定义编辑的JSON／YAML使用原严格转换器；YAML是定义的输入形式，不表示可执行Python recipe，也不授权任意import。二进制附件保留原字节；摘要算法、canonical JSON、原始文件SHA、执行位和完整Git OID各沿原合同，不能统一成一种“通用hash”。密钥只用环境变量引用，不写配置快照、提示、报告或示例。

SQLite只经[State](../../src/ergora/state.py)及领域事务；变更持久语义时判断schema版本／旧writer隔离、备份、恢复和回退。索引库、原意图及外部训练记录还有各自文件合同，不能用SQLite迁移替它们做隐式重写。沿[迁移](../../tests/test_state_migrations.py)、[备份](../../tests/test_state_backups.py)和相应schema／领域接缝检查真实兼容；增加一个普通配置字段不自动意味着新建表或迁移全部历史。

## 执行和证据

[tasks](../../src/ergora/tasks.py)和[training](../../src/ergora/training.py)提供应用入口；原生操作进程装载所选注册配置。按版本的[WorkflowInput](../../src/ergora/reference_inputs.py)与原Temporal、executor、job、process及budget owner负责执行／取消／恢复。先沿[当前架构](current.md)和[reference边界](reference-boundary.md)找到具体owner；UI、CLI和新提案模板不持有第二套运行状态。

新增外部操作保留attempt-before-send和原ID／完整意图／receipt身份。丢回复表示unknown，应先沿原run/history对账；不能因为重启、当前配置变化或没有成功回执就重发。修改预算时核跨阶段、恢复、进程后代停止与取消，不能只约束单次模型调用。沿对应`test_task_*`、`test_budget_*`或`test_training_*`选择含这些状态转换的已有接缝。

训练的manifest／baseline／runner、比较门禁、质量约束、归档和精确批准仍归原owner；[多轮索引](../../src/ergora/training_rounds.py)只链接原观察，不执行优化、推进baseline或授予批准。流程图、kernel设计和测量建议不等于实际执行。kernel评估在总提案路径中保留，允许无需kernel修改。新性能主张必须绑定原baseline／candidate、固定工作负载与质量oracle、环境、成对原数据／测量窗口和收益不确定性；CPU合同不能验收真实GPU或训练质量。

本仓库不拥有目标训练框架的optimizer、model、dataset、loss或forward实现。对目标项目开发／重构时，先识别其原生组件构造与训练／checkpoint调用，再在**实际组件目录**补局部协议：允许扩展的接口与配置、张量／样本／mask／归一／状态义务、禁止隐式改变的算法或数据语义、调用／资源／恢复、最小数值／梯度／并行检查及已有示例／基类位置。协议写进目标项目自身文档和目录；Ergora模板不会自动生成它，更不会直接修改未授权的业务仓库。

设计参照见[固定研究的具体接口](../research/2026-11-15-iterative-optimization-architecture.md#可替换组件的具体源码接口)：TorchTitan局部typed构造和有限作用域替换、Bridge forward callable、slime最小函数扩展。选择与目标栈一致的实际接缝，保留其归一、通信、参数及恢复义务；Bridge已deprecated的数据兼容ABC不作为新接口范本。这里借鉴职责分界，不引入生产trainer依赖。

## 改进和可选工具

记忆的有效期／修订归[memory](../../src/ergora/memory.py)，Skill内容／head归[skill_assets](../../src/ergora/skill_assets.py)，可信suite与评价归[evaluation](../../src/ergora/evaluation.py)，生成和候选导出归[retrospectives](../../src/ergora/retrospectives.py)。资料选择及首次冻结归[task_context](../../src/ergora/task_context.py)，恢复使用原冻结输入。候选生成、静态检查、真实评价、明确采用和回退是不同操作，不能由生成器改可信suite或把当前head替换进历史任务。

GEPA文本搜索、研究来源、镜像记忆和原生kernel工具分别由`optimization`、`research`／`scheduling`、`memory`、`kernel`拥有实际选择和生命周期。这些领域并未全部统一成同一ABC／插件总线。先核现有支持范围和真实消费者；需要多实现接缝时在本族立片，不在调度层增加所有工具的总分派。可选工具声明、安装、原生身份、认证、支持操作和实际执行分别报告；不可用就说明具体缺口，不假装功能成功。

## 交互入口

[CLI](../../src/ergora/cli.py)和[HTTP](../../src/ergora/web.py)只解析传输输入并调用同一用例。领域身份／权限／评分／发布和恢复留在owner，页面不复制这些状态机。`data/console`沿现有view接口组织；schema／组件目录已能驱动的字段优先复用元数据，不再硬编码一份选项表。

页面异步读取保留项目、控制目录、view生命周期和选择代际；迟到响应不能覆盖新选择。变更请求显式提交，失败／unknown不自动重试；同源及请求头合同保持。读索引、读完整正文、下载和实际运行各自显示真实覆盖。UI协议变化选原HTTP／DOM接缝，真实布局／交互问题再用浏览器，不为文字调整新增模型测试。

## 脚本和检查

安装／升级沿[scripts](../../scripts)的现有入口、固定工具身份和[安装手册](../USAGE.md)。参数、路径、空格、平台选择、旧环境保持与原意图恢复都属于实际接口；子进程使用argv，密钥仅继承环境引用。只有Linux／WSL2支持的执行不能标作Windows原生，当前容器边界不能标作Agent间OS隔离。

根据所改行为选[现有测试](../../tests)和[scripts/ci/run.py](../../scripts/ci/run.py)中的显式分组。新增文件确有独立接缝时再登记[Linux分组](../../scripts/ci/linux-groups.json)；不要为一项功能新建重复CI job。只为可能静默连错身份、丢结果、错误复发、恢复／资源／并发失效补最小回归；已由普通执行清楚暴露的错误、提示措辞和复制实现的断言不增加矩阵。删除测试先指出其独特风险由哪个实际接缝接住。

需要确认安装行为时构建并安装新的非editable wheel，确认实际导入`site-packages`，再运行相应原测试；源码通过与安装通过分别记录。纯文档或机械修改检查相关链接／格式／完整差异，不重复无变化的模型、训练或全量回归。最后按根规则更新计划／交付，使用自身原模板和新的独立reviewer，保留精确源码／配置／产物与未验范围；新候选只由自己的适用CI认证。
