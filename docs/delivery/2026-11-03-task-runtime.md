# F3.3：原生运行状态与显式操作

日期：2026-11-03。分支refactor/architecture-foundations，设计基线b6802216b0a60c9e439b1441c39004bf269503c3。F3.2最终本地验收及独立本地审查已通过，精确两OS CI收口中；本文件先记录分段设计，当前F3.3a进入实现/定向验证，F3.3b/F3.3c尚未实施；不代表完整F3.3完成。

## 事实和所有权

原DevelopmentTransport已有固定workflow ID、REJECT_DUPLICATE、原始启动spec比对、显式run ID、单次启动和协作取消。lookup通过describe和第一份history验证原始输入；poll区分运行状态、完成outcome及异常终态NEEDS_RECONCILIATION。原agentflow的doctor、可信检查、IngressLeases、owner批准回执及精确计划SHA继续是运行和授权规则，不另造任务状态机或通过状态。新统一入口只组合已有合同、持久意图/回执及原生端口。

## 分段及验收

|切片|范围|验收与依赖|
|---|---|---|
|F3.3a|只读原生运行状态；CLI/API同源|published项目的本地spec先由既有reader验证，再经固定专用进程调用原Transport.lookup/poll；返回workflow/run ID、request/profile身份及原始phase/status/outcome。显式run ID原样沿用；未指定时查询原workflow ID并返回查得的run ID。只有原生NOT_FOUND可报不存在，连接/认证/超时/输入冲突明确报错；不从本地文件或服务进程状态补造运行结果。可选SDK缺失提示安装。旧正式任务可只读；不写任务/ledger/配置，不调用start/signal/cancel。|
|F3.3b|显式提交与原ID对账|当前项目revision及精确创建意图/原spec准入；复用原doctor/可信检查/IngressLeases/Transport.start。任何外部调用前保存不可变操作意图，结果绑定原workflow/run ID。丢响应/超时保留unknown，按原ID查原始输入后恢复；不能换任务ID或重启已关闭workflow。旧在途任务不隐式接管。|
|F3.3c|精确计划批准、取消及恢复|批准必须绑定同一任务spec、原run ID、当前plan SHA和明确owner决策；沿用原批准receipt/信号，持久意图与结果分别记录。取消必须有原因及明确确认，信号成功只记请求已发出；CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION及原外部进程对账保持可见。不得用terminate、删ledger或重提交来掩盖未知。|

各段为完整可审查切片，分别做fresh-context结构/性能审计。F3.3a仅是读接口，不代表提交、批准、取消已交付；F3.4才做两模板新的完整六阶段和分支导出/异常重启综合验收。

## F3.3a拟定接口与约束

CLI `task status PROJECT TASK_ID [--run-id RUN_ID] [--timeout SECONDS]`；API `GET /api/projects/PROJECT/tasks/TASK_ID/status`，可带run_id/timeout。返回仍保留本地spec身份，runtime_status标明queried/not_found；直接附原Transport.poll结果，不把闭合的Temporal状态一律当作成功。没有找到运行也不自动start。

进程使用登记且身份核对的reference安装代码及配置/状态目录，明确的包路径隔离原导入全局，选定SDK只在专用进程导入。所有网络等待有总预算；SDK/RPC/连接错误转换为可见公共错误，不自动重试变更操作。SDK的内部连接管理不构成新的调度器。平台范围按真实依赖分别验收，不能从Windows本地编译推断正式执行。

验证先覆盖真实合同与可控原Transport协议替身的running/completed/异常终态/not-found/输入碰撞/显式run ID/SDK缺失/超时，以及CLI/API一致与无写入；再对已有真实任务做只读CLI查询，核对原任务字节保持。性能报告区分CLI/进程启动及真实服务查询延迟，限定测量条件，不用fixture推导生产吞吐或任务效果。


## F3.3a实现进度

tasks.status及CLI/API已实现；reference_task_runtime是新的专用原生读取边界，复用登记安装的原Transport.poll（含lookup原始spec/固定run ID），无新状态表、引擎或持久运行镜像。父进程只探测可选SDK是否安装，实际SDK/原全局在子进程导入；网络查询使用asyncio总预算，父进程加5秒启动/强制回收余量，不自动重试。连接规则沿用原core.environment的本地Temporal端点，不误用资料研究scheduler绑定。

新增原Transport+只读SDK协议夹具覆盖运行/完成/取消未确认/异常终态、原生NOT_FOUND与RPC失败、原始输入碰撞、显式/未指定run ID、SDK缺失、进程/网络超时、CLI/API一致及原任务字节不变。首轮25通过/1失败是NOT_FOUND夹具误断言describe失败后仍应有第二次handle绑定；只修正夹具预期，不改产品语义。最终定向结果、非editable包/实际只读旧任务旅程/性能及新的fresh-context独立审计、精确两OS CI尚待记录。辅助证据单独放.ergora/checks/f3-task-runtime/，F3.2的包/CI身份继续只绑定b680221，不混用当前新源码。


F3.3a最终源码定向26 passed（22.12秒），原始结果fixture-fixed-targeted.log；首轮夹具失败保留source-targeted.log。当前26项仅覆盖原Transport+可控SDK端口及CLI/API，不是实际Temporal服务验收。准备新的fresh-context结构/性能审计，以及最终非editable包/实际旧任务只读旅程/精确CI；原始服务和在途任务不做变更。


## F3.3a独立审查与发行身份

[独立源码/结构/性能审查](2026-11-03-task-runtime-read-review.md)通过，无确认finding；审查者独立26项检查通过（23.51秒）。真实父进程兜底探针在timeout=1时约6.010秒明确超时并回收子进程，父进程未导入SDK。当前非editable wheel SHA256为816b72d75fca0ae8c8e25911d88d165f8e2618c278c57fb7108305314747e43f，342文件×源码/wheel/开发与基础两安装一致，冻结283文件通过，独立只读重算一致。

实际既有两模板任务通过48次CLI查询：当前服务均返回权威NOT_FOUND、run_id=null，两个原任务目录20个文件字节保持。每个模板20次样本的CLI端到端中位1224.93/1218.01ms、最大1444.52/1295.10ms。该测量包含本地合同/安装身份预检、CLI/子进程/SDK启动及不存在分支RPC，不是纯RPC延迟，也不代表存在运行的查询性能；没有优化收益或并发吞吐结论。基础安装在真实无SDK时明确返回安装指导。

这些真实服务查询**没有取得旧run**，不证明真实running/completed、history输入比对或找到run后的固定；原因未在本切片确定。对应语义当前仅由原Transport+受控SDK合同覆盖，将在F3.4的新两模板完整旅程继续实测。不为扩展只读验收去修改现有服务、启动模型或接管旧任务。

准备推送已源码复审候选以触发精确两OS CI；完整适用回归及最终身份/CI独立复核单独记账，当前不把本切片标为完成。


当前816b…包的完整适用Linux回归396 passed、19 skipped、36 subtests passed（230.11秒），只含已有Starlette弃用警告。该结果与源码定向/真实只读旅程分别保存，精确两OS CI和最终审计仍待完成。
