# D真实六阶段旅程：独立证据评审

日期：2026-11-13。评审者为新的 fresh-context 独立 Agent；收到原始要求、固定产品身份、七路径冻结清单和原始证据位置，未继承实现讨论。本轮使用 maintainable-project-delivery 及其 independent-review brief，仅做只读核验并写本报告；没有修改产品、测试、计划或作者交付记录，没有安装、模型调用、服务启动、网络请求、提交或推送。

**最终判词：Spec approve／Standards approve，开放 finding 0／0。** 初审发现一项 P2 记录错误，作者最小修正后已复核关闭。结论覆盖下面固定输入的一条治理旅程及其记录准确性；D0–D3本地证据出口通过，D4普通发布、精确远端身份和本候选必要CI仍待完成，不据此关闭完整发布交付。

## 固定输入与审查边界

产品固定为 `5af9882367bbe5708f1a86ddabc16b2b665e9a49`，父提交 `a00896146c6499f58ae86a5b6b76fa13c3c7c796`，tree `7eb58e030ae79954f1b9f409a5f6720dd38b2a49`。评审开始时HEAD与该产品提交相等；后来工作区的行政片及D2并行变更不改变本次对象，未对它们作产品审查。D没有新增产品实现。

初始记录输入为私有 `six-stage-native-journey-r3/delivery-r1/manifest.json`，SHA256 `507bb11a556eb9fece1e6ce9ab7411103d73ade3b794c08c3149069296982fde`。逐份重算七个快照的大小／SHA256，全部匹配；六份已跟踪Markdown相对固定产品提交的实际diff与冻结 `tracked.diff` 逐字相等，新JSON核全文。最终输入只有D交付记录按SP1修正，其余六份复核时仍与原快照逐字相等：

|路径|最终字节数|SHA256|
|---|---:|---|
|`docs/PLAN.md`|34144|`b847e24b3c7944c58abf5eb5ee29567b9d4fd9156f8afbd8c7616a52e7eefe27`|
|`docs/plans/2026-11-12-six-stage-native-consumer.md`|11676|`792bb8523f771d08aa44503b4e426607b1f29d7c0056cba2dbee03c4c637692e`|
|`docs/plans/2026-11-12-specialist-template-refresh.md`|12253|`aa75b3770a34c15b057fce0d41584b2a98db9752f6ed70b20e70941d20be57bb`|
|`docs/delivery/2026-11-12-specialist-template-refresh.md`|18394|`454a91878a3d826f4c205a0856e33271ca35204be8d25a76138575d34360616b`|
|`docs/delivery/2026-11-13-six-stage-native-invocation-review.md`|16796|`e87fdab838023f964a7c7c26f8108616df682706e14224519ec0951160d4ae58`|
|`docs/delivery/2026-11-13-six-stage-native-journey.md`|8071|`fb3ecd5e680b84a94f300b2fec68cab7e39233b3b03b9c3a29940816a17ff470`|
|`docs/delivery/evidence/2026-11-13-six-stage-native-journey.json`|13445|`0dd9186beb275cb007ad941ae9b8fccc26998923b47d7347d72b6f3a795f3a71`|

D交付记录的初始前像为7602B／`3293ec06f12bcbaa27eb3d6f94beac3e029fde62249198e0d1e30b3c8d64a383`，仍留在原冻结快照。本判词包含上述8071B后像，不能只用原manifest身份代指修正后的七件。

C独立报告原有14500B正文完整保留，仅追加普通本地提交身份补核。独立重算C的 `ready-r2` manifest SHA256 `67da35fc98828b043dcef96432f57d5576d7e88c8797ba62c6bd19355084fd50`，27条路径／616044B均与精确提交blob相等；原报告blob大小、SHA256及前缀均匹配。追加没有把D运行、远端或CI纳入C原判词。

## 两轴判断与finding

|轴|判词|依据|
|---|---|---|
|Spec|approve，SP1已关闭|一个普通父内的单个六阶段实例实际沿原task、Temporal、job、批准、预算及候选所有者运行；完整材料、同ID恢复、原件和清理证据可复核，未测边界明确。|
|Standards|approve，开放0|本片只有交付记录及公开证据投影；沿用现有版本化输入、工作流、模型调用、进程及证据所有者，没有新增调度器、账本、单用抽象、测试或CI。记录将真实运行、历史受控结果和独立评审分开。|

**SP1／P2，已关闭：D1把实际并行writer记为串行。** 位置为[交付记录第14行](2026-11-13-six-stage-native-journey.md#L14)。原冻结表格写“串行工作”且标记完成，但私有原件 `control/ergora.sqlite3` 的 `agent_runs` 保存：

- `964e3db77414472cab0db28d7e706319`／boundary-test：02:52:59.223709–03:00:01.692172 UTC。
- `c6ba14e043fb47babe30432b3368d33a`／knowledge-map：02:52:59.259627–02:58:11.427455 UTC。

冻结composition的work concurrency为4，两叶在同一level；各自materials中的checkout属于不同job。该偏差会让读者错误认为本轮验证了串行writer调度。最小修正是准确记为两独立checkout并行执行，并保留原先错误及未验串行的范围；无需修改治理图或重跑模型。作者后像仅更正表格并追加原重叠时间／串行另片验收说明，逐字diff及上述后像SHA256已核，SP1关闭。其余已审范围未发现新增问题。

## 原始证据的独立核验

**安装及真实入口。** wheel SHA256为 `1da3b270eb63c9c8d20eba96f659bf6a5049288b35c8100cfc143841327dd598`。独立比对固定提交、wheel和非editable安装的全部458个产品文件，逐字相等；wheel／已安装RECORD分别463／468条均按各自记录算法核验。固定提交内283个冻结参考文件属于该已核集合；实际运行安装目录的279个platform正文也与固定提交相等。没有采用当前D2工作树替代运行产品。

原 `commands.jsonl` 的371条命令记录全部exit0，逐条对应stdout／stderr原件。核了prepare、preview、双摘要create、start、plan及approve的精确参数与回执；正式definition6转为保存的input10。批准按原消费者的canonical SHA核验，和请求、profile、计划及history唯一 `approve_plan` 信号一致；不是把带换行文件的原始字节SHA误作批准摘要。

**task／run／原生lineage。** 任务为 `native-governance-3`，workflow为 `dev-task/native-governance-3`，run为 `01a1d2cd-96df-7d38-879f-777f119909b1`。原父 `root` 的 `native-development@1.0.1` 精确转发到 `root/development` 的 `prepared-delivery@1.0.1`。检查了[native调用投影](../../src/ergora/native_six_stage.py)、[版本化输入](../../src/ergora/reference_inputs.py)、[原工作流继承](../../src/ergora/reference_workflows.py)、task创建与envelope读取等消费者；原任务、状态、完成结果、实际会话及handoff中的lineage相等。九个job全部SUCCEEDED，三个必需reviewer的原结果及候选绑定均为approve，结果为REVIEW_READY。

**材料与读取。** 从冻结manifest重新编译完整图，重算实际／准备input树、全部资源定义树及摘要；完整task、编译prompt、运行prompt、协议prompt与实际stdin逐字核对。七次调用的动态材料与原root task、legacy spec、admission及job身份相等；每个结构祖先正文完整进入prompt。由每份资源的原definition／path重新展开全部Skill附件和固定文件，得到的scope与保存scope逐项相等，再直接解码原生Codex JSONL返回页，检查URI、原请求offset、内容、大小、SHA及终页：

|实际阶段|固定资源份数|字节数|原生读取结果|
|---|---:|---:|---|
|inventory|6|2657|完整连续UTF-8至null|
|plan|6|2657|完整连续UTF-8至null|
|work:boundary-test|5|1852|完整连续UTF-8至null|
|work:knowledge-map|5|1861|完整连续UTF-8至null|
|review:test-value|6|2129|完整连续UTF-8至null|
|review:structure|6|2139|完整连续UTF-8至null|
|review:correctness|6|2061|完整连续UTF-8至null|
|合计|40|15356|40个完整UTF-8内容页；失败MCP调用0|

独立重建的逐会话字段与原 `model-calls-audit.json`、公开[证据投影](evidence/2026-11-13-six-stage-native-journey.json)完全相等；包括七份原结果、native receipt、stdout和usage字段的摘要。这里的40份是七会话的固定资源计次，不是40个不同文件，也不是全部动态task正文的字节数。读取／完整供给不证明模型理解。全部后端实际为Codex／`gpt-6.1-sol`；没有把同后端七会话称为异构后端或独立产品评审。

**权限及预算。** 逐节点核父权限上限，并核实际policy的requested permissions和全部permission ceilings与冻结图相等。只读前阶段／review为task-mcp，writer为已接受可信容器中的workspace-task-mcp；没有将声明路径、工具限制或advisory sandbox称为OS隔离。首次prepare的预算原件与正式input完全相等：7200秒wall、60秒清理预留、7个模型槽。九份owner／attempt均绑定同一budget和admission摘要；七份model-attempt的stage→member集合与原slots逐项相等，integrate／verify没有模型槽。该单位是模型CLI会话，不是provider内部API次数、token或费用上限。核了[原模型槽占用及清理消费者](../../src/ergora/reference_job_lifecycle.py)，本轮未以新测试代替原运行。

**重放及恢复。** 独立重算原 `history.json` 41356977B／SHA256 `9e2ebd2abb7fbb5ec87ee9b3e59ad5f24419f596feb886d91276ff544ee894dd`，事件ID连续1–1317。首事件的完整输入与原task.spec对象相等，workflow type为 `ErgoraCompositionWorkflowV10`、queue为 `development-tasks.composition-v10`，原run一致；最后结果与保存outcome相等。使用同一安装包的离线Replayer再次重放1317事件，通过；SDK给出native模块在初始workflow加载后导入的warning，没有重放失败。本操作未连接Temporal服务或网络。原start、repeat-start、保存submission和服务重启后的submission对象相等；只重启Temporal的服务回执中worker／executor等保持STOPPED，原run读回与outcome对象相等。

**候选及交接。** baseline为 `8e4f83f7057495c1e0075471a898f6dfdd900868`，candidate为 `2bd4d5a282ce9ef4dea7bb639fe53265fc16d5c7`。直接查原Git对象：main／HEAD仍是baseline，`agent/native-governance-3`为candidate，变更只有map与AST边界测试两文件／57行，保护源码及可信checks不变。原integrate／verify回执和checks原件均绑定该候选；检查了生成文件及可信检查源码、原detached worktree命令、stdout／stderr及摘要，复验exit0／3个unittest，验收worktree已移除。这里的“独立worktree复验”指原运行后的另一checkout；本评审没有重跑候选检查，也不把它当独立产品评审。

完整handoff SHA256为 `a7fe51ee6f0c49a98251a63174f80cc87126fa360c345834db23090b6d37d9db`。调用已检查源码为只读的安装包 `handoff.verify` 离线复核，返回对象与原verify回执完全相等；包内index与原evidence相等，80个唯一blob／921861B全部重算通过。九job的85处artifact引用亦与各自原文件摘要相等；85是引用数，80是交接去重blob数。该包未证明外部来源认证，也未进行合并或远端写入。

**停止与失败保留。** 逐个核九份owner、attempt、body-stopped、collection-stopped和collected原件；执行／收集均确认成功及清理，collected与原job receipt相等。九个PID／start-tick精确身份复核时均不存活，原管理daemon回执为not_running；只读检查本机TCP状态没有7233／8233／8765监听，原Temporal SQLite仍在。没有运行close-journey，没有创建或删除worktree，也没有替作者清理。此证据不等同全系统后代进程采样。

r1／r2的原prepare失败、独立任务和预算仍保存，二者agent_runs均为0，命令序列均未进入服务start。直接读取内部worker stderr：r1是 `Preparation repository paths must cover the original work unit paths`，r2是 `issue_id must be a positive issue number / IID`；原prepare outcome均cleanup_confirmed，管理daemon回执均not_running。没有以r3结果改写两次失败；r2命名替换导致空目录的附带驱动错误未由本评审重现。

## 已查与未查范围

已独立重算公开JSON列出的八件raw evidence大小／SHA、全部七会话和40资源的完整链、1317事件重放、九owner／七slot、全部job引用产物、完整handoff及精确Git候选；读取了相关原入口／生命周期消费者。原73项安装回归和七模型不重跑，旧B2的v9故障测试及C完整产品评审保留原范围。本报告的Standards判断覆盖D记录及其所依赖的实际调用路径，不是重新审完历史全部产品。

六份Markdown的148个相对文件目标在核验时均存在；不含anchors、外链或Mermaid渲染。目标中新的D2计划和本片公开JSON当时未跟踪。协调者说明先提交独立验收的D2-A1计划再提交D全局记录；该提交顺序及最终树仍须发布时核对，不能把当前可读链接当作已经进入提交的证据。D2、Apache行政片、后续A2及方向专家的实现／判词不属于本评审。

未验Claude成功或异构后端、串行writer、v10运行中取消／到期故障、GPU训练、Windows服务、多个native、任意外层混合图、Forge内部全部会话、生产多机、远端tracker写入、推送或CI。单治理组合的真实运行不能授予这些能力通过。普通发布、精确远端Ref和本候选自己的必要CI仍是交付责任，不因本地两轴approve自动完成。
