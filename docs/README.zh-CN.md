# Ergora 文档

[English（默认）](README.md) · 简体中文 · [项目 README](../README.zh-CN.md)

先读[项目概览与快速试用](../README.zh-CN.md#快速试用)，再按下表选择指南。当前功能文档跟随 `main`；冻结的 v2.2 参考发行保留其文档所述范围。复现记录中的结果时，应固定完整源码提交。

已完成的语言对默认使用英文。下表标明各指南提供的语言；当前命令和恢复义务由对应指南拥有。

## 安装与操作

|指南|适用内容|语言状态|
|---|---|---|
|[安装与日常使用](zh-CN/USAGE.md)|安装组合／离线 wheel、Agent 认证、正式任务操作、工单来源、服务与恢复|[English](USAGE.md) / [中文](zh-CN/USAGE.md)|
|[Windows](zh-CN/WINDOWS.md)|原生控制面、PowerShell 安装、交接核验和 WSL2 执行边界|[English](WINDOWS.md) / [中文](zh-CN/WINDOWS.md)|
|[项目](zh-CN/PROJECTS.md)|统一登记、修订、有效绑定及显式采用旧参考登记|[English](PROJECTS.md) / [中文](zh-CN/PROJECTS.md)|
|[备份与恢复](zh-CN/BACKUP_RECOVERY.md) · [English](BACKUP_RECOVERY.md)|控制／执行／Temporal／Git 联合离线快照与原路径恢复|中英文完整对照|
|[测试维护](zh-CN/TESTING.md) · [English](TESTING.md)|安装后 wheel 检查、CI 选择、collection 覆盖与原失败日志|中英文完整对照|

控制面安装不会启动服务、认证模型或启用可信参考执行器。控制 home 备份不包含存放在其他目录的执行数据。凭据与本地运行数据应留在公开文档之外。

## 定义 Agent 与工作流

|指南|适用内容|语言状态|
|---|---|---|
|[模板入门旅程](zh-CN/TEMPLATE_WALKTHROUGHS.md)|治理／重构／训练提案的完整旅程与 manifest|[English](TEMPLATE_WALKTHROUGHS.md) / [中文](zh-CN/TEMPLATE_WALKTHROUGHS.md)|
|[Agent 定义](zh-CN/AGENT_DEFINITIONS.md)|独立专家定义、资源与不可变版本|[English](AGENT_DEFINITIONS.md) / [中文](zh-CN/AGENT_DEFINITIONS.md)|
|[Agent 后端](zh-CN/AGENT_BACKENDS.md)|真实角色／模式支持、后端配置、正式执行和会话恢复|[English](AGENT_BACKENDS.md) / [中文](zh-CN/AGENT_BACKENDS.md)|
|[工作流定义](zh-CN/WORKFLOW_DEFINITIONS.md)|嵌套引用、资源继承、权限、图编译、manifest 和显式叶调用|[English](WORKFLOW_DEFINITIONS.md) / [中文](zh-CN/WORKFLOW_DEFINITIONS.md)|

有效定义、preset 安装或预览不等于执行整张图。正式开发保留受支持的六阶段运行时。逐 binding 的推理设置请求所选后端／模型支持的等级，不证明模型实际使用了该等级。自动按任务选档仍属后续设计。

## 审查、训练、报告与改进

|指南|适用内容|语言状态|
|---|---|---|
|[本地审查](LOCAL_REVIEW.md)|精确 Git／需求／上下文材料包、离线核验和显式来源采集|中文；第四批完成完整双语|
|[预训练与后训练审查](TRAINING_REVIEW.md)|领域审查者与 CPU 合同示例|中文；第四批完成完整双语|
|[训练](TRAINING.md)|workload／baseline／runner、实验、证据、批准、受管执行及优化提案|中文；第四批完成完整双语|
|[完整改进旅程](IMPROVEMENT_WORKFLOW.md)|来源绑定的记忆／Skill／Workflow 候选、评价、明确采用和新任务冻结|中文；第四批完成完整双语|
|[工具接入](INTEGRATIONS.md)|工具绑定、记忆投影、GEPA、有界研究与调度|中文；第四批完成完整双语|
|[证据报告](zh-CN/EVIDENCE_REPORTS.md) · [English](EVIDENCE_REPORTS.md)|只读报告作者、原来源／覆盖记录及自包含 HTML 导出|中英文完整对照|

训练提案与证据索引不授权实验，也不证明 GPU 质量／性能。显式授权的训练控制器在同一个原预算内执行冻结的有限候选；自适应搜索、设计关卡与通用 Repeat 仍由持续计划跟踪。外部工单评论／标签、候选采用及发布仍使用各自明确的操作／批准流程。

## 理解与扩展实现

以下架构指南说明当前语义owner与合同；持续计划记录当前检查和剩余工作。

|指南|Owner 与用途|
|---|---|
|[当前架构](architecture/current.md)|模块／调用者／数据边界和实际支持的扩展点|
|[组件变更协议](architecture/component-change-protocols.md)|改动组件前的构造／配置、所有权、生命周期、恢复和相关验证|
|[合同与身份](architecture/contracts-and-identities.md)|版本 schema、完整资源身份及不同摘要合同|
|[reference 边界](architecture/reference-boundary.md)|冻结运行时访问与逐步迁移职责|
|[状态迁移](architecture/state-migrations.md)|数据库兼容、备份与回退|
|[领域词汇表](../CONTEXT.md)|项目术语与原领域 owner|

修改仓库代码前，先读根[合作规则](../AGENTS.md)及当前计划。[编辑器比较示例](../examples/editor-comparison/README.md)是独立设计实验，有自己的构建要求。冻结 preset／reference 指令和第三方资料属于产品／来源资产，不做无差别文档翻译。

## 当前工作

[当前计划](PLAN.md)与[活动交付](delivery/2026-11-19-main-branch-integration.md)记录实际检查和剩余工作。[架构决定](architecture/decisions/)保留其日期所对应的设计背景。[冻结参考HTML](distribution/multi-agent-development-platform.html)仍是自包含v2.2 Linux发行，具有自身原始部署和训练手册范围。

[第三方说明](../THIRD_PARTY_NOTICES.md)
