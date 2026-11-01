# S11 / A1 独立审查

日期：2026-11-01。审查者：Codex 独立 reviewer `audit_review`，使用新上下文；输入为原始需求、A1 边界、精确基线、完整变更清单和实际检查记录，没有实施会话。按仓库 AGENTS.md 与 maintainable-project-delivery 的 independent-review 执行。权限仅为只读检查及写本报告；未安装、改生产代码、提交、推送或修改外部状态。

## 范围与身份

审计来源为 `0027f3f9bf9f03a62afe8710970587b66103f7fe`。审查期间 HEAD 因独立 M2 文档记账前进至 `33ed20072aa9ec870c17cf50b38284bc8f8f60a9`，父提交仍为上述基线；两者 `src` 树均为 `3df37c618814fe4b7b41b17bf49cb915ede42e32`。本报告不替代 M2 审查。

完整检查了 A1 的三份已跟踪改动和三份新增产物（包括全部 JSON 索引记录）：

- [PLAN](../PLAN.md)、[详细计划](../plans/2026-11-01-all-in-one.md)、[原架构基线](../architecture/2026-11-01-baseline.md)。
- [审计正文](../architecture/2026-11-01-audit.md)、[日期源码索引](../architecture/2026-11-01-source-index.json)、[交付记录](2026-11-01-audit.md)。

人工核对了自有模块的所有权、CLI/Web 相邻消费者，以及五条流程涉及的 SDK、reference 编译/准入、Temporal workflow/activity、adapter、executor、部署和进程监控代码；另查前端 API 使用与安装/报告生成对镜像的实际消费。701 个定义的索引逐条验证不等于逐个函数的运行语义验收。

## 结论

- **需求符合性：通过，原 P2 已修正并复核。** 五条基线流程已对应实际入口与函数；正式任务、部署及取消恢复另有序列；不可达 tools 分支、Skill/evaluation 职责环、摘要差异、进程差异和分发镜像均有源码依据。计划、审计和交付记录区分现状、建议和未验证项；本轮交付仅为 A1 文档审计。
- **可维护性：通过。** 建议限定在完整用例、组件描述、DDL/升级及前端现有责任；保留已有 CLI/Web 复用、领域事务、Protocol、外部框架 hook、平台/执行模式差异和冻结镜像，没有用虚构消费者或新增基类凑抽象。后续 R/F 节点仍须各自实现、验证与审查。

已检查范围内无未解决 findings；没有阻断 A1 收口的审查事项。提交、推送与计划状态收口仍由实现者完成，未由本审查执行。

## Finding 与复核

**P2，已解决：训练图遗漏人工执行入口。** 初版审计正文第 116–119 行把 `training.prepare → ExperimentWorkflow.run → LocalTrainingAdapter → training_executor.process` 连为连续流程；原架构图也直接由 prepare 指向 runner。可达场景是操作者完成 prepare、worker-start 和 start 后等待训练自动执行：实际上 [prepare](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L73) 返回 `started=False`，[create_job_if_absent](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L123) 仅写 request；[run-local 分支](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L244) 才在确认精确 manifest SHA 后调用 executor。[worker-start](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L237) 明示 `automatic_training_execution=False`，[服务命令表](../../src/ergora/data/reference/platform/local/agent_platform/service.py#L13) 也无自动训练 executor。遗漏会使 F9 误判已有执行能力及迁移责任，或让实际实验一直停留 QUEUED。

最小修复是补出显式 start、queued request/result 文件边界、操作者 run-local 及 SHA 确认，并同步原基线图。实现者已完成：[审计图及正文](../architecture/2026-11-01-audit.md#3-五条基线流程对应到函数)第 112 行起明列两个控制/执行入口和结果回读，[原基线](../architecture/2026-11-01-baseline.md#35-kernel-候选与正式训练)第 164 行起也明确手动执行。已重新对照上述源码及 `training_executor.process`、`ExperimentWorkflow.run`、setup/service 核对，修复充分；无需扩展为本轮生产改动。

## 实际检查与限制

本审查实际执行并通过：

- 独立 Python AST 遍历全部 113 文件，核对原始 SHA、701 定义的名称/范围/async/decorators、全部作用域 imports 和 9,267 条 callee 记录、分组统计及 13,304 行；30 显式路由与 decorators 一致。模块 scope 的 `<module>` 表记已按索引规范核对。
- 全部 21 组镜像逐字节相同；同时读安装器从 bootstrap/local 复制的代码及报告生成维护两个前缀的代码，确认保留理由。
- 只读导入核对非 Agent CATALOG 不含 codex/claude-code/command，GEPA 委派对合法 argv 接受、空 argv 拒绝；结合全部生产调用者搜索确认删除范围。
- 五份相关文档当前 80 个本地文件链接存在、代码围栏配对；33 节点唯一、前置存在且依赖无环。链接检查只验证文件目标，不声称校验所有锚点或渲染结果。
- `git diff --check`；`git diff --exit-code 0027f3f -- src scripts tests pyproject.toml .github docs/distribution`；`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B` 调 `reference.verify()`，结果 `PASS 283`。

未重跑生产回归、安装器、浏览器、Mermaid 渲染、真实模型/GPU 或分布式故障注入；未把实现者另行执行的 A2 预调查回归计为本审查证据。AST 和人工源码推理均不是运行 trace，历史运行验收不自动覆盖未来重构。
