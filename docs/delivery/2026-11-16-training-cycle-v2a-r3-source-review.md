# M6-V2a r3 closed 拓扑独立源码复审

2026-11-16。审查者 `/root/training_v2a_r3_fresh_review`，非实施者，使用未继承实施对话的 fresh context。先读原始[运行合同](../plans/2026-11-16-training-cycle-v2-runtime.md)、[容量实施分期](../plans/2026-11-16-training-cycle-capacity-implementation.md)和完整实际差异／调用路径，再读[作者交付](2026-11-16-training-cycle-v2-runtime.md)与[前审](2026-11-16-training-cycle-v2-runtime-source-review.md)。已读根／源码／测试 AGENTS、PLAN、组件协议的执行／证据／检查分支，以及 maintainable-project-delivery 的 independent-review 和 ergora-codebase-quality 的 repository-style／module-design／test-seams。唯一写入为本报告。

## 结论与准确范围

|轴|r3 源码结论|范围|
|---|---|---|
|需求符合性|approve，0 findings|原 cycle 服务的四 versioned poller、两业务许可、等待消耗原截止、正常停服／取消／fatal 收尾，以及强行 SDK 中止时显式 unknown。全部 schema3 执行效果仍关闭。|
|结构维护性|approve，0 findings|职责留在原 factory／服务 owner，复用原 S/H、candidate、stop fanout 与 SDK 公共接口；没有新增执行器、状态账本或管理层。|

本结论只认证 closed V2a 的源码及已记录接缝；F1 的完成判据、F2 的可选 SDK fixture 均已在准确 r3 修正。强行中断 SDK shutdown 后的真实资源仍是 unknown，本审没有把报错或 task cancelled 解释为 cleanup 已完成。新安装、原模板、真实服务和后继 M6 的验收分别记账。

固定树为 `.ergora/worktrees/training-cycle-v2-runtime-fixed`，HEAD `82c6595907b4d2173890b82e6fcb6ab8920832b1`，准确基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`。进入及终核时工作树 clean，`git diff --check baseline..HEAD` 通过。完整差异仅四文件：

- `src/ergora/reference_training_worker.py`
- `tests/test_training_runtime.py`
- `tests/test_training_submission.py`
- `tests/fixtures/training_cycle_operations.py`

独立重算完整 binary patch：50,110B，SHA256 `25cf19fa37473e72e81255e8f5680033868fe1b60eb114bd076cec437064997a`，与 `v2a/frozen-r3/complete.patch` 逐字节相同。作者基线 `f9b9d72d6d5f2102809a3cafaadb2226bba0966b` 至准确基线的 src／tests 无差异。固定树相对作者2064项 freeze 的4份文档差异与7份新增文档，全部正是该基线推进带入的 docs 差异；产品与测试字节／执行位一致，不能把完整树笼统称为2064项全同。

## F1、F2 的独立处置判断

**F1 已修正，支持范围成立。** `reference_training_worker.py:2656` 的 `finish_worker` 先等待原 run task，收回自身创建的公共 shutdown waiter，再于 `:2678` 核 SDK 公共 `is_running/is_shutdown`。run 已结束但 SDK 未完成时抛固定 incomplete／unknown，避免把 task 完成当成 drain。`finish` 在 `:2687` 使用 `gather(return_exceptions=True)`，先等同组另一 normal 已开始的真实 drain，再传播错误；因此一个 normal 中止不会使正常 peer 的 cleanup 被根 main 提前退出打断，也不会主动进入 stop 组。`:2708` 的 finally 即使遇到 cleanup 错误仍等 connecting／waiting 结束并移除本服务 signal handlers。

独立读取已安装 SDK1.34 的 `_worker.py:766–927`：`is_shutdown` 表示 shutdown-complete，`Worker.run` 明确警告 cancel 可打断 shutdown；实际 `shutdown()` 只发请求并等待 completion，没有公共 resume／finalize 接口。validate 在 `_started` 之前失败与已经运行后清理中止是不同状态，r3 判据保留了这种区别。此处不需要私设 SDK event、复制 SDK 算法或重启 run。

生产链实际为 `services._prepare → reference.training_cycle_worker_command → cycle_main → asyncio.run(_serve_cycle())`。SIGTERM／SIGINT和 SDK fatal 只设置停止事件；主 owner 取消不会由 `asyncio.wait` 传播给四个 SDK run，finally 持续等公共 shutdown。未发现 src／scripts 存在直接取消这些 run、提前 `loop.stop` 或全 tasks 取消的生产 caller。因此可保证的 loop teardown 是根 main 已完成 drain 后进入 Runner.close。外部强行 run.cancel／loop.stop／全 tasks 取消没有公共恢复保证，应保留原身份、资源 unknown 和后续原件对账，也不承诺报错后 stop 仍可用。

r3 两个直接中止用例没有伪造 completion。两 normal 中止时现场 `is_shutdown=false/finalized=false`、`stop_shutdown_started=false`；一个 normal 中止时另一 normal 尚未放开 cleanup，`serving_done=false`，随后才显式报 unknown。测试最后仅用公共 shutdown 回收仍活的 stop 组；被中止 normal 始终未 finalize。它们证明判据与停序已修，不能证明强行中止后的实际 OS 资源已回收。

**F2 已修正。** `tests/test_training_submission.py:2675` 在新 fixture 的 SDK import 之前调用 `pytest.importorskip('temporalio')`。依赖仍在原 optional extra；core 不因此要求安装 SDK。已读缺 SDK probe 的脚本／command／result：它实际进入该 fixture，得到 skip，SDK modules loaded 为空；这是缺依赖模拟，不是新 core wheel 验收。后者由根的新安装接续。

## 其余合同与维护性核对

`_serve_cycle` 只构造 normal／stop 各一个局部 `Semaphore(1)`。v1／v2 normal 共用前者，v1／v2 stop 共用后者；四个 Worker 各自仍为一个 SDK activity 槽，类／活动／queue 沿原封闭版本表注册。两 normal 同时请求 shutdown 并等待本组完成，再关闭两 stop；正常／fatal／主 owner 重复取消的真实 SDK run/shutdown 接缝没有发现另一条提前放行路径。

许可覆盖完整 invoke，释放留在原 `_CycleOperation.run`、`_CycleCandidate.run`、`stop_live_controller` 已完成 cleanup 之后。排队前固定 BOOT cold window，取 SDK scheduled／started 两个绝对截止的最小剩余额度；等待与 invoke 共用该 SDK 截止，拿到许可后不重开 cold。snapshot 后继续取原 control／work 上限，stop 分支仍沿原 total。余额不足1秒的拒绝与 BOOT 回退／跨 BOOT 检查均对应真实准入风险。没有扩大原 SDK10秒、control、cleanup reserve或70秒服务 stopwait。

本地 `finish_worker/finish` 隐藏的是本服务的 SDK waiter与分组收尾义务；factory 的可选许可参数只有实际服务 caller 负责构造。普通版本选择沿既有协议表，不是新增可替换组件族，无需新 ABC／通用管理器。新增测试保留真实 SDK lifecycle 或原 S/H／实际后代，保护等待取消、超时、stopped 帧后仍等 S、重复取消与 peer drain，断言具有实际失败接缝。

独立 AST 比较确认两 Workflow 类与准确基线完全相同；产品顶层函数差异仅为 `create_cycle_activities` 和 `_serve_cycle`。相对 r1，factory、`_CycleOperation`、`_CycleCandidate`、`stop_live_controller` 的完整 AST 均不变，六项 r2 S/H 检查只在此未变调用链内有参考价值，不转授整个 r3 服务通过。protocol／cycles／budget／execution／submission／services／argv 未改；还逐处读取了 controller、worker、budget.source 和 validate_context 的 schema3 关闭分支。原来源、预算、机会、历史恢复合同没有被重写。

## 实查证据与未验边界

证据根为 `.ergora/checks/training-cycle-v2-runtime/`。下列运行均为独立读取既有 argv／raw／JUnit／manifest，非本审重跑；环境为 Python3.11.15、SDK1.34.0，明确 PYTHONPATH 指向作者隔离源码。

|原件|独立核对结果|可支持范围|
|---|---|---|
|`v2a/frozen-r3/` 与两批 r3 `inputs.json`|freeze manifest SHA `e7f4082abb67e613e55eee78e09835a6a5f313a80ecc357e53de935d83ce9495`；两批输入 SHA 均 `8817d890c985b110bcc7f37082b60469ad5ee0babcede78bff494c8afb8973b5`；逐2064项 raw／bytes／执行位无 delta|运行输入确实是该 freeze，固定树产品／测试同一|
|`v2a/sdk-lifecycle-fix-r1`|exit0、waited=true；raw／JUnit 为12 passed，JUnit2.099秒；读取两份中止现场 JSON|准确 r3 的本地 bridge／poller替身＋真实 SDK run/shutdown，含单／双 normal 中止|
|`v2a/affected-runtime-r3`|exit0、waited=true；raw／JUnit 为65 passed，JUnit11.466秒|准确 r3 的 cycle 选择：旧 V1 history、默认 sandbox、V2/v3、预算／容量／取消和服务 lifecycle 接缝|
|`v2a/final-submission-r2`、`v2a/no-sdk-probe-r2`|六项 S/H passed，JUnit37.198秒；实际 fixture 缺 SDK 为 skip，loaded0|factory／原操作链未变的历史证据；不称 r3 新安装或真实服务通过|
|`v2a/process-audit-r3.json` 与 summary|SHA `0075c58b4648634c2542fc47a269ee1fb96f9a332d80ad0f6f71617847297e12`；197行重新分类为194 absent、3 synthetic；112条非JSON实际均为零字节 permit 控制旗标|审计当时已捕获完整进程身份的结果；本审未重新探测进程，不代表全系统零残留|

本审执行了只读 Git／源码／SDK 原件检查、AST与完整 manifest／patch比较、diff-check；没有运行测试、模型、服务、网络、安装、提交或昂贵检查。r1 安装／原模板结果没有转授 r3。根正在做的准确 r3 新非editable core／SDK 安装不在本报告认证范围内。

真实旧 queue 在原 SDK10秒内成功 start 仍未验；既有失败 shared-start 不能改写为通过，也没有理由延长预算。完整 M1c Payloads／Memo／Failure、所有晚处10MB reader／最后 gate、真实注册与 server history、实际 CPU 两候选顺序 archive／丢回复／重启／停止／全部资源收尾和 GPU／训练质量仍归后继。接纳 closed 源码前后，公开交付与计划均须保留上述 SDK 强制中止 unknown 边界；未验项不能由本次0 findings关闭。
