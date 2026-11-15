# c1b0：有界异步控制器准备操作

日期：2026-11-15。基线为已固定的c1a1 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`。该片本地独立两轴闭合，远端仍按原顺序。[总计划](2026-11-15-training-cycle-workflow.md)中的SDK投递需要一个真实受监管的普通操作边界；现b2所有已知效果mode只用原total，而原`reference._training_process`只有单次timeout与收尾余量，不能把它们当作普通compute∩control截止。因此先交付本普通边界及真实c1a1准备caller，再接SDK attempt／dispatch／对账，避免增加另一进程driver或reaper。kernel专家保持v3。

## 本片范围与明确边界

沿原`_CycleOperation`／`cycle_operation_main`和`processes.run(supervised=True)`添加内部`prepare-controller`mode。输入仍是完整原snapshot／身份，ordinal为null；H沿原`training_cycles.prepare_controller`准备同一不可变intent，不启动Workflow／候选或训练，不创建attempt／receipt，不装载SDK。它是为后继普通操作铺设的真实接缝，不是独立cycle服务或自动循环验收。

|owner|变更|保持|
|---|---|---|
|training_execution_protocol|新增mode的完整验证；同一bootstrap字段保存普通操作一次性BOOT窗口；remaining取该窗口与原compute较小值|inspect原1–60秒观察界、停止mode原total、stdlib依赖、GATE_SOURCES key集合|
|reference_training_worker|在实际spawn前固定一次原compute remaining∩control timeout窗口；H组合原准备入口，结果出界为unknown|原S／H、4异步pipe／wait task、shield取消／spawn与唯一reaper；停止fan-out、原budget入口保持|
|training_cycles|作为既有被调用owner，不复制其准备／State／ready／stop／项目算法|原c1a1产品逻辑不改；准备结果不是执行许可|
|原tests／fault fixture|已知普通窗口、SQLite或同步阻塞、stopped后结果读取、耗尽不spawn的实际接缝|复用现有fixture／测试文件与分组，无另一调度或断言矩阵|

所有业务文件／State／SQLite／fsync留在H；异步父loop仅内存、clock、进程身份与管道。父pipe／wait、S stop_requested与H前后active检查使用同一已固定窗口，poll、取消及本次operation内部不重置。普通截止须属于原boot，跨度不超过原control timeout，不能晚于原compute BOOT上界；每次remaining还核原UTC／BOOT连续性。原compute已尽时不spawn任何H。

准备是不可变元数据操作；超时或有结果的停止观察仍可能已有intent落盘，操作只能返回unknown并保留原件。调用者取消沿原shield取回真实spawn／回收后继续抛CancelledError；此时已发布元数据的执行状态仍未知，不能删除原件、重开clock或视作执行许可。最后训练副作用的精确准入仍由后继SDK／原四gate片负责。本片不承诺跨进程重启恢复普通请求；未来SDK活动若恢复同一operation，必须携带原窗口而非重新构造截止，并在其独立片实际验收。当前唯一单次operation在重复poll／取消期间保持同一原payload。

## 验收节点

|节点|证据|进度|
|---|---|---|
|具体设计|原caller／clock／四task／reaper路径及独立设计核对|新的独立设计两轴approve／开放0／0；取消措辞R1关闭|
|实现|原protocol／worker内完整mode，实际S-H准备caller，不添产品文件／依赖|已实现，源码／最终安装及新的独立产品两轴批准已核|
|源码|真实准备成功／原intent幂等；普通control先到与compute先到均受限；阻塞H时并行asyncio心跳响应及stopped后结果、取消、耗尽不spawn；原停止仍用total|r1共24通过／60.55秒；随后marker原子发布只修测试，最终安装另验|
|安装|新core／SDK各652源码／wheel／安装逐字、283及依赖；相关原父gate／停止与架构回归|两安装652／283／依赖、33通过／156.96秒，core实际异步准备1.157秒通过|
|审查／固定|自身原模板、新fresh-context产品两轴、原件／已知actor；普通本地固定，后继远端门禁保持|自身原模板26.433秒approve；新的独立产品需求／维护性两轴approve／开放0／0，22已知actor活匹配0；接续固定本地提交|

每步见[交付](../delivery/2026-11-15-training-cycle-prepare-operation.md)。未实施的总SDK投递、独立normal／stop Worker与配额、Workflow、c1d接受／rounds门槛、公开入口及真实CPU两轮继续开放。
