# Ergora 实施计划与进度

最后更新：2026-11-14。恢复时先读本页、活动片计划／交付、`AGENTS.md` 和 Git 状态。此前 52,782B 的计划已[逐字归档](PLAN-history-2026-11-14.md)，更早记录见[11月10日归档](PLAN-history-2026-11-10.md)与[更早历史](PLAN-history-2026-11-09.md)。历史文档中的“当前／在途／待完成”仅指当时，不覆盖本页。

## 当前检查点

开发分支 `refactor/architecture-foundations`，已推送文档检查点 `67966095814eec01f2e1e5d65d87e289320ad79f`，产品基线仍为 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`。普通推送当前分支，不合入 `main`。H3b r3 实现、安装／实际调用、自身模板与新独立两轴本地出口通过；普通发布与本候选自己的 CI 待验，不把工作树改动算作已发布能力。

|节点|实际状态|接续动作与权威记录|
|---|---|---|
|S1 工程 Skill|两标准 Skill、`refactoring-quality`／`optimization-performance-diagnosis` 已发布；561 产品／两 RECORD／283 冻结、33 安装测试、四实际只读叶、自身原结构模板及新 fresh-context 两轴通过；原23条目保持，共25 preset|自己的 CI `43485238011`：第五官方run HTML Success，八job／30必要步骤及十八原HTTP获原独立终核通过，精确交付完成。[计划](plans/2026-11-14-engineering-skills.md)／[交付](delivery/2026-11-14-engineering-skills.md)／[评审](delivery/2026-11-14-engineering-skills-review.md)|
|W1 真实参考源码试用|固定十三源码／93,748B；Ergora design 142.704秒、profile 138.210秒、measurement 91.065秒均成功。原源码、两完整前驱JSON、十五inline／六参考12,954B的实际交付已核|精确文档发布 `6796609` 及原独立发布终核通过、开放0／0；measurement保留补证据的`request-changes`。无产品变化，不新增CI成功主张。[计划](plans/2026-11-14-workload-source-trial.md)／[交付](delivery/2026-11-14-workload-source-trial.md)／[评审](delivery/2026-11-14-workload-source-trial-review.md)|
|F8-H3a 归档读取|`560bfdf`精确交付完成；r3包551／两RECORD／283、安装60项、两原生历史逐字分页及网页生命周期通过；自身approve、新独立两轴及自己的CI `43481386288`八job／30必要步骤终核通过|原三P2及首修失败保留并已修正；只提供归档观察。[计划](plans/2026-11-14-harness-session-readback.md)／[交付](delivery/2026-11-14-harness-session-readback.md)／[接缝](architecture/2026-11-14-harness-session-seam.md)|
|F8-H2 真实后端|`322007f`精确交付完成：显式Responses、真实只读调用／完整资源链、自身及新独立两轴、自己的CI `43475349587`通过；原completions HTTP400保留|不等于续接、OpenHands受限准入或workspace支持。[计划](plans/2026-11-14-harness-real-model.md)／[交付](delivery/2026-11-14-harness-real-model.md)|
|C2.1 Forge身份准入|`a0a42ba`精确交付完成；原kernel owner包／scripts Git身份门禁、安装23通过／9跳过、自身回退、新独立两轴及自己的CI通过|完整C2开放，不关闭原`failIfUnavailable`绕过隔离限制。[计划](plans/2026-11-14-forge-native-admission.md)／[交付](delivery/2026-11-14-forge-native-admission.md)|

W1仅验源码提案与交接：共享仓库HEAD／213条status字节保持，不扩大为全部WIP逐字认证。未执行训练、parser、profiler或GPU，未申请资源、读取模型／数据或采用候选；本开发会话不直接修改业务代码，不以源码建议关闭B3。三调用采用授权Codex回退，不冒称异后端成功。

## 下一可执行项

1. **F8-H3b实际续接**：沿[计划](plans/2026-11-14-harness-session-continuation.md)／[交付](delivery/2026-11-14-harness-session-continuation.md)完成普通发布与自己的CI。迁移注入点已修；r1成绩保持原候选范围。独立审查的home副本／生命周期时窗、失败增量两P2已修并按原场景复核、开放0。r3包561／两RECORD／283、源35项通过；实际SDK成功／断连／发送后超时／取消四场景通过，真实模型source＋followup完整继承／前轮记忆成功。安装七suite133通过／12跳过；自身结构模板73.433秒approve；最终新独立两轴本地出口通过，开放0／0。冻结原项目／资料／权限／后端／schema，原home／cwd／session不分叉；unknown不自动重发，正式恢复归原owner。
2. **F9实验导航**：将既有workload、baseline、experiment、可信runner、compare／gate、MLflow及Forge交接接到同一入口；复用原训练owner和账本。CPU合同与真实GPU分别验收，见[总计划F9](plans/2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)。
3. **F10受评价改进**：沿记忆／Skill／评价／采用owner，补正式任务可选冻结、来源／失效／容量可见及复盘候选／明确采用回退。复用AC3资料合同，不让生成器改可信评价或扩大权限，见[总计划F10](plans/2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)。
4. **G1集成交接**：开发／治理／训练公开旅程，核新安装、配置、角色替换、工单、演进、旧项目升级／回退、跨机重建；更新[架构](architecture/current.md)、README、[使用手册](USAGE.md)、[训练手册](TRAINING.md)与Windows手册，再完成相关完整回归、独立审查与推送。U3日常安装只覆盖其精确旧包，不代表S1等新包已升级。

完整C2、真实B3和P2／P3不因局部成功而完成。外部权限／环境缺项保留，继续可独立工作，不反复请求相同授权。

## 开放验收与支持范围

|范围|剩余条件|
|---|---|
|真实B3训练优化|资产、环境／设备、预算、正式baseline／candidate、独立正确性／质量oracle及原evidence SHA批准尚未完整绑定；[B3a](plans/2026-11-14-proposal-experiment-handoff.md)只完成手册字段与原产物走查|
|完整C2原生Forge|父完整材料、普通teacher／student／judge及内部全部会话权限、跨恢复预算和真实停止待验；原隔离要求保持。[D2-C2设计](plans/2026-11-13-specialist-presets.md#c2第一个执行适配片的准入设计)|
|F7后续|只读来源、来源任务、显式评论、GitHub原生ID单标签、远端候选核对、已有PR／MR关联及页面已接；GitLab严格标签追加仍unsupported，稳定Trigger需真实consumer|
|可选Harness|DeepSeek SDK/runtime `0.2.2rc2`已有Linux／WSL2只读适配与归档读取；OpenHands `1.62.0`因ambient／工具／MCP生命周期缺口暂缓受限准入；Windows原生逐项验收|
|P2／P3|MCP／A2A跨服务、远端执行／真实隔离、参数搜索、外部格式、团队／规模化设计按真实需求立片，不预建第二调度／进度权威|

## 已完成工作与恢复入口

以下链接指向各自原验收范围；失败、未验维度及精确身份保持。更多逐片发布／CI记录在上述完整归档和各交付文档。

|主题|权威记录|
|---|---|
|原安装、RSI、Windows、主线／重构、F1–F5／G0|[总计划](plans/2026-11-01-all-in-one.md)、[当前架构](architecture/current.md)、历史归档；Apache-2.0已落实，main已建立且维护者已设置默认分支|
|Agent定义／后端、祖先资源、串并行组合、画布／正式选择|[AC总计划](plans/2026-11-08-agent-composition.md)、[图形规格](plans/2026-11-09-composition-console.md)、[架构交付](delivery/2026-11-11-architecture-platform.md)|
|六阶段材料／预算／消费者及实际旅程|[专家总计划](plans/2026-11-12-specialist-template-refresh.md)、[六阶段旅程](delivery/2026-11-13-six-stage-native-journey.md)；串行／并行以原实际范围为准|
|重构模板／实际旅程|[A1配方](delivery/2026-11-13-refactoring-preset.md)、[A2第三轮](delivery/2026-11-13-refactoring-journey.md)，前两失败保留；S1新根复用原全部子角色／权限／预算|
|跨域专家／十八优化方向|[采用矩阵](research/2026-11-12-specialist-adoption.md)、[D2方向计划](plans/2026-11-13-specialist-presets.md)、[共享v2专家](delivery/2026-11-13-optimization-experts-v2.md)，B2a–B2i各交付；最新kernel `41dd5aa`自己的CI及独立终核通过|
|Linux CI／Windows|[分组计划](plans/2026-11-13-linux-ci-shards.md)／[交付](delivery/2026-11-13-linux-ci-shards.md)，保留原取消与诊断失败；分段覆盖不同于单次全套|
|同事试用／日常安装|[试用入口](delivery/2026-11-13-colleague-onboarding.md)、[U3安装](delivery/2026-11-14-daily-installation-refresh.md)，README的25 preset来自S1，新包升级另验|
|F7来源／任务／候选／写回页面|[来源](delivery/2026-11-12-issue-console.md)、[来源任务](delivery/2026-11-12-source-task-console.md)、[候选观察](delivery/2026-11-12-candidate-observation-console.md)、[PR／MR](delivery/2026-11-12-review-context-console.md)、[评论／标签](delivery/2026-11-12-issue-writeback-console.md)，各精确提交／自己的CI及独立终核已完成|
|F8可选后端|[准入总计划](plans/2026-11-12-harness-admission.md)、[H1探针／实现](delivery/2026-11-12-harness-probes.md)、H2／H3a当前记录；研究不等于兼容结论|
|工程经验／标准Skill|[本地盘点](research/2026-11-14-local-engineering-skills.md)、S1当前记录；原创可移植包与用户本地修改分别处理|

## 持续执行与验收规则

- 用户已授权沿计划持续推进，每步更新本页和所属交付；恢复后核Git／活动片。长期文件在项目docs或home持久目录，不依赖临时目录。
- 完整实现片用新的fresh-context reviewer，提供原始要求、固定baseline、tracked／untracked差异及实际证据；需求／维护性两轴，修实证finding后复核。状态记账不递归审查。
- 大项使用Ergora自身审查模板，保存实际输入／后端／原回复；优先异后端。Claude不可用时用户已授权Codex／ChatGPT回退，保留失败理由，不冒称异后端成功。
- 凭据仅引用外部环境变量，ChatGPT变量名`LINGZHI_API_KEY`；公开仓库不含密钥、私有源码、内部服务或本地验收缓存。
- 保持六阶段、原candidate／approval／attempt-before-send／unknown对账、版本冻结和283参考文件；复用Temporal、process monitor及证据owner，不增第二调度器／实验账本。
- 子模板读取全部祖先Skill／上下文；资源累加不扩大工具授权，子权限不越父模板。追加权限父子共同修订，已开始运行保持旧版本；容量不足明确拒绝，不截断后宣称完整。
- 按风险验证公开行为，必要检查通过后不无理由重复扩大；测试保护真实静默错误，不为文案／默认参数／普通可见失败堆断言。结构改动先查真实调用者与原库／owner。
- 已接受容器／当前用户作为可信项目边界，无宿主权限；不提权、不绕审批，不把只读模型工具限制称OS沙箱。未验平台及外部能力如实保留。
- 每片普通提交／推送当前分支、核精确远端及自己的必要CI，不借其他候选成功，不强推／自动合main；最终交接自包含，说明安装、交互、使用和关键限制。
