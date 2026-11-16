# M6-V1 正式 V2／v3 表达片独立源码审查

2026-11-16。Reviewer：fresh-context 独立代理 `m6_v1_expression_review`；未参与实施，先读原始范围和源码，再读作者交付。应用 maintainable-project-delivery 的 independent-review brief，以及 ergora-codebase-quality 的 module-design／test-seams。初始唯一写入为本报告；根后续明确授权将 R1 的同一 probe／精确 argv／原始输出另存本片 `source-review` 私有目录。不修改源码、测试、PLAN，不安装、不运行服务／模型／网络，不提交或推送。

|审查轴|最终结论（final-r2）|开放 finding|
|---|---|---|
|需求符合性|**approve，仅限下述准确表达片及适用验证**|0|
|结构／维护性|**approve，仅限下述准确表达片及适用验证**|0|

首轮 final-r1 的需求结论为 request-changes（R1，P2），维护性为 approve／0 个独立结构 finding。根完成最小修正、重新冻结并补齐新安装及原模板后，独立终核关闭 R1。可以关闭 **M6-V1 正式 V2／v3 表达片**；这不认证 V2 服务、schema3 执行开放、完整 M1c、真实 CPU 两轮或 GPU／训练质量，不把 M5/native 的闭合转授本片。

## 范围与准确身份

权威范围为 [M6 设计](../plans/2026-11-16-training-cycle-v2-runtime.md)、其 [fresh 静态审查](2026-11-16-training-cycle-v2-runtime-design-review.md) 的 **V1 正式 V2 与 v3 表达** 分片，以及 [PLAN](../PLAN.md) 的当前职责。另读根／src／tests AGENTS、组件协议的定义／执行证据／检查分支及 measurement-wire 的精确 envelope／status／原机会合同。作者记录为 [本片交付](2026-11-16-training-cycle-v2-expression.md)。

候选隔离树 `.ergora/worktrees/training-cycle-v2-expression`，分支 `feat/training-cycle-v2-expression`，准确 HEAD／baseline `bc58be6781d35e7e4fbd54ad997df8a4743428a8`。实际 Git 状态只有下列五个未提交文件，无 untracked；没有把根的 PLAN／交付差异计入产品。

|所审文件|final-r2 raw SHA256|
|---|---|
|`src/ergora/reference_training_runtime.py`|`b8ed226f24c54a16f292a23567c5e36b47fd165b3922ac331bc8083570c9fd70`|
|`src/ergora/reference_training_worker.py`|`80079d2774aba09e4894308d594d1d2cd487109c913aafe9dc2c391be0029fe3`|
|`src/ergora/training_execution_protocol.py`|`573366d01ed271ddd544235cf16886faa2d569f3870e079808b64d40e441d073`|
|`tests/test_training_runtime.py`|`400f8e56b5fcf834584a99218407f00b64bb4dd3850b95d7f0c9263b5c14f430`|
|`tests/test_training_submission.py`|`f996f3153862499a02da1284e0bcab674c6ae6cfc1ceaa6c6313845b165b2bc3`|

最终实际 `git diff --binary HEAD` 的 82,225B 与 `final-r2/source.patch` 逐字一致，SHA256 `b871eb2bec5bc09c63f758f0771d6cfccb05d967e2050d18e5bf20196a69c23e`。实际完整 manifest 为 `{baseline,files,untracked}`，其中 `files` 是路径到 `{bytes,executable,sha256}` 的映射；未预设 list 格式。final-r2 `complete-input-manifest.json` SHA256 `610ab4bbef44cc9e6adc011697b09fe60275a52e185d191d511fdd4edee45328`，2019 项与真实 tracked 集合、每项字节／执行位均一致，untracked 为空。最终仍是准确 bc58be6 上的五文件未提交候选；本审不声称已提交／导入。

首轮 final-r1 的 82,059B patch `9d3d72501e0fd9170d5378b27205dccf3d5a5f3a79755c4e7d3e5e695e0e54fe` 与 manifest `38233007dc3ec025e8b74131da7060f52c1c4aa85d296c8f205596d240f3f641` 已先独立核同一；其 worker SHA 为 `bf07f39a1ce5b9ec4eac47bc84d2527be4dc260021b20ef01c47b057cb4bb83c`，其余四文件与上表相同。原身份／原失败及原运行成绩保留，不改写成 final-r2 的运行结果。

## R1（P2，已关闭）：新增正向 SDK 用例与消费端的路径表示不一致

位置：候选 `reference_training_worker.py:2261–2263`、`tests/test_training_runtime.py:1038–1043`；CI 可达入口为 `.github/workflows/portability.yml:36,61–64` 的 Windows `all` job。该 job 安装 temporal extra，新增正向 SDK 用例未被跳过。

真实 H 的目录 owner 使用 `Path`：`_round_operation:1231` 取 `admission.folder / 'rounds' / str(ordinal)`，`:1288` 用 `state.root / 'operations/training-cycles' / operation_id / 'helper/observation.json'`。新 fixture 也用本机 `Path` 形成这两条引用；首轮 Workflow 却用 `rstrip('/')` 加 `/...` 的字符串拼接做精确相等检查。因此 Windows fixture 的 `C:\training-cycles\demo\first\controller\rounds\0` 与首轮消费端的 `C:\/training-cycles/demo/first/controller/rounds/0` 不同；observation 路径存在同样差异。合法 accepted 合成结果会走 observation rejection／stop，正向两轮、丢 collect completion 后推进和跨轮预算等用例不能保持其预期。

轻量复核在独立 `-B` 解释器直接调用真实 V2 `_consume`，仅以 `PureWindowsPath` 代入路径验证／fixture 构造语义，其他完整合法 facts 保持：原 Windows 形式抛 `Round acceptance differs from the complete current candidate facts`，confirmed=0；仅将上述两条字符串改成消费端的拼法，同一 facts 得到 confirmed=1／ordinal=1。此为纯路径／消费接缝复核，**没有运行 Windows 主机或声称 Windows 正式训练执行受支持**。

根已在现 owner 用 stdlib `PurePath` 按 H 的相同组成规则纯拼接两个 expected path；不读文件、不增加 helper／validator／抽象，保留原精确绑定检查及正向用例，没有新增 Windows skip 或扩大正式执行支持。同一私有 probe 已在旧包得到红／控制绿，在修后源码及新非editable包得到绿，详见最后一节；R1 关闭。

## 需求符合性与可达效果边界

除 R1 外，所审源码未形成另一项可达阻断：

- 新顶层 `TrainingCycleWorkflowV2` 在原可选 SDK owner 内，工厂封闭选择 1／2，拒绝 bool 和未知版本；v3 七活动及 normal／stop queue 分明。request／context／operation 按原授权或已验 cold context 严格路由，schema／protocol、namespace、type、queue、attempt 和完整身份继续核对。原运行 `_serve_cycle` 缺省仍只注册 V1，不能称四 poller 已交付。
- 三机会均在 `start_activity` 前占用。collect 固定 `candidate-<k>-collect`、retry maximum_attempts=1；丢 start／request／collect 回复不返还机会。wrapper 将重投 start／request／collect 分别转到 reconcile／observe／existing-only reconcile；runtime scanner 对固定父 run 完整 decode 唯一 collect 和当前 scheduled command，新 retry 分支保留原 collect source。后继保存前一次完整 predecessor，不从新观察替换已经出生的 intent。
- consume 先量完整 received envelope，再核严格形状、固定父 run、本次完成的 operation、当前 ordinal、原 candidate／submission／五记录库存、selection 三值及 measurement 接受关系。只有 observed／accepted／durable／ready 的完整正面值推进。N、累计计数、已确认 prefix 和本轮三机会分开保存；跨轮仅重置本轮状态，原 BOOT／work／total 截止仍取 min，最后 ordinal=N−1、confirmed=N。
- 原 H 的广泛 schema3 拒绝收窄后，read-only 包含原 receipt 对账保存、执行链 fsync／同步和观察文件写入；它并非完全无存储副作用。这些仍由原 owner 持有，未发现 dispatch／create／request／launch／native 或 stop 通知经只读 mode 获得新机会。prepare／submit-controller、三个 start mode、request-execution、stop-writer／notify-owner 均在实际 H 保持明确关闭；`_controller_ready`、budget.source、validate_context／native 最后关闭门未被开放。collect／reconcile 保留 M2 的索引及观察语义，reconcile 目标缺失仍不能 create。
- V2 stop 仍只发唯一独立 stop queue command，保留原清理等待；cycle-level 三个 stop 证明保持 null。它不把 H stopped、SDK 取消或 Workflow 终态改写成 executor durable stop。

本片没有完成四 poller／两配额、完整 M1c 的 Memo／最终 Failure／所有晚处 reader 正向、schema3 真实出生执行、真实 CPU 两轮或 GPU／训练质量；作者记录没有把这些填成通过。父 M5/native 已由根普通导入 1308e32 的历史事实只作为准确基线依赖。

## 结构／维护性判断

新类的必要性来自 SDK 顶层重导入及旧 history 隔离；继承复用原 `_capacity`、`_guard`、原预算收窄与候选事实校验，没有新产品模块、ledger、通用 validator 或可替换实现总线。生产路径仍为 service → 原工厂／wrapper → S/H → 原 submission／runtime／rounds／evidence；原 native stdlib owner 未引入 SDK／State。

独立 AST 比较确认旧类除 `_consume` 外的原方法全部一致；提取的 `_consume_facts` 等于原方法校验尾段，仅把 ordinal=0 参数化，V1 仍显式传 0。`_serve_cycle`、`native_main`、`validate_context` AST 一致；原 source 表与 effect gate 文件没有借本片更改。版本专属 command／envelope 留在各自类，当前没有足以要求再提公共执行抽象的调用义务。

新增 guard 对应外部 envelope／source、持久身份、原机会或容量边界，未发现无消费者的防御层。14 个 source／attempt 接缝覆盖七个真实活动模式的差异；实际 S/H 关闭与 oversized 请求留存保护本次放宽的入口，不能只由 helper 模拟替代。N2 是所供配置；独立轻量 SDK activation 对 N=1、3、32 分别得到 (ordinal,confirmed)=(0,1)、(2,3)、(31,32)，累计 ordinary=2N。未发现为满足测试而固定有效 N／预算为默认值的实现。

## 原 final-r1 记录与审查限制

实际只读核对 `final-r1` 的精确 argv／cwd／显式 PYTHONPATH、JUnit、原始 stdout／stderr、source／input manifest，以及 replay/core 原件：

|原记录|独立核得的范围|
|---|---|
|`runtime-final.command.json/xml/stdout`|80 tests，0 failure／error／skip；JUnit 59.981秒、stdout 59.99秒；195 份 actual-owned PID／BOOT／start 记录，原检查均 absent|
|`submission-final.command.json/xml/stdout`|8 tests，0 failure／error／skip；JUnit 93.218秒、stdout 93.22秒；189 份 actual-owned 记录，原检查均 absent|
|`replay-core-final.command.json`|returncode=0；5 份 actual-owned 记录，原检查均 absent；三条命令合计389份捕获记录，不宣称全系统零残留或389个独立进程|
|三份 V1 history|78／45／46 events；82,086／44,640／48,561B；raw SHA 分别 `dc7d9587…`／`3a5d086c…`／`1e9310ce…`；原默认 Replayer／eviction 记录为0退出|
|`core-no-sdk.json`|独立解释器主动拒绝 temporalio，三 owner core import 成功，新工厂明确报告 optional SDK 不可用；非 native 全链或真实执行通过|

上述是原记录核对，未重跑昂贵 suite；早期探索／原失败不转成冻结候选验收。独立执行仅 Git／SHA／AST／文本检查、N 变化的轻量 SDK activation 和 R1 的纯路径／消费 probe，均未写测试或运行现场。Linux 上尝试直接为 sandbox 换入 Windows 路径时，原宿主路径校验即拒绝，未把这种模拟计为实际 Windows 运行；R1 的结论来自实际字符串构造、CI 可达性及后续纯方法接缝。

根新增的 package-r1／self-review-r1 仍只对应首轮 9d3d7250 候选：旧安装80＋8、旧 wheel `2df00b82…`、原模板81.715秒 approve 保留原范围。它们没有被转授 R1 修后的新候选。修后只重跑受影响接缝；H 路径未变的8项不为状态记账重复运行。

## final-r2 修正与源码／安装／原模板最终复核

根在同片只增加 `PurePath` import，并将原 root／两个 expected path 改为相同 owner 的纯路径拼接。独立与 package-r1 中的原 worker 全文件比较，差异恰为该 import 及三行路径表达；未改其余逻辑。新的五文件 patch 为 `b871eb2bec5bc09c63f758f0771d6cfccb05d967e2050d18e5bf20196a69c23e`，worker raw SHA `80079d2774aba09e4894308d594d1d2cd487109c913aafe9dc2c391be0029fe3`。

根要求保存可复跑原件后，独立 reviewer 在保留的旧非editable package-r1 SDK 上重新得到真实红例：使用 `-I -B`、不插入源码目录，三 owner 实际均来自旧 `site-packages`，raw SHA 与首轮 manifest 相同。native Windows owner 形式 rejected／confirmed=0；仅改两条 facts 为旧 literal 拼法的控制组 accepted／confirmed=1。脚本按正确合同断言，实际退出1。随后同一脚本显式选 final-r2 source，native 形式 accepted／confirmed=1，旧错误 literal 反而 rejected／confirmed=0，实际退出0；没有削弱精确路径绑定。

私有原件：`.ergora/checks/training-cycle-v2-expression/source-review/path-consumer-probe.py`，SHA `70c0b32fc7dbec36a2697c062d077189b3a2bc9b883c33843949be2da9326ebc`。精确命令、原始 stdout／stderr 分别为 `path-r1-installed.command.json/stdout/stderr` 和 `path-r2-source.command.json/stdout/stderr`；命令记录 SHA 分别 `2c5011fcbc56328d8b818d8c8174270246171ccc4fae141cbb2b48d13b818f7b`／`31acee9c54d2af2c52638b95ba1cb55ccce5da6725f8ca604dcb63b2f6447af0`。这些 probe 仅为纯路径／消费接缝，不是实际 Windows 运行或执行开放。

根最终补证后，独立核得：

|final-r2 原件|最终核对结果与实际范围|
|---|---|
|`final-r2/source-v2-affected.*`|准确原 argv 选择 `cycle_v2 or cycle_v3`；25 passed，JUnit3.160秒／stdout3.16秒，0 failure／error／skip。不是修后全80项或H8项的新运行。|
|`package-r2` 新非editable core／SDK|wheel SHA `8574ebe644804c0bebd869caed4e06e47c1757116e161db42f94dd3e2bb48fbf`。独立逐项比较665个源码／wheel／core／SDK文件，名称集合、raw字节、执行位及记录SHA完全相等；三 owner 实际导入均为各自site-packages。854项构建输入、179项复制tests／examples与原源文件／副本的字节和执行位也一致。原283参考及两边依赖检查0退出；core无SDK，SDK1.34.0。|
|新安装25项及同一R1 probe|实际`-I -B`、去除源码PYTHONPATH，在复制测试目录运行。25 passed，JUnit6.066秒／stdout6.07秒；安装probe0退出，三owner raw SHA与final-r2一致，native表示通过而旧literal拒绝。`installed-windows-path-probe.*`记录仅为Windows路径语义模拟，非Windows主机运行。|
|新安装三份旧history／core|三份原history的完整raw SHA／长度与原件一致；安装SDK `-I -B`代码不插入源码目录，全部默认Replayer／eviction0退出。安装core真实缺SDK，三owner导入成功，新工厂明确报告缺optional SDK。|
|`self-review-r2-codex` 自身原结构模板|原`ergora-structure-review/1.0.0 → root/review`、3份祖先资源，actual Codex、requested Claude及回退原因分别保留；没有声称异后端成功。10个完整文件683,081B和准确五文件patch均与源相等且完整进入实际771,343B stdin，SHA `341e70d9f96c53537f784fbf8a92acfc382d7cc54aa73487ff70403f5c8cd640`。原result与protocol result相等，SHA `5a9d21109692301fd2d4dab7119511e6c28bcbae8d4c79b4649c63056695b685`，76.9076秒approve。它仅为supplied-text结构审查，不替代本独审或运行验收。|
|最终freeze／实际资源|`final-freeze-resource-check.json` SHA `77ad0fa0368885fd6985c53c2839451f47439e886f78e1208a67f3aefc21ff14`。本审复核完整2019输入及patch同一、`git diff --check`无诊断；106个worker函数无增删，R1→R2仅`TrainingCycleWorkflowV2._consume` AST变化。4条新命令合计8份实际捕获身份；本审再按PID／BOOT／start逐份检查，8份均absent，不宣称全系统零残留。|

首轮代码审及新候选的上述证据共同关闭 R1，需求符合性／维护性均 **approve，开放0**。没有后续源码或测试变化；后续固定提交／普通导入由根处理。下一片仍为原服务拓扑／完整M1c及统一开放候选，真实CPU两轮另片；本结论不授予这些后继通过。
