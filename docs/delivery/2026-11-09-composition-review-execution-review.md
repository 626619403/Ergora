# CR3b 正式单叶审查执行桥：独立两轴审查

日期：2026-11-09。审查者：Codex fresh-context 独立审查者；未继承实现对话。固定基线为 `d8668a43abf5adcbabdf12d0ee5b1f570114262b`，检查基线至工作区的完整 tracked diff、untracked 文件正文和相关调用者。同一审查者在本片内补核修正；行为审查候选为 R4，最终 R4-final 仅清理一个 EOF 换行，源码、非 editable 发行、受影响回归和真实模型原件已独立核对，六项实证发现均已关闭。精确候选 `6826047031aebddb7eb6c5fcf43cfe91ebb45ada` 的固定 Git 对象、自身双 OS CI 及即时 SSH 远端终核亦通过，见文末。

审查依据：[AGENTS.md](../../AGENTS.md)、[当前计划](../PLAN.md)、[本片记录](2026-11-09-composition-review-execution.md)和[CR3 执行范围](2026-11-09-composition-executor.md)，并应用 maintainable-project-delivery 的 independent-review 与 codebase-design。检查的生产文件为 `reference_executor.py`、`reference_creation_process.py`、`reference_task_creation.py`、`reference.py`、`stage_driver.py`、`agent_runs.py`、`workflow_definitions.py`；测试为两份 executor 测试、`test_composition_manifests.py` 及 `reference_acceptance.py`、`stage_agent.py`。本片/PLAN 文档一并核对。CR3a 的原 verify 实现及其后续状态记录不是本片新生产行为。

|审查轴|当前结论|
|---|---|
|要求符合性|通过本片内部单叶执行范围：六项发现均有源码处置及修正包行为证据，最终 R4 的 22 项正式执行回归通过，真实自身模板 approve。公开 v2 入口与完整 Temporal/Supervisor 旅程仍是后续范围，未提前宣称可用。|
|结构与可维护性|通过：专用创建进程、原子 manifest 恢复、Git 完整有界读取及原 monitor 生命周期各归现有所有者；没有新增调度器、账本、模板分支或通用插件框架。M1 的聚合预算已验证，SP4/SP5 仅在原启动/读取命令修正。|

实证发现及处置：

- **CR3b-SP2 / P1，已关闭：真实原 review 的已批准 plan 被误当成最终候选依赖而拒绝。** 冻结 `dev_platform/workflow.py:209` 发出 `dependencies={'verification': verification, 'plan': plan}`；plan receipt 绑定起始候选，verification 绑定集成后的候选。R2 `reference_executor.py:238` 对每个依赖都要求当前候选，当时新增 fixture 却只提供 `{'verify': verification}`，隐藏了正常有提交的任务也会失败的问题。审查者按真实 R2 receipts 和原 shape 重现 `Review dependency belongs to another candidate`，旧包原生用例实际 **1 failed / 11.99 秒**。现源码严格要求 verification/plan 两键，verification 绑定本候选，plan 等于已批准 receipt/digest，全部正文共用预算与摘要核验；fixture 保留冻结 workflow 的真实各阶段形状。R3/R4 修正包以及两次真实 MCP 的已批准 plan 正文核验均覆盖此修正。
- **CR3b-SP4 / P1，已关闭：候选工作目录可以劫持可信 Python driver 导入。** R3 `reference_executor.py:366` 用 `python -m ergora.stage_driver` 启动，冻结 `process_job.py:109` 明确保留 `cwd=checkout`。候选顶层 `ergora/__init__.py` 或被导入的 `json.py` 可在受限后端之前执行，checkout snapshot 无法发现外部写入。此项由 R3 自身模板提出，审查者沿实际调用链独立确认，并用只读 Python 搜索路径探针核实。最小修正在现有 driver 命令添加 `-I`，保留原 monitor。新增 shadow 候选在 R3 包 inventory 阶段真红；R4 六阶段通过，审查者另核四次 driver 记录均含 `-I`，外部 shadow 标记未生成。
- **CR3b-SP3 / P2，已关闭：成功调用恢复时可缺失 invocation 证据。** 此项来自 R2 自身真实模板审查，审查者另检查原 monitor 与 `reference_executor.model` 后确认：缺 `output/invocation.json` 时旧代码跳过 binding/policy/input/prompt 核对，保留成功 terminal 和 result 即可能发布缺少绑定的 pass。最小修正在组合调用 code=0 时强制要求 invocation，再核身份及成功状态/结果摘要；失败或取消允许没有尚未生成的 invocation。R3/R4 缺 invocation 的中断恢复回归通过，正式 MCP 结果摘要亦独立核实。
- **CR3b-SP1 / P2，已关闭：实际选中后端的当前准入发生过晚。** 初版构造只 preview 定义默认 backend，实际 override、mode 和冻结 policy 到 review 调用才核对，backend 合同漂移可能先产生原 project/claim 副作用。最小修正在 `super().__init__` 前核选中 binding、平台、mode、当前 policy、推理配置和 task-MCP 依赖；调用后核实际回执属于不同职责。现源码准确，R3/R4 policy-drift 场景均在原构造副作用前拒绝。
- **CR3b-SP5 / P2，已关闭：Git replace refs 使审查材料与可信验证器读取不同对象。** R3 `reference_executor.py:169` 的 `_git_bytes` 没有关闭 replacement objects，而冻结 `harness/git_scope.py:72` 显式关闭。共享 mirror 的替换 ref 可以让已删除 base-only blob 在原 oid 响应头下返回替换正文，自算正文 SHA256 不能证明原 Git 对象。此项由 R3 自身模板提出并经独立调用链核实；最小修正在统一命令添加 `--no-replace-objects`。新用例在 R3 已完整 review 后因错误 base-only 正文真红；R4 通过。审查者另用真实 mirror 核同一 oid 的普通读取仍返回替换字节，关闭 replacement 后与正式 materials/diff 中保留的原始字节一致。
- **CR3b-M1 / P2，已关闭：依赖材料总量只在完整序列化后拒绝。** 初版允许 100 个 artifact 各至 16 MiB，全部文本聚合后才按 1,000,000 字节输入限制拒绝。最小修正沿读取累计预算，复用 `read_raw(..., 1_000_000 - used)`，保留最终完整编码上限。R3/R4 两份摘要有效、各 600,000 字节的日志场景均在超出剩余额度时拒绝。

同期实现者把 carried manifest 恢复移入 `workflow_definitions.restore_manifest`，复用已有完整 inspector 和原子 publisher，避免中断暴露半成品；这是已有资产所有者的内聚能力，无需新资产框架。`reference_creation_process.task_creation` 由应用用例和 executor 实际消费，保持专用进程与标准库依赖，避免多线程全局 reader patch 及静态循环。Git 资料改为先批量核对象大小、再按长度读取原始 blob；两份树按对象引用完整内容，减少未变化源码的重复及逐文件子进程开销，没有截断材料。

历史证据：源码创建/架构 37 passed / 17.99 秒，输入/架构 33 passed / 2.49 秒；初版非 editable R1 包正式协议场景 17 passed / 106.98 秒。R2 源码资产/架构 46 passed / 3.85 秒，非 editable 包 executor/架构 43 passed / 403.64 秒、相关合同 111 passed / 155.45 秒。审查者独立重算 R2 全部 369 文件映射一致，wheel SHA 为 `ec66e9a060c76de5048fb998d1302a595bc658c47e2629166c06040120092ba1`。R1/R2 旧 fixture 的通过不覆盖真实 review shape 和其后修正；这些结果只保留各自原范围，不移记为最终发行验证。

审查者另独立执行 `git diff --check`（通过）、冻结身份 `reference.verify()`（PASS，283 文件，源分发摘要 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`），并核冻结目录无差异。真实 Git 轻量探针对同一基线的两份源码验证批量读取：两份树完整、两个唯一 blob、正文摘要与原字节一致、diff 为空，约 0.15 秒。工具自身审查建议 Git 输出应在超限时停止，而非先完整落盘；新实现使用标准库 selector 同时有界读取 stdout/stderr，finally kill/wait。审查者再用 10,000 个真实 blob 请求和 10 字节输出上限验证即时拒绝，Git 返回 -9 且已回收；同次正常批量读取仍通过，约 0.19 秒。没有修改源、依赖或提交，也没有调用外部消息工具。

R2 正式 task-MCP 实际模型已经运行，native list/read 成功并留下原生回执；模型正确指出默认治理 acceptance 的边界 reproducer/仓库 map 未由 syntax-only 合成检查证明，返回 request-changes，外层保存 FAILED/independent-review=fail。fixture 强制期待成功而断言失败，不能把该结果记作模型批准。它也暴露出 fixture 没有给出计划正文，进一步核原 workflow 才定位到 SP2；不能只补正文而保持错误候选条件。

R2 自身结构模板实际调用 201.41 秒，decision=request-changes，提出 SP3 和上述 Git 建议。审查者从原生事件独立重组附件 8 页，连续覆盖 0..222,714 字节至 next_offset=null，SHA 为 `2f1e5cffd827ebd3bf92e06464dfaa06bde53cd39dfe62cfe279f64c2f899927`；protocol result 与规范化 run result JSON 等价，后者摘要与原记录一致。这次结果不能替代修正后候选的自身审查。

R3 非 editable 包正式 executor 回归 **20 passed / 224.60 秒**，使用冻结 workflow 的真实依赖形状，并包含缺 invocation 恢复、当前 policy 漂移及两份有效大日志拒绝；旧 v1 两模板两后端和相关 verify 为 **9 passed / 15 deselected / 90.42 秒**。审查者独立重算 R3 全部 369 个源码/wheel/安装文件映射一致，wheel SHA `af618bfd6a1431017eb6d4b0699d252c9b711fc2176c13b7d54d4c2f32b44dd6`，executor SHA `a2f29bfec267ffa590f877adfb475f21cc2e331a6273b1ccf2d133db492ebd1f`。上述旧发现至此已由修正包覆盖；SP4/SP5 后的源码不能直接继承该包身份。

R3 正式 task-MCP 再实调返回 request-changes，外层 FAILED/independent-review=fail，仍为语义正确的治理验收拒绝。审查者独立重算全部 11 个正式 artifact 摘要，核 materials/prompt/candidate/input/invocation/result 相互绑定、plan 等于 approved receipt/digest、两条依赖的正文摘要正确，MCP scope 与原件 JSON 等价、audit 原始字节一致；底层 invocation 的 `formal_execution_authorized` 仍为 false。这证明实际协议和证据闭合，不证明模型批准或成功开发。另核 1,000 文件/树、1,015 个唯一 blob、89,260 原始源码字节的三次材料准备为 0.214/0.168/0.680 秒，只代表仓库材料准备，不是整体 workflow 性能。

R3 自身结构模板通过实际 Codex `gpt-6.1-sol` / high / task-MCP 运行 **301.20 秒**，run `e86e4caff43e43d3af2b93aaef55cef8`，decision=request-changes，提出 SP4/SP5。审查者从真实 stdout 的 MCP completed result 重组全部 276,858 字节附件：5 个唯一页连续 `0→65536→131072→196608→262144→276858` 至 next_offset=null，第一页另重复读一次；各页及重组字节均与源附件一致，SHA `3cc5892571d969e2bf8a6f4e8bdc154c8f24a798a1b831496b6e1cf25e6c0e75`。protocol result 与规范化 run result JSON 等价，摘要 `e069498c810cd127a0c39fc6ba36d5a5342f1afbf182956476747d09aa664140`，response 正文与保存审查文本一致。模型明确区分源码观察和未执行验证；此次不是 approve，也不能替代 SP4/SP5 修正后的自身审查。

最终 R4 的源码、wheel、非 editable 安装全部 **369 文件**独立重算一致；wheel SHA `5f44d0dfec32cfbc12c3070ffcf3210bd2d16c13780171871c5e3247136d7b4d`，executor SHA `7afa9d3cd16ddc0f95743e50a33d38647529a3d28d896459388c4047cde71b33`。R3→R4 生产源码只有上述两个命令参数修正。独立运行 R4 安装包 `reference.verify()` 为 PASS/283，源 ZIP SHA 仍为 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，冻结目录相对基线无差异，`git diff --check` 通过。新增两例在 R3 包实际 **2 failed / 20.80 秒**，R4 正式组合全套 **22 passed / 250.68 秒**；统一注册等相关旧合同 **9 passed / 15 deselected / 94.66 秒**，原两模板×两后端及可信 verify **9 passed / 15 deselected / 87.13 秒**，两组重复了五项 verify 边界，不计为 18 个独立场景。

R4 正式 task-MCP 的实际模型再次 request-changes，外层 FAILED/independent-review=fail，准确保留合成治理验收未满足的结果。审查者重核全部 11 个正式 artifact、materials/prompt/input/selection/policy/candidate/invocation/result、两条依赖正文及原 plan 批准关系、scope/audit 原件均一致；result SHA 为 `aab0750d0fd2c88cd3d7ed4f2b9b0fa053eb949c90495ddd49d5e752bfc72f2f`。这是协议与证据验证，不是成功开发。

R4 自身结构模板实际 **205.12 秒 / approve**，run `dee75f24f3e5419c90a93e3ae45c1847`。审查者从 MCP completed results 独立重组完整 279,029 字节，5 唯一页连续 `0→65536→131072→196608→262144→279029` 至 null，另有一次重复首读；每页与原件逐字节一致，附件 SHA `9df97bfa89c74e7770d345052878dde2e0b070cb326ffa707c5a54761c061fa9`。20 项源码/测试身份均等于 R4 实调时文件，其中 15 份生产及冻结邻居全文与 R4 wheel 原字节相同。protocol/规范化结果 JSON 等价，result SHA `e3a229707c6b0be4b4c8a6a30b3426bb4529c62976412f5ed2b3fde79f093b33`，response 与保存审查正文一致；公开[输入身份](evidence/2026-11-09-cr3b-r4-self-review-identity.json)及[结果原件](evidence/2026-11-09-cr3b-r4-self-review-result.json)可复核。模型只审所给源码，没有冒称执行测试或证明整栈。

提交前 staged 检查另发现新 helper 尾部多余空行；此前 unstaged 检查未覆盖该新文件的完整新增内容。实现者只删除 `reference_creation_process.py` 的一个 EOF 换行，R4 原件 2,058 字节、最终 2,057 字节；审查者逐字节确认原件恰为新件加一个 LF，完整 AST 含位置信息亦逐节点相同。最终 helper SHA `8e6122720bed4c53b009a828d8039f7abfd322d29b106a6d6107e684be3f0914`，其余 19 项自身审查身份保持；R4 模型/行为结果仍归原件，本次机械清理不冒称另行实调。审查者另重算 R4-final 源码、wheel、非 editable 安装 **369 文件**全部一致，两个 wheel 的源码集合唯一差异即该 LF；最终 wheel SHA `bd72d38bde47930c82e7d0acaa37fb7aab1f3efc3d8ae778f3e85a180584c3ca`，executor SHA 不变。独立运行最终安装包 `reference.verify()` 为 PASS/283，源 ZIP 身份不变；不因相同版本号沿用旧 wheel 摘要。

最终核本片记录、PLAN、运行桥总记录、CR3 执行范围及 AC 计划的当前状态一致；九份变更 Markdown 的 62 个本地链接（含一个锚点）有效。三轮公开自身证据与私有原件一致，历史 request-changes、旧包红例、重复场景和最终 approve 均保留真实范围。CR3a 的候选之后状态追记是原片历史交付记账，不是本片生产实现。

本审查只写此报告，没有修改生产源码、依赖或提交。合成原生协议不证明模型质量；底层 input 仍是 operator-supplied/非正式授权，正式权威来自外层已核创建、job/context/candidate 与可信 receipt。公开扫描/start/status 及实际 Temporal 旅程见[下一片调查与计划](2026-11-09-composition-public-runtime.md)，Supervisor 及恢复出口沿 CR4/AC3c.4；该计划没有宣称行为已实现。Claude 回退理由是先前已保存的实际上游失败和用户明确授权，没有把同模型实调称为模型错误独立。精确交付终核与本地行为审查分别记录如下。

固定候选为 `6826047031aebddb7eb6c5fcf43cfe91ebb45ada`，父提交恰为本片基线。审查者从 Git 对象读取变更集合及原始 blob，核其恰为保存 scope 的 27 个文件，各 SHA256 全部一致；固定候选 `diff --check` 通过。固定 Git 树 `src/ergora` 完整 369 文件集合与 R4-final wheel、非 editable 安装及身份清单完全相同；最终 wheel 仍为 `bd72d38bde47930c82e7d0acaa37fb7aab1f3efc3d8ae778f3e85a180584c3ca`。固定 manifest 及 283 个 Git blob 摘要全通过，冻结目录相对父提交无变化。后片工作区变动不参与本段比较。

本候选自己的 [Portability CI 42545445322](https://github.com/626619403/Ergora/actions/runs/42545445322) 为 push / attempt 1，独立 API 已核两个作业 `head_sha` 精确等于固定候选。01:32:34 UTC 起公开 API 返回 403 rate limit exceeded，停止该轮询后改用公开 Actions HTML；作业原生 step 状态及日志路径仍绑定同一完整候选，没有新增认证或修改配置。2026-11-09 **01:38:45.064259 UTC** 独立读取确认总体为 Success、两个作业 completed，七项适用必要步骤均 success：

|平台 / Python|作业|适用必要步骤|必要步骤最后完成 UTC|
|---|---|---|---|
|Ubuntu / 3.11|[128929318653](https://github.com/626619403/Ergora/actions/runs/42545445322/job/128929318653)|构建安装、包身份、应用回归：3 项 success|2026-11-09 01:38:15|
|Windows / 3.12|[128929318513](https://github.com/626619403/Ergora/actions/runs/42545445322/job/128929318513)|构建安装、包身份、应用回归、PowerShell 安装升级：4 项 success|2026-11-09 01:33:01|

本段只记录 CI 步骤结论，不声称每个平台条件测试均实际执行。确认成功后的同一进程于 **01:38:45.064320 UTC** 立即启动默认 SSH `git ls-remote`，使用 BatchMode 与 15 秒连接超时；**01:38:46.457071 UTC** exit 0、stderr 为空，远端返回：

```text
6826047031aebddb7eb6c5fcf43cfe91ebb45ada  refs/heads/refactor/architecture-foundations
```

CR3b 要求与结构两轴、六项发现修正及固定候选精确交付终核全部通过，无剩余阻塞 finding。此段为候选提交之后的同片记录追记；结论只覆盖本片内部单叶桥，后续工作区或新候选不继承本次 CI/远端身份。
