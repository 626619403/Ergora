# F4.3c1：网页取消与原请求恢复

日期：2026-11-04。状态：页面实现、本片独立发行身份及本地浏览器/真实取消验收、新fresh-context独立审查均已通过，提交推送与精确CI待完成。本片接续已交付F4.3b的计划审阅/批准；两个切片的包、浏览器证据及CI分别登记。

## 范围与现有所有者

在正式任务详情中接入现有`cancellations/REQUEST_ID`的GET/POST及`/resume`。仍由`tasks.js`拥有详情、原run选择和局部操作工作区，复用`api.js`与`ui.js`，不复制`_Cancellation`的状态机、journal、原Transport.cancel或精确信号对账。后端、格式、SDK和冻结reference保持各自既有合同。外部作业证据/明确对账另归F4.3c2，精确候选导出归F4.3d。

## 页面合同

1. 只有已明确查询且仍运行的固定原run提供新取消入口；固定该查询代际和run，并提示协作取消不会立即证明任务或外部进程已停止。已闭合状态仍可按原请求ID查看旧记录，不提供新的取消确认。
2. 用户填写稳定request ID，先GET原取消记录。`not_recorded`且来自固定原运行时，才显示原因输入（必填、最多1000字符）与显式确认；发送既有接口所需的当前revision、固定run、原因、confirm和timeout。服务端继续处理状态变化、原提交归属和严格输入，不在页面重算权限/门禁。
3. 任务详情另有按原request ID读取入口。`prepared`明确恢复原意图，`unknown`只核对原run精确信号；恢复始终发送原intent SHA，不用当前编辑原因覆盖旧意图。原记录显示原run、原因、修订、SHA和投递依据。`requested`/`already_closed`不提供再次投递；`already_closed`明确表示没有新信号。
4. `cancel_requested`、`cancellation_confirmed`、运行终态和外部清理分别显示；返回原run再明确查询，不能从本地回执推导已停止或已释放租约。没有自动轮询、重试、换ID或取消后自动导出。
5. 写前保存按项目/任务分域的原request ID选择并锁定输入；未知回复保留原ID查询。关闭/替换、切项目/任务、编辑ID或换run使旧响应失效，关闭页面不声称撤销已发出的请求。浏览器清空选择或换设备后仍可手工输入原ID读取持久记录。

## 验收与后续

- 先核既有架构/取消合同，再做纯页面所需语法和noneditable资源身份；不因相同Python没有改变而重复本地重型套件。
- 受控UI传输分别验未记录/恢复/未知/已请求/已闭合、读失败/旧修订、迟到及390px；明确记为fixture，写不转发。
- 用新专用演示任务验证至少一个真实请求、实际成功后丢浏览器回复与原ID恢复，直接history核至多一个精确信号；保留F4.2c/F4.3a/b原合同/操作/材料。选择无新增模型调用的可控等待点时，先用正式服务管理停本次专用executor，核所有者和活动任务，不影响其他服务；若不适用则记录限制而不修改原证据来伪造运行。
- 两个现有REVIEW_READY原run可用于真实已闭合竞态的有界读取；若显式演练already_closed，使用独立新request ID并分别核零新增signal，不能把本地取消意图记作已执行取消。
- 桌面/390px实际查看；分别记录成功段、失败尝试与原生检查范围。同步公开使用手册、README、帮助和当前架构。
- 实现、验证后更新本记录与PLAN，再由新fresh-context审查者检查正确性、所有权、重复逻辑/必要守卫和实际成本；修正、提交/推送、精确两OS CI及同片独立终结核对后仅关闭c1。之后c2外部清理、d导出和F4.4综合旅程仍须独立验收。

本片无需预建通用操作框架；批准、取消和导出的字段与恢复语义不同，先保持各自所有权清晰，只有出现必须同步维护的实际重复契约时，再单独提出可验收的提取切片。

相邻跟进：F4.3b最终只读首轮观察到一次submission子进程超时，后续真实GET成功；F4.4需在有代表性的运行/重开场景测量详情加载及自动恢复选择与手动重复选择的请求成本，再决定是否减少重复读取。该根因目前未知，不靠延长产品预算或掩盖错误完成本片。

## 首轮实施检查点

生产仅扩展现有tasks.js取消工作区、原运行/原请求读取入口及app.js帮助；README/使用手册/当前架构同步实际交互。没有修改Python、原生协议、格式或依赖。新请求使用固定查询run/当前revision/原因/显式confirm，恢复只发送原intent SHA；写前保存原ID并锁定输入，既有详情/内容连接/读取及run代际限制迟到结果。尚未执行本片请求或记浏览器通过；独立C环境会保留B的最终4fcdb9包/两安装。

首包`a4081f8d52acbc867e93f4933741438771c01c5df56298fed33f62ed02460664`实际构建/安装通过（35.41秒）：348源码/wheel/两专用noneditable安装逐字一致、283冻结保持，基础Web无SDK，tasks.js模块语法通过。未复用或覆盖B的4fcdb9包与两安装；尚无本片浏览器、真实取消或独立审查通过结论。

受控两模板浏览器已实际exit0（39.35秒）：40页面请求/6个拦截POST、另2个真实辅助GET，零转发写入/零pageerror。真实闭合原run不显示新取消；仅原ID读取not_recorded无写按钮；受控运行中的新请求固定run/revision/原因且必填原因，prepared→unknown/signal_not_found→requested恢复只带原intent，旧原因不可编辑，requested/already_closed无再投递，cancellation_confirmed/execution_success保持null。两个390px页面/弹窗均无溢出。该段不是原生取消成功；真实新任务、迟到/丢回复及独立审查仍待完成。

## 本地真实与边界验收

私有证据在忽略目录`.ergora/checks/f4-task-cancellation-console/`，截图在`output/playwright/f4c1-*`。本片未改Python、格式、依赖、测试或CI；后端原合同不重新复制进页面。

四段成功浏览器共118页面请求、11个POST（10个受控拦截、1个真实取消），另2个辅助GET，均无pageerror：

|段|页面请求/POST|实际检查|
|---|---|---|
|`browser-controlled`|40/6，全部POST拦截|两开发模板的未记录/准备/未知/已请求/已闭合状态、原因必填、不可变恢复、读取失败、390px|
|`browser-native`|27/1，真实取消|成功回复丢失、reload、重复读取、清除浏览器选择后手工输入原ID、返回原run、390px原回执|
|`browser-boundaries`|27/4，全部POST拦截|编辑ID、关闭/替换弹窗、程序化底层run输入改变、旧revision、unknown无自动恢复、写中锁定输入、跨项目/任务迟到写回复|
|`browser-readback`|24/0|两个原REVIEW_READY和新取消run的真实终态、闭合时无新取消入口、帮助及三个390px任务页|

真实新任务`governance-f4c-cancel-r1`沿已审阅预览摘要创建并启动，固定原run `01a1a5c0-06db-77fa-bbec-2ba74eb71ef1`，取消请求ID `owner-f4c1-one`。先确认无活动workflow、两个旧任务的request/receipt完整且全部成功，再正式停止本次专用executor；新任务只有一个inventory请求排队，没有receipt或模型调用。浏览器仅允许一次原run/原因/revision精确POST，服务端200/requested后故意丢弃回复，后续恢复只GET原记录。

`native-cancel-proof.json`直接核SDK原history112连续事件，唯一`request_cancel`在事件101；request SHA、原因、操作SHA与原intent/attempt/result一致。原意图SHA `123da41c12423458d47fe4413ba4bdaede1ea93e8556ddb01a158d0d74ccf109`。104份既有文件摘要不变，两个旧原run仍COMPLETED/REVIEW_READY（329/348事件），其保存history前缀保持。

新原workflow实际COMPLETED，outcome保留`CANCEL_UNCONFIRMED`及原未确认job；取消回执的`cancellation_confirmed`和`execution_success`仍为null。先核任务fence绑定同一request，再正式恢复专用executor，实际排队作业在模型之前被fence拒绝，发布唯一`CANCELLED`回执（`Task is fenced`）及一个摘要匹配的executor-error产物。恢复exit0、服务RUNNING，无新模型调用；没有修改原workflow结果、发外部对账或释放工单租约。外部对账页面属于下一c2切片。

保留三项验收脚本失败：初次stop缺必需`--confirm`、初次create缺`--definition/--preview-sha256`均由parser以exit2退出，分别未停止服务/未发布任务；核实际检查点后沿同一任务ID、正式预览摘要继续。首次直接history核验脚本把request SHA误取自intent，KeyError发生于恢复executor前；修为读取并校验原冻结spec后，v2 exit0（6.55秒）。这些不是产品合同变更，未重发取消、换ID或放宽门禁。

本片独立wheel的既有架构边界检查8项通过；`final-resource-syntax.json`终核348资源/两安装仍与初包逐字相同，13个JS模块语法通过，冻结283的构建核验保持。首次文档静态核验9份Markdown/316本地链接及锚点、27条README parser命令通过；后续审查报告和登记改动后再终核。桌面真实丢回复和390px回执截图已人工查看。无本地完整重型Python回归的新结论；精确提交仍需正常两OS CI与同片独立最终核对。下一先完成新fresh-context审查及交付，再进入c2显式外部证据/对账页面。

## 独立本地审查

[新fresh-context报告](2026-11-04-task-cancellation-console-review.md)需求符合性、可维护性均通过，无未解决findings。审查者实际重哈希348源码/wheel/两安装、104旧文件及原112history，直接只读SDK核三原run的329/348/112事件与唯一预期信号，并核取消GET与浏览器原record一致。守卫对应已演练的生命周期边界，没有新增通用框架或test/CI；性能结论限于实际请求数和无后台轮询，不声称测得全局优化。审查时指出F4总览两处过时状态，已在本地修正并独立复读确认。

四段浏览器完成后的`post-browser-invariants.json`另核无运行workflow、两个旧run各一个approve_plan、新run一个request_cancel及完整112history不变、新取消目录只有原ID三份journal、104旧文件不变、executor RUNNING。提交仅携带取消页面及相关文档（含B最终CI归档）；精确包/提交身份、推送、CI及同片终结复核仍分别登记，不先标完整F4完成。
