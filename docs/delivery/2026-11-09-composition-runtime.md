# AC3c.3：版本化运行桥与正式审查调用

日期：2026-11-09。状态：CR1精确交付完成，细节见[独立记录](2026-11-09-composition-workflow-inputs.md)；CR2a/CR2b已按各自精确候选、双OS CI及独立终结交付，CR3a精确d8668a4/双OS CI42540516079及独立终结完成；CR3b内部执行精确6826047/双OS CI42545445322及独立远端终结完成。CR3c公开有限单叶入口已实现，真实三任务Temporal旅程/自身模板通过，最终包内合同与独立交付在途；CR4尚未完成。依赖AC3c.2完整信封交付；当前只支持单个纯只读review叶，其他形状提交明确拒绝。本文件是后片，不能混入AC3c.2精确候选。

## 已核调用链与需要保留的行为

原任务提交复用原cli.task_action准入、单task锁、dispatch前attempt、原run history和submission memo；计划批准沿_Submission核创建/原run，计划receipt摘要绑定实际job上下文。原DevelopmentWorkflow拥有六阶段、批准、工作单元、fence和取消；不复制该调度器。原Executor通过context.spec核legacy合同，selectable Executor只覆盖model和receipt。特别注意：原verify阶段会向tasks/ID/task.spec.json写legacy spec，新显式wrapper不能被降级或覆盖，必须为可信scope gate提供独立且核对的原投影。

新运行输入必须把完整v2信封带入Temporal原始payload。查询/恢复须比较其完整JSON身份，不能先解包后只比legacy投影；作业context、计划批准、候选审查和最终收据沿同一信封摘要。旧入口遇v2应在副作用前拒绝，新worker显式注册新workflow类型；原v1历史/运行ID不改。信封及加入运行态材料后的上下文均沿原容量界限拒绝，不截断。静态manifest中的端口映射不是运行态结果。

## 可验收切片与实现顺序

- [x] CR1：新增独立版本workflow入口，继承原六阶段调度；统一原始输入/legacy投影合同供提交、查询、批准消费。先用实际SDK验证注册及重放/查询/信号继承；未接真实executor前保留公开v2 start拒绝，不冒称可运行。
- [x] CR2：原提交/运行查询/批准/恢复经版本入口带完整身份；新worker与服务管理显式支持两版本；组合通过版本专用submit活动与请求命名空间派发，旧worker/原executor不得消费成单Agent任务；相应计划/证据读取按同一版本路径。原memo、attempt-before-send及NOT_FOUND未知语义保持。
- [ ] CR3（内部a/b已交付，[公开c](2026-11-09-composition-public-runtime.md)最终独立交付在途）：selectable执行器在所有阶段核原v2创建信封/context/冻结选择；复用可信集成/检查并解决verify投影路径；首条review仅单个纯只读叶子。调用前重验原包/当前后端能力，完整祖先材料和同候选动态证据形成独立调用快照，实际prompt/result/收据可回溯。多成员/串并行留AC4，支持范围在准入明确拒绝。
- [ ] CR4：真实安装包与本地Temporal/worker/受监控执行流程，覆盖显式owner批准、相同legacy但不同manifest拒绝、删源后执行、失败/取消/恢复及v1兼容；新fresh-context独立审查、Ergora自身模板真实审查、普通推送/必要双OS CI和原run/远端终结。AC3c.4再做完整备份恢复出口。

## 所有权与取舍

workflow_definitions仍拥有资源/图/权限语义，task_envelopes拥有标准库历史字节合同，agent_backends拥有实际模式/政策，task_mcp/agents/process monitor拥有固定资源与进程生命周期。正式执行沿现有reference桥与executor，不另造State数据库中的第二套正式运行记录。适配器有真实变化时使用同一构造/执行interface，在实现目录局部注册；上层不按厂商分支。只读MCP不是任意shell或文件系统隔离，能力记录不转化为授权。

已开始CR1最小输入/继承实现，未完成上述验收；每切片实施前更新基线/精确范围，实际结果逐步追加。若可信验证原阶段不能以小seam复用，先记录具体重复与行为差异并做专门兼容验收，不复制整个engine来求短期可跑。

CR2接线细化（待实现）：先交付两版本worker和队列/请求路径，再接提交与证据读取，保持公开v2启动关闭直至CR3可信执行完成。新任务使用单独Temporal队列与`requests-composition-v2`根；新worker分别绑定各版本队列和原FileAdapter，复用原Activities，只给v2 submit提供已有专用名。这样旧worker不能接到新版poll/authorize/fence，也避免改变CR1已保存history的活动顺序/名称。取消fence必须扫描同版本请求根，不能只写fence后漏查新版作业。队列/路径规则归版本输入合同，读取、worker和后续executor共用；不让上层按后端/版本重复分派。

原verify没有替换spec路径的hook，直接执行会与wrapper不可变发布冲突。禁止全局patch write/subprocess来适配并发阶段。若需迁出该分支，只迁入可信verify的范围检查、原命令/基线对照和回执逻辑，其他阶段继续继承；新旧版本都经同一新verify所有者做等价验收，v2给scope harness传独立legacy投影，完整wrapper保持原字节。该有限迁移须单独记录实际重复/差异和新旧候选证据，不能用“复用”掩盖算法复制。
