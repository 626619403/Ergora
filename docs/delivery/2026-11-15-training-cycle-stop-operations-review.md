# b2b：训练循环并发停止操作独立审查

日期：2026-11-15。审查者：fresh-context独立Agent `training_cycle_stop_operations_product_audit`。未继承实现对话；依据原始要求、批准设计、实际源码／调用者和原始验收证据审查。权限限于只读检查、小型只读探针和本报告写入；未改产品／测试、安装、提交、联网写入或重跑昂贵suite。

|审查轴|最终本地结论|开放问题|
|---|---|---|
|需求符合性|approve：满足本片内部operation及独立停止fan-out合同|0|
|可维护性|approve：原owner、依赖方向、资源生命周期与测试接缝适当|0|

结论只覆盖下列固定候选和本地证据，不表示前置CI、普通发布或本片自己的CI已闭合。

## 固定范围

基线为`877e1e4f7397731915c36b82f335efeaab3854dd`，分支`refactor/architecture-foundations`。证据根为项目内私有`.ergora/checks/training-cycle-stop-operations/`。先审查原`review-scope-r1.json`、冻结文件及tracked diff；最终逐字核对`review-scope-r3.json`、`review-scope-r3/`、当前八文件及`review-tracked-r3.diff`。r3只在r2七份完整文件之外追加当前架构的一段说明，原七份字节保持。

最终八文件为`docs/PLAN.md`、`docs/architecture/current.md`、[实施计划](../plans/2026-11-15-training-cycle-stop-operations.md)、[交付记录](2026-11-15-training-cycle-stop-operations.md)、`src/ergora/reference_training_worker.py`、`src/ergora/training_execution_protocol.py`、`tests/test_training_submission.py`及`tests/fixtures/training_cycle_operations.py`。本报告属于同片审查记录，不在上述实现清单内。最终scope为1,473B／SHA256 `9f933fc6333a201362c7547b3f1ab0115ff08a4d33d19f05897fb2ef189906ad`；tracked diff为46,559B／SHA256 `6062d9fa4b24407b7f6ab511129592c70061b3df3ef1fec38417941a63906d93`，与当前Git差异相同。

已读取根、源码与测试`AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)、[批准监管设计](../plans/2026-11-15-training-cycle-stop-supervision.md)、ergora-codebase-quality的风格／模块／测试参考和maintainable-project-delivery独立审查指引。另沿原`_Submission`、`_TrainingProject`、`CycleAdmission`、`ExecutionRecords`、budget／execution／cancellation／release、`processes`、`budget_clock`及所选fixture核实际调用和恢复路径。

## 产品与结构核对

- `training_execution_protocol.py:170`的请求检查绑定完整operation／父进程身份、授权SHA、模式和ordinal。冷inspect只接受null input／snapshot及固定1至60秒BOOT截止；其余模式检查原授权canonical SHA、完整clock／policy并使用同一`budget_clock.remaining`。H随后重读原件、比较完整snapshot，payload本身不授予执行权。32 KiB请求／结果及65,536B stopped封套超限拒绝；原budget的codec和容量不变。
- `reference_training_worker.py:26`将spawn、stdin、两条读取和wait各放入异步task。父侧只处理内存、内核身份／clock及异步管道；没有State构造、业务文件、锁、fsync或同步wait。独立owned task和shield保留实际spawn及handle；取消请求停止后仍等原task完成，不把future取消当回收。缺帧、坏帧、pipe错误、退出码及已尽clock均保留unknown。
- `reference_training_worker.py:265`在产生H前安装TERM／INT处理并核原父身份；两类截止均实际进入原`processes.run(supervised=True, stop_requested=...)`。每个S只监督一个H及其后代；原run返回后先发匹配stopped，再直接读现存结果，不再spawn。父侧只有匹配首帧才可在同一截止已尽时kill S；没有以S退出码替代H子树停止证明，也没有第二个reaper。
- `reference_training_worker.py:150`复用原start reader和完整controller binding，核原revision／ordinal及owner的intent／authorization SHA；通知前复核原clock／父身份，再由原pidfd API核PID／start_ticks／boot_id。读取原目标与通知不调用当前installation／source validator或SDK。独立writer、逐ordinal通知、drain和执行链观察不相互等待业务存储；drain仅用原非阻塞父许可及同原件同步，不取得submission／registry／executor锁。
- 执行观察继续使用原`ExecutionRecords.load().observe(durable=True)`，完整正文留独立operation文件并给SHA，有限响应保留原typed事实。独立核r2两份实际观察文件：SHA和summary与完整正文一致，均为`not_requested`且executor停止未确认；没有因notification或owner退出伪造执行链。通知、stop可见／持久、父许可排空和executor停止始终分列。
- 独立AST核全部84个控制面模块无环；两个变更产品模块的全部既有顶层定义保持，`training_cycles`、`reference_training_budget`及`processes`与基线逐字相同。没有新产品文件、registry、依赖、source key、queue或公开入口。新增私有helpers隐藏本次身份／生命周期义务，保留在原worker／protocol即可，不需要再抽层。原六阶段合同、祖先资源／权限、旧授权／attempt slot、原clock／reaper、release和模板均保持；实际读取v3的`kernel`节点仍引用原kernel assessment及kernel专家。

## 已关闭问题

1. **R1，原r1依赖环：已关闭。** 作者首轮架构检查发现、审查独立确认cycles反向导入submission／worker形成环。将本片新增snapshot／目标读取／H用例／fan-out整体放回已有worker，cycles恢复基线字节；原架构检查未削弱，r2及安装均通过。没有复制reader或新增绕行模块。
2. **R2，安装并发测试混淆通知与清理：已关闭。** 原安装r1要求beta owner在固定12秒内退出；审查直接读取同次H原stdout，实际已`notified`且executor停止为null，原beta随后沿自身fence／cleanup完成。修正仅该测试及该fault分支：真实pidfd调用返回后记录完整目标身份，在该事件核writer／alpha仍阻塞，完整operation结束后另核两owner退出。最终安装r2通过。原产品、clock和reaper未改；原失败未覆盖。

原r1另两项新测试环境错误分别为两owner共用单Experiment替身、错误读取create结果；修正使用独立service record及实际配置，保留原完整身份拒绝。没有开放产品或维护性最低修正项。

## 实际证据与界限

- 原终态逐项核JUnit、stdout和退出码：source-r1为19通过／3失败、42.84秒；source-r2为22通过、57.23秒；source-r3为2通过、27.72秒。r2与r3两产品文件SHA相同，前后源码身份记录一致。新接缝保留原S／H／reaper，在实际fsync、目标读取、post-stopped结果读取及spawn／真实新session后代边界注入阻塞，覆盖的不是协议字面量。
- 安装r1为30通过／1失败、125.42秒；修正项在同一产品的安装r2为1通过、29.25秒。独立核`installed-r1-r2-test-diff.txt`：只改变该并发测试的观察条件及仅该场景生效的通知marker。r1其余30项包含原准入／registry／持久stop／drain、完成／大型gate／manual-release、历史读取与完整架构；保留其原终态，不宣称存在一次全31项通过的运行。最终178份测试／示例均与r2冻结副本及清单一致；r1只有这两份测试文件与最终不同。
- 实际双原budget owner的通知独立性由源码r2及最终安装r2共同覆盖。错误controller／start_ticks、缺失installation及被禁止的当前validator／H SDK导入，由source-r3和安装r1的归档目标接缝覆盖；该目标是真实受控Linux进程及schema1旧owner记录，不冒充真实训练owner。原完成／manual-release检查通过，不增加统一Temporal cancel或更改归档权威。
- 独立重核source、wheel、core及SDK安装各652份产品字节和manifest；两份安装各664条有hash的RECORD均正确。wheel SHA256为`2c90440c684ed2cb26900158fac7acfc46aa925d9a9836bebcda3a378ee20a68`，只有原worker／protocol两个产品文件与基线不同。两份原reference均283／PASS，依赖检查退出0；core无Temporal SDK，SDK为1.34.0。
- `core-offline-operation-r1.json`记录新core安装真实异步S-H inspect通过／1.059秒、父侧State／SQLite被禁止、七份原cycle文件保持。审查另用已有core-only解释器作只读探针，在temporalio缺失并禁止State构造／`_open`、SQLite及当前installation／source validator时，经原`_load`和worker `_cycle_target`重读实际alpha目标，完整ordinal／intent／authorization身份匹配；没有发送信号或写原件。
- 最终自身原结构模板`self-review-r2.json`为43.807秒／approve。独立核19份全文共501,008B、三份实际资源正文均进入真实stdin，prompt与stdin逐字相同，原result SHA一致。该回复只认证完整供稿；其后新增架构段由本次独立审查直接对照产品核验，不转作新的模型或运行结论。
- 独立核`integrity-cleanup-r1.json`中38个完整actor身份的79处原始来源引用，并再次读取实际进程身份：活匹配0、不可读取0。此结论覆盖已记录actor；不声称全机器无进程。`git diff --check`及三份相关计划／交付／架构的61个本地链接目标检查通过。

CPU／容量边界明确：实现为`2 + 2N`个效果operation，每个一个S／H；有效上限N=32时最多66个operation、132个子进程，并各自重读完整原件。父loop以50 ms让出执行，不忙等业务锁。实际并发验收只有两个原owner，没有32候选容量或延迟基准；本报告不据此提出新配额／调度器，也不作扩展性收益主张。OS确实无法及时回收时仍保留unknown及实际等待，未把截止视为停止成功。

本片可按原计划收束本地交付。普通发布仍受前置43d准确CI及原独立门禁约束，本片发布后须有自己的适用CI；本审查未联网终核它们。c1总Workflow／独立cycle服务／stop queue、c2公开交互、真实CPU两轮，以及实际GPU／业务训练质量和性能收益仍是后继责任。

## 固定发布终核

原reviewer恢复同片上下文，对固定发布`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`完成需求／可维护性两轴终核，均为**approve，开放0／0**。上述10,133B本地报告完整保留为不变前缀，SHA256为`3c316391622eafd78c82b9c1855b3fb1f06a6c0ef5baba15ef160b3367eea8b8`；本节仅追加固定发布与当前CI边界。

固定提交的唯一父提交为`877e1e4f7397731915c36b82f335efeaab3854dd`，tree为`68878094d9e8d0aab99c6aa2f6fb2fa1067dd7e4`。独立从实际Git对象核`local-commit-r1.json`的九份完整路径、blob ID及SHA256，全部一致；原记录保存九份staged blob与tree相同。相对原r3八文件审查快照，仅PLAN、本片计划和交付补入实际本地approve／状态，另加入上述原审查报告；产品、测试及架构正文未变。

从固定Git提交重新读取的652个产品文件，与原wheel及core／SDK两份保留非editable安装、manifest逐字一致；178份已提交测试／示例与最终r2冻结副本及清单相同。原安装r1的30通过／1失败及同一产品r2精准修正项通过保持各自证据身份，本轮没有重复安装或suite，也没有把后继HEAD的产品混入本片。

`push-before-r1.txt`、`push-after-r1.txt`、`push-r1.stdout/.stderr`及`fixed-publish-r1.json`记录普通推送从877e1e4快进至1b8c2ed，没有force。审查者另执行只读`git ls-remote origin refs/heads/refactor/architecture-foundations`，完整远端Ref精确返回`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`；发布的是原固定候选。

已读取前置[b2b0原reviewer的准确CI终核](2026-11-15-training-cycle-offline-reader-review.md#自己的准确ci终态核验)及其官方HTTP200原件。其证据位于`.ergora/checks/training-cycle-offline-reader/ci-b2b0/20261115T122331991398Z-{runs,jobs,summary}.json`，绑定run`43708885957`／attempt1／push、准确仓库／分支及完整877e1e4；独立核八个job和30必要步骤均completed／success，并与已提交workflow的step名称和原summary对应。原run／jobs SHA256分别为`e4b7d91c430b7990a8b8654aa80a8a67c2f0f0bdffb8248a14c652394eb759e0`、`be9687431ce3b4614f328b6e6dc0503352312ae7647f6783a7096b6fe898e590`。此前403和中间观察保留；这只关闭前置条件，不认证1b8c2ed自己的CI。

**本候选自己的准确CI终态仍待。** 本轮未查询其run／job／step，不以普通发布或前置CI成功替代自己的适用CI。当前后继HEAD`f00bfdfd15173ceb0e961681679d6d3d62254bed`及其他后继源码／未提交文件不属于本次固定发布结论。仅追加本报告，未改产品／测试、安装、重跑suite、提交或推送；v3 kernel及原训练／质量／性能边界保持。
