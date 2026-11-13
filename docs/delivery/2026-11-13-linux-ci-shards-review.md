# Linux CI 分组独立双轴审查

日期：2026-11-13。范围为 [Linux CI 分组计划](../plans/2026-11-13-linux-ci-shards.md) 的本地实现、证据审查及同片发布终核。要求符合性复核通过；维护性审查在所检范围内无 finding。精确候选 `9250bf880c07e13b0aa2af9ba49f612737082a50` 的普通发布与自己的 CI 已终核通过，细节见末节。

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

上传的具体合同为 `always()` 尝试且硬终止不保证，未找到“上传失败不得影响 job”的直接标准，因此未将缺少 `continue-on-error` 列为违规。后续精确 CI 已核远端上传步骤成功；未下载 archive 检查内容。

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
|workflow|原 suite、wheel 安装、reference 核对、Windows PowerShell 5.1 与 native 20 分钟上限保持。`workflow-r1.json` 对应同一 JSON 生成六 Linux＋一 Windows matrix；r4 workflow／分组与 r2 相同。历史六组阶段估计 812.58–812.63 秒只用于预算；后续远端实际耗时见终核。|
|自身结构审查|`self-review-r1-codex.json`：67.247731 秒 approve，六全文 21,629B、prompt／stdin／protocol 25,947B，结果 SHA `d0df2970baca7ae2f5b24f4b32bda259c12e769a92e084e753f52cd9a4066e05`。修正后 `self-review-r2-codex.json`：48.880621 秒 approve，六全文 22,097B、prompt／stdin／protocol 26,663B，结果 SHA `44ef04dba3bf72750be1bf496f8ee65ed34d8d11244a14c68bc5f7c6195136a7`。两轮均核实际输入、三个祖先／自身资源全文及原结果；后轮代码与 r4 相同，计划差异仅实测状态。各 approve 只覆盖自己的聚焦 packet。|

证据表中的验收目录均在本仓库 `.ergora/checks/` 下。本审查只写本报告；其余为只读检查、原件复算及仓库外低成本受控重试，未改产品／测试、安装、提交或发起远端写入。审查者没有重跑完整 suite；collection、局部运行、分段历史和静态检查各保留实际范围。r4 中自身及独立复核的“在途”状态已在 r5 统一结案记账，后续发布／CI 记录也不扩大实现范围。

## 精确发布与 CI 终核

同片协调者于 2026-11-13 离线直接核原 Git 对象、官方 HTML 和请求回执；本节为结案记账，不递归审查报告，也未新增网络请求。

普通提交为 `9250bf880c07e13b0aa2af9ba49f612737082a50`，父提交精确为原基线 `d2dac8d58a57334aa7930ce98856487de065941e`。`review-r5/manifest.json` SHA256 为 `6076cc8241237f649a3f3bab945b3735a872b8d69ced9da4efd55be63d533ea7`；13 个 Git 对象与全部全文快照逐字一致，变更集合恰为这些路径。r4 后只有四份状态文档更新并加入原报告，CI 实现不变，`src`／`tests`／`pyproject.toml` 无差异。`precommit-static-r2.json` 绑定同一 manifest，13 文件／173 本地链接／5 个秘密值检查、issues 0。原未 stage 新文件的 `commit-r1` pathspec 失败保留；显式 stage 后 `commit-r2` 成功。`push-r1` 普通推送 exit 0／6.651743 秒，未使用 force；`ref-r1` exit 0／1.333619 秒，远端分支完整 SHA 相等。

该候选自己的 [Portability run 43402253789](https://github.com/626619403/Ergora/actions/runs/43402253789) 在 `ci-run-html-r3` 原 HTML 为 `Success`，完整提交链接指向上述候选。原 body SHA256 为 `6342eb4f8b3161b47eba39dacb778232bd2a4340c5d3951c63723f44f681ae4a`。直接解析 run 的八个 job 名称／ID 链接，并与原 200 API 的 `head_sha`／`run_id` 绑定核对；再分别检查 plan、六 Linux 的 job HTML r1 及 Windows job HTML r3。九份原 HTML 的 HTTP 200、最终官方 URL、字节数和 SHA256 均与各自回执相符。

全部 30 个必要 `check-step` 均为 `success`，有完成时刻及 `data-job-completed`；全部 30 条日志路径均逐条绑定完整候选 SHA、对应 job ID 和 step number。独立原件解析结果随后与 `ci-html-r3.json` 逐项相符。

|job|ID|必要步骤数|Native application regression|
|---|---|---|---|
|plan|131807719238|1|不适用|
|Linux group 0|131807805734|4|180 秒|
|Linux group 1|131807805784|4|271 秒|
|Linux group 2|131807806080|4|179 秒|
|Linux group 3|131807805715|4|111 秒|
|Linux group 4|131807805713|4|198 秒|
|Linux group 5|131807805737|4|205 秒|
|Windows all|131807805681|5|743 秒|

Windows 回归的原时刻为 09:34:05–09:46:28 UTC，PowerShell 5.1 为 47 秒，上传为 1 秒；其最新原 body SHA256 为 `afa13ecebd09e9c83a40a15d785ddc3bf77b49a8bf9a289fb8030042cdbc819f`。六组 Linux 的上传均成功，耗时 1–2 秒。原 HTML 可见步骤起止跨度为 Linux 128–293 秒、Windows 837 秒；这些是步骤时刻跨度，七个 native job 均在原 20 分钟配置下正常成功终结。未把本地历史成本当作远端计时。

前两次 API 200 原件仍为 `in_progress`／无结论，第三次 403 及 run HTML r1／r2 的 `In progress` 均按原哈希核准并保留；终态依据为 HTML r3 和各 job 原件。没有成功终态 REST、完整日志或 artifact ZIP 下载声明；上传步骤成功不授予未下载内容的额外校验。原 00922 的 Windows 成功／Linux 取消、原九个 research 失败和分段成本范围不改写。硬截止后的上传仍无保证。

至此，本片精确候选的本地实现／验证／独立审查、普通发布／精确 Ref 及自己的必要 CI 均完成。当前报告追加与后续状态说明属于该候选之后的结案记录；下一片通信方向计划不属于本次 CI 候选，也不继承本次验收。

Standards：累计 0，最严重无；Spec：初审 2 项 P3、已关闭 2、开放 0，当前最严重无；本片精确发布及自己的必要 CI 已终核通过。
