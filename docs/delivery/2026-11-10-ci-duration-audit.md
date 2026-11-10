# CI 时长与冗余审计

2026-11-10，独立只读审计。固定已提交候选 `0a495aaaa489f838c009820b7cd978bbed0c5e37`（AC5 C2）；C3a 的未提交实现由其自己的审查负责。本审计只新增本报告和私有分析证据，没有修改源码、测试、CI 或依赖，没有安装、调用模型、运行整套回归、重跑/取消远端 CI、提交或推送。

**当前没有实证支持在下次 CI 前先修产品、删除测试或延长 timeout。** C2 自己的 [CI42747066139](https://github.com/626619403/Ergora/actions/runs/42747066139) 已 Cancelled，Ubuntu 原生回归没有完成，因此 C2 的双平台 CI 门禁尚未通过。已定位到回归步骤耗尽 job 预算，尚未取得逐例 console 进度，不能定位停住的测试，也不能判定为产品 bug、确定的性能退化或冗余测试所致。

审计独立读取了 C2 的 `snapshot-01/02/03/04` 原件：前两次是 In progress；第三次采样选择断言失败，不作为 CI 终态证据；第四次是 Cancelled。原 sample 所列来源逐一重算 SHA256 均匹配，job selector、完整 commit、工作流及各非空日志 URL 的候选身份分别核对。另核独立终态读取保留的公开逐步日志响应：精确端点返回 404 页面，没有 pytest 进度或尾部。没有改写任何原件，也没有把在途或采样失败记录当成成功。

|精确来源|实际观察|边界|
|---|---|---|
|[C2 Ubuntu job129601601956](https://github.com/626619403/Ergora/actions/runs/42747066139/job/129601601956)|构建安装 20 秒，包内身份步骤小于页面 1 秒精度；原生回归 03:05:30–03:25:06 UTC，1,176 秒，cancelled|原注释为 “The job has exceeded the maximum execution time of 20m0s”；20 分钟是整个 job 的上限，1,176 秒是已观察到的回归运行区间，不是完整套件完成时间|
|[C2 Windows job129601602409](https://github.com/626619403/Ergora/actions/runs/42747066139/job/129601602409)|原生回归 496 秒，四项必要步骤 success|加上 Ubuntu 的构建/身份共六项必要步骤成功，不能替代第七项未完成的 Linux 回归|
|[前片 03f1f58 的 CI42616678385](https://github.com/626619403/Ergora/actions/runs/42616678385)|run 14分44秒、七必要步骤 success；[Ubuntu job129158155380](https://github.com/626619403/Ergora/actions/runs/42616678385/job/129158155380) 回归 861 秒，[Windows job129158154892](https://github.com/626619403/Ergora/actions/runs/42616678385/job/129158154892) 回归 541 秒|独立核其终态原 HTML；不同运行且本次被截断，没有控制 runner、依赖解析或系统负载，不能计算因果退化率|

C2 run 的公开列表时长是 20分8秒，Ubuntu job 页面是 20分4秒；它们与回归步骤 19分36秒描述不同边界。原注释还包含 checkout/setup-python 的 Node.js 20 弃用提示，没有观察到其导致失败。页面明确要求登录查看日志；[完整候选绑定的原生步骤端点](https://github.com/626619403/Ergora/commit/0a495aaaa489f838c009820b7cd978bbed0c5e37/checks/129601601956/logs/6) 没有提供可用 console 内容，额外无凭据公开读取也未取得日志。本轮没有使用私密凭据或绕过访问限制。因而没有能稳定触发同一超时症状的快速反馈命令；采用 `diagnosing-bugs` 的证据优先流程，停留在反馈信号收集，不声称已复现或找到根因。

[C2 相对 03f1f58 的精确差异](https://github.com/626619403/Ergora/compare/03f1f583f91c6f1b2f35b89ff8d0d513f40c519d...0a495aaaa489f838c009820b7cd978bbed0c5e37) 中，非文档变化只有 `app.js`、`workflow.js`；没有新增 Python 测试、依赖或 CI。现有 Python Web 测试读取打包静态资源，并未在 CI 执行 C2 的浏览器旅程。此事实排除了“本片新增 Python 测试数量”这一解释，不能单独证明 JS 对所有成本完全无影响。

已对照的私有既有日志如下，均是各自候选、各自选择范围的历史观察，没有为审计再执行一次。

|已有回归记录|已核计时信号|可支持的结论|
|---|---|---|
|F3 对账完整回归，711 passed / 19 skipped / 36 subtests，1,722.63 秒|最慢项为真实慢远端/数据库锁边界 13.73 秒；多项任务导出/恢复 call 约 8–12 秒|原生任务链有分散的累计成本；不是当前候选的耗时分布|
|F4 原候选完整诊断，711 passed / 19 skipped / 36 subtests，2,550.05 秒|导出 call 24.50 秒、setup 21.00 秒和 19.19 秒；慢远端边界 14.29 秒|setup 与原生子进程都值得分开计时；与前一记录不是受控对照|
|AC4 工作纵切片定向包回归，291 passed / 6 skipped / 1 failed|既有 `test_reference_executor` 的单例子进程 90 秒超时；保留原失败，原样单项后来 9.52 秒通过|证明历史存在一次局部超时及后来成功；没有证明根因，不能据此认定本次停在同一例|
|当前 C3a R1 定向包回归，180 passed / 1 skipped，74.63 秒|最慢 8 项中 Web 慢探针 5.13 秒、目录/资源边界 4.62 秒、定义库整组导入 4.52 秒|只覆盖定义、manifest、Web、架构和 reference 七组，不是本次 Linux 完整 CI，也不构成 C3a 性能验收|

上述完整回归和旧成本审计的范围见 [V4 原始进度记录](2026-11-04-ci-regression-progress.md)、[原成本审计](2026-11-03-verification-redundancy-review.md)、[工作纵切片记录](2026-11-09-work-agent-runtime.md)与 [C3a R1](2026-11-10-definition-revisions.md)。本次抽取保留每份原日志摘要及其 SHA256，不把来自旧候选的数字外推为当前每例耗时。

[当前精确工作流](https://github.com/626619403/Ergora/blob/0a495aaaa489f838c009820b7cd978bbed0c5e37/.github/workflows/portability.yml) 每个 OS 启动一次 pytest：共同执行 `tests` 与冻结 `test_contracts.py`；Linux 再追加 `test_portable.py`、`test_workflow.py::AdapterTests`、`test_runtime.py`。这些路径没有父子包含式重复选择，Linux 也没有同时选择整个 `test_workflow.py`。两 OS 的平台边界、Python 版本及实际选择不同；Windows 的 PowerShell 安装升级覆盖另一个安装入口，不能作为相同运行删除。

按 C2 已提交 Git 对象静态读取，第一方有 56 个顶层测试模块、536 个顶层测试函数；这是 AST 数量，不是参数展开后的 CI 用例数。忽略装饰器只比较函数体，发现两组相同 wrapper：可信 verify 的 5 个模式与组合输入/审查失败的 10 个模式，以及模板指令失败的 3 个模式与新任务注册失败的 3 个模式。纳入参数装饰器和函数参数后没有完全相同的测试定义。人工核对这些模式进入不同失败边界，不能因为 wrapper 相同而删掉案例；提取调用 helper 主要减少代码重复，尚无运行时收益证据。

其他看似重复的保护也有不同职责：独立 `reference verify` 提供安装后提前失败与 CLI 接线信号，`test_reference.py` 校验 Python 返回合同；相同六阶段 wrapper 覆盖 legacy/unified/imported/旧快照，旧快照确实删除新增 configuration，注册场景确实在 inventory 后改变当前注册；重复查询和文件快照分别保护幂等/恢复及只读副作用。真实延迟后代写入的进程测试还必须等待足够的窗口才能证明清理，不能直接删除 `sleep`、重试查询或快照断言来缩短时间。

前次优化已经体现在当前源码：纯输入反例进入轻量 `test_task_inputs.py`，原六个 Linux 专用模块提前 skip，外部状态 fixture 基于已提交任务而非导出 Git 仓库；现有 concurrency 按 workflow、事件与 PR/ref 分组取消同类过时运行。它们不重复登记为待修。保留的 Actions 首页面对 C2 只显示一项 pushed 运行，没有证据证明本次实际跑了重复 push/PR 矩阵；PR 合并树与分支 HEAD 的不同覆盖仍须保留。

后续最小工作按以下顺序进行，各项尚未实施或验证：

1. **先取得同一失败的信号。** 若由已有权限的查看者取得原 job console，保留精确 commit/job/step 身份、最后完成 nodeid、取消前一项、相邻时间和 pytest 统计尾部。持续推进到预算耗尽与长期停留在同一项需要不同的处理；目前不能选择其中之一。无需为此另跑整套本地回归。
2. **使用下一次本来就必须执行的精确候选 CI。** 保持完整选择及已有 `-u -v --durations=20`，成功时读取其 durations，取消时读取已有逐例进度。若只能取得页级状态，再明确保留逐例计时未验；成功本身不证明旧超时原因。新候选的 CI 不能改写 C2 原取消，也不能把不同 runner 的时长差当作退化率。
3. **只对日志确认的慢项建立小反馈循环。** 在匹配候选与安装环境下先运行精确 nodeid，区分 setup/call/teardown，保留其子进程 timeout、退出码及原清理证据；需要复现上下文时再最小扩大到相邻模块。单项成功只说明该次未复现，不能宣布超时已修。若后续正式 CI 仍缺中途定位信息，另审一个不改选择/退出语义的临时逐例起止计时方案；不凭终止时未必执行的后置步骤承诺一定取到工件。
4. **另立 Windows 调度小切片。** [work_creation](https://github.com/626619403/Ergora/blob/0a495aaaa489f838c009820b7cd978bbed0c5e37/tests/test_work_agents.py#L77) 在 `creation_project` 与 `work_graph` 初始化后才跳过非 Linux。其五个现有消费者在 Windows 会先完成不需要的依赖 setup，可沿原 V2 方法只对这五个节点提前 skip，继续执行该模块纯 `work_graph` 跨平台案例。先核消费者/参数清单与 setup 命中，再按同节点测量；未测得收益，不解释 Linux 超时，也不作为下次 CI 前必修。
5. **按真实计时再决定 fixture 优化。** 原生验收 fixture 每次复制参考安装树、初始化 Git 并经实际六阶段所有者运行，存在可测的重复准备。先用日志选出一个代表性节点，分开计复制、初始化与执行；若准备确为主要成本，再比较有隔离副本的方案。当前 module 安装树会创建/删除 `.venv`，个别模式还删除源包，不能直接共享可写 session 树或以硬链接冒充隔离。既有正常/失败/unknown 恢复、候选身份及清理覆盖必须保持，优化前后以相同合同清单和少量同节点对照验收。

本审计完成的是成本与证据范围核对；Linux 根因、可重复失败反馈、当前完整逐例分布及任何优化收益仍未验。没有新增产品阻塞 finding；C2 未通过的精确 CI 门禁继续按原事实记账。完整派生证据与可重跑的只读分析脚本保留在 `.ergora/checks/ci-duration-2026-11-10/`，原件仍留在各自切片目录，不公开个人路径、原生缓存或凭据。
