# S11 / R3.1：集中迁移独立审查

日期：2026-11-02。审查者：独立 fresh-context reviewer（/root/state_migrations_review），未继承实施对话。项目和 docs 根均为 Ergora；按 AGENTS.md、maintainable-project-delivery 及 independent-review brief 审查，只负责 R3.1。

需求符合性：**通过，限 R3.1**。可维护性：**通过**。已检范围无 correctness / maintainability findings，无待修正的阻塞项。R3.2 离线完整备份恢复仍待实现，R3 整体不能据此关闭。

## 身份、原始要求与范围

- 基线：0d86315eb29e45757367b36848417a7c0e71bcd5。
- 候选：4d4d12468725001c94b39120a2966516eadbec56，分支 refactor/architecture-foundations；审查结束时生产代码和测试仍为此提交。
- 完整检查基线至候选的 15 文件 diff：README.md；docs/PLAN.md、USAGE.md、architecture/state-migrations.md、delivery/2026-11-02-storage.md、plans/2026-11-01-all-in-one.md；src/ergora/state.py、drafts.py、evaluation.py、kernel.py、memory.py、optimization.py、research.py、skills.py；tests/test_state_migrations.py。未发现遗漏的未跟踪实现。
- 先读取[原 R3 要求](../plans/2026-11-01-all-in-one.md)、[ADR 0001 状态边界](../architecture/decisions/0001-refactoring-foundations.md)、[A1 存储归属](../architecture/2026-11-01-audit.md)与 [A2 说明](../architecture/2026-11-01-compatibility.md)，并实际读取原 schema.sql、state.json、固定身份和兼容测试，再核对实现、调用者及作者交付记录。
- 审查期间实施者只补了 PLAN、详细计划和 storage 交付记录的状态/证据，并登记 R3.2 下一步边界；已核看这些文档差异，不把未来接口记为已实现。本报告由 reviewer 单独新增。

原 R3 包含集中 16 表 DDL、有序版本、迁移前备份、事务故障/中断回滚、拒绝较新版本、revision 并发、跨进程锁、库与资产恢复核对、ReMe canonical 保持及旧二进制拒写。本次按已经登记的拆分，只验收集中迁移、DB 快照和旧 writer 保护；完整资产清单与离线恢复归 R3.2。

## 需求与所有权核对

[state.py](../../src/ergora/state.py) 第 34–52 行将原 16 表声明集中为当前唯一的 0→1 有序迁移；与独立旧夹具列定义一致，允许旧库缺少尚未 lazy 创建的表。它不复制、解析或重写既有 JSON 行。额外表、索引和触发器保留；未知列布局明确拒绝，不以重建原表完成升级。当前只有一个迁移，未将多版本迁移链的未来运行情况写成已验收。

State 第 96–131 行的初始化文件锁、BEGIN IMMEDIATE 和显式事务分别负责新客户端串行初始化、SQLite writer 排斥及 DDL/user_version 原子提交。备份通过独立只读连接的标准 backup API 获取，integrity_check 和关闭连接后才发布正式文件；失败不进入 DDL。每次连接的版本检查位于第 139–149 行，已存在的 State 也拒绝后续出现的不支持版本。

第 44–48、133–137 行的 48 个触发器及连接函数提供真实的旧 writer 拒写机制，包含返回 NULL 的情形；结论不依赖旧程序检查 user_version。旧版所有已知控制面 DML 均经其 State.connect，没有找到绕开连接策略的生产写库路径。普通读仍可用。文档明确要求先停止旧进程并对账外部工作，且不将该机制称为同用户安全边界或文件/外部作业隔离。

核对了 CLI、Web 的长生命周期 State、research worker、reference_executor，以及 projects/tools 和七个改动领域模块的调用路径。领域改动只移除 lazy DDL；drafts.save 直接验证 project，替代原来为初始化调用 listing。项目、草稿、记忆、Skill 头与研究提案的 BEGIN IMMEDIATE、revision 比较和写入仍在原所有者；研究取消、Forge outcome_unknown、Skill/评价摘要及 ReMe canonical/projection 归属未迁移到 State。

README、USAGE 和[升级说明](../architecture/state-migrations.md)准确区分 DB 快照与完整 home/文件资产备份，说明停服务、原位置恢复及回退丢失快照后变更，不声称代码 revert 等于数据降级。没有实际用户库迁移或 R3.2 恢复实现混入本切片。

可维护性方面，State 已是原连接/初始化所有者，集中迁移不新增一层 repository、ORM 或领域状态机。新增 _schema_v1 是完整私有迁移步骤，_open 共用初始化和普通连接的 writer 注册策略，均有明确资源/一致性职责；无需为复用数量制造跨文件包装。列布局检查、未来版本拒绝、备份临时文件清理与错误路径对应真实持久输入或文件系统失败；没有发现无依据的 fallback、重试或控制流。

## Reviewer 实际检查

Linux Python 3.11.15 / SQLite 3.50.4，使用已有解释器，不安装依赖；所有数据库与故障注入仅写授权的 .ergora/checks/r3-1/reviewer 隔离目录，没有打开实际用户持久库。

- 独立复跑源码迁移套件：**10 passed，6.00s**。命令如下。覆盖新库/完整与部分旧库、额外对象、DELETE/WAL、48 种旧连接 DML、错误 writer/NULL、迁移异常/骤停、备份失败清理、新版本拒绝和两个子进程升级/revision 竞争。首次审查命令因 --basetemp 的父目录不存在而在准备阶段失败；创建审查父目录后上述命令全部通过，不是产品失败。
- 另保持原连接打开并禁用 WAL 自动 checkpoint，确认新增项目行只存在于 **8272 字节 WAL**、主 DB 尚无此行时执行升级；自动 v0 备份和新库都保留了该行的原 JSON 字节，备份完整性通过。
- 从 Git 实际加载并执行 A2 前源码 0027f3f9bf9f03a62afe8710970587b66103f7fe 的原 State。迁移前已打开和迁移后重新打开的旧连接均拒绝写入；定向包含 UPDATE、INSERT OR REPLACE、DELETE，报缺少 ergora_writer_schema_version，旧读取保留。这里执行的是原 State 代码，没有声称安装运行了完整旧发行。
- 补充故障注入：创建全部 guards 并已设置 user_version=1 后 os._exit(24)，重开确认版本回到 0、guards 为 0、原行保留、integrity_check=ok，再次升级成功。
- 最终 wheel SHA-256 实查为 ce75e43e02b42c5181a3fc2700c5ff78af0995fee6bdf13e041a3d34907f5305；wheel 的 **319 个包内文件**与源码逐字节相同，其中包含 23 个应用 Python 文件。独立 source reference verify 为 **283 PASS**，manifest 的 source_zip_sha256 仍为 8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760，runtime 未启动。
- 完整基线到候选 git diff --check 通过。轻量运行与身份结果保存在 .ergora/checks/r3-1/reviewer/runtime-checks.json，CI 元数据在同目录 ci.json；这些是本地检查产物，不是用户运行数据。

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q --tb=short -p no:cacheprovider --basetemp .ergora/checks/r3-1/reviewer/pytest tests/test_state_migrations.py

## CI 与实施者证据的区分

本 reviewer 直接读取 GitHub 公开 run/jobs API，核对 [run 41337468262](https://github.com/626619403/Ergora/actions/runs/41337468262) 的 head_sha 为精确候选，head_branch 为上述分支，状态 completed / success。

|实际核对的 job|完成时间（UTC）|结果|
|---|---|---|
|[Windows / Python 3.12，124940214282](https://github.com/626619403/Ergora/actions/runs/41337468262/job/124940214282)|2026-11-01 18:38:48|completed / success|
|[Ubuntu / Python 3.11，124940214574](https://github.com/626619403/Ergora/actions/runs/41337468262/job/124940214574)|2026-11-01 18:37:21|completed / success|

两 job 的 Build and install wheel、Packaged reference identity、Native application regression 均逐项 completed / success；Windows PowerShell 5.1 installer and upgrade 在 Windows 成功，Ubuntu 按条件 skipped。这是候选真实两 OS 的远端证据，不由本地 Linux 推导 Windows。

实读 .ergora/checks/r3-1/regression-final.log：**182 passed、17 skipped、36 subtests passed、1 既有 warning，82.71s**，与交付记录一致。该全量运行、A2/memory/projects-tools 的 18 passed / 5.20s，以及基础 venv 中五项 optional 缺席时的真实 CLI 升级和未来版本退出检查，属于实施者记录；本 reviewer 没有重复安装或重跑这些完整旅程。CI 元数据核对不冒充逐条重读全部测试日志。

## 结案与保留边界

R3.1 没有未解决 findings 或待补的本切片验收证据。实施者可记录本审查结论并按既有授权完成状态文档的提交/推送；本 reviewer 未改源码或测试、未提交或推送。

R3.2 的库/资产一致清单、完整离线恢复及对应新独立审查仍是 R3 的未完成责任。本结论不覆盖其计划中的接口，也不覆盖真实用户库升级、模型/GPU、真实 ReMe 引擎或 Temporal/其他外部服务的恢复与效果。本切片未改 JS/浏览器行为，未声称重新验收浏览器。
