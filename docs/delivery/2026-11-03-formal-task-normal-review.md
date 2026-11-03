# F3.4c 正常正式任务旅程独立审查

2026-11-03，审查者 `/root/formal_task_normal_review`，全新独立上下文。先读取原 F3 验收、正式操作脚本、原始运行/命令/失败记录，再对照作者交付叙述；遵循项目 AGENTS.md、maintainable-project-delivery 的独立审查约定及 review-pr。审查只读原源码、候选和原始证据，仅在本报告及私有 `normal-reviewer/` 写核算资料；未调用模型、重跑任务、安装、启动/停止服务、修改原 state、提交或推送。

**需求符合性：通过，限 F3.4c。** 两开发模板均经正式 CLI 入口和真实执行栈完成六阶段，固定原 spec/memo/run/候选；正式分支导出、独立 worktree 可信复验和 HTTP/CLI 重开证据成立。发现一项证据范围表述问题，作者已修正并经本审查复核关闭，当前无未解决阻塞 findings。该结论不验收 d 或完整 F3/e。

**可维护性：通过，限本次文档与验收证据切片。** 没有生产、测试、依赖、冻结执行器或六阶段合同变更；正式操作继续由现有 tasks/reference 用例及原 Temporal、executor、monitor、准入 ledger 所有者负责。私有验收脚本消费现有接口，没有新增产品调度/持久化框架或绕过门禁。候选中治理 AST 检查有真实基线及合成拒绝样例；大型变更的纯汇总模块与 CLI I/O 分工符合冻结任务范围。未发现本切片引入的结构或性能退化。

**Finding 及处理：**

- P2，已关闭，位置：[交付记录第 51 行](2026-11-03-formal-task-journeys.md)。初稿称所有操作 journal 均做过 HTTP 前后字节摘要对照，但 `reopen-normal.py` 在 `ergora/` 下按 `task_id in path.name` 选文件，漏选 decision 子目录中的 8 份批准 journal，且未选 `approvals/` 中 2 份 owner 回执。后果是把 104 文件的快照结论扩大到未对照文件。最小修正是限定实际覆盖范围并列明缺口，作者已完成；本审查独立确认 104 份前后及当前 hash 一致、这 10 份文件未进入原快照。另核这些批准文件当前内容与原 signal、plan、owner 摘要相符，但不据此追认 HTTP 前后字节不变。未重跑或改写原记录。

**精确审查身份与文件：**

- 生产/测试基线 `7139d1a85cdce13689d75471620da8dd143156a8`；审查 HEAD `a170dd12cf7f672e7dffb9c89ebc03b398506091`，后者仅 b2 文档。入场时三份未提交 c 文档为 `docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/delivery/2026-11-03-formal-task-journeys.md`；审查期间该记录新增 d 计划/进展，不纳入本 c 运行验收。
- 独立复算 wheel SHA256 为 `c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb`；源码、wheel 和实际 `.venv-dev` 非 editable 安装的 347 文件逐份一致。当前 `src/`、`tests/`、`pyproject.toml` 与生产/测试基线无差异；复制 runtime 的 279 文件及原冻结清单 283 文件也一致。
- 检查原计划 F3.4 验收/迁移边界、上述文档、私有 `prepare/start-services/create-start/approve-plans/inspect-normal/export-normal/reopen-normal` 脚本及对应命令/log、五份 `normal-*.json`、两份完整 history、原生 task/spec/request/receipt/artifact/操作 journal、选定模型 monitor/stdout/stderr、可信检查脚本和候选 Git diff；邻接源码检查 `tasks.py`、`reference_task_submission.py`、`reference_task_approval.py`、`reference_task_export.py`、`reference_executor.py`、`stage_driver.py`、`agents.py` 和原 workflow/ingress 所有者。

**独立核算的事实：**

|模板|原 run|精确 candidate|history / unique job / 模型阶段|
|---|---|---|---|
|repository-governance|`01a1a106-8352-7c7a-96c3-4a8efd34ac5b`|`ebb9f7bed44a110bc7a9d895c49ac6175f4b4c45`|302 / 7 / 5|
|large-change|`01a1a106-9420-7808-a9a8-05f6268f8d27`|`6ad080e1f3ac58d6312fae7f969d03fcbb63c112`|326 / 6 / 4|

两新 repo 的 main/原 HEAD 均为 `f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`，分别只注册一个模板。4 角色冻结绑定 Codex / `gpt-6.1-sol` / current-container，revision 5，模型 job 预算 600 秒、executor 上限 2；两套新配置/state/control 与旧验收分开。服务命令和 doctor 原回执表明新 Supervisor 栈就绪；9 份原模型 stdout 均含独立 thread/turn started 及 turn completed，monitor 均 returncode 0，prompt/result 摘要匹配原 agent-selection。仅核事件与摘要，模型原文和机器路径留私有。

每份 history 的事件 ID 连续，最后事件为 WORKFLOW_EXECUTION_COMPLETED；原 start 输入逐值等于本地 spec，原 run/workflow ID 和 submission memo 等于原提交 intent 摘要。请求/profile/spec 摘要、全部 13 个 dev_submit context/envelope、回执与每份 artifact 均独立复算匹配。工作单元仍保留 `work:unit` 原合同，治理 2 单元、大型 1 单元，覆盖 inventory/plan/work/integrate/verify/review。

错误计划只留 prepared 意图：无 owner 回执、attempt、result 或对应 signal；正确计划各恰好一个 approve_plan signal，payload、owner 采用摘要、精确 plan receipt 以及后续各 context 的 approved_plan 一致。最终 outcome 的 verification/review 和 evidence 摘要均指向同一精确 candidate，所有要求检查 pass；reviewer session 与 work 作者不同。正常成功任务没有 fence，原 external-status 的 external_confirmed=false 被保留，不能把这次正常导出当作已完成 b2 异常外部对账。

正式 export intent/attempt/result、`agent/TASK_ID` 分支及本地 native export 相符，重复 export/export-status 返回原回执。独立读取 ledger 的 DB/WAL 字节副本，没有打开原数据库写连接：

- 治理精确 claim `027958027937d3d3f79e954cbdd9f6a1e9f68540b58b19524c8d961c1a54624a` 已释放，evidence digest 为原 outcome `88b849ee553e0d5e34636eff6f4366e6f28555ad975bcc2cf0a0305de0e074d1`。
- 大型精确 claim `693d54c6987a5ad98a1c44440e3b93bc0cdc515407e9064b4cfe9a2d20ded7ef` 已释放，evidence digest 为原 outcome `9f384dce21ca97c343bd572f84242d4c8061f4368fe5c85c801bd87762a6340d`。

两者 resource/owner/task/spec 均绑定原准入记录，active 中无对应 claim。原业务 main/HEAD 保持基线，导出分支精确命名候选，独立 detached worktree HEAD 相同，repo/worktree 均干净；祖先关系、diff --check 和 3/5 个变更文件范围成立。记录中的独立 worktree 可信脚本摘要保持，治理 3 项/大型 6 项全部实际通过；直接 unittest 原日志为 4/11 项通过，治理另显式 discover 3 项 AST 用例通过，默认 CLI 为 9，大型 opt-in 分组为 build=6/test=3。本审查未再次执行这些候选测试。

两轮 serve 的不同 PID、完整 shutdown 日志、每轮访问顺序与 `normal-reopen.json` 相符：44 份记录请求中 36 个 200、8 个 403；另有每轮一个 bootstrap。两项目的详情/creation/submission/固定 run 状态/external-status/export/list 与新 CLI 进程比较成功，跨源读取及缺请求头的写入拒绝，重复 start/export 返回原 run/回执。104 文件快照前后相同且本次读取仍匹配，批准文件的快照缺口按上述 finding 保留。

**检查方式、性能与待验边界：**

独立核算入口及结果位于私有 `.ergora/checks/f3-formal-journeys/normal-reviewer/audit.py`、`audit.json`，运行 `PYTHONDONTWRITEBYTECODE=1 python3 .ergora/checks/f3-formal-journeys/normal-reviewer/audit.py` 通过；仅用标准库读取、hash、Git 查询和 ledger 副本。原辅助脚本的 binding 参数、SDK to_proto、work:unit、urllib Request.method 四类失败及修后成功日志均保留，核到的失败发生在验收辅助代码，没有变更产品或重发未知任务。

性能结论仅限原环境：最终 inspect/export/reopen 记录 6.25/15.75/57.85 秒，不能视为优化对比。9 个模型 monitor 单次约 25.15–68.08 秒，时间区间峰值并发 2，与显式资源上限相符；没有测 CPU/内存峰值、持续吞吐、跨机/规模化或可用性保证，也无新生产热路径变更据以宣称收益。

真实取消、父子进程终止、worker 停止重开、异常 fence/终态对账/claim 释放以及旧计划/候选漂移/审查 checkout 篡改/失败/丢响应的新增异常演练属于 d；完整 F3 收口及新的大节点综合审计属于 e。未重跑完整回归/两 OS CI、Windows 原生执行、缺认证/权限场景或任意真实业务仓库；以前切片结果保留原身份与范围，不由本报告扩张。本次没有合并、部署、推送或改变业务 main。
