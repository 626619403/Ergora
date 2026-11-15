# WA1：工作流调研采用与验证审计

日期：2026-11-15。固定源码基线：`a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`，独立 detached worktree `workflow-research-reuse-audit`，开始时工作区干净。本报告对应[WA1原始要求](../plans/2026-11-15-workflow-evidence-and-human-gates.md)，只读审计预训练／后训练审查、六阶段开发、重构、训练优化和复盘；不修改实现、测试、CI、计划或已发布资源。主工作区尚未完成的c1b1接线、其他worktree和未合入BR1／BR2均不计入本基线能力。

**结论：已有研究确实进入了版本化资源及正式消费者；主要缺口是效果评价和若干尚未闭合的执行合同。** 工程方法已进入重构根的完整Skill树，领域方法已进入两类训练reviewer，六阶段和串行重构有真实运行记录，GEPA也有真正的SDK消费者。与此同时，四个领域小例不证明总体检出率，五叶优化提案不执行自动循环，复盘导出不等于评价或采用。下一步应优先补逐finding独立反证与成对质量评价、原训练owner上的客观停止闭环，以及可核的问题／知识／设计决定，不能靠增加提示词或agent数量宣布完成。

## 1. 证据范围与判定方式

|证据层次|本报告如何使用|不能据此推导什么|
|---|---|---|
|说明性Skill|读完整操作文字、references和精确来源，确认方法被写入|宿主已经调度其中的循环、脚本或人类动作；模型已经理解或遵从|
|定义与生产消费者|读精确定义、祖先资源继承，以及CLI／正式owner的实际调用|静态DAG等于任意运行器；单叶prepare已经执行前驱|
|历史运行|引用交付中固定产品／候选、原run、检查及独立终核，保留失败和未验范围|本轮重新执行过；结果适用于其他SHA、平台或业务|
|效果评价|要求同任务、可比预算、独立oracle、正负例及原输出|安装通过、模型approve、合成scorer或读过附件等于质量／性能改善|
|计划／建议|明确标成未实现或本报告推论，列最小动作和未来验收|计划登记等于已交付，或本报告已批准新产品方向|

本轮新增验证仅为静态审计：以固定源码的`agent_definitions.inspect_bundle`／`workflow_definitions.inspect_bundle`检查完整包、资源摘要和schema，再直接遍历所选根的精确引用。结果为**32个preset、80个bundle（31 Agent／49 Workflow）、97条精确节点引用、错误0**。九个根的Skill来源遍历用于核采用范围，未运行生产编译器的完整执行路径，未安装包、跑产品测试、调用模型、启动服务或训练。回执保存于本worktree忽略的`.ergora/checks/wa1-readonly-audit/`；公开报告不依赖本机绝对路径或未提交原文副本。

源码、资源与历史交付分开核对；旧研究中的“尚未实现”按固定基线消费者和同片最终记录修正。例如领域交付早期的“没有根报告”已经由当前`review_requests.report`覆盖，不能照抄为当前缺口。历史CI仅按相应交付记录引用，本轮未联网重验这些CI原页。

## 2. 来源身份与方法边界

本轮直接重读十份官方原文，公开GET均返回200。前三份是2026-11-15取得的动态文档快照；其余用上游commit固定。以下来源是方法证据，不是对第三方服务、执行器或效果的验收。

|来源|精确身份／实际读取|对本次审计的用途|
|---|---|---|
|S1 Anthropic团队文章|[How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic.md)，发布2026-10-15；22,410B；SHA256 `a322aa7632a44e82af40bf467cd89912eb870ea646bb5df7b4d51c80d8dd8577`|可运行验证、fresh reviewer、找问题与复核分工、事故eval、复审收敛、精确commit批准、风险与上线后回滚|
|S2 Claude产品文档|[Code Review](https://code.claude.com/docs/en/code-review.md)，10,665B；SHA256 `78ff48627f8e08e5551e254a963356b6988160a6b0edc873fc8772e3f301e06a`；[本地审查](https://code.claude.com/docs/en/code-review-local.md)，14,272B；SHA256 `092b76076a9fad31f02a4054ae6f601d6b864ffc07030e90ef3991e7e30ec6f5`|区分托管服务、本地能力和团队内部流程。托管review读取源码，不build／运行项目代码，评论不代替批准或阻断决定|
|S3 Claude公共插件|`anthropics/claude-plugins-official@b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6`的[code-review command](https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/commands/code-review.md)及[pr-review-toolkit command](https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/commands/review-pr.md)|具体分工与finding验证；两插件不是同一实现，toolkit的simplify可编辑，不能把整个包称只读reviewer|
|S4 Megatron Bridge|[review-pr](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/review-pr/SKILL.md)固定`40d446774bb17a5dfe1029afd0fd18004d49dafb`；[MoE optimization workflow](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-perf-moe-optimization-workflow/SKILL.md)固定`55694838ce73cd23b00ff95bd00512aefb963ce0`|完整调用者、数值／分布式／恢复合同、尝试推翻finding；freeze→fit→scale→profile→retune→validate。两份是不同快照，不能混写成同一个上游版本|
|S5 slime|`THUDM/slime@79aa41a884ab0bf65222c94418f6357d3c31192b`的[add-rollout-function](https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-rollout-function/SKILL.md)|sample／group／mask／status与train/eval返回合同。其他review／reward／filter方法本轮沿已交付Skill及既有研究核对来源，不声称重新审过整个trainer|
|S6 AI Hero|`mattpocock/skills@4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`的[codebase-design](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/codebase-design/SKILL.md)、[code-review](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/code-review/SKILL.md)|真实接口义务、module／seam／adapter、Standards／Spec分轴、项目规则优先；Skill依赖宿主执行，没有自己的持久调度|

其余依据沿仓库既有研究和当前实现追踪：[重构与六阶段研究](../research/2026-11-12-refactoring-workflow-agents.md)51–73行所列SWE-agent／Agentless／TestGen-LLM论文、[工程Skill盘点](../research/2026-11-14-local-engineering-skills.md)、[循环优化研究](../research/2026-11-15-iterative-optimization-architecture.md)、[持续演进研究](../research/2026-10-28-continuous-evolution.md)。本轮未重新获取或复现这些论文及全部第三方源码。TorchTitan／PyTorch等固定来源可从当前[flow-map Skill](../../src/ergora/data/presets/agents/ergora-training-flow-analyst/skills/ergora-training-flow-map/SKILL.md)40–43行追踪，不能把引用它们当成已集成对应Trainer／profiler。

既有[Anthropic对照研究](../research/2026-11-15-anthropic-code-review-comparison.md)及[R0–R4计划](../plans/2026-11-15-review-validation-evolution.md)已正确说明：此前研究过公共插件／产品，**没有证据证明既有三路模板最初由S1这篇特定文章派生**。本报告比较方法相合与采用缺口，不倒推因果。

## 3. 当前精确根与生产消费边界

下表版本指资源中的ID/version，不是目录名或研究日期；digest来自本轮完整bundle静态核验。

|preset／根|版本与bundle digest|实际叶／消费方式|
|---|---|---|
|pretraining-review／`ergora-pretraining-review`|`1.0.0`；`d482a88fd372d0e8fd862841249f1821ee08de874e20190e7811346b0fde4be7`|`general/{structure,correctness,test-value}/review`＋`domain/review`；proposal-leaves|
|posttraining-review／`ergora-posttraining-review`|`1.0.0`；`7206e155114560e55beb54e2d62528c7d18e11cf3d8a77e9687588d614e328e3`|同上四叶；领域Agent不同|
|repository-governance／`ergora-governance-delivery`|`1.0.0`；`e82c02d01d2c717a38f35f242107efce32dd873027a4a3a6fb0f18f7d1fae077`|knowledge-map／boundary-test＋三路review；development-v5|
|large-change／`ergora-large-change-delivery`|`1.0.0`；`25dbfff6830e4123bedbfe975c964de96b8a9ce0ed8c76e8f365fecf2f7e2cc8`|contract／server／client／integration-tests＋三路review；development-v5|
|refactoring-quality／`ergora-refactoring-template`|`1.1.0`；`79376039d7794e228c4f4e57e42383927460c26da0948781b9f7d4cc4a62b48e`|inventory／plan／rewrite／compatibility＋三路review；七个Agent实例均继承完整工程质量Skill|
|training-optimization-v3／`ergora-training-proposal`|`3.0.0`；`7532009200221f23d70474e5882c447df4fc65350fd94bed6e79d0566153dd79`|flow/map→analysis/{design,profile}→kernel/assess→measurement/review；五叶proposal-leaves|
|retrospective／`ergora-skill-retrospective`|`1.0.0`；`357659a19315d3ed0a3bc1ed239bfbcd6de2d091820b8459cd9e15898a47dce8`|propose→review；共同继承复盘证据Skill|
|memory-retrospective／`ergora-memory-retrospective`|`1.0.1`；`f80ea1f1512d5ac0d31ec90cd16a4c1360fd06aeee56a46eca76f04d419cd18b`|propose→review；memory证据Skill|
|workflow-retrospective／`ergora-workflow-retrospective`|`1.0.0`；`404068c127a352dcb0f21f1fd7cc8c1cffe6587dcd881d5ac74f78f1f4f6d737`|propose→review；workflow证据Skill|

真正消费者分四类，不能用相邻路径的能力互相替代：

- **显式单叶**：[CLI](../../src/ergora/cli.py)1147–1164行调用`workflow_definitions.prepare_input[_from_manifest]`及`agent_runs.run_input`。[compile_input](../../src/ergora/workflow_definitions.py)377–395行明确标记ports尚未执行，只编译选中Agent的完整输入。优化／复盘图中的依赖不会由该入口自动跑完。
- **外部审查原件与汇总**：[CLI](../../src/ergora/cli.py)830–846行消费[review_requests](../../src/ergora/review_requests.py)；prepare绑定完整source和manifest，report读取操作者显式提供的原run，不启动整图。
- **正式六阶段与ReviewDAG**：[tasks.py](../../src/ergora/tasks.py)159–182行冻结manifest并接入[native_six_stage.invocation](../../src/ergora/native_six_stage.py)；[reference_executor.py](../../src/ergora/reference_executor.py)496–530行生成实际阶段输入与candidate-bound调用原件；[reference_workflows.py](../../src/ergora/reference_workflows.py)261–303行按依赖并行调度review，核独立session后汇合。这是真实执行能力，但native入口只接受一个受限原六阶段实例，不是任意混合图引擎。
- **评价与采用**：[CLI](../../src/ergora/cli.py)875–906、1384–1389行分别消费`retrospectives`和`optimization`；[Web](../../src/ergora/web.py)571–614、1081行也消费同一owner。生成／导出、评价、明确采用分别由原模块持有，不由提案文本授予。

资源继承本身也有实现：[workflow_definitions.py](../../src/ergora/workflow_definitions.py)155–187行累加完整资源并保留来源、拒绝冲突，277–320行核祖先权限／预算。这证明资源可进入消费者；实际会话是否取得全部附件仍要看相应运行原件。

## 4. 预训练／后训练PR审查：来源到采用矩阵

|来源→方法|实际资源／节点／生产消费者|已有验证|缺口或不采用理由|
|---|---|---|---|
|S1／S3／S6：独立分工，固定原diff与要求|[delivery-review](../../src/ergora/data/presets/workflows/ergora-delivery-review/workflow.json)38–91行为structure／correctness／test-value三路all-join；[预训练根](../../src/ergora/data/presets/workflows/ergora-pretraining-review/workflow.json)38–75行再接domain，后训练对应。正式ReviewDAG按原候选调度；外部包沿`review prepare-input`单叶调用|领域交付、六阶段旅程均有真实独立会话；外部`report`核distinct原run ID、精确source／manifest／task，保留每叶原文|独立会话不证明统计独立或多后端效果；外部根的四叶声明不等于自动调度已发生。不能以模型票数替代owner批准|
|S4：完整调用链、数值与分布式不变量、反证finding|[预训练Skill](../../src/ergora/data/presets/agents/ergora-pretraining-reviewer/skills/ergora-pretraining-review/SKILL.md)8–28行：token／mask／分母、accumulation／update时钟、mesh／collective、RNG／checkpoint／restore、成对性能。由`root/domain/review`实际消费|固定产品`0b5b5f1ff7a3463fcb10cf5a05e5f7c7bcae7c62`的两个真实Codex CPU例：mean-of-means回归5.333…对oracle7.5被请求修改；合法重分组被approve|只是两个具体算术合同；scalar检查结果已在材料中，不是盲测。没有多rank次序、真实梯度／更新、恢复一致性、收敛或GPU收益证据|
|S5＋Bridge证据分级：按实际算法检查反馈链|[后训练Skill](../../src/ergora/data/presets/agents/ergora-posttraining-reviewer/skills/ergora-posttraining-review/SKILL.md)8–27行：SFT／偏好／RL区分，rollout→reward/filter/group→trainer→weights，mask／sample状态、版本／staleness、queue／actor恢复。由后训练domain叶消费|同一固定产品两个真实CPU例：丢mask的51.5对oracle3被请求修改；合法masked变体被approve。四run及输入范围见[领域交付](2026-11-15-training-domain-reviews.md)18–35行|不能推广为PPO／GRPO数学审计、独立生成质量或异步系统完整验证；当前Skill正确地不硬套一个PPO公式|
|S1／S3：另一组agent逐条核实finding|当前两域Skill要求reviewer自行反证、读合法配置变体；`review_requests.report`94–152行只核原run、完整覆盖与分支decision。缺叶为incomplete，任一request-changes保留|现有完整报告和保守汇总是已实现能力；不会用其他分支赞同覆盖原request-changes|**尚无逐finding独立复核消费者／生命周期**；没有“确认／驳回／缺证据→独立原run”的结构闭合。R1已计划，未实现；不能把self-check或all-join称第二组验证|
|S1：事故与干净PR的质量eval，跟踪有害建议／人类时间|通用`evaluation`已有可信suite、双方完整评价、validation／holdout比较能力；领域已有四个小例|固定输入／原输出交付核过；安装和自身审查有记录|**没有本审查组合的成对质量eval**。无已确认回归集上的漏报、合法非默认样本误报、有害修复、轮数／延迟／可观测成本对照。R2不是既有四例的改名|
|S1：有限复审、精确head批准和风险分工|source／manifest／原run精确绑定；正式任务继续沿既有批准。新head需新输入身份|可核原包、候选和批准，不借旧批准授予新候选|R3增量复审及R4风险提示尚未实现。应沿原owner显式有界；原文三轮和0／1／2人政策不是通用阈值，也不能降低既有人工release|

上表领域固定交付有自己的安装／适用CI与独立终核；它们证明该片交付，不证明reviewer总体效果。后来增加的完整`report`已在当前基线，不能沿旧领域交付35行的中间状态声称“现无汇总”。本报告也不把完整报告误称为自动四路执行。

**有意适配：** S3固定插件9–10、37–49行要求假设工具都工作、部分bug扫描只看diff，并排除依赖特定输入／状态的问题。训练mask、合法配置、collective次序和恢复故障恰会依赖输入／状态；照搬这些过滤会损害目标职责。Ergora要求完整调用者、具体可达配置和原失败／unknown，属于必要适配。S4默认单agent，S6要求双轴并行，S3又有自己的分组；应取职责和反证方法，不能把任何一家的agent数量或置信度数值当普适策略。

## 5. 六阶段开发与重构：来源到采用矩阵

|来源→方法|实际资源／节点／生产消费者|已有验证|缺口或不采用理由|
|---|---|---|---|
|S6及既有六阶段研究：先调查／计划，再编辑、整合、可信检查、独立审查|`inventory→plan→work→integrate→verify→review`由原正式task／Temporal链持有；native调用经`tasks`、`native_six_stage`和原executor，不是Skill模拟状态机|[六阶段真实旅程](2026-11-13-six-stage-native-journey.md)29–44行：固定产品`5af9882367bbe5708f1a86ddabc16b2b665e9a49`，实际CLI＋Temporal＋7个Codex会话／9个job，精确owner plan批准，REVIEW_READY；1,317事件重放及原run恢复|证明该治理组合，不证明任意native嵌套、异构后端、Windows服务或v10运行中取消故障。已有真正plan等待／批准，不能称“完全没有人类关卡”；详细设计问题闭合见WA3职责|
|S6：深模块、调用者义务、locality、deletion反事实|[refactoring-quality根](../../src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/workflow.json)14–17行携完整`ergora-codebase-quality`树，digest `45bb58d30e958c314f29ecc9ed50c016f1ca3d2245b59d66fab7870da0a07693`；[module-design](../../src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/skills/ergora-codebase-quality/references/module-design.md)3–9行要求真实生产调用、依赖分类、生命周期、迁移和删除实验。七叶经祖先继承，由正式准备／工作／审查owner消费|[S1工程Skill交付](2026-11-14-engineering-skills.md)15–19行：固定发布`fde425164e45a15e255eb62e0e6f6fd959e00f6c`，四次真实只读调用，25份inline／11份完整参考；识别目标仓库非默认风格与双caller／恢复缺口|这次试用没有重跑完整v1.1重写六阶段；不能把资源读取和只读建议称为重构完成或质量提升|
|六阶段研究＋TestGen／Agentless方法：生成、兼容、可信oracle分离|[refactoring-work](../../src/ergora/data/presets/workflows/ergora-refactoring-work/workflow.json)42–83行`rewrite→compatibility`；正式owner提供前驱候选，原integrate／verify保留检查权威|[重构第三轮](2026-11-13-refactoring-journey.md)67–89行：baseline `19cd20e31210eb938020df034427f53dcc9c76ed`→candidate `63004b35f123e0efa49f3746627247d9036d1de8`；实际串行，独立checker核212 normalize／6 aliases、2个真实caller、generator／恢复，623事件重放；原两轮失败保留|原structure回复遗漏明确deletion反事实，后由同候选独立离线补核闭合；不能倒填为原模型已经输出。一次等价重构不证明一般架构收益或性能改善|
|工程Skill研究：仓库规则优先；测试接缝捕获真实失败|[工程Skill入口](../../src/ergora/data/presets/workflows/ergora-refactoring-template-v1.1/skills/ergora-codebase-quality/SKILL.md)6–12行按角色读取repository-style／module-design／test-seams；通用[structure](../../src/ergora/data/presets/agents/ergora-structure-reviewer/skills/ergora-structure-reviewer/SKILL.md)和[test-value](../../src/ergora/data/presets/agents/ergora-test-value-reviewer/skills/ergora-test-value-reviewer/SKILL.md)也已有真实caller／失败边界原则|S1实测没有强推Bridge行宽／strict类型约定，指出局部normalization通过不能覆盖双caller恢复失败|**采用范围较窄：**`repository-governance`、`large-change`和两域general review没有继承这份完整质量Skill，只带已有短指导。是否需要新可选根取决于真实任务；不能说原则全无，也不应无差别塞入全部references|
|原研究中的语义编辑／机械迁移／架构lint／mutation|[重构研究](../research/2026-11-12-refactoring-workflow-agents.md)27–49行分别审过Aider、Serena、LibCST、Import Linter、mutmut等真实接口|本轮只复核原研究与当前消费者，没有这些新增工具的安装／运行验收|是适用时可选工具，未接入不自动构成缺陷。已有精确架构／接口检查时不叠重复机制；小手改不先建codemod框架；mutation分数不授权删测试；不能把MCP配置当工具已准入|

人类在方向、取舍、规范和验收上的参与要求已在原计划／重构instructions中，但文案要求与机器强制的“关键问题已回答”不同。本轮不把WA3的结构负例扩大为运行时批准绕过；WA4应以WA3的原证据决定最小设计包和问题闭合契约。

## 6. 训练优化：来源到采用矩阵

|来源→方法|实际资源／节点／生产消费者|已有验证|缺口或不采用理由|
|---|---|---|---|
|S4＋TorchTitan／slime：先还原算法、执行依赖、状态生命周期，再找冗余|[flow-map Skill](../../src/ergora/data/presets/agents/ergora-training-flow-analyst/skills/ergora-training-flow-map/SKILL.md)12–30行分别要求算法图、执行图、source锚点、rank／stream／actor及生命周期；v3的`root/flow/map`将其交给两个analysis叶|v3固定发布`eadabc0441991a02acc06e17efd8d6c16b7d9d27`，两个公开任务各五叶共十次真实调用，完整前驱／stdin／固定资源交付可核|是源码分析和显式交接，不是训练运行图或实际critical path；未运行目标代码、GPU或profiler|
|S4＋PyTorch：固定workload／质量合同，profile与稳态计时分开，匹配诊断工具|v2 experiment-designer／performance-analyst／measurement-reviewer各有完整evidence-contract；[measurement参考](../../src/ergora/data/presets/agents/ergora-measurement-reviewer-v2/skills/ergora-measurement-reviewer/references/evidence-contract.md)5–9行要求原件、有效工作量、同步／窗口、全rank、variance、wrapper／端到端分离；`optimization-performance-diagnosis@1.0.0`另带完整工具路线Skill|工程S1片的实际profile叶对缺baseline提出原runner反馈命令，对不匹配phase／单rank合成trace保留unknown；资源树摘要`88017dbf291214dcfe387603038b9ad3282184a7dc6fe02593d3c1abb838f5e1`|方法已采用；实际采集、reader可用性、未profile成对计时和质量收益仍由原实验验收，不能从Skill名单推出工具已运行|
|按瓶颈选择干预、保留kernel专业判断|[v3根图](../../src/ergora/data/presets/workflows/ergora-training-proposal-v3/workflow.json)44–119行及[根Skill](../../src/ergora/data/presets/workflows/ergora-training-proposal-v3/skills/ergora-bottleneck-optimization/SKILL.md)12–21行：flow→analysis→kernel assessment→measurement；原task保持，完整结果交接|[v3旅程](2026-11-15-training-bottleneck-path.md)29–67行：主机例kernel明确无需修改；算子例仅有条件设计；两measurement都因缺真实证据而request-changes|**kernel评估保留是用户已明确决定**，不是未消除的强制重写。早期研究提出取消必经kernel，后续[Q计划](../plans/2026-11-15-domain-review-optimization-quality.md)的决定及v3覆盖它；不能据旧建议再次移除专家|
|S4：retune→validate→再识别瓶颈，保留所有轮次|`training_rounds.py`30–57行固定初始anchor／每轮comparison／parent SHA，消费者为原CLI的create／read；[根Skill](../../src/ergora/data/presets/workflows/ergora-training-proposal-v3/skills/ergora-bottleneck-optimization/SKILL.md)33–39行明确baseline、runner、采用仍归原owner|[Q4.1](2026-11-15-training-round-chains.md)13、19–29、43–47行：固定`750dd68ff2b1e41f6fe390d6a52e651bf41d5642`，两candidate实际CPU exit7／exit9，18CLI不可变两轮索引与新进程读回，原失败完整保留|是真实执行失败与跨轮索引合同，不是成功优化或自动循环；索引不判收益、不授权、不推进baseline|
|用户要求：达到可验证目标／预算上限／边际收益不足时停止|当前`training_cycles`等已有有限准入、授权、投递／对账原语；但固定[reference_training_worker.py](../../src/ergora/reference_training_worker.py)334行投递`TrainingCycleWorkflow`，509–535行worker仅注册`ExperimentWorkflow`|现有前置小片有自己的交付，不能拿它们代替尚未实现的总Workflow／下一轮接受门槛；WA2追踪详细运行边界|**本基线没有闭合可运行的目标循环。** v3根明确静态只读，方向选择仍显式调用；c1b1／c1b2／c1c／c1d是接续计划。不可因图有依赖、模块有cycle名称或提交已持久化而称“直到达标自动优化”|

这里的缺口是本域循环的执行与停止合同，不是“必须换LangGraph”。版本化模板沿自己的编译／DAG和原Temporal运行；仓库另有[local/agent_platform/search.py](../../src/ergora/data/reference/platform/local/agent_platform/search.py)76–99行的LangGraph＋SQLite有界候选搜索，其[独立CLI消费者](../../src/ergora/data/reference/platform/local/agent_platform/cli.py)211–213行及边界由WA2追踪，本轮也直接核了上述源码。不能说全仓库没有LangGraph，也不能把该搜索checkpoint当训练循环或正式模板运行器。

## 7. 复盘与持续演进：来源到采用矩阵

|来源→方法|实际资源／节点／生产消费者|已有验证|缺口或不采用理由|
|---|---|---|---|
|持续演进研究：原始结果、派生经验与有权限规则分开|Skill／memory／workflow三类复盘根均为propose→review；[复盘证据Skill](../../src/ergora/data/presets/workflows/ergora-skill-retrospective/skills/ergora-retrospective-evidence/SKILL.md)8–16行要求完整原材料、失败／cancel／unknown、精确引用、全候选树及独立评价计划|null候选是合法结果；[workflow复盘交付](2026-11-14-retrospective-workflow-candidates.md)23–39行：固定`54fcd0b188f1f1dc46229dfe504f5dddb9c4aaea`，实际Codex→Claude调用产出candidate:null／review approve，固定资源和checked前驱完整|证明链路与不无故改规则，不证明workflow质量提升或一般跨后端独立性|
|同一研究：候选定址、显式导出、原评价／采用／回滚|[retrospectives.py](../../src/ergora/retrospectives.py)152–181、225–268、282–310行冻结来源、核citations／baseline／candidate、导出完整树；返回`quality_evaluated:false`、`adoption_authorized:false`。CLI／Web调用原owner，不直接改活动头|[Skill采用旅程](2026-11-14-retrospective-skill-adoption.md)9–17行：14次实际CLI export→import→同suite双方评价→compare→adopt→rollback，原head按1→2→3追加且恢复baseline|使用合成正候选及scorer，只证明身份／门禁合同；不能宣称模型生成的规则带来泛化改善。该片自己的历史CI曾取消，不能抹为该SHA全绿|
|GEPA：反馈驱动候选搜索、validation／holdout与显式采用|[optimization.py](../../src/ergora/optimization.py)24–68、164–184行真实调用`gepa==0.1.4`，不向搜索接口发送holdout，限制metric calls／proposals／时长／报告成本；[evaluation.compare](../../src/ergora/evaluation.py)170–197行核同suite、完整双方结果、正确性、validation gain与holdout不退化；[skill_assets](../../src/ergora/skill_assets.py)129–153行保留活动head修订与回退|[S4交付](2026-10-31-s4-skills.md)13–27行：真实SDK＋确定性提案／evaluator，实际选不同候选，身份篡改、部分结果、退化、预算失败和回退有独立复核|**不是所有迭代都未实现。** 但这属于Skill文本搜索，不是任意工作流循环或训练优化控制器；尚无真实模型效果／泛化收益，报告cost不是provider账单硬限额|

采用步骤及可信evaluator边界在[INTEGRATIONS](../INTEGRATIONS.md)70–129行已有公开合同。应复用它们补review质量评价，而不是因为当前缺少特定任务集再建一套评价／采用账本；候选修改scorer、阈值、holdout或活动baseline仍应由原owner拒绝。

## 8. 缺口优先级、最小建议与未来客观验收

以下是待WA4汇总和设计讨论的建议，不是本轮实施或已经决定的阈值。优先级按误导用户／接受错误结果的风险和现有消费者排序；沿原owner补合同，不另造调度器、实验库或Skill注册层。

|优先级／缺口|最小建议及归属|未来验收应直接观察什么|
|---|---|---|
|P1／G1 finding复核与review质量缺少闭环|沿已登记R1→R2，给原finding绑定source／head／manifest／提出run，再关联独立反证run和确认／驳回／缺证据；保留原意见与少数意见。复用`evaluation`可信suite比较原审查与新组合|至少跑真实可达缺陷、可推翻误报、合法非默认配置、必要证据缺失；错head／缺叶／unknown不能变通过。固定模型／输入／预算并保留每次原输出，报告漏报、误报／有害修复、轮数、延迟及可取得的成本。改善阈值和样本策略由设计确定；无改善也须有可接受的否定结果|
|P1／G2 目标训练循环与收益停止尚未交付|按已有c1顺序接原budget／runner／Temporal／round索引；在原合同定义目标oracle、质量不退化、initial／current／candidate、可比测量、预算和边际收益算法。与WA2合并，不建第二个搜索权威|用固定输入使达到目标、正确但无收益、质量退化、噪声／证据不足、轮次／预算耗尽、取消／超时／丢回复分别发生；保存每轮原结果和停止原因。用用户认可的重复测量与阈值计算，不能由LLM“足够好”结束。unknown先对账，不能重领预算／偷换baseline；人工采用门槛保持|
|P1／G3 设计／知识问题只有部分提示要求|保留现有精确plan等待及owner回执；把必要设计报告、未决问题、选项／取舍、来源／公司知识缺口、每轮答复和明确决定绑定同一设计版本。优先扩原plan消费者，采用WA3实际证据|必要问题未回答、资料缺失／冲突、拒绝／撤回或关键设计变化时，实际work调度保持阻断或使旧确认失效；已明确允许的假设有原答复可核。验证正常答复后的恢复，不把三段非空“BLOCKED”文本等同问题已经闭合，也不重复索取无关日常开发许可|
|P2／G4 工程质量采用范围与来源追踪容易失联|先在项目文档维护来源→方法→版本资源→实际消费者→验证／限制登记；确认governance／large-change／训练general叶的真实需求后，才发布继承必要工程参考的新可选根，保留旧manifest|新根的每个实际会话都取得完整选定资料；来源／内容摘要、权限／预算与旧任务身份可核。用非默认仓库风格、双caller／恢复失败场景检验选定职责；不把资料更多当收益，不用同名全局Skill替换冻结资源|
|P2／G5 事故／误报反馈没有任务专属评价闭环|将已确认回归、误报／有害建议及复盘来源送回原组件协议、Skill或确定性检查；沿G1评价新规则，保留失败与适用范围|原案例在固定candidate上可复现；新增规则在合法变体／独立保留样本上比较；规则来源和采用／回退修订可读。lint／现有合同能精确处理的重复问题归原检查，不再复制多个提示文件|
|P3／G6 安全分支、平台review与上线策略的需求未定|仅在真实团队／部署消费者需要时评估专门security review、发布评论、merge queue、flag／rollback及风险提示；沿原后端／平台／发布owner，记录权限、许可、支持范围|先有具体目标仓库／部署、原候选和可核操作；分别验read／run／comment／approve能力及失败，不把托管服务或CLI插件名称当已支持。没有消费者时保持明确延期，不为追齐Anthropic内部平台改变现有人工release|

G3的详细机器合同与G2的取消／恢复细节分别由WA3、WA2原报告支持，本报告不代替那两路独立审计。它们的结构负例只证明相应边界，不能扩大成未经实测的运行时批准绕过或训练失败结论。

## 9. 有意不采纳、未交付候选和未验证效果

|对象|本基线应如何表述|理由或后续条件|
|---|---|---|
|Anthropic内部全套／自动低风险merge|未复刻；研究中的有用方法可按R1–R4分片适配|内部merge queue、trusted author、0／1／2人批准和flag策略需要具体团队消费者；原文也保留人类方向／风险判断，公共产品不替代批准|
|上游硬件、模型、窗口、轮数、置信度与编码规范|不直接设为全局默认|Bridge的TP／EP／BF16／训练步数、B200指标、三轮、confidence80及特定lint／docstring适用于各自栈；需真实配置／成本与用户认可依据|
|Aider／Serena／Agentless／PR-Agent／mutation等整个工具栈|原研究中的可选候选；不因有README或配置而称集成|角色、编辑器、源码工具、evaluator和运行器职责不同；许可、依赖、能力和原owner接缝各自验收，不需要整套迁栈才能采用方法|
|BBuf历史知识／KernelWiki等全库注入|按问题选择资料，不整包复制为训练审查合同|已有[PR／MR研究](../research/2026-11-15-pr-mr-review-tools.md)区分serving／kernel与trainer语义，并保留固定版本／许可待核；历史经验不能证明当前dispatch、梯度或恢复|
|kernel assessment|保留在v3路径，允许明确“无需kernel修改”|后续用户决定优先于早期研究建议；避免用每轮必须重写算子制造工作|
|BR1后端指导／BR2报告叶|**未合入，不能作为本基线能力**|[固定并行状态](2026-11-15-backend-review-and-reporting.md)11–15行：BR1仅窄文档／配置独立审查通过，真实新安装／厂商review等待验；BR2真实小报告已发生但独立审查仍待。两者的后续状态由各自分支另核|
|“工程／审查／优化能力已提高”|未得到本轮或历史小例支持的效果主张|已有资源、真实消费者和小例足以反驳“研究毫无复用”，仍不足以证明总体bug recall、可维护性、收敛、GPU或端到端性能改善|

本轮唯一新增的非忽略文件是本报告；未实现上述建议、未修改原模板默认值、未运行额外模型或实验，未提交／推送。报告收尾核本地Markdown链接目标、原tracked diff及新文件空白，HEAD保持固定基线，ignored证据目录不进入变更范围。WA4可据此直接讨论G1–G3的具体合同、优先级和客观验收，并保留已有可用能力与其精确证据。
