# Q4.2b1 前置阻断：独立实施前计划评审

日期：2026-11-15。角色：fresh-context 独立计划 reviewer；本次不实现产品，不递归委派 reviewer。

## 范围与结论

完整待审计划为[原训练提交的前置阻断](../plans/2026-11-15-training-start-fence.md)，固定副本 `.ergora/checks/training-start-fence-planning/proposed-plan-r1.md` 与读取时计划均为6,409字节，SHA-256 `beabf73860a35b79255b830343fb6309538c6feaa82da7f51c852f60c51811d3`；对应 JSON 指定事实基线 `d3c90e751ee9257df36b74e57e8956d38bbde848`，实施基线仍为空。a2 的实现、安装、评审及发布不属于本次认证，b1 实施仍须等待其精确基线。

已读根／`src/ergora/AGENTS.md`、当前 `docs/PLAN.md`、[组件变更协议](../architecture/component-change-protocols.md)、[当前架构](../architecture/current.md)、[reference 边界](../architecture/reference-boundary.md)、[总体有界循环计划](../plans/2026-11-15-bounded-training-cycles.md)、[a2 计划](../plans/2026-11-15-training-cycle-selection.md)及相关原评审。应用 `ergora-codebase-quality` 的 repository-style、module-design、test-seams 三份 reference。下述原源码锚点已核相对事实基线无差异；共享工作树中的 a2 新模块、schema、CLI／注册修改不作为 b1 产品证据。

|评审轴|结论|开放阻塞项|
|---|---|---|
|需求符合性|**request-changes**。原 primitive 足以支撑手工确认的本地阻断小片，但必须先澄清 fence 的 release／executor 效果，以及无投递锁时的状态快照与幂等恢复合同。|R1、R2，均为 P2 计划合同问题。|
|可维护性|**approve，限设计方向**。沿原 `training → reference.training_submission → _Submission → LocalTrainingAdapter`，保留原 reader／registry／不可变 writer，符合实际 owner；无需新增状态表、训练器、通用 adapter 框架或独立转发模块。|0。下文路径、依赖和进程要求属于实施验收义务。|

这里的 request-changes 不否定先补必要接缝的分片方向。R1／R2 可以通过最小合同修订解决，不要求先完成 b2／b3。两项关闭前不应把 B1 标成完成；计划结论不认证尚无的实现、测试、安装、服务或 CI。

## 实证阻塞设计项

### R1（P2）：确认含义须覆盖原 fence 的实际效果，不能无条件保留所选实验的 release

受影响的是计划第9、19、23及32行。原本地 [fence_and_lookup](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L167) 在 registry 锁下查 job，再写 `training/fences/<experiment>.json`。同文件第201–205行的 `authorize_release_and_create_task` 在同一锁下先拒绝该 fence，再创建 integration ticket。因此 create 先于 fence、但 release 的 ticket 尚未创建时，本次 fence 会抑制**所选实验**的未来 release，即使测量已经成功。unknown 没有 receipt，不代表它还未测量完成。

同一 fence 还由 [training_executor](../../src/ergora/data/reference/platform/local/agent_platform/training_executor.py#L58) 在 runner 开始前、runner／归档的 Sandbox 和证据校验节点观察，可能使原 executor 走取消路径；它并非只有阻止新 job 的效果。反过来，ticket 若先在锁内创建，后写 fence 不会撤回该 ticket；原 [workflow](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/workflow.py#L174) 已明确允许 ticket 与迟到取消交错。

最小修订：把 `--confirm` 定义为操作者对**这个精确原 Experiment 的原本地 fence**的明确授权，并写明它可能抑制其 runner／归档及尚未创建的 release ticket，本命令不确认这些资源已停止，也不撤回已有 ticket。“保留人工 release”只适用于未被本次显式 fence 的已完成前轮；父循环不得统一 fence 这些旧轮。回传只确认已核实的本地 fence 和锁内 job 查找结果，不回传“release 已取消／ticket 不存在”或“executor 已停止”。

验收接缝：用原 adapter／registry 验 fence 与 ticket 创建的两个顺序；fence 先则不新增 ticket，ticket 先则原 ticket 保持。另一个未选中的成功实验不能出现新 fence。已有 job 的返回值不能被升级为停止证明。这些检查可以在原本地 owner 完成，不需要为 b1 启动真实训练或扩展批准协议。

主实现者在本次评审沟通中说明，其原意也是保留未选中前轮的 release，并承认 fence 不撤回已有 ticket；这与上述源码一致，但原固定计划尚未写清。该说明不算文档已修订或实现已通过。

### R2（P2）：状态准入、并发完成与同一 fence 重试须有一致合同

受影响的是计划第16、18–19、31及35行。原 [_Submission.status](../../src/ergora/reference_training_submission.py#L120) 只读取 intent／attempt／receipt／rejection；它不取得 registry 锁。原 dispatch 在投递锁内执行远端 lookup／start，并在第176–180、204、211行独立发布 rejection 或 receipt。b1 明确不取得这个覆盖 RPC 的投递锁，因而 `prepared／unknown` 只是观察时的本地状态，不能与 native fence 写入形成一个原子状态准入。

两个可达顺序需要在合同中处理：

1. b1 读到 prepared／unknown，原 dispatch 随后发布 submitted 或 rejected，b1 再写 fence。只在写前重读一次也有同样窗口。特别是 preexisting-run／start-conflict rejection 意味着 run 归属不能据原 intent 推定；native `lookup_job` 只核完整 Experiment，不核 Temporal memo。
2. b1 已写同一 fence，但回复丢失；在途 start 随后保存 receipt。再次执行同一确认时，若仍按“只接受 prepared／unknown”先拒绝 submitted，就无法按第19、35行读回已经生效的同一 fence。实际副作用不能被新的拒绝响应表述成“本次从未阻断”。

最小修订无需增加锁协议：明确本命令是手工授权的**实验级本地 fence**，不是已验证 run 归属的取消；状态字段是本地观察快照。首次阻断若已观察到 submitted／rejected，拒绝新增 fence，分别指向原精确取消／归属对账；但并发终态可能在观察之后落盘，命令不保证全程排斥这些状态，也不得输出“未影响该运行”。对已经存在且完整 binding 相同的 fence，允许仅确认／读回原本地事实，即使本地 submission 状态后来变为 submitted／rejected；这不发 signal、不重发 start、不补造 start receipt，也不授予接管权。不同 binding 或损坏记录仍明确拒绝。

回传应区分 `submission_status_observed`、可有的原 intent SHA 与本地 fence 事实；没有查询服务时不能认证 run／父循环归属。若产品要求的是“任何变为 rejected 的实验都绝不可能被本入口 fence”的严格不变量，则上述薄接入不能满足，须另立与 dispatch 协作的原子协议并评审，不能靠一次 status 检查冒称已实现。

验收接缝：让实际 submission fixture 分别在 status 读取之后发布 receipt／rejection，再完成 fence，核响应仍准确描述局部事实；再让 fence 写入后丢回复、receipt 随后落盘，同一确认必须读回原同一 fence。原 intent／attempt／receipt／rejection 字节和 RPC 次数保持，不生成新 ID。测试不能用单线程“先改状态再调用”的例子代替上述交错。

## 已成立的调用与身份边界

|事实与原 owner|设计判断|
|---|---|
|[training._project](../../src/ergora/training.py#L197) 要求 published 和 training-optimization；[原应用提交](../../src/ergora/training.py#L217) 只在本地 prepare 期间预留 revision，远端阶段另起调用。|b1 可沿同一应用入口做 revision／manifest／confirm 校验，只覆盖本地 fence 进程；不需要新 SQLite 表，不跨 RPC 持事务。|
|[_TrainingProject](../../src/ergora/reference_training_context.py#L17) 从原注册选择 canonical execution 目录，逐件核注册投影和 control_home；`_Submission.load` 第80–101行绑定原 repo／execution／registration SHA／experiment。|保留这些校验、注册漂移先拒绝是合理首片边界；旧上下文恢复留 b2，不删 guard。原 intent 的旧 project_revision 与此次确认的当前 revision 要分别呈现，不把本地记录一致性当 run 归属。|
|[原 records](../../src/ergora/reference.py#L448) 核两份 manifest 的原字节 SHA、Binding／spec URI／时间窗、runner／job 与项目及 Git repo 关系。|无 start intent 沿 records 读原准备事实即可；不调用 start preflight，不创建 start intent，不复制读文件器。已有 intent 从冻结 observation 取 spec，不能改读当前同名 spec。|
|[原取消](../../src/ergora/reference_training_cancellation.py#L23) 要求 submitted receipt／精确 run；第120–127行另核完整初始输入和 start memo。|b1 不能冒充此取消，prepared／unknown 的本地 fence 也不补齐这份所有权证明；手工授权与未来父循环授权必须分开。|
|[原 registry](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L123) 在同锁内先拒绝 fence，再 lookup／create；fence 同锁内先 lookup 再不可变 write。|真正的新本地 job 创建具有所需顺序接缝。完整 Experiment 不同的既有 job 会拒绝，已有不同 binding 的 fence 由原不可变 writer 拒绝覆盖。不能把它改写成无锁先写后查。|
|[Activities.submit_or_lookup](../../src/ergora/data/reference/platform/upstream/temporal/perf_temporal/activities.py#L29) 首先 lookup，已有 job 则直接返回；只有无 job 才到 create。|fence 不阻止重取已经存在的 job，更不阻止晚到 workflow 出现。B4 中“不能绕过 job fence”只可指不能创建新的 native request，不能指 RPC／workflow 被阻止、取消或已结束。|
|[原 adapter 导入](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L19) 经过 `perf_temporal.client → temporalio`；`connect` 只在实际调用时读取连接／API key。|首版确实需要 `ergora[temporal]`，但不需要连接服务。固定用原本地 factory，不能按调用环境切入未验外部 scheduler。|

## 实施后的验收义务，不是本次已认证结果

- **B2 的最小改动面。** CLI 只解析；`training` 持有确认／revision 校验；`reference.training_submission` 进入原独立进程，并把新操作加入真正需要 SDK 的集合；`_Submission` 本地分支复用原 local factory／fence。不调用 `core.environment()`：该函数第77–82行会读 credentials，与本地阻断“不读取 API key”的边界不符。直接导入 adapter 足够，不调用 native client main、connect、runner 或模型。
- **路径义务不能随 frozen intent 分支丢失。** 原 adapter 的 `registry_lock` 使用普通 `.open('a')`，lookup／write 使用 native 路径；canonical execution 根本身不校验其后代。沿已有 `adapter.safe_file` 在 native mutation 前核 `training/registry.lock`、本实验的 job request 和 fence 路径，尤其已有 intent 时不能假定 records 已替它们检查。原[准备入口](../../src/ergora/reference_training_preparation.py#L140)已有这种边界；[原回归](../../tests/test_training_preparation.py#L179)覆盖 symlink registry lock。b1 应沿原 fixture 补其可达的 frozen-intent／fence 路径，不另写通用文件安全框架。
- **B3 原身份与最小失败。** 无 intent、prepared、unknown；错误 manifest／revision／缺 confirm；完整 Experiment 或 fence binding 冲突；源 spec 改变／移除时仍使用原 intent；相同 fence 重试和 R2 的状态变化；明确观察到 submitted／rejected 且尚无 fence 时不新增。只记录实际新 fence／原 job，不改变原 intent／attempt／receipt／rejection、manifest／runner／注册或 DB。缺 SDK、非 Linux 和注册漂移都应在新增 fence 前失败。
- **B4 原竞态。** 在真实原 registry／adapter 上用分进程或可控制的原调用接缝固定 fence→create 与 create→fence 两个顺序。前者拒绝新增 request，后者返回同一 job，后续 lookup 仍可能取回该 job。再把原 submission 停在最后 preflight 之后，让 b1 在 RPC 仍在途时完成 fence，恢复 RPC 后核新的 native create 仍被拒绝，而 workflow／receipt 可以迟到出现。原 `.lock` 不得被 b1 等待；不能用替身 fence 字典或只核 argv 代替真实 registry。SDK service double 与真实 Temporal 证据分别记录，不以本片关闭晚到 run 的后续对账义务。
- **成功与错误的可观察合同。** 退出0只表示精确本地 fence 已保存／匹配读回，附原 binding、原 fence 文件及完整字节 SHA、锁内 `existing_job` 或 null。`runtime_status=not_queried`、`executor_stop_confirmed=null`、`execution_success=null`；null job 不表示无 workflow、无后代或整体停止。超时／中断可能发生在 fence 已写之后，错误不能声称无副作用；只沿同一 binding 查原 fence或幂等重试，不重发 start。回传不承诺硬墙钟或完整 cleanup 成功。
- **B5 独立交付。** a2 精确发布后固定 b1 实施基线；新非 editable wheel 核实际 site-packages 导入和283参考身份，安装后的真实 SDK CLI 在无服务条件下完成本地 fence。复用已登记 Linux 分组内 submission／cancellation／preparation／必要 release 接缝，不新增重复 CI job；只为独特交错补回归。保留原 lost-ack 和取消保护，按本片最终差异运行必要原检查，再执行自身原模板、新 fresh-context 两轴及自己的适用 CI。无须为纯计划评审运行这些产品验收。

注册漂移后的旧上下文／授权恢复、不可续期 deadline 与试次、完整 clone／worktree／runner／archive／MLflow／后代停止、父循环当前活动轮所有权、双向 Temporal 容量和完整结果保存仍分别属于 b2／b3／c／d。当前薄 primitive 不解除自动派发禁令；Kernel 专家继续保留，未修改提案路径或目标业务项目。

## 本次实际检查与边界

本次只做静态读取、固定计划 SHA／字节核对、相关原源码相对 `d3c90e7` 的 diff 核对、调用／持久／锁顺序检查，以及本报告的本地链接和空白检查。只新增本报告；未修改计划或产品，未运行测试、安装、模型、训练、GPU、服务、网络、资源平台、提交、推送或其他外部写入。R1／R2 为原固定计划的开放问题；其余清单是后续实现必须出示的证据，不是额外已发现的产品缺陷或已通过项目。

## 2026-11-15：r2 修订合同复核

本节由同一独立计划 reviewer 追加；上文 r1 的14,820字节全文保持，原 SHA-256 `fcc4149b5540b6b62fa7e67e4670299e07aedddd9a169c2643e725bc4ba674b7`。原 r1 的开放结论保留其历史范围，下列结论只覆盖修订后的实施前合同。

本次完整复核[修订计划](../plans/2026-11-15-training-start-fence.md)及固定副本 `.ergora/checks/training-start-fence-planning/proposed-plan-r2.md`／`.json`：计划与固定副本均为8,064字节，SHA-256 `3bc5d3761fee70772d913094708baa66de9333733d922cc0e231167fdcd49aaa`。JSON 与计划第3行均将 b1 实施基线固定为本地已存在的 `1b58e929aaf495c16f448454c78de23718786ae9`。对照 r1／r2 完整差异，并复核原 submission 的状态／投递／回执、native registry 的 create／fence／release 源码；这些相关原 owner 从 `d3c90e7` 到新基线没有变化，读取时也无相对新基线的工作树差异。本次不核 a2 的远端 Ref、实现验收或 CI 终态。

|评审轴|r2 结论|开放设计项|
|---|---|---|
|需求符合性|**approve，限实施前合同**。R1／R2 的最小修订已落实；手工实验级本地 fence 的效果、状态快照、幂等读回与未确认事实可以沿原 owner 实现。|0，R1／R2 设计关闭。|
|可维护性|**approve，限实施前合同**。继续复用原 records／load／status、独立进程、本地 factory、registry 锁与不可变 writer，没有为修订引入第二状态机、锁协议或通用框架。|0。|

|原问题|修订证据与原源码边界|复核结果|
|---|---|---|
|R1：实际效果与 release|计划第15、23行明确 `--confirm` 授权精确 Experiment 的本地 fence，包含 runner／归档观察取消与尚未创建 ticket 的 release 阻断；已创建 ticket 不回滚，未选中已完成前轮保留人工 release。第19行不推断 ticket／run／停止事实，第32行列出两个 ticket 顺序和未选中实验检查。这与原 adapter 第167–171、201–205行及 executor 的 fence 消费关系相符。|关闭。没有继续承诺被 fence 的实验仍可 release，也没有把抑制未来 ticket 误说成撤回已有 ticket。|
|R2：状态竞态与丢回复恢复|计划第16行将首次状态准入限定为观察快照，明确可后落 receipt／rejection；第19行允许已有同 binding fence 在终态后确认／读回，且不 start／signal／补 receipt／授予接管权。第31行要求实际状态交错，第35行保留 fence 已写但回复丢失的可能。原 status 与 registry 并非共同原子事务的事实得到保留。|关闭。首次阻断的观察与已有本地事实确认已分开，不再要求无投递锁实现全程排斥 submitted／rejected，也不再以迟到 receipt 否认已生效 fence。|

计划第18、21行还明确补上 native mutation 前的原 `safe_file` 路径检查、SDK 要求和禁止调用加载 credentials 的 `core.environment()`，与原导入／进程边界一致。第32行准确区分晚到 workflow／receipt、新 native request 和既有 job lookup；不承诺 fence 阻止晚到 workflow。第19行的退出0与 null 停止／执行字段只确认本地事实，符合本片证据范围。没有发现需要追加的阻塞合同修正。

上文 B2–B5 仍是实施验收义务：同 binding 的已有 fence 不能被报告成“由本次调用新建”，幂等分支仍须核原注册／control、原 intent 身份、完整 Experiment／job 与 fence 冲突；真实 registry 两个 create 顺序、ticket 顺序、RPC 在途和迟到回执交错须以实际接缝验证。计划列出这些检查不等于它们已通过。本片仍无父循环授权，不能将这个手工 primitive 直接用于接管运行；b2／b3 的旧上下文恢复、原授权、不可续期预算和完整资源停止，以及 c／d 的服务／CPU 循环验收均未关闭。

本次只追加本节，并核固定字节／SHA、相关源码差异、本地链接、行号范围、原 r1 前缀及空白；未修改计划或源码，未运行测试、安装、模型、训练、服务、网络、提交或外部写入。a2 自己的 CI 与原终核没有在本次认证，计划第3行的后继产品发布限制保持；本节的两轴 approve 不能当作 b1 实现或发布通过。
