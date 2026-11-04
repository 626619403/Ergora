# F5.1 原任务证据引用索引：独立审查

日期：2026-11-05。审查者：独立 agent `/root/evidence_index_review`。使用新的上下文，只接收原始范围、基线、文件及实际验证位置；先读 AGENTS、独立审查规范、原始 diff 和相邻实现，再读作者交付记录。项目及报告归属均为 Ergora。

**需求符合性：本片源码与本地验收通过。可维护性：通过。范围内无未解决 finding。** 本结论不代表本片已提交、推送或通过精确双 OS CI；这些交付项仍须另行完成并由同片复核。

## 精确范围

- 基线及审查时 HEAD：`da80e777f9ccb1caf6de54f66d245669d953b8d2`；本片生产改动尚未提交。
- 六个生产文件：`src/ergora/cli.py`、`reference.py`、`reference_task_reconciliation.py`、`reference_task_submission.py`、`tasks.py`、`web.py`。这六文件的完整 `git diff` 输出 SHA256 为 `ef7aa7973a4054049585580016b66473f608cf2a71fd3adcf895663b80b95f4c`。
- 新增 `tests/test_task_evidence_index.py`，文件 SHA256 为 `83c6e87be44c63093578f9bbc9f046884a90daee8a80e63d17bf382cc8510e1e`。
- 对照 [F5 分片合同](../plans/2026-11-05-evidence-handoff.md)、[交付记录](2026-11-05-task-evidence-index.md)、README、USAGE 和当前架构。相邻创建/提交、原 job 证据、FileAdapter、activities、workflow 及对账 checkpoint 均已追读。完整工作树中的 F5.0 审查/交付终结追加属于前片状态归档，未当作本片运行证据。

## 代码判断

1. `tasks → reference → _Inspection` 延续原职责，没有新增生产模块、依赖、持久账本或抽象框架。CLI 与 GET API 是同一用例的两个实际消费者；reference 包装继续承担专用进程边界。`_Submission.creation_record` 保留本次已验证的原快照，避免为索引重新读取创建记录。
2. 原创建/提交/spec/memo/run 归属、闭合且无后继检查、连续完整 history、单 payload/SDK codec、请求 envelope 和 FileAdapter 根/回执/逐材料 SHA 校验均复用原所有者。重复同 context 调度只追加 event 引用；冲突仍拒绝，`history_jobs_sha256` 仍仅由原 job 身份构成，对账 checkpoint 未改变。
3. 仅 `inspect-index` 返回完整已核回执及引用扩展。原 external-status 和对账 job 行的字段集合保持；只读分支不经过 fence 发布、写记录或 lease 释放。必要的外部输入、持久归属、缺失/损坏材料和资源上限守卫均有可达失败场景，没有发现需删除的重复断言或无用回退。
4. `published_evidence` 只陈述当前材料核验，原 outcome 不改写；verification/review 的显式摘要比较独立呈现。无引用、无可信回执、摘要冲突和未记录上下文分别保留其状态，未以 SUCCEEDED、材料存在或当前配置推导过去采用、任务成功或清理成功。
5. 新测试复用既有轻量 fixture，使用真实 SDK 消息/codec 和本地 FileAdapter；覆盖输出合同、引用匹配/冲突/缺失、重复调度、错误原范围、坏材料、安全路径、CLI/API、错误传播及超大响应。没有新增 CI 矩阵或通用测试框架；未发现为了断言实现细节而值得删除的测试。

## 已核证据与成本

作者实际运行的命令、退出码和原日志均已读取，分别为源码 43 passed（pytest 2.97 秒）、发行包新增 23 passed（7.85 秒）、两模板旧 external-status/对账代表 4 passed（36.50 秒）。首轮 42 项中的文案期望失败被保留，不合并成一次全量通过。本审查没有重复这些测试或运行重型套件。

审查者另行只读复算当前源码、实际 wheel、两处 noneditable 安装的完整路径集合及字节摘要，350 资源逐项一致；冻结 283 reference 资源与 F4 原记录一致。实际 wheel SHA256 为 `9e3caeb50dc327109d06025933cdd83fff629681ea9c91f7476c8b5d3eabcf74`。基础安装无 Temporal SDK 的原命令/log 已核。

已读真实三 run 验收脚本、命令/log 和结果，再独立比较落盘 CLI/API、原 outcome、原回执和材料字节。实际为三 CLI、五个进程内 ASGI GET（含错误 run 和跨项目各 HTTP400）；成功端点执行真实登记原生子进程与 Temporal RPC。此证据不包含外部 HTTP socket 或浏览器测试。

|原范围|history 事件|job|材料数 / 字节|观察|
|---|---:|---:|---:|---|
|repository-governance 正常|329|7|23 / 105296|REVIEW_READY 保持，verify/review 各 matches；无 fence|
|large-change 正常|348|6|19 / 156248|REVIEW_READY 保持，verify/review 各 matches；无 fence|
|repository-governance 取消|112|1|1 / 59|原 CANCEL_UNCONFIRMED 保持，后续清理确认单独为 true|

三个 CLI 为 1.76–2.37 秒，ASGI 端点为 1.47–1.58 秒，CLI 响应 15347–32101 字节；仅证明当前小规模、本地持久 Temporal 及包含启动/预检的整体耗时。未测大 history、并发吞吐、峰值内存或优化收益。

完整 history 被扫描，原 context 保留至核验结束，每个回执的所有材料由 FileAdapter 重新读并算 SHA；共享材料也可能重复读取。新增索引没有逐 job 再查 history。1 MiB 是最终响应上限，检查发生在读取和组装之后；16 MiB 是逐材料限制，两者均不是总 IO/内存上限。查询采用 1–60 秒预算及父进程另 5 秒超时，本地合同预检另计；同步文件读取的中断最终依靠外层进程超时。公开手册已披露这些实际成本，没有把体积上限或上述小样本当作规模性能保证。

已独立比较 `native-before.json == native-after-verified.json`，并重新读取当前 139 份原证据文件核摘要；三份完整 history/outcome、两 repo 文件/HEAD/refs/worktrees、三 claim 和零 active lease 的前后记录一致。已检查 shutdown 与最终离线脚本、真实 argv/log/result：仅本次专用 Temporal 被启动，worker/executor 保持停止；正式 shutdown confirmed，两个专用进程退出、四端口关闭、三份持久数据库保留，最终离线又核 139 文件和 leases 不变。审查者未启动服务、调用模型、发任务信号或写执行状态。

证据位于忽略的 `.ergora/checks/f5-task-evidence-index/`：`package-identity.json`、`index-contracts-fixed*`、`wheel-contracts*`、`legacy-representative*`、`original-index*`、`native-before.json`、`native-after-verified.json`、`shutdown-final*`、`final-offline*`。本报告不收录运行配置、机器路径或凭据。

## 交付边界

本地功能、结构/复用、必要守卫及测试成本范围内无 finding；本片验收可进入正常提交交付。仍需绑定精确提交重核最终文档/包身份，完成正常推送、实时远端核对、精确双 OS CI 和同片终结复核。前片 F5.0 的通过不替代这些项；F5.2 预算、F5.3 归档、F5.4 页面及完整 F5/G0 不在本审查完成范围。
