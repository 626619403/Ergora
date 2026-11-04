# F4.3b：网页计划审阅、批准与原决策恢复

日期：2026-11-04。状态：F4.3b完成。生产提交`c54230eb8a6d3468ef33e6365c874a4e3a2407d6`已推送并核实时远端；最终4fcdb9包及本地验收、精确CI41797567476双OS必要步骤和[独立终结审查](2026-11-04-task-approval-console-review.md)均通过，无findings。下文历史检查点保留各自当时范围；完整F4仍待取消/对账/导出与F4.4。

## 目标与边界

把已有计划读取和精确批准合同接到正式任务页，让用户在完整审阅材料后明确决定，并在未知回复或重开页面后按原decision ID查询/恢复。只新增页面消费者，不复制状态机、批准算法、owner回执或网络重试。取消、外部清理、候选导出和通用日志留给F4.3c/d、F4.4。

沿用`tasks.js`内的正式任务详情所有权以及现有api/ui原语：`node/pre`将模型材料作为文本，`form`提供显式确认，`modal`提供局部工作区。现有CSS已对pre及长标识换行，不提前引入新库、通用操作框架或样式层。只有实际视觉反例才作最小样式修正。

## 页面行为

1. 从成功查询的原run待批状态提供“审阅计划与批准”。固定所选run及状态返回的plan SHA，调用F4.3a GET；完整展示三材料、逐材料摘要和回执身份。缺失、过大、状态改变或传输失败时没有批准按钮，只能重新读取原状态/记录。
2. 用户填写稳定decision ID并先读取该ID的原批准记录。只有`not_recorded`且本次完整材料已读，才提供“确认批准此计划”；正文使用读取到的项目当前修订、固定run/plan和`confirm: true`。新确认发出前保存该ID的浏览器选择并锁定输入；关闭页面不撤销已发出的操作。
3. 已有decision不被新计划覆盖。若材料工作区查到既有记录，转到原decision查看，而不在另一份材料旁恢复旧计划。正式任务详情另有按原ID读取入口，不依赖当前仍处于待批phase。
4. 原记录显示其run/plan/intent/owner receipt/期限和`not_recorded / prepared / unknown / requested`事实。prepared可明确恢复原意图，unknown只明确对账原信号；requested不再提供投递按钮。所有恢复只调用已有`resume-approve` API，不创建替代ID或自动重发。
5. 结果及错误都保留原ID入口。requested仅是投递事实，实际采纳与进度需再次查询原run；不把本地回执或浏览器状态当批准生效。原ID选择按项目/任务保存，后端仍是权威；清空选择后可手工输入原ID取回记录。
6. 编辑decision、改run、切任务/项目、关闭/替换对话框和新请求代际都会使旧回包失效；迟到回复不能恢复旧确认按钮、覆盖另一任务或在DOM外继续写。网络请求是否已发生由后端记录决定，页面关闭不声称撤销。

## 验收与交付

- 源码语法、必要架构/既有批准合同和非editable资源身份检查；没有后端行为变化时不机械重复共享重型回归。测试脚本保留在本片私有checks目录，浏览器截图按Playwright技能进入`output/playwright/`。
- 真实浏览器核两模板材料、显式新决策、重复读取及重开恢复。只对本次专门创建的两个演示run实际批准，各最多一个有效信号；保留A的54文件摘要及原112事件前缀，新增操作/后续job另计，不再要求整个目录仍只有54文件。
- 至少一条真实POST成功后丢弃浏览器回复，重载后按原decision取回实际记录，确认没有第二个信号。prepared/unknown及其恢复、旧修订/错误计划/迟到响应可用明确标记的受控UI传输验收，不能记为原生信号已投递；不为造反例篡改两原任务证据。
- 桌面和390px实际查看材料、稳定ID、确认/错误说明；无pageerror、无意外写请求、无横向溢出。关闭/替换/项目切换的迟到边界及无浏览器选择时后端原记录恢复分别记账。
- README、使用手册和当前架构同步实际页面行为；记录准确包/请求/原run/决策身份。新的fresh-context独立审查检查正确性、所有权、复用、必要守卫和成本；修正后提交推送，再核精确两OS CI和实时远端。

首轮实现只改既有tasks.js；README/使用手册已同步。尚无本片浏览器验收或独立审查结果。A的精确CI与终结审查先收口，再交付本片；完整F4/F5/G0未完成。

## 实施检查点

待批状态按钮、完整材料读取、稳定decision原记录检查、显式批准/原意图恢复及不确定回复入口已首轮接入；所有网络写仍调用原API。选择/代际/内容连接保护沿现有详情所有者，写前保存原ID并锁输入。`node --input-type=module --check`实际exit0。本片独立开发/基础venv正在准备，不覆盖A的wheel或两安装；当前工作树的页面及README变化不能当作A提交14100cd的发行身份。浏览器及后端实际决策尚未执行，不宣称页面验收通过。

初包SHA256 `6524aee986d0f0d6e9e6a10426574a8899862c36e6a57e2fb48360cc589c3135`：348源码/wheel/两专用noneditable安装一致，283冻结保持，基础无SDK且开发环境含SDK；模块语法通过。第一轮真实只读浏览器已取得治理三材料和not_recorded原记录，但390px dialog scroll542>352而exit1；没有点击批准。独立DOM探针定位为三份材料描述p中的64字符SHA，pre/既有facts未溢出，截图已查看；已将摘要移入现有facts布局，不增加CSS或削弱断言。初包、源码、失败脚本/命令和截图均保留，修包/两模板完整重验待执行。

恢复核验：修后wheel SHA256 `f81edfd0983604c98736d620c24314f8a1e7b29467c90d6dc91f36366f500bf1`已在本片两专用noneditable环境安装；348源码/wheel/两安装逐字一致、283冻结及无SDK基础安装/模块语法通过。`check-browser-readonly-fixed-command.json`实际exit0（22.71秒）：两真实原run的六份材料完整正文与API一致、原decision读取及重开入口通过，22请求全GET、零拦截/零pageerror；两个390px页面scrollWidth390、dialog352/scroll352。请求/正文/DOM身份、脚本/CLI原输出及桌面/390px截图保留在本片私有checks与`output/playwright/`。初轮溢出失败继续保留，不将只读结果记为批准成功。下一步验收prepared/unknown、迟到与读失败边界，再在两个专用演示run明确批准并核原ID恢复和精确信号。

受控边界：`browser-boundaries.js`实际exit0（24.39秒），40页面请求/4个拦截POST、零转发写入、零pageerror。prepared→unknown/not_found→requested沿原intent恢复；既有决策从材料区转到独立原记录；完整材料失败/原记录503均无确认；编辑ID、关闭替换、换run及跨项目迟到写回复均不恢复旧按钮或覆盖新工作区。模拟旧revision的400保留原ID、不自动重发。requested的390px宽度仍为390/352/352，截图已实际查看。以上是明确标记的UI传输夹具，不是原生signal成功；正式54文件在此段后仍逐字保持。当前非editable包既有架构边界8项通过（0.24秒），不重复已通过的重型原生回归。

## 真实批准与恢复

`native-before`直接查询Temporal确认两个原run仍各112事件、零signal；两份execution-plan/ownership-map/rollback-plan已逐份审阅，范围、工作单元、可信检查和回退与本次两个专用演示请求一致。随后`browser-actual-approval.js`实际exit0（54.28秒）：57页面请求、2真实POST、零状态fixture/零pageerror。每项目均先取完整计划、读取原decision未记录，再明确确认一次。large-change的POST经`route.fetch(maxRetries=0)`实际返回200/requested后主动丢弃页面回复，页面显示未确认；reload后按原ID取回requested，不重发。两模板均重复读取两次、清空decision浏览器选择后reload并手工输入原ID，取回逐字相同的后端记录；requested保持`approval_accepted/execution_success=null`，390px无溢出。

|项目/原任务|原run|decision/owner回执|原意图SHA256|
|---|---|---|---|
|governance-f4c / governance-f4c-normal-r1|01a1a4e2-67b9-7bf3-986d-9dc0437ff134|owner-f4b-one / owner-6f98669287fc49b1aef7a60c86f01b53|86ebb2dc161db3996740c0fd6e44c8bc41e279505bb2eebf7e6e9039f8ee480e|
|large-f4c / large-f4c-normal-r1|01a1a4e2-961d-7959-83b1-b962ce3d9767|owner-f4b-one / owner-50e0c5f597744c3bbb8d966485fef9cc|96631eb6d68cbad5b4e635259e42b490d9afcdff34498ef0c9ab89eb830636f0|

`native-after`直接读回完整history与本地intent/attempt/result/owner receipt：两run各且仅一个`approve_plan`，均为事件113，精确绑定原run、对应plan/request SHA和owner receipt；intent/signal SHA、owner正文与检查点一致。原54文件及两history原112事件前缀逐字保持。2026-11-04 06:35 UTC快照时两个原run仍RUNNING、207/158事件；这些是采样事实，不代表六阶段已完成。后续产物另增，不把整个native目录仍只有54文件作为验收条件。

上述三个成功浏览器段共119页面请求：4个受控POST不转发、2个真实批准POST；受控段另有1辅助只读计划请求。完整脚本、命令/CLI Result、逐请求正文和原history保留在本片私有checks。原f81edf包和身份已另存`approved-dist`/`approved-package-identity.json`；自查发现应用内帮助仍称批准只走CLI，正在仅修`app.js`该文案并重建最终发行，`tasks.js`行为不改。最终包只读恢复/帮助与身份仍需重核，不能直接借原包记为已验。

最终包`4fcdb979ef45cb68ebf03dba075b58bcbd114bb00b4aab9f3d65437d49f5ffbd`已构建/两noneditable安装、348文件/283冻结/无SDK基础及13模块语法通过；与已验f81edf包唯一文件差异为`data/console/app.js`帮助文本，`tasks.js`逐字相同。核原HTTP PID/命令/属主后SIGTERM，PID/端口退出确认，再用同端口启动最终包HTTP。首轮只读脚本等任务标题超时，原HTTP记录有一次submission子进程超时400；后续两项目直接GET均200，未确定这次暂时超时根因，不记为已修生产缺陷。v2减少脚本重复选择后两原记录与run读取完成，但在390px点击原本隐藏的帮助按钮而失败；保留脚本和失败输出，v3只在帮助前切回桌面重验。以上失败不计入成功请求总数，未重发批准或修改后端超时。

`browser-final-readback-v3`已实际exit0：25页面请求全GET/零pageerror；最终包两原decision均requested且无再投递按钮，390px无溢出、桌面新帮助可见。直接查询的两原run均为终态`REVIEW_READY`；本片只记录该状态事实，不借此关闭尚未实施的取消/导出页面或F4.4综合验收。四段成功浏览器共144页面请求/6POST（4受控、2真实），与前述三个段及辅助请求分别可追踪。两次失败旅程保留各自范围，不混计成功总数。源码自查及静态文档核查后交新fresh-context审查；精确提交/双OS CI/实时远端仍待完成。

结构与成本：生产代码只扩展现有`tasks.js`详情所有者和`app.js`帮助，不新建状态机、包装接口、UI库或持久调度器。结果失效守卫分别对应实际关闭/替换/编辑/跨项目反例；网络操作复用原API。没有自动轮询或浏览器重试；只读重复操作与后端超时均如实记录，不据少量旅程宣称吞吐、费用或性能提升。最终HTTP及专用执行栈保留给紧接的F4.3c/d/F4.4，真实原run已闭合；取消和导出尚未在页面接入。

## 独立审查与交付检查点

新的fresh-context审查者已亲自写入[本地审查报告](2026-11-04-task-approval-console-review.md)，需求符合性/可维护性均通过，无findings。独立重算348源码/wheel/两安装、283冻结、六材料、144请求/6POST及原回执/意图；实时SDK核两原run均COMPLETED、329/348连续事件、各仅事件113一个精确信号，原54文件和各112事件及早期after快照整个前缀保持；独立读取outcome均REVIEW_READY。13模块语法、范围9文档329链接/锚点和27README命令通过。审查者仅写报告/只读核验，不发信号或重复重型回归。自动审批服务曾使报告首次落盘超时，后经单文件补丁成功；这是工具服务deadline，不是安全拒绝。

下一片取消页面计划单独保留，不纳入本次B提交。当前提交归档/推送、精确两OS CI和同片独立终结复核仍待完成；完整F4尚未完成。

B已提交推送`c54230eb8a6d3468ef33e6365c874a4e3a2407d6`，实时远端一致。12文件/归档348包文件与最终4fcdb9身份一致，同片独立提交/包/远端复核通过。精确CI[41797567476](https://github.com/626619403/Ergora/actions/runs/41797567476)首次官方HTML仍In progress，不能关闭本片完整交付。随后工作树的c1源码与包独立记账，不改变B提交和验收身份。

最终交付：精确CI41797567476的Windows126465188338四必要步骤、Ubuntu126465188976三必要步骤均success；原run/job HTML、完整commit/selectedJobId及每项log URL已核。同片独立终结报告重新核原HTML和实时远端完整c54230e后通过，无findings。B完成；C1的独立a4081f包/新页面验证另记，不纳入B身份。
