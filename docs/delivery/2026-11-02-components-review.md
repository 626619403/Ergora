# S11 / R1 独立审查：组件描述与绑定所有权

日期：2026-11-02。审查者：独立 Codex agent `/root/components_review`，fresh context；未继承实现对话。先阅读原始 R1 验收及实际 diff，再阅读交付叙述。项目根为 `Ergora/`，本记录属于该项目的 `docs/`。

## 身份与范围

- 精确基线：`588161b04d2ca56805220a2dcb5c11b7caa2773a`。
- 首轮完整审查提交：`007a88ecd7529d2838ad8f0f0c5b4b7635898e7d`；分支 `refactor/architecture-foundations`。首轮审查开始及写初稿前，工作区均无实现差异或 untracked 文件。
- 补丁复审提交：`1cbc77e8cc799d68985a908f48da64c481332a08`；相对首轮仅修改同一范围内的 `tests/test_components.py` 和交付记录，生产源码、脚本及依赖无差异。下文结论包含该补丁。
- 完整范围为 `git diff 588161b04d2ca56805220a2dcb5c11b7caa2773a..007a88ecd7529d2838ad8f0f0c5b4b7635898e7d` 的 19 个文件，均已读取：

```text
docs/AGENT_BACKENDS.md
docs/PLAN.md
docs/delivery/2026-11-02-components.md
docs/plans/2026-11-01-all-in-one.md
scripts/install-agent.sh
src/ergora/agents.py
src/ergora/components.py
src/ergora/data/components.json
src/ergora/data/console/app.js
src/ergora/kernel.py
src/ergora/projects.py
src/ergora/reference_executor.py
src/ergora/tools.py
src/ergora/web.py
tests/fixtures/components-v0_2_0.json
tests/test_components.py
tests/test_installation.py
tests/test_projects_tools.py
tests/test_web.py
```

适用规则为仓库 [AGENTS.md](../../AGENTS.md) 及 `maintainable-project-delivery` 的独立审查规则。另检查了基线 agents/tools、当前 CLI、stage_driver、打包声明、CI workflow、A1 删除依据和 ADR 0001。未改源码、测试、依赖或安装；仅写本报告，未提交或推送。

## 分别结论

**需求符合性：通过。** 代码审查、Linux/浏览器既有证据、补丁复核及精确提交的真实两 OS CI 已齐备。组件能力、平台、操作、配置、默认绑定和固定安装来源已集中，现有消费者实际使用；现有绑定合同、默认和可信执行边界保持。未把 R2 schema 校验依赖、DB 或用例重构带入此切片。

**可维护性：通过。** 在上述差异与必要调用者范围内无 correctness、ownership、实际复用或多余控制流 findings；无须修复的阻断项。该结论及 CI 不扩展现有 Windows 支持范围，也不等于模型效果、GPU 或远端服务验收通过。

## 证据与判断

|方面|检查结果|
|---|---|
|正确性与兼容|`agents.py:20`、`tools.py:20`、`kernel.py:17` 仍拥有原绑定业务校验；允许字段改读描述，原有合法/非法集合未扩大。独立从精确基线 AST 取出的 `ROLE_CAPABILITIES`、`GENERAL_CAPABILITIES`、`TOOL_CAPABILITIES`、`CHOICES` 与当前四个派生视图完全一致；新增绑定矩阵、旧目录夹具和默认隔离检查通过。|
|实际消费与默认所有权|`components.py:8` 读取随包 JSON；agents 派生角色/选择及驱动名，tools 派生目录/字段视图，`projects.py:26` 复制新项目默认，kernel 读取 Forge 固定版本，CLI 通过原 tools/agents 入口，Web bootstrap/表单消费相同数据。默认复制避免后续项目修改污染其他项目；显示默认没有注入已保存绑定或冻结快照。|
|真实 probe 与安装|`tools.py:58` 仍分别使用可执行文件解析、模块存在探测及明确的未知状态；目录未将认证/连通写成成功。doctor 继续按具体绑定检查 mini 的 Python 和 Forge campaign。`install-agent.sh:17` 实际读取同一文件的 git repository/commit，后续 fetch 和已有 checkout 校验消费这些值；两个固定配方的离线替身检查通过。|
|新组件与执行边界|`test_components.py` 的 `test_added_command_component_runs_template_without_vendor_branches` 在复制的包中添加 `implementation: command` 的 fixture-harness，跨进程注册、绑定并真实调用 training-optimization 的 experiment-planner，检查真实结构化产物、catalog 和 doctor；模板保持相同。`agents.py:106` 与 `reference_executor.py:44` 按实现名处理协议，模板和 JS 无 fixture/厂商新增分支。兼容命令仍受同一能力及结果校验，未把描述当作新 SDK 实现。|
|新增抽象的实际复用|新 `components.py` 的数据接口由 agents、tools、projects、kernel、reference_executor、web 多个生产文件消费；安装器直接读取同一 JSON，不为脚本导入应用或可选 SDK。`configuration()` 只有 tools.catalog 一个直接生产调用者，但它拥有平台/角色配置投影和副本隔离这一配置接口语义；`_choices()` 是该所有者内凝聚的私有派生算法。未用测试、重导出或假定未来调用者凑复用。|
|必要控制流与删除|组件版本拒绝保护随包目录格式；按角色能力/支持层过滤、平台显示默认/枚举过滤及声明能力默认都有实际消费者。`tools.py:58` 的 probe 分派保留未知，未知 probe 显式失败。`app.js:693` 的分支只处理当前声明的字段类型；可选空值跳过、数组解析和数值转换保护实际表单提交，`required: null` 避免可选字段被 HTML 布尔属性误设为必填。A1 证明不可达的旧 tools Agent/model/command 块已删；`tools.py:43` 的 GEPA → implementer command 校验委派仍可达且保留。|
|可信合同与范围|reference_executor 仅将原 command 判断改为实现名判断；新任务绑定快照、既有快照恢复及六阶段/可信 integrate/verify 的所有权不变。差异没有修改冻结 reference、模板、旧 HTML、hash 或 DB/schema。|
|记录与交接|首轮计划及交付记录明确区分已实现、Linux/浏览器已验和当时待完成的两 OS CI/独立审查；没有把历史 Windows CI 或配置展示扩写成当前执行验收。本报告后续补记核实了最终 CI；节点状态由实施者据此收口，下一节点仍为 R2。|

## 本审查实际检查

运行环境：Linux，`.venv-dev/bin/python` 为 CPython 3.11.15，`ergora` 从非 editable 的 `.venv-dev/lib/python3.11/site-packages/ergora` 加载。

- `PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q -p no:cacheprovider --tb=short tests/test_components.py tests/test_installation.py::test_optional_installer_consumes_pinned_recipe_without_network`：**8 passed，2.68s**。包含缺失可选 SDK 的普通 CLI、默认隔离、新兼容组件的真实协议调用及两个安装配方；未执行实际下载/安装。
- 独立逐字节比较源码、现有 wheel、已安装包的全部 22 个应用 Python 文件及 `components.json`、`app.js`：**24 文件一致，0 mismatch**。wheel `.ergora/checks/r1/dist/ergora-0.2.0-py3-none-any.whl` 的 SHA-256 为 `06746c7e9d652eae4a3a663ae16f81f75830f1932cf730538959ec2730ba7c70`。
- 安装包的 `python -m ergora reference verify`：**PASS，283 文件**，source zip SHA-256 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，未启动 runtime；完整 diff 无冻结目录或 HTML 改动。
- `node --check src/ergora/data/console/app.js`、`bash -n scripts/install-agent.sh`、`git diff --check BASE..HEAD`：通过。
- 阅读 `.ergora/checks/r1/regression.log`：记录为 **152 passed、17 skipped、36 subtests passed、1 个既有 Starlette warning，80.46s**；与当前 workflow 的 Linux regression 范围及交付记录一致。该完整回归是实现者的本节点运行，本审查未重跑。
- 查看 `output/playwright/r1-temporal-viewport.png`：390×844 的 Temporal 弹窗完整落在视口内。交付记录提供的配置保存、刷新、默认切换及 console 0 errors/warnings 属于实现者真实浏览器检查；本审查没有重放浏览器全旅程，截图本身仅证明该画面。

## Windows 测试数据补丁复审

首轮 CI [41332520254](https://github.com/626619403/Ergora/actions/runs/41332520254) 已确认 Windows 新绑定矩阵失败（实现者提供的日志摘要：1 failed、88 passed、25 skipped）：有效 Forge 测试数据使用 `/forge`，不满足 Windows 的原有绝对路径校验。首轮 Ubuntu job 未单独核对状态，不作为成功证据。本审查确认 `kernel.validate_binding` 的该校验在基线中已存在；不能以此放宽生产输入或宣称 Windows 支持 Forge 执行。

已读取 `007a88e..1cbc77e8cc799d68985a908f48da64c481332a08` 全部补丁。修正将有效样例改为 `Path(__file__).resolve().parent` 下的路径及 `sys.executable`，只是跨平台合同测试数据；未知字段、错误角色和无效绑定断言仍保留。交付记录保存首次失败和未完成状态。最小修正适当，复审通过，无新增 findings。审查者在 Linux 重跑受影响的 `test_binding_matrix_preserves_acceptance_and_rejection`：**1 passed，0.02s**；补丁 `git diff --check` 通过。这不替代新提交的真实 Windows CI。

## 最终两 OS CI 独立核对

审查者于 2026-11-01 17:49 UTC（北京时间 2026-11-02）独立以新时间戳读取公开 [run 41333003887](https://github.com/626619403/Ergora/actions/runs/41333003887)，HTTP 200，页面显示 **Status Success、2 jobs completed、2m 34s**；与实现者保存的 `.ergora/checks/r1/ci-fixed.html` 一致。随后独立读取 GitHub 公共 jobs API（HTTP 200，服务端 Date 为 `Sun, 01 Nov 2026 17:49:28 GMT`），逐 job 核实，未仅从无失败公告推导成功：

|job|精确 head_sha / head_branch|状态与结论|
|---|---|---|
|[native (windows-latest, 3.12) / 124926862162](https://github.com/626619403/Ergora/actions/runs/41333003887/job/124926862162)|`1cbc77e8cc799d68985a908f48da64c481332a08` / `refactor/architecture-foundations`|`completed` / `success`；2026-11-01T17:47:01Z 完成|
|[native (ubuntu-latest, 3.11) / 124926862331](https://github.com/626619403/Ergora/actions/runs/41333003887/job/124926862331)|`1cbc77e8cc799d68985a908f48da64c481332a08` / `refactor/architecture-foundations`|`completed` / `success`；2026-11-01T17:45:29Z 完成|

最终 CI 对应本次已审查的原生路径测试补丁；两 OS 验收证据已补齐，本切片无剩余审查或 CI 阻断项。

## 保留限制

真实模型认证/效果、GPU、远端 ReMe/Temporal 未验收，保持原限制；上述 CI 仅证明 workflow 定义的打包、身份及回归范围。R2 的集中 JSON Schema 校验与后续 DB/用例重构不属于本次结论。
