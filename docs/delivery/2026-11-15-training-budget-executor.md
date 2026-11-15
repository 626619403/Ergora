# Q4.2b3 训练预算与实际执行停止：交付记录

日期：2026-11-15。[具体计划](../plans/2026-11-15-training-budget-executor.md)r2处于实施前合同复核，未改本片产品、测试、schema或283参考。前置b2仍在最终独立验收；本片实施前固定其实际发布Git身份，不把b1／b2 CI转授后继。

已只读追踪原`reference_budget → task lifecycle`及`training start → native request → training_executor.process → Sandbox → process_job → runner`。原executor覆盖Git两臂准备、runner、archive和MLflow tracking；Sandbox及runner各自新session，仅杀外层进程组会漏真实后代。`processes.run(supervised=True)`有专用driver／subreaper回收，但不按timeout参数自行截止，须实际stop predicate。六阶段task scope／slots不是训练循环授权。这些是源码观察，未运行训练或作停止主张。

计划分为授权／原期限、提交slot／晚到边界、专用executor／真实后代和安装交付，逐片验收；SIGKILL／跨boot／缺原件保留unknown，不请求宿主权限或扩大已接受容器边界。下一步为新的fresh-context独立计划两轴审查，明确字段与可验收接缝后再实施。Kernel专家继续保留在v3提案路径。

[新fresh-context r1评审](2026-11-15-training-budget-executor-plan-review.md)需求request-changes／开放2，维护request-changes／开放1。R1的首RPC至queued／executor交接缺连续owner、R2的首次live admissions与原时钟顺序不明均有真实可达调用依据，接受。计划r2明确同授权独立owner在首attempt前启动并持续监管RPC／queued／交接，deadline自动原fence，不等后继c；其验收包含CLI先返回、native create延后以及held RPC跨截止。原授权时钟先于全部昂贵live检查，pending不授执行权，同ID中断／lost-ack不续期，全部检查与完成fsync耗时计入；另固定完整原输入、授权和ready记录的SHA／字节界。当前待原reviewer复核，未开始产品实现。

同reviewer已核最终r2两轴approve／开放0／0，R1–R2关闭；明确原手工submitted fence限制及原adapter／registry lock应用扩展接缝，手工权限保持。固定计划17942B／SHA`831127e9aa6a5aad5d0f6fdc65f7cd3e4abf9f16c74203a4eb4d0233b81fe227`和原delivery／review保存在本片ignored检查目录，后续仅同步进度。产品未改，计划通过不等于预算／进程／循环运行通过；实施前须固定b2实际发布Git身份。

## B3.1实施启动

基线已固定为b2普通发布`9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`，原reviewer已核固定发布两轴approve／开放0／0；其自己的CI43655794070在途，闭合前不推后继产品。本地先沿原`training_cycles`实现授权／状态两入口及同ID原时钟恢复，纯stdlib时钟提取有原task／新训练两个真实消费者。字段、持久位置、reader／writer容量、无覆盖fsync顺序、当前项目漂移和检查范围已补在具体计划。此段为实施启动，不表示测试／安装／模型审查或训练已通过。Kernel专家保持在v3路径，不改其定义。

## B3.1源码候选r1

四产品文件：原`training_cycles`保存／核本地授权与ready，CLI新增两入口；从原`reference_budget`提取共同`budget_clock`，只有原task与训练两个生产消费者，不搬scope／slots。原`test_training_submission`补七个场景（四deadline边界加完整CLI／部分恢复并发／持久来源损坏），无新suite／CI job、schema或表，283参考保持。`source-scope-r1/`及其JSON／完整diff固定四产品和原测试，包括新clock完整内容。

首轮源码七场景通过，pytest24.71秒／外层26.198秒；此候选随后补父目录fsync和同原记录的跨boot／倒退时钟观察，后继将由新安装验证，不把首轮转授。原task budget／submission两suite正在源码运行，结果未定。一次检查驱动的`--help`误用在创建测试进程前失败，只生成空日志；已读驱动并记录，未算作测试。尚未做本片安装、实际CLI进程旅程、自身模板或新fresh-context独立产品审查，不作训练／停止／自动循环主张。

## 独立r1发现与修正候选r2

[新fresh-context产品r1审查](2026-11-15-training-cycle-authorization-review.md)需求request-changes／开放2，维护approve／开放0。接受R1：临时目录在首次授权完成文件fsync后、目录发布前中断会清掉原时钟；接受R2：ready link在父目录fsync前被并发状态读成完成。两条均用r1真实非editable安装实红：首次发布中断1 failed／2.87秒，ready-directory-fsync1 failed／3.94秒，原stdout／XML保留，不记后继通过。

r2沿原cycle锁先保留正式ID目录，fsync父层后先写原授权，再无覆盖保存完整输入；异常不清理目录或已发布原件。缺原授权／输入时明确失败，不新时钟或补造。状态在原锁忙时以原期限报告pending／exhausted，不等待检查，不把尚未完成写盘的ready当完成。仅提取本owner私有bytes writer供原输入与元数据两处，保留各自容量及canonical／原bytesSHA。`source-scope-r2/`固定四产品与同原测试，九新场景；原schema／表／283参考保持。新的core／SDK非editable安装正在构建，SDK加原task-mcp extra以实际覆盖首轮因缺mcp跳过的三项；尚未取得最终通过或关闭独立findings。

## r2安装与在途验收

新wheel SHA`0a71da8bbbf0f768c2fab09ce98adc10978f8a4e8296e79044c6c5c4a3e5713b`；core／SDK两套各646份源码／wheel／真实site-packages逐字一致，283参考PASS、两份依赖检查通过。core确无Temporal SDK，SDK为1.34.0并含既有task-mcp extra。相对固定基线只增加`budget_clock.py`、修改原三产品（CLI／task budget／training cycles），无参考或preset变化。原三suite完整测试与39份原测试／fixture固定副本逐字绑定（索引SHA`ec33ba9b9ff84e2f335d74f39300cf86c7aca860add5d9fd60f103a45dbcdcda`）已在r2非editable SDK安装运行，结果未定。另启动实际core／SDK CLI的原生准备→有限输入→授权→删外部源后原恢复→耗尽与项目漂移旅程，暂不记通过。

## R2异常分支与r4候选

同reviewer复核指出r2只处理active publisher，ready link后父目录fsync抛错、释放锁再读仍会被误判完成。接受并沿同一原场景补实红：r2安装1 failed／3.81秒，保留stdout／XML。r3将同一可见ready的恢复置于原锁内，flush原目录失败为unknown，成功后再核原期限；不改任何原bytes／checked_at／clock，不另建ack或状态表。reviewer进一步要求耗时flush后重核原来源，r4复用原_load重读完整来源／记录，固定原authorization SHA，再观察当前项目／期限。该来源丢失分支在r3安装上运行实红，结果另按原JSON／XML记录，不能把r3安装当最终。

r4固定四产品／原测试在source-scope-r4；十新场景，仍只有原test_training_submission suite。新非editable r4 core／SDK构建中。r2完整原三suite仍在途；r2的实际CLI旅程已完成13个实际命令，外层24.847秒，50原生／注册文件及原数据库保持，仅明确的后续memory binding改变项目revision。原输入删外部目录后原授权／ready保持，短预算恢复耗尽、当前项目变化分别观察；没有workflow、模型或runner调用。r4须独立验证自己的影响范围和同批原件，不能继承r2对异常分支的认证。

## 安装r2完整回归的夹具遗漏

原r2固定三suite运行终态为49 passed／15 errors，pytest321.86秒。49项属于完整原training_submission；15错误均在原task budget／submission的fixture setup，验证快照漏复制`EXAMPLES=Path(__file__).parents[1]/examples`读取的agents／composition数据，尚未进入这些测试的产品调用。保留原stdout／XML／固定39文件，不记全通过、不改产品fallback／测试断言。已只修验证快照：原39文件加逐字／执行位保持的真实tracked examples，另存`installed-clock-r4-scope`与完整索引，直接用最终r4安装重跑原task两suite，不重复已验的r2 training_submission。r4自身受影响的全部cycle场景单独运行，不能把两个候选相加成一次完整通过。

## B3.1最终本地r4证据

最终四产品／原测试固定`source-scope-r4/`，manifest SHA`dfcca3cacf2c56145e68d2392b7deec5cd418d3caa326dc10575956ea62dbee4`，完整diff SHA`92d04a323ddb2e6d6b8f68971524e900e0e0037f219227da0294c47bebcb7cf5`。wheel SHA`c986db854e90bb77c5f4c94ff5ecbc9b72aa526fad9852ae632c61ad2f88bd1d`；core／SDK各646份源码／wheel／实际site-packages逐字，283参考PASS、两依赖通过，core无SDK，SDK1.34.0含原task-mcp。

- `installed-tests-r4`：最终安装沿原test_training_submission全部cycle相关16项通过，零失败／错误／跳过；pytest56.85秒、XML56.844秒、外层57.686秒。固定39原测试／fixture索引SHA`98a45897e10e87a6fe5b901dcc31ae5637db72b1335f7b7893167ac771589da9`；覆盖R1及R2活跃／目录失败／postflush来源丢失三接缝、首个／后续检查和文件／目录fsync耗尽、并发同ID／部分恢复／原来源／普通文件等。
- `installed-clock-r4`：修正验证数据目录后，最终安装跑原task budget／submission两suite15项全通过，零失败／错误／跳过；pytest138.20秒、XML138.195秒、外层139.384秒。83份原测试／fixture／真实examples逐字及执行位保持，索引SHA`41c851832d65c7eed980cdbfb2f4c65266ef9c06e221240daecf12306bc9a6d2`。没有产品fallback或新增suite／CI。原r2的49通过／15 setup错误属于原候选，不能相加成一次完整最终通过，也不称r4重跑原三suite。
- `native-journey-r4`：最终安装实际13条CLI，外层24.947秒；原生准备→完整双候选→确认前拒绝→授权→删外部源原恢复→SHA冲突拒绝→短时钟耗尽／同ID不续期→明确项目binding变动后的只读不可继续。50原生／注册文件及SQLite保持，唯一DB变化为明确的memory binding；无SDK core可用，credentials故意无效且未读取。
- `native-readback-r4`：最终core安装另四个实际CLI重读同批r2／r4原授权及短预算，2.620秒。两case各完整373文件inventory和SQLite dump逐字保持，原SHA／时钟／ready不变，不重授／补输入。
- 自身原`ergora-structure-review@1.0.0`，通过`refactoring-quality`安装并调用：run`0e508f3c8b58423b9960cb84ef14821a`，46.167秒succeeded／approve，外层48.825秒。25完整文件591938B／完整diff及三份祖先资源全部进入真实stdin；input digest`a12057161b75681499073d047524088fca338e61b65a7d223ef791c3db4292b3`，result SHA`7231af03e1548ffa33d005f081882222b30838ebdb2000b58b1b61870745605a`。用户授权Codex回退，无异后端成功主张；仅审所给完整源码文本，不认证未见私有原件或未来CI。

[新fresh-context原reviewer](2026-11-15-training-cycle-authorization-review.md)已核r4源码两轴approve／开放0／0；R1／R2运行关闭及整片最终本地结论待上述原件终核。真实Temporal、训练／GPU／质量／收益、派发slot、连续owner及OS／后代停止均未验。B3.1只交付本地授权／准入，不关闭B3.2／3或Q4.2c／d。普通发布与自己的CI也尚待，不能转授b2。

新fresh-context原reviewer已直接终核上述固定r4原件，需求／维护最终本地均approve／开放0／0，R1／R2关闭。实际17个CLI是13全旅程加4同原件只读，非17轮训练；r2的49/15夹具错误历史、r4的16+15各自范围及源码／wheel／安装身份均保持。结论只认证B3.1本地，不认证发布／CI或后继步骤。

前置b2自己的CI出现一个Windows测试平台标记遗漏，单独修复且不带本片产品。当前共享原test_training_submission因此另加该原测试的Linux skip，四产品及十新场景相对固定r4不变；该标记在b2原最终安装单独核Linux1通过，Windows以修复提交自己的CI为准。最终B3.1发布前会核此唯一机械差异，不为该标记重建未改产品／重跑模型或已验cycle。

平台修正已单独普通发布`82ea3f163e0c29759eb6ebef93fb2e58d87e983a`，parent为上述产品实施基线9c9ffee；独立已核四blob／完整远端Ref和645产品tree不变，自己的CI43658729462在途。B3.1保持固定r4产品与验收，仅准备本地提交以便后继工作使用明确基线；前置修复自己的CI闭合前不推送B3.1。后继产品的本地实施不改变这些固定源码／wheel／证据身份。
