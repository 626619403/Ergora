# D2-B2b：CUDA Graphs 与 sequence packing

承接[D2方向计划](../plans/2026-11-13-specialist-presets.md#b2按决策粒度发布资料子模板)和[R6固定来源研究](../research/2026-11-12-optimization-execution-graph-agents.md)。前置B2a资料、安装、实际叶、自身审查及fresh-context独立验收均已完成，普通提交`fc67c3d`；本片两个方向分别验收，不借前片结果授予新包运行通过。

本片仍复用`ergora-training-analysis@2.0.0`和`ergora-measurement-review@2.0.0`，分别提供design／profile与包含正确性门槛的measurement职责。每个根只有workflow、instructions、完整context三文件，使用原catalog／CLI／HTTP定义入口，不增加Agent类、执行器、schema或状态。图只声明组合；实际只读叶调用及完整前驱交接逐项记录，真实训练和采用仍由原runner／owner负责。

|节点|可验收出口|状态|
|---|---|---|
|B2b.0 资料与合同|两个独立根，固定R6 provenance；graph实际scope／地址／RNG，packing四路径／边界／loss／有效token分开|六份数据及catalog登记已提升到工作树，与已验安装候选原字节相等；运行验收分别见下两行|
|B2b.1 安装|保留既有根／v2／283，原Interface检查完整祖先与三叶权限；隔离noneditable包及必要preset检查|512产品／两RECORD／283及安装17项／69.67秒通过；B2a提交后已将catalog／test提升至工作树，八文件与已核候选逐字相等|
|B2b.2 实际叶|每根三次独立只读调用，完整资料与手动前驱；缺硬件／数值／测量证据仍明确保留|六叶真实Codex成功，36资源62,230B完整连续UTF8及两前驱全文手动交接通过；两measurement均缺证据request-changes，没有GPU／自动图承诺|
|B2b.3 审查与交付|自身原审查模板及fresh-context双轴；更新使用入口／计划，普通提交／推送／必要CI另记|原结构模板108.003秒approve／八件41,857B全文；输入／protocol／stdin及最终13文件fresh-context双轴终核通过，开放0／0；过期catalog状态P3已修复复核，本地出口完成|

CUDA Graphs资料以真实host gap为选择依据，区分compile图、CUDA capture／replay和optimizer capture；按实际Bridge／Core／TE版本核组合。Packing资料区分offline、in-batch、Energon worker buffer、global-batch，不合并动态THD门禁；训练语义覆盖样本边界、loss归一、MTP和checkpoint恢复。来源是本项目短知识综合及固定上游链接，不复制上游Skill或宣称已装工具。

新文件由原catalog安装Module的CLI／HTTP两个现有生产调用者消费；新增context由三个实际叶继承，差异留在数据资源。测试沿既有方向合同参数化增加两项，仅覆盖漏装、精确版本／祖先材料遗漏和离线manifest持久性的可达静默风险，不为资料文字建立新算法测试框架。

预候选从`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`精确归档，仅叠加已核stdin／poll前置、B2a三根以及本片六数据与两份私有catalog／test覆盖；没有改变B2a正在评审的产品文件。wheel SHA256 `7dfe5549d61959aab2eea97f08a5485bd5eda46db0e931abb0dfcf9e9e895263`，隔离源码／wheel／安装512产品相等。测试控制器71.623秒、pytest69.67秒分别记录；当前只授予这组明确覆盖候选，提升时将逐文件核与工作树相等，内容变化才重建／重测。

B2a独立终核并提交后，已按原字节提升八个产品／测试文件，`promoted-source-identity.json`逐项记录；没有产品内容变化，未重复模型／测试。手册增加两个可选preset、所需graph／packing资料及同一三叶／手动交接入口。原自身模板结果SHA256 `d56d450d7f773bf3ffeef13c1d195b074c64fc13bb275a12f5e20bcdc5927d28`；聚焦正文和全部结构资源确已进入stdin，其approve不替代固定源码事实的独立核对。

## 原始叶与交接

Graph三叶共18资源29,831B，packing三叶18资源32,399B；每叶核完整manifest／input／祖先与自身资源、prompt／protocol／stdin、原MCP连续UTF8／末页null、结果SHA。measurement任务手动提供design与profile的完整原结果，前驱SHA逐项相符。两方向各用独立State和三个实际会话，不把静态边称为自动执行。

固定输入是已保存的未来dense decoder／BF16／AdamW／PP2场景，以及示例shape序列和两个样本token数组；没有实例化模型、采集trace或执行训练。Graph明确需先证host关键路径及真实版本的capture/replay合同；packing需按实际路径核PP等限制、sample/loss边界和恢复。两measurement均返回request-changes并保留硬件／版本、独立数值／质量、实际replay或mask、配对端到端测量与候选缺项。独立Codex会话为授权回退，不宣称异构后端、GPU收益或采用。

[新独立评审](2026-11-13-optimization-execution-directions-review.md)按固定基线`fc67c3da7041bdcfd46430bc7268e25a55df6de9`核完整13文件及原件：512产品的source／wheel／installed／当前工作树相等、两RECORD／283及旧catalog／共享v2保持，六原始叶、完整前驱、自身模板和13份来源逐项核准。原唯一P3为本表catalog状态过期，已作单cell修正并获双轴复核关闭；最终manifest SHA256 `ec95f820b2f0ba45fc28553e5c6f03e2d13e317fbf13e086dc44960054f26aec`。本地出口通过，远端及本候选自己的必要CI另记。
