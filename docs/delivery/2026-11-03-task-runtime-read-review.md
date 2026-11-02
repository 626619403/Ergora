# F3.3a 只读原生任务状态独立审查

日期：2026-11-03。审查者：fresh-context reviewer `f3_task_runtime_read_review`。按 `maintainable-project-delivery` 和 `review-pr`，先读原始 diff、新文件、相邻 reader/原 Transport，再读作者设计和验证叙述。基线：`b6802216b0a60c9e439b1441c39004bf269503c3`；本轮生产/测试改动审查时尚未提交。只读审查产品及适用定向检查，唯一仓库写入是本报告；未安装、调用实际服务、提交或推送。

## 结论

- **需求符合性：源码及受控协议范围通过，无已确认 finding。** published 项目、安装身份和本地任务归属/spec 校验先于网络；原安装 `DevelopmentTransport.poll` 继续拥有 lookup、原始启动 spec 比对和 run ID 固定。仅 `RuntimeNotFound` 成为 `not_found`；其他失败公开报错，没有本地状态回退。原 phase/status/outcome 直接保留，terminal 未转换成取消或验收确认。
- **结构、复用和资源边界：通过，无已确认 finding。** CLI/API 共用 `tasks.status`，没有复制状态机、持久镜像或新的执行器。此次代码不调用 start/signal/cancel，不写任务、ledger 或租约。默认网络预算 20 秒、允许 1–60 秒；父进程在网络预算之外留 5 秒并强制回收，已有本地合同预检另计。
- **发行验收：已复核本地包身份和真实不存在分支，完整回归/精确 CI 待收口。** 当前 wheel 的 342 文件在源码及两非 editable 安装间一致；两个旧 L0 任务对当前真实服务均为权威 not_found。该结果不证明真实在途/完成运行、原 history 输入验证或真实固定 run ID 已验收，也不代表 F3.3b/F3.3c/F3.4 完成。

## 检查范围与身份

已读生产差异 `src/ergora/{cli,reference,tasks,web}.py`、新增 `src/ergora/reference_task_runtime.py`，边界变更 `tests/test_architecture_boundaries.py`，新增 `tests/test_task_runtime.py` 和 `tests/fixtures/task_runtime_client.py`。已读相邻 `reference.task_files/_task_files_main`、`tasks._project`、`reference_task_creation`，以及冻结原 `dev_platform/{runtime,connection,workflow}`、`agent_platform.core.environment` 和相关 reader/Transport 测试。

同时核对 AGENTS、PLAN、详细计划 F3、切片设计记录及 README、USAGE、PROJECTS、AGENT_BACKENDS、current/reference-boundary 架构差异。F3.2 creation 两份交付记录的收口变化不作为本次新增运行能力的验收。

源码/测试精确身份如下。以路径为键、下列摘要为值的 JSON 对象按 `sort_keys=True,separators=(',', ':')` 序列化，其 SHA256 为 `2a9260a4e43c5aacbb4b67b4c71927c56e8bbbf8b06a0fc49c3ae01623422ee2`。

|文件|SHA256|
|---|---|
|src/ergora/cli.py|87868187678533b6640e7a38d7525f07ec220c7d3c2fae2ed16b8501a5854507|
|src/ergora/reference.py|e37c9ec89399e5b0d58d8a0703feed06d332555d92ce889157712a27524c31f9|
|src/ergora/tasks.py|4cf8fc2413230571ae60138695226f0f934d1bf9d56f87565247b83cef3f179c|
|src/ergora/web.py|db28de12a4c16d537be1b906afcce2419027dbc17acf54c0542ddf2fdabf5e33|
|src/ergora/reference_task_runtime.py|9fdb8c9089b4dc6c1266afd9c247c873fe155195da2bd820e0c077808851e1ba|
|tests/test_architecture_boundaries.py|eb4d93eb85676692410f8058e8c593af344aca2a6ed8c64bb26111ac8ebe740c|
|tests/test_task_runtime.py|65445bdbe111f3031a1f44c2e8c58f9b7472bdb35c4d9fc48285749ca74aa850|
|tests/fixtures/task_runtime_client.py|2a6042c13111977603a34a25a867423ac50e4ff69881ca6c54dd5756d2d9ed29|

## 职责、控制流与复用

`tasks.status`（tasks.py:82）有两个不同生产文件的直接消费者：CLI 和 Web。它复用已有 `_project` 的 published/安装核对和 `reference.task_files` 的归属、目录 ID、tracker、baseline、摘要及安全读取，不重复编写本地任务准入规则。

`reference.task_runtime_status`（reference.py:322）只有 tasks 这一生产调用者，但拥有实际的进程协议、登记安装路径、可选 SDK 可用性错误、环境与父进程回收职责；这与现有 reference 子进程边界一致。新增模块 `reference_task_runtime` 的入口只有该父进程，独立文件的依据是隔离原 CONFIG/STATE 及 SDK 导入。私有 `_status` 将同一个查询协程纳入总网络预算，是局部异步生命周期，不是额外通用抽象。

run ID/timeout 的校验位于公共用例；SDK 缺失指导位于进程边界。子进程 `RuntimeNotFound` 分支仅处理原 Transport 抛出的权威不存在；RPC 和超时分支保证失败不成为状态。连接 RuntimeError 等未被专门归类的异常仍使子进程失败，并由父进程转换成公共 ValueError。非零退出和空 stderr 分支对被杀进程可达。没有建议增加重复校验或另建状态适配层。

原 `poll` 调用路径包含 describe → 使用返回 run ID 重新取 handle → 第一项 history 的原始输入验证 → query/result。未指定 run ID 也不会在后续读取时漂移；异常关闭保留 NEEDS_RECONCILIATION，完成但取消未确认保留 CANCEL_UNCONFIRMED。原启动输入不可用、输入碰撞或后续 RPC 错误均失败，不伪报 not_found。

## 独立检查与性能边界

环境：Linux x86_64，Python 3.11.15，已有开发环境，无新安装。

1. 独立运行 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_task_runtime.py tests/test_architecture_boundaries.py`：**26 passed，23.51 秒**；仅既有 FastAPI/Starlette 测试客户端弃用警告。原 Transport 未被替换，SDK 客户端为受控夹具；覆盖 running/completed/unconfirmed/terminated、权威不存在/RPC/连接/输入碰撞、显式及未指定 run ID、SDK 缺失、选项、两层超时和 CLI/API。夹具没有 start/signal/cancel 方法，成功路径比较原任务目录下全部文件字节。
2. 独立实际父进程回收探针：仅将所启动子进程的程序体换成向临时文件记录 PID 后睡眠 60 秒；保留生产 `subprocess.run` 和 `timeout=1` 的原参数。**6.010 秒**抛出 `Task runtime query process timed out; execution state remains unknown`，随后 `os.kill(pid, 0)` 报进程不存在，父进程 `sys.modules` 中无 `temporalio`。临时材料自动清理。该探针证明父进程真实 kill/reap 兜底，不测量 Temporal 延迟。
3. `git diff --check`：通过。新增模块导入图/原生边界在上述 8 项架构检查中通过。

性能判断限于调用和资源边界：每次请求增加一个专用 SDK 查询进程，前置 reader 仍有自己的进程；身份校验和本地读取成本不能计入或假称被网络 timeout 覆盖。网络等待由 asyncio 总预算包住，即使原 SDK RPC 的单次 20 秒预算更长，外层仍可取消；取消无法及时完成时父进程兜底。没有新任务全量扫描、轮询循环或持久 worker。实际服务证据目前限于下面补核的 not_found CLI 端到端延迟；不从 26 项测试耗时推导生产性能，也不将一次生命周期探针视作跨平台性能验收。

## 本地发行证据补核

随后收到并读取 `.ergora/checks/f3-task-runtime/verify-package.py`、package-identity.json、构建/两安装日志、legacy-journey-performance.py/json/log。没有重新执行会写证据的作者脚本；另以只读 Python 对照 SHA256：wheel `816b72d75fca0ae8c8e25911d88d165f8e2618c278c57fb7108305314747e43f` 的 **342 文件 × 源码/wheel/两非 editable 安装全部一致**，包含本报告上列 5 个生产文件身份。

真实旅程脚本仅将旧注册/策略复制到隔离配置和控制目录；任务状态读取指向原 task store，服务没有启动/停止或其他变更调用。原始完整结果为 **48 次 CLI**：两个旧 L0 模板各一次初查、20 次重查和一次真实无 SDK 错误，再加四次隔离注册导入。两个旧任务当前真实服务均为 `runtime_status=not_found`、`run_id=null`，各 10 个原任务文件摘要保持；基础安装明确返回 `install ergora[temporal]`。

20 次重查的 CLI 端到端中位数分别为 **1224.93 / 1218.01 ms**，最大值 **1444.52 / 1295.10 ms**。这是同机 Linux、wheel 安装、warm 重复调用、当前本地真实 Temporal 的不存在分支测量，含 Python/reader/SDK 查询进程和本地预检；不是服务纯 RPC 延迟、吞吐、回归前后加速比或存在运行的性能。脚本仅在首查发现 run ID 时追加 pin；本轮两者为 null，因此没有真实固定 run ID 的验收证据，此限制已反馈实现者。

F3.2 的后续 HEAD `10f9f3e` 仅收口文档，源码基线仍为本报告的 b680221；本报告的源码/测试身份未变。补核时 wheel-regression.log 仍在输出测试进度，未将未完成运行记为通过。

## 尚待收口

需对同一精确源码/测试候选核对完整适用回归和 Ubuntu/Windows 精确 CI；实际服务的在途/完成运行、原 history 输入验证与固定原 run ID、真实 API 查询仍按现有证据范围分别记录。真实 Windows 连接/凭据路径只能按实际证据表述，受控 SDK 端口通过不证明真实 Windows 服务已验收。本审查未执行模型/GPU任务或任何运行变更；下一实施段仍为 F3.3b，需独立计划和审查。
