# S11 / R2 独立审查：结构合同与身份

日期：2026-11-02。Reviewer：Codex 独立 reviewer（`schemas_review`），fresh context；未接收实现对话。先读原 R2 要求、ADR 0001 和完整差异，再读实施说明。遵循仓库 `AGENTS.md`、maintainable-project-delivery 的 independent-review brief 和本计划采用的工程纪律。权限仅为源码/必要轻量只读检查及本报告写入；未改生产/测试、安装、提交或推送。

## 初审身份与结论

- 项目/文档根：Ergora / `docs/`；分支 `refactor/architecture-foundations`。
- 基线：`9808870c7baf298f0d3ac20337daed0e1e561297`。
- 初审实现：`defda32aed4811e7bcf77bab531d5c6f566da0fc`。开始时工作区干净；完整 tracked diff 共 17 文件，无遗漏实现 untracked。
- 需求符合性：**未通过**。发现严格整数与数值范围组合的可达回归（下文 P1）；两 OS CI 也未验收完成。
- 可维护性：**需修复后复审**。共享所有权、实际复用及业务边界合理，但共享 validator 的两个数值类型定义不一致，使库的范围关键词失效。除同一 P1 外，已检查范围无额外可维护性 findings。

完整差异包括：`pyproject.toml`；`src/ergora/agents.py`、`contracts.py`、`tools.py`、`kernel.py`、`evaluation.py`；`src/ergora/data/components.json`、`schemas/evaluation-manifest-v1.json`、`schemas/evaluation-result-v1.json`；`tests/test_schema_contracts.py`、`test_compatibility_baseline.py`、`test_skills_evaluation.py`；`docs/AGENT_BACKENDS.md`、`PLAN.md`、`architecture/contracts-and-identities.md`、`delivery/2026-11-02-schemas.md`、`plans/2026-11-01-all-in-one.md`。另读 CLI/Web、projects、components、reference_executor、processes、mini driver、skills、原固定身份夹具及 CI workflow 的有关调用与合同。

## Findings（按严重度）

### P1：巨大整数绕过原有步数和超时范围

位置：初审版 `src/ergora/contracts.py:19–22`，相关合同为 `data/components.json:314` 和 `data/schemas/evaluation-manifest-v1.json:15`。

`integer` 接受任意 Python `int`，但 `number` 对 `math.isfinite` 转换溢出的整数返回 False。jsonschema 4.24.0 的 `minimum` / `maximum` 实现先检查 `validator.is_type(instance, "number")`，为 False 时直接返回。因此 `10**1000` 和 `-(10**1000)` 同时满足新 `integer` 类型，却跳过上下界。

可达复现：`tools.validate_binding("implementer", {"tool": "mini-swe-agent", "model": "p/m", "step_limit": 10**1000})` 在初审版成功，负值同样成功；基线均拒绝。对完整 `evaluation.register` 以 SQLite `:memory:` 状态和只读现有 evaluator 文件运行，两种巨大 `timeout_seconds` 均成功进入保存的 manifest，基线均 ValueError。1001 位 JSON 整数可解析，Web `BindingPayload.model_validate_json` 原样保留该整数；CLI JSON 和 API 的实际共享业务调用链都可到达，无需 optional SDK、模型或远端服务。

后果：mini 的 1–1000 步约束和 evaluator 的 1–300 秒约束不再成立；无效配置被持久化并传给下游。`processes.run` 将超时直接交给 subprocess / deadline 计算，不能代替注册边界保证，巨大值还可能造成未捕获的数值溢出。

最小修正：使严格整数判定与数值关键词使用的 finite-number 判定保持一致，或确保数值关键词对这些整数仍执行范围判断。当前只有上述两个 integer 字段，均有小范围，不需放宽 number、改变有效语义或引入新 validator 框架。补正负巨大整数的 binding 和完整 register 回归，同时保留正常端点、bool、float、NaN/Infinity 的原结论。

状态：初审已反馈。实施者随后修改了 validator、针对性测试和说明；这些工作区修改不计为本次初审通过，待精确新身份与验证后复审。

## 所有权、被删除规则与复用核查

|原手写规则|初审实现中的负责位置与核查结果|
|---|---|
|Agent 额外字段、model/python 非空白及禁 NUL、sandbox、mini 必需 model/数值、command argv/protocol/capabilities|组件 configuration 及同一 `contracts.validate`；命令角色能力覆盖仍由 agents 负责。除巨大 integer 范围回归，其余对照接受集合保持|
|GEPA proposer argv、Temporal 三个必需非空白字段、ReMe 字符串/额外字段|对应组件 schema；ReMe URL 结构和 token 环境变量名仍由 tools 负责。未启用库的通用 URI format 检查来偷偷加规则|
|kernel manual 无选项、Forge 必需非空白/禁 NUL 字段|组件 schema；工具选择及绝对路径仍由 kernel 负责|
|Agent 必需字段/产物、非空白内容、review decision、拒绝额外字段|实际发给驱动的 `agents.result_schema` 与 `validate_result` 共用；调用者是 tools 的模板调用与 reference_executor 的正式阶段，未制造消费者|
|评价 manifest 顶层/case 字段、argv/files 类型与长度、cases 数量、数值边界|随包 manifest schema；版本、安全/唯一 case ID、三个 split、可信文件与指纹仍由 evaluation 负责。timeout 巨大 integer 是唯一已证接受集合回归|
|evaluator object、有限 score/cost、bool passed、string feedback|随包 result schema；额外字段继续被接受并忽略，原 stdout 仍保存，不改为严格拒绝。预算/候选/可信评价规则仍属 evaluation|

`contracts.validate` 有 agents、tools、kernel、evaluation 四个不同生产文件的真实调用；新 schema 文件是配置接口，不按函数复用数量要求删去。`_is_finite_number` 是库的必要类型回调，OverflowError 分支对应可达外部输入；未引入空壳包装、通用插件层、重试或无依据 fallback。工具选择、跨字段能力、URL/文件/绝对路径和可信门禁继续留在原业务所有者，依赖方向未倒向 Web。CLI/Web 的绑定入口均调 `projects.bind`，评价注册均调 `evaluation.register`；嵌套 dict 未经 Pydantic dump/coercion 重算身份。

文档准确说明 legacy 评价版本实际接受 `1` / `1.0` / `true`，并保留各自原值类型与 digest；未知版本继续由 evaluation 拒绝。目录未知版本检查仍在 components。绑定位于既有 project v1，stage 信封仍是 stage-json-v1，evaluator 响应未新增版本字段；冻结合同/存储/其他领域格式的所有者有明确登记。R3 迁移未混入。

## 实际检查与证据限制

本 reviewer 未重跑 pytest、安装或浏览器旅程。以下是本次独立只读检查，与实施者运行报告分开：

- 读取基线到初审提交的全部 17 文件 diff、原要求/ADR、相关调用者；`git diff --check` 通过，固定身份夹具未改。
- 用 `PYTHONPATH=src .venv-dev/bin/python -B` 从 Git 加载原验证函数，与初审实现做纯内存对照：2484 个绑定样本出现一个巨大正整数 step 接受差异，另定向确认负值；264 个 Agent 结果和 146 个 evaluator 响应样本没有接受集合差异；295 个完整 manifest 注册样本仅出现巨大正/负 timeout 两个接受差异。注册检查只写内存 SQLite，读取已有 fixture 文件，没有写业务数据。数值溢出的旧异常变为 ValueError，未算作接受集合变化。
- 独立检查全部随包组件/评价 schema 和生成的两种 stage schema 有效；验证不注入默认值的实现与回归断言一致。版本 `1` / `1.0` / `true` 的完整注册对照保留类型和旧 digest。
- 独立核对初审 wheel、源码与 `.venv-dev` 安装内容，23 个应用 Python + components / app.js / 两个 schema，共 27 文件逐字节相同。该初审 wheel SHA-256 为 `2c3954fa6fd272794ff41cbbe34dcdd47b2de99dcb03cbbd2d2968d5bac91c62`；修复后须记录新包身份，不能沿用此核对。
- 独立读 wheel METADATA，基础依赖为 PyYAML 与 jsonschema 4.24.0，Web/GEPA/Temporal 仍属 extras；现有基础 venv 实查 fastapi、uvicorn、gepa、temporalio、minisweagent 均缺席，仍能导入核心、读取工具目录并 reference verify。这里未新建 venv，也未重跑会初始化状态的 CLI 命令。
- 独立从固定向量核对评价 manifest SHA `bd59b7200356d1883aa1422cfc148929bbc574dc72f181bd31df9c9cb9547897`，与 reference canonical/adapter SHA `42006e97289eba594ee5e2cac8e1c5323283a66e575ef35c0e7e5d814b83e93b` 各保留原编码、彼此不同。Skill 目录/执行位及两种 compiled/request/profile 的 golden 测试与期望未变；此轮未重跑这些文件系统测试。
- `.venv-dev` 和现有基础 venv 的安装包各自 reference verify：283 文件 PASS，source zip SHA `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，runtime 未启动。
- 核看 `.ergora/checks/r2/regression.log`，内容与实施者报告相符：170 passed、17 skipped、36 subtests passed、1 warning、87.09s；workflow 确有 Ubuntu/Python 3.11 和 Windows/Python 3.12 的非 editable wheel 与相应 regression step。这是已记录运行证据，未由 reviewer 重跑。

实施者报告的源码定向 41 passed、基础 wheel CLI 检查和 Linux 完整回归，不等于两 OS CI。初审后实施者新告知 `defda32` 的 CI run `41334860593` 失败（Windows 研究启动相关四项）；本 reviewer 未独立读取该远端 run，不据未改相关文件推断它已无关或已通过。修复后须记录并核对新提交的两 OS CI、安装与回归结果，再关闭本节点。R1 浏览器通过保留其原范围；R2 未改 JS，不声称重跑浏览器。真实模型/GPU/外部服务及效果均未验收。

## 待补交付

修复并复审 P1，核对最终源码/测试/非 editable wheel 身份与受影响检查；完成当前提交的两 OS CI，记录原失败的处置与新 run 身份，然后按既有授权提交/推送并核对远端。完成前不得将 R2 标为完成。下一业务切片仍为 R3；本报告及后续审查状态记录属于 R2，不另起实现切片。

## 修复复审：d402d1b

精确复审提交：`d402d1b88d273e0cb7e2a2a4bf7f25ef636ba503`；原基线仍为 `9808870c7baf298f0d3ac20337daed0e1e561297`。复审开始时分支不变、工作区干净。已读 `defda32` 到本提交的全部改动文件及相关实现：七文件包括 contracts、schema_contracts 测试、格式说明、PLAN、详细计划、交付记录和本初审报告；本报告及状态登记属于原切片 bookkeeping。

生产修复只在严格 integer 的判定中共用现有 `_is_finite_number`，并说明库的数值关键词先询问 number 的原因；没有新增包装、分派、异常兜底或跨层职责。两个现有 integer 字段（step_limit、timeout_seconds）均有小范围上下界，因此排除溢出整数保持旧有效输入集合。新测试直接保护正负巨大步数的拒绝和完整评价注册边界，没有改 golden 或下游生命周期约束。

**P1 已关闭。** 需求符合性：本次源码/合同复审通过，节点的完整验收仍待新提交的两 OS CI 与交付核对。可维护性：通过；本次复审范围无新增 findings。上文初审结论及旧包/旧运行身份保留为历史证据，不代表最终候选。

本次实际独立只读复核：

- 再从 Git 加载原基线验证函数，对最终源码做 2570 个绑定样本和 295 个完整注册样本对照，接受集合差异均为 0，绑定无意外异常。注册仍仅使用内存 SQLite 和只读已有 evaluator fixture。
- 定向核对 step_limit 的 1/1000、timeout_seconds 的 1/300 可接受；0、上界+1、bool、1.0、正负 `10**1000` 均以 ValueError 拒绝。完整注册的 `1` / `1.0` / `true` 版本继续保留原类型和旧 digest。
- 最终非 editable wheel SHA-256 实查为 `685d3d874c47bd52efed0447f45fb641b24e3f53bda61ad27ccd024219b1d4e6`。27 个生产 Python/JSON/JS 文件在源码、wheel、开发 venv 安装和基础 venv 安装四者间逐字节一致。
- 基础 venv 的 fastapi、uvicorn、gepa、temporalio、minisweagent 五个模块仍实际缺席，核心导入和工具目录可用；两个安装环境分别 reference verify，283 文件 PASS，source zip 身份仍为 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，未启动 runtime。
- 实读 `.ergora/checks/r2/regression-fix.log`：172 passed、17 skipped、36 subtests passed、1 原有 warning、86.00s，与交付记录一致。43 passed / 10.27s 的源码定向结果和四条基础 CLI 再验为实施者记录；本 reviewer 未重跑 pytest、安装、状态初始化 CLI 或浏览器。

本次未读取新远端 CI。`defda32` 的 `41334860593` 失败记录继续保留，不能从这次本地修复/复审推导 Windows 的研究计时问题已解决。`d402d1b` 推送后的 Ubuntu/Windows 新 run、对应 SHA、检查结果及远端交付一致性仍待补齐；在此之前 R2 保持“源码复审通过、CI/交付未完成”。真实模型/GPU/外部服务的原未验证范围不变。

## 两 OS CI 独立核对与最终审查结论

2026-11-01 **18:25:30 UTC**（本地 2026-11-02）直接读取 GitHub 公开 jobs API，两次请求使用 `Cache-Control: no-cache`，响应 Date 均为上述时间；未从旧 run 或 HTML 页面缓存推导。两 job 的 `run_id` 均为 **41336217446**、`run_attempt` 为 1、`head_sha` 均为 **`d402d1b88d273e0cb7e2a2a4bf7f25ef636ba503`**、`head_branch` 均为 `refactor/architecture-foundations`。

|独立读取的 job|最终状态|开始 / 完成（UTC）|
|---|---|---|
|[Windows / Python 3.12，124936492868](https://api.github.com/repos/626619403/Ergora/actions/jobs/124936492868)|completed / success|2026-11-01 18:21:42 / 18:24:31|
|[Ubuntu / Python 3.11，124936493019](https://api.github.com/repos/626619403/Ergora/actions/jobs/124936493019)|completed / success|2026-11-01 18:21:42 / 18:22:50|

两个 job 的 `Build and install wheel`、`Packaged reference identity`、`Native application regression` 步骤逐项均为 completed / success；Windows 的 `Windows PowerShell 5.1 installer and upgrade` 也为 completed / success，Ubuntu 的该 Windows 专用步骤按 workflow 条件为 skipped。

**本次 CI 门禁已关闭。需求符合性通过，可维护性通过；已检范围无未解决阻塞 findings。** P1 的关闭、最终包身份和源码复审仍以上节 `d402d1b` 的实际检查为依据；本节补齐同一精确提交的真实两 OS 证据。`defda32` / run `41334860593` 的 Windows 历史失败原因仍未证实，原计时断言与该失败记录继续保留。

实施者报告 `defda32..d402d1b` 已推送；本 reviewer 实查的 GitHub 两 job 与该源码提交和分支相符。最终计划/交付状态和本审查追加内容的提交、推送及远端一致性仍由实施者按已有授权完成。本 reviewer 仅追加本报告，没有提交或推送。真实模型/GPU/外部服务效果与 R2 浏览器重跑仍不在本次验收范围。
