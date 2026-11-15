# Anthropic 代码审查流程与 Ergora 对照

核验日期：2026-11-15（Asia/Shanghai）。本次独立研究直接读取用户指定的一手文章及官方产品文档，并静态核对 Ergora 源码、模板、研究和既有交付记录。仓库读取基线为 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，分支 `refactor/architecture-foundations`；工作区另有在途 training c1b0 变更，本研究不审查、不修改或认证该产品片。

本次仅新增本报告，未运行模型、第三方审查服务、训练或测试，未读取凭据、发表评论、提交或推送。下文“已实现”来自现有源码与明确指出的历史验收记录，不表示本次重做运行验收；“仅文档”表示规范或提示要求；“计划”指已有计划或明确标出的研究建议；“未证实”表示本次范围没有足够证据，不能推导远端平台一定未配置该功能。

## 结论

**Ergora 此前研究过 Anthropic 的公共审查产品和官方插件，但未找到对这篇特定文章的直接引用。** 当前已有相似的基础：独立会话、多专长并行审查、精确候选与完整材料绑定、三路／四路 all-join，以及保留完整原意见和覆盖缺口的本地报告。这些事实不能反向证明它们来自该文章。[E01][E02][E03][E04][E05]

文章更完整的机制还包括：另一组 agent 逐条验证 finding、控制审查轮次和重复意见、用专家确认的历史事故持续评测 reviewer、按变更风险分配人类批准，以及 merge queue、渐进发布和快速回滚。**现有 all-join 是汇合独立意见，不等于逐 finding 验证或多数票过滤；模型 approve 也不等于人类或平台批准。**[A1][E03][E04]

最适合接续研究的是 **P1：逐 finding 复核与成对质量评测；P2：有界增量复审与风险提示**。这些是本报告建议，不是新获准的产品计划。全部原 finding、少数意见及其验证处置应保留；增量复审继续绑定完整原包、祖先 Skill 和精确 head；风险提示不覆盖现有人工 release。本轮不修改模板版本或代码。

## 一手来源与可核边界

|来源|本次取得的内容与边界|
|---|---|
|[用户指定文章][A1]|原地址直接返回 HTTP 200，HTML canonical 仍为该地址，无需重定向或镜像。页面实际标题为 **How the Claude Code team does code review**，署名 Addy Osmani、Morgan Westlee Lunt、Qing Wang，发布日期 **2026-10-15**。它描述 Claude Code 团队，不能无条件推广到 Anthropic 所有仓库。|
|[同站官方 Markdown][A1md]|从原 HTML 的 Copy markdown／alternate 链接取得，22,410B，SHA256 `a322aa7632a44e82af40bf467cd89912eb870ea646bb5df7b4d51c80d8dd8577`。含图表的文字描述，补足 HTML 正文提取未展示的收敛统计。摘要只固定本次取得的字节，不认证其内部生产数据。|
|[Code Review 官方文档][A2]|再次直接读取其官方 Markdown，10,665B，SHA256 `78ff48627f8e08e5551e254a963356b6988160a6b0edc873fc8772e3f301e06a`。用于区分公共托管产品与文章中的内部合并流程。|

取得原页时 Python `urllib` 返回过 403；`curl` 直接读取原站 HTML 及其官方 Markdown 成功。没有以转载、搜索摘要或代理替代原文。文中内部流程和数字是作者的一手自述，本次未取得其私有实现、原始评测集或生产日志。

## 原文明示的实际机制

下列各项均为文章明确陈述；可复用判断和适用性建议另列于后文。[A1]

|环节|原文明示的行为|需要保留的限定|
|---|---|---|
|目标与指标|优化每次变更消耗的人类时间，同时把 revert／incident rate 作为护栏；记录每 PR 人类批准数的中位数与 P95、人类评论数、等待人的时间。|目标包括审查时间与坏代码造成的返工时间，不能只缩短审批等待。|
|PR 前验证|给 agent 可运行的测试、build 或截图比对，要求展示实际输出；再由 fresh-context subagent 审 diff。部分成员另用找 bug、简化 diff、端到端行为检查等内部 Skill。|原文没有发布这些内部 Skill 的完整实现，也没有说每位成员每次都运行全部 Skill。|
|仓库与局部规范|短 `CLAUDE.md` 指向详细资料；code owner 写短 `REVIEW.md`，说明本域失败形态、跳过路径、限制琐碎意见、要求文件与行号、清楚报告无问题。团队另查 reviewer 是否遵守规范。|“写了规范”和“已经验证模型遵循规范”是两件事。|
|并行发现与独立验证|多个 agent 并行找 bug；另一组对每个候选 finding 投票，达到同意条件才发表。过滤仅风格、诊断或清理类意见；曾对过滤器做内部 A/B。|没有披露 agent 数量、所用模型、投票阈值、完整 prompt 或误报率。公开插件不能据此被认定为同一私有系统。|
|问题呈现与处置|按严重度发表行内意见，并区分 Important、Nit、Pre-existing；每条都须修复或写理由 resolve。安全审查单列；内部流程中 bug／安全 finding 未关闭时不能 merge，后续提交修复后可自动清理。|文章同时说过滤纯风格类意见，不能把其 Nit 标签简单等同“保留所有风格建议”。原文没有完整分类规范。|
|CI 与责任|lint、类型、跨平台测试和 build 阻断；PR 模板写测试方法与撤销方法，发起变更的人签字负责。|自动填写模板不转移责任，审查报告也不代替实际检查输出。|
|按风险批准|低／中／高风险对应 0／1／2 位人；一个分类器定风险，第二个判断是否额外需要人。敏感路径和 CI 文件有强制人类规则；仅 trusted authors 可走较轻路径，外部作者需要第二人。|变更决定风险档，不由作者身份决定档位；作者可信度另限制能否使用轻路径。agent 批准不能充当人类名额。|
|精确提交与人类责任|指挥 agent 的人可以计入要求的人类审查者，并负责结果；approval 只覆盖一个特定 commit，不能担保的新提交需要重新批准。|不是“只要是可信作者就可批准后任意改代码”。|
|集成与发布|merge queue 在应用到 main 的组合上重跑检查；通常先用 feature flag 给内部员工，再到 latest，stable 滞后；可关 flag／revert，值班与事故回顾查漏过哪一层。|这是降低无人批准风险的重要配套。文章承认尚无随事故／回退指标恶化自动收紧批准的 circuit breaker。|
|持续质量评测|收集导致事故的历史 PR、fix-forward、revert，由懂代码的工程师确认 bug 及位置；每天评测 reviewer，每次改 reviewer 对全套案例评分。按评论响应区分已修、误报、故意行为、不重要；另用干净 PR 检查可能诱导有害修改的误报。|作者优先级是检出真实 bug，其次减少轮次；“评论多”不自动等于质量更高。|
|收敛|记录 rounds-to-pass 与 recall；三轮后要求作者退一步重想方案；前几轮后只复审新增 diff；指出一类 bug 便于一起修；不重复已经发表的 finding。另在夜间查既有代码。|“三轮后反思”不等于公开了强制三次失败即关闭 PR 的硬状态机；diff-only 的确切切换轮次未给出。|
|人类仍做的事|判断是否该做、方向／范围、风险代码和示范性架构、阅读实际证据、承担后果。用当前源码的局部 explainer／可视化补充团队理解。|作者明确承认共享代码上下文尚无正式流程；没有证明生成讲解完全替代代码知识传播。|

### 数据说明了什么

文章报告 6–9 月 Claude Code 合并 PR 数翻倍以上、回退占比下降超过 40%；研究预览时有实质评论的 PR 比例从 16% 到 54%。图表文字报告收敛改进后：一轮通过 65%→78%，五轮及以上 8.9%→1.5%，平均轮次 2.08→1.32。[A1md]

这是同一团队的观察结果，原文没有给出可复算的样本数、绝对回退／事故率、完整分母、独立对照或成本，不能据此宣称多 agent 投票造成了全部改善，更不能直接承诺 Ergora 同样收益。文章所说约 59% 的反复发现来自“第一轮时已经存在的代码”，指后续轮次不断发现初次已存在的问题；它不等于“59% 都是 PR 基线里的旧 bug”。[A1]

### 内部流程与公共产品要分开

原文末尾明确区分：公共 Code Review 发表 findings，不批准；内部仓库更进一步，由 owner 决定哪些低风险变更只靠自动检查即可 merge。[A1]

官方公共产品文档同样写明：若干 agent 并行读取 diff 与周边代码，验证、去重、排序，再发表行内意见／summary／check；**不会批准或阻断 PR，不 build／run 被审代码**。它通过 GitHub App 运行在 Anthropic 基础设施，Team／Enterprise 适用。`/code-review`、Ultrareview、GitHub Actions／GitLab CI、自写 subagent／Skill 是不同接法。[A2] 因而“买到／调用公共 reviewer”不等于已安装文中风险批准、合并队列、安全闭环和事故评测整套系统。

## Ergora 当前状态与证据

### 是否已经引用、有哪些模板

对本报告写入前的 HEAD，以文章 slug、完整标题、`claude.dev/blog/solving` 及作者姓名检索 `docs`、`src`、`AGENTS.md`、`.github`，未找到直接命中；同时对工作树研究／模板文本做交叉搜索。已有 [PR／MR 工具调研][E01] 第 2 节详细核对了内建命令、官方 `code-review`／`pr-review-toolkit` 插件、Action、托管产品等，第 5 节提出了完整材料和领域审查，但没有这篇指定文章的引用。该结论限本次当前树，不声称审过全部 Git 历史、私有文件或对话。

现有代码审查组合包括：

- `ergora-delivery-review@1.0.0`：structure、correctness、test-value 三个独立分支，显式 `join: all`。[E02] 节点 38–91 行。
- `ergora-pretraining-review@1.0.0` 与 `ergora-posttraining-review@1.0.0`：通用三路之外再加一位领域专家，外层 all-join；领域 Agent 有独立完整 Skill。[E06][E07]
- `ergora review prepare / collect / prepare-input / report`：本地完整材料、外部 GitHub／GitLab 只读来源、所选单叶输入和多分支建议报告；实际调用仍用原 composition／agent run。[E03][E05][E08]

这里的“模板”是 Ergora 的可组合审查定义。当前 tracked 文件中没有 `.github/PULL_REQUEST_TEMPLATE*`、`.gitlab/merge_request_templates/*`、`CODEOWNERS` 或名为 `REVIEW.md` 的文件；`LOCAL_REVIEW.md`／`TRAINING_REVIEW.md` 是操作手册，不是同名 owner 规则文件。未查询远端 branch protection、已安装 App 或组织策略，因此不能断言平台端也没有这些配置。

### 逐项对照

|文章机制|Ergora 状态|证据与实际边界|
|---|---|---|
|先验证，再独立审查|**仅文档要求＋有历史执行记录**|`AGENTS.md` 11 行要求每个完整实现片交新上下文 reviewer；`PLAN.md` 的持续规则要求原始需求、固定 baseline、完整差异和实际验证。三路并行交付记录实际核过成功、反对、取消和原件；这是既有记录，本次未重跑。[E09][E10] 它不证明任意新 PR 都自动触发审查。|
|精确 commit／材料绑定|**已实现**|`review_packets.prepare()` 固定完整 base/head/diff-base、全文 Git blob、需求与 evidence，自动收所选路径祖先 `AGENTS.md`；`review_sources.collect()` 绑定平台来源；`review_requests.prepare()/verify()` 核来源与 manifest 摘要。[E08][E05][E03] 全文只是选中的变更／显式上下文，不是自动加载全仓或认证检查真实。|
|多 agent 同一候选并行|**已实现**|三路节点无互相依赖，all-join；正式 `ReviewDAGWorkflow.stage()` 261–298 行按依赖和并发 scope 调度，检查独立 session。[E02][E04] 本地 `prepare-input` 只准备一个叶，`report` 只读已选 runs，不自动执行整根。|
|逐 finding 的另一组验证／投票|**当前内置审查组合与报告未实现**|`ergora-delivery-review` 只有三位互补 reviewer 与 gather；`review_requests.report()` 94–152 行按每叶 decision 汇总，没有候选 finding→独立验证证据→处置步骤。[E02][E03] 通用 DAG 支持串行依赖，不表示已有逐 finding 验证器。|
|保留少数意见／完整覆盖|**已实现，且应保留**|`report()` 拒绝重复 run 代填不同成员；逐叶核 input/prompt/result 及来源，缺失／失败为 incomplete，全部完成后任一 request-changes 即总体 request-changes；原回复与错误保留。[E03] 这是证据完整性和不掩盖反对意见，不是多数票判真。|
|局部审查知识与约束|**已实现资源传递；遵循效果未证实**|完整祖先资料、AGENTS、工程／领域 Skill 进入输入；correctness Skill 6 行要求可达案例，structure Skill 6 行区分实证缺陷和猜测，领域 Skill 24–28 行要求反证、位置、影响和缺证据说明。[E08][E11][E12] 没有核到按文中方法独立评价每条 owner 规则遵循率。|
|降噪、严重度、Pre-existing 标签、行内发表|**部分仅提示；自动平台闭环为计划／未证实**|现有 Skill 要求区分缺陷、假设、覆盖缺口，`response` 保留正文；报告并未结构化每条 finding 的类别／生命周期。Q2.3 已实现完整本地报告；远端行级意见明确另片，不默认 approve／merge。[E03][E12][E13] 已有候选 PR/MR 关联也不等于发表或审结。|
|独立安全 reviewer＋未 resolve 阻断|**当前内置交付组合无此专门分支；远端能力未证实**|三路定义没有安全专用叶；本仓唯一 tracked workflow 是 Portability，没有调用 Claude 安全审查或处理 review thread 的步骤。[E02][E14] 不能用 correctness reviewer 的广泛职责宣称已有安全闭环。|
|CI、build、跨平台|**已实现 CI；平台 required 设置未证实**|Portability 在 pull_request 触发，构建 wheel、校验参考身份、运行 Linux 分组／Windows 回归及 Windows 安装升级。[E14] 7 行与 55–74 行。未核到 article 所述全部 lint／type 必需检查，也未读取平台 required-check 配置。|
|风险 0／1／2 人、trusted author、敏感路径、approval 失效|**文章式平台规则未证实**|当前组合的只读权限与候选摘要不是人类风险分类器；all-join instructions 2 行明确不授予 owner approval 或 merge。[E02] 本地报告返回 `formal_execution_authorized: false`。[E03] 不得以模型 approve 替代现有人工 release。|
|三轮后反思、diff-only、跨轮不重复|**未找到此审查生命周期实现**|当前本地报告按一个来源／manifest和精确 runs 读取，没有 review-round／finding-history 状态。[E03] 通用 DAG 是无环依赖，不自动承担跨 head 审查循环；训练优化轮次也是另一领域，不能拿它充数。|
|事故驱动每日评测／干净 PR 误报／真实人类耗时|**领域小例已验证；文章式效果系统未证实**|领域交付有两缺陷＋两有效变体的四次真实 CPU 叶调用，原记录明确 scalar 输出已随材料提供，不是盲测或总体检出率。[E07] 28–35 行。已有通用 Skill evaluation／adopt／rollback 合同可复用，但没有因此自动建成 incident corpus、每日 review eval 或人类时间仪表盘。[E15]|
|merge queue、flag、渐进发布、自动收紧与值班|**本文式整套能力未证实**|本地 workflow 无 `merge_group` 或 release rollout 步骤，未查询远端设置。[E14] Skill／记忆／安装回退是另外的已有能力，不能等同生产 PR 的开关、灰度、事故监控。文章自己也尚无指标触发的批准 circuit breaker。[A1]|

上表以具体 owner 为准：旧工具研究中“建议实施”的 Q1／Q2 不覆盖后续交付。当前 Q1.1／Q1.2、Q2.1／Q2.2 与 Q2.3 诸片已有代码和交付；其中完整报告的既有最终记录为 `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`、自己的八 job／30 步 CI 及独立终核完成。[E13][E16] 不能仍把“只能审一个叶、没有汇总报告”的旧时点当现状。

## 适合复用的思路与分片建议

以下是根据原文与现有实现作出的**工程推论／研究建议**，不是 Anthropic 已公开的实现规范，也不是 Ergora 当前能力承诺。

### P1：逐 finding 复核与成对质量评测

1. **先保存完整 finding，再记录复核处置。** 在原 source／manifest／run／report owner 上，为候选问题记录稳定身份、精确 head、文件／行、可达配置、后果、原审查者与证据；复核记录区分 confirmed、rejected、unresolved，并写理由和反证。保留原 finding、少数意见、原回复及所有复核意见，不建议用多数票自动抹去原问题。当前 all-join 的失败和缺覆盖语义保持。
2. **第二组先尝试推翻 finding。** 独立会话检查实际调用者、合法配置、前后版本和 bug 是否由候选引入；缺少源码／检查时保留 unresolved。需要执行复现的验证仍由原可信执行／检查合同持有，只读叶不能因收到代码或命令就取得 shell 权限。现有 source-bound 单叶输入不支持自动执行前驱，不能把增加一条 DAG 边冒充该闭环已完成。[E03][E04]
3. **先证明质量收益，再选投票或门禁。** 固定同一批已确认缺陷与干净／合法非默认样例、同一材料、模型／prompt／工具版本，成对比较“原三路／领域审查”与“附逐条复核”。记录检出、误报、诱导有害修复、未覆盖、失败、耗时与费用。以维护者确认或独立运行 oracle 标真值，模型一致不能自作 oracle。复用已有 evaluation 的固定 suite／baseline／candidate／holdout 与明确采用合同；现有四个 CPU 小例只能作为回归种子。[E07][E15]

### P2：有界增量复审与风险提示

1. **给复审定义收敛条件和停止义务。** 显式记录原审查、后继 head、已处置 finding、轮数和预算；达到阈值要求人重新判断方案，不默认再做“完整扫一次”。三轮可作初始实验参数，不能称为原文披露的唯一硬规则。
2. **diff-only 只选择本轮重点。** 原完整包、祖先 Skill、需求、失败检查、少数意见及原始 head 继续保留；新 head 必须形成新包和来源绑定。每轮明确本次新增／改变范围、旧问题处置、未复查范围。去重依赖具体 finding 身份和证据，不把同一 bug 类的不同可达实例误删，也不把新代码自动纳入旧批准。
3. **风险先作为可解释提示。** 根据改动内容、敏感路径、发布／恢复影响和缺证据给出建议审查力度；写清规则来源和理由。保留现有人工 release 与精确 evidence gate，不先实现“模型说低风险就无人批准”。若将来改变平台合并策略，须另核人类规则、作者信任、敏感路径、branch protection、commit 变化失效、queue、回滚和事故指标；公共托管 reviewer 本身不提供这些授权。[A1][A2]
4. **反复出现的问题回到原 owner。** 能用确定性 lint／类型／架构检查解决的模式，优先移入已有检查；局部知识改原组件协议或所属 Skill，不复制多个规则文件。先固定已发生的真实反例再评价规则修改，避免因模型偏好扩展到整仓清理。

## 局限与不应推导的结论

- 原文是一个团队的运行经验，没有公开完整内部 reviewer／投票器／风险分类器、阈值和评测集；无法仅凭文章复刻相同效果或审计其全部生产断言。
- 多会话、多 agent 或不同后端可以增加视角；它们共享模型知识、输入和盲点时仍可能同时出错。这是推论，文章没有提供相关错误率或训练领域保证。
- 文章的 verification 是跨多个层次的：本地可执行检查、源码 finding 验证、安全、CI、集成与发布不能混称同一次模型“验证”。公共 Code Review 不执行被审代码；训练数值、分布式次序、恢复、收敛与收益仍须真实领域证据。[A2][E12]
- 减少人类批准的前提包括可信作者、小变更、敏感路径规则、可回退性、内部使用与监控。Ergora 的建议报告和训练人工 release 不能因本研究越过原权限或批准合同。
- 本次只读了明确相关的当前树和公开一手网页，未审全部代码、私有原件、远端平台策略、全部历史分支或实际新调用。没有证据的能力均保留为未证实。

## 本地证据索引

行号为本次核验位置，后续文件增长时应以具名函数／章节交叉定位。

|索引|位置与用途|
|---|---|
|E01|[2026-11-15-pr-mr-review-tools.md](2026-11-15-pr-mr-review-tools.md)：第 2 节（36 行起）区分 Anthropic 公共产品／插件；第 5 节（82 行起）为当时采用建议；基线与只读边界见 3 行。|
|E02|[delivery-review workflow](../../src/ergora/data/presets/workflows/ergora-delivery-review/workflow.json)：38–91 行三个 reviewer 和 all-join；[instructions](../../src/ergora/data/presets/workflows/ergora-delivery-review/instructions.md)：2 行独立完成／保留原意见／不授予批准。|
|E03|[review_requests.py](../../src/ergora/review_requests.py)：`_task` 25–34、`_reviewer` 37–50、`prepare/verify` 53–91、`report` 94–152、`markdown` 160–179。|
|E04|[reference_workflows.py](../../src/ergora/reference_workflows.py)：`CompositionWorkflow.stage` 85–113、`ReviewDAGWorkflow.stage` 261–303；[review_dags.py](../../src/ergora/review_dags.py)：114–139 行全部成员和显式 all-join。|
|E05|[review_sources.py](../../src/ergora/review_sources.py)：`collect` 47–75、`read` 78–97；[LOCAL_REVIEW.md](../LOCAL_REVIEW.md)：来源观察、调用、报告与覆盖限制。|
|E06|[pretraining root](../../src/ergora/data/presets/workflows/ergora-pretraining-review/workflow.json)：38–75 行 general／domain 与 gather；[posttraining root instructions](../../src/ergora/data/presets/workflows/ergora-posttraining-review/instructions.md)：1 行完整来源、独立分支与 source-only 边界。|
|E07|[training-domain-reviews 交付](../delivery/2026-11-15-training-domain-reviews.md)：9–12 行实施范围与最终状态，18–35 行四次 CPU 合同及小例局限，51–53 行本片 CI 终态。|
|E08|[review_packets.py](../../src/ergora/review_packets.py)：`_instructions` 34–38、`prepare` 134 行起；[LOCAL_REVIEW.md](../LOCAL_REVIEW.md)：准备材料、离线自洽与显式上下文／evidence 限制。|
|E09|[AGENTS.md](../../AGENTS.md)：恢复与独立审查合同；[PLAN.md](../PLAN.md) 的“持续执行与验收规则”：需求／维护性两轴、完整原件与授权边界。|
|E10|[parallel-reviews 交付](../delivery/2026-11-09-parallel-reviews.md)：7–11 行职责，45–55 行实际并行／反对／取消／回放及模型边界，61–65 行精确交付。|
|E11|[correctness Skill](../../src/ergora/data/presets/agents/ergora-correctness-reviewer/skills/ergora-correctness-reviewer/SKILL.md)、[structure Skill](../../src/ergora/data/presets/agents/ergora-structure-reviewer/skills/ergora-structure-reviewer/SKILL.md)、[test-value Skill](../../src/ergora/data/presets/agents/ergora-test-value-reviewer/skills/ergora-test-value-reviewer/SKILL.md)：各第 6 行；[agent_backends.py](../../src/ergora/agent_backends.py)：`ClaudeCodeBackend.command` 256–273 行真实工具限制。|
|E12|[pretraining Skill](../../src/ergora/data/presets/agents/ergora-pretraining-reviewer/skills/ergora-pretraining-review/SKILL.md)：8 行材料和授权，14–22 行数值／分布式／恢复，24–28 行 finding 与证据。|
|E13|[领域审查与质量总计划](../plans/2026-11-15-domain-review-optimization-quality.md)：32–33 行少数意见与产品区分，51–55 行 Q1／Q2 当前交付，远端行级发表另片；不是全部节点仍停在起始计划。|
|E14|[portability.yml](../../.github/workflows/portability.yml)：3–8 行触发，17–81 行实际 CI；当前 tracked `.github`／`.gitlab`／CODEOWNERS／PR 模板文件清单的只读检索。|
|E15|[INTEGRATIONS.md](../INTEGRATIONS.md)：70–109 行 Skill 候选／评价／采用／回退及可信 evaluator 边界。|
|E16|[complete-review-reports 交付](../delivery/2026-11-15-complete-review-reports.md)：62–66 行独立终核，68–72 行精确发布及自己的 CI 终态。|

[A1]: https://claude.dev/blog/solving-code-review-at-anthropic/
[A1md]: https://claude.dev/blog/solving-code-review-at-anthropic.md
[A2]: https://code.claude.com/docs/en/code-review.md
[E01]: 2026-11-15-pr-mr-review-tools.md
[E02]: ../../src/ergora/data/presets/workflows/ergora-delivery-review/workflow.json
[E03]: ../../src/ergora/review_requests.py
[E04]: ../../src/ergora/reference_workflows.py
[E05]: ../../src/ergora/review_sources.py
[E06]: ../../src/ergora/data/presets/workflows/ergora-pretraining-review/workflow.json
[E07]: ../delivery/2026-11-15-training-domain-reviews.md
[E08]: ../../src/ergora/review_packets.py
[E09]: ../../AGENTS.md
[E10]: ../delivery/2026-11-09-parallel-reviews.md
[E11]: ../../src/ergora/data/presets/agents/ergora-correctness-reviewer/skills/ergora-correctness-reviewer/SKILL.md
[E12]: ../../src/ergora/data/presets/agents/ergora-pretraining-reviewer/skills/ergora-pretraining-review/SKILL.md
[E13]: ../plans/2026-11-15-domain-review-optimization-quality.md
[E14]: ../../.github/workflows/portability.yml
[E15]: ../INTEGRATIONS.md
[E16]: ../delivery/2026-11-15-complete-review-reports.md
