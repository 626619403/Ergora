# M6-V2b：完整 SDK 容量接缝独立设计审查

2026-11-16。Reviewer：fresh-context 独立代理 `training_v2_capacity_design_review`，未参与方案编写或产品实现。按 maintainable-project-delivery 的 independent-review brief 和 ergora-codebase-quality 的 module-design／test-seams 审查；先读原始合同与当前源码，再读作者实施清单。唯一写入为本报告。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|**approve，仅限 closed V2b 静态实施设计**|0|
|结构／维护性|**approve，仅限 closed V2b 静态实施设计**|0|

在下述实际读取范围内，未发现需要修改方案的可达缺陷。批准的是原 owner 上的 SDK 容量接缝与验证安排，不是产品实现、安装、真实 Temporal 服务或完整 M1c-V 通过；schema3 效果、ordinal1、真实训练／设计和 CPU 两轮均继续关闭。V2a 的许可／服务生命周期结果保留各自准确身份，没有转授本片。

## 要求、身份与检查对象

原始要求是持续交付多后端组合工作流和真实训练的有界循环，同时保留原 baseline／candidate、全部原结果、身份、失败／unknown、恢复、原预算和独立审查。本片只细化下一完整的 closed SDK 容量实现：不开放效果、不改 V2a 的四 poller／两业务许可和生命周期，不增加执行或持久状态 owner，也不靠重复 tests／assertions／CI 替代真实接缝。

主树分支为 `refactor/architecture-foundations`；基线与审查时 HEAD 均为 `c540939d3b3f38f3851b0de965c9cd0f969eea77`。根报告给出的 V2a 产品为 `82c6595907b4d2173890b82e6fcb6ab8920832b1`；本审没有重验它的安装／原模板结果。读取了根、src、tests AGENTS、当前 PLAN 及组件协议的执行／证据和脚本／检查分支。

|实际读取原件|独立核得的 raw SHA256|
|---|---|
|[V2b 实施清单](../plans/2026-11-16-training-cycle-capacity-implementation.md)，与 `.ergora/checks/training-cycle-v2-capacity/design-r1/plan.md` 逐字相同|`25069beea90535070de5f0691831eee3bcf2fbd1b0a552de9a24194e121956c2`|
|[M6 原合同](../plans/2026-11-16-training-cycle-v2-runtime.md)，重点 M1c-V/R|`c228041efb586f3f0e929e20695106d779ca56b4d2ce544d27f67d457bd305da`|
|[容量分期](../plans/2026-11-16-training-cycle-measurement-capacity.md)|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|[M6 独立设计终审](2026-11-16-training-cycle-v2-runtime-design-review.md)|`10f7903803a83da5e07fcbdc30863965d8b62e6d8cfde602e849f310f7518415`|
|`src/ergora/reference_training_worker.py`|`932159e3e5ad25095327e2cc0d205c84d96abbd9a7a743895c391eae6c4196a4`|
|`src/ergora/reference_training_runtime.py`|`b8ed226f24c54a16f292a23567c5e36b47fd165b3922ac331bc8083570c9fd70`|
|`src/ergora/training_execution_protocol.py`|`573366d01ed271ddd544235cf16886faa2d569f3870e079808b64d40e441d073`|

另读 `training_cycles._controller_ready/_claim_controller/_record_controller`、原 `perf_temporal.connection.connect`，以及现有 `tests/test_training_runtime.py`、`test_training_cycle_controller.py`、`test_training_submission.py` 和两个指定 S/H／service fixtures 的相关接缝。以上产品与测试文件相对 HEAD 无差异。进入时已有他人的 PLAN／交付文档差异及未跟踪报告／计划，未覆盖或纳入本片产品结论。

SDK 仅静态读取 `.ergora/checks/training-cycle-v2-runtime/package-r3/venv-r3-sdk/lib/python3.12/site-packages/temporalio` 及其 METADATA，版本为 **1.34.0**；未 import SDK。所读包括 client `_client.py/_impl.py`，converter `_failure_converter.py/_data_converter.py`，worker `_activity.py/_workflow.py/_workflow_instance.py`，默认 sandbox runner／in-sandbox 和 bridge `worker.encode_completion`。这是可读安装的能力调查，不是本片新安装验收。

## 需求审查

|审查点|源码事实与方案判断|
|---|---|
|完整 input／Memo 与原发送机会|当前 worker `_dispatch_controller:1397` 在原 permission 内 lookup、claim、fsync 后重验 ready，再 send；确实还没有完整 `Payloads`／`Memo` gate。方案第13行把两次完整计量放在 claim 前及同步后的最终 send gate；第42行要求真实 H／attempt／SDK request 反例。原 claim 不返还、没有新 receipt／ID，编码继续消耗同一 remaining/window，符合原合同。现有 schema2 接缝可验证这一共同 owner，但不能据此称真实 V2 dispatch 已运行。|
|完整 assembled envelope 与结果保留|当前 `_cycle_capacity:1712` 已计实际 converter 生成的完整 `Payloads`；invoke 在入站及 envelope 全部组装后调用。stop fanout `stop_live_controller:1504` 保留 `2+2N` 分支并在 finally 等待所有 peer。方案第14、43行要求新 v3 N32、混合 refs／inline unknown 与聚合超界到达末次计量，未用单分支大小或删分支冒充完整结果；原 S/H、stdout/raw 和 cleanup 合同保持。|
|固定 wrapper 错误不得泄漏小 raw|当前 invoke 的 `ApplicationError(str(error)) from error`、`inspection['reason']`，以及 execute 的容量异常链，确实可能把正文带到 SDK。方案第15、30、45行要求 v3 wrapper 无论原错误是否超 B，都先映射为封闭固定 type/message、non_retryable，且不携原 cause／details；旧 wrapper 保持。仅在 converter 超界时替换不能满足这一规则，方案没有把两者合并。取消保留原 cleanup，未提出吞掉 BaseException。|
|真实最终 Failure 树|SDK `_activity.py:352–355,457–459` 在函数返回后编码 result／failure；默认 `_failure_converter.py:126–160` 加 traceback、递归 cause/context 并编码 details，已有 FailureError proto 也会 CopyFrom。方案第30行要求委托未经改写的默认 converter 先形成整树，再量 `Failure.ByteSize()`；不能在逐 cause 的递归中提前替换。超界只整体替换为固定小非重试 Failure 并复核，不制造成功。第45行采用真实 Worker completion 出口而非只运行 ActivityEnvironment／helper，能观察本项实际风险。|
|converter 之后的扩张|`DataConverter.encode_failure` 在 `to_failure` 后仍遍历 payload；Workflow 也在 to_failure 后经过 `_workflow.py:499` 和 bridge `encode_completion`。静态读取表明，这些后续变换在当前默认 payload converter、无 codec／external storage 的连接下不再扩张 payload；原 `perf_temporal.connection.connect` 确实未配置这些扩展。这里不能推导 core／server 不加 activity-error 包装。方案第34、54行将支持范围及真实 server 完整树验收保留为明确未闭合项，未用本地测量替代。|
|V2 输入、发送、consume 与出口|实际 V2 `_ordinary:2129` 量完整 predecessor request，`_consume:2172` 在读 facts 前量整体；status／signal／run 通过原 converter gate。方案不重写推进算法，并要求从真实 schedule、query、run completion/failure 读 protobuf，consume 拒绝后不退还 start/request/collect 机会、不推进 prefix／ordinal。原 `_cycle_operation:749` 和 `_controller_ready:451` 的 schema3 effect gate 继续关闭。|

SDK 的固定 message 本身不足以证明最终 Failure 合界，这个原审提出的缺口在本方案中有具体公共接缝，而非仅新增一条测试愿望。实现时仍须按方案证明实际类、activities 和两个 V2 Worker 都接到同一派生 client；本设计通过不代替该证明。

## 结构、性能与测试价值

`Client.config()`／`Client(**config)` 是该 SDK 的公共构造接口，配置保留 service_client 和 namespace；替换 DataConverter 的 failure_converter_class 无需建立新连接。保留 V1 原 client、只给 V2 normal/stop 与 v3 activities 使用派生 client，能把新语义限制在准确版本，不需要另造 adapter 工厂。模块级可选 SDK 类留在现有 worker，由 SDK 要求的 converter 协议承担实际最终编码义务；这不是为了单次调用包装一层，也没有理由新增通用 capacity 模块或持久状态。

默认 sandbox 通过 Workflow module 重新导入实际类，真实实例从传入的 `failure_converter_class` 构造 converter；core 当前通过可选 SDK import 保留只读导入。方案第32、46行把模块级类、无 SDK 与默认 sandbox 的受影响检查列为必要验证，未通过关闭 sandbox 或使 core 强依赖 SDK 来回避问题。新增类应按第30行完整委托默认实现；继承后让默认递归重新进入自己的容量替换逻辑不符合所审方案。

新增成本主要是 H 发送前两次完整 protobuf 编码／计量，以及默认 Failure 整树形成后的一次总量计量；没有新的并发分支、服务、业务许可或长期缓存。它不承诺构建原 Failure 的常量内存或实测性能，编码成本仍受原 window 约束。当前没有据此提出额外性能 harness 或重跑 V2a 生命周期矩阵的依据。

测试计划使用现有 owner 接缝，针对可能静默误发、丢分支、错误回收机会、泄漏 raw 或最终编码超界；未新增测试文件／CI job。第38、42、48行允许记录固定合法 shape 的真实可达大小：生产 Memo 目前是一个固定 key 加 SHA，不自然覆盖 2047/2048/2049，因此用 converter 的合法 metadata 到 SDK 出口检查计量，并清楚标注为本地 SDK 边界；不伪造生产 Memo 字段。stop reason 本身是合法可变字段，多字节及相邻界可沿它验证。有效 predecessor/status 的关系仍由原配置和身份导出，不用非法 operations 字段填充或缩短真实路径来宣称合法接纳。这与原测试中已有的非法 envelope 早拒绝情景是不同证据，方案已要求分别到达相应最终 owner。

## Findings、未验范围与后继

本次两轴均无 finding；无需修改本方案后再启动 closed V2b 实现。下列是方案已保留的实施验收门槛，不是本审新增阻断：

- 准确隔离候选的固定 wrapper 错误、两次 dispatch 容量 gate、完整 v3 envelope／V2 command 和最终 Failure 出口，分别记录实际到达的 owner；claim 后拒绝必须保留原 attempt 且无 send。
- 新非 editable wheel 的实际 site-packages、默认 sandbox 与无 SDK 导入，以及受影响旧版本／history；没有变化的 V2a 许可、deadline、shutdown 只引用原身份。
- 真实 Temporal server 保存／返回的 started input/Memo、Failure 及其包装树、signal／query／outcome、N32 全分支，仍由最终候选验收；本地 bridge／service 替身不能关闭完整 M1c-V。
- M1c-R 每个 10MB 晚期 reader、原最后 native／budget／executor gate、统一开放与真实 CPU 两候选顺序 archive／恢复／停止／收尾继续归后继，不据本审宣布训练质量、GPU容量或性能收益通过。

本次执行的只有只读文本、Git、cmp／SHA 和本报告的文档静态检查；未执行 tests、probe、SDK import、replay、安装、模型、服务、网络、训练、提交或推送。没有修改产品、测试、PLAN 或其他报告，也没有重新验证 V2a 原运行库存。
