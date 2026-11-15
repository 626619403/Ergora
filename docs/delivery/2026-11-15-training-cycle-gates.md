# Q4.2c0.2b：原执行门禁与独立停止通知交付

日期：2026-11-15。按[本片计划](../plans/2026-11-15-training-cycle-gates.md)准备；产品基线 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`，a片自己的CI仍待恢复读取／原终核。当前只有只读源码调查和设计文档，没有b片产品改动、安装、测试或发布结论。kernel专家保留在v3路径。

已核原`training_cycles`、`training_execution_protocol`、`reference_training_budget`、submission、worker、execution、runtime、`processes`及真实原native create接缝。确认四个gate的实际动作与阻塞点：原唯一RPC、原registry lock内lookup、原execution.lock下request／launch，以及原executor callback。完整context仍五key；原native来源集合不变，不能下沉State／SDK。

原`_BudgetPhase`已能start／poll／stop，但构造与budget目录／payload、mode及两帧协议相连；`processes.run`复用唯一reaper却为同步接口；`reference_creation_process`是短编译／专用owner观察，不能直接承担独立fan-out。计划将b1 gate和b2监管／停止分开，避免为复用制造假budget或复制reaper。b2具体共用接口尚未固定，不在本记录宣称其设计或产品通过。

下一步：检查设计链接与完整差异，新的fresh-context reviewer评审b0；a片CI闭合后才实施b1。b1、必要b2a和b2b都各自更新本文件与根PLAN，完成必要回归／自身模板／新独立审查与精确发布后才关闭各节点。真实服务、CPU合同和业务训练仍须各自验收。

## b0独立设计审查

新的fresh-context[设计报告](2026-11-15-training-cycle-gates-plan-review.md)已给需求／维护性两轴approve，开放0／0。独立核两新文档及十份源码共12原件、四本地链接、tracked差异与产品零变动，未运行产品测试／服务。明确prepare在原SQLite reservation中必须保持本地验证；远端核验分别在dispatch、worker原registry锁前和Execution.check；native不读SDK。没有受支持的在线替换父锁writer，沿现有离线联合恢复前提，helper不得删除该锁。两项源码澄清已补回计划，不改变原授权／运行合同。

b1可以独立验收真实完整binding消费与四gate，但自动循环仍以b2／c1为前置。b2具体监管接口没有预先通过，正在利用a片CI等待期进一步固定。08:23 UTC官方查询已恢复，a片run43693023635／attempt1仍in_progress；没有后继产品改动或测试。

## b2监管接口准备

已按原代码写[实际接口草案](../plans/2026-11-15-training-cycle-stop-supervision.md)：cycle异步父侧使用stdlib子进程／pipe tasks，原budget selector保持；两消费者共用原reaper，必要时只上浮两帧codec到现有stdlib protocol owner。S先装信号／watchdog，再运行唯一reaper，匹配stopped后不再spawn；初始化读取与独立writer／逐目标通知／drain／原链观察的边界、容量和实际目录已固定为草案。新的独立审查待开始；没有b2产品或通过结论。

b2原fresh设计reviewer初审发现R1冷inspect尚无原clock／input SHA的截止缺口，需求request-changes／维护性approve。r2补只读bootstrap固定观察截止及完整snapshot后原clock，r3再补匹配stopped后的冷结果读取使用同一bootstrap截止；原失败设计身份保留，正在同reviewer复审，没有b2产品结论。

原reviewer已对固定r3（10,699B／SHA256 `d8d049eb6b281c591e0f3716563adbffd2c87fa14f315a2b54851ef14f7d3692`）给最终设计两轴approve／开放0／0，R1仅设计关闭；原初审前缀保持，[终核报告](2026-11-15-training-cycle-stop-supervision-plan-review.md)14,014B／SHA256 `62b448bd52b4bd82ab457d81eecf0cac37d2fb9935ee376ee4512c329b8a2ea7`。b2产品仍未实施；原source核对归07cbae，不把b1新增代码归给该设计审查。

## b1实施开始

前置a片自己的CI run43693023635／attempt1八job／30必要步骤及原独立终核已精确闭合。b0新的独立设计两轴通过，以07cbae固定产品／原测试，在九文件私有baseline快照上开始b1。当前所有其他工作树差异为已记录的文档／状态接续，不伪称新源码基线为空。实现仍限原protocol、budget、submission、worker、execution和runtime以及原测试接缝；无总Workflow producer、无fan-out和公共新交互。

b1首轮在上述六原owner接线：共享stdlib binding／三件套／ordinal，三异步消费者的固定父run核验，父许可覆盖原RPC、registry create、request／launch和native process；自动actor取原授权。原手工binding继续schema1分支，旧普通schema2路径仍拒绝；历史读取不引入SDK。完整attempt字段固定为`workflow_input_sha256`（父workflow input canonical SHA），与cycle原raw input SHA分列，供后继producer沿同一合同生成。首两个新接缝检查及原拒绝路径正在实际源码运行，没有安装或完成结论。

源码r1选择三项为2通过／1失败（43.06秒）：本地完整prepare及旧普通schema2拒绝通过；正向远端路径因runpy fixture未把自身目录加入sys.path，无法导入新增共享controller服务替身。原错误与JUnit保留；没有正向父run／实际派发通过结论。已修fixture导入路径，并让七种负远端场景分别核其真实错误类型，避免任意ValueError误算身份拒绝。源码r2正在同三项重跑；产品源码未因该fixture错误修改。

源码r2现已终态：三项通过／43.74秒（驱动44.621秒）。完整本地binding、七种固定父run负例、正向一次原start及resume不重发、原手工路径拒绝均在实际原接缝验证；原budget owner精确通知并wait收尾。原件为私有`training-cycle-gates/source-b1-r2.{py,json,stdout,stderr,xml}`。这是源码与SDK服务替身结果，不是安装、真实Temporal服务或训练验收。

源码r3开始七项真实交错检查：原start RPC在途、原registry锁等待，以及request／launch／executor锁／attempt／ack五处停止。沿真实SDK编码、原worker／native executor和真实子进程；受控暂停只置于原发布或原锁内callback，停止与父许可不替身。完整native夹具为复用旧SDK依赖向所选解释器追加已有SDK目录，不把该检查称无SDK；低层stdlib绑定另验。所有源码／测试／fixture在该运行期间冻结，驱动保存前后SHA；没有r3通过结论。

源码r3终态六通过／一失败，117.10秒（驱动118.010秒），前后源码／测试／fixture SHA一致。原RPC及五处执行交错通过；registry用例实际返回`Original training budget cannot start work: stopped`并拒绝创建，失败仅为测试错误要求另一层stop文案。已改为匹配实际状态错误，未改产品源码。r4只重跑该用例、新增原attempt目录同步后停止／resume不重发，以及原完整binding新增的真实`-I -S`无site包验证。完整suite留给后续最终新安装，避免重复源码全套。原r3失败原件保持。

源码r4终态三通过／38.02秒（驱动38.916秒），前后源码／测试／fixture SHA一致。registry锁内停止、attempt同步后停止及已有attempt只对账不重发、完整本地binding的`-I -S`无site依赖均通过。没有新增产品修正；六owner的最终候选与r2／r3相同，测试修正与新增分别绑定r4。

## b1新安装与完整回归

`build-install-b1-r1.py`已构建新的非editable wheel并安装到两个新环境，原候选与旧验收件均未覆盖。core与SDK各652份源／wheel／site产品文件逐字相等，原283参考完整、依赖一致性通过；新增产品文件0，删除0，六原owner变化。原生冻结文件／delta、依赖声明、CI组和模板不变。私有`package-b1-r1-{core,sdk}.json`与`reference-b1-r1-{core,sdk}.json`记录实际身份，测试与fixtures完整复制及SHA清单为`installed-tests-final-b1-r1-inputs.json`。

最终新SDK安装中正在运行原submission完整suite与架构边界，不带源码PYTHONPATH；当前无终态通过结论。之后运行Ergora原结构模板并新建fresh-context产品审查，原b0／b2设计approve不替代本片产品验收。公开架构与组件协议已按实际消费gate更新，同时保留无producer／fan-out／自动多轮的限制。

自身原`ergora-structure-review@1.0.0`已在新SDK安装实际运行，57.525秒，run `75cde5ffc09c4fae8fa85feda5a6cc95`；完整21文件490,275B、原diff及全部三项模板资源进入实际stdin，input digest `c954f52ffe5697386586bb66c935ed884708031dc2fffa408fc7cf53e0594cbb`。原回复需求／维护性两轴approve，没有新增修正意见；它明确完整安装suite仍在途，且仅审所给文本，不认证私有原件或CI。采用用户已授权的Codex回退，不称异后端成功。原件为`self-review-b1-r1.json`和`self-review-b1-r1-codex/`。

新的fresh-context产品reviewer已启动，完整23文件tracked／untracked快照、baseline、实际安装／源码原件及尚在途完整回归均已提供；需求与维护性分列，未有独立终态结论。

## 独立产品R1：已有job与不可分类intent

独立reviewer在原native算法的副本重现：已有完整job、提交intent为部分JSON时，07cbae返回原`local-perf-alpha`，r1候选在原registry lookup前提前JSONDecodeError。证据为`product-audit/manual-existing-probe-r1.{py,json}`。这破坏原只读恢复路径，不能以新创建需要完整授权为由拒绝已有job。新的原create回归在r1不可变安装实红（一项失败／5.47秒），原错误保留；红测实际新文件身份见`red-manual-existing-b1-r1-inputs.json`，通用驱动的旧test_identity字段不是该新增回归的身份。

最小r2修正只在原worker分类：不可读取／不可解码或非对象budget视为无法提前判断controller，转回原super算法；已有job沿原锁返回，没有job仍在原lookup内由budget_for读全意图／授权并拒绝，不能获得新创建权。可读的controller binding继续在原create前取父许可／查固定远端run，原锁内最后gate保持。新增检查覆盖部分JSON／非对象／null budget的原job bytes保持与无job拒绝。源码r5只运行该回归，尚待终态。

r1完整回归继续在其原安装和原测试副本运行，源代码修正没有改该安装或副本；其结果只归r1候选。r2将另建两个新非editable安装、核实际身份、跑受影响的完整controller门禁／手工create与架构检查、自身模板及同reviewer复核，不把r1完整回归或模板approve自动转授r2。

源码r5新增回归终态一通过／10.54秒（驱动11.581秒），前后SHA一致。同reviewer在另一份私有真实native副本独立重跑原probe：baseline与修正候选均返回原job，无job时均为原JSON错误且未创建，R1源码层关闭，没有新finding；初审原件／前缀保持，最终产品通过仍待安装与终态。其新原件为`product-audit/manual-existing-probe-r2.{py,json}`。

r2两个新安装现已各652源／wheel／site逐字相等，原283与依赖通过。相比r1仅worker分类与新增回归改变；完整11个相关测试函数（含五执行断点与两schema owner参数）及架构边界将在r2安装验收；新的原结构模板使用同一最终产品、完整文本和R1红／修证据重新运行。r1原完整suite继续在原副本，不改其候选或输入。

同reviewer补查R1发现同一分类边界的RecursionError：20,001B深层JSON在原baseline仍返回已有job，在r2提前decoder失败；无job两者均拒绝。原`manual-existing-deep-probe-r2.{py,json}`与先前未达该解释器限制的浅probe均保留，R1阶段性重新打开。r3仅将RecursionError加入原分类异常元组，并把该原输入加到既有回归raw循环，不新增抽象／矩阵。源码r6一通过／12.43秒（驱动13.432秒），前后SHA保持；r3新安装开始。

r2自身原结构模板43.242秒、完整21文件494,831B和三资源实际进入stdin，需求／维护性两轴approve，仅归其固定文本。该轮未给后来发现的深层JSON边界认证；原r1完整suite及r2受影响suite仍保持各自输入／安装，r3不会继承它们的候选身份。r3只需验最终分类回归、原controller晚create／registry门禁与完整架构边界，再运行最终自身模板及同独立reviewer复核；没有新产品改动时不重复原完整长suite。

同reviewer已对最终r3源`b068c81e…`独立重跑原深层native probe，baseline／修正候选均返回原job，缺job均原RecursionError且不创建；R1源码完全关闭、开放finding0／0。最终r3两新安装各652源／wheel／site、283与依赖通过。r3原create／controller晚RPC与registry门禁及完整架构边界**19项通过／54.48秒**（驱动55.534秒）；最终实际自身原模板**49.515秒两轴approve**，21文件495,907B、三资源完整进入实际stdin，run `8ff5e256e5f945b3a71b2080786c3679`、input digest `e60b52b61091b9f5944ec5252da9a5f9408ea24d348e16e99e1d341f453134d0`。对应私有`installed-b1-r3.*`、`package-b1-r3-{core,sdk}.json`及`self-review-b1-r3*`；仅报告各自实际范围。

原r1完整127项与r2较广受影响安装检查仍待终态；下一步由同reviewer核最终安装／实际终态与完整候选，再普通发布并等待自己的CI。没有最终b1完成或自动循环主张。

r2较广受影响安装检查现已终态**32通过／338.38秒**（驱动339.438秒），含原完整controller正负／五执行断点、手工schema1／schema2 owner创建／唯一slot、owner死亡与lost-ack恢复、离线history和架构。其产品／测试身份仍归r2；最终r3仅增同一分类边界的RecursionError处理及同回归raw输入，已在r3原接缝19项重验。原r1完整127项仍在途，无终态主张。

原r1完整回归现已终态**127通过／1208.80秒**（驱动1209.961秒）：完整原submission suite与架构边界在其不可变新安装和测试副本通过。它保留r1候选身份，不覆盖随后发现／修正的R1；最终r3的19项、r2的32项与同reviewer原native复现分别验证相关最终变化，没有重复不变的完整长suite。最终本地终核所需原件已齐，待同reviewer核完整范围和原终态；尚未发布或认证自己的CI。

## b1本地独立终核

新的fresh-context[产品审查](2026-11-15-training-cycle-gates-review.md)已最终本地需求／维护性两轴approve，开放0／0，R1含深层JSON完全关闭。原初审、部分修正及重开历史保留；终核报告23,747B／SHA256 `ffed5ed33ddaffaec80b8c5813600cfbe454c42105782af2dadf4fb4f9f4403b`，原20,124B前缀逐字保持。独立核完整24文件tracked／untracked范围、原diff、三候选终态、最终652源／wheel／两site及177输入副本；公开状态记账不递归审查。

收尾：本方原67个已知owner身份无匹配活进程；reviewer另扫含最早r1工作目录的68份owner原件同样无匹配，两个观察分列，均不声称全机无进程。原件分别为`owner-closure-b1-r3.json`、`product-audit/owner-closure-verification-r3.json`。所有长期证据保持在项目持久目录，未创建公共新交互或总Workflow。

b1本地实施／验收／审查闭合，接下来普通提交／推送当前开发分支并核自己的精确CI；发布终态未完成前不把b3总交付关闭。b2a必要监管整理／b2b独立通知、c1独立cycle进程／loop／queue和总Workflow、c2公开CLI／HTTP、新可信CPU两轮、Q5.2据证整理和Q6继续开放；真实GPU／业务训练／质量／收益仍需各自外部条件。

## b1普通发布与自己的CI

已普通提交／推送`43d215af0ed372d7d1502bbe244b5631ee6d9b24`，parent为07cbae，tree为`a7e17fcd1dd29e80c9fa1607fae93a8c34869e2a`；24份已审staged blob与Git对象逐字一致，原报告前缀保留，实际post-push完整SSH Ref相同。没有合入main或推送后继产品。私有`staged-publication-b1.json`、`publication-b1-local.json`与`publication-b1-remote.json`保留身份。

自己的官方CI第一次查询为09:22:55 UTC匿名REST403／remaining0／reset09:23:01，原件保留；重置后09:23:47 UTC查询200，精确run **43698966489／attempt1／push**匹配本提交完整SHA及本分支，当前in_progress。未给终态CI成功结论，也不借前片自己的成功。原HTTP与完整响应分别在私有`ci-b1/20261115T092253998868Z-*`与`ci-b1/20261115T092347821198Z-*`。同reviewer固定发布核验已请求；完整CI终态待。
