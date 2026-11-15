# c1d M0：出生版本、活动 wire 与最后准入草案

日期：2026-11-16。**Draft；R1/D1 文档修订待原独立 reviewer 复审，c1c 仍待终审。** 本页只把[已审详细设计](2026-11-16-training-cycle-measurement-and-index.md)的版本／wire 接缝具体化，不自授 approve，不表示产品已实现或 ordinal1 已开放。[本页首轮独立审查](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)针对原稿 `988ee80088df07c58c5294c61c8ab2ab369b3cd151d8fd44b54503066a00fb75`（35,560B），需求轴 request-changes／R1阻断1，维护性轴 approve／阻断0，另有D1事实修正。本页末尾保留修订说明；该原结论不被作者自改为通过。c1c r5 新现场仍在验收；父任务提供的安装 runtime53、原完整 history replay、W2 pre-start／pre-request、W4 outage、W5 cancel只认证各自范围，W7准备及完整终审未闭合，其余真实结论以[现场记录](../delivery/2026-11-16-training-cycle-workflow-live-acceptance.md)为准。

## 调查身份与权限

只读调查主树 `refactor/architecture-foundations`，HEAD `df436606a7f080da494a781f86235b0e55064e65`；现场已有他人的 PLAN／c1c／Windows 文档差异，本片不覆盖。另只读 c1c 树 `.ergora/worktrees/training-cycle-workflow`，HEAD `fa78747d6c6ca62935fe6a44aa6db143c362baad`，其两项未提交改动的 raw SHA 为 worker `7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`、runtime tests `4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`。这是读到的源码身份，不能冒充未来 c1d 固定包。

主树原设计八项 SHA 仍相同：worker `d42d090b…`、protocol `b8f8c829…`、rounds `d4ca342b…`、evidence `1ffce17c…`、runtime `1183a95c…`、budget `d002c88e…`、execution `f6b4a1ab…`、cycles `07215a1b…`；完整值见原设计的调查表。另核 `reference_training_context.py` `5e46e0b5f128658f3e4dafdf8b9071b0e1cc413dafa6eacd27e641630d334ecf`、submission `9c775643b07a937690230cdb86bd19e0d6fc89fcdb092fbb50d7bc3856a7575c`、training `5f53423fd2017521b9103756de5df508e1221f1f840e021375dc3b9bb76e580d`、reference `a3c53b2f8b15954709ec068a984d3623918acd5a55e3d18ed59c41ec977bdb30`、release `bba8cd011f7aec0a79f596e7898e3daa84afa7f375c8f0394a622c4255b5ab62`、rounds schema `7a5e13cd74f17cbd96ff06420328d8e4dc91c2d84a7f419e4644e6a0c0b33109`。

采用 `maintainable-project-delivery` 与 `ergora-codebase-quality`，先读根／源码 AGENTS、PLAN、组件协议及前设计／审查，沿真实 caller 调查。本片只创建本文；不改产品、测试、主 PLAN、283参考、依赖、模板或批准策略，不运行测试／服务／网络／安装／模型／训练，不 commit/push。c1d 的能力上限仍是同一出生同意中顺序消费 1..32 个**既有**候选、同一不可续原预算；不生成候选、不 approve/release、不迁 baseline。旧 c1c run 永无 ordinal1。

## 已核 caller 与拟变更 owner

|真实路径|观察与最小改动|
|---|---|
|`training_cycles.authorize_controller → _authorize → _authorization/_controller`；`prepare_controller → CycleAdmission.intent_record`|授权当前仅 schema1/2，完整值以 canonical SHA 封闭；同 ID 不换 clock。schema3仍由同一持久发布算法出生，intent 仍归原 owner。|
|worker `_serve_cycle → create_cycle_workflow/create_cycle_activities`；c1c 顶层 `TrainingCycleWorkflow`|现有可选 SDK 装载、普通／stop 两配额和 S/H 均可复用。新顶层类、新名字注册；旧类不插 patch、多轮分支或新 command。|
|`create_cycle_activities → _CycleOperation → _cycle_operation`；start 经 `_CycleCandidate → _candidate_operation → training._prepare_submission`|H 才读取原件、采集、发布；S 的 pipe loop／SDK loop 不读大文件。collect 私有组合留在此现有 worker，无新 service／manager。|
|`_execution_candidate_operation → ExecutionRecords / runtime.lookup+observe / LocalTrainingAdapter.poll_job`|可复用四事实中 runtime/native/stop 的实际采集；原 facts 缺 `Status.evidence_sha`／`Outcome.report_uri`，新 wire 必须从原完整结果投影，不能凭旧 phase 推接受。|
|`training_rounds.create → training.inspect/evidence/submission/approval`|原 create 只采新增轮、保留旧值并调用原 schema/semantic checks；approval 是本地 `reference_training_release._Release.status`，不是 release 操作。公开 create/read 和低覆盖声明保持。|
|`training.evidence → reference.training_evidence → reference_training_evidence.inspect`|原 archive/evidence/manifest/baseline/comparator 语义唯一 owner。新 H 组合它，不复制 archive reader／comparator。|
|`BudgetedStart.source/require_active/check_controller_history → CycleAdmission.bind`；`Execution.check/current/request/admit → protocol.validate_context`|原 source/context 与锁内最后准入必须消费相同 schema3 前驱；不是只删 Workflow 的 ordinal0 guard。|
|worker `create_adapter.BudgetAdapter.create_job_if_absent/lookup_job`；protocol `native_main → process(admit=...)`|原 registry/executor 锁、父共享许可和 attempt/ack 是最后动作 gate；native 不导入 State/jsonschema/SDK、不查实时 phase。|

不新增第二调度器、ledger、可变 current-round 表、proof 文件、通用 plugin 或 archive reader。新增纯校验只因 rounds 的离线入口和 protocol 的隔离 native 入口确有不同生产 caller；其准确边界见后文。

## 严格值与出生格式

本页 `{a,b}` 表示**恰好**这些键，所有对象拒绝额外／缺失键；`null` 是显式值，不能省略。整数拒绝 bool，浮点必须 finite；digest 是完整小写 SHA256。`C(x)` 沿 `training_cycles._sha/CycleAdmission._sha` 的 canonical JSON；`R(file)` 为文件原 raw SHA；rounds 内容 SHA 仍沿原 pretty JSON＋换行算法，不能混用。路径不得 symlink/reparse、`..` 或别根，所有 artifact 位置由原身份推导。所有错误都保留原件及原机会，不靠异常文本猜 pending。

schema3 authorization 的完整顶层集合：

```text
{schema_version, kind, cycle_id, control_home, project, project_revision,
 input_sha256, registration, execution, clock, controller, measurement_sources, sha256}
schema_version = 3
kind = "training-cycle-authorization"
registration = {operation_id, intent_sha256}                 # 原 _origin 合同
execution = 原 plan.project.registration.definition.execution 完整值
clock = {authorized_at, deadline_at, boot_id, boottime_ns}    # 原 budget_clock 合同
controller = {protocol, workflow_id, task_queue, execution_scope,
              continuation, actor_id, confirmation}
protocol = "ergora-training-cycle-v2"
workflow_id = "ergora-training-cycle-v2/" + C(identity)
identity = {control_home, project, cycle_id, input_sha256}      # 与原 _controller 身份字段相同
task_queue = "ergora-training-cycle-v2"
execution_scope = "ordered-selected-native-once"
continuation = "accepted-archive-pass"
actor_id = 原 unix:<uid>:<name> 合同；confirmation = true
sha256 = C(去掉 sha256 的完整 authorization)
```

`control_home/project/cycle_id/project_revision/input_sha256` 仍精确绑定原 plan、当前 revision 及原登记。`measurement_sources` 不是可配置任意路径表；拟固定为下节的四路径映射，值为出生时当前发布包的 raw SHA。新出生须在保留原唯一 ID 前完整构造并校验；一旦保留 ID，发布失败也不换文件／模式／clock。重试只读取已存原值；不能重采 source hashes。schema3 选用显式程序版本选择参数进入原 `authorize_controller` 算法（拟 `program_version=2`；缺省仍旧 schema2），不新增独立授权 writer。公开 CLI/HTTP/UI 启用归 c2，不能因安装新代码改变既有命令的出生含义。

新 controller intent **保持原 schema1 字段集合**，六字段 workflow_input 形状不变，只由授权内 protocol／queue 值选新程序；不增加冗余 workflow_type 字段：

```text
workflow_input = {protocol, control_home, project, cycle_id,
                  input_sha256, authorization_sha256}
intent = {上述六字段, schema_version, kind, project_revision,
          workflow_id, task_queue, workflow_input}
schema_version=1；kind="training-cycle-controller-intent"
```

intent/attempt/receipt/rejection 的原完整 SHA 与字段集合不变；`workflow_type` 由严格、封闭映射 `ergora-training-cycle-v1 → TrainingCycleWorkflow`、`ergora-training-cycle-v2 → TrainingCycleWorkflowV2` 得出。runtime `_controller_history`、worker `_dispatch_controller`、实际 start options、activity source validator 都使用此同一原 owner 的选择，不各自允许一组名字。first/original run、attempt1、无 reset/continue-as-new、input/memo/queue 的原认证保持；新 Workflow ID prefix 防止新旧程序碰撞，绝不据“latest run”续接预算。

schema1 手工授权不得带 controller；schema2保留原 controller/v1/ordinal0 产品限制；schema3必须带 v2 controller。旧 ID 不能升降级、加 measurement_sources 或 predecessor。原 owner/capability/执行 request/launch/attempt/ack/stopped schema 不无故升版：它们已通过完整 intent/context SHA 绑定新字段。旧 owner 的 `GATE_SOURCES` 精确键集不能被新 reader 全局放宽。

## source inventory：实际依赖与待审增量

拟保留原 capability 的固定 25 项 `GATE_SOURCES`，schema3 出生另冻以下 **四项**：

```text
measurement_sources = {
  "training_rounds.py": R(...),
  "reference_training_evidence.py": R(...),
  "data/schemas/training-rounds-v1.json": R(...),
  "reference_training_release.py": R(...)
}
```

前三项是已审方案的缺口；第四项是本次沿 `rounds.create → training.approval → reference.training_release(operation="status")` 查出的真实生产依赖。首轮 M0 独立审查已静态认可四项 inventory 和下述 ROOT 核验方向，此认可不是实现／运行结论，也不消除报告的R1阻断。其消费者是 collect 前后 source 检查与原 native/source 最后 gate。即使 local approval 不参与接受条件，其代码仍参与采集、索引并在有 write 权的 H 子进程加载，不能把它当不存在。只允许原 status 路径，观察 approval 变化不触发 approve、receipt 创建或 signal。

|依赖组|真实入口与覆盖方式|
|---|---|
|原25项|protocol 的 `GATE_SOURCES` 已覆盖 worker、protocol、budget/execution/submission/runtime/context/cancellation/history、training/reference/cycles、registration/contracts/State、asset/definition、clock/process/creation、包入口及原 manifest/native descriptor。新 H 以各原 candidate owner 的 capability 核原值；不能重建旧 owner 来采新值。|
|上述四项|schema3 授权固定值；H 采集前后、index 同步后、后继 intent 出生前、budget/source/context/native 最后 gate 均比较当前字节。`C(measurement_sources)` 给投影绑定完整原映射。|
|包内原283参考|`training.inspect → reference.training_files → _training_reader` 的 PYTHONPATH 使用包内 `reference.ROOT`，不是所选安装；`reference.validate_installation` 不验证这套 ROOT。schema3 H 接受前后须调用原 `reference.verify()` 对 pinned `data/reference-manifest.json` 中全部283原字节核验。native 最后 gate也核相同原 manifest 身份所指的完整参考，不以安装核验代替。此为本页新增接线义务，未实测。|
|所选 native 安装|沿原 `reference.validate_installation(training=True)`，原 descriptor/overrides、解释器、core/config/state 与原 capability；`perfctl/baseline_ok`、原 adapter、比较器及 perf_temporal 来源继续由此原安装身份覆盖。|
|业务原文件|原 plan/registration/manifests/baseline、intent/context、execution链、evidence.files 全映射、各 prefix 文件均按各自 raw/semantic 合同核原值，不是 Python source 路径白名单。|

`reference.verify()` 和安装／原 source 检查都消费同一 operation/work deadline，不能在过界后给新执行许可。若最小纯算法提取保留在 protocol，无需第五新路径；若实现再引入持有接受权的未 pin 代码，先扩审固定表。原25项 owner capability 在各轮出生时形成，四项 measurement inventory 在授权时形成；本文不把两者混称“全部代码在授权瞬间被冻结”。c1d 新安装与冻结输入还须保证 worker 服务在单一固定产品身份上运行。

## 新 Workflow 与活动名字

定义名 `TrainingCycleWorkflowV2`，新 query/outcome protocol `ergora-training-cycle-workflow-v2`、schema_version=2；signal 保持 `request_stop`、query 保持 `status`，请求／结果由新 protocol 区分。新类在原 worker 顶层、同一可选 SDK 装载中注册，保留默认 sandbox；core 无 SDK 导入保持。原 normal／stop 进程与并发配额共用，不新增服务。

|action|精确 SDK activity 名|队列|唯一效果|
|---|---|---|---|
|start|`ergora.training_cycle.start.v3`|`ergora-training-cycle-v2`|每候选至多一次原 start offer|
|reconcile|`ergora.training_cycle.reconcile.v3`|同上|仅原 start 对账|
|request-execution-or-observe|`ergora.training_cycle.request-execution-or-observe.v3`|同上|每候选至多一次 request|
|observe-candidate|`ergora.training_cycle.observe-candidate.v3`|同上|只读原事实|
|collect-round|`ergora.training_cycle.collect-round.v3`|同上|每候选至多一次可能发布 index|
|reconcile-round|`ergora.training_cycle.reconcile-round.v3`|同上|现存确定 artifact 同步／重读，永不 create|
|stop|`ergora.training_cycle.stop.v3`|`ergora-training-cycle-stop-v2`|原独立 stop owner／唯一 stop command|

活动用 v3 是因为 c1c 已真实使用 request/observe 的 **activity v2**；Workflow/program v2不等于 activity v2。这里不增加无人调用的 inspect.v3：V2 第一个普通 command 是 observe-candidate.v3，内部仍复用已有冷检查 H。旧 inspect/start/reconcile/stop.v1 和 request/observe.v2 的名字、request、result、queue、ordinal0 guard 均保持。运行服务可把新旧普通 queue／stop queue 分别放入原两配额，但实际注册拓扑和容量仍须新安装验证；不能因名字写进表就称已部署。

所有 ordinary `maximum_attempts=1`，r5 `TRY_CANCEL`、stop `WAIT_CANCELLATION_COMPLETED`／shield 的修正保持。SDK attempt>1 在 wrapper 也只能读／对账，不因上层 retry 设置承诺安全而省略。活动 source 精确字段沿原 `{workflow_id, workflow_run_id, workflow_type, workflow_namespace, namespace, activity_id, activity_type, task_queue, attempt}`；新版本只允许新类／精确本活动名字／本 queue／相同 namespace 与固定 run。

## 新 request 与 predecessor

新 ordinary request 全部恰为 `{workflow_input, ordinal, predecessor}`；stop 活动和 stop signal 恰为 `{workflow_input, reason}`，仍不允许任意 caller 选择目标目录。`ordinal` 为 0..N−1 的 int，N 从原 plan 的1..32选择取得，不用默认32代替实际选择。

```text
budget = {cycle_id, authorization_sha256, task_queue, controller}
task_queue = "ergora-training-budget-v1"                    # 原预算执行 worker 不升版
controller = {protocol, workflow_id, run_id, intent_sha256, ordinal, predecessor}
protocol = "ergora-training-cycle-v2"
predecessor = null                                         # 当且仅当 ordinal=0
predecessor = {prefix, acceptance}                          # ordinal=k>0
prefix = {directory, sha256, bytes, rounds, last_round_sha256, initial_anchor_sha256}
acceptance = {observation, source_operation_id, candidate, submission,
              execution, runtime, evidence, common_sha256, measurement_sources_sha256}
observation = {path, sha256, bytes}
candidate = {ordinal, experiment_id, manifest_sha256, project_revision, registration_sha256}
submission = {intent_sha256, workflow_id, run_id, spec_sha256}
execution = {owner_sha256, record_sha256, raw_inventory_sha256}
record_sha256 = {request, launch, attempt, ack, stopped}       # 五项全部 digest；不能只 pin stopped
runtime = {namespace, kind, phase, job_id, binding_sha256,
           memo_sha256, evidence_sha, report_uri}
evidence = {evidence_sha256, gate_report_sha256, files_sha256}
```

prefix 的 directory 为原 cycle `controller/rounds/<k-1>/`，bytes>0 且≤10,000,000、rounds=k；其他 ordinal 的目录不合格。initial_anchor_sha256 是 `C(report.initial_anchor)`，last_round_sha256 是原 rounds 内容 SHA。完整 index 与所有旧 prefix 保存在原处，不塞进 SDK。

acceptance.candidate.ordinal=k−1，其他候选／manifest／revision／registration均从完整原 plan、原 start intent、原 index 最后轮核出。submission 精确指原 start receipt 的固定 native Workflow/run；spec_sha256=C(原完整 Experiment input)。execution 的 owner／五记录摘要用原 `ExecutionRecords.sha`，raw_inventory_sha256=C(其完整 raw_sha256 映射)，映射在 observation 原件保留，包含原start intent/attempt/receipt/native request等，不靠五个 semantic SHA 代替 raw。

runtime.kind 恰为 `status` 或 `outcome`。status 只接受 RUNNING／非terminal／AWAITING_RELEASE，`evidence_sha` 必须等原 archive evidence SHA、`report_uri=null`；outcome 只接受 COMPLETED／terminal／RELEASE_EXPIRED或INTEGRATION_TASK_CREATED，`evidence_sha=null`，`report_uri` 必须精确等 `Path(原 native result.gate.report).as_uri()`。原 `reference._training_records` 已校验该路径恰为本job的gate-report.json及其raw SHA，原 `LocalTrainingAdapter.collect_and_gate` 正是用此路径形成 GateDecision.report_uri；不能编造 recorded_gate_report.report_uri 字段。`memo_sha256` 是原 intent memo 中的完整 start intent SHA；binding_sha256=C(完整 Binding)，namespace 与真实SDK及父一致。不发明 Outcome.evidence_sha。H另核原 native SUCCEEDED、job完全相同；这些接受谓词由完整 observation 对照原事实，不是可由调用者只填上述常量的证明。

evidence.gate_report_sha256=C(原 recorded_gate_report)，files_sha256=C(原 evidence.files 完整映射)，evidence_sha256=archive content address。common_sha256=C(从原 manifest按 `training_cycles._COMMON` 取出的完整键值对象)，不含人工分数或重新评分。measurement_sources_sha256=C(授权内完整四项映射)。这些摘要的真实消费者是 H 的前驱再认证和 protocol 的 source/context/native 本地一致性校验；详细值、raw文件列表、原四事实保留在 observation，不新增一套摘要算法或 artifact-wide 认证主张。

observation.path 必须是同一 home `operations/training-cycles/<source_operation_id>/helper/observation.json`，source_operation_id为原32hex operation ID；H在发布原结果前写完整原件，下一活动重读此准确引用，不扫描 latest。acceptance 只有完整正面条件齐备才非 null；acceptance 本身不含 prefix，避免自引用／重复序列化。predecessor 的两部分在同一 H 接受中一起核出。新候选原 start intent 保存完整 predecessor，原 context SHA、owner、request 链自然绑定它；之后各次request/observe传回同值，不能换一个新观察投影“修复”已出生 intent。

## 新 result：固定封套、原 facts 与测量状态

所有新活动返回同一严格封套，stop 也不把旧 v1 结果误当 typed cycle stop proof：

```text
{schema_version, protocol, action, status, workflow_input, controller,
 observation, inspection, operations, runtime_status, facts}
schema_version=3；protocol="ergora-training-cycle-activity-v3"
status="observed"|"unknown"；action=上表之一
controller={workflow_id,run_id,intent_sha256}|null
observation={total_remaining_seconds,boot_id,boottime_ns,observed_at}|null
facts=null | {source_operation_id,budget,candidate,submission,execution,runtime,native,
              request_outcome,selection,measurement}
selection={count,common_sha256,measurement_sources_sha256}
measurement={measurement_state,index_state,continuation_ready,prefix,acceptance}
measurement_state="pending"|"accepted"|"rejected"|"unknown"
index_state="absent"|"published_unconfirmed"|"durable"|"unknown"
continuation_ready=bool；prefix=null|上述 prefix；acceptance=null|上述 acceptance
```

`inspection/operations` 沿原 `_activity_operation_result` 的精确记录 `{operation_id,mode,ordinal,operation_stopped,supervisor_returncode,result}`，result仍为原有互斥 `ref` 或 `inline`；完整保留，超容量真实拒绝，不裁前几项。`runtime_status`沿原查询状态，不用于替代四事实。无法取得可信事实时 facts=null、status=unknown；Workflow不读 ref 来补事实，只消费H已经形成的 typed inline 值。

facts 的原八字段沿 c1c `_consume` 精确嵌套合同：budget的七字段、candidate的六字段、submission的六字段、execution的六字段、runtime的八字段、native的两字段、request_outcome及source_operation_id均保持；只是 candidate.ordinal跟随本轮，不能仍硬编码0。新 `selection.count` 固定真实N，另外两个摘要固定完整common／出生四项映射；Workflow跨所有轮不允许它们变化。这是总循环终止和跨轮合同的实际消费者，不 inline 原 plan或source全表。

collect/reconcile-round 必须返回本次 H 已复核的 facts，不能让 SDK wrapper借前一个活动的正面 facts 给新artifact盖章。只有 status=observed、measurement_state=accepted、index_state=durable、完整正面接受谓词和最终 gate 都齐备时 continuation_ready=true，且 prefix/acceptance均非null。其他任何组合不得前进。accepted测量但durability未确认可以保留 measurement_state=accepted、published_unconfirmed、ready=false、acceptance=null；这不是后继授权。原 gate明确false/FAILED为rejected；缺事实／坏源／RPC丢回复为unknown；确实处于原非终态或等待reap才为pending。不能仅从 COMPLETE、文件存在或父SDK成功填 accepted。

start/reconcile/request/observe 的 measurement 缺省是 `{pending,absent,false,null,null}`（若已有本轮固定artifact，只可报告实际只读状态）；它们没有 index 发布权。stop 的 facts=null，cycle级 stop_durable/admission_drained/executor_stop_confirmed保持null／needs_reconciliation；不能把 `operation_stopped` 汇总为执行器停止证明。

V2 status/outcome 精确为：`{schema_version,protocol,workflow_id,run_id,input_sha256,authorization_sha256,ordinal,selection_count,confirmed_rounds,prefix,phase,outcome,observation_count,total_observation_count,start_scheduled,request_scheduled,collect_scheduled,last_normal_activity_id,stop_activity_id,stop_activity_status,last_facts_operation_id,last_signal_rejection,candidate_executor_stop_confirmed,stop_durable,admission_drained,executor_stop_confirmed}`。三项cycle stop证明仍null；prefix仅最后已确认引用，confirmed_rounds不因目录出现而增加；最后一轮后ordinal保持N−1、confirmed_rounds=N。phase复用c1c控制阶段并增加 `COLLECTING_ROUND/RECONCILING_ROUND/CYCLE_OBSERVED`，正常终点outcome=`selected_rounds_observed`；失败仍needs_reconciliation。每轮计数和三次机会布尔按本轮显示，total_observation_count不归零。不得在query累计32份完整结果或给收益／质量结论。

## H observation、丢回复与唯一发布

拟在原 operation 的 observation.json 保存严格 `{schema_version,kind,identity,activity_context,predecessor,selection,facts,runtime,native,execution,evidence,prefix}`，schema_version=1，kind=`training-cycle-round-observation`。identity为原完整 operation identity，activity_context为原完整三字段SDK context；runtime/native/execution/evidence为原 owner 的**完整**结果（不是新 archive schema），facts恰为原八字段 `{source_operation_id,budget,candidate,submission,execution,runtime,native,request_outcome}`，selection另存完整三字段投影，prefix为本次artifact pin。该文件不内嵌 measurement/acceptance及自己的 ref，避免循环摘要；index正文也不复制。完整 source／evidence.files／ExecutionRecords.raw_sha256在这些原值中可重核。predecessor只含此前轮的接受引用，不含此前观察正文；递归按固定路径最多31层，不能把每轮完整观察内嵌到后一轮。

**R1 修订提案：单文件完整编码与10,000,000B合计界。** 不改上面的单文件shape／ref，不拆隐式附件。原collect私有实现一次构造完整对象，以现有stdlib JSON路径编码为 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'`；UTF-8无BOM，末尾恰一个LF，无NaN/Infinity，字段不裁剪。`observation.bytes`及raw SHA都量／散列这份**包括LF**的最终完整字节。磁盘观察的准入上界直接沿原artifact界 `M=training_rounds.MAX_INDEX_BYTES=10_000_000`，不是由各reader上界相加推导，也不保证每个合法原观察都能放入。为隔离native import，拟在protocol现有cycle.json的10MB合同旁命名同值常量 `CYCLE_ARTIFACT_BYTES`，rounds公开 `MAX_INDEX_BYTES` 保持同值alias，worker与native均直接用protocol的同一个值；不得在native误用 `read_raw` 的默认1MiB。这只集中原数值owner，不增配置项或新模块。

|新观察内完整值|实际生产来源与原界|是否重复及消费者|
|---|---|---|
|identity/activity_context/predecessor|原S/H `request.json`；整个request原本≤32KiB，已含10字段identity、完整三字段SDK context及前驱引用|本文件不复制整个snapshot／plan／原intent；只存上述完整值。predecessor只嵌引用／摘要，正文不递归。native核原H request和前轮intent同一身份。|
|selection/facts|本次H已有内存中的固定三字段selection和原八字段facts|summary与下面完整原结果的少量字段有意重复，供Workflow事实与原结果交叉绑定；不把measurement/acceptance或自身ref嵌回文件。|
|runtime|原 `reference_training_runtime.lookup/observe` 对固定子run形成的完整 Status 或 Outcome 结果；当前直接SDK查询没有可据字段数推出的本地字节界|保留完整原值，包括实际 status.evidence_sha／outcome.report_uri/detail。以新**整个文件**界拒绝大值，不另创runtime字段配额或截detail。|
|native|原 `LocalTrainingAdapter.poll_job` 的完整 `asdict` 结果；与本次固定request/job绑定|job/state在facts有摘要，原结果完整保留；同样由整个文件界决定能否发布可接受ref，不另限字符串。|
|execution|原 `ExecutionRecords.load/request_record/observe(durable=True)` 的完整返回对象|原五执行记录／owner等各沿1MiB reader，原start intent读取可达16MiB；但该intent正文**不在observe返回值中再次复制**，返回的是owner、五records、完整record/raw库存及durability事实。所有原字节仍在原chain文件；native按完整库存重读原件。不能拿16MiB单文件界充当本观察界。|
|evidence|原 `training.evidence(artifact=None)` 经 `reference_training_evidence.main → _native_bytes(...,8_388_608)` 的完整返回值|完整archive元数据及files映射保存；不读取全部artifact正文、不删较大的合法files。与index最后轮native.evidence逐项交叉核对，index正文仍只在原rounds文件。|
|prefix|本次原rounds.read及同inode/raw同步重读后形成的六字段pin|只保存完整pin，不复制≤10MB累计index；read端必须重读该准确原artifact和所有已确认prefix。|

写端H对完整最终raw做**一次合计判断**。同一operation的 `helper/observation.json` 用原不可覆盖 `xb` 保存完整raw：若 `len(raw)>M`，此文件只是明确不被准入的未发送原材料，保留完整字节和所有原reader/chain/index文件，不产生acceptance/ref/ready，不把前M字节当观察，也不改写文件凑界。H给原S返回容量失败；若写原件本身失败／被原deadline终止，保留已有原件并给unknown，不能声称完整观察已保存。若 `0<len(raw)<=M`，H同步该同一文件及原operation目录链、同inode/raw重读后才构造ref；同步／重读也消费同一原window，超界不是加时理由。

所有H前驱再认证、`CycleAdmission.bind/BudgetedStart.source`、`validate_context/Execution.current`和native读同一ref时都显式用 `protocol.read_raw(path,M)`；先核普通文件／同根固定路径、`0<ref.bytes<=M`、实际完整字节数及raw SHA，再用原 `protocol.decode` 解码和严格shape／原事实绑定。读端不重排字段／重新pretty编码来比较raw SHA，不使用默认1MiB，不扫描附件、不以当前编码重写原件。过M的保留诊断文件没有合法ref，直接拒绝；接近M的合法文件也不因reader少读而“通过”。该合计界是一项保守的c1d可表示性限制，原evidence/chain/index各自支持的完整范围不被上游单字段限额改窄。

### 完整wire编码：实际owner与拒绝时机

10MB观察文件不能证明32KiB投影可发送。下面每一关都检查本次**最终完整表示**；本页不承诺任意路径长度／reason／原runtime值都可装下，也不以固定字段数推出容量证明。只有逐关实际通过才有可接受结果；任何关整体拒绝后均无新效果机会。表中owner是真实已有函数；对新wire的接线、完整材料日志和明确标出的新版本guard均是未来实施义务，不称当前旧代码已经完成。

|最终表示／实际owner|执行时机和完整计量|超界后的原件与效果|
|---|---|---|
|Workflow started input／dispatch H `_dispatch_controller`|新版本在原claim/start发送前用该连接的 `client.data_converter` 编码完整六字段input，量实际 `Payloads(payloads=encoded).ByteSize()`≤32768；memo沿原同一converter编码原intent SHA值，并量含完整key/value的实际Memo protobuf≤2KiB。attempt-before-send保持，claim后任何失败也不返还|保留原controller intent/input/memo及原claim/receipt，拒绝完整start；不改短home、丢SHA或换run。此新版本检查要接原owner，不能冒称当前旧dispatch已有它。|
|ordinary request／V2 `_ordinary`；stop request／`_stop`；signal／`request_stop`|command前对完整 `{workflow_input,ordinal,predecessor}` 或 `{workflow_input,reason}` 调原Workflow `_capacity`，量 `workflow.payload_converter().to_payloads_wrapper([value]).ByteSize()`≤32768；signal拒绝不接受部分reason|未调度的command没有效果；保留产生该request的原history／完整前驱原件和已占用的机会。收到的signal完整input仍属原service/history材料，拒绝码不等于stop证明。|
|活动入站request／`create_cycle_activities.invoke → _cycle_capacity`|SDK已解码完整request后、任何S/H前，再用实际 `client.data_converter.encode([request])` 及完整Payloads量≤32768，含metadata|入站原request在同run history；非重试容量拒绝，绝不截predecessor后继续。|
|S/H最终request／`_CycleOperation.__init__`，S及H `cycle_operation_main`|构造完整payload后按原compact UTF-8 JSON量≤32768，含identity/snapshot/authorization四项sources/window/reason/start_context及完整activity_context；S/H各自`read(limit+1)`复核。root/context的原外层也必须量完整request，不只量新predecessor|新版本拒绝路径须沿现有错误日志记录完整未发payload及其原授权／观察引用；S已收到时另有原request.json。超界不spawn该H/root，已消费的start/request/collect history机会不退回。|
|H最终stdout／H `cycle_operation_main(False)`及S的 `_read_bytes(helper/stdout.txt,32768)`|H只输出完整typed小投影／ref，不输出10MB观察正文；stdout自身JSON格式沿原 `json.dumps(...,ensure_ascii=False,allow_nan=False)`＋LF。S量该文件**全部字节**≤32768|完整stdout原文件及observation/原chain保留；S给真实capacity失败，不从中截取能parse的前缀。|
|S最终result frame／`cycle_operation_main.frame`及 `PhaseFrames.receive`|量原compact JSON的 `{**identity,event,result}` **整个frame**≤32768，含`_stdout_ref`三字段及新投影；单个分帧LF在现有协议里为delimiter、不是JSON line的计量字节。原stopped控制帧单独保持65536B界，不能把它误当32KiB业务result|完整H stdout仍在原文件。新版本沿同一frame owner对capacity失败封套再做一次完整frame核验；失败封套也过界就不发送result帧，由原S/父进程保留材料并报容量失败／不完整unknown，不能发送超界“成功”或删identity凑界。旧frame语义不全局放宽。|
|活动完整result／`create_cycle_activities.invoke → _cycle_capacity`|所有 `inspection/operations`、同时inline的facts/measurement/acceptance、外层input/controller/budget等组装完毕后，沿原实际DataConverter＋Payloads核≤32768；stop的2+2N完整分支也整体计入，不裁末尾|原各operation的request/stdout/observation及SDK现有完整unsent-value错误日志保留。原 `_activity_operation_result`只在确有原stdout ref时使用ref，不为凑容量临时把inline换成未定义附件。整体非重试拒绝后Workflow无接受结果，不推进prefix／ordinal。|
|Workflow消费／query／outcome／V2 `_consume/status/run`|消费前对完整收到的活动封套用相同Workflow `_capacity`复核；query/outcome完整对象在返回前复核，包含最新prefix、全部状态及stop字段。不能只量facts或prefix|结果容量失败不变成测量失败类别或stop确认，不补造更小成功结果；保持最后history已确认prefix及全部已消费机会，走原唯一stop／needs_reconciliation或真实query容量错误。|

原 `perf_temporal.connection.connect` 实际使用默认 DataConverter，Workflow内使用Worker绑定的相同payload converter；此处没有新增codec/plugin配置。实际安装必须核该对应关系及所有最终Payloads；若未来开放自定义codec，须在其真实传输编码owner另立范围，不能用本页的Workflow局部计量冒称任意codec后大小。新Wire只在原cycle边界增加上述完整检查；既有native Experiment/result及archive reader仍沿各原合同，不因此统一降为32KiB或静默裁正文。

无需给各字段叠新配额：来源shape和原reader提供语义边界，单文件M及各真实最终编码检查提供完整字节边界。尤其 `facts+acceptance+operations+outer identity` 即使各自较小，也可能一起超过32KiB；这是允许的**整体容量拒绝**，不是放宽、截断或“压缩后总能通过”的承诺。静态设计固定这些分支；真实边界编码和收尾证据仍是下表M1c及后续实现项，本次未运行。

新 Workflow在 command前永久设置本轮collect_scheduled；collect活动ID固定 `candidate-<k>-collect`，只一次、attempt1。reconcile-round只能读确定性目标，缺目标也不create；即使原collect未开始／尚无H operation也不返还机会。其余ordinary活动ID仍按本轮单调计数派生，guard把collect/reconcile也计入256界。

丢SDK completion时 Workflow可能不知道原collect的operation_id；不能要求一个未知ID，也不能扫描operation目录挑“最新”。reconcile-round从实际ordinal派生原collect activity ID和确定性rounds目录，复用原 `lookup_controller`／history读取，在同一固定run中核原 `ActivityTaskScheduled` 的精确ID、collect.v3名字、queue与完整request，且没有第二个同ID效果。只读取有界原history（仍受8000/8MiB），不解析event错误文案。此为新增的原history认证接缝，**当前源码尚无，须先验证SDK事件/decode及丢完成反例**。

恢复对同一现存index重新核原evidence/runtime/stop、完整前缀及来源，然后在本次原H operation写新的完整观察、形成新的acceptance/ref。它不声称恢复了未知operation ID，也不代替原publish机会。若原artifact不存在、部分、坏SHA或与任何已确认前缀冲突，只给unknown；不删／重建／换目标。若该轮已有原 start intent，其predecessor保持旧值；新观察不能升级它。

index只由原 `training_rounds.create`（每次单个新增轮）发布；目录仍恰只有 rounds.json，旧prefix逐项等于原文件，并且previous_report.raw SHA/rounds/last-round都匹配。H取得现存fd/raw/dev+inode，沿原sync_directories同步文件及到cycle根目录链、重开同路径核同inode/raw，再用原rounds.read与实际previous原件核完整前缀。发布后同步／重读／最终原件检查任一失败，保留published_unconfirmed或unknown，不能覆盖写“已接受”。这一fd生命周期留单caller的collect私有实现，不全局改publish_directory。

## 原 context/native 最后 gate 与最小纯提取

新 `validate_budget_binding`仅按controller.protocol选择严格键集；schema2旧五字段不接受predecessor，schema3新六字段必须有predecessor。`CycleAdmission`允许2/3，但用授权版本核精确protocol；bind除原receipt／selection绑定外核 predecessor。`BudgetedStart.source`、`validate_context`与actor选择中所有当前 `schema_version==2` 分支都必须逐个落实schema3，不能统一改成“>=2”而放宽未来未知版本。完整核对面包括 cycles 的 `_authorization/_load/_status/_authorize`，protocol 的 operation snapshot／CycleAdmission 构造／budget binding／cached context／native外层父许可及actor，budget.source，Execution.check 的actor，worker中 source/type/queue/start guards 和 runtime._controller_history；root/phase内携带schema3 snapshot/context的原validator也须到达同一严格分支。schema1手工binding绕过仍拒绝。

拟在**现有 protocol**增加一个内聚的纯本地前驱校验，供 `CycleAdmission.bind`（budget.source及native）、Execution.current和worker H最后动作复用；不创立新文件／协议族。它的最小合同是：

1. ordinal0要求null；k>0要求本run／授权／原选择的前k轮完整artifact，不允许短前缀或别cycle复制件。核acceptance observation的原request/activity_context/operation身份、原H结果／文件raw引用与parent intent/receipt；此记录只是同可信项目边界内的原owner观察，不是外部签名。
2. 用原plan和前轮intent解析相同 `_COMMON`、candidate/manifest/revision/registration，核prefix完整raw与轮内容SHA、annotation和previous_report；所有0..k−1轮逐项等原已确认prefix文件。继承前轮原intent里的更早predecessor递归核下去，最多31层，不重采早轮phase；缺任何已确认原文件即拒绝，不回退较短合法index。
3. 对紧邻前轮 `ExecutionRecords.load/observe(durable=True)`，核五记录及所有raw库存等冻结值；读已停原件不要求旧owner仍活。原archive语义不重算，只核原evidence owner已接受并冻结的完整 `files` 映射原字节、原gate/evidence/manifest/baseline/comparator摘要及路径；不只核摘要字符串相等，不重新采人工approval。
4. 核measurement_sources、原capability／包内283／所选安装原身份、当前父stop与不可续clock。H另认证父RUNNING和本次紧邻前轮实际phase；native不查SDK，仅核冻结当时观察及当前原文件，不能称实时phase认证。

`training_rounds` 顶层导入 contracts/training/State且在import时读schema，native不能直接import它。最小提取方向是把原 `_check` 中**schema验证之后**的纯内容／绑定部分（原 `_sha/_comparison/_anchor` 与内容检查）移到已pin protocol的局部纯函数，由rounds._check在原contracts.validate后调用；native对H已schema验证、并以原raw SHA固定的同字节index复用纯内容检查。JSON schema验证仍只归rounds，native无需复制jsonschema。提取不改rounds.create/read公开合同、原pretty SHA或覆盖字段，不新增“trusted rounds reader”。需要先以真实离线read和stdlib-only native import接缝确认无循环导入／第三方依赖；本页未做该实现或运行验证。

完整archive语义仍由 `reference_training_evidence.inspect` 唯一拥有；纯前驱校验只核原H接受后的文件绑定，不复制 `perfctl.baseline_ok`、artifact读取或比较器。若为达上述gate需要在native再实现archive接受算法，应停止这一路实施，先审原evidence owner最小纯提取；不能“补一个reader”视为同意。

gate落点按真实动作保持：H在后继 `_prepare_submission` 前／原intent fsync后；submission在原RPC attempt及发送前后；BudgetAdapter在父RUNNING之后、原registry锁内lookup确认缺job至create返回；Execution在原execution锁内request同步后／launch同步后；native外层父共享许可与executor callback内attempt发布前、ack发布后／process返回前。各点先核同一前驱／源，再核父stop和原clock最后瞬间；不能只在H第一次采集核过。原锁序和父共享许可直到四动作实际返回不变，stop writer不等index锁，SQLite事务不跨RPC。

新内部 H operation protocol 拟为 `ergora-training-cycle-operation-v2`，identity**仍原10字段集合** `{protocol,operation_id,mode,control_home,project,cycle_id,input_sha256,authorization_sha256,ordinal,parent}`；activity_context属于payload，不在identity内。复用原所有mode并增加 `collect-round/reconcile-round`。这两个mode必须带activity_context、原snapshot/window及start_context.controller；只接受匹配新collect/reconcile activity。其余mode对新授权按新协议验证，旧operation-v1完整校验和拒绝保持。root/phase/ExecutionRecords协议不因此升级，payload仍携完整原source并由既有validator读取；若实际32KiB request编码超限则保留完整未发原件并拒绝，不改字段当“兼容”。

## 可验证子片顺序与尚未闭合项

所有子片仅是未来实施顺序；每片固定实际diff、针对其静默错误风险的最小反例，独立需求／维护性审查后才更新状态。整体仍沿原M1–M8，不让小片通过替代正式真实验收。

|子片|单一owner／前置|最小证据与停点|
|---|---|---|
|M0a wire收口|原独立报告保留；复核R1的完整单文件编码／M界／最终frame及Payloads检查、D1计数修正。四项source／ROOT／history／纯提取方向已有静态认可；c1c固定源码和真实终审仍是独立前置|由原reviewer记录修订后结论；作者不自关R1。未获结论或c1c未终审则保留全部旧successor_not_enabled，不进入多轮产品。|
|M1a纯内容提取|protocol＋rounds，行为不变|原rounds离线read/create语义及pretty SHA保持；真实native隔离import不加载State/jsonschema/SDK。单独证明后再改授权语义。|
|M1b出生与兼容|cycles/protocol/runtime/submission；默认仍schema2|新schema3同ID/丢回复不换clock/source；旧schema1/2完整原件与旧history replay；V2仅新出生可选。暂不启用ordinal>0。|
|M1c完整编码接缝|原worker/protocol编码owner；在集成collect发布／后继前验证，不以schema parser通过代替|真实完整observation在M−1/M/M+1；原reader各自成功但合计超M仍保留原件／不给ref；H stdout自身合界但加identity/_stdout_ref后过32KiB；SDK facts自身合界但加完整operations/acceptance/metadata后过32KiB；N32 stop完整结果。均由真实owner整体拒绝、无截断／无机会返还，合法小值经相同写读界可确认。实际默认converter对应关系及query/signal/outcome也核其完整Payloads；本次没有执行。|
|M2a H只读接受|worker复用原facts/evidence/chain；无index发布|四事实交错、evidence_sha/report_uri真实字段、错run/job/archive/namespace及source漂移都不ready。原reader总超时由S真实终止。|
|M3a唯一collect与durability|原worker collect、原rounds.create；前述history接缝已证|rename/fsync/同inode/原raw替换/丢reply；reconcile缺目标不create；完整prefix变化拒绝。仍保留ordinal>0产品门。|
|M5a最后gate|protocol/budget/execution/worker adapter；原intent冻结前驱|直接ordinal activity、手工binding、别run接受投影、伪前缀与缺早轮原件分别在原锁内拒绝；stop/source/clock在H检查后改变不spawn。|
|M6a新正式V2|worker新类／新活动／实际两配额注册，前述owner已接通|新默认sandbox/replay、start/request/collect机会各一次；D_work/D_total只缩、切轮不cold；每轮256、8000events/8MiB先到真实stop。此时才可移除**新版本**ordinal>0关闭分支。|
|M7/M8安装和真实链|新固定wheel、实际site-packages／冻结输入，独立审查|至少两个既有CPU候选、原runner实际数值与oracle、原collect_and_gate accepted archive；完整index/原链/history/replay/重启/收尾。无approve/release/baseline迁移；CPU只认证控制／原数值合同。|

明确未决项：①c1c新现场最终范围、固定源码与终审尚未作为本页前置闭合；②R1/D1本次编码／合计容量修订待原reviewer复审，M1c完整实际编码反例未执行；③恢复时原collect `ActivityTaskScheduled` 的真实SDK读取／decode接缝未验证；④四项measurement inventory及包内ROOT `reference.verify`已获首轮静态设计认可，但实际window／native／安装接线未实施；⑤最小纯提取的具体diff、离线兼容与native隔离未实施。②的数值／完整编码／读写owner已在本次提案中固定，不再留给实施者选择不同界；实际证据仍不能由静态设计替代。

原边界继续有效：完整SDK DataConverter＋Payloads（含metadata）、signal/query/outcome与S/H request/result各≤32,768B，memo≤2KiB；完整index≤10,000,000B、最多32轮。每个command前占本轮计数，cold仅首次、同BOOT的 `D=min(旧D,A+remaining)`只缩，所有RPC/读写/fsync/返回共用原window；没有新run/continue-as-new/reset续时钟。unknown只对账，停止／源漂移／缺文件不重授效果，原完整未发送材料保留。祖先资源、父权限收窄、六阶段和人工release窗口保持；本片不认证质量收益、统计收益或真实训练。

## 首轮审查修订说明

原稿身份永久保留：35,560B，raw SHA256 `988ee80088df07c58c5294c61c8ab2ab369b3cd151d8fd44b54503066a00fb75`。[原独立报告](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)的需求request-changes／R1阻断1、维护性approve／阻断0及D1事实修正不被覆盖。本次只修改本页，不改该报告。

- R1：固定单个observation完整compact UTF-8＋LF编码、包括LF的10,000,000B合计准入界、同一常量owner及全部显式read limit；列明原组件来源和重复情况。较大的完整合法原观察允许整体拒绝，保留完整原字节，不拆附件／加逐字段配额／截断通过。
- R1相关外层：列出每个最终request/result由谁、在何时核完整H frame或实际Payloads（含metadata），同步覆盖inline facts/acceptance、operations、identity/_stdout_ref及N32 stop。需要的新版本dispatch／失败frame检查在原owner接，不声称旧实现已具备；超界保留原件且原start/request/collect机会不返还。M1c是未来真实编码／边界证据前置，当前没有运行。
- D1：identity改为真实10字段并列全；activity_context仍为payload字段，不为文档计数新增产品字段。
- 原审已静态认可四项source、ROOT核验、原history恢复及纯提取方向，本文相应区分“设计认可”与“未实施／未实测”，不要求为同一已认可设计重复审查；R1修订本身交原reviewer复审。

本次只做只读源码／Git／hash调查与文档静态检查；没有测试或运行结论。原草案及本修订都不由作者自称approve/M0ready；c1c仍未终审，不修改主PLAN或前设计审查结论。
