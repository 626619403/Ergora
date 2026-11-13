# D2-A2 第二轮原件独立评审

日期：2026-11-13。评审者：fresh-context agent `refactoring_r2_evidence_review`；仅收到原始验收要求、固定身份和证据位置，没有继承实现讨论。按 `maintainable-project-delivery` 及 independent-review brief、AI Hero 索引1.3.2（上游 `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`）、`code-review`、`codebase-design`，由同一独立评审者完整覆盖 Spec／Standards 两轴；本次没有再派生子评审。

## 身份与范围

- 产品基线 `3122487fe57d43188cd5c5a42a787d506a29d5a7`，检查时 HEAD `e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`，分支 `refactor/architecture-foundations`。固定比较命令为 `git diff 3122487fe57d43188cd5c5a42a787d506a29d5a7...HEAD`；其间为 `00922d3`、`e2bbde0` 两提交，本次没有将这些其他片的实现纳入评审。
- 正式要求：[D2计划 A2](../plans/2026-11-13-specialist-presets.md) 第77–81行及第185行；原始要求还包括精确 task／run／budget、原ID恢复、完整材料、全部实际 job owner 清理，以及失败／未知保持。规范来源为 `AGENTS.md`、`docs/PLAN.md` 稳定规则和上述交付 Skill；没有发现额外的项目 `CONTRIBUTING.md`／`CODING_STANDARDS.md`。
- 主要文字范围为[交付记录](2026-11-13-refactoring-journey.md)“独立第二轮准备”“第二轮实际终止结果”两节，检查时全文 SHA256 `fb7ede936c441f30767febccb7efcdaf465590b5142c5fa26af6cacb23ea79bf`；D2计划全文 SHA256 `f864613b6a02b08cfb61e3e51f0cd93b7373e0df79517706cd0fb383a3ab2ee0`。首轮仅作身份区分，没有重新授予首轮通过。
- 原件范围：`.ergora/checks/refactoring-journey-r2/`，两个原驱动 `real-journey-r2.py`／`inspect-terminated-r2.py`，以及持久 `refactor10b` 的 control／runtime／必要非认证配置。读取了原 SQLite 的只读连接、冻结输入、回执／产物、完整历史和 Linux procfs 身份。未读取认证配置或密钥。
- 工作树另含 stdin 修正、B2a数据和其他记录，全部排除实现评审；仅为解释现有恢复入口，读取并核对已安装版本的任务观察／取消／reconcile、原执行器和 job lifecycle。七个相关 Python 文件与 A1 wheel 安装副本逐字相等。本次只写本报告，未启动服务、运行模型／测试、安装、提交、推送或清理进程。

## Spec

第二轮终止事实及取消限制的文字与原件相符；A2完整行为旅程仍未通过。以下两项是实际验收阻断，交付记录已经承认开放，不能据本报告关闭它们。

1. **R2-SP1，P2：原 run 的外部 reconciliation 尚未闭环。** [交付记录](2026-11-13-refactoring-journey.md) 第45行仍列清理开放；要求是“重试与unknown沿原task／run”和清理。7个已启动 job 已有可信终态且 owner 身份不存活，但另外2个已提交 review 请求仍无 receipt，fence 目录为空；原 ingress claim 的 `released_at`／`evidence_digest` 均为 null，`active` 仍指向它。停止托管服务和进程结束不能证明请求已 fenced 或 claim 已归还。最小后续是沿原 task／run／预算使用现有 `reconcile`，为原请求建立 fence，取得余下两个请求的原 owner 终态，再以同一 intent `resume-reconcile` 核全9 job并释放原 claim；保留原 TERMINATED 与取消失败。
2. **R2-SP2，P2：本轮没有三类独立 review 及完整成功路线，历史重复载荷是已见的阻断。** 要求是“work／integrate／verify／review→candidate／evidence”，三类 reviewer 检查同一最终候选。实际只有首个 test-value 会话启动，native 输出为空；另两会话未启动。210次 poll 的输入只有9份不同内容，每次重复完整 `context`，其中含完整 admission；poll scheduled 事件的紧凑 JSON 合计64,162,298B，超过完整原历史文本的90%。原 history-service 在第1,638事件终止 workflow。应在原 submit／poll 接缝及既有 receipt／job 所有者内解决引用与完整材料保存，另片验明恢复、停止和兼容；不得仅提高 history 上限、延长期限或刷新原预算。修正后新的独立成功验收也不能改写本轮结果。

## Standards

在所审第二轮文字及其证据范围内，**新增规范 finding 0**。终止原因、已关闭服务后的连接拒绝、未重放和未完成清理均如实保留，没有把 `terminal=true`、`cancelled` 或单个 validator 的报告写成三类 review approve。原件留在私有运行存储，公开记录没有复制认证内容或本机运行路径。

按 `codebase-design` 检查现有职责：完整 admission 属于原任务创建／提交所有者；receipt 身份及停止证据属于原 job owner；claim 释放属于现有 `_Reconciliation`。后续历史压缩宜在这些现有 Module 的 Interface／Seam 内保持 Locality，不需要另一调度器、结果存储或包装层。本次没有新增产品 Module，Fowler smell baseline 无可定位的新实现违规。上述两项 Spec 阻断不因规范轴无新增 finding 而关闭。

## 已核事实

|身份|原件读回|
|---|---|
|project／task／workflow|`native-refactoring`／`refactor-module-2`／`dev-task/refactor-module-2`|
|原 run|`01a1d37d-b869-7b0f-81bd-d24937826961`|
|fixture baseline／候选|`58fda65bfcd12a3f5babac2d52ed97153f900cb1`／`6e67538230bb7aa28370692992858f41fec53ff2`|
|预算ID／SHA256|`f9c174ad28cb48a398201a62e947d8a3`／`fb24609c48d819068eeb5609888e158062de3f5e3efaac2db561099a5c08ea77`|
|授权／截止|2026-11-13 05:59:43.450433 UTC／07:59:43.450433 UTC|
|冻结配置|7200秒总量，60秒清理保留，7个精确 model slot；stage 1200秒，executor容量1|
|plan／approval|plan `2dda8e13054451d7663c7e830de95d15888b19f2b6b46f5e03367acf77357331`；原批准 signal acknowledged，history第191事件为 `approve_plan`|
|安装 wheel|`ergora-0.2.0-py3-none-any.whl`，1,731,185B，SHA256 `f97741f8a21e78db1813ee9abe86dce357a4fd65c14a11f5d40109be88677143`|

冻结预算的 canonical SHA、definition身份和全部9个 request context hash 均重新计算相等；9份请求均引用这一预算，没有第二轮续领预算证据。7份实际 finalization 的 overrun 均为0，最晚原 test-value finalization 仍余5,523.69854秒。7 slot 是授权上限／精确映射，不代表7个 native 会话已启动。

以下 job ID 均为 `refactor-module-2-` 加表中完整后缀；与9个原 submit 历史事件及请求文件逐一对应。

|job 后缀|stage|执行器／receipt|native session|
|---|---|---|---|
|`468519c303ac175bf7c8fabb`|inventory|SUCCEEDED|`3d245c9bb9b54b00a5da737d5c3364cd`|
|`29c77e683944f0250f07816e`|plan|SUCCEEDED|`20677f32e88b4360be7e24b5d5bc8456`|
|`accbcbc29c989cd48d9f28c3`|work:rewrite|SUCCEEDED|`7c2a97fd63674f749ccc7e22d9f76857`|
|`6714857e49847277c5472592`|work:compatibility|SUCCEEDED|`52b599f7d21a46528888688f841fa549`|
|`65bd4e363e016ec396722c0a`|integrate|SUCCEEDED|可信阶段，无native会话|
|`5ef460a3142b5ab94c4ff7a4`|verify|SUCCEEDED|可信阶段，无native会话|
|`1145684cfd52f66b3691fd82`|review:test-value|FAILED|`90d07ba9eead4a0d80583247747de1f8`，cancelled／-15|
|`27394aae724aee4260cbddb2`|review:correctness|无ledger／receipt／owner|未启动|
|`7a38a723440b2a99a56774ae`|review:structure|无ledger／receipt／owner|未启动|

因此实际计数为9份已提交请求、7个已启动执行器 job、5个 native 会话。rewrite于06:04:39.097119 UTC完成，compatibility于06:04:51.617502 UTC启动，串行且后者冻结 `work_inputs` 保留 rewrite 的完整 receipt／产物。候选差异为 `aliases` 调用现有 `normalize`、一个真实 caller 的非法 alias／generator 停止位置回归及报告；protected caller／checker未在候选差异中改变。原可信 verify 日志记录212个 normalize／6组 aliases、2个 unittest及独立精确 baseline 源码恢复，exit0；本次只核原件，没有重跑这些检查，也没有据此替代独立review。

**完整材料。** 5个实际会话各自的 input prompt／stdin／protocol prompt 逐字相等且 prompt SHA 与 control row 相等。全部 scope 的内容／长度／SHA、来源、冻结 manifest 与每个 input assets 逐项相等，inline resource text 均完整出现在 prompt；祖先覆盖 root、development、所在 preparation／work／review子链及自身。4个成功会话共20资源14,525B，native audit显示每份完整连续读取；首 review 的6资源2,954B已冻结，native audit不存在、stdout／stderr各0B、无result，读取与模型判词未获证明。5份 material 中12项前驱 artifact 文本与原回执产物逐字相等；compatibility 的 rewrite receipt也逐项相等。全部7份已发布回执引用的55项产物摘要重新计算均相等。未启动两叶只有完整冻结的原任务／manifest和request，不存在实际会话输入或阅读证据。

**完整历史。** `terminated-inspection-r1/history.json`为70,666,291B，SHA256 `2d6798714a8208aa7fe189115218f3b8d0a88e5cf7f7e0d04f30d77d03386866`；1–1,638事件连续，首payload JSON与原 `task.spec.json` 完全相等，原 run ID相同，workflow类型为 `ErgoraCompositionWorkflowV10`。末事件为06:22:01.301408400 UTC的 `WORKFLOW_EXECUTION_TERMINATED`，identity `history-service`，reason `Workflow history size exceeds limit.`。210份 poll context与对应持久request逐项相等，三个review各重复58次；没有截断原材料。只完整读取和结构／身份检查，没有执行 Replayer。

**停止和 owner。** 主驱动于06:22:05.870125 UTC取得 shutdown `confirmed`／daemon `not_running`；首review会话直到06:27:39.138345 UTC才 cancelled，job finalization 为06:27:39.752352 UTC。因此服务停止早于这个独立owner的终态。后补 Temporal-only读取于06:33:29 UTC取得相同终态并再次shutdown。全部7份 body／collection停止见证的 `cleanup_confirmed=true`，与对应原 job／budget身份相等。

2026-11-13 06:46:04 UTC读取 procfs，以下7个owner的 PID 均不存在；逐项使用记录的 `start_ticks` 和同一 `boot_id` `731db6b0-5ba2-456a-bde2-3c68c376ed3d`，没有仅凭PID判定。

|job 后缀|owner PID|start_ticks|
|---|---:|---|
|`1145684cfd52f66b3691fd82`|1573140|`251182287`|
|`29c77e683944f0250f07816e`|1551188|`251143928`|
|`468519c303ac175bf7c8fabb`|1546952|`251136261`|
|`5ef460a3142b5ab94c4ff7a4`|1572355|`251180668`|
|`65bd4e363e016ec396722c0a`|1571671|`251179255`|
|`6714857e49847277c5472592`|1564343|`251165527`|
|`accbcbc29c989cd48d9f28c3`|1560435|`251157856`|

9个原受监督进程的 PID／start_ticks 也逐项不存活：`1573307/251182630`、`1551322/251144241`、`1547063/251136378`、`1547230/251136648`、`1572431/251180771`、`1564577/251165843`、`1571024/251177931`、`1560561/251158156`、`1563924/251164691`。loopback 7233／8233／8765均未监听。本次没有全系统后代历史采样；这组事实不扩大为未知进程、排队请求已取消或claim已释放。

## 现有恢复入口与限制

只读代码检查，不是运行验收：相关实现与原A1安装副本相等。

- `task status --run-id` 对非COMPLETED闭合状态投影 `NEEDS_RECONCILIATION`；`task external-status`／`evidence` 的 `_Inspection` 明确接受TERMINATED，读取连续完整历史、全部submit context、回执和fence，不改变lease。见 `reference_task_reconciliation.py:27`、`:133`及原 `dev_platform/runtime.py:74`。
- 原取消错误记录为连接拒绝；对应request仅有intent，没有attempt／result，原历史只有批准signal、没有 `request_cancel`。保留 request ID `supervised-stdin-reproduction`，intent canonical SHA256 `d6cd8f1c33f30edf1555b72455581156cb86257e67f4eca4b1c1fe3ab46d1392`。现有 `resume-cancel` 能继续这个未dispatch的原intent；连接可用且原run已终止时，只会记录 `already_closed`／`not_sent`，不产生fence或lease释放。见 `reference_task_cancellation.py:126`和原 `dev_platform/runtime.py:85`。
- 正式清理入口是 `task reconcile native-refactoring refactor-module-2 --revision 1 --run-id 01a1d37d-b869-7b0f-81bd-d24937826961 --confirm`。它先核原run／无successor及完整9job，再写原request fence并重读。缺两review终态时会保存原intent、返回 `external_confirmed=false`，且保持claim；取得完整可信终态后，才可用返回的精确intent SHA执行 `resume-reconcile`，最后释放原claim。见 `reference_task_reconciliation.py:314`。当前不存在第二轮reconciliation记录。
- `FileAdapter.fence`只发布fence和观察回执，不替代两个job写终态。现有executor会扫描尚无receipt的原请求；`BudgetedJob.supervise`会观察fence，原owner负责停止、收集和终态。故需要正式验证“先fence、再由既有owner处理两个排队请求、没有新native调用、同预算、全receipt、同intent释放”的恢复路径。没有fence直接重启executor时，这两份请求仍有被原扫描器启动的可能；源码没有依据已关闭Temporal状态自动抑制它们。见 `reference_executor.py:846`、`reference_job_lifecycle.py:117`及原 `dev_platform/adapter.py:187`。

## 原件身份与未验出口

下表路径均相对第二轮原件目录；完整历史身份见上文。身份是本次读取快照，不表示原命令成功路线已完成。

|原件|SHA256|
|---|---|
|`submission.json`|`7a99b045535089627e3b0185b9802423c27d44c34fb043f898f840ab5f1872e9`|
|`outcome.json`及后补原status|`c69c6450066ebab810df2e1253ff63562fbca68a956bb4ebe2a022e5b74201bb`|
|`task-definition.json`|`2b754e59c37447889f7d179dcbf60103581097f99a3d32275d0153f3f98d79c7`|
|`commands.jsonl`|`4b5cdc55472c3b83daec9859df7263f54f56c8c7589c66ca97727a780252390f`|
|`cancel-attempt-error.json`|`225788466e089c1e4b859c2bf736e57ba901900701521be21b91aed046c25e83`|
|主驱动及后补 `shutdown.stdout`|`8d3d36d9fab609dd5b6ea9f947789aec040614fbd64c040d40648a72880e3400`|
|`terminated-inspection-r1/result.json`|`bb5a9a6a1285a907e87b3bc9aee959c4334d592a5a645b840c22f8382a5106c1`|

两驱动SHA256分别为 `4ab4e2435be34faf2cbceada2127314a9602d2704a3bfbfa131c583fb738371b` 和 `5fa87afb6e1106c50e4aff8c5e3de486d7a9afe64a0cc33bda4aa21bd64bc177`。主驱动的422项CLI／Git记录均exit0，其中最后status成功读到了失败终态；随后 `REVIEW_READY` 断言没有通过，不能把命令exit0计为完整旅程成功。

仍未验：第二轮原ID重复start、全job fence／终态／claim释放、原历史成功重放、三类review判词、approved candidate export、handoff及独立导出复验、修正后新的完整成功旅程。此轮没有 `repeat-start`／`evidence`／`export`／`handoff`／成功 `history.json`／`journey.json` 原驱动产物。后补历史读取只保全终止证据；原run／预算保持。公开第二轮证据投影和交付记录的最终同步也仍需主agent完成。

Spec：2项P2验收阻断开放；Standards：所审失败记录新增finding 0。未授予D2-A2完整出口通过。

## 同片补核：原 task 收尾

2026-11-13 07:09–07:11 UTC由同一独立评审者只读补核。新增范围为[交付记录](2026-11-13-refactoring-journey.md)“第二轮原件核对与原任务收尾”、PLAN首检查点、原 `recover-terminated-r2.py` 和 `closed-recovery-r1/` 命令／输出／result／端口记录，以及原 `refactor10b` 的保存状态；正文 SHA256 分别为 `73db83ea836612d5223a408753c796c7a148c61006d84a6f7954b85a58de5d10` 和 `71dae4898a38e7ac064c8361569d7afd2cf6382eacc6895480ab8273602f5f90`。本补核未运行产品、服务、模型、测试或Replayer，也未探测端口；第三轮及H片实现均排除。上文原先无fence、两job缺终态和claim未释放的结论保留其06:46时的历史范围。

**Spec：R2-SP1关闭，限原 run 的外部收尾。** 补核支持 `external_confirmed=true` 和 `lease_released=true`，没有发现新增缺口。原任务仍是TERMINATED／NEEDS_RECONCILIATION，原 `original_outcome` 为null；R2-SP2及完整A2成功出口仍开放。

**Standards：新增finding 0。** 收尾沿原A1非editable解释器、既有公开操作和原owner完成，未换run／预算，也未把 `already_closed`／`not_sent` 写成workflow已取消。五个恢复／执行器所有者模块与原安装副本仍逐字相等；新stdout与result JSON内容相等，外层stderr及10条命令的stderr均为空。

实际核对如下：

- 原命令顺序为Temporal-only启动、原status、`resume-cancel`、external-before、`reconcile`、仅启动executor、external-after、同intent `resume-reconcile`、原status、shutdown。两份启动原输出分别选择 `temporal` 和 `executor`，worker始终STOPPED；10条命令中首次reconcile exit1，其余exit0。首次reconcile已写原request绑定fence，但返回 `external_confirmed=false`、两个unresolved且未释放lease，原失败检查没有被省略。
- 原取消intent canonical SHA仍为 `d6cd8f1c33f30edf1555b72455581156cb86257e67f4eca4b1c1fe3ab46d1392`；补得的result为 `delivery:not_sent`／TERMINATED，没有attempt。CLI明确返回 `already_closed`、`cancel_requested:false`、`cancellation_confirmed:null`；原历史没有新增取消signal。
- 原9个history submit context、全部9份request、9份receipt和external-after／保存evidence的job身份及canonical SHA逐项相等。此前7份receipt及55项产物摘要保持；新增两份为原排队review的CANCELLED、各0产物／0检查，actor为 `budget-job-owner`，没有review判词。现在回执总计6 SUCCEEDED、1 FAILED、2 CANCELLED，executor ledger同为9项且逐项相等。
- 原fence canonical SHA为 `08837fc4a7b1f465e64335b4519482a5e4f7bfa05eb4cc7cb3b0b0b4b5f5c2c2`，内容精确绑定原task及request `8a5f9484ccfdef0fa966ef3ca63f38464be2ae2c215396bae43a86abf28a50cc`。完整历史推导的9job身份摘要重新计算为 `a059a88e8554426f76e4499201840d92488443fbca5197c55e35dd22f058488a`，与两次external观察及reconciliation checkpoint相等。
- 原reconciliation intent canonical SHA为 `e47080cc84dd5d599d3e792a533a97d16ce187002175e997f76211c4cc868473`，首次与resume命令保持同一值。保存evidence canonical SHA、result的evidence／release_evidence SHA及原claim数据库的 `evidence_digest` 均为 `cfbd1926953ab1dfbca272bb26668f656b42803cbcb64e9680fa02a546235581`；claim内容与原 `cli-ingress.json`及intent相等。原claim ID `8a3d971035c078eda566e388d39b8cdf09f72fd0daeb6535bc80901bff1d5692` 的 `released_at` 为2026-11-13 07:00:43.375230 UTC，原ingress `active` 表为空，实际支持lease已释放。
- 两个新增owner的原attempt／stopped／finalization都绑定同一原job、admission和预算；body为 `cancelled`／returncode null，`cleanup_confirmed=true`，没有pending、collection或model-attempt记录。其最终候选receipt文件与正式receipt字节相等，finalization文件SHA也相等；均 `cancel_requested=true`、overrun0、无clock error。不能据此声称两场review曾运行。

|新增清理owner对应job后缀|owner PID／start_ticks|可信finalization UTC|原总预算余量|
|---|---|---|---|
|`27394aae724aee4260cbddb2`|`1683073`／`251500014`|07:00:33.098173|3550.352665秒|
|`7a38a723440b2a99a56774ae`|`1683161`／`251500215`|07:00:35.114496|3548.336585秒|

07:09:18 UTC以原PID／start_ticks及同一boot身份读取procfs，这两个owner PID均不存在；原七owner也再次逐项不存活。全部5个native会话ID集合与上文完全相等，状态仍为4 succeeded／1 cancelled，没有新增native会话。原 `task.spec.json` 字节SHA仍为 `e1d4c507169c9d89a9217113e3efd1a66e967fcb84393d6e2df25386e62e0300`，与原history首payload JSON相等；预算ID／SHA、授权／截止和7槽映射均未改变。9份request继续引用同一完整预算。

原历史仍为同一run、1,638连续事件、70,666,291B、SHA `2d6798714a8208aa7fe189115218f3b8d0a88e5cf7f7e0d04f30d77d03386866`及同一TERMINATED末事件；收尾前后status原件SHA均仍为 `c69c6450066ebab810df2e1253ff63562fbca68a956bb4ebe2a022e5b74201bb`。shutdown原回执为confirmed／daemon not_running，驱动保存的三个端口关闭值均true；这是收尾时的原采样，本次没有探测当前其他运行使用的端口。

新增原件身份如下，路径相对 `closed-recovery-r1/`：

|原件|SHA256|
|---|---|
|`commands.jsonl`|`a9dee8460a2e64e718c182c4570ff7134a7691c9317e5d627b4c84cb8c8e1f2c`|
|`reconcile-original.stdout`|`516599c608c63f96bc5c382d2ab616ca8aab9de5d7ead2a184669668af23caab`|
|`external-after.stdout`|`8a0cecc98a8213f9f71505585e318d6bac92e5dd7b94bc9764f13e7ef3adda77`|
|`resume-original-cancellation.stdout`|`3c343c54194681e8c55f8ed570da6807bab59f034f036a465ecea478027f0197`|
|`resume-original-reconciliation.stdout`|`fecdcf9d5d1f30357211919fc83b1210f4f1b8d1e53d0b5c032b4f0768b0249f`|
|`result.json`|`538c84bf47ee6b56f9e87489afb4fac9d27c5403df3c46577e28edcb2cd5e6d4`|
|`ports-closed.json`|`6b079b2b690dd784efa796cddb5bc6bb99af702e4be9934ea5190ddb18ed95f8`|

原收尾driver SHA256为 `6fe1d43fd67bafe25286417b04a8624be8b130a8af2de1567b557d7db398e4ce`，外层stdout SHA为 `004b2c9c002f33a80280da1810a187764bfe7d1423b7d03c3206feb4af2a088f`。

另读取H片的 `original-replay-r1.json`／`installed-original-replay-r1.json`，原件SHA分别为 `ce3f3934b2831fadab95be98e4fe2ff3ab8263771031e10882a247eb26aa3604`／`34ed51fa21f693a70709aa0d9e735f3dc2f827441c332fc9a2e87a32e9ca9b30`。两份记录的A2-r2条目均写明原1,638事件、上述同一history SHA、原input identity `d68da746eca5333354a74278eb95e70d40e6d4eb2087776320ad00fb19a2953b`及 `replay:passed`；此处核准的是记录与本轮原件身份一致，没有独立重跑Replayer或评审H产品。历史兼容重放不恢复已终止workflow，也不授予原候选review通过。

补核后：R2-SP1关闭；R2-SP2保持原历史缺陷／未完成成功旅程范围，完整A2成功及其新独立验收仍开放。Standards新增finding 0；本次外部收尾范围通过。
