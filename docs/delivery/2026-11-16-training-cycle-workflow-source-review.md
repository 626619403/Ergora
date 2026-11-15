# c1c 首轮 TrainingCycleWorkflow 独立源码审查

日期：2026-11-16。Reviewer：fresh-context `/root/cycle_workflow_source_review`。范围仅为 ordinal0 正式 Workflow 源码，不认证测量接受、ordinal1、公共入口、新安装、真实 server/native 或官方 CI。

**当前 r4 源码结论：需求 approve／可维护性 approve，开放 finding 0／0。R1／R2 已按原反例修复并复核；这是源码层结论，全片实际验收仍由主控分别闭合。** 下文保留 r3 原发现及末节 r4 的准确修正／验证身份。

## 输入与结论

先读根／src／tests AGENTS、主 PLAN、[原具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[首轮详细要求](../plans/2026-11-16-training-cycle-workflow-first-round.md)、组件协议及 maintainable-project-delivery 独立审查 brief、ergora-codebase-quality 的 module-design／test-seams／repository-style。随后完整阅读候选差异及相关 producer／caller，最后才读[实施交付](2026-11-16-training-cycle-workflow-first-round.md)。没有继承实施对话或预设结论。

源码基线为 `c52fc0a338118a19491ad7cd458b82cf2f146a9b`；审查候选为 `fa78747d6c6ca62935fe6a44aa6db143c362baad` 加 r3 未提交修补。主仓库 ignored `cw1/candidate-r3.diff` 完整覆盖基线至工作候选，SHA256 `b88c3cd52cc5d910fa74bf960d73e8bd8e07284b43c6c442244ac9dc7a02fa03`；`freeze-r3.json` SHA256 `d376670d2b5aa554afddb06b976ecc2c2ee45a4b8ab430b729a1bf976d8e079e`。两项均实际重算。

|文件|r3 raw SHA256|
|---|---|
|`src/ergora/reference_training_worker.py`|`bbe0f58860847be48b7ffea3df01d9e7cc4430d65c8686e01bbd5e2949e594ce`|
|`tests/test_training_runtime.py`|`469d8b754784d5caa3ce4dab565c0d5a9a66d73b5e4475072ad5af6bd06c1838`|

**r3 历史结论：源码需求 request changes，R1／R2 当时开放；源码可维护性 approve，无另立的结构性 finding。** 此维护性结论未解除需求修正或全片验收门禁。两个缺口均可在现有 owner／既有测试接缝内修复，不需要新模块、ABC 或重建调度器。

## Findings

### R1 — 中：终点分支绕过结果收窄后的预算／history guard

位置：[worker](../../src/ergora/reference_training_worker.py) r3 第1453–1460、1526–1538行。

`_consume` 可能将 `D_work` 收窄到当前 history 时间之前，或本次活动完成事件使 history 达到阈值。但 `_next` 先接受首轮终点，直到后面的 positive 分支才调用 `_guard`；run 又在其后 guard 之前直接返回。因此恰好携带成功终点的那份观察可以跳过统一停止出口。

使用现有真实默认 sandbox activation fixture 的小型只读驱动已复现：cold 在 A=0 返回 work=9、total=30，R=1；ordinary observe 在 A=2 调度，原 SDK timeout=7；其合法最终 facts 给 work=1、total=20，并在 R=4 处理。新界应为 `D_work=min(9,2+1)=3`，已耗尽，但实际得到 `FIRST_ROUND_OBSERVED / first_round_observed_c1d_required`、`complete_workflow_execution`，stop 数量0。结果处理仍在原活动 timeout 内，故不依赖违反 SDK 超时的注入。原文明确要求正常预算尽、观察／history 容量界进入同一停止出口；此时 total 仍正，可排一次 stop。相同排序也让终点结果绕过 count／history 阈值检查。

最小修正：认证并消费结果后，先检查统一 guard，再决定首轮终点；保留已经存在的停止意图。现有 activation 接缝增加“终点结果自身缩尽 work／达到 history 界”的回归即可，无需扩大服务矩阵。正常未耗尽终点仍须保留人工 release 窗口且不额外停止旧轮。

### R2 — 低：SDK 参数解码绕过非法 signal 的 typed 拒绝记录

位置：[worker](../../src/ergora/reference_training_worker.py) r3 第1228行 `request_stop(self, request: dict)`。

对于已进入 history 的合法 JSON 非对象值，例如 `[]`，SDK 1.34.0 先按 `dict` 类型提示解码。其 `_process_signal_job` 捕获参数解码失败、记录日志并丢弃 signal，根本不进入 handler。因此 handler 的 shape catch 无法设置约定的 `last_signal_rejection`。小型真实 sandbox 驱动 `start → signal([]) → query` 返回 `last_signal_rejection=None`；之后合法 signal 仍能处理。没有发现该路径重授执行权或毒化 Workflow Task，但 query 的约定拒绝观察缺失。

最小修正：signal 入口接受未提前强制成 dict 的值，由已有严格 validator 在 handler 内拥有 shape 拒绝；在现有 signal rejection 测试加入一个非对象顶层值，并核 typed rejection 及随后合法 stop。无需修改 wire、SDK 或业务授权。

## 结构、兼容与检查范围

新类留在原 source-pin worker owner，框架 run/query/signal 和唯一 `_serve_cycle` 工厂 caller 都有实际用途。私有方法隐藏编码、command 前计数／一次机会、认证投影、绝对截止和停止 handle 生命周期；没有发现要求再拆一个 manager／backend 的实际调用证据。原六阶段、native 最后 gate、唯一 root/reaper、执行记录和人工 release 仍归原 owner。nested 模板／可替换后端及继承资源／权限收窄不在本片改动中，未被本类另行实现或绕过。

沿实际 `_serve_cycle → create_cycle_activities → S/H → _execution_candidate_operation`、submission 状态、runtime 固定 run 观察以及 protocol validator 核过：start/request 标记在 command 前消耗、attempt 最大1，丢 completion 不重授；v1 仅收窄 total；A+remaining 只缩不延；null request facts 修补不创建 work；未知身份／source／clock 不授新效果；双 QUEUED 与 Binding/job 同时就绪才 request；native/reap/phase 分开；stop 独立 queue，ordinary 未完成时先发取消请求并排 stop，重复取消由 shield 保留唯一 handle；旧 stop 的 durable/drain/executor 字段维持 null。未见 accepted／rounds／ordinal1 或旧轮 Temporal cancel 路径。可选 SDK 缺失只捕获顶层缺包，坏依赖继续传播；normal 增正式类而原 budget 入口和 stop 独立槽保持。

实际读了 `result-r3.json`、stdout／stderr、JUnit和 `w0-source-r1.json`：r3 为源码导入、真实 SDK 1.34.0 默认 sandbox 与离线 activation **21 passed／3.32秒**，853项冻结前后相同；其中 activity facts、history size/length 为注入值，4项旧 service lifecycle 不是实际 Temporal 服务验收。core 无 SDK 导入／显式工厂拒绝和坏 SDK 依赖传播分别已有真实解释器证据。审查者没有重跑 suite；仅运行上述两个小型纯 SDK activation 复现、只读 Git／SHA 和 diff-check，未安装、启动服务、模型、训练、网络或修改产品／测试。

审查后段观察到实施者开始增加回归，工作测试文件已变为另一个 SHA；本报告 r3 的完整范围以最初核实的冻结 diff 和上述两个 raw 身份为准，未将后来工作测试冒记为 r3。后继候选须重新冻结并复核。

新 wheel/core／SDK 安装身份、正式 Worker 真实注册、真实 server history／Replayer／重启、丢回复原件链、真实 stop/native/reaper 收尾、真实 history 阈值及官方 CI 均未由本审查验证。根任务仍须分别记录 W0–W10 实际证据；本报告不将未完成验收当作源码已通过，也不把这些外部缺项另造成本片结构性 finding。

## r4 修正与独立复核

同一 reviewer 在原源码审查后接收明确的 r4 冻结复核任务。HEAD 仍为 `fa78747d6c6ca62935fe6a44aa6db143c362baad`，基线仍为 c52，两项产品／测试仍是未提交修改。实际重算主仓库 ignored `cw1/candidate-r4.diff` SHA256=`edc532693b2eadfeb73f49dfe3b9520591fb7d65974bba00da3efa5e302700e6`、`freeze-r4.json` SHA256=`1a28aa876840e0373665b3e492a589ca7752c0839fe655d255235cde1dcf2899`，工作文件分别为：

|文件|r4 raw SHA256|
|---|---|
|`src/ergora/reference_training_worker.py`|`187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`|
|`tests/test_training_runtime.py`|`56f67f74aadbe8a0db53fd3ea7df22f9b2865327c104d8533871753e29c1e6a1`|

完整 r3／r4 diff 比较确认：源码只把统一 `_guard` 移至 `_next` 开头、删除 positive 中的后置重复调用，以及移除 signal 的 `dict` 类型提示；测试只增加终点 guard 的4个参数节点及原 signal 拒绝例中的顶层 `[]`。未扩大 owner／wire／授权范围。相对 c52 的完整 diff-check 通过，复核前后两个 raw SHA 都保持上述 r4 身份。

- **R1 关闭。** `result-r4-before.json`／stdout／JUnit 核实原 r3 worker raw `bbe0f…` 上 work、history-events、history-bytes、ordinary-count 四参数均实际失败，失败均为终点已完成且 stop 数0。修后 guard 在任何终点判断之前执行；测试消费新样本后再核工作截止、8000 events／8MiB、256次边界，并核一次独立 stop 和 needs_reconciliation。原正常首轮测试仍要求无 stop，防止把未越界终点一并改坏。审查者另用原 R1 的小型 SDK activation 驱动复核 A=2、w=1、R=4：当前 phase=STOPPING、独立 stop 数1、timeout=18（`min(30,2+20)-4`），没有先完成 Workflow，也没有续 total。
- **R2 关闭。** `result-r4-r2-before.json`／stdout／JUnit 核实同一原 r3 worker 上新增 `[]` 断言失败，并包含 SDK 参数解码后 dropping signal 的原日志。移除入口类型提示后仍由既有 strict validator 拒绝。审查者另用真实默认 sandbox 驱动复核 `signal([])` 得 `signal_identity_or_shape_rejected`，随后合法 signal 保留完整 reason 并仅排一次 stop，不发 start。

修后 `result-r4.json`／stdout／stderr／JUnit 实际为 **25 passed／3.85秒**、完整 runner5.21秒、冻结前后相同、完整 diff 未变；相比 r3 新增4个 guard 参数节点，原 signal 节点原地增强。reviewer 读取了 before／after 原件和 JUnit，不重跑已完成 suite，仅做上述两个小型纯 SDK activation 复核，没有产品／测试／配置编辑、安装、服务、训练、网络或 Git mutation；两个信号驱动产生的 originating-event-ID=0 提示属于离线 fixture 的明确 history 注入边界，不是实际 server 验收。

**r4 源码需求 approve；源码可维护性 approve；R1／R2 关闭，无新增 finding。** 默认 sandbox／注入 facts 与 history 的离线检查、新 wheel 身份、实际正式服务／原件链、Replayer／重启／真实阈值、资源收尾及准确 CI 必须各自记账。本复核未验证新的安装／真实 server/native 结果，不以无现场否定已核源码修正，也不以源码 approve 认证全片 W0–W10 已完成。测量接受、ordinal1、公共接口及训练／GPU质量继续在本片范围之外。
