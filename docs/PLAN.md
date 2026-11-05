# Ergora 下一阶段计划与进度

> 最新状态（2026-11-05）：完整F1–F5、G0及[V5文档push分流](delivery/2026-11-05-ci-document-scope.md)均完成。V5精确51284fd双OS CI41950353820/df0a908文档事件窗口及[同片终结](delivery/2026-11-05-ci-document-scope-review.md)通过，02:03:23 UTC独立实时远端为df0a908；生产代码4c87c2a/352资源保持。当前[F6.1编辑器比较](delivery/2026-11-05-editor-comparison.md)初审两P2已修复，新Web环境/18请求回归/13资产逐字匹配及新旧试验数据保持通过；本片浏览器已关闭、新HTTP正式SIGTERM且实际shell143。最终静态、同片复审及精确交付待完成。

本文件是项目执行与上下文恢复入口。最后更新：2026-11-05。S0–S10 及 A0 计划已交付；用户已批准开始主线合入、审计、渐进重构与按优先级补齐功能，并要求每完成一步更新文档。各阶段详细计划只在对应链接内维护节点状态。

持续执行要求：用户已授权睡眠期间沿既有计划连续推进，无需每个子节点等待回复。每个完整切片均使用新的独立审查上下文；每个大节点额外核查代码结构、复用及性能，性能结论绑定实际测量条件。实现、验证、审查和提交推送分别记账，完成后继续下一项；权限或外部条件受限的维度明确记录，不阻断可独立工作。

下一可执行项：F6.1初审两项P2已在源码/结构化记录复审范围关闭；工具超时导致独立身份与部分原记录核对未完成，仍阻塞E6终结。下一按[F6 E1–E6](plans/2026-11-05-low-code-editor.md)作报告后最终静态、普通候选提交/推送与精确CI，再补同片独立核对；未满足前不登记完成。随后F6.2a编辑状态与缓冲所有权，再做撤销重做/修订与错误定位。默认前端及执行合同未替换。

## 当前检查点

最新可执行项在本文件末尾的“最近完成/下一可执行项”；下面保留各阶段交付快照，历史条目中的当时状态不替代该最新检查点。

- 前阶段基线：`3b52365`，实现分支 `feat/evolution-console`，S0–S9 已交付。
- 上一交付：S10 Windows 支持完成，分支 `feat/windows-support`，基线 `4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`；已验证运行代码 `9c196a9d27874d11befbcdf21a294f3a438697a7` 已推送。最终交接提交 `44c1c94d8c34ac3d6179eba91dfcd194ea9b005a` 是本轮源码基线；原 Linux 发行及冻结参考内容保持可比较。
- 当前交付：S11 / A0 完成，形成 [下一阶段详细计划](plans/2026-11-01-all-in-one.md) 和 [架构基线](architecture/2026-11-01-baseline.md)，静态核查及独立文档审查通过。主体计划提交 `7d9d246fccf7c8226e5028bfe52a97b7403726a6` 已推送 `feat/windows-support` 并核对远端一致；审查后仅补状态/交接信息，实际检查在 [A0 交付记录](delivery/2026-11-01-all-in-one-plan.md)。
- 主线交付：M1 完成。已从研究基线创建 `main` 并快进纳入 Windows/计划历史；主线提交 `ae5319d57f1a647c8ab8874039fd6245ce423e5f` 已推送并核对一致。main CI 41319564418（Windows/Ubuntu）成功，[独立审查通过](delivery/2026-11-01-mainline-review.md)，范围内无 findings；见 [主线交付记录](delivery/2026-11-01-mainline.md)。
- 审计交付：A1 完成，[调用与影响审计](architecture/2026-11-01-audit.md)和 113 文件 / 701 函数的日期索引静态核查通过，[独立审查通过](delivery/2026-11-01-audit-review.md)；训练人工执行边界 P2 已修正复核，无未解决 findings，见 [交付记录](delivery/2026-11-01-audit.md)。
- 兼容交付：A2 完成，分支 `refactor/architecture-foundations`，基线 `cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`，运行/测试/CI 身份 `4deb8b78690ba1c102c2b08aa6dd3c4054815d6c` 已推送。[兼容基线](architecture/2026-11-01-compatibility.md)、固定旧数据/摘要与 [边界 ADR](architecture/decisions/0001-refactoring-foundations.md) 已交付；Linux 144 passed、17 skipped、36 subtests passed，两 OS CI 41323798679 成功，[独立审查通过](delivery/2026-11-01-compatibility-review.md)，见 [交付记录](delivery/2026-11-01-compatibility.md)。
- 组件交付：R1 完成，`refactor/architecture-foundations` 上实现 `007a88e`、跨平台测试修正 `1cbc77e` 已推送；集中内置组件描述及 Python/CLI/Web/安装配方消费者。非 editable wheel 的完整 Linux 回归 152 passed、17 skipped、36 subtests passed，冻结 283 文件身份保持；浏览器 / 两 OS CI 41333003887 / [独立审查](delivery/2026-11-02-components-review.md)均通过，见 [R1 记录](delivery/2026-11-02-components.md)。
- 合同交付：R2 完成，基线 `9808870`，最终运行/测试 `d402d1b` 已推送。共享 schema / 字段错误 / 原身份规则已接入，初审 P1 数值边界已修正；最终非 editable wheel 的 Linux 172 passed、17 skipped、36 subtests passed，基础 CLI / 两 OS CI 41336217446 / [独立复审](delivery/2026-11-02-schemas-review.md)均通过，见 [R2 记录](delivery/2026-11-02-schemas.md)。
- 存储迁移交付：R3.1 完成并推送 `4d4d124`，基线 `0d86315`；16 表初始化、有序版本、迁移前 DB 备份与旧客户端拒写已接入。最终非 editable wheel 的 Linux 182 passed、17 skipped、36 subtests passed；基础 CLI / 两 OS CI 41337468262 / [独立审查](delivery/2026-11-02-state-migrations-review.md)通过，见 [R3 记录](delivery/2026-11-02-storage.md)。
- 存储恢复交付：R3.2 / R3 完成，最终运行/测试 `4fe2ec5` 已推送，Linux 202 passed、18 skipped、36 subtests passed，基础 CLI 完整恢复通过；两 OS CI 41340075293 / [独立审查](delivery/2026-11-02-state-backups-review.md)均通过，见 [R3 记录](delivery/2026-11-02-storage.md)。未迁移实际用户库。
- 本地验收交付：L0 [本地完整环境与 CLI 全流程验收](delivery/2026-11-02-local-e2e.md)完成并推送 `b80d90e`：独立持久配置与数据、两开发模板六阶段/导出、真实GPU微实验门禁/票据、控制面/调度/离线恢复均通过适用验收，[独立审查通过](delivery/2026-11-02-local-e2e-review.md)。取消原workflow保留CANCEL_UNCONFIRMED、沿原ID对账确认进程已停。未验范围保留；不替代R4–R8或未来F/G功能。
- 研究交付：L1 [DeepSeek Super-agent原型与Harness](research/2026-11-02-deepseek-agents.md)完成，已核实用户帖子指向及两个固定源码，记录50文件来源；报告和F2–F10/D3验收细化已写，84个本地链接/50文件提交身份/静态差异核查及[独立审查](delivery/2026-11-02-deepseek-research-review.md)通过。Thread图表标注已修正；未安装或接入DSH，文章全文未取得。
- 默认分支：M2 完成。用户已设置，2026-11-01 15:30 UTC 远端 HEAD 实际指向 main，与当时主线 `0027f3f` 一致，[独立核对通过](delivery/2026-11-01-default-branch-review.md)，见 [设置记录](delivery/2026-11-01-default-branch.md)。
- 用例交付：R4 [用例所有权与依赖整理](delivery/2026-11-02-application-use-cases.md)完成，运行/测试 `f9a9b74` 已推送；非editable包Linux206 passed/18 skips/36子测试、基础21次CLI符合预期，最终35项定向和两套324文件身份通过。精确候选CI41380351919两OS成功，[独立审查及最终CI复核](delivery/2026-11-02-application-use-cases-review.md)通过，无未解决findings。
- DeepSeek参考项已在[详细计划 L1 执行清单](plans/2026-11-01-all-in-one.md#l1-deepseek-agent-管理工具调研用户追加)按DS1–DS7关联F1–F10/D3：有效配置、意图/回执、人工待办、事件/授权、可选DSH、受评价改进及隔离实测。均待对应节点实施；不整包替换当前执行链。
- 生命周期交付：R5 [运行契约与平台生命周期](delivery/2026-11-02-runtime-contracts.md)完成并推送 `d685bb9`，远端SHA已核对；生产身份仍为 `f9a9b74`。已形成[结果/产物/平台矩阵](architecture/2026-11-02-runtime-contracts.md)，无额外源码抽取依据；Linux最终43项/5跳过、固定Forge/mini SDK及SIGINT/KILL探针、106链接/283冻结身份通过，[独立审查](delivery/2026-11-02-runtime-contracts-review.md)通过。保留mini首轮超时及未验维度。
- 边界交付：R6 [reference访问边界](delivery/2026-11-02-reference-boundary.md)完成，运行代码`277ec1f`已推送并核对一致。Web模板读取已归入reference接口，[已有边界/退出清单](architecture/reference-boundary.md)已写；Linux206项+36子测试/18跳过、324文件×两安装/21次基础CLI、104链接/283冻结身份及精确两OS CI41388048791通过，[独立审查](delivery/2026-11-02-reference-boundary-review.md)通过；原六阶段、冻结绑定和证据身份保持。
- 前端交付：R7 [CLI/Web与前端模块化](delivery/2026-11-02-console-modules.md)完成，实现`ad73bec`及窄屏修复`b8bee53`已分别提交推送，远端SHA一致。12模块/入口149行及资产diff已归位；最终包Linux206项+36子测试/18跳过、335×两安装、21次基础CLI/30次API对照及完整浏览器旅程/390px六页与图通过。精确候选CI41410702773两OS成功，[独立审查及最终远端复核](delivery/2026-11-02-console-modules-review.md)通过，无未解决findings。
- 重构出口：R8 [交付](delivery/2026-11-02-refactoring-exit.md)完成；当前架构/13项清单/ADR及8项边界检查已写，初审两项已解决。实现/测试46ac633已推送并核对远端；最终wheel Linux214项+36子测试/18跳过、335文件×两安装/21次基础CLI/10种反例及精确两OS CI41421965020通过，[独立复审和精确CI/远端最终核对](delivery/2026-11-02-refactoring-exit-review.md)通过。应用源码保持R7身份。
- 配置交付：F1.1 [有效绑定与运行快照](delivery/2026-11-02-project-configuration.md)完成，实现/测试`d914ea724e87495fb5efcd92e12f50b5931fc42c`已推送且远端一致。初审两项P2已修正；最终wheel222项/36子测试、18跳过，335文件×两安装/28次基础CLI、桌面及390px六页/三模板浏览器、精确两OS CI41440299977和[独立复审/最终远端核对](delivery/2026-11-02-project-configuration-review.md)通过。当时完整F1尚未完成，当前状态见下方F1阶段检查点。
- 研究补充：LC1 [低代码编辑器研究](research/2026-11-02-low-code-editors.md)完成并随`d914ea7`推送；7个固定仓库/18份来源及官方文档复核、[独立审查](delivery/2026-11-02-low-code-editors-review.md)通过，作为F4/F6设计依据。未安装竞品或改变图形库。
- 注册交付：F1.2已推送`a6fd291`且远端一致，最终wheel255项/36子测试、18跳过及337文件×两安装、[独立复审](delivery/2026-11-02-project-registration-review.md)及精确两OS CI41448910719通过，见[注册记录](delivery/2026-11-02-project-registration.md)。
- F1阶段交付：单一项目及有效配置全部完成；[F1.3旧注册预览/显式采用/恢复](delivery/2026-11-02-project-import.md)及tracker合同补修已推送`4ffcfdd`且远端一致。最终wheel281项/36子测试、18跳过、337文件×两安装/8次CLI、精确两OS CI41485234297与[独立最终复核](delivery/2026-11-02-project-import-review.md)均通过，无未解决阻塞，见[F1阶段记录](delivery/2026-11-03-f1-completion.md)。F2进度见下一检查点。
- 安装组合交付：F2.1已完成，[记录](delivery/2026-11-03-installation-profiles.md)。运行/测试`8201c5d`已推送且远端一致；最终wheel288项/36子测试（18跳过）、337文件×两独立安装/实际Bash安装一致、Linux5次安装/22次CLI、精确两OS CI41495971680及[独立最终复核](delivery/2026-11-03-installation-profiles-review.md)通过，无findings。默认control与旧参数兼容，development/research按同源配方加装SDK。下一项为F2.2诊断状态与修复指引，之后F2.3服务管理、F2.4综合验收；完整F2尚未完成。
- 诊断交付：F2.2已完成，[分项诊断记录](delivery/2026-11-03-readiness.md)及[独立最终审查](delivery/2026-11-03-readiness-review.md)通过。生产`1f78235`、最终测试`ede2dc2`已推送且远端一致；最终包337文件×两安装一致，Linux308项/36子测试（18跳过）、基础无SDK两次CLI、实际浏览器卡片/切页/390px/延迟响应及精确两OS CI41508379597均通过。两P2已关闭；诊断性能测量仅说明请求内去重。当前[F2.3显式服务管理](delivery/2026-11-03-services.md)已完成源码独立复审及24项定向检查，两P2关闭；最终包338文件×两安装与大日志性能通过，完整回归/精确两OS CI和最终收口进行中，[F2.4综合旅程](delivery/2026-11-03-f2-acceptance.md)的Linux5次安装/48次CLI与两次HTTP重开通过，独立综合审计及精确CI待收口；完整F2尚未完成。
- F2阶段交付：F2.3[服务管理](delivery/2026-11-03-services.md)及F2.4[综合旅程](delivery/2026-11-03-f2-acceptance.md)均完成，最终生产/测试`67d88ec`已推送且远端一致；最终wheel338资源×各安装一致、冻结283通过、Linux324项/36子测试（19跳过）、5次安装/48次CLI及API、精确两OS CI41514705189和两份独立最终审计通过，无未解决阻塞。完整F2完成；当前[F3.1正式任务只读入口](delivery/2026-11-03-tasks-read.md)已实现，审计修正后34项源码定向/26项独立合同检查通过，三P2关闭；最终包339文件×两安装/冻结283一致，完整回归/新性能/精确CI与最终审计待收口；后续编译/提交/批准/取消/导出分段实施，完整F3尚未完成。
- 正式任务读取交付：F3.1[记录](delivery/2026-11-03-tasks-read.md)完成，生产`13e9f33`/最终测试`e9b53f7`已推送且远端一致；最终wheel339文件×两安装/冻结283、Linux350项/36子测试（19跳过）、旧任务只读复验/1000合同分页测量及精确两OS CI41521060898和[独立最终审查](delivery/2026-11-03-tasks-read-review.md)通过。首轮Windows夹具失败与修正均保留。当前[F3.2显式创建/恢复](delivery/2026-11-03-task-creation.md)已实现CLI/API与专用原生边界，初轮26项创建/82项联合定向通过；审计大意图P2已修正，36项源码定向及独立复审通过，最终包341文件×两安装一致，完整回归/基础旅程/精确两OS CI和最终审计待收口，之后F3.3运行操作和F3.4完整旅程；完整F3尚未完成。
- 正式任务创建交付：F3.2[记录](delivery/2026-11-03-task-creation.md)完成，生产/测试`b680221`已推送且远端一致；审计大意图P2修正并关闭。最终b361…wheel341文件×两安装/冻结283、Linux378项/36子测试（19跳过）、无SDK基础两模板127次CLI旅程/测量、精确两OS CI41525112557及[独立最终核对](delivery/2026-11-03-task-creation-review.md)全部通过；不包含工作流启动。当前F3.3a只读原生状态已实现/定向验证，独立审计和发行验收进行中；完整F3仍待后续运行变更及综合旅程。
- 原生任务状态：在F3.2精确CI独立收口期间，[F3.3a](delivery/2026-11-03-task-runtime.md)已实现只读task status CLI/API，26项原Transport/SDK协议定向通过；原始spec、run ID及未知/未确认终态均保留。独立源码审查及342文件×两安装、真实服务NOT_FOUND/旧文件不变/无SDK指导通过；完整包回归及精确CI/最终审计待完成（真实存在run的查询留待F3.4）；F3.3b提交和F3.3c批准/取消尚未实施。
- 原生状态交付：F3.3a[记录](delivery/2026-11-03-task-runtime.md)完成，生产/测试889d9b49已推送且远端一致；816b…wheel342文件×两安装/冻结283、Linux396项/36子测试（19跳过）、实际旧任务NOT_FOUND只读旅程及精确两OS CI41528801888和[独立最终审查](delivery/2026-11-03-task-runtime-read-review.md)通过。真实存在run留待F3.4；当前推进[F3.3b显式提交/恢复](delivery/2026-11-03-task-submission.md)，之后批准/取消和综合旅程，完整F3尚未完成。
- 任务提交实施：F3.3b[记录](delivery/2026-11-03-task-submission.md)已接CLI/API、创建所有者复用、原准入及写前dispatch检查点；首轮定向/初版发行验证已通过；独立审计两项P1/P2已修源码（竞争归属memo/严格原history JSON），71项源码定向及独立复审通过，两finding关闭；最终f8d92f…包343文件×两安装、441项/36子测试（19跳过）和72次无SDK基础CLI旅程通过，最终归档/精确CI核对中。未知NOT_FOUND不重发，不标完整F3完成。
- 任务提交交付：F3.3b[记录](delivery/2026-11-03-task-submission.md)完成，97567b9已推送且远端一致；最终f8d92f…包343文件×两安装/冻结283、Linux441项/36子测试（19跳过）、72次无SDK基础CLI/限定性能、精确两OSCI41566783007及[独立最终审查](delivery/2026-11-03-task-submission-review.md)通过。两finding关闭；当前进入[F3.3c1精确批准](delivery/2026-11-03-task-decisions.md)，c2取消、d锁改进及F3.4旅程待完成。
- 并发跟进：F3.3b最终包的真实共享SQLite锁探针（受控connect延迟18秒）确认其他项目写者15.04秒busy失败、无部分写入，提交后明确重试成功；已将F3.3d修订保留/远程等待分段列入F3.4前P0，保持不可变意图及同任务锁，不凭快速fixture声称无并发影响。
- 精确批准实施：F3.3c1[记录](delivery/2026-11-03-task-approval.md)已实现CLI/API、稳定decision ID、原owner回执与原run精确signal/history恢复。首轮105项及NOT_FOUND补充7项定向、独立6项/4个真实SDK内存分页探针和[源码审查](delivery/2026-11-03-task-approval-review.md)通过，无finding；最终053212…wheel344文件×两安装/冻结283、Linux477项/36子测试（19跳过）、86CLI与18秒并发探针通过；精确两OS CI和最终审计待完成。准备意图与远程阶段分段，不把requested当批准已采用；c2取消、d提交锁迁移及F3.4仍待完成。
- 精确批准交付：F3.3c1[记录](delivery/2026-11-03-task-approval.md)完成，b3b7d65已推送且独立远端SHA一致；最终053212…wheel344文件×两安装/冻结283、Linux477项/36子测试（19跳过）、86CLI/18秒并发、精确两OS CI41572513289及[独立最终核对](delivery/2026-11-03-task-approval-review.md)通过，无未解决finding。当前c2取消实施，d锁迁移及F3.4仍待完成。
- 取消实施：F3.3c2[记录](delivery/2026-11-03-task-cancellation.md)已接CLI/API、原Transport.cancel的实际signal检查点、稳定request ID和原history操作SHA对账；原spec/memo/已提交读取及流式history与c1实际共用。六种闭合状态明确不发新信号，不把requested或already_closed当外部已停；首轮152项、独立5个SDK分页/21类journal及源码审查通过，无finding；345文件×两安装/冻结283、90CLI和18秒并发、最终Linux522项/36子测试（19跳过）均通过，c3113ad已推送且远端一致，精确两OS CI41576751862及独立最终本地/CI/远端核对通过，C2完成；当前D源码联合回归及新独立审计进行中，F3.4待实施。
- 提交锁交付：F3.3d[记录](delivery/2026-11-03-task-submission-locks.md)完成，765c39a已推送且远端一致；c774ba…包345文件×两安装/冻结283、Linux528项/36子测试（19跳过）、72CLI、18秒并发、固定C2十态升级及六历史项目兼容、精确两OS CI41580249518和[独立最终审查](delivery/2026-11-03-task-submission-locks-review.md)全部通过，初审创建锁P1关闭。远程等待不占共享DB；初次提交额外0.79–0.97秒的观察范围保留。下一项F3.4a候选导出，完整F3尚未完成。
- 已交付平台范围：原生 Windows 控制面、CLI、项目 / 记忆 / Skill / 资料观察及支持的原生工具；完整六阶段与 Linux 专用工具走 Linux/WSL2。后续仍按实际能力逐项验收。
- 验证：Windows / Ubuntu CI 41225920073 全部成功；Linux 完整回归 115 passed +36 subtests。两个切片最终独立审查通过；Linux 用户目录 0.2.0 升级和 314 文件身份一致。真实模型 / GPU / winget 空白系统等未验收范围保留在交付记录，不从 CI 推导。
- 恢复要求：重读本文件及活动切片记录，对照分支、工作区和最近提交；完成核对后继续当前项，不重新做已验收的调研。

## 从调研收敛的决策

既有 [协作工具调研](research/2026-10-28-multi-agent-landscape.md) 和 [持续演进调研](research/2026-10-28-continuous-evolution.md) 保留为日期快照。下表是本阶段的实施选择，避免直接把候选清单全部装入默认环境。

|层与能力|采用方式|本阶段的实际范围|
|---|---|---|
|项目合同、六阶段、可信检查和证据|迁入现有实现|保持三个模板及已有边界；不另造完整 DSL 或第二套开发生命周期|
|持久控制、实验观测、工单与通信|继续复用 Temporal、MLflow、Symphony、A2A|保留参考发行与接入位置；新增控制面不要求外部工单才能使用|
|角色与工具选择|自行实现项目绑定与能力检查，复用实际工具接口|实现者、审查者、记忆、优化器、资料来源分别配置；区分“可配置”“已安装”“已连通”“已验收”|
|项目记忆|SQLite 持久基线 + 外接 ReMe|自行负责项目范围、来源、修订和删除；ReMe 负责现成记忆整理与检索，不复制其引擎|
|skill 资产与改进|Agent Skills 目录、版本化候选 + 可选 GEPA|自行负责候选、评价输入、证据、采用和回退；GEPA 负责搜索和反思算法|
|主动资料探索|先做有界资料检查与研究任务，后接调度|来源、去重、成本与结果归属由项目控制；继续复用 Temporal 调度，不启动无预算的后台探索|
|代码与架构演进|使用既有项目任务和分支流程|先交付可审查候选与评估，不让生成器直接修改当前运行的核心或评分规则|
|图形入口|自有轻量控制台，复用成熟 Web / 图组件|先项目、绑定、记忆、skill 候选与证据；再支持协议允许的 DAG 配置和运行视图。前端与 CLI 共用服务逻辑|
|程序演化、权重训练、更多完整 harness|保留适配方向|ShinkaEvolve / OpenEvolve / Agent Lightning / Letta Code / Hermes 按真实任务再接，不列入本轮默认必装|

## 切片与验收

状态分别记录实现、验证和独立审查；只有三者完成才标为完成。

|切片|交付与验收|实现|验证|独立审查|
|---|---|---|---|---|
|S0 计划与恢复|本计划、简短 AGENTS 恢复规则、明确工具归属；随 S1 审查|完成|已验证|[通过](delivery/2026-10-31-s1-review.md)|
|S1 公开源码与软件包|从已发布 HTML 提取可信源码、三模板和手册；记录内容身份；独立包可安装，合同及现有参考命令有可复验入口|完成|52 项 + 36 子测试通过|[通过](delivery/2026-10-31-s1-review.md)|
|S2 项目与工具绑定|持久项目配置、分层选择、实际能力检查；不支持的选择明确报错；CLI 与后续 Web 复用|完成|9 项通过|[通过](delivery/2026-10-31-s2-review.md)|
|S3 长期记忆|项目范围、来源与修订、检索、纠错/删除、跨进程恢复；SQLite 基线与 ReMe 接口使用同一语义并记录后端|完成|2 项集成测试通过|[通过](delivery/2026-10-31-s3-review.md)|
|S4 skill 改进闭环|导入标准目录，生成/导入候选，固定评价集与评分，比较基线、保存失败及成本，明确采用与回退；接 GEPA 的有限优化|完成|10 项通过|[通过](delivery/2026-10-31-s4-review.md)|
|S5 有界资料研究|指定来源抓取、版本去重、来源快照与提案；任务预算、失败和取消可见；验证后再接持久调度|完成|11 项回归通过；既有服务重启恢复通过|[通过](delivery/2026-10-31-s5-review.md)|
|S6 图形页面|项目导航、各层工具表单、记忆与来源、候选 diff / 评价 / 采用、受约束 DAG；浏览器走通关键操作，无页面自造的正式状态|完成|5 项 API + Chromium 关键操作 / 窄屏 / 延迟响应通过|[通过](delivery/2026-10-31-s6-review.md)|
|S7 交接与发行验证|安装、CLI、Web 和参考三模板说明一致；全量相关检查、公开内容核对及独立审查；保留真实未验证项|完成|隔离 venv / home 安装通过；110项+36子测试；新增安装器及独立5项通过|[复审通过](delivery/2026-10-31-s7-review.md)|
|S8 三模板 Agent 选型与解耦|分方向调研真实 Agent 实现，分离模板语义与 Agent 适配，再通过同合同评价替换或补充现有 Agent；包括 ForgeKernel kernel 调优候选|完成|最终110项全量+36子测试；信号反例 / 原生CPU / Chromium通过|[治理](delivery/2026-10-31-s8-governance-review.md)、[大型开发](delivery/2026-10-31-s8-development-review.md)、[训练](delivery/2026-10-31-s8-training-review.md)复审通过|
|S9 最终提交与远端推送|全部任务完成后核对范围、验证及独立审查，提交并推送到 Ergora GitHub 分支，记录远端地址、分支与提交号|完成|360 个变更文件公开检查通过；提交推送并核对远端 SHA 一致|前序切片均通过；[交接核对](delivery/2026-10-31-handoff.md)完成|

## 新增任务：三模板 Agent 选型与解耦（S8）

用户追加要求：分别为当前三个模板所需方向调研较好的 Agent 实现，整理代码以便接入其他 Agent，使模板与 Agent 实现解耦；调研后用合适的实现替换或补充现有 Agent。此任务接在当前 S5 / S6 与首轮发行验收之后，保持现有可用工作流，再按方向逐个迁移。

1. **S8.1 分方向调研与选型表。** 以三个模板的真实角色、调用链及证据要求为出发点：仓库治理的代码理解、知识地图、依赖边界、架构审查与回归；大型开发的规划拆分、实现、集成、测试与独立审查；训练优化的实验规划、参数搜索、训练/推理性能分析、kernel 调优与正确性复验。记录官方来源和固定版本、许可证、输入输出接口、运行依赖、模型及硬件要求、可替换范围、优缺点与实测证据。重点调研 [OpenBMB/ForgeKernel](https://github.com/OpenBMB/ForgeKernel) 作为 kernel 调优 Agent 的替换或补充，也比较既有 KDA 等候选；不将候选直接标为已接入或已优于现有实现。
2. **S8.2 解耦 Agent 与模板。** 沿用现有 JSON 合同、六阶段与业务所有权，抽离当前模板隐含绑定的 Agent 调用。模板只声明目标、角色、所需能力、输入输出与验收；项目配置选择具体实现。复用现有工具绑定、进程执行与证据存储，为真实消费者增加适配；明确取消、恢复、产物和失败语义。不支持的能力显式拒绝，凭据继续使用环境变量，不在模板中硬编码某个 CLI、厂商或本机路径。
3. **S8.3 按证据替换 / 补充。** 为各方向选出首批实现，在相同任务输入和正确性合同下比较基线与新实现，保存失败、耗时、资源 / 报告成本和产物身份；需要 GPU 或外部服务而未实测的项目标为待验收。ForgeKernel 首先以可选适配参与 kernel 候选生成，正确性与性能复验仍由项目可信评价负责。保留基线和可回退选择，通过验证后再调整推荐配置。
4. **S8.4 CLI / 页面 / 文档一致。** 工具选择按角色或所需能力展示已实现的适配，说明安装、认证、兼容性及实际验收范围；三个模板、两本手册与示例同步更新。每个方向作为独立切片接受新的独立审查，不以配置可填写代替真实接入。

验收要求：同一个模板无需修改正文即可切换至少两个已实现的兼容 Agent；模板源码不导入具体厂商实现；适配结果能被既有证据门禁消费；缺少能力、未安装和调用失败可辨识；原三个模板合同回归保持通过。涉及模型 / GPU 的效果结论须有实际对比，未具备环境时保留明确的未验证状态。

## 最终任务：提交并推送 GitHub（S9）

用户明确要求整个任务处理完后推送到远端 GitHub。此项属于交付完成条件，不能只留在本地工作区。待前序任务、所需验证及独立审查完成后：

1. 核对 Git 差异、公开内容、第三方来源与文档；不提交密钥、登录状态、运行数据或验收缓存。
2. 在当前工作分支提交，核对 `origin` 指向 `https://github.com/626619403/Ergora.git` 或其等价 SSH 地址；先检查远端变化，避免覆盖他人工作。
3. 推送工作分支并核对远端提交一致；不强制推送，不擅自合并默认分支。
4. 在交接记录写明完成项、实际验证范围、未验证限制、远端分支及提交号，并向用户提供可打开的链接。若推送因权限或网络失败，保留提交并明确记录实际阻塞，不标记为已推送。

## 仓库与数据归属

- 本仓库包含应用、模板、测试、文档及必要的参考源码；运行配置、凭据、记忆、候选实验和日志放用户持久目录，不写入仓库或临时目录。
- 新配置采用版本化 JSON 与结构校验。skill 继续采用 `SKILL.md` 目录；正式执行合同延续既有版本，界面布局与执行语义分开。
- 保留旧参考分发作为可比较基线。新增模块需要实际 CLI / Web / 执行消费者，不为候选工具清单提前建立整套插件平台。
- 项目与工具的取消、隔离、恢复能力按实际接口显示；共享用户执行边界不宣称提供强隔离。

## 完成记录与下一阶段

每个切片的检查命令、结果、发现与修正记录在 `docs/delivery/`，在本文件链接对应记录。提交、推送沿用用户已授权的分支交接方式；不覆盖远端其他工作。

S0–S10 后续范围现在由 S11 详细计划承接；尚未测得收益的优化能力保持候选状态。项目许可证仍待维护者选择，第三方源码按具体许可保存来源与声明。


## S10：Windows 支持（2026-11-01）

原始要求：“进一步实现一个 windows 版本”。本轮提供相同控制面的 Windows 原生安装和运行路径，并明确完整参考执行器 / 原生优化工具的 Linux 依赖；不复制第二套工作流或业务实现，不改冻结 283 文件。

|切片|范围及验收|实现|验证|独立审查|
|---|---|---|---|---|
|S10.1 原生运行适配|移除导入级 fcntl 阻断；跨进程互斥；原生 Agent / evaluator / proposer 的 UTF-8、超时及整棵后代清理；抓取取消、预算与控制器异常退出边界|完成|Windows / Ubuntu CI 41225920073 通过；Linux 115 项 +36 子测试|[最终复审通过](delivery/2026-11-01-s10-runtime-review.md)|
|S10.2 安装与交付|用户目录 PowerShell 安装 / 升级及外来入口保护；Windows 手册与平台能力提示；跨平台 wheel / CLI / Web / 回归 CI；Linux 无回归；提交推送|完成|Windows 真实安装 / 重复升级及完整 CI 通过；home 升级通过，运行代码远端一致|[最终复审通过](delivery/2026-11-01-s10-delivery-review.md)|

验收使用真实 Windows runner 执行 Windows 路径，不以 Linux 上模拟 os.name 代替。本轮已通过实际 Windows / Ubuntu CI，历史失败、修复、独立审查及未验证范围记录在 [Windows 交付记录](delivery/2026-11-01-windows.md)。

## S11：all-in-one、重构与功能补齐

详细节点、前置依赖、验收、迁移/回退及状态统一维护在 [2026-11-01 详细计划](plans/2026-11-01-all-in-one.md#5-执行节点及进度登记)。[架构基线](architecture/2026-11-01-baseline.md) 保存本轮已核实的模块、调用链、格式与重复候选；它不是未来结构已实现的声明。

- A0：仅计划/盘点文档；按 [交付记录](delivery/2026-11-01-all-in-one-plan.md) 记录静态核查、独立审查和推送。
- M1/M2：正式主线及 Windows 合入、GitHub 默认分支设置分别验收。用户最新授权覆盖 S9 当时“不擅自合并默认分支”的交接限制；保留历史、不强推。默认分支管理认证待补时继续不依赖它的工程工作。
- A1/A2、R1–R8：函数级调用/重复审计、行为保护、组件/合同/存储/用例/平台/reference/前端逐项整理，再做重构出口验收。
- P0：单一项目、安装运维、正式任务 CLI/API/页面、证据与预算的完整用户旅程。
- P1：低代码、逐项目工单、真实可选 harness/会话、训练实验与受评估的持续改进。
- P2/P3：通信、远端隔离、搜索/格式互操作、多用户与规模化，按固定版本和真实需求分阶段验证，不进入默认必装。

每次上下文压缩、换机、节点切换后，重读本文件、详细节点及其交付记录，核对 Git 后从未完成项继续。M1/M2/A1/A2/R1–R8/L0/L1/F1/F2/F3.1–F3.3 已完成；F3.4a候选导出亦已完成；F3.4b1只读证据子节点亦已完成，测试成本V1–V3亦已完成，b2显式外部对账亦已完成；当前推进c/d真实旅程，完整F3尚未完成；尚无实际业务用户数据迁移，各 M/A/R/F 节点只以登记表和交付证据为准。

最近完成：[F3.4a候选导出](delivery/2026-11-03-task-export.md)，生产/测试ef8068a；最终346文件/两安装、591项/36子测试、74CLI、旧记录兼容/18秒锁测量、精确CI41589227955及最终独立本地/CI/远端复核全部通过，身份与范围见交付记录。

正式外部证据交付：[F3.4b1](delivery/2026-11-03-task-external-status.md)完成，生产/测试a2349e8已推送；52d26d…包347文件×源码/两安装/归档、冻结283、59项定向、无SDK两模板27CLI、18秒读取/22.78ms跨项目写者及精确两OS CI41597961138通过。独立终结审计核原HTML/实时远端与全部身份，无未解决finding；P1孤立回执漏检已关闭。完整F3仍等待b2与c/d/e。

最近完成：[V1测试输入分层](delivery/2026-11-03-verification-input-layers.md)及[V2平台提前跳过](delivery/2026-11-03-platform-test-scheduling.md)/[V3过时CI取消](delivery/2026-11-03-ci-scheduling.md)。原36反例语义保持、29轻量/91首轮及修后12项通过；V2的115测试/152顶层函数AST、323案例/fixture保持，40项定向通过。V1的4e01a4e/CI41605898404和V2/V3共同d558885/CI41612623462均已推送并通过两OS及各自最终独立提交/CI/实时远端审查，无未解决findings。Windows步骤390→212秒仅记两次运行观察；真实重叠取消未演练。下一可执行项：[c/d真实两模板正常/重启异常验收](delivery/2026-11-03-formal-task-journeys.md)，b2已完成；之后e综合收口，再进入F4页面，完整F3仍未完成。

用户新增并行审计：[测试与CI审计](delivery/2026-11-03-verification-redundancy-review.md)已形成，实测纯输入用例的重型初始化成本，并核实Linux晚跳过和CI重叠触发条件；没有建议删除的生产守卫。后续[V1–V3成本跟进](plans/2026-11-03-verification-efficiency.md)按输入/集成分层、平台提前跳过、CI过时运行分切片验收；不因“重复”直接删除故障反例或放宽门禁，V1已完成；V2/V3亦已完成：已推送d558885，精确两OS CI41612623462及各自最终独立复核通过。

最近完成：[F3.4b2显式终态外部对账](delivery/2026-11-03-task-reconciliation-write.md)，生产/测试`7139d1a85cdce13689d75471620da8dd143156a8`已推送且独立实时远端一致。最终c741…wheel347文件×源码/两安装/冻结283通过；Linux711项/36子测试（19跳过）、无SDK两模板27CLI与18秒并发边界通过；精确两OS CI41621015706及[独立最终发行/CI/远端审查](delivery/2026-11-03-task-reconciliation-write-review.md)通过，0 findings。原CANCEL_UNCONFIRMED保留，不改变b1只读合同或宣称完整F3完成。

当前实施：[F3.4c/d真实服务旅程](delivery/2026-11-03-formal-task-journeys.md)，使用相同最终包、新独立持久运行栈和两个新业务repo。两任务经过真实Codex inventory/plan，错误计划批准无信号、正确计划各一个信号；均完成六阶段进入REVIEW_READY，固定原run与精确候选。完整history302/326事件、7/6原job与产物身份、正式候选导出/独立worktree可信检查及4/11项测试、两次HTTP/CLI重开44请求均通过；c新独立审查通过，快照范围P2已修正关闭。b2文档已推送a170dd1且远端一致。d两新任务已通过真实worker停止期间取消/重开、8个直接采样的helper/child/driver/timeout进程消失、原CANCEL_UNCONFIRMED保持与显式对账释放、13HTTP重开；另实测baseline检查失败阻断和只读monitor两种126拒绝。d独立审查通过、timeout/monitor范围P2已修正关闭；[e阶段收口](delivery/2026-11-03-f3-completion.md)已更新README统一旅程、公开使用/训练手册及当前架构/导航。347包文件/两非editable安装/冻结283及README命令parser核对通过，本地链接/锚点已重核通过；核5原run闭合且无运行workflow后已正式shutdown本次专用栈，持久数据保留。[新独立综合审计](delivery/2026-11-03-f3-completion-review.md)需求/可维护性均通过、无新增findings；当前提交推送和远端核对后登记完整F3完成，再进入F4页面。

最近完成：[完整F3 CLI/API](delivery/2026-11-03-f3-completion.md)已收口，c/d与e三份新独立审查均通过，证据范围P2均关闭；当前源码/测试7139、同一347文件最终包711回归/精确两OS CI身份保持。文档已推送449a5be9f20d5d6b1789e178725b4b7d690e4261且实时远端一致；五原run闭合、专用栈正式shutdown及持久数据保留已核。

当前实施：[F4.1正式任务只读页面](delivery/2026-11-03-formal-task-console.md)。当前3f287e…wheel348文件×源码/两非editable安装、冻结283及13模块语法通过；新会话五原run/刷新/390px、分页/错误、14阶段及真正dashboard等待/失败/A→B→A累计129GET通过，视觉段另9GET及可读中文截图已核；保存/刷新两反例22请求（2模拟POST不转发）通过。R1–R3已修；416原证据文件前后完全一致，5原run闭合/无运行workflow与专用栈正式shutdown confirmed、持久SQLite保留已核。执行环境重开后仅清理经PID/socket/inode/属主核验的失效服务标记，再只起Temporal确认/正式退出。原初审上下文已不可用，[新的独立最终审查](delivery/2026-11-03-formal-task-console-final-review.md)代码/本地证据通过，无未解决finding；8份Markdown305链接/锚点与26条README命令终核通过；生产候选11e89cf44eb29fe9064bd0015417cf6bc54fdc5e已提交推送，实时远端和精确两OS CI核对中。首包44后端测试与F3历史711结果保持各自范围。下一按分片推进[F4.2a预览/创建与原ID恢复](delivery/2026-11-03-task-creation-console.md)，再接F4.2b提交与F4.2c组合验收；a的实施/验证清单已写，尚未实现；完整F4/F5/G0仍未完成。

恢复后检查点：F4.1远端仍为11e89cf且一致；精确CI41662193234 Windows全部必要步骤成功，Linux原生回归超过20分钟上限被取消，官方run/job HTML已保存，不能关闭完整交付。先用原已安装3f287e包作同源Linux回归诊断，不扩大超时或删除测试来隐藏结果。[F4.2a](delivery/2026-11-03-task-creation-console.md)已首轮实现任务页局部预览/创建/原ID读取恢复及CSS，尚未构建/浏览器验收/独立审查/提交。两片身份及验收分别记录；继续完成可独立的F4.2a验证，之后F4.2b；完整F4未完成。

2026-11-04追加：[V4 CI即时进度](delivery/2026-11-04-ci-regression-progress.md)已写，原wrapper结束后才输出日志导致超时缺逐例定位证据。仅改回归输出/有界尾部，保留套件/矩阵/退出码/20分钟；实际YAML的成功、失败、信号及结束前输出三个探针通过，新的独立审查待进行。原3f287e包完整Linux诊断仍在运行，未套用历史711结果。[F4.2a](delivery/2026-11-03-task-creation-console.md)已构建独立无SDK包并准备两个新持久项目，未复制凭据或启动模型/执行服务；浏览器真实首个治理任务已发布，脚本在模态框外等待不可见标题失败，保留原记录后修脚本，尚未记验收通过。V4独立提交不携带待验收的页面源码。

最新验收：原3f287e包Linux完整诊断为711 passed/36子测试、19跳过、1warning，2550.05秒，exit0；精确远端20分钟取消仍保留为未通过。V4初审尾部字符界限P2已修为3500字符，三探针新身份通过，待独立复核/提交/新精确CI。F4.2a两模板真实正常浏览器旅程通过，34页面请求含3预览/2创建，另2只读辅助检查；预览=服务端、编辑废弃确认、创建不start、选择重载、390px弹窗/页面均无溢出且无pageerror。后续重复/中断恢复/迟到请求边界及独立审查尚待完成，未关闭F4.2a。

提交前检查点：V4[独立修后复核](delivery/2026-11-04-ci-regression-progress-review.md)通过，尾部P2关闭，无未解决源码finding；独立提交只含CI和文档，应用包仍是11e89cf原348文件。F4.2a本地源码尚未提交；正常两模板和显式重复创建已通过，正验证旧revision/真实部分发布恢复，不能从V4提交推导页面已交付。12份文档318链接/锚点和26条README命令已静态通过，提交前再核当前差异；随后推送V4同源候选并取得新精确CI。

最新检查点：V4已独立提交推送`2137a95418879d48cce557016caa5c7f0d6a6a1b`且实时远端一致，只有CI/文档8文件；应用/测试树=11e89cf，新精确CI41679431542核对中，未继承旧取消为通过。[F4.2a](delivery/2026-11-03-task-creation-console.md)初包两模板/重复/旧revision/实际pending与conflict恢复已通过，保留原修订1角色且当前修订2。补原ID发出前选择保存及读取失败恢复入口后，最终421c81…包348文件×源码/两非editable安装、冻结283/13语法及两模板正常34请求/5真实POST、390px通过；回复丢失/迟到边界、实际文件终核和独立审查进行中，未提交该片。F4.2b/c与完整F4仍待后续。

2026-11-04恢复检查点：V4精确CI[41679431542](https://github.com/626619403/Ergora/actions/runs/41679431542)两OS及全部必要步骤成功，绑定完整2137a95；F4.1和V4两位独立审查者均已最终通过。原11e89cf的Linux超时取消记录保持；2137仅CI/7文档，348应用文件仍与原3f287e包一致。两位审查者的终结段因自动审批服务deadline未落盘，待归档，不误记为安全拒绝。F4.2a最终421c81包的lost-response为8请求/2POST，真实发布后丢回复、reload按原ID取回同intent；late为14请求/5POST，编辑/关闭/替换及跨项目迟到隔离通过，0pageerror。最终三段合计56页面请求/12POST；可读桌面/390px及原ID恢复截图已查看。[独立源码与证据审查](delivery/2026-11-04-task-creation-console-review.md)已落盘、无finding，实际文件终核和额外只读入口/帮助文案、文档终核/提交CI待完成。未成功生成或执行verify-created.py和browser-final-readback.js，不引用其为通过；不重复已有重型回归。

当前实施：[F4.3a原run待批计划有界读取](delivery/2026-11-04-task-plan-inspection.md)，接续已推送581144c且远端一致的F4.2c。五个现有生产文件内接入task plan CLI/GET API，复用原提交归属、SDK分页/codec、安全路径与有界文件读取；轻量合同测试已写但尚未执行。待完成源码定向、公开文档、最终非editable包/冻结身份、两原run只读材料核对及新的独立审查，再提交推送核精确CI。保留两待批run，零批准/取消；F4.3b页面批准及后续F4.4仍未完成。

F4.3a验证检查点：计划读取/批准/原运行/架构联合源码定向90项通过（266.68秒），首轮失败及修正均在本片记录；7文件303本地链接/锚点与27条README parser命令初核通过。非editable包与无SDK基础Web安装正在构建，新fresh-context只读审查已启动；尚未记真实两run只读验收、精确CI或提交通过。

F4.3a本地验收完成：最终4160cfdd包348源码/wheel/两非editable安装、283冻结、无SDK基础Web及32项wheel合同通过；两真实原run计划CLI/API一致，三材料6849/7889字节与原artifact相同、错误run exit2/错误plan HTTP400，54原证据不变、两history各112事件/零signal。[新独立审查](delivery/2026-11-04-task-plan-inspection-review.md)已归档，本地无finding；本片测试HTTP显式SIGTERM后PID/端口退出，原执行栈保留。尚待提交推送、精确两OS CI与同片最终复核，之后F4.3b页面审阅/批准及原decision恢复。

F4.3a已提交推送`14100cd8d9efca270e0a93d9a6c1b77fde9ed66c`，实时远端一致，提交前8文档315链接/锚点及27条README parser命令通过；精确CI41781897332仍在运行，未标完整切片完成。下一[F4.3b页面审阅/精确批准/原decision恢复](delivery/2026-11-04-task-approval-console.md)调用链和最小设计已写，尚未实现。先收口A精确CI与同片最终复核，再交付B。

并行实施检查点：A精确CI41781897332仍进行，Windows必要步骤成功、Ubuntu回归未结束。B网页计划审阅/原decision消费者首轮已写在现有tasks.js，单模块语法通过，公开说明同步；尚未构建或发任何批准。B使用独立验收venv，保留A的4160cfdd包及两安装，两个切片不混记身份；待浏览器/独立审查与A收口后交付B。

F4.3a已完成：14100cd精确CI41781897332的Windows126415114987/Ubuntu126415115241及全部必要步骤成功；同片独立终结报告实际核原HTML、完整commit/selectedJobId/log URL与实时远端，无未解决findings。A文档终结状态随下一片提交归档，不重复纯状态CI。B初包6524ae的348文件/两专用安装/冻结283通过；真实只读首轮在390px发现材料描述段长SHA使dialog scroll542>352，DOM和截图已归档，已改用既有facts的长值换行，未增加CSS/库或放宽尺寸断言；修包和浏览器重验待完成。

F4.3b恢复后进度：修后f81edf包348文件/两安装/冻结283与两模板22GET只读浏览器通过；390px溢出已关闭。受控边界另40请求/4拦截POST、零转发/零pageerror，prepared/unknown/精确intent恢复、材料与读取失败、旧revision及编辑/关闭/换run/跨项目迟到隔离通过；非editable架构8项通过。两个专用演示计划已实际审阅，54原文件摘要保持；当前准备显式批准（各至多一个有效信号）与真实丢回复/原ID恢复，尚未记原生批准或独立审查通过。

F4.3b本地验收完成：最终4fcdb9包身份通过，任务模块与真实批准f81edf包相同，仅帮助文案变化。四段成功浏览器144页面请求/6POST（4受控不转发、2真实），各run一次精确信号及丢回复/原ID恢复通过；最终25GET读取两原run均REVIEW_READY，54文件/112历史前缀保持。原子进程暂时超时400与窄屏帮助脚本失败均保留、未放宽产品超时。新的独立审查及提交/精确CI/实时远端待收口，再推进取消/导出页面。

F4.3b独立本地审查通过：新fresh-context报告已归档，348文件/两安装/283冻结、144请求/6POST、原54文件/112事件前缀与实时329/348历史各一个事件113精确信号已独立核；两原run COMPLETED且outcome REVIEW_READY。无findings，下一提交仅含批准页面与相关文档，下一取消计划单独保留；精确两OS CI及同片最终远端复核尚待完成。

最新推进：B已提交并推送c54230eb8a6d3468ef33e6365c874a4e3a2407d6，归档348=最终4fcdb9包，同片独立提交/包/实时远端复核通过。精确CI41797567476仍In progress，待必要步骤及终结审查。下一[F4.3c1取消页面](delivery/2026-11-04-task-cancellation-console.md)首轮消费者已实现，尚待语法/独立构建/浏览器和新审查；C与B保留不同发行身份。

B完成/C1当前：B已获精确双OS CI41797567476和原审查者终结核原HTML/实时远端，无findings。C1首包a4081f8d的348文件/两noneditable安装/冻结283、基础无SDK和tasks语法通过；两模板受控取消浏览器40页面请求/6拦截POST、另2辅助GET、零转发/零pageerror通过，未记真实取消。下一验证迟到/失败与独立新任务真实取消及原ID恢复，之后新fresh-context审查、提交/精确CI。

F5.3a本地检查点：原生收集/无State离线验证已接线；修正首轮控制Python3.11/原生3.12的schema二进制依赖耦合，外来manifest入口才加载StrictValidator，收集端保留原生完整性与字节重核。最终352资源2a0f829包、97项定向及三个原run/43份材料逐字节对照通过；前后139文件/三history/outcome/两repo/claims/leases相同，正式退出与独立审查及精确交付收口中。HTTP下载、页面、完整F5/G0尚未完成。

F5.3b首轮实现：Web严格POST仅run/timeout、私有临时目录收集/有界读回核SHA并先清理后发送，未新增生产模块/依赖/持久账本或CI作业。9项404真实红例后16传输+9架构25项通过；独立包、真实本地HTTP/原生/离线复核、新独立审查及精确交付尚待。a片精确87538b3正常推送/352资源归档同cdf4ab及同片独立提交/实时远端复核通过，精确CI41921284766仍进行。

F5.3b本地独立审查通过：[新审查报告](delivery/2026-11-05-handoff-download-review.md)独立核352资源/两安装、43原材料/离线CLI、139文件/Git/leases与正式退出，范围内无findings。a精确双OS CI41921284766及同片终结已通过；b生产/测试/54548b包身份保持，提交前刷新包含a终结和宏观计划记账的完整清单/静态结果。下一正常提交推送b并核精确双OS CI，期间可独立实现F5.4页面，完整F5.3/F5/G0尚未完成。

F5.3b已正常提交推送`bde57e17d84a0063683be9c5c34392072b255853`，352资源归档=54548b包、实时远端一致；提交前10文档346链接/锚点及30 README parser命令通过，精确CI41925067903仍进行、同片交付复核待收口。下一[F5.4证据/预算/交接页面](delivery/2026-11-05-task-evidence-console.md)设计与验收已写，尚未实现；复用现有任务详情、原job窗口、API和下载辅助，不自动收集。

F5.4首轮已在原tasks/api/ui三个前端所有者实现按需索引、预算/未知量和SHA核对后下载，复用原job窗口与请求世代；任务模块语法通过。公开手册/架构同步，全部模块/最终包/真实浏览器和新独立审查尚待，不改后端/冻结或新增测试框架。F5.3b精确CI仍在途，不推下一生产候选。

F5.4发行/真实首轮通过：f644858包352资源/两noneditable安装/283冻结、13模块语法及10项包内定向；浏览器三原run34请求/3真实收集、原索引/43材料、无SDK离线CLI、桌面/390px通过，取消结果保持。受控失败/延迟/分页与原数据终核、服务退出和新独立审查尚待；F5.3b精确CI在途。

F5.3完成：b精确CI41925067903的Windows126907187498/Ubuntu126907188269全部必要步骤成功，原审查者独立核原HTML/精确commit/log URL及实时远端bde57e1并终结，无未解决finding。a/b原包、原43材料和CI各保持独立身份；下一F5.4边界验收/原数据与服务退出及新审查，不继承b作为页面运行验证。

F5.4本地验收收口：受控十项证据场景111请求/6拦截POST、独立文本代表1GET通过；脚本语法/JSON比较及未加载模板超时保留原失败，未更改产品/包身份或将exit1写为通过。前后139文件/history/Git/leases相同，浏览器/HTTP有序SIGTERM（shell143）和专用栈正式shutdown通过、五端口关/三库保留。新独立审查及精确交付待完成，随后F5.5。

F5.4新独立本地审查通过：[报告](delivery/2026-11-05-task-evidence-console-review.md)核需求/所有权/复用/必要守卫/成本及实际包/浏览器/原材料/数据保持/退出，范围内无findings；未重复重型矩阵，第三轮脚本失败和恢复分项证据保持。下一终核文档/清单，普通提交推送、精确双OS CI及同片终结；F5.5/G0尚未完成。

F5.4已提交`4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`，352资源Git归档同f644858包；提交前10文档344链接/锚点及30命令通过，普通推送及自己的双OS CI收口中。[F5.5恢复与阶段收口](delivery/2026-11-05-f5-completion.md)的范围/验收已写，复用同一安装，新增真实服务停止/恢复下的索引与下载组合验证；不重跑模型或任务写。

F5.5恢复组合本地通过：基础全离线三包exit0；新会话与真实停止/恢复共39 API请求/5只读收集POST（4实际下载、1失败）、43原材料和取消结果保持。首轮结果读取过早exit1及后续r2成功分开保留。139原文件/329、348、112事件history/Git/claims保持，owned浏览器/HTTP和专用服务已正式退出、五端口关/临时根空/三库保留；F5.4精确CI41929749342双OS必要步骤成功。下一新的综合审查、文档交付和G0，不重放模型或任务写。

F5.5新的独立综合审查通过：[报告](delivery/2026-11-05-f5-completion-review.md)独立核实际恢复/退出/原材料与源码身份，另四次无SDK离线核包均通过，无findings。下一刷新包含报告的最终scope/静态清单，纯文档普通提交推送、同片远端终结后登记完整F5，再发布G0分片计划。

下一阶段[G0分片计划](plans/2026-11-05-new-user-acceptance.md)已写：G0.1新应用/原生依赖环境/数据和无模型旅程，G0.2两模板真实六阶段与取消/重开/重复，G0.3公开流程/平台边界与综合收口。当前[G0.1](delivery/2026-11-05-new-user-onboarding.md)仅设计，等待F5.5精确文档提交cd0b5a0普通推送后的原综合审查者终结；不将原run恢复作为G0。

完整F5完成：cd0b5a0纯文档普通推送、12文档370链接/30命令、352归档同原包和同片独立实时远端终结通过，无findings。G0计划已发布于工作树，当前开始G0.1；F5.5终结追加随本片归档，纯记账不递归审查。

G0.1新安装已通过：公开development Bash安装exit0（58.78秒）、独立基础接收者与原lock/hash的新原生venv（54.62秒）；352资源/283冻结/新runtime身份一致，无editable/旧venv软链、无control库/Temporal库创建/四服务端口关。原系统工具/cache/认证明确复用，未跑apt或声称空OS一键通过。下一公开CLI两新repo登记与无模型旅程。

G0.1无模型CLI旅程通过：两新Git根各一次register、一次角色选择保存到revision2，9项真实项目基线；两模板预览/创建/重复、旧revision拒绝、缺服务prepared保留及离线合同读取通过，四端口仍关/零模型。首轮辅助脚本错误期待prepared重复exit0而失败，真实exit1及r2恢复分开保留；共40次ergora CLI/9可信检查/4Git。当前新HTTP/浏览器只核本地旅程，G0.2才显式启动执行。

G0.1本地验收完成：新浏览器交互14 GET/零POST/零pageerror、桌面与390px及原prepared恢复窗口通过；两status400使用明确测试opaque值，无真实run观察或派发。owned浏览器close/HTTP有序SIGTERM（实际shell143）、五端口关/新control库保留；两新repo/任务意图与旧139文件/Git/claims保持，最终verifier exit0。HTTP provider手工选项与medium/600秒/并行2仅元数据、零模型，配置面已记账。下一新的独立审查、静态文档核对与纯文档提交推送；G0.2尚未开始。

G0.1新独立本地审查通过：原11文档与静态368链接/30命令、现存包/新依赖及二进制、新旧数据/真实命令/代表截图/正式退出均独立核实，需求和可维护性无findings。原系统包预检失败、辅助首轮exit1、HTTP143和opaque probe边界保留。下一刷新包含报告的scope/静态结果、纯文档普通提交推送与同片实时远端终结；尚未启动G0.2服务/模型。

G0.1完成：精确18ed62e/唯一父cd0b5a0/12纯文档、371链接/30命令、352资源与新安装一致及普通push exit0通过；同一审查者00:04:59 UTC另行核远端完整SHA并终结，无findings。下一G0.2具体记录已发布，沿同一新数据及两原prepared恢复；本片终结追加随G0.2归档，尚无新模型结果。

G0.2服务已就绪：重核G0.1原文件与四端口后，公开services start显式启动Temporal/worker/executor/a2a，实际exit0及原doctor ready_for_real_tasks=true，MLflow仍停；完整辅助20.56秒。尚无workflow或模型结果，下一按两原prepared SHA执行resume-start并固定实际run，不能以服务RUNNING宣称六阶段通过。

G0.2两原意图已恢复：两次公开resume-start均exit0/submitted，保留G0.1原creation/submission SHA；实际governance run 01a1a909-7372-7418-8529-e09c76d1c1d7、large run 01a1a909-7dec-74f5-92f9-7fdbca8bc0ff，已保存原回执。当前执行inventory/plan，尚未发批准或确认六阶段成功；下一原ID核计划/history/spec/memo并审阅。

G0.2待批计划核验通过：两run各连续112事件/零signal及真实Codex inventory+plan SUCCEEDED，spec/memo/request/receipt/产物身份一致；CLI与网页完整材料相同，浏览器16 GET/零POST/390px通过。已完整审阅6份计划/所有权/回退原文及范围/可信检查/覆盖缺口，审阅理由保存。下一正式重开HTTP并沿原ID批准精确SHA，尚未执行work或宣称候选通过。

G0.2 HTTP恢复通过：owned初轮正常SIGTERM/真实shell143/临时根空，显式同一来源新PID的bootstrap200；同一浏览器reload后19 GET/零POST，原run选择及完整计划回执保持，390px通过。下一按已完整审阅的两精确SHA批准；一项真实回包丢弃后的原decision只读恢复纳入本次验收，不模拟成功或重发。

G0.2批准/幂等通过：页面35请求/2真实POST，各原run仅一次owner-g0-one；一真实成功回包丢弃后reload按原decision读回requested，无重发。4条重复CLI start/approve exit0且原记录/18文件不变；原history前112事件保持、各恰event113精确approve_plan及唯一原run，owner/intent/attempt/result绑定通过。后续真实work/verify/review只读观察中，候选复验、取消和交接尚待。

G0.2两真实六阶段通过：原history324/337事件、7/6 job与5/4真实Codex模型job，COMPLETED/outcome REVIEW_READY；候选44d697f/68ff73c，治理5/大型8检查及同候选独立review pass，原材料和证据摘要完整核实。首轮辅助提前检查零租约exit1保留；按公开external-status/显式reconcile后，逐字未改脚本r2 exit0、2 claims/0 active，原结果不变。下一候选分支/独立worktree复验、额外取消与交接，未登记完整G0.2完成。

G0.2候选独立复验通过：两次公开export exit0/exported、各agent/原task分支精确指向44d697f/68ff73c，源HEAD仍基线、未checkout/merge；操作者新detached worktree的9条原可信检查全过且脚本SHA/候选干净保持。下一单独取消任务与真实进程/外部对账，随后本次新证据/预算/ZIP离线与下载，最后新独立审查。

G0.2取消通过：新cancel run 01a1a91a-ed65-7b18-abda-7f65e1da5bc2在实际selected进程存活时发一次稳定取消；监控器fence/nonzero终态、原进程组停/monitor退出，35原事件恰一request_cancel且零批准。COMPLETED/CANCEL_UNCONFIRMED保持，公开外部核对/显式reconcile后3 claims/0 active。辅助首轮末尾字段误用KeyError/exit1保留；r2按冻结spec核request SHA，只读回4条成功命令而不重复写，完整核验exit0。下一三本次原run的证据/预算/交接与退出，再新独立审查和精确交付。

G0.2新交接通过：CLI/网页三包一致，浏览器36请求/3真实下载POST/零pageerror、390px与按需窗口通过；45原材料引用/SHA一致。无SDK接收者三包exit0、六项错误SHA/CRC有效复制包篡改明确拒绝，原结果/未知量保持、未创建control库。下一正式退出owned服务、无服务核包和新旧数据终核，然后新独立审查与精确文档交付。

G0.2本地收口：三原history324/337/35保持、零running/3 claims/0 active；owned浏览器close、HTTP有序SIGTERM/实际shell143、专用Supervisor公开shutdown及5进程退出通过，五端口关/临时根空/三库保留。全离线三包再核exit0，新152文件/Git与旧139文件/Git/leases保持，原Supervisor ini不变。下一新的独立审查与精确文档交付，然后G0.3。

G0.2新独立本地审查通过：[报告](delivery/2026-11-05-new-user-journeys-review.md)独立核两真实六阶段/原信号/候选与检查、取消进程/原未知、45材料及三包/六项拒绝、152新/139旧数据和正式退出；另九次无SDK核验均符合预期。唯一P2用量表述已文档修正并同片复核关闭：原CLI自报usage不等于正式索引已归一化或完整计费。下一最终静态/scope、纯文档普通提交推送和同片精确终结，然后G0.3。

G0.2完成：82f69cd唯一父18ed62e/7文档/247链接/30命令/352资源、普通push及01:06:25 UTC同片独立实时远端终结通过，无未解决finding。G0.3开始：已修正README/两使用说明及当前流程图，说明正常REVIEW_READY不会自动释放租约，暂不导出可显式对账；原结果与质量/外部终止/清理分别保留。实际每项目1次register+1次可选bind、零手改Supervisor；安装文档仍7/3命令，未宣称下降百分比。下一静态/新综合审查与交付，不重启已关栈或重复模型。F8补记CLI自报usage的版本化归一化/覆盖边界，旧run不回填。

F6下一阶段[具体计划](plans/2026-11-05-low-code-editor.md)已发布：E1固定版本/许可，E2独立可复现原型，E3两模板同旅程，E4构建/交互成本，E5选型，E6新审查/精确交付；随后F6.2编辑状态/撤销重做/修订与错误定位，再F6.3容量。前置npm元数据及独立36包准备成功，尚无原型/浏览器/性能结论，默认前端未变；G0.3完成后才开始E2。

G0.3新综合审查通过：[报告](delivery/2026-11-05-new-user-acceptance-review.md)核公开正常关闭/计数、原两片证据与当前包/新旧数据/退出、F6前置及计划，无未解决finding。P2澄清主动验证和push自动CI，保留原workflow未变。下一最终静态/scope与纯文档普通提交推送/终结；随后V5独立评估文档push分流，PR/manual全量与必需检查语义保持，F6.1按具体计划继续。

完整G0完成：73cd3ce唯一父82f69cd/12文档/384链接/30+3parser/352资源、普通push及01:29:10 UTC新综合审查者实时远端终结通过，无未解决finding。V5开始：仅原push加入docs Markdown/根README/AGENTS过滤，PR/manual及原矩阵/回归/Windows安装不变；公开GitHub语法说明已读取，本地6路径例与其他配置逐项相同。下一新独立审查、真实CI与纯文档push窗口验收；不虚构没有自动调度。

V5本地新独立审查通过：[报告](delivery/2026-11-05-ci-document-scope-review.md)核完整YAML仅一行过滤、7文件身份、256链接/30parser和维护成本，无finding；REST只读实测403限流，不当成未触发。下一普通精确push并用公开HTML核实际矩阵，随后仅文档事件窗口。F6独立home原型三入口实际构建exit0，尚未浏览器验证，未进入本片Git scope。

V5普通提交51284fd已推送且01:42:45 UTC远端同SHA，352资源/7文档258链接/30parser通过；公开HTML实际run41950353820仍进行。下一仅文档记账提交作为过滤事件，保留明确观察窗口，必要步骤成功和同片终结后才标完成。F6原生及React Flow两模板旅程已实际通过，JSON Forms待同组验证；均只写独立试验草稿，没有任务执行。

V5精确CI41950353820已Success，Ubuntu126992566188/Windows126992566519全部必要步骤逐项success且日志绑定51284fd；docs-only df0a908普通push及01:55:21远端一致，01:57:07/01:59:09 UTC两次官方HTTP200列表均无该文档候选行，原run正常完成。只声明此窗口，PR/manual/远端规则未实测。下一原审查者同片终结，然后继续F6.1；JSON Forms默认Ajv因CSP失败已保留，官方NoValidation渲染+原服务端显式校验的两模板旅程通过，不变更CSP。

V5完成：原新审查者独立核512/df唯一父、8/2文件身份、352资源、实际push矩阵必要步骤及两次文档窗口；02:03:23 UTC另行实时远端df0a908一致，报告已追加终结，无finding。状态归档随F6，不递归审查。F6源码已在examples/editor-comparison，36包clean npm ci和默认npm build实际exit0/7秒及1.34秒；final HTTP从该源码重开，同一独立control，原首轮HTTP正式SIGTERM子进程-15/包装shell241已取回，未当成产品失败或伪记exit0。下一最终三方案旅程/成本、选型及新审查。

F6.1最终本地收口：交付源码clean npm ci/默认build、三方案六旅程87请求/66POST、额外实际图形/ID边界20请求/2POST全过且零pageerror；六份r2摘要一致、16表其余零运行，HTTP逐字同构建/CSP保持，owned浏览器/HTTP正式退出且DB保持。选型见ADR0003：保留Cytoscape/原生模块，React Flow入口实测更小但无迁移必需收益，JSON Forms默认CSP失败与NoValidation模式分开保留。下一静态/scope与新fresh-context审查/普通精确交付，再进入F6.2a；不把原型当生产编辑器。

F6.1初审修复核验通过：独立审查两P2分别为公开安装缺少Web extra、Cytoscape跨重建待连接状态残留，均已局部修正。新基础venv实际安装/导入/pip check与HTTP通过；真实红例保留，修后两入口18请求/2校验POST、零pageerror，13资产逐字同当前构建。旧库六r2及SHA保持、新库仅project/零草稿及Agent；owned新HTTP正式SIGTERM/实际shell143、浏览器exit0，PID消失/8981关闭。13文档347链接/30参数/例子Bash通过；下一刷新scope并同片复审，再普通精确交付及F6.2a。原107请求仍绑定修复前源码，默认生产保持。
