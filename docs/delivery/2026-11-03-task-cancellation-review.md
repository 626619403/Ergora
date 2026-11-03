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
