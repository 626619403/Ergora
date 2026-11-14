# Q4.2a2 有限训练选择：独立设计复核

日期：2026-11-15。评审者：Codex，原 Q4.2 计划 reviewer。按后续明确范围，本次另写此报告，不追加或修改原 Q4.2 评审报告。

## 范围与结论

完整读取[待审 a2 计划](../plans/2026-11-15-training-cycle-selection.md)，SHA-256：`7bee340a6230c5eb30996f6526c902ba44d5683b2240e151e5b4bcd3a822c16b`。用于了解依赖合同的 [a1 计划](../plans/2026-11-15-training-start-admission.md) 读取时 SHA-256：`3f1f01d76b6952943322a3e257a79aa0e5891cab0045143df8ac94c6a2f0ce95`；收尾时该邻接文档已另有更新，不纳入本次 a2 快照。a1 的实现、安装、测试及审查状态均不属于本次认证。

原训练源码以固定 Git `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9` 的 `git show` 为准，排除共享工作树 a1 新实现。下文应用模块位于 `src/ergora/`；原 Temporal 模块位于 `src/ergora/data/reference/platform/upstream/temporal/perf_temporal/`；原 executor／core／Sandbox 位于 `src/ergora/data/reference/platform/local/agent_platform/`。

|评审轴|结论|
|---|---|
|需求符合性|设计方向 approve；1–32个明确候选、预算策略与执行授权分开、原结果 owner 与离线边界合理。S1 仍需定稿下述 timeout 语义和完整冻结关系，不能据此宣称预算已可执行。|
|可维护性|设计方向 approve；沿原准入组合、单个不可变输入、薄 CLI 和原发布／读取能力，不需要新增预算时钟、运行表、冗余试次数或通用调度／存储框架。|

未发现需要否定该设计方向的实证问题；尚待 S1 定稿的合同不是已实现产品缺陷。第11、19、31、37行正确保留了授权起算、具体预算组合及 b 执行边界的未完成状态。本次提供的最小关系可用于完成 S1，不能替代后续实现评审。

## 预算策略的最小合同

建议策略只保留 `wall_seconds=W`、`cleanup_seconds=C`、`control_timeout_seconds=T` 三个变项，均为严格整数，排除 bool／小数。候选数 `N=len(candidates)`，要求 `1≤N≤32`、experiment ID 唯一且顺序固定；最大训练试次直接由这份列表推导，不另存可独立变化的计数参数。控制 activity 的重试与同一原 start 的对账不是新的训练试次。

准备阶段可以独立判定的最小关系为：

|关系|含义与限制|
|---|---|
|`1≤C<W`|清理时间包含在总墙钟内，工作窗口为 `W−C`，不是另加一份 `C`。正整数条件已使两窗口均至少有1秒。|
|`1≤T≤60`|与原 training status／submission／cancellation／stop-status 的 timeout 支持范围一致（`training.py:79–80,179–180,211–212,237–238`）。|
|`T` 是传给原用例 timeout 的上限|后续 b／c 可以按原 deadline 的剩余阶段预算缩小 timeout，或拒绝启动该调用。不要把 `T` 写成整个用例的严格墙钟上界。|
|a2 不创建时间实例|不保存授权起算、deadline、已用试次、当前轮、自动恢复状态或执行许可。显式启动才由原应用／Temporal 生命周期一次创建总 deadline 和工作截止点，恢复保留它们；a2 不调用单 task 的 `reference_budget.authorize`。|

采用“上限且允许缩小”的语义时，没有必要因 `T>W−C` 或 `T>C` 就在 a2 禁止一切策略；执行时可缩小或不调用。若决定 `T` 固定且绝不缩小，则至少还需 `T≤min(C,W−C)`，但这仍不能证明完整调用或停止能装入窗口。建议使用上限语义，并在 a2 结果中只表示策略已冻结，不能标成可执行循环已经准入。

不应要求 `W≥sum(max_run_seconds)`：有限选择允许有效提前停止，每个 max_run 也是上限。也不应要求 `T≥180`：180秒属于原子工作流内部 activity 的 schedule-to-close，和应用进程／RPC timeout 不是同一层。原 task 预算的604800秒／258次模型调用限额还绑定 task scope 和 slots（`reference_budget.py:22–37,112–128`），不能不加说明移成训练循环合同。a2 若另选首版支持上限，应写明其产品支持理由及真实消费者，而不是为短示例或旧测试收窄合法配置。

### 为什么停止保证必须留在 b

原 `training.start` 和 `cancel` 都先本地 prepare，再进入第二个 dispatch／resume 进程（`training.py:214–230,240–255`）。`status` 又先 inspect；该记录读取进程有独立30秒 timeout（`training.py:83–89`；`reference.py:336–353`）。每次 `_training_process` 的外层调用还使用 `timeout+5`（`reference.py:425–430`）。所以把 `T` 传进这些入口，并不意味着整次调用只花 `T`；即使两个内部进程各自受 `T+5` 约束，也还有安装核验、锁等待和进程清理义务，不能把两项相加后当成已经证明的全用例上界。

原 control activity 的 start-to-close 为30秒、schedule-to-close 为180秒，最多3次尝试（原 `workflow.py:15–20,64–70`）。取消要等在途控制调用返回，再调用 fence／cancel；`cancel_wait_seconds` 从这次调用返回后才起算（第79–90行）。确认循环先 poll，再无条件 sleep poll_seconds（第89–97行）；最后一次 poll 和 sleep 都可能跨过 cancel_wait 截止。因而 `C≥cancel_wait`、甚至简单的 `C≥180+cancel_wait` 均不是所有时序的停止证明。

原 Experiment 的 poll 30–300、max_run 60–86400、release_wait 60–604800、cancel_wait 30–3600 仍由原 spec 验证（`models.py:33–44`）。a2 只保存并核这些原关系，不修改 spec、不增加另一套 poll 或 retry 参数。b 应选择实际停止路径后，再证明完整用例／原 workflow 等待／executor 清理能怎样消费 `C`；不足或服务不可达就保留 cleanup-unconfirmed 并停止派发。有限的 `C` 不能保证失联服务最终确认。

executor 的 Git clone／两臂 worktree 在 runner 前，归档有独立600秒窗口，MLflow 跟踪在其后（`training_executor.py:67–118`）；原 Git helper 的单次 timeout 为120秒（`core.py:86–95`）。这些不都包含在 runner timeout 或 max_run 中，跟踪在此路径也没有可由 a2 直接相加的统一硬上界。因此 a2 能验证的是策略与原输入的一致性；b 才能验证 deadline 前不再派发、调用及后代停止、晚到 RPC、恢复不续期和预算不足时的真实终态。没有这份证明时，即使 a2 准备成功也必须拒绝自动执行。

## 完整冻结：S1 应明确的最小关系

第7、18、21、32行已有正确方向，建议把实际保存内容与共享字段关系写清后再实现，不另造平行 preflight：

1. **一个原上下文。** 保存 control 目录、project ID／repo／revision、registration SHA、原注册定义与注册文件的预期内容、execution／原安装与存储位置；不复制凭据。这些是原 `_Submission.identity` 和 `_TrainingProject.registration` 的实际消费者（`reference_training_submission.py:28–32`；`reference_training_context.py:27–47`）。每个候选观察的项目／revision 均须与它一致，发布前再核当前项目身份。准备的原训练观察只通过 a1；若还需读取 State 的原项目快照以冻结注册，应在计划中明确这个本地只读步骤，不能假定 a1 的“完整观察”必然已经返回完整注册配置。
2. **逐个完整观察，不截断。** 每个请求 ID／完整 manifest SHA 与返回绑定一致，完整保存其原 manifest、Experiment spec、baseline、runner 和源文件 SHA；spec／binding／manifest URI／runner 的关系沿原 owner 及离线格式核验。原 `_training_records` 第484–501、511–527行已拥有单实验的这些关系；a2 不重复 Git、比较器或当前文件准入，更不能在离线 read 时再次读取它们。
3. **共享语义逐字段比较。** 初始 baseline ID／commit／base config／workload，以及 dataset／initial checkpoint／environment／validation contract／comparison tool／checks_required／quality_required／performance_policy 应由完整冻结值核对。candidate commit／candidate config、track／allowed_changes 按每候选原合同保留，不能为了表面“相同”改值或抹掉获准近似改动。机器相同的指纹不认证实际模型、数据或 oracle，仍须原可信流程证明。
4. **区分两种摘要。** 整份新 JSON 的原始文件 SHA、原 source 文件 SHA 和原 canonical JSON 身份保留各自语义。原文件 SHA 来自原字节（`reference.py:464–474`），完整观察通常是解析后的 JSON 值；重新序列化该值不一定还原原文件字节。离线读能证明新文件的期望 SHA、版本和内部关系，不能把重排 JSON 的摘要当成重算了原 source SHA 或认证来源。
5. **集合观察不是原子快照。** 逐个 check 与最终项目核对能够拒绝观察到的冲突；它们不预留实验，也不能证明所有外部文件在整个读取期间从未变化。第11行继续要求实际启动重新核当前原身份是必要边界。离线结果不得重新授予 a1 的 ready 许可，亦不得接管后来出现的 prepared／unknown 意图。

单个新领域输入 owner 隐藏上述持久格式、采集与交叉关系，有实际 CLI 消费理由；无需再加通用上下文包、预算实例、摘要包装器或替代组件族。严格 JSON／版本校验、普通文件检查及不覆盖发布优先使用原 `parse_json`、`contracts`、`asset_trees.publish_directory` 等能力。

## 容量、未来传输和结果留存

**a2 本身。** 第20行的10 MB应固定为最终完整序列化文件的 **10,000,000字节**，与 `training_rounds.MAX_INDEX_BYTES` 和普通资产总容量一致（`training_rounds.py:15,152–154`；`asset_trees.py:41–44`），不是字符数或10 MiB。包含所有 metadata／注册／候选完整观察后再判容量，超限不发布，不用截断或只存摘要冒充完整冻结。新目录、普通单文件、严格 JSON、实际原始文件 SHA 和无覆盖发布足够；不能把原提交16 MiB聚合意图的读取限额误当新输入可承诺的容量。

**未来 Temporal 传输。** 第22行应明确“小引用＋SHA”同时覆盖 workflow／activity **输入、返回值和异常信息**，不是只缩小启动参数。原 evidence 响应上限8 MiB（`reference_training_evidence.py:38,135`），完整选择可10,000,000字节；activity 若直接返回这些正文，仍会产生大 history blob。未来应在原 owner 本地读取／验证全文，只返回受限的精确 run／binding／evidence SHA、状态／覆盖事实和有完整 SHA 的不可变快照引用。引用也要绑定原 control／项目／registration／execution 范围，消费时重新核内容，不能凭路径相同就相信旧文件。

固定 defaults 原件 `constants.go` 的 SHA-256 为 `3fdabe4ec1649bd11b473966e522be18905a6394f1255fd4580b369353e1dd67`，与随附 request 记录一致；其第387–395行确为 blob error 2 MiB／warn 512 KiB，第431–455行为 history error 50 MiB／51200事件、warn 10 MiB／10240事件。计划第25行正确称它们为所给 Server 1.32.0 源码默认值，未称当前服务实测限额。本评审只核本地捕获源文件，没有重新联网或运行 CLI／服务，也不独立认证 CLI 内嵌版本映射。

c 前仍须按实际受支持部署验证真实编码后的请求／响应与 history 增长。限制为32轮不能单独约束长等待或频繁轮询产生的事件数；c 应用原截止点与有界观察节奏推导其界限，不必为 a2 新增另一份试次或轮询计数器。服务大小默认值调查不授予执行准入。

**未来结果。** 第23行把结果容量另列为后继义务是正确的：准备输入不超过10 MB，不代表运行后原 evidence／归档／批准观察能装进同样大小的累计 rounds。原 `training_rounds.create` 会复制旧前缀再追加完整观察，最终才拒绝超限（第127–154行）；不能只在最后一轮调用它才发现整份结果无法发布。后继合同须同时覆盖单轮完整观察过大、累计过大、快照发布失败：先保留原结果及原件、记录明确未保存／未读取覆盖，停止下一轮；不得通过丢失败轮、重算统计或改原索引格式硬塞。每轮快照及受限引用可以是最小结果链接方案，但应由原结果 owner 定义、实际验证，不在 a2 预建第二实验存储系统。

## 检查与未验范围

本次只读两份设计文档、固定原训练源码及所给容量调查原件；待审计划的两个本地文件链接均存在。未读取或认证 a1 产品差异、安装件／日志／测试结果；未运行模型、训练、服务、测试或安装，未提交、推送或外部写入。原 [Q4.2计划评审报告](2026-11-15-bounded-training-cycles-plan-review.md) 全文保持 SHA-256 `1c1b185d5ced949a52ce7abfce9ffd8a559f62cb94ecb2979a21dab456e47cf3`（20,318字节）。

最小下一步是把三字段预算及 timeout 上限语义、注册快照来源、字节上限和 future activity 输出边界写入 S1；a2 仍只交付完整不可变选择。严格执行预算与停止证明留给 b，实际传输／history与完整结果旅程留给 c／d，各自的新实现 reviewer 不继承本次设计结论。

## 2026-11-15 同切片修订设计复审（追加）

本节复审完整重读后的 [a2 修订计划](../plans/2026-11-15-training-cycle-selection.md)，SHA-256：`b79531b5ccdbc89b07f534240513d6fa22419a392b45b55c1e32e50e48206c63`（39行）。[a2 交付记录](2026-11-15-training-cycle-selection.md) 读取时 SHA-256：`d0214ddec8275f35be55865293c7429d029ba51680ed59c8dc284eb87880dbf4`；只用它确认设计复审和实现／验证的范围分离，不认证其中实现、6项测试或耗时陈述。本节之前的13,356字节原文保持不变，其 SHA-256 为 `ed87836fd08c7f604d89d216dc681fdf4d90a4b113b072a0c71e9fdc1d43df99`；原始计划快照、发现及当时结论仍按上文保留。

新版第3行把已发布的 a1 `d3c90e751ee9257df36b74e57e8956d38bbde848` 明定为后续实现基线，并保留 a1 自身 CI 完成后才允许后继推送的门禁。本节补核原 owner 事实也只使用该固定 Git 对象的 `git show`；不读取当前 a2 产品／测试工作树，不转认 a1 的实现审查或 CI 结论。

|评审轴|修订设计结论|
|---|---|
|需求符合性|approve。此前待 S1 明确的预算语义、完整冻结来源、字节容量和未来双向传输边界已在计划中写明；没有新增阻塞设计项。|
|可维护性|approve。一个 `training_cycles` owner、单个不可变 `cycle.json` 和实际 CLI 消费者的边界清楚；未来 Temporal 消费者未被算作当前复用，也没有引入平行预算时钟、运行状态或调度／存储框架。|

以上均为设计批准，不是当前实现、测试、安装、CI、执行准入、原生 owner 审批或业务质量认证。a1 的审查结论不能转移到 a2；新的 a2 实现 reviewer 仍须独立检查实际差异。

### 原设计建议的处理

|计划位置|复核结果|
|---|---|
|第7、21、37行：注册及完整冻结|明确从原 State 取得完整项目／revision／注册定义与预期注册文件，训练观察只走原 `training.check_start`，离线 read 只读冻结文件。control／project／registration／execution 范围、候选 revision／binding／spec URI／runner 及共享字段均须在文件内关联；原 source SHA、重排 JSON 与整份 cycle 原始字节 SHA 分开。逐次观察未被称为原子外部快照。|
|第11、17–19行：三字段策略|严格整数 `W/C/T`、`1≤C<W`、`1≤T≤60`、1–32个唯一且有序候选及由其推导试次上限均已定稿。`T` 是原 timeout 的传入上限，执行时按剩余阶段预算缩小或拒绝调用；不宣称它约束完整用例墙钟。未迁移 task 七天／模型调用上限，未要求各次 max_run 之和装入 W，也未用 C／cancel_wait 或 T／180 的静态关系冒充停止证明。授权时才创建原截止点，恢复不续期；策略有效不等于执行准入。|
|第20行：完整文件容量|最终完整 UTF-8 `cycle.json` 限额固定为10,000,000字节，并采用原严格 JSON 的64层／100000值边界；超限在发布前拒绝，不截断、不覆盖。容量覆盖完整项目和所有观察，未以摘要替代冻结内容。|
|第22、25行：未来传输|受限引用同时覆盖 workflow／activity 输入、输出及异常。全文核验留在本地原 owner，仅传精确 run／binding／evidence SHA、状态／覆盖及 SHA 绑定快照；真实双向编码、history 和 worker 验收继续留给 c。所给 Temporal 数值仍被限定为源码版本默认值，没有升级成部署实测或执行准入。|
|第23行：结果留存|保留原32轮／10,000,000字节限制，明确未来单轮或累计超限、快照发布失败时保留原结果并停止后继派发；没有改原格式或用删轮／重算统计解决容量。|
|第39行：后继责任|b 继续承担启动前停止、晚到 RPC、注册漂移后的停止、完整 executor 与恢复预算；不能仅凭 manifest 一致接管后来由人或另一 cycle 发起的意图，原意图还须属于本次授权。c／d／B3 未被本次准备成功或设计批准提前关闭。|

第9行把 CLI 明确为当前消费者，第31–35行也把本次修订设计复审、实现审查、已述测试、安装旅程及发布状态分开，未借本报告补齐尚未完成的证据。

### 固定源码事实与未验范围

本次针对修订补核 `d3c90e751ee9257df36b74e57e8956d38bbde848` 的原能力：`definition_bundles.py:30–63` 已提供重复键／非有限数处理及64层／100000值的树边界，后者由 `parse_json(..., bounded=True)` 显式启用。设计可沿用该合同；当前实现是否实际启用并完整使用，须由实现 reviewer 核验。`registrations.py:99–115` 的 canonical 注册摘要、预期文件、marker 的 `control_home`／`definition_sha256` 及 State 中的项目 revision／注册快照，支持第7、37行所述来源和内部关联，不赋予该顺序读取原子性。

同时核对原 `training_rounds.py:15,132` 的10,000,000字节／32轮、`asset_trees.py:43` 的10,000,000字节总容量、原 Temporal `workflow.py:67–68` 的30秒／180秒，以及 `reference_training_evidence.py:38` 的16 MiB artifact／8 MiB response 限额仍在固定基线中。它们与本节设计判断一致，不能替代未来执行和传输验收。上文基于所给 `constants.go` 的默认值调查不变，本次未重新联网或运行服务。

本次没有读取或认证当前 `training_cycles`／schema／CLI 实现与测试差异，没有运行模型、训练、测试、安装或服务；未提交、推送或外部写入。只追加本报告，并静态检查引用、空白、原前缀及旧 Q4.2 报告完整性。原 [Q4.2报告](2026-11-15-bounded-training-cycles-plan-review.md) 仍保持20,318字节及 SHA-256 `1c1b185d5ced949a52ce7abfce9ffd8a559f62cb94ecb2979a21dab456e47cf3`。
