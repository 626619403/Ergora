# M6-V2b：完整 SDK 容量边界实施清单

2026-11-16。静态实施设计，尚未实现、运行或独审。恢复已核主树 HEAD `c540939d3b3f38f3851b0de965c9cd0f969eea77`，已接纳V2a准确产品 `82c6595907b4d2173890b82e6fcb6ab8920832b1`。已读根／src／tests AGENTS、PLAN、组件协议、maintainable-project-delivery，以及 ergora-codebase-quality 的 module-design／test-seams。权威合同仍是 [M6 的 M1c-V/R](2026-11-16-training-cycle-v2-runtime.md)、其[设计终审](../delivery/2026-11-16-training-cycle-v2-runtime-design-review.md)和[容量分期](2026-11-16-training-cycle-measurement-capacity.md)；本页只细化下一小片。

前置V2a已完成四 poller、两业务许可、等待消耗原 deadline 和正常路径cleanup；源码／新安装／fresh独审／原模板分别闭合并普通合入，详见[其交付](../delivery/2026-11-16-training-cycle-v2-runtime.md)。外部强行终止SDK run仍为incomplete／unknown，不声称可恢复。V2b从上述接纳后的准确产品新建隔离树，不修改原作者／固定树。两片共同触及 worker，但容量片不重做许可、拓扑、服务 shutdown 或 BOOT 窗口。全部 schema3 效果、训练和设计 gate 保持关闭，原预算、输入、历史和诊断原件保持。

## 已核事实与最小产品改动

`B=32_768`，Memo `2_048`，均按最终 protobuf 字节；UTF-8 字符数／JSON 长度不能替代。实际调用链是 services → cycle worker → SDK registered activity → invoke → 原 S/H；controller 则在 H 的 `_dispatch_controller` 内连接原 SDK client。新边界均留在 [reference_training_worker.py](../../src/ergora/reference_training_worker.py)，不增通用 capacity 模块、第二账本或序列化器。

|真实 caller／现状|V2b 的最小责任|
|---|---|
|H `_dispatch_controller` → `client.start_workflow`；目前未量完整 input/Memo|在原新-send 路径、claim 前及 claim/fsync 后的最终 send gate，分别量原六字段 input 的完整 `Payloads` 和原全部 key/value 的完整 `Memo`。复用 `_cycle_capacity` 和 SDK `Memo`，memo 的每个 value 仍用该 client 实际 converter；不能只量 intent SHA。原 lookup/reconcile 不因未发新 command 而重新占机会。最终编码也消耗原 remaining/window，容量失败不能返还已落盘 attempt、补 receipt、换 ID 或再次发送。|
|`create_cycle_activities(..., 2)` → invoke；目前入站和完整 envelope 末尾已有 `_cycle_capacity`|保留两个完整检查，核新 facts/selection/measurement/acceptance、inspection、全部 operations 和 stop 的 `2+2N` 分支确实进入末次计量；不只测每个分支。失败发生在真实 peer cleanup 后，不删 branch 或引用来凑界。|
|v3 registered wrapper／invoke 目前有 `ApplicationError(str(error)) from error` 和 `inspection['reason']`|新 wrapper 对外只发封闭、固定、non_retryable 的 type/message，不附 raw、reason、details 或原 cause；即使原异常尚小于 B 也不能泄漏原正文。异常完整业务材料继续由已有 H/operation/已审诊断 ref 保存。只改新版本；旧 v1 wrapper 的行为与旧 history 保留。取消仍走原取消／cleanup，不宽泛吞掉 BaseException。|
|V2 `run/_ordinary/_consume/status/request_stop`|已有完整 input、发送 request、received envelope、完整 status/query/outcome 和 signal 的 converter 检查；`_consume` 在读取 facts 前先核整体。默认不重写这些算法；补实际 SDK command／错误出口证据。拒绝 signal 只留有界码；拒绝 consume 不推进 prefix/ordinal，原三机会不退还。|
|SDK 在 wrapper 退出后才编码异常|必须接实际 Failure 出口；见下一节。局部异常 message 小或 helper 编码成功都不能闭合此项。|

预计产品仅 worker；验证扩展现有 `tests/test_training_runtime.py`、`tests/test_training_cycle_controller.py`、`tests/test_training_submission.py`，确有必要才改原 `tests/fixtures/training_controller_service.py`／`training_cycle_operations.py`。不预设 protocol、training_cycles、CLI、HTTP、schema 或 CI 分组变化。schema3 早期 gate 仍会拦住 dispatch 的正向现场；本地 SDK 接缝可借现有 schema2 dispatch 验同一个 owner，但必须如实标注没有运行真实 V2 dispatch，不 mock ready 为 pass 冒充现场。

## SDK 1.34 的实际编码出口

静态读取联合安装下 `venv-r1-sdk/lib/python3.12/site-packages/temporalio`，METADATA 为 **1.34.0**，未 import SDK。可复核的库位置：

- `client/_impl.py:_populate_start_workflow_execution_request` 用 client 的上下文 converter 编完整 args；`converter/_data_converter.py:_encode_memo_existing` 对所有字段编码并写 Memo map，key 和 metadata 均占字节。
- `worker/_activity.py` 在真实 `_execute_activity` 返回后再次 `data_converter.encode([result])`；异常路径在 wrapper 外调用 `encode_failure(err, completion.result.failed.failure)`。
- `converter/_failure_converter.py:DefaultFailureConverter._error_to_failure` 加实际 traceback，递归 cause/context，编码 details；已有 `FailureError.failure` 也可直接携完整 proto。`DataConverter.encode_failure` 随后还会转换 failure 内 payload。
- `worker/_workflow_instance.py` 的真实 query 失败、Workflow fail command 也使用绑定的 failure converter。status/run 的 payload 检查不能替代这些 Failure 检查。

因此允许在原 worker 内新增**一个** SDK 所要求的局部 failure-converter 类，使用 SDK 公共 `DefaultFailureConverter`／`FailureConverter` 接口，不复制异常到 proto 的规则。先委托未经改写的默认 converter 形成完整树，再核 `Failure.ByteSize()`；避免在递归每个 cause 时提前缩小，掩盖完整聚合超界。超 B 时以固定 capacity type/message、non_retryable、无 stack/cause/details/raw 的小 Failure **整体替换**并复核，不截短原错误或制造成功。新 wrapper 的固定错误规则无论大小都先执行；converter 是保护 SDK 后续追加内容的最后边界。不能在 wrapper 内预编码后又重新抛同一异常并声称最终已核。

使用 SDK 公共 `Client.config()`／`Client(**config)`，复用原 service_client、namespace 与既有配置，仅把新 client 的 DataConverter 通过其公共 dataclass 配置换入该 failure_converter_class。V2 normal/stop 两 Worker 及其 v3 activities 使用同一派生 client；V1 两 Worker 继续原 client。无需新连接、service、业务许可或适配器工厂。具体配置接线在 V2a 固定后实施，不能抢先改其服务构造。模块级类须能被默认 sandbox 重导入；core 无 SDK 的只读导入合同保持。

当前认证范围是已安装的默认 payload converter、无自定义 codec／external storage 的连接；额外 interceptor/plugin 改写最终出口、任意 codec 后大小都不作保证。以真实 Client/Worker 出口捕获 protobuf 验证这一支持范围，不新增假想配置 guard。若固定安装实证仍出现此 converter 之后的扩张，保持门禁关闭，记录最小 SDK 接口缺口并先复审；不能只在本地多调一次 helper。

## 最小验证清单与复用接缝

不为每个 helper 复制矩阵。合法值才可证明接纳；若固定 shape 不能达到某个字节值，记录其真实可达大小，把相邻编码界放到有真实可变字段的同一 SDK 出口，不加非法字段或改生产阈值。

|已有接缝|必要新增／扩展证据及可观察结果|
|---|---|
|`controller_dispatch` + `DispatchService`；原 `request.pb` 已捕获真实 `StartWorkflowExecutionRequest`|保留真实 H、claim/attempt/fsync 和 SDK 请求编码，检查实际 input Payloads/Memo；超界 claim 前无新 attempt，最终 gate 超界保留原 attempt 且无 start。复用 lost-reply／final-admission 原状态转换，不重跑全 controller 矩阵。Memo 固定单 key+SHA 目前不会自然接近 2048；用 client converter 的合法 metadata 扩张测试真正编码出口，标注为本地 SDK 边界，不把伪造额外 memo 字段称生产 shape。|
|`cycle_sdk_activity`／`cycle_operation_fault`／原 S/H fixture；`test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes`、`test_cycle_sdk_stop_keeps_all_66_real_branch_refs`|补新 v3 N32、完整 assembled envelope 各分支合界但聚合超界、混合 refs/inline unknown；完整 66 分支与原 bytes/SHA、所有 peer cleanup 均保留，整体 non_retryable failure。旧 N32 结果不能认证 v3；活动内初始早拒绝不能认证后面的 assembly。|
|`cycle_workflow`／`cycle_v2_workflow` 默认 sandbox activation harness|从真实 V2 class 的 schedule command、signal/query response、run complete/fail command 读取实际 protobuf：B−1/B/B+1、多字节、metadata、完整 predecessor/status/stop。复用已有 capacity／late-ordinal／signal-rejection 情景；query 超界为真实 failed response，run 不返回缩小的成功状态，拒绝 consume 后确认机会与 prefix 不推进。|
|现有 ActivityEnvironment 加 SDK 活动 Worker 实际 completion 出口|ActivityEnvironment 只执行函数，不等于 Worker 最终 encode_failure。保留真实 SDK failure converter 与 completion 组装，仅替 bridge/poller 捕获 `failed.failure`；错误至少含长 traceback、显式 cause/context、details metadata、预存 Failure，以及各部分小但完整树超界。断言固定 wrapper 错误即使原正文小于 B 也无 raw/reason/details；最终完整 Failure≤B，合法小错误语义保持，超界成为固定 non_retryable。不能只调用 converter/helper 后判通过。|
|原源码与新非 editable 安装接缝|新增行为的定向检查分别在源码／新 wheel 实际 site-packages 运行；保存准确产品、差异、安装来源和 SDK 版本。core 无 SDK、旧 history replay 只在新 optional import/converter wiring 真正影响它们时跑一次；V2a 已完成且本片未改的许可／deadline／shutdown 结果引用原身份，不重复跑。|

完整 Payloads 的相邻界为 32767/32768/32769，Memo 为 2047/2048/2049；Failure 最终完整 proto 同样测界。使用该 fixture 的有效配置推导长度和预算，禁止延长原时间、重开 BOOT、删 traceback 后称完整原 Failure 已合界、缩短真实路径或只测合成非法对象。既有 stdout/frame/raw-retention 合同不重写；只有实际差异触及其新 mode 或上行错误时选相关原测试。

## 分账与后继

本片闭合标准：准确 V2a 依赖身份；固定小 wrapper 错误；原 dispatch 两次完整 input/Memo gate；V2/v3 真实 SDK Payloads 和最终 Failure 接缝；必要新安装与 fresh 两轴独审。每项记录实际到达 owner、原失败、修正结果及未达边界。产品实现、源码检查、新安装、服务替身和真实服务分别记账。

真实 Temporal 仍须由最终同一候选的默认 sandbox 注册 V2/v3，捕获 server 实际保存／返回的 started input/Memo、activity Failure、signal、query/outcome 和全部 N32 stop 分支；服务加的 activity-error 包装也要量完整实际树。本地 bridge/service 替身结果不能认证这些。现场尚未完成时，V2b 可作为 closed 接缝子片接纳，**完整 M1c-V 继续开放**。

M1c-R 的每个 10MB 晚期 reader、最后 native/预算/executor gate、完整 M1c 与真实 CPU 两候选顺序 archive／恢复／停止仍归后继；本片不承诺它们已可达，也不提前开放训练或设计关卡。新产品决定若出现只记录未决。本次仅静态读取与本页写入，没有 tests/probe/模型/服务/网络/安装/提交/推送；其他 agent 的根文档变化未动。

## 根接纳后的实施状态

- [x] 以上完整静态方案已由新的fresh reviewer两轴approve／0；准确受审字节SHA256 `25069beea90535070de5f0691831eee3bcf2fbd1b0a552de9a24194e121956c2`，冻结原件 `design-r1/plan.md`，见[独立设计审](../delivery/2026-11-16-training-cycle-capacity-design-review.md)。本节为后继进度，不改受审原件。
- [x] 从已接纳联合产品 `c540939` 新建隔离 `training-cycle-v2-capacity`／`feat/training-cycle-v2-capacity`，已交独立实施者沿原owner和真实SDK接缝实施；不改原V2a固定树。
- [ ] 固定源码／受影响验证、必要新安装、原模板及fresh源码独审；实际状态写本片交付，未验不转授。
- [ ] 普通集成／发布及准确候选自己的CI；完整M1c／真实服务／reader／CPU效果仍按原合同另验。
