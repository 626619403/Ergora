# c1d：原测量接受、不可变 rounds 与后继准入设计

日期：2026-11-16。状态：详细设计准备，待独立需求／维护性审查；没有产品实现、运行或两轮质量结论。承接[具体合同](2026-11-15-training-cycle-controller-contracts.md)、[c1总计划](2026-11-15-training-cycle-workflow.md)及[严格首轮c1c](2026-11-16-training-cycle-workflow-first-round.md)。本页将原方案尚未定义的出生版本、认证投影和最后准入列为明确实施前置，不以“复用”掩盖当前 API 缺口。

## 固定观察与前置

本次只读调查时主树 HEAD 为 `879654c`，分支 `refactor/architecture-foundations`，写本页前 tracked／untracked 差异为空；产品导入点为 `01ef69b71137df860e8fc433362d039ae241e744`。已验 c1b2b 的固定源码 bcc3048／wheel55029、安装、真实六活动和原预算根／native CPU结论沿[原终审](../delivery/2026-11-16-training-cycle-execution-product-review.md)保存；两个 CPU 例故意缺 evidence、原 gate=false，不能称 accepted measurement。此处没有重跑这些检查。

源码观察身份如下；这些是本设计的调查基线，不是未来 c1d 新包的验收身份：

|文件|SHA256|
|---|---|
|`src/ergora/reference_training_worker.py`|`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`|
|`src/ergora/training_execution_protocol.py`|`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`|
|`src/ergora/training_rounds.py`|`d4ca342b902f9d8c869171bbefa78b7fa6c0f0b129f57ea162b505e1d5124e7a`|
|`src/ergora/reference_training_evidence.py`|`1ffce17c7a6e7747d33e9544f5eade399565f6bf9443eb94a00083feb681580a`|
|`src/ergora/reference_training_runtime.py`|`1183a95c53a9550789983e245676a46637b5de748ddf32eb0ec5df9def46458a`|
|`src/ergora/reference_training_budget.py`|`d002c88e79bc3d856c86415511d307636d4a11698168ece6100e18824b149d4e`|
|`src/ergora/reference_training_execution.py`|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|
|`src/ergora/training_cycles.py`|`07215a1b1b1876c462333154ef834ef73f2a3b6020703270bfb3395c084f5972`|

c1c 当前在独立工作树实施，**尚未作为本设计的已验前置**。进入 c1d 产品实施前，须先取得 c1c 固定源码、W0–W10真实验收、新包／默认 sandbox／正式类运行和独立审查结论，并重核以上调查差异。c1c 永久只 ordinal0；不能给其旧运行安装新代码后自动开放 ordinal1。本页允许先审设计，不授权跳过该门禁。

授权范围是顺序消费同一出生同意中1–32个既有候选；各轮保留自己的原 baseline、manifest、结果、archive、stop 链和索引。沿原比较门槛决定能否继续，不改变算法、模型、数据、质量要求、统计方法或人工采用政策。kernel 专家仍在 v3 总提案路径，与通信、调度、内存等方向并列；本片不运行专家或训练。

## 实际调用链与当前缺口

|原 owner／实际生产 caller|已存在的责任|c1d必须补足的具体接缝|
|---|---|---|
|[training.evidence](../../src/ergora/training.py) ← CLI evidence／web evidence／`training_rounds.create`|经 `reference.training_evidence` → 独立原生进程 → [evidence.inspect](../../src/ergora/reference_training_evidence.py)，验证已接受 archive 的 gate／evidence／manifest／baseline／comparator及原文件SHA。|结果明确 `runtime_status=not_queried`、`artifact_content_status=not_read`；不能推出实际 phase、durable stop、当前执行许可或真实训练质量。|
|[training_rounds.create/read](../../src/ergora/training_rounds.py) ← CLI rounds-create/read|create 依次调用 `training.inspect/evidence/submission/approval`，保存四类完整观察；只重读新增轮，保留 previous 原 prefix；完整JSON后核10,000,000B／32轮。read 离线核完整文件SHA、schema、round内容SHA、父链接和同一初始baseline。|`training.approval`仅 local release记录，无RPC；index无实际phase或ExecutionRecords。`_COVERAGE` 明确 `origin_authenticated=False`、`authorization_status=not_evaluated`、`promotion_approved=False`，必须保持。|
|[worker._execution_candidate_operation](../../src/ergora/reference_training_worker.py) ← `_cycle_operation` ← `_CycleOperation` S/H ← SDK activity|H认证原controller、候选 intent／attempt／receipt、固定子run及memo；经原runtime lookup/observe、LocalTrainingAdapter.poll_job和ExecutionRecords给v2 typed facts。|当前不调用 evidence／rounds；request／observe及start具有多处 ordinal0 拒绝。不能只删除这些 guard。|
|[runtime.lookup/observe](../../src/ergora/reference_training_runtime.py) ← worker／Execution.check／原status|固定receipt.run，核完整Experiment started input；RUNNING取status，COMPLETED取不follow的新旧outcome。worker另核原memo与namespace。|runtime phase与archive／reap必须组合，不能把 COMPLETED、native SUCCEEDED、local approval 或 gate PASS单独当接受。|
|[ExecutionRecords.load/observe(durable=True)](../../src/ergora/training_execution_protocol.py) ← worker／Execution／native／原inspect|绑定request→launch→attempt→ack→stopped、原owner／intent／native request；同步既有文件／目录、重读原raw后才给 durable_stop_confirmed／executor_stop_confirmed。|不得用PID消失、S/H退出、SDKtimeout、`stop_observed`、父drain或native terminal替代。该方法重读比较raw；不要误报它已经检查同inode。|
|[BudgetedStart.source/require_active/check_controller_history](../../src/ergora/reference_training_budget.py) ← submission／worker adapter／Execution|原源、授权、候选位置、项目／clock和父RUNNING检查；父共享permission覆盖原实际动作。|`CycleAdmission.bind`当前只核本候选和父receipt，ordinal>0并无前轮门槛；须补本地不可绕过的版本化必要条件。|
|[protocol.validate_context/native_main](../../src/ergora/training_execution_protocol.py) ← 原execution／native admission callback|无SDK／State；完整cached context、原source capability、BOOT预算、父stop和原executor锁内attempt／ack最后检查。|不能导入 `training_rounds`（依赖State/contracts）或SDK查询phase；最后gate仍必须核同一前缀和冻结接受投影，不能只信Workflow曾说可以。|
|`asset_trees.publish_directory` ← rounds／cycle等原不可变目录发布|Linux `renameat2(RENAME_NOREPLACE)`，Windows rename；不会覆盖竞争目标。|没有fsync。原rounds返回“已发布”不等于可作为durable前置；H须同步并重读同一现存artifact，不改变所有目录发布者语义。|

原锁序保持父共享许可 → submission／registry／execution／executor各原锁；原预算clock贯穿。stop writer先发布可见拒绝，独立drain不拿业务锁；c1d不能反向持executor锁等父排他许可，也不能在共享许可中等待Temporal里另一个需要同一许可的操作。archive读取／索引采集不持SQLite事务跨RPC，不进live root的pipe loop。

## 必须先审定的版本合同

当前授权只认识schema1/2，controller binding、六字段workflow_input、activity request/context、owner和capability都严格字段集合；`GATE_SOURCES` **没有** `training_rounds.py`、`reference_training_evidence.py`和rounds schema。仅增加一个collect helper，或把旧binding原样放开到ordinal>0，不足以安全交付。本页推荐以下最小版本方案，尚未修改这些格式：

1. **新出生授权分支。** 保留schema1手工、schema2首轮的全部字节／语义；c1d采用新authorization schema3，仍由原 `authorize_controller` 的同一发布算法显式出生，永不升级既有cycle ID、补同意或重开clock。controller的执行范围仍为已选顺序一次，continuation仍是accepted-archive-pass；增加明确程序版本及下面固定的measurement source inventory。新ID／新授权是产品开放后继的前提，不由status/reconcile自动生成。
2. **新程序及wire分支。** 建议新protocol `ergora-training-cycle-v2`，六字段workflow_input形状保持，protocol值区分；SDK定义名 `TrainingCycleWorkflowV2` 在原被pin worker模块顶层可选装载。与c1c原类并存，原normal／stop服务进程与独立配额复用；不新建调度器。runtime根据原授权版本验证精确type、queue、input、memo及first/original run，而非接受任一名字。新start/request/observe/collect/stop的版本化活动入口不得放宽旧v1/v2含义；名字／版本表在实现前一次固定并审查。旧类及旧history保持原command序列，不用patch或查询当前文件把旧run切到新分支。
3. **源冻结扩展。** 不改既有 `GATE_SOURCES` key集合，不把低覆盖index变成source认证。schema3在出生原件内新增严格、固定三路径SHA inventory：`training_rounds.py`、`reference_training_evidence.py`、`data/schemas/training-rounds-v1.json`。它们与原owner capability的GATE_SOURCES共同覆盖实际采集／校验路径；在H采集前后、后继intent出生前、原source/context最终gate都核当前字节。不得在恢复时把新hash采作原hash。index中的local approval不是接受权来源，不能因调用它而允许release。若实现发现接受权还实际依赖其他未pin文件，先列真实依赖并扩审固定inventory，不能任意路径表或漏pin后宣称完整。
4. **必要认证冻结在原候选intent内。** 新controller binding分支包含 `predecessor`：ordinal0必须null，ordinal k>0必须是本页所述已认证的0..k−1前缀与最后轮接受投影。它随原 `.intent.json`、context SHA、owner及后续request链冻结；没有独立proof.json、表、可变current-round、cache或“已批准”文件。原schema2不允许携带该分支。单有index或任意复制的投影不能执行：还须新授权、同一父run／活动来源、原一次机会、原source和所有最后gate。

替代项是维持schema2、通过新的独立输入字段／patch marker辨别新程序，但必须同时证明未启动旧授权与在途旧history不会获后继权，并给native提供出生选择依据；当前接口没有这个依据，推荐显式schema3。另一个替代项是扩大GATE_SOURCES为新全量版本capability，但要维护旧owner的版本化reader与key集合；与原“不改key”合同冲突更大。不能以零格式改动的假兼容替代上述问题。

这是原owner的格式／程序扩展选项，须取得独立设计结论后才算实施合同；不要求新增权限种类，不替用户作WA4的人决策、自动批准或采用政策决定。若独立审查不接受该版本方案，c1d继续关闭，先在本页记录选定替代及其兼容／pin证明。

## H内接受事实与准确绑定

接受的消费者是**原worker中受监管H**，不是Workflow、UI、rounds reader或live root。首选在 `_cycle_operation` 增加一个内聚的 `collect-round` 分支／私有函数，组合现有 `_execution_candidate_operation`、`training.evidence` 和 `training_rounds.create/read`；不增加模块、通用reader或manager。Workflow只消费H形成的有界typed投影和原件引用。

对 ordinal k 的接受必须同时满足：

|事实|精确正面条件及绑定|
|---|---|
|父与当前来源|原schema3／ready／完整plan／authorization/input SHA、controller intent/attempt/receipt、同一namespace/type/queue/固定run；原父仍RUNNING；候选是冻结列表的k，project完整身份／revision／registration／执行路径不漂移，父stop明确不可见，BOOT和work／operation窗口为正。|
|原子实验|原start intent／attempt／receipt、完整Experiment input、memo、workflow/run、binding、job ID、native request原raw/semantic SHA与ExecutionRecords一致；native=SUCCEEDED。不能按实验ID或文件名拼接别轮证据。|
|实际phase|RUNNING且 `AWAITING_RELEASE`，或同一固定run的COMPLETED outcome为 `RELEASE_EXPIRED`／`INTEGRATION_TASK_CREATED`；必须是真实query/outcome，不是保存的local approval。RUNNING status中的evidence_sha须与archive一致；终态outcome没有同等evidence_sha字段，须用其原 `report_uri` 与本轮原gate-report、完整input/memo及job共同绑定，不能编造outcome字段。|
|原accepted archive|`training.evidence`整体成功，archive_status=recorded、recorded_gate_report.passed严格true、原recorded result=SUCCEEDED、baseline_matches=true且无fence。evidence SHA、原gate/archive报告、manifest原raw SHA、baseline snapshot原raw SHA、comparator原SHA及files完整映射均绑定同一原轮。保留reader的 `artifact_content_status=not_read`，不宣称重新读完全部artifact。|
|原durable stopped|同一完整ExecutionRecords同步与raw重读成功，durable_stop_confirmed及executor_stop_confirmed严格true；保存全部record semantic SHA及raw_sha256，原request、launch、attempt、ack、stopped缺一不可。不得要求老owner仍活以读取已停原件，亦不得为缺件补造stop。|
|完整前缀|原rounds完整读取／check成功，0..k恰为冻结列表前k+1个、每轮候选／manifest／注释逐字匹配；相同initial anchor和cycle `_COMMON`语义合同。所有已确认prefix逐项与原保存值相同，previous_report链接及整文件raw SHA正确。|

原 `_COMMON` 包括baseline、config、workload、dataset、initial checkpoint、environment、validation contract、comparator、checks、quality_required和performance_policy。接受投影只给这些完整原值的摘要，不重新评分；比较器仍由原gate重算成对原数据并检查测量窗口、normalization/statistics/thresholds。收益不确定、质量不足或失败保持原报告，不改成“优化通过”。仅以base/candidate commit相同或缩短摘要代替完整语义绑定不合格。

H的结果分开 `measurement_state`（pending／accepted／rejected／unknown）、`index_state`（absent／published_unconfirmed／durable／unknown）及`continuation_ready`；只有整体observed且上述全部正面事实、durable index和最后准入都齐全才有ready=true。原typed失败／负gate不臆断质量类别；缺phase／archive／stop、RPC丢回复、源漂移、坏记录、容量或时钟unknown都不给后继权。明确尚在GATING／等待reap可在原界内只读等待；认证失败不会靠猜error文字转为正常pending。

接受投影冻结在H原operation结果及后继原start intent中，至少包括：完整cycle/controller/ordinal/候选/manifest/registration身份、原start/request/owner及全部execution记录摘要、真实runtime observation种类／phase／job／namespace／input和memo摘要、evidence原raw SHA／archive gate和files映射摘要、source版本／inventory摘要、同一operation ID与SDK activity source、prefix路径／完整raw SHA／长度／轮数／last-round SHA／initial-anchor摘要。它是源已pin的原owner对本次观测的记录，**不称独立身份认证或质量签名**。

详细结果不能先从H输出再让父loop裁剪：原S只接受32KiB helper stdout。H复用当前 `_cycle_operation` 已有的 `helper/observation.json` 归档方式，将完整新采集的runtime／ExecutionRecords／evidence观察写在该实际operation输出目录，文件上界沿原各reader与10MB index界，返回仅完整有界投影和准确文件raw SHA／bytes。完整累计index不再复制到此文件，仅引用原rounds artifact；所有引用路径由原operation身份派生。该观察文件只是原操作证据，不是独立准入凭证、批准或第二账本；后继H必须重新读原archive／链及认证phase，不能导入任意调用者提交的observation冒充认证。低覆盖rounds不改覆盖声明。

## 只追加原索引、恢复与持久确认

原 `training_rounds.create` 足够完成采集及append，首选不改它的公开参数／schema，也不增加snapshot注入接口。每轮只传一个原候选的 `experiment_id/change/next_bottleneck`；k>0同时传此前history确认的previous目录及准确整文件SHA。它实际重读新增轮，故H须**校验最终发布的index内那份native观察**，不能把create前的一份evidence检查当成create后的证明。

建议索引目录是原cycle目录下确定性 `controller/rounds/<ordinal>/`；每目录仍严格只有一个原 `rounds.json`，不放acceptance标记。路径从原home/project/cycle/ordinal派生，调用者不选任意目标。历史保存全prefix的**引用和准确SHA**；完整累计index留原磁盘，不塞入SDK或S/H的32KiB请求。

1. collect command在Workflow history中先永久消耗本轮唯一“可能发布”机会，最大attempt1。H首次且未见目标时，完成原事实preflight再调用原create；不因重试attempt、新operation ID、超时或目录不存在返还这次机会。后续恢复活动是只对账，不能再次调用create；即使原命令实际未发布也保守停在unknown。该规则与start/request的一次history机会一致，不新建index-attempt账本。
2. 已存在目标必须原read核普通目录／文件及完整schema、SHA、prefix、当前轮及注释；不能覆盖、删后重建、换临时目标当新一轮、扫描“最新”或挑较短有效prefix。并发create由原RENAME_NOREPLACE整体拒绝；输家只读胜者完整artifact，只有完全符合原预期才可确认。源不匹配或残缺目标永久保留并needs_reconciliation。
3. 不能把create返回直接置durable。H打开现存rounds.json取得fd／raw／dev+inode，完整read/check后fsync该fd、索引目录及到原cycle根的目录链；重开相同路径核同inode与同raw，再read同一SHA／完整prefix。复用 `protocol.read_raw/sync_directories` 和原rounds reader，少量fd生命周期逻辑留collect owner；不全局修改publish_directory。同步失败或替换即published_unconfirmed／unknown，保留文件。
4. 完整index内最后轮的evidence／records／submission／approval与本次原链交叉检查；本次原phase及stop再次观察，源／项目／父stop／operation窗口在同步之后再核。preflight正面而最终index捕到no_accepted_archive、其他run、baseline drift或任何冲突时不确认；该不可变artifact不被修补。已有完整正面artifact但仅持久确认丢回复时，恢复可以同步同一raw并重新核原绑定，不创建第二份。
5. history收到并验证完整typed结果才增加已确认prefix和ordinal。结果丢失、SDK编码失败、H输出超限、发布后fsync失败均不推进；下一只读对账只定位确定性目标，重新核全部接受条件，返回同一artifact引用。旧prefix引用仍是权威恢复点；不能以新目录存在推history已经确认，也不能以文件不存在回到空prefix。
6. 各次累计index都保留，最后一份包含此前完整已确认轮值而不是重新采集旧轮；`previous_report.sha256`指原文件原SHA，逐轮内容与原prefix精确相等。原rounds `_check`只核声明链接，collect还须拿已pin的previous实际report作完整prefix相等检查，防止只保留最后一条SHA却替换早期观察。

index保存local approval可能正好看到人工决定变化，此字段只记录当次原观察，不能要求自动approve或把未批准当测量失败。失败、负gate或unknown的原结果始终留原native／H／history；若有完整可采观察和正work窗口，可由同一次collect保存原失败轮的低覆盖index，但continuation永久false。窗口／原件不足时不为了“完整报告”新授写入或伪造空轮，保留已确认prefix及原失败／未知引用，显式说明该轮未索引。完整prefix超过10MB时不分片冒充完整、不丢旧轮；停止并保留原index和原实验结果。

## 后继在原最后动作也必须过门

仅Workflow顺序正确不够。新ordinal k>0的start intent必须在原 `_prepare_submission` 出生前，从H已认证结果取得前缀pin与最后轮投影，并作为controller binding的一部分冻结。新start request只传有界prefix pin／先前operation引用；H从原路径读取并认证完整原件，不能信请求自称accepted。ordinal0明确无前驱；缺失、错位、多轮／少轮、同一候选重复、不同父run／授权都拒绝。

`CycleAdmission.bind`／`BudgetedStart.source`及 `validate_context`增加同一版本化、纯本地必要条件：检查schema3与新binding、完整原prefix raw SHA和候选序列、冻结投影与前轮ExecutionRecords／archive文件摘要、原授权source inventory、前轮原intent中更早prefix的递归链接。只需至多32层，不持本地可变状态；原index仍不授权。早轮一经确认不重采phase、不覆盖结果；既有原候选intent中的投影承接早轮的当时认证，最新H接受则认证紧邻前轮实际phase。缺任一已确认原artifact即拒绝新动作，不降级为ordinal0或较短prefix。

H在start、原worker创建job、Execution.request／launch这些异步原消费者，还须在原父RUNNING认证后、各原锁的最后动作前核相同前驱和原operation／clock。`native_main`外层父共享许可及executor lock内callback使用同一纯validator，attempt发布前、ack发布后／返回process前核冻结的完整前驱、source、父stop和clock。native不查询Temporal，不把一份历史phase说成实时phase；原H已认证的phase观察随原intent冻结，native核其不可换绑的本地前置，和当前原archive／stopped原件／source。不能让另一个SDK请求／手工binding、晚到create或直接native invocation绕过这些条件。

纯validator属于已pin的 `training_execution_protocol`，实际生产caller分别在budget的source、execution的context/current以及worker H／native最后gate，职责是绑定前置而非复制原archive reader／comparator。完整archive语义只由已pin的原evidence owner认证；最后本地gate核被冻结的完整文件inventory与raw／semantic摘要、原stop链、prefix及出生源。若实现不得不复制evidence算法才能满足它，说明边界仍未闭合，应先复审最小原owner的纯校验提取，不能另造第二archive reader。索引读仍用原rounds；依赖隔离native需要的局部纯prefix绑定校验应从原算法提取复用并保持原离线read行为，而不是在native导入State/jsonschema。

停止可能发生在接受投影形成、索引rename、fsync、后继intent、晚到RPC或executor callback之间：前几步留下原件不等于后继被准入；任何最后gate见父stop／源变／预算尽都拒绝。父锁仍覆盖实际四动作到返回；发布index不是扩大共享许可的理由，stop writer永不等待索引锁。已接受前轮保留原release窗口，不对它统一cancel；父stop只拒绝后继及清理活动／未确认轮。总循环结束不approve／release／创建integration task，不迁baseline，不换新run续clock。

## 最小函数边界与影响范围

|拟变更位置|实际caller／必要性|最小责任与不增加的接口|
|---|---|---|
|worker原 `_cycle_operation` 中collect私有实现|SDK新collect／只读对账入口，经过原S/H；单owner算法无需第二caller。|组合原evidence／runtime／ExecutionRecords／rounds，按原window采集、发布、同步、重读、最后认证；不新增service／reader／进程driver。|
|worker原 `create_cycle_activities`／新程序类|真实SDK框架注册、Workflow command与恢复／query／stop。|旧活动保持，新版本严格shape；有界inline投影+原refs，history持一次机会／prefix／ordinal。普通H和stop仍分配额，不在loop读大文件。|
|training_cycles原授权／intent生成与validator|原authorize_controller／prepare_controller／status／H读取。|新出生版本，版本化workflow type/input/source inventory；同一clock／不可覆盖发布。无本地current-round表。|
|protocol原binding／context／source及必要纯校验|budget.source、Execution.current、H及native最后gate，分布在真实不同文件。|一套必要前驱绑定；保留stdlib-only与原离线历史读取。源和SHA算法沿原合同，不把rounds漂亮打印SHA混成canonical semantic SHA。|
|budget原source／history、execution原request/current、worker adapter原lookup|原RPC投递、锁内job创建、request/launch/native。|接同一新版本前驱准入，原事务／锁／一次launch／reaper保持。不得只有SDK层检查。|
|rounds原read/check，必要时提取已有纯算法|CLI离线read、H完整prefix、native必要的纯绑定。|首选公开create/read不变；仅真实隔离调用需要时提取共同算法到已pin protocol，原完整schema校验仍归rounds。不增加“可信index”API。|

受影响最小产品面预期为现有training_cycles／protocol／worker／budget／execution，及必要的submission绑定传递；evidence／rounds优先不变，只有上述实证的纯校验提取才扩改。schema3及wire的实现格式在各原owner严格validator内定义；本次不新增schema文件或第二份文档交付。公开CLI／HTTP／页面属于c2，不借此自动启用新授权。原283参考文件、native delta、算法／比较器和定义包不变。

## 容量、预算、history与unknown

继续c1c的 `D_work=min(旧D_work,A+H_remaining)`／`D_total` 保守预算，所有轮共用一个原BOOT授权与不延长的SDK绝对界；进入新ordinal不重新cold、不刷新10秒、不重置D或control窗口。collect含所有原reader、RPC、rename、fsync、最终重读及返回，均消费同一operation window，H同步返回后也要复核截止。原子reader内部20/30秒或原gate的比较器120秒不能替代这个上界；S的原stop_requested/reaper负责过界终止及收尾，SDKtimeout与OS实际停止分列。

|界|具体约束|
|---|---|
|原plan／每份累计rounds|各≤10,000,000B；先完整序列化后整体拒绝。最多32轮，k的累计index必须全含0..k，不以单轮文件相加冒充原完整index。|
|SDK与S/H|完整每份input/result/signal/query/outcome≤32,768B，SDK按实际DataConverter及Payloads metadata核；H原request／result frame同为32KiB。memo≤2KiB。全prefix、artifact正文、完整大files映射不inline；仅固定投影及准确ref/digest，详细材料保留原件。|
|有界投影|prefix pin、当前／上一轮必要事实固定shape；query只给当前ordinal、已确认数量、最新prefix准确SHA/路径及history IDs等，不累计32份大结果。必要投影本身超限就拒绝，不截字段、reason或identity。新source inventory／binding使原start context变大亦须真实编码核验。|
|调度|沿c1c每候选ordinary command至多256，cold归ordinal0；collect、对账、失败及只读观察都计入，command前占数，SDK maximum_attempts=1。切轮只初始化新的该轮计数，保留原total计数，不重置原轮次数或预算。|
|history|沿c1c每ordinary活动／timer前核8000events或8MiB任一界，停止普通调度并走唯一stop／终态；32×256不是保证可跑完，先到history／预算界即停止。无continue-as-new／reset／新run／加server上限。|
|unknown|目录已rename但未确认、phase／reap交错、NOT_FOUND、RPC/SDKtimeout、fsync阻塞、坏链／源漂移／父stop、DataConverter或history拒绝均保存原事实与最后已确认prefix。只有完整正面认证可续；NOT_FOUND和缺文件永不重授effect。|

当前v1 stop封套没有cycle级完整typed汇总；沿c1c保持stop_durable／admission_drained／所有executor汇总为null或needs_reconciliation，不能因collect测量成功或所有S/H operation_stopped就填true。若新版本希望query认证停止分项，须在原stop owner另审typed投影；本片不暗扩。完整refs超32KiB仍保持真实非重试容量失败；原stop writer／通知／drain／reaper原件不删。

## 渐进验收节点与可达反例

以下全部是未来实施的验收要求，本次未执行。复用 `tests/test_training_evidence.py` 的原archive／prefix接缝、实际归属的training runtime/controller tests及 `tests/fixtures/training_controller_service.py` 等既有fixture；fixture合成archive只验合同，不认证真实训练。新增测试以真实静默越权／丢前缀风险为由，不为文案或默认常量增加矩阵。

|节点／前置|最小可达反例与必要结果|
|---|---|
|M0 版本设计及c1c验收先闭合|独立审定schema3／新program/wire／固定source inventory及原intent前驱投影；固定c1c源码与W0–W10实际结论。未闭合不删除任何旧successor_not_enabled。|
|M1 旧历史／新出生／默认sandbox|原schema1/2原件逐字保持；旧c1c成功、取消、失败和在途history用原类Replayer，重启原终点仍无ordinal1。新schema3同ID重试不换clock，旧ID不能升级；新类默认sandbox／实际Worker注册、core无SDK导入分别核验。|
|M2 四事实交错|native SUCCEEDED、AWAITING_RELEASE、accepted archive、durable stopped按不同次序到达，任缺一项均无ready／ordinal1。正phase搭负gate／缺archive、同名另一evidence、stopped仅可见未同步、SDK COMPLETED均不得接受；原完整链实际同步重读才可确认。|
|M3 原索引完整前缀|第二轮append只采新增轮，旧native observation逐字不变；伪造早轮但保持最后link、错previous整SHA、错project/revision／annotation／candidate顺序或baseline/common合同均拒绝。保留原prefix文件与原native结果，离线read无需SDK／当前安装。|
|M4 发布／durability／丢回复|在rename前、rename后fsync前、file fsync后dir fsync前、最终重读／SDK completion前注入丢失或阻塞；同path inode/raw替换、并发目标也覆盖。先保留unconfirmed，恢复只同步同一完整artifact；不存在目标不再create，不能换目录；全部前缀和原stop/request/launch SHA保持。|
|M5 最后gate绕过|直接新ordinal activity、手工binding、复制别run的接受投影、只放一个合法low-coverage index、略前驱／短prefix、缺已确认文件，均须在H和原source／context最后gate拒绝。分别让stop／source／clock在H检查后、原registry锁内、request同步后、native attempt/ack边界变化，无后继真实spawn；不只断言Workflow没调用。|
|M6 完整容量与原时钟|完整累计index刚跨10MB、32轮上界、H frame／SDK metadata跨32KiB、每轮256及history8000/8MiB先到；保留最后已确认prefix和完整未发送原件，只有一次stop。新ordinal不刷新D；队列／fsync延迟与server/worker停机至BOOT耗尽后恢复不产生新start/request/launch。|
|M7 合法CPU两轮的控制合同|新固定包／真实正式V2 Workflow至少两个既有候选，原runner产生实际数值和可独立检查oracle，原collect_and_gate真实接受archive，两轮各原baseline相同、各request/root/native/stopped与累计index完整。历史只各一次start/request/collect发布，前轮仍保留原release窗口，没有approve／release／baseline迁移。故意缺evidence的旧负例原gate=false保持，不借合成PASS或直接fixture写facts宣称两轮成功。|
|M8 新安装、真实恢复及收尾|新源码／非editable wheel、core/SDK实际site-packages／283参考／依赖／固定输入身份；真实server导出history及Replayer，lost reply、重启／取消／源漂移和代表性最后gate。核所有自建PID完整身份／后代／reaper、服务端run和监听终态；前片wheel与测试Workflow不认证本类。|

M7分两级：c1d产品接缝与真实链所用CPU oracle须是合法证据，但只认证控制、数值检查及原gate合同；可复现公开两轮脚本和完整例证仍归后继d片，不暗扩本次范围。真实GPU／ML训练必须另有已授权资产、训练／质量oracle、固定设备环境、baseline/candidate成对测量、窗口和不确定性、独立审查及准确accepted archive；CPU、合成fixture或控制器连续两轮不替代这些结论。任何成功报告须分别写控制合同范围和实际质量范围。

## 本次交接

本次仅阅读AGENTS／PLAN／组件协议、适用skill、原方案与实际源码／既有测试fixture，核Git状态和上述文件SHA，写本页并作文档静态检查。没有运行服务／训练／测试／安装／模型／网络，没有commit/push，没有修改主PLAN／交付或产品。采用 `maintainable-project-delivery` 与 `ergora-codebase-quality`；本片独立设计审查由根任务安排，本页不自称审查通过。

独立设计 review 已完成：[报告](../delivery/2026-11-16-training-cycle-measurement-design-review.md)需求／维护性两轴 approve、开放0，仅限本设计与所核原源码。M0 的严格版本 wire 表及必要纯校验提取尚未审定，c1c 正式验收也仍在进行；当前不开放 ordinal1。待这些前置闭合，再按 M0–M8 开最小实现片；c2 公共入口、d 公开 CPU 示例和真实 GPU 训练保持后继责任。

## M0严格wire设计接续

新增[严格wire合同](2026-11-16-training-cycle-measurement-wire.md)明确schema3、正式V2类、七个v3活动、前驱／恢复与完整容量owner；[独立审查](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)原R1容量缺口修后两轴approve、开放0，旧draft与原request-changes保持。源清单根据真实release.status依赖增为四项，并要求原reference.verify核包内283参考；这是明确审过的增量，旧三项方案不再作为实施冻结。当前仍须先闭合c1c终验，再按wire的M1子片实施，尤其完整编码／历史恢复与纯内容校验提取要用实际接缝验证。没有产品变化、ordinal1或测量接受结论。
