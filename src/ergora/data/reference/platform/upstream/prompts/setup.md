# 仓库接入指令
请在当前训练仓库接入本套件，模板目录为 <ABS_KIT_PATH>。保留现有框架与未提交工作；先创建设置分支，不直接改生产配方。
1. 调查实际启动器、最终生效配置、数据/权重来源、四目标/多反向/GAS/更新映射、已启用优化与旧失败记录；建立 workload-contract.md 与架构地图。
2. 记录安装版本、GPU SKU、拓扑、驱动、CUDA、PyTorch、NCCL、DeepSpeed/Megatron、编译与精度设置；固定已验证镜像或锁文件。不要为套件整体升级训练栈。
3. 适配 adapters/project_adapter.py 的 doctor/capture/verify/measure/collect；所有未实现入口必须失败。doctor不启动昂贵训练。
4. 适配现有Slurm/Kubernetes/企业平台作业API；只让一个runner身份提交/查询/取消。GPU资源使用平台租约；完整验收隔离CPU、NIC、存储干扰。
5. 实现计时：窗口入口对齐、完成端点同步，窗口内保留正常异步；跨rank聚合max elapsed与源样本账本。保存原始窗口与rank数据，生成compare_runs.py要求的配对记录。
6. 将模板AGENTS约定合并到现有文件；保护baseline、计时/验证脚本和审批记录；CI跑纯CPU工具自测与项目必要检查。
7. 配置Temporal Cloud实验工作流（见temporal/README），将不可变manifest哈希与experiment_id接入集群adapter。先用fake adapter测试幂等、取消、断网、重启、拒绝过期批准，再用一个真实小作业验证。
8. 配置symphony/README.md中的GitLab/GitHub原生WORKFLOW与独立bridge；使用agent-ready/waiting/review/blocked标签。bridge做准入与幂等交接，Symphony不能重复提交GPU作业。
9. 在小任务上跑通：固定基线→一个可逆候选→独立正确性→无profiler配对→证据归档→人工确认→新基线。提交设置PR并报告未适配项。
不要宣称已经提速。没有真实GPU结果时只报告系统接入与测试结果。
