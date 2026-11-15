# c1a2：总投递与固定运行对账逐步交付

日期：2026-11-15。基线 `836179e9ff3eae0795f0c22bf4c58f0bab1ea777`，分支refactor/architecture-foundations。恢复时工作树干净，原c1a1及c1b0本地门禁闭合；[具体计划](../plans/2026-11-15-training-cycle-dispatch.md)在原S-H与owner上接总SDK投递和对账，kernel专家保留v3。

只读重核 `CycleAdmission`／原 `bind`、`training_cycles`短事务／无覆盖publisher、`lookup_controller`固定RUNNING gate、实际worker四task／H／reaper、选定native environment及既有测试fixture。真实SDK 1.34.0原编码probe的start handle.run_id为null，result_run_id才是准确启动run；原记录保持，不当作真实投递验收。

正在补真实Temporal元数据观察，以明确原单次run、continue／retry／reset等后继链身份在当前服务的实际字段；使用独立本地probe，无业务训练或业务仓库修改。当前只有计划，没有后继产品、子实验、服务或Workflow实现结论。下一步固定具体设计并交新的独立审查，再实施／安装／自身模板和产品终核。

## 真实SDK／服务metadata观察

沿已有CLI启动独立端口／持久DB的本地Server 1.32.0，只注册无业务副作用的metadata probe Workflow。r1最后的进程身份记录错误地把已退出进程的FileNotFoundError继续抛出，退出1、没有结果JSON；原脚本／日志和失败身份保留，不能当probe成功。r2只修probe收尾记录，实际4.977秒／驱动6.324秒、退出0，原server身份活匹配false且正常退出，未修改产品。

`sdk-history-metadata-r2.json`实际记录普通初始run、同ID人工ALLOW_DUPLICATE、continue-as-new与retry。启动result_run_id为准确首run；continue／retry的describe.first_run_id保留原首run，后继started带continued_execution_run_id／initiator，而固定首run仍可读取关闭历史。人工复用则重开first_run_id且同input，证明最新单份metadata不能排除人为完整重放；已把独占协议ID这一恢复前提与已知歧义明确写入具体计划。不以这些字段声称能检测一切人工复用。

私有probe SHA256 `53076829558e77f17fbf18366371e5d855f431993eec56732a8fd5d6083cdc24`，原命令／stdout／stderr、独立DB和server日志保持；CLI 1.9.1／SDK 1.34.0。终止probe时一条原SDK workflow-task-not-found warning保留，全部原case仍正常结束。此项只认证实际metadata，不是Ergora总Workflow、取消恢复、业务训练或性能验收。下一步独立核具体设计，不先开放子实验派发。

独立设计初审发现R1：无attempt时发出的lookup可能晚于另一合法请求claim／start返回，若直接写preexisting拒绝，会永久阻断其receipt。已把最小修正写入计划：拒绝和claim共用短reservation，进入后重读全部原件；attempt一旦出现，旧lookup只转对账、不写拒绝。receipt与拒绝也在同一reservation中核互斥，无RPC持事务。具体reason／run及attempt关系已固定，产品尚未实施；设计复审待。

独立r2设计复审需求／维护性两轴approve／开放0／0，R1只在设计层关闭；报告9,950B／SHA256 `5bd641d5753fa742b35bc4216676542068d3542b84d63cd95d3e269469c0152c`。开始原四owner实施：protocol共用原件生成／完整验证与新增两mode窗口；cycles持短claim／互斥终态发布；runtime提取完整history验证但原RUNNING gate保持；worker只在H装载选定native环境及SDK投递／对账。复用原服务替身和operation fixture，初选源码验证即将运行。尚无安装／自身模板／产品独立结论；SDK替身不代表实际总Workflow或训练。

源码r1在途，当前观察新增S-H fixture使用-P时未把自身目录加入sys.path，无法导入同目录服务替身；失败属于fixture，产品尚未经过这些新case。保持原输入等待终态后最小修正，不把部分结果或后续源码归回r1。远端877e1e4的原官方run仍无终态结论；11:58 UTC查询403／remaining0，reset 12:23:14 UTC，原件保存，限额前不重复查。后继普通推送继续等待其准确CI／原独立终核。

源码r1终态11失败／40通过，驱动129.684秒，前后身份同一；只修fixture自身导入后，r2新增接缝17通过／125.59秒（驱动126.522秒）。原r1失败与r2候选分别保留；r2不认证后续修正。新的独立产品初审R1发现reset恢复丢失latest身份，真实reset探针4.580秒证实first_run_id／原started不变，server正常退出且原身份活匹配false；R2指出SDK等待期间原授权变更时终态publisher只用缓存授权。按真实reset形状和原授权损坏补两项接缝，在修前source-r3-red两项实红／13.27秒，保留原件。

现已在原runtime最小收窄：无receipt时latest与first不一致一律unknown，CAN／retry也不接管；原receipt仍只观固定run，RUNNING gate不变。原cycles终态publisher在同reservation重新_load完整plan／authorization／ready并核原SHA，允许stop／expired的纯观察，不重新授执行权。source-r4受影响十项正在运行，新core／SDK非editable包开始构建；自身模板和独立修正终核仍待。

修后source-r4为9通过／1测试观察失败，驱动68.404秒；两原finding对应项已实绿。耗尽后对账测试在2秒控制窗口内H已持久保存attempt／服务请求并返回unknown，但父侧过期拒收其帧，测试错误地要求该响应还带attempt_saved。已改为核实际原件／请求，并在给定有效5秒控制／10秒总窗口下等待原total耗尽；不改产品或重开clock。原失败保留。新core／SDK各652源码／wheel／site逐字同一、283参考PASS及依赖检查通过，最终178输入副本已冻结；实际安装回归及自身原结构模板开始运行。

当前自身原结构模板真实Codex65.884秒approve，18份完整供稿452,851B及3份祖先资源进入原stdin，仅认证其供稿范围。新core实际异步cold inspect1.158秒通过，SDK缺席，父State／SQLite／原件reader禁止；原7文件bytes与DB dump保持（该probe未记录前后inode，不作其inode通过主张）。独立reviewer已读R1／R2最小修正与原实红／修后对应实绿，最终安装终态／完整scope及收尾仍待。下一片SDK sandbox／独立worker边界只作只读研究，不先开放自动派发。

最终安装r1终态67通过／347.05秒（驱动348.193秒），JUnit／stdout／退出码一致；覆盖原runtime／四gate／停止／release／架构和新增投递接缝。独立reviewer已核R1／R2源码修正关闭、开放finding0。自查另发现bind末尾rejected分支已被共享原件互斥与前置result_saved检查完全覆盖，原独立reviewer确认不可达；按其意见只删两行，不增浅测。原67项和自身供稿保持原产品身份；新r2两安装重建后只跑受影响原bind／SDK接缝与收尾，不把原结果改标成新包。

## 最终候选r2验证与收尾

新core／SDK非editable安装各652文件与源码／wheel逐字同一，283冻结参考及依赖检查通过。`guard-removal-final-r1.json`精确核实r1→r2唯一产品变化是protocol中两行不可达guard删除，其余651产品文件不变。`installed-r2`的原bind（含隔离native解释器）、固定RUNNING gate、四类冲突与真实late-lookup并发／独立SQLite writer共7项通过／83.56秒，驱动84.620秒／退出0；原r1的67项保留r1身份，不改称r2全套通过。

`core-inspect-r2`实际异步调用1.210秒，SDK缺席，禁止父State／SQLite／原件reader，原7文件bytes、DB dump与窗口保持；未记录inode，不能用它声称inode验证。自身原结构模板r2真实Codex40.251秒approve，18份完整正文458,285B与3份祖先资源核实进入真实stdin；原结果SHA256为`3e65ff503fc291128b226a884e43e60ed68b7fb919ab326f611aac20a6759762`，只认证该完整供稿范围，不是异后端或外部CI结论。

`integrity-cleanup-r1`退出0：当前源码与r2双安装652份保持同一、178份最终测试输入仍同一；从所有源码／安装运行及metadata probe原件取得的74个已知actor身份，活匹配0。原失败、修前实红、旧包与新包结果分别保留。最终本地两轴仍待原独立产品reviewer核当前完整scope、精准回归及收尾；固定提交和逐片普通发布另记录，不把后继只读SDK研究混入本片。

原独立产品reviewer已对最终r3 scope全部12文件、r2源码／wheel／双安装652、178输入、67旧r1／7新r2的JUnit／stdout／退出码、自身完整供稿及74原actor再次活匹配0直接终核；需求／维护性两轴最终本地approve／开放0／0，R1／R2关闭且原失败保持。[报告](2026-11-15-training-cycle-dispatch-review.md)15,833B／SHA256 `ceb7c13026cc0207a2de6bc0ac8ec09c5900fff59ddfa3b8c67897046a0eec57`。本片本地门禁闭合；接续固定提交，远端仍按原准确CI队列逐片普通发布。后继SDK研究与原b2b0 CI终核文档不属于本片提交。
