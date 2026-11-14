# Q2.3a：精确来源绑定的只读审查输入

日期：2026-11-15。基线 `6f42cad6edcd2ef53f2f6326628d1df728a118bd`，642产品／283参考。Q1.2已普通发布且原独立固定发布两轴通过，自己的CI另跟踪。本片承接[Q总计划](2026-11-15-domain-review-optimization-quality.md)的Q2.3，先落完整输入，随后Q2.3b接原run的完整结果与本地报告。

## 行为和所有权

操作者选择本地packet或外部来源包及独立SHA、完整冻结manifest及digest、一个reviewer叶、完整prompt容量和新目录。新CLI将原需求、全部包内源码／上下文／祖先规范／检查、外部来源观察完整放进原composition input的task。通过manifest选择领域／专长，后端仍由后续原`composition check-input/run-input`逐叶选择。缺资料／超限／权限不符或依赖未运行前驱时拒绝，不截断或冒称完成总图。

原`review_packets.read`／`review_sources.read`唯一解释来源及SHA；原`workflow_definitions`唯一编译完整资源／权限、生成和核对composition input；原`review_dags.require_root_task`核输入不依赖未执行端口。新用例仅隐藏来源到只读叶的组合义务、来源绑定task与校验、暂存后原子发布，不增加调度器、输入包文件格式、数据库、平台客户端或模型驱动。产物直接供原单叶调用，保留其input digest／完整冻结包和实际后端记录。

校验入口显式提供原来源及SHA，重新用原reader读取完整材料，与冻结task逐字比较，再核原input digest和只读叶。离线没有来源目录时仍可沿原`composition verify-input`验证完整输入自身；那不额外认证原来源。材料的规范结构及原需求／源码字节保持；原始packet文件的排版不成为task文本，来源字节SHA仍作为声明保留并在带原来源的校验中核对。两种校验的含义分开，不声称来源认证或正式批准。

## 接缝和必要限制

- 叶必须是reviewer、无write／shell／network，沿全部结构祖先直接映射根task；串行前驱／外部端口需要真实执行消费者，首版明确拒绝。原始定义与其它合法静态图不改写。
- 包内所选workspace路径必须在叶的有效read上界内；显式原需求／检查作为操作者提供的数据，不变成可执行指令或额外权限。父级完整Skill、上下文、MCP声明及逐级权限沿原编译器保留，实际能力仍以原后端准入为准。
- 构造后再核冻结图与明确选择manifest相同，避免两次读取之间切换manifest；在临时目录校验后才公开新输入。目的地不能在原来源或manifest内部，不修改已有包，也不覆盖任何既有目录。
- 真实审查仍须显式调用模型。失败／unknown先读原run，不自动重发；Q2.3b将补原run精确读取和完整报告，不能拿当前输入准备称为四路领域审查已运行。

依据复用[已有一手调研](../research/2026-11-15-pr-mr-review-tools.md)和Q1／Q2实际owner，不新增另一图格式或搬入托管审查产品。原预训练／后训练两域组合与三类通用审查均保留，kernel评估路径不变。

## 验收与进度

|步骤|完成条件|状态|
|---|---|---|
|Q2.3a-1 合同／盘点|原来源reader、完整manifest、root-task与单叶run接口、真实原消费者明确；先写计划|已盘点并固定本计划|
|Q2.3a-2 实现|prepare-input／verify-input CLI＋来源绑定用例，复用原完整输入格式，State前分派|已实现原reader→原编译器的来源绑定用例及两CLI，用户手册已补；未增加schema、数据库或调度|
|Q2.3a-3 接缝|原Git／领域preset／manifest fixture；完整原材料与祖先资源、域/专长切换，错来源／模板漂移／越权／未执行依赖／容量及原件保持；适当原回归|原四suite源码216通过／67.16秒，含两平台完整来源／祖先依赖／容量新增接缝；未新增test文件或CI job|
|Q2.3a-4 独立安装／实用|新wheel／非editable身份及283保持，实际CLI和至少一次完整领域叶调用，原run／结果保留|r1新wheel／643源码及安装逐字一致、283参考保持；安装216通过／77.35秒，17实际CLI／四完整输入及真实预训练叶24.379秒完成，保留request-changes及完整原件。私有driver收尾字段错误已沿同run读回，未重发。无训练／GPU／质量／性能主张|
|Q2.3a-5 审查／交付|自身原结构模板、新fresh-context独立两轴；普通push及完整Ref／自己的CI／原终核|自身原结构模板Codex45.105秒approve，20完整文件／三resources／原task及stdin保持；新独立本地两轴approve／开放0／0，完整源码／原件直接核过。普通发布及自己的CI另闭合|

每步更新[交付记录](../delivery/2026-11-15-source-bound-review-inputs.md)和PLAN。Q2.3b再实现完整原run证据／多分支覆盖及本地报告；当前不增加自动调度或批准。
