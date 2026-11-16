# M6-V2a：封闭服务拓扑与共享配额

2026-11-16。r3 四文件候选已冻结；SDK 直接取消边界按根批准的最小方案修正，12项 lifecycle／65项受影响检查通过，准确候选的固定安装与同片独立复核由根接续，当前尚未验收本片。r1／r2 和原红例保留。本片只交付原 cycle 服务内四个 versioned poller、两份业务许可及等待／清理边界。**所有 schema3 effects 继续显式关闭。** 完整 M1c、M5 晚处正向入口、统一开放候选和真实 CPU 两轮仍是后继，不能由本片通过代替。

## 身份、授权与实际 owner

唯一可写源码树 `.ergora/worktrees/training-cycle-v2-runtime`，分支 `feat/training-cycle-v2-runtime`，准确基线 `f9b9d72d6d5f2102809a3cafaadb2226bba0966b`；进入时 clean。已含最终 M6-V1 `2acdcc44`、M5/native 与 inspection-only a1。主树产品、他树、用户 control-home、PLAN／CI／283参考／原锁／公共模板均不改，不安装、不访问真实 Temporal、不跑模型或业务训练，不提交／合并／推送。

已读根／src/ergora／tests AGENTS、组件协议、当前 PLAN、[M6 最终设计](../plans/2026-11-16-training-cycle-v2-runtime.md)及[设计审](2026-11-16-training-cycle-v2-runtime-design-review.md)、wire／capacity／M5 设计和前置交付／源审。应用 maintainable-project-delivery 与 ergora-codebase-quality 的 module-design/test-seams。根明确选定 V2a 最小 closed 子片；本片不得再派代理，新的安装／原模板／fresh 独审由根接手，未由实施者自批。

实际调用为 `services` 原 argv → `cycle_main` → `_serve_cycle` → `create_cycle_activities` → 实际 SDK wrapper → `_CycleOperation`／`_CycleCandidate`／`stop_live_controller` → 原 S/H、peer、唯一 reaper。没有新增服务、管理器、账本、ABC 或输入协议。

## 分期与修改范围

1. 仅在原 `reference_training_worker.py` 内构造 normal／stop 两个局部许可，注册 v1／v2 normal 和 v1／v2 stop 四个 SDK poller，各自仍为1活动槽。wrapper 持许可至原 S/H／candidate／peer 清理返回；normal 和 stop 不共享许可。
2. 共享许可等待之前固定原 cold BOOT window，按 SDK1.34 的 `Info.scheduled_time + schedule_to_close_timeout`、`started_time + start_to_close_timeout` 取最早截止；等待和实际 invoke 都消费同一 SDK 截止，拿到许可后不重开 cold。原 policy／授权 work／total 继续收窄，原 source 九字段／payload／history 不增字段。
3. 关闭时先同时请求两 normal poller shutdown 并等实际清理，两 stop 保持可用，再停止两 stop。fatal／重复取消继续走真实 SDK run/shutdown 与原 cleanup；不扩大70秒服务 stopwait。
4. 沿原 `tests/test_training_runtime.py` 的真实 SDK lifecycle、`ActivityEnvironment` 和 S/H 接缝验证注册、混合版本配额、等待／取消、deadline 和 cleanup。只替 bridge／无关业务叶；无独立新接缝不增加测试文件／CI job。旧 v1 history 和显式 schema3 负 gate 保留。

## 明确未关闭的后继

- 完整 M1c Failure：当前 wrapper 仍有 `str(error)`／cause；SDK1.34 在 wrapper 返回之外再次 `encode_failure`，加入 traceback／cause。局部小异常或 helper 预编码不能证明最终 Failure ≤32KiB；本片不加半套 converter，也不认证 Memo／assembled N32／signal／query／outcome 全边界。
- M5／10MB：`BudgetedStart.source`、`validate_context` 已先调用完整本地 verifier 再显式关闭。CycleAdmission.bind／source／Execution／native 外层与 callback 的所有更晚正反入口仍须在同一统一候选可达，ordinal>0 的完整链到0、原25＋4／ROOT／stop／budget及 attempt／ack 后 gate 不能省略。
- 正式 V2 producer、真实 SDK scheduled history、固定非editable安装、真实服务 CLI 与两个 CPU 候选顺序 archive、恢复／丢回复／取消／预算及捕获进程收尾，均由根在后继接续。只在此隔离片注册新 poller，不把主树或任何效果开放。

## 逐步状态与证据

已完成只读基线／owner／SDK字段核对，并在改源码前向根报告分期与阻断；根已确认按 V2a 推进。实际 SDK1.34 字段来自 `Info` 及 SDK 从 bridge Start 构造 Info 的原实现；没有给 source 九字段加 deadline，也没有把 ActivityEnvironment 当成服务器历史。

实现留在原 worker：服务一次构造两个 `asyncio.Semaphore(1)`，四 poller 共用本族许可；所有 SDK poller 活动并发仍为1。wrapper 排队前将原 BOOT cold window 与两个 SDK 截止绑定；原 cold 合同最短1秒，余额不足时保守拒绝。排队超时无 S/H；已持许可时 deadline／取消沿原 run 方法等实际 S/H／根／peer cleanup，再释放。两 normal 同时发 shutdown、共同等 cleanup，之后才停两 stop；没有扩大服务 stopwait。

测试复用原两个测试文件和原 operation fixture。fixture 的新故障只在真实 H 的原件读取前可控阻塞并产生实际后代；S 写出匹配 stopped 帧后暂停，用来观察“已有 stopped 仍须持许可等 S”。normal/stop 及 v1/v2 共用同一实际 factory／SDK context；没有 mock verifier 为通过，也没有把缺失 controller 的 unknown 当作训练正面结果。

## frozen-r1 准确范围

基线不变，完整差异只有以下四项，均为非执行文件；untracked=0。`complete.patch` **44,476B**，SHA256 **`85a97b67e888eaf4e369d0e3a3221553524691a4f77645b49fe64cf72b5e97bf`**。完整2064 tracked 输入含 raw bytes／SHA／执行位及当前 mode，`complete-inputs.json` SHA256 **`f01b71e22d604d35590bd8080a87485e739fa81e102d82592d1e02c8bfc9b7f9`**。原件在本片私有 `v2a/frozen-r1/`，保持不覆盖；后续机械依赖保护和 reviewer 要求的红例分别记账。

|文件|frozen-r1 raw SHA256|
|---|---|
|`src/ergora/reference_training_worker.py`|`8ff852bf984a20b9a6cab25c5737cbef1f521cd1fbde595746d31e705e96b110`|
|`tests/fixtures/training_cycle_operations.py`|`8f944b7c3bf7a80f1998c047514e5420ae234a42e8bf038ad86e206e772d5357`|
|`tests/test_training_runtime.py`|`dccc48cd38afe2ababb8c563c4866195757fa26d5feec74ece1521e17b09c805`|
|`tests/test_training_submission.py`|`3657b6700103717af476fd306b5a639c0d6dfbb1c365b1455692e666131bd978`|

原 V1／V2 Workflow 类完整 AST 均与基线相同；原协议、cycles、budget、execution、submission 产品文件、旧25／四measurement表、283参考、CI、服务 argv／70秒stopwait未改。旧 pin 仍拒绝新产品来源，不补写旧 owner 或授权。

### frozen-r2 可选依赖保护

仅在新 `shared_cycle_activities` fixture 入口补 `pytest.importorskip('temporalio')`，使无 SDK 的 core 环境进入该 fixture 时正常 skip；产品 worker 与 r1 完全同字节。r2 完整 patch **44,515B**／SHA256 **`1cfbcc75c13ba47693674efcd5470a3f979702832aaba1dc4c2328f45f182370`**，完整输入 SHA256 **`27239764fe9ff959a5e8f75590f184ae32278d4829c73040965ce6ea1a28e0ce`**，2064 tracked／untracked0。submission 测试 raw SHA256 变为 `58187eb7acb3ed5145264c20ddfbbbd0ca845accf3919b8f770c9b0cd2644a7f`，其余三项仍为上表身份；机械差异原件为 `v2a/r1-to-r2.patch` 和 `r1-to-r2-identity.json`。r1、r2 冻结均保留，不能用新 red 测试输入覆盖。

r2 之后先只加 reviewer 指定的 `normal-run-cancel` 红例，当时产品 worker 仍为上表 `8ff852bf…`；该红例完整差异、runtime 测试 raw 与输入均另存其运行目录。根先前接走的 r1 固定树／安装／模型结果只认证其准确身份，不自动转授 r2 或后续修正。

### frozen-r3 最小 SDK 中止状态修正

根核真实生产 caller 并获同片 fresh 独审认可最小设计后，明确批准在原 `finish_worker/finish` 修正：先回收本 owner 的公共 shutdown waiter，再用 SDK 公共 `is_running/is_shutdown` 识别 run task 已结束而 SDK 未完成；本组 `gather(return_exceptions=True)` 等另一 normal 已有 drain 完成后才报固定 incomplete／unknown 错误，不主动进入 stop 组。`cleanup.result()` 抛错也在 finally 等 connecting／waiting 结束、移除本服务 signal handlers。没有 SDK 私有事件写入、复制 shutdown 算法、重启 run、新 manager／pool／thread 或预算延期。

完整四文件 patch **50,110B**，SHA256 **`25cf19fa37473e72e81255e8f5680033868fe1b60eb114bd076cec437064997a`**；完整2064 tracked 输入／untracked0，`complete-inputs.json` SHA256 **`e7f4082abb67e613e55eee78e09835a6a5f313a80ecc357e53de935d83ce9495`**。准确原件为 `v2a/frozen-r3/`。worker raw SHA256 为 `932159e3e5ad25095327e2cc0d205c84d96abbd9a7a743895c391eae6c4196a4`，runtime 测试为 `cb34ef5d2b41df9d3cb707874e567fc2a03e11325103d61d1013c130e319ae7e`；fixture 和 submission 测试分别保持 r1／r2 上列身份。

相对根固定 r1 提交 `019c667a79e965a4ea4a74d37667bd7a0f7f1e81` 的机械差异另存 `v2a/r1-to-r3.patch`，10,794B／SHA256 `f5f70d4d2e2dd65abf8f960b4b64536db28280e38af6335416ee33d8b75d3a8f`。`static-final-r3.json` 逐2064项核 frozen raw／mode／执行位及完整 patch；两 Workflow 类仍与基线同 AST，活动 factory 完整 AST 与 r1 同一，原 protocol／cycles／budget／execution／submission／services／argv 七文件均未改。r3 两批检查的完整输入 SHA256 均为 `8817d890c985b110bcc7f37082b60469ad5ee0babcede78bff494c8afb8973b5`，逐项 raw／执行位与该 freeze 相同；未转授此前运行输入。

## 本地检查与保留的失败

所有测试使用现存开发解释器 Python3.11.15／SDK1.34.0，`PYTHONPATH` 明确指向此隔离源码；未安装包。测试批原件保存实际 argv、cwd、选定环境、完整输入／执行位、JUnit、raw stdout/stderr、pytest 与 observer 的 BOOT／start_ticks／PID、wait 终态，冻结另记 mode。最初快速红例 `red-service.log` 的 PID 未捕获，不补造；下表的基线复现完整记录这些身份。

|证据目录|实际结果|范围|
|---|---|---|
|`baseline-red-r2`|2 failed／5.58秒，预期红|准确 f9b9d72 package 的私有只读副本＋当前测试：旧服务只出现2 poller，两个 normal 注册场景到原等待上限；完整基线包 raw／mode另存|
|`service-r1`|8 passed／1.20秒|真实 SDK `Worker.run/shutdown`，bridge／poller为本地替身；两版本 validate／fatal／收尾竞态，非真实服务|
|`permits-r1`|2 passed／1 failed／25.01秒|首版 fixture 错把取消 H 当作成功 H，等不到只在成功分支读取 stdout 的 marker；保留失败，没有改产品绕过|
|`permits-r2`|6 passed／38.70秒|修 fixture 为真实 stopped 帧后暂停 S；混合版本两许可、取消等待、重复取消至实际 S 返回、SDK scheduled／started 的等待与 invoke 截止、loop teardown 实际 S/H／后代退出|
|`affected-runtime-r1`|63 passed／11.33秒|加入正常 shutdown／主 task 重复取消后的10个 lifecycle 场景；原 V1 三份 history 重放／默认 sandbox、V2/v3 及容量／预算／取消接缝；生产 bridge 仍未连接|
|`affected-submission-r1`|15 passed／1 failed／303.41秒|旧缺省 start、共享 stop 6分支、旧66 refs、原 S/H 取消、容量、最后 source/window 和实际 schema3 closed；唯一失败是下述新增 shared-start 错误正向预期|
|`final-submission-r1`|7 passed／78.84秒|准确 frozen-r1 输入：六个新实际 S/H 场景＋原缺省 start|
|`final-submission-r2`|6 passed／37.20秒|机械 SDK 保护后的六个新实际 S/H 场景；不继承 r1 原缺省 start 的输入身份|
|`no-sdk-probe-r2`|实际 fixture 入口 skipped，SDK modules loaded=0|通过 meta-path 明确阻断 SDK import 的缺依赖模拟；不是新非editable core 安装验收|
|`sdk-run-cancel-red-r1`|1 failed／1.61秒，reviewer 指定的真实红例|真实 SDK 两 normal `Worker.run` 已进入 cleanup 后直接取消；tasks done/cancelled 而 SDK 未 finalize，当时实现却开始 stop shutdown，见下文待复核 finding|
|`sdk-lifecycle-fix-r1`|12 passed／2.10秒|r3准确输入：原10个 lifecycle 场景＋同 harness 两 normal 和单 normal 直接中止；单 normal 中止期间另一 normal 的真实 SDK cleanup 未放开，serving 不提前结束；之后显式 incomplete／unknown。测试以公共 shutdown 收尾仍活 stop，未私设 completion|
|`affected-runtime-r3`|65 passed／11.47秒|r3冻结后的原 cycle_ 选择，原63项＋两个新中止场景；两 Workflow AST／默认 sandbox、原 V1 history、V2／v3及普通关闭／主 task 重复取消／fatal 保持|

### 原 SDK10秒与新增 shared-start 预期

原 Workflow ordinary 的 `schedule_to_close_timeout` 和 `start_to_close_timeout` 都取 `min(10, control, work)`，不能因 candidate 的原 control=30秒就把 SDK 截止改成30秒。原正向单测缺省 factory 没有服务共享许可，ActivityEnvironment 的 epoch deadline 从未约束原 candidate；它在原范围通过，不证明服务 SDK10秒正向。

本片曾给该旧正例新增 shared 参数，并按真实 Workflow 取 SDK10秒，仍要求 `observed`。实际到10秒停止 dispatch：prepare／owner confirm／原 attempt 已占，dispatch H stdout 为空；独立 stop 后原预算根收尾。完整原件及 `start-sdk-deadline-r1.json` 保留。根确认该新增必成功预期不成立，只撤这个新增参数；**原缺省正向正文／预算／保护均保留**，不扩大 deadline、不重开 window、不吞掉失败。SDK deadline／cancel／持许可至真实 cleanup 的风险由六个新 S/H 场景和原 Workflow 单次机会／只对账覆盖。

真实旧 queue 正常 start 在原 SDK 截止下的正向仍未验收，留给根的固定安装／真实服务现场；本片不称“可训练”。上表15个通过只认证其实际原件与入口，不把失败参数或默认 factory 的长 control 成绩转授服务。

## 开放 finding：SDK run 终止不是 cleanup 完成

独审要求直接取消真实 SDK1.34 的 normal `Worker.run`，与既有只取消主 serving task 的场景区分。新红例先经 SIGTERM 请求正常关闭，等两个 normal 都进入真实 SDK `wait_all_completed`，再取消两个实际 run task；原 cleanup 仍暂停。两个 task 均 `done=true/cancelled=true`，两个 Worker 均 `is_shutdown=false/finalized=false`，当时 `finish_worker` 仍提前进入 stop 组。raw／JUnit／输入／PID 原件保存在 `v2a/sdk-run-cancel-red-r1/`，完整输入 SHA256 `0aad307d791e51732f8df8106deeb5c2c0fd28595a29d3dbc7b93b437681dd54`；`test-root/test_cycle_service_closes_peer0/sdk-run-cancel.json` 是放开 cleanup 前的实际观察。原红例测试 finally 中设置 SDK completion event 只为救援 teardown，不能称真实 cleanup 或产品恢复。

生产调用为 `services._prepare → reference.training_cycle_worker_command → cycle_main → asyncio.run(_serve_cycle())`。cycle 主循环将 SIGTERM／SIGINT 注册为 `stopped.set`，SDK fatal callback 也只设置同一事件并留存 failure；生产源码没有 `loop.stop` caller，也没有直接取消四个 Worker.run 或其 SDK 内部 task 的 caller。主 serving task 取消不经 `asyncio.wait` 传播给四 run task，finally 用公共 shutdown 等原任务；正常完成 drain 后才由 Python3.11 Runner.close 取消其余任务。外部 `loop.stop`／全 loop tasks 取消会破坏这个顺序，应与原正常信号和主 owner 取消区分。

SDK1.34 `Worker.run` 的公共文档明确取消也可能中断 shutdown，并建议显式 `shutdown()`；实际 `shutdown()` 只设置请求事件、等待 completion，没有公共 resume/finalize API。不能复制 SDK 私有清理算法、私设 completion 或以 task cancelled 冒充 stopped。真实 caller／SDK／Python Runner 原文和 raw hashes 保存为 `v2a/sdk-lifecycle-boundary-r1.json`，SHA256 `acac3a0b261bb9cd1aa00466a42edd544496375127c76e644523d8f4f5974f52`。

根和同片独审已确认上述最小公共状态设计及支持范围，r3 实施／本地实证见前文，**F1／F2 的准确候选独立复核仍待根发起**。正常 SIGTERM／SIGINT、主 owner 取消和 fatal 都由既有公共 shutdown 完整 drain；loop teardown 的可保证范围是根 main 完成 drain 后进入 Runner.close。外部强行 run.cancel／loop.stop／全 loop tasks 取消没有公共恢复保证；实际资源状态保持 unknown，错误不能替代 cleanup 证据，也不承诺此后 stop 仍可用。r3 测试在报错前确认服务没有主动停止 stop，随后仅测试显式公共 shutdown 回收它们；原已中止 normal 始终未 finalize，不伪造 completion。原70秒 stopwait不变，旧63项通过不关闭此新边界，独审复核前不能验收本片。

## 捕获进程身份审计与交接

`v2a/process-audit-r3.json`（SHA256 `0075c58b4648634c2542fc47a269ee1fb96f9a332d80ad0f6f71617847297e12`）在本地检查结束后逐份只读核对这12个证据目录中实际捕获的完整 PID／BOOT／start_ticks：**194个实际身份均 absent**，另3个 `synthetic_execution` fixture 身份明确分列，不混入真实进程数。112个非JSON条目已逐项核为零字节 `permit-release-*`／`permit-finish-*` 控制旗标，分类另存 `process-audit-r3-summary.json`；没有未分类项。原 `process-audit.json` 保留，不用新统计覆盖历史原件。该审计仅覆盖已捕获身份，不声称全系统零残留，也不把 SDK fake bridge 的 finalized 代替真实执行器 durable stopped。

当前源码停在 frozen-r3，不提交／合并／安装／模型或访问真实服务。根下一步需从该准确候选建立固定树／新安装，发起同片 F1／F2 独立复核，核 core 无SDK fixture skip 与 SDK受影响 lifecycle；原模板、真实服务旧 queue SDK10秒正向 start、完整M1c／M5最终消费者／效果开放／CPU两轮分别按其准确入口验收。r1模型或安装若结束，仍只记录r1结果，不自动认证r3。根负责 PLAN 与公开 SDK 边界补充，本实施者只更新本交付，不自批 closure。

私有证据位于 `.ergora/checks/training-cycle-v2-runtime/`。源码、自查、安装、原模板、独立审查、真实服务与业务质量分别记账；未运行或未到达的边界保持未验。

## 根接续：准确r3独审、新安装与模板

作者r1→r3完整增量已移植到固定树 `training-cycle-v2-runtime-fixed`，产品 `82c6595907b4d2173890b82e6fcb6ab8920832b1`，基线 `eba8680`。本基线相对作者基线仅为文档；产品／测试与作者freeze逐文件同一。固定树完整四文件patch为 `1722801f99bf0b180915f58da5261b6b69b497468a62c61c58a338445b8a9d4d`，其git头部与作者full patch不同；对应关系、完整输入和changed-files另存 `fixed-r3/`，不能混用两种patch身份。

[新的fresh-context r3源码审查](2026-11-16-training-cycle-v2a-r3-source-review.md)需求／维护性两轴approve，开放0；F1／F2在此准确候选关闭。源码、SDK公开状态、12／65项原件及完整输入均独立核过，未把r1安装或模型结果转授。

`package-r3/` 的新非editable wheel SHA256 `af6089392dd5040b7461422df7c6236e2cc930747358440209af30ea1ea92730`，core／SDK各668完整产品与source／wheel的字节及执行位同一，实际三训练owner从site-packages导入；283参考与依赖检查通过，core无SDK、SDK1.34.0。实际新安装runtime **65 passed／7.793秒**、六个实际S/H许可／截止／取消／收尾接缝 **6 passed／36.297秒**；core仅加入测试runner，不含temporalio，同六节点 **6 skipped／1.147秒**。准确argv／raw／JUnit和捕获的自有进程身份见对应 `installed-*.command.json` 等原件；未重跑未改变的完整业务大套件。

同一新安装使用原Ergora `refactoring-quality` 的结构审查模板，完整原始要求／四文件／差异／仓库规则均入实际stdin。优先Claude的r3调用 **420.591秒超时／exit1**，原件 `self-review-r3-claude-code/`保留，不能视为审查通过。已沿用户原授权回退Codex，新调用在途，结果另记实际后端；不声称异后端通过。尚未合入或发布；真实服务旧queue正向、完整容量与CPU两轮仍按原计划分别验收。

后继同一原模板的Codex回退实际 **31.254秒／succeeded／approve**，输入及3份原资源完整进入stdin（663,217B，SHA256 `90dc8a18124d060c23e9da1ed42c489892a6902af7a9a8bfc443a2bb026c09cb`），原result SHA256 `c18b993d68de0779e5628164adfaa78b2af48a32a44f3d1167be1dd5a36f4192`；原件在 `self-review-r3-codex/`。Claude超时不覆盖，模型回退不当作独立异后端成功；新的fresh源码独审另有报告。本片源码／新安装／原模板边界已经分别闭合，产品已普通合入开发分支；联合安装、公开候选及其自己的CI接续，不授予真实服务／业务或后继M6效果。
