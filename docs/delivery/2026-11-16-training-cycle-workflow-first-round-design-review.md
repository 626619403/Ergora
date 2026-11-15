# c1c 首轮 TrainingCycleWorkflow 独立设计审查

日期：2026-11-16。Reviewer：`/root/cycle_workflow_design_audit`，fresh context；未接收设计者实施对话。本报告为唯一写入；未修改设计、PLAN、产品或测试，未执行测试、安装、构建、联网、服务、训练或提交。

## 两轴结论与身份

**需求轴 approve／开放0；维护性轴 approve／开放0，仅为设计层结论。** 在本次检查范围内未发现需阻断草案的具体可达设计漏洞。这不认证正式 Workflow 已实现、SDK sandbox 已运行、真实首轮／取消已验，也不关闭 c1b2b 产品前置或 c1d 接受／后继门槛。

待审文件为 [首轮草案](../plans/2026-11-16-training-cycle-workflow-first-round.md)，SHA256 `10462494852d423c341b1e5c1af50e3e56e3eda810598ca6a14fe12c3b7836fb`。主树分支为 `refactor/architecture-foundations`，HEAD `691809563c410cc1f9d93bc6f821b313f7a2772b`；该文件为 untracked，主树已有其他在途文档差异，本次未接管这些差异。

原始依据为 [c1总计划](../plans/2026-11-15-training-cycle-workflow.md)、[具体合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[执行消费者r2](../plans/2026-11-16-training-cycle-execution-consumer.md)。先读根／src AGENTS、docs/PLAN、组件协议的执行／证据与检查规则，以及 `maintainable-project-delivery` 的 independent-review、`ergora-codebase-quality` 的 repository-style／module-design／test-seams 引用；再核草案、真实 owner 与 SDK 源码。

执行消费者专属树 HEAD 为 `af176cf6e79adb9c6ef6f32946672bc77cdb89de`，三个源码 owner 与四个测试／fixture 文件仍为未提交修改。静态检查涉及 worker 的 cold／ordinary facts、SDK工厂／服务注册，protocol 的请求／来源／mode 与原执行链 reader，execution 的 request/check/current／root admit，及主树 runtime/submission 的固定 run 读取路径。结束取样时三个 owner SHA256 如下；这是调查样本，不能作为固定交付身份：

|文件|SHA256|
|---|---|
|`reference_training_worker.py`|`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`|
|`training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`reference_training_execution.py`|`c105ac8d2b248169b46a4c8a5692dbda90c7642e7907e7f19969345de1c7ea90`|

worker 在本轮只读调查期间有变化，已不同于草案第13行的历史取样；草案第9、17行已明确要求实施前重核固定结果。另读了 [c1b2b产品审查](2026-11-16-training-cycle-execution-product-review.md)：其 runtime 外来 job 投影 R1 仍属该 producer 的修复／验收责任，本报告不替其关闭。

## 需求核对

- **默认 sandbox／可选 SDK（草案35–47、134–142行）。** 模块级 decorated 类保留原被 pin 的 worker owner；工厂只返回该类，真实 caller 是 `_serve_cycle` 的 normal Worker。原 budget 进程／8槽与 cycle normal／stop 各1保持。只读 SDK 1.34 的 `workflow/_definition.py` 确认 run 拒绝 `<locals>`，sandbox `_runner.py` 按 module/name 重导；草案未靠局部类、alias、关闭 sandbox 或新增线程绕过。应用依赖 pass-through 与 worker 本身重导的区别明确，无SDK与损坏SDK也分别处理。该结构在设计上成立，仍需 W0 的新安装、默认 runner 与真实注册证明。
- **固定输入／一次效果（49–82行）。** 六字段、固定父 run/memo/history、ordinal0 与原 producer 保持；start/request 在 command 前永久消耗机会，未知、timeout、not_attempted 或文件 absence 不重授。receipt 只进入观察；双 QUEUED、固定 run、完整 Binding/job 与最后 H gate 才能请求。新两 v2 才有 compute facts，v1桥接只收窄 total；cold facts 的 operation ID 可匹配 inspection，未假设只在 operations。整体 unknown 的局部事实可留存，但不授新效果。c1d 闭合前无第二候选、accepted 或 rounds 写入。
- **数值截止／恢复（84–107行）。** `D=min(旧D,A+remaining)` 使用 command 前 history 时间 A，收到结果的 R 不刷新窗口。例如 A=0、R=4、末样本 work=9，则 D_work=9、处理时只剩5；若下一次 A=5、R=7、work=6，新界仍为 min(9,11)=9，剩2。例中数值仅说明推导，不限定有效配置。B 再取原 control 与10秒上限，非正不发；total 独立收窄供 stop，未知不补清理额度。回放重建同一 command／D／计数；真实 BOOT、父许可及锁内发布前后 gate 仍归原 H/root，不把 SDK history clock 当授权时钟。对服务器暂停后的实际最后 gate，W4 仍须取真实证据。
- **取消与独立 stop（109–120行）。** 草案先保护 ordinary handle 的所有权，再请求取消并立即调独立 stop，不先 await ordinary cleanup。SDK `workflow/_asyncio.py` 的 deterministic wait 只清除等待回调，不会取消传入 task；SDK `_workflow_instance.py` 的 activity cancellation 等待逻辑说明了直接 await ordinary 时 catch 可能被推迟的原因。草案持有并 shield 唯一 stop handle、保留 CANCELLED 语义的选择有实际库依据。cold无total、重复cancel、SDK timeout、服务shutdown与不可中断OS调用分别保留未知；SDK完成不证明 S/H 或原子树停止。旧 stop.v1 无 cycle级 inline durable 汇总，草案据此保持 stop字段 null／needs_reconciliation，没有假读 refs 或用 observed／operation_stopped 填业务成功。
- **容量／query／history（61–65、122–130行）。** query 是预先定义的小型控制观察，仅读确定性状态，不读 refs、不调 activity、不改计数或截止；原完整封套／错误留 history 与原owner。signal合法性、拒绝投影与已进入history的事实分开；拒绝不会反复失败同一 Workflow Task。SDK公开 payload_converter／to_payloads_wrapper 确实能计算含metadata的 Payloads，草案限定已核默认converter／无codec边界，不以JSON长度替代。256包含全部ordinary command与失败；8000 events／8MiB在下一ordinary／timer前检查，留一次stop及固定outcome余量，不continue-as-new、不跟新run。外部signal突发和较低server上限的限制如实记录。

首轮终点同时要求 native成功、durable／executor停止与真实release阶段或限定原完成outcome，仍只是交接观察。runtime owner 对 COMPLETED 的 `phase` 来自固定 run 的 `outcome.status`，故草案所写 RELEASE_EXPIRED／INTEGRATION_TASK_CREATED 可由既有 typed facts 消费，不需要 Workflow 另读 outcome 文件。完整 job 身份须以 c1b2b 修后固定 producer 为前置，不能借本段绕过其 R1。

## 维护性与验收边界

现有 source-pin owner 承载真实框架类与唯一服务注册点有明确归属；工厂是可选SDK构造边界，run/query/signal是框架要求的方法，无须伪造第二生产caller。私有方法仅隐藏该类的command计数、截止和停止handle生命周期，未引入 manager、第二reader、第二executor／reaper或通用循环框架。protocol只在确有共享wire需要时扩纯validator，保留原runtime/submission/execution权限边界。没有独立维护性 finding，也没有要求扩大到通用Repeat／WA4产品决定。

后续客观验收按草案W0–W10执行，尤其必须保留以下证据，不能由本次设计结论填格：

1. 先固定 c1b2b 三 owner／wire 与 job身份修正，取得其自身适用源码、新非editable core／SDK、真实S–H／服务和fresh产品审查；若facts合同变化，先修订本设计。
2. 用正式 TrainingCycleWorkflow 的真实history核一次start／request、receipt先到与双QUEUED、发前／fsync后丢completion、worker重启与失败／终态Replayer；核原件／request／launch身份和数量，不能只数mock调用。
3. 排队／RPC／timer／server暂停后核原A/D及BOOT最后gate；normal真实阻塞下，重复signal／cancel须先调独立stop，再分别记录ordinary cleanup、stop transport、原资源收尾和CANCELLED，total不足保持未知。
4. 用真实SDK编码与真实server history核32KiB、256、8000／8MiB及预留stop；query/outcome保留合法固定字段且不产生业务动作。新wheel、site、输入冻结、283参考与所有自建进程／端口／Workflow收尾单独记账。

本次只有文档／源码／SDK源码只读核对、Git与SHA检查；没有运行任何上述产品验收。后续CPU受控runner只认证控制／执行链，训练质量、真实GPU、accepted archive、rounds、第二候选和公共入口仍由各自后继片负责。
