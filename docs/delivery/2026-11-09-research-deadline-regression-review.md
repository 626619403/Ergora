# CR5：研究 HTTP 回归独立审查

日期：2026-11-09。审查者：fresh-context 独立 agent `research_deadline_review`；未继承实现对话。固定基线及审查时 HEAD 均为 `a4cc0b2b54c82ee46ff411f0232823387510de6d`。遵循本仓 AGENTS、maintainable-project-delivery 的独立审查要求及 codebase-design。

## 初审范围与结论

初审直接读取相对基线的完整 tracked diff、`git ls-files --others --exclude-standard` 及唯一未跟踪交付记录。行为变更仅在 `tests/test_research.py`：HTTP 夹具显式释放响应头/重定向正文，原用例以状态和目标请求事实替代整次调用小于 1.8 秒。初审测试 SHA-256 为 `336d3c3db23205949bdaf8e753323d920dadcc98b2203d6d318968cee070b9e1`。另读 `docs/PLAN.md`、AC3c.4 交付/审查追加及 CR5 活动记录；随后新增两份总计划状态记账亦已核差异。生产、依赖和 CI 无变更。

**需求符合性：初审未通过，P2 待修。结构与维护性：所查局部设计未见另一项阻塞。** 重定向信号能直接证明未排空正文，但响应头断言削弱了原有有效 deadline 覆盖，不能以本次普通正例或完全禁用 deadline 的反例通过替代。

### P2 / CR5-1：有效 deadline 被延长三倍仍通过

初审 `tests/test_research.py:182–184` 使用 `timeout=1`，只断言 `timed_out` 和 `elapsed_seconds >= 1`；外层十秒等待是挂起守卫。独立在内存编译原 `research.run`，只将 `deadline = session_started + timeout - elapsed_before` 改成 `deadline = session_started + 3 * timeout - elapsed_before`，其余真实下载、持久化和进程清理均保留，未改任何安装包文件。

同一次定向 pytest 中，新用例在冻结请求仍为一秒、实际终态 `timed_out`、`elapsed_seconds=3.005785522982478` 时通过；基线原用例在 `3.004605125170201` 秒时失败。合计 **1 passed / 1 failed，7.80 秒**。运行前后安装模块 SHA 均为 `8449b65af42f04658383abd598da20b1332797ea7f23689564ecff7f8dbb1b54`。基线测试副本已独立比对 `git show a4cc0b2:tests/test_research.py`，字节相同。

后果：一秒预算变成三秒这一原测试能检出的错误被放过；该断言也未确认服务端已进入响应头处理。最小修正方向是为有效预算保留有意义的检查，排除预算外启动开销；可在真实请求开始后推进仅父控制器使用的逻辑时钟，以原接口观测终态，避免重新引入机器吞吐阈值。实现者已接受 finding，修正与复核在途。

## 维护性、性能与清理

已读 `src/ergora/research.py` 的 `run → _download → _fetch_source`、`state.py` 的连接生命周期及 `windows_job.py`。重定向目标 `/tiny` 的服务端记录加上 succeeded、两字节和最终 URL，能在 `release` 仍未设置时证明目标请求完成；排空正文的客户端没有该路径。HTTPError 显式关闭、不读正文，生产所有权保持原处。

夹具继续复用同一 HTTP server 和已有事件，没有新增生产函数、包装模块、正式调度/账本、依赖或 CI 任务。`finally` 先释放服务端再退出 executor，对本次故障注入可解除等待；`_download` 原 finally 仍 kill/join 并关闭管道，Windows Job 仍拥有子进程集合。独立未运行 Windows，不能以源代码核读代替原生清理验收。

不排空正文应由请求先后事实验证；用整次调用的小于 1.8 秒代替会混入启动和持久化耗时。显式释放夹具适合此处，额外抽取通用测试框架没有实际调用者。本片用例数量与 CI 配置初审均未增加；已有取消、控制器崩溃恢复和快照覆盖继续运行，不需再加同义整套。

## 已核证据与限制

- 独立核原件：受控调用前增加 1.9 秒，基线 **1 failed / 3.69 秒**，修后 **1 passed / 3.65 秒**；这只证实断言混入预算外开销，不证明 Windows 原延迟的具体来源。
- 实现者原非 editable 包的研究回归原件为 **10 passed / 1 skipped，9.08 秒**；跳过项需显式 Temporal 地址。没有将该结果称为独立重跑或全平台通过。
- 独立核两个复制包的实际代码、日志与 JSON 的 SHA：排空正文时新成功断言失败，**11.75 秒**；完全禁用父 deadline/延后 Linux alarm 时 Future 守卫失败，**10.75 秒**。这两项反例不能替代 CR5-1 的预算倍增反例。
- 独立重算源文件、wheel 内文件、实际安装文件三方各 **369** 个对象，与 `r1/package-identities.json` 全部映射一致；wheel SHA 与记录相同。该记录的冻结包为 **283 / PASS**，未改冻结参考文件。
- 独立执行上述单一 deadline 反例，核必要源码/调用者和完整工作区范围；`git diff --check` 通过。没有修改源码/测试/安装包、commit、push、重跑 CI 或运行昂贵整套。

初审阻塞仅 CR5-1。新候选的提交、必要双 OS CI 和精确远端身份尚未发生；原 a4cc 的 CI 42557137619 六项成功、一项 Windows 原生回归失败保持原结果。本报告的任何后续本地通过不改写它。

## R2 修正后复核

**需求符合性：本地通过，CR5-1 关闭。维护性：通过；所查范围无其他阻塞 finding。** 本节取代初审的待修结论，保留原 finding 及其反例。最终测试 SHA-256 为 `878f01b463e991818c4df2710d4b6b849e94695c3d6d5bda7e1eb5a067c9c1e4`。

最终两个用例分别观察响应头 deadline 与重定向正文。响应头用例先等真实服务器 `started`，再将仅父端 `research.time` 属性里的 monotonic 推进到配置的 30 秒预算，要求 `timed_out` 且持久化耗时为 30。标准 time 模块、Event/Future 的外层等待与 spawn 网络子进程保持真实时钟；没有向生产引入新的 clock interface。父端过了预算必须结束，不能由网络子进程的真实 30 秒 alarm 在十秒守卫内替代成功。

独立重做与初审相同的内存三倍 deadline 反例，新响应头用例在 `Future.result(timeout=10)` 处失败，**1 failed / 10.70 秒**，随后正常退出。安装文件 SHA 仍为上文原值，标准 `time.monotonic` 函数对象未变。因此原能实证通过的预算扩张现在能检出，且响应头阶段有实际请求证据。独立对未改安装包运行新两个用例与原响应头取消用例：**3 passed / 1.92 秒**。

复核实现者 R2 原件：研究全套 **11 passed / 1 skipped，8.59 秒**；一项增加来自把原合并用例拆成两个不同的协议行为，没有重复一遍同义断言或增加 CI job。原 1.9 秒预算外开销探针现在 **2 passed / 3.23 秒**。三个复制包 mutant 的实际代码、failure.log 与 JSON SHA 均一致：排空正文 **1 failed / 10.74 秒**，禁用父 deadline/延后子 alarm **1 failed / 10.73 秒**，三倍 deadline **1 failed / 10.72 秒**。独立没有机械重复这些整组故障注入。

两个用例各用自己的 fixture，故响应头异常释放不会使重定向信号提前放行。所有新等待在 `try/finally` 内，释放发生在 executor 退出前；没有在模块级替换真实 time 函数，也没有复用已释放的正文事件。用局部 SimpleNamespace 表达受控父时钟比专设全局夹具或生产注入接口更小，单独用例各自持有状态，维护成本与两个实际行为相称。原取消和控制器崩溃覆盖保持。

最终核对范围为 **8 文件**：`tests/test_research.py`；`docs/PLAN.md`；`docs/plans/2026-11-01-all-in-one.md`；`docs/plans/2026-11-08-agent-composition.md`；AC3c.4 的交付记录与原审查追加；CR5 交付记录与本报告。当前 HEAD 仍为固定基线；没有生产、依赖、workflow 或冻结文件差异。原失败与新候选在计划及交付记录中明确区分。

本片本地需求与结构审查已闭合。尚需新候选自己的普通提交、必要双 OS CI 和精确远端身份；**本审查没有 Windows 原生运行证据**，不预记这些交付门禁通过，也不改写 a4cc 的失败。
