# F3.4d：异常与恢复独立审查

日期：2026-11-03。审查者：Codex fresh-context agent，任务标识 formal_task_recovery_review。未继承实现对话；先读取[原验收要求](2026-11-03-formal-task-acceptance.md)、原始脚本、命令和失败日志，再检查[c/d交付记录](2026-11-03-formal-task-journeys.md)的 d 部分及相邻实现。

**需求结论：范围内通过。可维护性结论：范围内通过。** 初审一项证据范围 P2 已修正并独立复核关闭，当前无未解决 findings。此结论只关闭 d；c 由[另一份独立审查](2026-11-03-formal-task-normal-review.md)负责，e 综合收口及完整 F3 仍须分别验收。

**Finding 与复核**

- **P2，已关闭：直接采样的第4个进程被误标为 monitor。** 位置：[交付记录第76行](2026-11-03-formal-task-journeys.md#d真实取消重启与终态对账结果)。原文将每任务4份 PID/starttime 记录解释为命令父进程、忽略 TERM 的子进程、stage driver 和 monitor。实际 recover-cancel.py 通过祖先 cmdline 子串选择进程；冻结 process_job.py 的 Popen 启动 /usr/bin/timeout ... ergora.stage_driver，因此第4份是 timeout 包装进程。两份 pid.json 与所列包装进程匹配，started.json.monitor_pid 则另有 PID，没有纳入直接 starttime 采样。原文会使读者误以为 monitor 的系统进程消失也已直接验证。最小修正是正确标注 timeout，并限定 monitor 只有持久 terminal 证据。作者已如此修正；本审查重新对照实际冻结运行文件、父子关系和记录确认，未改原证据、重跑任务或以当前进程不存在追认历史。

**审查身份与范围**

生产/测试基线及实际发行均为 7139d1a85cdce13689d75471620da8dd143156a8；审查时 Git HEAD 为文档提交 a170dd12cf7f672e7dffb9c89ebc03b398506091。原已跟踪审查增量为 docs/PLAN.md、详细计划和 c/d 交付记录；d 没有生产、测试、依赖、workflow 或冻结参考发行变化。审查期间作者另行开始的 README、手册、项目导航、当前架构与 F3 阶段收口记录属于 e，不包含在本报告的通过范围内。

独立重算安装 wheel SHA256 为 c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb，与环境及安装分发元数据一致；非 editable 开发安装的347个包文件与当前源码逐字节一致。实际运行的 sandbox.py、process_job.py 也分别与冻结源文件一致。

重点检查 reference_task_submission.py、reference_task_cancellation.py、reference_task_reconciliation.py，原 FileAdapter/workflow、IngressLeases、executor/Sandbox/process_job，以及 task submission/approval/export/reconciliation 的相关测试和故障夹具。私有原证据为 .ergora/checks/f3-formal-journeys/ 内的 environment、recovery-runs/cancellation/reopen、baseline-rejection、readonly-probes、完整 history、stdout/stderr、脚本与正式 command/log。173份索引文件的摘要和字节数全部匹配。

**独立核验结果**

|实际原run|完整history|唯一原inventory回执|原结果保持|精确claim释放摘要|
|---|---|---|---|---|
|治理取消 01a1a11f-dd2d-76d7-a587-a911fb26d239|92事件|CANCELLED|CANCEL_UNCONFIRMED|独立清理 evidence SHA|
|大型取消 01a1a11f-f165-749a-b581-bced244d7a90|81事件|CANCELLED|CANCEL_UNCONFIRMED|独立清理 evidence SHA|
|检查失败 01a1a125-95d0-732b-abac-f662741a4df6|40事件|FAILED|BLOCKED|原 native 适用 outcome SHA|

三个 history 都从事件1连续到原 COMPLETED，起始 spec 与原本地/创建记录相同，提交 memo 与不可变提交意图 SHA 相同。原 dev_submit 均仅一个 unique inventory job，实际 request envelope、可信 receipt、executor ledger 的 job/session/终态和全部8份 receipt 引用产物摘要一致。固定原 run 与最新 run 相同，没有后继 run；业务 HEAD/main 均保持原基线 f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7，checkout 干净。

两个取消任务仅 inspector 使用显式 command/stage-json-v1，其余三个开发角色仍为冻结 Codex 默认绑定；唯一实际执行阶段是 inventory 的受控等待命令。冻结 monitor 请求记录600秒预算。正常 c 旅程与本 d 演示的角色/任务没有混用，也没有把这两个受控命令解释成模型验收。

原服务记录显示只选择 worker 停止，确认为 STOPPED；Temporal/executor PID 全程保持，worker 重开获得新 PID。两个 request_cancel 信号的事件时间均在该停止/重开边界内，且各恰好一次，payload 的 request SHA 与操作 SHA 对应原任务和取消意图；取消 attempt/result 也一致。停止期间原 history 尚未闭合，脚本在取消前后验证已登记进程的 PID/starttime 存活。恢复后的8份直接采样均为 null，覆盖每任务的命令父进程、忽略 TERM 子进程、stage driver 和 timeout 包装进程；这是留存的历史采样事实。本审查没有重新检查当前 /proc 来补造当时的证据。

两个原 outcome 的即时 fence 都是未确认，仍保留唯一 unresolved job；稍后原 fence 文件、唯一 CANCELLED 回执和产物完整。正式 external-status 及四份 reconciliation intent/attempt/evidence/result 对应完整原 history job 集合，没有 unexpected/unresolved job。原 cli-ingress.json、tracker resource、owner、spec SHA、claim ID 与复制后查询的真实 ledger 相同；外部进程停止后、reconcile 前的历史 claim 仍持有，最终释放记录保留且 active 为空，摘要精确等于独立 evidence SHA，未改为成功或覆写原 outcome。

原重复 reconcile、reconciliation 与重开 CLI 都返回同一结果。原恢复脚本与 HTTP 日志/13请求记录相符；其中 resume-reconcile 沿原意图返回，already_closed 的新取消请求没有 attempt 文件且 delivery 为 not_sent。留存重开结果与本次实时 history 都仍各只有一个取消信号。本审查没有重开 HTTP 服务或再次执行这些写操作。

失败演示的原命令摘要索引 baseline 三项为17/0/0，故意失败脚本身份匹配；无 inspector marker、selected 进程记录或 model-log/agent-selection 产物。原 FAILED receipt、BLOCKED outcome 和确认 fence 一致。export 明确拒绝非 REVIEW_READY，目标分支不存在，仅保留 prepared 意图；对账依原 native 合同使用原 outcome SHA 释放同一 claim，未将检查失败改写为通过。

两个只读反例的实际冻结 Sandbox/process_job 请求均为 writable=false，现存 clone 分别保留未跟踪修改和新的空 commit。helper 与执行日志、terminal 相符，monitor 返回126。该结果只覆盖共用 monitor 对 checkout/HEAD 变更的拒绝；没有真实 review workflow、模型或 review receipt，也没有证明恶意 agent 隔离。

**协议反例、失败记录与复用边界**

旧计划/过期决定/相同 decision ID 漂移、候选与分支竞争、丢响应及中断恢复的证据来自固定发行的原测试。已读取对应测试及夹具：它们在真实本地 Git/SQLite 与可控 SDK 的明确故障点检查不重发、保留未知和原归属；SQLite release 夹具确实在原 commit 前/后注入异常。c 的实际错误计划 SHA 与正常批准只作为前切片已记录的真实服务证据使用。本轮没有将协议夹具称为当前 Temporal RPC 断线或对已通过候选进行真实篡改。

原最终包命令/log 以退出0结束于711 passed、19 skipped、36 subtests passed；原精确两OS CI为 [41621015706](https://github.com/626619403/Ergora/actions/runs/41621015706)。本审查核对保存的命令、结果、候选身份以及官方 run/jobs HTML 的原摘要，10份固定发行证据和8份候选源码/测试摘要匹配；没有重新请求 CI、运行回归或把 Linux 计数套给 Windows。

准备失败的非数字 issue ID、注册输入/投影比较，以及失败实验的 clone stdout JSON 解析、baseline 按检查名错误索引，都有首轮脚本与正式失败命令/log。辅助差异仅修正实际接口使用或沿原 run 用 finish 脚本继续；三个当前 history/spec/memo/ledger 仍对应各一个原提交。未发现改生产、删除 ledger、丢弃原失败结果或重提已运行任务来取得通过。

生产所有权仍由现有提交/取消/对账模块与原执行器分别承担；d 没有新增生产抽象或依赖。验收脚本局部复用环境元数据、已有 CLI/HTTP/SDK 及现成的 worker 管理入口，证据与公开摘要分离，控制流程可沿原记录恢复。该切片没有形成需另建公共模块的复用需求。

原 cancellation 主流程32.20秒、HTTP恢复29.43秒、两只读探针合计3.51秒，仅是本环境的命令墙钟观察。并发上限2、每 stage 600秒、轮询/终态等待均有边界；没有实测 CPU、内存、规模化 history 开销或吞吐变化，也没有性能收益或无回归的比较结论。既有冻结实现的成本没有因本次文档/验收改变。

**本次审查执行与未验范围**

实际执行私有 recovery-reviewer/audit.py 的标准库核算、live.py 的只读 Temporal describe/history/result/memo 查询、Git/hash/链接与差异检查；138份选定原 task/request/receipt/artifact、fence、JSON process/journal 文件在实时查询前后摘要不变。SQLite 先复制 DB/WAL/SHM 到审查私有目录，查询复制品，没有让 SQLite 打开原库。审查核算结果为0条身份/合同不一致。

可复查核算保存在 .ergora/checks/f3-formal-journeys/recovery-reviewer/ 的 artifact-audit.json、live-audit.json、baseline-audit.json、database-snapshots.json、原文件前后摘要和独立实时 history。审查只写该私有目录和本报告；未安装、测试、调用模型、修改原运行记录、启停服务、提交或推送。

未验：monitor 的 PID/starttime 直接消失采样；容器/主机掉电、强制崩溃、跨机接管、任意逃逸后代进程；真实 RPC 断线与当前服务中的旧计划/候选篡改；真实失败 review 的全链路；Windows/WSL2 的真实服务恢复；CPU/内存/吞吐和规模化性能。e 的手册/当前架构/最终身份、阶段综合审计、独立栈最终关闭及提交交接由后续记录负责，本报告不提前验收这些事项。
