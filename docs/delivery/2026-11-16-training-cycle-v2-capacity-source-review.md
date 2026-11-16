# M6-V2b 完整 SDK 容量接缝：独立源码审查

2026-11-16。审查者为 fresh-context 独立 agent `training_v2_capacity_source_review`。先读原要求、已审合同与完整差异，再读作者交付；未继承实施对话。产品只读，唯一写入为本报告。

**需求符合性：approve；可维护性：approve；本次受审范围内无阻断 finding，亦无必须修正项。** 结论限定为 closed 容量源码及已到达的本地 SDK 接缝，不代表完整 M1c-V/R、真实 Temporal 或 CPU 训练验收通过。

## 准确受审身份

- 基线：`c540939d3b3f38f3851b0de965c9cd0f969eea77`，含已接纳 V2a。
- 固定候选：`.ergora/worktrees/training-cycle-v2-capacity-fixed-r1`，HEAD `919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`；读取时干净。
- 完整差异为 `impl-r1/freeze-r2/source.patch`，SHA256 `622a2ba0065162dc9839cc1d4c19048b372e2127bee9c9d433785e634dde49ab`；五个变更文件，无 untracked。逐文件 SHA 均与 `freeze-r2/summary.json` 相同。
- 唯一生产变更：`src/ergora/reference_training_worker.py`，SHA256 `1fb235e141ce196d45e7c6ccdc95d04c4ed10c47dcff54335f00ef1fd0fd7044`。另四文件为 `tests/fixtures/training_cycle_operations.py`、`tests/test_training_cycle_controller.py`、`tests/test_training_runtime.py`、`tests/test_training_submission.py`。
- 权威合同：[实施清单](../plans/2026-11-16-training-cycle-capacity-implementation.md)及其冻结原件 `.ergora/checks/training-cycle-v2-capacity/design-r1/plan.md`，已复核原件 SHA256 `25069beea90535070de5f0691831eee3bcf2fbd1b0a552de9a24194e121956c2`。后加实施状态不冒充原受审字节。

已读根／src／tests AGENTS、PLAN、组件协议、maintainable-project-delivery 及独立审查 brief、ergora-codebase-quality 的 module-design／test-seams／repository-style，并沿原 M6、容量分期和相关 SDK 源码核对。

## 需求审查

以下行号均指上述固定候选的 `src/ergora/reference_training_worker.py`。

|合同与可达情景|源码和实证判断|
|---|---|
|新 dispatch 的完整 input／Memo 两次边界|1463–1472 使用同一 client 的 Workflow serialization context；复用 1755–1763 的完整 `Payloads.ByteSize()`，Memo 则量含原全部 key、value、metadata 的完整 protobuf。1505 在 claim 前量度，1517 在 claim／fsync 后再量度；1518–1519 随后执行原 final-ready／remaining。1491 的既有 attempt 和 reconcile 路径不重新编码或占机会。容量异常在 1533–1537 返回观察，不删除 attempt、不补 receipt／rejection、不换 ID 或再发送。|
|编码仍消耗原窗口|1457–1458 的原 timeout 未重开；claim 前编码后再核 remaining，最终编码完成后才执行 final-ready／remaining。新增阻塞测试保留原 4 秒 H 窗口及真实进程收尾，没有增加编码预算。|
|默认完整 Failure 树之后整体替换|51–70 的框架 converter 持有独立 `DefaultFailureConverter`，先由默认实现递归形成完整树，再量 `Failure.ByteSize()`。递归不会返回本片边界而逐 cause 缩小。超界时 Clear 整棵 proto，写固定 type/message 与 non_retryable，无 stack/cause/details/raw；小 Failure 及解码仍委托默认实现。|
|v3 wrapper 即使原错误小也不得外传原文|2598–2656 的固定错误覆盖 request、inspection、operation 与 assembly 失败，封闭为三种 type/message、non_retryable，并 `from None`；原诊断由既有 operation 原件及日志保留。2640 的 SDK cancellation 直接传播，asyncio cancellation 也未被 Exception 捕获；V1 分支保留原错误／cause 行为。|
|V2 派生 client／V1 保持原接线|2697–2710 通过公共 `config()`、`Client(**config)` 和 dataclass `replace` 只替换 failure converter；原 service client 和配置继续复用。V2 normal／stop Worker 与其 v3 activities 共用派生 client；V1 两 Worker 使用原 client。未增加连接、业务许可或调度层。|
|完整 assembled envelope、N32 与 Workflow 出口|原 stop fanout 在 1558–1603 保留 `2+2N` 分支并完成 peer cleanup，2589 才量完整 envelope。V2 的 2165、2181、2216、2380、2410 保留完整 status/request/received/stop/input 边界；2216 在读取 facts 前拒绝超界。新增 SDK command 测试实际观察 query failed response、run fail command、predecessor、signal／stop 和已消耗的三次机会，未改 Workflow 主体推进算法。|

另直接读已安装 **Temporal 1.34.0** 源码：`client/_impl.py:269` 的 start request 对完整 args 编码并填全部 Memo；`worker/_activity.py:347` 起在活动返回后再次形成 result／failure completion；`converter/_failure_converter.py:94`／`:126` 包含 traceback、cause/context、details 和预存 Failure；`worker/_workflow_instance.py:855`／`:2872` 使用绑定 converter 形成 query／run Failure。默认无 codec／external storage 时，`DataConverter.encode_failure` 后续 outbound payload 转换不扩张内容。本片未认证任意 codec、external storage、interceptor／plugin 或 server 后加包装。

## 可维护性审查

变化留在 SDK 编排 owner 内，没有通用 capacity 模块、第二序列化器、账本或 speculative factory。局部 `capacity()` 隐藏同一发送路径两次所需的完整编码义务；新 module-level 类是 SDK／sandbox 所需的 FailureConverter 接口实现，并复用默认转换规则。新分支分别保护外部编码大小、旧版本行为或取消语义，未发现无可达用途的新增控制流。

测试延伸原 fixture 和三个原测试文件。`cycle_sdk_completion` 在 runtime 与 submission 复用，保留真实 `_ActivityWorker` 最终编码，只替 bridge completion 接口；默认 sandbox harness 保留实际 Workflow command。SDK 私有接口的使用限于测试且版本固定，直接观察本片的真实风险。metadata 扩张保持合法原业务 shape；N32 使用真实 S/H 和既有 ref bytes／SHA，没有删分支凑界。没有新增测试框架、CI 分组或产品配置。仓库 pyproject 未要求额外 formatter／type-checker；`git diff --check` 通过。

## 原件核验与实证边界

审查者未重跑 pytest、安装、活动、Workflow、服务或模型。除只读源码／Git／hash／JSON／JUnit 检查外，仅经根知情后用现成 SDK 解释器 `-B` 解析已保存 protobuf，没有调用产品或写回原件。

已核 `.ergora/checks/training-cycle-v2-capacity/impl-r1/` 的实际 argv、JUnit 和身份记录：

- `red-wrapper-r2` 为真实原出口反例；初次 `red-wrapper` 的测试接缝构造失败另留原件，不混作产品反例。
- `dispatch-r1` 为 9 过／52.586 秒；其保存 request 实际 input 为 32767／32768 B、Memo 为 2047／2048 B，只有原一个 input 和 Memo key。最终发送顺序收口后 `final-dispatch` 为 4 个超界节点过／26.185 秒；其全局 `-k` 未运行原 final-admission 节点，不把它记作已重跑。
- `final-runtime` 为 79 过、1 个旧 history 子进程原 10 秒超时；同源码 `replay-r2` 原节点另为 1 过／3.559 秒。原失败未抹去。`core-import` 的无 SDK 导入记录为通过。
- `v3-stop-r2` 的接纳参数 cold 超时，只有超界参数通过；接纳另在 `v3-stop-positive-r3` 原时限 41.672 秒通过。独立解析两场已存 `assembled.json`／`completion.pb`：均 **66 分支**；接纳完整 Payloads **19424 B**；各分支合界但聚合 **37515 B** 的场整体失败，最终 SDK Failure **1205 B**。两 completion SHA 分别为 `b1a3779c4acde60d86150ede854f04727cb3148916d0ab1cfb22f0206f3b7477`、`bc3522b3f24b164ae1ab1a6a00a5ed7c40d3319e1a02c77657849ea6f8a45d29`，与保存 summary 相同。

这些是本地 SDK／service double 与真实本地 S/H 证据。schema2 dispatch 触达共同 H owner；schema3 fixture binding 与独立本地 stop 只用于到达 closed v3 stop，其真实 H effect gate 仍拒绝。**没有真实 V2 dispatch 或 Temporal server Failure 包装通过结论。**

handoff 时根通报：新的非 editable 包 source／wheel／site-packages 同一、core 无 SDK／SDK 1.34／283 参考与依赖核验通过；41 个非 N32 安装定向节点通过／52.85 秒。这些由根运行，本审查未重跑或转授。N32 安装检查首次 runner 的相对 Python 路径在 copied-tests cwd 无法定位，产品进程 0，原 stderr 保留；N32 新安装尚未启动，自身审查模板仍未运行。

安装后续验收及 Ergora 自身审查模板交新 agent 接续，最终状态以[本片交付](2026-11-16-training-cycle-v2-capacity.md)为准。完整 M1c-V/R、各 10MB 晚期 reader、统一最后 gate、真实 Temporal 与 CPU 两候选仍须各自证据；schema3 效果继续关闭。无需产品修正；完成上述独立记账后，根方可按 closed 子片合同接纳。
