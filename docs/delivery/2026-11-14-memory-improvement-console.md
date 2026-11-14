# F10d6a 原记忆保存与恢复页面交付

[具体合同](../plans/2026-11-14-memory-improvement-console.md)；实施基线 `ed7fac5ba6bbe5ec73da0fed7175c4705116ea5b`，前片已普通发布／完整Ref相同，自己的CI和原独立固定发布补核均已闭合。本片最终r2本地验收完成，独立最终本地两轴已通过，发布状态见文末。

初始盘点阶段检查原memory.save/catalog/history/restore/delete与HTTP／页面caller，先准备基线复现，当时尚未修改产品、执行模型或完成运行验收；后续实施与最终r2结果分别记录如下。不继承Skill片的包／评价结果为本片通过。原有效期、预期revision、跨项目隔离和删除不可恢复语义保持。

## 基线复现与实现决定

基线安装件的四个owner与`ed7fac5`逐字相同，身份见`.ergora/checks/memory-improvement-console/baseline-identity-r1.json`。原真实HTTP之后延迟回复，浏览器7项／5样本／3.175秒复现：历史覆盖后开的Help，保存关闭替代Help，恢复期间按钮仍可再次发请求（原CAS拒绝第二次状态迁移），同步回复跨项目打开窗口。另3项／2样本／2.293秒复现原CRLF正文在未编辑更正时变为LF；后端本身保持传入的完整Unicode。原记录与失败现象保留在`baseline-r1.json`及`baseline-text-r1.json`，不算修后验收。

修正沿原页面实现：历史先同步打开其专属窗口，后续回复只更新同一仍可见内容；save／restore／delete／sync使用同一局部提交回执，移除已发出表单的再次提交入口，成功后显示原记录、不自动关闭或刷新其他页面。Skill页已有同类实现，现有两个实际生产caller，因此上浮为小型共享模块，保留原评价锁及业务owner。更正未编辑正文保持原字符串；新增可选UTF-8正文文件供完整候选保存，严格解码并保留BOM／CRLF。异步读取文件后再次核对来源窗口才发请求。下一步执行源码、包与真实页面验收；此时未宣称修后通过。

## 首包与自有模板审查

r1非editable包604产品、wheel612条／安装617条RECORD、283冻结逐字核过；原memory／web／skills-evaluation三suite共59项通过／59.39秒（监督进程60.94秒）。未新增镜像实现的单元测试。自有原`ergora-structure-review`模板固定九个完整文件与继承资源，通过原CLI/Codex调用81.645秒，返回`request-changes`：共享表单的Skill回退caller传入被内部布尔`active`遮蔽的生命周期函数。该R1成立，源码将布尔改名`isActive`，首包保持，待实际红例与最终新包复验。测试脚本曾因内联过量夹具超过shell单参数上限而未启动浏览器操作；缩减为实际所需字段后继续，不计作产品失败或通过。

## 最终r2本地验收

最终三产品为原`memory.js`、原`skills.js`及两实际caller共用的新`submissions.js`；原Python／HTTP／数据库／评价与权限合同不改。未新增test或CI。公共使用手册补上完整候选文件保存、更正、恢复和未知回复的操作，当前架构记录共享实现和原owner。产品源码／构建快照／wheel／非editable安装604件逐字相同，两RECORD为612／617条、283冻结核过，wheel SHA256 `cc697e93e2100a7e47a908ea56fa104cd9a929a94f0b7be109519db1ccb89e83`。

|实际检查|范围和结果|
|---|---|
|最终原suite|`tests/test_memory.py tests/test_web.py tests/test_skills_evaluation.py`，59通过／57.48秒，监督进程59.05秒|
|记忆主旅程|20项／10样本／4.536秒；原CLI完整候选导出，页面从文件明确保存12,828B完整Unicode／BOM／CRLF及精确来源；未编辑更正保持原文、更正清期限、并发CAS拒绝、恢复追加修订保期限、到期不进新召回、跨项目隔离及三宽|
|最终完整生命周期|同一r2安装件的新夹具完整28项／15样本／6.778秒一次通过；迟到历史成功／错误、save成功／CAS错误、执行后丢回复与原记录、文件读取后窗口失效、严格解码前置错误恢复、目录与检索交错、restore／delete单次提交及Help保持、删除全部历史不可恢复、sync跨项目与明确rebuild|
|共享Skill旅程|23项／10样本／5.519秒；完整原UI导入、可信fixture suite双方评价、比较失效、明确采用和回退到原baseline revision3。原R1另在保留r1安装件实际7项／5样本复现，回退报`current is not a function`且零rollback HTTP；最终正例使用r2|
|布局|记忆主页面和Skill页各1440／960／390px；更正和历史窗口另6项／2.729秒，核完整长正文／来源且目视检查，无横向溢出。合计最终页面77项／35样本；不把早期失败片段相加冒充完整通过|
|原CLI|主记忆、Skill和最终生命周期夹具各原prepare/check/export三次，另5次记忆catalog/list/history/search/other读回，共14操作。页面保存与恢复到revision5的完整文本、来源和原history／catalog／CLI逐字同一|
|自身原模板|最终九完整文件61,069B及全部继承资源在原stdin，Codex61.176秒approve；run `67a190d136ea4327b0c11ab06a8a165a`。它与fresh-context独立审查分列|
|原件与收尾|最终三个r2夹具共130原HTTP、20次真held、4次执行后503夹具；其中新完整生命周期32原HTTP／8held／2丢回复。全量request/response SHA与原trace核同一。原候选／input／manifest／来源包／baseline历史／Git、原Skill来源／scorer保持；六服务PID／端口、三观察到的浏览器PID均已关闭|

## 保留的驱动失败

首包APIResponse采样误用`.request()`、Skill红例setup误包manifest、r2安装脚本误替换历史解释器路径、首次打开误填临时端口，以及生命周期脚本对检索词OR匹配、移动视口隐藏Help、HTTP完成不等于DOM刷新、续跑变量作用域的错误均保留。修正的是验收脚本，最终产品SHA保持；最终新夹具完整重跑28项通过，不能以各旧片段代替它。

原memory r1/r2驱动在uvicorn关闭socket后调用`getsockname`，退出前收尾日志阶段报错；原行为与逐份HTTP已保存，不称原finally成功。最终新生命周期驱动修正端口取值并正常完成原cleanup。另只读`audit-final-r2`核两个旧驱动进程／端口已退出、全部原材料与baseline保持；r2主夹具停机前原trace亦逐字核对全部76响应。错误、原件和独立补核分别记录。

## 当前出口与后续

本地验收与收尾已完成，原fresh-context独立reviewer已直接核242固定引用、全部604产品／两RECORD／283、130原HTTP及原trace、77项页面旅程、CLI全文／来源、自身原模板完整stdin、原件与收尾；最终本地需求／可维护性两轴approve，开放0／0，R1已实红／实绿关闭。[证据索引](evidence/2026-11-14-memory-improvement-console.json)保持242原引用，普通发布、完整Ref和本片自己的CI另验。前片F10d5固定发布与自己的CI43576070452已获原reviewer两轴终核approve／开放0／0。

候选提案和scorer使用显式合成夹具，仅验证合同。没有真实质量、训练性能或外部ReMe可用性结论；前端表单不构成跨浏览器执行去重。后继F10d6b沿原workflow import和精确新版本选择，之后F10汇总、F9d和G1分别验收。

## 普通发布

已普通发布`0fd74b16c98185081e06c4ef356700b881c781e7`至当前开发分支，14固定blob与完整远端Ref同一；未合main。242固定原引用保持，5份发布调用／回执另列。原reviewer固定发布补核已两轴approve／开放0／0，242原引用及五份发布调用／回执直接核同一。本片自己的CI43578921368八job／30必要步骤全部成功，原reviewer终态两轴approve／开放0／0；40条原CI引用单列，精确交付闭合。
