# F4.2b：提交运行页面独立审查

日期：2026-11-04。审查者：fresh-context `/root/task_submission_console_review`。本报告只覆盖F4.2b；F4.2a精确CI及其终结记录、F4.2c组合旅程和完整F4不在本次通过范围内。

## 结论

- 源码合同：在下述身份与范围内无可报告finding。五态动作、原意图摘要、未知不重发及迟到回包约束符合F4.2b要求。
- 可维护性：通过。逻辑留在任务详情所有者内，复用现有传输、表单、对话框和事实展示；没有引入第二套后端状态机、通用操作框架或轮询。
- 本地验收：通过。终包身份、状态fixture、迟到边界、真实旧修订拒绝、原文件保护及公开说明已续核，无未解决finding。最终文档快照及提交CI/远端仍须按精确候选收口；本结论不等于完整交付已关闭。

## 输入与精确范围

基线：`e63bc8ba9366b9ec798712fb402722f952f990a9`，分支`refactor/architecture-foundations`。先读仓库AGENTS、PLAN最新检查点、[原始F4要求](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)、[F4分片合同](2026-11-03-formal-task-console.md)和[本片记录](2026-11-04-task-submission-console.md)，再读实际diff、未跟踪本片记录、邻近实现与作者验证材料。使用maintainable-project-delivery及其independent-review brief、review-pr技能。

实际生产变更为`src/ergora/data/console/tasks.js`及`app.js`帮助文案；读取了README和USAGE同步差异。源码身份：

|文件|SHA256|
|---|---|
|`data/console/tasks.js`|`057c94f2a57ac95958259bc66b6b6899e386d34a6d3c204a48a32c12add82a15`|
|`data/console/app.js`|`8dac29a924521f72c3134a59e3f465b6caecc7aa34f69ca64c512416d73d7e7a`|

首轮读取时仅tasks.js新增88行；审查期间作者增加`record.reconciliation`事实行、同步帮助和公开说明，已复核新增diff。邻近F4.2a交付/审查文档只有独立终结记账，本次未重新审查其CI或远端。

追踪的既有合同包括`tasks.js`列表/详情/创建与原run查询，`ui.js`的form/modal，`api.js`，`app.js`项目与页面刷新，`web.py`请求模型和路由，`tasks.py`版本保留与start/resume-start，`reference.py`原生进程边界，`reference_task_creation.py`不可变发布校验，`reference_task_submission.py`派发/归属/恢复，以及既有submission和锁测试的相关分支。未修改这些既有合同。

## 源码与结构核查

1. `tasks.js:348–350`只允许published+not_recorded明确start、published+prepared/unknown明确resume；submitted保存原run选择，rejected没有写入入口。POST携当前读取的creation修订及正确种类的digest（`tasks.js:371–374`）。原生边界仍校验不可变创建、项目修订、原intent和task锁。
2. unknown恢复只调用resume-start。既有`reference_task_submission.py:218–229`在attempt存在时仅沿原workflow核对；NOT_FOUND仍返回unknown。页面展示该事实，没有自动start、换ID或从submitted推断六阶段成功。
3. 读取失败移除写确认，写入异常只保留原ID和重新读取入口（`tasks.js:376–380`、`402–407`）。共享form同步禁用原按钮，提交后立即移除旧确认。失败和读取分支均无隐式写入。
4. `view.isConnected`约束切页/项目后旧视图，详情sequence约束同页切任务和重新读取详情，content存活及dialog.open约束关闭/替换，readingSequence约束同一弹窗内的新读取。以上检查对应不同可达生命周期，未发现应删除的重复守卫。所有异步结果显示以及submitted的sessionStorage写入均先通过current检查。
5. submissionDialog只有任务详情入口调用，放在inspect内便于固定task/path/runKey及详情代际；showSubmission与read是该局部交互的内聚私有操作，不需要跨文件抽象。继续使用api、form、modal、facts/disclosure，未发现包装层或虚构复用。
6. 每次明确检查或重读并行发出两个本地GET，确认一次才发出一个POST，没有后台定时器、全列表运行查询或递归重试。既有读取/原生进程有期限及合同大小上限；新增DOM成本与单个任务合同大小相关。关闭弹窗不会中止已发出的请求，但迟到响应不能修改新视图。此为代码成本分析，没有新延迟/吞吐测量结论。

## 已核证据及限制

审查者仅做文件读取、Git差异检查、标准库静态hash/归档核算；没有运行应用/API、浏览器、模型、测试、构建、安装或服务。

- 首包wheel为`862f3f2d5cf0ed1ecdf554b4a4fa37f8c623d6708e6efa4b2a91255af46620ae`。已读`browser-blocked.js`、实际CLI日志、command与result：exit0，29页面请求/8真实POST（两模板各preview/create/start/resume-start），4次start/resume均HTTP400；读取结果为真实prepared、attempt_saved=false。payload使用对应creation与submission digest，0pageerror。浏览器console的4条resource error对应这4个400。
- 上述脚本未保存400响应正文；“doctor阻止”的scope字符串不是独立响应正文证据。其直接证据范围是实际400及prepared/无派发检查点，不能据此宣称真实Temporal提交、六阶段运行或真实submitted回执。
- 终包为`54130609fb4c873e5d38244f2fab5287695db648f5938156284a9ce677c3b393`。审查者独立重算wheel SHA，并将manifest的348文件逐一与源码、wheel、开发非editable安装和基础非editable安装比较，零差异。已读最终构建/两安装和13模块语法command记录，全部exit0；冻结283为作者包核验记录。首包blocked浏览器没有冒作终包重新运行。
- 首轮审查时`browser-fixtures.js`只有提案脚本，command/result不存在，未记为通过；两个审批deadline尝试没有执行。后续实际运行证据见下方续核，未追溯改写此前尝试。

## 终包浏览器与文件证据续核：本地通过

同一独立审查者继续只读核对终包材料，生产两个文件仍分别为上述`057c94…`和`8dac29…`。逐一读取三段实际脚本，静态比对command末尾脚本与源文件一致、CLI的Result与独立result.json一致，三个command均exit0。模拟结果没有扩为真实Temporal成功提交。

|实际材料|独立续核结果|
|---|---|
|browser-fixtures，终包541|40页面请求/5POST均由明确route.fulfill或abort拦截，另5个只读helper；两模板not_recorded→模拟submitted、原run选择、unknown恢复一次且not_found仍unknown、rejected无写入口通过。丢模拟resume回复后先移除确认，再由用户GET恢复submitted；503读取失败无写入口。最终帮助DOM匹配。两模板390px测得页面390、dialog/scroll均352，0pageerror。|
|browser-late，终包541|17页面请求/2拦截resume POST，另1只读helper；持留读取后关闭并替换modal、持留写回复后切任务与切项目，释放后仍保留新的任务/项目/modal，原run选择未变，0pageerror。|
|browser-stale，终包541|10页面请求/1真实resume POST；另一个helper PUT实际将本验收项目revision1改2。旧确认携revision1和原intent，实际400正文为`Project revision changed; reload before the task operation`。旧表单消失，明确重读后current revision2、submitted revision1、同intent和原冻结角色保持，0pageerror。|

已读取新增console日志：ERR_FAILED、503及最后400分别对应主动丢回复、受控读取失败和真实旧修订拒绝，没有把这些resource error记为pageerror或产品成功派发。

已读`verify-native.py`、`verified-native.json`及首版差异，并额外只读核实际JSON/文件：两原creation/submission摘要均与初包一致，原提交revision均1，两任务各七个创建文件与原intent一致，attempt/result/rejection及requests/receipts均不存在。另独立重算F4.2a原35文件、F3原416文件字节摘要，均零差异；作者checker还核对原9个creation intent。首版误读不存在doctor.json的尝试保留，修正版仅报告`doctor_snapshot_saved=false`，没有由此推断ready状态或具体拒绝因果。

审查者实际查看大型任务390px截图，中文及可见摘要可读，截取区域无横向溢出；这是可滚动长表单的部分可见区域，不代表全部字段同时展示。README、USAGE、app帮助与当前架构已同步本片能力和后续CLI操作边界，PLAN及详细计划保留F4.2c/F4.3/F4.4未完成范围。已读取本轮静态文档checker及结果：15份Markdown/339本地链接与锚点、26条README命令parser，missing为空；审查者没有执行该parser或任何应用代码。`git diff --check`本次实际exit0。

以上证据覆盖本片新增行为与可达生命周期风险；没有新增源码或验收finding。现有原生重型回归无需因本次前端接线重复执行，真实成功提交组合仍按F4.2c验收。

## 剩余验收

刷新包含本报告续核段的最终文档身份记录，再核精确提交范围、CI及实时远端。首包862的真实拒绝与终包541的受控状态/迟到、真实旧修订拒绝继续分别记账；不将后续F4.2c真实组合旅程提前计入本片。
