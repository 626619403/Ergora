# Q4.2c0.2b2：停止分支的实际监管接口草案

日期：2026-11-15。细化[b0](2026-11-15-training-cycle-gates.md)保留的共用接口设计门禁；源码基线仍为`07cbae2227d60c849df6ac96b4f96d3f71d80d43`。当前只做准备，不把草案当作已批准接口或实现。b1的实际调用若改变此处前提，实施前修订并复审。a片自己的CI仍待Windows终态；没有后继产品源码变更。

## 使用已有库，保留已有owner

调查确认原`_BudgetPhase`是同步live budget owner的非阻塞selector监管，不能给cycle伪造BudgetedStart。新的cycle进程本来就使用asyncio loop，因此其父侧使用stdlib `asyncio.create_subprocess_exec`和独立pipe tasks，不再抽出或复制一套selector transport。两种父侧有不同运行约束，无须强行继承同一个进程driver。

两个真正共享的部分是原`processes.run(supervised=True)`的唯一reaper，以及原budget的两帧身份协议。前者直接调用；后者可在现有`training_execution_protocol`内抽出内聚的`PhaseFrames(identity, output, result_limit)`：保留`receive(raw)`、frames、buffer和problem，负责两帧顺序、完整身份、普通process observation、有限UTF-8 JSON、分帧与容量。预算phase和cycle operation分别在`reference_training_budget`、`reference_training_worker`中消费它；没有第三个抽象registry。使用该stdlib owner已有严格`decode`，保留有限数、重复key拒绝和顶层对象要求，不新引入parser依赖。

原budget的`start/poll/request_stop/finish/supervise`、输出目录、原identity、payload、65,536B stopped／2 MiB result及成功条件保持。b2a只移动两帧codec并迁移原调用；不改变预算、进程取消、native业务或最终持久化语义。若复用实证表明codec抽取反而扩大调用义务，则保留同owner的局部结构并在审查中解释，不能为了行数强制抽取。

## cycle operation的实际接口

运行编排留在`reference_training_worker`，应用数据／目标判断留在`training_cycles`，原子记录与纯stdlib身份留在protocol。公共入口仍待c2；不让现有存储`stop_controller`变成live同步总stop。

父侧异步operation具有`start`、异步`run`和`request_stop`生命周期，使用每次独立生成的operation ID及完整身份；它不是另一个执行调度器。身份为协议`ergora-training-cycle-operation-v1`、operation ID、mode、control_home、project、cycle_id、input SHA、authorization SHA、可空ordinal及父进程PID／start_ticks／boot_id。mode仅为inspect、stop-writer、notify-owner、drain、observe-execution。只有冷启动inspect允许input SHA为null，且仍须完整原authorization SHA和父进程身份；其他mode都要求完整非空input SHA及经inspect验证的原clock／policy snapshot。父侧发完整有限JSON请求，S重核它仍属于原父进程；没有裸PID通知。

父loop只处理内存中已核身份、内核clock／PID身份采样、asyncio子进程和pipe；不读State、原业务文件、锁、目录或fsync，不执行同步`wait`。stdin写入、stdout分帧、stderr有限诊断与进程wait分别使用异步task，慢reader不能阻塞其他operation。创建过程被shield并保留实际spawn task和child handle；取消时仍等待原spawn task、取回已创建的handle，再向这个S请求停止并等待原H回收，不把取消future当作回收证明。

S和业务H均使用现有`reference_training_worker`的新明确入口，保持source key集合。S在任何child产生前安装TERM／INT处理和原父身份watchdog；非inspect模式还使用已验证snapshot的原clock watchdog。冷启动inspect改用下节一次固定的观察截止，不伪造尚未读取的原clock。随后调用唯一`processes.run(..., supervised=True, stop_requested=...)`启动一个H。**supervised run的timeout参数本身不负责截止**，两类截止及父取消必须实际进入`stop_requested`。S无需原业务registry／executor锁。H可以进行本地原件读取、fsync、pidfd通知及原链观察；这些阻塞只属于这个operation。S在原run返回、全部H后代已回收后才输出匹配stopped帧；之后仅直接读取现存结果／写最终帧，**不得再spawn**。

收到stopped前父侧只能请求TERM，等待原S回收；收到匹配stopped后，若S卡在结果读取／持久观察，父侧使用本operation的同一截止：冷inspect使用spawn前一次固定的bootstrap截止，其他已验证模式使用原total。相应截止已尽即可kill这个S并返回结果unknown；冷inspect不能等待一个尚未读取的原total。无匹配帧时不能把S退出码或父future取消当作已回收。与原budget相同，确实无法完成的OS回收保留unknown和实际延迟，不把超时当停止成功。stdout只消费完整帧；每个cycle result≤32 KiB，超限拒绝而非截断，完整日志留operation目录。原budget容量不缩减。

操作目录由各S在`<control>/operations/training-cycles/<operation-id>/`内创建，原请求、H stdout／stderr及S stderr分别保存；父loop不建目录。目录不可覆盖，不与原训练结果／controller事实混在一起。S的停止后直接存储也可能阻塞，因此先有stopped帧再做结果观察，沿原顺序，不新增reaper。

## 初始化与真正fan-out

总stop冷调用首先只有control_home、project、cycle_id和原authorization SHA，尚无已核input SHA／clock。其inspect-only观察timeout为1至60秒；**在首次spawn前只计算一次绝对BOOTTIME截止**，完整绑定原父boot身份并随请求传给S，启动／读取／取消／恢复不得重置。S将此截止与父退出／TERM一并放入`stop_requested`。该mode只允许只读inspect H，不得派发writer、通知、drain或训练；这是读取原身份的观察窗口，不能成为执行授权或新训练预算。

inspect H核完整原authorization SHA、cycle raw SHA和policy，使用原`budget_clock`验证clock及剩余时间，返回≤32 KiB的完整原authorization／policy、input SHA、有序候选轻量索引和本次BOOTTIME／UTC观察。读盘耗时自然消耗原clock；结果超限／部分、超时或父取消都保留unknown，不从未经完整验证的部分结果启动effectful分支。原immutable输入不可读时，不承诺通知未能识别的目标。

父侧取得完整snapshot后，仍复用原`budget_clock.remaining`的BOOTTIME与UTC保守算法及boot／负elapsed／大于5秒漂移的拒绝；不只从缓存的正remaining减monotonic时间。该原owner的内核clock采样允许在loop中使用，业务存储仍只在H。各effectful S收到同一完整原snapshot，继续用原clock watchdog；每个H在任何效果前重核真实原文件与snapshot。bootstrap窗口不得改变原authorized_at／deadline／boot／ticks，返回后所有分支按实际剩余total计算，不续期；已尽或clock discontinuity不启动新分支，并请求收尾已启动的operation。未来c1已有已核snapshot时仍须绑定原身份，不能接收未经核验的任意候选列表。

取得原身份后，在同一父loop中并发启动以下独立S／H：一个stop-writer、每个原selected ordinal一个notify-owner、一个drain。writer调用原可见优先停止存储用例；drain在原total窗口中只重试父排他许可／同原件同步，不能获取submission／registry／executor锁。任一writer fsync、某目标intent或owner读取、结果观察阻塞均不阻止其他已识别目标的独立通知。原clock已尽时不再启动新分支，如实返回未确认项并收尾已启动的operation。

每个notify-owner H独立重读完整原cycle、该ordinal、原start intent和owner，核完整controller binding及原intent／authorization SHA；只向匹配原PID／start_ticks／boot_id的活owner调用原`processes.notify_identity(SIGTERM)`。不依赖当前源码hash、当前project revision或当前SDK可用性来清理旧owner；不因新软件拒绝执行而放弃原精确通知。缺失／部分／不同controller的owner不可猜测或接管。H不发送全体Temporal cancel，不调用新的native start；原owner继续拥有completion优先、fence／cleanup和实际reap算法。

通知完成与原链停止观察分离；后者在独立observe-execution H中复用原c2 reader，只读原request／launch／attempt／ack／stopped链并同步同原件。不会让一个慢观察阻止通知其他owner。已退出且没有stopped链保持unconfirmed，不补造链；此前已接受的测量轮保留人工release窗口。最终响应列出每个operation的实际结果／unknown、父stop可见／持久、父许可drained及每个原执行链的executor stop，不推导合成成功。

## 验收与交付顺序

1. 先对本草案、实际原源码及b0合同作新的独立两轴设计审查；当前不写产品测试。b1完成后重核接口前提。
2. b2a仅作共用codec的行为保持整理，沿原budget真实大型stdin、停子树／TERM、坏／缺帧、最终同步阻塞和capacity接缝验收；保留原两帧身份、结果形状及failure semantics。该片不得顺带开放父停止。
3. b2b实现独立cycle operation和fan-out。实际两个原owner，其中writer fsync和一份目标业务读取分别阻塞，另一个owner仍收到精确通知；检查原reap和各operation全部收尾。另验冷inspect已发stopped而S卡在结果文件读取时，父侧仍按同一bootstrap截止结束／unknown并收尾S，不依赖尚无的原clock。并验callback前后停止、原clock已尽、父取消、错误controller／PID、无SDK／来源漂移旧owner清理及前轮release保留。只用原接缝的必要检查，不复制原预算全矩阵。
4. 每片新的非editable安装、283保持、自身原结构模板及新的fresh-context产品审查，再普通发布与自己的CI；不借b0设计或a片通过。c1总Workflow／独立worker／stop queue、c2公共交互和真实两轮验收仍是后继责任。

## 设计R1接续

新的独立初审指出冷inspect还没有原clock，而r1笼统要求每个S使用原clock watchdog，属于可达的bootstrap截止缺口；需求request-changes，维护性approve。r2明确inspect-only固定观察截止、null input SHA范围、实际`stop_requested`、spawn取消回收及完整snapshot后的原clock算法；同reviewer续核又指出post-stopped冷结果读取仍不能等未知原total。r3将父侧最终kill／finish截止按mode明确为同一bootstrap截止或原total，并补该可达窗口验收；未改产品，待同reviewer复审，不把设计修订当作产品通过。

原fresh reviewer现已对固定r3（10,699B，SHA256 `d8d049eb6b281c591e0f3716563adbffd2c87fa14f315a2b54851ef14f7d3692`）给最终设计需求／维护性两轴approve，开放0／0，R1仅设计层关闭。[审查报告](../delivery/2026-11-15-training-cycle-stop-supervision-plan-review.md)保留10,775B初审前缀，最终14,014B／SHA256 `62b448bd52b4bd82ab457d81eecf0cac37d2fb9935ee376ee4512c329b8a2ea7`。尚无b2产品；b1实施后仍核接口前提，产品验收不继承设计通过。
