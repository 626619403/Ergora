# c1d 超限父请求留存：独立设计审查

2026-11-16。Reviewer：fresh-context 独立 agent `cycle_parent_request_retention_design_review`，未参与方案起草或实现。应用 `maintainable-project-delivery` 的 independent-review brief，以及 `ergora-codebase-quality` 的 module-design／test-seams；已读根、源码、测试 AGENTS、当前 PLAN 和组件变更协议。本报告是本审唯一写入。

**需求符合性：request-changes，阻断 R1 一项。可维护性：request-changes，阻断 M1 一项。** 方案抓住了真实的 constructor 留存缺口，并明确区分业务拒绝与诊断成功；同 UUID、不可恢复机会、原 window、不启动业务 H／root、旧版本隔离这些方向合理。但目前不能把整份新增协议／receipt／watchdog 方案作为已审可实施设计接受。范围修订尚需主控处置，实际新 operation-v2 caller 仍是前置，完整 M1c 与全部执行门禁继续关闭。

## 审查身份及原要求

|对象|独立核得身份／范围|
|---|---|
|被审计划|`docs/plans/2026-11-16-training-cycle-parent-request-retention.md`，27,697B，SHA256 `6566ca5ba0c2c97fd6b55120706c2f0297a6ce210b7cf59459e7d8fe1eb72f5b`|
|权威 wire|`docs/plans/2026-11-16-training-cycle-measurement-wire.md`，SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`；已读其接受复审|
|容量分期|`docs/plans/2026-11-16-training-cycle-measurement-capacity.md`，SHA256 `c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`；已读 fresh 审查及 D1 关闭|
|当前主树|HEAD `23ad171bf8228bf80b070d6ad866f79d63986d56`；M1b 产品 `67ab9b4e446527fd27a61eff1aa6acb8d24feb01` 已普通导入，仍是 storage-only|
|实际 worker|`src/ergora/reference_training_worker.py`，SHA256 `645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`|
|实际 protocol|`src/ergora/training_execution_protocol.py`，SHA256 `fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`|
|实际 process owner|`src/ergora/processes.py`，SHA256 `56c1961745b03ee4775e75f17dcb5a30a3d105e4bbd0f3fb516451e0fcd55867`|
|实际测试与 fixture|`tests/test_training_submission.py`，SHA256 `d0d11c557c4982ef91b57fa3d4f8c2043707fdf46165d2b75043bb3cccaed54e`；`tests/fixtures/training_cycle_operations.py`，SHA256 `03edbad39b2108fc09afbf5003124c5d109896cbdf46176843a3b60e9bfcb844`|
|相邻、另审计划|`docs/plans/2026-11-16-training-cycle-measurement-acceptance.md`，SHA256 `dbcf438ca0bff975c0e974db6e6e9f1b4d4bd8716894e3f9868d0cda6f2651cc`；只核其内部 caller／mode 前置关系，本审不接受该方案|

被审计划第9／15–19行记载的是作者当时读取的旧主树字节；本报告按上表当前 M1b 后的真实源码检查，没有把两种源码身份混作同一候选。进入时已有他人的 PLAN、delivery 修改及未跟踪设计／报告，均未改动。

原要求来自 wire 第206／241／261行及容量方案第30–32行：保留这一次已组装、完整 compact UTF-8、无尾随 LF 的原 request 字节和原 operation 身份；不能换 UUID、重构 snapshot 子集或用 SDK history 冒充原 raw。正常 S/H request、result 和实际 SDK Payloads 的32,768B界不放宽；拒绝不启动该业务 H／root、不返还机会。必须保留原 BOOT／compute／total／cleanup／冷观察窗口、父死监督、取消与完整 peer 收尾。完整留存仍是 required gate，分期接受没有 waiver。用户同时要求尽量减少无必要 wrapper、ledger、断言与重复测试。

## 实际生命周期与可复用边界

- [worker:69–83](../../src/ergora/reference_training_worker.py#L69) 先生成原 UUID／完整 parent identity、验证并一次编码；超界 raise 发生在 `self.output` 赋值之前。此时没有 S、`request.json` 或 H stdin。SDK wrapper [1671–1675行](../../src/ergora/reference_training_worker.py#L1671) 只记异常文字；stop 构造失败 [1003–1014行](../../src/ergora/reference_training_worker.py#L1003) 又生成另一个 UUID。新方案保留同一对象、把容量拒绝处理移到其 async 生命周期，有真实责任，不能由同步全量日志修复。
- [worker:124–180](../../src/ergora/reference_training_worker.py#L124) 持实际 spawn／pipe／wait task，经取消继续收尾。普通 S [1044–1071行](../../src/ergora/reference_training_worker.py#L1044) 只读 limit+1，写原 request；[1096–1114行](../../src/ergora/reference_training_worker.py#L1096) 经 `processes.run(supervised=True)` 启动唯一 H、清理后才发 stopped／result。[processes:140–194](../../src/ergora/processes.py#L140) 在启动 H 之前同步写 `stdin.txt`，SDK 父端直接调用它不能满足受管异步留存。
- [PhaseFrames:226–264](../../src/ergora/training_execution_protocol.py#L226) 固定匹配完整 identity、第一帧 stopped 的 process shape／`output/helper`、再接 result；[worker:168–170](../../src/ergora/reference_training_worker.py#L168) 依赖该帧才允许杀普通 S。不能为减少一个小诊断响应 parser 而伪造 H-reaped stopped，或改普通 kill 资格。原 `_stdout_ref` 也只允许 `helper/stdout.txt` 且≤32KiB（[worker:184–191](../../src/ergora/reference_training_worker.py#L184)），不能改为大 request ref。
- 可直接复用的是 `protocol.decode/_exact/_digest/_process`、原 process identity、目录同步、当前取消持有模式及既有测试入口。诊断只需留在原 worker 的私有生命周期，不应另建模块、ABC、通用 retention service 或执行／授权 reader。
- [原容量测试:3022–3066](../../tests/test_training_submission.py#L3022) 的 `operation-request` 分支证明 SDK 入站合界而 stop-writer 组装超界、其余五 peer 收尾；该分支没有读取 rejected raw。另两个 stdout／frame 参数读取的是已存在的真实 H stdout。原测试不能认证新留存路径。

## R1 — P1，需求阻断：独立 S 的时钟监督没有完整保留原 budget clock 语义

位置：[被审计划第79–89行](../plans/2026-11-16-training-cycle-parent-request-retention.md#L79)、[第97–99行](../plans/2026-11-16-training-cycle-parent-request-retention.md#L97)。第81行要求开始／每块／最终确认继续调用原 `remaining`；但控制封套只列 identity、固定 BOOT window、N，S 主线程和 watchdog 随后只定义为检查 parent、BOOT 和固定 D。封套没有原授权 clock／相应 policy，因此 S 在接收尚未完成时无法实际调用原 `cycle_operation_remaining(payload)`；其主线程阻塞时更不能靠父端代查补足独立监督。

实际 [cycle_operation_remaining:457–472](../../src/ergora/training_execution_protocol.py#L457) 对 work／stop 不只检查 BOOT deadline。它调用 [budget_clock.remaining:48–57](../../src/ergora/budget_clock.py#L48)，同时观察 UTC 和 boottime，取较大 elapsed，且 UTC 倒退、elapsed 为负或两种时钟相差超过5秒均拒绝。`budget_clock._clock:13–17` 只返回 BOOT／boottime，不能替代这些检查。

可达序列：work 或 stop 的大 raw 留存已经开始，SDK 父 loop 暂不能调度，S 主线程在 storage I/O 中；UTC 前跳使原 budget clock 应当立即拒绝，但原 parent 仍活、BOOT 未变且 D 未到。按第89行的 watchdog 算法，诊断 S 仍可继续写直到旧 D。父端最后恢复后会拒绝 durable result，所以这里没有已证明的业务接受绕过；问题是新增独立资源 owner 比原 S 的 `stopped()` 少了原时钟拒绝条件，违背不放宽原预算监督的设计前提。第81行的泛称不能消除后面明确算法与可用输入的矛盾。

**最小修正：** 明确 S／watchdog 如何在原 parent 不能调度、raw 尚未收完／主线程阻塞时独立执行原 budget clock 拒绝。可在有界封套中携带调用既有 clock 算法所需的最小原 clock／policy／mode 投影，并保留原整数 D 只缩约束；冷观察只复用其既有 BOOT window。无需加入完整 snapshot、第二授权证明或另造时钟库。也可以提出能证明等价的更小机制，但必须列明 UTC／boottime drift 的停止语义，不能仅以 `A+remaining` 的一次投影替代后续原 clock 检查。

后续验证在真实诊断 S 的 watchdog 接缝选一个原 clock 已无效而 BOOT D 尚未到的 case，保持 parent 不能代查／主线程阻塞，观察实际同一 S 被回收及无 durable 确认。无需复制全部 `budget_clock` 测试矩阵。本次仅静态审查，没有运行该场景。

## M1 — P2，可维护性阻断：第二 receipt 与双向握手缺乏独立必要消费者

位置：[被审计划第53–56行](../plans/2026-11-16-training-cycle-parent-request-retention.md#L53)、[第83–85行](../plans/2026-11-16-training-cycle-parent-request-retention.md#L83)、[第99–107行](../plans/2026-11-16-training-cycle-parent-request-retention.md#L99)。

在现有合同中，业务永远是 capacity failure；只有父端在原 window 内收到合法确认后才能报告 durable ref。丢 reply 后，即便 receipt 已落盘，父端仍必须 unknown（第45／107行）；本片明确没有新增只读诊断 reader／对账入口（第101行）。因此 `request-retention.json` 当前只有写端再读自己的消费者，之后的“以后只读核对”是假定未来用途。它没有给现有父调用者增加恢复能力，却增加第二次 exclusive publication、fsync、目录链同步、receipt inode/raw 验证及再读 request 的窗口负担。一个本来已完整持久的 rejected request 会仅因这份额外文件失败而无法获确认。

同样，ready 的 envelope SHA 用于让父端知道诊断 S 已接受控制封套，但该 S 没有 H／外部效果且父端本来就持有 pipe、完整原 identity、固定 D；S 预检失败关闭管道，原 send／wait 监督即可拒绝。32B binary trailer 让 S 比对父端 digest，但父端已经流式计算同一 immutable raw SHA，可在接收最终 identity-bound 确认时与 S 的逐块写入／重读 SHA 比较。计划没有指出一个此最终比较与精确 N＋EOF 无法检测、而必须靠 trailer 才能保护的业务或诊断接受失效。当前方案把同一完整性事实放进三份交换／状态，没有展示三者各自必要性。

**最小修正：** 先以原 `request.json`、受管 chunk 发送、N／EOF、同 fd fsync／目录链同步／同 inode raw 重读和一个严格有界的最终 identity-bound 确认为最小设计，父端用同次原编码的 SHA 核对最终 ref；沿原小错误日志保留发现入口。移除第二 receipt、ready 和 trailer，或为要保留的每一项给出当前真实 caller、独立失效序列以及上述较小方案不能保护的原因。该建议不要求修改普通 PhaseFrames 或扩大 `_stdout_ref`；新失败诊断响应可以是同 owner 内很小的私有协议解析。若确实需要持久诊断 receipt，须先给出本片真实只读调用者与恢复问题，不能以“将来可能用”添加第二状态文件。

留存状态也应只反映可达观察：`available_unconfirmed` 可以描述 S 的局部观察，但当前没有定义发送该观察的帧；父端不能新增一个没有 producer 的中间状态分支。无需为每个局部 step 建状态枚举或单测。`request_capacity_rejected` 则有直接 caller：constructor 需要让同一 operation 的 `run()` 选择失败留存，并永久禁止普通 send；这个事实必须保留，但可由最小本地表示承载。

## 新设施逐项判断

|设施|真实责任／失效情形|本审判断|
|---|---|---|
|同文件、无 H 的 subprocess entry|SDK async 父端不能同步写／fsync；blocked I/O 必须有实际 process handle 可停止、可 wait|有必要的生命周期 owner；只随首个真实 operation-v2 caller 一起交付，不作为无人调用 helper 先落地|
|独立小控制封套及最终确认|raw 超普通32KiB；S 需先得到原 identity／监督输入，父端需绑定最终 raw 和真实 wait|失败专用协议修订有依据；最小字段与时钟输入按 R1 修正，复用原 JSON／identity primitives|
|原 UUID／immutable encoded 保持|旧 constructor throw／stop replacement ID 会丢原身份，source 重构不等于原 raw|必要；oracle 必须截获同次 encoder 输出，不能重新编码来证明|
|direct-kill 诊断 S|它永不 spawn H／后代，停止时无 H-reaped 帧可等；等待文件 I/O 不能依赖 cooperative signal handler|有必要；必须由专用失败分支和真实 wait 收敛，不能改变普通 S 的 kill gate 或称 H stopped|
|S 内只读 watchdog|parent SIGKILL 后主线程可能阻塞在 open／write／fsync；父 monitor 已消失|有实际失效情形；一个随 S 退出的 thread 足够，原普通 S monitor 无法从外部监督另一个诊断 S。原 clock 语义按 R1 补齐，无需另建 reaper／服务|
|`request-retention.json`／ready／trailer|现有最终确认加原 raw 可承担已列责任；receipt 无实际恢复 reader|M1 阻断；先删除或给具体必要性，不因设计已写长而接受|
|外部输入／文件／帧 guards|输入 shape、exact identity、N int、SHA、完整帧界、普通固定路径、exclusive 文件、同 inode/raw 防止静默连错原件|边界检查必要；沿既有 primitives，在实际使用点验证，不为每层重复包 validator 或全合法字段测试|
|diagnostic stopped／returncode|普通字段分别表示 H stopped／业务 S；新过程必须如实等 wait|需要独立事实，字段可内聚在 `request_retention`；不得复制一个通用 process-state ledger|

不强制改成“普通 S 再生一个 writer 子进程”：那会新添无 H 的 stopped 语义、reaper／FD 接线，并把同一问题转移进另一个进程树；在本任务约束下未见它必然比单个诊断 S 更小。已有 `processes.run` 的先行同步写也不能直接接住 async 父 raw。watchdog 与不能取消的父 executor 写线程不是同一种生命周期。

## 可行性、失效与兼容判断

|场景|设计中可接受的约束／仍需实际证据|
|---|---|
|精确 raw 与 backpressure|父端只保留同次 immutable `encoded`，chunk 发送、逐块 SHA、显式让出 loop；`drain()` 不保证每次都会 yield，实施时不能漏显式公平调度。S 只写原 N 字节，无 LF／封套／trailer 混入 raw；总内存与磁盘是随实际 N 的界，不是任意 N 都能成功|
|S 不读／blocked write／fsync|父 monitor 仍能调度则按 stop／原 deadline 直接 kill，父死后由 S watchdog；发送／stdout／stderr／wait 全部保留实际 task 与 handle。不能因 BrokenPipe、取消或发出 SIGKILL 就报告 process stopped|
|取消／reply loss|先停止同一诊断 S、排空原管道并等实际 wait；receipt／文件存在不能补造父端当时已确认。不得重发 raw、重建 UUID、续 window 或退还 ordinal／机会|
|父 SIGKILL／PID 复用|`processes.identity:18–26` 核 pid＋start_ticks＋BOOT 并拒 zombie，S 还核 getppid。父死前仅在封套读取中，父 pipe 关闭可产生 EOF；不能据此凭空宣称必有 orphan。storage 阻塞中的父死必须真测 watchdog，async cancel 不能代替。内核 D-state／停调度仍只能诚实保留未回收 identity|
|同 inode／tamper／root 路径|计划要求 raw 长度／SHA、同 dev+inode、exclusive／no-follow、原固定 operation 路径合理。`protocol._fd:176–190` 是逐级 lstat 后 open，`sync_directories:624–633` 是逐路径同步；它们不构成对并发替换所有祖先的原子目录能力保证。沿仓库既有可信用户边界报告实际保护，不把文件同 inode 测试称为全面 rootescape 或永久防篡改证明；如要加强该威胁模型须另明范围，不能暗改全局 reader|
|stop peers|保留 [worker:1000–1027](../../src/ergora/reference_training_worker.py#L1000) 全部可运行 peer 先起 task、finally 全部 stop／shield 收尾。retention task 未结束不能让其余分支不发通知／排空；容量异常只在实际收尾后上抛|
|普通 wire／旧 history|最小仅接新 operation-v2，旧 constructor raise／fallback ID／activity names／25 source gates保持，符合已接受版本隔离；这不修复旧 v1 留存缺口。普通32KiB、stopped65536B、真实 H reaper、原 stdout ref 均不改。旧 v1 若改接留存是独立扩审范围|
|proof／授权|诊断 raw 与其最终 ref永不被 CycleAdmission、BudgetedStart 或 native source 当成 permission、acceptance、prefix；诊断成功不影响 capacity_exceeded，也不产生新 launch／attempt／root。不能让未来 reader 把本地诊断“确认”当执行证明|

磁盘满、I/O 错误、原 window 已尽、强杀与掉电下不能绝对保证文件完整保存。计划第47／93／115–117行明确 unknown／partial、D-state 限制和无固定 N 成功保证，披露正确。**unknown 是实际失败，不是完整留存成功的另一种名称。** 正常可留存路径仍必须给出完整原 raw 的成功证据；故障路径保留 available originals、不覆盖修补、不虚报 complete。不能用不可能的绝对保证作为移除 required 留存 gate 的理由。

## 未决范围处置与最小后继

以下事项是未决决策／验收前置，和 R1／M1 finding 分开：

1. 主控决定是否接纳大于32KiB的失败专用流和无 H 诊断 S 的 direct-kill／本地 watchdog 语义；本审认为有具体生命周期依据，但不代替该范围处置。普通成功 wire 和普通 H 的停止合同不放宽。
2. 主控明确有限 window／磁盘故障的 truthful unknown 合同；不得把未知记为完整 durable，也不要求实现者保证不可能的所有故障完整保存。
3. 实际 operation-v2 内部 producer、原 source／activity-context 认证和 mode 校验先在其所属 M2／M3 方案中成立。被审计划第128–130行正确禁止先落 future helper；相邻方案尚未接受不构成留存 caller 已存在。不要为了验证诊断路径提前注册 v3 活动／V2 或放开 schema3 执行。
4. 完整逐 operation 的小失败发现入口要在实施时指明实际日志 owner／调用点；第109–111行不应被理解为另加索引或隐藏状态文件。失败集合不能完整放进 SDK Failure 时诚实报告整体 unknown，不能沿 `_cycle_capacity` 的成功 Payloads 检查冒称 Failure protobuf 也合界。

R1／M1 修订后的最小可实施目标是：一个真实新 operation 及其唯一原 raw，原 async 父生命周期，一个不启动任何业务后代的受管诊断 S，原时钟完整监督，原 operation 的完整 raw 文件，以及父端在真实 wait 后能验证的有界诊断结果。只保留有独立责任的检查与状态。

未来验证可沿 [cycle_operation_fault:1973–1993](../../tests/test_training_submission.py#L1973) 扩一个准确 argv 接缝。现有 fixture [第14–16行](../../tests/fixtures/training_cycle_operations.py#L14) 会先把 stdin 全部读完再 JSON parse，不能原样用于二进制 chunk 诊断流；新接缝必须保留真实流、S、watchdog、磁盘和 wait，不能以“saved” mock替代。优先最少完整场景覆盖：实际 producer 原 raw 对比；32KiB分流；partial／blocked I/O 的 loop 公平与全部 peer 清理；receipt／reply 丢失后的 unknown；parent 真 SIGKILL；同 inode/raw 冲突；R1 原 clock 无效。可把独立失效合并到已有参数化边界，不为每条错误文案、chunk helper 或合法字段增加测试。源、非 editable 安装、服务替身、真实现场证据分别记账，不能继承 M1b 或旧 c1c 的通过。

## 本次检查及限制

本次只静态读取被审完整文本、权威原计划／复审、AGENTS／PLAN／组件协议、实际 worker／protocol／process／budget owner 及相关 fixture／assertions；核 Git 身份与列明 SHA。没有运行 tests、probes、replay、安装、服务、网络、模型或训练，没有递归扫描 `.ergora/checks`，没有产品／原计划／PLAN 修改、commit 或 push。本报告的发现是设计可实施性与最小范围判断，不是未来代码已触发的运行结果。

关闭 R1／M1 并完成范围 disposition 后，仍需同一份修订设计复审；只有实际新 caller 接线和完整 raw／原监督／失败收尾／兼容证据到齐，才能关闭父请求留存 required gate。当前 M1b storage-only 和已限定接受的 M1c-T不因此回退，完整 M1c 与 successor 执行仍未接受。

报告静态检查：全部本地链接目标存在；`git diff --no-index --check /dev/null <本报告>` 无空白诊断（新文件差异状态为1），被审计划 SHA 保持不变。共享树出现另一份相邻设计审查报告；本审未读它形成结论，也未修改它。
