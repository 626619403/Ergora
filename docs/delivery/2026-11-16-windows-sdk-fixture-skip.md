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

后续消费者bcc已真实导入01ef，逐字比较其tests只多本片两行mark；联合候选`879654c5c0989e1880af85293296897a0d2b7089`已普通推送开发分支并核精确远端同一。自己的官方push／attempt1 [43752183692](https://github.com/626619403/Ergora/actions/runs/43752183692)当前in_progress；旧863六setup错误不改写，新候选全平台结果待定。未新增重复CI矩阵或改变原时限。

## r2：新增消费者窗口测试的平台标记

根协调者在消费者合入后静态发现另一可达 Windows 失败：`tests/test_training_runtime.py::test_cycle_execution_sdk_keeps_one_work_window_without_parent_file_reads` 的四个参数节点没有平台标记。它调用 `budget_clock.authorize(wall) → budget_clock._clock()`，后者在非 Linux 明确抛出 `ValueError('Budgeted native operations require Linux; use WSL2')`；后续 `_CycleOperation` 也使用原 Linux boot clock。因此本例固有 Linux 执行边界，保留真实 BOOT 时钟检查，不能通过模拟 clock 将其描述为跨平台测试。这是新消费者测试的 call 阶段静态风险，**不属于原 8635692 官方六错**，也没有声称新 Windows 官方运行已经复现。

原两处 submission 标记已提交为 `958a6fe7792ef2d5ac2c1030c0bdb72b1d68269a`。本次在同一专属树普通合入固定消费者 `01ef69b`，形成准确实施基线 `bc602a38c9658bab8f8f431ac48f4969c76ebf95`。核实该 HEAD 的产品、测试、脚本、CI 和配置与 01ef 逐字相同，已包含此前两处 submission 平台标记。新未提交差异仅在 runtime 模块增加标准库 `import sys` 与该既有函数前一个 `skipif(sys.platform != 'linux', reason='SDK work windows use the original Linux boot clock')`，共两行。不改原四参数、fixture、产品、时钟、预算、断言及其他测试。

r2 复用原轻量边界脚本，仅将所选模块／函数改为上述 runtime 函数。依赖先正常导入，只在所选模块 reload 时局部设置 win32，随后立即恢复 Linux；实际 pytest setup 阶段仍在宿主 Linux。修前四节点触发首个 fixture setup sentinel，**4 errors／0.30 秒**，不执行 fixture 函数体或测试 call；它只证明缺少提前 skip，并非原生 Windows call 失败复现。修后 **4 skipped／0.02 秒**，fixture setup 钩子调用为零。Linux 纯收集 **4 tests collected／0.02 秒**，四个新增 skipif 条件均 false；前后及 Linux 三组节点身份完全一致。逐字移除这两新增行可恢复基线文件，`git diff --check` 通过。未执行 Linux 四个活动场景、全量 suite、安装、服务或训练。

r2 脚本、修前／修后日志、Linux 收集日志、汇总 JSON 与准确 patch 独立保存在原专属检查目录的 `r2/`，没有覆盖 r1 六节点历史。patch SHA256 为 `25b2968d03bd0cc8308c75d6ac9de9bf179b273eafc0f75eb1e013fec79be2b3`，基线如上。

r2 已取得[新的独立审查](2026-11-16-windows-sdk-clock-skip-review.md)，需求／维护性均 approve、开放 0；协调者已核准确两行并固定导入开发树 `c52fc0a338118a19491ad7cd458b82cf2f146a9b`。其完整差异只有上述 runtime 测试的标准库导入与装饰器；原 Linux 时钟测试保持。c1c 实施树已普通合入此提交，产品不因该测试修正变化。尚未推送本次 r2，故在途 879 候选自己的 CI 不含该修正；最终发布及新候选自己的必要 CI 分别记账。

之后官方 879 候选自身 run `43752183692` 已终态 failure。其 Windows 完整 annotations 核实恰为本函数四参数的 `ValueError: Budgeted native operations require Linux; use WSL2`，与此前静态 call 路径预测一致；这是官方实际四失败，不能与此前局部 setup sentinel 混记。六 Linux job 全部 success，group5 15分04秒内完成，未调高原20分钟时限；Windows 安装升级的具体结果沿该 run 原 jobs 另记。官方原响应保存在消费者 `publication-r2/`。原六 setup 错误已不再出现，但这不把 879 总 CI 改写为成功。c52 的修正已经独立验证／导入，接续普通发布及自己的全平台 CI。
