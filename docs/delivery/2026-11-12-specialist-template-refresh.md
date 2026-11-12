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

最新要求已同步到计划：最初列举的七方向不作为固定划分，按官方Skill Reference拆分纵向职责；完成后增加横向架构设计、端到端kernel及跨域诊断／实验／独立评价研究，形成技术方向与agent职责的多对多矩阵。R1 kernel、R2量化、R3通信独立报告已完成；R4并行策略、R5显存继续，余项按并发容量分批。当前未因研究结论修改产品或宣称硬件实测。

[分类说明](../research/2026-11-12-optimization-taxonomy.md)已逐组对应索引的Getting Started、Adding Model Support、Performance Techniques、Cluster & Debugging，另标kernel／低精度补充来源和MoE跨域场景。保留现有Agent多职能／多专长及精确引用，不为研究新建一套运行语言；真正子流程执行缺口交D1单独验收。

## U2 实际日常入口验收

通过真实日常启动器、隔离状态与新建本地Git夹具运行43条命令，全部退出0，累计命令22.21秒；52项检查通过。三个preset各自安装和重复导入完全相同，仍明确不授权执行；显式grant的preview、完整manifest、离线叶input及摘要核验通过。各叶继承资料正文在完整prompt内，保留root来源；六次text-only／task-mcp的Codex准入均无模型调用，回退理由显式记录，不是双后端成功。

三个冻结参考模板可复制。通过升级后包内正式编译器，治理与大型变更两个官方例子在源码工作区之外生成原task spec，task_type正确；未把训练提案当作开发合同，也未执行六阶段、workflow ports或审批。原283冻结文件再次核验通过。

真实CLI启动页面并通过10次HTTP200：入口、bootstrap、preset、agent库、安装配置、OpenAPI及入口引用的四件静态资源。项目来自隔离夹具；没有重做完整浏览器交互矩阵。所属server已终止／wait回收、端口关闭，Agent runs列表为空。没有SaaS业务写、模型或GPU调用。

原命令、逐条stdout／stderr、10份HTTP正文与摘要、server输出和52项投影保存在私有`local-upgrade/journey-r1/`。本轮产品未变，不重复H1已过189测试或模型审查；U1/U2原件独立验收另行进行，不提前记录为完成。

## U0 前片精确交付

H1原独立评审已从官方run／两job原HTML及receipt重算身份、独立解析状态和七件步骤，确认产品`5ab6d350024de8515487d0bedb3b950be60ac867`自己的CI43170918496为Success，Linux三／Windows四必要步骤均success／completed。[原终核](2026-11-12-harness-probes-review.md#自己的-ci-与精确交付终结)已记录，H1精确交付终结。匿名API／独立Ref403、导航404、早期In progress和私有解析记账失败原件保持；没有新网络请求或全日志下载声明。U0不重跑已核产品、模型或CI，不关闭H2／H3。
