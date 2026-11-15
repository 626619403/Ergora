# c1c 首轮 TrainingCycleWorkflow 实施与验证

日期：2026-11-16。当前状态：**r5源码26／新安装runtime53、原完整history安装版回放及新正式类CPU与代表性W0–W10真实恢复／停止／容量检查已完成各自范围。38Workflow终态、服务／监听／自建进程实际收尾，最终853输入和源码保持；完整fresh独立终审两轴approve／0，已固定ec6dcbc并普通导入5b04b2b；推送／新候选自己的CI待。旧r4与新脚本失败原件保持，ordinal1未开放。** 以下至“W0–W10 执行次序”为此前只读准备的原始记录；当时唯一写入为本页，未改产品或运行验收。实施接续及准确候选另见末节。

权威要求为[首轮详细设计](../plans/2026-11-16-training-cycle-workflow-first-round.md)和[独立设计审查](2026-11-16-training-cycle-workflow-first-round-design-review.md)。已读根、src、tests AGENTS、主 PLAN、组件协议及 `maintainable-project-delivery`、`ergora-codebase-quality` 的 owner／caller／测试接缝规则。本记录接续设计，不重做设计审查。当前设计文件 SHA256 为 `d01d5774d592e21178cdabc2a918a61c7ba7f32a673daf6ac321849b28a8dbcb`；独立报告内的 `104624…` 是其原审查样本，不改写历史身份。

## 静态基线与可继承证据

主树分支 `refactor/architecture-foundations`，HEAD `86356927cd88750717bb910502e3f7bd66aa41ba`；已有他人在途 docs。消费者专属树 `training-cycle-execution` 当前 HEAD `bcc304894622040a7d844f8c6f9ddfded65aa895`、工作区 clean，双亲为 r5 `585e3dabefdde93ac826dec0aa45aa5cb27f420e` 与 CI `7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`。尚未把该候选导入主树。实施树／基线由主控发信号时确定，不在主树误用旧产品。

本轮实际重读三 owner 的 raw SHA256，均与前置记录相同：

|owner|SHA256|
|---|---|
|`reference_training_worker.py`|`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`|
|`training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`reference_training_execution.py`|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|

已实际重算前置 wheel SHA256：`55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`，实际 SDK metadata 为 1.34.0。[安装报告](2026-11-16-training-cycle-execution-installed-checks.md)及[消费者交付末节](2026-11-16-training-cycle-execution-consumers.md)记录 source＝wheel＝core／SDK site 各663项、core 无 SDK、283 reference／依赖保持、183输入／462冻结运行文件、2236唯一 collect 节点、15项安装定向通过、SDK-free 真实 S/H inspect 与 scoped cleanup。这些是前置原证据；本轮只读了 driver、freeze summary、selected result／JUnit、core inspect result，未重跑或扩大验收范围。自身 Codex supplied-source approve 亦沿原报告归属，不替代真实现场或终审。

## 固定 producer 与消费边界

已沿专属树核生产链：`cycle_main → _serve_cycle → create_cycle_activities → _CycleOperation/S/H → _cycle_operation → _execution_candidate_operation`。normal 注册旧 inspect/start/reconcile 与两个新 v2，stop 独立 queue，各活动槽1；原预算 worker 保持8槽。当前没有正式 `TrainingCycleWorkflow`，normal 没有 workflows 注册，不能将旧活动测试或测试 Workflow 称为 c1c 已实现。

固定 wire 满足保守的首轮消费：六字段原输入、ordinal0、四旧 v1 保持；仅 observe-candidate／request-execution-or-observe v2 附 facts。facts 的 source operation 可来自 inspection 或 ordinary operations，不能只查后者。预算含 work／total／control／boot；candidate、submission、execution records、runtime、native 分项齐全。H 核完整父原件与固定 run，runtime COMPLETED 的 phase 来自原 outcome.status，故可表示 RELEASE_EXPIRED／INTEGRATION_TASK_CREATED。原 request owner 仍在锁内 publish 前后核 source／window。外来 runtime job 已使 runtime unconfirmed、整体 unknown，保留原观察。

以下没有新增 producer 扩展授权，消费者不得猜测补齐：

- `stop.v1` 没有 cycle 级 durable／admission drained／executor typed 汇总。只可记录唯一 stop command／transport 结果；query 的 cycle stop 字段保持 null／needs_reconciliation，不能以 envelope observed 或 operation_stopped 代替。若将来要求直接认证，须另立 producer wire 变更。
- receipt 早到、runtime SUBMITTING／native request 尚缺时，固定 producer 返回 runtime 已查、native unconfirmed，整体可能 unknown；其 problems 是文字，没有区分正常未发布与各种损坏的 typed reason。完整已认证分项可保存并有界只读观察；不得读错误文字重授 start/request。身份／source／clock认证缺失时保守对账，不在 Workflow 另读 refs／文件。
- start／reconcile v1 没有 work facts，只有旧 total observation；不能拿旧结果创建／延长 work 截止。cold facts 不等于 runtime 已查询，只有后续完整同 run、Binding/job 与双 QUEUED 才能请求。
- 本片没有 accepted archive／gate／rounds 可消费许可；native成功、reap、runtime phase 各自独立。c1d 前 ordinal1、measurement_accepted、selection_complete 始终禁用。

## 最小实施与已有接缝

收到信号后的首选产品改动只有原 `reference_training_worker.py`：模块级可选 SDK 导入／应用依赖 pass-through、真实模块级 decorated `TrainingCycleWorkflow`、显式工厂、run/status/request_stop 和少量内聚私有方法，以及 `_serve_cycle` normal 注册。`training_execution_protocol.py` 只在确有共享纯 shape 校验需要时调整；不预设改 runtime／submission／execution、增模块／manager／reader／账本。原 source-pin owner 已覆盖 worker，旧 live owner 不因换源码继续执行。

实际唯一工厂 caller 是 `_serve_cycle`；run/query/signal 是框架必要入口。已读新安装 SDK 的 `_definition.run`、sandbox `_runner._create_instance`、deterministic `_asyncio.wait`、`_workflow_instance._await_temporal_operation`、公开 payload converter／history info 源码：run 拒绝 locals 类，默认 sandbox 按 module/name 重导，wait 的 finally 只移除回调，直接 await activity 的取消会由 SDK 等待处理。因此仍按设计持有 ordinary handle、先取消请求并立即调独立 stop、shield 唯一 stop、最后传播 CANCELLED；本轮源码阅读不认证该时序已经运行。原 `_ErgoraPackage` 仅在真实新安装复现 package 导入失败时复用。

现有测试归属已按 bcc3048 核实：`tests/test_training_runtime.py` 有真实 SDK capacity、ActivityEnvironment 的 source／window 和真实 SDK service lifecycle 接缝；`tests/test_training_submission.py` 保留 `cycle_sdk_activity`、receipt前首活动、双 QUEUED／外来job／丢 completion、最后同步gate、完整 stop／capacity；`tests/test_training_cycle_controller.py` 有原 root、取消／交接／stop 及共享 `cycle_budget_root`。`training_controller_service.py`／`training_submission_client.py` 是真实 codec＋固定 history 的离线替身，不是实时 server。`tests/test_budget_workflow.py` 提供真实 local Temporal／Worker／package finder 使用先例，但不覆盖本类。优先沿这些文件补最小行为检查，不新加 CI job 或重复服务 fanout 矩阵。

## W0–W10 执行次序

下表均未执行；精确定义仍以权威设计为准。先取得主控前置终核／实施信号，再固定实际候选及输入。

|次序|节点及证据重点|
|---|---|
|1|W0：可选 SDK/core 缺失边界、模块身份及默认 sandbox 准备；正式 normal Worker 注册、原预算进程／stop槽保持。|
|2|W1：正式类真实首轮，receipt先到／SUBMITTING等待／双QUEUED；history一次start/request、原request/root/唯一launch与ordinal1缺席。|
|3|W2：command前后／fsync后丢completion，文件不存在亦不重授；原attempt／receipt／request／launch数量与SHA。|
|4|W3、W4：同run worker重启、成功／失败／终态history replay；A+remaining只收窄、v1不刷新work，排队／回传／timer及server暂停后BOOT最后gate无新publication。|
|5|W5、W6：normal真实阻塞下重复signal/cancel即时独立stop；唯一stop／total不续、CANCELLED与实际资源分列；native/reap/phase交错不接受测量、不写rounds、不发ordinal1。|
|6|W7、W8：全部ordinary失败亦计256，真实server history阈值与stop余量；实际Payloads含metadata的32KiB拒绝及完整query/outcome／stop失败保留。|
|7|W9：原身份／source／project／旧pin拒绝与显式本地恢复；只补与本片新增路径有关的回归。|
|8|W10：新candidate的新wheel、core／SDK site与输入冻结、283／依赖；正式默认sandbox真实首轮及代表性恢复／丢reply／取消；全自建进程、端口、Workflow收尾。新安装不能继承55029对新字节的认证。|

随后更新本片状态与主 PLAN（由主控协调），提交完整实际差异／验证给新的 fresh reviewer 做需求／维护性两轴，并跑自身原结构模板。CPU受控runner只证明控制／执行链，GPU、训练质量、真实接受／两轮、公共入口和 WA 未决人工设计另属后继。当前下一步为等待主控提供实际 c1b2b 现场／终审结果和实施信号。

## 首个核心实施候选与源码检查

主控已确认前置完整终审／真实现场闭合，授权在独占 `training-cycle-workflow` 树实施，基线 `01ef69b71137df860e8fc433362d039ae241e744`、分支 `feat/training-cycle-workflow`。本次只改 `src/ergora/reference_training_worker.py` 与原 `tests/test_training_runtime.py`，不改 protocol／runtime／submission／execution、CI、依赖、283 reference 或业务仓库。主 PLAN 及后续新包／真实服务／自身模板／fresh 审查由主控协调。

原 worker 现定义模块级 `TrainingCycleWorkflow` 和显式可选 SDK 工厂，normal Worker 注册本类，stop queue／两槽1:1／原budget8保持。类只消费原 v1/v2活动、纯 validator／converter 和 deterministic SDK API；固定六字段、父run／候选／Binding/job与原记录摘要，一次 start／request 的标记在command前消耗，v1仅缩total，A+remaining只缩不延，全部ordinary最多256，history8000／8MiB守界，独立stop只用已认证total。ordinary pending通过确定性wait持有；signal／取消先请求ordinary cancel并在同activation排独立stop，shield唯一stop后保留CANCELLED。旧stop无cycle汇总，返回封套亦不填durable／drain成功。无accepted、rounds或ordinal1行为。

已执行的检查均为**源码＋SDK离线activation，未接真实server/history**：

- 使用前片55029 SDK解释器 `-I -B`，显式将本树src/tests置于导入路径并核实际 worker 来源。真实默认 `SandboxedWorkflowRunner.prepare_workflow`及每例重新创建的默认sandbox实例均通过；类module/name/qualname准确。20项（16个新activation参数节点＋4个原SDK lifecycle节点）**20 passed／2.99秒**，完整runner4.40秒，stdout／stderr／JUnit在主仓库ignored `cw1` 的r1原件。
- activation检查覆盖首轮等待／双QUEUED、三事实交错和c1d门、两种effect丢completion不重授、A起算／v1不放work、normal未完成先排stop／重复cancel、全部失败计256、两个history阈值、signal拒绝及原身份／budget／GATE_FAILED。activity结果在此接缝显式注入，不能冒称真实producer／native验收；history length／size也是SDK activation输入，真实server阈值及Replayer另验。
- 后只增强原signal节点：compact JSON恰32KiB但完整Payloads含metadata越界，随后合法signal保持完整首reason；完成stop后typed outcome仍needs_reconciliation且三业务stop字段null。该节点新冻结 **1 passed／0.46秒**、完整runner1.86秒（r2）。未无依据重跑其余未变节点。
- 现有core解释器实际无temporalio，显式导入本树worker成功，工厂明确拒绝缺SDK；另SDK解释器注入坏SDK内部依赖，原ModuleNotFoundError名称原样传播，未误当core可用。两次独立subprocess均exit0，命令／输出在 `w0-source-r1.json`。这仍是源码检查，不是新安装认证。
- 两个修改文件的内存compile与 `git diff --check`通过；未写pyc。r2前后852项tracked src/tests/examples/scripts/pyproject输入的字节／SHA／模式相同，无产品或输入在运行中漂移。

准确r1／r2冻结、完整binary diff、命令／环境／stdout／stderr／JUnit均存主仓库ignored `.ergora/checks/cw1/`。r2完整diff SHA256=`e21dcd9d8a88c1c437dd9d91510845e42dd92024635ff32d260bd4868a5b16b5`；worker raw=`f16d78e056cf866f1d2017e43f94e3e062a35ad4bc2b437d841969ee1c450fea`，runtime测试raw=`733f5a3e7b097178273e0e7dc054175b51ae0fc661012ab3d1392f5484dc3a8e`。这些是未终审的核心候选身份，不是发布或全片完成证明。

尚未完成W0的新安装／真实Worker注册、W1／W2／W5的正式类真实服务／原件链、W3真实history replay／重启、W4 server暂停和最后BOOT gate、W7真实server阈值、W8真实服务容量与W9旧pin现场、W10全新wheel/core／SDK及统一资源收尾。前置CPU runner故意缺evidence而GATE_FAILED，只能用于负路径，不能充本片正常首轮；正常CPU终点须沿原完整证据合同另验，GPU／训练质量及c1d仍另片。

主控已另授权仅为基线固定做本地WIP提交，再普通合入已独立通过的clock平台skip提交 `c52fc0a338118a19491ad7cd458b82cf2f146a9b`；该提交／合并及后继冻结状态待下节补记。下一步提供固定完整diff给主控启动新fresh源码两轴审查／自身模板和新包；不push，不将WIP称终审通过。

## 固定WIP、合入平台skip与r3交接

已按上述单独授权，将r2两文件固定为本地WIP `05f966597d1ddc932d3cc1c25b63362bc371a19e`；随后普通merge `c52fc0a338118a19491ad7cd458b82cf2f146a9b`，无冲突，得到HEAD `fa78747d6c6ca62935fe6a44aa6db143c362baad`。merge后最初clean。三方静态核实：WIP→merge的src/tests/scripts/.github/pyproject只多原runtime测试的 `import sys` 和已另审的Linux BOOT skip两行；worker逐字同一。c52→本片完整产品差异只有worker和原runtime测试；随merge进入隔离树的主控docs没有回写他人主文档。未push。

最终freeze前发现一个具体W2回包边界：原H在request publication后丢completion frame，可返回完整unknown封套但facts=null，而非ActivityError。最小修补限于**本片已经发过唯一request、原work已认证、同一controller仍完整匹配**的这一回包：沿封套收窄total，转已有work内的只读observe，不能从null创建work／重授request。缺facts的cold仍不重新探测；其余认证失败保持保守停止。现有丢completion参数例只新增这一真实wire分支；没有扩大其它矩阵。

该修补及参数例当前为fa78747上的两文件未提交差异，未作第二次未经单独授权的提交。主控用于源码fresh review的权威候选为 **fa78747＋r3完整冻结字节**，不能只读其HEAD当最终源码。ignored `.ergora/checks/cw1/` 中：

- `freeze-r3.json`：固定HEAD／双亲／working status、权威主设计SHA及853项tracked src/tests/examples/scripts/.github/pyproject的字节／SHA／模式；新增一项相对r2来自明确补冻的 `.github`，没有把历史852改记为853。
- `candidate-r3.diff`：相对c52的**完整**产品差异，包含WIP与后继修补，SHA256=`b88c3cd52cc5d910fa74bf960d73e8bd8e07284b43c6c442244ac9dc7a02fa03`；`working-r3.diff`另存只相对fa78747的后继差异。
- r3 worker raw=`bbe0f58860847be48b7ffea3df01d9e7cc4430d65c8686e01bbd5e2949e594ce`；runtime测试raw=`469d8b754784d5caa3ce4dab565c0d5a9a66d73b5e4475072ad5af6bd06c1838`。`result-r3.json`／stdout／stderr／JUnit记录新实际源码导入、**21 passed／3.32秒**（17新activation节点＋4原lifecycle节点，完整runner7.28秒）、853项前后相同及完整diff未变。由于新增可达W2分支，重跑了本片核心接缝；没有跑全suite／native或服务。

r3内存compile与相对c52的diff-check均通过，产品／测试只有预期两文件。当前实现／activation／新安装／真实服务／独立审查状态分别记账：本实施者接续仅负责源码、activation、静态核验及本交付；新的fresh源码两轴审查、新包、正式类真实W0–W10代表性验收、原结构模板及主PLAN由主控协调。没有自行启动Temporal、MLflow或训练，没有把55029的安装结果继承到新字节。

正常CPU现场的原接缝为参考 `local/agent_platform/training_executor.py` 的trusted runner占位符 `{manifest}/{output}/{baseline_repo}/{candidate_repo}`，产出 `{output}/evidence.json` 后由原 `perfctl archive` 做完整gate。证据格式可查参考 `upstream/docs/evidence-format.md` 和 `templates/training-optimization/{evidence.json,runner-template.example.json}`。现有 `tests/fixtures/training_evidence_archive.py` 和参考 `upstream/demo.py` 均明确synthetic，前者还会重写fixture manifest／request，不可作为已授权运行中的真实runner。新CPU现场需先冻结适用检查／配对计量合同，由runner产真实CPU范围的原始记录／结构化检查／比较器输出与哈希；合成示例PASS不能填成训练质量或实测收益。当前仓库没有已核可直接复用的实测CPU正gate runner，该实际样例仍由主控现场片补齐或保留未验。

## r4：fresh审查R1／R2的修前反例与最小修补

fresh reviewer在r3指出两个可达问题；本实施者已复现并修补，**仍待原reviewer复核及全文审查结论，不自行关闭finding**。HEAD仍fa78747，当前两文件未提交；r3源码／wheel／自身模板证据保留原身份，不转记r4新字节。

- **R1，完成路径绕过守界。** 原 `_next` 在terminal判定后才核guard，run又在后置guard前返回成功。新增一个真实默认sandbox activation回归，分别把同一完整终点放在work新截止已过、history8000 events、8MiB、ordinary256边界。work反例按实际SDK command timeout取remaining=timeout/4，R=A+2×remaining仍在原activity timeout内，却已过消费新样本得到的A+remaining；total保持正数。原r3产品raw未变，四参数均在“已经complete且stop0”的断言处失败，**4 failed／1.31秒**（runner2.79秒）。修补只将 `_guard()` 提到 `_next` 开头，在已认证facts消费之后、任何terminal完成／效果选择之前执行；去掉positive条件中的后置重复guard。修后四边界都立即排唯一独立stop并返回needs_reconciliation，不再以已停止executor代替控制器的守界。
- **R2，非dict信号在handler前被SDK丢弃。** 在原signal拒绝节点增加一次 `h.signal([])`，原r3产品上 **1 failed／0.58秒**（runner1.95秒），query的last_signal_rejection为None；真实SDK日志明确因dict类型反序列化失败而drop signal。最小修补为移除handler参数dict注解，让原有完整容量／shape校验记录typed拒绝；该节点后续过容量、异身份和合法首reason的原检查保持，合法signal仍生效，不增加其它矩阵。

修前命令／freeze／stdout／stderr／JUnit分别保存在ignored `cw1/*r4-before*`（R1）与 `cw1/*r4-r2-before*`（R2）；两次前后853输入完全相同，产品仍为r3 raw `bbe0f588…`。没有以假想反例替代真实失败，也没有修改旧证据。

修后r4在同一既有SDK解释器 `-I -B`、明确本树src/tests导入下重新执行受影响核心接缝：**25 passed／3.85秒**（21新activation参数节点＋4原lifecycle节点，runner5.21秒）。包括新增四终点边界和增强signal节点；默认sandbox实际运行，activity结果／history计量仍是离线注入，不认证真实server/history或新包。两文件内存compile、相对c52的diff-check通过；853项冻结输入及完整diff运行前后不变。

当前源码重审权威身份为 **fa78747＋r4冻结字节**：`candidate-r4.diff`（相对c52完整差异）SHA256=`edc532693b2eadfeb73f49dfe3b9520591fb7d65974bba00da3efa5e302700e6`；`freeze-r4.json` SHA256=`1a28aa876840e0373665b3e492a589ca7752c0839fe655d255235cde1dcf2899`。worker raw=`187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`；runtime测试raw=`56f67f74aadbe8a0db53fd3ea7df22f9b2865327c104d8533871753e29c1e6a1`。命令与实际结果在 `result-r4.json`／stdout／stderr／JUnit，`working-r4.diff`另存相对HEAD差异。产品／测试仍只有这两文件；未commit、push、安装、启服务或改主PLAN／主审报告。交主控做fresh复核、r4新包及现场接续。

## r4 源码复核、安装与真实现场准备

[原 fresh reviewer 复核](2026-11-16-training-cycle-workflow-source-review.md)已确认 R1／R2 修正及原反例，源码需求／维护性均 approve、开放0；另独立驱动核到耗尽时只排一次 stop、原 total 不续，以及坏 signal 的 typed 拒绝／随后合法停止。结论不认证尚未执行的现场。

r3 先构建非 editable wheel `a84e944cc16f6f0537e14e1836914f1eb83950ac0ddb7f03e738b1686ff4a859`；core／SDK 各663文件的 bytes／执行位与 source／wheel 一致，283参考及依赖通过。r3 自身结构审查模板实际 Codex 75.36秒 approve，完整16文件／587403字节和3份祖先资源实际进入642024字节stdin。该源码范围结论没有发现后由 fresh reviewer 复现的 R1／R2；保留原回复，不将其 approve 当作无缺陷证明。

修后重新构建 wheel `7ee6cb43eefc682f0ace5f3732369156ade5cb78978c004062eb0c3e4a2bda67`，存于 ignored `cw1/package-r2/`。新 core／SDK 各663文件的 source＝wheel＝site-packages bytes／执行位全部一致；只有原 worker 相对 c52 改动，283参考和依赖检查通过；core实际无SDK，SDK1.34.0。新 core 导入成功，调用工厂以明确 `requires ergora[temporal]` 拒绝。冻结副本中的整个 `test_training_runtime.py` 在新 SDK 安装的实际 site-packages 导入下 **52 passed／54.96秒**（完整driver57.49秒），stdout／stderr／JUnit／命令及测试原 SHA 均保留于该目录，没有导入源码树。

r4 自身原结构模板实际 Codex 41.27秒 approve；完整16文件／593079字节、原3份祖先资源实际进入651156字节stdin，stdin与冻结输入逐字一致。候选 input digest、原回复／运行ID均存 ignored `cw1/self-review-r2-codex/`。沿用户已授权回退，复用既有 Claude Code 420.60秒 timeout 事实，不宣称本次异后端成功；这些是完整提供文本的审查，不代替源码 fresh审查或真实服务。

已通过原接口配置全新独立CPU测试项目、固定真实Git源码、实际输入／两份配置／独立整数oracle／原比较器及新manifest，没有使用synthetic archive helper补PASS。初次本地配置把 `allowed_paths` 写为 `.`，原native校验明确拒绝；改为四个实际文件路径后重新注册成功，未改产品校验。CPU样例的 fresh审查另发现外层 integration 缺candidate_commit，已在样例副本最小修正，正在用全新项目／baseline／manifest身份复核；未改旧immutable准备原件，也未投递该旧候选。

真实现场当前仅启动原Supervisor管理的Temporal／MLflow及独立 `training-budget-worker`／`training-cycle-worker`，四服务均RUNNING，两个worker PID独立；其它执行服务未启。正常cycle Worker使用正式类及默认sandbox，stop仍独立queue／slot1，原预算slot8保持。尚未投递正式Workflow；真实首轮、history replay／重启／取消／容量／最后gate及最终全进程收尾仍开放。外部 `/proc` sampler只观察本次自建daemon及后代，最终按原件和完整进程身份核收尾，不扩大为OS隔离或GPU／训练验收。

随后[真实现场报告](2026-11-16-training-cycle-workflow-live-acceptance.md)已取得正常与负gate两条正式类路径及实际history回放：负例原归档正确拒绝平台日志漂移，stop1并needs_reconciliation；修正样例后新身份实际8对CPU／512输出检查、原archive gate通过，start1／request1且无stop，原durable／executor stopped均true、固定子run仍AWAITING_RELEASE，父run正常first_round_observed_c1d_required。两实际history均由正式类默认sandbox Replayer通过。没有ordinal1、measurement_accepted、release或baseline迁移；重启／丢reply／取消／history边界与统一收尾继续接续。

## r5取消缺陷修补接续

真实W7取消暴露的SDK缓存eviction问题已按[独立诊断](2026-11-16-training-cycle-eviction-diagnosis.md)最小修补；准确源码、先红后绿、wheel、安装53项及原完整history安装版回放见[修补交付](2026-11-16-training-cycle-eviction-fix.md)。ordinary TRY_CANCEL与stop WAIT／shield的设计已在原计划明确修订，真实资源停止仍归原S/H／reaper，不能由本地handle完成推断。fresh源码两轴及自身原模板Codex approve仅认证各自范围。原r4现场已全部收尾；新r5正式类现场使用全新任务身份接续，W0–W10未因此整体闭合。

## r5正式类新现场与统一收尾

新身份CPU、丢完成前后／同run重启／真实服务断联／阻塞重复停止／实际8MiB及完整编码分项、失败原件、原链、source与统一资源收尾见[新现场逐场结果](2026-11-16-training-cycle-workflow-live-acceptance.md#r5现场逐场结果)及该页末节。新包／源码／自身模板／fresh终审各自范围分列；完整[终审报告](2026-11-16-training-cycle-workflow-final-review.md)已独立核实最终原件，两轴approve、开放0。新产品仍严格ordinal0，最终发布和c1d／c2另验。

## 固定提交与开发主线导入

产品已固定提交`ec6dcbcf23d35818aa23e87b6dbb129ed8ff75a1`，从fa78747的最终两文件变化为150行增加／9删除；相对c52的整体首轮实现仍为原两文件833行增加／6删除。以普通merge导入当前开发分支`5b04b2b4cb4eb1c5d6899fc517cf86ecdec5536f`，无冲突、无额外产品文件变化；没有自动合main。raw worker7996f73d…／tests4b5d7ed4…不变，原包与现场按同一字节绑定。最终fixed-commit身份复核、普通push和准确新候选自己的CI接续，不借df43660成功代替。
