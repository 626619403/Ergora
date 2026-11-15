# B3.3c：同一原预算下的真实执行与停止

日期：2026-11-15。上位设计r2与c2具体记录合同r2均获新的fresh-context设计两轴approve／开放0／0。前置c1固定`75285e3271bb93271eaea050ca7812cb0cd98b5a`自己的CI43676697981及原产品独立终核已闭合。c2最终r6两安装各652逐字／283／依赖通过，原submission84及processes／architecture24通过／4跳过；真实Temporal／native五类旅程91条CLI及全部收尾通过。自身原模板65.888秒两轴approve，原fresh-context独立对最终完整scope及原件两轴approve／开放0／0，R1–R5关闭；普通发布、自己的CI与原reviewer固定发布终核仍待。详见[逐步交付](../delivery/2026-11-15-training-managed-execution.md)。kernel专家继续在v3路径。

## 交付目标与已有owner

允许用户显式选择一个原已submitted、已有精确native request的实验，由其出生时声明支持执行的原预算owner，驱动派生原生`training_executor.process(..., admit=...)`。Git准备、两臂runner、archive和MLflow仍用原算法；取消及共同期限覆盖整个执行子树，包括新session后代。控制fence或其fsync阻塞时，执行停止仍独立进行。停止事实、持久停止证明、native训练结果和控制面结果分别呈现。

沿[生命周期调研](../research/2026-11-15-training-executor-lifecycle.md)、[总执行合同](2026-11-15-training-budget-executor.md)及[phase监督](2026-11-15-training-budget-phase-supervision.md)，保留原intent、start attempt、slot、receipt、memo、authorization／clock和实验账本。新记录只链接同job的执行生命周期，不建SQLite表、第二调度器、第二start／signal客户端、训练器、比较器或收益评分器。原v2.2的283字节保持。

当前真实消费者及必要变化：

|owner／调用者|当前边界|本片最小变化|
|---|---|---|
|`training`→`reference`→原`_Submission`|用户应用入口与原已submitted身份|薄的显式execute／只读execution入口；先沿原receipt及完整run/history/memo核验，不另发start|
|`BudgetedStart`／原budget worker|出生身份、共同期限、控制phase与final|明确出生能力；保持旧schema1控制合同；只有原显式请求才进入执行|
|`_BudgetPhase`|串行阻塞`run`，每phase独立S及真实reaper|先提取本owner内非阻塞start／poll／finish，保留原run合同；原owner并行监管执行与控制，不加阻塞磁盘thread|
|派生原`training_executor.process`|在原executor.lock内调用admit，拒绝旧started／手工接管managed目录|直接消费b协议，不改delta、不复制主体|
|`processes.run(supervised=True)`|专用S中的原subreaper及后代回收|继续作为唯一业务回收算法；S的stop predicate用原clock／owner身份／catchable取消，不以timeout参数冒充截止|
|原`_Cancellation`|持久取消意图、固定run及唯一signal attempt／history恢复|对匹配的新执行owner增加精确本地停止通知；远端signal仍走原入口，不重试未知派发|

新增的native gate具有真实跨解释器职责：在应用侧准备与读取同一协议记录，在native解释器内提供原锁内callback。它不能import State、SDK或应用配置框架；不得为每个动作新建转发模块。无替换实现族，不引入ABC／全局插件总线。

## 分片及门禁

|节点|完整可验收行为|状态|
|---|---|---|
|c0 完整设计|固定出生能力、显式权限、无重复launch、锁内gate、并行停止、记录及恢复；新的fresh-context两轴计划审查|r1生命周期问题保留；r2同reviewer设计两轴approve／开放0／0，R1仅设计关闭|
|c1 非阻塞phase生命周期|原run仍工作；存储在专用S内，父owner可同时监管两个独立phase；没有新runner权限或owner能力|r2两安装650逐字／283、24控制回归／16架构、真实控制旅程／自身原模板与新独立产品两轴通过；75285e3自己的CI及原独立终核已闭合|
|c2 单job显式受管执行|出生能力、原request请求／不可重用launch／锁内attempt与ack，原native过程、独立执行S及持久stopped；取消、状态、原件恢复和手册一起可用|已按[具体记录合同](2026-11-15-training-execution-records.md)r2接线；最终r6安装108通过／4平台跳过、91条真实CLI及收尾、自身两轴approve已验；整片独立终核及发布／自己的CI待|
|c3 安装与真实控制旅程|各产品片自己的非editablecore／SDK身份、受影响原suite、实际CLI、原模板审查、新独立产品两轴、普通精确发布与自己的CI；c2另验真实Temporal＋短CPU生命周期|逐片验收，不等最后一次才检查|

c1与c2分别交付，不能把c1的并发phase演示记为训练已执行。每步更新本计划、[逐步交付](../delivery/2026-11-15-training-managed-execution.md)和[总计划](../PLAN.md)。后继Q4.2c才自动调用这些已有应用用例；Q5.2有据重构、Q6严格发布和真实GPU／业务训练条件保持。

## c1：保留原合同的并行监管接缝

`_BudgetPhase.run()`继续提供当前四mode的串行合同。内部拆分为该类自己的启动、一次非阻塞poll与最终结果收集；`run()`循环调用同一生命周期，不维护第二份管道／终止算法。多phase监管是`BudgetedStart`的实际需要，不上浮为通用workflow引擎。

父owner在业务启动后只做非阻塞pipe读写、selector、进程poll／signal、内存身份比较及原clock的内核时钟／proc观察。现在run内的output.mkdir／stderr.open移入对应S；父侧不读取业务文件、不拿registry／executor锁、不fsync、不读取helper stdout文件。S在启动时准备自己的诊断目录／stderr，然后调用原`processes.run`；失败前的stderr由有界非阻塞pipe收集。诊断不承担授权或终态权威。

S仍在`processes.run`返回、实际回收之后先发匹配stopped帧，再读取／发送有界result。父侧在stopped之前只能TERM请求safe reap；不能为了赶total deadline先SIGKILL一个尚未回收的S。stopped之后S不再创建任何子进程，只能直接做自身的记录读取／写入／同步及观察；这些存储动作可以在total期限被终止。管道短写、完整帧身份、offset、旧结果容量及异常unknown合同保持；各mode仍使用原compute／cleanup期限。父owner不启subreaper。

单纯非阻塞Popen／proc及Linux回收不能承诺对内核不可中断I/O的硬实时截止。实际安全回收若超过total，保留overrun；缺stopped不伪称按时停止。测试观察窗依据实际授权剩余及回收余量，不缩短合法cleanup。

## c2：出生能力与显式执行入口

新reader兼容原owner schema1的严格原字段，继续控制观察／fence／清理；不得为旧活owner补文件、修改身份、重新启动或据新二进制追认执行能力。原预算identity、intent及phase仍schema1，不因owner记录升级而重写。

新owner记录使用schema2：原intent／authorization SHA、boot／PID／start_ticks、原context SHA，以及`execution_capability`。该字段要么为null（仅原控制），要么为严格对象，包含执行协议`ergora-training-execution-v1`、原`training-executor-admission-v1` descriptor SHA、固定native安装／解释器路径及出生时实际应用gate／共享clock源码身份。能力仅在新owner出生、原派生来源完整验证后写入；legacy来源的新owner仍仅控制。依赖实际可用性须另核，能力本身不授启动权限。已有schema1记录保持原件，新代码不能重启它获得schema2。

拟新增：

```text
ergora training execute PROJECT EXPERIMENT \
  --revision REVISION --intent-sha256 ORIGINAL_START_INTENT_SHA \
  --run-id ORIGINAL_RUN_ID --request-sha256 ORIGINAL_NATIVE_REQUEST_BYTES_SHA --confirm

ergora training execution PROJECT EXPERIMENT
```

execute不start、不替unknown寻找另一个run，不接受用户传任意Python import、patch、job目录或runner。`execution`是离线只读观察，不查询SDK、不启动owner／执行器、不补缺记录、不重试。CLI只解析，应用用例仍在training／reference边界。

执行请求须绑定：schema／kind／协议、control home／project／revision、原登记来源、start intent与原start attempt／receipt canonical SHA、authorization SHA、workflow及精确run、job ID、完整native request原字节SHA、出生owner记录canonical SHA、明确confirm及操作者身份。完整原request必须严格等于四字段`schema_version:1, job_id, experiment, runner`，其中完整Experiment与runner分别匹配原intent；不止比较job ID。request原字节SHA与canonical语义SHA分开。

请求持久化和最后准入分别核验。应用helper先验证当前原登记、ready／compute、原submitted receipt及同run初始完整Experiment/history与intent memo、允许执行的RUNNING控制状态；不可确认或已终结拒绝新工作。再核协议来源、无旧started／result及精确native request，写不可变请求。所有网络／存储耗时计入原clock，写后再核余量；慢发布不授迟到执行权。

普通cycle-start、queue worker、重启、status、resume-start及旧登记恢复均不产生执行请求。无能力、部分请求、旧owner、不同revision／run／request、取消／过期或来源变化明确拒绝；不退回手工run-local。不把同用户可改文件的容器称安全隔离，支持范围继续要求新native状态目录和全部参与writer使用b协议。

## 请求、launch、attempt、ack与stopped

固定位置为原`training/jobs/EXPERIMENT/managed-execution/`；路径由原job计算，禁止用户配置。创建部分目录即受b协议的无hook保护。元数据各最多1MiB，普通非链接文件、完整父路径检查、strict finite／duplicate-key JSON，无覆盖发布及文件／目录同步；已有原intent16MiB、cycle10MB容量保持。

|记录|作者与顺序|完整身份与恢复|
|---|---|---|
|`request.json`|显式应用helper在原job的局部execution锁内保存，写后再核时钟|上述完整授权引用；同内容重读只观察，换内容拒绝；不直接调用process|
|`launch.json`|原owner的受监督admission helper，在Popen执行S之前独占保存／同步|原请求canonical SHA、原owner、单次launch／attempt UUID、预先固定执行S nonce、原clock／protocol引用；已存在便永不再次返回可launch许可|
|`attempt.json`|native callback持原executor.lock，在任何started／Git之前发布并完成同步|同launch／request／run／native request SHA、原owner、实际S与native执行进程boot／PID／start_ticks；重复或部分发布拒绝|
|`ack.json`|同callback在attempt同步后发布并同步，返回原主体前再核截止／owner／fence|同attempt canonical SHA及实际接收进程；缺失不等于未执行，不授重试|
|`stopped.json`|执行S实际reap完成并发出匹配帧之后，直接读取／写入及同步；该S此后不再spawn任何子进程|同launch／attempt／ack／request、实际S身份、原run的process结果与实际reap事实／时间；无匹配attempt／ack不得补造成已受管成功|

**launch不是新的start slot。** 原start attempt仍唯一、不可归还。launch预留解决“执行S已生但native hook尚未写attempt就被强杀”的窗口：helper只有在首次独占创建并成功同步、仍在compute内时，向同活owner返回一次内存launch许可。已有launch即使内容相同、没有attempt／ack、Popen失败或返回丢失，都只观察unknown，绝不再返回可启动许可。原owner不重启；显式execute重试和恢复也不能重建该许可。Popen前中断可能保守地零执行，但不能通过缺文件重新执行。

helper在launch写前后核同完整授权和原来源、精确run/memo／native request、无result／started、活新owner及原期限。原owner收到完整成功帧后，在同一次活生命周期里只调用一次Popen；原owner若丢失该帧便不启动。该机制不替代executor锁内最后gate。

## native解释器内的最后gate

执行S使用所选native安装的`.venv/bin/python`和原requirements，运行实际派生process；不能用应用Temporal extra冒充MLflow环境，不能把另一个venv的site-packages拼进sys.path。native gate只使用stdlib及已有native依赖；复用现有`reference.worker_command`的bootstrap方式，临时加入包父路径仅import ergora，立即移除该搜索路径，后续经ergora.__path__装载固定应用包自身代码，复用现有byte-source validator和原budget_clock。不将应用site-packages目录留作依赖搜索路径，也不导入State／SDK／yaml／jsonschema；不另造一套package spec或环境bootstrap。实施时必须用不含应用依赖的native解释器实测这个导入边界，不能只凭静态推测。

原source validator仍拥有完整279字节校验；native侧和应用侧使用同一实现，不复制一份manifest校验器或时钟算法。应用gate及其实际stdlib依赖身份在出生能力及请求中固定；缺源／换源不启动，不以路径相同追认升级。原native core中的PYTHON／ROOT／STATE／CONFIG必须与原登记、选定native解释器及payload相同。

调用派生process时，callback在其原executor.lock内再次完成：

1. 核原namespace／request／launch的完整记录和预定S nonce；核当前native父进程确是原S及原活owner，核birth能力／原clock。
2. 重读native request原字节，严格解析、完整SHA及语义均匹配process所读的record和原Experiment／runner；不接受schema bool、额外字段或半文件。
3. 核精确fence缺失及compute尚余，拒绝已有／部分attempt或ack；已有native result仍只是原process只读返回，不能追认受管执行。
4. 保存并同步单次attempt及ack；同步耗时继续计入原clock，最后再核owner／compute／fence，才返回原Git／runner主体。任一失败不写业务result，也不删除已消耗记录。

任意网络、磁盘读写、锁或fsync均在S所辖native子树中，S本身以原clock独立监督，不在stop predicate中读业务磁盘或RPC。CLI外层预检与此锁内gate之间的竞态仍由b协议原started检查保护。

## 并行停止、取消与完成判定

原owner在launch前用受监督monitor/admission helper处理完整来源与原run核验。执行开始后同时监管执行S及控制monitor S；两者各有自己的子树、session和原subreaper。到compute期限／catchable取消时，owner立即通知执行S停止，并独立启动原fence phase；不等registry锁、fence文件／目录fsync、控制取消RPC或执行reap之一先完成。原S自己也核同一clock及原owner的boot／PID身份，父owner死亡时停止已有子树；父owner不能因此推断已停。

原`_Cancellation`在明确原取消意图和同start receipt／run归属后，向匹配的新执行owner发送本地停止通知，之后远端signal仍走原attempt／history接缝。通知用pidfd绑定实际进程、核原boot／start_ticks，不按名字、用户、陈旧PID或宽泛pkill；不可确认就报告未确认，不扩大信号对象。旧仅控制owner继续原合同。取消意图丢回复不增加第二signal客户端；本地停止是安全收尾请求，不是远端取消成功回执。

执行S继续使用原`processes.run(supervised=True)`，其TERM handler只置取消标记；实际回收不得被catchable取消打断。run返回后先向原owner发匹配stopped帧，证明本次业务子树已完成实际reap。随后由同一S直接读取匹配attempt／ack并写入／同步持久stop，最后读取结果；在发出stopped之后禁止再创建任何子进程。原owner继续非阻塞监督这个无子进程的S至total；不能让stopped的锁／读写／fsync拖住已完成的业务停止。native result可能在reap之前出现，不能让completion提前终结owner。持久stop发布卡住时，原owner已收到reap帧，total后可以终止只做直接存储操作的S，留下“实际回收已观察、持久停止证明unknown”。不得以“新子进程仅发布记录”为由在stopped之后另spawn publisher再杀S。

`executor_stop_confirmed`只有完整匹配request／launch／attempt／ack／durable stopped且真实reap顺序成立时才为true；否则为null／unknown，不能凭native result、control完成、PID消失、锁释放或不存在attempt补造。观察保留原训练结果与gate，停止成功不等于训练成功；gate passed也不代替人工release／采用。

对有本次managed namespace的job，原completion须另核受管stop合同才可结束owner；fence helper同样不能因先见native result就跳过仍在执行的子树。没有managed request、此前已完成并等人工release的旧轮，继续原只读完成合同，不统一加fence。预算final只引用上述分别观察和overrun，不合成native训练终态。

原owner／执行S被SIGKILL、跨boot、缺proc、身份冲突、source漂移或缺生命周期原件都不自动重启。存活S仍可按原clock清理它自己的子树；观察者只记录有证据的事实。当前无可委派cgroup／宿主权限，不能承诺任意SIGKILL后无孤儿；真实故障验收须主动收尾本次已知PID，不占用其它项目。

## 验收与成本边界

优先扩展原training_submission／training_runtime／processes／architecture suite及已有native fixture，不为每种文件形态复制整套服务／CI矩阵。测试保留真实锁、实际spawn／reap、原native主体和原记录状态转换；替换叶依赖时明确实际范围。

|风险|必须实际经过的接缝|
|---|---|
|c1回归与并行|旧四mode／完整大帧／短写／异常S／TERM safe-reap保持；两个S同时有setsid后代、一个helper卡文件而另一个实际停止；父owner不启subreaper|
|新权限关闭|schema1活owner、schema2仅控制owner、普通cycle-start／status／resume／旧登记恢复和单起queue均不生执行S或attempt|
|原身份与原子准入|同run完整history/memo／Experiment／runner／request字节；原锁争用及预检后手工started-crash；原锁内拒绝不落业务result|
|不重复launch|真实在launch同步后Popen前中断、S启动后hook前强杀、attempt后ack前失联、ack后CLI丢回复；重复execute和恢复均保持原件且没有第二次业务进入|
|实际全周期|短CPU原process确实经过绝对`/usr/bin/git`准备、runner／新session后代、archive及原track调用；各阻塞／取消点在同预算内回收，MLflow可用本地HTTP服务替身但不能替换整个track后称真实tracking验收|
|控制与执行解耦|实际持registry锁或让fence文件／目录fsync卡住；在释放故障前核执行子树PID已消失／被原reaper收完|
|结果与证明顺序|native result先写但仍有后代时不得完成／确认停止；stop发布fsync卡住时先核实际reap、最终保持持久unknown；原gate／result／start slot字节不改|
|实际安装／服务|新core／SDK源码-wheel-site逐字、283保持、受影响安装suite；同一实际CLI旅程与真实Temporal＋短CPU原控制流程；依赖可import不等于MLflow服务或真实训练成功|

各失败与修正运行保留原身份，不重跑未改GPU／训练。c2的CPU合同不认证算法／模型／数据质量或性能收益，真正B3仍需明确workload、模型／数据、设备／预算及独立质量oracle。有限自动循环、动态baseline／采用权不在本片。

## c0 r1问题处置

r1同时要求先发stopped再起publisher helper，并允许父在stopped后于total终止S。这会使后来新生的publisher失去reaper；独立计划评审用原processes.run构造顺序探针，实际观察S被SIGKILL后同PID／start_ticks的publisher仍存活，随后已精确收尾。接受这一生命周期问题，r2改为业务run全部reap后先发匹配帧，此后S只直接读取／写入／同步及观察，不再spawn。stopped前safe-reap与stopped后可终止的边界因而保持一致。原r1和探针保留；当前只改设计，不以构造探针替代未来产品验收。

现有worker_command的包自身bootstrap另经Python -S便宜探针确认可导入reference／budget_clock，不导入State／yaml／jsonschema／Temporal，原native依赖仍沿选定路径解析；r2明确复用这一已有接缝。这不是未来native gate／实际venv验收。同fresh reviewer固定r2设计复核已两轴approve／开放0／0，详见[独立计划报告](../delivery/2026-11-15-training-managed-execution-plan-review.md)。
