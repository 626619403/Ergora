# F3.3c2：取消请求的独立源码、结构与性能审查

日期：2026-11-03。审查者：独立上下文 `/root/f3_task_cancellation_review`；未参与本段实现，未递归委派。依据项目 `AGENTS.md`、`review-pr` 与独立 maintainability review 规则，先读原始差异，再读交付说明及实际调用方。

## 结论与身份

- **需求符合性：源码审查通过，范围内无确认 finding。** 原取消 guard、不可变请求、signal 前检查点、closed 无信号回执，以及 unknown 只按固定原 run 的完整 payload 对账均保持要求。此结论不代表 F3.3c2 最终发行或 F3.4 真实服务验收完成。
- **结构与可维护性：通过。** 新文件拥有取消的专用原生进程与 journal，实际复用提交所有权和 history 算法；没有第二套取消引擎、通用基类、DB 表或新依赖。
- **性能：锁分段与流式查询设计通过审查；基础 CLI 实测边界已核。** 未发现新增全库锁覆盖网络等待的路径；18 秒并发实测仍待核，本次没有声称真实网络性能或吞吐改善。

源码基线为 `b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b`，分支 `refactor/architecture-foundations`。审查结束时 HEAD 为只追加 c1 文档的 `3c5d91a`，c2 仍为未提交源码。精确检查了以下 11 个变更文件：

- `src/ergora/{cli,reference,reference_task_approval,reference_task_runtime,reference_task_submission,reference_task_cancellation,tasks,web}.py`。
- `tests/test_architecture_boundaries.py`、`tests/test_task_cancellation.py`、`tests/fixtures/task_cancellation_client.py`。

按上述相对文件名映射到各文件 SHA256，再以 `sort_keys=True, separators=(',', ':')` 编码该映射所得审查身份为 `b215f9553a3ba8ac716b70bd86ecf285af7eb1d3c0fc6e92956078dd023255bd`；新增取消模块 SHA256 为 `322d3bc0a71bc838f69dce757def795a47024c34b82be4937aecd050998bed67`。

另读创建所有者、State/文件锁、原 `DevelopmentTransport`、`DevelopmentWorkflow.request_cancel`、底层不可变写入、CLI/API 调用方和公开手册/当前架构差异。c1 审查报告尾部追加属于前段验收，没有作为本段实现变更。

## 正确性与结构证据

`reference_task_cancellation.py:103` 的局部 `RecordedCancellation` 仍调用原 `DevelopmentTransport.cancel`。其 lookup 先执行原 spec/固定 run 校验，再核原提交 memo；只包装原 transport 实际调用的 signal。原 RUNNING guard 和原 handler 仍拥有业务语义，包装不查询另一个当前 run，不 terminate、不改 ledger/fence/lease。signal payload 保留原 request/reason，并附加完整意图 SHA；attempt 在调用 SDK 前不可变保存，result 在应答后保存。丢应答、结果写失败或客户端超时留下 unknown。

`reference_task_cancellation.py:71`、`:78` 对两种回执做互斥校验：`not_sent` 必须有合法闭合枚举且没有 attempt；应答/history 回执必须有匹配的 attempt。RUNNING 不能构成闭合回执，history event ID 必须是正整数且拒绝 bool。关闭检查后中断可保留 prepared；显式 resume 重查原 run 后再决定是否发 signal。requested/already_closed 都保留 `cancellation_confirmed: null`、`execution_success: null`，没有外部停机成功推断。

`reference_task_cancellation.py:142` 的同 ID 重复只读既存状态，拒绝改原因；派发校验原 actor。prepared 仅经明确 resume 继续；有 attempt 的恢复只走 `reconcile`，NOT_FOUND、RPC 错误、总超时或未匹配事件都没有回到派发分支。原提交/创建及当前修订检查沿既有边界保留，错误 run、未提交或旧入口任务不能被采用。

共用提取有实际所有者与消费者：`_Submission.submitted()` 分别被批准与取消 prepare 使用；`verify_run_owner()` 同时服务既有提交 lookup 和取消的原 transport lookup；`reference_task_runtime.find_signal_event()` 分别由两种操作恢复调用。后者使用真实 converter，按 signal 名和完整 canonical JSON 比较，包含取消操作 SHA，额外字段也不被认作同一事件。c1 的 owner 回执、expiry、phase/plan guard 和 signal 内容未被泛化或改变。`tasks._decision_prepare` 是用例模块内的修订/确认/预算准备函数，Web 的恢复模型只是共同正文 schema；取消没有继承审批业务。

## 独立验证

使用 Python 3.11.15、当前源码及已存在 SDK；未安装依赖、未运行全套、未修改生产源码或提交推送。两个独立脚本最初在临时目录运行，随后按追加授权原样保存于 `.ergora/checks/f3-task-cancellation/reviewer/`。`observed-results.json` 记录脚本 SHA、实际命令和退出码。`*.stdout.log` 是已完成工具调用捕获 stdout 的原样保存，没有原始磁盘日志，也没有为保存证据重跑。

`history-probe.py` 直接调用本次 `_Cancellation.reconcile`，使用真实 SDK `WorkflowHandle`、`WorkflowHistoryEventAsyncIterator`、`DataConverter` 和 protobuf 事件，仅替换 history RPC，并断言 workflow/run、每页请求 100、连续 page token 和 20 秒 RPC deadline。五个探针均退出 0：

|场景|实际取页|结果|
|---|---:|---|
|第一页同 reason 无 marker；第二页其他操作 SHA/多余字段；第三页完整匹配|3|requested，仅保存第三页 event ID=300 的 history 回执|
|末页仍为另一 request SHA，全部不匹配|3|unknown，无 result 写入|
|第二页 RPC UNAVAILABLE|2|异常，原 attempt 不变，无 result 写入|
|首个 RPC 等待超过外层总预算|1|总超时，原 attempt 不变，无 result 写入|
|首个分页为空但带 next token，后续第三页完整匹配|3|继续分页并正确补 history 回执|

`test_journal_probe.py` 复用项目的创建/提交及网络端口 fixture，实际调用原 transport/handler；断言由独立脚本新增。结果 **1 passed in 25.05s**。21 种矛盾 journal 均明确拒绝：意图的 bool revision/schema、错误 run/request/submission SHA、空 reason/actor；attempt 的错误 run/schema/signal SHA；result 的错误 delivery、ack 带 event ID、额外字段；缺 intent/attempt；history event ID 为 bool/0；closed 状态为 RUNNING/未知枚举/bool，以及 closed 同时出现 attempt。恢复合法字节后状态可读；这些 status 读取没有网络调用，合法闭合回执的同 ID 重复也没有新网络调用。

独立 `git diff --check` 通过。另只读核对作者 `.ergora/checks/f3-task-cancellation/source-first.log`：五个相关文件集合的联合检查为 **152 passed，1 个现有 Starlette/httpx 弃用 warning，593.96 秒**。这是作者运行证据，与上述独立探针分开记账。

## 性能边界与剩余验收

prepare 在当前 revision 的控制库写保留下，只执行本地合同读取/意图保存，并非阻塞取得任务锁；网络 dispatch/resume 已离开控制库事务，只持原任务锁。原描述结果的 memo 解码没有额外 RPC。新增持久成本是必要的检查点和回执写入；闭合分支只保存无信号结果。history 每次请求 100 个事件，SDK 只保留当前页，算法扫描到匹配或结束；外层总预算和父进程回收预算仍生效。没有全量收集 history，但长历史扫描成本仍随事件数增长；真实服务的大历史延迟/吞吐未实测。

只读核对作者包清单：候选 wheel SHA256 `4abad37df7b16992dd897d524e67e7d47c538bd43dca915e070cb81a4a5078d4`，记录 345 文件及两安装；本次 8 个变更生产模块的源码 SHA 均与该清单一致。本轮没有重新计算整包/两安装的全部文件，也没有把汇总文件代替最终验收。

随后只读审查作者已完成的 `journey-performance.py/json/log`：Python 3.12.11 基础环境缺 FastAPI/Temporal/GEPA，通过另一含 SDK 的 Python 3.11.15 原生解释器调用。两模板共 90 次 CLI；首次 start/cancel、丢应答/history 恢复及闭合由受控网络端口执行，每模板 1 次 start、2 次实际 signal，闭合没有新 signal。各模板的 cancellation/cancel/resume-cancel 每项重复 10 次，使用真实 CLI 的本地记录路径；返回值相等、原任务与操作文件字节不变、calls 日志不增加均有脚本断言。

|模板|cancellation 中位 ms|cancel 中位 ms|resume-cancel 中位 ms|
|---|---:|---:|---:|
|repository-governance|1198.07|1249.83|1202.85|
|large-change|1242.61|1220.86|1203.21|

重复样本最大 1332.02ms，含 CLI/原生子进程启动、SDK 导入和合同校验，与完整回归并行。该测量限定于本地重复路径，没有网络/模型性能结论，也没有同条件旧功能基线。候选 11 文件身份与本报告摘要完全一致。

审查截止时，作者的最终包完整回归和 18 秒延迟并发探针仍在执行；精确两 OS CI、最终独立核对、提交及远端身份也待完成。旧提交的全库锁迁移仍归 F3.3d。真实 Temporal 服务历史/权限/保留期、worker 和外部作业停机、原 fence/租约终态、两模板六阶段/导出/重启综合旅程归 F3.4；受控网络端口、直接 handler 和内存 SDK 探针均不替代这些检查。当前没有阻塞源码审查的 finding；以上未验项仍是所属节点的验收条件。

## 最终本地发行复核：c3113ad

2026-11-03，由同一独立审查上下文核对最终本地候选 `c3113ad119c72ed933876ddae95d3c849c804852`。直接父提交为仅 c1 文档的 `3c5d91a44b00f973700d737d6e86aaf0ca59e97b`，生产源码基线仍为 `b3b7d65`。本轮授权只读核对最终本地工件并追加本报告；没有重跑全套、安装、修改源码或推送。

**最终本地发行核对通过，无新增 finding。** 下列已完成证据替代前文当时尚待完成的本地项；精确两 OS CI 与远端核对继续单独验收。

独立读取候选的 Git archive，按相对文件名和 SHA256 重算全部 345 个生产/资源文件，与当前 `src/ergora`、候选 wheel、开发安装和基础安装逐项一致，额外文件/缺失文件均参与比较，仅排除字节码缓存。11 项已审源码/测试同时与提交、当前字节及 `candidate-source-identity.json` 逐项一致，聚合仍为 `b215f9553a3ba8ac716b70bd86ecf285af7eb1d3c0fc6e92956078dd023255bd`。wheel 完整 SHA256 仍为 `4abad37df7b16992dd897d524e67e7d47c538bd43dca915e070cb81a4a5078d4`。此处独立计算，没有调用会改写作者摘要的 `verify-package.py`。

分别在两个已安装解释器下确认实际导入路径、发行安装元数据与依赖可用性：开发环境 Python 3.11.15 含 FastAPI/Temporal/GEPA；基础环境 Python 3.12.11 三者均缺。两者均从 wheel 非 editable 安装，各自 `reference.verify()` 为 PASS、冻结 283 文件、原 source zip SHA `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`。没有将两个 Python 版本合写为同一环境。

已核 `wheel-regression.log` 与 `wheel-regression-command.json`：退出码记录为 0，最终 **522 passed、19 skipped、36 subtests passed、1 个已有 Starlette/httpx 弃用 warning，832.89 秒**。实际命令为：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ergora/data/reference/platform/upstream/platform .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests src/ergora/data/reference/platform/upstream/platform/tests/test_contracts.py src/ergora/data/reference/platform/upstream/platform/tests/test_portable.py src/ergora/data/reference/platform/upstream/platform/tests/test_workflow.py::AdapterTests src/ergora/data/reference/platform/upstream/platform/tests/test_runtime.py
```

PYTHONPATH 只提供原 reference 平台；仓库没有 pytest 配置或 conftest 将顶层 src 注入应用路径。以相同 PYTHONPATH 独立核对应用实际导入来自开发安装的 `site-packages/ergora`，安装内容已与候选逐文件核同。该发行回归与先前显式 `PYTHONPATH=src` 的 152 项源码检查身份不同，不混用两次结果。

已读 `lock-contention.py/json/log`，JSON 与原始 stdout 完全一致，wheel 与安装路径绑定本候选。脚本使用实际 State、共享 SQLite、另一项目的真实 bind 写者和原任务文件锁；只在受控 SDK connect 端口加入 18 秒等待，取消预算 25 秒。另一项目写者 **20.26ms** 完成到 revision 2；同任务第二个 prepare **846.56ms** 内明确返回 errno 11 busy，之后另一项目继续写到 revision 3。脚本分别断言写者和同任务拒绝均早于原远程结果；总时长 **19774.38ms**，原请求为 requested，确认字段仍为 null。数据支持本取消入口没有持控制库写锁等待该远程阶段；没有证明真实 RPC 延迟/模型收益，也没有修复旧 b 提交路径。

此前已核的 `journey-performance.py/json/log` 未改；再次确认候选 SHA、90 次 CLI、两模板各三项本地操作各 10 样本、每模板一次 start/两次 signal 与已记数值一致。最终 README、USAGE、PROJECTS、AGENT_BACKENDS 和当前架构仍将 requested/already_closed 与外部停机分开；PLAN 和详细节点表没有提前把 c2 的最终 CI 标为完成，d 保持调查设计、F3.4 保持待实施。交付记录较早段落仍保留过程中的 pending 描述，已提示作者在最终收口时同步当前摘要；不影响本地工件结论。

最终提交 `git diff --check` 通过。范围内没有未解决的源码/发行阻塞 finding；精确两 OS CI、远端分支身份和最后状态提交尚未在本轮核验。真实 Temporal/外部作业停止、fence/租约终态、新两模板六阶段/导出/重启与 F3.3d 的既有边界不变。

## 精确 CI 与远端最终核对：c3113ad

2026-11-03，同一独立审查上下文仅对固定候选 `c3113ad119c72ed933876ddae95d3c849c804852` 完成最后只读核对。当前工作区已开始 F3.3d，任务/提交源码有未提交修改；本轮从 `git show c3113ad:...` 核查 C2 的 11 项已审身份，聚合仍为 `b215f955…`，并确认原 `4abad37…` wheel 未变，没有把 D 工作区或之后的安装作为 C2 证据。此前最终本地发行结论继续有效；本轮没有重跑全套、安装、编辑源码、提交或推送。

**C2 的精确 CI 与远端核对通过，范围内无未解决 finding。** 独立解析 `.ergora/checks/f3-task-cancellation/ci/` 内官方原始 `ci-run-latest.html` 和两个 job HTML：run 页面完整提交链接为本候选，状态为 Success，关联 job 集合恰为以下两个；job 页面自身的 selectedJobId、矩阵标题和每个必需步骤的日志 URL 均绑定正确 job 与完整候选提交。随后才核对 selection JSON 与 `ci-html-status.json` 的来源哈希一致，没有仅采用作者摘要。

|精确 CI 41576751862|必需步骤|原 HTML 结论|
|---|---|---|
|[Ubuntu 3.11 / job 125721921231](https://github.com/626619403/Ergora/actions/runs/41576751862/job/125721921231)|Build and install wheel；Packaged reference identity；Native application regression|全部 success，Complete job success|
|[Windows 3.12 / job 125721920856](https://github.com/626619403/Ergora/actions/runs/41576751862/job/125721920856)|上述三项；Windows PowerShell 5.1 installer and upgrade|全部 success，Complete job success|

两个 job 都没有 failure/cancelled/timed_out 步骤。Ubuntu 的 Windows PowerShell 步骤按条件 skipped；该步骤在 Windows 实际 success。固定候选的 `.github/workflows/portability.yml` 与上述矩阵/步骤一致：从 wheel 安装，验证打包 reference 身份，执行该系统适用回归；Linux 另执行原平台 portable/adapter/runtime 检查。此处核验的是官方 HTML 的步骤结论，未下载完整 CI 日志，不把本地 522 项计数移作两 OS 的实际计数，也不把 Windows 兼容检查当原生正式取消运行支持；正式执行仍按手册走 Linux/WSL2。

原始 HTML 身份分别为：run `8744e8d3b344fc2a9b72505acbb70df635264b89ad9d80d044eadc0188c269b8`；Ubuntu job `7ff4c9648a6f3082d52eab6c5e3a14c31521a5c1657ae4e0eb074aa9f61be41b`；Windows job `27d6f05335f069025af35a13d7d3068c96b39124f78c419da1afefdc3b00b3a6`。精确运行见 [CI 41576751862](https://github.com/626619403/Ergora/actions/runs/41576751862)。

确认 origin 为 `https://github.com/626619403/Ergora.git` 后，独立执行 `git ls-remote --heads origin refs/heads/refactor/architecture-foundations`，退出 0，返回 `c3113ad119c72ed933876ddae95d3c849c804852`；与已保存 `ci/remote-head.txt`、本地固定候选和精确 CI 完全一致。该结论绑定核验时点，不预认后续状态文档或 D 提交的远端身份。

至此 C2 的已审源码、最终本地发行、精确两 OS CI 和候选远端身份均已独立核同。F3.3d 的旧提交锁迁移，以及 F3.4 的真实服务/外部作业停机、fence/租约终态、两模板六阶段/导出/重启验收仍是后续范围，不由本次成功继承通过。
