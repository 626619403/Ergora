# 训练优化与持续改进

训练模板负责固定 workload、实验输入、正确性要求、基线和候选证据。实际训练、kernel 生成及设备访问由所选工具和项目环境完成。Ergora 的项目记忆、Skill 候选和资料观察可以先独立使用，不代表模型训练或性能已经得到改善。

Windows 原生可设计训练模板、运行提案角色并管理记忆 / Skill；ForgeKernel、mini 驱动及完整参考实验执行请使用 WSL2/Linux，可信参考执行器还要求 Linux 容器。原生安装不会配置 CUDA、GPU 或这些参考服务，详见 [Windows 手册](WINDOWS.md)。

## 准备工作

```bash
ergora templates copy training-optimization ./training-task
ergora project add my-project --repo "$HOME/projects/my-project"
```

也可在控制台“工作流设计”中选择“训练优化实验”，预览和下载文件。模板包括 `workload-contract.md`、`baseline.json`、`experiment.json`、runner 示例、hypothesis、result、evidence、attestation 和负结果记录。先将其中的占位内容替换为真实配置，再批准合同与精确实验。

固定模型 / 代码版本、数据身份、随机种子、数值精度、并行布局、设备、计时区间、重复次数及正确性阈值。训练环境与数据由项目准备；安装控制台不会安装 CUDA、PyTorch 或申请 GPU。性能候选同时满足项目正确性和质量约束后才有比较意义。

## 参考实验执行

完整参考发行提供 `agentflow training`、可信 runner 与 perfctl 门禁。按 [完整训练优化参考手册](../src/ergora/data/reference/platform/docs/TRAINING.md) 的参数执行：

```text
init / runner-add → prepare → worker-start → start
→ 选定精确实验并以 manifest SHA 执行 run-local
→ 可信证据与统计复验 → 人工批准 evidence SHA
→ 该项目的集成 / 复验任务
```

`run-local` 逐实验显式执行；没有常驻训练队列消费者。审批、结果、取消和恢复沿用原实验身份。未知结果需要对账，不直接用新 ID 重跑。候选模型或 Agent 的报告不能替代可信 runner 的验证；实验失败和负结果也要保存。

## 记忆、Skill 与资料

- 将已核对的项目约定保存为带来源和修订的记忆；`ergora agent run --recall QUERY` 将所选项目记忆作为可核对的观察传入。
- 用标准 Skill 目录保存操作知识。手动或 GEPA 产生候选后，用固定 train / validation / holdout 评价，核对正确性、报告成本和泛化限制，再明确采用。它优化文本资产，不更新模型权重。
- 对明确的官方文档和论文来源配置有界 URL 观察；资料变化生成待审提案。Temporal Schedule 可持久触发，默认暂停，每次有独立预算。

具体 JSON 输入 / 输出、CLI、ReMe 与 GEPA 接入见 [INTEGRATIONS.md](INTEGRATIONS.md)。基础安装、控制台和备份见 [USAGE.md](USAGE.md)。

## 专用 Agent 的接入方向

模板以 `agent-contract.json` 声明 experiment-planner、performance-analyst 和 kernel-tuner 的能力与产物；具体 Agent 由项目角色绑定选择。参数搜索可由项目 runner 接 Optuna 等现成工具，可信实验执行和数值/质量/性能复验不交给生成器。

[OpenBMB/ForgeKernel](https://github.com/OpenBMB/ForgeKernel) 提供可选固定版本的原生 campaign 适配。先安装独立工具环境、配置本地任务与设备，再通过 `ergora kernel plan/prepare/status/run` 或训练页面操作。固定版本仅支持 Claude backend；计划检查与创建 campaign 不调用模型/GPU。完整配置、继续执行和结果不明时的对账步骤见 [Agent 手册](AGENT_BACKENDS.md#forgekernel-原生候选)。

生成器原生报告只作为候选材料，仍需提交候选代码、冻结实验 manifest，并运行上述可信证据门禁。KDA、ForgeKernel、mini-swe-agent 等的比较和许可证见 [三模板选型](research/2026-10-31-template-agents.md)；CPU 接口验证不能证明 GPU 性能提升。
