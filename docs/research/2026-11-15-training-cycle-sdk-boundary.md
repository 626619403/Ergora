# TrainingCycleWorkflow 的可选 SDK、sandbox 与独立 worker 边界

核验日期：2026-11-15。建议沿现有 `reference_training_worker.py` 使用**可选 SDK 导入、模块级装饰类、明确子模块名的业务 import pass-through**，在新的 cycle 进程中注册普通／stop 两个 Worker。标准 sandbox 可以保留，core 也无需安装 SDK。这里有两个不能省略的后继前提：`from . import owner` 原样套进 pass-through 块并不保证 owner 被复用；长期 budget owner 的进程归属和父进程退出语义要分别闭合，短 H 的后代不能跨原 supervisor 回收存活，async subprocess 也没有公开 detach 合同。[S1][S2][S5][P1][P3]

本次只写本文及 ignored `.ergora/checks/training-cycle-sdk-boundary/`。未改产品、依赖、计划、测试或现有 dispatch 证据；未安装、提交、推送、读取凭据、启动服务、训练或模型。自足 throwaway Workflow 执行了两次**本地 SDK activation**，Worker 探针只走 Python 构造／注册，替换了连接 Rust Worker 的边界，未调用 `Worker.run()`。这些观察不认证 c1a2、后继产品 Workflow、真实队列运行、取消或 CPU 两轮。[L1]

后续另做了六组仅含惰性 OS 子进程的退出对照：本机 `ThreadedChildWatcher` 下，async subprocess 在正常 loop／父进程退出及 SIGKILL 后均存活；`to_thread(Popen)` 仅执行 OS 创建、公开 pipe 传小输入、仅 `poll` 的对照也存活。六个 root 全部按准确身份 TERM／wait 收尾。此项只补进程生命周期事实，不认证原 budget owner 的启动／授权／时钟／恢复。[L2]

## 来源与观察身份

已读根／源码 `AGENTS.md`、[组件协议](../architecture/component-change-protocols.md#执行和证据)、[c1 计划](../plans/2026-11-15-training-cycle-workflow.md)及[controller 合同第4节](../plans/2026-11-15-training-cycle-controller-contracts.md#4-workflow活动和阻塞通路)。读取起点 HEAD 为 `836179e9ff3eae0795f0c22bf4c58f0bab1ea777`，分支 `refactor/architecture-foundations`，c1a2 四 owner 差异正在共享工作树。其安装／终核结论归原片，本文没有采用在途测试作后继成功证据。

本地解释器为 Python 3.12.11，SDK 为 Temporal Python 1.34.0；core 环境 `find_spec('temporalio') is None`。实际读取的 SDK 文件 SHA、字节数和带行号摘录存于私有 `sdk-primary-sources.json`；产品来源 SHA 存于 `product-primary-sources.json`。以下引用均指本次本地一手源码，SDK 内部 API 的调用只用于探针。

|引用|源码及具体位置|
|---|---|
|S1|SDK `temporalio/workflow/_definition.py:56–99,123–148`；`worker/workflow_sandbox/_runner.py:64–164`；`_in_sandbox.py:37–78`：装饰、重新导入和重新获取定义。|
|S2|SDK `workflow/_sandbox.py:122–148`；`worker/workflow_sandbox/_importer.py:190–277,312–345,544–576`：pass-through 的作用范围、宿主导入和完整模块名处理。|
|S3|SDK `worker/_worker.py:96–125,476–508,572–596,637–664,929–972,1154–1188`；`worker/_workflow.py:184–228`；`worker/_tuning.py:344–363`：默认 runner、活动注册、每个 Worker 的 slots、生命周期及 lazy client 拒绝。|
|S4|SDK `worker/workflow_sandbox/_restrictions.py:553–572,652–706,1019–1057`：默认文件访问限制与代理对象；`service.py:405–438`：构造 service client 与实际连接的区分。|
|S5|本地 Python 3.12.11 stdlib：`asyncio/base_subprocess.py:96–129` 的 transport `close`／`__del__`；`runners.py:65–82` 的 Runner 收尾；`unix_events.py:195–230,919–980,1349–1473` 的 transport／两种 watcher；`subprocess.py:1092–1134` 的 Popen context／析构；`threads.py:1–25`、`base_events.py:1664–1678` 的公开线程／write-pipe 接缝。逐文件 SHA 与原摘录存于私有 `python312-primary-sources.json`。|
|P1|[worker](../../src/ergora/reference_training_worker.py)：顶部业务 import、`_CycleOperation`、`cycle_operation_main`、`_dispatch_controller`、`_serve`、`main`、`budget_main`。|
|P2|[cycles](../../src/ergora/training_cycles.py)：`_SCHEMA`、`_controller`；[protocol](../../src/ergora/training_execution_protocol.py)：`GATE_SOURCES`、controller intent 和 operation 封套。|
|P3|[submission](../../src/ergora/reference_training_submission.py)：`dispatch`、`run`；[budget](../../src/ergora/reference_training_budget.py)：`ensure_owner`、`own`；[processes](../../src/ergora/processes.py)：`_adopt_children`、`_reap_children`、`run`。|
|P4|[reference](../../src/ergora/reference.py)：worker 命令构造、`_training_process`；[services](../../src/ergora/services.py)：`NAMES`、`_prepare`、`control`；[training](../../src/ergora/training.py)：`start`、`_submission`。|
|L1|本次私有 `probe.py`、`source-r4.json`、`sdk-result.json`、`core-result.json` 和 `evidence-index.json`；关键原输出已列于下文。|
|L2|补充的私有 `async-root-lifecycle-r1.py`／原失败、`async-root-lifecycle-r1-recovery.json`、`async-root-lifecycle-r2.py/json`、逐例 stdout／stderr 与 `async-root-lifecycle-evidence-index.json`；此轮来源状态为 HEAD `f00bfdfd15173ceb0e961681679d6d3d62254bed`，与先前 SDK r4 的来源身份分列。|

SDK／core 探针运行前后，四个在途 owner 的 SHA 均保持下列值；`reference.py`、`services.py` 也逐字保持。另只读观察到 283 个 tracked reference 文件、该目录 Git diff 为空；没有运行安装／283 验收，不能把此观察替代其原门禁。

|在途 owner|本次观察 SHA256|
|---|---|
|`reference_training_worker.py`|`5fb2df49e3c44a8b1c5d0e576a69fdf4c778a626e542c3a841b2fc631f7dfe98`|
|`reference_training_runtime.py`|`1183a95c53a9550789983e245676a46637b5de748ddf32eb0ec5df9def46458a`|
|`training_cycles.py`|`37a9a2010377eeb99c35d87e444852d32a3ca2b14640d16e34ea4dc3e7f56fa6`|
|`training_execution_protocol.py`|`5f9c2bda1dae01a98df7cb5e722161bbcba193b997187b36cd33e778b313ce76`|

## 标准 runner 与实际 pass-through 覆盖

标准 `Worker` 的 `workflow_runner` 默认是 `SandboxedWorkflowRunner()`。注册时，`_WorkflowWorker` 对每个类执行 `_Definition.must_from_class()`，再调用 `prepare_workflow()`；后者用 fake info 创建真实 sandbox instance。`_Instance._create_instance()` 实际生成并执行以下形状的导入，然后 `InSandbox` 从**新导入的类**重新取得 decorator 定义。[S1][S3]

```python
from <cls.__module__> import <cls.__name__> as __temporal_workflow_class
```

因此类必须在重新导入时仍以原 Python 类名导出。`@workflow.defn(name=...)` 改的是 Temporal 的类型名，不能替代该 Python 导出。局部 factory 的 `@workflow.run` 会因 `__qualname__` 含 `<locals>` 直接报 `Local classes unsupported`；修改 `__module__`／`__qualname__` 或仅保留另一 alias 也不是需要引入的装载方案。[S1][L1]

`imports_passed_through()` 设置一个有界、可嵌套的线程局部标志。SDK 在处理该块内的 import 时，可临时撤下 sandbox importer，从宿主正常导入并复用 module；它不把整个 Workflow 文件标成 pass-through，也不为之后的 import 永久配置白名单。[S2]

本次在同一个自足包中使用 owner／transitive owner；它们只读取自己的小 `schema.json`。通过 Python audit hook 计数这个文件的 open 事件，并直接比较 sandbox／宿主对象身份。结果如下；没有读取业务原件。[L1]

|观察项|实际结果|含义|
|---|---|---|
|普通 `from . import owner`|标准 prepare 成功；宿主首次读 schema 2 次，sandbox 又读 2 次|prepare 成功不能证明没有业务 import I/O。|
|块内 `with ...imports_passed_through(): from . import owner`|prepare 仍成功；sandbox 又读 2 次，owner 与宿主不是同一对象|父包已先进入 sandbox 的这个 fresh-package 形状没有得到预期 pass-through。|
|块内 `import probe_pkg.owner as owner`|prepare 新增 schema open 为 **0**；直接 owner、其 transitive owner 均与宿主同一|明确子模块名的导入得到实际覆盖。|
|上述显式 import 的两次 `create_instance`|两份 Workflow module／class／module marker 均与宿主不同，两个 sandbox module 也互不相同；新类仍有 decorator 定义|标准 runner 确实重新导入了 Workflow 文件，未把 Workflow 自身整体放行。|
|pass-through 块结束后再导入另一含直接文件读取的 owner|`RestrictedWorkflowAccessError`，指向 `pathlib.Path.read_text.__call__`|作用范围没有覆盖后面的所有 imports。|
|类的 Temporal 名为 `DifferentWireName`，但删除原 Python 名、只留 alias|标准 runner `ImportError: cannot import name 'RequiredModuleName'`|Temporal 类型名与 Python 导出名是两个边界。|

第二行的原因与 SDK 的具体调用点一致：`_import()` 先解析这次请求的完整名，只有该名尚未在 sandbox `sys.modules` 时才调用 `_maybe_passthrough_module()`。`from . import owner` 请求的是已存在的父包，不能据此保证 fromlist 子模块得到标注。产品完整 import graph 可能因先前缓存呈现别的结果，后继应消除这种导入顺序依赖。[S2][L1]

还需要收窄“schema I/O 必然被默认 sandbox 拒绝”的说法。本次 `Path(__file__).with_name(...).read_text()` 在重新导入时确实读取了文件；当前产品 `_SCHEMA` 使用 `Path(__file__).parent / ...` 的链式构造。SDK 的默认代理限制并非完整的 I/O 安全边界，不能从限制列表或一次 prepare 推断所有等价文件调用都被拦截。本次未用原完整 worker 装载来定位其第一条失败依赖；既有交付所述 `HTTPRedirectHandler` 错误仍只属于其原探针。[S4][P2][L1]

两次本地 activation 还观察到：`in_sandbox=True`、`is_sandbox_unrestricted=False`、`is_imports_passed_through=False`；Workflow 中直接 `Path(__file__).read_text()` 被拒绝，但调用 pass-through owner 的 `read_schema()` 读到了自己的文件，宿主共享 list 依次变成 `[1]`、`[1, 2]`。这证明默认限制仍在，也证明复用 owner 会共享状态／函数的宿主 globals；**pass-through 不能替代确定性约束或 S-H 隔离**。Workflow 必须只消费输入、history 中的活动结果和 durable timer，不调用这些业务函数、读取 `_SCHEMA` 或修改 owner 全局。[S2][S4][L1]

## 推荐的最小可选导出与注册形状

下面是待实施的装载形状，不含产品 Workflow 状态机。SDK 可选判断放在现有业务 imports 之前；只捕获顶层包确实缺席的 `ModuleNotFoundError`，SDK 已安装但缺少其子依赖／损坏时继续暴露原错误。[S1][S2]

```python
from contextlib import nullcontext

try:
    from temporalio import workflow
except ModuleNotFoundError as error:
    if error.name != 'temporalio':
        raise
    workflow = None

with (workflow.unsafe.imports_passed_through()
      if workflow is not None else nullcontext()):
    import ergora.budget_clock as budget_clock
    import ergora.processes as processes
    import ergora.reference as reference
    import ergora.training_cycles as training_cycles
    import ergora.training_execution_protocol as protocol
    from .reference_training_budget import BudgetedStart, TASK_QUEUE, validate_binding
    from .reference_training_submission import _Submission
    from .reference_training_execution import Execution
    from .state import State, now

if workflow is not None:
    @workflow.defn
    class TrainingCycleWorkflow:
        @workflow.run
        async def run(self, request: dict) -> dict:
            ...  # 只有确定性编排；业务动作通过 remote activity。
```

`if` 不产生 `<locals>`，因此自然导出仍是 `ergora.reference_training_worker.TrainingCycleWorkflow`。需要的 activity 装饰也可放在同一 SDK 存在分支；不必新造 loader／插件注册表、动态 class factory 或另一个执行模块。新增 cycle 入口在 SDK 缺席时明确报不可用，原 core 导入及只读操作保持。自足模块在最终 core 环境成功导入、未导出 SDK 类、显式 `require_sdk()` 报可选依赖缺席；同一探针还从当前 `src` 成功导入原 worker，之后 `temporalio` 仍未载入。[L1]

本形状应保持 `reference_training_worker.py` 本身由 sandbox 重建；不要将 `ergora` 或整个 worker 加入 pass-through，不设置 `sandboxed=False`，不替换为 unsandboxed runner，不使用全模块放行。现有 `GATE_SOURCES` 已包含 worker、训练／协议／预算等 owner，新增类和入口留在现有文件中；SDK 仍是现有可选依赖，无需修改 key 集合或 283 参考文件。[P1][P2]

生产入口使用公共 `Worker(..., workflows=[TrainingCycleWorkflow])`，让它完成标准准备；研究探针直接调用 `SandboxedWorkflowRunner().prepare_workflow(workflow._Definition.must_from_class(...))` 只是定位装载接缝。`_Definition`、fake info、手工 `WorkflowInstanceDetails`／activation 及对象内部字段均是 SDK 内部细节，不建议产品调用。[S1][S3][L1]

在新的 `_serve_cycle` 中，用同一个**已连接** client 建两个 Worker：普通 Worker 消费 intent 已冻结的 `ergora-training-cycle-v1`、注册总 Workflow 和普通 async activities；stop Worker 只注册停止活动、消费另一个明确固定的 queue。正常和 stop 分别设置正的 `max_concurrent_activities`；Workflow 的停止分支显式指定 stop task queue，避免把 stop 放回普通 queue 或使用 local activity。stop queue 名和精确活动名仍需 c1b／c1c 设计固定。[P2][S3]

SDK 在每个 Worker 构造中各自调用 `WorkerTuner.create_fixed(activity_slots=...)`，再给各自 Rust Worker 传入 `TunerHolder`；该参数是活动执行 slots，不是 poller 数量，也不是全进程共享配额。自足 Python 注册探针捕获到下表，两个 activity slot supplier 确实是不同对象。[S3][L1]

|探针 Worker|queue|Workflow|活动|传至 bridge 的 activity slots|
|---|---|---|---|---|
|普通|`probe-cycle-normal`|`TrainingCycleWorkflow`|`probe-normal`|2|
|停止|`probe-cycle-stop`|无|`probe-stop`|1|

2／1 只是用于区分构造结果的探针值，不是产品容量建议。探针使用未连接的内部 service-client 对象，并**仅替换 `temporalio.bridge.worker.Worker.create`**；实际 Python 注册、decorator 校验和标准 sandbox prepare 保留，`bridge.client.Client.connect` 调用为 0、两个 Worker 的 `is_running=False`。另实证正常公共构造拒绝 lazy client：`Lazy clients cannot be used for workers`。真实服务应继续沿原 connection owner 获取 client；本次没有验证 Rust Worker slots 消耗、poll、server 调度或停止活动及时性。[S3][S4][L1]

两个 Worker 可在 cycle loop 中用两个 async context 共同管理；SDK 原 context 在致命错误时会取消外层 task，并在退出时 shutdown。需要保留错误传播，不能在服务循环中吞掉 cancellation。它们仍共用 event loop：任何同步业务读取／锁／fsync／等待都会同时阻塞两个消费者，所以新增活动应只调用现有异步 `_CycleOperation.run()`／stop 用例，把业务留在受监管 H。SDK 默认的 Workflow task executor／sandbox 线程是库自身执行方式，不能用它替代服务 PID 隔离。[S3][P1]

|具体接入点|后继最小职责|
|---|---|
|`reference_training_worker.py` 顶部及模块级类|如上完成可选导出与显式业务模块 pass-through；保留原 `create_adapter`／budget `_serve`／`main`。|
|同 worker 的 cycle 入口|另一个 `cycle_main(installation)` 调用自己的 `asyncio.run(_serve_cycle())`；构造普通／stop Worker，活动只异步监管原 S-H。|
|`reference.py` 的 worker 命令构造|沿现有 budget 命令方式使用应用解释器及可选 SDK，指向 cycle 专用入口；不改用可能缺少应用依赖的 native 解释器。|
|`services.NAMES`／`_prepare`／`control`|增加明确的 `training-cycle-worker` 服务、自己的 argv／日志／PID／SDK 可用性判断；可沿 budget 现有方式使用 training-worker 配置模板，保持显式启动和 `autostart=false`，不改 283。|
|`_dispatch_controller`|已有类型名 `TrainingCycleWorkflow` 和 intent queue 与模块级导出对齐；不增加第二套 start／receipt／对账代码。|

原 budget 服务仍有自己的 PID、原 `_serve()` event loop、`ExperimentWorkflow`、`Activities(BudgetAdapter)` 和原配额。新的两个 Worker 只在新 cycle PID 内管理；把它们加到旧 `_serve()`、在一个 PID 中开第二条 loop 或增加线程都不能满足已经批准的进程边界。[P1][P4]

## c1b 先要解决的长期 owner 归属

源码确认了一条后继不能直接组合的路径：[P1][P3][P4]

```text
cycle SDK loop → S（原 subreaper）→ H
  → training.start → 原 submission 进程
    → _Submission.dispatch → BudgetedStart.ensure_owner
      → Popen(budget_main, start_new_session=True) → 长期 budget owner
H 结束 → S 的原 processes.run finally → _reap_children
```

`ensure_owner()` 在确认 owner 活着后就返回，owner 继续 `own()`／原执行链。`processes.run(supervised=True)` 把 S 设置为 Linux child subreaper，在 H 结束后收养并 kill／wait 其剩余后代。`start_new_session=True` 改变 session／进程组，不改变这个后代归属；嵌套原 `_training_process` 也不能让长期 owner 逃离祖先 S 的回收范围。因此不能把原 `training.start` 直接放入短 H，再把 `owner_alive` 的短暂观察说成跨调用独立；更不能豁免后代、跳过或复制 reaper。这里是 c1b 开放前提，本次未实际启动或回收任何 budget owner；现 c1a2 的总 controller 投递不生成这种子 owner。[P1][P3][P4]

另只读核到了原安装 reaper 的独立惰性 probe：`.ergora/checks/training-cycle-owner-boundary/reaper-probe-r2.json` 记录 H 后代被原 reaper 收养回收、独立兄弟在另一 S 收尾后仍存活，两惰性进程均收尾，实耗 0.582 秒。它支持上述**OS 归属**判断，不是预算 owner、父 loop 退出或跨重启验收；其身份及 SHA 引用存于本次 L2 索引。

一个可供后续设计核验的窄候选是：先由 H 沿原 prepare 冻结子 start intent／启动材料，再由 cycle loop **异步等待一次仅做 OS 创建的 `to_thread(Popen)`，使原 `budget_main` 成为 cycle 的直接子进程、S 的兄弟**；另一 H 核原 owner 完整身份后，普通 start-H 只能使用原 owner。只把 Popen 的 OS 创建放进线程，业务仍在原独立 budget 进程与 S-H；它不以线程替代进程隔离。公开 write-pipe API 传 stdin、Popen 非阻塞 `poll` 的具体限制见下节。原 budget owner 自身继续负责原 total clock、精确停止和唯一 reaper；这仍是待具体设计／评审的候选，未证明既有业务接口足够。[P1][P3][S5][L2]

至少需要先固定以下条件，才能据此实施；不能以两份 Worker 注册替代：

1. **复用原 prepare 与启动合同。** `training.start` 的 `_submission` 当前会在短数据库冻结后继续 dispatch；prepare-only 接缝实际在原 `reference.training_submission(operation='prepare')`／`_Submission.run`。应在原 owner 内明确窄的阶段接口，保留原 revision／manifest／budget／完整 intent 校验及事务范围，不在 worker 重写一份。H 提供完整原 payload、intent SHA、原解释器／环境与日志去向；SDK loop 不加载 State、读取业务文件或重建它们。
2. **启动 reservation 与原锁保持一致。** 现 `ensure_owner` 的 launcher lock、`owner.json`、owner lifetime lock／出生能力不能因为父进程换位而失效。需要明确直接启动原 `budget_main` 与旧手工 launcher 并发时的唯一归属、确认时点和失败记录。owner 输出／日志的打开也不能回到 SDK loop 做同步业务 I/O。这些不是现有 loop spawn 自动提供的能力。
3. **后续 H 在最后调用点强制 existing-only。** 单独一次先前 H 的 `owner_alive` 不足够：当前 `ensure_owner` 当 `owner.json` 不存在仍会 Popen。c1b 路径必须在实际 dispatch 时拒绝缺失／损坏／变身份，或有等价的最后约束，使短 H 永远不能补启 owner；原手工调用行为由原 owner 保持。
4. **保留真实 spawn handle 与取消收尾。** 在 spawn pending、原 owner 尚未发布身份、超时／活动取消／响应丢失时仍需掌握实际根进程。未知不能再次 Popen；精确 stop、原 owner 清理及实际 stopped 分列，不能取消 future 就宣称树已停，也不能强杀正在使用原 reaper 的 owner 来制造假停止证明。
5. **跨调用／重启继续用原不可续期记录。** 确认后的 owner 按原 clock 独立存活，cycle 重启只沿其原身份／完整 intent／attempt／receipt 观察；不重启旧 owner、不返还 start／launch slot、不让新的父进程续期。确认前失联、部分发布以及 cycle／owner 同时退出的责任必须有明确未知结果和对账入口。

如果这些条件不能在现有 worker／training／submission／budget owner 中安全内聚，应先复审 c1b 具体设计并保留未支持状态，不为这一候选建立通用 process-host／插件框架。[P3][P4]

## Python 3.12 的根进程退出语义

**本机正常 teardown 与 SIGKILL 的存活结果相同，均留下同一惰性 root；不能写成“正常退出必 kill”。** 但这也不证明 `asyncio.create_subprocess_exec` 提供了可跨 worker 重启的公开所有权转移接口。`BaseSubprocessTransport.close()` 在 returncode 尚未到达且 Popen `poll()` 仍为空时调用 `self._proc.kill()`；未 closed 的 transport 在 `__del__` 中调用 `close()`。它按 PID 操作，所以 `start_new_session=True` 不能抵消这次 kill。[S5][L2]

`asyncio.run` 的 Runner 收尾会取消剩余 task、结束 async generators、关闭 default executor 和 loop，并不承诺 detach 活 subprocess。本机 uv Python 3.12.11 没有 `os.pidfd_open`／`signal.pidfd_send_signal` 的 Python 包装，默认 `ThreadedChildWatcher` 的 daemon wait 线程把 callback／transport 保存在参数中；这解释了 loop 结束、删除 Process 引用及 GC 后 transport 仍没有进入上述析构路径。标准库也存在 `PidfdChildWatcher` 分支，其引用由 loop reader 管理。不能把本机这次引用存活行为当作所有 Python 构建／watcher／服务退出方式的合同。[S5]

探针中的 child 只 sleep，Popen 路径额外读取一行固定启动标记。所有 child 都使用新 session，stdout／stderr 为 DEVNULL；没有 budget/store、业务文件、SDK、服务或真正的循环 worker。私有 harness 临时设为 subreaper **只用于 wait 它自己的孤儿惰性 child**，不调用或改写产品 `processes.run`。每次观察核 PID／start ticks／boot，另记录状态、PPID、PGID 和 session；信号通过绑定该身份的 pidfd 发送。[L2]

|对照|loop 返回后|显式 GC 后|父进程退出后|实际收尾|
|---|---|---|---|---|
|`create_subprocess_exec`，释放 Process|同一 root 活|同一 root 活|父正常退出0；root 活，PPID 转到 harness|TERM／wait `-15`，原 `/proc` 条目消失|
|`create_subprocess_exec`，保留 Process 至解释器退出|同一 root 活|同一 root 活|父正常退出0；root 活，PPID 转到 harness|同上|
|`create_subprocess_exec`，父在 loop 内被 SIGKILL|未走正常收尾|未走正常收尾|父 `-9`；root 活，PPID 转到 harness|同上|
|公开 `loop.subprocess_exec`，释放 transport|同一 root 活|同一 root 活|父正常退出0；root 活，PPID 转到 harness|同上|
|`to_thread(Popen)`，公开 pipe 传小 stdin，释放 Popen|同一 root 活|同一 root 活|父正常退出0；root 活，PPID 转到 harness|同上|
|同一 Popen 路径，父在 loop 内被 SIGKILL|未走正常收尾|未走正常收尾|父 `-9`；root 活，PPID 转到 harness|同上|

六例共 1.469 秒，脚本退出0，六 parent 均 wait，六 root 均 TERM／wait `-15` 且最终无原身份；实际身份和每个阶段的观察保存在 L2 原 JSON。短观察没有认证长期时钟执行、系统关机、Supervisor stopasgroup 或预算 owner 的最终清理。SIGKILL 绕过 Python 清理的事实也不构成可靠 root 授权／回收协议。[L2]

|公开方案|已核语义／实际限制|
|---|---|
|`asyncio.create_subprocess_exec`|返回的 Process 由 SubprocessTransport 管理；没有公开 detach。当前 watcher 下正常退出实测存活，但 close／析构有 kill 语义；保留 Process 引用只能延迟释放，不能构成跨进程生命周期合同。|
|`loop.subprocess_exec`|公开低层接口仍产生同一种 subprocess transport；换 API 层级没有改变 close 语义。|
|`create_subprocess_shell`|仍沿 subprocess transport。让 shell 再后台启动／双重 fork 是额外 launcher／移交协议，不是公开 async 根句柄的 detach；会增加身份、丢回复与取消责任。此次未运行 shell。|
|直接同步 `Popen`|其 `__del__` 只警告、非阻塞 poll，并把仍活对象加入 `_active` 以待以后回收，不 kill；但 OS 创建是同步调用，不能直接放入要求不被 spawn 阻塞的 SDK loop。Popen 的 context `__exit__` 会 wait，亦不适用于长期 root。|
|`await asyncio.to_thread(Popen, ...)`／同类 executor 创建|创建返回的仍是 Popen，不给 root 绑定 SubprocessTransport。此次线程只做 OS 创建，public `connect_write_pipe` 发送一行后关闭 write transport，之后只用 `Popen.poll()`；default executor 在 loop 收尾时没有等子进程寿命。业务继续在独立 OS root，这个线程不持有 budget/store。|

Popen 对照只覆盖一个小 stdin 和已完成的 OS 创建；产品还须固定有限缓冲／flow control、启动中取消后保留真实 handle、确认前失联和 once-only claim。取消 `to_thread` 的 Future 不会终止已开始的线程；如果 Popen 自身卡在创建，Runner 的 default-executor 收尾仍可能等待该调用。本次没有模拟这种阻塞，也没有 `to_thread(wait)`／`to_thread(communicate)`：把长期 wait 放进 executor 会使服务退出与原 owner 寿命耦合。root 的 stdout／stderr 应由原根 bootstrap 在自己进程中打开原日志，SDK loop 不打开业务文件；此次 DEVNULL 不能认证该真实日志接缝。[S5][L2]

未发现可以仅靠公开 asyncio subprocess API 宣称完成上述 detach／归属移交的接口；当前默认 watcher 下的存活事实应保留，不能反向写成必失败。如果支持范围要依赖该 watcher 的引用持有，仍须在真实退出路径固定并验证，维护上需要承担这项额外假设。仅在线程中做 Popen 创建使“活 child 的 Popen 析构不 kill”成为更直接的 stdlib 依据；后继选择它也仍须明确评审 spawn／取消边界，不能因此认为长期 owner 业务协议已闭合。[S5]

若不允许这种窄的 OS 创建线程，替代选项有同步 Popen 的 loop 阻塞限制，或专用 launcher／长期 S 的额外进程和交接责任。不能把 budget/store 搬到线程，也不能让长期 owner 留在原短 S 的后代树，或改原 reaper 为它留例外；本研究不建议为此建立通用 processhost。[P3][S5]

原 lifecycle r1 因错误使用本机缺少的 `os.pidfd_open`，在第一例收尾时抛 `AttributeError`，没有最终成功 JSON，源码和 stdout／stderr 保持。已先按该例原 PID／start ticks／boot 用 libc pidfd 精确 TERM，确认原 `/proc` 条目消失，保存 `async-root-lifecycle-r1-recovery.json`。原 harness 当时已退出，恢复进程无法 wait 非子进程，未把它记成已 wait。r2 仅补该平台 pidfd 包装兼容及 watcher 类型记录，才取得上表六例完整 wait／收尾；新运行不替代旧失败。[L2]

补充实际命令为：

```bash
.ergora/checks/training-cycle-dispatch/venv-r1-core/bin/python .ergora/checks/training-cycle-sdk-boundary/async-root-lifecycle-r2.py
```

脚本 SHA256 `1efc8567fb698ddde471b5e06bb58daa8a355bd2b9c9686b3450a1c4c01e560a`；结果 JSON SHA256 `05635ba5a1adad2019852d196dc59db5f5e8b2283f7315cd7f6a513598429ffe`。原 r1 恢复原件 SHA256 `8f288612c501403f697427a86b0780932d6b4008cbe7b09e305d796728218b24`。完整私有索引 `async-root-lifecycle-evidence-index.json` 将本轮源码／结果／原失败、Python 一手来源和独立 reaper 证据各自绑定。

## 复现、局限与最小后继验收

私有目录中的最终 `probe.py` SHA256 为 `6870ceb0bcd9cdd1b4b7590a33c31c31fd9b0a88b6ce17b4e0f0150d2e9a2af6`。以下两条实际命令均退出 0；结果和 stdout／stderr 为同一最终源码下的 r4，核心观察已在上表展开：

```bash
.ergora/checks/training-cycle-dispatch/venv-r1-sdk/bin/python .ergora/checks/training-cycle-sdk-boundary/probe.py
.ergora/checks/training-cycle-dispatch/venv-r1-core/bin/python .ergora/checks/training-cycle-sdk-boundary/probe.py --core
```

`sdk-result.json` SHA256 为 `ff1398ae99288d868981c974d852148fd0d99d66b0278988915f1eb22e05324e`；`core-result.json` 为 `f67fb33c819086c0b8f03a996da2fdf828eaf4c3ffdffcc5273f7ca41cdb94ad`。原失败与各版源码快照保留：r1 错误假设链式 schema read 必被拒绝；r2 错误假设 from-parent 块可保证零重复读取；r3 在宿主 loop 直接调用 SDK activation，清除了该线程 running-loop 状态，随后 Worker 校验失败。r3 外层含 `cat` 的 shell 退出 0 不作成功证据。最终改在专门线程顺序执行本地 activation，保留标准 SDK runner／默认 restrictions；stderr 的三条 `Path.read_text restricted` 对应刻意验证的限制路径。[L1]

本次没有测试原完整候选 worker 的新增类、安装 wheel／两环境资源身份、真实 server history、Workflow replay、queue 可用性、普通活动饱和时的 stop 执行、两服务 PID／loop 或长期 owner 移交。SDK 内部 API／代理行为以本地 1.34.0 为准；生产支持其他 SDK 版本时需要在声明范围重新核实际装载，不能用本探针做普遍兼容承诺。

后继最小验收应按真实边界排列，先完成 c1b，再实现 c1c：

|次序|必须取得的最小实际证据|
|---|---|
|1. 产品模块装载|固定 c1a2 终态及准确 baseline；新非 editable SDK 安装以默认 Worker／runner 重新导入 `ergora.reference_training_worker.TrainingCycleWorkflow`，核新类完整装饰、Workflow module 不是 host、所有业务 owner 的实际 pass-through、无重复 schema I/O；同源码 core 导入／既有只读观察且 SDK 缺席。|
|2. 子 owner 归属先闭合|由原接缝产生可核 budget owner，短 H 及 S 完整退出／原 reaper 收尾后，它按设计仍以同一 PID／start ticks／boot／原 clock 存活；再分别核真实 worker 正常 loop／解释器收尾与被 SIGKILL 的路径，不能用惰性 root 代替。缺失／冲突／慢发布／丢回复／取消／重启不得补启或换身份，实际 owner 与其执行后代最终沿原链清理。|
|3. 独立服务与配额|实际 `training-budget-worker`、`training-cycle-worker` 两 PID／两入口 loop、准确 argv／queue；保持旧 ExperimentWorkflow 注册。真实普通 Worker 占满 slots 且 H 持原 registry／State 锁或 fsync 阻塞时，独立 stop queue 仍得到活动执行机会，budget 服务阻塞不挡总取消。|
|4. 全部活动阻塞通路|父 SDK loop 禁止同步 State／SQLite／原件 reader；取消覆盖 spawn pending、大 stdin、H、后代和原回收，普通 operation 消耗同一 compute∩control 窗口，stop 用原 total；writer／各 owner 通知分别隔离。|
|5. 首轮 Workflow|真实 Temporal 的原完整 input／memo／固定 run、确定性 query／timer／取消；副作用活动 `maximum_attempts=1`，非正剩余时间不派发；重启或丢回复只对账原 start／launch，不换 ID／run、不重开 clock。|
|6. 后继轮门槛|c1d 的原 accepted archive、实际 phase、durable stopped、完整 rounds 追加与 payload／history 容量全部通过后才开放后继候选；保留人工 release、原 baseline 与283／source-pin门禁。|

以上是建议的验收义务；本文不预判任何产品片通过。
