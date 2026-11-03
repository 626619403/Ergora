# F3.4b1：固定原run的外部作业证据只读视图

日期：2026-11-03。实现基线`d98a62a4c9f6d9d514225f033a3f8dad3de3ca60`，前置F3.4a已完成并确认远端一致；本切片源码已实现，定向验证进行中，尚无独立审查或发行结论。主节点与反例见[终态对账调查](2026-11-03-task-reconciliation.md)。

## 合同与边界

CLI `task external-status PROJECT TASK --run-id RUN --timeout 20`与GET `.../tasks/TASK/external-status?run_id=RUN&timeout=20`。仅统一创建/已保存原提交的闭合run；原run/spec/memo和当前workflow ID的run均核对，另一在途/后续run不得被当成原scope。GET不持控制DB写锁，不保存本工具记录、发布fence、改任务、释放租约或调用doctor。父进程无需SDK；使用登记Linux完整运行时，Windows原生明确提示Linux/WSL2。

复用_Submission/原Transport、真实SDK converter、原FileAdapter/read/poll及摘要/安全文件函数。流式读取固定原run完整history，要求原始start及对应终态事件；只收集dev_submit上下文，绑定原spec/task/request/profile，重复相同job幂等，冲突或截断历史拒绝。原outcome独立返回，不将新的外部事实改写成workflow终态。

只支持原参考STATE五类adapter子目录，明确检查配置根，错误根不猜测。逐个原history job核原envelope及原FileAdapter可信终态receipt/产物；缺失或无效证据保留unresolved，额外job使本次外部确认保持false，冲突envelope/fence明确拒绝。既有fence必须匹配原task/request；仅在有效fence、完整history及全部原job/envelope/可信终态回执均匹配且无额外job时报告external_confirmed。它是原可信文件协议的快照，不是独立OS进程扫描或六阶段质量通过。

响应保留原workflow/run/temporal状态与outcome、history job身份摘要、每job的请求/回执状态及摘要、额外/未决job、原fence事实；lease_released_by_operation固定false、execution_success保持null。只读视图不接管B2的显式对账意图/检查点/释放责任。预算沿原专用进程1–60秒及父额外5秒，本地合同预检另计；不缓存跨请求证据以掩盖变化。

## 验收

两模板闭合但外部未确认/已确认的真实原生文件旅程，纯查询无文件/租约变更；原run/spec/memo/最新run/完整history的身份反例；已知job丢失不能变零作业通过；adapter根漂移、同ID context冲突、无效或损坏receipt/产物、额外请求与错误fence可区分；CLI/API共用规则、缺运行时显式失败，长RPC不保留DB写锁。先源码定向和新fresh-context独立审查，再最终非editable包/无SDK控制旅程/适用定向回归与精确两OS完整CI核对；本切片不重复宣称A旧完整回归是新源码通过，不替代B2与c/d真实服务验收。

## 实现与首轮反例

新增`reference_task_reconciliation`是专用原生查询入口和外部证据算法的所有者，实际由`reference.task_external_status`供tasks/CLI/API调用。复用_Submission/创建合同/原Transport查找与memo归属、SDK converter及原FileAdapter的路径/回执/产物校验；无新依赖、数据库表、通用runner或冻结文件修改。父进程不导入SDK、不持共享DB写保留，实际读取在登记解释器中执行。

测试仅替换不可控RPC边界，使用真正SDK1.34.0的protobuf、DataConverter自定义codec和WorkflowHistoryEventAsyncIterator多页协议；上下文由原DevelopmentWorkflow.context生成，请求、回执、产物和租约真实落盘。外部确认只是可信终止证据，FAILED/CANCELLED仍不代表六阶段质量通过。

`source/before-fixes.log`（四例26.20秒，退出1）确认两个产品缺口：漏中间history event原先仍通过；非法结构receipt的TypeError原先中断整次查询。现已检查1起连续event ID，并把原receipt解析/校验的TypeError列入该job的invalid/unresolved。另两例是测试页数期望错误（5个事件按两条分页为每次3页，两次6页），只修正计数；查询事实及不变性断言保持。更早一次检查因basetemp父目录不存在未执行到产品，已建立持久证据目录，不计为产品验证。

首轮源码定向为54 passed、1 failed（232.71秒、1个已有warning），唯一失败是测试regex用`run ID`而原公共拒绝诊断为`Run ID`；产品正确拒绝空ID，修正仅校正测试大小写。补充五个输入边界复验及两个原CANCEL_UNCONFIRMED/BLOCKED结果保持反例，共7 passed（29.77秒）。生产实现从首轮到复验保持，当前49个外部证据用例及8项架构边界均有对应通过证据；未将首轮失败标成通过。命令/退出码/原日志在`source/initial*`与`source/followup*`。

尚未构建B1 wheel，现有开发/基础安装仍为A候选，不能沿用旧发行或旧完整回归作为B1通过。公开USAGE/PROJECTS/AGENT_BACKENDS与边界图已同步，已完成实际入口/原生所有者/冻结依赖及只读路径自查；准备新的fresh-context源码审查。最终非editable包、无SDK基础旅程、适用回归/性能、精确两OS完整CI及独立终结审计仍待完成。

## 独立初审与首候选边界

[独立源码审查](2026-11-03-task-external-status-review.md)复现1项High/P1：仅枚举requests会忽略receipts中的孤立job，合法终态或损坏的孤立回执均可使external_confirmed虚假为true。证据为`reviewer/orphan-receipt*`，两个完整入口断言均失败。现已在同一files所有者合并requests与receipts的job ID；不在原完整history中的ID统一保留unexpected/unresolved，不按任意artifact文件名猜job。新增两类孤立回执反例，零history正例同时清空请求与回执；修后定向运行中，尚未关闭finding。

首候选6a669736…wheel已完成347文件×源码/包/两安装一致及冻结283、111项适用包回归（319.10秒）和无FastAPI/Temporal/GEPA基础两模板25CLI旅程。18秒受控连接等待时其他项目写者21.15ms完成。该候选不含上述孤立回执修正，不是最终发行验收，原包及日志保留；不能用其通过关闭P1。准备修后重建，最终包仅补受影响B1与架构检查、基础旅程，邻近未改模块检查由已记录首候选与最终两OS完整CI分别说明身份。

## 修正复审与最终包

修后源码10 passed（52.28秒）。同一独立审查者重跑原两项孤立回执探针均通过，并对零history/有无fence/保留普通artifacts边界独立复验；P1关闭、无新增结构/正确性/性能finding。其相邻探针曾因自身SQLite连接未close产生WAL/SHM、影响第二次文件快照；已修正探针生命周期后1 passed（7.92秒），原失败保留，不记为产品缺陷。

生产/测试`a2349e8c3b183918a68935d5199e7c78509364a4`已提交推送。八文件aggregate为`85fa8b1dcffadb39bddab760deb8110260ad3e0daa646fafa4d764be90440798`，新wheel SHA256为`52d26ddcd998e1cf94bdb274bb6d3aa4ae1cf62a57d28d8b8bbc84849d6d4051`；347文件×源码/wheel/两非editable安装一致。开发Python3.11.15与基础Python3.12.3分别装同一包，基础环境无FastAPI/Temporal/GEPA；冻结283保持。final-package-commands.json和package-identity.json保留命令/身份。最初开发环境不具备build可执行入口，已用现有独立构建Python完成，没有新增依赖。

最终包的全部51个外部证据用例加8项架构边界 **59 passed**（247.84秒，1个已有Starlette/httpx warning），命令/退出0/原日志见final-wheel-targeted*；相邻status/tasks/web的54个未改用例由首候选111项记录说明，不冒充最终包全量，最终候选的完整回归由精确两OS CI完成。

最终无SDK基础两模板 **27次CLI** 通过，包括注册/预览/创建/缺完整运行时明确失败/单次提交、缺fence与缺receipt/完整可信终态/缺原envelope/孤立receipt/根漂移。每次查询的原任务、journal、envelope/receipt/artifacts/fence字节及活动租约保持，原CANCEL_UNCONFIRMED结果未改。三次完整查询中位治理1194.47ms、大型1148.55ms，含CLI/原生解释器及SDK导入；不作为纯启动或模型性能结论。治理模板两次各9秒受控connect、25秒总查询预算下，其他项目真实SQLite写者 **22.78ms** 成功且早于查询结果（总19213.23ms）；没有控制库远程写保留。原日志/命令/JSON见base-journey-final*。

最终包/命令/基础旅程与源码的独立终结核对、精确两OS CI及远端收口仍待完成；不标b1或完整F3完成。用户追加的[测试/CI成本审计](2026-11-03-verification-redundancy-review.md)另行完成，其优化[V1–V3计划](../plans/2026-11-03-verification-efficiency.md)不混进当前功能源码身份。

## 独立本地与精确CI

独立最终本地核对已通过：347文件×源码/wheel/两非editable安装/a2349e8归档、八文件85fa8b…、冻结283与原manifest字节保持；59项命令退出0、27CLI日志与JSON及计数一致，原CANCEL_UNCONFIRMED、两模板活动租约1和空released_at/evidence_digest均独立核实。没有重跑旅程/完整回归，reviewer/final-local-*保留直接核对及17份证据摘要。

精确[CI41597961138](https://github.com/626619403/Ergora/actions/runs/41597961138)已成功：Windows job125789665133的构建安装/冻结身份/完整应用回归/PowerShell安装升级四必需步骤，Ubuntu job125789665389的前三必需步骤均success。官方run/job HTML、完整commit及各必需步骤log URL已由verify-ci.py核对，来源摘要见ci/ci-html-status.json。最终独立CI/实时远端终结核对待完成，当前仍不标b1完成。

## 最终收口

F3.4b1完成。最终独立审计直接从官方原HTML重建run选择，核实精确a2349e8、Windows四/Ubuntu三必需步骤及各日志URL/完成标记、来源摘要；实时origin在2026-11-03 08:00:40 UTC仍为a2349e8。八文件85fa8b…、wheel52d26d…和已核17份本地验收证据身份未变。独立脚本退出0，P1关闭，无未解决结构/正确性/性能finding，见[终结审查](2026-11-03-task-external-status-review.md)及reviewer/final-ci-remote-review.*。

最终347文件×源码/包/两安装/提交归档、冻结283、59项定向、27CLI、18秒并发及精确两OS完整CI均在各自声明范围通过。首候选、失败探针及修正复验继续独立保留，不作为最终结果替代。手册/架构/进度、两份审查与成本跟进计划沿同一已授权分支以文档提交推送，不改变生产身份或重复同代码CI。

下一切片先做[V1测试输入分层](2026-11-03-verification-input-layers.md)以落实已量化的初始化开销；之后[b2显式对账](2026-11-03-task-reconciliation.md)复用本只读证据边界。b2的fence/持久检查点/适用租约释放、c/d/e真实六阶段/重启异常和完整F3均未完成。
