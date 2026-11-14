# Q4.2 有界训练循环：独立计划评审

日期：2026-11-15。评审者：Codex 独立 fresh-context reviewer，任务 `training_cycles_plan_audit`。仅评审计划与现有训练 owner 的对应关系；只写本报告，未修改产品、测试或待审计划。收到的额外源码线索均重新对照实际实现，不作为预定结论。

## 身份与结论

固定源码基线：`96b4bb5454714a73e1d5f60b880a479c195e5269`，分支 `refactor/architecture-foundations`。读取及中途身份核对时，下述训练源码、参考目录和所读原训练测试相对该基线的差异为空。共享 HEAD 随后前进到 `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`，报告最终核对时应用 `training.py`、`reference.py`、`reference_training_submission.py` 又出现后继未提交改动；这些改动不在本次评审内，已用固定基线的 `git show` 重新核对所引原接口与行号。没有审查 Q2.3b2／b3 或后继 Q4.2a1 实现，也不继承其审查结论。

路径简写：应用 Python 模块均在 `src/ergora/`；“原” Temporal 文件在 `src/ergora/data/reference/platform/upstream/temporal/perf_temporal/`；`LocalTrainingAdapter` 及原 training／training_executor／process_job／sandbox／core 文件在 `src/ergora/data/reference/platform/local/agent_platform/`；perfctl／compare_runs 在 `src/ergora/data/reference/platform/upstream/`。测试路径均从 `tests/` 起。

完整读取并在收尾复核两份未跟踪文件：

|待审文件|SHA-256|
|---|---|
|[具体计划](../plans/2026-11-15-bounded-training-cycles.md)|`1c28feb0e23f2dfc3d1cd1102e4fd7e78fca26e854f1364bd29495815038c5f9`|
|[交付记录](2026-11-15-bounded-training-cycles.md)|`8add6e2ed4f6308e4dd983804c2cdf4b07a1864926097dca522d0ca4ef95565f`|

|评审轴|结论|适用范围|
|---|---|---|
|需求符合性|approve，计划层面|可进入 Q4.2a／b 的源码核实及小片实施；计划没有把尚未实现的循环、CPU合同或既有索引宣称为真实训练验收。|
|可维护性|approve，计划层面|原实验、提交、证据、取消与批准仍归原 owner，Temporal 承载应用控制扩展；没有提出第二实验库、评分器或批准权威。|

**阻塞本次计划评审的实证 finding：0。** 这不是 Q4.2a–d 的实现、安装、运行或业务批准。计划第55–58行已把关键接缝列为未解决义务，不能因为未实现而判作现有产品缺陷；也不能在这些义务未验收时开放自动派发。下面的具体接缝和最小补充应进入相应子节点的实施与验收记录。

## 已核对应关系

|原要求／计划边界|实际源码证据与判断|
|---|---|
|先图谱、依赖与测量，再按瓶颈优化；保留 Kernel 专家|[Q总计划](../plans/2026-11-15-domain-review-optimization-quality.md)第10–11、34–37、88–111行规定该顺序；本计划第3、33行保持原 v3 提案路径，首版只运行显式有限候选，不把循环变成候选生成器或算子搜索。该缩小范围是可验收的第一增量，未冒称完成所有持续优化方向。|
|固定算法／模型／数据／质量及初始参照，保留每轮结果|`training_rounds.py:30–89` 校验原比较、绑定、初始 baseline／workload 与批准观察；`perfctl.py:56–75,93–160` 核 track、allowed_changes、quality、固定政策、数据／初态／配置等绑定。本计划第24、33、37行延续这些合同，不隐式推进 baseline。真实语义仍须独立 oracle 证明。|
|投递不换身份，unknown 先对账|`reference_training_submission.py:28–32,103–152,170–226,267–270` 保存原意图、attempt、memo、receipt，attempt 后恢复只 lookup/history；原 `perf_temporal/client.py:36–43` 拒绝重复 workflow 且不重试整个训练。计划第10、25–26行与此一致。|
|测量完成、门禁、人工批准与 workflow 完成分开|原 `workflow.py:132–177` 先 gate，再进入 `AWAITING_RELEASE`，收到明确 release 后才创建集成任务；`reference_training_runtime.py:11–62` 核完整初始 Experiment／精确 run 并区分实时 phase 与终态；`reference_training_evidence.py:31–39,44–92` 只验证保存的原归档。本计划第18、56行准确描述缺口，没有用离线报告或 Temporal COMPLETED 代替测量成功。|
|不得自动批准或借清理破坏人工 release|`training.py:133–150,258–277` 要求明确确认；原 `LocalTrainingAdapter.authorize_release_and_create_task` 在 `training.py:177–205` 重核 gate／receipt／baseline／fence。循环正常结束不能对先前成功实验统一写 fence；原实现第202行会因此抑制其 release。计划第18行已明确保留独立窗口。|
|跨轮与恢复预算，取消投递和实际停止分别报告|`reference_budget.py:33–37,71–79,112–128` 的 scope／slots 属单个六阶段 task，时钟恢复还有同 host／boot 限制（第91–102行）；原 `models.py:23–44` 的 max_run_seconds 只是单实验确认后的排队加运行窗口。计划第15、25、35行没有把两者误当训练循环授权。`reference_training_cancellation.py:179–200` 也确实把控制面、executor 和 fence 分开。|

子节点顺序合理：a 先证明有限选择与冻结输入可执行，b 先打通原提交与全生命周期停止，c 再开放 Temporal 顺序控制，d 最后验安装后的实际 CPU 旅程。不得把 a 的本地只读成功升级为服务可达、把 b 的 fence 存在升级为 OS 停止，或把 d 的合成门禁升级为 B3／GPU／训练质量与收益。

## 最先要落实的具体接缝

### 1. Q4.2a：复用原提交准入，补总容量与运行位置边界

`training.inspect`（`training.py:64–73`）只观察原记录；`training.submission` 的 status 在无 intent 时只读 records（`reference_training_submission.py:120–126,229–233`）。两者均不等价于 `_Submission.preflight` 第51–78行的完整准入：当前 baseline／runner、已有原 job／fence／negative result、runner walltime、Git root／完整 commit、比较器字节及冻结观察。准备阶段的 preview 也不是已准备实验的 start 准入（`reference_training_preparation.py:66–98,151–162`），其入口当前需要可选 SDK（`reference.py:374–379`）。

若 a 需要独立只读 start 检查，最小扩展应留在 `training`／`reference_training_submission`，直接复用原 preflight 和 load/status，真实消费者是有限选择准备与 CLI；不必新建校验器或转发模块。应显式保留 prepared／unknown／submitted／rejected 等投递事实，不把离线通过当成服务无旧 run 或允许发送。实际 start 的两次最终 preflight（第182–184行）仍须保留；事前检查不能消除漂移或并发。

**建议给计划第24、26行补一项明确验收：有限选择的总字节容量、Temporal 传输／history 预算和 worker 对原存储的可达范围。** 原 manifest 单件最多1 MiB（原 `LocalTrainingAdapter.read_manifest` 第107–113行），单 start 聚合 intent 可达16 MiB（`reference_training_submission.py:20,251–257`）；已有 `test_training_submission.py:124–141` 明确保护合法单件产生超过1 MiB的聚合 intent。原 Q4.1 索引还有32轮／10 MB上限（`training_rounds.py:15,131–132,153–154`）。因此“有限”本身不保证最终完整索引或 Temporal 输入能容纳，不能直接将所有原观察全量塞入 workflow input／每次轮询，也不能到已执行多轮后才发现无法保留完整结果。

实施前应固定真实部署支持的 payload／history 上限，选择有摘要核对的不可变引用或明确受限的内嵌值，核原索引容量，并在超限时完整拒绝或按已定义边界停止，不能截断。引用每次消费都核完整 SHA；裸绝对路径不是冻结身份。当前 manifest 为本地 `file:` URI，原 registry 用本地 `flock`（原 `training.py:28–33,97–101,107–113`），连接环境又绑定本地服务（`core.py:69–76`）。首版可明确仅支持原运行环境及其存储；异 worker／host 缺少原存储必须可见失败，不据 Temporal 的跨 worker 恢复能力推断文件与锁可共享。这里没有验证任何部署的具体服务容量数值，也不预设另一套存储系统。

### 2. Q4.2b：先验证原 fence，再谈父级取消或 deadline

现有应用取消要求原 start 已为 submitted，且必须有精确 run ID（`training.py:159–165`；`reference_training_cancellation.py:23–30`），因此确实不能直接覆盖尚无 run ID 的开始窗口。原 `LocalTrainingAdapter.create_job_if_absent` 第137–144行和 `fence_and_lookup` 第167–171行使用同一个 `registry_lock`：后者在锁内**先 lookup 再写 full-binding fence**。并发保障来自同锁，不是无锁先写后查。原 `Activities.cancel_exact_job` 第76–83行已把 fence、精确 job 查找和取消串接起来。

最小方向是在原应用取消／提交 owner 显式暴露绑定原 start 意图与 Experiment 的提交前停止能力，保留本域 intent／身份／恢复；循环不直接拼路径写 fence。必须验证三种顺序：fence 先于创建、创建先于 fence、最后一次 preflight 之后 RPC 才到达。前两者由原锁提供接缝；第三者仍可能产生晚到的 Temporal run，不能因没有 job 就宣称 workflow 不存在或控制面已取消。保留原 memo／完整初始输入／run 对账，未确认则报告 unknown／cleanup-unconfirmed，禁止下一轮和重发。

验收应让实际原提交接缝停在上述交错位置，覆盖 lost-ack／恢复；同一原 attempt 不应因 activity 重试或重启再次消耗试次或获得新额度。还须覆盖 deadline／owner cancel 与 `AWAITING_RELEASE` 同时出现：清理活动中的执行和 unknown，不误 fence 已完成测量且保留人工 release 的先前轮。单独取消 worker future 不能证明任何这些结果。

### 3. Q4.2b／c：明确谁启动 CPU executor，并覆盖其全部生命周期

原 start 只提交 `ExperimentWorkflow`；adapter 创建 `request.json`，没有启动训练进程（原 `training.py:123–144`）。本地执行入口仍是显式 `run-local`，先核 manifest，再调用 `training_executor.process`（同文件第243–250行）。因此 c 仅顺序调用当前 start／status 用例时，CPU 轮次会停在 QUEUED；d 的一键旅程还需明确哪一个应用／进程 owner 调用这个既有执行入口，不能默默假定原 worker 已自动执行它。原训练 worker 目前只注册 `ExperimentWorkflow` 和五个原 activities（原 `worker.py:9–16`；`activities.py:102–104`），新增应用工作流还须明确实际注册与 task queue 路由，保持冻结 worker 原件不变。

训练 executor 的 Git clone／worktree 在 Sandbox 前，归档和 MLflow 跟踪在 runner 后（`training_executor.py:66–118`）。runner timeout 与 process fence 只直接覆盖相应 Sandbox 进程（`process_job.py:95–122`）；`Sandbox.run` 还会独立启动 monitor session（`sandbox.py:57–69`）。杀掉外层 activity／调用进程不能自动证明后代已停，fence 也不能凭存在就证明处于 Git／跟踪阶段的 executor 已结束。b 应把准备、两臂 checkout、runner、归档、跟踪和恢复观察都列入原预算／资源验收；最小修正放原应用进程／执行入口，不新增循环专用训练器。

预算不能改写已冻结的 Experiment 来迁就短样例。原 `models.py:33–44` 对 poll、run、release、cancel 窗口有真实支持范围；原 control activity 又有每次30秒、总3分钟和最多3次尝试（`workflow.py:15–20,64–70`）。a／b 必须说明哪些预算组合可执行，如何在剩余时间内限制控制调用并保留 cleanup reserve，超出原能力时明确拒绝或保留未确认结果，不能用默认数字的测试替代这些关系。

### 4. Q4.2b：注册漂移恢复不能走“取当前项目”的捷径

当前 `training.status` 先 inspect 当前注册／spec，再取当前项目（第83–89行）；cancel／resume 又调用当前 `_project` 并核 expected revision（第233–255行）。`_Submission` 身份含 registration SHA／execution（第28–32行），`_TrainingProject.registration` 还会核当前注册文件（第41–47行）。所以只保存旧 revision 或把它传入现有公开入口，不能自行得到“冻结上下文仍可观察／停止”的能力。

计划第57行抓到了这个真实接缝。实现须在原 owner 区分：旧运行的绑定观察／停止可以用原冻结上下文，任何新派发仍须当前准入。不能通过删掉 registration 检查或全部改成旧配置来解锁新启动。验收应改变实际项目 revision、registration／execution，再证明旧 run 的完整初始输入、memo、精确 ID、原取消记录与原存储不分叉，新轮拒绝。现有 submission 测试第168–177行只证明 baseline 改变／runner 删除后的原 attempt 对账，不能外推为注册或执行位置漂移已经验收。

### 5. Q4.2c：先核原分类可读范围，再确定停止原因

实时 `Status` 提供 phase／binding／job／evidence SHA（原 `models.py:107–113`），原 accepted archive 读者能核 gate、evidence、manifest、baseline 和 comparator 的对应关系（`reference_training_evidence.py:44–92`）。c 应以精确 submitted run／完整原始 Experiment 的实时测量事实，加同一 evidence SHA 的原 accepted archive 作为继续依据；多轮离线索引的 coverage 明确不查询运行、不评价授权（`training_rounds.py:17–19,46–49`），不能替代该判断。

原 executor 会把缺 evidence 或 archive/gate 失败汇成 `passed=false` 与摘要（`training_executor.py:89–113`），原 workflow 最终同为 `GATE_FAILED`。结构化质量先在 `perfctl.gate` 第112–133行检查，性能比较在第134–160行；目前不能仅从高层 bool 准确断言是哪种失败。计划第37、58行要求先核原报告、无法区分则报告缺口，这是正确边界。需要更细分类时，先在原证据／gate owner 暴露已存在的可信分类或最小缺口，不让控制工作流解析自由文本或重写评分逻辑。

原 comparator 明确区分 PASS／FAIL／INCONCLUSIVE（`compare_runs.py:164–188,217–228`），同时声明固定样本筛选不提供 optional-stopping／多次搜索校正（第180–184行）。循环可据预定条件停止与保存这些原结论，不能把多轮挑选出的通过结果升级为新的累计显著收益或质量批准。d 应同时保留无收益、区间交叠／缺证据、质量失败和无法细分的结果，不靠重新统计改变原门禁。

## 已做检查与未验边界

- 已读根及源码／测试入口规则、组件变更协议、maintainable-project-delivery 及独立 brief、ergora-codebase-quality 的风格／模块／测试接缝参考；读当前检查点、Q总计划、Q4.1／测量合同计划及相关交付范围。
- 完整读取本次两份计划／交付和 `training.py`、`training_rounds.py`、submission／runtime／evidence／cancellation／context／budget owner、原 Temporal worker／workflow／models／activities；针对调用路径读取 `reference.py` 训练相关函数、preparation、原 local training／executor／process／Sandbox、连接环境及应用 worker 路由。源码行号均相对固定基线；未声称审完这些邻接模块的无关功能。
- 只读检查原 submission、runtime、cancellation、evidence 测试及相应服务替身的相关接缝。它们支持选择下一片回归位置；本评审没有运行这些测试，也没有把历史通过外推为 Q4.2 的取消竞态、跨恢复预算或真实服务验收。
- 对两份待审文档核5个本地文件链接，缺失0；收尾 SHA 与首次读取相同。加入本报告后共3份文档／8个本地文件链接，缺失0、行尾空白0。训练源码身份以本文固定 Git 基线为准；最终出现的三份后继源码改动已单列排除。
- 未调用模型、Temporal／MLflow／外部平台，未运行训练、GPU、profiler 或全量测试，未安装、提交或推送。未重新认证 Q4.1／B2 的发布、私有原件或 CI；未验证实际 Temporal 容量、不同 worker 的存储可达性、native fence 并发行为及 OS 后代停止。

下一步可先在原 submission owner 完成只读 start 准入的小片，并将容量／存储限制固定进 Q4.2a；随后以原取消 owner 的提交前 fence 和全生命周期 executor 停止为 Q4.2b 的硬门槛。Q4.2c／d 仍须各自实际证据、新安装身份和新的独立实现评审，当前计划评审不替代它们。

## 同片计划修订复核

日期：2026-11-15；仍由本 fresh-context 计划 reviewer 进行同片复核。本节只追加记录，保留此前16,763字节及其 SHA-256 `9bfeaf41ed6a55e880c56bc8886823088667f1679b6355fa3575060ac31c2566` 的原报告前缀。初版两份文档的 SHA 与当时结论也保留，不以后续文档覆盖历史身份。

本次完整重读的修订文档：

|文件|本次 SHA-256|
|---|---|
|[Q4.2计划](../plans/2026-11-15-bounded-training-cycles.md)|`73fe4e10637b99de6261abc6463291c018bd3166ede42bd47a5b8af9246c68b9`|
|[Q4.2交付](2026-11-15-bounded-training-cycles.md)|`ecf90ab8c05219ac34bf3e4f77c48cf0caec6e1b545f4af1c7f2d5d80a3f7502`|

**修订复核：需求符合性 approve／可维护性 approve，均仅为计划层面；新增阻塞 finding 0。** 初版建议已成为相应子节点的显式验收前提，没有把调查义务或本次审查意见写成已实现能力：

- 计划第24行先拆 Q4.2a1 原 owner 只读启动检查，再做 a2 有限选择与预算冻结；其链接的[准入子片合同](../plans/2026-11-15-training-start-admission.md)第7–11、22–24行明确无服务查询、不能替代最终 start 检查、实现片另需新 reviewer。本次只用该文档核职责和审查边界，不认证其中接口的实现、测试或可用性。
- 第64行纳入总字节、真实部署 payload／history 限额、原索引32轮／10 MB的完整保存策略、消费时核完整 SHA 和本地文件／锁可达范围；对超限和异 worker／host 缺存储要求可见处理，没有发明已验证的服务容量或分布式存储能力。这回应了“有限选择仍可能无法完整传输／保存”的接缝；实际限额及停止策略仍待 a2 证明。
- 第65–66行明确同锁 lookup／fence 与创建、最后一次 preflight 之后的晚到 RPC、无 job 不代表无 workflow，并把原 run-local 的启动责任和从 Git 准备到归档／跟踪的 executor 生命周期纳入验收。第43、48行流程图将清理对象限定为未完成活动轮，成功测量保留独立人工 release；未要求对先前成功轮统一写 fence。
- 第67–68行保留原 Experiment／control activity 的真实范围，要求先证预算可执行；注册漂移以真实配置变化验证旧运行观察／停止与新派发的分离，没有通过删除注册检查扩大授权。
- 第69行保留 PASS／FAIL／INCONCLUSIVE 及无法细分的原门禁失败，明确不提供多次搜索／optional-stopping校正，不把挑选出的多轮通过结果称为累计显著收益。第37、55–58行的证据分类／绑定及取消问题仍明确未解决。
- 交付第10–11行区分计划评审与后继 a1 的开始状态，有限选择、前置停止和自动控制仍标为未实现；没有借 a1 或前片 CI 关闭 Q4.2b–d 或 B3／GPU／完整 Forge。

本次核两份修订文档的8个本地文件链接，缺失0，并从原固定 Git 基线复核容量、同锁 fence 和统计限制的五处源码锚点。源码基线仍为 `96b4bb5454714a73e1d5f60b880a479c195e5269`；共享 HEAD 为 `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`。没有检查或认证新的 training-start-admission 产品差异与测试，没有运行模型、训练、服务、测试或安装，也未提交、推送。

本次关闭的是计划表述的补充核对。全周期预算／停止、晚到提交、注册漂移恢复、真实证据绑定、实际服务容量及 CPU 旅程仍要在各自实施片提供证据，并由其新的独立实现 reviewer 验收。
