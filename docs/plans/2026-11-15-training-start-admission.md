# Q4.2a1：已准备训练实验的只读启动检查

日期：2026-11-15。固定实现基线`5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`；承接[有界循环计划](2026-11-15-bounded-training-cycles.md)。前片自己的CI另跟踪，本片可本地实施，前片终核前不推后继产品。

## 行为与原owner

循环冻结有限选择和操作者准备启动都需要同一原启动准入观察。`training.inspect`只读取原记录；`submission`无意图时只调用records；`preview_experiment`是准备新实验的owner。它们均不等价于原`_Submission.preflight`的Git根／完整提交、runner／时限、comparator、baseline和原job／fence占用检查。

在原`training`／`reference_training_submission`及薄CLI增加`training check-start PROJECT EXPERIMENT --manifest-sha256 SHA`。复用原preflight／load／status，明确选择完整manifest身份；不复制检查，不新增schema、State、SDK或训练实现。新实验尚无原投递意图时，返回完整原准入观察与`ready_for_new_start=true`。已有prepared／unknown／submitted／rejected意图时，只读回原提交状态，返回false；不把原意图接管成新循环，不尝试重新准入或对账／重发。所选SHA须与对应原manifest一致。

该结果仅是顺序只读观察，没有预留、执行或当前服务状态证明；检查后实际start仍保留原两次preflight与attempt-before-send。未使用的实验在检查时若原检查失败，沿原错误明确拒绝。项目修订在观察期间变化拒绝混合结果。密钥、Temporal SDK／服务、模型／GPU和写入intent均不需要。读取沿原SDK-free进程，但原preflight调用Linux的`/usr/bin/git`，因此新check-start沿原Linux／WSL2准入；Windows原生历史读取保持，不假称该原生Git准入已移植。

CLI在可作为新实验候选时exit0，已有原投递时exit1并保留JSON；格式、身份或原准入失败沿原CLI错误exit2。即使exit0也不自动start或批准，不表示真实训练成功。

## 验收步骤

|步骤|完成条件|状态|
|---|---|---|
|A1 实现|原submission owner只读模式、应用入口和薄CLI，原start／恢复行为保持|已实现；产品仅原training／reference_training_submission／CLI三文件|
|A2 接缝|无SDK可检查完整未提交实验；已有prepared／unknown／submitted／rejected明确不可新用且不重发；错SHA、原准入失败、项目漂移拒绝，读取原件保持|源码新两接缝修正测试注入后2通过／1.63秒；原四suite安装54通过／210.12秒，不新建测试文件或CI job|
|A3 安装／实用|新非editable包／283参考核身份；实际CLI在无SDK环境完成原已准备实验检查，记录原文件和数据库保持|最终r2两独立安装643源／wheel／安装逐字一致，283保持；无SDK实际三CLI通过，42原文件／DB保持。只读CPU合同准入，不是训练验收|
|A4 审查／交付|自身原结构模板、该实现片新的fresh-context两轴；更新交付与总计划，普通推送／精确Ref和自己的CI|自身原模板43.254秒approve、新独立本地两轴approve／开放0／0；已精确交付d3c90e7／15blob／完整Ref核同，自己的CI43644626885八job／30步骤全成功，原独立固定发布／终态两轴approve／开放0／0。纯Q4.2计划评审不认证实现|

仅修改原training／reference_training_submission／CLI、原submission测试及手册／记录；reference.py沿原Linux／WSL2限制保持。不提供自动循环、前置fence、预算执行、候选生成、批准、HTTP／页面或训练任务派发；这些分别沿Q4.2后续子节点。本片给循环的有限选择提供真实复用入口，不提前声明其预算或取消已解决。实际过程见[交付](../delivery/2026-11-15-training-start-admission.md)。
