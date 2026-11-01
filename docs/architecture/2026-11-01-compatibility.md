# A2：重构前兼容与操作基线

日期：2026-11-01。源码身份：`cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`；生产树仍是 A1 的 `3df37c618814fe4b7b41b17bf49cb915ede42e32`。实施分支 `refactor/architecture-foundations`。[审计](2026-11-01-audit.md) · [边界 ADR](decisions/0001-refactoring-foundations.md) · [交付记录](../delivery/2026-11-01-compatibility.md)。

## 保护内容与来源

新增 [兼容测试](../../tests/test_compatibility_baseline.py)与 [固定夹具](../../tests/fixtures/compatibility-v0_2_0/identities.json)：

- Unicode/排序/分隔符的 canonical 与 evaluation 摘要向量，固定不同结果；不将两种 SHA 算法合并。
- Skill 目录内容、每文件 SHA、POSIX executable bits 和整树 digest；Windows 核对普通文件向量，可执行位另由 POSIX 检查。
- 两个公开开发模板的完整 compiled JSON canonical SHA 及 request/profile SHA，捕获于重构前编译器；不是在测试运行时计算“期望”。
- [旧 SQLite schema](../../tests/fixtures/compatibility-v0_2_0/schema.sql)与 [合成数据/资产](../../tests/fixtures/compatibility-v0_2_0/state.json)：16 表、项目/草稿修订、记忆历史/镜像、Skill/头/事件、评价/优化、资料/来源/提案、独立运行和 Forge 未知状态。绕过当前 State 初始化先建旧库，再由应用重开与跨进程读取；旧 revision 写入必须拒绝。

schema 是 0.2.0 所有 DDL 实际执行后从 sqlite_master 捕获的文本；项目默认和身份向量来源为重构前源码。状态样例人工合成，包含失效的历史 evaluator/Forge 路径与不具执行意义的占位身份，只检查旧序列化/读取和保留语义，不能作为可执行评分证据。`@HOME@` / `@REPO@` 只由测试夹具替换，**不是产品配置语法**。Skill 和来源文件内容可实际核对；真实评分/批准验证继续使用既有合成子进程和 adapter 测试。

固定向量不应随重构重生成来消除失败。确需新协议版本时，保留旧向量及拒绝/迁移证据，再另加新向量。整个夹具没有用户真实任务、密钥、机器 home 路径、活动数据库或模型产物。

## 可复跑检查

按现有开发环境安装 `.[dev,web,gepa,temporal]` 后，从仓库根运行；以下命令不默认调用付费模型：

```bash
python -m pytest -q --tb=short tests \
  src/ergora/data/reference/platform/upstream/platform/tests/test_contracts.py
```

Linux / WSL2 追加 frozen portable 与 adapter/runtime 边界：

```bash
PYTHONPATH=src:src/ergora/data/reference/platform/upstream/platform \
python -m pytest -q --tb=short \
  src/ergora/data/reference/platform/upstream/platform/tests/test_portable.py \
  src/ergora/data/reference/platform/upstream/platform/tests/test_workflow.py::AdapterTests \
  src/ergora/data/reference/platform/upstream/platform/tests/test_runtime.py
python -m ergora reference verify
```

CI 保留两 OS wheel 安装、冻结身份、应用与原生 PowerShell 安装/升级；新增 `refactor/**` push 触发和 Linux adapter/runtime 检查。AdapterTests 不启动 Temporal 测试服务器，RuntimeTests 使用假传输检查原输入、重复 start、取消 signal 与异常 close；不能把它们算真实 history replay/服务重启验收。

|保护边界|复用的实际测试位置|
|---|---|
|候选、计划批准、可信检查、review actor、fence 未确认|reference `test_workflow.py::AdapterTests`|
|原始输入恢复/重复 start、transport failure 不等于不存在、取消只发意图|reference `test_runtime.py`|
|scope/依赖环/未知字段/固定 profile、编译包及 digest|reference contracts/portable + 新 compiled golden|
|Skill 变造/exec 位、同评价集、holdout/partial evidence/错误 scorer、采用回退|`test_skills_evaluation.py` + 新 digest golden|
|项目/记忆/草稿 revision、项目隔离、重开/跨进程|原 projects/memory/web + 新旧库夹具|
|运行取消/后代清理、研究预算/取消恢复、Forge 对账|原 processes/reference_executor/research/agents；可选 SDK/服务未配置会跳过|

## 实际测量与限制

重构前 Linux Python 3.11.15 回归实际 **109 passed、17 skipped、36 subtests passed、1 warning，81.53 s**。跳过边界包括原生 Windows、明确选择的 Forge/mini SDK 和独立 Temporal 服务；不把跳过计为已验收。新增 adapter/runtime **28 passed，1.89 s**；新增固定夹具 **7 passed，1.05 s**。最终组合与两 OS CI 结果由交付记录更新，不把此首次基线计数写成永久期望。

已安装 CLI 的首次无模型命令旅程：1 次 `git init`，`project add/bind`、`agent run/output` 共 4 次 Ergora 调用，创建 binding/prompt 两文件，共 7 个操作单元。用当前解释器作为 command 回显，实际 succeeded、revision=2、stdout 可读；自动脚本总计 1.18 s。**不含安装、人工输入、模型认证、正式任务服务或六阶段验收**；这个时间不表示人工易用性或 LLM 性能。

安装基线按使用手册计数：Ubuntu 空环境示例含包索引/基础包、clone、cd、安装脚本、PATH、serve 共 7 条 shell 指令，要求系统包权限；已有 Python 的自有 venv 示例为 3 条。这里是文档步骤计数，不是新空白系统安装实验。原生 Windows 和完整 reference 各有独立手册/权限范围，不据此推算它们的安装时间。

新增 Agent 的当前同步面按 A1 核查为 agents、tools、projects 默认（若变更）、JS 字段、SDK 安装配方及 kernel 版本（若对应工具）；R1 用真实新增兼容组件检查缩小范围。后续比较操作数、必须编辑的位置和用户错误可恢复性，不以代码行数或抽象类数量证明易用性提升。

本地没有新增真实模型、GPU、ReMe 引擎、Temporal 服务恢复或空白 Windows 安装证据。FastAPI 测试客户端的 httpx 弃用提示和 Actions 的 Node/runner 提示分别记录，当前不为消除警告顺带升级依赖；schema 依赖在 R2 单独接入并验证。
