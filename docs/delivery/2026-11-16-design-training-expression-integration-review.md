# a1／M6-V1 联合集成独立审查

2026-11-16。Reviewer：fresh-context 独立代理 `design_training_integration_review`，未参与两片实现或本次合并。依照 maintainable-project-delivery 的 independent-review brief 与 ergora-codebase-quality 的 module-design／test-seams，先以原始范围和实际源码判断，再用作者交付和原 source-review 定位验证证据。本次唯一写入为本报告；没有改源码、测试或其他文档，没有重跑 suite／probe、安装、模型、服务、网络、提交或派生 reviewer。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|**approve，仅限准确联合候选的 a1 inspection-only／M6-V1 表达及所核安装接缝**|0|
|结构／维护性|**approve，同一范围**|0|

未发现可达的跨片缺陷或应阻断本次集成的维护性问题，无源码修正要求。该结论不认证后继设计运行关卡、训练效果开放、真实服务、完整 M1c、CPU／GPU 两轮、公开发布或候选自己的 CI。

## 范围与身份

原始合同为 [WA5a-1 最小首片](../plans/2026-11-16-design-knowledge-gates.md)及 [M6 设计的 V1 正式 V2／v3 表达](../plans/2026-11-16-training-cycle-v2-runtime.md)。已读根、src、tests 的 AGENTS、当前 PLAN 与[组件协议](../architecture/component-change-protocols.md)。只审两片合并后的真实跨片关系，不递归审查状态记账。

联合基线 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`，候选 HEAD `f9b9d72d6d5f2102809a3cafaadb2226bba0966b`；源码／测试工作树无未提交差异。a1 固定 `cb861ea7138627d6646e8de1c0867a3ed92ce474`，经 `3d632a78b6acc4f0027b2225e7771a5da927af81` 导入；M6 固定 `2acdcc44eb86659f3ab9d22d2f83bb0973388406`。本次核对完整产品 diff，并追读必要相邻 caller。

|原片|检查文件|
|---|---|
|a1 六文件|`src/ergora/reference.py`、`reference_task_approval.py`、`task_design.py`、`data/schemas/task-design-v1.json`、`data/design-profiles/framework-development-v1.json`，以及 `tests/test_task_plan.py`|
|M6 五文件|`src/ergora/reference_training_worker.py`、`reference_training_runtime.py`、`training_execution_protocol.py`，以及 `tests/test_training_runtime.py`、`test_training_submission.py`|

独立按 Git blob 重算私有 `merged-source-inputs.json` 的十项原字节与 SHA，均与各自固定产品相等；清单外的 `test_training_submission.py` 也与原 M6 完整同一，记录的 `submission_test_difference` 确为空。两片产品变更无交叠文件；不是为这次合并重新修改 Windows skip、测试正文或新建第三套实现。

原交付／原审仅保留各自范围：[a1 交付](2026-11-16-design-packet-inspection.md)／[原 source-review](2026-11-16-design-packet-inspection-source-review.md)，[M6 交付](2026-11-16-training-cycle-v2-expression.md)／[原 source-review](2026-11-16-training-cycle-v2-expression-source-review.md)。本联合实证见[集成记录](2026-11-16-design-training-expression-integration.md)；未将作者或前 reviewer 的 approve 直接作为本次判定。

## 实际集成关系

**应用／native 依赖边界保持。** `tasks.plan → reference.task_plan → _task_operation → 所选 native Python → reference_task_approval._plan/_read_design` 仍沿原调用。`reference.py` 顶层只加载原 stdlib／process／creation-process 依赖；完整 `contracts.validate` 与纯 `task_design.inspect_packet` 只在应用取得 `design_read` 后懒加载。native `_read_design` 只做安全有界读取所必需的列表、记录、唯一 ID、access／path 检查，读取全文并返回实际 SHA／bytes。它没有引入 jsonschema；protocol/native 读取 `contracts.py` 等 gate source 的字节也不会导入这些模块。

公开 `reference.task_approval(..., 'inspect-plan', ...)` 转入同一个 `task_plan`；status／dispatch／resume 保留原 `_task_operation` 路径，没有递归调用。无 packet 原结果直接返回；有 packet 的两公共入口均先完整结构／领域校验、消耗并删除 `design_read`，再返回受限结果。原注册解释器回归保留主 dispatch、`_Submission`、native main、history／envelope／receipt，只有远端连接叶子为 SDK 替身；明确拒绝 native jsonschema 后，两个入口均可读合法材料且均拒绝缺 `problem` 的 packet。联合 82 项包含此实际进程接缝，不能仅由应用内 helper 的通过替代。

**检查未变成批准或运行。** companion profile 的 schema 固定 `inspection_only:true`／`runtime_enforced:false`；结果亦显式保持这两个值，纯 readiness 永为 false，Q 仍未决，K supplied 仅表示可读资料供给。`actor_assurance`、未冻结 policy／owner 和 false approve／resolve／execute capabilities 没有被 M6 消费为执行许可。没有 input12、definition8、State6、journal mutation、模板默认或六阶段变更。原批准 writer 未改，设计 packet 不会替旧批准增加隐含 gate。

**训练默认与效果关卡保持。** 生产 `_serve_cycle` 与基线 AST 相同，仍调用缺省 V1 工厂；显式 program 2 才选择顶层 V2／v3。旧 `TrainingCycleWorkflow` 除 `_consume` 转调原事实校验尾段外，其余原方法 AST 相同；V1 对共享 `_consume_facts` 仍传 ordinal 0。新 V2 保留原 facts／预算／BOOT、三次原机会及唯一 collect；received-envelope 先验完整容量，再核当前 operation／ordinal／candidate／selection／acceptance，重投 collect 沿真实原 source 转 existing-only reconcile。`PurePath` 按原 H 的 `Path` 组成同样的目录字符串，不做 Workflow 文件读取。

H 的 schema3 关闭门仍拒绝 prepare／submit-controller、三个 start mode、request-execution、stop-writer／notify-owner；原 `training_cycles._controller_ready`、`BudgetedStart.source`、`validate_context`／native 末端拒绝未移除。新增只读／对账 mode 可保存原 receipt、同步原件和形成观察，不因此获得 start／native create／request／launch／runner 机会。collect／reconcile 保留原 M2 索引与观察发布语义，reconcile 缺目标仍不能 create。联合 H 检查确实到达原 S/H 和六个关闭 mode；不能把合成已有链写成真实父 Workflow／两轮执行认证。

**来源身份未遗漏或换绑。** AST 对比确认 `GATE_SOURCES`、`GATE_SOURCE_PROTOCOLS`、四项 `MEASUREMENT_SOURCES` 与基线同一，仍为 25＋4。合并后的 `reference.py` 与 M6 worker／runtime／protocol 均在原 25 项中，由原 source capability 按各完整文件的当前真实字节固定；`validate_sources` 仍在原件／安装检查前后重核，并调用原 `reference.verify()`。旧 owner 的旧 pin 不会被合并重写或按当前包重授，旧 history replay 也不等于旧执行授权。a1 的 schema／task_design／approval reader 只服务应用 inspection，没有成为 native 训练执行依赖，未见应扩展效果 source 表的真实新增消费者。原 manifest、native descriptor／patch、283 参考及含 127 个 requirement pin 的原锁与基线无差异。

## 维护性与验证接缝

现有 owner 各自持有实际义务：应用 `task_plan` 负责公开校验，native reader 负责安全 I/O，纯 `task_design` 隐藏整套 ID／引用／Q/K 领域关系；它虽当前只有一个生产 caller，仍有内聚职责，不为未来 caller 另造接口。M6 的顶层新类满足 SDK 重新导入和旧 history 隔离，共享原事实算法而保留版本专属 command／envelope。无新调度器、ledger、通用 registry、库或测试框架。

native 的最小读取 guard 与应用 schema／领域校验保护不同边界；V2 完整 envelope／operation 检查和共享原 facts 检查也有各自输入义务。未发现可删除而不重新暴露安全读取、持久身份、原机会或容量风险的重复 guard。本集成不增加只证明实现字面量的测试；沿现有应用→所选解释器、SDK activation／history 和真实 S/H 接缝核现成证据，覆盖层次与其声称一致。

## 本次独立核对的证据与限制

原件在私有 `.ergora/checks/design-training-expression-integration/`；本审只读取、重算字节／AST／集合及 `/proc` 身份，不执行其中脚本。

|原件／检查|独立核得的结果|
|---|---|
|`package-r1` 新非 editable 产品|wheel SHA256 `ea1927be9ad5a51fdf28142af9a0e713beb5994aeb53c3efd32e647d88b53d71`。668 项源码、wheel、core、SDK 的文件集合、完整字节、SHA、执行位均同一；训练三 owner 的记录路径为各自 site-packages。core 无 SDK、SDK 1.34.0；原依赖检查／283 reference 校验均 0 退出。|
|冻结输入／复制测试|独立重算 862 项构建输入及 179 项测试／示例副本的字节／SHA／执行位，均同源。冻结清单 SHA256 `7177f292c9d4377a8c616e4123dc88546d1ead487f7b708def67e53ca8388054`；源码／测试没有后改。|
|`installed-affected-r1.*`、外层 `installed-design-and-runtime.command.json`|准确 `-I -B`／去除源码 PYTHONPATH、复制测试目录；JUnit 82 tests，0 failure／error／skip，stdout **82 passed／39.06 秒**。组成是原 plan＋旧批准两例 57，以及原 V2／v3 25；未跑全 suite。|
|`installed-submission.*`|原 S/H 定向 **8 passed／90.66 秒**，JUnit 0 failure／error／skip。含原唯一 collect／丢回复、完整 stdout／frame、operation-v2 ordinary／ordinal=None 原编码留存和实际 H effects 关闭；替身／合成链限制保持。|
|`installed-core-no-sdk.*`|命令 0 退出；脚本同时导入 reference、task_design、训练三 owner，确认无 temporalio 模块，V2 工厂明确报缺 optional SDK。不是 native 全127依赖安装或服务认证。|
|`installed-windows-path-probe.*`|原同一 probe，三 owner 与测试 fixture SHA 同候选；native Windows 目录语义 accepted／confirmed=1，旧 literal 控制组 rejected／confirmed=0，0 退出。仅纯路径／消费模拟，不是 Windows 主机或正式执行。|
|原 CI collector|`ci-collector/result.json` 0 退出／9.241 秒。独立比较前候选 2335 与当前 2386 的完整 node multiset，唯一原参数化 ID 精确映射到保留的 collect-round 原分支后，删除 0、净新增 51：plan 23／runtime 25／submission 3；与 reconciled 原件同一。只证明收集，不冒称执行通过。|
|最终固定／资源|`final-freeze-resource-check.json` SHA256 `930c42d1fc781c94852c552d787e5849d154a1d79cedd2f370244e8390934c2a`。五命令合计 269 份实际捕获 PID／BOOT／start 记录，原记账均 absent；本审再按这三字段独立读 `/proc`，269 absent、0 live、0 unknown。只限捕获身份，不称全系统零残留。|

单片原非重叠源码／安装、三份旧 V1 history replay、原模板及独审仍保留原候选范围；本次不重复认证或重跑它们。后继 S1／M6-V2a 在其他 worktree，未混入本包。实际可信 owner 通道、设计 G1/G2、完整 M1c／四 poller、真实 Temporal 恢复与 CPU／GPU 训练、发布及本候选官方 CI 仍须各自在既定节点取得证据；没有把这些未验项变成本集成的新源码 finding。
