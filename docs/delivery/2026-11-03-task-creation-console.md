# F4.2a：正式任务预览、创建与原 ID 恢复

日期：2026-11-03起，2026-11-04续。状态：F4.2a完成，已推送e63bc8b且精确CI与独立终结审查通过。前置 [F4.1 只读控制台](2026-11-03-formal-task-console.md)已完成；其原候选 `11e89cf` 的 Linux CI 超时取消保留，[V4](2026-11-04-ci-regression-progress.md)候选`2137a95418879d48cce557016caa5c7f0d6a6a1b`保持同一应用树，新精确CI41679431542两OS通过。本文是本片的实施与恢复入口，实际进度由 [PLAN](../PLAN.md) 记录。

## 行为和范围

用户可从正式任务页选择已保存的开发草稿，填写任务 ID、工单或本地标识，并审阅输入；也可沿已有模板接口取得输入后编辑。仅允许项目已登记的 `repository-governance` / `large-change`。训练优化继续使用已有独立合同和入口。

预览先在服务端编译，页面展示项目修订、模板、任务 ID、冻结角色、请求/合同、完整输入及 preview SHA。修改任务字段、输入或选择后废弃旧预览及确认控件。明确确认只创建冻结合同，不自动提交运行；成功以原 creation 状态为准。

创建中断或回复未知后，先按原任务 ID 读取创建记录，再明确恢复原 intent。未完整发布的任务不一定出现在正式列表，因此按 ID 读取与恢复须始终可进入；同一浏览器会话只保留任务选择，不缓存成功、意图或其他权威状态。

F4.2b 再接提交、submission 与 resume-start；本片不接批准、取消、对账、导出、日志或新的后台调度，不修改原编译器、数据格式或创建状态机。

## 已核合同与所有权

|界面动作|既有消费者和参数|保留的语义|
|---|---|---|
|读取模板/已有草稿|`GET /api/templates/KIND`、项目 dashboard 的 drafts|页面只取得输入；使用原工作流编辑器保存的内容，不复制编译规则|
|预览|`POST /api/projects/ID/tasks/preview`：definition、revision|definition v1 含 task_id/task_type/issue_id/input，可选 starting_sha；server owns schema、项目归属、冻结选择和摘要|
|确认创建|`POST /api/projects/ID/tasks`：上述参数及 preview_sha256|确认的是实际返回的快照；意图先于原生文件发布，不启动 Temporal|
|读取创建记录|`GET /api/projects/ID/tasks/TASK_ID/creation`|not_recorded/pending/published/conflict 分开；不从目录存在推断成功|
|恢复创建|`POST .../resume-create`：当前 revision、原 intent_sha256|沿原不可变意图补齐；不重新编译、覆盖冲突文件或更换 task ID|

服务端仍沿 `web → tasks → reference.task_creation → reference_task_creation`；没有新的 API、表或副本。前端优先在 `tasks.js` 的页面所有者内实现局部对话框及其私有流程，复用 api/ui 的表单、modal、文本 DOM、facts/disclosure；不为单一消费者建立通用操作框架。必要拆分须有明确的生命周期/阅读收益。

预览、创建和恢复各自的异步结果受本次对话框和页面存活、请求序号约束；关闭对话框、替换对话框、切项目或离开页面不得恢复旧确认界面。按钮禁用只防当前页面重复点击，服务端锁/意图仍拥有跨请求幂等性。已经发出的操作不因关闭页面而撤销；未知结果引导读取原记录。保存与刷新继续遵守 F4.1 的快照归属边界。

写操作携带既有同源请求头；凭据沿原环境变量读取，页面不增加密钥输入或保存。错误直接显示，不自动安装、重开服务、重试创建或以新 ID 绕过原意图。

## 实施与验收节点

1. 在正式任务导航增加“预览与创建”和“按 ID 读取创建记录”。表单选择已登记开发模板/兼容草稿，输入完整定义；旧预览在编辑后立即失效。
2. 展示服务端预览的冻结身份、角色和完整合同；明确确认后创建，显示原结果和查看新任务入口。提供按 ID 读取、pending 的显式恢复及 conflict 的可辨识错误；网络失败不当作未创建。
3. 构建并以非 editable 包验收，核源码/wheel/安装和冻结 283 身份；后端未改时不重复完整重型回归来声称验证新 DOM。
4. 在独立持久项目中用真实 API / 浏览器走两模板预览→创建→读取；重复创建、旧 revision、预览变化、合同冲突与原 ID 恢复分别验证。受控响应只验证界面分支，真实文件中断验证服务端恢复，两者分开记账；不修改 F3 的原任务。
5. 检查对话框关闭/替换、项目切换和迟到回复，以及桌面/390px；明确浏览器写请求数量及实际转发范围。失败脚本和中间包保留原身份。
6. 更新 README / USAGE / 当前架构、活动记录及 PLAN；启用新的独立审查者检查代码所有权、复用、生命周期和有界成本。修正后提交推送，核精确 CI / 远端，再关闭本片并推进 F4.2b。

## 当前实施检查点

首轮源码只修改 `tasks.js` 和任务表单的局部 CSS。页面所有者内增加预览/明确创建、创建状态展示及按原 ID 读取/恢复；复用已有模板、草稿和四个创建 API。编辑废弃预览，已发出创建后锁定编辑，错误只提供原 ID 查询入口；未自动启动运行。结果受页面、对话框内容连接状态、dialog.open 和本次请求序号约束。已发布结果刷新任务选择/列表与详情。仅训练项目明确提示使用独立入口。

上述为首轮检查点。后续补充创建发出前保存原任务选择、合同未完整读取时的原ID查询入口，保证重载后还能查原记录；app使用指南、README、USAGE和当前架构已同步。生产范围为`tasks.js`、局部CSS及app帮助文案；没有Python、测试、依赖、CI或冻结reference改动。源码比较基线为`2137a95418879d48cce557016caa5c7f0d6a6a1b`，V4与本片保持独立提交。

## 实际验证与身份

私有原始材料位于`.ergora/checks/f4-task-creation-console/`。独立持久控制/配置/执行目录中注册两个新项目：开发项目允许两开发模板，训练项目只允许训练模板。只读复用已核参考安装；未复制凭据、启用执行、启动Temporal/worker/executor或调用模型。可信fixture检查只配置，不将其算作六阶段验收。

初包保存在`initial-dist/`，身份JSON为checks根目录的`initial-package-identity.json`，与当时基础安装逐文件一致；其浏览器材料保留以下范围，未改写为最终候选重新执行：

|材料|结果与范围|
|---|---|
|browser-normal|34页面请求含3真实预览/2真实创建，另2只读辅助检查；两模板快照=服务端、编辑清确认、发布不启动、选择重载、390px页面/弹窗无溢出、0 pageerror|
|browser-duplicate-stale-preview|6请求/3 POST；显式重复创建返回同一原意图，另保留修订1预览供后续旧revision验证|
|prepare-recovery / recovery-environment|在独立原生子进程中受控中断真实发布，保存原意图及3份合同；另一个任务修改一份实际文件形成conflict，再将项目reviewer绑定变为修订2。不是HTML模拟状态|
|browser-recovery-real|20请求/2 POST；旧revision创建400且锁定表单，按原IDnot_recorded；真实pending沿原意图发布，当前修订2/原创建修订1及旧角色保持；实际conflict不提供恢复/覆盖；重载恢复选中新任务，0 pageerror|

首个正常脚本在实际发布治理任务后，错误地在打开的modal外等待不可见标题而超时；原脚本/CLI/命令保存在`initial-normal-attempt/`。修正等待顺序并在新浏览器会话使用新ID取得上述正常结果，没有删除原已发布任务或把失败当成功。

包含原ID重载保护及帮助文案的新包SHA256为`421c81f203292610173a0885163c15297e018df93b11c805adede1f5328ed7b7`；348文件=源码=wheel=开发/基础两非editable安装，冻结283及13模块语法通过。`package.py`保留构建/安装/语法实际命令和原始日志。`browser-normal-final`在此包重跑两模板：34请求含3预览/2创建、另2只读检查，当前冻结修订2，两份完整预览与服务端一致，390px页面390/弹窗352均无横向溢出、0 pageerror。

最终包还完成`browser-lost-response`：8页面请求/2POST，`route.fetch`真实发布后`route.abort`丢失回复；仅一次create，reload保留原ID，GET查回同intent的published。`browser-late`为14请求/5POST：真实preview回包持留时编辑，旧确认不恢复；关闭/替换对话框后旧preview不覆盖lookup；真实create已published后持留回复，切训练项目并打开新提示，再释放旧回复，不改项目或新提示，返回原项目仍可查同intent。均0pageerror。最终normal/lost/late合计56页面请求/12POST，未混入初包计数。

桌面治理、390px大型任务和原ID丢回复恢复截图已实际查看，中文可读、可见区域无横向问题；长表单截图位于对话框中部滚动位置，不声称整份表单同时可见。[独立源码/合同/维护/成本审查](2026-11-04-task-creation-console-review.md)无高置信finding，报告已落盘。

工具部分恢复后，`verify-created.py`已实际执行并保存`verified-created.json`：9份intent中8份published，七文件内容及result的原intent/compiled/各文件canonical SHA逐项一致；1份conflict保留task.json真实差异及其余2匹配/4缺失，无result。35份中断前既有文件与F3原416文件字节SHA保持，原pending冻结修订1及旧reviewer保持。最终421c81包348文件再次核源码/wheel/两安装一致。此为只读静态核算，不是执行验收。

`browser-final-readback`已在重新打开的浏览器会话取得7真实GET/0POST：实际不完整conflict合同的错误面板保留原ID，按钮打开readonly原ID查询，实际conflict无resume；原pending已published且冻结修订1/当前2和旧reviewer保持，app新帮助文案在实际DOM中可见，0pageerror。没有重跑已成功的正常/丢回复/迟到旅程，也未把最终只读检查写成重新执行初包恢复。

当前文档终核为13份Markdown328本地链接/锚点及26条README命令parser通过，`git diff --check`通过；脚本和原结果复用F4.1 checks下的`check-documents.py`/`static-documents.json`，不改写F4.1历史计数。当前独立续核及本片提交推送/精确CI尚待收口。此前自动审批服务deadline阻止的命令保留未执行范围；仅以成功工具原输出和产物登记新检查，不追溯改写。F4.2b提交执行和F4.2c组合验收未实现，不把当前创建页面写成完整F4交付。

最终交付：14文件提交`e63bc8ba9366b9ec798712fb402722f952f990a9`已推送且实时远端一致，生产三文件/文档11文件，无Python/测试/依赖/CI变化。首次SSH传输关闭后明确重核远端仍2137，再一次显式重推成功。精确[CI41763676211](https://github.com/626619403/Ergora/actions/runs/41763676211)两OS全部必要步骤success；本片ci/保存官方run、job-group和两job HTML、selection/status及实际取证脚本。GitHub此次列表由server HTML及独立job-group返回，旧JSON脚本not_listed和辅助解析失败均保留为未通过尝试，不当作未触发CI。最终verify实际exit0，selectedJobId和精确提交log URL均核。

[独立终结审查](2026-11-04-task-creation-console-review.md)已核14文件、348 Git blob=421c81包、13提交文档=终版静态身份、两job原步骤和实时远端，0未解决finding；F4.2a完成。下一项为[F4.2b明确提交与恢复](2026-11-04-task-submission-console.md)，之后F4.2c；完整F4未完成。
