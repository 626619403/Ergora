# F9：训练实验工作台

日期：2026-11-14。承接[总计划 F9](2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)与[训练手册](../TRAINING.md)。首片基线 `47443840b68693f63ee011dc6fbe29421a42223f`；该提交的 H3b 自己的 CI 与原独立两轴终验已完成，不借给本片。节点进度见本文及[交付记录](../delivery/2026-11-14-training-workbench.md)。

## 所有权与接入方式

现有 `agent_platform.training` 保存 baseline、manifest、spec、job、fence、approval 和集成票据；`training_executor` 负责可信执行、perfctl 复验与 MLflow 记录，`perf_temporal` 是原控制工作流。Forge campaign 仍是候选来源。控制面不建立实验表、训练队列或新的批准协议；`optimization.py` 的 GEPA 是 Skill 文本优化，不充当训练 owner。

比较两种读入口：直接调用 `agentflow training` 需要完整 Linux runtime／SDK，现有 CLI 也不提供离线列表；沿 `reference.task_files` 的独立标准库 reader 可读取固定版本原件，且基础安装无需加载可选 SDK。首片选择后者，保留原布局、原字节与摘要。后续执行动作才进入原 Linux owner；不把离线文件读取当作实时状态或批准。

新增控制面 `training.py` 负责项目范围的查询，CLI 与 Web 是两个实际消费者。读取进程和固定参考布局归 `reference.py`，复用已有 safe-file、bounded reader、Windows reader 及原 manifest／Experiment validator；不复制训练调度或统计算法。页面增加独立训练导航，先提供原件查询与到模板／Forge／原生操作说明的入口。不会在首页刷新时启动外部查询。

## 可验收子节点

|节点|行为及复用|出口|
|---|---|---|
|F9a 原实验只读导航|按已发布且登记训练模板的项目读取 baseline、分页实验、完整 manifest／spec、原 runner／job／result／gate／fence、负结果及已有 MLflow ID。固定项目／repo／manifest／job 关联；损坏与缺失明确显示，未查 runtime 保持 not_queried；开始标记不证明仍在运行，runner SUCCEEDED 不证明 gate 通过或采用|CLI／HTTP 相同查询语义；不同项目／同进程环境不串读；分页／坏原件／陈旧baseline／篡改摘要／路径越界有针对性行为证据。新安装包、283冻结参考、自身模板、新独立两轴及本提交CI；真实浏览器检查切项目和迟到响应|
|F9b 原生有界操作|原项目修订、可信 runner 与精确 manifest 下接 prepare／start／查询／取消；按原实验身份保存发送前意图与unknown并对账原 workflow，不新建第二训练账本。明确原控制 worker 与逐实验 run-local 的区别|先 CPU 合同旅程；注入请求后失联、重复、取消及停止收尾，保留真实错误，不从 started 文件推断停止|
|F9c 可信结果与采用|展示原配对比较、gate、MLflow及负结果；按原 evidence SHA 批准并查看原集成／复验票据，Forge结果只作提案材料|原 evidence绑定、独立正确性／质量与人工批准保持；核精确票据，不自动合入或伪造训练收益|
|F9d 实际训练旅程|在具备完整资产、设备、预算、真实baseline／candidate、独立oracle及精确批准后运行真实GPU对比，按原owner交接开发集成／复验|单列真实B3验收；缺外部条件保持开放，CPU／合成不替代真实训练收益|

F9b 开始前再按现有原 owner 的 API 与实际恢复语义划分小片，不预先添加通用执行框架。参数搜索／远端作业分别依赖 D4／D3，完整 Forge 依赖 C2；首片不隐含实施它们。

## F9a 实现范围与验证

- 预计修改原 `reference.py`、CLI、Web、console app／index；新增有真实 CLI／Web 消费者的 `training.py` 和单一页面模块。复用既有 suite；需要新 suite 时登记原显式 CI 分组，不另建 CI。
- 读取原项目 performance registry 的 manifest，再核全局 spec／manifest 对同一字节SHA的绑定；runner／job须属于同项目与同Git根。详情只读取固定文件，不接受任意 artifact URI。每文件有界、路径拒绝 symlink／越界，分页限制实际检查条目；不枚举私有凭据或其他项目正文。
- 原报告只显示 recorded 状态；gate摘要须与原 result 引用的 report SHA 和 binding一致。没有 runtime 查询、没有重新执行比较器，不能报告当前成功或已采用。并发原写入可使本次读取缺项／不一致，显示观察错误，允许用户重新读取；不修写原件。
- 单独保存隔离 CPU 原生 prepare／原 owner生成记录及CLI／API／浏览器实际检查原件。真实GPU不在首片，原业务项目保持只读。
- 用户已授权的持续开发、普通推送与每片审查规则保持；源码／包改变后核其自己的证据，不借 H3b 或历史安装成绩。

## 当前进度

F9a源码已实现，本地验收完成：r1包563／两RECORD／283、六安装suite121通过；两P2修复后r2三suite33通过，源训练／架构27通过。r3最终展示包563逐字／两RECORD／283、原生CPU记录18件保持、实际浏览器完整原件／迟到排列／三视口／停止收尾通过；自身核心11文件及最终六前端聚焦两轮approve。两独立方向最终本地原件核验通过，开放0／0；普通发布／自己的CI待收口。r1成绩保持原候选范围，初始夹具错误和原request-changes保留；未为可逆布局重复核心回归。F9b–d待实施，真实B3与完整C2保持开放。
