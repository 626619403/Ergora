# c1a2：总控制器一次投递与固定运行对账

日期：2026-11-15。基线 `836179e9ff3eae0795f0c22bf4c58f0bab1ea777`，分支 `refactor/architecture-foundations`，开始时工作树干净。承接[总Workflow计划](2026-11-15-training-cycle-workflow.md)的c1a及[完整记录合同](2026-11-15-training-cycle-controller-contracts.md#2-总投递身份与每轮来源)。c1a1意图与c1b0普通窗口已本地验收／独立批准；普通发布仍逐片等待准确CI。本片不改变六阶段、出生同意、原clock、唯一reaper、子实验start／launch、原证据或人工release；kernel专家保留v3。

## 目标与具体消费者

在原 `_CycleOperation` → S → H 中增加内部 `submit-controller` 和 `reconcile-controller`，完成原intent→不可变attempt→一次逻辑SDK start→固定run receipt，以及不重发的原运行对账。现有cold inspect继续无SDK可用，并可观察本地总投递事实。所有业务文件、SQLite、原native配置和SDK连接初始化留在H；异步父loop不打开业务文件或数据库，仍使用原四task、shield取消和`processes.run(supervised=True)`。

|owner|本片职责与真实调用|保持的边界|
|---|---|---|
|training_execution_protocol.CycleAdmission|共用原attempt完整期望值，供原bind和新记录producer；完整封套增加上述mode及原窗口消费|stdlib-only，原bind字段与原错误／停止优先级保持，原stop-total／cold inspect不续期，GATE_SOURCES key集合保持|
|training_cycles|总投递原件读取／验证、短本地claim及同一receipt／拒绝事实无覆盖保存；由worker的H调用|原 `_load`／`_record`／status／State事务／parent许可；不导入SDK或反向导入worker，不添加可变current-round或第二账本|
|reference_training_runtime|共享完整started input、memo、type、queue核验；新增允许关闭历史的投递查询|原lookup_controller仍要求原固定RUNNING状态，不以历史查询放宽四个最后gate；describe后取得的handle须固定run再取history|
|reference_training_worker|真实H装载原选定installation／config，SDK start与对账编排，返回有界typed事实／原件引用|旧budget入口、普通prepare及stop分支保持，不新增进程driver、服务、Workflow或公开入口|
|原submission测试／fixture|真实SDK编码与历史解析、原件／clock、S-H阻塞和实际取消接缝|原CI分组和相关既有fixture，不给字段或提示句逐一扩浅层测试|

实际SDK 1.34.0编码探针已证明：start返回handle的`run_id`为null，准确启动run来自`result_run_id`。使用公开 `Client.start_workflow('TrainingCycleWorkflow', complete_input, id=original_id, task_queue=original_queue, id_reuse_policy=REJECT_DUPLICATE, id_conflict_policy=FAIL, memo={CYCLE_MEMO_KEY: intent_sha})`，不复制SDK传输或关闭sandbox。一次逻辑调用内SDK的同request重试与应用层再次投递不同；本片不在应用层重发start。

## 原件和顺序

沿原schema1字段：attempt为原schema、intent SHA、workflow ID和完整workflow input canonical SHA；receipt为完整attempt加非空精确run ID。意图由原c1a1准备，SDK分支不临时重造意图。拒绝为完整attempt字段加reason与run_id：preexisting_run必须有非空冲突run，lookup_rejected的run为null，两者只允许无attempt；start_conflict允许服务未给run的null且必须已有attempt。网络异常不写拒绝。部分、错身份、冲突或损坏的现存文件不覆盖或修复。receipt与拒绝不能同时被当成功。

1. H验证原完整snapshot、schema2授权、原durable ready、项目revision、source／native配置及同一普通窗口；已存在attempt时直接进入只查路径，不重新claim。现存receipt始终固定其run；未准备或坏原件明确拒绝。
2. 没有attempt时，先查同workflow ID；这次lookup只取服务事实，不能直接决定本地拒绝。落拒绝和claim共用原短SQLite reservation，进入后先重新读取全部intent／attempt／receipt／rejection；若已有attempt，丢弃旧的“无attempt”拒绝决策，转只查，绝不阻断并发合法投递。确认仍无attempt且无其他终态后，才可保存preexisting_run或lookup_rejected；服务已有运行即使输入相同也不接管。网络错误不保存“服务明确拒绝”。
3. 唯一attempt在原短SQLite本地reservation和parent共享许可下无覆盖发布并同步；本地事务在网络前结束。竞争者只读已存在attempt，无权发start。同步失败也不回收slot。
4. 真正start前重新核原revision／ready／完整意图、parent stop和同一普通窗口；parent共享许可持至SDK动作返回。调用前任何等待／同步都计原窗口。stop或耗尽可留下attempt，但不再start。
5. 成功回复取`result_run_id`，核非空固定身份，再保存同一receipt。超时／断连／取消／被回收可能已有服务副作用，保留原件并返回unknown或沿原取消传播；不能删除attempt重来。明确AlreadyStarted冲突与unknown分别记录。
6. 有attempt无receipt时只describe同ID；latest.run_id必须与服务的first_run_id一致，再固定该首run读取完整started input／memo／type／queue；NOT_FOUND保持unknown。发现任何latest后继（包括continue-as-new／retry／reset）都保持unknown，不补receipt、不遍历链或借后继状态继续。本控制器本来只支持一次总run，SDK禁重试；已有receipt或可信run hint则只查该精确run，不能借关闭历史通过RUNNING gate。无receipt时查询到的服务事实必须足以认证原单次运行，证据不足返回unknown；不能仅凭ID或最新status补receipt。后继首次子活动可把其认证run交给同一查询／receipt算法，必须在任何子start前关闭receipt竞态；本片不声明该活动消费者已经存在。

receipt／拒绝也用同一短reservation重新_load完整plan／authorization／ready并核原SHA，再读投递原件后无覆盖发布；此时只认证原件，不以已stop／expired为由拒绝观察。已有相同终态只同步重读，不替换字节／inode，矛盾终态不写入。reservation结束才允许任何SDK RPC。并发验收必须覆盖前置lookup晚到时另一请求已经claim、包括其尚未收到start回复的窗口，保证旧lookup不能写出拒绝。

原生单次ID属于本协议；人工复用／重置这些ID不是恢复方法。对原历史链和当前SDK字段的实际判定先用真实本地Temporal作只读metadata探针，再固定最小实现；不以服务替身默认字段或推测说明“不跟随新run”已验收。停止、过期和历史观察不产生新的执行权；最终四gate仍各自检查原固定RUNNING run。

真实SDK 1.34.0／CLI 1.9.1内置Server 1.32.0的独立metadata探针已核：正常首run的describe.first_run_id与started.first_execution_run_id均为其run；continue-as-new／retry的latest指向后继，但二者仍保留原first_run_id。独立产品审查随后指出直接丢弃latest会漏reset；新增真实reset探针证实latest可变而first_run_id及原started仍不变，latest的initiator甚至仍为0。因而将原r2设计收窄为上述“未收receipt不得遇到任何后继”，不声称可恢复不受支持的多run链；原receipt存在则只查其精确run。首run已关闭仍可认证其原件，但不能通过原RUNNING gate。

探针还明确证明：人工ALLOW_DUPLICATE复用已关闭ID，会产生新的first_run_id、初始attempt1和相同input；仅凭最新describe／初始history无法证明这不是人工再开的一次。支持的无receipt恢复因而以本协议独占ID、唯一attempt和REJECT_DUPLICATE为前提，不能声称能识别相同材料／memo的人为完整重放。已知人工复用／reset或来源不足时保持unknown、不得借新run继续；完整run hint只能来自原启动回复或后继真实SDK活动身份。此局限必须在后续手册和验收中明确；不以first_run_id当“全历史从未复用”的证明。

## 普通投递与对账观察的时间

`submit-controller`沿c1b0固定一次原compute remaining∩control timeout的BOOT窗口，父pipe／wait、S stop_requested与H最后动作消费同一payload；不重开授权或内部重试窗口。原compute已尽不spawn新投递。

`reconcile-controller`只做原投递元数据／SDK历史对账，没有start或训练分支。与cold inspect一样在spawn前固定一次1–60秒观察截止，H仍读取并认证完整原授权；允许在原compute结束后观察已发生的事实、补同一receipt，绝不续原clock或授予执行权。该mode无候选ordinal，不把外部列表或可变状态当权威。poll、取消及同operation恢复仍保留原请求窗口；本片没有自动跨进程恢复服务。

## 可验收节点

|节点|真实证据与限制|状态|
|---|---|---|
|设计|原owner、SDK返回对象、原件格式、历史run身份、两种窗口与取消语义；新的独立设计核对|[新的独立设计报告](../delivery/2026-11-15-training-cycle-dispatch-design-review.md)两轴approve／开放0／0；R1旧lookup拒绝竞态在r2设计层关闭，产品另验|
|实现|原owner接实际S-H caller；完整原件、一次start及对账，不触发子实验|原四owner已接入；R1 reset身份与R2终态授权重读的源码修正已由独立reviewer复核关闭，最终本地两轴approve／开放0／0|
|SDK与原件|真实SDK＋内存服务替身覆盖accepted、lost reply、NOT_FOUND、关闭run、冲突input／memo／type／queue、linked run拒绝、SDK等待中原授权损坏；竞争claim只一个逻辑start，RPC期间独立SQLite writer可完成；原attempt／receipt bytes／inode与clock不变|修前r2共17通过；R1／R2两项先实红，修后最终安装r1共67通过；删两行不可达guard后r2原bind／gate／冲突／并发接缝7通过。各归原产品身份，不认证实际Workflow或训练|
|真实边界|实际S-H投递／对账；阻塞H的数据库／同步／SDK等待时父loop响应且stop／取消沿原reaper回收；普通耗尽不spawn，对账只观察；core无SDK仍可读原本地状态|原安装接缝通过；r2 SDK-free异步cold inspect1.210秒，父业务I/O禁止、7原文件bytes／DB与窗口保持（该probe未核inode）；74已知actor活匹配0|
|安装／审查|新core／SDK源包安装同一、283原参考、适用原gate与架构回归；自身模板、新fresh-context产品两轴、固定提交与逐片发布|r2两安装各652三方逐字同一／283／依赖通过；原r1共67通过与r2精准7通过分列。自身完整供稿r2真实Codex40.251秒approve；178输入与安装收尾同一。最终12文件scope与收尾已由原独立reviewer核过，本地需求／维护性两轴approve／开放0／0；固定提交待，逐片发布仍等前片准确CI|

每步更新[交付](../delivery/2026-11-15-training-cycle-dispatch.md)。真实cycle PID／normal和stop配额、标准sandbox总Workflow、接受后继轮门槛、CLI／页面与可信CPU两轮仍由父计划后续片交付。
