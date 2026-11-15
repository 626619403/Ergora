# B3.2 原训练提交与连续截止责任：交付记录

日期：2026-11-15。[具体设计](../plans/2026-11-15-training-budget-submission.md)r3已独立通过；当前r4已完成安装／受影响回归、真实控制流程、自身模板及最终独立产品两轴核验，发布／自己的CI待结算。下列初始与中间记录保留当时状态，最新结果见末节。原B3.0合同和B3.1本地授权验收见[前置记录](2026-11-15-training-budget-executor.md)，不能替代本片证据。

## 初始设计记录

本地产品基线`b53bba613a3c02b14c69a6df9b0d526755d7e216`，parent为单marker修复`82ea3f163e0c29759eb6ebef93fb2e58d87e983a`；前置修复自己的CI43658729462在途，B3.1本地提交尚未推送。当前未实现B3.2代码。具体设计r1原件保存在本片ignored `plan-r1.md`和`plan-r1.json`，明确原intent持有预算引用、原attempt即不可归还slot，以及独立owner与原fence／取消接缝；不新建slot表或start客户端。

新fresh-context审查者正在只读核真实调用链与设计，尤其检查accepted调用已返回／held RPC时的自动fence、原来源缺损／owner失联、锁顺序、已完成轮保留和cleanup。源码、安装、服务替身、真实服务及OS停止均无本片新验收；Kernel专家继续保留在v3路径。

## 设计r1审查与r2修订

[独立r1设计审查](2026-11-15-training-budget-submission-plan-review.md)需求request-changes／3、维护request-changes／1。接受R1：owner失联／跨boot且尚未fence时，已accepted的原workflow仍可由旧adapter迟到创建；接受R2：同步source／DB／gate／registry锁阻塞会使监管本身失去截止处理；接受R3：原native writer只fsync文件，adapter返回不等于fence目录项已持久完成。原设计／报告／28文件只读索引保持，没有通过测试来掩盖设计缺口。

r2明确budgeted starts的应用版本queue及真实managed adapter的最终create gate，旧queue／无预算不变；监督owner把可阻塞动作放专用子进程，以同原clock实际stop predicate约束compute／cleanup；完成原fence目录与必要父层fsync并重核完整binding后才保存持久完成，失败保留unknown。原intent＋原attempt继续是唯一绑定／slot权威，不改283参考。固定r2原件在ignored `plan-r2.md/json`；等待同reviewer复核，当前仍无B3.2产品变化。

实施准备进一步核到native SDK锁定环境缺jsonschema，而完整预算reader依赖该包。r3据此保留旧training-worker／原queue和native Python，新增可选training-budget-worker／版本queue，使用安装Ergora及temporal extra的应用Python；缺SDK明确失败，不修改原lock或拼接其他环境。services本域复用原Supervisor设置生成独立program，不影响旧服务选择。r2未先行记通过，原件保持；固定r3已送同reviewer一并续核。

## B3.2a设计通过／实施启动

同reviewer已直接终核固定r3两轴approve／开放0／0，R1–R3仅在设计层面关闭。r2／r3及源码身份、worker依赖和16本地链接均已核；未运行产品。开始沿原submission、budget应用owner与可选managed worker实现，不改原workflow／实验／批准算法和283参考。helper不继承owner／submission锁，元数据及fence各自完成目录同步；运行findings与实际结果将单独记录，不继承设计通过。

## 实施中：原提交与首次真实owner检查

基线已普通发布为上述b53bba6，前置82ea自己的CI及原审查已通过；b53自己的CI另有边界测试声明遗漏，单独修正后才允许推送后继。八个在途产品（含预算owner／worker两个新模块）已接入原intent的可选budget、原attempt目录同步、版本queue和managed service。源码首个场景`source-start-r1`为1 passed／19.92秒，驱动20.892秒：真实独立owner在提交返回后自动fence，原SDK服务替身仅接受一次start，迟到native create被拒，原slot与授权bytes保持。原scope／XML／stdout留在ignored本片目录。只有这一个场景已验，完整失败矩阵、真实worker注册、非editable安装、自身模板和新独立产品审查仍待。实际executor停止保持未知。

## 源码r2八场景与r3接缝

`source-budget-r2`：原suite八项通过／153.91秒，驱动154.863秒，原scope／stdout／XML保持。覆盖accepted返回后自动fence、held-start跨截止且不等submission锁、活owner的managed create、异cycle拒绝、owner真实SIGKILL且无fence时managed create拒绝、阻塞monitor、fence目录fsync失败／阻塞的unknown和同原fence恢复、registry锁耗尽cleanup。全部使用真实独立owner／helper／原文件锁和native adapter，Temporal由SDK服务替身提供；没有executor／训练。

r3把完整已核缓存摘要加入原owner身份，防止helper的policy／published context脱离该原owner；进程入口和adapter移到worker边界避免循环import，owner不反向依赖提交／取消模块。已在原suite补lost-ack与原授权丢失后的只对账、不重发；真实bootstrap接线和原Supervisor配置复用原reference／services测试。r3源码运行和core／SDK非editable安装在途，尚不把r2通过转授为r3全部通过。

## r3安装、测试输入修正与真实服务准备

r3 core／SDK两安装各648份源码／wheel／site-packages逐字相同，原283参考PASS，两套依赖检查通过。源码r3原运行9 passed／2 failed／178.43秒：lost-ack测试错误地要求独立owner尚未对账（实际owner先对账为submitted，且自然退出导致清理kill已退出PID）；worker注册测试错误地把adapter的fence方法当作activity名。均只修验证预期／清理：允许同原run已被owner对账，保留原slot不重发，检查实际原cancel_exact_job注册。最终r3安装上受影响2项通过／25.72秒，产品未变，原两失败保留。

完整五suite已从173份逐字测试／fixture／examples快照运行于r3 SDK非editable安装，当前在途，不能记全通过。真实本地Temporal旅程前两次在服务启动前失败，分别漏准备原supervisor.d和platform.json，原stdout／stderr保存；改用原initialize构造完整运行前置环境，不改产品或原参考。没有启动未知服务或把这两次准备失败称为产品成功。最终真实服务、进程收尾与自身／新独立产品审查仍待。

## R1：最终记录写盘也须受监督

自身原`ergora-structure-review@1.0.0`通过既有refactoring-quality实际调用，r3 run`5214d04f055f44eaa0359094c461c241`：66.340秒succeeded／request-changes，27完整文件533289B＋三祖先资源全部进入真实stdin，input digest`76d63c2c80a191a3a4d9c3ebebd5efdb0a7ab02714f27bd8333cfe9b5853df84`，原result SHA`495a6e56f697a63a06a2807dab06d2645b3a65bae580cba91e9420947fdbb9cc`。原件为`self-review-r3-codex/original-result.json`及review.md；用户授权Codex回退，仅完整源码文本审查，不认证未见原件。模型R1/P2指出own末尾直接_record(final.json)的文件／目录fsync可阻塞owner锁超过cleanup；[新fresh-context产品评审](2026-11-15-training-budget-submission-review.md)独立确认并保持需求request-changes／1。

接受并在原r3安装运行精确故障：`installed-final-publication-red-r3`为1 failed／34.00秒，owner超原cleanup仍活且持锁，测试只杀回已知原owner收尾，原scope／日志／XML保存。r4仅改预算owner：final发布沿同一个受原cleanup clock限制的supervise helper；原owner结束且无final时，观察只flush／核已有同绑定fence，owner状态保持unknown；不新写final／fence／owner或延长时钟。正常完成仍在原剩余预算内保存final。原两类最终fsync故障（link前文件、link后目录）复用原fixture；耗尽cleanup可没有final，原测试改按真实owner／锁结束观察，不假造最终记录。

r4 core／SDK各648文件逐字、283参考与两依赖检查通过。受影响预算／正常completed及原factory接缝15项和新的真实Temporal旅程在途；原r3完整五suite仍保留原候选，不转记最终r4全部通过。r3c真实服务实际自动fence／ack取消已验，但driver在空锁truthiness处失败；同原授权／run／slot的只读恢复第二轮10.430秒通过、30原件保持、无新start／无executor，owned栈及两端口收尾。第一轮恢复未启动matching worker的原query timeout保持，不改产品来隐藏。

## r4实际控制流程与受影响回归

r3完整五suite已结束：111 passed／1 skipped，716.84秒，外层717.901秒；固定173份测试／fixture／examples与原输出保存在`installed-tests-r3-*`。仅归r3安装，不将完整套件结果转授r4。

r4真实Temporal＋真实预算worker旅程`native-journey-r4-execution`以exit0结束，47.4759秒。一个合成unchanged experiment通过原预算queue消费、native queued request、compute截止自动持久fence和原exact-run取消；原授权／slot／native字节保持，实际resume可读，原owner／helper身份均已停止，Supervisor与两端口已收尾。该旅程没有executor，不能认证真实训练、GPU、质量或收益。原件包含`result.json`、`commands.json`、`owned-processes.json`、`cleanup.json`和`original-authorizations.json`。

r4原15项受影响安装回归为12 passed／3 failed，241.56秒，外层242.618秒。三个原失败均保留：final目录故障场景没有保证实际进入目标注入点；accepted与monitor场景错误要求cleanup耗尽时必然有final记录。产品未为这些测试变化；测试改以真实owner身份和原锁结束为准，缺final保持unknown并核同原fence。两种final故障保持compute窗口10秒，cleanup改8秒，并要求fixture实际写出目标阻塞marker，防止未触发故障的假通过。最终173份测试快照`installed-tests-r4b-scope`与四项精准重跑在途；没有重建未变的r4产品wheel。

四项精准重跑`installed-tests-r4b`现已4 passed／58 deselected／93.12秒，外层94.034秒；两种final故障都实际进入marker，原owner释放且同原fence恢复。r4其余十二项原通过仍保留其测试快照，不把这两次运行说成一次十五项全部通过。r4 wheel SHA为`27a27377df2be065c3fe08df2f2e5fe3bf43df80b96e5f14fe061e3071c1b972`；后续仅测试预期调整，产品未变。

自身原结构模板r4复核为succeeded／approve，run`6ce000618e764488b42dcde5c7ae2a37`，56.218秒，外层58.740秒。18完整文件240668B＋三祖先资源均实际进入stdin，input digest`60bb762602861a2d5bcb65dfde1ed7d1b6f17571f7cbffe22fc27ed1214a9d77`，原result SHA`a1de5835bfa83ab8a0c067c47092beb30deb5dee699537f82aa1c32fb533518d`。仍为授权Codex回退及完整源码文本审查，不代替独立原件核验。最终22文件及含untracked diff固定在`review-scope-r4/`，原fresh-context评审者正在终核R1修正、两安装、原运行与收尾证据；未提前关闭独立门禁或宣称发布／CI通过。

## 最终本地独立终核

原fresh-context评审者已完成[最终报告](2026-11-15-training-budget-submission-review.md)：需求approve／结构维护approve，开放0／0，R1/P2关闭。固定22件scope SHA`ba4dc4dd5c50876d00d8b70f00d062593887f4ef0f9c7166e9efb2c648caba58`，原完整diff SHA`82c1975a13084f18d3063b14e1d531b5d82ea67b1f1de9076cb4141490bc26a9`；后续仅计划／交付当前状态更新，未改产品。独立逐字核两包648件、三版173测试快照、r3实红／原失败／r4b精准检查与自身结果；实际核真实流程23项原bytes／CLI／收尾、五个已知owner／helper身份与原session均无活进程，服务socket及两端口已释放。15处报告链接／锚点及差异检查通过，原结论和四项核验输入／JSON在`reviewer/`。没有重跑昂贵服务来替代原件核查。

本地实施、运行和独立审查门禁已通过；普通精确发布及本SHA自己的适用CI仍待前片b78门禁后结算。B3.3实际executor／后代停止、Q4.2c自动循环与真实训练继续开放，原失败各归原候选。
