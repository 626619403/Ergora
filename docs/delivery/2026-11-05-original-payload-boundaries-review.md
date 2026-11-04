# F5.0：原单参数 history 边界独立审查

日期：2026-11-05。审查者：新的独立上下文 `original_payload_review`，仅受委派审查，未参与实现。先读适用 `AGENTS.md`、原始 diff、新文件及相邻调用，再读作者交付说明；按 maintainable-project-delivery 及其 independent-review brief 执行。本报告仅裁定本片源码和已核本地证据，提交、远端及精确双 OS CI 尚待终结。

## 范围与身份

基线及审查时 HEAD：`f2b93d4daba751a707af43755f2dd30fc19c74f8`，分支 `refactor/architecture-foundations`；当前变更未提交。完整检查了 tracked diff 和三份 untracked 文件：

- 生产：`src/ergora/reference_task_runtime.py`、`src/ergora/reference_task_reconciliation.py`。
- 夹具：`tests/fixtures/task_runtime_client.py`、`task_submission_client.py`、`task_external_status_client.py`。
- 测试：`tests/test_task_external_status.py`、`tests/test_task_reconciliation.py`、新增 `tests/test_original_payloads.py`。
- 文档：`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、新增 `docs/plans/2026-11-05-evidence-handoff.md`、新增 `docs/delivery/2026-11-05-original-payload-boundaries.md`，以及 F4 的 `2026-11-03-formal-task-console.md`、`2026-11-05-f4-completion.md`、`2026-11-05-f4-completion-review.md` 状态记账。后者是原片终结记录，本审查未重做其历史运行验收。

读取了原生 `DevelopmentTransport.lookup/start/cancel`、workflow/signals/activity 的单参数合同、`_Submission.lookup_run`、批准/取消恢复、原 job/plan 读取及对账 fence/lease 调用顺序。F5.1–5 仅为计划，没有新增索引、执行账本或外部投影实现。

|身份|SHA256|
|---|---|
|`reference_task_runtime.py`|`5f9a17f3d8d8b27e834766853c4865e76cdd781b5203c7c6692e2cd48a238207`|
|`reference_task_reconciliation.py`|`57db923fa4180858ff9d66e1993ced002fc29fa8a04e0e4551a94b661daead17`|
|`tests/test_original_payloads.py`|`1e24b7f9d4fbb80fb400e4170c4f52b8aab7784e6a1776b969620842c45445bd`|
|已核 wheel|`191cef78663ce545084c8373aa2b6ab35cba4e3b2b70db47efacc199b965788b`|

## 需求符合性

**通过，限上述切片及已核证据；无本片正确性 finding。**

- `reference_task_runtime.py:43` 在原 workflow input 容器处拒绝零个或多个 payload，再调用原 converter 并保留完整 JSON 摘要比较。真实调用仍将 `payloads, [dict]` 传入；describe/memo 继续使用原 SDK converter，没有改变合法单参数、codec、run 或提交归属校验。
- `reference_task_runtime.py:19` 对同名但非单参数的 signal 继续扫描，只有完整 JSON 身份相等才返回其原 event ID。批准/取消调用者仍在未找到时保持未知状态，并仅恢复原 intent；新增守卫没有重发或写入成功回执的分支。
- `reference_task_reconciliation.py:44` 在每个原 `dev_submit` 调度事件的输入处拒绝非单参数。`_Inspection.run()` 必须先完成整个 history 检查，`_Reconciliation.reconcile()` 才能保存 attempt、发布 fence 或释放 lease。多参数不能被默认为一个已确认 job；已有 decoded dict/身份及完整 history 检查仍各自保护不同不变量。

独立读取 SDK1.34.0 的 decode 路径并以内存消息复现：两个 JSON payload 加 `[dict]` 只返回第一个对象；截断位于 transfer-type wrapper 对 values/converters/type_hints 的 `zip`。因此新增原始数量检查保护真实可达缺陷，不能由现有 decoded-list 长度检查替代。也已核 SDK PayloadCodec 的数量合同，合法单参数不允许编码扩成多 payload；本片保持一对一 codec 的解码能力。未扩展到自定义 converter 违反其合同或其他 SDK 版本。

## 可维护性、性能与必要测试

**通过；无本片可维护性 finding。** 三个守卫位于已有所有者，不增加生产文件、函数、抽象、依赖或配置接口。原有单 job/plan 容器守卫保持不变；本片没有将所有调用者改为各自重复校验，也没有改动冻结 reference。

新增测试直接使用 SDK Payload、HistoryEvent 和 codec，覆盖零/单/双参数、两种实际 signal 名称及异常事件后的继续扫描。隔离 `_Inspection.jobs` 的测试只构造其所需的原身份；两个既有集成矩阵各增加一个多参数情形，分别验证只读不变和任何 fence/lease 副作用前拒绝。两份旧夹具改为单个 spec 占位，保留其原有错误/中断场景；新的真实 SDK 测试承担数量合同验证。这些用例分别保护解析边界与资源生命周期，未发现需要删除的重复测试。

生产增加的是 repeated-payload 容器长度判断，没有新增 RPC、history 扫描、重试或持久写入；原扫描复杂度和限时保持。没有性能基准，也不据测试耗时宣称通用性能提升。独立建议停止重复初始化成本较高的本地 240 项矩阵，保留已完成个案，补其余代表调用与未知恢复；现有两 OS CI 已安装 Temporal SDK 并自动发现全部 `tests`，无需新增 CI 矩阵或调整测试语义。

## 实际检查与限制

- 审查者独立运行 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .ergora/checks/f5-evidence-foundations/development-venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_original_payloads.py`：**12 passed，0.96 秒**，仅内存 SDK 消息，无服务或缓存写入。
- 审查者逐项重算当前源码、实际 wheel 和两处安装的 **350 资源**，全部相等；核实际 `direct_url.json`，两处均非 editable。独立从基础安装运行 `python -B -m ergora reference verify`：**283 文件 PASS，runtime_started=false**。`git diff --check` 通过。
- 直接读取作者原命令和完整结果：SDK 红例 **8 failed / 4 passed**、修后 **12 passed**；新 wheel 边界 **14 passed / 103 deselected，17.03 秒**，包括外部只读和显式对账两个多参数反例。未把这些作者运行记成审查者重跑。
- 原 240 项命令实际 **74 passed 后 SIGINT、exit2，pytest421.69秒**；读取了精确 argv/PID 的 interruption 记录和原日志。74 是已完成个案数，**240 项整体未通过验收**。其余代表源回归另行 **15 passed，71.02 秒**，命令覆盖批准精确信号恢复、取消正常/缺 marker 未知恢复、两模板外部只读/精确 claim 对账，以及 8 项架构边界。均直接核原日志，未另启重型矩阵。
- 以上作者证据保存在私有 `.ergora/checks/f5-evidence-foundations/`：`sdk-baseline-command.json` / `sdk-baseline.log`、`sdk-fixed-command.json` / `sdk-fixed.log`、`wheel-boundaries-command.json` / `wheel-boundaries.log`、`package-identity.json`、`affected-source-command.json` / `affected-source-interruption.json` / `affected-source.log`、`representative-source-command.json` / `representative-source.log`。基础安装无 SDK 的命令/log 已核；本审查没有安装、启动服务、调用模型、操作原业务任务、提交或推送。

作者已同步先前调查措辞和中止矩阵记账，当前计划/交付明确保留精确提交与双 OS CI。**本地需求与可维护性审查无未解决 finding；F5.0 仍须完成精确提交、正常推送、完整 CI 和同片终结复核，方可登记交付完成。** Windows 实际结果和远端状态不由本报告的 Linux 内存检查代替；F5/G0 及后续功能保持各自未完成范围。

## 精确提交、包、静态与实时远端复核

日期：2026-11-05，同一独立审查者续核。精确候选为 `da80e777f9ccb1caf6de54f66d245669d953b8d2`，唯一父提交为原基线 `f2b93d4daba751a707af43755f2dd30fc19c74f8`。本节检查只使用该提交的 Git 内容和原发行包，后续 F5.1 工作树或提交变化不归入本片。

- **精确范围与提交通过。** 独立读取 Git 提交和完整文件列表，实际为 16 文件：2 生产模块、6 测试/夹具、8 文档，逐项等于 `staged-scope.json` 和 `commit-command.json`。新增 SDK 回归文件的 Git blob SHA256 等于上文已审身份；两生产模块也随下述资源逐项核实。已读原 `commit.stdout` / `commit.stderr` 及 exit0 记录，精确父子范围 `git diff --check` 独立通过。
- **精确发行身份通过。** 独立在内存读取该提交的 `git archive`，实际 350 资源的完整路径集合、字节及摘要逐项等于实际 wheel、两处原安装和 `package-identity.json`。实际 wheel 完整 SHA256 仍为 `191cef78663ce545084c8373aa2b6ab35cba4e3b2b70db47efacc199b965788b`，与 `commit-package-identity.json` 相符。没有重新构建、安装或继承其他源码的包结果。
- **最终静态文档通过。** 对精确候选的 8 文档重算 blob SHA256，全部等于原 `static-documents.json` 及 `staged-scope.json`。从该提交的内存归档独立重核全部本地链接/锚点，实际 257 条、零 missing；使用已核同源发行的 CLI parser 重新解析该提交 README 的 27 条命令，数量和命令内容均与原记录一致。此项只检查文档及 parser，没有执行任务或调用服务。
- **正常推送及实时远端通过。** 已直接读取 `push-remote-identity.json`、`remote-before.stdout` / `remote-after.stdout`、`push-rsa.stdout` / `push-rsa.stderr` 和对应 remote stderr：原推送 exit0，普通快进 `f2b93d4..da80e77`，前后远端与记录一致。审查者另于 `2026-11-04 20:31:56 UTC` 使用已有 RSA 身份及现有配置的 SSH 传输执行只读 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`，独立 exit0、stderr 为空，实时远端精确返回完整 `da80e777f9ccb1caf6de54f66d245669d953b8d2`。未读取或输出私钥内容，也未推送。

**本片源码/本地验收、精确提交、发行身份、最终静态文档和正常推送/实时远端复核通过，无新增 finding。精确双 OS CI 尚未核验，F5.0 仍保留该项和同片最终终结，不据本节登记完整交付完成。** 本次仅追加本报告；没有启动服务、重复重型回归或修改后续功能。

## 精确 CI 与同片最终终结

日期：2026-11-05，同一独立审查者续核。精确候选仍为 `da80e777f9ccb1caf6de54f66d245669d953b8d2`；官方 [Portability CI 41906996732](https://github.com/626619403/Ergora/actions/runs/41906996732) 已完成并显示 **Success**。当前未提交 F5.1 工作树不归入此次验收。

独立读取原 `fetch-ci.py` / `verify-ci.py` 和实际保存的官方 actions、run、两 job HTML、job-groups JSON 及 selection/status JSON；另写只读内存解析核验，没有调用会覆盖证据文件的原脚本。六份来源的实际字节数/SHA256 全部等于 `ci-html-status.json`。官方 actions 行的完整 commit/run 关联、行摘要、run 页完整 commit 链接及 portability workflow 链接均相符，run 状态为 Success。两 job 页的 `selectedJobId`、平台名称、必要 step 的 completed/conclusion 及含完整候选 SHA/job ID 的 log URL 逐项核过。

|平台与精确 job|独立核实的必要步骤|
|---|---|
|[Ubuntu / Python3.11，126844222428](https://github.com/626619403/Ergora/actions/runs/41906996732/job/126844222428)|Build and install wheel、Packaged reference identity、Native application regression 均 completed / success|
|[Windows / Python3.12，126844222800](https://github.com/626619403/Ergora/actions/runs/41906996732/job/126844222800)|上述三步及 Windows PowerShell 5.1 installer and upgrade 均 completed / success|

全部实际 check-step 无 failure/cancelled/timed_out；Ubuntu 的 Windows 专用步骤按原 runner 条件 skipped，Windows 本身该步骤成功。原 workflow 的 Native application regression 执行全量 `tests` 及各平台适用套件，本次没有修改 CI 或缩减该步骤。本地 240 项中止记录仍保留其原范围，由此次精确 CI 完成完整矩阵验收；本审查未下载逐行测试日志或推造具体用例计数，也未重新运行套件、安装、启动服务或操作原业务任务。

**最终结论：F5.0 需求符合性与可维护性通过，源码及本地证据、精确提交/原包身份/最终静态文档、正常推送/实时远端和精确双 OS CI 的同片复核全部通过，无未解决 finding 或本片剩余验收项，F5.0 可登记完成。** 本节关闭上文按当时状态保留的 CI 待验项；本次仅追加原报告。F5.1 及后续 F5/G0 功能和支持范围仍各自独立验收，不继承本片完成状态。
