# c1b2a：独立 cycle 服务与普通／停止配额

日期：2026-11-15，r2修订2026-11-16。状态：已按[接口审计](../delivery/2026-11-15-training-cycle-service-design-audit.md)固定具体选择，待原独立reviewer终核；产品未实施。承接[原控制器合同第4节](2026-11-15-training-cycle-controller-contracts.md#4-workflow活动和阻塞通路)与[c1总计划](2026-11-15-training-cycle-workflow.md)。前置c1b1已固定`d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，本地76＋7安装接缝和最终／固定提交独立两轴通过；原包SHA256为`565aefd026e01f83470af5e49a74d1743c3919779a4b4a217fc2dc56755eb29b`。后续BR资源／CI fixture联合候选仍另验，实施前再固定准确基线。kernel专家继续保留v3。

## 交付目标与范围

提供可由原Supervisor启动的独立`training-cycle-worker`进程，与原`training-budget-worker`使用不同PID／event loop。在cycle进程的非阻塞loop中分别注册普通和停止Worker，各自保留活动并发配额。普通活动只消费已冻结授权及真实SDK controller身份，经原H读取／核对资料，再复用c1b1的start或只对账消费者；停止活动复用原独立writer／逐owner通知／drain／实际执行链观察。

本小片先交付服务边界与inspect／start／reconcile／stop的真实消费者。总`TrainingCycleWorkflow`、显式execution消费者、测量collect／接受／rounds、第二候选和公开自动运行按钮分别后接，不注册会假成功的空实现。没有总Workflow时，此服务单独启动不会发起实验。服务boundary验证中的最小Workflow夹具只能证明SDK路由与进程隔离，不能称正式总Workflow或训练旅程。

## 已核源码事实

|实际owner／接缝|现状与本片复用点|
|---|---|
|`reference_training_worker._serve`／`main`|只注册原ExperimentWorkflow与Activities，8活动配额；保留此入口和其原loop。新入口在同一已pin的owner，不往原loop塞第二Worker|
|`_CycleOperation`／`_CycleCandidate`|已分别持有原S-H与独立Popen预算根；业务文件、State、锁、native注册装载及SDK调用在H／根。继续调用同一算法，不另建process-host|
|`stop_live_controller`|先经冷inspect得到原完整snapshot，再独立启动writer／drain／各候选notify与observe；一个分支阻塞不串行挡住另一分支。各观察不等价于durable stop|
|`training_execution_protocol`／`CycleAdmission`|严格operation封套、原compute∩control一次窗口、父共享准入／可见stop、原intent／attempt／receipt及完整controller身份已有owner。新活动来源核对放在这个边界及H，不放CLI／页面|
|`reference.training_budget_worker_command`／`services._prepare`|前者用应用解释器与所选native安装，后者从原training-worker配置生成独立服务命令／日志；服务目录与管理身份已有归属，不修改283参考配置|
|Temporal SDK 1.34.0|已在实际安装只读核`activity.Info`有workflow_id／workflow_run_id／workflow_type／workflow_namespace／task_queue／attempt；Worker有各实例独立max_concurrent_activities与graceful_shutdown_timeout。这里只核API，不等于真实服务注册通过|

## 输入、身份与恢复合同

活动业务输入沿原六字段workflow_input：protocol、control_home、project、cycle_id、input_sha256、authorization_sha256；候选动作只再携原ordinal，不接受另外一份候选／baseline／command列表。服务从真实`activity.info()`取调用Workflow ID／run／type／namespace，不信任业务输入自述身份。普通活动的来源与ordinal在H中和原完整授权、controller intent、attempt、receipt及有序位置重新核对。

首次活动可能早于客户端receipt保存。缺receipt时只沿c1a2原同一attempt／memo对账，匹配实际SDK run才继续；NOT_FOUND／不同run／reset／旧receipt／不完整started input均保持unknown或明确拒绝，不补新attempt、不发第二次start。原case不能以“活动已启动”直接自授预算owner或SDK投递权。

具体活动、H上下文和结果采用下节r2接口；沿原strict转换器，不另建数据库表或可变current-round。SDK身份的采集在activity adapter，完整记录认证在H／原protocol。只读inspect与start的最后执行gate必须分开，前一次认证不能替代真实SDK动作前的父许可、完整owner及同一窗口。

普通活动先取得一个有界冷观察；后续start只使用c1b1自己的compute∩control一次窗口，prepare／Popen／传送／confirm／dispatch共用，不因活动轮询刷新。已存在intent时不再授offer；已有attempt只能调用原reconcile路径。SDK producer的副作用活动maximum_attempts=1在c1c实现；本片服务也不能把unknown或重投的activity请求改成新的执行机会。

停止输入含同一原身份及非空reason，由独立stop queue消费原total剩余，不占普通槽。取消普通activity仍按c1b1区分交接前／后；取消停止activity或服务关闭时，必须继续持有已创建的原S/H／Popen并完成原退出观察，不能以Future取消冒充回收。不能给已接受历史轮统一发送Temporal cancel。server terminate与实际本地停止分别记录。

## r2固定接口与审计处置

下列选择接纳接口审计A–D，属于原c1服务接线，不实施WA的新通用Hook／人类设计关卡。

|注册活动名称|业务参数的完整key集合|首版真实动作|
|---|---|---|
|`ergora.training_cycle.inspect.v1`|`workflow_input`|冷认证及原事实观察|
|`ergora.training_cycle.start.v1`|`workflow_input, ordinal`|仅ordinal0的原单次offer／预算根／dispatch|
|`ergora.training_cycle.reconcile.v1`|`workflow_input, ordinal`|已有intent／attempt只对账，不prepare|
|`ergora.training_cycle.stop.v1`|`workflow_input, reason`|原独立writer／逐owner通知／drain／执行链观察|

`workflow_input`严格为前述六字段。SDK adapter用真实`activity.info()`构造`activity_source`，完整key为`workflow_id, workflow_run_id, workflow_type, workflow_namespace, namespace, activity_id, activity_type, task_queue, attempt`。拒绝standalone／local activity、缺workflow信息、错误type／queue；workflow_type为`TrainingCycleWorkflow`，activity_type为当前注册名称，queue按下节对应Worker。两SDK namespace与实际client.namespace必须相同；不接受业务自述source。attempt>1的start只能观察／对账，不产生new_offer。ordinal>0的新start在intent／Popen之前明确拒绝`successor_not_enabled`；reconcile仍可观察已有同binding原件。c1d以前不提供allow_next旁路。

原operation严格封套增加可选`activity_context={workflow_input, activity_source, service_namespace}`，后者来自创建Worker的实际client。增加冷mode `inspect-controller-activity`，`snapshot=None`；H内完整读取原cycle／授权／ready，比较六字段及原controller intent。适配后的候选prepare／confirm／dispatch／reconcile和stop分支随同一context；原`cycle_start_source`同时核后阶段与原prepare request的context逐字身份。不带context的既有c1b1调用保持原合同；新SDK活动不能省略它。protocol保持stdlib-only，不接SDK／State反向依赖。

认证复用原`_dispatch_controller`的reconcile算法及`lookup_controller_submission`：原intent、唯一attempt必须已存在；缺receipt时以**真实activity workflow_run_id作为run_id传入lookup**，完整核description／first-run／started original／六字段input／两处memo／type／queue／非retry-reset-CAN，在`_record_controller`写回**之前**证明同run。已有receipt先比其run再查；NOT_FOUND、错run、坏attempt、错input／memo等不补attempt、不重发controller，不让候选出生。正常认证在H内核实际查询client.namespace与service_namespace／SDK namespace；旧intent没有namespace字段，不改版本也不冒称从旧记录认证过它。

**已绑定停止保留离线路径。** stop有完整原receipt时，H用原receipt及可信source核本地binding，不新添每个notify的远端查询依赖；receipt缺失才沿同attempt认证，失败就明确unknown。原显式本地`stop_live_controller`保持原行为，不新增SDK前置。普通认证可观察已关闭run；new start在offer前及原最后SDK点仍核RUNNING／原父许可，认证本身不授执行权。

冷认证全过程只开一次1–60秒BOOT观察window，读取、SDK查询、receipt同步与结果都消费它；多个H复用同一bootstrap，原构造器的observation分支需接纳传入window，不能逐次续期。新start认证后另开且只开一次原compute∩control窗口；已有intent／attempt不重开执行机会。reconcile可在compute／total已尽时有界观察，不能转start。

### 完整结果与容量

SDK结果协议为`ergora-training-cycle-activity-v1`，共同key为`schema_version, protocol, action, status, workflow_input, controller, observation, inspection, operations, runtime_status`；schema_version为1，action对应四活动，status只说明完整观察／unknown，不是全局stopped或接受证明。controller保存原`workflow_id, run_id, intent_sha256`或尚未认证的null；observation保留原预算／clock观察，inspection指向本次冷H结果，snapshot仅供同次activity内存消费者，不发history。runtime_status沿实际H／SDK结果，不凭Worker RUNNING推断。

每个operations项完整保存`operation_id, mode, ordinal, operation_stopped, supervisor_returncode, result`，result恰为`ref`或`inline`。ref仅由S在实际读到原`helper/stdout.txt`之后，用raw bytes算`{file:"helper/stdout.txt", bytes, sha256}`，路径根由原control_home／operation_id推导；adapter不读业务文件。S仍先发原stopped帧再读结果，原bounded frame完整验证通过后才能声称ref存在。原H的observation文件引用继续留在原stdout；不写新聚合账本。

没有完整可验证文件时，inline保留全部父侧unknown／失败事实和完整reason；未spawn明确stopped=false／returncode=null，不能与已stopped但丢result混为一谈。inspect及start保留全部实际operation，stop必须保留原`2+2N`全部分支。各分支构造失败只记该分支，其余可构造peer继续，所有已创建task仍在原finally实际收尾。stop_visible／durable／drained／通知／reap／durable_stop_confirmed／executor_stop_confirmed的三值事实由原H拥有，不推断新的总stopped布尔。

业务input、完整frame及SDK result各自≤32KiB；SDK侧用本服务实际DataConverter编码，并检查包含metadata的完整protobuf Payloads.ByteSize。超限以非重试`cycle_activity_capacity_exceeded`失败，保留已发生原件／完整worker错误，不截reason或分支，不将未生成文件的异常说成已归档。丢completion后仍只能对账，不能重授start。审计中66refs18,613B／66unknown16,103B仅是合成表示探针，真实32候选完整fanout仍待本片验证；不承诺所有路径／异常必能装入。

## 服务、配额与结果边界

新服务使用原应用解释器及可选`ergora[temporal]`；core未安装SDK时，普通离线读取／inspect仍可用，启动该服务可见拒绝。服务启动期沿原native环境装载；运行中的SDK loop不读业务State、JSON、日志，不执行fsync／flock或同步等待。不得把这些操作放入线程伪装成非阻塞；OS-only Popen创建继续沿c1b1的明确例外及生命周期合同。

独立入口为`reference_training_worker.cycle_main(installation)`／`_serve_cycle()`，由`reference.training_cycle_worker_command`供`services._prepare`管理；服务名`training-cycle-worker`，复制原配置但`autostart=false`，独立日志。normal queue固定`ergora-training-cycle-v1`、注册inspect／start／reconcile；stop queue固定`ergora-training-cycle-stop-v1`、只注册stop。首版各1活动槽，独立Worker／queue，不能从普通槽借配额；不额外暴露无人读取的调优字段。原budget Worker的queue／8槽／进程／注册及283参考不改。旧运行Supervisor缺新program时明确拒绝，沿已有显式stop／shutdown／restart重启，不偷偷reload；RUNNING仅是OS状态，task_readiness仍not_checked。

### 关闭合同

新服务Supervisor显式`stopwaitsecs=70`，不继承原15秒。这是观察期限而非所有OS情况的收尾保证；既有service control客户端1–60秒到期仍可返回unconfirmed，不提前丢弃应用清理任务。SIGTERM／SIGINT与单Worker fatal都进入同一closing流程：先停止normal新领取并显式`shutdown()`，其grace为0以使取消进入原清理；normal实际S/H及未交接Popen仍收尾时保持stop Worker可运行；normal终态后才shutdown stop，等所有已领分支及两个run／shutdown task实际完成，再关闭loop。重复取消必须继续持有这些任务，不先cancel全loop冒充完成。

已完整确认的预算根沿原total自持，服务关闭不通知它；未交接根按c1b1精确通知／wait。停止整个cycle仍走原显式stop并分别观察durability和实际执行链。70秒到时Supervisor强杀只能证明服务PID退出，业务停止为unknown／待原件对账；不能返回clean stopped，也不能补launch。不可中断OS创建／存储I/O可使有限期限内无法完整回收，这一支持限制保留。

活动input／result仍≤32KiB。完整大内容保留原operation文件，返回完整typed事实及准确原件引用；不得切掉候选、身份、异常或分支后称完整成功。现有snapshot或停止聚合无法容纳时，明确容量拒绝并保留已经发生的原事实，不假定32候选一定能运行。需要聚合引用时必须确认原文件实际存在并绑定原operation，而非加第二份停止账本。SDK编码、业务成功、durable stop和子树回收分别验证。

## 实施节点与客观验收

|节点|最小变更与原owner|验收证据／禁止越界|
|---|---|---|
|b2a.0 具体身份与设计|固定前置提交；沿原protocol／H明确SDK来源认证、首活动receipt竞态及typed封套，明确独立queue与关闭顺序|新的fresh-context设计两轴通过后才改产品；不是仅凭本文批准实现|
|b2a.1 服务入口|原worker内新增独立入口与普通／stop活动注册；reference提供真实命令，services管理新服务／日志／SDK可用性|实际Supervisor两个worker PID／loop不同；core无SDK拒绝新服务但原读取保持；不改旧Worker与283|
|b2a.2 有界普通活动|适配inspect、原start与只对账reconcile；真实SDK身份由H认证，不新增候选调度|同run正常消费者到达原H；错input／run／ordinal不Popen／不start；receipt未落盘只恢复同一attempt，NOT_FOUND不重发|
|b2a.3 独立stop与关闭|直接消费原stop_live_controller，独立Worker槽；普通H持真实锁／fsync阻塞|真实SDK路由下stop仍被领取，writer／逐owner异步通知，原reaper／实际wait完成；各durability结果不互相替代|
|b2a.4 安装与交付|新非editable core／SDK、原适用service／submission／架构接缝；自身模板、新独立产品两轴|完整包／资源／283保持；真实服务与fixture范围分列，所有进程／端口收尾，更新手册及精确发布状态|

测试优先扩展`test_services.py`、`test_training_runtime.py`及`test_training_submission.py`已有真实注册／S-H接缝；只有独立风险确需新测试文件时才动CI分组。SDK服务替身用于协议反例，真实Temporal／两个OS服务用于queue与loop隔离，不拿前者代后者。此片没有实际训练／GPU／质量或测量收益验收。

本r2已固定审计A1／A2／B1／C2的选择；原独立reviewer需复核具体接口及关闭语义后再改产品。运行验收必须分别覆盖补receipt之前的实际SDK run反例、ordinal1无任何新动作、真实32候选完整refs／unknown／容量失败、normal槽与真实存储阻塞时独立stop领取、SIGTERM／SIGINT／重复cancel／fatal及强杀unknown、无SDK／旧Supervisor兼容。方案不足时先缩小片或修订接口，不增加无caller的通用活动总线。

每步写本片交付；前置产品固定后再新建交付记录和设计审查，随后b2a接线。之后的execution／collect、标准sandbox总Workflow与c1d完整接受／后继门槛仍沿[c1原计划](2026-11-15-training-cycle-workflow.md)，不提前称自动循环可用。
