# F3.4c/d：正式任务真实服务旅程

日期：2026-11-03。前置 [b2显式外部对账](2026-11-03-task-reconciliation-write.md)的生产/测试候选为 `7139d1a85cdce13689d75471620da8dd143156a8`，源码/完整包回归/精确两OS CI和独立最终审查均已通过，b2已收口。c/d真实旅程和各自独立审查均已完成；下文保留执行时的准备、失败与恢复记录，完整F3的e阶段状态见[综合收口](2026-11-03-f3-completion.md)。

## 本次范围与验收

使用相同非editable wheel、全新持久执行目录及新控制注册，通过正式CLI/API创建和提交两个模板，固定原spec/memo/run，精确计划批准，再经历 inventory → plan → work → integrate → verify → review，取得原结果并导出精确候选到本地分支。独立worktree重跑可信检查，业务main保持原基线；重开CLI/HTTP后沿原ID恢复。真实Codex调用与可信检查分别留原始身份，不继承旧L0结果。

后续 d 分开记录真实取消/外部原进程确认、终态显式对账、受控独立worker重启，以及可在协议层验证的错误批准/旧计划/候选漂移/丢响应。缺认证、权限或服务的维度明确记录，继续可测范围；保留失败和未知，不修改旧结果、删ledger或绕过门禁。

配置/数据/日志留持久用户目录的独立验收子目录；仓库私有检查脚本和身份索引位于 `.ergora/checks/f3-formal-journeys/`，公共文档不保存凭据/模型原文。所有测试操作员批准只适用于隔离演示，不能视作业务负责人批准或生产采用。

## 准备事实

只读盘点：默认服务端口当前未监听，既有完整参考依赖和Temporal二进制可用；Codex命令存在，历史验收配置采用 `gpt-6.1-sol` 和环境凭据，当前该凭据存在。没有测试真实模型请求，不能据此宣称认证有效。后续启动前重新核端口与自己服务的归属。

参考执行依赖沿已核冻结发行复制到新目录，Python/二进制可复用现成依赖，控制应用必须核新wheel身份。原setup会初始化私有配置/文件adapter目录；服务使用现有显式Supervisor用例，只管理本次登记的新执行栈。原模型配置含环境变量名，凭据只由运行环境提供，不打印/写入公开文档。

## c独立环境与真实提交

已复制并验证新参考运行时，复用既有完整依赖/二进制；新私有配置、native state和控制库独立于旧L0目录。两个业务仓库从旧演示main的已提交基线克隆，基线 `f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`，没有复制旧运行或采用旧候选。两个新项目分别注册一个模板，可信检查脚本有固定摘要，基线3项/6项全部通过。

4个开发角色各显式绑定Codex/current-container，当前项目revision均为5，绑定随新创建冻结。每模型stage预算600秒、最多2个并行外部job。服务启动前核默认端口为空，只通过当前登记控制的Supervisor栈启动Temporal/worker/executor/A2A/MLflow，doctor ready通过；这不证明模型认证有效。

正式CLI预览/创建/提交/固定原run读取共8次通过，两个run均进入INVENTORY，候选仍为基线：

|模板|新任务|固定原run|
|---|---|---|
|repository-governance|governance-f3-normal-r1|`01a1a106-8352-7c7a-96c3-4a8efd34ac5b`|
|large-change|large-f3-normal-r1|`01a1a106-9420-7808-a9a8-05f6268f8d27`|

私有入口/命令/计时在 `.ergora/checks/f3-formal-journeys/` 的 `environment.json`、`normal-runs.json`、prepare/start-services/create-start脚本及命令日志。服务脚本首轮把 `--binding` 错当内联JSON，CLI实际要求文件，未修改任何binding或启动服务；保留首轮脚本/错误后改用文件，8次binding更新、自己服务启动与doctor通过。属于验收辅助代码修正，不是产品修复。

## c真实计划与六阶段终态

两个原run均实际调用Codex完成inventory/plan并进入AWAITING_PLAN_APPROVAL。逐份核执行/回退计划的原始artifact SHA及范围后，使用测试操作员决定批准这两个隔离演示。计划SHA分别为治理`ce388a5742371e5d8dd9843a86d890e2384ebcb4237e4ff065c9324dd4c0015f`、大型`e870ca615d5ab5556e30c0d9694a1121c35a7c5e693db5dd192ad4f8672f2ffb`。

先以错误计划摘要探测正式批准入口：两者均明确拒绝，原journal保持prepared/attempt_saved=false，原history没有approve_plan信号；再以审阅过的精确计划批准，各原run恰好一个信号。原始脚本、命令和`normal-approvals.json`保留实际决定、artifact摘要和信号计数。

现已通过正式CLI固定原run核两者terminal=true、phase=REVIEW_READY。治理候选`ebb9f7bed44a110bc7a9d895c49ac6175f4b4c45`新增ownership文档及AST边界测试；大型候选`6ad080e1f3ac58d6312fae7f969d03fcbb63c112`新增summary/opt-in CLI/测试/rollout文档。各原结果的可信检查与独立Codex审查均通过，verification/review绑定同一精确candidate；没有合入业务main。

正在留完整history/回执/产物身份，之后导出候选并在独立worktree复验、重开HTTP/CLI。c/d独立审查尚未完成；届时使用新的独立上下文核原始证据和失败范围，不复用b2审查充当本旅程验收。


## c候选导出、独立复验与重开

正式`task export`已将上述两个精确candidate分别导出为各业务仓库的`agent/TASK_ID`分支；Git没有checkout、merge或push业务分支。两个main/原HEAD均保持基线，导出后精确原claim已按原outcome摘要释放。重复export和export-status均返回相同原回执。

分别创建持久独立detached worktree：固定可信脚本仍与注册摘要一致，治理3项、大型6项全部重跑通过。额外直接运行candidate unittest：治理4项、大型11项通过；治理的3个新增AST用例另显式discover通过。两者默认CLI均输出9，大型`--by-kind`输出build=6/test=3；base到candidate的diff/check/祖先关系和精确文件范围通过，main和验收worktree均干净。没有将该小演示的通过推导为任意业务的质量保证。

通过实际`ergora serve`启动/关闭/重开两轮loopback控制台，每轮读取两个项目的任务、creation/submission、精确原run实时状态、external-status、export和列表，并逐项与新CLI进程结果一致；两轮共44个记录HTTP请求，包含跨源/缺自定义头拒绝及重复start/export。原run和候选保持；HTTP前后快照覆盖104份原task/request/receipt/artifact及按文件名选取的操作journal，其字节摘要均保持。该快照没有包含按decision子目录保存的8份批准journal和2份owner批准回执，不宣称这些文件做过HTTP前后字节对照。HTTP服务完成后关闭，仅本次运行栈仍待d使用。

完整原history分别302/326事件，连续且最终为COMPLETED；原start输入与本地spec完全相同。原`dev_submit`共7/6个unique job覆盖六阶段，治理两个独立work unit、大型一个；全部请求/可信回执/产物摘要与history匹配。实际Codex model阶段分别5/4个，reviewer session不在work作者session集合中；verification和review检查全部pass并绑定原candidate。正常成功任务尚无fence，external-status的false保留该事实，不将缺fence当已完成外部对账。

原始可复查入口为私有checks目录的`inspect-normal.py`、`export-normal.py`、`reopen-normal.py`，对应命令/log及`normal-completion.json`、`normal-exports.json`、`normal-reopen.json`；完整history与各原artifact保持私有。inspect辅助首两轮分别误用SDK不存在的to_proto和未去除work:unit前缀，HTTP首轮误用urllib Request.method；均为验收脚本错误，没有修改生产/测试或任务事实，保留初始脚本/失败命令日志后，按真实SDK和原stage合同修正。最终inspect/export/reopen分别6.25/15.75/57.85秒，仅为当前环境实际观察，不推导性能收益。

c实现与实际验收及[新独立审查](2026-11-03-formal-task-normal-review.md)均完成；快照范围P2已修正复核关闭，无未解决finding。c可以收口，提交推送与d/e分别记账。b2收口文档已推送`a170dd12cf7f672e7dffb9c89ebc03b398506091`并核实时远端一致，生产/测试身份仍为7139d1a。下一步d另建受控取消演示，使用真实服务/monitor/父子进程及worker停止重开，保持原结果、沿正式对账入口核外部证据并释放精确claim；不修改这两个已完成正常run。


## d计划与运行边界

另建两个注册项目/业务clone，分别沿两个模板创建全新task；复用本次隔离执行栈和固定可信脚本，只把inspector显式绑定为受控stage-json-v1命令。该命令等待取消并启动一个忽略TERM的子进程，记录精确PID/starttime，不能作为模型效果或完整inventory交付；正常旅程的Codex证据不被替换。

正式入口提交并确认两个命令父子进程存活后，仅停止本次栈的worker，保持Temporal/executor运行；在worker停止时明确取消，核原run history的request_cancel恰好一个，再启动原worker。核新PID和相同原run继续、fence/可信终态回执及精确原进程消失，然后通过正式external-status/reconcile/reconciliation及重复操作确认原claim释放与原outcome保持。全部停止/启动沿现有services用例，未确认STOPPED不重启，不强杀用户服务；任何未知或失败如实保留。最后再重开CLI/HTTP核相同记录。现阶段不改生产、测试、冻结发行或依赖。


## d真实取消、重启与终态对账结果

两个新任务均在inventory的受控命令父子进程存活时操作，未运行模型或进入后续阶段：

|项目|原task / run|实际原结果与本次对账|
|---|---|---|
|governance-recovery-f3|governance-recovery-f3-cancel-r1 / `01a1a11f-dd2d-76d7-a587-a911fb26d239`|CANCEL_UNCONFIRMED保持；reconciled|
|large-recovery-f3|large-recovery-f3-cancel-r1 / `01a1a11f-f165-749a-b581-bced244d7a90`|CANCEL_UNCONFIRMED保持；reconciled|

正式services stop核worker为STOPPED，Temporal/executor PID保持；此时两原run仍RUNNING、每个任务4个已登记进程仍存活，task cancel各保存一个原request_cancel信号。正式services start取得新worker PID，原run继续并闭合。每个任务的命令父进程、忽略TERM的子进程、stage driver和timeout包装进程均核PID/starttime后消失；真实可信终态回执/产物及fence完整。原process_job monitor另有持久terminal记录，本轮没有将其PID/starttime纳入这4份直接采样，不把terminal记录扩大为该monitor的系统进程消失证明。原workflow即时fence结果为未确认，两原outcome没有被改写。

沿正式external-status读取完整原history的唯一inventory job，再显式reconcile保存四份不可变记录并释放精确原claim。租约摘要为本次独立清理evidence SHA；重复reconcile/reconciliation返回同回执，原run、outcome和业务HEAD保持。实际主流程32.20秒；只证明本环境的受控worker停止重开与这些原进程，不代表容器/主机掉电、跨机接管或任意逃逸进程扫描。

随后新起实际HTTP控制台，13个记录请求通过：各原run仍显示CANCEL_UNCONFIRMED，与CLI结果一致；external-status/reconciliation和原取消回执一致，resume-reconcile返回原事实。新request ID对已经闭合run只记录already_closed/cancel_requested=false，无写前signal attempt。重新核各原history仍恰好一个request_cancel，原outcome不变；HTTP服务正常关闭。原始证据为`recovery-runs.json`、`recovery-cancellation.json`、`recovery-reopen.json`及prepare-recovery/recover-cancel/reopen-recovery脚本与命令/log。

## d检查失败与只读边界

另建baseline-rejection-f3隔离项目/原run `01a1a125-95d0-732b-abac-f662741a4df6`，可信behavior命令故意返回17，其他两项通过。真实executor在inventory的baseline门禁返回FAILED；没有启动inspector命令，无model-log/agent-selection，原workflow为BLOCKED且candidate保持基线。正式export拒绝非REVIEW_READY，目标分支不存在，原prepared导出意图保留；正式reconcile以原native适用outcome摘要释放精确claim，原BLOCKED和main保持。该实验验证预先声明的可信检查失败，不改真实业务门禁以取得通过。

在两个独立可丢弃clone调用同一冻结Sandbox/process_job的真实只读monitor：一例写未跟踪文件，一例创建空commit移动HEAD；命令本身返回0，但monitor均以126及“read-only changed the checkout or HEAD”拒绝。原业务仓库不变。这里只验证review等只读stage共用的monitor边界，没有Temporal工作流、真实模型或review回执，不能扩大为恶意agent隔离证明。脚本/终态为`probe-readonly.py`、`mutating-reviewer.py`和`readonly-probes.json`，两例合计3.51秒。

## d协议反例与证据分工

下表区分本次实际服务与固定7139d1a最终711项回归已有的可控协议故障；代码/测试未变，后者使用原命令与日志，不重复昂贵回归或将其改写为网络/系统故障演练。

|边界|已核证据与范围|
|---|---|
|重复start/export|c真实HTTP/CLI两轮重开，原run和分支不重复；d重复reconcile/resume保持同一回执|
|错误/旧计划|c真实等待批准期间错误SHA无owner回执/attempt/signal；正式批准合同测试wrong_plan_or_run、expired_decision、same_decision_id覆盖过期与漂移，不对已完成c任务改写批准|
|候选/分支漂移|固定回归test_task_export的outcome_identity、other_owners_branch、unknown_recovery_preserves_deleted_branch_and_drifted_outcome等；真实Git/可控SDK，不声称在当前服务篡改已通过候选|
|丢响应/中断/未知不重发|固定回归test_task_submission/approval/export/reconciliation各原interruption与lost_parent_response；b2实际SQLite提交后丢响应恢复，不声称此次真实RPC被切断|
|review改checkout/检查失败|上述实际冻结monitor两种126拒绝、真实服务baseline exit17阻断；候选/检查/独立review身份另有固定AdapterTests及c真实正向证据|
|取消/进程/worker恢复|本d两原run、8个精确原进程消失、同一Temporal/executor和新worker、原取消结果保留、独立清理证据及lease精确释放|

验收辅助准备首轮使用非数字issue ID被原合同拒绝（尚无task创建/提交）；恢复脚本曾把输入注册定义与规范投影直接比较；失败实验脚本曾把git clone stdout当JSON、把按命令摘要索引的baseline记录当检查名索引。均保留初始脚本和失败命令，按实际合同修正或沿已创建原run另开finish脚本继续，没有重提已运行任务、改生产/测试或删历史/ledger。

d实际验收及[新的独立异常/结构审查](2026-11-03-formal-task-recovery-review.md)均通过。第4个采样进程误标monitor的P2已修正复核关闭，无未解决finding；独立核算173份索引、三原history和138文件实时查询前后身份保持。完整F3还需e手册/当前架构与身份汇总及综合审计。已确认5原run均闭合且无RUNNING workflow，通过正式shutdown关闭本次专用栈、保留持久数据，没有管理其他旧服务。公开文档只保留验收摘要，模型原文、凭据、运行数据和检查缓存不提交。
