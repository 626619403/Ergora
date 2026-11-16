# c1d M2a＋M3a：内部测量接受与轮次发布

2026-11-16。当前状态：内部片实现／源码／安装／自身模板／fresh最终终核闭合，产品68ba793已普通导入c6cfafb；公开新联合候选及自己的CI另验。以下保留逐阶段原件与当时状态。

具体[计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)及R1修订已由[fresh独立设计审查](2026-11-16-training-cycle-measurement-acceptance-design-review.md)接纳，需求与维护性两轴approve、开放0。根任务接纳B分片：现有operation-v2内部collect／reconcile用例，M2四事实和M3索引／完整观察由同片闭合实际consumer；M5仅必要只读binding格式提前，SDK v3注册／正式V2及执行开放不提前。

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

## 子实施 r3：原 index 内部逐份留存修正与源码交接

根明确解冻后，先保留原 `training_rounds.create` 的实际控制流加入两项反例。隔离 H fixture 在原 reader 返回边界加入独特大诊断，仅在真实 create 调用栈内使后继 submission 或 approval reader 失败；没有以整个 create 替身证明内部留存。原 evidence reader 已返回，新的合法 detail 与 preflight 不同，每份完整返回 marker 为1,121,637B。`run-14` 在旧 r2 产品上 **2 failed／12.51秒**：先核 unknown、无 acceptance／prefix／目标索引及实际后继失败 marker，再因 `index.inspect` 留存缺失失败；两份新 evidence 完整值也均未出现于原 stderr，见 `capture-red-evidence.json`。失败原件与完整新值保留。

r3 只在原 [rounds owner](../../src/ergora/training_rounds.py) 添加 keyword-only、默认 None 的 `on_reader_return`，每次 inspect、evidence、submission 和实际调用的 approval 返回后立即通知，先于下一读端／处理。回调返回值不参与决策；回调异常直接退出，不继续发布。旧调用者不传 callback 时仍使用原数据、校验、编码、前缀与公开结果。原 worker 仅把 callback 接到已有 H stderr 完整写／flush，不全局包装产品训练 reader，不增加账本、持久格式、注册或授权。原正例进一步逐项核对四份实际留存值与最终 index.native 的完整值完全相等。

完整最终候选恰八个既有 src/tests 文件，在 r2 七文件外仅增加原 `training_rounds.py`，该 owner 本来就在 measurement sources 中。`implementation-r3.patch` 为129,722B、SHA256 `3e150ce906ba894fcd4842c3cc92a05303a979b4c18dd395ad4c3ec690288624`；781份 tracked src/tests 原字节／mode manifest SHA256 `275642485a116a1cac468f777a4c77652cacc20b0280fc4a52291d2e36a83b6a`。独立 `frozen-source-r3`、`freeze-r3.json` 和 r2→r3 delta 保留，delta SHA256 `541a8c894611204cfdeb8e0d3786627165942433b1d707a2c5e92addf6017912`，未覆盖 r1／r2。changed Python AST 和完整 patch reverse apply --check 通过。

|固定 r3 源码检查|实际结果|范围|
|---|---|---|
|run-15|23 passed／189.22秒|全部测量21项加上述真实 create 内部两反例；完整新 evidence 在两条原 stderr 均逐值相等留存，unknown／null且无新prefix；正例四内部返回与原index.native完全相等|
|run-16|14 passed／29.31秒|完整原 evidence／rounds 保护，含 callback 缺省的负观察、前缀、丢ack与离线读取；不称为其余旧27项重跑|

运行后重新核全部781份 src/tests raw／mode和完整patch，均与 r3 冻结相同；`src/ergora/data` diff为0，原 `reference.verify()` 为283 PASS、runtime_started false。`post-check-r3.json` 仅对 run-14／15／16 实际持存的33份完整进程身份查当前匹配，活匹配0；没有为未捕获进程补造身份或扩大为全系统收尾证明。两条反例完整返回／stderr 对照保留于 `capture-green-evidence.json`。未修改CI分组／job／时限；本机测量整轮成本不能替代远端CI预算验收。

补记根在 r3 解冻时报告的 r2 安装终态：新21项 **21 passed／303.71秒**（driver305.105秒），原兼容27项 **27 passed／349.92秒**（driver351.471秒）。该 r2 wheel SHA256 `fd8dbc471301fc7dc03b2e5ee26339048e88e3d0fed4bcfce2fa28eccbc25983`，`final-inputs-r2.json` 原848输入＋663产品／core与SDK全部同一。它们属于已知 P1 的旧 r2 身份，不能继承给 r3，也不能把原模型 request-changes 改写为通过。

本子实施的 r3 源码和定向检查已交接、保持冻结，未提交／合并／推送。根负责为新身份另建包、affected安装行为、真实自身原结构模板复查、fresh实施审查及最终固定提交／发布／自己的CI；这些尚未由本子任务验收。父请求 raw 留存、M5／M6、全M1c和真实两轮仍未混入，schema3及ordinal1执行门继续关闭。

## r3 独审最后读端 P1 与 r4 修正接续

新的 [fresh 源码审查](2026-11-16-training-cycle-measurement-acceptance-source-review.md)固定针对 r3：需求轴 request-changes／P1一项，维护性轴approve／0，原报告 SHA256 `0e006b4ae16110df73c759dbbf869f712cb513cf413118a1c9f31e57e42b32f9`。原字节另以 `source-review-r3-original.md` 保存在本片有界证据目录，后续报告追加复审不覆盖此身份。确定性缺口在最终 parent RPC 与最终原 rounds.read：其后没有完整本地来源／项目复核；final index reader 返回后只查 operation clock／父进程，读期间已持久可见的原 stop 仍可能形成 accepted／ready。已有 source-after-create 与第四次 sources 内的 stop 反例发生较早，不能保护这个窗口。根接纳并授权 r4 最小修正。

根报告的旧 r3 package 仅认证新包身份：wheel SHA256 `0271fdb0ad39d081c4b9cd1a655db2491c3c835cd1337d126fa1e155dddad667`，core／SDK663产品同一、283参考／依赖通过，`final-inputs-r3.json` 原848＋663保持，明确 installed_behavior_run=false／self_template_run=false。因已知P1，未重复启动该旧身份安装行为或自身模板；r3源码23＋14通过不能覆盖最后读端缺口。

真实反例保留原S/H、原parent Describe及原rounds.read，在它们真实返回后只用fixture marker阻塞。final index read期间，父通过原admission.request_stop写入并确认stop_visible／stop_durable；最后parent RPC期间，父分别改变所选descriptor原字节或原State项目revision，然后释放。首轮run-17中source／project已实际错误接受，但stop测试用了错误的观察键，原3失败／20.80秒不全作为有效产品反例。仅修测试键后，产品保持原r3，run-18 **3 failed／20.85秒**：三项均observed／accepted／readytrue，stop项已确认原stop持久；失败前核原index／observation字节保持。`final-gate-red-r3.json` 核run-18所有产品hash等冻结r3，并保留三份原reply及合法stop完整观察；没有用任意“最后瞬间”竞态或替换整个rounds owner构造漏洞。

r4 从原 `_round_gate` 局部提取 `_round_local_gate` 复用原完整authority、source、项目、candidate原绑定、所选安装／registration；在最后parent RPC及最后index reader均返回后，再完整调用本地复核。原work allowance、active与admission.check位于其本地I/O之后，此后才形成acceptance，不再新RPC／archive／index reader。不增owner、状态机、持久格式或执行权限。

r4仍恰八个既有修改文件，完整patch135,245B、SHA256 `0ccbc19e2da14e11eec2b4ff3fa55a55addbb35ad0a80cc6aa40ead40df0192c`；781份src/tests raw／mode manifest SHA256 `3a9fc2c097286fa5ba845f1942f616646c6b22b9a09b9f8e58b220aef3e04eb1`，r3→r4 delta SHA256 `2bfcce5d6e3d765da0c12b464771c132569c4dd4358e1652838b664b058dcc0b`。r4独立冻源原件、AST、完整patch reverse apply及whitespace通过，旧r1／2／3全部保留。此追加时run-20原evidence14已 **14 passed／28.85秒**，run-19全部测量26项仍在途；新包身份／安装、同reviewer复审、原模板及最终发布／CI另验，尚不预记闭合。

### r4 源码检查终态与交接

同一冻结 r4 的 run-19 已正常结束：全部测量 **26 passed／217.94秒**，含原21、新capture两项及最后阻塞读端三参数。run-20 的原 evidence **14 passed／28.85秒**。`final-gate-green-r4.json` 对三份实际最终reply核 unknown、无acceptance／prefix且readyfalse，原index和完整observation继续保留；其index SHA仍与原observation完整prefix匹配，stop参数的原stop_visible／stop_durable完整观察保留。测试实际先读出原index／observation字节，再改变条件并释放，随后逐字核不变，不删除、repair或重发。

运行后 `post-check-r4.json` 重核全部781 tracked src/tests字节／mode及完整patch，均保持冻结 `0ccbc19e`，无untracked产品／测试，`src/ergora/data` diff为0；`reference-r4.json` 原283参考验证PASS、runtime_started false。仅对run-17／18／19／20实际持存的49份完整进程marker身份核当前活匹配0，没有扩大为未捕获进程的收尾认证。当前无子任务pytest运行，源码继续冻结，不提交／合并／推送。

r4源码定向交接完成；新非editable包、安装affected行为、同reviewer对原P1的复审、真实自身原结构模板与最终候选固定／发布／准确CI由根另验。已知旧r3的独立request-changes保留到真实复审，不由实施者自行关闭。完整父请求留存、M5／M6、全M1c、正式V2／v3和真实两轮仍不在此源码范围，执行门保持关闭。

## 根协调的新非editable r4、完整输入与固定提交

准确r4 wheel SHA256 `4c130b24d69957eafc545cce355e7d8777376a9b7014ad63b5193745bd43558e`；新core／SDK环境各663完整产品文件与冻结源码／wheel逐字及执行位相同，283参考与依赖检查通过。仅package-root AGENTS不打包；嵌套参考AGENTS仍是产品资源。848源码／测试／示例／配置／CI输入和179份冻结测试／示例副本按各自原manifest保存。没有覆盖含已知缺口的r1／r2／r3包。

实际安装行为使用Python3.12的真实site-packages，`-I -B`、无PYTHONPATH，在冻结测试副本运行：

|同一r4安装检查|实际结果|范围|
|---|---|---|
|installed-measurement-r4|26 passed／339.646秒；driver340.735秒|全部新测量链、原reader回调、真实最后read／parent RPC三参数修后拒绝、原S/H／reaper与完整容量；服务替身／合成原chain，不认证正式V2或训练|
|installed-evidence-r4|14 passed／39.162秒；driver40.425秒|原evidence与round create/read默认callback缺省、正负／前缀／丢ack／离线协议|
|core-full-observation-r4|0退出／0.158秒|新core真实site-packages，`-I -S -B`，实际读完整H产物10,000,000B（多字节／LF）并核ref；未导入yaml/jsonschema/temporalio/ergora.state。只证明本reader，不是整个native callback无SDK|

Ergora自身原`refactoring-quality → ergora-structure-review@1.0.0`经新安装SDK实际使用Codex，**28.753秒approve**。16份完整文件615,352B、完整diff／三份原baseline及3份全部祖先资源进入955,349B原stdin，SHA256 `d96f8a52f31dd1977a62003563a478b432110212cffc137f857dca116341e315`；结果SHA256 `1928bb373199c47c39cc29560db27b531750664b08addb6b192fb6eb94e44874`。该模型为所供完整文字审查，没有workspace／独立运行，不认证CI／真实训练；原r2模型P1 request-changes保持。模型输入先于本节状态记账，原文本／资源／输入／输出保持，不因状态更新重跑模型。

根post-check实际核848输入、663完整产品和179测试／示例副本原字节／执行位不变；安装两组仅已捕获37份完整process marker身份当前活匹配0，未捕获身份不补造。源码49份身份的独立记录仍沿原source-r1/post-check-r4。新core实际读的10MB原件SHA256 `8b0ac1e5fa84cb1044ea0b44795cdf410fc04f508727465982126e5d34e5d63e`；它是run19原完整产物，不是另造JSON roundtrip。

准确产品固定提交`68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，唯一父23ad171，clean、恰八文件1551+/57-；其完整Git diff与原冻结135,245B patch0ccbc19e逐字同一。根原件在ignored `cycle-measurement-collect/package-r4`：build/install／每组完整argv／stdout／stderr／JUnit／result、core-full-observation-r4、final-inputs-r4、process-markers-r4与candidate-r4。自身模板完整原件另在self-review-r4-codex。

源码／R1真实先红后绿已由同fresh reviewer复核两轴approve／开放0；本节新安装／模型／固定提交尚待同片终核，尚未导入或推送。后续公开与自己的CI另验。父请求完整留存／全M1c／M5／正式V2及实际两轮、GPU／训练收益质量均未由本片关闭。

## 最终终核、普通导入及合并收集

同一fresh reviewer完成新安装／模型／固定提交原件终核，需求和维护性均approve／开放0，允许普通导入准确68ba793；[当前报告](2026-11-16-training-cycle-measurement-acceptance-source-review.md)SHA256 `6752988ac491b5e20c08acfb075ea36f7b5229fbcc679a45562c150eec061f7c`（原91582终核后仅去除本机根路径，结论与证据不变）。原r3 request-changes报告备份及各轮来源保持。

已普通合并开发分支`c6cfafb0b556c0cd36cf6f541e95ac4b15d3b254`。根逐项核663完整产品byte／mode同一；原848输入仅差另两片已审的CI JSON和Windows四行平台mark，分别沿其原交付，不扩大本产品行为范围。新联合真实collector2295节点＝原2269＋本片全部26；无删除，原38节点仅随两完整文件5→3，组3为453、组5为484。现成PhaseLog真实收集与纯选择接缝回放保留于final-union-r2；没有执行全组body，也没有在本机运行Windows。

final-union-r1首次协调命令将venv解释器symlink误resolve为基础Python，子进程缺pytest、0.118秒退出，尚未collect；旧stdout／stderr／请求保持。保留venv入口后final-union-r2实际collect退出0／10.03秒，不以首次失败冒称产品故障或覆盖旧结果。

**本内部片已闭合并导入；公开发布与该联合候选自己的CI仍另验。** 接续父raw留存已获准隔离实施，M5／M6／完整M1c／真实两轮及GPU／训练质量保持独立未完成，不由此关闭。
