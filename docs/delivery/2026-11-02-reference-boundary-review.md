# S11 / R6：reference 边界独立审查

日期：2026-11-02。审查者：Codex fresh-context reviewer（`/root/reference_boundary_review`）。新建审查上下文，未继承实现对话；先读原始要求和实际 diff，再核对作者交付记录。项目及文档归属为 Ergora。

## 身份与范围

- 基线：`d685bb9867ef2cdc35d3c5b785dba2bb147dbeac`。
- 实现候选：`277ec1f76e0b304dc30fb82a14e0f95ac9d022d1`，分支 `refactor/architecture-foundations`。
- 完整提交 diff 共7文件：`src/ergora/reference.py`、`src/ergora/web.py`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/architecture/reference-boundary.md`、`docs/delivery/2026-11-02-reference-boundary.md`、`docs/delivery/2026-11-02-runtime-contracts.md`。与 `.ergora/checks/r6/review.diff` 逐字节一致；`review-context.json` 记录提交时无遗漏未跟踪文件。
- 另复核候选后的三份计划/交付状态 diff：只登记本候选推送、最终104链接及两OS CI；两个生产文件仍逐字节等于候选。
- 依据：[原计划 R6](../plans/2026-11-01-all-in-one.md#r6-reference-边界)、[A1 保留/删除清单](../architecture/2026-11-01-audit.md#6-可执行的保留合并与删除清单)、[ADR 0001](../architecture/decisions/0001-refactoring-foundations.md)、项目 AGENTS 与 maintainable-project-delivery 独立审查规则。

## 结论

**需求符合性：通过。可维护性：通过。** 在本次完整 diff、相邻调用及记录证据范围内，无 findings，无阻断性验收缺口。

R6 的收敛范围充分。配置定位、隔离编译、执行加载、绑定快照和 file/ledger 操作在基线已由 `reference.py / reference_executor.py` 持有；原正式查询/命令继续由 agentflow、DevelopmentRuntime/Transport 与原 Workflow 拥有。A1 明确允许保留现成 Protocol、框架 hook 和分发镜像，没有依据要求再造一层逐函数转发。统一项目与正式任务 API 的实际缺口由 F1/F3 承接，边界文档没有将其写成已实现。

## 关键检查与判断

- `reference.py:72–83` 的新 `template_details` 只有 Web 一个生产消费者。其责任是读取冻结模板资源并隐藏目录布局，归属现有 reference 所有者；它实现实际资源访问，并非无语义的透传。已有 `agent_contract` 只提供角色合同，`copy_template` 会写目标目录，均不能替代页面所需的只读输入接口，无需新模板类或存储层。
- `web.py:268–270` 已只传输接口结果。开发模板仍返回 `kind/agents/input`，训练仍返回 `kind/agents/files`；文本 UTF-8、文件排序及生成合同 JSON 的编码保持。未知 kind 的 guard 保留原 `ValueError("Unknown template")`，经原 HTTP 错误处理仍映射为400；它有保持既有外部错误合同的具体用途。
- 检查 CLI、Web、drafts、agent_runs、stage_driver 和全体非冻结应用导入。原 `agent_platform/dev_platform`、`sys.path`、Windows 私有 reader patch 的知识仍在 reference 边界，应用已无 `reference.ROOT` 或私有入口访问。没有第二条六阶段链、额外配置副本或 ledger 状态机。
- 复核 `reference.executor` 的安装身份核对与专用进程入口，及 `reference_executor.Executor.__init__/model/receipt/process`。冻结绑定、已有 receipt 时拒绝切换、可信 integrate/verify、候选 SHA、原回执发布和 ledger 更新未改。导入缓存/原 CONFIG/STATE 的单安装进程约束被准确记录，未被宣称为可供 Web 热切换的多实例服务。
- [边界与退出清单](../architecture/reference-boundary.md) 明确冻结目录仍为生产分发；迁出须有真实消费者，并先比较取消、未知、恢复、精确批准与候选证据。F1/F2/F3/F9、R8 的后续责任及 Windows reader 的移除前提均可追踪；没有把未来迁出或完整模型/GPU能力写成本轮成果。

## 验证证据与限制

本审查没有安装软件、重跑 pytest/SDK、启动服务或调用模型；以下区分独立只读检查与作者执行记录。

独立执行了候选 diff/空白检查、调用/导入搜索、wheel 及安装文件哈希交叉核对。wheel SHA 为 `2e0c239583c232fed1294bf7d9be0a75a6ea987acb5cefc1dd311fc62cdeaf05`，其中两个改动 Python 文件与候选一致；`package-identity.json` 的324条哈希分别与源码、已有开发安装、已有基础安装全部一致。按 manifest 重算283个冻结文件，无缺失、symlink或摘要差异；候选 diff 未触及冻结目录、旧HTML/zip、测试、依赖或CI。五份当前文档104个本地文件链接均存在；102是保留的早期快照。

核对作者原始日志：定向20 passed；非 editable wheel 的 Linux206 passed、18 skipped、36 subtests passed，均有1项既有 Starlette warning。读实际断言而非仅看汇总：现有 Web 测试覆盖三模板/合同及 DAG 拒绝；两模板×command/Codex fixture 经原六阶段，inventory后修改绑定仍沿冻结值执行，校验候选与检查/回执；原 adapter/portable/runtime 测试覆盖精确计划批准拒绝、不可变导出、冻结快照恢复、取消与未知结果语义。恢复证据是这些合同检查，不是重启真实 Temporal 服务的旅程。

核对 `base-journey.py/json`：21次真实CLI记录中19次成功、2次为预期不可变导出拒绝；脚本检查无5种可选包、三模板reader/copy/合同一致、两开发模板旧golden编译及转换/校验/导出往返。没有把同实现之间的比较当作全部兼容证据，旧golden和原合同拒绝检查另有独立期望。

最终复核作者保存的官方 Actions 原始响应 `ci-run.json / ci-jobs.json / ci-status.json`：[Portability 41388048791](https://github.com/626619403/Ergora/actions/runs/41388048791) 为 completed/success，run及两个job的 head 均为完整候选 `277ec1f76e0b304dc30fb82a14e0f95ac9d022d1`。Ubuntu/Python3.11 job `125093151283`、Windows/Python3.12 job `125093151521` 均成功；build/install、packaged identity、native regression成功，Windows PowerShell安装/升级步骤成功。原始响应SHA分别为 `7615fe45a2342e95eb89d22b10273577330403cb694dc32d199592e68ab5420e`、`a5d89b7ecf9b1767fb0e3058de355f2deb340f286a93ef8e7a6cec7231ca817a`，与摘要一致。审查者没有另发网络请求；没有逐项CI日志，故不推导Windows测试数量，也不复用R5历史CI代替本候选。

未验证真实模型/GPU、新浏览器交互、真实Temporal重启/分布式恢复、空白Windows系统或本轮真实Forge/mini SDK效果。Linux的18跳过及这些限制在交付记录有明确归属；本次只移动资源读取，没有执行引擎/默认路径切换，不需要用这些未来或既有独立验收维度制造本轮完成声明。

## 剩余交付

范围内无需源码修正或追加行为验收。作者仍需把本审查结论登记到计划/交付记录，并按原授权提交、推送审查及状态收尾文档；未来 F/R 节点继续遵循已记录的迁出和独立验收条件。
