# Linux CI 分组独立双轴审查

日期：2026-11-13。范围为 [Linux CI 分组计划](../plans/2026-11-13-linux-ci-shards.md) 的本地实现与证据审查。要求符合性复核通过；维护性审查在所检范围内无 finding。自己的精确发布与远端 CI 仍开放。

协调者为 `linux_ci_slice_review`；Spec、Standards 分别由 `linux_ci_slice_review/spec`、`linux_ci_slice_review/standards` 两个 fresh-context 子审查者独立完成，未继承实现对话。同片修正由原轴复核，下面保留初审 finding，不跨轴合并或排序。采用 code-review 及 maintainable-project-delivery 的 independent-review brief。

## 精确候选与依据

基线和审查时 HEAD 均为 `d2dac8d58a57334aa7930ce98856487de065941e`。`git diff d2dac8d58a57334aa7930ce98856487de065941e...HEAD` 与 `git log d2dac8d58a57334aa7930ce98856487de065941e..HEAD --oneline` 均为空；本片是基线上的未提交工作，实际逐文件比较基线 Git 原件与全文快照，新文件也全部纳入。

|轮次|精确候选|manifest SHA256|
|---|---|---|
|初审|`.ergora/checks/linux-ci-shards/review-r2/manifest.json` 及 `files/`|`fc41721d135803962d084044f2639f4e963f3c450260ae5fa043e42183118c58`|
|修正复核|`.ergora/checks/linux-ci-shards/review-r4/manifest.json` 及 `files/`|`da5b935409bd972e8292d77f4300f5b5a79eb98cbeedd4f955a63d0e71d91b2c`|

每轮均核全部 12 份快照的字节数和 SHA256。r2 首次固定时与当前文件全部一致；随后三份说明的自身审查状态更新单独对照。r4 复核时全部快照与当前文件一致。完整文件范围为：

```text
.github/workflows/portability.yml
README.md
docs/PLAN.md
docs/TESTING.md
docs/plans/2026-11-13-linux-ci-shards.md
docs/delivery/2026-11-13-linux-ci-profile-review.md
docs/delivery/2026-11-13-publication-status.md
docs/delivery/2026-11-13-linux-ci-shards.md
docs/delivery/evidence/2026-11-13-linux-ci-costs.json
scripts/ci/run.py
scripts/ci/pytest_phases.py
scripts/ci/linux-groups.json
```

规范来源为根 `AGENTS.md`、`PLAN` 持续规则、本片计划与 `TESTING`，以及上述 skill 的工程规则。仓库无适用于本片的 `CONTRIBUTING.md`／`CODING_STANDARDS.md`；冻结参考中的模板不是本片规则。原要求包含保留 installed wheel、原 suite／Windows PowerShell 5.1、20 分钟 job 上限、原故障／恢复用例及 283 份冻结参考，并要求完整 collection 后分组和可中断观测。

## Standards

初审 hard 0、judgment 0；r4 同轴复核新增 hard 0、judgment 0，累计 finding 0，最高严重度为无。

已检查 workflow → `run.py:12` → 独立 `python -m pytest` → `pytest_phases.py:18` 的实际调用链及必要邻近源码。runner、pytest 框架钩子和唯一 JSON 的所有权清楚；配置同时供 matrix 与选择使用。重复／漏登记／缺失路径／越界／空选择均对应可达的配置错误，未发现无用防御、冗余新测试或需求外抽象。

完整 Fowler 基线已逐项检查：Mysterious Name、Duplicated Code、Feature Envy、Data Clumps、Primitive Obsession、Repeated Switches、Shotgun Surgery、Divergent Change、Speculative Generality、Message Chains、Middle Man、Refused Bequest。它们均作为判断启发，未当作硬标准；本范围未形成可支持的 smell finding。

r4 的三个外围 wrapper 保留在原观测所有者 `pytest_phases.py:78`、`:83`、`:88`。实际 pytest 提前 skip／xfail 路径支持其必要性，`return (yield)` 透传原返回和异常；没有增加防御分支、抽象或遍历。三个短方法分别实现框架钩子并复用 `emit`，未形成重复代码 finding。wrapper CPU 开销未单独量化。

上传的具体合同为 `always()` 尝试且硬终止不保证，未找到“上传失败不得影响 job”的直接标准，因此未将缺少 `continue-on-error` 列为违规。实际远端上传仍未验收。

## Spec

r2 初审共 2 项 P3、0 项阻塞；未发现需求外扩展或覆盖漏项。r4 同轴复核两项均关闭，新增 0、开放 0。

1. **SP1／P3：阶段起点不完整，已关闭。** 初审 `scripts/ci/pytest_phases.py:78` 的普通 setup hook 晚于 pytest 的提前跳过处理，违反计划第 13 行“即刻写……setup／call／teardown起点”。正式 `selected-r1` 的五个原 setup skip 均无起点。独立冻结夹具还复现 skipif 求值失败时仅有失败报告、求值挂起中断时仅有用例 `start`，影响中断阶段归因而未造成漏执行。最小修正为外围 wrapper。r4 三阶段 wrapper 已实施；正式 `selected-r2` 的 103 份报告均有更早起点，包括五个 setup skip。独立复制原 red 夹具、只替换候选 plugin 后，求值失败仍 exit 1 且正文保留，挂起中断前已有 setup 起点且无 finish，边界修复成立。原 red 四份关键文件哈希保持不变。
2. **SP2／P3：最慢文件声明过时，已关闭。** 初审 `docs/plans/2026-11-13-linux-ci-shards.md:7` 仍称 reconciliation 约 542 秒最慢；根 `AGENTS.md:9` 要求记录实际检查。原 phase 与公开成本均为 export 586.729 秒、reconciliation 542.369 秒，会误导预算阅读。r4 已同步准确的最大值及文件名，与原件复算一致。

独立 Spec 另外以外部新目录复验缺失路径、空选择均 exit 4，并确认完整 collection 为 1,708。原受控 red、green 夹具及运行原件保留在私有审查存储；公开报告用仓库内正式原件定位相同边界，不记录个人机器绝对路径。

## 原件核对及边界

两轴与协调者均以原件核对主要声明；没有把作者自己的 approve 当作独立结论。

|范围|核对结果与原件|
|---|---|
|历史完整成本|`publication-2026-11-13-r1/segmented-cost-r1/summary.json` 所指两份 phase 日志 SHA 相符；从原日志重算 1,463＋233 无交集覆盖原 1,696。剔除未完成 setup 1.104574 秒、去掉 36 个子报告重复后，父阶段合计 4,875.574389396235 秒／75 文件，逐文件与公开投影相等。九个 research 失败及原 cancellation 保留；tail 为 227 passed／6 skipped／36 subtests passed。这是分段覆盖与成本，不是连续 suite 成功。|
|安装身份|`linux-ci-shards/install-r1/` 的 wheel SHA、521 份源码／wheel／安装内容相等、RECORD 529／534 行及非 editable 身份已核；reference 原件为 283 份通过。本片 `src`、`tests`、`pyproject.toml` 相对基线无差异。|
|完整选择|最终 `collect-{all,0..5}-r3/` 均记录完整 1,708，实际分组 254／250／342／312／251／299，并集等于全量、交集 0；每份 plugin 身份匹配 r4。r2 的七份旧 collection 单独保留。|
|运行与观测|旧 `selected-r1` 为 31 passed／5 skipped／57.86 秒；最终 `selected-r2` 同结果／58.00 秒，103 phase 起点齐全。`infrastructure-r4.json` 及原 JSONL 支持提前 skip／xfail、子报告类型、重复／漏登记／越界拒绝、exit 1 完整失败正文和 owner 实际中断；中断无 finish／result，仍为 incomplete。fixture 两脚本逐字等于候选；旧夹具失败不改写。|
|workflow|原 suite、wheel 安装、reference 核对、Windows PowerShell 5.1 与 native 20 分钟上限保持。`workflow-r1.json` 对应同一 JSON 生成六 Linux＋一 Windows matrix；r4 workflow／分组与 r2 相同。历史六组阶段估计 812.58–812.63 秒只用于预算，未证明远端实际耗时。|
|自身结构审查|`self-review-r1-codex.json`：67.247731 秒 approve，六全文 21,629B、prompt／stdin／protocol 25,947B，结果 SHA `d0df2970baca7ae2f5b24f4b32bda259c12e769a92e084e753f52cd9a4066e05`。修正后 `self-review-r2-codex.json`：48.880621 秒 approve，六全文 22,097B、prompt／stdin／protocol 26,663B，结果 SHA `44ef04dba3bf72750be1bf496f8ee65ed34d8d11244a14c68bc5f7c6195136a7`。两轮均核实际输入、三个祖先／自身资源全文及原结果；后轮代码与 r4 相同，计划差异仅实测状态。各 approve 只覆盖自己的聚焦 packet。|

证据表中的验收目录均在本仓库 `.ergora/checks/` 下。本审查只写本报告；其余为只读检查、原件复算及仓库外低成本受控重试，未改产品／测试、安装、提交或发起远端写入。没有重跑完整 suite；collection、局部运行、分段历史和静态检查各保留实际范围。r4 中自身及独立复核的“在途”文字待本报告后统一结案记账，该状态更新不扩大行为验收。

剩余验收为普通提交／推送及精确远端 Ref，随后核该候选自己的 plan、六 Linux／一 Windows 全部必要步骤终态、20 分钟实际预算和上传观察。原 00922 的 Windows 成功／Linux 取消不能替本候选关闭 CI4；硬截止后的上传仍无保证。

Standards：累计 0，最严重无；Spec：初审 2 项 P3、已关闭 2、开放 0，当前最严重无；自己的精确远端 CI 待验收。
