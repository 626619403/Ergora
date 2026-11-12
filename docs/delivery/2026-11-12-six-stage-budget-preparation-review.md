# B2a 持久预算准备独立评审

**当前结论（r3修正／r4最终候选）：已审B2a本地独立评审通过，Spec 0项开放、Standards 0项开放；SP1–SP3／ST1–ST3全部关闭。** 普通发布、精确Git身份及本候选必要CI仍待后续核验。下文保留r1／r2当时的失败判词；最终依据见末节。

日期：2026-11-12。协调评审者为 fresh-context `budget_preparation_review`；另按 `code-review` 分别启动了 `fork_turns:none` 的 Spec、Standards 两轴，均未参与实现，也未读取对方笔记。这里的独立性指新的模型上下文，不表示不同模型或统计独立。遵循项目 AGENTS、`maintainable-project-delivery` 的独立 brief 和 `codebase-design`，先读原始计划、设计复核和源码，再读作者交付说明。

**r1：Spec 需修正，开放2项P2；Standards 需修正，开放2项P2。** 两轴分别保留判词；SP1与ST2指向同一并发身份问题。尚不能关闭B2a出口，后续修正及实际验证须按新候选同片补核。

## 身份与范围

固定基线与实际HEAD均为 `e37f617f9aca566d862175de5a1e6b25a08ba2de`；前一产品为 `f394945db894740ad23a81c62b4ad87c85a84511`，e37只含文档。标准三点diff及提交列表为空，本片实际比较为 `git diff e37f617f9aca566d862175de5a1e6b25a08ba2de --` 加未跟踪文件。

独立逐字核对私有 `six-stage-budget/b2a-review-candidate-r1/` 全部18文件；`b2a-review-files-r1.json` 的SHA256为 `7ad2bc8e280da130ec0c9bc33ed036000e383b2eb89055007608bd925dc2476b`，各文件尺寸／SHA均相等，核对时当前18文件也逐字相同；`b2a-review-tracked-r1.diff` 与上述工作树tracked差异相等。三份新增文件为 `reference_budget.py`、`task-definition-v5.json`、`test_task_budget.py`。未把随后开始的修正纳入r1身份。

审查范围仅为[已审B2a](../plans/2026-11-12-six-stage-budget.md)：一次授权持久prepare、完整准备消费者、固定preview、精确create／恢复、完整预算与有限slot读取，以及新v9执行关闭。B2b／c尚无正式生命周期消费者本身不作为本片缺陷；其实现与实际六阶段旅程仍待后续。核了CLI／HTTP、原creation／submission、版本输入、Executor、项目绑定与注册写入者、进程监督及相关夹具；没有修改源码／测试、安装、运行测试／模型、请求远端或提交。

## Spec

**结论：需修正，2项阻塞P2；未发现额外范围扩张。** 原预算、完整材料和版本化运行门禁的主要接缝已接入，下面两个恢复路径尚未满足合同。

### B2a-SP1 · P2：锁忙分支漏核本次请求的完整身份

- **位置：** [reference_task_creation.py](../../src/ergora/reference_task_creation.py#L565) 的 `BlockingIOError` 分支；正常比较在r1第370、381–382行。
- **要求与事实：** [预算计划](../plans/2026-11-12-six-stage-budget.md#L47)要求保存原定义／项目身份，第80行要求“绑定或注册修订冲突可见”。锁忙时直接调用 `preparation()`，而其第317–320行只核control／project／repo／execution／registration／task_id，不比请求定义摘要、project revision或policy。
- **可达后果：** 原prepare持锁时，同task ID的不同input／预算，或已变修订的请求，可得到原授权的unknown／prepared状态，冲突被静默当作同一次请求。原预算没有重领，后续preview仍会拒绝，但prepare的精确身份合同已违约。
- **最小修正：** 原授权已可读时，锁忙观察也比较请求的完整scope／policy；只让相同请求观察，冲突明确拒绝，原件尚未可读仍可busy。补核并发不同定义／预算／revision。

### B2a-SP2 · P2：安装停止计时器时回补了持久attempt的耗时

- **位置：** [reference_task_creation.py](../../src/ergora/reference_task_creation.py#L385)，r1第385–398行。
- **要求与事实：** [预算计划](../plans/2026-11-12-six-stage-budget.md#L50)要求沿原绝对截止约束；第82行规定工作截止请求停止。代码先取remaining，再写prepare-attempt、mkdir和import，最后从较晚时刻按旧remaining设置timer。冻结 `core.write` 含fsync，耗时并非零。
- **可达后果：** 若原剩余2秒、持久化耗0.8秒，worker开始时检查仍可通过，但慢安装／材料将到原工作截止后0.8秒才收到停止，消耗清理预留。worker第541行只检查一次；最终exhausted不能纠正此前超期业务工作。本项为源码可达性推导，未作受控重现。
- **最小修正：** 持久attempt后、设置timer／启动worker前，从原instance重算剩余；已耗尽只收尾，保留原起点和attempt。

## Standards

**结论：需修正，2项P2硬违反；无另列可行动baseline smell。** 标准来源为AGENTS、[当前架构](../architecture/current.md)、[合同与身份](../architecture/contracts-and-identities.md)、原D1／B2计划及上述skills；未发现CONTRIBUTING／CODING_STANDARDS文件，工具可检查的规则不重复列finding。

### B2a-ST1 · P2：发布所有者在观察超时后失去项目修订锁

- **位置：** [reference_creation_process.py](../../src/ergora/reference_creation_process.py#L40)；父锁在r1 `tasks.py` 第202–206、226–233行，实际发布在 `reference_task_creation.py` 第440–488行。
- **标准与事实：** 当前架构规定控制项目为权威、项目revision与有效绑定由tasks准入；合同与身份表明确tasks拥有该责任。新launcher对create／resume也在30秒后返回unknown并留下owner继续执行；父SQLite reservation随返回释放。原创建超时会停止子进程，不存在这个持续发布窗口。
- **可达后果：** 慢读取／验证／发布超过观察窗后，`projects.bind` 第68–82行可更新控制DB和revision。owner仍比对捕获的旧project，`check_registration()`只核未随binding改变的磁盘注册投影，因而可继续发布旧修订合同，破坏原创建写锁不变量。
- **最小修正：** 将持续发布期间的原SQLite reservation及当前revision核对交给存活owner；或保证create／resume返回时发布已经停止，只单独保留必要安全清理。须实际覆盖观察结束后的修订竞争。

### B2a-ST2 · P2：并发失败路径绕过持久身份校验

- **位置与场景：** 同SP1，独立Standards轴也定位到r1第565–572行绕开第381–382行，导致不同定义／policy的并发prepare收到原授权的正常状态。
- **标准：** 违反原精确身份责任，以及 `maintainable-project-delivery` 关于在所属所有者校验不变量、保留必要persisted-state检查的规则；这是硬违反，不是命名或smell判断。
- **最小修正：** 在锁忙观察中复用同一局部scope／policy核对，补不同定义的并发入口回归。

预算Module已有tasks、creation、envelopes三个生产消费者，纯数据所有权和Interface深度合理；版本选择沿既有共同Interface，无第二调度器／正式账本。新测试主要保护真实丢回执、进程树清理、迟到成果和v9拒绝等静默风险，未新增重复CI，也未要求算术同形测试。

非阻塞成本观察：每次已完成preview仍永久保存完整操作目录；CLI／HTTP r3一份为190,303字节，其中stdout184,431字节，重复预览会线性复制完整record。unknown时保留安全owner文件有实际理由；可考虑只回收已结束的读取观察目录。本片没有给该目录留存上限，不据此另列硬违反或牵强归类smell。

## 实际证据与限制

只读核了私有 `six-stage-budget/` 下的原件，区分pytest正文计时与外层wall计时：

|原件|已核结果与实际范围|
|---|---|
|`b2a-source-r1/result.json`|记录首轮7通过／1项CLI测试命令误写失败；首轮没有保存本地stdout，未声称直接复核其完整输出。|
|`b2a-source-r2/`|原stdout为7通过／1失败、48.40秒；HTTP缺已有同源头被403拒绝。|
|`b2a-cli-http-r3/`|修正测试头后1通过、9.12秒；CLI／HTTP共用原prepare。|
|`b2a-cleanup-r1/`|1通过、10.17秒；测试经真实prepare和实际flock阻塞回收，有活后代时unknown且无prepared／完成witness，解锁后exhausted并回收。|
|`b2a-install-r1/`|非editable Python3.12.11 wheel已构建／安装；原stdout为76通过／1失败、127.20秒。失败是既有architecture allowlist未登记新增stdlib依赖，不能称安装回归通过。|
|`b2a-source-r3/`|审查时仍只有部分输出，无result终态；不提前称完整11suite通过。|

评审者另外自行重算：wheel SHA256 `c30f651134fbcf65737e6987b12f7f48f1b7704f395bfc5968fbd74f4e46a6e1`；455产品文件在源码／wheel／安装三处逐字相等，两份RECORD逐行hash／size均通过；283冻结文件在源码及安装均与原manifest一致，manifest本身等于固定基线。身份通过不替代行为验收。

v9的submission拒绝、worker／request-root枚举排除、直接Executor拒绝均已核源码及上述受控检查；可信当前容器未被称为OS隔离。未把B1或进程原语探针的通过移作本片通过，也未把静态slot预留称为模型实发次数。

下一出口为修正以上两轴finding、取得新候选完整身份及受影响复验，再由本片两轴补核。完整安装修正、实际自身审查模板、最终静态与本候选的必要发布CI仍缺；B2b／c及真实六阶段旅程保持后续职责。私有轴笔记为 `b2a-spec-review-r1.md`、`b2a-standards-review-r1.md`，后续判词不得覆盖本轮失败／未验范围。

r1两轴计数：Spec 2项、最高P2（并发身份／绝对截止）；Standards 2项、最高P2（发布修订锁／并发身份）。

## r2 同片补核：最终完成见证仍有P2

原两轴继续本片复核，没有另起重复评审或借新模型判词替代源码审查。完整20文件 `b2a-review-candidate-r2/`、清单 `b2a-review-files-r2.json`（SHA256 `0aad4336c09bd5a315387e3b017991f676fb5c6d2c6fef5bcbf2ae728eae2f70`）及tracked diff均已独立核准。核对时20份当前字节也相等；其中本报告为追加本节前的9,489字节、SHA256 `1d63ac7ed6406e99fad2692076d702335d44f2870b176ba1dd85982c118d5225`，不声称r2清单覆盖后来追加内容。

**r2 Spec／Standards仍需修正，各新增1项P2。** 原SP1／SP2／ST1／ST2的修正已有源码及真实行为依据；新增SP3／ST3是同一最终witness问题在两轴的独立判词。

### Spec：B2a-SP3 · P2，最终witness的阻塞落盘发生在截止终核之后

- **位置：** r2 [reference_task_creation.py](../../src/ergora/reference_task_creation.py#L427) 第427–434行；冻结 `core.write` 第39–47行先write／flush／fsync，最后才link公开不可变路径。
- **要求：** [预算计划](../plans/2026-11-12-six-stage-budget.md#L9)规定“总截止时清理或结果仍未确认，保存原unknown／未确认及实际超时事实，不能报额内成功”；第82行要求确认后超期记录exhausted与实际overrun。
- **可达场景与后果：** 代码先采样elapsed／recorded_at并决定prepared或exhausted，然后在已关闭监督timer的情况下写最终prepare_result。如果这次fsync显著阻塞并跨总截止，截止时仍无完成witness，之后却公开旧elapsed、prepared、overrun0。动态budget_status exhausted不能区分“按时完成后自然过期”与“完成见证迟到”。create仍按原截止拒绝，本项不构成执行绕过。
- **最小修正与状态：** 将最后有意义的持久化放到完成事实公开之前，在fsync后／link前按同一instance复核总截止；迟到只保留unknown或发布exhausted及当时实际超期事实，不能先公开prepared再覆盖。须用真实prepare最终witness的fsync延迟作red／green；本项当前开放，未借现有80／54项或模型approve关闭。

SP1已核锁忙分支重新比较完整请求scope／policy；SP2已核attempt落盘后重新取原剩余量。原r1 wheel上的有效red分别出现未raise与elapsed7.02932秒大于6.5秒，修正后的源码／安装检查覆盖相同真实入口；原两项关闭依据成立。

### Standards：B2a-ST3 · P2，完成事实发布缺少最后的生命周期核对

Standards轴独立核到同一第427–434行的有意义阻塞窗口，违反计划的实际超时事实要求，以及 `maintainable-project-delivery` 关于必要checkpoint／resource-lifecycle检查和证据准确性的规则。它是硬违反，不是微小原子操作竞态或smell判断。最小修正仍由原creation所有者在最终持久化完成、公开prepared之前核预算；不改283冻结write，不增加正式账本，也不以读取时的当前expired时间伪造旧prepare耗时。ST3当前开放。

ST1已核实际publisher用原State `BEGIN IMMEDIATE`，比较当前revision／registration，并由ExitStack持有至完整record核验和文件发布返回；父预算create／resume不再持同锁等待。真实flock阻塞publisher、提前返回unknown时，绑定写者仍被原SQLite锁挡住，解锁发布后才能进入。ST2与SP1的同一身份修正也已核。原两项关闭依据成立。

原非阻塞preview成本观察，以及实际自身模板r1提出的preview只读P2，已通过复用原短生命周期 `task_creation(..., budgeted=True)` 消除；预算preview继续只读已冻结材料，没有新层。对原r1包的两次preview确实多8个文件，修正后检查整个operations树不变。原架构测试只登记新增stdlib foundation及合法下层依赖，原保护未删除；新增检查针对已复现的并发、截止、锁和存储错误，没有新增CI或算术同形测试。

### r2 已验原件与仍缺部分

- `b2a-findings-red-r2/` 用原r1未变wheel的 `python -I` 实际得到4失败、27.89秒：并发冲突未raise、慢attempt导致7.02932秒、绑定写者提前完成、preview多8文件。`red-r1`误把venv解释器resolve成缺pytest的基础Python，不作为有效red。
- `b2a-fixes-r1/`：预算与原架构检查24通过、74.10秒；外层wall为74.664秒。这是SP3发现前的修正范围。
- `b2a-install-r2/installed-core`：非editable／`-I` 的budget、creation、tasks、architecture四suite，80通过、139.08秒；外层140.855秒、exit0、无timeout。
- `b2a-install-r2/installed-transport`：原submission、locks、composition_transport三suite，54通过、316.08秒；外层316.885秒、exit0、无timeout。SDK受控fixture不能被称作真实Temporal端到端生命周期。
- r2 wheel SHA256 `a9fd7371d407f8d95139b70b44cd91c9c8c5307c7708328c57ff8dc88e6e826b` 已自行重算；455产品源码／wheel／安装字节相等，460行wheel RECORD及465行安装RECORD的hash／size无差异，283冻结文件和manifest保持基线。
- 实际自身模板r1为314.23秒succeeded／request-changes，18完整文件554,700字节；r2聚焦复核为145.60秒succeeded／approve，11完整文件186,675字节。评审者自行从原native stream的成功MCP文本页重组两轮全部五scope至null；candidate分别21／9连续页，全文及所载18／11份完整冻结文件均逐字相等。r2 attachment SHA为 `5938b9d5c935ea59981ccac3256883c9f2f1f319879c4b35f8bd00d5398a7ac8`，原result SHA为 `731f6185e6625d8d6aaa480f5e45a10fea4192ded5cd6db80e1af6aa528546e4`，failed MCP均为0。原审计与四个采样身份无存活的结果也已读取；不把采样扩大为覆盖所有短进程。聚焦approve不覆盖后来发现的SP3／ST3或完整21文件。

原11suite `b2a-source-r3` 已900秒外部终止，无pytest终态；`timeout.json`、partial stdout和空的专属进程后查均已直接读取。后段源码已改变，保留为混合范围partial，不称全通过。五个代表旧／v8／work进程旅程、最终状态文件清单、SP3／ST3真实red／修正及新包验收仍待。后补D1状态及记账不在r2的20文件字节身份中；最终静态和精确发布CI也尚未据此关闭。

r2两轴计数：Spec 新增1项P2（SP3）／原2项修正已核；Standards 新增1项P2（ST3）／原2项修正已核。

## r3修正／r4最终同片结论：B2a本地出口通过

原Spec、Standards两轴分别完成最终同片补核，未读取对方笔记；协调者核原件后汇总。**Spec通过，开放finding 0，SP1／SP2／SP3关闭；Standards通过，开放finding 0，ST1／ST2／ST3关闭，无新增硬违反或可行动baseline smell。** 本节关闭已审B2a本地出口，原r1／r2问题及失败史保留。

### 最终候选身份

基线／核验时HEAD仍为 `e37f617f9aca566d862175de5a1e6b25a08ba2de`，实际范围仍是工作树差异及明确列出的新增文件。独立核r3的21文件／597,400字节，清单SHA256为 `22d6871c240bd2ab5de17a9375e715f6b170a245995d62ac55820b591f5d8841`；最终r4的21文件／598,664字节，清单SHA256为 `1fe46e78926bb4f6a83bf6f380ee39de58e2008b3babdbf2a96a9e31f3582744`。快照各尺寸／SHA、核验时当前文件字节及tracked diff均相等。r3至r4只改PLAN、预算计划和交付说明的状态记录，产品／测试相同；相对r2增加的[D1计划](../plans/2026-11-12-six-stage-native-consumer.md)仅更新B2状态。

r4清单、最终静态及模型材料中的本报告均是本次更新前的15,877字节，SHA256 `d67d979f3a9223523458a93764c70851ab85c1577510f22bf1f247db49267341`。不声称这些冻结身份覆盖随后新增的当前结论和本节。评审者只更新本报告及各轴私有笔记，未改产品／测试。

### SP3／ST3关闭依据

[原creation所有者](../../src/ergora/reference_task_creation.py#L434)现先以冻结 `core.write` 完整写入并fsync私有 `outcome.json`，随后按原instance的总截止重新核remaining；迟到时改选exhausted候选、清除prepared hash／failed detail并保存当时观测的超额，最后仅hardlink已持久字节到唯一完成witness。预算起点、原attempt和task锁保持，不改冻结write，不新增正式账本。时钟／boot核验失败仍保留unknown，不重跑body。

显著阻塞的prepared候选持久化已进入最终资格门禁，不能在慢fsync之后公开先前的额内成功。时间字段是候选决策处的观测；不将其扩大为最后hardlink或exhausted候选fsync返回时刻，也不承诺内核强实时。按时prepared的历史结果仍可在自然过期后确定性只读preview。

关闭有真实red／green支撑：`b2a-final-witness-red-r1/` 在未变r2安装wheel的实际owner最终outcome `os.fsync` 中延迟4秒，期间观察为unknown，随后旧实现错误prepared，原stdout为1失败／9.72秒，外层10.736秒。新增回归按 `cleanup_confirmed` 的真实write识别最终候选，不依赖公开文件名；因此改成私有候选仍触发同一慢fsync，核了期间unknown、迟到exhausted及正overrun、重复原ID结果不变和preview拒绝。`b2a-install-r3/affected` 的非editable、`python -I` 预算及原架构检查25通过／82.89秒，外层84.774秒、exit0，无timeout。两轴分别确认SP3、ST3修正充分。

SP1／ST2的完整scope／policy并发校验、SP2持久attempt后重算原remaining、ST1由实际publisher保持SQLite reservation至完整发布均维持r2已核修正；preview仍复用会回收的原临时transport。没有额外产品修正使这些结论失效。

### 最后实证及其范围

- r3最终wheel SHA256已自行重算为 `e3d294ff82fc1baaf12750ee631327ff62f11d383833433405d9f6abb95b7276`。455产品文件在源码／wheel／非editable安装逐字相等，460行wheel RECORD及465行安装RECORD的hash／size通过；283冻结文件和原manifest身份保持。环境为Python3.12.11。
- r2安装core的80通过、transport的54通过保留原范围；`installed-journeys` 原stdout另核为5通过／140.10秒，外层140.850秒、exit0、无timeout，覆盖旧命令治理／大改动、v8完整及issue-source材料、原work完整旅程。其原Executor和真实可信夹具命令确实运行，提交SDK受控；不据此声称预算v9或真实Temporal六阶段生命周期通过。最后产品变更只在prepare最终witness，不将未重复的r2检查改称r3全套。900秒外部终止的广泛源码运行仍是混合范围partial。
- 实际自身模板r3为Codex／`gpt-6.1-sol`／high，修订1.0.124，run `0b84959536944de185c1c60a9d5b7ca2`，106.919秒succeeded／approve；只覆盖七份完整冻结文件、114,994字节。协调者另从原native stream重组全部五scope的连续UTF8页至null，candidate共九页，七文件与r3快照逐字相等，失败MCP为0。candidate SHA256为 `c2d17cc5081cbbd24b33ab080355557831d4788c538b191c5032ce79d7e741c3`，原result SHA256为 `643cf0ff0e010b77e5c8cd01cfea19f8a6b510be54874c480a61b0ec3939d892`，native stream SHA256为 `3d01cd58f7af51a88cab666e9359d1a8fc367bf3e8dc6cf0ed8dbebd0896df5b`，均独立重算相等。已读原审计及四个采样身份无存活的记录；聚焦approve不代替两轴全21文件审查、不声称模型运行测试或核私有日志，三轮同后端也不声称统计独立。
- 最终静态原件核21文件、173本地链接目标及六个已加载秘密值，issues为空，空白检查通过、无新依赖。它覆盖上述更新前报告，不核锚点、Mermaid渲染、外链或运行行为；本次报告更新另核本地目标及空白，未把旧静态结果扩成新字节的全扫描。

本地两轴出口已满足，普通提交／推送、精确Git候选及自己的必要CI仍按后续同片证据核验，当前不宣布精确交付完成。[B2b／c与后续C／D](../plans/2026-11-12-six-stage-budget.md)保持各自出口；新v9的start／worker／Executor继续关闭，真实预算六阶段旅程尚未验收。当前可信容器仍不等于OS隔离。

私有两轴最终判词追加在 `b2a-spec-review-r2.md`、`b2a-standards-review-r2.md`。本次复核未运行测试、模型、安装或远端请求，也未提交。
