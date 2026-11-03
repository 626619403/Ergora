# F3.3b：显式提交与沿原身份恢复

日期：2026-11-03。分支refactor/architecture-foundations，设计源码基线889d9b49fd12e6e972dfccef58b40d3b306bb5eb。F3.3a最终本地验证及独立核对通过，精确两OS CI进行中。当前F3.3b已实现CLI/API与专用提交边界，定向验证进行中，尚无完成或独立审查通过结论。

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


## 实现进度与边界补核

当前reference_task_submission复用_Creation.published对创建意图/登记/七合同的完整校验；临时编译目录只传给原创建compile/run，不为读取持有无关临时资源。提交、提交记录读取和恢复全部使用登记完整Linux参考环境的.venv解释器；控制面本身不导入SDK，submission虽然只读本地记录，仍依赖该参考环境的SDK以复用原workflow_id。Windows明确报WSL2要求，不声称本切片原生执行。没有新增依赖或修改冻结283文件。

原task_action保留doctor/策略/可信检查/claim，专用进程内的窄Transport继承仅在原start前执行ownership查询并保存attempt。意图先于本次doctor/claim。没有attempt的明确resume可继续；已有attempt只lookup原spec并补原run回执，NOT_FOUND保留unknown、不重发。重复start只读保存状态；项目修订通过父进程SQLite写保留，创建/提交共享原同ID锁。

自查补足一个恢复反例：首次发现既有原run时保存不可变rejection（绑定同意图/spec/run），不保存本次attempt。后续resume保持rejected，即使该run历史消失也不能当作尚未派发来开始新执行。拒绝记录与意图/attempt/result一并校验；不能把它当成本次submitted回执。此记录是已知所有权冲突的事实，不是另一套任务状态机。

已新增持久SDK端口夹具，实际调用原task_action、IngressLeases和DevelopmentTransport；只替换doctor外部依赖结果、网络client及定点文件中断，覆盖两模板、重复/并发/父响应丢失、各写前写后中断、准入拒绝/离线、旧运行及未知NOT_FOUND、原输入冲突、修订/摘要/文件漂移和CLI/API一致。同受控服务返回的run仅证明协议，真实模型和六阶段由F3.4补验。首轮定向验证进行中，后续源码复审、最终包/性能/完整回归和精确两OS CI分别登记。


首轮源码定向（task_submission + task_creation + architecture_boundaries）68 passed，140.19秒，原始source-first.log保留。自查随后把意图/attempt/result/rejection比较收敛为原canonical SHA以严格区分JSON数值和布尔值；补原始输入碰撞的持久拒绝、丢失意图的孤立记录拒绝，以及跨平台WSL2/缺完整环境反例。新定向和审计待进行，不将首轮结果移用于后续修改。


最新源码定向44 passed（136.65秒，task_submission及architecture_boundaries），覆盖上述最终边界。独立审查者f3_task_submission_review已开始fresh-context结构/性能/恢复语义审计；非editable包构建完成，基础/开发安装正在核对。


## 独立审计发现与修正（待复审）

审查者确认P1竞争窗口：预查NOT_FOUND之后，原Transport.start会将WorkflowAlreadyStartedError当成可兼容重入并返回其他入口的run。另有P2：原lookup使用Python相等比较，不能区分原history的true/1/1.0。实际失败探针保留在[审查报告](2026-11-03-task-submission-review.md)。

修正不改冻结Transport：专用客户端的start窄代理为原SDK调用添加`ergora.submission_sha256` memo（原意图SHA），保留spec/workflow ID/队列/一次尝试/重复策略；AlreadyStarted保存start_conflict拒绝，不走原兼容采用。未知恢复先按原lookup验证输入，再核对describe响应已有的memo；缺失或不同不补本次回执，即使冲突拒绝记录保存失败也不能采用无本次标记的run。memo只是同一可信本地协调边界的归属关联，不替代用户认证或权限。固定原Workflow没有upsert_memo，SDK1.34的description.memo仅本地解码，不增加RPC；F3.4仍需真实服务验证。

严格原始JSON比较由reference_task_runtime.VerifiedSpecClient拥有，原生只读status与submission两处真实消费者共用。它仅代理Transport的原始spec解码，保留单次history读取；返回的SDK description仍持自己的原converter，memo等数据不经过spec比较。补boolean/float历史反例，同时修正F3.3a只读入口的同源问题。native task_spec再次读盘时在原task_action的局部输入hook核意图spec SHA，漂移在doctor/claim之前拒绝；不通过额外读取或重编译改变角色。两个局部hook只在专用进程、finally恢复。

修正前e285…wheel343文件×两安装一致，冻结283通过；其完整Linux432 passed、19 skipped、36子测试（371.99秒），无SDK基础两模板72次CLI旅程及本地查询测量通过。这些仅保留为初版证据，**不适用于修正后的源码**。新定向、发行身份、性能与完整回归分别存review-fixed-*，等待独立复审；当前不标完成。


修正版源码定向71 passed（192.48秒）；审查者独立12项及原失败探针已复核，竞争现在rejected，丢拒绝记录时无memo仍unknown，bool/1.0均拒绝且没有重发，实际SDK description.memo本地解码与只读audit通过。两finding关闭，最终归档审计待完成。修正版wheel SHA256 f8d92f51317a3b3d6f7466ab1bc38b97a4bd4de6658ab06358580bf1d735c44e，343文件×源码/wheel/开发及无SDK基础两安装一致，冻结283保持；完整适用回归和新72次基础旅程/测量正在运行。将推送已源码复审候选以触发精确两OSCI，当前尚未标完成。


## 修正版本地发行验收

中断恢复后核对：f8d92f…最终包的适用完整Linux回归441 passed、19 skipped、36 subtests passed（397.38秒），原始review-fixed-wheel-regression.log。两模板无SDK基础控制面旅程72次CLI全部通过；完整SDK只在所登记原生解释器中使用。每模板首次start使用受控SDK（各一次），其后10次×submission/start/resume-start调用真实发行CLI、只读取已保存原回执，没有RPC、doctor或start重发；原任务/操作文件字节保持。

本地重复路径的CLI端到端中位为：repository-governance的submission/start/resume分别1068.34/1000.21/1024.68ms，large-change分别1068.74/1066.56/1079.09ms，最大1127.86ms。包含CLI/子进程/SDK启动和合同预检，并行完整回归；仅说明该条件下本地记录路径成本，不是实际RPC/模型/吞吐或优化收益。SQLite跨项目长锁争用未实测，现有15秒busy预算的串行权衡按手册保留，不能由这些快速重复调用推导为无影响。

71项源码定向、独立12项/失败重放、343文件×两安装与上述完整包回归及旅程分别记账，初版e285…证据不混用。新的最终本地归档独立核对已发起；精确两OSCI和远端身份待推送后核验。下一项[F3.3c批准/取消](2026-11-03-task-decisions.md)已分两段调查，尚未生产实现；真实服务原history/memo、两模板六阶段和导出仍由F3.4验收。
