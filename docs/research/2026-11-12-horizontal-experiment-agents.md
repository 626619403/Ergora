# 横向诊断、实验与独立评价协作

检索及源码核对日期：2026-11-12。承接[专家模板重整 X3](../plans/2026-11-12-specialist-template-refresh.md)，在 R1–R10 之后复用其固定原件，按[技术方向与职责两轴](2026-11-12-optimization-taxonomy.md)研究跨域协作。本轮只读公开来源和仓库源码，未安装依赖、调用模型、运行 GPU／训练或复现性能。仓库检查点 `42902bbe1af59059b287a38f0c9efa51a72dca4b`，产品基线 `5ab6d350024de8515487d0bedb3b950be60ac867`；当前工作树中的方向研究是研究证据，不能授予产品运行能力。

**建议采用现有冻结合同、独立评价和候选采用边界，优先让原可信 runner 按需消费 Optuna；已有 Ray 环境及分布式试次需求时再适配 Tune。** AIDE 与 RD-Agent／FT-Agent 是确有实现的实验 Agent 闭环，值得保留完整内部协作，当前应借鉴并作为可选适配候选。它们尚不满足 Ergora 的逐内部会话完整资源、父权限、总预算和原身份恢复门禁，完整 native 模式保持 `unsupported`。没有必要再建立搜索引擎、正式实验账本或顶层调度器。

## 已有边界与本轮增量

|现有消费者|源码实际行为|X3 可复用处与限制|
|---|---|---|
|[GEPA 适配](../../src/ergora/optimization.py)|固定 `gepa==0.1.4`；仅生成 `SKILL.md` 候选，绑定 baseline／suite；提供 train／validation，拒绝 holdout ID；限制 metric calls、proposals、墙钟和 reported cost，不移动 active head。|保留文本资产搜索用途。调用由外部 proposer argv 和 evaluator 承担；不是训练参数／模型权重优化器，也不是通用实验 Agent。成本为返回值，不能当服务商实际花费证明。|
|[评价](../../src/ergora/evaluation.py)|冻结 evaluator argv、声明文件及文件参数摘要，调用前后核一致性；全 suite 完成、candidate required checks、validation minimum gain 与 holdout 不回退后才 eligible。|保留生成／评价分离。split 访问限制、文件摘要不等于秘密 holdout 的操作系统隔离，也不证明独立抽样、统计置信度或 evaluator 的语义正确性。|
|[ForgeKernel](../../src/ergora/kernel.py)|原生 campaign＋操作回执，固定源码／global config；未知 prepare／run 保留 `outcome_unknown`，继续前对账；产物标为 candidate-only。|沿原 campaign 身份继续。R1／X2负责其内部搜索与工具边界，X3只复用外部合同和评价出口，不复制 campaign 调度。|
|[参考训练执行器](../../src/ergora/data/reference/platform/local/agent_platform/training_executor.py)|逐精确实验 `run-local`；baseline／candidate 独立 checkout，原 runner 执行，`perfctl archive`核证据；MLflow按 manifest SHA 查重并记参数、指标、完整产物和 gate。|MLflow是可选观测投影，既有原实验／job／manifest／evidence 继续拥有执行与采用语义。没有常驻训练队列消费者，不能凭记录到 MLflow 称实验成功。|
|[WorkflowInput](../../src/ergora/reference_inputs.py)、[单叶调用](../../src/ergora/agent_runs.py)|原输入版本选择原六阶段 SDK workflow／adapter；`run-input`独立调用一个叶子，不执行图前驱／端口或正式批准。|[WorkflowDefinition](../WORKFLOW_DEFINITIONS.md)可描述静态嵌套、依赖与数据绑定，尚不是混合 Agent／native 流程图 runner。完整实验接入须有原运行所有者的真实消费者。|

可信训练门禁已有 [perfctl](../../src/ergora/data/reference/platform/upstream/perfctl.py) 与 [compare_runs](../../src/ergora/data/reference/platform/upstream/compare_runs.py)：绑定准确候选、配置、数据、环境、初始 checkpoint 与比较器；重新计算成对统计结果，核正确性／必要质量／integration／review结构化证明，再返回 `ELIGIBLE_FOR_HUMAN_REVIEW`。比较器要求以独立 paired run 为单位、AB／BA覆盖、相同源样本数和未插桩的 global completion window；默认8对、95% paired bootstrap属于固定样本筛选策略。源码明确**不提供多重搜索／可选停止校正、质量／P99批准或真实性认证**。这些限制必须随结果传递，不能因新 Agent 包装而消失。

以下纵向结果直接继承，不重新抓取工具百科：[R1 kernel](2026-11-12-optimization-kernel-agents.md)、[R2低精度](2026-11-12-optimization-quantization-agents.md)、[R3通信](2026-11-12-optimization-communication-agents.md)、[R4并行](2026-11-12-optimization-parallelism-agents.md)、[R5显存](2026-11-12-optimization-memory-agents.md)、[R6执行图](2026-11-12-optimization-execution-graph-agents.md)、[R7诊断测量](2026-11-12-optimization-profiling-agents.md)、[R8运行恢复](2026-11-12-optimization-cluster-agents.md)、[R9模型配方](2026-11-12-optimization-model-recipe-agents.md)、[R10开发重构](2026-11-12-refactoring-workflow-agents.md)。R7已核官方 Nsight BYO Skill 与第三方 MCP，R8已核 NVRx Restart Agent并经[独立审查](../delivery/2026-11-12-cluster-research-review.md)关闭 findings；不另找同名 Agent替换这些证据。

## 少量实现的可采用程度

|对象、固定版本／许可、形态|真实入口和适用范围|决定|
|---|---|---|
|**GEPA 0.1.4**，tag快照 `8b0ce6cd99a234f6b74daf37558a2ac0ce18f975`，MIT；反思式文本搜索库。[API][gepa-api]／[许可][gepa-license]|`gepa.optimize(seed_candidate, trainset, valset, adapter, custom_candidate_proposer, max_metric_calls, stop_callbacks, run_dir, ...)`；评价轨迹形成反馈，维护候选与验证 frontier。论文讨论语言模型系统的提示演化。[论文][gepa-paper]|**采用已有适配。** 继续优化文本资产；跨域训练实验可借鉴反馈结构，不把该搜索器再包成顶层自主训练 Agent。|
|**AIDE ML 0.2.2**，`6568c8bc27af51fe90ac83cdc87eb59512e4f527`，MIT；真实 LLM Agent＋完整 code-tree 实验流程，Python≥3.10。[setup][aide-setup]／[许可][aide-license]|`aide data_dir=... goal=... eval=... agent.steps=... exec.timeout=...`；Python `aide.Experiment(...).run(steps=...)`；内部 draft／debug／improve／执行／模型反馈，输出 journal、完整代码、日志和 best solution。[入口][aide-run]／[Python][aide-init]|**借鉴完整闭环；有条件适配，当前 native运行unsupported。** 可用于有受限代码执行环境的 ML 实验，未证明 Bridge、多节点或 GPU优化专用能力。不要用商业 Weco产品说明替代开源参考实现。[层次说明][aide-readme]|
|**RD-Agent FT-Agent**，`484776c211e4fbbeef03e0ec00d6bbee7362a4f4`，MIT；真实文本微调 Agent流程，非本轮新 release。[R9](2026-11-12-optimization-model-recipe-agents.md)|`rdagent llm_finetune --base-model ... --benchmark ... --loop-n ... --timeout ... --path ...`；内部假设、数据处理、LLaMA-Factory配置、fail-fast、训练与 OpenCompass反馈。|**保留完整流程的可选适配候选。** R9已核模型选择尚未实现、准备在 loop timeout之前、训练／评价各自超时和 session恢复缺口。X3补统一预算／资源／独立测试门禁，不重写内部角色。|
|**Optuna**，复用既有固定 `8c615f0404e4cd41dca763c6de235af7e36b75d5`，自报 **5.1.0.dev**，MIT；成熟搜索库的开发快照，不能称稳定5.1 release。[版本][optuna-version]／[许可][optuna-license]|`create_study(storage=..., study_name=..., load_if_exists=True)`；`study.optimize(objective, n_trials, timeout, n_jobs)`，或原执行者用 `ask()`／`tell()`与已有 runner配合；sampler／pruner／storage。[Study][optuna-study]|**优先适配参数搜索组件。** 生产片另冻结拟用 release与schema兼容，不据此安装 dev快照。没有GPU、Agent、正确性审查或批准功能；storage只保存原生搜索状态。|
|**Ray Tune 2.53.0**，`0de211850589aea71f842873bc32574c702ab492`，Apache-2.0及仓库所列第三方条款；搜索／试次执行框架。[许可][ray-license]|`tune.Tuner(trainable, param_space, tune_config=TuneConfig(...), run_config=RunConfig(...)).fit()`；资源配置、ASHA等scheduler、ResultGrid、checkpoint及 `Tuner.restore(...)`。[配置][ray-config]／[Tuner][ray-tuner]|**已有Ray需求时适配原生子流程；普通单机搜索先不用。** 原Tune拥有内部试次调度；Ergora只调用、观察、停止和核输出，不逐trial另套重复调度器。|
|**MLflow Tracking**；既有参考环境的观测服务／库，本文只归档官方网页，不额外选新发行或宣称升级。[官方用途][mlflow-doc]|现有 `MlflowClient` consumer记录 `manifest_sha`／原实验／job、参数、metrics、artifact和gate；参数来源见上表源码。|**采用现有投影。** 查询 UI、MLflow run状态、best metric和artifact上传本身不替代可信证据与原owner决定。无需再接一套跟踪服务。|

这些是相互补充的层次：Skill是可供专家读取的知识与步骤；Optuna／GEPA是搜索库；Tune管理原生试次；AIDE／FT-Agent包含模型假设与代码／配置反馈循环；Nsight与可信 runner产生／检查测量证据。完整流程可内部调用搜索库，外层预算必须包含这些内部工作，不能把库名字增加成新的“Agent数量”。

## 实际闭环中的预算、失败与归因

### AIDE：保留 code tree，外接可信评价

`search_policy()`先产生指定数量的初始 drafts，再按概率选择可调试的失败叶，否则贪心改进 best good node；`num_drafts=5`是累计初始草稿阈值，README表格的“drafts per step”不能当真实并发数。每个node保留父节点、代码、plan、执行结果、metric及bug标记；论文把“提出一个可检验的改进→执行→反馈”作为基本操作。[策略][aide-agent]／[journal][aide-journal]／[论文§2][aide-paper]

**内部feedback有用，但不是独立评分。** 候选自己选择验证划分、训练并打印metric；反馈模型读取代码／terminal output后提交 `is_bug`、`metric`、`lower_is_better`。异常、非float metric或模型判断bug会变为最差metric，但没有可信程序重算划分、指标方向和分数。它可能把错误输出／数据泄漏／指标实现差异当成进步；同一代码与日志还进入后续提示。`best_solution.py`和 `Solution.valid_metric`只是这个内部选择的产物，出口必须重新用冻结 evaluator验候选，不能信任LLM抽取的数值。[实现][aide-agent]／[输出][aide-init]

默认配置为20次step、每段代码3600秒，coding用 `o4-mini`、feedback用 `gpt-4.1-mini`、report用 `gpt-4.1`；README的旧默认与源码不同，以固定配置为准。`exec.timeout`只约束代码解释器执行，不包括数据复制／解包、生成代码、反馈、API重试、journal保存和最终报告。OpenAI后端的 `backoff_create`使用指数退避且未设置总尝试数／总时间上限；顶层 `query()`取到 token counts后仅返回output，缺少可直接消费的总cost账。[配置][aide-default]／[backend][aide-backend]／[retry][aide-backoff]

解释器每次重置Python子进程，但使用同一个experiment workspace及 `working/`；这不是不同候选的文件系统隔离，前次模型／submission／cache可遗留。超时先向解释器PID发SIGINT，超过5秒后清理该PID；源码没有等价的全rank／进程组停止与远程job对账合同。因此不能推导候选启动的子进程或远端训练已停止，也不能把数据copy模式当只读权限边界。[执行器][aide-interpreter]／[工作目录][aide-config]

CLI与Python构造器都新建Journal；配置准备生成新的带序号目录。已核入口保存journal／config／best代码，**未提供从原journal原位继续的CLI／Python恢复入口**。进程失联后先保存原目录、node、日志和所有外部执行身份；不以再跑相同命令创建新experiment冒充恢复。完整适配至少要在实际 `query`及exec callback边界接入父资源、权限、剩余额度和每node独立运行产物，核清全部内部模型调用后才可声明可运行。[CLI][aide-run]／[Python][aide-init]／[配置与保存][aide-config]

AIDE论文自身表格实验是16个Kaggle表格任务，GPT-4 Turbo，报告超过人类的分位数均值51.38、Above Median 50%；其holdout labels由外部保留，区别于Agent自行生成的train／validation划分。本文不把该准确率／分位数、论文转引的MLE-bench奖牌或RE-Bench结果转换成训练吞吐／GPU收益；也不将源码0.2.2与论文全部实验环境视为同一复现快照。目标硬件、模型版本、任务和完整成本仍须新验。[论文§3][aide-paper]

### Optuna：由原runner消费建议，硬约束在执行前检查

`ask()`返回具有原生trial number的参数候选，原runner可将其绑定到已有candidate／experiment；可信阶段结束后 `tell(trial_number, values, state=...)`反馈。这样无需迁移现有GPU调度。sampler约束是软约束，官方FAQ明确不保证hard constraints；许可、父权限、显存容量、安全的mesh组合等必须在launch前由可信准入拒绝，不能先试再以低分处罚。[Study][optuna-study]／[约束FAQ][optuna-faq]

`optimize(timeout=...)`在试次边界检查，已进入objective的训练不会由该参数硬中断；`n_trials`是**每个process**的上限。`n_jobs`多线程不形成候选隔离，也不提供GPU或文件锁。多进程共享study需适当的RDB／JournalStorage；官方不推荐SQLite并行／NFS，分布式顺序带来采样不确定性，固定seed不保证并行重放同一候选序列。[loop][optuna-loop]／[FAQ][optuna-faq]

RDB heartbeat是实验性机制，原生 `optimize`可将stale RUNNING标FAIL，`ask/tell`模式需要调用者显式处理。它只说明worker心跳过期，不能证明外部训练job停止。`RetryHeartbeatStaleTrialCallback`以新WAITING trial重排，保留original／retry history，默认 `max_retry=None`允许无限重试；适配应显式有界，并先核原job，而非让heartbeat和外层同时重启同一个workload。failed、pruned、NaN和合法无收益分别保存；pruned只表示没有投入足够资源，不能作为最终质量低劣的实测结论。[RDB][optuna-rdb]／[retry][optuna-retry]／[FAQ][optuna-faq]

恢复study状态不等于恢复训练optimizer／RNG／数据位置，也不保证sampler RNG等所有外部状态已恢复。候选代码、数据、环境或quality合同改变时，旧value及intermediate values不能自动沿用；精确重复候选也要区分cache命中与新的测量。Optuna是可调用的成熟组件，本文没有其作者基准到本目标GPU的性能结论。

### Ray Tune：内部试次恢复可用，外层仍需总额度与隔离

`TuneConfig`提供 `num_samples`、`max_concurrent_trials`、`time_budget_s`；grid会将num_samples重复应用到网格，而不是保证总trial数相等。`num_samples=-1`是近似无限采样，`max_concurrent_trials=None/0`没有显式并发上限。`RunConfig(failure_config=FailureConfig(max_failures=...))`控制失败恢复，默认0，-1无限；适配都要给有限值。[TuneConfig][ray-config]／[FailureConfig][ray-runconfig]

Ray逻辑CPU／GPU资源用于调度准入；官方明确实际CPU使用不受该数字限制，也没有CPU物理隔离，GPU分配主要通过 `CUDA_VISIBLE_DEVICES`。独立trial目录需唯一ID，actor复用还可能保留运行状态；因此并发GPU性能比较应取得实际独占设备／互不干扰allocation和独立工作目录。小数GPU、同一节点共享内存／网络／PCIe或CUDA cache不能当成匹配的独立实验环境。[资源文档][ray-resources]／[trial配置][ray-config]

`Tuner.restore(path, trainable=..., resume_unfinished=..., resume_errored=..., restart_errored=...)`区分继续checkpoint与从头重训；search space必须保持相同，只能按约定替换失效的Ray object references。已TERMINATED的trial不能恢复，训练本身必须实现checkpoint保存／读取。保留experiment directory、trial ID、trainable／param space身份、checkpoint及实际外部job映射；`can_restore()`只检查可恢复状态文件存在，不能替代checkpoint完整性与原job对账。[Tuner][ray-tuner]／[fault tolerance][ray-fault]

`TimeoutStopper`会保存已扣除的剩余budget；反序列化将last-check清空，因此不是每次恢复都重新领满额度。首次 `stop_all()`只设置last-check，后续检查才扣除间隔时间，首次检查前的setup和恢复停机间隔不在该计时中；它不足以单独表达父合同从准备开始的绝对deadline。外层沿原owner约束准备、内部retry、训练、评价与停机期间的合同时间，超时后核所有trial／外部rank确已停，不能只读取driver exit。[timeout实现][ray-timeout]／[controller][ray-controller]

ASHA使用单调增长的 `time_attr`、`max_t`、`grace_period`和halving参数；缺少time／metric时该次结果会CONTINUE。源码默认 `training_iteration`不是有效token或墙钟。论文说明资源可以是迭代／样本量等，并比较特定CNN／LSTM／worker设置，不能据其“更快找到好配置”推导本集群训练step加速。缺失／非有限结果应由原trial evaluator显式报失败，warmup前的score不应进入竞争。[ASHA源码][ray-asha]／[原始论文][asha-paper]

### RD-Agent、诊断Agent与GEPA的组合边界

R9的FT-Agent／FT-Dojo已提供真实闭环证据，同时核到 `--timeout`由loop步骤检查、场景准备与baseline先发生、默认训练100小时及benchmark timeout=0、`--path`恢复Agent session而非完整训练checkpoint；Agent² RL-Bench对Agent子进程计时，但准备／baseline在此前，启动继承完整环境。X3沿用这些确定缺口；不能将论文单B200／12小时／Qwen2.5-7B／最多2000样本的设置泛化为全任务总预算已经受控。[R9](2026-11-12-optimization-model-recipe-agents.md)

R7的Nsight分析流程可产生跨kernel／host／通信／显存的诊断证据；R8的NVRx Restart Agent可解释日志与restart建议。它们不拥有候选质量批准，尤其degraded／缺日志诊断不能变成准许重启。把这两个现有角色作为诊断输入，交给原作业／训练恢复所有者；本轮没有证据支持再引入一个可普遍定位全部跨域瓶颈并独立批准干预的成熟全能Agent。[R7](2026-11-12-optimization-profiling-agents.md)／[R8](2026-11-12-optimization-cluster-agents.md)

GEPA上游 `run_dir`能保存和恢复搜索状态，timeout／cost stopper及Pareto选择有明确接口；Ergora当前 `optimize()`每次新建run，不能据上游能力声称产品已暴露原ID续跑。其train／validation是反复用于候选选择的数据，GEPA frontier或反思自评分不具有独立holdout的身份。现有适配已在adapter／proposer处再检查预算；训练原生子流程要用自己的正确性／质量／性能合同，不能把score=1.0当成跨领域PASS。[上游API][gepa-api]／[stopper][gepa-stop]／[现有适配](../../src/ergora/optimization.py)

## 从瓶颈到方向：用可证伪的干预选择能力

先冻结目标、相同workload与允许语义变化，再用R7核capture质量、稳态窗口、全部相关rank、关键路径和未插桩基线。技术标签不决定派哪个Agent；同一测量专家可跨全部方向，模型／系统设计者可联动多个方向。按“能解释实际目标损失的证据强度、可检验性、可恢复收益上限、投入成本和风险”排序下一实验；收益上限是ceiling而非实测预期值。证据不足时先做能区分替代解释的最小测量，而非无限增加候选数。[R7](2026-11-12-optimization-profiling-agents.md)

|观察与必要核验|优先交接及互补职责|一次有界反证／干预|
|---|---|---|
|关键路径是长算子，确认实际dispatch、shape／dtype、layout与总step占比|kernel＋精度＋模型专家，测量者核整模命中|在相同输入、数学合同上替换一个kernel／layout；同时验梯度和整step。若端到端未改善，保留no_gain并查dispatch／其他瓶颈。|
|暴露collective／P2P或MoE all-to-all，确认依赖、rank偏斜和compute争用|通信、并行、集群诊断互补|固定mesh测一个通信后端／overlap；另一个隔离候选改变mesh。全rank进展与网络隔离先于吞吐排名。|
|OOM／峰值内存逼近容量，区分allocator、activation、optimizer和通信buffer|显存、并行、模型／精度、cluster共同定义可行域|先一项recompute／offload／分片；同时量host内存、传输和step时间。容量可行与性能获益分别记录。|
|CPU launch gap／capture warmup／形状波动或padding占比高|执行图、kernel、数据与模型语义专家|单独试CUDA Graph或packing／batch调度；核有效源样本、mask、RNG及graph实际replay，不把少做工作当加速。|
|loss／梯度／质量退化，或者压缩proxy更好而任务分下降|低精度、模型／配方、独立质量评价者|固定数据／初始化定位最早差异；分开精度变化与结构／数据变化，给足短恢复与最终质量预算。|
|straggler／超时／吞吐抖动，疑似硬件或恢复问题|R7测量＋R8诊断，通信／并行辅助|先核节点、时钟、rank／job与checkpoint证据；只读诊断后由原owner决定恢复。测量环境失效时不据该样本淘汰算法。|

测量若显示多个瓶颈，先选择有因果路径且预算内可区分的一项；单项完成后重新profile，瓶颈迁移再选下一方向。完整native流程若已经有内部tree／planner／角色分工，让它继续管理内部候选与交接，外层只冻结允许空间和出口，避免同时由两层修改同一配置或分别重启同一试次。

## 技术方向 × 职责的多对多矩阵

下表是D0可消费的能力关系，**不是新增Agent类别或运行schema**。表内每项可由一个多专长Agent承担，也可分给互补专家；同一精确定义可被多个方向模板引用。原执行／恢复／采用所有者保持单一。

|技术方向|诊断／归因|候选空间与实现|实验执行／测量|独立评价及采用所需证明|
|---|---|---|---|---|
|kernel／layout／fusion|profile关键路径与dispatch；模型专家核数学|kernel agent可同时改layout、fusion与精度；R1／X2 native闭环|受限编译／shape sweep、原campaign及整模命中|数值、导数、边界shape、实际调用路径与未插桩整step；原candidate采用|
|低精度／压缩|定位scale／overflow／quality差异|精度＋模型专家；R2工具与搜索，R9恢复训练|校准、QAT／QAD、checkpoint／runtime导出；实际硬件格式|独立校准／validation／holdout、训练稳定性、导出可用性及目标吞吐|
|通信／overlap|全rank依赖、拓扑／偏斜／争用|通信＋并行／kernel专家；原生合成器或配置搜索|多节点原job／全组退出；微基准与整模分开|collective顺序／数据／token、前进性、全rank与完整step，不能仅看bus bandwidth|
|并行／分片|分解stage／rank不均与容量约束|系统设计＋并行＋模型专家；R4计划／配方搜索|原trainer消费mesh／stage；checkpoint／state转换|loss／gradient／update、路由／mask、布局恢复、全局完成吞吐与成本|
|显存／offload／recompute|snapshot与全部设备／host峰值|显存专家＋并行／图／通信专家共同约束|profile与未插桩两套证据；buffer／IO／重计算代价|容量、数值、RNG／恢复、host瓶颈与整step时间，估计值不晋升实测|
|执行图／packing／microbatch|launch／padding／shape与数据流|graph＋kernel＋数据／模型专家|原编译／trainer调度，capture／cache身份与重放|mask／样本边界、RNG、梯度／状态、有效工作量与整step；组合重验|
|模型／配方／框架|数值关联、模型结构／数据／目标辨识|模型专家兼精度／并行，R9原生FT／压缩闭环|转换、有限训练、目标框架E2E、质量工具|参数覆盖、真实模态／任务、独立质量、完整checkpoint与部署兼容|
|集群／恢复|R8作业／rank／日志／故障解释|系统专家给资源与恢复建议，恢复owner选择行动|原Slurm／native executor／trainer各自状态与attempt|全组停止／前进、checkpoint／数据／RNG、丢失工作及总资源成本；缺证据unknown|

贯穿各行的“实验设计／预算监管”可由同一多专长专家提供提案，硬预算由原执行者施加；“独立评价”同时需要可信程序与独立审查者。换一个模型route或显示名只改变实现来源，不授予权限或证明错误相互独立。

## 并行候选、干预冲突与组合重验

每个候选冻结同一个baseline身份及各自完整diff／有效配置，使用独立branch或source bundle、checkout、输出／checkpoint／cache命名空间和native ID；并行仅用于互不干扰的设备／allocation或CPU筛选。候选不能共享可写训练配置、正在增长的checkpoint、sampler状态或通用 `working/`目录。共享只读模型／数据缓存应固定身份；影响编译和计时的cache预热策略预先一致。Ray试次目录、AIDE node或Optuna trial仅提供原生归属线索，不自动满足以上隔离。[AIDE工作目录][aide-config]／[Ray配置][ray-config]

在candidate产物中列出“改了哪些字段／代码、影响哪些状态、前置条件、与其他候选冲突及需要重验的范围”，映射既有candidate／experiment资料，不建第二冲突账本。常见组合包括FP8布局／kernel和graph capture、offload和通信overlap争用、recompute与RNG／graph、packing改变shape及CP负载、mesh改变collective与checkpoint语义。R2–R6的真实版本约束优先于Agent的口头兼容判断。

两个单项有效时，组合产生新的精确候选和配置SHA，重跑正确性／必要质量／恢复及匹配性能，不借用旧单项PASS。预算允许且确需归因时，预先做baseline、A、B、A+B四组；同工作量时间的交互项可记 `I=t_AB-t_A-t_B+t_base`，连同独立run不确定性。它用于说明组合效应，不能把一个点估计当因果证明。只核组合而未分解时，准确报告“此组合有效、贡献未分离”，不把收益分配给各方向Agent。

若实现依赖共同改动才能合法运行，可把它作为一个明确的联合干预候选，记录最小必需改动及替代解释；不强行拆出无效／不相容子试验。跨分支集成和最终正式采用沿原开发六阶段／可信集成，保留原owner、candidate与批准链。[训练交接](../TRAINING.md)

## 多保真、污染、测量噪声与独立错误

**多保真只负责节省筛选成本。** 每条结果注明fidelity：CPU／估计、kernel微基准、小模型／短训、目标模型稳态、完整质量／长期恢复。不要跨等级直接排score；先检查代理与目标的对应关系。R5 memory estimate漏项、R7 profile ceiling与未插桩吞吐、R1微算子与整模dispatch、R9剪枝评分与蒸馏后质量都是不同证据。R9的官方教程已提示接近的pruning候选在短蒸馏后可能换序。

ASHA或pruner的grace period至少覆盖预先定义的初始化／编译／warmup与可比较学习阶段；progress口径冻结为所需有效样本／token／update或训练墙钟，明确哪个是优化目标、哪个是预算。一个epoch、一次 `training_iteration`或配置容量tokens在不同batch／packing下可能代表不同工作量。对分数接近、误差较大或学习曲线交叉的候选保留top-K与少量预先指定的对照／探索名额，升到相同更高fidelity复核；被剪枝者只记“未充分评价”。ASHA论文与库不保证任意跨模型／precision／硬件代理永不误排。[ASHA][asha-paper]／[实现][ray-asha]／[R6](2026-11-12-optimization-execution-graph-agents.md)

**冻结三种数据用途。** 搜索者可以看train与validation反馈；final holdout／确认集的标签、评分实现与访问权由独立评价者控制。Agent自己构造的“hold-out validation”、反复查看的public leaderboard或GEPA valset都属于选择过程。AIDE论文外部分离holdout的方法可借鉴，项目当前API不向GEPA提供holdout ID只是第一层限制；若候选代码／模型API能读取label、改evaluator、调用final test服务或从共享日志取得答案，仍然发生污染。可信evaluator摘要、依赖／模型／数据revision、实际输入与完整输出应进入现有证据链，搜索Agent没有改reference／容差／质量门槛的权限。[AIDE实验协议][aide-paper]／[现有评价](../../src/ergora/evaluation.py)

搜索数越多，最高validation分受有限样本方差选择的风险越大；Cawley／Talbot的一手研究说明该偏差可与算法间差异同量级。最终先冻结胜出候选，再按预先合同做独立确认；不得边看holdout边改候选／阈值，直到通过。holdout已反馈并用于新一轮选择时，明确其已消耗，另立评价数据／合同；复用现有固定样本bootstrap时保留其无多重搜索／optional stopping校正的限制。[JMLR论文摘要][selection-paper]／[比较器](../../src/ergora/data/reference/platform/upstream/compare_runs.py)

**性能以匹配的完整运行作证。** 冻结硬件／拓扑、全部rank、功耗／时钟与并发条件、软件／有效配置、初始化checkpoint、真实输入及工作量，预热策略一致。测量者输出未profile稳态的全局完成时间／有效源样本，独立run配对、AB／BA及预定重复数；同一长job中的多个step／rank／窗口有相关性，不能膨胀成IID样本或反复共用同一baseline run。抖动／thermal／网络争用或capture缺失先作为measurement-invalid，不给算法低分。预算无法支持确认集时结果为inconclusive，保留effect及误差，不说已证有效。[R7](2026-11-12-optimization-profiling-agents.md)／[既有比较器](../../src/ergora/data/reference/platform/upstream/compare_runs.py)

**评价独立性有多个层次。** 候选作者与reviewer身份不同、session分开、执行与审查后端不同值得记录，但同后端会共享训练偏差／错误假设，不同后端也可能读同一污染资料而一致出错。使用独立参考实现或数学不变量、确定性数据／结构检查、可信指标重算、数值／梯度／update比较和真实任务质量作不同证据；模型judge仅在有冻结rubric、版本、样本与不确定性说明时参与。正确性与质量不同，速度通过也不授予收敛／恢复／P99通过。`perfctl`的reviewer ID比较与hash绑定不会认证真实作者，按其现有限制继续做独立审查。

## 总预算、失败词义与原身份恢复

父合同在**首次准备前**给出总量和绝对deadline，并预留最终独立评价／清理的额度；子预算是同一总量的切分。总账沿原任务／实验owner，不从每次loop、worker、Agent session或resume重新领取预算。AIDE retry、Optuna retry callback、Tune `max_failures`以及trainer in-job retry必须分别计数，并说明哪个原生所有者会实际行动；禁止两层同时对同一原job实施自动恢复。

|预算面|必须覆盖的工作与拒绝条件|
|---|---|
|墙钟／停机|下载／解包、环境／容器准备、compile／cache warmup、baseline、候选／内部retry、训练、评价、归档／清理、断连待对账。native只计active time时，外层仍约束合同绝对deadline。|
|模型API／token／费用|planner、coding、debug、反馈、judge、报告及失败重试；单次可调用上界与剩余额度先检查。只返回reported cost时标清口径；缺计量为unknown，不能算0或允许无限重试。|
|GPU／CPU／节点|实际allocation×占用时间、失败试次、teacher／蒸馏、评价、所有rank、host RAM、显存、网络和磁盘IO；逻辑CPU数／GPU-hours目标不替代实际进程权限和物理容量。|
|数量与存储|unique candidates、实际attempts、native trials／retries、训练token／steps、采集与tool calls、checkpoint／artifact大小、scratch／缓存总量；重复候选／cache命中分别记清。|

各阶段在launch前保留足够预算并施加可执行限制；只能步骤检查的native流程需要原owner的外部有界进程／作业控制。若无法限制一个内部API／训练动作、不能确认子进程／全rank停止，或没有真实计量消费者，拒绝该自动模式；可返回只读提案和未验范围。总预算耗尽不使尚未完成的正确性／质量评价自动通过。

以下词义用于报告归一化建议，**不新增产品正式状态枚举**；保存原native状态、完整日志和归一化依据。

|结果|可以得出的结论／后续|
|---|---|
|verified improvement|固定候选的正确性／必要质量／性能／恢复证据满足合同，交原owner决定采用；best score、exit0和MLflow FINISHED均不单独产生此结论。|
|no_gain|有效匹配测量未达到预定实际收益门槛；保留改动、成本、effect／误差与诊断。噪声覆盖门槛时另记inconclusive，不能宣称技术永远无效。|
|incorrect／quality regression|达到所需fidelity且失败条件明确，拒绝候选并保留最小反例／质量原件；不可通过改reference、换数据或放宽容差恢复高分。|
|pruned／budget_exhausted|资源分配决定或额度耗尽，保留已做的工作与停止原因；尚无完整最终质量／性能结论。|
|timeout／execution failed|操作未按约完成；记录原进程／job／rank和部分产物。只有停止、退出及输出已核，才能确认本次失败完成。|
|unknown／measurement-invalid|断连／原job未明／缺产物，或测量条件失效；不评分、不采用、不盲目重提。原owner按同一身份对账、补读或有依据地停止。|
|unsupported／unavailable|接口／继承／权限／硬件能力不支持或当前不可用；明确具体范围，可换一个已获准backend，不能静默换模型／精度／训练栈。|

恢复分开保存并核对五层身份：Ergora原task／run／candidate／experiment，native campaign／study／Tuner目录／Agent session，trial／node／attempt，实际cluster job／rank／process，checkpoint／数据位置／RNG／optimizer。搜索缓存、Agent journal、训练checkpoint和部署权重各自的可恢复性分别验收。prepare／start回应丢失先查原身份；找不到回应不能等价于没有启动，换ID重发会重复花费与污染比较。R8继续拥有集群与trainer的恢复分工，X3不建立新恢复控制面。

## 最小可组合子模板与真实接入门槛

建议D0保留以下四个职责边界，先以已有只读叶和原runner消费；是否实现native操作由D1另片验收。结构嵌套决定完整资源和权限上限继承，协作边只传具名产物／依赖，不继承对方权限。它们是可复用能力模板，**不是新顶层状态机**。

|子模板|最小输入 → 输出|实际消费者／权限／退出|
|---|---|---|
|**诊断与方向选择**|原合同、baseline、R7／R8原件、工作量／拓扑／版本 → capture质量、替代解释、排序的可证伪假设、方向／native流程及一个最小实验。|现有performance analyst／experiment designer可消费完整只读资料；离线读批准artifact，写专属分析产物。缺证据给unknown及最小追加采集需求。|
|**有界候选实验**|冻结允许空间／语义、候选、精确native版本、真实runner接口、父资源和总预算 → 原生trace／trial／node、候选代码／配置／checkpoint与所有attempt／失败／成本。|原可信runner选择一个已验native流程；Optuna ask/tell在该owner内给参数，或完整AIDE／FT／Tune保留内部协调。写隔离candidate／scratch；模型API、GPU、网络、作业操作按已授权接口。当前完整模式需D1，不能由静态图启动。|
|**可信测量与独立评价**|冻结候选、baseline、评价合同／独立数据、原生输出和实际生效路径 → 正确性／质量／恢复／性能逐项证据、effect／误差、失败及独立review。|既有runner／perfctl／compare_runs，按R9可选稳定文本任务评价工具；独立角色可替换后端。只读candidate／reference；仅评价输出可写，禁止改阈值和原模型／数据。模型判词不能替代可信程序。|
|**候选整合与采用交接**|同一候选的完整证据、预算、冲突图与组合重验 → eligible／reject／no_gain／unknown理由、可复现集成材料。|原evidence SHA批准者及原六阶段集成／复验owner；正式候选和批准不由研究／搜索Agent写入。再次改变候选或baseline重新冻结并核所需门禁。|

共同输入还需源码／镜像／依赖、模型与数据许可／revision、真实硬件、workload fingerprint、所有祖先完整instructions／context／Skill、工具与行动权限、每阶段预算及原身份映射。输出绑定这些身份与完整原件hash；native journal／MLflow只作附属产物，不替代原正式记录。

**完整祖先资源必须进入每个实际内部模型session。** AIDE的code、feedback、report，FT-Agent的planner／data coder／judge等，以及native流程的debug／retry新会话，都需沿真实调用边界注入整条结构祖先链的完整内容，或通过受限资源接口实际完整读取并留连续审计。只在外层包装提示放manifest路径、资源名或摘要不满足要求；只给主planner也不满足。先核容量，不够明确拒绝，不截断、摘要化或绕过父限制。每个内部session的实际工具／shell／网络／目录／服务操作权限不得超过任一结构父级；若流程内部opaque、不能核完整传递及权限实施，**对应完整native模式unsupported**，可保留已核的离线工具／只读专家范围。

当前 [AgentDefinition v1](../../src/ergora/data/schemas/agent-definition-v1.json)与[WorkflowDefinition v2](../../src/ergora/data/schemas/workflow-definition-v2.json)的resources只有instructions／context／skill；[task-MCP](../../src/ergora/task_mcp.py)只提供固定scope的 `list/read`。其现有native核验主要确认固定工具就绪，不能据此宣称任意新上游内部session已完整读完祖先资料。**不存在可将任意外部MCP endpoint填入resource即获得工具的接口。**

因此新工具接入必须先出现可审查的真实消费者：例如原实验runner对固定native流程暴露本次需要的prepare／start／status／cancel／resume，或指定诊断后端的受限import／query操作；逐项核参数、artifact路径／hash、实际operation allowlist、权限／网络／设备范围、进程／native ID、deadline、计量与错误。CLI存在不等于所有操作可用；未实现的cancel／resume须明确unsupported。R7第三方MCP的有界工具经验可复用，不能把其endpoint绕过现有权限装配。D1只补被选中流程必需的能力，沿原WorkflowInput／runner所有者调用，不先实现一个覆盖全部混合图的新runtime。

D0建议顺序：①采用已核R7诊断／测量合同与现有评价边界；②在真实训练项目的原runner内适配有限参数空间的Optuna和候选隔离；③已有分布式需求才适配Tune原生子流程；④逐内部会话／权限／预算／恢复具备可验证hook后再适配AIDE或FT-Agent完整闭环。每步分别验离线／CPU接口、真实模型、GPU／多节点、失败清理与恢复；前一等级成功不授予后一等级。

## 来源与核验范围

私有原件位于 `.ergora/checks/specialist-template-refresh/research/horizontal-experiments/`，保存URL、UTC、响应原文、SHA256、失败回执、固定本地输入及来源索引。本轮45次公开HTTP读取：43个200、两个404（AIDE错误的根部pyproject／config路径）；正确的setup及`aide/utils/config.yaml`随后取得，原404保持。初次公开git refs成功回显被单独记录；三次后续归档重取超时保持，未将其称为成功。JMLR PDF已取原文，本机缺pdftotext及现成PDF解析库，未安装，论文结论限于一手HTML摘要。没有尝试连接器、凭据或GitHub REST受限接口。

本轮没有安装／运行上述系统，没有新的Agent质量、GPU收益、budget hard-cap、完整继承、checkpoint或取消实测。报告中的子模板和接入门槛是D0／D1建议；研究本身只写本文与指定私有来源目录，未修改产品、模板、计划或提交／推送。

[gepa-api]: https://github.com/gepa-ai/gepa/blob/8b0ce6cd99a234f6b74daf37558a2ac0ce18f975/src/gepa/api.py
[gepa-stop]: https://github.com/gepa-ai/gepa/blob/8b0ce6cd99a234f6b74daf37558a2ac0ce18f975/src/gepa/utils/stop_condition.py
[gepa-license]: https://github.com/gepa-ai/gepa/blob/8b0ce6cd99a234f6b74daf37558a2ac0ce18f975/LICENSE
[gepa-paper]: https://arxiv.org/html/2507.19457v1
[aide-readme]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/README.md
[aide-setup]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/setup.py
[aide-license]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/LICENSE
[aide-run]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/run.py
[aide-init]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/__init__.py
[aide-agent]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/agent.py
[aide-journal]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/journal.py
[aide-interpreter]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/interpreter.py
[aide-config]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/utils/config.py
[aide-default]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/utils/config.yaml
[aide-backend]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/backend/__init__.py
[aide-backoff]: https://github.com/WecoAI/aideml/blob/6568c8bc27af51fe90ac83cdc87eb59512e4f527/aide/backend/utils.py
[aide-paper]: https://arxiv.org/html/2502.13138v1
[optuna-version]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/optuna/version.py
[optuna-license]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/LICENSE
[optuna-study]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/optuna/study/study.py
[optuna-loop]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/optuna/study/_optimize.py
[optuna-rdb]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/optuna/storages/_rdb/storage.py
[optuna-retry]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/optuna/storages/_callbacks.py
[optuna-faq]: https://github.com/optuna/optuna/blob/8c615f0404e4cd41dca763c6de235af7e36b75d5/docs/source/faq.rst
[ray-license]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/LICENSE
[ray-config]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/tune/tune_config.py
[ray-tuner]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/tune/tuner.py
[ray-runconfig]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/air/config.py
[ray-fault]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/doc/source/tune/tutorials/tune-fault-tolerance.rst
[ray-resources]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/doc/source/ray-core/scheduling/resources.rst
[ray-asha]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/tune/schedulers/async_hyperband.py
[ray-timeout]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/tune/stopper/timeout.py
[ray-controller]: https://github.com/ray-project/ray/blob/0de211850589aea71f842873bc32574c702ab492/python/ray/tune/execution/tune_controller.py
[asha-paper]: https://arxiv.org/html/1810.05934v4
[selection-paper]: https://www.jmlr.org/papers/v11/cawley10a.html
[mlflow-doc]: https://mlflow.org/docs/latest/ml/tracking/
