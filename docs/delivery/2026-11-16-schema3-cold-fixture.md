# Schema3 cold fixture CI 回归修正

状态：[fresh独审](2026-11-16-schema3-cold-fixture-review.md)需求／维护性两轴approve，开放0；产品 `e3a436933eb31d0ea5d18d22d0f615fc82aa2253` 已普通合入开发分支 `a975098eebb39eaba6dcf43a83605854c1f8bd86`。原失败与修后定向证据保留；尚未推送或认证新候选CI。

## 问题与合同

准确基线 `eba86805e5d50824eefb5e69edd0faab099cbf42` 的官方 CI [43807888266 attempt1](https://github.com/626619403/Ergora/actions/runs/43807888266)为 7/8 jobs 成功。Ubuntu group2 唯一失败是 `test_schema3_intent_is_local_and_all_execution_entries_remain_closed`。原件位于 `.ergora/checks/design-training-expression-integration/publication-r1/` 的 `current-summary.json` 与 `20261116T053126Z-failed-job-annotations.json`。

原 fixture 无 snapshot／activity_context，`_CycleOperation(..., 'inspect')` 因而选择 operation-v1。实际 H 的 `_cycle_operation` 读取 schema3 授权后先拒绝协议身份；原断言却要求执行关闭原因。版本化后的 `inspect` 本身是只读入口，不能据此证明执行关闭。

修改仅在独立工作树 `.ergora/worktrees/schema3-cold-fixture`、分支 `fix/schema3-cold-fixture` 的 `tests/test_training_cycle_controller.py`。原用例保留 cold v1 精确身份拒绝；随后复用 `_cycle_snapshot` 的原计划／完整授权，为 `prepare-controller` 显式选择 operation-v2，走真实异步父调用→S 监督进程→H 子进程，要求精确返回 `Schema3 controller execution is not enabled`。未修改生产 gate、config、其他测试、CI 分组或时限。

两次调用均核 unknown 的精确原因、已认证 stopped 帧、S 返回码 0、H process 观察成功，以及 controller 原件逐字不变。原用例的本地意图复用、漂移、截止期、显式存储停止及无 controller attempt／服务 start／训练 submission／budget／job 检查保留。未新增测试函数或参数矩阵。

## 实际验证

使用既有 `.venv-dev/bin/python`，未安装依赖或修改环境。父测试从隔离工作树收集，子进程导入主树 editable 产品；已逐文件核主树全部 tracked `src/` 字节与基线同一。

|检查|实际结果|原件（仓库根相对路径）|
|---|---|---|
|原用例、原 fixture|1 failed，7.70 秒；精确复现 protocol differs 与原预期不符|`.ergora/checks/schema3-cold-fixture/before.argv.json`、`before.raw.log`、`before.xml`|
|原文件中 `schema3 or controller_original_type_is_authenticated_read_only`|6 passed，80 deselected，20.10 秒|`.ergora/checks/schema3-cold-fixture/after.argv.json`、`after.raw.log`、`after.xml`|
|完整差异空白检查|`git diff --check` 通过|独立工作树实际差异|

6 项覆盖 schema3 出生／原件身份、本次真实 S/H 关闭动作、managed 与 managed-v2 原生回调拒绝及既有结果读取、v1／v2 原始 workflow 类型只读认证。服务调用部分使用既有服务替身；未执行真实 Temporal 服务、训练、安装验收或新候选官方 CI。该检查证明本地真实 S/H 生命周期与受管 fixture 接缝，不转授业务质量验收。

## 冻结身份与交接

- baseline：`eba86805e5d50824eefb5e69edd0faab099cbf42`。
- 完整 tracked 输入 2071 文件，新 untracked 输入 0；唯一源码差异为上述测试文件。
- `.ergora/checks/schema3-cold-fixture/candidate.patch` SHA256：`e179a86ad04cab599232772a78f7f526e7efac7c78fd9c82a7e5678a14404169`。
- `complete-input-manifest.json` SHA256：`889fd356478b2d4fe16391b3416d4be6c9c63fdab93e616a1c8ff05338fbb920`，含每文件字节 SHA、执行位、symlink／tracked 属性。
- 测试文件 SHA256：`f2d48cbc59330cc9f0270e8b8a80a56d3abc4cb04a176e9e44667e11f4086838`。
- `candidate-identity.json` 保存基线、分支、完整输入数量、差异文件、实际解释器／产品导入及运行结果。

根代理接续：以这些冻结原件独立审查需求与维护性，再决定普通导入／发布及观察新候选自己的 CI。本记录是主树本片唯一文档写入，根 PLAN 由根代理统一维护。
