# F3.3c1 精确计划批准：独立审查

日期：2026-11-03。审查者：独立 fresh-context Codex 审查上下文 `f3_task_approval_review`；没有参与实现，没有递归委派。按 `review-pr` 与 `maintainable-project-delivery/references/independent-review.md`，先读原始需求、基线差异和新增文件，再对照作者记录。审查仅写本文件，未修改源码、安装依赖、提交或推送；未运行全套回归。

## 范围与身份

分支 `refactor/architecture-foundations`，HEAD/比较基线 `d47e97b172c425b2400465593dae6916f225c30d`；本次候选为其上的未提交变更。检查原始 tracked diff 和三个新增源码/测试文件：

- `src/ergora/cli.py`、`reference.py`、`reference_task_submission.py`、`tasks.py`、`web.py`，新增 `reference_task_approval.py`。
- `tests/test_architecture_boundaries.py`，新增 `tests/test_task_approval.py`、`tests/fixtures/task_approval_client.py`。
- `README.md`、`docs/USAGE.md`、`PROJECTS.md`、`AGENT_BACKENDS.md`、`PLAN.md`、详细计划、当前架构/reference 边界、决策设计和批准交付记录。

必要邻接读取包括 `_Creation`、`VerifiedSpecClient`、`State/file_lock`，冻结的原 `DevelopmentTransport`、`DevelopmentWorkflow`、`FileAdapter.authorize/publish`、`agent_platform.cli/core`，及创建/提交/运行测试和相关夹具。冻结 reference 目录相对基线没有差异。

已核对候选 wheel `0532122914082e995568df20396182a45e9109f2b11d046d6016da86b588b7e6` 的 `package-identity.json`：344 文件、两安装，相关源码摘要与本次读取一致。核心新增批准模块 SHA256 为 `a3d47ff7517959d1ab2f7f6cbb07079664a304323640071acc9bd4dc0a965912`；提交模块 `4a738e520c2069f1d9a4b9861475bef7b296e642ec4f5b2a3e3726f54654eab2`，tasks `a23ba9ff5305e438a163a656db41909f682581c45ba52e893dd9e3b4d6ada851`。发行身份核对是记录检查，不替代本审查的源码定向执行。

## 结论

需求符合性：**本次已检查的 c1 实现范围内通过，无确认 findings**。可维护性/代码结构：**通过，无需为本段增加抽象或移动所有权**。没有待修复的阻塞源码问题。这不是完整 F3、真实服务验收或最终发行/CI 收口结论。

关键证据如下：

- CLI/API 调用同一 `tasks.approve/approval/resume_approve`。当前 revision、run、精确 SHA、严格确认和预算由用例/请求模型守卫；合法 decision ID 由既有 slug 边界处理。只接受已完整发布的统一创建及原提交回执；所有权检查复用原创建/提交快照，没有热换原角色。
- `tasks._approval_prepare` 的写保留只覆盖本地准备；批准进程准备阶段不加载连接环境或进行 RPC，且以非阻塞方式获取原任务锁。网络阶段在事务结束后仅持同任务锁。意图固定控制目录/登记/creation/submission/spec/run/plan/actor/receipt/24h expiry。
- 原 `adapter.publish` 发布与原 CLI 相同格式的 human/owner 回执；原 workflow handler 和 `FileAdapter.authorize` 仍分别拥有信号采纳与授权。actor 变化、过期、回执漂移/撤销拒绝派发；授权时仍检查有效期和撤销。检查当前 phase/plan 后发生竞争时，也只报告 requested，`approval_accepted/execution_success` 保持 null。
- attempt 在 signal 之前，result 在 SDK 应答之后；本地读取按 result、attempt、owner 回执顺序验证不可变证据。重复同 ID 只读，不续期或重发；prepared 的显式 resume 重查原 run/spec/memo/phase/plan，unknown 的 resume 仅查固定原 run history。NOT_FOUND、错误、超时或未找到信号没有转回派发分支。
- `VerifiedSpecClient` 通过 canonical SHA 区分 JSON 类型并拒绝非有限值；恢复使用实际客户端 converter 解码信号，要求原 signal 名及精确 request/plan/receipt payload，额外字段也不作为同一证据。真实 SDK 的 handle 固定 run，分页器只保留当前页；100 事件分页及外层总 timeout 没有把全历史加载成列表。
- `reference_task_approval` 是独立原生操作的进程/journal 所有者，私有方法对应本地状态校验或派发/恢复算法。`reference._task_operation` 被提交和批准两个生产入口调用；`_Submission.lookup_run` 被原提交恢复和批准调用，负责同一 spec/memo 身份。没有仅靠测试或假设未来使用建立的共享接口，也没有增加第二套授权器或工作流。
- 新守卫覆盖外部输入、持久状态、原运行身份或有意义的失败；未发现要求删除的不可达分支/静默 fallback。路径仍使用既有有界/no-follow reader 和安全根检查，journal/回执仍由原不可变、临时文件加原子链接写入；权限来源保持本地 OS/可信文件目录，公开文档明确没有团队身份认证。

## 本次独立检查

执行环境：Linux 当前 Docker，Python 3.11.15、temporalio 1.34.0；源码检查显式 `PYTHONPATH=src`。`bwrap` 无法启动后，按既有授权在当前 Docker 执行只读/定向检查。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_task_approval.py -k 'exact_owner_approval or signal_ack or reconciliation_requires or missing_original_run or owner_receipt_drift or remote_wait'
```

结果：**6 passed，30 deselected，39.60 秒**。覆盖稳定决策重复、冻结角色、phase 竞争不冒充采纳、精确信号恢复、原 run NOT_FOUND 不重发、撤销回执拒绝，以及远程等待期间其他项目真实写入/同任务准备拒绝。

另通过 stdin 运行四个独立内存探针：直接调用本次 `_Approval.reconcile`，使用真实 SDK `WorkflowHandle`、`WorkflowHistoryEventAsyncIterator`、`DataConverter` 和 protobuf 事件，仅替换 history RPC，并以断言固定 workflow/run、page_size=100 和连续 page token。结果：

|输入|读取页数|结果与写入|
|---|---:|---|
|前两页为不同 receipt/request，第三页为精确原 signal|3|requested，仅写第三页 event ID 的 history 回执|
|三页均不匹配，末页 payload 多一个字段|3|unknown，不写 result|
|第二页 RPC UNAVAILABLE|2|异常保留未知，不写 result|
|首个 RPC 等待超过外层总预算|1|总超时，不写 result|

该探针隔离了分页/解码算法，没有替代完整所有权链的测试，也没有真实 Temporal 服务。`git diff --check` 通过；未执行全套回归。

## 性能与作者证据核对

已读 `.ergora/checks/f3-task-approval/` 下 `lock-contention.py/json`、`journey-performance.py/json`、`package-identity.json`，以及先前原 authorize/handler 的 `contracts-probe.json`。这些是作者执行证据，与以上独立运行分开记账。

18 秒受控 connect 等待探针确实使用已装候选包、真实共享 SQLite/State 和原任务锁：其他项目写者 14.70ms 完成，同任务第二 prepare 804.22ms 明确拒绝，两者均早于远程完成，随后其他项目可继续写到 revision 3。代码与测量支持新批准入口不持全库写锁等待 RPC；没有证明旧 F3.3b 已修，F3.3d 仍需独立迁移与验证。

基础 Python 3.12.11 环境无 FastAPI/Temporal/GEPA，两模板 86 次 CLI 脚本对返回值、signal 次数和文件字节不变作了断言。首次 start/approve、丢应答恢复使用另一个含 SDK 的解释器和受控网络端口。重复 approval/approve/resume-approve 每操作每模板 10 次，中位约 1.09–1.20 秒、最大 1.67 秒，包含 CLI/子进程/SDK 导入及合同校验，并行完整回归。该成本有明确测量边界；没有同条件旧功能基线，也没有真实网络/模型性能或吞吐提升结论。

## 剩余验收

审查截止时最终完整发行回归仍由作者执行，精确候选两 OS CI、最终独立核对、提交和远端身份尚待完成。本审查不预先接受这些结果。已安装两环境分别是含 SDK 的 Python 3.11.15 和仅基础依赖的 Python 3.12.11，不能合写为同一 Python 版本。

真实 Temporal 分页/历史保留/权限错误、真实 worker 授权 activity 与新两模板六阶段/导出/重启旅程未在本次运行，归 F3.4；SDK 夹具、内存探针和原 authorize 直接调用不替代它们。大历史服务延迟/吞吐没有实测。c2 取消与旧提交锁迁移 d 均不属于 c1 通过范围。

## 最终本地发行复核：b3b7d65

2026-11-03，由同一独立审查上下文复核本地候选 `b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b`，其直接父提交为原审查基线 `d47e97b172c425b2400465593dae6916f225c30d`。本次授权仅核对最终本地证据并追加本报告；没有重跑全套、安装依赖或修改源码，也没有核对或预认远端/CI。

本地发行结论：**通过，无新增 findings，初审的需求符合性和结构/可维护性结论保持**。精确提交、已审源码、最终 wheel 和已记录运行证据之间的身份链已核实：

- 独立以首次审查记录的 9 项源码/测试 SHA，逐项比较候选提交内容、当前工作区和 `candidate-source-identity.json`，全部一致。将该文件到 SHA 的映射按 key 排序，以 `json.dumps(..., sort_keys=True, separators=(',', ':'))` 编码后重算聚合，得到 `d106eef37092ffcc58da083309104d8e7fac0dad622fa36a5e68f3642a9f25a2`，与作者记录一致。
- 独立只读重算 344 个包文件摘要：`git archive` 读取的候选提交、`src/ergora` 工作区、最终 wheel、开发安装和基础安装逐文件完全一致，也与 `package-identity.json` 一致。实际 wheel SHA 为 `0532122914082e995568df20396182a45e9109f2b11d046d6016da86b588b7e6`。复核没有运行会覆盖原证据的 `verify-package.py`。
- 分别在两套安装中直接导入应用并执行只读 `reference.verify()`，均返回 PASS、283 文件、`runtime_started: false`。开发环境实际从 Python 3.11.15 的 site-packages 导入；基础环境实际从 Python 3.12.11 的 site-packages 导入，且 FastAPI/Temporal/GEPA 均不存在。
- 已读完整回归日志首尾，确认完整成功摘要为 **477 passed、19 skipped、36 subtests passed、1 warning，566.19 秒**。warning 是 FastAPI 测试客户端的 Starlette 弃用提示。作者记录执行会话 exit 0；本审查核对原始日志与包身份，不冒充独立重跑。原始日志 SHA256：`07dd226d06e719468785198cd56b93e7012ed05b9deb296c5e6b84c4cba7f100`。

作者补充的实际完整回归命令如下；日志本身只有 pytest 输出，命令来源与日志结果分开记录。其套件选择与 `.github/workflows/portability.yml` 的 Linux 选择一致，`PYTHONPATH` 只提供原 reference 平台，没有应用源码顶层 `src`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ergora/data/reference/platform/upstream/platform .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests src/ergora/data/reference/platform/upstream/platform/tests/test_contracts.py src/ergora/data/reference/platform/upstream/platform/tests/test_portable.py src/ergora/data/reference/platform/upstream/platform/tests/test_workflow.py::AdapterTests src/ergora/data/reference/platform/upstream/platform/tests/test_runtime.py > .ergora/checks/f3-task-approval/wheel-regression.log 2>&1
```

再次核对旅程/锁脚本及原始日志，两个 log 可解析为与各自 JSON 记录完全相同的对象，且均绑定上述 wheel。两模板 86 次 CLI 的重复无 RPC/重发及原文件字节不变、18 秒等待下其他项目 14.70ms 写入/同任务 804.22ms 拒绝的限定结论保持。所读脚本 SHA256 分别为 `journey-performance.py: ea2e7e413a5af6c8111d75a8ffb00ffd4d788b7ea8d447f6009d7757189a375c`、`lock-contention.py: 5793caf2ae74ea576354f7beb4368a6e4a1799a88651cd807605246422c4416b`。未重跑这些旅程或从其结果推导真实服务/模型性能。

候选的计划/手册保留 c1 的精确 run/plan/decision 与 requested 仅投递事实边界；F3.3d 仍登记为旧提交锁迁移，c2 的新增内容明确只是下一切片设计、没有生产实现，F3.4 两模板真实六阶段/导出/重启仍待实施。精确提交 `git diff --check` 通过。此前“完整发行回归待完成”是初审截止状态，由本节的已核完成结果更新；**精确两 OS CI、远端分支身份及相应最终独立核对仍待后续单独提供与审查**。

## 精确 CI 与远端最终复核

2026-11-03 03:47 UTC，同一独立审查上下文完成 c1 最终核对。结论：**精确候选 CI、远端身份和最终独立审查通过，无新增 findings；c1 在记录的验收范围内完成**。

此时作者工作区已进入 c2，包含未提交取消代码。本节只以 `git show/archive b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b` 读取 c1 源码，没有拿当前 `src` 与 c1 比较，也没有审查或接受 c2。再次重算固定提交的 9 项源码/测试，聚合仍为 `d106eef37092ffcc58da083309104d8e7fac0dad622fa36a5e68f3642a9f25a2`；344 个包文件与既有 `0532122914082e995568df20396182a45e9109f2b11d046d6016da86b588b7e6` wheel、当时仍为 c1 的两套安装逐文件一致。没有重新安装或运行全套回归。

独立执行只读 `GIT_TERMINAL_PROMPT=0 git ls-remote origin refs/heads/refactor/architecture-foundations`，exit 0，得到：

```text
b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b refs/heads/refactor/architecture-foundations
```

已读并独立解析作者保存的官方 actions/run/job 原始 HTML，重算 `ci-html-status.json` 声明的来源字节数/SHA，均一致；actions 内嵌选择记录同时绑定 `.github/workflows/portability.yml`、该分支、精确完整提交和 run `41572513289`。随后另行只读实时 GET 官方 run 与两个 job URL，均返回 HTTP 200，确认整体 Status 为 Success，以下必需步骤均有 `success`、`data-job-completed`，且各自 `data-log-url` 包含本次完整提交 `/commit/b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b/checks/JOB_ID/logs/`：

|官方 CI 来源|已核必需步骤|
|---|---|
|[Portability run 41572513289](https://github.com/626619403/Ergora/actions/runs/41572513289)|精确提交链接与整体 Success|
|[Ubuntu 3.11 / job 125708461054](https://github.com/626619403/Ergora/actions/runs/41572513289/job/125708461054)|Build and install wheel；Packaged reference identity；Native application regression，三项全部 success|
|[Windows 3.12 / job 125708461321](https://github.com/626619403/Ergora/actions/runs/41572513289/job/125708461321)|以上三项及 Windows PowerShell 5.1 installer and upgrade，四项全部 success|

CI 原始缓存路径为 `.ergora/checks/f3-task-approval/ci/`，已核 `ci-run-latest.html` SHA256 `798cda5b338419c85641505024d6a73cc892bf3215fddca6ddc010f9bee8d715`、Ubuntu job HTML `6771fa504742ac3819cb9f609e02c0927a7ba22e7676b57cae35df4478988779`、Windows job HTML `4270b385050fef391cb6f9599fb60278dd7df752fc4a5266bbb53d5e8fa62d47`。作者因公开 API HTTP 403 rate limit 使用官方 HTML；本审查独立的实时 HTML 核对也通过，没有将 API 受限解释为 CI 缺失。HTML 证明工作流/步骤状态，没有从中推导未公开的逐测试计数。

以上更新前节“精确 CI/远端待验”状态。c1 的 Linux 477 项/36 子测试、本地两安装/冻结身份、86 CLI 和并发证据与精确两 OS CI 分别记账；真实 Temporal/worker 授权及新的两模板六阶段/导出/重启仍按 F3.4 验收，旧提交锁迁移 d 和当前 c2 均不随 c1 结论自动通过。此次只追加本报告，没有修改源码、外部应用或远端。
