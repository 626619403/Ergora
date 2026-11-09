# CR4 服务生命周期独立审查

审查者：fresh-context Codex reviewer `composition_lifecycle_review`。初审：2026-11-09 02:03 UTC；本地终核：02:23 UTC。应用 `maintainable-project-delivery` 的 independent-review 及 `codebase-design`；只读源码、原始证据，唯一写入为本报告，未运行模型、安装、旅程、提交或推送。

## 固定范围与当前结论

- 固定基线与终核时 HEAD：`8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`，父提交 `6826047031aebddb7eb6c5fcf43cfe91ebb45ada`。初始计划复用 CR3c 发行；实际发现 C1 后，同片增加一行生产修复及三个测试文件，未修改依赖、CI 或 283 冻结文件。CR3c 远端/CI 追加属于前片历史记账，不是新增行为。
- **需求符合性：本地通过。** C1 经旧包红例、最小修复、新包合同及真实原服务旅程关闭；范围内没有剩余阻塞 finding。
- **可维护性：本地通过。** 修复复用原版本化输入 Interface，完整文档用于身份、legacy 投影用于原 ID/signal；服务、六阶段、批准、monitor、receipt 与 ingress claim 的所有权保持集中，没有新调度器、账本、版本分派或重复校验。三例回归保护可达缺陷、未知投递恢复及 admission 碰撞，未扩测试框架或 CI 矩阵。

生产/测试精确范围如下；相邻调用链另读 `reference_task_submission.py`、`reference_task_runtime.py`、`reference_inputs.py`、`reference_worker.py`、`reference_workflows.py`、`reference_executor.py`、`reference_task_approval.py`、`reference_task_reconciliation.py`、`services.py`、`processes.py`、`stage_driver.py` 及原 Supervisor/Temporal workflow/adapter/process monitor 的有关实现。

|候选文件|终核 SHA-256|
|---|---|
|`src/ergora/reference_task_cancellation.py`|`19d5725d97fcb6197fd409508328335bd9e5b33e2d262289ec63dbb8c376b8fc`|
|`tests/test_composition_tasks.py`|`76dedd91db83a4d27e4abf9654dab5ae7fcd3126849590098027f92fb99a7110`|
|`tests/test_task_cancellation.py`|`0ba2341c306d1e55b76f583bfd88463072e966dbc3975cd13967e2e171c47d33`|
|`tests/fixtures/task_cancellation_client.py`|`e6c8682507a76186ee6895b0582873dcefde9c856abb350f772655c468290d92`|

记录范围：`docs/PLAN.md`、`docs/USAGE.md`、AC 计划、运行桥总记录、CR3c 交付/独立终结、CR4 交付/本报告及四份 `2026-11-09-cr4-*` evidence JSON。公开证据逐份与缓存原件 JSON 比对相同；原始运行缓存位于忽略的 `.ergora/checks/ac3c3-lifecycle/r1`–`r3`，不是新增正式运行框架。

## Finding

### C1 / P1，已关闭：v2 公开取消误用 legacy projection 校验完整原历史

位置：`src/ergora/reference_task_cancellation.py:126`；来源：`src/ergora/reference_task_submission.py:33`、`:38`；身份校验：`src/ergora/reference_task_runtime.py:49`。

旧 `_Cancellation.prepare()` 将 `self.spec` 设为 `_Submission.spec`，后者是 `self.input.spec` 的 legacy 六阶段投影；旧 `dispatch()` 却以此构造 `VerifiedSpecClient`。公开 v2 任务的原历史保存完整 admission，严格 JSON 校验因此在 signal 前拒绝，阻断活动审查取消及后续恢复。

最小修复已实施：该调用使用 `self.submission.input.document`，与原 `_Submission.lookup_run()` 一致；保留完整 admission 身份检查及原取消的投影契约。原 cancellation 测试只消费 v1 SDK fixture，确实缺少 v2 保护。

实际红例已独立核：R2 持久运行根的 `cancelled-v2-cancel.stderr` 正是该 JSON identity 错误，`r2/lifecycle.log` 在公开 CLI 调用处失败；该轮没有到达 cancel 完成、新 v1 或最终验收出口。`r2/cancellation-red.log` 对原 wheel 的新增三参数回归为 `2 failed, 1 passed in 19.06s`：正常及丢 ack 被错误拒绝，同 legacy/不同 admission 正确拒绝。

同片修复复核：生产仅改上述一行；`tests/test_composition_tasks.py:246` 加正常、丢 ack、不同 admission 三例；既有 SDK fixture 与 v1 装配解耦，handler 复用 `execution_input(...).spec`。回归跨公开 `tasks` 与原 lookup seam，核原信封不变、信号零/一次及原 intent/history 恢复。新非 editable 包 **50 passed /320.19 秒**；实际 v2 原历史包含一次 `request_cancel`，review 终态 CANCELLED，后续 external-status/reconcile 与原 claim 均已核实。C1 关闭。

### E1 / 非阻塞，已处置：旅程汇总的字面量身份不能单独证明执行包

自身模板指出 `.ergora/checks/ac3c3-lifecycle/r3/lifecycle.py:272` 的字面量 wheel SHA 和工作区 hash 单独不足以排除旧安装包。该观察在其附件范围内成立，原结果完整保留。处置是独立核实际执行安装：R3 运行前 **02:07:46.102333 UTC** 与运行后 **02:20:01.993947 UTC** 的实际 wheel、同一非 editable venv 和源码，369 文件 map 全同，283 冻结保持；本审查又直接从 actual wheel/installed/current source 重算相同。实际 CLI 显式使用该 venv，源码四文件及自身模板 13 源身份均匹配。因此本次身份缺口已闭合，不把汇总字段自身当证明，不改原自审或机械重跑未变行为。

旧 wheel SHA 为 `306677fdd8df02fbac1b862e5dec4ac6d572bd52a3d88e5ce96af8ff18e03d3a`；新候选为 **`aaa55f011bbc8ddcdfead0e1d59859695f07f6d7f80ddbdb309d26e37d98e703`**，包内仅 `reference_task_cancellation.py` 改变。旧 134 项检查仅是 CR3c 历史，不替代新候选证据。

## 独立核验结果

- 已读项目 `AGENTS.md`、计划及本片记录；核对 R1/R2/R3 探针。R1 原 `FileNotFoundError` 是装配漏建 `config/supervisor.d`，发生于 services 启动前。R2 除公开 cancel 红例，还在服务停止两秒后观察到 4 个原 monitor 相关进程，稍后同 PID/starttime 全退出；两份结果均保留，不把服务 confirmed 当作外部作业已停。
- 已沿 `services.control/_prepare` → 原 Supervisor program 配置 → `reference_worker` 的两版本 Worker → `reference_executor.main/request_roots` 检查真实生产调用链。幂等 start、非选服务停止、原 state DB 和不接管 legacy socket 均有明确所有者；公开 status 仅读原运行，不会启动服务。
- 已读原 `process_job`、`processes.run(supervised=True)` 与 `stage_driver`：fence 由原 monitor 消费，专用 driver 请求取消并收养、终止和回收后代。`CANCEL_UNCONFIRMED` 保留原事实，不自动改称停止；原 external inspection/reconcile 要求完整原历史、匹配 request/receipt/fence，释放时核原 claim，保持原 outcome。
- 新包检查完整 argv 见 `r3/check-command.json`：安装包 `python -I -m pytest -q tests/test_task_cancellation.py tests/test_composition_tasks.py::test_composition_cancellation_preserves_full_input_and_original_signal_recovery tests/test_architecture_boundaries.py`，加持久 basetemp，exit 0、50 passed。审查者核原日志、未重复执行测试。
- [R3 实际旅程](evidence/2026-11-09-cr4-lifecycle.json) exit 0、**428.35 秒**。原 Supervisor 两次 daemon 启动/停止、幂等 PID、未选服务 STOPPED、实际 Temporal/UI/A2A 监听均有原件；原待批任务整栈 shutdown 后 status 是真实 `ConnectionRefused`，不自启动；同 DB/原 run/原 plan/两份原 receipt 恢复，重复 start 未重派，同 legacy 不同 admission 的真实 SDK 查历史拒绝。

|原任务|历史事件|review receipt / 原 outcome|完整输入、队列、SDK replay|
|---|---:|---|---|
|resumed-v2|161|SUCCEEDED / REVIEW_READY|已核，v2 专用队列|
|rejected-v2|167|FAILED / BLOCKED|已核，v2 专用队列|
|cancelled-v2|162|CANCELLED / CANCEL_UNCONFIRMED|已核，v2 专用队列|
|legacy-v1|161|SUCCEEDED / REVIEW_READY|已核，原队列，无 admission context|

- 四条原历史事件连续、首输入与保存文档一致，六个原 submit context/receipt 摘要匹配；已独立核 **24 receipt /87 artifact /4 owner-plan**，包括原授权 activity 及批准 signal。四 history 文件 SHA 与 replay 记录一致，SDK replay 是原探针已执行并留存的证据；本审查不冒称重新运行 SDK replay。
- 取消实际投递 ack 仍返回 `cancellation_confirmed:null`；原历史恰一次取消 signal，monitor/fence 后产生 CANCELLED receipt。验收副本的忽略 TERM 子进程迟写窗口为 10 秒，终态后 10.3 秒观察无 marker；外部状态无未决项，显式 reconcile 的证据、完整 status、原 outcome/candidate 均保持。独立只读 DB 核四原 claim 的 owner/spec 身份，仅 cancelled 释放、其余三条 active 保持，与[原件摘要](evidence/2026-11-09-cr4-evidence-check.json)一致。
- 最终正式 shutdown 后，原 Supervisor 日志与 104 个已观察 daemon/递归后代 PID/starttime 已核；另读 `/proc` 无原存活实例，7233/8233/8765 关闭、managed socket 消失，原 Temporal DB 保留 3,383,296 字节。采样不能证明捕获所有短命进程；终态 receipt 和迟写检查提供另外的作业清理证据。
- [自身模板身份](evidence/2026-11-09-cr4-self-review-identity.json)及[原结果](evidence/2026-11-09-cr4-self-review-result.json)已核：真实 Codex `gpt-6.1-sol` / high / task-MCP、**116.20 秒 approve**。7 个唯一连续页至 `next_offset:null` 重组 **150147 字节**，SHA `0475b998eef6ff27fd334a35772ce5d3872c3820c0c2ed06460d5713f278bde9` 与附件逐字节相同；另一次首页重读一致。首次短路径 read 拒绝保留，随后完整虚拟 URI 成功；scope/audit/prompt/result 及 13 源身份匹配。模型未自行执行这些测试；E1 按上述独立身份实证处置。

记录与限制：已核 `docs/USAGE.md` 对完整取消信封及外部确认的说明，PLAN/本片记录分别保留实现、验收、审查和待交付状态。`git diff --check` 通过；本审查只读重核最终 8 份 Markdown/91 本地链接无缺失，另核实现者 75 条 CLI parser 记录。文档链接/parser 是静态检查，不是运行验收。普通提交、自己的必要 CI 及即时远端精确终结由后续交付记录，本报告只给本地两轴结论，未借用 CR3c 的 CI。

确定性协议 Agent 只证明协议、资源生命周期与可信执行契约；test-operator 是原 owner 合同身份，不推导真实业务人工验收或模型质量。Claude 不可用按用户授权回退，不声称模型错误独立。本轮没有重新验全部祖先权限/资源矩阵或未提供平台；多成员/嵌套仍属 AC4，完整联合备份恢复仍属 AC3c.4。范围内无其他实证 correctness 或 maintainability finding。

## 提交后独立终核：2026-11-09 02:41 UTC

- 固定 CR4 提交为 **`cee213a581895d491c1cd41b5fe79b23bfd09b59`**，父提交 `8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`，分支 `refactor/architecture-foundations`。已独立将 `git diff-tree` 的精确 **16 文件**与 `r3/review-scope.json` 比对，并对每个 `git show <commit>:<path>` 重算 SHA-256，全部一致。提交中的生产树仍匹配上述实际新 wheel，依赖、CI 与冻结文件均无差异；该提交中的本报告 SHA-256 为 `43c50ada4fd72c6962c9c01e896345b50c505108e85890c78df734cfad7f792f`。
- 本片自己的 [Portability run 42551052990](https://github.com/626619403/Ergora/actions/runs/42551052990) 于 **02:41:48.705871 UTC** 独立读取为 **Success**。初始官方 REST jobs 返回的两 job `head_sha` 均为上述完整 CR4 SHA；后续 REST 遇到 HTTP 403 rate limit，最终结论由官方 run 页面及两个固定 job 页面直接读取。每个必要 step 均为 `success`、job 已完成，日志 URL 均指向该 CR4 commit 与对应 job；未见失败、取消或超时 step。未用只返回首项的 job 分页响应代替完整矩阵。

|必要 job|独立核验的成功步骤|
|---|---|
|[native (ubuntu-latest, 3.11), 128946493666](https://github.com/626619403/Ergora/actions/runs/42551052990/job/128946493666)|Build and install wheel；Packaged reference identity；Native application regression|
|[native (windows-latest, 3.12), 128946493982](https://github.com/626619403/Ergora/actions/runs/42551052990/job/128946493982)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|

- CI 读到成功后立即于 **02:41:48.877781 UTC** 发起显式 HTTPS 远端核验，**02:41:50.465610 UTC** 完成，exit 0、stderr 为空：`https://github.com/626619403/Ergora.git` 的 `refs/heads/refactor/architecture-foundations` 精确返回 **`cee213a581895d491c1cd41b5fe79b23bfd09b59`**。实际以 `/` 为工作目录、清除继承的全部 `GIT_*` 环境、设置 `GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_TERMINAL_PROMPT=0`，执行 `git -c protocol.ssh.allow=never ls-remote --exit-code` 加上述公开 HTTPS URL 与精确 ref，排除工作区及全局 HTTPS→SSH rewrite 的影响；未将 SSH 结果冒充 HTTPS。

本片需求符合性与可维护性均通过，固定提交、自己的必要 CI 和即时远端身份已闭合。此节为 CR4 提交后的同片记账，供后续普通提交携带；并不声称这段追加已包含于上述 CR4 固定对象，也不将当前 AC3c.4 工作区变更纳入本次审查。
