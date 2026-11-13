# D2-B2a：显存、重计算与卸载方向子模板

实现基线`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`。承接[D2方向计划](../plans/2026-11-13-specialist-presets.md#b2按决策粒度发布资料子模板)及[R5一手来源研究](../research/2026-11-12-optimization-memory-agents.md)，先交付三个独立选择的readonly根，不把全部方向强制装入共享训练根。

隔离非editable wheel已构建，SHA256 `06f9ad909396597409dcebe86c6fbe63bffefd0aec16867d56fbe238e4aa039a`。506产品文件与隔离源码／安装目录相等，wheel和安装RECORD及283冻结参考文件通过。该包明确叠加已独立审查的stdin／轮询前置修正，安装测试、实际叶和独立评审另记，未借前置片旧包结果授予本片运行通过。

|catalog选择|实际根／版本|主要独立交付|
|---|---|---|
|`optimization-memory-tuning`|`ergora-opt-memory-tuning-proposal@1.0.0`|最热rank／阶段容量分解、估算假设与缺项、碎片证据及有限候选|
|`optimization-activation-recompute`|`ergora-opt-activation-recompute-proposal@1.0.0`|实际版本的selective／full边界、RNG／数值／梯度与通信重放、图与卸载组合限制|
|`optimization-cpu-offloading`|`ergora-opt-cpu-offloading-proposal@1.0.0`|层级激活／细粒度激活／优化器三个机制的兼容矩阵、host／pinned／NUMA／传输及端到端代价|

每个根仅新增`workflow.json`、`instructions.md`、`context/<direction>.md`三份数据。根组合原`ergora-training-analysis@2.0.0`与`ergora-measurement-review@2.0.0`，复用designer／analyst／measurement reviewer三位专家；无新Agent、role、Python类、runner、schema、调度或状态账本。根context与所有结构祖先资料进入每个所选叶；兄弟资料仍不继承。现有五catalog条目、共享v2包与283冻结参考文件保持。

这些来源是项目自编短知识材料和固定上游链接，没有复制带独立许可的文档或上游Skill。R5已核到Skill与固定Core源码的漂移，资料保留空selective control、fine-grained offload的PP支持及特定full-iteration例外，要求以实际安装版本和Bridge model spec准入；不会把旧Skill泛化成统一PP／graph／recompute规则。

|节点|完成条件|状态|
|---|---|---|
|B2a.0 数据与使用入口|三独立根及catalog；复用共享专家；手册列版本、路径与手动交接|数据与两使用入口已实现；不改变共享v2和原5个catalog条目|
|B2a.1 安装与合同|三个根可独立安装／重复导入，全部三叶只读且完整继承本方向context，离线manifest可重建输入；隔离包身份及必要检查|506产品／两RECORD／283及安装15项／59.22秒通过；外部控制器61.03秒|
|B2a.2 实际交付|真实只读叶输出方向特有合同／资料缺口，完整资源及手动前驱原件可追溯；无GPU运行或收益冒称|九叶实际Codex成功；54资源88,611B完整连续UTF8读取及全前驱手动交接已核；三measurement均保留缺证据request-changes|
|B2a.3 审查与交付|本项目自身模板、新fresh-context两轴，计划与原件同步；普通提交／远端及必要CI分别记录|自身原结构模板42.021秒approve／11件46,784B完整内联通过；最终16文件和原件新独立两轴开放0／0、P3关闭，本地出口通过；发布／自己的CI开放|

测试只在原preset suite增加一项三方向参数化合同检查，针对共享Agent时方向context被遗漏、版本漂移或活动库删除后丢资料的静默风险；复用原manifest／输入Interface，没有为文字规则复制算法负向suite。`run-input`仍每次只执行一个选中叶，完整前驱结果由操作者手动提供。实际实验、停止、恢复、质量与采用仍由原可信runner和owner负责；单次文本提案不证明原生流程已接入。

首轮源码suite记录为4 failed／11 passed／50.52秒：新增测试误从workflow实例读取只提供给agent叶的`resources`，以及源码父进程与旧安装包的`-I` CLI子进程catalog不一致。前者只修测试以读取本包完整材料并核继承来源；后者为验证harness混用候选，后续采用同候选非editable安装核CLI。原失败保留，不通过修改产品Interface或原CLI测试来掩盖。

## 实际只读叶与原件

每个方向在独立State中安装并冻结精确根，分别执行design、profile、measurement三个叶；measurement的task正文手动附入两份前驱原始结果全文并核SHA。固定输入是已保存JSON配置场景（dense decoder、BF16／AdamW、TP2／PP2／DP2等），不是已经运行的模型、GPU或观察到的OOM。所有叶只可读冻结MCP资料，不可shell／外部网络／写项目。九次实际调用均为Codex显式回退并保存原因，独立会话不宣称异构后端。

显存方向18资源28,637B，重计算18资源28,823B，卸载18资源31,151B；全部来源／实际input／prompt／protocol／stdin与原件相等，MCP连续UTF8读至null。各方向measurement收到两个完整原始前驱结果，并因缺少实际版本／rank硬件、独立数值／质量oracle、配对计时／峰值及候选恢复材料返回request-changes；该结果不等于产品失败或测得无收益。提案及缺项交给原可信runner／owner，没有实际实验／GPU测量／采用。

同一安装的原structure-review模板收到11份新增／修改产品与测试全文46,784B，42.021秒返回approve，原结果SHA256 `66cc297403e7709b7cb1486321cb46017a3e68da9d6db4ca8276cc41004e8bb9`。完整结构资源和正文与实际stdin逐字相等，聚焦模型审查不替代完整独立评审。安装、九叶审计和模型原件保存在本项目私有checks的`optimization-memory-directions`；公开投影保留摘要与原件SHA，不分发环境路径／凭据。

独立Standards初审指出D2计划仍有“当前仅数据／检查准备”和九叶在途的过期文字（P3）。已在原检查点就地修正为安装／九叶／手动交接完成，保留独立评审、发布和自己的CI开放；没有修改产品或重跑模型。该状态修正及最终两轴结果由[独立审查记录](2026-11-13-optimization-memory-directions-review.md)负责。

新fresh-context最终复核已完成：Spec／Standards开放0／0，P3关闭；r3的16文件、506产品／两RECORD／283、九叶完整材料／原前驱／结果、原结构模板及12份固定来源原件均独立核准。本地B2a出口完成；普通提交／远端及精确候选必要CI分别记录，未授予训练执行或GPU收益。
