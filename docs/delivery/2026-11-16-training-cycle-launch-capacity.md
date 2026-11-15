# c1b2a 完整 launch 容量分类修正

日期：2026-11-16。隔离分支 `feat/training-cycle-service`，修改起点 HEAD `eedba08c8c112683a7946726aab3f4fd590f26d6`，服务片集成基线 `478c98891522930817fa7005a8ac96e408f37230`。本次响应自身结构模板 Codex 原审查提出的 launch 容量疑点；原回复保存在 ignored 验收目录的 `self-review-r2-codex/review.md`。

本次按 maintainable-project-delivery、ergora-codebase-quality 和仓库组件协议核真实调用路径，仅改两个既有产品 owner 与原测试文件。PLAN、安装包、发布及最终独立审查由主控接续；本报告不标作独立审查通过。

## 可达性与原反例

疑点成立。`_candidate_operation` 先通过原 `_prepare_submission` 发布不可变 intent 并同步，再调用 `BudgetedStart.launch_context`。完整 launch 包含整个已注册项目，operation snapshot 仅包含 compact authorization/policy/candidates，两者容量并不等价。原 guard 在 intent 已占位后抛普通 `ValueError`；H 的原异常投影固定为 `unknown`，SDK adapter 因而返回 unknown 封套，遗漏合同要求的非重试容量拒绝。

新增原接缝 `test_cycle_sdk_launch_capacity_keeps_occupied_intent_without_another_offer` 在**首次真实注册之前**添加 schema 允许的完整 check 参数，随后沿原 registration、cycle create/authorize、controller prepare、真实 SDK ActivityEnvironment 和真实 S/H 运行。未伪造 launch、预算或 intent，也未注入容量异常。

|采样|原产品|修后|
|---|---:|---:|
|业务 activity request JSON|475 B|464 B|
|prepare operation request 原件|4043 B|3977 B|
|operation snapshot JSON|2112 B|2068 B|
|完整冻结 project JSON|44601 B|44535 B|
|按完整持久输入重建的未发送 launch JSON|46467 B|46324 B|
|H stdout 原件 status|`unknown`|`capacity_exceeded`|

前后路径长度不同导致 byte count 略异，均显著跨越同一 32768 B 门槛。重建值只用于字节核算，不是捕获到已发送的 launch；真实原 guard 的完整错误原因及 H stdout 原件同时保留。

正式原反例 `before-confirmed.txt`：**1 failed，22.31 秒**。失败前已经通过以下断言：同一 intent 字节与 inode 不变，重复 start、SDK attempt=2 和 reconcile 全部只走 `reconcile-candidate`，只有一个 prepare，没有 owner、start attempt 或 SDK start，原 authorization/ready 字节不变。最终准确失败为 H `status='unknown'`，对应 SDK 没有抛出 typed 非重试错误。

两个更早的 fixture 探索结果单独保留：`before.txt` 尝试重写已发布注册，被原不可变注册正确拒绝；`before-real.txt` 的有效项目仅 28571 B，未到 launch 反例所需采样量。两者不作为产品缺陷证据，最终 fixture 在首次注册前选取更大的有效 check 后重新独立运行。

## 最小修正

- `reference_training_budget.py`：仅将原完整 launch 的既有 32 KiB guard 改抛 `training_cycles._CycleCapacityError`，复用同一个 `ValueError` 子类，不改变原阈值、完整序列化、错误原因、intent 占位或 launch 目录创建顺序。
- `reference_training_worker.py`：H 原异常投影仅对该精确类型返回 `capacity_exceeded`，继续保留完整 reason；普通 `ValueError`、OSError 等保持原 unknown 语义。后续 S/frame/adapter 沿现有容量合同抛 `cycle_activity_capacity_exceeded`、`non_retryable=True`。
- `test_training_submission.py`：只在已有文件增加上述真实回归，复用既有 fixtures，无新 CI 分组、fixture 文件、账本或调度器。

没有截短 launch、输入或事实；容量失败不产生预算根，恢复不产生第二 offer，不重授 clock/预算。三个产品/测试文件最终差异为 57 insertions、2 deletions。

## 验证、身份与边界

使用现有 SDK 验收解释器、SDK 1.34.0，显式 `PYTHONPATH=src:tests` 导入隔离树源码。`source-identity.json` 核明实际 `ergora` 导入为隔离树 `src/ergora/__init__.py`。**本次是源码验证，尚未验收新非 editable 安装包。**

修后 `after.txt`：**9 passed，114.79 秒**，命令为原 `python -m pytest -q` 加下列已有测试入口与新回归，完整实际命令的解释器和持久 basetemp 由主控验收目录记录：

- 新 launch 容量回归：typed 非重试拒绝，完整 H 原因、intent 与 existing-only 恢复均保留。
- `test_cycle_sdk_start_hands_off_once_then_duplicate_only_reconciles`：原正常创建、移交与重复调用生命周期。
- `test_cycle_sdk_dispatch_rechecks_prepare_activity_source_after_attempt_sync`：真实 H 中普通来源 `ValueError` 仍为 unknown，已有 attempt 保留且 SDK starts=0。
- `test_cycle_candidate_lost_prepare_reply_never_recreates_its_root_offer`：丢 prepare 回复后不重建 offer。
- `test_cycle_candidate_root_cleanup_waits_after_notification_races` 两项：自然退出与通知异常时实际 wait/reap 保持。
- `test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes` 三项：原 operation request、stdout、frame 容量路径及 peer 收齐保持。

`git diff --check` 通过。未启动 live 服务、未重跑大 suite、未 commit/push、未更改 PLAN 或其他报告。未把服务替身与 SDK ActivityEnvironment 检查称为真实 Temporal server、正式 Workflow、训练执行或 GPU/质量验收。

主树 ignored 证据根：`.ergora/checks/training-cycle-service-acceptance/launch-capacity-r1/`。保留 `before-confirmed.txt`、`after.txt`、各自持久 `*-tmp` 的完整 request/stdout/intent、`samples.json`、字节核算 `sample.py`、`source-identity.json` 与 `changes.patch`；探索日志另存且不覆盖正式反例。

最终三文件 SHA256：

|文件|SHA256|
|---|---|
|`src/ergora/reference_training_budget.py`|`d002c88e79bc3d856c86415511d307636d4a11698168ece6100e18824b149d4e`|
|`src/ergora/reference_training_worker.py`|`ab67539284cdc6b47d95c8e402170c5515d906cbd1f810f16d0e93d5b692c928`|
|`tests/test_training_submission.py`|`eb272c1d8626ab1b5910975196f23eead81e16331ab8c374c1d335d9c6e4dc6b`|

下一步由主控固定该产品候选、构建新包，再用新的 fresh reviewer 与自身模板复核最终实际差异。旧安装和旧审查结论不能继承到本次新产品。
