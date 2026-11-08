# AC1.2 固定模板说明：独立评审

日期：2026-11-08。评审者：fresh-context 独立代理 `template_instructions_review`，未接收实现对话或预设结论。先读原始 Q-1、验收及 diff，再读相邻调用与作者记录；已读 `AGENTS.md`、maintainable-project-delivery/独立评审说明及 codebase-design。

**需求符合性：本地通过。可维护性：本地通过。所审范围内无新增 finding，无未解决源码阻塞项。** [Q-1](2026-11-08-agent-composition-review.md)的固定正文消费已有源码、实际进程输入和失败路径证据。[本片交付](2026-11-08-template-instructions.md)仍待归档审查、普通精确候选及自身 CI/远端终核；不据此登记新组合、训练或真实模型质量通过。

## 身份和范围

项目与 docs 归属为 Ergora。实核分支 `refactor/architecture-foundations`；基线及本地评审时 HEAD 都为 `bf99bd47220572fd721546a2eeb5b1b2739a57b5`，没有用别的提交或已安装旧包代替工作树。

首轮九文件清单 `.ergora/checks/ac1-template-instructions/review-scope.json` 为 1,766 字节、SHA256 `140d641aa5d1c0ac600096203cf927b831d2492af50a6b59abff344795d39f6a`。八个 tracked 文件的实际 `git diff` 与 `review-tracked.diff` 逐字相同：28,802 字节、SHA256 `6f6dbf5477fcbbf084731e0198eae396383f7cce155fb2b49e9858b9bd40b2a5`。新交付记录单独实读并核身份，没有漏掉 untracked 文件。

|生产/测试身份|字节|SHA256|
|---|---:|---|
|`src/ergora/reference_executor.py`|11151|`b079f25318cfe6d184d2d418167abf4a00c3b24dcead3fabf61df5856002ecef`|
|`tests/fixtures/reference_acceptance.py`|14707|`53b919b13f8eea4c9ed006d2993dd6cc65304c0bdd11d7806f02d17b0ed1ac93`|
|`tests/test_reference_executor.py`|6777|`6ef6164e73fae02983e6ce24dbdfbe8dd3143f0f2d97aec0aec0f6d74d0f8fe8`|

其余六文件均实读并核对首轮清单 SHA：`docs/AGENT_BACKENDS.md`、`docs/architecture/current.md`、`docs/PLAN.md`、`docs/plans/2026-11-08-agent-composition.md`、新增本片交付记录及前片 `2026-11-08-skill-publication-review.md` 的候选追加。

评审期间前片独立者继续追加 AC1.1 终结，其首轮 12,965 字节前缀保持原 SHA，新增段实读为前片归档。随后作者更新 AC1.1 交付、共享回应及计划状态，未扩大本片行为范围；这些归档在候选固定后再核最终身份。本片三份生产/测试终写前仍保持表内 SHA。本报告未独立核验 AC1.1 远端 CI，亦未将它替代 AC1.2 验收。

相邻实读覆盖：`reference.executor` 的安装身份检查、`reference_task_creation` 与原 `agent_platform.projects.create_task` 的 compiled 保存、portable 的 package/compiled/spec 校验、继承 executor 的六阶段与错误回执、`stage_driver → agents.invoke → processes.run` 的实际输入、原 Workflow/Activities 的批准/候选/作者/session 门禁。ADR0004 只作未来范围背景；没有将组合设计当成现有行为。

## 需求符合性

1. [reference_executor.py](../../src/ergora/reference_executor.py)第 56–59 行读取当前任务完整 compiled，调用既有 `validate_compiled`，再要求完整 `compiled["spec"] == self.spec`。portable 第 258–272 行核摘要、重新推导 spec 和大小，第 111–155 行核正文组件摘要及固定 profile；spec 相等再绑定当前任务。这两类守卫各有可达反例，摘要校验未被独立当作授权。
2. 同文件第 63–76 行明确要求按阶段遵守固定说明，并将完整正文和 profile 中的说明摘要放入实际 prompt；正文没有使用依赖产物的 60,000 字符截断。继承 executor 的 inventory、plan、每个 work unit 和 review 都调用这个 override；integrate/verify 保留可信实现。第 102–105 行沿原 `agent-selection` 同时保留说明摘要、原完整 prompt SHA 和结果 SHA。
3. 读取与校验早于第 83 行 Agent 请求写入及第 90 行模型监控启动。三种反例沿原 `execute` 异常处理产生 FAILED，无活动包回退；独立重跑均通过，并检查没有 `selected-agent/request.json`。
4. `validate_compiled` 使用已保存 package 重新验证，不调用 `load_package` 或当前 registry。删除创建源 portable package 后，独立重跑仍完成六阶段，并逐模型阶段核固定正文、摘要及 prompt SHA。原安装 profile 身份校验保留在继承 executor 的第 83 行；源包删除与安装 profile 漂移的合同在文档中准确区分。
5. 继承六阶段、批准、可信检查、候选/作者/session、只读/取消及旧 binding 路径未改，原 fixture 仍经过批准、poll、候选与 fresh session 检查，并保留取消/迟写、legacy/统一登记用例。283 个冻结文件独立核对一致；直接 `agentflow` 未改，文档也未声称其获得新正文行为。

文档区分源码、非 editable 包、独立审查与候选 CI，Q-1 的本地修复范围符合原要求。

## 可维护性

|检查项|结论与依据|
|---|---|
|模块深度/ownership|改动留在拥有 prompt 与追溯信息的 `Executor.model`，interface 不变，一处覆盖四类模型 stage；提交、批准、检查、回执继续由继承执行器拥有。|
|复用和控制流|复用 `validate_compiled`、`require`、任务文件及 `agent-selection`。没有新公共 helper、状态、依赖、上游逻辑副本、fallback 或额外 handler；两项校验各有实际职责，无无效守卫 finding。|
|测试价值|fixture 读取 `processes.run` 写出且传给 `communicate` 的同一 stdin，再核正文/摘要和 prompt SHA，跨过真实进程 seam。三种拒绝与删源包旅程保护不同合同，复用原 fixture，没有新测试框架/CI 作业。|
|资源成本|每次模型调用增加一次本地 compiled 读取/验证和完整说明注入，当前正文为 2,451/2,801 个 UTF-8 字节；不增加模型调用、网络查询、服务或缓存。四项定向复跑 11.80 秒。未测 token/费用、峰值内存或长任务性能，无证据要求额外缓存或扩大矩阵。|

未发现应删除的冗余守卫/测试或需要新增抽象的证据；后端 adapter 仍属 AC2。

## 实际检查与证据限度

独立检查使用现有新 wheel 环境，不安装依赖、不重建包、不重跑完整重型矩阵。移除 `PYTHONPATH`，禁写 bytecode 和 pytest cache，实际导入位于该 wheel venv 的 site-packages。

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 \
  .ergora/checks/ac1-template-instructions/wheel-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_reference_executor.py::test_template_instructions_fail_closed_before_agent_invocation \
  tests/test_reference_executor.py::test_task_keeps_template_instructions_when_source_package_is_unavailable
```

结果：**4 passed，11.80 秒，零 skip**。只在隔离临时 fixture 中运行，没有调用实际模型、服务或用户任务。

另用 wheel 中实际 portable 模块做两种纯内存反例：改正文并重算外层 package 摘要，报 `Component digest mismatch: instructions.md`；再重算组件摘要，报 `Package cannot reproduce pinned legacy profile`。未修改既有证据。

独立逐字比较 352 个当前源码/wheel/实际安装文件，差异为 0；wheel SHA256 为 `9cb4793a794d5f85c022c3771c16ee28935b2a1d37f6374226711375058eaaf6`，与原记录相同。独立重核 manifest 中 283 个冻结文件，差异为 0。六份首轮 Markdown 快照的 203 个本地文件/锚点和 30 条 README parser 命令通过；`git diff --check` 通过。静态复核只在内存运行，未覆写作者 `static-documents.json`。

实读作者命令/日志：原真实进程红例缺 `template_instructions` 失败；显式 `PYTHONPATH=src` 的四文件检查 104 passed/零 skip（161.54 秒）；非 editable 包 8 passed/11 deselected/零 skip（70.94 秒）。生产/测试 SHA 与本轮一致；这些是核过的作者记录，本轮未重跑全部 104/8 项或旧码红例。

未验：真实模型遵循说明的质量/速度，Claude/mini 的本片实际进程旅程，真实 Temporal 服务端完整运行，新组合与训练执行，原生 Windows 正式执行，安装 profile 漂移的新增动态反例，恶意同用户隔离，长任务并发/资源上限，以及 AC1.2 尚不存在的精确候选、远端 CI 和推送终结。未逐行审计所有 vendor 或所有历史测试。上述“无 finding”仅适用于本报告所列切片及实读相邻路径。

本次唯一项目写入为本报告；生产、测试、依赖、CI、前片报告及既有证据均未修改，没有提交或推送。候选提交后需由同一评审者固定 Git 对象核本片最终身份、状态归档和自身 CI/远端事实；后续新行为切片使用新独立评审上下文。
