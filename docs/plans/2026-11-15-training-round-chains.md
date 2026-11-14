# Q4.1：不可变的多轮优化证据索引

日期：2026-11-15。固定基线 `eadabc0441991a02acc06e17efd8d6c16b7d9d27`，承接[Q总计划](2026-11-15-domain-review-optimization-quality.md)和[按瓶颈提案路径](2026-11-15-training-bottleneck-path.md)。本片开始时产品638，Q3.3已普通发布、自己的CI另跟踪；不得用本片工作树认证前片。先写本计划，再改实现。

## 问题与最小边界

原training owner已保存每次experiment、manifest、执行结果、negative result、accepted archive及批准投递；缺少一个能把多次结果连起来、区分初始锚点和每轮实际比较对象的持久索引。不能为了记录轮次另建实验数据库、指标判定器、调度器或批准系统。

首个增量是操作者显式选择原实验后生成的新只读索引目录。它保存原观察的完整JSON值、原文件SHA／归档引用、每轮前驱身份及明确标为未验证的变化／后继瓶颈注释。原始日志和大trace仍在原存储，索引不能代替备份或宣称全部artifact已读。失败、无收益、未接受和未知结果必须能记录，不能只收通过门禁的结果。

本片不执行优化、训练、候选采用或baseline迁移。现有原生registry仍不允许隐式推进baseline；初始锚点与本轮比较对象分别存储，即使它们暂时相同。不得从不同比较推算累计收益。kernel专家继续由原v3提案路径保留，本索引不跳过或替代专家。

## 复用与接口

- `training.inspect`／`reference._training_records`：原manifest／spec／request／result／gate／negative result及原文件身份，包含未通过结果。
- `training.evidence`：原accepted archive、manifest／baseline／comparator／artifact索引及精确关联，保留`not_read`等覆盖范围。
- `training.submission`与`training.approval`：只读原本地投递记录。只有原已提交运行才读取其原批准状态；未提交或unknown明确不评价批准，不把门禁或票据当当前授权。采集可能需要原`temporal` extra，但不查询服务；离线读索引只需核心安装。
- `contracts`／`definition_bundles.parse_json`／`asset_trees.publish_directory`：严格格式、重复键拒绝及新目录原子不覆盖发布。复用原进程／路径／资源限制，283参考与state schema保持。
- 新的训练领域索引owner只隐藏索引格式、链接验证和采集组合；CLI调用该owner，不把训练实现移入CLI或新增通用插件层。

拟提供 `training rounds-create PROJECT --definition FILE --directory NEW` 和 `training rounds-read DIRECTORY`。输入JSON选择实验和注释；扩展时显式给旧目录与完整SHA，在新目录保留全部旧轮原值和新前驱链接，不重新观察或覆盖旧轮。读取能离线验证内部链接和外部期望SHA，但不认证来源、不重算统计、不证明当前运行或当前授权。格式细节随真实消费者固定在本片schema／手册，不能先称已支持。

## 可验收步骤

|步骤|证据与完成条件|当前状态|
|---|---|---|
|Q4.1a owner与持久格式|沿上述真实调用路径，固定初始锚点／实际比较／原观察／前驱链接／注释与覆盖边界；无第二实验或批准权威|已实现独立只读索引owner和v1 schema，已独立审查|
|Q4.1b CLI与离线读取|新目录不覆盖，显式扩展保持旧轮；篡改／错误项目／重复原实验／不匹配原绑定可见拒绝；unknown与失败不升级为通过|已实现两CLI、严格JSON、固定前缀扩展及离线核对；接缝回归与原旅程已验，lost-ack回归已验|
|Q4.1c 原安装合同旅程|至少两份独立原结果含失败或无收益；保存初始与实际比较、注释、原数据／报告引用及批准事实；重启读回相同索引，原件不变。CPU合成合同与真实训练明确分开|已跑两次刻意exit7／9的原CPU executor失败、18命令／121原件保持；另只读原C3三运行／合成归档及原requested批准投递，重启读回不变；无新服务／训练／GPU／收益主张|
|Q4.1d 审查与发布|相关原回归与必要接缝测试、独立非editable安装／283参考、实际CLI、自身原模板、新fresh-context独立两轴；普通发布和自己的适用CI|r1独立安装640逐字／283参考、安装60项已过；扩大原submission及lost-ack接缝回归74通过／128.84秒；自身原结构模板29.539秒approve；新独立本地两轴approve／开放0／0，另三接缝12.10秒通过；已普通发布750dd68、原固定发布补核两轴approve／开放0／0；自己的CI43629303623在途|

只为能静默连错实验、丢失旧轮或把拒绝结果提升为成功的风险补回归；不测试提示词或新增模型调用测试矩阵。采集到的多次原观察有各自覆盖范围；遇到原绑定／原文件身份冲突明确报错，不伪称原子实时快照。具体失败和修正逐步写入[交付记录](../delivery/2026-11-15-training-round-chains.md)。

Q4.2有界自动循环必须等本片人工证据旅程成立，再沿原生命周期／预算／取消／unknown恢复owner立片。真实B3／GPU、跨baseline推进和完整Forge的原条件保持；Q1.2、Q2.3、Q5及Q6继续在总计划跟踪。

## 精确交付闭合

固定750dd68ff2b1e41f6fe390d6a52e651bf41d5642自己的CI43629303623八job／30必要步骤成功，原独立CI终态补核两轴approve／开放0／0、片内剩余验收0。Q4.1精确交付完成；旧在途记载保留历史身份，当前状态见[交付闭合](../delivery/2026-11-15-training-round-chains.md#自己ci及精确交付闭合)。有界自动循环及真实训练仍另按Q4.2／B3条件实施。
