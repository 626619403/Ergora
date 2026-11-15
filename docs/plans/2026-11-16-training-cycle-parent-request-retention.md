# c1d：超限父请求的原字节留存设计

2026-11-16。**设计修订，待原 fresh reviewer 复核 R1／M1；未实现、未验收。** 本页只处理父端已生成、因超过32,768B而不能发送给业务 S/H 的完整 request。[权威 wire](2026-11-16-training-cycle-measurement-wire.md)及[容量分期](2026-11-16-training-cycle-measurement-capacity.md)的完整留存义务保持；不关闭完整 M1c，不开放 successor，不扩大 M1b storage-only。

最小建议：仅随**实际新 operation-v2 内部入口**接线。原 `_CycleOperation` 保持同次UUID／immutable raw，容量拒绝后沿原async生命周期启动无业务后代的诊断S。父端分块发送，S只写原 `request.json`，按原完整时钟语义监督、同步并重读后发一次小确认；父端核同次原raw SHA及真实wait才给诊断ref。正常S/H／SDK成功wire仍≤32,768B。**大raw失败流、诊断S direct-kill及进程内watchdog是待接纳的明确scope amendment，不能称为现有wire功能。**

## 权威、调查身份和邻片状态

已读根／源码／测试AGENTS、PLAN、组件协议，应用maintainable-project-delivery及ergora-codebase-quality的module-design/test-seams。原稿27,697B、SHA256 `6566ca5ba0c2c97fd6b55120706c2f0297a6ce210b7cf59459e7d8fe1eb72f5b`；[fresh首审](../delivery/2026-11-16-training-cycle-parent-request-retention-design-review.md)两轴request-changes，分别有R1／M1阻断。报告不改写，本修订不自称关闭finding。

首轮调查HEAD为 `59b74ceb4e3b90c2c875bb5eca56bbf8a102c384`，与指派基线 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b` 产品相同。原M1b九文件patch `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c` 未被本工作修改。本修订按M1b导入后的主树 `23ad171bf8228bf80b070d6ad866f79d63986d56` 核实际owner，不混用旧源码身份。

|原件|本次核得raw SHA256|
|---|---|
|权威measurement-wire|`ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|measurement-capacity（D1修正后）|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|`reference_training_worker.py`|`645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`|
|`training_execution_protocol.py`|`fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`|
|`budget_clock.py`|`6815a8c59dae720823ad10d2426776e0aa27eb0919478c02118ed3856ec622bb`|
|`processes.py`|`56c1961745b03ee4775e75f17dcb5a30a3d105e4bbd0f3fb516451e0fcd55867`|
|`tests/test_training_submission.py`|`d0d11c557c4982ef91b57fa3d4f8c2043707fdf46165d2b75043bb3cccaed54e`|
|`tests/fixtures/training_cycle_operations.py`|`03edbad39b2108fc09afbf5003124c5d109896cbdf46176843a3b60e9bfcb844`|

[M2／M3计划](2026-11-16-training-cycle-measurement-acceptance.md)修订SHA `2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff` 已获R1设计复核通过／开放0，在23ad171基线启动隔离实施。[邻片交付](../delivery/2026-11-16-training-cycle-measurement-acceptance.md)明确排除本项未接纳的父请求留存。本页不进入其实现树，不把邻片设计批准当成本项实现；schema3执行与ordinal1仍关闭。

本次只改本页，不改PLAN／报告／产品／测试，未运行probe、tests、history replay、模型、安装、网络、服务或训练，未commit／push。主控固定字节后交原reviewer同片复核；自身原模板及后续实施审查另记。

## 实际缺口与旧版本范围

当前 [`_CycleOperation.__init__`](../../src/ergora/reference_training_worker.py)先生成10字段identity／UUID，拼完整payload、验证，再以 `json.dumps(..., ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')` 得到 `encoded`。**request没有尾随LF。** 超过32,768B即raise，此时未赋output，没有S／request文件／H stdin。

正常链为 `_CycleOperation.run → _run → S → processes.run(supervised=True) → H`。S保存request，原唯一reaper先清理H后代，再发stopped／result；父 `PhaseFrames` 核完整identity／顺序，匹配stopped才允许过时后强杀普通S。普通request／result32KiB、stopped65,536B及该kill资格不改。

父caller包括 `_CycleCandidate` 的prepare／confirm／dispatch、`stop_live_controller`独立分支、`create_cycle_activities.invoke` 的cold／candidate／reconcile，构造在async父loop。现wrapper只日志异常文字，stop构造失败还换UUID；history／snapshot／sources不是这次原raw。不能重构子集或同步全payload日志冒充留存。

现成 `test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes[operation-request]` 证明可达：30,000字符reason使SDK入站合界、组装writer超界，五peer结束。原断言只核inline capacity failure、`operation_stopped=False`、`supervisor_returncode=None`，没有原raw。stdout／frame参数和occupied launch-intent测试保护其他风险。

**仅接新operation-v2。** 旧v1 constructor立即raise、stop fallback UUID、inline failure及普通路径保持；旧Workflow定义／commands／activity names／converter和25项GATE_SOURCES不改。旧测试预期保持，不宣称旧v1缺口修复。若旧v1也接入，会改抛错时机、ID、进程、延迟／取消和failure内容，须另获范围接纳、验旧真实history；不暗中扩大。

## 成功、未知及无法保证的边界

容量拒绝确定不启动业务H／root，不接受效果、不返还机会。父caller只暴露两种留存结果：

|父端实际证据|结果|
|---|---|
|S完成N字节与EOF、原fd fsync、目录链同步、同路径同inode／N／raw SHA重读；父在原window内收到唯一完整identity-bound确认、核同次发送SHA，全部pipe结束且S实际wait成功|`request_retention.status='durable_confirmed'`，给原request诊断ref。|
|上述任一条件未完成，包括原clock拒绝、partial／I/O失败、断管、取消／回复丢失、错绑定／SHA或未回收进程|`request_retention.status='unknown'`，不给完整ref；只保留原ID／目录、实际诊断wait及小错误事实。文件可能不存在、空、部分或完整。|

父内存持完整raw不是durable状态；S写完／重读完的局部事实不产生中间响应或父端状态分支。回复丢失时即使完整文件已存在，父仍unknown，不补造成功、不再发raw／业务效果。

有限deadline、磁盘满、I/O错误、强杀、掉电、不可中断I/O下不能无条件保证所有拒绝都留下完整可恢复文件，或fsync／回执按时完成。正常路径仍须证明完整raw成功；故障保留已有available／partial字节并unknown，**unknown不是留存成功**。若合同要求所有故障也无条件完整durable，则冲突仍阻断完整M1c，须主控处置；不能自行waive required gate。

## 明确待接纳的scope amendment

1. 新operation-v2容量失败增加 `ergora-training-cycle-request-retention-v1` 内部通道：≤32,768B控制封套、N字节原raw、EOF、一次≤32,768B最终确认。大raw不接业务parser／H／root／SDK成功结果，正常wire不放宽。
2. 同原operation目录exclusive写原 `request.json`；不增加第二持久状态文件、ledger／索引／表／恢复队列／后台reader、ID、机会或window。
3. 诊断S绝无子进程，父stop／原clock拒绝时可直接kill并真实wait，不等待H stopped；普通S/H kill gate／唯一reaper保持。
4. S内一个进程拥有的只读watchdog独立核parent及**原完整budget clock算法／整数window**，主线程阻塞或父loop不能调度也监督；只触发自身SIGKILL，不写raw、不跨operation存活。父持实际handle收尾。
5. 接纳上述truthful unknown故障合同，或保留绝对保证不可兑现的阻断；不能移除完整留存要求。

不接纳失败专用流，就无现成通路将大raw交隔离filesystem owner而维持正常32KiB界。不接纳watchdog，则父死且S主线程阻塞时父monitor／cooperative signal handler无法独立停写。另设受原reaper监管的纯诊断writer子进程会增加FD／进程接线，须另设计，不能暗换。拒绝必要修订时，来源原件与unknown是诚实退路，**本项未解决**。

## 最小控制输入与完整原时钟监督（R1修订）

控制封套固定为 `{protocol, identity, bytes, bootstrap, budget, deadline_ns}`：

- `identity`是同次已验证payload的完整原identity；`bytes=N=len(encoded)`，严格整数且N>32,768。只接受实际接通的operation-v2 mode，未知mode拒绝。
- `bootstrap`逐字投影原 `{boot_id, started_ns, deadline_ns}` 整数window或原null，不换新cold window。
- 原 `CYCLE_OBSERVATION_MODES` 的 `budget=null`，沿原 `cycle_operation_remaining` 冷观察语义只用原BOOT window。
- 其余mode的 `budget`恰为 `{clock, policy}`：clock完整保留 `budget_clock.FIELDS` 四字段 `authorized_at/deadline_at/boot_id/boottime_ns`；policy仅原 `wall_seconds/cleanup_seconds`。work使用cleanup reserve，其余total模式使用0。不携整snapshot／授权／sources正文或control_timeout。
- `deadline_ns=D`是只缩小原区间的额外整数上限，不是新window或原budget clock检查的替代。

父从已验证payload投影，进入前调原 `protocol.cycle_operation_remaining(payload)`。cold D≤原bootstrap结束；work D≤原bootstrap结束且≤原clock `boottime_ns+(wall_seconds-cleanup_seconds)*1e9`；stop／其余total模式D≤原clock `boottime_ns+wall_seconds*1e9`。若再以当前A+remaining缩短D，只能向下取整数并取原整数端点min，不因float上扩。BOOT与原parent boot相同；不重读当前配置、不重新authorize。

S复用 `protocol.decode/_exact/_process`、原identity shape、policy必要范围、`budget_clock.validate(clock, wall_seconds)` 校验小输入；不重新parse N字节或建立第二授权证明。projection仅供监督，**不替代原request raw**；最终父encoded SHA／原identity及文件确认绑定原件。

S主线程和watchdog共用一个同owner局部剩余量算法，实际调用原clock函数：

1. `budget_clock._clock()` 核原BOOT、原bootstrap的 `ticks≥started_ns`（有时），取原bootstrap deadline及D剩余。
2. 非cold每次都调用 **`budget_clock.remaining(original_clock, wall_seconds, cleanup_seconds if mode in CYCLE_WORK_MODES else 0)`**，与window／D取min。原函数核UTC与boottime的较大elapsed，并拒绝换BOOT、负elapsed、UTC倒退或两clock差>5秒；异常直接停止，不能退成只看D。
3. 剩余≤0、clock异常、完整parent identity／getppid不符或stop均终止同一S，不重新开窗口。父仍每次调用原 `cycle_operation_remaining(payload)`，不以小投影替换自身校验。

watchdog在输出filesystem操作前启动，每约50ms跑上述同一算法；主线程每次读／写／fsync／目录同步／重读／最终确认前后也跑。父loop不可调度且主线程阻塞时，UTC前跳／倒退／drift仍由S独立按原算法拒绝，**不等旧D才停止**。父恢复后不接受过时确认。采样不能撤销已进kernel的I/O，也非零延迟硬实时保证；已观察clock无效后不能再发起写或确认。D-state／停调度保留unknown并真实wait，不追加工作许可。

## 同次raw、N／EOF和唯一最终确认（M1修订）

产品落原worker的 `_CycleOperation` 与同文件私有subprocess entry，不建新module／ABC／通用storage层。entry隐藏async父已有raw向隔离storage进程的转移、blockedI/O监督；删去它这些义务会回到父SDK loop，非无内容转发。

### 父构造与发送

新v2生成一次UUID、验证原payload、同一次compact编码，固定output／payload；超界只记录本地拒绝事实，`run()`进诊断分支，永久禁普通 `_send`／H／root handoff。未生成完整raw的validator／encoder错误不在本合同内。已消费start/request/collect机会不退，不换ID／重试／推进ordinal或prefix。

父持原immutable `encoded`到S及全部pipe实际收尾；先发小封套＋LF，立即分块发N原bytes并关stdin，无前置响应。≤65,536B `memoryview`片逐块算同次原SHA，`write → await drain`并**显式公平让出loop**，复核原clock／stop；drain可能立即返回，不能假定其让出调度。不一次塞N字节，不复制O(N) raw，不写磁盘／全raw日志。

S用同一buffered stdin读有界首行和后续raw，避免首行预取raw后换reader丢字节。最多写N字节，再读一个额外字节核EOF；短读、额外数据、断管或原clock拒绝都无成功确认。S预检失败关闭管道，父send／read／wait沿原失败收尾。原文件只有N原bytes，无控制封套／其LF。

父算原SHA、S独立算接收／写入及重读SHA，最终比较足以检测错raw／传输或原件错连；没有实际reader或独立失效要求额外持久证明、中间响应或raw尾部digest，本实现不添加。原完整编码目前仍同步、需N字节memory；本方案不声称固定CPU／memory界。若实际producer证明编码本身阻塞stop，应另立原owner具体片，不暗改原raw。

### S文件及最终确认

S读有界封套、核原parent含getppid／小输入／clock，安装SIGTERM／SIGINT取消及watchdog后才碰输出filesystem。它从不spawn，不进业务H/root，不调用State／业务安装／SDK服务／模型／训练。父可直接kill它，普通S/H仍依原stopped资格。

固定原 `control_home/operations/training-cycles/<operation_id>`；沿可信用户边界复用无symlink／reparse／普通目录检查。目录exclusive0700、文件O_EXCL/O_NOFOLLOW0600并核普通文件；已有目录／空或partial文件不覆盖、删修、重建或扫描别的operation。`protocol._fd`／`sync_directories`是逐路径检查／同步，不构成并发替换全部祖先的原子目录capability或永久防篡改；不暗改全局reader威胁模型。

按≤65,536B接收、write循环和SHA，short write／异常留下已有字节。N与EOF完整后flush／fsync原fd，复用 `protocol.sync_directories(output, control_home)` 同步目录链；安全重开原路径核同dev+inode、普通文件、N、逐块raw SHA等于接收SHA及EOF。不读回N字节memory、不用默认1MiB `read_raw`、不重新JSON编码。最后核原文件身份／clock／parent，发**唯一一行最终确认**并退出。

确认固定 `{protocol, identity, ref}`；protocol为诊断版本、identity完整等于原identity，ref恰 `{file:'request.json', bytes:N, sha256:raw_sha}`。完整JSON行（不计delimiter LF）≤32,768B；超界不发。write／sync／重读／确认异常即停止，raw不添错误文本、不截短冒充成功；stderr只留有界小错误。

父严格收恰好一帧及EOF，核shape／完整identity／文件名／N／SHA，无额外帧或残余；不喂 `PhaseFrames`、不伪造H stopped。仅发送task完成全部原bytes和EOF、父SHA匹配、全部pipe结束、S wait成功、父原clock／stop最终检查通过才给durable诊断ref。S无需预知父SHA：确认另一份bytes会被父最终比较拒绝，不产生业务或诊断接受。

### 生命周期、peer及发现入口

spawn／send／stdout stderr drain／wait沿原run取消持有：cancel请求stop，不丢handle，反复shield并恢复被loop teardown取消的观察任务。S内只读watchdog随S退出，不是父executor不可取消写线程；parent SIGKILL后仍独立监督。SIGKILL／BrokenPipe不等于stopped，必须实际wait。

业务始终 `capacity_exceeded`，原ID／mode／ordinal／output保持；`operation_stopped=False`、业务 `supervisor_returncode=None`表示没有业务H stopped。诊断wait／returncode内聚 `request_retention`，不做通用process ledger。`operation.result_ref`仍只允许 `helper/stdout.txt`≤32KiB；大request诊断ref不进入该字段，不伪造 `_stdout_ref`／permission／acceptance。

所有可运行peer先起task，各自通知／排空，不等一支留存storage。finally向全部operation请求stop并等实际task后才上抛非重试容量失败。不可中断I/O可能使wait晚于deadline：记录unknown及未回收identity，不虚报硬实时cleanup，不续任何许可。

发现入口在 `_CycleOperation` 诊断最终收尾点：用原worker logger逐operation输出有界记录，含原ID、mode／ordinal、output、留存结果、已确认小ref及实际诊断wait，不格式化全payload／大reason。caller沿 `_activity_operation_result` inline失败或所属内部operation结果携这份小事实，不加索引。SDK仍小非重试错误，不加raw正文details；若后片扩大Failure，须真实failure converter／完整protobuf owner核界，不能以成功Payloads `_cycle_capacity`替代。引用集装不下则逐operation日志留下，整体未完整返回仍unknown，不裁成成功／放宽wire。

## 资源、替代与实际caller前置

raw为父实际已存在的有限N；S最多写N，控制／确认各32KiB，pipe／S额外memory O(65,536B)，无另一份整raw。不保证任意N可存或window足够，不增10MB诊断成功配额、无限disk预留、GC／全局存储合同。要求固定disk界时须另定准入／生命周期；不能同时无条件保存任意超界raw，不能用截断掩盖。

|已有替代|不直接适用的原因|
|---|---|
|普通S／PhaseFrames|S先读limit+1拒绝；放宽扩业务transport，伪stopped削弱H回收资格。|
|`processes.run`|spawn前同步mkdir及全量写stdin；SDK loop不受管，普通S也不能靠尚无H监督。原业务H继续用它／唯一reaper，不把lock_fd冒作raw fd。|
|父executor写线程|取消future不能停blockedI/O，loop teardown后可能仍写；可kill／wait的S才能收束写owner。|
|history／sources重构／全日志|不是同次raw／UUID，全日志还阻塞loop；仅相关来源。|

不孤立落future helper。M2／M3获准内部v2并启动实施，但排除本项；待其真实producer／mode／source／snapshot／window落定，本项获范围接纳及复核后作为后继最小片接入。来源认证未成立先解决caller合同，不能伪context／删认证／用fixture冒充生产入口。v3注册／V2 dispatch／执行开放留后片，不提前打开、不继承邻片通过。

## 最小验收，全部未运行

沿现有 `tests/test_training_submission.py` 的 `cycle_operation_fault`／`cycle_sdk_activity`及 `tests/fixtures/training_cycle_operations.py`；不加文件／CI job。原fixture会全read再JSON parse，**不可原样包诊断流**；按新entry准确argv分支进入真实流，保留async父、S/watchdog、磁盘、wait，不mock“saved”。

|风险|最小真实证据|
|---|---|
|输入合界、完整新request超界|实际producer截同次encoder作oracle；文件逐字一致、N／SHA／UUID／parent／来源完整，multibyte且无LF；无H/root／attempt／launch／prefix效果，不退机会。|
|32,768／32,769B分流|真实普通S/H及诊断owner；前者正常wire，后者始终业务拒绝；封套／最终完整确认也核整体界。|
|partial／short write／ENOSPC／断管|真实S fd失败、前缀保留、无完整ref／重建；父显式公平／heartbeat，peer继续通知／排空。|
|sync／重读阻塞及inode/raw冲突|原window监督同一S并真实wait；换inode／raw不能确认，既有空／partial不修补；保护范围按可信用户边界。|
|R1原clock无效但D未到|实际S内进程局部时间接缝使原 `budget_clock.remaining` 观察UTC／boottime drift而拒绝；BOOT／D仍有效、父不能代查、主线程阻塞，watchdog真实终止同一S、无确认。不只测parent最后检查，不复制整clock矩阵。|
|创建／发送取消、最终reply丢失|实际spawn／pipe／wait保持；raw可能partial／完整但父unknown，不重发／再spawn／退机会。错SHA或额外数据由N／EOF／最终比较拒绝。|
|parent真SIGKILL且S阻塞|有界外层真实强杀parent；watchdog独立核完整identity消失、自终止并核absent；async cancel不替代，D-state不认证硬实时。|
|stop一支失败、peer收尾|原6分支及必要时N32聚合接缝；每个原ID、全部真实task后非重试失败；诊断wait不叫H stopped。|

可合并既有参数化，不为错误文字／chunk helper／合法字段加矩阵。至少实际新producer原raw成功及真实async父／S故障收尾；临时测试operation不证明生产caller。旧v1 request/stdout/frame、取消／spawn、blocked-stop、三份原history按实际影响选兼容检查，不重跑无变化全suite。固定新非editable安装另验，源码／安装／替身／真实现场分开；M1c-V/M6全SDK／Memo／query／signal／outcome不由本项替代。实施另走fresh两轴及自身原模板，不继承M1b／c1c。

## 修订与闭合

R1修订提供S实际所需的原clock四字段、policy两字段、原bootstrap及整数D，主线程／watchdog持续调用原 `budget_clock.remaining`；M1修订只留原raw、N／EOF及一次identity-bound确认，父以同次分块SHA验证，没有无reader第二持久状态或无producer中间成功状态。是否关闭finding由原reviewer复核，原request-changes保持。

主控处置scope、固定字节复核后，在真实新v2边界实施。闭合须同次exact raw／UUID、完整原clock／window监督、无H/root／机会返还、故障unknown、全部peer／诊断进程真实清理及旧v1／history／25来源保持的准确候选证据；其他完整M1c和执行gate分别待验。

不接纳失败通道或仍要求磁盘／deadline故障下无条件完整durable，则本项未解决、阻断完整M1c；M1b、M1c-T及获准M2／M3按各自范围推进。来源齐全、文件存在、size probe、这份设计均非留存验收。
