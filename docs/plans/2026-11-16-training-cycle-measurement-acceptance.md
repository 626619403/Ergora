# c1d M2a：H 四事实接受与 M1c-O 的实际消费边界

2026-11-16。**具体设计，待 fresh 独立需求／维护性审查；没有产品实现或验收。** 本页建议把 M2a 的只读接受与 M3a 的内部 collect／reconcile 用例作为一个实现片审查，SDK v3 注册、V2 producer 和执行开放仍留后片。接受该分片调整后才实施。设计遵循 maintainable-project-delivery、ergora-codebase-quality 的 module-design／test-seams 及 independent-review brief。

权威仍为[原测量／索引要求](2026-11-16-training-cycle-measurement-and-index.md)、[wire 合同](2026-11-16-training-cycle-measurement-wire.md)及其[已接受复审](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)。wire raw SHA256 为 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`。[M1c 分期](2026-11-16-training-cycle-measurement-capacity.md) SHA256 为 `c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`，[审查](../delivery/2026-11-16-training-cycle-measurement-capacity-design-review.md)仅认可真实消费者分期，未豁免完整留存、实际容量或最后准入。

## 调查身份与不能继承的结论

调查主树 `refactor/architecture-foundations`／`59b74ceb4e3b90c2c875bb5eca56bbf8a102c384`；相对 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b` 没有 src／tests 差异。主树已有 M1a 的 `protocol.ARTIFACT_LIMIT=10_000_000` 和纯 round-content 校验。[M1b](2026-11-16-training-cycle-v3-birth.md)产品仍在隔离树，准确九文件冻结 patch SHA256 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`；这里只读核其 schema3 关闭点，未修改或重跑。其源码审查与安装／自身模板验收分别记账，不能据本页称 M1b 已交付。

|调查的主树文件|raw SHA256|
|---|---|
|`reference_training_worker.py`|`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`|
|`training_execution_protocol.py`|`bd5f1b2878c533aeadd6e69d2c5b3a830e52b135f808e12d283f9251c8068a09`|
|`training_rounds.py`|`ad9fba3d3f675ec0a91dc07a4224852482e0b75730218b5feaecb3f342abe310`|
|`reference_training_evidence.py`|`1ffce17c7a6e7747d33e9544f5eade399565f6bf9443eb94a00083feb681580a`|
|`reference_training_runtime.py`|`1183a95c53a9550789983e245676a46637b5de748ddf32eb0ec5df9def46458a`|
|`reference_training_release.py`|`bba8cd011f7aec0a79f596e7898e3daa84afa7f375c8f0394a622c4255b5ab62`|

开始实现须以已完成验收、已确定导入身份的 M1b 候选重核实际差异，并接收 M1c-T 的准确候选运输记录；不覆盖其原失败或未验范围。本页不改变 PLAN、产品、测试、冻结资源或 CI。

## 最小完整片为什么需要调整

当前实际生产链是 `create_cycle_activities.invoke → _CycleOperation.run → cycle_operation_main(S) → processes.run → cycle_operation_main(False/H) → _cycle_operation`。普通 request／observe 再调用 `_execution_candidate_operation`。后者已有完整 runtime、native 与 ExecutionRecords 观察，但没有 evidence／rounds。旧 `_cycle_operation` 末尾写出的 observation 只是 pretty 编码的 stop-chain 观察；它的旧 shape、路径意义和返回合同保持。

当前不存在 collect mode、v3 SDK 活动、V2 Workflow。M1b 在 `_cycle_operation`、`BudgetedStart.source` 和 `validate_context` 明确拒绝 schema3 live；旧活动及 operation snapshot 还只接受旧版本。不能添加一个序列化函数、用测试调用它，再称已有消费者。完整新 observation 的 prefix 来自本次实际 index；完整 acceptance 要依赖 index 持久确认，跨 operation 的 ref 重读又是 reconcile／predecessor 的责任。原 M2a 单独的“只读正面谓词”不够关闭 M1c-O。

|方案|准确创建／调用入口|范围与判断|
|---|---|---|
|A：M2＋M3＋部分 v3 SDK|提前在 `create_cycle_activities` 创建 v3 closures，再在 `_serve_cycle` 原 worker queues 注册；closures 构造 `_CycleOperation`|实际注册越过 M6；没有 V2 历史 producer，合法父运行与 collect history 仍不存在。增加未启用注册项不能解决正式生产调用缺口；不推荐。|
|B：M2＋M3 的完整内部 operation 用例|已有 `_CycleOperation` 构造完整 operation-v2 请求，已有 S/H 可执行入口严格分派 `collect-round/reconcile-round`；`_cycle_operation` 分支直接调用私有采集、原 rounds 和观察写读逻辑|推荐。用例入口是现有进程协议／构造器，不新增 `collect_cycle_round` 包装器、服务或 SDK stub。明确交付的是内部用例与真实 S/H 接缝；SDK 生产 creator 尚不存在，留到 M6，不能称活动端到端已验。|
|C：先补齐 V2 与所有执行前置|M5 的 intent／budget／native 最后 gate，加 M6 的 V2 commands、活动注册和正式 dispatch，才产生真实 schema3 父／子 run|能提供正式端到端调用，但把多个需独立审查的生命周期片合为大改动。本片不采用；最终开放仍必须走此依赖顺序。|

**推荐 B 不以潜在 SDK caller 充数。** `_cycle_operation` 是新增私有接受／保存算法的实际生产 caller，S/H 的进程入口和原 `_CycleOperation` 是内部用例的边界；同文件内的调用只说明归属，不声称多处复用。若移除私有算法，四事实绑定、fd 生命周期和拒绝处理全部会回到该分支，故它们是内聚私有算法，不需要新模块或接口族。完整用例由模式严格选择，既有可执行入口可接收该模式；目前正式产品没有能产生合法 V2 source 的 SDK creator，这一缺项单独保留。

本片最多把 schema3 的**这两个测量用例**纳入 operation-v2 的完整内部语义，不开旧 cold-H、prepare／dispatch／request／launch 或 native。测量仍须 ready、原父 RUNNING、完整真实 source、原窗口及 stop 检查；没有真实父与原记录时正常结果就是拒绝／unknown。不能把旧 schema2 的原实验换绑到新授权以凑正例。内部接缝中替换外部服务、构造原件的正例只证明该接缝，不证明现场 schema3 已运行。

如果独立审查认为在这些执行前置关闭时不能单独交付该内部用例，则本页只交付设计，实际组合实现顺延到 M5／M6 联合候选。不得为通过审查额外开 live 或以测试入口替代生产 creator。M2a、M3a 原编号及各自义务保留，合片交付记录须逐项给结果，不把 M1c-O 或全 M1c 自动关闭。

## 文件归属与严格验证的 owner

|已有 owner／拟修改点|实际调用者与职责|不移动的责任|
|---|---|---|
|[worker](../../src/ergora/reference_training_worker.py)：`_CycleOperation`、`cycle_operation_main`、`_cycle_operation`|已有构造器／S/H 执行链增加 operation-v2 严格模式；collect 分支持有四事实组合、index 同步、最终 observation、投影和状态；reconcile 实际读取已有 artifact／观察|不增加第二 supervisor、reaper、时钟、队列或 controller 状态机；不在 SDK async loop 读取／写入大文件。|
|worker `_execution_candidate_operation`|collect／reconcile 用只读分支取得完整 runtime／native／execution 以及原八字段 facts；只保留有实际调用的最小私有提取|不能让 collect 模式落到 `Execution.request()`；旧 request／observe.v2 返回不变。完整值在 H 内消费，禁止把它们直接塞进 stdout。|
|[protocol](../../src/ergora/training_execution_protocol.py)：现有 cycle validators／`read_raw`／`sync_directories`|S/H validator 严格区分 operation-v1／v2、schema2／3、新 mode／context；新观察／ref 的严格 shape 与本地交叉绑定在此作为现有协议的一部分，被 H 写后重读及 reconcile 使用|不导入 State、SDK、rounds、jsonschema；不复制 archive reader。只增加本片真实 H 消费的校验，M5 本地前驱／native gate 仍另验。|
|[rounds](../../src/ergora/training_rounds.py)：原 `create/read/_check`|H 仅按原 API 每次新增一轮，read 负责完整 JSON schema；M1a `validate_round_content` 保持纯内容归属|不加 snapshot 注入、不改公开参数／pretty 编码／coverage，不新建 trusted reader。CLI／离线历史兼容保持。|
|[evidence](../../src/ergora/reference_training_evidence.py)／[training.evidence](../../src/ergora/training.py)|collect／rounds 原调用，`artifact=None`，完整 accepted archive 语义由唯一原 reader 验证|不在 H／protocol 复制 perfctl、baseline_ok、比较器或重读全部 artifact 正文；原 reader 上界不变。|
|[runtime](../../src/ergora/reference_training_runtime.py)：`lookup/observe`|H 认证固定子 run、完整 spec，再读真实 Status／Outcome；新增 collect history 读取留该现有 SDK runtime owner，由 H 调用|不让 native 查 RPC，不追 latest／follow-runs，不通过 local approval 推 phase。|
|[release](../../src/ergora/reference_training_release.py)／`training.approval`|只有 rounds 原 `status` 读取 local 记录|不 approve、不创建 receipt、不 request_release、不产生 integration task。|
|[budget](../../src/ergora/reference_training_budget.py)／[execution](../../src/ergora/reference_training_execution.py)|本片只读取现有能力与记录；现有执行 gate 保持关闭|schema3 最后 source／predecessor／context／native 和原锁内动作全部属 M5；不为本片放行。|

B 还需要把 M5 中仅供读取的 binding 格式接缝提前：当前 `validate_budget_binding` 只认 v1 五字段 controller，`_cycle_target → CycleAdmission.bind` 因而不能读取新六字段原 intent。protocol 以封闭版本分支核 v1 旧键／v2 新键，后者必须有 predecessor；`CycleAdmission.bind` 按授权 schema2／3 与原 parent protocol 严格匹配并保留原 selected admission／receipt 关系，H 再核完整前驱。此处只是新内部测量读取的必要前置，须随 B 一同设计审查，不是把 M5 最后执行 gate 提前宣布完成。`BudgetedStart.source`、`validate_context` 的 schema3 拒绝及 start／request／adapter／native 关闭仍原样保留；缺这些关闭点的候选不进入本片验收。

预计产品 diff 仅 worker、protocol、runtime；测试沿原 submission／evidence fixtures。若实际需要改 rounds/evidence 的公开合同、新 source 路径或额外文件，先提出具体不可满足的调用证据再扩审，不默默扩大本片。

严格键集沿 wire：request、identity、context、facts 八字段及其原嵌套键均由 protocol 外部输入边界核；新 observation 恰为 `{schema_version,kind,identity,activity_context,predecessor,selection,facts,runtime,native,execution,evidence,prefix}`，schema_version 为 int 1，kind 为 `training-cycle-round-observation`。未知键、重复 JSON 键、NaN／Infinity、bool 冒充 ordinal／长度均拒绝；沿原 `decode/_exact/_digest`，不另写 JSON parser。完整 runtime／native／execution／evidence 沿各原 owner 的结果，不人为发明一个删字段的 archive schema。

接受投影、prefix／observation ref 与 selection 的精确键集仍以 wire 为唯一合同；新协议 validator 同时核 shape 和原值关系。业务接受谓词只由 H 组合，rounds schema 和 native 纯内容检查均不自行授权。M6 才实现新 SDK 封套／V2 收到结果的严格验证和整体容量检查；旧 V1 `_consume` 当前没有整体容量重查这一事实保持，不顺带改旧历史。

## collect／reconcile 的完整数据流

1. **既有 S/H 准入。** 完整 operation-v2 identity 保持原十字段，payload 继续包含原 snapshot、window、`start_context.controller` 和三字段 activity_context。新增两 mode 只接受 schema3、v2 controller、新 collect／reconcile.v3 的精确 type／queue／namespace／attempt，并逐一核 input／authorization／parent process。不能用 `schema_version>=2` 放宽未来版本。旧 v1 mode 与旧字段集合继续各自拒绝新键。
2. **原机会与真实父。** H 经原 controller receipt／intent／attempt 认证固定父 run，沿原 `lookup_controller` 要求 RUNNING；不能以 caller 传来的 context 为历史证明。collect 只能来自该轮固定 `candidate-<k>-collect`、attempt1 的真实原 `ActivityTaskScheduled`；核精确活动名、queue、完整 `{workflow_input,ordinal,predecessor}`，唯一命令和原输入。reconcile 核同一历史事件但永不 create；SDK attempt>1 只能对账。不得增加本地 collect-attempt 文件补机会。
3. **先前前缀。** k=0 的 predecessor 为 null；k>0 必须为原请求／已出生 candidate intent 同值，读完整准确 previous 与所有已确认 prefix，恰为冻结列表 0..k−1、原注释／manifest、共同 `_COMMON` 和 initial anchor；禁止按目录扫描、挑短前缀或以一个 SHA 声明代替逐项相等。这里是 H 的测量必要条件；M5 才把它接到每个不可绕过的执行最后动作。
4. **采集前来源与预算。** 在 H 内核 ready、项目 revision／registration／执行路径、授权四项 measurement_sources、原 candidate owner 的固定 25 项 capability、所选 installation 和 descriptor、包内 ROOT 283 个原文件；确认父 stop 不可见，原 BOOT／work／operation 剩余为正。先核 pinned reference manifest 身份再 `reference.verify()`，不能只验证安装或读当前 manifest 后自认冻结。原 capability 的形成时点与授权四项形成时点不混称同一冻结瞬间。
5. **四事实 preflight 与先行诊断。** 复用只读 `_execution_candidate_operation` 和 `training.evidence`；绑定表见下一节。每份完整 runtime／native／execution／evidence reader 值一旦取得，在进入下一个可能失败的 reader／index 操作前，由同一受 S 监督的 H 将该完整值编码并 flush 到原 `helper/stderr.txt`（具体规则见下节）。不等四份齐全或 prefix 形成，也不只保留 facts 摘要。对不能完成原观察的分支保留已取得真实结果／错误，不能从异常文案猜 pending。读取原 source 与实际 source 的 API 都留在各 owner；不得通过 status/reconcile 生成同意、重建 owner 或 source hashes。
6. **唯一 index 用例。** collect 在本次唯一 publish 机会、原 work window 内对确定性 `controller/rounds/<k>/` 调原 `training_rounds.create`，只给本轮 `experiment_id/change/next_bottleneck` 和准确 previous pin。目标若已存在，只 read／比对；竞争输家同样只读胜者。reconcile 缺目标／部分目标／坏 SHA 一律 unknown，不 create、不换路径、不修文件。明确负面但完整可读的失败轮可由同一机会保存低覆盖 index，永不 ready；没有完整原值时不伪造空轮。
7. **index 最终核验。** create 会重新调用 inspect／evidence／submission／approval，必须验证最终 index 的那份 native 观察。用最后轮 records／evidence／submission 绑定原链／固定 run／原 spec／manifest／job；approval 只观察其原 status，不把人工决定变化视为测量授权。此前完整 prefix 与原 actual previous report 逐项相等，previous_report 三字段与原件相符。索引不可变；最终捕到 no archive、错 run、baseline drift 或 prefix 冲突不能修补它。
8. **持久确认和最终事实。** 以实际 rounds.json fd 取 raw／dev／inode，经原 read/check 后 fsync 同一 fd、index 目录及至原 cycle 根的目录链；重开相同路径要求同 inode／同 raw／同 raw SHA，再用原 rounds.read 核相同完整 prefix。重新采原 runtime／native／ExecutionRecords／evidence，确认它们与最终 index 的稳定原事实／完整 files 绑定。phase 允许原合法状态变化，local approval 不作为接受条件；不能拿 preflight 的正面数据给最终失败 index 盖章。
9. **完整 observation。** 用本次最终完整四观察、原八字段 facts、完整 selection、真实 prefix pin 和准确原 source 构造单文件；prefix 没有形成时不生成可接受的完整 observation／ref／acceptance，也不伪造 prefix pin。已取得的完整原reader值此时已经在步骤5及每次重新采集的原 `helper/stderr.txt` 中；不能靠现有外层catch的status/reason声称保留了RPC detail。原子文件发布与字节／同步规则见后节。observation 不包含 measurement、acceptance、自身 ref 或累计 index 正文，不把此前完整观察递归嵌入。
10. **发布前再核。** index 同步后、完整观察同步重读后，均核同一 measurement_sources／capability／ROOT／安装身份、原项目、父 RUNNING、stop、原 BOOT／work／window。所有正面条件、durable index 和观察 ref 都齐全才可在内部结果形成 accepted／durable 投影；当前产品执行开放仍受 M5／M6 门禁。任何输出／容量／丢回复都不能推进 history 的 prefix／ordinal。本片没有能推进它们的 V2 producer。

步骤 2 的实际 SDK scheduled-event／decode 是新的必要接缝：留 runtime 私有内聚算法，沿原 handle stream 和 client DataConverter，以相同原 window 消费最多 8000 events／8MiB 原 history，不新建 history 库。RPC、decode、页读取或容量未完整成功就是 unknown。没有 V2 正式历史前，只能在保留真实 SDK event／converter 的替身原服务上核这一算法；正式运行与丢完成恢复须在 M6／真实两轮再次验，不能以该替身证明发生过发布机会。

## 四事实必须共同绑定

|原事实|必须读取的完整值与正面条件|典型错配与结果|
|---|---|---|
|runtime|原 receipt 固定 Experiment run、完整 started input、memo=start intent SHA、真实 namespace；RUNNING／非 terminal 的 AWAITING_RELEASE，`status.evidence_sha` 等原 archive SHA；或 COMPLETED／terminal 的 RELEASE_EXPIRED／INTEGRATION_TASK_CREATED|Outcome 不存在 evidence_sha 字段；其 `report_uri` 必须为原 native result.gate.report 的准确 `Path(...).as_uri()`。不能编造 gate_report.report_uri 或 Outcome.evidence_sha。错 run／job／memo／namespace、不可认证 outcome 均 unknown。|
|native|`LocalTrainingAdapter.poll_job` 完整 asdict，state 严格 SUCCEEDED，job 等原 ExecutionRecords.request／完整 native request／runtime job|native SUCCEEDED 单独不 accepted；FAILED／CANCELLED 保留原失败、rejected；QUEUED／RUNNING 只在原事实可信时 pending。|
|execution|`ExecutionRecords.load → request_record → observe(durable=True)`，保存 owner、五 records、完整 record_sha256 和 raw_sha256 inventory；原 request／launch／attempt／ack／stopped 齐全，durable_stop_confirmed 与 executor_stop_confirmed 均严格 true|owner 不必仍活；不得以 PID 消失、H 停止、父 drain、ack 或 stop_observed 代替原 durable stopped。原 observe 目前只做 fsync＋raw 重读，不能声称已核同 inode；本片新 observation／index 的同 inode 确认单独实施。|
|evidence|`training.evidence(artifact=None)` 完整成功；archive_status=recorded、原 gate.passed is True、原 recorded_result_state=SUCCEEDED、baseline_matches is True、无 fence；原 raw manifest／baseline snapshot、comparator、archive gate、evidence content address 和完整 files 映射一致|原 reader 缺 archive 或负 gate按真实状态保存；错 archive／坏 source／reader 失败 unknown；原 gate 明确 false 为 rejected。保留 artifact_content_status=not_read，不称 artifact-wide 或训练质量认证。|

额外共同键：同一 home／project／cycle／input／authorization、controller original run、ordinal、冻结 selection、revision／registration、candidate manifest／binding、完整 start attempt／receipt 和 native request raw／semantic SHA。`common_sha256=C(原 manifest 的完整 _COMMON 对象)`，`measurement_sources_sha256=C(出生固定四项映射)`；不改比较阈值、normalization、statistics、quality_required 或 performance_policy。索引当前轮及注释逐字来自原 plan，不能只核同 commit 就认为同一测量。

四项 measurement inventory 是 `training_rounds.py`、`reference_training_evidence.py`、`data/schemas/training-rounds-v1.json`、`reference_training_release.py`。release/status 即使不授权也会在有写权 H 的原采集链加载，不能漏 pin。原 25 项 `GATE_SOURCES` 精确集合不扩展；若本片实际再引入持接受权的新代码文件，先扩审四项固定表，不能用任意路径配置或当前哈希替代出生值。

## M1c-O：完整写入、实际重读及失败语义

`M=protocol.ARTIFACT_LIMIT=10_000_000`；rounds 的 `MAX_INDEX_BYTES` 继续 alias。新单文件最终 raw 恰为 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'`。UTF-8 无 BOM、一个末尾 LF、有限数字；bytes／raw SHA 包括 LF。rounds 的原 pretty／content SHA 算法不变。

### R1：prefix 之前失败也保留完整已取得观察

[首轮独立设计审查](../delivery/2026-11-16-training-cycle-measurement-acceptance-design-review.md)发现：完整reader结果仅在H内存，`rounds.create/read/fsync`失败时原外层catch只输出reason，原chain也没有Status／Outcome的RPC detail。修订明确沿 `processes.run` 已直接打开并传给H的stderr普通文件描述符保留资料；不新增诊断文件、账本、观察schema或权限。以下是新增两mode的实际H责任，旧operation-v1不变：

- 每次reader返回后、继续下一易失败调用前，直接向H的 `sys.stderr` 写入一条包含该reader名称和**完整原返回值**的UTF-8 JSON记录并flush；使用finite、无BOM、单LF的既有JSON编码规则，所有detail／files／raw库存不截断。每次重新采集的原值分别追加，不能覆盖前次或只在函数最终返回后写一条。其调用点留在实际取得该值的worker路径；若提取原只读逻辑，必须把留存接在每份原值赋入内存的位置，不能等另一个owner已经失败。
- 原 `processes.run:157–164` 直接将 `helper/stderr.txt` 的fd作为子进程stderr，故这份完整资料不经过父 `_CycleOperation.diagnostics` 的65,536B内存上限，也不放入H stdout、32KiB帧或SDK envelope。H内JSON编码／写／flush全部在原S监督和同一原window中；不在SDK async loop写大日志，不增加时限或额外子进程。
- 若编码／写／flush失败或被原deadline终止，停止采集／发布并返回unknown；available原chain与已写前缀保持，不能声称未写完的值已完整保留。普通flush只证明成功时已交给原文件fd，不证明fsync、同inode持久确认或重启后的可用性；此诊断绝不生成合法observation ref／acceptance／ready，不被后继reader当证明。正式完整observation的M界和durability仍按原规则执行。
- 验收须由真实H先取得含独特大detail的runtime及其他完整值，再分别让后续reader与index create/read/fsync失败，核原operation的 `helper/stderr.txt` 仍能解出此前每份完整值、无合法ref／acceptance；至少一次原S超时／取消只按实际partial范围记账。不能以外层reason或磁盘原chain存在代替这一检查。

这是R1的最小owner修订；原审查的request-changes保留，须由同一reviewer复核后才可记录闭合。M1b现已固定并普通导入 `23ad171bf8228bf80b070d6ad866f79d63986d56`，实施基线将绑定该已验产品及本修订；上文原调查SHA仍是其当时身份，不替换为新字节。

文件路径只由原 operation ID 派生为同一 home 的 `operations/training-cycles/<operation_id>/helper/observation.json`，原 operation ID 为 32hex；普通路径、祖先目录和文件身份沿原 safe/open owner 核验，拒绝 link／非普通文件／根逃逸。用 `xb` 写完整 raw，不能覆盖前次文件或把旧 stop-chain observation 转成新 shape。容量判断是完整单文件合计界，不给 runtime detail、files 或单个原记录叠更小的配额。

- `0<len(raw)<=M`：保存完整 raw，flush／fsync 同一文件 fd，沿原 `sync_directories` 同步 operation 目录链至原 operations/training-cycles 根；关闭后重开同路径核 dev+inode、完整 raw／bytes／raw SHA。写、同步、重开与最终 gate 全消费同一原 window。仅此后才可生成观察 ref，且 acceptance 还需完整 durable index。
- `len(raw)>M`：同一原 H 在原 S 监管下尽量保存**完整**原 raw 为 diagnostic；写完也不产生合法 observation ref、acceptance 或 ready，原 index／reader outputs／chain 全保留，返回 capacity failure。不能截前 M 字节、切附件、压短 detail 或重新写一个更小“完整观察”。若完整写入没完成，不声称已保存完整原件。
- write／fsync／同 inode／raw 重读／deadline 失败：已有文件不删除、不 repair，不换 operation 重放 publish；只能 unknown／published_unconfirmed，available originals 与原错误保持。被 S 终止时由原 reaper 处理 H／后代，stopped 之后禁止再 spawn reader。无结果 frame 或父收到不完整 frame时仍 unknown。

**本片真实 reader**：collect／reconcile 写后确认，以及 k>0 时两用例对原请求 `predecessor.acceptance.observation` 准确引用的完整读取，调用 `protocol.read_raw(path, ARTIFACT_LIMIT)`，先核 ref bytes 为 int 且 `0<bytes<=M`、准确固定路径、实际完整长度及 raw SHA，再 `decode` 与严格原事实绑定；读端不重编码计算 raw SHA，不用默认 1MiB。严格新 request 没有“本轮旧 observation ref”字段，不能为了恢复另加一个。reconcile 对本轮只用确定性 index＋原 collect scheduled event 重新采本次观察；收到过的前轮引用只来自原请求／已出生 intent 的 predecessor。SDK completion 丢失不知本轮 operation ID 时不扫描旧 operations 来猜 ref。

M5 后继 H／`CycleAdmission.bind/BudgetedStart.source/validate_context/Execution.current/native` 的同 ref 消费仍是 M1c-R，不能由这里的写后重读代验。该 reader 是现有 protocol 内的严格协议算法，不是新的可被 arbitrary path 调用的 trusted archive reader。超 M diagnostic 没有合法 ref，任意传入也必须拒绝。

新的 H stdout 与 S 最终 result frame 沿 32,768B 完整编码界；stdout 计 LF，frame 计完整 identity／result／`_stdout_ref`，不计其分隔 LF。新 wire 接线需在替换 capacity failure 后再次核完整 frame；不合界就没有成功 result，保留原 stdout／stopped。65,536B stopped 控制帧不变。不能凭一个 synthetic 大 replacement 宣称已找到现有可达漏洞。

SDK 完整 assembled envelope（facts＋selection＋measurement＋acceptance＋所有 operations＋外层 identity＋metadata）仍须 `_cycle_capacity` 用实际 DataConverter／Payloads 整体核 32,768B，禁裁 branches／换未定义附件。B 没有 v3 SDK invoke，故这部分明确留 M1c-V／M6，不以旧 V1 或局部 helper 通过关闭。exact oversized parent request 的完整留存仍未解决：`_CycleOperation.__init__` 超界先于 S 和 output 目录，原异常日志不保存完整 assembled raw；不得在 async loop 加大同步写／日志、无监管线程／进程或新窗口。本片不得称全 M1c 闭合或允许 successor。

## 状态、恢复和旧兼容

|可观察结果|measurement／index／continuation|保持的原副作用|
|---|---|---|
|四事实正面且 index／观察同 raw 持久确认，所有最终 gate 成功|内部可形成 accepted／durable 与非 null prefix／acceptance；只有完整原谓词成立才可能 ready|不等于已开放执行；M5／M6／全部 M1c／真实验收未闭合时原执行 gate 仍拒绝。|
|四事实正面但 index fsync／重读未确认|accepted／published_unconfirmed，ready=false、acceptance=null|index 原件保留；下一 reconcile 只确认同一 artifact。|
|原 gate false，或 native 明确 FAILED／CANCELLED|rejected，ready=false；可保存同机会的完整失败低覆盖轮|原 result／gate／证据和既有 prefix 不改，不 approve／release／rollback。|
|可信非终态／等待原 reap|pending，ready=false|只在原 window 内读；不续 clock、不自动新 request。|
|缺事实、身份／source／ROOT／stop／raw 冲突、RPC／decode／编码／容量／时钟错误|unknown 或明确 capacity failure，ready=false、acceptance=null|不把错误降格 pending，不返还原 start／request／collect 机会，不删坏目标或消费较短 prefix。|
|publish 后丢 H／SDK completion|history 不增加 prefix／ordinal；reconcile 再核同 index 与四事实，形成本次新观察|不要求未知 operation ID，不声称找回原回复；已有 candidate intent 的 predecessor 永不替换。|

没有真实 V2 history 就没有可退还或补造的 collect 命令；直接调用内部 H 也不能据 payload 自称“首次”来绕过 source／scheduled-event 检查。重复 SDK attempt、恢复、超时和目录不存在都不授第二次 create。完整 prefix 超 M 保留原产物并停止，不分片、不丢旧轮、不新 run 续预算。

schema1 手工、schema2／program-v1／operation-v1／旧 activity.v1/v2 原字节与意义保持。旧 index schema、coverage、离线 read 及缺安装历史读取保持；旧 c1c ordinal0 commands 不 patch、不升级现存 ID。新 schema3 modes 不放宽 `BudgetedStart.source`、`validate_context`、原 adapter／executor 最后动作，也不开放新 cold inspect、父 dispatch 或 native。新 observation 不成为 approval、proof 文件、第二账本或可变 current-round。

原六阶段、candidate-bound evidence、attempt-before-send／unknown-only 对账、连续 BOOT 根及 cleanup reserve、原父共享许可与锁序保持。文件读取／archive／index 工作全在原受监管 H，不占 live root pipe loop、不持 SQLite 事务跨 RPC；stop writer 不等 index 锁。父 stop 拒后继，不统一 cancel 已接受前轮的原 release 窗口；总循环完成不发布 release、不迁 baseline。

## 最小验证接缝与证据等级

此表是未来实施验收要求，**本次全部未运行**。在准确候选选择最小必要参数，不锁配置默认值，不新建重复 CI job／test 文件。

|接缝|保留的真实边界及最小反例|能／不能证明|
|---|---|---|
|`tests/test_training_submission.py` 的 `cycle_operation_fault`＋原 `_CycleOperation/S/H`，`tests/fixtures/training_cycle_operations.py`|保留真实 spawn／S／H／reaper；只替 runtime/native 外部服务。四事实交错到达，native SUCCEEDED 但 runtime 未准／archive 缺／stop 未 durable；再分别错 run／memo／namespace／job／evidence SHA／Outcome report_uri|证明内部 H 组合不会静默误接受；服务替身与合成 schema3 chain 不证明正式 V2／真实训练 accepted。|
|原 `tests/test_training_evidence.py` archive、round index fixtures|实际 evidence reader、rounds.create/read、真实失败／pending 与 previous prefix；create 前正面、最终 index 采到 drift／错 run／no archive 时拒绝；旧 prefix 任一早轮变动拒绝|证明唯一 archive owner、最终 index 数据绑定和低覆盖兼容；不重写 gate／comparator。|
|真实 H writer／reconcile reader|最终合法 shape 在 M−1／M／M+1，含多字节 UTF-8 和 LF；合法 >1MiB 必须通过同一 writer／reader；每个原 reader 都合法而合计过 M 时完整 diagnostic 保留、无 ref／acceptance|证明完整合计界；不能用空占位 synthetic JSON roundtrip 或 monkeypatch writer 成功代替。|
|同一 fd／目录链／重读与 S supervision|index rename 后、fsync、目录同步、同 inode 同 raw 重读分别注入失败；同 raw 换 inode仍拒绝；观察 partial write／fsync／deadline；source／ROOT／stop 在前后核之间变更；实际阻塞 reader 被原 S 终止并收尾|证明真实调用链里的资源／时间拒绝。ExecutionRecords 原 raw-only durability 与新同 inode 保证分别报告，不虚报全链同 inode。|
|runtime 原 history stream＋SDK event／DataConverter|固定 run 的完整 ActivityTaskScheduled request、活动 ID／name／queue 错配与重复、截断／超 8000 events／8MiB、decode/RPC 失败；collect 完成丢失后 reconcile 缺目标不能 create|证明 SDK 结构与只对账算法；没有注册 V2 的真实 history 不称 Workflow 恢复验收。|
|原 S/H 运输边界|新完整 stdout／frame 32,767／32,768／32,769B，真实 identity／_stdout_ref；原 stdout hash、原 stopped／收尾；大 result 无截断 successful frame|归 M1c-O 本片新增值的运输范围；SDK assembled v3、N32 与 V2 接收界留后片。|
|兼容与隔离|准确候选旧 schema1／2、旧 operation.v1／activities、round index 及 stdlib-only protocol 内容检查；新 schema3 执行路径仍拒绝|运行必要现有 checks；源码／新非 editable 安装／真实服务／历史 replay 分开记账，历史成功不自动继承。|

M1c-T 旧 stdout/frame/stop refs 与 peer cleanup 结果可按准确候选复用其已运行项；旧 N32 的 66 refs 不认证新 v3 N32。M6 必须以实际 invoke 组装 facts／measurement／acceptance／所有 operations 后核 Payloads，以及 V2 started input／2KiB Memo／ordinary／stop／consume／signal／query／outcome；单独 `_cycle_capacity` 调用不能替代。真实两轮、installed worker 固定产品、真实父／子 history、模型／训练质量属于后续正式验收，不使用这里的内部反例冒充。

## 开放门禁、下一片和独立审查输入

最近可实施片是 **B：M2a＋M3a 内部 operation-v2 collect/reconcile 与 M1c-O**，先接受分片调整，再以验收完成的 M1b 固定候选建立隔离实现；仅改原 owner，先证明内部完整采集／唯一发布／durability／完整观察写读，保持 SDK 注册与所有执行开放关闭。如果实际实现无法在不移动 M5 gate 的前提下读取 schema3 原件，或必须复制 archive 算法，停止扩展这部分设计，给出具体依赖并复审，不暂时放行 native。

仍未解决／不得在本片关闭：

- M1b 新包／自身模板／最终候选交付及 M1c-T 的准确记录，以根交付为准。
- 超界 assembled parent-request exact raw 的有界、受监管留存方案；保留原 operation ID、原 deadline／取消／reaper，失败时如实 unknown。此问题仍阻断全 M1c 与 successor 开放。
- 新 collect history scheduled-event 实际读取／decode 与原机会判定的内部证据；V2 未注册前缺正式生产 creator／真实恢复历史。
- M5 完整 predecessor 在原 intent/context/request 冻结、所有 source／budget／registry／execution／native 原锁内最后 gate，以及各真实 ref reader 的 ARTIFACT_LIMIT 接线。
- M6 真 V2／v3 注册与服务拓扑、新 cold-H／dispatch、完整 input／Memo／Payloads／received-envelope 检查；此前没有正式 SDK acceptance 或 ordinal 推进。
- 新包／默认 sandbox／固定 worker 来源、真实两轮及失败／丢完成／stop 收尾；CPU／服务替身不认证 GPU 或训练收益／质量。

本设计的 fresh reviewer 由根任务另启。brief 应含原始任务、上述 wire／容量及其原审，不提供预期结论；固定主 HEAD、M1b 九文件 patch 身份、本文完整新文件和 SHA、已观察源码／关闭点、只读调查范围与“未运行”清单，并授权 reviewer 仅写项目自己的设计审查报告。审查要求分别判定需求和维护性，尤其核 B 是否有完整内部用例而非死 helper、唯一 publish 机会、完整观察实际读写、旧兼容和未开放 gate。若接受调整，再更新根计划／交付；本任务不编辑这些共享文件。

本次实际只读命令包括 `cat/sed/rg`、Git status／branch／log／限定 src/tests diff、指定文件 SHA；私有检查只核明确给出的冻结 patch 和隔离源码，不递归检查缓存。本次没有运行 tests／probe／replay／install／services／network／model／training，没有 commit／push；只写本页。文档静态链接和 whitespace 检查单独报告，不代替独立设计审查或任何产品验收。
