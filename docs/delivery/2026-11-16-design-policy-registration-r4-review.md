# WA5-S1 r4 独立两轴审查与 F1 复核

2026-11-16。审查者：fresh-context agent `/root/design_s1_r4_independent_review`。独立阅读原始要求、完整候选差异、实际 producer／caller 和原始证据；没有继承作者、自身模板或前轮 reviewer 的 verdict。

**需求符合性：approve；结构维护性：approve。本轮开放 findings：0。** [前轮兼容审查](2026-11-16-design-policy-registration-v1-compatibility-review.md)的 F1／P2 在本次准确候选上关闭。结论只覆盖 S1 首次登记、持久 policy／State6、恢复及拒绝执行；不认证后继设计关卡或生产部署。

## 固定输入与完整范围

|输入|独立核对结果|
|---|---|
|产品树|只读 `.ergora/worktrees/design-policy-registration-fixed-r4`；baseline `c540939d3b3f38f3851b0de965c9cd0f969eea77`；detached HEAD `b28cd316b63bb788c502a026f1ec971d5572242a`。开始与结束均 clean，无未跟踪产品文件。主 checkout 的其他在途文档／后继合入不改变本审查身份。|
|完整 diff|14 文件；`package-native-resolution-r4/source.patch` 与实际 `git diff --binary <baseline> HEAD` 字节相同，SHA256 `5a109196321ed79df8b78e5ff26f0a4feb365141afe3645fdd04c7a650f0db81`。同源 `--full-index --binary` 的 SHA256 为 `2d99ea35b839bd2a0fee2f0574f1cee0edfc9d712a3072094787d389e7db155c`；两种 index-header 格式不混同。`git diff --check` 通过。|
|完整输入|`package-native-resolution-r4/frozen-inputs.json`，2,072 项，文件 SHA256 `81d01f4e105887a929c4040644d49feecd0e0706e1565f55658077dbefd7148a`；逐项重核候选 bytes、SHA、执行位，差异 0。`product-inputs.json` 的 670 源包输入包括原打包排除的 `src/ergora/AGENTS.md`，实际 runtime 为 669 项。|
|生产变更 6 文件|完整阅读 `data/schemas/project-registration-v2.json`、`reference_executor.py`、`registrations.py`、`state.py`、`task_design.py`、`tasks.py` 的全部差异、新 schema 与相关实现。|
|测试变更 8 文件|完整阅读 `fixtures/reference_acceptance.py`、`test_budget_jobs.py`、`test_composition_executor.py`、`test_registrations.py`、`test_state_backups.py`、`test_state_migrations.py`、`test_task_budget.py`、`test_task_creation.py` 的全部差异与相关原 fixture。|
|权威要求|[原始要求](../plans/2026-11-15-workflow-evidence-and-human-gates.md)、[D1–D4](2026-11-16-workflow-design-decisions.md)、[设计合同](../plans/2026-11-16-design-knowledge-gates.md)、[登记／journal 拆片](../plans/2026-11-16-design-gates-registration-and-journal.md)。只审 S1，不把 F／J／G、人类 assurance 或可执行 input12 纳入已实现能力。|
|相邻 owner|原 native `projects.create_task`、`core.project_for/read/write/slug`、`executor.Executor/claim/execute`；原 portable `compile_task/validate_compiled`；`reference.registration_io/_registration_main`、`reference_job_lifecycle.DirectJob/BudgetedJob`、`reference_inputs` 工厂与 request roots；原 Activities／adapter／poll、task creation／preparation、State 迁移与 backup 边界；`pyproject.toml` 和既有 CI 分组。|
|合作与质量规则|根／src／tests AGENTS、PLAN 和本片 delivery、[组件协议](../architecture/component-change-protocols.md)；`maintainable-project-delivery` 及 independent-review；`ergora-codebase-quality` 的 repository-style、module-design、test-seams。没有引入其他框架的风格规则。|

下文证据路径均相对 `.ergora/checks/design-policy-registration/`，原失败／旧安装原件保留。未把 80cb39c 的 13 项、r2 的 119 项或其他候选 CI 改写为 b28cd31 的运行结果。

## F1 已关闭：普通 native 解析失败回到原回执 owner

候选 `reference_executor.py:35` 的 `_admit_project` 现在只从原同任务 `project.json`／`binding.json` 识别 preclaim 所需的登记身份：project name 与 binding project ID 相同、binding 的完整 tracker 与已校验 spec 相同、native tracker 与其 kind／project 相同。随后核原 marker／control home，并从 State 读取 policy；registration2 或携带设计 policy 的记录保持拒绝。缺失、不可读或关系错误的固定身份仍 fail closed，不扫描其他项目补身份。

原 mutable `project_for` 留在 constructor 的原位置。它失败时仍由 `_execute` 绑定原 job／context、生成 `agent-admission-error`，再由 DirectJob／adapter 发布正式 FAILED，原 poll 取得终态。这里没有吞掉 native 查找错误、另造异常回执、移动 claim／budget owner 或把 mutable 配置当作冻结 selection 的新前提。外层 `process` 和直接 constructor 两处 gate 分别保护 BudgetedJob 的提前 claim 与直接调用，具有不同实际入口义务。

独立核对 `native-resolution-fix-r4/green-original-installed-probe/` 的原 argv、raw 与 `result.json`：同一原 `-I -B` probe，**2.455 秒**；实际 executor 来自新 SDK 的 site-packages，SHA256 `b6ca6c2b96a144d0cfd8785762f650bd01c430a5c5d0ed8388648dfa5f52184a`。合法旧 job submit 后仅删除 mutable native project config，得到 FAILED＋`agent-admission-error`，poll 同终态、receipt 存在；claim／body 各 1，prepare／model／commands 全 0，原固定 project 保持，原进程 wait 后 absent。原 probe 与 `reviewer-native-resolution-r1/probe_fixture.py` 字节相同，SHA256 `1c1c19b8c1a082c6ac804398218602777f4d41990de49e7600eb77b67acb06fc`。

本 reviewer 还在主控明确授权的 `reviewer-r4-identity-edge-r1/` 内运行一次独立最小安装 probe，检查“固定项目 A 与稍后 mutable resolution 的 B 不同”是否可能绕过 gate。沿真实 v1 register(A) → 原 create_task(A) → Activities.submit → 删除 A 的 mutable project config → 同 tracker 的真实首次 register(B, v2) → 原 process／DirectJob／constructor／claim。没有改 spec、compiled、binding 或业务返回值；只在首个 prepare 叶设停止，避免实际业务工作。

实际 **3.357 秒**、同一 site-packages executor SHA：B 的登记确为 v2 且 `execution_supported:false`；但原 constructor 的 `core.write(task/project.json, B)` 因 A 的不可变原件已存在而拒绝，尚未到 constructor 的业务 claim／prepare。随后 `_execute` 沿原拒绝回执路径 claim 一次，正式 FAILED／poll 可见；body 1、prepare／model／commands 全 0，task project 仍为 A，无 B frozen selection，compiled／binding／spec SHA 不变。12 个采样自有进程身份终核全 absent。argv、raw、实际模块 SHA、输入修改说明和过程身份均保留。

因此该疑点被原不可变发布合同和真实安装反例否定，**不是新 finding**。这里的 claim 是原失败回执 claim，不能误称 B 获得业务授权；也不能据此要求 preclaim 再建 mutable resolver。合法 A 的原件与当前 B 分歧，应继续由原 constructor／FAILED owner 处理。

## 全片需求与结构判断

|方面|审查结论|
|---|---|
|policy 与持久身份|显式输入 v2／嵌套 registration2 保留版本判别。完整 profile／policy 与 canonical SHA 进入原 definition、marker digest、intent／result；status 读回原对象、有效最低项、unsupported 与 `human_channel_unavailable`。owner／assurance 是要求，没有被提升为已认证事实。最低 Q／K 并集、跨类别同 ID 冲突、task types 和配置容量由 registration owner 核。|
|首次资格与零增量拒绝|已有 registration 的升级／替换／降级（包括空 v1）在 `_prepare` 拒绝。首次 v2 拒已有任一原生四投影；publication 锁内再次核 State 与原四投影，之后才记录 intent／reservation。原四文件格式、不可变冲突与同操作恢复保持。完整 intent 先核自身 UTF-8 写入大小，避免发布不可由原 recovery reader 读回的记录。|
|出生／执行拒绝|普通 `_definition` 与预算 `_budget_project` 均在创建／准备 intent 和授权预算前消费 State policy；没有由 payload 自报 scope／small-fix 放行。managed executor 的 process／直接 constructor 在原业务 claim 前拒绝 v2；BudgetedJob 原早 claim 接缝得到独立保护。没有新增可执行 v12、definition8、Workflow、queue 或假 adapter。|
|v1 兼容|原 frozen selection 的消费者未被当前 repo／项目存在性重新约束；缺 State 项目仍回原失败或冻结分支。status／`_finish` 新输入重验仅用于 registration2，不把今日 tracker schema 施加给合法旧 v1 history；`published_project` 原有严格完整来源校验保持。foreign-home marker 拒绝是明确的 authority 边界，不冒充人类认证。|
|State6／恢复|沿 v5 模式只替换全部原领域表的 writer fences，不建表或重写历史 JSON；原事务、DB backup 与旧连接 fencing 保持。migration／backup 测试覆盖 v5 中断、rollback 和已开旧 writer。control-home inventory 与外部 config／runtime 的恢复责任明确分列，没有跨根部署回退主张。|
|owner／复用|schema 与 version／eligibility／policy union 留在 registration；共享拒执行规则位于既有纯 `task_design`，由 tasks 与 executor 两个生产模块消费，无新 SDK／jsonschema native 依赖。私有 `_admit_project` 隐藏两入口必要的同一身份义务；`_intent` 隐藏原写入／读取容量合同。没有通用 resolver、registry、policy service、第二批准或停止状态机。|
|测试价值与原合同|新增测试沿真实注册发布／恢复、预算授权、claim／receipt／poll 和 migration seams，配置采用非默认有效值；没有按每字段堆重复矩阵、新 CI job 或缩短原 fixture 时限。283 参考原件、原 lock、六阶段与 candidate／完整 evidence 绑定没有产品差异。|

## 实际验证与剩余边界

|证据层|本轮核对及限度|
|---|---|
|准确包身份|独立逐项重核新 wheel、core 与 SDK 各 **669** runtime 文件 SHA／执行位，差异 0；wheel SHA256 `9736406796a6f2272cffdef1a878198a978c6d0bc5a4a1d0f80acd8cbd865040`。读取实际包检查、283 reference／依赖结果均 exit0／PASS；core 无 SDK，SDK 为 1.34.0。本 reviewer 没有安装或修改环境。|
|受影响源码|作者 `native-resolution-fix-r4/source-affected/` 的原 argv／输入、stdout、JUnit／result：**17 passed／89.72 秒**，runner 90.634 秒；明确通过 PYTHONPATH 选作者源码，并非安装结果。该记录与 root 冻结身份分别保留。|
|准确新安装|独立核 `package-native-resolution-r4/installed-affected-r1.command.json`、选择、stdout／stderr／JUnit：绝对 SDK Python `-I -B`，cwd 为复制 test-inputs，清除 PYTHONPATH；五入口展开 **17 passed／92.33 秒**，JUnit 92.316 秒、0 failure／error／skip，runner 93.710 秒。607 个记录的自有进程身份全为 absent。没有重跑或转授旧 13／119 项。|
|独立行为复核|原 F1 安装 probe 的不变输入／实际 FAILED／poll 已核；本 reviewer 的 A→B 最小安装 probe 实际运行且否定疑点，原件见上。受控 prepare 停止叶不证明业务正向；这次也没有实际 model、business command 或 service 调用。|
|自身结构模板|主控提供的 `self-review-r4-r2-codex/summary.json` 与输入身份已核：实际 Codex 78.706 秒、supplied-text approve；stdin 511,335B／SHA256 `26065d9f815d23a9612beb2027a59645248d9cadd17a3175610b779b7d6400cf`，result SHA256 `ce2497a5872a15ceee137b7112d8239247050f4814d3a97396690302e0a6db85`。首轮 diff-header 检查未启动记录保留；该模板不是本独立 verdict，也不认证运行。|

源码审查、当前安装的定向运行与上述确定性 probe 可以关闭 S1／F1 的本轮审查门。真实 Temporal／旧服务迁移窗口、standalone stack 的停用隔离、可信人类通道、完整设计执行、人类正向旅程、训练／GPU 质量、跨根部署回退均未由本轮认证。S1 仍须保持所有设计执行关闭；后继 F／J／G、旧 creation 跨登记迁移及部署各按其原验收合同推进。普通合入／发布和联合候选自己的安装／CI 由主控另行记录，不从本报告推出。

除授权的独立 probe 证据目录与本报告外没有写入；没有产品修改、昂贵套件、安装、网络、模型、真实服务、commit 或 push。PLAN／delivery 的状态收尾由主控统一更新。
