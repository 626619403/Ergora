# c1d B（M2a＋M3a）独立源码／架构审查

2026-11-16。Reviewer：fresh-context 独立代理 `cycle_measurement_collect_source_review`。按 maintainable-project-delivery 的 independent-review brief 与 ergora-codebase-quality 的 module-design／test-seams 审查；没有继承实施对话。只读产品／测试／指定证据，本次唯一写入为本报告。

**需求轴 request-changes，开放 P1 一项；维护性轴 approve，未发现独立架构阻断。** 这是固定 r3 源码的静态结论，不是运行验收。完整安装、自身模板与最终证据闭合仍待准确新候选；r1／r2 的通过不继承给 r3 或修后候选。

## 身份、要求与实际检查

项目根为本仓库根目录；被审源码为隔离树 `.ergora/worktrees/training-cycle-measurement`，分支 `feat/training-cycle-measurement`，HEAD／基线均为 `23ad171bf8228bf80b070d6ad866f79d63986d56`。完整 r3 binary patch 为 129,722B，SHA256 `3e150ce906ba894fcd4842c3cc92a05303a979b4c18dd395ad4c3ec690288624`；manifest 为 `275642485a116a1cac468f777a4c77652cacc20b0280fc4a52291d2e36a83b6a`。独立重算当前 diff 与 frozen patch 逐字相同；781 份 tracked src/tests 在 frozen-source-r3 和当前隔离树的长度、SHA 与模式均匹配 manifest，零差异。恰有以下八个既有文件修改，无未跟踪产品／测试文件：

- `src/ergora/reference_training_runtime.py`、`reference_training_worker.py`、`training_execution_protocol.py`、`training_rounds.py`。
- `tests/test_training_submission.py`，及 `tests/fixtures/training_controller_service.py`、`training_cycle_operations.py`、`training_evidence_archive.py`。

已读根／src／tests AGENTS、当前 PLAN、组件协议的执行／证据及脚本／检查责任、[内部片权威计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)、[容量分期](../plans/2026-11-16-training-cycle-measurement-capacity.md)、[wire](../plans/2026-11-16-training-cycle-measurement-wire.md)、[原索引设计](../plans/2026-11-16-training-cycle-measurement-and-index.md)、[R1 设计审查及复审](2026-11-16-training-cycle-measurement-acceptance-design-review.md)、[交付记录](2026-11-16-training-cycle-measurement-acceptance.md)。权威计划独立重算 SHA256 为 `2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`。根树此时 HEAD `610f111`，没有把其 Windows marks／文档差异当作隔离产品修改。

逐段审查八文件 diff，并沿原 `_CycleOperation → S → H → _cycle_operation`、runtime lookup/history、CycleAdmission.bind/check、ExecutionRecords.load/request_record/observe、rounds.create/read、原 evidence/archive owner 及相关失败 fixtures 跟读。`git diff --check 23ad171 -- src tests` 无诊断。未运行 tests、安装、服务、网络、模型、训练、commit 或 push；没有递归读取其他 `.ergora` 运行库存。

交接时 r3 run-15 新23项与 run-16 原 evidence14 结果尚未由根提供，本审没有把目录存在视为通过。已完成 r1／r2 检查及 r2 模板 request-changes 只按交付记录原范围引用，不重新认证。根随后明确 r3 package 仅先 build／身份，尚未启动 installed 或 self-template。

报告完成前根通知：r3 源码23＋原 evidence14 已通过；指定 `source-r1/post-check-r3.json` 保存781 raw／mode零差、同一patch及已记录process身份均absent，`package-r3/final-inputs-r3.json` 保存848输入＋663产品不变、wheel `0271fdb0ad39d081c4b9cd1a655db2491c3c835cd1337d126fa1e155dddad667`、core／SDK身份及 installed_behavior_run=false／self_template_run=false。本审只读核这两份明确指定记录，未重新运行或据其认证未覆盖的最后gate。根已接纳本审P1并授权原实现者解冻r4。**本文所有源码位置与结论固定指向 `source-r1/frozen-source-r3/` 和上述原patch；随后live工作树的修改不属于r3，更不能据live变化自行关闭finding。** r4完成后由同一reviewer按新冻结原件作同片复审。

## R1 — P1：最后索引读取之后缺少原 stop／来源的本地复核

位置：被审 r3 `reference_training_worker.py:1199–1204`；同文件 `_round_gate:835–886`、`active:554–557`，以及 `training_execution_protocol.py:904–911`。

可达路径：最终 observation 已写、同步并经真实 ref reader 重读，随后 `_round_previous` 核完整旧前缀；`:1199` 调最后 `_round_gate`。该 gate 在 `:837–863` 核 plan／ready／项目、candidate intent／owner、25 sources、四项 measurement_sources、安装／descriptor／ROOT／registration，之后 `:880` 仍执行原 parent lookup RPC／history。RPC 返回后只执行 `active()` 与 `admission.check()`；前者仅核原 clock／父进程，后者只核原 authorization 与可见 stop，不复核上述来源或项目。

更直接的确定性窗口在调用者：`:1201` 的原 `training_rounds.read(destination, sha256=...)` 发生在最后 `admission.check()` **之后**，它包含完整文件读取及 schema／内容检查，可以阻塞。若 H 在此 reader 暂停期间，原 stop owner 发布合法 stop，然后 reader 返回同一合法 index，`:1203` 仅检查 clock／父进程，`:1204–1210` 仍构造 acceptance 并返回 `accepted/durable/continuation_ready=true`。同样，来源／所选安装／项目在最后 parent RPC 或这个最终 reader 期间漂移，也没有随后本地重核。无需超时、损坏 index、伪造 RPC 或任意“最后检查后的一瞬间”竞态；有明确的后续可阻塞 I/O 窗口。

这违背权威计划第72行发布前全部正面条件，以及第126、144行 stop／source 冲突必须拒绝与前后核之间变更的实际验证义务。当前没有正式 V2／后继执行 owner，不会因此直接启动训练；但它会形成已被原 stop／来源变化否决的正面内部接受投影，不能作为本片正确结果交付。

最小修正仍留原 worker：在最后 parent RPC 和最后 index 重读完成后，再核当前完整本地 authority／candidate 原绑定、原 measurement／capability／ROOT／所选安装／registration，以及 stop 和原 clock，然后才构造 acceptance；其后不再调用 RPC 或额外 archive／index reader。可局部提取并复用 `_round_gate` 已有本地检查，避免复制一套条件、增加 owner 或第二状态机。最后 stop／clock 应位于这些本地检查之后。这里要求收紧已有最终检查的顺序，不要求跨服务／文件的绝对原子快照。

最小真实接缝：沿现有 `cycle_operation_fault` 保留原 S/H/reaper；仅在 `_round_operation` 最后直接调用原 `training_rounds.read` 时，先真实读出结果，发布 marker 并阻塞返回。父测试在 marker 后通过原 `admission.request_stop` 发布 stop，再释放 reader；要求最终 unknown、acceptance=null、ready=false，原 index／observation／诊断保持，不 create／repair／重授机会。另可在最后 parent RPC 返回前改变 descriptor，验证同一个修后本地 gate；无需全面新增矩阵。当前 `round-source-drift` 在 create 后改 descriptor，`round-stop-after-observation` 在第四次 validate_sources 内发布 stop，均发生在最后 `admission.check()` 前，不能保护上述窗口。本审只给源码证明与实际故障位置，未运行该反例。

## 其余需求与维护性判断

- 版本与权限边界明确：operation-v2 只用于 collect/reconcile，必须 schema3／v2 controller／精确 activity source；旧 operation-v1 与 schema1／2 分支保留。`BudgetedStart.source`、`validate_context` 和原执行路径仍拒绝 schema3；没有 V2 producer、v3 SDK 注册、公开 CLI、新 execution/native 权限或 ordinal1 开放。内部三候选 fixture 不能认证三个真实训练 run。
- runtime owner 使用真实 SDK history stream／DataConverter，完整扫描后才确认唯一原 scheduled collect；精确 ID／type／queue／完整 request、原父 run、8000 events／8MiB 及 decode/RPC 失败均由已有 owner 控制。没有本地 collect-attempt 账本。collect 只在原确定性目标首次机会调用原 create；reconcile 与目标竞争输家均只读既有目标。
- 四事实接受没有用单个 SUCCEEDED 或 preflight 替代最终 index。原 runtime binding／receipt run／memo、native Job、ExecutionRecords 五记录及严格 durable stopped、原 accepted archive/files 与最终原 records／evidence／submission共同绑定；Outcome 使用原 report URI。原 evidence/comparator／baseline 算法及 `artifact_content_status=not_read` 保持。明确失败与 unknown 分开，local approval 仅观察。
- `_round_previous` 逐层读取确定性每一原 prefix、原 observation/ref、原 source request／stdout 及 intent predecessor，比较完整轮值／注释／manifest／previous_report／initial anchor；最早原件不是只靠最后一条 SHA 代替。紧邻前轮重新观察 phase，早轮保留原当时观察与当前原 archive／stopped inventory。没有发现需要第二 reader 或扫描恢复算法的理由。
- r2 ref 绑定修正位于实际 `read_round_observation` 的协议边界，交叉核 candidate ordinal／manifest／revision 与完整 evidence/native 值；新增反例改真实固定路径原件并保持 ref SHA／bytes 自洽，接缝能观察原缺口。
- r3 对原 `rounds.create` 的可选 keyword-only `on_reader_return=None` 是已证实真实消费者所需的最小接口扩展。四个 callback 均紧接真实 inspect/evidence/submission/approval 返回并先于下一 reader；worker 原 retention 完整有限 UTF-8 JSON＋LF 写原 H stderr 并 flush，异常终止出版，返回值不参与业务。默认 None 的旧 create 算法／数据与公开结果保持，没有新增 proof 文件、snapshot 注入、archive 复制或 wrapper。新两反例保留原 create 及前后 reader，并使用刚返回的独特大 evidence 值，有别于 preflight 留存测试。
- index 与 observation 的新 durability 算法在原 H，用原 fd／目录链同步／同 inode 与同 raw 重开；10,000,000B 常量沿原 owner，真实 observation writer 包含 UTF-8 末尾 LF，writer 后与 reconcile/predecessor reader 显式用 ARTIFACT_LIMIT。ExecutionRecords 的旧 raw-only durability 没有被报告为全链同 inode。大结果不进入32KiB stdout，超界只保留 diagnostic，无合法 acceptance。相关行为仍须准确候选实际运行认证。
- 新私有函数均服务现有 H 的内聚算法，删除后完整绑定／fd 生命周期仍须回到同一分支；没有虚构跨文件 caller 或新通用框架。protocol 未新增 SDK／State／rounds／jsonschema import。guard 保护的是持久身份、外部输入、容量与资源生命周期；没有仅因函数长、同文件调用或必要重复身份绑定提出架构 finding。

不因未穷举每个 guard 变体或故障矩阵而增加 finding。当前具体缺口是 R1 的真实最后 I/O 顺序，已有测试没有覆盖它；修正与原反例通过后需同片复审，再根据准确新 frozen source 完成所需新包、installed、自身原模板与证据终核。parent-request exact raw 留存、完整 M1c／M5／M6、正式 V2/history/replay、真实两轮／模型训练质量继续开放，不能由本静态审查关闭。

## r4 同片源码复核：静态缺口已修，行为证据待补

2026-11-16，同一独立 reviewer。原 r3 全文由根以不可覆盖方式保存于指定 `source-r1/source-review-r3-original.md`，本审独立重算 SHA256 `0e006b4ae16110df73c759dbbf869f712cb513cf413118a1c9f31e57e42b32f9`；上文原 request-changes／P1 及其源码身份保持。以下只审新冻结 r4，不以 live 工作树变化替原结论。

r4 基线仍为23ad171，八文件同范围。完整 patch135,245B，SHA256 `0ccbc19e2da14e11eec2b4ff3fa55a55addbb35ad0a80cc6aa40ead40df0192c`；781份 manifest SHA256 `3a9fc2c097286fa5ba845f1942f616646c6b22b9a09b9f8e58b220aef3e04eb1`；r3→r4 delta SHA256 `2bfcce5d6e3d765da0c12b464771c132569c4dd4358e1652838b664b058dcc0b`。独立核 `frozen-source-r4/` 与当时 live 隔离树781份长度／SHA／模式均零差，完整当前diff逐字等于r4 patch；`git diff --check`无诊断。本轮只读该delta、冻结源码、指定run18/20记录和当前计划／交付，无测试或源码修改。

**r4限定源码结论：需求轴静态 approve／开放源码 finding 0；维护性轴 approve／开放 finding 0。R1所述检查顺序在源码中已修，行为闭合暂待run19原件，尚不标记整片验收完成。**

原 `_round_gate` 的本地条件局部提取至 `reference_training_worker.py:828–865` 的 `_round_local_gate`，旧调用在 `:874` 复用它。plan／authorization／ready／完整注册项目、原 intent/controller／owner/capability、所选 installation、25 gate sources、四项 measurement_sources、pinned manifest后的ROOT verify及registration检查均保留；没有把校验缩成clock／stop。原work预算检查移动至本地来源及registration读完成之后，随后仍核原operation window／父进程及原stop。它没有授执行权、刷新clock或增加机会。

最后接受路径现在为 `:1211` 的原父RPC认证 → `:1213` 的原完整index重读 → `:1215` 的完整 `_round_local_gate` → `:1216–1222` 纯接受投影／本地协议shape检查及返回。新最后local gate之后不再调用parent RPC、index或archive reader，因此不是把已报告的后续阻塞reader窗口换个位置。原stop在final read期间发布会由新local gate拒绝，descriptor／项目在final parent RPC期间漂移也会被重新读取拒绝。这里仍是有序的真实观察，不声称跨多个文件／服务构成绝对原子快照。

该helper有原远程gate前置及最终发布后置两个实际阶段，避免复制完整本地条件；删除它会让同一不变量散回两处。同一既有worker内的私有算法具有明确生命周期归属，不需要新模块或声称跨文件复用。r4产品delta仅worker提取／顺序，不改r3 callback、archive/index算法、strict ref reader或旧schema1／2/v1路径；全部schema3执行关闭点与既有非目标保持。

新三参数反例保留真实原read／parent describe的返回值，在返回后阻塞，父测试实际通过原owner发布stop或改变descriptor／project revision，再释放reader；检查原index／observation字节保持及真实S/H停止。停止项核的是实际 `stop_visible=true` 与 `stop_durable=true`，不是错名字段。fixture没有直接替换 `_round_operation` 的返回值或跳过reader；其caller code identity与observation已存在条件将故障定位至最终实际边界。原run17的stop参数错键不作为有效stop红证据。

独立读核run18 argv／JUnit／日志：原产品r3加新fixture的三个参数均得到真实 observed＋accepted＋ready=true，而目标unknown断言失败；JUnit **3 failed／20.853秒**（result墙钟21.140秒）。保留此真实先红，不能当作修后成绩。独立读核run20的source.patch等于r4 patch，完整原evidence **14 passed／28.850秒**（result墙钟29.208秒），涵盖旧负面／unknown索引与离线read等实际原用例。

本轮读核时run19尚无result／JUnit，故未预记新26项或三项修后绿；r4新包、installed／自身模板与最终冻结输入终核亦未提供。待根提交这些准确原件后，由本reviewer继续追加本片证据结论；上述有限静态approve不覆盖这些开放证据，也不继承r3或更早包的运行结果。

## r4 同片行为复核：R1 已关闭，安装及最终交付仍待验

2026-11-16，同一reviewer只读根随后提供的指定原件。本次没有重新执行tests／服务／安装／模型，也没有改产品或测试。**固定r4内部collect/reconcile切片的源码及已提供源码行为证据：需求轴 approve／开放 finding 0，维护性轴 approve／开放 finding 0；原R1行为阻断关闭。** 上文r3 finding及先红、r4早期pending均为当时准确状态，保持原文。

独立核run-19与run-20的source.patch SHA均为准确r4 `0ccbc19e…`，读取完整JUnit／result：run-19 **26 passed／217.940秒**、零failure/error/skip，墙钟218.239秒；其中最后index-stop、parent-source、parent-project三个实际反例分别通过。run-20原evidence仍为 **14 passed／28.850秒**，墙钟29.208秒。没有把修前run-18三红或r3的23＋14当作r4运行结果。

逐条读取 `final-gate-green-r4.json` 指向的三份实际 `round-final-result`，与汇总完全相同；三项均真实unknown、无acceptance／prefix／ready，原S/H已停止且supervisor_returncode=0。stop项明确报原Controller stop可见；descriptor项报原runtime descriptor不完整；project项报原plan／ready／registered project失配。分别从实际operation输出路径推导并重读原index及observation，长度／raw SHA与汇总一致；三个测试也在reader释放前后比较了完整原件不变。stop项另读取实际 `round-final-stop`，确认与原stop观察逐字值相等，`stop_visible=true`、`stop_durable=true`（admission_drained=true）；没有把operation_stopped当作原executor停止证明。

这些真实S/H先红后绿正好覆盖原finding的两个可阻塞I/O窗口，不靠模拟最终返回值：原r3即使stop已持久可见或source/project已变仍ready=true；固定r4的最后本地gate拒绝并保留已发布原件。源码顺序与实际反例共同支持R1关闭，不要求不可能的跨服务／文件原子快照。

另读 `post-check-r4.json`：781 raw／mode零差、完整patch保持、无untracked src/tests、src/data diff0、283reference通过；其中49个已捕获完整process marker均matching_alive=false。本审核该记录的精确范围，没有将有限已捕获身份扩称全部未知进程的现场清理证明。前次本审已独立逐份核冻结树／live781原件与manifest相同；本次post-check将检查后的身份保持接续到上述真实运行。

根同时提供新SDK包经Ergora原结构审查模板的Codex原件。本审读核 `self-review-r4-codex/summary.json`、`scope.json` 与 `review.md`：实际succeeded、28.753秒、16份完整文件615,352B＋3祖先资源，完整stdin955,349B／SHA `d96f8a52f31dd1977a62003563a478b432110212cffc137f857dca116341e315`，记录complete_task_and_resources_in_stdin=true，decision=approve，result SHA `1928bb373199c47c39cc29560db27b531750664b08addb6b192fb6eb94e44874`。其正文只给patch0ccbc19e的静态源码意见，明确没有执行tests／工作区修改，不能替代独立运行、installed行为或CI。本审没有重新调用该模板或把汇总的stdin完整性字段当作自己重新解析全stdin的证明。

新package-r4的core／SDK663身份、283资源及依赖通过目前为根提供的状态；installed26＋14仍在跑，最终冻结输入与固定提交证据尚待。故R1及限定源码结论可以关闭，**整片安装验收／最终交付仍未由本审批准完成**。原parent-request留存、M5最后gate、M6正式V2／v3、全部M1c、真实两轮及训练／质量／GPU性能均保持各自开放边界。后续只对准确新原件作同片证据复核，不递归启动新审查或复用旧包成绩。

## 固定r4新安装／模板／提交最终终核

2026-11-16，同一独立reviewer。根据根补交的准确原件，只读核包、完整输入、实际安装结果、实际core reader、模板原输入／回复与Git对象，没有重新运行tests、安装、模型或服务，没有修改产品／Git状态。本节接续上文当时的pending状态；原r1／r2／r3失败及全部冻结原件保持。

**本片最终结论：内部M2a＋M3a／operation-v2 collect/reconcile及相应M1c-O接缝，需求轴 approve／开放 finding 0，维护性轴 approve／开放 finding 0。准确产品提交可由根普通导入；本审不批准或预记公开推送／该候选自己的CI成功。** 这一结论不以未交付邻片阻断本内部用例，也不把内部替身链认证为正式V2或真实训练。

独立查询被审隔离树：HEAD `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，唯一父 `23ad171bf8228bf80b070d6ad866f79d63986d56`，worktree clean，恰八个既有文件1551新增／57删除。独立取两Git对象的完整binary diff，135,245B、SHA256 `0ccbc19e2da14e11eec2b4ff3fa55a55addbb35ad0a80cc6aa40ead40df0192c`，逐字等于原冻结r4 patch与package-r4副本。`candidate-r4.json`与实际Git一致。运行／模型freeze内原HEAD23ad171仍准确表示当时基线，不重写历史为后来的提交；新提交内容同一性由此完整diff及原件核对建立。

新wheel独立重算SHA256为 `4c130b24d69957eafc545cce355e7d8777376a9b7014ad63b5193745bd43558e`。实际读取848份原source/config/test/example/CI输入、663份产品及179份冻结test/example副本，raw SHA与执行位均匹配各原manifest，零差异。再逐份读取wheel条目、core和SDK实际site-packages中的663份产品，字节及执行位均匹配原产品manifest，零差异。包检查脚本与记录使用真实新venv／非editable安装，owner imports均指site-packages；core无temporalio，SDK为1.34.0，两个环境的283reference均PASS、依赖检查均exit0。仅包根AGENTS不进入wheel，嵌套参考AGENTS包含在663完整库存，没有省略原产品资源。

|准确新安装原件|独立核到的实际结果及范围|
|---|---|
|`installed-measurement-r4.xml`／command／result|26 passed／339.646秒，零failure/error/skip；driver340.735秒、exit0。包括原内部reader留存及最后阻塞I/O三参数拒绝。|
|`installed-evidence-r4.xml`／command／result|14 passed／39.162秒，零failure/error/skip；driver40.425秒、exit0。保留原archive/index与callback默认None的实际兼容接缝。|
|`core-full-observation-r4.json`／stdout／stderr|exit0／0.158秒；新core `-I -S -B`实际调用原read_round_observation，stdout报告正确site-packages路径、完整10,000,000B及forbidden_imports空，stderr为空。|

安装两组实际argv均为新SDK Python3.12的 `-I -B -m pytest`、PYTHONPATH=null、冻结test-inputs cwd；没有用源码PYTHONPATH冒称安装。已读执行driver，参数沿run19／20原选择，未缩小成只验helper。core reader原argv显式只加入新core site-packages，实际导入后检查yaml/jsonschema/temporalio/ergora.state均未加载。本审另直接读取其引用的run19完整H observation：10,000,000B、UTF-8有效、末尾LF，raw SHA `8b0ac1e5fa84cb1044ea0b44795cdf410fc04f508727465982126e5d34e5d63e`；不是另造placeholder roundtrip。它证明此真实reader的隔离性，不扩大为整个native callback或全协议所有入口的隔离证明。

模板补做原输入终核：通过新SDK安装的真实 `ergora composition check-input/run-input` 命令、原模板`ergora-structure-review@1.0.0`、实际Codex backend。独立读取scope内16份COMPLETE FILE正文，按各自615,352B合计长度与SHA逐项核，零缺失／差异；三份祖先instructions／SKILL资源完整正文、完整task均出现在实际stdin。stdin与原prompt逐字相同，955,349B／SHA `d96f8a52f31dd1977a62003563a478b432110212cffc137f857dca116341e315`，task SHA与request相符。实际原result SHA `1928bb373199c47c39cc29560db27b531750664b08addb6b192fb6eb94e44874`、decision approve，与28.753秒summary一致。原模型文字仍明确这是完整所供文本的静态审查，无workspace／独立执行或CI认证，未拿它替代上述独立审查和真实安装检查。

已读`final-inputs-r4.json`及生成检查脚本，其原848＋663＋179输入保持由本次逐份只读复核再次确认。`process-markers-r4.json`仅覆盖安装两组37份已捕获完整身份，记录全matching_alive=false；源码49身份仍在其独立post-check-r4原记录，本审没有将这些有限marker扩大为未捕获进程或全系统收尾。没有发现尚需额外运行才能关闭本内部切片的substantiated finding。

后继仍按原计划：完整父request raw受监督留存、M1c-R/V、M5最后执行/native gate、M6正式V2／v3注册、真实history/replay／恢复及两轮、GPU／训练质量和收益均未由本片认证。旧schema1／2/v1、BOOT／stop／一次机会、原六阶段及baseline/candidate证据责任保持；公开导入后的实际内容与准确候选自己的CI仍由根另验。
