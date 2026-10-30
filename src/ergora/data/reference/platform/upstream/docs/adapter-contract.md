# 项目适配器协议
这些入口必须在目标仓库的setup PR实现；套件不能推断真实训练入口、集群凭证和损失语义。

## doctor
读取环境与配置，不启动昂贵任务。输出GPU SKU/topology、软件版本、有效配置、启动命令解析、checkpoint/data指纹、已启用优化和检查入口。不得记录完整环境变量或密钥。

## capture / verify
capture保存允许导出的真实shape、stride和输入指纹；敏感样本留集群，仅将摘要交给云模型。
verify根据契约运行forward/backward/JVP、optimizer更新、分布式归一化、缓存失效、恢复等检查。报告每项PASS/FAIL/NOT_RUN，绑定candidate与manifest。测试代码由独立审查保护。

## measure
由Temporal执行活动提交到已有调度器；不是在agent会话中直接裸跑torchrun。
每个attempt新run_id，稳定idempotency_key对应一次逻辑提交。提交响应丢失先查已有job；不能因agent重启再开一份。
同一pair两臂使用相同样本/增强与初始checkpoint，实际恢复，不连续接着训练。交替AB/BA；基线run不复用作多个独立pair。
profile任务与计分任务分开。窗口内不插入新的每步全局同步；正确处理所有stream的窗口完成端点、最慢rank和源样本账本。
原始输出至少包括：rank窗口elapsed、source样本账本、actual update计数、OOM/重试/skip、A/R/N/host、温度/功率、所有已声明生命周期事件。

## collect
将原始窗口聚合为每个独立run的global_completion_window数据，生成compare_runs.py输入。保留原始rank记录和排除窗口的预先规则。
调用比较器后生成evidence.json：实验/manifest/candidate/baseline绑定、校验项、独立审查、集成验收、质量、比较输入与报告、各artifact哈希。
所有运行（含失败、取消与不确定）原始数据及时归档到artifact store，返回稳定URI；只有完整可校验的bundle成为正式门禁收据。工具perfctl验证记录和重算统计，不证明run真实、权限身份或质量。

## 资源与故障
调度器GPU申请不是完整隔离证明：检查CPU/NUMA、NIC、存储、其他GPU共享带宽和MIG。整组分布式作业统一启动/取消。
取消只针对本experiment的job_id；状态unknown先reconcile，禁止按PID模式批量kill。lease超时不证明进程已死。
容错重启由一层拥有：Temporal做生命周期控制，scheduler adapter核对launcher已拥有的重启策略；agent不再自动重启。
