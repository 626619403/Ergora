# c1b2a：独立训练cycle服务逐步交付

日期：2026-11-16。按[已审r2具体合同](../plans/2026-11-15-training-cycle-service-boundary.md)与[独立设计审计](2026-11-15-training-cycle-service-design-audit.md)推进。产品代码仍在隔离分支`feat/training-cycle-service`，主开发分支当前已发布478c988；服务固定候选af176cf本地验收及最终两轴已闭合，导入与发布仍待；下文保留各阶段原记录。

设计以c1b1 d5b5891为产品前置，独立通过后固定b719353；实施候选797da567f8b282b4884fceafe16c3efba506f493已在本地固定，再真实合入6725得到`fef7d98e30d5625e5ce37dc45e14904f76447775`。自动merge保留了新BR资源与CI fixture修正；尚未向主开发分支导入本片产品。

四个原owner改动：`reference`／`services`提供独立命令、配置和70秒关闭观察；`reference_training_worker`／`training_execution_protocol`提供四实际活动、可信SDK来源／receipt前run认证、原S-H／一次窗口、仅ordinal0新start、完整原件引用与unknown／容量、双queue各一槽及关闭接线。原283参考、原budget queue／8槽及旧直接接口保持；正式总Workflow／sandbox、execution／collect、接受／后继门槛仍后接。

源码子任务原验证分别见[活动记录](2026-11-16-training-cycle-activity-implementation.md)与[管理接线](2026-11-16-training-cycle-service-wiring.md)：原22回归、新SDK7组及若干精准接缝、services19通过／1平台skip等，各轮有重叠，不相加冒称全库。来源篡改新测试两次断言失败保留，最终按实际H层级及start计数修正；没有为这些断言改变产品。它们不代替联合新安装或真实Temporal。

已在home持久目录准备全新CPU验收stack及本地git项目`cycle-service-acceptance`，注册revision1且发布一致；仅复用既有native依赖、Temporal1.9.1／Server1.32.0，不装系统包、不改共享环境、不覆盖用户命令。准备时没有服务／实验／授权／预算根。原件在项目ignored `training-cycle-service-acceptance/preparation-r1/`；后续运行前仍需核7233可用。具体本机目录仅留私有原件。

合并候选的新包已完成：core／SDK各663产品文件source＝wheel＝site（含执行位），仅前述四原owner变化，283参考／依赖保持；core无SDK，SDK1.34.0。wheel SHA256为`b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`。178测试／示例在build前冻结，原件在ignored `training-cycle-service-acceptance/package-r1/`。

安装接缝实际collect68项／216可见项，最终67 passed／1平台skip／148 deselected，531.82秒，完整命令／输出／JUnit保存`installed-tests-r1/`，见[安装记录](2026-11-16-training-cycle-service-installed-checks.md)。另一真实core subprocess已经核SDK不存在、services.status可读，启动cycle服务明确拒绝且前后status相同，没有服务被启动。

真实r1已启动Temporal、budget与cycle三个独立PID，并以标准SDK sandbox中的最小测试Workflow完成四活动的真实normal／stop queue路由和非法输入非重试拒绝。测试Workflow已经COMPLETED；记录history时曾误用不存在的to_proto方法导致记录脚本失败，原输出保留，后续仅只读恢复同一run的完整history／结果，没有重投活动。此用例不是正式总Workflow或有效业务cycle。随后明确停止两个空闲worker，确认OS终态；本地Temporal仍保留供修后验收。两份CPU候选通过真实baseline／runner／experiment预览准备，尚未授权或执行。

新fresh reviewer的[源码两轴审查](2026-11-16-training-cycle-service-product-review.md)已收：需求request changes／4开放，可维护性独立0开放。R1实际SDK验证失败后shutdown可能永久等；R2需用on_fatal_error及时触发normal-first关闭；R3父侧Popen／transfer／cleanup事实丢失；R4部分typed容量降格unknown。高强度子任务正在原owner修正。旧包安装／路由结果保持其原范围，修后必须新身份定向复验。

R1–R4已在原worker及读取owner修正，详见[逐项修正](2026-11-16-training-cycle-service-review-fixes.md)。为精确区分stdout容量，原ValueError子类移入training_cycles并由worker复用；因此相对主线的产品差异为五个原owner，没有新模块或第二reader。源码反例和修后11／最终14项保留各自范围及重叠。修正本地固定72939f3，再真实合入已发布478c988，准确服务候选为`eedba08c8c112683a7946726aab3f4fd590f26d6`。原独立reviewer已核源码身份、修正与SDK生命周期四场景，R1–R4源码关闭，两轴approve／开放0；整体验收仍pending。

修后package-r2 core／SDK各663文件source＝wheel＝site及执行位同一，283参考／依赖保持；core无SDK、SDK1.34.0。新wheel SHA256为`747e221b584fa71518e2b64ce69fcace2eb4ef1340450cfd50e6f47e8729e017`，178测试／示例在build前重新冻结。定向安装实际collect20项，包含四生命周期、新父侧完整事实、容量及原SDK来源／66refs／重投等，目前运行中。

[真实新包业务](2026-11-16-training-cycle-service-live-acceptance.md)已完成首个正常场景：显式关闭旧daemon后由新包原命令重建，独立budget／cycle服务；原producer prepare／submit、默认sandbox的测试TrainingCycleWorkflow最先inspect、ordinal1明确非重试拒绝、ordinal0实际prepare／confirm／dispatch、重复start只对账且原attempt bytes保持、显式reconcile、stop全部六分支ref逐个raw SHA与bytes相符。controller已COMPLETED，实际预算根被原stop／reaper回收并保留fenced终态；生成了原native job，没有执行器运行。它仍是服务夹具，不能称正式总Workflow或训练验收。

自身原结构模板正在用修后SDK包及完整源文件发起Claude Code审查；本机实际auth status已可用，模型调用结果尚未定。不把登录或调用发出当审查通过。

## 修后安装与现场验收收尾

上述进度为各阶段原记录。当前主开发树仍是`478c98891522930817fa7005a8ac96e408f37230`；服务产品位于隔离树`eedba08c8c112683a7946726aab3f4fd590f26d6`，尚未导入／发布。手册与架构服务入口的文档改动也尚未提交。

新包定向安装最终 **20 passed／155.47秒**；无SDK的真实S-H只读inspect通过，9份cycle原件、业务DB与原窗口保持，详见[安装r2记录](2026-11-16-training-cycle-service-installed-checks.md)。[真实服务验收](2026-11-16-training-cycle-service-live-acceptance.md)已收尾：四活动、缺receipt真实竞态、实际SDK attempt2只对账、normal存储阻塞时独立stop、交接根跨原命令停止／重启、TERM／INT／重复取消／fatal与受控强杀均分别记账。核144个进程身份无业务残留、73份stdout引用字节／SHA相符、3个预算根退出并留final；全部自建Workflow终态、daemon停止且7233／8233无监听。现场N=2，未跑真实SDK 32候选fanout、未交接根故障或执行器／训练，不把测试清理terminate当作业务停止。

## 自身模板审查与新增容量疑点

以修后安装SDK包调用原`refactoring-quality`／`ergora-structure-review@1.0.0`模板，完整23文件726356字节，三份继承资源与完整任务实际进入stdin（834602字节）。Claude Code有登录但实际调用420.60秒后退出1，未取得审查结论；失败原件保持。按用户预先授权回退Codex，真实调用95.84秒、run=`35453ca57bc64d2299a7fc132f22cde0`、input digest=`9de759c3529174e4c3e96d765c3b6d461c7633bdedcd7c8307066083e2aa518e`，结果为request-changes；不能称异后端审查通过。

Codex指出原`BudgetedStart.launch_context`的完整launch材料超32KiB时仍抛普通ValueError，可能在H降格为unknown。它与R1–R4原源码复核分开记为新增疑点；正在原owner核真实可达性、反例与最小修正，详见[launch容量专项](2026-11-16-training-cycle-launch-capacity.md)。完整原回复／scope／stdin／后端命令位于ignored验收目录`self-review-r2-*`，没有将密钥或本机路径写入公开报告。

该疑点已由真实合法注册大项目复现并最小修正，见[专项交付](2026-11-16-training-cycle-launch-capacity.md)：原反例1 failed／22.31秒，修后9 passed／114.79秒；原intent占位、重复／重投只对账与普通ValueError保持。隔离候选已固定`97a0bbfae9687c15927f1437a374cd070baf0a94`，相对eedba08只有两个既有产品owner与一个测试变化；相对发布478产品为六个原owner。新package-r3正在独立重建，新的fresh最终审查与自身模板复核接续，源码／新安装／现场历史分开记账。

下一步：取得新包及适用定向复验、最终独立两轴与自身模板复核，再导入主开发树、普通推送及准确CI。旧包20项与现场结果保持原范围，不自动转给新源码；尚不称服务片闭合、自动循环或真实训练收益通过。

## r3当前终核

新包081aab45已完成双环境663文件／执行位、283参考与依赖核对。新的[fresh终审](2026-11-16-training-cycle-service-final-review.md)已独立核完整源差异与实际安装文件，源码需求／维护性两轴approve／开放0，另5项无业务资源短探针通过；整体验收仍pending。自身原结构模板r3真实Codex68.458秒approve：24完整文件736157字节、三份资源与完整任务实际进入850834字节stdin，run=`dfd8172c3ba642f09e908df011d4a7c5`、input digest=`0212b8aff2d52c5debae2dbd8026edebe3ab9b18c7692eda52cefc82d0691249`；该结论只认证supplied source，不认证现场或CI。

r3安装原9项初跑8通过／1失败，失败是正常场景7秒窗口实际耗尽，父侧unknown正确保留；原件完整保持。按独立复核只改该正常测试的显式control=30，新冻结单项1通过／21.58秒，SDK-free真实S-H读核／9原件／DB／窗口保持通过；共用fixture默认、产品超时gate、故障预算与所有断言未改。该一行修订固定`af176cf6e79adb9c6ef6f32946672bc77cdb89de`，产品与97a0bbf／wheel081aab45逐字同一，详见[安装r3记录](2026-11-16-training-cycle-service-installed-checks.md)。

新包[现场r3](2026-11-16-training-cycle-service-live-acceptance.md#r3launch-guard-容量分类修正后的定向实测)已完成：N2正常与N32实际SDK的66完整分支（含metadata19,354字节）通过，无裁剪／扩限。140个记录身份无业务残留、84活动refs＋4producer refs核实，全部自建Workflow原COMPLETED、唯一start预算根退出留final；Temporal／daemon／监听均停止。r2信号／fatal／阻塞等只保持其原候选范围，没有重记为r3实测。当前等原fresh reviewer复核最终原件及固定身份，再导入主开发树、普通发布／准确CI。


## 本地服务片闭合

[最终独立审查](2026-11-16-training-cycle-service-final-review.md)已复核r3b实际history、完整未发送日志封套、134真实refs及274记录身份：两轴approve／开放0，允许固定af176cf6导入。N32短原因场景为65refs＋1完整inline unknown（19,510字节）；长原因场景实际input493字节、完整聚合39,518字节，真实SDK非重试容量拒绝，20,066字节原因完整保留，全部已创建peer仍收尾。两场只在私有harness注入constructor故障，不冒称OS syscall故障；原授权／输入不变，controller原COMPLETED，daemon／端口停止。

本地c1b2a服务边界验收闭合；原r2信号／fatal／强杀、r3正常／全refs及r3b注入各自保持源码与方法范围。Supervisor等待70秒后强杀、正式总Workflow／执行消费者／接受后继／真实训练仍非本片结论。下一步固定真实导入身份与普通发布，CI测试重分组及后继c1b2b分别记录。
