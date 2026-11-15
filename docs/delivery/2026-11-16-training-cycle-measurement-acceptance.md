# c1d M2a＋M3a：内部测量接受与轮次发布

2026-11-16。状态：具体[计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)及R1修订已由[fresh独立设计审查](2026-11-16-training-cycle-measurement-acceptance-design-review.md)接纳，需求与维护性两轴approve、开放0。根任务接纳B分片：现有operation-v2内部collect／reconcile用例，M2四事实和M3索引／完整观察由同片闭合实际consumer；M5仅必要只读binding格式提前，SDK v3注册／正式V2及执行开放不提前。

已审计划SHA256 `2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`，独立设计报告SHA256 `6feca847785ed8bc7a7ceb496d8be52b5c3282d60cb842c0ad02e63caa94eb48`。原首审R1 request-changes保留：reader完整返回在prefix前失败可能丢失；修订要求实际H逐份写／flush原 `helper/stderr.txt`，不把reason／原chain说成完整RPC detail，不增加文件／ledger／授权，也不冒称flush durable。

实施基线 `23ad171bf8228bf80b070d6ad866f79d63986d56` 已含M1a与已验M1b固定产品，新的持久隔离分支为 `feat/training-cycle-measurement`。实现、源码检查、真实S/H与服务替身、安装、自身原模板、fresh源码审查、固定提交／发布分别待验；设计批准不代记实现通过。旧schema1／2、operation-v1与c1c命令、25来源、原ready／预算／stop／一次机会、六阶段保持。

超界父请求exact raw有界留存的[另案设计](../plans/2026-11-16-training-cycle-parent-request-retention.md)仍在审，不在未接纳时偷偷实现。全M1c、M5最后native／前驱gate、M6正式V2／v3及实际两轮仍开放，schema3执行拒绝和ordinal1门不解除；此片不认证训练／GPU质量或收益。

## 隔离实施接续，未冻源

worker／protocol／runtime的首轮核心接线已写入原隔离树：新两mode、原SDK scheduled-event／DataConverter的固定机会核验、H逐reader完整stderr留存、原rounds用例／完整prefix、同fd与目录链同步／同inode raw重读、完整观察及小投影。仍在开发，尚未冻结或交付；不能将以下阶段性结果继承给最后候选。

指定ignored `cycle-measurement-collect/source-r1`中`run-04`首个真实S/H正例**1 passed／10.35秒**：原archive reader和rounds.create/read，合成schema3完整stopped chain，原SDK protobuf／DataConverter与外部服务替身；collect accepted／durable后，attempt2 reconcile只读原索引、重采本次新观察，schema3的BudgetedStart.source仍明确拒绝。该正例不认证真实V2／native执行或训练。前`run-01..03`失败原件保留，分别涉及fixture的SDK ActivityType误用与archive fixture重排原native request raw导致链拒绝；修fixture，没有放宽产品校验。反例、M−1／M／M+1真实完整shape、最终冻结源码／安装／自身模板和fresh实施审查待验。

另案留存设计随后已复核R1／M1闭合、两轴approve／0，根接纳限定失败诊断语义，但本片仍不包含其实现；在实际新mode入口稳定后另片接线，避免未验能力混入本次范围。全M1c及后继执行门保持开放待验。

CI成本按原限制继续检查：前候选59b74ce自己的group5已成功，但整个job19分26秒、原限20分钟。新case须保留JUnit逐项耗时；若新增真实保护使原分组不再可容纳，沿已有分组调查另作最小平衡，不删生命周期保护、不增加job或放宽时限。当前实施代理不改CI，尚未根据推测预记新候选可在远端预算内通过。


## 子实施源码交接 r2：已冻结与定向检查，安装和独审另验

本节由隔离实施子任务追加，2026-11-16。产品与测试仍基于 `23ad171bf8228bf80b070d6ad866f79d63986d56`，分支 `feat/training-cycle-measurement`，未提交、合并或推送。正式内部用例已接到原 `_CycleOperation → S → H → _cycle_operation`；这里交付源码及定向证据，不把服务替身与合成 schema3 原链称为正式 V2、真实训练或 SDK 活动注册。根任务随后负责新包、原结构模板和 fresh 实施审查。

完整修改恰为七个既有文件：产品为 [worker](../../src/ergora/reference_training_worker.py)、[protocol](../../src/ergora/training_execution_protocol.py)、[runtime](../../src/ergora/reference_training_runtime.py)；测试为 [submission](../../tests/test_training_submission.py) 及其原 [cycle operations](../../tests/fixtures/training_cycle_operations.py)、[controller service](../../tests/fixtures/training_controller_service.py)、[archive](../../tests/fixtures/training_evidence_archive.py) fixtures。未修改 rounds/evidence 的公开合同、CI、依赖、包内参考资源或注册新 Workflow／活动。

worker 增加严格 operation-v2 的 collect-round／reconcile-round，读取原四事实、出生四项 measurement sources、原 owner 的25项 capability、所选安装、原项目及 pinned manifest 所指的283参考文件。原 runtime owner 用真实 SDK history stream／DataConverter 核固定父 original run、唯一 `candidate-<k>-collect`、完整请求和 attempt1；完整历史按8000 events／8 MiB界消费，错误或不完整即 unknown。collect 仅对确定性原目录调用原 rounds.create；reconcile 只读原目标，缺失、部分或损坏时不 create／repair。每个旧 prefix、原注释、manifest、previous_report 与相应原件逐项核对；同一 fd、目录链同步、重开同 inode／同 raw，再重采最终四事实，才可能形成内部 accepted／durable 投影。

R1 沿原 H stderr fd 逐份写完整有限 UTF-8 JSON＋LF 并 flush，先于下一 reader／index 操作；不经父65,536B缓冲或 H stdout，不把普通 flush 说成 durable。完整 observation 沿原 operation 固定路径，以包含末尾LF的单文件10,000,000B合计界写入、同步及实际重读；超界完整原件保留、无 ref／acceptance。新 stdout／完整 identity-bearing frame 的32,768B界及 capacity replacement 后的再次检查仅接新版本，旧 v1 语义保持。

### 冻结身份与 ref 绑定修正

原 r1 冻结包含781份 tracked src/tests 的原字节和执行位，manifest SHA256 `ae58dde741ffcdb95abf1c937e83e93a344208adb5f88d48957559100306e2b3`；完整 binary patch 为121,722B，SHA256 `1c99f9990d3129bbcc0f77b090ffc6bb12067268c6102ae31d653139c1d82b2a`。其新21项和必要兼容27项分别通过，见下表；这不能覆盖随后发现的 ref reader 缺口。

静态自核发现 facts.candidate 与完整 native／evidence 的重复身份缺少本地交叉约束。先用真实 H 已写 observation，在原固定路径写入完整、finite UTF-8＋LF、与新 ref SHA／bytes 自洽的篡改原件，只改 facts.candidate.manifest_sha256。`run-11` 证明修前真实 `read_round_observation` 没有拒绝，原反例 **1 failed／9.42秒**，finally 恢复原 raw；完整篡改 raw／ref 与原运行证据保留，没有只测一个 JSON serializer。

r2 在现有 protocol owner 交叉核 candidate experiment／manifest／revision 与完整 native.Job／evidence.Binding，并在同一真实 reader 反例中要求拒绝。另只清理新私有 `_round_state` 的两个未用形参，无额外上层 gate 或第二账本。r2 仍是相同七文件，完整 binary patch **123,427B**、SHA256 `08926a95aa9be4593bf0a79940cea59d464b20d08c4de536fe88343e1a5544eb`；781份 tracked source/tests 原字节／mode manifest SHA256 `fd93ec54aa84c6ae9bc356fbca7330c84d8d43b3cf780411101036e104495bbe`。r1→r2 新增三文件 delta SHA256 `40df083a7789532262fd3e7b80ecad3bf043b3039710e510b4dcf8be105f8d90`；两份原冻结树与原 patch 分别保留，未覆盖。完整 patch 的 reverse apply --check 与 changed Python AST 检查通过。

### 实际定向检查与证据范围

私有有界证据索引为 `cycle-measurement-collect/source-r1`；每轮保留独立 basetemp、完整 argv、有效环境、固定 source patch／manifest、完整 log、JUnit XML 和 exit／耗时。正式 pytest 使用开发 Python 3.11／SDK1.34，`-B`、`PYTHONDONTWRITEBYTECODE=1`、仅隔离 src 的 PYTHONPATH；不安装依赖、不启真实服务、模型或训练。

|源码身份／原件轮次|实际结果|准确范围|
|---|---|---|
|r1 `1c99f999`，run-09|21 passed／178.60秒|完整新增测量用例；不包含后来补的 ref 绑定拒绝|
|同 r1，run-10|27 passed／183.67秒|完整 evidence 14、schema3 出生／实际关闭3、原 parent binding、历史离线、legacy owner1／2、旧SDK request／observe和容量|
|同产品加 reader 反例，run-11|1 failed／9.42秒|修前真实路径／自洽SHA的篡改观察未被拒绝；原失败保留|
|r2 `08926a95`，run-12|21 passed／189.86秒|重跑全部受影响新测量链，含真实 ref reader 修后拒绝与原正例后续 reconcile|
|同 r2，run-13|18 passed／46.20秒|完整 evidence14、schema3 出生／实际执行关闭3和历史离线1；没有把其余9项旧r1行为检查称为r2重跑|

新增21项保留真实 S/H／reaper、fd／fsync／目录同步和 SDK event／codec，仅替换外部服务并构造原 schema3 source records。覆盖四事实交错、错 run／memo／namespace／job／archive SHA／Outcome URI、明确失败与低覆盖、preflight 与最终 index 漂移、每份大于1MiB完整 RPC detail 在后续 reader／create／read／fsync失败后的 stderr 留存、同 raw 换 inode、观察 fsync失败、真实 S 原 deadline 终止并保留实际已完成诊断、history 缺事件／错完整输入／重复／decode／8000 events／8 MiB界、丢 S 回复后的 existing-only reconcile、部分目标不 create、三候选内部 prefix 的最早一轮篡改、最终 source／stop 和目录逃逸拒绝。三轮内部 source 为合成原链，不是三个真实训练 run。

M−1／M／M+1 使用最终合法完整 observation，含多字节 UTF-8 与末尾 LF；只调合法外部 RPC detail，全部实际 BOOT／window／facts 保持，若采样浮点格式造成长度差异，后续仅用原 reconcile 对同一 index 反馈匹配，逐次原 raw／实际 budget／window 保留。M 内用同一个真实 reader 完整读取，超 M 保留完整 diagnostic、无 ref／acceptance。stdout／完整 frame 的32,767／32,768／32,769B也经真实新 S/H；完整 identity 和 stdout ref 包含在 frame 计算内。没有以合成超大 replacement 冒称现存可达漏洞。

阶段失败不覆盖：run-01..03 为已述 fixture／原 raw 漂移拒绝；run-05 为12通过／3失败的开发探索，期间发生源码编辑，明确不认证固定候选；run-06 的3通过／57.59秒曾稳定 reported budget projection，范围限该替身，随后已移除。run-08 和最终 r2 重跑均保留真实原时钟；旧阶段结果不能替代最终身份。

根报告旧 `package-r1` 仅做 build 和 core／SDK 安装身份核验：完整663产品文件、283参考及依赖通过；初662漏嵌套 AGENTS 的库存已在 `product-inventory-correction.json` 纠正，原848输入本已包含该文件，未改 wheel／source。该包仍含已知旧 ref 缺口，没有安装行为验收，不是修后包。根已为 r2 另建新 `package-r2`，报告 build／core+SDK663完整身份／283／依赖通过；其安装21＋27及自身原结构模板 Codex 仍在途，本子实施记录不预记通过。

新增测量21项本机整轮189.86秒，逐项耗时在JUnit／日志保留。原group5距20分钟限制已很近，需由根按实际CI成本另评原分组；本片未改job／时限，也未认证远端CI。schema3 BudgetedStart.source、validate_context／native callback、旧 start／request／adapter 及 ordinal1 执行仍关闭；未实现另案 parent-request 留存，未完成全部M1c、M5最后gate、M6正式V2／v3、真实两轮或训练质量。源码、安装、模板、fresh审查与最终发布分别记账；本片仍待根 fresh 实施审查，不能自行标记完整交付。

### r2 模板模型审查发现 P1，保持冻结待最小修正

根任务报告：基于新 r2 SDK 安装包，通过自身原结构模板实际调用 Codex，67.499秒返回 **request-changes**。完整 stdin 为900,065B，包含完整15文件与3份祖先资源，原件独立保留于 `cycle-measurement-collect/self-review-r2-codex/`。模型指出 P1：原 `training_rounds.create()` 内部再次读取 inspect／evidence／submission／approval；worker 现有逐份 retention 只覆盖其直接 reader，未覆盖 create 内部刚返回的新值。后续 reader 失败时该完整新值可能丢失，preflight 的旧观察不能替代。根静态核对 create 的42–64行，确认此路径实际可达。这是已知产品缺口，前述源码定向通过与安装身份核验均不能消除它，r2 不作最终行为验收或交付。

此时 run-12／13 已正常完成，结果如前表；r2 源码与原证据保持冻结。根另行启动的 installed21＋27 在本次追加时尚未由子任务收到最终结果，不能预记通过；即使通过，其范围也不能证明上述尚未覆盖的内部 reader 失败留存。fresh 实施审查、最终固定候选安装／原模板复查、远端CI与发布仍待完成，不把模型 request-changes 写成 approve。

待根明确解冻后，拟在原 rounds owner 添加默认关闭、只观察返回值的可选 callback，紧接每个真实内部 reader 返回后调用；worker 接原 retention，不包装或全局替换训练 reader，不改变旧调用者的数据、算法或公开结果。先保留原 create 编写真实反例，使内部 evidence 已返回后下一 submission／approval reader 抛错，证明完整新值留存缺失；修后要求完整 stderr 留存、unknown／null 且无新 prefix。预计仅在原 rounds owner、worker 及现有 submission／cycle fixture 范围最小修改。后继 r3 将另冻源、另建包与证据，不覆盖或继承 r2 身份。
