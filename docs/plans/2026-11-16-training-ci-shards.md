# 训练回归CI分组恢复

日期：2026-11-16。状态：b653完整新安装组2／5通过并收尾，四文件仅JSON再平衡及全节点核对已固定7ed77c9，最终独立复核中。原官方478候选已completed／cancelled，group5达到整个job的20分钟上限，其余native成功；完整远程逐项日志仍未取得。[只读调查](../delivery/2026-11-16-ci-training-shard-duration-analysis.md)将准确远端、各自本地候选与推测分开，新候选预算仍待自己的官方CI。

## 范围与基线

隔离实施基线`97a0bbfae9687c15927f1437a374cd070baf0a94`，分支`fix/training-ci-shards`；该基线包含尚待最终独立验收的服务片。此片仅迁移已有测试接缝与分组，不改产品、测试行为、参数、预算、断言、六组数量、runner、观察插件或workflow超时。新module负责独立controller／candidate root生命周期，复用原fixture，不建立第二测试框架。

实现文件限原`tests/test_training_submission.py`、新`tests/test_training_cycle_controller.py`与`scripts/ci/linux-groups.json`，确有fixture依赖问题先核真实调用再决定最小处置。不能导入测试函数造成重复收集；module级installation fixture次数及平台提前skip都要保留其明确语义。原服务片产品身份、新包与真实服务验收不由本片重新认证。

## 可验收节点

|节点|完成标准|状态|
|---|---|---|
|C0 调查与分界|固定原超时、成本原件、原有替代与独立接缝；不以删测试或增时限掩盖问题|完成，见调查|
|C1 最小迁移|同一函数／装饰器／参数／fixture闭包保持，接缝单向依赖，新增文件登记现有group2|固定5e953a1→b6538cf；37测试／75节点＋1专用helper原文迁移。后续四文件仅JSON再平衡已固定7ed77c9，见下节|
|C2 静态覆盖|沿原runner/plugin收集；仅归一迁移路径后，前后完整node multiset相等；六组唯一、存在、无漏项，原skip标记保持；不得只比较AST数量|af176→b653及JSON后继7ed77c9均保持真实Linux2227／Linux上Windows选集2172；fixture／skip／scope保持，六组节点349／285／399／415／315／464，真实Windows未运行|
|C3 安装行为与成本|同一新非editable产品安装下完整跑受影响Linux2／5组，保存JUnit、phase、退出与收尾；先读成本，不无依据重跑其它组。Windows受影响可移植／skip关系单独说明|b653两组完成：460＋537通过／1＋2原跳过，1520.84／2444.95秒、输入结束未变；245记录身份live0／unknown0。后继JSON没有本机新组合成绩，全部官方CI另验|
|C4 独立审查|新的fresh-context reviewer按实际diff、节点身份、fixture行为及真实运行需求／维护性两轴，关闭实证finding|最终7ed77c9需求／维护性两轴approve／开放0，允许导入普通发布；自身原结构模板最终Codex32.76秒approve，只认证supplied source；真实合入身份另核|
|C5 发布|固定、普通推送当前开发分支、核精确远端与候选自己的CI；两组均在原20分钟限制内完成才认证远端预算|待C4|

迁移只改变调度归属，不能保证总计算成本下降或Windows关键路径改善；远端没有phase／日志时不假定某个单测挂住。新代码／测试差异、输入身份及未验范围写所属交付；每步更新本页与主PLAN，状态记账不递归审查。

## 完整组观察后的有限再平衡

group2本机终态与[同候选逐文件成本](../delivery/2026-11-16-ci-training-shard-cost-followup.md)支持进一步只调现有JSON：task_cancellation从2到3、reference_executor从2到1、training_release从5到4、task_external_status从5到0；不再拆模块。先等b653完整group5退出、核冻结输入及记录身份收尾，才改变该固定工作树。

四次转移已固定`7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`，原plugin全节点、skip、fixture及六组归属保持。原b653完整2／5只作为同包、同测试正文与拆分接缝的行为证据。仅JSON后继没有本机新组组合／成本成绩，其全部官方CI负责最终组合执行、收尾和整个job时限。[fresh独立核查](../delivery/2026-11-16-training-ci-shards-final-review.md)未发现要求无差别本机重跑六组的具体session级耦合，最终正在复核group5与后继固定身份。若发生真实组合／fixture故障，再按失败接缝补最小验证；不能将旧组通过移记成新配置实测。
