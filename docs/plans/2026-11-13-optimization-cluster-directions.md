# D2-B2g：集群启动、诊断与恢复子模板

日期：2026-11-13。承接[专家计划](2026-11-13-specialist-presets.md#同事试用入口与剩余专家清单)，基线为`9c84b088146e11eb45bb8c2065c9091526297789`，开始时工作树清洁。B2f自己的CI与独立终核已完成；该基线只比B2f产品增加已审查的试用／结案文档。

## 行为与归属

新增`optimization-cluster-resiliency`配方和`ergora-opt-cluster-resiliency-proposal@1.0.0`根，复用analysis／measurement v2与现有design／profile／measurement三位专家。三个叶继承完整方向context及全部结构祖先，使用原单叶调用与完整前驱手动交接。定义导入由`workflow_definitions.install_preset`统一拥有，CLI与HTTP是既有消费者；没有新分派或执行接口。

方向资料区分唯一rank生成者、实际初始化路径与共享存储，原生experiment／job／cycle身份及unknown对账，确定性日志诊断、模型丰富与重启建议，checkpoint持久化与下一optimizer update恢复，以及框架／调度器／外层预算和采用所有者。缺少真实资料时交付可验证方案与未验项。

本片不安装或执行Slurm、NeMo Run、Submitit、NVRx，不申请资源、不提交／取消／重启作业，不实现第二调度器、归因引擎或恢复账本。带内部模型的Restart Agent完整流程须另验全部父合同；本片不把自己的模型调用视为原生内层调用。

## 范围与资料

产品只新增workflow／instructions／context三文件、catalog一条、既有方向参数测试一项；保留20旧catalog条目、共享v2和542旧产品除catalog外字节、283冻结参考文件。同步README、训练手册、模板旅程、总计划及本片交付。

复用[R8](../research/2026-11-12-optimization-cluster-agents.md)的15份固定资料，257,662B，原HTTP回执／NVRx归档成员长度和SHA已重核，新请求0。Bridge固定`55694838ce73cd23b00ff95bd00512aefb963ce0`，NeMo Run固定`5f39d666bfdf9efca07d274722f7d84a41532a2e`，Submitit固定`d1fd7ac4f357a2c1ac4d5c9d025147617513224a`，NVRx固定`be12a1e3af7eee550abd28a67f85928ef7a9d3ab`。产品采用原创综合，出处URL仅为来源；没有复制上游实现或新增工具权限。

## 可验收节点

|节点|完成条件|状态|
|---|---|---|
|G0 来源与计划|固定原件／回执与基线核准、明确执行边界|完成|
|G1 定义与合同|只读根／catalog可导入，完整context继承及重复导入沿原测试|完成|
|G2 独立安装|非editable wheel、source／installed身份及RECORD／283、原preset suite|r1保留；修正r2的545／两RECORD／283、28项／109.49秒通过|
|G3 实际叶交接|三次真实task-MCP调用、完整祖先读取、measurement完整接收原design／profile|r1保留；修正r2三叶18资源44,924B与手动原前驱通过，measurement为request-changes；仅synthetic资料|
|G4 审查与发布|自身原审查模板、新fresh-context独立两轴、普通推送和精确候选自己的CI|本地两轴通过、SP1/P3关闭／开放0／0；8f0b580已普通推送，精确Git／作者Ref获独立补核；自己的CI43451540232官方Success，八job／30必要步骤及完整SHA日志路径获原独立终核，精确交付终结|

Synthetic资料故意混用两节点、每节点四task且每task四worker，丢失提交回执却拟重提，空／degraded日志给RESTART与异步checkpoint仅入队。调用应分析该配置的32个潜在worker与期望8的冲突，并保留原身份、日志和持久恢复证据缺项。它只验方案与审查行为，不证明真实启动、归因器、集群权限、checkpoint／GPU恢复或收益。

实际结果持续写入[交付记录](../delivery/2026-11-13-optimization-cluster-directions.md)。下一方向为低精度／量化，再独立kernel根；B3与C2继续拥有真实实验及原生嵌套验收。
