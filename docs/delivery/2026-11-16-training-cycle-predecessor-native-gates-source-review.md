# c1d M5-G 前驱与最后准入：独立源码审查

2026-11-16。审查者：fresh-context reviewer `m5_predecessor_source_review`。按 `maintainable-project-delivery` 的 independent-review 和 `ergora-codebase-quality` 的 module-design／test-seams／repository-style 审查。未参与实现；本次仅只读源码、冻结输入和既有证据，唯一写入为本报告。未启动 tests、probes、模型、服务、安装，未改 source／test／PLAN，未 commit／push。

> 当前结论：r3已以真实红／绿关闭R3，r4仅普通测试出生预算显式配置，经单项原窗口／来源门复核。准确r4源码限定需求／维护性两轴approve，R2／R3关闭；R1 whole-hook无SDK mandatory仍开放，完整M5未通过。文末保留所有版本身份与原失败，最新结论只适用于准确r4，不转授其他源码／安装。

## 首冻r1：两轴结论与适用范围

|范围／轴|结论|开放项|
|---|---|---|
|新增全链认证与原最后门禁接线，需求静态源码范围|**approve，限定下述冻结10文件**|此范围未发现新增阻断性算法或接线缺陷；不授予 schema3 效果|
|结构／维护性，所审冻结源码|**approve，附非阻断 P2 建议**|R2：H 的重复 ROOT 全量遍历|
|完整 M5 原需求／整片验收|**未通过，pending；R1 为已证实 mandatory 阻断**|whole native hook SDK-free 未满足；冻结回归终态、新安装、自身原模板及最终整片终核尚无本次可认证证据|

第一行不能解读为完整 M5 通过。纯 `-P -S` 本地认证通过与附真实 SDK 后到达 callback／schema3 关闭分支分别有效，但两者组合不能替代整条 hook 拒绝 State／schema／SDK 导入的验收。schema3／ordinal1 的 start、create、request、launch、native 正向效果仍属 M6，当前必须继续关闭。

## 输入身份与检查边界

主项目为 Ergora，文档均属本项目。已读根／源码／测试 AGENTS、`docs/PLAN.md`、组件变更协议、原 `training-cycle-measurement-wire`、`training-cycle-predecessor-native-gates` 及其独立设计审查，按原合同核 candidate-bound、六阶段、出生身份、锁内最后准入、attempt-before-send、unknown 只对账、来源不可升级与 native 隔离。主树读到分支 `refactor/architecture-foundations`、HEAD `debf6f96ed02620d22adc0ac6385c72641b3d53b`；主树他人的文档差异未覆盖。

实际审查源码在 `.ergora/worktrees/training-cycle-predecessor-gates`，分支 `feat/training-cycle-predecessor-gates`，基线 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，尚无本片提交。全 patch 为 `.ergora/checks/cycle-predecessor-native-gates/m5-g-source.patch`，77,125B，SHA256 **`fba1838ac6e7cb13cdbab9ec9b96e66cc38cdf8c5de3eb00c381f120ca050e1d`**。实际 `git diff <baseline>` 的完整字节 SHA 与该 patch 相同；diff 名单恰等 source-freeze 的10项，无新文件。另读28,340B的 `01-pure-migration.patch`，区分机械迁移与新增认证，未把全片称为行为不变。

本次逐项重算 source-freeze 的 raw SHA／bytes，10项全相同；对 frozen-inputs 的665项输入逐项重算亦全相同。manifest 分列25项 gate sources 和4项 measurement sources，未读取旧 private command.json 的环境值。

|冻结文件|raw SHA256|bytes|
|---|---|---:|
|`src/ergora/reference_training_budget.py`|`c5d0245f1946e2375c6f6a7bdacd1fec8365e58074dd57a7912c7825550b91be`|37337|
|`src/ergora/reference_training_execution.py`|`fa12537d2514e4ea29da496f55f4d4492d8f5485890eae84b6cc159db1d7ef4a`|12215|
|`src/ergora/reference_training_submission.py`|`abc69091830934cf5759f436a7bcfbc9c399490fe44b9506c173f3d92a3b492c`|24416|
|`src/ergora/reference_training_worker.py`|`5ad5466c84dba9a093a53b9a4f8c626e06939d637e8268ce41403265b67c8334`|145827|
|`src/ergora/training_cycles.py`|`911a6f6ff0aed679d4eb85ee0c20d8c19dfd50f24aaef37261cca015493a5cd5`|39024|
|`src/ergora/training_execution_protocol.py`|`5cfeac98893c3b8715947956b0b718218129dd556e7bf8a465fe9e6b8dda8347`|115669|
|`tests/fixtures/training_budget_client.py`|`438f4bc471a3f59c9a094235cef33f0230481ced4adba3cdd846c344e09859df`|13425|
|`tests/fixtures/training_controller_pause.py`|`702476e1ddd8d79d5a76aa93dd93db20a5e87f43bddd115ab67b16fe14dcd971`|1577|
|`tests/test_training_cycle_controller.py`|`7a075ff2e6dc7aaaa4988201f361a2b844a42446304df2d5657dbef98991f55e`|95798|
|`tests/test_training_submission.py`|`d6efa091486365ed937f5cf5d191af6c69b366307eab011c0519076cb5baea19`|242394|

源码位置在下文均指上述隔离树；未改的 reference／native 资源也是该树原字节。审查还沿必要邻接消费者读取 `reference.py`、原 reference executor／training／Temporal client、原 admission-v1 patch、原 registry／submission／execution 生命周期及相关现有测试，不凭作者叙述推定行为。

## Findings

### R1 · P1 · 完整 native hook 仍导入 SDK，完整验收阻断

**位置：** `training_execution_protocol.py:1683` 导入 `agent_platform.training_executor.process`；原 `data/reference/platform/local/agent_platform/training_executor.py:13` 顶层导入 `.training`（实际打 patch 后为第14行）；`agent_platform/training.py:20` 导入 `perf_temporal.client.load_experiment`；`data/reference/platform/upstream/temporal/perf_temporal/client.py:10` 导入 `temporalio.common`。

**可达证据：** 既有 `exploratory-05.log:135` 起的真实 traceback 在 protocol 第1683行、callback 入场前被禁 SDK import hook 拒绝，最终为 `AssertionError: Native reader imported application or SDK: temporalio`。已与真实源码逐点核对。`native-sdk-dependency-originals.json` 给出原 executor `e6d2273c…`、training `97dcf661…`、client `e01ac4d8…`、原 patch `45af2823…`、descriptor `d7e2b706…`、manifest `1f39b63b…` 及实际 patched executor `feed0fa7…` 的 raw 身份；本次全输入核验涵盖未改原件。

**后果：** 新纯认证 owner 不导入 State／schema／SDK 的局部结论成立，整条 `native_main → 原 patched executor → callback` 的 stdlib-only 合同不成立。该依赖在本片前已存在，不能归因于新增 verifier；它仍是本片原 mandatory 验收条件，不能被历史存在、schema3 效果关闭或测试附 SDKsite 消除。当前测试明确记录 `executor_sdk_loaded=True`，没有给出 whole hook 无 SDK 的通过证据。

**最小处置：** 由原 reference/native owner 做独立、版本化依赖隔离，保留旧283／旧 v1 原件与旧路由；使用真实完整 hook，在禁止 State／jsonschema／YAML／Temporal import 的环境到达真实 callback 并检验原锁／permit／持久阶段。不能补第三方假模块、mock verifier pass、放宽 source 表或用两份局部证据替代。设计在途不等于修复；本报告不认证它。

### R2 · P2 · H 在同一 local gate 重复完整 ROOT 遍历（非阻断维护性建议）

**位置：** `reference_training_worker.py:1082` 调用 `protocol.validate_sources(capability)`；本片已在 `training_execution_protocol.py:961` 将 `reference.verify()` 放入该函数。worker 第1086行仍直接调用一次 `reference.verify()`，中间仅比较四 measurement sources。

**可达情形与后果：** 每次 `_round_local_gate` 都顺序对同一个包内 manifest／ROOT 再遍历一次283文件；后者没有独立输入或不同来源。该 gate 在 collect／reconcile 多个真实同步点反复调用，重复 I/O 消费同一不可续 work／operation window，并让 ROOT 责任同时散落于 H 和共享 source owner。没有证据说明这项重复是必要的额外边界；逐文件验证本来也不构成抗同用户并发替换的原子快照。

**最小修正：** 移除 worker 第1085–1086行遗留注释／调用，继续由 `validate_sources` 完成先 pin25／manifest、verify ROOT、验证所选安装、最终复核 sources，保留 H 的 measurement 比较及最后 clock／active／stop。仅复核原 round collect/reconcile 和 source／ROOT 负例即可，不需新增测试矩阵、来源项或模块。此为非阻断建议，不否定当前保守拒绝语义；若实施会产生新 patch，须重新核准确身份及受影响证据。

## 需求源码判断的具体依据

- **整条前驱链：** `training_execution_protocol.py:1473` 的 `authenticate_cycle_candidate` 从当前完整 intent 的 predecessor 递减回0，ordinal 来自严格 binding／原实际 selection；固定目录只含 `rounds.json`，先核 index 完整 raw SHA／bytes，再核纯内容、prefix、previous_report 与所有旧轮逐值延伸。第1528行起遍历原件，`round_report_binding:145` 核 manifest／spec／binding／revision／annotation／完整共同约束／anchor；不只核最后一轮。每步沿早轮原 intent 中的 predecessor 继续，第1605行后核最早 previous=null 与最终 predecessor=null。
- **来源与原库存：** `authenticate_cycle_candidate:1552` 起将原 request 的 identity／snapshot／activity_context、成功 helper 的完整 accepted／durable 投影、父 fixed run、原 intent、完整 observation/ref 和推导 acceptance 相等；使用 canonical `_match` 防止 bool 与 int 在 helper 投影中混同。`ExecutionRecords.load/request_record:1298/1373` 重读原 intent、owner、五 records、start attempt／receipt、native request；`observe(durable=True):1401` 从真实 originals 生成完整 raw inventory并同步／重读，和观察库存精确比较。evidence.files 完整映射在第1580行后沿原 safe-file 与冻结 state/config 根重读，拒别根／`..`，不扫描或升级旧观察；不复制 archive comparator。
- **H 与 native 责任分开：** worker `_round_previous:1177` 消费上述同一算法，再调用原 `_round_read_evidence` 重核 archive 语义；只有紧邻前轮额外查当前四事实／phase。纯 boundary 对更早退出 owner 不做 live 要求，不查 SDK phase。原 `_round_operation` 的同步后重读和最后 gates 保持。离线 `training_rounds` 的 coverage 仍不授予 origin／execution／promotion。
- **25＋4＋ROOT与所选安装：** `validate_sources:954` 先核原25恰好键集／完整 digest／当前字节，pin 原 owner 的 manifest 后调用原 `reference.verify`，再验所选 installation／descriptor并重核 sources。`_round_sources:1446` 读取授权出生四项映射，并核 ready-bound 原 owner capability；unborn prepare 不虚构25项授权 pin。认证前后均重核四项和同一原预算。未新建 whitelist、ledger、proof、可变 current-round 或替代 manifest walker。
- **真实最后动作：** Budget.source 第263行先完整认证再明确拒绝 schema3；context 第1636行同样认证后关闭。原 submission 第234行持父共享许可，attempt 第251行写入／同步后再 preflight／require_active，保留 attempt-before-send；本片第355–358行补 intent同步后复核。原 BudgetAdapter 第1672行持父许可到原 create 返回，lookup absent 第1687行仍在原 registry create 链里 require_active。Execution.current 第57行重读现存链，request 第88–91行、launch 第108–123行仍在原 execution 锁和父许可内 publish后复核。未知／占用 launch 不换 UUID重发。
- **native 持久阶段：** native callback 第1686行只接受 launch已消费而 attempt/ack/stopped为空；`active:1711` 每次重载、validate_context、核同 owner及恰为本次阶段的 records，随后原 owner／clock／fence／parent stop检查。attempt 第1729行、ack 第1734行发布同步后分别 active，未把自身新记录误判成未用 launch，也未放宽成任意旧 attempt恢复。原 patched executor 仍在 executor.lock 内 callback后才写 started。原 result 在 process中先读并返回，schema3外层不提前拦历史 result；外层父共享许可目前仅schema2，第1737行仍明确，不能声称schema3正向已经闭合。
- **旧版本：** schema1 手工不能带controller；schema2保持原 v1 binding／首轮限制；schema3仍明确关闭；未知版本第1634行显式拒绝。owner1/2 reader与原25键集未宽化，无旧ID升级或clock续期。两个旧schema3测试放宽了错误文案断言，仍核 ValueError与无新增效果／已有result早读；这只是缺完整binding会先拒绝的实际顺序，不能用于认证完整schema3正向门。
- **维护性与复用：** 纯 selection／report binding／pin／four-fact predicate／acceptance从worker迁入既有 protocol，worker与真实 budget/context/native消费共同计算，旧本地副本已删除；没有通过同文件重复调用或测试伪造第二生产caller。`_round_candidate_intent` 与 `_round_sources` 为该完整认证内部身份／来源算法，非单调用转发层。State／SDK／archive采集和发布留原owner；六产品文件没有修改原六阶段／preset／批准／release或baseline迁移流程。除R2外，在所审范围没有新的维护性阻断finding。

## 实证、检查与未验项

本次自行执行的检查只有只读 Git／文件读取／raw hash与bytes重算。没有运行任何测试或probe。实际测试结论仅来自已存在原件，并按范围记账：

|既有原件|本次读到的结果|可认证范围|
|---|---|---|
|`exploratory-02.log`|3 passed／55.20s|当次探索：原M2 H collect/reconcile、k1/k3与最早index漂移；非冻结整片验收|
|`exploratory-05.log`|完整禁SDK hook在callback前失败的原traceback保持|R1真实失败；不能被后续局部通过覆盖|
|`exploratory-07.log`|1 passed／55.87s|当次大reader／来源探索；测试源码和`native-reader-results.json`分列纯-S无SDK与实际native附SDK到关闭分支|
|`frozen-source-01.log`|审查期间已有进度中的 `F` 标记，无pytest终态摘要／失败详情|冻结回归仍在作者运行且至少有失败标记；本报告不宣称通过节点数或总suite通过|

已读新增测试的实际序列：k3先通过后篡改最早index、原start attempt的raw空白、旧archive文件、原helper bool投影；大观察按最终UTF-8/LF编码 M−1/M/M+1，经H、Budget.source、validate_context与分开的两个native模式；复制实际package后改25中来源、四measurement、manifest与ROOT；真实attempt／ack持久点暂停后改来源／ROOT／clock，并要求没有 started/result/runner、保持原记录。测试使用合成已停原库存、SDK服务替身和真实本地S/H／patched executor，未把它们称作真实schema3训练。已检查 fixture 保留原锁／fd／publish和真实callback，未用新 verifier pass替身；这些静态观察不是测试运行结果。

尚不能关闭：冻结定向回归终态与准确节点、必要旧v1 history按影响回放、当前候选新非editable core／SDK安装及实际site-packages身份、完整原自身审查模板、whole-hook无SDK、schema3持父共享许可和全部正向action、更晚schema3 attempt／ack故障门、完整M1c与正式V2／真实两个新候选CPU结果。也无GPU、质量／性能收益、公开CI或部署认证。局部检查不继承前片68ba793／1f57ca4的验收。

下一步是保持schema3效果关闭，完成R1独立版本化隔离及对应完整hook验收；收齐本冻结候选自己的回归／安装／自身模板证据后再做最终终核。R2可按最小范围清理并重新冻结。本报告是该准确patch的源码独立审查，不能转授后继修改。


## 同 slice r2 最小修订复核

2026-11-16。仍由同一独立 reviewer 只读复核，唯一写入本报告；未运行测试／probe／安装或修改产品。此节更新本 slice 当前结论，保留上文原r1身份与原失败，不覆盖它们。

|轴／范围|r2结论|开放项|
|---|---|---|
|新增认证／原最后准入接线，限定源码|**approve**|未发现新增阻断性算法／接线finding；schema3效果仍关闭|
|结构／维护性，限定源码|**approve，R2已关闭**|所审范围开放维护性finding 0|
|完整M5需求／验收|**pending／未通过**|R1 whole-hook SDK-free mandatory仍未满足；独立隔离设计通过不等于实施／验收|

### r2准确身份

基线和分支不变。新全10文件patch `.ergora/checks/cycle-predecessor-native-gates/m5-g-source-r2.patch` 为78,823B，SHA256 **`47669d3b99614ca0f41a3f03161a50cb3dcbb1f861d50ed7ede718263879bfd0`**；本次实际 `git diff <baseline>` 完整字节SHA同一。`source-freeze-r2.json` SHA256为 `44aad07c0d79ce95f4330b462343ef9fb68bfa23bde8fb36e811a164588a0072`；`frozen-inputs-r2.json` 为 `a03556bb4fb04095cdd63ce4059b9e84b1e00a5f6d71a7e93673f50653e56c6c`。10项source-freeze与665项输入的raw hash／bytes逐项核对，全相同；25＋4来源集合保持。

相对r1只两项raw变化，其余8个变更文件保持上表值：

|文件|r2 raw SHA256|bytes|
|---|---|---:|
|`src/ergora/reference_training_worker.py`|`babeb0f1db0032bba117ff548dd072de799d6916e0c0c5bb08ad57fe92b484ab`|145713|
|`tests/test_training_submission.py`|`369dd09ba7c46eb8fb87347495340578567af897e470cc9e2f09132c15fa0a77`|242537|

已对比r1／r2完整patch。worker仅删 `_round_local_gate` 原第1085–1086行的旧注释和重复 `reference.verify()`；原第1082行 `validate_sources` 仍在共享owner第961行完整核ROOT，measurement比较、registration以及末尾clock／active／stop均保留。没有减少不同责任边界的来源检查，没有改25表／四项／283／descriptor／native patch。**R2按最小修正关闭。**

### 原失败定位与测试oracle修正

原 `frozen-source-01.log` 现已终态：**37 passed，1 failed／639.04s**，失败为 `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync` 原第2977行 `KeyError: ref`。上文“尚无终态”是初审时快照，本节以实际终态补录；不能把原批称作全通过。

已直接读取原固定 operation `3a730bd8bf2a4272bfa3f6801b06cea8` 的 `request.json`／`helper/stdout.txt`、原alpha attempt、fault marker和 `service.json`，并与 `frozen-source-01-failure-diagnosis.json` 对照：

- H原stdout为103B，raw SHA `ff5e3f7cc73c289b92b076431bbe23b75cbb86eb0fdb595244a933ca16b0e75d`，完整JSON为 `status=unknown`、`reason=Original candidate activity context differs from its prepare source`；不是泛化超时或猜测的execution错误。
- 该原dispatch request的bootstrap为 started_ns=`2811949691556699`、deadline_ns=`2811956691556699`，恰为原7秒。marker进程start_ticks=`281195546`，对应约5.77秒位置；原alpha attempt实际存在。service原件为 starts=0，calls仅一次describe。
- 未改fixture `training_cycle_operations.py:389` 先调用原同步函数，确认attempt存在后才改原prepare request的 `activity_context.activity_source.activity_id` 为 `foreign-source` 并记marker。真实submission同步后最终 gate仍经 `BudgetedStart.dispatch_remaining/_start_remaining → cycle_start_source`，其第843–844行精确拒绝不相等的原activity_context。这证明 fault在attempt同步后到达来源校验，既未提前伪造rejection，也未send。
- 父 `_CycleOperation._run` 第257–270行只有两完整frames、无解析问题且最终仍在窗口内才接纳 `_stdout_ref`；否则返回透明unknown，不必有result.ref。原H诊断保留下来不能据此升级成父已接纳ref／durability证明。

r2只将该测试第2978–2979行改为沿本次返回的已知dispatch operation_id，读取固定 `helper/stdout.txt`，不扫描latest、不换原operation，也不重写产品结果。第2981–2983行仍要求明确source拒绝、原attempt存在、SDK starts=0。没有修改7秒配置、原bootstrap、S/H／同步fault或任何业务gate；未删除独特的最后source风险保护。固定路径读取在此仅作为保留诊断的证据，注释也明确它可以没有accepted parent stdout ref。该oracle修正符合原unknown合同，静态复核通过。

### r2验证证据与剩余范围

本次只读 `frozen-source-r2-affected.log` 已见明确终态：**10 passed／194.00s**。这是实施owner运行的本次受影响检查，不是reviewer自行重跑；本次已核运行所用r2源码／665输入身份。原37项通过保留首冻各自范围，不冒充r2全38项重跑。新日志不能消除原KeyError历史；它只补证本次最小修订的受影响范围。

r2仍未提供可由本报告认证的新非editable包／实际site-packages行为、自身原结构模板和完整最终收尾证据；准备中不算完成。依赖隔离片虽已报告静态设计通过，但未实施，故R1保留开放，whole-hook禁SDK原失败依然有效。schema3正向共享permit／所有action及更晚持久阶段、完整M1c／正式V2／真实两新候选CPU结果继续归M6。当前限定两轴approve不授权移除schema3关闭分支，也不是完整M5验收通过。


## r2后续独立核实：R3 · P1 · callback最后准入未复核所选解释器可用性

本次收到Ergora自身原 `refactoring-quality → ergora-structure-review@1.0.0` 的新增finding后，独立只读重沿真实调用与原需求核实；未照搬模型结论作为证明，未运行tests／probe／安装，也未重启实施owner占有的installed检查。原模型结果保存在 `.ergora/checks/cycle-predecessor-native-gates/self-review-r2-codex/review.md`／`summary.json`；summary记录Codex64.043s、request-changes、18完整文件879,039B、3份ancestor resource、stdin964,086B。上述是该原记录的范围，不将模型文本审查等同真实反例。

### 当前两轴及开放项

|轴／范围|更新结论|开放项|
|---|---|---|
|r2需求源码／原最后准入|**request-changes**|R3／P1成立；此前限定approve漏检了该迟到资源失效路径，不能继续用作最终批准|
|r2结构／维护性|**approve，限定已审结构**|R2仍关闭；R3需在原共享source owner做最小修正，尚未审r3|
|完整M5验收|**pending／未通过**|R1 whole-hook无SDK mandatory与R3均开放|

### 源码证据、可达序列与后果

**位置：** r2 `training_execution_protocol.py:1711` 的callback `active()` 在每个阶段重载并调用 `validate_context → validate_sources:954`。该 source validator只核gate sources、ROOT、所选installation的manifest文件和descriptor，不检查 `capability['native_python']`。`reference.py:117–129` 的 `_validate_installation_files` 遍历的是manifest中的platform来源，并不覆盖 `.venv/bin/python`。`owner_record:911–913` 只将该字段绑定到原installation的准确路径；`native_main:1678–1681` 仅比较已运行解释器的 `sys.prefix` 与core路径常量。

较早的 `reference_training_execution.py:64–65` 确有 `Path(capability['native_python']).is_file()` 检查，但它在原request／launch阶段的 `Execution.current`，不能保护后来的native attempt／ack同步后变化。原设计第81行及wire的来源表明确要求所选native interpreter身份／准入保持；没有依据把这一原检查从最后source边界豁免。

**可达序列：** 正常通过较早解释器检查并启动真实native进程；在原 `publish(attempt)` 或 `publish(ack)` 同步后的既有pause缝隙暂时移走所选venv解释器入口；释放pause。Linux上已运行的解释器进程不因该路径被移走而自动停止，内存中的 `sys.prefix` 和core.PYTHON路径也不改变。当前 `active()` 因未查路径可用性而可继续通过，返回executor。

这不是只会在无副作用的普通启动时报出的冗余参数错误。原admission-v1 patch在executor锁内callback返回后继续执行；未改executor原第66行先写 `started.json`，第68行起可clone／worktree，第81行才调用Sandbox。`sandbox.py:59` 之后才会再次使用 `PYTHON` 路径 `Popen` 原process_job，届时解释器缺失虽可使后续执行失败，却已越过了应拒绝的started／仓库副作用边界。缺失在先前动作后、最终同步后发生，恰是本片保护的迟到资源失效。

**后果：** callback来源／时钟／stop重读不完整，已不可用的所选native运行资源仍可能得到started。schema2真实callback已经可达，不必等M6才是风险；schema3当前早关不能消除它。本次仅根据源码证明可达，实施owner正在原pause缝隙构造真实红例；红例尚未提供，本报告不虚构其运行结果。

### 真正最小owner与修正／验证要求

把 `Execution.current` 现有的**所选解释器可用性准入**移入 `training_execution_protocol.validate_sources`，使同一原source owner在budget/context/native callback各真实最后边界重新核它；随后移除current中的重复检查。该函数本来已拥有installation／descriptor这一完整capability对应的当前资源，适合统一隐藏检查义务。原owner_record的准确路径绑定继续保留，无需新模块、wrapper、来源白名单、解释器hash格式、capability版本或新开关。

维持原 `.is_file()` 支持语义和有效venv入口，不凭本finding新增禁止venv正常symlink的合同。它保护的是最后同步后已消失／不可解析为文件的原入口，不宣称防止任意同用户敌对原子替换或给解释器二进制新增raw pin。较早producer的命令构造／可用性检查若负责不同动作仍按真实边界评估，不无差别删除。

沿现有真正 `publish` pause测试追加最小故障：attempt或ack同步后移走原解释器，确认修前确实越过callback并写started，保留完整红例；修后在同一位置拒绝、没有started／runner，新写attempt与阶段允许的ack及真实reap记录保持。恢复同一入口仅为测试资源收尾，不恢复执行权、不重发。共享validator修正还需原相关旧schema1/2与source正例确认可用入口继续被接受，不为每个helper重复矩阵。

r2完整patch身份此前已核；本reviewer未改source／test。收尾重核时六产品源码仍与r2相同，仅 `tests/test_training_submission.py` 已因实施owner准备红例而不同于r2；该开发测试没有r3 freeze，本报告未审其开发差异。新r3尚未提交本reviewer核实，故不能认证“已修复”或以准备中的新包替代r2开放finding。R1依赖隔离设计静态通过仍不等于整条hook无SDK已经实施／通过，两项必须分别闭合。


## r3修复／r4测试出生配置：同 slice 实证复核

本次仍只读源码／冻结原件，不运行tests、安装、服务或probe，不修改产品／测试。下述红绿测试均由实施owner执行，本reviewer读取其原件并独立核行为。R1依赖隔离在另一tree实施，不属于本M5 patch，未继承该片结果。

### 准确身份与两轴结论

r3完整patch `.ergora/checks/cycle-predecessor-native-gates/m5-g-source-r3.patch` 80,907B，SHA256 **`41fcda7acf74b6600f4dbf1a56aa1fa1a19c1c55300156c32b01233b42bed2be`**；source-freeze-r3 SHA `1b5c4f03e2ef72ab97cceae38509b4ecae03671e586c7232ce53afb0ab1d6a7a`，frozen-inputs-r3 SHA `fe44aa003752a2a42b534b0c52f2e43567de8f609360f244536d53202c46cc2f`。复核起点实际diff完整SHA、10文件及665输入raw hash／bytes均同一。

r2→r3单独delta `m5-g-r2-to-r3.patch` SHA **`aab2b4f87788935b3d59c30a3503320d9693e81de3b635c8777d7e3a65cf0068`**，只将原Execution.current的is_file两行移入共享validate_sources末尾，并扩原native publication测试的ack/interpreter一项。新值为 execution `e4246453bbcfdd15157150ff2ececdcf591a23e7027bd0d5af808e9554a0168b`／12,055B，protocol `50283fbcc2506cee1c82b62b7e43534571ea2f6cefbec49a076353823440952e`／115,796B，test_submission `2d96be9a3ffba9b1743dd92ada31d23277abe13d72143e434a8eec72abdf27c4`／243,745B；其余冻结值沿r2。

复核期间r4准确原件已形成，故也核了实际r4而非只审提议：完整patch `m5-g-source-r4.patch` 为81,431B，SHA256 **`141448e6cb9eb169e06f5722bda64e462690680d654b2e62c76029b59cd404a3`**；source-freeze-r4 SHA `5ea94ea6e9c56395ab35bdfc158407c156b95088795fa1858f62c4d1eb97ba0a`，frozen-inputs-r4 SHA与r3相同（665项产品／pyproject输入，不含本次改动测试）。r4十文件／665输入均逐项核同一；相对r3只有 `tests/test_training_submission.py` 新增一个decorator，raw SHA `6b1561acf029a19762450a2381ee8c86f8ab7404af399a8f09b6acb744eb9a32`／243,844B，六产品字节与r3相同。

|范围|本次结论|开放finding|
|---|---|---|
|准确r3产品／r4源码需求接线|**approve，限定源码及下述原件**|R3实证关闭；本范围无新增阻断finding|
|准确r4结构／维护性|**approve**|R2保持关闭；R3在原共享owner最小处理，未增重复检查|
|完整M5验收|**pending／未通过**|R1 whole-hook无SDK mandatory仍开放；准确新产品自己的安装／模板／最终收尾仍需另核|

### R3修复必要性与真实红绿

r3没有增加新的限制种类：原先 `Execution.current` 的“原所选native interpreter须is_file”准入被迁到 `validate_sources` 第968行，保留原错误与venv symlink语义，删掉原current的重复。由于 `validate_context`／callback每次active都到共享validator，这一检查现在在attempt及ack的publish同步后实际可达；source／ROOT／descriptor的既有检查及最后stop／clock顺序保持。没有新增source键、native版本或解释器raw pin，不把“路径文件可用”扩大成二进制不可替换承诺。该guard保护的可达失败已由下述红例实证，不是重复普通启动异常。

**修前红例：** `interpreter-red-r2-02.log` 终态 **1 failed，3 deselected／25.44s**。同时直接重算该case实际复制package的六产品文件，与source-freeze-r2全部相同，原件确认使用r2产品。原测试在ack已真实发布的pause点rename所选 `.venv/bin/python`，释放pause后等待原attempt中executor的完整进程身份不再活跃，再restore；不是在callback继续前就恢复入口。修前断言失败于 `started.json` 已存在。直接读取原launch/attempt/ack/stopped、started与result确认：started存在，result为FAILED，detail准确为该fixture缺少 `config/platform.json`。**这证明callback错误放行并写started；不证明因missingPython发生spawn失败，也不证明执行了真实训练。** 原始红例与diagnosis完整保留。

**修后绿例：** `frozen-source-r3-affected.log` 为 **7 passed／138.75s**，4个函数包含native4参数化节点、原writer锁、offline history和collect。直接沿解释器case原launch的execution_phase_id `9c25f901c4794bd8b6631fa1c7f4e757` 定位原helper/stderr，含 `Original native interpreter is unavailable`，stderr raw SHA `56553048f02a729e6fe5b28c8eeb638e4382fc9187cbf9c9fb0d1b40f6e5c329`。该case没有started／result，原request／launch／attempt／ack／真实stopped均保留，故观察到的是同一ack后最后gate的拒绝，不是更早启动失败。其他source／ROOT／clock节点的阶段保留关系也未被解释器故障替代。

测试只在现有真实publication pause增加一个故障值，保留真实callback／锁／S-H／reaper；沿原launch phase-ID读stderr，等真实native退出才restore，finally负责同一测试入口收尾。无需另建fixture／新矩阵。结合准确delta与同缝隙修前／修后原件，**R3关闭**，此前r2需求request-changes按修复证据更新为上述r3/r4限定approve。

`source-r3-integrity-and-identities.json` 原记录10文件／665一致，captured137、live_matches空、unknown空；本reviewer只核其摘要及源码身份，没有新查询／终止进程，不能将该时间点收尾结果说成之后所有新包运行也已收尾。

### r4普通source-sync测试：出生前配置，非途中续预算

先保留准确原安装失败：`package-r2/installed-main-r2.stdout` 为 **37 passed，1 failed／843.49s**；失败于原source-sync测试的fault marker尚不存在。这和首冻源码批次的KeyError: ref是两次不同失败。读 `installed-r2-dispatch-diagnosis.json`：原prepare与confirm共享一个7秒bootstrap，confirm H有owner_confirmed，而没有dispatch request、alpha attempt、service记录或fault marker；下一次inspect开始在原deadline后约0.077秒。因此该原安装case没有到最终同步source门，不能用来证明其通过。该case没有持久父accepted frames／inline return，不能据H stdout或整秒mtime猜测具体哪帧或哪一次最后检查耗尽。

实际r4仅对这个**普通故障注入测试**增加原有indirect `controller_admission={control_timeout_seconds:30}` 参数。已核 `controller_admission:738–745`：先从request.param取值、更新selection预算，第743行才create、第744行才authorize；参数在原plan/input SHA／authorization／bootstrap出生前生效。默认cycle_selection的7秒、wall／cleanup及产品代码均不改，原超时反例不改。原相邻execution-sync已有同类配置，不新建时间豁免逻辑。它给普通source故障路径选用有效配置，使测试能到它所保护的晚门禁；不延长现存run、不重开clock，不把错误消失当业务修复。

本次实际 `frozen-source-r4-dispatch.log` **1 passed／27.36s**。直接读三份已知原request：prepare `0e28c06bc47941249fa2ce2f7583ddab`、confirm `b4a530ce0c91409080fcd71bf5657431`、dispatch `32a8431ed0f94605bfe533ea42dda880` 的bootstrap完全相同：started_ns=`2814112552064284`、deadline_ns=`2814142552064284`，恰为同一个连续30秒窗口。原alpha attempt与fault marker均存在；dispatch固定H stdout仍为原103B source拒绝JSON，raw SHA `ff5e3f7cc73c289b92b076431bbe23b75cbb86eb0fdb595244a933ca16b0e75d`；service为starts=0、仅describe。这是晚source门被实际触发的证据，未靠加新deadline、改clock或跳过故障达成。**该r4单项配置与验证适当，所审范围无finding。**

不要求无变化的38／10／7组重复全跑；各原候选结果按准确身份保留。r4只改变测试出生参数，r3产品需自己的新非editable安装与后续模板／最终终核证据；r2安装37项通过不转授r3产品，r4源码单项也不冒称安装已通过。完整R1、schema3正向effects、M6／完整M1c／真实两新候选结果依然未由本报告认证。
