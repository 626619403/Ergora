# c1d M5a 前驱／native 最后门禁：独立设计审查

2026-11-16。审查者：fresh-context 独立 reviewer `cycle_predecessor_native_gates_design_review`。本次仅审静态设计及其必要实际调用点；唯一写入为本报告。未参与方案编写或 M2/M3 实施，不把作者自检、邻片测试或历史通过作为本片验收。

## 结论

|轴|Verdict|开放 finding|
|---|---|---|
|需求符合性|**approve，限所审静态设计**|0|
|结构／维护性|**approve，限所审静态设计**|0|

在下列输入和范围内未发现需要修改方案的可达缺陷。批准的是 M5 的职责划分、认证算法及后续验收设计；不是实现批准、产品验收或 schema3／ordinal1 执行开放。M2/M3 固定候选重核、是否确有 M5-P、父请求留存、完整 M1c、M5 实施和 M6 正式 V2 仍分别待完成。原用户要求的有预算、有客观质量／证据、保留前后结果的优化循环及真实两轮，不能由此报告认证。

## 输入身份与实际检查

已先读根 `AGENTS.md`、`docs/PLAN.md`、组件变更协议，再核分支／状态／近期提交；另读源码与测试目录指引、M1b 和 M2/M3 活动交付。按 `maintainable-project-delivery/references/independent-review.md` 和 `ergora-codebase-quality` 的 module-design、repository-style、test-seams 审查。主树为 `refactor/architecture-foundations`，HEAD `833966d4ba21fa7bcb6670e9908d05f058cf8fdd`；现有未提交修改是他人的进度／设计文档，未覆盖。

完整读过主审文档及三份直接前置，核过权威 wire／原测量设计的相应义务。主审文件 28,547B，开始及写报告前两次 raw SHA 相同：

|文档|实际 raw SHA256|
|---|---|
|`docs/plans/2026-11-16-training-cycle-predecessor-native-gates.md`|`8d5f84b36357a6f9ec6e524a1dc7d7af4e6ed22a6ae69e9b7ff8e32cba521044`|
|`docs/plans/2026-11-16-training-cycle-measurement-capacity.md`|`c2248b4ed7237d3419844a6ab3a69684c67a8bd3bd5602e68a7a467786374371`|
|`docs/plans/2026-11-16-training-cycle-measurement-acceptance.md`|`2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`|
|`docs/plans/2026-11-16-training-cycle-parent-request-retention.md`|`bf35924d01b665470fe5ba216f9e9e450162390498cff44dcdd5eb5ddb39bafe`|
|`docs/plans/2026-11-16-training-cycle-measurement-wire.md`|`ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|`docs/plans/2026-11-16-training-cycle-measurement-and-index.md`|`4575d4f0dae80ea0ab822c002780acfa4decafa41c882b85f1c99509d4abb72d`|

主树必要源码核对了原件、调用者、持久点和依赖，而非只看函数名：

|文件|实际 raw SHA256|
|---|---|
|`src/ergora/training_execution_protocol.py`|`fff35a4f712316678d13065538c752d3649a6f8bd11cc141caa5c2f87209225a`|
|`src/ergora/reference_training_budget.py`|`1fde5981eb63aa50dcaaae427144528ff27d2ff4bba3345bc13fe1059a441cb4`|
|`src/ergora/reference_training_execution.py`|`f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`|
|`src/ergora/reference_training_submission.py`|`9c775643b07a937690230cdb86bd19e0d6fc89fcdb092fbb50d7bc3856a7575c`|
|`src/ergora/reference_training_worker.py`|`645c68ec7c913ff17719f879142aadcd950572af84b14c204c1cb45a9d132b14`|
|`src/ergora/reference.py`|`a3c53b2f8b15954709ec068a984d3623918acd5a55e3d18ed59c41ec977bdb30`|
|`src/ergora/data/reference-manifest.json`|`1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`|
|`src/ergora/training.py`|`5f53423fd2017521b9103756de5df508e1221f1f840e021375dc3b9bb76e580d`|
|`src/ergora/training_cycles.py`|`0a96a1c14ede76510e7480299e0958d36296ba0e5895a63743e311d1a03ff110`|
|`src/ergora/processes.py`|`56c1961745b03ee4775e75f17dcb5a30a3d105e4bbd0f3fb516451e0fcd55867`|
|`src/ergora/reference_creation_process.py`|`d01e4af1e2ac41b0d18401fce9f9e0b4656347b11ea904f689c27a887c91f5ac`|
|`src/ergora/data/native-runtime/training-executor-admission-v1.patch`|`45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`|

实际检查了原 submission/runtime 测试中方案点名的接缝，包括 registry 晚到 create、execution request／launch writer、attempt 同步后 prepare source 变化、native executor 锁内 admission、SDK-free history。测试文件身份为 `tests/test_training_submission.py` SHA `d0d11c557c4982ef91b57fa3d4f8c2043707fdf46165d2b75043bb3cccaed54e`、`tests/test_training_runtime.py` SHA `4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`。本次只读其接缝，没有运行它们。

另外仅在指定 M2/M3 开发树读取必要 protocol shape/ref、worker `_round_report_binding/_round_state/_round_acceptance/_round_previous/_round_gate` 位置，核 Git HEAD 仍是 `23ad171bf8228bf80b070d6ad866f79d63986d56`，七个实现／fixture 文件尚未提交。两次末段 SHA 观测一致：protocol `a0b29a9412b2ab1b31341873e8cbeb24da0af5529ec40e541b5dd68c811e220a`，worker `83ee661f035257c4a5a55e58b1b0b7b185ff560b84350df890913d8d3f3d0c92`，runtime `280cf8699ee1b22577b85171835779369d922391c01e884bb46921b2547c7314`。这是在开发源码的定位证据，不是冻结审查输入或实施 verdict；未审该树整体 diff、测试结果或临时 API 稳定性。

## 两轴判断的依据

### 需求与兼容

1. **全链与内容身份。** [方案第52行起](../plans/2026-11-16-training-cycle-predecessor-native-gates.md#原前驱的一个本地认证算法)明确 ordinal0/null、严格版本和实际 N，从前轮 intent 的原 predecessor 逐级反向核到0；要求完整 index 前缀相等、previous_report、注释／manifest／revision／registration／共同约束和 initial anchor，而不是只验证最后摘要。观察、原 H request、helper accepted/durable 投影、start attempt／receipt、ExecutionRecords 原库存和完整 evidence.files 共同绑定；缺早轮原件拒绝，不挑较短链。与 M2/M3 的前缀与恢复义务兼容。
2. **实际最后门禁。** 主树 `CheckpointedClient.start_workflow` 在 attempt 写入／同步后再次 preflight；`BudgetAdapter.lookup_job` 的 absent 分支在原 registry 创建链内调用 `budget.require_active`；`Execution.request/admit` 在原 execution 锁内各有 publish 后 `current`；native patch 在 executor 锁内调用 callback。方案把同一认证接到这些位置，保留父共享许可、最终 stop／clock 和原锁序，不把 H 早先认证当最后许可。native 入场、attempt 后、ack 后的不同合法记录集合已明确，避免重用 unused-launch 检查拒绝自身进度或允许恢复重跑。
3. **来源／ROOT。** 原 `GATE_SOURCES` 确为25项，含 protocol、reference、processes、reference_creation_process、manifest 和 descriptor；四项 measurement 也与出生代码一致。`source_capability` 在 owner 出生时采25项，authorization 只存四项，ready 没有25项。方案明确这些时点和 ordinal0 尚无 owner 的限制，要求 pin manifest 后调用原 `reference.verify()`，最后再核来源／stop／clock，并单独检查所选安装。未要求补造授权时不存在的 manifest pin。
4. **容量与故障语义。** protocol 默认 `read_raw` 确为1MiB，M1a artifact 界为10,000,000B。方案要求每个实际 index／observation 读端显式用 artifact 界、严格 bytes、完整 raw SHA 和 LF，保留原 intent16MiB及业务32KiB界；将 M1c-R 的未可达正向动作留到 M6，不借静态 shape 关闭读端验收。原机会消耗、partial／unknown、只对账、不修文件、不重绑已出生 intent 均保留。父请求留存的已接纳失败专用流和 watchdog 是另片前置，没有被本方案悄悄替代或宣称完成。
5. **旧版本和执行开放。** schema1 手工／schema2 v1 的旧键集、首轮限制、owner1/2历史、缺安装只读和已有 result 顺序均明确保持；不通过 `>=2` 扩未来版本。M5 接认证仍保留 schema3 effect 拒绝，M6 承担正式 V2／v3 source、注册、converter/Memo/inbound/query/signal/outcome、真实 history 与实际正向效果。方案没有把内部原件或服务替身称作正式 V2／真实训练。

### 结构与维护性

- **复用位置有真实调用证据。** protocol 已是 stdlib 本地执行记录／原子持久点的共享 owner，budget、execution、worker 是不同实际生产文件。把共同纯计算放在该处能隐藏重复的前驱读取／绑定义务；worker 继续持有 State／SDK／archive采集和发布编排。`training_rounds` 顶层依赖 State／schema，不让 native 直接导入它符合现有边界。
- **ROOT 无需新增抽象。** `reference.verify()` 及其实际顶层依赖为 stdlib 路径；直接复用现有 owner 比复制 manifest walker 或新增 source 文件更小。其 `is_file`／symlink 检查与逐文件读取不构成抗敌对同用户替换的原子目录快照，方案明确了这一限制，也没有冒称原 ExecutionRecords 的 fsync＋同raw重读具有同inode全链保证。
- **没有无reader持久物或虚构双caller。** 没有新 receipt／ledger／proof 文件、注册表、第二 archive reader、调度器或通用 guard 层。M5-P 以固定上游的两个现存不同生产文件确实共用计算为条件；只有 worker 一个现存消费者时随 M5-G 真实 native caller 一起迁移，删除重复算法。这不把未来消费者或同文件调用充作独立复用。
- **检查与变更规模相称。** 现有 tests／fixtures 能暴露真实锁、fd、fsync、原 source、attempt/ack、自身窗口和恢复语义；方案要求在真正持久点故障注入，并按风险选择检查，没有为新文案、私有 helper 或同一失败重复增加矩阵。明确将源码、新安装、服务替身和正式现场分开记账。

## 尚待实施证据与限制

以上无 finding 不代表以下门禁已通过：

- M2/M3 固定、独立审查和导入后，重核实际 parser、投影、前驱算法、调用者、异常分类及完整来源表；当前私有函数签名不能冻结成新公共合同。
- 实施时确认 prepare 的既有真实范围：`training._prepare_submission` 的短 SQLite reservation 会等待本地 submission 子进程，后者另持 submission 锁。本地认证不可新增 SDK/RPC 到该范围，也不能把“协议代码不导入 State”说成外层没有数据库 reservation；现有锁／事务职责须据固定 diff 核实。
- schema3 在效果关闭时的纯正例和本地拒绝，不能证明 schema3 已经经过所有原 callback 持久阶段。M5 应记录真实可达范围；M6 须补完整正向 start/create/request/launch/native 和 attempt／ack 后失败的实际调用证据，不能由较早关闭分支的拒绝代验较晚门禁。
- 大于1MiB及 M−1/M/M+1 的合法完整原件须经实际 H/budget/context/native caller；来源／ROOT、stop、BOOT／work/window 在同步后变化时，须证实真实效果未发生且已占记录保留。全链 I/O 的实际预算成本也待测，不能新增窗口或缓存跨动作的“已认证”布尔量。
- 固定新非editable core／SDK包、stdlib-only 实际 import/hook、schema1/2与owner1/2兼容、原v1 history按影响回放、自身原结构模板和 fresh 实施审查仍需各自证据；完整 M1c 与正式 V2／真实两轮没有由本报告关闭。

本次未执行 tests、probe、history replay、安装、模型、服务、训练或网络；未查询 CI、扫描运行缓存、改源码／测试／PLAN、commit 或 push。对并行 M2/M3 产品质量、真实资源生命周期、GPU／训练质量／收益均无验收结论。唯一产物是本静态独立报告。
