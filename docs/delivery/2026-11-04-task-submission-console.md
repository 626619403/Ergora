# F4.2b：明确提交运行与原意图恢复

日期：2026-11-04。状态：页面、终包、浏览器状态/迟到/旧修订、文件检查及独立最终本地审查通过，待最终文档/提交CI收口。基线为已完成F4.2a提交`e63bc8ba9366b9ec798712fb402722f952f990a9`；其精确CI41763676211及独立终结审查通过。前置行为与证据见[创建页面记录](2026-11-03-task-creation-console.md)，原生语义见[提交合同](2026-11-03-task-submission.md)及[锁分段](2026-11-03-task-submission-locks.md)。

## 用户行为及所有权

正式任务详情增加显式“检查提交与恢复”入口。打开后重新读取原creation与submission，展示当前修订、原创建意图、冻结角色/合同、workflow/run及原submission intent；旧页面快照不直接成为写入授权。

|最新记录|允许的页面动作|
|---|---|
|creation非published或任一读取失败|展示原因、重新读取；不提供start或resume|
|published且submission=not_recorded|审阅冻结身份后明确确认一次start，携当前revision及creation.intent_sha256|
|prepared|展示尚无派发检查点；明确resume-start原intent，由原生合同决定是否可继续首次派发|
|unknown|展示原派发不确定；明确resume-start原intent，只由原生流程查询/补回执，不重发start；NOT_FOUND仍是未知|
|submitted|展示固定原run及本地回执，保存run选择，提供返回详情重新读取入口；不当作六阶段完成|
|rejected|展示归属拒绝/冲突原run，不提供覆盖、换ID或再次start|

复用GET `.../creation`、GET `.../submission`，POST `.../start`的`revision/creation_sha256/timeout`，POST `.../resume-start`的`revision/intent_sha256/timeout`。服务端仍沿`web → tasks → reference.task_submission → reference_task_submission`，保留doctor/admission、不可变意图、memo归属和写前派发检查点。HTTP超时或错误不证明操作未发生：提示保留原ID并重新读取本地记录，恢复需再次明确确认。

前端继续由`tasks.js`任务所有者实现局部对话框，复用`api/ui/modal/form`及既有facts/disclosure，不新增通用操作框架、后端、持久状态、schema、依赖、测试框架、CI或轮询。操作回包检查页面/详情代际、对话框内容和open状态；关闭/切任务/切项目后旧回复不覆盖新视图。已经发出的操作不因关闭页面撤销。

## 可验收节点

1. 完成上述读取、明确写入与五状态投影；重新读取会废弃旧操作确认，读取失败和操作未知提供原ID查询入口。
2. 构建新的非editable包，逐项核源码/wheel/两安装及冻结reference，13模块语法通过。已有后端不改时，以浏览器和现有CI验收，不额外重跑完整重型回归。
3. 在独立持久验收项目中检查真实creation/submission读取及实际被阻止的start；两开发模板的submitted、prepared、unknown/NOT_FOUND、rejected和丢回复/旧revision分支，以可控后端或浏览器响应明确标出模拟范围，绝不声称模拟即真实Temporal执行。缺服务/缺SDK不自动启动或安装。
4. 检查关闭/替换对话框、编辑或切换任务/项目及迟到写回复；桌面/390px、页面错误和实际POST数分开记账。保护F3及F4.2a原任务；不为验收改原意图或创建伪原生回执。
5. 更新README、USAGE、帮助与架构；新的fresh-context独立审查关注所有权、复用、未知不重发、回包生命周期和有界成本。记录实际证据后提交推送、核精确CI/远端。

F4.2c负责两模板草稿→创建→提交的真实组合旅程；计划批准/取消等完整人工待办归F4.3，运行观察与综合归F4.4。本片不提前宣称这些节点完成。测试用配置与运行材料留在持久验收目录，公共记录只存身份和可复查范围。

## 首轮实施

生产仅改tasks.js：原本地提交回执面板增加检查入口，详情所有者内的局部对话框重新读取creation/submission，并按上述状态展示明确start/resume表单。写回复失败后只给原ID和重新读取按钮；submitted保存原run选择，用户点击后返回详情再明确查询。每次读取废弃旧确认，页面/详情代际与modal存活约束迟到回复。未新增Python/API/状态机/轮询，后端准入和恢复合同保持。

后续补一行恢复查询事实及app帮助文案，README/USAGE/当前架构同步；生产范围为tasks.js/app.js。原生状态机、Python、测试、CI、依赖及冻结reference未改。

## 实际验证与身份

私有原始材料在`.ergora/checks/f4-task-submission-console/`。新持久control/config、两个新repo仅用于本片；只读复用原参考安装，未复制凭据或启动Temporal/worker/executor/模型。首次基础venv没有web extra，serve明确拒绝；随后离线安装同包的`[web]`才启动HTTP，原日志与命令保留，不修改产品依赖。

初包`862f3f2d5cf0ed1ecdf554b4a4fa37f8c623d6708e6efa4b2a91255af46620ae`保存在`initial-dist/`及`initial-package-identity.json`。当时348文件=源码/wheel/两安装、冻结283及13语法通过。最终帮助/恢复查询文案补充后的新包为`54130609fb4c873e5d38244f2fab5287695db648f5938156284a9ce677c3b393`，最终348文件与源码/wheel/开发和无SDK基础两非editable安装逐项一致，冻结283与13语法通过；`package-final.py`保存实际构建/安装/语法命令日志。独立审查者已重新算终包348身份，零差异。

|材料及候选|实际结果与范围|
|---|---|
|browser-blocked，初包862|29页面请求/8真实POST：两开发模板各preview/create/start/resume。4次start/resume返回实际400，明确重新读取后为原prepared且无attempt/result；两摘要payload正确。响应body未保存，脚本scope中的doctor解释不能充作已取得的错误正文，不从这里推导真实Temporal或模型已运行。|
|browser-fixtures，终包541|40页面请求/5POST均由浏览器拦截不转发，另5只读helper。两模板模拟start→submitted、原run选择、unknown/not_found仍未知、rejected无覆盖、丢模拟resume回复后明确GET恢复、读取503无写表单、最终help DOM通过。390px页面390/dialog352无横向溢出，0pageerror。|
|browser-late，终包541|17页面请求/2拦截POST，另1只读helper；持留读取后关闭/替换modal、持留resume回复后切任务和切项目，旧结果不替换新内容或改原run选择，0pageerror；无后端派发。|
|browser-stale，终包541|10页面请求/1真实resume POST，另1真实helper绑定PUT将验收项目修订1改2。旧确认实际400，保存正文为Project revision changed；随后GET显示当前2/原提交1、同intent及原冻结角色，0pageerror。未再次派发或编造回执。|
|verify-native|只读实际文件：两任务创建七文件等于原intent，提交intent摘要保持初包原值，均无attempt/result/rejection且无requests/receipts；F4.2a原35文件及9intent、F3原416文件保持。doctor快照不存在，未推导ready或具体失败原因。|

初次verify-native错误假定存在doctor.json，读取失败，原脚本保留verify-native-first.py；修为仅报告快照是否存在后实际exit0并保存verified-native.json，不将无快照记成ready=false。此前fixture执行前的审批deadline均未运行，也没有计作失败产品行为或通过。

已实际查看大型任务390px截图，中文可读、可见区域无横向问题；截图是可滚动长表单的一部分，不声称全部信息同时可见。上述fixture结果只验证页面分支，原始prepared及旧修订拒绝另有实际原生记录；真实成功提交组合旅程保留F4.2c。待文档终核、[独立最终续核](2026-11-04-task-submission-console-review.md)及提交推送/精确CI后关闭本片。

独立最终本地续核已通过，无未解决finding：审查者核源码/348终包身份、浏览器原脚本=command内容、CLI Result=独立result且exit0，实看窄屏截图；另直接核原生两任务文件/意图、F4.2a35和F3原416，零差异。静态脚本现复制到本片`check-documents.py`，结果保存本片`static-documents.json`，后续不覆盖其他切片。精确提交/CI/远端继续待实际证据。


## 最终交付

已提交并推送`f54c077f3f61dc5020147975dc34872dbabbe0e7`，父提交为完整e63bc8b；11文件只含2生产JS及9份Markdown。提交前15份Markdown/339本地链接锚点、26条README命令parser与diff检查通过；审查者独立核f54中348个包Git blob及15份文档摘要均与实际验证记录一致。

精确[CI41772980312](https://github.com/626619403/Ergora/actions/runs/41772980312)实际success：Windows126386731279的wheel/包身份/原生回归/PowerShell安装升级四必要步骤、Ubuntu126386731612的wheel/包身份/原生回归三必要步骤全部success。root与原审查者均直接核官方run/job HTML、完整commit、selectedJobId和必要步骤commit日志链接；原审查者另重算6份原始来源摘要并于2026-11-04 04:46:52–04:46:53 UTC实时ls-remote取得完整f54，0未解决findings。详见[最终审查](2026-11-04-task-submission-console-review.md)。

F4.2b完成。真实成功提交组合另在[F4.2c](2026-11-04-task-console-journeys.md)验收，不将本片受控页面状态扩大成真实执行结论；完整F4仍待后续人工待办与观察出口。
