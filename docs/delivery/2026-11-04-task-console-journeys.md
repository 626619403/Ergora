# F4.2c：两模板真实创建与提交组合旅程

日期：2026-11-04。状态：真实组合旅程、本地身份和持久恢复已验证，独立审查通过，文档已提交推送`581144c3d6205bb400577a79b694f53a8638cf15`，恢复后实时远端一致。前置[F4.2a](2026-11-03-task-creation-console.md)和[F4.2b](2026-11-04-task-submission-console.md)均完成；b已提交推送`f54c077f3f61dc5020147975dc34872dbabbe0e7`，精确CI41772980312两OS必要步骤与独立CI/实时远端终核通过。本片无生产代码变更，不改冻结协议以使验收通过。

## 范围与环境

使用同一最终541306包及新持久control/config/native/runtime、两业务Git仓库，不向F3/F4.2a/F4.2b任务试写。复用已安装完整依赖和Temporal二进制，初始化新的配置与可信检查；只迁移已核非凭据的模型配置，认证值仍由环境提供，不打印或复制凭据。默认端口须先核空闲，服务只管理本次项目登记的Supervisor栈，无宿主机权限需求。

分别登记repository-governance和large-change，使用已验证的小业务基线及独立可信检查。固定源码/安装包、基线、项目修订、实际有效绑定、输入草稿与可信检查摘要；服务启动前确认模型仅配置与认证存在性，实际调用成功另记。

## 可验收节点

1. 两项目各保存一份有效草稿，明确设置四个开发角色并发布统一登记；验证业务基线的可信检查。记录实际命令与失败，不把配置存在记成运行成功。
2. 显式启动自己的Temporal、worker、executor和必要服务，用正式readiness/doctor确认；浏览器从草稿→服务端预览→明确创建→检查提交→确认start取得真实原生run及本地回执。全部操作记录实际POST，任何受控响应另列，不能借F4.2b fixture记真实成功。
3. 读取固定原run及实际history，核workflow ID、原始spec、submission memo与intent、角色冻结及工作单元。若实际执行进入AWAITING_PLAN_APPROVAL，保存计划/摘要并保留人工等待；本片不自动批准。六阶段完整UI批准/取消归F4.3/F4.4，既有F3真实完整旅程保持原范围。
4. 关闭重开浏览器/HTTP，重新读取两原任务、创建/提交回执和run选择；不重新start，不依赖页面内存制造状态。可在明确预算内演练一次未知回复或服务失联后原ID恢复，区分实际断线与浏览器拦截的界面故障。
5. 只读核原任务/操作文件与历史证据，读取所有本次run的最终/等待事实。服务留作紧接F4.3时明确记录所有者/运行状态；结束验收时按正式shutdown并保留持久状态，不任意杀其他服务或清理原记录。
6. 更新本记录及PLAN，新的fresh-context独立审查检查真实请求、包/配置/候选身份、持久恢复和结构/成本范围。文档核查后提交推送；无代码变化时不重复重型回归或为纯记录再触发CI。

每个节点区分实现、实际验证及独立审查。环境/认证或服务受限时完成可测范围并登记缺口，不争取宿主机权限、伪造回执或将not_found当作可重提；下一功能仍按F4.3人工待办、F4.4有界观察、F5证据与G0综合验收推进。

## 实际进度

- 环境准备：私有`f4-task-console-journeys/prepare.py`实际exit0；最终541306包、新control/config/native/runtime和两个业务repo已创建。两个项目登记修订1，固定基线`f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`；治理3项、大改6项可信基线检查均通过。
- 模型配置：仅迁移非凭据白名单；认证变量存在，模型为`gpt-6.1-sol`，单阶段上限600秒、最多2个并行job。尚未调用模型，不能据此认定认证成功。
- 运行边界：显式接受可信当前容器，未尝试宿主机权限。`start-services.py`实际exit0，两个项目均明确绑定四角色Codex/model/current-container，修订1→5；默认端口空闲核对后，通过正式services start启动本次Supervisor栈。doctor实际`ready_for_real_tasks=true`；这只证明正式任务准入，不能将可选服务端口或认证变量存在等同于模型成功。HTTP页面已用最终非editable开发安装启动，尚未以此认定任务执行通过。
- 原始私有材料：`.ergora/checks/f4-task-console-journeys/`，含准备脚本、逐命令stdout/stderr和`environment.json`；均不提交公开仓库。

## 真实组合验收

最终wheel为`54130609fb4c873e5d38244f2fab5287695db648f5938156284a9ce677c3b393`；348文件与当前源码、wheel、实际开发安装逐字一致，源码仍为f54身份，包内283冻结reference身份保持。对新runtime另执行原`validate_installation`所要求的Python文件身份检查，不将其范围扩大到运行目录的全部文件。

|成功段|实际证据与范围|
|---|---|
|browser-normal|38页面请求，10真实POST：每项目各一次草稿校验、草稿保存、预览、创建、start；全部38响应正文保存。两个草稿修订1、项目修订5，冻结输入/七文件/角色与服务端预览一致；两次start实际200/submitted，页面保存真实原run并明确读取INVENTORY。0拦截、0pageerror，无批准/取消。|
|inspect-awaiting-v2|两个真实Codex inventory及plan共4个成功job；分别112个连续history事件。原始workflow input等于本次spec，memo等于原submission SHA，requests/receipts/全部产物摘要一致；每任务只有inventory/plan，无任何signal，均AWAITING_PLAN_APPROVAL。执行计划与回退文本已保存并实际阅读，不据此批准。|
|browser-awaiting-v2|36请求全GET；两原创建/提交意图、run、实际等待状态与DOM一致。submitted不提供再次start/resume；同标签reload保留选择，重新明确查询原状态，不显示旧权威结果。0pageerror。|
|browser-reopened|先核本次HTTP PID/命令/属主后SIGTERM，确认进程退出及端口关闭；实际关闭浏览器，再启动新HTTP和新浏览器。36请求全GET，两模板从持久后端取回同creation/submission及原run，继续同标签reload/明确查询；无写操作、无fixture、0pageerror。新浏览器不依赖旧sessionStorage。|
|browser-storage-free|另16请求全GET；明确清空会话选择并记录剩余0项后reload，显式选择两原任务。两次run选择键均为null，DOM输入仍等于实际持久submission的原run，0pageerror；不将“浏览器重开”本身当作亲查空storage。|
|check-identities before/after|新任务合同、requests/receipts/artifacts及本次ergora/approval/fence JSON共54文件逐字相同；不覆盖SQLite、workspace、进程数据、日志或锁。两个任务各2个job，未写人工批准/取消记录。|
|check-prior-native|F4.2b两原任务仍为原prepared且无attempt/result/rejection/requests/receipts；F4.2a原35文件/9意图及F3原416文件保持。|

三段**成功**浏览器旅程合计110请求/10真实POST，均没有传输拦截。首次只读浏览器辅助脚本误等待已折叠pre可见，超时失败；保留原脚本及日志，v2改为等待内容附着后通过。该失败尝试不计入110，也不算产品故障。首次history辅助脚本使用了错误的memo字段名而退出1，保留`inspect-awaiting.py`及initial-inspection材料；按实际`ergora.submission_sha256`合同修正后的v2实际exit0，不修改产品或原生记录。

正常浏览器脚本命令/完整CLI与Result分别保留；只读两段的外层`run-check.py`命令记录调用的browser-command及原JS，内层CLI日志同时保留实际执行代码和Result。成功结果JSON与CLI Result可以直接对照。已实际查看新浏览器大型任务的完整截图，计划等待、原run与候选可读；窄屏及模态框分支仍是a/b各自最终包验收范围，不额外声称本片重做所有390px测试。

浏览器close/open原输出当时仅留在工具记录；`browser-reopen-tool-transcription.json`是root明确标注的原工具输出转录，不是审查者亲自观察或补跑命令。已有HTTP退出身份、新HTTP启动日志和新页面快照另存。新增storage-free的实际CLI/command/Result直接记录了空会话及后端回执回填，不依赖这份转录证明storage状态。成功主旅程110请求与补证16GET分别记账。

## 留用与下一步

两个原run如下，均保留在本次专用Temporal，等待后续F4.3的明确操作；本片没有完成work/integrate/verify/review或导出。

|项目/任务|原run|待批计划SHA256|
|---|---|---|
|governance-f4c / governance-f4c-normal-r1|01a1a4e2-67b9-7bf3-986d-9dc0437ff134|5d233e8b03ecf759c18503f6fe69724020f4ab7d6208837186bc2ab02cd9d325|
|large-f4c / large-f4c-normal-r1|01a1a4e2-961d-7959-83b1-b962ce3d9767|42ff9bc800db7f82854011b6a9aea0261bce4c16623948aebd313efaaf7b900a|

本次Supervisor栈及重开的HTTP/浏览器留给紧接的F4.3验收。正式services status核daemon running、temporal/worker/executor/a2a/mlflow均RUNNING，未启动training-worker；这不是按监听端口推断服务完成。所有者为本次F4专用验收，不管理其他旧栈。待后续整体验收结束，沿正式shutdown并保留持久配置/SQLite及证据。

本片没有生产、依赖、测试或CI变化；不重复执行相同完整回归。结构/成本结论限于复用现有正式API、两个单模板项目和以上有界手动查询；没有后台自动派发/轮询，没有吞吐或费用优化的量化结论。完整F4/F5/G0仍未完成。


## 独立审查与交付

新的fresh-context审查者已写入[最终报告](2026-11-04-task-console-journeys-review.md)，需求符合性与可维护性均通过，范围内无未解决finding。审查者独立重算348源码/wheel/实际安装与54当前文件、原history input/spec/memo及4job全部产物摘要，核实际CLI代码/Result、110请求与补证16GET；另直接查询原服务确认两run仍各112事件、零signal、待批且无活动阶段，5服务RUNNING、training-worker STOPPED，并重算旧B/A/F3证据。浏览器close/open原工具转录与其直接核验证据分别列出，不把转录当独立重开观察。

本片文档已随581144c提交推送并实时核对远端一致，纯状态记账不重复重型CI；接续[F4.3a有界计划材料](2026-11-04-task-plan-inspection.md)。该组合验收的正式执行源码与精确CI身份固定为f54；完整F4仍未完成。
