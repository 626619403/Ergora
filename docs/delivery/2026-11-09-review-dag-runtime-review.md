# AC4.3b 只读审查 DAG 运行独立评审

日期：2026-11-09。评审者以全新上下文独立读取原始要求、固定差异及邻近生产调用者；另以两个全新上下文分别检查 Spec 和 Standards。依据根 `AGENTS.md`、AIHERO 的 `code-review` / `codebase-design` 与 `maintainable-project-delivery` 独立评审说明。仅写本报告和授权的离线检查目录，未修改源码、依赖或 Git 身份，未启动模型或服务。

**本地最终门禁：Spec、Standards 均通过，RD-1 已关闭。** 下文保留初审失败历史，并追加同一片的修正包与原件复核。R2 包、服务旅程、离线交接、自己的模型补证复审及完整 34 文件范围均已核验；普通提交后的同一精确候选、自己的必要 CI 与明确 HTTPS 远端身份仍待另核，尚不宣布最终交付通过。

## 固定范围与身份

基线为 `e9b682c4be4f19aa11aca4717a7f6d86050278ed`，审查时 `HEAD` 与基线相同，分支为 `refactor/architecture-foundations`。完整未提交范围含新增文件，来源为 `.ergora/checks/ac4-dag-runtime/review-scope.diff` 和 `review-scope.json`，不是只比较 tracked diff。

- 初始范围 JSON 的 SHA256：`cd82724d3fa06aca75bc4bca99814e229020d33027cc5f96e9b2ae77b2bd067b`。
- 初始完整 diff 的 SHA256：`545d1c5c9453480c5811a5a9cd80d040347654fad54c30f32cb11ee834ed90ba`。
- 共 19 文件：`docs/PLAN.md`；前片合同交付及独立记录各一份；本片交付记录；AC 总计划；`examples/composition/serial-review/` 两文件；任务定义 v2 schema；`reference_executor`、`reference_inputs`、`reference_task_creation`、`reference_workflows`、`review_dags`、`task_envelopes`、`tasks` 七个生产 Python 文件；原验收 fixture、新 DAG fixture 和两个 DAG 测试文件。逐文件 SHA 以该固定 JSON 为准。

原始规格为[已审端口合同](../plans/2026-11-09-review-dag-contract.md)，上层请求仍要求有界多专家、独立会话和后端选择、嵌套串并行显式汇合、祖先材料完整读取及权限收窄。本片只接只读 reviewer；原六阶段、owner 批准、候选与证据身份、attempt-before-send、未知恢复、Temporal / monitor 及唯一原账本和 283 冻结文件必须保持。

初审期间作者继续增加测试和验收记录。后来出现的测试扩展、三个使用手册及无行为 import 清理已收到说明，但不自动并入上述固定身份。后续需用新的完整范围和包身份复核。

## Spec（初审历史）

**结论：暂不能通过。** 原端口、职责和调度主路径未发现其他已证实违约；RD-1 违反了“没有显式新协议时保持旧运行行为”的兼容要求。仍缺少的验收另列，不当成已证实实现缺陷。

### RD-1：旧 v2 / v3 的 Executor 新增了未声明的 Temporal SDK 运行依赖（P2，阻塞）

位置：[reference_executor.py](../../src/ergora/reference_executor.py) 初始候选第 312 行；[reference_inputs.py](../../src/ergora/reference_inputs.py) 第 99 / 134 行；[reference_workflows.py](../../src/ergora/reference_workflows.py) 第 10 行。

可达场景：控制端只安装基础 Ergora，原参考安装的 `.venv` 提供完整 worker / Temporal SDK。该布局下，原 Executor 用标准库 FileAdapter 读取已经发布的 v2 / v3 审查材料。新代码把所有版本都改为 `execution_input(...).adapter(...)`；v2 / v3 的 adapter 导入 `reference_workflows`，继而强制导入控制端的 `temporalio`。托管入口也可达到此布局：[services.py](../../src/ergora/services.py) 第 139 行用控制端 `sys.executable` 启动 Executor，而 worker 沿 [reference.py](../../src/ergora/reference.py) 第 115 行使用参考安装的 Python。

后果：合法旧任务在 review 阶段抛 `ModuleNotFoundError`。该异常不在 `execute()` / `process()` 的捕获集合中；scanner 记拒绝请求，不能发布该 job 的终态回执，工作流最终停止或进入清理未确认。固定合同要求保留 v1 / v2 / v3 行为，[身份规则](../architecture/contracts-and-identities.md) 也明确 Temporal 仍是可选依赖。

独立反例：`.ergora/checks/ac4-dag-runtime/independent/no-sdk-adapter.py` 仅阻断 `temporalio` 导入，未卸载或安装依赖；原 `FileAdapter(config)` 成功，同一配置调用 v2 / v3 `.adapter(config)` 均抛 `ModuleNotFoundError`。原始 JSON 为同目录 `no-sdk-adapter.json`。Standards 评审者另以独立只读探针得到相同结果。

最小修正：旧版本保留原 FileAdapter，通过原 `WorkflowInput.request_root` 选择请求根；把实际需要共享的可信意见读取放在不导入 SDK 的原生所有者，由 Activities 和 Executor 两处直接消费。不用增加旧任务必装依赖来替代兼容修复。作者已接受该问题，计划修正后建立 R2 包；R1 结果保留原候选身份，不能证明修正。

## Standards（初审历史）

**结论：不通过，RD-1 为本轴唯一实证阻塞。** 独立 Standards 评审将其定为 P1；Spec 轴按受影响的可选依赖部署范围定为 P2，保留各自判断。SDK 只应由实际使用 SDK 的原生操作加载；Executor 的原件读取不需要 Workflow 装饰器或 SDK。该问题同时是兼容缺陷与依赖位置问题，沿用 RD-1 编号。

`review_dags` 有 `task_envelopes`、原 Workflow 和原 Executor 三处实际消费者，计算原冻结实例的先后与端口投影，没有持久化第二图或第二运行账本。它复用标准库 `TopologicalSorter`；共享端口以稳定地址去重，未递归展开重复 join。原意见校验的提取保留 v3 的字段、候选、原 FAILED / SUCCEEDED 状态及严格结果摘要合同；新路由类的薄方法是既有版本注册所需 Interface，没有据此建议增加通用插件层。

测试复用原创建与执行 fixture，没有新增 CI 平行入口。纯端口检查覆盖外部来源、未知端口、漏叶、具名嵌套及共享 join；运行检查跨越真实 Executor 的 prompt / 原件 seam。未发现仅复刻实现而需删除的新增测试。图投影存在跨调用重复计算，可在实际大图测量证明必要时优化；当前共享 join 检查和离线测量没有形成性能阻塞证据，不要求为了本片加入缓存或另一份图状态。

## 初审已核检查与边界

|证据|本次观察|可以证明的范围|
|---|---|---|
|`b2.log`|36 passed / 73.72 秒|B1 与原建议审查源码检查，不代表新包或模型质量|
|`b3.log`|19 passed / 6 failed / 104.44 秒|原失败保留；失败为 fixture 同时启动 scanner 的单例 flock 冲突|
|`b3-executor-r2.log`|7 passed / 85.43 秒|改为 scanner 原 process handler 后，受影响 Executor 用例通过|
|`b4-progress.log`|1 passed / 3.38 秒|独立慢分支仍运行时，已完成前驱的后继可以推进|
|`independent/ports.log`|独立运行 9 passed / 1.99 秒|从源码导入的纯端口算法检查，未启动服务或模型|
|`independent/no-sdk-adapter.json`|旧 FileAdapter 成功，v2 / v3 新路径缺 SDK 失败|RD-1 的可选依赖反例|

已追踪原提交 `lookup_run` / memo 归属检查、原 history 的 submit 活动选择、版本化请求根、原 FileAdapter / claim 及产物读取。前驱内容进入实际输入前再次核来源、candidate、approved plan、收据、backend / session 与原 claim；未新增逐叶 Temporal 查询。上述源码核查不能代替指定 run 的真实来源和恢复旅程。

## 初审缺失验收

以下是初审时尚未终结的证据，不是从测试缺失推断的 bug：

1. RD-1 修正的完整源码身份、无 SDK 回归及受影响执行链的新非 editable 包复核。
2. 同 admission / candidate 的裸 run 不能取得正式归属，以及原 submission 确认后的同 job / context 幂等恢复。
3. 真实 worker 停启、并行祖先限额、取消竞态、清理 unknown 与原 ID 对账；原请求、claim、调用次数和已完成活动保持。
4. 本片最终包 / 安装身份及 283 冻结文件、公开 CLI / Supervisor / Temporal、原 evidence / 离线 handoff、新 v4 和旧 v1 / v2 / v3 history 重放、进程清理。
5. 本片自己的真实模板审查、最终完整范围独立复核，以及普通交付后的自己的必要 CI 和精确远端身份。

初审计数：Spec 1 项实证兼容 finding；Standards 1 项相同依赖 finding；其余项属于未终结验收。RD-1 关闭且最终验收原件齐备后，才能给本片完整通过结论。

## R2 固定包复审

修正候选的完整范围为 `.ergora/checks/ac4-dag-runtime/r2/review-scope.json` / `.diff`，初次固定时含 25 文件，SHA256 分别为 `5d2ac7aa2ce2a45d26db948a9c97ca739cf296b3148a6e5fb1db36d2f2dffed4` / `327b983913cf5d71378a6377f2901d80c5358a3694cfd10d3a1455bd9e2b5fb0`。评审者核对全部文件与记录相同；后续状态文档、补充测试及公开证据的变更需由最终 scope 单独收口。R2 的生产代码未因补证再次修改。

最终完整 34 文件固定在 `r2/final-review-scope.json` / `.diff`，SHA256 为 `b8600b67567ac9fd6f46e680549ece54916971cd5bbbb2486c693cc0e1bbb038` / `7cfdb321ab27f2c7c107e43e6deaaf4612dcf3b3dde4f1c6114671e9db0ce8ca`。独立核对全部文件和当前完整 tracked / new 清单一致；相对上述 R2 仅增加八份公开证据和原架构门禁登记，并更新计划、交付及评审状态。两位分轴评审者完成同一增量终核，未发现新 finding；生产源码保持已审身份。当前追加的最终门禁正文属于该固定范围后的评审记账，不冒称已存在于先前 scope。

独立比较源码、wheel 与非 editable 安装后的全部 372 文件，以及基线 Git 对象中的 283 冻结文件，均逐字节一致。包 SHA256 为 `1d266efb0329f267383ba3abc295c7bf6421f1c3a8012a2d220dd7dae05a629b`；独立结果为 `.ergora/checks/ac4-dag-runtime/independent/r2-identities.json`。可随仓库查阅的包记录见[package R2](evidence/2026-11-09-ac4-dag-package-r2.json)。

### RD-1 关闭

Executor 现保留原 `FileAdapter`，仅以原 `WorkflowInput.request_root` 选择版本化请求目录；原生可信意见读取归属新增 SDK-free `reference_review_opinions`，Activities 与 Executor 两处直接消费。独立 AST 比较确认提取后的 22 个语句在把原 `self.adapter` 归一为参数后与基线 v3 意见解析一致；原活动仍把相同 `ContractViolation` 包装成原非重试错误。Spec / Standards 两位评审者均确认修正关闭原问题，未发现新阻塞。

回归 `test_old_review_executors_keep_their_sdk_free_terminal_receipt_contract[2/3]` 在实际 R1 安装包中 **2 failed / 20.29 秒**，修正源码中 **2 passed / 23.99 秒**，并已包含在 R2 安装包的 **259 passed / 604.60 秒**全组中。该检查在执行过程中阻断 worker SDK 导入，覆盖原 Executor 及终态回执；不是把需要 SDK 的 adapter factory 自身改成无 SDK。原反例仍保留其原含义。日志为 `rd1-original.log`、`rd1.log` 和 `r2/packaged-tests.log`。

### Spec 复审

**源码与已完成的本地验收通过；尚缺的交付证据另列。** 四条真实公开 CLI / Supervisor / Temporal / scanner 旅程使用上述安装包及确定性后端协议 fixture，耗时 464.97 秒，未把 fixture 当作模型质量证据。原件摘要见[journey R2](evidence/2026-11-09-ac4-dag-journey-r2.json)。

|原公开任务|原 run ID|结果与实际调用|
|---|---|---|
|`dag-resumed-v4-public`|`01a1bf46-93aa-7da4-bba3-72b276fa03ec`|REVIEW_READY；8 个 job、3 次 reviewer 调用；原 advisory request-changes 保持 FAILED，两条 required 后继成功|
|`dag-required-v4-public`|`01a1bf48-6e51-7362-8f1f-bff778522ede`|BLOCKED；8 个 job、3 次 reviewer 调用；required 意见为 request-changes|
|`dag-operational-v4-public`|`01a1bf4a-4088-738a-ada9-7dcb1ca240a9`|BLOCKED；6 个 job、1 次 reviewer 调用；失败进程没有可信意见，未运行后继|
|`dag-cancelled-v4-public`|`01a1bf4b-d90f-7602-b018-4b50a321e9a9`|原 CANCEL_UNCONFIRMED；6 个 job、1 次 reviewer 调用；首审 CANCELLED，未运行后继；外部对账释放原 lease，保留原 outcome|

worker 停启旅程保留前六份原请求；worker 停止时首审完成，没有额外模型调用，恢复后才发出两个后继。同原 creation 重复 `task start` 返回原 submission。四条新 history 和九条旧 v1 / 单 v2 / 并行 v2 / v3 成功、拒绝、运行失败、取消 history 均由当前安装包重放；旧记录见[legacy replay R2](evidence/2026-11-09-ac4-dag-legacy-replay-r2.json)。正常 REVIEW_READY 没有 fence，因此 `external_confirmed=false`，同时 unresolved / unexpected 为零；这是原状态语义，未据此报缺陷。

评审者没有重跑服务，而是以只读 SQLite、原文件字节及离线 handoff verifier 独立核对留存原件：**28 条 request / receipt / 原 claim 链、126 份 receipt 产物、32 份完整结构祖先资源正文、8 次完整 prompt 至真实 backend stdin、4 份后继完整 producer 材料、4 条 creation→submission→原 history memo 链**。所有 job / context SHA、candidate、approved plan、producer 原 FAILED 状态、receipt 摘要、原 session、实际产物与下游正文均相符；结构资源与任务后缀逐字节完整，权限仍只读。四份 handoff 的原 SHA 与离线复验均通过。独立脚本与结果为 `independent/r2-raw-chain.py` / `.json` / `.log`；历史先后次序由原旅程的实际停启断言证明，不从最终文件反推。

额外 ownership 回归 **3 passed / 24.50 秒**：保存的创建意图不能删除显式协议；已有原提交 attempt 而无匹配原 memo 的同 admission run 不能取得正式归属；匹配 memo 仅恢复原 run、不再次 start。它们走原 `_Submission` / `VerifiedSpecClient` 与 SDK Client fixture，**没有声称是真 Temporal 裸 run 旅程**。四个真旅程另已核实实际提交 memo 的完整归属链。并行祖先限额、独立慢分支推进和嵌套端口覆盖来自原 runtime / ports 测试，服务旅程覆盖串行首审与两个并行后继。

### Standards 复审

**通过，未发现剩余实证标准阻塞。** 原静态架构门禁在首次对 R2 安装包执行时有两处登记失败：`task_envelopes` 新增 foundation `review_dags` 依赖、新原生 reader 未登记在 reference 边界。作者在原门禁中明确准许 `task_envelopes→review_dags`，同时新增 `review_dags` 的零本地依赖与两者仅标准库限制，并登记 `reference_review_opinions`；没有放开应用层通用依赖。修后原安装包门禁 **11 passed / 0.20 秒**，差异已读。

原三处消费者、唯一图与账本归属及共享 join 设计结论不变。重复派生图是非阻塞性能建议：122 实例 / 40 叶的离线投影测量约 23.7 毫秒，未形成运行性能缺陷；超出完整 stage 输入预算的极大图不能当作可达运行基准。无需为本片新增缓存或另一个图状态。原件清理观察记录了 Supervisor 后代及已见重归属进程的 **128 个 PID / starttime，最终 0 存活**，端口关闭；采样不等于证明观察到了每一个极短生命周期进程。

### 模型审查与当前缺口

本片自己的实际 `structure-review` / task-mcp 首次 Codex fallback 调用成功结束，但 decision 为 **request-changes**，不是通过。它没有提出已确认的阻塞源码缺陷；要求补齐未完成的最终 R2 验收，以及 schema、原 submission / memo / evidence / handoff 所有者后再审。403690 字节源附件完整分页读取至 EOF。身份与原结果分别保留在[self-review R1 identity](evidence/2026-11-09-ac4-dag-self-review-r1-identity.json)、[self-review R1 result](evidence/2026-11-09-ac4-dag-self-review-r1-result.json)，原结果与原文件逐字节相同，不覆盖失败历史。

同一生产包的补证复审 run `60a9d429f6bb48d1a4c1dbacbab1fc74` 使用已授权 Codex `gpt-6.1-sol` / high，**357.75 秒 / succeeded / exit 0 / approve**。身份与原结果见[self-review R2 identity](evidence/2026-11-09-ac4-dag-self-review-r2-identity.json)、[self-review R2 result](evidence/2026-11-09-ac4-dag-self-review-r2-result.json)，结果 SHA256 为 `8666ff39d27b94e889996111f20f4633f4975d4389bb21c3dcb8cc6679797a5e`。评审者独立核 saved run / result / input / stdin，37 份原源码 SHA 与附件完整正文、6 份验收原件均相符；从实际 native 流重组 **19 个连续成功页面、587523 字节至 next_offset=null**，逐字节等于附件，SHA256 为 `8de8b9851b2f98a58d28167708786f12e7e71a56e63c38a29b2bdc2f1f3dcbb4`。原先错误 URI 的一次 read 失败保留，随后读取完整。首审 13 页也独立复验一致，见[公开读取记录](evidence/2026-11-09-ac4-dag-self-review-read-audit.json)；独立原件为 `independent/r2-model-chain.json` 和 `independent/r2-final-scope-audit.json`。这证明实际字节交付，不声称模型理解、错误独立或 Claude 成功；模型没有执行本片测试或重放。

评审追加后独立执行现有静态检查：**11 份 Markdown、208 个本地链接 / 锚点、82 条现有 CLI parser** 通过，`git diff --check` 通过；原件为 `independent/static-documents.json` / `.log`。这里只检查文档与参数解析，不替代应用测试。

**本地最终计数：RD-1 已关闭；Spec 0 未解决实证源码 finding，Standards 0 未解决实证标准 finding；剩余本地阻塞为 0。** 八份公开证据与保留的包、旅程、日志、模型原结果及源码身份均核对一致，模型保留的性能建议仍非阻塞。剩余仅为普通提交后该精确候选、自己的必要 CI 与明确 HTTPS 远端身份；这些交付门禁不包含在本地通过结论中。
