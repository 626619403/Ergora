# c1d：超限父请求原字节留存实施

2026-11-16。状态：r3 源码交接完成，22项诊断＋8项必要旧v1及三份旧实际历史通过，[fresh源级复审](2026-11-16-training-cycle-parent-request-retention-source-review.md)两轴approve／开放0；根正在完成新包安装行为、自身原模板及整片终核，尚不预记这些结果。依据[限定设计](../plans/2026-11-16-training-cycle-parent-request-retention.md)及其[原审／复审](2026-11-16-training-cycle-parent-request-retention-design-review.md)，保留 R1 完整原 clock 和 M1 原 raw／N／EOF／一次确认；不开放 schema3 执行或后继轮次。

准确产品基线为 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，唯一父 `23ad171bf8228bf80b070d6ad866f79d63986d56`。隔离分支 `feat/training-cycle-parent-retention` 从该提交创建，根代理管理相邻产品来源与整合；本实施不修改相邻来源树、不 commit／merge／push。应用 maintainable-project-delivery 及 ergora-codebase-quality 的 module-design／test-seams。

实际接口核定：新 operation-v2 只有 `collect-round/reconcile-round`，使用原十字段 identity、schema3 snapshot、必需 activity_context、原 controller binding 与 work bootstrap。M2 的已接纳 B 分片把 `_CycleOperation` 的实际 constructor／同次 UUID 与 compact 编码／run 作为内部 producer 边界；正式 SDK v3／V2 上层 creator 尚不存在，保留到后片。根再次明确这一范围后继续。本片不新增 SDK 注册、上层 creator、伪造来源认证或削弱原业务 reader 的认证。

最小改动仅原 [worker](../../src/ergora/reference_training_worker.py)、现有 [submission tests](../../tests/test_training_submission.py) 与 [operation fixture](../../tests/fixtures/training_cycle_operations.py)。worker 在 v2 编码超界时保留同一次 UUID 和 immutable raw，原 async owner 选择无 H／无后代的诊断 S；普通 v1 constructor 仍立即抛错，普通 S/H 的 stopped kill gate／唯一 reaper 不变。小封套携完整 clock 四字段、两项原 policy、bootstrap 与只缩整数 deadline；S 主线程和进程内 watchdog 持续实际调用原 budget_clock.remaining。stream 分块≤65,536B，父显式 yield／drain并逐块 SHA；S exclusive 保存唯一 request.json、N／EOF、原 fd fsync、目录链同步、同 inode／N／SHA 流式重读后发一次小 identity-bound 确认。没有第二 receipt、ledger、ready、trailer 或恢复 reader。

父只有在发送结束、全部 pipe 结束、实际 wait 成功及最终原时钟／stop 检查通过时给 request_retention.durable_confirmed 和小 ref；其他故障均 unknown／不给 ref。业务始终 capacity_exceeded，不发普通 S/H/root、不返还机会或重发。诊断 wait 不伪装成 H stopped；小发现日志仅含 ID、mode／ordinal、output 与留存／实际 wait 事实，不打印原 reason／raw。有限窗口、磁盘错误、SIGKILL 及内核不可中断 I/O 无法保证完整 durable 或硬实时回收；保留 partial／unknown 的实际范围。

私有逐轮证据位于根 ignored `.ergora/checks/cycle-parent-request-retention/`，每轮保留原 argv／env、basetemp、JUnit、完整 patch、src/tests manifest 与输出。后续候选不继承较早轮通过：

|轮次|实际结果与范围|
|---|---|
|run-01|1 failed／7.20 秒。真实诊断路径已经返回 durable_confirmed，196,331B raw 逐字比较成立；测试 oracle 把小 envelope 也计成第二次原 payload 编码而失败。修测试过滤至含 snapshot 的原 payload，原失败保持。|
|run-02|1 passed／6.01 秒。真实内部 constructor 同次 196,331B 多字节 UTF-8 raw，无末尾 LF、原 UUID／full identity、唯一 request.json／完整 ref、实际 wait；业务容量失败、无 helper／H，原 admission 文件逐字不变，日志无 reason。source 内部接缝与合成原 source，不是正式 SDK 或真实训练。|
|run-03|新增真实 stream／N／EOF、32,768／32,769B、partial／fsync／same-raw replace／raw corrupt、reply／SHA／identity／额外帧、blocked writer取消／peer，以及父 loop 不可调度时 S-local UTC drift 的 watchdog 检查正在运行，未预记通过。|

尚待：本轮结果、真实 parent SIGKILL、spawn／发送生命周期、必要旧 v1／history 回归；固定最终 src/tests 后受影响组。安装、原模板、新 fresh 独审与发布由根后续负责。当前不关闭完整父留存 gate、M1c、M5／M6 或真实两轮验收。

## 后续源码检查与 r1 冻结

初始进度快照已由根固定到 `a0d533d`；以下仅追加实际观察，不改写早轮范围。run-03 实际 **15 passed／62.13 秒**：原 32,768B 普通 S/H 与 32,769B 诊断分流、N±1／EOF、真实短写后失败保留17B前缀、fsync失败、同 raw 换 inode、原 inode raw损坏、丢最终确认、错 SHA／完整 parent identity、额外帧、blocked fsync 取消及独立 peer 完成。UTC drift 场景的父 expired 检查被禁用且父 loop 同步阻塞0.4秒，S 主线程阻塞于 fsync；只有 S-local UTC+10秒使原 budget_clock.remaining 拒绝，旧 BOOT D 未到就由 watchdog 实际 SIGKILL 同一 S，父未发信号、实际 wait=-9，unknown／无 ref／无确认。该一例覆盖完整原 clock 的独立拒绝，不声称覆盖所有 clock 失效矩阵。

run-04 实际 **5 passed／19.90 秒**：真实外层持 parent handle SIGKILL／wait 后，阻塞 fsync 的 S 由自身 watchdog SIGKILL；外层限定 subreaper 实际 wait=-9 并确认 `/proc/<pid>` 已不存在，整数 D 尚未到、无确认。另含诊断 spawn 延迟返回／2MB raw 管道背压发送／async loop teardown 三种取消，实际同 S wait 与 unknown，及 1.5MB raw 的同 immutable memoryview≤65,536B／逐 chunk 公平 heartbeat／完整 raw 成功。每个新增 Linux 测试均用函数级 skipif 在 fixture setup 前保护。

此后 r1 的 src/tests 已冻结，run-05 全部 round_ 受影响组和 run-06 必要原 v1 preparation／普通 S-H 取消／cold inspection／blocked stop-peer／capacity／construction-failure 兼容组正在独立 basetemp 运行。两轮持有相同完整 patch 和 src/tests manifest；未预记结果。实际 SDK replay／旧历史与最终静态身份检查另记。若出现新 finding，先报告根再解冻；修后候选不继承这里的成绩。

r1 完整三文件 patch SHA256 为 `709e9ba2172546a8654bbbc0d66eba0b3112f45d25a35f69863213c319b469fb`，冻结781份 src/tests 输入。run-06 实际 **17 passed／196.57秒**；run-07 现有 runtime SDK 取消／history-bound／真实 replay eviction 接缝 **5 passed／2.45秒**。run-08 保留三份旧现场历史原件，逐份核原 SHA／长度／78、45、46 events，原完整 argv 仅切 src 至当前冻结树，`create_cycle_workflow()`／默认 sandbox／单 child20秒上限保持；三份均实际完成 replay 与 eviction、returncode0、原完成标记、空 stderr（各约1.30秒）。未重生成 history 或把内部测量用例称为正式 SDK creator。

静态身份核验：25项 GATE_SOURCES 键与基线逐字同一，原 reference manifest SHA `1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943` 保持；实际 `reference.verify()` 283文件 PASS／runtime_started=False。该核验不代替新包安装或独审。

冻结后静态自检发现一项确认边界风险，已先报根且未解冻：当前父确认用 Python dict equality 核完整 identity，`False == 0` 会使 malformed ordinal=False 与原 ordinal0 相等；S 入站已有 strict int，但父最终确认也需保护这一类型。私有静态反例已保留，不声称已运行新的 S 反例。r1 原跑组继续完成并保持原件；它的通过不能消除此项，也不传授后继修正候选。最终 r1 不能据此交付为无开放风险候选。

## r1 原终态与 strict identity 修正 r2

run-05 原冻结终态为 **46 passed／334.92秒**，即原 round26＋新增诊断20。此后按根处置，先只在既有 reply-identity fault 参数加入 ordinal=False，产品 worker 保持 r1 SHA 不变。run-09 实际 **1 failed／6.27秒**：真实同一 S 完整保存124,337B原 request、唯一确认被 fixture 改为 bool ordinal、真实 wait0；旧父误报 durable_confirmed。该红例证明的是诊断确认外部输入边界，不是业务执行授权绕过；业务仍 capacity_exceeded。

修正仅在原父确认边界增加 `type(confirmation['identity']['ordinal']) is int` 条件，拒绝 Python bool／float 与原整数相等的类型错配；不新建 validator／协议／状态，也不改变 raw 或普通 v1。现有错误 identity 参数保留原 parent.start_ticks 错绑定与这个独立类型陷阱，不复制每字段测试矩阵。

r2 冻结完整三文件 patch SHA256 `b376d5470617b777bd11ab0c981b1eddf73ca0f2130f2570b69ce92d17cd823d`，worker SHA256 `c794f265f7420c599b7e112a40c781631accb0ada47f73a755ac743409896537`；781份 src/tests 输入逐轮 manifest 同一。run-10 全21诊断（包括真实32,768B普通 S/H）及 run-11 必要旧v1 capacity／spawn-helper-loop取消／blocked-stop-peer／cold-inspection 组正在独立目录运行，源码保持冻结，未预记通过。r1完整原26／17与历史重放仅保留自身范围；安装、自身原模板与 fresh 独审仍由根安排，未提前记完成。

## fresh 静态 finding、真实反例与 r3

r2 原冻结 run-10 **21 passed／83.05秒**、run-11 **8 passed／101.09秒**后，fresh reviewer 指出同类 parent.pid 的 float 可与原整数相等。根先反馈该 finding，实施独立核实后才解冻。run-12 在原 r2 worker 上沿现有 reply identity 参数将真实确认 parent.pid 改为 float，实际 **1 failed／6.26秒**：同一 S 保存完整124,337B raw、真实 wait0，父仍错误给 durable_confirmed。原件保留；r2 的通过不消除此缺口。

r3 仅在原父确认处复用已有 `protocol._process(confirmation['identity']['parent'])`，保护 pid 的 strict int 及原 start_ticks／BOOT shape，保留 r2 ordinal strict int。其余原 identity 值均为原字符串，与原 identity 的完整 equality 和外层 exact shape 共同校验；ref bytes 已单独 strict int。不另造验证器或扩字段矩阵。

r3 完整三文件 patch SHA256 `f5b46155f6b135257bcbf4a00ab05c2afc096e52c4bae0659af13ef005d60c76`，worker SHA256 `be12b4de17c448e7e07217aacf60a097e080333f169e99cccaa91981e66bd926`，781份 src/tests 再冻结。run-13 全22诊断与 run-14 原必要8项 v1兼容正在运行；已将准确冻结身份交根，可并行安排新包／安装和 fresh 复核，不修改该 source。

证据处理另修本地 runner：既存完整环境原件仅保留于私有 ignored 区，访问权限收紧；后续 command 只保存必要非敏感 allowlist 与环境变量名，不输出继承环境值。权限收紧未跟随 symlink，保留 owner 原执行权限；runner／证据修改不混入三文件产品 patch，也不入库。

## r3 源码交接结果

r3 固定字节上，run-13 **22 passed／88.09秒**，包含两个真实 typed-identity 红例的修后拒绝、原完整 raw 正例、普通32,768B／诊断32,769B、N／EOF／SHA／full identity、filesystem failures／partial／exclusive target、cancel／spawn／pipe／wait／peer、真实完整 clock watchdog 拒绝、真实 parent SIGKILL 和公平 immutable chunk stream；run-14 **8 passed／102.51秒**，原 v1 capacity 的 constructor立即抛错／peer完整收尾、普通 S-H spawn／helper／loop取消、cold stopped reader 与 blocked stop-peer 保持。run-15 再以准确 r3 重放三份原现场 v1 history，原 SHA／长度／78、45、46 events不变，默认 SDK sandbox／20秒 child界，三份 replay与eviction均成功／空stderr，各约1.30秒。r1／r2及两次真实红例继续独立保留。

最终私有原 marker 共161份不同实际 process identity，再核无一 active；诊断实际 wait、H停止及 parent-SIGKILL 中 `/proc` 已不存在的证据仍按各自原测试范围解释，不能把 zombie拒绝或发信号本身冒作所有进程已回收。完整 patch、每轮 argv／安全环境元数据、manifest、basetemp、JUnit及原失败均保留于本片私有目录。源 r3三个候选文件和全部原781输入逐项 SHA 未变、diff whitespace通过；9个新增 Linux 测试函数全部在 fixture setup前 skipif。根构建期间出现6份 ignored egg-info metadata，单独归为构建副产物，原冻结输入没有更改，未把这些生成文件混入三文件 patch。

源码交接身份仍为基线 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`、分支 `feat/training-cycle-parent-retention`、相对根隔离树 `.ergora/worktrees/training-cycle-parent-retention`；完整三文件 patch `f5b46155f6b135257bcbf4a00ab05c2afc096e52c4bae0659af13ef005d60c76`。没有 commit／merge／push、SDK注册／执行开放、CI job／配置／依赖改动，未调用模型、真实外部服务或训练。

本记录交付 source 内部用例；source fixtures 的 schema3 source与外部服务均为明确合成／替身，正式 SDK 上层 creator仍后置。新非editable包、安装检查、自身原模板、fresh复审、整合／发布由根另记；不预记已通过，不据源码结果关闭完整 M1c、M5／M6 或真实两轮验收。有限窗口／磁盘失败／D-state的 partial+unknown 与硬实时限制保持。后继若改动这份候选，须另冻实际字节及其对应证据。

根已把6份构建元数据归档后逐个移除；实施最终再次核得 src/tests 文件集合准确恢复原781份、全部 SHA及完整 patch同 frozen-r3。最终源码交接摘要与161身份收尾位于本片私有 source-handoff-r3.json／final-process-identities.json。上述 fresh源级报告已实际复核 r3，R1关闭、需求与维护性approve／开放0；其范围仅准确源码与定向证据。根另已报告新 core／SDK包的非editable安装身份／663文件／283参考／依赖静态检查完成，安装22＋8行为及自身模板仍在进行，不据此预记通过。


## 根验收：新安装、自身模板与固定候选

准确新r3 wheel SHA256 `0426af971d2d573b952873d89be327cd8e7de115547f05d1391ad31c7507faeb`；core／SDK两套非editable实际site-packages，各663完整产品文件与冻结源码／wheel字节及执行位同一，无新增／删除产品文件、仅worker字节变化。原283参考与依赖检查通过；SDK为1.34.0，core无Temporal。源853份输入、663产品及179份测试／示例副本逐项冻结，构建六份egg-info已单独归档后移除，不混入产品。

安装行为使用新SDK的Python3.12、`-I -B`、无PYTHONPATH及原冻结测试副本，实际结果如下；source和installed分别记账，不借用早轮身份。

|新r3安装检查|实际结果|范围|
|---|---|---|
|installed-retention-r3|22 passed／116.27秒（driver117.429秒）|完整诊断组，含真实S／filesystem／pipes／watchdog／实际parent SIGKILL与strict确认反例修后拒绝|
|installed-compatibility-r3|8 passed／119.15秒（driver120.278秒）|既有v1容量／取消／cold／blocked-stop-peer定向兼容|

Ergora自身原 `refactoring-quality → ergora-structure-review@1.0.0` 使用新安装SDK，实际Codex **61.542秒approve**。13份完整文件607,088B、完整47,112B diff、完整baseline worker及3份全部祖先资源进入802,880B原stdin，SHA256 `2b1be0f9ec1b5cdd9294b405ddf6d220f99696db62e69440a5e8783df9d5356a`；原result SHA256 `6cc016d4ca0db063b90c4ee2567d5fc71d79c5155fc45e55a41b44ad328dd600`。模型只审所供完整文字，没有workspace或独立跑测试，不认证正式runtime／CI／训练。实际输入／输出／资源与命令沿ignored `cycle-parent-request-retention/self-review-r3-codex/`保留。

根最终post-check核853输入、663产品（core／SDK各自）及179测试／示例副本byte／mode不变；安装两组已捕获55份完整process marker身份当前全部absent，没有补造未捕获进程身份。源码161份身份无active仍沿原source-handoff范围；不同捕获集不合并冒称全系统收尾。

准确产品固定 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，唯一父68ba793，隔离树clean，恰三文件710+/12-；完整47,112B Git diff与冻结patch `f5b46155f6b135257bcbf4a00ab05c2afc096e52c4bae0659af13ef005d60c76`逐字同一。新包、实际安装argv／输出／JUnit／结果、最终输入／进程核验及candidate-r3原件位于ignored `cycle-parent-request-retention/package-r3/`。

源级fresh已两轴approve／0；以上新安装／自身模板／固定提交尚待同一fresh reviewer整片终核，尚未导入或推送。父raw只在已接纳的内部v2边界闭合，不增加正式SDK creator／V2／v3或ordinal1；M1c其余容量／reader、M5最后gates、真实两轮及GPU／训练质量保持各自待验。


## 最终独审与普通导入

同片fresh reviewer独立核实固定产品、853源输入／663产品及两安装、179副本、实际22＋8安装行为、原模板完整材料和已捕获进程收尾；最终需求／维护性两轴approve，R1关闭、开放0，允许普通导入准确1f57ca4。[当前报告](2026-11-16-training-cycle-parent-request-retention-source-review.md)SHA256 `5033855a61e6434f797bd4ad0f00bc492027237d036ba7cd826a689d610bc4dc`，原r2 request-changes与真实红例仍保持。

已普通合并开发分支 `c4c0946060ba781eb8b2cb2e7e9d3ad2798dcd5a`。合并后全部663产品字节／执行位与原已验候选同一；853冻结输入仅两项另外已审的主线差异：Windows四行提前skip与CI分组JSON，原归属／证据不变。`package-r3/merge-inputs-r3.json`保留准确合并身份。该产品内部片闭合；公开联合候选与自己的CI待后续，不借M2或前片CI通过。

接续M5-G在固定1f57ca4上独立实施；全M1c／正式V2-v3／schema3效果／ordinal1及真实两轮仍待各自候选验收。已审留存只覆盖当前collect/reconcile两个内部v2 mode；M6新增mode的实际producer、诊断控制表和完整Failure／Payload边界需在M6重新接齐，不能沿用本片结果称已全开。


## 联合公开候选

已普通推送 `debf6f96ed02620d22adc0ac6385c72641b3d53b` 到原开发分支，精确远端SHA同一。它包含已审父留存及另已审两完整文件的CI再平衡9a35174、闭合记录及M5/M6后继计划。官方API HTTP200在01:08:41Z准确发现其自己的push／attempt1 [43784344936](https://github.com/626619403/Ergora/actions/runs/43784344936)，head_sha同一，in_progress／无终态。推送／远端／发现请求和原响应沿ignored `cycle-parent-request-retention/publication-r1/`保留。前a0d533d的八job成功不授予本候选；后续按它自己的结果更新。


01:17:46Z准确run／jobs查询均HTTP403，官方rate-limit headers为remaining0、reset01:25:06Z；原响应和headers逐次保留，不将该失败改写为Workflow失败或成功。最后成功发现仍为准确debf6f9的run43784344936在途；配额恢复后再查询，本地M5工作继续。

配额恢复后01:30:01Z的run／jobs均HTTP200，准确debf6f9、push／attempt1、八job中七项成功且Windows在途。01:31:47Z再次官方HTTP200，准确同一head／run／attempt已completed／success，plan／六Linux／Windows八job全success。group5实际17分31秒、group1为7分07秒、Windows23分48秒；原Linux20／Windows30分钟未改。日期固定原件为`publication-r1/20261116T013147Z-{run-response,jobs-response,summary}.json`及响应headers，原403不覆盖。该CI仅闭合debf6f9联合候选，不授予尚在隔离测试的M5或未来M6。
