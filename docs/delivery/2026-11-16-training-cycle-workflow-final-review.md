# c1c TrainingCycleWorkflow 最终独立审查

日期：2026-11-16。Reviewer：fresh-context 独立代理 `cycle_workflow_final_review`。本轮只读产品、测试和现场原件，只写本报告；未运行 runner、测试、Replayer、网络、训练、安装、服务命令或 commit。

**最终结论：需求轴（源码及本片实际验收）approve／开放 finding 0；可维护性轴 approve／开放 finding 0。c1c 首轮控制片的本轮审查与验收证据闭合。** W7新真实阈值、W8 consumer、新现场统一资源收尾和最终源码身份均已独立终核。批准仅绑定下述准确字节与范围；提交／导入／候选自己的CI和c1d接受层仍分别办理。

## 审查输入及准确身份

先读项目 AGENTS、PLAN、原始[W0–W10 要求](../plans/2026-11-16-training-cycle-workflow-first-round.md)，再读实际完整 diff／实现及必要邻 owner，最后对照交付和现场报告。采用 maintainable-project-delivery 的独立审查 brief，以及 ergora-codebase-quality 的仓库风格、模块设计、测试接缝规则。

产品树为 `.ergora/worktrees/training-cycle-workflow`，HEAD `fa78747d6c6ca62935fe6a44aa6db143c362baad`，审查基线 `c52fc0a338118a19491ad7cd458b82cf2f146a9b`。实际完整 tracked diff 只有以下两文件，401／432 行增加、6 行删除；没有新产品模块、脚本、服务配置、schema 或参考文件变更。

|材料|独立重算 SHA256|
|---|---|
|基线至当前完整 diff／`cw1/candidate-r5.diff`|`2337f7f9fda354a41ad284a0f90181636ed0aeeed1494256597a84f408a3d0e6`|
|`src/ergora/reference_training_worker.py`|`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`|
|`tests/test_training_runtime.py`|`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`|
|新非 editable wheel|`74e2f6f990a3f4125fcebd81b06f8729b24ec1a148db47a58037e49f60eacf86`|

完整读新增 Workflow 与测试，并追踪原活动 adapter、`_execution_candidate_operation`、S/H 操作与 `_serve_cycle`；核原 runtime 固定 run／memo／Binding、execution 及 protocol 的认证、最后准入与 durable stopped 所有权。没有把前片的产品验收或其他提交的 CI 当成本片证明。

## 源码需求轴

模块级条件定义的 decorated 正式类位于原被 pin 的 worker owner。唯一生产 factory caller 为 normal Worker；stop Worker 无 Workflow 且保留独立 queue／一个活动槽，预算服务仍分开。可选 SDK 仅吞确切缺失顶层 `temporalio`，应用依赖沿 SDK pass-through，正式类仍接受默认 sandbox 重导。没有关闭 sandbox、创建局部类或新调度器。

run／signal 复用原严格六字段，候选固定 ordinal0；controller run、intent、candidate、submission checkpoint、执行记录摘要、Binding 与 job 持续固定。unknown 不恢复新效果许可；start／request 的机会在 SDK command 前消耗，各最大 attempt1，原文件缺席或 completion 丢失均不能重授。v1 仅收窄 total，下一次 v2 才重新观察，不把 v1 observed 当 submitted／执行许可。

预算使用调度时刻 A 加 H remaining，后续取 min；不使用收到结果时刻 R 续窗。work／total 和 BOOT 身份各自检查，ordinary 的排队、返回、timer 与失败均消费同一绝对截止。普通活动计数包含失败且止于256；history 8000／8MiB 守界后仅保留停止路径。正式三事实终点同时要求同一 job 的 native SUCCEEDED、durable／executor stopped 和许可的原 runtime phase／terminal；任何单项都不生成 accepted、rounds、release、baseline 迁移或 ordinal1。

ordinary TRY_CANCEL 只解决 SDK 本地 handle 取消／eviction，不充作 S/H 或业务清理证据；真实 S/H cleanup 仍归原活动与 reaper。停止只发独立 queue 的一个 command，最大 attempt1、剩余 total、WAIT_CANCELLATION_COMPLETED／shield 抵抗重复取消。原 normal-first shutdown 保持 stop 服务直到 normal 实际 SDK cleanup 退出。query／outcome 不把返回的 stop transport 当作 cycle durable／drained／executor 停止；这三项和 measurement_accepted 仍为 null。

## 可维护性轴及测试价值

没有发现需产品修改的实证 finding。新增 factory 是可选 SDK 与框架模块身份的必要边界，实际生产 caller 明确；其余方法是同一 deterministic 状态机的局部算法，不是假定复用的公共抽象。没有搬入文件／SQLite／锁／native 执行或第二证据 reader；完整事实投影与来源继续由原 H owner 提供。外部封套、持久身份、单调 checkpoint、clock、容量与取消的检查各有可达失败，未发现与功能无关的防御分支。

新增测试复用原 runtime 模块和真实 SDK sandbox activation 接缝。延迟双 QUEUED、effect 丢完成、A+remaining／v1 不刷新、三事实交错、最终 facts 不能越过 stop guard、失败累计256、signal 容量／身份、重复取消与独立 stop 各保护不同的静默错误。合成 history 的有界 child Replayer 专门捕获原 eviction hang，不能由普通 activation 断言替代。该测试使用 SDK 私有 activation API，升级 SDK 时需随实际 SDK 接缝维护；本片固定1.34.0，现有使用有明确必要性。没有建议再加复制实现的断言或全量重复回归。

## 已核原件及实际证明范围

原件均在项目 ignored checks 存储，本报告使用相对位置以便核对，不作为公共下载承诺。审查者独立解析真实 history 的 activity schedule、完整 JSON payload、最大 attempt 与 ordinal；并重算所读 retained 原件的 SHA，未仅采信 control-checks 的 true。

|节点／材料|本轮核实事实|范围限制|
|---|---|---|
|W0／W10：`cw1/package-r3/`|独立打开 wheel，对 core／SDK 各663文件逐字比较 source、wheel、site-packages，差异0；wheel SHA准确；安装 JUnit53项、0失败／0错误／0skip，suite54.309秒，driver56.586秒。安装 owner 路径指向 site-packages|没有重新运行测试；283 reference、依赖与853输入冻结沿原检查原件，不混为本轮独立重跑|
|W1：`cw-live-r1/first-positive-r5/`|原 history78 events：observe6／start1／request1／stop0，全部ordinary ordinal0、最大attempt1；最后完整 facts 为 native SUCCEEDED、durable／executor true、固定子run RUNNING／AWAITING_RELEASE；outcome 为 first_round_observed_c1d_required、cycle停止及接受字段null|真实 CPU 固定整数合同；未认证训练、GPU或接受层；后续显式 cancel 测试子run应与首轮原观察分开|
|W2 pre-start／pre-request：`fault-harness-r5/runs/w2-pre-*-r5/results/`|真实 history中所选 effect各一次；失败后只读observe，pre-start无request；managed request／launch／attempt缺席。retained SHA独立重算无差|故障为显式 before-adapter SDK failure，不是物理断包|
|W2 post-start：`w2-start-r5/results/`|新源真实 history106 events，start1／request1／observe8／stop1；所选 activity失效后没有第二start，retained owner／managed链摘要独立核实；原session wait登记driver／wrapper各exit0|独立看到了原 adapter return与实际故障场景原件；统一资源收尾另核|
|W2 post-request＋W8 signal：`w2-request-r5/results/`|真实 history58 events，start1／request1／observe2／stop1，null投影保持；retained六份共同原件及最终链 SHA无差|合法signal紧接故障，本场不证明故障后继续ordinary观察；该范围由W3补足。32800B完整编码拒绝与967B outcome只认证实际信号／控制投影，不等于stop封套容量consumer已验|
|W8 stop consumer：`w8-stop-failure-r5/results/`|原stop完整return先于显式capacity-type bridge；真实history event42为stop的非重试`cycle_activity_capacity_exceeded`，stop只一次；正式outcome为needs_reconciliation／stop_activity_status=failed，cycle停止及接受字段null；原完整stop结果SHA `58a3c3cd…`、真实Replayer结果及driver／wrapper各实际wait0保留|这是原adapter返回后的typed错误消费检查，不是本场真实聚合overflow。原producer／N32容量范围仍归前片原验收；未因本场复制该矩阵|
|W3：`w3-restart-r5b/results/`|同run原history中request只有一次、后续只读observe；两个不同完整进程身份bootstrap的安装worker SHA和完整argv相同；root-interruption保留七份原件及clock，独立核最终retained链无差；helper实际wait新child0|私有settings包含driver发布的workflow_id／marker等运行字段，bootstrap raw SHA因此不同；不能称其raw settings字节不变。原授权／产品预算／原件保持，旧relative／absolute argv失败保持|
|W4：`w4-outage-r5b/results/`|真实history34 events：start1／request0／observe2／stop1，原BOOT耗尽后无managed request／launch／attempt；新collector complete，与旧r5 RPCError失败分列|精确SDK A+w及v1收窄由源码／activation测试补；现场断联提供原BOOT预算恢复反例|
|W5：`w5-cancel-r5/`、`w5-signal-r5/`|原history分别45／49 events，均start1／request1／observe2／stop1、独立stop queue；事件保留真实H阻塞、两次RPC及stop先于normal清理。retained链SHA独立核无差|cancel成功RPC数不冒作server cancel event数；某场managed stopped缺席保留，不能由parent CANCELED或wrapper退出填cycle停止true；统一资源检查仍必要|
|W6|真实正例三事实齐全；原r4 gate失败场景及新增SDK交错测试保持各自范围；源码无evidence／rounds／release调用|未以CPU正例认证所有三事实排列的现场矩阵|
|W7：`w7-history-r5/results/`|原真实阈值测试明确failed，control-checks中history guard／no second ordinary均false；history与新Replayer收尾各自保留；原r4完整10,995,598B JSON历史的新安装replay证明eviction修补范围|导出JSON大小不能替代server8MiB，此场真实阈值未命中；不得把旧history成功replay计为W7守界通过|
|W7新身份：`w7-history-r5b/results/`|实际Describe在272确认RPC后为8,766,985B；完整history364 events中的SDK task size最大8,773,754B，均超过8MiB。原cold窗口未改，首server signal早于本机原adapter返回；actual command只有observe1／stop1，reason=history_capacity_limit、无start／request；真实默认sandbox replay完成，driver／wrapper实际wait0|完整JSON导出11,844,323B、SHA `5229dc97…`独立重算一致，与server threshold分列；旧r4／r5 timing miss仍失败。真实只验size阈值，8000事件及256 ordinary精确守界由原SDK activation接缝覆盖|
|W9：`cw1/old-owner-source-probe-r5.json`及原认证owner|新安装原validator拒绝旧worker source pin，旧owner raw SHA前后不变；Workflow不写旧source／owner、不绕最后effect gate|这是原validator只读检查，不是正式server旧run恢复认证|

新CPU manifest为 `34e3c4f06912eca774dcd422f8e48df1df2e325f4c219d6f2d35eff7faff379c`、clean代码 `d04229205fc5d9f2e90617d2592812e9229a36e6`，原evidence SHA `9da94e910e9cd8fba6dce021a8cfbca0253f4d16febd3038c2bab34d981a4af8`。独立重算该evidence及其73项artifact SHA均匹配；读实际 archive/evidence记录为 passed／ELIGIBLE_FOR_HUMAN_REVIEW、baseline_matches=true、quality范围保留；不是measurement_accepted。另读oracle源码确认其逐次奇数累加算法不导入workload。8 pair、每组32整数、独立512输出精确oracle与进程耗时归一的CPU性能结果，仅归该固定CPU样本，不推广为训练、模型、GPU、P99或资源隔离收益。

自身原结构模板的 `cw1/self-review-r3-codex/` 保留实际Codex run、完整stdin／result摘要与approve；该结论范围是所供完整文本，服务与CI另验。原Claude失败不被它改写。审查者未再触发模型调用。

## 最终收尾及身份终核

W7新真实server阈值触发和W8 consumer bridge已按上述原件闭合；旧timing miss／argv／RPC及r4异常收尾保留各自失败，不以新场成功改写。W8仅认证consumer typed failure及null投影；完整容量producer的原N32／完整编码验收仍归未改的原owner与前片证据，不将新bridge写成真实聚合overflow。

读取 `cw-live-r1/{workflow-inventory-r5,stop-infra-final-r5,shutdown-final-r5,final-process-audit-r5,operation-refs-audit-r5}.json`、两份sampler终件及`cw1/live-session-waits-r5.json`。独立数出38个Workflow，33 COMPLETED／5 CANCELED／RUNNING0；原services owner stop confirmed，所有自建服务STOPPED、Supervisor shutdown confirmed／not_running。实际wrapper／driver wait保留exit0，旧r5失败driver／helper仍exit1，W3新helper的原root-interruption直接wait新child0。取消控制与资源事实不互相冒充。

增强fault sampler有647份完整身份，survivor／unknown／observation_errors均0；simple服务sampler98份只声明survivors0。本轮独立只读 `/proc` 逐一重核两组身份均absent，再对综合原件／sampler去重的759份完整身份逐一重核，759 absent、活匹配0、unknown0；没有把98＋647当作不重叠总数。该综合audit读取471份实际保留原件，不是对所有极短子进程的全程普查。另独立执行只读`ss -ltn`，7233／8233／5000无监听。

原operation audit有273个独特实际返回观察，均operation_stopped=true／supervisor_returncode0；273份H stdout引用逐份独立重算bytes／SHA，全匹配。结合已读预算根final／launch stdout、原S/H清理与executor stopped链，支持已保留现场资源收尾；不把没有回传的观察、sampler间隙、单独PID消失或SDK本地取消写成完整业务停止证明。原summary字段仍null的场景保持null。

最末再次独立重算基线至当前完整diff `2337f7f9…`、worker `7996f73d…`、tests `4b5d7ed4…`，与首表及新wheel相同。`cw1/post-live-identity-r5.json`记录HEAD `fa78747…` 与相对该HEAD工作diff `4c1b0611…`，它与相对c52完整diff是两个不同范围，不能混用。本轮另按`package-r3/frozen-inputs.json`对853份source／tests／config／CI输入逐份核bytes／SHA／执行位，差异0。无需为无变化输入重复53项或再跑模型／训练／性能矩阵。

本轮没有开放的产品finding或本片验收缺口。继续按原交付／PLAN记录本结论，固定提交／导入开发分支并验证其准确身份与自己的必要CI；这些发布动作未由本报告认证。c1d是后继独立片，ordinal1／measurement_accepted／rounds／release／baseline迁移仍未开放，真实训练／GPU及质量收益仍不在本片范围。

## 固定提交及开发树导入身份复核

独立只读Git／raw文件复核产品专树固定提交 `ec6dcbcf23d35818aa23e87b6dbb129ed8ff75a1`，以及开发分支普通merge `5b04b2b4cb4eb1c5d6899fc517cf86ecdec5536f`。前者相对fa78747只改原两文件150增加／9删除；后者相对原开发树df43660只改同两文件833增加／6删除，没有额外产品、脚本、配置或CI变化。当前未提交变更均在公开docs，不进入本次固定产品结论。

两个提交的`git show`原worker blob SHA均为`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`，测试blob均为`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`；与本报告审查、新wheel／安装和真实验收字节完全一致。ec6dcbc相对c52的完整diff，以及两个提交限定原两文件的c52产品diff，SHA均为`2337f7f9fda354a41ad284a0f90181636ed0aeeed1494256597a84f408a3d0e6`。merge提交相对c52的不限路径diff还含两条分支已有docs差异，SHA另为`9d8fe85c…`，不能把产品范围摘要写成该不限路径摘要；两提交间的差异全部是docs。

固定提交及导入后的需求／可维护性结论均保持approve／开放0。未重复测试或全审；不认证推送、远端、main合入或候选自己的CI，后续公开docs提交仍另核准确身份。
