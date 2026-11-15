# c1b1：子训练预算进程的跨调用生命周期

日期：2026-11-15。准备基线为本地固定 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `refactor/architecture-foundations`。c1a2总投递／对账的本地与固定提交两轴已通过；普通发布仍按前片准确CI队列。本文细化[父计划c1b](2026-11-15-training-cycle-workflow.md)的实际进程前提，当前为设计准备，尚未修改产品或开放自动派发。kernel专家继续保留v3。

## 问题与最小范围

原 `training.start` 冻结意图后，在 submission 进程中由 `BudgetedStart.ensure_owner()` 创建独立预算进程。将整个调用直接放入短S-H，会使预算进程成为原subreaper的后代；H结束时原 `processes.run(supervised=True)` 必须回收它，`start_new_session`不能改变此归属。不能跳过、复制或豁免原reaper。

实际安装的无业务探针已经核实：H创建的独立session惰性后代会在原S收尾时退出；调用方创建的兄弟根在另一次S收尾后仍活，随后精确TERM／wait收尾。修前r1的存活观察未处理已消失的proc文件而退出1，原失败保留；仅修probe观察的r2退出0／0.582秒。这不是实际预算owner／训练／重启验收。

另一前提来自[SDK与进程边界研究](../research/2026-11-15-training-cycle-sdk-boundary.md)：Python的asyncio子进程transport在关闭／析构时可以kill仍活的子进程。实际本机ThreadedChildWatcher持有transport，惰性probe中正常teardown／GC／父退出后确实仍活，不能写成必然kill；但公开API没有detach，这次存活不能升格为跨watcher保证。兄弟归属本身不足以证明所有生命周期；不调用private transport detach。

本片只交付完整的内部候选准备、原预算根启动／确认和原start的existing-only接续。没有新的总Workflow、execution request、测量接受、后继候选、独立cycle服务或公共按钮。原schema1手工启动保持；schema2控制器路径不再允许短H补启预算owner。

## 所有权与拟用接缝

|现有owner|本片责任|必须保持|
|---|---|---|
|`training`|从原 `_submission` 提取已有短事务prepare阶段，让原start／resume及新的H消费者复用|原revision／manifest／budget／完整意图检查与手工返回语义；SQLite不跨网络；不重复实现一份prepare|
|`reference_training_budget`|复用原owner锁／初始化锁、完整预算来源和原 `own()`；生成原根启动材料／日志位置；schema2 `ensure_owner`只接受原已活owner|不再从schema2短H执行Popen；schema1原launch锁及行为保持；同一原clock／能力／停止与phase reaper；不重启丢失owner|
|`reference_training_worker`|原 `_CycleOperation`承载普通H操作；异步调用方持有真实spawn及传送／取消句柄，budget入口负责自己的初始化／日志|父loop不读State／SQLite／业务原件，不打开业务日志，不把业务搬到线程；实际预算执行仍为独立OS根进程|
|`training_execution_protocol`|严格mode／controller／ordinal与一次compute∩control窗口；不同H阶段共享同一原窗口|stdlib-only、原schema／GATE_SOURCES key集合与283参考保持；不引入第二账本／current-round|
|原submission测试／fixture|沿真实caller检验跨调用、取消、重复及恢复；迁移内部schema2测试的准备方式|原schema1接缝、固定RUNNING最后gate、非归还start／launch、旧失败与原候选身份保持；不加新CI矩阵|

所有新增函数须有真实本片caller或明确私有算法职责。若原owner无法内聚承载，应先缩小或重新审查本片，不造通用process-host／任务调度器。

## 已有实证与选定的待审启动方式

选定供独立设计审查的方式是仅把 `subprocess.Popen` 的**OS进程创建**交给短的 `asyncio.to_thread`，保留Popen句柄；后续用公开 `connect_write_pipe`传送完整有界材料，用非阻塞poll观察退出。不得用线程执行预算、业务文件或数据库，也不把长时间 `wait()`交给默认executor，以免正常loop退出等待整个训练。Popen析构源码无kill；研究r2六个惰性root／1.469秒实际核了async与Popen的正常teardown／GC／父SIGKILL，两类均仍活，原清理harness逐个精确TERM／wait-15，proc全部消失。此证据只固定OS句柄行为，不认证实际budget、clock、一次投递或取消竞态。r1的pidfd包装缺失导致的probe收尾失败及精确恢复保持。

只有独立具体设计审查闭合后才实施该方式。实际预算root跨正常loop重启及原clock仍须产品实证。Popen创建尚未返回时shield只能保留future，不能中断OS创建；default executor正常收尾可能等待它，不能据惰性probe保证这个阶段有界退出。必须验晚到句柄、原窗口已尽后不传送／不dispatch及真实收尾。若公开接口不能满足，记录不可用和替代方案，在原所有权约束下重新设计，不关闭sandbox、不修改原reaper、不以更长的活动超时代替跨调用生命周期。

## 完整顺序与不确定性

1. 内部异步候选start调用方从原snapshot固定本次compute remaining∩control的一次窗口；prepare／owner确认／dispatch的不同H和root传送均消费同一窗口，不因轮询重新创建bootstrap。原controller完整workflow／run、intent SHA及ordinal进入mode封套。H重读全部原件并核固定RUNNING来源，不接受外部替换的候选列表。首次活动早于receipt时，先走c1a2原唯一attempt对账，不能直接给子start授权。
2. 在原短事务prepare阶段冻结该子start意图，验证原完整budget／manifest／revision。已有意图须完整绑定同一controller／ordinal；原attempt／receipt只允许观察／对账，不造新意图或补slot。
3. **复用原子intent作为唯一offer，不新增launch账本。** 原 `.lock`下prepare只有一个`created=True`；只有该次完整H回复可携带可启动材料。已有intent且原owner未确认，无论是否有start attempt，都只返回unknown／观察，不Popen；已确认则只使用该原owner。H在原intent发布后同步原目录；丢回复／失联／启动失败不删intent／再造offer。原 `.budget/launches/<intent.operation_id>/`只放该次日志，不作为第二启动权威。完整材料预检及32KiB封套校验不截断；失败必须明确说明子intent可能已存在，不声称未占用。
4. 根材料是完整原submission payload、子intent SHA、调用方完整进程身份及原一次window；这些来自原cycle operation请求和唯一prepare回复。父loop只接收材料与明确的路径环境覆盖，密钥继续继承进程环境，不能把密钥值保存到材料或history。命令固定为本应用解释器的原budget入口；子进程初始化时自行装载原注册环境，核原子intent／schema2／完整controller及仍活的原调用方／原窗口，打开原日志。日志位置由原budget owner按原intent.operation_id生成，环境只含原注册路径；Workflow不重建它们。
5. 父loop在原窗口内只发起一次实际spawn并异步传完stdin；spawn future必须被shield并保留至真实句柄可得，取消future不能当进程已停。另一H核原 `owner.json`完整内容、PID／start_ticks／boot、原owner及初始化锁，再返回原owner事实。确认不能续原clock。
6. 原schema2 `ensure_owner`在实际dispatch最后调用点强制existing-only，任何缺失／损坏／变身份／已final都不补启owner；dispatch-H核同一完整确认事实。原 `_Submission`仍负责原attempt-before-send、原SDK投递／history／memo对账；父许可覆盖真实SDK动作，原四gate不变。仅提前一次H检查owner存在是不够的。schema1仍使用原手工launcher，不因为内部消费者改变其行为。
7. **交接点是调用方收到完整且匹配的owner确认。** 在此之前，取消／超时仍保留spawn句柄，先取消并收尾实际短S-H，再向已知原根发精确TERM并保留实际wait；确认回复丢失也属于未交接，不能重新Popen。不得强杀正在使用唯一reaper的owner并宣称子树已停。OS无法及时退出时保持实际等待和unknown，SDK loop仍响应其他任务。
8. 完整确认后，原预算根按原total自持；普通活动取消／异常／unknown和worker正常关闭只收尾本次短S-H、停止非破坏性的退出观察，不向已交接根发送TERM。总controller取消／用户stop必须另走原b2b用例，发布parent veto、逐owner通知、drain和实际停止观察；普通活动的CancelledError不能冒充这个流程已完成。c1b1只提供内部start／观察及原stop消费者的接入责任，不提前宣称c1c总Workflow取消消费者存在。取消发生在确认后lookup／attempt fsync／SDK回复等待的三个窗口均须分别验收此区别。根退出观察用非阻塞poll且保留Popen引用；正常loop teardown不kill根。cycle崩溃无法补通知时只沿原身份／clock对账，不重启或返还机会，不统一取消此前已接受轮次。

## r2固定封套、原窗口与恢复行为

原四字段operation封套及既有mode保持。下列**新mode**才增加`start_context`字段，完全字段集按表验证；不接受额外字段或以缺字段退回手工launcher。identity沿原schema，ordinal必为原位置，snapshot仍是原完整authorization／policy／有序候选；controller使用原五字段`{protocol,workflow_id,run_id,intent_sha256,ordinal}`，必须与原receipt、子intent和identity.ordinal一致。

|新mode|start_context完整字段|bootstrap／结果|
|---|---|---|
|`prepare-candidate`|`{controller}`|仅首次构造固定compute∩control窗口；完整结果为`new_offer`或`observed`，不自动dispatch|
|`confirm-candidate`|`{controller,origin_operation_id,intent_sha256,root_process}`|沿最初窗口；root_process是本次实际Popen句柄的完整`pid/start_ticks/boot_id`。仅在原owner完整记录、context／capability、活进程和两原锁均匹配时返回`owner_confirmed`及完整owner；否则unknown|
|`dispatch-candidate`|`{controller,origin_operation_id,intent_sha256,owner}`|沿最初窗口；owner是上述已确认完整原记录。只能接续本次新offer；原最后gate通过后调用原SDK start或观察原已发生事实|
|`reconcile-candidate`|`{controller}`|像原reconcile-controller一样固定一次1–60秒纯观察窗口；允许原compute结束后只查／补同一receipt，没有dispatch或Popen分支|

`new_offer`结果必须含完整子intent SHA与一个有界launch对象。launch只含`request`和`environment`；environment为H生成的原PYTHONPATH／AGENTFLOW_CONFIG_DIR／AGENTFLOW_STATE_DIR路径覆盖，不含密钥值。request固定为`{protocol,origin_operation_id,parent,window,submission}`：protocol=`ergora-training-cycle-root-v1`，origin为本次prepare identity.operation_id，parent为其完整进程身份，window等于其原bootstrap；submission完整字段是`{project,control_home,experiment_id,timeout,intent_sha256,mode}`，mode=`controller-owner`。project／路径／timeout来自原prepare上下文，子intent SHA来自刚写入的原件。根入口从该sha重读完整intent／budget／controller，不接受根材料另选候选或续窗口。原日志目录只由budget owner按intent.operation_id派生。根装载原native environment后仍保留完整应用＋选定native的原PYTHONPATH，不能因环境更新使其后代导入另一版本应用。

`observed`结果必须给出原submission事实及原owner观察，不能含可启动launch；`owner_confirmed`必须含同一子intent SHA和完整owner。unknown必须保留原operation身份及已知原件事实，不能以空对象充作成功；原32KiB编码界整体拒绝，不截断身份。原操作框架自动附加的mode／ordinal／operation_id／output／stopped等观察继续使用，不另存可变状态。

**一个调用只有一个窗口。** 首个prepare operation的id、parent和bootstrap由原调用方保留在内存；confirm／dispatch必须显式传同一bootstrap，构造器不得重算。H和原submission最后点共用原协议读取者，重读已有`operations/training-cycles/<origin_operation_id>/request.json`，核它确为同一prepare-candidate及完整project／cycle／authorization／controller／ordinal／parent／snapshot，bootstrap逐字一致。此文件是原operation请求，不是新增运行／交接账本。根bootstrap同样核原来源与仍活的原parent／原窗口。

dispatch-H把这一次完整operation传给原submission调用；schema2 `ensure_owner`拒绝没有该内部上下文的dispatch，核完整确认owner且不Popen。原SDK `start_workflow`的最后点（包括前置lookup与attempt同步之后）再消费同一个window，SDK等待与H的原S监管均不能超出它。此检查只约束本次子start，不能套用到之后原budget worker创建job或native执行的生命周期；那些仍消费其既有gate与原compute／total。已有schema1不带新上下文，行为保持。

|恢复时的原事实|本片允许的行为|必须拒绝的行为|
|---|---|---|
|无子intent|新显式start可沿原prepare取得唯一offer；是否仍有原执行时间由原授权／window决定|另造实验／controller或改变原候选|
|有intent、无可确认owner|只观察unknown；原offer已失联，不恢复|重新Popen、删intent或用原resume尝试启动|
|owner活、无start attempt|同一次仍活调用持原offer／parent／window才可进入dispatch；失联后的新调用只观察`unconfirmed`，即使root仍活也不补SDK start|借新operation窗口调用原resume的无attempt分支|
|attempt有、receipt无|`reconcile-candidate`直接复用原reconcile算法读取同一run／memo，不经过可能dispatch的resume入口；NOT_FOUND保持unknown|Popen、再次SDK start、换ID／run|
|receipt或明确rejection已有|只读原事实／固定run状态；旧root最终停止与原manual-release分别观察|把旧成功当新offer或将新parent续入原启动|
|owner缺失／变身份／损坏／已final|原记录／同一receipt观察与原停止用例；执行权未知或拒绝|最后点补启owner或修复原件|

这选择允许留下未曾启动的intent或活着但没有start attempt的预算根：失联不自动补副作用，原预算根仍按原clock清理，后续只读与显式stop可用。恢复不会创造新的offer／control窗口或执行权。当前只有设计，不是产品验收。

## 验收与步骤状态

|节点|可验收结果|当前状态|
|---|---|---|
|b1.0 所有权设计|实际reaper／stdlib teardown证据、原唯一prepare offer与真实caller、取消／重启责任；新的fresh-context设计两轴|原reaper惰性probe及stdlib六case通过／原失败收尾保持；独立r1提出R1交接／取消与R2封套／恢复缺口，已在r2补完整确认交接、mode／结果／共享窗口及恢复表；原reviewer r2设计需求／维护性两轴approve／开放0／0，R1／R2仅设计关闭，产品待实施|
|b1.1 原prepare复用与existing-only|原schema1行为保持，schema2短H无预算Popen；完整controller／ordinal／原源漂移仍拒绝|未实施|
|b1.2 原预算根跨调用|实际原预算owner同一PID／start_ticks／boot／clock，在S-H结束后及cycle正常重启后存活；真实原owner与后代最后收尾|未实施；惰性兄弟probe不替代它|
|b1.3 重复／丢回复／取消|慢claim／慢初始化、spawn pending／stdin／确认前后取消、缺失／损坏／变身份、原预算尽；恢复只观察且SDK start／native launch不重发|未实施；各按真实状态转换选择原接缝|
|b1.4 包与审查|新core／SDK非editable安装同一、283／依赖、适用原接缝、SDK-free观察、自身原模板及新的独立产品两轴、固定提交|未实施；分别记录旧失败／新候选，不继承probe或前片通过|

每步更新[本片交付](../delivery/2026-11-15-training-cycle-owner-lifecycle.md)。完成本片本地与固定提交门禁后，再做c1b2真实cycle服务／normal-stop配额，然后c1c总Workflow；只有c1d完整接受门槛闭合才能派发候选2。
