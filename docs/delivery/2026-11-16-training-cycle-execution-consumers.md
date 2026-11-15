# c1b2b 原执行请求与运行观察消费者

日期：2026-11-16。当前状态：**r5源码、CI组合、新非editable包、15项安装检查、SDK-free真实inspect、自身模板和真实Temporal六活动现场均已完成；最终独立需求／维护性两轴approve／0。固定bcc已真实导入开发树01ef，保留已另审的Windows两行提前skip；普通发布及准确候选CI接续。** 本记录属于主项目 docs；实施范围以[已独立通过的 r2 设计](../plans/2026-11-16-training-cycle-execution-consumer.md)、[后续消费者顺序](../plans/2026-11-16-training-cycle-runtime-consumers.md)和[独立设计复核](2026-11-16-training-cycle-execution-consumer-design-review.md)为准。各历史检查保留准确候选与范围，不将设计结论转作运行证据。

## 完整片闭合与导入

[新安装](2026-11-16-training-cycle-execution-installed-checks.md)、本文末节15项准确检查和[真实现场](2026-11-16-training-cycle-execution-live-acceptance.md)分别验收；[最终独立复核](2026-11-16-training-cycle-execution-product-review.md)另核193份原文件、56 refs、完整两条执行链、原controller input/memo/intent/receipt、实际attempt2只观察、真实flock时序和三个实际SDK封套容量，并独立观察171身份live0／unknown0。完整c1b2b需求／维护性均approve，开放0；两CPU故意缺evidence的gate false保持，正式c1c、接受层和训练质量不因此通过。

已普通merge固定`bcc304894622040a7d844f8c6f9ddfded65aa895`，开发树提交为`01ef69b71137df860e8fc433362d039ae241e744`。导入后相对bcc的src／scripts／.github／pyproject逐字差异0，产品仍同wheel55029；tests仅多两行另行fresh审查通过的[Windows提前skip](2026-11-16-windows-sdk-fixture-skip.md)，原fixture、测试体及参数保持。原安装的183输入身份不改写为这两mark已在原运行中出现。普通发布／准确候选自己的CI另记，未自动合main；后继c1c可从该完整本地门槛开始。

## 准备基线与授权

专属源码工作树为 `training-cycle-execution`，只读检查 HEAD `af176cf6e79adb9c6ef6f32946672bc77cdb89de`，初查 clean；最近三提交为 af176cf、97a0bbf、eedba08。af176cf 只调整一项正常测试的显式控制窗口，产品同前置 97a0bbf。主 docs 的 PLAN 仍把服务 N32 混合 unknown／容量现场补验列为在途，本片不自行关闭该门槛。

已读根、源码和测试 AGENTS、主 PLAN、组件变更协议、r2 两份消费者计划及其设计复核；使用 `maintainable-project-delivery`、`ergora-codebase-quality` 的 owner／测试接缝规则。主控限定本阶段只写本记录，不改 PLAN、他人报告、产品、服务端口或其他工作树，不运行全 suite、不提交或推送。独立实现审查应在实际实施和定向证据具备后另行进行；本次准备不是该审查。

## 已核接缝及真实消费者

|既有 owner|源码观察与后续最小接入|
|---|---|
|`reference_training_worker.create_cycle_activities`|现有工厂使用真实 `activity.info()`、严格业务输入和 SDK converter 容量检查，再驱动 `_CycleOperation`；注册表目前只有四个 v1 action。新增两 v2 action 沿同工厂／normal 槽接入，旧四返回封套保持。`_serve_cycle` 的 normal／stop 独立槽仍由原入口持有。|
|`training_execution_protocol.validate_cycle_activity_request/context/operation`|已有六字段身份、完整 SDK 来源、mode/action 映射、candidate context 和 BOOT/window 验证；两新 mode 必须同时进入 CANDIDATE 与 WORK 集合，不能只接观察集合。原 `cycle_operation_remaining` 已能消费 compute∩固定 window。|
|`worker._cycle_operation`、`_cycle_submission/_cycle_target`|H 中 `_load`、`_activity_binding` 认证原授权和父 receipt；原 selector 从冻结 ordinal 取得候选并核 intent／owner。新局部 H 算法由 `_cycle_operation` 一处调用，隐藏请求与三类观察的组装；不需要新模块、manager、ledger 或缓存。|
|`worker._select_cycle_project`|既有初始化选择原安装和 native 配置。冷 H 的 `_dispatch_controller` 已进行该选择；新的普通 H 应只选择一次，随后复用 operation／intent／owner，不再借 public execute/status 产生新 helper 或当前 preflight。|
|`reference_training_execution.Execution.request/check/current`|`request` 已完整确认 revision／intent／固定 run／native raw SHA，在父共享许可和 execution.lock 内不可覆盖发布；`check` 核原父 history、子 run/memo、QUEUED 和 job。新增 H 直接调用它，不调用 public execute。`current` 目前只核原 compute／来源等，尚未消费本次 operation window；这是 r2 要求实际扩展的位置。|
|`reference_training_budget.BudgetedStart`／`Execution.admit`|原 root 等 request 并持唯一 launch 机会；已有空／部分 launch 一样消耗机会。新消费者不得调用 `ensure_owner`、重建 root、重新 admission 或 native execute。`request` 的 schema2 H 来源要求与 root `admit` 的既有上下文须分别处理，不能令 root 错用已结束的短 H window。|
|`training_execution_protocol.ExecutionRecords`|`load` 验原五类链、`request_record(actor)` 验 start attempt／receipt 和 native 完整请求及 raw SHA，`observe(durable=True)` 同步并重读同一链。无 request 时 `load` 不会读取 native，所以不能据此合成 native QUEUED；部分／损坏链不能当 not_requested，也不另写容错扫描器。|
|`reference_training_runtime.lookup/observe`|固定 receipt.run_id 的 lookup 核完整原 Experiment，caller 还需核原 memo；observe 返回实际 Temporal status、phase、完整 Binding，RUNNING query 与 COMPLETED outcome 分开。缺 receipt 不查 latest run、不补候选 receipt。|
|`agent_platform.training.LocalTrainingAdapter.poll_job`|`exact_job` 验原 Binding／job，poll 验 result Binding／job 后返回 native 原状态。它与 runtime phase、durable stopped 是独立事实；不调用 collect_and_gate，不推 accepted／next_allowed。|

准备阶段没有观察到需要重开设计的矛盾。新增 source 检查仍有明确实施义务：把完整本 H operation 经原 `_Submission.payload.cycle_operation` 交到 Execution，使用原 protocol validator 和原 request.json 对照本 H mode/action/attempt、controller/ordinal、候选 intent、来源及父身份；不能只传 deadline 或复用 `cycle_start_source` 授权新 request mode。私有辅助函数若确需提取，只应承载这个内聚不变量，其生产消费者是原 Execution；不为未来调用者另建接口。

## 最小验证边界

优先扩展已有测试与 fixture。当前工作树 controller／SDK tests 仍位于 `tests/test_training_submission.py`；另一工作树的 CI 机械拆分不在本片编辑范围，未来整合再按实际迁移位置适配。

|行为／静默风险|现有接缝与必要观察|
|---|---|
|SDK 来源、旧合同和 v2 封套|`cycle_sdk_activity` 使用真实 SDK `ActivityEnvironment`／converter，跨真实 S/H；`controller_dispatch`、`training_controller_service` 提供原 history/memo 双。沿该路径增加两 action、ordinal=0、attempt>1 只观察、namespace/type/queue/run 漂移，保留旧四行为。它是本地 SDK 协议测试，不是真实 Temporal。|
|正常一次 request 到唯一 launch、丢回复和部分原件|复用 `controller_admission`、`cycle_candidate`、`service` 和现有 request-writer／consumed-launch tests；保留原 root、锁及链发布。断言原 request→唯一 launch，重复／重投／丢 completion／部分记录不补 root 或机会，而非仅 mock `Execution.request` 被调用。|
|receipt 早到、双 QUEUED|`training_submission_client` 的固定 run/query/native 接缝可延迟 job 或首次 poll；先记录 submitted＋SUBMITTING/native unconfirmed，再出现同 Binding/job 的双 QUEUED。request 一经调度永不重授的正式 history 分支仍属 c1c，本片仅证明 facts 足够表达等待和阻断。|
|最后同步读取过窗|扩展 `training_cycle_operations` 的真实 H 故障接缝，在异步验证之后、`current` 同步读取期间让 operation window 过期但 compute 仍正，再允许 H 继续一次；应无新 request/launch。不能只观察 S 已杀进程或外层 timeout。分别令 cold／control／compute 最短，核同一起点。|
|runtime/native/reap 交错|复用 runtime fixture、原执行历史读及真实本地 publication；覆盖 native result 早于 reap、reap 早于 phase，原事实分别返回，无接受或后继字段。|
|project/source/stop 漂移|沿已有最终 gate／controller pause／stop tests，使漂移发生在最后同步边界；应拒 request，保留已消费原件，不改变 schema1 人工确认和原 root 收尾。|
|容量及完整 ref/inline|复用 `test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation`、真实 H frame 和父 late/cleanup tests；含新增 facts 的完整 v2 封套按 `Payloads.ByteSize()` 守 32 KiB，metadata 过界整体拒绝，不删字段／原错误／stop 分支。|

可用前置 `package-r3/venv-r3-sdk` 的已有解释器进行后续源码定向测试；须显式选择本工作树源码并记录实际 import 来源。该解释器及前置 wheel `081aab45` 仅是依赖环境，不会因此成为本片新安装结果。新非editable core／SDK、283参考／source pin、真实 Temporal 和独立预算根的 E6/E7 仍需在实施后分别验收。

## 只读准备时的实际检查和未验范围

本次仅执行 Git 身份／状态、`rg` 定位与文档／源码／fixture 阅读；核实前置 package-r3 SDK 环境目录存在，未执行其中解释器或声称重新安装。唯一写入为本记录。未运行测试、服务、训练、native executor、安装／构建、自身模型审查或独立产品审查，未修改任何产品／测试／资源／PLAN／其他报告，未 commit／push。

准备交回时的下一步是等待主控服务终核和明确实施指令；该授权现已收到，实施状态见下节。正式总 Workflow、标准 sandbox/history/replay、accepted／rounds／后继和 WA 人类设计关卡均另片交付。kernel v3、全部祖先资源与逐级收窄权限不在本片改动范围。

## 已授权实施第一步：源码与短检查

主控后续明确发送“服务片验收通过，开始实施”，前置服务终核由其负责。本片仍基于 af176cf，不合并主树或 CI 工作树；后续只改三个原 owner 和必要既有 tests/fixtures，不 commit/push、不改主 PLAN。另一 CI 工作树的完整组在跑，按主控指示暂缓下面两个真实 S-H 新场景；没有启动服务、安装、真实 Temporal 或训练。

|当前改动|具体行为与所有者|
|---|---|
|原 protocol|保留四 v1 名称，新增 request-execution-or-observe.v2 和 observe-candidate.v2；两新 mode 同入 CANDIDATE/WORK，六字段＋ordinal0、SDK source/action 约束沿原 validator。新增 `cycle_execution_source` 只有原 `Execution.current` 一个生产调用者，用于核完整本 H request.json／controller／intent／来源，不产生执行能力或读取框架。|
|原 Execution|新增 H 的单一 `request` 调用始终带本 H 完整 operation；原 `current` 完成同步来源／身份读取后重核父 stop 和同一 operation remaining，在原锁内 publish 前后均生效。原 root `admit` 的 operation 不携短 H payload，保持其原 compute/context 和唯一 launch 所有权。原 schema1／schema2 公开完整确认请求不增加短 H 窗口。|
|原 worker|新 `_execution_candidate_operation` 被冷 inspect 和新普通 mode 两处调用，负责本地事实、runtime/native 独立观察和条件 request；局部 `execution_observation` 在请求前及发布后的原链重载复用，`problem` 保存完整局部异常。SDK parent 只消费 H 内存投影和原 refs，收窄冷10秒／control／compute一次窗口；normal 注册五项，stop 独立一项，槽仍各1。|
|既有 fixtures/tests|增加 SUBMITTING 服务状态和锁内同步读取跨窗的 H 故障。两新 S-H 用例分别覆盖冷事实→submitted先观察→双QUEUED→唯一request/launch→重投/部分记录只观察，以及允许同步读取在窗口后返回仍不publish；尚未执行。SDK拒绝来源测试在任何 `_CycleOperation` 构造前拦截非法 ordinal/额外权限字段/本地活动/namespace/type/action。原服务生命周期 fixture 注册项随工厂扩展。|

实际短检查使用既有 package-r3 SDK 解释器、`PYTHONPATH` 明确指向本专属树 `src`，记录为**源码验证**。`short-r1`：`tests/test_training_runtime.py` 的新增未信任输入拒绝、原32KiB含metadata容量、原服务SDK生命周期四fault，共 **6 passed／1.02秒**（runner总1.64秒）；命令、各修改文件SHA、HEAD、stdout/stderr保存在主仓库私有 `.ergora/checks/training-cycle-execution-consumers/short-r1.{json,stdout,stderr}`，不是共享结果地址。另 core-r3 无SDK解释器实际导入三个本树源码owner成功，`find_spec('temporalio') is None`；compileall 和 `git diff --check` 通过。尚未把这些检查扩称新包、原生链路或完整兼容验收。

静态复核确认旧四 action 仍使用 schema1/原十字段封套，v2 才添加 facts；原 source pin 清单和 native283文件未改，预算worker8未改；H 观察不调用 ensure_owner、collect_and_gate、rounds 或 native execute。真实 S-H、最后gate行为反例、完整facts容量、来源/项目/stop漂移与三事实交错仍待后续有界验证；独立审查、新安装、自身模板及真实服务由主控接续。

后续静态核对补上新普通 H 的 runtime client.namespace 与已认证 service_namespace 比较，并在原 Execution.check 再核真实客户端 namespace；不改变旧人工路径。无S-H父侧窗口接缝 `short-window-r1` **4 passed／0.87秒**（runner总1.44秒）：分别令冷10秒、配置control、配置compute最短，及attempt2强制observe；保留真实SDK环境、converter和实际operation validator，仅替代H结果，不认证真实来源或执行。命令／源码SHA／输出在同私有证据目录。两新S-H用例现在各两个参数，共4场景：完整／丢完成reply，锁内同步跨窗／持久operation来源漂移；均未执行。正常链还准备在双QUEUED且无request时验证attempt2只观察，以及synthetic native成功先于reap时保留runtime QUEUED／launch_consumed，不推accepted。除明确synthetic文件和服务替身外，S/H、预算根、原链发布和收尾使用真实本地实现。

当前7文件源码已在私有 `source-freeze-r1.json`／`candidate-r1.diff` 冻结，diff SHA-256=`e0b0b7150b3c7b121f13fe438f0882ba151a83dfe6ecc6a337da93bc2e32f14f`。之后只有正常S-H测试新增外来job反例，产品尚未变动。主控新的fresh独立审查指出：原runtime.observe只核Binding，`another-job`服务替身可返回同Binding/QUEUED且外来job；当前组装直接标runtime queried，虽请求双QUEUED比较阻止publish，观察事实仍过强。已与reviewer沿原源码／fixture核实可达性，尚无本次运行反例。该问题的最小修正归原H组装：同一已验证native request存在且job冲突时保留完整runtime原观察，将facts.runtime降为unconfirmed并使整体unknown；原SUBMITTING/native尚缺的实测阶段继续保留。产品暂未修，准备在CI释放后先记录原场景修前失败，再最小修正、新冻结并复验，独立报告由reviewer维护。

后续测试runner会在启动前保存准确命令、7文件SHA和基线，退出后再次比对源码，并为每次运行使用独立的私有持久basetemp保留S/H输出／原件。现有 `collect-r1` 只收集4节点（0.84秒），没有执行fixture、S/H或root，不能视为4项行为通过。

## 真实 S-H 定向验证与修正

CI两组结束并完成主控收尾扫描后，开始串行验证。每次命令都明确使用既有package-r3 SDK解释器与本树src，启动前后保存实际源SHA，TMPDIR与pytest basetemp均显式放在主仓库私有证据子目录；保留原输出和各次S/H／budget原件，未启动server或安装新包。

|实际检查|结果及可核范围|
|---|---|
|外来job修前反例 `job-before-r1`|**1 failed／32.97秒**。准确失败是foreign状态observed而非unknown；该场景之前的冷无intent/owner可用facts、早receipt＋SUBMITTING/native缺失、双QUEUED断言均已通过。7文件前后未变。|
|同场景修后 `complete-after-r2`|**1 failed／47.42秒**。原H仅加4行：已验证native request存在且runtime job非null但异于原job时，runtime降unconfirmed、整体unknown，完整runtime/native/execution保留。外来job断言已通过；后续root无launch marker失败，原admission stderr证明SDK启动root尚未装既有服务替身，连接默认7233被拒；未启动server。|
|root替身初次装配 `complete-after-r3`|**1 failed／50.77秒**，产品同r2。原root实际admit并保存launch，但原managed-no-launch故障只认owner，不认root envelope进入时的controller-owner，故未生成预期marker；native helper随后在无SDK解释器import阶段失败，未执行训练。原stderr和原件保持；非产品窗口缺口。|
|共享原fixture后 `complete-after-r4`|**1 passed／46.41秒**。把原cycle_candidate的Popen算法提取成共享cycle_budget_root，原direct与新SDK测试共用，不另造root；原training_budget_client的managed-no-launch只补认controller-owner。正常完整节点通过外来job降格、首轮冷事实、双QUEUED、无request时attempt2只观察、原一次request→原root唯一launch、既有launch只读、native synthetic成功但runtime仍QUEUED且无reap不推接受、partial launch不修复；8文件前后未变。|

r4产品仍是r2修正版本：worker SHA-256=`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`，Execution=`c105ac8d2b248169b46a4c8a5692dbda90c7642e7907e7f19969345de1c7ea90`，protocol=`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`。`source-freeze-r4.json`／`candidate-r4.diff`准确8文件，diff SHA-256=`93978d8adef9b828dc9094f008fc3fade21e1fa44b21384f533c142b9c6ee192`。8文件由原7文件加必要的既有training_budget_client fixture一行变化组成；均在授权源码／测试边界。

余下 `remaining-r4` 正串行执行丢completion reply、锁内同步过窗但compute仍正、锁内原operation来源漂移3节点，结果未定。原root／S/H是真实本地进程，Temporal为原真实SDK codec上的服务替身；这些检查不是新安装或真实Temporal／正式总Workflow验收。独立reviewer正在按实际diff与证据审查，结论由其记录，尚未把本片标为完成。

`remaining-r4` 已结束：**3 passed／101.71秒**（runner102.30秒），8文件运行前后未变；因此r4新S-H共正常1＋余3节点通过。余3实际证明已发布request但S读completion阻塞时父unknown／无facts、后续attempt2只观察原唯一launch；锁内同步读取跨固定窗口后允许H继续一次而compute仍正，无request/launch发布；锁内完整operation活动来源被改时拒发布。`compatibility-r4` 正在串行跑三个直接受改动影响的既有接缝：共享fixture的原direct root交接、schema1完整人工请求唯一launch、旧v1 retry/successor拒绝；结果未定。

补核原schema2显式人工路径时发现语义需主控澄清：原 `test_controller_stop_at_original_execution_boundaries` 已通过public training.execute完整confirm驱动schema2，并核原actor与stop/admit/attempt/ack。当前Execution.request新增“controller且无cycle_operation一律拒绝”会撤销该既有显式路径；r2写的是schema2“新H不能省略来源”，未明确撤销旧schema2人工完整确认。已报主控与独立reviewer，建议仅约束新H始终传完整source，去掉过宽全局guard以保持原显式确认，其current来源/window和原人工完整确认/父history仍核；暂未改产品或以旧测试反裁合同。此项仍开放，不把r4四新场景通过视为全片可完成。

主控与独立reviewer已分别沿原public调用链、控制器合同和r2文字核实：原schema2完整人工确认是既有授权路径，r2没有撤销它；“新H不能省略来源”由新增H的单一调用处无条件传完整cycle_operation实现，无需新增wrapper/第二分派。已移除Execution.request过宽的2行拒绝，current有source时的全部本H／来源／最终window gate不改，原人工确认／父history／owner／stop／唯一launch保持。源码已新冻r5：8文件diff SHA-256=`7c8e07ae1d7062ffdd5151b3fd5e2d81692f2c264119a4371519599e269a85f9`，Execution SHA-256=`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`；worker/protocol仍同r2/r4。

`compatibility-r4` 已结束：**3 passed／57.43秒**，8文件前后未变。当前 `gates-r5` 仅跑4个受纠正影响的节点：原schema2 public request/launch两个stop边界，新H锁内同步过窗/持久来源漂移两个节点；结果未定。r4新4/旧3的准确通过范围保持，不直接改写为r5整体验收。

## r5 实施交接

最终专属树仍基于af176cf，无commit/push；只改8个已列原owner/tests/fixtures，无新产品module、manager、ledger、reader或reaper。`candidate-r5.diff`与`source-freeze-r5.json`为当前完整差异及逐文件SHA；产品3文件身份如上一节，合计diff SHA仍`7c8e07ae1d7062ffdd5151b3fd5e2d81692f2c264119a4371519599e269a85f9`。旧四v1 wire/queue保持；两v2沿原normal槽，stop独立槽保持1/1，budget worker8、source pin清单、native283、kernel v3与全部祖先资源／权限均未改。原公开schema1/schema2完整确认保留；新H实际单一request调用无条件带完整operation，原锁内最后source/window gate保护实际publish前后。

|最终证据快照|结果与范围|
|---|---|
|r4 新消费者 `complete-after-r4`＋`remaining-r4`|**1 passed／46.41秒＋3 passed／101.71秒**，两次8文件前后未变；准确产品范围为r4。|
|r4 原接缝 `compatibility-r4`|**3 passed／57.43秒**：原direct root交接、schema1完整人工唯一launch、旧SDK v1重投／后继拒绝；8文件前后未变。|
|r5 最后gate `gates-r5`|**4 passed／91.25秒**：原schema2完整人工request/launch stop边界，以及新H同步过窗／来源漂移；8文件前后未变。|
|r5 短检查 `short-final-r5`|**10 passed／1.04秒**：未信任v2输入、冷/control/compute窗口与attempt2只观察、32KiB含metadata、原SDK生命周期；8文件前后未变。|
|r5 旧source/ref `v1-source-r5`|**1 passed／23.89秒**：真实SDK首次receipt恢复、完整history/memo/run/namespace/type/queue变异拒绝、原stdout ref字节／SHA与converter往返；8文件前后未变。|
|r5 core导入 `core-import-r5.json`|既有core-r3无SDK解释器实际从本树src导入worker/execution/protocol，SDK确实不可见；0.43秒，无新安装。|
|静态与收尾|compileall、diff-check、交付3相对链接存在；最终`cleanup-r5.json`仅对本片持久证据中的已记录身份作只读扫描，2137个JSON文档、45个身份，live_match=0／unknown=0。两个测试故意写成`{`的partial launch解析skip分别保留，未删除／修复，未冒称全系统进程扫描。|

全部命令、精确源码、stdout/stderr和实际S/H／预算根原件留在主仓库ignored `.ergora/checks/training-cycle-execution-consumers/`，不是公开共享地址；各次独立TMPDIR/basetemp未交给系统临时目录回收。修前job事实失败及两次fixture适配失败保留原始范围，没有转写为成功。原3产品未因fixture失败放松任何gate。

主控与reviewer已确认的两个源码问题均已按最小位置处理：外来job投影过强在原H native核定后降格，并由修前失败／修后完整节点证明；过宽schema2无source拒绝已移除，原schema2实际request/launch两个stop节点通过。独立reviewer仍拥有最终finding关闭与源码结论，本报告不代其approve。

明确未验／后继：本片没有构建安装新wheel、启真实Temporal/7233、跑正式总Workflow/sandbox/history-replay、接受测量或后继ordinal、训练/GPU质量、自身模型审查或全suite；以上由主控按原分片接续。native成功早于reap使用synthetic结果文件验证三事实不相互推断，不能称真实执行成功；reap先于Workflow phase的真实链路未在本片单独实测。当前新gate/来源及既有stop边界有定向证据，项目修订漂移和完整新增facts超容量的真实服务反例不额外冒称已验。

CI整合只记录主控实际863源码事实：cycle_sdk_activity及旧SDK tests仍在submission，新两SDK tests继续留submission，无需迁移或互导；机械迁移的controller/candidate-root模块须显式导入共享cycle_budget_root。合入时对真实完整diff核fixture闭包，实际collect及一个原direct-root节点确认后再冻结测试输入；当前r5或先前181输入不能充当该迁移已验。该适配由主控接续，本树未中途合主树／CI树，未修改对方工作树或主PLAN。

已实际读回[独立产品源码审查r5复核](2026-11-16-training-cycle-execution-product-review.md)：reviewer核当前完整diff／8源身份和原gate/short/core证据，R1、R2均关闭，**源码＋已核定向门槛需求／维护性两轴approve，开放0／0**。其结论明确不覆盖新包、现场、自身模板或完整c1b2b交付；本片交接状态据此更新，不将源码门槛扩大。最终v1-source与cleanup原件已交主控／reviewer，可由其按实际原件接续。


## 新授权：提交、CI整合与新包定向验收

主控后续明确授权提交8个r5文件、仅本地合入CI提交`7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`，并仅补controller模块显式导入原`cycle_budget_root`。r5提交为`585e3dabefdde93ac826dec0aa45aa5cb27f420e`；无冲突merge提交为`bcc304894622040a7d844f8c6f9ddfded65aa895`，双亲准确为上述两项。未合入主树8635692、未push，源码树clean。相对CI提交的controller diff只有这一行import；SDK fixture及新旧SDK tests实际仍在submission，无迁移或循环互导。CI自带controller尾部空行导致merge staged diff-check报告`new blank line at EOF`，保留其原字节，未冒称该项检查通过。

新的私有持久证据目录为主仓库`.ergora/checks/training-cycle-execution-consumers/installed-ci-r1/`。`freeze.json`固定HEAD、父提交、183项实际输入（117 tests＋62 examples＋4 CI/config）、全部663产品项的字节／SHA／执行位，以及462份冻结运行文件（183输入＋279 native platform测试数据）。freeze SHA-256=`8b85a24344e9571d22d442c1d96bde8b3119f68c72b46e08a6190660d15d2ba5`；相对af176cf完整diff SHA-256=`7201deb20067777534deade5e85e2ee6a83e0f9df6acff05882121144eb6888a`，相对r5提交的merge diff SHA-256=`dd4e3af9922a775125428de5643ef7eeb90f35f8bffd08d4b2e248592eef98b8`，对应diff原件均保存。初次freeze脚本错误地排除了native模板自身AGENTS，导致662计数assert失败；纠正为仅排除顶层owner指令后再冻结，产品未变，后续663比较才通过。

新wheel由主控包片构建，路径为同私有根下`package-r1/dist-r1/ergora-0.2.0-py3-none-any.whl`，SHA-256=`55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`。本片逐项实际重读当前663源码、wheel成员及core/SDK两个非editable site文件，字节与执行位全部相等，三个owner仍为r5身份。本次没有复用旧181输入的HEAD校验，也未把旧r3源码测试改称安装结果。

实际collect使用该新SDK解释器`-I -B`，清除PYTHONPATH，在新冻结cwd执行；只显式加载冻结CI plugin及native reference导入路径，无应用源码路径。`collect-result.json`记录**exit0／8.61秒**，`collection-closure.json`记录**2236唯一节点／86文件**，精确覆盖原六组，组节点数依次349／285／399／415／315／473，配置文件不缺、不重、无未归组节点。实际fixture闭包中，迁移后的controller direct-root、schema2 request-stop，以及留在submission的新SDK正常／两个最后gate节点均解析到原共享`cycle_budget_root`。`collect-imports.json`记录真实新SDK site路径、三个owner实际SHA、isolated=1及dont_write_bytecode=true；源码与冻结输入运行前后不变。collect不执行fixture或行为。

按授权在同一新非editable SDK环境串行执行五个过程节点（controller direct-root、新SDK完整正常、最后同步window/source两参数、原schema2 request-stop）及十个短SDK节点，**15 passed／186.77秒**，完整runner187.70秒／exit0。实际命令为新SDK解释器`-I -B -m pytest`，无PYTHONPATH，准确选择、环境、持久TMPDIR/basetemp和前后输入身份在`selected-command.json`／`selected-result.json`，stdout/stderr与JUnit均保留。没有失败重跑或改产品；source／frozen运行前后不变。真实Temporal／7233、全suite、自身模板与最终片审仍由主控负责，本次未启动server。


主控再授权增加一次真实SDK-free plain inspect。本次实际选上述已stop收尾的`test_cycle_sdk_execution_last_0`完整controller/cycle，以新`package-r1/venv-r1-core/bin/python -I -B`、无PYTHONPATH，在冻结cwd调用原`_CycleOperation(mode='inspect')`；`find_spec('temporalio') is None`。实际S/H操作**0.821秒**、完整subprocess**1.569秒／exit0**，返回inspected／submitted／runtime not_queried，S rc0；完整H stdout ref为2784B，实际字节与SHA核对。实际supervisor完整身份及两帧、原H stdout引用在`core-inspect/result.json`。父异步loop期间禁止State／SQLite／业务reader，未生成candidate request、owner或重授原业务窗口。

`core-inspect/{before,after}.json`逐文件记录原cycle目录9份实际文件和106份业务常规文件的字节摘要，并核数据库原始bytes及SQL dump、原authorization clock完全相同。9份包含原admission lock和测试fixture的`parent-history-observed`标记，不扩大为九种独立产品原件类型。inspect自身的临时冷观察bootstrap仅属于本次观察envelope，不替换原业务clock或工作窗口。其新观察目录只产生5份文件（request、H stdin/stdout/stderr、supervisor stderr），在result另列，没有混入原件不变数量。

`site-during-selected.json`与最终`site-after-selected.json`实际重读663项source／wheel／core／SDK字节及执行位一致；实际隔离core／SDK import均来自各自site，core无SDK、SDK可用。`final.json`重新核183源码输入＋663产品及462冻结输入SHA／执行位，全部不变，HEAD仍bcc3048／clean。最终`cleanup.json`范围明确为本次持久basetemp／TMPDIR／core-inspect中的记录身份，只读扫描689份JSON、16个完整身份，**live_match=0／unknown=0**；正常SDK节点故意留下的单个`launch.json`内容`{`解析skip独立记录，未修复或删证据。早先只扫selected的683／15快照另存`cleanup-selected-only.json`，未覆盖成全系统扫描结论。

当前可导入提交为r5实现585e3da及其CI merge bcc3048；推荐主控固定该产品身份／55029新wheel接续最小真实现场和完整c1b2b终审，再按主计划导入。主控已告知新SDK包自身原结构模板真实Codex supplied-source review approve（run `7e08910035274c158594bfb92bfc551a`）；其证据由主控负责，本报告不把该来源审查替代现场或运行验收。当前源码、CI实际fixture闭包、新包15项与core plain inspect已交回，没有剩余本片授权定向检查；现场、完整片终审、实际CI和发布状态仍分别待主控闭合。
