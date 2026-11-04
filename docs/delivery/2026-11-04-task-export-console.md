# F4.3d：网页精确候选导出与原回执恢复

日期：2026-11-04。状态：页面、独立发行、受控/真实浏览器及原ref/claim验收本地通过；[新的独立本地审查](2026-11-04-task-export-console-review.md)通过、无findings；提交/远端CI尚待完成。源码基线为F4.3c2本地提交`401bacb28cf99e121357860901c4d95332417dae`；c2本地及精确提交/包审查通过，SSH推送认证失败、精确远端CI待完成。本片使用独立发行和验收记录，不继承前片包或CI身份。

## 需求与所有权

从明确查询且已闭合、outcome为REVIEW_READY的原run进入导出，固定原run及完整candidate SHA；先读取原本地导出记录，再填写目标分支并明确确认。另提供不依赖运行查询的原记录检查/恢复入口。读取本地记录不查询Temporal或Git ref；历史exported回执不证明当前分支仍指向该候选。

复用GET/POST `tasks/{task_id}/export`和POST `export/resume`，`tasks.py`继续拥有revision/confirm与原意图准备，`reference_task_export.py`继续拥有原提交、精确REVIEW_READY结果、可信Git根、条件ref事务、原lease释放和原生export回执。浏览器不复制Git分支规则，不增加后端、格式、数据库、依赖或正式状态机。任务详情的局部工作区仍由现有`tasks.js`拥有；展示复用ui.js的文本安全DOM、事实列表和表单。

## 页面合同

1. 新导出只从本次明确读取的终态REVIEW_READY原run进入。固定run/candidate与当前项目修订，读取原记录成功且为not_recorded后才显示目标分支表单；不以输入框、浏览器缓存或当前项目默认值替换候选。
2. prepared表示原意图保存且尚无写前检查点，明确恢复可能首次创建原目标分支；unknown只核原分支，不隐式重新创建。branch_not_found继续显示未知并引导检查原分支/候选，不提供换分支或新导出以绕过原意图。
3. 已有prepared/unknown记录只以原intent SHA及记录返回的当前revision明确恢复，目标repo/run/candidate/branch保持不可编辑。exported展示历史回执且不再提供写操作；区分lease_released、checked_out、merged和execution_success=null，导出不代表开发成功、合并或推送。
4. 写前再次展示固定候选和目标分支。回复未知先读取此原任务的本地记录；不自动重试、恢复、轮询、checkout、merge、push或新建导出ID。写中锁读取，关闭或切换页面不撤销已发操作；旧详情/读取/被替换弹窗/底层run变化后的回复不得恢复旧确认。
5. 本地记录入口可在reload、清除浏览器任务/run选择后通过原任务使用；不要求Temporal在线，也不以not_recorded提供新导出。记录失败保持错误且无写入口。

## 验收计划

- 构建本片独立wheel和两份noneditable安装，核348源码/wheel/安装资源、283冻结文件、无SDK基础Web与13模块语法，运行已有8项架构检查。Python/测试未变时不重复本地完整重型套件；推送仍核精确双OS CI。
- 两模板真实GET读取原候选/本地not_recorded；受控not_recorded/prepared/unknown/exported、原intent恢复、branch_not_found、无新导出绕过、读取失败、旧revision、写中锁读取、编辑run/关闭/替换/跨项目任务迟到与390px。受控POST不转发并单独计数。
- 真实操作前快照全部原任务文件、完整三条history/outcome、3个claim/2个active，以及两业务repo的HEAD/refs/工作区状态。使用两个已有正常任务各一个新本地导出分支；不再调用模型或启动新workflow/signal。
- 至少一次真实成功回复故意丢失，reload/反复GET及清除浏览器选择后读取同一原intent/exported回执，不再次导出或resume。验证精确新ref、原repo HEAD/工作区及其他ref保持，原候选/native export一致；只有对应原claim释放，其余ledger/原文件/history/outcome保持。
- 更新公开使用/帮助和架构/计划，交新的fresh-context审查者核正确性、结构、必要守卫、读取/渲染成本及冗余test/CI。修后复核、提交包身份、远端精确双OS CI和同片最终审查通过后关闭d，再进入F4.4有界观察与完整页面旅程。

私有验收记录使用`.ergora/checks/f4-task-export-console/`与`output/playwright/f4d-*`，不进入公开仓库。当前生产只新增现有tasks.js详情内的导出工作区、固定REVIEW_READY候选入口及本地记录恢复入口，app.js帮助同步；没有Python、测试、CI或依赖变更。写中锁读取，prepared/unknown只传原SHA恢复，exported不再提供写入口。构建已开始，浏览器和原生导出尚未执行。

变更前只读快照已exit0：131份原文件、3 claims/2 active、三条完整history/outcome（329/348/112事件）和两业务repo的HEAD/refs/工作区。两repo干净，指定新分支不存在；从实际原outcome读取完整候选，未以手抄摘要作为导出依据。

## 独立发行与受控浏览器

首包`2d1bbafb9b3d85e8b5623fe45405cc15ec3451586b9d4d2280372086f283e41b`的uv wheel构建18.23秒，含建venv/两安装/核验整段39.68秒，均exit0。348源码/wheel/两noneditable安装逐项相同，283冻结文件保持；基础Web无Temporal SDK，13模块语法及既有架构8项通过。独立HTTP从本片development安装载入，未覆盖c2包或其验收身份。

受控两段浏览器已exit0：`browser-controlled`36请求/8拦截POST，`browser-boundaries`34请求/4拦截POST，均零pageerror、零转发写。两模板真实只读核原REVIEW_READY候选/本地not_recorded，覆盖四态、固定新run/candidate/branch/revision、只传原SHA恢复、unknown的branch_not_found保持未知、prepared明确恢复、exported无写、读取失败与非REVIEW_READY无新导出，以及390px。迟到段另核同dialog后读胜出、底层run编辑、旧revision拒绝、写中读取锁及程序触发也不发GET、替换dialog/切任务/切项目后的旧写回复隔离。浏览器fixture只证明页面边界，不当作原生Git/服务失败矩阵。

真实导出前`verify-native.py before`exit0，131原文件、三原完整history/outcome、两个repo的原HEAD/所有ref/工作区/工作树列表及3claim/2active与基线完全相等，证明受控写未落盘。两个真实原候选导出正在验收，尚未记原生写与新独立审查通过；不重复调用模型、工作流或信号。

## 真实导出与最终本地验收

四段成功浏览器共174页面请求/14POST，零pageerror：controlled 36/8和boundaries 34/4的12次POST全部拦截；native 76/2为两次真实单次导出，readback-v2 28/0。没有额外helper请求或resume。治理任务实际200/exported成功回复被故意丢弃，随后reload、反复GET、清除浏览器任务/run选择仍读回同一原intent；大型变更亦在reload/清选择后恢复同一回执。原生变更均沿已存在的两个原REVIEW_READY运行，没有创建新任务或信号/模型调用。

|原任务|新本地分支|原意图 SHA256|
|---|---|---|
|governance-f4c-normal-r1|agent/f4d-governance-f4c-normal-r1|42460976f64b989a63beb4979692c13e809e6cc31f079a44b3faf47c8780e48a|
|large-f4c-normal-r1|agent/f4d-large-f4c-normal-r1|f61ddb7b0c468bfb5cdef3aed50d0633cb9dbc830b8d6ab892a8d1bfdca37ad4|

`native-after-command.json`实际exit0（2.76秒），`native-after-verified.json`核131份原文件逐字保持，只新增每task的intent/attempt/result及原生export共8文件。两个新ref分别指向SDK原outcome的完整候选，其他ref、原HEAD、symbolic HEAD、工作区每份文件/状态及worktree列表全等。未checkout、merge或推送任何业务repo分支。

只有两个原正常任务的精确claim释放，依据分别为原outcome SHA `e971b6cd88e4bda0ec0eca9fe1e26e70ca8f5f2164c2aaafd41b78496d86622d` / `73a8b52c2d2ac1398580e47eef3cefcb2938558052a4165a64e0b2ebac707add`；claim其余字段及c2已释放claim完全保持，实际3claim/0active。三条完整history仍329/348/112事件且逐JSON不变，原结果仍REVIEW_READY/REVIEW_READY/CANCEL_UNCONFIRMED，无Running workflow。最终网页再次真实读取三个原结果，两个exported不再给写入口、取消任务没有新导出，原reconciled记录及开发未知事实保持。

已实际查看390px的治理exported顶部/租约与checkout/merge/开发未知事实、大型变更固定候选顶部截图，无横向溢出。首轮readback在390px点击原CSS隐藏的“使用指南”超时，原脚本/CLI/exit1保留，不计为成功段；v2只改为按现有桌面入口打开帮助后再检查390px内容，没有修改产品/扩大超时/重复真实导出。帮助在窄屏的直接可达性仍是既有页面范围限制，本片不宣称验证该入口。

下一对最终资源/文档再核后，交新fresh-context审查者核本片正确性、结构、实际请求/渲染成本及验证冗余；通过后提交并核包归档。GitHub认证未恢复前保留远端/精确CI未完成，不用c1/c2或历史Python回归代替本片交付。随后按F4.4分片接有界观察与完整页面旅程。

## 独立本地审查

新的fresh-context审查者先核原diff与调用/原生状态机，需求及可维护性本地审查通过，无findings。独立重算348包/源码/两安装、283冻结，原131文件/8新增、两个repo原HEAD/工作区/其他ref、原claim精确释放，并只读重取三条完整history/outcome与基线全等；四段CLI嵌入脚本/Result逐项相等，174请求/14POST范围保持。审查另作两次明确GET取原exported/not_queried回执，分别3.057/1.590秒，这两次不计入浏览器174请求，也不当作受控性能基准。

下一保存最终文档/README命令检查结果，提交本片并核归档=2d1b原包；GitHub SSH恢复前仍不能声称远端或精确双OS CI通过。后续F4.4按a1/a2/b/c分别实施与新审查，不以本片审查批准其代码。
