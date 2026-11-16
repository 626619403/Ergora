# c1d M5-G 前驱与最后准入：独立源码审查

2026-11-16。审查者：fresh-context reviewer `m5_predecessor_source_review`。按 `maintainable-project-delivery` 的 independent-review 和 `ergora-codebase-quality` 的 module-design／test-seams／repository-style 审查。未参与实现；本次仅只读源码、冻结输入和既有证据，唯一写入为本报告。未启动 tests、probes、模型、服务、安装，未改 source／test／PLAN，未 commit／push。

> 当前结论：准确r7冻结源码的需求／结构两轴均为 scoped approve；R6已由真实r6红例、r7末端完整intent重读和准确source绿色关闭，R2／R3／R4／R5保持关闭。R1 whole-hook mandatory仍开放，完整M5未通过；新r7安装／自身模板／最终验收未由本次源码报告认证。历史request-changes与原始失败保留于下文。

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


## r4后续独立核实：最后parent读取与前驱认证的两个晚阻塞窗口

实际自身模板结果为 `self-review-r4b-codex/review.md`／`summary.json`：Codex86.323s、request-changes，18文件880,313B，3份ancestor，stdin967,968B，stdin SHA `7e7811f75dd8e2c566d812afc7efb9ba4daf0b5a826fa323d414bf7ff17d19b7`，result SHA `5b13d19484086564a509c7c99c8d2e8c94aa997763432332db944b8aa0e8aea3`。这是实际模型文本审查记录；此前r4配置路径替换错误的setup-error／failed目录保留，模型未启动，不能当作另一模型结论。

本reviewer独立沿源码、真实caller和预算合同静态核实以下两项，不运行tests／probe，不把模型结论代替证据。检查时六产品文件仍与准确r4相同；原publication fixture和submission测试已有实施owner准备红例的开发差异，尚无新r5 freeze，本节不认证这些开发测试或其运行结果。

|范围／轴|更新结论|开放项|
|---|---|---|
|准确r4需求源码／最后准入|**request-changes**|R4、R5两项P1静态成立，真实红例／修后证据待提供|
|已审共享owner与模块结构|**approve，限定结构**|R2／R3保持关闭；新修复须仍由原owner最小处理|
|完整M5|**pending／未通过**|R1 whole-hook mandatory与R4／R5开放；另一tree依赖隔离源码审查不转授本片|

### R4 · P1 · native最后parent读可能在clock采样后阻塞

**位置与实际caller：** r4 `training_execution_protocol.py:1713` 的native callback `active` 先重载记录／validate_context，第1719–1723行的完整条件按fence、live owner、`budget_clock.remaining(original clock, wall, cleanup)` 顺序检查；第1724–1725行才 `parent.check()`。ack第1736行publish后，最后active返回就会把控制交回原executor。`CycleAdmission.check:1047` 调用 `_authorization`（第1024行 `read_raw(authorization.json)`）后仅查stop路径；它**没有**work或operation时间检查。更早 `validate_context` 内的clock采样也不能替代这次最后阻塞读取返回后的采样。

**可达序列与后果：** schema2真实native仍持原executor锁和父共享permit，在ack同步后的最后active采样work>0，随后parent.check的原authorization读取阻塞，直到work耗尽才返回；授权原字节和stop均未改变，所以parent.check仍可通过。当前代码没有第二个晚clock采样，callback可返回并让executor写started／后续动作。锁和共享permit约束并发／排空，不冻结clock，也不隐含延长原work。此前clock故障节点在publish同步后、进入active前使clock异常，不能保护这个在active末尾parent读中才耗尽的窗口。

**最小修正与必要验证：** 在同一native.active内把原完整fence／owner／remaining条件移到最后parent.check之后，使剩余work采样成为这些原本地读取之后的最后准入；不再添加第二套clock或放宽window，不依赖异步取消。仍沿同一原BOOT／UTC／cleanup语义。现有ack同步pause加只匹配此active→parent.check的真实authorization读取暂停；读返回时同时前移native局部BOOT／UTC到work已过而total／cleanup仍在，使用原 `remaining` 算法。应保留修前实际started等越界证据，修后要求原ack保留、没有started／runner。当前只静态确认可达，作者真红例尚未提供，故不伪称已复现或已修复。

### R5 · P1 · 最后SDK／索引／local gate之后没有完整前驱重读

**位置与实际caller：** r4 `reference_training_worker.py:1281` 在当前round的完整observation已同步／读回后调用 `_round_previous` 并核report binding；随后第1282行 `_round_gate` 还会在第1120行进行SDK父describe/history观察。返回后第1284行只读取**当前round**的index，第1286行 `_round_local_gate` 只核当前plan／ready／项目revision、intent／owner、sources／ROOT、registration／clock／stop，完全没有调用 `authenticate_cycle_candidate` 或重读此前各round index／observation／execution／evidence库存。没有其他暗含的caller在这段里补全链核验。

**可达序列与后果：** k=1当前round1 observation已同步，round0原件刚认证完；最终parent SDK describe阻塞时给固定round0 `rounds.json` 追加LF，JSON语义不变，但原predecessor pin的raw SHA／bytes已不符。SDK正常返回、当前round1 index和所有source保持，后两个当前gate不会读取round0，于是旧accepted投影可能仍给 `continuation_ready=True`。原前驱当时accepted不能豁免晚gate对当前原字节的要求；后继即使稍后再拒绝，也不能把此当前acceptance当作已完成认证。本次静态可达判断成立，真实case待作者原件确认，不声称当前已有运行中的true结果。

**最小owner与修复边界：** 继续由现有protocol共享认证算法负责完整本地原件，H保留原archive语义和紧邻前轮SDK phase职责；调整最后认证顺序，使真正的**共享纯本地全链认证**位于后续外部阻塞观察之后，移除被替代的旧位置，不复制parser／ledger或增加跨动作“已认证”缓存。

不能只机械把整个 `_round_previous` 调用搬到函数末尾就假设所有晚阻塞已闭合：该函数自身第1180行先调用 `authenticate_cycle_candidate`，之后第1189行还读archive，第1195行还查询紧邻前轮SDK。单纯挪wrapper仍会在其内部的SDK等待之后留下未经重读的早轮原件。修复应明确纯认证与H额外观察的实际先后；保留有独立作用的真实边界，避免为满足顺序无理由重复完整链遍历。局部逐文件读取仍不是抗敌对同用户并发改写的原子快照，但不能因此忽略此明确在认证之后的外部等待缝隙。

在现有k1真实H fixture的“当前observation已落盘→final parent describe”缝隙改原round0 raw，仅追加LF且不改当前round1 index／observation，保留修前完整stdout／continuation投影及修后拒绝、原件和原机会不回收的证据。还需静态追踪最后共享认证之后是否仍有SDK／archive外部阻塞；仅证明一个fault被新顺序捕捉不足以掩盖同类被搬到内部的等待。无需扩展为每个helper重复矩阵。

截至本节：R2／R3此前修复的准确证据继续有效，R4／R5新发现使r4先前限定需求approve失效；新r5尚未送本reviewer核对。R1依赖隔离另一tree的11文件源码和另一fresh审查状态，与本M5晚gate修复、其新非editable包及whole-hook实际验收分别记账。


### R5重排方案追加复核：保留末次H的当前phase语义

本次继续只读真实workflow／runtime／four-fact predicate，结论是：**不能仅以较早一次H观察替代原末次H并宣称行为不变。** 当前所提“保留初始／中间 `_round_previous`，删除原final H，只在末端做纯认证”会删去一个有独立可达意义的晚phase观察；在正式r5冻结前应调整。

真实原workflow支持在accepted观察之后取消：`perf_temporal/workflow.py:57–62` 的request_cancel设置cancel_reason；第144行处于AWAITING_RELEASE时，第158行可进入cancel_and_confirm；第80行置CANCELLING，第91–95行即使原job仍SUCCEEDED也将Workflow转为CANCELLED并返回取消Outcome。native已停止、原evidence／archive文件保持稳定不能阻止这个合法控制面变化。`reference_training_runtime.observe:182–199` 会返回新的Status／Outcome；protocol.round_state只将RUNNING/AWAITING_RELEASE或COMPLETED/RELEASE_EXPIRED、INTEGRATION_TASK_CREATED的原合法绑定判为accepted，CANCELLING／CANCELLED不满足并返回unknown。因此，在中间H后、原末次H前发生该变化，r4原末次H可拒绝，而拟议删除版本只验证冻结历史value可能放过。原设计第63行明确H对紧邻前轮核当前可接受phase，native纯认证不承担SDK状态观察，这个职责不能顺手删除。

较小且保守的可审重排是：保留初始H（before create）与原末次H的archive／紧邻phase观察，末次H之后的final parent SDK／当前index／local gate返回后，再执行共享纯本地全链认证；中间same-fd同步后的round_report_binding使用此前已认证的previous，不重复整段H。这样仍保留same-fd／同raw／当前prefix校验和首末phase观察，完整纯遍历可保持三次；没有复制算法。中间没有向外释放acceptance，末次H或最后纯认证失败仍拒绝continuation并保留已出版原件，所以移除中间重复H有具体边界理由。

这只是依真实调用给出的最小结构处置，不是r5实现批准。若实际新diff发现中间H还有上述检查未覆盖的独立义务，应保留该义务，允许有理由的额外末端纯认证，不为维持计数删掉末次H。新顺序也只能声明观察到的合法采样和最终本地身份复核，不能声称SDK状态与本地文件形成跨系统原子快照。R5仍开放，待准确新patch、旧末次phase回归保护和原晚raw漂移红绿证据后复核。


## 准确r6：R4／R5修复实证终核（源码范围）

仍为同一slice独立reviewer，仅只读冻结源码、原红绿结果及固定Git身份，唯一写入本报告；未运行tests、probe、安装、模型或服务，未改代码／测试／PLAN，未commit／push。r5是探索候选，其worker曾删除末次H，不能作为最终产品通过；r6恢复全部原H调用后重新冻结并验证。

### 当前两轴与完整验收状态

|范围|结论|开放finding／缺证|
|---|---|---|
|准确r6源码需求／前驱与最后准入接线|**approve，限定源码和下述证据**|R2／R3／R4／R5关闭；本范围未发现其他阻断finding|
|准确r6结构／维护性|**approve**|末端额外纯认证有真实独立晚边界作用，未以计数删末次H，无新wrapper／ledger|
|完整M5／whole native hook|**pending／未通过**|R1 whole-hook无SDK mandatory仍开放；新准确包的安装／自身模板／最终验收分别待核|

本结论不开放schema3 effects，不把另一source-v2依赖隔离tree的源码审查视作本片whole-hook验收。M6／全部M1c／真实两新候选CPU／质量或GPU仍不在本次通过范围。

### 冻结、固定提交与复核范围

r6完整patch `.ergora/checks/cycle-predecessor-native-gates/m5-g-source-r6.patch` 为89,837B，SHA256 **`3a56cf9952e4acd1616787bcaed616b3c5b593b2e7dfd683e700e3261e5aca1c`**；source-freeze-r6 SHA **`88a423b0f7dc2bc00e7773a67f1f73a38ccdc62f341666a3ddd4bc20bf2de459`**；frozen-inputs-r6 SHA **`e88af9b3a21298945bad2180b7346f8d22dfb32402bfccc2dd839538ef8b857c`**。实际实施tree相对原baseline `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3` 的完整diff逐字SHA相同；11项source-freeze raw hash／bytes和665项输入全部重算相同。新增的第11个变更是既有 `tests/fixtures/training_cycle_operations.py`，没有新文件／模块或CI分组。

完整审阅r4→r6 delta `m5-g-r4-to-r6.patch`，SHA **`0c0c5a789bed01e6adf572e53857cec5f897215a2a3a8be8c2f4bf8ba513a9ee`**。相对r4两产品变化仅protocol的原clock条件顺序与worker最后三行共享认证；其余增量是两个已有fixture和既有submission测试的真实边界故障值／断言。当前重要raw值：

|文件|r6 SHA256|bytes|
|---|---|---:|
|`src/ergora/reference_training_worker.py`|`885c14055851fd1ea34cd37d5afad04b0aa0f44edd12be7edc0c4592516aecd9`|145975|
|`src/ergora/training_execution_protocol.py`|`32736ca4720cc5c39cebb04ab3f29384778fd67e879a2eae6b3794888ef04138`|115879|
|`tests/fixtures/training_controller_pause.py`|`dd9fe1632464c90c2636b299d663d791d0c78ce7bbf976a9aabf7c4b2c0a4760`|3742|
|`tests/fixtures/training_cycle_operations.py`|`99bb3e2682b2ba08dd3be99e3293ac414e85200c3cebc515421022b78b1b3948`|27837|
|`tests/test_training_submission.py`|`e262c2d25917a292661c94bbf6edfca66f981d2fdc91b1682fbd965e5d70ed2e`|245122|

另直接核根固定tree `.ergora/worktrees/training-cycle-predecessor-gates-fixed-r2` 当前分支 `feat/training-cycle-predecessor-gates-fixed-r6`：HEAD **`f6722141cfa9ed885993360161c004e47e8df3a5`**，父 `68f3241695f5de1fdc188609db612c1d30434edf`，working tree干净；`git diff <原baseline> <该HEAD>` 的完整字节SHA仍等r6 patch。只是固定源码身份，不表示合并／发布／CI／安装通过。

### 两条r4真红例

原 `frozen-source-r4-order-red.log`：**2 failed，7 deselected／41.63s**，失败分别为ack-parent-work和round-final-parent-predecessor。原diagnosis／marker／request／stdout／native记录保留；还直接重算native case的复制package六产品hash，全等r4，未用修后代码冒充修前红例。

**R4红例：** fault仅在真实 `read_raw(authorization.json)` 已读原字节、即将返回时，经调用栈严格限定为native.active→parent.check且ack已存在，暂停并同步平移该native子进程的BOOT／UTC。没有替换 `remaining()` 返回值或原授权。原`.clock`采样显示同一boot，work_remaining=`-1.0063169999999673`、total_remaining=`168.99365`；原attempt／ack／stopped存在，却实际写started和FAILED result。FAILED detail准确为原fixture缺 `config/platform.json`，不是宣称真实训练或缺解释器spawn失败。该红例证明work耗尽之后callback仍越过started边界。

**R5红例：** k1当前observation落盘后，原final parent SDK describe在返回前暂停；只给round0 index追加LF，当前round1 index／observation字节不变。固定collect operation `2aaf7da25a6e4319a007a91cc39d0e7a` 的原完整H stdout仍为observed、measurement accepted／durable、`continuation_ready=True`且有完整acceptance，operation已stop／supervisor0。这是早轮raw pin已失效仍释放acceptance的真实证据；不是只看到一个私有helper未raise。

### R4修复与对应绿色：关闭

r6 `training_execution_protocol.py:1719` 先执行原parent.check，再于第1722–1726行执行同一个完整fence／owner／BOOT-UTC work condition。没有新clock、没有重复采样条件、没有调整wall／cleanup／window；原最后clock采样现在晚于parent授权读取和owner观察。

`frozen-source-r5-affected.log` 是探索批 **12 passed／212.38s**，其中native5节点认证的protocol／所有测试与fixture字节和r6完全相同；r5与r6唯一raw差异是worker，故这里只取native5的对应scope，不把其探索worker的通过转授r6。直接读其ack-parent-work case：work_remaining=`-1.0001569999999447`、total_remaining=`168.99981000000002`、同boot；ack／真实stopped保留，started／result均不存在；沿原launch phase `bbd270a398b24ebcbece18d75634a5e5` 的真实stderr含 `Original execution fence, owner or computation deadline forbids work`。这在与修前同一parent读返回边界观察到原完整时钟拒绝，**R4关闭**。其他source／ROOT／clock／interpreter节点仍各有原保护，不被此新节点替代。

### R5最终结构、对应绿色与额外遍历理由：关闭

r6保留原 `_round_previous` 的全部三次调用（首、same-fd同步后、当前observation后），因此原archive重新inspect与紧邻前轮当前phase检查均不减少；此前“删final H”的探索方案不进入最终产品。末次H内部的archive／SDK读取也已返回，随后final parent SDK、第1284行当前index读、第1286行local gate都返回后，才新增第1288行 `protocol.authenticate_cycle_candidate` 和第1289行report binding。末端使用原同一算法，重新从当前intent的完整predecessor回溯到0，核原raw pins／库存／来源；它不执行H额外SDK查询，所以不存在把旧外部等待藏进最后wrapper的问题。

该额外纯遍历与较早三次有不同责任：较早H保持真实采集／archive／phase与持久同步义务；末端纯认证关闭这些外部观察之后的本地早轮漂移窗口。原三个H均留时，新增这一遍是有证实故障边界的必要复核，不是R2那种相邻同输入无独立作用的重复ROOT调用。不新增模块或复制ledger／parser；实际I/O消费同一个不可续预算，未加时或缓存。

最后共享认证自身第1522–1525行active先 `admission.check` 读parent／stop，再调原完整work remaining；末尾第1613–1614行核完sources后再active。其后仅纯report binding／acceptance投影／shape校验，无SDK／archive外部等待。原父 `_CycleOperation._run:257–259` 在收到两完整frames、所有I/O任务成功且 `not self.expired()` 时才接纳结果；expired仍通过 `cycle_operation_remaining` 消费原 `min(operation window, original work)`，没有因最后纯读取／编码而跳过父最后时间门。这里依然不声称逐文件认证是抗同用户敌对替换的原子filesystem快照。

实际 `frozen-source-r6-affected.log`：**8 passed／138.86s**，准确4函数为最终blocking-read四节点、原internal collect/reconcile、k1／k3全链两节点、大reader一节点。直接读新故障case的固定operation `be50d5133f8c4d22945a27f901904a58`：原round1 index与observation仍保留，H返回unknown，reason为 `Previous round pin differs from its complete raw original index`，没有continuation／acceptance。这和修前仅追加最早轮LF后仍true的原例对应，**R5关闭**。原same-fd/source／stop／project负例、k1/k3与10MB reader维持此次准确worker范围的绿色。没有重复跑无变化的38／10／7组，也不把任何旧批次写成新r6全量通过。

### 未认证项

`source-r6-integrity-and-identities.json` 原收尾记录captured184、live_matches空／unknown空；本次只读该记录，不将它扩称所有之后安装／模型进程均已收尾。根新r6 core／SDK663文件包构建及身份核验在另一路，安装和自身模板仍准备／执行中；本源码报告不继承、不认证尚未提供的结果。准确r6需要自己的新安装及自身模板／最终终核，R1 whole-hook无SDK必须由独立依赖版本及真实hook证据闭合。当前结论仅为准确r6源码范围两轴approve，完整M5仍未通过。


## r6后续独立核实：R6 · P2 · 共享认证只核缓存，漏读当前实际intent

实际自身模板 `self-review-r6b-codex/review.md`／`summary.json` 记录Codex79.601s、request-changes，18文件858,633B、3份ancestor、stdin955,359B，stdin SHA `262d40104a2c0370bb8f8622f69f0b40ee2df6951eb0235d4455008b4436a5ec`，result SHA `60c5b39ef69c815689dd18ac012aba92a7415bb59ba28c7513effab5134d94cd`。本reviewer没有把模型意见直接当作finding证据；已独立逐点核以下共享代码及全部真实消费者。此次检查时11文件仍与source-freeze-r6相同，尚无新冻结候选；不运行test、probe或安装，唯一改本报告。

|范围／轴|当前结论|开放项|
|---|---|---|
|准确r6需求源码／完整持久身份认证|**request-changes**|R6/P2静态成立，属于可静默接受过期持久身份的正确性缺口；待真实反例与修复|
|已有owner／模块结构|**approve，限定结构**|R2／R3／R4／R5保持关闭；修正应留原共享算法|
|完整M5|**pending／未通过**|R1 whole-hook mandatory及R6开放，新安装通过不自动涵盖新风险|

### 独立源码证据与三个消费者

`training_execution_protocol.authenticate_cycle_candidate:1512` 构造 `current = ExecutionRecords(...)` 后，第1513行只读owner；`_round_candidate_intent:1431` 校验的是调用者传入的完整intent缓存。尾部第1609行重读owner、随后重读ready／cycle并核sources／clock，始终不读取当前 `<id>.intent.json`。`ExecutionRecords` 的构造本身不读取该文件，只有 `load:1304` 才以 `16 * LIMIT` 读取它；`document:1290` 只是对调用者指定路径执行safe raw read／decode，不会连带读取intent。因此不能把construct current或读owner误认为已经读过完整当前intent。

三个真实消费者也没有在此之后补齐：

- `BudgetedStart.source:259–266` 消费缓存 `self.intent`，schema3先调用共享认证，之前只重载plan／authorization／ready，没有重读当前实际intent。schema3effect随后关闭仍在，但不能称缓存正例认证了当前持久物。
- H的 `_round_previous:1175` 入口 `_cycle_target`／`operation.load` 较早读取intent；末端 `_round_operation:1288` 使用更早取得的 `intent` 缓存执行最后纯认证，之后只有纯binding／acceptance投影和父clock接纳，不再 `_cycle_target` 或load当前intent。当前actual intent在该长认证期间改变／缺失，owner及早轮完整链仍可保持，故可能发出acceptance。
- `validate_context:1618` 确实核 `context.intent == chain.intent`，其caller的 `ExecutionRecords.load` 较早读过actual file；但schema3第1639行长共享认证期间发生的变化，在认证返回前没有再次读取current intent。native未来消费也是同一问题；不能用schema2其他路径或schema3关闭效果否认H已经可达的只读接受风险。

例如k1当前轮observation落盘后，最后共享认证进入原大文件／source读取；这时移走当前candidate的actual `.intent.json` 或将其完整语义换成另一个operation身份，同时保留owner及传入缓存。当前代码只比owner.intent_sha与缓存sha，早轮库存与plan都可继续通过，当前实际文件未被访问。缺失与完整语义漂移是此finding；并非要求当前intent新增未约定的raw字节pin。本次为源码可达判断，实施owner正在准确r6构造真实红例，尚未提供运行结果，本报告不虚构已复现。

### unborn prepare与最小修正

unborn prepare是实际合同，不应因新增检查被误拒绝。`reference_training_budget.prepare_binding:47` 在 `_Submission.run:349` 构造binding时先调用 `BudgetedStart(...new intent...).require_active`，随后第355行才write当前 `.intent.json`；owner更晚才出生。这一前置本地认证必须允许owner和intent均不存在。另一个prepare同步后的第358行复核已面对现存intent；H末轮则必有既存capable owner。不能一律要求文件存在，也不能用一律optional吞掉已经出生文件的丢失。

最小修正在现有共享 `authenticate_cycle_candidate` 内，沿 `ExecutionRecords.document` 读取准确固定当前intent路径，显式使用原 `16 * LIMIT`（16 MiB）上限，以canonical `_match` 核完整实际值与调用者缓存。原owner已经存在时actual缺失须拒绝；无owner且文件也未出生时保留unborn路径。记录入口的存在性／完整语义，长前驱／来源读取结束后再次读回并比较，才能捕捉认证期间existing→missing／改义；只入口读一次不能关闭本次晚变化。存在性或既存owner提供必要本地状态，无需调用者可信的allow_missing／already_authenticated开关，也无需新文件／ledger／schema或独立wrapper。

当前intent原完整身份沿canonical SHA，读取合法JSON后比较完整语义即可；不要顺手引入当前文件raw pin或拒绝语义不变的空白重编码。前驱已接受observation的raw inventory／ref字节规则仍按各自原合同执行，不能因此被放宽。safe ordinary-file／symlink／duplicate-key边界和16MiB aggregate容量继续复用原reader；不扩为默认10MB，也不把合法大intent缩回1MiB。

最小真实验证应沿当前final纯认证的一处真实阻塞读改变当前actual intent，保持缓存／owner／早轮原件不变，修前保留错误acceptance，修后unknown无acceptance且不重建／修复文件；覆盖缺失与改义的有意义关系，并保留unborn prepare和合法现存16MiB语义边界。作者新installed13 passed／346.70s只认证该批原行为，未加入新风险保护时不能据其关闭R6。R1完整hook另树最终安装同样独立，当前准确r6不具备最终无开放风险批准。


## r7同片复审：当前实际intent完整重读，R6关闭

本次仍只读实施源码、固定提交和既有终态证据；未运行test／probe／安装／模型／服务，唯一写入为本报告。保留r6发现和红例，不以新绿色改写历史。r7没有扩大产品边界；原candidate绑定、出生身份／source pins、六阶段、锁／父许可、attempt-before-send与unknown只对账保持原合同，schema3 effects／M6仍关闭。

|范围／轴|准确r7结论|边界|
|---|---|---|
|共享全前驱／最后准入的需求源码|**approve，限定本节准确冻结**|R6关闭；R2／R3／R4／R5保持关闭，没有新增开放源码finding|
|已有owner／模块结构与维护性|**approve**|完整intent检查留在同一共享认证，复用原safe reader／canonical比较／16MiB容量，无新模块、ledger、schema或可信跳过开关|
|完整M5／whole native hook|**pending／未通过**|R1 mandatory仍开放；准确r7新安装／自身模板／最终整片验收须单独核实，本节不认证|

### 准确输入与固定身份

完整r7 patch `m5-g-source-r7.patch` 94,220B，SHA256 **`61e1e11fbbc582453b3afeba3d20786eb2347c279fea3b4969285c0121f3b017`**；`source-freeze-r7.json` SHA **`37a93c5e947e6cb24fb02c61302f4dd9c52f0b757d733e2c57b0df58d4452a77`**；`frozen-inputs-r7.json` SHA **`9dd92719f6542977f92f96c56641a2e6e6389595f7e851ad685c2ec10bdfafde`**。本reviewer逐项重算11个变更文件的raw bytes／SHA、665个product／pyproject输入的raw bytes／SHA与所列executable状态，全部相同。实际实施树相对原baseline `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3` 的完整diff字节与上述patch相同。

另直接读取固定树 `.ergora/worktrees/training-cycle-predecessor-gates-fixed-r2`：HEAD **`5bcecf37b615e3708ceb08acc329ba3dd0470f4a`**，父 `f6722141cfa9ed885993360161c004e47e8df3a5`，working tree干净；该HEAD相对同一baseline的完整diff亦为94,220B及同一r7 SHA。这仅固定源码，不代表已合并或完整验收。

完整审阅r6→r7 delta `m5-g-r6-to-r7.patch`，8,291B，SHA **`64250fa2be9d490fbd185a2a2455d4dba522bc625e74145dbd76a6054d47ff96`**。增量恰为三个既有文件，产品只有共享protocol的六行；其余为同一故障fixture和既有submission测试的边界断言。所有11项仍是既有文件，无新文件／模块／CI分组。

|r7增量文件|raw SHA256|bytes|
|---|---|---:|
|`src/ergora/training_execution_protocol.py`|`e16894b51d747b112d11dbc67afa5d6d4ee7a9fba5ac41884ff44661730f9976`|116336|
|`tests/fixtures/training_cycle_operations.py`|`76cc2450a311b0d2b62bca88526995b92279a0dfae9131741a502406c6f74a12`|28816|
|`tests/test_training_submission.py`|`9633abee4decca4b9f03ca6c203c868ab088e01cbfd7dd702c08a39912091629`|247363|

### r6真实红例与原H输出

`frozen-source-r6-current-intent-red.log` 为 **1 failed，4 deselected／18.09s**，runner returncode1／wall18.8076398503s；log raw SHA **`2c4225f2a653bd5abed5b8e65f646c55e3f2c2ac05ffcc5e563816c4a5d3f87e`**，result JSON SHA **`44faa752b35a76357537228fc377d9c19eaf5f0b34c746a7fc4868c5663c0c5f`**。原command明确使用 `source-freeze-r6.json` 产品，并仅把新红例输入加入原测试／fixture；保存的两份test-input raw SHA逐项与该command相同（submission `c2547fed…`，fixture `76cc2450…`），没有把r7修复产品称作r6红例。

故障在ordinal1当前observation已落盘，最后共享认证的当前owner末端重读返回前暂停。fixture沿真实 `protocol.read_raw` 读取原件，调用栈同时限定 `authenticate_cycle_candidate`、已有 `result` 和直接caller `_round_operation`，没有替换认证结果或原intent缓存。测试只将当前actual intent的完整JSON `operation_id` 改为另一个32位身份；当前index／observation、owner和早轮链不改。marker的raw SHA由 `20d6acc7e061e8d8f1b3602aa0967d20d1022dda0c76c02eea9c0245a80ec82e` 变为 `d1fda836cc06be246f917a5be267496d0670ccab2f01ab721a8a4a4266d3a80c`，不是仅追加空白。

直接读原operation `743b35e075ad4639bfb1172c2baed7eb` 的 `helper/stdout.txt` 和 `round-final-result`：H仍为observed，measurement有 `continuation_ready=True`、完整acceptance／prefix，父operation stopped=true／supervisor0；原断言是在确认当前index／observation原字节未变之后，因预期unknown却收到observed失败。该原输出证实R6是实际只读acceptance错误，不是仅凭私有helper推演，也不声称发生真实训练效果。测试finally恢复actual intent，原artifact中恢复后的SHA与marker before一致。

### 六行共享修复的源码判断

`authenticate_cycle_candidate:1513–1517` 读取当前owner后，以原固定 `.intent.json` 路径和 `ExecutionRecords.document(...limit=16 * LIMIT)` 读取actual intent；owner存在时不允许缺失。只要文件存在，完整canonical `_match` 必须与调用者原intent缓存相同，未只比较operation_id或另加raw pin。原 `decode:536` 强制顶层JSON object，因而optional缺失返回的None不会与文件内容JSON null混淆；原ordinary-file／NOFOLLOW／duplicate-key／容量规则继续生效。

第1618–1620行的再次读取放在长前驱遍历、owner／ready／cycle复核及最后 `_round_sources` 全部返回之后，紧邻原final active。尾读与入口actual完整值比较：入口既存则尾部不允许丢失，语义变化拒绝；入口无owner且actual也未出生时，尾部仍允许真实缺失，而期间新出现的任何完整object与None不同，保守拒绝。owner在认证期间出生也仍由原owner前后比较拒绝。不新增调用者可传的allow_missing开关，也不重建／修复持久文件。

unborn prepare在write intent和owner birth之前必须合法；本修复用现有本地存在性区分该阶段。合法现存intent追加LF仍按canonical值相同接纳，不把当前intent升级为raw字节pin。原前驱observation／inventory的raw pin没有因此放宽。末尾仍先完成identity读取，再进入原parent／work最后active；没有重置或续预算。r6保留的三次H archive／紧邻前轮phase读取及额外末端纯认证全部保持，R2–R5不重开。这里仍不把逐文件验证称为对抗同用户任意并发替换的原子快照。

### 准确r7 source绿色及其限制

`frozen-source-r7-affected-command.json` 指定准确实施tree、source-freeze-r7与上述665输入SHA，调用三个函数展开为四节点：新current-intent阻塞故障、扩展internal collect／reconcile、ordinal1／ordinal3完整早轮链。实际 `frozen-source-r7-affected.log` 为 **4 passed／69.57s**，runner returncode0／wall70.1858168598s；log SHA **`087cf012f878a1b2bb25f564e5866aef248289dfae38d3e6a0941cda1e5b8baa`**，result JSON SHA **`2e43a78053f8849404e442cda08c4e8e7bac17bc82f23b5dcacd15cd7a58bd31`**。

直接读新故障operation `93ade55e64314ec49278351390787bec` 的原H stdout：`status=unknown`，reason为 **`Complete original current candidate intent differs from its complete original identity`**。原父result没有measurement continuation／acceptance／prefix，仍stopped=true／supervisor0；测试已核原当前index和observation字节保持。marker从 `9ec28a5ed7c38f374d2b62e663d9312b2ec64c081453d518283acc2eaa91f38d` 变为 `db82090262071b8a203bd689d6d5e28647cf08f1f39d6fa927beed3a8cae4caa`，故障作用于同一实际intent晚漂移边界。finally恢复后actual SHA回到before。

扩展的既有internal测试先保留真实collect与reconcile，随后在现存owner下核actual intent追加LF通过、删除则FileNotFoundError，再原字节恢复；最后沿原 `_cycle_submission` 为ordinal1构造合法尚未出生的完整intent，回溯真实已接受round0，返回一个original且没有创建intent／owner。该测试直接覆盖缺失、canonical空白及unborn之间必要差异，没有假造verifier-pass或新增兼容开关。late existing→missing由尾部必读的同一代码路径静态核实；本节不虚构另跑过该故障。原16MiB限制在两处均明确保留；新四节点没有包含大reader，不写成r7重新跑过大reader或旧完整矩阵。

以上真实红绿及源码核对足以关闭本finding，**R6关闭，准确r7需求／结构两轴scoped approve**。本节未取得并核验准确r7新installed5／自身原模板／最终整片终态，不将r6安装13通过或旧模型模板结论转授r7。独立source-v2依赖隔离仍属另树；**R1 whole-hook SDK-free mandatory与完整M5继续pending／未通过**，不授予schema3正向effects／M6。
