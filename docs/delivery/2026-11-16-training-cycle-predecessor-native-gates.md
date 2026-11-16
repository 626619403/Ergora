# c1d M5-G：完整前驱与原最后准入实施

2026-11-16。状态：开始隔离源码实施前核定；尚无产品／测试／安装／模型或fresh实施验收。依据[已审设计](../plans/2026-11-16-training-cycle-predecessor-native-gates.md)及[独立设计审查](2026-11-16-training-cycle-predecessor-native-gates-design-review.md)，不开放schema3效果或ordinal1。

实施基线为固定父留存产品 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，其父为已验M2产品68ba793。父留存源码／新安装／自身模板已完成，根仍单独进行其最终整片独审；本片不把它的成绩转授新改动。隔离分支 `feat/training-cycle-predecessor-gates`，持久worktree为ignored `.ergora/worktrees/training-cycle-predecessor-gates`。

固定M2实际算法重核：report binding、four-fact判定、acceptance和previous编排仍在worker；当前没有原生第二caller，故不先单立M5-P或为复用落无人调用helper。M5-G接真实protocol／budget／Execution／native消费者时，同片迁移所需纯计算并删除重复，机械迁移和新认证按diff分块审。State／SDK／archive读取与publish编排留其原owner。

交付范围是完整前驱链、原25来源＋四measurement与ROOT／所选安装，以及原submission、registry、request／launch、native attempt／ack同步后的最后检查接线。保留明确schema3关闭分支；不得用新开关、伪source或信任参数启动新训练。正式V2／v3、全部M1c与实际两轮统一开放沿[已审M6设计](../plans/2026-11-16-training-cycle-v2-runtime.md)另片交付；M5的纯正例不能关闭尚不可达的实际effect正向验收。

检查复用原submission／runtime测试和operation fixtures，保留真实锁／fd／S-H／reaper与callback，按已审矩阵逐项注明可达及未到达边界。固定源码、新非editable包、原结构模板及新的fresh两轴实施审查各自记账；不新增CI job、放宽时限、复制archive reader／manifest walker、改283原件或新建账本／证明文件。具体变更、运行和未验项将按实际结果追加。

## 隔离实现进展：原件认证与首个完整局部正例

实施树准确基线仍为 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，开始时干净。重核固定 M2：原 report binding／state／acceptance／pin／selection 只有 worker 调用；随新的 protocol 本地认证真实消费者同片迁移，没有预先 M5-P。共同约束常量由原 `training_cycles._COMMON` 移至 protocol，原 owner 直接引用同一常量；State、SDK、archive、publish 编排保持原 owner。机械迁移 patch 单独保存在 ignored `.ergora/checks/cycle-predecessor-native-gates/01-pure-migration.patch`，最终新增认证 diff 另记。

新增本地认证已经接入 BudgetedStart.source、validate_context、H 前驱读取；prepare 增加 intent 同步后 source 复核，Execution.current 重读完整当前链，native callback 在入场、attempt 同步后、ack 同步后重读并仅接受本次对应阶段的 records。来源复用原25键集／owner出生 pin、四 measurement 出生值和 reference.verify，未增加第二 archive comparator 或白名单。源码仍开发中，尚未冻结或独审。

首轮探索 `exploratory-01.log` 为2失败／1通过，失败原因是机械替换误改一处 `validate_round_acceptance` 调用名，已定位修正；原 native 锁接缝通过。随后独立新目录 `exploratory-02.log`：**3 passed／55.20s**，原 M2 collect/reconcile、k1 和 k3 全链认证及最早 index 原 raw 漂移拒绝通过。k3 实际读取3份原前驱，正例后 Budget.source 仍明确 schema3关闭；这是合成原库存与服务替身的本地认证，不是 schema3 新 start 或真实训练结果。

额外确认原 `test_training_cycle_controller.py` 的 schema3 native 反例故意没有完整 controller。新认证应先拒绝缺失的完整绑定，旧断言仅需移除过窄异常文案，保留 ValueError、无新效果与已有 result 早读。native 外层继续保留 schema2原许可顺序；schema3 外层原父许可及全部新效果正向按 M6 开启表延期，不能因 callback 早关而宣称 attempt/ack 更晚门已经可达。后续将沿实际 callback／fd／原锁接缝验证 schema2最后检查和大原件实际 reader。

本片私有检查目录以0700创建，文件按077 umask保存；没有完整环境快照、凭据输出、依赖安装、模型、真实训练、外部服务、commit、merge或push。以上只认证当次探索输入，最终候选及安装／自身模板／fresh实施审查尚待根流程。

### 后续探索与隔离边界发现

`exploratory-03.log`：3通过／1失败，83.55s。attempt 后 source 漂移、attempt 后原 clock discontinuity 及原 schema3已有result读取通过；ack 后 ROOT 漂移确实阻止 started/runner，但原测试错误要求 stopped 为空。实际 S 在已有 ack 后重收原 native 子进程并写真实 stopped 是合法观察，断言已修为保留这份实际 reap，同时仍要求没有 started/result/runner。`exploratory-05.log` 的三个同步故障随后全部通过；没有产品修复或删去真实 stopped。

容量探索 `exploratory-04.log` 在实际H、Budget.source、validate_context 已读取合法9,999,999B（完整UTF-8含LF）后，真正 `native_main -S` 在原 sys.prefix 检查拒绝：Python3.11 的 `-S` 不载 site，sys.prefix 退为 base prefix。保持原所选venv身份校验，不伪prefix。分列 `-P -S` 的纯认证和正常 `-P` 的实际native callback后，`exploratory-05.log` 进一步证明同一纯认证在拒 State/schema/SDK 导入hook下通过该大原件；真正 native callback 则在进入callback前因原executor的传递SDK导入被hook拒绝，**容量检查整体仍失败／未闭合**。

实际固定原依赖链为 `agent_platform.training_executor → agent_platform.training → perf_temporal.client → temporalio`。原283文件和native patch/descriptor均未修改，原 schema3 native测试本就显式附SDKsite。protocol/reference纯本地认证本身的stdlib隔离通过，不能由此称整个原executor真实hook无SDK。该实际接口与设计验收措辞差异已报根处置；未添加SDK shim、伪source、mock verifier pass或放宽产品接口。原失败日志及各次raw仍在私有检查目录，后续最终结果另记。

原 executor 传递 SDK 依赖的最小静态位置：原 `platform/local/agent_platform/training_executor.py:14` 顶层导入 `.training`；后者第20行顶层导入 `perf_temporal.client.load_experiment`；原 `platform/upstream/temporal/perf_temporal/client.py:10` 顶层导入 `temporalio.common`。探索05首次实际拒绝的 traceback 沿这三点，在 M5 `native_main` 导入 executor 时触发，尚未进入 callback。最小范围若要纯化应由原 reference/native owner另设计，不在本片改原283或补第三方假模块。

|原件|实际raw SHA256|
|---|---|
|未改283中的 training_executor.py|`e6d2273c5958b0d2327338ebb07aade8b4c6e3ce27eee42c39454bf9af31eed0`|
|未改283中的 agent_platform/training.py|`97dcf661b34de14f8edd28a1ca3c7fb4b40ca891b40398bbad73b8b8b6ebf9e0`|
|未改283中的 perf_temporal/client.py|`e01ac4d801af1ae3a6a56ca84b0645a0f9ab9dd50820943ad4374ed969d73ba9`|
|原 admission-v1 patch|`45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`|
|原 admission-v1 descriptor|`d7e2b706599c6fcbb874a1a1dbec8b9875df817dc71ffa455801e48c240c2c55`|
|原 reference manifest|`1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`|
|探索05所选实际patched executor|`feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`|

上述完整字节数、实际私有位置另存 `native-sdk-dependency-originals.json`。根已限定处置：M5源码gates继续受审；完整M5/M6保留真实hook SDK-free mandatory未满足。实际callback检查沿原真实SDK依赖进到关闭分支，纯认证另以-S和拒应用／SDK import hook验证；两者分别记账，不以其中一项替另一项。

## 冻结源码／测试输入与定向检查在途

准确 baseline 仍为 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`。冻结前已向根报告十文件完整patch及原件身份；`m5-g-source.patch` raw SHA256为 `fba1838ac6e7cb13cdbab9ec9b96e66cc38cdf8c5de3eb00c381f120ca050e1d`，`source-freeze.json`列每个变更文件bytes/raw SHA。开始冻结检查后 product/test均未修改。变更为六个产品owner和四个已有测试／fixture；没有新产品文件、CI、依赖、State表、参考283、patch或descriptor变更。

|固定产品源|raw SHA256|
|---|---|
|training_execution_protocol.py|`5cfeac98893c3b8715947956b0b718218129dd556e7bf8a465fe9e6b8dda8347`|
|reference_training_worker.py|`5ad5466c84dba9a093a53b9a4f8c626e06939d637e8268ce41403265b67c8334`|
|reference_training_budget.py|`c5d0245f1946e2375c6f6a7bdacd1fec8365e58074dd57a7912c7825550b91be`|
|reference_training_execution.py|`fa12537d2514e4ea29da496f55f4d4492d8f5485890eae84b6cc159db1d7ef4a`|
|reference_training_submission.py|`abc69091830934cf5759f436a7bcfbc9c399490fe44b9506c173f3d92a3b492c`|
|training_cycles.py|`911a6f6ff0aed679d4eb85ee0c20d8c19dfd50f24aaef37261cca015493a5cd5`|

独立输入记录 `frozen-inputs.json` raw SHA256为 `79c952517ebd1ec5501caade0a386afff8eb7b29c27a0ad8342bc5355eabcf6a`：665个受控source/pyproject输入，原25 gate和四measurement映射，reference.verify实际283 PASS。实际纯protocol导入未出现State、YAML、jsonschema或Temporal模块。只记录Python／依赖版本、平台及必要环境变量名，没有环境值快照；此记录不是新安装验收。

`exploratory-06.log` 保留一次fixture重复出生失败：第一份M−1完整原件已经通过H/Budget/context/native/纯-S及全部来源负例，随后同一个合成archive source bundle再次生成把已有evidence.json误纳入artifacts而由原archive owner拒绝。修正只使第二份容量reader原件重绑合成记录而不重复构造archive；不改产品archive语义或重写早轮原件。`exploratory-07.log`：**1 passed／55.87s**，最终编码9,999,999／10,000,000／10,000,001B均实际到达；前两者的Budget/context和真正native callback读完整原件后仍显式关闭schema3，纯-S返回本地认证成功且无SDK，实际callback明确观察到原executor导入SDK。H也实际读取M−1前驱并接受其内部观察；M+1完整raw保留、原ref容量边界拒绝，不能称更晚effect gate可达。

冻结后仅给manifest负例增加了纯边界的owner出生pin顺序断言，未再改产品；该测试变更已包含上述冻结patch。当前完整定向检查为 `frozen-source-01-command.json` 中准确23个既有函数及其参数化节点，实际使用现有dev解释器、源码PYTHONPATH和独立basetemp。范围覆盖k1/k3及最早raw/archive/helper投影漂移、最终M边界、原schema2的五个stop同步边界及三个native source/ROOT/clock故障、原registry/dispatch/window、owner1/2及离线round读取。最终返回码、节点数、耗时及冻源复核完成后另追加，当前不记通过。

controller测试额外scope仅为移除两处缺完整schema3 binding反例的过窄错误文案断言，保留ValueError与无intent/attempt/owner/native效果、已有result早读全部语义；没有给历史反例补伪source。原budget/pause fixture仅增加准确复制包的故障来源及native同步后原clock接缝，保留真实原publish/fd/锁/子进程/reaper。

时间顺序更正：上一节“冻结后仅给manifest负例增加”应为“探索07后、冻结前给manifest负例增加”；该断言已经包含在 `fba1838a…` 冻结patch，冻结检查启动后没有product/test改动。原23函数检查持续同一次运行，未因文档追加而重启。


### 原冻结批次终态与同片最小修正（源码r2）

原首冻 `fba1838a…` 的23个函数实际38参数化节点已终态：**37 passed，1 failed／639.04秒**（wrapper639.6245秒）。原命令、日志、结果及首冻原件保留。准确失败为 `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync` 第2977行 `KeyError: ref`，并非此前猜测的显式execution用例。

原dispatch operation `3a730bd8bf2a4272bfa3f6801b06cea8` 的已知固定 `helper/stdout.txt` 保留103B完整JSON：`status=unknown`，reason为 `Original candidate activity context differs from its prepare source`。原fault marker与alpha原attempt实际存在；service记录starts=0、仅describe。prepare／confirm／dispatch共用原7秒窗口，fault进程的原start_ticks对应约5.77秒处。父owner只在两完整帧且最后仍在原窗口时接纳stdout ref，透明unknown可无ref；因此该失败是测试无条件索引ref的oracle缺陷，实际同步后source gate已经拒绝。不能把保留的H诊断当作已接纳ref或完整durability认证。私有 `frozen-source-01-failure-diagnosis.json` 固定准确raw SHA与原窗口，未改窗口或业务result语义。

r2只在原测试按已知operation_id读取固定原H stdout，保留fault、真实source拒绝、attempt占用和零SDK send断言；另按独立审查R2删除 `_round_local_gate` 在 `validate_sources` 已执行原283核验后的重复 `reference.verify()` 及旧注释。measurement比较、原registration、最终clock／active／stop检查完整保留。未改283清单、SDK来源或schema3效果闭门。

新完整10文件patch `m5-g-source-r2.patch` SHA256为 `47669d3b99614ca0f41a3f03161a50cb3dcbb1f861d50ed7ede718263879bfd0`；`source-freeze-r2.json` SHA为 `44aad07c0d79ce95f4330b462343ef9fb68bfa23bde8fb36e811a164588a0072`；`frozen-inputs-r2.json` SHA为 `a03556bb4fb04095cdd63ce4059b9e84b1e00a5f6d71a7e93673f50653e56c6c`。665个source／pyproject输入、原25 gate／四measurement映射重新冻结，原283实际PASS，纯protocol新进程导入的禁止模块列表为空。当前仅重验原失败及实际受影响的collect/reconcile、k1/k3全链、大reader／ROOT、最终source／stop及最终阻塞读，准确命令为私有 `frozen-source-r2-affected-command.json`。原37个通过节点保留其首冻自身范围，r2尚待本轮终态与fresh复核；全M5完整native hook无SDK mandatory仍开放。


### 源码r2受影响验证与原件收尾

固定r2的同次受影响检查实际 **10 passed／194.00秒**（wrapper194.5995秒、returncode0）。准确六函数及参数化节点的命令、日志和结果位于同一私有证据根的 `frozen-source-r2-affected-command.json`、`.log`、`-result.json`。原失败用例现通过，仍实际观察到同步后source拒绝、已消耗attempt、零SDK send；读取的是原固定H诊断，不宣称父ref接纳。其余节点实际覆盖collect／reconcile闭门、k1／k3完整前驱链、9,999,999／10,000,000／10,000,001B raw边界及ROOT／来源负例、最终source／stop两例、阻塞读后的最终index／parent source／registered project三例。未重跑原38节点总批；原37通过的其他节点只保留首冻范围。

运行后 `source-r2-integrity-and-identities.json` 已核完整tracked diff仍是 `47669d3b…`、10文件raw SHA全部匹配r2、665输入raw SHA／执行位保持、首冻patch原件保持。`git diff --check` 通过。仅从实施owner拥有的探索与两轮冻结test根中的原request／owner／marker／native／execution记录提取，去重113个完整Linux身份经原 `processes.identity` 核实均absent identity，live match=0、unknown=0；合成pid1记录显式排除，未信号任何任意PID。该收尾范围不包含父owner的新安装／自身模板运行。

实施owner自有证据已按要求规范：9,335目录为700，23,896普通文件为600或保留owner执行位的700，跳过63个symlink；再次读回自有目录无权限偏差。父owner的package／自身模板证据未改动。原件、命令、失败诊断、完整输入冻结均保留，无commit／merge／push、依赖安装、模型、真实训练或外部服务调用。r2等待同一fresh reviewer复核两项最小修正；新非editable包／自身模板／最终整体验收由父owner继续。全M5的完整native hook无SDK mandatory仍开放，schema3效果未开放，正式M6不在本片验收范围。


### 自身模板新P1：解释器最后准入的原r2反例与r3修正

父owner执行的原结构模板Codex真实64.043秒 `request-changes` 指出：`Execution.current` 原有解释器 `is_file()` 准入未进入shared source校验，因此native callback在实际attempt／ack同步后重新核源码／安装descriptor时可能遗漏所选Python路径已不可用。实施owner未先假定finding成立：保持六个产品文件逐raw匹配r2，只在既有真实publication pause函数增加一个 `ack/interpreter` 参数；ack原同步后把所选 `.venv/bin/python` 路径重命名保留（不改symlink目标），release后按原attempt的完整executor身份等待真正native退出，再恢复原路径并走原stop／reaper／records断言。

初次直接指定节点ID未包含原叠加fixture参数而收集失败，returncode4／no tests；`interpreter-red-r2-command.json`、`.log`、`-result.json` 保留。修正仅用原函数 `-k ack-interpreter` 后，原r2真实 **1 failed，3 deselected／25.44秒**（wrapper25.9700秒），准确失败为测试1027行无started断言。原ack／attempt均存在，真实callback已经返回并让原executor写了 `started.json` 和FAILED `result.json`；原stderr为空，stdout／result说明后续因fixture缺 `config/platform.json` 失败，未运行真实runner。这证明最后准入遗漏，不能把后续失败算作解释器拒绝，也不声称Python spawn或真实训练。原精确测试完整文件、SHA、原started／result和身份索引保留于 `interpreter-red-r2-02-*`，原r2冻源／安装结果不覆盖。

r3最小产品修正仅把 `Execution.current` 现有两行 `Path(capability['native_python']).is_file()` 准入及原错误移到existing `validate_sources` 最后，删除current重复。仍使用原venv路径绑定和合法symlink语义，无新validator／协议／hash／版本合同。新参数同原source／ROOT／clock故障共用原native publish／锁／callback，不扩SDK／业务时限；额外按原launch的execution_phase_id读取固定原helper stderr，要求明确 `Original native interpreter is unavailable`，同时保留request原件／ack／真实reap以及无started／result，避免无关native失败掩盖反例。

新10文件完整 `m5-g-source-r3.patch` SHA为 `41fcda7acf74b6600f4dbf1a56aa1fa1a19c1c55300156c32b01233b42bed2be`；`source-freeze-r3.json` SHA为 `1b5c4f03e2ef72ab97cceae38509b4ecae03671e586c7232ce53afb0ab1d6a7a`；`frozen-inputs-r3.json` SHA为 `fe44aa003752a2a42b534b0c52f2e43567de8f609360f244536d53202c46cc2f`。665 source／pyproject、25 gate／四measurement重冻，283实际PASS、纯protocol禁止模块列表空。正在固定r3仅跑四个必要既有函数：native四参数（含新单项）、原request锁writer、SDK-free离线history、collect／reconcile；不重复r2原38节点或10边界批。准确命令为 `frozen-source-r3-affected-command.json`，终态与冻源／资源复核另记。完整native hook的无SDK mandatory仍开放，schema3效果仍关闭。


r3固定受影响组已终态：**7 passed／138.75秒**（wrapper139.3284秒，returncode0）。四个native同步故障（source／ROOT／原clock／解释器）全部通过，新解释器单项原helper stderr明确为 `Original native interpreter is unavailable`，started／result实际均不存在；原request writer锁、SDK-free离线history与collect／reconcile通过。只按实际移动的共享source门复核这7节点，未重跑旧38／10边界组。

运行后完整diff、10文件raw SHA、665输入raw SHA／执行位均匹配r3，首冻及r2完整patch原件保持，`git diff --check`通过。私有 `source-r3-integrity-and-identities.json` 覆盖全部实施owner自有探索、三轮冻结source和解释器红例test根，去重137个完整原Linux身份当前live match=0、unknown=0（合成pid1排除），没有发送任意PID信号。自有证据重新规范为11,302目录700／29,052文件600或保留owner执行位的700，跳过72个symlink；读回权限偏差0。父owner的package及自身模板证据只读、未规范或修改。r3留待父owner的新安装／自身模板与fresh复核，完整native hook无SDK仍开放，schema3效果保持关闭。


### 安装r2原source-sync用例的第二种真实失败（只读定位）

父owner的安装r2原批为37 passed／1 failed／843.49秒，失败仍是 `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync`，这次在fault marker存在断言，不能与首冻源码的ref索引失败合并。实施owner只读其原命令与固定case原件，确认prepare `e028a3e6…` 和confirm `0175f1aa…` request都实际存在且共享同一个7秒bootstrap（started_ns2813410663711268，deadline_ns2813417663711268）；confirm H stdout实际owner_confirmed，但没有任何dispatch-candidate request、alpha.attempt、故障marker或service.json。后续inspect原started_ns2813417740654644已经在该deadline后约0.077秒，原BOOT总预算仍约883秒。这说明普通用例在confirm接纳／dispatch之前已消耗完原一次start窗口，最终同步source反例没有到达，不能称为source gate验收。父accepted frames／inline result未在此case持久保存，confirm stdout文件mtime只有整秒，因此不声称更精确的帧时序或额外失败原因。

既有fixture明确在create／authorization出生前用indirect `controller_admission` 参数更新selection.budget，相邻普通execution-sync用例已用30秒。已向父owner报告最小方案：仅给这一普通source-sync用例显式control_timeout_seconds=30，保留原一次prepare／confirm／dispatch共享连续窗口、原默认7秒和专门timeout反例；不改产品或重开clock。当前尚未编辑r3冻结源，等待父owner接受此最小配置方案。原installed-r2现场、原38节点结果保留；只读索引为私有 `installed-r2-dispatch-diagnosis.json`。


### r4仅修普通source-sync出生配置及最终源码交接

父owner接受上述最小方案后，仅在既有 `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync` 增加原indirect `controller_admission={'control_timeout_seconds':30}` 参数。六个产品文件raw逐字保持r3；默认7秒、专门timeout反例、原BOOT授权、prepare／confirm／dispatch的单次共享窗口和全部最终source／attempt／no-send断言未改。没有运行中重开或扩窗。

r4完整10文件 `m5-g-source-r4.patch` SHA256为 `141448e6cb9eb169e06f5722bda64e462690680d654b2e62c76029b59cd404a3`，`source-freeze-r4.json` SHA为 `5ea94ea6e9c56395ab35bdfc158407c156b95088795fa1858f62c4d1eb97ba0a`。新的 `frozen-inputs-r4.json` 原件与r3完全同字节，SHA仍为 `fe44aa003752a2a42b534b0c52f2e43567de8f609360f244536d53202c46cc2f`；665输入raw／执行位、25 gate／四measurement及283实际PASS保持，纯protocol禁止模块列表空。r2原安装37／1和confirm后尚无dispatch／attempt／fault的真实失败保留，不覆盖为通过。

按授权只跑该一个既有函数，实际 **1 passed／27.36秒**（wrapper27.9285秒，returncode0），原命令／日志／结果为 `frozen-source-r4-dispatch-*`。运行后独立读prepare／confirm／dispatch三份原request，bootstrap完全相等且deadline−started恰30秒，原authorization.clock三份全同；原fault marker／alpha.attempt存在，原H固定stdout103B明确 `Original candidate activity context differs from its prepare source`，service starts=0、仅describe。完整原件SHA／窗口和身份索引为 `frozen-source-r4-dispatch-boundary.json`，没有把早期窗口拒绝或保留H诊断冒充父ref／完整durability接纳。未重跑38／10／7节点批。

最终复核full diff／10文件／665输入全部匹配r4，首冻／r2／r3完整patch保持、r3产品字节及665记录原件保持；`git diff --check`通过。自有探索／冻结源码／解释器红例test根去重141个完整Linux原身份均absent，live0／unknown0（合成pid1排除）。自有证据11,449目录700／29,504文件600或保留owner执行位700，跳过74个symlink，权限读回偏差0；父owner的package／自身模板现场仅只读。无commit／merge／push、依赖安装、模型或真实训练。固定r4留给父owner新noneditable安装、原模板及fresh最终复核；完整native hook无SDK mandatory仍开放，schema3效果和正式M6不在本片开放。


## 根验收：r2安装／原模板原件与r4新候选

根曾构建准确r2新wheel `0d40d2fcf49403afa8ddd96d18d55c8a3d51543b24b407190e3c2fff1ac20278`，非editable core／SDK分别实际site-packages，完整663文件与源码／wheel的字节及执行位同一；原283和依赖核验通过，core无Temporal／SDK为1.34.0，853源输入与179测试／示例副本已冻结。六份build生成egg-info已归档后按已知原件移除。r2安装38节点实际37过／1失败843.49秒（driver844.651秒），上节已逐原件解释这一次未到dispatch的7秒窗口失败；不能把它与source首冻ref错误混同，也不认证整批通过。

同r2新SDK实际运行原 `refactoring-quality → ergora-structure-review@1.0.0`，Codex64.043秒 `request-changes`。18完整文件879,039B、完整77KB级diff和三份全部祖先资源进入964,086B原stdin，SHA256 `b9e8dfa56a7be03804d459d5164d68396a5b1eff7b64300ffeb73c5bc7abac4a`；result SHA `ef279d9b1725f2ecd6ebbc2bb4090112321de11bf7c79630dcfc9f429ef8ea60`。原回复指出真实解释器最后门P1，后续红例／r3修正沿上节保留。模型仅审完整所供文字，不称workspace／独立测试；whole-hook SDK-free仍未满足。

为保持原在途安装输入，根没有更改原测试树HEAD，另将相同853输入的r2树固定为a1ff338候选；在独立固定树上普通提交r3／r4小差异，当前准确r4源候选为 `68f3241695f5de1fdc188609db612c1d30434edf`，唯一父a1ff338，完整相对实施基线1f57ca4的10文件patch仍 `141448e6cb9eb169e06f5722bda64e462690680d654b2e62c76029b59cd404a3`。这些是固定源码候选，尚未导入／推送，也不表示完整M5已通过。

同片[fresh源码复核](2026-11-16-training-cycle-predecessor-native-gates-source-review.md)已核原红／绿、r4单项与连续window，当前限定源码需求／维护性两轴approve，R2／R3关闭；R1完整native hook无SDK保持开放。报告SHA `62758b9b229b91e7b5f53a16c8068c771ee32f1e35780c206d114a44032ac714`。根正在以r4重新构建新的非editable core／SDK包，单独验安装受影响行为／自身模板／最终证据；不把r2／r3结果无条件转授r4。私有原件沿 `cycle-predecessor-native-gates/package-r2/`、`self-review-r2-codex/`及新 `package-r4/`保存。
