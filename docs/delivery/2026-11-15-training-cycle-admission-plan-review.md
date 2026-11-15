# Q4.2c0.2a admission 计划独立两轴审查

日期：2026-11-15。审查者：fresh-context 独立 agent `training_cycle_admission_plan_audit`。直接接收原始要求、baseline、固定完整计划和只读检查边界，未继承作者的实施对话。本次审查的是实施前设计，不认证产品差异或测试结果。

|轴|固定 admission-plan-r1 结论|开放设计 finding|
|---|---|---|
|需求正确性|approve；可继续本片实施准备|0|
|维护性|approve；沿现有 owner 和实际接缝实施|0|

检查范围内未发现新增的 P1／P2／P3 设计问题，也未发现细化与已批准 c0.1 第一、三节的实质冲突。此结论仅放行固定计划；**前置 Q5.2a 自己的 CI 与独立终核闭合后才可实施产品**。没有将原合同批准、CPU 记录、旧候选验收或本次只读检查记为自动循环、真实竞态、GPU／训练质量／收益通过。

## 固定输入与检查范围

HEAD／baseline 为 `e09fd60a635f16e9265b18d1529c4934e687f303`，分支 `refactor/architecture-foundations`。清单 `.ergora/checks/training-cycle-controller/admission-plan-r1/scope.json` 的 SHA256 独立重算为 `6f37c071761ac59bafca9985c5d01baeb5503bad35f731b27c78b373a19f3705`。以下当前全文、冻结副本、清单长度／SHA 均相同：

|文件|字节数|SHA256|
|---|---:|---|
|[admission 计划](../plans/2026-11-15-training-cycle-admission.md)|8,509|`cf256f3443ab2d8bef2016a9eb9e94a2fe83b514284332468ac660dab57c25bf`|
|[具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)|26,550|`42bd4bc177b023149d6d44faf9d43b14ff357df1264b508bef07af672b084133`|
|[控制器准备计划](../plans/2026-11-15-training-cycle-controller.md)|10,086|`df46c8949cd9784e2f0738747df65ff536ce19922672de1663df6e6c46548a77`|

已读根、源码与测试 `AGENTS.md`、活动 [PLAN](../PLAN.md)、[组件变更协议](../architecture/component-change-protocols.md)的配置／持久格式、执行／证据、脚本／检查规则，以及 c0.1 原独立报告的范围与最终设计结论。应用 `maintainable-project-delivery` 的 independent-review、`ergora-codebase-quality` 的 module-design／test-seams／repository-style 和 `codebase-design` 的必要规则。没有重审前片测试修复或重开 c0.1 整体合同。

独立比较 `src/ergora` 的 653 个 tracked 文件（含该目录 `AGENTS.md`，即 652 个产品文件），当前 bytes 与 baseline、`ac86043d9e11983750bf63b90c0dfcbeea05ea41` 均逐字相同；这只是身份核对，不表示逐行动态验收。283 份参考文件逐份匹配现有 reference manifest。`src`／`tests`／`scripts`／`.github`／`pyproject.toml` 相对 baseline 无 tracked 差异。审查前已有三个状态文档差异和未跟踪 admission 计划；未将整个工作树称为空。

## 直接核对与设计判断

|计划位置|真实调用与判断|
|---|---|
|[出生授权与同一算法](../plans/2026-11-15-training-cycle-admission.md#L21)|[`_authorization`](../../src/ergora/training_cycles.py#L218)重建完整 schema1，现 [`authorize`](../../src/ergora/training_cycles.py#L367)在实时检查前永久占 ID、记录原 clock／authorization／cycle，再沿原 ready 发布。局部参数化同一算法、显式 schema2 应用入口、重复操作先核原模式、历史保留原 actor，足以约束旧 ID 升级和丢回复续权；不需要第二授权器或 schema1 迁移。|
|[普通锁与 ready](../plans/2026-11-15-training-cycle-admission.md#L25)|原 [`_record_bytes`](../../src/ergora/training_cycles.py#L273)是临时文件 fsync→link→目录 fsync；[`status`](../../src/ergora/training_cycles.py#L332)沿原外层锁观察 ready 的发布，缺损原件不会重造。新父锁必须在同一出生流程、ready 前持久化；ready 后只开既有普通空文件，与原恢复算法相容。现 [`State.file_lock`](../../src/ergora/state.py#L115)使用 `a+b` 且为排他锁，不能直接充当新父共享许可；计划已选择 protocol 的既有文件读取接缝。|
|[stdlib owner](../plans/2026-11-15-training-cycle-admission.md#L31)|[`_fd`／`read_raw`／`decode`](../../src/ergora/training_execution_protocol.py#L56)已有非阻塞普通文件、symlink／reparse、完整 JSON 接缝；同文件 [`_match`](../../src/ergora/training_execution_protocol.py#L36)和 [`publish`](../../src/ergora/training_execution_protocol.py#L177)确实动态导入 native 包，应用侧不可直接借它们。局部 canonical SHA 可沿原 [`training_cycles._sha`](../../src/ergora/training_cycles.py#L43)与 native [`canonical_sha`](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/contracts.py#L29)的相同编码规则实现。父记录放入已被 pin 的 owner 有真实用途：应用停止，以及后继现有 worker／native gate；不需要新 source key、插件总线或公共通用抽象。|
|[先可见停止与四种事实](../plans/2026-11-15-training-cycle-admission.md#L33)|stop 的目标 `O_EXCL`→写入／文件与目录 fsync→同 raw 重读，明确区别于普通记录的 temp-fsync/link。出现路径即撤销准入，部分／损坏记录不补写、完整重复保留首份 bytes；完整身份、durable、父许可 drained、原子树 stopped 分列。原 [`ExecutionRecords.observe`](../../src/ergora/training_execution_protocol.py#L332)确实要求同步既存链再重读才确认 stopped，父排空不能替代它。没有将新记录能力冒称原 executor 已停。|
|[a5 封住旧 binding](../plans/2026-11-15-training-cycle-admission.md#L14)|原 [`validate_binding`](../../src/ergora/reference_training_budget.py#L32)只允许三个字段，单纯扩 `_load` 接受 schema2 后，普通 [`cycle.start`](../../src/ergora/training_cycles.py#L353)就会将它传给 `training.start`；[`prepare_binding`](../../src/ergora/reference_training_budget.py#L42)再经 `BudgetedStart.require_active` 调用 [`source`](../../src/ergora/reference_training_budget.py#L297)。在 `source` 核 schema／binding 对应是必要的共同关闭条件，也覆盖 dispatch 前 `ensure_owner` 与现 worker 的 `require_active(owner=True)`。本片仍拒绝 schema2 的完整 controller binding，直到 c0.2b 接完来源与最后 gate；没有提前开放无父 gate 的派发。|
|[许可范围与阻塞隔离](../plans/2026-11-15-training-cycle-admission.md#L37)|原 worker [`create_job_if_absent`／`lookup_job`](../../src/ergora/reference_training_worker.py#L26)进入 native [`registry_lock`](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L137)，native callback 经既有 [delta](../../src/ergora/data/native-runtime/training-executor-admission-v1.patch#L16)位于 executor 锁内，应用侧 [`native_main`](../../src/ergora/training_execution_protocol.py#L399)仍调用原 `process`。这些正是后继完整许可的实际接缝。本片低层 flock 不等待，存储用例不进入 live budget owner 或 SDK loop，公开 live stop／独立 fan-out 和全部 gate 明确留 c0.2b，与已批准的两个 worker 进程设计相容；没有复制 executor／reaper。|

## 实施验收与未验范围

现有 [`cycle_selection`](../../tests/test_training_submission.py#L610)、[授权与部分发布检查](../../tests/test_training_submission.py#L1480)、[原服务替身](../../tests/test_training_submission.py#L205)及 [SDK-free 历史档案](../../tests/test_training_submission.py#L41)具有实际复用价值。默认服务替身保留原 `_Submission`／`prepare_binding`／`BudgetedStart.source`，可用于 a5 的未派发负例；其 [budget 故障模式](../../tests/fixtures/training_budget_client.py#L20)另可替换 phase 行为，不能据此认证完整 native 链。该替身也不能证明真实 Temporal、文件持久性或 flock 交错。a1–a5 的必要验收应保留以下可观察关系：

- a1／a2：新旧入口在 ready 前、ready 后及丢回复时均保持原 schema／actor／input／clock；同 ID 跨模式拒绝。真实锁文件或目录 fsync 失败／延迟不得提前 ready；ready 后删除父锁，读／gate 必须拒绝且不重新创建，schema1 不产生该锁。
- a3：在目标文件已出现、首次写入或 file／directory fsync 尚未完成时，由另一进程看到准入拒绝和 durable unknown。重复／并发／重启恢复只同步重读原完整 bytes；部分文件、FIFO、坏身份保持拒绝，不能修补成停止证明。
- a4：真实跨进程多个共享者存活时，drain 无法取得排他许可；stop 可见后新共享者拒绝并释放资源，原共享者退出后才可报告 drained。整个过程保持 `executor_stop_confirmed` unknown，不借原子树停止替代父排空，也不反向取得 registry／executor 锁。
- a5：沿普通 `cycle.start` 和带原三字段 budget 的 `training.start` 验 schema2 被拒绝，未消费 start attempt、未建立新 owner、未发 RPC；另验原 schema1 正常链及可移植历史读取。不要只测新增 schema 判断 helper。

本次实际只做文档／源码阅读、三份固定输入和产品／参考 bytes 核对、diff 与本地链接目标检查；三份计划的 24 个本地链接目标存在，未认证锚点或外部 URL，`git diff --check` 通过。唯一写入为本报告。未运行产品测试、安装包、启动服务、执行 SDK／文件故障竞态、提交／推送或发起网络请求；前置 CI 额度耗尽及其后续状态未由本 reviewer 重新查询或认证。

a6 的最终非 editable 安装、实际回归、自身原审查模板、新的 fresh-context **产品**两轴审查、普通发布与该候选自己的 CI 仍须交付。c0.2b 的最后 gate／fan-out、c1 的实际进程／loop 隔离和总 Workflow、c2 公共交互、新可信 CPU 示例及真实 GPU／业务训练／质量／收益均保持开放。原六阶段、实验／授权／start-slot／attempt／恢复、人工 release、模板／执行／工单／通信的所有权，以及 v3 kernel 专家路径不因这份设计审查改变。

## 固定设计发布 a10e693 补核

同一 reviewer 只读核实普通发布 `a10e69389e228d311df56bad182b9798f4ca236d`，唯一 parent 为上述 e09fd60，tree 为 `2748425c7b6b9331414f6068616133dddcd816fe`。实际差异恰为五份 Markdown：根 PLAN、本片 admission 计划／原报告，以及 Q5.2a 的 delivery／review 状态。五份已发布文件的 blob、长度、SHA256 均与私有 `admission-plan-staged-r1.json` 相同。完整 `admission-plan-staged-r1.diff` 为 36,970B／SHA256 `59c8c8fa6e23d07197dae54b4780130a813585912fb8939b32671f58452c0dca`，与实际 parent→commit 的 binary diff 逐字相同；commit diff-check 通过，清单的 194 个本地引用与实际全文提取一致、目标均存在，未认证锚点或外部 URL。

原 admission 计划 8,509B／`cf256f3443ab2d8bef2016a9eb9e94a2fe83b514284332468ac660dab57c25bf` 仍为完整前缀；仅追加 475B 已发生的设计 approve 状态与原报告身份，发布文件为 8,984B／`91dd6e554627d3696ae6f753f367bd3b78fc9af1b3942fa6dbc38f7e5b17be80`。原报告仍以完整 10,047B／`0088b20d92bedccbb3202d3a367328037259a267298fa45510e696daddc31720` 发布，本节在其后追加。具体合同未改；`src/ergora` tree 与 e09fd60 完全相同，产品／测试／脚本／依赖／CI 无差异，前述 652 产品和 283 参考文件身份不变。

已直接读取 `admission-plan-publication-r1.json` 及 commit／push／ref 的原 stdout、stderr。记录三个命令 exit 0；原普通 push 输出为 `e09fd60..a10e693 HEAD -> refactor/architecture-foundations`，完整 SSH Ref stdout 精确为 a10e693 加该分支，stderr 空。该留存观察时间为 `2026-11-15T07:13:16.856929+00:00`，不是本 reviewer 新查远端。暂存清单为 25,053B／SHA256 `88ae6dfdc1a007016643805709b50ab01e8a39f005251fa3ba4ae0b2ef50d60e`，publication JSON 为 1,015B／`5d5945bb90d32707d3c1edfc2f8e72ce4848d758e0bd48e4ee017f1372a4debc`；ref stdout SHA256 为 `638ddb4064937639462de305feffafd074540a927e452da2332bc6daa3ab07d3`。

**固定设计发布的需求／维护性两轴均 approve，开放 0／0。** 这只确认已审设计、状态同步及留存的普通发布身份。现有 [push 路径过滤](../../.github/workflows/portability.yml#L6)覆盖这五份 Markdown；本轮未查询新 CI，也不称 a10e693 获得新的产品 CI 成功。Q5.2a 的 e09fd60／run43688128824 在途观察仍只归其原 reviewer，本轮不复核其产品或 CI；自己的 CI／独立终核关闭前不放行控制器实施。未新增产品运行、安装、昂贵测试、网络、提交或推送，唯一写入仍为本报告。
