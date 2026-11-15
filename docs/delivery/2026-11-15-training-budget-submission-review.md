# B3.2 原训练预算提交：独立产品审查

日期：2026-11-15。审查者为新建 fresh-context `training_budget_submission_audit`；未继承实施对话。按仓库 `AGENTS.md`、组件协议及 `maintainable-project-delivery`、`ergora-codebase-quality` 的 module-design／test-seams 执行。产品只读，仅本报告和 ignored reviewer 原件可写；没有修改产品、安装依赖、提交、推送，或启动服务、模型与训练。

**r4 最终本地产品审查：需求 approve，结构维护 approve；开放 0／0，R1 已关闭。** 同一独立审查者核过固定 r4 全部候选、最小修正、两安装、故障回归、真实控制旅程、自身原模板及进程／服务收尾原件。原 r3 实红、r4 首轮失败和各候选范围保留；本结论不认证发布、CI、B3.3 executor 停止或真实训练。

**R1／P2 历史 finding，r4 已关闭。** r3 的 [own](../../src/ergora/reference_training_budget.py#L246) 在 owner 生命周期锁内直接调用 `_record(final.json)`；[原 writer](../../src/ergora/training_cycles.py#L273) 在 link 前文件 fsync、link 后目录 fsync，均不受 `supervise` 的原 clock stop predicate 约束。文件 fsync 阻塞时尚无 final，目录 fsync 阻塞时虽有 final 仍持 owner 锁；两种情况下原 [observe](../../src/ergora/reference_training_budget.py#L169) 的 final 存在且 owner 已结束分支均不可用，持续显示 active，无法完成已有精确 fence 的恢复。首次静态遍历未发现问题，随后自身原件 `self-review-r3-codex/review.md` 指出此处，本审查者沿 r3 冻结源码独立确认需求 request-changes／1；结构维护没有另外阻塞 finding。以下 r4 处置与实红／修后证据关闭此问题，保留原结论的历史范围。

产品基线为 `b53bba613a3c02b14c69a6df9b0d526755d7e216`；工作树 HEAD 为 `b78f7b233316f3248c5a5865d90e6a23870693ac`，两者仅四个前置边界测试／记录文件不同，无产品变化。本片完整候选来自 ignored `review-scope-r1/{scope.json,author-diff.patch,files/}`，含 untracked；22 个原件全部匹配清单 bytes／SHA，首次审查时当前工作树也全部逐字相同。8 个产品文件为 `cli.py`、`reference.py`、`reference_training_submission.py`、`services.py`、`training.py`、`training_cycles.py` 及新增 `reference_training_budget.py`、`reference_training_worker.py`；另核原提交、取消、reference、services、架构测试及三份 SDK fixture，和清单内七份计划／使用／架构／交付记录。明确合同为[本片 r3 计划](../plans/2026-11-15-training-budget-submission.md)。

已沿真实调用链核对的需求和结果：

- [原提交](../../src/ergora/reference_training_submission.py#L81) 的预算字段为可选；旧意图的 expected／attempt／receipt／memo 算法保持。首次绑定完整来源、选择、观察、项目修订与剩余计算期；已存意图不换 budget，省略选择仍由原意图发现绑定。缺源观察标 unknown，不授予新发送权限。
- [dispatch](../../src/ergora/reference_training_submission.py#L214) 在远端 lookup 前确认独立 owner，在昂贵 preflight 后、原 attempt 写入与目录同步后再核 owner／clock。原 `.attempt.json` 是唯一不可归还 slot；已有 attempt 的 dispatch／resume 只返回／对账同 run，NOT_FOUND／lost-ack 不走第二次 start。
- [owner](../../src/ergora/reference_training_budget.py#L134) 使用独立 session，身份绑定原 intent／authorization、完整缓存摘要、boot／PID／start ticks 和原锁。已存在身份时不重启；owner 不获取 submission 锁。确认后的完整来源、DB／native probe、registry fence、控制面清理与 r4 final 发布位于受监督 helper，compute／cleanup 共用原 clock stop predicate。
- [实际预算 adapter](../../src/ergora/reference_training_worker.py#L21) 复用固定 native create 算法，在其 registry 锁内最后 lookup、写新 request 前检查完整原源／Experiment、budget、owner 与 clock；`ContextVar` 在 finally 复位。已有 request 的读取、poll、fence、gate 和人工 release 不受新工作准入 gate 阻断。
- [worker](../../src/ergora/reference_training_worker.py#L55) 的真实 factory、SDK 注册和版本 queue 与 [managed services](../../src/ergora/services.py#L132) 接线存在；预算服务使用应用 Python 和可选 SDK，旧 `training-worker` 仍用原 native 命令／queue，没有回落。CLI 只传输原用例输入。
- [fence 持久观察](../../src/ergora/reference_training_budget.py#L199) 在原 adapter 的精确 fence 后同步 fences、training 和原 state 根目录，随后重读完整 binding；cleanup 过期或 helper／fsync 失败不能记持久确认。已有 final 的恢复只 flush／重核同一可见 fence，不新建 owner、fence、授权、attempt 或改写原 final。
- [完成与清理](../../src/ergora/reference_training_budget.py#L293) 验完整原 request／runner，匹配已完成 native 结果单独保留；有效成功及等待人工 release 不统一 fence。其余清理只沿原 run／memo 和 [稳定取消 ID／reason](../../src/ergora/reference_training_worker.py#L99)；没有接入 B3.3 executor 或自动循环，`executor_stop_confirmed` 保持 null。API／密钥处理未新增明文配置。

结构维护核查没有另外的阻塞 finding。预算模块把来源、身份、时钟、连续生命周期和持久观察集中在同一 owner，生产消费者是原 submission 与专用 worker 边界；worker 模块集中 adapter／SDK／进程入口及取消接线，使预算 owner 不反向依赖 submission／cancellation。新增短函数分别是严格绑定入口、进程身份算法、原用例入口或现有 factory 的必要构造接缝，未发现只为单次转发新建的公共抽象或具体实现分派。新增 guard 对应持久身份、来源、资源或并发失败；没有提出删除这些分布式／恢复检查。测试沿原 suite 和 SDK fixture，accepted／held、owner death、blocked observation、registry lock、fsync failure／delay、lost-ack／缺源及完成 native 各暴露不同失败，未发现应删的浅层重复矩阵；r4 已补 final 文件／目录同步的两个不同故障接缝。模块 AST／真实调用者核查原件在 ignored reviewer 目录。

r3 首轮实际核验与历史证据边界：

- 审查者实际执行冻结 22 文件摘要／bytes 核查、两新增模块 AST／调用者核查、`git diff --check`（通过）及 source／wheel／两非 editable 安装逐字比较。两安装各 648 件同一，清单摘要同一，wheel SHA 为 `c29bfc0fb2c1f97583b1545fe514b063a2c88f5152ba638d169e9a577e0d2f71`。实际 Python stdin 原文及输出保存在 ignored `.ergora/checks/training-budget-submission/reviewer/{inputs-r1.md,*-r1.py,*-r1.json}`；未替代运行验收。
- 已查作者原件：r2 真实 owner＋SDK 服务替身 8 passed／153.91 秒；r3 源码 9 passed／2 failed 保持原失败，所述两处验证预期／清理修正后，在最终安装受影响 2 项 25.72 秒通过；新增 completed-native 1 项 15.75 秒通过。两安装包身份、依赖检查和原 283 reference PASS 原件存在，并已独立重核包字节；这些结果各保留实际范围。
- 首次审查时，完整五 suite 的固定 173 份测试／fixture／examples 快照仍在途。真实服务 r3c 已完成原 queue／native request／自动 fence／acknowledged 取消后，在 inventory 把空锁 bytes 当 False 的验证处退出 1；它不是全旅程 pass。其后同一原 cycle／run／slot 的第二次只读恢复 10.430 秒通过，原失败、第一轮 query timeout 与原目录／计时保留。
- 本审查没有运行行为测试；未认证真实 executor／后代停止、GPU／训练质量／性能收益、B3.3、自动循环、发布或 CI。后续产品若改变，不能继承这次逐字身份与检查结果。

**r4 处置与终核证据。** 完整 r4 候选为 ignored `review-scope-r4/{scope.json,author-diff.patch,files/}` 的 22 件，含 untracked；全部 bytes／SHA 匹配。r3→r4 的产品修正只在预算 owner：其 [final 发布](../../src/ergora/reference_training_budget.py#L275) 复用原 `supervise('publish', cleanup=True)`，helper 在完整缓存／原 intent／活 owner 身份核验后调用原 immutable writer。文件与目录 fsync 都受原 cleanup clock 的 stop predicate 监督，没有第二份时钟或延长额度。无 final 且原 owner 已结束时，[观察分支](../../src/ergora/reference_training_budget.py#L191) 仅调用原 `durable_fence()`；缺 fence 返回空，已有 fence 只同步／重核，owner 保持 unknown，不写新 final／fence／owner／授权／attempt。改动保留正常 completion，未扩张取消或 executor 职责。

审查者独立逐字核两套 r4 非 editable 安装各 648 件 source／wheel／site-packages 和原清单同一，wheel SHA `27a27377df2be065c3fe08df2f2e5fe3bf43df80b96e5f14fe061e3071c1b972`；原 283 reference PASS 与依赖检查原件俱在。r3／r4／r4b 各 173 份测试／fixture／examples 冻结输入均独立匹配摘要，当前测试与 r4b 完全一致。r3 原五 suite 为 111 passed／1 skipped／716.84 秒；r3 final 文件 fsync 实红为 1 failed／34.00 秒。r4 首轮 15 项保留 12 passed／3 failed／241.56 秒；最终 r4b 精准四项为 4 passed／58 deselected／93.12 秒，覆盖全部三个原失败和两种实际 fsync 注入，不合称一次全十五项通过。两种 final 故障各有真实 marker 和 publish stdin：文件故障没有 final，目录故障已有同一 final；缓存／intent 摘要均与原 owner 相同。测试验证 owner 真实退出／锁释放后，恢复仅核原 fence 和原件不变；原正常 completed-native、held、owner death、lost-ack／缺源及实际 factory 接缝保留各自 r4 通过范围。R1 实红与修后同一风险可观察，修正测试没有削弱一次性 slot、原 fence 或进程停止的断言。

真实 r4 旅程 `native-journey-r4-execution` 为 exit 0／47.4759 秒，实际本地 Temporal＋预算 worker 消费版本 queue，产生一个合成 unchanged Experiment 的 queued native request，随后自动持久 fence、对同一原 run 发出 acknowledged 取消并 resume 读回。审查者沿原 `native-location-r4.json` 独立核对 23 项保存的授权／空锁、intent、attempt、receipt、request、fence、final、九条 CLI stdout／stderr 摘要和服务收尾，全匹配；当前五个已捕获 owner／helper 完整身份均不存活，原 owner session／进程组无活后代，managed socket 已消失，7233／8233 无监听。没有 executor started 记录，也未创建第二个候选 request。`executor_stop_confirmed` 仍为 null，取消送达与本地 fence 没有被写成训练停止证明。

自身原结构模板 r4 为 run `6ce000618e764488b42dcde5c7ae2a37`，56.218 秒 succeeded／approve。审查者另核 18 个冻结完整文件 240668B 的摘要及其全文均进入真实 stdin，三份祖先 instructions／skill 内容均在 stdin，prompt 与 stdin 逐字相同，原 result SHA `a1de5835bfa83ab8a0c067c47092beb30deb5dee699537f82aa1c32fb533518d` 匹配。模板只认证给定源码文本，运行原件由本独立审查另核；不把模板批准转作未见运行或 CI 结论。

本轮实际只读核查的命令源文与输出保存为 ignored reviewer 的 `identity-check-r4.py/json`、`native-evidence-r4.py/json` 和 `supplemental-evidence-r4.py/json`；没有重新运行昂贵服务、安装或行为 suite。冻结 r4 后仅 `docs/PLAN.md`、本片计划、交付的当前状态／历史标识更新，经逐项核对与实际终态一致，没有改变设计合同或产品。报告源码链接改为仓库可用的 `#L` 锚点并按最终源码复核；状态同步不触发新产品审查。

最终本地开放 finding：需求 0、结构维护 0，R1 已关闭。普通发布与自己的 CI 仍须分别结算；前置 B3.1 的原 CI 失败与 b78 修正继续保留其原片身份。Kernel 专家保留在 v3 优化路径；B3.3、自动循环及真实业务优化继续按原计划通过工具验收。

**固定本地提交补核。** 同一审查者沿 Git 原件核对 `75d1ee325288527f67fb1ea814332d1522ff4860`：唯一 parent 为 `b78f7b233316f3248c5a5865d90e6a23870693ac`，tree 为 `bf234c59476e777f1307bcb60faffc56b79b2b92`。23 个变更 blob 的 bytes／SHA／Git OID 与原 staged、local 两份清单完全匹配；相对冻结 r4 的 22 件，只有 `docs/PLAN.md`、本片计划和交付三份当前状态／历史记录不同，逐项阅读未改变设计合同，另加入本报告原文 SHA `05daf601eb461d985ee8786de960f6726f8bfae846039e32d09c9fd98ef20b53`。没有 B3.3 设计／产品或旧片五份记录夹带。Git archive 的 648 个产品文件与 r4 wheel、core／SDK 两安装原件全部逐字相同；没有重跑安装、行为 suite、服务或训练。需求 approve、结构维护 approve，阻塞 finding 仍为 0／0，R1 保持关闭。

本次完整固定提交的静态检查有明确诊断：`git diff --check b78f7b233316f3248c5a5865d90e6a23870693ac 75d1ee325288527f67fb1ea814332d1522ff4860` 返回 exit 2，`src/ergora/reference_training_worker.py:141: new blank line at EOF.`。该空行已存在于受审 r4 原件，属于非阻塞格式项；先前 worktree diff 通过未覆盖当时的 untracked 新文件，不能据此前检查宣称固定 commit 的差异检查全通过。

按固定 Git tree 核对 8 份 Markdown 的 313 条相对链接，设计审查报告中的五个 `plan-audit/` 证据目标仅存在于本地 ignored 目录，不能作为 GitHub 下载链接；其余相对目标存在。本报告 15 处链接及源码 `#L` 锚点另核有效。固定 PLAN 另有一处“最终独立终核待”的旧状态短语。作者后续未提交的纯文档记录已把五项标为明确本地路径文本并同步该状态；这些记录修正不属于上述固定提交，也不改变产品批准范围。本补核命令原文与输出保存在 ignored reviewer 的 `commit-check-local-r1.py/json`，三份状态差异保存在 `commit-status-docs-local-r1.patch`。

本补核只认证固定本地提交及其与已验 r4 原件的身份；远端精确发布、自己的 CI 和后续记录提交仍待分别核结。

**普通远端发布与自身 CI 首轮观察。** 已核作者普通精确 push 的 exit 0／11.7834 秒原件和完整 SSH Ref：`75d1ee325288527f67fb1ea814332d1522ff4860 refs/heads/refactor/architecture-foundations`。UTC `2026-11-15T01:58:43Z` 起独立匿名 GET 官方 GitHub，Ref REST、commit HTML 和 branch HTML 均为 200 且绑定完整 75d SHA；commit 页面中的唯一 parent 与全部 23 个变更路径同已审本地对象。完整 SHA 绑定上文已验 tree／blob 身份。commit REST 与 runs REST 两项实际返回共享 IP 配额用尽的 403，原错误／headers 保留，没有记成成功，也未据此声称直接取得远端 tree／blob REST 原件。

随后由官方 Actions 页面发现本 SHA 自己的 [Portability run 43665465985](https://github.com/626619403/Ergora/actions/runs/43665465985)：run number 228，push 于 `2026-11-15T01:57:18Z`，完整 commit 链接为 75d；run 页面和首方 `job_groups_batch?attempt=1&batch=0&size=200` 均为 200，明确 attempt 1。UTC `01:59:54Z` 导航显示 `totalCount=8`／`hasMore=false`，plan 为 success，六个 Linux group 和 Windows all 共七 job 为 in_progress，CI 门禁仍在途。必要步骤由固定 75d workflow／六组显式分组导出，仍为八 job／三十项，不借用 b78 的 CI。

独立发布原件与命令保存在 ignored reviewer 的 `ci-publication-r1/`，首轮索引为 `publication-identity-r1.json`、`workflow-contract-r1.json`；每次 GET 的实际 URL／时间／status／完整响应 bytes／SHA 与 headers 均保存。此后低频观察同 run 终态，再核各自适用步骤；原 r3／r4 失败和固定提交静态诊断保持，尚未认证自身 CI 通过。
