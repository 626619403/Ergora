# B3.1 公共时钟架构检查独立审查

日期：2026-11-15。Reviewer：`/root/budget_clock_boundary_audit`，fresh-context 独立上下文。按根目录／tests 的 AGENTS、组件检查协议、`maintainable-project-delivery` 和 `ergora-codebase-quality` 审查。产品只读；本轮仅写本报告及授权的 ignored 核查原件，没有安装、模型、服务、训练、提交、推送或再委派。

**最终本地需求轴：approve，开放 0；可维护性轴：approve，开放 0。** 结论绑定下面的固定 r2 范围；初核唯一文档 finding R1 已关闭。B3.1 原 CI 的失败保留，本修正的固定提交、普通发布和自己的适用 CI 尚待续核，不在本结论内。

固定基线为 `b53bba613a3c02b14c69a6df9b0d526755d7e216`。已逐份读取 ignored `.ergora/checks/budget-clock-boundary-regression/review-scope-r2/` 的完整文件并核长度／SHA256：

|文件|字节|SHA256|
|---|---:|---|
|`tests/test_architecture_boundaries.py`|3794|`c2b9361bf37e7854ddbb1ebaa188a56d6a6f030fd8bdf9dde8dfe01206a0bcb6`|
|`docs/delivery/2026-11-15-budget-clock-boundary-regression.md`|2016|`e06a5486e3b996ce18ae5c97c5dccd85e457fbfcb161dd4f927986c5cf2f3841`|
|`docs/PLAN.md`|52490|`ff9a78b5306fd2641ac53b57cbb6981004c52c219575fccbd88ad9db3aede9af`|

scope JSON SHA256 为 `a3720111652073026c5540e5e72c897eb8ce5a8971e82ca4726bfb79037406e5`；完整 diff 为 5235 字节，SHA256 `a082f439362e210c3bfecc723f059efbacbb323167178ad2f6ac44f88fa6e665`。三文件核查时与工作树相同；其他在途文件不属于本次候选。未跟踪的新交付文档已通过 manifest／完整内容核查，没有只看 tracked diff。

**需求与边界语义。** [原测试](../../tests/test_architecture_boundaries.py)只允许 `reference_budget → budget_clock`，新增 `budget_clock` 的空本地允许集合及纯标准库约束。固定产品 `reference_budget.py:13` 的 `from . import budget_clock` 经原 AST collector 同时生成 `ergora` 和 `ergora.budget_clock`；新外部根分类正确排除本包根，原 `local_dependencies` 仍提取并约束 `budget_clock`。近似名字 `ergora_extra` 仍作为外部根拒绝，不因前缀被放行。

原 import collector、local dependency fixture、无环、应用不得依赖入口、reference 内部边界五个函数的 AST 与基线完全相同；没有删断言、增加跳过或改 CI 选择。直接调用原断言作 11 项内存负例，`budget_clock`／`reference_budget` 越层依赖、第三方库与近似包名、依赖环、应用导入 CLI、clock 导入 reference 内部均被拒绝，未修改安装文件。clock 实际仅导入 `datetime`／`pathlib`／`re`／`sys`／`time`。固定提交中 `reference_budget` 和 `training_cycles` 都有真实 clock 调用；本片没有新增生产接口或改变其职责。

**安装与失败原件。** 独立用原 B3.1 r4 SDK venv 的解释器、`-I -B` 确认实际导入其 `site-packages/ergora`，venv prefix 与基础解释器不同，安装元数据指向非 editable wheel。原 wheel SHA256 为 `c986db854e90bb77c5f4c94ff5ecbc9b72aa526fad9852ae632c61ad2f88bd1d`。实际安装、wheel、manifest 与固定 b53 提交的 646 份完整产品文件逐份字节相同；四产品也同原已审 r4 scope。没有把共享工作树的 B3.2 源码作为安装验证输入。

直接读取原官方 group 1 HTML：172214 字节／SHA256 `1ade5be63145e79dd2b717ae5e2aa9e621565828c9970b63ff9716f77284a5ea`，确认 run `43660736309`／job `132649282883` 的 `reference_budget-allowed6` 空允许集合失败和 `1 failed, 253 passed, 6 skipped`。本轮未重新访问平台或认证整次旧 CI 终态。

|核查原件|实际范围和结果|
|---|---|
|`installed-r1`|venv 符号链接被解析为基础解释器，`No module named pytest`；未进入 pytest，保持环境失败。|
|`installed-r2`|16 项，15 passed／1 failed；XML 0.438 秒，失败仅为把裸包根 `ergora` 当作非标准库。|
|`installed-r3`|最终测试 SHA 同上，16 passed，零失败／错误／跳过；XML 0.389 秒。|
|`reviewer-installed-r1`|reviewer 在同一原安装独立执行完整固定 suite，16 passed，零失败／错误／跳过；pytest 0.39 秒，XML 0.396 秒。|

reviewer 的实际 argv 使用 `-I -B -m pytest -q -p no:cacheprovider`，测试输入为固定 `review-scope-r1/tests/test_architecture_boundaries.py`，与审查快照 r2 测试逐字相同；具体 argv、cwd、退出码及 stdout／stderr／XML 均保存在 ignored `budget-clock-boundary-regression/reviewer-installed-r1.*`。原 installed-r2 输入还可由最终文件仅还原包根 predicate 得到，SHA 与原记录的 `f220710a7f1ea9dc558e10abc1e54dcdbf9ab303b536d9df73ac5f9c1cae33f3` 相同。审查快照 r1→r2 仅改文档，未重复无变化的 suite。

**R1（P2，文档候选完整性）：已关闭。** 初始固定 r1 的 `docs/PLAN.md:9、58` 新增三处 B3.2 plan／delivery 链接，目标既不在 b53 基线也不在本片 manifest，只存在于共享工作树的未跟踪文件。独立提交此片会造成断链，并使恢复工作依赖范围外文件。实施方接受后，r2 PLAN 从 b53 原文派生，仅追加本片 CI 失败／修正段，移走三个跨片新链接；本报告按「基线文件树＋候选文件」核 132 个本地 Markdown 目标，缺失 0。修正未改变测试或产品，R1 关闭，没有其他已证实 finding。

核查索引为 ignored `budget-clock-boundary-regression/reviewer-inspection-r1.json`、`reviewer-evidence-r1.json`、`reviewer-semantics-r1.json`、`reviewer-r2-scope.json`。本轮证明本地静态架构修正与原安装的兼容性；未重跑整个 CI group、Windows／其他 Python 环境或任何业务旅程。后继 B3.2、实际 executor、服务、模型与训练均未验收。下一步应固定本修正提交，逐份核候选身份，再续核其自身发布与适用 CI；不能把原失败或本地 16 项通过转记为该门禁已闭合。

## 固定本地提交续核：尚未发布

已只读核实际普通提交 `b78f7b233316f3248c5a5865d90e6a23870693ac`；唯一 parent 为 `b53bba613a3c02b14c69a6df9b0d526755d7e216`，tree 为 `099d00878d6fba605c83f9e46dbd6f8c757351e4`。实际变化严格为下列四路径，各自长度及 SHA256 均与 ignored `budget-clock-boundary-regression/publication-local-r1.json` 相同：

|路径|字节|实际 Git blob|
|---|---:|---|
|`docs/PLAN.md`|52542|`768c2067175809902d465ddefe23cee75c935d6c`|
|`docs/delivery/2026-11-15-budget-clock-boundary-regression.md`|2378|`b1ef0a53eaa89a73ebfd9c95d05067bdd61c9d59`|
|`docs/delivery/2026-11-15-budget-clock-boundary-review.md`|5985|`aee9df26a364a39ac5c131258684e415c7f1fb27`|
|`tests/test_architecture_boundaries.py`|3794|`cd10545ecc0802669dde772313c78145854b6d75`|

实际完整 commit diff（`--binary --full-index --no-renames`）为 14509 字节，SHA256 `0ec3da5d6f9944ea66360e2011fa87e52d3ab73cf8916c74f11f5dcfa4b2e890`。测试 blob 与固定审查 r2 逐字相同；产品、脚本、CI 和依赖配置对 parent 的 diff 为空。两份实施文档相对 r2 仅记录已发生的独立 approve／finding 关闭及本报告链接，提交中的本报告为原已完成的 5985 字节版本。B3.2 产品或范围外文档没有混入。

按这个固定 commit 的文件树核三份候选 Markdown 中全部 134 个本地链接，缺失 0；其中三个片段链接也逐一匹配该提交目标文档中的标题。没有借共享工作树的未跟踪文件补足链接。`git diff --check` 通过；行为输入未变，未重复 suite、模型或业务运行。原安装 16 项结果仍只对应原固定产品和相同测试，不能替代尚未取得的本修正 CI。

**固定本地提交需求轴 approve／开放 0；可维护性轴 approve／开放 0。** 没有新增 finding，R1 保持关闭。本轮没有联网、平台操作或推送，也不更新原 B3.1 CI 的终态主张；远端完整 Ref、本修正自己的发布和适用 CI 仍待续核。原件为 ignored `budget-clock-boundary-regression/reviewer-publication-local-r1.json`／`.diff`。此次仅追加本报告与授权的 ignored 核查原件；本段不属于上表所核的原提交 blob。

## 普通远端发布与自身 CI：首轮观察

已核原普通 push 的成功记录及完整 SSH Ref：`b78f7b233316f3248c5a5865d90e6a23870693ac refs/heads/refactor/architecture-foundations`。Ref 原 stdout 为 86 字节／SHA256 `312d4646b1d453582037c24e32452239f464a4e92498fcd79dcf28b65e866c71`。2026-11-15 UTC 01:30:36 起独立匿名 GET 官方 GitHub：Ref／commit REST 和 commit／branch HTML 均返回 200，精确 SHA、parent、tree 与上段已审本地对象相同；commit API 的四个实际 blob OID 逐一同本地记录。普通远端身份已确认。

本修正自己的 [Portability run 43663286019](https://github.com/626619403/Ergora/actions/runs/43663286019) 为 run number 227、attempt 1、push，开始于 `2026-11-15T01:29:00Z`，官方 REST 明确绑定完整 b78 SHA 和本分支。UTC 01:31:02 的 REST jobs 与首方 `job_groups_batch?attempt=1&batch=0&size=200` 导航相符：`totalCount=8`／`hasMore=false`，包含 plan、六个 Linux group 和 Windows all；初始只有 plan success，其余七 job 仍 in_progress。此时 CI 门禁尚未闭合，不能记作通过。

本轮证据独立保存在 ignored `budget-clock-boundary-regression/ci/reviewer-publication-r1/`，发布身份索引为 `publication-identity-r1.json`；原请求 URL、时间、响应状态／headers、完整响应 bytes／SHA256 均保留。只读查询本修正自己的 run；原 b53 的 CI 失败没有被改写或用作本次通过依据。后续低频观察其终态，再逐项核适用业务步骤。

## 自身 CI 终态与精确交付结算

UTC `2026-11-15T01:54:27Z` 的完整首方导航已为八 job 全部 success；随后取得的官方 REST run／jobs、run HTML 和 Windows 最终 job HTML 相互一致。run `43663286019`／attempt 1 明确为完整 `b78f7b233316f3248c5a5865d90e6a23870693ac` 的 push，终态 `completed/success`，平台 `updated_at=2026-11-15T01:53:51Z`。导航仍为 `totalCount=8`／`hasMore=false`，没有遗漏 matrix job 或借用其他 run。

|Job|官方 ID|必要业务步骤|终态|
|---|---:|---:|---|
|plan|132657099751|1|success|
|Linux 3.11 group 0|132657127004|4|success|
|Linux 3.11 group 1|132657126989|4|success|
|Linux 3.11 group 2|132657127037|4|success|
|Linux 3.11 group 3|132657127003|4|success|
|Linux 3.11 group 4|132657127042|4|success|
|Linux 3.11 group 5|132657127084|4|success|
|Windows 3.12 all|132657126996|5|success|

必要步骤从固定 b78 的 workflow 和六个显式 Linux 分组推导：plan 的分组读取，七个 native job 各自的 wheel 构建安装、packaged reference identity、原生回归、观察上传，以及 Windows 独有的 PowerShell 5.1 安装升级，共 30 项。每项在各自 job HTML 中恰好出现一次且 success，与 REST steps 逐项一致；八个 job 的最终标题和 `Complete job` 同样已核，所有已有日志 URL 都钉住本片完整 SHA 及各自 job ID。Linux group 1 与 Windows all 的原生回归本次均成功，修复自己的适用 CI 门禁已成立。

UTC `2026-11-15T01:54:57Z` 最后一次官方 Ref／commit REST 和 commit／branch HTML 均为 200；完整 Ref 仍是 `b78f7b233316f3248c5a5865d90e6a23870693ac refs/heads/refactor/architecture-foundations`，parent、tree、四个远端实际 blob 仍逐一同已审本地对象。当前共享工作树和后继本地提交不作为本次远端或 CI 输入。

终核为同目录 `terminal-verification-r1.json`；`terminal-summary-r1.json` 为 78718 字节／SHA256 `5e8470acdd2976f8f6008cea669d4a4f09cba0be0d631049155658fb0140151d`。已逐份重核 49 次官方匿名 GET 的响应原件与捕获 metadata，全部 200，无本轮权限或下载错误；`evidence-index-r1.json` 索引 84 份证据、5029574 字节（不含索引自身），索引为 14870 字节／SHA256 `a60583c5bced85f8249562ef867991414277fdb1e3c0c024753b45b5ebc85071`。终态步骤与身份结论来自这些官方页面／REST，不宣称取得完整 step log、JUnit 或可下载的 CI artifact，也不从页面 success 推算 pytest 项数。

**固定发布及自身 CI 终核：需求轴 approve／开放 0；可维护性轴 approve／开放 0。** 本公共时钟边界修正的精确交付门禁闭合，R1 保持关闭，无新增 finding。此前各次失败、准备错误和中间态保留；本结论不改写 b53 原 CI 的失败，也不认证 B3.2 或其他后继片。整个发布续核只读官方平台与固定产品，仅追加本报告及授权的 ignored 审计原件；未运行模型、服务或训练，未改产品／CI，未作提交、推送或平台写入。
