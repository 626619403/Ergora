# ForgeKernel 原生候选

简体中文 · [English](../../agents/forgekernel.md) · [文档目录](../../README.zh-CN.md)

```bash
bash scripts/install-agent.sh forgekernel
```

默认源码为 `~/.local/share/ergora-tools/forgekernel`，安装固定版本，不安装 CUDA/PyTorch、不登录 Claude、不启动 GPU。依据 [官方说明](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78) 填写原生任务和本地设备配置后绑定：

```json
{
  "tool": "forgekernel",
  "checkout": "/YOUR_HOME/.local/share/ergora-tools/forgekernel",
  "python": "/YOUR_HOME/.local/share/ergora-tools/forgekernel/.venv/bin/python",
  "task": "/YOUR_HOME/projects/my-project/kernel-task"
}
```

```bash
ergora project bind my-project kernel --binding kernel.json --revision CURRENT_REVISION
ergora kernel plan my-project
ergora kernel prepare my-project
ergora kernel list my-project
ergora kernel status my-project CAMPAIGN_ID
ergora kernel run my-project CAMPAIGN_ID --timeout 3600
```

同样操作位于“工作流设计 → 训练优化实验 → 原生 Kernel 候选”。`plan` 检查并展示原生计划；`prepare` 只创建并冻结原生 campaign；`run` 才执行模型/GPU，显式调用也用于继续同一个 campaign；`status` 核对原生状态。Ergora ID 与原生目录映射持久保存，改变当前项目绑定不会改变已有 campaign。

固定版本仅支持 Claude backend；Codex 登录不能替代它。首版适配仅支持 local delivery，SSH delivery 显式拒绝。超时/中断可能留下原生子作业，记录为 `outcome_unknown`，不声称远端或 GPU 已取消。先核对原生目录和旧作业是否停止；需要继续时，提供 `--reconcile-reason '实际核对依据'`，页面也有对应字段。创建结果不明时先 status 从该 ID 的原生目录对账，不能直接创建另一个 campaign 替代。

固定版本检查同时覆盖 `src/forgekernel` 和实际使用的 `scripts`：相对 Git HEAD 的修改、删除或未跟踪文件会使 doctor 显示 `version=unsupported`，并在启动 native driver 前拒绝操作。需要自定义包装脚本时放在 checkout 之外；固定源码检查不保证外部 Python 依赖、CLI 二进制、环境或 OS 隔离。

除原生任务快照，campaign 还固定 models.toml、loop.toml、backends.toml 的 SHA；后续配置漂移会明确拒绝，须恢复对应配置。运行中不要修改共享默认配置；备份与换机须同时保留工具源码、这些配置及 campaign。报告与实际 best/kernel.py 或 best/kernel.cu 的身份会保存；`native_finished` 只描述生成器的完成，`native_failed` 保留上游失败。选择候选提交后，继续用训练模板的 manifest、可信 runner、正确性/质量与配对性能证据，并按 evidence SHA 人工放行。ForgeKernel 的内部 judge、target_met 或报告文字不能直接成为 perfctl PASS。GPU／模型质量须由独立工作负载验收。

新增后端的代码入口是`agents/backends.py`的共有`AgentBackend`合同及本地映射；命令、结果提取、后端专用配置和诊断归各实现，公开配置schema与能力仍只在`components.json`声明。`agents`、正式阶段和doctor复用这些实现，进程监控与取消由`processes`管理。接入步骤和调用关系见[当前架构](../../architecture/module-map.md#agent-backend-integration)。新增专长定义、模板成员和嵌套资源继承仍按[工作流指南](../../definitions/workflows/permissions.md#complete-inheritance-and-conflicts)实施。
