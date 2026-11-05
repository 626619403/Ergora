# G0.2：全新数据的真实六阶段、恢复与交接

日期：2026-11-05。状态：两原run六阶段、候选独立复验、额外取消与显式对账、三份页面下载/无SDK核包及六项错误包拒绝均通过；服务退出及新旧数据终核通过；新的独立审查通过，P2用量文案已关闭；精确交付尚待。

沿G0.1全新持久环境与两个revision2项目，不再次注册、不导入旧run。使用公开services start显式启动Temporal/worker/executor/a2a，不启MLflow；以两原prepared意图SHA执行resume-start并固定返回run。模型选择Codex/gpt-6.1-sol/medium，阶段墙钟600秒、执行器并行2，正式索引未记录的token/费用不补零。当前可信容器与本机用户为执行边界。

依次核 inventory/plan 到 AWAITING_PLAN_APPROVAL，原生history/spec/memo/可信receipt身份；主入口完整读取计划、所有权和回退材料，逐项审阅后批准精确plan SHA。两任务必须保持允许路径、原行为基线及外部可信检查；独立review阶段绑定相同候选并可请求修改，不能为了验收改判。

HTTP正式关闭重开后读原run/决定，重复start/approve不新增workflow或有效信号；另建明确取消任务并沿原ID查闭合结果、外部作业和显式对账。REVIEW_READY后导出精确候选分支，以独立detached worktree运行操作者可信检查。闭合run证据/预算/实际交接包、基础无SDK接收者离线核包，错误SHA/复制包篡改须拒绝；网页实际下载与CLI材料一致。

逐步保存实际命令/结果/原history、模型日志、阶段耗时和失败，不伪造模型或回执、不盲重发unknown。新任务不继承旧F5模型结果；旧139文件/Git/claims保持。退出时无active lease/未核运行，正式关闭owned浏览器/HTTP/Supervisor，保留新库与原Supervisor ini。产品缺陷另列最小修复片；不新增生产测试框架/CI或重复未变矩阵。完成后新的fresh-context审查，普通提交推送与远端核对；G0.3另做易用性/平台边界和综合收口。

## 新服务就绪

启动前重核G0.1保存的新任务/意图文件SHA与四服务端口关闭。公开`services start governance-g0 temporal worker executor a2a --revision 2 --timeout 50`实际exit0；完整辅助命令20.56秒，包括原生doctor协议就绪核验。原`ready_for_real_tasks`为true，MLflow保持stopped；尚无workflow或模型调用。没有新注册、改绑定、手改Supervisor ini或跳过准入。私有原命令与结果在`.ergora/checks/g0-journeys/`的`services-start-*`、`native-doctor-*`和`service-start.json`。下一按两原prepared SHA显式resume-start，RUNNING/准入不作为模型成功证据。

## 两原意图实际恢复

两个公开`task resume-start --revision 2 --intent-sha256 原SHA`均实际exit0，返回submitted；总辅助6.32秒。创建与提交SHA保持G0.1原记录，未再次create/start或更换任务：

|项目/任务|原workflow|实际run ID|
|---|---|---|
|governance-g0 / governance-g0-normal-r1|dev-task/governance-g0-normal-r1|01a1a909-7372-7418-8529-e09c76d1c1d7|
|large-g0 / large-g0-normal-r1|dev-task/large-g0-normal-r1|01a1a909-7dec-74f5-92f9-7fdbca8bc0ff|

原命令、输出、退出和`normal-runs.json`已保存；submitted只证明原run回执，真实模型/六阶段结果待后续。下一只读核实际计划、原history/spec/memo和可信回执，完整审阅后才批准精确计划。

## 原计划与主入口只读核验

两任务均实际停在AWAITING_PLAN_APPROVAL；每个原history连续112事件、零signal、两个SUCCEEDED的inventory/plan job，原spec输入与submission memo精确匹配。请求envelope、可信receipt、产物字节/SHA及实际Codex角色选择核验通过；四个真实模型阶段没有用fixture代替。两计划SHA分别为`68a3379712ddb1781151c8379fd0e3714e3a8d6b94357967a363237121074f5f`和`0359dd7e3e44a75a477583ff570f50a692f7ee3e0daf76c6eb71215a493a5483`。

公开CLI完整读取两计划，浏览器只读旅程16 API GET/零POST/零pageerror，返回材料逐字段与CLI相同，桌面/390px通过。操作者已完整阅读execution-plan、ownership-map、rollback-plan共6份原文，确认治理两并行单元/大型单一完整单元、允许路径、默认行为、外部可信检查和定向回退均保持；动态导入等覆盖缺口明确保留，没有将未来候选结果当作现有事实。原材料/摘要与审阅理由保存于`pending-verified.json`，截图在`output/playwright/g0-journeys/`。下一先正式关闭重开同一HTTP来源，再沿原ID读取并批准；当前仍零批准信号，费用未知不补零。

## HTTP正式重开

初轮HTTP按owned PID/命令/用户核身份后SIGTERM，有序关闭、端口关/临时根空，工具session89262真实exit143已取回；原identity/日志/lifecycle另存不覆盖。显式在同一来源/端口启动新PID，bootstrap实际200。原浏览器reload后19次API GET/零POST/零pageerror，两原run输入选择和计划身份/完整回执逐项等于重开前，桌面/390px仍通过；这19次含reload测量窗口内的初载请求，非全部HTTP总量。尚无批准或替代run。下一用已审阅SHA明确批准，另保留一次真实成功回包丢弃后的按原decision读取，不把requested当作执行已完成。

## 精确批准、回包丢失与重复操作

真实页面批准旅程35 API请求/2 POST/零pageerror，两项目各以稳定`owner-g0-one`发送一次精确原run/plan。大型任务的实际成功200/requested回包被测试路由丢弃，页面显示未确认；同窗reload后只读原decision取得同一requested，无重发、无模拟成功。390px记录窗口通过。requested中的approval_accepted/execution_success仍为null，后续采用和完成由原run另核。

随后公开CLI对每任务各重复一次start和同ID approve，共4条命令exit0，返回逐字段等于原submission/approval；18份原创建/提交/批准/owner文件摘要保持。原生history保留最初112事件，每个run恰一个event113的approve_plan，payload与owner receipt、意图/attempt/result摘要精确绑定；Temporal可见性查询每个workflow恰原一个run，没有新workflow或第二批准信号。核验时两history为268/202事件，仅作当时进度快照；最终六阶段与清理仍待独立检查。原证据为`browser-approve-result.json`、`repeat-verified.json`及各真实命令和history。

## 真实六阶段与显式对账

两原run已COMPLETED，原outcome均REVIEW_READY；治理候选`44d697f0701a69fdfad50e72ee1b463d70adc9fe`、大型候选`68ff73c485ea9faedf1dd8a94f98629f26fb489a`。完整history为324/337事件，原前缀和各唯一批准signal保持；7/6个原生job均SUCCEEDED，覆盖原六阶段与治理两单元。实际Codex模型job分别5/4个，角色session各自独立；integrate/verify由可信执行器拥有。治理5项、大型8项声明检查及同候选独立review均pass，全部原request/receipt/产物字节、outcome证据摘要绑定通过。操作者已完整读两原review-report，覆盖缺口保留，未改判或合并业务候选。

首轮最终辅助脚本在其他核验完成后，提前要求零active lease而实际exit1；当时原生库2 claims/2 active，闭合任务需显式外部对账并非自动释放。原脚本/命令/状态保留，不修改断言或产品以求通过。两次公开external-status确认全部原job已有回执、无额外或未解决job，再分别`task reconcile --revision 2 --run-id 原run --confirm`实际exit0/reconciled/external_confirmed=true/lease_released=true。随后用逐字未改的原脚本、新标签复核exit0，实际2 claims/0 active，原REVIEW_READY结果未改。G0.3会把这项关闭流程纳入公开说明与操作步骤计数。

## 精确候选导出与独立复验

两个公开task export均exit0/exported，分别创建各业务repo的`agent/原task ID`分支且指向上述精确候选，checked_out/merged均false，业务repo HEAD保持原基线。另建操作者持有的两个detached worktree，对治理3类/大型6类可信外部检查共9条实际复验，全部exit0，验收器原SHA和候选worktree干净保持。私有`candidate-verifications.json`与每条原命令/输出保存；独立worktree保留以便复查，没有改候选、合并或部署。下一新增明确取消任务，验证实际活动进程、原取消信号、闭合未知与显式清理，再收集/下载本次新证据。

## 新取消任务与外部进程

公开preview/create/start创建独立`governance-g0-cancel-r1`，原run为`01a1a91a-ed65-7b18-abda-7f65e1da5bc2`。在可信监控器记录的实际selected-agent子进程存活时核PID/start_ticks/boot_id/命令/工作区归属，之后仅以稳定`owner-g0-stop`请求一次取消；requested的cancellation_confirmed/execution_success保持null。监控器真实终态为`Cancellation fence observed`且非零退出，原进程组无活成员、原monitor退出，没有由测试脚本直接终止Agent。

原workflow实际COMPLETED，35连续事件中恰一个精确request_cancel，零批准；原结果CANCEL_UNCONFIRMED保留。重复同ID取消返回原记录、未增signal。公开external-status确认原job回执和完整材料，无额外/未解决job，再显式reconcile实际exit0/reconciled并释放原租约；原取消结果不变，当前3 claims/0 active，不记开发成功。

首轮取消收尾辅助在上述真实动作已成功后，末尾误从取消intent读取request_sha256导致KeyError/exit1。原脚本/命令保留；根据现有signal所有者，从冻结task.spec.json核request SHA、从intent核操作SHA，r2只读回首轮4条成功命令、没有重复取消/对账写，精确信号/attempt/result及进程/租约核验exit0。私有原证据为`cancel-run.json`、`cancel-final-history.json`、`cancel-verified.json`与`finish-cancel-r2-readback.json`；产品与断言语义未放宽。

## 新证据、真实下载与接收者

三个原run的公开CLI evidence/handoff均exit0。真实页面旅程36 API请求、3次显式收集POST/实际ZIP下载、零pageerror；按需索引、未知量、原job文本窗口、关闭重开空索引与390px通过。页面索引逐字段等于CLI，三ZIP逐字节相同；23/19/3共45份材料引用与原可信receipt及磁盘字节/SHA一致。两个正常包保留REVIEW_READY，取消包保留CANCEL_UNCONFIRMED，不将离线校验当执行成功。

全新基础接收者确认无Temporal SDK，三包各离线verify exit0，origin_authenticated=false/execution_success=null，未创建control库。每包错误预期SHA和仅改复制ZIP一个blob（重算CRC、原manifest不改）各明确拒绝，共6项预期非零；原包保持。私有`handoffs.json`、`browser-evidence-result.json`、`downloads-verified.json`、`negative-handoffs-verified.json`和原命令/下载保存。两次无关的全目录文件索引探针耗时停滞，按owned PID终止，实际shell143；没有到达其后产品命令，也未改变验收结果。下一正式关闭owned浏览器/HTTP/Supervisor，再无服务核包与数据终核。

## 正式退出与最终数据保持

退出前只读核三原history仍为324/337/35事件、原outcome逐字段保持，实际零running workflow、3 claims/0 active lease。owned浏览器公开close exit0；HTTP核原PID/用户/命令/start身份后SIGTERM，有序shutdown且真实工具session5616的shell143已取回，请求临时根为空。公开services shutdown（revision2/confirm）exit0/confirmed，5个owned Supervisor及服务进程均退出、socket/PID文件移除；四执行端口及本轮HTTP端口关闭，没有处理其他片HTTP。

关闭后同一无SDK接收者三包再verify exit0，没有启动服务或创建control库。新152文件及导出后的Git refs/worktrees、可信检查脚本保持；旧139文件、旧两repo的文件/HEAD/refs/worktrees及3 claims/0 active保持。新Temporal、租约和control三库非空保留，Supervisor ini与G0.1原SHA相同。私有`before-shutdown-verified.json`、`shutdown-verified.json`、`http-lifecycle.json`、`final-offline-verified.json`及原命令保存。未重复模型、改任务结果或重跑未变多OS矩阵。

## 交付范围与剩余事项

本片仅文档与实际验收，基线为G0.1精确`18ed62eb4eb0dba6a27d0535919a394330fa1e45`；生产仍为`4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`，新app构建归档与接收者原f644858归档分别记账，352资源相同不等于归档字节相同。模型/任务结果来自本次新run；原精确双OS CI41929749342仅保留其原覆盖。

[新的fresh-context审查](2026-11-05-new-user-journeys-review.md)及同片文案复核通过，需求与可维护性无未解决finding；最终文档静态核对、普通提交推送与实时远端终结尚待。G0.3随后修正正常任务的external-status/reconcile关闭说明并核A2操作计数/配置面/平台边界；完整G0尚未完成。空OS、本机Windows/WSL2、远程工单和GPU未在G0.2验收，完整/计费消耗与金额仍未知；原CLI日志存在自报usage，未归一化到正式索引。

## 审查修正：用量事实的三种来源

独立审查指出原“真实token/费用仍未知”文案过宽。9份成功Codex的model-log包含真实turn.completed.usage事件；这是CLI自报用量。正式证据索引尚未按原job归一化这些字段，model_calls/tokens/cost仍为not_recorded/null，不用文本或当前价格表反填历史索引。原日志的CLI自报、正式索引记录与完整/计费消耗分别陈述；未覆盖取消期间消耗，金额也没有账单来源，仍未知。cached/input/output/reasoning各字段可能存在包含关系，不相加成所谓总成本。本次只澄清文档，不改产品、原日志/回执或未知语义；同片复核通过，P2关闭。
