# Q4.2c0.2a：自动循环的出生同意与父停止记录

日期：2026-11-15。细化已独立通过的[具体合同](2026-11-15-training-cycle-controller-contracts.md)第一、三节。准备基线为 `e09fd60a635f16e9265b18d1529c4934e687f303`；其 652 个产品文件仍等于 ac86043，只修测试与同步文档。前置e09自己的CI八job／30必要步骤及双方原reviewer已终核闭合，实际实施基线为a10e693。a1–a5开始实施，a6仍待；本页不将已批准设计记为产品完成。

目标：在已有 owner 内提供 birth-only schema2 同意，以及供后继最后 gate 使用的普通文件、共享许可、停止观察与排空算法。保留 schema1 的完整字段、结果形状、时钟、旧 start slot 和恢复语义。kernel 专家继续保留在 v3。Linux／WSL2 同一可信主机和用户边界不变。

## 现有接缝与变更所有者

|现有代码|本片动作|边界|
|---|---|---|
|[training_cycles](../../src/ergora/training_cycles.py) 的 `authorize`／`_authorization`／`_load`／`_status`|复用同一授权算法；新增独立的 `authorize_controller(..., confirm=True, execute_selected=True)` 应用入口；按具体合同验证完整 schema2|普通 `authorize` 仍只创建 schema1；已有 ID 不能换模式、输入、操作者或时钟|
|同一 owner 的 `_record_bytes`／`_record`|普通授权、完整输入和 ready 继续原临时文件 fsync 后 link 的算法；schema2 在 ready 前创建并同步 `controller/admission.lock`|不改变原记录格式或静默修补缺失的 authorization／cycle；ready 后缺锁不重建|
|[training_execution_protocol](../../src/ergora/training_execution_protocol.py) 的 `_fd`／`read_raw`／`decode`／`sync_directories`|在这个既有被 pin 的 stdlib owner 内实现父停止记录读取、既有锁的共享许可及排空观察|不新增源 key、模块、插件总线或原生依赖；不从原生解释器导入 State、jsonschema、SDK|
|[reference_training_budget](../../src/ergora/reference_training_budget.py) 的 `BudgetedStart.source`|增加 schema／binding 对应检查，阻止新 schema2 经过原三字段手工 binding 派发|这是本片的必要关闭条件。完整 controller binding／实际 gate 接线仍归 c0.2b；schema1 不受影响|
|[既有 submission 测试](../../tests/test_training_submission.py) 的 cycle_selection／原服务替身／历史档案|沿原入口验新旧授权、部分持久化、原身份、拒绝普通派发及真实 flock 交错|不复制整套服务、进程回收矩阵或新增 CI job；可移植历史读取保留|

新低层父许可可以采用同一文件内一个内聚的记录对象，供应用停止、worker 与 native gate 共同使用；不是新的调度器。其调用方先完成自己原有的完整来源、clock 与身份验证，父许可只增加原授权绑定和 stop／共享锁约束，不能单独授予 start 或 launch。

## 授权与兼容

schema2 的字段、稳定 workflow ID、queue、执行范围、continuation、actor 和布尔确认严格沿具体合同，不另加默认自动模式。完整 canonical SHA 包含全部 controller 字段。记录出生前取当前操作者；历史读取与重复操作保留原操作者，不把当前环境写回旧记录。

原 `authorize` 算法只作局部参数化，继续先永久保留 ID／原 clock／完整 cycle 再实时 admission。两种入口的重复操作必须核原模式；不能利用丢回复、ready 缺失、相同输入或新软件升级旧同意。原发布中断导致 authorization／cycle 缺损的行为保持，不在本片增加补造原件的恢复。

只有完整 schema2、原 clock 未失效、原 admission 一致和新锁持久化完成后才能发布原 ready。锁只在授权尚未 ready 的同一出生流程创建；已有普通锁仅同步／重读，缺损、FIFO、symlink、reparse 或非空内容都可见拒绝。ready 后 reader／gate 只打开既有锁，不在读操作中创建它。

新增字段仅属于 schema2；schema1 的 `_status` 和 coverage 形状保持。显式同意、预算 ready 和执行已获准是不同事实；本片仍没有可运行的自动 start／execute。普通 binding 无法消费 schema2，避免在 c0.2b 完整准入交付前出现缺少父最后 gate 的执行通路。

## 停止文件、许可与持久观察

停止记录的完整身份、可空的原 controller intent SHA、原 actor、reason、UTC 时间与严格字段集沿具体合同。记录路径及应用操作属于 `training_cycles`；共享文件读取和锁算法属于 `training_execution_protocol`。读取不调用当前会动态导入 native `dev_platform` 的 `_match`／`publish`。若确需 canonical SHA，使用该 stdlib owner 内局部且与原格式相同的实现，不把应用依赖下沉给 native。

**停止文件是不可逆的准入否决。** 普通 `_record_bytes` 在临时文件 fsync 完成后才 link 到目标；这不适合证明“目标文件 fsync 阻塞时停止已可见”。因此本片为 stop 使用语义明确的普通目标 `O_EXCL` 创建：路径先可见，随后写入完整内容、flush、fsync 文件及原父目录，再同步重读同一文件。这个差异留在停止 owner，普通发布算法保持。

创建后崩溃或写入不完整的文件永久阻止新准入；观察返回可见、持久未知和具体原因，不补写、不替换，也不把它当正确停止证明。若文件已完整，重复停止只同步／重读原 bytes，保留第一次 reason／时间／actor，不因调用的新文案发生变化。并发首次请求由 `O_EXCL` 选出同一原记录；另一请求只观察它。

父共享许可只打开既有普通锁，以非阻塞 flock 获取。取得后再核原授权和 stop 路径；任何 stop 路径（包括损坏、特殊文件或读取失败）均禁止新动作。拿不到锁不在低层新增 sleep／计时器；有界等待由后继独立操作进程及原 budget owner 负责。c0.2b 才把此许可覆盖 start RPC、registry create、execution request／launch 和原 native process 的全部期间。

停止观察至少区分：路径可见、完整身份匹配、`stop_durable`、`admission_drained`。持久确认必须同步现有文件与父目录并重读相同 raw bytes；排空必须在 stop 可见后取得父排他许可，并再确认同一记录。排他锁只保护父准入，不拿 submission／registry／executor 锁。`admission_drained=true` 不能推出进程后代已停止；`executor_stop_confirmed` 本片保持 unknown，直到原 c2 chain 的真实回收／持久观察提供证明。

本片仅实现记录／许可用例。**公开 live stop、独立 writer／各 owner 通知／drain 的 fan-out 监管留在 c0.2b**；直接的存储函数不能声称在总预算内返回，也不能放进原 live owner 或未来 SDK event loop。本片不向 CLI／HTTP 暴露一个会同步等待业务文件的停止命令。

## 可验收子节点

|节点|必要检查|当前状态|
|---|---|---|
|a1 出生同意|新旧授权、完整摘要／原 actor、重复操作与模式冲突、原 ID／clock 不变；原 ready 和 input 保持|已实施；最终r3安装／对应原件通过，本地独立两轴通过；发布／CI待|
|a2 普通父锁|ready 前锁持久化，部分 fsync／丢回复、ready 后缺锁不补建、普通文件边界；原 schema1 无新增锁|已实施；最终r3安装／对应原件通过，本地独立两轴通过；发布／CI待|
|a3 停止记录|真实可见文件与阻塞 file／directory fsync分列、重复／并发请求原 bytes 保持、部分／坏身份／FIFO均拒绝，持久恢复只同步同一完整记录|已实施；最终r3安装／对应原件通过，本地独立两轴通过；发布／CI待|
|a4 许可与排空|真实跨进程共享锁仍活时排空 unknown；stop 可见后新共享者拒绝；原共享者退出后才可 drain；排空不声称 subtree stopped|已实施；最终r3安装／对应原件通过，本地独立两轴通过；发布／CI待|
|a5 关闭不完整执行路径|schema2无法经旧三字段binding／普通cycle-start派发；原schema1旧流程和历史SDK-free档案保持|已实施；最终r3安装／对应原件通过，本地独立两轴通过；发布／CI待|
|a6 完整交付|固定最终源码／非editable安装、283保持、原接缝必要回归、自身原模板及新的fresh产品reviewer，再普通发布和自己的CI|待前置与a1–a5|

先对本页作 fresh-context 设计审查，不把它当产品审查。实施时另建交付记录，列明实际 caller、原件、失败、最终身份及未验范围；若共享许可的具体结构影响 c0.2b 调用或恢复，先回写具体合同再实现。后续 c0.2b、c1 进程／queue 隔离及总 Workflow、c2 公共交互、可信 CPU 示例和真实训练验收保持独立依赖，不因本片记录能力完成而提前关闭。


## 独立准备审查结果

新的fresh-context[设计审查](../delivery/2026-11-15-training-cycle-admission-plan-review.md)已给需求／维护性两轴approve，开放设计finding 0；固定三计划、652产品和283参考身份已核。原报告10047B，SHA256为0088b20d92bedccbb3202d3a367328037259a267298fa45510e696daddc31720。此结论只允许继续准备，a1–a6没有产品实现或竞态验收；前置Q5.2a自己的CI及独立终核闭合后才实施。

## 产品实施接续

a1–a5已沿三个原owner实施；r1安装选择51项及追加意图绑定1项通过，但自身模板／独立反例确认null stop的完整身份R1。已在原protocol最小修正，源码两项通过；r2新安装／必要回归／自身复审及原fresh reviewer终核后才关闭a1–a6。普通派发仍关闭，后继完整gate／fan-out／真实worker保持未实现。详见逐步交付。

最终r3两新非editable安装各652三方逐字／283／依赖、54项选择及六CLI原件／SQL保持已验；原结构模板57.874秒approve。R1／R2实红及同owner最小修正已分列，原fresh reviewer正在最终本地终核。普通发布及自己的CI仍待，a6未闭合；自动派发保持后继完整gate交付前关闭。

原fresh reviewer最终本地需求／维护性两轴approve，开放0／0，R1／R2关闭，已核54项／六CLI／652与283及原模型证据。a1–a5本地完成；a6普通发布与自己的CI待，未放行后继产品。

## 固定发布接续

已普通发布 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`；原独立reviewer核18份staged blob、完整tree／Ref、652产品及283参考后，固定发布两轴approve／开放0／0。a1–a5的本地证据保持，a6仅剩自己的CI终态及原reviewer续核。08:07 UTC官方查询为匿名REST限额403（remaining=0，08:23 UTC reset），没有已核run／job verdict，原响应完整保留。等待期间仅准备后继设计，不开放完整自动派发。

## a6精确闭合

自己的CI `43693023635`／push／attempt1已completed success，八job／30必要步骤全部success。原reviewer核原HTTP身份、固定发布和精确矩阵，最终两轴approve／开放0／0；最终报告19,896B／SHA256 `8db11e6100ed0287c3fb9a959c0aa73ac277d234e75fca38b683afd21095fab9`。a1–a6精确闭合，仅归07cbae；不认证后继完整gate／fan-out／总Workflow。403和原中间状态保持。
