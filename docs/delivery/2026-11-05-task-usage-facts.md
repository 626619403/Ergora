# F5.2：冻结预算与原history用量事实

日期：2026-11-05。状态：在一个既有生产所有者完成首轮实现，源码51项定向通过；独立包及三个原runCLI/API对照通过，前后不变及正式退出已通过，[新的独立本地审查](2026-11-05-task-usage-facts-review.md)通过，无未解决finding；精确交付待收口。源码基线`2c0ddbccd25dda66d971eadd6770b61877c83bb7`，F5.1本地验收/新独立审查通过且已正常推送；其精确双OS CI41911536059及同片独立终结现已通过，前置F5.1完成。来源：[F5分片计划](../plans/2026-11-05-evidence-handoff.md)。本片可独立实施，前片CI终结前不推下一生产候选。

## 事实与合同

在同一`task evidence`索引增加`budget`和`usage`，无新命令、生产模块、依赖、持久账本或schema迁移。原创建/提交/spec/memo、完整闭合history、可信FileAdapter和响应/墙钟限制全部复用；旧external-status/对账输出不增加字段。

`budget`直接引用原spec的profile摘要、`limits.max_work_units/max_parallel_units`、`stage_timeout_seconds/approval_timeout_seconds/poll_seconds`，范围明确为工作流准入、work单元并发及等待策略。真实源码中stage期限在dev_submit返回后建立，空回执poll后才检查期限，活动RPC、成功回执和外部进程并不具有相同的硬截止语义。该字段不能称为执行器进程walltime、任务总超时或计费预算；不读取现在的executor配置推断原工具限制。

`usage`在已有完整history扫描中累计事件、activity调度、history实际记录的activity-start与signal数量、dev_submit调度事件数及不同原job数；冻结request给出配置的work单元数量。SDK会合并部分activity重试历史，记录的start事件不等于全部实际尝试、模型调用或计费次数。重复同context调度保持事件次数而不增加不同job数，冲突仍拒绝。

原history首事件和终态事件的Timestamp给出`workflow_span`：来源和event引用、开始/结束时间及秒数。没有时间戳为`not_recorded`、反向时间为`invalid_timestamps`且秒数null；真实零跨度可为0。该跨度包含服务停机、排队、人工等待和并行阶段，不是模型运行时长或各job时长之和，不据signal时间估算批准等待。模型调用、token和费用没有可验证的provider记录，明确`state: not_recorded/value: null`；费用币种和来源亦null，不显示0或自行估价。

## 所有权与验收

- 仅扩展`reference_task_reconciliation._Inspection`现有扫描和索引组装，保留旧jobs返回类型、原context/清理checkpoint摘要及旧操作输出。扫描可接受只在索引请求中提供的计数容器，不增加第二次history查询或持久缓存；统计状态只属本次调用。
- 使用真实SDK消息/时间戳与既有轻量FileAdapter夹具，验证冻结预算、重复调度与调度/start/信号的区别、明确未知费用/token、缺失/反向/零时间、取消/失败原结果与只读不变；沿用现有上限/CLI/API合同检查。
- 独立noneditable350资源/两安装与283冻结核验；风险相称源码/包定向及两模板旧对账代表路径，不复制全量本地矩阵。精确双OS CI承担完整套件，保持原超时和矩阵。
- 对已保留的两个正常原run和取消原run，用最终包CLI/API读回并直接核原profile、SDK原始event分类/Timestamp及原文件摘要。核原139文件、三history/outcome、refs/worktrees/leases不变；只开专用Temporal、不开worker或模型，结束正式shutdown并保留持久数据。
- 实施及证据更新后启动新的fresh-context审查，核正确性、维护性、必要测试/守卫和实际成本。完成精确提交/普通推送/CI及同片终结后才关闭F5.2，继续F5.3交接格式。

已实现的范围与实际验证见下节。费用采集、新执行预算、provider计费插件、批准等待推断、OTel/MLflow投影及页面归后续独立范围；本片只投影原来源可证明的事实。

## 实施与验证进度

生产只改`reference_task_reconciliation.py`：索引模式给已有jobs扫描提供本次计数容器；旧模式保持无统计/原返回，完整history只读一次。时间戳缺失/反向只使跨度未知，不改变已闭合原结果或材料核验；冻结profile/request直接从原验证spec读取。没有添加生产文件/函数/依赖、持久状态或CI。

真实红例：原2c0ddbc生产下8项新增用量合同全部失败（字段不存在，pytest1.81秒）；原命令及日志保留。实现后同源51项定向全部通过（其中31索引/用量、12单payload、8架构，pytest2.38秒、外层3.15秒，1上游TestClient弃用warning），没有重跑全量矩阵。随后给原legacy合同补显式budget/usage不新增断言，包内验收将覆盖。测试复用原夹具并补实际profile/request字段和Timestamp/额外事件；未新建测试框架。

私有命令与原日志在忽略的`.ergora/checks/f5-task-usage-facts/usage-baseline*`及`usage-fixed*`。下一构建独立350资源包/两安装、原runCLI/API直接对照和前后不变/服务退出；完成本地记录后启动新的fresh-context审查。前片精确CI仍保留独立身份，不以本片局部结果替代。

## 最终包与三原run事实对照

独立wheel SHA256 `17cd87edef513cce25df4546a2d031fa4c92c642fe69596d3af8853b2fbcbd07`，350源码/wheel/两noneditable安装逐项相同，283冻结reference保持，基础Web安装无Temporal SDK。包内31项索引/用量合同全部通过（pytest6.80秒、外层9.25秒），旧external-status/对账两模板代表4项通过（pytest35.01秒、外层36.03秒）；范围分别记录，不合成完整回归。

最终包通过三CLI和五ASGI GET（含错误run/跨项目各400）；每成功端点调用实际登记原生子进程与Temporal。独立期待值用SDK原history的event_type Counter、首终Timestamp及原文件profile/request获得，没有用索引回填期待。三原run的139证据文件及每份context/receipt/产物字节亦沿F5.1脚本直接核对；模型零调用，没有执行任务或批准/取消信号。

|原运行|event / activity调度 / 记录start / signal|dev_submit / 不同job|配置work单元|服务跨度秒|
|---|---|---|---|---|
|repository-governance正常|329 / 40 / 40 / 1|7 / 7|2|6541.066190111|
|large-change正常|348 / 37 / 37 / 1|6 / 6|1|6629.486720524|
|repository-governance取消|112 / 11 / 11 / 1|1 / 1|2|113.910954298|

两个正常原结果仍REVIEW_READY；取消仍原CANCEL_UNCONFIRMED，既有清理确认另报true。冻结阶段/批准/poll为3600/86400/15秒，治理work限制4/2、大变更24/4；这是原工作流策略，不是当前执行器600秒配置的历史证明。全部model_calls/tokens/cost仍`not_recorded/value null`，未用调度或start次数推断模型用量。

本地三CLI约1.74–1.93秒、ASGI端点1.51–1.55秒，CLI16672–33427字节，仅当前小规模运行的整体观察；无额外history RPC或新持久缓存，未声称吞吐/内存或性能提升。私有`original-usage-verified.json`/逐runCLI与API、`original-usage-command.json/.log`保留确切命令/结果；前后139原文件、三完整history/outcome、两repo文件/HEAD/refs/worktrees及三claim/零active lease完全相同。正式shutdown confirmed、两个专用进程退出、四端口关闭、三个持久数据库保留；最终离线重算139文件/leases仍不变，未启动外部HTTP。新的独立本地审查和精确提交推送/CI待收口。

新的fresh-context独立本地审查已通过：源码/必要守卫与测试、350资源/两安装/冻结283、三原run计数/纳秒跨度及139文件/Git/leases不变/正式服务退出均独立核实，无未解决finding。下一完成精确提交/正常推送、Git archive同包核验、精确双OS CI和同片终结；不继承前片CI结果。
