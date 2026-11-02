# F3.3b：显式提交与沿原身份恢复

日期：2026-11-03。分支refactor/architecture-foundations，设计源码基线889d9b49fd12e6e972dfccef58b40d3b306bb5eb。F3.3a最终本地验证及独立核对通过，精确两OS CI进行中。本文件为下一切片设计，尚无F3.3b生产代码或通过结论。

## 范围与已确认事实

仅接入通过统一入口完整创建的开发任务；旧任务仍可只读，不通过提交入口采用。CLI/API共用tasks，保持原doctor、可信检查、IngressLeases及DevelopmentTransport.start。原Transport使用REJECT_DUPLICATE、FAIL和一次workflow尝试，冲突时核对原始spec；它不保证Temporal已清理历史后仍记得旧run。因此不能把NOT_FOUND作为自动重新发送未知提交的依据。

原agentflow.task_action(start)先执行doctor/可信检查，再连接、获取工单租约并调用Transport.start。doctor使用所选运行时的完整依赖元数据并写doctor.json；控制面仅安装temporal SDK不足以运行它。提交子进程使用登记且已核对源码身份的Linux参考运行时及其.venv解释器，指定当前Ergora包路径，不将这些依赖导入Web，也不重新实现doctor或租约。Windows明确要求WSL2；只读status仍保留其独立支持范围。

## 用户接口

- `task start PROJECT TASK_ID --revision N --creation-sha256 SHA`：明确当前项目修订和原创建意图，完整校验冻结合同/绑定/登记投影后提交。响应只证明提交的原workflow/run身份，不表示六阶段成功。
- `task submission PROJECT TASK_ID`：只检查本地操作意图、派发检查点和结果，不查询运行状态、不发起提交。
- `task resume-start PROJECT TASK_ID --revision N --intent-sha256 SHA`：按原意图恢复。只有能够证明尚未进入原Transport.start的准备阶段才可继续派发；已有派发检查点时只沿原workflow ID查询、核对原始输入并补回执，绝不再调用start。
- 对应项目范围API：POST `.../tasks/TASK_ID/start`，GET `.../tasks/TASK_ID/submission`，POST `.../tasks/TASK_ID/resume-start`。写请求沿用同源保护，使用严格revision及摘要。

## 持久意图和派发边界

1. 在当前项目修订保留和执行目录的同ID跨进程锁中，复用创建所有者校验原七文件/创建意图摘要及project/control/registration/执行目录；确认published且内容一致。冻结原spec/角色选择，不重新编译或改绑。
2. 保存不可变start意图，包含原创建摘要、完整spec身份、项目/控制目录/登记身份、原workflow ID和发起修订。位置为登记执行状态目录的Ergora专用操作子树；复用原core.write，不建第二套atomic writer或状态引擎。意图必须先于doctor/工单claim等本次可变操作。
3. 调用原task_action(start)。在固定专用进程内，以原Transport的窄start hook记录派发边界；hook先确认没有无本次提交归属的原有执行，再在实际原start调用之前保存不可变attempt检查点。hook不更改SDK的workflow身份、重复策略或原始spec验证。除该必要检查点外保持原提交算法。
4. 原start返回后保存原workflow/run ID的不可变结果回执，绑定原意图和spec摘要；最后才返回已提交事实。相同start已存在操作时只返回原本地记录，不重发RPC。未知或未派发返回明确状态及非零CLI退出码，不把HTTP接收或RPC异常当成功。
5. 恢复必须提供当前项目修订和原意图SHA。没有attempt检查点，说明本工具的start RPC尚未执行，显式resume可重走原准入/同一租约并继续；已有attempt则只能lookup原workflow ID（或已保存run ID），原输入匹配后补原run回执。NOT_FOUND、连接失败或历史不可用均保留unknown/needs_reconciliation，不能创建新任务或新run。已保存结果继续保持原run ID，不重启关闭运行。

attempt是调用前的写前检查点，不是请求被服务接收的证明。进程可在其写入后、RPC前中断，此时即使NOT_FOUND也保持未知；宁可保留人工对账责任，不自动重新执行。这是同一提交意图下区分“确定尚未调用”和“调用结果未知”的边界。已有原cli-ingress/阶段回执但没有本工具start意图的任务拒绝接管；没有创建意图的legacy任务同样拒绝。

## 所有权和实施顺序

创建记录的完整校验继续由reference_task_creation拥有，为原生提交消费者提供明确的已发布创建读取入口；不复制其16MiB意图/七合同校验。新提交边界拥有操作记录、同ID锁和派发检查点，依赖原task_action/Transport；CLI/Web只传结构化参数。若为真实复用调整创建对象的临时编译目录传入位置，保持原preview/create/resume行为并回归验证，不增加通用Runtime/Task基类。

网络和子进程仍有明确预算。原doctor/start调用链没有启动agent子进程；实际agent执行由已存在的持久worker/executor负责，提交客户端超时不终止或重启它们。若调用链未来增加本地命令，必须先接入现有进程树清理，不能沿用仅回收客户端的假设。失败后通过submission/原ID对账，不自动重试写RPC。

## 验收

- 源码/CLI/API：两开发模板、严格修订和创建摘要、无SDK控制面使用完整参考运行时、未初始化运行时/Windows明确拒绝；原生准入失败不绕过doctor、策略或工单claim。
- 意图保存失败时原提交函数和claim均未调用；准备阶段中断可显式继续同一意图；attempt前/后及结果回执前逐点注入中断，原意图和原角色不变。
- 重复/并发start及丢响应只发出一次真实start调用。attempt已存在时，即使Transport.lookup为NOT_FOUND，也不能再调用start；found原输入不匹配拒绝补回执。关闭run、相同task ID其他项目/控制目录、legacy、原文件/操作记录漂移均明确拒绝或保留未知，不覆盖。
- 新的fresh-context审查包括具体hook必要性、原编译/快照复用、锁/超时、结果真实性及性能边界。最终非editable包/基础与完整运行时组合、适用完整回归/精确两OS CI分别记账。
- 本节点的受控SDK/原生准入夹具不当作真实模型或新六阶段验收。实际两模板新工作流、原history/spec/run固定和导出恢复在F3.4完成；不修改现有用户服务来扩充测试。
