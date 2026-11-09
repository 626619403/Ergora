# AC4.3c.2–5 专长执行者正式纵切片独立审查

本报告保留本片初始源码审查、WA-S1 修复复核及 R2 最终本地验收。审查者 `/root/work_agent_runtime_review` 从新的上下文读取原始要求、已审合同及实际差异，并按 AIHERO 索引应用 `code-review`、`codebase-design` 和 `maintainable-project-delivery` 的 independent-review 要求。两个轴分别交给新的无历史上下文审查者，未委派实现；同片修复与最终证据由原审查者继续复核。

**当前状态：R2 最终本地 Spec / Standards 验收通过；WA-S1 已关闭，WA-CI1 的测试修正也已通过同片本地复核，精确交付仍待。** 原 `8a856f54c0e0d16b762f5c62ca1b170eca2ddd9f` 的对象身份已核，自己的 Windows 必要回归失败，Ubuntu 回归在最近采样时仍在途。修正候选须取得自己的必要 CI 与明确 HTTPS 远端 SHA，不能借局部重验覆盖原失败。原全组的一个 90 秒超时失败及原样单项重验另外保留；不称原全组全绿。下方按初审、修复、本地验收和精确候选复核分别记载证据。

## 固定范围与证据身份

- 基线和 HEAD 均为 `11a00061c0573f3d24e0402671d02acc1d1e9107`，分支 `refactor/architecture-foundations`，没有本片提交。`base...HEAD` 的空结果没有作为审查范围。
- 完整范围为 19 个 tracked 改动和 7 个 new 文件，逐文件名单及完整新增正文见私有 `runtime/initial-review-scope.json` 和 `.diff`。SHA256 分别为 `e3ac6dc1eb35ae4b44ef22604e12a569154aaed7e03a394cd5347a8c101a5693`、`94bcea6a3517d22d4409cc493410e70a1cf10fa028e873755f05daa8a9364394`，独立核验一致。
- 生产范围包含 `agent_backends / agent_runs / agents / reference_executor / reference_inputs / reference_task_creation / reference_workflows / review_dags / stage_driver / task_envelopes / tasks` 和 task-definition-v2 schema；同时覆盖全部文档、两个新增组合、validation implementer、原有两份夹具及新增工作旅程夹具/测试，未漏 untracked 文件。
- 初次逐文件 SHA 核验全部匹配。审查末期只有 `docs/PLAN.md` 和本片 runtime 交付记录追加实际进展，生产源码、夹具、测试及示例仍与初始范围一致。两个文档当时 SHA 为 `747f9e8cb84c6c6139c060a2934d2936d368ee597713643b5be42487b38a35bc`、`3c6856d73c1072619c53c92e6ba93ae14247ea974c846b14aa1a015a7b472098`；后续追加记录不冒称初始快照。完整终核存私有 `independent/source-identity.json`。
- 要求来源为原 `runtime/raw-requirements.md` 和[已审 C1 合同](../plans/2026-11-09-work-agent-contract.md)。标准来源为 `AGENTS.md`、`docs/PLAN.md` 及 current/reference-boundary/contracts-and-identities 三份架构文档；没有找到额外 CONTRIBUTING/CODING_STANDARDS。

## Spec

**未通过：1 项阻塞 finding，WA-S1。** 其余已审实现覆盖显式 v5 路由、一对一原 unit 分配、静态图传递顺序、完整祖先材料、全部实际 writer 的后端多样性、原工作来源到 review、祖先容量和取消竞争。旧公开只读入口继续拒绝 workspace/write/shell/network 请求；原 units、checkout、monitor、ledger 和 integrate/verify 所有者保留。待验收事项不计作源码 finding。

### WA-S1（P1，阻塞）：首次 HEAD gate 前崩溃后，恢复可接受 writer 自己的提交

位置：[reference_executor.py:393](../../src/ergora/reference_executor.py#L393)、[恢复祖先判断:410](../../src/ergora/reference_executor.py#L410)、[HEAD gate:609](../../src/ergora/reference_executor.py#L609)。

合同要求：“候选 Git 操作、确定性检查和 commit 仍由可信 Executor 执行”，并要求“完成或允许恢复的原调用不能……重跑写副作用”；没有可靠结果的窗口须保留人工对账。这两个义务须同时保持。

可达窗口为：writer 自行 commit，原 monitor 已成功保存终态，Executor 在第一次 `HEAD == self.candidate` 检查前崩溃。恢复时原 `prepare()` 已把 `self.candidate` 设成 checkout 当前 HEAD；saved-call 分支只核原起点为当前 HEAD 的祖先，随后 model 的 HEAD gate 比较两个当前值，便失去首次调用的起点。受控重放实际执行生产 `_composition_request()` 和 `model()`，原本被正常负例拒绝的调用成功返回并发布内存中的 agent-selection/change-summary。

原 r6 commit 负例提供直接事实：formal-call 起点 `27dcfd800352522efa763ffbcb27ba5d93013eee`，实际 HEAD `35fe54dac16e76dcbb70391c01707a65beae4395`，原 selected monitor 返回 0，起点到 HEAD 的祖先检查返回 0，**可信 post-gate agent-selection 不存在**；原负例的 FAILED 原因正是 “Work Agent changed HEAD; only the trusted Executor may commit”。只读事实存私有 `independent/recovery-window-static.json`，可执行脚本/输出为 `independent/replay-wa-s1.py` / `.log`。主审用 `.venv-dev/bin/python -B` 独立重跑该脚本，exit 0，结果为 `production_model_replay: accepted`、`native_calls_started: 0`；脚本/输出 SHA256 为 `ac9fe7f176839fbbd13644d32494e0100ff23a8f665bbfd5ab0c6d970be4ac95` / `b006d8da055ec7ff8d0a0f0afb79b64217907a63847531de307b6550405b5fe1`。重放不启动 CLI、模型或服务；对象在内存重建，monitor 返回原终态，artifact 仅存内存、write 仅比较原 request，未修改原失败原件。这是生产方法的受控重放，完整崩溃进程回归由修复方另做。

后果是恢复会承认未经可信 Executor 提交的候选；原 unit 路径 gate 只检查未提交改动，不能替代丢失的 HEAD 检查。最终整体 task scope 也不能证明每个 unit 的写范围和 commit 所有权。

最小修正方向：HEAD 偏离 formal-call 起点时，要求原可信所有者已持久保存的、完整且匹配原调用和原模型结果的 post-gate 证据。已有 `agent-selection` 在 HEAD gate 后、原可信 checks/commit 前发布，可复用其 role/binding/project revision/prompt/template/result SHA，并对照原结果字节；缺失、不完整或不符时停止并保留人工对账，不重发 writer。只检查文件存在或 Git 祖先不足。也不能无条件改成 HEAD 必须等于起点，因为那会破坏可信 Executor commit 后、receipt 发布前的合法恢复。补交叉窗口负例，并保留合法原调用恢复和调用计数不增的正例。

## Standards

**通过：明确规则违例 0，阻塞 finding 0。** 此轴只评价结构和工程标准，不抵消上方 Spec finding。

后端差异仍归 `AgentBackend` 的共有 Interface，调度器没有按厂商分派。纯数据图投影有 `tasks`、`task_envelopes` 等真实消费者；资源、准入、调用、work 来源、框架 hook 和恢复材料留在现有所有者。没有第二调度器、持久 running 表或账本，也没有新增依赖或 CI 作业。新增断言分别保护外部选择、冻结持久状态、原 receipt/claim/产物、候选祖先和取消竞争，未发现应删除的重复防御或只镜像实现的测试。

两项非阻塞观察不计 finding：`ReviewDAG(StageDAG)` 的空兼容子类可以改成旧名别名，但当前没有额外运行状态或类型分派；工作依赖原件在 dependency/port 表和后继审计正文中重复，会增加输入成本。原 r6 材料实际为首 writer 14,271 B、次 writer 170,100 B、review 约 442,700 B，仍完整且受明确预算控制。去重是可后续评估的性能机会；目前没有材料丢失、无界执行或时间回归证据，不能把合法的超预算拒绝改写为性能缺陷。

## 实际核查与限制

- 独立重新执行不含六个原生进程场景的本片检查：`PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -B -m pytest -q -p no:cacheprovider tests/test_work_agents.py -k 'not formal_work_reuses_original_checks_commits_and_sources' --basetemp=…/independent/pure-tests`，**13 passed / 6 deselected / 27.11 秒**，日志在私有 `independent/pure-tests.log`。
- 独立读取作者 r6 原件：**19 passed / 143.04 秒**；日志 SHA256 为 `76ff7bc03ff52c9acaffed3ab61d05bb1fbc38d85861bab74c0d98999da86389`。其范围为确定性原生 CLI 协议、真实进程/MCP/原 checks/commit、来源篡改、正常 HEAD 拒绝、合法提交后恢复、调度与取消竞争；它没有覆盖 WA-S1 的交叉窗口，也不是模型质量证明。旧 83 项、合同 11 项、scope/取消 2 项各保留原日志，不把 r4/r5 失败覆盖成通过。
- Standards 审查者只读 AST 解析 15 份改动 Python 文件通过。独立 `git diff --check` 通过；冻结 reference 树的 tracked diff 为空，未修改 283 冻结文件。
- 未运行模型、服务、安装、Git 发布或新 CI。父代理后续 R1 包、既有历史重放和真实旅程的进行中状态不纳入本次已核通过证据；最终非 editable 包、真实模型/自身模板、完整 CLI/Supervisor/Temporal/evidence/handoff、旧 history 及精确候选 CI/远端身份须按各自候选取得并复核。

私有双轴报告为 `runtime/independent/spec-axis.md`、`standards-axis.md`。同片后续修复须补对应回归并由本审查者复核；**WA-S1 未关闭前，不可将本片标记完成或据本初审发布。**

初审计数：Spec 1（最严重 WA-S1）；Standards 0。验收 pending 与源码 finding 分开记录。

## R2 同片修复复核：WA-S1 关闭

本次由原独立主审和原 Spec 轴审查者复核同一切片，没有继承作者的通过结论。固定基线和 HEAD 仍为 `11a00061c0573f3d24e0402671d02acc1d1e9107`；R2 完整 27 文件 tracked/new 范围见私有 `runtime/r2/review-scope.json` / `.diff`，SHA256 为 `8eea33f6cfd5381951cc1b92453252a9743283a821e4e39ceb45b41ecb0b9b04` / `44528120c1ba76b3860a4491e66d6f833cc4572cefe9367918859f7b824ef9dc`，均已独立核验。相对初审，生产改动只有 `reference_executor.py` 的 11 行恢复检查，另有原工作旅程夹具和本片测试增量；其余为本报告与进度记录。固定生产文件 SHA 为 `a01c7ec460adfe3cf127d580e1cb684c2f53d62d8983d6b3763af7114c8e9789`；夹具/测试 SHA 分别为 `65e03c3abec49526269e6fc9f01b328b8613c95933a50ab8806f4f769c252ea9` / `6ba78644f67ba0b70dfb7cc70ea2b28538fbeae55c3f774b653ea9848d0cd7ad`。本报告及 PLAN/runtime 记录继续记账的字节与该快照分开，私有 `independent/r2-source-identity.json` 记录本次差异和漂移。

修复位于 `src/ergora/reference_executor.py:412–422`：恢复 HEAD 偏离 formal-call 起点时，必须从原 `STATE/artifacts/<task>/<job>/agent-selection.json` 读取完整 post-gate 内容，逐项核 role、实际 binding、冻结 project revision、原 prompt/template 摘要和原结果字节 SHA。少字段、多字段或不符均不能作为证明。该原产物确在首次 HEAD gate 后、可信 Executor checks/commit 前发布，故能区分本次漏洞窗口与合法提交后恢复；没有新增 marker、账本、调度器或写调用。原 formal-call、monitor、invocation、MCP、claim 和来源核验仍执行。

本次实际核查：

- 已读原 R1 安装包 `wa-s1-original.log` 的 **2 failed / 31.93 秒**，和作者另跑原独立重放的 `wa-s1-independent-r1.log`。无 proof 的旧恢复实际变成 SUCCEEDED；篡改 proof 的旧例在更晚的 immutable agent-selection 冲突处失败，不能说两个旧例都成功推进。两例均未满足正确的恢复拒绝边界。
- 已逐行核查真实 monitor 返回成功后、首次 HEAD gate 前注入 `BaseException` 的新夹具。`wa-s1-fixed.log` 为 **3 passed / 18 deselected / 64.18 秒**：缺 proof、篡改 proof 在 post-gate 恢复门禁拒绝且原 run 数不增；合法可信 commit 后仍恢复同原调用、复用同原 receipt。该日志 SHA256 为 `b36c625bf698af9ca178fb4e8cd1b7b0467d9e088ad232b4a1dc0bb63a81cba6`。
- 主审对原 r6 commit 负例重跑相同独立脚本；R2 现于 line 417 抛出“lacks original post-gate evidence; reconcile before recovery”，未再次调用模型。输出为私有 `independent/r2-replay-rejection.log`。
- 主审以合法恢复原件执行实际生产 saved-call 分支的 **10 项内存矩阵**：完整 proof 接受；六个字段分别篡改、少字段、多字段以及原 result 字节变化全部拒绝。恢复正常 proof 后，实际生产 `model()` 合法恢复重放成功。脚本/输出为 `independent/r2-proof-matrix.py` / `.log`，SHA256 为 `db9933e17e3838eec59eac3589ac1556db7b89ee21907a8193e1aeabb0094ee1` / `979f387856e2606ab8b709c34536f2055a18e94f7d6d8c2437c0a4965ca5b27b`。全程原件只读，publication/monitor 在内存替换，**零新 native 调用**；它补充原生故障回归，不冒称完整服务崩溃旅程。
- 原 Spec 轴另对 R1/R2 实际方法作同原件对照：合法可信 commit 两者均接受；缺 proof 及 result SHA 不符从旧恢复验证路径接受变为新门禁拒绝。其复核追加在私有 `independent/spec-axis.md`。

**Spec：本修复通过，WA-S1 关闭，未发现新的源码阻塞。Standards：本增量通过，剩余明确违例/阻塞 0。** 校验属于原持久恢复所有者，直接复用已存在的 post-gate 原件；新增两个负例保护不同的缺失/篡改路径，与原合法恢复正例互补，没有为修复引入第二套状态或冗余框架。

缺少可靠 post-gate 原件的 HEAD 已推进窗口继续明确拒绝并要求对账，这是必要的失败关闭；本结论不声称覆盖任意模型/进程崩溃窗口。R2 自身非 editable 安装包和依赖身份、完整回归、新旧 history、实际 CLI/Supervisor/Temporal/evidence/handoff、真实模型/自身模板与精确 CI/远端交付均继续单列，R1 的结果不能替代新候选。

截至此复核：Spec 历史 finding 1、已关闭 1、开放 0；Standards finding 0。完整交付状态仍为待验收。

## R2 最终本地验收：Spec / Standards 通过

**本次最终本地结论：Spec 通过，Standards 通过；WA-S1 保持关闭，新增 finding 0、剩余本地阻塞 0。** 本节补齐上文当时待验的 R2 安装包、回归、历史、正式服务旅程、一个真实 writer 和自身真实审查模板。主审及原两轴审查者分别核原件，没有用作者或模型的 approve 替代独立结论。本轮只读检查与报告写入没有重新启动服务、模型或原生写调用，也未安装、提交或推送。

### 最终范围与包身份

基线和 HEAD 仍为 `11a00061c0573f3d24e0402671d02acc1d1e9107`。最终 tracked/new **38 文件**范围为私有 `runtime/r2/acceptance-review-scope.json` / `.diff`，独立核验 SHA256 为 `b7861b8a19bdbe2430d92f9d86fa756253bfc924dbc708565fc6a824e2cfce78` / `4ddfa593aa82c030d16084d50df1ad3c0995f3dba8f43a35b29e7197880d1390`。生产源码、测试、夹具及示例仍与 WA-S1 关闭版本一致；相对前一快照新增范围为手册说明及七份公开证据，不是新的实现修订。

主审重新逐字比较 source、wheel 和独立非 editable 安装目录：**372 文件全部一致**；另从基线 Git archive 核 **283 冻结文件全部一致**。wheel SHA256 为 `6fe8a5a663ef82fb9468e5d3eb24c6cb0f82a4f011e6f6e8c96743b5a13c1bdf`，排序内容清单摘要为 `f990f22953b010ef4b633ddec80fa01f00b14908340dea2c65804f886d17f2a7`。没有生产依赖或 CI 作业改动；环境身份见[包证据](evidence/2026-11-09-ac4-work-package-r2.json)。私有独立结果为 `independent/final-package-check.json`。

审查期间 runtime 交付记录从快照 SHA `f4503f6c185132a985916eb3c61d39a3772bd02276f7c950e3803f974ab5fd1e` 变为 `95aaa4647235d10db1acf7dd3e72d8550bdd5f0f7c4c86b7b98641decd8d0b12`：实际增量仅静态链接数、精确成功服务脚本路径及原 timeout 观察限制，已逐字复核。本报告此后追加本节并更新状态；这些记账字节不冒称固定快照原字节。其余 37 文件在追加前匹配，完整结果为 `independent/final-scope-identity.json`。

### Spec：原件与行为

| 已核事项 | 事实与边界 |
|---|---|
| 安装包回归 | 原 `packaged-tests.log` 为 **1 failed /291 passed /6 skipped /1466.25 秒**。唯一失败是既有 `test_existing_six_stage_contract_consumes_selectable_agent_evidence[command-repository-governance]` 触及原 90 秒子进程超时；同包、同源码、原测试和超时不变的 `timeout-rerun.log` 为 **1 passed /9.52 秒**。两个记录合计覆盖 292 个通过用例，原全组仍为失败。六个 skip 属未配置外部 Forge/mini 集成，不计模型或 GPU 成功。I/O 停顿不是已证明根因。 |
| 历史兼容 | R2 安装包实际重放 **13 份原 v1–v4 history** 和四份新 v5 history。Spec 轴核原历史字节摘要、事件数量、workflow type、启动 input、queue、run/memo 及重放原日志；没有以新历史替换旧历史，也未再次重跑。[旧历史证据](evidence/2026-11-09-ac4-work-legacy-replay-r2.json)。 |
| 四正式服务任务 | **374.270961943 秒**的实际公开 CLI/Supervisor/Temporal 旅程，共 **24 原 stage request、24 receipt、24 原 claim/session/state、12 Agent 行及 155 份回执产物原始 SHA**，均独立核验。四个离线 handoff 的 packet/manifest/index 与 **145 个唯一 blob** 相符。[旅程证据](evidence/2026-11-09-ac4-work-journey-r2.json)。 |
| 完整调用材料与所有权 | 12 份所选 prompt 与原 native stdin 相等，原材料 JSON 与冻结图 resources 一致；336 项 manifest 文件比较、20 份 dependency 和 8 份 port 来源表均等于完整原产物。四份可信 work commit 的差异只含各自 unit 路径、原检查保留，且为 integrate/verify 候选祖先；两组各三 reviewer 的实际运行区间确有交叠，且使用非作者 session。没有把它称为速度提升。 |
| 停机、取消与清理 | worker 单独停止期间原 Executor 完成首 writer，重启后才发后继；前三份 request 字节保持由原脚本前后摘要断言记录，原调用和 Executor/A2A/Temporal PID 身份保持，没有重复 Agent 行。取消 signal/intent/fence/reconcile/lease 与原结果一致。服务旅程采样 **137 个原 PID/starttime**，结尾原进程无存活且端口关闭；这是采样范围，不能推及未观察的短命进程。原超时另仅核到一个保存的 monitor PID/starttime 已退出、monitor rc0，不借服务样本扩大其清理结论。 |

四任务各自结果保持，正常运行与停机恢复是同一任务的两个阶段：

- `work-resumed-v5-public`：`REVIEW_READY`，9 jobs /5 Agent 调用，两个 writer 后由可信 integrate/verify 接三个 reviewer。
- `work-scope-v5-public`：`BLOCKED`，3 jobs，首 writer 路径拒绝且无后继。
- `work-required-v5-public`：`BLOCKED`，9 jobs，required correctness reviewer 失败，其他意见仍完整保留。
- `work-cancelled-v5-public`：保留 `CANCEL_UNCONFIRMED`，3 jobs，首 writer `CANCELLED` 且无后继；显式 reconcile 释放原 lease，不修改原结局。

精确成功脚本是 `runtime/r2/service-retry/journey.py`，SHA256 `c93e34b6c135b60cd56b56fed0cf4b6bb4ef28e03c880742153a901b1cce10e8`。根 `r2/journey.py` 是夹具 marker 越 unit 范围的保留失败首试，不能与成功副本互换。六份 writer MCP scope 全部核过；五个已完成 writer 有原 native handshake/audit，取消的 fixture 在 native handshake 前被杀，不能称六次 native MCP 全部完成。这些服务调用使用确定性原生协议，证明生命周期与合同，不证明模型质量。

另一个 **76.000459968 秒**旅程实际使用一个 Codex formal workspace writer。主审通过 R2 安装包只读 `inspect_input/inspect_manifest`，核 **9 receipt、9 原 claim、60 份 raw artifact SHA、5 次原 call/input/material/manifest/run/result、9 个独立 stage session**；两个工作 commit 均为最终 `49b852c6be547577243ee083faef3af7fce419c5` 的祖先。完整首 writer 产物进入第二 writer，后者完整产物进入三个最终候选 reviewer，原 plan/verification 仍在。真实首 writer job 为 `task-1-5ab9a1f44e56770c58a41bdd`；原 CLI 路径和 `agent_message / command_execution / file_change` 事件与实际 `src/new.py` 内容相符。原 MCP 证明握手和 `list/read` 工具就绪，不证明 writer 主动读取了每个固定资源。第二 writer 与三个 review 明确是确定性夹具。[真实 writer 证据](evidence/2026-11-09-ac4-work-real-writer-r2.json)。

### 自身真实模板与 Standards

本候选用 R2 安装包的实际 `structure-review` 模板运行，用户已授权 Claude 不可用时的 Codex 回退，实际为 `gpt-6.1-sol / high`，**258.906392136 秒**，run `d4de65fb9ee447fdb344e7fc48aec3ec`，结果 `approve`。独立核原 input/manifest/prompt/result 与 39 份源身份；原定义库移除后，已保存输入仍可完整核验。原 native stream 的成功 MCP 读取连续 **18 页 /642,870 字节至 `next_offset=null`**，与原附件字节完全相同；一次错误 URI 读取保留，未算作成功页。[输入身份](evidence/2026-11-09-ac4-work-self-review-r2-identity.json)、[原意见](evidence/2026-11-09-ac4-work-self-review-r2-result.json)、[完整读取审计](evidence/2026-11-09-ac4-work-self-review-read-audit.json)。该模型没有执行所供测试；它的意见不替代独立审查、owner approval 或不同后端的错误独立性。

主审的原件核验脚本为私有 `independent/final-originals-audit.py`，SHA256 `3df983d76b9b651afa443fbb86e546bbd5fac40735fef1b88053624a9a637880`；成功输出 `final-originals-audit.json` / `final-originals-audit-final.log` 同 SHA256 `0dd8c82ce93b2d546d1a5934be52bafe3a46f65e9c68e70de74cb5270d4009b9`。原件只读，无新 native 调用。

两轴最终私有报告为 `independent/spec-axis.md` / `standards-axis.md`，SHA256 分别为 `ae38650db4a709ab26c7221384da815d8ed6bf3c08381599dfaf9340dc05bae9` / `99401b26dc30d12fe210b7377bf2784a93565baf68e056928caadb99552b4c49`；均已完成同片最终本地结论。

Standards 轴复核当前架构图、协议版本和恢复说明、示例依赖导入顺序、进度状态与七份公开 JSON。公开证据的完整键/值未见个人绝对路径或凭据值，机器位置以 `<repository>` 表示，原 run/job/内容身份保留；重新排版后的公开结果使用 canonical 身份，不冒称原文件字节。原 Temporal、monitor、ledger、Executor checks/commit、六阶段和旧公开只读入口继续各归原所有者；没有第二调度/账本、新生产依赖或 CI 作业。既有两项非阻塞结构/材料增长观察保持，不因没有比较基线便制造性能 finding，也不要求删除保护不同合同的回归。

本次状态追加前的低成本检查为 **12 Markdown /276 本地链接和锚点、88 条文档命令 parser、15 Python AST 全通过**，`git diff --check` 通过。它们不充作应用或外部集成运行结果。实际时长只代表这些运行，没有加速或多模型质量结论。

**最终本地计数：Spec 历史 finding 1、已关闭 1、开放 0；Standards finding 0；本地验收阻塞 0。** 剩余精确交付门禁为本片普通提交、该提交自己的必要 CI 与明确 HTTPS 远端同 SHA；这些尚未发生，本报告不提前登记通过。后续三个领域模板、AC5 页面和 AC6 新用户旅程仍按后片范围推进。

## 精确候选 8a856f5：对象通过，必要 CI 失败

本节由原独立主审继续同片交付核验，不将下一片 AC4.4 的当前工作树混入本片。精确候选为 `8a856f54c0e0d16b762f5c62ca1b170eca2ddd9f`，父对象为原基线 `11a00061c0573f3d24e0402671d02acc1d1e9107`。`git diff-tree` 的 **38 文件**名单与已审 acceptance38 和作者 commit 记录完全相同；34 文件直接匹配原 scope SHA，另外四文件仅为 PLAN、AC-plan、runtime 和本报告的已核本地状态增量。本报告提交内字节精确为已核 `d4c3b76ed31b2695d0dbc7abb0a7d603cd677d6a675a1dd287bd0990efa1e9e4`。从固定 diff 重建原文、逐字核其余状态增量，没有新增生产行为。

以私有保留原件 `runtime/r2/dist/ergora-0.2.0-py3-none-any.whl`（原 SHA `6fe8a5a663ef82fb9468e5d3eb24c6cb0f82a4f011e6f6e8c96743b5a13c1bdf`）独立比对该候选 Git 对象和原 R2 安装目录：**372 文件逐字一致**、清单摘要仍为 `f990f22953b010ef4b633ddec80fa01f00b14908340dea2c65804f886d17f2a7`；283 冻结树相对基线无差异。保留原包与根目录当前 `dist` 分开，未把后者当原 R2 证据。Portability workflow 与基线逐字相同，SHA `81c168fdb140f44ccfdca497003e452355c9164a6ed6f8dfb8fa31729a1943ca`。原件核验结果为 `independent/commit-object-audit.json`，SHA `4d2fb1533efa88c1cca98b69756affc0d5fa15e352a75ac5807257680ff9ded8`。只从该 Git 树核 **12 Markdown /284 本地链接及锚点，0 失效**，结果 `independent/commit-doc-links.json`；未使用下一片当前源码。

### WA-CI1（P1，交付阻塞）：新增第三份专家示例未同步既有库存断言

位置：[test_agent_definitions.py:39](../../tests/test_agent_definitions.py#L39) 与 [validation-implementer 定义](../../examples/agents/validation-implementer/agent.json)。原测试遍历 `examples/agents` 的全部目录，却在第 40 行要求导入数量和不同 digest 数都恰为 2。本候选真实目录已有 `architecture-reviewer`、`kernel-implementer`、`validation-implementer` 三份合法示例；因此原测试到达 `assert (3 == 2)`。这是既有测试的目录库存假设没有随新增示例更新，不是已证实的 workspace 执行生产缺陷。

独立于作者再次读取官方 [Portability run 42599729729](https://github.com/626619403/Ergora/actions/runs/42599729729) 及两个 job 页面，核候选完整 SHA、workflow、所选 job ID 和各步骤的精确 commit/check/log URL。**2026-11-09 10:28:32.377196 UTC** 的原页采样为：

| job | 必要步骤原结论 |
|---|---|
| Ubuntu 3.11，`129100927761` | Build and install wheel、Packaged reference identity 成功；Native application regression 在途、无终态。 |
| Windows 3.12，`129100928088` | Build and install wheel、Packaged reference identity、Windows PowerShell 5.1 installer and upgrade 成功；**Native application regression 失败**。 |

全 run 在该时刻仍为 `In progress`，但 Windows 已完成的必要失败已阻止门禁通过。官方 annotation 的完整 test ID 为 `tests/test_agent_definitions.py::test_complementary_examples_material_and_filtering_share_backend_without_sharing_identity`；原末行为 **1 failed /749 passed /572 skipped /16 subtests passed /439.33 秒**。这不是上文原本地 90 秒 timeout 的重现，也不能把两次失败合成同一原因。官方 Windows 原页 SHA 为 `e8908ca714d6cd0d70a0972bb14cdda3fec54607404a7abe985671df21c4b7f7`；采样摘要与原页保留在 `independent/exact-ci-observation-02/`，摘要 SHA `f0334c558c074159fcc2eaac8c38c1734a9ecf39c7d9b6b2444e7b6d8334b6b1`，可见失败原文另存 `independent/exact-ci-windows-failure-visible.json`。

最小处置在原测试：明确其原语义针对的互补实例集合，并按实际集合核彼此不同的 digest，继续保留原后端、筛选和完整资源检查；不需要改生产调度/权限、放宽资源校验或增加 CI 作业。保留 `8a856f5` 的原失败，修复须普通提交，并核修复候选自己的必要 CI；不能以另一片后续 CI 或一次局部通过替代原失败身份。主审没有修改测试或实现、取消原 CI、启动重跑或读写下一片状态。

**本次精确交付结论：对象/包/文档身份通过；WA-CI1 开放，必要 CI 门禁未通过，明确 HTTPS 远端 SHA 的最终门禁尚未执行。** 最近采样的 Ubuntu 终态仍未知，不能推为成功或失败。此前本地验收及 WA-S1 关闭保留为各自范围的历史事实；当前 Spec 历史 finding 2、已关闭 1、开放 1，Standards finding 0。本次返回等待原 CI 终态与作者处置，不持续轮询或提前登记精确交付完成。

### WA-CI1 同片测试修正复核：本地关闭，精确交付待新候选

已直接读取作者用保留 R2 非 editable 包执行的原例和修后整文件日志：`runtime/r2/ci-example-original.log` 为 **1 failed /0.54 秒**，同一 `3 == 2`；`ci-example-fixed.log` 为 **54 passed /1 skipped /15.74 秒**。skip 是 Linux 不能执行的真实 Windows junction 用例，不计 Windows 成功。这些结果与官方 Windows 的原失败分别保留，主审没有重新运行测试或服务。

实际修正仅在原 `tests/test_agent_definitions.py:39–42`：显式选择 `architecture-reviewer` 与 `kernel-implementer` 这对原测试要比较的互补同后端实例，按 `len(sources)` 检查 digest 彼此不同；原 schema、共同后端、职能/专长过滤及完整资源文本检查均保留。该测试的用途不是要求整个示例目录永远只有两个实例或一种后端；将比较对象显式化比把全目录常量改成 3 更符合原语义。新增 validation 示例的正式 v5 映射、输入材料和实际工作路径已在本片原工作旅程覆盖，无须为该修正增加生产校验、重复测试层或 CI 作业。

主审读取完整差异、检查 Python AST，并保存修后测试原文、diff 和两日志身份至私有 `independent/ci-example-fixed-source.py`、`ci-example-test-fix.diff`、`ci-example-test-fix-review.json`。修后测试 SHA256 为 `4d75b81a856553b246c8ac5a34273ce0f1faa40bfd2e1904aae136c7eda58306`。**WA-CI1 测试修正的本地复核通过，源码 finding 关闭；Spec 历史 2、已关闭 2、开放 0，Standards finding 0。** 原 `8a856f5` 的 Windows 必要失败不改变；修正此时尚未作为新精确候选完成自己的 CI/HTTPS 门禁。本次仅核这份测试修正与前片记账，不接受当前 AC4.4 源码、数据或其后续 CI 作为前片替代证据。
