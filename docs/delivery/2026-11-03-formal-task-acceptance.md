# F3.4：正式任务出口与综合验收设计

日期：2026-11-03。当前仅为下一切片的调查/执行拆分，尚未实现或验收。先完成[F3.3d提交锁分段](2026-11-03-task-submission-locks.md)的发行/精确CI/独立收口。D的c774ba…候选不能被本文预认完成，旧L0真实模型结果也不自动验收新统一入口。

## 已核事实与缺口

统一tasks/CLI/API已有创建、单次提交、固定原run查询、精确计划批准与取消；`task status`对已完成原run已经返回原outcome，不需要另造结果状态机或单纯别名。当前尚无统一候选导出或终态后外部fence对账入口。原参考`agentflow task export`会等待原结果、要求REVIEW_READY、按原规则释放准入租约、将候选fetch到业务仓库本地分支并保存export.json；已有分支只能位于同candidate，不checkout、不merge。

原`agentflow task result`会释放适用的准入租约，不能直接包进只读GET：原release仅接受REVIEW_READY或BLOCKED且fence.confirmed为true。L0取消原workflow保留CANCEL_UNCONFIRMED，而外部进程稍后已停；查询和外部对账必须保留这两份事实，不能改原workflow结果或删除ledger来解除未知。候选结果、可信检查与独立审查仍由原执行器拥有，控制面不另算通过。

源码依据：`tasks.status`、`reference_task_runtime.VerifiedSpecClient`、`reference_task_submission._Submission.submitted/lookup_run`、冻结参考`agent_platform.cli.task_action`及`ingress.release`、`DevelopmentTransport.poll`。后续先继续核原FileAdapter.fence和IngressLeases合同，再决定最小可复用边界；尚无新增依赖或抽象层决定。

## 分段节点

|子节点|交付与复用|验收与退出|
|---|---|---|
|F3.4a 候选导出|同一CLI/API入口显式确认当前revision、原run、精确candidate和目标分支；复用原REVIEW_READY结果、spec/memo归属、Git分支冲突保护及原导出实现。保存不可变意图/写前检查点及可查询回执；长网络/仓库操作不持控制库写锁|运行中/失败/旧candidate/错误run或memo/已有不同分支拒绝；fetch前后中断沿原记录恢复；未知不隐式重做有冲突操作；已有正确分支只补同一回执；不checkout/merge/推送业务仓库。先核原实现实际可复用程度，再实现最小完整切片并独立审查|
|F3.4b 终态后对账|沿原任务、原run与已有job/ledger使用原FileAdapter/fence确认实际外部状态；显式写操作与只读查询分开，适用时由原租约合同释放，不改原workflow终态|未知/未确认不释放或伪造成功；原run闭合后仍可表达“workflow原结果未确认、此次外部已确认”；拒绝错误项目/ID/证据。没有足够权限的维度记限制，继续其他验收|
|F3.4c 新两模板正常旅程|最终非editable发行、全新持久隔离项目与数据，从同一入口注册/预览/创建/提交/原run状态/精确计划批准到六阶段结果/候选本地分支；真实可用模型与可信检查另记身份/预算|核实际history原spec、提交memo和run固定；重开CLI/HTTP后同原ID；独立worktree复验导出候选，业务主分支保持原基线；不继承旧L0通过|
|F3.4d 异常与恢复|重复、丢响应、旧计划、候选漂移、审查改checkout、检查失败、取消及受控独立worker重启；保留失败和未知|协议反例与真实服务范围分开；不修改/重启已有用户服务，不争取宿主权限；缺认证/权限/服务时记录具体限制，能测的路径继续测|
|F3.4e 阶段收口|固定源码/配置/安装/证据身份，当前架构与两本公开手册同步，独立结构/性能及综合审计、精确两OS CI、提交推送|只标记实际完成范围，未验维度有后续责任；完成后才进入F4正式任务页面|

每个完整实现切片使用新的fresh-context审查；单纯状态/报告更新无需递归审查。先小反例/原合同检查，再发行与端到端，避免在入口仍缺失时重复运行昂贵模型。真实模型认证沿已授权环境变量读取，不打印凭据；持久原始证据放隔离验收目录，公共文档只写可复核身份、结果和限制。
