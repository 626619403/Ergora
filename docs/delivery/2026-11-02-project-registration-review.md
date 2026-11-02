# F1.2 统一项目注册：独立结构与维护性审查

日期：2026-11-02。审查者：Codex 独立审查代理 `f1_registration_review`，使用 fresh context；未参与实现。按 `maintainable-project-delivery` 的独立审查 brief、`disciplined-repository-engineering` 及工程政策执行。本次只读源码/证据、进行小型只读检查并写本报告；未修改源码、安装、提交或推送。

## 结论与范围

- **需求符合性：F1.2 修正后在所审范围通过。** 发现的 P2 容量问题已修正并独立复核，无未解决阻塞 finding。修正版最终 wheel 的本地完整回归、文件身份、精确 Windows/Ubuntu 候选 CI 及远端身份均已复核通过，F1.2 交付收尾通过。
- **结构与维护性：通过。** 所有权及依赖方向合理，现有合同/绑定/模板/文件原语得到实际复用；两项小型重复已清理，没有要求新增抽象或扩大重构。
- 本次只验收统一 JSON 定义、角色/执行位置/模板/检查/策略、reference 单向不可变投影、intent/pending/resume、CLI/API 一致性及新任务准入/旧快照兼容。F1.3 旧注册 dry-run/diff/import 不属于本切片，新增 F1.3 计划记录不作为本报告的实现审查对象。

原始依据为 [详细计划 F1](../plans/2026-11-01-all-in-one.md#f1-单一项目及有效配置)、[F1.1 分步边界](2026-11-02-project-configuration.md)、[F1.2 交付记录](2026-11-02-project-registration.md)。基线为 `f11b8ccb59a4073a4e17b35d5c7500105c9d5b29`，分支 `refactor/architecture-foundations`，初审时工作区未提交。最终本地补核时源码已提交为 `a6fd29162bc066cd8954275032bc103b3f11fc66`，与下表运行文件身份一致。初审工件 `.ergora/checks/f1-registration/review.diff` 的 SHA-256 为 `1c6efa1ee06b6ae7d7d636ec5bb24e77ce2be035eb980720e1e716c469655b19`，`review-files.txt` 为 `5f8bb60829ba589e865dc6e704986265c29f587637f927c901d844f6df67411b`；本报告另外复核审查期间的容量修正及两项清理，不将初审 diff 当作修正后的完整身份。

完整审查文件：`src/ergora/{cli,projects,reference,reference_executor,web,registrations}.py`、`src/ergora/data/schemas/project-registration-v1.json`、`tests/test_registrations.py`、`tests/test_reference_executor.py`、`tests/fixtures/reference_acceptance.py`、`README.md`、`docs/{AGENT_BACKENDS,PLAN,USAGE,PROJECTS}.md`、`docs/architecture/{current,reference-boundary}.md`、本切片交付记录。新文件均直接读取。邻接检查包括 `bindings/components/contracts/state/backups`、原 `core/projects/executor/training`、`dev_platform.adapter/contracts`、`harness.git_scope`、原模板/portable tracker 合同及现有架构测试/CI。

## Findings 与处理

### P2 / C1：可发布超过 reader 上限的项目文件（正确性，已关闭）

位置：[reference.py](../../src/ergora/reference.py:171)、[原 reader](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/adapter.py:61)、[注册用例](../../src/ergora/registrations.py:177)。

可达场景：定义中增加 `checks.unused = ["echo", "x" * 1048576]`，仍能通过原 JSON schema/argv 校验且小于 HTTP 4 MB 输入上限。修正前 `core.write` 没有容量上限，注册会返回 `published`；之后 status 对同一文件使用 1 MiB 的 `read_raw` 而报 `File exceeds size limit`。resume 也经过同一 inspect 路径，无法把该发布恢复为可查询的一致状态。实现者实际复现保存在 `.ergora/checks/f1-registration/oversize-reproduction.json`，内容为 published 后 status 超限。

最小修正已采用：在 reference 文件预检处按原 `core.write` 完全相同的 UTF-8、`ensure_ascii=False`、`indent=2`、末尾换行计算每份投影字节数，超过 reader 的 1 MiB 上限即拒绝。该预检由 register 在 `_reserve` 之前调用，保留原 reader 边界，也不留下 pending 控制记录或已发布投影。

复核：已读新增 `test_registration_cannot_publish_files_larger_than_its_reader_limit` 及实现者 `size-limit-fix.log`（2 项通过）。审查者另外只读调用实际 `reference.registration_io(..., files=...)`，把已保存 fixture 项目中的额外 argv 改为内存中的 100000 个 `"x"`，得到 `BLOCKED: Registration file exceeds 1 MiB read limit: projects/demo.json`；未发布文件或改动 DB。源码检查确认修正先于预留事务。**关闭。**

### P3 / M1：同一输入重复 schema 验证及重复导入（维护性，已关闭）

位置：[register](../../src/ergora/registrations.py:169)、[私有准备算法](../../src/ergora/registrations.py:37)、[正式验收 fixture](../../tests/fixtures/reference_acceptance.py:1)。

初版 `register` 先验证输入，随后唯一生产调用的 `_prepare` 又对同一输入进行相同 schema 验证；fixture 同时重复导入 `subprocess`。已保留 register 的外部输入边界并删除私有算法内的重复验证，fixture 只保留一次导入。直接核对当前源码及 AST 解析通过。**关闭。**

## 结构与行为核查

- `registrations` 有 CLI 和 Web 两个真实生产消费者，负责跨 SQLite/文件的完整用例；`projects.new_document` 被轻量创建和完整注册共同使用，Git 根与初始绑定仍归基础项目所有。`projects` 未反向导入 reference。私有准备、预留、完成和 journal 算法分别服务必要的一致性步骤，没有搭建额外注册框架或数据库表。
- 模板角色/必需检查来自 `reference.agent_contract`，绑定仍由 `components.resolve_binding` 与现有 `validate_binding` 校验；正式 command 的 stage-json 协议检查对应可达的不兼容输入。路径及 scope 复用原 `_paths`/`validate_policy`，投影复用 `core.write`，正式执行继续使用原 Executor/FileAdapter/证据链。283 份冻结内容通过独立只读身份校验。
- reference 的登记 I/O 在固定随包代码的独立 `-P -S` 进程运行，项目路径经 `safe_file` 和有界 no-follow reader 检查；当前改动不在 Web 解释器里切换导入时固定的 CONFIG/STATE。安装身份检查仍由 reference 所有。没有新增凭据或平台设置读取入口。
- 同一控制目录锁加配置目录锁覆盖参与该协议的注册发布；SQLite `BEGIN IMMEDIATE` 加前态比较处理 register/bind 的并发修订。完整 intent 在 DB 预留前写入，pending 阻止绑定修改，项目文件最后发布；任意部分发布后可按原意图幂等恢复，冲突不覆盖。最后完成回执失败时，published 项目仍可按原操作补齐回执。此判断针对代码路径与已有进程中断证据，不扩展为机器断电或任意外部写入者的事务保证。
- 新任务在首次冻结前检查 published、Git 根、安装/配置/状态位置、投影及模板；已有 `agent-bindings.json` 继续读原快照。旧配置切换测试在原 CONFIG/STATE 专用执行器里处理在途任务，符合文档边界；没有把自动迁移旧 history 当作已实现能力。
- CLI/API 调用同一个 register/status/resume，用同一版本化定义；strict revision 拒绝 HTTP 类型强制转换。新文档将注册与服务/认证、正式任务界面、训练 runner/基线/实验的责任分开，实际调用链与该范围一致。

## 实际检查与限制

审查者执行：完整变更与邻接调用链阅读；`git diff --check`；对 9 份 Python 变更进行 AST 解析及 1 份新增 schema 的 JSON 解析；`reference.verify()` 核对 283 文件；上述只读容量预检。没有把测试绿灯作为正确性结论，也未重复运行长回归。

已核对初版非 editable wheel `c3d94c6ad8b7419c77ff996da7b1a92de2188cd878ea930e4339b1b311ffa5e0` 的 `wheel-regression.log`（254 passed / 18 skipped / 36 subtests passed）及 `cli-saved-execution.log`（2 项通过），保留其初版身份。最终修正包位于 `.ergora/checks/f1-registration/dist/ergora-0.2.0-py3-none-any.whl`；审查者独立计算其 SHA-256 为 `8c690d6b087e9f293ed5c40adaec3d0347e24d276f939d6832ad695a0e919750`，并逐一核对源码、wheel 和两套安装的 337 份文件，均与 `package-identity.json` 匹配。已读 `final-wheel-regression.log` 末尾的 255 passed / 18 skipped / 36 subtests passed。长回归由实现者执行；上述文件身份由审查者只读复核。本地验收与下附精确 Windows/Ubuntu CI 分别保留各自身份；源码定向、受控六阶段 fixture、取消和旧快照证据按各自实际范围保留，未验证真实模型、外部服务或 GPU。

审查结束时的运行相关文件身份：

|文件|SHA-256|
|---|---|
|`src/ergora/registrations.py`|`06591d54443435a9d6ebc911e15222cdea9445d4eb7214a0a59475c2937aedc9`|
|`src/ergora/data/schemas/project-registration-v1.json`|`225a7414cb381f0f37c60afccf7c76271b6a674b0e38b4700117c0972833400f`|
|`src/ergora/projects.py`|`28c7d15ea79632d2f9a1f2550a97959e9f801aaa10f86deb4fc4f52e50ee1500`|
|`src/ergora/reference.py`|`821facb18f562ef03e4768f277961ba8818c556489f4c05bf5e69e0b86d0b1b5`|
|`src/ergora/reference_executor.py`|`f93a1897901e8197ea190f30e0970aa0d977e7c601785562fe9ad6d681eb460f`|
|`src/ergora/cli.py`|`5cbad4b014f89a9678e2a237f56c0c68d1144a58540083edcf71e75ed7d2dee5`|
|`src/ergora/web.py`|`f6e4c54a65c672756fce31b34a5baab879574ee8fd57eda88e6ab6991ab37d71`|
|`tests/test_registrations.py`|`7fe8913b87d77efd19772d4af5f2d65fc99ba9955e4a45bf242524de72a8c732`|
|`tests/test_reference_executor.py`|`656f138b903053408a76bd00777380188db012867de24836eb3684ae93722cc6`|
|`tests/fixtures/reference_acceptance.py`|`5f46690d992a0a0c302dc7440daaa7b0c608f17f5c91c9722811577db07f19b6`|

最终本地补核还确认详细计划已将 F1.2 更新为已实现，项目手册明确切换配置后旧任务必须保留原 CONFIG/STATE/安装；`--project` 不自动迁移旧任务。报告中 10 份运行/测试文件身份也已逐一与 `git show a6fd291` 复核一致，本地链接和空白检查通过。以上为初审及本地验收记录；最终远端和 CI 复核见下文。F1.3 由另一切片及独立审查处理。**当前无未解决的阻塞 finding。**


## 最终 CI 与交付复核（2026-11-03）

审查者重新只读核对保存的最终 wheel SHA-256 `8c690d6b087e9f293ed5c40adaec3d0347e24d276f939d6832ad695a0e919750`，其 337 份文件均与固定提交 `a6fd29162bc066cd8954275032bc103b3f11fc66` 的内容一致；报告中 10 份源码/测试摘要也逐一与该提交匹配。独立执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，远端返回同一完整 SHA。

已只读解析 `.ergora/checks/f1-registration/` 下的 `ci-html-run-selection.json`、`ci-run-latest.html` 和两份 `ci-job-*.html`，并核对四份源证据的大小/哈希与 `ci-html-status.json` 一致。公开 API 限流后保存的 GitHub 官方 HTML 将 [Portability run 41448910719](https://github.com/626619403/Ergora/actions/runs/41448910719) 关联到上述完整候选，运行状态为 Success；[Ubuntu / Python 3.11 job 125288899157](https://github.com/626619403/Ergora/actions/runs/41448910719/job/125288899157) 和 [Windows / Python 3.12 job 125288899281](https://github.com/626619403/Ergora/actions/runs/41448910719/job/125288899281) 的 Build and install wheel、Packaged reference identity、Native application regression 均为 success，Windows 的 PowerShell 5.1 installer and upgrade 也为 success。逐步骤日志链接包含完整候选 SHA 及对应 job/check ID，步骤已完成，未见 failure/cancelled/timed_out 步骤。

**F1.2 的需求、维护性与最终 CI/交付复核通过，无未解决阻塞 finding。** 本次仅补记原切片交付证据，未审查或修改 F1.3 工作区源码；真实模型、外部服务和 GPU 的未验边界保持原记录。
