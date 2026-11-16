# c1d M5-G：完整前驱与原最后准入实施

2026-11-16。状态：开始隔离源码实施前核定；尚无产品／测试／安装／模型或fresh实施验收。依据[已审设计](../plans/2026-11-16-training-cycle-predecessor-native-gates.md)及[独立设计审查](2026-11-16-training-cycle-predecessor-native-gates-design-review.md)，不开放schema3效果或ordinal1。

实施基线为固定父留存产品 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，其父为已验M2产品68ba793。父留存源码／新安装／自身模板已完成，根仍单独进行其最终整片独审；本片不把它的成绩转授新改动。隔离分支 `feat/training-cycle-predecessor-gates`，持久worktree为ignored `.ergora/worktrees/training-cycle-predecessor-gates`。

固定M2实际算法重核：report binding、four-fact判定、acceptance和previous编排仍在worker；当前没有原生第二caller，故不先单立M5-P或为复用落无人调用helper。M5-G接真实protocol／budget／Execution／native消费者时，同片迁移所需纯计算并删除重复，机械迁移和新认证按diff分块审。State／SDK／archive读取与publish编排留其原owner。

交付范围是完整前驱链、原25来源＋四measurement与ROOT／所选安装，以及原submission、registry、request／launch、native attempt／ack同步后的最后检查接线。保留明确schema3关闭分支；不得用新开关、伪source或信任参数启动新训练。正式V2／v3、全部M1c与实际两轮统一开放沿[已审M6设计](../plans/2026-11-16-training-cycle-v2-runtime.md)另片交付；M5的纯正例不能关闭尚不可达的实际effect正向验收。

检查复用原submission／runtime测试和operation fixtures，保留真实锁／fd／S-H／reaper与callback，按已审矩阵逐项注明可达及未到达边界。固定源码、新非editable包、原结构模板及新的fresh两轴实施审查各自记账；不新增CI job、放宽时限、复制archive reader／manifest walker、改283原件或新建账本／证明文件。具体变更、运行和未验项将按实际结果追加。

## 隔离实现进展：原件认证与首个完整局部正例

实施树准确基线仍为 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，开始时干净。重核固定 M2：原 report binding／state／acceptance／pin／selection 只有 worker 调用；随新的 protocol 本地认证真实消费者同片迁移，没有预先 M5-P。共同约束常量由原 `training_cycles._COMMON` 移至 protocol，原 owner 直接引用同一常量；State、SDK、archive、publish 编排保持原 owner。机械迁移 patch 单独保存在 ignored `.ergora/checks/cycle-predecessor-native-gates/01-pure-migration.patch`，最终新增认证 diff 另记。

新增本地认证已经接入 BudgetedStart.source、validate_context、H 前驱读取；prepare 增加 intent 同步后 source 复核，Execution.current 重读完整当前链，native callback 在入场、attempt 同步后、ack 同步后重读并仅接受本次对应阶段的 records。来源复用原25键集／owner出生 pin、四 measurement 出生值和 reference.verify，未增加第二 archive comparator 或白名单。源码仍开发中，尚未冻结或独审。

首轮探索 `exploratory-01.log` 为2失败／1通过，失败原因是机械替换误改一处 `validate_round_acceptance` 调用名，已定位修正；原 native 锁接缝通过。随后独立新目录 `exploratory-02.log`：**3 passed／55.20s**，原 M2 collect/reconcile、k1 和 k3 全链认证及最早 index 原 raw 漂移拒绝通过。k3 实际读取3份原前驱，正例后 Budget.source 仍明确 schema3关闭；这是合成原库存与服务替身的本地认证，不是 schema3 新 start 或真实训练结果。

额外确认原 `test_training_cycle_controller.py` 的 schema3 native 反例故意没有完整 controller。新认证应先拒绝缺失的完整绑定，旧断言仅需移除过窄异常文案，保留 ValueError、无新效果与已有 result 早读。native 外层继续保留 schema2原许可顺序；schema3 外层原父许可及全部新效果正向按 M6 开启表延期，不能因 callback 早关而宣称 attempt/ack 更晚门已经可达。后续将沿实际 callback／fd／原锁接缝验证 schema2最后检查和大原件实际 reader。

本片私有检查目录以0700创建，文件按077 umask保存；没有完整环境快照、凭据输出、依赖安装、模型、真实训练、外部服务、commit、merge或push。以上只认证当次探索输入，最终候选及安装／自身模板／fresh实施审查尚待根流程。
