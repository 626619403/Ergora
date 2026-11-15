# 训练 CI 分组成本补充分析

日期：2026-11-16。本轮只读分析；唯一写入为本报告，没有执行测试、安装、网络请求、产品／测试／分组修改或提交。按 `ergora-codebase-quality` 的 `test-seams` 参考保留真实取消、恢复、进程回收接缝，不以删除场景或缩短预算改善成本。

结论：只移动 controller 到 group 2 的固定候选 **b6538cf 尚不能认证成本**。本机完整 group 2 已超过整个官方 job 的 1200 秒限制；仍在运行的 group 5 也已有超过 1600 秒的 phase 记录。现有 JSON 整文件重新分配仍有改善空间，不必再拆测试模块。建议的有限后续候选是下面四次文件转移；它们有同候选本机成本支持，但接收组和 group 5 最终成本尚未测量，不能承诺远端成功。主控决定是否实施；本报告不作评审结论。

## 准确候选与环境

|证据|候选／环境|能说明什么|
|---|---|---|
|官方 run 43737570677，attempt 1，已有 jobs API 原件|`478c98891522930817fa7005a8ac96e408f37230`；ubuntu-latest／Python 3.11，Windows 为 Python 3.12|旧分配的准确 job／step 成本与终态；不包含后来的服务产品和 controller 拆分|
|完整安装 group 2|`b6538cf0e5026f27c1c5983aa586926a666e4788` 测试／CI；本机 Python 3.11.15 非 editable 新环境、产品 wheel `081aab45`|新分配实际执行成本；不是 GitHub runner 成本|
|运行中的安装 group 5|同一 b653 测试／CI、同一安装环境与 wheel|只提供已经写入的 phase；本轮读取时没有 `result.json`、JUnit 或 finish，不能写为通过或终态|
|历史官方 43676697981，attempt 1|旧训练片自己的官方候选，见原测试价值审计；不同于478与b653|说明原初分配曾经较轻，不能作为当前容量|

固定 b653 JSON 文件数为 `12 / 13 / 14 / 15 / 12 / 20`，总计86个；controller 的37个测试函数／75节点已经登记 group 2。本文不变更此前已核的 Linux 2227／Windows 选集2172节点身份。

## 官方成本：478 自己的最终 job 记录

原件为 `.ergora/checks/ci-training-shards/public-run-r1/response.json`，由主控提供的已保存 HTTP 200 响应，本轮未另请求 API。按每个 job／step 的 `completed_at - started_at` 计算：

|478 官方环境|整个 job 秒数|Native application regression 秒数|终态|
|---|---:|---:|---|
|Linux group 0|253|233|success|
|Linux group 1|295|273|success|
|Linux group 2|255|232|success|
|Linux group 3|195|178|success|
|Linux group 4|225|205|success|
|Linux group 5|1215|1195|cancelled；已有公开页明确20分钟超时|
|Windows all|1541|1419|success|

准确478的五个成功 Linux job 中，job 比回归步骤多17–23秒；这是该次实际开销，不是下个候选的预留保证。group 5 的1215秒来自 API 的 job 时间戳，不能解释为允许 pytest 独占1215秒。workflow 的 `timeout-minutes: 20` 仍覆盖检出、安装、reference verify、回归和上传。

此前官方43676697981回归步骤的 groups 0–5 为299／293／202／223／206／693秒、Windows1418秒（[旧审计](2026-11-15-training-test-value-review.md)）。478自己的回归改为233／273／232／178／205／1195秒，其中 group 5 已取消；它们是不同候选的两次记录，不是可相减得到本次服务新增成本的对照实验。478仍显示3、4、0、1可作为初始接收组；Windows1541秒也说明仅优化 Linux 不认证整个 workflow 关键路径下降。

## b653 本机实际成本

group 2 的 `result.json`：exit 0、外层1522.575秒、输入结束后无变化；JUnit 为461节点、460 passed／1 skipped、suite1520.806秒，stdout 的四舍五入汇总约1520.84秒。JUnit testcase（含其记录的 setup／call／teardown）按文件汇总如下：

|b653 本机 group 2 文件|节点数|JUnit case 秒数|
|---|---:|---:|
|`tests/test_training_cycle_controller.py`|75|798.513|
|`tests/test_task_cancellation.py`|38|390.002|
|`tests/test_reference_executor.py`|24|117.292|
|`tests/test_issue_writebacks.py`|41|76.346|
|其余10文件|283|约131.754|

controller 外的同轮 case 成本约722秒，而478官方旧 group 2 整个回归步骤232秒。这支持本机与远端存在明显成本差异的判断；产品候选、测试集合、运行环境都不同，不能将二者比值当作固定加速系数，也不能用 `232 + 798.513` 宣称新官方预算可过。

group 5 只读快照截至本机2026-11-16 02:08左右（最后 phase elapsed1610.430秒），没有 finish，最后进入 `test_cycle_lost_ack_and_missing_authorization_only_reconcile_the_original_start` 的 call。下列来自已写完的 phase，均为 b653 同轮本机观察；不包含未完成 call 的尚未落盘时间：

|b653 本机 group 5 文件|已记录 phase 秒数|当时边界|
|---|---:|---|
|`tests/test_training_release.py`|288.751|27节点均有 teardown|
|`tests/test_task_external_status.py`|241.713|48节点均有 teardown|
|`tests/test_training_cancellation.py`|170.860|13节点均有 teardown|
|`tests/test_training_submission.py`|463.312|仅46节点已有 teardown，后续仍运行|

release／external status 两个已完成文件的530.464秒可以支持选择迁移对象；不能把未完成 submission 的463.312秒当作全文件成本。不要据此宣布 group 5 最终耗时、结果或剩余预算。完整终态由主控继续消费原件。

原[成本调查](2026-11-16-ci-training-shard-duration-analysis.md)里的75285旧预算／phase片 suite495.259秒、c1b1安装r2 suite985.931秒、同产品精准r3 suite153.696秒、服务安装r2 suite155.466秒，均为各自候选的不同选集。历史两份去重66 case／1389.711秒和拟迁移32 case／678.587秒只支持原拆分方向。本次已有完整controller798.513秒，应优先使用它；不能将历史剩余711.124秒拼接成本次 group 5 总成本或下界。

## 最小的具体后续候选

建议仅调整现有 `scripts/ci/linux-groups.json`，保留 controller 在2，按下面顺序构成一个有限、可审阅的四文件候选；不增组、runner、测试拆分或观察机制：

|文件|从组→到组|选择依据|
|---|---|---|
|`tests/test_task_cancellation.py`|2→3|b653本机390.002秒；准确478官方group3回归178秒，是最轻接收组|
|`tests/test_reference_executor.py`|2→1|b653本机117.292秒；给较重的旧group1接收较小文件，避免继续堆给3|
|`tests/test_training_release.py`|5→4|b653本机完整27节点phase288.751秒；准确478官方group4回归205秒|
|`tests/test_task_external_status.py`|5→0|b653本机完整48节点phase241.713秒；准确478官方group0回归233秒|

转移后文件数为 `13 / 14 / 12 / 16 / 13 / 18`，仍86个，每文件恰好一组。只以本机同轮 group 2 的 donor 算术核方向：移出两个文件的 testcase 成本507.294秒，原 suite 减它们约1013.512秒。只移 cancellation 一个文件则约1130.804秒，在本机只余约69秒才到整个job1200秒，且还没计官方安装等；在接收组成本未知时，没有理由将这一更窄余量称为稳妥。因此建议再移117秒的完整 reference 文件，而不再拆 controller。

上述减法是对已观察样本的重新归属估算，**不是重分组后的实测**：fixture构造、进程位置、机器负载会影响成本；接收组没有b653同环境完整成本。也不将478官方接收组秒数与b653本机迁入秒数相加形成“预计成功”。group 5 减去530.464秒仍有未完成节点，无法预测；若最终仍重，先读该轮完整JUnit／phase再决定是否还需迁出已有完整文件，不能预先宣称这四次移动足够。此方案是低变更量的下一候选，不证明数学意义上的最少迁移次数。

这四个文件已有各自真实测试模块边界。cancellation／external status 原本就从 registration、task submission等模块导入fixture；release从 training evidence／training runtime导入fixture。整文件改变组号不需要复制fixture、导入测试函数或创建第二测试框架，也不应顺手改变这些依赖。静态节点相等仍不证明在新进程分配下fixture开销和生命周期结果保持。

## 必须保留的未测范围与后续验收

本报告未实施上述 JSON，因此不存在四次转移后的节点核验、完整六组本机成本或官方成功证据。先等原b653 group5终态并核输入未变；保留它现有失败／成功的真实结果。若主控采用四次移动，先用原runner/plugin核六组唯一、文件存在、无漏项及完整node multiset不变，Windows all选集保持；不要只核文件数。

分配变更会触及0／1／2／3／4／5，完整行为成本需要候选自己的受影响组证据。已有b653完整group2可用于定位，不能标成后继JSON已通过；本机四个接收组目前没有同候选完整成本，不应无依据套旧官方时长。沿现有非editable安装与JUnit／phase／退出／输入摘要记录验证，不新增冗余小测试。原取消、失联只对账、预算／恢复、原生进程收尾必须照常触发并结束。

最终仍须新候选自己的准确官方CI证明六个Linux job均在原20分钟限制内完成，Windows保持自身原要求；本机经过合理重分配只能支持进入验证，不能替代这一门槛。没有证据支持删用例、预算或断言、延时、增组或引入第二runner。

原件校验：官方jobs响应 SHA256 `69b5aa084b40d2c8f046c61113e1254dfd1cb4826b85e6a2df941c8f9f23cfd2`；b653 group2 result `f5d0d34c0ea64d05288ea4891e2452967d31fd44b8c2b8106462721184bc98c7`，JUnit `418b0ca78194dd97531e7ffbfb760601b1b7f70cb935160682d0460357046bda`；b653 JSON `298e4160010d20840f2152fb647e5f58eddfc43948fa92fa1c55d190164ec0e0`。仍增长的group5 phase不固定摘要，也不修改其原件。
