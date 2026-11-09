# AC3c.4 联合离线备份与原路径恢复独立审查

日期：2026-11-09。审查者：fresh-context Codex 独立审查代理；没有继承实施对话，未派生审查。固定基线与本地终核 HEAD 均为 `cee213a581895d491c1cd41b5fe79b23bfd09b59`，本片 16 文件尚待普通交付。R2 离线恢复、R4 在线续验、R4/R5 自身真实审查及完整文档 scope 已核原件，不将脚本中的待运行断言当作通过。

## 本地两轴结论

- **需求符合性：通过本片本地范围。** R2 原控制备份/拒绝覆盖/同路径恢复、外部完整树、五 SQLite 逻辑表与 32 Git 状态，加 R4 四原 run/重复 start/history/replay/受保护材料和账本保持及显式 shutdown 已完成。AR-1/AR-2 已关闭；R1–R3 各自失败范围保留，不合并成独立成功旅程。自身模板 R4 request-changes 与 R5 approve 分别留证。
- **可维护性：通过本片范围，无剩余实证 finding。** 产品仍由 `backups` 管控制 home，`services` 管显式进程生命周期，原 submission/runtime/reconciliation/executor 拥有任务身份、恢复和 claim。没有新增生产模块、第二调度器或 ledger，也没有以一次验收程序建立产品备份框架。控制快照保持原小 interface，跨目录保存复用 GNU tar；验收前后重复核对分别保护离线原件、恢复点与 scanner 重开后的事实，未添加镜像产品测试或 CI。

## 审查输入与顺序

先读 `AGENTS.md`、`docs/PLAN.md`、AC 计划、`composition-manifests.md` 原 AC3c.4 出口及架构恢复合同，再读 `src/ergora/backups.py`、`services.py`、`tasks.py`、`reference.py`、`reference_task_submission.py`、`reference_task_runtime.py`、`reference_task_reconciliation.py` 和 executor 扫描所有者，之后才检查本片手册/实施记录。应用 `maintainable-project-delivery` 的 independent-review brief 与 `codebase-design`。

初审变更：tracked `docs/PLAN.md`，新增 `docs/BACKUP_RECOVERY.md`、`docs/delivery/2026-11-09-composition-recovery.md`；本审查报告是唯一获准写入路径。验收原件在忽略的 `.ergora/checks/ac3c4-recovery/`，精确运行/备份路径仅留本地原件，均在持久 home 下。

最终 inspected scope 为 **16 文件，10 Markdown / 6 JSON**：`docs/BACKUP_RECOVERY.md`、`docs/PLAN.md`、`docs/USAGE.md`；`docs/plans/2026-11-01-all-in-one.md`、`2026-11-08-agent-composition.md`；`docs/delivery/2026-11-09-composition-{lifecycle,lifecycle-review,runtime,recovery,recovery-review}.md`；`docs/delivery/evidence/2026-11-09-ac3c4-{recovery,evidence-check,r4-self-review-identity,r4-self-review-result,r5-self-review-identity,r5-self-review-result}.json`。前片 CR4 独立终结追加只做其原提交的记账，不借此替代本片交付核验。最终手册 SHA 为 `8c6ff8bd0ca587a4e18b36a154098b6f085226ea1e8d31a7d81c0998e47b8672`。

原始约束保留：六阶段、candidate/批准、attempt-before-send/memo/unknown、283 冻结文件；同平台原绝对路径、不覆盖原目录、不重写旧信封/ledger、停止服务不释放原 claim。只验 AC3c.4，不扩多成员执行/AC4；原业务 Agent 为确定性协议，真实模型审查另记。

## 发现与证据问题

### AR-1 / P2：在途原 run 不能直接调用 external-status（已关闭）

`docs/BACKUP_RECOVERY.md:9` 要求逐一查看“在途任务”的 `task status` 和 `task external-status`。可达场景是原 run 仍 RUNNING；`reference_task_reconciliation._Inspection.run` 只接受已闭合原 run，并明确拒绝尚未闭合的执行。照手册执行会在正式离线前遇到不能满足的读取条件。

最小修正：先用 `task status` 核原 run；只有原 run 闭合后才用 `external-status` 检查外部证据。尚未闭合或 unknown 的任务保留原记录，按已有取消/对账流程处理；不需要改产品或重跑恢复旅程。

复核：最新手册明确上述顺序与查询失败的事实边界，符合 `_Inspection.run` 所有者；AR-1 关闭。

### AR-2 / P2：自定义控制 home 的重启命令漏选原 home（已关闭）

自身真实结构审查在 R4 手册 `docs/BACKUP_RECOVERY.md:76` 发现：`ergora services start PROJECT ...` 没有 `--home "$CONTROL"`，而备份/恢复显式使用该目录。可达场景是自定义 CONTROL 且 ambient home 不匹配；命令会找不到项目或选择另一个同 ID 注册。独立审查沿 `services._context` 的 State 项目读取与 owner 的 control_directory 核对确认成立。“重复 start”同时需要明确为 task start，服务 start 只返回进程状态。

最新手册在 project show、task status/external-status、services start 和重复 task start 均显式指定原 home，区分 Temporal 先起与其他服务选择，以及服务启动与任务原提交恢复。独立者核最终正文及五种具体 CLI 形式的 parser，并核 R5 真实复审 approve 与最终手册身份，AR-2 关闭。此最小文档修正无需重跑不变的恢复旅程；该项来源于自身模板，独立审查没有把它冒称为首次独立发现。

### E1：R1 的 Linux 链接模式假设（已核处置，非产品缺陷）

R1 在外部提取后、上线前失败。`r1/restore-diff.json` 只有三条 symlink 从 0775 到 0777，目标保持，GNU tar compare 成功；普通文件/目录仍逐项相同。Linux 不以 symlink 模式位授权访问。R2 仅对 symlink 采用目标身份，普通文件/目录仍核模式，并先对照 R1 最初快照、五库逻辑和 32 Git 状态。该调整符合手册明确的 Linux 文件/目录模式及链接目标范围；不能把 R1 未到达的上线阶段计入成功。

### E2：external_confirmed 一概为 true 的探针假设（已由 R4 闭环）

`r2/recovery.py:204` 在 resumed-v2 的 external-status 断言失败。原件显示原 REVIEW_READY、六作业 request matches/receipt SUCCEEDED、unexpected/unresolved 均为空，但原 fence 为 not_recorded。实际 `reference_task_reconciliation.py` 明确 `external_confirmed = fence is not None and not unresolved`；查询不建立 fence、不释放 claim，因此 false 是这个原任务的正确事实。

最小修正是核原 fence 与恢复后状态一致，并保留无意外/未核作业条件；不能为满足探针而创建 fence 或 reconcile。R4 复用未变的 R2 离线原件，先核受保护树/四账本/Git，再完成四 run 查询、同 start、history/replay、scanner 无副作用和显式 shutdown。正常 v2/v1 无 fence 保持 false，拒绝/取消任务原 fence matches 保持 true，四任务均无 unexpected/unresolved jobs；没有增加 fence 或释放 claim。

### E3：离线清单函数遇在线 Supervisor socket（已由 R4 闭环）

R3 已取得四任务的有效 status/start/history/replay 原件，但在上线后的全树遍历遇 `ergora-services/s.sock`，于受保护范围过滤之前拒绝特殊文件。R4 的在线清单只进入 requests/receipts/artifacts/approvals/fences/tasks/workspaces 与 `ergora/task-*`，避开正在变化的服务 socket、数据库和日志；R2 离线全树的特殊文件拒绝没有放宽。R3 原失败、五进程/零 live 观察和首次 observer 日志未创建的小失败分别保留。

## 已独立核对与限制

- R1 初始与 R2 restored 外部清单相同（仅剔除链接模式），共 1,992 项：1,400 普通文件、589 目录、3 symlink；五库逻辑快照与 32 Git 快照均相同。外部目录含 CONFIG/STATE、安装、四业务库及工具入口；原目录保留在各自持久备份中。
- R2 控制备份/verify/restore 同 manifest SHA `912ce5282e4f47d59acaa8e3337193ca6eff17d762778f8e4ea07932fa05512b`，71 文件，schema 1；原存在 home 的 restore exit 2。控制库物理页不要求与原库逐字相同，逻辑数据另核。
- 独立重算 source/wheel/installed 完整集合，369 文件逐字相同；wheel SHA `aaa55f011bbc8ddcdfead0e1d59859695f07f6d7f80ddbdb309d26e37d98e703`，283 冻结参考与 manifest 相同，源码/测试/依赖/CI 对基线无差异。
- 独立重算 R2 外部 tar，11,489,280 字节，SHA `3a52f9276228f4806a9d6fdd6b2df4569e979375654fab2ef0acc88dd278f8de`；直接 compare 保留原目录 exit 0，九个原目录存在。
- R4 在线原件为 44.47 秒。独立解析四 history，161/167/162/161 个原事件前缀及完整首输入 JSON 均保持，v2/v1 队列正确；脚本只在 SDK replay 成功后保存对应 history。原 REVIEW_READY/BLOCKED/CANCEL_UNCONFIRMED/REVIEW_READY、candidate 与原 submission 保持。
- 关停后独立重算 1,145 项受保护清单，与 R2 初始一致；以只读 immutable SQLite（无非空 WAL）核当前控制/leases/a2a/executor 四库 integrity 与全表逻辑均相同，四 claims/三 active/一 released。managed socket 不存在，7233/8233/8765 均关闭；观察器原件保留五个原进程且零 live，采样不证明捕获每个短命进程。
- 另独立逐个读取当前 32 个 Git repo/mirror/worktree 的 HEAD、refs、bare 与完整未提交状态，对 R2 初始全部相同；24 receipt、87 artifact 的路径与 SHA、四原 owner-plan 绑定均无差异。公开恢复 JSON 仅按声明去除依赖目标路径并标记未归档，其他字段与原件一致；公开计数 JSON 与本地原件相同。
- 外部 venv/工具只恢复链接，目标环境留在原路径并另核；本片不证明跨机器重建环境。控制原件中当前无 Agent/Workflow 资产库，任务需靠已封存信封和运行材料恢复，不能将“零资产”当作整个组合定义导入功能的新验收。
- 未自行安装、启动服务、运行模型或昂贵旅程；只读源码与必要原件并写本报告。Windows/Linux 支持边界、远端系统、跨路径、在线多库原子快照、ACL/xattr、模型质量和宿主隔离不由本片证明。

## 自身真实审查原件（R4）

已核实际非 editable Ergora `structure-review` / `architecture-reviewer`、task-MCP、Codex/ChatGPT 回退调用：166.23 秒、应用 status succeeded/exit 0，但审查 decision 为 request-changes（AR-2），两者不能混淆。供应九份完整源码/手册/脚本；模型没有运行恢复旅程或读取未供应原件，报告明确保留该限制。

独立从原生 stdout 重组首轮连续五页 `0→24000→46000→68000→87000→null`，共 107,106 字节，SHA `325bbd3edb738b52ac9fcbc945e7344e1e3126957600134b1e39d28124d17a6c`，与保存 input asset 逐字相同；另有 `0→60000→null` 两页重读。prompt SHA、应用 result SHA、protocol/应用结果 JSON、原生 audit 均吻合，stderr 为空；原定义库在从完整 manifest 准备 input 前移除。R4 request-changes 保留，不能用调用成功冒称审查通过。

R5 复审为 **96.92 秒、approve/exit 0**，run `80e4cb76640c47d8ac73564fbbd64569`；完整 46,348 字节单页 `0→null`，SHA `afc1f979acce4a9b500be59fda45641c0da31fdf9e5e2edffe555a72bfd37ac4`。独立核保存 input asset、prompt/result、原生 audit 和只读 SQLite run 相同，protocol/应用结果 JSON 相同，stderr 为空；四份供应源与最终身份匹配，原定义库仍缺席。公开两轮 identity/result 四 JSON 与原件逐 JSON 相同。R5 只复查更正手册及三个原所有者，不扩大为模型独立执行恢复旅程或未供应依赖的认证；Claude 不可用按原授权回退，不冒称不同模型错误独立。

## 文档与交付出口

最终 16 文件范围与 tracked/untracked 清单相符；十份 Markdown 的本地目标及 20 个锚点独立核无缺失，另读作者 207 链接/79 CLI parser 静态原件，四个新手册 shell block 语法通过。独立额外核五个带原 home 的 project/task/services 具体命令形式 parser 通过。JSON 可解析、公开证据与原件一致，`git diff --check` 通过。静态检查不替代运行验收；报告/计划的后续状态记账不触发递归审查。

本地需求符合性与可维护性均通过，可冻结本片文档范围并普通交付。剩余为本片精确提交、自己的必要 CI 与即时远端身份核对，不能用前片 CR4 的 CI 代替；本报告未预记这些交付动作完成。
