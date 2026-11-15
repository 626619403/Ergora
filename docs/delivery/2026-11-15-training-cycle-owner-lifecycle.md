# c1b1：子预算owner生命周期逐步交付

日期：2026-11-15。准备基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `refactor/architecture-foundations`。承接[本片计划](../plans/2026-11-15-training-cycle-owner-lifecycle.md)，下文按研究、设计和产品实施分别记录；最新产品状态见末尾恢复检查点。没有服务、总Workflow或训练验收结论，kernel专家保持v3。

c1a2已固定本地十二文件提交，原reviewer固定提交需求／维护性两轴approve／开放0／0；其普通发布仍在原队列。后继只读研究指出：短S-H内直接调用原start，会令长期budget owner成为原reaper的后代；asyncio直接兄弟根又有正常teardown主动kill的风险。先闭合实际生命周期，不能把短暂owner_alive、独立session或两Worker注册当跨重启成功。

私有 `training-cycle-owner-boundary/reaper-probe-r1.py`先因存活观察未处理已退出进程的proc文件而退出1，未启动兄弟case，原脚本／身份／S输出与失败JSON保持。r2只修观察，沿新安装原 `processes.run(supervised=True)`执行：H的独立session惰性后代在S结束后活匹配false；调用方兄弟根在另一个S结束后仍活，随后TERM／wait退出-15、活匹配false。r2退出0／0.582秒，脚本SHA256 `c7a8331e17284133b9d83957eecbeb0b59a3d8db92266fb6157c70e3c3b8ba9a`；安装processes源码SHA256 `56c1961745b03ee4775e75f17dcb5a30a3d105e4bbd0f3fb516451e0fcd55867`。只认证惰性进程与实际Linux reaper，不认证预算owner、服务或重启。

SDK边界研究已有标准sandbox／显式pass-through／core缺SDK与Python Worker构造证据，见[研究报告](../research/2026-11-15-training-cycle-sdk-boundary.md)。它没有RPC或Worker.run，不能作为真实配额验收；公开stdlib根启动的正常teardown／父SIGKILL对照正在追加。拟仅将OS Popen创建异步化，所有业务与原预算执行仍在独立进程；该候选尚未通过设计，未修改产品。下一步固定实际spawn／初始化／确认／取消字段和职责，交新的独立设计审查，再实施。

## Stdlib生命周期观察与设计收窄

研究r2六case退出0／1.469秒，ThreadedChildWatcher下纯async正常teardown／GC及父SIGKILL后的惰性root实际仍活，不能写成必然kill。async transport的close／析构有kill语义且无公开detach；Popen析构无kill，窄的to_thread仅OS创建＋public connect_write_pipe＋非阻塞poll正常退出／SIGKILL对照均存活，六root最后由独立harness精确TERM／wait-15且proc全部消失。原r1的os.pidfd_open缺席失败已按原身份经libc pidfd精确TERM并确认proc消失；恢复者不是其父，未称已wait。原失败与最终六case分别保留。

据实际caller进一步删减设计：原_Submission在锁内prepare仅一次created=True，直接复用原不可变子intent作为根启动offer；created=False而无确认owner就unknown，不Popen，不新增launch.request／进程账本。schema2在实际ensure_owner最后点统一existing-only，schema1原launcher保持。不同H阶段与根传送消费一个原compute∩control窗口；窄线程不承载任何业务文件／预算。具体设计已写回计划，下一步新的fresh-context设计两轴审查；真实预算owner与产品仍未实施。

## r1独立设计finding与r2修正

新的fresh-context reviewer对r1固定六文档／源零diff给需求request changes（R1／R2）、维护性request changes（R2）；[原报告](2026-11-15-training-cycle-owner-lifecycle-design-review.md)保留取消职责与封套／恢复缺口，属于未实施设计问题。R1现明确完整owner确认才交接，之前由本调用方精确收尾根，之后普通活动只收尾短S-H；总controller取消／用户stop另走原b2b veto／通知／drain／实际观察，c1c消费者尚未实现。R2新增四mode／完整字段与结果表；所有H及根传送复用最初prepare请求的同一window，原schema2 submission最后点也核这份上下文。失联后活owner但无attempt只观察，不借resume补SDK start；有attempt只复用原reconcile算法，原唯一offer不重发。

r2还明确原Popen pending的真实句柄必须保留、OS创建卡住时不能保证default executor正常退出有界；root装载native环境后保留原应用＋选定native PYTHONPATH。没有新增持久交接／启动账本，未改产品。下一步冻结完整r2并由同reviewer复核，再实施。

## r2设计独立闭合

原fresh-context reviewer已逐字核最终r2七份快照、218本地链接、原resume无attempt派发路径、b2b独立停止分支及原25个GATE_SOURCES／283参考，需求／维护性设计两轴approve／开放0／0；R1／R2只在设计层关闭。报告SHA256 `e5e986722e5039a2811f48be603f96f1c7b8461a484da66edb6160e8bc39ecc0`，原r1意见和证据保留。产品、实际预算owner跨调用／重启、pending spawn／取消／恢复、新安装与真实cycle配额仍未验。接续固定本地设计／状态文档，再以其准确提交为产品实施基线；不把原惰性probe当预算验收。

## 固定设计与产品实施恢复检查点

设计／状态13份纯文档已固定本地`4d060ae8609424cc2f6f5f0b44393da7e2ba03f7`，父`f00bfdfd15173ceb0e961681679d6d3d62254bed`。原reviewer已在原报告追加固定提交需求／维护性两轴approve／开放0／0，核229本地链接及非docs零差异；追加不改变原r1／r2前缀。此提交为以下产品实施的基线，仍在原逐片发布队列中。

当前五个原文件存在**未完成、未提交**的产品修改：

|文件|已做的接线|尚缺的真实消费／验收|
|---|---|---|
|`training.py`|从原`_submission`提取并复用`_prepare_submission`，保留原短事务与后续原dispatch／resume|新prepare-candidate H尚未调用；旧手工行为未重验|
|`training_execution_protocol.py`|新增候选四mode、严格start_context和原prepare operation／同一window读取校验|真实H、根bootstrap及最后gate尚未联通；无运行验证|
|`reference_training_worker.py`|仅向原`_CycleOperation`构造器接入start_context／共享window及mode集合|尚无新H处理、一次Popen编排、完整owner确认、交接前后取消或只观察恢复|
|`reference_training_budget.py`|schema2 existing-only、原dispatch窗口校验与仅生成根材料的`launch_context`|新根`controller-owner`入口／来源校验／日志初始化及真实caller未完成；schema1未重验|
|`reference_training_submission.py`|原SDK start最后点接同一窗口的timeout|新内部上下文尚无完整生产caller；旧schema2 fixture直接dispatch将不再满足合同，须沿真实新caller迁移，不伪造上下文使测试通过|

上述五文件只有`ast.parse`语法检查，不能算产品测试、新安装、自身模板或独立产品审查通过。现阶段不得运行此半成品并宣称cycle已经可用，也不能继承旧c1a2或惰性probe的运行结果。

下一步先完成原worker新H与根bootstrap、唯一offer／同一窗口的真实接续、只允许对账的恢复路径、Popen真实句柄和公开pipe的生命周期；重点保留应用＋选定native的PYTHONPATH、完整确认后才交接、交接前真实TERM／wait、交接后普通活动取消不杀预算根。随后沿原fixture验证跨调用／正常loop退出、失联／重复／取消／窗口耗尽与schema1，再做新非editable包、适用接缝、自身模板及新的fresh-context产品两轴。总controller停止继续由原b2b契约负责，c1c消费者尚未提供。

用户新增的调研复用、循环／非agent Hook、设计讨论与缺失知识补齐已保存到[WA1–WA5计划](../plans/2026-11-15-workflow-evidence-and-human-gates.md)，审计未启动；BR1／BR2继续独立分支，不改变本片产品身份。

本次仅补恢复／状态记录：六份变更Markdown的204个本地链接无缺失，两份并行分支交付报告路径存在，`git diff --check`通过；重新解析五份当前源码均通过，未运行行为测试。准确HEAD／五源码摘要与检查范围保存在私有`training-cycle-owner-boundary/implementation-resume-r1.json`，与旧研究／验收分别归属。

## b1.1／b1.2产品接续与首个真实接缝

已补原H的prepare／confirm／dispatch／只对账reconcile四分支、共同native项目装载与原根bootstrap，以及原调用方持有的一次Popen／公开pipe／确认交接／非破坏观察。根与SDK最后点复用原prepare请求及同一compute∩control窗口；原schema1入口保留，schema2原手工owner入口不再能补启。代码仍未完成整片验收或提交。

源码首个实际接缝r1在原7秒控制窗口只得到unknown，JUnit失败保留，不推定成功或根已出生。正向多步生命周期用例随后显式选择原合同允许的30秒控制窗口；r2真实触发公开pipe已关闭后再次abort的AttributeError，已保存准确源码／fixture快照和JUnit。最小修正为shield关闭观察，仅在关闭尚未完成时abort；r3同一正向用例1 passed／24.40秒：SDK服务替身编码下同一原预算根在短S-H及正常asyncio.run退出后存活，再次调用无offer、无第二次start；三个H消费同一原window、授权原bytes保持，父loop业务State／record读被禁用。最后按原身份TERM、原预算清理和真实Popen wait收尾。

这只是首个源码接缝，不是新安装、服务或训练验收。重复／丢回复／确认前后取消、窗口耗尽、旧schema2测试迁移、schema1回归、新包／自身模板／新的独立产品评审仍待。私有`source-r{1,2}-snapshot`、inputs、各JUnit和工作区保留各自身份；不把r3通过改标到旧两候选。


## 恢复核对：r4／r5与独立产品finding

已核私有JUnit原件：源码r4共9项，7通过／2失败／289.49秒；失败为测试用固定20秒观察窗早于合法30秒operation截止，SDK-start与丢prepare回复的故障边界尚未到达。原记录保持。仅将观察改为本次operation实际剩余窗口及任务终态后，r5这两项通过／62.30秒；其余7项仍归r4，不能写成一次完整9项通过。

原fresh-context产品reviewer在a4371c8＋准确13文件补丁的独立树发现：R1，pre-handoff根自然EOF夹在poll与通知之间，或pidfd通知OSError，会跳过实际poll／wait，且内部异常可能覆盖调用者取消；R2，reconcile先解析owner，坏owner会阻断已占用attempt的同一run／memo对账；R3，新caller的测试固定观察秒数可能早于合法operation窗口。独立惰性子进程与只读reconcile spy已分别实证，正式报告待reviewer落盘，不冒称已关闭。

当前修正中：R1保留根的真实句柄与退出等待，活根通知失败保留诊断，原取消在收尾后继续抛出；R2将原intent定位与严格owner定位在原worker内分开，confirm／dispatch／notify的完整身份检查保留，reconcile沿原submission的owner unknown观察独立对账；R3把本片迁移的两处12秒观察改用同一原operation截止。尚未运行修后接缝、新安装或自身模板。下一步先实证原两处最小反例与适用真实caller，再完成本片包和独立复核。


## 修后源码与双安装r1

修后源码r6清理两项通过／1.96秒，完整生命周期9项通过／160.69秒：原预算根跨短S-H及正常loop退出、确认前与确认后四个取消边界、丢prepare回复不再授offer、晚到Popen句柄、原window／owner漂移均过；SDK-start取消例还在损坏owner原件保持时，通过真实原H＋SDK编码服务替身补同一run receipt，owner_status保留unknown且starts仍1。该结果不认证真实Temporal服务或训练。

已构建新非editable wheel `73149fcb805a6ee833acf6f5bb2180eadac956c2c6ea0b1b757952d1e15968f2`；core／SDK各652源码／wheel／site文件逐字同一，仅五个原产品文件相对a4371c8变化，无新增／删除产品文件；283参考及两环境依赖检查通过。冻结178项测试／示例输入后，适用的新生命周期、原controller四gate／独立stop、schema1手工start与恢复、offline training及架构边界的安装回归在途。原fresh reviewer已收到固定r2完整快照，尚未给修后最终结论。core实际观察与自身原模板仍待终态，不能以源码通过代替整片验收。


## 自身模板新finding与实红接续

自身原`ergora-structure-review@1.0.0`经真实Codex fallback完成91.711秒，结果request-changes；19文件536,818B和3份祖先资源完整核入原stdin，结果SHA256 `d92685c1b49c86e3e7e632a6cd394bf20784322eec142b2dc2d992308e65cdfc`。它提出两个新的边界：P1正常loop teardown全任务取消可以直接取消to_thread包装而遗失晚到Popen；P2最后owner读取之后仍返回先前的remaining。该模型意见只归完整供稿范围，不替代独立原件复核或外部CI。

源码r7两项失败／24.65秒。P1在真实原prepare＋晚到OS创建上实证：asyncio.run收尾后operation.root为None，但harness已拿到一个实际仍活Popen；harness精确收尾，原失败保持。第二项新fault过早命中ensure_owner的首次dispatch_remaining，未到attempt，属于错误接缝，不能声称P2最终SDK越界已实证。现将fault限制在原attempt已经存在的最后读取，并以r8-red单独复现；此时五产品仍为原r6身份。

拟将仅OS创建的结果保留到公开concurrent Future，父loop只轮询done/result，不让asyncio全任务取消销毁唯一创建完成句柄；等待实际spawn／退出期间吸收取消后继续真正收尾，业务仍不进入线程。仅创建调用使用一次性ThreadPoolExecutor.submit并shutdown(wait=False)，不等待长训练、不增加进程host或账本，OS创建不可中断／可能无限等待的支持限制保持。此为最小生命周期接缝修正，先交原reviewer核边界；P2先核owner再由原_start_remaining重读完整来源／parent并在最后读取剩余时间。安装r1较广回归仍在途且已出现失败，旧包／原输入保持，不把新源修复标到旧安装。


## r8／r9／r10与安装r1终态

r8将fault正确限定到原attempt存在的最后owner读取，实红1项／17.51秒：原attempt存在且错误地保存receipt，服务starts1；r8 JUnit已在worker修正前终态，旧五源码身份与r7准确快照同一。修后r9五项／27.22秒通过，仅认证CFuture与最后剩余时间等该候选接缝。

原独立reviewer进一步独立实证：全loop取消活动S-H时，原监督任务／读／wait也一起被取消，三个原S/H／新session后代仍活；harness只通知原S，原唯一reaper才完成收尾。这是自身模板P1的另一分支，登记R4开放；P2旧remaining登记R5，已由有效r8红／r9绿及源码关闭。现仅在原_CycleOperation让直接取消转request_stop，沿原stream重接被取消的读／wait、被取消stdin只close、不重发；实际S TERM／原matching stopped帧／退出保持原顺序。原spawn已成功但句柄未赋值的交界也重新取得实际结果；只有stdlib创建本身终态cancelled且尚无输入时才返回unknown。

r10真实原S-H与候选接缝6通过／49.43秒：包括活动H＋新session后代全loop关闭、confirm H全loop关闭、原caller取消与新根／最后SDK边界。随后给confirm用例追加根通知前S已退出／原matching帧已观察的检查，后续r11另验，不将新断言归回r10。

较广安装r1最终62通过／8失败／945.11秒，JUnit／stdout／退出码一致。七个history拒绝例最终读取了从未调用的训练服务文件，前面的实际拒绝／原intent／无attempt检查均已到达；改为核不存在等价starts0。launch例的原admission stderr明确同一run历史未知，服务文件被另一惰性RPC旧快照覆盖成starts0，不能简单归因15秒等待。现仅修服务替身：所有RPC在原file_lock内重读／追加／原子替换同一服务记录，原request／starts／calls不被旧导入快照清除；取消／release两个实际fixture调用者同步迁移新save参数，产品权威未改。r11复验原七拒绝／accepted、launch及两个全loop边界在途。原62通过仍属于旧安装r1，不继承为后继新包。

## 恢复核对与新安装r2

r11现已终态11通过／186.65秒：两个全loop边界、八个history分支及launch接缝。未找到本次运行前的完整输入manifest，不能事后把当前文件冒充原运行快照；该限制登记在私有`pre-install-r2-identity.json`，r11结果按其实际证据范围保留。当前11个变更产品／测试文件已逐字重核，与原独立reviewer固定r3一致。

新wheel SHA256为`565aefd026e01f83470af5e49a74d1743c3919779a4b4a217fc2dc56755eb29b`。新的core／SDK非editable安装各652文件，源码／wheel／site逐字同一；相对a4371c8仍仅五个原产品文件变化，无新增／删除产品文件，283参考及两环境依赖检查通过。实际SDK版本1.34.0，core明确无SDK。全部178项tests／examples输入在运行前冻结；原较广70项加两个pending-root及三个原operation取消边界，共75项安装回归已启动，终态待，不能移用原r1或r11结果。

独立reviewer在其固定r3中又以真实惰性S/H／新session后代验证cancel-all：caller保留CancelledError、两个原帧完整、S正常退出，三进程身份失活且proc消失，无harness兜底TERM。R4活动S-H源码分支已获得独立实证，整片安装与最终审查尚待；根通知前S已退出的新断言由本次冻结输入r2认证。新的SDK-free实际观察、自身原模板及全部收尾继续逐项验收。

远端前片1b8c2ed的准确CI现有终态失败，已单独记入[原片交付](2026-11-15-training-cycle-stop-operations.md)。此片继续本地验收，不把该失败或其修复归成当前候选的CI。BR组合安装在隔离工作树推进，WA三审计与详细方案保持文档状态；当前产品身份不被它们改写。

r2 core实际SDK-free观察1.220秒通过：经原异步S-H执行inspect，父loop的State／SQLite及业务原件读取明确禁止，原八文件bytes与DB rows保持、同一operation窗口保持。它只认证冷观察，不认证SDK、总Workflow或训练。原独立reviewer固定r3源码需求／维护性两轴现均approve、开放0／0，R1–R5及S1源码 finding关闭；35,266B报告已逐字收到，SHA256`cd76f799449707b4d6e608d53c0653c06304e0e4bac24d1d60ef8bb167462a2a`。安装r2终态、自身模板与整片最终独立门禁仍待。

新安装r2经原`ergora-structure-review@1.0.0`完成真实Codex调用56.323秒、decision=approve。21份完整文件584,346B及三份祖先资源完整进入实际stdin；输入digest`5e27cff0f0bf66d878b5f676a8e7ec99cb9644985a47a4d8672da4ac4906cdd8`，原结果SHA256`e44a6bfc1b3b3b2622d45cc28c5b7ffa865b1bd3ad603f42fa9c2455d23f4d02`。按用户授权回退Codex，没有异后端成功主张。模型明确安装回归当时仍在途；其结论仅归完整供稿，不能代替回归终态、原件核验或最终独立审查。当前计划已将80,454B旧检查点逐字归档，活动状态精简，245个相关本地文档链接目标通过；归档不改变任何历史验收身份。

## r2终态与精准r3覆盖补充

安装r2实际终态为**76 passed／985.95秒**（JUnit985.931秒，外层989.215秒，exit0、stderr空），而非前述预估75；旧70项之外还有最终owner-deadline分支，共六个新增case。JUnit17,627B、SHA256`a3bf566750d38b8cddd4606f966ebdd1b0de0dbf80f7ec4075d91d1354c02de8`。独立reviewer直接重核了原结果、652产品／两安装RECORD／283参考／25来源及178冻结输入，也核了21完整文件／三资源进入713,439B实际stdin。原r1的62／8与r11身份限制保持，不回写成同一次绿。

覆盖核查发现b1.3中并发offer、发送完整输入／确认回复丢失、pending-Popen实际窗口耗尽和schema2 NOT_FOUND尚缺明确原caller序列。现在只沿原正向／取消／pending测试及已有fixture扩展：两个真实Candidate同时争同一intent，仅一个有Popen；原完整输入已发送后取消；confirm H已返回owner_confirmed但S结果读取被阻塞后取消；原SDK-start丢回复先NOT_FOUND保持attempt与starts，再接受同run补receipt；OS创建保留到原实际窗口耗尽才释放，原stdin关闭且不交接。另精确运行既有`test_owner_observers_share_the_initialization_read_lock`来覆盖原初始化锁，不另搭一套owner测试。七个精准case使用同一r2已安装产品，178项新测试输入另冻为r3；结果在途，不重跑已通过的76总suite，也不将新测试归给旧输入。

实际预算根父SIGKILL仍未验。原b1.2产品目标是短S-H结束与正常loop重启后的同一根／clock存活；此前惰性创建研究不能认证这条更广场景。最终验收将保留此边界，不为覆盖数字增加进程host或修改产品职责。

## c1b1最终本地闭合

精准安装r3已终态：**7 passed／153.70秒**（外层154.801秒，exit0、stderr空），继续使用同一r2产品包；JUnit SHA256 `5a112678b18ef884dd91ffdfdc917ab0feb3b54f130090f8e0784d64753ca6b1`。新增序列与r2的76项各属自己的178份冻结输入，没有重跑或重标旧suite。

原fresh-context reviewer已对25份完整scope／patch、五产品、六测试、652双安装、283参考／25来源、两轮结果、SDK-free真实H、自身模板完整stdin及收尾原件完成终核，**需求／可维护性均approve，开放0／0**。最终[审查报告](2026-11-15-training-cycle-owner-lifecycle-review.md)46,090B，SHA256 `e9f6438327eb2e158060a7b11a23ad0f12eb541691f9b8bbe15a0e52c689551d`；逐字接收追加段，四个历史正文前缀保持。R1／R2／S1／R4／R5均关闭。

收尾记录实际解析十四个工作根的7,616份JSON，267个不同完整进程引用已由reviewer逐一对1,697份来源原件复核；266项当前proc不存在，另一项是与当前进程不符的历史固定PID1，活匹配0、unknown0。九份>2MB文件未读，此范围不是全OS spawn清单；非父进程核查不冒称wait。实际退出等待由相应用例和原reaper支持。原件索引为`final-verification-r4.json`，SHA256 `0a48ba206e99dea84c0cf415b27c5d75f0988965a8813912b36a3a834a89a403`。

据此本片内部单候选生命周期本地闭合，进入固定提交。实际父SIGKILL、独立cycle服务／配额、正式总Workflow、后继接受门槛、自动多轮及真实训练仍分别未验。前片准确CI失败与其独立修复、BR组合和WA设计不借本报告批准；普通发布及自身CI另记。

已固定本地`d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，父a4371c8。原reviewer核11个Python提交blob与原r4同一、五产品与r2包同一，状态／完整报告身份准确，固定提交两轴保持approve／0。追加报告47,319B，SHA256 `411b5608ec93c4553477066c797a87a7d6590de6cd74ea129a5a27f36bd99829`，历史五前缀保持。后续BR联合安装及CI fixture适配另片验收，不反向改本片身份。
