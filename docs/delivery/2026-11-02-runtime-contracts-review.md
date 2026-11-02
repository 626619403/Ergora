# R5 独立需求与可维护性审查

日期：2026-11-02。Reviewer：Codex `runtime_contracts_review`，fresh-context 独立代理，未继承实现对话。按项目 AGENTS、`maintainable-project-delivery` 及其 independent-review brief，先读原始 R5/A1/ADR 和实际差异，再对照源码、调用者与验证记录。

## 结论与 findings

- **需求符合性：通过。** 当前共用运行摘要、产物引用、领域状态及实际平台能力已准确记录；没有改变旧 run 文档、正式六阶段或原生状态。A1 已明确“无必要不抽新层”，已有复用足以支持本次保留决定，R5 不以新增代码为完成条件。本轮可按契约核对及现有生命周期证据的范围收口。
- **可维护性：通过。** 在实查范围内无 findings，无阻断性问题。没有增加单一消费者包装、通用基类、第二套状态机、调度器或隔离承诺；文档放在本项目的架构/交付目录，R6、F3/F4、F5 和 D3 的所有权保持清楚。

上述结论不把真实 Forge 模型 campaign 的取消竞态、Linux 正式 monitor 被 SIGKILL 后即时整树停止或 Temporal 服务端到端旅程标为本轮实测通过。mini 首轮超时仍未解释；作者如实保留失败与后续通过，未修改源码或放宽阈值。这些限制不构成本次文档整理的阻断项，也不能被后续状态登记删去。

## 身份与差异范围

原始要求为[详细计划 R5](../plans/2026-11-01-all-in-one.md#r5-运行与平台责任)、[A1 保留/合并清单](../architecture/2026-11-01-audit.md#6-可执行的保留合并与删除清单)及 [ADR 0001](../architecture/decisions/0001-refactoring-foundations.md)。授权边界是持续按计划推进、逐步更新文档及完成后推送；本 reviewer 只获准写本报告。

基线及审查时 HEAD 均为 `39e0c34f503d7cc607e8ae72a755a89b8b64b3e1`，分支 `refactor/architecture-foundations`；实际生产/测试身份为 `f9a9b743be1b5bde352d212b75c47358d5d73e9a`。实际 `git diff HEAD` 与 `.ergora/checks/r5/review-tracked.diff` 逐字节相同。完整审查四份文件如下；本报告为额外审查产物。

|文件|差异及审查时 SHA-256|
|---|---|
|`docs/PLAN.md`|tracked 增加活动切片；`61a6bb5e3d5135e1273bc6a97d7977425fd3e3522c476662e7a671482f51943e`|
|`docs/plans/2026-11-01-all-in-one.md`|tracked 登记 R5 及保留决定；`872819f0ee55e51a898ea7602a56c066cdd038bbf64f6cffec67355365ec5f3d`|
|[运行契约矩阵](../architecture/2026-11-02-runtime-contracts.md)|untracked 全文；`2619b546c0423f3b58d88a041489ed8f966bda64985d0809a1222b09cb1a6f4f`|
|[R5 交付记录](2026-11-02-runtime-contracts.md)|untracked 全文；`e6b890dc1a938bfe06b4c1be572c6862be0dd77f4f03441328e6c56d32c6274e`|

独立核对 `git diff f9a9b74 -- src tests README.md pyproject.toml .github/workflows` 为空；没有生产、测试、依赖或 CI 变更。

## 源码与相邻调用核对

|实查位置|判断与依据|
|---|---|
|`processes.py:102`、`agents.py:113`、`evaluation.py:128`、`optimization.py:127`、`kernel.py:101`|四个独立生产模块实际消费同一个 `status/returncode/output` 结果和输出文件。新目录、UTF-8 协议、进程创建/清理可抛异常的说明准确；结构化 Agent 结果、评价资格和候选采用仍由领域边界判断。|
|`agent_runs.py:13`、`agents.py:68`；`cli.py:238`、`web.py:165` 及各域操作路由|独立 Agent 用例保存原 binding/revision、prompt SHA、Skill/recall 快照及条件性的结构化结果；CLI/Web 直接读取各域记录。同步调用没有持久后台取消/恢复 API，硬退出可能保留 `running`；没有证据需要另造通用 Run 文档。|
|`windows_job.py:34`、`processes.py:28`、`research.py:86`|Job 的两个生产消费者分别使用 stdin gate 和 Event gate。assign 前不启动真实命令/网络；控制器独占非继承句柄。正常/超时/取消走终止、确认 active=0、关闭句柄，终止/查询/等待失败不返回假停止；该机制没有文件/网络访问隔离。|
|`processes.py:111`、`stage_driver.py:13`、`reference_executor.py:48`；原 `agent_platform/process_job.py:62`、`:75` 及 `sandbox.py:43`|普通命令新建进程组并在 finally 清理；专用 stage_driver 保留监控组、采用 subreaper 和仅置位的 TERM 处理。supervised 路径不使用普通 timeout，deadline/fence/TERM-KILL 由原 monitor/timeout 负责；started 而无 terminal 的提交不自动重执行。矩阵没有宣称 monitor 硬退出保证。|
|`research.py:24`、`:86`、`:188`、`:224`|抓取子进程的网络通信、总墙钟/字节预算、父死亡信号、持久取消意图及保守恢复账目具有独立语义。父 PID 核对在网络前执行；同 ID 恢复核对项目及冻结 request。将这些控制流搬入命令原语或 Job 会混淆所有权。|
|`kernel.py:64`、`:74`、`:86`、`:106`；`data/drivers/forge.py`|沿原 binding 和 campaign 对账；可捕获的 prepare/run 进程非成功或 JSON/文件异常保留 `outcome_unknown` 与 reconciliation。硬退出可留下 `running`，下一次调用也按不确定处理。失败的 status 查询不清除 reconciliation，重跑需要显式理由；`native_finished` 只表示原生候选完成，不等于可信评价通过。|
|原 `dev_platform/workflow.py:63`、`:172`；`reference_executor.py:98`|取消意图与 fence/terminal 的停止确认分离；正式任务可保留 `CANCEL_UNCONFIRMED`，原 ID/引擎与候选证据没有被统一展示状态覆盖。|

另完整读取 `evaluation.py`、`optimization.py`、两 SDK driver；检查 `tests/test_processes.py`、`test_projects_tools.py`、`test_research.py`、`test_reference_executor.py`、`test_agents.py`，以及 `reference_acceptance.py`、`signal_windows.py`、`windows_cancel.py`、`mini_acceptance.py` fixtures 和 `portability.yml`。框架 hook、预算检查、取消/未知分支都有现有职责，本轮没有新增 guard、fallback 或控制流需要辩护。

## 证据核查及限制

本 reviewer 实际执行了以下廉价、只读的独立检查，未重跑测试或探针：

1. 四份文档 **106 个本地文件链接存在**，无行末空白，`git diff --check` 通过；未检查 Markdown 锚点。
2. 按 R4 最终包清单逐字节核对 **324 个当前源码文件及 324 个非 editable 安装文件**，全部与清单一致。清单 wheel SHA 为 `b58be7546fb3af84886e1654631c1a55972cde51bfee0c7c07c639b8adbee83d`。此为内容身份核对，不是重新构建或完整运行验收。
3. 两 SDK checkout HEAD 分别为 ForgeKernel `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`、mini `04d809ceab9df28f9adaed044884180159172930`，与 `environment.json` 一致；导入结果只复核作者记录，未再次导入 SDK。
4. 独立解析 R4 保存的官方 Actions HTML：run **41380351919** 为完整 head `f9a9b743be1b5bde352d212b75c47358d5d73e9a`、Success、2 jobs completed；Windows **125069579809** / Ubuntu **125069579994** 均 succeeded。原页 SHA 依次为 `6133f43a1dcbd9175d702068edff37e67b66035046305878e6f14cb521ca9c28`、`8faae89d9f120ef75fd2eb8a4bc9583a3636525d3c78993b97c40320699ad721`、`4e7809bf8fb277b275d4b766ed47411f5df75adb23ccf8c7ac27763a806e6f36`，与 R4 审查相同。workflow 运行完整 tests，相关 Windows 专属测试在真实 Windows 条件下不跳过；未取得登录后的逐测试日志，也未新增 Windows 计数或声称本轮重跑。

作者运行证据已读取原始记录：首轮 **42 passed / 5 skipped / 1 failed（140.06s）**，mini `complete` 在 15 秒阈值内未结束、stderr 空；mini 单独复跑 **3 passed（15.56s）**，最终整组 **43 passed / 5 skipped（122.14s）**。5 skips 确为 4 项 Windows-only 和 1 项未选择的隔离 Temporal；固定 Forge 三项、mini 三项没有跳过。Forge 验证覆盖 CPU plan/prepare/status、冻结身份/产物、失败观察后拒绝无理由重跑；其不确定/取消处理另沿源码追踪，不能称为真实模型 campaign 取消竞态实测。

一次性 POSIX 探针的脚本与 JSON 一致：SIGINT 返回 `cancelled`、命令及后代停止；SIGKILL 无结果、两进程在观察时仍存活；两场景最后都主动清理并回收，`cleanup_confirmed=true`。它支持“普通命令没有父硬退出自动清理保证”，不构成让孤儿存活的产品承诺。`static-checks.json` 中 reference **PASS / 283 files** 为作者本轮检查；本 reviewer 的文件身份核对包含相应冻结内容，未再次执行 reference CLI。

未独立运行完整 Linux/Windows、模型/GPU、真实 Forge campaign、Temporal 服务或 monitor SIGKILL 实验；未安装、提交、推送、改服务或写入其他仓库文件。所见文档正确区分当前运行、历史同源码 CI、源码判断和未验维度。

## 剩余条件

范围内无待修正 finding 或待补的阻断性验收证据。作者需将本审查结论登记到计划/交付记录，并按既有授权完成提交及推送。R6 的 reference adapter、F3/F4 的持久任务与控制视图、F5 的跨域证据/成本投影、D3 的隔离实测继续按各自验收推进；任何后续生命周期行为变更都不能只继承本报告或历史 Windows CI 的通过结论。
