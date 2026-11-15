# c1d M2a／M3a 内部测量用例：独立设计审查

2026-11-16。Reviewer：fresh-context 独立 agent `cycle_measurement_acceptance_design_review`，未参与方案编写或实施，未继承作者讨论。按 `maintainable-project-delivery` 的 independent-review brief、`ergora-codebase-quality` 的 module-design／test-seams，先读原要求及已接受 wire，再沿真实源码核对本次方案。根、源码、测试 AGENTS、PLAN 和组件协议已读。本报告是唯一写入。

**需求轴：request-changes，阻断 finding 1（R1）。维护性轴：approve，阻断 finding 0。** B 的内部用例边界和有限分片调整可行，但在实施前须补齐 index／prefix 尚未形成时完整原观察的留存 owner 与失败顺序；不能按现稿宣称留存合同闭合。该结论不表示当前已有合法 schema3 现场运行、SDK creator、V2 注册或测量接受；不关闭完整 M1c，不开放任何 successor／native 执行。下列开放验收是已知合同义务，不是已完成项。

## 审查对象与固定身份

|对象|独立核对的身份／范围|
|---|---|
|[被审计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)|33,333B；raw SHA256 `dbcf438ca0bff975c0e974db6e6e9f1b4d4bd8716894e3f9868d0cda6f2651cc`，完整155行|
|[原测量／索引要求](../plans/2026-11-16-training-cycle-measurement-and-index.md)|raw SHA256 `4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d`；连同[原设计审查](2026-11-16-training-cycle-measurement-design-review.md)读取|
|[wire](../plans/2026-11-16-training-cycle-measurement-wire.md)|raw SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`；读取[原审及已接受复审](2026-11-16-training-cycle-measurement-wire-review.md)，包括完整 history 扫描和唯一 Schedule 的要求|
|[容量分期](../plans/2026-11-16-training-cycle-measurement-capacity.md)|raw SHA256 `c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`；读取[限定批准及 D1 关闭复审](2026-11-16-training-cycle-measurement-capacity-design-review.md)|
|本次实际主树|`refactor/architecture-foundations`；HEAD `23ad171bf8228bf80b070d6ad866f79d63986d56`|
|M1b 产品|`67ab9b4e446527fd27a61eff1aa6acb8d24feb01`，父 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`；实际 Git 差异为九个既有文件、352+/34-。交付记录的冻结 patch SHA 为 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`|
|本次相邻产品字节|worker `645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`；protocol `fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`；rounds `ad9fba3d3f675ec0a91dc07a4224852482e0b75730218b5feaecb3f342abe310`；runtime `1d1d3a3f27c84529e3e4f4a509e4df60b52f459013f95edc4473750182fdff86`|

方案第9行和第146行保存的是作者当时的调查／前置状态。本次主树已含 M1b；[M1b 交付](2026-11-16-training-cycle-v3-birth.md)末节记录源码、安装24＋14、自身模板、fresh 同片终核闭合，公开发布／自己的 CI 另验。本审以已导入源码判断后继设计，没有重新认证这些历史运行。M1c-T 的实际证据审查也由其自己的交付负责，不能由本次设计结论代替。

审查开始时已有 PLAN、M1a／M1b 交付修改及本次计划、容量计划／报告等未跟踪文档；未将这些共享状态改为 clean，也未修改它们。

## R1 — P1，阻断：prefix 前失败没有完整原观察的确定留存路径

位置：[计划第67–71行](../plans/2026-11-16-training-cycle-measurement-acceptance.md#L67)，以及第96–99、115行的失败留存声明。原要求第75、90行要求完整新采集 runtime／ExecutionRecords／evidence 结果留在原 H 操作证据中，失败／unknown 原观察也保留；wire 的完整材料合同和容量分期没有豁免该路径。

可达场景：H 已成功取得完整 Status／Outcome、native poll、ExecutionRecords 和 evidence；随后 `training_rounds.create` 因完整 index 超10MB、目录创建／rename错误或已有坏目标失败，或者 read／fsync／同 inode 复核失败，尚无可接受 prefix。现稿第71行明确不生成完整 observation／ref／acceptance，只说“可用原 operation 输出保留诊断”，没有指定完整已取值由谁、在何时保存，也没有禁止异常只留下 reason。已有输出机制不能自动补齐：worker `:695–696,718–719` 只将 runtime/native 完整结果放入 H 内存；外层 `cycle_operation_main:1057–1062` 捕获异常后只输出 `status/reason`。S 的 `helper/stdout.txt` 因而只有该小错误，request.json 保存的是输入，原 execution／archive 文件也不能恢复当次 RPC Status／Outcome 的 detail。之后 reconcile 只能产生新观察，不能找回当次原值。

后果：控制仍会保守拒绝后继，但方案承诺的完整失败材料并未保存；真实 create／read／fsync 失败反例可能仅得到 reason，却被记为“原 reader outputs 全保留”。这不是要求为缺 prefix 伪造合法 observation，也不是全 M1c 已知 parent-request 留存问题的重复：本项发生在已受 S 监督的 H 内，正常大小的输入也可触发。

最小设计修正：仍由原 H、同一 operation 和同一 deadline 负责，在每份完整 reader 返回后、进入后续可能失败的调用前，确定地保存已取得的完整值及其身份／阶段；最终重采的值也遵循此顺序。可复用原 `processes.run:157–158` 已保留的 `helper/stderr.txt` 作为非授权诊断输出，显式完整编码并 flush；或者明确一个同 operation 的不可覆盖诊断文件及原字节身份。选择必须在计划中固定，而不是只写“可用输出”。不需要新模块、第二账本或独立状态机。不能往32KiB成功 stdout塞完整正文、靠截断日志、放宽 observation 严格 prefix shape、抢占 observation 的 `xb` 路径后覆盖改写，或把诊断生成合法 acceptance/ref。诊断保存本身失败／被 S 截止时只保留已有字节并如实 unknown，不声称完整，也不增加时间／机会。

相应最小验证：在真实 H 四项 reader 已成功后，分别让 create（含合计超M）、read、fsync／同 inode 复核失败，核当次完整 runtime detail 及其余已完成 reader 结果的实际保留字节，并核无合法 ref／acceptance／ready。再覆盖诊断写入失败／deadline，区分完整留存与部分原件。可沿方案已有 S/H 与 archive fixture 增补，不需要新测试文件或额外服务。修订后须对此项同片复审；本次没有运行反例或修改实现。

## 调整必要性、真实入口与权限

现有 [worker 构造器](../../src/ergora/reference_training_worker.py#L46) 接收完整 operation 请求，经 `_run:121` 启动现存 `cycle_operation_main:1033`，后者读取 stdin、验证父进程、保存原 request，再通过原 `processes.run` 启动唯一 H，最终进入 `_cycle_operation:486`。这是实际可执行的内部进程协议入口。当前的 mode／snapshot／activity validators 仍只有旧版，且 `_cycle_operation:495` 在 schema3 进入业务前拒绝；当前没有 collect 分支或正式 SDK creator。

方案 B 将两个严格新 mode 接入这条完整入口，包含准入、四事实组合、唯一原索引发布／对账、资源生命周期、最终投影及失败结果。因此它可以作为顶层内部用例独立交付；不是仅由测试 import 的序列化 helper。`_cycle_operation` 是拟增私有算法的实际归属和调用点，同文件调用不冒称跨模块复用。删除私有算法后，完整绑定、fd 生命周期和失败处理仍必须回到该分支，分离一个内聚私有实现有明确可读性理由。无需新增 collector 包装器、manager、注册 stub、通用 archive reader 或服务。

这个判断不补造缺失的生产链：正式 SDK 尚不能创建合法的新 collect 请求，M1b 也不能生产合法 schema3 父／子运行。内部服务替身可以检验完整用例的外部依赖，不能证明真实 V2 曾调度或发生过发布机会。计划第31、34、36、74、134、148行明确保留这一限制；实施报告必须继续使用“内部用例／服务替身”证据等级。

合并 M2a 的事实组合与 M3a 的发布／持久确认有实际理由：完整 observation 的 prefix 必须来自本次原索引，acceptance 必须在 index 和 observation 都持久确认后形成，reconcile 又是跨 operation 的真实 ref 消费者。单独写正面谓词无法关闭 M1c-O。提前加入 SDK closures／队列注册会越过 M6，也不能凭注册制造合法父 history；提前合并全部 M5／M6 则扩大生命周期改动。B 的边界更小，原编号和逐项验收义务保留。

第53行提前的 M5 部分限于读取格式，必要且可局部实现：`_cycle_target:443 → _cycle_submission:427 → CycleAdmission.bind:776 → validate_budget_binding:148` 当前拒绝六字段 v2 controller。严格按 protocol 分支接受其 shape，并按授权2／3核精确父 protocol、receipt 和 selected admission，才可读取新原件。该解析能力不产生执行权；[BudgetedStart.source](../../src/ergora/reference_training_budget.py)、[validate_context:1085](../../src/ergora/training_execution_protocol.py#L1085)、原 adapter／request／launch／native 关闭点必须保持。只能给 schema3 的 collect／reconcile 两 mode 特许进入内部测量，不可把全局 schema3 拒绝直接删除后让其余 mode 穿透，不可使用 `>=2`。方案已把缺少这些关闭点列为验收拒绝条件。

## 四事实、原 owner 与最终绑定

|检查点|实际源码事实及审查判断|
|---|---|
|真实 runtime|`_execution_candidate_operation:682–706` 已核连接 namespace、固定 receipt.run、完整 spec 和 memo，再调用 [lookup／observe](../../src/ergora/reference_training_runtime.py#L11)。后者 RUNNING 查询 Status，COMPLETED 读取不 follow 的 Outcome。计划只接受 AWAITING_RELEASE 或明确的 RELEASE_EXPIRED／INTEGRATION_TASK_CREATED；Status 用 evidence_sha，Outcome 用原 native gate-report URI，不发明 Outcome.evidence_sha。|
|原 native／execution|worker `:638–651,708–729` 已保留完整 native asdict、ExecutionRecords 观察及 request/job 绑定。`ExecutionRecords.load/request_record:936–1037` 核 owner、五记录、原 start attempt／receipt／完整 native request；`observe(durable=True):1039–1064` 同步原件、目录和 raw 重读。计划保留两个 stop-confirmed 严格 true，且准确承认该旧算法没有同 inode 检查，不要求已停 owner 仍活。|
|accepted archive|[evidence.inspect:11–92](../../src/ergora/reference_training_evidence.py#L11) 是唯一 archive 接受 reader：核原 gate、原成功结果、content address、manifest／baseline／comparator、完整 files。第40行负 gate／无 gate 返回真实 no_accepted_archive；不应从 reader 错误猜 pending。计划保留 `artifact_content_status=not_read`，不复制 comparator、baseline_ok 或 artifact-wide 验证。|
|最终 index 的实际观察|[rounds.create:59–69](../../src/ergora/training_rounds.py#L59) 会再次调用 inspect／evidence／submission／approval。计划第69–70行明确拿最终索引最后轮的那份完整 native 观察绑定原链，并在持久确认后重采四事实；不会用 preflight PASS 为后来捕到错 run、no archive 或 drift 的不可变索引盖章。|
|approval 权限|`training.approval:180` 调原 release/status；[_Release.status:101](../../src/ergora/reference_training_release.py#L101) 读取本地决定。计划保留原观察、不进入 receipt／approve／signal 分支，也不将人工决定变化作为接受权。原低覆盖 index 仍不认证来源或授权。|
|source／ROOT|计划固定授权四项 measurement_sources，并保留候选 owner 的原25项 capability、所选安装和 descriptor。原 wire 已指出包内 ROOT 与所选 installation 不同；这里要求先核 pinned reference manifest，再用原 reference.verify 核283项，并在采集、index 同步、observation 确认后重核。未新增接受权代码文件，预计 diff 的 worker／protocol／runtime 已由原25项覆盖。|

故意错 run／memo／namespace／job、archive 或 source 漂移、坏 raw 和 RPC／decode 失败是 unknown；完整可信的负 gate／FAILED／CANCELLED 可以是 rejected，低覆盖失败 index 仍不得 ready。可信非终态或等待原 reap 才是 pending。计划第68行“完整可读失败轮”、第83行 reader 失败 unknown 以及第115行身份冲突 unknown 应合并理解：不能让一个局部负值覆盖同次观察的身份／来源不可信。该要求已在计划的全局绑定条件中，不需要新增失败分类体系。

## 发布顺序、恢复及容量

原 [rounds.create:42–89](../../src/ergora/training_rounds.py#L42) 保留 previous 完整轮值、只采新增轮，原 pretty／content SHA、10MB／32轮和不可覆盖目录发布都可复用。原 read 只核本文件和声明链接，不读取 previous 原件；计划正确在 H 额外拿所有已确认原 prefix 逐项比对，核候选顺序、原注释／manifest、完整 `_COMMON`、initial anchor 和 previous_report 的 raw SHA／rounds／last-round。不能用一个自报摘要或较短合法 index 替代旧前缀。

durability 的 owner 顺序完整：原 create 或只读现存目标 → 固定 fd/raw/dev/inode → 原 read/check → 同 fd fsync → 原 index 目录至 cycle 根目录链同步 → 同路径重开、同 inode/raw/SHA → 原 rounds.read 核相同 prefix → 最终四事实／source／父 RUNNING／stop／clock → 完整 observation 写入及同步重读 → 最终小投影。原 publish_directory 没有 fsync，不被全局改造。index 最终绑定失败后不能修补；写入／fsync／同 raw 或 deadline 失败只能保留 unconfirmed／unknown，不能形成 acceptance。

唯一发布权继续由原 history command 消耗，不新增本地 collect-attempt 账本。计划要求固定父 run 的真实 Scheduled event、精确 `candidate-<k>-collect`、collect.v3、queue、完整 request 和唯一命令；runtime 私有接缝必须完成有界完整扫描后才作唯一性结论，不能匹配第一个 Schedule 就返回。这个要求来自已接受 wire 复审，计划第64、74、134行没有取消它。Scheduled 证明机会已消耗，不证明 H 已开始或 artifact 已 durable。

collect 目标存在或竞争输家只读胜者。reconcile 缺目标、部分或坏目标均不能 create；completion 丢失时用确定性 index 和原 collect history 重新观察，在自己的原 operation 保存新观察，不扫描旧 operations 猜 ID、不要求未知 ID、不改已有 intent.predecessor。恢复必须重读同一原 prefix，并消费原 BOOT／work／operation window；不能刷新 cold timeout、归零轮计数或以原 reader 自身20／30秒上界延长 S 的监管窗口。真正阻塞 reader 及后代仍由原 S／reaper 停止，stopped 后不得再 spawn。

单文件观察严格沿 wire 的完整 shape、compact UTF-8／一个 LF，bytes 和 raw SHA 包括 LF；唯一数值 owner 是已实施的 `protocol.ARTIFACT_LIMIT=10_000_000`，rounds 常量保持 alias。合法观察须 `xb` 保存完整字节、同 fd／目录链同步、同 inode/raw 重读；真实 H 写后及 predecessor／reconcile reader 显式 `read_raw(path, ARTIFACT_LIMIT)`，不误用默认1MiB。超过 M 的完整字节只可作为不被准入的 diagnostic；写入未完成则如实 unknown，不能声称全件已保留。单个 reader 成功不证明合计可放入。

32,768B 的 H stdout（含 LF）、S 完整 result frame（含 identity／`_stdout_ref`，delimiter LF 单列）仍分别核验；新版本容量失败 replacement 也必须重核，65,536B stopped 界保持。SDK 最终 assembled result／Payloads／metadata、V2 收到结果的整体检查、输入／Memo／signal／query／outcome 没有被该内部片替代，它们留在真实 M6 owner。计划没有许诺所有合法大输入总能装下，也没有通过附件、截断或更小字段配额凑界。

## 阻断 findings 与开放验收

本次设计有上述需求阻断 R1；维护性未发现需要新增架构修订的 finding。R1 修订复审后，以下既有门禁仍须在准确新候选上取得证据，**不是本审批准的现成能力**：

1. M1c-O／M2a／M3a：完整内部 S/H 调用，四事实交错、错绑定、原 evidence／rounds 实际重采和最终漂移拒绝；同一观察 writer／reader 的 M−1／M／M+1、多字节 LF、合法 >1MiB、原 reader 均成功但合计超 M；同 fd／inode／raw、目录同步失败、源／ROOT／stop 变化及阻塞 reader 的原 S 收尾。沿现有 submission／evidence fixture，不能用 placeholder roundtrip 代替。
2. runtime 新 history 接缝：真实 SDK event／DataConverter，有界完整读取及唯一 Schedule／完整 request，重复／错 queue／decode／RPC／history 界失败 unknown；reconcile 缺目标永不 create。正式 V2 未注册前，服务替身只能证明内部算法，真实 lost-completion 恢复留后验。
3. **完整 assembled parent-request exact raw 留存仍未解决，并继续阻断全 M1c／successor。** 当前 `_CycleOperation.__init__:79–83` 超界时 S 尚未出生、output 未赋值，现有异常日志不保留完整 assembled raw。方案第105、147行明确留存该合同。不得通过本次内部 writer、原输入可重构、另一 operation ID、大同步日志、无监管线程或新窗口声称关闭。
4. M1c-R／M5：完整 predecessor 冻结在原 intent／context／request，所有真实 reader 显式10MB界；budget／registry／execution／native 原锁内最后 gate 实际拒绝直接调用、别 run 投影、缺早轮原件及 stop／source／clock 竞态。此次提前读取格式不认证这些效果 gate。
5. M1c-V／M6：真实 V2、七活动注册及原两配额服务拓扑、cold／dispatch、完整 Payloads／metadata／Memo／consume／signal／query／outcome 和 N32 真实聚合；全部 M1c、接受、durable prefix 和 M5 关闭后才可开放新版本后继。旧 V1 消费者当前缺整体容量重查的事实及原 commands 保持。
6. 新非 editable 安装、实际来源／默认 sandbox、真实父子 history／replay、两轮原 runner 数值及合法 oracle／accepted archive、重启／丢完成／取消及原进程／run／监听收尾仍属 M7／M8。前轮人工 release 窗口、六阶段、原25来源、283资源、attempt-before-send／unknown-only 与 BOOT 根保持；不 approve／release／迁 baseline，不把 CPU 控制合同认证为 GPU／训练收益或质量。

本审仅做只读文本、Git 身份／限定差异、指定文件 SHA 和报告静态检查；未运行 tests、probe、replay、install、services、network、model 或 training，没有 commit／push，没有递归读取 `.ergora/checks`，未改产品、测试、作者计划或 PLAN。没有重新认证旧 v1 历史，也没有认证不存在的 V2 运行。可实施性、需求 request-changes 和维护性 approve 是基于上述固定源码的静态设计判断，未来实际 diff 仍须自己的独立实施审查。

报告静态检查：17个相对文件链接全部存在；`git diff --no-index --check /dev/null <report>` 无 whitespace 诊断，exit1 为新文件差异状态。被审计划 raw SHA 未变。结束时另外出现 transport 审查与 parent-request retention 计划等共享文档，未由本 reviewer 修改或纳入本报告的设计认证。

## R1 同片有限复审

2026-11-16。由同一独立 reviewer 复核修订后的[计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)，独立重算 raw SHA256 为 `2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`。原稿 `dbcf438c…`、原需求 request-changes 及 R1 finding 均保留在上文；没有覆盖历史结论，也没有产品实现改动。

**修订后需求轴 approve／开放 finding 0；维护性轴 approve／开放 finding 0，仅限本次内部用例设计与有限分片调整。R1 设计阻断关闭。**

修订第67、71及93–102行已固定实际 owner、路径和顺序：每份完整 H reader 值返回后，在下一可能失败的 reader／index 操作前，向同一受原 S 监督的 H stderr 写完整 UTF-8、finite JSON＋LF并 flush；保留完整 RPC detail、files 和 raw 库存，不等四项齐全、函数返回或 prefix 形成。每次最终重新采集分别追加。原 `_execution_candidate_operation` 如需私有提取，留存必须接在实际取得每份值的位置，不能等整个组合成功才写。因而后续 reader、create/read/fsync 失败时，已有完整观察已有明确保存路径，不再依赖外层仅有 status/reason 的 catch。

再次沿 [processes.run:157–166](../../src/ergora/processes.py#L157) 核实：原 S 直接打开 `helper/stderr.txt`，把该 fd 作为 H 的 stderr 传给 `subprocess.Popen`。它不经过 `_CycleOperation` 父进程的65,536B diagnostics 内存缓冲，也不进入 H 业务 stdout、32KiB result frame 或 SDK envelope。修订仅复用该原 operation 诊断输出，无新文件、账本、schema、时钟、进程或权限。完整观察的严格 prefix shape、10MB 准入及同 fd／inode／raw 持久确认保持，不用诊断替代合法 observation。

编码／写／flush 失败及原 deadline 终止明确停止采集／发布并 unknown；只报告实际 available／partial 字节，不把 flush 说成 fsync／durable，不发合法 ref／acceptance／ready，也不延长原窗口或返还一次机会。这与 R1 所需的最小失败顺序一致。新增验收要求保留真实 H、独特大 runtime detail、后续 reader／create／read／fsync 故障和原 S 超时／取消 partial 边界，能观察原问题，未以普通 reason 或原 chain 存在冒充完整留存。

关闭的是静态设计缺口，不是诊断写入的运行验收。完整 parent-request exact raw 的受监管留存、全 M1c、M5 最后 gate、正式 M6／V2／SDK 注册、真实两轮及安装／恢复／收尾仍按上文开放；R1 使用已有 H stderr 不能解决 S 尚未出生的 constructor 超界问题，也不认证旧 v1 历史或未来 V2 运行。本次只读修订、相邻 fd 路径并追加本节，未运行产品检查或改作者计划。
