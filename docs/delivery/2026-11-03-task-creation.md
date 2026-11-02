# F3.2：显式编译、创建与恢复正式开发任务

日期：2026-11-03。分支 `refactor/architecture-foundations`，源码基线 `44e98158cdc08e15bc848e0347469fee132024ea`。F3.1完整交付及独立最终审查已通过。本切片进入实现和定向验证，尚未完成发行验收或独立审计。

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

实现预览时在父进程管理的TemporaryDirectory中由专用子进程调用原create_task并读取其六份有界结果；临时state只在该子进程导入原模块前设置，不改Web全局，也不进入真实执行状态目录。返回内容和实际创建都用同一编译流程，不复制portable编译器。准备使用专用reference创建边界集中暂存、原生helpers和发布生命周期，避免把更多写入算法堆进现有资源读取入口。

冻结开发角色快照将由bindings所属的共享函数生成，实际消费者为新tasks创建与原reference_executor首次选择；保持原snapshot字段/内容与六阶段调用不变，现有兼容回归验证。生成器仍不拥有可信检查或计划批准权限。意图放在真实执行状态目录的Ergora专用子树，原任务目录没有平台意图时拒绝自动采用；完整发布后才写回执，提交工作流另属F3.3。

F3.1最终本地归档已独立核对通过，精确CI仍在运行；F3.2先实现与其运行结果无关的预览/创建合同，两个切片始终按各自提交与包身份验证，不把F3.2工作区混入F3.1结论。


## 实现进度

已实现版本化外层定义、tasks共享用例、CLI/API的preview/create/creation/resume-create。专用reference_task_creation边界集中原生create_task/portable复用、安全读取、不可变意图/文件/结果及同ID跨进程锁。临时编译目录由父进程管理，子进程导入前将STATE指向该目录；超时回收子进程后仍清理材料。真实发布路径只取登记执行目录，不调用Temporal或工单/模型。

bindings.development_snapshot为tasks与原reference_executor两个真实消费者共享，保持旧快照字段及六阶段执行；架构测试明确只允许新专用原生边界导入reference内部。create/resume通过原SQLite写保留防止项目revision在发布中变更，同时以执行目录中task ID锁协调发布；不增表、不新增任务引擎。七份合同中绑定最先、spec最后发布；意图在第一份真实合同之前写入，回执在全部完成后写入。

初轮26项创建定向通过（15.37秒）；相关读取/配置/边界/原六阶段联合检查82项通过（102.35秒）。覆盖两模板、不落真实目录的稳定预览、明确摘要与修订、八个发布中断位置、意图存储失败、变更绑定后原快照恢复且禁止重编译、并发同ID/丢响应、外来控制目录、legacy/内容冲突、不安全意图以及CLI/API同源写保护和等价响应。联合检查期间仅进一步澄清新输出字段为execution_started_by_operation，最终定向与非editable包验证仍待进行；不从本地发布状态推断实际任务未运行。

公共使用/项目/Agent手册、README及当前架构/边界图已同步。辅助证据目录为.ergora/checks/f3-task-creation/。新fresh-context独立结构/性能审计将与非editable包、基础无SDK旅程/性能、适用完整回归和精确两OS CI分别记账。完整F3仍需F3.3运行操作和F3.4综合旅程。


## 初版发行验证与独立发现

初版wheel SHA256为15bd9d3cc38aef5cd81b463956379453947dda820bc9ef61269291b12d86f67c，341文件×源码/wheel/开发及基础两安装一致，冻结283文件通过。初版完整适用Linux回归376 passed、19 skipped、36 subtests passed（196.74秒）。无Web/Temporal/GEPA的Python3.12基础安装通过两模板127次CLI旅程：稳定预览不写真实task store、创建/幂等重试/恢复/读取合同一致且原字节保留，没有启动workflow。原始包、日志和journey-performance.py/json/log保留为初版证据，不能代替修正后身份。

独立审计复现P2：合法聚合意图可以超过1MiB，而原core.write在既有意图重试比较时经core.read使用单合同1MiB限制，导致首建成功后无法重试/恢复。修正为在同ID锁下load/validate已保存意图后复用原始文件，首次创建才write意图；不放大其他合同读取上限。新增大于1MiB合法意图的完整首建和中断恢复回归，验证每份原生合同仍不超过1MiB、意图原字节保留。修正后将统一重包/复验基础旅程及性能/适用全回归，再收口精确CI和独立审查。


## 修正后源码与包身份

大意图修正后，作者源码定向36项通过（16.25秒），[独立复审](2026-11-03-task-creation-review.md)另跑36项通过（15.69秒），P2关闭且无未解决源码finding。最终wheel SHA256为b361813de921eca66eb7f3eae0b896f5bd4ce728b5fd3a3f84ef8db646a18ce9；341文件×源码/wheel/开发及基础两安装一致。修正后的完整适用Linux回归与127次CLI基础旅程/测量运行中，精确两OS CI及最终审计身份仍待完成。准备按授权推送源码已复审候选以触发CI；推送不代表本切片已完成。
