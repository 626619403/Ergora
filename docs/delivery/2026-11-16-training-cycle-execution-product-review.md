# c1b2b 执行消费者独立产品审查

日期：2026-11-16。Reviewer：`/root/cycle_execution_product_review`，fresh context；未接收实施对话。先阅读原要求、实际差异与真实调用者，再阅读作者[交付记录](2026-11-16-training-cycle-execution-consumers.md)。本报告是本 reviewer 唯一写入；未编辑产品／测试，未运行测试、安装、网络调用、服务或提交。

**最终同片结论：固定 bcc 候选的源码、CI fixture闭包、新非editable包、SDK-free真实plain inspect、自身模板及 E7 真实 Temporal／独立预算根现场均已独立复核；需求轴 approve／开放0，维护性轴 approve／开放0，R1、R2保持关闭。完整 c1b2b 可以关闭，固定候选可导入主树；导入须保留主树已另审的 Windows 双mark修正。** 本结论不认证正式CI运行／发布、c1c／E8正式Workflow、接受测量、训练质量或后继ordinal。各轮准确身份、历史失败与结论边界保留如下。

## 结论与范围

初轮**需求轴 request-changes，开放 1；维护性轴 approve，开放 0**。初轮结论只覆盖下述未提交源码的静态审查；后续复核见文末。尚不能认证新非 editable 包、SDK-free 新包、自身模板或真实 Temporal 验收，也不认证正式总 Workflow、接受测量、后继候选或整个自动循环。

源码树为 `.ergora/worktrees/training-cycle-execution`，分支 `feat/training-cycle-execution`；HEAD／差异基线均为 `af176cf6e79adb9c6ef6f32946672bc77cdb89de`。实际 `git status --short` 仅以下七个 tracked 修改，无 untracked 产品文件；`git diff --stat` 为 529 insertions／10 deletions。审查时身份如下，后续修改需重新核对：

|文件|SHA256|
|---|---|
|`src/ergora/reference_training_execution.py`|`c105ac8d2b248169b46a4c8a5692dbda90c7642e7907e7f19969345de1c7ea90`|
|`src/ergora/reference_training_worker.py`|`3b072bde0888cccfbc0951512955dc79b7745ad697c6302882efaac41f5e78cb`|
|`src/ergora/training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`tests/fixtures/training_cycle_operations.py`|`03edbad39b2108fc09afbf5003124c5d109896cbdf46176843a3b60e9bfcb844`|
|`tests/fixtures/training_submission_client.py`|`4c5d5d97f3dc785e12b201ffa02182a938789fc80ae3d5b40594bb5286039b60`|
|`tests/test_training_runtime.py`|`c8b6a25892dabc5f658853254cfad098ed60f491013dee4252bc988d92c24bba`|
|`tests/test_training_submission.py`|`ebd3a9c61cc80455b20c53bd40258d61463942561b3390a27856e743fe179805`|

依据为根／src／tests `AGENTS.md`、主 `docs/PLAN.md`、组件变更协议的执行／证据及检查部分，[r2具体合同](../plans/2026-11-16-training-cycle-execution-consumer.md)、[runtime消费者顺序](../plans/2026-11-16-training-cycle-runtime-consumers.md)、[原控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[c1总计划](../plans/2026-11-15-training-cycle-workflow.md)；另读 `maintainable-project-delivery` 及其 independent-review、`ergora-codebase-quality` 及 repository-style／module-design／test-seams 三引用。

## Finding

**R1／P2：runtime 的外来 job 身份被投影为已确认事实。** 位置：产品专属树 `src/ergora/reference_training_worker.py:679`（读取和投影至 684 行）；邻接原 owner `reference_training_runtime.observe:126` 仅校验 `Status.binding`／`Outcome.binding`，并不校验 job ID。新 H 随即把返回标为 `facts.runtime.state=queried`，没有将 `status/outcome.job_id` 与原 job 核对。

可达场景：已有完整 submitted receipt 和正确 native request，原 run 的 query 返回原 Binding、`phase=QUEUED`，但 `job_id=another-job`。现有 `tests/fixtures/training_submission_client.py:164` 的 `another-job` 场景直接提供此响应。调用 `observe-candidate.v2` 时当前返回整体 observed、runtime queried＋外来 job；native 可同时是原 job QUEUED。新 request 的 718 行比较仍阻止发布，因此这里没有发现重复执行／launch 绕过；问题是原合同要求的身份冲突被伪装成已确认运行事实，后继消费者无法只凭 queried 判定认证是否完成。r2“运行观察的组合与恢复表”明确规定子 job mismatch 应为对应项 unconfirmed，并要求完整 Binding／job 核对。

最小修正：在当前 H 的运行事实组装边界，用原固定 job 身份校验返回 status/outcome 的 job；冲突时保留完整 `result.runtime` 原观察及错误，令 runtime unconfirmed、整体 unknown；保持 native／execution 独立事实及原记录。无需新 reader、helper 模块或在公共 runtime 中扩大本片范围。原 native request 尚未发布的正常 SUBMITTING 等待不应因此被改成伪造 QUEUED。验证应复用 existing another-job 服务接缝，保存修前与修后结果，并确认 request／launch 未新增。

## 静态核对与证据边界

已沿 SDK 工厂→cold S–H→普通 H→原 `Execution.request/check/current`→原 root `admit`／native gate／唯一 reaper 阅读。新 mode 同入 CANDIDATE 与 WORK；request／observe 的 action、ordinal0、attempt1约束在原 protocol；新 request 携完整本 H operation，在原锁内 publish 前后，经同步来源读取之后检查同一 window。原 root 不携该短 H payload，原 admit 和 launch 所有权保持。观察无 ensure_owner／执行／collect／rounds／后继许可。新 H 内聚在原 worker，单调用 source helper 位于 protocol，隐藏完整来源不变量，有实际归属理由；未发现需要拆新文件或增加抽象的维护性问题。

冷无 intent／owner 路径能由原 `_cycle_target`、`status(None)`、空 `ExecutionRecords` 形成 not_recorded／not_requested；native request 缺失不会合成 QUEUED。现有／损坏 request 或部分 launch 阻止新 request，异常保留 unknown。runtime、native、durable stopped 各自读取，不从 native SUCCEEDED 或 reap 推导接受或 Temporal 完成。SDK converter 仍对完整封套计 metadata 后整体拒绝；旧四活动沿原 schema1封套，新两活动才使用 v2／facts；normal五项＋独立stop一项且各槽1，原budget8未改。这些均为静态观察，真实竞态／容量与进程行为仍需对应验收。

只读检查过作者保存的 `short-r1`、`short-window-r1` 命令 JSON 与 stdout：分别记录 6 passed／1.02秒和4 passed／0.87秒，使用前置 package-r3 SDK解释器＋本树 PYTHONPATH；不是新包或真实 Temporal。其冻结 worker／execution／S–H fixture／submission test 的 SHA 与本报告初查身份不同，故保留为早先源码检查，不能覆盖本报告全部当前差异。作者记录的 core无SDK导入、compile、diff检查本轮未重跑。四个新增真实 S–H 场景当时均未执行；主控后续将给出实际结果与固定输入身份，再在本报告补充复核。

初轮阻断为 R1；关闭后仍须分别取得当前源码真实 S–H 及受影响兼容证据、新包／SDK-free、自身模板、真实 Temporal 的准确身份和原件。通过本源码片不意味着 c1c／c1d 或整个自动循环交付完成。

## r4 复核：R1关闭，公开 schema2 兼容义务仍开放

本轮仍只读源码／原件，未运行测试。**需求轴 request-changes，开放 R2 一项；维护性轴 approve，开放 0**。作者对 R1 的最小修正和真实证据已核：原 H 在取得同一完整 native request 后，比较已查询 runtime 的非空 job ID；冲突时将 runtime 降为 unconfirmed、整体 unknown，完整 `result.runtime` 和 native／execution 事实保留。没有扩大公共 runtime 或新建 reader。R1 关闭。

已核 `job-before-r1` 的命令 JSON、源码前后身份与原 stdout：**1 failed／32.97秒**，失败准确落在外来job应为 unknown 的断言，产品 worker 为初轮 `3b072bde…`。修后 `complete-after-r4` 为 **1 passed／46.41秒**，`remaining-r4` 为 **3 passed／101.71秒**，两次各八文件运行前后 SHA 同一。r4 worker 为 `d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`；execution／protocol 仍为初轮表内身份。额外原 fixture `training_budget_client.py` SHA 为 `3b1e5def93899890bdf62fa2eddfc55eca010f64684ada79756a167f7f1386e6`；submission test 为 `db916b9d88262446bcdf7bde6e77e9538e235fae21400bc60b1e3779a532d807`；其余五文件 SHA 同初轮表。准确 r4 diff SHA 为 `93978d8adef9b828dc9094f008fc3fade21e1fa44b21384f533c142b9c6ee192`。

已读 r4 八文件实际差异。原 `cycle_candidate` 的预算进程 Popen 替身提取为 `cycle_budget_root`，由原 direct 与新增 SDK 测试共用；原 `managed-no-launch` fixture 补认真实 root envelope 的 `controller-owner`，归属明确。四个新 S–H 场景保留真实本地监管／root／链发布；Temporal 仍是原 SDK codec 上的服务替身。它们证明正常／丢completion、部分slot、一次launch、结果先于reap和同一同步最后window／source gate的实际局部行为；不变成真实server或整个兼容面认证。`complete-after-r2/r3` 的失败仍保留为作者记录的替身装配问题，不改写成产品通过。

**R2／P2：新 guard 撤销原 schema2 公开显式确认。** 位置：专属树 `src/ergora/reference_training_execution.py:76` 的 controller 且无 cycle_operation 全局拒绝（相邻两行）。原 `training.execute:121` 接受完整 revision／intent／固定 run／native raw SHA／confirm，经 `reference.training_execution:464`、`worker.execution_main:1509` 调到同一 `Execution.request`，该公开路径没有 cycle_operation。`tests/test_training_submission.py:1750` 附近原 `test_controller_stop_at_original_execution_boundaries_preserves_consumed_records` 的 request／launch／executor-lock／attempt／ack 五种场景，明确对带完整 controller binding 的 schema2 使用此公开入口，同时核原 actor／stop／admit／已消费记录。新 guard 在任何这些原 gate 之前拒绝，静态可确定旧路径无法到达；本轮未执行旧测试，不能声称已运行复现。

这不是凭旧测试反裁新合同：原控制器合同第51／55行明确复用原 `training.execute`／`Execution.request`；r2第6项要求的是 schema2“新H不能省略该来源”，第156行仍明确“人工确认及原admit语义保持”。没有将全部 schema2 公开显式确认删除的授权。初轮未追到这一既有调用者，本轮将其补记为需求回退。

最小修正为删除该过宽全局 guard，保持现有新 H 唯一 request 调用点始终设置完整 `cycle_operation=payload`；`Execution.current` 发现 source 时继续严格校验完整本 H source／父stop／同步后的同一window，publish前后都保留。原公开调用仍核完整确认、owner、父history、原compute／source／stop及唯一launch，不获得新H调度能力。没有必要为此另加 wrapper、标记或第二入口。已将此判断直接发送实施者和主控；作者尚待执行该修正与受影响兼容检查，本报告不预定修后结果。

## r5 复核：R2关闭，源码与定向门槛通过

本轮仍由同一独立 reviewer 只读复核，无测试／安装／服务执行。已核实际源码、`source-freeze-r5.json` 与完整 `candidate-r5.diff`：HEAD仍为af176cf；八个文件准确身份同r4，仅 `reference_training_execution.py` 变为 `f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`，完整diff的实际 SHA256为 `7c8e07ae1d7062ffdd5151b3fd5e2d81692f2c264119a4371519599e269a85f9`。worker仍`d42d090b…`、protocol仍`b8f8c829…`，测试／fixture仍为r4上列身份，无额外产品变更。

r5只删除R2所指的两行全局guard。原公开调用可重新进入已有完整确认及全部原gate；新H唯一调用处仍无条件设置 `cycle_operation=payload`，删除条件在该非空source路径本来不会触发，因而不改变新H的发布逻辑。`Execution.current`中的完整source、父stop及同步后的同一window校验原样保留，仍在原锁内publish前后调用，没有新增wrapper／分派或扩大执行许可。**R2关闭；在已审源码和下述定向证据范围内，需求轴approve／0，维护性轴approve／0。**

已核原JSON、stdout与运行前后八文件身份：

|证据|准确结果与限制|
|---|---|
|`gates-r5`|**4 passed／91.25秒**，runner91.84秒；原schema2公开显式确认的request／launch两个stop边界，以及新H锁内同步跨窗／来源漂移两个节点。八文件前后未变，证明此次兼容纠正和新H最后gate保持；未运行原五边界的其余三个节点。|
|`short-final-r5`|**10 passed／1.04秒**，runner1.61秒；实际SDK来源拒绝、一次window参数、完整converter容量及原SDK服务生命周期接缝；八文件前后未变。H结果在window参数测试被替代，不能据此认证真实S–H或server。|
|`core-import-r5`|原有core-r3依赖解释器实际导入三个当前源码owner，输出各自本树src路径且`find_spec('temporalio') is None`；不是本片新非editable包验证。|
|`compatibility-r4`|**3 passed／57.43秒**，runner58.03秒；r4八文件前后未变，准确覆盖direct原root交接、schema1完整人工确认的一次launch及旧v1重投／后继拒绝。保留为r4运行，不改写为r5重跑。|

r4四个新S–H的历史通过与原范围保持；r5只删除不作用于带source新H的guard，以上静态核对及r5两项新H gate实测支持该局部保持，不把旧四项伪称为r5完整重跑。R1修前失败、r2/r3替身失败和早先short身份限制均保持。

本轮只关闭R2的源码／定向门槛。新非editable core／SDK包正在其他授权工作流构建，本报告未核完包、冻结全输入、安装回归、自身模板或真实Temporal／独立预算根现场；旧v1首次source/ref补验与最终清理亦等待最终原件。后续CI机械合入的新输入、fixture导入和实际节点还须独立核对，不能继承这里的源码身份。当前approve不得用作完整c1b2b交付或c1c／c1d自动循环验收。

## 固定提交／新包／CI组合复核

本轮只读审查已完成的构建／安装／收集／定向运行／自身模板原件，没有重跑测试、构建、安装、模型或服务。产品树现为clean的`bcc304894622040a7d844f8c6f9ddfded65aa895`，双亲为r5实现`585e3dabefdde93ac826dec0aa45aa5cb27f420e`与CI组合`7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`。三产品文件与r5完全相同。相对7ed的实际九文件差异保留原r5行为，额外controller模块唯一变更是显式导入原`cycle_budget_root`；`cycle_sdk_activity`及新SDK tests仍在submission，没有迁移或循环互导。已读该实际diff和安装后fixture闭包，归属清楚，无新finding。原CI尾部空行警告属于继承字节，未将其记作本候选diff检查通过。

新wheel为`55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`。不只依赖作者布尔结论，本 reviewer 实际逐项重读当前源码、wheel成员、core和SDK的非editable site：**663项字节／SHA／执行位全同，差异0**。两个site探针均为隔离解释器的真实site导入；core没有temporalio，SDK为1.34.0。构建步骤、两环境`uv pip check`原件均exit0，两份原`verify()`报告各283参考文件PASS且runtime未启动。构建最初冻结af176＋r5八文件的181输入身份保持为其历史构建身份，没有冒充后来CI组合测试输入。

安装后独立冻结在`installed-ci-r1`：`freeze.json`实际SHA=`8b85a24344e9571d22d442c1d96bde8b3119f68c72b46e08a6190660d15d2ba5`，相对af176完整diff实际SHA=`7201deb20067777534deade5e85e2ee6a83e0f9df6acff05882121144eb6888a`，相对585e的merge diff实际SHA=`dd4e3af9922a775125428de5643ef7eeb90f35f8bffd08d4b2e248592eef98b8`。本 reviewer 另逐项重读**183项当前源输入及462项冻结运行文件**的字节数／SHA／执行位，差异0；产品663项亦独立重读同一。当前clean HEAD、父提交和三产品SHA与运行记录吻合。

已核以下准确原件和边界：

|证据|复核结论|
|---|---|
|实际collect／fixture闭包|新SDK解释器`-I -B`、无PYTHONPATH、冻结cwd，exit0／8.61秒。实际2236个节点均唯一，86个文件；六组分别349／285／399／415／315／473节点。迁移controller的direct-root／schema2 request-stop与留在submission的新正常／两个最后gate节点，都解析到原共享`cycle_budget_root`。收集不执行fixture行为。|
|安装后定向15项|实际命令、stdout、JUnit三方一致：**15 passed／186.77秒**，runner187.70秒／exit0，无failure/error/skip。准确覆盖原controller direct-root、新SDK完整正常、最后同步window/source两个参数、原schema2 request-stop及十个短SDK节点；运行前后源／冻结输入不变。应用模块来自新SDK site，没有应用源码路径；它仍使用原Temporal服务替身，不是真实server验收或全suite。|
|新core真实SDK-free S–H|新core解释器`-I -B`、无PYTHONPATH，实际plain `inspect`为0.821秒，完整命令1.569秒／exit0；core无SDK且worker来自新site。读取的是已stop的原完整controller/cycle，返回inspected／submitted、runtime not_queried，S rc0、完整stopped/result两帧。父loop禁用State／SQLite／业务reader期间仍完成实际S–H。H stdout ref为2784B，本 reviewer重读其实际字节和SHA一致。|
|SDK-free观察原件保持|已读before/after及脚本：9份原cycle文件、106份业务常规文件和SQL dump／数据库原始bytes／原授权clock一致。另独立重读当前9＋106份实际文件仍匹配after。9份包含admission lock和fixture marker，不扩大为九类原件；本次冷bootstrap仅属新观察envelope，未替换原业务window。新operation的5文件单列。|
|收尾|原r5补验`v1-source-r5`记录1 passed／23.89秒、八源不变；原r5扫描2137 JSON／45身份、live0／unknown0，两个故意partial launch parse-skip单列。新安装最终扫描689 JSON／16完整记录身份、live0／unknown0，一个故意partial launch parse-skip单列。已读原报告及逐身份结果；这是相应持久证据内的身份扫描，不是全系统无进程结论。|

自身模板已核到原真实命令和实际run：新SDK包通过原`ergora-structure-review@1.0.0`、Codex，run=`7e08910035274c158594bfb92bfc551a`，41.77秒，succeeded／approve。实际stdin与冻结prompt逐字相等，741,435B、SHA=`74b75e06550ce9d7a801ed97fb19a249f62ebced54fe7db40f2cf6a2da8d9b9b`；包含完整operator task和三个祖先／本实例资源。scope为22份文件、679,419B，完整7ed→bcc patch与实际Git diff逐字相等且全文在任务中。实际run result与副本逐字相等，SHA=`d43e38db7134b816acc29bee706d28a0acaeb77ac3e7202a42ccf01671dede9b`，input digest=`5059651067b3ce2733f2a67c390827e130035c6f11faf3c1c3c3f9b80c0e7f42`。原回复明确只approve supplied-source结构，未自行核私有运行或server；本报告不把模型回复当这些运行的证明。

**本轮已核源码／集成fixture／新包定向验收的需求与维护性均approve，开放0／0；R1、R2保持关闭。** 当前未发现新的可达源码或集成问题。真实Temporal、新两activity→首候选原request/root/native链、实际独立budget/cycle进程和queue／窗口／取消／完整收尾仍由现场片接续，尚不能判定完整c1b2b验收通过。source／project漂移、完整v2 facts聚合容量及phase／reap交错的真实服务覆盖只能按后续实际原件登记，不能因本15项通过自动扩大；正式sandbox总Workflow、accepted／rounds／下一候选、实际CI与发布继续各自另验。


## E6／E7最终同片独立复核

本轮承接上节已核 E6 新包及安装检查，直接读取[真实现场交付记录](2026-11-16-training-cycle-execution-live-acceptance.md)、原临时消费者／服务wrapper／fault／驱动／审计脚本和现场原件；未重跑任何测试、服务、安装、构建、网络或模型。最终再核产品树仍clean，HEAD为`bcc304894622040a7d844f8c6f9ddfded65aa895`，三产品owner仍为上节r5 SHA，现场新wheel仍为`55029a3b…`。没有把作者汇总布尔值单独当作通过依据。

已独立重读现场所列**193份原文件**的字节数／SHA／inode及**56个不同完整stdout ref**的实际字节数／SHA，均相符。两个真实execution request的canonical SHA分别为`e742ba3902b7016421c2a0e8869a42e9e2ef42e07c3754a77f43e0dd816ac1a9`、`d66d323b6d480d8bb4c2f9362ff24c175b506567adbea5f872692c1cb7b99719`；本 reviewer 从原JSON重算，逐项核request／launch／attempt／ack／stopped的同链指向，以及native request的原始字节摘要，未发现第二条request／launch。ref只作审计材料，临时Workflow的业务分支读v2 facts。

|原件核对|独立结论与边界|
|---|---|
|真实生产者与来源|三个controller的history起始input、memo、workflow/run/queue与原intent／attempt／receipt逐项一致；重新计算intent和workflow_input的canonical SHA，并与实际controller原文件比对。两个候选使用原experiment链；真实budget与cycle worker分属独立PID/event loop，normal五活动共用1槽、stop独立1槽，budget保持8槽。|
|首候选执行|首场history有11个成功activity completion，request只有一个schedule。原producer→新v2活动→原request／root admit／唯一launch／native attempt+ack／runner／reaper形成完整实际链；SDK-free旧v1 source/ref缺口另由先前源补验和本场六活动证据各自覆盖。|
|真实SDK重试|已读wrapper：调用原安装活动，记录第一次实际返回后才抛测试retryable error。原attempt1返回requested；实际SDK attempt2返回existing_only，同一request SHA。另直接读取attempt2两个operation/request.json，实际source均为同一controller/run、default namespace、normal queue、activity_id=6、attempt=2，mode仅inspect-controller-activity与observe-candidate。history只一个request schedule，maximumAttempts=2、初始0.1秒、两attempt共用10秒schedule-to-close；这是回包后测试错误，不是网络丢回复。|
|真实锁等待与stop槽|已读实际fcntl flock注入和驱动，正常H原read之前等待真实共享锁，驱动持排他锁。选定operation的原事件为wait=`2788673318725298`，stop可见=`2788675116122151`，H acquired=`2788675189647991`（均monotonic ns）；stop在持锁时已写入，间隔1.797396853秒。之后释放锁，normal与完整stop／drain分别完成；没有用stop已发布替代全部清理。|
|独立状态事实|两个runner原输出均actual=expected=70，native均SUCCEEDED；故意无evidence.json，gate均false、archive_report均null。首场最后runtime为COMPLETED／terminal=true／GATE_FAILED；重试场最后观察为同binding/job的RUNNING／terminal=false／QUEUED，同时native SUCCEEDED及execution stopped、reap/durable/executor均true。该非原子交错保持原事实，不推导质量或Temporal完成。|
|旧v1与真实history/replay|首场／重试场／独立inspect补场合计取得全部六活动的真实成功结果。三个controller原history分别101／65／23 events，均以WORKFLOW_EXECUTION_COMPLETED结束；直接解码history completion payload，与各workflow-result副本完全相等。三个replay原件通过，驱动实际使用默认sandbox的SDK Replayer；临时消费者不等同正式c1c Workflow或E8。|
|容量|从history实际base64 metadata/data按protobuf wire长度独立重算Payloads大小，三场completion最大为3597／3582／2691B，与原记录一致且小于32768B；完整ref全部验证。这是本次真实结果容量，不扩写为旧N32矩阵或全部聚合边界重验。|
|原根与进程收尾|两个budget owner和final副本分别与原owner.json／final.json逐项相等，final均completed、durable_stop_confirmed及executor_stop_confirmed均true。五个固定Workflow的最终before/after均COMPLETED、cleanup_terminated=false；完整history亦支持自然完成。最终原shutdown confirmed，daemon not_running、7233／8233／5000无监听；独立汇合原审计三份身份来源得171个唯一PID/start_ticks/boot_id，再直接只读检查当前/proc：live=0、unknown=0。该结论限所记录身份，不是主机全局无进程声明。|

原失败保留不冲销：长socket第一次在服务启动前拒绝、初次MLflow HTTP未就绪、重试fixture给inspect.v1误带ordinal而被真实nonretryable拒绝，以及审计最初混用canonical／raw SHA。短物理路径重注册、HTTP health后再授权、独立inspect补场和只修审计分别解决对应问题，没有修改产品或重授同一cycle。inspect补场原history只有observe→inspect→stop，无start／request／budget root／runner。旧平台配置仍execution_enabled=false；注册一致性和最终安装owner摘要均与固定身份相符。

**最终需求轴approve／开放0，维护性轴approve／开放0；R1、R2关闭，无新增finding。** 已批准合同内的完整c1b2b可以关闭，允许将固定候选`bcc304894622040a7d844f8c6f9ddfded65aa895`导入主树；主树已另经独立审查的Windows双mark修正须保留，本 reviewer没有替该无关修正出具新认证。导入后身份及机械冲突处理仍须由主控核对，当前报告没有声称已经导入或提交。

本结论覆盖源码、实际CI fixture组合／节点收集、新包定向安装检查、自身模板和本片E7现场；不声称官方CI已运行，不代替发布门槛。正式c1c／E8 sandbox总Workflow、c1d验收层、accepted measurement／rounds／训练质量及下一候选／后继ordinal继续保持未认证；native CPU成功和三次临时sandbox replay不改变这些边界。
