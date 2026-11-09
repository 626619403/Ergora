# AC4.3c.1：工作 Agent 合同独立设计评审

日期：2026-11-09。评审者：Codex `/root/work_agent_contract_review`，fresh context；另由 fresh-context `spec` 与 `standards` 评审者分别检查两轴。输入只有原始要求、固定基线、完整 tracked/new 差异、相关所有者路径及实际验证位置，没有继承实施会话或指定结论。使用 AIHERO 索引中的 code-review、codebase-design 与 maintainable-project-delivery / independent-review 规则。

## 固定范围

基线与评审时 HEAD 均为 `0fd881e4f21d2814eaf7ce0db47a7fd3c28c4144`，分支为 `refactor/architecture-foundations`。本片是未提交的纯设计/计划差异，因此审查的是相对该基线的 working-tree 差异及新增文件，而非空的 baseline…HEAD 差异。

完整五文件为 [PLAN](../PLAN.md)、[AC 总计划](../plans/2026-11-08-agent-composition.md)、[工作 Agent 合同](../plans/2026-11-09-work-agent-contract.md)、[本片交付记录](2026-11-09-work-agent-contract.md)、[前片运行交付记账](2026-11-09-review-dag-runtime.md)。独立重建 tracked/new diff，逐份核 SHA256、当前 HEAD、分支及完整清单，均与交接一致：

- scope SHA256：`9f40962142f18e2ca7c8cccd117c221c3be93c4fb913281386f50329331ee14e`。
- diff SHA256：`2335f8180cf8cc80117600310768e1ba41dc1df4747ae133244e7a956e091042`。
- 合同 SHA256：`8dcac2c022ee89601643509c6114d09eb5740d7bd07313f61460b03764ace652`。

同片新增明确平台段后，五文件 scope SHA256 为 `daef001a6eee521137b60a01cc206188de0ff85f3d6acb245afcd9f3640c8517`，diff SHA256 为 `e650eeca86dc520dad33619f29ff7d791f77525b90f09ae51f529933894efc0e`，合同 SHA256 为 `e61fcf1e4780544ee9318230883a38f715442b8d40d931ca00d86e011da51c8e`。逐字节比较确认仅合同增加 Linux/WSL2 运行范围段，其余四文件保持；主评审者与两位分轴评审者均已复核该增量，无新增 finding。

没有生产代码、schema、模式、队列、依赖或 CI 变更。本报告及随后仅更新审查/交付状态的记账属于同片，不递归审查，也不冒称已在上述五文件 scope 中。被 ignore 的本地探针仅辅助复核，不能充当公共运行能力。

## Spec

**设计门禁通过，0 项实证 finding；严重度不适用。** 本合同没有声称任意职能拓扑或可写模式已经实现；inventory/planner 保留原绑定，工作分配与 review 的新增范围明确。

合同第 56–62 行的一对一映射、工作依赖传递关系相等、完整 unit 写范围和祖先限额，能接到原 `DevelopmentWorkflow.units/context/stage`；原每 job checkout、依赖 commit 合并、路径 gate、确定性检查及 commit 仍由 Executor 拥有。没有另行运行模板 work 图或新增账本。

“完整材料与实际写调用”保留旧只读调用拒绝，将新 workspace 调用放在原 stage/准入/owner 批准链内，要求完整祖先材料及依赖原件、超预算拒绝、真实能力声明与明确的 current-container 选择。没有借 MCP 名称或静态 manifest 提供写权限，也没有将 Git 最终范围检查称为过程隔离。

“work→review只运行原六阶段”与“失败、取消与恢复”保留 integrate/verify 后审查、强制最终 candidate/plan/verify、原工作 commit 祖先关系、作者/session 来源及原 ID 对账；work 原件不经 review-opinion parser 冒充意见。“显式选择与旧版本”和纵切片表禁止提前发布无完整消费者的 v5，C2 必要时与 C3 合并。没有可证实的合同矛盾、范围扩张或缺失要求。

本轴结论限于设计及现有接点，不证明未来 adapter、调度或恢复已经运行。

## Standards

**本片设计范围通过，0 项实证标准 finding；严重度不适用。** 仓内未发现 CONTRIBUTING/CODING_STANDARDS；硬规则来自 AGENTS、当前 PLAN 与当前架构，codebase-design 与 smell 清单作为判断性启发。

合同的所有者表与真实调用一致：原 units/context/stage 调度，原 Executor/monitor/claim/ledger 负责副作用；版本化 queue/request-root/活动/Workflow 可沿现有 `WorkflowInput` 局部注册选择，SDK-free 读取不应导入装饰器。新后端能力仍归 `AgentBackend` Interface / Adapter，没有在调度器按厂商分派或提出通用插件层。

新工作调用正确识别 `agent_runs._admit_input()` 当前拒绝 write/shell/network，以及 `run_input()` 使用独立 cwd 的现状；不能把原只读叶子调用当正式 writer。原工作原件认证留在其真实所有者，端口共享算法只有在实际共用后提取，Locality 合理；没有无真实消费者的新生产抽象。

文档没有新增镜像测试、CI 作业、缓存或持久 running 表。C2–C5 的结构与性能审查出口清楚；目前没有足以要求性能改造、删除测试或新增检查框架的实证。实际成本、嵌套限额及写后崩溃窗口仍需后片测量。

## 现有所有者与验收边界

|关注项|独立源码核查与后片责任|
|---|---|
|原六阶段与批准|原 `dev_platform/workflow.py` 的 `run/approval/units/context/stage` 依次执行 inventory、plan、owner 批准、work、integrate、verify、review；新实现需延伸已有版本继承层。|
|单写所有者|原 `agent_platform/executor.py` 的 `claim/prepare/execute` 核原 context、审批、checkout、依赖合并、unit paths、检查及 commit；`reference_executor` 当前仍让非 verify/组合 review 走该实现。|
|完整输入|`workflow_definitions` 的结构材料与权限链、`reference_executor._composition_request` 的候选材料是已有接点；原非组合 `model()` 仍截断依赖到 60000 字符，新路径明确不能沿用。|
|后端与任务 MCP|`stage_driver`、`agent_runs`、`agent_backends` 已有调用 Interface；当前组合模式均只读。固定任务 MCP 资源与外部 MCP 能力不同，新模式不能从名称推导外部 server 支持。|
|平台|`task_mcp.check_available()` 显式拒绝非 Linux，固定资源读取使用 `O_NOFOLLOW` / `dir_fd`；原 Executor 使用 `fcntl.flock`，Sandbox 依赖 Linux 容器机制。第一版新写模式限定 Linux/WSL2 与事实相符；不把 Windows 包 CI 或本次源码核查当新写路径、WSL2 旅程已验收。|
|版本与来源|`tasks`、`reference_task_creation`、`task_envelopes`、`reference_inputs`、`reference_workflows` 保有冻结选择与原身份；`reference_task_submission/evidence/reconciliation` 保有 attempt、memo/run 归属及原 history 对账。|
|C2–C5|C2 取得真实 CLI/工具/Skill/MCP 与拒绝证据；C3 同片接通完整 v5 分配与原写消费者；C4 扩展真实跨阶段端口及恢复场景；C5 完成安装包、283 身份、CLI/Supervisor/Temporal/evidence/handoff、history、自身模板与新独立审查。合同的“完整消费者前不发布”约束对所有节点有效，不能把 C4 尚缺的必需恢复能力推迟到一个已宣布可运行的 C3 候选之后。|

最后一项是合同已有发布约束的适用说明，不是发现已存在的实现缺陷。若真实实现发现 C3 不能形成完整可运行纵切片，应按合同末段调整合片及依赖；本设计没有授权提前注册半接通格式。

## 已执行检查与限制

独立复核完整五文件及来源身份，重跑 **5 份 Markdown / 74 个本地链接与锚点 / 82 条现有 CLI parser**，全部通过；tracked 与新增文档分别进行 diff 空白检查，均通过。读取原调用/创建/提交/证据/恢复链及前片端口合同，未修改生产文件。两个 fresh-context 分轴评审者均报告 0 项实证 finding。

平台段复核并加入本报告后，再核 **6 份 Markdown / 79 个本地链接与锚点 / 82 条现有 CLI parser**，全部通过；完整 tracked/new 文档空白检查通过。平台段之外原五文件内容保持，完整公开差异另增加本报告这一个审查记账文件。

额外读取安装 CLI 的留存 help：Codex/Claude 均 exit 0。Claude help 中 restricted 的工具例外、bare 的配置范围及 disable-slash-commands 说明支持后续必须验证具体组合；help 只证明语法资料存在，不能证明可写调用、实际 Skill/MCP 装载、权限强制或推理可用。

没有运行模型、服务、应用测试、安装、提交、推送或新 CI；没有将前片 CI42584734023 用作新 workspace/v5 功能证据。本片没有必须处置的开放 finding。后续真实 CLI 能力、完整材料交付、祖先限额、独立分支推进、取消/unknown、写后崩溃恢复及精确候选交付，仍按 C2–C5 取得各自证据；设计通过不替代这些验收。

两轴计数：Spec 0，Standards 0；本片设计阻塞为 0。普通文档提交、适用路径过滤检查及精确 HTTPS 远端身份仍由主代理按实际结果记录。

## 精确文档交付终核

2026-11-09 同片接续核验普通提交 **`11a00061c0573f3d24e0402671d02acc1d1e9107`**，唯一父为 `0fd881e4f21d2814eaf7ce0db47a7fd3c28c4144`，实际变更恰为 **7 份 Markdown**。提交前最终 scope JSON / diff SHA256 为 `bfe6889e1e1b8e1d6c8b6c70867d820a03dee6e81e742603a9d8063313c8a945` / `502d9523f2b967010168c58f0e965facb9fab7f8a8266336ec55d1b994116271`；七个 Git blob 与逐文件记录全部匹配。对象 diff SHA256 为 `1834eae609812a933771785c1b35c8146b5414a6ac4c489d71ca5b65ba4503e5`，各文件差异段与提交前固定 diff 逐字节相同，仅排列顺序不同。

合同的已审正文及 Linux/WSL2 平台段保持；相对平台复核稿只有开头状态与末尾评审/交付链接更新。提交内合同 SHA256 为 `4279b5dec4e4dd53b03c543feba8e557a5e4556339641b4042db930a5ad48e24`，本报告原批准稿为 `bc99830f4ff79521e17de703a96fe3de32a9d66ea3c05124c666dde1ba24400c`。新增前片 runtime review 内容只记录 `0fd881e` 的对象、自己的 CI 与明确 HTTPS 终结，没有增加 C1 行为或借其 CI 证明本设计已运行。

独立从固定提交读取七份文档及链接目标，并从该 Git 对象导出私有源码快照、显式通过 PYTHONPATH 加载精确 parser，得到 **7 份 Markdown / 98 个本地链接与锚点 / 82 条现有 CLI parser 全部通过**；对象 `git diff --check` 通过。没有使用后续 C2 的工作树文档或源码替代本次对象。作者已单列旧开发安装缺少当前命令导致的首次 parser 失败；修正验证入口后使用源码 parser 通过，不是生产源码或应用测试失败。

固定提交的唯一 CI 工作流 `.github/workflows/portability.yml` 与父提交相同，SHA256 为 `81c168fdb140f44ccfdca497003e452355c9164a6ed6f8dfb8fa31729a1943ca`。现有 push 的 `paths-ignore: ["docs/**.md", "README.md", "AGENTS.md"]` 覆盖本次全部七个路径，因此本次文档 push 适用原路径过滤；没有人为增加或触发应用 CI，也没有将父片 CI42584734023 当成本片新能力验收。

独立明确 HTTPS 读取于 **2026-11-09 08:45:21.420359→08:45:22.908502 UTC** 完成：移除继承的全部 GIT 环境项，禁用系统/全局 Git 配置并阻止仓库配置发现，关闭 credential helper/askpass 与 HTTP 重定向；有效配置只有命令行项，无 URL insteadOf/pushInsteadOf。命令为 `/usr/bin/git -c credential.helper= -c core.askpass= -c http.followRedirects=false ls-remote --exit-code https://github.com/626619403/Ergora.git refs/heads/refactor/architecture-foundations`。结果 **exit 0，stderr 0 字节**，stdout 精确为完整 `11a00061c0573f3d24e0402671d02acc1d1e9107`、TAB、目标分支及换行，共 86 字节，SHA256 为 `8da1ad158e28cf49fb33f9bfd31f5d90362bf5f16ffb4ee7df966afdf83621c2`。

本片 **Spec / Standards 设计门禁、七个精确提交对象、适用 CI 路径过滤和明确 HTTPS 远端身份均通过，剩余 C1 交付阻塞为 0**。此段是 `11a0006` 交付后的终核记账，没有声称追加正文已存在于该提交；C2–C5 运行责任保持。未运行模型、服务、应用测试、安装或 Git 发布，未修改生产或其它文档。原对象、静态和远端核验原件保存在本片独立检查目录的 `delivery-11a-*` 文件中。
