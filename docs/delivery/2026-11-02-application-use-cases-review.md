# R4 独立需求与可维护性审查

日期：2026-11-02。Reviewer：Codex `application_use_cases_review`，fresh-context 独立代理，未继承实现对话。项目及文档归属为 Ergora / `docs/`。按仓库 AGENTS 和 `maintainable-project-delivery` 的 independent-review brief 审查；先读原始要求、差异及真实调用者，再读作者[交付记录](2026-11-02-application-use-cases.md)。

## 结论

- **需求符合性：通过。** R4 的用例所有权、依赖环、兼容和拒绝语义符合原始验收；DeepSeek DS1–DS7 已列入计划并保持待实施。最终精确提交的 Windows/Ubuntu CI 条件已独立核对满足，R4 可按本轮范围收口；真实未验维度保留在下文。
- **可维护性：通过。** 在下述范围内无 findings，无阻断性源码或设计问题。三个新增模块持有真实职责及生产调用者；未增加纯转发服务、泛用基类、调度器或第二条事实写入路径。

## 审查身份与范围

原始验收：[详细计划 R4](../plans/2026-11-01-all-in-one.md#r4-应用用例与依赖环)、[A1 第 6 节](../architecture/2026-11-01-audit.md#6-可执行的保留合并与删除清单)、[ADR 0001](../architecture/decisions/0001-refactoring-foundations.md)，以及用户持续推进、逐步更新文档和登记 DeepSeek 参考项的要求。

- 基线/初审时 HEAD：`9633962c29240319c54d07a3942cffe0ccd77ce3`；分支 `refactor/architecture-foundations`。完成源码审查后，作者将相同 17 文件提交为 `f9a9b743be1b5bde352d212b75c47358d5d73e9a`；独立核对其提交范围和当前工作区，未增加生产变化。审查报告尚未纳入该提交。
- 原始完整差异 `.ergora/checks/r4/review-diff.patch`，SHA-256 `8027ed91bb3744895627c1eca9a0fe47b99bb0fc45a31bbc26a77ad28f89eb61`；文件身份 `.ergora/checks/r4/review-files.json`，含 13 个 tracked 和 4 个 untracked 文件。
- 实际读到的 17 文件如下；本报告为额外的审查产物，不计入原实现差异。

|范围|文件|
|---|---|
|说明与计划|`README.md`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/delivery/2026-11-02-application-use-cases.md`|
|生产代码|`src/ergora/backups.py`、`cli.py`、`evaluation.py`、`optimization.py`、`projects.py`、`skills.py`、`tools.py`、`web.py`，新增 `agent_runs.py`、`bindings.py`、`skill_assets.py`|
|合同保护|`tests/test_compatibility_baseline.py`、`tests/test_skills_evaluation.py`|

源码、测试及 README 起初均匹配原身份。审查期间只另改了 `bindings.py` 文件末尾一个空白行，最终 SHA-256 为 `4b465b91117e194710abda0e50df7fb2ab6f4905f09774635a99770293d1bbe6`，其校验函数 AST 与基线一致。其余源码、测试及 README 仍匹配原清单。另读并核对了下列初次源码审查收束时的文档状态；变化为完成验证的登记与下一动作修正。其后 CI 收口状态登记不属于此身份快照：

|文档|初次源码审查核对 SHA-256|
|---|---|
|`docs/PLAN.md`|`8aa3117b19c5b90bd148543e4032ce994ab1b9f6393b5a3b68bffaaa2aa4a94a`|
|`docs/plans/2026-11-01-all-in-one.md`|`a62a7c46baf178d7933c7bc890cb58493fdfb5b5f00753090098875c276b3b73`|
|`docs/delivery/2026-11-02-application-use-cases.md`|`7db45a1bd85185ebbb331177f8a31ef2fc5fa69932ac4a87a43edd2293ee45bf`|

最终非 editable wheel：`b58be7546fb3af84886e1654631c1a55972cde51bfee0c7c07c639b8adbee83d`，身份清单 `.ergora/checks/r4/package-identity-final.json`。独立逐字节核对其 324 个包文件与当前源码、wheel 及两套既有安装全部相同。

## 所有权与必要性

|所有者 / 函数|真实生产调用与判断|
|---|---|
|`agent_runs.run_agent/runs/output`|CLI 和 Web 两个入口都直接调用；实现持有上下文选择、模板约束、绑定/修订快照、执行、持久运行记录及输出读取。`tools` 只为旧 API 直接别名。该迁移没有只包住旧函数。|
|`skill_assets.get/versions/import_bundle`|`get` 被 Agent、评价、搜索、采用、CLI/Web 使用；`versions` 被 Agent、CLI/Web 使用；`import_bundle` 被 CLI/Web 和 GEPA 搜索使用。资产层不导入评价/采用。|
|`skill_assets.digest_tree/metadata/export`|`digest_tree` 用于资产完整性及 backups 核对；`metadata` 是导入内凝聚的格式解析；`export` 当前直接生产调用为 CLI，且是既有公共资产 API。后两项保留在资产所有者合理，无需制造额外消费者或拆成新抽象。|
|`skill_assets.rollback/move_head`|回退由 CLI/Web 使用；`move_head` 由采用用例及同模块回退使用。活动头和事件在同一 SQLite 事务中修改，revision/expected digest 检查留在资产边界。|
|`skills.adopt`|CLI/Web 直接共用比较、资格拒绝、候选读取、原子采用的完整用例（`skills.py:20`）。原文件已退出资产实现职责；evaluation 只依赖 skill_assets，原职责环消除。不需要再增一层 application 转发。|
|`bindings.validate_binding`|`projects.bind`、`tools.doctor`、`agent_runs.run_agent` 三个生产模块共用。Agent/kernel 校验仍委托原所有者，其余层复用 schema 及原 ReMe 规则。放入只持静态描述的 components 会引入执行依赖；留在 tools 则让新运行用例依赖其兼容 facade。当前位置有具体职责理由。|

另追踪了 `agents`、`components`、`kernel`、`state` 及现有 Skill/Agent/Web/Windows/兼容测试。evaluation、optimization、backups、projects 和 agent_runs 可在冷进程中导入而不载入旧 skills/tools facade。没有新增依赖或改动冻结 reference、持久结构、摘要规范和六阶段。

迁移的控制流没有新增断言、fallback 或异常分支。保留的必要边界包括：资产导入的格式/文件树/复制稳定性；`get` 的项目范围和内容身份；比较的同一冻结评价集、全量正确性、收益及 holdout；活动头事务的 revision/expected digest 和操作理由；Agent 的角色、输入/预算、活动 Skill、模板角色约束，以及失败记录和有界输出。它们都有外部输入、持久资产变动或并发更新的可达场景，未发现本切片新引入的重复防御。

旧入口的仓库消费者主要是兼容、Skill/Agent、Web、schema、Windows 和备份测试；生产入口已迁到新所有者，`skills.adopt` 继续作为用例入口。外部 Python 调用者无法从仓库穷尽，因此本轮不删除公共入口；交付记录要求未来明确 API 版本、迁移公告并再次核对调用者后单独退出，适合当前兼容承诺。别名与新实现保持同一函数对象，不形成双写。

## 需求与证据核对

- 导入 → 固定评价 → 比较 → 采用/回退保持原调用语义。`evaluation.compare` 先核对套件及资产；`skills.adopt` 继续要求 eligible；`skill_assets.move_head`（`:134`）在事务内核对活动头，未放宽可信评分。
- 候选改写/缺失由 `skill_assets.get`（`:62`）拒绝；不同评价集由 `evaluation.compare`（`:170`）拒绝；旧 revision 由资产头事务拒绝。缺失 Skill 在创建运行和调用 evaluator 前失败，六项独立定向测试包含这些路径及原闭环。
- Agent 的 Skill digest、记忆召回、binding、project_revision、prompt SHA 仍进入原运行文档；回退改变后续运行上下文，旧运行保持原快照。真实 CLI 原始输出能对应这一结果。
- [L1 执行清单](../plans/2026-11-01-all-in-one.md#l1-deepseek-agent-管理工具调研用户追加)与研究第 6 节一致：DS1→F1/F2，DS2→F3/F5，DS3→F4，DS4→F6/F7，DS5→F8，DS6→F10，DS7→D3；优先级、采用方式和反例可验收，均保持待实施。未将 DSH 接入、隔离能力或原型收益写成已完成，也未改 R4–R8 顺序。

## 实际独立检查及边界

本 reviewer 实际执行：

1. 原始 17 文件身份及当前增量核对；独立 AST 比较 8 个资产函数、3 个运行函数和通用绑定校验，共 **12 PASS**，只标准化 `skills → skill_assets`、`_move_head → move_head`。末尾空白修正后再次核对 bindings AST。
2. 初轮及最终 wheel 的 SHA、源码/压缩包/安装字节核对；最终 **324 文件 × 两套安装 PASS**。这是文件身份检查，不等同重跑整套运行验收。
3. 源码定向 pytest **6 passed in 2.74s**：`test_legacy_python_entry_points_share_the_actual_owners`、`test_asset_and_invocation_consumers_import_without_compatibility_facades`、`test_candidate_evaluation_adoption_and_rollback`、`test_holdout_regression_partial_evidence_and_mutation_are_rejected`、`test_missing_selected_asset_is_rejected_before_agent_or_evaluator_runs`、`test_adoption_rejects_evidence_from_a_different_suite`。使用 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider --basetemp /tmp/ergora-r4-independent-review` 加上述节点；只调用确定性本地命令，无模型。
4. 逐项核对 `.ergora/checks/r4/base-cli-journey.json` 与脚本：21 次调用为 20 次成功及 1 次预期旧 revision 拒绝；采用、Skill/recall 内容、回退、历史运行不变及 reference PASS 与输出一致。**未独立重跑这 21 次旅程。**
5. 当前四份变更 Markdown 的 **105 个本地文件链接目标存在**（不验证锚点）；tracked `git diff --check` 通过，另确认新增 bindings 的末尾空白修正。

读取并核对的作者运行证据：源码 Skill 44 passed/1 skip、Agent 69 passed/6 skips；初轮 wheel `3e6e96069aaa888002ae0c9435de85a80c99e4f90d09c08067d89b8260fec959` 的完整 Linux **206 passed、18 skipped、36 subtests passed**，及上述 21 次基础 CLI 旅程；最终 wheel 的 **35 passed** 边界检查及 optional 缺席/旧数据再读。原始日志分别位于 `.ergora/checks/r4/{skill-regression.log,agent-regression.log,wheel-regression.log,boundary-regression-final.log,base-final-check.log}`。完整回归和旅程保留初轮包身份；交付记录已区分最终仅空白修正后包的实际检查，未借用旧包宣称最终完整运行验收。

18 项完整 Linux 跳过为 11 项 Windows-only、6 项未选择的 Forge/mini SDK 检查、1 项未选择的隔离 Temporal；既有 Starlette warning 未冒充回归失败。未独立运行完整 Linux、Windows、模型/GPU、浏览器、Temporal 服务或 DSH；未安装、提交、推送或外部写入，除本报告外未修改仓库文件。

## 最终 CI 复核与收口

2026-11-02 03:05:54 UTC，同一 reviewer 仅复核本切片的最终身份及 CI 条件，未扩大实现范围。`git diff --name-only f9a9b743be1b5bde352d212b75c47358d5d73e9a -- src tests README.md .github` 无差异；HEAD 仍为该完整提交，工作区除本报告外仅有作者的交付状态文档更新。

本次独立解析保存的官方 Actions HTML，核对其完整提交链接/检查日志路径、run/job URL、可见终态与文件 SHA-256；没有使用 API、登录或凭据。`ci-final-web.json` 记录官方页获取时间为 `2026-11-02T03:03:19.843512+00:00`，job 页身份与原始文件一致；未采用早期 `ci-actions.html` / `ci-web-run.json` 的 in_progress 状态。

|官方页 / 原始证据|独立核对结果|原页 SHA-256|
|---|---|---|
|[run 41380351919](https://github.com/626619403/Ergora/actions/runs/41380351919) / `.ergora/checks/r4/ci-run.html`|push 事件、`refactor/architecture-foundations`、完整 head `f9a9b743be1b5bde352d212b75c47358d5d73e9a`，Status **Success**，2 jobs completed|`6133f43a1dcbd9175d702068edff37e67b66035046305878e6f14cb521ca9c28`|
|[Windows job 125069579809](https://github.com/626619403/Ergora/actions/runs/41380351919/job/125069579809) / `.ergora/checks/r4/ci-job-125069579809.html`|`native (windows-latest, 3.12)`，**succeeded**，3m 12s；检查路径含相同完整 head|`8faae89d9f120ef75fd2eb8a4bc9583a3636525d3c78993b97c40320699ad721`|
|[Ubuntu job 125069579994](https://github.com/626619403/Ergora/actions/runs/41380351919/job/125069579994) / `.ergora/checks/r4/ci-job-125069579994.html`|`native (ubuntu-latest, 3.11)`，**succeeded**，54s；检查路径含相同完整 head|`4e7809bf8fb277b275d4b766ed47411f5df75adb23ccf8c7ac27763a806e6f36`|

上述证据满足本报告原先保留的精确提交两 OS CI 条件，无新增 findings，R4 范围内无剩余验收阻断。此处核对公开运行/job 摘要，未读取逐项测试日志，不据此补造 Windows 测试数量、跳过明细或模型效果；CI 成功也不改变初轮/最终本地 wheel 的身份与实际检查区别。前文未验模型/GPU、浏览器、隔离 Temporal、可选 SDK 和 DSH 等范围继续保留。

若后续源码改变，应核对增量与受影响检查。本报告的无 findings 仅覆盖所列源码、文档、调用者及证据范围。
