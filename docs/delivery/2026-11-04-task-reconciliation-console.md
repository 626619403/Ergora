# F4.3c2：网页外部证据与显式对账

日期：2026-11-04。状态：页面及本片独立发行、受控/真实浏览器、原claim释放和[新独立本地审查](2026-11-04-task-reconciliation-console-review.md)通过；一处耗时范围Low记录已修正关闭，无未解决findings。已提交401bacb并核归档=原包；当前SSH推送认证失败，远端精确CI与同片终结核对待完成。基线为已推送的F4.3c1 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`；c1精确CI41808523543及独立终结复核已完成，不由c2结果替代。

## 范围与所有权

接入既有GET `external-status?run_id=...&timeout=20`、GET `reconciliation`、POST `reconcile`与`resume-reconcile`，由现有`tasks.js`任务详情拥有局部工作区，复用api/ui组件。`tasks.py`、`reference_task_reconciliation.py`和原生FileAdapter/IngressLeases继续拥有完整history、job/回执/产物/fence校验、原claim及租约释放。没有新后端、数据库、格式、依赖或调度器；导出仍属下一d，完整证据索引属F5。

## 页面合同

1. 从明确查询且已闭合的固定原run进入“外部证据与对账”，读取该run的完整外部证据和本地原对账记录。显示原outcome、Temporal闭合状态、history job摘要、每个job请求/回执状态与摘要、fence、异常/未确认job，以及`external_confirmed`；读取本身不发布fence或释放租约。
2. 同任务详情另有“检查原对账记录与恢复”，只GET原本地记录，无需外部服务即可查看已保存事实。`not_recorded`只有从固定已闭合run进入且本轮外部证据读取成功才提供新明确确认；单独查记录不提供新对账。
3. 明确说明对账会重验原run、建立/复用同一fence，只有原外部job全部确认后才释放原工单租约。新操作固定run/当前revision/confirm；`prepared/unknown/confirmed`恢复只发送原intent SHA，不用当前run或页面值替换。`confirmed`只代表清理证据已保存，仍需恢复释放回执；只有`reconciled`表明原租约已释放并保存回执。
4. 只读观察、历史清理回执、实时外部确认、租约释放、原workflow outcome和开发成功分别表达。`CANCEL_UNCONFIRMED`原结果保持；`execution_success:null`不改为true或false。`reconciled`不再提供写操作，当前外部事实需再次显式读取。
5. 读失败不提供未经本轮材料支持的新确认，但已有原意图仍可独立查看/明确恢复；回复未知先读原记录。无自动对账、轮询、重试、删除证据或新建租约账本。写中锁读取；关闭/替换、编辑run、切项目/任务令旧响应失效，关闭页面不撤销已发操作。

## 验收与交付

- 使用本片独立非editable包/两安装与独立HTTP/浏览器会话，保留c1的a4081f包及原始证据；核348资源、283冻结及JS语法、既有架构检查。Python/测试未变时不重复本地重型回归。
- 受控页面验证五态、原intent恢复、新run准入、外部读取失败与本地记录独立、unknown未确认job、confirmed未释放、旧revision、关闭/替换/run/任务/项目迟到及390px。写全部拦截并和真实操作分别计数。
- 两个原REVIEW_READY运行仅GET，验证所有原history job及无fence时不会显示已确认清理，也不自动修改原候选。沿c1新的取消任务验证真实外部证据、明确一次对账，实际成功后丢回复，再reload/清浏览器选择按原任务恢复原记录，核唯一原intent、原outcome/history及request/receipt/artifact不变。
- 真实对账前保存本次相关文件与原lease行；只允许新取消任务原claim由占用转为带精确evidence摘要的释放，其他任务/租约不变。无模型调用或新workflow/signal，不手改ledger或journal。
- 更新本记录/PLAN与公开手册后启用新的fresh-context审查者，核正确性、所有权、复用、必要守卫、真实请求成本与冗余test/CI。修正后提交推送、核精确双OS CI和同片独立终结，才关闭c2；随后d导出和F4.4。

## 首轮实现

生产仅在现有tasks.js内增加局部对账工作区、已闭合run入口和独立本地记录恢复入口；app.js帮助同步。外部证据与本地记录读取使用各自Promise.allSettled结果，远端失败不会伪装成功或抹掉可读的原本地意图。新确认需要本轮外部材料，已有意图恢复只带原SHA；写开始后废弃先前观察，避免把变更前材料显示成实时事实。写中禁止读取，原详情/内容连接/读取及run代际限制迟到结果。无新Python、依赖、格式、测试或CI，本片尚无验证通过结论。

首包`3b9c800484bc328f839741e06aee4e77fed2899431e739918313c1bd101bdec1`的uv wheel构建14.82秒，包含建venv、两安装及身份核验的整段31.83秒，均exit0；348源码/wheel/两noneditable安装逐字一致，283冻结保持，基础Web无Temporal SDK，tasks/app语法与差异格式通过。使用独立HTTP与新浏览器会话，不覆盖c1包/安装。`native-before.json`在本片任何真实变更前只读保存127份原文件、三条原history及3个claim/3个active行；新取消任务原租约尚未释放。受控页面与真实对账分别记录，尚无本片原生写入或浏览器通过结论。

两模板受控浏览器v2已exit0：46页面请求/6拦截POST、零转发写/零pageerror。真实只读原REVIEW_READY的7/6个job均请求匹配且SUCCEEDED，无fence时external_confirmed=false，没有因读取自动建立屏障或释放租约；本地记录入口未查外部服务。fixture覆盖not_recorded→unknown→confirmed→reconciled、固定run/revision、只用原intent恢复、confirmed尚未释放、原outcome/开发成功不改写、写开始废弃旧观察、远端/本地读取分别失败以及390px。此段不证明原生对账已执行。

首轮脚本在第二模板把第一模板的3次受控POST累计进“本次读取前无写”断言，exit1；原失败脚本/CLI及只读取回的33请求/3拦截POST保留，不计为成功段。v2改为每模板读取前后比较同一计数，没有改产品、门禁、原任务ID或native文件。迟到边界、真实对账和新独立审查继续待完成。

## 本地验收与真实边界

私有证据在`.ergora/checks/f4-task-reconciliation-console/`，截图在`output/playwright/f4c2-*`；不随公开仓库提交。四段成功浏览器共139页面请求/10POST，其中9次受控拦截、1次真实原claim对账，没有pageerror：

|段|请求/POST|范围|
|---|---|---|
|`browser-controlled-v2`|46/6，POST全拦截|两模板真实外部GET、五态/原intent恢复、独立失败、变更前观察失效、390px|
|`browser-boundaries`|28/3，POST全拦截|迟到外部材料、底层run编辑、旧revision、写中锁读取、关闭/替换、切项目/任务的迟到写回复|
|`browser-native`|35/1，真实对账|单次精确原run/revision明确POST，实际200/reconciled后丢回复，reload/反复GET/清除浏览器选择后按原任务读取|
|`browser-readback`|30/0|三个真实原run的当前外部证据/原本地对账记录、帮助、390px顶部及真实释放事实视口|

真实变更前`verify-native.py before`确认127文件、三条完整原history/outcome和3个claim/3个active行都与基线一致，受控写没有落盘。真实新任务沿c1原run `01a1a5c0-06db-77fa-bbec-2ba74eb71ef1`，只允许一次`reconcile` POST；执行成功后故意丢弃回复，之后仅GET恢复，没有发送resume或第二次reconcile。

`native-after-verified.json`与实际脚本exit0（2.68秒）核：127份原文件逐字保持，仅新增原task的intent/attempt/evidence/result四文件。原intent SHA `75f71f0c68b0d3eb2c8060ad023514d4431580f7aa4428b790f4b236939b62d1`，清理/租约依据SHA同为`f0accdb828d820da45aab3051a6af0a92048845604afb07c7d42c31a565fbce0`；唯一原CANCELLED回执与证据摘要匹配。只有原claim `a53f23ac76be99e258984ed649f8671355c59f183f899f816bd3b160fcdb9762`的释放时间/依据更新、active移除，其他claim和active行完全保持（3 claim/2 active）。没有直接修改ledger或覆盖原owner。

三条原history仍精确329/348/112事件且全部JSON不变，原outcome分别REVIEW_READY/REVIEW_READY/CANCEL_UNCONFIRMED，无RUNNING workflow。新对账原记录的external_confirmed/lease_released为true，execution_success仍null；没有改写原workflow结果、新signal或模型调用。固定原任务读取即可恢复持久回执，无浏览器权威缓存或新对账ID。

8项既有架构边界检查通过。初包后生产未改，最终348资源/两安装及13模块语法另核；文档本地链接/README parser随后终核。本片不在本地重跑未改动的重型Python完整套件，精确提交仍需正常双OS CI与新的同片独立终结复核。

视觉范围：首次治理任务fullPage图片的dialog区域为空白，原图保留，未用它声称可读或推断根因。后续源码未变，最终只读旅程用实际390px viewport、双帧绘制与dialog顶部/几何核查，两个模板顶部和真实释放事实均已实际查看清晰；对应PNG作为视觉通过证据。没有为了截图修改产品或放宽宽度断言。下一完成新的fresh-context源码/实证审查及交付，再进入d候选导出。

## 独立本地审查

新的审查者从原始差异、调用方和后端合同独立审查，并复算348发行资源、127原文件/四新增文件、原lease唯一释放，实际只读重取三条history/outcome与基线逐JSON相等；核原始浏览器CLI/嵌入脚本/Result及最终可读截图。需求与可维护性通过，唯一Low是wheel构建14.82秒与整段发行核验31.83秒的记录范围，已分别命名并复核关闭。无新增生产改动或重型回归；最终文档静态检查与提交/精确CI仍需单独核对，完整F4/F5未完成。

提交前静态核验为本片10份Markdown、325个本地链接/锚点及27条README parser命令，均通过；下一d设计文档明确排除本片提交与静态范围。生产资源仍为原3b9c包身份，未因记录修正改变。提交后继续核归档/包、实时远端和本次精确CI。

提交`401bacb28cf99e121357860901c4d95332417dae`的348资源归档与原3b9c包一致，同片独立提交/两安装/最终静态摘要复核通过。正常推送和只读SSH核查均返回publickey认证失败，未取得本次远端SHA或CI，已请操作者恢复认证；不以此前c1的远端或CI替代本片。下一d可继续本地实现，c2保留交付未终结状态。
