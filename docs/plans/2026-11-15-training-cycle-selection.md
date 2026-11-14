# Q4.2a2：有限训练候选与预算策略冻结

日期：2026-11-15。承接[Q4.2总计划](2026-11-15-bounded-training-cycles.md)和[只读启动检查](2026-11-15-training-start-admission.md)。实施基线为a1精确交付`d3c90e751ee9257df36b74e57e8956d38bbde848`；其自己的CI和原独立终核已闭合。本片r2安装与本地两轴评审通过，普通发布／自己的CI待，**不提供自动循环**，不修改Kernel专家或既有v3优化路径。

## 最小可用行为

操作者明确选择有序、已准备且未投递的实验及各自完整manifest SHA，冻结为一个不可变本地输入。准备从原State读取完整project／revision／registration定义及预期注册文件，再只经原`training.check_start`收集训练观察，每个候选保留完整观察、spec／runner／baseline／源文件摘要。读回仅核目录、完整SHA、版本和内部关系，不读取当前项目／原训练目录，不需要SDK、服务、密钥或模型；离线读不能认证来源或重新授予准入。

生产入口是薄`training cycle-create`／`cycle-read` CLI；`training_cycles`隐藏本片配置输入／持久格式、收集与交叉关系，schema为`training-cycle-v1`。当前生产消费者是CLI，不把尚未实现的Temporal消费者算作已有复用。`training_rounds`继续拥有结果索引，`training`继续拥有实际准入／投递／证据／批准／停止。不把有限选择或预算策略写进新的SQLite运行表，不新增调度器、训练器、评分器或预算时钟。

第一版只冻结策略，不创建执行授权和起算时间。后续显式启动仍须核当前项目与所有原身份、创建一次不可续期的原始deadline并由Temporal保留；准备或离线读取不能重开预算。a1的观察不是预留，准备期间或准备后漂移仍由真正start边界拒绝。

## 输入和容量决定

|内容|本片约束与理由|
|---|---|
|候选|1–32个明确experiment ID／完整manifest SHA，顺序固定，同一实验不能重复。最大试次直接取选择数，不再提供一个可与列表冲突的重复计数参数|
|共同语义|同一初始baseline／workload及数据、初态、环境、验证合同、比较器、质量要求和性能政策；不能通过跨轮放宽门槛改变停止含义。每个候选的commit／config、track及allowed_changes仍完整保留，近似改动沿原门禁|
|预算|严格整数W=wall_seconds、C=cleanup_seconds、T=control_timeout_seconds；`1≤C<W`、`1≤T≤60`。T是传给原用例timeout的上限，后继执行须按剩余phase预算缩小或拒绝调用；不是整次用例的硬墙钟。只冻结必要关系，不借用单task的7天／模型次数上限，不要求W覆盖全部max_run之和，不把C≥cancel_wait或T与180秒activity窗口的关系当停止充分条件。费用／GPU小时不支持；策略通过不表示实际预算准入|
|完整冻结|普通目录内单个完整cycle.json，包含metadata／完整project及全部候选观察；实际最终UTF-8文件最多10,000,000字节，另沿原严格JSON的64层／100000值读取边界，超限在发布前明确拒绝，不截断。不覆盖已有目录，源文件与数据库保持|
|运行位置|首版仅原Linux／WSL2单协调主机和可达本地存储；完整保存control目录、项目修订／注册和execution位置。未来消费必须核完整SHA，裸路径不算冻结；异worker／host不能假设原文件或本地flock自动共享|
|Temporal传输|未来workflow／activity输入、返回值和异常均须受限，不能只缩小启动参数再返回完整计划／8MiB evidence。原owner本地核全文，传精确run／binding／evidence SHA、状态／覆盖及有完整SHA和原范围的本地快照引用，消费时核原件。a2不声称已验某个部署的容量，c前还需实际双向payload编码／history边界和worker注册验收|
|结果保存|原结果／失败／无收益材料继续留在原owner；原单份rounds索引32轮／10,000,000字节限制保持。后继须定义并验收每轮独立完整快照与受限引用、单轮／累计超限及快照发布失败的停止和原件保留，不能到最后才发现整份累计索引不可保存|

容量依据已经对照本机工具的公开版本：Temporal CLI 1.9.1搭载Server 1.32.0；其[固定源码默认值](https://github.com/temporalio/temporal/blob/v1.32.0/common/dynamicconfig/constants.go#L387)为blob error 2 MiB、warn 512 KiB，history error 50 MiB／51200事件、warn 10 MiB／10240事件。它们是该版本的默认设置，**不是当前或任意远端服务的实测限额**；开发server支持`--dynamic-config-value`覆盖。后续必须用实际受支持部署验证所选传输／历史策略，不能把这里的版本调查当成服务准入。只读源码调查原件保存在ignored验收目录，未启动服务。

## 可验收步骤

|步骤|完成条件|状态|
|---|---|---|
|S1 合同与owner|固定a1已发布基线、请求／完整输入版本、真实调用者、预算必要关系与容量拒绝；明确离线完整性不等于准入／来源认证|初版及修订设计复核两轴approve；原意见已落实为本版合同，独立实现审查另列|
|S2 原owner组合|沿原check_start逐个收集；同基线／语义、全部完整身份和项目修订一致；已有投递及漂移明确拒绝；不可变发布与离线SHA读回|r2已补齐离线完整性和内部关系并复用原注册投影；原R1／R2已由同一独立reviewer关闭|
|S3 最小接缝|复用原prepared／submission及rounds已有fixture，验完整读回／源保持、异合同、既有unknown、完整SHA／策略／源漂移和发布冲突；仅为原测试无法保护的可达风险补测试|补注册核对曾四失败；按原封套修正后八通过／35.61秒，原失败保留；源码验证不替代安装验收|
|S4 安装与实用|新非editable包逐字核身份／283参考；实际原owner准备至少两个公共CPU合同，冻结／离线三CLI且无训练派发；安装已有相关suite|r2 core／SDK645逐字／283、三CLI／47文件和DB保持；安装七suite148通过／304.32秒；原r1及红回归保留|
|S5 审查与发布|自身原结构模板、新fresh-context两轴；更新计划／逐步交付，普通推当前开发分支，自己的适用CI和精确终核|r2自身78.648秒approve，原fresh-context最终本地两轴approve／开放0／0，R1／R2关闭；普通发布／自己的CI及固定终核待|

完整project／registration及预期注册文件由State原记录提供；注册marker的control目录／project／definition SHA、各候选project／revision／binding／spec URI／runner和共同字段在新输入内交叉核对。原文件SHA保留其原字节含义，不把重新排序后的JSON摘要当作原文件摘要；整份cycle.json另取原始文件SHA。依然是逐个观察，不是所有外部文件的原子快照。

提交前停止、晚到RPC、注册漂移后的原运行停止、全executor生命周期和跨恢复预算仍是Q4.2b硬门槛。若候选后来被人工任务／另一循环投递，后继start必须核原意图与本次授权归属，不能仅凭相同manifest接管他人的运行。S2完成也不能开放自动循环；Q4.2c／d另有实际Temporal和完整CPU旅程，真实训练／GPU／收益继续按B3条件验收。逐步结果见[交付](../delivery/2026-11-15-training-cycle-selection.md)，设计依据见[原报告](../delivery/2026-11-15-training-cycle-selection-plan-review.md)。
