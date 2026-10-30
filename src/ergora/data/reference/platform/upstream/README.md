# 多 agent 开发平台 · v1.3

从这里开始：[平台快速上手](platform/README.md)。本包使用云端模型；在云端 Linux CPU 协调主机运行 worker、网关和执行器，不部署本地模型。

## 选择入口

| 你要做什么 | 先读 |
| --- | --- |
| 填写与复用任务模板 | [可移植契约](platform/PORTABILITY.md) |
| 让其他平台的 agent 委派开发任务 | [A2A 配置与客户端](platform/A2A.md) |
| 从 GitHub/GitLab 工单触发 | [Symphony 接入](symphony/README.md) |
| 升级现有部署 | [迁移与回退](platform/MIGRATION.md) |
| 给现有仓库做首次接入 | [交给 Codex 的接入任务](platform/ONBOARDING.md) |
| 理解设计与参考资料 | [标准和厂商调研](platform/STANDARDS_RESEARCH.md) |
| 查看实测与限制 | [验证记录](platform/VALIDATION.md) |

日常只填写新 task；模板、项目 policy 和 runtime binding 分别维护。Symphony 与 A2A 共用同一 [工单所有权库](platform/INGRESS.md)。A2A completed 只表示待人审候选，不自动合并。

## 安装与自测

以下命令均在本包根目录运行：

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r platform/requirements-a2a.txt
RUN_TEMPORAL_INTEGRATION=1 PYTHONPATH=platform python -m unittest discover -s platform/tests -v
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s symphony/tests -v
```

真实项目还需接入 Codex/CI 阶段执行器、云账号、身份与目录权限。测试使用的 synthetic executor 不能作为真实验收结果。

## 可选训练模块

原有训练优化 v1 保留，未迁移到 A2A。需要时阅读 [原训练快速上手](docs/TRAINING_ROOT_README.md)，其命令仍从本包根目录执行。普通开发任务不需要配置训练 baseline 或 GPU adapter。

ZIP 沿用原 `training-efficiency-kit` 目录名以兼容已有引用；通用开发主入口是本页和 `platform/`。
