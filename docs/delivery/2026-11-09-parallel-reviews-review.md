# AC4.1 必需并行审查：独立需求与维护性评审

日期：2026-11-09。审查者：`/root/parallel_reviews_review`，新的 fresh-context 独立上下文；只接收原始需求、有限合同、固定基线、变更范围与已有检查位置，没有继承实现对话。按项目 `AGENTS.md`、`maintainable-project-delivery` 的 independent-review brief 和 `codebase-design` 检查。审查者仅写本报告；未修改源码、测试、包、依赖、运行状态，未启动模型、服务、完整测试矩阵、commit 或 push。

## 范围与当前结论

固定基线及初审 HEAD 为 `4538f4e44a3c301aedde570e130a342bc1c55714`，分支 `refactor/architecture-foundations`，候选为未提交工作树。已自行取得完整 tracked diff 和两个初始 untracked 文件，逐一阅读六个生产文件：`task_envelopes.py`、`reference_inputs.py`、`reference_workflows.py`、`reference_executor.py`、`reference_task_reconciliation.py`、`handoff.py`；四个测试文件：新增 `test_parallel_reviews.py` 及修改的 `test_composition_executor.py`、`test_composition_tasks.py`、`test_handoff.py`。文档范围为 `docs/PLAN.md`、本片交付记录和前片 CR5 两份交付/审查记录的终结追加。另核原 workflow/stage、Activities.poll、FileAdapter、executor/monitor、composition 编译/准入/创建/提交、证据索引、导出、A2A 结果消费者和既有 CI。

需求依据为[AC 逐片计划](../plans/2026-11-08-agent-composition.md)、[本片有限合同](2026-11-09-parallel-reviews.md)及原始需求：模板可组合不同职能/专长、后端/资源/权限，所有祖先资源完整继承且子权限不越父，保留六阶段、批准、可信 verify、精确候选、attempt-before-send/memo/unknown 恢复及 283 冻结。本片只开放多必需只读 review 的独立嵌套分支与显式 all-join；建议审查、动态前驱输出、写者分配和完整 AC4 后置。

**初审需求符合性：待修及待验。维护性：待修。** 下列四项已在初审非 editable 安装包中独立复现，并即时交给实现者；前三项修正已进入工作树，AC4-4 新报，尚待新包复核及真实旅程证据，不预记关闭。实际 R2 在首次公开 start 时因缺 `a2a-sdk` 包元数据失败；原失败保留，不能称 Temporal 并行验收通过。R3 与自身真实模型审查尚未完成。

## 初审 findings

初审源码定位：AC4-4 为 `src/ergora/task_envelopes.py:150`；AC4-1 为同文件 `:159`、`:173`；AC4-2 为同文件 `:187`、`:199`，及 `src/ergora/handoff.py:60` / `src/ergora/reference_task_reconciliation.py:166`；AC4-3 为 `src/ergora/reference_workflows.py:77`。以下行号绑定修正前初审包。

1. **AC4-4 / P1：合法共享 all-join DAG 使覆盖计算呈指数增长。** `coverage` 对每个前驱反复递归，没有按实例/端口记住已完成的集合。独立以现有 schema 和 `_Compilation.compile` 编译两个无依赖 reviewer 的合法静态图：j00=all(r0,r1)，j01=all(r0,j00)，后续 ji=all(j[i-2],j[i-1])，root 输出最后 join。安装包 selector 接受；只在该调用期间用 `sys.setprofile` 计数，18 个 join/21 个实例产生 **13,530 次 coverage**，24 个 join/27 个实例产生 **242,786 次 coverage**；对应样本耗时为 0.0106/0.1941 秒，增加六个节点即放大约十八倍。这不是模型耗时或网络噪声。更大图仍远低既有实例上限，却会让创建、摘要、历史读取和执行准入长时间占用 CPU。最小修正是局部缓存 `(path, port)` 的已完成覆盖集合，保留 active 环检测；用共享 DAG 的访问次数或等价复杂度回归，不引入机器墙钟阈值。

1. **AC4-1 / P2：合法静态 passthrough 输出导致摘要崩溃。** 初审位置：`task_envelopes.review_members` 的终端选择和 `coverage` workflow 分支。WorkflowDefinition 的 binding 明确允许 `{"input":"task"}`，静态 schema 与 `_Compilation._links` 都接受，但新代码无条件取 `origin['node']`/`origin['output']`。独立从实际三成员 admission 取得图，将 root 输出改为这种合法静态输出，先核 schema/links 可接受，再调用安装包 summary，得到 `KeyError('node')`。嵌套 workflow 输出同形会在 coverage 递归中失败。此前多成员统一返回不支持，静态创建和历史仍可保留；新代码破坏这一兼容合同。最小修正是在两个使用处明确把 passthrough 判为运行时不支持的 `ValueError`，以真实导入的 root/nested 合法静态图检查 summary 为 false，而非整体吞掉 KeyError。

2. **AC4-2 / P2：聚合声明的 stage/job 身份与原回执矛盾仍报告 matches。** 初审位置：`task_envelopes.outcome_receipt_sha` 及两个证据消费者。helper 只读成员的 receipt SHA，忽略同一成员引用中的 stage、job ID 和 job SHA。独立以新增 handoff 用例的同形原件索引，在安装包中分别把这三个字段改成矛盾值，按原规则重算 outcome 摘要；`handoff._references` 三种全部接受，原 job 仍声明 matches。这是包内链接矛盾，与离线格式不认证来源的既有限制不同。最小修正是由同一个 helper 比较 stage/job ID/job SHA/receipt SHA，两消费者保持同一规则；正常旧回执形状和 unavailable/not_recorded 语义保持。

3. **AC4-3 / P2：窄子 scope 等待者占用祖先额度，独立兄弟分支被无谓串行化。** 初审位置：`reference_workflows.CompositionDevelopmentWorkflow.stage` 的 semaphore 取得顺序。独立用既有 `_Compilation` 在内存编译合法图：project/root 并发 4，子 workflow a 含四个无依赖 reviewer、a 并发 1，兄弟 workflow b 含一个 reviewer，root all-join(a,b)。所有叶直映同 task，selector 接受五成员。门控首个 a 回执并让事件循环推进二十轮，只有 a/r0 进入提交；其余 a 任务已占住 project/root 额度并等待 a，b 无法进入，尽管它可与 a/r0 并行。现有根并发 1/2 用例测不出这种嵌套性能退化。最小修正是按固定树形 scope 从窄到广取得额度，或等价保证等待子 scope 不保留父额度；增加一项不同子 scope 的饱和回归，不需要另一套调度器。

## 所有权、复用与检查价值

运行形状选择归无 SDK 的 `task_envelopes`，由 summary、正式 submission 和 executor 三个生产调用点共用；图覆盖递归属于它的私有算法。原 `reference_workflows.stage` 承担并行协调，成员继续调用原 stage；`reference_executor` 仅将完整稳定 stage 映射到唯一冻结成员，保留原 claim、隔离 worktree、monitor、receipt、实际后端与 MCP 证据。没有新增生产文件、全局注册框架、持久调度器或另一套账本。

聚合没有伪造模型 actor/通过回执，而是将各成员原 receipt 的身份纳入可信 workflow 结果与原 evidence 摘要。两消费者共用引用判定是实际复用，AC4-2 的修正也应集中在该所有者。authors 排除 review 子阶段，使较慢审查不会因较快审查已完成而被误判为实现作者；原 Activities.poll 仍核候选、角色、独立检查、作者 ID/会话。

新增 scheduler 单测在原 call seam 控制提交与 poll，检查根上限、独立会话、失败/取消及 aggregate 原件引用；不将其合成成功回执当成完整 poll、真实 Temporal 或模型质量证明。既有测试只调整有限支持边界的错误文本，没有新增 CI job 或重复整套旧六阶段。四项 handoff 引用矛盾可共用一个参数化回归；没有证据支持删除原批准、恢复和候选合同检查。AC4-3 是已测的嵌套性能问题，其余图校验/冻结重验未据纯代码行数判为冗余。

## 已核检查与未验范围

- 独立重算首包 wheel、安装树和身份记录：**369 文件完全一致，非 editable，283 冻结身份一致**；wheel SHA `3664fe70244d707cc8673bd1db54b2eeff7531dbde60a5bcb816863f8f5e0340`。冻结目录对固定基线无 diff。
- 已读实现者首包原日志：相关五组 **124 passed / 81.36 秒**。这属于初审包协议/回归证据，不能替代修正包、真实 Temporal 或模型运行。
- 独立四类反例均只在内存改变输入或用现有函数观察，未改安装文件；`git diff --check` 通过。没有机械重跑整套应用、CI 或真实服务矩阵。
- R2 原日志确认为公开 start 的依赖失败，先于实际任务执行；新 R3 必须保留自己的运行输入、后端、原 receipt/artifact、完整 history/replay、取消/fence/reconcile、index/handoff 与正式退出证据。还需本大项自身模板真实模型结果和修正包身份。Windows 原生执行、本候选的提交/CI/远端身份尚未核验。

本报告保留初审事实与 findings；同片修正及验收证据到齐后另节追加复核，不覆盖失败原件，也不把本片称为完整 AC4 交付。

## 四项修正与最终包独立复核

同片复核固定基线不变。实现者先在旧包取得 root/nested 透传两红、三种引用矛盾三红及正常摘要一绿、窄 scope 一红、共享 join 一红，原日志保留。修正集中在原所有者：输出端口明确判为不支持；`outcome_reference_state(outcome, job)` 供线上/离线共同比较完整引用；固定树形 scope 从窄到广取得；局部覆盖缓存只存完成的 `(path, port)` 集合。环检测先于缓存命中，父层 union 不修改已缓存的子集合。没有新增通用调度或缓存框架。

独立重算最终 R5 包 **369 份 source/wheel/安装/记录字节全部相同，283 冻结保持**，非 editable；wheel SHA 为 `e69663a6b0d9b682201943f00241208fced85e969214cfd09b6819857657c214`，`task_envelopes.py` SHA 为 `b43114591e99b17fe67cb3775142514d866adaa4632e5a382af01b0ff456cd4a`，`reference_workflows.py` SHA 为 `7dcdd6b2483593ba097985a89ffc51dd948f374626d6af9aa2895ff6538e1f8b`。审查者在该安装包独立复做：

- 读取已真实导入/prepare 的 root、nested 透传 manifest，两者 summary 均为 `runtime_supported: false`，不抛 KeyError。
- 合法 24-join 共享图仅 **52 次 coverage**；独立样本约 0.000421 秒，此耗时只作观察，验收没有墙钟阈值。原同算法反例为 242,786 次，缓存实际消除了重复子图展开。
- 门控窄子 workflow a 的首个 review 时，a 与独立兄弟 b 均已进入原提交，祖先并发仍受限。
- 正常完整引用返回 matches；四个引用字段分别矛盾均返回 differs。再用真实成功任务的原 index 改这四项并正常重算 outcome 摘要，handoff 全部明确拒绝。

**AC4-1、AC4-2、AC4-3、AC4-4 均关闭；所查生产代码的需求实现及维护性通过，没有其他开放代码 finding。** 这不预记真实模型审查或交付门禁通过。

已核实现者 R4 原包五组 130 passed / 149.08 秒；最终 R5 首轮为 **1 failed / 70 passed，35.93 秒**，失败是旧架构 allow-list 未承认新的 wire-contract 依赖。`task_envelopes` 实际顶层只导入标准库，不依赖应用或 SDK。现有架构测试将其明确约束为无第一方依赖的基础模块，并仅允许 handoff 依赖这个基础模块；**10 passed / 0.19 秒**。这没有放开任意应用依赖，也没有因此改生产包。旧 unsupported 测试把只有解释器软链接的假 venv 留在 module-scoped installation，现改为与已有原生 fixture 一致复用完整 `sys.prefix`；原支持形状拒绝和无副作用断言保持。上述两项是必要测试装配/合同同步，未增加 CI job。

## 真实协议旅程与最终代码重放

已读 R3/R4 实际脚本和原 CLI 输出。R3 的首次成功运行属于初审包，worker 停止时三审查原 receipt 完成，原 run 重开后到达 REVIEW_READY，只有三个原 Agent 调用；随后的验收脚本误读终态字段而失败。R4 使用前三修正的包继续同一组不可变任务：第一条只重读/重放和收集原件，另两条继续原创建任务执行拒绝和取消。R5 只增加图覆盖缓存；实现者最终包重查原件，审查者也在最终安装包亲自本地完整重放三份原 history，均通过。没有将旧包生成的成功 receipt 重新归属 R5，亦没有重复模型 fixture 副作用。

|原任务|完整 history 事件|原 job|原 outcome|三个 review 原终态|
|---|---:|---:|---|---|
|成功及 worker 恢复|183|8|REVIEW_READY|SUCCEEDED / SUCCEEDED / SUCCEEDED|
|必需审查拒绝|189|8|BLOCKED|SUCCEEDED / FAILED / SUCCEEDED|
|活动审查取消|178|8|CANCEL_UNCONFIRMED|SUCCEEDED / CANCELLED / SUCCEEDED|

独立从三份 history 的实际 payload 核原 workflow 类型/队列、完整 admission 输入、八个 submit context 和最终 outcome；逐个对照当前磁盘原 receipt、job/context 摘要与 stage 路径，核三位 reviewer 的不同 session、其会话不进入作者集合、同一最终候选，重算 **116 份原 artifact 的实际字节 SHA**。成功 aggregate 覆盖全部成员，没有 actor；verification/aggregate 的原 evidence 摘要一致，三个审查原件均 matches。失败和取消 outcome 没有通过聚合，三个原件引用均保留 not_recorded。三份交接包以各自原整包 SHA 在最终包重新验证，outcome 与原 history 相同，仍为 `origin_authenticated: false`。

拒绝/取消之后当前 external-status 均无 unresolved/unexpected job；取消的原 outcome 保持 CANCEL_UNCONFIRMED，显式 reconcile 的原结果为 external_confirmed/lease_released，且原 outcome 未改写。R4 原脚本等待延迟写窗口后核没有 late-review。独立核观察记录的 **49 个 PID/starttime** 没有原存活进程，三服务端口当前关闭；该抽样不能证明看见每个短命进程，不声称完整活动进程崩溃恢复。R4 的 228.312 秒为这一继续旅程总体耗时，不作模型速度或跨版本性能承诺。

这些是实际 CLI/Supervisor/Temporal/scanner、真实控制面和确定性 Agent 协议的运行证据；业务 owner 的人工决策、模型审查质量和 Windows 原生运行另计。私有原件位于本片忽略的 `.ergora/checks/ac4-parallel/` 各轮目录，未向公开文档写入机器配置或凭据。

## 自身模板真实审查与建议处置

已独立读实际安装包调用脚本、原 `composition run-input` 记录、模型 stdout、原 result、task-MCP scope/审计及公开的[输入身份](evidence/2026-11-09-ac4-parallel-self-review-identity.json)与[审查结果](evidence/2026-11-09-ac4-parallel-self-review-result.json)。本次真实运行使用 `structure-review` 模板及 `architecture-evidence` Skill，经用户已允许的 Codex 回退，以 `gpt-6.1-sol` / high 执行；run 为 `064340c46a714076b647842064462494`，耗时 **135.072 秒**，原运行 succeeded / exit 0 / approve。它不是原六阶段正式批准，`formal_execution_authorized` 为 false，不推导模型错误独立或 OS 隔离。

审查者从原模型 stdout 提取实际 MCP 工具返回：先读取 Skill，随后连续读取 candidate 的 **8 页**，offset 为 0、30000、60000、90000、120000、150000、180000、210000，末页 21383 字节且 `next_offset: null`。逐页偏移、总长及 SHA 均一致；重组完整 **231383 字节**，SHA `537e3b0afbf35f24daf861cba33d7e47ce7fe59ef800e8be9dba4ff571069300`，与原 manifest 附件、run 输入快照及 scope 的实际内容相同。16 份完整源码各自字节 SHA 对应原身份。原 scope SHA 与 native 审计回执 SHA、prompt SHA `6a0650460200fca33e762b27f1462fa95a915f55d1a74bcf1eb882e575fb8cf2`、result SHA `5bd39d4062fa0d65fe00175ad6ccd07b4def31db24e4b9283af91b083cafaa5e` 均独立重算一致；最终安装包重验原 manifest/input 及 run 输入快照，完整 digest 与公开身份一致。原定义库已移除，附件读取不依赖它们。

模型没有阻塞 finding，只提出一项非阻塞建议：原架构检查虽禁止 `task_envelopes` 的第一方应用依赖，却没有真正禁止第三方 SDK。实现者在**同一原断言**中增加该模块的 import roots 必须属于 `sys.stdlib_module_names`，其余模块许可不变。独立读当前 AST 收集和断言后确认建议已落实；原日志为 **10 passed / 0.19 秒**。这是模型结束后仅有的受保护源码变化，原模型输入身份及结果未回写，生产包保持不变。

模型明确表示未运行测试，且缺少完整 admission/backend/transport 等相邻模块与基线 diff，不能独立证明全部继承、权限、恢复或 283 冻结；没有把实现者的旅程叙述当独立复现。本报告此前的完整仓库审查、包身份重算、原 artifact 核验和最终代码 history replay 分别提供其实际范围内的证据，不把两次审查合称更广的模型质量或跨平台验证。**自身模板真实审查及建议处置已核通过；四项原 finding 保持关闭。**

## 最终本地两轴与文档范围

固定基线仍为 `4538f4e44a3c301aedde570e130a342bc1c55714`。再次独立取得 tracked diff 和全部未跟踪文件，当前完整候选 **29 文件**：6 个生产模块、5 个测试文件、13 份 Markdown 和5 份公开 JSON 证据。除上述架构断言的建议处置，全部受保护源码身份与真实模板输入保持相同；六个生产模块和 wheel 与最终 R5 身份一致。未夹带 AC4.2 建议审查或串行/写执行者实现。

已读新增公开手册、示例说明、当前架构、总计划与 AC 逐片计划，以及前片 CR5 的精确终结追加。文档按原所有者解释显式必需 all-join、完整祖先材料、稳定 stage/job、共享配额、同候选与独立会话、原件聚合及取消/恢复；建议审查、通用串行、写分配、三领域默认组合、页面与完整 AC6 继续后置，没有把本片称为整个 AC4 完成。公开五份 JSON 与原数据逐字段核对，旅程仅省略服务机器详情；完整 history/job/收据身份和结果保持，未包含机器目录或凭据。包文件映射 SHA 按原 `json.dumps(files, sort_keys=True)` 序列化独立重算一致。

最终安装包的只读文档检查为 **13 份 Markdown、342 个本地链接及锚点、零缺失**；README、Agent/Workflow 手册及自身模板示例的 **75 条公开命令**通过当前 CLI parser，另独立核新增 USAGE 的 **2 条 parallel-review 准备/验证命令**通过。`git diff --check` 通过。原失败、R3/R4/R5 执行身份及 Windows 原生未验范围保持，未因文档收口而重跑已成功副作用或宽测试矩阵。

**最终本地需求符合性：通过；维护性：通过。** AC4-1 至 AC4-4 已关闭，自身真实模板建议已处置，没有开放 finding；可按这 29 文件的固定范围进入普通提交。精确提交对象、该提交自己的必要双 OS CI 和实时 HTTPS 远端身份尚未执行或终核，不预记交付门禁通过。

## 普通提交身份与自己的 CI

独立 `rev-parse` 得普通提交 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`，唯一父提交为固定基线 `4538f4e44a3c301aedde570e130a342bc1c55714`。从 Git 提交对象逐份读取全部 **29 文件**，字节 SHA 均与实现者冻结的 `review-scope.json` 相同，完整对象范围无增减，冻结目录相对父提交没有 diff。该 scope 原文件 SHA 为 `b9e9d63315c7c370519d87b6dfdef4e197a1c8c6202d235313145605bc724d39`。

2026-11-09 04:48:27.540035 UTC 的独立 REST API 首读为 **403 rate limit**，280 字节响应 SHA 为 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`，保留原失败而转用官方 HTML。随后直接读取该提交自己的[Portability 42563729227](https://github.com/626619403/Ergora/actions/runs/42563729227)，核 run 页明确链接完整提交及 `.github/workflows/portability.yml`；04:49:19.388114 UTC 尚为 In progress，Ubuntu job `128985557789` 的 wheel 与 identity 已成功、应用回归在途。这是中间观察，不预记 Windows、七必要步骤或精确远端终结成功。

## 精确 CI 与即时 HTTPS 远端终结

原 `job_groups_batch?attempt=1` 响应仅返回 Ubuntu，且明确 `totalCount: 2 / hasMore: true`；这属于读取只取了首批，不能由此推断 Windows 未调度。试加 `page=2` 仍返回同一首批。审查者读官方 `actions-run-jobs-list` 所引用脚本，核实际分页参数为 `batch` / `size`，再用 `batch=0&size=200` 取齐两作业，返回 `totalCount: 2 / hasMore: false`。上述分页限制和 API 403 均保留；没有重跑或替换 CI。

**2026-11-09 05:02:56.122194 UTC**，独立直接读取原 run `42563729227` 的官方 run 页、完整 job groups 和两 job 页，整体为 **Success**。从该提交自身 workflow 对照矩阵及步骤，核以下 **七个必要步骤全部 success**，每条步骤有 `data-job-completed`，原 logs URL 均包含完整提交 `f9f4fc01546aa065f2fe32294a28c31387b2cf56` 及相应 job ID；没有 failure、cancelled 或 timed_out 步骤：

|原作业|必要步骤|最终结论|
|---|---|---|
|[Ubuntu / Python 3.11，128985557789](https://github.com/626619403/Ergora/actions/runs/42563729227/job/128985557789)|Build and install wheel；Packaged reference identity；Native application regression|3 项全部 success|
|[Windows / Python 3.12，128985558051](https://github.com/626619403/Ergora/actions/runs/42563729227/job/128985558051)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|4 项全部 success|

这一轮独立官方读取的 run 页为 157579 字节，SHA `138729b3e808c37980462fbbea6b854c4b6724e3a12502bfbb063c3ec8a6c6d6`；完整 job groups 为 700 字节，SHA `2bed0c95fec63e3dc306f3c58677f2aa2cb02d944bbca8565963b5b2b90d50cf`。Ubuntu/Windows 原 job 页 SHA 分别为 `ed9241f94378b6d5088e19cfccda13cec2273757c96606abe3332603a0644ae5`、`b3d4c9b0f93c8cbac723829c9f38c38b5e677fdcb3960d9bde0c2ed80d496211`。原运行未重试，未沿用父提交或后续候选的 CI。Windows 这里证明原生应用回归与安装升级 CI，不扩为 Windows 的真实三审查协议旅程。

七项核完后，在**同一独立脚本中立即**执行 `git ls-remote --exit-code https://github.com/626619403/Ergora.git refs/heads/refactor/architecture-foundations`，以无仓库目录和禁用全局/系统 Git 配置避免 URL 被隐式改写，使用明确 HTTPS 传输。**2026-11-09 05:02:58.894557 UTC** 命令 exit 0、stderr 空，远端分支返回完整 SHA **`f9f4fc01546aa065f2fe32294a28c31387b2cf56`**，与已核 29 份对象的本片普通提交相同。

**AC4.1 本片最终结论：本地需求符合性、维护性、自己的必要双 OS CI 和即时精确远端身份均通过。** 四项原 finding 及自身模板建议已关闭，历史失败与未验范围保持；通用串行、建议性审查、写分配、三领域组合、页面和完整 AC6 仍属后片。本报告这一终结追加不回写原提交对象或模型输入身份，后续状态归档另按其实际提交记账。
