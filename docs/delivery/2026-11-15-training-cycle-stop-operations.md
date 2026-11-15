# b2b：训练循环并发停止操作交付

日期：2026-11-15。本地基线877e1e4f7397731915c36b82f335efeaab3854dd，分支refactor/architecture-foundations。[实施计划](../plans/2026-11-15-training-cycle-stop-operations.md)承接原已批准监管设计。三个既有owner分别持有纯身份／截止、异步operation监管和具体原件／效果用例；复用原两帧codec、只读_load与唯一processes.run reaper。

立项时仅完成原设计、实际调用和前片本地固定身份核对。以下逐步记录实际实施／验收，尚不声明停止fan-out、总Workflow或真实训练已通过。前置43d匿名API限额reset10:23:02 UTC及各自发布／CI门禁保持。kernel专家继续在v3优化路径。

## 首轮实现

原三个owner已接线：stdlib请求校验与同一截止、父侧异步spawn及独立pipe／wait tasks、S内唯一processes.run监督一个H、冷inspect及writer／逐owner通知／drain／执行链观察。父loop只读内存／内核身份和异步管道；H复用原Path读取／_Submission.load／CycleAdmission／ExecutionRecords，不创建State，不用当前SDK或来源校验来阻断旧owner精确通知。完整执行观察留独立操作文件／SHA，成功通知不称executor已停。

所有效果分支由完整原snapshot准入，H再核原文件与原clock；冷观察截止在spawn前只计算一次，匹配stopped后的结果读取也使用它。取消保留真实spawn task／handle并等待原S收尾；没有新增reaper或修改原budget selector／执行器。新增一个原测试fixture只在真实文件同步／owner读取／post-stopped读取接缝注入阻塞，保留原监管和回收器；原controller fixture可显式传入有效预算，既有调用保持原配置。

`git diff --check`和三个owner解析通过。原接缝中的新停止／取消／过期场景与完整架构正在源码运行，没有终态结论。首次真实冷stopped后读取截止及spawn／helper取消接缝已有局部进展，不提前宣称完整运行通过。需要后续新的非editable安装、必要原回归、自身模板和新独立产品审查；原设计批准不转授产品。

## 源码r1终态与修正边界

原源码选择与完整架构终态为19通过、3失败／42.84秒（驱动43.770秒）。原日志、JUnit和候选身份保持，不覆盖。真实产品问题为cycles新增反向导入submission／worker形成依赖环；须在原worker运行边界保留异步编排和原intent目标读取，cycles保留Path领域记录用例，不能弱化原架构检查或复制reader。

两项新测试环境问题在停止fan-out前发生：双owner的beta启动碰到服务替身只存一个全局Experiment而被原完整身份检查拒绝；已尽clock检查误把create返回当含plan的对象。修正测试替身隔离／读取原配置，保留产品身份拒绝，不为过测试改产品合同。冷inspect匹配stopped后阻塞结果读取截止、真实spawn取消和H／新session后代取消接缝通过；整体并发停止仍未通过，新的非editable安装、自身模板与独立审查待。已把实际终态和架构修正方向发给本片独立reviewer。

## r2源码修正已接线

将本片新snapshot／目标读取／H操作／fan-out移回原worker，调用cycles原Path记录读者，cycles本片恢复基线字节；没有隐藏或删除原架构检查。服务fixture新增可选独立record路径，仅双owner新调用使用，原调用仍用原record；已尽clock接缝读取实际配置。修正后运行另存r2；当前还没有r2终态，未推送。

## r2源码终态

修正后的同一原选择终态22通过／57.23秒（驱动58.137秒），实际源码／测试运行前后SHA相同；原架构检查、真实两个原owner以及writer同步／alpha读取并行阻塞时beta被精确通知、冷stopped后结果读取截止、spawn与真实后代取消、原clock已尽不派发均通过。r1失败保持。尚需错误controller／PID与无当前来源／SDK的实际通知、原完成／人工release回归、新安装和自身／独立审查；不据局部通过标完整片完成。

## 原身份／缺失安装接缝及新安装

源码r3补充两项终态通过／27.72秒，运行前后源码／测试同一：使用原prepare写出的完整controller intent及一个记录为schema1旧owner身份的真实受控Linux进程，先分别改变原controller run／start_ticks，实际S-H操作拒绝且目标仍活；恢复原bytes后移走注册installation、禁止H导入temporalio并令当前来源／installation validator直接报错，实际pidfd通知原目标成功，仍不称executor停止证明。这个单项是归档身份边界检查，不是实际训练；实际两个budget owner并发属于r2。另复用原完成结果／大型gate／人工release未fence测试通过。

新非editable core与SDK各652文件，source／wheel／site逐字相同；只有原worker／protocol两产品文件改变，cycles保持基线。原283参考文件与两依赖检查通过，core确无temporalio。178份测试／示例副本冻结；原停止准入／registry／可见与持久／排空／人工release、全部本片新接缝及完整架构开始安装回归，终态待。

## 安装r1终态与通知／收尾检查修正

安装r1终态30通过／1失败／125.42秒；原JUnit／stdout／候选保持。失败在新并发测试要求beta在固定12秒内退出；同一原操作H输出已记录`notified`，原owner随后沿自身fence／cleanup结束。该断言混淆精确通知到达与独立owner完成回收，也额外缩短原总预算；产品操作及原生命周期无需改变。修正将于真实pidfd发送返回后记录原目标身份，验证该事件发生时writer与alpha读取仍阻塞，再分别等待原总截止／原收尾并核已知actor。不靠通知推导executor停止，不改原clock／清理算法。

自身原结构审查模板19完整文件／498,679B、三原资源完整送入，Codex48.863秒approve；仅认证当时完整供稿结构，报告明确安装回归尚无终态。新core安装实际异步S-H只读inspect1.059秒通过，运行时确无temporalio，父侧State／SQLite被禁止且七份原cycle文件逐字保持。这两项不覆盖上述新测试观察条件修正；最终独立产品审查仍待。

## 安装r2精准复核

同一r1产品wheel及两安装未变；只修正上述一个新测试与仅该场景生效的fixture通知事件。新的178份冻结测试副本和精确r1→r2差异单列保留。修正项实际安装运行1通过／29.25秒（驱动30.153秒）：真实pidfd返回后完整beta身份匹配，writer／alpha读取仍活且受阻，随后各operation的匹配stopped与两原owner最终均已退出。r1其他30项保持其原同一产品终态，不把r1失败改写为全通过，不无变化重复整个选择。最终供稿模板与独立产品终核、原件身份及所有已知actor收尾正接续。

## 最终本地身份与独立终核输入

最终自身原结构审查模板19完整文件／501,008B与三原资源完整送入，Codex43.807秒approve；原r1供稿和原回复分别保持，不称异后端或独立磁盘验收。运行后重新核源码／两安装各652文件与原产品manifest同一，最终178份测试／示例与新冻结副本同一；源码r1／r2／r3及安装r1／r2全部原记录内的38个完整PID／start_ticks／boot_id当前活匹配0。kernel与其他模板未改。

新的fresh-context reviewer正在对最终七份变更、原baseline、所有实际终态与原失败作需求／维护性两轴终核；原架构环已修复，产品终核仍待。下一步先固定本地提交；普通发布按前片准确CI与各自发布／CI门禁，不能把本地验收称远端闭合。c1独立cycle进程／总Workflow及stop配额、c2公共交互、真实CPU两轮／GPU／业务训练均继续开放。

## 独立本地门禁闭合

新的fresh-context reviewer已对最终八文件、安装r1原30项／原失败与r2精准修正项、同一产品双安装、实际core操作、自身供稿范围及38个actor收尾给最终本地需求／维护性两轴approve，开放0／0；R1依赖环与R2把通知等同退出的测试问题关闭。[报告](2026-11-15-training-cycle-stop-operations-review.md)10,133B／SHA256 `3c316391622eafd78c82b9c1855b3fb1f06a6c0ef5baba15ef160b3367eea8b8`，原设计或自身模板均不代替该独立结果。现在可固定本地提交；普通发布和自己的CI另验。32候选最大容量、独立cycle服务／总Workflow、真实CPU两轮与GPU／业务训练没有借本片通过而完成。kernel专家保持v3路径。
# 远端终态接续（2026-11-15）

准确发布`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`的官方run`43713822317`／attempt1／push／`refactor/architecture-foundations`已终态failure：七job success，Linux 3.11 group5的job`132810977047`失败。此前in_progress及403保留其原时点，不覆盖成success。

公共job HTML HTTP200暴露原失败：`test_cycle_stop_notifies_peer_while_writer_and_other_target_reads_block[controller_admission0]`读取`operation-markers/stop-writer`得到FileNotFoundError；该job汇总1 failed、524 passed、13 skipped、1612 deselected／998.57秒。匿名日志下载HTTP403，未获得完整job日志；gh本地缺失，不据此猜测其他步骤成功。原HTTP／run／jobs与HTML分别保存在ignored验收目录。

独立调查确认原fixture在beta真实通知后立即写marker，而六个并发operation并无writer／alpha先到约束；原测试立即读取另两个marker，存在不受产品合同保证的顺序假设。这解释一个可达测试竞态，尚不单凭HTML认证实际失败的全部原因。已委托在精确1b8的隔离候选先复现该合法交错，再让fixture于beta真实通知前确认两个阻塞边界，保留原并发证明；产品、原reaper和原发布均不改写。修复、适用安装回归、新独立审查及自己的CI另验，后继发布继续受原门禁约束。
