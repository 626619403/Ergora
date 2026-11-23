# 查询正式任务运行状态

简体中文 · [English](../../development/run-and-recover.md) · [文档目录](../../README.zh-CN.md)

安装development组合或 `ergora[temporal]`，并准备所登记的参考运行时。通过CLI或 `GET /api/projects/ID/tasks/TASK_ID/status?run_id=RUN_ID&timeout=20` 只读查询原生运行事实：

```bash
ergora task status my-project TASK_ID --timeout 20
# 后续查询固定前次返回的原生run_id：
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

该操作先验证本地任务的项目归属和spec，再由所登记安装中的原DevelopmentTransport核对Temporal的原始启动输入。`runtime_status: queried`附原生workflow/run ID、phase及status或outcome；未提供run ID时先解析当前workflow并返回其确定的run ID，后续可固定这个ID。只有原生NOT_FOUND返回 `runtime_status: not_found`，不附伪造phase；连接、认证、超时、原始输入碰撞等均报错，不能当作未启动。查询不提交、批准、取消或释放工单租约，不写入任务状态。

`terminal: true`只表示Temporal运行已闭合；outcome仍可能是CANCEL_UNCONFIRMED，或phase为NEEDS_RECONCILIATION，均须沿原ID对账。该入口使用登记的参考环境连接规则（目前是本机127.0.0.1:7233/default），项目scheduler绑定的地址/队列只用于资料研究调度。1–60秒timeout约束网络查询；子进程另留5秒启动/回收预算，本地合同预检和安装身份检查另计。SDK缺失会明确提示，不自动安装或从本地COMPILED/服务RUNNING推断运行状态。完整六阶段执行仍使用Linux/WSL2。

## 提高待派发工作单元的优先级

原计划批准后，监管者可以通过已登记的 Linux/WSL2 CLI 指定一个待派发的工作单元。任务须有 `task start` 的原提交回执。先查询原运行，取得 `status.work_priority.pending_work_unit_ids`、`plan_sha256` 和项目修订号。当前带预算的准备工作流需要由支持此操作的 Worker 执行，且查询显示 `work_priority.available`。为本次决定指定唯一的决定 ID。

```bash
ergora task status my-project TASK_ID --run-id RUN_ID
ergora task prioritize-work my-project TASK_ID UNIT_ID --revision REVISION \
  --run-id RUN_ID --plan-sha256 PLAN_SHA --decision-id DECISION_ID --confirm
ergora task work-priority my-project TASK_ID DECISION_ID --run-id RUN_ID
```

`applied` 表示工作流已记录优先级。原前置工作完成且原并发限额允许时，该单元优先派发。等待期间，其他已就绪的单元仍可派发。后续决定可以改变优先项。每个单元沿用原输入、执行者和 Job ID，继续使用原计划审批、预算截止时间、集成、验证和审查流程。

系统把尝试记录保存在原提交记录目录中，再向原运行发送 Temporal Update。请求回执丢失时，用 `task work-priority` 按原运行和决定 ID 查询。重复提交同一决定也只读取结果。结果暂不可查时，状态保留为 `unknown`。发送前检测到拒绝或 Worker 未提供此操作时，不会保存尝试记录。若请求与派发、取消或预算耗尽同时发生，原工作流可能返回一条已记录的拒绝结果。运行和恢复期间，更新后的队列使用支持此 Update 的 Worker。

## 分段读取原运行事件

对统一创建且已保存原提交回执的任务，固定该回执的run ID，读取事件元数据：

```bash
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --timeout 20
# 仅在需要继续时，将上次返回的next_after原样传入：
ergora task events my-project TASK_ID --run-id RUN_ID --limit 20 --after CURSOR --timeout 20
```

同源只读API为`GET /api/projects/ID/tasks/TASK_ID/events?run_id=RUN_ID&limit=20&after=CURSOR&timeout=20`，首次省略after。该入口使用上述Linux/WSL2参考运行时和原提交/spec/memo验证，不跟随其他run。返回事件ID、类型、时间和适用的activity/scheduled_event/signal关联字段，不返回原始输入、prompt、result或payload；事件投影不解码payload，原身份验证仍需解码启动spec。`read_only: true`、`execution_success: null`明确这只是事实片段。没有原生run时返回`runtime_status: not_found`；连接、超时、错误归属或游标错误明确失败，不自动重试或重发任务。

原验证完成后每次读取一个事件SDK物理页、返回最多limit条（1–100，默认20），不是保证每次填满limit；整个请求另有原运行describe及启动前缀读取，不等于一次RPC。Temporal的物理页大小是建议值，可能超出请求条数；游标保留该页未读位置，下一次先继续剩余内容。`next_after`是绑定原提交/run的只读导航信息，不是授权或完整history证明，不能跨run使用。显示limit可以调整；SDK页大小保持原游标的值。总JSON响应最多1 MiB；SDK接收物理页的网络内存不受此响应上限约束。timeout为1–60秒墙钟预算，父进程另留5秒启动/回收，预检另计。

`has_more`表示已知还有未读内容，`at_current_end`只表示读至本次可见尾部。RUNNING即使暂时无新事件仍保留next_after，稍后由用户显式读取；终态读至尾部才返回null。事件片段不证明六阶段完成、候选通过或外部进程已停；继续通过原status/outcome和外部对账核实这些事实。

网页在正式任务中先“读取原运行”，再点击“读取原运行事件”。打开时读取第一批，之后每次点击最多读取20条，不自动轮询或重试。页面显示累计读取数及最近200条；关联字段超过256个Unicode字符时显示省略号，完整元数据可沿CLI/API读取。运行中到达当前尾部仍可手动“读取新增事件”；终态读完后按钮停用。读取失败保留本次已读片段和原位置，明确点击重试才继续。关闭重开后从第一批读取；切换项目、任务或run后旧回复失效。显示记录只是本次观察，不作为持久证据或完整历史证明。

## 读取原job回执与文本证据

从上述原事件中选择Activity类型为`dev_submit`的`ACTIVITY_TASK_SCHEDULED`事件ID（不是activity ID或completed事件ID），先读取job目录。以下42只是示例，请使用实际ID：

```bash
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --timeout 20
# 从返回receipt.artifacts选择名称，保留本次receipt_sha256；不要传本地路径
ergora task job my-project TASK_ID --run-id RUN_ID --event-id 42 --artifact model-log --receipt-sha256 RECEIPT_SHA --offset 0 --limit 8192 --timeout 20
```

API为`GET /api/projects/ID/tasks/TASK_ID/jobs/42?run_id=RUN_ID&timeout=20`；文本窗口再带`artifact=model-log&receipt_sha256=RECEIPT_SHA&offset=0&limit=8192`。沿返回`artifact.next_offset`手动继续，null表示该文本的末尾。offset/limit以Unicode字符计数，不是UTF-8字节；每窗默认8192、最多16384字符，保留原全文的SHA、字节数及字符数。回执变化或产物字节变化时明确失败，不能拼接成同一份日志。产物名称只从所选原job回执匹配，不解析用户传入的路径。

该读取仍固定统一任务原提交/run/spec/memo，按连续history前缀核到所选调度事件，只解码该事件的原context，再核原请求envelope与可信目录发布的回执。支持事件ID1–10000；更后的事件明确拒绝，不能据此判断没有job。RUNNING和闭合原run均可读；`runtime_status: not_found`表示当前原history未知，`receipt_status: missing`表示尚无可验证的已发布回执。没有回执时不提供日志，也不将请求目录存在当作执行完成。

`receipt_status: published`只表示原job的当前发布回执通过本机可信文件适配器核对，`workflow_receipt_accepted: null`与`execution_success: null`保留未知。即使回执state为SUCCEEDED，也要通过原运行status/outcome、候选检查与外部对账核实际采用、开发结果及清理事实。此功能不改原意图、回执、claim或Git引用，不提交、重发或自动重试。

沿原生适配器每份产物最多16 MiB；先核完整摘要，再严格解码所选UTF-8全文、拒绝NUL，之后返回窗口。缺失、损坏、非UTF-8、NUL、超限或不安全路径均明确失败。每次核回执会重读其全部产物摘要，所选文本还需完整读取/解码；窗口和1 MiB JSON响应上限不代表SDK物理页或总文件读取/内存的上限，没有隐藏缓存。timeout为1–60秒；协程内网络受20秒RPC及请求预算约束，同步文件读取由父进程timeout+5秒最终回收。本入口使用现有Linux/WSL2参考运行时；基础Web本身不需Temporal SDK，原生查询需要所登记完整执行环境及其SDK。环境不完整时按工具诊断页配置，不自动安装或启动服务。

网页中先读取原运行及其事件，在Activity为`dev_submit`的调度行点击“原job证据”。弹窗读取该原run/事件的job目录，展示原回执、候选及摘要；缺失或失败时可手动重新读取。选择回执中的材料不会发起文本请求，点击“读取所选材料第一段”后才读取8192字符窗口，再手动读取下一段。每次固定首次回执SHA，页面只保留当前窗口及完整产物摘要。材料错误或原运行未知时保留已读窗口和原偏移，可“重试原位置”；回执变化时关闭并重新核目录，不能拼接旧窗口。切换材料清空窗口并归零，末尾停止；关闭重开不恢复文本、不后台轮询。编辑run、切任务/项目、替换弹窗或离开页面后，先前请求的迟到回复失效。

## 提交正式任务与恢复未知结果

在Linux/WSL2安装参考运行时所需依赖并初始化所登记的配置，使用该运行时的`.venv/bin/python`执行准入。控制面无需安装全部执行依赖；v1–v6使用原安装级doctor，v7来源任务按[冻结选择](../projects/issues.md#从工单快照创建来源任务)检查实际依赖。实际提交继续核可信检查、策略和工单占用，所选服务及模型须就绪。此入口仅接受通过统一入口完整创建的任务，保留其原spec和角色快照。

```bash
# CREATION_SHA取自task creation的intent_sha256；修订取自project show。
ergora task start my-project TASK_ID --revision 1 --creation-sha256 CREATION_SHA --timeout 20
ergora task submission my-project TASK_ID
# 中断后先读submission，再用其原intent_sha256和当前项目修订显式恢复：
ergora task resume-start my-project TASK_ID --revision 1 --intent-sha256 SUBMISSION_SHA --timeout 20
```

`submission`仅检查本地提交记录，不连接Temporal。`status: submitted`表示保存了原workflow/run ID回执，`execution_success: null`不代表六阶段成功；运行进度用`task status --run-id RUN_ID`查询。重复start只返回原本地记录，不重发提交。`not_recorded`表示没有提交意图，`prepared`表示已有意图但尚无派发检查点，`unknown`表示检查点已保存而原调用结果未知，`rejected`表示发现不属于本次提交的既有run并保留了拒绝记录。变更命令仅在submitted时返回CLI成功。

先保存不可变意图，再走原准入/claim；实际start之前保存attempt，最后保存原生回执。prepared可通过明确resume重走准入、复用同一租约；unknown只能沿原workflow ID查询原始输入并补回执，即使NOT_FOUND也不能重发。检查点写入后、实际RPC前崩溃也保留unknown，需人工对账。发现既有run时拒绝接管，后续历史消失也不会自动重新开始。原start在Temporal memo中关联本次提交意图摘要，未知恢复还会核对该标记；没有或不同的标记不能被采用为本次提交。提交竞争返回AlreadyStarted会持久拒绝，不采用其他入口的run。原始输入按规范JSON摘要精确比较，true/1/1.0不混淆。原始输入不一致、RPC失败、合同/登记漂移均明确报错，不换任务ID绕过未知状态，不释放租约。已保存回执的重复操作继续返回原run ID。

意图、派发检查点、回执及适用的所有权拒绝记录位于执行状态目录`ergora/task-submissions/TASK_ID.{intent,attempt,result,rejection}.json`，必须与创建记录、任务目录和原运行状态一起保留。准备阶段在当前项目修订保留下非阻塞取得原同ID锁，仅保存意图；随后释放控制库写锁，网络阶段只持原任务锁。1–60秒timeout分别约束准备和网络阶段，父进程各另留5秒启动/回收，预检另计。超时只回收提交客户端，实际Agent由持久执行器拥有，不能据此判断已停机。完整环境缺失时明确报错；不自动启动服务或修改执行权限。

API：`POST .../tasks/TASK_ID/start`正文为`revision/creation_sha256/timeout`，`GET .../tasks/TASK_ID/submission`，`POST .../tasks/TASK_ID/resume-start`正文为`revision/intent_sha256/timeout`；写请求沿用同源保护及`X-Ergora-Request: 1`。同任务并发准备或创建/恢复创建遇活跃任务锁时及时报busy；并发读取也可能取得prepared/unknown快照；无需等待另一请求完成才返回。操作结束后读取submission及当前项目修订，再决定是否明确resume；重复start不隐式重试未派发准入，unknown不重发。其他项目不会因本次网络等待而被持续占用控制库写锁。HTTP成功响应仍须检查status，unknown/rejected不能当作提交成功。

## 请求取消与恢复未知投递

统一创建且已保存原提交回执的任务，可固定原run请求协作取消。与批准入口相同，使用当前项目修订、稳定请求ID和明确确认；原因非空且最多1000字符：

```bash
ergora task cancel my-project TASK_ID --request-id stop-one --revision 1 --run-id RUN_ID --reason 'Owner requested stop' --confirm --timeout 20
ergora task cancellation my-project TASK_ID stop-one
# 中断后先读cancellation，用其原intent_sha256恢复同一请求：
ergora task resume-cancel my-project TASK_ID stop-one --revision 1 --intent-sha256 CANCELLATION_SHA --confirm --timeout 20
ergora task status my-project TASK_ID --run-id RUN_ID --timeout 20
```

`cancellation`只检查本地记录，不连接Temporal。`prepared`尚无派发检查点，明确恢复可继续原cancel；`unknown`已有检查点但投递未确认，只能沿原run history核对包含本次操作SHA的完整signal，不能凭相同原因认领其他请求，也不会重发。重复同ID保留原原因/actor，不生成第二个请求；不要用换ID来绕过未知，先核原运行和外部作业事实。

`requested`和`cancel_requested: true`仅表示signal已应答或原history有对应事件。`already_closed`表示原run在本次检查时已闭合，`cancel_requested: false`、`signal_delivery: not_sent`明确本次没有新信号；重复读取是已保存事实，不是新的实时查询。两种状态的CLI变更返回0，仍须核对状态字段。`cancellation_confirmed: null`和`execution_success: null`不表示已停机；用`task status --run-id`核对原phase/outcome。CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION要继续按原fence和外部作业对账，不能删ledger、terminate或自动释放未确认租约。

意图/attempt/result位于执行状态目录`ergora/task-cancellations/TASK_ID/REQUEST_ID.*.json`，须与原任务、创建及提交记录保留。准备阶段在当前revision下非阻塞获取原任务锁，远程阶段已释放控制库写锁；每阶段1–60秒预算，父进程各另留5秒，本地预检另计。Windows使用已登记Linux/WSL2完整运行时；该本地入口不是团队权限系统。

API为GET/POST `.../tasks/TASK_ID/cancellations/REQUEST_ID`，POST正文`revision/run_id/reason/confirm/timeout`；POST同路径`/resume`使用`revision/intent_sha256/confirm/timeout`。严格确认必须为true，写请求沿用同源保护及`X-Ergora-Request: 1`。旧入口任务仍由原CLI管理。

## 正常任务完成后的关闭

`REVIEW_READY`表示原候选通过了工作流要求的验证和审查，workflow闭合不会自动释放工单租约。准备采用候选时，按[候选导出](evidence-and-export.md#导出精确候选与恢复回执)明确导出并核回执；该入口沿原规则释放适用租约。暂不导出或只需结束本次任务时，也可先核证据，再明确对账：

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
ergora task reconcile my-project TASK_ID --revision CURRENT_REVISION --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
```

先确认原run闭合、原job与可信终态回执/产物完整，无额外或未解决job。没有正确fence时，首次只读检查的external_confirmed可能仍为false；它不发布fence，也不释放租约。明确reconcile才建立原执行屏障、重新核对并释放精确claim。缺证据时保持unknown；外部进程是否已停止仍按实际执行器核对，可信文件回执不能代替操作系统检查。

对账保留正常REVIEW_READY及精确候选，不合并或删除分支；之后仍可明确导出同一候选。只有reconciled表示本次租约释放及回执已保存，中断按下节原intent恢复。下载交接包、关闭浏览器/HTTP或停止服务都不释放租约；停止共享栈前逐一核对其项目的在途任务和外部作业，再按[服务管理](../operations/services.md#显式服务管理)退出并备份持久目录。

## 显式终态对账与工单租约释放

原运行闭合后，使用当前项目修订和固定原run明确授权fence及外部清理核对：

```bash
ergora task reconcile my-project TASK_ID --revision 1 --run-id RUN_ID --confirm --timeout 20
ergora task reconciliation my-project TASK_ID
# 中断或补齐原可信回执后，使用上条返回的原intent_sha256恢复：
ergora task resume-reconcile my-project TASK_ID --revision 1 --intent-sha256 RECONCILIATION_SHA --confirm --timeout 20
```

只接管本控制目录统一创建、保存原提交回执且保留原`local-cli`工单归属的任务。对账前后都核原run仍是当前run、完整原history及登记adapter目录；额外请求/孤立回执会阻止接管该scope。发布原不可变fence后，须逐一确认所有历史job的原请求、可信终态回执及哈希产物；缺失/损坏证据保持unknown并保留租约。可信执行器仍须遵守fence和独立walltime；这份文件协议证据不能代替系统进程扫描。所有协调者必须保持task ID不可复用，不能在协议外为同task启动新run。

`reconciliation`只读本地记录，不查远端、不发布fence或释放租约。`prepared`尚未保存写前检查点；`unknown`已保存原outcome/history身份但没有完整清理证据；`confirmed`已保存清理证据但释放回执尚未保存；只有`reconciled`表示租约已按精确原claim释放且回执已保存。恢复会重验原事实，按同一fence/证据摘要幂等推进。重复reconcile返回已保存状态，明确resume-reconcile才继续未完成操作。已完成回执是历史事实，实时外部状态继续使用external-status。

`original_outcome`保持真实原结果：即使原结果是CANCEL_UNCONFIRMED，本次确认清理也不会把它改成BLOCKED或开发成功。`execution_success: null`不推断候选是否通过。原native release适用时保留原outcome摘要，其余闭合清理使用独立清理evidence摘要，不能手改owner/ledger或删证据绕过冲突。CLI变更只在reconciled时返回0；HTTP成功也须检查status。

API：GET `.../tasks/TASK_ID/reconciliation`、POST `.../tasks/TASK_ID/reconcile`（`revision/run_id/confirm/timeout`）、POST `.../tasks/TASK_ID/resume-reconcile`（`revision/intent_sha256/confirm/timeout`）。confirm严格为true，写请求沿用同源保护及`X-Ergora-Request: 1`。Linux/WSL2使用登记完整运行时；每阶段1–60秒，父进程另留5秒，本地预检另计。原任务锁保护同task，远程阶段不持控制库写锁。

执行状态目录`ergora/task-reconciliations/TASK_ID.{intent,attempt,evidence,result}.json`须与原任务/创建/提交、请求/回执/产物/fence及`ingress/leases.sqlite3`一起备份。证据或数据库丢失时保留未知，不通过新建ledger重建所有权。
