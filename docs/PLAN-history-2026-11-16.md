# Ergora 实施计划与进度

最后更新：2026-11-16。恢复时先读本页、活动片计划／交付、`AGENTS.md`，再核 Git 状态与实际运行。此前完整检查点与逐片记录已[逐字归档](PLAN-history-2026-11-15.md)；[11月14日](PLAN-history-2026-11-14.md)、[11月10日](PLAN-history-2026-11-10.md)和[更早历史](PLAN-history-2026-11-09.md)保留原结果与身份。历史“当前／在途”只指当时，不覆盖本页。

## 当前检查点

**c1c首轮正式Workflow实现／验收／发布／自己的CI闭合。** [最终fresh独立审查](delivery/2026-11-16-training-cycle-workflow-final-review.md)需求／维护性均approve、开放0；源码／安装／真实现场及资源收尾原件全部终核。固定产品提交`ec6dcbcf23d35818aa23e87b6dbb129ed8ff75a1`，已普通导入当前开发分支合并提交`5b04b2b4cb4eb1c5d6899fc517cf86ecdec5536f`，新产品仍严格ordinal0。新wheel74e2f6f9、安装53／853输入保持；真实CPU原gate/archive、W2丢完成、W3重启、W4跨原BOOT预算、W5重复停止、W7实际server8766985B、W8编码及失败桥接按各自范围通过。38Workflow终态、原服务／监听停、759实际身份全absent、273原stdout refs匹配。旧r4／私有脚本失败保持，无重复测量接受／release／baseline迁移。见[逐场现场](delivery/2026-11-16-training-cycle-workflow-live-acceptance.md)。

当前分支`refactor/architecture-foundations`。c1c发布候选fa2fd17自己的[43766716392](https://github.com/626619403/Ergora/actions/runs/43766716392)八job全success；M1a产品5cb4cb9已导入bd47905，公开候选59b74ce自己的[43769505506](https://github.com/626619403/Ergora/actions/runs/43769505506)八job全success。对应精确输入、安装、独审与CI沿各自[交付](delivery/2026-11-16-training-round-content-extraction.md)保留，不转授后继。

M1b storage-only产品67ab9b4已导入23ad171，源码24＋12、旧v1 history三份、安装24＋14、663完整包、Ergora自身模板与fresh终核均闭合，仍不开放schema3执行。公开833966d自己的[43773202173](https://github.com/626619403/Ergora/actions/runs/43773202173)终态failure：plan／六Linux成功、Windows四个新增测试五个setup errors。最小四行平台mark经局部检查／fresh两轴approve／0，隔离1351e78普通导入6493f30；公开文档候选`610f111f0755edcfd8b4c582a7644ff79621c8ce`已普通推送／精确远端同一，其准确push／attempt1 [43777200480](https://github.com/626619403/Ergora/actions/runs/43777200480)已completed／success，八job全success；group5为15分46秒、Windows24分42秒，原时限不变。[修正交付](delivery/2026-11-16-windows-schema3-fixture-skip.md)保留原失败，不能用此前Linux成功替新Windows认证。

[M2／M3内部测量接受](plans/2026-11-16-training-cycle-measurement-acceptance.md)实现／源码／新非editable安装／自身模板／fresh最终终核已闭合。准确产品`68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，父23ad171，八文件固定patch0ccbc19e；r4源码26／217.94秒＋14／28.85秒，安装26／339.646秒＋14／39.162秒、新core实际10MB reader隔离通过。新包4c130b24的core／SDK各663完整字节／执行位同一、283参考／依赖过，848＋663＋179输入保持，37安装与49源码已捕获进程身份无活匹配。自身原结构模板Codex28.753秒approve；[fresh最终终核](delivery/2026-11-16-training-cycle-measurement-acceptance-source-review.md)需求／维护性两轴approve／开放0，当前报告SHA6752988a；原ref缺口、模型内部reader P1、fresh最后阻塞读P1及各轮真实失败／修后证据沿[交付](delivery/2026-11-16-training-cycle-measurement-acceptance.md)保留，不覆盖旧包／结果。

产品68ba793已普通导入本开发分支`c6cfafb0b556c0cd36cf6f541e95ac4b15d3b254`；663完整产品与已验输入同一，848中仅另两项已审差异为Windows四行mark和CI分组JSON。据[有限成本调查](delivery/2026-11-16-measurement-ci-budget-analysis.md)，两现成文件5→3的[再平衡](delivery/2026-11-16-measurement-ci-balance.md)已fresh两轴approve／0并导入a01570a；合并后真实collector2295=基线2269+新measurement26、无删除，原38节点恰按两文件5→3，组3=453／组5=484，无新job／加时／删保护。初次collector误解析venv二进制symlink为基础Python、缺pytest快速失败，原件保留；改为保留venv入口后实际收集通过。新联合公开候选`a0d533d13b4aae9441e3b6b920b27c2534353b87`已普通推送且远端精确同一；自己的官方push／attempt1 [43780806957](https://github.com/626619403/Ergora/actions/runs/43780806957)在00:56:31Z准确快照已completed／success，plan／六Linux／Windows八job全success；group5为18分43秒、Windows23分23秒，原20／30分钟不变。此通过不转授后继父留存。为新增22保护按[有限预算调查](delivery/2026-11-16-parent-retention-ci-budget-analysis.md)，[两完整文件5→1](delivery/2026-11-16-parent-retention-ci-balance.md)仅改原JSON：六组86文件保持；实际collector2317=2295+新22、无删，原70node恰按两文件移动、组1=355／组5=436，fresh需求／维护性两轴approve／0，配置已固定`9a351740de95eebc3376bc1454162e030b1a1731`；新联合公开候选自己的CI另验。

[父请求有界留存](delivery/2026-11-16-training-cycle-parent-request-retention.md)已闭合：固定产品`1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，原47,112B patch、源码22＋8、安装22＋8、完整663包／853输入、自身模板及fresh终核两轴approve／0；普通导入c4c0946。联合公开候选`debf6f96ed02620d22adc0ac6385c72641b3d53b`已推送／远端同一，自己的push／attempt1 [43784344936](https://github.com/626619403/Ergora/actions/runs/43784344936)官方01:31:47Z确认completed／success，八job全success，group5为17分31秒／Windows23分48秒、原时限不变。原403配额失败保持，不转授后继。

**M5-G前驱／最后gate与native source-v2已通过新fresh联合终核，普通导入1308e32、公开0a5a0ff已推同一，自己的官方push／attempt1 [43801502094](https://github.com/626619403/Ergora/actions/runs/43801502094)已completed／success，plan／六Linux／Windows八job全success。** [交付](delivery/2026-11-16-training-cycle-predecessor-native-gates.md)固定产品`5bcecf37b615e3708ceb08acc329ba3dd0470f4a`，11文件patch61e1e11f。r1–r6原失败／红例／探索保持；r7最小六行补实际current intent完整canonical与存在性末端重读，保留unborn。源码4过69.57秒，新core／SDK各663同字节／执行位，283／依赖过，安装 **5 passed／148.89秒**。原模板Codex67.198秒request-changes只重申已知R1、无新接线finding；同片源审关闭R2–R6。[新fresh联合终审](delivery/2026-11-16-predecessor-native-final-review.md)两轴approve／0，R1由下述显式v2最终whole-hook证据关闭，不反复模型刷判定，不开放schema3。

**完整hook无SDK前置最终r5已完成并普通导入1308e32、公开0a5a0ff已推同一，自己的官方push／attempt1 [43801502094](https://github.com/626619403/Ergora/actions/runs/43801502094)已completed／success，plan／六Linux／Windows八job全success。** [交付](delivery/2026-11-16-native-admission-dependency-isolation.md)固定`bc58be6781d35e7e4fbd54ad997df8a4743428a8`，唯一父5bcecf3；native-only 11文件patch3524d80f，2019／665输入冻结、两树同一，同片[源审](delivery/2026-11-16-native-admission-dependency-source-review.md)两轴approve／0。新非editable core／SDK665同字节／执行位、283／依赖过，安装 **25 passed／161.78秒**。正常选定native解释器首次executor导入前禁SDK／State／YAML／schema，v2真实native_main/callback在9,999,999及10,000,000B达到原schema3闭门且SDK未加载；v1真实禁SDK失败保持。自身原模板Codex28.602秒approve。安装原件和完整输入终核过；2实际父身份absent、2合成分列，原初混计记录保留。[联合终核](delivery/2026-11-16-predecessor-native-final-acceptance.md)两轴approve／0，报告771e33ba；已普通导入bc58be6及其r7父为1308e32；665完整产品名字／字节／执行位同一，855输入仅已审CI JSON与三个旧Windows skip差异。主树原collector2335／8.841秒同集合，同片固定集成复核两轴继续approve／0，报告更新30b4077d，准确0a5a0ff自己的43801502094八job全success；M6／训练效果另验。

联合公开候选`0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`已普通推送／远端完整OID同一；自己的官方push／attempt1 [43801502094](https://github.com/626619403/Ergora/actions/runs/43801502094)在04:29:27Z准确快照已completed／success，plan／六Linux／Windows八job全success。group5为15分41秒、Windows26分17秒，原20／30分钟未变。此前quota403／官方HTML在途及恢复后中间快照原件保留于publication-r1；成功只认证0a5a0ff，不转授a1／M6。

最终[CI再平衡](delivery/2026-11-16-predecessor-native-ci-balance.md)候选四完整既有文件5→1，六组86文件／Windows／时限保持。准确855输入仅替JSON、原collector **2335**，与同产品旧单文件配置node multiset同一；对父留存2317净增18／四改名映射无删除，搬移原87／最终89节点。组数354／444／410／453／315／359，原selector组1／5重放444／359。JSON8ffe961f已fresh两轴approve／0、固定55dc51c，已随联合0a5a0ff普通推送，自己的官方43801502094八job全success；旧r4／单文件历史不转授。

[M6正式V2／完整M1c与真实两轮设计](plans/2026-11-16-training-cycle-v2-runtime.md)已fresh静态两轴approve／0；V1正式类／v3表达片已冻结五文件patch9d3d7250、2019完整输入；源码runtime80过59.99秒＋真实S/H8过93.22秒、三份旧V1 history重放与无SDK导入过，389份实际捕获身份均absent。基线bc58be6为显式依赖；原表达候选新非editable core／SDK665、安装80＋8／三history／core与原模板approve均保留；fresh发现Windows owner路径与literal比较不一致P2，最小PurePath修正后patch b871eb2b、2019manifest610ab4bb，源码V2/V3定向25过。新包8574ebe6/coreSDK665完整同一，安装V2/V3组25过、Windows纯路径probe、三原history/core通过，原模板Codex76.908秒approve；同片最终独审接续，不把表达片验证写成M6完成。V1只接严格版本与有限机会／原预算表达，保留所有schema3效果关闭；原服务四poller／完整M1c正向和真实两轮仍后继V2／V3另验。已完成[真实CPU素材只读清点](delivery/2026-11-16-training-cycle-v2-cpu-prerequisites.md)：现有正例仅N1，后续须两个新候选各自manifest／review、新schema3出生及实际现场，旧pin／clock不升级。M5不单独开放执行；ordinal1／schema3效果、正式v3 producer及真实两轮仍待验，GPU／训练质量独立未认证。

**c1b1已固定提交并通过身份终核。** 主分支 `refactor/architecture-foundations`，提交`d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，实施基线 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。原预算根跨短S-H及正常loop退出／重启、唯一offer、existing-only、原一次窗口和只对账恢复已接通。原reviewer与自身模板发现的真实取消／receipt／最终deadline缺口已修；最终及固定提交独立需求／维护性均approve，开放0／0。新非editable core／SDK各652文件同一，283参考／25来源／依赖保持；安装r2 **76 passed／985.95秒**，同产品精准r3 **7 passed／153.70秒**，两轮各178输入冻结。SDK-free真实H观察、自身原模板真实Codex及已知原件收尾均通过。历史r1的62／8和r11输入身份限制保持；实际预算根父SIGKILL未实测。发布／准确CI仍另验，不认证总Workflow、自动多轮或训练质量。[计划](plans/2026-11-15-training-cycle-owner-lifecycle.md)／[交付](delivery/2026-11-15-training-cycle-owner-lifecycle.md)／[最终独立审查](delivery/2026-11-15-training-cycle-owner-lifecycle-review.md)。

**前片原CI失败及独立修复保留，已整入联合主线。** 原 `1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b` 官方run `43713822317`／push／attempt1为七job成功、group5失败：beta通知后过早读取writer marker。仅修原fixture到真实阻塞位置后通知及原子发布marker，旧反例失败／同fault修后通过，独立两轴approve／0。候选 `7025e15f40e1934097a5c1c962bb7bf5e82a979d` 已普通推送两个原ref；其自身CI未观察到，最后精确SHA查询HTTP200／total_count0，不证明未来不会有run或成功。修正已适配整入6725并保留c1b1新faults，未改CI。[调查](delivery/2026-11-15-cycle-stop-ci-failure-investigation.md)／[前片交付](delivery/2026-11-15-training-cycle-stop-operations.md)。

**BR／CI fixture联合已固定并普通推送，自己的CI在途。** 已接纳隔离组合的28项精确差异，保留主线五产品及所有旧资源，catalog33。新联合core／SDK非editable各663文件同一，283参考／依赖通过；216旧资源／旧对象／manifest／八输入保持。完整BR **50 passed／208.52秒**；同一178冻结输入下另跑CI／取消／并发候选 **8 passed／106.07秒**，未重跑c1b1总suite。三个preset真实CLI及报告完整资源通过；自身原结构模板真实Codex29.200秒approve。known markers／JSON原件的15完整进程身份当前活匹配0、unknown0。原报告390px下70px溢出保持，没有新浏览器质量认证。联合fresh及固定提交两轴approve／开放0／0；提交`6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`已推送本开发分支，精确远端同一。自己的官方run[43735663360](https://github.com/626619403/Ergora/actions/runs/43735663360)为push／attempt1，最新官方快照仍in_progress：5 success、group3 failure、Windows／group5在途。group3准确失败为review packet fixture硬编码1.0.1与新preset冲突；原完整日志403保持。最小fixture修正本地原反例失败、修后49通过，新fresh及固定提交两轴approve／0；已固定并普通推送`478c98891522930817fa7005a8ac96e408f37230`且精确远端同一。旧run最终completed／cancelled（5成功、group3失败、2取消）保持；新候选自己的官方push／attempt1 [43737570677](https://github.com/626619403/Ergora/actions/runs/43737570677)在途，plan成功／另七job运行，终态未定。[联合计划](plans/2026-11-16-review-reporting-mainline-integration.md)／[交付](delivery/2026-11-16-review-reporting-mainline-integration.md)。

**c1b2a服务片验收闭合并导入6918095，发布另验。** [r2具体合同](plans/2026-11-15-training-cycle-service-boundary.md)及[独立设计审计](delivery/2026-11-15-training-cycle-service-design-audit.md)已通过；R1–R4源码修正及复核两轴approve／0。服务产品隔离基线eedba08已吸收478，容量修正候选`97a0bbfae9687c15927f1437a374cd070baf0a94`已固定；服务已真实导入开发树6918095，尚未推送。修后包747e221b的core／SDK各663文件同一、283参考及依赖保持、178输入重冻；20项定向安装155.47秒通过，SDK-free真实S-H只读及原件／DB／窗口保持已验。[真实服务](delivery/2026-11-16-training-cycle-service-live-acceptance.md)四活动、receipt竞态、SDK attempt2只对账、独立stop、交接根跨原命令重启、信号／取消／fatal／强杀边界已验并统一收尾：144进程身份无业务残留、73份stdout引用核实、3预算根退出、自建Workflow终态、服务及监听停止。现场N=2，无执行器／训练。自身原结构模板Claude420.60秒失败，授权回退Codex95.84秒真实request-changes，指出launch材料容量异常降格unknown；已真实复现及两owner最小修正，源码9项114.79秒通过。新r3包081aab45的core／SDK各663文件同一、283／依赖保持；自身模板Codex及fresh源码两轴approve／0。安装初跑8通过／1正常窗口失败保持，独立确认unknown符合合同后只显式配置该正常测试control30，新冻单项1通过21.58秒；SDK-free真实S-H保持通过。后继af176cf仅该一行测试、产品同一；现场r3正常及N32完整66refs通过；r3b N32混合65refs＋完整unknown和39,518B聚合真实SDK非重试容量拒绝通过，全peer／原件／身份已收尾。最终fresh需求／维护性两轴approve／0，已允许af176cf导入，6918095已真实合并，不认证正式总Workflow／接受后继。[逐步交付](delivery/2026-11-16-training-cycle-service.md)。

**WA1–WA3 三份审计已收，WA4 详细方案仍为草案。** 用户新增的历史研究复用、任意循环、硬脚本／人工 Hook、调研设计前人类反复讨论与缺失公司知识提问均已[完整登记](plans/2026-11-15-workflow-evidence-and-human-gates.md)。[研究复用](delivery/2026-11-15-workflow-research-reuse-audit.md)、[实际 runtime](delivery/2026-11-15-workflow-runtime-capabilities-audit.md)、[设计／知识关卡](delivery/2026-11-15-workflow-design-knowledge-audit.md)审计明确现状：自有定义／StageDAG＋Temporal；受限嵌套串并行和既有批准／检查存在，通用 Repeat、任意非 Agent Hook和 typed 问题／答复／设计修订硬关卡尚未实现。已[汇总详细方案、客观验收和 D1–D4 产品取舍](plans/2026-11-15-workflow-design-and-execution-evolution.md)；先完成手头授权工作，再与用户讨论，不把设计写成已实施。

WA4三项异步讨论已获用户明确答复，D1–D4均采用建议；[原答复及决定](delivery/2026-11-16-workflow-design-decisions.md)已保存。新profile对框架／结构重构／重要变化强制设计；项目／模板最低必答、单owner决定、免答明确记录、新revision与重要变化重批、沉默非同意；先设计／知识关卡，再可信检查，与当前训练循环并行，最后通用Repeat／混合画布。[WA5a／b详细设计](plans/2026-11-16-design-knowledge-gates.md)r2 SHA5360d993补齐G1冻结policy原件路径与withdraw尾部恢复，经[新fresh设计审](delivery/2026-11-16-design-knowledge-gates-design-review.md)需求／维护性两轴approve／0。WA5a-1 [只读typed材料检查](delivery/2026-11-16-design-packet-inspection.md)五文件已冻结patch cfde3166，2053输入同一，源码118 passed／25.11秒、原283保持；r1新非editable core／SDK666及安装118过；fresh发现真实原生解释器缺jsonschema，原模板另提重复source ID与报告媒体两P2，已确认原真实native入口红例及两P2红例，最小修后三项过，作者六文件r2冻结／源码121过30.76秒。已移植当前0a5主线为独立a8d1855，五文件raw/exe同一、task_plan AST同一，fixed patch292bd725；新668产品／858输入安装121过；原结构模板Codex48.475秒发现公共task_approval(inspect-plan)绕过应用验证的新P1，根已两行路由修复，原双入口红1／绿1；新fixed-r3 patch4daea8ea、2064输入，源码56过＋1可选Web skip、新包668安装57全过，自身模板Codex31.855秒approve；同片最终两轴approve／0，固定cb861ea并普通导入3d632a7，inspection-only片闭合；自己的发布CI另验。同片源审r2关闭前述三项，不覆盖此新finding或新的最终安装。不能以r1安装绿代真实native seam。旧admission无design policy时明确inspection-only、runtime_enforced:false，不把packet自报owner升级身份。不注册input12／新writer，不改默认模板，新runtime门未实施。

## 接续顺序与可验收节点

|优先／节点|下一步与完成标准|权威记录|
|---|---|---|
|P0 c1b1|已固定d5b5891且提交身份终核通过；随联合候选普通发布及准确CI另验。源、安装、模型、独立、发布各自记账|[生命周期计划](plans/2026-11-15-training-cycle-owner-lifecycle.md)／[交付](delivery/2026-11-15-training-cycle-owner-lifecycle.md)|
|P0 前片 CI 修正|7025已独立通过／双ref推送；最小修正已整入6725，候选自身未观察到run，旧失败保持|[前片交付](delivery/2026-11-15-training-cycle-stop-operations.md)|
|P0 BR1／BR2及CI成本|6725自身CI group3失败／整体cancelled；修正478已推同一。官方API已确认43737570677终态completed／cancelled：plan与另六native成功，group5超时取消；新分组b653自身CI尚未发起|[fixture交付](delivery/2026-11-16-review-packet-ci-fixture-fix.md)／[成本调查](delivery/2026-11-16-ci-training-shard-duration-analysis.md)|
|P1 c1b2|af176cf产品同97a0bbf；新包／自身模板／终审闭合；安装8+新冻1分别记账，SDK-free保持；真实N32完整／unknown／容量及收尾通过；已导入6918095，发布待CI分组收尾|[服务交付](delivery/2026-11-16-training-cycle-service.md)|
|P0 CI测试分组／Windows skip|879自己的43752183692终态failure及Windows原四错保持。c52已fresh两轴approve／0并随df43660普通推送／精确远端同一；自己的43755708928终态success，plan／六Linux／Windows八job全success，group5 17分29秒在原时限；只认证df43660，隔离Workflow另验|[CI分组计划](plans/2026-11-16-training-ci-shards.md)／[Windows修正](delivery/2026-11-16-windows-sdk-fixture-skip.md)|
|P1 c1c|ec6dcbc终审两轴approve／0并导入5b04b2b；文档随fa2fd17普通推送／远端精确同一，自己的官方43766716392八job全success。仍严格首轮ordinal0|[首轮交付](delivery/2026-11-16-training-cycle-workflow-first-round.md)／[现场](delivery/2026-11-16-training-cycle-workflow-live-acceptance.md)／[最终审查](delivery/2026-11-16-training-cycle-workflow-final-review.md)|
|P1 c1d|最终r7/5bcecf3源码4、新安装5过，R2–R6关闭；原模板仅已知R1。native最终证据／收尾／新fresh联合终核两轴approve／0，R1关闭；已普通导入1308e32，主树2335同集合；公开0a5a0ff已推同一，自己的43801502094八job全success；M6／实际两轮另验|[M5交付](delivery/2026-11-16-training-cycle-predecessor-native-gates.md)／[M6设计](plans/2026-11-16-training-cycle-v2-runtime.md)|
|P1 M6-V1正式表达|五文件冻结9d3d7250／2019输入，源码80＋8、三原V1 history重放及core无SDK过；原core／SDK665安装80＋8、replay/core／原模板过；fresh路径P2以PurePath最小修后patch b871eb2b／源25过，新包665／安装25／probe及原模板approve，最终复核接续。全部schema3效果保持closed，服务拓扑／真实CPU另片|[M6设计](plans/2026-11-16-training-cycle-v2-runtime.md)|
|P1 M5真实hook依赖前置|r5/bc58be6接最终r7，新core／SDK665身份过、安装25过、v2实际禁SDK native reader过、原模板approve；收尾／联合终核两轴approve／0，已普通导入1308e32、产品665同一，保留v1失败，不改283／旧pin|[依赖片交付](delivery/2026-11-16-native-admission-dependency-isolation.md)|
|P1 WA4→WA5a／b|D1–D4确认、设计r2 fresh通过；a-1 r1五文件冻结、源码118／新安装118过；fresh native依赖与模型两P2已真实红／最小修，作者r2源码121过，固定移植a8d1855新668包安装121过；原模板发现公共approval inspect-plan绕应用验证新P1，fixed-r3两行修／双入口绿、新包安装57与原模板approve，最终独审两轴approve／0，cb861ea普通导入3d632a7；后继S1/J/F/G拆片三finding已最小修订，方案a94b4a5a经同片需求／维护性approve／0；A最终闭合后实施S1。执行门与源journal写入独立验|[详细设计](plans/2026-11-16-design-knowledge-gates.md)／[已确认决定](delivery/2026-11-16-workflow-design-decisions.md)|
|P1 R1–R3／WA5c|逐 finding独立验证、成对eval和可信非Agent检查。不能以Claude产品能力或提示词冒充当前runtime|[审查演进计划](plans/2026-11-15-review-validation-evolution.md)／[设计演进方案](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|P1 Q5.2／Q6|按实际调用证据细化可维护性重构；最终严格全面审查、手册／示例／脚本／组件协议与发布。kernel专家保留在v3路径|[领域／优化／质量计划](plans/2026-11-15-domain-review-optimization-quality.md)|
|P2 WA5d／e|本域闭环后再设计一般有界Repeat和混合图，随后CLI／页面／交接；沿原编译与Temporal|[设计演进方案](plans/2026-11-15-workflow-design-and-execution-evolution.md)|

## 已完成能力与开放外部条件

|主题|当前边界与入口|
|---|---|
|安装／工具层／Windows／RSI／主线|[总计划](plans/2026-11-01-all-in-one.md)、[架构](architecture/current.md)、[使用手册](USAGE.md)；Apache-2.0已落实，main已建立且用户已设默认分支|
|定义／资源／后端／组合与画布|[AC总计划](plans/2026-11-08-agent-composition.md)、[定义手册](AGENT_DEFINITIONS.md)、[组合手册](WORKFLOW_DEFINITIONS.md)；全部祖先Skill／上下文累积、权限逐级收窄、版本冻结、正式选择|
|开发／重构／优化模板|[专家总计划](plans/2026-11-12-specialist-template-refresh.md)、[重构模板](delivery/2026-11-13-refactoring-preset.md)、[采用矩阵](research/2026-11-12-specialist-adoption.md)、[优化方向](plans/2026-11-13-specialist-presets.md)；六阶段、专业子模板／横纵专家、kernel v3保持|
|PR／MR审查与工单|[领域审查计划](plans/2026-11-15-domain-review-optimization-quality.md)、[审查手册](TRAINING_REVIEW.md)、[Anthropic比较](research/2026-11-15-anthropic-code-review-comparison.md)；三路all-join／领域专家／只读来源／本地报告已接，逐finding复核与增量循环后继|
|记忆／Skill／评价／复盘与交接|[改进计划](plans/2026-11-14-evaluated-improvement.md)、[集成交接](plans/2026-11-14-integrated-handoff.md)；原候选→可信评价→明确采用／回退→新任务冻结，CLI／页面已验，旧结果保持|
|真实训练优化B3|仍需完整资产、环境／设备、预算、正式baseline／candidate、独立质量oracle与准确evidence批准；[B3a](plans/2026-11-14-proposal-experiment-handoff.md)及[源码试用](delivery/2026-11-14-workload-source-trial.md)不替代真实训练|
|完整原生Forge C2|仍需父完整材料、teacher／student／judge、内部会话权限、跨恢复预算与真实停止；原隔离要求保持，不能关闭failIfUnavailable绕过。见[原生准入](delivery/2026-11-14-forge-native-admission.md)|
|可选后端与服务|DeepSeek Linux／WSL2只读及归档／真实续接按[准入计划](plans/2026-11-12-harness-admission.md)；OpenHands受限准入、Windows原生、MCP／A2A跨服务／远端隔离等按各自真实缺项验收|

## 持续执行与验收规则

- 用户已授权沿计划持续推进，每步更新本页和所属交付；恢复后核Git／活动片。长期文件在项目docs或home持久目录，不依赖临时目录。
- 完整实现片用新的fresh-context reviewer，提供原始要求、固定baseline、tracked／untracked差异及实际证据；需求／维护性两轴，修实证finding后复核。状态记账不递归审查。
- 用户允许按任务复杂度调整子agent思考强度：小而明确的实现用较低强度；架构、并发、生命周期／恢复及权限边界用较高强度。任务范围和客观验收先明确，重要变更仍由新的独立reviewer审查，不以降低强度省略门禁。
- 大项使用Ergora自身审查模板，保存实际输入／后端／原回复；优先异后端。Claude不可用时用户已授权Codex／ChatGPT回退，保留失败理由，不冒称异后端成功。
- 凭据仅引用外部环境变量，ChatGPT变量名`LINGZHI_API_KEY`；公开仓库不含密钥、私有源码、内部服务或本地验收缓存。
- 保持六阶段、原candidate／approval／attempt-before-send／unknown对账、版本冻结和283参考文件；复用Temporal、process monitor及证据owner，不增第二调度器／实验账本。
- 子模板读取全部祖先Skill／上下文；资源累加不扩大工具授权，子权限不越父模板。追加权限父子共同修订，已开始运行保持旧版本；容量不足明确拒绝，不截断后宣称完整。
- 按风险验证公开行为，必要检查通过后不无理由重复扩大；测试保护真实静默错误，不为文案／默认参数／普通可见失败堆断言。结构改动先查真实调用者与原库／owner。
- 已接受容器／当前用户作为可信项目边界，无宿主权限；不提权、不绕审批，不把只读模型工具限制称OS沙箱。未验平台及外部能力如实保留。
- 每片普通提交／推送当前分支、核精确远端及自己的必要CI，不借其他候选成功，不强推／自动合main；最终交接自包含，说明安装、交互、使用和关键限制。

## 压缩／换机恢复清单

1. 先核本页、Git HEAD／分支／diff与在跑进程，不重复启动现有回归或训练。旧摘要不能覆盖原JUnit／receipt与准确候选。
2. M2／父留存各自八job成功。M5最终r7/5bcecf3安装5过、R2–R6关闭，模型仅已知R1；native最终r5/bc58be6安装25过、真实正常前缀禁SDK完整hook过、原模板approve。收尾／新fresh联合终核已两轴approve／0、R1关闭，已普通导入1308e32／产品665同一／主树2335collector，公开0a5a0ff已推远端同一，自己的43801502094八job全success（官方04:29:27Z快照）；不重启旧批、不转授结果。CI新四文件配置2335真实collector／selector过、fresh两轴approve／0、已固定55dc51c，随0a5a0ff自己的八job全success。M6各自另验。
3. 前片CI准确失败须保留，不把限额／403／未知改成success；独立候选修复与自己的CI分别记录。
4. Windows四行修正610f111自己的43777200480八job全success，833原五setup errors保持。CI两文件再平衡已独审导入a01570a，合并2295 collector只新增M2的26节点，无删除；正式运行时限仍由新联合候选自己的CI认证，不借旧CI。
5. WA1–WA3已完成、D1–D4明确确认，不重复问。WA5a／b设计r2已fresh两轴approve／0，a-1 r1源码／安装118过；r2原native依赖与两P2已修、固定a8d1855新包121过，模型又发现公共approval inspect-plan漏验证，最小修正及最终新包／复核接续，勿转授r1/r2绿；恢复先核其worktree与交付，不启临时v12或借packet自报信息批准。训练／依赖片继续各自验收。
6. 每个节点完成更新本页及所属交付。当前事实与历史分开，具体数值／原件留所属交付，本页只保留可恢复的活动状态。

当前后继设计拆片：[registration／State与源journal](plans/2026-11-16-design-gates-registration-and-journal.md)，r2 SHAa94b4a5a；[fresh设计审](delivery/2026-11-16-design-gates-registration-and-journal-design-review.md)两轴approve／0，原三finding关闭。a1已最终闭合并普通导入3d632a7；最小下一片S1可按已审范围实施，真正首次登记、State6与pre-claim拒旧输入，先登记准确序列化边界；既存creation与registration修订耦合、同UID真实人类通道不可用、b1封存／撤回及a2双门／最后spawn为明确后继，不用storage-only冒充新v12执行。
