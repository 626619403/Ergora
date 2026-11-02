# F1.1 有效绑定与运行快照独立审查

日期：2026-11-02。审查者：fresh-context 独立 reviewer（`project_configuration_review`）；未继承实现对话。按根 `AGENTS.md` 及 `maintainable-project-delivery/references/independent-review.md` 审查原始 F1 要求、F1.1 切分、实际源码与原始证据。仅写本报告；未修改生产代码或测试，未安装、提交、推送或重跑昂贵回归。

**最新复审裁决：F1.1 需求符合性通过、可维护性通过；首轮 R1/R2 均已关闭，检查范围内无未解决 findings。** 精确候选 Ubuntu/Windows CI 与远端身份已完成独立核对，F1.1 验收闭合。下文保留首轮发现、复审身份及历史待验状态，最后一节记录提交后的实际核查；完整 F1 仍未完成。

## 首轮裁决

- **需求符合性：需修正。** 来源、逐层校验、旧角色继承、固定支持层默认及主 Agent/正式任务绑定快照实现基本符合 F1.1；下面两项使页面一致性和调用配置身份尚不完整。
- **可维护性：需修正。** 既有 `components` / `projects` 所有权、无新模块/依赖/表的取舍合适；统一解析已被多个真实生产消费者复用。仍有绕过解析的页面消费者，以及一个重新读取可变项目的上下文调用路径。
- 两项均阻断本轮 F1.1 审查通过。F1.2 单一注册/单向投影、F1.3 旧注册导入没有实现，本报告不裁决完整 F1 完成。Windows 精确候选 CI 仍待提交后核对。

## 输入与身份

基线/HEAD：`267cc776772c96d68870b55b726333ce0d175810`；分支 `refactor/architecture-foundations`，未提交实现。首次检查独立重算下列原始 manifest 的 **28 个文件 SHA256，全部一致**：

- `.ergora/checks/f1-configuration/review-context.json`，SHA256 `95c57c222f8f7f32e5caf3223cc9297985ac8d1d1d1ec9dbbe7f7d411fa98f81`。
- tracked 差异 `.ergora/checks/f1-configuration/review.diff`，SHA256 `fa81e85ce7bf65bacc4e4e4b4c16b758c05c9d111edbcf2a74c5d76dee1e1609`。

28 个输入包括：`README.md`；`docs/AGENT_BACKENDS.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/delivery/2026-11-02-project-configuration.md`、`docs/delivery/2026-11-02-low-code-editors-review.md`、`docs/research/2026-11-02-low-code-editors.md`；`src/ergora/` 下 `agent_runs.py`、`agents.py`、`cli.py`、`components.py`、`kernel.py`、`memory.py`、`optimization.py`、`projects.py`、`reference_executor.py`、`research.py`、`scheduling.py`、`tools.py`、`web.py`、`data/console/state.js`、`data/console/tools.js`、`data/console/workflow.js`；`tests/fixtures/reference_acceptance.py`、`tests/test_project_configuration.py`、`tests/test_reference_executor.py`。LC1 来源研究及其已完成的独立审查不重复裁决。

另读必要相邻消费者/边界：`bindings.py`、`contracts.py`、`state.py`、`reference.py`、`data/components.json`、前端 `app.js`、`skills.js`、`research.js` 和兼容性/冻结身份测试。原始 `skills.js` / `research.js` 未列入本次变更 manifest，但与所验 wheel 清单身份一致；它们是 F1.1 页面复用审查的实际邻接消费者。

## 发现

### R1 — P2：缺支持层的旧项目仍会使技能页和资料页渲染失败

位置：原始 `src/ergora/data/console/skills.js:282`、`:283`，`src/ergora/data/console/research.js:147`；可达入口 `src/ergora/data/console/app.js:115`、`:119`。

旧项目只保存 `bindings.implementer` 时，新的有效配置正确给出 `optimizer=manual`、`scheduler=manual`；原项目文档按合同保持不回写。但技能页仍使用 `data.project.bindings.optimizer.tool`，资料页仍使用 `data.project.bindings.scheduler.tool`。点击对应导航会读取 `undefined.tool`，导致整页无法渲染。当前 `State.project` 不补齐字段，因此 dashboard 返回有效视图并不能避免这条路径。

影响：F1.1 明确支持的旧项目在工具页显示正常，在技能/资料页不可用，页面没有共用有效绑定。原浏览器日志仅验证工具页和工作流页，未覆盖这两个入口。

最小修正：两页导入并调用现有 `bindingFor(data, layer)`，不向原项目文档补默认；在缺五个支持层的旧项目上验证全部六页，确认显示 manual 且无 pageerror。

作者已收到发现并开始修正；原 wheel 的真实 Chromium 复现另记于 `.ergora/checks/f1-configuration/browser-support-repro.log`。该修正及新包证据待后续独立复核，不能继承首轮包结论。

### R2 — P2：并发修订可使调用保存的 memory 绑定与实际 recall 后端不同

位置：`src/ergora/agent_runs.py:20`、`:21`、`:36`，`src/ergora/memory.py:150`、`:158`。

`run_agent` 先读取项目 r1 并构造所有层的 `configuration`，之后带 `recall` 的路径调用 `memory.search`；后者重新读取当前项目。若在两次读取之间保存 r2 的记忆绑定，本次实际检索使用 r2，运行归档却仍保存 r1 的 memory 绑定。`search` 的远端路径还调用再次读取项目的 `sync`，也应沿同一绑定完成本次检索。

独立纯内存探针将第一次项目读取设为 r1/SQLite，第二次设为 r2/ReMe；用 FakeState/FakeDB 和内存 stub 拦截外部调用，不写文件或访问网络。实际结果：`snapshot_memory={"tool":"sqlite"}`，`actual_memory_calls=[{"binding":{"tool":"reme","endpoint":"https://memory.invalid"},"operation":"search"}]`，调用终态 `succeeded`，归档 INSERT/UPDATE 均发生。这不是外部工具内部默认值变化，而是项目层绑定身份不一致。

影响：保存的全层有效视图不能准确解释本次调用采用的记忆组件；并发编辑可能改变调用上下文的后端。主 Agent 角色绑定仍使用 r1，问题限于 recall 支持路径。

最小修正：让 `run_agent` 的 recall 路径复用初次项目读取/已解析的 memory 绑定，并传递至该次 `search` 所需 `sync`；保留普通独立 memory 入口的既有选择方式。增加回归，在初次配置读取后保存新的 memory 修订，核对实际 backend/request 和运行归档仍对应同一选择。

## 核查与证据边界

- `components.resolve_binding` 有多个真实生产文件消费者：Agent 入口、memory、optimization、research、scheduling、kernel 及有效视图。`projects.effective_configuration` 被 CLI、Web、doctor、独立调用和正式执行桥使用。固定历史默认值与新项目推荐默认分开具有兼容性语义；深复制保护原文档及历史视图。没有为复用数量增加新模块或框架。
- 逐层校验复用既有 `bindings.validate_binding`，将无效继承记录为可诊断结果；选中角色仍由调用边界拒绝。不相关角色无效不会阻止独立 Agent 调用。工具可用性和认证继续与结构/能力校验区分；无效 reviewer 的兼容工具占位修正路径与保存 revision 检查相符。
- CLI `project config`、configuration API、dashboard 和工具页共用有效视图。dashboard 对项目/有效配置/doctor 使用同次项目读取。R1 是仍遗漏的浏览器消费者。
- 独立调用在 `agents.invoke` 前持久化视图，并由其中的角色绑定执行；正式桥首次选择保存同份视图，后续阶段读取已有选择，不重建当前项目。旧正式任务缺 `configuration` 时仍走旧绑定；旧 agent run 的列表/输出也不要求新增字段。所读测试包括中途修订后的六阶段选择稳定性及缺新字段的恢复。
- 独立重算实际 wheel SHA256 为 `bd49b976ce310bcc577542abdc034ac0b0dce853323d1b4f3c2278a0357c4f17`，并从归档逐项核对 **335 文件**，与 `package-identity.json` 全部一致。检查时源码仅新增作者对 `skills.js` / `research.js` 的修正与原 wheel 不同；原 28 文件仍匹配原 manifest。两安装身份为所读记录，未重新安装或重复全量运行。
- 独立运行只读 `reference.verify()`：**PASS，283 文件**；冻结参考内容未改。
- 已读取 `final-regression-command.json` 与原始 `final-wheel-regression.log`：记录为 **220 passed、18 skipped、36 subtests passed，177.80s**，1 个既有 Starlette warning。跳过范围包括 Windows、未显式选择的固定 Forge/mini SDK 和 Temporal 服务，未计为通过。已读 final/base CLI 和 browser 日志的相关覆盖声明；原工具/工作流浏览器通过不能代替 R1 的六页覆盖或 R2 的并发绑定验证。
- 未复跑昂贵测试、完整浏览器、实际模型/GPU/外部服务，也未验证 Windows。没有发现需要改变原六阶段、证据身份或 F1.2/F1.3 边界的理由。修正后应提供新的精确 manifest、包身份、受影响检查及独立复审。

## 修正后独立复审

2026-11-02，同一独立 reviewer 复审两项修正、相邻调用及新增回归，未继承作者实现对话。基线/HEAD 仍为 `267cc776772c96d68870b55b726333ce0d175810`，分支不变，实现未提交。

### 身份

- 新输入 `.ergora/checks/f1-configuration/review-fixed-context.json` 的 SHA256 独立重算为 `d5edf8cbbf0f0407bb33cefe51da93e97e70f15a8b288f8d6befdeda8477e3c7`，**30 文件全部匹配**。较原 28 输入新增 `src/ergora/data/console/skills.js` 和 `research.js`；另有变化的输入仅为 `agent_runs.py`、`memory.py`、`tests/test_project_configuration.py` 及 PLAN/详细计划/本切片交付记录。报告自身不计入该 manifest。
- 新 tracked 差异 `review-fixed.diff` 的 SHA256 为 `4583281bb638efabf56b880809a033d389c9e7b847c95d11054880c209cdcd96`。原 `review-context.json` / `review.diff` SHA256 再次核对不变，首轮证据未覆盖。
- 实际最终 wheel SHA256 独立重算为 `3e76b1902b83871a95219d73675360b77e3d081cc727739284cf088bfcc26e73`。按现 `package-identity.json` 逐项读取 **335 文件**，源码、wheel 内容、开发安装、基础安装均无不一致。首轮 wheel 的清单已保留在 `pre-review-fix-package-identity.json`，其摘要仍为首轮 `bd49b976…`。

### 发现关闭与回归充分性

**R1 关闭。** `skills.js:283`、`:284` 与 `research.js:148` 均消费既有 `bindingFor(data, layer)`；独立搜索自有前端，无 `project.bindings` 直接读取。原 wheel 的 `browser-support-repro.log` 保留了两个真实 `undefined.tool` 错误。已读新包的 `review-fix-browser-all-pages.log`：同一缺五支持层旧项目在 1440px/390px 各进入六页，明确检查 optimizer/manual、scheduler/manual，12 次页宽均无溢出，pageErrors 为空。此证据直接覆盖首轮遗漏入口。

**R2 关闭。** `agent_runs.py:36` 将首次读取的项目传入 `memory.search`；`memory.py:105`、`:147` 的 keyword-only `project` 输入沿用该文档，`:158` 将同份文档继续传给 sync。原 CLI/Web 调用仍保留既有参数和自行读取方式。扩展位于既有记忆所有者，有独立调用和 search→sync 的实际消费者，没有新增包装层或无关校验。

新增 `tests/test_project_configuration.py:110` 与 `:133` 使用真实 State/SQLite 和真实 command 调用，在 search 前 SQLite→ReMe、sync 前旧→新 ReMe endpoint 两个时点插入修订；仅远端请求替换为 fixture，分别核对禁止新后端访问、实际 write/search 的旧端点、记忆结果及跨 State 恢复的运行快照。回归验证外部可观察合同，没有仅断言参数转发。

独立重做首轮无文件写入的内存探针：修正版仅读取一次项目，快照 memory=sqlite，取回原 SQLite observation，远端调用为空，状态 succeeded。另独立重跑只读 `reference.verify()`：**PASS、283 文件**；`git diff --check` 通过。

### 最新证据与裁决

已读实际定向日志 `review-fix-targeted.log`：**9 passed，2.82s**；最终完整命令 `review-fix-regression-command.json` 与原始 `review-fix-wheel-regression.log`：**222 passed、18 skipped、36 subtests passed，204.11s**，1 个既有 Starlette warning。18 跳过的 Windows/固定 SDK/Temporal 范围与首轮一致，没有从跳过推导通过。`review-fix-modules.log` 记录 12 模块全部解析/链接。

已读修正包两套基础 CLI 记录：**21+7 次**，包括预期的两次不可变导出冲突及一次旧 revision 拒绝；真实 command succeeded，运行 revision 与保存视图 revision 一致。已读新 `review-fix-browser-configuration.log`，12 层 UI/API、继承/兼容默认、无效继承显式修正至 r2 和刷新持久均通过；新 `review-fix-browser-workflow.log` 对三模板分别核对 4/4/3 角色继承、两开发图、训练 manual kernel 及 390px 无溢出/pageerror。

- **需求符合性：通过（F1.1 检查范围）。** 两项首轮缺口已有针对修正和实际证据；来源/校验、旧状态、主调用/recall 的绑定身份和正式任务恢复未见剩余问题。
- **可维护性：通过。** 统一解析的实际消费者已补全，内存接口的项目输入拥有明确的一次调用一致性用途；没有扩大为新注册/迁移/执行框架。
- **剩余阻断 findings：无。** 精确候选 Ubuntu/Windows CI、提交/推送尚未发生，应在交付关闭前另行核对。本复审没有重跑昂贵全量/浏览器，没有验证真实模型、GPU、外部服务或竞品；LC1 研究未重复审查。F1.2/F1.3 未实施，完整 F1 继续保持未完成。

## 精确 CI 与远端最终核对

2026-11-02，独立 reviewer 完成提交后的状态收尾核查；以上首轮和修正后身份不变。

- 实现/测试提交 [`d914ea724e87495fb5efcd92e12f50b5931fc42c`](https://github.com/626619403/Ergora/commit/d914ea724e87495fb5efcd92e12f50b5931fc42c) 的直接父提交为审查基线 `267cc776772c96d68870b55b726333ce0d175810`。独立读取 origin URL 为 `https://github.com/626619403/Ergora.git`，实际 `git ls-remote origin refs/heads/refactor/architecture-foundations` 返回该完整候选 SHA，与 `remote-candidate.json` 一致。
- 从候选提交直接读取并计算 **335 个应用文件**和复审 manifest 中 **21 个源码/测试文件**的 SHA256，分别与已验最终包清单、复审输入全部一致。核对时工作区仅有 PLAN、详细计划、F1 交付记录、current 架构页四份状态文档变化；没有新的生产/测试变更。
- 读取候选自身 `.github/workflows/portability.yml`，确认 Ubuntu 3.11 / Windows 3.12 矩阵、wheel 构建/安装、冻结参考身份、Native application regression 的实际命令，以及仅 Windows 执行的 PowerShell 5.1 安装/升级步骤。没有把两平台的适用套件范围混为一谈。
- 已独立重算 `ci-html-status.json` 列出的四份原始证据字节数与 SHA256，全部匹配：selection `8ff4e9e6…`、run HTML `ad40e585…`、Ubuntu job HTML `f26aeee7…`、Windows job HTML `0d684568…`。selection 将完整候选映射至 run `41440299977`；它保存于运行中，最终结论另由最新 run/job HTML 核对。`verify-ci-html.py` 最后会写入汇总，reviewer 未执行该写操作，而是独立进行只读解析，未改原始证据或汇总。
- 另实时读取三个官方页面，均 HTTP 200：[run 41440299977](https://github.com/626619403/Ergora/actions/runs/41440299977)、[Ubuntu job 125260189208](https://github.com/626619403/Ergora/actions/runs/41440299977/job/125260189208)、[Windows job 125260188816](https://github.com/626619403/Ergora/actions/runs/41440299977/job/125260188816)。run 的完整 commit 链接匹配候选，Status 为 **Success**；两 job 的 selectedJobId、平台/Python 名称及所需 check-step 日志 URL 中的完整 SHA/job ID 均一致。
- Ubuntu 的 Build and install wheel、Packaged reference identity、Native application regression 均为已完成 **success**；Windows 的这三步及 Windows PowerShell 5.1 installer and upgrade 均为已完成 **success**。Ubuntu 跳过 Windows 专用安装步骤符合 workflow 条件，未计为 Windows 安装通过。官方页面证据没有使用历史绿色运行替代本候选。

**最终裁决：F1.1 需求符合性、可维护性及本切片所需交付证据均通过，首轮两项关闭，无未解决 findings。** 可在计划和交付记录关闭 F1.1。此收尾未重复全量测试/浏览器或 LC1 来源审查；CI 核对使用官方 HTML 与候选 workflow，没有重试已限流 API，也没有重新下载逐项测试日志。它不增加真实模型、GPU、外部服务或竞品效果结论。F1.2 单一注册/单向投影、F1.3 旧注册显式导入仍未实施，完整 F1 不标完成。
