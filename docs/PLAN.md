# Ergora 实施计划与进度

最后更新：2026-11-16。恢复／换机先读本页、根 AGENTS、活动片交付，再核 HEAD、diff 和实际运行；旧摘要不能覆盖原件。此前本日检查点已[逐字归档](PLAN-history-2026-11-16.md)；[11月15日](PLAN-history-2026-11-15.md)及更早历史保留各自原结果。历史“当前／在途”只指记录当时。

用户要求交新agent接续：先读完整[English handoff](HANDOFF.md)／[中文交接](HANDOFF.zh-CN.md)，其中包含准确候选、关键计划／任务／调研／原始证据路径、未完成验收与下一条操作。交接后已接续S1／容量片和双语研究；这些原片审查已完成，当前另有S2静态设计fresh审查。自有模型／测试／训练／服务命令已结束，未操作其他owner进程。仅更换负责agent，不撤销后续实施授权或将未完成项标为完成。

## 当前检查点

主开发分支 `refactor/architecture-foundations`，最新已核联合产品 `6cec589f404b17f4828a70807d5e33d89fad3fa0`（S1与V2b均普通合入），后继文档HEAD `fc632ad`。联合新安装32过／135.20秒，待本候选普通推送及自己的CI；最后核远端仍为旧 `04af2344239306cb00458e89f81258093235f049`，其已接纳产品为 `c540939d3b3f38f3851b0de965c9cd0f969eea77`。文档提交不改变产品身份，实际HEAD仍须每次核Git。恢复前检查点已逐字归档；下列状态据实际Git、原报告和在跑进程核正。默认分支仍为用户已设置的 `main`；普通发布开发分支，不自动合 main／强推。根在途为计划／交付，其余产品在各自隔离树；勿覆盖其他agent报告。

- **前置 M5/native、a1 与 M6-V1 已有各自源码／安装／独审结果。** 最后公开 `eba8680` 的联合包、82＋8及独审保持原身份；其自己的官方 CI `43807888266` attempt1 已终态 failure：7/8 jobs成功（含Windows），唯一失败为旧cold fixture默认operation-v1，却期待schema3 effect关闭提示。原生产身份拒绝没有失效；不能用此前 `0a5a0ff` 的8/8成功替代。[原联合交付](delivery/2026-11-16-design-training-expression-integration.md)。
- **CI最小修正已审、合入并随联合候选发布。** 产品 `e3a4369` → `a975098`；只改原测试，保留cold v1身份拒绝，另以明确v2来源触达真正关闭动作，真实S/H stopped与无副作用均核。原1失败、修后相关6过；fresh两轴approve／0。公开04af234自己的8/8 CI已核，下述联合记录保留准确身份。[交付](delivery/2026-11-16-schema3-cold-fixture.md)／[独审](delivery/2026-11-16-schema3-cold-fixture-review.md)。
- **WA5-S1最新r4源码／安装／独审／原模板闭合并普通合入。** 原80cb39c的13安装和r2的119安装均保留各自身份；fresh reviewer真实安装发现native配置缺失旁路FAILED回执，request-changes。最小修正沿原已发布project/binding固定身份作preclaim policy读取，完整mutable项目检查保留原constructor／回执owner；作者17受影响节点过。准确新产品 `b28cd316b63bb788c502a026f1ec971d5572242a`、core／SDK669完整包／283参考／依赖通过；同一原-I反例在此新安装2.455秒通过，真实FAILED／poll／实际executor SHA同一。原17节点新安装已17过／92.33秒，607自有进程终核absent；Codex原模板78.706秒approve；新fresh完整两轴approve／0并关闭原F1/P2，普通合入6cec589。联合新安装32过，发布／自己的CI待核，不转授旧绿。[交付](delivery/2026-11-16-design-policy-registration.md)／[兼容源码审](delivery/2026-11-16-design-policy-registration-v1-compatibility-review.md)。
- **M6-V2a最终r3源码／新安装／独审／原模板已闭合并普通合入。** 固定产品 `82c6595` → 合入 `c540939`；四SDK poller仍仅两实际业务许可，原等待预算和normal先drain/stop后关；F1/F2在新的fresh源码审两轴approve／0。新安装runtime **65过**、实际S/H **6过**、core无SDK **6 skip**。原模板Claude **420.591秒超时**保留，用户已授权的Codex回退 **31.254秒／approve**，不称异后端通过。SDK强行run取消明确incomplete/unknown，不伪造cleanup，不承诺外部loop.stop可恢复。联合候选安装／发布、完整M1c、真实旧queue SDK10秒正向start及CPU两轮仍未验，所有schema3实际效果继续关闭。[交付](delivery/2026-11-16-training-cycle-v2-runtime.md)／[r3独审](delivery/2026-11-16-training-cycle-v2a-r3-source-review.md)。
- **逐Agent思考强度源码／独审／原模板已闭合并普通合入。** 固定产品 `0dcbc20` → 合入 `a2655c3`：Codex `reasoning_effort`、Claude `effort`，原组件表单自动展示，原绑定／定义／历史reader／任务冻结消费。源码45过／8原Forge/mini外部依赖skip，13个parallel节点均已过；后继8项是重复并行验证，不计新覆盖，错误归类已据独审更正。实际页面Codex reviewer high、Claude reviewer medium、implementer low保存／重开及API读回通过，未安装系统依赖；正式组合selector和真实模型等级另验。fresh两轴approve／0；原模板Claude420.553秒超时保留，用户已授权Codex回退68.049秒approve，不称异后端成功。联合新安装／发布另验，训练／设计storage不继承本片通过。[计划](plans/2026-11-16-agent-reasoning-and-parallelism.md)／[交付](delivery/2026-11-16-agent-reasoning-options.md)／[独审](delivery/2026-11-16-agent-reasoning-options-review.md)。
- **上述三项联合新安装／普通发布／自己的CI已闭合。** 准确产品 `c540939`，新wheel `630fae78…`，core／SDK各668完整包、执行位和source同一，site-packages真实导入／283参考／依赖通过；合并候选的必要定向 **33过／34.808秒**，实际两CLI、正式冻结、异后端并行、SDK生命周期与实际S/H许可及cold拒绝均到达。捕获80个自有进程结束后均absent。公开 `04af234` 远端完整OID已核；额度恢复后官方API核自己的run **43819270365／attempt1／8 jobs全success**，含Windows。原403保留为观察限制，不计测试失败。S1及V2b新候选不在该包，不能继承其CI。[集成交付](delivery/2026-11-16-reasoning-cycle-runtime-integration.md)。
- **M6-V2b源码fresh两轴approve／0，新安装和原模板完成，已普通合入。** 完整容量产品 `919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`，新wheel `8fe43f44…`、core／SDK668完整包／执行位／283参考与依赖过；新安装41定向过／52.85秒，133捕获自有进程均absent。源码N32两场各保留66分支，19424B接纳、37515B整体拒绝、Failure1205B，独审已只读核原件；不转授安装。首次N32安装runner未启动原记录保留；绝对argv新label串行两场新安装2过／66.88秒，均66分支，19425B接纳／37525B拒绝／Failure1223B，461自有进程终核absent；Codex原模板65.349秒approve。普通合入3292379已完成；联合安装32过；发布／自己的CI及真实服务／完整M1c／CPU仍未验，schema3效果保持关闭。[交付](delivery/2026-11-16-training-cycle-v2-capacity.md)／[源码独审](delivery/2026-11-16-training-cycle-v2-capacity-source-review.md)。

本日更早完整检查点和身份已逐字存历史，各交付保留原始失败、修正及未验界限；只重跑变化真正影响的接缝，不再重复无变化大套件。

## 已确认的产品决定

[用户 D1–D4 原答复](delivery/2026-11-16-workflow-design-decisions.md)已齐，不重复问：

1. 新profile对框架开发、结构重构、重要算法／数据／权限／验收变化强制调研与设计；小修复按项目规则。
2. 项目／模板给最低必答项，单任务owner可追加；免答／降低要求／接受假设由有权人明确记录，Agent不能自行跳过。
3. 设计材料修订产生新revision，重要变化重新批准；保留原答复／决定，沉默不是批准。
4. 先设计／必要知识关卡，再可信脚本／测试节点；并行完成现有训练循环；最后一般Repeat与混合画布。沿原编译／Temporal，不另建调度器。

这些方向决定不替代精确候选的运行批准或真实人类身份。当前无受保护owner通道的部署只能展示 `human_channel_unavailable` 和完整材料，不能靠UID／TTY／JSON／配置布尔宣称可信人类已决定。原安全取消能力仍保留。

## 接续顺序与验收节点

|优先／节点|下一步与完成标准|权威记录|
|---|---|---|
|P0 CI／集成发布|S1与V2b准确候选独审／安装／原模板均闭合，普通联合产品6cec589新包669完整文件和283参考通过，联合32过／135.20秒，709采样自有进程终核absent。接续普通推送并核本候选自己的CI，不继承旧04af234的8/8。|[最新联合交付](delivery/2026-11-16-design-capacity-integration.md)|
|P1 逐Agent思考强度|显式配置源码／fresh独审／原模板／联合新安装／普通发布及自己的CI已闭合。最新A6a–d明确四模式；完整双语后端参数研究、静态检查与新fresh语义独审均完成，两轴approve／0；唯一P2补明Claude text-only safe-mode／ultracode限制并同片复核关闭，再写配置／冻结设计并fresh设计审后分片实施。当前只有显式值，preset／planner／automatic未实现；不把请求值当native实际强度，不暗中降档／换模型／加预算。|[本片计划](plans/2026-11-16-agent-reasoning-and-parallelism.md)／[后端研究](research/2026-11-16-backend-runtime-options.md)|
|P1 WA5-S1|最新b28cd31新包同一、原-I反例及原17节点新安装全部通过（92.33秒；607自有进程终核absent）；Codex原模板与新fresh两轴approve／0，原F1/P2关闭，普通合入6cec589，联合新安装32过，发布／自己的CI待核。此前80cb13过／r2的119过不转授；所有v2拒执行及原v1冻结对照必须保持。|[交付](delivery/2026-11-16-design-policy-registration.md)／[已审拆片](plans/2026-11-16-design-gates-registration-and-journal.md)|
|P1 WA5-S2／F-J-G|完整source journal实施proposal已冻结，新的fresh设计审进行中；先保存两轮全文与同ID恢复。后继marker／旧creation跨登记迁移另给完整合同；最终冻结policy/owner、权威source／seal／withdraw尾部、G1/G2与最后spawn。F/J/G完整且通道可用前，不开放可执行v12。|[S2 proposal](plans/2026-11-16-design-source-journal-s2.md)／[详细设计](plans/2026-11-16-design-knowledge-gates.md)／[拆片](plans/2026-11-16-design-gates-registration-and-journal.md)|
|P1 M6-V2／V3|V2a已合入；V2b源码独审闭合，准确新安装41过，N32新安装两场与Codex原模板均通过，普通合入3292379完成，联合安装32过，接续普通发布／自己的CI。再做10MB实际reader、原最后gate统一候选、真实服务／CPU两个候选顺序archive、丢回复／重启／停止／预算／收尾。真实服务旧queue正向另验；未验不开放／不认证GPU质量。|[M6设计](plans/2026-11-16-training-cycle-v2-runtime.md)／[V2b交付](delivery/2026-11-16-training-cycle-v2-capacity.md)／[CPU素材清点](delivery/2026-11-16-training-cycle-v2-cpu-prerequisites.md)|
|P1 R1–R3／WA5c|逐finding反证与独立oracle成对eval；可信非Agent脚本／测试／人工节点，失败／unknown／错candidate阻断，原执行与恢复owner复用。|[review演进](plans/2026-11-15-review-validation-evolution.md)／[工作流演进](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|P1 Q5.2／Q6|按实际caller细化可维护性重构；最终严格全面审查、组件协议／可复现脚本／手册／示例与发布。kernel专家保留在v3优化路径。|[领域／优化／质量计划](plans/2026-11-15-domain-review-optimization-quality.md)|
|P2 WA5d／e|本域闭环后细化一般有界Repeat、混合图、统一CLI／页面／交接；定义／编译／runtime均有实际消费者才声明可执行。|[工作流演进](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|并行 文档／分支整理|首批12文件与3本地分支安全清理已fresh两轴approve；唯一P3的Linux20／Windows30分钟已双语修正并同片复核关闭，明确13文件提交eb14df1，待普通推送。远端未删。其余完整手册／架构／历史导航batches2–7保留，不能把索引当全部指南完成；完整双语后端选项研究已修正并语义独审两轴approve／0，四模式配置／冻结设计仍待做。历史报告可增自包含HTML并保留原证据；活动工作树／独有提交保护。|[分批计划](plans/2026-11-16-bilingual-documentation-and-branch-cleanup.md)／[交付](delivery/2026-11-16-bilingual-documentation-and-branch-cleanup.md)|

## 已有能力与外部条件

|主题|当前入口与范围|
|---|---|
|安装／工具／Windows／RSI／主线|[总计划](plans/2026-11-01-all-in-one.md)、[架构](architecture/current.md)、[使用手册](USAGE.md)；Apache-2.0、main默认分支已落实。|
|定义／资源／后端／组合与画布|[AC计划](plans/2026-11-08-agent-composition.md)、[Agent定义](AGENT_DEFINITIONS.md)、[工作流组合](WORKFLOW_DEFINITIONS.md)；所有祖先Skill／上下文累积，权限逐级收窄，版本冻结／正式选择。|
|开发／重构／优化模板|[专家计划](plans/2026-11-12-specialist-template-refresh.md)、[重构交付](delivery/2026-11-13-refactoring-preset.md)、[采用矩阵](research/2026-11-12-specialist-adoption.md)、[优化方向](plans/2026-11-13-specialist-presets.md)；六阶段、横纵专家、kernel v3保持。|
|PR／MR审查／工单|[审查手册](TRAINING_REVIEW.md)、[Anthropic比较](research/2026-11-15-anthropic-code-review-comparison.md)；多路审查／领域专家／只读来源／本地报告已有，逐finding验证／增量循环待后继。|
|记忆／Skill／评价／交接|[改进计划](plans/2026-11-14-evaluated-improvement.md)、[集成交接](plans/2026-11-14-integrated-handoff.md)；候选→可信评价→明确采用／回退→新任务冻结，旧结果保留。|
|真实训练优化B3|[B3a](plans/2026-11-14-proposal-experiment-handoff.md)和[源码试用](delivery/2026-11-14-workload-source-trial.md)不代替训练；真实workload／完整资产、设备、正式baseline/candidate、独立质量oracle与准确evidence批准仍分别验。|
|原生Forge与其他后端|[Forge准入](delivery/2026-11-14-forge-native-admission.md)、[Harness准入](plans/2026-11-12-harness-admission.md)；完整会话／teacher-student-judge／跨恢复预算与真实停止等缺项不绕过。OpenHands、Windows原生、跨服务MCP/A2A与远端隔离按各自真实支持范围。|

## 持续执行与恢复规则

- 用户已授权持续按计划推进，每步更新本页及所属交付。长期文件在项目docs／home持久目录，不依赖系统tmp或`~/project/tmp`。
- 新完整实现片用新的fresh-context独立reviewer，给原始要求、准确baseline、tracked＋untracked完整差异及实际证据；需求与维护性两轴。实证finding修后同片复核；状态记账不递归审查。
- 大项使用Ergora自身审查模板，保存完整输入／实际后端／原回复。优先异后端；Claude不可用时用户已授权Codex／ChatGPT回退，不声称异后端成功。简单任务可用较低思考强度，复杂权限／恢复／并发任务用较高强度。
- 凭据只引用环境（ChatGPT为`LINGZHI_API_KEY`），不写公开配置／报告／提示。保留283参考、原锁、既有六阶段、candidate绑定、attempt-before-send、unknown只对账、预算与唯一reaper。
- 新模块／guard／测试跟随真实owner/caller/失败；可配置值按有效关系验证，不锁默认、不堆重复测试／CI。源码、安装、服务替身、真实服务、业务质量、发布各自认证，不重复无变化大套件。
- 当前容器／当前用户仅用于可信项目；无宿主权限，不提权或绕审批，不称OS隔离。模板资源累积不扩大工具授权，子权限不越父级；已开始任务保持冻结版本。
- 迁移只在授权隔离fixture，不能顺手升级用户运行home或停其他owner训练；原DB/control-home备份不冒称外部config/state整体回退。未验／unknown如实保留。
- 每片普通提交／合入开发分支／推送并核精确远端和自己的适用CI；不强推、不自动合main。恢复时先核在跑命令，勿重复启动旧批或用其他候选的绿替代。
