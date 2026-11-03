# F3.4b2 显式终态外部对账独立审查

日期：2026-11-03。审查者：`/root/task_reconciliation_write_review`，全新上下文；先读原要求、原合同调查和实际 patch，再读作者交付叙述。采用 maintainable-project-delivery 的 independent-review 与 review-pr 指导。仅只读审查、少量定向执行及本报告/审查证据写入，没有修改生产或测试源码、安装、提交、推送或运行全量回归。

## 结论

- **源码需求符合性：通过。** 在本次检查范围内无可复现的 correctness finding，无阻塞项。显式 fence、独立清理证据、精确原 claim 释放、原 outcome 保留和按原意图恢复形成闭环。
- **结构与可维护性：通过。** 现有所有者和原接口复用合理；未发现应删除的生产守卫、重复测试或新增 CI。性能结论仅限下述代码成本与实际隔离测量。
- **最终发行验收：通过，b2 满足收口。** 最终包完整回归、精确两 OS CI、候选源码/包/两安装与实时远端身份均已独立只读复核，详见末节。完整 F3 仍等待 c/d/e，不承接这些真实运行的验收结论。

## 审查身份与范围

基线 HEAD：`bca8c6eefcbeec6f67b7d78bc033f7e5ad95d9ba`；分支 `refactor/architecture-foundations`。初始 11 文件全部与提供的 [review-source-identity.json](../../.ergora/checks/f3-task-reconciliation-write/review-source-identity.json) 匹配；tracked patch SHA256 为 `72d351ddc01f1a52f19f058da7d57dc4b9269da731d93012bdbe2596813baec1`。原始 patch 和新增文件直接读取，没有用旧包代替源码。

生产范围：`cli.py`、`reference.py`、`reference_task_reconciliation.py`、`tasks.py`、`web.py`。测试范围：`tests/fixtures/task_external_status_client.py`、`tests/test_task_inputs.py`、新增 `tests/test_task_reconciliation.py`。初始文档范围：`docs/PLAN.md`、`docs/USAGE.md`、新增作者交付记录。另读原 `_Creation`、`_Submission`、原 FileAdapter/IngressLeases/core.write、控制库准备与文件锁，以及 b1 测试调用链。

审查期间作者仅更新交付/计划记录，并补充 `docs/architecture/current.md`、`docs/architecture/reference-boundary.md`、详细计划和原调查的链接；这些增量已读。8 份生产/测试文件始终保持原审查 SHA，冻结参考目录无 diff。身份和增量分别保存于 [intake.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/intake.json)、[completion-identity.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/completion-identity.json)、[final-scope.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/final-scope.json)。

## 合同与恢复核对

|检查点|代码证据与判断|
|---|---|
|授权与锁|[tasks.py:289](../../src/ergora/tasks.py#L289) 复用严格 confirm/预算校验，短 `BEGIN IMMEDIATE` 核当前 revision 后返回；远程 dispatch 在事务外。[reference_task_reconciliation.py:292](../../src/ergora/reference_task_reconciliation.py#L292) 在准备阶段非阻塞取得原 task 锁，远程阶段继续持该任务锁。|
|原始所有权|[reference_task_reconciliation.py:136](../../src/ergora/reference_task_reconciliation.py#L136) 组合既有 `_Inspection`/原提交，保存并重验完整原 tracker/local-cli/task/spec claim；登记根、原 spec/memo/run 和完整 history 沿 b1 原所有者验证。|
|fence 前后|[reference_task_reconciliation.py:256](../../src/ergora/reference_task_reconciliation.py#L256) 在完整原事实及 scope 校验后保存 attempt，再调用原不可变 fence；发布后再次完整检查。缺请求/可信终态回执/产物、额外请求或孤立回执、已知后继 run 都不能进入 release。没有采信原 fence 的目录空集 confirmed。|
|原 outcome 与清理事实|[reference_task_reconciliation.py:168](../../src/ergora/reference_task_reconciliation.py#L168) 保留 COMPLETED 的真实原 outcome；其他闭合状态保持 outcome 为 null。独立 evidence 绑定 checkpoint、历史 job 集合、每个 job 的原请求和回执摘要及匹配 fence，没有把 CANCEL_UNCONFIRMED 改为 BLOCKED。|
|释放摘要与所有者|[reference_task_reconciliation.py:213](../../src/ergora/reference_task_reconciliation.py#L213) 的 native 条件与原 `agent_platform.ingress.release` 一致：REVIEW_READY，或 BLOCKED 且 fence.confirmed 为 true。适用时保留原 outcome SHA，其余使用独立 evidence SHA；先保存 evidence，再重验 claim/ledger 存在，只调用原 `IngressLeases.release`。没有复制 SQL、重建丢失 ledger 或释放别的 claim。|
|中断恢复|[reference_task_reconciliation.py:234](../../src/ergora/reference_task_reconciliation.py#L234) 重算并验证本地不可变记录；resume 重查原事实，重复写入须相同，提交后丢响应沿同一摘要幂等 release，再补 result。已完成记录按历史事实返回。|
|只读入口|[reference_task_reconciliation.py:288](../../src/ergora/reference_task_reconciliation.py#L288) 的 status 在锁/远程分支前返回，仅验证本地记录；原 inspect 路径仍只读。GET 不发布 fence、不打开 ingress ledger 或调用 release。|

新增私有 `_Reconciliation` 的单一生产入口是同文件 main，职责是完整持久恢复算法，留在现有 reconciliation 所有者内有充分依据。其小方法分别服务意图/检查点/证据/回执的创建与恢复校验，未新增投机复用层。`tasks` 用例有真实 CLI/Web 消费者，`reference.task_reconciliation` 是既有专用进程边界，`TaskRunDecisionPayload` 由批准和对账两个实际接口共用。

对 persisted JSON 的字段/摘要校验、缺 ledger、claim 漂移、history 完整性、两类目录、回执及产物守卫都有可达的损坏/中断/外部输入场景。保存后重验与外部查询并非可随意合并的重复断言。新增集成反例覆盖不同资源提交边界；纯输入反例保持在轻量模块，Linux skip 保持模块级，无需删除这些保护来缩短回归。

## 独立检查与证据

独立源码定向执行：

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q --tb=short tests/test_task_reconciliation.py -k 'cleanup_releases and repository-governance or each_interruption and after-release-commit or missing_original_evidence and all-requests or recovery_rechecks and receipt or successor_detected'
```

**5 passed、51 deselected，36.54 秒。** 分别覆盖原 CANCEL_UNCONFIRMED 精确释放、SQLite commit 后响应丢失恢复、全部原请求缺失后补齐、保存 evidence 后回执漂移拒绝、fence 发布后后继 run 拒绝。原始命令/环境/计时与输出见 [targeted-command.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/targeted-command.json) 和 [targeted.log](../../.ergora/checks/f3-task-reconciliation-write/reviewer/targeted.log)。`git diff --check` 通过。

另读取作者实际 65 项输入/读取、首轮 46 passed 后测试 regex 失败、修后 9 passed/46 deselected、journal 1 passed/55 deselected 的原始范围。首轮是探索性执行且测试仍在增补，没有将其计作当前固定源码完整验收；没有将 build-initial 计作最终包。

对最终候选 wheel `c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb` 重新计算 ZIP 内容和源码、两安装的全部 347 文件哈希，全部一致。只读重验两模板 CLI 旅程实际留下的 intent/attempt/evidence/result、原 outcome、各回执/产物及 SQLite ledger：均保留 CANCEL_UNCONFIRMED，原 claim 已释放且 ledger 摘要等于清理 evidence SHA。证据见 [artifact-check.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/artifact-check.json)。

已读 27 次 CLI 的脚本断言、实际日志和记录；该旅程用独立无 SDK 控制安装、登记的完整运行时、真实 SDK codec/分页、真实 FileAdapter/SQLite 和可控 RPC。独立核验是重新计算身份与最终事实、审查执行记录，没有重复运行 27 次旅程。记录的 4×4.5 秒 connect 延迟下，另一项目写入 19.92 毫秒、同 task 1090.03 毫秒 busy，均在对账完成前；这支持远程阶段不保留控制 SQLite 写锁。

## 性能与待验边界

代码成本是 fence 前后两次完整历史/文件检查，加原 FileAdapter.fence 自带的请求/回执扫描；每次正常完成最多三轮回执产物哈希读取。原合同最多 24 个 work unit，正常工作流 unique job 数有界；管理员显式操作沿已有超时/父进程预算执行。未发现新增后台轮询、全项目扫描、跨项目远程持锁或第二套作业监控。较大产物和高延迟 history 的端到端性能没有在本次审查测量，不能从小 fixture 推导吞吐或启动收益。

文件协议仍以可信执行器遵守 task fence、独立 walltime 和不可复用 task ID 为条件；本地 task 锁无法原子占有远端 workflow ID。源码保留发布前后对已知后继的检查，文档明确此边界。可控 RPC 与异常注入不替代真实 workflow/模型、系统进程已停或操作系统掉电持久性的证明。真实两模板六阶段、取消进程与 worker 重启仍归 F3.4c/d/e；本次未运行它们，也未自行运行完整发行回归或两 OS CI。

初轮审查无阻塞 finding，无需源码修正。其时待验的最终包回归、精确两 OS CI 和最终身份已在下节收齐。

## 最终发行、CI 与远端只读复核

2026-11-03 追加最终复核。最终生产/测试候选为 [`7139d1a85cdce13689d75471620da8dd143156a8`](https://github.com/626619403/Ergora/commit/7139d1a85cdce13689d75471620da8dd143156a8)。重新读取该提交的 8 份生产/测试 blob、当前文件、candidate-identity 及初轮 review-source-identity，全部 SHA 相同。基线到候选的冻结参考目录无差异；工作区增量属于文档状态和后续 c/d 旅程记录，没有生产/测试改动。

重新计算 wheel `c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb` 及其 347 个包文件，与源码、完整开发安装和独立基础安装一致。两解释器实际导入均来自 `site-packages/ergora`，分发元数据的非 editable wheel 摘要也匹配；开发 Python 3.11.15/35 个分发包，基础 Python 3.12.3/9 个分发包，当前版本列表与 environment-v1 原记录一致。

最终包原始回归命令覆盖 `tests`、原 contracts/portable、workflow AdapterTests 和 runtime；PYTHONPATH 仅为原 vendored platform 路径，没有加入 `src` 应用目录。实际 exit code 0，日志完整结束为 **711 passed、19 skipped、36 subtests passed、1 warning，1722.63 秒**；唯一警告为既有 StarletteDeprecationWarning。已检查原命令、运行器、环境记录和完整日志，没有重跑测试或安装。原始证据为 `packaged-regression-v1-command.json/log` 和 `environment-v1.json`，本次校验保存了它们的字节数与 SHA。

独立重新请求 [官方 CI 41621015706](https://github.com/626619403/Ergora/actions/runs/41621015706) 及两个官方 job 页面，均 HTTP 200，run 状态 Success，提交链接和全部必需步骤 log URL 绑定完整候选 SHA：

|官方 job|必需步骤与结论|
|---|---|
|[Ubuntu / Python 3.11，125866432315](https://github.com/626619403/Ergora/actions/runs/41621015706/job/125866432315)|Build and install wheel、Packaged reference identity、Native application regression：全部 success|
|[Windows / Python 3.12，125866432579](https://github.com/626619403/Ergora/actions/runs/41621015706/job/125866432579)|上述三项，加 Windows PowerShell 5.1 installer and upgrade：全部 success|

同时核对候选的 portability workflow：Linux 运行应用及适用的原生套件；Windows 运行其适用范围，Linux 专属测试沿原 skip 合同。两 OS 结论依据官方完成状态、各必需步骤及精确 SHA，不把本地 711 项计数套用于 Windows，也不把可控 RPC 扩大为真实服务/模型验收。

独立 `git ls-remote --heads origin refs/heads/refactor/architecture-foundations` 在 **2026-11-03 10:57:23 UTC** 返回原候选 `7139d1a85cdce13689d75471620da8dd143156a8`。实时官方 HTML、远端原输出、重新核算的身份与原始证据摘要分别保存在 [final-live-sources.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/final-live-sources.json)、[final-live-remote.txt](../../.ergora/checks/f3-task-reconciliation-write/reviewer/final-live-remote.txt)、[final-review.json](../../.ergora/checks/f3-task-reconciliation-write/reviewer/final-review.json)；可复查校验器为 [final-verify.py](../../.ergora/checks/f3-task-reconciliation-write/reviewer/final-verify.py)。大体积原始记录保留在私有 checks 目录。

**最终判断：b2 源码、结构、发行和候选身份门禁全部满足，无未解决 finding，可以登记本切片完成。** 后续 c/d 已启动的两条真实 run 未纳入本次验收；真实模型、两模板六阶段、取消进程、worker 重启及完整 F3 综合收口仍由 c/d/e 自行提供证据。可信文件协议、本地锁、task ID 不可复用和大产物性能的前述边界保持。
