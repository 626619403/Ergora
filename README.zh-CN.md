# Ergora

[English](README.md) · 简体中文

**面向仓库开发和训练实验的多 Agent 协作合同与参考运行时。**

Ergora 将任务目标、角色、允许的变更、人类决定、并行工作、可信检查、独立审查和原始执行证据连接起来。每个业务项目保留自己的 Git 仓库和工单命名空间；任务导出各自的候选分支。

`ergora` CLI 和本地控制台管理项目、Agent 与 Workflow 定义、正式任务、证据及改进候选。正式开发使用现有的 Linux 六阶段参考运行时。[文档](docs/README.zh-CN.md)按任务组织；[当前计划（English）](docs/PLAN.md)记录活动交付及剩余边界。

## 快速开始

在 Linux 上使用 Git、Python 3.11+ 和 venv/pip。克隆到尚不存在的目录：

```bash
git clone --branch main \
  https://github.com/626619403/Ergora.git "$HOME/Ergora"
cd "$HOME/Ergora"
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"

ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset refactoring
ergora serve
```

在运行服务的机器上打开 `http://127.0.0.1:8977`。随包控制台无需 Node 构建或运行时 CDN。原生 Windows 使用 [PowerShell 安装指南](docs/zh-CN/install/windows.md)；完整正式执行需要 Linux/WSL2 和明确受信任的容器。

默认 `control` profile 安装 Web 控制平面。`development` 增加 Temporal SDK；`research` 还增加 GEPA。[安装指南](docs/zh-CN/install/linux.md)介绍各 profile 和离线 wheel。Profile 不会认证 Agent、启动服务或运行训练。复现验收记录时应固定完整 Git 提交；仅凭包版本不能确定源码等价。

## 选择任务

|目标|从这里开始|
|---|---|
|治理仓库、开发大型变更或重构行为|[内置模板旅程](docs/zh-CN/development/templates.md)|
|创建正式开发任务|[冻结准备](docs/zh-CN/development/preparation.md)，然后[预览和创建任务](docs/zh-CN/development/tasks.md)|
|定义专家或嵌套工作流|[Agent 定义](docs/zh-CN/definitions/agents.md)和[工作流组合](docs/zh-CN/definitions/workflows/compose.md)|
|采集和审查精确 PR/MR 材料|[审查材料（English）](docs/review/materials.md)，然后[明确调用审查者并汇总（English）](docs/review/invoke-and-aggregate.md)|
|准备和执行训练实验|[训练概览（English）](docs/training/overview.md)|
|根据原始证据撰写报告|[证据报告](docs/zh-CN/review/evidence-reports.md)|
|将复盘用于后续任务|[改进工作流（English）](docs/improvement/workflow.md)|
|迁移或恢复本地任务栈|[联合备份与恢复](docs/zh-CN/operations/backup-recovery.md)|

正式运行前，先[配置并认证所选后端](docs/zh-CN/agents/configuration.md)、[登记已提交的业务仓库和可信检查](docs/zh-CN/projects/registration.md)，并准备完整模板 manifest。后端原生登录和可选自定义 API provider 配置沿各自实际支持的路径进行；Ergora 不会登录或复制账号状态。

## 正式开发

六阶段保持为 inventory → plan → work → integrate → verify → review。通过[计划批准](docs/zh-CN/development/design-and-approval.md)读取完整计划并批准其精确 SHA。原可信检查和独立审查绑定候选；Agent 的成功消息不授予正式验收。

[提交、状态与恢复](docs/zh-CN/development/run-and-recover.md)保留原 task/run/intent 身份。外部结果不确定时必须对账。仅送达取消请求不能证明进程已停止。[证据与导出](docs/zh-CN/development/evidence-and-export.md)生成本地候选分支供维护者检查；导出不会合并或推送分支。

定义沿结构父链累积祖先 Skill 和上下文，同时逐级收窄权限。有效定义或已保存 manifest 不会执行图。[工作流合同](docs/zh-CN/definitions/workflows/contracts.md)和[权限规则](docs/zh-CN/definitions/workflows/permissions.md)解释支持的投影与限制。

## 当前范围

开发版本适用于在单机上对可信项目进行小规模试用。Linux 和原生 Windows 支持控制平面；[Windows 指南](docs/zh-CN/install/windows.md)说明执行边界。参考执行器使用当前可信容器和 Unix 用户，没有逐 Agent 的操作系统隔离。

训练提案、kernel 建议和证据索引不能证明实际训练质量或性能。明确授权的[有限控制器（English）](docs/training/controllers.md)在同一原始预算下使用冻结候选。自适应候选生成、自动逐轮 profiling、一般 Repeat 和不支持的混合图仍有各自独立的实现与验收要求。

后端可用性、支持模式、认证、实际执行和业务质量是独立事实。不支持的操作会明确失败。源码检查、wheel 安装、真实服务、模型行为、GPU 结果及候选的 [GitHub Actions](https://github.com/626619403/Ergora/actions)各自保留自己的证据。

## 理解与扩展

从[架构（English）](docs/architecture/current.md)、[源码所有权地图（English）](docs/architecture/module-map.md)和[组件变更协议（English）](docs/architecture/component-change-protocols.md)开始。[格式合同（English）](docs/architecture/contracts/formats.md)和[内容身份（English）](docs/architecture/contracts/identities.md)描述各自独立的持久输入与摘要。贡献者应阅读根[协作规则（English）](AGENTS.md)和[当前计划（English）](docs/PLAN.md)。

[冻结的 v2.2 参考 HTML 发行版（中文）](docs/distribution/multi-agent-development-platform.html)保留原 Linux 部署与训练范围；此链接不会使其获得后续控制平面功能。独立的[编辑器比较示例（English）](examples/editor-comparison/README.md)有自己的 Node 构建要求。

Apache-2.0。参见 [LICENSE](LICENSE)、[NOTICE](NOTICE)和[第三方声明（English）](THIRD_PARTY_NOTICES.md)。
