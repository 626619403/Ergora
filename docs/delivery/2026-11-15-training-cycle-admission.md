# Q4.2c0.2a：出生同意与父停止记录交付

日期：2026-11-15。遵循[具体实施计划](../plans/2026-11-15-training-cycle-admission.md)与[原控制器合同](../plans/2026-11-15-training-cycle-controller-contracts.md)。准备计划及纯文档发布已独立两轴 approve；前置Q5.2a的精确CI及其原reviewer、c2原reviewer的接续终核现均闭合。开始a1–a5实施，a6安装／审查／发布和自己的CI待。尚无本片产品验收结论。

Git 准备基线为 `a10e69389e228d311df56bad182b9798f4ca236d`，其产品和测试等于 e09fd60；652 个产品文件仍等于 ac86043。当前其他文档差异属于既有 CI／设计的状态接续，不冒称工作树为空。

## 实施边界与已有所有者

修改原 `training_cycles` 的授权算法／schema 分支、`training_execution_protocol` 的 stdlib 父记录与许可、`BudgetedStart.source` 的授权／binding 共同检查，以及原 submission 测试。根据实际接口补组件协议和架构，不先建立新模块、调度器、插件或实验账本。普通授权和历史结果的形状、原 clock、start slot、native 算法、人工 release、283 冻结文件、CI 矩阵与依赖保持；kernel 专家继续留在 v3。

新的同意只在出生时显式记录；普通入口仍产生 schema1。父共享许可只约束已有最后 gate，不能自己授予执行。stop 的不可逆可见路径、同文件持久确认、父准入排空与原执行子树停止分别观察。c0.2b 才接完整 controller binding、最后 gate 和独立停止 fan-out；c1 才提供实际总 Workflow／独立 worker，c2 才接公共交互。本片不公开一个同步等待业务 I/O 的 live stop 命令。

## 验收记账

|子节点|产品／实际检查状态|
|---|---|
|a1 新旧出生同意及原 clock／ID|已实现；源码原actor／完整摘要／跨模式／确认通过；最终r3安装回归通过|
|a2 ready 前普通父锁及中断恢复|已实现；源码三同步中断恢复及ready后不补锁通过；锁同步截止已在最终r3通过|
|a3 可见停止、完整原件与持久 unknown|已实现；源码三个实际进程阻断点／并发原件／坏文件通过；持久失败恢复已在最终r3通过|
|a4 真实共享许可／排空交错|已实现；两个真实Python -S持有进程及原退出顺序通过，子树停止保持unknown|
|a5 schema2 无法走旧三字段派发|已实现；普通cycle-start和training.start共同拒绝，原slot／owner／RPC未产生|
|a6 非 editable 安装、原接缝、自身模板、新独立产品审查及发布／自己的 CI|最终r3 core／SDK各652／283／依赖、54项及六CLI、自身模板approve已验；本地独立两轴approve；普通发布／自己的CI待|

开始产品后在此逐项追加真实源码／安装身份、实际命令与结果、失败和修正、审查结论及剩余范围。局部替身、真实文件锁、实际服务、CPU 合同与真实训练分列，不将一项成功扩大为另一项验收。

## 实施开始

以a10e693固定原产品／测试，原件和新检查保存于ignored的`.ergora/checks/training-cycle-admission/`。复用同一授权发布算法；在既有stdlib protocol中增加内聚的`CycleAdmission`，只负责完整授权绑定、既有空锁、停止文件及非阻塞共享／排空许可。应用侧持有路径和出生同意；未来controller最后gate再使用这些许可。低层不等待、不导入native／SDK，不在本片开放自动派发或公共live stop。

## a1–a5 首轮实现与检查

三个原产品owner已接线，没有新增产品模块或依赖。schema2完整确认包含原actor／稳定workflow ID，普通授权保持schema1；同ID跨模式拒绝，原clock不续期。ready前无覆盖发布并同步空父锁；ready后缺失或非普通空锁直接拒绝，不重建。新schema2在`BudgetedStart.source`共同边界拒绝旧binding，两个真实手工入口都没有落intent／attempt／owner或发RPC。

`CycleAdmission`隐藏普通文件读取、完整授权／停止身份、先可见O_EXCL停止、同inode／同raw同步重读、非阻塞父共享许可与排他排空。已有controller intent时只接受原完整固定身份并记录其canonical SHA；此前停止可保留null。没有producer／controller调度器。`stop_controller`仅为受监管helper可调用的存储用例，不是live owner或SDK loop中的同步停止命令。普通status对schema2追加只读停止观察，schema1形状保持。

首个私有驱动把venv解释器resolve为基础Python，因缺pytest在产品收集前失败；source-r1单独保留。source-r2实际源码在新controller目录尚未创建时误调会lstat的`is_link`，11项均未完成（3失败／8setup错误）；已在原目录边界修正。source-r3实际源码11项通过／28.96秒，含三个独立进程阻断点（空可见文件／文件fsync／目录fsync）、两个真实共享持有进程、并发O_EXCL、部分／坏身份／FIFO拒绝及SDK-free Python -S。所有已知子进程由对应Popen收尾。新增锁同步截止及同原件持久恢复检查，随最终安装统一验；不把源码11项转记为安装验收。原架构16项通过／0.39秒。

## a6 固定r1安装

wheel SHA256 `39d55847e980f67ca369a2857ff5f3916a3cc03d99e6e629afba7c592dbbf23d`。core和含Temporal1.34.0的SDK非editable新安装各652产品文件与source／wheel／site逐字相同，只有上述三份原产品文件变化；283冻结参考及两依赖检查通过。全部14项新检查、原schema1授权／丢回复／并发恢复、原managed create／原slot、SDK-free历史链及完整架构边界正从冻结测试执行；实际nodeid清单与JUnit单列，不扩大为全套测试或真实训练。原低层- S子进程检查确认没有yaml／jsonschema／Temporal／State／native包导入。自身原结构审查及新的fresh-context产品审查随后接续。

## 自身模板R1、实际反例与最小修正

原`ergora-structure-review@1.0.0`实际Codex审查61.776秒，完整15文件397,343B及三祖先资源均逐字进入stdin，需求request-changes，维护性认可原owner边界。使用既有Claude超时后的授权Codex回退，不声称后端多样性。其P2指出null stop遇到后来出现的controller intent时未核完整绑定；原r1安装实红1失败／3.41秒，实际给出了错误的identity／durable／drained=true。原独立reviewer另行复现相同持久读取边界，并核同raw换inode／排他拒绝共享探针。

接受R1：无条件读取现存intent并与停止记录的可空SHA严格相等；既有stop重试先观察原件，不先用后来意图／新reason构造另一份。失配或损坏保留同stop bytes与永久准入否决，身份／持久／排空unknown；不修补或追认新意图。源码两项（非null原绑定漂移、null从缺席变出现／坏intent）通过／5.73秒，新的r2两安装及受影响最终回归、自身模板复审正在进行。r1的51安装通过／159.19秒和非null追加1通过／3.33秒保持原候选身份，不转授r2。

私有CLI驱动的前两次准备错误为pytest `current`软链接重计、截断目录名猜错，前者未调用产品，后者已执行四条状态读取但整项未完成；最终旅程换用固定真实目录并逐条记录。原日志保留，不把它们描述为CLI产品失败。

## 自身r2复审R2与同步后重核

r2两新安装各652／283／依赖已验（wheel `846a37dcc51402d6e558d963909c82c4914e152570069ccfeb7742a046ce96a5`），原选择53项通过／164.17秒。自身模板92.068秒维护性approve、需求request-changes，指出在持久同步阻塞期间原intent仍可能变化：同步前通过的匹配不能直接复用到同步后的durable／drained。新独立reviewer以r2安装在排他drain的第二次真实stop文件fsync中注入完整intent，独立复现三字段错误true；原r2安装新增精准回归实红1失败／3.42秒，原stop bytes保持。

接受R2：同inode／同raw同步重读成功后，最后再次核原授权与完整stop／现存intent，再报告当前身份和持久确认；失配将identity=false、durable／drained未知，保持可见停止否决。只在原读取owner增加这次跨阻塞边界复核，不新增锁／调度器或修补原件。源码精准回归已通过，r3最终两新安装、含17项新检查的54项选择、自身复审及独立终核接续。原r1／r2通过和失败分别保持原候选身份。

## r3最终本地回归

最终r3 wheel SHA256 `34381db249f707e766bcd09f4e175c26b6f462194cce00b527b060f2d78f7fa3`。新core／SDK各652份source／wheel／site逐字相同，仅三原产品owner有变化，283及依赖全部通过。冻结安装选择54项通过／166.34秒（命令167.468秒）：本片17项新检查、原schema1授权／丢回复／并发恢复、原managed create／start slot、SDK-free历史链和完整架构16项。它是明确的原接缝选择，不称全库suite或真实服务／训练验收。

R2源码精准反例1通过／3.73秒；独立reviewer另用r3安装Python -I -S实际复核相同同步窗口转绿，原stop保持。self-review-r3首驱动在模型调用前误用不存在的配置路径；原准备scope／input保留，改用相同15全文的`self-review-r3-retry.py`与已有配置，结果尚待。真实六条core／SDK CLI状态旅程正在跑；源码／模型／安装及后续远端CI分别记账。

## 最终自身复审与交互检查

相同r3产品的原`ergora-structure-review@1.0.0`复审57.874秒，需求／维护性approve；15完整文件405,026B、三祖先资源和完整任务均逐字进入真实stdin。结果原件SHA256 `217bb482cf45ec19c22634a9714df7ce9d2a27670303fa1d0804b1369e87e3b1`，位于`self-review-r3-retry-codex/`；它是完整所供文本审查，不替代原件／安装／远端审计。初始失败driver没有发起模型调用。

r3实际六条CLI全部0退出：core／SDK各观察完整stop为stopped、FIFO原件为unknown、普通schema1为ready；只读stop观察仍保留durable／executor stop未知，原完整authorization、所有周期文件bytes和SQL内容保持。没有启动Temporal、训练或新的本地owner。两原生命周期R1／R2的失败、最小修正、源码与新安装转绿均分列；新的fresh-context reviewer正在最终核所有原件，普通发布／自己的CI仍待。

## 最终本地独立终核

新的fresh-context[产品审查](2026-11-15-training-cycle-admission-review.md)已对固定r3产品／测试及r4最终状态给需求／维护性两轴approve，开放0／0，R1／R2关闭；两安装、54项、六CLI、原模板完整stdin／原result均独立核过。报告本地终态13,019B／SHA256 `701eb5d483d031af7c9d0fd8775c6b7572b9ffee351571eded6735b26605c8a9`。此快照随后可追加固定发布／CI续核，不改写本地结论身份。

a1–a5本地实现与验收闭合；a6普通发布／自己的CI仍待。准备只普通推送当前开发分支，不合main，不新建重复CI，不把原r1／r2失败或前片CI改记成功。下一产品片仍是完整controller binding／父许可最后gate及独立停止fan-out，再接真正总Workflow与公开交互；当前没有可运行的自动多轮控制器。

暂存前私有链接检查把有效目录链接当作Git index blob，因而未生成暂存清单；后续发布驱动也在读取缺失清单时停止，没有commit或push。已区分目录的tracked子路径与文件的精确暂存blob校验；不改产品、测试、CI或审查结论，不重复产品回归。
