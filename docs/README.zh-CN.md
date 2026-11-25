# Ergora 文档

[English](README.md) · 简体中文 · [项目 README](../README.zh-CN.md)

按正在执行的任务选择指南。当前文档以英文为主；明确标注的中文链接指向译文或冻结的来源材料。[当前计划（English）](PLAN.md)区分已交付行为与等待实现或验收的工作。复现结果时应固定完整源码提交。

## 安装与运维

|任务|指南|
|---|---|
|安装控制平面并准备离线 wheel|[Linux/WSL2](zh-CN/install/linux.md) · [Windows/PowerShell](zh-CN/install/windows.md)|
|配置后端登录、工具和有效 binding|[Agent 配置](zh-CN/agents/configuration.md)|
|登记仓库、tracker、角色和可信检查|[项目登记](zh-CN/projects/registration.md)|
|保留持久数据进行升级或重建|[升级](zh-CN/install/upgrades.md)|
|使用本地页面和编辑工作单元草稿|[控制台](zh-CN/operations/console.md)|
|诊断、启动、停止和恢复选定服务|[服务](zh-CN/operations/services.md)|
|建立协调一致的离线恢复点|[备份与恢复](zh-CN/operations/backup-recovery.md)|

安装不会认证 Agent、启动服务或授权任务。Control-home 备份不包含存储在其他位置的执行数据。

## 运行正式开发任务

参照[模板旅程](zh-CN/development/templates.md)进行治理、大型变更和重构，然后使用相应操作：

1. 为所选配方[准备组合、预算和上下文](zh-CN/development/preparation.md)。
2. 根据这些精确输入[预览并创建任务](zh-CN/development/tasks.md)。
3. [提交并观察原运行](zh-CN/development/run-and-recover.md)。
4. 等待批准时，[阅读设计材料并批准精确计划](zh-CN/development/design-and-approval.md)。
5. [读取原始证据、校验交接并导出精确候选](zh-CN/development/evidence-and-export.md)。

[工单上下文](zh-CN/projects/issues.md)冻结明确的来源观察。[候选操作](zh-CN/projects/candidate-actions.md)涵盖原候选观察、明确评论/标签和已有 PR/MR 关联；这些操作不会合并或批准远端变更。

## 定义 Agent 和工作流

|任务|指南|
|---|---|
|选择后端并检查实际角色/模式支持|[后端选择](zh-CN/agents/backends.md)|
|使用可选原生集成|[DeepSeek Harness](zh-CN/agents/deepseek-harness.md) · [正式六阶段桥接](zh-CN/agents/formal-execution.md) · [ForgeKernel](zh-CN/agents/forgekernel.md)|
|创建或派生不可变专家定义|[Agent 定义](zh-CN/definitions/agents.md)|
|修订/读取完整资源与附件|[共享定义资源](zh-CN/definitions/resources.md)|
|导入、组合、预览和冻结工作流|[组合](zh-CN/definitions/workflows/compose.md)|
|理解数据端口、工作单元和审查职责|[工作流合同](zh-CN/definitions/workflows/contracts.md)|
|检查祖先资源、权限和静态预算|[继承与权限](zh-CN/definitions/workflows/permissions.md)|
|发布精确新版本并分享依赖|[工作流修订](zh-CN/definitions/workflows/revisions.md)|
|明确调用/检查一个受支持的叶及固定 MCP 资源|[叶调用](zh-CN/definitions/workflows/leaf-calls.md)|

静态预览或已安装 preset 不会执行图。逐 binding 的 reasoning 字段请求受支持的级别，不能证明实际使用了该级别。

## 审查和解释原始证据

从[精确本地/PR/MR 材料（English）](review/materials.md)开始，再[调用并汇总冻结的审查者（English）](review/invoke-and-aggregate.md)。[训练代码审查（English）](review/training.md)选择预训练/后训练专家。[证据报告](zh-CN/review/evidence-reports.md)将原始材料转成可读 Markdown/HTML，并明确覆盖限制。

## 训练与测量

从[训练概览和 CPU 合同演示（English）](training/overview.md)开始，继续阅读[实验准备（English）](training/prepare-experiments.md)、[原执行与恢复（English）](training/execution.md)、[有限控制器授权（English）](training/controllers.md)或[证据/轮次/精确批准（English）](training/evidence-and-approval.md)。执行未成功时，可通过[保留归档读取（English）](training/evidence-and-approval.md#read-a-retained-local-archive-after-unsuccessful-execution)核对原实验保存的本地归档。

[专家提案（English）](training/proposals.md)将源码流程与瓶颈分析映射到实验合同；[优化专家（English）](training/specialists.md)选择聚焦方向。提案叶和合成 CPU 检查不能认证真实 GPU 质量或性能。

## 改进后续任务

在 campaign 中保存精确的操作员计划，通过原队列上的 Worker 停止计划，或观察已授权的固定检查。工作流状态不可用时，在线状态可从原 Temporal History 核对已保存的观察回执，以及携带 Job 通过结果的定时 Activity 完成记录。[Campaign 操作指南（English）](improvement/campaigns.md) · [停止原计划（English）](improvement/campaigns.md#stop-the-original-campaign-plan) · [定时回读（English）](improvement/campaigns.md#allow-one-timed-readback-of-a-waiting-check)

[改进工作流（English）](improvement/workflow.md)连接[来源绑定的复盘候选](zh-CN/improvement/retrospectives.md)、[项目记忆与可选 ReMe](zh-CN/improvement/memory.md)、[可信 Skill 评价/采用（English）](improvement/skills-and-evaluation.md)及[有界调研/调度（English）](improvement/research-and-schedules.md)。生成、评价、采用和新任务冻结上下文是独立操作。

## 理解和修改实现

先看[框架结构图与运行路径（English）](architecture/framework-tour.md)，了解静态定义与快照、独立工作流图、原生会话回执、正式六阶段交付、训练、campaign 操作者记录和评估。再阅读[架构概览（English）](architecture/current.md)、[源码所有权地图（English）](architecture/module-map.md)、[组件变更协议（English）](architecture/component-change-protocols.md)和[领域词汇表（English）](../CONTEXT.md)。

|参考|用途|
|---|---|
|[结构化格式（English）](architecture/contracts/formats.md) · [内容身份（English）](architecture/contracts/identities.md)|版本化记录及各自独立的编码/摘要合同|
|[开发执行（English）](architecture/execution/development.md) · [训练执行（English）](architecture/execution/training.md)|原状态、预算、恢复和进程所有权|
|[CLI/HTTP/控制台（English）](architecture/interfaces.md)|传输与异步视图所有权|
|[原生参考访问（English）](architecture/reference-boundary.md)|固定源码、原生进程和迁移职责|
|[数据库迁移（English）](architecture/state-migrations.md) · [测试](zh-CN/architecture/testing.md)|持久数据恢复与尊重证据边界的检查|
|[架构决策](architecture/decisions/)|带日期的决策，当前所有者另行链接|

修改仓库前遵循根[协作规则（English）](../AGENTS.md)和活动[计划（English）](PLAN.md)。[编辑器比较（English）](../examples/editor-comparison/README.md)是独立原型。[冻结的 v2.2 发行版（中文）](distribution/multi-agent-development-platform.html)及随包参考手册保留原范围；它们是来源产物，并非当前指南的译文。

[第三方声明（English）](../THIRD_PARTY_NOTICES.md)
