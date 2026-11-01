# S11 / A0：all-in-one 计划独立审查

日期：2026-11-01。Reviewer：独立 fresh-context 文档审查 agent。收到原始用户要求、本切片范围、精确源码身份、完整变更文件列表和实际验证说明后自行读取文档、必要源码及 Git；未继承实施对话。按 `review-pr` 分阶段检查，并参照项目 `AGENTS.md` 和 maintainable-project-delivery 的独立审查要求。

## Findings 与结论

**本次检查范围内无已确认的阻塞或非阻塞 findings。**

- **需求符合性：通过，仅限 A0 计划交付。** 计划涵盖 all-in-one 差距、主线整理、模块/调用/数据归属盘点、函数级后续审计、重复与抽象判断、逐层变更影响、低代码范围、库与 skill 选择，以及可验收重构和功能优先级。用户最后要求“先整理一份 plan 文件”，本次没有以此提前执行合并或生产重构。
- **可维护性：通过，作为后续实施依据。** 重构以真实消费者和变化点为依据，保留领域状态权威、摘要规则、可信检查及平台必要差异；没有强制数量配额、角色继承树、万能 repository 或竞争调度器。最终接口和删除名单仍由 A1/A2 的证据决定，允许缩减无依据的重构项。

上述结论不代表 M1、A1/A2、R/F/G/D/X/PUB 节点已完成，也不代替具体实现、迁移、运行效果或发行验收。A0 的提交、推送和远端 SHA 核对仍由实施者按交付记录收口。

## 审查身份与文件范围

源码 baseline 与审查时 HEAD 均为 `44c1c94d8c34ac3d6179eba91dfcd194ea9b005a`，分支 `feat/windows-support`。审查对象为未提交的四份文档：

|文件|审查时内容 SHA-256|
|---|---|
|[docs/PLAN.md](../PLAN.md)|`016ef59f38cfb9d0f096466272af62d8014d12f58895b39432fb7379d99e332d`|
|[详细计划](../plans/2026-11-01-all-in-one.md)|`e006320f1fbfc4446b862891229c524ecaa7d7c5ea23a6ba3f9c4d88daa9e84e`|
|[架构基线](../architecture/2026-11-01-baseline.md)|`be8cc8639888304710fd78f877652cb8cd02422395f74337019f6ea55e0138b4`|
|[A0 交付记录](2026-11-01-all-in-one-plan.md)|`079ff007a3db1f6791f78c0989f783eecc52084317f74295ba840e8e69e6e843`|

已纳入审查期间作者的两项文案修订：复用证据不作为消费者/实现的数量配额；工具选型表不混入当前机器的可用性状态。审查者唯一写入文件为本报告；未修改源码、计划、依赖、数据、分支或外部状态。

## 需求与证据核对

|核对项|证据与判断|
|---|---|
|市场差距与优先级|详细计划第 1/2 节区分已有基础、待补用户结果及代表性来源；没有声称穷尽市场或已经优于其他产品。前置整理、P0 正式开发闭环、P1 扩展与实验、P2/P3 高级能力分开；完整执行首版明确为 Linux/WSL2。|
|主线合入|详细计划 M1 区分创建/推送 `main`、CI 与 GitHub 默认分支设置；要求重核 refs、保留历史、正常处理新增提交和独立回退。本次只读远端结果仍无 main/master，HEAD 为研究分支；研究/evolution SHA 均为 Windows HEAD 祖先。|
|模块与流程事实|架构基线列出自有模块、冻结参考边界及五条流程，并说明图省略部分边；没有把独立 Agent 成功当成正式验收，也没有把草稿 DAG 当成正式任务入口。函数级完整审计属于 A1，未写为本轮已完成。|
|重复、抽象及迁移|基线第 5 节区分已确认同步点、疑似遗留分支及必要差异；A1/A2 和 R1–R8 有证据、兼容样例、验收和迁移/回退条件。目录是职责草案，协议、摘要与证据不得为拆分方便而改写。|
|配置/格式/低代码|基线第 4 节与详细计划第 4 节分开当前格式和目标规则；项目修订、DB 迁移、Skill 目录、命令协议、冻结合同、布局及凭据引用各有归属。配置组合和真正的新 adapter/协议语义分开验收。|
|持久交接与范围|PLAN 是恢复入口，节点状态明细只在详细计划维护；每节点要求独立记录与审查。历史 CI、模型/GPU和外部服务未验收项没有转写为本轮结果。公开文档均在本项目 docs 下。|

以下关键事实已对照实际函数，而非仅采信文档描述：

- `tools.run_agent` 读取项目修订、Skill digest 和 recall 内容，随后调用 `agents.invoke`；后者通过 `processes.run` 执行。`tools.output` 有读取上限，Web 直接同步调用这些用例。与基线 3.1 的范围相符。
- `reference_executor.Executor.__init__` 在新任务首次接入时冻结四个角色绑定并校验同名项目与同一 Git 根，已有快照继续使用；正式 `DevelopmentWorkflow.run` 按 inventory、plan、精确批准、work DAG、integrate、verify、review 推进。与基线 3.2 相符。
- `skills.adopt` 延迟调用 `evaluation.compare`，后者调用 `skills.get` 校验资产；基线所述职责环确实存在。Skill 目录 digest 包含资源内容和可执行位，不能机械并入其他 JSON hash 规则。
- `ResearchActivities.observe` 调用 `research.run`；Temporal 历史和本地抓取/取消责任分开。`training.prepare`、训练执行器及 perfctl 保留精确绑定、证据 gate 和 owner 决策；MLflow 用于观测。基线没有把 Forge 的原生完成状态当作项目采用，人工转交也以虚线说明。
- `State` 使用 SQLite 并在初始化时创建基础表，其他域仍有 lazy DDL；`projects.bind` 使用事务和 expected revision；`memory` 以本地记录为 canonical、ReMe 为检索投影；Web 的 Pydantic DTO 位于可选 Web 依赖内。格式/所有权建议有相应事实基础。

## 独立检查与限制

已执行并通过：

- `git status`、最近提交、HEAD、tracked diff 和四份新旧文档内容核对；`git diff --check` 无错误；生产路径 `src/`、`scripts/`、`tests/`、`pyproject.toml`、`.github/` 的 tracked diff 为空。
- Python 只读 AST/行数盘点：自有 23 个 Python 文件、3,319 行，app.js 2,108 行，与基线一致。
- 四份文档 62 个本地文件/章节链接均可解析；围栏配对、8 个 Mermaid 块、尾随空白检查通过。图的主要边另对照源码抽查。
- Python graphlib 检查 32 个节点，未见重复 ID、未知前置或依赖环；节点表与各阶段的主要产出/验收能够对应。
- 独立读取远端 refs，并以 `git merge-base --is-ancestor` 核对两项祖先关系，退出码均为 0；未更新远端或默认分支。
- 定向检查个人绝对路径、临时路径、私钥头和常见 token 形态，无命中；这不构成完整秘密扫描证明。
- 只读获取 OpenHands SDK 当前 pyproject，确认 `1.59.0`、Python `>=3.12`；读取两份所引外部 SKILL 原文和 MIT 许可，确认其临时报告/委派流程与本计划“仅借鉴方法、未完整执行”的表述一致。计划将正式接入前固定版本和合同实测列为后续责任。

本次没有运行生产测试、lint/typecheck、Mermaid renderer、浏览器、模型、GPU、新 Windows 实机或服务连通测试；文档审查不据此产生新的运行支持声明。没有独立重放全部 S0–S10 历史验收，也没有重新穷尽全部外部市场资料。静态 AST/import 检查不能覆盖所有动态 SDK/子进程行为，A1/A2 的函数级及运行证据仍是实施前置。

下一动作：实施者记录本审查结果并收口 A0 提交/推送；下一生产实施节点为 M1。
