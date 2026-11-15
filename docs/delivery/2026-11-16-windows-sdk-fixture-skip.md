# Windows SDK fixture 提前跳过修正

日期：2026-11-16。状态：实现／局部验证／新的fresh独立两轴审查完成，已固定并逐字导入开发分支；发布及候选自身官方 CI 待完成。基线 `3a176c75f4afdc73f9fbe96ffd37a7fb26854f4a`；隔离工作树 `windows-sdk-skip`。本片只修改 `tests/test_training_submission.py` 两处既有测试的平台装饰器，不修改产品、fixture、预算、断言、参数或 CI，不增加测试文件。

## 观察与原因

官方 push／attempt1 [43747795571](https://github.com/626619403/Ergora/actions/runs/43747795571) 的候选为 `86356927cd88750717bb910502e3f7bd66aa41ba`。完整 annotations 已保留于专属本地检查存储，并读取核实：Windows 的六项 setup 错误均为 `ValueError: Native training submission requires Linux; use the registered runtime in WSL2`，涉及 `test_cycle_sdk_start_retains_parent_failures` 的 `popen / cleanup / oversized-parent` 与 `test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes` 的 `operation-request / oversized-stdout / oversized-frame`。官方原结果 1190 passed、976 skipped、6 errors／1459.85 秒保持，不能改写为成功。该 run 最终 failure，六个 Linux job 均 success；Windows PowerShell 5.1 安装升级 success 与原生回归 failure 分别记账。

这两函数依赖 `cycle_sdk_activity → controller_dispatch → controller_admission`。fixture 需要真实 Linux 原生提交、controller 授权及 supervised S/H；产品 `reference.training_submission` 明确拒绝非 Linux 的非 status 操作。测试函数体在 fixture setup 后才执行，因此不能依赖函数体内的后续逻辑避免该错误。邻近 SDK 测试已经使用函数级 `skipif(sys.platform != 'linux', ...)`。本片在两函数各自既有 parametrize 前补同一邻居装饰器，理由同为 `SDK activities consume the original supervised Linux H`。

## 验证与边界

复用现有 SDK 非 editable 环境的解释器；其包身份不由本次测试变更重新认证。执行以下轻量检查，未执行训练或启动 S/H、Temporal 服务，也未重新运行 Linux 全量回归。

- 保存并运行独立检查脚本 `check_boundary.py`。先在 Linux 正常导入依赖，只在选定测试模块重新导入时局部设置 `sys.platform='win32'`，`finally` 立即恢复，随后使用真实 `pytest.main` 收集和执行原六节点。pytest 与 pathlib 的执行平台保持 Linux。
- 修前相同六节点没有 skipif，真实 pytest setup 到达 fixture setup 钩子；该钩子立即抛出 sentinel，得到 **6 errors／0.50 秒**。首次 fixture 为 `tmp_path_factory`，其函数体也未执行。这是 fixture 前跳过缺失的最小反例；原 Linux 提交 ValueError 的真实反例仍以官方 annotations 为准，不把 sentinel 称作 Windows 原生故障复现。
- 修后相同模拟选择 **6 skipped／0.04 秒**，全部发生在 setup，fixture setup 钩子调用为 **0**；六个 mark 条件均为 true。证明实际 pytest skip 发生在所有 fixture setup 前。
- 原生 Linux 纯收集同一六节点成功，所有新增 skipif 条件均为 false。逐节点身份与修前模拟收集完全相同。逐字核实移除新增的两行后恢复基线文件，原测试体、fixture、参数与既有标记全部保持。
- 隔离工作树 `git diff --check` 通过，diff 为一个测试文件、两行新增。

可复核命令形式为：`<existing-sdk-python> check_boundary.py <isolated-worktree> windows`，Linux 收集使用 `linux-collect` 参数。脚本、修前／修后输出、Linux 收集输出、汇总 JSON、准确 patch 和官方匹配 annotations 摘录保存在项目 ignored 专属检查目录 `windows-sdk-fixture-skip`；原官方完整 annotations 仍在 `ci-training-shards/publication-r1`。原件路径及解释器的本机绝对位置只通过交接提供，公开文档不记录机器目录。

上述检查验证测试选择及 pytest setup 顺序，不认证原生 Windows 执行、SDK 活动产品行为或新候选官方 CI。六个参数的 Linux 活动行为没有变化，故按机械标记变更采用收集及边界检查；原 run 的六 Linux 成功只属于其原候选。下一步由协调者组织 fresh 独立审查，更新主计划后再决定导入与提交，最终以新候选自身官方 Windows／Linux CI 记账。

## 独立审查与固定导入

[fresh独立审查](2026-11-16-windows-sdk-fixture-skip-review.md)实际核官方六错误、完整两行diff、fixture闭包与三份轻量原件，需求／维护性均approve，开放0。隔离候选固定为`958a6fe`；主分支普通cherry-pick为`39ec257`，对src／tests／scripts／.github／pyproject逐字比较差异0。未强推、未改main；暂与即将验收的消费者合并后普通发布，避免为同一联合候选重复发CI。原863失败保持，新候选自身CI仍待实际运行。
