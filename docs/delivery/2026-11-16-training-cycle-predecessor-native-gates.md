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

同片[fresh源码复核](2026-11-16-training-cycle-predecessor-native-gates-source-review.md)当时已核原红／绿、r4单项与连续window，限定源码需求／维护性两轴approve，R2／R3关闭；R1完整native hook无SDK保持开放。当时报告SHA `62758b9b229b91e7b5f53a16c8068c771ee32f1e35780c206d114a44032ac714`仅代表该版；后述自身模板新finding已使当前源码结论重新成为request-changes。私有原件沿 `cycle-predecessor-native-gates/package-r2/`、`self-review-r2-codex/`及新 `package-r4/`保存。

### 根r4安装通过与自身模板新增时序缺口

准确r4新wheel SHA256 `f567e8f379c1e971357f0469e6797ee6938160463bb12012144ceb356def9006`，新非editable core／SDK各663产品文件的raw／执行位与源码及wheel同一；283参考／依赖检查通过，core无Temporal、SDK1.34.0，853完整构建／测试输入与179测试／示例副本固定。仅用这些冻结副本跑11个既有函数的18参数化节点，实际 **18 passed／424.83秒**（driver426.051秒、exit0）；原件在 `package-r4/installed-affected-r4-*`。这属于r4已安装行为证据，不能转授正在修正的后继源码。

同一已安装r4 SDK实际运行原 `refactoring-quality → ergora-structure-review@1.0.0`，Codex86.323秒 **request-changes**。18完整文件880,313B、完整diff与三份全部祖先资源构成967,968B stdin，SHA256 `7e7811f75dd8e2c566d812afc7efb9ba4daf0b5a826fa323d414bf7ff17d19b7`；原result SHA256 `5b13d19484086564a509c7c99c8d2e8c94aa997763432332db944b8aa0e8aea3`，保存在 `self-review-r4b-codex/`。前次脚本路径替换错误只造成模型启动前失败，原 `self-review-r4-codex/`与setup-error保持，没有模型调用或审查成绩。

原模板提出两个P1，已由同片独立reviewer静态核实并由原r4产品真实复现：最后native clock条件之后的parent授权读取可阻塞至work耗尽仍写started；最后SDK等待期间最早round0原index只加LF，当前round1材料保持，仍错误返回continuation_ready。真实红例 **2 failed／41.63秒**、同BOOT原work约−1.006秒而cleanup总预算仍正、真实started后因fixture缺config失败；未运行真实训练。准确命令／结果／完整原测试输入和诊断为 `frozen-source-r4-order-red-*`，不覆盖已有r4安装成功。

实施owner正在修正最终顺序。首个r5方向探索删除原末_H的archive／phase复核，经根与独立审查核到真实AWAITING_RELEASE→CANCELLING／CANCELLED路径，因此不能作最终候选；保留该探索及其同次受影响验证，后继恢复原末_H并在全部阻塞操作之后重新核完整本地链。不能为了减少遍历次数删除真实phase保护。R4／R5仍开放，最终冻源、受影响源码／新安装／自身模板及终核另验；R1无SDK完整hook继续由独立source-v2片承担，schema3效果未开放。


### r4自身模板两项最后读取 finding：原字节红例、探索与最终r6

父owner记录的r4首次模型启动是本地config路径setup错误、模型未调，原失败保留；第二次 `self-review-r4b-codex` 才是真正完整967,968B输入的Codex审查，summary实际86.322764秒、exit0／succeeded、decision=request-changes。其两项finding分别指出native最后父authorization读取可能阻塞到work已过，以及worker在最后认证前驱后仍做SDK／index等阻塞读取，可能释放旧链acceptance。实施owner先核实际调用和原合同，没有将模型结论直接当作已重现事实。

仅在原publication／read／SDK fixture接缝增加两条必要反例，运行前六个产品文件raw逐一匹配固定r4。native新 `ack/parent-work` 在真实ack出版后的最终 `active→parent.check→authorization.json` 读取返回前pause；release时在该native进程同时前移原BOOT采样与UTC，保留原boot／authorization并用原完整 `remaining` 实测work=-1.006317秒、total=168.993650秒，cleanup仍正。没有替换remaining返回值、传入accepted或改授权clock。等待原executor完整身份退出后，原r4仍实际写started与FAILED result（fixture缺platform.json、未运行真实runner）。链新 `round-final-parent-predecessor` 在当前round1 observation已落盘、真正最终parent SDK describe返回前pause，仅给已知最早round0原index加一个LF；当前round1 index／observation字节保持，原r4却返回observed／continuation_ready=True。原件在finally恢复，变化前后真实材料和失败结果保留。

原 `frozen-source-r4-order-red` 准确 **2 failed／7 deselected／41.63秒**（wrapper42.5066秒）。命令／日志／结果、原完整测试与两个fixture、原started／result、完整合法clock采样及错误接受原结果，分别保留于 `frozen-source-r4-order-red-*` 和 `r4-order-red-test-inputs`。native失败在无started断言，链失败在应为unknown而实际observed；这是两项不同的真实遗漏，不把早拒绝或无关SDK失败当作最终门禁证明。

第一方向r5将最后_H wrapper换成末端纯链认证，固定patch `8edffae7…` 的4函数12节点实际 **12 passed／212.38秒**（wrapper212.9585秒），运行后原11文件／patch保持。但父owner及独立合同核对确认原 `AWAITING_RELEASE→CANCELLING/CANCELLED` 可达，即使SUCCEEDED job原件稳定也会变化，原最后_H phase查询必须保留。r5因此只作为探索原件，不是最终合同验收；其源freeze／665输入／差异和成功检查没有删除、改写或转授最终候选。

最终r6恢复原末_H的原位置，首／中间same-fd阶段／末端_H完整archive语义与紧邻phase读均保持；另外在最终SDK／当前index／本地gate读之后调用同一个 `protocol.authenticate_cycle_candidate` 再绑定本轮index。保留原_H语义后，较r4多一次末端纯链遍历，是上面真实晚阻塞漂移所需的重认证；不通过删除phase门、缓存“已验”或扩预算规避。native只把现有parent.check移动到原fence／owner／完整clock条件之前，未复制validator或新增clock合同。相对准确r4提交 `68f3241695f5de1fdc188609db612c1d30434edf`，产品仅worker末端3行新增与protocol原parent／clock顺序移动及说明，原_H调用无删除。

新增末端纯链I/O仍消费原预算：shared authenticator自身末尾在owner／ready／cycle／所有source读取之后，执行原active，顺序为admission.check（authorization读和stop）→原完整remaining(clock,wall,cleanup)→return。其后worker只做纯report／acceptance投影。上层实际 `_CycleOperation._run` 在两完整帧／pipe EOF／原S回收之后，仍要求 `not self.expired()` 才接纳ref；expired调用原 `cycle_operation_remaining`，collect／reconcile属于CYCLE_WORK_MODES，计算同一bootstrap窗口与原BOOT／UTC work的最小值。这样H迟到私有诊断不转为父accepted ref，不需要再造clock／stop validator。

最终11文件 `m5-g-source-r6.patch` SHA为 `3a56cf9952e4acd1616787bcaed616b3c5b593b2e7dfd683e700e3261e5aca1c`；`source-freeze-r6.json` SHA为 `88a423b0f7dc2bc00e7773a67f1f73a38ccdc62f341666a3ddd4bc20bf2de459`；`frozen-inputs-r6.json` SHA为 `e88af9b3a21298945bad2180b7346f8d22dfb32402bfccc2dd839538ef8b857c`。665 source／pyproject、25 gate／四measurement重冻，283实际PASS、纯protocol禁止模块空。相对68f3241给父owner接独立source-v2用的 `m5-g-r4-to-r6.patch` SHA为 `0c0c5a789bed01e6adf572e53857cec5f897215a2a3a8be8c2f4bf8ba513a9ee`，实施owner未触碰该独立树。

r6运行仅验证实际受影响worker：原final-blocking四参数（含新漂移）、collect／reconcile、k1／k3完整链与大reader，共四函数8节点；多出的纯链遍历产生新大raw读取成本，因此这次大reader有明确重验理由，不增加control时限。native protocol raw与r5五native参数成功时完全一致，未为freeze格式重复测试；这些native证据只陈述同raw callback行为，不冒称整r6验收。准确命令为 `frozen-source-r6-affected-command.json`，终态与源／资源复核另记。原r4安装独占运行及其副本、source-v2、主树source／PLAN未改；全hook无SDK mandatory仍另片开放。


### 最终r6源码受影响检查与交接

固定r6四个worker函数实际 **8 passed／138.86秒**（wrapper139.39624秒，returncode0）。原final-blocking四例分别明确拒绝stop、安装source、registered project与最早前驱raw index；新增最晚SDK漂移例的原结果为unknown、reason为 `Previous round pin differs from its complete raw original index`，当前round1 index／observation保持。collect／reconcile、k1／k3完整链与原最早start inventory／archive／helper投影漂移通过。大reader实际命中9,999,999／10,000,000／10,000,001B原raw，包含同一末端额外纯认证成本；前两边界按原消费者认证后仍关闭schema3效果，M+1保留完整原件且原ref容量拒绝，未扩大任何budget或窗口。

同raw protocol的r5五native参数均已通过；其中新ack父读work边界原stderr明确 `Original execution fence, owner or computation deadline forbids work`，原完整clock实测work<0、total>0且boot保持，started／result均不存在。r6没有再次修改该protocol，也没有为冻结记账重复五native；其准确raw SHA与原phase定位、r6晚链拒绝原件索引固定在 `source-r6-boundary-summary.json`，完整r5探索仍不转授_H phase合同验收。原r4两条真实红例、r5被拒绝方向及全部成功／失败原件保留。

运行后full diff／11文件raw SHA／665输入raw及执行位全部匹配r6，首冻、r2／r3／r4与r5探索patch保持，`git diff --check`通过。自有探索／所有冻结source／解释器及两项顺序红例test根去重184个完整原Linux身份当前live match=0、unknown=0（合成pid1排除），未信号任意PID；14,969目录700／38,396普通文件600或保留owner执行位700，跳过90个symlink，读回权限偏差0。父owner的安装／模型现场和原source-v2树未改。

最终source已稳定供父owner据完整r6及相对68f3241的精确delta继续新noneditable安装、原结构模板与fresh终核。实施owner未commit／merge／push或安装依赖，无模型调用／真实训练／外部服务操作；schema3效果保持关闭，全hook无SDK mandatory仍属独立片，源码受影响通过不关闭全M5。


### 根：r6新安装、原模板及新增current intent问题

最终r6全patch `3a56cf9952e4acd1616787bcaed616b3c5b593b2e7dfd683e700e3261e5aca1c`已固定为源码候选 `f6722141cfa9ed885993360161c004e47e8df3a5`（父68f3241），完整相对1f57 diff逐字同一。新r6非editable core／SDK各663产品文件与新wheel的字节／执行位同一、283参考／依赖通过，853源输入与179测试／示例副本固定。新安装仅跑实际顺序修正涉及的五个既有函数，**13 passed／346.70秒**（driver347.800秒），不重跑无变化38／18总批；原件在 `package-r6/installed-affected-r6-*`。六份生成egg-info已归档后按准确原件移除。

同片reviewer已核r4真红／r6绿及末_H保留，R4／R5关闭，r6限定源码两轴approve；当时报告SHA `3d028dc01c237e4aa83cbc4d1345a52aee38507ae5640e42074f38ecfdce1b84`。随后根以r6安装SDK调用原结构模板，Codex79.601秒 **request-changes**，发现shared长链认证末端可能遗漏当前磁盘intent漂移。18完整文件858,633B、完整diff及三祖先资源进入955,359B stdin，SHA `262d40104a2c0370bb8f8622f69f0b40ee2df6951eb0235d4455008b4436a5ec`；原result SHA `60c5b39ef69c815689dd18ac012aba92a7415bb59ba28c7513effab5134d94cd`，保存在 `self-review-r6b-codex/`。所有改动文件完整提供；仅未提供无变化的reference.py全文，未截断任何已提供文件。r6首次私有review脚本误设2,000,000字节，被现有1,000,000上限在prepare阶段明确拒绝，未调用模型；失败目录／setup-error原件保持，修正仍沿原上限，未改产品容量。

新增R6／P2由同片reviewer静态核实：shared构造current但只读owner，当前intent仍是caller缓存；较早H／Execution读取不足以覆盖最后完整链的阻塞窗口。实施owner正在准确r6作原fixture真实反例，随后按原canonical意图身份最小重读，不新增raw pin或caller可放宽开关，保留owner／intent均未出生的prepare合同。r6安装通过只归本r6；R6、R1仍开放，完整M5未通过，后继产品／新安装／自身模板及最终终核另验。


### r6自身模板P2：当前实际intent缺口与r7语义修正

父owner的新r6非editable安装13 passed／346.70秒保留；其后自身模板 `self-review-r6b-codex` 实际Codex79.600703秒、955,359B完整输入、exit0、decision=request-changes，指出shared authenticator仅验证caller缓存current intent和当前owner，却未读当前实际intent。实施owner先核真实路径：`prepare_binding` 在intent发布前构造BudgetedStart并require_active→source→shared，因此必须允许尚未发布intent／owner的原prepare；发布后的Budget.source、H的原_H认证及末端pure、Execution／native context同样调用shared。H的_cycletarget／local gate虽较早读实际文件，末端pure大读取期间仍可能过时。

保持准确r6六个产品文件raw不变，只给既有final-blocking fixture增加 `round-final-current-intent` 一个反例。真实round0已接受、当前round1 observation已落盘后，在最终direct `_round_operation→authenticate` 的末端current owner原始读取返回前pause（已读完旧链）；仅改变当前beta.intent.json的合法operation_id，owner／旧链不动，当前round1 index／observation字节保持。既有上下层保护完整保留。原r6仍返回observed／continuation_ready=True，准确status断言失败：**1 failed／4 deselected／18.09秒**（wrapper18.80764秒）。原命令、日志、结果、before／after原raw SHA及错误接受原件在 `frozen-source-r6-current-intent-red-*`，准确红测试和fixture完整原件在 `r6-current-intent-red-test-inputs`，finally恢复原intent。这是实际内容漂移，不把合法空白变化称作语义漂移。

r7产品只在原shared函数增加6行：入口沿existing `ExecutionRecords.document` 以原 `16*LIMIT`（16 MiB）读取当前实际intent；有owner时缺文件直接拒绝，实际文件存在时完整语义_match caller缓存。当前owner和intent均尚未出生仍允许原prepare；末端所有source I/O后再读完整语义及原存在性，入口已有文件时末端不得缺失，入口缺失时也不得静默换成新文件，随后仍走原stop／完整clock active。没有新函数、caller开关、pin、替代intent、State／SDK或ledger。当前intent沿原canonical JSON合同比较，合法空白继续允许；前驱的原raw inventory约束保持。

在原collect／reconcile函数尾复用真实fixture补充必要合同验证：当前intent仅加LF仍能认证；当前owner已经出生而intent缺失会拒绝；下一个candidate1的真实未发布prepare对象在intent／owner都缺失时能纯认证原前驱，且两个文件仍未出生。新晚漂移反例能击穿仅入口早读的修法；这些检查没有开放schema3效果或伪造SDK来源。

完整11文件 `m5-g-source-r7.patch` SHA为 `61e1e11fbbc582453b3afeba3d20786eb2347c279fea3b4969285c0121f3b017`；`source-freeze-r7.json` SHA为 `37a93c5e947e6cb24fb02c61302f4dd9c52f0b757d733e2c57b0df58d4452a77`；`frozen-inputs-r7.json` SHA为 `9dd92719f6542977f92f96c56641a2e6e6389595f7e851ad685c2ec10bdfafde`。665输入、25 gate／四measurement重冻，283实际PASS、纯protocol禁止模块空。相对r6的准确三文件 `m5-g-r6-to-r7.patch` SHA为 `64250fa2be9d490fbd185a2a2455d4dba522bc625e74145dbd76a6054d47ff96`，旧文件取原r6b scope且逐raw匹配r6冻结，当前r7 reverse apply --check通过；相对68f3241完整delta `m5-g-r4-to-r7.patch` SHA为 `d578d5e551f4a959fecd568f76acfcff37113079db10770e0ea96476806a976d`。未编辑独立native树或包副本。

固定r7仅跑新增late-current-intent单项、扩展collect／reconcile、原k1／k3全链，实际 **4 passed／69.57秒**（wrapper70.18582秒、returncode0）。准确命令／日志／结果为 `frozen-source-r7-affected-*`。未重跑既有13／8／native／大reader批，旧结果仍只归各自固定候选；完整hook无SDK mandatory仍由独立片另验。运行后完整源／原件／进程与权限复核另记。

r7终核已完成：full diff／11文件raw／665输入raw及执行位全部仍匹配固定r7，首冻、r2／r3／r4、r5探索与r6原patch全部保持，`git diff --check`通过。新增晚current intent原结果为unknown，原reason为 `Complete original current candidate intent differs from its complete original identity`，supervisor returncode0且operation_stopped=true。自有测试根去重191个完整原Linux身份当前live match=0、unknown=0，未信号任意PID。权限归一记录15,494目录700／39,920普通文件600或保留owner执行位700，跳过98个symlink；随后同范围实际读回15,494目录／39,921文件／98 symlink，权限偏差0（读回多含刚生成的归一记录）。

终核原件为 `source-r7-integrity-and-identities.json`、`source-r7-permission-normalization.json`、`source-r7-permission-readback.json`；红／绿准确result SHA、晚intent拒绝原结果及边界状态索引在 `source-r7-boundary-summary.json`，SHA256 `5a2baf52898480f0ce2f125b59f6a9fba765c767fb0176533710574cb4bccfc3`。产品与测试不再修改，交父owner继续新r7非editable安装、原模板及fresh复核。独立native树、父owner包／模型原件未改；本实施owner无存活自有工具会话，无commit／merge／push、安装、模型调用、真实训练或外部服务操作。完整hook无SDK mandatory仍OPEN，schema3效果仍关闭，源码4项通过不等于完整M5验收。

### 根：r7 新安装与原结构模板终态

完整 r7 已固定为 `5bcecf37b615e3708ceb08acc329ba3dd0470f4a`，父 `f6722141cfa9ed885993360161c004e47e8df3a5`；相对 1f57ca4 的完整 patch 仍为 `61e1e11f…`。新非 editable core／SDK 各 663 产品文件的字节／执行位与源码、wheel 同一，283 参考与依赖检查通过；core 不含 Temporal，SDK 为 1.34.0，Python 3.12。wheel SHA256 为 `fafeede32f20d162a4b2977bb121afef80a8df48e07dcda720e44c4d37a3a02e`。853 构建／测试输入、179 测试／示例副本冻结，六个生成 egg-info 文件按准确原件归档后移除。

安装受影响组 **5 passed／148.89 秒**（driver 150.153 秒、exit 0）：末端当前 intent 漂移、collect／reconcile 的 canonical／missing／unborn 合同、k1／k3 全链和原完整容量 reader。命令、JUnit、日志、原件为私有 `package-r7/installed-affected-r7-*`。没有无理由重跑 r6 的 13 项或同 raw native 五项，旧结果只保留原候选范围。

同一安装 SDK 使用 `refactoring-quality → ergora-structure-review@1.0.0`，Codex **67.198 秒、request-changes**；仅重申已知 R1 完整 hook 无 SDK 前置，没有新增接线 finding。18 个完整文件 862,310B、完整差异与三祖先资源全部进入 963,759B stdin，SHA256 `5c20e359784202e0da60506c4984414f8b20a477ec206e056bcfe4cc2c911316`；原 result SHA256 `d3423a6ec31f1a9cdb992a4a960f1714a2e1c8b451f28616594163829ef78974`，见 `self-review-r7-codex/`。保留该历史判定，不为消除文字上的 request-changes 反复调用模型。

同片源码 reviewer 已关闭 R2–R6，限定需求／维护性通过，报告 SHA256 `8e7a72954e74af7568f67b829a6f49db3df6487a7f179cd56404b073057e9e23`。R1 由[原生依赖隔离独立片](2026-11-16-native-admission-dependency-isolation.md)的最终安装 whole-hook 证据解决，须新 fresh 联合终核后才能关闭；尚未导入或认证正式 M6／schema3 效果。安装原件与捕获身份另做终核。
