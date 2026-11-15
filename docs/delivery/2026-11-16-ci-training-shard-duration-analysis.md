# Linux 训练分组超时归因与最小修复建议

日期：2026-11-16。只读分析基线为主树 `478c98891522930817fa7005a8ac96e408f37230`；服务后继树为 `eedba08c8c112683a7946726aab3f4fd590f26d6`，其未提交修正不属于本次 CI。唯一新增为本报告；没有网络请求、pytest、安装、源码／CI／计划修改或提交。

结论：已证实 group 5 整个 job 达到 20 分钟限制；目前最强的本地解释是训练提交回归持续集中在一个串行文件。没有证据支持删生命周期／恢复场景或延长超时。仅把其他文件搬出 group 5，或把整个训练提交文件搬到另一组，不能可靠解决单文件成本。可审阅的最小后续方案是按 controller／candidate root 的独立接缝迁移原测试到一个模块，登记到现有较轻 Linux 组；不增加 job，不改变 runner 或测试逻辑。它需要实际验证，尚未实施或证明能通过远程预算。

## 已确认事实

官方 [run 43737570677](https://github.com/626619403/Ergora/actions/runs/43737570677) 的已有公开页捕获为 HTTP 200，准确 SHA 为上述478、push、attempt 1。页面仍显示 `In progress`、矩阵 `6/7 jobs completed`，但已明确给出 `Native (ubuntu-latest, 3.11, group 5)` 的 `The job has exceeded the maximum execution time of 20m0s` 和 canceled 注解。不能据此宣布整个 run 的最终状态或其他 job 的最终结论。原件为 `.ergora/checks/review-packet-ci-fixture-fix/publication-r1/public-page-r2/{summary.json,response.html,visible-text.txt}`。既有 API 请求遇到403／额度0，完整远程日志不可用。

实际 workflow 是 [portability.yml](../../.github/workflows/portability.yml)：六个 Linux 3.11 job 加一个 Windows 3.12 job；Linux 的 `timeout-minutes: 20` 限制整个 job，包含检出、Python、构建安装、reference verify、回归和观察件上传，并非 pytest 独享1200秒。Windows 的30分钟与 Linux 的运行集合不同，不是本次可删除的重复矩阵。

[run.py](../../scripts/ci/run.py) 调一个 pytest 子进程；没有 xdist 或用例并行。Linux 另收 portable、workflow AdapterTests 和 runtime，Windows 保持应用全库及 contracts。[pytest_phases.py](../../scripts/ci/pytest_phases.py) 先收全部节点，再按文件选择一个显式组；它已拒绝重复登记、缺失文件和未登记收集文件，已有 phase-start／phase 和 JUnit 观察入口。

当前 [linux-groups.json](../../scripts/ci/linux-groups.json) 的文件数为 `12 / 13 / 13 / 15 / 12 / 20`，共85个唯一文件，应用 `tests/test_*.py` 无漏项。group 5 包含全部九个 `test_training*.py` 文件及11个其他文件。75285e3 至478分组没有变化，而 `test_training_submission.py` 从1562行／44个顶层测试函数增长到3866行／99个函数；行数和函数数不是时长，但说明旧均衡假设没有跟随新增真实进程接缝更新。

## 已有本地成本原件

以下是已有本机非 editable 安装回归的 JUnit，均不是本次新运行，亦不是该远程 job 的逐项时间；选择集合和产品候选不同。case 秒数包含 JUnit 记录的测试阶段成本，suite／外层还包含其他开销。

|原件，均相对 `.ergora/checks/`|已有结果|其中 training_submission|
|---|---:|---:|
|`training-phase-lifecycle/installed-regression-r2.xml`，75285e3旧预算／phase片|24项，suite495.259秒，case合计494.614秒|22项，491.149秒|
|`training-cycle-owner-boundary/installed-r2.xml`，c1b1安装r2|76项，suite985.931秒，case合计984.318秒|47项，965.725秒|
|`training-cycle-owner-boundary/installed-r3.xml`，同产品精准补验|7项，suite153.696秒|7项，152.128秒；不与r2相加|
|`training-cycle-service-acceptance/installed-tests-r2/junit.xml`，服务后继|20项，suite155.466秒|15项，153.955秒；不是478 CI输入|

前两行 submission 有3个同名展开case重合，分别计60.650／67.163秒。以首行优先、按完整case name去重，两份历史观察共66个不同case、1389.711秒；相应测试函数当前均仍存在。这是定位单文件聚集成本的信号，**不是同候选全文件时长、远程下限或可直接相加的性能保证**。c1b1原件中单项 peer writer／stop 故障为51.916秒，lost prepare reply为36.023秒，多个原 execution 边界约26–32秒；不是一个循环打印或一条重复断言能解释的总量。

旧[测试价值审计](2026-11-15-training-test-value-review.md)已有官方43676697981回归步骤时间：Linux组0–5分别299／293／202／223／206／693秒，Windows1418秒。它们只能用于选择初始接收组，不能与本机新样本拼成当前 CI 预测。已有 `training-evidence/ci-group-collect-r1/phases.jsonl` 只有 identity／coverage／partition／collected／finish，没有运行阶段记录；collect-only外层7.657秒，不能用于setup／call归因。

上述两份主要 JUnit SHA256分别为 `1a6a4cf7f8ae4344746a9051becf90f74288a02dd9c3a0dcf4a92e92f4eb5d30`、`a3bf566750d38b8cddd4606f966ebdd1b0de0dbf80f7ec4075d91d1354c02de8`。当前分组 SHA256 为 `b50d95a1954d6e2612183feccc7b5a764c9109c479997dec7fe628127b55981e`。

## 推测、缺失证据与最小后续片

推测：真实 detached owner、预算等待、原生安装与TERM／KILL／后代回收等集成成本在同一串行文件累积，是比“CI重复登记”更有证据的原因。仍不能排除某个远程case挂住、runner性能差异、安装慢或恢复失败；没有远程 phase尾部，就不知道超时时正在setup、call、teardown或哪个节点。已有 `faulthandler_timeout=90` 只提供栈观察，不是单测截止，也不应改成掩盖失败的skip／xfail。

最小文件重分组可以保持全部节点和断言，但仅搬group5其他19个文件，仍留下历史样本已很重的submission；整体搬submission到旧202秒的group2，也只是转移风险。更可验收的小片是三个实现文件：

1. `tests/test_training_submission.py`：迁出 controller准入／恢复及candidate root生命周期的原测试，保留原fixture与故障语义；不缩预算、不删参数、不改停止／恢复断言。
2. 新增一个有独立接缝的测试模块，例如 `tests/test_training_cycle_controller.py`：沿用现有fixture，通过显式fixture导入或必要的原样迁移建立单向依赖，不复制测试、不导入旧模块的测试函数。候选集合可从 `test_controller_*`、`test_cycle_controller_*`、`test_cycle_candidate_*` 开始，最终按fixture依赖和真实状态边界核定，不能只凭名字机械分类。
3. `scripts/ci/linux-groups.json`：新模块登记到现有group2；仍为六组85个旧文件加一个拆分模块，全部旧场景各运行一次。runner、观察插件和workflow无需新增机制。

在前述66项历史去重样本中，该候选迁移集合为32项／678.587秒，剩余34项／711.124秒；两边还有未计量节点，且新模块可能增加module级installation fixture构造。因此这些数仅支持拆分方向，不承诺当前组耗时或总计算成本下降。若已有fixture依赖不能简单单向复用，应先缩小迁移边界，不为调度新建通用分片框架。

实施验收应先走静态 partition gate：JSON六组／全部分配唯一／存在／无漏项；对固定前后收集的每个节点，仅将迁移模块路径归一回旧路径，比较完整node multiset（含参数id），要求零增加、零减少、零重复，Windows `all`同样比较。另核fixture scope、原平台标记、fixture依赖闭包、collect错误及模块导入无循环；仅AST函数计数不够。已有收集插件和 `run.py --collect-only` 已提供入口，不增加第二套观察框架。

必要行为验证是同一个新非editable安装候选下运行受影响的完整Linux组2和5，消费现有JUnit、phase、退出码与观察件，确认所有节点终态、无setup／teardown错误，原生命周期故障仍真实触发并回收。拆分可能改变module级fixture次数，应特别检查managed installation、原一次start／attempt、unknown只对账、原fence、SIGKILL和setsid后代回收场景；Windows路径只需其受影响可移植节点及原skip集合／提前skip关系，不无依据全量重跑。最后由新候选自己的官方CI确认两个job在原20分钟限制内完成；本地成功不代替它。若仍超时，先读已有phase／JUnit确定单项问题，再决定下一片。

旧审计的Windows提前skip与报错整句断言清理属于独立小动作：前者不减少Linux成本，后者不会实质缩短真实进程等待，均不能作为本次超时修复。没有删必要生命周期／恢复保护的依据。

## 官方终态补证

2026-11-15 18:08 UTC后API额度恢复，主控通过一次jobs及一次run请求取得HTTP200原件（不是重试循环）。完整SHA仍为`478c98891522930817fa7005a8ac96e408f37230`，push／attempt1；run=`43737570677`已`completed/cancelled`，plan与另外六个native任务成功，group5为`completed/cancelled`。因此此前公开页面的in_progress只保留为历史快照，不再代表当前状态；没有取得完整远程逐项日志或artifact。

|Linux组|整个job秒数|回归步骤秒数|结论|
|---|---:|---:|---|
|0|253|233|success|
|1|295|273|success|
|2|255|232|success|
|3|195|178|success|
|4|225|205|success|
|5|1215|1195|cancelled，原页面已明确20分钟超时|

Windows同候选整个job1541秒、success。这是478自身的官方step结果，不是b653本地阶段时长，不能直接套比例或相加保证新预算。原始响应与请求身份保存在ignored `ci-training-shards/public-run-r1/{response.json,request-result.json,run-response.json,run-request-result.json}`。后续只按新候选自己的官方结果认证发布。
