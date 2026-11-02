# F2.3 显式服务运维独立审查

日期：2026-11-03。审查者：fresh-context 独立 reviewer `f2_services_review`。仅获授权检查源码/证据、运行适度隔离检查及写本报告；未修改源码、安装依赖、提交、推送或操作用户运行栈。

当前结论：**源码同切片复审通过，两项 P2 均已关闭，检查范围内无未解决的源码/结构 findings**。最终修正 wheel 的身份、适用完整回归、更新后的性能及精确两 OS CI 尚待独立核对；本结论不代表完整 F2.3 验收已收口。初审及修正记录如下。

## 范围与身份

基线为 `6c153b1347921a5b05b60241236425468b14ce69`，分支 `refactor/architecture-foundations`。先读 `AGENTS.md`、`docs/PLAN.md`、详细计划 F2.3 及当前切片记录，再检查完整 tracked diff 和两个未跟踪文件，未用作者结论替代检查。审查依照 maintainable-project-delivery 的独立审查流程及 review-pr 的单 reviewer 流程。

初审范围：`src/ergora/services.py`、`tests/test_services.py`、CLI/Web 入口、`pyproject.toml`、README、`docs/USAGE.md`、`docs/AGENT_BACKENDS.md`、`docs/WINDOWS.md`、`docs/architecture/current.md` 和本切片记录。邻近检查包括注册/发布/修订、State/file_lock、reference 身份/选择式执行器、冻结 service launcher 和 Supervisor 配置、实际 Supervisor 4.3.0 RPC/状态/日志实现、架构测试及两 OS CI 定义。原 `.ergora/checks/f2-services/review.diff` 不包含两个新文件，已直接读原文件。下述复现时 `services.py` SHA256 为 `e5df2a41920c5011a2ff9d9de28768c6d4da1988f58fb28dd479b55c79296820`，包含关闭过渡及不自动重放 RPC 修正。

## 初审结论

需求符合性：**需修正两项 P2 后复审**。显式选择、复用原 Supervisor/launcher、全部 autostart 关闭、CLI/API 共享用例、原生 Windows 的 WSL2 边界、修订/投影/控制库检查及冻结参考保护在检查范围内成立。多字节文本日志和重复停止的真实过渡状态仍有可复现问题。

结构与维护性：**总体符合，两个问题由现有 services 所有者局部修正即可**。`services` 在两个不同生产入口实际复用；其私有上下文、原子配置写入和配置准备具有同一资源生命周期所有权，不需要进一步抽成通用框架。两个标准库 Unix transport hook 是现有框架的必需适配点；单请求 hook 保护变更 RPC 不被默认重试。依赖方向不反向导入入口，未建立竞争的持久任务调度器，Linux dev extra 的 Supervisor 固定版本与真实验收相符，生产依赖未增加。

## Findings

### P2-1：合法 UTF-8 文本在默认日志窗口可能不可读（已修正，复审关闭）

位置：初审 `src/ergora/services.py:243`（`tailProcessStdoutLog`/`tailProcessStderrLog` 字节切片 RPC）。

Supervisor 4.3.0 的 `options.tailFile` 先按字节 seek/read，再严格 UTF-8 decode。普通多字节文本的窗口起点可能落在字符中间，触发 HTTP 500；当前入口将其转成“日志不可用或不兼容 XML”。这不限于二进制日志，与手册所述文本日志能力不符。

真实隔离 fixture：启动受控 temporal 服务并等日志 ready，将日志写为合法 UTF-8 的 `文` × 4000，文件共 12000 字节。默认 `limit=8192` 返回 `ValueError`，原因是 `ProtocolError: 500 Internal Server Error`；同文件 `limit=8190` 成功读取 8190 字节。默认窗口会在常见中文/其他多字节日志中反复失败。

最小修正：保留有界读取和原生日志归属，增加 UTF-8 边界处理及真实默认窗口/追加分片回归。若原生 RPC 的严格 decode 无法满足合同，应在同一 services 所有者使用最小的有界替代，并同步手册和实际性能证据，不应完整读日志或盲目重试变更 RPC。作者已接受，修正待复审。置信度：100。

### P2-2：重复 stop 把正在停止的服务当成可再次发 stop 的状态（已修正，复审关闭）

位置：初审 `src/ergora/services.py:210`–`212`（stop 请求条件）。

`STOPPING` 不在 `_STOPPED` 中，重复 stop 会再次调用原生 `stopProcess`。Supervisor 的 `RUNNING_STATES` 为 RUNNING/BACKOFF/STARTING，不含 STOPPING，因此返回 fault 70 `NOT_RUNNING`，当前入口抛 `ValueError`。这时停止已经在进行，应继续观察其确认结果。

真实隔离 fixture：将受控 temporal 设为忽略 SIGTERM，`stopwaitsecs=3`。第一次 `stop(timeout=1)` 返回 `outcome=unconfirmed`，实际查询为 STOPPING；立即 `stop(timeout=5)` 却抛 `Supervisor rejected the service operation (fault 70)`。现有停止未确认测试只 mock 查询状态，底层进程尚为 RUNNING，未覆盖此真实原生状态。

最小修正：STOPPING 时不重发 stop RPC，只在同一有界等待内观察停止结果，并补真实在途 stop 重试回归。原生 BACKOFF/STARTING 的 start 选择也应按实际 Supervisor 状态语义核对，避免重发原生已在处理的启动。置信度：100。

## 检查与性能证据

- reviewer 直接运行最新源码的服务和架构定向检查：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_services.py tests/test_architecture_boundaries.py`，**18 passed、1 skipped**；仅 FastAPI/Starlette 既有弃用警告。跳过为 Linux 下的原生非 Linux 平台检查。
- reviewer 单独运行真实 Supervisor 4.3.0 fixture 完成上述两个反例；各 fixture 在 finally 中只关闭其临时 daemon，未连接实际用户服务。
- reviewer `ergora reference verify` 为 **PASS，283 文件**，未启动运行时。
- 已读 `performance.py`/`performance.json`：64 MiB 稀疏 ASCII 日志、40 次 4096 字节窗口，中位 2.554 ms、最大 3.391 ms；20 次 status 中位 2.772 ms；客户端/Supervisor 峰值 RSS 增量 792/224 KiB。该测量确实使用受控无模型服务和原 launcher，支持“该条件下无整文件读取”的有限结论。它不覆盖多字节日志反例，也不代表真实 Temporal/MLflow/模型或 GPU 收益。日志实现修正后需重测对应路径。
- 历史非 editable wheel 的 316 passed、19 skipped、36 子测试及 338 文件/两安装证据只绑定其当时包身份；该包不含本次后续源码修正。reviewer 未运行完整套件、未重包装或安装，也未将历史 CI 记为当前候选通过。

## 余项

两项修正后的同切片复审、最终非 editable wheel 与源码/两安装身份核对、适用完整回归及精确候选 Ubuntu/Windows CI 仍待完成。保持当前切片为进行中；F2.4 综合旅程和真实服务/模型验收仍为后续范围。

## 同切片源码复审

复审父提交为 `7402ea6239ab68e3a912535478bebb601d7e610e`；本节结论绑定其后工作区的 `services.py` SHA256 `0c880bed08670e61e9f1704d4929a7ee14c10de7517f518773077d35b18b1414` 及对应更新测试/手册。`7402ea6` 自身及先前 wheel 不因此获得修正后的验收身份。

P2-1：改为 Supervisor `getProcessInfo` 获取实际原生日志路径，再以非阻塞 open、普通文件 fstat、seek 和有界 read 读取窗口。没有完整读文件；标准库 UTF-8 增量解码器处理窗口边界，不完整后缀不推进返回游标，下一次用该游标补齐。原 tail RPC 的重复回包修剪分支已删除，未为单一用例引入通用日志框架。最小窗口改为 4 字节，避免小于完整 UTF-8 字符时无法前进；默认 8192、最大 65536 不变。当前候选尚未完成对外发布，这一 API 收窄已有明确手册和拒绝测试。`limit`/`bytes_read` 指原始字节窗口，替换/JSON 转义后的响应可增大，手册已明确。

reviewer 用真实临时 Supervisor 独立验证：`文` × 4000 的默认 8192 窗口成功；2 字节未完整后缀保留原游标，补齐后恢复完整字符；4 字节窗口下分次追加的 3/4 字节字符持续前进；非法 UTF-8 可见替换，原始窗口仍有界；超过窗口时保留末窗并设 overflow。新 FIFO 回归通过，非普通文件在 fstat 后拒绝，非阻塞 open 避免 reader 被 FIFO 等待卡住。P2-1 关闭。

P2-2：当前 `control` 在 STOPPING 时只轮询，不再次发 `stopProcess`；STARTING/RUNNING/BACKOFF 不重复发 start。真实忽略 SIGTERM、3 秒 stopwaitsecs 回归通过：首次 1 秒等待返回 unconfirmed/STOPPING，第二次 5 秒等待返回 confirmed，两个调用合计仅发送一次 stop RPC。reviewer 另用真实退出/重试 fixture 验证 BACKOFF 下重复 start 保持 unconfirmed，不会变成 ALREADY_STARTED。P2-2 关闭。

复审检查：相同服务/架构定向首跑 **23 passed、1 skipped、1 failed**。唯一失败来自新增 UTF-8 测试一次追加 7 字节后要求 4 字节尾窗先返回前 3 字节，把 tail 合同误当顺序分页；已及时反馈，作者改为分次追加并另断言 overflow。reviewer 针对此实际修改补跑该测试，**1 passed**。此前通过的其他检查不重复扩大执行；真实停止、FIFO 和 RPC 不重放回归均已在首跑通过。当前无未解决源码或测试问题。

需求及维护性复审通过；性能结论仍限于初审所述历史路径，修正后的本地读取须重测并绑定最终候选。后续只核对最终包/两安装、适用完整回归、精确两 OS CI 和交付记录；未验证范围继续保留。
