# 控制与执行边界
人：定义训练质量、可改范围、预算与基线发布决定。
Codex协调者：读当前证据，分配方向任务、准备修改和解释结果；原生子agent按需存在。
Symphony：已含GitLab/GitHub WORKFLOW生成、workspace hooks与独立bridge；agent-ready领取，交接后agent-waiting，正式集成工单生成后agent-review。真实部署见symphony/README.md。不是GPU调度器。
Temporal Cloud：保存实验工作流状态、幂等提交请求、轮询/等待、失败恢复和人工集成决定。
现有Slurm/Kubernetes/企业平台：GPU/CPU/拓扑资源租约、整组作业生命周期与实际隔离。
训练runner：执行不可变代码/config；输出原始数据。以run_id/attempt/job_id区分逻辑重试和物理执行。
对象存储/MLflow：原始trace/日志/检查点与长期证据。Git只保存代码、配置、短报告和证据指针。
独立审查者：读取代码和原始证据；不能修改计时/阈值。基线集成人负责组合验证。

## 唯一状态归属
issue：需求、允许范围、人工决定；Temporal：实验生命周期；scheduler：实际job状态；baseline.json：已发布训练配方；artifact store：不可变证据。
重复事件按experiment_id+manifest_sha256查重；读取到旧baseline的结果标STALE，不自动回写当前基线。
LangGraph：若有复杂候选搜索图才接入，输出候选请求；不再拥有GPU作业重试或另一份权威实验状态。

## 快速部署与升级
套件perfctl是单协调主机、受信本地磁盘上的轻量证据台账。不是多租户数据库、身份认证或集群锁；不要把其文件锁当NFS/跨主机协调。
生产事件/元数据可接已有PostgreSQL/MLflow，对象存储负责大文件。Temporal使用Cloud，无需部署本地模型或自建Temporal服务。
一个实验只有一个提交/重试owner。审批接口需要现有SSO/RBAC；workflow signal本身不证明人的身份。
