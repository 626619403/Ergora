# F9b2：已准备训练实验的原生提交与对账

日期：2026-11-14。承接[F9b1实时读取](2026-11-14-training-runtime.md)与[F9总体计划](2026-11-14-training-workbench.md)。这是下一片设计；产品未实现，实施前固定F9b1提交与最终验收身份。原baseline／runner登记／prepare仍可先按完整训练手册执行；把这些写操作接到控制面另列后续小片，不隐含加入本片。

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
