# F4.3d 精确候选导出页面独立审查

日期：2026-11-04。审查者：`/root/task_export_console_review`，本片新建 fresh-context 独立上下文。遵循仓库 [AGENTS.md](../../AGENTS.md)、maintainable-project-delivery 的 independent-review brief 与 review-pr；先检查原始需求、diff 和相邻调用，再读取[作者交付记录](2026-11-04-task-export-console.md)。本轮只执行必要只读检查并写本报告，没有修改生产、测试或其他文档，没有安装、构建、提交、推送或重放原生写操作。

## 结论

- **需求符合性：本地审查通过，范围内无 findings。** 新导出固定明确查询的闭合 REVIEW_READY 原 run 和完整候选；先读原记录，只有 `not_recorded` 提供新分支确认。原意图恢复、未知结果、历史回执及迟到响应处理符合本片合同，六阶段与候选/租约证据保持。
- **可维护性：本地审查通过，范围内无 findings。** 归属、实际消费者、必要守卫、读取/渲染成本及测试/CI 冗余均已检查，没有需要增加通用状态机或新模块的依据。
- **交付尚未终结。** D 当前未提交；精确提交归档、正常远端推送、该精确提交的双 OS 必要 CI 步骤和同片终结复核仍待完成。前置 C2 的 SSH publickey 认证失败和远端精确 CI 缺口保持，不能由本报告或先前 C1 CI 代替。本结论不表示完整 F4、F5 或 G0 完成。

## 精确范围与身份

基线及本轮 HEAD 均为 `401bacb28cf99e121357860901c4d95332417dae`，分支 `refactor/architecture-foundations`；审查对象是其上的未提交工作树。

生产差异仅为 [tasks.js](../../src/ergora/data/console/tasks.js) 新增 93 行和 [app.js](../../src/ergora/data/console/app.js) 帮助文案一行。已检查 README、USAGE、PLAN、current architecture、all-in-one 计划、formal-task-console 入口及新 export-console 交付记录。两份 reconciliation-console 记录只有前片提交/发行/认证状态补记，不把它们当 D 行为证据。审查期间 all-in-one/formal-task-console 又补 F4.4a1/a2/b/c 的未来切片计划，已看原始差异；明确尚未实现，不纳入 D 的运行验收，也不在此批准未来实现。

独立非 editable wheel SHA256 为 `2d1bbafb9b3d85e8b5623fe45405cc15ec3451586b9d4d2280372086f283e41b`。审查者直接复算当前源码、实际 wheel、两份安装的全部 348 资源及安装 direct_url，逐项相等；283 冻结 reference 文件另与精确基线 `git show` 逐项相等。生产源码摘要为：

|资源|SHA256|
|---|---|
|`data/console/tasks.js`|`af238c2f22c4b47ddc433d74ceaf810605f02c755f3a8688cebd6f4a138ea2a7`|
|`data/console/app.js`|`cf570b7f285ae6968f75430d4d123d0445d4502914927d69ecb49dbeb9294af5`|

Python、测试、CI、依赖及冻结参考内容均无本片变更。相邻调用检查包括 [tasks.py](../../src/ergora/tasks.py)、[web.py](../../src/ergora/web.py)、[reference.py](../../src/ergora/reference.py)、[reference_task_export.py](../../src/ergora/reference_task_export.py)、原 creation/submission、原生 agent ingress/IngressLeases，以及 api/ui/app 的请求、表单、modal 和页面替换生命周期。

## 需求核对

1. `tasks.js:930` 仅在 `terminal && runtime_status === queried && outcome.status === REVIEW_READY` 提供新导出入口，以回包中的完整 `run_id/candidate_sha` 构造闭包；`687–711` 另核详情与 run 代际，GET 成功且 `not_recorded` 后才出现分支输入。浏览器不重复 Git 名称或候选格式规则；原 `tasks.export`、Web payload 和 native outcome 校验负责最终拒绝错误 run、短 SHA、旧 revision 或非精确 REVIEW_READY 结果。
2. `tasks.js:893` 的任务本地记录入口不先查运行，`759–768` 只调用原 GET `/export`。读取失败不提供写确认，单独的 `not_recorded` 入口也不能创建新导出。GET 的原服务实现不连接 Temporal、不核目标分支当前 OID，不释放租约；它仍会验证本地创建/提交、登记配置和 Git 根，并在已有意图时执行 Git 分支语法校验，不能把“本地记录读取”理解成没有进程或文件成本。
3. `704–749` 分清 `prepared` 可能首次创建原目标与 `unknown` 只核原分支。恢复正文只有原 `intent_sha256` 及 revision/confirm/timeout，没有可编辑 repo/run/candidate/branch。原 `reference_task_export.reconcile` 在 `branch_not_found` 返回 unknown，不 fetch 或创建 ref；`exported` 只展示历史回执，无导出/恢复表单，正文说明当前 ref 仍需复验。租约释放、checkout、merge、开发成功分别显示，没有把 `execution_success: null` 当成功。
4. `700–702` 的页面连接、详情代际、内容连接、dialog open、候选 run 代际与读取序号分别覆盖切页面/项目、切任务、替换或关闭 dialog、编辑/重新查询 run、逆序读取。确认回调再次核 `current(reading)`；写开始同步设置 `writing`、禁用读取并移除确认表单，`read` 也检查写锁。受控记录/写回包不能复活旧确认，finally 只恢复当前活跃 dialog 的读取按钮。没有自动 retry、轮询、resume 或新 export ID。
5. Git 条件 ref 创建、完整原 outcome 校验、原 claim 释放及 native export 回执仍由原所有者完成。原 `IngressLeases.release` 以原 spec/claim 与 canonical outcome SHA 约束释放和幂等，本片没有绕过它、改写 workflow outcome 或把历史导出当人工合入成功。

## 结构、性能与验证成本

`exportDialog` 的两个生产入口都在 `tasks.js` 同一详情内；新增私有 `show/read/active/current` 只被这个工作区的初始读取、重读、确认回调和显示生命周期消费，没有跨生产文件的复用消费者。这些局部函数封装同一任务详情的完整交互，保留在现有所有者中合理；和批准/取消/对账的外形相似并不构成提取通用状态机的依据。`show` 只渲染、`read` 只读取，正式状态及原意图继续由已有服务拥有。

新增条件均有可达场景：外部 API 状态决定可用动作；记录失败缺少可确认身份；用户可在请求未完成时关闭/切换/编辑或连续读取；写操作可能成功后丢回复。相应守卫位于拥有 DOM/请求生命周期的边界，没有新增与此操作无关的断言或复制后端 Git/租约验证。

新增 GET 只在显式打开/重读时发出，一次读取一个任务的本地合同/创建与提交记录及至多一组 export 记录，不扫描任务列表或 history，不自动附加到任务详情初始读取。它有专用 Python 进程启动、合同验证与 Git 根/分支格式检查成本；前端仅按固定字段和完整原记录渲染一次，不累积 DOM。审查者对现有本片安装服务各做一次明确 GET：治理 `200/exported/not_queried` 为 **3.057 秒、647 字节**，大型变更为 **1.590 秒、622 字节**，意图 SHA 与原回执一致。两次串行本机样本没有冷暖/负载控制，只证明此环境下的实际读取成本，不证明通用延迟、吞吐、大记录规模或性能提升。174 页面请求的整段旅程时间亦不能替代单 API 性能测量。

没有新增测试文件、测试框架或 CI job。已有架构 8 项只保护 Python 导入边界，不能证明 JS 行为；浏览器四段分别验证状态/正文、迟到隔离、真实一次副作用及最终读取，有不同合同目的。受控两模板检查虽覆盖同一界面，也同时核实际原候选/运行来源，不构成需删减的重型重复套件。未因仅前端与文案变化再跑完整 Python 重型套件，也没有为了审查重复真实导出；精确 CI 仍应按原正常配置取得。

## 独立核验与证据边界

本片私有证据在 `.ergora/checks/f4-task-export-console/`，截图在 `output/playwright/f4d-*`，不进入发行资源。

- **源码/发行静态检查：** 审查者直接执行 `git diff --check 401bacb28cf99e121357860901c4d95332417dae` exit0；13 个 JS 模块逐个 `node --input-type=module --check` exit0；348 资源/两安装/283 冻结的独立复算通过。已核 package/build/install/base-SDK-absence、final-resource-syntax 和 wheel-architecture 的原命令、退出码及日志；原有架构检查实际为 8 passed。构建 18.23 秒与含建 venv/两安装/核验的整段 39.68 秒范围分别成立，没有混记。
- **浏览器证据链：** 四段保存脚本与 command.json 内实际传入脚本相等；CLI 原始 `### Result` 与各 result.json 逐 JSON 相等，保存退出码均为 0。controlled **36 请求/8 拦截 POST**、boundaries **34/4 拦截**、native **76/2 真实**、readback-v2 **28/0**，合 **174/14，其中 12 拦截、2 真实，零 pageerror**。前两段的每个 POST 均有对应 fixture；真实段每任务只转发一次 `/export`，原始 200/exported 后治理回复故意 abort，再 reload/重复 GET/清除任务与 run 选择恢复同一回执，没有 resume 或重发 export。
- **原文件、Git 与 ledger：** 审查者独立读取当前快照覆盖的 tasks/requests/receipts/artifacts/ergora/approvals/fences 七类目录，131 原文件摘要全等，新增集合精确为两个任务各 intent/attempt/result/native export 共 8 文件。两个业务 repo 的原 HEAD、symbolic HEAD、全部原 ref、工作区文件/状态和 worktree 列表全等，新增 ref 分别精确指向原候选。SQLite 使用显式 `mode=ro`/query_only 读取，读取前后 DB/WAL 摘要保持；3 个 claim/0 active，两个正常任务只更改 released_at/evidence_digest，原取消 claim 与其余字段不变。释放证据分别为原 outcome SHA `e971b6cd88e4bda0ec0eca9fe1e26e70ca8f5f2164c2aaafd41b78496d86622d` 和 `73a8b52c2d2ac1398580e47eef3cefcb2938558052a4165a64e0b2ebac707add`。
- **实时原运行：** 在已有 SDK/服务上另做只读核验，三条完整 history 与保存的 before JSON 逐项相等，事件数仍 **329/348/112**，原 outcome 分别仍 **REVIEW_READY/REVIEW_READY/CANCEL_UNCONFIRMED**；Running workflow 列表为空。没有 start/signal/model 调用。上述运行核验不修改 native 文件或 ledger。
- **视觉与失败保留：** 审查者实际查看治理 exported 顶部、租约/checkout/merge/开发未知事实和大型变更候选的 390px 截图，长身份可换行、无横向溢出。原 readback 在 390px 点击既有 CSS 隐藏的 help 按钮，CLI/exit1 保留；v2 只改为桌面打开帮助后检查 390px 内容，没有产品改动或第二次真实写。本报告不宣称窄屏 help 入口已支持。
- **文档静态范围：** 已核 10:44 UTC 原命令 exit0、9 份 Markdown/322 个本地链接锚点/27 条 README parser 命令；首次核对时 9 份摘要均与保存记录一致。随后作者补 F4.4 未来计划，本报告也是新文件，所以该旧记录不覆盖最终全量文档；作者须在最终记录落盘后重核并保存新身份。

真实运行证据仅覆盖两个既有原候选各一次成功导出和历史回执恢复；prepared/unknown/branch_not_found、读取失败、旧 revision 与迟到异常主要由受控浏览器验证，并通过相邻后端源码核对。本轮未实际断开 Temporal、篡改/删除导出分支、重放 unknown native 恢复、重跑浏览器或完整 Python 套件，没有把这些未执行项记为通过。

当前无阻塞本地源码 findings。下一步为最终文档检查、D 精确提交/归档资源核对，以及认证恢复后的正常推送、实时远端 SHA、精确双 OS 必要 CI 和同片终结复核；下一 F4.4 实现切片需另启新审查上下文。
