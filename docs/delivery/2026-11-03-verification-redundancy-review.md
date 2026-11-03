# 测试、CI 与生产校验的独立成本审查

日期：2026-11-03。结论：**优先减少测试初始化和重复调度，不建议按重复字段、代码行数或测试数量删掉故障反例，也没有确认可直接删除的生产守卫。** 已实测的问题是纯入口校验承担完整任务 fixture 的成本；Windows 跳过顺序、CI 触发策略和测试辅助连接的显式释放另有可落实的改进。

需求符合性：本次已完成约定的只读成本审查，仅写本报告与自己的小型分析证据。可维护性：以下三项中等成本优化及一项低优先级辅助资源修正值得分切片处理；本次成本范围没有当前功能阻塞。本报告不是 F3.4b1 的功能初审或发行验收。

## 身份、范围与证据界限

- 独立审查者使用新上下文，先读仓库 `AGENTS.md` 与实际测试/CI/实现，再读计划、活动记录及 `maintainable-project-delivery` 的 independent-review 和 `review-pr` 指引；没有再派实现者。
- 基线及审查时 HEAD：`d98a62a4c9f6d9d514225f033a3f8dad3de3ca60`，分支 `refactor/architecture-foundations`。起始清单和 tracked diff 由 `.ergora/checks/verification-redundancy-review/baseline.json`、`tracked.diff` 固定。
- 成本探针时点 `tests/test_task_external_status.py` 从起始 287 行增加到 298 行，新增两个原结果保持反例；当时文件 SHA256 为 `a042900756033eeca6000b7aebc72c4af9406ac1957767791b3ad827a9c67660`。当时生产文件与协议夹具的起始 SHA 没有变化。该八文件 aggregate `3559d7de109983d8e1803c4cb92898289b0b4e6ca9cfe80a5c010ab4bf66c8bd` 对应保留的 `source-identity.json`。
- 静态身份记录时间为 **2026-11-03 07:31:39 UTC**，位于自己的 `static-analysis.json`；它记录全部 30 个顶层测试模块、292 个测试函数、CI 与第一方顶层模块 SHA。语义审查重点为任务系列、fixture/原生进程链、安装、参考合同、迁移/恢复及进程边界；其余测试只做 AST/入口和代表性断言抽查，不宣称逐例穷尽。
- F3.4a 的 `7c1fa4…` 非 editable wheel 完整 Linux 回归确为 **591 passed / 19 skipped / 36 subtests、1801.14 秒**，wrapper 退出 0、1801.779 秒；精确 CI `41589227955` 两 OS 成功。直接核过指定的原始命令/日志和 CI 状态 JSON。它们属于 `ef8068a…` 的 A 候选，不能证明 B1。
- 收尾期间功能初审另发现孤立 receipt 漏检，实现者将 `files()` 扩为合并 requests/receipts job ID，并新增两个反例及修正零 history 正例。已重读这两文件：现在为 147/313 行，SHA 分别为 `1dd5d118f7530b796123552e8ff12908152435c5fbddaf64da02622ee2c87c49`、`4dc4532a39affbb88f4acb84346493847621c9e3e5023405ce56fe1efe72eca7`，最新 aggregate `85fa8b1dcffadb39bddab760deb8110260ad3e0daa646fafa4d764be90440798` 对应单独的 `final-source-identity.json`。入口 guards、export fixture 与 external_task 初始化未因此变化；成本结论仍适用，但下述通过/计时只绑定原时点，**没有重跑为新候选结果**。
- 成本探针时 B1 有 49 个用例，最新修正增加至 51 个。功能结论由该切片自己的验证和独立审查给出；本审查只执行三个现有成本用例、入口哨兵及内存连接生命周期探针，没有运行全套、构建/安装包、操作用户服务、提交或推送。以下 B1 行号已对齐收尾文件，计时保留原身份。

## 1. 中等：纯入口反例依赖完整任务链，成本已确认

位置：[导出输入测试](../../tests/test_task_export.py) `:183/:190`、[外部状态输入测试](../../tests/test_task_external_status.py) `:260/:262`（探针时 `:245/:247`）、[批准输入测试](../../tests/test_task_approval.py) `:161/:166`、[取消输入测试](../../tests/test_task_cancellation.py) `:162/:167`；共同初始化见 [registration](../../tests/test_registrations.py) `:17/:25`、[creation_project](../../tests/test_task_creation.py) `:19` 和 [export_task](../../tests/test_task_export.py) `:30`。

实际调用为 `installation` 复制参考目录 → `registration` 初始化 Git 与控制库 → `creation_project` 发布注册 → `export_task` 预览、创建、原生提交，再 clone bare repo / mktree / commit-tree → 测试调用。B1 的 `external_task(export_task)` 还构建工作流上下文、请求、回执、产物和 fence。

但 [tasks.py](../../src/ergora/tasks.py) `:100/:229/:258` 在 `_project` / `_native_prepare` 之前就拒绝非法 timeout、缺确认和非法 candidate SHA。以下三例在同一源码身份、既有开发环境中实测：

|用例|setup|call|实际需要的拒绝边界|
|---|---:|---:|---|
|导出 `candidate_sha='abc'`|2.99 秒|0.83 秒|服务入口的完整 SHA 格式|
|导出 `confirm=False`|2.14 秒|0.84 秒|服务入口的严格确认|
|外部查询 `timeout=True`|2.26 秒|小于 0.005 秒|服务入口的严格整数预算|

结果为 **3 passed in 9.26s**；setup 合计 **7.39 秒，约占 80%**。两个导出用例的 call 还含 `status()` 启动的原生只读进程，不能把整段 call 当成格式校验时间。另一个不触达存储的哨兵探针直接调用这三个真实服务函数：均得到原错误，`tasks._project` 调用 **0 次**，单次入口耗时低于 0.1 毫秒。这只是定位成本归属，不能据三个样本承诺整套加速比例。

原始证据：`.ergora/checks/verification-redundancy-review/targeted-cost-probe.json`、`targeted-cost-probe.log`、`early-guard-probe.json`。测试前后五个相关生产/测试文件摘要一致；使用独立临时 fixture，没有连接真实 Temporal 服务。

最小处理：

1. 把这些**纯服务输入**矩阵放入轻量测试，用一个会失败的 `_project` / 持久化入口 spy 证明未到存储或原生调用，保留原错误及严格类型反例。无需新建通用 fixture 框架。
2. 每种命令保留至少一个真实注册/已提交任务上的拒绝集成用例，核对原生文件、journal、租约和 RPC 计数不变；继续保留一个 CLI/API 严格输入与错误映射检查。这样仍覆盖入口接线和真实副作用隔离。
3. **不要移动**“非原始 run”“语法正确但陈旧的 revision”“Git 才能识别的非法分支”等用例：它们必须读取原提交/控制状态或走 `git check-ref-format`，与早期 Python 格式拒绝不同。
4. B1 全部正常/异常用例也经由 `export_task` 创建 Git 候选。`_Inspection.run/files` 实际只读原 outcome 和文件证据，不读取 bare candidate repo；可在后续测试切片让 B1 基于“已提交任务 + 原 outcome 数据”，仅为导出测试保留 clone/commit-tree。先复用已有 `submitted_creation` / `_start` 能力；不要改成各测试手写一套提交 journal。此项可静态确认多做了 Git 工作，**尚未测出它占 B1 总时长多少**。

风险：若把服务函数本身或文件副作用全部 mock 掉，会失去集成保护；若只删除参数案例，会丢掉 Python bool/int、边界值和严格确认故障覆盖。优化应改变这些案例的执行层级。

## 2. 中等：部分 Linux 专用测试在重型依赖之后才跳过

位置：[submitted_creation / native_client](../../tests/test_task_submission.py) `:18/:32`、[export_task](../../tests/test_task_export.py) `:30` 及它们在批准、取消、锁和 B1 测试中的消费者。

`submitted_creation(creation_project)` 在函数体内检查 `sys.platform`；pytest 必须先运行 `creation_project → registration → installation`。`native_client` 的 Linux 跳过也不能撤销此前的注册。用两例 `--setup-plan` 确认的顺序包含 `installation → registration → creation_project → submitted_creation`，B1 则是前面三项后才到 `native_client → export_task → external_task`；**no tests ran in 0.21s**。因此 Windows 上即使最终不执行 Linux 行为，也可能反复复制参考目录、初始化 Git 和发布注册。没有在本次审查运行 Windows，节省秒数未知。

最小处理：给真正只能在 Linux 执行的用例/分组添加收集后、fixture setup 前生效的 `skipif`；先拆出第 1 项的跨平台纯输入测试。保留 `test_submission_requires_the_registered_full_linux_environment`、B1 `test_missing_full_runtime_has_actionable_guidance` 及原生 Windows 编译/WSL 提示等平台合同，不可一刀切跳过整个任务模块。

不要直接把 `installation(scope='module')` 提升为 session：当前消费者会建立或删除 `.venv` symlink、检查缺运行时及身份漂移。`--setup-plan` 也显示跨测试模块会分别建立 module installation；这次复制有隔离作用。需先厘清谁写安装树，再决定是否共享不可变基底；可写文件不能靠硬链接冒充隔离副本。

## 3. 中等：CI 可同时触发两套矩阵，且旧候选不自动取消

位置：[portability.yml](../../.github/workflows/portability.yml) `:3/:5/:6/:12`。

工作流同时监听 `refactor/**` 等分支 push 与所有 pull_request，且没有 concurrency。相同仓库的 PR 分支收到 push 时，两个事件都符合配置，各自构建/安装并运行 Linux + Windows 矩阵；后续 push 也不会取消仍在运行的旧候选。这里确认的是**触发条件和缺少取消机制**，没有查询本分支全部远端运行记录，不能声称最近一次 CI 已实际多跑一倍或已浪费多少 runner 分钟。

最小处理分两步：

1. 先对同一 PR 或同一分支、同一种事件的未完成旧候选设置 concurrency/cancel-in-progress，保留最终候选的必需检查。不要无条件让 push 与 PR 共用同一取消组，防止它们互相取消所需门禁。
2. 若实际运行记录确认 push/PR 经常验证相同树，再明确分工：PR 保留合并结果门禁，非 PR 分支可按需手动预验，主线 push 保留交付回归。需要记录失去的分支提前反馈；不能只按 SHA 相同就取消 PR 的合并验证。

限制：PR checkout 可能是合并结果，push checkout 是分支 HEAD；基线变化时它们能发现不同故障，不能把两者永远视作等价。

## 4. 低：lease 测试辅助函数没有显式关闭 SQLite 连接

位置：[test_task_export.py](../../tests/test_task_export.py) `:90` 的 `lease()`，亦由 B1 多处副作用断言导入使用。`with sqlite3.connect(...) as db` 只管理事务，不调用 `close()`；函数读完返回后，连接资源的释放依赖引用/GC 生命周期。

定向核查提取当前文件的实际 `lease` 函数 AST，仅把其连接替换为内存 SQLite 并保留连接引用以观察。函数返回正确的租约结果后，该连接仍能执行 `SELECT 1`，证明辅助函数没有显式 close；观察后探针自行关闭。原始记录为 `lease-lifecycle-probe.json`，没有查询真实状态库。本探针不证明无观察引用时 GC 会保留多久，也没有测量 Windows 锁、WAL/SHM 或快照波动的实际发生率。

最小处理是对这个只读 helper 用 `contextlib.closing(sqlite3.connect(...))` 或 `try/finally close()`；无需新建数据库抽象。把它纳入测试成本切片，继续保留 lease 与文件快照断言；通过放宽快照去忽略辅助 reader 的副作用会掩盖资源所有权问题。此项是测试辅助生命周期修正，不是本轮产品 finding，也不扩大成全仓连接重构。

## 已确认重复工作、合理的不同层保护与待测成本

|观察|分类与处理|
|---|---|
|CI `:39` 的 `python -m ergora reference verify` 与 `tests/test_reference.py:11` 再调 `reference.verify()`，都遍历同一安装包的 283 文件|hash 核心重复，但 CLI 接线、Python 返回 `files == 283` 以及提前失败诊断各有作用；没有完整重复的测试/步骤可直接删。优先级低，保留现状合理。不能据此删除冻结身份门禁。|
|Windows 安装循环三次 `reference verify`，安装器自身也验证|每次安装/升级后的环境是不同状态，且前者检验实际 launcher，后者检验 venv Python；不是当前主应用 wheel 身份检查的替代品。三次安装分别覆盖 control、research、重复兼容选项，不能只因命令相似删掉。|
|F3.4a 本地完整 wheel 回归与 CI Ubuntu 完整回归相近|历史确有两套完整执行成本，但环境与实际安装过程不同。B1 当前已选择“受影响的安装包定向 + 两 OS 完整 CI”，不再重复 A 的本地完整套件；这是已经采用的减量，不作为待修 finding，也不把 A 当作 B1 通过。|
|源码定向、安装包定向、无 SDK 控制环境、两 OS CI|分别验证快速功能反馈、包内文件/导入、可选依赖边界和平台差异；仍各有必要。内容未变的状态文档提交沿用候选身份，已有 `[skip ci]` 历史表明不必重跑发行。|
|相同创建/状态函数多次调用和整个文件快照断言|在幂等、重试、unknown 恢复、readonly 查询中，重复调用本身是被测试的行为；snapshot 与返回值检查分别证明外部副作用和响应事实。不能合并成一次调用。|
|多处慢连接/其他项目写入测试|提交、批准、取消、导出及 B1 有各自准备/调度入口，能独立回归为持有 DB 写锁；不能只留下一个共用 helper 测试。真实 18 秒探针与快速夹具检测不同预算边界，可采用一个代表性实测，避免无理由做模板全组合。|
|B1 固定 6 页 / 10 次 codec decode 断言|能证明两次查询真实遍历 SDK 分页/codec，但与五事件、每页两条的 fixture 布局绑定，属于易受夹具变化影响的交互断言；不是算法正确性的唯一证明。若更改布局，应以完整 job 集合、连续历史反例及多页/codec 实际经过为合同，别为保持数字修改生产逻辑。|

完整 A 日志没有逐例 durations；不能用 1801 秒反推哪个测试族最贵。建议在下一次**本来就需要执行**的最终 CI/回归中加 `--durations=20`，再决定六阶段矩阵、进程启动或目录复制的优化顺序，不为取得性能列表再跑一遍完整测试。

## 镜像实现与应保留的生产校验

对成本探针时点的 292 个顶层测试函数体做去位置 AST 比较，没有发现完全相同的函数体；这不证明语义上没有重复。重点人工跟踪的 fixture 调用真实创建/提交/协调代码，替换 RPC、模型或安装命令等边界，没有观察到另写 `_Inspection.jobs/files` 算法然后拿它作 oracle 的情况。

有些预期值确实来自生产接口，例如角色矩阵、`DevelopmentWorkflow.context` 和 `sha`；这些测试适合验证生产者/消费者协议一致，不能单独证明合同没有整体漂移。现有固定 `components-v0_2_0.json`、[历史编译摘要](../../tests/test_compatibility_baseline.py) `:71`、严格 JSON 数值向量和外部协议反例提供另一方向的保护，应保留。六阶段 legacy/unified/imported/旧 snapshot 场景也有实际分支差异：旧 snapshot 会删除 `configuration` 后继续运行，统一注册会在 inventory 后改变注册及当前绑定，不能当作相同正常路径删掉。

第一方 `src/ergora/*.py` 的 AST 中没有 Python `assert`；生产校验主要是明确异常/合同检查。检查以下关键边界后，**没有给出删除守卫的建议**：

|边界与位置|不能因为相似而移除的原因|
|---|---|
|[contracts.py](../../src/ergora/contracts.py) `:10/:31`、Web 严格字段及服务入口类型检查|JSON schema、HTTP 输入与 Python 调用的 bool/int、NaN/Inf 和字段错误路径不同；Python 的 `True == 1` 不能代替严格身份。|
|[创建记录校验](../../src/ergora/reference_task_creation.py) `:117/:157/:163` 与初次 compile|恢复读取的是跨进程、可漂移的持久状态；初次编译通过不能证明后续意图/原生文件仍一致。保持 compiled、定义、注册和冻结绑定的关联检查。|
|[document](../../src/ergora/reference_task_creation.py) `:62` 与 [read_raw / safe_file](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py) `:48/:61`|前置 regular-file 检查避免原 reader 对 FIFO 打开时阻塞；fd 上的 fstat、no-follow、目录逃逸与尺寸限制保护不同竞态/输入，不是可任删一个的重复 stat。|
|[原始 spec 验证](../../src/ergora/reference_task_runtime.py) `:40`、[memo 归属](../../src/ergora/reference_task_submission.py) `:166`、[闭合与最新 run / 完整历史](../../src/ergora/reference_task_reconciliation.py) `:29/:106`|本地提交、远端原始输入、控制者归属、当前 run 和完整作业集是不同事实。仅验证部分 run/spec 字段或 describe 的终态不能替代完整历史。第二次 lookup 有查询成本，但承担“仍为最新 run”的检查；本次未建议绕过它。|
|[原 FileAdapter receipt/artifact](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py) `:131/:165` 与 B1 envelope/fence|合法 JSON、正确 job 身份、可信终态、原产物字节与已有 fence 互不等价；目录丢失不得把已知 job 变成零作业确认。|
|[导出 record/load/status 与 Git](../../src/ergora/reference_task_export.py) `:43/:57/:238`|服务入口验证新请求，原生 record 校验还用于磁盘意图恢复。candidate/run/outcome 摘要、原 journal、CAS 分支/符号引用/HEAD、原租约释放保护不同阶段，不能只在服务入口检查一次。|
|[迁移](../../tests/test_state_migrations.py) `:56/:99/:185`、恢复和进程系列|迁移前备份、已打开旧写者、未知未来版本、恢复目标不覆盖、同组后代、Windows Job Object 和控制器死亡分别对应实际失效路径；它们不是普通成功路径的重复断言。|

## 建议落地顺序与验收

1. **先做一个测试成本切片**：纯服务输入矩阵与一个真实副作用拒绝集成检查分层；B1 改用真正需要的已提交任务基底，导出继续走真实 Git；顺手显式关闭已确认的 lease helper 连接。前后案例语义清单保持，并用同一环境少量相同节点的 setup/call 对比验收，不靠删测试数证明优化。
2. **再改平台调度**：提前 skip 真正 Linux 专用用例，跨平台保护继续运行。以 Windows 日志中这些用例不再进入注册 fixture、原生 Windows 门禁仍执行为验收；实测节省时间后再登记收益。
3. **再处理 CI 旧候选**：先加合适的 concurrency，再根据实际 push/PR 记录决定触发分工；最新候选两 OS 完整矩阵仍是验收条件。
4. 保持 B1 当前“本地受影响包定向 + 无 SDK 控制旅程 + 精确两 OS 完整 CI”的安排。源码/测试/依赖改变后重新绑定候选；仅报告变化不重建、不复跑完整发行。本次的三个成本探针不能替代任何功能或发行验收。

证据位置统一为 `.ergora/checks/verification-redundancy-review/`；源码、测试、CI、既有计划和已有交付报告均未被本审查修改。
