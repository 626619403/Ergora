# 训练回归CI分组恢复

日期：2026-11-16。状态：最小迁移与两轮静态节点／fresh审查完成，Python3.11非editable全组2／5验收中。原官方478候选group5达到整个job的20分钟上限；全部run终态仍未知，完整远程日志不可用。[只读调查](../delivery/2026-11-16-ci-training-shard-duration-analysis.md)将远端事实、跨候选本地成本与推测分开；不以本地历史样本声称新候选已达标。

## 范围与基线

隔离实施基线`97a0bbfae9687c15927f1437a374cd070baf0a94`，分支`fix/training-ci-shards`；该基线包含尚待最终独立验收的服务片。此片仅迁移已有测试接缝与分组，不改产品、测试行为、参数、预算、断言、六组数量、runner、观察插件或workflow超时。新module负责独立controller／candidate root生命周期，复用原fixture，不建立第二测试框架。

实现文件限原`tests/test_training_submission.py`、新`tests/test_training_cycle_controller.py`与`scripts/ci/linux-groups.json`，确有fixture依赖问题先核真实调用再决定最小处置。不能导入测试函数造成重复收集；module级installation fixture次数及平台提前skip都要保留其明确语义。原服务片产品身份、新包与真实服务验收不由本片重新认证。

## 可验收节点

|节点|完成标准|状态|
|---|---|---|
|C0 调查与分界|固定原超时、成本原件、原有替代与独立接缝；不以删测试或增时限掩盖问题|完成，见调查|
|C1 最小迁移|同一函数／装饰器／参数／fixture闭包保持，接缝单向依赖，新增文件登记现有group2|固定5e953a1，合入原服务fixture后继得b6538cf；37测试／75节点＋1专用helper原文迁移|
|C2 静态覆盖|沿原runner/plugin收集；仅归一迁移路径后，前后完整node multiset相等；六组唯一、存在、无漏项，原skip标记保持；不得只比较AST数量|两轮通过：最新af176→b653真实Linux2227／Linux上Windows选集2172逐节点同一；fixture／marker／scope保持，真实Windows未运行|
|C3 安装行为与成本|同一新非editable产品安装下完整跑受影响Linux2／5组，保存JUnit、phase、退出与收尾；先读成本，不无依据重跑其它组。Windows受影响可移植／skip关系单独说明|运行中：Python3.11.15、新venv完整extras、wheel081aab45及663产品同一／283核验／依赖通过；b653固定输入，实际组2／5各独立进程|
|C4 独立审查|新的fresh-context reviewer按实际diff、节点身份、fixture行为及真实运行需求／维护性两轴，关闭实证finding|源码／静态fresh两轴approve／0；C3与固定合入证据待追加|
|C5 发布|固定、普通推送当前开发分支、核精确远端与候选自己的CI；两组均在原20分钟限制内完成才认证远端预算|待C4|

迁移只改变调度归属，不能保证总计算成本下降或Windows关键路径改善；远端没有phase／日志时不假定某个单测挂住。新代码／测试差异、输入身份及未验范围写所属交付；每步更新本页与主PLAN，状态记账不递归审查。
