# F3.4b1 外部作业证据只读视图：独立审查

日期：2026-11-03。审查者：`/root/f3_task_external_status_review`，新的独立上下文；未继承实现会话。按 `maintainable-project-delivery/references/independent-review.md` 与 `review-pr` 检查实际源码、原始验收及相邻所有者，再核计划和交付记录。本报告依次记录只读源码检查、隔离轻量探针、最终本地发行证据和精确 CI/实时远端核对；没有修改生产/测试源码、安装依赖、运行全量、触碰用户服务或冻结参考文件、提交或外部写入。

终结结论：**F3.4b1 的源码需求、可维护性、最终本地发行、精确两 OS CI 与生产提交实时远端核对均通过；无未解决 finding。** 初审 High/P1 已由原独立反例复核关闭，历史失败证据保留。生产/测试 `a2349e8c3b183918a68935d5199e7c78509364a4`，8 文件 aggregate `85fa8b1dcffadb39bddab760deb8110260ad3e0daa646fafa4d764be90440798`；CI [41597961138](https://github.com/626619403/Ergora/actions/runs/41597961138) 成功，实时 origin 同提交。公开文档的提交/推送由实施者收尾；本结论只关闭 b1，不验收 b2/c/d/e 或完整 F3。

## Finding

### High / P1（已关闭，见源码复审）：孤立回执没有进入额外和未决 job，仍可报告外部已确认

- 位置：`src/ergora/reference_task_reconciliation.py:68–75`、`:99–102`；相应用例 `tests/test_task_external_status.py:235–242`。
- 原因：`files()` 只枚举 `requests/TASK/*.json` 构造实际 job 集合；`receipts/TASK/*.json` 仅对 history 中的已知 job 按名读取。额外回执的文件名具有明确 job 身份，却完全不参与归属检查。由此，不能绑定固定原 history/context 的回执既不被验证，也不进入 `unexpected_jobs` 或 `unresolved_jobs`。
- 可达反例：在真实创建/提交、固定原 run、真实 SDK converter/多页 iterator、三个匹配的 history/envelope/可信终态回执及正确 fence 的隔离夹具上，增加 `receipts/new-task/orphan-job.json`。分别写入按原合法终态回执改 job ID 的 JSON，或损坏 JSON。通过未修改的公开 `tasks.external_status(..., run_id='original-run')` 调用，两个结果均为 `external_confirmed=true`、`unexpected_jobs=[]`、`unresolved_jobs=[]`。文件快照不变，活动租约仍为 1。没有替换证据算法、文件适配器或创建/提交校验。
- 影响：原验收要求额外 job 保持未决；这里无法区分另一个 job 的孤立/冲突/损坏证据与完整受支持证据集，查询会给出错误的完整确认。当前入口只读，没有实际释放租约；该事实不消除确认字段的合同错误，也不能让 b2 沿用此确认。
- 最小纠正：在同一 `files()` 边界从 **requests 和 receipts** 两个明确按 job 命名的目录合并 observed job IDs，任何不在固定 history 的 ID 均列入 `unexpected_jobs`/`unresolved_jobs` 并阻止确认。保持已知 job 的原 FileAdapter 校验，不从允许任意路径/多文件的 artifacts 目录猜测 job。增加合法与损坏孤立回执回归；零 history 的正例应同时没有孤立请求和回执，现有用例不能继续以遗留回执被忽略为通过条件。
- 证据：`.ergora/checks/f3-task-external-status/reviewer/orphan_receipt_probe.py`、`orphan-receipt-command.json`、`orphan-receipt.log`、`orphan-receipt-valid-terminal.json`、`orphan-receipt-invalid-json.json`。两个契约断言均失败，退出 1，12.29 秒（pytest 11.83 秒）；失败是上述产品反例，未记为通过。置信度：99。

## 身份与检查范围

基线：`d98a62a4c9f6d9d514225f033a3f8dad3de3ca60`；分支 `refactor/architecture-foundations`。实际读取 tracked diff、未跟踪新增模块/测试/fixture，独立计算下列 8 个生产/测试文件的 SHA-256，全部匹配 `.ergora/checks/f3-task-external-status/source-identity.json`；登记 aggregate 为 `3559d7de109983d8e1803c4cb92898289b0b4e6ca9cfe80a5c010ab4bf66c8bd`。

- 生产：`src/ergora/cli.py`、`reference.py`、`tasks.py`、`web.py`、`reference_task_reconciliation.py`。
- 测试：`tests/test_architecture_boundaries.py`、`tests/test_task_external_status.py`、`tests/fixtures/task_external_status_client.py`。
- 相邻实际调用链：`reference_task_submission`、`reference_task_creation`、`reference_task_runtime`、`state.State.project/connect`，原 `DevelopmentTransport`、`DevelopmentWorkflow.context/stage`、`FileAdapter`、`agent_platform.core.environment`、初始化/执行器 adapter 选择及原执行协议。
- 文档：`AGENTS.md`、`docs/PLAN.md`、本切片记录、task-reconciliation 与 formal-task-acceptance 记录，以及 USAGE/PROJECTS/AGENT_BACKENDS/架构边界的实际改动。

## 结构、正确性与性能核查

`tasks.external_status` 有 CLI/Web 两个实际生产消费者；`reference.task_external_status` 是专用原生进程接口。新增 `reference_task_reconciliation` 拥有跨 history 与可信文件的完整证据算法，复用 `_Submission.submitted/lookup_run`、原创建合同、实际 SDK converter 与原 `FileAdapter.poll`；其私有方法和进程 `main` 是内聚算法/必需入口，没有为单个消费者额外制造通用层。测试与 fixture 不计作生产复用。

原创建/提交/spec/memo、固定原 run、闭合状态、另一 latest run、连续完整 history、同 ID context 冲突、envelope/fence 一致性、可信终态回执和产物摘要的检查均能对应持久外部输入或实际竞态边界。原 outcome 独立保留，`execution_success` 不由终止证据推断。没有发现通过 result、doctor、fence 发布或 ingress release 绕过只读合同的调用。

父进程只在 `State.project()` 的短连接中读取项目，连接在启动专用进程前关闭，没有跨远程等待的控制 DB 写保留。子进程按 100 条分页流式读取 history，只对 dev_submit 调用实际 converter；保留原 job context 后逐项校验，复杂度随 history、job 数量和实际产物字节增长，没有全 history materialization 或跨请求缓存。每个 artifact 的原有读取上限 16 MiB、每份 receipt 的原协议上限继续适用。文件读和摘要是同步的；总查询仍由父进程超时兜底，不将轻量夹具时间当生产规模吞吐结论。这里是可信不可变文件协议的观察快照，不是原子跨 Temporal/文件系统快照或 OS 进程扫描；未添加写锁或新状态机。

## 验证范围与剩余验收

独立运行仅为上述两项隔离反例，均完整走公开查询/专用解释器/真实文件路径，并保存结果及不变性证据；未运行全量。环境默认 bwrap 在命令开始前失败，按已授权当前容器边界执行。历史源码结果已直接核原日志和命令：首轮 54 passed、1 failed（原公共 Run ID 文本的测试大小写），后续 7 passed；不把首轮失败改写成通过，也不以作者已有测试代替独立结论。

上述初审仅覆盖初始 8 文件身份下的 b1 源码；同一 reviewer 的修正复核见下节。最终非 editable 包、无 SDK 控制环境、精确两 OS CI/远端，以及真实服务/两新模板六阶段和异常重启的相应节点仍需各自实际证据。本报告不继承 F3.4a 的 591 项、包身份或两 OS 结论，不宣布 b1 发行或完整 F3.4b/F3 完成，也不接管 b2 的显式 fence/检查点/租约释放、c/d/e 或页面工作。


## P1 修正的独立源码复审

复审日期：2026-11-03，仍由本 reviewer 对同一切片复核。基线保持 `d98a62a4c9f6d9d514225f033a3f8dad3de3ca60`。独立重算 8 文件摘要，全部匹配 `final-source-identity.json`，aggregate `85fa8b1dcffadb39bddab760deb8110260ad3e0daa646fafa4d764be90440798`；相对初审仅生产 `reference_task_reconciliation.py` 和对应测试变化，另外 6 文件未变。旧 `source-identity.json` 与初审失败证据未覆盖。

修正直接落在原 `files()` 所有者：第 68–77 行对 requests/receipts 两个 job 命名目录取并集，然后继续按固定完整 history 区分额外项；没有按 artifact 名猜测 job、添加其他抽象或引入写入。合法和损坏孤立回执都以同一个未知 ID 保持未决，无需先信任其内容。目录丢失沿原缺失语义处理，错误/不可读目录不会降级为已确认。额外成本为一次 receipts 目录枚举与 job ID 集合去重，符合此查询的必要完整性检查，没有发现不合理性能回退。

独立验证如下：

- 将**原探针逐字节不变**复制到 `reviewer/rereview/orphan_receipt_probe.py` 后运行。两项均通过；合法终态和损坏 JSON 的孤立回执均返回 `external_confirmed=false`、`unexpected_jobs=unresolved_jobs=['orphan-job']`，查询前后文件快照相同、活动租约为 1。原初审的误确认反例已消除。
- 相邻零 history 探针同时移除请求和回执，保留不按 job 名约束的产物文件：有正确 fence 时确认，无 fence 时不确认；两次均保持 jobs/额外/未决为空、文件快照不变、活动租约为 1。单项复验通过，退出 0，8.44 秒（pytest 7.92 秒）。
- 首次组合运行是 2 passed、1 failed（18.16 秒）。第三项产品查询事实正确，失败来自本 reviewer 探针复用原 `lease()` 测试辅助函数后未显式关闭 SQLite connection，探针自己的租约读取产生 shm/wal，污染二次快照；已只修改 reviewer 探针用 `contextlib.closing` 关闭连接后单独复验。初始探针及日志保留，不将这次失败记成产品通过或产品 finding。
- 已直接核作者 `source/orphan-fix-command.json` 和 `source/orphan-fix.log`：10 passed、41 deselected，pytest 52.28 秒，覆盖两模板正常、缺失、额外请求、两类孤立回执和无作业历史。独立结论主要依据原反例复验及源码，不用作者通过替代审查。

复审原始证据在 `.ergora/checks/f3-task-external-status/reviewer/rereview/`：`probes-command.json`、`probes.log`、两份 `orphan-receipt-*.json`、`zero_history_probe-initial.py`、`zero-followup-command.json`、`zero-followup.log`、`zero-history-results.json`。

**P1 关闭；该身份下 b1 源码需求和结构复审通过，无新增 finding。** 首候选 `6a669736…` 的 347 文件/111 项/25 CLI/18 秒并发记录不含本修正，只能作为其本身身份的历史证据；本次不以它验收最终包。最终非 editable 发行、无 SDK 旅程、精确两 OS CI/远端及相应真实服务节点仍由后续独立核对，不在此处提前关闭。


## 最终本地发行与记录的独立核对

本次不重新安装、不重跑完整旅程或任何测试套件，仅直接读取实际脚本、原命令/退出码/日志、保留状态，独立计算内容身份，并作轻量解释器检查。结论：**该最终包的已声明本地验证范围通过，无新增 finding**；CI/实时远端未在此阶段提前验收。

身份核对：

- 生产/测试提交 `a2349e8c3b183918a68935d5199e7c78509364a4` 的 8 文件与已复审 aggregate `85fa8b1dcffadb39bddab760deb8110260ad3e0daa646fafa4d764be90440798` 一致；工作区生产/测试未再变化。当前 HEAD 和本地 origin 跟踪引用亦为该提交，实时远端留待下一阶段读取。
- 独立逐文件重算 **347 个包文件**：源码、最终 wheel、开发安装、基础安装和该提交的 `git archive` 内容全部相同。最终 wheel SHA-256 为 `52d26ddcd998e1cf94bdb274bb6d3aa4ae1cf62a57d28d8b8bbc84849d6d4051`，与登记 package/archive 身份一致。
- 两安装的 `direct_url.json` 均指向此 wheel 的 archive URL，无 editable 标记；实际导入路径均为各自 site-packages。轻量解释器检查确认开发 Python 3.11.15、Temporal SDK 1.34.0；基础 Python 3.12.3 无 FastAPI/Temporal/GEPA，assertions 开启，未设置 PYTHONPATH。
- 冻结清单本身与基线 `d98a62a` 的字节相同，其 **283 个文件摘要** 独立核实全匹配；所有包/安装/归档的相等也包含这些参考文件。本次没有启动参考服务。

验证证据核对：

- 直接核 `final-package-commands.json` 及 final-build/install-dev/install-base/package 原日志：构建、两安装和验证均退出 0，最终包记录为 347 文件/2 安装。没有把首候选 `6a669736…` 的旧 111 项记录当作最终包结果。
- `final-wheel-targeted-command.json` 明确只运行外部证据与架构两文件；原日志为 **59 passed**（51 外部证据 +8 架构），pytest 247.84 秒、总 248.32 秒、退出 0。唯一 warning 为既有 Starlette/httpx 弃用提示。已检查测试/fixture 内容及新 P1 回归，确认使用 SDK protobuf/converter/分页及真实证据文件；没有依据此结果宣称最终包的全量回归完成。
- `base-journey-final.json` 与原 `.log` 完全相同；按脚本循环和 commands 列表重算 **27 次 CLI**：23 次退出 0、4 次预期退出 2，8 次直接入口、19 次受控 fixture 入口。`cli()` 在记录命令前检查实际 returncode，最终记录仅在所有断言完成后写入；总命令退出 0（54.48 秒）。两模板分别覆盖注册/预览/创建、缺运行时、单次提交、无 fence/无回执、可信终态、缺原 envelope、孤立回执与根漂移；治理模板额外一轮并发查询。
- 保留文件独立核查：两模板均仍保存原 `CANCEL_UNCONFIRMED` outcome、3 个请求/3 个回执/3 个产物及原 fence；租约以只读 immutable SQLite 连接核查，活动数均为 1，claim 的 `released_at` 和 `evidence_digest` 均为 null。脚本每轮查询前后对原 execution 目录的任务/journal/请求/回执/产物/fence 做摘要比较，仅排除 fixture RPC telemetry；三次完整确认还逐次断言原 outcome 相等及不释放标记。
- 实际保留的 RPC telemetry 与 27 次命令吻合：治理 8 次外部查询对应 16 次连接、24 页 history、40 次 codec decode、8 次原 result；大型 7 次对应 14/21/35/7。doctor/start 均各 1 次，只在受控提交路径，外部查询未额外触发。`seed-evidence.py` 直接调用原 FileAdapter submit/fence/verify_receipt/publish；查询 fixture 替换 RPC 边界，未替换生产文件校验。提交 fixture 的 doctor 可用性是受控夹具，不构成真实环境准入/模型验收。
- 并发脚本在首个受控连接开始后执行其他项目真实 SQLite 写入，断言写完时查询 future 仍未完成；记录 **22.78 ms** 写者、**19213.23 ms** 总查询，与两次各 9 秒延迟的 fixture 控制一致。保留控制 DB 中 other-project 的 revision 已为 2、memory binding 为 sqlite。三次查询中位治理 1194.47 ms、大型 1148.55 ms，只代表这两个隔离夹具的 CLI/专用解释器/SDK 查询成本，不外推为模型或 OS 进程性能。

本 reviewer 的直接身份与保留状态核查写入 `.ergora/checks/f3-task-external-status/reviewer/final-local-identity.json`、`final-local-journey-records.json`，17 个已读发行证据的精确摘要在 `final-local-evidence-identity.json`。原始首候选、初审失败、修正复审与最终记录继续分开保留。

本地结论不覆盖真实 Temporal 服务、真实工作流/模型、两新模板六阶段、OS 进程已停或 b2 的 fence 发布/检查点/租约释放。本地核对阶段的 CI/实时远端在当时待验，后续终结核对见下节；此处不以本地结果单独宣称完整 F3 完成。


## 精确 CI 与实时远端的独立终结核对

核对时间：2026-11-03 08:00:40 UTC。独立读取 `ci/` 中保存的官方 actions/run/job 原 HTML、选定 run JSON、来源摘要与获取/验证脚本；没有执行作者的会覆盖状态文件的 verify-ci.py，而以 reviewer 自有只读解析器重建结论。解析器退出 0（1.78 秒）；没有重跑测试、构建、安装、旅程或 CI，也没有外部写入。

- 从 `ci-actions.html` 的原嵌入 JSON 递归选择 run `41597961138`，对象与 `ci-html-run-selection.json` 完全相同。workflow 路径为 `.github/workflows/portability.yml`，分支 `refactor/architecture-foundations`，description 链接绑定完整提交 `a2349e8c3b183918a68935d5199e7c78509364a4`，状态 completed/success。run 原页面同一提交链接和可见 Status=Success 均匹配。
- Windows job [125789665133](https://github.com/626619403/Ergora/actions/runs/41597961138/job/125789665133)，`native (windows-latest, 3.12)`：Build and install wheel、Packaged reference identity、Native application regression、Windows PowerShell 5.1 installer and upgrade **四项均 success**。
- Ubuntu job [125789665389](https://github.com/626619403/Ergora/actions/runs/41597961138/job/125789665389)，`native (ubuntu-latest, 3.11)`：Build and install wheel、Packaged reference identity、Native application regression **三项均 success**。Windows 专属安装步骤为预期 skipped。
- 两 job 页面自身的 selectedJobId、summaryHref、当前视图标记与 run/job 对应；每个必需 check-step 的完成属性、开始/完成时间和 `.../commit/完整SHA/checks/JOB/logs/STEP` URL 均核实。两 job 的 Complete job 均 success，没有 failure/cancelled/timed_out 步骤。`ci-html-status.json` 的四份登记来源 bytes/SHA-256 全部与原文件匹配，独立导出结果与其 jobs/required_steps 一致。
- 读取该提交实际 workflow：矩阵确为 Windows 3.12/Ubuntu 3.11；在非 editable wheel 安装后执行包内参考身份及整个 tests 目录/参考合同用例，Linux 另有 portable/adapter/runtime 用例，Windows 另执行 PowerShell 5.1 安装升级。以上结论基于必需步骤的官方终态和实际 workflow 合同；没有从页面推算未获取的逐测试数量，也不把真实六阶段或服务验收附加到 CI。
- 独立执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，origin URL 为 `https://github.com/626619403/Ergora.git`，实际返回完整生产/测试 SHA `a2349e8c3b183918a68935d5199e7c78509364a4`，与 HEAD、精确 CI 候选和已验归档一致。
- 重算确认 8 文件 aggregate `85fa8b…` 与 wheel SHA `52d26ddc…` 保持；此前 `final-local-evidence-identity.json` 固定的 **17 份本地验收证据逐份摘要均未变**。因此已核 347 文件身份/两安装/提交归档、冻结 283、最终 59 项、27 CLI、原 outcome/文件/活动租约保持及并发结论继续对应这次 CI 候选，没有借用首候选旧 111 项。

CI 原始记录位于 `.ergora/checks/f3-task-external-status/ci/`；本 reviewer 的精确输入摘要、每个步骤日志 URL/完成时间、实时远端输出和独立结论位于 `reviewer/final-ci-remote-review.json`，脚本/命令/日志为同前缀 `.py`、`-command.json`、`.log`。读取器先后遇到 GitHub summary job 链接带 fragment、job 页没有独立 commit 超链接的格式差异；已按实际 selectedJobId 与完整 commit 日志 URL 校验，原 `-initial`/`-fragment` 读取失败保留。这些是 reviewer 解析器假设修正，不是产品或 CI 失败。

**b1 的独立验收已完成，无剩余阻塞项。** 待实施者将公开手册、计划和审查记录作仅文档的提交/推送并核对；该记录整理不改变生产/测试身份。b2 的显式 fence/检查点/租约释放、c/d/e 的新两模板真实正常/异常/重启旅程、正式任务页面及完整 F3 仍未完成。本报告没有验收真实 Temporal/model 执行、OS 进程终止，也不将后续测试成本 V1 切片纳入此身份。
