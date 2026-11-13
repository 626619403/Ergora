# D2-A2：重构配方真实串行旅程

承接[A1重构配方](2026-11-13-refactoring-preset.md)，使用其精确已核非editable wheel，运行产品、父模板及Agent包不修改。A1本地出口后再启动实际模型；准备与运行、独立审查、普通发布各自记录，不借治理旅程的并行writer结果证明本片串行。

## 输入与验收出口

隔离标准库小项目中，`normalizer.aliases`重复`normalizer.normalize`的逻辑，真实`client.request`调用这两个公开函数。目标是让aliases复用既有normalize，并保持Unicode lower、输入类型／TypeError、空值、顺序／去重、generator消费、返回类型和真实caller。一个writer只改normalizer，后续兼容性writer在集成前驱的候选上补一个有价值的caller测试并写实际证据；原可信integrate／verify后接三个必需独立reviewer。

保护真实caller、检查脚本及原baseline参数。可信检查读取精确baseline Git blob，以固定边缘输入和确定性样本作原实现／候选差分，运行真实caller和unittest，再在持久目录下的独立临时子目录恢复精确baseline源码并验证caller。该回退证明本地源码恢复，不是生产部署回退。检查脚本与项目持久数据不放系统或项目tmp目录。

|节点|实际出口|状态|
|---|---|---|
|A2.0 准备|已核安装包；独立Git fixture／baseline及可信原checker预验；原refactoring根完整manifest与definition6准备|第三轮独立task／budget及精确plan批准通过，前两轮身份保留|
|A2.1 执行|一次总预算、7槽；真实inventory／plan／owner精确批准；rewrite→compatibility串行；可信集成验证／三review，保留实际outcome|第三轮REVIEW_READY／9 job／7会话成功；前两轮BLOCKED／TERMINATED保持|
|A2.2 恢复与交接|同ID重复start／重启原run；完整history重放；精确候选导出、独立复验及handoff|第三轮623事件重放、原ID重启读回、精确导出／checker复验及handoff通过|
|A2.3 原件与清理|所有实际会话、完整祖先与scope、串行前驱产物／原slot／owner清理；服务停止而持久记录保留|第三轮9 owner／7槽／85回执产物、7会话38资源23,329B完整读取、原claim释放及端口关闭已核|
|A2.4 交付|新的独立两轴审查、计划和手册同步；普通提交／远端／自己的必要CI|第三轮原件已补核，新的独立审查与发布待完成|

显式采用用户已授权的Codex回退，独立会话不宣称异构后端。A2不扩展运行图、GPU优化、远端业务写或Windows服务支持；失败、超时、unknown和未通过审查都保留原结果，不在原任务下换输入或重领预算。

## 首轮实际结果及后续边界

2026-11-13原run `01a1d360-d7ca-744f-9f7d-469409c581ad`形成候选`ad230f4dece315541934ed3bc87c3844860e7ac2`。inventory、plan、rewrite、compatibility及可信integrate／verify六job成功；rewrite会话于05:32:53.978730 UTC结束，compatibility于05:33:06.477789 UTC开始，实际串行。

三个review会话于05:35:09–10 UTC启动，在约600秒阶段期限结束时均为`cancelled`／returncode -15，executor回执均为`FAILED`。三个原native stdout、stderr均空，未记录MCP握手或模型结果，因此无法判断是provider等待、CLI启动停滞或其他底层原因；也不能把它称为模型request-changes或候选被审查否决。总预算未耗尽、overrun为0，原fence确认且无unresolved job。shutdown回执为confirmed／daemon not_running。

原run、7槽、5400秒总预算、600秒stage配置及失败证据保持。先补核原件、清理与实际差分／回退结果，再按证据决定是否另建独立验收任务；新的输入、期限或执行容量只用于新task和新预算。该首轮没有完整重构REVIEW_READY、恢复／导出／handoff验收；后续独立第三轮见末节。

## 原件补核与失败恢复

[公开证据投影](evidence/2026-11-13-refactoring-journey.json)保留精确原件SHA、run／候选／预算与未验项。四个成功会话共20资源14,525B完整连续UTF8读取；三个取消会话共18资源8,804B有冻结scope但没有读取，完整input／prompt／stdin／protocol和祖先来源仍逐项相等。九job的原owner PID／start身份均不存活，body与collection清理确认、原回执及全部产物摘要、7个精确slot均核准；端口关闭、持久Temporal库保留。未作全系统后代采样。

从原runtime的隔离bare仓库创建detached worktree复验原候选，受保护checker用原baseline `16f94116df2c9ec795b085146b5be6c27711d1d2`完成212 normalize／6 aliases差分、2个真实caller unittest、generator检查及独立精确baseline源码恢复，exit0／0.217秒。随后只移除该验收worktree。该候选仍隔离保存，没有approved export或采用。

后补仅重启Temporal，原run终态、submission及重复start身份保持，完整1,253历史事件重放通过，原evidence为verified；这只说明失败原件完整，不是审查通过。恢复首轮因离线harness漏加已安装reference Python路径而报`ModuleNotFoundError`，原失败及shutdown保留；只修harness后在新证据目录重跑成功，产品与原task／budget未改。服务再次shutdown确认。新的独立两轴证据审查待完成，下一实际成功验收需要独立task和预算。

## 独立第二轮准备

首轮取消发生时三review均无native输出，尚未确定底层原因；后续优化专家的独立单叶已正常返回。为验收成功路线，另建`refactor-module-2`和独立runtime，沿同一A1安装包与fixture重新准备／冻结／批准。新任务预先声明7200秒总预算、1200秒阶段上限和7槽，将executor容量设为1以限制同时在途调用；review图仍允许并行，实际排队由原executor管理，不改模板或原调度。此配置只用于第二轮，不把首轮改写为成功，也不从一次通过推断底层故障已修复。运行及后续出口等待真实结果。

## 第二轮实际终止结果

原run `01a1d37d-b869-7b0f-81bd-d24937826961`先完成准备、串行rewrite／compatibility及可信integrate／verify，在首review等待期间于2026-11-13 06:22:01.301408400 UTC被Temporal `history-service`终止，原reason为`Workflow history size exceeds limit.`。驱动随后读到`NEEDS_RECONCILIATION`／`TERMINATED`并shutdown。后补仅启动Temporal读取到完整1,638事件、JSON70,666,291B，SHA256 `2d6798714a8208aa7fe189115218f3b8d0a88e5cf7f7e0d04f30d77d03386866`；这不是成功重放，也没有新的run／预算。

后来的原cancel命令因已关闭的服务连接拒绝，没有成功取消回执，不能称取消已确认。第二轮比首轮更长的stage上限及容量1没有解决无输出条件；[慢stdin独立复现及修正](2026-11-13-supervised-stdin.md)优先验收。同时新增历史增长后续节点：调查原submit／poll／status活动的重复材料，沿现有job／receipt／budget所有者压缩引用，保留原run、完整材料、停止／恢复和候选证据，不用延长历史上限或刷新预算掩盖。第二轮实际owner清理、原件投影与独立补核仍开放。

## 第二轮原件核对与原任务收尾

[新独立第二轮审查](2026-11-13-refactoring-journey-r2-review.md)核得：9份已提交请求中有7个实际启动的job、5个实际native会话；4会话成功，首test-value review取消／-15，另外两review无会话和回执。7原owner及9个受监督进程的PID／start身份均不存活，原body／collection停止见证和55产物摘要相符。最初停止服务后仍无原fence、两review终态或claim释放，评审明确保留该P2；不能照搬首轮的9 owner／7会话运行数量。

随后沿同一原task/run/budget，使用原已核A1安装及现有公开操作收尾。仅启动Temporal后，`resume-cancel`恢复原`supervised-stdin-reproduction`意图，明确得到`already_closed`／`not_sent`；不是成功发送取消signal。`task reconcile`先写原request绑定的fence并保持两个unresolved job，再仅启动原executor；原owner在fence下为两条尚未开始的review各发布CANCELLED回执，没有新增native会话。原5会话ID集合不变。

2026-11-13 07:00:44 UTC，沿同一intent的`resume-reconcile`核9个原job回执、原fence及完整历史后，返回`reconciled`／`external_confirmed:true`／`lease_released:true`。原run仍为TERMINATED／NEEDS_RECONCILIATION，原结果没有改为成功或workflow cancellation confirmed，原预算ID `f9c174ad28cb48a398201a62e947d8a3`／SHA `fb24609c48d819068eeb5609888e158062de3f5e3efaac2db561099a5c08ea77`未更新。服务再次shutdown确认，原三端口关闭；持久数据库、原失败和新收尾回执保留。公开CLI原命令／输出及终态保存在第二轮本地checks的`closed-recovery-r1/`，待原评审同片补核，完整A2成功仍开放。

[轮询历史修正](2026-11-13-workflow-poll-history.md)的新源码已将该原1,638事件历史和首轮1,253事件历史分别重放通过；这是历史兼容验证，没有恢复原执行或创建新预算。完整成功路线将使用含stdin与历史修正的独立安装、新task与预算，不能覆盖这两轮失败。

## 第三轮独立验收准备

第三轮`refactor-module-3`沿同一隔离fixture与验收合同，使用包含stdin／轮询修正的已核wheel `85e20a342361f8fda1233f607dc94679364a0691b0b5452bb6b274648d117ab7`。新runtime和独立7200秒／7槽预算保持1200秒stage及executor容量1。复用原串行rewrite→compatibility、可信integrate／verify和三必需review；完整input10及原owner不改。

本轮先读取原精确plan，再通过原公开CLI批准；验收driver不自行批准未读计划。已过安装检查后与H片独立审查并行运行，最终验收仍等待该独立审查及全部原件，不将启动／在途视为成功。

原第二轮收尾已获原独立评审补核：R2-SP1仅在原外部收尾范围关闭，9回执、原fence及release evidence均与原claim账本相等，原5会话／7槽不变；R2-SP2所要求的完整成功旅程仍开放。H片代码与安装／模型原件已独立两轴0／0，第三轮沿原run `01a1d3ba-600c-7c5f-b4e2-0e52c156d305`完成inventory／plan，下一为精确plan的owner核实／批准与串行work。

## 第三轮运行结果（原件补核中）

2026-11-13 07:20:51 UTC，原run到达REVIEW_READY，9 job及7个独立Codex会话全部成功。原预算ID `73cab749f22c48e9945538de025a9670`、SHA `19b7d833ccf84fd6b3b78f65c3d87a58913072b72005b1bb4d052e92b3356f23`保持；owner读取精确plan与原baseline来源后，通过公开CLI批准plan `113e5cd337aedb013237fa3d5634478e1dcb098298bce5b031050d9a07d4a9e1`，driver未自行批准。

候选`63004b35f123e0efa49f3746627247d9036d1de8`已导出到隔离项目的本地agent分支，原HEAD仍为baseline `19cd20e31210eb938020df034427f53dcc9c76ed`。原handoff验证通过，SHA256 `264c48b1500b594a88f36e3c6dd91e6dc9986420ebb347357a873f89ee37036b`；623事件完整历史重放通过，历史SHA256 `22bb6bd0327c3bdb90075cc3bb3b7e90cd4b56ba70d4d4fda781a394a13d37c9`。首次shutdown后仅重启Temporal，原run终态与submission读回一致，最终shutdown及三端口关闭已记录。

以上为driver实际出口；全部祖先／MCP连续读取、原owner／回执／预算槽、实际串行时序、导出候选独立复验与清理补核，以及新的独立评审仍在进行，不借REVIEW_READY提前关闭整片或远端／CI交付。

## 第三轮原件补核

[第三轮公开投影](evidence/2026-11-13-refactoring-journey-r3.json)保存原件SHA及候选身份。七次实际会话的manifest→input→prompt→protocol／stdin和完整祖先资料逐字相等；38份资源23,329B通过原MCP完整连续UTF8读至`next_offset:null`，失败MCP调用0。这里只核交付与读取原件，不推断模型理解、异构后端独立性或用量计费。

rewrite于07:14:40.285809 UTC结束，compatibility于07:15:00.468038 UTC开始；后者原materials的candidate等于rewrite实际回执候选。9个原owner均按PID／start身份确认不存活，body及collection停止见证相符，9回执和85个回执产物摘要核准；7个model-attempt与原预算slots精确相等。导出操作释放原claim，SQLite active表为空；原持久Temporal数据库保留。此处85是各回执引用次数，handoff验证为79个打包产物，两者不是同一计数口径。

从已导出的精确本地分支创建detached worktree，原受保护checker针对baseline运行212 normalize／6 aliases差分、2个真实caller unittest、generator及独立精确baseline源码恢复，exit0／0.199秒；验收worktree随后移除，原HEAD不改。历史实际为6,111,384B／623事件，其中61个poll仅携带三字段引用，输入合计10,065B，原patch marker存在。该完整成功历史与第二轮不同task／时长，不能把总字节之比解释为严格同负载性能提升；它证明本次真实长材料旅程已正常结束。

离线补核harness首轮误把公开canonical receipt digest当原文件字节SHA，第二轮误用内部`dev_poll`别名筛历史；原失败stdout／stderr保留，修正harness后全部通过。没有改产品、原回执、原task／budget或历史，也没有重跑模型。新的fresh-context独立评审进行中，提交／远端／本候选必要CI仍开放。

## 独立评审与结构补核

[第三轮独立审查](2026-11-13-refactoring-journey-r3-review.md)初审分别发现Spec P2：原structure模型报告缺少A2要求的明确deletion反事实；Standards P3：PLAN仍把已完成的原件补核写成在途。原Spec评审者直接读取同一精确baseline／candidate／真实caller，完成[独立离线结构补核](2026-11-13-refactoring-journey-r3-review.md#独立离线结构补核)：复用normalize既有Interface，让client.request与aliases两个生产调用路径共享算法所有者；删除normalize会让校验和规范化复杂度回到这些路径或要求另找共享owner。该变化保持Depth／Seam，提升Locality并减少重复实现。

该补核是独立审查者针对同候选的新离线评价，不是原Temporal任务新增模型会话／回执，没有替换原structure判词、7会话、7槽或原aggregate。PLAN过期状态已按实际补核完成修正。两项的最终同片复核见上述报告；普通提交、远端和本候选必要CI各自开放，不把本地A2通过称为已合并或部署。

独立最终复核已完成，Spec／Standards开放0／0；SP-R3-1与R3-ST1均按原报告关闭。本地A2行为、原件、恢复与结构补核出口通过；前两轮失败保留，发布／自己的必要CI继续开放。
