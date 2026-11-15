# B3.1 本地训练预算授权：独立两轴产品审查

日期：2026-11-15。Reviewer：`/root/training_cycle_authorization_audit`，fresh-context 独立上下文。审查只读产品、测试和原件，仅写本报告；未运行 suite、模型、服务、安装、提交或外部写入，未再委派。

## 范围与判定规则

原始要求是持续按计划完成各产品片，每个大项保留自身原审查模板及新独立审查，保持模块深度、解耦、必要 guard 和高价值测试。Kernel 专家保留在 v3 提案路径，不能成为执行授权。完整合同见[本片计划](../plans/2026-11-15-training-budget-executor.md)；此次仅审 B3.1 本地授权／原期限和 task／训练共用时钟，B3.2／B3.3／c／d 不在范围内。

已读根、`src/ergora`、`tests` 的 `AGENTS.md`、当前 `docs/PLAN.md`、组件变更协议，以及 maintainable-project-delivery 的 independent-review brief、ergora-codebase-quality 的三份 references、codebase-design。按真实消费者、持久身份和可达恢复路径评判，不按文件长度或抽象数量评判。

基线为分支 `refactor/architecture-foundations` 的固定 b2 发布 `9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`。r1 完整候选在 ignored `.ergora/checks/training-budget-executor/source-scope-r1/`，配套 `source-scope-r1.json`、`source-scope-r1.diff`；五份文件的实际长度和 SHA256 已逐一读取并与 manifest 相同，包括未跟踪的新 `budget_clock.py`。

|r1 文件|完整字节|SHA256|
|---|---:|---|
|`src/ergora/budget_clock.py`|2875|`6815a8c59dae720823ad10d2426776e0aa27eb0919478c02118ed3856ec622bb`|
|`src/ergora/reference_budget.py`|5110|`1c9209d391586eb6db02e8903d1801405ff12a24dc1e0b84cb6c8dc21861a252`|
|`src/ergora/training_cycles.py`|25176|`79b0006e47ac6b4563428f911f9840a9f2b76c88710640cb210122478431b492`|
|`src/ergora/cli.py`|98834|`2679fbf80e4513d8b958139668f33e8bcb7f17a7b48aaabcb4ea914f076d6649`|
|`tests/test_training_submission.py`|59098|`9771a68450fab0955bf85434a90e1ed9c80dcd782001602d45bb7d9f00c761a6`|

同时读必要的 `training.check_start`／`training._project`、`registrations.published_project` 和其严格原件 reader、`state.file_lock`、`asset_trees.publish_directory`、严格 JSON reader、旧 cycle schema、原 task budget 调用点与仓库配置。当前工作树已继续修改，以下 r1 行号和结论只属于上述固定原件。

## r1 判定

- **需求轴：request-changes，开放 2。** R1 会在首次落盘中断后允许同 ID 重新起算；R2 会在 ready 的目录 fsync 完成前暴露本地 ready。均应在本片闭合前修正。
- **可维护性轴：approve，开放 0，限已读源码范围。** 新 `budget_clock` 有 `reference_budget` 与 `training_cycles` 两个真实生产消费者，只隐藏 UTC／同 boot elapsed／原时刻校验；没有搬入 task scope、slots、训练来源或派发状态。授权和恢复继续由 `training_cycles` 持有，CLI 只解析调用，没有新数据库权威、插件层或单动作转发模块。
- 这不是最终安装、实际 CLI 旅程、自身原模板或发布／CI 的通过结论；这些证据尚待固定并提供。

### R1 — P1：首次目录发布前的清理会丢失已起算身份，同 ID 可重开期限

位置：固定 r1 `src/ergora/training_cycles.py:352`、`:355`、`:363`、`:367`，以及同 ID 判断 `:338`。

可达路径：首次调用在内存起算 clock 后，把原输入和授权写入 `TemporaryDirectory` 管理的 staged 目录；`_record` 已可完成授权文件及 staged 目录 fsync，但最终 `publish_directory` 尚未发生。此时后续 fsync／rename 的 `OSError`、可捕获中断会退出 context 并清掉 staged 原件；强制中断也只留下不按 cycle ID 恢复的随机临时目录。重试只判断最终 `destination.exists()`，最终目录不存在便再次调用 `budget_clock.authorize`。

后果：前一原 clock 和首次 fsync 已消耗的时间不再约束同 ID 的后次调用，违反“中断／fsync／同 ID 不续期”和错误仍保留原记录的合同。该问题发生在首个 live admission 之前，现有“第二个检查失败后恢复”用例无法覆盖。

最小建议：在原 cycle 锁中先持久预留该 ID，使失败后的同 ID 只能读回已保存身份或因缺件明确失败／unknown；不要清理并把它重新变成可首次授权。无覆盖写入原授权、完整原输入及 fsync 仍由现有 owner 持有，不必新建表或通用恢复框架。回归应在首次授权文件／目录 fsync 或发布接缝注入真实 `OSError`，再调用同 ID，证明原 clock 不被替换且不会多次调用时钟授权。

处置：实现方已接受，拟以最终目录的持久预留及原无覆盖文件写入代替一次性 staged 目录发布；缺授权或原输入则拒绝补造／重授。尚未核修后固定候选或运行证据，R1 保持开放。

### R2 — P1：并发只读状态可在 ready 目录 fsync 未完成时返回 ready

位置：固定 r1 `src/ergora/training_cycles.py:283`、`:284`、`:312`、`:315`、`:293`。

可达路径：`_record(ready.json)` 先 `os.link`，再同步父目录。与此同时 `status` 不观察 publisher 的原锁，直接 `_load` 已可见的 `ready.json`；若这次目录 fsync 很慢，它在发布仍未完成且尚未做最终期限复核时便返回 `status=ready`。fsync 随后可耗尽原计算期限，甚至失败。

后果：只读状态把未完成持久化的本地结果当成完成，绕过“完整完成存储后再核截止”的 ready 合同。`coverage.execution_authorized=false` 限制了 B3.1 的执行后果，但不能使此 ready 语义成立。原 r1 的 ready-file-fsync 延迟发生在 link 前，不能保护这个 link 到目录 fsync 的窗口。

最小建议：状态以原锁非阻塞地判断 publisher 是否仍在写；busy 时仍观察原 clock／当前项目并保守返回 pending／exhausted，不能等 live admission，也不能宣称 ready。完整 fsync 后的 publisher 最终复核继续保留。高价值回归是在真实 ready 父目录 fsync 内并发读状态，再跨截止完成，验证读者没有先返回 ready。

处置：该问题由实现方在同片自身检查中发现并通知，reviewer 独立确认固定 r1 路径。工作树拟追加非阻塞原锁观察和 `ready-directory-fsync` 回归；旧 r1 安装实红及修后固定候选尚待核，R2 保持开放。

## 已确认的合同与必要控制

原输入以完整原 bytes SHA 绑定，授权另以 canonical 内容 SHA 绑定；`_decode` 保留原 10,000,000 字节、32 候选与树合同，授权／ready 的 writer 和 reader 同守 1MiB，严格 finite／duplicate-key JSON、ordinary／no-follow 检查位于持久输入 owner。没有用摘要或重新编码替代原 bytes。

`_origin` 沿本 home 的 matching published result 取原 intent SHA，再调用 `registrations.published_project` 核完整 journal；外部 plan 不自行证明来源。初始授权核完整当前项目，完成与状态还核完整项目匹配及原时钟；损坏或缺失来源明确拒绝，不自动迁移。已发布授权的同 ID 恢复用本地原输入，外部路径之后可不存在；live 检查异常后原时钟保留，完整 admission canonical 比较保护原输入身份。跨 boot、倒退或断续时钟返回 unknown，不扩大为训练已经收尾。

ordinary 文件、完整字节、strict JSON、canonical 身份、当前漂移、nonrenewable clock、原 cycle 锁及无覆盖写入均保护真实外部输入／持久／并发失败，不建议删除。新增测试沿原双候选 fixture 和原 suite 检查 lost ack、部分检查恢复、并发同 ID、期限／fsync、来源损坏与只读覆盖，风险可达；现有两处发布窗口仍须补对应接缝。没有发现需为复用虚构新的接口或统一所有账本的理由。

## 已读验证与 pending 证据

- 原 `source-authorization-r1.json`／stdout：七个源码场景通过，pytest 24.71 秒／外层 26.198 秒。该轮后新增父目录 fsync 与跨 boot／倒退时钟观察，因此此通过仅归其当时源码，不转授完整固定 r1 或后继修正。
- 原 `source-task-clock-r1.json`／stdout／stderr：`test_task_budget.py` 与 `test_budget_submission.py` 的源码运行 exit 0，12 passed、3 skipped，pytest 100.94 秒／外层 101.940 秒。三项跳过不能计作通过；实现方说明因未装可选 MCP，待后继 SDK 环境补原 extra 验证。
- 实现方已通知 r1 非 editable 包完成 646 三方／283 参考检查；本轮尚未审其原件，不认证该项。旧安装的新增失败接缝、修后候选 manifest／完整 diff、新非 editable core／SDK 包、固定原测试、实际 CLI 旅程、自身原模板均 pending。
- 未见 B3.2／B3.3 连续 owner、单次 attempt、自动 fence、专用 driver 或后代回收证据；本报告不对这些后继产品、自动循环、真实训练或性能作验收。

下一轮在本报告追加，保留本轮发现、原候选身份、失败与通过范围。修正后只关闭实际核实的问题，最终两轴与剩余证据另记。

## r2 固定候选续审

同片续审，仍为上述独立 reviewer，仅做只读检查和本报告续写。`source-scope-r2/` 五文件实际长度／SHA256 均与同名 manifest 相同；与 r1 比较仅授权 owner 和原测试变化，时钟、task budget、CLI 三文件逐字保持。r2 完整 diff 为 42139 字节／SHA256 `e04feb76e47e079cb47869e4a274befee060c707649125310e58d7174cdc3ed6`。

|变化文件|完整字节|SHA256|
|---|---:|---|
|`src/ergora/training_cycles.py`|25571|`4ba2c4d4ab94d47eabe5d3c9696ca044e08d49b0381cc9d11bf88be0f417006b`|
|`tests/test_training_submission.py`|61345|`36ecba26152276b4c7d74c532437754e4b4c1802f6c5fa1a60a0a85a73819542`|

`installed-tests-r2-scope/` 的 39 份原测试／fixture 已逐份读取并核同名 JSON，包含此 r2 测试全文。它们是固定待运行输入，不是测试通过证据。

### R1 处置复核

r2 `training_cycles.py:372` 在原 cycle 锁内预留正式 ID 目录，`:373` 起同步父层，`:376` 先无覆盖保存授权，`:377` 再保存完整原输入。没有自动清理此目录或已保存原件；再次调用走 `:379` 的原件读取，缺输入／授权会明确失败，无法重入起算分支。原 r1 可达的“授权已持久化但临时目录退出被删除”路径已在源码中修正；计划也记录了这项必要的持久合同修正，没有扩大派发／执行权限。

新增原 suite 的 `test_cycle_interrupted_initial_publication_retains_the_original_id_and_clock` 在真实 `_record` 完成后注入 `OSError` 模拟丢失持久授权确认，检查正式目录和原授权 bytes 保留，再调用同 ID 检查只起算一次、缺原输入不被补造。这是原恢复接缝的有效保护。它没有直接注入底层 fsync 错误，报告应保留这一准确范围。

旧安装实红已读 `installed-initial-publication-red-r1` 的命令 JSON／stdout／XML：pytest 2.87 秒、外层 3.571 秒、1 failed，实际失败为正式目录不存在。源码修正已确认；新安装运行证据尚待提供后才能完成 R1 的运行关闭。

### R2 处置复核：活跃写入窗口修正，但异常释放锁分支仍开放

r2 `training_cycles.py:322` 起核原 lock，`:326` 非阻塞尝试持锁，busy 时以原时钟及当前项目返回不含 ready 的观察，不等待 live admission。新增 `ready-directory-fsync` 在真实目录 fsync 内调用状态，再跨原期限，确实能保护原 r1 活跃 publisher 的窗口。旧安装 `installed-ready-visibility-red-r1` 的命令 JSON／stdout／XML 已读：pytest 3.94 秒、外层 4.772 秒、1 failed，实际失败为并发观察返回 ready 而非 pending。

**仍开放的可达分支：** r2 `training_cycles.py:282` 将 ready link 成功公开后，`:283` 的父目录 fsync 可抛 `OSError` 或被可捕获中断打断；`:284` 的 finally 仅删 temporary，已经可见的 `ready.json` 保留。`authorize` 异常退出释放原锁之后，下一次 `status` 可在 `:326` 取锁成功并由 `:327` 返回 ready；同 ID `authorize` 也可由 `:385` 直接返回它。完成持久化没有成功，而锁已不再 busy，单靠当前锁的占用不能证明该 ready 已完成存储。这仍违反本片要求的失败保持 pending／unknown、完成存储后再核期限的语义。

最小建议：在原 owner 中明确处置“ready 已 link、完成 fsync 失败／取消”后的恢复事实，使下次只读和同 ID 恢复无法把它认证为 ready；继续保留原授权和原期限。补一个在原 ready 父目录 fsync 接缝抛异常、释放锁后再调用 status／同 ID authorize 的回归，检查不报告完成、不重新起算、不覆盖原输入。无需扩展新调度／数据库层。已把此分支反馈实现方，尚未见固定修正或运行证据。

### r2 两轴与证据状态

- **需求轴：request-changes。** R1 的源码修正已确认，运行关闭 pending；R2 活跃窗口已修但 fsync 异常后的完成认证仍开放。没有据此关闭整个 B3.1。
- **可维护性轴：approve，开放 0，限已读 r2 源码。** `_record_bytes` 是本 owner 私有的原 bytes／metadata 两处真实用法，隐藏同一无覆盖写入与 fsync 义务，调用者各自传原容量；没有另建框架或把来源／slots 搬入时钟。新的非阻塞 lock guard 对应真实可达 publisher 窗口。R2 的剩余问题属于未完整实现的持久完成状态，不能靠更多无关 guard 掩盖。
- r1 wheel SHA256 `5be8fdf78085d2e99f7828a51008b56449e4141bad93533430c8476b93a42134`，2037578 字节；本轮只读逐一核 646 份 wheel／core 安装／SDK 安装内容与各 manifest，四产品文件与固定 r1 原件相同。已读原非 editable 安装命令、检查脚本和 reference-r1 两套 283 PASS 记录，未运行服务。此证据仅绑定旧 r1 和其两条实红，不转授 r2。
- r2 的新 core／SDK 包、补装原 MCP extra 后的原 tests、完整适用 suite、实际 CLI 进程旅程、自身原模板和最终固定证据仍 pending。未新增任何产品执行或模型调用。

实现方已接受 R2 的 fsync 异常分支，拟在取得原锁并核原件后，对已有 ready 的原目录实际 fsync；仍失败返回 unknown，成功后重新核完整原件／来源、当前项目和原期限。这个方向可以仅完成原 link 的持久化，不改任何 bytes、checked_at 或 clock，也不需新 receipt／ack；status 的 lock busy 路径仍应立即保守观察，不进入 flush。文档须明确这一目录 flush 的观察行为。该方案尚非已核实现或通过证据，R2 保持开放。

## r4 固定源码与契约复核

已读 `source-scope-r4/`、同名 JSON／完整 diff，并逐份核实际长度／SHA；四产品和原测试都与当前工作树逐字相同。相对 r2 仅 `training_cycles.py` 和原 `test_training_submission.py` 继续变化，原 task budget、纯时钟、CLI 三文件保持上表身份。完整 diff 为 45726 字节／SHA256 `92d04a323ddb2e6d6b8f68971524e900e0e0037f219227da0294c47bebcb7cf5`。

|r4 变化文件|完整字节|SHA256|
|---|---:|---|
|`src/ergora/training_cycles.py`|26663|`5680e198befbb3b3c9c80bf0a011864a994b8a155322ced14b58be072361582f`|
|`tests/test_training_submission.py`|63777|`51e80cf58684ea3034b98ba92028ada2eaeb1ff588b00d4ee18b79c8a27b77a6`|

`installed-tests-r4-scope/` 的 39 份原测试／fixture 逐份与同名 manifest 匹配；manifest 为 6306 字节／SHA256 `98a45897e10e87a6fe5b901dcc31ae5637db72b1335f7b7893167ac771589da9`。这是待运行输入身份，不把它写成运行通过。

### 两条补充实红与 R2 源码处置

已读 `installed-ready-failure-red-r2` 的外层 JSON／stdout／XML：r2 实际安装上 1 failed，pytest 3.81 秒／外层 4.472 秒；失败为 ready 目录 fsync 仍抛错时，锁释放后的状态却返回 ready。已读 `installed-postflush-source-red-r3` 对应原件：r3 实际安装上 1 failed，pytest 4.02 秒／外层 4.872 秒；前半的失败 unknown、原目录 flush 恢复和 bytes 保持通过，后半在 flush 接缝删原 journal 后没有拒绝。两次失败保留各自候选，不能计作 r4 通过。

r4 `training_cycles.py:316` 的私有 `_durable_status` 由只读状态和同 ID 已有 ready 恢复两个原调用使用，只隐藏本 owner 的持久完成义务。`:320` 实际 flush 同一个目录，`:321` 的 `OSError` 返回不含 ready 的 unknown；`:326` 成功 flush 后复用 `_load` 重新核完整原输入、来源 journal／matching published result、授权和 ready，`:327` 钉住原 authorization SHA，最后 `:329` 再核当前完整项目和 UTC／同 boot elapsed 剩余。这个顺序保护慢 flush 期间的来源缺损及身份漂移，未刷新 clock、checked_at 或原 bytes。

`status` 的原 lock busy 路径仍不进入 flush，不等待 live admission。新入口没有 live admission、SDK／服务查询、派发或新授权；原件缺损时明确失败，而非补造。手册和具体计划已说明已有 ready 的目录 flush 及失败 unknown。R1 的正式 ID 预留／缺件拒绝路径继续保持；R1、R2 的源码修正均已确认，没有新的源码阻断发现。

原 suite 新增的 `test_cycle_ready_directory_failure_is_unknown_until_original_publication_is_durable` 保留真正的 fsync 接缝与异常后的原调用顺序，同时检查状态、同 ID 恢复、原 bytes 和 flush 期间丢原 journal。它保护可达的持久／来源风险，不是复述实现；不建议另建 suite 或 receipt 状态层。

### r4 当前两轴与安装身份

- **需求轴源码复核：approve，开放源码 finding 0。** R1／R2 的运行关闭及整片最终验收仍 pending；未凭静态修正认证新测试结果。
- **可维护性轴：approve，开放 0，限已读固定 r4 范围。** 两个真实时钟消费者和训练 owner 职责未改变，必要恢复逻辑留在原 owner；没有引入执行 owner、额外数据库权威或投机复用。
- r4 wheel 为 2037901 字节／SHA256 `c986db854e90bb77c5f4c94ff5ecbc9b72aa526fad9852ae632c61ad2f88bd1d`。本轮逐份只读核 646 份 wheel 内容、core 与 SDK 的真实 `site-packages` 和各 manifest；四产品与固定 r4 源码一致。已读非 editable 安装／检查／依赖命令 exit 0、core 无 SDK／SDK 1.34.0 的 package 记录、SDK 安装原 task-mcp extra 的命令，以及两套 283 reference PASS。未代跑检查或启动 runtime。
- 实现方已启动 r4 安装上的全部 cycle 接缝、实际完整 CLI 和自身原结构模板；本轮尚未接收最终原件。r2 固定 39 文件上的完整三 suite 仍以其原候选记录，不转授为 r4 的整套运行。最终证据到齐前，本段不是整片最终完成结论。

## 最终本地 r4 原件终核

本轮直接读最终原件、固定测试输入、实际 CLI stdout／stderr／原记录和自身模板真实输入／结果后重新判定，不继承上轮源码 approve。最终基线、四产品、原测试、wheel 均保持上述固定 r4 身份；当前五文件再次逐字核同固定副本。源码 manifest SHA256 为 `dfcca3cacf2c56145e68d2392b7deec5cd418d3caa326dc10575956ea62dbee4`；产品源码、wheel、core／SDK 两套实际安装完整 646 文件再次逐份核字节相同，各 manifest 同一，283 reference 原 bytes 保持，安装及依赖记录均通过。

### 最终实际验证范围

|最终 r4 原件|实际结果|原 pytest／XML／外层秒|
|---|---|---|
|`installed-tests-r4`|原 `test_training_submission` 全部 cycle 相关 16 passed，零失败／错误／跳过|56.85／56.844／57.686|
|`installed-clock-r4`|原 task budget／submission 两 suite 15 passed，零失败／错误／跳过|138.20／138.195／139.384|
|`native-journey-r4`|13 个实际 core／SDK CLI，确认／SHA 拒绝、原输入恢复、耗尽与当前项目漂移均有原输出|外层 24.947|
|`native-readback-r4`|4 个最终 core 实际 CLI 重读同批 r2／r4 的两个原授权|外层 2.620|
|`self-review-r4-codex`|自身原结构模板 succeeded／approve，Codex 回退|模型运行 46.167／外层 48.825|

测试命令确用最终非 editable 安装的 `python -I -B` 及固定输入；已核 JSON、stdout／stderr 与 XML，16 个 cycle 测试名包含 R1 和 R2 的活跃写入、目录失败、成功 flush 后来源丢失接缝。新十场景和原六个 cycle 场景均实际执行，没有把 deselected 的 34 项计为通过。

`installed-tests-r4-scope.json` 的 39 文件／SHA 保持上轮身份。`installed-clock-r4-scope.json` 为 16329 字节／SHA256 `41c851832d65c7eed980cdbfb2f4c65266ef9c06e221240daecf12306bc9a6d2`；83 份文件的实际字节、SHA 与执行位均核相同，其中 39 原测试／fixture 与 r4 原 scope 一致，44 份所需 tracked examples 逐份同固定基线。没有改产品 fallback、测试逻辑或断言来修验证环境。

旧 `installed-tests-r2` 仍是 49 passed／15 errors，pytest 321.86 秒／XML 321.842 秒／外层 323.060 秒。XML 的 15 个错误已逐一核均为 fixture setup 阶段缺 `examples` 的 `FileNotFoundError`，与原测试 `EXAMPLES` 真实读取路径一致；该次未运行 task 产品检查不能写成通过。补齐验证输入后仅在最终 r4 重跑受影响 task 两 suite；原 r2 的其他 49 项不转授成 r4 全部三 suite 通过。这个受影响范围与 r4 只改变 cycle 私有持久／状态路径、原 task 提取时钟内容保持一致相符，未见需重复未变化接缝的证据。

### 实际 CLI 与自身模板原件

已核两个 CLI 驱动的真实 argv、每个命令的 stdout／stderr SHA 和返回状态。`native-journey-r4` 原 50 个原生／登记文件当前仍同 before 清单，完整原 cycle bytes 与保存副本及输入 SHA 相同，外部输入目录确已删除；授权、ready 和 clock 在三个成功读取原输出中相同，剩余时间递减。SQLite 当前 dump 仅项目原文的明确 memory binding 和 revision 加一不同，其余 dump 不变；这项操作发生在授权后的主动漂移场景。原拒绝命令返回 2，短预算状态和同 ID 重试保持 exhausted，漂移后返回 project-changed；所有本地覆盖仍为 execution_authorized=false。

`native-readback-r4` 的两 case before／after 清单、各自实际全部 373 文件及只读 SQLite dump 已逐份核相同；四个命令读回的授权分别与 r2／r4 原旅程保存授权相同，短期限不被续期。上述仅证明原件观察，不证明提交、runner、模型、Temporal、训练或停止。

自身原 `ergora-structure-review@1.0.0` 通过既有 `refactoring-quality` 安装后实际调用，run `0e508f3c8b58423b9960cb84ef14821a`。已读完整驱动、25 文件 scope、完整 diff、原 composition／request／task／prompt、真实 stdin、原 backend stdout 和 result／response：25 完整文件共 591938 字节都进入 task，完整 diff 也进入 task；实际 prompt／stdin 均为 673850 字节且相同，三份祖先资源原 text 全部在其中。四产品／原测试的 scope SHA 与固定 r4 相同；完整 input tree digest 独立只读重算为 `a12057161b75681499073d047524088fca338e61b65a7d223ef791c3db4292b3`。原 result SHA 为 `7231af03e1548ffa33d005f081882222b30838ebdb2000b58b1b61870745605a`，原 response 明确 approve 并保留 supplied-text 限制。实际 requested binding 为 Claude、执行 binding 为授权的 Codex 回退；不声明异后端成功，也不将其认证范围扩成它未读的私有原件或 CI。

### R1／R2 关闭与最终判定

- **R1：关闭。** 正式 ID 预留、首次持久失败后原 clock／bytes 保留、同 ID 缺件拒绝与不再次起算的修正，已由最终安装原场景实绿。保留 r1 实红与中间轮待验记录。
- **R2：关闭。** 最终安装实际验证 active publisher 的目录 fsync 可见窗口、link 后目录 fsync 失败的 unknown／同 ID 恢复、成功 flush 后原来源丢失拒绝；源码还在成功 flush 后核原授权 SHA／完整记录并最终观察当前项目和原时钟。没有删除或重写原 ready、刷新 clock 或增加第二 ack 权威；r1／r2／r3 实红保持。
- **需求轴：approve，开放 0。** 完整本地 B3.1 要求及适用安装／恢复证据成立，不因上轮源码结论或旧候选通过自动取得。
- **可维护性轴：approve，开放 0。** 模块深度和实际所有权保持，两个真实消费者只共享时钟算法；来源、持久恢复及必要并发 guard 留在训练 owner，CLI 不持有另一状态机。回归沿原接缝保护真实的期限、身份和持久失败，没有新增无消费者框架、无关 guard、重复 suite 或修改配置来迎合测试。

本结论只关闭 **B3.1 最终本地授权／准入片** 的审查与上述证据，不认证普通发布、远端身份、自己的 CI 或前置 b2 CI。前置报告中的 CI 状态不由本 reviewer 转授；尚未发布的 B3.1 仍需自己的发布与适用 CI 门禁。B3.2／B3.3／Q4.2c／d、连续 owner、attempt／slot、实际 executor／后代停止、真实 Temporal、GPU／训练质量／收益全部保留后继义务。Kernel 专家仍在原 v3 路径，不能成为执行授权。

reviewer 全程未运行 suite、模型、服务、安装或平台操作；只做必要源码／原件读取、SHA／字节／执行位／XML／只读数据库核对及静态 diff 检查。本报告外没有写入。上述限制不是产品未完成项的替代证明。

## 固定本地提交续核：尚未发布

已只读核实际 Git 对象及 `publication-staged-r1.json`／`.diff`、`publication-local-r1.json`，本地普通提交为 `b53bba613a3c02b14c69a6df9b0d526755d7e216`，直接 parent 为 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a`，tree 为 `133df8a95afdb763a00a2300a47fa7b34dbc760f`。该 parent 包含前置 b2 单独处理的原测试 Linux 标记；B3.1 产品实施基线仍是 `9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`。

实际 commit diff 的完整 107650 字节与固定 staged diff 相同，SHA256 为 `46d75cbe45beb2c13c2004f99ca13820fb06ef49146e8096a51ac4917f16cbe0`；11 个变化路径的实际 Git blob OID、字节和 SHA256 逐一同两份 publication 索引，未扩大文件范围。四产品 blob 与最终已审 r4 完全相同；另直接读 commit 全部 646 产品文件，与原 r4 wheel `c986db854e90bb77c5f4c94ff5ecbc9b72aa526fad9852ae632c61ad2f88bd1d` 和 core／SDK 两套实际安装逐份比对相同，包含 283 参考、原 schema／preset 和数据库 owner。

commit 中原 `test_training_submission.py` 为 63882 字节／SHA256 `a9525bac126d3e69608c0c2cba83188d7770da501bfd46306593176a08698ff7`。与固定 r4 的唯一文本差异是 `test_original_registration_is_rechecked_in_the_selected_training_process` 前的一行 Linux `skipif`，去该行后全文逐字相等；该行已在 parent 82ea 存在，本次 B3.1 不再次修改此标记，十个新增场景不变。不借该机械差异重跑未改产品或把前置 CI 转授本片。

已按固定 commit 的文件树独立核六份变化 Markdown 的 178 个本地链接，缺失 0；实际差异静态检查通过。额外 Windows 回归文档变化仅同步前置修复的既有固定身份／在途 CI，没有产品变化或提前终态主张。未跟踪的 B3.2 设计文档不在该 commit，亦没有混入后继代码。

**固定本地提交需求轴 approve／开放 0；可维护性轴 approve／开放 0。** 这绑定上述本地对象与既有最终本地证据，不表示已推送或发布成功。远端完整 Ref、B3.1 自己的适用 CI 均待后续原件；前置 82ea 的 CI `43658729462` 也不在本轮认证范围。此次仅追加本报告，没有测试、模型、安装、提交、推送或平台写入。

## 普通远端发布与自身 CI 续核：已确认失败，尚待整次终态

2026-11-15 UTC 00:58:39 起独立匿名读取官方 GitHub。`publication-remote-r1.txt`／`.json` 中 SSH 完整 Ref 为 `b53bba613a3c02b14c69a6df9b0d526755d7e216 refs/heads/refactor/architecture-foundations`，原 txt SHA256 为 `01f12787e87952f0df5ff1d1733dd89faf05fc509265d1238b81416be0754617`；官方 Ref REST 200、commit HTML 200 和 branch HTML 200 另与同一完整 SHA／原 parent 相符。普通远端身份已确认；该事实不等于自身 CI 通过。

本片自己的 Portability 为 [run 43660736309](https://github.com/626619403/Ergora/actions/runs/43660736309)，run number 226、attempt 1、push，开始于 `2026-11-15T00:57:18Z`。官方 Actions 列表嵌入数据把该 run 明确绑定本片完整 SHA；官方 run HTML、job HTML 与首方 `job_groups_batch?attempt=1&batch=0&size=200` 导航 JSON 相互核对。导航明确 `totalCount=8`／`hasMore=false`，六个 Linux group 和一个 Windows native job 加 plan，没有以单个 matrix 预览替代完整枚举。

### R3：共享时钟的原边界测试未同步，自身 CI 已实红

Linux group 1 job [132649282883](https://github.com/626619403/Ergora/actions/runs/43660736309/job/132649282883) 于 `2026-11-15T01:01:59Z` completed／failure；步骤 6 `Native application regression` failure。官方原 HTML 的注释保留完整失败和统计：

```text
tests/test_architecture_boundaries.py::test_foundations_do_not_depend_on_application_modules[reference_budget-allowed6]
tests/test_architecture_boundaries.py:51: assert local_dependencies[module] <= allowed
AssertionError: assert {'budget_clock'} <= set()
1 failed, 253 passed, 6 skipped, 1801 deselected in 250.96s
```

固定 commit 的 `reference_budget.py` 已按本片设计导入共享 `budget_clock`，而原 `test_architecture_boundaries.py` 的 parametrization 仍把 `reference_budget` 的允许本地依赖设为空，也未单列共享时钟的纯标准库基础边界。已直接读固定两个产品 blob 和原测试确认；这不是下载、安装或 runner 的暂态错误。该 job 的 wheel 构建／安装、packaged reference identity 和 observation 上传均 success。

实现方复现入口为固定 commit、其非 editable wheel 的 `python scripts/ci/run.py --group 1 --output ci-results`；最小选择为 `python -I -B -m pytest -q 'tests/test_architecture_boundaries.py::test_foundations_do_not_depend_on_application_modules[reference_budget-allowed6]'`。reviewer 未执行这些命令。最小修正应同步真实共享时钟依赖并保留其无应用层依赖／仅标准库约束，不能通过删边界断言、跳过或改 CI 选择掩盖失败。已即时向实现方发送精确步骤、原件路径和复现命令。

原件在 `.ergora/checks/training-budget-executor/ci/reviewer-publication-r1/20261115T010451303908Z-job-132649282883-html.html`，结构化摘录为同目录 `failure-observation-r1.json`。匿名步骤 log URL 返回 404，原响应和 headers 已保留；没有认证后取得完整 log／JUnit artifact 的主张。官方 job HTML 本身已明确给出上述断言、位置和 suite 统计。

截至官方 `20261115T010632162645Z-jobs-navigation-api.json`，plan 和 Linux group 0、2、3、4、5 success，group 1 failure，Windows group all 仍 in_progress。因此 **本片自身 CI 门禁当前 request-changes，R3 开放 1；不可写成整片发布验收通过**。此前本地 r4 的限定证据与 R1／R2 处置保持原记录，但不覆盖这条新增失败。继续观察所有 job 与 run 的终态，最终 8 job／30 个必要业务步骤对账和证据索引另追加；本段没有提前宣称终态。

匿名 REST 后续因共享出口 IP 的每小时 60 次额度耗尽而返回 403／remaining 0，原响应／headers 同样保留。此后用无需认证的官方 HTML 和首方导航 JSON 继续观察，不把 REST 错误写成成功。前置 `82ea3f163e0c29759eb6ebef93fb2e58d87e983a` 的 run `43658729462`／attempt 1 成功，仅是实施方及其原 reviewer 的独立前置证据，绝不转授本片。此次只追加本报告和授权的忽略审计证据，没有运行产品、测试、模型、安装或平台写入。

## 自身 CI 最终终核：failure，R3 保持开放

已从 UTC `2026-11-15T00:58:39.179314Z` 持续低频观察至 `2026-11-15T01:27:26.139338Z`，覆盖整次终态。限流重置后的官方匿名 REST 恢复 200，明确本片完整 SHA `b53bba613a3c02b14c69a6df9b0d526755d7e216`、Portability run `43660736309`、number 226、attempt 1、push；最终 `status=completed`、`conclusion=failure`、`updated_at=2026-11-15T01:25:45Z`。官方总 HTML 显示 Failure，与最终首方导航、attempt jobs REST 和八份最新 job HTML 全部一致。此轮没有取消原 run 或用后继运行代替它。

|实际 job|Job ID|最终结论|
|---|---:|---|
|plan|132649252951|success|
|Native Ubuntu 3.11 group 0|132649282871|success|
|Native Ubuntu 3.11 group 1|132649282883|failure|
|Native Ubuntu 3.11 group 2|132649282852|success|
|Native Ubuntu 3.11 group 3|132649282901|success|
|Native Ubuntu 3.11 group 4|132649282881|success|
|Native Ubuntu 3.11 group 5|132649282870|success|
|Native Windows 3.12 group all|132649282859|failure|

最终 **8 job 全部终态，6 success／2 failure；30 个必要业务步骤完整出现一次，28 success／2 failure**。30 项取自固定 commit 的实际 workflow：plan 读分组 1 项，七个 native 各构建安装、参考身份、原生回归、上传 4 项，以及 Windows PowerShell 1 项。固定 workflow SHA256 为 `be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`；原分组配置为 `b50d95a1954d6e2612183feccc7b5a764c9109c479997dec7fe628127b55981e`。逐项对比 REST 和 HTML，名称、job 身份、状态及每个必要步骤的结论一致；所有非空 HTML log URL 钉住本片完整 SHA 和各自 job ID。

两项失败都是 `Native application regression`，且都只列同一条 R3：`test_foundations_do_not_depend_on_application_modules[reference_budget-allowed6]` 的 `{'budget_clock'} <= set()`。Linux group 1 为 **1 failed／253 passed／6 skipped／1801 deselected，250.96 秒**。Windows 为 **1 failed／1175 passed／830 skipped／16 subtests passed，1562.36 秒**；官方 annotations REST 200 与最终 job HTML 均保留该原输出。不能把其中跳过项、subtest 或 deselected 项合并成普通测试通过数。

Windows 原生回归于 `01:24:39Z` failure 后，PowerShell 5.1 安装升级实际继续执行并于 `01:25:40Z` success，结果上传于 `01:25:41Z` success，job 收尾于 `01:25:43Z`。七个 native 的构建安装、参考身份、上传均成功。六个 Linux PowerShell 步骤依原 workflow 条件 skipped；另外两个失败 job 的 setup-python post 步骤 skipped，均不在上述 30 项之内。其余基础步骤没有失败。没有第二条失败测试或把 Windows 的最终安装升级结果误报为在途。

终态后 `01:27:24Z` 另抓官方 branch／commit HTML，两个 branch `refInfo.currentOid` 仍为完整本片 SHA，commit OID 和唯一 parent `82ea3f163e0c29759eb6ebef93fb2e58d87e983a` 亦相符；其后才通知实现方原 run 已终态，可以继续既有授权内的独立修复发布。该时点远端身份原件保留，不依赖后续 branch 是否前进。

### 最终证据索引与判定

授权忽略目录 `.ergora/checks/training-budget-executor/ci/reviewer-publication-r1/` 已保留原始 HTTP bodies、headers／时间／状态／SHA 元数据、固定 workflow／分组、逐字复制的实施方发布输入，以及只读审计 helper 和结构化核对。`capture-integrity-r1.json` 核全 **80 份原始响应** 字节与 SHA 相同：71 个 HTTP 200、7 个 HTTP 403、2 个 HTTP 404；错误响应也保留，没有删除限流或不可取得原件的记录。`terminal-summary-r1.json` 记录完整 8 job／30 步骤交叉对比，`final-remote-identity-r1.json` 记录终态后远端身份。

`evidence-index-r1.json` 索引自身以外的 **142 文件／10117940 字节**；索引为 **25421 字节**，SHA256 **`a7d98b4eb257c0ce1bd3583eefab8de05ab4ae685e93050aafe12f1ccece6c84`**。原完整 log／可下载 workflow artifact 没有取得，不把官方页面／annotations 的原输出扩称完整 JUnit 或全部日志审计。

**普通远端身份已确认；本片自身 CI 终态 failure；本片发布验收需求轴 request-changes，R3 开放 1。** 原本地 r4 的 R1／R2 已关闭和产品可维护性 approve 保持原候选、原证据及原范围，不能覆盖新发现的边界测试合同遗漏。实现方已准备独立小修复，交由另一 reviewer 核对；本 reviewer 未核其修后候选或运行，R3 不在此旧固定 SHA 上关闭。修复应有自己的固定身份、审查和适用 CI，前置成功及未来成功均不转授本次失败。

最终仅追加本报告及授权的忽略审计证据，没有修改产品、测试、其他文档或 B3.2 在途内容；没有执行 suite、模型、安装、服务、提交、推送或平台写入。B3.2／B3.3 和实际执行／停止／训练的后继义务仍保持上述界限。
