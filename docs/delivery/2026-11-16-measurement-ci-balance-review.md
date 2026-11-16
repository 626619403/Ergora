# Linux CI 有限再平衡独立审查

日期：2026-11-16。Reviewer：fresh-context 独立 reviewer `measurement_ci_balance_review`，未参与实现；按 maintainable-project-delivery 独立审查 brief 与 ergora-codebase-quality 的 repository-style／test-seams 检查。只新增本报告，源码只读；没有运行测试正文、安装、服务、网络、提交或推送。

## 两轴结论

- **需求符合性：approve。** 限定为已授权的两份完整测试文件 group5→group3 的纯 JSON 再平衡；覆盖与选择证据充分。开放 finding 0。
- **可维护性：approve。** 保留现有配置 owner、runner、plugin 和检查接缝；不引入重复测试、CI job、选择器或长期验证框架。开放 finding 0。

此结论不认证远端时长、测试正文组合通过、Windows 执行或最终 M2/r3 联合候选。没有发现需要修改源码或追加本机 suite 的实证问题。

## 准确对象与要求

审查根与 docs 均属于 Ergora。实际核实隔离树 `.ergora/worktrees/measurement-ci-balance` 的 HEAD 为 `610f111f0755edcfd8b4c582a7644ff79621c8ce`，分支 `fix/measurement-ci-balance`；tracked／untracked 状态只有 `scripts/ci/linux-groups.json` 修改。相对此基线完整 tracked diff 仅该文件，并与保存的 `config.patch` 逐字相同，SHA256 为 `b751bf77b0bb07de3b5bb3b1e17cf769a1ee7c34a2642a16309fc4fe6fd73b24`。

原始范围是持续推进计划时，仅按已有成本证据分散串行工作：完整 `tests/test_training_cancellation.py` 与 `tests/test_work_agents.py` 从5搬至3，六组／86唯一文件保持，不改正文、产品、runner、plugin、workflow、job数量及原时限，不重复运行无变化的测试。不把旧环境数据线性换算为20分钟保证。

已读根与 scripts AGENTS、当前 PLAN、组件协议“脚本和检查”、[原分析](2026-11-16-measurement-ci-budget-analysis.md)及[本片交付](2026-11-16-measurement-ci-balance.md)。根树审查时也是上述基线，另外两份报告为 untracked 文档；它们与隔离配置分别记账。共享 PLAN 当时尚未登记本片，交付如实标待审；由根任务在收到本报告后作状态更新即可，不需要递归审查记账。

## 实际检查与判断

1. 独立只读 Python 检查 Git diff、配置、保存的 collector 与选择日志，未调用 `verify.py`，避免改写证据。核实两个配置文件集合完全相同、六组、86唯一存在路径；文件数 `13/14/12/16/13/18`→`13/14/12/18/13/16`。唯一变更正是两份文件5→3。`git diff --check`通过。
2. 逐字核上述两份测试、原 runner／plugin 和 `.github/workflows/portability.yml` 与基线一致；完整 diff 也排除了其余产品／测试改动。两份测试 SHA256 分别为 cancellation `a97730396bfc42787e9a6dd8b18e59c5620ab1df05cb9bf01d5685a79a651142`、work_agents `208a002cf7c7fefecc825bb86a70cfcd9fd6529e865266ffdb414222a647a709`。
3. 限定读取 `.ergora/checks/measurement-ci-balance/` 的 manifest、原／新配置、diff、实际 request/result、phase 日志、验证脚本及 comparison。两个真实 runner 子进程均为 `--group all --collect-only`、exit0，耗时11.032／2.975秒；前后实际 collected node multiset 相同，2269节点且全部唯一，所有文件均已登记。phase 日志没有 start／setup／call／teardown 事件。解释器是既有非editable r2 SDK 环境，不是新包验收。
4. 读原 `PhaseLog.pytest_collection_modifyitems` 后核实适配对象完整提供了本选择分支消费的 `nodeid`、`path`、`rootpath`、可变 items 和 deselected hook。此分支只做文件存在／覆盖／唯一性检查和路径映射；这里不需要真实 fixture 或 test-item 执行。四份保存的原插件选择日志逐项等于真实 collector 节点按配置所得选集：group3 `415→453`，group5 `496→458`；只有 cancellation13＋work_agents25＝38节点移动。结合真实完整 collector，这是充分的纯映射检查。它不证明 fixture 执行、deselection 对其他执行插件的交互或新组成本；当前代码也未改这些接口，没有实证理由再重复六组收集或增加测试。
5. 沿实际 fixture 导入查看两份测试及 `test_training_submission.prepared/service`、`test_training.experiments`、`test_training_runtime.installation`、`test_registrations.installation/registration`、`test_task_creation.creation_project`。prepared／service／submitted／experiments／registration／creation_project／work_graph／work_creation 均 function scope；状态、service record、repo、runtime 由 tmp_path 构造。两类 installation 为 module scope，并由请求模块的 tmp_path_factory 创建；不会要求被导入模块的测试同时执行。显式 fixture 导入闭包保持，service／work_creation 保留 Linux 约束及原 optional-SDK 检查；monkeypatch 的恢复义务保持。两份测试没有直接互相依赖，也没有观察到要求与 submission 正文同进程执行的状态。静态证据支持整文件移动，不能升级为全部组合无耦合的运行证明。
6. 实际 workflow 仍生成六 Linux job，各20分钟，Windows Python3.12 group all、30分钟。runner 的 all 不传 `--ci-group`；plugin 的 group=None 在读取 Linux 配置前返回。因此 Windows all 的选择行为在配置层保持；本次 Linux collector 不是 Windows 执行。

历史预算判断只消费原分析的明确证据范围：59b／833 是不同准确候选的官方整个 job 时间，旧 b653 JUnit 是不同环境的逐文件成本。它们支持从较长组向较短组移动既有工作这一方向，不能将333.339秒从远端 group5直接扣除或加到group3。本审查没有访问这些其他缓存、重算历史远端数据或新增网络请求，不冒称独立验证了历史原件。

## 剩余验收

本基线不含活动 M2/r3 新测量 case；最终冻结后应另核实际联合候选的节点／归属及必要安装验收，不继承本次2269节点证明。随后准确发布候选自己的官方 head／event／attempt、六 Linux 原20分钟与 Windows 原要求仍须闭合，读取其自己的 phase／JUnit；本片没有本机新组合正文、性能测量或自己的远端CI结果。若实际组合出现 fixture／生命周期故障，再按原接缝处理。本报告没有要求为推测增加测试或放宽预算。
