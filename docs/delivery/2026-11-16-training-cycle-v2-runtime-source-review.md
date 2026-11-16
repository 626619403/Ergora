# M6-V2a closed 生命周期独立源码审查

2026-11-16。审查者 `/root/training_cycle_v2a_lifecycle_review`，非作者，使用未继承实施对话的新上下文。先读原始验收、AGENTS、组件协议、已审 M6 设计和实际完整 diff／源码，再读作者交付。适用 maintainable-project-delivery 的 independent-review，以及 ergora-codebase-quality 的 module-design／test-seams。只写本报告；未改源码、其他文档、依赖或环境，未运行测试、服务、安装、网络或模型。

## 固定输入与结论

本轮对象为 `.ergora/worktrees/training-cycle-v2-runtime-fixed`，分支 `feat/training-cycle-v2-runtime-fixed-r1`，HEAD `019c667a79e965a4ea4a74d37667bd7a0f7f1e81`，准确基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`。完整四文件 patch 为 44,476B，SHA256 `85a97b67e888eaf4e369d0e3a3221553524691a4f77645b49fe64cf72b5e97bf`，与作者 `v2a/frozen-r1/complete.patch` 相同。独立逐项核对 `fixed-r1/source-inputs.json` 的2071份文件字节、SHA和执行位，无差异；工作树 clean，diff-check通过。作者基线 f9b9d72 至准确基线的 src／tests 子树无差异。

准确四文件为 `src/ergora/reference_training_worker.py`、`tests/test_training_runtime.py`、`tests/test_training_submission.py`、`tests/fixtures/training_cycle_operations.py`。完整检查原 invoke、S/H、candidate、stop fanout、SDK1.34 Worker.run/shutdown 与邻接真实调用；没有从作者判断或前审继承结论。

|轴|r1结论|理由|
|---|---|---|
|需求符合性|request changes|四poller／两许可、等待窗口与生产主owner取消路径成立；被验收点名的强制SDK run取消边界仍可把未完成的cleanup当作完成，须按F1显式报unknown并限定支持范围。未发现正常服务入口会主动触发该强制中止。|
|结构维护性|request changes|职责留在原服务与活动owner，没有新增scheduler／manager／ledger／通用层；但 F1 的完成判据与实际SDK契约不一致，F2 破坏可选SDK检查边界。无其他独立结构性finding。|

## 按严重性列出的 finding

### F1 — P2：意外终止的 SDK run 不能当作 cleanup 成功

落点为固定树 `reference_training_worker.py:2659`、`:2666` 与 `:2682`。`finish_worker` 在 `worker.run()` task 结束后就退出等待；若 task 已取消，直接跳过异常和完成状态检查，再推进两stop的shutdown。

实际依赖 SDK1.34 的 `_worker.py:859` 只在运行阶段接住首次取消，随后 shutdown 的 poller wait（约884行）和 `wait_all_completed()`（约896行）没有取消保护。若停服／fatal 已进入这个阶段，外部再直接取消 normal 的 run task，它会以 cancelled 结束，尚未执行 `finalize_shutdown` 和设置 shutdown-complete。两个normal同时遇到此事（人为全tasks取消也会覆盖）时，本服务可以提前停止stop poller，最终还可能正常返回；原活动／S/H／pending root的实际完成未经确认。全tasks取消还会同时取消poller，SDK对已取消poller调用 `task.exception()` 本身也可抛出 CancelledError。

该源码反例随后已由作者保留的真实SDK harness复现，本审独立读取了 `v2a/sdk-run-cancel-red-r1` 的command、完整raw、JUnit、inputs和现场JSON；本审未自行运行。其产品worker SHA仍为r1的 `8ff852bf984a20b9a6cab25c5737cbef1f521cd1fbde595746d31e705e96b110`，只是增加red场景；输入manifest SHA `0aad307d791e51732f8df8106deeb5c2c0fd28595a29d3dbc7b93b437681dd54`。SDK1.34／Python3.11.15、1 failed、JUnit1.601秒：两normal均到真实SDK `wait_all_completed` 后直接取消其run task，现场为 `cleanup_released=false`、两task均done/cancelled、两worker均 `is_shutdown=false/finalized=false`，但 `stop_shutdown_started=true`。断言明确失败于提前停止stop组。该实证保留真实SDK run/shutdown而替换bridge／poller，证明停序错误；没有伪称这是一次实际OS资源泄漏验收。测试finally伪置completion event只为退出红例，不是恢复通过。

原件SDK另读自 `package-r1/venv-r1-sdk` 的实际1.34安装。r1原10个服务lifecycle场景中的 `cancel` 只取消 `serving`；新增ActivityEnvironment的loop teardown没有运行SDK Worker，均不能关闭本项。

生产可达性另行核过：`services.py:149 → reference.py:232 → cycle_main:2707 → asyncio.run(_serve_cycle())`，cycle是根main。SIGTERM／SIGINT和SDK fatal只设置stopped事件；仅主task取消不会由 `asyncio.wait` 传播给run tasks，finally盾内继续drain。src／scripts没有直接取消这些run、提前 `loop.stop` 或全tasks取消的生产caller。Python Runner.close在根main退出后才执行cancel-all；正常退出时四run已drain。因此初报将该故障按P1与正常生产停服并列过宽，完成caller核对后修正为P2：它是原始验收点名的异常边界缺省处理与支持声明问题，不是已证明可从正常服务操作触发的资源回收回归。

SDK公有run文档明确警告取消可能同时打断shutdown，推荐explicit shutdown；公有shutdown只有发起请求并等complete，没有resume／finalize接口。最小修正设计可采用公有 `is_running`／`is_shutdown` 识别run终止后SDK仍未完整结束，显式报cleanup-incomplete／unknown，不把该状态推进为成功，也不继续主动进入stop组；无需复制SDK、访问私有event、重启run或引入管理层。应先回收本函数创建的shutdown waiter，汇总并等待另一normal已经开始的正常drain，再报告异常；不能让gather的首异常过早结束根main，从而连带取消仍正常清理的peer。

该小设计在此审认可，**实施与复核尚未完成，F1仍open**。计划的loop teardown须精确限定为根main完成drain后的Runner.close；外部强行run.cancel／loop.stop／全tasks取消为SDK不能恢复的中止，实际资源状态保留unknown并沿既有原件对账，不宣称stop仍可用或全资源已清理。验证复用本red边界，期待显式unknown错误和未主动停止stop组；另保留正常SIGTERM／主task重复取消／fatal的完整drain证据。实际S/H与root cleanup证据仍按对应入口记录。

### F2 — P2：新共享fixture没有可选SDK缺省处理

落点为固定树 `tests/test_training_submission.py:2673`。新 `shared_cycle_activities` 在Linux直接import temporalio，而六个新节点只按平台skip。core安装故意不含SDK，因此这些节点会在fixture setup报 ModuleNotFoundError，无法按既有可选依赖约定跳过；同文件已有依赖fixture的间接skip不能保护这个独立fixture。

最小修正是在该fixture import SDK前调用已有 `pytest.importorskip('temporalio')`，沿原测试入口核core无SDK为skip、SDK环境仍执行原六个节点。本审已通知根，尚未把在途修正版当作当前r1结果。

## 需求与测试价值核对

`_serve_cycle` 一次构造normal与stop各1个局部Semaphore，v1／v2 normal共用前者，v1／v2 stop共用后者；四个真实注册配置各保留1活动槽。版本类、活动名与queue沿原封闭表选取。活动wrapper包住完整invoke，许可直到原 `_CycleOperation.run`、`_CycleCandidate.run` 和 `stop_live_controller` 返回后才释放；普通取消、重复取消与等待取消没有发现另一条早放路径。

SDK scheduled/start绝对截止在排队前取min，同时固定BOOT cold window；等待与invoke消耗同一原SDK allowance，获取许可后未重开窗口。小于1秒在原cold合同前保守拒绝；取得snapshot后原control／work继续收窄，stop仍用原total。未改变SDK10秒或control30来追求正例。

两normal的正常shutdown并发开始，完成后才进入两stop；fatal callback在SDK等待活动cleanup前唤醒服务。这个设计在通常shutdown、主task重复取消和已测fatal边界成立，F1单列其缺口。Semaphore等待／持有、S stopped帧之后仍等S退出、真实H后代回收等新增断言保护实际状态转换，并非仅复述配置。

撤回新增“shared start必observed”参数合理：原Workflow SDK10秒上限不承诺prepare／owner／attempt／dispatch全链一定成功，记录中的超时不是放宽预算的理由。其风险有真实既有接缝：六个新S/H用例保护排队／执行deadline、取消和许可；原Workflow测试保护机会已占与unknown只对账；`tests/test_training_cycle_controller.py` 原pending-Popen取消／deadline、loop teardown的spawn／confirm、notification race／真实wait保护candidate清理。最后一组本候选未提供重跑证据，且这些接缝**不证明生产共享factory在真实SDK10秒内成功start**。仍须保留该正向未验项，不以缺省factory下control30的通过转授服务。

独立AST比较确认原 `TrainingCycleWorkflow` 与 `TrainingCycleWorkflowV2` 完整类不变；此次产品函数差异限于factory内部invoke／wrapper与服务shutdown。协议、cycles、budget、execution、submission、283参考、原来源25＋4、服务argv／70秒stopwait未改，schema3 controller／worker／budget／context的effect关闭仍保留。未发现本片擅自补半套Failure／Payloads／Memo容量或宣称完整M1c／真实服务／CPU两轮完成。

## 已读证据与其界限

以下均为独立读取既有raw／JUnit／manifest，非本审重跑。私有原件统一在 `.ergora/checks/training-cycle-v2-runtime/`。

|原件|可支持的结论|不能支持的结论|
|---|---|---|
|`v2a/affected-runtime-r1`：63过，JUnit11.325秒|真实默认sandbox／SDK activation、原V1三history replay、V2/v3与10个本地bridge／poller服务lifecycle场景|真实Temporal服务、直接run取消或服务全loop teardown|
|`v2a/affected-submission-r1`：15过／1失败，303.406秒|原S/H取消、6／66stop分支、容量／最后gate；失败shared-start保留原身份与原件|失败参数已过或SDK10秒成功start|
|`v2a/final-submission-r1`：7过，JUnit78.832秒；runner80.28秒|冻结后六新S/H节点与原缺省start；输入manifest无delta|共享factory成功candidate start，完整真实业务|
|`v2a/sdk-run-cancel-red-r1`：1失败，JUnit1.601秒；runner2.210秒；产品worker仍r1|直接取消两normal SDK run后，原cleanup未完成即进入stop shutdown，实证F1|F1修复、实际OS资源泄漏／完整服务loop teardown已验收|
|`package-r1`：新非editable core／SDK、wheel SHA `4348d4071f281072ed8d3933ddaa93b1244ba23ecf2159e4e7555f478914e899`；668产品、源／wheel／安装字节与执行位同一，SDK1.34、core无SDK、283参考／依赖检查过|该准确r1安装身份与导入位置|修正版安装、真实服务或F1已解决|
|`package-r1/installed-cycle-runtime.xml`：63过，JUnit15.671秒|r1安装中对应runtime接缝|更多submission节点、在途自身模板或后继候选通过|

F1、F2修复后须另冻准确完整候选，保留原失败并按受影响接缝复核。原模板、当前安装后续检查、真实旧queue成功start、完整M1c／10MB最终消费者、统一效果开放、CPU两轮和真实外部收尾分别保留未验；本报告不转授这些通过。
