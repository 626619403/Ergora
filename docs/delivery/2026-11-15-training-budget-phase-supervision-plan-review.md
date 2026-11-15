# B3.3a 独立阶段监督：r2计划独立审查

日期：2026-11-15。评审者为新的fresh-context Codex子Agent `training_phase_supervision_plan_audit`。只收到原始目标、固定输入、基线及检查边界，没有继承实施对话或预定结论。按根／源码／测试 `AGENTS.md`、[组件协议](../architecture/component-change-protocols.md)、maintainable-project-delivery独立评审brief及ergora-codebase-quality的module-design／test-seams规则检查。

|审查轴|r2结论|开放finding|
|---|---|---|
|需求符合性／可实施性|request-changes|1：R1，大输入传输所选API不能按计划续写|
|结构维护|approve，仅指本片owner与依赖设计|0|

**r2整体尚未批准实施。** 先修订R1并复核同一片计划；结构轴通过不代替功能可实施性。此次没有产品实现、产品测试或安装验收。

## 固定范围与身份

产品HEAD为 `75d1ee325288527f67fb1ea814332d1522ff4860`，parent为 `b78f7b233316f3248c5a5865d90e6a23870693ac`，分支为 `refactor/architecture-foundations`。相对基线的 `src/`／`tests/` diff为空。B3.2既有运行、安装、审查和未完成发布门禁只归原片，没有重验或转授。

先读取固定 `.ergora/checks/training-budget-phase-supervision/plan-r2.md`、`plan-r2.json`及 `design-scope-r2/` 中的三份完整文档；r1仅为历史原件，未作为本次候选。独立逐字核对结果如下，三份当前工作树文档均与固定原件相同：

|固定文档|字节|SHA256|
|---|---:|---|
|[具体计划](../plans/2026-11-15-training-budget-phase-supervision.md)|9393|`2bb1f05fe0d26ebfd7fe746eaf1a3900a6216f312de7a62ec857cf92300b0440`|
|[初始交付](2026-11-15-training-budget-phase-supervision.md)|2069|`4a36b0b119e4679fd7a6b60a9e0d28206707e30efba092c3f9f30c019dbd1b4e`|
|[生命周期调研](../research/2026-11-15-training-executor-lifecycle.md)|26917|`1b3ea709a6a2e2b364662258e9618a682c0e7620f4c40fb4c287445892219ec0`|

直接检查了 `reference_training_budget`／`reference_training_worker`、`processes`、`reference_job_lifecycle`、原native training adapter／executor／Sandbox／process_job、submission／context／clock／record reader及相关原fixture。完整来源清单、固定文档与20个相对链接核对、283参考文件的基线blob对照在 ignored `.ergora/checks/training-budget-phase-supervision/plan-audit/static-audit.json`；283无字节差异。

## R1：高，大输入首次超时后不能用所选communicate调用继续发送

位置：[具体计划](../plans/2026-11-15-training-budget-phase-supervision.md)第30行；[交付](2026-11-15-training-budget-phase-supervision.md)第11行也把“可继续的短轮询communicate传输”作为已固定设计。

可达场景是完整context大于PIPE容量，supervisor启动或读取stdin较慢。计划要求首次 `Popen.communicate(payload, timeout=短轮询)` 超时后继续完整发送且不重发stdin；在本机Python 3.12.3的POSIX实现中，这个组合不可用。`pyproject.toml:12`支持 `>=3.11`，不能把3.12排除在已有支持范围外。

已直接读取本机stdlib源码：`subprocess.py:2098`仅在**本次调用的input非空**时把stdin加入selector，后续 `communicate(input=None, timeout=...)` 不会注册尚未写完的stdin；第1183行又拒绝通信开始后再次传入非空input。内部 `_input_offset` 被保存并不意味着公共调用会继续发送。不能只照用“第二次传None”的常见输出收集方式处理尚未传完的输入，也不能依赖私有字段修补stdlib。

独立纯stdlib探针未import或运行Ergora：向延迟0.15秒读取的子进程发送851,968B完整UTF-8输入，首次0.02秒超时后以0.05秒轮询继续调用13次，仍未完成。手动关闭stdin后，reader正常退出但只收到65,536B，SHA也不相同。探针源码与原结果分别保存为 ignored `plan-audit/communicate-continuation-probe.py`／`communicate-continuation-probe.json`。

后果是合法context停在半途，supervisor的 `json.load(stdin)` 等不到EOF，原phase不能开始；若取消前还没有独立停止接线，则可能连原fence／cleanup窗口也耗掉。关闭stdin强行前进只会得到截断JSON，重发payload则被公共API拒绝，均不能满足完整输入与及时停止合同。

最小修订是在原owner内固定等价的可轮询传输，例如 `selectors` 配合非阻塞PIPE：保存唯一stdin字节偏移，仅推进未发送部分，写完关闭stdin；同时读取stdout协议帧、处理stderr并检查原clock／停止标志。所有状态留在已有阶段生命周期owner，不新增通用传输框架，不缩窄有效context容量，也不修改 `processes.run`。修订应说明完整帧的累积／解析与输出边界，保持匹配stopped帧之前不硬杀reaper、帧可见之后才可停止无业务后代的supervisor。大输入慢reader回归必须核收到的完整字节／SHA及停止行为，不能仅断言多次调用communicate。

## 其它合同的源码核对

没有发现其它独立阻断，限于下列已读范围：

- [processes](../../src/ergora/processes.py)第76–99、117–156行确实在调用进程设置subreaper并kill／wait全部直接子进程。四种phase都移到各自专用supervisor、原owner不再调用监督路径，能消除未来两个phase共用reaper的结构风险。该supervisor内部仍须只拥有本phase子树，不继承原submission／owner生命周期锁；这项义务已在固定调研第57行记录。
- 原监督路径不使用timeout控制截止，实际依赖predicate；`waitpid`没有严格耗时界。r2没有用父级总截止强杀替代回收，也没有缩短有效预算。期限后只等待既有安全回收并记录unknown／overrun，在当前原语下是可实施的保守合同；它不是任意阻塞下的硬实时保证。调研第73行已承认启动及原run准备I/O也可能阻塞，不能把这些未知情形写成及时回收成功。
- [预算owner](../../src/ergora/reference_training_budget.py)第227–278行串行调用monitor／fence／cleanup／publish；第311–320行由publish helper写原final。r2保留该业务顺序和受监督发布。stopped帧必须在原run完整返回后实际写入并flush到PIPE，再进行helper结果读取；帧后故障仍为业务unknown。短轮询读取端须能识别尚未EOF时的完整stopped帧，不能等进程退出才看它。
- 原 [record reader](../../src/ergora/training_cycles.py)第195–199行给helper普通JSON结果1MiB界；r2已把阶段封套开销另算，并绑定phase ID／mode／context及原intent／授权摘要。实施仍须保留截断、乱序、身份冲突、超期的保守处理；临时停止观察不成为executor停止证据或新恢复权限。
- 原 `owner_record` 第99–107行严格读取schema 1的既有字段。r2不添加执行能力、不重启／接管旧owner，并把新能力版本留给后继执行设计，当前没有持久格式升级缺口。旧owner可能继续启动新版磁盘上的 `budget_main` helper；迁移时须保留其原四种直接helper模式和普通JSON输出，新的supervisor协议应只由新的明确入口使用。固定计划的“helper原输出”和“原持久合同保持”覆盖该兼容义务，后续产品审查需直接验它。
- 原 [training executor](../../src/ergora/data/reference/platform/local/agent_platform/training_executor.py)第51–66行自己获取非阻塞executor锁，既无锁内admission hook，也不因已有started而拒绝再次进入；[Sandbox](../../src/ergora/data/reference/platform/local/agent_platform/sandbox.py)第59–61行和 [process_job](../../src/ergora/data/reference/platform/local/agent_platform/process_job.py)第108–112行另开session。r2把锁内原子准入、whole-executor不可重用attempt、新owner能力和真实停止验收留为后继开放项符合实际接口。不能在本片把它们视为已解决或默认获得执行授权。

模块职责留在已有 `reference_training_budget` 与 `reference_training_worker.budget_main`，阶段启动、停止和结果收集确有一组需要隐藏的调用义务；没有新文件、插件总线或第二训练账本的必要性。`reference_job_lifecycle`只用作回收后才发停止证据的相邻范例，未照搬其task ledger或同步发布。Kernel专家、模板、queue、slot、原native算法均不在本片变更范围。

## 检查与尚未取得的验收

实际执行：只读Git／源码／文档检查、三份固定文档字节与SHA对照、20相对链接检查、283参考blob对照、`git diff --check`，以及上述约0.68秒的纯stdlib传输探针。没有运行Ergora产品或测试，没有安装、提交、推送，未启动模型、训练、Temporal、MLflow或其它服务。当前共享树有其它文档在途，本评审只写本报告及授权的 ignored `plan-audit/`。

R1修订后仍需同片计划复核。产品实施随后须取得自己的真实进程证据：两个supervisor互不回收、setsid后代停止、可捕获取消／总截止不会打断正在reap的supervisor、stopped帧前后失联和帧后处理阻塞保持unknown、完整大输入慢reader正确传输；并沿原submission／budget fixture保留accepted／held、completed、lost-ack、fsync故障与同fence恢复，核旧helper兼容及原slot／clock／queue／283保持。非editable安装、自身原审查模板、新fresh-context产品两轴、真实本地控制流程、精确发布及自己的CI仍全部待后续产品片。此次计划审查不认证训练质量、GPU或性能收益。

## r3同片复核：两轴通过，R1在设计层面关闭

日期：2026-11-15，同一独立评审者继续核对固定r3；上文r2结论、实红探针及原件保持。原r2报告9617B／SHA256 `f57cb6f768c9d77e6bcaf02622643db5e06d732d913eb209f90b5802dc2470f6` 另逐字保存在 ignored `plan-audit/plan-review-r2-original.md`，本段仅追加r3处置。

|审查轴|r3结论|开放finding|
|---|---|---|
|需求符合性／可实施性|approve，仅批准本片计划|0|
|结构维护|approve，仅批准本片计划|0|

复核输入为 `.ergora/checks/training-budget-phase-supervision/plan-r3.md`、`plan-r3.json`及 `design-scope-r3/` 的三份完整文档。固定身份如下，当前工作树三文档均与原件相同：

|固定文档|字节|SHA256|
|---|---:|---|
|具体计划r3|10933|`108622cb099964d1529d3d580a19336225e364741d73cf5ca37533fa247b2ed1`|
|交付记录r3|2752|`e8c9df451791a1f7f117fbbb84c8723b6bcf6e878e77075018f7a162fe37c329`|
|生命周期调研，原文保持|26917|`1b3ea709a6a2e2b364662258e9618a682c0e7620f4c40fb4c287445892219ec0`|

R1的具体失效机制已被消除：[计划](../plans/2026-11-15-training-budget-phase-supervision.md)第30行改用 `selectors.DefaultSelector` 与非阻塞PIPE，持续保存唯一发送字节偏移，发送完再关闭stdin；读取stdout与检查原clock／停止标志交错进行，轮询间隔至多0.2秒。它不再依赖超时后 `communicate(None)` 续写或stdlib私有字段，现有Linux公开原语足以实现该局部算法。未重跑r2原探针，也没有用计划文字宣称新传输实现已通过。

第40行进一步固定完整UTF-8 JSON行、EOF前可见且已flush的stopped帧、同绑定的stopped→result两帧顺序、64KiB／2MiB封套界，并将缺损、错序、冲突、多余数据及输入未发完保持unknown。原helper的1MiB容量独立保留；未引入新的持久文件格式。相对r2报告提出的旧进程兼容义务，r3现在明确保留四种直接helper模式的原普通JSON，只允许新supervisor入口使用分帧协议。已再次核对 `budget_main` 原直接入口与 `processes.run` 的finally／reap顺序，并读取现有 `parse_json` 的strict／finite／duplicate-key接缝；没有需要先修改共享processes或原283参考的接口缺口。

实现时应依约用实际写入量推进偏移并处理非阻塞短写／EAGAIN／断管，按字节累计到完整行后再解码。stopped可在EOF前改变“是否仍在回收”的观察；最终业务成功仍须确认进程退出、恰好两帧且没有尾随内容。封套应以编码后的字节计量，并用原helper容量附近的完整UTF-8结果核不缩容量。这些是r3既定传输与身份合同的实现／验收义务，没有新增开放设计finding，也不要求为四个phase复制测试矩阵。

其余边界与上文源码核对一致：所有四phase仍串行迁移；原owner不设subreaper；监督helper沿原clock停止，父owner不强杀正在安全reap的supervisor；publish保持受监督，耗尽可缺final；旧owner不升级、不接管且无执行权限。实际executor锁内admission、whole-executor attempt、新owner能力和后继并行停止设计继续开放，不由本次approve默认批准。Kernel专家与原queue／slot／clock／final／native算法保持原责任。

本轮实际检查为r2→r3文档差异、三份固定原件及SHA、22相对链接、原23项来源与基线身份、283参考blob及空的source／test diff、相关入口／解析器源码与 `git diff --check`。产品HEAD仍为 `75d1ee325288527f67fb1ea814332d1522ff4860`；静态原件在 ignored `plan-audit/static-audit-r3.json`。75d普通发布和CI43665465985在途为本轮交付输入提供的状态，本评审没有访问远端或检查该CI，不代替原产品评审者结算。

**下一步可以按r3计划实施B3.3a1。** B3.3a2真实进程证据、B3.3a3安装／自身模板／新fresh-context产品审查／控制流程／发布及自己的CI仍未取得；本轮没有运行产品、测试、模型或服务，也没有新增安装、提交或推送。R1只在设计层面关闭，后续产品仍须以实际慢reader完整传输和停止证据验收。
