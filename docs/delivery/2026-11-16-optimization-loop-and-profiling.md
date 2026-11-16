# 多轮优化与 Profile 闭环：接续记录

2026-11-16。当前为调查与拆片，源码尚未修改。用户已授权实施多轮实验、自动搜索、真实收益验收，并把 Profile Agent 放入循环；能力未齐时允许手工协调 Agent 执行。权威拆片见[计划](../plans/2026-11-16-optimization-loop-and-profiling.md)。

## 准确起点

开发分支 `refactor/architecture-foundations`，开始于 clean `f8df8af90ae5ad2d9e64047b0b87197ce2bfb432`。其 src／tests／scripts／CI／pyproject 与已核产品 9f3 同一；原 CI、S2、V2a／V2b 证据保持各自候选范围，不认证本后继。

已读根／源码／测试 AGENTS、组件变更协议、当前 PLAN、M6 设计及 V2a／V2b 交付；已核现有性能分析角色声明只读且不运行 profiler。实际 `training_cycles._controller_ready` 和 `reference_training_budget.BudgetedStart.source` 仍显式拒绝 schema3；没有删除 guard 或开放实际训练效果。

## 并行工作与当前证据

- 真实任务由 baseline 子 Agent 在业务项目独立工作树准备；模型算法／结构／尺寸／精度固定，配方与元数据兼容独审、实际测量和清理分别记账。业务配置与资产不写入本框架公共文档。
- 元数据 reviewer 为新的独立上下文；完整来源投影与 spawn／实际 worker 的锁生命周期仍按其报告闭合，未凭格式一致先放行训练。
- Profile 子 Agent 已实际完成小 kernel 工具采集与读回：nsys CUDA／NVTX／OSRT 和 torch.profiler CPU／CUDA／shape／memory；ncu 实际返回 `ERR_NVGPUCTRPERM`，未生成报告。根已通过共享视图核 capability 原件 9,125B／SHA256 `02ad144bb06b226af5363ecef3ea3bf03d6e210fe89a8843070c364cf591bb1f` 和循环合同草案 6,183B／SHA256 `545d2958f1caff0280be0fea5cd6c77bc634cd3e66e2d0f22c01dbbdf0f15a54`；这不是模型 baseline 或新产品能力的验收。CPU 完整调度信息缺失、NCCL 实际工作负载未采集等限制保留。
- 用户允许 Agent 自主探索适合工具并沉淀到版本化 Skill／MCP 等组件，不限上述三项；ncu 放最后。采集者继续验证真实操作与读回，提出候选组件和实际消费者；不直接改写现有只读角色或扩大权限。
- 已核现有 `ergora-training-flow-analyst@1.0.0`、完整 flow-map Skill 和 `training-optimization-v3`：源码算法／依赖／数据流、组件／张量生命周期与可反证冗余分析已经是提案前置，不等于自动运行。已把用户强调的“去冗余优先”接入本轮实际分工与计划。
- 已核原证据报告 Agent 的通用只读四字段合同及本地实验报告指导；新的报告资源作者已读取操作者示例的结构，正做新版本 Skill 与自包含抽象参考，原模板不改。参考的具体优化方法、实验数字与结果不进入公共资源。
- 框架根正在核 M6 晚期 reader／最后启动检查；有限搜索与 Profile 产品合同仍待设计／独审。未跑本片产品测试、安装、真实循环或自己的 CI。

## 接续要求

每次实质变更或运行终态更新本页及 PLAN，记录准确源码／配置／命令、通过与失败、原件位置和剩余工作。独立新片完成前不宣称全自动闭环就绪；手工协调结果保留实际方式。恢复先核在跑进程和原 run，不能换 ID、预算、候选或当前 head 重做。
