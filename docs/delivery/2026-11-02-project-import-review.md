# F1.3：旧注册导入独立审查

审查日期：2026-11-03。审查者：fresh-context 子代理 `/root/f1_import_review`。本上下文仅接收原始要求、范围、源码基线和证据路径，未继承实现对话。使用 `maintainable-project-delivery` 及其 independent-review 规范、`disciplined-repository-engineering` 及完整 engineering-policy；先读根 `AGENTS.md`、`docs/PLAN.md`、原始 F1 验收和本切片记录。审查者只做源码/证据读取、内存探针及本文写入，未改生产源码、安装、提交或推送。

## 结论

- **需求符合性：当前 tracker 补修的源码及本地包验收复核通过，最终提交/远端与精确 CI 待核。** 容量兼容 P2 及收口补查发现的 tracker 末尾换行 P2 均已修正并独立复核关闭，当前无未解决的源码阻塞。此前 `62c4d69` 的提交、包、回归、两 OS CI 与远端身份已核对，但仅保留其历史范围，不用于证明新 schema；补修后的新包、281 项完整回归及独立 CLI 旅程已有单独证据。
- **结构与维护性：通过。** 项目、注册、reference 文件边界的所有权清楚；导入实际复用原 `_prepare / _reserve / _finish / resume`，未新增持久表、依赖、插件、通用引擎或第二条项目写入链。没有要求额外拆文件或引入抽象的依据。

原始要求见[详细计划 F1](../plans/2026-11-01-all-in-one.md#f1-单一项目及有效配置)及[F1.3 交付记录](2026-11-02-project-import.md)。已审范围包括默认只读预览、JSON Pointer 差异、完整规范化定义及目标控制目录/修订绑定、原字节与投影语义摘要、携带预览摘要的显式采用、旧文件保持、缺失策略/归属记录补建、跨资源中断/恢复以及 CLI/API 共用入口。

## 源码与差异身份

基线/初审时 HEAD 为 `a6fd29162bc066cd8954275032bc103b3f11fc66`，分支 `refactor/architecture-foundations`；F1.3 当时尚未提交。初审工件 `.ergora/checks/f1-import/review.diff` 的 SHA-256 为 `6c7d0580ad0fe89140234f0d1a9516dea1e6be783c7841a2bc83c8418701483f`，`review-files.txt` 为 `9467f48c9e77c9f970b185b6bd684edf9df397b576513583cdc0a3c05fcff003`。容量修正另从实际 Git 差异和文件内容复核，不把初审工件当作修正后的完整身份；最终提交身份见末节。

完整读取变更：`src/ergora/{cli,reference,registrations,web}.py`、`tests/test_registrations.py`、`tests/test_reference_executor.py`、`tests/fixtures/reference_acceptance.py`、`README.md`、`docs/{AGENT_BACKENDS,PLAN,PROJECTS,USAGE}.md`、`docs/architecture/{contracts-and-identities,current}.md`、本切片交付记录及 F1.2 审查记录补记。审查期间又读取原详细计划及 F1.2 交付状态更新；F1.2 最终身份/CI 补记属于前一切片，不计为 F1.3 新实现。

必要邻接包括注册 schema、`projects / contracts / state`、新任务的 `reference_executor` 准入与旧快照分支、Web 公共传输边界、原 `agent_platform.core / projects` 的读写和任务编译、`dev_platform.adapter` 的有界安全读取、`harness.git_scope.validate_policy`、现有架构边界测试及打包配置。

当前所审运行/测试/schema 文件身份（tracker 补修后；此前候选身份在后文区分）：

|文件|SHA-256|
|---|---|
|`src/ergora/registrations.py`|`f5d9a312a1cc951a36153e8a7065826aab0151c14d2122bc1aa9661d34c7b7ed`|
|`src/ergora/reference.py`|`ec926f0c83fed0e737e91a2b60921ce3dde607358aa8cc1cf81fa6b4a6f6ce0e`|
|`src/ergora/cli.py`|`353c1942091884743fb71da69145f643d1d1ec30f992ee7be994f06782ef1f80`|
|`src/ergora/web.py`|`1aadee9d23bbdad1880c9838970a91fbed1e53fc530ca03ceb29e940b0edbc56`|
|`src/ergora/data/schemas/project-registration-v1.json`|`debfd0675db190d79b649c9d9efa7806ed6d0ac8460b8e526ad32f61942b7993`|
|`tests/test_registrations.py`|`9da87fc38a663fc59a1ae2164580b11e426b391bcbaa37a223fb2a2c5eb54aa8`|
|`tests/test_reference_executor.py`|`a2f57588fec47f76d69d6b5f342ade3fedd07da8b7de56c9e5cadb3c29e4b3e7`|
|`tests/fixtures/reference_acceptance.py`|`a543a5f48fed0cf746845073ca43bb8b1f050fa814f670cb83147a1b8ca01be0`|

## Finding 与处置

**P2：已采用文件被不会落盘的重编码长度误拒绝，已修正关闭。** 路径为 `registrations.py:260` → `reference.py:175` 的投影预检。一个满足旧项目 schema、实际 UTF-8 字节不超过 reader 上限的紧凑 JSON，采用时保持原字节，但原预检仍计算 indent=2 的假设输出并限为 1 MiB。审查者只读内存探针得到原文件 **440,358 字节**、假设美化后 **1,210,521 字节**，预览错误为 `Registration file exceeds 1 MiB read limit: projects/demo.json`。这是合法旧配置无法导入的可达场景，不能要求改写原文件或提高 reader 上限来绕过。

最小修正已由实现者落实：仅在 `observed[relative] is None`、确实需要创建文件时计算并限制生成字节；已有文件继续受原 `read_raw` 的 1 MiB 上限、采用源 SHA 和语义冲突检查约束，仍由原不可变 `write` 保持字节。新增 `test_import_adopts_bounded_raw_json_even_when_its_pretty_encoding_is_larger` 检查 preview/apply/resume/status 与字节保持。

已读取实际先失败的 `compact-source-before-fix.log`（上述预览路径失败）和修正后的 `compact-source-fix.log`（新回归及原新建超限拒绝，共 2 passed）；`fixed-registration-regression.log` 的注册/导入及架构边界组合为 58 passed。审查者另对修正版运行四个无文件写入的内存边界探针：有界既有文件通过；相同内容作为缺失文件待新建仍拒绝超限；采用源字节变化仍拒绝；语义冲突仍拒绝。修正没有放宽新建文件、源身份或冲突边界。

## 结构、验证与恢复核对

- `preview_import / apply_import` 的实际生产消费者为 CLI 和 Web；两入口只负责传输与显式采用条件。导入 spec 和旧项目结构从现有注册 schema 属性复用，严格版本及字段校验归注册边界所有。
- `_import_plan` 是同一注册所有者中的共享预检；`_differences` 是其私有 JSON Pointer 算法；`_execution_directories` 集中既有登记与导入的目录规则。这些私有算法有明确本地职责，不需要伪造额外调用者或拆成通用工具。apply 在取文件锁前需要确认输入与锁目录，锁内重做预检保证批准内容仍一致；没有为省一次廉价校验而增加模式参数的必要。
- 预览摘要覆盖目标 `control_home`、expected revision、完整有效绑定/定义、差异、所有源原字节 SHA、adopt/create 意图及投影摘要；随机 operation ID 和 created 时间不参与用户配置批准。apply 在同一用例重新生成预览并比较摘要，reserve 再比较完整 before 文档，避免旧修订覆盖。
- 旧 execution allowlist 先按成员集合校验，再保留原顺序；投影文件摘要仍绑定实际采用的数组顺序。同登记后仅绑定变化时保留已批准 `files`，避免后续普通登记重新制造顺序冲突。严格 UTF-8 拒绝原 runtime 无法读的 BOM/UTF-16，未引入静默编码修复。
- 共享文件锁协调合作的控制面发布者，SQLite reservation 与 finish 再作并发文档比较；来源记录只用于采用文件的原 SHA 复核，旧 F1.2 journal 没有 `source.files` 时沿用原登记语义。恢复继续已保存意图，不接受新导入输入来替换 pending 操作。缺失策略/marker 的幂等补建及逐文件发布仍复用原原语。
- 多文件与 SQLite 不是单个事务。手册要求先停止旧注册写入者；本审查不将“在检查和发布之间仍任意改写文件”的非合作进程当作已隔离，也不把该实现描述为完整文件系统事务。原文件、旧任务目录和运行历史未被迁移；新任务准入继续核对投影，已有任务使用先前冻结的选择。

## 实际检查与证据边界

审查者执行了全部差异/调用链阅读、`git diff --check`、7 份 Python 变更的 AST 解析、上述修正前/后内存探针及冻结 manifest 的 **283 文件**逐一核对。未修改冻结资源。

容量修正前，审查者独立计算预审 wheel SHA-256 为 `5d5eb60011d69f7e544a665208ae736b260c2ef98ea0b5a9fccdd2aee7629db6`，并逐一比较源码、wheel、开发安装和独立基础安装的 **337 文件**，与当时 `package-identity.json` 一致。此包的 `reference.py` SHA 为 `01f6b47c008af900449e4d4b10cfd515bf29aae50b80e70ac6ebac7c89218327`，早于本次容量修正；不能用它证明修正后最终包。

容量修正后、tracker 补修前的 `62c4d69` 候选 wheel SHA-256 为 `6d1ef44aa2d71988e21930cc7908aa5fb6e398bf057106d8907b3e8e79e5319f`。审查者当时再次逐一核对源码、wheel、开发安装和独立基础安装的 **337 文件**，与当时的 `package-identity.json` 一致；其中 `reference.py` 与上表身份相符。该历史包及身份清单现保存于 `.ergora/checks/f1-import/accepted-62c4d69/`。`final-base-journey.log` 记录该候选包的 8 次 CLI 操作通过且 `source_bytes_preserved: true`。

已读实施者运行日志：`targeted-complete.log` 为 72 passed；`wheel-regression.log` 为 278 passed、18 skipped、36 subtests passed。已读 `base-journey.py / base-journey.json`：8 次基础环境 CLI 操作覆盖只读预览、显式采用、状态、幂等恢复、绑定修订和有效配置，删除 PYTHONPATH 后执行，记录旧字节保持。两开发模板的新 fixture 确实经原 register → preview/apply → 保存目录的 CLI 入口 → 六阶段，并验证后续登记不替换旧任务快照。以上长回归/旅程由实现者执行，审查者未重复运行；两项容量回归属于修正后证据。

首次源码审查结束时仍待容量修正包的完整适用回归、精确 F1.3 两 OS CI、提交/远端身份及计划/交付状态同步；其后交付复核见下节。真实模型、GPU、外部服务效果未验证，受控 command/伪 Codex fixture 和历史 F1.2 CI 不替代这些范围。**没有未解决的源码审查 finding。**

## 62c 候选交付复核（历史范围，2026-11-03）

**62c 候选交付复核通过。** 下述结果仅适用于该候选；tracker 补修后的最终交付尚待新证据。实现/测试提交为 [`62c4d696396942fbad86fc21f56f9e854e3ed4d1`](https://github.com/626619403/Ergora/commit/62c4d696396942fbad86fc21f56f9e854e3ed4d1)。审查者独立执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，远端分支输出同一完整 SHA；本地历史也对应此提交。该次复核时源码、测试、CI 与打包配置相对该提交没有工作区差异，仅有阶段/计划/架构状态文档收口。

在该次复核时，逐一将当时 7 份运行/测试文件的 SHA-256 与 `git show 62c4d69:PATH` 及工作树比较，全部一致；其中 `tests/test_registrations.py` 当时为 `bc20cf7a6afd716f1ace5dc540872b042b67995317b8b8f477ac61aba4b7da0e`。另以该提交的 Git 归档计算 **337 份包文件**身份，与当时源码、wheel、开发安装及独立基础安装全部一致。该 wheel SHA-256 再次核实为 `6d1ef44aa2d71988e21930cc7908aa5fb6e398bf057106d8907b3e8e79e5319f`；因此该提交、容量修正版源码与其实际验收安装属于同一身份。

已读 `final-wheel-regression.log` 的最终结果：**279 passed、18 skipped、36 subtests passed**。已核对 `final-base-journey.log` 与 `final-base-journey.json` 一致，均为 **8 次 CLI 操作**且 `source_bytes_preserved: true`；这是容量修正后的最终包证据，不混用预审包的 278 项结果。长回归与旅程仍由实现者执行，审查者作身份与结果复核，没有重复运行。

审查者独立解析 `ci-html-run-selection.json`、`ci-run-latest.html`、两份 `ci-job-*.html`，核对四个来源文件的大小/SHA 与 `ci-html-status.json` 一致；该 manifest 的 SHA-256 为 `e96041d39b012cc2ea84f9df35e06f2465dc386cd1f74b4755f038d8d6bcba99`。选择元数据明确绑定完整候选 SHA、分支与 `.github/workflows/portability.yml`。官方 [CI 41480569812](https://github.com/626619403/Ergora/actions/runs/41480569812) 为 Success；另直接读取官方实时 run 页面及两个 job 页面，得到相同结论：

|Job|平台|实际成功的必需步骤|
|---|---|---|
|[125397456711](https://github.com/626619403/Ergora/actions/runs/41480569812/job/125397456711)|Windows / Python 3.12|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|
|[125397457185](https://github.com/626619403/Ergora/actions/runs/41480569812/job/125397457185)|Ubuntu / Python 3.11|Build and install wheel；Packaged reference identity；Native application regression|

每项上述步骤均为 completed/success，`data-log-url` 均包含完整 `62c4d696396942fbad86fc21f56f9e854e3ed4d1` 及对应 job ID，没有借用相邻提交或历史绿灯。工作流实际命令负责构建/安装 wheel、核对冻结 reference、运行对应平台适用测试；Windows 另运行 PowerShell 5.1 安装升级。此结论基于官方步骤状态及其日志 URL 绑定，未额外下载完整 CI 原始日志。

该次顺带读取 [F1 阶段记录](2026-11-03-f1-completion.md) 和当前架构/reference 边界的状态差异，未见把 F2/F3/F4、训练初始化或真实模型效果写成已完成的明显不实表述。后续发现的 tracker 合同补修改变了 schema，当前交付状态以下节为准。真实模型、GPU、外部服务效果仍未验证，Windows CI 证明该候选适用的原生支持范围，完整六阶段执行范围继续是 Linux/WSL2。

## Tracker 输入合同补修复核（2026-11-03）

**P2：注册接受原执行合同拒绝的末尾 LF，源码修正及本地包验收已复核，最终提交/CI 待补。** 实现者在收口检查中报告该边界，审查者独立复现。`project-registration-v1.json:26` 的原 `tracker.project` pattern 使用 `$`；Python/jsonschema 可在单个末尾 LF 之前匹配结束，因此 `local/demo\n` 能通过新注册的共享 schema 和旧注册导入校验。`_prepare` 的 traversal/GitHub 段数检查不能排除该值。新注册可到 published，旧导入可生成预览，但后续 `create_task` 的原合同校验在 `dev_platform.contracts.py:140` 使用 `re.fullmatch` 报 `Invalid tracker project`，形成已登记却不可执行的配置。

最小修正只在同一 `tracker.project` schema 增加标准 JSON Schema `not: {pattern: "\\s"}`，不剥除输入、不复制校验函数、不改变版本、投影内容、DB 或冻结代码。`_LEGACY_PROJECT_SCHEMA` 复用同一 tracker 属性，注册与旧导入因此在各自已有输入边界一起拒绝。原允许字符本来不含空白，正常标识集合保持不变；这项约束使注册输入与已有执行合同一致。

已读取 `tracker-before-fix.log`：新注册与旧导入的两项 `tracker-newline` 参数化回归均因 DID NOT RAISE 失败；`tracker-fix.log` 同两例为 **2 passed**。测试加入原有公开入口/无落库的回归表，复用既有 fixtures，没有另起测试框架。审查者用 `git show 62c4d69` 的原 schema 确认 LF 被接受，直接调用冻结 `validate_task` 确认其拒绝，再对实际修正版共享 schema 做 **13 个只读内存边界检查**：正常多级/标点标识、300/301 长度、LF/CRLF/tab/空格/Unicode 空白与非 ASCII 输入，结果均与原 fullmatch 词法域一致；也确认注册与 legacy schema 确实复用同一个 tracker 属性。修正后的 JSON/测试 AST 解析及 `git diff --check` 通过。

本次实际源码/测试增量只有共享 schema 与两项参数化测试，上表已更新这两份身份并新增 schema 行；六份其他运行/测试文件保持先前身份。**此补修的需求与维护性在所审源码范围通过，无未解决源码 finding。** 旧 `62c4d69`、`6d1ef44…` 包、279 项及 CI 41480569812 保留其原范围；补修后的本地新包验收见下，新提交/远端及精确两 OS CI 仍须另行核对。

### Tracker 补修包本地验收补核

新 wheel 为 `.ergora/checks/f1-import/dist/ergora-0.2.0-py3-none-any.whl`，审查者独立计算 SHA-256 为 `4fa5adac91721adfd6e274a544336d492800494b82339658d321ff63d0b9dd63`，并逐一核对源码、wheel、开发安装及独立基础安装的 **337 文件**，与新的 `package-identity.json` 一致；当前报告上表 **8 项**身份也逐一匹配。与保留的 62c 包清单比较，包内容仅变更已审的 `data/schemas/project-registration-v1.json`；保留的旧 wheel 实际 SHA 仍为 `6d1ef44…`，没有用新包覆盖历史证据。

已读 `tracker-wheel-regression.log` 完整结果：**281 passed、18 skipped、36 subtests passed**；`tracker-reference-verify.log` 为 **PASS / 283 文件 / runtime_started=false**。这些结果属于 `4fa5adac…` 新包。完整回归由实现者运行，审查者没有重复长测试。

已读新的 `tracker-base-journey.py / .log / .json`，独立工作目录和移除 PYTHONPATH 的环境避免混用前一候选，log 与 JSON 均为 **8 次 CLI 操作**且 `source_bytes_preserved: true`。审查者另以 SQLite `mode=ro` 读取该旅程的最终项目及原恢复意图，核对 published、revision=2、reviewer 变更、4 份投影语义一致；两份采用源文件的当前原字节 SHA 均与批准意图一致，预览 SHA 和最终有效配置 SHA 也与旅程结果吻合。这些检查未写运行状态或重跑 CLI。

**新包本地证据复核通过；本次尚未给出最终交付通过。** 待新实现提交、远端身份及绑定该提交的精确两 OS CI 到齐后，再关闭最终交付；历史 62c 的 279 项和 CI 结论不替代这三项。
