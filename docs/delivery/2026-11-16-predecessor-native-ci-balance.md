# 前驱链与 native-v2 联合候选的 CI 再平衡

2026-11-16。实施基线 `3a57987dcca17395d7fd993843c28255013e2970`；实际收集产品为 `bc58be6781d35e7e4fbd54ad997df8a4743428a8`，包含 M5 r7。配置已由[新 fresh 独立审查](2026-11-16-predecessor-native-ci-balance-review.md)需求／维护性两轴 approve、finding 0，固定提交 `55dc51c`；尚未取得自己的官方 CI。这里的 collector 只证明收集与归属。

唯一产品配置修改为 `scripts/ci/linux-groups.json`：将四个完整既有文件 `test_training_preparation.py`、`test_task_budget.py`、`test_training_runner.py`、`test_training_runtime.py` 从 group5 移至 group1。保留六组、86 个唯一文件、全部测试正文、Windows all、Linux 20／Windows 30 分钟、原 job 和上传逻辑。

初始[有限成本调查](2026-11-16-predecessor-gates-ci-budget-analysis.md)只有 M5 r4 净新增 5 个节点，因此先提一个文件；最终又有 M5 的 3 个保护及 native 的 10 个节点，合计净新增 18。若干新增 native fault／链检查的本地观察约 278 秒，包含 fixture、子进程和 I/O，不能线性加到远端 job。旧公开 group5 为 17分31秒，账面余量149秒；group1为7分07秒。现在分配四个现成完整文件，利用目标组余量，不增加时限或拆分大 submission 套件。

旧指定 JUnit `ci-training-shards/installed-py311-r1/group-5/ci-results/junit.xml`：preparation 15／76.380秒、task_budget 12／48.461秒、runner 7／42.713秒；这三个文件正文与旧输入相同。runtime 旧26／46.019秒，而最终已有55节点，旧成本不代表其新总成本。禁止把四项相加当成可节省远端秒数；准确时长仍待新候选自己的官方 CI。

四文件的 fixture 通过原模块导入，function scope 的注册／项目／配置都在独立 tmp_path；module scope installation 用 tmp_path_factory 和原 managed venv 选择。runtime 的 SDK 模块替换由 monkeypatch 复原，Workflow 测试保留原独立环境及停服收尾。导入 fixture 不要求将来源模块的测试正文同组执行。没有发现依赖 group5 同进程的共享运行状态；收集成功不等于这些正文已在远端新组验证。

## 最终实际 collector 与 selector

私有原件 `.ergora/checks/predecessor-gates-ci-balance/final-native-r5-four-files/`：复制准确 855 个冻结源码／测试输入，只覆盖建议 JSON；实际使用 native-r5 已安装 SDK 的原 `scripts/ci/run.py --collect-only`，退出0／6.874秒，pytest 收集 2335 节点。原 PhaseLog selector 对组1／5真实重放，分别444／359节点。

|项目|最终结果|
|---|---|
|旧／新 JSON SHA256|`5995dfe1bd13235475fbbfd79b2ff51dc2065f302924e465e4fa1474456241df`／`8ffe961f3e4578485186d864430b9f93becf5eed81bea37338a6aa0015e685ab`|
|六组文件数|13／20／12／18／13／10；唯一86|
|六组节点数|354／444／410／453／315／359；总2335|
|同一最终输入对前一单文件配置|node multiset 完全相同，四完整文件全部5→1，其余归属保持|
|相对父留存实际2317|净增18（M5八／native十）；四已有节点改名映射后无保护删除|
|搬移文件节点|旧基线87、最终89；不是按更旧 JUnit 猜测的60／62|

`comparison.json` 保存完整新增集合和四个改名：ordinal3 完整链参数、source-sync 出生参数、旧 CLI 的显式 v1 后缀、旧 history 的 None 后缀。原始集合为移出4／移入22，不能称字面 node ID 全不变。该记录与 `collector-result.json`、`identity.json`、原 collector request／phases／stdout、855 项复制身份共同保存，不改写此前单文件候选或 r4 收集结果。

下一步：最终产品联合终审通过后与已审配置普通导入／推送，核准确远端和自己的官方八 job。在此之前没有测试正文、Windows、最终时长或官方成功认证；不重复无变化总批来替代正式 CI。
