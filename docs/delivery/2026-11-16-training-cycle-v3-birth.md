# c1d M1b：新版本授权出生与兼容交付

日期：2026-11-16。状态：具体[计划](../plans/2026-11-16-training-cycle-v3-birth.md)的 storage-only 范围已接纳，[fresh 设计审查](2026-11-16-training-cycle-v3-birth-design-review.md)修订后需求／维护性两轴 approve、开放0；源码已冻结，24控制器＋12兼容与三份旧v1真实历史回放通过。[fresh 源码审查](2026-11-16-training-cycle-v3-birth-source-review.md)两轴approve、源码阻断0。安装24控制器＋14兼容通过，含E1所缺旧owner1／2实际接缝；自身原结构模板Codex approve。原848＋663冻结输入未变，fresh同片终核两轴approve／0、E1闭合；产品67ab9b4已普通导入23ad171，发布／自己的CI接续。

实施基线为 M1a 后 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`，持久隔离分支 `feat/training-cycle-v3-birth`。仅允许内部显式新出生 schema3、原件读取和本地 controller intent，缺省 schema2 及旧ID不变；新版本的 live／manual／native 执行全部明确关闭。native 拒绝须沿真实 executor admission callback 验证，不把外层 schema2 permission 分支说成 schema3 已执行。

来源四项、原clock／ID／完整字节恢复、边界关闭、旧历史和最小测试接缝见计划。后续源码、测试、安装、自身模板、fresh 实施审查和发布分别记录，不由设计审查代记成功。没有 V2 Workflow／activities／collect／measurement acceptance 或 ordinal1。

## 隔离实现与源码验证 r1

2026-11-16。本节更新当前状态：**storage-only 源码／定向检查已完成，fresh 实施审查、安装与后续验收待主控进行，尚未认证整片完成。** 实施留在原隔离分支 `feat/training-cycle-v3-birth`，基线 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`；未改主树产品。按已审具体计划与 component protocol，复用原 writer／锁／clock／link/fsync，不新增产品或测试模块、CI 分组、公开 CLI、权限或服务。

`authorize_controller` 仅新增内部关键字 `program_version=1`；精确 int1 保持 schema2，精确 int2 创建 schema3，bool 等非整数拒绝；手工 schema1 不变。原 ID 的版本／模式不得双向替换。schema3 使用独立 v2 protocol／queue／ID prefix，controller intent 仍由原 `CycleAdmission.intent_record` 生成原 schema1 与严格六字段 workflow input。四项 package-root 原字节 SHA 在出生冻结；历史读取只核原 map 固定键／digest 形状及完整授权 SHA，不比较当前模块。新 intent 准备与原 intent 恢复比较当前四项 SHA，仍消费原预算与 stop；ready 重试不再捕获来源、clock 或 admission。

schema3 仍只授本地出生、读、锁、stop 和 intent。`_controller_ready` 在直接 claim 写 attempt 前拒绝；真实 cold S/H 在装载／核完整授权后、SDK／activity／各 mode 动作前拒绝；`BudgetedStart.source` 在 manual/controller 分派前拒绝；native `admit → validate_context` 在 executor `started`／managed attempt／ack／runner 前拒绝。native 外层 schema2 专用 permission 分支保持原样，schema3 不运行该分支。已有 native result 的早期读取保持。runtime／worker 共用一个封闭 protocol→Workflow type 映射，v2 仅可做只读身份认证；没有 V2 类、注册、活动、队列启动、collect、前驱接受 gate 或 successor。原 `successor_not_enabled` 保持。

### 冻结字节与证据定位

最终九文件 patch raw SHA256 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`；完整 tracked source／tests manifest SHA256 `0a8715f7643e4104c1c404204923919c05b2af51b681d423e560a2a241bc782c`。冻结后重算全部 manifest 文件无漂移。五产品 owner raw SHA256：

|文件|SHA256|
|---|---|
|`training_cycles.py`|`0a96a1c14ede76510e7480299e0958d36296ba0e5895a63743e311d1a03ff110`|
|`training_execution_protocol.py`|`fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`|
|`reference_training_budget.py`|`1fde5981eb63aa50dcaaae427144528ff27d2ff4bba3345bc13fe1059a441cb4`|
|`reference_training_worker.py`|`645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`|
|`reference_training_runtime.py`|`1d1d3a3f27c84529e3e4f4a509e4df60b52f459013f95edc4473750182fdff86`|

另外只改现有 `test_training_cycle_controller.py`、`test_training_submission.py` 与原 `training_controller_service.py`、`training_executor_client.py` fixture；各准确 raw SHA 在同一冻结 manifest。`reference_training_submission.py` 沿现有预算调用，无修改。私有原件位于项目 ignored `.ergora/checks/cycle-v3-birth/source-r1/`：`frozen.patch`／`frozen-source-manifest.json`／`frozen/`、各次完整 argv/env/解释器身份、stdout/stderr 日志、JUnit、retained replay 结果及其完整 history SHA。公开报告不包含运行数据或机器路径。

### 实际检查

源码以 Python3.11.15／SDK1.34.0 开发环境执行，显式选隔离树 `src` 并禁 bytecode；没有安装或真实服务。最终冻结字节：

|检查|实际结果／范围|
|---|---|
|`controller-r4`|**24 passed，112.54秒**。新旧出生／模式与完整原件保留，schema2/3 的授权文件、父锁、ready 目录同步故障，永久不完整 ID／原 source 与 clock 恢复，schema3 来源漂移与 map 篡改、intent 幂等、stop／预算、直接 claim、真实 cold S/H、两种 manual 入口拒绝；真实 SDK codec 的 v1/v2 只读 type 身份以及 v2 对错 v1 type 拒绝；原单 attempt／unknown 对账回归。|
|`compatibility-r4`|**12 passed，46.64秒**。schema1 CLI 丢回复、完整原 cycle/auth/ready/native intent/attempt/receipt 在读／重试后逐字保持，原 owner 历史读取及缺 installation 接缝、原 ordinal1 SDK 拒绝、native 锁／manual／已有 result 语义，以及原取消／eviction 的 bounded child Replayer。|
|静态保留|`git diff --check` 无诊断；对基线核 AST，原 `create_cycle_workflow` 整体不变；原 `GATE_SOURCES` tuple 的25项精确不变。没有把 unrelated owner schema 扩为3。|

实际 native 拒绝测试重用原 historical execution 链与 executor fixture：只重绑完整原 intent／owner／request／launch 身份，删去 fixture 原 attempt/ack/stopped，经所选 native venv 的真实 `native_main → process → admit → validate_context` 拒绝，核原件不变且无新 started／attempt／ack／runner 效果，再核已有 result 的早期读取。子进程通过 `PYTHONPATH` 使用开发环境已有依赖，**这不是整条 callback SDK-free 的证明**；原 stdlib-only 协议／历史 reader 接缝的证明保持独立，未安装依赖或调用服务。

另以 `-I -S -B` 有界子进程读取合成的原 schema1／schema2 owner 历史（均无 execution request，schema2 capability 为 null）：真实 `ExecutionRecords.load/observe` 返回 `not_requested`／`execution_authorized=false`，两份 raw 均保持，且 `yaml/jsonschema/temporalio/ergora.state` 未导入，0.08秒通过。该窄范围 SDK-free 检查原件为 `legacy-owner-sdk-free.json`；完整有 request 的 owner2 历史仍由上述原 fixture 另验，不将空链说成可执行历史。

保留的前置 fixture 失败：`birth-r1` **11 passed／1 failed，24.15秒**，失败为在父解释器构造 native chain 时缺 native 模块；`native-sdk-r2` **2 passed／1 failed，6.92秒**，失败为无依赖新 venv 缺 SDK。改为真实 native 子进程并提供现有开发依赖后，`native-r3` **2 passed，7.18秒**；最终 r4 在冻结字节重验其相关边界。旧日志／JUnit 和 argv 保留，未覆盖或当作通过。前置测试／fixture 字节在开发中调整，最终 manifest 只认证冻结后的两组检查；五产品字节从这些前置运行到最终冻结保持同一。

### 原 c1c 历史重放

从原 c1c 交付定位原件，未重新生成 history。冻结后用原 `create_cycle_workflow()`／正式 v1 类、SDK 默认 sandbox，在各自20秒有界 child 中实际重放并完成 eviction：

|原历史|原件身份|本次结果|
|---|---|---|
|`cw-live-r1/first-positive-r5/history.json`|82,086B／78 events；SHA `dc7d9587823941f0f7a99d0a6f2c6a366d58ddbd7d50f695f48cc7c87fbd47c8`|通过，1.49秒；父 COMPLETED 成功首轮。|
|`cw1/fault-harness-r5/runs/w5-cancel-r5/results/history.json`|44,640B／45 events；SHA `3a5d086c0ba68f544903fc6ca6e689774f6671fdd8c41ea3fdccb0ec143b2b90`|通过，1.39秒；父 CANCELED，原独立 stop／取消链。|
|`cw1/fault-harness-r5/runs/w8-stop-failure-r5/results/history.json`|48,561B／46 events；SHA `1e9310ceaf8269d8d103a773b991223243cd0285b548c83f1feef2ac8b1f1336`|通过，1.40秒；原 stop activity 失败桥接路径，父实际 COMPLETED，不误记为 Workflow FAILED。|

本次只认证旧 v1 history 的兼容重放；不是 V2 执行或回放，不覆盖历史未运行的变体。

### 待验与交接

准确九文件已冻结供主控 fresh 实施审查／自身模板及后续 packaging 使用；本代理未 commit／merge／push。尚未做新非editable 安装、真实 Temporal／native training／GPU／两轮测量、measurement acceptance、ROOT/source 最后执行 gate、collect 或 successor。M1c／M2／M3／M5／M6 与 M7/M8 的责任及原 ordinal0 限制均保持；源码测试通过不替代这些后继验收或独立审查。

## 新非editable 包与安装验证在途

主控在冻结九文件上构建wheel，SHA256 `1ed714c885686d134033ac610ac0367fe275288d2ce45b8e6c4f1058dc801292`。新core／SDK两环境各663个完整产品文件，源码／wheel／site-packages原字节和执行位逐项同一；原283参考和各自依赖检查通过，core无Temporal SDK，SDK为1.34.0。冻结848源码／测试／示例／配置／CI输入及663完整产品文件，实际包检查原件位于本片ignored `package-r1`。

安装行为以Python3.12的真实site-packages、`-I -B`、无`PYTHONPATH`、冻结测试副本执行。沿源码24控制器及12兼容原选择，并仅为源码review E1额外选择已有`test_cycle_managed_create_requires_its_live_owner_and_preserves_single_start_slot`两参数用例。结果尚在途；不将包身份检查当作行为通过，也不将合成空历史当成完整旧owner1／2接缝证明。自身原结构模板、fresh同片终核及提交尚未完成。

### 安装与自身模板实际结果

上述两组已经结束，原完整argv／cwd／退出码／stdout／stderr／JUnit均保留：

|安装检查|实际结果与范围|
|---|---|
|`installed-controller-r1`|**24 passed，61 deselected，142.11秒**；driver143.50秒。与源码控制器选择相同，使用新SDK包。|
|`installed-compatibility-r1`|**14 passed，115.12秒**；driver116.57秒。原12项加已有legacy owner1／2的完整native create／唯一start slot／不可越权execute／重试与原件保持，用于补E1；这是实际服务替身与native接缝，不认证真实Temporal部署或训练。|
|安装core隔离reader|真实core `site-packages`，`-I -S -B`、10秒有界child，0.106秒通过。合成原owner1／2空execution链分别`not_requested`／`execution_authorized=false`，raw不变，未导入State／SDK／YAML／jsonschema。只证明该reader范围，不冒充完整callback无SDK或完整legacy execution历史。|
|冻结终核|实际补验和模型审查后，848源码／测试／示例／配置／CI输入及663完整产品文件的原字节和执行位均不变，九文件diff仍为`a15d116c…`；并非另一轮重跑的结果。|

Ergora自身原`refactoring-quality → ergora-structure-review@1.0.0`模板经新安装SDK包与用户授权的Codex回退实际运行，**45.671秒approve**。实际输入含17份完整文件613,678B、两份原完整baseline正文、完整九文件diff及3份全部祖先资源，完整stdin778,400B；SHA256 `9f474fb37880fb0475e3cddac405b4b0c968c4a49cfa2439b8633a1e6df92ed5`。原结果SHA256 `e7210aaf8dd8e87364660b15b59fffa7f05dd92f4792c69572b84e3f3a7a973e`；已核task／资源全部进入实际stdin，未截断。输入／原回复／结果和完整scope另存本片ignored `self-review-r1-codex`。

该模型只审所供完整文本，没有workspace访问、独立运行检查或包验收；未声称本次Claude成功或异后端多样性。其结论为未发现可达结构缺陷，五owner职责、封闭type映射、schema3执行拒绝与已有result读保持。新增结果只改变验收状态，不改当时模型输入，也不对状态更新重复调用模型。fresh独立reviewer仍须按原件补核E1、安装、模板和固定产品提交；准确发布／自己的CI另验。M1c及后继执行门保持关闭。

## 固定提交、终核与普通导入

同一fresh reviewer已追加安装／模板／固定提交终核，需求与维护性均approve、开放0／0，E1闭合；[原报告](2026-11-16-training-cycle-v3-birth-source-review.md)SHA256 `cfcaa636510ca20f64a5551769b6b08fa165fcca705f4846e4af7210fe6adfdc`。其独立核到实际legacy[1]/[2] JUnit、179份冻结测试副本、wheel/core/SDK的663完整产品bytes／mode、283参考、848＋663原输入及自身模板原stdin／结果／State，范围与上文一致。

准确产品提交`67ab9b4e446527fd27a61eff1aa6acb8d24feb01`，父为`bd479050ddd2d9c6b6964f89fe44cfc895273d6b`；clean、仅九个既有文件352+/34-，Git提交diff与原冻结patch逐字同一。已普通合并开发分支，合并提交`23ad171bf8228bf80b070d6ad866f79d63986d56`；主控再逐项核合并树848＋663原SHA／执行位同一。没有强推或自动合main。

**本M1b实现／源码／安装／自身模板／fresh终核闭合，公开发布及自己的CI另验。** 后继[M1c-T](2026-11-16-training-cycle-capacity-transport.md)只验证原transport，不改变上述产品。schema3 live／native／V2／collect／measurement acceptance／ordinal1与训练质量仍未开放，不由本片storage-only验收代替。

公开文档候选`833966d4ba21fa7bcb6670e9908d05f058cf8fdd`现已普通推送`refactor/architecture-foundations`；精确`git ls-remote`同一，原push／remote请求、退出码与完整输出留在本片ignored `publication-r1`。自己的官方push／attempt1 [43773202173](https://github.com/626619403/Ergora/actions/runs/43773202173)由HTTP200核准确head，目前in_progress，**不预记最终成功**。该候选同时发布M1c-T已审验证及M2／M3已审设计、留存方案待复核快照，未包含在途M2／M3源码；不因前候选43769505506成功替本候选认证。

公开候选833966d自己的43773202173随后已终态completed／failure：plan及六Linux全success，Windows恰为新controller测试的五个fixture setup错误。原annotations与安装各步骤范围见[独立最小修正交付](2026-11-16-windows-schema3-fixture-skip.md)；修正已四行固定导入，准确后继自己的Windows CI仍须另验，原failure不改写。
