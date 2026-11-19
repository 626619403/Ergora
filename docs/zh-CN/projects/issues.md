# 读取项目工单上下文

简体中文 · [English](../../projects/issues.md) · [文档目录](../../README.zh-CN.md)

普通项目无需安装参考执行器、启动服务或配置模型，就能读取一个明确的工单。先用`project add`登记业务Git仓库，再保存tracker绑定；项目命名空间与API地址分别配置。下面的文件只含变量名称，环境变量的值在启动CLI／Web的同一环境中设置。

```json
{
  "tool": "gitlab",
  "project": "team/subgroup/repository",
  "api_url": "https://gitlab.com/api/v4",
  "token_env": "GITLAB_TOKEN"
}
```

将其保存为`tracker.json`后：

```bash
ergora project show PROJECT
ergora project bind PROJECT tracker --binding tracker.json --revision 1
ergora issue show PROJECT 7
```

`--revision`填写`project show`返回的当前值。GitHub绑定使用`"tool":"github"`、`"project":"owner/repository"`，API默认`https://api.github.com`；默认固定REST版本`2022-11-28`，可用`api_version`显式选择支持的日期版本。GitLab默认API为`https://gitlab.com/api/v4`，支持完整subgroup路径。自托管API须使用HTTPS；HTTP仅支持loopback。公共工单可省略`token_env`匿名读取；配置了变量名但环境缺值时明确失败。未知字段和URL内凭据被拒绝，接口不跟随重定向。

`issue show`参数是GitHub仓库内number或GitLab项目内iid，响应另存全局native ID。返回完整标题／正文／标签、原生状态与更新时间、ETag（若有）、原始响应SHA256、API地址／namespace、项目修订／配置摘要和本次观察时间。正文保留为文本，标记`context_only:true`；`show`不保存，需要持久化时使用下面的`capture`。不扫描远端列表、不读取评论、不派工或回写。ETag／更新时间／摘要仅为观察线索，不提供写入CAS，也不构成任务批准。

HTTP入口为`GET /api/projects/PROJECT/issues/7`，与CLI共用同一用例。原工具绑定页面按schema显示tracker配置；工单专页见[页面读取说明](#在页面读取与保存工单)，observe列表按计划继续。已正式注册的项目只允许读取其登记的kind／namespace；改变来源绑定会产生新项目修订，不修改旧任务或参考注册。正式注册尚未包含API host，后续跨host派工必须另行核准身份，不能直接复用旧claim。

只接受普通GitHub issue／GitLab project issue；GitHub PR、GitLab非issue类型或不兼容响应明确拒绝。每次一个GET、20秒socket I/O超时、1MiB完整响应上限，无自动重试；这不是整个调用的20秒wall-time保证。认证／不可用／重定向／超限／截断等失败不会伪装成空工单。详细接口取舍和未验自托管范围见[接入指南](../../projects/issues.md#project-issue-sources)。

## 保存工单与关联任务上下文

`capture`显式读取并保存一份完整、不可变的工单上下文。后续读取已保存快照不需要当前tracker或凭据可用；所有命令使用同一控制目录`--home`。先查看项目当前revision，再执行：

```bash
ergora issue capture PROJECT 7 --revision 2
ergora issue snapshots PROJECT --limit 20
ergora issue snapshot PROJECT SNAPSHOT_SHA
```

capture返回`snapshot.sha256`、`snapshot.first_observed_at`和本次`observed_at`。SHA绑定完整观察与当次tracker配置，包括API基地址、命名空间、工单number／iid、native ID、正文、响应摘要及项目修订；配置只保存凭据变量名。首次保存时间不参与内容SHA，相同内容／配置重读返回原快照，工单更新产生新快照。GET期间修改配置仍保存明确标注原修订的观察。没有保存原HTTP响应正文，`response.sha256`仅是该响应的字节摘要。

要将快照关联到已有任务，先按原流程`task preview → task create`发布合同，再用`task creation PROJECT TASK`读取其`intent_sha256`。随后显式指定这个SHA、快照SHA、任务ID和关联原因：

```bash
ergora issue link-task PROJECT SNAPSHOT_SHA TASK --creation-sha256 CREATION_SHA --revision 2 --reason "本次工作参考的来源"
ergora issue links PROJECT --snapshot SNAPSHOT_SHA --limit 20
ergora issue links PROJECT --task TASK --limit 20
```

一份快照可关联多个任务，一个任务也可显式关联后续快照。重复同一关系返回原原因／时间，即使原请求的项目修订已过时；新关系仍要求当前项目修订、目标creation已published且SHA精确相符，pending先走原resume-create，conflict先核原文件。`created_revision`是创建时的项目修订；新工作版本沿原合同使用新任务ID。旧任务输入／批准不被改写，关联不启动任务，也不自动让运行中的Agent读取资料。输出的`operator_asserted_context / context_only / execution_authorized:false`表示操作者声明的上下文关系；旧正式来源没有API host，因此关联不能证明原生来源归属或替代派工准入。

两个列表只返回有界metadata，完整正文通过单份snapshot读取。`--limit`为1–100；`next_cursor`非空时原样传给`--after`，并保持相同项目／过滤条件。分页期间新增且排序在游标之前的内容需要从首页重读；这是发现已保存记录的查询，不是固定视图或一次派工去重。capture响应丢失后可查询本地列表；再次capture可能观察到更新内容。

HTTP与CLI共用相同用例；POST沿用本地Origin及`X-Ergora-Request: 1`保护：

|操作|HTTP入口／正文|
|---|---|
|保存|`POST /api/projects/PROJECT/issues/7/snapshots`，`{"revision":2}`|
|快照metadata列表|`GET /api/projects/PROJECT/issue-snapshots?limit=20&after=CURSOR`|
|完整快照|`GET /api/projects/PROJECT/issue-snapshots/SNAPSHOT_SHA`|
|关联|`POST /api/projects/PROJECT/issue-links`，`{"snapshot_sha256":"…","task_id":"TASK","creation_sha256":"…","revision":2,"reason":"…"}`|
|关联列表|`GET /api/projects/PROJECT/issue-links?task_id=TASK&snapshot_sha256=SNAPSHOT_SHA&limit=20`，两过滤条件可选，可带`after`|

快照与关联保存在控制面的SQLite中，由原`state backup / verify-backup / restore`完整离线备份恢复；当前数据库为schema v6，升级先停止旧进程并保留旧库备份，旧客户端不能写新库；见[有效期与升级说明](../improvement/memory.md#记忆有效期与检索)。完整备份仍要求停写、同平台及原home；外置执行目录须另行保存，不会从上下文关联重建任务。来源派工见下一节，候选评论见[回写说明](candidate-actions.md#为已导出的候选发布工单评论)，来源阅读可使用下节页面；其余工单动作页面按[接入指南](../../projects/issues.md#project-issue-sources)分片交付。

## 在页面读取与保存工单

在“工具绑定”选择当前项目的 GitHub 或 GitLab 来源后，打开“工单来源”，填写工单 number／iid，点击“读取当前工单”。平台读取必须明确点击；进入页面只读取本地快照列表。标题、完整正文、native ID、API 来源、项目修订和响应摘要以文本显示，完整记录可展开查看。

点击“重新读取并保存快照”会再次读取平台，并按当前页面持有的项目修订保存；平台内容可能已更新，应核对返回的完整快照。保存不会创建或启动任务，也不发送评论、标签或 PR／MR。项目修订变化时先点顶部“刷新”再操作。保存结果未确认时先“重新读取列表”核对，避免把响应失败当作未保存。

历史每页最多20条，“上一页／下一页”沿原游标浏览，“查看快照”完整离线读回。列表按内容摘要排序，新增内容可能出现在之前的页，可重新读取首页。历史快照保留当时来源；项目改用其他来源或manual后仍可阅读，不代表平台当前内容或当前工具绑定。manual禁用外部工单读取。正文不执行HTML／Markdown，不能通过工单文本扩张Agent权限。点击已保存快照的“以此快照准备正式任务”可转到原正式任务表单，页面只临时承接本项目摘要；刷新后可从快照重新进入或自行粘贴SHA。来源页本身只负责阅读，候选动作继续使用下文CLI。

## 从工单快照创建来源任务

页面入口：在“工单来源”查看已保存快照，点击“以此快照准备正式任务”，再点击“从所选快照预览与创建”。也可在“正式任务”的“预览与创建”手动填入可选来源SHA。点击“读取来源快照”，完整离线核读正文和来源，工单编号随之固定。修改摘要后必须重新读取；“清除来源选择”恢复无来源入口。来源读取失败不会自动转为无来源任务。

选择已登记开发模板并编辑完整输入，在“本任务Agent来源”选择“完整manifest · 组合执行与审查”，沿[正式组合选择](../../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)核包、分配工作单元、选择每叶后端和执行信任。预览显示来源SHA和完整冻结文件；审阅后明确创建。服务端重新核当前绑定、登记来源及项目修订，历史快照可读不代表当前可创建。预览和创建不连接工单平台、不启动Agent、不回写工单；需另行提交运行。未知创建沿原ID读取／恢复，不重新capture或改ID重发。

为新任务固定工单正文时，使用`task-definition-v3`；它支持治理和大变更模板，要求显式`work-units-v2`的执行／审查组合。先按[专长执行者配置](../../definitions/workflows/contracts.md#specialist-writers-and-original-work-units)准备完整的`task-definition.json`，其中已有真实manifest、摘要、工作分配和逐实例后端。再保存快照，将以下命令中的项目、编号和修订替换为当前值：

```bash
ergora issue capture my-project 7 --revision 2 > issue-capture.json
python - <<'PY'
import json
from pathlib import Path
definition = json.loads(Path('task-definition.json').read_text(encoding='utf-8'))
saved = json.loads(Path('issue-capture.json').read_text(encoding='utf-8'))['snapshot']
definition.update(schema_version=3, task_id='issue-7-r1',
    issue_id=saved['payload']['observation']['source']['issue_id'],
    source={'snapshot_sha256': saved['sha256']})
Path('issue-task.json').write_text(json.dumps(definition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
ergora task preview my-project --definition issue-task.json --revision 2
# 检查 files/task.spec.json 中的完整 issue_source、项目配置、专家与权限后，使用本次摘要：
ergora task create my-project --definition issue-task.json --revision 2 --preview-sha256 PREVIEW_SHA
ergora task creation my-project issue-7-r1
ergora task show my-project issue-7-r1
```

快照与当前执行配置必须属于同一项目、provider、完整API地址及namespace，number／iid也须匹配。来源相同时，捕获后更换Agent或token变量引用不强迫重新读取工单；捕获修订与本次创建修订分别保存。读取保存的快照和预览无需tracker在线或token，仍须有登记项目及选定的完整组合。API host/path或项目切换后应重新捕获，不以网页URL或旧hostless登记推断来源。

新创建使用creation3／正式信封v7，完整来源进入原始执行输入及每次work／review材料，祖先Skill与权限仍由原组合控制。发布后不再依赖控制库中的该快照、当前绑定或外部正文；`resume-create`按原intent SHA恢复，不重新选择来源。工单更新后如需另一份工作，用新task ID和新preview；旧任务、批准和B0上下文关联保持。

来源任务按冻结选择准入：只检查实际inventory／plan角色、工作／审查叶的程序与配置、所选MCP模式，以及原Git、timeout、Python和已确认的当前容器执行条件。A2A、MLflow、LangGraph及未选的默认implementer／reviewer不成为此入口的必需依赖。先明确启动`temporal worker executor`，再按[正式提交](../development/run-and-recover.md#提交正式任务与恢复未知结果)执行start；可信检查、策略、Temporal连接和共享工单占用仍走原流程。程序可用不证明认证、配额或worker就绪；实际失败会保留具体依赖和原提交状态。unknown恢复只查询原ID，不重发，也不因当前工具变化重新准入。旧v1–v6保留原安装级doctor。

安装并重启本版worker／executor后才接收v7队列；真实Agent消费须查原调用材料与回执。单文件1MiB、stage／prompt各1,000,000字节、全部祖先资料和动态产物限额保持；静态必然超限在预览拒绝，后续产物超限在原阶段拒绝，没有隐式摘要。v7的证据／handoff保存完整`contract.original_input`并核来源／原admission SHA，合计仍受原1MiB索引与包manifest限额；旧v1–v6和旧交接包不迁移。
