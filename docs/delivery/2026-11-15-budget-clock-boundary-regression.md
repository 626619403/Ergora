# B3.1 公共时钟架构检查同步

固定产品基线 `b53bba613a3c02b14c69a6df9b0d526755d7e216`。其自身 CI `43660736309` 的 Linux group 1 在 `test_foundations_do_not_depend_on_application_modules[reference_budget-allowed6]` 失败：允许集合仍为空，实际依赖为已提取的 `budget_clock`；原组结果 1 failed／253 passed／6 skipped，不记全通过。官方原件和独立对账见[B3.1 原审查](2026-11-15-training-cycle-authorization-review.md)。

本修正让原边界检查允许 `reference_budget → budget_clock`，并把 `budget_clock` 自身纳入无应用依赖和纯标准库检查。实际 `from . import budget_clock` 的 AST 还包含包名 `ergora`，因此标准库检查按完整包根排除本包；本包内部依赖仍由前一个精确允许集合检查。既有无环／入口／reference 边界断言保持；不放宽其他依赖、不改产品。本地验证使用 B3.1 原非 editable 安装及本次测试快照，后继 B3.2 在途源码不作为该结果的输入。

首轮验证驱动把 venv Python 的符号链接解析成基础解释器，实际未进入 pytest，保留为环境准备失败；第二轮正确使用原 venv，15 passed／1 failed，暴露上述包根误分类。两份原输出保持，最终修正的安装检查、独立审查、普通发布及本修正自己的 CI 待记录。

最终测试快照 SHA256 `c2b9361bf37e7854ddbb1ebaa188a56d6a6f030fd8bdf9dde8dfe01206a0bcb6`，用原 B3.1 r4 SDK 非 editable 安装执行完整边界 suite：16 passed／0.39秒，驱动1.038秒，原件在 ignored `budget-clock-boundary-regression/installed-r3.{json,stdout,stderr,xml}`。该结果不包含 B3.2；独立两轴审查待核。

独立初核接受一项文档finding：共享在途PLAN含不属于本修复候选的B3.2链接。已将本片PLAN从固定b53原文派生，仅追加本片失败／修正段；在途B3.2状态保存在ignored文件，后继片自行携带，避免单独提交后断链。产品和已验测试未变。

[新fresh-context独立审查](2026-11-15-budget-clock-boundary-review.md)固定r2需求／维护均approve，开放0／0；文档finding关闭，独立重算646产品与原提交／wheel相同，并在同原安装重跑固定suite16通过。原官方失败、两轮验证准备／分类失败保持。准备只提交本片测试与记录，不带B3.2产品。
