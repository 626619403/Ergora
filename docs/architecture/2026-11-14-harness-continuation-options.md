# F8-H3b：一次 standalone 原生续接的两种 Interface

日期：2026-11-14。调查基线 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`。本文承接 [H3a 接缝](2026-11-14-harness-session-seam.md)、[计划](../plans/2026-11-14-harness-session-readback.md)和[精确交付](../delivery/2026-11-14-harness-session-readback.md)，是下一实现片的设计建议，**不是续接实现或独立验收结论**。本轮只读产品、固定上游源码和已有私有探针；没有安装、import SDK、启动 runtime、模型或网络调用，也没有修改业务项目。

建议首片提供一个明确的 `composition continue-input` 消费者：**对显式授权的新 standalone 只读源调用，以相同材料、权限、后端和原生 home／cwd／session，发送一个新的 prepared prompt，保存一个新的 Ergora 调用记录。每个源仅允许一次续接。** 下层扩展原 `Invocation → AgentBackend.command → processes.run`，由 DeepSeek Adapter／driver 实现原 ID 的 `resume_session → Session.run`。保留 H3a 的归档观察入口；原生历史持久保留不要求常驻 runtime。

## 1. 实际接缝与缺失事实

|现有 Module|已实现的职责；对本片的约束|
|---|---|
|[`agent_runs.run_input / _admit_input / _admission`](../../src/ergora/agent_runs.py)|完整验证 prepared input，检查只读叶、绑定、模式与各祖先权限上限。保存项目修订、input／prompt digest、资料来源及 policy。新续接仍由这里拥有项目归属和调用授权，不能由 driver 自批。|
|[`_run_prepared`](../../src/ergora/agent_runs.py)|新 run、完整 `.input` 副本、新 scope／preflight／审计、新 `.cwd`，再进入 `agents.invoke`。当前总是新调用，不能直接以旧 `.input` 再调用它并宣称续接。|
|[`agents.invoke / Invocation`](../../src/ergora/agents.py)、[`AgentBackend`](../../src/ergora/agent_backends.py)|统一协议目录、命令、原 `processes.run` 和结果 schema 校验。其他 Adapter 的续接必须默认明确拒绝；上层不按厂商名分派第二条调用链。|
|[`deepseek.py`](../../src/ergora/data/drivers/deepseek.py)|当前新建 home／session，固定 `sdk-minimal` patch，保存 request、实际 native prompt、身份、通知和本轮结果。没有 resume 分支，不能把归档读取当作该分支。|
|[`task_mcp.freeze / probe / verify_native / verify_reads`](../../src/ergora/task_mcp.py)|已有固定材料、完整 scope、只含 `list/read`、连接回执及完整附件读取证明。当前 standalone 结果只调用 `verify_native`；`verify_reads` 的产品消费者在原 Executor，不能声称 standalone 已自动验完整附件。|
|[`stage_driver`](../../src/ergora/stage_driver.py)|正式只读阶段也以 `supervised=True` 调用 `run_input`；其记录也可为 `formal_execution_authorized=False`。**这个布尔值不足以识别 standalone。**|
|[`State.agent_runs / file_lock`](../../src/ergora/state.py)|现有 JSON document 可存源合同、lineage、intent 和发送状态；非阻塞文件锁可跨完整调用。无需 native-session 表、第二预算账本或迁移。|

现有源记录没有封存有效 schema、timeout、项目 repo／cwd 的物理身份或 request／patch 摘要。已有 H2 源只能继续作为归档和机制证据；不能事后补字段并宣称当时已冻结。首片应在新源调用的真实消费者上形成并立即消费续接合同。

## 2. 固定 SDK 的输入与回执

以下结论限 DeepSeek SDK／runtime `0.2.2rc2`、固定源码 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` 和现有禁用工具生产者的 `sdk-minimal` patch。已有五副本探针只验零 prompt 的恢复、缺失／占用拒绝、cwd 与写入；未验新输入、MCP 续接、pending inbox 或发送后断连。

- [`DeepSeekHarness.run`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py#L175) 实际是 `start_session(id).run(input)`。`start_session` 只建 lazy handle。已有持久会话必须先 `resume_session(original_id)`；缺失或占用就失败，不退回新建、不重发到新 session。
- [`Session.run`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py#L214) 先订阅 session notifications，再调用 `session/query`。普通输入返回 `messageId`；SDK 等到同 root、匹配该 ID 的 `agent/inbox/spliced`，从该 receipt 起记录，直到之后的 root `idle`。本轮 events 可能含同期活动，不能自动称为仅由新 prompt 引起的全部事件。
- `RunResult` 不单列 receipt ID；`on_notification` 的首个已接收事件就是 SDK 已匹配的 receipt。首片在“单输入、无并发、空 inbox”的限定下核它唯一的 inserted user、完整 content 与实际 native prompt 相同，保存其 ID／seq。无需访问 `_RunActivity`、改 SDK 或重写其等待循环。
- [`session/query`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/src/server.ts#L289) 可执行原生 slash command。[现有编译器](../../src/ergora/workflow_definitions.py) 的非空材料以 `Resource …` 开头；无材料时也先加固定 `Operator supplied task …`。因此**完整校验后的 prepared prompt** 首个非空字符不会是用户 task 的 `/`；driver 追加 schema 不改变此前缀。应验证实际发送文本仍满足此条件，不另开放 raw slash-command 输入。
- 低层公开 [`client.session_prompt`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/client.py#L201) 可直接返回 messageId 并绕过 command routing，但需要自己维护 receipt／idle 等待与结果投影。当前 prepared consumer 无此需要；首片优先保留 `Session.run`。
- [`server.prompt`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/src/server.ts#L262) 在内部生成消息 UUID 后 `followup`，wire 没有调用者提供的幂等消息 ID。通知或返回值也不是刷盘证明：[session append 同步发布、持久化异步缓冲](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/session/src/index.ts#L812)。现有 [checkpoint policy](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/session/session-checkpoint-policy/src/index.ts#L20) 在模型／顶层工具派发前 flush；这不消除 Ergora DB 与 SDK 两方提交之间的崩溃窗口。

### 必须分别保存的字段

|事实|固定载体和字段|
|---|---|
|原 session 身份|canonical 未压缩 JSONL 首行 header：`type="session"`、`version=4`、`id`、`cwd`，与源 `native-identity` 的 `session_id`、`home`、`profile` 及原 cwd 对应；header 没有必填 `origin` 字段，不能凭空要求。|
|新 prompt 入队|JSONL／notification event：`type="agent/inbox/spliced"`，`data.target="next-turn"`，`data.start`，`data.inserted` 中 user 的 `id/role/source/content`；SDK 的匹配键是消息 ID。|
|输入被消费|同一 `agent/inbox/spliced` 的 `removedCount` 与空 `inserted`；之后 surface 的 `user/message` 中正文直接在 `event.data.{id,role,source,content}`，不是 `data.message`。|
|本轮原生终态|JSONL `turn/end` 的 `data.turn` 和 `data.reason.kind`；仅接受该新 receipt 之后的 `completed`，再验本次 result schema／MCP 证据。|
|SDK idle|notification `method="session.status"`，`payload.sessionId` 为原 root、`payload.status="idle"`；**idle 不是 JSONL 事件**，须保存本次通知回执。|

归档完整历史、新 prompt 的 SDK owned interval、resume／shutdown 新增字节分别记账。恢复的种子／修复事件可能仅在 JSONL 中；空通知不代表零写入。

## 3. 两种最小 Interface

两者都先增加明确的 `agent_runs.continue_input(state, project, source_run_id, prepared_input, *, intent_id, timeout)` 消费者。调用者只给项目／源 run／新完整 prepared input／稳定输入意图／新预算，不提交任意 home、session ID、cwd、scope 或 patch。新 input 仍用现有 prepare／verify 流程形成。CLI 是首个入口；HTTP／网页交互可后续沿同一 Module 增加，当前 Web POST 普通 agent-run 不是 composition 执行入口。

|方案|调用者必须知道的 Interface|收益与代价|
|---|---|---|
|**A：原 Invocation 携带可选的已准入源描述符，推荐**|默认仍是新调用。明确续接时传 Adapter 消费的原生来源／冻结合同，沿原 `command/read_result` 和进程 owner；共同入口先检查 Adapter 的续接能力，默认拒绝。源原生身份／归档验证和 per-call native 回执保持在原 Adapter／driver。|调用、schema、取消、预算、MCP 和归档消费者可复用。新增描述符不是用户可自由构造的“万能 session 配置”；它来自上层已核源记录。既有 Adapter 不能忽略该字段并静默新建。|
|B：独立 `AgentBackend.continuation_command(source, request)` 操作|共同 `agents` 调用 Module 明确选择新调用或续接命令，再汇入同一个私有进程／结果消费者。默认续接方法拒绝。|操作名清晰，若将来后端的续接准备与新调用差别很大有价值。当前仍需相同源合同和每次 Invocation；多一套参数／能力检查容易遗漏 schema、MCP 或停止处理。必须提取并共享原消费路径，不能复制 `agents.invoke` 或新建长驻 session runner。|

A 的深度来自“同一次调用的既有结果与进程合同仍有效”；B 的显式性尚不足以抵消新增表面。首片可在原文件内实现少量私有帮助函数，但不新建 `session_manager`、registry、通用事件投影框架、常驻 daemon 或第二调度器。后端可切换继续体现为同模板的新源调用选 Adapter；已有 native session 不能跨后端／模型／版本搬运。

## 4. 新源的先决合同

显式 `run-input --allow-one-continuation` 才形成可消费合同；默认关闭。`run_input(supervised=True, allow_one_continuation=True)` 拒绝，`stage_driver` 保持默认关闭。`run_workspace`、普通 `run_agent`、已有正式阶段和续接子调用都不能作源。不能靠 `formal_execution_authorized=False`、角色名或“只读”猜测授权。

仅对这条真实消费者，在第一次发送前保存下列实际值，完成后核原生证据并标为可续接；失败或合同不完整则不可续接：

1. 同项目的原修订和 repo 身份；源 input 固定位置、完整 digest、composition／根和叶版本、grant、全部祖先资源／来源、权限上限和原有效 policy。保留完整 `.input`，不从今天的活动 Skill／记忆重建材料。
2. 原实际 binding，包括所有有效默认值；有效结果 schema 及其摘要；源 timeout 和一次续接的显式授权。原 `.cwd`、原 home 的固定位置与普通目录物理身份，固定 driver／SDK／profile 及实际 request、patch、native prompt 的身份。schema 先决定再发送，不能发送后从答案猜。
3. 原生源 ID、header／cwd、完整归档的稳定 byte cut／SHA 及源本次 SDK 回执。只接受这条固定生产链产生、原进程已结束、新 receipt 已消费、正常 completed 且无 pending／中断歧义的源。先核清洁单轮形态，不为任意历史重写 inbox／surface／tool 修复器。
4. task-mcp 源的完整 scope、连接与附件读取证据。对显式 opt-in 源和本次续接，复用 `verify_native` 与 `verify_reads`；这是一项需要实现并验收的加强，不能把原 standalone 的连接成功宣传为完整阅读。

“相同冻结材料”不等于“新旧 input digest 相同”。新 task 必然改变 task／prompt／input digest。允许变化仅为完整新 task、由原编译器导出的 prompt／请求摘要和本次 run／scope／审计位置；composition、叶、grant、材料文件及来源、权限、绑定、schema 与项目身份必须一致。输入／材料容量不越原上限；不能省略祖先材料、静默裁剪或把后端压缩历史当完整资料交付。扩大权限、换材料或换后端应新建源。

源 patch 与新 patch 含不同的 per-call scope／audit 路径，其完整 SHA 本就不同。分别保存实际文件；由原 Adapter 只允许这些明确位置差异，比较其余有效插件／工具／路由配置。不能简单比较完整 patch SHA 后拒绝正常续接，也不能忽略整个 patch 让 ambient 或新工具进入。

## 5. 一次续接的所有权与顺序

|顺序|负责的 Module 与必须完成的事实|
|---|---|
|1. 查源、核合同|`agent_runs` 按 project＋source ID 查询；复验新旧完整 input、源 opt-in／未被占用、当前项目修订／repo、原目录及 binding／schema／policy。DeepSeek 原生格式知识留在 Adapter。旧 H2、正式来源、未知源、缺 cwd 或换目录均明确拒绝，不自动 mkdir／relocate。|
|2. 独占和保存 intent|用源 root 身份派生的现有 `file_lock(..., blocking=False)` 跨整个操作；锁内重新读记录。一个短 DB 事务在现有 `agent_runs` 中保存新 child 与源 slot 的 claim／lineage／intent 指纹和显式预算，避免两方各创建一个 child。源原 status／结果／成本不覆盖；不跨网络持有 SQLite 写事务。|
|3. 冻结本次资料|复用 `_run_prepared` 的完整快照检查及 `task_mcp.freeze(new_input, new_run_id, new_scope)`、preflight、新 native audit。新 scope 的 `run_id/input_digest` 正确属于 child；文件 URI／内容 SHA／来源仍须与原授权材料一致。不能用旧 audit、旧进程或旧连接成功替代本次证据。|
|4. 原进程 owner 启动一次 Invocation|在可能启动 driver 前持久记录不可重派的 attempt 状态；`agents.invoke` 创建 child 的新 protocol／stdout／result，进程 cwd 使用原源 cwd。只把已核来源交给原 Adapter。原 `processes.run` 继续拥有 SDK init、resume、prompt、shutdown 和 MCP 后代的停止；不从 CLI／Web 直接调用 SDK。|
|5. 同原 home 恢复再发送|driver 使用原 home／ID／cwd，保持原 runtime cwd；不复制 home、不建替代 ID、不让副本成为权威。先 `resume_session` 取得原生 writer lease，再核恢复后的实际原字节与只允许的恢复后缀；保存恢复活动。仅在确认没有额外输入／pending 或未知变化后，持久记发送开始，再 `Session.run` 发送完整新 native prompt。|
|6. 保存新结果及实际增量|原 Adapter／driver 保存本次 receipt、通知、`native-result` 和字节区间；原业务结果仍经 `agents.validate_result`。`agent_runs` 验本次 scope／连接／完整读取后持久 child 终态；原 owner 完成清理后才释放应用锁。SDK completed 或 reviewer JSON 的 approve 都不写正式 candidate／approval。|

应用锁用于 slot／intent／预算互斥；[原生 lease](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/session/session-persistence-jsonl/src/lease.ts#L1) 用于原日志 writer 排斥，二者不能互代。应用进程崩溃会释放文件锁，但已保存的发送不明记录仍占 slot；原 runtime 可能还活着。不得以锁文件存在／年龄判生死，不删 lock、不抢 writer、不因调用者离线释放未知占用。

### 预算与原进程 owner

续接 timeout 是本次显式授权，保留源已花成本；首片最多“源＋一次 Ergora 调用／一个新 prompt”，**不是最多两次模型 HTTP**。tool loop 可多次请求模型。重复同 intent 不追加预算，unknown 占用不返还，child 不再作源；不宣称 token／费用累计账本或正式 task 的共享 deadline。

推荐 `agent_runs` 在 claim 后用单个 monotonic deadline 扣除本次准备实际耗时；preflight 的等待上限取剩余额度与其原固定上限的较小值，进入原 `processes.run` 时只传剩余额度，不足则不启动 SDK。原有 timeout 只覆盖 `processes.run`，不能原样沿用却宣称覆盖 preflight。同步本地验证／文件 IO 和停止清理的实际尾部要如实记录；deadline 记账不等于任意阻塞 IO 的强制总 wall 上限。严格总 wall 要由原进程 owner 的包围范围实证，不能通过新增预算表或 SDK request timeout 冒充。首片仍用原 Ctrl+C／timeout 停止，独立取消入口和 Windows 原生续接不提前承诺。

### 原历史和增量

将源已封存的稳定末尾记为 `B0`。源限定为 fresh ID、一次受控 prepared prompt：唯一 operator 的 `next-turn` 插入有对应消费，无其他待处理的 queue 插入，末轮 completed；额外 inbox 形态拒绝，不扩展成通用 projection。在原 SDK 持有 writer lease、恢复后且发送前取得 `B1`，核完整 `[0,B0)` 原字节保持为前缀。首片 `[B0,B1)` 只接受零个或一个固定 `session/end-seed`；相同已冻结路由不应新选模型，额外选择／repair／queue 活动均拒绝发送并保留有写恢复事实。新 prompt 之后 SDK receipt→idle 是逻辑结果区间；context manager 退出、原 owner 完成后取得 `B2`，另保存物理 `[B1,B2)`，包括 shutdown 可能追加的内容。三者不混称本轮模型 events。

复用 H3a 的安全固定路径／header／普通文件打开与稳定观察规则，可在原 Adapter 内提取所需私有帮助函数；完整 SHA 只有实际流式遍历后才报告。用 SDK 已匹配的 receipt、其 root events 与 notifications 处理普通输入，不复制上游全量 persistence／surface validator。归档 suffix 仅检查首片实际支持的少量 envelope／类型与原字节前缀，未支持形态明确拒绝；本轮自制的轻量检查不能冒称 SDK 原生格式验证或任意 pending-inbox 恢复。

H3a `output` 当前总按当前 run 的 `.protocol/.cwd` 取归档。child 的 native history 应由 `agent_runs` 沿同项目、受信源 lineage 解析到**原 root protocol／cwd**，再交同一 `archived_history`；本次 stdout／result 仍属 child，返回时明确原 native source run 和 child interval。不能放宽 Adapter 让 `native-identity.home` 指任意路径，也不能为迎合旧 reader 复制 home 或加 symlink。

## 6. 重复输入与崩溃窗口

稳定 `intent_id` 是调用者对这次输入的身份，不是 prompt hash；人可以有意重复相同文字。指纹至少绑定 project、source、完整新 input digest、binding／schema／policy 与本次预算。锁内同 intent＋同指纹只返回同一个已保存 child，**不再启动 SDK／preflight**；同 intent 不同指纹拒绝；已 claim 的源即使换 intent 也拒绝。查重不能依赖 `runs()` 最近 100 条列表。

|窗口|持久事实与后续允许行为|
|---|---|
|claim 前／可证明未进入任何派发|校验失败就没有发送；纠正输入可形成一次新请求。|
|claim 已存，准备或派发前崩溃|重复只读返回原 child；不借“尚无 native-result”自动重跑。首片宁可留下需要检查的占用，也不把恢复准备实现成隐藏重试器。|
|原生 resume 已成功，新 prompt 尚未证明发送|原 archive 可能已有种子／修复；保存 restore interval。不能称零写观察或回滚原历史。|
|发送开始后，receipt／响应／DB 终态之间断连或崩溃|调用 outcome 为 unknown；保留本次 intent／预算／原进程所有者证据。缺 receipt 不证明没入队，已 receipt 不证明模型／工具结果。先查归档增量和 owner，禁止自动再次 `Session.run`。|
|native completed，但 schema／新 MCP 连接／附件读取证据不合格|本次 Ergora 结果拒绝，保留原生事实；不能借源旧结果或旧 audit 提升成功，也不重发。|
|本次结果已保存，客户端没收到|相同 intent 返回原 child 及其结果／未知状态，不新增 run 或预算。|

超时／取消的过程状态与“输入是否被接收／结果是否已知”分开记录。原 SDK 修复出的 `TOOL_OUTCOME_UNKNOWN`／interrupted 并不证明外部效果未发生；首片不升级旧调用 outcome、不续跑正式 attempt、不发起新的候选审批。正式六阶段、Temporal、原 Executor／monitor、candidate 绑定的证据与批准权均保持原归属。

## 7. 首片范围与实现前须满足的证据

优先选择 **task-mcp 的一个含祖先 Skill 附件的 standalone 只读叶**。`text-only` 少了新 scope／连接／读取的实现与成本，适合单独验证上下文带回；但它不提供 Skill 附件，不能验“原父资源仍可完整读取”，也不能代替本片要求的新 MCP scope。选择 task-mcp 直接复用现有真实消费链，避免先交付一个仍缺核心资源合同的旁支。首片只做新源＋一次续接，后续若要多轮 head／累计预算／正式恢复再按真实消费者立片。

实现片至少需要以下独立证据；本调查没有执行这些验证：

1. 新显式 opt-in 源在发送前冻结合同；其成功＋原 owner 退出＋完整 scope 阅读后才开放一次 slot。legacy、正式只读 `stage_driver`、workspace、普通 agent-run、续接 child、未知源和其他后端均拒绝；默认新调用和 H3a 归档行为保持。
2. 固定 SDK 的受控 fixture 实际证明：先 resume 同 ID，再恰好一个 prepared prompt；前轮 user／assistant 内容进入新模型请求，原 ID／header cwd／home 未分叉，原 `[0,B0)` 字节保持，resume 与 prompt／close 区间可重建，新结果不取旧结果。
3. 实际 task-mcp 续接有自己的 run／scope／审计；全量祖先 inline 与附件连续范围读取通过，新增 scope 无额外 URI／工具，拒绝 host path／未授权路径。原源码的 native readiness 与完整阅读证明分别核对。
4. 在 receipt 前／后、结果保存前／后注入断连与崩溃，并发第二调用、重复 intent／冲突指纹、换 intent、cwd／资料／schema／binding／项目变化和 native writer 占用均触发真实拒绝。observer 失败或 receipt 缺失不得自动重发；有写恢复失败仍保留真实增量。
5. 用原进程 owner 核 timeout／Ctrl+C、初始化和恢复／MCP 后代清理、remaining-budget 到期不派发；重启后的 unknown 仍占用。后续一次有界真实模型续接和产品包／相关回归、自身模板与新的 fresh-context 需求／维护性评审分别记在实现片交付；受控 fixture 或本设计不能替代它们。

首片先决条件不是“归档已能读”或“SDK 方法存在”，而是上述新源授权／合同消费者、按 intent 的一次派发、原 owner 停止、同原 session 的精确输入和增量证据能够同时成立。当前 H3b 仍开放。
