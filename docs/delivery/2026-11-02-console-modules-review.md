# S11 / R7：CLI/Web 与前端模块化独立审查

日期：2026-11-02。审查者：Codex 独立 reviewer（`console_modules_review`），fresh context；未继承实施会话。先读取项目 `AGENTS.md`、[原始 R7 要求](../plans/2026-11-01-all-in-one.md#r7-cliweb-与前端)、独立审查规则和实际源码，再核对[交付记录](2026-11-02-console-modules.md)及验证材料。仅写入本审查记录；未改源码、安装、运行服务、提交或推送。

## 审查身份与范围

- 基线：`c0ad3433f0b507d28e0d4e219a7f1860a64e6367`；分支 `refactor/architecture-foundations`。初审对象为当时尚未提交的完整工作区，包含 tracked 与 untracked 文件；最终提交及远端复核见末节。
- 审查前候选清单：`.ergora/checks/r7/review-context.json`，SHA256 `df098ec2091a9b854f232d8d5cb7a0ea51cc9b9876384ca1d9da10b9db3f8de8`；其中全部 18 个文件的实际 SHA256 和 Git 变更集合独立核对一致。完整差异 `review.diff` 的 SHA256 为 `e2b14fb2a41ceeb230d98c0cb9a8a412dc19dc16cf16cd00f87f7136ace9d124`，已核对。
- 生产候选身份：将清单中 `src/` 项按路径排序，以 UTF-8 的 `路径\tSHA256\n` 拼接后计算 SHA256，结果为 `e56ad9bb448d94ffe6343742adfa4a8eec699c8d8f2ba0072cf00062dbe7371e`。
- 最终本地 wheel SHA256：`e67755fb3b109ed6794a98beb45fe33a0edfa2a7bed9a6569a625851fdf8d673`。

实际逐项检查的变更文件：

|位置|文件|
|---|---|
|`src/ergora/data/console/`|`app.js`、`api.js`、`state.js`、`ui.js`、`projects.js`、`tools.js`、`overview.js`、`agents.js`、`memory.js`、`skills.js`、`research.js`、`workflow.js`、`style.css`|
|`src/ergora/`|`web.py`、`skill_assets.py`|
|`docs/`|`PLAN.md`、`plans/2026-11-01-all-in-one.md`、`delivery/2026-11-02-console-modules.md`|

邻接核查包括原 `app.js`、`index.html`、CLI 分派、`skills.py` 的采用调用者、资产读取/身份检查、`tests/test_web.py`、`pyproject.toml`、`.github/workflows/portability.yml`，以及实际浏览器脚本和检查入口。未将冻结参考、未改依赖或未实现的 F3/F4/F6 作为本切片实现内容。

## 分别结论

**需求符合性：通过，含最终远端复核。** 请求、显示状态、项目/绑定、资产、研究、工作流/图及 Agent 运行视图已按真实责任拆成原生 ES modules；现有页面、Cytoscape、R1/R2 元数据与 HTTP/CLI/合同语义保持。单条窄屏修复有原基线反例，范围合理，已与职责移动分别提交。精确生产候选 `b8bee53bdc85a803109a9b8b804aee7408d7a535` 已推送，远端 SHA 独立核对一致，Ubuntu/Windows CI 均成功；原源码、远端与 CI 待验项已关闭。作者尚需登记完成并提交推送最终状态文档。

**可维护性：通过。** 在下列检查范围内无需要修正的 findings，无源码阻断项。拆分保持完整页面与状态生命周期，未建立通用 view 框架、服务转发层或推测性扩展接口。单消费者页面模块具有完整页面责任，Agent 对话框/归档显示具有明确运行视图归属，不以调用者数量要求继续合并或拆碎。

## 结论依据

- [入口](../../src/ergora/data/console/app.js)只协调 HTTP 刷新、导航和视图组合；`refreshSequence` 保留。视图显式接收所需 `refresh/render`，均不反向导入入口。`api/ui/state` 分别承接请求、DOM/表单和 UI 选择/服务器快照；模块导入图无环。实际共用的 DOM、绑定解析和阶段显示保持共享；私有表单辅助函数仍留在所属页面。
- [工作流](../../src/ergora/data/console/workflow.js#L8)保留草稿、epoch、kernel 请求身份和图实例的同一所有者。`resetWorkflow` 的实际生产调用者是注册项目和切换项目；`disposeGraph`承接原入口的销毁逻辑。`drawGraph` 的项目/输入判断从原 `render` 移至拥有草稿的模块，判断条件等价。模板乱序、保存期间编辑、后续 revision 对账和 kernel 的视图归属判断正文保持。
- [资产 diff](../../src/ergora/skill_assets.py#L76)拥有资产读取与比较语义，继续通过 `get` 检查项目归属和内容摘要；实际消费者为 [HTTP 路由](../../src/ergora/web.py#L216)。独立 AST 对比确认其正文与原路由完全一致，仅调整本模块 `get` 名称。没有第二个比较实现，也未新增不在需求中的 CLI 命令或采用路径。
- [窄屏样式](../../src/ergora/data/console/style.css#L585)只为 `.check-row strong` 增加 `overflow-wrap: anywhere`。同数据、同浏览器的原基线与拆分后初稿在 390px 下均为 589px 页面宽度；修复后六页及草稿图检查通过。短标签显示不变，长仓库路径可折行；没有改变资产/执行合同。
- 原纯文本 DOM、请求头、HTTP 错误映射、CSP 和本地同源边界保持；`index.html`、vendor、包配置及依赖无差异。新增 JS 仍由现有静态资源挂载及 setuptools 数据规则提供，无 Node 运行/构建要求或新前端框架。

## 实际检查与证据限度

本 reviewer 执行的低成本只读检查：

- 独立核对清单全部 18 个文件、完整 diff、tracked/untracked 范围及当前 wheel 身份；335 个应用文件在源码、wheel、开发/基础两套非 editable 安装中逐字节相同。
- 独立从基线提取全部 24 个具名函数及 16 个共享箭头定义逐一对比。除元数据从全局变量移到 `app`、显式回调参数/调用、两个生命周期函数和图绘制判断归属外，无正文变化；参数与生命周期差异另经人工检查。
- 12 个模块用 Node 原生 `vm.SourceTextModule` 编译及链接通过，导入无环且无视图导入入口；这是开发期只读检查，不构成产品 Node 依赖。两处变更 Python 的 AST 解析通过。
- Skill diff 与原 HTTP 正文 AST 等价；冻结参考、tests、依赖/打包配置及 CI 的 Git 差异为空；`git diff --check` 与三个变更文档的 100 个本地链接检查通过。

读取并核对实施者已运行的实际入口、断言和结果，没有重复昂贵回归或服务运行：

- 最终 `wheel-regression.log`：Linux **206 passed、18 skipped、36 subtests passed**，176.14s；跳过范围及既有 warning 保留在交付记录。
- `final-base-journey.py/json/log`：无五类可选依赖时，21 次基础 CLI 符合预期，三模板、两个 golden 编译和不可变导出保持。
- `cli-api.py/json/log`：三个同一持久项目的 30 次 CLI 与 HTTP 快照一致，跨项目归档拒绝理由一致，三类同源拒绝均 403。普通 CLI 拒绝码按原合同为 2；初轮脚本设错的历史失败没有混作产品修正。
- `r7-core-final-ui.js` / `browser-core-final.log`、归档复验、`r7-workflow-ui.js` / `browser-workflow-retry.log`、`r7-mobile-ui.js` / `browser-mobile-stable.log`、`r7-research-stable-ui.js` / `browser-research-stable-retry.log` 的实际断言与成功结果相符。延迟通过 `route.fetch()` 取得真实 HTTP 响应后再释放，覆盖模板/dashboard 乱序、保存期间编辑、旧 revision 拒绝、JSON 编辑身份与项目切换；另覆盖 schema 绑定、记忆/纯文本、双方评价/采用、Agent 上下文/归档、资料审阅/取消、项目注册及 390px 六页/图。
- 原漏导入 `outputPanels` 的修正已存在于实际 `overview.js`，归档复验与最终完整旅程均成功。窄屏基线反例和其他脚本失败/修正过程有单独记录。`cleanup.json` 记录两个本切片测试端口已关闭。

这些记录证明确定性本地用例与此次职责移动。真实模型/GPU、浏览器中成功 Forge 响应的晚到行为、外部工单、ReMe/GEPA/Temporal 服务和未配置宿主依赖的空白 Windows/winget 路径未在本切片重验；不能从 fixture 分数推导模型收益。浏览器断言和既有代码一致，不替代未运行能力的验收。

## Findings 与最终远端复核

在上述实际源码、调用者与证据范围内，**无 findings，无需源码修正**。同一 reviewer 于 **2026-11-02 08:13 UTC** 复核最终提交、远端及官方 CI；没有重跑昂贵回归、安装、提交、推送或外部写入。

1. 提交链独立核对为 `c0ad3433f0b507d28e0d4e219a7f1860a64e6367` → 职责移动 [`ad73bec7c7bbdf271e18c90ce01d80e7b7423719`](https://github.com/626619403/Ergora/commit/ad73bec7c7bbdf271e18c90ce01d80e7b7423719) → CSS/初始验收文档 [`b8bee53bdc85a803109a9b8b804aee7408d7a535`](https://github.com/626619403/Ergora/commit/b8bee53bdc85a803109a9b8b804aee7408d7a535)。前者只有 14 个职责移动生产文件，后者的生产变更只有一条 CSS 规则，其余是四个文档；与“先移动、分开修行为”的要求一致。
2. 用初审清单重新计算 15 个生产文件 SHA256，并逐一读取最终提交树比较，全部一致。当前工作区仅有状态文档修改；冻结参考、tests、依赖/包配置和 workflow 相对原基线仍无差异。本地包/浏览器证据继续绑定同一生产内容。
3. 读取 `push-identity.json`，并独立执行只读 `git ls-remote origin refs/heads/refactor/architecture-foundations`：远端完整 SHA 为 `b8bee53bdc85a803109a9b8b804aee7408d7a535`，与受审候选相同。
4. 读取 08:10:35 UTC 保存的完整官方 `ci-run.json`、`ci-jobs.json` 及 `ci-api-status.json`，又独立直接查询 `api.github.com/repos/626619403/Ergora/actions/runs/41410702773` 和 `/jobs`。仓库来源为 `626619403/Ergora`，事件为 `push`，分支为 `refactor/architecture-foundations`，workflow 为 `.github/workflows/portability.yml`。run、两个 job 及 `head_commit.id` 均对应精确候选 `b8bee53bdc85a803109a9b8b804aee7408d7a535`；结果如下，无需借用历史 run。

|官方结果|身份|状态/结论|
|---|---|---|
|[Portability run](https://github.com/626619403/Ergora/actions/runs/41410702773)|`41410702773`，attempt 1|`completed / success`|
|[Ubuntu / Python 3.11](https://github.com/626619403/Ergora/actions/runs/41410702773/job/125162845678)|`125162845678`|`completed / success`|
|[Windows / Python 3.12](https://github.com/626619403/Ergora/actions/runs/41410702773/job/125162845984)|`125162845984`|`completed / success`|

保存的官方 run 原始响应 SHA256 为 `972349427905adcae50db79d0a5c32e6b2845f7af2c18e52c9052654c0677707`；jobs 原始响应为 `ce4dbef476c62e19899e6391ba215dc473a646472fb00144781aee0ddb416191`。早期匿名限流及 in-progress HTML 属于历史过程；最后一次 matrix 页面请求的 SSL EOF 不作为最终成功证据，最终结论来自完整官方 API 响应和本次独立查询。

实际 workflow 在两平台均构建/安装非 editable wheel（含 dev/web/gepa/temporal 可选依赖）、核查随包 reference 身份、执行 `tests` 和冻结合同测试；Linux 另执行 portable、workflow AdapterTests 及 runtime 回归。原始 job 响应确认这些步骤均成功。Windows 还成功运行 PowerShell 5.1 安装/升级检查，实际覆盖首次安装、重复升级、中文/空格路径与外来入口保护；该步骤在 Ubuntu 按条件跳过。已核查 workflow 与 `tests/windows-installation.ps1` 的实际内容，没有把 CI 扩张为真实模型/GPU、外部服务、浏览器晚到 Forge 成功响应或无宿主依赖空白 Windows 安装的验收。

源码、提交分离、生产推送身份及精确两 OS CI 的验收待办均已关闭，可登记 R7 完成。**剩余交付动作**是作者更新计划/交付状态，提交推送本报告及最终状态文档并核对远端 SHA；若只改文档，生产验收身份继续为上述候选。真实未验范围按前节和原交付记录保留，下一实施节点为 R8。
