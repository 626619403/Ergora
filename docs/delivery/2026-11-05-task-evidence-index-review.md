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

## 精确提交、发行、静态与实时远端续核

日期：2026-11-05，同一独立审查者续核。精确候选为 `2c0ddbccd25dda66d971eadd6770b61877c83bb7`，唯一父提交为 `da80e777f9ccb1caf6de54f66d245669d953b8d2`。本节只使用该候选的 Git 内容及原发行/交付证据；后续工作树与 F5.2 不归入本片。

- **精确范围及提交通过。** 独立读取 Git 父子关系、17 个变更路径和全部 blob，逐项 SHA256 等于 `staged-scope.json`，路径集合也与 `commit-command.json` 完全一致。新增测试保持上文已审摘要；六个生产文件保持原审及发行身份。原 `commit.stdout` / `commit.stderr`、exit0、完整 HEAD 均已核；精确父子 `git diff --check` 独立通过。
- **精确发行身份通过。** 独立在内存解析候选 `git archive`，350 份应用资源的完整路径及字节摘要等于实际 wheel、两处 noneditable 安装及 `package-identity.json`。实际 wheel SHA256 仍为 `9e3caeb50dc327109d06025933cdd83fff629681ea9c91f7476c8b5d3eabcf74`，与 `commit-package-identity.json` 相符。没有重新构建或安装。
- **最终静态文档通过。** 候选中的十份 Markdown blob SHA256 全部等于 `static-documents.json` 和 staged scope。审查者另从候选的内存归档重核本地链接/锚点，实际 331 条、零 missing；使用同源已核发行的 CLI parser 重新解析该候选 README 的 28 条命令，命令内容及数量与记录一致。没有运行这些命令对应的任务操作，也未覆盖作者证据。
- **普通快进推送及实时远端通过。** 已核 `push-remote-identity.json`、原 remote 前后 stdout/stderr、`push-rsa.stdout` / `push-rsa.stderr`：原推送 exit0，快进 `da80e77..2c0ddbc`，前后完整远端身份吻合。此前默认代理 HTTP407 为独立的只读预检失败，原日志及修正记录保留，没有归成推送通过。审查者于 `2026-11-04 21:00:42 UTC` 使用现有 RSA/CONNECT 传输及仅本次命令的 URL 改写，独立执行只读 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`；exit0、stderr 为空，实时远端返回完整 `2c0ddbccd25dda66d971eadd6770b61877c83bb7`。没有读取或输出私钥内容、修改 Git 配置或推送。

**本片源码/本地验收、精确提交与原发行身份、最终静态文档、普通推送及独立实时远端复核通过，无新增 finding。精确双 OS CI 尚未核验，F5.1 仍保留该项与同片最终终结，暂不登记完整交付完成。** 本次仅追加本报告，没有重复重型套件或三 run 验收，没有启动服务、执行模型或修改源码。

## 精确 CI 与同片最终终结

日期：2026-11-05，同一独立审查者续核。精确候选仍为 `2c0ddbccd25dda66d971eadd6770b61877c83bb7`；官方 [Portability CI 41911536059](https://github.com/626619403/Ergora/actions/runs/41911536059) 已完成并显示 **Success**。当前 F5.2 生产/测试工作树与其新发行不归入此次验收。

已读取 `fetch-ci.py` / `verify-ci.py` 及保存的官方 actions、run、两 job HTML、job-groups JSON、selection/status JSON，另以只读内存解析核验，未运行会覆盖原证据的脚本。六份原来源的实际字节数和 SHA256 全部等于 `ci-html-status.json`；actions 中精确候选行及其摘要、run ID、完整 commit 链接和 portability workflow 链接相符。run 为 Success，两 job 的页面平台名称、`selectedJobId`、必要步骤的 completed/conclusion 和含完整候选 SHA/job ID 的 log URL 均逐项吻合。

|平台与精确 job|独立核实的必要步骤|
|---|---|
|[Ubuntu / Python3.11，126860081709](https://github.com/626619403/Ergora/actions/runs/41911536059/job/126860081709)|Build and install wheel、Packaged reference identity、Native application regression 均 completed / success|
|[Windows / Python3.12，126860081963](https://github.com/626619403/Ergora/actions/runs/41911536059/job/126860081963)|上述三步及 Windows PowerShell 5.1 installer and upgrade 均 completed / success|

全部实际 check-step 无 failure/cancelled/timed_out；Ubuntu 的 Windows 专用步骤按原条件 skipped，Windows 该步骤成功。已独立读取精确提交的原 workflow，并核它相对父提交没有变更：Native application regression 仍执行全量 `tests` 及各平台适用的冻结参考套件，双 OS 矩阵和 20 分钟上限保持。本审查未下载逐行测试日志或推造具体用例计数，也未重复本地套件或三 run/服务验收。

审查者另于 `2026-11-04 21:13:47 UTC` 使用既有 RSA/CONNECT 配置执行只读实时远端查询，exit0、stderr 为空，分支仍精确返回完整 `2c0ddbccd25dda66d971eadd6770b61877c83bb7`。没有推送、修改 Git 配置或源码。

**最终结论：F5.1 需求符合性与可维护性通过；源码及本地验收、精确提交/原包身份/最终静态文档、普通推送/实时远端和精确双 OS CI 的同片复核全部通过，无未解决 finding 或本片剩余验收项，F5.1 可登记完成。** 本节关闭上文按当时状态保留的 CI 待验项；本次唯一写入为追加原审查报告。F5.2 及后续 F5/G0 的范围、包、CI 与独立审查仍分别验收。
