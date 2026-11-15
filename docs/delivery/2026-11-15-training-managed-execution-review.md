# B3.3c2 受管执行独立产品审查

日期：2026-11-15。审查者为 fresh-context 独立 reviewer `training_managed_execution_product_audit`。先读原始范围、项目规则与固定合同，再沿实际入口检查；未继承作者、自身模板或前置片的通过结论。使用 maintainable-project-delivery 的独立审查规则和 ergora-codebase-quality 的 module-design／test-seams／repository-style。

本报告按候选追加历史；下文 r1／r3／r5／r6 的“当前／待”只指各节当时。最终本地及固定 `ac86043` 普通发布在原核实范围内保持需求／维护性两轴 approve、开放 0／0，R1–R5 关闭；该候选自己的 Portability run `43684533043`／attempt 1 已核到终态失败：七 job 成功、Windows 因六个测试 setup error 失败，30 必要步骤中 29 成功／1 失败。原失败保持，CI 接续门禁未闭合。

## 固定 r1 与当前结论

产品基线为 `75285e3271bb93271eaea050ca7812cb0cd98b5a`，分支 `refactor/architecture-foundations`。本轮只审 `.ergora/checks/training-managed-execution/product-source-r1/` 的 19 份固定文件，包含两份新源码全文；`scope.json` SHA256 为 `5d105ed110d5d05b345f300beb1cf1b00d515a923cedcebb68a50241e165f30e`，`changes.diff` SHA256 为 `f8271cebb4db5b3609f9244e8b2f289cda22d7521c04acb39df32a5208046366`。19 件长度／SHA 均与清单相同，12 份 Python AST 可解析；另读的 19 份约束／相邻 owner／原协议文件均等于基线。以下行号均指固定 r1，不以随后变化的工作树替代它。

|审查轴|固定 r1 结论|开放项|
|---|---|---|
|需求／行为正确性|request-changes|R1、R2；最终安装、真实 CPU 生命周期及失败窗口证据仍待|
|结构／可维护性|request-changes|R1 的工作截止／证明收集职责、R2 的停止信号顺序；其余已审路径暂未发现新的结构缺陷|

作者已接受 R1、R2，拟分别保留 execute 在 total 内取得的停止观察、在 fence 启动前实际通知现有 peer。接受和拟修正不等于已关闭；须以新的固定候选、相应真实接缝回归及最终安装复核关闭。本报告不提前认证 c2 完成或发布。

## R1 · P2：compute 截止后完成的停止证明被 finish 丢弃

位置：[reference_training_budget.py](../../src/ergora/reference_training_budget.py) 固定 r1 第 204–206 行、82–85 行；[reference_training_execution.py](../../src/ergora/reference_training_execution.py) 第 146–147、168–169 行。

execute 的原业务必须在 compute 截止停止；同一个 S 随后在剩余 cleanup 中完成 safe-reap、匹配 stopped 帧和持久 stopped。当前 `finish()` 用 `not self.expired()` 同时决定是否接收第二帧，而 execute 的 `expired()` 始终采用 compute。因此，即使真实停止证明已在 total 内完整同步，父 owner 仍把完整结果改为 unknown；drive 只能取得 `execution=None`，预算 final 也丢失已经取得的 `executor_stop_confirmed=True`。离线 reader 可以另作恢复，但不能说明这次父 owner 已正确合并观察。

便宜探针执行固定源码 AST 中原 `expired/request_stop/finish`，给定 compute=-0.1 秒、total=+5 秒、退出码 0、完整两帧及第二帧的停止确认 true：execute 返回 unknown；采用 total 的同一收集路径保留该观察。探针不运行 native 或实际进程，证明的是精确方法的结果传播问题。

最小修正：只让 execute 的**完成结果收集**在 total 内保留原 reap／持久 stop 观察；execute 的启动、业务 stop predicate 及最后 gate 继续采用 compute，admission 的 grant 和 monitor 不延期。回归应经过原 phase 生命周期，在 compute 截止后、total 尚余时完成实际 reap／停止发布，再核父 final；不能只改变一个模拟 result 的预期。原件：`.ergora/checks/training-managed-execution/product-audit/execute-proof-allowance-r1.json`。

## R2 · P2：fence.start 发生在执行 S 真正收到 TERM 之前

位置：[reference_training_execution.py](../../src/ergora/reference_training_execution.py) 固定 r1 第 116–132 行；[reference_training_budget.py](../../src/ergora/reference_training_budget.py) 第 149–160 行。

`stop_work()` 仅调用 `request_stop()` 置内存 flag，真正的 `process.terminate()` 要等下一次 `poll()`。drive 在该 poll 之前先调用 `start('fence')`。所以 catchable cancel 到达时，fence 的序列化／Popen 启动若停住，原 execute S 尚未得到本地停止请求；它只能靠自己的原 clock 到 compute 截止停止。原计划要求先及时送出本地停止请求，再进入可能等待的控制启动，不能让提前取消等待 fence 启动。

便宜顺序探针运行固定源码中的原 `drive/request_stop`，保留无副作用的 phase／信号记录接缝：已有 execute 后设置取消，观察到 `start(fence, execute_signal_delivered=false)`，随后才有 monitor／execute 的 TERM。它没有实际阻塞 Popen 或运行业务，不声称已做真实取消故障验收。

最小修正：对已有业务／admission／monitor peer 置停止请求后，立即逐个非阻塞 poll 或等价地实际送 TERM，再启动 fence；不等待 peer reap 或结果。回归应让 fence 的启动接缝停住，同时确认已有执行子树已被及时通知并由原 reaper 收尾。原件：`.ergora/checks/training-managed-execution/product-audit/cancel-before-fence-order-r1.json`。

## 已沿实际接线核对的需求与结构

- **完整授权与最后 gate。** 显式 CLI 经 `training.execute → reference.training_execution → execution_main → Execution`；不复用带 DB reservation 的提交 prepare，不增加 start 客户端。native callback 位于原 b delta 的 executor.lock 内、started／Git／业务 try 之前。它反算原 intent／attempt／receipt／完整 native request，核 C 的完整五字段 SHA 与出生 owner、authorization／原 cycle bytes／原 policy／ready、完整 clock 与原 cleanup reserve、固定 gate 源码及原 279 来源、解释器／core 路径和实际父子进程身份。attempt／ack 同步之后再次核 owner／compute／fence，拒绝不落业务 result。未发现以任意单独 clock 或当前同路径 runner 替换 C 的接线。
- **一次 launch 与旧能力。** admission 持局部 execution 锁先 lstat 确认 launch 不存在，发布／同步后仅返回一次内存 grant；已有、部分、丢帧或 Popen 失败均没有重新授予路径。drive 只消费一次 admission 结果；native 又拒绝已有 attempt／ack／stopped。旧 schema1、schema2 null 能力、普通 start／queue／status／resume 不创建执行请求，也没有为旧 owner 回填能力或重启它的分支。
- **所有权与停止顺序。** `BudgetedStart` 继续持出生、锁、signal、final；`Execution` 隐藏单一应用用例的请求／准入／并行监管；协议模块由应用 writer／离线 reader、执行 S、native callback 实际跨解释器消费。未增加第二 scheduler、实验账本、reaper、比较器、backend 分派或通用插件框架。父循环只传内存 payload、非阻塞 pipe／selector、poll／signal 及原 clock／proc 观察；业务文件、锁、RPC、fsync 在各 S 子树。R2 是这里的具体顺序缺口。
- **reap、完成与持久性。** execute S 继续调用原 `processes.run(supervised=True)`，实际收完子树后先发完整 stopped 帧，再由同 S 直接读写／同步记录；该分支没有后续 spawn。managed namespace 下 completion 不凭 native result 单独完成；fence 也复用这一条件。离线 reader 先读历史，不先 validate/import 所选安装；已有 stopped 只有在同步原链文件及必要目录、重读相同 bytes 后才确认 durable，失败保持 unknown，不创建缺记录、不返回执行权。R1 是父结果收集的具体缺口。
- **取消。** 原取消 intent 与 receipt/run 归属保持；新增通知复用 `processes.notify_identity`，pidfd 绑定后重核 boot／start_ticks，CPython 缺 wrapper 时仅用真实 libc pidfd 接口，失败保留 unknown，没有宽泛 kill。远端 signal 仍沿原 attempt/history，不新增或重发客户端。
- **guard 与测试接缝。** 严格字段、完整内容／bytes 摘要、来源检查、原锁、无覆盖记录和原件同步分别保护跨进程／持久身份、单次权限、资源和并发的可达风险。未发现应为了减少 guard 而删去的具体保护；也未发现需要再建实现族接口的真实消费者。源文件长度本身不构成拆分理由。最终覆盖应复用原 submission／phase／native／process fixture，不用 AST 探针替代真实锁、后代回收或失败窗口。

## 已验事实、候选身份与未验范围

本 reviewer 已直接核固定 19 件、相邻基线身份、原 283 reference 文件摘要无变化，完成上述两个便宜 AST 接缝探针。首次 R1 探针因 AST 人工装配缺少行号在方法执行前失败，随后用 `fix_missing_locations` 修复探针装配；未修改产品。身份原件为 `.ergora/checks/training-managed-execution/product-audit/initial-scope-verification-r1.json`。

作者报告的首轮 AST／架构 16 项、四个原接口回归、首包 core／SDK 652 三方逐字与依赖检查，均按各自原候选保留。本轮直接读取首包清单发现它与固定 source-r1 在 `processes.py`、`reference_training_cancellation.py`、`training_execution_protocol.py` 三件不同：首包 wheel SHA256 为 `158e9350107d192af34f99a4b384605af049a505ac986c171168df9b8ceb1872`。这些差异属于已报告的 owner 观察锁／pidfd 修正，不能把首包的三方一致转授为本固定 r1 安装一致。记录在 `.ergora/checks/training-managed-execution/product-audit/initial-evidence-identity-r1.json`。

原 `native-journey-r1.json` 明确为 exit 1／62.816 秒；已知 monitor 观察锁碰撞、final 等待超时及 cleanup 的 CPython wrapper 缺口保持失败身份。其 recovery 原件显示原 owner 已退出、final 已存在、服务 socket 消失、三端口已释放。仅这些记录和作者原旅程说明，不足以认证新的完整 CPU 旅程；本 reviewer 未重新运行它，也没有把 recovery 改记为原旅程成功。

仍待新的固定修正源码与测试、匹配的新 core／SDK 非 editable 安装与原 283、受影响原 suite、同一候选的真实 Temporal／native 原 Git／runner／setsid 后代／archive／track 全周期及精确收尾；另须核 launch／attempt／ack 中断、原锁竞争、context／source／clock／run 漂移、控制存储阻塞与执行 reap、result 早于 reap、stop link 可见而目录同步未完成的真实窗口。自身原模板、新独立最终本地复核、普通发布／固定 Ref 和自己的 CI 另行闭合。

本轮没有安装、服务、训练、产品或测试修改、commit／push 或外部写入；仅写本报告和授权 ignored 审计原件，无后台进程。没有进行性能测量，也不据静态并行结构宣称停止延迟或吞吐收益。CPU 控制与生命周期证据不认证真实训练、GPU、模型／数据质量或性能收益；kernel 专家继续留在 v3 提案路径，原实验／门禁／批准和采用权保持。

## 固定 r3 中途复核：R1、R2 关闭，最终验收仍待

同一 reviewer 接续复核；本节保留此前 r1 的问题和失败原件，**不是最终产品验收或发布结论**。新固定范围为 `.ergora/checks/training-managed-execution/product-source-r3/` 的 23 件，`scope.json` SHA256 为 `68a056be0ac2e2c8d9d91ab76c74155b62817e9c7fe1817e1efcb69477e8de82`，`changes.diff` 为 `5b6852411cb45574296a9d846297b590c17f4164d192367f9ea4b7cc89f9b49e`。23 件均逐字符合清单，16 份 Python AST 可解析；相对已审 r1，产品只改原 budget 与 execution 两处，其余产品保持。

|审查轴|本次中途复核|开放范围|
|---|---|---|
|需求／行为正确性|R1、R2 在固定 r3 修正范围关闭；已核新 CPU／取消原件，暂未发现新的实质产品缺陷|中断窗口、最终安装回归／用户文档／自身模板与最终候选仍待，不能标全片完成|
|结构／可维护性|两项职责／顺序缺口关闭；本次增量未引入新的结构 finding|最终完整差异及正式交付门禁仍须续核|

**R1 关闭。** `finish()` 仅对 execute 的结果接收传 `total=True`；其 start、poll、S stop predicate、native 最后 gate 继续使用 compute，admission／monitor 没有取得额外执行窗口。新的 `test_execute_phase_keeps_stop_proof_within_cleanup_without_granting_more_work` 经过原父管道／TERM 生命周期：以叶 reporter 替代 native 工作，在 compute 后、total 内返回完整停止结果，父端保留确认，同时拒绝再启动 execute／admission。其观察边界是结果传播和启动准入，不是 native reap 或持久性。与下述独立的原 native 完整 stop 链证据合看，修正接在真正丢失结果的 owner，不需复制停止算法或延长原工作预算。

**R2 关闭。** `stop_work()` 先对现有工作 peer 全部置停止请求，再逐个做原非阻塞 poll，最后才进入 fence.start；原 `_BudgetPhase.poll` 的 TERM 发送因此先于可能等待的控制启动。`test_managed_cancel_delivers_peer_stops_before_launching_fence` 保留原 drive，用可控 phase 直接检查该顺序。它不模拟实际 fence Popen 卡死；下述真实 registry 持锁取消则经过原 TERM／native／setsid 后代回收，补充正常控制阻塞时的实际行为。源码修正未等待 peer finish／reap，也未把业务 I/O 放回父 owner。

已直接读取这两项源码接缝、固定测试正文和 `source-review-fixes-r3.xml`：两项 passed／0 failure／0 error，XML 为 1.510 秒；作者外层命令记 1.54 秒。未重跑这两个已通过的检查。正在开发的 no-launch 用例在 `source-no-launch-r3.xml` 中是 `prepared_training_installation` fixture 缺失的 setup error，保持其失败身份，不计作单次 launch 或中断矩阵通过。

### r3 安装与实际解释器身份

独立从固定 r3 及基线未改文件、wheel 到 core／SDK 的 site-packages 逐份读 bytes：两安装各 652 件完全一致，无遗漏／差异。wheel SHA256 为 `064521159c0e1d30360b95b1fa712d89d5a2fe0fb8a2de509336f93f835366ac`；两份 direct_url 均为该 wheel，未见 editable 标志。独立 `-I -B` 小探针实际定位 core／SDK 的 `ergora` 至各自 site-packages；core 缺 Temporal，SDK 可用。原 dependency check 两次 exit 0，包内 reference 检查各 283 PASS，且这 283 的 bytes 已包含于上述逐份核验。

所选 native 解释器的 sys.prefix 为其自己的 `.venv`，找不到安装的 ergora；native 自带 Temporal。另逐字核当前 279 份派生 native 源码和完整 descriptor 与固定包相同。该检查没有在 native 安装应用依赖，也没有借应用 venv 替代 native 环境。r3 私有构建 driver 的首次 setup 失败及修正输入保留，记录为构建前解释器路径错误，未被改记为当时已经构建／安装成功。

### 新 CPU 旅程及持锁取消的原件复核

直接读取 `native-journey-r2.py/json`、`native-cancel-r3.py/json`，两脚本 SHA 均与执行元数据相同；命令分别使用 r3 SDK Python `-I -B`，外层 exit 0／25.9278 秒与 exit 0／21.2818 秒。各自八次 CLI 均 exit 0，stdout／stderr、命令、原 phase 输入／输出、原 request／授权／原链及 final 均保留。共建立 155 份原件长度／SHA 索引，未重跑服务或旅程。

对两个不同原实验，独立重算全部 request→launch→attempt→ack→stopped 的完整引用、原 intent／attempt／receipt／native request bytes 与语义 SHA、owner 完整 SHA、实际保存的 C 和 owner.context_sha、authorization 去 sha 字段后的摘要、原 cycle bytes／policy／project／ready、launch.clock_sha 与出生 gate_sources；均与固定 r3／原路径匹配。保存的离线观察及 final.execution 与当前原件一致，没有凭 summary 的布尔字段代替身份核验。两个原 owner／phase／executor／已捕获 descendant 身份本次均已不再存活；原 cleanup 记录分别确认三端口释放且 errors 为空，本 reviewer 未再启动服务或重新占用端口。

- **CPU 生命周期例。** 原 job 确有 Git mirror 和两个 worktree；以 `/usr/bin/git cat-file` 只读核原 baseline／candidate 完整 OID 均为 commit。原 gate 仍是 false，archive 日志明确因 `check:harness_integrity` 缺 PASS 拒绝，native state 为 SUCCEEDED 只说明原流程返回；没有将该状态写成质量成功。实际 native stdout 与结果引用同一个 MLflow run。另以只读、immutable SQLite 连接核真实 MLflow 数据库：该 run 存在、状态 FAILED、`gate_passed=0.0`，与负 gate 一致。原 CPU 两臂均为 690880；final 为 completed，admission／execute／monitor 三 phase 都有原 stopped 观察，executor_stop_confirmed 为 true，未发生 overrun。
- **持 registry 锁取消例。** 脚本用原 file_lock 包住 execute、cancel、执行 stop 和 held 原件保存，之后才离开锁作用域；其调用原 native registry 入口。保存的 held 观察已经有同一条完整持久 stopped，并表明 native executor／setsid child 已停、native result 与 budget final 尚不存在，fence helper 已进入。释放后原 final 为 fenced、五 phase 均已回收，execute process 为 cancelled／returncode -9，停止确认 true、无 overrun；控制取消回执另列。文件系统 mtime 只有整秒精度，held 与 fence 的时间相同，本次没有用文件时间臆造二者先后，顺序依据固定脚本的锁作用域和保存的各阶段原件。

CPU 例及提前取消例都在 compute 仍有余量时结束；它们不单独证明 compute 截止的完整 native 场景。真实 stop link 已可见而目录 fsync 卡住、结果先于实际 reap、launch／hook／attempt／ack 中断、原锁竞争及完整 context／source／clock／run 漂移等剩余窗口，仍按原验收计划开放。新 no-launch 测试、最终受影响安装 suite、用户文档、自身原模板、最终完整候选审查及普通发布／自己的 CI 未被本节提前记为通过。

本次新增的独立原件均在授权 ignored 目录：`interim-scope-install-r3.json`、`interim-runtime-origin-r3.json`、`interim-native-evidence-r3.json`、`interim-originals-index-r3.json`。本轮仅做静态、逐字身份、只读 Git／SQLite／proc 和三个短解释器定位检查；没有产品／测试修改、安装、服务、训练、长 pytest、commit／push 或外部写入。新结果继续只认证所述合成 CPU 控制与生命周期，不认证真实训练／GPU／算法质量或性能收益。

## 自身 r4 模板与固定 r3 的新增独立发现

本节继续使用上节固定 r3 产品；R1、R2 的既有关闭保持。整片最终需求／维护性结论仍待新固定候选与其安装／实际验收，**没有批准当前工作树或提前关闭 R3、R4**。

已逐字核自身原结构模板的 30 份完整文件／727,803B、实际三项祖先资源、完整 task／diff 和 857,508B prompt，均完整进入同一次原 stdin；input digest 为 `05a421c9617cd094c3ca735626fb6f2afa0d06233cc51e9d7cffe9474444b0dd`，原 result SHA256 为 `a996a0713dd3091111c733842025a7630c355f96ad1491dd55c8c46ccfdd0813`。原 run `2e55dabc0384437ab4649096fd8e80b6` 为 Codex 授权回退、returncode 0／88.522 秒，需求 request-changes、维护性 approve。该模板只审所供文本，不认证私有运行原件、供应方上下文完整性、异后端或 CI。本 reviewer 没有继承它的判断，而是沿固定方法和实际锁独立确认下列两条路径。

### R3 · P2：可见请求仍被 writer 持锁时，唯一 admission 直接失败

位置为固定 r3 `reference_training_execution.py` 第 69–72、78–104、139–160 行，以及原 `state.file_lock` 第 115–145 行。request 在局部 `execution.lock` 内发布后，还持同一锁执行完整 `current()`；相同确认也能处于该窗口。admission 只等到 request 可见便离开等待循环，随后非阻塞拿同一锁，没有捕获或重试 `BlockingIOError`。唯一 admission helper 因此返回 unknown 后被 drive 删除，没有 consumed launch，也不会重新 admission；合法请求可一直等到原预算耗尽。

独立短探针直接执行固定 r3 原 `admit` AST 与实际 Linux `file_lock`，由另一个打开的 fd 保持原锁。它在一次 `require_active/check` 后抛出 errno 11，未创建 launch。叶 check 为受控替身，故它只证明锁争用及调用者处理，不认证真实授权或 native 执行。另直接读取作者冻结的新测试与旧 r3 非 editable 安装的原红：原 writer 在 publish 后完整 current 窗口实际持锁，admission 的原锁确实碰撞；释放 writer 后十秒内仍未出现 execute launch。测试以既有 SDK 服务替身保留真实 owner／helper／文件锁，execute 仅标记准入而不运行业务。

最小修正是把局部锁争用留在原 compute 有界的 admission 循环，每次重做完整 owner／source／request 检查，拿锁后再核当前身份；已有或部分 launch 仍永久消耗机会，不能把相等重读变为新 grant。作者的新源码三项精准回归已报告通过，但本节尚未取得它的固定最终范围／新安装身份，R3 保持待修复复核。

### R4 · P2：monitor 的非 completed 结果被丢弃，活执行继续到 compute 到期

固定 r3 drive 第 139–160 行只处理 monitor 的 `status == completed`，其他结果记录后直接删除该 phase。原 monitor 在 completion 未完成时调用 `require_active()`，项目 revision 漂移会使其退出为 unknown；而已进入 native body 的执行 S 后续只核原 clock、本地取消与原 owner 进程，父 drive 的 remaining 也不读当前项目。因此原 monitor 已发现失效时，活执行仍持续到原 compute 截止。这回退了原串行 owner 在 monitor 非完成后进入 fence／cleanup 的行为。

独立执行固定原 drive AST，以受控 phase 让 admission 已授予、execute 活跃、monitor 返回 unknown；事件中 monitor 已 finish，随后直到可控 compute 耗尽才实际送 execute stop 并启动 fence。作者旧 r3 安装的原红在同一现有 phase 接缝也记录了该顺序，取消分支原控制项通过。此探针和该项回归都没有实际修改项目 revision，不替代活 native runner 的真实漂移验收。

最小修正是在 monitor 非 completed 后立即复用原 stop／poll／fence 路径，保留原 monitor unknown 观察；不增加调度器、owner 或新的信号客户端。作者报告的新源码已共用这一局部路径并通过精准接缝，但真实项目漂移及新固定候选复核仍待，R4 未关闭。

两项旧安装原红为 `review-bug-repro-r5.xml/stdout`：2 failed／1 passed，XML 31.250 秒；新源码 `source-review-fixes-r5.xml/stdout` 为 3 passed／21.236 秒，按各自范围保存，未将源码绿转授最终安装。独立探针为 `product-audit/new-findings-r3-probe.py/json`；自身输入身份为 `self-review-input-r4.py/json`。身份验证器初次误取 native stdout 不存在的 exit_code 字段，已改用实际 returncode 并完整重核；产品与原件未改变。

## 旧 r3 六个实际故障窗口的原件复核

本 reviewer 已另行直接读取并核 `native-fault-r5.py`、递归 CLI／phase 注入器及六个 home 原实验；**脚本 r5 使用的是已审 r3 core／SDK 安装**，不是新的修复产品。外层 exit 0／111.120 秒，37 个内 CLI 均明确使用 r3 `-I -B`，没有用外层 Python 推断内层安装身份。

六例的完整出生 C、owner.context、原授权及完整 cycle bytes／policy／project／ready、原 clock、gate sources、原 start intent／attempt／receipt、native request bytes 和 request→launch→attempt→ack→stopped 引用均已独立重算；保存观察中的完整记录／原 bytes 摘要均匹配原件。共索引 375 原件，111 个保存的已知进程身份当前均已不存活；原 cleanup 确认三端口释放且 errors 为空，本 reviewer 未重新启动服务或占用端口。

- before-hook 在原 native callback 之前退出；launch 已消耗，attempt／ack／stop 与 native started／result 不存在。after-attempt 只留下原 attempt，after-ack 留下完整 stopped，二者同样未进入业务 started／result。各例重复显式确认没有再发 grant；原 final 为 fenced。
- lost-grant 在原 admission.finish 已返回 admitted 后丢失唯一内存 grant；保存的 grant 与原 launch 同一，没有 execute phase／attempt／native body，重复确认仍没有新 launch，最终 fenced。
- result-before-reap 的注入器阻塞的是原 `processes._reap_children`，发生在直接 executor wait 后、后代 reap 前。原 native result 已存在，脚本实际核活的 setsid descendant，保存 marker 与原 S 身份同一；释放前 CLI 原观察无 stopped／停止确认，脚本也核原 final 不存在。释放并沿原 reaper 收完后，完整 stop 与最终 completed 才出现。
- stop-fsync-blocked 的注入器在 `adapter.publish` 已完成文件 fsync 并 link stopped 后、任何父目录 fsync 前停住同一 S。fresh stdlib reader 同时注入 fsync 失败，保存的观察有完整 reap record、durable／executor stop 仍为 unknown。原 owner 消失且无 final 后，正常 reader 同步同一现存链并重读不变 bytes，才确认 stop；该 reader 未补文件、改授权或返回执行权。这是可控存储故障，不是内核不可中断 I/O 验收。

独立结果为 `product-audit/native-fault-r5-audit.py/json` 与 `native-fault-r5-originals-index.json`。先前 r4 驱动未递归穿过 submission、未触发预设断点的失败继续保留；后续 r7 驱动的内层候选身份与 launch 等待失败由作者另行诊断，本节不认证它。上述结果只属于旧 r3 所述合成 CPU 故障窗口，不能替代新修复候选、完整项目／source／clock／run 漂移、最终安装回归／文档／自身模板／独立终核、普通发布与自己的 CI，也不认证训练／GPU／质量／性能。

## r5 修复增量与新 R5：最终整片结论仍待

新 r5 产品相对固定 r3 仅修改 `reference_training_execution.py`，SHA256 为 `f96ac41f7fc84cde7758665917c30994b4a19b80e218123e02190f0830116a08`；本 reviewer 已另存精确字节，不能被后继工作树覆盖。独立逐字核 core／SDK 各 652 份源码→wheel→site 相同、各 283 参考保持，wheel SHA256 为 `815628e0f31766582f3e17df33a6cb0c1341eeb6e418359eb68a902b09c19f02`；两次短 `-I -B` 实际导入均来自对应 site-packages，core 无 Temporal、SDK 有。身份为 `increment-install-r5.json` 与 `runtime-origin-r5.json`。

R3 的锁等待留在同一个 admission helper 的原 compute 循环，每次重新 `require_active/check`，锁内继续完整 current；已有／部分 launch 的 lstat 拒绝及唯一 grant 不变。R4 的非 completed monitor 先保存原 phase unknown，再立即共用 stop→poll→fence；该修正没有延长时钟、新 owner 或另建信号路径。两项**在这些精确修复字节和下述各自验证范围内关闭**；整片最终候选与完整安装 suite 仍须续核，R1／R2 关闭继续保持。

### 新 r5 的实际 CPU、取消、项目漂移及故障原件

已独立核 r7 CPU／持 registry 锁取消／真实活 runner 项目 revision 漂移三例，外层分别 exit 0／26.195、21.641、20.294 秒，共 23 个内 CLI 全部是精确 r5。另核 r8 六故障 exit 0／110.691 秒、37 个内 CLI 全部 r5，递归 phase 注入器与旧已审边界逐字相同，driver 只更换候选／独立实验和原件目录。前述 r7 六故障失败确有内 CLI 仍引用 r3 的错误，保持失败，未借其外层 r5 解释器替它认证。

三例与六故障的原件索引分别为 250 件、390 件，各完整 C／原授权／cycle bytes／policy／project／ready／clock／gate sources、原 start 与完整 managed 链及 saved 原观察均逐项重算同一。已知身份分例 32／28／31／112 个均已死，原 cleanup 各确认三端口释放且 errors 为空；本 reviewer 没有重启服务或再次 bind 端口。CPU 例仍负 gate：两臂 690880，native SUCCEEDED 只表示流程返回，原 archive 因缺 `check:harness_integrity` PASS 拒绝；只读 immutable SQLite 中新 MLflow run `1127dc3c102e42c0ac29aa5b9c640186` 为 FAILED、`gate_passed=0.0`。

真实漂移例通过原 `projects.bind` 将 revision 1 变为 2，没有发本地取消通知。原 monitor helper 输出含 `project-changed`，其 final phase 保留 unknown；实际执行子树在 registry 锁释放前已经 reap 并有同一完整持久 stopped，原 native result／budget final 当时不存在，fence 已进入等待。释放后 final 为 fenced、停止确认 true，total 尚余 139.851 秒，cleanup 为 30 秒，明确是在 compute 尚余时停止，不能归因于预算到期。它补充了 R4 接缝的真实项目失效场景。

原件为 `native-r7-audit.py/json`／`native-r7-originals-index.json` 和 `native-fault-r8-audit.py/json`／`native-fault-r8-originals-index.json`。三例身份验证器首次复用变量名导致把 CPU completed 按取消 fenced 校验，在写审计结论前已修为独立 case_name 并完整重核；原产品与原件未改。

另已核 r9 四个**受控 native payload／file-read 漂移注入**：exit 0／60.349 秒，26 内 CLI 均 r5，289 原件索引。完整 C 的 policy、读取到的原 authorization.clock、gate source bytes、native request bytes 各自被注入不匹配；native marker 记录实际进程身份并确认原 executor.lock 持有，原 stderr 分别包含精确拒绝原因，均无 attempt／ack／stopped 或业务 started／result，重复确认不返 launch。三份 file-read marker 的 before SHA 等于现存原 bytes，按注入器重算 after SHA 也匹配；物理授权、源码和 request 没有被改写。52 个已知身份已死，原 cleanup 通过。这只认证注入的最后 gate，不能冒称完整真实物理 source／clock／run 漂移矩阵；身份为 `native-fault-r9-audit.py/json` 及其原件索引。

### R5 · P2：执行 S 启动异常跳过原 control cleanup 与 final

自身修后原模板 r5 新发现此项，需求 request-changes、维护性 approve。本 reviewer 已核其 31 份完整文件／794,086B、三项祖先资源、939,468B 实际 stdin 与原 result；input digest 为 `ca13faf6750ba8acd91a52030238483d9dcb6f946d6bcff9c49d1f13b3a4380e`，result SHA256 为 `a5c99f5c21968ba3d4c3b701bc29d94984fa60638fc66eefbdc765490ee83945`，Codex 授权回退 run `13bc9d1bd4374c9f943e7bb397bc3153` 为 exit 0／102.987 秒。没有继承它的判断；另直接核以下原调用链和短探针。

精确 r5 `Execution.drive` 第 115–119、153–157 行在 admission 已消耗 launch 并返回 grant 后调用 execute phase.start。原 `_BudgetPhase.start` 第 119–148 行在 Popen／selector 等启动异常时清理自身并 re-raise；drive 只有 finally 收停剩余 peer，没有转入原 fence／cleanup。`BudgetedStart.own` 第 479–502 行在 drive 返回后才合成与发布 final，所以这一异常也绕过原 final。唯一 launch 保持消耗是正确的，但已 submitted 的原 QUEUED 控制 run 没有完成原 owner 的清理职责；该 owner 又不能重启。

独立便宜探针执行上述精确 r5 原 drive AST，在 admission 已返回唯一 grant 后让受控 execute.start 抛 OSError。实际事件只剩 monitor stop／finish，异常传播，无 fence／cleanup，也没有返回 outcome；它没有实际调用 Popen、运行业务或创建物理 launch，范围为启动错误传播与原协调路径。原件为 `execute-startup-r5-probe.py/json`。原计划规定全部 peer 终止后合并观察并发布原 final，不能仅用不重复 launch 代替这一职责。

最小修正仍可留在原 start 协调接缝：保留该 phase 的 unknown 启动观察，先停止／poll 已启动 peer，再进入既有 fence／cleanup，并给 own 返回可分别呈现的 outcome；无论启动失败、相同确认或恢复，都不能返还已消耗 launch。作者已接受 R5，正在保留旧 r5 安装实红并修正，**R5 当前开放，最终整片需求／结构结论仍待**。本轮没有修改产品或测试、安装、运行训练／长 pytest、commit／push 或外部写入。

## r6 修复和新原件复核：R5 关闭

本节只关闭精确 r6 修正及核实下述原件，不提前给整片最终 verdict。r6 相对已审 r5 的产品仅在原 `Execution.drive` 协调接缝处理 phase 启动失败；`reference_training_execution.py` SHA256 为 `1cf2f686fd009b544a1c4926d0e0d4ba7b9c5a7e129620e53f89cf77f982ba1d`。本 reviewer 已直接读修正，独立从当前源码→wheel→core／SDK site-packages 各核 652 份完全相同，并将 283 参考文件逐份与原基线 Git blobs 对比，相同。wheel SHA256 为 `f1106d11b7c6b074b5f35c5a3d96208267735536cbdd549a6dbbb577f6c93a44`；两次短 `-I -B` 导入定位各自 site-packages，core 无 Temporal、SDK 有，原依赖与 reference 检查各 exit 0／283 PASS。身份保存于 `product-audit/verify-install.py` 和 `install-verified-r6.json`，没有重新安装或运行 suite。

私有 r6 构建 driver 曾误把 aggregate 写到旧 r5 输出名，作者此前已保留 r5 精确原件，随后另存实际 r6 并恢复旧名。独立确认 `build-install-r5.json` 与 `build-install-r5-before-r6-exact.json` 相同，SHA256 为 `20540153ccdaffb1c644572d2c48a1192e52a52fb6890b6132251e31b1fab1fa`；新 r6 aggregate 为 `647b82c080083bf46dbf3bd86014b9f997fb3f378cae6d7b3818bf3fe36ec0fd`，各实际步骤与候选／exit 0 匹配，见 `build-placement-r6-audit.json`。不声称旧输出名从未被误写。

**R5 在该精确 r6 范围关闭。** 局部 start 保留未启动 phase 的原 unknown 观察，捕获原启动 OSError／返回 false，再将现存 peer 送入原 stop→poll→fence；fence 起不来保留 unknown，cleanup 起不来将 control unknown 单独呈现。原 phase reaper、clock、launch、attempt、远端客户端均未另建或重试。独立执行精确安装 r6 原 drive AST 的受控短探针，确认 admission 只授予一次、execute.start 只调用一次，异常后 monitor 收停、fence／cleanup 顺序完成且返回原 fenced／control requested outcome；其范围仅是协调接缝，没有物理 Popen／native／授权或 launch。原件为 `execute-startup-r6-probe.py/json`，旧 r5 的传播异常探针继续保留。

原安装实红 `startup-repro-r5.xml/stdout` 为 1 failed／23.875 秒（XML），确在真实 detached owner 已消耗 launch 后注入原 execute Popen 失败，十秒内没有 final。最初名为 `source-startup-fix-r6` 的命令实际上仍载入旧 r5 安装，1 failed／2 passed／23.765 秒保持该身份；显式源码路径的 `source-startup-fix-r7` 才是 3 passed／22.111 秒。修后 no-launch 用例相应等待原 fenced final，随后相同确认被拒绝，并继续核原 launch bytes；它不被解释为返还或重新 admission。

### r6 三条实际旅程

新独立原授权的正常 CPU／持 registry 锁取消／真实项目 revision 漂移，分别为 26.763848／21.694216／20.121579 秒，共 23 个内 CLI 全部精确 r6、exit 0。完整出生 C、原 owner／授权／cycle bytes／policy／ready／clock／gate sources、原 intent／attempt／receipt／native request，以及 managed request→launch→attempt→ack→stopped 全链均独立重算；保存观察及 final 与原件相同，索引 250 件。各例 30／30／31 个已知身份均已停止，原 cleanup 均确认服务收尾、三端口释放、errors 为空；本 reviewer 未重启服务或重新 bind 端口。

正常例确经过原 Git mirror／两 worktree／真实 setsid 后代／archive／MLflow track，final completed 且持久停止确认 true。两臂 CPU 结果仍为 690880；原 archive 因缺可信 `check:harness_integrity` PASS 拒绝，gate false。只读 immutable SQLite 核新 run `fa8566e991d041d48e4880be64867cc9` 为 FAILED、`gate_passed=0.0`，不将 native SUCCEEDED 写为质量成功。持锁取消例在 registry 锁释放前已经 reap 同 job 执行子树并持久 stop，当时 native result／budget final 不存在、fence 等待；释放后原 final fenced、停止确认 true。

真实漂移通过原 `projects.bind` 将 revision 2 改为 3，没有本地取消通知。monitor 原输出含 `project-changed`、其 phase 保留 unknown；registry 锁尚持有时已实际回收并持久 stop，native result／budget final 不存在，fence 等待。释放后原 final fenced、停止确认 true；total 尚余 140.203843 秒、cleanup 为 30 秒，明确仍有 compute 余量。该例继续支持 R4 的真实失效停止路径，而非预算到期或显式取消。身份为 `native-r10-audit.py/json` 及 `native-r10-originals-index.json`。

### r6 七个实际故障窗口与四项受控 gate 拒绝

七故障原运行 123.272426 秒、42 个内 CLI 均精确 r6／exit 0，444 原件逐项核；126 个已知身份均已停止，原 cleanup 三端口释放、errors 为空。前六窗口为已审同一注入边界的新独立原授权，分别保留 before-hook 无 attempt、after-attempt 仅 attempt、after-ack 完整 stop 但无业务 body、lost-grant 不启动 S／不返 launch、native result 先于后代 reap、stop link 可见而目录同步卡住。result 窗口在直接 executor wait 后阻塞原 `_reap_children`，实际 setsid 后代尚活、保存观察无 stop／final；释放后由原 reaper 收完。stop 窗口在原 adapter 已 fsync 文件并 link stopped 后、任何父目录 fsync 前阻塞，fresh observer 注入 fsync 失败时保持 durable unknown；原 owner 消失且没有 final 后，正常 reader 同步并重读同一现存 bytes 才确认，不补文件或返执行权。

新增 execute-start-failed 直接在原 owner 的原 `_BudgetPhase.start` 中让实际 Popen 抛 OSError；marker 对应 owner 与唯一 execution phase，没有 execute 输出子树／attempt／ack／stop／业务 body。原 final 已是 fenced、control requested、signal delivery acknowledged；execute 观察为 unknown、stopped false、helper_process null，并保存原启动失败理由。total 尚余 92.542089 秒、cleanup 20 秒，launch 仍一次消耗，没有 regrant。这条实际原生控制旅程补足上述短探针与源码回归，支持 R5 关闭。身份为 `native-fault-r10-audit.py/json` 及 `native-fault-r10-originals-index.json`。

四个受控 native payload／file-read 漂移原运行 61.368003 秒、26 个内 CLI 均精确 r6／exit 0，289 原件逐项核，52 个已知身份均停止、原 cleanup 完整。C.policy、读到的 authorization.clock、gate source bytes、仅增加换行的完整 native request bytes，均在 marker 确认原 executor.lock 持有时被精确原 gate 拒绝，无 attempt／ack／stopped／业务 body，launch 不返还。独立重算注入 before／after SHA，现存物理授权／源码／request bytes 未改；注入器与已审 r9 相同，仅 driver 更换 r6 与新实验目录。此项认证受控读取／payload 反例，不称完整真实物理 source／clock／run 漂移矩阵。身份为 `native-fault-r11-audit.py/json` 及 `native-fault-r11-originals-index.json`。

### r6 自身模板与检查的实际范围

已独立核 run `35067fcac3fb4437a97a398e3fa66532` 的原输入／回复：31 份完整文件 800,054B、三项祖先资源、完整 task／diff 均在同次 954,391B 实际 stdin，input digest 为 `e3f3370d7ea96b144e59b8cdc03e99195bee3852be976048c55bc8a1b28fd993`，原 result SHA256 为 `0c5de8137fc994603aad0cb6fbfdeaba6fbb99055dfa513077cb007bfe231b05`。Codex 授权回退 exit 0／65.888445 秒、需求／维护性均 approve；本 reviewer 只据原资料认证其所供文本与原结果，不转授为异后端、runtime 或 CI 认证。见 `self-review-input-r6.py/json`。

安装 `processes`＋`architecture` 两 suite 已直接读原 XML／stdout：24 passed／4 Windows 专项 skipped／12.653 秒（XML）、无 failure／error。174 份冻结 test／example 输入共 1,682,471B 均逐字匹配清单及当前源码，manifest SHA256 为 `95f041d527eab417a40af4eb889330604ed78a46d26bc111bb6fb6302a88981d`，见 `verify-test-inputs-r6.py`／`test-inputs-verified-r6.json`。

此前完整八 suite 的 186 passed／5 skipped 属于 r3 安装配 r4 冻结测试；188 passed／5 skipped 属于 r5 安装配 r5 测试。r6 这次命令意图按 `-k` 选择受影响项，但父目录 `training-managed-execution` 使筛选实际命中整个原 submission suite，独立 collection 为 84 项；其原运行仍待终态，不称 r6 完整八 suite 已跑。最终固定完整差异／文档与该运行终态仍须续核，整片最终本地两轴结论待后节；普通发布／固定 Ref／自己的 CI 未被本节认证。

## 最终本地复核：两轴 approve，开放 0／0

最终固定范围为 `product-source-r7/scope.json` 的 30 份全文，SHA256 为 `d477d76e390ec452f4e821b2e14cce77967549a7e5193e53a7f94b057790386c`，产品基线仍是 `75285e3271bb93271eaea050ca7812cb0cd98b5a`。独立核每份长度／SHA、完整 tracked diff 与基线差异相同；diff SHA256 为 `c7a3b7b4d52d754b0259917b78e3fa12116692cb09711dd77a80dc438afa18fb`。本片全部 tracked／untracked 改动均在范围内，后继 controller 的两份纯计划文档明确排除；本报告是声明允许继续追加的唯一 live review 文档。r7 相对 r6 快照只去掉交付记录中通向不随本片发布的后继草案链接，产品／测试 bytes 未变。

30 件中的产品源码逐字匹配上节已独立认证的 r6 core／SDK 安装，所列测试逐字匹配 r6 冻结输入；17 份 Python AST 有效。此前已读的 README／训练手册／架构公开交接与最终计划／交付状态相符：新出生能力下显式 execute、旧 owner 不补权、仅观察不重新执行、同原件 durable 恢复及 CPU 验收界限均清楚。独立按基线 Git tree＋本片实际发布 scope 核 13 份 Markdown／442 个本地链接，零缺失；未以工作树中存在的后继草案冒充会发布的文件。见 `verify-final-scope-r7.py`／`final-scope-verified-r7.json`。

安装回归的原运行现已终结，逐项核命令、原冻结输入、XML 与 stdout／stderr：

|安装产品／冻结测试|实际范围|通过／跳过|XML 秒数|
|---|---|---|---|
|r3／r4|当时完整八 suite|186／5|1001.846|
|r5／r5|当时完整八 suite|188／5|1022.117|
|r6／r6|原 submission 完整 84 项|84／0|801.415|
|r6／r6|完整 processes＋architecture 两 suite|24／4|12.653|

上述各运行均 exit 0、无 failure／error。r6 submission 的 stdout 为 801.52 秒、外层命令 802.672 秒；84 个 collection 名称与 84 个 XML testcase 逐项相同，没有把原意筛选子集误记为实际范围。r6 两项合计 108 passed／4 Windows 平台 skipped，不称完整八 suite；旧 r3／r5 的完整回归保持各自候选。原件与身份为 `verify-saved-checks-r6.py`／`saved-checks-verified-r6.json`；本 reviewer 只读验证，没有再次运行 pytest。

|审查轴|最终本地结论|开放 finding|
|---|---|---|
|需求／行为正确性|approve：显式单次 launch、最后原生 gate、原执行子树回收、同链持久停止、失败控制清理与既有预算／所有权合同一致|0|
|结构／可维护性|approve：职责留在原 owner／phase／process reaper，协议跨解释器由实际消费者共享，没有第二 scheduler／实验账本／时钟或新重放权限|0|

R1 的结果传播和 R2 的停止通知顺序在已固定修复及 r6 保持；R3 原 writer 锁争用的同 compute 有界处理、R4 原 monitor 非完成的及时 stop／fence、R5 原 execute 启动失败的 fence／cleanup／final，均按前节各自接缝／原安装实红／修后安装与实际旅程证据关闭。r6 的三旅程、七故障、四受控 native gate 拒绝共 91 个实际内 CLI 原件均已独立核到精确安装与原链；清理记录和已知进程核验如前节。历史自身 request-changes、旧安装实红、错误候选／失败驱动及恢复均保留，不改写为当时通过。

本地审查已完成；余下必要交付门禁是普通提交／推送的精确本片 scope、完整远端 Ref、该固定候选自己的必要 CI run／attempt／job／步骤终态及原 reviewer 的固定发布续核。本报告当前没有认证它们，也不借前置 c1 的成功。GitHub 预检首个 403 仅在工具原输出中，没有独立保存 HTTP body；另有官方 `/rate_limit` 的 200 原响应记录 core remaining 0／reset，二者均不是本片 CI 结果。额度恢复后由发布流程另存该候选真实响应与核验，不改变鉴权或绕限制。

本结论只认证所列工具行为与合成 CPU 生命周期、受控故障和身份拒绝。真实业务训练／GPU／模型与数据质量／性能收益、Q4.2c 自动循环及完整其他外部能力继续各自后继验收；kernel 专家留在 v3 提案路径，原实验／比较／批准／采用权不变。parent 继续开发工具，业务优化仍通过 Ergora 任务。本 reviewer 的写入仅为本报告及授权 ignored 审计目录，没有产品／测试编辑、安装、服务／训练、长 pytest、commit／push 或外部写入。

## 固定普通发布 ac86043：两轴 approve，自己的 CI 待

已独立核固定 commit `ac86043d9e11983750bf63b90c0dfcbeea05ea41`，唯一父提交为原基线 `75285e3271bb93271eaea050ca7812cb0cd98b5a`。commit 相对父恰好修改本片 30 件，逐份长度／SHA256／Git blob OID 都与 `publication-staged-r1.json` 相同，文件集合与最终 r7 完全一致；后继 controller 的两份纯计划文档均不在 commit tree 中。

相对 r7 快照，只有 `docs/PLAN.md`、本片两份 plan、delivery 和本报告五份文档收尾，逐项读到的都是本地两轴 approve／开放 0／0 与后续发布门禁记账，没有改变产品或验收合同。commit 中的原审查报告仍精确等于最终本地快照：45,743B／SHA256 `7b3cc906075ed0c77bd4b021b221204fa82976bab3faf3d11e410a1cc765e804`；本节是在其后追加的固定发布续核。

直接按 Git commit tree 中的完整 blob OID 核 wheel 及 core／SDK 各 652 份安装 bytes，均相同；283 参考文件的路径／mode／OID 与基线完全相同，发布测试与 r6 冻结测试逐字相同。验证器首轮把仓库专用、不打包的 `src/ergora/AGENTS.md` 也算入 wheel 集合而断言失败；已保存 `publication-verifier-setup-failure-r1.json`，显式核其基线不变并分清 653 个仓库文件与 652 个包文件后完整通过，未把这次收集假设错误记为产品或发布失败。

原普通 push stderr 显示 `75285e3..ac86043 HEAD → refactor/architecture-foundations`，已核其原 bytes SHA 与发布记录一致。独立实时 SSH `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations` 在 2026-11-15 06:17:38 UTC 开始、exit 0／1.325 秒，完整 Ref 精确为该 commit，stderr 空；原保存 Ref 与之同一。固定来源及原输出身份为 `verify-publication-r1.py`／`fixed-publication-verified-r1.json`。

**固定发布需求／维护性两轴均 approve，开放 0／0，R1–R5 关闭保持。** 这一步核实普通发布与精确候选，没有重跑 suite、安装或实际旅程，也没有访问已知限额中的 GitHub API。该 commit 自己的 CI run／attempt／jobs／必要步骤尚未取得并认证，继续开放；后续按官方额度恢复后取得的真实原件续核，不能借前置 c1 或本地检查完成此门禁。真实训练／GPU／质量／收益及后继自动循环的范围保持前节限制。

## 自己的 CI 首次官方来源核验：在途，未给终态结论

已直接核额度恢复后保存的首次官方响应：`ci-r1/20261115T062259895303Z-runs.json` 为 11,989B，SHA256 `a786ec0c0a2bda9dbe8678a14c250d19af627eeeff8fa420a45211bf75aa33e9`，与同次 HTTP metadata 的长度／SHA 相同。metadata 记录匿名 GET 官方 `api.github.com/repos/626619403/Ergora/actions/runs?head_sha=ac86043d9e11983750bf63b90c0dfcbeea05ea41&per_page=100`、HTTP 200，观察时间 2026-11-15 06:23:00.708065 UTC，晚于原官方 reset；没有将此前 403 异常输出冒充本次原件。

该精确 SHA 的响应只有一个 run：[Portability 43684533043](https://github.com/626619403/Ergora/actions/runs/43684533043)，attempt 1／run number 233，push 到原开发分支，创建时间 06:14:29 UTC。原响应的仓库／head repository、完整 head commit 与 tree、workflow ID／路径均与固定发布相同，保存 summary 逐字段匹配原响应。**在这次观察时 status 为 in_progress、conclusion 为 null**，没有据此给 CI 成功或失败结论。

另从固定 commit 直接读 workflow、六个 Linux 分组及原 CI runner 来源并登记长度／SHA。它们定义 plan＋六 Linux native＋一 Windows native，共八 job，30 个必要步骤；这是待核终态的固定预期，不是已经观察到八 job／30 步成功。固定发布需求／维护性 approve／开放 0／0 保持，自己的 CI 仍待实际 run／attempt／jobs／步骤终态原件及续核。此轮没有新网络请求，结果为 `verify-ci-initial-r1.py`／`ci-initial-origin-r1.json`。

## 自己的 CI 原终态失败：Windows 历史夹具 setup，接续未闭合

已直接核官方保存的 `ci-r1/20261115T064300157007Z-runs.json`／`-jobs.json` 及各自 HTTP metadata：均 HTTP 200，原 bytes 分别为 11,992／21,121，与 metadata 的长度／SHA256 相同。run 精确是 `ac86043d9e11983750bf63b90c0dfcbeea05ea41` 的 Portability `43684533043`／attempt 1／#233，原仓库、分支、push 事件、完整 head commit／tree 与固定发布同一；status completed、conclusion failure，updated_at 为 2026-11-15 06:42:52 UTC。八个 job 的 run／attempt／完整 head SHA 均一致，逐一核固定 workflow 的预期集合，没有用 summary 替代原 jobs。

实际结果为 plan 和六个 Linux native job 成功，Windows job `132722147582` 失败。30 个必要步骤逐项恰好出现一次、均已终止，**29 success／1 failure**；唯一失败是 Windows 的 `Native application regression`。同 Windows job 的 build／packaged reference、PowerShell 5.1 installer and upgrade、upload observations 均成功。它不是八 job／30 步通过，原 c2 CI 交付门禁继续开放。

另核 `20261115T064400163955Z-windows-annotations.json`／`-http.json`：官方 check-run URL 精确对应该 Windows job，HTTP 200，4,664B，SHA256 `12c87975096bec1ff24cbbac422719256aa812d9ea4cb70cffdc0fc167f2f662` 与 metadata 相同，各 annotation 的 blob URL 均指向原 ac86043。`Native regression` 注释尾部报告 **1179 passed／876 skipped／6 errors／16 subtests passed／1557.34 秒**。六条 ERROR 为 SDK-free history 一项及 inconsistent original chain 的 numeric-identity／native-runner／foreign-ack／duplicate／fifo 五参数，原因均为 `Native training submission requires Linux; use the registered runtime in WSL2`。这是官方注释中的截取日志和汇总，不冒称取得完整 job log、XML 或下载产物。

诊断另从固定 ac86043 的 Git blobs 核实，未使用当前维护中的测试替代原输入：`tests/test_training_submission.py:42` 的 `historical_execution` 夹具在第 49 行无条件调用 `reference.training_submission(..., 'prepare', ...)`，六例都依赖它；原 `src/ergora/reference.py:496` 的入口对非 status 操作在非 Linux 平台直接拒绝。该拒绝发生在历史 reader 测试体之前，与六个原 setup errors 一致；fifo 的测试体内 skip 也尚未到达。相关测试源码 SHA256 仍为 r6 冻结值 `1b9257535ceea369696ce49240287acedc69f0d0c499ce994b614f8810f2fdaf`。这项可移植夹具问题应由独立测试维护片修正并保留离线 reader 的平台验收，不构成放宽产品 Linux 原生提交边界的授权。

本地／固定发布两轴结论及 R1–R5 关闭按原核实范围保持；它们不覆盖这次 Windows 验收缺口。原 run 的失败原件和结论完整保留，当前不认证在途维护修正或其后续发布／CI；维护片须按自己的固定输入、独立审查及精确 CI 接续闭合。身份、30 步重算与固定源码诊断为 `verify-ci-terminal-failure-r1.py`／`ci-terminal-failure-r1.json`。本轮没有新网络请求、产品／测试／其他文档修改，也没有重跑 suite、安装、服务或训练。
