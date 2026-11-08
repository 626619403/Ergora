# AC3c.3 / CR1 版本化 Workflow 输入独立审查

日期：2026-11-09。审查者：fresh-context `composition_workflow_input_review`，另以两个 fresh-context 子审查分别检查 Standards 和 Spec。最新本地结论：**R4 的 Standards / Spec 均通过，ST1、SP1、SP2 全部关闭，范围内无新增实证 finding。** 已独立核修正、最终包、原始 SDK histories 及真实自身审查的完整交付身份；最终精确提交、CI 与远端终结仍待核。以下保留各轮证据，不登记为完整 AC3c 或正式 v2 执行验收。

## 范围与身份

项目及文档根分别为 Ergora 与其 `docs/`。已读 `AGENTS.md`、AIHERO 索引，以及 maintainable-project-delivery、codebase-design、code-review 与 independent-review 指引。标准来源还包括 ADR0001/0002、reference 边界、当前架构及测试成本计划；需求来源为本片原始合同和 [CR1 记录](2026-11-09-composition-workflow-inputs.md)、[运行桥计划](2026-11-09-composition-runtime.md)。

固定基线为 `e9c3484fbfa0cfb8cf0737c4d930b5ec176992d3`；初审时 HEAD 等于基线，新增提交列表为空。本次审查未提交改动，读取实际工作树与 [初始范围](../../.ergora/checks/ac3c3-runtime/review-initial-scope.json)、[tracked diff](../../.ergora/checks/ac3c3-runtime/review-initial.diff) 和 `review-new-files` 全文。

初始九文件为 `docs/PLAN.md`、`docs/architecture/current.md`、前片 `composition-admission-review.md` 的终结归档、`src/ergora/reference_task_runtime.py`、`tests/test_architecture_boundaries.py`，以及新增的两份 runtime/workflow-inputs 记录、`src/ergora/reference_workflows.py` 和 `tests/test_composition_runtime.py`。初审逐项核对生产/测试 SHA256 与快照相同；之后仅 PLAN 与本片记录有结果追加。前片归档未被当成本片运行证据。为检查真实调用链还读取原 workflow/runtime/activities、submission/approval/status、`task_envelopes` 与相关测试。

## Standards

**初审：无阻塞的源码标准问题；一项非阻塞 P3。**

**CR1-ST1，P3，测试效率判断项：可选 SDK 检查发生在昂贵 fixture 之后。** [新测试](../../tests/test_composition_runtime.py) 初版第 18–19 行的 `original_input(composed_creation, monkeypatch)` 先完成依赖，再调用 `pytest.importorskip('temporalio')`。没有 Temporal SDK 的有效安装环境会为九个最终跳过的案例逐一初始化 Git、注册项目及建立 manifest；reference 安装复制还会按模块执行一次。后果是跳过不能避免这些准备成本。最小修正为模块级提前 `importorskip`，或使 SDK 前置 fixture 成为昂贵准备的显式依赖。此项依据 [测试成本计划](../plans/2026-11-03-verification-efficiency.md) 的成本原则作判断，其 V2 字面要求只针对 Linux 专用案例，并非本例的硬性违规；未测量本例的实际节省秒数。

新模块有真实版本差异：`LegacyInput` 和 `CompositionInput` 交付不同注册入口和原始 payload；`execution_input` 由 runtime client 与 workflow 实现消费。局部映射留在所属模块，上层没有按后端分派。ABC 是实际版本接口，不是为未来 AC4 添加的插件框架。继承保留六阶段、单元调度、批准、取消和 fence，未见 Refused Bequest 或第二套调度器。

完整 payload 数量/身份、原 projection 一致性、新入口版本及扩展后容量检查各保护可达的不同失败，不建议合并成宽泛异常兜底。可选 SDK 导入仍位于原生 runtime 路径；未向标准库历史读取或基础 CLI 引入 SDK 必需依赖。Standards 子审查的只读 AST 探针解析 48 个自有模块，导入图无环。无新增依赖、schema 或冻结源码改动。

性能方面，每阶段仍先生成原 context，再序列化加入 admission 的完整 context；额外一次有界序列化对应冻结父实现和新增完整容量合同，未见可据此要求复制父实现的收益。信封完整携带会增加每阶段 payload，但合同明确要求保留全部材料。新测试复用现有构造 fixture，身份差异、入口/信号、完整上下文、容量及活动前拒绝覆盖不同失效，未发现值得删除的重复断言；ST1 是准备顺序问题。

## Spec

**初审：CR1-SP1，P2，阻塞，需在持久信封所有者修正。**

需求为完整且经过验证的 v2 原始信封，CR1 记录承诺“完整v2输入核验”。[task_envelopes.py](../../src/ergora/task_envelopes.py) 初版第 119–123 行直接以 graph instance path 建索引并调用 `path.startswith(...)`；[reference_workflows.py](../../src/ergora/reference_workflows.py) 第 72–77 行只将约定的输入校验异常转成不可重试 `ContractViolation`。

可达反例：保留合法 legacy spec 与选中 workflow，把 `composition.json` 中一个 agent instance 的 `path` 改成 JSON 数字 `7`，重新计算文件 base64、完整 manifest inventory digest 和 envelope SHA256。R2 完整性检查通过，随后 `7.startswith(...)` 抛出 `AttributeError`。审查者在固定 R2 非 editable 安装上分别调用 `task_envelopes.unwrap` 和 `CompositionDevelopmentWorkflow.run`，均独立复现相同异常。它逃过输入拒绝路径；SDK 默认会把这种非应用异常作为 workflow task failure 重试，而不是形成不可重试合同拒绝。公开 start/status 仍拒绝 v2，故这不是已开放的正式任务漏洞，但它违反本片新 SDK 入口的验证合同。

最小修正是在原 `task_envelopes` 所有者先验证文档/graph/instance 的必要对象形状与 path 字符串，再建索引；对重复 path 明确拒绝，避免索引折叠。错误以 `ValueError` 传播，由现有 workflow 拒绝合同处理。补充重算 digest 的坏输入回归，确认 `ContractViolation/non_retryable` 且未调用任何 activity。不要增加宽泛 `AttributeError` 捕获或复制完整图权限引擎。作者已接受，修正及复核待补。

该问题首先由真实自身模板 [R2 原始报告](../../.ergora/checks/ac3c3-runtime/r2/hosted-review/codex-review.md) 提出，本审查者独立复现；两轴初次只读检查未发现它，收到新增证据后重开 Spec，而非沿用先前零 finding 观察。

其余已查合同符合：新注册名显式为 `ErgoraCompositionWorkflowV2`；完整单 payload 在原 Transport 得到 legacy projection 之前按完整 JSON 核对；同 legacy/不同 admission 不可采用；六阶段 context 均携完整 admission 并重查 1,000,000 字节限额。新版 submit 使用专用活动，旧版仍用 `dev_submit`。当前公开 start/status 拒绝仍存在。实际 worker/executor/批准接线、verify 路径修复及 AC4 多成员/嵌套运行是明确后片，未据其未实现另报 CR1 缺失。

## 已核证据与限制

独立只读重算 R2 源码、wheel、非 editable 安装和记录的 **366 文件**，集合与 SHA256 全相同；wheel SHA256 为 `4bb71770bf06d80ed279555462cc3e8a9fc62c1da14d710ed65d696e7dbdd8b8`。**283 冻结文件**逐项与 manifest 和固定基线 Git 对象相同。见 [包身份记录](../../.ergora/checks/ac3c3-runtime/r2/package-identities.json)。`git diff --check` 通过。

独立读取 [SDK 脚本](../../.ergora/checks/ac3c3-runtime/r2/sdk-journey.py)、[摘要](../../.ergora/checks/ac3c3-runtime/r2/sdk-journey.json) 及两份原 history：文件 SHA256 与记录相符；各 95 个事件，原始单 payload/type、六份 stage context SHA256、完整 admission、专用/旧 submit 区分、继承批准 signal 与完成事件均从原 JSON 解码核对。13.87 秒、本地 Temporal/SDK 完成和各自重放成功来自作者实际运行记录；本审查者未重新启动服务或重放。脚本在 finally 终止服务并检查端口，记录 `server_stopped=true`。

已读取原日志：四套源码 **50 passed / 31.90 秒**；submission/approval/composition 三套 **106 passed / 409.25 秒**；R2 四套安装包 **50 passed / 30.30 秒**，均零 skip。误拼 suite 的 `exit 4 / no tests ran` 单独保存，没有计入通过。本审查者未重跑这些套件或进行安装。

上述 SDK 活动使用原 validators 和明确的 SyntheticAdapter；无真实 owner receipt、Agent 或可信候选核验，不能登记为正式 v2 执行通过。真实自身 R2 模板用时 128.73 秒，结果为 request-changes；其发现已复现，但完整输入/原生读取/结果的独立身份审计尚待补。CR1 新候选 CI、精确 scope/普通提交推送和同片远端终结尚未形成，不借用前片 CI。修后必须重核相关包身份、坏输入合同、两项 finding 和最终自身审查；原 R2 正常旅程保留原身份，不自动变成修后验收。

初审计数：**Standards 1 项非阻塞 P3（ST1）；Spec 1 项阻塞 P2（SP1）。**

## R3 同片复核与新增 SP2

范围增加原持久信封所有者 `src/ergora/task_envelopes.py`。该所有者先拒绝非对象 document，再核 graph instance path 为非空、唯一字符串后建索引；workflow 不增加宽泛异常捕获。三条 resealed 坏输入回归在保留 R2 包全部为红，见 [原红例](../../.ergora/checks/ac3c3-runtime/r2/malformed-red.log)。测试可选 SDK 检查已移到模块第 13 行，在 fixture provider 导入前跳过；Standards 子审查确认 **ST1 关闭**。

独立重新计算 R3 的源码/wheel/安装/记录，**366 文件全部相同、283 冻结文件等于基线**；新 wheel SHA256 为 `845dde7fbc2d389558c55420f1c2e4c7d02c5e65618f5a725fc6a8891ff05b5a`。源五套 **90 passed / 44.95 秒**，相同安装包五套 **90 passed / 47.47 秒**，零 skip，均核原日志。没有把 R2 的 50 项当修后测试。

读取 [R3 正常 SDK 旅程](../../.ergora/checks/ac3c3-runtime/r3/sdk-journey.json) 和两份原 history：各 95 事件、六 context、原始 payload/type/context 摘要、submit 区分和完成事件全部相符；12.02 秒旅程及重放是作者实际记录，仍使用 SyntheticAdapter。另读取 [实际坏输入 SDK 脚本](../../.ergora/checks/ac3c3-runtime/r3/sdk-invalid.py)、[结果](../../.ergora/checks/ac3c3-runtime/r3/sdk-invalid.json) 及三份原 history：numeric-path、duplicate-path、null-document 各 **5 事件**，最终为 `WorkflowExecutionFailed`，其原始 `applicationFailureInfo` 明确为 `ContractViolation / nonRetryable=true`，**零 ActivityTaskScheduled**。该旅程 8.31 秒、服务已结束；本审查者独立核原事件而未重新启动服务。由源码、红例及实际终态证据，**SP1 在 R3 关闭**。

**CR1-SP2，P2，阻塞：深层 graph JSON 的解码异常逃过永久拒绝。** [R3 自身原报告](../../.ergora/checks/ac3c3-runtime/r3/hosted-review/codex-review.md) 指出 `task_envelopes.py` 原第 118 行的 JSON 解码；相同“完整v2输入核验”合同受影响。将完整 snapshot 内 `composition.json` 改为 10,000 层数组的合法 JSON，共 20,001 字节，并重算 manifest 与 envelope 摘要，前序身份/容量检查通过，`json.loads` 却抛出 `RecursionError`。本审查者在固定 R3 安装上分别对 `unwrap` 与 workflow `run` 独立复现；后果同为 workflow task 反复失败，而不是不可重试合同终态。

最小修正为只在原所有者的 graph 解码处将 `RecursionError` 转成 `ValueError`，保留 cause，由现有 workflow 拒绝路径处理。作者已按此修正并给原参数化测试增加第四个 deep-graph 分支；Spec 子审查以只读探针确认原 owner 抛 RecursionError、修后 owner 抛 ValueError，两者仍接受合法原信封。此为源码级处置，**SP2 仍待 R4 包和实际 SDK 终态核验**，不将它回写成 R3 通过。

## 两轮真实自身材料的独立审计

除阅读模型报告，还逐项核对 R2 与 R3 原材料：SQLite `agent_runs` document 的 run/input/prompt/result 身份，完整 protocol prompt，原始 `result.json` 字节 SHA256 和 decision，完整输入副本的 13 文件 tree identity，原 manifest 与输入共有的 10 文件内容，以及 attachment 中七个文件的完整正文和身份。所有生产正文另与各自安装包核对，不以当前已修工作树替换旧轮附件。源 definition libraries 被删除后的原 manifest 与保存输入仍完整。

R2 实际 run `c272578237ce4588b9d869366e54c512`，128.73 秒，**request-changes**；附件 **48,482 字节**，SHA256 `bbdc3e717aeff97f9aab71e5e874618f9671ab0f277864fb68b1b02dd38ff2ac`。原生 stdout 的已完成 MCP read 实际返回全部正文，`offset=0 / next_offset=null`，内容逐字节等于附件。它提出 SP1。

R3 实际 run `a2589de162294e538e547cd725cccca8`，153.57 秒，**request-changes**；附件 **50,622 字节**，SHA256 `25e43f7e44607c86e20d51a09fcb1d1383c85a2449df765a98a169a05b2357d8`。原生 stdout 有三页连续读取 `0 → 18000 → 35000 → null`，并另有一次完整重读；四次返回各自 byte slice、整份 digest 与正文均核对相符。它提出 SP2。原生工具日志与预检日志分开保存；没有从模型声称“读完”推导实际读取。

以上审计只证明真实材料交付、记录身份与这两轮 request-changes。R4 自身审查、修后包/SDK 及最终精确交付仍待形成；不据此前运行批准完整正式 executor。

## R4 最终本地出口

**Standards：通过。** ST1 的模块级可选 SDK 检查仍在 fixture 导入前。两项异常修正均留在持久信封所有者：图路径先验证再索引，只有 graph JSON 解码的 `RecursionError` 转换成 `ValueError`；未增加全局异常吞没、备用解析或重复权限引擎。Standards 子审查独立复核这次小增量，无新增判断项或硬性标准违规。

**Spec：通过。** SP1 的数值/重复 path 与非对象输入、SP2 的深层 graph 均已由最终实际 SDK history 证明永久拒绝。新的第四个回归先在 [原 R3 包为红](../../.ergora/checks/ac3c3-runtime/r3/deep-graph-red.log)，其后三轮材料分开保留。所有已述 CR1 输入/原始身份/继承调度/上下文容量/专用 submit 合同保持；公开 v2 start/status 仍关闭。**ST1、SP1、SP2 全部关闭，无剩余源码阻塞项。**

独立重算 [R4 包身份](../../.ergora/checks/ac3c3-runtime/r4/package-identities.json)：源码、wheel、非 editable 安装及记录的 **366 文件**集合和内容全部相同；283 冻结文件逐一等于 manifest 与 e9 基线 Git 对象。最终 wheel SHA256 为 **`bfd98f933ba6622ca6d9d4caf6705174f1ec706a5fcf552a474c6d58daf105bb`**。最终五套源码 **91 passed / 46.31 秒**、同五套安装包 **91 passed / 48.01 秒**，零 skip，已核两份日志；本审查者未重跑套件。

独立解码 [R4 正常 SDK 摘要](../../.ergora/checks/ac3c3-runtime/r4/sdk-journey.json) 对应两份原 history：各 95 事件、六 context，单原始 payload、完整 admission、所有上下文摘要、两类 submit 与完成事件均吻合；本轮实际旅程及重放记录为 12.55 秒。再核 [R4 坏输入 SDK](../../.ergora/checks/ac3c3-runtime/r4/sdk-invalid.json) 四份原 history：numeric-path、duplicate-path、deep-graph、null-document 各 5 事件，全部原生终态为 `ContractViolation / nonRetryable=true`，零活动调度；前三个原始 payload 的 manifest/envelope 摘要再次独立重算有效，null 使用 SDK 的 `binary/null` 编码。坏输入实际旅程 7.48 秒，两个服务结束。这里核的是实际原事件，非只读 `run` mock 推论；正常阶段仍使用明确合成的外部 Adapter。

最终真实自身 run **`c8effe5eccad46b49b0a709e7c09e4f3`**，132.03 秒，**approve**。独立重算其 13 文件输入副本、manifest 及相同源文件；核 SQLite run document、protocol prompt、原始结果和七个保护文件与当前源码/测试均一致。附件 **50,938 字节**，SHA256 **`c0285e261a3de5f61bd9253780c03663ea5fb9499a5124dce83cb2d6ad8aae6a`**。从原生 stdout 验到一次完整 `0 → null` 读取及六页重读 `0 → 10000 → 20000 → 30000 → 40000 → 50000 → null`，七次返回的 byte slice 与整份内容摘要均相同。没有以模型的“读完”陈述代替原始读取。

[公开最终身份](evidence/2026-11-09-cr1-self-review-identity.json) 与原 R4 JSON 全同，[公开原始结果](evidence/2026-11-09-cr1-self-review-result.json) 与实际 result 文件字节全同；[公开历史](evidence/2026-11-09-cr1-self-review-history.json) 的 R2/R3/R4 三条各与原轮一致，保留两个 request-changes。最终结果是 supplied-source 静态审查，未声称执行测试、原生批准、Agent 或可信候选验收。

本地完整改动集合为 **14 文件**：初始九文件、`task_envelopes.py`、本报告及三份公开自身收据。独立核对 [预出口范围](../../.ergora/checks/ac3c3-runtime/review-final-scope.json) 与实际 tracked/untracked 集合和全部内容摘要一致；当时 scope SHA256 为 `3c53f1c18df1635e0d7ec543a00d489360a5e6f803bb5783b6516ea78d499e30`。本段和作者后续状态追加后需刷新文档 scope/static，生产/测试身份不变。`git diff --check` 通过，已有本报告本地链接核对零缺失；最终文档静态检查由作者刷新。

CR2 下一步的独立队列/`requests-composition-v2` 路径和同版本 fence 扫描已明确列为待实施；不把这些设计文字当当前接线。CR1 本地出口通过后，尚须普通精确提交推送、新候选必要双 OS CI 与同片即时远端核验。完整 worker、可信 executor/owner 批准、verify 投影迁移及 AC4 按后片验收；本次未重启服务、调用模型、安装依赖、修改生产/测试或进行远端写操作。

最终本地计数：**Standards 原 1 项 P3 已关闭；Spec 原 2 项 P2 已关闭，两轴均无未解决 finding。**

## 精确候选与同片交付终结

本审查者继续核对已普通推送的固定候选 **`77f93302c53f2d619bf7f84ff9dd23905f754b41`**，唯一父为原基线 `e9c3484fbfa0cfb8cf0737c4d930b5ec176992d3`。CR2 已在本地推进，本轮只读取固定候选 Git 对象及原 R4 证据，没有将当前工作树的新运行桥实现计入 CR1。

[最终 14 文件 scope](../../.ergora/checks/ac3c3-runtime/review-final-scope.json) SHA256 为 **`5f5d71c734a38dfe37483171261a4b29e02e2b0e4afaf92232be9598951f14e6`**。提交相对唯一父的文件集合精确等于 14 项，全部 blob ID 和内容 SHA256 与范围记录相同；本报告在候选中的版本仍保留当时的本地出口及待交付状态。本次终结追加归原片归档，不改变候选身份。

从候选 `git archive` 直接取得的 **366 个包文件**，逐项与保存的最终 R4 wheel、非 editable 安装及身份记录完全相同；wheel SHA256 仍为 **`bfd98f933ba6622ca6d9d4caf6705174f1ec706a5fcf552a474c6d58daf105bb`**。283 冻结文件逐项等于 manifest 和原基线 Git 对象。七个实际自身审查保护文件均与候选对象相同，六份 Markdown 的最终静态摘要也逐项绑定候选，**265 本地链接 / 75 CLI parser / 零缺失**保持。父→候选 `git diff --check` 通过。见 [固定 Git 对象核验](../../.ergora/checks/ac3c3-runtime/reviewer-r1/final-git-object-results.json)。

独立重新 GET 官方 [Portability CI 42532654631](https://github.com/626619403/Ergora/actions/runs/42532654631)、完整作业批次及两个作业页面。运行绑定完整候选和 `portability.yml`；批次为 **`totalCount=2 / hasMore=false`**，没有以页面先显示的单个作业代表整批。最终整体 **Success**；[Ubuntu / Python 3.11 作业 128890052698](https://github.com/626619403/Ergora/actions/runs/42532654631/job/128890052698) 与 [Windows / Python 3.12 作业 128890052478](https://github.com/626619403/Ergora/actions/runs/42532654631/job/128890052478) 均为 **completed/success**，未发现失败、取消或超时步骤。候选 workflow 所需七项步骤逐项核对如下：

|必要步骤|Ubuntu|Windows|
|---|---|---|
|Build and install wheel|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052698/logs/4)|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052478/logs/4)|
|Packaged reference identity|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052698/logs/5)|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052478/logs/5)|
|Native application regression|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052698/logs/6)|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052478/logs/6)|
|Windows PowerShell 5.1 installer and upgrade|—|[success](https://github.com/626619403/Ergora/commit/77f93302c53f2d619bf7f84ff9dd23905f754b41/checks/128890052478/logs/7)|

完整官方页面、批次、各内容 SHA256、步骤完成时间及各轮进行中观察均独立保存。最终 [CI 与远端回执](../../.ergora/checks/ac3c3-runtime/reviewer-r1/ci-42532654631/final.json) 的官方核验结束于 **2026-11-08 23:07:57.599879 UTC**；**23:07:57.600222 UTC** 随即启动只读 SSH `git ls-remote`，于 **23:08:01.795165 UTC** 收到 `exit 0`：`refs/heads/refactor/architecture-foundations` 返回完整 **`77f93302c53f2d619bf7f84ff9dd23905f754b41`**，与候选一致。连接配置及凭据未写入公开回执。本次核官方步骤状态与完整候选日志链接；未取得的日志正文没有被用于推导额外测试项数。

**CR1 精确交付终结通过；Standards / Spec 通过，三项 finding 全部关闭。** 本轮没有提交、推送、安装、模型调用或应用套件重跑。完整正式 v2 worker、executor、owner 批准、verify 迁移及后续嵌套执行继续按 CR2/3/4 与 AC4 各自范围验收，不从本候选继承未实施能力。
