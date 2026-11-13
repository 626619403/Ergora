# 同事试用入口：独立文档评审

日期：2026-11-13。评审者：`/root/colleague_onboarding_review`。使用 fresh context，仅接收原始需求、验收条件、基线及证据路径；未继承实施对话。按本项目 AGENTS 和 maintainable-project-delivery 的独立评审流程进行，只写本报告。

## 范围与身份

需求是把进度、同事试用、模板与剩余工作直接写入顶层 README，并回答计划中的子 Agent 与模板是否全部补完。产品基线为 `2d13c0ee76ddeb960365b6b8e77853801def14d5`，分支为 `refactor/architecture-foundations`。

读取 `.ergora/checks/colleague-onboarding-r1/` 下的 `baseline.json`、`baseline/`、`incoming.diff`、`slice.diff`、`candidate.json` 和 `candidate/`，将开始时已有的五份 B2f 发布状态改动与本片分开。评审本片四文件及同片修正后的 live 内容；未把已有 B2f 记录算作本片产品实现。最终所读身份如下，后续评审结案状态记账不改变产品行为。

|文件|SHA256|
|---|---|
|`README.md`|`1370e724e94c67574ca228e513a086bad1bf1196982d9e5bc215fc284e2b7676`|
|`docs/PLAN.md`|`6602643102d5dd0de37da521b9bd3db1ad8ccb7389307e37dd871a5c18a0aaed`|
|`docs/plans/2026-11-13-specialist-presets.md`|`1d48ce27d7c716e7bc1acf5f6f20880b1a5b9c75fd1729ca695d289a2d8790d7`|
|`docs/delivery/2026-11-13-colleague-onboarding.md`|`7fc3f197aab1693e98583ae30414ee59229e1909b1808c28548392d01dae53c0`|

## 双轴结论

**需求符合：修正后通过，开放 0。** README 给出正确开发分支、可复制的 Linux 控制面安装与 preset 导入命令、Windows／使用／训练手册入口，并把模型认证、项目可信检查、完整 manifest、参考运行栈和 task-mcp 依赖列为正式执行前置。清楚回答“尚未全部补完”，列明 cluster-resiliency、low-precision 与专门 kernel 方向包，以及 Forge 完整嵌套和其他原生系统的剩余边界。

**可维护性：通过，开放 0。** 改动位于既有 README、总计划、专家计划和片交付记录中，没有新增产品抽象、定义库或运行器。README 保留适合初学者的概览，完整 preset ID、版本、运行步骤仍链接既有手册与生产 catalog；方向按组概括，没有复制十五套操作步骤。下方原有安装／参考发行章节的用途与新快速试用入口能够区分。动态 CI 结果留在所属交付记录，README 仅链接 Actions，未形成第二份终态清单。已复核 PLAN“下一可执行项”第 0 条的同片状态更新：A2 第三轮与 B1／B2a–f 的现状、B2g→B2h→B2i 及 B3／C2 后续边界可恢复；前两轮失败仍留在历史记录中。

## Finding 与同片复核

**SP1／P2，已关闭：AgentDefinition 与实例权限归属混淆。** 初稿 [README 第 18 行](../../README.md#当前试用范围)称独立 Agent 可声明“上下文与权限”。实际 [AgentDefinition v1 schema](../../src/ergora/data/schemas/agent-definition-v1.json)第 5–20 行禁止额外字段，只有 roles、specialties、backend、resources 等字段；权限在 WorkflowDefinition 及其 Agent 节点声明，编译器沿项目 grant／祖先上限检查。初学者据此在独立 Agent 中增加 permissions 会被 schema 拒绝，也容易误认权限的维护位置。

最小修正是从 Agent 字段列表去掉权限，并明确工作流为实例声明权限、沿结构父链收窄至项目授权上限。作者已作此修正；复核 live README 第 18 行以及 `workflow_definitions.py` 的 `_within`、`_materials`、`_workflow` 路径后关闭。没有要求或实施 schema、运行行为变更。其余所审范围未发现实质 correctness 或维护性问题。

## 核对与证据范围

- 直接读取生产 `data/presets/presets.json`、全部方向根及其引用链、相关 Agent 定义和 schema：20 项为四个主要入口、保留的训练 v1 加 15 个细方向；所有细方向均为 proposal-leaves，递归引用 design／profile／measurement 三个 2.0.0 专家，叶权限均只读、无 shell／network；总训练 v2 另含 kernel designer 2.0.0。未发布方向不在 catalog。结构祖先资源合并、实例权限与后端职责限制均有既有生产所有者。
- 对照 `scripts/install.sh`、Windows／使用／模板旅程／训练手册以及 kernel 既有原生操作，核查控制面安装、SDK profile、正式运行和可信实验 runner 的区别。README 的显式逐叶调用、完整前驱手动交接、evidence SHA 人工批准及原生流程限制与这些所有者一致。
- 读取本片 `cli-checks.json` 与六条原 stdout／stderr：列出 20 项，治理与重构导入返回 `execution_authorized:false`，重构重复导入保持原身份；serve 检查只有 help，reference verify 为 283 文件 PASS 且未启动 runtime。stderr 均为空。另核实际安装 metadata 的非 editable 身份，以及安装版 catalog 与源码逐字相同。这里复核既有 CLI 原件，没有重跑 CLI 或安装。
- 核治理原旅程、重构第三轮和 B1 交付记录及其公开证据投影：真实 Codex、六阶段、候选复验与原 ID 恢复只属于各自历史任务；B1 是四个只读单叶及手动前驱交接。没有把这些历史模型结果写成本片再次运行通过，也没有把资料包称 GPU 或训练验收。
- 对同片后续 B2f 状态更新，读取原评审的 `ci-independent-terminal-audit-r2.json`：对应同完整产品提交、run 43426570060、Success、8 job／30 必要步骤、issues 为空。这里只核所属独立终核记录与状态文字一致，不替代原 B2f 评审或声称本次访问 Actions 成功。
- 独立重查初稿四文件的 227 个本地文件目标／Markdown 锚点，问题 0；随后 PLAN 第 0 条收口减少两处旧链接，最终 live 四文件 225 个目标及本报告 2 个链接均核准。`bash -n scripts/install.sh` 与 `git diff --check` 均退出 0。最终 tracked 改动仍只有文档，产品源码没有本片差分。

未运行联网全新安装、服务启动、正式任务、模型、GPU、训练、Windows／WSL2 或原生 Forge 内部流程；未重新审计历史任务的全部私有运行原件、云端完整日志或实际收益。未读密钥，未提交、推送或写外部系统。本片没有尚缺的文档验收证据；作者可据本报告将 PLAN 与交付记录中的评审状态收口。
