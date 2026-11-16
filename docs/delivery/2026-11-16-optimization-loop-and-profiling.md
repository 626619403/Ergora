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

## M6 隔离实现与原始边界回归

已从准确文档head `b71680bc2f2fabf5b10d5499104389391fa23a4f` 建立 `feat/training-cycle-v2-enable-r1` 隔离树，未合入／发布产品。实现留原 controller、worker、budget 和 pure native protocol owner；旧V1及新V2的完整 Workflow class AST均与baseline相同，未复制六阶段或调度循环。主开发分支仍保留已发布的schema3关闭行为。

`m6-r1/red-controller-dispatch-r1` 两个新版本初始提交／丢回复节点在原生产字节上真实失败，原因分别为关闭gate及没有dispatch attempt，原件保留。隔离修正后 `controller-dispatch-r2` 单次14过／104.72秒（runner105.318秒），覆盖两版本及7种原ID恢复事实，179采样自有进程终核absent。`dispatch-boundaries-r3` 单次19过／97.00秒，覆盖完整SDK input／Memo边界、原intent／claim与旧绑定拒绝；这两轮各自绑定当时源码，不转授后续修改。

新原生许可反例 `native-permit-red-r4` 先遇旧测试服务只识别v1父workflow前缀，未到目标边界；修正版本化fixture后 `native-permit-red-r5` 在真实native attempt边界失败：实际executor没有持原父锁的共享许可。新修正由native owner用局部ExitStack覆盖实际callback至process返回，同时保留已有结果早读；`native-permit-r6` 正在跑原5个执行边界的双版本及无效旧绑定／已有结果读回。原反例与所有中间结果保留；尚未认证整片运行、安装、真实服务或两个CPU候选。

原件位于ignored `.ergora/checks/optimization-loop-orchestration/m6-r1/`，包含每轮argv／raw／JUnit与所记录的输入身份。完整前驱／大原件晚处可达、其余最后准入、统一候选、fresh源码审、新安装和真实服务／CPU两轮均是后继门槛；不能仅移除关闭guard就宣称开放。

## 工具与报告资源的追加检查点

Profile扩展后已冻结不可变capability快照SHA256 `ac6834155e7591ce7a55d3d8c07546abca048313cfbe3668fd4ba3b31ad4439e`；根通过共享视图核17,632B及19件引用原件bytes／SHA。早先02ad…便利JSON在追加工具项时被作者覆盖，未留独立raw；该缺口如实保留，未重造旧字节。原始工具命令、trace和reader产物保持；后续每版独立以内容身份保存。

优化报告新资源作者片已fresh两轴approve／0，原@1／旧catalog与资源保持。新非editable wheel SHA256 `9743064d74a72d1836570efc58dc66f8d53d00447da7cf0b060160181fdff82e`，core实际site-packages的678runtime bytes／mode、283参考及新入口冻结消费通过，core无SDK。真实原CLI合成报告149.034645秒成功、四字段／静态HTML和两视图5表68单元格一致；原structure模板39.446412秒成功、两轴approve。初次私有runtime verifier把源码AGENTS算入产品导致的错误保留，只修verifier未改wheel。完整新安装／两次原生调用原件正在由同一fresh reviewer最终补核；普通整合／发布和自己的CI仍待，不认证真实模型性能。
