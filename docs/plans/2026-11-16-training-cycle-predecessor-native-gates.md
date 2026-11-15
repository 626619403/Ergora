# c1d M5a：原前驱、来源与 native 最后准入实施设计

2026-11-16。**仅设计，待独立需求／维护性审查；未实施、未执行验收，不开放 schema3 或 ordinal1。** 本页的实施建议从属于[原测量／索引要求](2026-11-16-training-cycle-measurement-and-index.md)、[wire](2026-11-16-training-cycle-measurement-wire.md)及其[复审](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)。发生差异时以原 wire 为准，不在此另定 wire、源码白名单或授权方式。

采用 maintainable-project-delivery、ergora-codebase-quality 的 module-design／test-seams；已读根／src／tests AGENTS、PLAN、组件协议、上述原件、[容量分期](2026-11-16-training-cycle-measurement-capacity.md)及 D1 复审、[M2/M3 设计](2026-11-16-training-cycle-measurement-acceptance.md)和相关真实 owner／接缝。本次只写本文；不改 PLAN、交付记录、源码、测试、参考资源、依赖或当前 M2 工作树，不运行 tests、probe、replay、安装、网络、模型、服务或训练，不 commit／push，不递归搜索整个 `.ergora/checks`。根任务另安排本页 fresh 审查；作者自检不是独立结论。

## 身份、前置与交付边界

主树只读身份为 `refactor/architecture-foundations`／`833966d4ba21fa7bcb6670e9908d05f058cf8fdd`；M1b 产品 `67ab9b4e446527fd27a61eff1aa6acb8d24feb01` 已普通导入 `23ad171bf8228bf80b070d6ad866f79d63986d56`。源码／安装／模板／fresh 的既有结果沿所属交付保留，公开候选自己的 CI 状态另记，本页未查询或继承 CI。主树已有其他人的文档改动，均不覆盖。

|本次读到的原件|raw SHA256|
|---|---|
|measurement-and-index 设计|`4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d`|
|权威 wire|`ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|容量分期／D1 修订|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|已接纳 M2/M3 核心合同|`2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`|
|protocol|`fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`|
|budget|`1fde5981eb63aa50dcaaae427144528ff27d2ff4bba3345bc13fe1059a441cb4`|
|execution|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|
|worker|`645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`|
|submission|`9c775643b07a937690230cdb86bd19e0d6fc89fcdb092fbb50d7bc3856a7575c`|
|reference|`a3c53b2f8b15954709ec068a984d3623918acd5a55e3d18ed59c41ec977bdb30`|
|包内 reference-manifest|`1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`|

M2/M3 实施树的 Git 基线仍为 `23ad171…`，**源码未冻结／未正式审查**。本次读到 protocol 的新前驱 shape、observation 完整读取，以及 worker 的本地 report／acceptance 绑定和 `_round_previous`，只用于证明实际职责位置。首个 positive 或探索检查不是整个候选验收；下文出现这些名字仅标注观察到的位置，未来签名和最终归属须以 M2/M3 固定候选重核，不把临时私有函数名冻结成合同。

[父请求留存设计](2026-11-16-training-cycle-parent-request-retention.md)的核心修订 `214debc739…` 已 fresh 复核／0、根限定接纳，尚未实施。本次当前文档 raw 观测为 `bf35924d01b665470fe5ba216f9e9e450162390498cff44dcdd5eb5ddb39bafe`；根说明后续仅首段状态／顺序更新，核心合同未变。本页不将新文档 SHA 当作新运行验收。完整 M1c 仍被实际留存、M1c-R/V 等未完成项阻断。

**M5 可以交付内部纯认证和原最后 gate 接线；不能独立启动新训练。** 当前没有正式 V2 producer／v3 注册，schema3 新 start 所需的真实 activity source／原 history 也不存在。M5 不增加测试后门、参数开关或伪 source 来获得“可运行正例”。保留 schema3 effect 的显式关闭；M6 在 V2、完整 M1c 与所有前置通过后，才在同一固定候选中逐点移除新版本关闭分支。旧 v1／schema1/2 永不升级。

## 现有调用、锁序与不能只改一个 guard 的原因

|真实路径|现有顺序与 M5 应落的最后认证|
|---|---|
|H prepare／confirm → `_prepare_submission` → `_Submission.main`|原 submission `.lock` 内出生完整 intent，现有 16MiB 聚合界不变。schema3 新 controller 的完整 predecessor 必须在出生前认证并原样进入 `intent.budget.controller`；confirm／dispatch 只读这份完整值。H 的原 request／prepare source 还须与它逐字段相同，不能从新 request 补一个 predecessor。|
|`_Submission.dispatch → CheckpointedClient.start_workflow`|既有 submission 锁在外，父共享许可持到原 start await 返回。父 history／namespace认证、原 child lookup、preflight、owner 检查 → 写 start attempt → 同步 → 再 preflight／source／clock／stop → SDK send。在 attempt 前及同步后、send 紧前复用同一纯前驱／来源认证；attempt 已写后失败永不删除／退机会。回复丢失只对账原 run。|
|`BudgetAdapter.create_job_if_absent → LocalTrainingAdapter.create_job_if_absent → lookup_job`|controller 路径先持父共享许可并异步核固定父 history，再进原 registry lock；原 `lookup_job` 在该锁内返回 absent 后，紧邻原 native request write。将纯认证放在该 absent 分支已有 `budget.require_active` 链中，保持原上下文变量传递和父许可到 create 返回。H 早先认证不能替代它。|
|`Execution.check → request`|check 在 DB reservation 外查固定父／子 history、QUEUED／job；父共享许可 → `execution.lock` → `current` → publish request／同步 → `current`。两次 current 都读同一完整前驱、原 source 和当前 work／stop；同步后失效时文件保持已占用，不能宣称 requested 成功。|
|`Execution.admit`|同原父共享许可 → `execution.lock`，`current` 后 lstat launch（空／partial 也占用）→ publish launch／同步 → `current`。launch 后失效不启动 execute，也不补造 ack、删除 launch 或重新 offer。等待锁只在原 work/window，不能重开 cold。|
|`native_main → patched process(..., admit=callback)`|native 先本地完整 context 核验并持父共享许可，原 `executor.lock` 内：已有 result 早读；无 result 才核 started／managed 状态并调用 callback；callback 原 unused launch 检查 → attempt publish／同步 → ack publish／同步 → 最终 active → 返回后原 started／runner。完整本地认证须在 callback 入场、attempt 后 ack 前、ack 后返回前各重读，不能只在最外层验证一次。|

实际 executor 接缝来自已有 `data/native-runtime/training-executor-admission-v1.patch`／descriptor；包内未打补丁的原283文件是历史原件，不编辑它们。patched executor 在锁内先读 result 的顺序、没有 admit 时拒绝 managed-execution、started 而无 result 时拒绝重跑，全部保持。M5 无需修改 patch 或 descriptor。

锁序保持各路径现状：submission 锁→父共享许可（start）；父共享许可→registry 锁（create）；父共享许可→execution 锁（request／launch）；父共享许可→executor 锁（native）。不让纯前驱读取再取得早轮 execution／registry／父排他锁，不在 stop 排空持有的父排他许可内调用 start/create，不新增跨轮锁序。stop 先可见，非阻塞父许可／原排空语义保持；持共享许可不是忽略 stop 的许可。

纯校验可能碰阻塞文件 I/O，仍只在原 H／S 或 native 子树中执行，不搬进 SDK loop／数据库事务，不另起永久线程。父 history 的异步查询仍留在各原消费者、原本地业务锁之外；start 的既有 submission 锁范围不因此重排。远端父 RUNNING 只能证明该次查询时刻，不能把本地共享锁说成与 Temporal 原子事务；最终本地 stop／source／clock 在锁内另核。

## 原前驱的一个本地认证算法

职责留在现有、已 pin 的 `training_execution_protocol`；这是有本地文件读取的纯边界，意思是不导入应用 State／schema／SDK、不创建或修复任何持久物、不发 RPC，不声称无 I/O。实际调用者有不同生产文件：`BudgetedStart.source`、`Execution.current`（经 `validate_context`）、worker H 的后继认证及 protocol 自身 native callback；不建新模块、proof 文件、注册表、archive reader 或 ledger。

其输入来自原 authorization／cycle raw plan／完整 candidate intent／原 capability，不能让调用者传一个新“已认证”布尔量。无 predecessor 时只在 schema3／v2 的 ordinal0 合法；k>0 必须是 wire 的完整 `{prefix,acceptance}`，k 严格 int 且小于原实际 N。schema2/v1 保持旧键集和 ordinal0，schema1 不能带 controller；未知版本显式拒绝，不用 `>=2`。

1. 先核原完整 plan raw SHA、authorization canonical SHA、ready、原注册／revision／selection，原父 intent／attempt／receipt／fixed run 和 controller protocol／queue；完整 intent 与 binding 的关系只沿原 owner 算法。ordinal0 明确 null；k>0 缺任一字段不能退成首轮。
2. 从 k−1 反向走到0，最多31份先前观察，每次要求 ordinal 严格减1。prefix 目录固定为本 cycle `controller/rounds/<j>`，仅有普通 `rounds.json`；observation 固定为该 acceptance 原 operation ID 的 `helper/observation.json`。拒绝 symlink/reparse／`..`／别根，先核实际 raw 长度和 SHA，再 decode。不可查 latest、扫描替代目录、缩成更短合法链或读取当前新 acceptance 换绑。
3. index 的 bytes/raw SHA、rounds=j+1、last content SHA、initial anchor canonical SHA 精确等 pin；复用 M1a 原 pretty content 算法和纯 `validate_round_content`。逐轮核原选中 experiment、完整 manifest／spec／binding、annotation、project／registration、原 revision、完整 `_COMMON` 与 anchor。后一 index 的 `rounds[:-1]` 必须逐值等较早原 index，`previous_report` 三字段核较早 raw SHA／count／last，最早 index 的 previous_report=null。仅核最后一轮不能保护最早轮篡改。
4. 读取对应前轮原 start intent／attempt／receipt（intent 仍沿16MiB界），核其完整 SHA／run／spec 和原 controller／父 run。观察 predecessor 必须等这份前轮原 intent 中的完整 predecessor；再沿它进入更早一轮，不沿调用者自行声明的另一链。每份原 H request 的完整 identity／snapshot／activity_context、原 collect/reconcile mode／source／namespace、helper 成功结果中的 accepted／durable 投影也必须绑定同一观察／prefix／acceptance。当前后继已出生 intent 永不因 reconcile 新观察改写。
5. 验证 acceptance 恰等从这份完整 observation、ref、原 intent 推导的原 wire 投影；核 candidate／submission／runtime／evidence／common／measurement 全字段，不仅核 digest shape。runtime status/outcome 的历史分支沿原四事实谓词：status 的 evidence_sha 和 outcome 的 report_uri 各用其真实字段；不编造字段、不把历史 phase 当当前执行许可。
6. 用 `ExecutionRecords` 重读早轮 owner、五个 records、原 start／native request 的完整 raw inventory，等观察中的原 inventory／各 semantic SHA／owner；要求原 durable stopped／executor stopped 证据齐全。早轮 owner 已退出是正常情况，不对早轮调用 live-owner 判定，也不重跑 executor。同步／重读沿原 `observe(durable=True)`，其既有保证是 fsync＋相同 raw，不能冒称整个旧链已同 inode 原子快照。
7. 早轮 `evidence.files` 的**完整原映射**与 observation／index／acceptance 的绑定全部保留；将其中每个 `state/`／`config/` 路径按原已冻结 execution 根和现有 safe-file 边界重读原 raw SHA，禁止任意绝对路径。ExecutionRecords 的 absolute inventory 也须由该实例真实 `originals` 的完整键集生成并精确比较，不能让 observation 授权任意文件读取。共享原 raw 读取／SHA算子；这里只验证既有 inventory 的当前字节，不重新实现 archive eligibility、baseline_ok、artifact 内容或比较器。原 optional ticket／approval 不改写历史观察、不产生新批准。
8. 最后核本轮原25 capability、出生四 measurement sources、包内 ROOT、所选安装、当前父 stop、原 BOOT／work／operation window；跨上述读取的时间都消费同一原预算。对早轮 capability 也核其原25表，不能新生 owner 换 source。文件缺失／partial／任一漂移或超时均拒绝当前动作，原件保留，不能用“当时已经 accepted”豁免当前再认证。

H 额外继续沿原 evidence owner 重新 inspect 完整 archive 语义，并认证父固定 run 的 RUNNING／namespace／完整原 history；紧邻前轮按原 M2/M3 合同认证当前可接受 phase。更早轮只核其冻结历史及当前原文件，不强迫其仍停在旧 phase。native **只**验证冻结当时事实与当前本地文件／来源／stop／clock，从不导入 SDK 或查询历史 phase。H 的正面结果和 native 的本地拒绝可以先后发生，必须由最后 gate 拒绝真实动作。

native 对 evidence.files 做原件身份复核不等于第二 archive reader；若实现发现需要重新调用 perfctl.baseline_ok／archive comparator 才能成立，应暂停此部分，单独设计原 evidence owner 的纯化前置，不能在 protocol 复制语义。对合法公开 release 后新增但未在历史 inventory 的文件，不扫描并升级旧观察；当前 fence 等实时 veto 仍按原 native/source gate 单独处理。

## 容量读端与纯代码归属

`ARTIFACT_LIMIT=10_000_000` 唯一；index／observation ref 每个读端都显式 `read_raw(path, ARTIFACT_LIMIT)`，ref.bytes 必须严格 int、`0<bytes<=M`，实际完整 raw bytes／SHA 含 observation 的末尾 LF。M−1/M/M+1 以原最终编码核，不用字符数。默认1MiB若漏接会错误拒绝合法大观察，读取短前缀后比较也不合格。原 intent16MiB、H request／stdout32KiB及原单文件各自界保持；不把所有 read_raw 默认改成10MB，不给 evidence 的每个字段另加更小配额。

M2 暂定 protocol 已有 shape／ref reader；这只是只读表达能力，不是执行 gate。M5 不再新增相同 wire parser，而在固定上游后复用并补本地来源与全链认证。原 round schema 验证仍归 training_rounds；native 不 import training_rounds（其顶层有 contracts/training/State 和 schema读取）。native 对 H 已 schema 验证、原 raw SHA 绑定的 index 使用同一个 M1a 纯内容验证；任意调用者制作一个“自洽 JSON”仍必须通过原 source／receipt／observation／全链认证，不能凭 content SHA取得 origin。

**先审纯化必要性，再决定是否有独立 M5-P 前置片。** 固定 M2/M3 后，将已存在 worker 本地 report binding、四事实纯判定和 acceptance 投影中确实可纯化的计算与 protocol 实际已有消费者逐项核对。只有确认两个现存不同生产文件确实调用同一计算、并能保持原行为，才单独提取到现有 protocol，所有原caller一起迁移；未来 M5-G 的 verifier 不是尚未存在时的第二caller。只有worker一个现存消费者时，不先落一份无人复用helper，直接在M5-G接真实native消费者时内聚迁移，并把机械迁移与新增认证的diff分块供审，不把整片称为行为不变。保留 worker 的 State／SDK／archive采集／publish／fsync 编排，不把 `_round_previous` 整段搬过去。独立M5-P不扩版本、不改变状态分类／异常／raw／格式／窗口；若上游固定产品已归protocol，则删去此片，不为分片再造包装。

## ROOT 与来源：复用实际纯 owner

静态核到 `reference.verify()` 的顶层只有 stdlib、`processes`、`reference_creation_process`；后二者实际顶层也仅 stdlib。`training_execution_protocol → reference → 两者` 当前不导入 State/jsonschema/YAML/Temporal；参考模块其他函数中的局部应用 import 不在 verify 这条调用路径。以上三个文件连同 protocol 均已在原25 GATE_SOURCES，manifest 也已在表内。因此**直接复用 reference.verify，无需新文件／复制manifest walker／新增第五 measurement source／本轮 reference 纯化**。实际隔离导入仍须在固定候选／安装包运行验证；若未来上游引入顶层 State，先单独提出两个真实 caller（reference.verify 原用户入口与 native gate）的行为不变依赖整理，不能让 native 临时 fallback 到复制算法。

顺序必须是：严格验证原 capability 的25项恰好键集和原 hash → 明确核其中 `data/reference-manifest.json` 的当前 raw SHA 等**这个原 owner 出生值** → 同一已 pin reference.verify 对它列出的全部原283字节核验 → 最终重核 manifest/source／stop／clock。绝不从当前 info／新 manifest 采一个 hash 当原值。H 首轮接受所用的 capability 来自同一原 candidate owner。必须区分出生时刻：schema3 authorization只pin四measurement项，ready也没有25项或manifest hash；原25／manifest是在原 `BudgetedStart.own → source_capability → owner.json` 一次出生时固定，不能谎称授权瞬间已固定。prepare intent时本轮owner尚未出生：k>0可核此前原owner的capability与ROOT；ordinal0在原source_capability出生前仅能核固定产品、四项source、原所选安装descriptor及其base-manifest与包内ROOT当前一致性，不能伪造不存在的“授权manifest pin”。这一步不授予效果；原owner出生并同步后，所有start/create/request/launch/native最终动作必须核本轮原capability的25／manifest固定值、ROOT及四项sources。source_capability采值只沿原一次owner出生，不在retry／恢复重采；实际M6验收要覆盖这段先后，不能从ready推导不存在的pin。

`reference.verify` 仍负责原 ROOT 文件内容；原 safe/open 路径规则负责 artifact／manifest 普通文件／祖先无链接的边界，不把 verify 的 `is_file` 说成完整目录抗替换或持续原子保证。若固定候选发现 reference ROOT 目录安全规则与原 source gate 不一致，应在原 owner 提出明确最小修正并独立验收，不能默默承诺 verify 本来没有的保证。所选安装仍另调原 `validate_installation(training=True)`、descriptor／overrides／native interpreter/core/config/state 身份；检查所选安装不能代替包内 ROOT283。

四项 measurement 精确沿出生映射：training_rounds、reference_training_evidence、rounds schema、reference_training_release。所有现有 source 读取复用 protocol raw/SHA／原 training_cycles birth算法，不新增可配置路径表。M5-P/G 会改变已有25中的 protocol／worker／budget／execution／submission，以及可能的四项中的实际 owner；新 candidate须重新出生并冻结这些**现有键的值**。不补写旧 authorization、capability或owner；owner1/2 reader不能为新字段变成宽泛兼容。代码升级后的旧历史可按旧原件只读，不能拿新当前 source 重授旧执行权。

## 从只读 binding 到 effect 的明确开启表

|位置|M5 内部交付|M6 最终开启前必须另核|
|---|---|---|
|binding／CycleAdmission.bind|schema3 精确六字段、null/完整前驱、所有 source/receipt/selection认证；schema1/2不变|禁止删成统一宽松 controller parser|
|H `_cycle_operation`、source/root/phase validators|只保留已接纳 collect/reconcile 内部入口；后继原 source认证可接线|新 start/confirm/dispatch/request/observe-v3 operation-v2 精确 names／type／queue／source，原32KiB request／retention闭合|
|BudgetedStart.source/context/permission|所有 schema3 caller均到同一严格 verifier，随后 effect关闭仍拒绝；无新授权方式|移除关闭时确认 start、owner、late create、request／launch全部走它；手工binding仍失败|
|validate_context／Execution.current／actor选择|本地完整前驱与四项/ROOT认证接入；live=False不变成执行后门；schema3 effect关闭仍拒绝|每个 `==2` 按显式(2,3)语义逐点改、actor取原controller.actor_id；未知版本仍失败|
|native 外层permit／callback／attempt／ack|同一校验在实际旧gate接线并保留schema3拒绝；callback各持久点重读|外层schema3也持原父permit，callback完整阶段校验可达；完整M1c-R＋V2来源后才允许新效果|
|Workflow／活动注册／公开入口|本片不改旧命令、旧类、旧activity或添加注册|M6正式V2、完整converter/Memo/inbound/query/signal/outcome及真实history；公开CLI另归原后片|

执行关闭不是一个可以跳过的装饰分支。M5 的 schema3纯正例只认证给定原件可通过本地边界；schema3 start/native 的正面真实效果须留M6统一验收。若希望 M5 当片真启动 schema3，必须扩大范围同时交付 M6和全部M1c，不能以“只内部使用”豁免。

native callback 局部终点需刷新链再复用 validator：入场要求launch已消费但attempt/ack/stopped均不存在；写attempt后的校验允许**本次刚写且完整相同**的attempt、仍无ack/stopped；写ack后只允许本次对应ack。重校验不能反复调用“unused launch”入口而错误拒绝自身进度，也不能放宽成任意已有attempt可恢复执行。任何阶段失败都保留已有记录，不删重跑；ack存在只表示原局部ack，不能承诺runner已执行。最终校验在ack同步后、callback返回前，仍在executor锁与父共享许可内，紧邻原started；既有result早读不受新增执行准入阻断。

## 最小 diff 与现成 seam 验收矩阵（均未运行）

预计 M5-P 只需 protocol＋worker与原fixture/测试；M5-G 主要为 protocol、budget、execution、worker adapter、submission最后start门禁，另按固定上游实际 source/context validator最小补差。reference.py、rounds、schema、native patch／descriptor／283资源、State表、runtime SDK认证不预设有改动；若需改变既有合同须先单列原因。测试留现有 `test_training_submission.py`／`test_training_runtime.py`、`fixtures/training_cycle_operations.py`，不建文件／CI job。M5不把未用函数先落地；提取与所有调用点一起迁移，删除重复本地算法。

|可达风险|保留的真实序列／最小证据|实际认证 scope 与延期|
|---|---|---|
|纯提取改变旧分类／SHA|原 M2 collect/reconcile 完整正负原件，原离线round read/create、pretty/content SHA和现有固定输入差分|M5-P行为不变检查；不重跑无变化训练/全suite|
|current0与多轮完整前驱|原controller_admission／cycle_selection＋M2真实H已保存原件；ordinal0 null；k=1与至少k=3全链认证，后者篡改最早轮仍拒绝|纯边界schema3 positive与真实H只读；实际新start成功延期M6|
|换绑／伪造全链|同原件交换acceptance/ref、错父run/namespace/source operation、早轮intent predecessor、annotation/common/revision/registration、raw SHA／previous_report；校验后再重写早轮|在真实最终gate拒绝后观察无send/create/request/launch/ack/started，按阶段允许已占用attempt/launch；不是只测shape raise|
|1MiB／10MB真实reader|M2保存的合法完整观察>1MiB，经H/budget/context/native本地gate各真实caller读取；最终编码M−1/M/M+1、多字节LF及合计越界|M1c-R只在实际可达reader关闭；M5尚关闭schema3 effect的路径只能认证拒绝／本地读取，M6补正向actual action，不能称已完整关闭|
|start attempt同步后来源失效|扩既有 `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync`；真实S/H、原attempt fsync后改前驱/measurement/ROOT或耗尽window|原attempt保留、无SDK send；父RUNNING／namespace/history服务替身与真实SDK converter范围分开|
|晚到create／其他SDK调用|沿 `test_cycle_start_returns_before_automatic_fence_blocks_a_late_native_create` 与原 registry 序列，延迟拿registry锁后改源/stop/clock；调用BudgetAdapter原create而不走新活动|无native request；原既有job早读保持，不靠新的Workflow guard；独立调用所选未受管adapter不称本系统授予执行权|
|request/launch同步竞态|沿 `test_cycle_sdk_execution_last_sync_gate_keeps_its_window_and_source`、`test_execution_admission_waits_for_the_original_request_writer`、`test_explicit_execution_consumes_one_launch_even_if_no_process_starts`|真实execution锁／publish／fsync，后检查失败保留记录，无execute spawn／再launch；旧schema2正例保持|
|native attempt→ack→runner缝隙|沿 `native_executor`、`test_native_admission_holds_the_original_lock_and_rejection_has_no_business_result`；真实patched executor，在attempt同步和ack同步后分别改前驱/源/stop/clock|前者无ack/started，后者ack保留无started／runner；原锁确实held，callback拒绝不造业务result。schema3完整正向effects留M6|
|BOOT／work与stop竞争|原budget_clock进程局部故障接缝覆盖BOOT变、UTC倒退/前跳/drift、work耗尽；真实同步阻塞／stop可见后最终检查|复用原完整remaining，不造新clock矩阵，不把async cancel代替同步最后检查；共享permit排空/清理reserve保持|
|来源漂移／ROOT错装|四项逐个、原25中未在当前快捷路径的依赖、manifest改后内容自洽、包内单个ROOT文件与所选安装分别错配|原pin拒绝；装了所选正确安装仍不得掩盖包内ROOT坏字节；source字段缺项/额外项拒绝|
|恢复／fsync／丢回复|复用M2 fsync/partial/reconcile原件、原lost-reply与occupied launch seam；重启只读已有链，新acceptance不得改已出生intent|不create index、不退start/request/collect机会、不补ack/stopped/换UUID；available/unknown按实记账|
|隔离和旧历史|沿 `test_execution_history_is_sdk_free_and_survives_missing_installation`、native `-P -S` stdlib路径／真实hook、原schema1/2和owner1/2；原v1三份history按影响回放|隔离检查实际拒绝State/jsonschema/YAML/Temporal import，不能mock validator成pass；只读history缺安装仍可读，执行source严格拒绝；M5本设计未replay|
|源码与新安装差异|固定候选新非editable core/SDK包原checks、实际site-packages、source/ROOT pin与上述重点锁/reader检查|源码/安装/服务替身/真实SDK现场/两轮CPU各自记账；不继承M1b或c1c的验收，不认证GPU/质量|

所有故障注入须在原fixture的真正阻塞／同步点发生，保留真实锁、fd、S/H/reaper和callback；不能只 monkeypatch返回“accepted”。同一可达失败不按每个helper再做重复矩阵；不测试文案或把源码行数当合同。M5-G完成须新fresh两轴审查并记录准确patch/来源/检查；重大交付的原自身模板与安装验收沿根流程，本文不执行。

## 下一片建议与开放风险

最小下一片是**等待M2/M3固定审查候选后重核差异，先决定是否确有M5-P行为不变双caller提取**；不提前改当前M2源。确有现存双caller时才单独提取并迁移，验原结果差分及真实native隔离，独立审后再做M5-G；否则最小完整下一片为M5-G，纯算法随真实caller一起落地。M5-G必须同时接全链、来源/ROOT与每个实际最后动作，不能以只改`BudgetedStart.source`作为完成。

主要风险是全链I/O放大耗尽同一窗口、旧inventory或合法release状态随时间变化导致保守拒绝、同步后source/clock/stop失效、临时shape误当origin、native callback中自身attempt阶段误判，以及M6缺席时虚构“新start可用”。不缓存“已验前驱”跨动作，不减掉早轮原件来省时，不加窗口解决成本。source/manifest逐文件检查并非对敌对同用户并发改写的原子filesystem快照；保持既有可信用户边界，不扩称OS隔离。

本页仅给可审实施方案，M5-P/G、完整M1c、V2及真实两轮仍未完成。只有全部前置与M6同候选终核通过，才可移除**新版本**的关闭分支；旧历史的首轮边界、原六阶段、attempt-before-send、unknown-only恢复、已有result早读与原人工release窗口永久保持。
