# c1：独立训练循环与总Workflow逐步交付

日期：2026-11-15。准备基线`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`，分支refactor/architecture-foundations。[实施计划](../plans/2026-11-15-training-cycle-workflow.md)细化原批准合同，承接b2b内部异步停止，不改变原六阶段、授权／clock、唯一reaper与人工release。kernel专家继续保留在v3路径。

## 只读准备

核对原controller binding／history gate、原worker／services入口、submission事务边界、显式Execution请求及rounds索引。现有原budget worker仍仅注册ExperimentWorkflow；总Workflow和独立cycle服务尚未实现。记录了两个实施前接缝：首次活动可能先于客户端receipt落盘，须通过原唯一attempt／固定run对账解决；标准SDK sandbox按module／name重新导入装饰类，而core worker导入不能强制SDK，因此须实际验证最小可选装载方式。

当前仅新增计划／本记录，没有c1产品变更、测试或运行结论。下一步先独立核本计划的需求／维护性与具体边界，然后按c1a固定总投递原件和SDK对账；真实普通操作／独立cycle进程与stop配额在自动派发之前验收。前置各片的普通发布／准确CI门禁保持，真实CPU两轮与GPU／业务训练仍开放。

## 可选SDK与标准sandbox探针

使用原worker完整导入快照的私有探针，不修改产品或安装。r1把装饰类放局部factory，真实SDK拒绝`Local classes unsupported`；r2改模块级可选SDK类，标准sandbox重导入时沿application依赖到HTTPRedirectHandler受到限制。两份原错误与源码保持。r3采用SDK原有`imports_passed_through()`仅标注application imports，保留标准SandboxedWorkflowRunner及其默认restrictions；模块级可选装饰类的SDK prepare_workflow1.552秒通过，core无SDK导入0.187秒通过，二者同一probe SHA256 `2c9076101f8e0bfe07c84e72e961a3fd616a9b842ed1da89b50cbd2044e51da6`。这仅证明该装载／准备路径可行，未运行真实Workflow／Worker、未证明c1确定性／服务隔离或训练行为，也没有选定尚未经独立核验的产品实现。

## c1实施计划r2独立门禁

新的fresh-context reviewer已逐字核最终三份计划／交付／PLAN及原合同／实际caller，并独立重跑默认sandbox准备，最终设计需求／维护性两轴approve，阻断0／0。[报告](2026-11-15-training-cycle-workflow-plan-review.md)9,681B／SHA256 `b0d1d38b3904c4efa508d6dd641de9047981c154cd11e732665693cd0ae7bb7c`。明确普通operation须另有一次性compute∩control截止、c1d前禁止后继派发、本地实施与普通发布分别记录；没有产品/API或真实服务批准。下一步c1a先实现纯意图生成与原件准备，原attempt／SDK投递／对账另接，分别验收。
