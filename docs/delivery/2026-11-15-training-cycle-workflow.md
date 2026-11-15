# c1：独立训练循环与总Workflow逐步交付

日期：2026-11-15。准备基线`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`，分支refactor/architecture-foundations。[实施计划](../plans/2026-11-15-training-cycle-workflow.md)细化原批准合同，承接b2b内部异步停止，不改变原六阶段、授权／clock、唯一reaper与人工release。kernel专家继续保留在v3路径。

## 只读准备

核对原controller binding／history gate、原worker／services入口、submission事务边界、显式Execution请求及rounds索引。现有原budget worker仍仅注册ExperimentWorkflow；总Workflow和独立cycle服务尚未实现。记录了两个实施前接缝：首次活动可能先于客户端receipt落盘，须通过原唯一attempt／固定run对账解决；标准SDK sandbox按module／name重新导入装饰类，而core worker导入不能强制SDK，因此须实际验证最小可选装载方式。

当前仅新增计划／本记录，没有c1产品变更、测试或运行结论。下一步先独立核本计划的需求／维护性与具体边界，然后按c1a固定总投递原件和SDK对账；真实普通操作／独立cycle进程与stop配额在自动派发之前验收。前置各片的普通发布／准确CI门禁保持，真实CPU两轮与GPU／业务训练仍开放。

## 可选SDK与标准sandbox探针

使用原worker完整导入快照的私有探针，不修改产品或安装。r1把装饰类放局部factory，真实SDK拒绝`Local classes unsupported`；r2改模块级可选SDK类，标准sandbox重导入时沿application依赖到HTTPRedirectHandler受到限制。两份原错误与源码保持。r3采用SDK原有`imports_passed_through()`仅标注application imports，保留标准SandboxedWorkflowRunner及其默认restrictions；模块级可选装饰类的SDK prepare_workflow1.552秒通过，core无SDK导入0.187秒通过，二者同一probe SHA256 `2c9076101f8e0bfe07c84e72e961a3fd616a9b842ed1da89b50cbd2044e51da6`。这仅证明该装载／准备路径可行，未运行真实Workflow／Worker、未证明c1确定性／服务隔离或训练行为，也没有选定尚未经独立核验的产品实现。

## c1实施计划r2独立门禁

新的fresh-context reviewer已逐字核最终三份计划／交付／PLAN及原合同／实际caller，并独立重跑默认sandbox准备，最终设计需求／维护性两轴approve，阻断0／0。[报告](2026-11-15-training-cycle-workflow-plan-review.md)9,681B／SHA256 `b0d1d38b3904c4efa508d6dd641de9047981c154cd11e732665693cd0ae7bb7c`。明确普通operation须另有一次性compute∩control截止、c1d前禁止后继派发、本地实施与普通发布分别记录；没有产品/API或真实服务批准。下一步c1a先实现纯意图生成与原件准备，原attempt／SDK投递／对账另接，分别验收。

## c1a1／c1b0本地接续与SDK只读准备

c1a1原意图准备已固定本地 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，c1b0有界异步准备已固定本地 `3947b1e28b2cbc27ddc53cab584cced0c8d971a6`；各自源码／新安装、自身模板和新的独立产品两轴本地闭合，见[原件准备交付](2026-11-15-training-controller-intent.md)与[普通操作交付](2026-11-15-training-cycle-prepare-operation.md)。两片各自的普通发布及准确CI仍排队，不继承这些本地结论为SDK／Workflow验收。

真实安装Temporal SDK 1.34.0的只读编码探针已结束：用内存服务替身接受一次完整controller input／原memo、REJECT_DUPLICATE与FAIL；返回handle的`run_id`实际为null，`result_run_id`／`first_execution_run_id`才是启动回复固定run。原件保留在私有`training-cycle-dispatch/sdk-start-probe-r1.py/json`。该探针无网络、真实server或Workflow，只固定SDK请求／返回对象事实；不能拿null的handle.run_id生成receipt，也不据此宣称投递已实现。

随后只读重核原`CycleAdmission.bind`的attempt／receipt字段、`training_cycles.prepare_controller`的短SQLite本地reservation、`lookup_controller`固定RUNNING最后gate、原H与所选native installation／environment装载。下一片仍须先明确：attempt唯一发布与SDK网络期间不持SQLite、闭合历史观察与最后RUNNING gate分离、SDK不引入core硬依赖、所有业务I/O留H，以及丢回复只查同ID／固定run不重发。没有后继产品改动，独立cycle服务、normal／stop配额、总Workflow和真实CPU两轮仍开放。

## c1a2固定提交与c1b1所有权前提

c1a2已固定本地`f00bfdfd15173ceb0e961681679d6d3d62254bed`，原reviewer本地及固定提交需求／维护性两轴approve／开放0／0；原安装r1的67通过与两行不可达guard删除后r2精准7通过分别归原身份。远端仍按原队列，不能继承本地通过为发布／CI成功。后继[owner生命周期具体计划](../plans/2026-11-15-training-cycle-owner-lifecycle.md)先解决长期budget根跨短H／S与正常cycle重启存活，研究确认async transport析构的主动kill也需处理；实际reaper惰性对照0.582秒已验，但实际预算根与产品接缝仍未实施。之后再接真正独立cycle服务／normal-stop配额、标准sandbox总Workflow与后继轮接受，不以研究探针冒充它们。
