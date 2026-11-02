# S11 / R6：reference 访问边界

日期：2026-11-02。分支 `refactor/architecture-foundations`；开始时工作区干净，HEAD `d685bb9867ef2cdc35d3c5b785dba2bb147dbeac`，已推送并核对远端。前置R5独立审查完成；生产基线仍为 `f9a9b743be1b5bde352d212b75c47358d5d73e9a`。

## 范围与验收

用户授权继续按计划实施。核对发现：原配置/状态全局、Executor继承、file/ledger及receipt发布已经局限在reference/reference_executor边界；编译也已用隔离子进程。当前应用层泄漏是Web直接拼接冻结模板目录并读文件。将该读取移到reference公开接口，让HTTP只传输结果；不改响应格式或原文件内容，不增加第二个runtime包装层。

|分步|产出|实现|验证|独立审查|
|---|---|---|---|---|
|R6.1 模板读取归属|移入reference，Web不依赖ROOT布局；保持开发input/训练files/agents响应|完成|20项定向通过|通过|
|R6.2 既有适配边界及退出清单|明确配置定位、编译、正式任务查询/命令、绑定快照、文件/ledger和Windows reader责任；记录保留理由及未来迁出条件|[边界及退出清单](../architecture/reference-boundary.md)已写|原合同/六阶段/绑定及静态检查通过|通过|
|R6 完整验收|非editable wheel、基础编译/模板、原六阶段/冻结绑定、导出/恢复/精确批准的适用回归及冻结身份、真实两OS CI|已打包安装，候选已推送|Linux206项+36子测试/18跳过、324文件×两安装、21次基础CLI及两OS CI通过|[通过](2026-11-02-reference-boundary-review.md)|

## 责任与非目标

`reference.py`继续是冻结资源及编译/执行加载的边界；`reference_executor.py`继续承载原Executor实际hook及原CONFIG/STATE、文件/ledger操作；`stage_driver.py`仅在专用进程处理凭据/信号/Agent调用。没有第三个相同职责的adapter，也不为原函数一一增加转发包装。

正式任务status/start/approve/cancel/export目前属于原agentflow/DevelopmentRuntime，尚无统一Ergora任务API；新任务用例归F1/F3。当前executor为单一安装的专用进程，不把导入时固定的原全局配置当作Web中可热切换的多实例服务。F3若需查询/命令，须使用明确安装/配置/状态的隔离访问，不能从Web直接载入原全局。训练仍保留人工run-local及manifest SHA边界。

不新增正式任务入口、调度器或协议，不切换在途任务引擎，不改变模板/摘要/批准/回执语义；283冻结文件、local/bootstrap镜像和旧HTML保持原字节。新增公开reader属于reference资源接口，有实际Web消费者；不引入通用模板基类或目录repository。

## 计划验证

先运行现有reference/Web/兼容定向检查，再构建非editable wheel、核对源码/安装及冻结283文件身份，运行相关完整Linux回归。沿用原执行器fixture，分别检查两开发模板与command/Codex协议、在途冻结绑定、可信集成/检查及回执；原portable/runtime/adapter测试负责批准拒绝、导出不可变及恢复合同。基础无extras环境核对模板/编译独立性；Windows保留真实CI、不用Linux模拟reader。没有生产行为/接口合同改变，不为搬移代码新增镜像实现测试。

所有测试/构建数据放忽略的`.ergora/checks/r6/`。不更换用户运行服务或实际项目注册；不在本节点再次进行模型/GPU/公网工单测试。实际结果、独立审查、推送身份和未验项逐步补录。

## 实际变更与检查

- 生产仅改`reference.py / web.py`：`template_details`承接原Web读取代码，返回结构、UTF-8文本及未知模板错误保持；HTTP路由直接传输结果。原Executor、导入加载、Windows reader、原全局/ledger及候选规则均未改。新函数是有真实消费者的reference资源接口，不是逐函数转发层。
- 源码定向：`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp .ergora/checks/r6/targeted-tests tests/test_reference.py tests/test_web.py tests/test_compatibility_baseline.py`，**20 passed、1既有Starlette warning，18.56s**；日志`.ergora/checks/r6/targeted-regression.log`。
- 离线`uv build --wheel`及两套非editable安装成功；wheel SHA **`2e0c239583c232fed1294bf7d9be0a75a6ea987acb5cefc1dd311fc62cdeaf05`**。324个应用文件与源码及开发/基础两个安装逐字节匹配；清单`.ergora/checks/r6/package-identity.json`。构建/安装日志在同目录，未升级实际用户服务。
- 新基础环境无fastapi、uvicorn、gepa、temporalio、minisweagent，真实执行 **21次CLI调用符合预期（19成功、2预期不可变导出拒绝）**。三模板复制/reader/角色合同一致，两开发模板编译摘要等于旧golden，convert/validate/compile/export往返及重复发布通过，篡改已有export明确拒绝；unknown reader错误保持。脚本`.ergora/checks/r6/base-journey.py`，逐次记录`.ergora/checks/r6/base-journey.json`。不依赖Web或外部服务。

- 非editable包完整Linux命令：`.venv-dev/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp .ergora/checks/r6/wheel-tests tests src/ergora/data/reference/platform/upstream/platform/tests/test_contracts.py src/ergora/data/reference/platform/upstream/platform/tests/test_portable.py src/ergora/data/reference/platform/upstream/platform/tests/test_workflow.py::AdapterTests src/ergora/data/reference/platform/upstream/platform/tests/test_runtime.py`，`PYTHONPATH`仅指冻结`upstream/platform`、`PYTHONDONTWRITEBYTECODE=1`，不选择外部SDK/Temporal服务。**206 passed、18 skipped、36 subtests passed、1既有warning，176.35s**；日志`.ergora/checks/r6/wheel-regression.log`。覆盖两开发模板×两个Agent协议的原六阶段、后续binding变更不改变在途任务、candidate-bound检查/回执、取消、精确批准和portable导出/恢复合同。
- 18项跳过为11项Windows-only、6项未选择的Forge/mini SDK、1项未选择隔离Temporal；不将R5的SDK实跑当成本轮重验。未跑真实模型/GPU、真实Temporal服务旅程、新浏览器交互或空白Windows安装；未改界面JS。原L0验收的身份与范围独立保留。
- 五份当前文档102个本地文件链接及空白检查通过；应用中原agent_platform/dev_platform导入只在reference/reference_executor，已无`reference.ROOT`或其私有入口的应用访问。非editable`reference verify`为 **PASS / 283 files**；源码diff确认冻结数据、测试、依赖及CI未改。清单`.ergora/checks/r6/static-checks.json`。与R4包清单统一相对路径后，仅`reference.py / web.py`两文件内容变化，其余322文件不变。

## 候选与跨平台CI

实现候选 **`277ec1f76e0b304dc30fb82a14e0f95ac9d022d1`** 已推送`origin/refactor/architecture-foundations`，再次读取远端SHA一致。该候选的[Portability CI 41388048791](https://github.com/626619403/Ergora/actions/runs/41388048791)为 **completed / success**：Ubuntu job **125093151283**（Python3.11，1m10s）和Windows job **125093151521**（Python3.12，2m52s）均成功。官方API的run与两个job均指向相同完整候选；不是复用R5的历史CI。

原始官方响应`.ergora/checks/r6/ci-run.json / ci-jobs.json`，摘要`.ergora/checks/r6/ci-status.json`，2026-11-02 04:26:24 UTC核对；两原始响应SHA分别为`7615fe45a2342e95eb89d22b10273577330403cb694dc32d199592e68ab5420e`、`a5d89b7ecf9b1767fb0e3058de355f2deb340f286a93ef8e7a6cec7231ca817a`。未下载逐项测试日志，不据job成功补造Windows项数；workflow包含真实原生回归及Windows安装/升级步骤。

新增详细计划导航后再次检查五份文档 **104个本地文件链接** 和空白，记录`.ergora/checks/r6/static-checks-final.json`，此前102个的初轮记录保留。源码/测试/CI在候选后未改。

## 独立审查与下一步

新的fresh-context reviewer已完成[独立审查](2026-11-02-reference-boundary-review.md)，需求符合性、可维护性及精确两OS CI均通过，无findings和阻断性验收缺口。独立检查候选diff、真实消费者、324文件×两安装、283冻结身份、原始CLI/回归日志、官方CI响应及实际断言；未把只读复核当作再次跑测试。

**R6完成。** 生产/测试验收身份保持`277ec1f76e0b304dc30fb82a14e0f95ac9d022d1`；本次收尾仅提交审查及状态文档，按原授权推送当前分支。原模型/GPU/真实服务/浏览器等未验维度保持上述范围；原执行器仍是生产路径，冻结目录尚未退为归档。

收尾核对：包含新审查报告的六份当前Markdown共 **112个本地文件链接** 目标存在，空白检查通过；`git diff 277ec1f -- src tests README.md pyproject.toml .github/workflows`为空。记录`.ergora/checks/r6/closure-checks.json`。仅状态/审查文档更新，无须再次运行已通过的代码测试。

下一节点R7：按请求/状态、项目与绑定、记忆/Skill资产、研究、模板图及运行视图的真实责任拆分现有ES modules，保持Cytoscape和纯文本DOM、异步顺序/草稿revision/同源边界；入口继续直接使用领域用例，不引入Node构建要求或框架重写。先读本记录及PLAN核对Git，分别验包文件、API/CLI与真实浏览器操作，再进行新的独立审查。
