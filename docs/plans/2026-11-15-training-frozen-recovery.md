# Q4.2b2：原登记上下文中的训练恢复

日期：2026-11-15。承接[有界循环](2026-11-15-bounded-training-cycles.md)及[b1前置阻断](2026-11-15-training-start-fence.md)。这是后继实施前计划，当前没有产品实现；实施基线待b1固定发布后填写。允许先核原owner和评审合同，不把b1或a2的验收转授本片。Kernel专家保留在v3路径。

## 问题和现有依据

当前所有训练入口取`State.project`的当前注册，再由`_TrainingProject.registration`比较当前config下的四份登记文件。原start intent绑定原execution／registration SHA／control home，但没有存完整项目登记。因此当前注册文件或项目登记变化后，原运行可能仍存在，观察／停止入口却先因漂移失败。删掉比较或仅提供旧revision不能证明原上下文归属；外部`cycle.json`的完整SHA也不提供来源认证。

现有`registrations._reserve`已在原control home的`registrations/<project>/<operation>.json`不可变保存完整before／after；`_finish`成功后再保存同目录`.result.json`，绑定原登记intent的canonical SHA、operation ID与registration SHA。这是既有本地发布凭据，可以作为**手工确认的旧登记恢复**的来源，无需另造授权账本、复制工作流或重写原训练checkpoint。它沿用已接受的当前用户／可信目录边界，不提供跨用户、跨机器或签名来源认证。

## 拟定合同，实施前独立复核

1. 只从**当前control home自己的原登记journal**选择旧上下文；项目ID、32位operation ID和原published result内的完整`intent_sha256`均须明确。确认canonical intent SHA与完整原record、published result、registration SHA和四原配置投影一致，原marker的control home须相同。成功import可保留execution policy的等价`allowed_task_types`列表顺序，比较投影须沿既有`training_cycles._decode`的规则仅规范该列表顺序；不排序其他字段／列表，不改原journal或files。路径／普通文件／容量沿现有有界读取owner，缺原result、不完整／冲突／被替换或来自别的home均拒绝。不得用外部导入的cycle输入、任意JSON或当前同名配置冒充原发布凭据。
2. 返回原published项目快照：只把原journal的pending状态按匹配的published result解释为原已发布事实，不改写journal。原登记revision、start intent冻结的revision、当前project revision、registration operation和摘要分别呈现；登记后合法binding变更可能使start revision更高，不能强求三者相等。当前项目仍须存在；改变repo、execution或已选模板不把旧运行转移到新位置，也不重写当前项目。手工变更操作显式确认当前revision与所选原登记，防止操作期间选择漂移。
3. 默认入口保持现有严格注册检查。只有显式选择并核实原发布journal的**恢复模式**可沿原execution访问旧记录；不能设一个通用`ignore_registration`开关。父进程在选旧execution前核来源，原训练进程复用同一读取合同再核原project／control关系，实际native运行仍由原模块和283参考代码提供。旧config的当前登记可以已变化，但不能因此放宽canonical执行路径、原intent身份、原记录、完整Experiment或run/history/memo核对。
4. 首片恢复操作仅限本地`submission`、已有attempt的`resume-start`对账、原`cancellation`／`cancel`／`resume-cancel`／`stop-status`和明确确认的`fence-start`。恢复模式下训练start的`prepare`、`check-start`、`dispatch`、没有attempt的start续发、runner执行、批准／release和所有新派发一律不提供。prepared且未attempt的原start只能读回或显式fence，不能用旧登记重新启动。这不禁止原取消owner内部必要的prepare／dispatch：取消仍须先本地冻结，再按原固定run单次发送或对账。
5. 恢复模式的fence要求已有且身份匹配的原start intent，继续从其冻结完整Experiment取值；没有原intent时，登记journal没有实验绑定，不凭当前spec补出旧绑定。原同binding fence幂等、状态快照、job ID／完整Experiment和release效果沿b1。当前已有job属于不同Experiment或损坏记录时拒绝，而非接管新作业。
6. unknown start只沿原`_Submission.reconcile`核同workflow、完整初始Experiment和原intent memo，找到后补原receipt；NOT_FOUND、服务不可达或归属冲突不清attempt、不新发start。submitted后沿原精确run取消与信号历史恢复，原actor、request ID、reason、attempt-before-send及丢回复语义不变。`stop-status`保留控制面／adapter／本地fence的分别观察，不以任何单项宣称OS或后代停止。其直接调用native adapter前，须沿原safe_file／document核会访问的request／started／result／fence路径及原canonical job ID／binding关系，不能因frozen分支绕过records就假定原native reader已经提供这些校验；完整Experiment仍由原adapter核对。
7. 原连接和本地adapter的支持边界不扩大。旧安装必须通过现有身份校验，实际SDK依赖保持；连接仍沿受支持原本地runtime的原policy。实施前核旧endpoint／namespace能否由固定原代码唯一确定；不能核定时明确阻塞该远程恢复，不能把当前环境的另一服务当作原服务。原安装、存储或服务已消失时保留具体缺口，不自动重建或迁移。
8. CLI拟为上述支持的原命令增加成组的`--original-registration OPERATION_ID --registration-intent-sha256 SHA --confirm`选择；缺一项拒绝，已有原命令的其他确认仍保留。确切名称在实施前复核固定。本片先提供CLI／应用，不隐式修改页面，也不授权父循环自动调用；父级授权、deadline与完整资源停止归b3／c。

这里“原published”来自该control home保存的原成功发布记录，不代表当前native配置仍等于旧配置。用户显式授权在原目录处理那个原intent；不得因此对所有历史实验自动加fence、批准旧候选或扩大权限。

## 所属模块和最小改动面

|职责|原owner与本片扩展|
|---|---|
|原登记归属／完整投影|`registrations`增加有界只读原journal选择，复用`publication_files`；不建表、不补造published receipt|
|手工确认／当前revision|`training`沿原应用保留当前revision确认，并传递已选择原上下文；CLI只解析|
|原执行目录和子进程|`reference._training_process`继续选择已校验的原安装和环境；不建立第二RPC客户端|
|严格默认与限定恢复|`reference_training_context`复用同一journal合同核来源；`reference_training_submission`只让原对账／本地fence进入恢复，禁止其dispatch路径|
|固定run取消／停止观察|`reference_training_cancellation`沿原_submission身份、lookup／memo／history和原adapter；不重写signal或停止状态|
|示例和手册|原`docs/TRAINING.md`说明原登记result如何取得、旧与当前身份、支持操作／依赖与失败恢复|

保留原`training._submission / _cancellation`的两阶段调用：仅本地冻结／当前revision确认期间持有DB预留，退出事务后才做远端对账／发送；不能把reconcile放进仅用于本地操作的`_setup`。journal含before／after和重复definition／files，读取聚合容量须单独固定／实证边界，不能套native单份1MiB；超过声明容量明确拒绝且不截断。两项在R2实现前核定，并在R3／R4用实际接缝验收。

新增函数应留在实际owner并列出真实消费者；纯单次调度逻辑不另造转发模块。普通当前模式不承担旧模式的分支细节。能沿原数据合同复用的，不复制manifest／intent／history读取器。

## 可验收节点

|节点|证据|状态|
|---|---|---|
|R1 来源和权限合同|核原journal/result格式、四文件投影、control归属与真实连接policy，独立两轴计划评审|r3独立需求／维护两轴approve，开放0／0；r1成功import顺序P2已按原等价规则关闭，见[评审](../delivery/2026-11-15-training-frozen-recovery-plan-review.md)，不认证实现|
|R2 最小实现|上述原owner、成组CLI确认与操作白名单；默认当前注册路径不变|待R1与b1固定实施基线|
|R3 真实变化与恢复|原公开注册生成旧journal，含成功import保留的非默认等价policy顺序；登记后binding修订再start，得到不同的登记／start／当前revision。改变四文件和实际登记execution后，明确选旧记录可读／对账／精确取消／fence，新派发被拒绝。原新目录、原intent与未知attempt保持，不产生新ID|待实现；服务替身与真实服务证据分列|
|R4 身份与故障|错home／摘要／operation／result、缺源、不同actor、同ID异Experiment／job／run／memo、symlink、丢回复重试均保留拒绝／unknown语义；未选中成功旧轮不被统一fence|待实现；优先扩原fixture／suite|
|R5 安装与交付|新非editable安装／283参考；实际新旧登记CLI旅程、原提交／取消／注册回归，自身原模板、新fresh-context两轴、普通精确发布和自己的CI|待R2–R4，不借b1或前片成功|

实施进度写入本片交付和[总计划](../PLAN.md)。仍开放的b3不可续期预算／全周期executor、c Temporal循环、d实际CPU循环及真实B3／完整Forge条件不因本片恢复成功而关闭。
