# D2-B3a：专家提案到原实验合同的可追溯交接

日期：2026-11-14。源码基线`41dd5aa30f589b5c27a1cc3f09db59d66005a40f`；本片开始时产品候选自己的CI与U3升级分别验收；期间补交接资料，不改产品、原执行器或283冻结参考文件。

## 目标与范围

沿[专家计划B3](2026-11-13-specialist-presets.md#b3实验执行保持在原所有者)，在现有训练手册说明如何从完整原提案填写workload、baseline、experiment及runner，逐字段保留来源、人工决定与未验项。复用原`agentflow training`的prepare／manifest SHA／run-local／可信证据与evidence SHA批准，避免另建运行器、训练账本或提案转换schema。

模板输出为自由文本／原result，不是原实验manifest。由操作者完成语义映射，真实配置、代码、数据、初态、oracle和资源由其原所有者提供；Agent意见不变成批准。允许用简短Markdown追溯表记录原结果摘要和字段依据，现有validator不自动核查该表。

|节点|可验收结果|状态|
|---|---|---|
|B3a.0 原合同核对|源码、冻结模板、prepare／gate／runner的实际语义|已只读核对；不运行或修改参考执行栈|
|B3a.1 使用说明|原手册内字段映射、预算／检查／批准／unknown与证据交接|已实现；22个experiment、6个baseline与6个runner字段已对照原模板|
|B3a.2 原产物走查|复用B2i真实调用的原result，核其字段依据与缺项，不复制synthetic为真实manifest|已完成四原调用身份及kernel两份／measurement三份完整前驱复核；实际B3开放|
|B3a.3 独立审查|文档链接／diff与新fresh-context两轴审查|195目标／14锚点、4凭据值／283冻结／diff及新fresh-context独立两轴通过，开放0／0|
|B3a.4 发布|普通提交／推送，准确保留B3真实运行开放|完成：6d4006e普通推送／作者完整SSH Ref核准；完整B3实际运行仍开放|

完整B3仍需真实项目workload、候选、数据／初态、受信runner与评价：至少一份真实提案映射到真实冻结manifest，再在同一原实验身份取得执行／失败或no_gain／独立评价及精确证据批准。当前没有提供这样的目标，不能用本片走查、现有设备可见性或synthetic数值关闭B3。

结果逐步记录于[交付记录](../delivery/2026-11-14-proposal-experiment-handoff.md)。资料与U3完成后，继续C2固定Forge入口的全会话接缝与父合同核对；只有实际支持的消费者才进入执行适配。
