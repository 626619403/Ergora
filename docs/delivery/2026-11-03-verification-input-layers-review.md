# V1 输入分层独立审查

2026-11-03。审查者：`/root/verification_input_layers_review`，全新上下文，非原成本审查者。先读实际 diff、新文件与相邻调用，再核计划、原成本审计和验证记录；使用 maintainable-project-delivery 的 independent-review 及 review-pr。只写本报告与 `.ergora/checks/verification-input-layers/reviewer/` 小证据，未改源码、测试、CI，未安装、操作用户服务、执行全量或提交推送。

**当前结论：V1 最终独立复核通过，可以收口。** 首审的一项中等验收缺口已关闭；源码需求符合性、可维护性、精确候选两 OS 完整 CI 与实时远端身份均通过，无未解决 finding。最终候选为 `4e01a4e53b9c1d787cf40ce8650d3397cc83b252`；本次没有借用旧 B1 CI。首审身份、发现及修后证据的各自范围保留如下。

## 首审身份

分支 `refactor/architecture-foundations`；基线及审查 HEAD 为 `b55af5d89ff2802ff3afd0125d396f80522942f6`，生产/原测试基线为 `a2349e8c3b183918a68935d5199e7c78509364a4`。实际逐字读取的七文件为：

- `tests/test_task_inputs.py`（新增、未跟踪）。
- `tests/test_task_submission.py`、`tests/test_task_approval.py`、`tests/test_task_cancellation.py`。
- `tests/test_task_export.py`、`tests/test_task_external_status.py`。
- `.github/workflows/portability.yml`。

独立重算七文件 SHA256 均等于 `source-identity.json`；排序紧凑 JSON 的 aggregate 为 `3902d0dad8a44ddcd45a62a1cc7230cba0dbec81e301864f4bf90cdf707fb951`。检查了 tracked diff 与新增文件完整内容，生产/依赖无 diff；实际重算全部 347 个生产资源均匹配原 B1 包清单，保留 wheel 身份为 `52d26ddcd998e1cf94bdb274bb6d3aa4ae1cf62a57d28d8b8bbc84849d6d4051`。没有重建或重新安装相同生产包。

## 首审发现（复审已关闭）

### 中等：真实早期拒绝尚未证明约定的完整副作用不变性

位置：[提交测试](../../tests/test_task_submission.py) `:308`、[批准测试](../../tests/test_task_approval.py) `:164`、[取消测试](../../tests/test_task_cancellation.py) `:165`、[导出测试](../../tests/test_task_export.py) `:189`、[外部查询测试](../../tests/test_task_external_status.py) `:268`。置信度 99。

V1 合同要求每族保留一个真实任务上的早期拒绝，验证文件/journal、租约和 RPC 没有副作用。五个函数的断言 AST 与原基线完全相同：提交只读 `not_recorded`；批准/取消另查没有 signal；导出另查 active 数为 1、没有 export-connect；外部查询只查没有 external-connect。它们没有比较完整运行文件、完整 lease 内容或全部调用；导出的用例名虽写 Git effect，也没有比较真实 refs/HEAD/工作区。

因此“仍无意图/信号”不能揭露额外只读 RPC、其他运行文件写入、lease 其他字段改变或非目标 Git 状态改变。轻量哨兵能保护所覆盖的入口顺序，但不能把这些局部真实断言提升为完整文件/租约/RPC 不变证据。首审没有观测到生产副作用错误；这是明确验收要求未落到断言的测试缺口，当时阻止 V1 完整收口。

最小修正：在各族代表性真实拒绝前后复用已有 `_files` 比较 runtime 字节快照，包含 task/journal、lease 数据库及 SDK fixture 调用日志，在状态查询之前比较；导出再比较实际注册 repo 的 `.git`、工作区和代表性未跟踪用户文件。不新增通用 fixture 框架，不扩展参数矩阵。只需复验受影响拒绝用例，再由同一审查者核修复和新身份。

## 已核实的通过范围

1. **案例语义保持。** 直接用 `git show b55af5d:tests/...` 解析原五函数装饰器，独立比较严格 JSON（区分 bool、int、字符串），并核原 inventory 的逐文件 SHA。原 36 例与新 29 轻量＋12 集成的语义并集严格相等；多出的 5 次是每族的真实代表重复。7 个原 run/Git 语法案例仍集成，陈旧 revision 测试及 CLI/API 严格类型检查没有被移走。正常执行减少 24 次重型初始化，不能由此推导全套耗时比例。
2. **哨兵确实会失败。** 新测试调用实际五个公共 `tasks` 入口，只替换 `_project` / `_native_prepare` 禁止访问边界，未 mock 判定逻辑。独立执行 29 项通过（0.16 秒，87 份计时均小于 5ms）。内存中让五族错误地先访问边界，现有测试全部能揭露；即使回归代码吞掉哨兵异常并抛匹配的 ValueError，`accessed` 断言仍揭露。共 10 个反证通过，没有改生产文件。
3. **fixture 复用有真实消费者。** 新 `submitted_creation` 模板参数由 B1 两模板测试实际消费；函数级 `creation_project` 提供各自 definition，默认治理模板/standard 风险保持。直接读取本次持久 fixture 的两个 `task.spec.json`、server spec、jobs/envelopes：实际分别为治理/standard 与 large-change/high，request/profile 摘要不同且各自严格匹配。它们通过原 preview/create/_start 形成原提交，继续调用真实 `DevelopmentWorkflow.context` 和 FileAdapter 校验；没有另写 B1 判定 oracle。
4. **Git 与证据所有权清楚。** B1 使用原 base SHA 作为合法 candidate，实际两份 fixture 均无 workspaces/bare 候选目录；`_Inspection` 只消费原 outcome、history/context、adapter 文件，没有 Git 候选读取。导出的原 clone/mktree/commit-tree 及两模板真实导出保护仍在。B1 缺历史、错归属、孤立 receipt、坏产物、缺 fence、原结果保持等反例继续存在。
5. **SQLite 关闭成立。** 对实际 `lease()` AST 做独立内存连接探针，函数仍返回 `((None, None), 1)`；保留连接引用后执行查询得到 closed 错误，证明显式 close，不依赖 GC。未放宽文件快照或忽略 WAL/SHM。
6. **CI 只增加诊断。** 实际 YAML diff 仅在同一 pytest argv 加 `--durations=20`；测试路径、Linux 分支、两 OS/Python 矩阵、触发与必需安装步骤保持。V2 提前 skip 和 V3 concurrency 未混入。

## 验证与限制

独立运行 `reviewer/check_scope.py`、`reviewer/runtime_probe.py` 与 `git diff --check`，均退出 0。小证据见 `reviewer/scope-check.json`、`runtime-probe.json`、`pure-inputs.log/xml`；脚本保留可复验实现。前者还直接核了作者 integration XML 的 91 个成功 testcase，其中 B1 48、纯输入 29，与命令/原日志的 **91 passed、297.31 秒、退出 0** 一致；本审查没有重跑这 91 项。

成本原三例 9.26 秒/setup 7.39 秒仍只绑定原审计时点；当前首个 B1 setup 为 6.91 秒。本次只能确认纯输入初始化被消除及无关 bare Git 操作被移除，没有可比全套/B1 总耗时测量，不声称该 fixture 或全套获得某个加速比例。生产未变，本审查未重复无 SDK 基础 CLI 或既有生产旅程。

首审时剩余验收：补强上述五族真实拒绝不变性并定向通过、同切片复审、最终精确候选两 OS 完整 CI。最终 CI 必须绑定新的测试/CI 身份；旧 B1 成功只保留其历史范围。

## 同切片修正复审

独立重读修后 diff、`final-tracked.diff`、计划/交付记录及原 helper。基线/HEAD 仍为 `b55af5d…`；七文件新 aggregate 独立重算为 `b60cd879d9bb7ca0b358ea0490d53c9e45ea88410b3f8e03867931aa736276d1`，逐文件与 `final-source-identity.json` 严格相等。相对首审仅五个既有任务测试文件改变：导入已有 `_files` 并在原五个拒绝函数中增加快照；轻量矩阵、fixture、CI 与生产保持首审内容。实际再核 347 个生产资源均匹配原包清单，`git diff --check` 通过。

五族现均在被拒调用前后比较 runtime 全部文件字节，未排除 SDK fixture，因此 journal、lease 数据库及记录 RPC 的 `calls.jsonl` 一起受保护。比较位于原 status/lease 查询之前，不把后续查询副作用混入入口不变性。导出同时比较实际注册 repo 全树，包括隐藏的 `.git` refs/HEAD/可能的 index，先加入的未跟踪用户文件也在比较内。复用现有 helper 的所有权清楚，没有新增通用包装、额外参数或扩大功能范围。

独立读 `fix-command.json`、`fix.log` 和 `fix.xml`，确认五函数全部 **12 passed、64.78 秒、退出 0**。未把原 91 项改称修后候选结果；它们继续只证明首审身份的范围。再次从原 Git blob 独立比较严格 JSON，原 36 案例与修后 29 轻量＋12 集成的语义并集仍相等。

小探针 `reviewer/recheck_fix.py` 提取实际修后测试函数和实际 `_files` AST，在专用临时文件上替换被拒操作以隔离断言能力：5 个无变化对照均通过；额外 journal、RPC 日志、lease evidence 字段、Git ref、Git HEAD、用户文件和 artifact 共 7 种变化均被新快照断言揭露，且检测先于状态查询。该探针不冒充真实任务集成；真实接线由上述 12 项定向结果证明。脚本退出 0，结果在 `reviewer/fix-recheck.json`，临时文件已清理。

**处置：首审中等 finding 关闭；源码需求符合性与可维护性通过，无新增 finding。** 源码复审时仅剩最终精确 V1 候选的两 OS 完整 CI/提交远端证据复核，当时未标记 V1 完整交付。

## 最终精确 CI / 提交 / 远端复核

2026-11-03 **09:03:04 UTC**，独立脚本 `reviewer/final_ci_review.py` 退出 0，结果保存在 `reviewer/final-ci-remote-review.json`。直接读取官方原始 actions/run/job HTML，重新从 `ci-actions.html` 内嵌 JSON 定位行，而非以作者摘要作为 verdict；记录完整 SHA、工作流、分支和 pushed 事件一致，原选择与已完成 Success 状态均匹配。run 为 [`41605898404`](https://github.com/626619403/Ergora/actions/runs/41605898404)。

|作业|精确 job ID|已独立核实的成功必需步骤|
|---|---|---|
|Ubuntu / Python 3.11|[`125815505886`](https://github.com/626619403/Ergora/actions/runs/41605898404/job/125815505886)|Build and install wheel；Packaged reference identity；Native application regression|
|Windows / Python 3.12|[`125815506254`](https://github.com/626619403/Ergora/actions/runs/41605898404/job/125815506254)|上述三步；Windows PowerShell 5.1 installer and upgrade|

原页面的每个必需步骤均有 success conclusion、job completed 标志、起止时间，log URL 绑定完整 `4e01a4e53b9c1d787cf40ce8650d3397cc83b252` 和各自 job ID；两份 job 页面均为 completed，无失败/取消/超时步骤。重新核了原始 actions、selection、run、两 job 页面摘要，作者状态摘要所列源文件 SHA/字节数也一致。没有把仍在运行的旧页面作为完成证据。

直接读取提交中的工作流，去掉唯一 `--durations=20` 后逐字等于 `b55af5d…` 基线；完整 tests、参考 contract 及 Linux 附加 portable/AdapterTests/runtime 选择、两 OS/Python 矩阵、安装步骤和触发均保持。官方完成步骤足以证明这些门禁通过；本次没有取得详细 console 中的测试计数或 durations 数值，不另报远端性能测量。

提交 `4e01a4e…` 的父提交确为 `b55af5d…`，实际 diff 恰为本次七个测试/CI文件。独立读取七个提交 blob，各自 SHA 与当前文件和 `final-source-identity.json` 三方一致，aggregate 仍为 `b60cd879d9bb7ca0b358ea0490d53c9e45ea88410b3f8e03867931aa736276d1`。生产/依赖无变更，实际 347 资源继续匹配原 B1 包清单，没有重建/安装或复跑本地测试。

独立实时执行 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`，远端 `https://github.com/626619403/Ergora.git` 返回完整 `4e01a4e53b9c1d787cf40ce8650d3397cc83b252`，与已复审、已完成 CI 的候选相同。工作树当前额外内容为项目进度/本报告与 V2/V3 后续合同文档，测试/CI候选没有继续变化。

**最终处置：V1 验收与独立审查完成，无未解决 finding，可在项目计划中收口。** V2/V3 仍按各自切片实施和验收；本结论不提前授予后续代码或完整 F3 功能通过。
