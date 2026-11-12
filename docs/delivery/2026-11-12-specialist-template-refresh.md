# 专家模板重整交付记录

[计划](../plans/2026-11-12-specialist-template-refresh.md)；基线 `c38227747b002ba4137f65a4982de51ce247773e`，产品基线 `5ab6d350024de8515487d0bedb3b950be60ac867`。

## 初始核对

已读 AGENTS／PLAN、当前 Git、H1 计划／交付、原 preset 与组合／正式执行边界。工作分支 `refactor/architecture-foundations`，开始时工作区干净。三个领域 preset 及其专长定义存在；训练 preset 的 runtime 为 proposal-leaves，不能据此称完整训练实验自动化。原六阶段由正式运行所有者执行，组合图当前仅承接所支持的工作／审查协议，通用可嵌套六阶段节点仍待设计。

用户最新说明采用 NVIDIA 官方 skills 索引校准优化方向，不要求整套导入。按方向研究单体 agent、工具与完整流程，分别判断接专家或子模板；研究及安装／执行结果单独登记。本片尚未修改产品或运行新增模板。

## U1 日常安装升级

升级前已核实际启动器、解释器、依赖清单和状态位置；控制台未运行，默认统一状态目录不存在，未迁移或覆盖其他项目与参考运行数据。先完整归档旧应用环境：5,572成员、32,657,016字节，SHA256为`cde8320bc5d49ac8345e9d4e1756bf2598173b588d6343cffbfc1e547a0d3f6f`。私有备份及恢复位置由`local-upgrade/backup.json`记录。回退时先停止相关进程并保留／移走新环境，再完整恢复旧环境，不能把旧包覆盖到新包上。

使用H1已核发行包及原选配`web,temporal,gepa,task-mcp`离线升级既有home应用环境；启动器链接保持。升级后38分发包，452产品文件逐字与产品基线`5ab6d35`一致，462行安装RECORD核验通过，组合／来源任务／回写模块实际存在。分发版本仍为`0.2.0`，因此本次升级身份以产品提交和文件核验为准，不能只凭版本号判断。实际日常CLI的`reference verify`通过283文件核验，组合／模板／项目帮助与配置列表已可用。

原始身份、备份、安装输出、前后依赖及核验原件保存在私有`.ergora/checks/specialist-template-refresh/local-upgrade/`；机器绝对路径不进入公开手册。U2继续通过实际日常启动器在独立验收状态中验证，尚未运行新增模型或GPU工作。

## 用户追加与研究范围

最新要求已同步到计划：最初列举的七方向不作为固定划分，按官方Skill Reference拆分纵向职责；完成后增加横向架构设计、端到端kernel及跨域诊断／实验／独立评价研究，形成技术方向与agent职责的多对多矩阵。R1–R10均已完成；R8作者报告另经新fresh-context事实／设计审查，两个P2最小修正后开放0／0。X1架构／系统、X2 kernel端到端、X3诊断／实验已按并发容量开始。当前未因研究结论修改产品或宣称硬件实测。

[分类说明](../research/2026-11-12-optimization-taxonomy.md)已逐组对应索引的Getting Started、Adding Model Support、Performance Techniques、Cluster & Debugging，另标kernel／低精度补充来源和MoE跨域场景。保留现有Agent多职能／多专长及精确引用，不为研究新建一套运行语言；真正子流程执行缺口交D1单独验收。

## U2 实际日常入口验收

通过真实日常启动器、隔离状态与新建本地Git夹具运行43条命令，全部退出0，累计命令22.21秒；52项检查通过。三个preset各自安装和重复导入完全相同，仍明确不授权执行；显式grant的preview、完整manifest、离线叶input及摘要核验通过。各叶继承资料正文在完整prompt内，保留root来源；六次text-only／task-mcp的Codex准入均无模型调用，回退理由显式记录，不是双后端成功。

三个冻结参考模板可复制。通过升级后包内正式编译器，治理与大型变更两个官方例子在源码工作区之外生成原task spec，task_type正确；未把训练提案当作开发合同，也未执行六阶段、workflow ports或审批。原283冻结文件再次核验通过。

真实CLI启动页面并通过10次HTTP200：入口、bootstrap、preset、agent库、安装配置、OpenAPI及入口引用的四件静态资源。项目来自隔离夹具；没有重做完整浏览器交互矩阵。所属server已终止／wait回收、端口关闭，Agent runs列表为空。没有SaaS业务写、模型或GPU调用。

原命令、逐条stdout／stderr、10份HTTP正文与摘要、server输出和52项投影保存在私有`local-upgrade/journey-r1/`。本轮产品未变，不重复H1已过189测试或模型审查；U1/U2原件独立验收另行进行，不提前记录为完成。

新的fresh-context评审已[完成U1/U2独立验收](2026-11-12-specialist-installation-review.md)，Spec／Standards开放0／0。其独立重算备份及安装RECORD、452产品、283冻结、三图全部16叶的祖先材料／完整树／prompt、六次实际准入、两个编译合同及10份HTTP；另核原server退出／PID无存活／端口关闭、只读SQLite零run及夹具干净，没有重跑旅程或网络。U1/U2范围内验收完成；未恢复旧环境、未全盘比较机器历史数据，未把HTTP入口冒称浏览器全矩阵或完整六阶段／GPU／新专家模板通过。

## U0 前片精确交付

H1原独立评审已从官方run／两job原HTML及receipt重算身份、独立解析状态和七件步骤，确认产品`5ab6d350024de8515487d0bedb3b950be60ac867`自己的CI43170918496为Success，Linux三／Windows四必要步骤均success／completed。[原终核](2026-11-12-harness-probes-review.md#自己的-ci-与精确交付终结)已记录，H1精确交付终结。匿名API／独立Ref403、导航404、早期In progress和私有解析记账失败原件保持；没有新网络请求或全日志下载声明。U0不重跑已核产品、模型或CI，不关闭H2／H3。

## D0前置：已核产品调用面

以下为当前源码事实，不是新方案已实现：

- [Agent定义](../../src/ergora/agent_definitions.py)已允许同一精确定义具备多个职能和专长标签，由现有后端能力逐职能准入；权限在工作流实例及父链中约束。因此纵向研究不要求每个技术项新增一个职能或一个基类。
- [工作流定义](../../src/ergora/workflow_definitions.py)和[v2格式](../../src/ergora/data/schemas/workflow-definition-v2.json)已支持嵌套Agent／Workflow引用和all-join。现有格式没有原生外部流程调用节点；新增一个上游系统的名字不会自动得到它的运行能力。
- [单叶调用](../../src/ergora/agent_runs.py)复用原快照、MCP、结果和进程所有者，独立运行选中叶子；不执行图前驱／端口。独立训练提案叶不能据此变成完整训练流程。
- [StageDAG／WorkDelivery](../../src/ergora/review_dags.py)是原运行图的阶段数据投影，正式消费者约束工作实现者与只读审查者，并将原unit一对一分配；不是任意混合职能图运行器。
- [Forge原生campaign](../../src/ergora/kernel.py)已有prepare／run／status、固定版本、native ID和未知对账，适合作为首个真实子流程消费者；不可重写其内部teacher／student循环或静默升级绑定。
- [WorkflowInput及原workflow](../../src/ergora/reference_inputs.py)拥有六阶段的版本路由、创建／批准／运行身份；要将六阶段作为可复用子模板，应设计通往该所有者的Interface，保留原task/run、计划批准与可信候选，不能仅用六个Agent节点替代。

D1待纵横向研究和D0决定后再细分实现；不提前引入第二调度、账本或只有一层转发的通用插件框架。

## 持久研究检查点

文档检查点`42902bbe1af59059b287a38f0c9efa51a72dca4b`已普通推送至原开发分支，退出0；既有SSH只读Ref核同完整SHA。包含U0收口、U1/U2作者验收、方向分类及R1–R3报告，共12件Markdown，210本地目标／6个已加载秘密值／私有路径与空白检查issue0。全部路径属于既有Portability文档忽略范围，没有新产品CI；不借H1 CI证明新研究或新模板能力。此检查点明确保留U1/U2独立验收和剩余纵横向研究待做，后到的报告另行保存／推送。

## 纵向研究收口与横向交接

R4–R10分别补齐[并行分片](../research/2026-11-12-optimization-parallelism-agents.md)、[显存与卸载](../research/2026-11-12-optimization-memory-agents.md)、[执行图／数据调度](../research/2026-11-12-optimization-execution-graph-agents.md)、[诊断与测量](../research/2026-11-12-optimization-profiling-agents.md)、[集群与恢复](../research/2026-11-12-optimization-cluster-agents.md)、[模型／配方](../research/2026-11-12-optimization-model-recipe-agents.md)和[重构／六阶段](../research/2026-11-12-refactoring-workflow-agents.md)。各文分别固定公开版本、原生接口、许可和未验范围；来源读取与作者结果没有冒称本项目硬件实测。

需要在D0处理的共同问题：多个Skill的开关／导入／支持表已滞后于同快照实际源码；不同项目的独立latest存在Python和Core／TE配套冲突；native exit0、缓存、schema或内部judge不等于正确性、质量或收益通过。原生系统的teacher／student／planner等每个内部会话如何完整接收父资料和权限，是实际接入门槛，不能靠包装CLI解决。具体建议须经X1–X3的跨域控制和交接证据汇总后定稿，不按纵向目录直接生成一套互斥agent类。

[R8新独立审查](2026-11-12-cluster-research-review.md)首审指出Slurm主Skill／复制模板启动形态未展开、内部模型缺少可拒绝的继承／权限／预算门禁。作者补固定模板引用、参数化rank生成者／共享路径合同，以及deterministic-only首片和不满足父合同的模型流程unsupported。原评审复核最终研究稿`d9419364dc0c2c25876d715dd2640a370672535d2a8aef5755374476fb799b9a`通过，R8-SP1／SP2关闭、Spec／Standards开放0／0；首稿身份和原finding保持。复核没有新增网络、安装或上游执行，不是D0、X或产品适配通过。

第二文档检查点限定U1/U2新独立验收、R4–R10、R8独立审查和三件进度文档，共12件Markdown，不包含仍在编写的X报告。首轮静态指出审查报告12个相对链接含`:行号`而指向不存在文件，已仅机械修正目标、保留标签／正文／判词及原报告前像；暂存校验另指出R7末尾多余空行，已机械修正，尚未运行commit。两项原失败保持；先前空白检查未覆盖当时未跟踪的新文件，不能当作完整暂存候选通过。完整候选的12文件／132本地目标／6个已加载秘密值检查issue0，最终Git空白检查按暂存候选重新核验。此为文档范围，无产品、测试或CI变更；不重跑U1/U2旅程、H1模型或旧候选CI。
