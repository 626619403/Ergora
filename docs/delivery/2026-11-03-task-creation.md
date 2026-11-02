# F3.2：显式编译、创建与恢复正式开发任务

日期：2026-11-03。分支 `refactor/architecture-foundations`，源码基线 `13e9f33623c5811547bdb43d3b2b0218b62ffda2`。F3.1源码审计已通过，最终350项/36子测试、339文件×两安装和旧任务只读复验已通过；精确两OS CI及最终身份正在收口。本文件先记录下一切片设计，当前没有F3.2生产代码或验收结论。

## 范围与既有能力

原生 `agent_platform.projects.create_task` 已使用portable编译器生成task/policy/binding/compiled/spec/frozen-project六份不可变文件；原 `core.write` 已具备原子写入和相同内容重试。复用这些实现，不复制编译器、JSON身份、DAG检查或六阶段协议。当前缺少统一项目下的显式预览、绑定配置修订的创建、跨多文件中断恢复及CLI/API等价入口。

本切片只创建本地编译合同，不连接Temporal、claim工单或启动执行器。提交、批准、取消、运行对账属于F3.3；导出与完整模板旅程属于F3.4。

## 用户流程与合同

1. 保存版本化任务定义：`schema_version: 1`、`task_id`、`task_type`（两个开发模板）、`issue_id`、原模板`input`，可选`starting_sha`。任务输入与DAG仍由原编译器校验；项目与可信策略来自published统一注册。
2. `task preview PROJECT --definition FILE --revision N`：在隔离进程的临时编译目录复用原create_task，不写实际task store。返回原始spec/编译身份、有效绑定与预览SHA；临时编译材料自动清理，不作为长期状态。
3. `task create`携相同定义、当前revision及已审阅`--preview-sha256`：重新编译并核对精确预览，在任何实际task文件发布前先保存持久意图。预览绑定控制目录、项目修订、注册/有效配置身份和完整编译内容；旧批准或变化的输入/绑定均拒绝。
4. 在原执行状态目录的Ergora专用路径保留不可变创建意图/最终回执，之后按原core.write发布六份原生合同及明确冻结的角色选择；全写完再记回执。跨进程锁保护同一task ID；发布中断可以沿原意图完成，不能重编译成另一份内容或自动采用既有legacy任务。
5. `task creation PROJECT TASK_ID`查看原意图与发布检查；`task resume-create ... --revision CURRENT --intent-sha256 ORIGINAL_SHA`显式按原冻结材料恢复。工具绑定后续修改不改旧任务快照；切换执行目录不自动迁移旧任务。CLI与API共用tasks用例、同源写请求保护及同一错误语义。

重复create只有相同预览/意图和文件才幂等；不同控制目录、其他项目、任务ID碰撞、原生文件被改写或符号链接均明确拒绝。没有自身创建意图的旧任务仍只读或使用原入口恢复，不用“create”接管。

## 所有权与实施顺序

应用编排仍在tasks；reference为调用边界。若编译/发布生命周期需要独立实现文件，使用专用reference创建边界，集中暂存/原生校验/意图和不可变发布，不新增通用插件框架或任务引擎。CLI/Web只传结构化参数，不拼原目录、不导入原全局。复用State的跨进程锁和原core.write/adapter安全读取，避免第二套atomic writer。新增顶层配置仅定义创建接口，不重复原input schema。

先交付原生预览与身份测试，再持久意图/发布/恢复，最后公开CLI/API与两模板验收；各内部检查写入本记录后再做整个F3.2的新独立结构/性能审计。

## 验收

- 两模板的preview不落实际任务文件；相同定义/配置摘要稳定，原编译器拒绝风险/路径/DAG/可信检查或策略不匹配。
- CLI/API create冻结相同spec/角色配置；创建不提交工作流。重复操作不增加作业或改变文件；换输入、旧revision/预览、外来任务与另一控制目录拒绝。
- 每个发布位置注入中断，原意图仍可查；同ID并发及请求丢响应后恢复只完成同一合同。配置变化后显式resume保留原快照；冲突文件不覆盖。
- 无可选SDK基础安装可preview/create/read；Linux/Windows支持子集分别验收。非editable包/冻结参考/适用回归及精确两OS CI、fresh-context独立审计收口后按授权推送。
- 性能只记录原编译/预览、幂等恢复和有界合同I/O的实测条件；不从编译成功推导模型/运行/证据验收。


## 实施前的边界细化

实现预览时在专用子进程的TemporaryDirectory中调用原create_task并读取其六份有界结果；临时state只在该子进程导入原模块前设置，不改Web全局，也不进入真实执行状态目录。返回内容和实际创建都用同一编译流程，不复制portable编译器。准备使用专用reference创建边界集中暂存、原生helpers和发布生命周期，避免把更多写入算法堆进现有资源读取入口。

冻结开发角色快照将由bindings所属的共享函数生成，实际消费者为新tasks创建与原reference_executor首次选择；保持原snapshot字段/内容与六阶段调用不变，现有兼容回归验证。生成器仍不拥有可信检查或计划批准权限。意图放在真实执行状态目录的Ergora专用子树，原任务目录没有平台意图时拒绝自动采用；完整发布后才写回执，提交工作流另属F3.3。

F3.1最终本地归档已独立核对通过，精确CI仍在运行；F3.2先实现与其运行结果无关的预览/创建合同，两个切片始终按各自提交与包身份验证，不把F3.2工作区混入F3.1结论。
