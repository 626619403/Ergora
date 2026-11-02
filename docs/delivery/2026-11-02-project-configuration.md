# F1：单一项目与有效配置

日期：2026-11-02。分支 `refactor/architecture-foundations`，源码基线 `267cc776772c96d68870b55b726333ce0d175810`；开始时工作区干净且与远端一致。沿已授权计划实现、测试、独立审查和推送，不改实际用户服务。

## 分步与验收

|子节点|范围与验收|实现|验证|独立审查|
|---|---|---|---|---|
|F1.1 有效绑定与运行快照|CLI/API/页面读取同一解析结果，显示项目修订、每层来源和校验状态；旧角色继承和支持层默认不变；独立调用和新正式任务保存快照，在途调用不随项目/默认变化|已实现；初审两项已修正|修正后完整包222项+36子测试/18跳过；两安装/28次CLI/浏览器通过；CI待提交|[复审通过](2026-11-02-project-configuration-review.md)，两项已关闭|
|F1.2 单一注册与单向投影|一次选择仓库、模板、角色、执行位置、检查/策略及可选组件；同一用例生成 reference 配置；CLI/API 等价、能力与 Git 根检查、不可变文件冲突和中断恢复|未实施|待验证|待审查|
|F1.3 旧注册显式导入|检测、dry-run、差异、revision 冲突和恢复记录；不自动双向同步、覆盖旧注册或切换在途执行器|未实施|待验证|待审查|

F1 的完整原始验收仍在[详细计划](../plans/2026-11-01-all-in-one.md#f1-单一项目及有效配置)。F1.1 通过不代表 F1.2/F1.3 或正式任务 API 已完成。

## F1.1 设计与边界

已有项目仅保存 `schema_version: 1` 的绑定文档。缺 Agent 角色时原执行逻辑继承 `implementer`；缺支持层时依次使用 SQLite、manual、urls、manual、manual。doctor 对缺支持层统一使用 manual，页面又继承 implementer，二者存在显示差异。本步集中解析这些已有执行规则，修正展示，不改旧项目文档、数据库版本、模板合同或冻结的 283 个参考文件。

- `components` 是已有无业务依赖的组件所有者，增加纯绑定解析入口，供 Agent、记忆、搜索、优化、调度、kernel、doctor 和有效配置使用。旧支持层默认固定为解析版本 1 的兼容规则，不把最新推荐配置套进旧项目。
- `projects` 生成带版本、项目身份/修订、逐层来源/校验结果及内容摘要的有效绑定视图。视图范围明确为项目工具绑定，不冒充 reference 检查、策略、凭据、服务端点的完整快照；不探测或调用工具。
- CLI、Web API、控制台消费同一结果。原 `project show` 和项目创建文档保持兼容。旧项目中不兼容的继承结果可查看并定位；运行仍由所选角色/正式四角色的既有校验拒绝，不因无关角色配置阻止独立调用。
- `agent_runs` 与 `reference_executor` 保存上述视图，沿用现有绑定/项目 revision 字段。正式任务恢复只读首次选择，旧快照不重建。原六阶段引擎、证据摘要、候选校验保持不变。

不增加运行依赖、DSL、插件层或新的数据库表。新增私有摘要构造只服务本输出身份；不替换已有不同语义的摘要算法。

## 验证计划

覆盖 CLI/API 一致、旧项目只读、来源与缺项默认、无效继承可诊断、选中能力拒绝、快照稳定/跨进程读取、正式任务六阶段恢复与旧快照兼容。构建非 editable wheel 核对资源身份，运行受影响回归、依赖边界及适用完整回归；浏览器核对新增有效配置展示。Windows 由精确提交 CI 验收。

证据保存在忽略目录 `.ergora/checks/f1-configuration/`。真实模型、GPU、外部工单与服务不从确定性 fixture 推导通过。每步完成后在此记录实际命令和结果。

## 低代码研究（LC1）

按用户追加要求调研工作流画布、属性表单、页面搭建和图形库，核对官方设计/固定源码/许可，形成[低代码编辑器研究](../research/2026-11-02-low-code-editors.md)并关联 F4/F6。本轮为研究与设计依据，不安装或整包迁入其他平台。

报告已写，7个官方仓库的完整HEAD已固定，18份文件的URL/字节/SHA256复核通过；1份n8n Canvas路径404记录保留。核对Node-RED、n8n、Langflow、Dify、Appsmith官方页面及React Flow、JSON Forms、Cytoscape库文档；未实测这些平台或其性能。建议先保留当前原生界面/Cytoscape，在F6用同旅程原型比较React Flow和成熟条件表单；角色绑定、任务依赖、通信关系分别表达，布局不进入执行摘要。8份当前文档178个本地文件链接存在。

新的[LC1独立审查](2026-11-02-low-code-editors-review.md)需求符合性/可维护性均通过，范围内无findings。reviewer重新抓取全部18份固定源码/许可/包描述，身份一致，预期404保持；复核官方页面及3份主审文档54本地链接。研究审查已完成，待与本轮提交推送交付；不把该文档审查计为F1.1代码通过。

## F1.1 实现与初步验证

`components.resolve_binding`已接入实际Agent与五个支持层消费者；`agents.binding_for`保留已有Python入口。`projects.effective_configuration`构造只读视图并逐层校验。doctor及控制台用相同选择，错误配置显示原因；dashboard只读取一次项目文档，避免本响应里的项目/有效配置/doctor来自不同revision。没有新增依赖、表或修改冻结内容。

新增CLI `project config`、API `GET /api/projects/{id}/configuration`与工具页来源/完整视图。`agent_runs`在工具启动前保存`configuration`；正式桥在新选择中附加视图，已有快照不回写。

- 源码定向：`PYTHONPATH=src .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_project_configuration.py tests/test_architecture_boundaries.py tests/test_compatibility_baseline.py`，**22 passed，5.22s**；1个既有Starlette warning。
- 正式执行定向：同一解释器/PYTHONPATH运行`tests/test_reference_executor.py`，**8 passed，43.77s**。四种开发模板/工具组合、取消/清理和旧任务无新增视图的恢复均在适用fixture范围通过；不调用真实模型。日志`targeted-reference.log`。
- 12个前端ES modules的解析与链接通过，记录`modules.json`。非editable wheel已构建并安装，完整回归、两安装身份与浏览器检查尚在进行。

## 包与浏览器首轮结果

首轮wheel为`7eb6d3c6ab1496a8e5347a3647df4f9b2342c47372cd1be64487817a9d31dfa5`，Python3.12.3构建，Python3.11.15在`.venv-dev`和全新基础环境非editable安装；**335应用文件×两安装**与源码/wheel一致。完整安装回归**220 passed、18 skipped、36 subtests passed，181.47s**；1个既有Starlette warning，完整命令/环境见`regression-command.json`。18跳过为11个Windows、6个未选择固定Forge/mini和1个未选择Temporal服务。

基础环境无fastapi/uvicorn/gepa/temporalio/minisweagent：**21次模板/编译CLI**通过；另**7次配置CLI**核对创建unborn Git项目、有效配置、修订拒绝、实际command调用及跨进程快照归档。新增旅程初次误将CLI参数错误预期为退出码1，实际原契约为2；修正验收脚本，保留初始日志，未改CLI错误语义。

浏览器首次默认Chrome路径不存在，改用已有完整Chromium又因libcups缺失无法启动；最终使用本机已有且依赖齐全的Chromium headless shell，无系统包安装。初轮旅程的相对API URL缺少baseURL导致脚本错误，改完整URL后继续。随后真实复现产品问题：旧项目继承mini-swe-agent至reviewer时，配置对话框对不存在的choice访问configuration，提示TypeError且不能打开。已改为展示必选的兼容工具占位项，由用户显式选择后保存，未自动替换绑定。该修正会产生新的wheel，最终包/浏览器回归待后续记录；首轮结果不冒充修正后验收。

## 审查前本地验收

- 修正后wheel SHA256为**`bd49b976ce310bcc577542abdc034ac0b0dce853323d1b4f3c2278a0357c4f17`**；停止隔离Web服务后替换两套非editable安装，源码/wheel/两安装的**335个应用文件**一致。原始与最终清单分别为`initial-package-identity.json`和`package-identity.json`；283冻结内容保持原身份，未改实际用户安装/服务。
- 同一完整命令仅改basetemp，结果**220 passed、18 skipped、36 subtests passed，177.80s**，1个既有Starlette warning。最终输入与原始输出为`final-regression-command.json`、`final-wheel-regression.log`；不把Windows、未选择SDK/Temporal的跳过算通过。
- `final-browser-configuration.log`：真实Chromium核对12层有效配置与API一致、旧继承/支持层默认、无效配置可见、显式修正reviewer并保存revision2、刷新持久；390×844下scrollWidth=390，无pageerror。`browser-workflow.log`：旧项目在治理/大型开发/训练模板中分别显示4/4/3角色的command选择，训练kernel为manual；两开发图实际装载，三模板均无横向溢出或pageerror。
- 截图位于`output/playwright/f1-effective-bindings.png`、`f1-mobile-bindings.png`和`f1-mobile-top.png`，最后一张已实际查看。浏览器使用安装包和独立数据目录，没有通过源码覆盖页面。基础CLI的21+7次检查及其原始身份保留上一节；最终包的Python代码未在UI修正中变化。

以上为首轮审查输入的验收范围。真实模型、GPU、外部工单/服务、竞品运行/性能仍未在本切片验收。F1.2/F1.3没有实现，当前视图只覆盖项目工具绑定。

## 独立审查发现与修正

[首轮独立审查](2026-11-02-project-configuration-review.md)提出两项P2，均采纳：

- R1：技能页和资料页绕过有效配置直接读取原项目字段，缺支持层的旧项目会发生`undefined.tool`。在原wheel的真实浏览器上复现后，两页改用既有`bindingFor`；新增旧项目六页、桌面/390px旅程，核对manual优化/调度显示和pageerror。
- R2：独立调用先读项目，再由recall/search/sync重读；期间修订会使实际记忆后端与归档不同。`memory.search`/`sync`增加keyword-only的已读取项目输入，该次recall沿用同份项目；普通CLI/API仍自行读取。两条真实State回归分别在search前从SQLite改为ReMe、在sync前改变ReMe端点，仅外部请求用fixture替代，核对实际请求与持久快照一致。

修正后源码定向`tests/test_project_configuration.py tests/test_memory.py`：**9 passed，2.82s**，1个既有Starlette warning，原始日志`review-fix-targeted.log`。一次初始定向命令误用了不存在的测试路径，未运行测试；上述结果来自纠正路径后的实际运行。

修正后wheel SHA256：`3e76b1902b83871a95219d73675360b77e3d081cc727739284cf088bfcc26e73`，源码/wheel/两套非editable安装的**335文件**一致；12前端模块解析/链接通过。证据`package-identity.json`、`review-fix-install.log`、`review-fix-modules.log`；旧身份保存在`pre-review-fix-package-identity.json`。

## 修正后最终本地验收

- 非editable最终包运行与CI相同适用套件：**222 passed、18 skipped、36 subtests passed，204.11s**，1个既有Starlette warning。输入`review-fix-regression-command.json`、输出`review-fix-wheel-regression.log`，退出码0。18跳过仍为11个Windows、6个未选择固定Forge/mini和1个未选择Temporal服务；不是这18项在本机通过。
- 最终基础安装重新执行**21+7次CLI**：三模板复制/查看、两开发golden编译、转换/不可变导出；有效配置、旧revision拒绝、真实command调用及归档恢复。记录`review-fix-base-journey.json/log`、`review-fix-base-config-journey.json/log`，可选Web/优化/调度SDK缺失时仍通过。
- `review-fix-browser-all-pages.log`：缺五个支持层的同一旧项目，**1440px和390px各六页**均装载；技能页optimizer=manual、资料页scheduler=manual，12个页面均无横向溢出/pageerror。新增窄屏截图`output/playwright/f1-mobile-skill-default.png`已实际查看。
- `review-fix-browser-configuration.log`：最终安装包的12层展示/API一致，继承和兼容默认来源可见；全新无效继承fixture可显式选择兼容工具，保存revision2、刷新仍持久。`review-fix-browser-workflow.log`：三模板分别4/4/3角色继承command，训练kernel=manual，两开发图实际装载，390px无溢出/pageerror。测试独立数据目录与本机现有用户服务分离。
- 最终安装只读`ergora reference verify`：**PASS、283文件**，没有启动运行时或修改冻结内容。自有前端已无绕过有效配置的`project.bindings`读取，`git diff --check`通过。

独立复审已通过，首轮两项P2均关闭，无未解决findings；reviewer另核对30输入、335文件×两安装及283冻结身份，并重做内存探针。精确候选Ubuntu/Windows CI仍待提交/推送后核对。下一可实施节点为F1.2的单一注册与单向投影，随后F1.3；本轮不把有效绑定视图宣称为完整环境快照、全套注册或all-in-one旅程。
