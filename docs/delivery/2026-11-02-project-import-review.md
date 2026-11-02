# F1.3：旧注册导入独立审查

审查日期：2026-11-03。审查者：fresh-context 子代理 `/root/f1_import_review`。本上下文仅接收原始要求、范围、源码基线和证据路径，未继承实现对话。使用 `maintainable-project-delivery` 及其 independent-review 规范、`disciplined-repository-engineering` 及完整 engineering-policy；先读根 `AGENTS.md`、`docs/PLAN.md`、原始 F1 验收和本切片记录。审查者只做源码/证据读取、内存探针及本文写入，未改生产源码、安装、提交或推送。

## 结论

- **需求符合性：修正后所审源码范围通过。** 初审发现一项 P2 容量兼容问题；实现者已作最小修正，审查者独立复核后关闭。当前无未解决的阻塞 finding。修正后最终 wheel 完整验收、精确 F1.3 Windows/Ubuntu CI 和提交/远端身份仍待交付记录确认，本文不把整个 F1.3 或 F1 标为交付完成。
- **结构与维护性：通过。** 项目、注册、reference 文件边界的所有权清楚；导入实际复用原 `_prepare / _reserve / _finish / resume`，未新增持久表、依赖、插件、通用引擎或第二条项目写入链。没有要求额外拆文件或引入抽象的依据。

原始要求见[详细计划 F1](../plans/2026-11-01-all-in-one.md#f1-单一项目及有效配置)及[F1.3 交付记录](2026-11-02-project-import.md)。已审范围包括默认只读预览、JSON Pointer 差异、完整规范化定义及目标控制目录/修订绑定、原字节与投影语义摘要、携带预览摘要的显式采用、旧文件保持、缺失策略/归属记录补建、跨资源中断/恢复以及 CLI/API 共用入口。

## 源码与差异身份

基线/审查时 HEAD 为 `a6fd29162bc066cd8954275032bc103b3f11fc66`，分支 `refactor/architecture-foundations`；F1.3 尚未提交。初审工件 `.ergora/checks/f1-import/review.diff` 的 SHA-256 为 `6c7d0580ad0fe89140234f0d1a9516dea1e6be783c7841a2bc83c8418701483f`，`review-files.txt` 为 `9467f48c9e77c9f970b185b6bd684edf9df397b576513583cdc0a3c05fcff003`。容量修正另从实际 Git 差异和文件内容复核，不把初审工件当作修正后的完整身份。

完整读取变更：`src/ergora/{cli,reference,registrations,web}.py`、`tests/test_registrations.py`、`tests/test_reference_executor.py`、`tests/fixtures/reference_acceptance.py`、`README.md`、`docs/{AGENT_BACKENDS,PLAN,PROJECTS,USAGE}.md`、`docs/architecture/{contracts-and-identities,current}.md`、本切片交付记录及 F1.2 审查记录补记。审查期间又读取原详细计划及 F1.2 交付状态更新；F1.2 最终身份/CI 补记属于前一切片，不计为 F1.3 新实现。

必要邻接包括注册 schema、`projects / contracts / state`、新任务的 `reference_executor` 准入与旧快照分支、Web 公共传输边界、原 `agent_platform.core / projects` 的读写和任务编译、`dev_platform.adapter` 的有界安全读取、`harness.git_scope.validate_policy`、现有架构边界测试及打包配置。

容量修正后已核对的运行/测试文件身份：

|文件|SHA-256|
|---|---|
|`src/ergora/registrations.py`|`f5d9a312a1cc951a36153e8a7065826aab0151c14d2122bc1aa9661d34c7b7ed`|
|`src/ergora/reference.py`|`ec926f0c83fed0e737e91a2b60921ce3dde607358aa8cc1cf81fa6b4a6f6ce0e`|
|`src/ergora/cli.py`|`353c1942091884743fb71da69145f643d1d1ec30f992ee7be994f06782ef1f80`|
|`src/ergora/web.py`|`1aadee9d23bbdad1880c9838970a91fbed1e53fc530ca03ceb29e940b0edbc56`|
|`tests/test_registrations.py`|`bc20cf7a6afd716f1ace5dc540872b042b67995317b8b8f477ac61aba4b7da0e`|
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

修正后最终 wheel 为 `.ergora/checks/f1-import/dist/ergora-0.2.0-py3-none-any.whl`，审查者独立计算 SHA-256 为 `6d1ef44aa2d71988e21930cc7908aa5fb6e398bf057106d8907b3e8e79e5319f`，再次逐一核对源码、wheel、开发安装和独立基础安装的 **337 文件**，与更新的 `package-identity.json` 一致；其中 `reference.py` 与上表修正后身份相符。`final-base-journey.log` 记录修正包的 8 次 CLI 操作通过且 `source_bytes_preserved: true`。

已读实施者运行日志：`targeted-complete.log` 为 72 passed；`wheel-regression.log` 为 278 passed、18 skipped、36 subtests passed。已读 `base-journey.py / base-journey.json`：8 次基础环境 CLI 操作覆盖只读预览、显式采用、状态、幂等恢复、绑定修订和有效配置，删除 PYTHONPATH 后执行，记录旧字节保持。两开发模板的新 fixture 确实经原 register → preview/apply → 保存目录的 CLI 入口 → 六阶段，并验证后续登记不替换旧任务快照。以上长回归/旅程由实现者执行，审查者未重复运行；两项容量回归属于修正后证据。

仍待最终交付补齐：容量修正包的完整适用回归、精确 F1.3 两 OS CI、提交/远端身份及计划/交付状态同步。未验证真实模型、GPU、外部服务效果或本切片的实际 Windows 运行；受控 command/伪 Codex fixture 和历史 F1.2 CI 不替代这些范围。**当前没有未解决的源码审查 finding。**
