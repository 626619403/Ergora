# b2b0：训练循环记录读取与State初始化解耦

日期：2026-11-15。本地产品基线`d1c728087423d85ed55f06010ec81e5e1d4b2fd1`，分支`refactor/architecture-foundations`。承接[已批准的停止监管设计](2026-11-15-training-cycle-stop-supervision.md)，先完成行为保持的记录读取整理，再接b2b异步operation及fan-out。前片本地独立两轴已通过，但远端发布仍等待其前置自己的CI；本片可本地实施，后继远端按顺序交付。

实际调查：`training_cycles._directory/_origin/_authorization/_controller/_load`只需`State.root`，不查询SQLite。现有真实生产调用位于training_cycles、reference_training_budget和reference_training_worker。`State(...)`却会创建home、获取`.schema.lock`并可能迁移数据库。新的inspect-only H如果沿这个构造方式读取原记录，就不是设计要求的只读检查；用伪造State、重复校验器或新增通用repository接口也没有必要。

本片将这五个原私有函数的首参数统一为`home: Path`，原公共应用入口保留State并传`state.root`。三个原owner的全部真实调用共同迁移；授权、ready、锁、读取上限、canonical／raw SHA、原clock和失败行为保持，不移动或重写校验算法。现有应用入口中原先已经存在的State生命周期不在本片改造。后继inspect-only H可以直接向同一读取算法提供已核控制目录，无须初始化State。

不新增文件族、wrapper、reader基类、registry、公共命令、持久schema或数据迁移；不新增异步运行、通知、drain或停止成功主张。kernel专家仍保留在v3路径。没有目标业务框架变更。

|节点|验收|状态|
|---|---|---|
|b2b0.1 原调用调查|固定三owner和五函数、State实际构造副作用、d1完整基线|已核；没有修改产品|
|b2b0.2 原参数迁移|只把原home依赖显式化，迁移全部调用；AST归一比较算法保持|三个原owner已实施；完整AST在唯一参数／调用归一后相同，无新产品文件或方法|
|b2b0.3 相关验收|新非editable安装／652与283／依赖；原授权、ready、恢复、停止与架构相关接缝；真实既有原件离线读取，不初始化State、不改变DB／锁／记录|两新安装各652／283／依赖通过；真实原件禁止State＋持schema锁离线读通过／0.091秒，原坏夹具拒绝保留；最终原安装27通过／57.10秒及1个owner收尾已核|
|b2b0.4 审查与交付|更新根PLAN／逐步交付，自身原模板、新fresh-context两轴，按前片门禁普通发布与自己的CI|自身原模板20.475秒及新的fresh-context最终本地两轴approve／开放0／0；可固定本地提交；远端发布／自己的CI仍按前片精确门禁分别接续|

逐步证据见[所属交付](../delivery/2026-11-15-training-cycle-offline-reader.md)。本片仅为b2b1异步operation和b2b2具体停止fan-out消除不必要的数据库构造依赖；两者仍须完成原设计的并发阻塞、取消／回收、同一截止与实际原owner通知验收。
