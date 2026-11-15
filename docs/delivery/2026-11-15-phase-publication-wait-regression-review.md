# final 发布故障观察等待：独立审查

日期：2026-11-15。评审者为 fresh-context agent `phase_publication_wait_audit`，未参与实现；先读原始要求和固定差异，再读作者交付叙述。按根、源码、测试 AGENTS、组件变更协议及 maintainable-project-delivery 独立审查 brief、ergora-codebase-quality 测试／结构引用核查。

|范围|需求符合|结构维护|
|---|---|---|
|固定 r1 的本地等待修正|approve；开放 0|approve；开放 0|

本片本地未发现阻塞项。原 `5182bfa` 的 CI 失败及其独立报告保持原结论；本次修正的普通固定发布、远端身份和自己的 CI 尚待同片续核，当前不记完整交付门禁闭合。

## 固定范围

基线为 `5182bfa03f536d4090b91014f97eedda1c5d2d3a`，审查分支为 `refactor/architecture-foundations`。原始要求保存在本片 ignored `raw-requirements.md`，SHA256 为 `0095cd3ebe454cd8fb161cd4b8530893e7b4cff26c3b803c45d85634e8b65ff9`。固定 `candidate-r1/scope.json` 为 1,505B，SHA256 为 `3e2c27185fa754f28c834af257d0e17c9527d754822a1439814f29b1e9bcb1ce`，其七份完整来源均已逐字核对：

- [原测试](../../tests/test_training_submission.py)、[总计划](../PLAN.md)、[本片交付](2026-11-15-phase-publication-wait-regression.md)、[前片交付](2026-11-15-training-budget-phase-supervision.md)。
- 后继 B3.3b 的[计划](../plans/2026-11-15-training-executor-protocol.md)、[交付](2026-11-15-training-executor-protocol.md)和既有[独立设计审查](2026-11-15-training-executor-protocol-plan-review.md)。后三份只按文档身份和交付边界检查；本报告不重新认证后继协议设计或产品。

固定 tracked diff 与首次核对时的基线差异相同。测试全文为 90,335B／`617bc579c432aeafc5c7c9279f3cfc551c13b0fa43e6bf66af279b85436d111b`；对整份测试做 AST 比较，唯一行为差异为该调用的 `seconds=20` 改为 `authorized['total_remaining_seconds'] + 5`。产品、脚本、配置和 CI 相对基线的 diff 为空，未带入 b 产品。

审查中作者另外同步了本片交付、前片交付及 b 计划／交付四份文档的 CI 终态与后继发布条件；已直接对照固定原件读完这些状态差异，未替换 r1 快照，也未改动测试或实验原件。前片 reviewer 自己的报告由其独立维护，本评审未编辑。

## 原失败与修正判断

[原 run 43670140205](https://github.com/626619403/Ergora/actions/runs/43670140205) 的 group 5／job `132678181529` 官方 HTML 为 174,294B／`8823052e5d4daf01df3f3154a530fd7b653a656ac6575b3f61c48544fab51ef3`。已直接核到两个原参数 `final-file-blocked`、`final-directory-blocked` 均报 `Original budget owner did not finish its bounded supervision`，同组为 2 failed／468 passed／13 skipped／1599 deselected，776.01 秒。原 reviewer 的终核记录为八 job 七成功／一失败、30 必要步骤 29 成功／一失败，Windows 与 PowerShell 安装升级成功；其 126 件 CI 原件索引的字节和 SHA 另行全核通过。完整 step 日志仍未取得，本报告不声称知道当次精确进程时间线。

可达误杀原因由源码成立：`wait_budget_stopped` 在观察超时后先对原 owner 发 SIGKILL，再抛上述断言。该测试的 wall 为 24 秒，cleanup 为其中的 14 秒，计算窗口为 10 秒；发布阶段继续使用原总期限。若 submitted 在授权后不足 4 秒返回，后续固定等待 20 秒即可在合法总期限之前杀死 owner。原调用因机器启动速度变化而存在错误的观察上限；已观察到的 CI 断言与这个风险相符。

`training_cycles._status` 的 `total_remaining_seconds` 来自原授权时钟，涵盖剩余清理窗口；授权 fixture 已要求 ready。取该快照再加 5 秒，从稍后的 submitted 返回点开始等待，可覆盖剩余授权及回收余量，且仍有有限观察上限。修正没有续期授权，也没有改变 wall、cleanup、计算窗口或 owner／phase 的停止算法。5 秒是测试观察容差，本次检查不将其解释为产品预算或精确的绝对退出时刻保证。

改动留在已有测试调用处，复用原 helper 和真实状态转换，符合配置优先的测试约束。没有新函数、抽象、测试文件或 CI 分组；不需要扩大所有调用者的默认等待。

## 实际回归与身份核验

已核实际 `installed-regression-r1.json` 的完整 argv、exit 0、XML、stdout 和空 stderr：原最终 r2 SDK 安装使用 `python -I -B -m pytest`，只选原 `test_cycle_final_publication_is_bounded_and_dead_owner_recovers_only_the_same_fence`。结果为 2 passed／67 deselected／65.44 秒，外层 66.446 秒。该运行使用 Linux、Python 3.12.11、Temporal SDK 1.34.0。

|原参数|独立读取的实际证据|
|---|---|
|final-file-blocked|真实 marker 文本匹配；无 final.json；原 owner 已停止，完整 owner stdout 保留，发布观察为 unknown；原 fence SHA 相同，starts 为 1。|
|final-directory-blocked|真实 marker 文本匹配；已有 final.json 与 owner stdout 的原 final 内容一致；原 owner 已停止，发布观察为 unknown；原 fence SHA 相同，starts 为 1。|

已沿原 fixture 核实：替身接管 SDK 服务应答和指定 fsync 故障，原 detached owner、phase supervisor、helper、文件发布和进程停止路径均实际执行。两个 owner stdout 都记录 monitor／fence／cleanup 的停止观察及 publish 的 unknown，原 PID／start_ticks／boot_id 身份现已不存活。公开 submission 对原件字节和同 fence 的保持、`executor_stop_confirmed is None`、resume 仅对账以及唯一次 start 断言均未变，并由本次两个通过的原测试实际检查。这里的 SDK 服务替身不构成真实 Temporal 服务或训练执行验收。

独立逐字核对当前源码、原 r2 wheel、core／SDK 两套安装各 648 个产品文件及两个 RECORD，全部一致；两安装的 direct_url 均指向固定 wheel，未采用 editable。wheel 为 2,048,686B／`56e24e967729304b9abcf2c5cdeb82be5b6619a7b55d9bdefbe5c27407bb03a5`。另外以隔离 SDK 解释器实际导入，确认 Ergora 和预算 owner 来自 site-packages；两安装与当前源码的 283 份 reference 均符合原 manifest。未重建或安装任何包。

`testscope-effective-r1.json` 的 173 份 tracked tests/examples 与工作树、实际运行副本全部逐字相同；选中测试与固定 r1 完整一致。物理冻结的另 2,928 份前端依赖／构建文件没有成为所选 Python 接缝的调用证据。本次没有为这些多余文件扩大运行。

独立便宜检查为 `python -I -B .../reviewer/static-audit-r1.py`，exit 0；结果在本片 ignored reviewer 目录 `static-audit-r1.json`，5,653B／`5eab860c0484dd486f00f8b4d95ba0ecc71564a4a01ca5c4ea37a07d0d1d49c3`，脚本为 11,269B／`41ce0c42b2ef1ee8a075cd0b23bd8ce99f11b3a88874fb242a092acf6cbea22d`。另核受影响 tracked 差异的 `git diff --check` 通过。

## 未验范围与同片接续

本次未重新运行 pytest、完整矩阵、真实服务、模型、训练或 GPU；未修改产品、安装、提交或推送。原 CI 的 Linux Python 3.11 与 Windows 成功项不转授给本次候选，原失败保持。B3.3b 仍只有独立审过的设计文档，实际执行能力、全后代停止和自动循环仍归后继。

下一步固定本片最终 staged 文件与普通提交，核测试／产品字节、完整 diff、远端完整 SHA，再跟踪该固定提交自己的必要 CI；由本评审者在本报告续记结论。只有这项接续 CI 和独立终核闭合后，才能按计划推进后继产品发布。

## 固定发布续核

同一评审者续核普通发布 `75bc99d788a9cef292b7c41eb7e01ac03d13de47`，parent 为原 `5182bfa03f536d4090b91014f97eedda1c5d2d3a`，tree 为 `a66b45a205de85e0d9a9b9ae3f3164aa4d9d28d3`。九份固定文件的 Git blob／字节／SHA 与最终 staged 清单全部一致；测试等于已审 r1，173 份有效输入保持，产品／scripts／配置／CI 的固定提交差异为空。完整 diff-check 通过，173 个文档链接在该 Git tree 中全部存在，含支持的 `:line` 定位；作者初次 checker 的十项误报及修正记录保留，未借此改源文件。

已读实际 commit／push／ref stdout／stderr 及记录：提交时工作树干净，普通 push exit 0／5.906607 秒，SSH 完整分支 Ref 指向上述 SHA。评审者另向首方 commit／ref REST、commit／branch HTML 及九份固定 SHA 的 raw 文件发起只读请求，均为 HTTP 200；完整 SHA、parent、tree、分支 Ref 和全部九份远端原字节与本地固定提交相同。两轴固定发布补核均 approve，开放 0／0；后续 b 工作树不纳入此固定对象。

首方 `head_sha` 查询发现本提交自己的 [Portability run 43672292421](https://github.com/626619403/Ergora/actions/runs/43672292421)，attempt 1；2026-11-15 03:28 UTC 观察仍在运行。完整官方 navigation 返回八个 job、`hasMore=false`，尚待八 job／30 必要步骤终态。原 `5182bfa` 的失败不转记成功，本次也不借用旧 CI。首方原件与逐字核验在本片 ignored `reviewer/ci-publication-r1/`；`official-identity-r1.json` 为 22,045B／`df286cdfbc938a53050830e957c7ab910824d5f09e053ba184fc40afeb2ab530`。

## 自己的 CI 终态与最终结论

2026-11-15 03:50 UTC，同一评审者完成固定 `75bc99d788a9cef292b7c41eb7e01ac03d13de47` 的 Portability #230／run `43672292421`／attempt 1 终核。完整官方 navigation 为八个唯一 job、`hasMore=false`，全部 completed／success；官方 run 页面为 Success，Actions 页的完成状态、完整 commit 链接与该固定 SHA 一致。

|job|官方 ID|必要步骤|
|---|---|---|
|plan|132684778815|1／1 success|
|Linux 3.11 group 0|132684809741|4／4 success|
|Linux 3.11 group 1|132684809759|4／4 success|
|Linux 3.11 group 2|132684809750|4／4 success|
|Linux 3.11 group 3|132684809763|4／4 success|
|Linux 3.11 group 4|132684809734|4／4 success|
|Linux 3.11 group 5|132684809848|4／4 success|
|Windows 3.12 all|132684809793|5／5 success，含 PowerShell 5.1 安装升级|

30 个必要步骤在各 job 原页中均恰好出现一次且全部 success；八个 job 页头与 navigation 结论一致，步骤日志 URL 全部绑定该完整 SHA 和各自 job。group 5 的安装、参考身份、应用回归和观察上传均成功；Windows 应用回归、PowerShell 安装升级与观察上传也成功。本结论依据固定 workflow／分组入口和首方终态，未取得完整 step 日志或下载回归 artifact，不据此补写测试逐项运行时间线或新通过数量。

本次共保存 84 条首方请求记录：81 次 HTTP 200、三次匿名 REST 限流 403；所有已保存响应的原字节／SHA 已重新核对。早期成功的 commit／ref／run REST 核定精确来源和 attempt；终态 run／jobs REST 的 403 原响应保持，终态依据首方 Actions／run HTML、完整 navigation 和八份 job HTML，没有将早期 in-progress REST 冒称终态。

本片 ignored `reviewer/ci-publication-r1/` 的最终证据为：

- `20261115T035002255818Z-terminal-summary-r1.json`：78,708B／`535144d51c88e9ec501b9dbcab5045a8989860e0df19483a64da21a9a3d80aad`。
- `ci-originals-index-r1.json`：139 份原件及检查来源，24,612B／`72666849679ee5006a5d16dc362ab567d68715186cf7c7b959999e9fc8c2e186`。
- `final-ci-audit-r1.json`：16,854B／`ccb58debdd09a62e93bd9d3d74bbb418993222456b59dfd12671ecea4a7c2d2b`。独立终核脚本 exit 0，实际检查范围及每项 job／步骤结论完整保留。

**最终需求 approve／结构维护 approve，开放 0／0。** 本片已审等待修正、九文件普通固定发布、完整远端身份和自己的八 job／30 必要步骤 CI 门禁均闭合。原 `5182bfa` 的失败与原 reviewer 的 R4 历史结论保持，等待缺口由本次独立接续解决；后续工作树及其产品、安装、执行和 CI 仍须各自验收，不继承本结论。
