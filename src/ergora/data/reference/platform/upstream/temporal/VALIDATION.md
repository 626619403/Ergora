# 实际验证记录

验证日期：2026-10-26。环境：Python 3.12.14；实际安装 `temporalio==1.34.0`。SDK 安装在独立临时目录，未改变项目运行环境。

|验证|结果|
|---|---|
|SDK 下载/导入、Workflow sandbox prepare|通过|
|`python -m compileall -q perf_temporal tests`|通过|
|`python -m perf_temporal.client --help`|通过|
|7 项单元/协议测试|通过|
|10 项 Temporal 临时测试服务集成测试|通过：人工等待/释放、signal/native取消、GPU失败不重跑、排队总窗口、submit/poll终失败时取消仍清理、清理双故障、坏receipt后换新receipt、原审批deadline不延长|

最终完整执行 **17 项测试，全部通过**（7 项协议/单元测试，10 项集成测试）。集成测试真实运行 Temporal SDK 的 ephemeral time-skipping test server；cluster adapter、审批服务与工单服务均是测试替身。未连接真实 Temporal Cloud、GPU 集群、artifact store、SSO 或工单系统；不能把这些测试视作生产适配验证。

独立审查后的三处修正及回归证据：

1. `max_run_seconds` 明确为提交/lookup确认后的 QUEUED+RUNNING 总窗口；测试全程QUEUED也会超时取消，结果包含正确原因。scheduler实际执行硬walltime仍由runner模板独立保证。
2. cancel signal在submit/poll期间到达且activity最终失败，仍fence并精确取消；测试同时验证原始控制面错误保留。若取消也失败，返回CANCEL_UNCONFIRMED并保留两段错误，不重复重提GPU作业。
3. 专用 `ApprovalRejected` 表示建单副作用前的确定审批拒绝；坏receipt后回到原等待窗口，新的正确receipt可建单，同一receipt不重复校验，GPU提交计数仍为1。deadline测试检查durable history内两次timer及workflow完成时点，证明拒绝没有重置原60秒审批窗口；不依赖测试服务可能额外快进的全局虚拟时钟。

重现命令（在隔离 virtualenv 中安装 requirements 后）：

```bash
python -m compileall -q perf_temporal tests
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s tests -v
```

集成测试服务输出一条能力告警：该测试服务没有公告 `activity_failure_include_heartbeat`，SDK 因而不能保证 activity 失败时保留最近 heartbeat details。本模板使用短 activity，不依赖 heartbeat 传递运行进度；这条测试服务告警不能替代真实 Cloud 兼容性检查。

生产接入验收仍必须验证：runner 原子幂等与失响应恢复、提交/取消并发 fencing、跨 worker 进程恢复、scheduler 硬 walltime、分布式 rank 组取消、独立数值门禁、外部审批 receipt 的真实身份与角色核验、基线漂移拒绝、真实工单幂等、Cloud 网络/密钥/RBAC与告警。任何一项未完成时保留 fail-closed 状态。
