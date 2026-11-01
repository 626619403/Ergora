# S11 / A2 独立审查

审查日期：2026-11-02（Asia/Shanghai）。审查者：独立 fresh-context agent `compatibility_review`。输入为原始 A2 验收、精确基线、完整变更清单与已运行证据；未继承实施对话。遵循项目 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review brief。

## 审查范围与身份

- 基线：`cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`。
- 已提交候选：`4deb8b78690ba1c102c2b08aa6dd3c4054815d6c`，分支 `refactor/architecture-foundations`。
- 完整 10 文件差异：`.github/workflows/portability.yml`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/architecture/2026-11-01-compatibility.md`、`docs/architecture/decisions/0001-refactoring-foundations.md`、`docs/delivery/2026-11-01-compatibility.md`、`tests/test_compatibility_baseline.py`、`tests/fixtures/compatibility-v0_2_0/{identities.json,schema.sql,state.json}`。
- 同时检查审查期间上述 4 份计划/交付/兼容文档的未提交补充：实际 CI 成功记账和公开可复跑旅程。后者 Python 片段 SHA-256 为 `9c2e7add47db4fd4a136abcc9545921cb0304c74946694baa4ff284c1ccfdb26`。生产、测试与 CI 未再变化。
- 邻近消费者：state/projects/drafts/memory/skills/evaluation/optimization/research/kernel/tools/reference、既有安装手册、冻结 contracts/portable/AdapterTests/RuntimeTests，以及既有评价、研究恢复、Forge 对账测试。

## 分别判定

**需求符合性：通过，限于 A2 兼容保护和决策范围。** 未改生产合同、依赖或冻结发行；固定身份、合成旧状态、旧库重开/跨进程读取、revision 冲突、已有可信证据和恢复取消反例均有对应保护。安装计数、无模型命令旅程及接入同步面有可核对依据。schema/注册/reference/状态权威 ADR 将目标和现有实现分开，明确 R2 接依赖、R3 处理旧客户端拒写限制。

**可维护性：通过。** 本切片没有新增生产抽象或第二套状态机；测试夹具自行构造旧库，固定期望不由被测实现生成。fixture 的递归路径替换和 SQL 仅服务可信合成输入，没有扩展产品格式。CI 的冻结 platform 路径明确传入子进程，未把 `src` 加入包回归的导入路径，wheel 构建/安装和原生 Windows 安装检查仍保留。

**Findings：在所审范围内无实质 findings，无阻塞项。** 不将此结论扩展为未来 R1–R8 的设计或运行验收。

## 独立核验

1. 固定期望标注的 `0027f3f9bf9f03a62afe8710970587b66103f7fe` 为候选祖先；其 `src`、`scripts`、`pyproject.toml` 与当前生产树相同。既有开发环境内安装的全部顶层生产 `.py` 也逐字节同源码，因此此次复跑没有误用另一份生产实现。
2. 独立执行实际 DDL，在临时目录重建所有域，再与固定 `schema.sql` 的 sqlite_master 比较：**16 表及全部索引一致**。旧数据的 evaluator/Forge 路径和占位摘要只进入读取/保留断言；测试没有拿它们构造成功评分或批准。Skill 内容和来源快照另有实际摘要校验。
3. 新测试独立复跑：**7 passed，0.88 s**。禁用仓库字节码和 pytest cache，临时资产写入临时目录。覆盖两种 JSON 摘要、普通/POSIX executable Skill 身份、两个 compiled golden、旧库保留及冲突拒绝。
4. 在未先导入 portable 测试的进程，只显式设置冻结 platform PYTHONPATH，复跑 **AdapterTests + RuntimeTests：28 passed，1.45 s**。已检查候选/计划批准、错误证据、独立审查主体、fence、输入恢复、重复 start、取消 signal 和异常 close 对应反例。
5. `reference verify`：**PASS，283 文件**。基线和当前差异检查通过；源码、安装脚本、依赖及旧发行无本切片变更。
6. 按文档原文提取并执行新增无模型 Python 片段：**7 操作、succeeded、revision=2、stdout 断言通过，0.743 s**。此时间与原 1.18 s 分别保留各自实测值，只说明脚本复跑；计数排除测量代码，不包括安装、认证、人工输入或正式六阶段。
7. 对照 `docs/USAGE.md`：Ubuntu 示例 **7 条**命令，自有 venv 示例 **3 条**；同步面与 A1 具体消费者相符。新增 3 份架构/ADR/交付文档的 **17 个本地链接、围栏及个人路径检查通过**。
8. 独立读取[公开 CI 41323798679](https://github.com/626619403/Ergora/actions/runs/41323798679)：精确候选与分支，**Success、2 jobs completed、3m 1s**。两份 job 页面分别显示 `native (ubuntu-latest, 3.11) succeeded` 与 `native (windows-latest, 3.12) succeeded`。workflow 仍执行 wheel 安装、冻结身份、应用回归及 Windows PowerShell 安装/升级。

## 证据限制与收口

实施者记录的 Linux 最终组合 **144 passed、17 skipped、36 subtests passed、1 warning，78.64 s** 已核对命令与边界；审查者未再次执行整个组合。公开 CI 页面证明 jobs 成功，完整日志需登录；官方 API 本次返回限流 403，没有据此编造 Windows 测试条目数。

没有新增真实模型/GPU、可选 Forge/mini SDK、ReMe 引擎、真实 Temporal 服务恢复或全新空白系统安装证据。Adapter/Runtime 的合成检查不等于真实服务 history replay。旧 0.2.0 不识别数据库版本的限制仍属于 R3，A2 没有承诺旧二进制自动拒写。

审查范围内的验收证据已齐；实施者可记录本审查结果，按既有授权完成 A2 文档收口、提交/推送及远端核对，再进入 R1。审查者只新增本报告，未安装依赖、修改生产文件、提交、推送或写外部系统。
