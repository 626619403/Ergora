# c1a1：总控制器意图准备

日期：2026-11-15。基线`fbafd8d7fc442acb8c52e0646ada327cdfb49fa3`。这是[总Workflow计划](2026-11-15-training-cycle-workflow.md)的第一个完整产品片；前置b2b本地验收与独立审查已闭合，远端逐片门禁保持。kernel专家继续保留v3。

## 行为与owner

在`training_cycles.prepare_controller`准备既有schema2授权的完整`controller/intent.json`。参数为原project、cycle、authorization SHA及expected revision；准备不创建attempt／receipt、不调用SDK、不启动候选或训练，也不重新授权。返回`created`、完整intent／canonical SHA及最后重新观察的cycle；只有其中cycle仍ready才可进入后继投递用例，准备结果本身不是执行许可。

`CycleAdmission.intent_record()`从原授权纯生成已有完整intent，原`controller_intent()`消费者和本片producer共用它；字段、SHA及错误保持。不新增模块、依赖、持久schema、source key、模板、CI分组或通用发布器；不反向导入worker。后继SDK投递、attempt／固定run对账仍独立交付。

本地准备在既有State reservation内固定项目修订，不跨任何RPC。先由原`status`核完整授权／ready实际发布、原clock、当前项目和停止；publisher仍持原cycle锁时可见ready不算完成。只在原共享父许可下发布，保留最后stop检查。首次用原`_record`的file-fsync→无覆盖link→directory-fsync；重复只验证原完整intent、同步原目录并重读，不覆盖原件或重开时钟。发布期间出现null-intent stop可以让最终intent无法绑定，但其不可逆veto必须保持，不能修复停止文件。最终重新观察耗时后的原计算窗口；exhausted不能返回ready。

初审R1实证要求最后clock观察晚于全部业务文件读取：保留显式父check，在它之后取最终status；原`_status`把同一次schema2 stop观察移至clock前，stop仍覆盖unknown／exhausted，不复制clock算法。原耗尽测试沿目录同步、最后authorization读取、status的stop读取三个真实阻塞接缝验证，旧r1结果保持原身份。

## 可验收节点

|节点|必要证据|进度|
|---|---|---|
|实现|两个既有owner、原格式共用、真实调用方向与完整diff|本地实现／验收／独立两轴已闭合|
|源码接缝|原publisher持锁时不准备；幂等／同步失败重试保持原bytes／inode／clock且无attempt；stop在link前到来；全部业务I/O消耗原compute|R1修后r3共25通过／54.94秒，原失败探针独立复跑已返回exhausted；旧结果另保留|
|安装回归|新非editable core／SDK与源码／wheel一致、283参考及依赖；原授权／父gate／停止与架构相关检查|修后r2两安装652／283／依赖通过；35通过／145.43秒，core实际0.070秒；旧r1身份保持|
|独立审查|Ergora自身原结构模板；新的fresh-context需求／维护性两轴，实证问题修正|修后自身模板31.493秒approve；新独立最终本地两轴approve／开放0／0，R1关闭|
|固定／发布|固定本片本地提交；普通发布仍等所有前片准确CI及原reviewer终核|本地门禁闭合，可固定；远端仍待原逐片门禁|

每步见[交付](../delivery/2026-11-15-training-controller-intent.md)。真实独立cycle服务、总Workflow、CPU两轮和GPU／业务训练不属于本片验收。
