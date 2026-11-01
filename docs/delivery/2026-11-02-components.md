# S11 / R1：组件描述与绑定所有权

日期：2026-11-02。基线 `588161b04d2ca56805220a2dcb5c11b7caa2773a`，分支 `refactor/architecture-foundations`，开始工作区干净。A2 的代码/测试/CI 身份为 `4deb8b7`，本基线只追加已审查的文档收口。

## 本切片范围与验收

把角色、能力、选择、配置字段、平台、默认绑定及安装来源集中到随包内置 JSON；Python 读取者负责目录/配置视图，不加载任意外部插件。实际消费者是 agents、tools、projects、kernel、Web bootstrap/页面表单和 SDK 安装器。进程执行、probe、结构化协议、可信门禁继续使用现有实现。

保留旧绑定接受/拒绝、默认和目录输出已有字段；新增配置描述供 UI/CLI 共用。删除经 A1 证实不可达的 tools 校验分支；不删除 GEPA 对 Agent 命令的真实委派。原 schema/DB、摘要、模板、reference 283 文件和旧 HTML 不变；JSON Schema 校验依赖在 R2 接入，不混入 R1。

验收包括：已有回归与 A2 golden；全部绑定矩阵；缺失可选 SDK 不影响普通 CLI；固定安装配方；新兼容 command 组件不改模板/JS 工具分支即可通过真实调用；通用配置表单的实际浏览器操作；Linux/Windows CI。只有声明而无实际适配的后端不能广告为可执行。

## 实现与验证进度

完成：实现、Linux、浏览器、两 OS CI、[独立代码审查与补丁/CI 复核](2026-11-02-components-review.md)均通过；无未解决 findings。

- `components.json` / `components.py` 集中 12 层、11 个工具的描述和派生目录；agents/tools/projects/kernel/reference_executor 复用。保留实现分派与业务校验，不加载外部插件。
- Web bootstrap 增加 `layers`，目录追加 configuration/note/installation；表单按类型和枚举生成，保留原层显示顺序。修正可选字段的 HTML required 属性写法。
- SDK 安装器读取同一个描述的固定源码/提交，安装目录和独立 venv 不变。工具手册新增维护说明及当前扩展范围。
- 新增旧目录已有字段夹具（从基线真实函数生成）、绑定矩阵、默认值隔离、平台表单默认、新 command 组件的跨进程真实结构化调用、缺少 SDK 的 CLI 和安装配方检查。原 reviewer 测试改为 mock 实际拥有调用的 `agents.processes`，不保留 tools 中无生产用途的导入。

当前实际检查：

|检查|结果与范围|
|---|---|
|系统 Python `-m build --wheel --no-isolation --outdir .ergora/checks/r1/dist`；`uv pip install --python .venv-dev/bin/python --no-deps --reinstall ...whl`|成功；非 editable wheel，24 个应用 Python/描述/JS 文件与源码逐字节一致|
|`pytest -q tests/test_components.py tests/test_projects_tools.py tests/test_web.py tests/test_installation.py --tb=short`|25 passed，12.68s；真实 SDK 安装/下载由可控替身代替，无模型/GPU|
|`.github/workflows/portability.yml` 的完整 Linux regression step|152 passed、17 skipped、36 subtests passed、1 既有 warning，80.46s；包含原 Adapter/Runtime 与 A2 固定身份|
|安装 wheel 的 `python -m ergora reference verify`|PASS，283 个冻结文件和原 zip 身份保持|
|`node --check src/ergora/data/console/app.js` / `bash -n scripts/install-agent.sh`|通过|
|真实 Chromium headless shell / Playwright CLI|Codex / Claude 留空模型，mini 必填模型/可选 Python/数字，command 数组/协议/角色能力，ReMe 可选 token_env，GEPA 参数数组，Forge 路径与未安装展示，Temporal 项目 queue，刷新恢复及切回默认工具均通过；390×844 弹窗 x=18、width=354、height=552.28，在 viewport 内|
|两 OS CI|[41333003887](https://github.com/626619403/Ergora/actions/runs/41333003887)，精确 `1cbc77e8cc799d68985a908f48da64c481332a08` / `refactor/architecture-foundations`；Status Success，Windows/Ubuntu 两 jobs 完成，2m34s；公开页面不提供完整日志，不推导 Windows 测试计数|
|独立审查|[代码与补丁/CI 复核通过](2026-11-02-components-review.md)，无未解决 findings；审查者独立重跑 8 项及补丁矩阵 1 项，24 文件 wheel 一致；公开 HTML 与 jobs API 确认精确 head_sha、分支及 Windows/Ubuntu 各 completed/success|

初次局部回归捕获到两个测试仍 mock 已删除的 tools.processes 导入；已迁到实际调用所有者后，局部和完整回归通过。早于 wheel 重装的检查不作为本节点证据。

浏览器材料位于忽略的 `output/playwright/r1-temporal-{mobile,viewport}.png`，使用本节点独立测试项目、非 editable wheel 和 loopback 服务。只验证配置和展示，没有调用真实模型/GPU或远端 ReMe/Temporal。自动化先后纠正了 select 的精确 label 定位和刷新后需要重新打开工具页的操作；不是产品错误。未安装系统库，使用已有缓存 headless shell；npm 使用隔离验收缓存，未改用户配置。

候选 `007a88ecd7529d2838ad8f0f0c5b4b7635898e7d` 已推送并核对远端一致。CI [41332520254](https://github.com/626619403/Ergora/actions/runs/41332520254) 的 Windows 回归暴露新增 Forge 绑定测试用了 POSIX 绝对路径（`/forge`）；该路径在 Windows 正确被原业务规则拒绝。`1cbc77e` 已将测试数据改为 runner 自身的绝对路径，本地 6 项通过（0.53s），不改变产品校验或 Linux 专用支持范围。修正已推送，新 CI 两 OS 成功。首轮 Ubuntu job 曾仅根据无失败公告推断成功，该推断不计验收；最终成功依据为新 run 的明确整体 Success 和两 jobs 完成。

## 迁移与下一动作

不迁移用户数据；项目创建时复制默认，已保存项目/冻结任务绑定不自动变化。UI 注解只用于配置输入，保存仍经过原业务校验。回退是本节点正常提交；在途任务不换执行器。运行实现 `007a88e` 和跨平台测试修正 `1cbc77e` 均已推送并核对；本次收口仅补文档与审查记录。下一项 R2：共享结构 schema、错误字段路径与身份规则，继续保持存储和冻结内容不变。
