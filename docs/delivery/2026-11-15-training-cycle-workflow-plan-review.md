# c1：独立训练循环与总Workflow计划独立审查

日期：2026-11-15。审查者：fresh-context独立Agent `training_cycle_workflow_plan_review`。未继承实现对话；先读原始要求、批准合同、待审计划及实际源码，再读交付叙述。权限限于只读检查、小型只读探针及本报告写入；未改产品／测试、安装、提交或推送。

|审查轴|结论|阻断问题|
|---|---|---|
|需求符合性|approve，限最终c1实施计划r2|0|
|可维护性|approve，现有owner与分片方向适当|0|

这是设计层结论，足以按原授权进入c1a本地实施／验收并固定具体入口及原件职责；不批准尚未实现的API、普通operation截止算法、Workflow继续分支或产品运行结果。没有将b2b、本次SDK装载探针或设计批准转作c1产品验收。

## 固定范围与依据

源码基线及本次实际HEAD均为`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`，分支`refactor/architecture-foundations`。本次没有相对该基线的`src/`、`tests/`或`pyproject.toml`差异。先逐字核`.ergora/checks/training-cycle-workflow/plan-r1/`和`plan-r1-scope.json`，再读完整r1→r2差异，终核`plan-r2/`、`plan-r2-scope.json`及当前三文件同一。最终固定身份如下；r1原件保持：

|文件|字节数|SHA256|
|---|---:|---|
|`docs/PLAN.md`|71,108|`24afc59743d01aa193e0e4d9089cdf3e5c107cd6b34478b6a5b864b3d75362ac`|
|[c1计划](../plans/2026-11-15-training-cycle-workflow.md)|9,576|`a947549ece875b013974afceb25a93e6cb540bbb1709914c154a3aeec64f43f8`|
|[c1交付记录](2026-11-15-training-cycle-workflow.md)|2,172|`0ee5fe3622cc38c97c8e791ec5d4f3ba98360bcb327863af0daea5c98f42cbb6`|

主合同为[controller具体合同r2](../plans/2026-11-15-training-cycle-controller-contracts.md)，并核[停止监管r3](../plans/2026-11-15-training-cycle-stop-supervision.md)、[b2b计划](../plans/2026-11-15-training-cycle-stop-operations.md)及其交付／独立报告。读取根、源码、测试`AGENTS.md`与[组件变更协议](../architecture/component-change-protocols.md)，采用maintainable-project-delivery独立审查指引及ergora-codebase-quality的风格、模块和测试接缝参考。

实际沿`training_cycles`、`training_execution_protocol`、`reference_training_worker`、`reference_training_submission/runtime/execution/budget`、`training`、`training_rounds`、`reference`、`services`、原evidence reader及ExperimentWorkflow／models核调用和恢复路径；核现有architecture、submission、runtime、evidence及services测试的对应接缝。另核v3原图／资源仍保留flow、双分析、kernel assessment和独立measurement。并行出现的gates／phase-frames审查状态更新不属于本次c1设计范围；本报告未终核远端CI。

## 需求与实际接缝

- **原授权和单次机会保持。** 计划第7、25、36行沿出生schema2、原ready／revision／clock／stop及唯一attempt，未知只对账。当前`training_cycles._authorize`永久占用ID后保存原clock，schema1／2不能互换；`training._submission`在本地prepare事务结束后才调用dispatch。c1a复用这些职责，不能把总start加入SQLite事务，也不能因为无receipt再投递。
- **首次receipt竞态真实存在，计划已明确收口。** 当前`CycleAdmission.bind`在protocol第443–448行要求完整总attempt和固定run receipt；Temporal可以先执行总Workflow再由客户端保存receipt。计划第38行要求首次子start之前，仅凭原attempt和认证固定run补同一receipt，符合现有消费者，不需要放宽最后gate或接受未绑定子操作。
- **历史观察与执行gate分界正确。** 当前`lookup_controller`在runtime第61–77行核固定ID／run、RUNNING、两处memo、完整started input、type和queue。关闭后的总run仍须可对账；计划第38行保留该RUNNING gate，并要求只读查询另有状态语义、共用完整输入验证。不能直接把现有gate作为总status，也不能为支持closed观察删掉执行约束。
- **运行边界在自动派发之前交付。** 原worker的`_serve`目前只注册ExperimentWorkflow，services尚无cycle服务。计划c1b明确另一PID／loop、normal与stop独立Worker及配额，普通业务进入受监管H，c1c依赖该边界；没有用另一个Worker对象或`async def`外观替代进程隔离。复用b2b的shield／真实spawn handle、两帧协议和原reaper方向适当。
- **一轮接受仍组合原权威。** `training.evidence`实际核原accepted archive、evidence／manifest／baseline／comparator及gate绑定；`ExecutionRecords.observe(durable=True)`才给同链持久停止确认；runtime区分AWAITING_RELEASE、RELEASE_EXPIRED、INTEGRATION_TASK_CREATED和未知phase。`training_rounds.create`完整嵌入四类原观察，核固定prefix、原baseline和10MB容量。计划c1d及其引用主合同保留全部条件，不能以native SUCCEEDED、owner final、Temporal COMPLETED或索引存在单独接受下一轮。
- **原业务目标没有被换成控制器成功。** 有限已选候选顺序执行是本片范围；完整算法／依赖分析、可信baseline、实测瓶颈、有效候选和重复优化仍须沿原v3／runner／evidence路径提供。kernel专家保留，可明确判断无需kernel修改。六阶段、资源／权限、原同意／clock／start与launch slot、人工release及独立采用权没有被新计划接管。

## 可维护性与实施门槛

没有发现需要新增模块、调度器、reaper、插件总线或实验账本的实际需求。`CycleAdmission.controller_intent`已有完整expected结构，`bind`已有attempt／receipt验证；把所需纯生成／字段校验留在原stdlib owner，可服务真实producer和既有consumer。`training_cycles`只持本地用例，SDK与S-H编排留原worker，避免重现b2b已修复的反向依赖环。`reference`／services复用现有命令及Supervisor边界，c2仍是薄公共入口。

r2已将下列截止、继续顺序及本地／发布口径写成明确门槛；同reviewer直接核过新增正文和探针原件，需求／维护性两轴保持approve。这些门槛仍须由产品兑现，**不是已实现接口的批准**：

1. **普通模式的截止不能直接继承b2b停止模式。** 当前protocol第235–244行只有冷inspect固定bootstrap与其余模式原total；它尚无普通compute／control截止。c1b须在具体请求合同中固定同一操作的一次性截止，使spawn、pipe、S的`stop_requested`、H及匹配stopped后的结果读取共同受原compute remaining与control timeout约束，不能在轮询／重试时重新给完整control timeout。初始inspect保持只读固定观察截止，停止分支保持原total。以普通H读锁／fsync及post-stopped读取受阻、取消／恢复不续期的原接缝验证。
2. **c1c不能提前开启下一候选。** 计划整体与c1d已经要求完整accept和索引后才继续。c1c的初始单轮执行／恢复验收须保持后继派发关闭，直到c1d的完整原绑定、实际phase、durable stopped及不可变索引均已交付；这是分片先后关系，不能用待实施collector的替身结果作为自动继续的产品批准。
3. **装载探针与运行证明分开。** 下节证明原被pin的worker可以容纳可选SDK模块级装饰类；实际Workflow只能消费history事实及durable timer，不调用pass-through的State／存储／应用函数。产品仍须在默认sandbox、真实Worker注册、两服务与取消接缝验收；不得把整个Workflow执行改为pass-through或关闭sandbox来绕过限制。
4. **本地实施与发布状态分别记录。** 前置本地固定／独立通过可支持后继本地实施和验收，前置CI若出现实际修正则先接续并重核基线；普通发布仍逐片等准确CI和相应终核。r2第32行已明确分列这两个状态，没有把本地通过写成完整发布；不改变原发布门禁。

## 检查与限度

- 独立核三份冻结原件及scope；`git diff --check`通过，两个c1文档的3个本地链接目标存在。当前84个控制面模块按原architecture接缝规则独立AST建图，无环；这是基线／计划静态核对，没有c1产品测试。
- 用既有core-only环境直接只读导入当前源码worker成功，`temporalio`既未安装也未加载；没有创建State或业务记录。
- 直接读SDK1.34.0的sandbox源码，确认按class的module／name重导入，并从重导入类读取decorator定义。核私有r1真实“local classes unsupported”错误、r2真实HTTPRedirectHandler依赖重导入限制；没有把失败记录改写为成功。
- 核私有r3与原worker的完整差异：可选SDK模块级装饰类、SDK标准`imports_passed_through`标记原application imports；没有新增产品文件。其固定probe SHA为`2c9076101f8e0bfe07c84e72e961a3fd616a9b842ed1da89b50cbd2044e51da6`。作者记录core无SDK导入0.187秒、默认sandbox准备1.552秒；审查另从当前源码路径运行`SandboxedWorkflowRunner().prepare_workflow(...)`成功。探针的run仅返回输入，未启动Worker／Temporal server／activity／训练，不能证明确定性运行、停止隔离或两轮成功。

本次没有需要修正后才能继续的设计发现。c1a的具体producer／纯validator整理、普通操作新请求及截止、独立cycle服务／stop配额、总Workflow、完整accept／索引／容量仍须各自实际实现、适用安装验收和新的独立产品审查。c2公开交互、新可信CPU两轮、32候选实际容量、真实GPU／业务训练质量及性能收益均继续开放；本报告不预批它们。
