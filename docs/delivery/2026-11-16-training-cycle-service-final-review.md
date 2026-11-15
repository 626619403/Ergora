# c1b2a 最终候选独立两轴审查

日期：2026-11-16。审查者：fresh-context 独立 reviewer `cycle_service_final_audit`。应用 `ergora-codebase-quality` 的 repository-style／module-design／test-seams，以及 `maintainable-project-delivery` 的 independent-review brief。先读原需求、协议与完整差异，再读作者结论及历史 review；没有把历史 approve 当作本次判断。

## 身份、范围与结论

- 主项目为 Ergora，产品隔离树为 `.ergora/worktrees/training-cycle-service`。
- 比较基线：`478c98891522930817fa7005a8ac96e408f37230`；初审候选：`97a0bbfae9687c15927f1437a374cd070baf0a94`；最终候选：`af176cf6e79adb9c6ef6f32946672bc77cdb89de`，产品相同，仅一行测试配置修订。审查及最终接续核验时隔离产品树均无未提交差异。
- **需求轴：approve，开放 finding 0；本片服务边界验收闭合，可导入主树。** 源码、受影响安装回归与真实N32剩余证据已经分层复核，具体身份及限制见末节；固定导入身份、准确CI／发布仍分别后接。
- **可维护性轴：approve，开放 finding 0。** 未发现有证据支持的冗余抽象、重复业务 owner、无实际用途的新增 guard／测试，或本片引入的结构性能 blocker。

完整检查 `git diff 478c988..97a0bbf` 的全部13文件：六个产品 owner `reference.py`、`reference_training_budget.py`、`reference_training_worker.py`、`services.py`、`training_cycles.py`、`training_execution_protocol.py`；两个 fixture `training_controller_service.py`、`training_cycle_operations.py`；三个测试文件 `test_services.py`、`test_training_runtime.py`、`test_training_submission.py`；隔离树 PLAN 与 review-fixes 新文档。没有省略新增测试或将其视为已运行。另读相邻 submission／runtime／budget 的最后 gate、原 service 管理及真实 caller。

依据包括隔离树 AGENTS／src／tests 协议、组件变更协议、[原 r2](../plans/2026-11-15-training-cycle-service-boundary.md)、[c1 总计划](../plans/2026-11-15-training-cycle-workflow.md)和原 controller contract 第4节。主树未提交的 USAGE／TRAINING／architecture/current 及公开交付、安装、现场、launch 专项记录也已核声明范围。主控已同步 PLAN／服务交付当前摘要为97a0bbf，明确主树478尚未导入产品；旧身份保留为历史。

## 需求路径与结构判断

|检查路径|独立判断及依据|
|---|---|
|真实 SDK 来源与原件认证|`create_cycle_activities` 只从 `activity.info()`及实际 client 取得来源；严格 request/context 拒绝 local／缺 Workflow／错类型、queue、namespace。H 的 `_activity_binding` 比完整原 intent、唯一 attempt、六字段 input 和原 receipt；业务输入不含自述来源。|
|缺 receipt 的竞态|`_dispatch_controller.reconcile` 把实际 activity run 传给原 `lookup_controller_submission`；原 runtime 核 first/original run、started input、两处 memo、类型／queue 及非 retry/reset/successor，写 receipt 前再次核同 run。NOT_FOUND／漂移保持 unknown，不补 attempt 或重发 controller。|
|单次 start 与窗口|ordinal 非0在操作创建前拒绝；attempt>1及已有 candidate intent只走 reconcile。新 start 的 H 先核父 RUNNING，后续原 prepare／confirm／dispatch 共用同一 compute∩control window，最后 SDK点仍沿原 parent permission／owner／source gate。冷认证及随后 reconcile复用一次 bootstrap，不逐 H续期。|
|结果、父错误与容量|S在匹配 stopped后实际读 stdout才计算 raw bytes ref；父侧 Popen／transfer／cleanup事实额外 inline，不能由 H ref冒充归档。原 reader的精确容量子类贯穿 H／S／adapter；实际 DataConverter的完整 Payloads.ByteSize包含 metadata，失败非重试，不截 reason／分支。launch guard的最小修正保留原 intent占位、普通 ValueError及一次机会。|
|stop 分支及取消|原 stop owner仍构造 writer／drain／每候选 notify、observe共2+2N分支；单分支构造／运行错误保留完整 inline，其他 peer继续。所有已创建 task在 finally中被持有到原 S/H实际收尾；各 durability／reap／execution事实不合成新的总 stopped。|
|进程、配额及关闭|原 reference／services提供独立 cycle command、日志、autostart=false和70秒观察期。新 loop 两 Worker各1活动槽；原 budget入口、注册和8槽不改。fatal回调及时触发normal-first关闭，重复取消仍持有cleanup，normal实际终态后才关闭stop。已交接根只留观察者，服务关闭不通知该根；强杀不生成业务stop证明。|

新功能沿既有平铺 owner 扩展，没有新模块、调度器、current-round账本、process-host或 reaper。新增私有 helper隐藏 SDK封套投影、实际操作结果保留及资源关闭时序，是原 owner内的具体职责，单 caller不构成应拆通用框架的证据。protocol保持 stdlib边界，应用 State／native／业务锁／fsync／同步SDK调用仍在 H或预算根；父loop只做有界编码和异步监管，未用线程搬运业务存储。

测试的独特风险可以落到真实接缝：服务旧daemon／缺SDK，缺receipt及来源漂移，实际 S/H／根生命周期，SDK run验证与poller fatal，父结果丢失，request/stdout/frame/metadata及完整launch容量。新增 launch回归在首次真实注册前加入合法大check，真实产生“compact snapshot可容纳、完整launch超限”的不同尺寸，不是注入同名异常；其重复／重投检查保护不可恢复的新offer风险。66 refs测试验证真实S/H分支和原文件，不等于真实Temporal server的32候选现场。没有发现应删除的浅层重复测试；测试私有SDK bridge／poller构造与当前1.34.0固定环境相符，产品只使用公开SDK API。

本片没有修改角色后端选择、祖先完整资源／权限收窄、六阶段、冻结证据、原 approval、kernel专家v3或质量门槛；相对基线没有preset、参考资源或这些owner的变化。此处只确认该合同未被本片绕开，不重做所有历史能力的运行验收。正式总Workflow／execution／collect／accepted后继和训练质量继续是后继片。

## 本 reviewer 执行的检查

1. 完整diff与真实caller静态检查、`git diff --check 478c988..97a0bbf`通过。最终budget／worker／submission测试SHA与launch专项记录完全相同。
2. 使用已有SDK1.34.0解释器，`PYTHONPATH=src:tests`、`-B`直接装载现有runtime测试函数，执行metadata容量及normal-validate／stop-validate／validate-during-shutdown／stop-fatal四种时序，**5项通过，完整命令1.3秒，退出0**。保留真实SDK run／shutdown代码，bridge／poller为测试替身；后者含重复cancel与最终零pending task断言。容量完整value及注入fatal日志是预期输出。没有pytest suite、业务文件／子进程／服务创建。
3. 对r3实际wheel与core／SDK安装，独立逐项重新读取并比较当前source、wheel、site的663文件SHA和source/site执行位，**两环境差异均为0**；wheel SHA256为`081aab4594f8afa18505c3ec8a8b78ff98690510303a7041e3074af5fcab38cf`。原件 `package-r3/package-r3-{core,sdk}.json`、reference／dependency记录分别为283 PASS及退出0；这些后两项本reviewer只读核原结果，没有重装或重跑。

只写本报告。没有改产品／测试、安装、启动服务、跑昂贵suite、commit或push，也没有改 ignored验收原件。

## 证据身份与待完成项

旧包`747e221b584fa71518e2b64ce69fcace2eb4ef1340450cfd50e6f47e8729e017`属于eedba08。其安装20 passed／155.47秒及真实N=2服务验收保持该身份。已读`live-r2/final-audit.json`及listener终态原件：144记录身份、73已核ref、3预算根无活匹配且有final；Workflow管理终态、根退出及execution_stop=null分别记录。两个候选Workflow最终测试terminate不计业务stop，受控SIGKILL不计Supervisor70秒到期验收。这些结果未转记为97a0bbf的新现场通过。

97a0bbf的launch源码原反例1 failed／22.31秒、修后9 passed／114.79秒有原日志及最终三文件SHA；本reviewer核源码与记录，未重新运行这9项。新r3包身份已如上核实；新安装冻结输入9项受影响回归尚在途。原自身模板r3的真实Codex结果已读：approve、68.458秒、run `dfd8172c3ba642f09e908df011d4a7c5`、input digest `0212b8aff2d52c5debae2dbd8026edebe3ab9b18c7692eda52cefc82d0691249`，24完整文件736157B、3资源、850834B stdin。其明确仅supplied source、不认证安装／live，不能替代本次独立审查或真实服务证据。

**完整交付仍 pending**：需回收新包定向回归结果、新r3最小正常服务及真实32候选SDK fanout／完整refs／unknown／容量拒绝证据，并核全部自建资源终态。原r2明确要求真实32候选，现有源码／冻结安装的66分支测试不能填此格。最终主树导入身份、文档集合及准确CI／发布也未在本报告认证。收到这些原件后，可由本reviewer复核证据和固定身份；没有新的源码缺陷需要先改产品。

## 接续：r3首次安装回归的7秒正常场景

新包首次冻结输入9项实际结果为 **1 failed／8 passed、177 deselected、118.82秒**，完整subprocess119.79秒、退出1；原件位于ignored `installed-tests-r3/{tests.stdout,tests.result.json,junit.xml,basetemp}`。唯一失败是 `test_cycle_sdk_start_hands_off_once_then_duplicate_only_reconciles` 期望 `observed`、实际 `unknown`；不把初跑计为通过。

本reviewer只读复核该失败的原授权、operation request／stdout、service记录及fixture配置。prepare／confirm／dispatch三个request的bootstrap完全相同，`started_ns=2782628976587442`、`deadline_ns=2782635976587442`，即原7秒窗口，没有续期。dispatch H stdout真实保存`submitted`，且`attempt_saved/result_saved=true`；service实际`starts=1`。授权clock为`2782623387191265`，H末采样`total_remaining_seconds=887.51203`、原wall=900，由此推得该采样距原deadline仅约 **0.101426秒**。父侧仍须等待S退出、读完匹配完整帧并核同一窗口未过期；原件中的晚成功事实不足以把父观察升格成功。产品返回unknown符合既有保守合同，目前没有证明重复start、丢失原attempt、窗口刷新或错误清理的产品缺陷。

**同意最小fixture处置**：仅给这一正常SDK start测试使用现有 `controller_admission` 的间接参数 `{'control_timeout_seconds': 30}`；相邻正常root生命周期测试已有相同方式。该测试验证handoff及重复只对账，不以7秒成本为被测行为；选择支持范围内的较宽正常预算合理。保持全局fixture默认7秒、产品默认与所有deadline／普通ValueError故障预算及现有断言不变，不将`unknown`加入happy-path成功预期，也不依据迟到stdout放松产品期限。单个parametrize即可表达本测试配置，无需新fixture／重试／sleep／产品改动。

这只是fixture修正的独立意见，尚未把新冻结输入重跑计为通过。应保留当前初败和其冻结输入，新输入另存身份后针对同r3产品安装复验；需求／维护性源码approve维持，完整交付继续pending。

## 接续：af176cf6固定身份及r3实际服务证据

固定候选为 `af176cf6e79adb9c6ef6f32946672bc77cdb89de`。本reviewer核 `97a0bbf..af176cf6` 完整diff，只有上述正常测试的一行间接parametrize；六产品owner没有变化，wheel081aab45及原源码审查仍准确绑定该产品。隔离树干净，完整基线diff whitespace检查通过。r3b的178份冻结tests/examples已由本reviewer逐份重读、核SHA及bytes，全部等于固定af176cf6树和实际新测试输入。

已核r3b `tests.stdout/tests.result.json/JUnit`：**1 passed／21.58秒**，完整subprocess22.51秒、退出0，实际`-I -B`、unset PYTHONPATH及site安装；初跑8通过／1失败继续分开记账。r3 core原件为真实SDK-free S/H inspect通过、操作0.857秒／完整subprocess1.321秒，9原件、DB和window不变；首次私有glob取样误匹配current symlink在H前失败，保留`first-core-*`，随后仅排除symlink而重读同原件。未把私有probe入口失败归为产品失败，也未删除它。

r3真实服务独立复核结果：

- 两个实际服务command均指向r3 SDK site安装，budget／cycle PID不同，cycle stopwaitsecs=70。正常start的操作顺序为prepare／confirm／dispatch；重复start和显式reconcile各只有reconcile-candidate。前后完整原intent／attempt投影相等。
- 本reviewer直接读取业务stop结果和真实Workflow history，用protobuf重新构造完整Payloads，核保存的pb字节完全相同：N2为**2,930B**，N32为**19,354B**，均包含metadata。N32的66操作恰为writer／drain各1、notify／observe各32，每个ordinal各1；全为ref、operation_stopped=true及supervisor_returncode=0。
- 独立重新读取并计算**84个不同活动stdout refs及4个producer refs**的raw bytes／SHA，全部吻合。完整计划231,293B、原产品snapshot5,775B的记录与实际完整fanout相符，没有以裁剪候选适配封套。
- `live-r3/final-audit.json`中2个controller和1个candidate均原COMPLETED、无测试terminate；唯一预算根退出且有原final，execution_stop仍为null。140记录身份／无业务survivor与端口／socket／daemon终态原件已读；本reviewer另对外部50ms观察器记录的**138个完整进程身份**逐一当前复查，活匹配为0。未观测到的短暂进程仍依赖原S/reaper stopped与wait证据，不能由50ms采样宣称穷尽全部子进程。

上述记录没有执行器／训练／GPU。r2的receipt竞态、实际attempt2、锁阻塞独立stop、信号／重复cancel／fatal及强杀保持其原产品身份；本次未重跑，不转记为r3现场通过。r3新增变化只涉及typed launch容量分类；旧生命周期证据、受影响新安装回归、实际SDK生命周期短探针与r3正常现场共同支持源码两轴approve，无新增产品finding。

**当前仍pending的原明确验收**：r2末段逐字要求“真实32候选完整refs／unknown／容量失败”。现有N32现场已闭合完整refs，但19,354B成功结果没有触发容量拒绝；N2安装替身中的unknown／容量反例也不是N32现场。主控已接纳此边界，安排两个全新N32授权场景，经ignored harness的operation构造接缝注入单分支unknown和长reason最终SDK容量拒绝，核peer收尾。没有新原件前不称这两项通过，也不称r2全部运行验收闭合；本片完成／导入建议待这两项证据复核。无需为此改产品或重跑无关大suite。

## 最终接续：真实N32 unknown／容量失败闭合

本节更新上节历史pending状态。审查产品仍为af176cf6／wheel081aab45，无新产品变化。已读[现场r3b](2026-11-16-training-cycle-service-live-acceptance.md#r3b真实-n32-混合-unknown-与最终-sdk-容量边界)以及ignored `harness-r3b/`、`business-{mixed,aggregate}-r3b/`和`live-r3b/final-audit.json`。两个场景各自经原API创建全新32候选／cycle／900/180/60授权。故障wrapper只在本cycle的notify-owner ordinal0构造处抛普通ValueError；它使用原cycle_main、真实SDK及其他65个原S/H分支，不替换产品容量判断或回收算法。此证据确为constructor故障注入，不能称实际OS syscall故障。

本reviewer执行的独立只读复核（同一r3 SDK解释器、`-I -B`，约1.1秒，未起服务或写原件）：

|场景|原件核验结果|
|---|---|
|mixed N32|从真实history重新解码实际stop input **489B**、完成结果 **19,510B**（完整Payloads包含metadata），与保存业务request／结果逐字对应。66分支恰为完整2+2N组合；65 peer refs全stopped／rc0，另一个inline unknown的**92B原因完整相等**、stopped=false／returncode=null，无operation目录或ref。|
|aggregate N32|实际history stop input **493B**，随后ActivityTaskFailed的原application type=`cycle_activity_capacity_exceeded`、non_retryable=true、retry_state=2。直接从原worker stderr的`full unsent value`重新解析完整封套，与独立保存原件相等；用同DataConverter重编码得到实际**39,518B**，与保存protobuf字节相等。完整**20,066B原因**未丢失；65 peer refs全部stopped／rc0，ordinal0 inline无H／目录／ref。39,487B preflight投影没有参与实际通过判断。|

两案全部原authorization／plan／ready等**各4份原件**重新读hash不变；完整原分支计数、逐ordinal组合及无伪造ref均已直接检查。独立重读并重算**134个不同活动stdout refs**的bytes／SHA全部吻合；遍历原件重建**274个完整进程身份**，当前活匹配0，与原final audit相同。writer原结果／原stop审计为stop_durable=true，仍不把它扩大为executor停止证明。两个controller原COMPLETED、无candidate submission或预算根；各次shutdown均daemon not_running，最终socket不存在、7233／8233无监听。两案均为首次运行，没有失败重投、改产品、扩容量或重授旧授权。

**最终需求轴approve／开放0；最终可维护性轴approve／开放0。c1b2a服务边界的本地验收闭合，建议允许把固定af176cf6导入主树。** 完整refs、混合unknown及最终SDK容量拒绝的真实N32证据现已分别成立；原源码／安装／SDK生命周期及r2现场故障证据保持其原身份，结合两行精确产品修正的受影响新安装复验和r3正常／N32现场判断本片，不宣称同一新包已重跑全部历史场景。正常测试初败8通过／1失败及新冻结1通过也继续分列。

本结论只覆盖四活动、真实SDK来源及一次机会／对账、独立服务及normal／stop配额、原S/H／预算根生命周期与完整结果容量。未认证正式总Workflow、execution／collect、接受后继、训练／GPU／质量收益；未实测Supervisor70秒到期SIGKILL，也未把constructor注入称真实OS故障。主树导入的固定merge身份及产品／资源字节仍待导入后只读复核；准确CI和普通发布尚未发生，不在本结论内。无关CI分组候选不属于本片。
