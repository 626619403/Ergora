# B3.3c2 执行记录／接线合同独立设计审查

日期：2026-11-15。审查者为 fresh-context 独立 reviewer `training_execution_records_plan_audit`，先读原始要求，再读候选及实际调用者；未继承作者或 c0 的通过结论。本报告只审设计，不认证 c2 产品实现。

## 固定范围与结论

产品基线为 `75285e3271bb93271eaea050ca7812cb0cd98b5a`，分支 `refactor/architecture-foundations`。候选 [执行记录合同](../plans/2026-11-15-training-execution-records.md) r1 的完整 SHA256 为 `e304167951b3e048eeb93c19c6096676c7f7b75fed363d554b1c2f636c9e9e55`；上位 [真实执行设计](../plans/2026-11-15-training-managed-execution.md)按固定快照 `235a5b58c3e596aeff56b0c5b8cf68b27d03fcac8670c2815a2c6a7d62e4c48c` 审查。

原始要求为 `.ergora/checks/training-managed-execution/c2-record-design-r1/raw-requirements.md`。22 份逐字范围清单为同目录 `scope.json`，SHA256 `bb2d9abdb7bb1391ba8bb017df6891f50d3e9f5948ad872241e75ac7ac8de751`；全部固定快照与清单相符。审查期间仅上位计划当前文件发生状态记账变化，未混入本次固定合同。核对原件为 `.ergora/checks/training-managed-execution/c2-record-design-r1/audit/scope-integrity-final.json`，SHA256 `9ee06ad22a06a4676acbfab8c1d9a9c08bbaa6ba68545ad53fe928896761b487`。

|审查轴|r1 结论|开放 finding|
|---|---|---|
|需求／行为正确性|request-changes|R1、R2、R3；均为设计合同问题，非已实施的 c2 缺陷|
|结构／可维护性|request-changes|R1 的观察入口依赖、R2 的授权输入及来源边界未闭合；未发现需要新增调度器、账本或通用执行框架的理由|

c1 自己的 CI／原独立终核仍按其原门禁处理；本报告不转授 c2 实施。kernel 专家继续留在 v3 提案路径，不获执行、release 或采用权。

## R1 · P2：拟复用的只读入口在 reader 之前拒绝来源漂移

位置：候选第 9、25、72 行；实际 [reference.py](../../src/ergora/reference.py) 第 505–526 行。

合同要求离线 execution 可读取已退出 owner，并说明历史身份与当前来源漂移，却把 `_training_process(..., sdk=False)` 列为只读接缝。该 flag 只省去 SDK 可用性检查；第 512 行仍无条件 `validate_installation(..., training=True)`，之后才启动目标模块。选定 native 安装缺文件、文件变化或 descriptor 不完整时，reader 根本没有执行机会。若 reader 再依赖应用 `_Submission`，它还会在 `_TrainingProject.__init__` 导入所选 native core／adapter，与独立观察漂移的目标冲突。

可达场景：原 job 已有 request／attempt／ack／stopped，owner 已退出，随后安装升级或缺源。用户只想核对原件，入口却只返回当前安装校验错误，无法呈现已有停止事实及 unknown 的范围。便宜探针调用实际 `_training_process(..., sdk=False)`，选定一个缺源目录：得到 `Unsupported reference runtime identity`，reader 子进程未进入，SDK 也未导入。这是入口行为证据，不是 c2 运行验收。

最小修正：在合同中明确 execution 观察采用随包固定来源的 stdlib reader 接缝，先定位并严格读取原件，把当前安装／gate 的漂移作为独立观察项；不先校验或导入所选 native 安装，不依赖 `_Submission`／State／SDK。可复用已有 `reference.training_files` 第 429–450 行的 `-S`、随包来源与有界独立读取方式。显式 execute 的实际准入仍须严格验证所选来源，不能借此放宽。

验收应让实际 execution CLI 在缺 SDK、已退出 owner、缺失／变化 native 来源下保留原文件字节并读出历史事实；同时确认同一条件下 execute 拒绝新工作。探针原件为 `.ergora/checks/training-managed-execution/c2-record-design-r1/audit/readonly-source-preflight.json`，SHA256 `ed0beb72654d50bc49cbc5bd4753ae816c28034d18f57cfcf8ad47a625b3a140`。

## R2 · P2：原锁内最后 gate 的完整授权输入仍未具体化

位置：候选第 25、31、43、45–47、72 行；上位固定合同第 89–96 行。实际 [reference_training_budget.py](../../src/ergora/reference_training_budget.py) 第 422–433、491–496 行，[budget_clock.py](../../src/ergora/budget_clock.py) 第 31–57 行，以及 [reference_training_runtime.py](../../src/ergora/reference_training_runtime.py) 第 11–41 行。

r1 已给出 `owner.context_sha256`、`launch.clock_sha256` 和“再核 compute／owner”的目标，但未定义 native callback 得到的 cached context、policy 与这些摘要的反算关系。native gate 按合同不能 import `BudgetedStart`，所以不能默认继承 `validate_cached` 中对完整 context SHA 的实际校验。`budget_clock.validate(clock, wall_seconds)` 只核 wall clock，不绑定 `cleanup_seconds`；只传入一个同样有效的 clock，不能证明执行仍使用原 compute 窗口。

具体反例：同一合法 60 秒 clock 在原 cleanup=15 时只有约 45 秒 compute；若跨进程接线把 cleanup 传成 0，clock 本身仍完全有效，但 `remaining` 允许约 60 秒工作。这里没有证明未来实现会传错；问题是目前列出的严格字段／最终 gate 步骤没有要求拒绝这种完整 clock、错误 policy 的输入。原函数便宜探针观察到约 15 秒差额。

同一授权边界还有未完成的来源集合：第 31、72 行列出的固定映射包含新 execution、budget、worker，却没有具体纳入已计划复用的 `_Submission`／`_TrainingProject`／`reference_training_runtime.lookup` 等完整原件、登记、run/history/memo 校验实现。worker 已直接 import submission；runtime lookup 拥有完整初始 Experiment 检查。仅说“实际 import 增加时再调整闭包”，尚未完成本片要求的实际 critical 来源盘点。活 owner 出生后若这些原校验源码变化，仅核当前列出的文件不能证明仍使用出生时的身份门禁。native 279 文件 validator 不覆盖这些应用源码。

最小修正：补一段最后 gate 的明确输入／反算顺序：严格读取同一出生 owner；`canonical_sha(cached_context) == owner.context_sha256`；由该完整 context 和原 intent／authorization 反算原 policy、authorization 引用与 `clock_sha256` 的确切定义；compute 一律扣原 cleanup reserve；对实际用到的原登记／业务来源明确哪些从原件重读、哪些以出生冻结 context 为权威，不能把任意当前同路径值当原值。列出实际复用的授权谓词及其完整 critical 源码集合，native 逐字核这些应用源码而不 import 它们。无需复制 clock／manifest 算法、扩散 State 到 native 或另加 RPC 客户端。

同时须把新增 admission／execute 的 allowance 明确为 compute，fence／cleanup／publish 为 total：当前 `_BudgetPhase.expired` 第 91 行对所有非 monitor mode 都使用 total；仅把新名字加入 mode 集合不会满足上述合同。原 `validate_cached` 的完整绑定语义应保留在适当的协议边界。

验收应保留同 clock 但 cleanup／context 改变、clock 引用不匹配、关键应用来源改变、原 request／完整 Experiment／run memo 漂移的拒绝场景，均在 attempt／业务 result／Git 之前拒绝。clock 原件为 `.ergora/checks/training-managed-execution/c2-record-design-r1/audit/clock-policy-binding.json`，SHA256 `2140aecfbb21be6f4139a8b6ca4fabe2d7317a644c21bfcf7e31e711e97eb763`。

## R3 · P2：完整可见的 stopped 尚不等于已同步的持久 stopped

位置：候选第 19、49、65 行；上位固定合同第 106–108 行。实际 [training_cycles.py](../../src/ergora/training_cycles.py) 第 273–290 行及 [reference_training_budget.py](../../src/ergora/reference_training_budget.py) 第 407–420 行。

合同正确要求 stopped 在实际 reap／匹配帧之后由同一 S 直接发布，stop fsync 卡住时保持持久 unknown，并允许将来离线核对 stopped。但目前未定义离线 reader 怎样判定其“持久”。原 `_record_bytes` 先 `os.link` 出完整目标，再同步目录；S 可在二者之间被 total 截止终止。此时完整匹配文件已可读，仍无已完成目录同步的证据。仅检查 exact fields／所有 SHA 会把合同要求保留的 durable unknown 提前变成 true。

便宜探针只执行实际源码中 AST 选出的 `_record_bytes` 函数，在其目录同步点注入错误：writer 报错，完整目标仍可见。没有运行 c2 或模型，也未生成受管停止证明。这个窗口与计划复用的 writer 顺序相同。

最小修正：具体区分 `reap_record_observed` 与 `durable_stop_confirmed`。离线读取若要确认持久性，应按既有 `durable_fence` 的同一可见原件恢复原则，重新核完整身份／原 bytes，同步该现存文件及所需目录，重读身份后才确认；同步失败或耗尽观察窗仍为 unknown。也可选择纯读取始终不升级 durable 状态，但需删去仅凭可见 stopped 即可恢复持久确认的承诺。允许同步时须明确它不改原件、不补缺记录、不返回 launch／attempt 权限。

验收应覆盖真实“link 已可见、目录 fsync 卡住”的停止发布，再用新进程观察；在同步完成前持久停止仍 unknown，之后只核同原件恢复。探针原件为 `.ergora/checks/training-managed-execution/c2-record-design-r1/audit/stop-publication-window.json`，SHA256 `d99eac16ffb92b9b86c03eaade56d05ad0b6518d1ce02273cfd59b081fb3a38e`。

## 已沿调用链核对的设计部分

- **原锁内 gate 可接入。** b delta 在原 executor.lock 内、旧 started 检查后、Git／started 与业务 try 之前调用 callback。拒绝不落 native 业务 result；已有 result 在 callback 前只读返回，不能追认 managed attempt。候选保留这一区分及完整 native request／Experiment／runner 绑定，没有理由改原 delta 或复制 executor 主体。
- **单次 launch 的保守消费设计成立。** execution 锁内先确认不存在，再发布／同步后只返回一次内存许可；既有／部分目标、丢帧、Popen 失败、hook 前强杀、attempt／ack 缺失均不恢复许可。它链接原 start slot，不成为第二 start attempt。仍需产品片实际跑这些中断点，文档并非已验 exactly-once 实现。
- **回收顺序可由现有 owner 实现。** 原 `processes.run(supervised=True)` 在专用 S 中启 subreaper、kill/wait 主 child 并收养回收其后代后才返回；c1 的两帧及父侧非阻塞 poll 可供多 phase 监管。候选明确 stopped 后 S 不再 spawn，持久 stop 直接在 S 内完成，未重引 c0 r1 的 publisher 遗留问题。父侧只能收完当前 peer 后 finish，不应因一个存储卡住的活 peer 阻塞其他 peer 的 poll。
- **并行停止保留正确所有权。** 设计把执行 stop 与 registry／fence／RPC 分开，仍使用原 cancellation 的 attempt/history。实施时本地 pidfd 通知必须放在明确本地取消意图及原 receipt/run 归属后、远端 lookup/signal 可能阻塞之前；发通知失败只记 unknown，不能补发远端 signal。`request_stop` 当前只置内存 flag，调度循环须及时 poll／送 TERM 再进入可能等待的工作。
- **旧 schema／恢复边界清楚。** schema1 原件继续严格读；parse 与 alive 分离；能力只能出生写入，旧记录、旧恢复、普通 start／queue/status 不生成请求或执行 S。失联只观察 unknown，不重启 owner，不归还 slot；缺 attempt／ack 时即使实际 reap 已观察也不补造 managed 成功。
- **新增模块有内聚职责。** 协议模块的应用 reader/writer、S、native callback 是实际跨解释器消费者；应用 execution owner 隐藏同一显式用例的装配和监管，单 owner 文件并不需要伪造复用。没有新实现族，无需 ABC／全局 registry。原实验账本、比较、MLflow、release／人工采用权保持在原 owner。
- **SDK 表述准确。** 候选第 108 行已清楚区分新 gate 独立导入闭包与冻结 executor 的 native SDK 依赖；原 `training_executor -> agent_platform.training -> perf_temporal.client` 确实导入 native SDK。独立 `-S` gate 导入和完整所选 native venv 执行需分别验收，应用 SDK 不能代替 native 依赖。

## 检查与边界

已读根／源码／测试 AGENTS、当前 PLAN、组件变更协议、maintainable-project-delivery 独立 brief、ergora-codebase-quality 三份对应参考；逐份核固定 22 件及相邻 production callers、已有 architecture／submission／runtime 接缝。额外只读文件身份记录为 `.ergora/checks/training-managed-execution/c2-record-design-r1/audit/neighbor-identities.json`，SHA256 `7b8480229ce6146913161bb304f24852923b82625d6160e701081acfb4835ed3`。

只做了三项 stdlib／原函数便宜探针与快照／链接检查，未启动服务、模型、训练或受管执行，未安装、修改产品、commit、push 或外部写入。探针均同步结束，未留下后台进程；小型输入与输出仅留在授权 audit 目录。未重跑 c1 矩阵，不借其历史通过认证 c2。

R1–R3 修为具体合同后应由本 reviewer 固定新快照复核。本轮不能标 c2.0 设计通过，也不能进入 c2 产品实施。即使设计复核关闭，native venv／严格协议／原锁／once launch／并行实际 reap／stop fsync／真实 Temporal 短 CPU 全周期、两安装与自己的 CI，仍分别是未来产品节点的验收义务。

## r2 同 reviewer 复核：两轴设计通过

日期：2026-11-15。本节为同一片的修订复核，不替换上述 r1 结论和探针。固定 r2 的两份计划清单为 `.ergora/checks/training-managed-execution/c2-record-design-r2/scope.json`，SHA256 `7c259c4609eddbd97729dc05bad93f65d2bbf6e0b180d22ad2a6ad1104d67ec5`；候选执行记录合同 SHA256 `76b52029334441dccb71ffe9163172a9a3391dcb04738e60e3e31832720af9ad`，上位计划 SHA256 `41b507fd8c95b8fd937dddcd7a9652d11de13be3f6c5b1b83158b322694153be`。两份快照／当前文件相同，r1 另 20 份源码及协议逐字保持，产品仍为原 `75285e3271bb93271eaea050ca7812cb0cd98b5a`；上位变化仅为发布状态及具体合同入口记账。

|审查轴|固定 r2 结论|开放 finding|
|---|---|---|
|需求／行为正确性|approve，限设计|0|
|结构／可维护性|approve，限设计|0|

R1–R3 均在设计层面关闭：

- **R1 关闭。** 第 9 行明确把 execution 观察接到已有随包冻结来源、`-S` 与独立有界 reader；选定安装的校验／导入不再位于历史读取之前。外层仅选择已登记路径，reader 不 import `_Submission`／State／SDK；当前漂移单列，execute 保持严格来源准入。独立便宜探针实际调用既有 `training_files`：选定 native installation 不存在，仍返回离线空记录观察且 `runtime_status=not_queried`。它只证明现成接缝可用，不认证未来 execution reader。
- **R2 关闭。** 第 31–46、66–77 行将完整 C 的 canonical SHA 与出生 O 绑定，重读同一 intent／attempt／receipt／native request、原 authorization／cycle bytes，明确 policy、clock SHA 与原 cleanup reserve；ready 另由出生 capability 的摘要固定。新增 admission／execute 明确使用 compute，消除了现有“非 monitor 默认 total”带来的接线歧义。25 项 exact critical 集合已包含原完整身份谓词和实际 JSON／schema／文件／State owner；本次核这些原方法的实际调用，未发现还需 native import 应用框架的部分。native 对原登记四件及 baseline_files／experiment.files 的复核沿既有路径、bytes／canonical 身份，只绑定出生已验证内容；当前 DB／原 history／memo／QUEUED 仍由应用原 owner 在 launch 前核验，未伪称跨服务原子准入，也未加第二 DB／RPC 客户端。
- **R3 关闭。** 第 79–85 行明确 `reap_record_observed` 与 durable 确认分开，允许有界观察进程只同步现存的同一条完整原件链及必要目录，再核原 bytes／身份；失败／超时仍 unknown。观察可晚于执行预算，却不能改原 clock／final／overrun、补文件或返还执行许可。便宜本地探针确认现存普通文件可以经只读 fd 做 fsync、同步目录并保持 bytes；真实 link／fsync 阻塞及新 reader 恢复仍是产品验收，不能用该探针替代。

复核重新核了 registration 四文件位置、原 observation 的 state/config 前缀、`BudgetedStart.context/validate_cached`、原 clock 与 mode allowance，以及随包 reader 的装载方式。未发现本次修订破坏单次 launch 消费、原锁内拒绝无业务 result、stopped 后无 spawn、独立 safe-reap、旧 schema 不升级或原 cancellation 唯一远端 signal 的设计边界。产品接线仍须让 `request_stop` 后及时 poll／送 TERM，所有可能阻塞的存储／RPC 留在受监督子树，保留同片具体运行证据。

复核证据只位于授权 audit 目录，均为代码路径与 SHA，不作为产品运行通过：

|原件|SHA256|
|---|---|
|`.ergora/checks/training-managed-execution/c2-record-design-r1/audit/r2-scope-integrity.json`|`52639e683da42f535309c5823077a6f1eb1103c9f8383fe7f83c34841f1defc0`|
|`.ergora/checks/training-managed-execution/c2-record-design-r1/audit/r2-readonly-seam.json`|`042f60a22f2ca56745e3f6b8f84c64367552d5b83a77a894fbedc33652427e6f`|
|`.ergora/checks/training-managed-execution/c2-record-design-r1/audit/r2-readonly-fsync-seam.json`|`a0a4e66f847b972d89a661376fae964d7826ce427ea65f2e31b9eacaf19582d5`|

本次只新增两项便宜接缝观察和静态核对，没有安装、服务／模型／训练、产品修改或后台进程。设计通过只关闭 c2.0 的合同 findings；c2.1–c2.5 尚未实施，也没有继承 c1 的运行／安装／CI 成功。c1 自己的 CI 与原独立终核须由其原门禁精确闭合后，才可按既有授权推进 c2。kernel 专家仍在 v3 提案路径，没有执行或采用权。
