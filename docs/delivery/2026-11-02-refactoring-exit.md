# S11 / R8：重构出口

日期：2026-11-02。分支 `refactor/architecture-foundations`，基线 `2a18427778ef65172bb5e6130c23876b1e579fd6`；开始时工作区干净，与远端一致。生产代码基线为 R7 的 `b8bee53bdc85a803109a9b8b804aee7408d7a535`。按已授权计划继续，不合入 main，不升级实际用户服务。

## 范围和分步

本切片为 R1–R7 出口：核对当前模块、调用、数据归属及兼容消费者，逐项结案 A1 清单，启用适用的静态边界检查，再复验相关合同、安装包、CLI/Web/模板和两 OS CI。保持生产代码、JSON/SQLite schema、旧资产和证据身份；统一项目、正式任务 API、低代码和远端执行仍属于 F/D 节点。

|分步|结果|实现|验证|独立审查|
|---|---|---|---|---|
|R8.1 架构与清单|当前责任/调用/数据图，A1 每项结论，兼容消费者和退出条件|[当前架构](../architecture/current.md)及 ADR 已写|源码/消费者及156个初审链接通过；收尾再核对|通过|
|R8.2 静态边界|选型 ADR；利用既有 pytest/标准库检查依赖方向和环|8项检查已加入；初审P2完整包名缺口已修正|最终Linux214项及10种隔离反例通过|修正复审通过|
|R8.3 出口验收|非 editable 包、相关完整回归、基础 CLI、Web/三方向及精确两 OS CI|两套包安装及最终本地验收完成|最终Linux214项+36子测试/18跳过、335文件×两安装、21次基础CLI通过；待精确两OS CI|本地范围通过；CI待复核|
|R8.4 交付|计划、独立报告、提交推送及远端身份|准备普通提交推送|待远端及CI|待最终复核|

## 已核实的基线和决定

- 当前自有包有 27 个顶层 Python 文件（含 `__init__` / `__main__`），原生前端有 12 个 ES modules。一次 AST 观察包括函数内 import，当前无自有模块导入环；不把这次观察代替持续检查或动态执行验收。
- `skills` 的旧资产入口、`tools` 的旧调用/校验入口为直接别名；生产 CLI/Web 已调用实际所有者。现有 `test_compatibility_baseline.py` 保护别名身份及无 facade 导入，新增检查不复制这些断言。
- 组件、schema、DDL、用例及前端职责分别沿用 R1/R2/R3/R4/R7 所有者。R5 的网络抓取与普通命令生命周期、R6 的框架 hook 和参考分发仍保留，不为目录布局新增基类或再拆包。
- 只读评估 [Import Linter](https://import-linter.readthedocs.io/)：本次 PyPI 返回 2.15、Python >=3.10，依赖 Click、Grimp、Rich、typing-extensions。其声明式合同和跨包图适合后续规模；当前只需少量自有 Python 导入边界，使用标准库 AST / graphlib 加既有 pytest，不增加依赖、缓存和运行命令。ADR 将限定检查范围；动态字符串/子进程行为仍由既有边界测试与实际探针验证。
- `docs/PLAN.md` 顶部正确指向 R8，末段残留 R7 已在本切片修正。历史日期审计、基线及 R1–R7 验收保持原记录，不改成当前事实。

## 验证策略

先在安装包边界检查自有 Python 的导入方向、底层依赖和无环；用隔离副本注入具体反向导入/环验证检查能够拒绝。现成兼容、迁移/备份、reference、组件/Agent、Web 和平台测试负责行为，不增加镜像实现测试。构建新的非 editable wheel，核对所有自有资源、283 冻结文件及三模板/golden 身份；在无 optional 包环境复验基础 CLI，在有 extras 的隔离安装运行相关完整回归及 Web/模板/角色检查。

浏览器已在 R7 对同一生产树完成完整旅程，本轮按实际变更决定复验范围，不复用其历史结果冒充新运行。Windows 以精确本轮提交的原生 CI 为准。真实模型/GPU、外部工单及未选择的服务不从 fixture 或 CI 推导通过。

忽略证据放 `.ergora/checks/r8/`，公共记录只含可分享身份和命令。每步分别更新实现、验证、审查状态；完整切片由新的 fresh-context reviewer 核查后才完成。

## 已完成的分步检查

- `tests/test_architecture_boundaries.py` 从实际 `ergora.__file__` 定位被测代码；标准库 AST 包含函数内显式 import，`graphlib` 拒绝环，另外保护底层模块、业务不导入传输入口及原执行器内部模块的边界。现有 CI 已运行 `tests`，无需增加第二条 CI 命令。
- 定向命令：`.venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider tests/test_architecture_boundaries.py tests/test_compatibility_baseline.py tests/test_components.py`，**23 passed，4.86s**。包代码仍为 R7 安装树，与本轮源码相同；待本轮新 wheel 的完整回归单独记账。
- `boundary-probes.py` 只复制27个自有顶层Python文件，分别注入 evaluation→optimization 的环、state→memory 的底层反向依赖、memory 函数内→web、memory 函数内→agent_platform.core；4次选定检查均以退出码1、恰好1个失败拒绝。注入代码仅被 AST 读取，从不执行；原源码/实际安装未改。原始四份 `*-rejected.log` 与 `boundary-probes.json` 保留。
- README、计划、两份 ADR、当前架构和本记录共7份文档的155个本地文件链接存在；空白检查通过。最终收尾/审查链接增加后再核对。
- 初次用 `.venv-dev/bin/python -m build` 失败：该环境未安装 build CLI（仓库构建目录被识别成同名 namespace）。未修改依赖或代码，改用已有系统 build 安装；构建与后续安装结果继续记录。

## 本轮本地出口验收

- 系统 Python **3.12.3** 的 `python -m build --wheel --no-isolation --outdir .ergora/checks/r8/dist` 成功；wheel SHA256 为 **`83ffb3a97c06f1eb63b88b996e817adcb9c46fdaab70f7c1e93c367e75f4dc62`**。验收解释器为 Python **3.11.15**。首次用该 uv 环境的 `python -m pip` 失败（未装 pip），未改包依赖，沿用已安装 uv 进行安装；两次工具缺失的原始日志均保留，非产品回归失败。
- 既有 `.venv-dev` 和新 `.ergora/checks/r8/base-venv` 均非 editable 安装本轮 wheel。`verify-package.py` 核对源码、wheel、两安装的 **335 个应用文件**逐字节一致，含12个原生前端模块；`r7-comparison.json` 另核对335个文件与R7最终wheel全部相同。新wheel的README元数据和打包身份单独记录，不把压缩包SHA变化误报为应用源码变化。
- 完整命令：`PYTHONPATH=src/ergora/data/reference/platform/upstream/platform PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp .ergora/checks/r8/wheel-tests tests src/ergora/data/reference/platform/upstream/platform/tests/test_contracts.py src/ergora/data/reference/platform/upstream/platform/tests/test_portable.py src/ergora/data/reference/platform/upstream/platform/tests/test_workflow.py::AdapterTests src/ergora/data/reference/platform/upstream/platform/tests/test_runtime.py`。实际PYTHONPATH及参数为绝对路径，仅加载冻结参考依赖，Ergora来自新安装包，完整调用保存在 `regression-command.json`。结果 **214 passed、18 skipped、36 subtests passed，177.47s**；1个既有Starlette warning，日志 `wheel-regression.log`。
- 18项跳过为11个原生Windows、6个未显式选择的固定Forge/mini SDK测试、1个未选择的隔离Temporal服务；不把跳过当通过。新增8项静态检查、旧数据/摘要/exec位、迁移中断与旧writer拒写、备份/恢复/篡改拒绝、进程清理、六阶段精确候选证据、三方向角色切换和Web业务回归均在适用测试范围内。
- `.ergora/checks/r8/base-venv/bin/python .ergora/checks/r8/final-base-journey.py` 的 **21次CLI**符合预期：283冻结文件、三模板视图/复制/角色、两golden编译、转换/验证和不可变导出。该环境不存在 fastapi/uvicorn/gepa/temporalio/minisweagent，结果及每次argv/退出码在 `final-base-journey.json`，日志 `final-base-journey.log`。
- Web本轮为安装包上的既有TestClient回归：同源/Host拒绝、绑定revision/归档边界、来源记忆、三模板/DAG、训练角色结构化调用、Skill diff/评价/采用。未新增浏览器旅程；R7曾对完全相同的335文件运行真实Chromium/390px/响应乱序验收，保留其原始身份和范围，不标成本轮新运行。没有新服务/浏览器需要清理。
- AST观察为27模块、86条自有显式导入边（含函数内），原执行器内部导入只在 `reference/reference_executor`。`git diff 2a18427 -- src pyproject.toml .github/workflows` 为空，无生产/依赖/schema/CI语义变化；测试和文档是本轮全部范围。没有迁移用户实际数据或重启实际服务。

真实模型/GPU、固定Forge/mini SDK、外部工单、ReMe/Temporal服务、无宿主依赖的空白Windows安装未在R8重验。L0/R5/R7的实际运行保留各自身份，不从本轮确定性fixture推导模型或训练收益；精确本轮Windows/Ubuntu CI仍待提交后核对。

## 审查与交付状态

新的fresh-context [初审](2026-11-02-refactoring-exit-review.md)完成，提出2项：

- **P2 reference显式完整包名漏检**：原规则只匹配 `agent_platform/dev_platform` 首段，普通 `ergora.data.reference...` namespace 导入可以绕过。已在同一个检查内增加随包命名空间前缀，覆盖普通import及绝对/相对from；没有增加解析平台或执行注入代码。修前两路径已独立重现，原证据保留。
- **P3 GEPA当前校验描述过时**：当前bindings调用contracts与components schema，不再保留旧递归。已修正当前架构的A1结案表；不修改历史审计或恢复递归代码。

其余初审范围无新增findings。修正后 `final-boundary-probes.py` 实际运行 **10种隔离反例**：保留原4种，再加完整包名普通import、相对from、绝对from，各含顶层/函数内作用域；10次均以退出码1和恰好1个失败拒绝。最终六条完整包名反例由原规则漏检，现已全部拦截；日志为 `*-final-rejected.log`，汇总 `final-boundary-probes.json`。只在测试副本做AST读取，没有执行原配置模块。

最终8项检查的同一完整回归已经结束：**214 passed、18 skipped、36 subtests passed，181.87s**，仍为1个既有Starlette warning。除basetemp改为 `.ergora/checks/r8/final-wheel-tests` 外，命令与首轮相同；完整最终调用与原始日志为 `final-regression-command.json` / `final-wheel-regression.log`，首轮日志保持原样。10种反例与最终完整回归共同覆盖修正后的测试实现。

[同切片复审](2026-11-02-refactoring-exit-review.md)已经落盘：P2/P3均已解决，需求范围与可维护性通过，无新增/未解决findings。reviewer独立核对最终原fixture、六条完整包名反例、父命名空间导入、bootstrap路径及相似名前缀，读取全部10份失败日志和最终完整回归；最终测试SHA256为 `de2d71626793076fd63292cbfe4df82bd5b6640bc2b00e5cb72a8d0953cbf762`。没有扩大生产改动。

接下来普通提交推送，再核对精确两OS CI及远端。R8尚未标为全部完成，F1尚未实施。
