# F3.3d 提交锁分段独立审查

日期：2026-11-03。审查者：独立 fresh-context agent；只接收原要求、固定基线、变更文件及实际证据，未接收实现讨论或预设结论。按项目 AGENTS、maintainable-project-delivery 的 independent-review 和 review-pr 流程执行。本报告先记录源码及修正复核；发行与精确 CI 仍独立记账。

## 结论与身份

- **要求符合性：源码及定向范围通过。** 初审发现的相邻创建锁次序 P1 已修正并独立复验。当前检查范围内无未解决 findings；不能由此认定 D 全部验收完成。
- **可维护性：通过。** 修订保留仍归 tasks；提交、批准、取消共用私有 `_native_prepare`，人工确认保留在决定入口。没有新增依赖、表、意图格式、后台调度器或公共重试策略。原创建/提交所有者、原 Transport 及本地 SDK hook 继续承载既有不变量。
- 固定生产基线：`c3113ad119c72ed933876ddae95d3c849c804852`。审查时 HEAD 为仅收口 C2 文档的 `e590af47c235dc488e25e7d0b270f96a362db403`；未提交 D 的三份源码、两份既有 fixture/test 及新增锁测试共六文件逐项 SHA256 与候选清单一致，聚合身份 `7aface07b4ad9239e0e5519aa4a835b5c420d45d9750a416ce0a5755a9183878`。独立核对记录为 `.ergora/checks/f3-task-submission-locks/reviewer/source-identity.json`。

直接检查相对固定基线的完整相关 diff、未跟踪 `tests/test_task_submission_locks.py`，以及 USAGE、当前架构、reference 边界、D 交付和计划。邻近检查覆盖 creation、runtime、approval、cancellation、State、项目修订写者、CLI/API callers、原 `agent_platform.cli.task_action`、Ingress 调用与 `DevelopmentTransport`/SDK 策略。C2 取消报告的追加是上一切片文档，不计作 D 行为。

## Finding 与修正

### P1：相邻 create/resume-create 可在等待远程 task 锁时重新占用全库保留（已关闭）

位置：`src/ergora/tasks.py:62`、`:79` 的创建事务，以及原 `src/ergora/reference_task_creation.py:236` 的阻塞 task 锁；修正位于当前 `reference_task_creation.py:237`。

可达场景：提交已释放 DB 并在原 task 锁下等待 connect；同一任务执行 `resume-create`，先取得 `BEGIN IMMEDIATE`，再等待相同 task 锁。第三方对另一个项目的真实 bind 于是继续等待提交。独立三方探针使用 3 秒受控连接延迟，跨项目写者等待 **3.035248 秒**，且写者完成前提交 result 已保存；仅分段 submission 无法消除这条间接全库等待。原证据为 `reviewer/creation-lock-probe.log`，1 passed / 6.39 秒。

最小修正：创建发布/恢复也使用原锁的 `blocking=False`，保留原编译、修订、意图与发布合同；任务忙时明确失败，退出控制库事务。作者已加入 create/resume-create 两项真实子进程回归，核任务字节/准入无变化且其他项目仍可写，原创建并发检查保留。

独立复验在真实在途提交中调用 resume-create：**0.072265 秒**返回 busy，另一个项目真实 bind **0.002486 秒**完成，此时提交仍在连接等待；最终仅一次 start。证据为 `reviewer/creation-lock-fix-probe.log`，1 passed / 5.85 秒。该 finding 关闭。最初探针曾因把父 Future.done 当作 task 锁释放时点而错误失败，修正为持久 result 证据后重跑；第一份日志和原探针均保留，不能把该探针断言错误算作额外生产缺陷。

## 实现与结构核查

1. `_native_prepare` 在当前修订的 DB 保留下只做本地 prepare/prepare-resume；子进程不加载完整连接环境，不调用 doctor、claim 或 connect。prepare 对同 task 锁非阻塞，失败通过原异常路径释放事务；无新预检重试或轮询。
2. DB context 已退出才调用 dispatch/resume。远程阶段重新加载并核验原创建、登记和精确意图 SHA，继续原准入、claim、严格 JSON/spec、memo 归属和写前 attempt；阶段间改角色或 revision 不改已授权快照。
3. 已有意图的重复 start 只返回原记录。明确 resume 若在原 dispatch 前抢先完成或保存 attempt，后到 dispatch 只读 submitted/unknown；有 attempt 的 resume 仅查原 workflow/history。NOT_FOUND、失联、未知归属均不触发新 start。原任务/run ID、spec 和 memo 未被改写。
4. 新共享函数是既有 tasks 内的修订事务算法，真实服务提交/批准/取消三个操作；确认检查仍归 `_decision_prepare`，没有为 start 伪造确认。新增测试文件只验证 changed contract，没有抽出单消费者生产框架。
5. 用户手册已说明 busy、prepared/unknown 并发快照、明确恢复和分阶段 timeout。CLI 仍仅在 submitted 返回成功退出码；HTTP 仍要求检查响应 status，没有把 200 解释为已提交。

## 验证证据

独立探针均显式使用源码：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests .venv-dev/bin/python -B -m pytest -q -s --tb=short -p no:cacheprovider`，Python 3.11。证据目录前缀均为 `.ergora/checks/f3-task-submission-locks/`。

|检查|结果与实际证明范围|
|---|---|
|`reviewer/probe_submission_contracts.py`|**10 passed / 54.02 秒**，原始 `reviewer/submission-contracts.log`。精确 C2 submission 源码生成六类 prepared/unknown/submitted/rejected journal，再由 D 读取及明确恢复；原有 intent/attempt/result/rejection 字节不变，原 spec 及适用的 server memo/ID 字节不变。未知 NOT_FOUND 零次新 start。|
|阶段间明确 resume 抢先|上面三项交错分别让恢复成功、attempt 后中断、server 接收后 result 前中断；后到 dispatch 无新增 RPC，返回对应 submitted/unknown，最后总 start 次数为 1/0/1。|
|prepare 后中断及 revision 更新|上面一项在无准入时中断父流程、将当前 revision 由 1 改为 2；旧 revision 恢复拒绝，新 revision 加原意图 SHA 恢复成功，submitted_revision 仍为 1，原意图及角色文件字节不变。|
|创建锁修正独立复验|真实 3 秒连接等待内，resume-create 及时 busy，其他项目真实写者先于提交完成；上节数值及日志。|
|作者六套首轮定向|已读完整结束日志：**156 passed / 1 个已有 warning / 715.79 秒**。这是创建锁修正前身份，只证明该首轮范围，不自动覆盖修正。|
|作者修正后 locks + creation|已读完整结束日志：**34 passed / 1 个已有 warning / 38.18 秒**，`creation-lock-fix.log`；覆盖非阻塞创建发布/恢复及原创建合同。|
|静态核对|`git diff --check` 通过；六个源码/测试摘要逐项匹配最终候选清单。|

上述 fixture 保留原 doctor/admission/claim/Transport 与 SDK 调用策略，在受控 SDK 端口替代真实服务响应。它们证明客户端协议、记录和锁次序，不是存在真实 workflow 的网络端到端验收；3 秒 probe 也不替代原 18 秒同条件验收。

## 剩余门禁

当前仍待最终 D 非 editable wheel 的两安装及冻结资源核验、同等 18 秒连接延迟下跨项目写者/同任务 start/create/resume-create busy 实测、首次提交额外子进程启动成本比较、旧 B/C1/C2 原地记录与十类 C2 状态升级恢复、两模板基础 CLI 旅程、完整发行回归、精确两 OS CI 与最终提交/远端身份独立核对。发行数据到齐后在本报告追加复核；任何未完成维度均不继承 C2 结论。F3.4 真实新六阶段、导出及重启综合旅程继续单独验收。


## 最终发行证据追加：已完成本地门禁

本节在上述源码审查后追加；逐项复核实际已结束的证据，不覆盖当时的待验记录。D 最终 wheel 为 `c774ba4f3eb1d8d553f86253cc23954c33404fe0eaec10f5106597d54a4d38bf`，六文件源码/测试聚合仍为 `7aface07b4ad9239e0e5519aa4a835b5c420d45d9750a416ce0a5755a9183878`。已完成发行、并发、兼容与性能范围内无新增 findings；完整发行回归和精确 CI 尚未作通过判定。

### wheel、安装与基础旅程

独立重新计算源码、wheel 内和两份非 editable 安装的全部 **345 文件** SHA256，四份逐项一致；两安装 direct_url 均指向该 wheel，Python 分别为 3.11.15 和 3.12.3。在两个已安装环境分别调用原只读 reference.verify，均 **PASS / 283 文件**；基础 Python 3.12 环境实际查询 FastAPI、Temporal 和 GEPA 均不存在。只读核对没有安装或回归重跑，完整结果在 `reviewer/package-recheck.json`。

已核 `journey-performance.py`、JSON 和结束日志：基础无 SDK 控制面两模板共 **72 次 CLI**，先验证完整运行环境缺失会明确失败，再使用登记 SDK 解释器完成一次受控提交；每模板 submission/start/resume-start 各重复 10 次，原响应精确相同，原生任务及提交记录字节不变，每模板 doctor/start 各一次。重复路径不是 RPC，初次提交仅替代 SDK 服务端口；不等价于真实新六阶段旅程。两模板重复命令中位约 1066–1141ms，包含 CLI/子进程/SDK 导入及并行完整回归开销，不能推出模型吞吐或独立 RPC 时延。

### 18 秒同条件协调验收

已核 `lock-contention.py` 和对应原始 JSON/log。最终 wheel、受控 connect 延迟 **18 秒**、各阶段 25 秒预算，使用实际共享 SQLite、原 task 文件锁和真实项目 bind：

- 另一个项目首次写入 **21.318ms** 完成。
- 同任务 start/create/resume-create 分别在 **780.115 / 113.313 / 94.183ms** 明确 busy；每次拒绝后另一项目均继续写入，最终 revision 为 5。
- 脚本在首次写入、三个 busy 和后续写入后均断言原提交尚未返回；最终仅一次 doctor/start，原 run 为 original-run，结果 submitted，总时长约 19.86 秒。

原 B 同 18 秒受控延迟下写者约 15.04 秒后 SQLite busy 的历史身份及范围保留；新证据支持解决共享控制库写锁争用，也覆盖初审发现的间接创建锁路径。SDK 连接延迟是 fixture，任务锁与数据库写者是真实的；不声称执行了真实远程 RPC。

### 首次提交成本与结构代价

已核 `startup-cost.py`、`startup-baseline.json` 和 `startup-candidate.json` 的实际五个样本/模板：同 Python 3.11.15 解释器和同 fixture 摘要，设置过程不计时。C2 baseline 两份关键源码摘要直接与 `git show c3113ad:...` 核对一致；D 摘要与最终 wheel 一致。

|模板|C2 首次提交中位|D 首次提交中位|观察差值|
|---|---:|---:|---:|
|repository-governance|971.854ms|1943.502ms|+971.648ms|
|large-change|1033.686ms|1821.872ms|+788.186ms|

D 将一次原生调用分为两个子进程，额外启动/导入及本地校验是可解释的成本。这里测到的是**两期不同回归负载下的首次提交总延迟差**，不是隔离出的精确进程启动开销。交付记录已明确接受本地提交延迟换取远程等待释放全库保留，未通过常驻进程、新 RPC 层或隐式重试隐藏成本；本切片没有更高吞吐结论或更窄延迟承诺。

### 固定 C2 升级恢复与旧项目

已核 `upgrade-compatibility-v3.py`、固定 C2 overlay 基线身份、`upgrade-v3-baseline.json`、最终 `upgrade-v3-candidate.json` 和两个结束日志：两模板五种状态共 **10 个新 C2 样本**全部通过；另 **6 个 B/C1/C2 原项目**原地读取，响应与原 config/execution 字节完全相同。独立再次读取并重哈希十个样本恢复前已有的全部 tasks/ergora 文件，以及六个旧项目的全部 config/execution 文件，均与基线匹配，证据为 `reviewer/upgrade-record-recheck.json`。

v1 在 prepared 明确恢复时错误禁止正常准入新增 cli-ingress/attempt/result，v2 又把 unknown 的 NOT_FOUND 临时观察字段当作持久 status 全等。这两份失败日志保留，不能作通过，也不构成生产缺陷。v3 从固定 C2 wheel overlay 重新生成未恢复样本，仅允许按状态规定的新增文件；旧文件摘要仍逐项严格比较。最终读取仅去掉 reconcile 返回的 reconciliation/instruction 临时观察字段，保留全部持久字段精确比较，修正合理。

normal 保持 submitted；doctor-blocked 的 prepared 明确恢复为 submitted；lost-response 的 unknown 沿原 ID 查到 submitted，未再 start；after-attempt 两模板继续 unknown/NOT_FOUND，**总 start 次数均为 0**；已拒绝的竞态仍 rejected。以上是原 journal/锁/Transport 加受控 SDK 的升级验收，不是正在运行真实 workflow history 的迁移。

### 当前仍待

完整非 editable 发行回归的 `wheel-regression-command.json` 当次 exit_code 仍为 null，原日志仍在输出，本节没有预认通过。D 精确两 OS CI、最终提交及远端 SHA 复核也待完成；源代码若再变化，须重新绑定受影响证据。完整回归结束后另行追加本地最终结论，精确 CI 到齐再追加远端结论。F3.4 真实新六阶段/导出/重启继续独立验收。
