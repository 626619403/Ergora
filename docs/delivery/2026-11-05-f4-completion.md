# F4.4c：完整页面旅程与阶段收口

日期：2026-11-05。状态：全部本地组合验收及最终退出完成，[新的独立综合审查](2026-11-05-f4-completion-review.md)通过，两文档P2修正关闭；纯文档f2b93d4正常提交推送及同片独立实时远端终结通过，完整F4已完成。前置a1/a2/b1/b2已完成；b2的77b334c精确双OS CI41896900471及同片最终独立审查通过。本片生产/测试仍精确77b334c，350资源最终包43e121不变，各片过去的真实写入与发行身份分别保留。

## 范围与基线

沿既有两开发模板、两个正常原run及一个已取消/对账原run，复用F4.2c创建/提交、F4.3b批准、c1取消、c2外部对账、d精确候选导出和F4.4a/b观察的真实证据。只作持久状态恢复与候选复验，不再启动模型、workflow、批准、取消、对账或导出。所有写操作的原始成功/回复丢失/原ID恢复仍以各自切片证据为准。

本片使用b2最终noneditable安装及原持久control/config/native/runtime。三个原run的完整history/outcome、139份原证据、三已释放claim/零active、两业务仓库的HEAD/refs/worktree/工作文件作为不变基线。服务操作仅限本次专用Supervisor栈及身份核实的本次HTTP/浏览器，不管理其他项目。持久数据保留。

## 可验收节点

1. **候选可独立复查。** 只读核两已导出本地分支仍等于原outcome/candidate/export intent；用`git archive`提取精确候选到新的验收目录，保留文件清单和摘要，运行登记时的可信检查与候选测试。原业务HEAD/refs/工作区不变。不将候选自身测试代替可信检查，也不将两个小项目的通过扩大为通用质量结论。
2. **全新页面恢复。** 关闭并核退出本次b2 HTTP/浏览器，重新启动同一包的新HTTP/浏览器，清会话选择。从后端重取两原合同/创建/提交、固定run/outcome、原批准/取消/对账/导出记录与事件/job材料；只GET，不从旧DOM或浏览器缓存还原事实。记录请求、失败、无重复副作用和实际可读范围。
3. **服务退出及原状态恢复。** 先核无Running workflow/未处理lease；通过正式`services shutdown --confirm`退出本次栈，核所属PID、端口及持久SQLite保留。服务不可达期间只查询本地合同/原操作记录，原运行查询明确失败。随后仅显式启动Temporal，确认三个原run/history/outcome及网页事件/job材料仍可从持久状态读取；worker/executor不启动，未触发新执行。最后再次正式shutdown并确认本次所有服务退出。
4. **公开边界与结构。** 更新当前架构/流程图、README及使用手册，区分Linux/WSL2完整执行与Windows控制面、历史回执与当前ref、请求/投递/实际执行/外部清理，以及有界响应和后端完整核验成本。保留F5证据索引/预算/交接及G0新用户验收未完成项。核文档链接/README命令与最终350资源/283冻结身份。
5. **独立综合审查与交付。** 使用新的fresh-context审查者核全部要求、实际组合证据、调用/所有权、必要守卫和测量范围。修正后只提交本片文档；无生产改动时使用b2精确源码/CI身份，不另跑完整重型回归或为纯记录重复触发CI。核正常推送与实时远端后才关闭完整F4，再细分并推进F5。

私有材料统一保存于`.ergora/checks/f4-completion/`，截图保存在`output/playwright/`，不提交运行数据或机器配置。软件/模型/API版本和各片发行身份按原证据保留，不用最新包追认过去所有真实写入。

## 候选独立复验

`revalidate-candidates.py`实际exit0，命令1.69秒。两个已导出分支分别仍指向原outcome、原export intent/result的候选`1d759a00ceb68fdc7c52261ace445268737165cf`（治理）与`46a53fef59d77bdcdfe7f4d912c2b6e53f6bb5e7`（大型变更），原意图摘要与lease_released匹配。精确Git archive解包13/14份普通文件，逐字摘要核对后运行登记时原摘要的可信检查：治理behavior/architecture/knowledge三类，大型变更再含integration/compatibility/migration-rollback共六类，全部通过。behavior内部运行候选自身unittest套件；本片没有再次运行同一套件或从隐藏输出推算测试数。

候选解包文件前后相同，两业务repo的HEAD、symbolic HEAD、所有ref、工作文件、status与worktree列表均与b2读后基线完全相同；没有checkout或新增worktree。原生组合前快照另exit0（1.99秒），139文件、三history/outcome、三已释放claim/零active、零Running保持。原始命令/日志、完整archive/提取清单和逐类检查在私有目录留存。

## HTTP、浏览器与服务恢复

已按原PID/UID/完整cmdline核对后向b2 HTTP发SIGTERM，进程退出且55981端口关闭；原浏览器显式close成功。随后从同一43e121 noneditable安装启动新HTTP和新浏览器。`browser-reopened`实际55GET/零POST/零pageerror、47.79秒，明确清会话选择后按原任务从持久提交取回run，显示三份原合同/创建/提交、两个原批准/一个原取消、两个导出/一个reconciled记录，原结果及事件/job材料均一致；390px三任务无溢出。`verify-browser-reopened`另核所有原intent/result/spec、两计划全文/回执、事件前缀和139原文件，exit0（0.17秒）。

正式服务退出首轮辅助脚本误将Supervisor包装命令当作Temporal直接argv，找不到`--db-filename`而在任何shutdown命令前exit1（1.72秒）；原脚本、日志及preflight保留。修后从实际Temporal进程argv核原持久DB，v2正式`services shutdown --confirm`exit0（7.78秒）、outcome confirmed。核零Running/零active后退出本次20个实际所属进程，四服务端口关闭、daemon/socket/PID标记退出，原Temporal SQLite保留；未移除失效标记或直接kill服务树。

`browser-services-offline`实际44GET/零写/零pageerror、27.39秒：服务全部停止时三任务的原合同/创建/提交/决策/导出或对账仍可读取，原运行查询明确返回失败并显示“运行查询失败”。浏览器记录一条预期失败资源console消息，未冒充无网络错误；没有fallback成成功、自动启动或重新提交。`verify-browser-services-offline`另核原意图/回执/合同及139文件，exit0。之后正式`services start ... temporal`exit0（4.98秒）且只有Temporal RUNNING，worker/executor和其他服务STOPPED；只重开持久历史，不触发执行。

`browser-temporal-restored`实际57GET/零写/零pageerror、48.75秒，重新清会话后恢复同三任务的原合同/所有操作回执/结果及两job计划全文；独立原intent/result/spec/事件/材料核对exit0（0.16秒）。三段组合共156GET，零POST，没有新的批准/取消/对账/导出或模型调用。只读snapshot在重启后及末次页面旅程后分别核全三条history/outcome、139文件、leases和业务refs/worktrees/工作文件相同；末次1.75秒、零Running。已实际查看重启后治理正常/取消两张390px任务合同截图，文本与长SHA可读；未据此声称截图展示屏外全部运行事实。

最后正式`services shutdown --confirm`exit0（3.17秒）、confirmed，核所属Supervisor/Temporal两进程退出、四端口关闭，daemon/socket/PID标记退出而原持久DB保留。浏览器显式close成功；按当前专用control、同UID与完整cmdline核实后，逐一SIGTERM关闭本次遗留9个HTTP，2.65秒、全部退出/端口关闭，未触碰其他control。首轮HTTP归属检查未预期早期`.venv-dev`相对入口，动作前失败；原脚本/日志保留，复核其原F4.2c启动PID日志与实际cwd后才纳入本次清理。

`final-offline-v2`exit0（0.53秒）：正式status返回daemon not_running/退出0，139文件及三已释放claim/零active保持，四服务端口关闭，control、Temporal、lease三个持久SQLite均保留；最终350源码/两安装及13模块语法再次通过（0.96秒）。末次辅助快照首轮把not_running退出码假设为3而失败，v2按实际daemon及原CLI允许码检查，未修改产品或放宽业务不变要求。

## 当前交付边界

F4.2c与F4.3各片已真实完成两开发模板创建/提交、计划批准、一个独立取消任务、终态外部对账及两精确候选导出；成功回复丢失和原ID恢复由各自原始记录证明，本片没有重放这些操作。事件与job消费者分别通过其独立源码/发行/真实与受控浏览器验收，最后UI源码`77b334c62346f92868c22c067949b0caf2d74d48`的双OS精确CI41896900471及原审查者提交/包/实时远端/官方原HTML终结均通过。当前架构图、39个顶层Python模块及新job边界已同步，公开手册增加服务依赖与离线恢复矩阵。

本轮组合不改变源码、依赖、测试、CI、schema或原六阶段合同；不为纯记录重跑完整重型回归/触发另一CI。实际模型使用原演示的Codex角色与Linux可信执行容器；Windows runner证明该提交的控制面/原生合同与PowerShell安装升级，不代表Windows完整Linux执行栈、真实模型/GPU或远端GitLab工单已验。候选复验只涵盖两演示repo及原登记可信检查，仍需维护者在合入时核当前目标分支/策略。

独立综合审查已指出并修正两个文档问题：旧F4恢复入口和总计划的c2/d/F4.4状态已同步至本次检查点；公开恢复矩阵区分已闭合run状态/结果和运行中workflow query，后者按原runtime实现还需要worker。本片三个原run均已闭合，仅Temporal恢复的实测结论限于该范围，未外推至运行中阶段查询。修正没有产品或运行数据变化，同片复核已关闭两finding；最终文档静态核查在提交前重核。

新的独立综合审查已通过；提交前最终静态检查覆盖本片10文档340个本地链接/锚点及27条README parser命令，均通过，`git diff --check`通过。纯文档`f2b93d4daba751a707af43755f2dd30fc19c74f8`已正常推送，独立审查者重新核精确提交/包/340链接/27命令和实时RSA远端全部通过；完整F4已完成。当前按[总计划F5](../plans/2026-11-01-all-in-one.md#f5-证据成本与交接)分片推进任务证据索引、预算/费用事实与可复查交接；G0新用户闭环及后续F6–F10仍未完成。
