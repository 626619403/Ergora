# B3.3c 真实执行与停止：逐步交付

日期：2026-11-15。固定[设计r2](../plans/2026-11-15-training-managed-execution.md)已获新fresh-context计划两轴approve／开放0／0，R1仅设计关闭；c1本地r2两安装身份、24控制回归、16架构、真实Temporal控制旅程及自身原模板已通过，新fresh-context产品最终本地两轴approve／开放0／0，已普通发布`75285e3271bb93271eaea050ca7812cb0cd98b5a`，自己的CI及原独立固定发布续核待；c2未实施。实际实施基线为B3.3b普通发布的`6c7e9d924f822e60a54ce8c0686a56758ae0359a`，它自己的CI及独立终核现已闭合。kernel专家保留在v3优化路径。下列分段保留当时状态。

本次只读复核原BudgetedStart／phase supervisor、processes回收、原submission／run历史、取消、native request／executor和解释器／依赖路径。计划将完整工作拆为c1非阻塞phase生命周期与c2显式单job受管执行，各自验收与独立审查。新增launch预留在执行S出生前消耗一次许可，避免hook前强杀后因缺attempt而重跑；原start slot、clock和实验账本保持原owner。

下一步固定c0原要求、候选文档与实际源码身份，交新的fresh-context计划评审者。当前不把草案中的命令、schema2能力、launch／attempt／ack／stopped或并行执行记为产品接口。B3.3b产品及原283没有因这两份草案而改变。

## c0 r1生命周期问题与r2修正

固定23份design-scope-r1的SHA256为`dadb2647c00f81651c5d97cd2c973cbe8af25d5c05e8b76f590e929e6938bc8b`。新fresh-context评审者独立复现r1的顺序冲突：先由原processes.run回收业务、发stopped，再在同S新起publisher，父据已stopped于total杀S后publisher仍活着；探针已精确SIGKILL／waitpid收尾。作者接受，r2明确S在stopped后仅直接做记录读取／写入／同步及结果观察，不再生成任何子进程；发布卡住时父只终止无子进程的S，持久证明unknown。

r2同时明确复用原reference.worker_command的包自身bootstrap，避免另一套环境加载；评审者Python -S探针只确认现有validator／clock及native依赖解析的导入边界，不认证未来gate或真实native依赖。原r1完整候选／probe-results.json保持，当前未修改产品、运行训练或授执行权；待同reviewer正式报告及固定r2复核。

## c0通过、c1开始本地实施

新的[独立计划报告](2026-11-15-training-managed-execution-plan-review.md)已对固定r2两轴approve／开放0／0，R1仅在设计层关闭。c1沿原`_BudgetPhase`拆start／非阻塞poll／request_stop／finish，原run调用同一生命周期；父侧用出生前已核budget.folder与固定相对路径纯拼接，真实safe_file／mkdir／stderr.open留对应S。原owner仍只运行原四种控制phase，不新增执行能力或runner。

原phase-isolation fixture去掉ThreadPoolExecutor，改同一父进程真实交错监管两S；peer进入受控fsync阻塞，monitor仍须回收真实setsid后代，父不启subreaper。收尾先向全部peer请求停止并继续轮询全部，已终止后才finish。父侧业务路径查验用可达失败接缝保护，不以只看函数文字认证非阻塞。原大帧、持有reader、异常S、取消、fence与final阻塞及原合同回归仍待实际运行；当前没有验收通过主张。

## c1源码首项与r1／r2安装身份

原phase-isolation源码精准回归1 passed／68 deselected／31.05秒，外层32.055秒；同一父进程实际轮询两S、peer确实触达受控fsync、monitor回收真实setsid后代、peer此时仍存活，父subreaper为0，最后两S／helper及后代均被原断言检查停止。源码r1冻结三文件清单SHA256为`1435f5b301d09febc5717c5d55cae0ef1cb953a9fd458af28901a7c860055604`。

r1两安装650逐字／283及依赖检查通过，wheel为`414a8ccf150f263159a99da02967bf3f73684e872b25bf1fa3ee65dc4359ecb0`；未用它跑最终完整矩阵。自查后r2只补尚未发送payload的selector初始化失败收尾，以及将已有有界startup stderr纳入unknown原因；原peer测试字节不改。r2三文件scope为`b7869bd8ac5baa22968bc00d830571fdcbef5af849676c3f986e46bbb29efdf0`，新安装进行中。第一次r2构建脚本误指不存在的前置venv，尚未启动构建即FileNotFoundError；原空输出及失败单列，修为已完成的c1 r1 SDK解释器后再构建，不改产品迎合脚本。

实际安装输入只冻结174份tracked tests/examples，未复制node_modules／构建产物。接着验原24项控制接缝、完整架构边界、真实Temporal控制CLI旅程和原自身结构模板，再交新的fresh-context产品审查；此前源码1项及r1身份不转授最终r2全部行为。无c2执行权限／runner／训练／GPU／收益主张。

## c1 r2安装与实际控制旅程

r2非editable core／SDK各650份源码／wheel／site-packages逐字、283参考和依赖检查通过；唯一产品变化为原reference_training_budget，未增加模块。wheel SHA256为`e66e1e5a73fc5bea6a2c4fc08a5cf349d26a88c7c7d0221531e6af9ed7a7cbb0`，core无Temporal，SDK为1.34.0。安装完整架构边界16 passed／0.44秒，外层1.217秒。174份实际测试输入保持，最终原24项控制回归及自身原模板仍在运行。

同一r2真实本地Temporal／budget worker的实际CLI控制旅程54.635秒通过：原submitted run、queued native request、共同预算下自动fence／原取消、只读回查和同slot resume，原授权／request／attempt字节保持，第二候选未启动。Supervisor、worker、owner／phase和两端口均已按脚本收尾；没有启动executor或业务训练。它是改变phase监管后的控制集成验收，不能替代c2的runner／全后代持久stop或真实训练／GPU验收。架构文档已同步新低层生命周期和仍串行的原owner边界。

## c1原自身结构模板通过、独立产品评审进行中

同一r2安装使用原`ergora-structure-review@1.0.0`及用户已授权Codex回退，实际54.264秒两轴approve／开放0／0，外层56.786秒。19份全文268198B与三份祖先资源完整进入实际stdin，原结果SHA256为`487188320a1c127267eed032429696a909d65e99e910372cdfefa13ca3a22604`；仅审供应的完整源码文本，不认证私有包／运行或CI。未声称异后端。

新的fresh-context产品reviewer已独立接收固定10份候选及原要求／c0r2合同、现有安装／架构／真实控制原件。候选scope为`5657f03c5a1225149863d55ee75ccd9cf43875a6cce09978e8db1354c049d4c9`；产品／测试继续等于source-scope-r2，完整原24项安装回归尚未结束，最终本地结论不预记通过。前置b自己的CI43674493548及原独立终核继续分别等待。

## c1 r2控制回归完成

原最终安装控制回归已结束：24 passed／80 deselected／495.27秒，外层496.327秒，exit0。输入为冻结174份tracked tests/examples中的原training_submission、reference及services三suite，沿原24项选择，覆盖phase peer隔离、短写／大结果、异常S、父死亡、safe-reap、fence／final发布故障、原start slot及来源边界。完整命令、stdout、stderr及JUnit均保留，不把选择子集称全库回归；同r2完整架构16项另计。

关键私有原件位于`.ergora/checks/training-phase-lifecycle/`，公开文档仅登记相对路径和SHA256，不要求读者有本机缓存：

|原件|SHA256|
|---|---|
|`source-scope-r2/scope.json`（三产品／测试）|`b7869bd8ac5baa22968bc00d830571fdcbef5af849676c3f986e46bbb29efdf0`|
|`installed-tests-r1-scope/scope.json`（174输入）|`df5957fae258427ccddf076a5983e2501dbae695194e4f8071055f713afdb42a`|
|`installed-regression-r2.json`|`60d28e096c4a96859c38158cbf8097c1d843e048f9d9793f6f3a911f80e721f4`|
|`architecture-r2.json`|`b0c701bcf068abf391f2e171f0483d9e154eb959159c9f325ae5b8589d27f9e5`|
|`native-journey-r2.json`|`d9f5f6afd8f0f8ef0f371af35f0b678a516b90f5c85430bce5f86dbf1b1c37ce`|
|`self-review-r2-codex.json`|`fc0fd9c76ef1440e985cba4a82ab6945ae0998203dacff701bf278b5956be2d6`|

原fresh-context产品reviewer已获完整回归原件继续终核，最终两轴结论与精确发布仍待。c1只提供原phase生命周期，原BudgetedStart生产四mode仍串行；没有c2出生能力、execute命令、launch／attempt／ack／durable stopped或自动循环。前置b自己的Windows CI及原独立发布终核未闭合前不推送本片；未改v3 kernel路径。

## c1独立最终本地审查通过

新的fresh-context[产品报告](2026-11-15-training-phase-lifecycle-review.md)对固定r2需求／结构两轴approve，开放0／0。评审者沿真实调用链核父侧无业务metadata I/O、四mode仍串行、stopped后无spawn及原唯一reaper，另独立便宜探针核769次实际短写、大帧、90k stderr排空并仅留64KiB、selector／Popen启动故障收尾。它逐字核两650安装、283参考、174测试输入，直接读取24项完整原件、架构、实际九CLI／同run原件与全部已知PID／socket收尾，以及自身19全文／三祖先资源实际stdin和原result，未发现可证实产品finding。

作者最终三份进度文档也已由同reviewer完整补核，`product-audit/final-docs.json` SHA256为`47699f0abb08a794e2dd9f71f2d295fae07ddc7048bb512c6ec610f33901eb8f`。此后只追加审查／发布状态。前置b自己的CI与原独立终核、本片精确stage／普通发布和自己的CI仍分别待闭合；不以本地通过代替它们。

## 前置b闭合，准备c1精确发布

前置固定6c7自己的CI43674493548／attempt1八job／30必要步骤全部success，原产品reviewer固定发布与CI终核两轴approve／开放0／0，原[终核报告](2026-11-15-training-executor-protocol-review.md)已追加。本片产品／测试继续等于已审r2，只追加这些门禁状态及原报告；现做完整staged范围／AST／Git tree链接和摘要核对。未将后继c2笔记或产品混入，也不提前认证c1自己的发布／CI。

## c1普通发布、自己的CI与原独立续核待

已普通发布`75285e3271bb93271eaea050ca7812cb0cd98b5a`，parent6c7，tree`1537f559fa36923ab0fdf5d328b10b3f3a753f38`。原新fresh-context reviewer固定staged r1的12blob／3AST／223个Git tree链接及完整cached diff-check通过；r2只纳入其报告的最后审查字节，其余11blob保持，三产品／测试仍等于已审r2，data／scripts／CI／attributes无变化。最终`publication-staged-r2.json` SHA256为`5ec87e01bcc4a5666a3a0b4e661d47ed587da56fc4ee021933a0c9793a1a9cc7`。

实际commit exit0／0.072秒、当时工作树clean，普通push exit0／5.775秒，完整SSH Ref同一。命令与原stdout／stderr保存在同片私有publication原件。原产品reviewer接续固定发布、原来源和自己的Portability终态；该门禁当前未闭合，不把前置6c7的CI成功转授75285e3。

等待期间仅细化[c2具体记录与接线合同](../plans/2026-11-15-training-execution-records.md)，没有改c2产品。新fresh-context设计reviewer获固定22份原要求／文档／实际源码，scope SHA256为`bb2d9abdb7bb1391ba8bb017df6891f50d3e9f5948ad872241e75ac7ac8de751`。具体schema、原生解释器与并行监管顺序须先审；c1自己的CI及终核闭合后才实施c2。

## c2原生环境准备，非执行验收

c1自己的Portability已定位为[43676697981／attempt1／#232](https://github.com/626619403/Ergora/actions/runs/43676697981)，由原产品reviewer固定75285e3续核，当前在途。等待期间通过已验c1 core CLI在home持久新目录准备b协议来源（1.921秒），使用系统Python3.12新建独立native venv（0.044秒），按原`requirements.lock`全哈希sync（25.638秒），三步exit0；未改原来源或既有日常环境。原lock SHA256为`2536ae14cd85db33d1ea93f0b97da67b28efd4e7bfc2f3423087b6c61599495c`。

独立native解释器实际导入原executor、MLflow3.17.2和Temporal1.34.0（10.163秒），核127个原依赖分发、sys.prefix／core.ROOT／core.PYTHON与所选native venv一致，应用Ergora包未安装／不在其普通搜索路径，`uv pip check`通过。私有`native-environment-r1/evidence.json`登记原命令／输出摘要；这只证明原生环境和导入，不证明新gate、MLflow服务、执行／停止或训练。没有启动服务、调用process、runner或业务训练；后续仍须同一native解释器实际全周期验收。

随后仅在新config／state目录初始化原native设置，沿用户已接受的当前Docker／当前用户边界绑定信任，普通自动executor仍disabled；复用持久home里的Temporal1.9.1（Server1.32.0）二进制，未启动服务。追加私有`native-environment-r1/evidence-r2.json` SHA256为`f135c914efc6271d3c09b6581c4b731382b3b73529d2f0d4d71a9617f608094f`，保留此前evidence原件。

新的本地CPU验收repo／baseline／runner及两个实验准备通过（12.021秒），原Git创建两个完整commit，候选只改注释，训练算法／模型／数据不在此验收。runner文件和源码AST有效；后续实际运行将产生相同CPU计算结果、真实新session后代及故意缺少可信attestation的evidence，让原archive拒绝而不是伪造质量／性能PASS，再经过原track。当前仅准备元数据，已核没有cycle授权、start、native job或服务；`native-environment-r1/prepare-acceptance.json`保存实际命令与输出摘要，runner尚未运行。两个实验不视为真实B3或收益证据。

## c2具体合同r1发现问题，r2复核进行中

新的[具体合同独立报告](2026-11-15-training-execution-records-plan-review.md)对固定r1需求／结构均request-changes：R1通用调用会在离线reader前校验所选native来源；R2缺完整cached context、原policy／cleanup与critical源码反算；R3完整stopped可在link后、目录同步前可见，不能仅凭SHA称持久。评审者三项便宜原函数探针保留；这些是设计缺口，不冒称已实施c2漏洞。

全部接受，[具体合同r2](../plans/2026-11-15-training-execution-records.md)改用随包固定只读入口，明确完整context／原auth／原cycle与policy／ready、clock及actual critical来源，新增admission／execute使用compute；离线停止证明须对同一现存链同步／重读才能durable确认，失败仍unknown且不补文件或返执行权。两份计划r2固定scope SHA256为`7c259c4609eddbd97729dc05bad93f65d2bbf6e0b180d22ad2a6ad1104d67ec5`，原另20来源不变；已交同reviewer复核。c1自己的CI／原终核继续在途，c2仍未实施。

## c2具体合同r2设计通过

同一fresh-context计划reviewer已对固定r2需求／结构两轴approve，开放0／0，R1–R3仅设计层面关闭；[原独立报告](2026-11-15-training-execution-records-plan-review.md)完整保留r1及修订证据，最终SHA256为`096bea3cf72bfd45d586f0e7b40f78b3b347eaf8875223052f5dd58397206869`。独立便宜验证仅确认既有随包`-S` reader在所选native不存在时可读，以及只读fd／目录同步不改bytes，不能替代c2产品的完整gate／launch／reap／持久stop／安装验收。

恢复已核HEAD／远端分支与计划；c1自己的#232仍只有Windows在途，其余七job已成功，原产品reviewer继续直接跟踪终态。本片继续读实际owner／调用链并准备接线，未在前置门禁闭合前修改c2产品。kernel专家继续留在v3路径。

## 原生MLflow服务准备验收

等待前置门禁期间，沿已验c1安装的原`services.control`启动已准备native环境中的真实MLflow3.17.2，仅选择`mlflow`，未启动训练worker／executor或提交实验。完整旅程32.388秒／exit0，真实`/health`与原experiment search接口均HTTP200；随后原Supervisor shutdown为confirmed，socket消失、捕获的八个服务／后代身份均不再运行、5000端口可重新绑定。启动前也核过该端口空闲，没有接管既有服务。

私有`native-environment-r1/mlflow-service-observations.json` SHA256为`2e4d8e1ba18d6fd5ab7a99e4a735ff4b141e589774dd9b119b3bceabeaa11d52`，完整命令／脚本／stdout／stderr另存。此项只确认真实服务可用与收尾，尚未调用原`track`、runner、archive或新gate；不把它记为c2或训练结果验收。c1自己的Windows CI及独立终核仍待。

## c1精确门禁闭合，c2产品实施开始

原fresh-context产品reviewer已完成固定75285e3及自己的CI43676697981／attempt1终核：八job／30必要步骤全部success，REST／HTML／Actions与完整SHA一致；12远端文件、两650安装／174输入／283参考保持，需求／结构两轴approve／开放0／0。原报告最终SHA256为`272d6fac2e6010acff99a844bab1cf9b303c69347af58dfce368e1dabe1be182`，私有`training-phase-lifecycle/product-audit/ci-publication-r1/final-ci-audit-r1.json`为`f2ca44020d08a2ac4f5cc3fa5fd0103f22b91033119641339d200b30f1a475bb`；作者已直接复核两原件摘要。

现沿已审具体合同r2开始c2，先实现共享stdlib记录／离线入口，再接出生能力、显式请求及原phase并行监管／native最后gate；原kernel路径、原记录与原生算法保持。安装、完整生命周期验收、自身模板与新的独立产品审查、普通发布和自己的CI均另行记录，不提前计成功。后台只读测试价值审查同步进行，未授权其删除现有恢复／回收检查。

## c2首轮接线与快速静态检查

共享stdlib协议、随包离线reader、显式execute／execution CLI、schema2出生能力及原phase并行监管已写入首轮源码；原process身份归既有processes供预算与native共同使用，原memo常量归既有runtime供原submission与执行helper复用。native最后callback仍在原executor锁内，S在真实reap及匹配帧后直接发布stop，不再spawn。取消增加精确pidfd本地通知，远端signal仍归原owner。当前未认证这些新行为，需回归和实际全周期验收；原283未改。

首轮源码AST与完整架构16项通过／0.38秒，仅证明解析和依赖声明。小范围既有接口回归与首轮非editable两安装准备在途，不能转授最终c2。另新只读[测试价值报告](2026-11-15-training-test-value-review.md)未证实可删除的整项恢复／回收测试或重复CI，建议后继单片提前Windows skip及删一条完整reason文字约束；本片保持这些原检查。

## c2 r1真实生命周期失败与修正

首包core／SDK各652份源码／wheel／site逐字、283参考及依赖检查通过。原四接口源码回归4 passed／91 deselected／43.92秒。首轮真实CLI／Temporal＋native CPU旅程62.816秒后失败：实际原Git镜像／两worktree、runner两臂同值、新session后代、原archive负gate和真实MLflow track均已发生，完整stop原件可读；但monitor启动时活owner观察发生初始化锁读者竞争，未在脚本40秒观察窗内出final。随后私有cleanup还因uv Python缺少os.pidfd_open封装中断；原失败／trace／实验与budget均保留，不记全旅程通过。作者用系统Python对本次精确O发pidfd TERM并原shutdown，原final随后完成、O不再运行、socket和5000／7233／8233端口释放，见私有native-journey-r1-recovery.json。

实证修正将初始化观察者改用共享锁，出生写者仍独占；同一旧r1安装／源码探针对已有共享观察者分别返回active=false／true，命令和输出固定在owner-lock-red-green-r2.json。processes增加真实libc pidfd调用以兼容没有Python封装的构建，仍重核boot／PID／start_ticks并绑定pidfd，不退回宽泛信号；两实际子进程通知回归2通过／0.05秒。离线完整链／无安装／原件与DB保持、同可见stop同步失败再观察、五种身份／FIFO故障、初始化读者并发共8源码回归通过／7.46秒。

r2新包及新CPU实验正在准备，原spent intent／slot／authorization不回收或改写。新的fresh-context产品reviewer已接固定19件中途源码与原要求，当前只做逻辑审查，最终验收与结论仍待。

## c2停止顺序和结果收集修正

r2两份非editable安装各652份逐字／283参考／依赖检查通过，仍不是完整生命周期验收。独立reviewer的便宜探针确认execute在compute结束后会丢弃cleanup内收到的完整停止结果；同时发现stop_work仅置flag、可能在fence的Popen等待前尚未实际送TERM。已接受并修正：execute只在结果收集使用原total期限，启动和业务停止仍按compute；先对所有工作phase置停止标记并非阻塞poll送出TERM，再启动fence。没有延长授权、增加launch或替换原reaper。

两个最小接缝回归源码2 passed／77 deselected／1.54秒：真实父管道／TERM验证cleanup内接收停止结果且不能再启动execute／admission；原drive的可控phase验证取消通知顺序。它们不声称原native训练或durable stop通过。r3两安装正在重新核验；其私有构建脚本首次因机械替换错误引用不存在的构建解释器，在构建前失败，已保存setup输入／错误原因，修正后重新执行。产品没有因该私有脚本错误发生改变。

新真实CPU旅程将使用独立实验及原预算，不覆盖r1。私有收尾改为逐项记录错误，并独立保证服务shutdown与已知精确PID／端口核对，避免一个通知错误跳过其余收尾；此驱动修正尚待实际运行。

## c2 r3安装及r2真实CPU旅程通过

修正后r3 core／SDK各652份源码／wheel／site逐字、283参考与依赖检查通过。新的两个独立CPU实验准备7.024秒／exit0；其中`cpu-negative-gate-r2`使用新的原授权与slot，经r3实际CLI完整旅程25.928秒／exit0，八条命令全部成功。原Temporal、新schema2 owner、显式request、launch、native锁内attempt／ack、原Git mirror／两个worktree、Sandbox runner、archive与真实MLflow track及直接stop持久发布实际发生。baseline／candidate CPU结果均690880；原质量gate因缺可信attestation而正确为false，不伪称训练／收益成功。

原final为completed，admission／execute／monitor三项原phase均完整回收，`executor_stop_confirmed=true`；新core离线读取同一原链也确认durable stop，`execution_success=null`。已捕获的新session后代不再运行，所有已知owner／phase／业务PID已停，原services shutdown完成、三端口可重新绑定，cleanup错误为空。私有`native-journey-r2.json`、home原`result.json`／八次stdout/stderr／完整原业务文件与`cleanup-confirmed.json`保留；r1失败及其恢复未覆盖。下一项为registry阻塞下的真实取消／独立reap，其余故障窗口、自身模板和最终独立产品审查仍待。

## c2原registry阻塞下的真实取消通过

新独立held runner／实验准备4.722秒，r3安装实际CLI／Temporal旅程21.282秒通过。runner先做与前例相同CPU计算、产生真实新session child，然后保持存活；原job生成后由验收者持有原registry.lock，显式execute与原cancel均实际调用。锁尚未释放时，同job完整stop已持久，native执行器及child的精确身份均不再存活，原fence phase已启动且等待，原native result和budget final均不存在。释放原锁后，原final为fenced，五phase皆已回收，execution保存原cancelled／returncode -9与`executor_stop_confirmed=true`，控制cancel单独保存，不伪造训练结果。

原request／intent／start attempt字节保持；已知owner／phase／业务PID全部停止、原服务shutdown与三端口释放、cleanup错误为空。原件在私有`native-cancel-r3.json`和home同名完整旅程／held-registry-observation／result／cleanup文件。该项证明registry等待不妨碍已有执行子树回收，不扩张到内核不可中断I/O或真实GPU。中断窗口回归与最终审查仍开放。

## c2继续回归和文档

沿原submission／budget进程fixture增加单次launch接缝，真实派生来源／空native venv只作准入、不执行native训练；固定SDK服务替身核完整run/history/memo和QUEUED。显式请求丢回复、launch后不启动S、相同确认再观察均保持同一launch，普通start／resume／execution不产生请求，四种控制身份／阶段及三种显式确认冲突拒绝；源码1 passed／79 deselected／30.58秒。初始三个fixture设置错误（缺导入、尝试改不可变登记、向已存在目录prepare）原XML分别保留，修fixture后才通过，不记产品故障或抹去原失败。

同一原控制回归扩展schema1和新schema2／null两个owner：均保留原创建／控制／单slot，但显式execute拒绝且不创建managed目录，源码2 passed／79 deselected／46.17秒。最终受影响八suite在r3非editable安装上运行，使用另存r4测试输入；尚未记录结果。新用户手册／架构／组件协议已按实际显式执行、同链持久观察、source独立限时和旧owner范围更新，链接及自身模板审查待。

固定r3中途产品复核已关闭R1／R2，需求／结构的整片最终结论仍待；原[独立报告](2026-11-15-training-managed-execution-review.md)完整保留检查范围。故障注入私有驱动r4未递归穿过原submission子进程，所以预设native断点没有发生，首例实际正常CPU执行，驱动44.259秒后失败；原实验、final、MLflow及cleanup保留，所有已知PID／三端口已收尾。已用独立新实验修正递归注入入口，r5正在实际执行；不将r4正常CPU误记为中断验收。

## c2六项真实故障窗口与自身模板新发现

r3安装的r5故障旅程111.120秒／37条CLI／六个独立原授权通过：hook前退出、attempt同步后退出、ack同步后退出、launch内存回复丢失、native result先于实际reap、stopped已link而其目录同步卡住。前三项确实到达native进程中的指定断点；分别保留无attempt、仅attempt、完整ack及回收后的stop，没有业务started／result，前两项停止证明仍null。丢grant无S也不返launch；每项相同request的再确认保留原launch。

result-before-reap在S原reaper前保持真实child存活，result已存在时原final／managed stop尚未完成；释放后由原reaper收尾。stop同步阻塞在完整原件已可见的实际S内发生；独立reader注入同存储同步失败时保留reap观察／durable unknown，原total后S终止且没有final，未来正常core reader同步并重读同一bytes才确认durable。这里的reader失败是明确故障注入，不冒称普通读取必然失败。六项全部已知PID／服务／三端口收尾，原件保留在native-fault-r5及home同名目录。

Ergora自身原`ergora-structure-review@1.0.0`的Codex实际调用88.522秒，30份完整文件727,803B及三份祖先资源均在真实stdin，需求request-changes／结构approve。首个私有setup因错误推导旧inference配置路径，在模型调用前失败，输入和原因保留；成功调用另存self-review-r4-codex原result。新R3为可见request的writer仍持execution.lock时唯一admission提前退出；新R4为monitor非completed被移除而不立即停止／fence。两项已接受。

旧r3安装配固定新fixture实红2 failed／1 passed／31.25秒：真实writer锁争用释放后不再launch；monitor失败仅到deadline才停止。产品在原admission helper内按同compute等待锁并重核，原drive共用局部stop_and_fence处理取消／期限与monitor失败，保持原phase记录。修后源码3 passed／80 deselected／21.24秒。r5新core／SDK各652三方逐字／283／依赖通过；当前以新的独立原授权复验正常CPU、持锁取消、六故障及活runner项目revision漂移，旧r3通过不转授新产品。最终安装回归、重新自身审查和原独立终核仍待。

## c2最终候选的验收接续

最终r5 core／SDK仍各652份source／wheel／site逐字相同，283参考及依赖检查通过。新原授权的真实CPU旅程r7为26.195秒／八CLI，原native Git、两臂CPU runner、archive负gate、真实MLflow与持久停止完整通过；registry锁阻塞下的新取消r7为21.641秒，原锁释放前已实际回收并持久stop，控制fence仍等待。两项全体已知进程／服务及三端口收尾通过；它们只认证CPU生命周期。

r7故障驱动虽然外层用r5解释器，内CLI误留r3路径；前三断点完成，第四lost-grant等待launch失败，87.684秒退出1。原件和已知进程／三端口完整收尾保留，整项不作为最终r5故障验收。已在新实验中修正r8内部CLI与递归注入路径，并明确逐条核安装身份，之后才运行项目revision漂移。最终r5安装八suite仍在途。此前r3安装配r4冻结测试的八suite现186 passed／5 skipped／1001.87秒，仅归旧候选，不转授r5或其新回归。

README、训练手册和架构均已补同预算显式执行与离线停止交接；当前状态表已区分设计批准、产品实现和待完成验收，kernel专家保留在v3优化路径。自身复审、最终独立审查及普通发布／自己的CI仍未完成。

## c2新候选六故障与真实项目漂移通过

r8故障驱动的内外CLI均使用最终r5安装，37条CLI／六新授权／110.691秒全部通过。hook前、attempt后、ack后、lost-grant、result先于reap及stop目录同步阻塞均到达实际注入点；单次launch不返还，前两断点无stop，result窗口在原reaper释放前无完成，stop同步失败后只用同原件恢复持久观察。新最终候选的所有已知PID／原服务及三端口收尾通过；旧r3证据和r7误装失败保持原身份。

随后r5活runner项目revision漂移旅程r7为20.294秒通过。runner和新session child实际运行、原registry.lock仍被验收者持有时，只改变控制项目revision，不发送本地取消通知。monitor产生非completed后，原drive立即停止执行并启动等待中的fence；20秒内、原锁释放前同job已持久stop、真实executor与child身份消失，native result／budget final均未出现。释放锁后原final仍保存executor_stop_confirmed=true，原request／intent／start attempt字节保持。全体已知进程／服务／三端口收尾通过，直接覆盖R4原活执行风险；最终独立关闭待。

接续四个只在私有验收中进行的native payload／file-read漂移反例：完整C.policy、原authorization.clock、gate source及native request完整bytes。保留原授权／源码／request物理字节，通过实际native gate／原executor.lock检查拒绝，不把受控读取注入称真实磁盘漂移；该项与上述真实项目revision漂移分别记录。最终安装八suite、自身复审及独立终核仍待。

## c2原锁内四项受控漂移拒绝通过

新r9的四个独立原授权、26条实际CLI／60.349秒通过：native payload中的C.policy变化、读取原authorization时clock变化、读取固定gate source时bytes变化、以及完整native request只增加换行。前者确实被完整cached C SHA拒绝，后三项分别被原授权完整身份、gate source SHA和native request完整bytes SHA拒绝。每项均在真实native解释器、原executor.lock独占期间进入原gate，原attempt／ack／stopped与业务started／result都未产生，已有launch不返还。

注入只改变指定payload或native读取返回值，原授权／request物理bytes在前后保持，安装包和native来源未改；它认证实际gate在所给受控漂移下拒绝，不冒称真实磁盘损坏。全体已知PID／服务／三端口已收尾，所有四例原始stderr、lock held／读入前后SHA及观察保留。项目revision漂移的真实写入验收另列于上一节。最终安装回归、自身复审、独立终核仍待。

## c2自身复审新增R5与原安装实红

自身原结构模板修后r5的Codex实际调用102.987秒，31份完整文件794,086B与三祖先资源进入实际stdin；需求request-changes／结构approve，原result与失败结论保留。R3／R4修正形状获认可；新增R5为execute的S创建失败后原drive异常退出，只在finally收monitor，未进入原fence／cleanup／final。新独立评审者用精确r5 drive接缝另行确认，接受该finding。

沿原fixture在真实detached owner的execute阶段对原Popen注入OSError，旧r5安装实红1 failed／83 deselected／23.88秒：已消费launch、未启动native、原run仍无budget final，不能靠禁止重发来替代清理义务。当前最小修正只在协调start接缝返回是否启动、记录原phase unknown并及时转原stop／fence／cleanup；fence本身起不来仍保留unknown，cleanup起不来保留control unknown，不另造时钟／重试／信号路径。源码、最终新安装和真实故障复验待完成；之前r5生命周期通过仍归其原候选。

## c2启动故障修正与新安装

R5修后源码精准回归3 passed／81 deselected／22.12秒，含实际detached owner／原Popen失败及原两个停止顺序接缝。最初一条标为source的命令未显式选择源码路径，实际上仍调用旧r5安装，原1 failed／2 passed／23.77秒另存；随后显式源码路径运行才记源码通过。False-start同样进入原fence，已有no-launch测试按实际清理合同改为等待fenced final后拒绝相同确认，仍核同一launch bytes。

新r6 core／SDK各652份source／wheel／site逐字相同，原283与依赖均通过，wheel SHA为`f1106d11b7c6b074b5f35c5a3d96208267735536cbdd549a6dbbb577f6c93a44`。只变更原Execution协调接缝与相关fixture／回归，不改原phase回收。最终安装受影响生命周期选择、原process／架构边界、自身原模板及实际Temporal全旅程正在核；真实故障旅程新增execute S的原Popen失败，要求无attempt／ack／业务result而原fence／cancel／final完成。前一r5安装的完整八suite现188 passed／5 skipped／1022.15秒，单独保持候选身份，不写成r6全套通过。

## c2最终候选自身复审通过

r6自身原`ergora-structure-review@1.0.0`真实Codex调用65.888秒，31份完整文件800,054B与三份祖先资源完整进入实际stdin；原result SHA为`0c5de8137fc994603aad0cb6fbfdeaba6fbb99055dfa513077cb007bfe231b05`。需求／结构两轴approve；明确认可R5启动失败保留unknown、实际停止peer后进入原fence／cleanup，原launch不返还，以及R3／R4和先前R1／R2的修正。该模型只审给定完整文本，不替代独立原件认证或运行验收。

最终r6安装的完整processes／architecture两suite为24 passed／4平台跳过／12.66秒。新独立原授权的正常CPU旅程26.764秒、原registry持锁取消21.694秒均通过；内外命令皆r6，原服务、已知PID及三端口收尾无错误。剩余安装选择、七真实生命周期故障、项目revision漂移与四受控gate拒绝仍在途，未预记通过。

## c2最终本地验收结果与固定复审

最终r6非editable安装的原submission完整84项通过／801.52秒。原命令使用`-k`尝试选生命周期案例，但收集器把父目录名也纳入匹配，实际收集全部84项；已用独立collection记录核明，不把它描述成预期子集或再开一次重复运行。连同完整processes／architecture的24 passed／4 skipped，最终r6共108 passed／4平台跳过；旧r5八suite188／5仍单独保留，不转授为r6八suite。

最终r6真实Temporal／native验收共91条CLI，内外均指向r6 core／SDK：正常CPU26.764秒、registry阻塞下取消21.694秒、七生命周期故障123.272秒、真实项目revision漂移20.122秒、四原锁内受控payload／file-read漂移61.368秒全部通过。Popen故障没有execute子树／attempt／ack／native result，原final仍为fenced且固定run取消acknowledged，compute仍有余量；停止字段为null，不把“没有启动”当回收证明。其余真实回收／同原件持久恢复合同保持，每项已知PID、原服务及5000／7233／8233端口全部收尾，cleanup错误为空。

源码与新两安装身份、所有新原件及r6自身两轴approve已提供原fresh-context reviewer；R1–R5在各固定修复范围已关闭，整片最终本地两轴仍待其对最后scope／84项终态确认。随后才普通提交／推送当前开发分支，并核完整远端及该候选自己的CI；不合main。当前GitHub匿名REST额度耗尽，官方reset窗口已记录，SSH Ref可读且仍为前置75285e3；不影响本地工作，不把CI查询缺项写成CI失败或成功。

后继Q4.2c控制器草案及其独立计划意见正在另片准备，明确不属于c2提交范围，也未开始后继产品实现。kernel专家保留在v3优化路径；真实GPU／业务训练／质量／收益继续开放。

## c2最终本地独立审查通过

原fresh-context reviewer对r7固定30全文／tracked与untracked完整差异、两安装、全部原件及原84项终态给最终本地需求／结构两轴approve，开放0／0，R1–R5关闭。17 Python AST、13文档／442链接按实际发布范围独立核过；后继两纯计划文件明确排除，本报告和计划的终态接续属于原片状态记账。原本地审查报告快照45,743B，SHA为`7b3cc906075ed0c77bd4b021b221204fa82976bab3faf3d11e410a1cc765e804`，最终本地审计索引SHA为`d23ae233891cfdfbdc394b807316c0230d1bcab29a8b797efa5767b7ab119ba4`；后续固定发布及CI续核会独立追加，不改变这一快照身份。

当前只进入普通提交／推送与自己的CI门禁；本地approve不等于远端已完成，不合main、不强推。kernel专家和真实训练的原开放范围保持。
