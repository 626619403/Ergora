# 研究耗时浮点比较：独立审查

审查者：`deadline_precision_review`，全新独立上下文；先读项目 `AGENTS.md`、`docs/PLAN.md` 和适用的 maintainable-project-delivery / codebase-design 指引。最终本地复核时间：2026-11-09 12:21:54 UTC。仅授权写本报告，未修改源码、安装、启动服务/模型、运行测试组或提交推送。

## 范围与身份

固定基线为 `61ccc2cce8bfcc3a46b4a069c78ea660f76063d9`，当前分支 `refactor/architecture-foundations`。直接检查相对该基线的测试差异、原测试及 `src/ergora/research.py` 相邻实现，再核原始证据和交付叙述。候选共七文件：

- `tests/test_research.py`。
- `docs/PLAN.md`、`docs/plans/2026-11-09-composition-console.md`。
- `docs/delivery/2026-11-09-definition-console.md` 及其 `-review.md`。
- `docs/delivery/2026-11-09-deadline-precision.md` 和本报告。

工作树另有 C2 的 `src/ergora/data/console/workflow.js` 和未跟踪交付记录，两者均不属于此候选。本审查未把它们当作精度修正或 R4 包源码。两份计划的 C2 文本只作后片状态记账，不构成 C2 验收结论。

测试最终 SHA256 为 `33e8b7cc483fb5783f9a682af39d383a93d15cd00a18e8057616070dd42467a5`，与本次 `r1/arithmetic.json` 一致；测试基线差异 SHA256 为 `b1dd5eed2afa10dfcaf94b48af8350904da1dd5dd906aa0d6ecd27efe579b7d9`。运行时 `research.py` 与基线、R4 非 editable 安装文件逐字相同。

## Standards：本地通过

唯一代码修改位于原测试 `tests/test_research.py:190–191`：保留严格 `status == "timed_out"`，仅把耗时精确相等改成已有 pytest 的 `approx(30)`。没有新增函数、文件抽象、生产断言、防御分支、依赖或 CI 工作流；不需要新的 module、interface 或 seam。修正在拥有此断言的现有测试内，保持 locality。

原测试仍从真实 monotonic 起点固定父端时钟，等待真实响应头 started 握手后推进 30 秒；真实 spawned 网络子进程、10 秒外层等待和 finally 释放均保留。原 `_download` 的父端检查、杀进程和回收路径未变，`run.check` 的 `monotonic() >= deadline` 与 `checkpoint` 的浮点差值语义也未变。因此未移动 deadline 决策到近似比较，未扩展运行预算或以速度阈值替代结果合同。

此切片复用原研究组验证，没有新增镜像实现的测试或 CI。已有 **11 passed、1 skipped / 11.79 秒** 的受影响组证据与改动风险相称；无需为这一断言重复模型、浏览器或产品服务验收。所列候选没有运行时或冻结文件变化，保留六阶段及 283 冻结合同；最终 Git 对象身份尚待下节门禁确认。

## Spec：本地通过，精确交付待证

直接读取原官方 `snapshot-02/` 的 run、完整 job-group、两份 job HTML 及终态 JSON。run **42612128319** 绑定完整基线；七个必要步骤六成功一失败，Ubuntu Native application regression 的唯一失败正是原精确比较。官方 annotation 明确给出 `timed_out` 和 `29.99999999999997`，汇总 **1 failed、1304 passed、84 skipped、36 subtests passed / 838.44 秒**；Windows 四必要步骤成功。交付文档如实保留该 Failure，没有把原 C1 本地通过写成 CI 通过。

使用保留 R4 环境做无网络的独立算术核验：`(226.4 + 30) - 226.4 == 29.99999999999997`，精确比较失败、`pytest.approx(30)` 通过。默认容差为 `2.9999999999999997e-05` 秒，即 30 微秒；29.9 和 30.1 均被拒绝。此处只允许浮点表示误差，严格超时状态和等待约束继续检查实际控制行为，没有证据表明它掩盖本片应保护的 deadline 合同错误。

本次实际 `r1/research-tests.log` 为 **11 passed、1 skipped / 11.79 秒**。它使用 C1 R4 原非 editable 包；保留 wheel 的实际 SHA256 已复算为 `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`，与原身份表相同。本审查没有把当前 C2 工作树当该包，也未用此结果替代未来候选自己的双 OS CI。

早期 `reproduce.py` 缺 spawn main guard；带 guard 的 `reproduce-safe.py` 仍把父端起点设为 226.4，而网络子进程保留真实 monotonic，不能共享绝对 deadline 时钟域。两份原日志均失败于 started 等待，不是官方耗时断言的网络复现。当前记录已区分这一限制与独立 IEEE-754 算术核验。

## 发现与同片复核

1. **DP-D1 / P2，候选文档缺失目标，已关闭。** 初查 `docs/PLAN.md:21` 和 `docs/plans/2026-11-09-composition-console.md:18` 引用未跟踪且明确排除的 C2 delivery；若整文件纳入候选，会在交付对象中断链。实现者已把两处改为无链接的本地状态文本。按“基线文件集 + 本片明确文件集”复查候选文档目标，没有缺失目标；未为补链纳入 C2 文件。
2. **DP-D2 / P3，跳过原因表述不精确，已关闭。** 初查精度记录第 21 行将跳过概括为可选依赖条件；原测试第 285 行首先按是否显式选择隔离 Temporal 服务 skip。现已写为“未显式选择专用隔离 Temporal 测试服务”，与原条件一致；没有声称该服务得到本次验收。

最终 **Standards 0 开放 finding，Spec 0 开放 finding**。两项发现均是文档修正，源码修正本身无阻塞 finding。

## 检查与未完成门禁

已完成只读 Git 状态/基线差异、相邻运行时与测试检查、原官方页面和实际本次日志核对、测试/运行时/wheel 身份核验、无网络算术检查、候选文档目标检查和 `git diff --check`。本次没有重新运行原网络失败、测试组、完整应用或远端 CI。

尚待固定七文件提交后，独立核对：精确候选及唯一父对象、排除 C2 的完整文件集、全部包文件和 283 冻结身份、该候选自己的双 OS 七个必要步骤终态，以及明确 HTTPS 读取的远端完整 SHA。上述门禁完成前，只能记本地审查通过，不能记精确交付终结。原 61ccc2c CI Failure 和早期诊断失败继续保留。
