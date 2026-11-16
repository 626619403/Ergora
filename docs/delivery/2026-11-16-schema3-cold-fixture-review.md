# Schema3 cold fixture 独立审查

审查者：fresh-context 独立 reviewer `schema3_cold_fixture_review`。日期：2026-11-16。仅写本报告；未修改源码、安装依赖、提交或重跑测试。按根／tests AGENTS、组件协议“脚本和检查”、maintainable-project-delivery 独审要求及 ergora-codebase-quality 的测试接缝／仓库风格引用开展审查；先读补丁及真实调用，再读作者交付与运行证据。

## 结论

|审查轴|结论|
|---|---|
|需求符合性|approve；本片范围内无 finding|
|维护性|approve；本片范围内无 finding|

本修正保留 cold V1 身份不符的真实拒绝，并用明确 V2 身份的关闭动作验证真实 S/H 边界。没有将任意 unknown 或失败当作通过，没有修改产品 gate、预算、时限或 CI。允许接续普通导入与新候选自己的官方 CI；本审查不宣称该后续 CI 已通过。

## 准确范围与身份

基线及隔离工作树 HEAD 均为 `eba86805e5d50824eefb5e69edd0faab099cbf42`；分支 `fix/schema3-cold-fixture`。隔离工作树 `.ergora/worktrees/schema3-cold-fixture` 仅有 tracked `tests/test_training_cycle_controller.py` 改动，无 untracked 文件。完整实际 `git diff --binary` 与候选补丁逐字相同。

- `.ergora/checks/schema3-cold-fixture/candidate.patch` SHA256：`e179a86ad04cab599232772a78f7f526e7efac7c78fd9c82a7e5678a14404169`。
- `complete-input-manifest.json` SHA256：`889fd356478b2d4fe16391b3416d4be6c9c63fdab93e616a1c8ff05338fbb920`。
- 独立逐项核对 manifest 的 2071 个文件：字节 SHA、长度、执行位及 symlink 属性均相符。测试文件 SHA 与 `candidate-identity.json` 一致。

主树当前在途仅 docs 文件；逐一读取基线 669 个 tracked `src/` 文件，主树对应文件字节全部同一。使用既有解释器从隔离工作树以 `-B` 导入 worker，实际路径确为主树 `src/ergora/reference_training_worker.py`。因此作者关于 editable 产品来源及产品字节同一的限制说明准确；本片没有非editable安装证据。

## 需求与真实接缝

`tests/test_training_cycle_controller.py:1551` 附近的两次调用仍走 `_CycleOperation.run` → 独立 S → `processes.run` 中的 H → `_cycle_operation`。`reference_training_worker.py:90` 根据 snapshot 的 schema3 授权选择 operation-v2；无 snapshot／activity_context 保持 operation-v1。H 在读取完整原授权后先核协议身份，再在 schema3 的 `prepare-controller` 等执行动作上拒绝。

因此第一项 `inspect`／无 snapshot 精确要求 `Cycle operation protocol differs from its complete original authorization`，保护原 V1 身份边界；第二项复用既有 `_load`／`_cycle_snapshot`，以原计划及完整授权调用 `prepare-controller`，精确要求 `Schema3 controller execution is not enabled`，确实到达关闭 gate。没有模拟关闭服务或直接调用内部 gate 来替代子进程。

两项都要求 unknown 的精确 reason、`operation_stopped is True`、S 返回码 0，以及首帧中 H process 的 `succeeded`。`PhaseFrames.receive` 对首帧执行完整身份、顺序、输出位置及 process 观察校验；S 在 H 执行及回收后才发 stopped 帧。这里 `succeeded` 是 H 正常返回受控拒绝的进程观察，不表示业务执行成功。意外异常、超时、缺帧、错身份或不同失败原因不能满足这组断言。

新增的 controller 目录文件集合／字节等值检查能捕获新增、删除或重写原件。原用例继续检查无 controller attempt、服务启动标记、训练 submission intent／attempt、budget 和 job，并保留本地意图幂等、源码漂移、原截止期与显式 storage stop 接缝。本修正没有开放 schema3 执行效果，也没有改默认 V1 路由。

## 维护性与证据

修改留在原有测试及 fixture 中，复用产品已有 snapshot 构造接口，无新文件、helper、参数矩阵或 CI 分组。两个具体场景的本地循环直接表达身份门与执行门的不同预期；精确原因在此用于避免把错门或普通故障当作关闭证据，属于有效回归保护。

已核作者[交付记录](2026-11-16-schema3-cold-fixture.md)、before／after argv、完整 raw log 及 JUnit XML。原记录为 1 failed（7.70 秒），失败原因与原断言不符；修改后为 6 passed、80 deselected（20.10 秒），XML 无 errors／failures／skips。六项节点确实包括 schema3 出生、本次 S/H、managed 与 managed-v2 原生回调、V1／V2 原 workflow 类型只读认证。另独立运行 `git diff --check` 通过。

官方原件 `publication-r1/current-summary.json` 与 failed-job annotations 绑定准确 eba 基线及 run `43807888266` attempt1，记录 7/8 jobs 成功，group2 为同一 fixture 唯一测试失败（408 passed、1 skipped）。这是旧候选失败证据，不能转为新候选 CI 通过。

## 限制与后续验收

本次独审未重跑昂贵测试，测试结果按保存原件引用。真实 S/H 运行覆盖本地进程／协议／停止边界；其余服务接缝仍使用既有 fixture 替身。没有真实 Temporal 服务、训练、GPU质量、新安装或新候选官方 CI 验收。后续由根代理记录普通导入后的准确身份并观察其自己的适用 CI；这些未完成项不影响本次仅测试最小修正的两轴通过结论。
