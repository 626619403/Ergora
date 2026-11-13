# B2b／c 运行预算实施记录

基线为B2a `c46f3834df08927f7d266757c0f7d3fae8308fb8`；范围和出口承接[总预算计划](../plans/2026-11-12-six-stage-budget.md)。B2a自己的必要CI及精确独立终核已在[原记录](2026-11-12-six-stage-budget.md)关闭，不借其通过关闭本片。B2b／c完整消费者、隔离安装及31文件最终独立两轴的本地出口已通过，开放finding为0／0；普通提交／推送及本候选自己的必要CI待。七种真实Temporal等待、受控九job／七slot旅程及真实模型审查各保留实际范围；完整六阶段原生子模板及真实模型旅程仍归C／D。

## 本片调用关系与节点

原composition adapter提取所属的提交验证Interface，预算variant在同处核原实例剩余量；不在上层按具体后端分派。原composition workflow把原spec运行保留为一个覆写点，预算variant继续调用原六阶段，外层仅监督该原运行的工作截止，覆盖排队／owner／stage／semaphore／poll和活动重试。活动schedule-to-close共享绝对剩余量，fence使用总额内清理预留；到期仍未确认就保留原未确认状态，不能用取消投递声称停止。workflow只读固定UTC截止，实际Linux消费者另核原same-boot时钟。

B2b先通过实际本地Temporal调度验证队列过期、owner等待和活动重试／并行等待；SDK启动的是当前受控预算workflow，不宣称公共新start已开放。B2c再让整个原job由专用进程所有者监督，child只产待核receipt，确认拥有树退出／收集及预算后才由唯一finalizer发布全部正式终态。它们作为同一未发布运行片收口，避免发布没有真实消费者的空Interface；实际单实例／专家模板旅程仍归C／D。

新进程实现必须保留原attempt-before-body、同job／slot不重发、unknown不退款及原jobs ledger；不复制Executor、进程回收算法或建立第二调度器。完整消费者闭合前不改变BudgetedInput的execution_enabled或require_submission拒绝。每个实测／finding／发布节点继续更新此记录和总计划；原件保存在持久私有six-stage-budget-runtime目录。

## B2b 第一次实际Temporal检查

本机已有Temporal CLI1.9.1／Server1.32.0，使用SDK1.34.0和私有独立SQLite／端口，无下载或宿主权限请求。实际sandboxed workflow和原activities调度首轮3通过／1失败（41.31秒）：排队超过工作截止后只有fence、真实owner批准等待和无activity worker的排队到期均按原未确认／停止合同返回。重试夹具只给3秒总额，准备及启动后剩余不足1秒backoff，原Temporal正确不再重试、提前返回CANCEL_UNCONFIRMED；测试却误要求work_exhausted，故该断言失败。它不是新预算失效的证据。

已调整受控场景：首poll失败触发原重试，第二poll保持等待以验证同一截止，不增加模型或改原RetryPolicy；测试控制adapter也改为使用原输入factory的真实v9请求根。继续运行这四个实际调度案例，所有history／trace／原结果及失败保留在私有b2b-source-r1，未声称新公共start或完整job已通过。普通单元CI仅在显式ERGORA_TEST_TEMPORAL_BIN配置时运行该可选本地服务验收，没有新增CI或下载依赖。

## B2b 四场景终态

修正后的私有b2b-source-r2保存完整result、stdout及逐例history／trace／outcome：四项通过（pytest 40.78秒，外层41.47秒）。实际覆盖排队跨截止、owner批准等待、无activity worker的活动排队，以及原poll首次失败重试后第二attempt等待跨同一截止；均未发新预算或额外业务。沿原fence分别保留BLOCKED、NEEDS_RECONCILIATION或CANCEL_UNCONFIRMED，而非把超时视作资源停止已确认。

使用当前源码、原activities和真实本地Temporal服务；receipt及poll故障为受控夹具，无模型请求，也不是公共v9 start／整个job验收。首轮三通过一失败继续保持。下一补并行review祖先semaphore和原生取消／正在FENCING场景，再完成B2c整个job监督、最终回执门禁及提交恢复；当前未做独立代码审查，未开放新运行。

## B2c 实施接缝

选择沿原WorkflowInput factory构造共同job Interface：旧输入保留原线程内body／发布，新输入选择专用job owner；executor不按具体输入类型或后端分派。生命周期实现放独立reference job模块，负责一次attempt、锁、专用owner及唯一finalizer；原Executor只提取“返回待核receipt”的body。子进程入口使用明确模块命令，不在同进程引入inputs→executor反向依赖。选型读取可信已发布task.spec.json，漏传admission的v9请求仍归预算owner处理。

原processes.run增加可选的停止观察函数，保留默认全局TERM语义及原subreaper／回收算法；同一个owner按原预算／fence停止body，再用总额内剩余量监督收集子进程。全部拥有树停止以前不发SUCCEEDED、FAILED或CANCELLED。结果核验失败或总额耗尽只能在停止确认后发布失败终态，待核原件保持；清理无法确认则一直没有正式terminal。最终成功候选先由原publisher持久化，再核同实例总截止并链接原字节，避免慢fsync发布过期success。时间采样仍不宣称内核强实时。

owner锁和attempt按原确定性job及预算摘要绑定，body持有继承锁；丢结果／重启只能观察原attempt。正式receipt已存在而ledger更新中断时只恢复原状态。已有started但没有原owner的停止witness时保留unknown，不自动重做或以PID消失推导后代全部停止。实现与行为检查尚待，不把本段设计写成通过结果。

## B2c 初轮实际进程检查

源码已接入共同job Interface、整个body监督、停止后独立collection、原ledger及所有终态的唯一finalizer，仍未开放v9公共启动。第一驱动误载旧r3安装包，六项在旧v8 adapter处拒绝，不能作为当前产品失败或通过；另一次18通过／4跳过同样只覆盖旧安装。原件和错误scope标签保持，并以本段纠正实际范围。

补齐源码PYTHONPATH后的b2c-source-r2为23通过／4跳过／1失败（51.76秒）。五个新的实际owner案例通过：构造阻塞flock按原截止停止、SUCCEEDED／FAILED／CANCELLED三种待核回执在脱离session后代仍存活时原poll为空且fence未确认、缺admission仍从可信已发布v9选择owner并在停止后拒绝；原架构和进程回归同轮通过，四个Windows专属检查在Linux跳过。唯一失败来自故障注入重用original_run变量导致递归，非产品超时失效。

修正夹具后只补受影响collection及新增最终fsync两案例：b2c-source-r3两项通过（21.18秒）。实际慢collection在同总截止停止后才发布CANCELLED；finalizer的真实fsync延迟五秒只会将旧成功候选改为失败，原正／超期采样均保存。另补owner私有stdout／stderr诊断，避免错误只剩不含原traceback的上层提示。原失败和各候选范围保持；恢复／slot、剩余Temporal并行取消、安装／自身及独立出口继续，尚未宣称完整新生命周期通过。

## 原attempt与ledger恢复

b2c-source-r4两项通过（13.04秒）：实际owner在attempt持久化后丢失，后续原ID仍unknown且不执行body；正式receipt已链接而原ledger更新丢失时，重进只核原候选字节并恢复同hash／session／state，不重跑body。四个停止／收集／finalization候选均留在原job工作目录，正式状态仍只有原jobs ledger。

B2b补验的原生Temporal取消及已FENCING跨工作截止两项通过；review并发夹具在verify阶段错误声称actor为agent，原activities正确提前拒绝，首轮2通过／1失败（33.18秒）保留，修正受控verify的ci身份／完整check后再核。新增提交点在原attempt落盘前后和原client入口重核同实例；已存attempt的到期恢复只lookup，不受新send门禁影响。新公共运行仍关闭，最终安装／实际模型和独立审查继续。

## 补验与源码运行连接

私有b2b-source-r4的review祖先并发名额场景1项通过（16.43秒pytest／17.09秒外层），与r3原生取消、FENCING两例共同补足原七种Temporal等待；此前错误ci夹具的失败保留。b2c-source-r5原生Executor.prepare被真实git.lock阻塞的检查1项通过（11.52秒pytest／12.23秒外层），覆盖实际构造／准入后进入Git的工作段，无模型请求。

submission-source-r1三项通过（46.29秒pytest／47.13秒外层）：原lookup期间到期不写attempt／不send；attempt慢落盘后到期只保留原attempt并lookup；真实start丢回复后到期、关闭执行且损坏新配置仍只对原ID查询，原start计数不增加。SDK为受控fixture，无真实Temporal网络或模型。

源码完整消费者连接后，pipeline-source-r1的原完整材料旅程预算variant1项通过（45.19秒pytest／45.97秒外层）：九个独立job owner、七个原model slot attempt、原Git／检查／MCP及全部停止／收集witness。Agent使用确定性CLI协议fixture；stage由既有驱动串行调用，不能称作真实Temporal完整六阶段或真实模型旅程。该连接不在r1冻结14文件评审内，须由完整最终候选补核；未发布。

## 首轮独立评审与恢复修正

[r1独立两轴](2026-11-13-six-stage-budget-runtime-review.md)基于14文件冻结候选：Spec SP1 P2为Executor父进程退出后，独立owner仍存活或原attempt未知，但重启仅按新future计并发；Standards ST1 P2为Linux测试顶层fcntl导致Windows收集失败，ST2 P3为当前状态文档滞后。Linux专用导入已移到实际用处，当前段已与历史区分；SP1先补真实父退出／跨任务排序竞争回归，再修正原ledger占用与恢复准入。最终完整候选、非editable安装、自身模板与同片复核仍待，未把未验状态写成通过。

## 重启资源占用修正与安装候选

restart-red-r1两项实际失败（25.63秒pytest／27.83秒外层）：原Executor父进程SIGKILL后，z-task的原owner仍运行或原attempt无停止witness，而排序更前的a-task被新Executor放行。不是同一job的flock替代。修正沿原jobs表在独立owner启动前将原claim的RUNNING标为OWNED；唯一record_terminal发布停止确认后的正式终态时才改变该状态。Executor重启按原OWNED集合和当前future的并集计安装占用，允许原job观察，保留rejected／unknown占用；单次main(request)也使用此门禁。没有新表或正式账本。

restart-green-r1两项通过（24.07秒pytest／24.64秒外层）。随后补单次main(request)不能越过原占用，在jobs-final-source-r1同轮与预算提交、原processes及架构共33通过／4跳过（156.54秒pytest／157.29秒外层）；四跳过均为Windows专属，不能证明Windows执行／收集。原运行者停止后a-task实际获准且两原正式receipt通过，unknown不会因Future结束而退款；原attempt字节保持。两red候选与修正前/后的范围分别保留。

install-r1新Python3.12.11非editable wheel SHA256 `e5be26b77c6f1738c774e19c374a8bdb4e0e6a3c8b01bab20e31ecd0553e5d5b`，456产品文件／461 wheel条目与源码、安装逐字相同；461／466两RECORD及283冻结身份通过。隔离-I运行core、原Executor／完整材料／transport及七种真实Temporal三组检查正在进行，尚未给出终态；Windows仍须本候选自己的CI。随包自身结构模板、完整最终候选两轴补核、静态及普通发布也仍待。

## r1 隔离安装终态与服务恢复补核

install-r1三组隔离-I检查全部终态通过：core-r1预算／提交恢复／准备／架构40项（226.66秒pytest）；original-r1原完整材料／原Executor／composition transport46项（355.44秒pytest）；temporal-r1本地真实Temporal七种排队／批准／活动重试／取消／FENCING／review并发场景（85.39秒pytest）。合计93项，各组原result／stdout保存；受控Agent协议、受控receipt与真实Temporal服务的范围保持，不能称真实模型整条六阶段，也不能把Linux结果当Windows。新无模型完整材料旅程含九owner／七slot；旧command／Codex协议fixture、候选门禁及原TERM清理行为同轮保留通过。

完整24文件r2冻结已交原独立两轴补核；实际随包结构模板使用Codex／high正在审查同一冻结，尚无判词。实现者另沿原恢复路径补核“receipt已链接／ledger未更新后重启daemon”的容量恢复，正在以同r1安装包验证；此前通过只验证直接process原ID恢复，不提前扩成服务入口已通过。

## r2 服务恢复修正与自身审查超时

原安装install-r1的original-receipt-red-r1一项实际失败（13.42秒pytest／14.18秒外层）：唯一finalizer链接SUCCEEDED后丢失ledger更新，daemon因receipt存在跳过原job，OWNED持续占用。原直接process恢复通过的范围保持，不能覆盖这个服务路径；独立Spec轴也独立识别了相同缺口，作为SP2与SP1超售分开记录。最小修正只允许retained且已有正式receipt的原job经原owner.reconcile恢复账本，即使旧观察者已记rejection；不重执body。原published-terminal测试扩到daemon重启再原ID观察，没有新增镜像测试或CI。original-receipt-green-r1三项通过（31.62秒pytest／32.46秒外层），同时保持父退出的live／unknown占用两例。

install-r2非editable wheel SHA256 `b4e14c1558c6f178e67f323ab392a8096f76256ed070320a7646dfd4db40418e`，456产品文件与源码／安装逐字相同；461／466两RECORD及283冻结通过。产品差异仅原main的正式receipt恢复准入，受影响job／架构检查进行中；未无理由重复原Temporal／旧旅程全套，原r1各组范围与本轮red分开保留。

实际随包结构模板self-review-r1-codex读取完整24文件（附件414,096B）和五份继承scope的连续UTF8全文，但1801.98秒timed_out，没有result／decision，不能称approve。原manifest／input／scope／成功页字节及最终null已核，四个采样所属进程无存活；原件和partial-read-audit保留。为控制材料与推理成本，r2改为完整产品diff、六份完整相关源码／测试／合同及一份明确标注的publication摘录，八件共110,017B；仍用真实随包模板和Codex，完整24文件交原独立两轴。r2模型尚在运行，未提前宣称通过或覆盖未提供材料。


r2安装受影响job／原架构两suite25项通过（108.05秒pytest／109.89秒外层），包括新增daemon终态恢复及两个真实父退出跨任务／单次入口容量。此后产品无编辑；原r1的93项仍只代表其各自旧候选，r2未宣称全量重跑。r3完整24文件候选交独立两轴复核，聚焦模板仍待判词，最终静态／发布／本候选自己的Windows及Linux必要CI待。

## r2 自身模板判词与完整材料证据

self-review-r2-codex实际760.63秒succeeded／request-changes，Codex／medium；八件packet为110,017B，加入文件标记后的完整附件110,685B。原manifest→准备input→实际input→prompt／stdin→admission→scope→原result全链相等，五scope成功UTF8页连续到null，实际packet与八份冻结原件逐件核过。四个采样所属进程无存活。原turn报告input239,809（其中cached174,336）、output2,039和reasoning994；按后端原计数保留，不重复相加或推账单。原完整24文件的1801.98秒超时仍保留，无判词。

模型唯一P2意见建议：已收集FAILED遇到后到fence也须改成CANCELLED。实现者处置为有争议、待独立复核：原预算合同要求SUCCEEDED／FAILED／CANCELLED都先确认拥有树停止，并禁止超期／取消后成功，没有要求覆盖已生成的失败事实。实际三终态fixture在body回收期间发fence，三个原stopped的body.status均为cancelled，因此走同一停止后fallback；FAILED参数的CANCELLED结果不能推出“收集后失败重写”的额外规则。原件与模型原request-changes不改写；不因该判词直接变更原业务语义，也不把本模型称approve。独立两轴将按原spec／基线分别确认处置。

用户入口说明已同步：README、USAGE的v5 prepare→双摘要create→原start／批准／恢复和未知占用、WorkflowDefinitions，以及架构职责表／预算流图／合同身份／reference边界；上层专家计划链接本片。静态首轮31文件／312本地链接目标／六秘密值issue0，Git空白通过。当前图形向导仍为v6，可引用原生六阶段子模板与最终真实模型Temporal旅程属于C／D；没有将输入预算消费冒称完整嵌套执行。

## 最终代码独立结论与手册收口

原独立两轴已核r3完整24文件、r2安装字节与25项原件，最终代码Spec／Standards均approve，开放0／0；ST1／ST2／SP1／ST3／SP2均关闭。独立Spec按原预算合同全部终态停止确认、禁止超期／未确认success及原基线发布行为，确认不采纳模型“晚到fence统一覆盖FAILED”的意见；该意见没有原规格条款，现三终态fixture也不覆盖它声称的收集后优先级。保留原model request-changes、其全部正文和成本，不将其改称模型approve；没有为迎合判词扩张合同或新增同形测试。

产品代码此后不变。用户手册／架构／上层计划共七文档补齐后，完整公开候选31文件做文档扩大范围独立补核；最终静态、普通提交／推送及本候选自己的必要双OS CI继续，不能借B2a CI关闭本片。下一可执行片C先设计单父／单六阶段实例的精确映射及拒绝范围，复用原creation／submission／预算和运行查询；本片不发布通用嵌套图调度或专家模板已接入的结论。

完整r4扩大范围已由同片原独立两轴补核并写入[评审记录](2026-11-13-six-stage-budget-runtime-review.md)：31文件741,589B，Spec／Standards均approve、开放0／0，原发现全部关闭。七产品／十测试与r3一致，未重复模型或行为检查。模型原request-changes及不采纳理由保持。本地出口完成，以下提交与CI记录另按精确提交追加，不能由本结论推断远端或Windows已通过。

## 本地提交与网络范围

最终静态static-r3为31文件／314本地链接目标／六已加载秘密值issue0、空白通过；冻结ready-r1清单SHA256 `f3505cdee95b0e357567bf96e8219d94c985198c1b2c99d085e6d541e3ce7917`。普通提交为`a00896146c6499f58ae86a5b6b76fa13c3c7c796`，31件Git blob与mode逐字等于ready；同片原评审已独立核精确对象和提交内评审报告身份，详见原评审补记。

首次普通SSH push在banner exchange超时exit128；第二轮45秒无返回，另用既有密钥及host-key身份经GitHub SSH443连接也在握手超时exit128。HTTPS公共仓库读取和两个远端TCP探测同期超时，尚未到密钥认证；不能称密钥失效、推送成功或远端Ref已更新。没有修改SSH配置、私钥、权限或强推。原件位于私有closure目录；自己的CI仍待成功推送后验收。网络不阻断本地C设计与实现，待连接恢复再发布该精确提交。
