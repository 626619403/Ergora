# AC4.2b 可信建议审查运行：独立评审

评审者：fresh-context 独立代理 `advisory_runtime_review`；未参与实现。日期：2026-11-09。固定基线及初审时 HEAD 均为 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3`。按原始组合需求、本片有限验收、项目 AGENTS、[AC 计划](../plans/2026-11-08-agent-composition.md)、[本片记录](2026-11-09-advisory-runtime.md)，以及 maintainable-project-delivery 的 independent-review 与 codebase-design 要求评审。仅写本报告及本地独立证据目录，没有修改生产、安装依赖、启动模型或操作 Supervisor/Temporal。

## 当前结论

- **Spec：R4 本地门禁通过，ADV-1/ADV-2 均已关闭，无开放阻塞 finding。** 安装包反例、分段原回归、四条新旅程、九份新旧重放、真实模板原件与最终完整范围均已独立核验；R2/R3 的原通过和原模型拒绝分别保留。
- **Standards：最终 35 文件范围通过。** 实现仍位于原所有者，未新增调度器、正式执行账本、后端分派框架、依赖或 CI 作业；新增测试各对应实际协议或回归合同，未发现有证据应删除的冗余测试组。

普通提交、该提交自己的必要双 OS CI 和即时明确 HTTPS 远端身份仍待后续精确终核；本地通过不等于上述交付门禁已经完成。

## 精确范围与检查方式

独立读取实际 `git diff` 和全部 untracked 正文。初审范围为 **14 tracked 改动＋2 untracked＝16 文件**；完整 diff、每份字节 SHA/大小及两份 untracked 原件保存在本地 `.ergora/checks/ac4-advisory/independent/initial.diff`、`initial-scope.json` 和 `untracked/`，不以作者列表代替实际 scope。

生产为 `reference_executor.py`、`reference_inputs.py`、`reference_workflows.py`、`task_envelopes.py`、`tasks.py`；测试为 `test_advisory_reviews.py`、`test_composition_tasks.py` 和 `fixtures/reference_acceptance.py`；其余为 README、PLAN、USAGE、WORKFLOW_DEFINITIONS、current 架构、本片交付记录及前片两份终结记账。前片 CI 记账未被当作本片 CI。

另外沿真实调用读取原冻结 `Activities`、`FileAdapter`、`DevelopmentWorkflow`、`Executor`、`Sandbox`、`process_job`，以及原 `WorkflowInput` 使用者、创建/提交/取消/对账、证据/交接引用、stage_driver、agents、agent_runs、processes、定义编译器/相关 schema 和现有 composition/parallel 测试。冻结源码与这些相邻模块只读，未借此扩大本片实现范围。

## Spec 核对

1. [职责冻结](../../src/ergora/tasks.py#L94)由原创建所有者把预览 v2 的每叶职责封入正式信封 v3；旧 v1 子树缺少新字段的叶子明确投影为 required。至少一名 required 在创建和提交形状处分别检查，覆盖当前输入与历史持久输入两种入口。[版本读取](../../src/ergora/task_envelopes.py#L232)保留旧 v2 字段集合，v3 校验职责与冻结图一致；不以活动库或缺省建议值改写旧任务。
2. [WorkflowInput v3](../../src/ergora/reference_inputs.py#L120)复用既有 construction/execution Interface 和局部注册，分别拥有队列、请求根、submit 活动与 workflow。旧 v2 的 adapter/workflow 现在核精确协议版本；其原 activity 名称、单叶分支、输出结构和 stage/job 身份没有变。
3. [可信执行器](../../src/ergora/reference_executor.py#L297)只在原 monitor 成功、只读快照检查、调用匹配、schema 校验及同份结果字节摘要核对后发布意见。request-changes 保留 FAILED 与 fail 检查，进程/合同失败不产生合格意见；没有用错误字符串判断业务意见。原 receipt 中既有 detail 文案兼容并未承担这一判定。
4. [专用 poll](../../src/ergora/reference_workflows.py#L139)先走 FileAdapter，核原收据身份、结构及全部产物字节；再核意见 job/context/candidate、原终态、agent/reviewer、作者身份/会话、必需产物、检查及成功调用结果摘要。二次读取意见和调用时再核原摘要，覆盖收据初读后的变化。缺少意见的 FAILED/CANCELLED 仅返回运行失败观察，不被升格为建议结论。
5. [v3 叶子与聚合](../../src/ergora/reference_workflows.py#L201)仅放行合格建议 request-changes；必需拒绝、运行失败和 deadline 仍设置/保留 cancel 并 StopWork。原共享祖先 semaphore、根 task 直映、显式 all-join 覆盖、多会话检查、取消其他任务及六阶段 stop/fence/reconcile 保持。聚合 v2 逐成员保留原收据摘要、职责及原意见，没有 actor，也没有把建议 finding 改成 approve。在线与离线使用原引用所有者接受新聚合版本。

## Standards、性能及测试/CI

新增 Input/Adapter/Activities/Workflow 方法是原框架要求的版本选择及执行 Interface；配置差异留在各版本的实现中，上层 worker、scanner 和运输调用者继续走同一 Interface。`_run_document` 和 `_aggregate` 是版本化 workflow 内的完整私有算法，将重复的正式输入/输出处理集中在原所有者；没有人为制造跨文件调用者。

v3 的 leaf polling 确实保留了一份与冻结 `DevelopmentWorkflow.stage` 相同的有界等待骨架，差异是必须消费“原收据＋可信意见”并保留全局取消。该版本隔离所需的局部覆盖有具体消费者；把冻结实现回炉或另建通用调度层会扩大本片范围。现有 all-join/会话/并发和 stop/fence 逻辑则直接继承，没有再复制。各新增 guard 均对应协议串用、历史降级、缺少必需审查、外部产物/候选/调用不符或运行失败等可达情况，未见无关防御分支或吞掉失败后继续批准。

预算继续由原完整 manifest 文件数/总字节、定义深度/实例/材料、1 MB stage context、叶子输入与 Git 原件容量、stage deadline、原进程 walltime 及活动预算限制；不截断后声明完整。新增 poll 只额外读取有原摘要且有大小上限的意见/调用两份产物；结果 JSON 改为一次读取后校验/求摘要，避免重复读取形成不一致身份。没有证据表明新代码引入无界 DAG 遍历或新的高成本调度。本阶段轻量探针耗时 **3.54 秒**，不将协议 fixture 或此耗时解释为真实模型性能。

新测试分别覆盖职责冻结/独立版本、FileAdapter 后的可信意见反例、聚合/停止/会话/取消，以及原受监控 Executor 的批准/拒绝和恢复。活动层原件核验与 workflow 层业务处理属于不同合同，不以两层均有测试判作重复。两例原 Executor 协议回归复用现有 fixture，没有再造执行器。既有 CI 一套双 OS 原生作业会消费新增测试，本片未增加同义 CI 任务；未以测试数量推导实现质量或模型质量。

## 独立执行证据

2026-11-09 **05:52:06 UTC**，使用已有原生环境、显式载入本次源码运行 reviewer 自有 `source-probes.py`，exit 0；`source-probes.json/log` 保留原件。没有启动模型、进程 monitor、网络或服务：

- 建议分支 poll 缺失并超过原 stage deadline 后 StopWork，保留超时 cancel，active_stages 清空。
- 在建议原 FAILED 回执完成 poll 时注入全局取消，完整原 workflow 走一次 fence；清理未知仍为 CANCEL_UNCONFIRMED，取消原因未清空，没有输出 REVIEW_READY。
- 将原 graph v2 信封按旧 v2 成员格式重新封装后仍可读，但 runtime_supported=false 且提交继续明确拒绝，未静默升级；v3 activity 接受旧 v2 context 时在发布前永久拒绝。
- 独立逐份重核 **370 源码/wheel/安装文件相同**，并从固定基线读取 **283 冻结文件**逐份比较；与作者身份表一致。wheel SHA 为 `06aeb3d4f69ae1516cbae1fbc2671018384feffbe9e6b9a79ae7de9e0f9840c3`。`git diff --check` 通过。

## 初审时的运行验收限制（历史状态）

初审读到作者原首轮新测试 fixture 漏 handoff 的失败及修正说明；这些记录不能被覆盖成一次通过。另直接读取到 `r2/packaged-tests.log` 的错误测试文件名（零项运行），以及 `journey.log` 在已完成首条原 run 后因读取不存在的 status 字段退出。两者是验收脚本/命令错误，不能冒充生产失败或完整旅程通过；原件应保留，后续结果必须核同一候选和原 run 身份。

作者 `source-r2`、`native-r1` 是源码及确定性协议证据，不替代最终非 editable 包回归。初审时八组最终包、同原四任务公开 CLI/Supervisor/Temporal/scanner 旅程、旧 v1/单叶 v2/并行 v2 完整 history 重放、原 evidence/handoff/进程清理、自身模板真实模型审查及最终文档/scope 均待独立终核。Windows 原生服务、模型质量、通用串行端口、写执行者、三领域默认组合和页面不在本次运行结论内。

普通提交、该提交自己的必要双 OS CI 与即时精确远端身份尚未发生本片终核。最终通过结论须按本片候选另记，不能继承 `5580c8c` 或前片 CI。

## 复核 finding：ADV-1（P2，阻塞 Spec）

**位置：R2 `src/ergora/reference_workflows.py:184`，`ReviewRequirementsActivities.poll` 的结果身份判断。** 意见与 invocation 的 `result_sha256` 只比较相等，没有校验其类型和 SHA256 格式。原 FileAdapter 核外层产物字节，不能代替内部文档字段的合同验证。由原可信 receipt publisher 发布两个都为 null 的字段、其余候选/角色/会话/检查/产物合法时，poll 接受 advisory request-changes；对 required approve 也相同。后续 workflow 因而能够使用没有有效模型结果摘要的意见，违反可信调用结果身份合同。该场景需要可信产物发布者提供畸形原件；不将 JSON 摘要说成认证，也不声称外部攻击者拥有该受信任卷权限。

**独立原件：** 06:00:59 UTC，使用保留的 R2 非 editable 安装包（该模块 SHA `1fce38ebf379d4b3bf4dfb713f769880d4088e2bea1bd7c61102f05550113a3c`），把真实原 required/advisory 两份 review 收据和全部有摘要产物复制到独立目录，仅把两文档的结果身份同时改为 null、空串、63 位 hex、大写 hex、False、list 或数字，并重新发布合法的外层产物摘要。**14 个反例全部被 R2 poll 接受**：required 原 SUCCEEDED/approve 与 advisory 原 FAILED/request-changes 各 7；每次 poll 前后 receipt 字节完全相同。`.ergora/checks/ac4-advisory/independent/digest-probe.py`、`digest-r2.json/log` 保留可复核程序与结果，没有修改实际原 run 的收据或源码。

最小修复是在拥有意见合同的专用 poll 处先要求结果身份为严格小写 64 位 hex 字符串，再比较 invocation 的身份；相等的畸形值必须是永久 ContractViolation，并保持原 FAILED/SUCCEEDED 原件。需覆盖共同 null 与其他畸形身份，保留有效意见及原运行失败行为。R2 已完成的 188 项、四 run、九份新旧 replay 不继承给修复后的包；修后回归、真实 v3 旅程、模型复审和新身份另行记录。

自身 Codex 原 run `40a6377d44b6444cb7aa9ec01edc72fa` 实际成功退出并返回 request-changes（240.51 秒），并非 approve；ADV-1 原由该模板提出。其关于未供原 Executor/Sandbox 等代码的只读疑问属于输入覆盖限制，没有给出可达写入缺陷。本独立者先前已读这些原所有者及只读快照路径，但仍需把新增 v3 写入尝试反例与修后输入作为后续证据核对。Claude 原失败和第一次 Codex request-changes 均须保留，不得被后续复审覆盖。

## R2 原候选证据终核

本独立者以原 R2 安装包只读执行 `verify-r2-evidence.py`，exit 0；`.ergora/checks/ac4-advisory/independent/r2-evidence.json/log` 保留结果。R2 安装/wheel/公开身份表 370 份相同，八套包回归日志原 SHA 为 `dec5e3c6e106792836a6d2b69637fda59d379d5f3c1e1e30c35cf7fe5453c472`，原文确为 **188 passed /418.31 秒**。这是原包完成结果，并不意味着 ADV-1 不存在。

逐份读取四份原 history，核连续 event ID、完整原信封、专用 v3 workflow/queue、28 份原请求/context/回执及全部产物字节；重新重放四份 **172/178/178/170** 事件 history。核原建议失败意见合法继续到 REVIEW_READY、必需拒绝 BLOCKED、进程失败缺意见 BLOCKED、原活动取消 CANCEL_UNCONFIRMED；每份在线 outcome 引用与原收据相等。四份原 handoff 按外部 SHA 再次离线 verify，与各原 run/outcome 完全对应。旧 v1、单叶 v2、并行 v2 成功/拒绝/取消五份 history 也逐份核原 SHA/事件数并重新重放通过。没有连接或启动服务。

88 份 observer PID/starttime 原件与公开摘要 SHA 相等，当前无同身份存活进程；只读 `/proc/net/tcp*` 核三服务端口没有 LISTEN。首轮 5/0 原 stdout 与公开摘要一致，但其逐 PID JSON 已被继续轮覆盖；只保留公开说明的这一证据限制，不补造已丢失的首轮原件。旅程 **334.09 秒仅为继续段**，不能作为完整首段加继续段耗时或模型性能。

另独立审计 `audit-template.py` 对应的 Claude/Codex 原件：输入 digest、prompt SHA、13 份附件源码正文 SHA、四份完整内联祖先资源和移除活动库后的快照均相符。Claude 确为上游 400、exit 1，未完成模型审查。Codex 原收据及 schema 合格结果确为 succeeded/request-changes，result SHA 为 `b10cca4860ccc176017a97e3a1a33703c8fa3d2f2726240334b9219ba8ea0fbf`；原 native stream 有 **11 个连续候选页**，从 offset 0 到 260,215 字节且最后 next_offset=null，逐页拼回的完整字节与附件 SHA `6b0b091a60d283d561d3bd19881303322f4a711eccf2e6e92a9480a747303193` 相等。第一次相对 URI 的领域拒绝及改用授权 URI 后完整读取均保留；没有把领域拒绝当传输失败或隐去失败尝试。这份真实审查的拒绝结果是证据，不是独立批准。

## ADV-1 源码修复复核与 R3 身份

专用 poll 在结果比较前新增 `isinstance(..., str)` 和严格 `[a-f0-9]{64}` fullmatch。重用独立程序加载修后源码，原 **14 个共同畸形摘要全部永久 ContractViolation**，原两类收据均字节不变；`digest-source.json/log` 保留。该 guard 位于内部文档合同所有者，没有重复整个 FileAdapter 验证或扩大旧活动的行为。

回归只新增共同 null/非 hex 两例及原 monitor 的 v3 写入尝试。后者通过测试 pinned CLI wrapper 显式传入攻击目标，保持生产环境 allowlist；检查原只读 terminal、FAILED 原收据和没有可信意见。这覆盖真实新增发布分支，未引入新的测试框架或 CI 作业。攻击目标经环境变量被原 allowlist 过滤的首次红例须保留为测试构造失败，不当作生产放过写入的证据。

06:07:05 UTC 独立重核 R3 **370 源/wheel/安装文件相同、283 冻结与固定基线相同**，wheel SHA 为 `6b5fd966339397f6c31b05e7d034a0fb6c9fa02ac9475ab9974c81e12e3a837e`；包内相较 R2 唯一变化为 `reference_workflows.py`，新 SHA `2e69800c36cf3ef82580934f46719496ec2d4aedcc17b419594c5fc994a62756`。`.ergora/checks/ac4-advisory/independent/r3-identities.json` 保留原件。新包的八组回归、四个新 run、后续真实模型复审、最终全部文档/scope 与精确提交/CI/远端仍待核，R2 证据不被改记为这些新结果。

## R3 原安装包与原运行证据终核（ADV-2 修复前）

06:11:23 UTC，独立探针以 **R3 非 editable 安装包**重新消费同两类原 receipt 的 reviewer 副本，14 个共同畸形结果身份全部永久 ContractViolation，收据字节均不变；`independent/digest-r3.json/log` 记录实际模块及 SHA，与 R3 wheel 相符。不是仅加载修后源码推导安装包通过。

06:13:28 UTC，以 R3 安装包只读执行 `verify-r3-evidence.py`，exit 0；`independent/r3-evidence.json/log` 保留原件。独立逐文件再核源/wheel/安装 **370** 份相同，最终八套包测试原日志确为 **191 passed /0 skipped /424.17 秒**，日志 SHA `963c6c3c950fba53929991d438fc0df82884daa7c238c6139cddb14648ec052d`。

|R3 原 run|原 outcome|原建议／必需收据|完整 history 事件|
|---|---|---|---|
|`01a1bee8-829b-7848-9547-6381aa950458`|REVIEW_READY|FAILED/request-changes；SUCCEEDED/approve|172|
|`01a1beea-1a42-7908-8dbe-c26fb0bbd5c7`|BLOCKED|FAILED/request-changes；FAILED/request-changes|178|
|`01a1beeb-adeb-79cb-98cb-fd5ef531c9da`|BLOCKED|FAILED/无意见；SUCCEEDED/approve|178|
|`01a1beed-45b6-72e3-a2fd-0c9ba50165dd`|CANCEL_UNCONFIRMED|CANCELLED/无意见；SUCCEEDED/approve|170|

四份 history 均逐事件核连续 ID、完整原 v3 admission、workflow/queue 和 **28 份原 job/context/receipt 及全部产物字节**，再实际重放通过；四份 handoff 用原外部 SHA 再离线 verify，outcome/run 完全相同。成功汇合的原 FAILED 建议和原 SUCCEEDED 必需引用均与聚合 v2 相符；其余原 outcome 没有批准汇合。原活动取消在显式 reconcile 释放原 claim 后仍保持 CANCEL_UNCONFIRMED。工作进程停启仅复用原请求和两个实际调用；原 start 重试返回相同身份。五份旧 v1、单叶 v2、并行 v2 成功/拒绝/取消 history 再逐份核 SHA 并以 R3 重放通过。

原旅程脚本完整耗时 **429.31 秒**，使用确定性后端协议 fixture，不能当作模型质量或模型时延。正常 shutdown 的 observer 保存 **127 个原 PID/starttime**，原件及当前同身份进程均无存活，独立只读核 7233/8233/8765 无 LISTEN；保留采样不能证明捕获每个短命进程的限制。没有为本次复核连接或操作服务。

06:15:51 UTC，`verify-r3-exports-and-mutation.py` 对新三份公开 `-r3.json` 与本地原件的字段、日志/observer 摘要逐份比较通过，公开去机器路径字段单独按规则核验；R2 包与四 run 身份仍分别保存，没有被覆写为 R3。再次以固定基线核 **283 冻结文件**相同。

同一程序直接读取最终包回归的三份原 Executor 目录，重新经 R3 Activities 验每份收据及全部产物：批准为 SUCCEEDED/approve，拒绝为 FAILED/request-changes；写入攻击的实际 checkout 正文确为 `MUTATED = True`，原 monitor terminal 为 `A stage declared read-only changed the checkout or HEAD; inspect its diff`，原收据 FAILED 且没有 `composition-review-decision`。三份 receipt 在复核前后字节完全相同。`independent/r3-exports-and-mutation.json/log` 保留原 receipt/terminal 摘要。原回归源可覆盖该行为，不能仅由测试总数推导只读保证；本次验证也未把快照监控解释为 OS 隔离。

上述包及运行终核只覆盖原 R3 身份；后续真实模板复审提出 ADV-2，不能据这些通过结果宣称 R3 整体 Spec 合格。精确提交、自己的必要 CI 和即时 HTTPS 远端身份仍未发生本片终核。

## R3 真实模板与 ADV-2（P2，阻塞 Spec）

R3 Codex `gpt-6.1-sol`/high 原 run `e0cd50a100a841399e6eb3ec7a212f69` 实际 **206.15 秒 /succeeded /CLI exit 0 /request-changes**，result SHA `0a8a730e2a370f6f177e09dfbb61efd326c1bd8ebb378511149619c05c93c3dc`。06:17:43 UTC 独立执行 `audit-template.py` 通过：19 份完整源码正文身份、四份完整内联祖先资源、冻结 input/prompt/manifest 与真实 run 相符；原 native stream 的 **12 个连续 MCP 页**由 offset 0 到 **335,664 字节**，最后 next_offset=null，逐页重建附件 SHA 为 `31aced75f9c9ed48b94aa379d4d616b62f7c30f47c15ec5a76aab8c7b75ff458`。初次相对 URI 的领域拒绝与随后正确 URI 完整读取均保留。独立又直接读冻结 prompt 第 57 行，ADV-1 复核任务确已送入本次调用。`independent/r3-hosted-review-codex-audit.json`、`r3-template-codex.log` 保留原件。

模型确认 ADV-1 的严格摘要及同份结果字节校验成立，没有新的 Standards 阻塞；但提出 **ADV-2：`src/ergora/task_envelopes.py:158` 的单成员快捷返回绕过新 graph v2/formal v3 的显式 all-join 合同**。此时仅一名 required、只读 reviewer，输入直接来自根 task，即使所选 workflow 输出只是转发根输入，或直接指向 reviewer result，正式形状门禁仍返回可运行。v3 workflow 自己会执行唯一 reviewer 并分组聚合；实际缺陷是接纳了本片声明不支持的图，不能描述成漏执行唯一 reviewer 或绕过候选批准。

06:20:07 UTC 独立以保留 R3 非 editable 安装包，从真实 WorkflowDefinition 导入、manifest 准备和 `tasks._composition` 形成 **六份完整合法静态 manifest 与封装**，逐份 unwrap 再调用 `execution_input.require_submission`，不是只给内部函数喂不合法 graph。graph v2/formal v3 的根输入直传、reviewer 直出、显式 all-join 三形状均错误地被准入；前两应保持可静态读取但拒绝正式运行。对照 graph v1/formal v2 的三形状也均准入，应保持其旧行为。`independent/join-probe.py`、`join-r3.json/log` 保存实际模块 SHA `7d9e207b2c6dc4cfd936e10b1ac820b114a67aefc194bab7f420e242a588b41b`、六个原封装与原 manifest 身份，未启动模型、monitor 或服务。

最小修复只将 `len(members) == 1` 快捷路径限定到 graph v1，让 graph v2 消费原有 output/coverage/all-join 验证。06:20:44 UTC 独立同程序加载修后源码，六份原封装的身份完全相同：两个新无汇合形状均明确拒绝，新 all-join 和旧图三形状保持准入；`join-source.json/log` 保存结果，修后模块 SHA `6703827c8b2c8ca9304191ada0a6c9711bd61e416aab6797d2cf85d55570290e`。

新增三参数公开创建/读取/运行支持测试对应上述两拒绝一接受，保留无汇合图的静态存储能力且不发布远程意图；原 R3 实际日志 `r3/adv2-original.log` 确为 **2 failed /1 passed /5.78 秒**，失败均为新无汇合图误报 runtime_supported=true。修后 `r4/targeted.log` 原文确为 **3 passed /6.46 秒**。原 Executor 的三份 v3 fixture 加上显式 gather，是使测试输入满足合同，并未更改旧公开模板。没有新增调度、schema 或 CI 任务。

R3 原模型没有执行测试或重放，原运行/安装/冻结全清单与 CI 也未完整交给它；这些边界在原意见和本报告中均保留。本独立者另有原件验证，不用其中一方的证据补成另一方已经做过的检查。ADV-2 源码修复通过仍不替代后续 R4 包、实际旅程和真实模板复审；精确提交/CI/远端终结继续另记。

## R4 安装包与原运行证据终核

06:23:22 UTC 再独立核 R4 **370 源/wheel/安装文件相同、283 冻结对固定基线相同**，reference.verify PASS。wheel SHA 为 `d16f835e18e564719d4e884ed8c64b28bbdd1196a8bf67c7d8da3adf3902cbee`；相较 R3 包唯一变化是 `task_envelopes.py`，SHA `6703827c8b2c8ca9304191ada0a6c9711bd61e416aab6797d2cf85d55570290e`，ADV-1 的 workflow 模块 SHA 保持。`independent/r4-identities.json/log` 保留结果。

独立程序分别改用 R4 安装包，14 个共同畸形结果摘要继续永久拒绝、原收据不变；六份合法 manifest/封装对照继续得到新无汇合两拒绝、新 all-join 与旧图三形状保持接受。`digest-r4.json/log`、`join-r4.json/log` 各自保存 R4 实际模块身份，不继承源码模式或 R3 结果。

R4 全套回归初轮批准/拒绝两例测试失败。独立直接读取同三份原 Executor 目录，并经 R4 Activities 重验原 receipt 及全部产物字节：SUCCEEDED/approve、FAILED/request-changes 和原只读写入 FAILED/无意见均符合合同；原收据均未变化。两份正常审查冻结 input 中 `call.member` 均为 `root/review`，该实例的 resources 完整；末实例已是新增 gather join，没有 resources。因此测试辅助函数 `instances[-1]['resources']` 的旧下标假设不再成立，不能把这两红解释为模型意见未正确发布。`independent/r4-original-regression-artifacts.json/log` 保存实际原件；它也不能代替 pytest 通过。

06:30:08 UTC 以 R4 安装包执行独立 `verify-r4-evidence.py`，exit 0。八组初轮原日志确为 **2 failed /192 passed /0 skipped /434.51 秒**，两失败均为上述 helper 的 KeyError，日志 SHA `20b2f78c5126a4fb547c4959e13fdb9200d15baa05381c42a93e77e147fcc7ff`。辅助函数改为按原 `call.member` 选择实例，只重验两失败、原 mutation 和旧单叶恢复消费者，原日志确为 **4 passed /45.14 秒**，SHA `44b727e33c366d6de2d19a58e7d2ac7bac0e311e3a59d6e1ad90630f8a63cee7`。生产包未变化；不把两轮相加当作 196 个独立用例，也不宣称有一次 194 全绿。已逐行读取 helper 最小修改，并重新只读核修后三个原 Executor 的全部收据/产物与只读攻击，`r4-corrected-regression-artifacts.json/log` 保留。

R4 四条全新原运行如下，原旅程完整耗时 **429.34 秒**：

|R4 原 run|原 outcome|原建议／必需收据|完整 history 事件|
|---|---|---|---|
|`01a1bef8-0a2c-7d03-b59f-c5edb69d7667`|REVIEW_READY|FAILED/request-changes；SUCCEEDED/approve|172|
|`01a1bef9-a174-73c8-b093-dd0a0b483197`|BLOCKED|FAILED/request-changes；FAILED/request-changes|178|
|`01a1befb-382b-76be-a39b-7435231a5716`|BLOCKED|FAILED/无意见；SUCCEEDED/approve|178|
|`01a1befc-cb45-7797-84e5-e409f3651d9b`|CANCEL_UNCONFIRMED|CANCELLED/无意见；SUCCEEDED/approve|170|

独立重读四份完整 history 的连续 ID、完整原 v3 admission、workflow/queue、**28 原 job/context/receipt 与全部产物字节**；每份在线 outcome 引用匹配原件。四份 handoff 用原外部 SHA 再次离线 verify，run/outcome 一致，四新 history 及五份原 v1/单叶 v2/并行 v2 成功/拒绝/取消 history 均以 R4 实际重放通过。首条原 worker 停启继续用同七请求和两调用，原 start 重试身份相同；取消任务 reconcile 释放原 claim 后仍保存 CANCEL_UNCONFIRMED。原 observer **129 个 PID/starttime**摘要与完整原件相等，当前同身份无存活，三服务端口无 LISTEN；保留采样不能穷尽短命进程的限制，没有连接服务或调用模型。

06:31:48 UTC，独立核三份公开 `-r4.json` 与全部本地原件、原八组和修正日志、observer 摘要相符；R2/R3/R4 wheel 与各四 run 均为不同身份，R2/R3 原真实模型 result 的公开文件字节 SHA 仍与其原记录相同，均保留 request-changes。`independent/r4-exports.json/log` 保存结论。

同一时刻独立从 Git 实际获取完整 **33 文件（16 tracked＋17 untracked）**，将完整 diff 与所有当前文件字节另存 `independent/scope-r4-before-model/` 和 `scope-r4-before-model.json`；相较初审 9 份原文件改变、17 份新增、零删除，各新增生产/测试行为和文档/原件已审。最终模型原件尚未进入此快照，不能把 33 当作后续完整终结范围。两 finding 在 R4 安装包的拒绝/对照和原运行验收均已实证关闭，当前已审范围无其他 Spec 或 Standards 阻塞；真实模板结果与最终全部 scope 仍另核。

## R4 真实模板与最终完整范围

最终 Codex `gpt-6.1-sol`/high 的 structure-review/task-mcp 原 run **`a9b3ff606e99415b8c79ad0d307156e9`，275.01 秒 /succeeded /CLI exit 0 /approve**。独立 06:35:43 UTC 运行 `audit-template.py` 通过：从实际 native stream 的 **14 个连续候选页**重建 **340,847 字节**，offset 0 到 340,847、最后 next_offset=null，附件 SHA `57fb28a55ba8158173a1dd01310b1d53b092526a4aa9494142dcb6d3f9edf218` 与原记录完全相同。19 份完整源码正文、四份完整内联祖先资源、冻结 input/prompt、native 审计收据与结构化结果均核过；初次相对 URI 的领域拒绝及之后授权 URI 的完整读取保持原件。`independent/r4-hosted-review-codex-audit.json`、`r4-template-codex.log` 保留独立重建证据。

06:37:43 UTC 又逐份核模型记录的 **19 份源码均等于当前最终文件**；完整 manifest 与冻结 input 的 composition 相同，原 manifest digest `e325510801821a336b099248aa5ee7f11b13f1eae52b0243f6ea71aa2561201c` 相符。实际 `task.txt` 同时包含两个 finding 和原 `2 failed, 192 passed`、修后 `4 passed` 正文，未从脚本存在的字符串推导已送达。wrapper/project 材料预算共同为 750,000；项目 grant 的权限、工作流权限及 AgentDefinition 其余字段保持原值，原有效 policy 仍无写/无 shell。扩充完整附件没有扩大工具权限。

[公开原身份](evidence/2026-11-09-ac4-advisory-self-review-r4-identity.json)与本地原记录完全相等，[公开原结果](evidence/2026-11-09-ac4-advisory-self-review-r4-result.json)字节 SHA 确为 `b0aee1a2db7b2a4b3b39aaa0d994a847489b3e523c1e0a08a6a6fa46b077c641`，其结构化 decision 为 approve。模型明确确认两 finding 修复、无新 Spec/Standards finding；它没有执行测试，原运行/冻结清单/CI 也不属于其独立验证范围，分段 192/2＋4 未被称为一次 194 全绿。独立者的实际原件核验与模型意见继续分别记账。`independent/r4-model-final-identity.json/log` 保存最终映射。

最终重新取得全部 **35 文件＝5 生产＋4 测试/fixture＋10 Markdown＋16 公开 JSON**；首次完整来源为 **16 tracked 改动＋19 untracked**，作者暂存后按 `git diff <固定基线>` 重新取得 35 份已跟踪变更，未只看 unstaged diff。HEAD 仍为固定基线 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3`。新增末两文件正是 R4 模型原身份和原结果；完整生产/测试正文、历史记账、计划/使用手册及全部公开证据已经阅读或逐字段与实际原件核验，不能以作者 scope 列表代替。所有当前字节及完整 diff 最后存 `independent/scope-r4-review-approved/` 与 `scope-r4-review-approved.json`。初审原件、R2/R3 拒绝、R4 初轮两 fixture 错误和修后四项均保持各自身份。

独立最终静态检查 **10 Markdown、249 本地链接/锚点、79 CLI parser 示例**全部通过，`git diff --check` 通过；原结果在 `independent/static-documents.json`、`r4-documents.log`。未把这些静态检查当作运行验收，也未将 ignored 的后片设计草稿计入当前 35 文件。

最终本地结论为 **Spec 通过、Standards 通过**，ADV-1/ADV-2 已在最终安装包实证关闭，无开放 finding。六阶段、owner 批准、原候选/账本/monitor/Temporal 和旧协议保持；没有证据支持继续提炼新框架、删除现有必要分层测试或新增 CI。真实模型时延和确定性协议旅程耗时只说明其各自范围，不构成性能改善或模型质量结论。Windows 原生服务、通用串行端口/可写专家分配、三领域组合、页面、完整活动进程崩溃恢复及外部 Claude 兼容性仍按计划另片处理。

精确 Git 提交对象、该提交自己的必要双 OS CI 及立即明确 HTTPS 远端身份须在普通交付后追加核验。此结论只终结本地两轴，不继承前片或其他候选的 CI/远端身份。
