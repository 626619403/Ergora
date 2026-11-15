# Ergora 实施计划与进度

最后更新：2026-11-16。恢复时先读本页、活动片计划／交付、`AGENTS.md`，再核 Git 状态与实际运行。此前完整检查点与逐片记录已[逐字归档](PLAN-history-2026-11-15.md)；[11月14日](PLAN-history-2026-11-14.md)、[11月10日](PLAN-history-2026-11-10.md)和[更早历史](PLAN-history-2026-11-09.md)保留原结果与身份。历史“当前／在途”只指当时，不覆盖本页。

## 当前检查点

**c1b1本地门禁已闭合，正在固定提交。** 主分支 `refactor/architecture-foundations`，实施基线 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`。原预算根跨短S-H及正常loop退出／重启、唯一offer、existing-only、原一次窗口和只对账恢复已接通。原reviewer与自身模板发现的真实取消／receipt／最终deadline缺口已修；最终独立需求／维护性均approve，开放0／0。新非editable core／SDK各652文件同一，283参考／25来源／依赖保持；安装r2 **76 passed／985.95秒**，同产品精准r3 **7 passed／153.70秒**，两轮各178输入冻结。SDK-free真实H观察、自身原模板真实Codex及已知原件收尾均通过。历史r1的62／8和r11输入身份限制保持；实际预算根父SIGKILL未实测。固定提交／发布／准确CI仍另验，不认证总Workflow、自动多轮或训练质量。[计划](plans/2026-11-15-training-cycle-owner-lifecycle.md)／[交付](delivery/2026-11-15-training-cycle-owner-lifecycle.md)／[最终独立审查](delivery/2026-11-15-training-cycle-owner-lifecycle-review.md)。

**前片CI修复已独立通过并推送，候选自己的CI尚未观察到。** 原 `1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b` 的官方run `43713822317`／push／attempt1保留七job成功、group5失败：测试在beta通知后过早读取writer marker。仅修原fixture到真实阻塞位置后通知及原子发布marker，旧受控反例失败／同fault修后通过，独立两轴approve／0。候选 `7025e15f40e1934097a5c1c962bb7bf5e82a979d` 已普通推送 `fix/cycle-stop-overlap-ci` 和符合原push规则的 `refactor/cycle-stop-overlap-ci`，两个精确远端ref同一；未改CI。最新一次官方精确SHA查询403／配额0，不证明无run或成功。主线尚未导入此fixture修复，保留c1b1的新分支再整合。[调查](delivery/2026-11-15-cycle-stop-ci-failure-investigation.md)／[前片交付](delivery/2026-11-15-training-cycle-stop-operations.md)。

**BR1／BR2隔离组合已独立通过，待主线整合。** `.ergora/worktrees/review-reporting-integration` 已合并后端差异Skill、新预训练／后训练根和只读 `evidence-report`，catalog33，保留旧216资源及旧身份；663文件非editable包同一。安装49通过／1缺fixture，补原数据后精准1通过，分别保留。报告真实Codex原输出及headless Chromium桌面已看，390px窄屏70px溢出未通过。组合新独立两轴approve／0，README入口补充也通过；尚未提交、推送或联合c1b1安装，不能把隔离验收移给主线。[计划](plans/2026-11-15-backend-review-and-reporting.md)／[交付](delivery/2026-11-15-backend-review-and-reporting.md)。

**c1b2a具体服务设计已获接口审计，待修订／独立终核。** [草案](plans/2026-11-15-training-cycle-service-boundary.md)与[接口审计](delivery/2026-11-15-training-cycle-service-design-audit.md)明确：补receipt前核真实SDK run；首版仅ordinal0新start；完整stop分支只引用存在原件、unknown内联；独立normal／stop queue各一槽，关闭先normal后stop且等待原资源。精确Supervisor期限／强杀unknown语义及typed封套还需固定，不能先实施；正式Workflow／sandbox和接受后继留c1c／c1d。

**WA1–WA3 三份审计已收，WA4 详细方案仍为草案。** 用户新增的历史研究复用、任意循环、硬脚本／人工 Hook、调研设计前人类反复讨论与缺失公司知识提问均已[完整登记](plans/2026-11-15-workflow-evidence-and-human-gates.md)。[研究复用](delivery/2026-11-15-workflow-research-reuse-audit.md)、[实际 runtime](delivery/2026-11-15-workflow-runtime-capabilities-audit.md)、[设计／知识关卡](delivery/2026-11-15-workflow-design-knowledge-audit.md)审计明确现状：自有定义／StageDAG＋Temporal；受限嵌套串并行和既有批准／检查存在，通用 Repeat、任意非 Agent Hook和 typed 问题／答复／设计修订硬关卡尚未实现。已[汇总详细方案、客观验收和 D1–D4 产品取舍](plans/2026-11-15-workflow-design-and-execution-evolution.md)；先完成手头授权工作，再与用户讨论，不把设计写成已实施。

## 接续顺序与可验收节点

|优先／节点|下一步与完成标准|权威记录|
|---|---|---|
|P0 c1b1|本地安装r2／精准r3、SDK-free、自身模板和独立终核已通过；固定提交。源、安装、模型、独立、发布各自记账|[生命周期计划](plans/2026-11-15-training-cycle-owner-lifecycle.md)／[交付](delivery/2026-11-15-training-cycle-owner-lifecycle.md)|
|P0 前片 CI 修正|7025已独立通过／双ref推送；自己的CI待实际观察。将最小fixture修正整入后继，旧失败保留|[前片交付](delivery/2026-11-15-training-cycle-stop-operations.md)|
|P0 BR1／BR2|隔离安装／原件／README和独立两轴通过；保留主线产品及新PLAN整合，联合安装与适用接缝另验，再发布|[BR计划](plans/2026-11-15-backend-review-and-reporting.md)|
|P1 c1b2|实证独立 cycle service、normal-stop 配额、原 compute／control 窗口及 SDK标准sandbox；复用原 process／budget，不造新host或账本|[c1总计划](plans/2026-11-15-training-cycle-workflow.md)|
|P1 c1c|接确定性总 Workflow的真实消费者，串接原候选／停止／恢复与取消；unknown不重发，旧人工运行保持|[c1总计划](plans/2026-11-15-training-cycle-workflow.md)|
|P1 c1d|候选2之前必须有真实 phase、accepted archive、durable stopped、原多轮索引与质量门槛；CPU两轮不能代替真实训练|[c1总计划](plans/2026-11-15-training-cycle-workflow.md)|
|P1 WA4→WA5a／b|与用户讨论详细设计和 D1–D4，保存答复／决定；具体设计／必答资料／修订硬关卡分片，先客观反例再实施|[设计演进方案](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|P1 R1–R3／WA5c|逐 finding独立验证、成对eval和可信非Agent检查。不能以Claude产品能力或提示词冒充当前runtime|[审查演进计划](plans/2026-11-15-review-validation-evolution.md)／[设计演进方案](plans/2026-11-15-workflow-design-and-execution-evolution.md)|
|P1 Q5.2／Q6|按实际调用证据细化可维护性重构；最终严格全面审查、手册／示例／脚本／组件协议与发布。kernel专家保留在v3路径|[领域／优化／质量计划](plans/2026-11-15-domain-review-optimization-quality.md)|
|P2 WA5d／e|本域闭环后再设计一般有界Repeat和混合图，随后CLI／页面／交接；沿原编译与Temporal|[设计演进方案](plans/2026-11-15-workflow-design-and-execution-evolution.md)|

## 已完成能力与开放外部条件

|主题|当前边界与入口|
|---|---|
|安装／工具层／Windows／RSI／主线|[总计划](plans/2026-11-01-all-in-one.md)、[架构](architecture/current.md)、[使用手册](USAGE.md)；Apache-2.0已落实，main已建立且用户已设默认分支|
|定义／资源／后端／组合与画布|[AC总计划](plans/2026-11-08-agent-composition.md)、[定义手册](AGENT_DEFINITIONS.md)、[组合手册](WORKFLOW_DEFINITIONS.md)；全部祖先Skill／上下文累积、权限逐级收窄、版本冻结、正式选择|
|开发／重构／优化模板|[专家总计划](plans/2026-11-12-specialist-template-refresh.md)、[重构模板](delivery/2026-11-13-refactoring-preset.md)、[采用矩阵](research/2026-11-12-specialist-adoption.md)、[优化方向](plans/2026-11-13-specialist-presets.md)；六阶段、专业子模板／横纵专家、kernel v3保持|
|PR／MR审查与工单|[领域审查计划](plans/2026-11-15-domain-review-optimization-quality.md)、[审查手册](TRAINING_REVIEW.md)、[Anthropic比较](research/2026-11-15-anthropic-code-review-comparison.md)；三路all-join／领域专家／只读来源／本地报告已接，逐finding复核与增量循环后继|
|记忆／Skill／评价／复盘与交接|[改进计划](plans/2026-11-14-evaluated-improvement.md)、[集成交接](plans/2026-11-14-integrated-handoff.md)；原候选→可信评价→明确采用／回退→新任务冻结，CLI／页面已验，旧结果保持|
|真实训练优化B3|仍需完整资产、环境／设备、预算、正式baseline／candidate、独立质量oracle与准确evidence批准；[B3a](plans/2026-11-14-proposal-experiment-handoff.md)及[源码试用](delivery/2026-11-14-workload-source-trial.md)不替代真实训练|
|完整原生Forge C2|仍需父完整材料、teacher／student／judge、内部会话权限、跨恢复预算与真实停止；原隔离要求保持，不能关闭failIfUnavailable绕过。见[原生准入](delivery/2026-11-14-forge-native-admission.md)|
|可选后端与服务|DeepSeek Linux／WSL2只读及归档／真实续接按[准入计划](plans/2026-11-12-harness-admission.md)；OpenHands受限准入、Windows原生、MCP／A2A跨服务／远端隔离等按各自真实缺项验收|

## 持续执行与验收规则

- 用户已授权沿计划持续推进，每步更新本页和所属交付；恢复后核Git／活动片。长期文件在项目docs或home持久目录，不依赖临时目录。
- 完整实现片用新的fresh-context reviewer，提供原始要求、固定baseline、tracked／untracked差异及实际证据；需求／维护性两轴，修实证finding后复核。状态记账不递归审查。
- 用户允许按任务复杂度调整子agent思考强度：小而明确的实现用较低强度；架构、并发、生命周期／恢复及权限边界用较高强度。任务范围和客观验收先明确，重要变更仍由新的独立reviewer审查，不以降低强度省略门禁。
- 大项使用Ergora自身审查模板，保存实际输入／后端／原回复；优先异后端。Claude不可用时用户已授权Codex／ChatGPT回退，保留失败理由，不冒称异后端成功。
- 凭据仅引用外部环境变量，ChatGPT变量名`LINGZHI_API_KEY`；公开仓库不含密钥、私有源码、内部服务或本地验收缓存。
- 保持六阶段、原candidate／approval／attempt-before-send／unknown对账、版本冻结和283参考文件；复用Temporal、process monitor及证据owner，不增第二调度器／实验账本。
- 子模板读取全部祖先Skill／上下文；资源累加不扩大工具授权，子权限不越父模板。追加权限父子共同修订，已开始运行保持旧版本；容量不足明确拒绝，不截断后宣称完整。
- 按风险验证公开行为，必要检查通过后不无理由重复扩大；测试保护真实静默错误，不为文案／默认参数／普通可见失败堆断言。结构改动先查真实调用者与原库／owner。
- 已接受容器／当前用户作为可信项目边界，无宿主权限；不提权、不绕审批，不把只读模型工具限制称OS沙箱。未验平台及外部能力如实保留。
- 每片普通提交／推送当前分支、核精确远端及自己的必要CI，不借其他候选成功，不强推／自动合main；最终交接自包含，说明安装、交互、使用和关键限制。

## 压缩／换机恢复清单

1. 先核本页、Git HEAD／分支／diff与在跑进程，不重复启动现有回归或训练。旧摘要不能覆盖原JUnit／receipt与准确候选。
2. c1b1先读交付末尾及独立报告，核当前r2输入、包、回归、SDK-free、自身模板与清理终态；私有缓存位于项目ignored持久目录，公开文档不带本机路径或密钥。
3. 前片CI准确失败须保留，不把限额／403／未知改成success；独立候选修复与自己的CI分别记录。
4. BR隔离组合及README独立通过但仍未提交；整入时只接纳其准确diff，不覆盖主线五产品和新PLAN。联合候选安装／接缝另验，不重用隔离663包验收。
5. WA1–WA3已完成；先读三审计与WA4草案，讨论D1–D4后再做新产品关卡。先前用户授权的c1与BR收尾继续，不因新设计等待而重复询权。
6. 每个节点完成更新本页及所属交付。当前事实与历史分开，具体数值／原件留所属交付，本页只保留可恢复的活动状态。
