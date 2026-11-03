# V3：过时 CI 运行取消

2026-11-03。依据[测试成本计划](../plans/2026-11-03-verification-efficiency.md)及[独立审计](2026-11-03-verification-redundancy-review.md)。这是下一切片的合同记录，工作流尚未修改；先完成V1交付及V2定向检查/独立源码审查。

## 已核事实与最小选择

当前Portability同时监听分支push、pull_request和手动事件，没有concurrency。只读读取公开的当前分支Actions首结果页，保存原HTML及SHA：`.ergora/checks/verification-ci-scheduling/actions-before.html/json`，观察到25项运行，全部为pushed；此范围不是仓库所有历史，也没有证明实际push/PR重复的频率或浪费量。因此本轮保留触发职责，不因配置同时允许两种事件就删除分支或PR检查。

最小改动只在既有`.github/workflows/portability.yml`增加workflow级concurrency及cancel-in-progress。组按workflow、event_name以及PR号（PR事件）或完整ref（push/手动事件）区分；同类事件同一分支/PR的旧候选可以取消，push、PR合并结果与手动事件不互相取消。不同PR号与不同ref值按GitHub的组名语义隔离；官方组名比较不区分大小写，因此仅大小写不同的分支会共组，不宣称服务提供严格区分大小写的锁。配置遵循已实际读取的[GitHub工作流并发文档](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)，来源与SHA保留于`github-concurrency-doc.json/html`。

不改测试命令、矩阵、超时、依赖、安装与冻结身份门禁；不增加定时任务、外部服务或重复一套CI。PR合并树与分支HEAD仍有不同验收价值。最新候选的Windows和Ubuntu必需检查均须完成。

## 验收边界

核YAML结构、最小diff及各事件组的实际表达式；保留原矩阵/步骤/触发身份。新独立审查者核事件隔离和取消范围；推送精确候选后核两OS完整CI及远端SHA。若没有自然重叠的在途候选，明确未进行真实取消演练，不为演练额外触发一套即将废弃的完整回归，也不宣称测得runner分钟收益。

实现、检查、独立审查及精确CI均待完成；实施基线在V2独立源码提交后登记；V2与V3保留各自审查及提交，共同最终候选仅执行一次完整两OS矩阵，并分别核文件身份。后续继续F3.4b2明确终态外部对账。
