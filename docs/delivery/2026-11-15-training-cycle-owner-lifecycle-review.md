# c1b1 产品独立审查：原预算根的跨调用生命周期

日期：2026-11-15。Reviewer：fresh-context 独立产品 reviewer `training_cycle_owner_product_audit`。先读原始要求、[批准的具体设计](../plans/2026-11-15-training-cycle-owner-lifecycle.md)及[原 r2 设计审查](2026-11-15-training-cycle-owner-lifecycle-design-review.md)，再读候选、相邻调用者和运行原件；未继承实施对话。原始目标是逐片补全可取消、可恢复、不重复启动的训练优化循环，每片用自身模板并独立审结构、可维护性及冗余测试。本片只审内部单候选 prepare → 调用方直接子 Popen 根 → 完整确认 → 原 SDK start，以及只观察恢复；总 Workflow、多轮、服务、公开入口和 WA／BR 排期不在产品范围。

**固定 r1 结论：需求符合性 request changes；可维护性 request changes。** 两个源码 finding 为 R1／R2；测试配置 finding 为 S1。R2 同时构成具体职责耦合。整片验收尚未完成，不能由这次静态审查或首个正向用例替代。以下结论只对应本页记录的固定输入，不覆盖主控后续候选。

## 输入身份与边界

基线／HEAD 为 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。工作树预先应用 13 文件未提交候选，原 patch 90,331B、SHA256 `de7477a46337f602d9be308ddf4481b36103433bd420563744c59724d16ad579`；私有 `product-review-r1-scope.json` 记录全部文件字节数／SHA256。Reviewer 实际逐一重算，13 项全部一致，无额外原始 untracked 产品输入。设计合同来自固定 `4d060ae8609424cc2f6f5f0b44393da7e2ba03f7`，这次基线只多了此前的 docs 检查点。

准确输入为：

- Docs：`docs/PLAN.md`、`docs/delivery/2026-11-15-backend-review-and-reporting.md`、`docs/delivery/2026-11-15-training-cycle-owner-lifecycle.md`、`docs/plans/2026-11-15-workflow-evidence-and-human-gates.md`。
- 产品：`src/ergora/reference_training_budget.py`、`src/ergora/reference_training_submission.py`、`src/ergora/reference_training_worker.py`、`src/ergora/training.py`、`src/ergora/training_execution_protocol.py`。
- 测试：`tests/fixtures/training_budget_client.py`、`tests/fixtures/training_cycle_operations.py`、`tests/fixtures/training_submission_client.py`、`tests/test_training_submission.py`。

已读根、源码、测试 AGENTS，[组件变更协议](../architecture/component-change-protocols.md)执行／证据及检查章节，maintainable-project-delivery／independent-review、ergora-codebase-quality 的 style／module／test refs，以及 code-review 两轴要求。此次已是外层工作流的新独立 reviewer；按仓库规则不递归启动“审查的审查”。仅写本报告与本 reviewer 树的 ignored 小核查原件；未修改产品、测试、CI、其他工作树，未安装、提交、推送、启动长期 owner 或训练。

## 需求符合性

### R1 · P1：交接前通知异常使真实根的等待被跳过

位置：[worker](../../src/ergora/reference_training_worker.py#L208) 的 `discard_root`，特别是第 215–222 行；取消传播在同文件第 294–309 行。原设计要求交接前保留真实 Popen／晚到句柄，精确 TERM 并保留实际 wait；无法及时停止时仍保持真实等待与 unknown。

可达场景：准备回复已产生根，确认尚未完成，调用被取消或耗尽窗口。`discard_root` 先关闭 stdin，再判断 `poll() is None`，随后读取身份并调用 `processes.notify_identity`。根可以在 poll 与通知之间自然退出；原 identity 对 zombie 会抛 `ValueError('Original process has exited')`。pidfd／信号失败也可抛 OSError。这里只捕获了等待 spawning 时的 OSError，通知周围没有保证继续等待的 finally，异常会直接跳过后面的 poll／wait。取消路径的 `running.result()` 随后把这个异常抛给调用者，覆盖原 CancelledError。

独立最小实证只使用两个真实惰性子进程，没有预算 owner：保留真实 Popen、原 `discard_root` 和原通知算法，用可控交错让 EOF 退出恰好发生在 poll／notify 之间。实际得到 ValueError，返回时 `returncode=None`、wait 调用 0；另一个 notification OSError 接缝同样 wait 0，子进程仍活。独立 harness 最后分别真实 wait 得 0／-15，两个 `/proc` 均消失。原件在 reviewer 私有 `.ergora/checks/product-review-r1-discard-probe.py`／`.json`，SHA256 分别为 `977bee742760b512eb2aad44aa750b636c18df48ecee020b978a0cfe398d935b`／`d46d73a4fda4dc669056ea2d80c530fbab9c641f7c2f2693191524b22a335eff`。

影响：交接前生命周期责任提前退出；通知失败时可遗留仍活的根，自然退出时也没有履行显式等待，错误还掩盖取消。不能把 unknown／抛错当作已完成收尾。

最小修正：把通知结果与实际退出等待分开。不论通知是否成功，都持有原 Popen 并继续异步 poll，退出后再真实 wait；自然退出竞态可经原句柄重新确认，其他通知失败须保留原因和 unknown，不能吞成停止成功。重复取消仍不能中断该清理，原取消不得被无关收尾异常替代。用上述 EOF／通知失败接缝以及原 pending-Popen／确认前取消序列复核，不修改原 reaper，也不强杀尚在收后代的根。

### R2 · P2：owner 损坏阻断已有 attempt 的原 receipt 对账

位置：[worker](../../src/ergora/reference_training_worker.py#L454) 在区分 reconcile 前调用 `_cycle_target`；该 helper 第 339–345 行只对缺文件降级，要求现存 owner 必须完整可解析。真正的 `reconcile-candidate` 分支在第 481–493 行。对照原 [submission](../../src/ergora/reference_training_submission.py#L367) 的已有 attempt 分支和第 290–303 行原 reconcile。

可达场景：原 attempt 已同步、SDK 接受的回复丢失，随后 owner 文件部分写入／损坏。对账只需原 intent／attempt／workflow／memo，不能再发 SDK start；但新路径先解析 owner，坏 JSON／不完整 owner 会令 H 提前返回 unknown，根本到不了原 reconcile。原 status 的 `BudgetedStart.observe` 本来会单独报告 owner unknown，不需要由 owner 的可解析性阻断同一远端事实的恢复。

独立小接缝读取原 r3 的真实 intent／attempt，保留实际 `_candidate_operation`、`_cycle_target`、`_Submission.load` 与 parent binding，把 owner lookup 只重定向到 reviewer 自己的缺失／坏 JSON 文件；reconcile 使用无网络 spy，避免写原运行记录。缺 owner 时进入 reconcile 1 次，坏 owner 时 JSONDecodeError、进入 0 次。该接缝只证明控制流阻断，不认证 SDK 或 receipt 写入。原件 `product-review-r1-reconcile-probe.py`／`.json` SHA256 为 `0e07173834079ffbeddc0f712a454a2b86159d5ec820e76c3da43e94150c7a05`／`e50512f68135d5a290783b41b4968526c2b3676042c622fa7b4c658a1f44ce41`。

影响：批准恢复表中的“attempt 有、receipt 无”无法直接沿原算法恢复；观察需求被耦合到启动／通知才需要的完整 owner 身份。该故障 fail closed，没有证据表明会重复 start，但它会使可恢复的原接受事实持续未知。

最小修正：恢复的 intent／attempt 定位与 owner 观察解耦。已有 attempt 的 reconcile 直接走原算法；owner 损坏独立输出 unknown／原因，不恢复执行权。confirm／dispatch／notify 仍须完整校验 owner，不放宽它们的身份条件。验证坏／缺失／已退出 owner 下同一 attempt 的 memo 对账与 NOT_FOUND，核 SDK start／Popen 都不增加、原 attempt 不变；无需新账本或可 dispatch 的 resume。

## 可维护性、职责和测试

### S1 · P2：故障测试提前用固定等待截断合法操作窗口

位置：[tests](../../tests/test_training_submission.py#L1194) 的取消／丢回复／pending-Popen 测试，第 1216、1261、1302 行分别等待固定 20／20／15 秒；它们显式选择合法的 30 秒控制窗口。第 1478／1547 行迁移到同一多 H caller 的旧用例仍保留固定 12 秒前置等待。

证据：固定 r1 的 source-r4 完整 JUnit 为 **9 项，7 passed、2 failed，289.49 秒**；失败分别为 sdk-start 与 lost-prepare-reply，均在硬编码 20 秒先断言 marker 未出现，没有实际进入所声称的取消／丢回复边界。它们不能解释为产品通过，也不能仅凭这两个失败判定 SDK start／丢回复语义有错。原 30 秒窗口仍有剩余、H 仍在正常导入／准备时，这些测试已提前失败；原 r3 正向序列也实际用了约 24 秒。

这违反适用 skill／仓库协议中“有效配置优先，测试预期随配置”的规则，并引入了与被测合同无关的机器启动速度假设。最小修正是等待本次实际 operation 窗口或操作终态，在真实 marker 到达后再注入取消；若原窗口已尽，则明确报告边界未覆盖。分别处理操作窗口与必要的真实收尾等待，不通过放大固定常数或限制有效预算掩盖问题。主控已通知正在修正／重验，但未提供后续固定候选前，本报告仍对 r1 保留此 finding。

R2 也是维护性 finding：现有 `_cycle_target` 为通知／执行链观察持有完整 owner 责任，新恢复消费者直接复用整个 helper，让本不需要 owner 的远端对账承担其失败条件。应复用原 `_Submission.reconcile` 及原 status 的 owner 降级，而不是再写恢复算法。

其余已检查职责未发现独立结构阻断：`training._prepare_submission` 保留原事务准备，手工 `_submission` 复用它；root／H 的注册环境由同一个 `_select_cycle_project` 负责；window 校验留在 stdlib protocol，真实最后点由 BudgetedStart 消费；`_CycleCandidate` 持有一次在内存 offer 和真实 OS 句柄，没有新持久账本。私有算法、框架入口和内部 start 接缝有本片责任，不能因单 caller 或源码长度自动判冗余。本轮未发现需删除资源身份／锁／外部输入检查的证据。新增序列测试覆盖跨 H、正常 loop 关闭、取消交接、丢回复和最终漂移，价值在真实序列，不应压缩成 argv／helper 返回字段断言。

## 已核行为、证据及未验收边界

静态沿真实调用核了 prepare 的唯一 `created=True`、intent 目录同步、schema2 `ensure_owner` existing-only、原 schema1 launcher 保持、confirm 的完整 owner／锁／context、最后 SDK gate 的原 window／owner 重读、attempt-before-send，以及 reconcile 不进入原 resume 的 dispatch 分支。父异步路径只处理材料、OS 身份和时钟；未发现业务 State／SQLite／业务原件读取或业务线程。实际创建只用 `to_thread(Popen)`，传送用公开 pipe，观察用 poll，未改 reaper 或使用 private detach。以上是源码判断，不能替代运行边界验收。

独立直接读取 source-r1／r2／r3／r4 JUnit 和对应身份原件：r1 原 7 秒正向 unknown 失败保持；r2 pipe.close 后多余 abort 的 AttributeError 失败保持；r3 修后单正向 1 passed／24.40 秒，实际 case time 23.798 秒；r4 为上述 7／2。r3 确实沿真实原 owner 核短 S-H 和正常 asyncio.run 关闭后的存活、第二调用不再 SDK start、同 window、授权 bytes 及最终收尾，但没有覆盖整片。r4 已通过 confirm／lookup／attempt-sync 取消、pending-Popen、window／owner 漂移和一项旧 accepted 迁移；两个未到边界的失败不能计入这些能力。

Reviewer 另执行五源码 ast.parse、`git diff --check`，逐字比较 **283 个 tracked reference 文件与基线全部一致**，AST 核 **GATE_SOURCES 原 25 key 及顺序保持**；依赖／CI 文件无 diff。两个小核查均用现成 SDK 解释器、固定 reviewer 源码，无安装、网络、长期 owner 或模型训练；其惰性子进程已由各自 harness 全部收尾。它们不证明原预算后代树或真实 SDK 服务通过。

以下仍是本片门禁：R1／R2 修正与同 reviewer 复核，S1 固定新候选的边界重验；同一原 clock 下真实 owner 的正常退出／父崩溃与精确后代收尾、唯一 offer 并发／丢确认回复、窗口累计耗尽／stdin 取消、已有 attempt 的 receipt 对账、其余 schema2 迁移与 schema1 回归；新 core／SDK 非 editable 包同一性、SDK-free 原读取、自身原模板、完整适用回归和全部收尾记录。具体运行证据须按各候选身份归属。Popen OS 创建 pending 时 default executor 正常退出可能等待它，是批准设计已公开的限制，本轮不另要求 launcher 框架。

总 controller stop 仍另走原 b2b veto／逐 owner 通知／drain／执行链观察；普通活动取消不是该流程。c1b2 两真实服务与 normal／stop 配额、c1c 总 Workflow、c1d 接受／后继轮均不由本报告提前关闭。原六阶段、固定 RUNNING history、非归还 start／native launch、原批准及预算身份、唯一 reaper 和 kernel 专家 v3 继续保持。

## r2 固定候选修正复核：2026-11-15

同一独立 reviewer 复核同片修正。本节之前的 r1 正文保持原样：13,067B、SHA256 `4b83ee09a77f765d5e86717f7327081552485f9a999aa15aa39b82ddddc8dddc`。本轮继续只写本报告和 reviewer 自己的 ignored 小核查原件，不安装、不改产品／测试／CI、不提交／推送、不启动预算 owner 或训练。

准确输入为私有 `product-review-r2-scope.json` 及 `product-review-r2-snapshot/` 的 17 份完整文件，基线仍为 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`；tracked patch SHA256 `3a0766993e72ba01a6d387a7987b041bfeb193d917837064b1f5cdf364cbba6a`。逐一核算 17 项 bytes／SHA256 全部匹配。相对 r1，产品变动只有 `reference_training_worker.py`，51,766B／SHA256 `9393be3eb5650e23818fc3febb1a0c846f3bfe1294b3248a936006117f03a0b3`；测试变动只有 `test_training_submission.py`，214,955B／SHA256 `20fba973ccd93730616a0daa0877cb61e55a8fe8a45ed25f00078e2d655908f1`。其余四源码和三个 fixture 与 r1 逐字相同。新增 r1 报告和三份 WA 审计属于记录输入，本节只核身份，不重新认证 WA 产品能力或替代其原审查。

**需求符合性：所审源码 finding 已关闭，整片验收仍待完成；可维护性：本次固定修正 approve。开放源码／测试 finding 为 0／0。** 这不是整片产品门禁完成，也不继承尚在进行的安装／回归结果。

|原 finding|实际修正与复核|处置|
|---|---|---|
|R1 真实根等待／取消异常|r2 worker 第 218–229 行捕获身份／通知 OSError／ValueError后，仍保留原 Popen 继续 poll／wait；已退出的 EOF 竞态不误记成活根通知失败，活根失败保留 `cleanup_problem`。第 301–322 行取消分支 gather 内部结果并继续抛原 CancelledError。独立惰性反例中两根均真实 wait 1 次、returncode 0、proc 消失；通知失败有诊断，重复取消加内部观察异常仍抛 CancelledError。|关闭。未改原 reaper、未加长期 wait 线程或强杀根。|
|R2 owner 与恢复耦合|第 339–368 行在原 worker 内拆出 `_cycle_submission`，原 `_cycle_target` 为通知／执行链观察继续读取严格 owner；candidate 的 intent 定位改用前者。第 503–515 行仍在原 submission 锁内检查原 status，只有既有 attempt 且无 receipt／rejection才直接调用原 reconcile，不经过 resume。坏 owner 的降级沿原 `submission.budget.observe`。独立原只读 spy 在缺／坏 owner 两种情况下均进入 reconcile 1 次；r6 sdk-start 实际序列另核原 receipt 恢复、owner_status unknown、坏 owner bytes／attempt 不变、start 次数不增加。|关闭。原 intent／controller／ordinal 绑定未删；不会因观察恢复补 Popen 或 SDK start。|
|S1／主控 R3 固定边界等待|原 20／20／15 秒的三个子 start 边界等待，以及迁移 caller 的两处 12 秒等待，均改成同一 `operation.preparation.expired()`／任务终态。先等真实 marker 再注入故障，预算／源码协议未为测试改值。r6 重新完整运行九个生命周期 case，通过。|关闭本 finding。没有把 marker 未达解释为已覆盖故障。|

独立小核查原件为 reviewer 私有 `product-review-r2-probes.py`／`.stdout`，SHA256 `54d08dad2e4e7b8553ef77fefd8ae26f40ef2de0f7032d6b716d0a5d82ab3622`／`4d0186ec9b208eedfb4e25360b14bb6fe4fec605cebd432b7c79db1a60b08841`。核查输出自报实际导入的 worker SHA 与固定 r2 相同。清理使用真实惰性 Popen；重复取消的内部异常为小接缝；恢复继续使用无 SDK spy 和原 r3 只读 intent／attempt，不写旧运行原件。两根已实际退出并等待，原 r1 红反例保持。

复查严格 gate：confirm 仍执行 `require_active(owner=True)`、完整进程与 context 比较；dispatch 仍传完整原 operation，原 `ensure_owner` 的 existing-only、同原 window／parent／confirmed owner 最后点、attempt 前后 preflight、固定 RUNNING history 和父共享许可均未放宽。`_cycle_target` 的严格 owner 来源比较仍供 notify／执行链观察；只观察恢复不需要它授予执行权。schema1 launcher、原 budget `own`／phase reaper、原协议／GATE_SOURCES 及依赖文件本轮未改。拆分 helper 隐藏了可达的失败条件，而非新增调度层或重复算法。

S1 的五处“等待子 start 到达边界”已修正。现存 registry／execution-request 的若干有限 harness 等待发生在 start 已完成之后，属于原 budget worker／native 的另一生命周期，不能一概套用这个子 start window。它们仍需相应迁移／回归的实际结果；本轮没有只凭固定数字增列未实证 finding，也没有据此认定那些用例已通过。

已直接读取终态原件：

- `source-r6-cleanup.xml` 为 2 passed、0 failure／error／skip，1.954 秒（stdout 1.96 秒）；JUnit SHA256 `6ab18fd5bace4a00cb8cbdbdcd0b44623650e39c5105c6d87a607474be357a00`。覆盖真实 EOF 通知竞态及通知 OSError，原 r1 失败未覆盖写回。
- `source-r6-lifecycle.xml`／stdout 为 **9 passed、0 failure／error／skip，160.69 秒**，覆盖同根跨调用／正常 loop 退出、确认前和 lookup／attempt-sync／SDK 回复等待三个确认后取消、丢 prepare 回复、晚到 Popen、最后 window／owner 漂移。新增坏 owner 的实际同 run／memo 对账位于 sdk-start case 内，不另计一个 case。`source-r6-inputs.json` 的五源码和四测试／fixture共九项 runtime 输入逐一匹配 r2 固定摘要。
- 固定 r2 的九份 Python 输入均 ast.parse 通过；四个未改源码与 r1 逐字一致。本轮没有重复运行长期 owner、昂贵 suite 或安装。

r6 的 9 项通过属于这个修正候选；原 r4 的 7／2、r5 的两项及 r3 正向各保留原身份。当前材料中的 build-install-r1 在最初交付 scope 中仍标在途，本节尚未验收其产物、双安装逐字身份或安装回归，不据后续目录存在推定通过。

后续仍须用准确终态和输入身份闭合原计划：其余 schema2 迁移与 schema1 手工回归、新 core／SDK 非 editable 包同一性、SDK-free 原读取、自身原模板、适用回归及全部实际 owner／后代收尾；原验收表中未由当前九项覆盖的并发唯一 offer、累计窗口耗尽／stdin 取消／窗口尽后的晚到句柄、实际预算根在父进程崩溃后的观察、仅对账的 NOT_FOUND 等，应复用适合的既有接缝逐项核覆盖，不能用 helper spy 或惰性根概括通过。Popen 创建 pending 时正常 executor 退出可能等待它的已批准支持限制仍保持。后继服务／配额、总 Workflow、下一轮和 WA／BR 的范围没有改变。

## 自身模板后新增边界复核：2026-11-15

本节之前的 r1／r2 正文保持原样：19,815B、SHA256 `176e24e26aa61400d725d87403666c598ec4f65e9710aaff0461cf37bcf9c12d`。主控提供自身原 `ergora-structure-review` 的真实 Codex 终态 request-changes，91.711 秒；reviewer 直接读取其 `self-review-r1-codex/review.md`（2,499B／SHA256 `2b479d37b7092eabad919678ae9f9e50053e53e0ffd4994f83207c94f799cfbf`），再独立核源码和可达场景，不把模板意见直接当结论。本节没有重新认证该次供稿 19 文件／三资源的完整输入流水。

### R4 · P1：全 loop 取消会绕过实际 spawn 或活动 S-H 的收尾

位置为固定 r2 worker 的 `_CycleCandidate._run` 第 253–256 行、`discard_root` 第 209–229 行，以及原 `_CycleOperation._run/run` 第 100–154 行。

场景一：main 在交接前、Popen OS 创建尚 pending 时返回，`asyncio.run()` 收尾会直接 cancel 所有 Task，包括外层 run、内部 `_run` 和 `to_thread(Popen)` 包装 Task。shield 只能挡从 await 传播的取消，不能挡 Task 自身被直接 cancel。原 `discard_root` 此时 await 已取消的 spawning Task，会得到 CancelledError 而拿不到随后由 OS 线程产生的真实 Popen。r7 的真实 caller 红例实际得到 `operation.root=None`，线程记录的 Popen 却已存在；它由测试 finally 另行收尾。原 caller-only cancellation 和成功交接后 normal-loop 测试均未覆盖这个交错。

场景二：同样的 cancel-all 发生在短 S-H 活着时。原 `_CycleOperation._run` 也可被直接取消，自己的请求停止、读管道和实际 wait 被绕过；其上层 `run` 只读取已取消任务结果，不能证明原 reaper 完成。candidate 随后进入未交接根的 discard，就失去了设计要求的“先实际 S-H 收尾、再通知根”的顺序。

独立最小实证使用固定 r2 的父 worker、既有 blocked-inspect fixture 与原 `processes.run(supervised=True)`，没有预算 owner／业务 State：在实际 H 与其新 session 惰性后代到达后直接返回 main。`asyncio.run()` 已返回、caller 已取消，但 `reap_frames=0`、`signalled=False`，S／H／后代三者均仍活。harness 随后只向同一原 S 发精确 TERM，原 reaper 清理后，三者身份均失活，另核三个 proc 均消失。stdout 和 loop-closed transport 诊断原 stderr 保持，没有强杀 supervisor 来伪造收尾。

该实证与下面 R5 的小接缝共用 reviewer 私有 `product-review-r3-boundary-probes.py`／`.stdout`，SHA256 `4fc3925465edefadf32720bb0558effda418b78713726aaef43260e128810775`／`29f1fe9a1dcb2879f939f0f08134c6e93ed66b622c72bc6316e7a15de7613919`。脚本自报实际父 worker SHA 为 r2 的 `9393be3e…`；子进程使用与本轮未变的原 S／fixture／reaper。

最小职责修正：Popen 仅 OS 创建可由局部公开 `ThreadPoolExecutor.submit` 持实际 concurrent Future，父 loop 只 done／result 观察，不再依赖可被 cancel-all 丢弃的 asyncio 包装。池不承载预算、文件或 SDK 业务，不新增服务／调度层；`shutdown(wait=False)` 不代表解释器最终不会等线程，原“OS 创建无限阻塞不能保证有界退出”限制仍成立。未交接 discard 自己的等待也须耐受直接取消。

同时，活动 `_CycleOperation` 必须在直接取消后仍沿同一现存 stdin／stdout／stderr／Process 完成原 S 的 TERM 请求和真实退出／读完；不重发 stdin，不复制或绕开 reaper，仍只在匹配 stopped frame 后才允许按原规则 kill S。spawn 边界收到取消时还须区分“spawning 已成功、Process 尚未赋给 self.process”与“创建 Task 自身取消且 stdlib 已完成未发 stdin 的 transport 关闭／等待”，不能一律推断未出生。实际 confirm H 全 loop 退出还应核 S-H 先于根通知收尾。确认后普通 loop 取消继续只能停止本次 S-H／观察，不把它升级成 b2b 总 stop。

**当前处置：部分修正，仍开放。** source-r9 的 concurrent Future／非阻塞轮询已在上述边界内，pending 根的全 loop 取消及原 late-Popen／EOF／通知失败四项均通过；但它未修改原 `_CycleOperation`，活动 S-H 的直接取消分支仍须准确修正候选和真实接缝复核。R1 原通知异常 finding 本身仍关闭；R4 是新增的直接取消触发路径，不能由 r6 的 caller-only 成功继承关闭。

### R5 · P2：最后 gate 的 owner 读取之后返回旧的相对 allowance

位置为固定 r2 [BudgetedStart](../../src/ergora/reference_training_budget.py#L376) 的 `dispatch_remaining` 第 383–387 行，以及 [SDK 最后点](../../src/ergora/reference_training_submission.py#L260)。原顺序先 `_start_remaining` 算正 remaining，再重读和完整比较 owner，然后把旧 remaining 交给新 `asyncio.timeout`。owner 的实际文件读取／进程身份验证若跨过原 deadline，返回时原窗口已尽，却仍得到一段新的正相对 timeout。S 的周期监管不能替代这一最后点。

独立小接缝保留原 `dispatch_remaining`，在完整 owner 读取中实际延迟 50ms，使原 20ms deadline 结束；方法仍返回旧正数。它只证明方法时序，不宣称实际 SDK 通过。主控 r7 的首次 deadline 红例在首次 ensure_owner 的 owner 读取就提前推进了时钟，尚未占用 attempt，故其 FileNotFoundError 不足以证明最终发送越界，原失败应作为错误注入接缝保留。

r8 只把注入限于已有 attempt 且直接调用 `dispatch_remaining` 的 owner 读取后，用原 H 的时钟接缝推进到原 window 之后。准确红例终态 1 failed／17.51 秒；reviewer 直接核原工作区，attempt 存在、receipt 存在、service starts=1，证明原最后点允许了该次发送。r8 不是实际等待完整 30 秒的文件系统慢读，但保留了实际原 caller、attempt、SDK 编码／memo 和最后点执行顺序。JUnit SHA256 `3b1e45b6c2d8ca8ccc3bba3c17b61b370012fbf5249d9bcbf77a1a7290e2a5cd`。

source-r9 最小修正保留完整 owner 比较，随后才 `_start_remaining` 重读原来源和执行条件，并把 parent OS 身份读取移到最后 remaining 计算之前；非正数拒绝，不替换窗口、不补启动、不返还 attempt。其 worker／budget／测试／fixture 四份完整 snapshot 逐一匹配 `source-r9-inputs.json`：worker SHA256 `812019428e519c25a7a6d1b617c773a22ad23bf8e876030f2dbebe3d63d2cd74`，budget SHA256 `6c85db0056b30a0e300b1e927f1695c0d635284dc3f66458dfdbab103f093524`。其余产品合同沿先前固定输入，未据动态主树替换身份。

**R5 关闭。** r9 准确终态 **5 passed／27.22 秒**，包含上述最终 deadline 反例修后、pending 根全 loop 取消、caller 取消 late-Popen，以及 EOF／通知失败两项。JUnit SHA256 `7757f699edd947e1530ef3028bb09e933539985d9e426e35b15aa63ac3f571cd`。这五项不能替代此前完整九项在新源码上的适用回归，也没有关闭 R4 活动 S-H 分支。

本轮 r7／r8／r9 snapshot 的逐项摘要均已直接核对；r7 两失败／24.641 秒、r8 有效最后点红例、r9 五项通过分别保留原身份。**需求符合性仍 request changes（R4）；可维护性仍 request changes（同一资源 owner 的直接取消清理尚未闭合）。** 安装 r1 已出现失败而尚无整套终态，本节没有认证其通过。原 R2 只对账恢复、S1 配置窗口修正及严格执行 gate 不因这些新增发现而放宽；scope 和后继服务／Workflow／下一轮限制继续保持。

## r3 固定候选复核：2026-11-15

本节之前的全文保持原样：27,395B、SHA256 `f5f4c68bcf713d6a79e75ecbabb461014eb96dabd1336aac723299cacd88081d`。继续只追加本报告，并在 reviewer 自己的 ignored 检查目录运行最小惰性反例；未安装、修改产品／测试／CI、提交／推送或启动预算 owner／训练。

本次准确输入为 `product-review-r3-scope.json`／`product-review-r3-snapshot/`，基线仍为 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。逐项重算 **21 份完整文件**的 bytes／SHA256 全部匹配；patch 为 131,948B、SHA256 `4c44c1ba9868c71cad357cc3795ed14e30df5fb1b9e037297692e8a967ed2160`。五份产品源码、六份测试／fixture和十份文档中，worker 为 54,159B／`9e30d9a985a48181940a76309a4869611fcb97e045087dbcba7af0e4bf51319c`，budget 为 36,988B／`6c85db0056b30a0e300b1e927f1695c0d635284dc3f66458dfdbab103f093524`；submission／training／protocol 与固定 r2 逐字相同。当前完整测试为 218,517B／`20cc4f857ddf7852d5f1912f0f8573e4db1692d413ec89d4118c7db0525a05bd`，submission fixture 为 11,296B／`97515eb9908d5b12000eea16e30fc5723dc2713eb3d23604326c7db6429ec51b`。snapshot 中的本报告只含初始 r1 正文，未覆盖 reviewer 后续追加；WA 资料继续只核输入身份，不作其产品验收。

**源码需求符合性：approve；可维护性：approve；开放源码／测试 finding 为 0／0。R4 关闭。整片最终验收仍待新安装件及剩余门禁，不由本节替代。**

### R4 活动 S-H 与 spawn 过渡

固定 r3 worker 第 108–184 行把直接取消留在同一 `_CycleOperation` 的资源责任内：创建成功但尚未取得 Process 时继续取得真实结果；只有创建 Task 自身已取消、stdlib 已关闭并等待尚未发请求的创建，才返回创建未完成的 unknown。现存 stdin Task 被取消后只关闭输入，不重发；被取消的 stdout／stderr reader 和 wait 则在同一现存 stream／Process 上继续观察。直接取消监督循环会请求停止，随后仍向原 S 发 TERM、读完并真实等待。只有原匹配 stopped frame 才能按原期限规则 kill S；未新增、复制或豁免 reaper。

外层 `run` 用 gather 保存内部异常，耐受重复取消直到内部实际结束，再保留原 CancelledError。candidate 在确认的 `operation.run()` 完成清理后才沿 finally discard 未交接根；完整 handoff 后仍不由普通取消通知预算根。根的 concurrent Future／真实 Popen 等待继续保留 r9 修正，线程仍只做 OS Popen 创建。没有新增业务线程、长期 wait 线程、私有 transport 操作或另一调度层。

Reviewer 用新原件 `product-review-r4-boundary-probe.py`／`.stdout` 重复此前活动 S-H 的独立红反例。父 worker 明确导入上述固定 r3；子 S／H 的 package path 同样优先指向该 snapshot，未改变相邻原 reaper，使用固定 r3 的既有 blocked-inspect fixture。main 在真实 H 及新 session 惰性后代到达后返回，使 `asyncio.run()` 直接 cancel 所有当时 Task。返回时 caller 已取消、`signalled=True`、两个原回复帧已读完、S 的 returncode 为 0，S／H／后代三者身份均失活且 `/proc` 均消失；没有进入 harness 的兜底通知，stderr 为空。该实证不使用预算 owner、业务 State 或 SDK 服务，证明的是此前确实泄漏的原 S-H 分支。

上述脚本为 5,297B／SHA256 `2ac8c230b93bb6772c442724a9844d3c5cfb0b6247c37c28ee30234fe5c9c237`，stdout 为 1,739B／`9f17a375c616586cfb71b5e88e0af1782d1d3cc3480f16e43d2c4ec77550ec06`。同一脚本另重复 R5 的原 20ms window／50ms 慢 owner 读取方法接缝，修后在原 deadline 已尽时抛拒绝，没有返回旧 allowance；它不认证真实 SDK。此前 r2 红反例及 stderr 原件全部保留，没有覆盖写回。

直接读取 `source-r10.xml`／stdout，终态为 **6 passed／49.43 秒**（JUnit 49.427），SHA256 `8b00570e603339704a010c49711d87ec658f7814d6550966fbba1169f26897d9`。`source-r10-inputs.json`／snapshot 的四份输入逐项核算一致：worker／budget／cycle fixture 与固定 r3 相同，测试为较早的 217,892B／`1b5121b846c286fa81b3bd109597b29de3ac275715b42fd61d62c5af61ebe211`。六项分别覆盖 pending 根 spawn／活动 confirm 的全 loop 取消、最后 owner deadline，以及原 operation 的 spawn／helper／loop 三取消边界。它们配合上述独立实证与实际 await／finally 顺序关闭 R4 源码 finding；不能据此声称运行了后来新增的“根通知发生时 S 已退出且 stopped frame 已读”的显式断言。

当前 r3 测试第 1356–1409 行确实加入该顺序断言，观察的是原 `processes.notify_identity`，没有替代通知或把清理成功伪造为输入值。其完整运行归属仍需准确输入身份。现有 `source-r11.xml`／stdout 终态为 **11 passed／186.65 秒**（JUnit 186.639），SHA256 `3b29634df520cc166f907f0eead3657f4af2ecb9e83a0ec4edb7258da70f4e51`，包括两项全 loop、八项固定 history及 launch。该次缺少预运行完整输入 snapshot／manifest；运行后当前文件与 r3 一致，不能倒推整个运行期间逐字同一。因此保留 r11 终态，尚不把新顺序断言或 fixture 修正的通过归给固定 r3。新非 editable r2 运行将承担这项归属验证。

### 服务替身、原安装失败及验收边界

现有 S-H 与 owner 是独立进程，旧 submission fixture 的 import 时全量 `record` 不能继续充当更新权威。固定 r3 把原 `save` 改为同一 lock 内重读当前记录、追加单次 call／counter／明确字段，再原子 replace；所有原同模块写入及 cancellation／release 两个实际消费者均迁移为增量更新。读者至多看见完整旧值／新值，不会因另一个客户端的旧快照把 start／request 覆盖回去。该职责仍留在服务替身原 owner，未加产品账本或批准权威。新增 lock／pending 是测试运行原件，不能把它们说成产品恢复协议。没有发现需要再拆模块、增加通用事件层或删除身份检查的维护性理由。

已直接核旧 `installed-r1.xml`：**70 项中 62 passed、8 failed／945.11 秒**（JUnit 945.082），SHA256 `2d35fd79957f36d6ed91da748171e746242860a36ab8259812516989193ec0c9`。七项 history 拒绝 case 均在末尾读取未产生的 service 文件时 FileNotFoundError，之前的既有 intent／只观察断言已执行；第八项 launch 没到真实 marker。固定 r3 对前者把未产生服务记录解释为 start 0，对后者修正上述替身旧记录覆盖。旧失败仍属于原安装 r1；没有把它们改记通过，也没有仅因 15 秒数字就把 launch 失败再定为 S1。

本轮 11 份 Python 源码／fixture／测试均 ast.parse 通过。R1／R2／S1／R5 的既有关闭保持；r3 追加的取消分支未放宽最后 window／owner gate、existing-only、只对账恢复、原六阶段／批准及预算身份。新增 spawn／confirm／operation-loop 反例保护各自真实资源过渡，不是重复 argv 或 helper 字段测试。283 reference 与原 25 项有序 GATE_SOURCES 的既有冻结约束不变；r3 没有更改其 owner 或来源。

整片仍须另核准确新 core／SDK 非 editable 包身份、适用 schema1／schema2 安装回归（含新顺序断言与服务替身修正）、SDK-free 原观察、修后自身原模板及全部已知 owner／后代收尾。原计划中未由现有序列明确覆盖的并发唯一 offer、累计窗口／stdin 取消／窗口尽后晚到句柄、父崩溃后的原预算观察和只对账 NOT_FOUND 仍应逐项给出实际覆盖，不能由本次惰性 S-H 概括关闭。主控新安装 r2 在途，本节未验其产物或结果。后继服务／配额、总 Workflow／下一轮和远端发布／CI仍分别依原门禁处理。

## r4 最终本地门禁复核：2026-11-15

本节之前全文保持原样：35,266B、SHA256 `cd76f799449707b4d6e608d53c0653c06304e0e4bac24d1d60ef8bb167462a2a`。同一独立 reviewer 继续核准确安装件、两轮固定输入、SDK-free 原观察、自身模板与实际原件／收尾；未重跑模型或既有 suite，未修改产品、测试、CI、其他工作树或 Git 状态，只追加本报告及自己的 ignored 只读核查记录。

**最终本地需求符合性 approve；可维护性 approve；开放源码／测试 finding 0／0。R1、R2、S1、R4、R5 全部关闭。** 此结论对应下面固定的 c1b1 内部单候选产品与本地证据；固定提交、普通发布及准确 CI 仍是后续门禁。

### 最终输入与包身份

基线仍为 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。`product-review-r4-scope.json`／`product-review-r4-snapshot/` 含 **25 份完整 tracked／untracked 变更文件**，五份产品、六份测试／fixture及十四份文档。逐项重算 bytes／SHA256 全部匹配；patch 为 226,866B、SHA256 `2c6ec2deed1925a9a739ea2b26cc993d5cde8650462a2dcb0043dfac54ab8d09`。五产品与上节固定 r3／新安装 r2 逐字相同，没有再修改已关闭 finding 的源码。

新 core／SDK 均来自同一非 editable wheel，SHA256 `565aefd026e01f83470af5e49a74d1743c3919779a4b4a217fc2dc56755eb29b`。Reviewer 独立读取 ZIP、两份安装目录、manifest、direct_url 和 RECORD，核 **652 个产品文件 source＝wheel＝core site＝SDK site**；wheel RECORD 660 行有效，两安装各 665 行、其中 664 行有 hash，全部逐项验证。core 无 Temporal SDK，SDK 环境为 1.34.0；两环境依赖检查原件均 exit 0。相对原基线只变五个既有产品文件，无产品新增／删除；283 个 reference 文件逐字保持，原 25 项 GATE_SOURCES 的内容及顺序保持，原 reaper／依赖／CI无变更。

安装 r2 前冻结的 178 份 tests／examples 输入逐一匹配 `installed-tests-final-r2-inputs.json`，该 manifest SHA256 为 `3ceb9ddbac5c5c1733adc768f8849bb2e2798d4d8b3ec07d85b73f7a28d15c67`。随后仅扩展两个既有测试文件，再冻结完整 178 项为 `installed-tests-final-r3-inputs.json`，SHA256 `2b6b1129de269914026c647da154ed65299a956a7b59661797b53e036c4eaed6`；无输入增删，其余 176 项逐字相同。新增候选的 test 为 221,273B／`f825580c32c527006b73ad61fad99fded8289761d8eac0ca29b87c9118cbb9db`，cycle fixture 为 10,237B／`cbff70790375491df77572e792df77a2261cd242066a8b3075778ccd96bb0a46`。最终 r4 的六份测试／fixture与该冻结输入全部吻合，不把后来测试倒归给原 r2 运行。

完整 scope 同时保留了 PLAN 归档／恢复入口、WA 审计、前片 CI 调查及未实施的 c1b2a 服务草案。这些文档只认证准确输入与状态边界；本次不替代 WA／服务方案的独立审查，也不批准服务或任意 Hook／总 Workflow 能力。十四份 Markdown 的 446 个本地链接目标均存在，十一份 Python 完整输入 ast.parse 通过。记录同步不递归引入产品审查。

### 两轮安装终态与原验收表

直接读取命令、stdout、stderr、JUnit 及对应冻结输入：

- **安装 r2：76 passed、无 failure／error／skip，985.95 秒**（JUnit 985.931）。原先预估 75 项，实际参数展开多含最终 owner-deadline case；旧安装 r1 的 70 个 case 名全部保留，另有两项 pending-root 全 loop、三项原 operation 取消及一项最终 deadline。JUnit 为 17,627B／SHA256 `a3bf566750d38b8cddd4606f966ebdd1b0de0dbf80f7ec4075d91d1354c02de8`，stderr 为空。覆盖原 schema1 手工 start／恢复、schema2 内部 caller／严格 gate／独立 stop、原 offline training 及架构边界。新 S-H 先于根通知的显式断言及服务替身原子更新已有这轮准确身份，关闭上节的运行归属待核项。
- **精准安装 r3：7 passed、无 failure／error／skip，153.70 秒**（JUnit 153.696），继续使用同一 r2 SDK 产品。JUnit 为 1,932B／SHA256 `5a112678b18ef884dd91ffdfdc917ab0feb3b54f130090f8e0784d64753ca6b1`，stderr 为空。只执行新增的实质序列及原初始化锁接缝，没有重跑 76 项总回归。

|原待核结果|准确复核与实际原件|处置|
|---|---|---|
|唯一 offer 并发、跨短 H／正常 loop 重启|原正向例改为同时运行两个真实 Candidate；只有一个 spawning，原 H 输出一个 `new_offer`、另一个 `observed`。完整 confirm／dispatch与获胜 prepare 共用同一 bootstrap；正常 loop 退出后同一原 owner 仍活，再次调用只观察同一 run，service starts 始终 1。|精准 r3 通过，原 scope 内闭合。|
|完整输入发送后、完整确认回复失联时的交接前取消|transfer case 先完成真实公开 pipe 发送，再在尚未进入 confirm 时取消；lost-confirm 在原 S 已收原 H 后阻塞读回复。已直接读到该 H 的真实 `owner_confirmed`，调用者未完成 handoff；两例均清理未交接根、保留 intent、无 attempt／SDK start，后续仅 observed。|精准 r3 通过；不把它说成部分 pipe 写入故障的独立实测。|
|原窗口耗尽后的晚到 Popen|沿原 pending 创建接缝分别取消与等待原 30 秒窗口自然结束；deadline case 没有改 clock／deadline 值。任务在真实 Future 未完成时继续持有责任，之后取得实际根并关闭未发送的 stdin、真实退出等待，未 handoff。原代码在 pending 分支结束，不进入 transfer／dispatch。|精准 r3 两项通过；保留 OS 创建无限阻塞无法保证有界退出的原支持限制。|
|已有 attempt 的只对账 NOT_FOUND|原 sdk-start 取消例中保持损坏 owner，先由实际 `reconcile-candidate` H 得 unknown／`not_found`，无 receipt、原 attempt bytes不变、starts 不增加；随后 accepted 对账补同一原 run 的 receipt，owner 独立 unknown。已直接核两份原 H stdout及最终 starts＝1。|精准 r3 通过；没有借新观察窗口恢复执行权。|
|慢初始化／完整 owner 交接|原 `test_owner_observers_share_the_initialization_read_lock` 真实子进程持原 owner／initializing 锁，从初始化排他态的 False 转为共享观察态的 True；confirm 继续调用该原算法并核完整 owner／context。|精准 r3 附跑通过，未搭另一 owner 框架。|

其余原 76 项继续支持完整确认后的 lookup／attempt-sync／SDK 回复等待取消保留根、重复／丢 prepare 回复不再授 offer、最终 window／owner／慢 owner 读取漂移拒绝、原 b2b veto／通知／drain及实际执行链观察。新序列扩展复用既有 fixture／原 owner和 service double，保护不同的真实资源过渡；未加通用调度、第二账本或无实际消费者的抽象，没有发现新的职责／耦合／冗余测试 finding。

原安装 r1 的 62 passed／8 failed、原 r11 缺预运行完整输入的 11 passed及先前各红例仍按原候选保留。两轮新通过没有覆盖写回旧失败，也没有倒推 r11 的输入同一性。SDK double 使用真实 SDK 编码／history／memo，但不是实际 Temporal 服务或训练。

### SDK-free 观察与自身原模板

已读 `core-inspect-r2.py`／`.json` 和实际 operation request、原 H stdout：**core r2 真实原异步 S-H inspect 通过，1.220 秒**，S returncode 0、stopped 可见、诊断为空。父 loop 期间禁用 State／SQLite／业务读取；原脚本在外部前后比较八份完整周期原件及 DB rows，并断言原 payload／window 不变。Reviewer 逐字段核 H 的实际输出与记录结果一致，原周期目录仍为八文件。该证据是 SDK-free 本地冷观察，不是 SDK 查询／Workflow／执行；结果原件 3,978B／SHA256 `fbe1e6123b1e4fbdbdacc22c49032b09b2ea3feae4e1cae320f322256e8de06c`。

修后自身原 `ergora-structure-review@1.0.0` 以用户授权的 Codex fallback 真实完成 **56.323 秒、approve**。Reviewer 独立核 21 份完整文件共 584,346B 的 snapshot／摘要，完整 diff、task 及三份祖先资源均包含在实际 stdin；input prompt、运行 input prompt和原 stdin 逐字相同，共 713,439B，SHA256 `7ef3ba1ccc90f32bebe0de00065893548b6a04102ebb854bdad8004a74297647`。输入 digest为 `5e27cff0f0bf66d878b5f676a8e7ec99cb9644985a47a4d8672da4ac4906cdd8`，原 result 与复制件逐字相同，SHA256 `e44a6bfc1b3b3b2622d45cc28c5b7ffa865b1bd3ad603f42fa9c2455d23f4d02`。

模型明确只审完整供稿，未运行测试或认证私有原件；供稿中的回归当时仍在途。该次十一份 runtime 输入匹配原固定 r3，后加的两测试扩展由本轮独立复核与精准 r3 认证，不声称模型读过后来内容。没有异后端成功、真实服务、训练／GPU 质量或外部 CI 通过的主张。

### 实际收尾、限制与最终范围

已读 `final-verify-r4.py`／`final-verification-r4.json`，后者为 369,907B／SHA256 `0a48ba206e99dea84c0cf415b27c5d75f0988965a8813912b36a3a834a89a403`。记录再次核 652 产品与 178 当前冻结输入；十四个本片 source／installed 工作根共解析 7,616 份 JSON，提取 **267 个不同完整引用身份**，记录活匹配 0、unknown 0；九份超过 2MB 的文件未读，明确不是全部 OS spawn 清单。

Reviewer 另逐一认证这 267 项在 1,697 份不同来源原件中确实存在，并独立重读当前 `/proc`：266 项已无 proc，唯一仍有 proc 的记录为历史夹具的固定 pid 1／start_ticks 0／零 boot，与当前 PID 1 不匹配；无实际活匹配或读取 unknown，没有向它发信号。Reviewer 自己从安装 r2／r3 工作区另提取的 81／15 项均包含在该总清单内，先前独立惰性反例的 S／H／后代也已确认退出。核查只观察身份，未伪称非父进程做过 wait；实际 Popen 的 wait 与原 S-H stopped／退出顺序由相应用例和原 reaper 原件支持。

本片 b1.2 的实测结论是实际预算根跨短 S-H 及正常 loop 关闭／重启仍活、同一原 clock继续、最后真实收尾。**实际预算根在父 SIGKILL 后的产品序列仍未实测**；先前公开进程研究只用惰性根，不能扩大为该能力验收。只观察恢复、不补 Popen／SDK start的源码合同保持。原 OS 创建永久阻塞的退出限制同样保持，未引入新的 process-host。

据此，c1b1 本地产品与证据门禁闭合；固定提交／发布及准确 CI 另验。前片 `1b8c2ed` 自己的 group5 失败及隔离修复不改标为本片 CI，BR仍在隔离工作树，WA／服务草案仍按各自审查处理。c1b2 真实服务／normal-stop 配额、c1c 总 Workflow、c1d 完整接受／后继轮和公开自动入口均未由本报告交付；原六阶段、候选绑定证据、批准身份、唯一 reaper和 kernel 专家 v3保持。

## 固定提交身份补核：2026-11-16

仅核固定本地提交 `d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，父为原基线 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。26 份变更包含原 r4 的全部 25 份及一份后继服务设计审计；后者明确不是 c1b1 产品验收或服务实施，不借本报告批准。

逐一读取固定提交对象：十一份 Python blob 与原 r4 完整 snapshot／摘要相同，五产品也与原 r2 包记录相同；没有使用随后变化的 HEAD 代替本片源码。提交内报告为完整 46,090B、SHA256 `e9f6438327eb2e158060a7b11a23ad0f12eb541691f9b8bbe15a0e52c689551d`，与 reviewer 原件逐字相同，本次仅在该完整前缀后追加。提交中的 PLAN、交付及验收表准确分列 76 项安装回归与 7 项精准补验、两轮各 178 输入及旧失败／r11 身份限制，保留实际预算根父 SIGKILL 未验、OS 创建可能无限阻塞及后继服务／Workflow／训练未交付的边界。

固定提交需求／维护性结论保持 approve／approve，开放 0／0。本次只做提交身份与记录收尾，没有重跑 suite／模型或递归审查状态记账；后续 BR 资源与 CI fixture 的联合候选及远端门禁另验。
