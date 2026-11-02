# S11 / R8 独立审查

日期：2026-11-02。审查者：Codex `refactoring_exit_review`，新上下文；先读原始 R8 验收、A1 第 6 节和完整原始差异，再对照源码、实际调用者与作者记录。依据项目 AGENTS.md、disciplined-repository-engineering 和 maintainable-project-delivery 的 independent-review brief。仅做只读核查及写本报告；未修改实现、安装、重跑昂贵回归、提交、推送或修改外部状态。

## 范围与身份

初审与修正复审 HEAD / 切片基线均为 `2a18427778ef65172bb5e6130c23876b1e579fd6`，分支 `refactor/architecture-foundations`；生产基线为 `b8bee53bdc85a803109a9b8b804aee7408d7a535`。最终交付候选为 `46ac6330432871d809767a3b11b808c4da129e82`，精确 CI / 远端核对见文末。初审检查了 `.ergora/checks/r8/review.diff` 的完整内容，包括四个新增文件；以下八个输入文件的初审 SHA256 均与 `review-context.json` 一致，修正版身份见文末复审记录：

- `README.md`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`。
- `docs/architecture/current.md`、`docs/architecture/decisions/0001-refactoring-foundations.md`、`docs/architecture/decisions/0002-static-boundaries.md`。
- `docs/delivery/2026-11-02-refactoring-exit.md`、`tests/test_architecture_boundaries.py`。

完整检查新增测试、两份新增架构记录、交付记录与四份跟踪差异，并核对 CLI/Web、agent_runs、bindings、skills/skill_assets/evaluation/optimization、State/backups、reference/reference_executor/stage_driver、前端入口和相邻消费者。原执行器、开发/训练 Protocol、训练排队与手动执行、mini hook、进程与抓取生命周期按相关声明作定向核查，没有重新审计全部冻结代码。

## 结论

**需求符合性：通过，含精确 CI / 远端复核。** 当前架构和 A1 的 13 项结案均有对应记录，旧 API 的别名与实际消费者、退出前提可追溯；未将 F1–F10 或历史浏览器/模型/GPU结果写成本轮实现。初审的 reference 显式导入缺口与 GEPA 所有者描述均已最小修正并独立复核，已检查范围无未解决 findings。最终完整回归、实现提交/推送及精确候选的两 OS CI 已核对；剩余为四份状态/审查文档的收尾提交与推送。

**可维护性：通过。** 使用既有 pytest、AST 和 graphlib 与当前单包规模相称；两个 fixture 属于测试准备，未增加生产框架、包层级、依赖或逐文件全量白名单。五个基础模块限制和入口限制对应实际职责，reference 修正只补充现有命名空间及点分隔匹配；已有公共别名不自带存储/算法，按明确 API 破坏版本和消费者迁移退出，比无依据强删合理。没有发现需要另建抽象、合并状态机或改动生产代码的依据。

## Findings

### P2：reference 边界漏掉随包路径的显式导入（已解决）

位置：[test_architecture_boundaries.py](../../tests/test_architecture_boundaries.py#L57)，核心条件第 60 行；相关声明见 [ADR 0002](../architecture/decisions/0002-static-boundaries.md#约束与失败场景)第 4 项。

测试只在导入名首段为 `agent_platform` / `dev_platform` 时拒绝。冻结 Python 同时存在于 wheel 的 `ergora/data/reference/` 下，可通过 Python namespace package 的完整路径定位。以下任一语句放在 `memory.py` 顶层或函数内时，全部 8 项检查仍通过：

```python
import ergora.data.reference.platform.local.agent_platform.core
from .data.reference.platform.local.agent_platform.core import CONFIG
from ergora.data.reference.platform.upstream.platform.dev_platform.contracts import canonical_sha
```

独立核查使用本次测试文件的原 fixture 和 assertion：只在内存中的 AST 输入附加语句，不执行注入代码、不改源码/安装包。三种语法各作顶层和函数内探针，六个场景均没有失败；同一方法下原始代码的 8 项检查通过，普通 `from . import web`、`import agent_platform.core` 则会被拒绝。`find_spec` 能在实际已安装 wheel 定位上述 core/contracts 文件，故不是不可达的假模块。

这些导入均为普通 `import` / `from`，不属于 ADR 明示排除的动态字符串、importlib 名称或隐式属性访问。它们又因 `ergora.data` 不在顶层模块图内而被依赖图忽略。后续调用者可绕过 reference 的所选安装/配置边界直接取得原 core 全局，静态门禁却保持通过。当前生产代码没有此违规；问题在本次新增的回归保护。

最小修正：在现有 reference 规则中同时识别随包 reference 实现的完整限定路径，覆盖 absolute/relative `ImportFrom` 及 `Import`，无需新增解析框架或递归审计冻结代码。用这类顶层/函数内反例确认拒绝，并保留原四种反例的实际失败证据；同步 ADR 的精确覆盖范围。

复审：原断言增加 `ergora.data.reference` 根，使用 `name == root` 或 `name.startswith(root + ".")`，AST 抽取和原两个边界所有者不变；ADR 第 4 项同步。独立重放上述六个原漏检场景，均由 reference 规则拒绝，未改基线的 8 项检查通过。补核 `from ergora.data import reference` 和 bootstrap 镜像路径也拒绝；相似但不同的 `reference_extra` 等名称不误匹配。修正已覆盖确认的可达缺口，无需扩大生产改动。

### P3：A1 结案表把 GEPA 的当前校验路径写成旧递归实现（已解决）

位置：[current.md](../architecture/current.md#L135) 第 135 行：“GEPA proposer 递归校验保留在 bindings”。

旧基线确实递归调用 `validate_binding("implementer", {"tool": "command", ...})`；当前 [bindings.py](../../src/ergora/bindings.py#L20) 已直接调用 `contracts.validate`，`proposer_argv` 的非空数组/非空字符串/NUL 拒绝由 [components.json](../../src/ergora/data/components.json#L557) 的 GEPA configuration 定义，没有该递归分支。`test_components.py` 保留合法输入及非法 argv 的行为核查。

这不是新发现的 GEPA 行为故障，但会把后续维护者引向不存在的校验分支，也使本轮“当前所有者”记录不准确。最小修正为写明原校验语义由 bindings 调用组件 schema/公共结构校验保留；无需恢复递归或改生产代码。

复审：当前表格已改为“GEPA proposer 参数的原校验语义由 bindings 调用组件 schema 保留”，明确没有遗留递归分支，归属 R1/R2。与当前 bindings/contracts 及 GEPA configuration 相符；历史 A1 审计和生产代码未改。

## 实际检查与证据

- 独立核对八文件 SHA、HEAD/分支及完整差异。相对切片基线和 R7 生产基线，`src`、`pyproject.toml`、`.github/workflows` 均无差异；`git diff --check` 通过。没有生产/依赖/SQLite 格式或 CI 语义变化。
- 从实际源码重建含函数内 import 的图：27 个模块、86 条自有显式边、无环，与 `import-graph.json` 完全一致。Foundation 的五项参数化约束、入口规则对当前结构有效；发现的 reference 漏检已单列，不能由原四个反例覆盖。
- 核对 A1 全 13 项及现有调用者：组件描述、DDL/有序迁移、资产/采用分离、直接 CLI/Web 用例、12 个前端模块、21 对分发镜像、框架继承和平台/运行模式差异均有源码依据。七个 Skill 资产入口及四个 tools 入口为直接别名，生产入口使用实际所有者，测试仍是明确消费者；现有兼容测试检查身份及无 facade 导入。reference 的退出表对安装/任务/训练/工单与 Windows reader 给出了替代、升级、在途恢复或原生平台证据条件，未要求仅为布局删除公共 API。
- 独立逐字节核对源码、本次 wheel、两套非 editable 安装的 335 个应用文件全部一致；两安装的 direct_url 元数据指向 wheel。wheel SHA256 为 `83ffb3a97c06f1eb63b88b996e817adcb9c46fdaab70f7c1e93c367e75f4dc62`。另直接读取 R7 最终 wheel，335 个应用文件也全部相同；当前 7 份文档的 156 个本地文件链接存在。
- 读取 `regression-command.json`、原始 `wheel-regression.log`、包身份、CLI journey、四份反例日志及相应脚本。已保存的 Linux 结果为 **214 passed、18 skipped、36 subtests passed、1 个既有 warning，177.47s**；18 项确为 11 个 Windows、6 个未选择的 Forge/mini SDK、1 个 Temporal。核对了所选 Web/模板/三方向、兼容身份、迁移/旧 writer fence、离线恢复的既有测试所有者。这里接受的是对应已保存运行证据，未宣称由 reviewer 重跑完整回归。
- 基础环境 journey 的 21 次 CLI 记录含三模板复制/角色、两个 golden 编译和转换/验证/不可变导出；两次篡改导出按预期退出 1，其余退出 0。四份隔离反例日志分别在所选边界检查失败，均恰好 1 个失败。新增的六次完整限定名漏检仅在 reviewer 内存中验证，没有执行其导入。

## 剩余验收

P2/P3 已解决并通过同切片复审，已检查范围没有剩余阻断 findings。最终完整回归、实现提交与远端 SHA、精确候选 Ubuntu/Windows CI 均已核对，依据本轮候选和最终状态，没有以历史 CI 替代。实施者仍须收尾提交/推送 PLAN、详细计划、交付记录及本报告四份文档；该记账不改变已验收的生产或测试实现。

浏览器、真实模型/GPU、固定 Forge/mini SDK、外部工单、ReMe/Temporal 服务和空白 Windows 安装没有在本轮重验。生产包与 R7 全相同支持沿用其历史边界说明，不将历史运行改称新验收；无需为本轮测试/文档变化无依据地扩大到这些运行。F1 尚未开始，R8 出口关闭前不进入产品行为变更。

## 同一切片修正复审

2026-11-02，由原独立 reviewer 复核两项修正；未引入实施会话。完整读取并比较 `review.diff` 与 `review-fixed.diff`，差异仅为上述测试/ADR/当前架构修正及计划/交付状态记录，八文件 SHA256 全部吻合 `review-fixed-context.json`。修正版完整差异 SHA256 为 `8dc1df9061ec7b3fe77ad4390601c7ccfc9f5fafabb2654f61b4610b79b485f5`；最终测试文件 SHA256 为 `de2d71626793076fd63292cbfe4df82bd5b6640bc2b00e5cb72a8d0953cbf762`。HEAD 和生产基线不变，相对两基线的生产/依赖/CI 差异仍为空，空白检查通过。

复审读取 `final-boundary-probes.py`、JSON、汇总日志及全部十份 `*-final-rejected.log`：保留原四个反例，新增三种完整限定名语法各顶层/函数内，共十次；实际退出码均为 1，均在目标检查恰好 1 个失败。脚本只复制顶层包文件并供 AST 读取，未执行注入导入。reviewer 又独立以内存 AST 输入运行最终原 fixture/断言，得到上文 P2 的基线、六个拒绝和附加语法结果，避免仅依据作者汇总下结论。

复审期间最终回归完成，已直接读取完整 `final-wheel-regression.log` 和 `final-regression-command.json`：**214 passed、18 skipped、36 subtests passed、1 个既有 warning，181.87s**。与初轮相比仅 `--basetemp` 改为独立最终目录，解释器、测试集合和环境相同；18 项跳过及 warning 的范围相同。最终日志 SHA256 为 `98b2abcd1bdfbbcbdbbb57ff19c6c5f8350f8bce8c4f0299ae52ae4e36550bba`；此时核对八个修正版输入身份仍全部吻合，未改最终测试实现。首轮结果继续保留原身份，没有覆盖成最终结果。

随后作者在 PLAN、详细计划登记表和交付记录补录最终 181.87s 结果，三文件的状态 SHA 已变化；已检查这些更新与原始日志一致，仍明确复审/提交/CI 状态。README、当前架构、两份 ADR 和最终测试的五个实现输入保持修正版 SHA 不变，未发生新的行为或架构变更。

本次修正复审结论为两项已解决，需求范围与可维护性审查通过，无新增 findings。复审当时待核对的提交、推送、远端 SHA 及精确两 OS CI 已由下述最终核对关闭。

## 精确 CI 与远端最终核对

2026-11-02，同一 reviewer 只读核对最终实现提交 **`46ac6330432871d809767a3b11b808c4da129e82`**。直接执行 `git ls-remote origin refs/heads/refactor/architecture-foundations` 返回相同完整 SHA，与本地 HEAD 一致。逐一读取该提交中的 README、当前架构、两份 ADR 和最终测试，五文件 SHA256 均与修正复审输入一致；最终测试仍为 `de2d71626793076fd63292cbfe4df82bd5b6640bc2b00e5cb72a8d0953cbf762`。相对该候选的 `src / tests / README.md / pyproject.toml / .github/workflows` 无差异；相对 R7 的生产/依赖/CI 差异仍为空。此时本地候选后仅 PLAN、详细计划和 R8 交付记录三份状态文档变化，本报告由本次核对继续更新。

独立解析 `.ergora/checks/r8/ci-actions-page.html` 的原始内嵌 JSON，定位唯一 run `41421965020`，其 `description.linkUrl` 包含上述完整候选 SHA，分支为 `refs/heads/refactor/architecture-foundations`、workflow 为 `.github/workflows/portability.yml`，最终状态为 `WORKFLOW_RUN_STATUS_COMPLETED / WORKFLOW_RUN_CONCLUSION_SUCCESS`。逐段解析 `ci-matrix-page.html` 的两个 `streaming-graph-job`，将每行自身的 job URL、平台名、`data-concluded=true` 和 `completed successfully: ` aria-label 关联核对：

|精确运行|平台 / Python|作业|已核对最终状态|
|---|---|---|---|
|[41421965020](https://github.com/626619403/Ergora/actions/runs/41421965020)|ubuntu-latest / 3.11|[125199372145](https://github.com/626619403/Ergora/actions/runs/41421965020/job/125199372145)|completed successfully|
|同一运行|windows-latest / 3.12|[125199372476](https://github.com/626619403/Ergora/actions/runs/41421965020/job/125199372476)|completed successfully|

保存的最终官方 Actions、run、展开矩阵 HTML 的 SHA256 分别为 `ec81e7740b2c9f65014aa37364412bfc4dc0febb680c451e72fb68529d3ad937`、`64210a22f0e997bade62fb0f8901bce37f4ae3db6fdf9fe4a979087c2a50f616`、`848aa9eb30706b7bbf94365449918a9319914444337e557be11f1a57c6c2a14c`；独立计算与 `final-ci-checks.json` 一致，`ci-html-status.json` 的身份也一致。核查依据为 09:39:46 UTC 保存的最终页面，未用 `initial-ci-*` 的 running 状态下最终结论。

reviewer 在 **09:43:33–34 UTC** 再直接读取官方 Actions 与该 run 页面，均返回 HTTP 200：Actions 内嵌数据再次确认相同完整候选和 completed/success，run 页面含相同完整 commit 链接。本次实时展开矩阵端点返回 HTTP 404，故两个作业的逐行状态依据上述已核验保存页面；没有声称取得实时矩阵、逐项 Windows 日志或其测试数量。没有依赖匿名 API 配额或额外认证。

已对照实际 workflow：两平台先构建并非 editable 安装 wheel、核对参考包身份，再执行 `tests`；Linux 追加冻结参考的相关集合，Windows 配置另有原生 PowerShell 安装/升级步骤。本次新增架构检查处于该实际 `tests` 路径，没有独立旁路 CI。最终核对通过，范围内无新增 findings；四份状态/审查文档收尾后可按原计划进入 F1，不扩大本次模型、GPU、浏览器或 SDK 的验证声明。
