# c1b0：有界普通准备操作独立产品审查

日期：2026-11-15。审查者：fresh-context 独立 reviewer `training_cycle_prepare_product_audit`。项目及文档归属均为 Ergora。本次先读原合同、实际 diff 与相邻调用链，再读实现叙述；遵循根／源码／测试 `AGENTS.md`、[组件协议](../architecture/component-change-protocols.md)、`maintainable-project-delivery` independent-review 及 `ergora-codebase-quality` 的 ownership／style／test-seams references。仅写本报告，未改产品、测试或依赖，未安装、提交、推送或运行昂贵回归。

## 两轴结论

|轴|本地结论|开放 finding|
|---|---|---|
|需求正确性|approve|0|
|结构维护性|approve|0|

在本片已批准的单次内部准备操作范围内，无需产品修正。它把原 `prepare_controller` 接到原异步 S-H 生命周期，给普通操作固定一次原 compute∩control 窗口；准备只产生原不可变意图元数据，不消耗 start／launch slot，不赋予训练或发布权限。本地源码、最终安装、core 实际调用、自身原模板及已知 actor 收尾证据已齐。

本结论不批准跨进程恢复、SDK 总投递／对账、独立 cycle 服务、normal／stop Worker 配额、总 Workflow、后继候选派发、公开入口、真实 CPU 两轮或 GPU／ML 质量及收益。未做固定提交或远端 CI 终核；普通发布仍受前片准确 CI 与原独立终核约束。

## 精确审查范围

基线及审查时 HEAD：`d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，分支 `refactor/architecture-foundations`。最终未提交范围为以下 9 份文件；本报告在原 scope 中明确排除，不形成递归审查：

- `docs/PLAN.md`
- `docs/architecture/current.md`
- `docs/plans/2026-11-15-training-cycle-prepare-operation.md`
- `docs/delivery/2026-11-15-training-cycle-prepare-operation-plan-review.md`
- `docs/delivery/2026-11-15-training-cycle-prepare-operation.md`
- `src/ergora/reference_training_worker.py`
- `src/ergora/training_execution_protocol.py`
- `tests/fixtures/training_cycle_operations.py`
- `tests/test_training_submission.py`

完整字节数及 SHA 在私有证据 `.ergora/checks/training-cycle-prepare-operation/review-scope-r2.json`，其 SHA256 为 `72964916cce8c8d4929327a8a1a38ceb177c07b46dd93b3a515fe46db1499b68`。独立重算 9 份 live 文件与 `review-scope-r2/` 快照全部相同，实际 tracked diff 与 `review-tracked-r2.diff` 逐字相同，后者 SHA256 为 `7b43e52dbec95130f62647a82357fcf1d8defd43c722467e655438be7866f89f`。r1 到 r2 仅更新完成状态文档，产品及最终测试身份未变。

|实际产品／测试|最终 SHA256|
|---|---|
|`reference_training_worker.py`|`5be969dcec98322d086a789d538d89855f7dcaf24e67d5626e9772e4e4197f11`|
|`training_execution_protocol.py`|`29dee8e9fa2f883df3935d0fababe47f7a2e783f3c169a7cf88380481f5ddbf7`|
|`tests/fixtures/training_cycle_operations.py`|`2ce6e6fbcd968e100bb41b16590489c2dfdeb730043195ecc5ae01f1502dd5cd`|
|`tests/test_training_submission.py`|`adc2760f65fac10f2d98877582fc90debe055e00fe4a1406b9b498e9044ccd5b`|

原始需求依据为[具体控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[父计划](../plans/2026-11-15-training-cycle-workflow.md)及[本片范围](../plans/2026-11-15-training-cycle-prepare-operation.md)。另读原 `training_cycles.prepare_controller`／status／publisher、`budget_clock`、`processes.run`／subreaper、原 stop caller、原取消与人工 release 接缝及当前安装配置；设计审查通过仅作为范围依据，未当作产品批准。

## 需求和生命周期核对

1. [worker](../../src/ergora/reference_training_worker.py) 39–46 行在 spawn 前创建窗口，取原 compute remaining 与配置 control timeout 的较小值，并再次限制到原 compute 的 BOOT 绝对上界。较早采样的 ticks 加较后采样的 remaining 使窗口保守；不会延长原授权。计算已尽时允许保存过去的截止，原 `_run` 会在 spawn 前返回 unknown。没有新增时钟、恢复入口或可变当前轮状态。
2. [protocol](../../src/ergora/training_execution_protocol.py) 232–260 行将普通窗口绑定原 parent／authorization boot、原 clock 起点、control 跨度及 compute 上界。每次 remaining 同时消费固定窗口和原 `budget_clock.remaining(..., cleanup_seconds)`，因此仍核 UTC／BOOT 连续性。cold inspect 保留原 1–60 秒观察窗口；四个原 stop／观察模式仍用原 total，不借普通 prepare 的 control 截止剥夺 cleanup reserve。
3. 父 `_CycleOperation` 仍只做 clock／精确进程身份与四个异步 pipe／wait task。S 的 `stop_requested`、H 前后 `active()`、父结果接收后的最后检查消费同一 payload／窗口。H 先核磁盘完整原 snapshot，再调用原 `training_cycles.prepare_controller(State(home), ...)`，因此 State、SQLite、锁、fsync 与意图发布均在被监管 H 内。H 或 S 的结果读取阻塞仍由原 `processes.run(supervised=True)` 及匹配 stopped 帧的原父侧规则处理；未建立第二 driver 或 reaper。
4. 取消路径未改：owned task／spawn handle 受 shield 保留，调用者取消先请求原停止并等真实回收，再重抛 `CancelledError`。新增 prepare 模式共享该生命周期；现有 spawn／helper 取消回归实际运行的是原 inspect 接缝，不冒称已单独运行 prepare 的取消矩阵。
5. H 在原准备前后检查活动窗口，父侧也拒绝出界结果。超时可以留下已发布 intent；只返回 unknown 并保留原件。原 c1a1 准备 owner 仍负责 ready、revision、stop、无覆盖发布及幂等，不把 `prepared` 或路径当执行许可。没有 attempt／receipt／候选执行分支；六阶段、出生同意、单次 start／launch、候选证据权威、人工 release 和 v3 kernel 专家资源均保持。

## 结构、guard 和测试价值

只有原 protocol／worker 两个产品 owner 改动，无新产品文件、公共 helper、依赖、schema、source-key、preset 或 CI 分组。调用链是既有 `_CycleOperation` → 原 S／H → 原 `training_cycles.prepare_controller`；新增业务分支留在其原编排 owner，磁盘格式与发布算法没有复制。

|新增判断|可达失败与责任边界|
|---|---|
|模式登记及只为 prepare 接受 bootstrap|区分普通 compute∩control 与原 stop total；防止停止请求带入另一截止语义|
|窗口完整字段、boot、起点、整数、跨度及 compute 上界|进程封套是输入边界；伪造、损坏或扩张窗口可静默延长普通操作，须在进入 S／H 前拒绝|
|窗口 clock 及每次原 compute remaining|窗口仍有效时，原 UTC／BOOT 可能变化或原 compute 更早耗尽；静态校验无法替代当前观察|
|准备前后 `active()`|等待 State／SQLite／fsync 可跨过截止；防止晚完成的元数据操作被当成有效准备结果|

这些判断分别保护输入身份、当前 clock 和资源生命周期，无实证冗余 guard。过去的 deadline 不强制要求正跨度，是耗尽后不 spawn 的有效内部状态，已有实际接缝覆盖。

三个新增测试／四个运行 case 复用原测试文件及 fixture，分别覆盖真实准备与原 inode／bytes 幂等、封套扩张拒绝、H 数据库阻塞／control 先到、S stopped 后结果读取阻塞／compute 先到，以及 compute 已尽不 spawn 而 stop 仍能使用原 reserve。对两个阻塞 case，心跳必须在 marker 所指进程仍活且原窗口仍有效时记录，能区别事后响应与实际同 loop 并行；marker 改成 pending+rename 避免测试读到半份 JSON。配置选择服务于两种边界先后，窗口预期取自传入 policy／clock，没有把产品有效配置锁到默认值。原共享取消、子后代回收、stop-total 及架构接缝已复用，无需再复制同一矩阵。

## 实际证据与独立终核

证据均位于 `.ergora/checks/training-cycle-prepare-operation/`，结果只认证各自范围。

|证据|已核事实及限制|
|---|---|
|`source-r1.json/.stdout/.xml`|24 passed／60.55 秒，外层 61.443 秒；原 before／after SHA 相同。当前对比仅 fixture marker 发布字节不同，原源码结果仍归旧 fixture SHA `0f31ef090b78f97193d0c1359e2eb80a26e1b0795506965e27df866d935c331c`|
|`package-r1-core.json`／`package-r1-sdk.json`|新非 editable wheel SHA `a288e8cc6f3c27da1edbd2fa91b8ba74e16b446ec07b4853085e34f82a2ddd1c`；独立遍历两套各 652 份 source／wheel／site 文件，集合及每份字节／SHA 全相同；相对基线只变 protocol／worker|
|reference／dependency 原件|两安装均为原 283／PASS，原 source zip SHA 保持；依赖检查 exit 0。core 无 temporalio，SDK 为配置固定的 1.34.0；未将 core 可用性混为 SDK 服务验收|
|`installed-r1.json/.stdout/.xml`|新 SDK venv 的 `-I -B` 命令实际运行最终 `installed-tests-final-r2`；33 passed／156.96 秒，外层 158.013 秒；JUnit 33、failures/errors/skips 均 0。覆盖本片及相关原准备 clock、完整 binding、双 owner 停止、完成证据／人工 release、SDK-free 历史与架构；不是全仓回归或真实训练|
|`installed-tests-final-r2-inputs.json`|178 份测试／示例独立对照 live／冻结副本，全部字节及 SHA 同一；清单 SHA `d9b1d861676157d5cf872f7e8300cc0a35abfbf89318235c04f9e0272f1d3a7f`|
|`core-ordinary-r1.py/.json`|实际无 SDK core 安装异步 S-H prepare 1.157 秒通过；父 State／SQLite／原业务 reader 被禁止，H 仍完成幂等准备；5 原 cycle 文件、DB rows、原窗口不变。已读完整 probe，补丁仅作用于父，子进程实际重入原 owner|
|`self-review-r1.json`／`self-review-r1-codex/original-result.json`|原 `ergora-structure-review` 模板 Codex 26.433 秒 approve；结果 SHA `467df427da525f53ea2553f2b7edb677d1cc96ec6a025b0d9dd3cc0f171573dd` 实算相同。16 份完整文件 456,339B、完整 diff 及 3 原资源均在同一 480,578B stdin；prompt／stdin／记录 SHA 匹配。它仅审所供文本、使用已授权 Codex fallback，不代替本独立原件审查或宣称后端多样性|
|`integrity-cleanup-r1.json`|独立重新扫描原 source／installed 工作目录的 JSON 与 marker，得到相同 22 个记录身份，其中 3 个是旧历史 synthetic 身份；按 PID＋start_ticks＋boot_id 重新读 `/proc`，活匹配 0，未跳过坏 JSON。健康 S 的退出及阻塞 H／独立 session 后代回收另由实际原测试断言保护；不扩大为全主机无进程主张|

独立轻量检查还包括四份变更 Python AST、`git diff --check`、实际调用搜索、最终 scope／diff 比对及文档链接原件。未重新安装或重复耗时回归。最终记录把源码、marker 修正、最终安装、自身文本审查与独立产品批准分列，未将设计批准、未完成服务或另一候选 CI 充作本片验收。

后继可据本地两轴结果固定本片，再沿父计划实施 SDK 原 attempt／唯一 start／receipt 对账与真实服务边界；恢复同一 operation 必须携原窗口并另验，不能通过重建 `_CycleOperation` 续其 control 截止。
