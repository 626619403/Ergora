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

## 精确候选首次独立采样：CI 未终态

本节补核普通提交推送后的固定对象 `03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`，唯一父对象确为 `61ccc2cce8bfcc3a46b4a069c78ea660f76063d9`。实际恰为前述七文件，测试内容与本地审查身份一致；独立审查后的差异仅是允许的文档状态记账。C2 `workflow.js` 在该对象中与父对象相同，C2 未跟踪 delivery 不在对象内。

**2026-11-09 12:27:42.378738 UTC**，从固定 Git 对象读取的 **435 个包文件**与 R4 保留 wheel、非 editable 安装及原身份表逐项一致；wheel SHA256 仍为 `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`。**283 个冻结文件**均符合原 manifest，Git 模式/对象身份也与父对象相同；Portability 工作流未变化。此项不使用当前 C2 工作树作为候选源码，没有重建或重新安装包。

已读原 CI 抓取/验证脚本逻辑，并在本片新独立目录保留原脚本及本轮采样实现。原验证脚本以 Success 为前提；本轮对非终态如实记账，不借断言失败推定 CI Failure。官方 Actions 精确候选行、run 原页、完整 job-group（`totalCount=2`、`hasMore=false`）、实际 job 的 `selectedJobId`、完整 SHA check/log URL 与步骤属性均直接核验。

**2026-11-09 12:27:43.119174 UTC**，本候选自己的 [Portability run 42616678385](https://github.com/626619403/Ergora/actions/runs/42616678385) 仍为 **In progress**。实际 Ubuntu job 为 `129158155380`、Windows job 为 `129158154892`；两 job 的构建安装和冻结身份步骤已见 success，两份 Native application regression 仍在运行，Windows 安装器步骤尚未开始。两 job 尚无终态完成标记，**七个必要步骤未通过终态门禁**。本轮各官方资源只取一次，没有轮询、取消或重跑。

**2026-11-09 12:27:39.344558→12:27:40.793613 UTC**，在确认不属于 Git 仓库的目录，清除继承 Git 环境覆盖、禁用 system/global 配置及凭据助手、禁用 SSH/HTTP 协议后，对明确 `https://github.com/626619403/Ergora.git` 执行只读 `ls-remote`。原 trace 确认实际调用 `git-remote-https`；远端 `refs/heads/refactor/architecture-foundations` 返回完整 SHA **`03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`**。

原对象差异、包/冻结身份表、官方原页和单次采样、明确 HTTPS trace/回执及其 SHA256 汇总，均保存于本片私有 `independent/commit-closure/snapshot-01/`。`closure-sample.json` 固定本轮证据身份；后续采样须另存，保留本次 In progress 原件。

对象、R4 包/冻结身份及明确 HTTPS 门禁已通过；Standards / Spec 仍为 **0 开放 finding**。**自己的双 OS 七个必要步骤仍待终态，03f1f58 精确交付尚未终结。** 本次未运行模型、浏览器、服务、安装或测试，也未改写原 61ccc2c CI Failure。

## 精确候选终态复采：交付终结

本节更新上节待终态项，固定候选仍为 `03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`，只复采明确指定的原 run **42616678385**。`snapshot-01` 全部证据 SHA256 已复核完整，原七文件对象、435 包文件与 R4 一致及 283 冻结身份的通过结论继续保留；当前 C2 工作树没有参与本候选验收。

**2026-11-09 12:41:11.657510 UTC**，官方 run 已为 **Success 终态**。完整 job-group 只有两 job，`totalCount=2`、`hasMore=false`；两 job 均为 completed/success。独立核对实际 job 的 `selectedJobId`、每个必要步骤的 success 与 `data-job-completed` 标记、绑定完整候选的 check/log URL，确认七项全部通过：

|官方 job|Build and install wheel|Packaged reference identity|Native application regression|Windows PowerShell 5.1 installer and upgrade|
|---|---|---|---|---|
|[Ubuntu 3.11，129158155380](https://github.com/626619403/Ergora/actions/runs/42616678385/job/129158155380)|success|success|success|平台条件不适用|
|[Windows 3.12，129158154892](https://github.com/626619403/Ergora/actions/runs/42616678385/job/129158154892)|success|success|success|success|

**2026-11-09 12:41:08.475411→12:41:09.857455 UTC**，重新在非 Git 目录清除继承的 Git 环境覆盖，禁用 system/global 配置、凭据助手及 SSH/HTTP 协议，对明确 `https://github.com/626619403/Ergora.git` 作只读 `ls-remote`。原 trace 再次确认实际调用 `git-remote-https`，远端 `refs/heads/refactor/architecture-foundations` 返回完整 SHA **`03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`**。

本轮官方 Actions/run/job-group/两 job 原页、单次采样和明确 HTTPS 原回执另存私有 `independent/commit-closure/snapshot-02/`，由 `closure-terminal-success.json` 固定证据身份。未覆盖 `snapshot-01`，没有取消、重跑或持续轮询，也未运行模型、浏览器、服务、安装或测试。

**03f1f583f91c6f1b2f35b89ff8d0d513f40c519d 的对象、R4 包/冻结身份、本候选自己的七项必要 CI 及明确 HTTPS 远端门禁全部补齐，精度修正精确交付终结。Standards / Spec 均通过，0 开放 finding。** 原 `61ccc2c` 的 CI Failure、早期诊断失败与首次 In progress 采样继续保持原状态；本结论不构成 C2 验收。
