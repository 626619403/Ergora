# B3.2：原训练提交的预算绑定与连续截止责任

日期：2026-11-15。承接[预算／executor合同](2026-11-15-training-budget-executor.md)。具体设计r3已独立通过，B3.2b–d已实施并完成受影响安装验收，B3.2e最终本地两轴approve／开放0／0，发布与自己的CI待结算；详见[逐步交付](../delivery/2026-11-15-training-budget-submission.md)。前置B3.1原CI失败由b78边界修正单独闭合，不借本片结果。Kernel专家保留在v3优化路径，本片不改模板。

## 范围与实际接缝

把一次本地授权接入原`training.start → _Submission.run → CheckpointedClient.start_workflow`，并在首attempt之前启动独立截止owner。owner不随观察CLI正常返回或其RPC进程结束而退出，覆盖start RPC、等待native request和queued。实际executor与其后代回收归B3.3；Temporal父循环归Q4.2c。本片不能声称受管训练已经执行或停止。

已核原生`create_job_if_absent`与`fence_and_lookup`共用`training/registry.lock`；因此预算owner沿原adapter持久化同一精确fence，使其后的native create被拒绝。原手工`_Submission.fence`对已submitted的限制保持；预算owner是已显式授权的不同调用者，不放宽手工入口。fence不等待跨RPC持有的原submission锁。缺`/proc`、跨boot、owner丢失和持久来源不完整均不授予新工作，不能按PID或名称猜测、接管或重启。

## 原记录优先

不另建训练slot表、跨home绑定索引或新的start客户端。预算引用直接进入原生state中**原start intent**的可选`budget`字段，恰为`{cycle_id, authorization_sha256, task_queue}`（queue为应用预算协议的固定版本路由），由完整原intent canonical SHA覆盖。旧无预算intent形状、attempt、receipt与memo算法保持；只有新budgeted intent增加字段。来源仍是本home原`training-cycles/PROJECT/CYCLE_ID/{authorization,cycle,ready}.json`及原登记journal／published result，不复制时钟成另一个权威。

prepare首次绑定时核完整来源／ready、当前完整项目与revision、原有限选择包含该实验、完整原observation相同，以及compute剩余。不能接管已有无预算intent；已有budgeted intent只认原引用，不得换cycle／授权。后续原prepare／dispatch／resume必须从原intent发现绑定，省略CLI选择也不会变为无预算。来源缺损的本地观察和原run对账须明确显示unknown；不得因此恢复发送权限。原登记恢复仍只能读回／对账／清理，不能新start。

每候选的原`.attempt.json`就是不可归还的start slot：同一原submission锁下保存，预算路径完成其目录fsync后才允许RPC；失败、NOT_FOUND、取消、重启或换cycle均不删除／重写它。先前已耗用的slot只允许原run对账，不能因时钟仍余而再发送。保留原attempt-before-send、全Experiment核验、memo、receipt和lost-ack合同；不增加独立slot记录与原attempt的双写窗口。

用户入口拟为`training cycle-start PROJECT CYCLE_ID EXPERIMENT --authorization-sha256 SHA --revision N`，从本home原选择取得manifest SHA，调用同一`training.start`。普通start／resume自动沿原intent执行绑定限制；CLI只传输参数。具体名称可在实现时按现有CLI惯例调整，不建立第二流程。

## 独立owner与锁顺序

新增内聚的`reference_training_budget`应用owner，持有预算来源读取、原intent绑定、owner启动／检查和截止清理；真实消费者为原submission和其专用进程入口，后续executor只扩展其生命周期。纯时钟仍归`budget_clock`；原实验／评分／归档／批准不迁移。

每个原start intent在原native state有自己的预算owner目录，保存immutable owner身份及最终观察，不承载实验结果。身份绑定完整intent SHA、原授权SHA、boot ID、PID和start ticks；记录容量沿原1MiB普通文件／no-link／strict有限JSON，写入无覆盖并fsync。owner独占锁与原submission锁分离。首个owner在确认授权、取得自己的锁并持久化原intent／owner目录后写原身份；调用者只有核原身份、同boot真实进程及其锁仍占用才可继续。已出现owner身份后不自动另起一个；死亡／失联为unknown，原attempt与时钟保持。

启动用独立session和单独原日志，不能继承submission进程的生命周期或锁，也不在共享CLI／HTTP启subreaper。owner未确认时不得写attempt或发送start。原dispatch在开始远端lookup之前启动确认owner，在昂贵preflight之后、attempt写入后和实际RPC前重新核原compute剩余及owner。计算时间覆盖全部这些步骤；一次ready／alive观察不能永久授权。

锁顺序为原submission锁→短owner启动／观察；owner自身从不反向获取submission锁。截止时owner仅沿原native registry锁建立fence；不得等被held RPC占用的submission锁。owner锁不持有control DB写事务。调用者查询不等待远端清理；专用owner保持责任直到匹配native完成或已记录fence和cleanup观察。系统调度与文件I/O不承诺硬实时；记录实际deadline、fence完成时间和未确认原因，不把在途或锁阻塞伪装为及时停止。

## 已accepted请求的实际创建边界

预算start使用与原queue分离的应用协议版本queue，queue身份进入原intent的budget引用。原`CheckpointedClient`为预算意图选择该路由，原Experiment／workflow逻辑、memo与RPC客户端保持；旧无预算仍走原queue。保留原managed `training-worker`及其原queue／adapter，新增可选managed `training-budget-worker`仅注册预算queue／预算adapter；原worker不会消费新queue。没有预算worker时任务只能排队，由原owner在截止后fence；不能偷偷回落原queue。原生训练worker、跨host／未遵守此协议的poller不属于本支持范围。

预算adapter实现原ClusterAdapter合同，沿原`LocalTrainingAdapter`复用manifest／runner验证及create/fence算法。仅在create调用的task-local作用域，于原registry锁内部的最后一次`lookup_job`虚调用检查原预算来源、匹配owner与剩余期限；该处不再调用持锁／目录flush的B3.1状态用例，而使用已持久绑定的完整原输入／auth／ready reader，最终clock检查放在原新request写入之前。预算queue缺原intent、缺budget、缺源、错Experiment／queue、owner失联或跨boot均明确拒绝创建；不以“没有budget”回落legacy。已有request的精确读取、fence、poll、gate与人工release不受这个新工作准入gate阻断。task-local标记必须在finally重置，不能污染并行activity或阻止截止fence。

新路由需要应用worker命令与managed services入口支持，不能只改变提交CLI的环境变量。冻结native SDK venv没有新预算reader所需的jsonschema；预算worker使用安装了Ergora及temporal extra的应用Python，缺SDK明确失败。原worker继续使用原native SDK环境，不拼接另一个Python环境的site-packages或修改283参考／requirements.lock。services本域从原training-worker配置复用必要Supervisor设置并合成新program，旧服务选择和构造不变。实现及回归须保护这个真实factory／queue注册接缝，不能以离线声明或修改283参考代替。源代码／文档借鉴现有版本task worker，但不把训练slot与task账本混用。

## 可阻塞操作与持久完成

连续owner在确认后只持有已核原时钟、进程身份与自己的锁，不同步执行可能阻塞的完整来源／DB观察、gate哈希或registry flock。实际观察／fence／控制面清理在该专用owner的受监督子进程中执行，复用`processes.run(supervised=True)`，stop predicate直接读同一原clock并按compute／cleanup阶段停止；不能只传timeout、使用async wait_for或在共享CLI启subreaper。首个owner确认前的完整来源读取不产生start权限，耗时仍计入原期限。

计算截止时停止只读观察，优先用已核缓存的精确原intent／Experiment在cleanup reserve内执行原fence，再做原run／取消对账；源文件运行中丢失也不得改用当前项目或另一次授权。传给子进程的缓存绑定与完整原intent SHA、原owner锁及身份相互核验，不写成第二份可续期授权。fence成功后必须fsync实际fences目录及新建父目录的条目；同步后重读完整fence／binding，只有这一顺序实际完成才能说持久阻断。文件已可见、子进程返回、owner/final记录fsync均不能代替它。锁占用、fsync超时、监管子进程失联或cleanup到期显示未确认，保留实际原件；受监督子进程退出及其后代收尾与将来的训练executor停止仍分列。

## 截止／完成／恢复

owner在原期限内观察同一原项目与job身份。到compute截止、项目漂移或可捕获取消时，先用冻结的完整Experiment／job/path核验并调用原`fence_and_lookup`。无request时仍保存fence；晚到native create使用原registry锁必见阻断。有匹配已完成native结果的先前轮单独保留，尤其不对有效成功且等待人工release的轮统一加fence。

fence之后，仅在原cleanup reserve内按原start receipt或原attempt的原run对账，再沿原取消owner保存／恢复固定request ID／reason的同一取消请求（不为恢复生成新ID）；不得新写start attempt。控制面不可用／没有完整匹配run／cleanup耗尽分别保留unknown和原件。local fenced、Temporal取消请求／控制状态、native result、实际executor停止是不同字段；B3.2的`executor_stop_confirmed`保持未知。来源在运行中丢失不能续期；已核缓存的原绑定仍足以尝试精确fence，但不能宣称完整恢复或继续工作。

读回owner身份时校验原文件、boot／PID／start ticks及原锁；锁释放不是后代停止证据。SIGKILL、跨boot、缺proc、锁或原件冲突不自动重启或重发。正常deadline收尾也不证明B3.3真实后代回收。未来executor交接必须在同一owner责任内完成，ack之前不能退出。

## 可验收子节点

|节点|检查与完成条件|状态|
|---|---|---|
|B3.2a 设计固定|独立核原intent可选字段／旧合同、slot单一权威、版本queue／实际create gate、监督锁顺序与持久fence恢复|r1 request-changes，R1–R3接受；固定r3两轴approve／开放0／0，仅设计层面|
|B3.2b 原绑定与slot|原suite验证同cycle重读、换cycle／缺源拒绝新工作、原无预算保持；原attempt后unknown不得重发|已实施；r3五suite111通过／1跳过；r4同预算／换预算与lost-ack／缺源接缝通过，原失败分别保留|
|B3.2c 连续owner|真实独立进程在首attempt前确认；accepted start先返回后，延迟实际native create越过截止，由owner自动原fence拒绝；held-start跨截止同样拒绝且不等submission锁|已实施；r4受影响安装accepted／held通过，真实Temporal控制流程47.4759秒通过，无executor主张|
|B3.2d 失败与清理|owner真实失联且尚无fence时managed adapter仍拒绝create；受控普通探测阻塞越compute、registry锁阻塞耗尽reserve、fence目录fsync失败／延迟皆保留unknown；原bytes／slot／clock不变，同原fence恢复只flush／核原件且不重启owner；cleanup原run／取消协议及已完成轮保留|已实施；r4原15项12通过／3测试预期失败保持，修正预期与故障marker后四项精准重跑通过；覆盖final文件／目录fsync阻塞，不要求耗尽时存在final|
|B3.2e 安装交付|新非editable core／SDK、原参考283保持、原suite受影响接缝与实际CLI、自身代码审查模板＋新fresh-context产品两轴、普通发布和自己的CI|r4两安装648逐字／283／依赖通过，自身原模板56.218秒approve；原fresh-context最终本地两轴approve／开放0／0，R1关闭；普通发布及自己的CI待前片门禁|

测试沿原`test_training_submission`及其SDK fixture；worker bootstrap和managed配置复用原`test_reference`／`test_services`接缝，不开新suite／矩阵。真实owner、进程身份与文件锁必须实际执行；SDK服务替身可模拟accepted／held／lost-ack与不可用控制面，但不能替测试手动fence。记录未改原实验文件和时钟／slot身份、实际耗时、进程收尾及模拟／真实服务的区别。若发现现有接缝无法满足合同，应在本片明确记录并最小调整设计，再实现，不以未来B3.3或c补证明。

## 设计审查处置

[独立r1报告](../delivery/2026-11-15-training-budget-submission-plan-review.md)需求request-changes／3、维护request-changes／1，原输入7841B／SHA `f758ec8f36de4e051299acfbdac770af97ccfa623e4f285982fbd0ff3afbfd30`保持。R1实际create可能在owner失联／跨boot后获得许可、R2同步依赖会阻塞连续监管、R3原native writer没有目录fsync，均接受。r2增加独立版本queue和实际create临界区的预算gate；把可阻塞探测／fence／取消放专用owner监督的子进程，以原clock实际stop predicate控制；明确fence目录／必要父层同步、原件重核后才保存持久观察，以及可见但未完成时的unknown／同原件恢复。原账本、旧queue、无预算合同和283参考保持。r3进一步明确旧training-worker与新增training-budget-worker是独立可选服务，预算服务使用具有核心reader依赖和temporal extra的应用Python，避免回归core环境使用旧native SDK服务的能力。固定r2原件仍保存，未对r2先行记通过。当前仅修订设计，待同reviewer复核，没有B3.2代码或新运行证据。

同reviewer已终核固定r3两轴approve／开放0／0，R1–R3在设计层面关闭。固定原件12979B／SHA `1b14d600b7d58a41a4d3d5277fd9a435dd3b3eed6e843de1c8d835916b5b2b3a`保持；此段仅同步审查状态。后续B3.2b–e实现、运行、安装和发布仍须本片自己的证据。

## 实施接线记录

预算owner不反向import原submission／cancellation，原预算逻辑与进程入口／adapter接线分别归`reference_training_budget`和`reference_training_worker`，保持静态无环。owner.json保存已完整核验缓存的canonical SHA，helper须与同一活owner身份／锁匹配；该缓存只供原截止清理，不能成为新授权。最终观察恢复只flush／重核同一已有fence，不重启owner、不写新fence或start、不改变原final.json，原最终unknown与当前local_fence持久观察分别显示。r2源码八场景通过不认证新增r3；最终安装与独立产品审查分别结算。

最终记录的文件／目录同步也属于受监督publish阶段，耗尽时可以缺final；原owner结束后仍只完成同一已有fence的持久观察，并保持原unknown／全部原件。自身模板及独立产品审查发现r3实现漏掉此处，r4按原合同修正，原实红和各候选证据保持，不把设计通过转授运行。
