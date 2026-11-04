# F4：正式任务控制台与运行视图

日期：2026-11-03。前置[F3 CLI/API](2026-11-03-f3-completion.md)已完成并推送449a5be，生产/测试基线7139d1a。需求来自[实施计划F4](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)及[LC1页面研究](../research/2026-11-02-low-code-editors.md)。本记录是F4实现与上下文恢复入口，不将分片进度视为完整F4通过。

当前F4检查点（2026-11-04）：F4.1、F4.2a/b/c、F4.3a/b/c1均完成各自交付。[c2对账页面](2026-11-04-task-reconciliation-console.md)本地验收/独立审查及401bacb提交归档核对通过，SSH推送认证失败，精确远端CI未取得。当前[d候选导出页面](2026-11-04-task-export-console.md)首包348资源/两安装/冻结283/13语法/架构8项及受控两段70请求/12拦截POST通过，真实两候选单次导出/丢回复恢复及原文件/历史/ref/租约核验本地通过，四段174请求/14POST；新独立本地审查通过、无findings；提交/远端CI待完成；F4.4尚待后续。本段优先于下面历史过程状态。

F4.1历史候选包为`3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021`，最终页面及保存/刷新反例均已验证；416文件前后相同，五原run闭合及本次专用栈正式shutdown已核。初审R1/R2及中间复核R3已修，[新的独立最终审查](2026-11-03-formal-task-console-final-review.md)已确认代码与本地验收通过；生产候选`11e89cf44eb29fe9064bd0015417cf6bc54fdc5e`已提交推送，其后精确CI/远端状态见末尾。以下过程中的旧包身份与未完成状态保留其当时范围。

## 分片与验收

|节点|行为与复用|验收及状态|
|---|---|---|
|F4.1 只读任务与原运行检查器|主导航/项目总览进入正式任务；使用现有tasks分页、详情、submission和status API，显示冻结输入/角色/工作单元及固定run的原状态/候选/结果。刷新/返回同一浏览器标签页保留项目/任务/run选择，执行事实重新读取|完成；R1–R3关闭，11e89cf源码与V4的2137a95同源应用，精确CI41679431542双OS及最终独立复核通过；原Linux取消记录保留|
|F4.2 从草稿到创建与提交|复用工作流输入草稿、F3 preview/create/creation/resume-create与start/submission/resume-start；确认界面展示冻结内容/修订/摘要，不将草稿校验当正式创建|a/b/c均完成；a/b各自精确CI及独立审查通过，[c真实组合旅程](2026-11-04-task-console-journeys.md)完成两原run/等待批准及重开验收，独立审查通过，文档581144c已推送并核远端|
|F4.3 人工待办与精确操作|为审阅提供有界且身份绑定的计划材料读取，沿原approve/cancel/reconcile/export及恢复用例操作；固定原run/plan/candidate/ID/revision与明确确认|a计划读取、b批准和c1取消页面均完成各自包/浏览器/精确CI及独立终结审查；c2独立包、受控/迟到/真实单次对账与原记录恢复本地通过，新独立本地审查通过，提交/精确CI待收口；d候选导出独立包/两段受控浏览器通过，真实两候选导出/原回执恢复通过，新独立本地审查通过、无findings；提交/远端CI待完成；F5完整证据索引另行负责|
|F4.4 有界运行观察与完整页面旅程|沿原运行ID增量展示阶段/工作单元/日志与证据引用，限制分页/游标或轮询范围；关系编辑仍是草稿，运行视图只投影事实|设计调查中、未实现；已实测SDK物理页可能超过page_size，下一先交付严格有界的原run事件读取，再接页面/原日志及完整浏览器旅程，独立综合审查后收口F4|

## F4.1 已核实现与设计边界

现有控制台为12个ES模块、无构建框架，app.js拥有导航与项目刷新，ui.js拥有文本安全DOM/表单组件，state.js只存选择及服务器快照。web.py已提供所有本片需要的API；tasks.listing限制每页扫描1–100条原目录，下一游标可经过其他项目/不可读记录，空items不代表扫描结束。tasks.show读取冻结合同；submission读取本地意图；status通过登记环境验证原spec并查询原Temporal run，NOT_FOUND与连接错误分开。页面不增加Python API、数据库、调度器、依赖或凭据入口。

新增tasks.js是正式任务页的完整界面所有者，与已有memory/tools/workflow页保持同一组织方式；其唯一生产调用者为app.js的导航，不再包一层通用传输/状态抽象。复用api/ui组件和现有六阶段名称，不在浏览器重算质量门禁。当前项目配置、冻结绑定、本地提交回执、实际原运行及外部已清理分别展示。任务列表不自动逐个查询Temporal；原运行查询由用户明确触发并带非空run ID，错误和未查询均保留。

浏览器只持久保存选择，不保存权威任务状态。每次重开重新读合同/提交回执；动态请求通过视图存活与请求序号限制，切项目、切任务或更改run后不得把旧响应写到新视图。继续采用原生表单与现有样式，桌面和窄屏均可操作；不在本片更换图形库或增加长连接。

## 验证与交付安排

先做JS语法、既有Web/tasks合同定向回归，再构建并非editable安装新wheel，核源码/包/安装与冻结reference身份。使用Playwright CLI做真实HTTP浏览器旅程，读取F3原持久任务时只重开所需专用Temporal，不启动executor/worker或调用模型；受控分页/迟到/失败响应分别标为浏览器传输反例，不能充作真实网络故障或正在执行的工作流。截图/CLI浏览器日志在忽略的output/playwright和本片私有checks下保存，不进入公开仓库。

原F3已通过完整711回归及精确两OS CI；该历史结果只属于7139身份。本片主要是UI资产变化，不在本机重跑相同后端完整套件，新增候选按变动风险做定向与浏览器验证，并核本次推送实际CI。实现与验证后更新本记录和PLAN，再交新fresh-context审查者审查正确性、结构与必要请求/渲染成本；完成修正及远端核对后仅关闭F4.1。

## F4.1 实现与验证过程

源码基线为文档提交`2add1bf3435738509462e6978d7f83742422ea6f`。生产增量仅在console下：新增tasks.js，app.js接导航/标签选择恢复和刷新生命周期，index.html新增正式任务导航，overview.js增加任务入口，style.css提供任务布局/事实列表及窄屏规则，workflow.js保护保存回复所用项目快照。无Python、测试、依赖或冻结reference变化；公开README/USAGE/当前架构同步只读页面范围。浏览器没有新增任务状态机或自动提交/信号/导出行为。

- 13个ES模块Node语法检查通过。首个非editable包运行原`tests/test_web.py tests/test_tasks.py tests/test_architecture_boundaries.py`：44 passed，1个既有Starlette弃用警告，43.47秒；包含CLI/API同合同、跨项目隔离和静态模块边界。之后仅修正浏览器可选DOM子项的null文本及合同标签措辞，后端/测试未变，不重复用这些后端测试声称验证DOM修正。
- 初轮浏览器实际发现可选子项经原生replaceChildren渲染成字面量null；已在原界面所有者过滤空项，未改公用DOM工具或HTTP。新wheel SHA256为`3cf98a00440ab0fdab24cc05d845fed0f1137e4e100a6a2f739954499fd0ad3e`，348文件与源码/完整开发安装/新无SDK基础安装一致；冻结283保持，当前37个顶层Python/13个前端模块。初包、源码清单与日志另存，未用修正前浏览器冒充最终验收。
- 最终包实际HTTP/Playwright读取F3五个原run：两个REVIEW_READY、两个CANCEL_UNCONFIRMED、一个BLOCKED，DOM的候选与原API完全一致；刷新恢复项目/标签/任务/run选择，状态仍需明确重新查询。该段41请求全GET、无pageerror；390×844下scrollWidth=390，可选DOM没有null泄漏。截图在私有output/playwright；这是已闭合原运行的只读页面验收，尚未在浏览器创建或批准新任务。
- 另段用真实Temporal查不存在的合法run ID，明确not_found且无phase。浏览器受控延迟原运行/跨项目详情响应未覆盖新选择；将真实tasks API扫描窗改为2，验证经过无匹配项的中间页仍可前进、终页停止及上一页；旧角色快照为空、HTML样式任务文本与未登记项目使用受控响应分别验证。累计75个已记录浏览器请求均GET、无pageerror；受控响应不充作真实网络故障、旧原记录变更或后端验证证明。

私有原始材料位于`.ergora/checks/f4-task-console/`：build/install/targeted日志和命令、initial-dist/initial-package-identity、最终package-identity、browser-normal与browser-boundaries的原CLI输出/脚本及解析结果。浏览器CLI最初解析器误以双换行分隔结果，导致辅助包装器在边界段真实脚本通过后退出1；原CLI的完整Result无Error，已按实际Result标题边界解析并沿同份原输出保存JSON，没有重跑浏览器取得另一结果。uv的direct_url元数据不含archive hash；本次以实际文件字节逐项核对和wheel SHA及来源URI确认身份，不伪造元数据。

当前镜像缺浏览器共享库及中文字体；只将7份发行包运行库与用户字体解包至持久用户目录，headless shell使用显式库路径，无系统安装、宿主权限或产品依赖变化。最初错误build入口与缺库启动失败保留，实际构建沿缓存uv离线完成。原生任务/操作/回执/产物的完整新前快照为416文件，待服务恢复和浏览器收尾后对照；不继承F3旧104文件快照范围。

实际停止Temporal后，同一页面明确显示连接拒绝、移除旧成功phase并保留合同及原run；辅助脚本末尾因错误限定文案失败，随后仅检查现有页面确认上述事实，没有重复发查询。正式重开Temporal后，同一原run再次读取REVIEW_READY及原candidate，累计77个GET、无pageerror。该恢复段仍属于3cf98a…包。

[新独立初审](2026-11-03-formal-task-console-read-review.md)发现两项P2：R1项目选择变化后至新dashboard返回之间旧视图仍连接，R2原生phase直接小写不能映射plan/work/integrate/verify/review。已分别在app.js的refresh入口同步移除旧快照与视图，并按既有refresh序号隔离迟到成功/失败；失败保留可重试页面。tasks.js显式映射六个原生活动phase，闭合/等待/清理不作活动位置。修正后新包、全部阶段及真正dashboard等待/失败/A→B→A浏览器反例待验证，不将初审写成通过。

首轮修正后的中间wheel SHA256为`1ff7a245da408cc6f2f9e8cd09193ee2ffbf9160fdfba54d07eb024a4d573058`；348文件×源码/两非editable安装、冻结283与13模块语法均通过。原3cf包和身份另存pre-review-fixes，未覆盖历史候选。五原run/41GET正常旅程及累计75GET边界段均在新包重新通过，新的日志/结果带final后缀。纯后端44项没有重复执行。

`browser-review-fixes-v3`通过14个受控阶段投影（六活动阶段、初始化/等待/清理/终态及闭合但保留活动phase的反例），也通过B的dashboard仍等待时释放A详情、B失败时释放A状态、等待/失败中切标签、重试和A→B→A之后旧A详情与旧B错误不得胜出的反例。最终再次真实查询原run成功。当前会话累计235请求全GET、无pageerror，计数包含前两次辅助脚本的失败尝试；它们在A→B→A中提前移除仍处理中的拦截器，报Route is already handled，未通过，不写成产品故障或有效验收。v3保留该处理器至旧回复完成，并让新A请求继续走真实API；未为脚本失败再改产品代码。

当前7份变更Markdown的294个本地链接/锚点及26条README命令parser已核通过。剩余：独立复核、416原文件后快照与服务收尾、可读中文截图及当前候选CI/提交推送。F4.2–F4.4仍未实施，完整F4尚未完成。


R3相邻异步边界：同项目刷新保留既有快照/视图；仅所选项目与快照项目不同（含切回时空快照）才立即卸载。独立审查者同时确认A保存待回→B→A的dashboard仍等待时，旧workflow保存回调可能访问空快照；已在原消费者进入app.data.drafts前检查实际快照项目，没有新增通用状态层。当前包SHA256为`3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021`，348文件×源码/两安装、冻结283、13模块语法通过；两种保存/刷新反例及任务页复测进行中，1ff身份不作最终候选。

当前包首次正常/边界脚本在同项目重新selectOption后误把刷新前同名标题当作新页面，查询回复随旧视图移除而被正确忽略，脚本等待超时；修正脚本明确等待新详情API，随后又因前一失败留下的测试run选择而拒绝继续。失败日志均保留；最终正常脚本明确填写已知原run，再验证重开时选择保留，不更改产品状态或后端。上述脚本失败不能计为通过。

当前3f287e…包的两种草稿保存反例已通过：同项目保存待回时刷新仍正确接受该回复；A→B→A且A新dashboard仍等待时，旧保存不解引用空快照或恢复旧工作流。该段22请求中2个POST由浏览器直接拦截模拟，未转发后端；其余为真实GET，0 pageerror。第一次当前包复测的重复事件监听器导致请求计数被多次累计，不以123/225作为实际请求数；正在用新的浏览器会话获取无重复计数的最终只读记录。

## F4.1 最终候选事实与收尾

源码基线仍为`2add1bf3435738509462e6978d7f83742422ea6f`；增量为6个console文件及文档，无Python/测试/依赖/CI/reference改动。包`3f287ecebdf37324a7960661f65e07a9713cfc1d277aa439e01370b25f044021`的348文件与源码、开发及无SDK基础两份非editable安装逐项一致；冻结283文件保持，13个ES模块语法通过。基础安装的5条本地CLI检查属于相同未变Python消费者；44项定向回归仅首包执行，不套用为最终DOM验证。新候选CI仍须实际核对。

|最终包验证|实际结果与证据|
|---|---|
|新会话正常旅程|`browser-normal-clean`：5真实原run与API的phase/candidate一致，41 GET、无pageerror；reload恢复选择、状态明确重查、390px无溢出/无null文本|
|边界旅程|`browser-boundaries-clean`：真实不存在run与原API扫描窗2/空页游标，受控迟到/缺快照/文本安全/缺注册；累计75 GET、无pageerror|
|审查修正|`browser-review-fixes-clean`：14种phase投影、真正dashboard等待/失败、等待/失败中导航/重试及A→B→A旧响应；新增54 GET、累计129、无pageerror|
|保存/刷新并发|`browser-refresh-draft`：同项目保存待回/刷新、切回A但dashboard未回时旧保存；22请求含2个完全拦截的模拟POST，未转发任何写请求；无pageerror|
|视觉收尾|`browser-visual-clean`：另9 GET、真实原run/candidate、390px无溢出；`output/playwright/*-readable.png`及viewport图的中文已实际查看可读。只对验收浏览器指定本地fontconfig，不改产品字体或依赖|
|原证据保护|`native-before.json`/`native-after.json`：tasks/requests/receipts/artifacts/approvals/fences及选定process/ergora JSON共416文件完全一致；不声称覆盖SQLite或日志|
|服务收尾|`final-shutdown-command.json`/`final-shutdown.json`：5原run均COMPLETED且无RUNNING workflow；正式shutdown confirmed、daemon not_running、socket/PID消失，Temporal SQLite保留|

最后的可读截图脚本已在最终包成功，不需要运行随后预备但未执行的visual-clean-v2来代替原结果。正常/边界/阶段三个clean脚本在全新浏览器会话运行，只有一份请求监听器，129计数有效；视觉段另列9条，未在环境结束后补造丢失的浏览器内存请求数组。

收尾期间执行环境重开，旧HTTP/浏览器/Temporal进程已消失，但本专用栈的Supervisor两份标记仍残留。实际核原PID不存在、Unix socket连接拒绝、原inode/属主未变后，仅移除这两份失效标记并保留记录；只重开Temporal确认原run，再沿正式shutdown退出。worker/executor未重开，也未调用模型、改权限或操作其他栈。此前F3 shutdown记录没有被当作这次收尾证明。

初审者上下文随环境重开已不可用；已启动新的独立最终审查者，从原需求、全部实际差异和上述原始证据复核，另存本项目交付报告。新的审查者已确认R1–R3关闭、无新增阻塞项及代码/本地验收通过；报告保留精确提交/CI/远端待核。当前只待文档静态终核、提交推送及精确CI，完整F4仍待以下三片。

## 下一可执行项：F4.2 创建与提交

1. **[F4.2a 预览/创建与原ID恢复](2026-11-03-task-creation-console.md)。** 从正式任务页选择现有开发草稿或输入完整definition；复用草稿内容，不在浏览器复制合同编译器。只接受项目已登记的repository-governance/large-change；训练优化继续使用既有独立流程。
2. 沿原preview展示project revision、冻结角色、原合同/输入及preview SHA；改任务ID/模板/工单/输入即失效预览。用户明确确认后才create，不自动start；创建失败或断线按原task ID查询creation并显式resume-create，保留原intent SHA。未发布的任务不一定能出现在正式列表，须始终提供按ID读取创建记录的入口；模态框关闭或项目变化后，旧回包不恢复已弃用的界面。
3. **F4.2b 提交与未知恢复。** 选择已published的统一创建任务，先读creation/submission；明确展示冻结身份后才start。submitted展示原run，prepared/unknown/rejected保持可见，恢复只调用原resume-start，不以重试start或更换ID绕过未知。项目/详情/预览和操作回包延迟继续受视图身份限制。
4. **F4.2c 两模板浏览器验收。** 在独立持久验收项目中用浏览器走两模板的草稿→预览→创建→提交；检查重复/旧revision/预览变化、发布中断、提交未知恢复、缺服务与离开页面。先用可控故障验证控制合同，再将真实执行及人工批准等完整旅程交F4.3/F4.4；不在F3原任务上试写。a/b作为各自可审查切片，c负责组合验收；每完整实现片重新启用独立审查者并登记源码/包/测试及提交身份。


提交与CI阶段：8份Markdown305本地链接/锚点及26条README命令parser终核通过；14份范围提交`11e89cf44eb29fe9064bd0015417cf6bc54fdc5e`已推送工作分支，未合并main或创建PR。独立报告后补的链接计数与状态文档将随最终CI复核记录另作纯文档提交，生产身份保持11e89cf。

2026-11-04续核：精确CI41662193234整体Cancelled；Windows全部必要步骤成功，Linux构建/冻结身份成功，原生回归超过20分钟上限未完成。独立审查者已按提交tree重核348文件=原3f287e包、14份变更及实时远端11e89cf一致；未混入F4.2a本地页面差异。代码/本地结论仍通过，完整F4.1交付待新的有效CI补齐。当前原已安装包Linux同套件诊断进行中；另以[V4](2026-11-04-ci-regression-progress.md)改进输出定位，不将取消算通过或直接扩大超时。

最终续核：V4提交`2137a95418879d48cce557016caa5c7f0d6a6a1b`仅改CI包装与7份文档，应用/测试树仍等于11e89cf、348文件仍等于原3f287e包。新精确[CI41679431542](https://github.com/626619403/Ergora/actions/runs/41679431542)两OS及全部必要步骤success，实时远端为完整2137；[F4.1独立最终审查](2026-11-03-formal-task-console-final-review.md)及[V4独立最终审查](2026-11-04-ci-regression-progress-review.md)均通过，R1–R3关闭，F4.1完成。原包Linux同套件诊断实际711 passed/19 skipped/36子测试、2550.05秒、exit0；原CI取消保留，不推导超时根因。F4.2a仍单独验收，完整F4未完成。
