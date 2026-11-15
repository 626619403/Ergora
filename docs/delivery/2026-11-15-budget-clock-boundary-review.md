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
