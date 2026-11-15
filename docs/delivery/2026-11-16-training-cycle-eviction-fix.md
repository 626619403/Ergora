# TrainingCycleWorkflow 普通活动取消与 SDK eviction 修补

2026-11-16。范围是首轮 Workflow 的普通活动取消策略及一个真实 SDK 回归；源码、新安装及原历史安装版回放已通过；新现场及完整产品终审由主控继续。本片未改首轮计划，不把原 r4 的运行结果转记到新源码。

## 固定输入与变更

产品专树基线 `fa78747d6c6ca62935fe6a44aa6db143c362baad`，接手时已有 r4 未提交变化。完整差异与原 r4 文件均私有保存；本修补相对接手 worker **只有一处枚举值变化**，既有 r4 变化保持。

|文件|接手 SHA256|修后 SHA256|
|---|---|---|
|`src/ergora/reference_training_worker.py`|`187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`|`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`|
|`tests/test_training_runtime.py`|`56f67f74aadbe8a0db53fd3ea7df22f9b2865327c104d8533871753e29c1e6a1`|`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`|

`TrainingCycleWorkflow._ordinary` 的 `start_activity` 从 `WAIT_CANCELLATION_COMPLETED` 改为 `TRY_CANCEL`。Core 可以在发出取消请求后完成本地 handle，Workflow 不再持有等待远端 ack 的任务进入 eviction。唯一 `_stop` 仍用 `WAIT_CANCELLATION_COMPLETED` 与 `asyncio.shield`，停止先排到独立 queue，再由原 stop owner 返回完整封套。普通 handle 的 done callback 保留；domain gates、预算、一次机会、source、权限及默认 sandbox 未改，SDK 仍为 1.34.0。

这项调整改变 Workflow 对普通活动取消确认的等待，不改变实际资源收尾的所有者。原 `_CycleOperation.run` 在调用者取消时 `request_stop()`，shield 等待真实 `_run` 完整结束／drain／reap 后才重抛取消。原 `_serve_cycle` 的有序关闭仍先等待 normal Worker 的 shutdown/run 全部完成，再关闭 stop Worker；普通 S/H cleanup 期间保留 stop 容量。SDK 本地取消完成与 Workflow 的 CANCELLED 结果均不证明 durable stop、许可排空或 executor 停止；stop 投影的未知语义保持。

## 先红后绿与实际覆盖

新增 `test_cycle_workflow_evicts_after_stop_before_normal_cancellation_ack`，复用本文件既有 `cycle_workflow` fixture 的输入、默认 converter 和完整合法 activity 封套。它构造 23 个事件的小型历史：cold 完成、真实 SDK `start.v1` handle pending、Workflow cancel、独立 stop 返回、Workflow CANCELLED；普通活动只有取消请求，没有远端 cancellation ack。真实 SDK Core Replayer 使用默认 sandbox，自己生成本地取消 resolve 并执行 `remove_from_cache`。没有 mock Future、没有按待测 cancellation_type 手填 resolve、没有第二 harness 文件。裸 Python activation 实例不执行 Core 的 TRY_CANCEL 语义，故本缺陷使用 Core replay 接缝。

1. **红：** 新测试先在接手 worker `187bda…` 执行，1 failed／11.46 秒。子进程因 eviction 挂起被 10 秒边界终止；stderr 精确包含 `RuntimeError: Eviction processed, but 1 tasks remain` 和 pending `ergora.training_cycle.start.v1` handle。原失败日志、JUnit、完整差异和源码身份单独保留，没有覆盖。
2. **绿：** 单字段修补后首次运行同 owner 的受影响接缝，26 passed／6.25 秒。随后补齐最终运行前冻结，对相同范围做一次固定输入验证：**26 passed、27 deselected／5.55 秒**，包含既有 21 activation、4 lifecycle 和新增 1 Core replay。最终运行的 853 输入文件及完整 Git diff 前后一致，`git diff --check` 通过。
3. **原现场历史的源码重放：** 不修改原 W7 history，以修后专树源码执行同一有界真实 Replayer，10,995,598 字节、SHA256 `5e1dda7daabad517fac30ce9abaad47c2875488d229499ed1af996c25131bb40`，**1.745 秒完成／exit 0**，没有 eviction 残留。此项使用现有 SDK 解释器显式导入专树源码，是源码验证，不能充当新 wheel 安装验证。

实际测试选择是 `tests/test_training_runtime.py -k 'cycle_workflow or cycle_service_closes_peers' -q --tb=short`，红阶段只选新增节点。私有验证记录保存完整 argv、解释器／cwd、前后输入冻结、完整 diff、原始 stdout／stderr、JUnit 和原 history 的只读身份；没有跑全 suite、runner、服务或网络操作。

fixture 的 `control_home` 使用 `str(Path.cwd().anchor)`，新 history 复用该值；临时历史使用 `tmp_path`，子进程通过实际 `training.__file__` 推导导入根并使用 argv。因此没有新硬编码 Linux home 或为通过测试削弱产品门禁。Windows 未实跑，旧候选的 Windows CI 不认证这些新增源码。

## 交接边界

源修补和受影响 SDK 接缝验证完成；**完整产品片仍未验收**。主控仍须从上述固定 raw SHA 构建新非 editable 包，重核实际安装／输入身份，并对新安装重放原实际 history、取得所需的新现场／S-H 清理证据、自身原模板审查与 fresh 独立两轴审查，更新主计划。本片没有安装、服务启动、训练、提交、push 或变更其他产品模块；没有使用原 r4 的 W2／W5 通过认证新源码。

## 新安装、原历史与自身模板核实

r5原字节保持上述身份。重新构建wheel raw SHA256 **`74e2f6f990a3f4125fcebd81b06f8729b24ec1a148db47a58037e49f60eacf86`**，新非editable core／SDK各663包文件与source／wheel逐字及执行位同一，283参考及依赖检查通过。core实际没有SDK，SDK为1.34.0；853项冻结输入前后不变。补充product inventory为662项，不将其误记作663项包清单。

在新SDK实际site-packages导入下，冻结测试副本整个runtime模块 **53 passed／54.32秒**，完整driver56.586秒／exit0，JUnit与stdout一致。新安装对未修改的原W7完整history **2.693秒／exit0、GREEN_REPLAY_COMPLETED**，没有eviction或pending start残留；history raw SHA仍为5e1dda7d…。

新的fresh独立源码[审查](2026-11-16-training-cycle-eviction-fix-review.md)需求／维护性均approve、开放0。自身原结构模板使用授权Codex回退，真实53.129秒／approve：18完整文件616866B及3份祖先资源，实际stdin679797B／SHA256 `f4a32ee8b7e2cd8afe39f81e066b11cb2e3c675d690ffe5e251f643e2977e957`，原回复SHA256 `aa204ebeb0bf27c83492a1f732b3fe769b54cf3ef9fc4cefb21bda3f90dc208d`。它只审完整供给文本，不能认证当时尚待的新安装或现场；新安装由本节独立实测记录。

原件位于ignored `cw1/package-r3/`（内部沿用r1文件名，以外层目录和摘要区分）及`cw1/self-review-r3-codex/`。原Claude420.60秒失败范围保留。下一步使用全新r5任务／授权／采样记录进行正式类现场验收；原r4的CPU／故障结果不转记r5，不启ordinal1。

## 完整产品片接续结论

新正式类代表性现场及统一收尾现已在[现场交付](2026-11-16-training-cycle-workflow-live-acceptance.md)闭合；[最终独立审查](2026-11-16-training-cycle-workflow-final-review.md)需求／维护性两轴approve、开放0。产品固定ec6dcbc并普通合入开发主线5b04b2b，准确字节保持本报告所列。发布和新候选自己的CI另验；本报告先前“待”段落保留当时交接范围，不覆盖最新结论。
