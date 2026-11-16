# M6-V1：正式 V2／v3 表达片

2026-11-16。M6-V1表达片最终独立两轴approve／0，准确固定2acdcc4并普通导入f9b9d72；联合安装／发布另验。严格保持 schema3／ordinal1 的真实执行关闭，本片不认证完整 M1c、四 poller 或真实 CPU 两轮。

## 身份与授权范围

隔离基线 `bc58be6781d35e7e4fbd54ad997df8a4743428a8`，唯一父 M5r7 `5bcecf37b615e3708ceb08acc329ba3dd0470f4a`；该依赖的最终联合 fresh 终核由根单独完成，不作为本片已通过前提。分支 `feat/training-cycle-v2-expression`。主开发树与原作者／fixed 树均不改。

权威 [M6 设计](../plans/2026-11-16-training-cycle-v2-runtime.md) 与其 [fresh 静态审查](2026-11-16-training-cycle-v2-runtime-design-review.md) 仅批准分期设计。旧设计关于父留存／M5进度及 D1–D4 未答属历史；当前状态以 PLAN 为准。使用 maintainable-project-delivery、ergora-codebase-quality 的 module-design/test-seams；已读根、源码、测试规则及组件协议。

## 最小实现与 owner

- `training_execution_protocol.py`：封闭的新 Workflow／queue／七活动映射；严格 v2 request/context 和 operation-v2，按已验 cold context／原授权选择，拒未知版本。旧缺省、旧 request 和 mode 语义保持。
- `reference_training_worker.py`：新顶层 `TrainingCycleWorkflowV2`；完整 facts／selection／measurement 消费，真实 N，三机会命令前占用、唯一 collect ID、丢回复只对账、同 BOOT deadline 只缩。旧类正文与生产 `_serve_cycle` 缺省保持 v1。工厂可显式返回新类／v3 活动；wrapper 复用原 S/H、candidate、stop、converter、failure、锁和 reaper。
- `reference_training_runtime.py`：复用现完整 scheduled history／decode owner，按实际受控 SDK 接缝暴露的缺口做最小修正，不建第二调度器／账本或 archive reader。
- 原 `_controller_ready`、`BudgetedStart.source`、`validate_context`、native callback 的 schema3 关闭门不开放；原 25 source、四 measurement、ROOT283、immutable v1 资源、旧授权／owner pin 不改。

## 验证矩阵

沿现 `tests/test_training_runtime.py` 的实际 SDK activation harness、`tests/test_training_submission.py`／`fixtures/training_cycle_operations.py` 的真实 operation 接缝：严格版本／源与 attempt>1 只读，N2 合成受控事实的有限推进与三机会、丢完成／迟到／漂移、完整 received envelope 容量，实际 SDK scheduled event／converter 的唯一 collect 对账。原 v1 三份 history replay、默认 sandbox 重导入及 core 无 SDK 导入分别记录。配置关系按传入预算／N推导，不扩原时限。完整 M1c 与真实 CPU 不由这些本地接缝替代。

## 逐步状态

1. 已建立精确基线隔离树，核实真实 caller：原 service → 工厂 → activity wrapper → S/H → 原 submission/runtime/round owner。现 operation-v2 仅 measurement modes、SDK 工厂仅旧六活动、旧 Workflow 只 ordinal0，是本片实际缺口。
2. 开始源码实施前已向根说明上列文件、guards、复用接口与验证矩阵。原依赖终核、新非editable安装、自身模板、新 fresh 评审及最终合入由根续接；实施者不自批。

私有证据由根指定检查目录保存：完整 tracked／untracked 源 patch、全部输入／mode／命令、JUnit、原始 stdout；原失败和修后分别保存。无安装／网络／模型／commit／merge／push。

## 实现候选与效果边界

候选仅五文件：原 worker／protocol／runtime，加原 runtime／submission 两个测试文件；没有新产品模块／ABC／ledger。原 2019 tracked 输入完整冻结、untracked 0，五文件 patch SHA256 `9d3d72501e0fd9170d5378b27205dccf3d5a5f3a79755c4e7d3e5e695e0e54fe`。V1 除 `_consume` 改调共享原事实校验（固定 ordinal=0）外，其余原方法 AST 均同一；实际旧 command 由下述三份原 history 重放核对。生产 `_serve_cycle` AST 同一，缺省工厂仍 V1。原 budget/context/cycles 文件、25+4 source 表及283参考 manifest 保持。

新类继承原 class 的容量／原事实语义／guard，另持有有限 selection、当前 predecessor、三机会和累计计数；不复制旧完整 Workflow。新 v3 全普通 request 有显式 predecessor；wrapper 用实际 SDK info 绑定新 type／queue／namespace／attempt。新 protocol-v2 不再只由 measurement mode 推断，cold 由已验 activity context 选定，取得 snapshot 后精确核 schema3；本地 controller prepare／submit／reconcile 从原 snapshot 选定。未知版本（包括 bool）拒绝。

新 wrapper 中 start attempt>1 仅 reconcile，request attempt>1 仅 observe，collect attempt>1 仅 existing-only reconcile。新 collect 的 source 为原 collect command，即使 SDK 再投 attempt>1 也不伪造 reconcile command；原完整 history scanner／DataConverter 同时核原唯一 collect 和本次 scheduled command。新 Workflow 完整 received envelope 先验容量，完整原 facts／selection／measurement 再验，prefix／acceptance 与当前 candidate、五记录、run/job/binding、common/source及目录绑定后才推进；本轮 identity／机会重置，总 BOOT/work/total 截止不重置。

H 原广泛 schema3 mode 拒绝改为明确关闭效果 mode，这是本片实质语义：

|mode|可达行为／效果限制|
|---|---|
|`inspect-controller-activity`|查询固定原 run/type/input/memo；可按原 `_record_controller` 同步原 receipt。没有 claim／start。|
|`reconcile-controller`|原已占 attempt 的查询／receipt 保存；不发 start。|
|`reconcile-candidate`|原 `_Submission.reconcile` 只 lookup＋memo认证并保存固定 receipt；无 dispatch、native create、launch 或 runner。|
|`observe-candidate`|原 execution chain 观察／fsync、固定 child runtime 查询及 `LocalTrainingAdapter.poll_job`；只有 `request-execution-candidate` 能走 request，后者仍在 H 拒绝。|
|`drain`／`observe-execution`|仅既有 stop／锁／执行链的观察和同步；不发布 stop、不发通知，也不把 H stopped 当 executor 证明。|
|`prepare-controller`／`submit-controller`、三 start modes、`request-execution-candidate`、`stop-writer`／`notify-owner`|schema3 在实际 H 入口继续明确拒绝。原 `_controller_ready`、budget.source、validate_context、native callback 等最后关闭门保持；没有真实 start/create/request/launch/native/stop 通知开放。|
|`collect-round`／`reconcile-round`|保持原 M2 的本地索引／观察语义与全部前驱／history门；reconcile 不 create。新 factory 可显式返回活动，不改变生产服务注册。没有借此认证真实 schema3 父／子执行。|

局部容量验证限于实际到达的 owner：新完整 Workflow request/received/query/outcome、活动完整 request/result、原 S/H request/stdout/frame 和新 operation-v2 拒绝留存。超界含 ordinal=None 的本地 controller mode 也沿原 streaming S 留存完整请求、不给 H；cold／无原 window 的不可留存请求沿完整 unsent 日志拒绝。完整 SDK Failure/Memo、四 poller 两配额、所有10MB晚处reader的正向和真实停止链仍属于完整 M1c-V/R 与后继，不以本片几个 helper 或合成 facts 宣称闭合。

## 实际验证与失败保留

- 初轮原 runtime：55 passed／48.63秒。首批新类契约7 passed／1.29秒；新增实际 ActivityEnvironment source／attempt／mode后22 passed／2.88秒。这些均为受控 SDK／合成 facts，不是实际 CPU N2。
- 冻源后的原完整 runtime 组：**80 passed／59.99秒**。包含新默认 sandbox 重导入、三机会、丢 start/request/collect 完成、有限 N2、错误或过界封套不推进、跨轮不续 deadline、独立 stop queue；原 lifecycle／history 接缝保持。
- 五项初轮真实 S/H 回归：5 passed／71.05秒，覆盖原 collect＋reconcile、唯一 history/decode、丢回复、完整stdout/frame和原请求留存。仍是原服务替身及合成 native 链，未运行训练。
- H 效果关闭反例初跑：1 failed／11.80秒，原因是测试给 request mode 遗漏其必需的原 window。产品未修改以迁就测试；修为显式沿 fixture 原 window 后 **1 passed／17.75秒**，六实际 H 均完整返回原 schema3 关闭结果并 stopped。两次 stdout/JUnit 分别保留。
- 三份原真实 V1 history 在本冻结源码分别完成默认 Replayer／eviction：82,086B／78 events／SHA `dc7d9587823941f0f7a99d0a6f2c6a366d58ddbd7d50f695f48cc7c87fbd47c8`（正常 COMPLETED）；44,640B／45／`3a5d086c0ba68f544903fc6ca6e689774f6671fdd8c41ea3fdccb0ec143b2b90`（CANCELED）；48,561B／46／`1e9310ceaf8269d8d103a773b991223243cd0285b548c83f1feef2ac8b1f1336`（含 activity failure，父 COMPLETED）。没有触网／服务或新历史。
- 独立解释器主动拒绝 Temporal SDK：worker／runtime／protocol core 导入成功，factory 明确报告 optional SDK 缺失，没有加载任何 temporalio 模块。
- 冻结完整输入 manifest SHA `38233007dc3ec025e8b74131da7060f52c1c4aa85d296c8f205596d240f3f641`；准确 argv／显式 PYTHONPATH、JUnit／原始stdout/stderr、源 patch及原请求材料均保存。runtime／replay/core 本次 sampler 捕获195＋5份实际本命令后代 PID/BOOT/start，检查时均 absent；只说明已捕获自有身份，不声称全系统零残留，合成 fixture 原件另作输入记录。

最终受影响 S/H 组仍运行中（含新 ordinary／本地 controller 请求留存及闭门反例），其结果与进程终核后追加。新非editable安装、自身模板和新的 fresh 需求／维护性审查由根接续；当前只交候选，不自称 approve／M6完成。

最终冻源 S/H 组：**8 passed／93.22秒**，包括扩展 operation-v2 ordinary 与 ordinal=None 本地 controller 的完整请求留存；捕获189份实际自有后代身份，检查时全部 absent。三条最终命令共捕获389份实际进程身份记录，均在各命令结束后按 PID/BOOT/start 检查为 absent。完整五文件源 patch 与原冻结清单复核同一；`git diff --check` 无诊断。原 native_main／validate_context AST 亦与基线同一。

先前55／7／22和闭门初跑均为冻源前探索，原argv、JUnit/stdout已保留，但当时未捕获完整历史源 manifest，不能把它们转记为冻结候选成绩。最终80＋8、三原history与core检查使用同一五文件固定源身份及完整2019输入清单，单独作为本片源码交付证据。没有后续源码修改。

依赖更新：根已确认 [M5/native 新 fresh 联合终核](2026-11-16-predecessor-native-final-review.md) 两轴 approve／开放0，原报告 SHA `771e33ba08f36aa54e8f5a5356913c538d152302f71300541d39509429876f21`；准确基线仍 bc58be6，本片不借该结论认证新表达或执行开放。实施完成并移交根作新非editable安装、自身模板和新的 fresh 两轴审查；在这些门闭合前，本候选维持“源码验证完成、产品／独审待验”。

## 主控：新非editable安装与自身模板

同一五文件冻结patch `9d3d72501e0fd9170d5378b27205dccf3d5a5f3a79755c4e7d3e5e695e0e54fe`，完整2019源输入前后同一。新wheel SHA256 `2df00b827f82e680a5c689669d020b8d05812c6490fce26fa4fb02c2b1101ddf`，core／SDK各665完整产品与源、wheel的原字节／执行位同一，实际三owner来自site-packages；原283参考与依赖检查通过、core无SDK／SDK1.34.0。854构建／测试输入与完整源清单分别固定，测试／示例原件另复制后运行；六个生成egg-info按原件归档后只删除已核生成文件，没有源码改动。

安装沿原精确两组：runtime **80 passed／77.00秒**，S/H定向 **8 passed／JUnit93.583秒**；两命令driver分别78.272与94.616秒。原SDK activation、合成facts／native链的范围不变，不认证真实两轮。三份原真实V1 history用安装SDK解释器、隔离模式、去除源码path插入后各完成Replayer／eviction；安装core直接导入三owner且V2工厂明确报告缺optional SDK。它们没有触网、新历史或服务。

同一安装使用原结构审查模板，真实Codex **81.715秒、approve**：10个完整文件683,076B、完整五文件patch和3项祖先资源进入771,001B实际stdin，SHA256 `51e215439b200cc7543314ab314bd81f5807accc917a82c8567cce7273945872`；原result SHA256 `4b2a9cd80b43cc3e688863f5fe1504b6041fd1283ca9cf57de3e3a6fc16e2f6b`。模型仅supplied-text结构审查，不代替真实runtime、安装或fresh独审。

本轮安装两组及replay/core实际捕获385份自有进程身份记录，检查均absent；原源码389分列，不混计为独立进程总数。完整patch、2019原输入及`git diff --check`最终保持。原件在私有 `package-r1/`、`self-review-r1-codex/`。新的fresh实现审查进行中，不自批；完整M1c／四poller、正式schema3执行和真实CPU两轮仍另验。


## final-r2：路径 owner 一致与最终受影响验证

fresh源审发现 R1/P2：新 V2 consume 以字面 `/` 构造目录，实际 `_round_operation` 的 prefix／observation 由原 `Path` owner 生成；Windows现有正向SDK fixture会给出不同字符串。该问题不是请求开启Windows真实训练，而是已纳入Windows CI的表达测试与其真正生成者不一致。原正向测试保留，没有加平台skip。

最小修正在原worker导入 `PurePath`，用纯路径运算构造两个expected路径；不触文件IO、不新增helper／validator。对前一冻结候选的106个worker函数AST核对，只有新 V2 `_consume` 改变；旧V1、服务、S/H、native与全部其他函数均同一。五文件完整patch SHA256变为 `b871eb2bec5bc09c63f758f0771d6cfccb05d967e2050d18e5bf20196a69c23e`；2019完整输入清单SHA256 `610ab4bbef44cc9e6adc011697b09fe60275a52e185d191d511fdd4edee45328`，最终原字节／执行位保持。

独立reviewer在真实 `_consume` 上采用纯Windows路径类、完整合成typed事实做小反例。旧实际安装2df00b82：native路径拒绝／confirmed0，仅改两facts为旧literal的控制例confirmed1，合同断言exit1；新冻结源码同probe接受native路径confirmed1且拒旧literal。原脚本SHA256 `70c0b32fc7dbec36a2697c062d077189b3a2bc9b883c33843949be2da9326ebc`、准确argv/raw在私有`source-review/`。这模拟纯路径语义，不认证真实Windows主机。

新源码仅复验受影响的V2/V3 runtime组：**25 passed／3.16秒**。新非editable wheel SHA256 `8574ebe644804c0bebd869caed4e06e47c1757116e161db42f94dd3e2bb48fbf`，core／SDK各665完整产品字节／执行位同源及wheel，283参考／依赖过，854构建输入同一；安装同组 **25 passed／6.07秒**，同一Windows路径probe exit0。三份原V1 history在新安装解释器各重放完成，安装core无SDK导入和明确缺SDK工厂行为通过。前候选80＋8保留原身份，不把它们续授最终candidate；未改变的S/H函数由AST及完整源身份核同，不重跑无变化的8项。

新安装原结构模板Codex **76.908秒、approve**：完整10文件683,081B、完整五文件patch和3项祖先资源进入771,343B实际stdin，SHA256 `341e70d9f96c53537f784fbf8a92acfc382d7cc54aa73487ff70403f5c8cd640`；原result SHA256 `5a9d21109692301fd2d4dab7119511e6c28bcbae8d4c79b4649c63056695b685`。同片源码／安装／probe／replay实际捕获8份进程身份记录，检查均absent，前389／385分列，非独立PID总数或全系统扫描。

final-r2完整源、patch及diff-check最终同一，准确原件在私有`final-r2/`、`package-r2/`与`self-review-r2-codex/`。当前交原fresh reviewer最终核对两轴／原R1关闭及完整新证据；未提前提交／导入。不改变任何执行开放／真实CPU两轮／M1c未验范围。


## 表达片独立门闭合与普通导入

[最终同片独立终核](2026-11-16-training-cycle-v2-expression-source-review.md)需求／维护性两轴 **approve／开放0**，R1/P2关闭，报告SHA256 `9e15489afe5cfde8684cb19708ed3a14c69da160f0a914a638726fab421594df`。最终五文件准确固定为 `2acdcc44eb86659f3ab9d22d2f83bb0973388406`，完整patch仍b871eb2b；普通导入主开发分支为 `f9b9d72d6d5f2102809a3cafaadb2226bba0966b`。与并行a1同树的新联合安装／必要接缝／公开候选自身CI由根接续，不转授各自单片结果。M6-V1表达片闭合；生产仍默认V1、所有schema3实际效果保持closed；M6-V2服务／完整M1c与V3真实两轮是下一阶段。
