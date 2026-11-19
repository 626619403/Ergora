# 当前设计流程的可用范围

简体中文 · [English](../../development/tasks.md) · [文档目录](../../README.zh-CN.md)

首次统一登记可以保存schema2设计policy及其有效摘要，并显示 `execution_supported: false` 与 `human_channel_unavailable`；schema2任务出生与受管native执行均以 `design_policy_execution_unsupported` 拒绝。已有登记不能通过该入口升级、替换或降级，详见[当前登记边界](../../projects/registration.md#current-limits-of-design-policy-registration)。这只提供policy存储，不是可执行设计批准；设计来源journal存取、可信owner／materials／gate处理仍按[PLAN](../../PLAN.md)实施，计划与调研不是已交付支持的证明。原schema1任务合同保留。

逐Agent显式思考强度字段可请求所选后端／模型支持的等级。统一fixed／preset／planner／automatic选择及配置冻结合同仍是后继工作；请求等级不证明native实际强度，也不授权换模型、暗中降档或增加预算。

## 正式任务的操作顺序与恢复

首次使用按[完整模板旅程](templates.md)和[项目定义](../../projects/registration.md)准备真实Git基线、可信检查与已认证角色，然后使用下列顺序。正式开发需要所登记Linux/WSL2完整执行器；页面中的工作流草稿尚不等于已创建的正式任务。

```text
project register → 选择角色/核revision → services start所选栈
→ task preview → 审阅摘要 → task create → task start
→ inventory/plan → status固定原run → 审阅实际计划 → approve精确plan
→ work/integrate/verify/review → 原outcome
→ REVIEW_READY：审阅精确candidate/检查/review → export本地分支并核租约回执 → 独立复验/人工合入
   暂不导出：external-status → 明确reconcile（原结果/候选保持）
→ 阻塞或取消：核原run闭合 → external-status → 明确reconcile → 按原intent恢复
```

正式任务页面也支持[选择已保存的完整组合](../../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)：可仅替换审查，或选择执行与审查子流程，为每个工作单元分配专长实例及逐叶后端。先读取原preview摘要对应完整包，再预览并明确创建。可写信任与不同后端策略由用户显式选择，失败会显示原owner错误。

保存task ID、创建/提交intent SHA和原workflow/run ID；所有写命令使用当前项目revision，批准另带稳定decision ID及精确plan SHA，取消带稳定request ID。HTTP 200、CLI 0或requested是对应操作回执，六阶段是否通过由原outcome和候选证据决定。页面关闭或CLI进程结束后，可用同一`--home`和登记的执行目录继续查询；不得复用task ID绕过旧记录。

|中断位置|先读|允许的下一步|
|---|---|---|
|任务合同发布|`task creation PROJECT TASK`|以原intent SHA运行resume-create；冲突文件先核对|
|提交结果不明|`task submission PROJECT TASK`|resume-start核原spec/memo/run；unknown只查询，不重新提交|
|批准或取消投递不明|`task approval PROJECT TASK DECISION` / `task cancellation PROJECT TASK REQUEST`|resume-approve/resume-cancel核原操作SHA与history；无匹配信号保持未知|
|闭合但外部未确认|`task status --run-id`及`task external-status --run-id`|保留原结果/请求/回执/产物/fence；明确reconcile，未完成则resume-reconcile|
|候选导出中断|`task export-status PROJECT TASK`|resume-export核原结果和实际ref；unknown不重fetch或复活已删分支|

备份必须联合保存控制`ERGORA_HOME`、登记的CONFIG/STATE、业务Git仓库、Temporal持久数据及实际工具认证；控制SQLite备份不包含原任务/history/候选/租约。执行STATE中的`tasks/`、`ergora/task-*`、requests/receipts/artifacts/approvals/fences、workspaces、进程记录及ledger均属于恢复证据。先停止相关写者并核在途外部作业，再按[备份说明](../install/upgrades.md#升级与持久数据)操作。 完整同平台、原路径的离线操作及启动前核对见[联合备份与恢复手册](../../operations/backup-recovery.md)。

## 正式任务页面

选择已统一注册的项目后，从左侧“正式任务”或项目总览的“查看正式任务”进入。列表按有界游标分页，本页没有匹配项仍可能有下一页；无法读取的记录和无效合同会单独显示。详情展示任务自己的冻结输入、角色快照、工作单元和本地提交回执，不从当前项目绑定补写历史，也不把合同存在或submitted当作执行通过。

“原生运行”默认使用已保存选择或提交回执中的原run ID，点击“读取原运行”后才连接所登记Temporal。结果保留REVIEW_READY、BLOCKED、CANCEL_UNCONFIRMED、NEEDS_RECONCILIATION等原事实；not_found和查询失败分别显示。切换任务/项目、修改run ID或离开页面后，旧响应不会覆盖当前选择。刷新或在同一浏览器标签页返回控制台时保留项目、页面、任务和run选择，执行状态重新查询。关闭标签页后的保留取决于浏览器自身的会话恢复。

点击“预览与创建”，选择项目已登记的开发模板，载入模板输入或兼容的已保存草稿。填写新任务ID、工单编号或本地标识，并编辑完整输入JSON；可指定起始提交，留空使用登记基线。服务端预览展示修订、冻结角色、完整文件与摘要；修改字段或来源后旧确认立即失效。审阅后点击“确认创建冻结合同”，只发布合同，不自动提交运行。训练优化仍使用独立入口。

创建请求发出前，浏览器会把原任务ID保存为本项目的任务选择。回复失败或丢失时表单锁定，先“按原ID读取创建记录”；也可随时从页面顶部按ID查询。重载后合同尚未完整发布时，详情错误中仍保留原ID和查询入口。`pending`展示原意图摘要与冻结修订，明确确认恢复时沿原内容发布；项目后续绑定变化不替换旧角色。`published`显示冻结合同已发布，`not_recorded`不接管旧任务，`conflict`保留冲突文件且不提供覆盖按钮。页面不自动重发创建、换ID或启动执行。

任务详情的“检查提交与恢复”会重新读取创建与本地提交记录。完整发布且无提交记录时，可审阅冻结合同、角色、当前修订和摘要后“确认提交此冻结任务”；`prepared`或`unknown`只提供原意图的明确恢复，后端决定继续尚未派发的提交，或查询已经不确定的派发。`not_found`仍是未知，页面不重发start；归属`rejected`不提供覆盖入口。回复失败时先重新读取原记录，不能据此更换ID。`submitted`保存原run选择，点击“查看原任务与运行”后再单独读取运行状态；提交回执不代表六阶段完成。

原run查询到`AWAITING_PLAN_APPROVAL`时，点击“审阅计划与批准”读取完整execution-plan、ownership-map及rollback-plan和精确回执身份。材料读取失败时没有批准入口。审阅后填写稳定的“决策 ID（用于恢复）”（例如`owner-one`），先“读取批准记录”；仅该ID尚无记录时提供“确认批准此计划”。确认固定本次材料的run/plan SHA，并在服务端再次校验当前状态。保留此ID，不用新ID绕过未知投递。

任务详情另有“按原 ID 检查批准记录”，不要求当前仍在等待计划。浏览器会按项目/任务保留最近的decision选择；选择已清空或换设备时，手工输入原ID仍可取回后端记录。`prepared`可“确认恢复原批准意图”，`unknown`只“确认核对原批准信号”，`requested`仅展示投递事实且不再提供投递按钮。若当前材料工作区查到既有decision，需单独查看原记录，不以当前材料覆盖旧决策。回复失败时先重新读取原记录；重载不会自动批准。实际采用和执行进度需返回原任务再次“读取原运行”。

原run仍运行时，可点击“请求取消此运行”，填写稳定的“取消请求 ID（用于恢复）”并先“读取取消记录”；仅该ID未记录时提供原因输入和“确认请求取消此运行”。服务端固定原run并再次核对状态。任务详情另有“按原 ID 检查取消记录”：`prepared`明确恢复原取消意图，`unknown`只核对原信号，`requested`/`already_closed`不提供再次投递。原原因与意图不可被当前编辑覆盖；`already_closed`表示发送前原run已闭合、没有新信号。

保留原取消请求ID；回复丢失后先读原记录，浏览器选择清空后可手工输入原ID恢复查询。取消是协作请求，`requested`不是停止确认。返回原任务再次“读取原运行”核阶段和终态；外部作业清理与租约释放另行对账。

原run已闭合时，可点击“外部证据与对账”，只读查看该原run的job、请求/回执/产物校验结果、fence和原结果；读取不会改变执行屏障或租约。即使某些作业已有终态，也须检查`external_confirmed`，不能从workflow闭合或取消投递推断清理完成。

同一工作区读取原对账记录；仅在本轮外部证据读取成功、记录为`not_recorded`时提供“确认外部对账并释放原租约”。操作会重验原run，建立或复用同一fence，在外部作业全部确认后释放原claim。任务详情另有“检查原对账记录与恢复”，只读取本地持久记录；`prepared/unknown/confirmed`可“确认恢复原对账意图”，固定原intent SHA，不使用当前编辑的run替换。`confirmed`尚未保存租约释放回执，只有`reconciled`表示原租约释放及回执已保存；后者不再提供写操作。

回复丢失后重载或重新选择原任务，再读原对账记录；无须创建新的对账ID。实时外部证据与历史对账回执分别读取。原`CANCEL_UNCONFIRMED`结果保持，清理完成不表示开发成功。外部读取失败时不能发起新对账，已保存的原意图仍可单独查看和明确恢复。

原run闭合且结果为`REVIEW_READY`时，可点击“导出精确候选”。页面固定本次原run/完整candidate SHA，先读取原导出记录；仅`not_recorded`提供目标本地分支输入和“确认导出此候选至本地分支”。分支是否合法及原候选能否导出由服务端Git/原结果检查，页面不替换已有分支，也不checkout、merge或推送。

任务详情另有“检查原导出记录与恢复”，只读取本地记录，不查询Temporal或当前Git ref。`prepared`可“确认恢复原导出意图”，可能首次创建已保存目标；`unknown`可“确认核对原导出分支”，仅核对原分支，`branch_not_found`保持未知，不重新创建。恢复固定原intent SHA，repo/run/candidate/branch均不可更换。`exported`只展示历史回执和原租约释放事实，不证明当前ref仍正确，也不表示开发成功或已合并。回复丢失后重新选择原任务读取同一记录，无须重发导出；维护者在采用前仍需复验实际分支及证据。

未统一注册时显示登记指引；服务不可用时仍可查看本地合同。关闭弹窗或页面不会撤销已经发出的操作，关闭页面也不取消外部任务；终态不等于外部作业已确认清理。浏览器仅保存选择，创建/执行事实每次从服务端读取。

## 读取正式任务合同

先完成[统一项目注册](../../projects/registration.md)，执行目录已有的开发任务可直接从主入口读取：

```bash
ergora task list my-project --limit 50
ergora task show my-project TASK_ID
```

同源API为 `GET /api/projects/ID/tasks?limit=50&after=CURSOR` 和 `GET /api/projects/ID/tasks/TASK_ID`。默认每页校验50个候选目录项，可设1–100；原样使用返回的不透明ASCII游标 `next_after` 继续，直到其为null；游标不是任务ID或文件路径。每页流式枚举全部目录名再选取候选窗口，因此枚举时间随任务数增加；`inspected_entries`只计该页校验项数。其他项目或损坏目录可能产生空页，仍应沿游标前进。`items`只包含匹配该项目/Git根/tracker并通过合同结构与摘要校验的任务；归属已确认但合同损坏的条目进入 `errors`，不能判断归属的条目只计入 `unreadable_count`。

详情返回原始spec、冻结项目、可选的 `agent_bindings` 及其文件SHA256。`project_revision`是当前控制项目修订，冻结绑定中的 `project_revision`属于创建或首次执行时的快照。`runtime_status: not_queried`表示没有访问Temporal；本地文件存在不代表任务开始、完成或验收通过。合同查询不安装SDK、启动服务、提交任务或写回旧记录；统一创建/提交的任务使用下文的明确批准、取消与导出入口，旧入口任务继续按[正式执行手册](../../agents/backends.md)管理。Linux/Windows均可读取本机可访问的执行目录，完整六阶段执行需要Linux/WSL2。

## 预览与创建正式任务

统一注册项目可在无Temporal/Web SDK的基础安装中编译和保存两个开发模板。先保存 `task-definition.json`；`input` 使用模板的原始输入格式，具体字段和DAG仍由原编译器校验：

```json
{
  "schema_version": 1,
  "task_id": "example-change",
  "task_type": "repository-governance",
  "issue_id": "1",
  "input": {
    "goal": "检查并整理 src 内的模块边界",
    "allowed_paths": ["src"],
    "acceptance": ["保持已有行为和可信检查"],
    "constraints": [],
    "risk": "standard",
    "work_units": [{"id": "inspect", "depends_on": [], "paths": ["src"], "instructions": "完成边界整理"}]
  }
}
```

模板可选 `repository-governance` 或 `large-change`，必须已在项目登记；大型开发按原模板设置其风险与输入。可选 `starting_sha` 是40位小写Git提交SHA，默认使用登记的基线。将以下修订替换为 `project show` 的当前值：

```bash
ergora task preview my-project --definition task-definition.json --revision 1
# 审阅返回的 files 中完整 spec、可信策略、冻结项目及 agent-bindings。
# 用本次输出的 preview_sha256 替换 PREVIEW_SHA：
ergora task create my-project --definition task-definition.json --revision 1 --preview-sha256 PREVIEW_SHA
ergora task creation my-project example-change
# 发生中断时，用 creation 中的 intent_sha256 和当前项目修订恢复：
ergora task resume-create my-project example-change --revision 1 --intent-sha256 INTENT_SHA
```

preview只在自动清理的临时目录调用原编译器，不写真实任务目录。摘要绑定控制目录、项目修订、登记身份、全部编译合同和角色快照；定义或绑定变化后必须重新审阅预览。create在任何原生任务文件发布前先保存完整意图，然后不可变发布七份合同，最后保存结果回执；相同请求可以幂等重试。任务ID在同一执行状态目录全局唯一，没有本工具意图的旧任务不能通过create或resume-create接管。

`creation.status` 为 `not_recorded / pending / published / conflict`，只描述本地文件发布。`runtime_status: not_queried` 和 `execution_started_by_operation: false` 表示本次操作未查询或启动工作流，不能据此推断该任务的实际运行状态。合同逐文件最多1MiB；意图上限16MiB。比较使用原生规范JSON内容摘要，保留等价既有文件的字节。意图及回执位于登记的执行状态目录 `ergora/task-creations/TASK_ID.intent.json` 与 `.result.json`，必须连同原任务目录保留；Ergora控制库的单独备份不包含执行状态目录。

发生中断先查creation，再以明确的原意图摘要恢复；恢复不重新编译，项目绑定改变后仍保留原角色快照。冲突文件保留并报错，不自动覆盖或重建历史。项目配置投影或执行目录发生漂移需要先修复原登记；切换执行目录不会自动迁移旧任务。写操作串行保留项目修订并非阻塞取得同ID文件锁，任务正忙时明确返回busy；单次原生进程预算30秒；超时后先查询原意图，不自动重试。

对应API为 `POST /api/projects/ID/tasks/preview`（`definition/revision`）、`POST /api/projects/ID/tasks`（加`preview_sha256`）、`GET .../tasks/TASK_ID/creation`、`POST .../tasks/TASK_ID/resume-create`（`revision/intent_sha256`）；写请求沿用本地同源限制及 `X-Ergora-Request: 1`。预览与创建支持Linux/Windows本地文件合同；完整六阶段执行仍使用Linux/WSL2和[正式执行手册](../../agents/backends.md)。
