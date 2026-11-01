# S11 / R3.2：离线完整备份恢复独立审查

日期：2026-11-02。审查者：fresh-context reviewer（`/root/state_backups_review`），未继承实施对话，未委派。项目与 docs 根均为 Ergora；遵循 AGENTS.md、maintainable-project-delivery 及 independent-review brief，仅审查 R3.2。

需求符合性：**通过，限 R3.2**。可维护性：**通过**。已检查范围内无 correctness / maintainability findings，无未解决阻塞项；精确候选的两 OS CI 已独立核实成功。R3.1 的既有审查和本报告共同提供 R3 的验收依据，实施者仍需收口计划、交付记录并提交推送。

## 身份、要求与检查范围

- 基线：`fd4be15e81a2656f66c6db84862424fe362b24b2`。
- 候选：`4fe2ec5133a9d055b35debf376e21d09d3df4ec9`，分支 `refactor/architecture-foundations`；开始时工作区干净，无遗漏的未跟踪实现。
- 完整检查基线到候选的 13 文件差异：docs/PLAN.md、USAGE.md、WINDOWS.md、architecture/contracts-and-identities.md、architecture/state-migrations.md、delivery/2026-11-02-storage.md、plans/2026-11-01-all-in-one.md；src/ergora/backups.py、cli.py、contracts.py、state.py、data/schemas/state-backup-v1.json；tests/test_state_backups.py。
- 先读基线中的[原 R3 验收](../plans/2026-11-01-all-in-one.md)、[ADR 0001](../architecture/decisions/0001-refactoring-foundations.md)、A2 的 schema.sql / state.json / identities.json 与兼容测试，以及 [R3.1 审查](2026-11-02-state-migrations-review.md)，再看完整生产/测试差异及相关调用者，最后核对作者交付叙述与当前 PLAN。

原 R3 包含有序迁移、迁移/恢复故障、较新版本拒绝、revision 与跨进程锁、库/文件核对、ReMe canonical 保持及旧二进制拒写。按已登记拆分，R3.1 已验收集中迁移、自动 DB-only 快照和旧 writer 保护；R3.2 本次负责真实 CLI 维护入口、升级前 schema 0 备份、完整离线库与本地资产核对及同平台原 home 恢复。未把邻接 R4/R5/R6 或外部服务恢复纳入实现范围。

## 需求与可维护性核对

[CLI](../../src/ergora/cli.py) 的 state 分支直接调用 backups，用 [State 共用的 resolve_home](../../src/ergora/state.py) 解析位置，未实例化 State，因而不会为维护命令创建新库或先升级旧库。backup / restore 同时在参数和用例边界要求显式 offline。普通项目等入口的初始化、revision 事务及旧 writer 机制未被改写。

[backups](../../src/ergora/backups.py) 在初始化锁和 SQLite 写锁内通过标准 backup API 取得数据库快照，包括 WAL 已提交数据；控制面 sidecar 和初始化锁文件按明确规则排除。其他普通文件和空目录进入清单，文件记录实际字节 SHA、大小及模式。源文件复制前后清单、复制内容及完整暂存备份分别核对，失败不发布正式目标。目录下降前拒绝符号链接、Windows reparse point 和特殊文件；清单中的绝对/驱动器/父级等不安全相对路径拒绝。

verify 同时验证 R2 严格清单 schema、平台、文件/目录清单、SQLite 完整性和数据库版本；Skill 复用现有 digest_tree（含执行位），来源原文 SHA 与 source_snapshots 对照。restore 先验证，再复制到目标父目录暂存区并重验同一清单身份，完成后发布到不存在的原 home。它不重定位旧绝对路径、不重编码持久 JSON、不改变旧证据摘要，也没有自动重提任务的调用路径。

backups 是凝聚的维护用例所有者。create / info / verify / restore 的实际外部消费者是 CLI，verify 也被创建及恢复流程复用；独立所有权符合本切片已要求的传输/用例边界，并非为假设消费者增加接口。私有路径、目录清单和数据库上下文函数各有实际调用及资源/输入校验职责；未发现需删除的单用代理、重复领域编排、无依据 fallback 或无关参数检查。resolve_home 在 CLI 与 State 两个生产文件实际复用；schema 延续 contracts 的结构配置职责。标准库 sqlite3 / shutil / tempfile / hashlib 和现有 Skill / R2 校验已满足需要，没有引入新依赖、ORM 或通用 repository。

手册准确要求停止写入及外部工作，区分自动迁移 DB 快照与完整离线备份，明确同平台原位置、现有 home 先保留、外部路径/服务另行恢复与对账、ReMe 显式 rebuild。它们未把本地文件清单声称为在线跨文件事务或业务仓库、reference、Temporal、MLflow、远端 ReMe 的联合恢复。

## Reviewer 独立实查

Linux Python 3.11.15 / SQLite 3.50.4；复用已有解释器，无安装。所有合成数据库、故障检查和输出仅位于 `.ergora/checks/r3-2/reviewer/`，没有打开实际用户 home 或运行数据。

- 独立复跑源码备份与迁移套件：**30 passed、1 skipped，20.31s**。跳过项是仅 Windows 的真实 junction 检查，本地未模拟其通过。命令如下；覆盖正常往返、旧 WAL、清单与领域身份反例、源文件变化、复制/恢复暂存故障、链接、CLI，以及 R3.1 的故障、版本和锁保护。
- 独立由 A2 固定 schema/数据构建 **16 表、17 行的 schema 0**，不经当前 State 生成旧库。真实 CLI info / backup / verify-backup / restore 后仍为版本 0；全部原 SQL 行（含原 JSON 序列化字节）、Skill 与来源文件/模式、记忆及 mirror、cancelled / outcome_unknown 状态保持。原 home 移走后校验不创建 home，恢复清单 SHA 不变，普通 State 打开后才升级至 1，升级后上述全部原行仍相同。另核对未知普通二进制文件和 Unicode 空目录。
- 独立补查 FIFO、数据库本身的符号链接及实际 user_version=2：均按边界拒绝，失败备份未发布；info 对较新版本报告 unsupported。
- 实查最终 wheel SHA-256 为 `ba3fa2e760ef4d138a15462d53cd20b009d0eb9eb5f466a2cb95c1f882620b3b`，其 **321 个包内文件**逐字节等于候选源码，其中 **24 个应用 Python 文件**。这是 wheel 与源码核对，不冒充重新安装验证。
- 独立 source reference verify 为 **283 PASS**，source_zip_sha256 保持 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，runtime 未启动；完整候选 diff --check 通过。

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider --basetemp .ergora/checks/r3-2/reviewer/pytest tests/test_state_backups.py tests/test_state_migrations.py

补充检查脚本和结果为同目录的 `independent_checks.py`、`independent-checks.json`；它们只包含合成数据与公开包身份，不是产品源码或实际用户数据。

## CI 与实施者证据

Reviewer 直接读取公开 GitHub run/jobs API，核实 [CI 41340075293](https://github.com/626619403/Ergora/actions/runs/41340075293) 的 head_sha 为精确候选、head_branch 为上述分支，状态 **completed / success**。过滤元数据保存在 reviewer/ci.json。

|独立核对的 job|完成时间（UTC）|结果|
|---|---|---|
|[Ubuntu / Python 3.11，124948012555](https://github.com/626619403/Ergora/actions/runs/41340075293/job/124948012555)|2026-11-01 19:08:18|completed / success|
|[Windows / Python 3.12，124948012651](https://github.com/626619403/Ergora/actions/runs/41340075293/job/124948012651)|2026-11-01 19:10:10|completed / success|

两 job 的 Build and install wheel、Packaged reference identity、Native application regression 均逐项成功；Windows PowerShell 5.1 installer and upgrade 在 Windows 成功、Ubuntu 按条件跳过。已读取工作流及 junction 测试，Windows 的 native suite 包含该真实路径；本 reviewer 核对的是候选真实 OS 的成功步骤元数据，未声称逐条下载重读远端测试日志。

实读 `.ergora/checks/r3-2/regression-final.log`：**202 passed、18 skipped、36 subtests passed、1 既有 warning，86.45s**。该最终 wheel 全量运行和基础 venv 在五项 optional 均缺席时的 CLI 旅程属于实施者证据，本 reviewer 没有重新安装或重跑完整全量。此前 202 / 17 skip 是 junction 补查之前的历史运行，未用于替代最终日志。

## 结案边界

R3.2 无未解决 findings 或待补的本切片验收证据。实施者可据此更新 R3 状态并按用户已有授权完成文档提交、推送；reviewer 仅新增本报告及授权隔离检查产物，未改源码/测试，未安装、提交或推送。

本结论不覆盖实际用户库恢复、真实模型/GPU、浏览器重验或外部仓库、evaluator、reference / Temporal / MLflow / 远端 ReMe 的恢复效果。恢复是离线、同平台、原 home 的明确合同；跨位置/跨 OS 迁移和外部在途任务对账仍保留其原责任。
