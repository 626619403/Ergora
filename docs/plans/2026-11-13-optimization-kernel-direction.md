# D2-B2i：独立 kernel 方向子模板

日期：2026-11-13。承接[专家计划](2026-11-13-specialist-presets.md#同事试用入口与剩余专家清单)，产品基线`d683c018344fb604be115a3ed2a02bd9d50d4eff`，开始时工作树清洁。B2h已普通推送并核作者完整Ref，其自己的发布独立补核／CI另行收口；本片先实现与本地验收，发布前核准该依赖。

## 范围与归属

新增`optimization-kernel`与`ergora-opt-kernel-proposal@1.0.0`。复用现有四叶提案形状及精确v2：analysis的design／profile、kernel、measurement的review。完整方向context由每叶继承；kernel手动接收两份完整原分析，measurement手动接收三份完整原前驱与真实实验材料。每次只运行选中叶，不引入图调度或原生执行。

资料覆盖真实operation／shape／stride／数值／梯度与wrapper、当前编译基线、关键路径与局部／整体测量、独立oracle、KDA／Forge／KernelAgent-Fuser／GEAK／AKG／robust-kbench各自调用面及限制。Forge固定adapter pin／native Claude协议／campaign身份保持；完整父材料、权限、总预算、恢复和实际后代停止仍属C2。原可信runner、原生搜索、独立评价及项目采用各有唯一所有者。

产品只加workflow／instructions／context三文件与catalog条目，原方向参数测试增加kernel并复用第四叶预期；同步README、两手册及计划／交付。保持548旧产品除catalog字节、22旧catalog条目、共享v2与283冻结文件。不安装／执行原生kernel工具，不改运行owner／backend／依赖，不建新Agent类、候选账本或搜索循环；实际GPU实验属B3。

## 来源与验收

复用[R1](../research/2026-11-12-optimization-kernel-agents.md)及[X2](../research/2026-11-12-horizontal-kernel-agents.md)21份固定原件920,972B，新研究请求0。十份R1已保存快照按其原索引／长度／SHA核准，十一份X2还核原HTTP200回执；两类来源身份分别保留，不把快照索引冒称新HTTP回执。KDA `acdd793…`、KernelAgent `e064717…`、GEAK `ec97e49…`、AKG `64b84b5…`、robust-kbench `078f5ba…`；Forge adapter `5030503…`与研究head `b2c8ae8…`分开。产品仅原创综合与固定链接，不复制上游代码／prompt或重新授权其资料。

|节点|验收结果|状态|
|---|---|---|
|I0 基线与来源|基线／分支／原资料身份及执行边界|完成|
|I1 定义与入口|只读四叶根、精确引用、catalog／原测试参数及两手册|已实现；548旧产品除catalog及22旧条目保持|
|I2 安装与兼容|noneditable wheel、source／installed及两RECORD／283、原preset suite|551产品／两RECORD／283与noneditable通过；原suite30通过／119.64秒|
|I3 实际交接|四真实task-MCP叶、完整UTF8资源、两处完整原前驱手动交接|四调用成功，23资源66,552B完整UTF8读取与两处完整原前驱通过；measurement保留request-changes，仅synthetic资料|
|I4 审查|自身原结构模板及新fresh-context需求／可维护性两轴，修正finding|自身29.578秒approve／五全文49,861B、新fresh-context完整原件／两轴通过，SP1/P3关闭、开放0／0|
|I5 发布|普通push、精确Git／远端Ref、本提交自己的CI与独立终核|41dd5aa已普通推送，作者完整SSH Ref／17Git及原独立发布补核通过；自己的CI43459951488八job／30必要步骤及原独立终核通过，精确交付终结|

Synthetic fixture检查：错误eager基线的4×、当前compiled的2×、条件Amdahl上限1.25×、wrapper反而慢20%、单forward／单shape／关闭dropout的生成PASS、缺梯度／strided／tail、Forge pin／协议混用、GEAK exit0却no_gain、AKG默认截断及lost-ack新ID重置预算。所有数值明确为假定，不是实测；这些只验方案与证据辨别，不能关闭真实工具／编译／GPU／质量／收益或原生嵌套。

每步写入[交付](../delivery/2026-11-13-optimization-kernel-direction.md)。随后B3先逐字段追溯原实验manifest，再按实际workload与授权运行；C2另验所有内部会话及原生生命周期。
