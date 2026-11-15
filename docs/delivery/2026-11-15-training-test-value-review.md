# 训练提交测试价值与 CI 重复审计

日期：2026-11-15。固定产品基线为 `75285e3271bb93271eaea050ca7812cb0cd98b5a`。这是独立只读发现审计，不是 c2 产品审查、CI 终核或删除测试的实施记录。

## 结论与范围

没有证据支持删除本次检查中的整项预算、来源、恢复或后代回收测试；六个 Linux 分组也没有重复登记。发现两个可独立处理的小动作：P2 将 40 个已经不支持 Windows 的 case 提前跳过，避免先构造训练原件；P3 删除一条复制产品完整报错文字的断言，保留真实 malformed stopped 场景及其状态、进程和恢复断言。没有发现需要中断后继产品片的 P0／P1 问题。

审计阅读了根、源码、测试与脚本的 `AGENTS.md`、当前 `docs/PLAN.md`、组件变更协议、活动片交付与相关产品调用，并应用 `ergora-codebase-quality` 的 `test-seams.md`／`repository-style.md`。重点是 `test_training_submission.py`、九个 `training_*` fixture、架构边界测试、CI runner／分组／实际 workflow；相邻训练、登记、reference 与服务接缝用于判断替代保护是否存在。

开始审计时工作树只有后继文档；期间 c2 开始实施。27 个固定来源均以基线 Git blob 为准；审计汇总原件记录的比较时刻只有 `processes.py` 与基线不同，后续出现的其他 c2 工作树修改也全部排除。本报告不评价 c2 的新能力、记录、实现或验收，也不要求按文件长度拆分现有模块。v3 的 kernel 专家路径保留。

## 可执行发现

### P2：Windows 已跳过的 40 个 case 仍先构造完整训练夹具

证据：[`service`](../../tests/test_training_submission.py)（基线 L40）依赖 `prepared`，在函数体内才判断 `sys.platform != 'linux'`。因此 pytest 必须先完成 `prepared → experiments → registration`，然后才执行 skip。`registration` 会创建 Git 仓库并执行两次 Git 命令（[`test_registrations.py`](../../tests/test_registrations.py)，L25）；`experiments` 随后发布登记、写 baseline、runner、两组 manifest／spec／job／结果；`prepared` 再删除 job 并重写来源。静态展开得到 25 个使用 `service` 的函数、39 个参数化 case。另一个 [`test_original_prepared_start_is_readable_and_fenceable_but_cannot_dispatch`](../../tests/test_training_submission.py)（L128）在测试体内跳过，也已经完成 `prepared`，共 40 个 case。这些 case 在 Windows 不运行训练行为，却至少先执行 80 次夹具中的 Git 初始化／提交命令。

最小动作：在收集／setup 的平台条件阶段标记这 25 个函数及上述单独函数，让它们在训练夹具初始化之前保持原 skip 结果；复用文件中现有 `skipif` 写法，不新增 job 或 CI 文件。保留 Linux 的所有节点、参数、预算、故障注入和断言。不能对整个文件加 Linux-only 标记：[`test_local_submission_inspection_does_not_require_the_optional_sdk`](../../tests/test_training_submission.py)（L188）和 [`test_submission_read_racing_with_conflict_publication_keeps_valid_checkpoints`](../../tests/test_training_submission.py)（L1331）仍有 Windows 只读／竞态保护。该文件共 69 个展开 case，现有 27 个已经有提前平台标记。

风险由哪个接缝保留：原 40 个 Linux 原生场景继续在 Linux group 5 运行；Windows 上它们原本就是 skip，提前 skip 不减少已运行的业务保护；两个可移植场景继续在 Windows 原生回归运行。最小验证是比较固定前后两平台的 nodeid／结果集合，并确认 Windows 的这 40 个节点不再进入 `registration`／`experiments`／`prepared` setup。使用现有 `phases.jsonl` 记录 setup，不增加专门镜像实现的测试。

限制：这是已证实的无效 setup 工作，尚未测得 Windows 的节省秒数。现有 own CI 缓存没有逐项 JUnit／phase 原件，不能把该 run 的 1418 秒总回归归因于这 40 次 setup，亦不能承诺收益。

### P3：不完整 stopped 的断言固定了整句内部报错

证据：[`test_budget_phase_interruption_preserves_the_original_fence_without_claiming_executor_stop`](../../tests/test_training_submission.py)（基线 L903）将 `monitor['reason']` 与 `Training phase stopped frame has no complete process observation` 完整相等比较；文字直接复制 [`_BudgetPhase.receive`](../../src/ergora/reference_training_budget.py)（L119）的 `ValueError`。调整诊断文字会使测试失败，尽管拒绝不完整 process 观察、保持 unknown 和不宣称停止的行为全部正确。

最小动作：删除这一个完整文字相等断言；若诊断非空是明确用户合同，可只检查非空，不固定措辞。不要删除 `phase-stopped-incomplete` 参数或把它改成 isolated parser helper。

风险由哪个接缝保留：同一真实 fixture 已先调用原 `processes.run` 完成回收，再写 `.incomplete-stopped` marker 并返回 `{}`；测试读取 marker、核精确 supervisor 身份停止、要求 `monitor.status == 'unknown'` 且 `monitor.stopped is False`，并通过原 `resume_start` 核同 fence SHA、无 executor stop 确认与原件不改写（同测试 L872）。这些断言能揭露错误接受缺损 stopped 的静默错误，不依赖报错句子。实施后只需原参数的精准回归；不以删除这一断言作为重跑全部 24 项或全库的理由。

## 原 24 项的成本与必须保留的接缝

直接读取了 c1 r2 已有安装回归的 request、stdout 与 JUnit：24 passed／80 deselected／495.27 秒，外层 496.327 秒。JUnit 的 24 个 testcase 合计 494.614 秒，其中下表 19 个预算／phase case 为 483.361 秒；另外 5 项为 11.253 秒。该命令只在 r2 SDK 非 editable 安装运行这一次选择，不是 core／SDK 两套各跑同一 495 秒。下表耗时是原件观察，不是本次新运行或优化收益。

|现有接缝（基线 `tests/test_training_submission.py`）|case／JUnit 秒|实际区分的风险与保留理由|
|---|---:|---|
|final 文件／目录发布阻塞，L521|2／64.929|pending 文件未完成与 rename 后目录未持久是不同状态；公开 owner 分别 unknown／fenced，均须只恢复既有同 fence，并保持单 start。|
|start 先返回、稍后禁止 native create，L546|1／19.125|自动 fence 必须独立于已返回的客户端；同时核 producer queue、原 attempt 与授权不变。|
|held start，L579|1／22.744|RPC 仍被持有时 owner 必须到截止并建立 fence；前项的已返回调用不能暴露这个失败。|
|managed create／单 slot，L603|1／28.219|真实预算 adapter 放行 live owner，重复 start／resume 与其他 cycle 不能改原 intent。|
|owner SIGKILL，L628|1／14.767|无自动 fence 的死亡 owner 不能被重启或由新 attempt 接管；正常 deadline 不是替代。|
|原生完成／大 final，L658|1／19.589|保留接近旧上界的 gate summary；phase 元数据不能使合法结果丢失，也不能误 fence／cancel 已完成 job。|
|monitor 阻塞／fence fsync 失败／阻塞，L707|3／64.434|观察超时、已发生的持久化错误与仍阻塞的持久化分别覆盖返回、等待和可见 fence 的恢复。相同 unknown 不代表相同路径。|
|registry 锁耗尽 cleanup，L731|1／21.565|拿不到原生锁时不能声称已创建 fence；前组已经可见 fence 的场景不能覆盖它。|
|lost ack＋授权暂缺，L747|1／26.294|独立 cleanup 与人工恢复可能交错，但只能对账原 run，不能续发或新建 managed job。|
|双 phase／setsid 后代，L810|1／28.351|同一父进程真实交错轮询；monitor 收尾不能误杀处在 fsync 中的 peer，父不能成为共享 subreaper。|
|总截止＋TERM 中的延迟 reap，L825|1／28.810|安全回收跨过总截止仍须完成，记录真实 overrun，不能起新 fence／final。普通及时退出不能代替。|
|完整大输入／held reader，L854|2／59.615|一项须完整传输超过 PIPE 容量的 Unicode 数据；另一项 reader 不读取时仍必须到截止。只测其中一项会漏短写或阻塞。|
|结果读取阻塞／S 强杀／stopped 缺损，L872|3／84.919|分别处于已确认回收后的观察、缺少回收帧、伪不完整帧；原 fence 恢复、精确 PID 停止和不得声明 executor stop 均继续保留。|

另外 5 项分别检查完整 cycle SHA、ready 目录持久失败、授权原来源／冲突、真实 budget worker bootstrap 和服务显式启动。预算 fixture 使用真实 detached owner、专用 S、原 helper 与进程回收，只替换离线 SDK 服务和指定故障叶；`training_cancellation_client` 的导入为 cleanup 安装真实 SDK signal／history 替身，不能按“相同导入／相同末态”删除。

实际调用链是 `training_cycles.start → training.start → _Submission.dispatch → ensure_owner → BudgetedStart.own`；owner 仍串行运行 monitor／fence／cleanup／publish，各 phase 的 `start/poll/finish` 监管专用 S，S 调用原 `processes.run(supervised=True)` 并在回收后发 stopped。`resume_start` 根据原 attempt 只对账原 run；原来源读取、clock、native 最后 lookup 准入和可见 fence 持久恢复分属不同边界。因此不建议把这些集成回归替换成复制内部状态的 helper 测试，也不建议因为相近名称或约 495 秒成本合并参数。

历史 5182bfa 的两项 final 等待失败仍属于原候选；75bc99d 已将观察等待改为实际授权剩余时间加回收余量。75285e3 的原 JUnit 两项已过，本次没有复现失败，也未发现其当前重复。前片约 497 秒和 c1 约 495 秒属于不同产品候选，不是同一候选的无变化重复执行。

## CI 与架构约束

[`linux-groups.json`](../../scripts/ci/linux-groups.json) 的六组共 85 个文件、85 个唯一分配，所有固定基线 `tests/test_*.py` 均有分组；没有重复文件或漏项。实际 [`pytest_phases.py`](../../scripts/ci/pytest_phases.py)（L38）按文件分配，并拒绝重复、缺失和未登记文件。实际 [`run.py`](../../scripts/ci/run.py)（L23）在 Linux 才添加 portable／AdapterTests／runtime；Windows 是应用全库加 reference contracts，不能把矩阵外观相似当作 Linux-only runtime 重复。

读取已有官方 REST／HTML 捕获中固定 [own CI 43676697981](https://github.com/626619403/Ergora/actions/runs/43676697981)／attempt 1 的步骤时间：

|原生回归步骤|原件秒数|
|---|---:|
|Linux groups 0／1／2／3／4／5|299／293／202／223／206／693|
|Windows Python 3.12，group all|1418|
|Windows PowerShell 5.1 安装与升级|56|

Windows 原生应用、Windows Job／编码／路径、离线 archive reader 与 PowerShell 安装器有各自真实入口；Linux 的训练 native、flock、subreaper 和 setsid 回收不能替代它们。PowerShell 与 Bash 安装用不同实际脚本，不是相同产品测试的重复矩阵。现有 Windows 原始逐项 JUnit／`phases.jsonl` 不在本地捕获范围，因此只记录步骤级耗时；下一次需要归因时先消费 workflow 已上传的观察件，不先新增 CI job、扩矩阵或调高超时。仅重排 Linux group 5 也不能据此声称降低该 run 的总体关键路径，因为 Windows 更长。

`reference verify` 在每份安装上核实际包完整性；[`test_public_reference_identity`](../../tests/test_reference.py)（L12）还固定冻结的 283 文件合同，CLI verify 本身只核 manifest 所列内容，不固定数量。两者有接近的调用，但没有证据支持删掉唯一的冻结数量保护。producer／bootstrap 两处固定 budget queue 则独立检查请求和 worker；只彼此比较当前常量会漏掉两端一起漂移。

[`test_architecture_boundaries.py`](../../tests/test_architecture_boundaries.py) 的四类约束也不是同一断言：拓扑无环不能排除无环的 foundation→application 反向依赖；foundation 白名单／stdlib 限制不能排除任意 application 导入 CLI／web；entry-point 限制不能阻止非 boundary owner 直接导入冻结 reference internals。前次 budget_clock 合法依赖的历史声明失败已经有独立修正，不能把它作为当前应删除边界检查的证据。本次没有建议扩大白名单或锁定另一份有效配置。

## 已做检查、限制和下一小片

本次只执行 Git／文件读取、24 份固定 Python 来源的 AST parse、JSON／JUnit 解析、分组唯一与完整性检查、源码与固定 Git blob 摘要比对；没有运行 pytest、安装依赖、启动服务、修改产品／测试／CI、commit／push 或外部写入。唯一公开新增为本报告。

审计汇总原件为 `.ergora/checks/training-managed-execution/test-value-audit/static-audit-r1.json`，SHA256 `66eff755f8900a69300f30f3392f734075956f65a04fae383b8f3d63546c11b3`。它固定 27 个来源摘要、39 个 service case、单独的 body-skip case、全部 24 项原 JUnit 时长和 own CI 步骤时间；原 JUnit 与 request／stdout 仍在 `.ergora/checks/training-phase-lifecycle/installed-regression-r2.*`，own CI 原 REST 在该片 `product-audit/ci-publication-r1/20261115T045152740523Z-jobs-api.json`。

下一可执行小片：独立实施 P2 的提前平台标记，保持 69 个原 nodeid 和 Linux 行为，比较 Windows／Linux 收集与 setup；P3 可作为同一测试维护片的一行断言清理，精准验证 `phase-stopped-incomplete`，不删除其故障参数。先记录实际 Windows setup 节省，再决定是否还有值得处理的瓶颈。c2 产品与其新增恢复／后代回收保护继续按原计划独立验收，本发现审计不代替它们。
