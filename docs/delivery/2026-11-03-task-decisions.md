# F3.3c：精确批准、取消与原运行对账

日期：2026-11-03。本文件保留决策设计；c1精确批准现已实现、定向验证，独立审查和最终发行待完成，见[批准记录](2026-11-03-task-approval.md)。c2取消尚待实施。F3.3b已完成修正版发行/CI收口，依赖其精确创建/提交意图、原run回执、严格原始输入与memo归属校验。

## 分段

- F3.3c1：精确计划批准。必须明确当前项目revision、原run ID、当前plan SHA和owner决策；只接受统一入口创建并已提交的原任务。CLI/API共用tasks，不让网页直接写审批目录。提交前确认原run仍在AWAITING_PLAN_APPROVAL且SHA一致；复用原plan-approval公开回执格式、adapter.publish和原authorize规则，保留明确human/owner/actor/expiry/non-revoked字段。保存本次不可变意图、稳定receipt ID和原始回执，再发送原approve_plan信号；不能把信号应答当作工作流已经批准或六阶段成功。
- F3.3c2：明确取消及对账。必须明确原run ID、原因和确认；复用原Transport.cancel的协作取消及fence语义。已闭合run不宣称新发出取消信号；信号成功只记请求已发出，CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION保持可见，不terminate、不删ledger、不释放未确认租约或换ID重开。

两段各为完整可审查节点，分别进行fresh-context结构/性能审计；F3.4继续负责新的两模板六阶段/导出/重启综合实测。

## 意图、信号与恢复边界

沿用当前专用原生进程和创建/提交所有者的完整校验。先保存包含项目/控制目录/登记、creation/submission SHA、原spec/run/plan或取消原因的意图，然后才发布owner回执或发出信号。原绑定不能热换，过期批准不能自动延长或改新plan。

信号前保存attempt，信号后保存准确的原生确认；重复命令读取原记录。未派发的明确resume需重新核原run/phase/plan及回执有效性。未知信号不盲目重发；先从原run的真实history核对稳定信号身份，原始输入及本次提交memo也必须匹配。批准已有receipt_id可用于history核对；取消原payload没有操作ID，实施前需确认怎样以兼容原handler的窄边界保存去重关联，不能仅按相同原因认定本次请求已送达。该具体选择仍待源码/SDK探针，不能预先写成已实现。

history查询必须有总预算，不能加载无界历史或因分页未找到便作不存在。网络/权限/历史不可用、原始输入冲突或身份不明保持unknown，明确返回原ID与人工对账责任。确认只是接收/投递事实，工作流是否采用批准、外部作业是否停止仍以原权威状态/授权和fence为准。

## 预定验收

- CLI/API严格修订、明确确认、固定run和精确plan；错误/旧plan、错误run、原spec/创建/提交/memo漂移、过期/撤销/非owner回执拒绝；默认和变更角色不改变旧任务。
- 意图前、审批回执前后、signal前后和最终回执前逐点中断；重复/并发不制造新owner回执或重复未知副作用；恢复保留原receipt、原授权范围和过期事实。
- 使用真实原authorize、workflow信号handler/Transport和可控SDK验证被接受、被拒绝及未知；不能把fixture成功当模型或实际服务验收。
- 取消的running、已terminal、信号丢响应、连接失败、fence未确认及真实外部对账分别记录。性能测量注明CLI启动/SDK/网络/历史范围与分页上限。
- 最终非editable包/两安装/冻结283文件、相关回归与精确两OSCI各自验收。每段更新PLAN、交付记录和独立审查，再提交推送。


## 原生接口探针与实施选择

已在隔离目录实际调用原FileAdapter.authorize和两个workflow信号handler，无Temporal服务/模型：有效human/owner回执通过，expired/revoked/agent/错误role/错误plan五类被原校验器拒绝；approve_plan接收原receipt ID，request_cancel在附加操作摘要时保留原原因并忽略额外关联字段。原始contracts-probe.py/json/log在.ergora/checks/f3-task-decisions/，不是实际信号投递或授权activity验收。SDK1.34支持固定run的signal与分页fetch_history_events；后续恢复使用流式分页、总预算，只在原run历史有精确原信号身份时补投递回执。

F3.3c1拟使用调用者提供的decision_id（合法稳定标识）区分多次明确owner决策，避免过期/撤销后把新的批准悄悄塞进旧意图。CLI approve需要--decision-id，读取/恢复携带相同ID；API以tasks/TASK_ID/approvals/DECISION_ID限定资源。重复同ID只读取原意图/回执；不同ID必须重新提供当前revision、原run、精确plan及确认，生成新的owner回执，而不是自动续期原批准。

审批入口采用两个明确阶段：在当前项目revision保留和非阻塞原任务锁下仅保存不可变意图（无网络）；释放控制库写保留后，以原任务锁执行精确run/plan检查、原回执发布和信号。阶段间中断留下prepared；若其他明确resume先取得任务锁，原调用只能读取其结果/未知状态，不重复信号。准备阶段遇任务忙应明确失败，不能持全库锁等待长远程操作。此处直接采用F3.3d要求，B提交的长锁迁移仍需独立完成，不能从新审批设计推导已修复旧提交。

## F3.3c2下一切片的已核接口

原`DevelopmentTransport.cancel`先按固定run核原spec，仅在description为RUNNING时发送`request_cancel`；已闭合时直接返回None。统一入口不能仅凭该返回值报告“已发送取消”。本段将复用原cancel，通过专用边界识别实际信号调用、保存写前attempt并附加已探针确认兼容的`ergora_operation_sha256`关联字段；原handler保留request/reason语义。已闭合回执必须明确没有新信号，且不把Temporal闭合推导为外部进程已停。

预定CLI为`task cancel ... --request-id ID --revision N --run-id RUN_ID --reason TEXT --confirm`、`task cancellation ... ID`、`task resume-cancel ... ID --revision N --intent-sha256 SHA --confirm`；API资源为`tasks/TASK_ID/cancellations/REQUEST_ID`及`/resume`。request ID表示稳定取消请求，原因沿原限制非空且最多1000字符。意图固定原run/提交/spec/原因/actor，重复请求不改变原因或重发；prepared明确恢复，unknown仅在原run history匹配包含本次操作SHA的精确payload后补投递回执。CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION及原fence/租约的责任保持不变。上述仍是实施设计，尚无c2生产代码或验收结论。
