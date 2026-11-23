# 读取待批计划材料

简体中文 · [English](../../development/design-and-approval.md) · [文档目录](../../README.zh-CN.md)

仅适用于统一创建且已保存原提交回执的任务，运行环境与提交入口相同。先用`task status --run-id RUN_ID`查询原状态，取得`AWAITING_PLAN_APPROVAL`的实际plan SHA，再读取对应材料：

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 PLAN_SHA --timeout 20
```

`plan`核对原提交run/spec/memo、当前待批phase与所选plan SHA，从原history定位plan job并核对请求envelope和已接受receipt。plan SHA是整个回执的规范JSON摘要，不是execution-plan文件摘要。`materials`按冻结profile返回完整UTF-8文本及各自的`name/sha256/bytes`；两个开发模板均提供execution-plan、ownership-map和rollback-plan。响应同时保留原run、请求、profile、回执及history事件身份，供审阅工作单元、范围、风险与回退措施。

每份材料最多256 KiB，总JSON响应最多1 MiB；缺材料、摘要不符、非UTF-8、路径不安全或超限时拒绝读取，不截断成貌似完整的计划。`--timeout`为1–60秒，父进程另留5秒启动/回收，本地预检另计。此操作不持控制库写锁、不创建decision或owner回执、不发信号。返回值是读取时快照；批准前仍由服务端再次核对原运行当前状态。

API：GET `.../tasks/TASK_ID/plan?run_id=RUN_ID&plan_sha256=PLAN_SHA&timeout=20`。网页“审阅计划与批准”使用同一入口。网络失败或计划已不再待批时，沿原ID重新查询status，不创建替代任务。

## 在原计划审批时补充工作单元的实施方法

当前带预算的原生任务可在初次计划审批时为已冻结的工作单元补充实施方法。将原单元 ID 映射到方法文本，例如 `{"parse":"先复用已有解析器，再分配内存。"}`。每段文本最多 2,048 个 UTF-8 字节，规范化映射合计最多 8,192 字节。补充方法沿用原目标、验收标准、检查、分配、权限、范围和预算。对这些字段的实质性修订走关联后续任务。

```bash
ergora task plan my-project TASK_ID --run-id RUN_ID --plan-sha256 ORIGINAL_PLAN_SHA \
  --method-addendum methods.json
ergora task approve my-project TASK_ID --decision-id owner-method --revision REVISION --run-id RUN_ID \
  --original-plan-sha256 ORIGINAL_PLAN_SHA --plan-sha256 APPROVAL_PLAN_SHA \
  --method-addendum methods.json --confirm
```

预览读取原计划和完整方法，并返回 `approval_plan_sha256`。审批时使用这个摘要，绑定原计划回执、原运行和精确方法文本。必须在首个审批回执进入等待或被使用前提交。原工作流在首次派发前按原历史处理审批、取消和截止时间的竞争。

审批送达不确定时，沿用决定 ID，使用 `task approval` 或 `task resume-approve` 对账。工作单元只读取自己的方法。审查者读取完整补充文档、原计划和绑定同一候选的证据。使用支持补充方法的 Worker 和 Executor 执行已审批的工作。提高待派发单元优先级时，使用状态返回的复合审批摘要。证据索引与后续修订检查点会核对原所有者回执，再报告已生效的复合摘要。回执丢失或变化时，审批证据标记为不完整。

## 保存完整设计来源与原答复

**已发布开发候选：** 本节对应源码 `2ae107b`，已包含于核远端一致的公开提交 `9f3e693498834f071cf20d0f25c18555554765f1`。它自己的Portability run `43867345323`已终态8/8 success，含既有Windows检查；本source存取片发布／CI门闭合，未继承e5结果。下述source命令仍须Linux／WSL2，不新增Windows原生source支持。旧安装可能没有这些命令。本节仅为inspection-only存取，不是新增的默认设计／批准流程。

使用Linux／WSL2、原项目登记的native解释器／运行时、匹配SDK和原creation／submission／state文件。任务须由统一入口创建并已可核验提交，真实pending plan的已接受原回执中已有有效 `design-packet` artifact。**本片没有添加默认seed producer**，普通模板创建本身不生成该原件；缺packet时停止，不得伪造artifact、编辑旧receipt或降级登记绕准入。首次inspection／anchor建立实际查询原在线run、history与receipt，不能由caller提供可信preflight。

```bash
ergora task design inspect my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --timeout 20 > design-current.json
ergora project show my-project
```

`SEED_PLAN_SHA`始终为原plan回执的规范SHA，不是报告文件或后继packet SHA。完整读取 `design.source_journal`：`source_chain_sha256`为下一次的 `PARENT_SHA`，`current_packet`是应复制到独立本地next-revision草稿的完整packet。保留所有未修改字段及原task／request／profile／admission／manifest／seed-job／design-profile／声明owner绑定与work-unit映射；publish要求packet revision+1、`previous_packet_sha256`等于当前packet规范SHA。本指南不提供缩略packet模板，使用完整[packet schema](../../../src/ergora/data/schemas/task-design-v1.json)及[source提交schema](../../../src/ergora/data/schemas/task-design-source-v1.json)。

准备 `publish-round-1.json`：`schema_version:1`、**完整**next `packet`对象，以及为每个 `access:full`来源提供完整descriptor的 `bodies`。每项含 `path`、`sha256`、`bytes`、`media_type`、`text`；摘要／长度按text准确UTF-8字节计算，不trim或改换行／BOM。JSON路径相对artifacts，为 `TASK_ID/design/RAW_BODY_SHA/body.SUFFIX`：plain text→`txt`、Markdown→`md`、HTML→`html`、JSON→`json`，服务端发布到执行state的 `artifacts/` 下，拒绝任意宿主路径。packet正文引用须与descriptor完全匹配；reference-only无body且不抓取。`report_ref`指完整full Markdown报告，声明的 `html_ref`指完整HTML报告；必须提供全部full正文，不能用摘要或本地文件名代替；publish最多32个body项，并拒绝重复source ID或未引用body。body-file仅为封闭submission形状，不是native envelope、已存intent或recorder metadata。

```bash
ergora task design publish my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --operation-id design-round-1 --parent-record-sha256 PARENT_SHA --revision CURRENT_PROJECT_REVISION --body-file publish-round-1.json --timeout 20
```

下一操作前重读inspection和当前project revision。respond的完整外层形状如下，按**当前**packet真实ID及准确原答复填写；大写SHA／ID／正文均为用户占位符：

```json
{"schema_version":1,"response":{"id":"RESPONSE_ID","question_ids":["QUESTION_ID"],"packet_content_sha256":"CURRENT_PACKET_SHA","choice_ids":[],"source_refs":[],"authored_by":"REPORTED_AUTHOR_ID","origin":"reported-human","supersedes_response_id":null},"body":{"media_type":"text/plain","text":"FULL_EXACT_ANSWER"}}
```

`origin`仅为 `agent`或 `reported-human`，`authored_by`只是reported metadata；question／choice／source IDs须来自当前packet。packet SHA使用UTF-8、Unicode不转义（`ensure_ascii=False`）、排序键、`separators=(',', ':')`、`allow_nan=False`且不追加尾换行的JSON计算；不是缩进文件字节SHA，也不是revision推进后的旧seed packet SHA。不要提交owner-channel、recorder、actor、role、attestation或server-time字段：可信自然人保证不可用，服务器仅记录本地process身份。答复正文只接受plain text／Markdown。完整填写后保存为 `answer-round-1.json`：

```bash
ergora task design respond my-project TASK_ID --run-id RUN_ID --plan-sha256 SEED_PLAN_SHA --operation-id answer-round-1 --parent-record-sha256 CURRENT_PARENT_SHA --revision CURRENT_PROJECT_REVISION --body-file answer-round-1.json --timeout 20
ergora task design operation my-project TASK_ID answer-round-1 --timeout 20
ergora task design resume my-project TASK_ID answer-round-1 --revision CURRENT_PROJECT_REVISION --intent-sha256 ORIGINAL_INTENT_SHA --timeout 20
```

resume仅用于检查已保存原operation后的明确恢复，成功写入不必再resume。保留task／run／operation ID、原intent SHA和recorder身份；超时／丢回复先读状态，再恢复同一ID，不换ID、改提交内容或重发unknown。resume使用完整原intent／正文，不需最初body-file。pending尾部会阻断新ID，须先恢复其准确原operation；旧schema1 approval与source共享operation命名空间。缺managed body只能明确恢复补齐，冲突字节／坏链会阻断，GET不修件。

第二轮仍先inspect，复制完整当前packet、推进revision／previous SHA、提供全部full正文，再用新IDs与最新parent publish／respond。每commit推进 `material_revision`，response不推进packet revision；packet、material和project revision各不相同。旧packet／报告／被supersede的原答复保持可读。anchor存在后，source history读取／恢复为本地并返回 `runtime_status:not_queried`；仍需原选定安装与文件，不证明旧run当前仍pending，需要实时状态另查task status。

[storage profile](../../../src/ergora/data/design-profiles/design-source-storage-v1.json)默认artifact／packet262144B、完整inspection1048576B、64 operations（含pending）、32 packet revisions、intent4194304B、raw journal16777216B。首次submission可选 `storage_limits`仅能收紧；完整有效profile冻结后不得提高／更换。实际完整intent／历史／最终编码public结果都须容纳，默认不保证64个operations或32个packet revisions都能容纳。完整committed视图／结果不截断，也不把部分读取伪装为完整成功。intent发布前的validation／容量拒绝不新增source intent；后继I/O／fsync／确认失败可能留下pending intent，或已有可见result但本次调用尚未确认持久。先查原operation，再用同一ID／intent SHA明确恢复，即使result字节已可见；不删除、覆盖或换新ID。冻结预算不足时需新的合法seed任务。CLI body-file读取另有16MiB边界。

这些记录不实现Q/K owner resolution、seal／withdraw、可信设计批准或执行；readiness／capabilities保持false，材料已供给不是owner决定。原schema1 `task approve`独立存在，**不消费**新讨论，也不把它传播给旧work；publish／respond不授权执行、不更改冻结任务字段、不开放schema3效果，也不构成真实服务／自然人／GPU验收。

## 批准精确计划与恢复投递

先按上节读取并审阅完整材料，再用当前项目修订、原run ID及该plan SHA明确批准：

```bash
ergora task approve my-project TASK_ID --decision-id owner-one --revision 1 --run-id RUN_ID --plan-sha256 PLAN_SHA --confirm --timeout 20
ergora task approval my-project TASK_ID owner-one
# 中断后先读approval，再用原intent_sha256和当前项目修订恢复：
ergora task resume-approve my-project TASK_ID owner-one --revision 1 --intent-sha256 APPROVAL_SHA --confirm --timeout 20
```

decision ID是本次owner决策的稳定标识。重复同ID只读取原记录，不重发、不修改plan或延长24小时有效期。计划更新、原决策过期或撤销后，应审阅当前计划并使用新decision ID明确作出新决策。原角色快照不随项目绑定变化；此本地入口使用当前Linux用户作为owner actor，不提供团队身份认证。

`approval`只读本地记录，不连接Temporal。状态为`not_recorded / prepared / unknown / requested`：prepared尚无信号检查点，可明确恢复；unknown已保存attempt，恢复只能在原run的分页history中核对精确request/plan/receipt，不重发。未找到信号或原run不可用时保留未知，应继续沿原ID对账。owner回执被撤销或更改时原意图不再可派发。

`requested`只说明SDK已应答信号，或原history有对应事件；`approval_accepted: null`、`execution_success: null`不是批准采用或六阶段成功。工作流仍按原授权规则检查owner/expiry/revocation/精确计划，用`task status --run-id RUN_ID`核对实际进度。CLI变更仅在requested时返回0；HTTP成功响应也须检查status。

审批操作记录位于执行状态目录`ergora/task-approvals/TASK_ID/DECISION_ID.{intent,attempt,result}.json`，原owner回执在`approvals/owner-UUID.json`；必须与原任务、创建和提交记录一起保留。准备意图时保留项目revision且非阻塞获取原任务锁；网络阶段已释放控制库写锁，只持同任务锁。准备和网络各有1–60秒预算，父进程各另留5秒，本地预检另计；超时后先读记录再决定恢复。

API：GET/POST `.../tasks/TASK_ID/approvals/DECISION_ID`，POST正文为`revision/run_id/plan_sha256/confirm/timeout`；POST同路径`/resume`正文为`revision/intent_sha256/confirm/timeout`。`confirm`必须为true；写请求沿用同源保护及`X-Ergora-Request: 1`。旧参考入口创建/启动的任务继续由原CLI管理，本入口不会采用旧运行。
