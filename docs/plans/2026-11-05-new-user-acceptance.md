# G0：新用户安装与P0完整旅程

日期：2026-11-05。来源：[总计划G0](2026-11-01-all-in-one.md#g0-新用户闭环验收)。前置完整F1–F5及各片独立终结。该文档只记录实际执行状态，设计不等于验收通过。

## 环境、范围与保护

使用F5.4已接受的生产源码`4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`；F5.5仅文档，不继承旧数据旅程为新用户验收。新控制面通过公开Bash安装器选择development组合、使用从未存在的持久安装/bin路径。另建基础无SDK接收者。记录非editable来源及352包资源/冻结283身份，不把安装器从源码构建的包宣称为此前wheel的同一归档字节。

使用全新的控制库、参考配置/state、原生依赖venv、Temporal持久库和两个业务Git根，不导入任何先前DB、任务、worktree、租约或结果。参考源码仅来自校验过的随包v2.2资产；新Python3.12 venv按原requirements.lock及hash同步，可复用缓存/固定二进制。环境已有Python/Git/Node/uv/Codex及用户认证明确列为复用前置。旧完整Linux系统包预检实际失败时保留日志，不尝试无权限的apt/sudo；低层用户目录配置成功不冒称完整一键安装器成功或空OS安装通过。

所有运行目录使用home下持久位置，位于业务repo之外；私有验收脚本/原日志在忽略的`.ergora/checks/g0-onboarding/`和后续分片目录，浏览器产物在`output/playwright/g0-*`。原先所有项目/state/ref不变。初始化、项目注册、任务与服务通过公开CLI或页面，不能直接写数据库、伪造回执或修改生成的Supervisor配置。

## 分片与可验收节点

|节点|行为和已有入口|验收与收口|状态|
|---|---|---|---|
|G0.1 全新安装/登记/无模型旅程|公开Bash development安装、独立基础接收者、原生init/模型元数据/可信容器显式enable；两新Git根各一次project register，模板copy、有效配置、doctor与services status|352资源/283冻结及实际非editable；新库/配置归属，未启动服务/模型；preview→审阅→create及同意图重复、旧revision拒绝；服务缺失start失败后按原intent查询/恢复，不重复发任务；本地合同/创建可离线读；新HTTP/页面/390px正常。新审查者/文档普通提交推送/实时远端终结|完成：本地验收、纯文档18ed62e/371链接/30命令/352资源、普通push及[同片独立终结](../delivery/2026-11-05-new-user-onboarding-review.md#精确提交与同片最终终结)通过|
|G0.2 全新业务正常与异常|显式管理新Temporal/worker/executor/a2a；两个开发模板使用真实Codex完成六阶段，由主入口读计划/批准、查候选/审查、导出/核证据/下载；HTTP重启及重复操作；一额外取消任务|固定原task/creation/submission/workflow/run/decision/candidate身份，重复不增加workflow/信号；两REVIEW_READY与精确可信检查/独立审查相符；候选独立worktree复验，取消未知保持并显式对账；错误复制ZIP/SHA拒绝、原材料不变。真实provider费用未知明确保留；新独立审查及精确交付|[本地验收通过](../delivery/2026-11-05-new-user-journeys.md)：两真实六阶段/候选复验、取消/对账、三包下载/离线/六错误拒绝、正式退出与新旧数据保持；[新独立审查](../delivery/2026-11-05-new-user-journeys-review.md)通过，P2用量文案已关闭；纯文档82f69cd普通推送及[同片独立终结](../delivery/2026-11-05-new-user-journeys-review.md#精确提交与同片最终终结)完成|
|G0.3 综合门禁/公开流程|公开手册按实际摩擦修正，比较A2步骤/注册/人工配置面；新基础接收者离线核交接，所有owned服务正式退出且持久库保留；重核旧状态|分别记录Linux新应用/新数据、复用OS工具、Windows精确CI支持子集，未做本机Windows/空OS/远程tracker/GPU不推断通过；完整G0新的综合审查、普通提交推送/远端终结；然后F6.1|[已实施公开流程修正](../delivery/2026-11-05-new-user-acceptance.md)，计数/静态及[新综合审查](../delivery/2026-11-05-new-user-acceptance-review.md)通过，P2关闭；纯文档73cd3ce普通推送及[同片独立终结](../delivery/2026-11-05-new-user-acceptance-review.md)完成，完整G0通过|

跨分片使用同一新持久数据旅程；后一片只增加新阶段证据，前片记录不覆盖。修复产品缺陷时先写独立最小子片，必要合同回归/新包/相应精确CI及审查；本片未主动重复运行无变更的重型Python/多OS矩阵；普通push仍可能由现有workflow自动调度，其触发/结果单独记账，不作为新的生产或G0运行证据。

## 具体成功与失败路径

1. 安装/复制模板/注册不启动模型或任何执行服务。`doctor`的安装、凭据、TCP和任务状态分别记录；凭据存在不等于模型可用。每项目一次完整定义登记，选角色增加修订可见；不先agentflow register再ergora add。
2. 可信检查使用业务项目自己的实际行为、AST依赖、知识链接，large-change另验集成/兼容/回滚。检查与原基线由操作者持有，位于候选允许路径之外；候选不能自报PASS或修改评分器。任务使用真实有界目标，沿两个公开模板输入编译，不重建六阶段引擎。
3. 无服务时保留原创建与提交意图，失败不是“未发生”。显式恢复同一意图；Temporal上线后核原run，unknown不得盲目重发。两模板实际模型预算以选择的模型和阶段墙钟/并行数量说明，未知token/金额不写0。
4. 先保存原运行身份，再关闭重开HTTP，重新选择原项目/任务/记录。计划材料完整读取后批准精确SHA；重复原decision查询或恢复不生成第二有效批准。所有新增动作的请求数/写目的与原生history分开保存。
5. 取消路径使用稳定request ID，先核原run终态和外部证据，再明确reconcile；requested或CANCEL_UNCONFIRMED均不冒称进程已停/任务成功。新HTTP恢复用原ID，不换task绕过。
6. 接收者仅核包内字节和声明关系；篡改仅改复制包，错误预期SHA/材料必须失败。原包、原139等历史材料与旧Git refs保持；实际新任务另计，不挪用旧run验收新项目。
7. 退出前核本栈无运行workflow/active lease；正式关闭owned浏览器、HTTP和Supervisor，记录实际退出码/端口及保留DB。不能为了形成“成功”日志强杀不归本片的服务。

## 易用性与平台口径

与A2的安装7条/自有venv3条是文档步骤对比，不是空OS耗时实验。新增统计包括：每个业务项目的正式注册次数、必须人工维护的配置文件种类、手改Supervisor次数、从主入口定位批准与证据的路径，以及失败后的恢复操作。按实际计数，不声称总体降低百分比。

Windows保留F5.4精确CI41929749342的Python3.12原生回归与PowerShell5.1安装/升级身份；G0没有本机Windows时仅引用原覆盖，不登记新Windows浏览器或WSL2旅程通过。完整执行仍限Linux/WSL2可信项目。远程工单、多harness、训练入口和Skill/记忆冻结继续归F7–F10，本片不偷偷扩展授权或引擎。

安装前调查：原参考doctor将本地提交与A2A监听绑定；G0按真实依赖补全公开启动示例，不能跳过准入或假称低耦合。后续F7需在版本化适配边界评估按入口能力准入，保持旧reference行为和明确不可用语义。
