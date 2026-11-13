# F9b2：已准备训练实验的原生提交与对账

日期：2026-11-14。承接[F9b1实时读取](2026-11-14-training-runtime.md)与[F9总体计划](2026-11-14-training-workbench.md)。实施基线 `106481a80abfd168f5b45fbba7381063505239d0`，F9b1本地出口及普通推送／精确Ref已验，自己的CI八job／30必要步骤成功且原结构轴终核通过；本片产品已实现，修后包／真实CPU／浏览器已验，CLI退出码补验、自身及最终独立两轴通过，开放0／0；普通发布与自己的CI待验。原baseline／runner登记／prepare仍可先按完整训练手册执行；把这些写操作接到控制面另列后续小片，不隐含加入本片。

## 所有权与待解决问题

现有 `perf_temporal.client start` 已使用原Experiment、workflow_id、REJECT_DUPLICATE、FAIL与单次工作流尝试；`agent_platform.training.prepare`已冻结manifest/spec/项目registry，`LocalTrainingAdapter`已负责幂等job与fence。缺口是控制面在发送之前记录意图／attempt、精确绑定确认、丢失回复后的原run归属核对。单纯进程退出或job文件存在不能证明这次提交已获确认。

不复制训练worker、队列、实验表、资源预留或批准。复用原CLI／SDK发送规则和原模型，控制面只保存操作意图与传输回执；路径在已选原执行state中，按项目／experiment／operation固定，不在SQLite增实验行。要复用现有core.write、file_lock和process owner，不能为此建通用任务执行框架。

## 可验收步骤

|步骤|行为|出口|
|---|---|---|
|1 预检与确认|已发布训练项目、精确project revision、已准备原Experiment／manifest SHA、同repo可信runner、当前baseline和未fence；CLI与页面显式确认精确SHA，不把只读历史baseline漂移的可见性当可提交许可|无效输入在发送前失败；旧项目／模板／配置／manifest／runner变化不借活动头重解释旧意图|
|2 原意图／attempt|冻结control home、registration／execution、原spec及manifest绑定；拿原文件锁后重读；发送前持久attempt并标unknown。用原workflow start加同一意图摘要的native memo，不扩大原重试策略|没有attempt不认发送；attempt后无回执不得start重发，进程超时／强制停止留下unknown；不以新实验ID“恢复”|
|3 原生提交|选择如何包装原client start；优先保留原CLI处理和SDK策略，通过局部连接／发送接缝加checkpoint，不把其所有操作复制到控制面。发送前若存在其他actor启动的同名run，拒绝认领|start只有一次；原Experiment完整输入不变，native memo足以在回复丢失后证明操作归属；重复／冲突有原件|
|4 显式对账|原workflow ID查询，固定实际run并核完整历史输入、原memo／意图、原binding；只有完全相同原意图才补回执。NOT_FOUND不等于可清attempt重发；冲突／网络／历史缺失保持未知或拒绝|请求已接收但回复丢失的原run能找回；预先存在的外部run不能冒充本次提交；不更改实验／调度／批准状态|
|5 接口与页面|共享training应用入口供CLI／HTTP；展示prepared／unknown／submitted及原run，实时领域状态仍走F9b1；页面先展示确认材料，再显式操作／对账，独立生命周期|默认导航不发送，双击／陈旧revision／迟到结果不会重复start或跨项目覆盖；失败可读且保留原原因|

F9b1新原输入核验需要被提交／对账实际复用时，在原训练runtime Module内部收拢lookup Interface；只为两个真实生产调用者深化，不提前给所有Task／Experiment建立泛化继承层。原开发六阶段submission仍属自己的owner。

## 验证与后续

使用真实SDK的有界Service替身注入请求被接收后失联、重复、原输入／memo冲突、原run缺失与timeout；用新noneditable包实际CPU Temporal验原prepared→提交→原ID查询→回复丢失对账。保留操作前后原registry／manifest、实际start次数、原history／memo／回执与停止证据；页面核确认和迟到行为。再用原结构审查模板及新的fresh-context需求／结构两轴，普通发布并核自己的CI，不借F9a／F9b1。

取消／停止对账另立F9b3；baseline／runner／prepare接入另立F9b4；原evidence SHA批准／票据归F9c，真实GPU收益归F9d／B3。不能因CPU旅程通过而关闭它们。当前授权沿原计划持续开发、普通推送开发分支；不自动合main或采用训练候选。

## 实施接缝细化

- 仅新增训练提交owner，不复用依赖Task creation的`_Submission`；其输入和批准规则不同。应用层沿原SQLite短写保留revision，仅本地prepare持有；网络阶段按已保存意图与原文件锁进行，不持有控制数据库锁。
- 原reference训练reader将同一算法收拢为可返回值的私有Interface，离线子进程与提交预检两个真实消费者共用；SDK lookup在原runtime Module深化为固定输入／run查询，两处实际复用。复用原safe_file／read_raw／core.write／file_lock。
- intent保存完整原spec、manifest、baseline／runner快照及原文件摘要、home／registration／execution／repo；先核已准备且未有job／fence／旧执行记录，原Git提交存在、当前baseline／runner和原comparator一致。checkpoint前重读；已attempt的对账沿原冻结spec，不把后来的baseline、runner或取消结果重解释为新提交许可。
- 原`perf_temporal.client.main`仍解析原start、load_experiment、connect并决定REJECT_DUPLICATE／FAIL／single-attempt。只在该独立进程包裹connect／start，核完整输入／参数、保存attempt并加入意图memo；捕获原stdout与run回执，不重写调度或改变原参考283文件。
- 未发送的prepared意图可显式`resume-start`继续；一旦有attempt只lookup原workflow，固定run并核首历史完整输入与memo。NOT_FOUND／RPC／冲突不清attempt、不自动重发。普通start重复返回原本地状态。

## 当前实施检查点

已完成步骤1–5的源码实现。r1安装65通过／4跳过；r3修后32通过；r4并发读序13通过；r5含load竞态补读的三定向安装检查通过。真实CPU原驱动等待页面超时，保留失败后恢复同SQLite／原run；四实际history／完整输入／memo／唯一run及原22件保持已核，控制Outcome保留两个CANCEL_UNCONFIRMED和两个CANCELLED，原执行器均CANCELLED且无训练启动。页面修复、错误SHA、双击、两迟到跨项目场景、三视口与收尾已验；不同包轮次范围见[交付](../delivery/2026-11-14-training-submission.md)。

独立两轴及自身模板已发现并修复容量、来源恢复依赖、迟到详情、并发发布读序和CLI退出码问题。当前产品最后变动仅CLI未确认／拒绝退出1及原失败场景断言；r6最终包565／两RECORD／283及5项CLI受影响安装检查已过；自身最终原模板approve；原两轴最终本地补核通过、开放0／0；普通发布与自己的CI待完成。没有提前关闭F9b3／F9b4／F9c或真实GPU。
