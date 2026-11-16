# Ergora 实施计划与进度

最后更新：2026-11-16。恢复／换机先读本页、根 AGENTS、活动片交付，再核 HEAD、diff 和实际运行；旧摘要不能覆盖原件。此前本日检查点已[逐字归档](PLAN-history-2026-11-16.md)；[11月15日](PLAN-history-2026-11-15.md)及更早历史保留各自原结果。历史“当前／在途”只指记录当时。

## 当前检查点

主开发分支 `refactor/architecture-foundations`，本次已审源码候选 `f9b9d72d6d5f2102809a3cafaadb2226bba0966b`；后继状态记录提交不改变该源码身份，恢复时另核实际 HEAD。root 在途变更目前只有计划／交付，勿覆盖其他 agent 的报告。默认分支仍为用户已设置的 `main`；普通推送开发分支，不自动合 main／强推。

- **M5／native 已交付且自己的 CI 闭合。** 固定产品 `5bcecf3`、`bc58be6` 普通导入 `1308e32`；公开 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a` 的官方 push／attempt1 [43801502094](https://github.com/626619403/Ergora/actions/runs/43801502094)于04:29:27Z确认 completed／success，8/8 jobs成功，原时限不变。原403和中间在途快照保留。[联合终核](delivery/2026-11-16-predecessor-native-final-acceptance.md)。只认证该候选，不认证后继模板或训练质量。
- **WA5a-1 inspection-only 已合入。** 产品 `cb861ea7138627d6646e8de1c0867a3ed92ce474` 普通导入 `3d632a7`；src／tests完整子树同一。完整六文件patch `4daea8ea…`、2064源输入、668完整包同一；源码受影响56过／1可选Web skip，新安装57全过，原模板Codex31.855秒approve；fresh两轴approve／0，原native缺依赖、重复source、报告媒体和第二公共读取入口四问题已关闭。发布／自己的CI另验。它只读设计材料，不赋予批准／执行能力。[交付](delivery/2026-11-16-design-packet-inspection.md)／[终审](delivery/2026-11-16-design-packet-inspection-source-review.md)。
- **M6-V1 最终路径修正版已独立终核并合入。** 隔离 `.ergora/worktrees/training-cycle-v2-expression`，基线 `bc58be6`，产品固定 `2acdcc44eb86659f3ab9d22d2f83bb0973388406`，普通导入当前 `f9b9d72`。五文件patch `b871eb2b…`、2019完整输入manifest `610ab4bb…`；新wheel `8574ebe6…`、core／SDK各665完整字节／执行位同一。源码V2/V3定向25过、安装同组25过、Windows纯路径语义probe、三份原V1 history安装重放及core无SDK过；原模板Codex76.908秒approve。前候选80＋8只保留原身份，当前106个worker函数AST仅新V2 consume路径改变；最终独立需求／维护性两轴approve／0；联合新安装／必要接缝与自己的发布CI接续。生产默认仍V1、所有schema3执行效果继续关闭，四poller／完整M1c／真实CPU两轮尚未完成。[交付](delivery/2026-11-16-training-cycle-v2-expression.md)／[源审](delivery/2026-11-16-training-cycle-v2-expression-source-review.md)。
- **WA5-S1 已开始隔离实施。** `.ergora/worktrees/design-policy-registration`、`feat/design-policy-registration`，准确基线 `3d632a7`，作者已固定formal policy要求的具体shape／SHA／实际owner并开始源码；v2发布中断、State6旧writer fencing、出生／legacy准入与backup范围正在原fixture验证，尚未freeze／安装／独审。前置a1已闭合；[拆片r2](plans/2026-11-16-design-gates-registration-and-journal.md)已审原字节 SHA `a94b4a5a…`、仅16个源码链接格式化后当前字节 `bde47bee…`，原件和映射另存，[新fresh设计审](delivery/2026-11-16-design-gates-registration-and-journal-design-review.md)两轴approve／0，原三finding关闭。范围：真正首次registration2、State6 writer fences、原status／恢复、tasks两出生入口和受管executor pre-claim拒旧输入；所有已有v1含空项目不升级。不开input12／definition8／新执行，原standalone stack切换与外部config/state整体回退不冒称受控。作者唯一交付为`docs/delivery/2026-11-16-design-policy-registration.md`，根统一更新本页。
- **a1／M6-V1 联合安装及独审已闭合，发布接续。** 新安装82＋8通过，collector2386节点、原参数ID映射后净增51／删除0，core无SDK／Windows纯路径probe通过；新fresh跨片审查两轴approve／0、报告SHA `afb0556c…`，无需源码修正。准确联合包 `ea1927be…`，完整边界见[集成交付](delivery/2026-11-16-design-training-expression-integration.md)和[终审](delivery/2026-11-16-design-training-expression-integration-review.md)。后继实现隔离，尚未借此开放执行或认证真实训练；普通推送后只观察该公开候选自己的CI。

本日旧c1b/c1c、BR、M1/M2、父留存、CI修正的完整固定输入和结果见历史及各交付，已审已合工作不重复跑。M6与S1各自隔离，不互相转授源码／安装／模型／CI通过。

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
|P0 当前片发布|a1与M6-V1已审合入f9b9d72，联合新包／82＋8／collector及跨片fresh两轴approve／0已闭合；普通推送并核精确远端，观察该公开候选自己的CI。源／安装／模型／独审／CI分别记账。|[联合交付](delivery/2026-11-16-design-training-expression-integration.md)／[集成终审](delivery/2026-11-16-design-training-expression-integration-review.md)|
|P1 WA5-S1|registration2/State6存储读回与恢复，首次登记边界及v1拒升级零原件增量；原预算前出生拒绝与真实executor pre-claim旧spec/job拒绝，旧v1对照；新安装、原模板、fresh实现审各自闭合。|[已审拆片](plans/2026-11-16-design-gates-registration-and-journal.md)|
|P1 WA5-S2／F-J-G|原journal保存两轮全文与同ID恢复；后继marker／旧creation跨登记迁移另给完整合同；最终冻结policy/owner、权威source／seal／withdraw尾部、G1/G2与最后spawn。F/J/G完整且通道可用前，不开放可执行v12。|[详细设计](plans/2026-11-16-design-knowledge-gates.md)／[拆片](plans/2026-11-16-design-gates-registration-and-journal.md)|
|P1 M6-V2／V3|已在`.ergora/worktrees/training-cycle-v2-runtime`／基线f9b9d72开始V2a closed拓扑子片，先四poller／两业务许可与等待预算／完整cleanup，全部效果保持关闭；后继完整候选再做原服务四poller／两业务配额、完整M1c容量与10MB实际reader、原最后gate统一候选；新非editable安装与真实CPU两个候选顺序archive、丢回复／重启／停止／预算／收尾。未验不开放／不认证GPU质量。|[M6设计](plans/2026-11-16-training-cycle-v2-runtime.md)／[CPU素材清点](delivery/2026-11-16-training-cycle-v2-cpu-prerequisites.md)|
|P1 R1–R3／WA5c|逐finding反证与独立oracle成对eval；可信非Agent脚本／测试／人工节点，失败／unknown／错candidate阻断，原执行与恢复owner复用。|[review演进](plans/2026-11-15-review-validation-evolution.md)／[工作流演进](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|P1 Q5.2／Q6|按实际caller细化可维护性重构；最终严格全面审查、组件协议／可复现脚本／手册／示例与发布。kernel专家保留在v3优化路径。|[领域／优化／质量计划](plans/2026-11-15-domain-review-optimization-quality.md)|
|P2 WA5d／e|本域闭环后细化一般有界Repeat、混合图、统一CLI／页面／交接；定义／编译／runtime均有实际消费者才声明可执行。|[工作流演进](plans/2026-11-15-workflow-design-and-execution-evolution.md)|

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
