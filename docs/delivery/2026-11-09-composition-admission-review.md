# AC3c.2 正式组合任务信封独立审查

最新本地结论：**固定 R4 范围内 Standards / Spec 均通过，五项 finding 全部关闭，无新增实证缺陷。** 已核 R4 安装包、历史恢复、标准库边界及真实自身审查的原生完整 MCP 读取/输入/结果身份。最终提交范围、普通提交推送、本片新 CI 和独立远端终结尚待形成并另行核验；以下保留 R1–R3 原发现及证据，不覆盖历史结论。

日期：2026-11-09。R1 本地结论（自身审查补证核验后）：**Standards 有 1 项 P2；Spec 有 2 项 P2，需修正后同片复核。** 本报告不等待尚未形成的本片 CI，也不将前片 CI 当成本片验收。

## 审查上下文与精确范围

审查者为新上下文 `composition_admission_review`，以 `fork_turns: none` 接收原始需求、合同、固定范围及实际验证交接，没有继承作者实现会话。先读原始需求、`AGENTS.md`、`docs/PLAN.md`、AIHERO 索引、AC 计划、ADR0004/0005 和合同/身份文档，再读实现及作者记录。应用 maintainable-project-delivery 的 independent-review、codebase-design 和 code-review；Standards 与 Spec 各由另一新上下文独立检查，受并发槽位限制顺序进行。

基线为 `539163e6f93539d7939181bc2ec7b7a60bd82bc4`，审查时 HEAD 与之相同，变更为未提交内容。固定材料：

- [13 文件范围及逐文件 SHA256](../../.ergora/checks/ac3c2-admission/review-r1-scope.json)，文件 SHA256 `82006aad7f4f535f1102794e73012547004ecefd00bd9020657b3950a8a5f796`。
- [tracked diff](../../.ergora/checks/ac3c2-admission/review-r1-tracked.diff)，SHA256 `c16a5bf21d6ef52bff1b9d3bd35527b8df58edbb9222bdf747cb37c238df90c6`。
- 完整文件快照位于 `.ergora/checks/ac3c2-admission/review-r1-files/`，包含全部 untracked 新文件；13 个快照均与范围 SHA256 匹配。

范围为 `README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/WORKFLOW_DEFINITIONS.md`、`docs/architecture/current.md`、本片交付记录，以及 `reference.py`、`reference_task_creation.py`、`reference_task_submission.py`、`tasks.py`、新增 `task_envelopes.py`、新增 `task-definition-v2.json` 和 `test_composition_tasks.py`。必要邻接读取覆盖原创建/提交、工作流编译、完整包核验、后端与权限所有者。

首次读取时 13 个工作树文件均匹配固定范围。审查中只有 PLAN 和本片交付记录追加状态，生产/测试仍匹配；结论绑定固定 R1 快照。邻接前片 CI 终结报告的变更不在本片范围。后续文档身份见私有 [live-drift.json](../../.ergora/checks/ac3c2-admission/reviewer-r1/live-drift.json)。

## Standards

初轮新上下文 Standards 轴无 finding；以下结构判断保留。随后作者真实自身审查提出持久化成员结构问题，本审查者在固定 R1 wheel 独立复现，新增 CA-ST1，不以原初审结论覆盖新证据。

所有权符合已记录职责：`workflow_definitions` 继续拥有完整包、图、资源继承与权限语义，`tasks` 拥有正式 review 子图选择及多样性决定；`task_envelopes` 只实现新信封身份、完整字节检查与读取投影。该标准库模块有创建桥、只读原生 reader 两个真实生产消费者，未为复用数量增设转发层。后端使用原工厂和共享合同，没有在应用层按厂商重复分派。

静态完整性检查、当前后端准入和稳定字节冻结承担不同职责，不能仅按重复遍历次数将其删除。`summary` 投影已核内容，不再次解码完整包。读取/恢复保留必要的外部输入、身份、容量和发布检查。新增回归主要经过原公共创建、读取、恢复接口，覆盖实际发布中断、未支持运行拒绝、多样性、字节损坏和容量合同，没有确认可直接删除的冗余测试组。

结构与性能判断只覆盖本片：完整包逐文件解码/哈希仍为有界线性工作；没有据此推导大规模列表、Windows 或模型性能。下述小样本测量不构成性能承诺。

### CA-ST1 · P2 · 持久化成员值与多样性结构未在信封所有者核验

位置：[task_envelopes.py:56](../../src/ergora/task_envelopes.py#L56)。违反 maintainable-project-delivery 的“Validate at the boundary that owns the invariant”及保留必要持久状态检查的要求：`unwrap` 核外层 SHA、manifest 字节和成员路径集合，却不核成员值、后端选择结构、mode/policy 对应或 diversity 内容。

可达场景是恢复或读取收到自校验和正确、内部选择结构错误的持久化 v2 文件。本审查者从合法 R1 创建文件分别将成员值改为 `null`、将 mode 改为 `native`（policy 仍 `text-only`）、将 binding 改为 `{"tool":null}`、将 diversity 改为不存在的 policy，重算外层 SHA 后，R1 的 show/list 均接受，列表 `errors=[]`。这不是声称普通创建会产生这些坏值，也不是要求 SHA 证明作者真实性；问题是自校验和不能替代新格式必要的结构和内部一致性检查。

证据：[r1-integrity-probe.py](../../.ergora/checks/ac3c2-admission/reviewer-r1/r1-integrity-probe.py)、[r1-integrity-results.json](../../.ergora/checks/ac3c2-admission/reviewer-r1/r1-integrity-results.json)。探针从未修改的 R1 安装包加载模块，`task_envelopes.py` SHA256 为范围内 `2d486523880e710e5da8163a34dd5b34ce65c8cfbb4bf085307c6806516abcfe`。

后果：reader 将畸形或自相矛盾的成员选择作为已核组合摘要展示；其他原持久合同已有结构检查，新信封缺少同层保障。最小修正是在标准库信封所有者核 v2 成员、后端选择、mode/policy、多样性记录的格式和内部关系，复用已经解码的冻结图。当前权限、图编译及后端可运行性继续由原应用所有者负责；不能在历史 reader/恢复中引入当前 catalog，未知历史 tool 名本身不构成损坏，亦不应硬编码 Codex/Claude 名单。

## Spec

### CA-SP1 · P2 · 选择更深 review 子图可绕过未执行外部依赖限制

原始范围要求“从单 task 输入、无未执行外部依赖的纯只读 review 子图”保存正式信封；本片合同亦写明“首片仅接受单 task 输入且不依赖未执行外部节点的 review 子图”。

位置：[tasks.py:61](../../src/ergora/tasks.py#L61)。当前只检查所选 Workflow 的直接 `depends_on` 和输入对象是否含 `node`。原编译器按立即结构父级保存输入映射，见 [workflow_definitions.py:245](../../src/ergora/workflow_definitions.py#L245) 与 [workflow_definitions.py:259](../../src/ergora/workflow_definitions.py#L259)，所以 `{"input":"task"}` 可能仍间接来自未执行的外部节点。

可达场景：根工作流有 `before` 和 `after(mid)`；`after.depends_on=["before"]`，且 `after.inputs.task={"node":"before","output":"result"}`。`mid` 内含 `inner(review-workflow)`，`inner` 的直接依赖为空、输入为 `{"input":"task"}`。直接选 `root/after` 会拒绝；选 `root/after/inner` 却成功，尽管其 task 仍取自子图外未执行的 `before`。所有 Agent 都是只读 reviewer，因此可以经过其他准入条件。

本审查者在固定 R1 源码、既有 Python 3.12 环境中运行受限离线探针，得到上述拒绝/接受对照，未创建真实 runtime、调用模型或连接服务。证据为 [probe.py](../../.ergora/checks/ac3c2-admission/reviewer-r1/probe.py)、[dependency-results.json](../../.ergora/checks/ac3c2-admission/reviewer-r1/dependency-results.json) 及 [接受的完整预览](../../.ergora/checks/ac3c2-admission/reviewer-r1/accepted-grandchild-preview.json)。独立 Spec 轴在未收到该怀疑提示前，从合同和源码识别同一缺口，没有重复执行探针。

后果：正式 preview/创建准入可封存超出本片支持范围的子图；该子图的实际输入无法仅由所选子图取得。当前执行拒绝仍有效，本发现不声称已产生远端执行。

最小修正：沿所选 task 输入和结构父链解析实际来源及前置依赖，直到根输入；拒绝仍依赖所选子图外未执行节点的选择。保持原工作流所有者的图/端口语义，补一个多层来源链行为回归即可，无需复制编译器或重跑全套。

### CA-SP2 · P2 · 创建恢复未完整绑定保存定义与冻结选择

原始范围要求“创建 preview/intent/publication/resume 复用原 owner、锁、revision 和 7 文件顺序”，并在源包、活动库及绑定变化后“恢复原快照”；每成员后端、政策及多样性决定属于该快照。

位置：[reference_task_creation.py:152](../../src/ergora/reference_task_creation.py#L152)。`validate_record` 只把保存 definition 的 `manifest_digest` 和 `review_instance` 与信封比较，没有对应 mode、backend overrides/reason 或 diversity；相邻旧合同字段则已经逐项核对 definition 与原执行 spec。

本审查者在 R1 wheel 私有状态目录生成完整合法 preview，将尚未发布 intent 的 definition.mode 单独改为 `task-mcp`，保持信封成员 `text-only`。`creation` 返回 `pending`，再向 `resume_create` 提供该次观察到的 intent SHA，成功发布；详情仍返回 `text-only` 成员，与保存 definition 矛盾。单独把 definition 的 override/reason 改为 Claude，或将 diversity 改为 `require-distinct`，同样被当作合法 pending 意图。证据同上述 [R1 完整性结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r1-integrity-results.json)。

后果：恢复记录不能确定操作者的完整保存选择与将发布的选择一致；被检查的定义、意图与正式信封之间出现两份互相矛盾的选择。最小修正是在原创建所有者从保存 definition、冻结图/成员及冻结 implementer 绑定核完整对应，并核默认 diversity 的规范展开；全部从保存字节完成，不能访问已删除源目录、使用当前项目 binding 或重算当前后端政策。此点与 CA-ST1 分开：即使信封自身结构完全有效，保存定义仍可与其不同。

除上述发现外，未确认范围内新增需求缺失或 scope creep。v1、原六阶段投影、旧运行器拒绝、提交拒绝和容量行为在所读调用链上符合本片设计；这不等于 AC3c.3/4 的批准或执行已经完成。

## 亲自核验与限制

- 核固定 13 文件及快照身份、基线和 diff；冻结参考目录相对基线无 tracked 差异。
- 独立逐文件比较记录中的 365 个源文件、安装文件和 wheel 成员，均匹配；wheel SHA256 为 `f5013c559a38c5370f238e175674c31aedb7de421a2ec80788395438f6088faa`。这包含原冻结内容的一致性检查，不代表重新运行原参考测试。见 [身份复核](../../.ergora/checks/ac3c2-admission/reviewer-r1/package-identity-results.json)。
- 亲自运行上述外部来源链红例。探针仅在 `.ergora/checks/ac3c2-admission/reviewer-r1/` 保存私有夹具/结果，未改生产或测试。
- 自身审查补证到达后，亲自在原 R1 wheel 运行 reader 结构与 pending intent 恢复红例；一次矛盾 mode 意图确实在私有目录发布成功，未连接远端。
- 亲自用 `-P -S` 导入并解包新信封，没有导入 jsonschema、PyYAML 或 Temporal。改变嵌入文件执行位并重算外层 SHA，仍因原 manifest 摘要不符而拒绝。见 [stdlib-results.json](../../.ergora/checks/ac3c2-admission/reviewer-r1/stdlib-results.json)。
- 同一标准库探针的 11 文件、24,373 内容字节、40,822 信封字节样本，连续 30 次 unwrap 合计约 9.995 ms，均值约 0.333 ms；该值只描述这份输入、此解释器和此机器。

没有重跑 pytest、整套回归、CLI/API 旅程、模型、服务、原生 Windows 或双 OS CI。作者报告的源码 79 项联合/最终新增 16 项属于作者验证。本审查读取到作者包身份、18 次 CLI 和 5 次 ASGI 记录；没有把这些操作登记为审查者执行。首次检查时 `wheel-regression.log` 尚无终结摘要，不能据此登记通过。

随后读取作者真实自身审查 R1 原文及元数据：run `7f62583e5343476bad188acec8e2f91a`，Codex，54,297 字节提供源码，附件 SHA256 `a7e62e9fcd65180aef7b8500cb2a478ea7705e475c887c29c684242cd95295ec`，结论 `request-changes`。其源文件身份与本报告 R1 对应；CA-ST1 和 CA-SP2 由该审查提出，再由本审查者独立实证，不能记作初轮两轴先发现。它对 CA-SP1 仅保留邻接源码缺失的疑问，该点由本报告完整邻接读取及离线探针确认。本片精确 CI/远端终结仍需各自实际证据，前片 539 的后来终结不改变本片 R1 结论。

R1 本地出口已形成：Standards 1 项 P2（CA-ST1）；Spec 2 项 P2（CA-SP1/2）。修正并复核后可更新本地结论；外部验收独立记账。

## R2 同片复核

仍由原新上下文审查者复核本片修正。基线仍为完整 `539163e6f93539d7939181bc2ec7b7a60bd82bc4`。固定 [R2 范围](../../.ergora/checks/ac3c2-admission/r2/review-scope.json) SHA256 为 `39af9a351cb4beb1ad7dbc3cc86cbefb6d9fc7b64e7f10d66da0a8a810ad2973`；[tracked diff](../../.ergora/checks/ac3c2-admission/r2/review-tracked.diff) SHA256 为 `d839bc5555f7523cc8c28f03c1574837fe0694d1410f5f21d18370b18d5c24eb`。13 个完整快照及初读时 13 个当前文件均匹配。复核源/安装/wheel 全部 365 项一致，原冻结参考相对基线无 tracked 差异；R2 wheel SHA256 为 `9fdcb718c27f34792618f1f8a12f3acde49739e3fc635b0f82d95f39b94e35c8`。见 [R2 身份复核](../../.ergora/checks/ac3c2-admission/reviewer-r1/r2-identity-results.json)。

### 原三项的修正结果

|发现|R2 独立证据|状态|
|---|---|---|
|CA-SP1|原直接及祖孙外部来源均拒绝；合法 `task → incoming → task` 重命名链通过。实现沿原编译图父链解析来源和顺序依赖，未增加第二图编译器。|原发现关闭|
|CA-ST1|原 null 成员、native mode、非字符串 tool，以及模式/政策、冻结请求、多样性坏值均被 show 拒绝，list 逐任务列出错误；历史未知 tool 字符串仍可读。|原发现关闭；更广保存格式问题另列 CA-ST2|
|CA-SP2|mode、绑定、reason、diversity 四类定义/信封矛盾均在 resume 拒绝，意图字节不变，没有任务文件或结果回执。|关闭|

亲自运行的 [R2 受限复核脚本](../../.ergora/checks/ac3c2-admission/reviewer-r1/recheck-r2.py) 与 [结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r2-recheck-results.json) 还包含合法恢复对照：移除源 manifest 和两活动库，将当前 implementer 改为 Claude 后，恢复仍为原 revision 1 / Codex 决定，七文件字节保持。上述操作全部限于私有审查状态。

修正保持 stdlib seam：`_binding` 是新信封私有结构算法，没有导入当前 catalog；创建 owner 从原保存 definition、成员和冻结 implementer 核选择。新增检查对应持久格式或原已实证失败，未增加无关参数检查。一次解码后复用图索引，祖先遍历和逐成员检查不重新解码全包；没有发现需要删除的重复完整校验。

相同 R1 小输入、同 Python 3.12 的 `-P -S` 解包 30 次，R2 合计约 9.394 ms、均值 0.313 ms，未加载 jsonschema、yaml、Temporal，见 [R2 stdlib 结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r2-stdlib-results.json)。该小样本不证明规模性能改善；源码中未增加额外的全包解码或扫描。

### Standards · CA-ST2 · P2 · v2 保存格式仍允许执行参数和矛盾能力声明

该点由 R2 自身审查补充，本审查者在未修改的 R2 wheel 独立确认。位置为固定 R2 的 [task_envelopes.py:46](../../.ergora/checks/ac3c2-admission/r2/review-files/src/ergora/task_envelopes.py#L46)、[policy 检查:90](../../.ergora/checks/ac3c2-admission/r2/review-files/src/ergora/task_envelopes.py#L90) 及 [恢复选择比较:183](../../.ergora/checks/ac3c2-admission/r2/review-files/src/ergora/reference_task_creation.py#L183)。

可达对照：相同新输入把绑定写为 `{"tool":"command","command":["echo"]}` 时，当前 preview 明确拒绝；但对 intent-only 记录同步修改 member 和保存 override，再更新内部 SHA，R2 resume 会发布。另将 policy 中 `write` 改成 `{"status":"enforced","effective":["workspace"]}`，不改其余只读成员合同，同样发布且详情原样显示该能力。

这里不应要求历史恢复重新通过当前准入；后端移除后仍可读是原合同。缺口是新 v2 持久格式没有明确、稳定的受限绑定字段和能力记录结构，`_binding` 接受任意额外执行参数，policy 则只要求 capabilities 是 dict，不能排除与本片只读合同相矛盾的声明。这仍违反格式不变量在其所有者核验的规则。当前 v2 运行拒绝继续有效，本发现不表示执行了 echo 或获得写权限。

最小修正是明确 v2 restricted binding 的保存字段（当前实际消费者为 tool/model/sandbox）和 restricted policy 的稳定字段/类型及只读能力约束，在 stdlib 所有者核验。保留历史未知 tool 字符串；后端特有真实能力、配置准入及权限图仍归原后端/工作流 owner。不能采用“读取时按当前厂商白名单拒绝”或“重算当前 policy 等于历史 policy”的修法，也不能把格式校验冒称来源真实性或当前可运行性证明。

### Spec · CA-SP3 · P2 · 恢复在发布后才触发单文件 1 MiB 限制

原合同保留正式单合同 1 MiB、意图 16 MiB，并要求超容量明确拒绝、不截断。固定 R2 的 [compile:117](../../.ergora/checks/ac3c2-admission/r2/review-files/src/ergora/reference_task_creation.py#L117) 检查逐文件容量，但 [load:190](../../.ergora/checks/ac3c2-admission/r2/review-files/src/ergora/reference_task_creation.py#L190) 调用的共享 `validate_record` 没有该检查。

本审查者确认两种 intent-only 反例：将 member reason 和 definition reason 同改为 1,050,000 字符，会在完整意图约 2.197 MB 时发布过大的 spec；更强对照仅增加 policy.basis、保持 definition 不变，意图为 1,146,881 字节，仍低于 16 MiB，spec 为 1,093,348 字节，高于 1 MiB。两例 resume 都先写出全部七文件和 result，再以 `File exceeds size limit` 失败，留下正常读取边界无法读取的正式文件。

证据：[R2 补充探针](../../.ergora/checks/ac3c2-admission/reviewer-r1/r2-additional-probe.py) 和 [完整结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r2-additional-results.json)。最小修正为将已有逐文件 `check_size` 移到编译与加载共用的记录校验，确保任何发布前先拒绝；compile 删除重复调用，保留 aggregate intent 限额及原七文件顺序，不截断材料。

### R2 验证边界与当前出口

以上两项来自作者真实自身模板 R2（run `a3e54e887d3c48669e2d5cb086da4433`，182.24 秒，82,359 字节附件，SHA256 `fe969bb5e8ddaefa9bea8092bba83a21349b1d434b219950915705dd8b98ecc1`，`request-changes`），再由本审查者独立复现。模型建议中的“支持后端变体”没有被理解为当前 catalog 白名单；本报告按稳定持久格式与历史准入分离作出上述限定。

作者在保留 R1 包运行新增 15 例得到 14 红/1 合法通过、R2 源码 31 通过，均属于作者验证。R2 的 CLI/API 日志已报告 18 CLI / 5 ASGI，本审查者未重跑；首次检查 R2 六套包回归仍无终结摘要。没有重跑全套测试、模型、服务、Windows 或 CI。本地审查已经可出具：原三项关闭，新增 Standards CA-ST2 与 Spec CA-SP3 两项 P2 待修；外部证据独立记账。

## R3 同片复核

固定 [R3 范围](../../.ergora/checks/ac3c2-admission/r3/review-scope.json) SHA256 为 `f273ab4436e2b758c511f77dc867071497d7af88cc53bc1b09e75c6762a766b6`，tracked diff SHA256 为 `fd4b5f1023cdf826b6564f5f938fa2c6bb5853861c5967edfc809a27d65b9b58`。初读时全部 13 快照/当前文件匹配；R3 安装/wheel 365 项匹配记录，wheel SHA256 为 `71066c9fafa1c57d4615a243ef7e968bd706d12c37109c5cf1f4ddb1d05d6419`。复核中作者在 R3 自审结束后推进 R4，仅当前 `task_envelopes.py` 和测试发生预期漂移，见 [身份与漂移记录](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-identity-results.json)；本节仍绑定原 R3 包/快照。

### Spec · CA-SP3 关闭

原 `check_size` 已迁入创建/恢复共用的 `validate_record`，先核七文件及 aggregate record，compile 不重复检查。亲自用 R3 包重放 R2 两个超限意图，均在发布前以 `task.spec.json exceeds its creation read limit` 拒绝，任务文件列表为空、无 result 回执。原 1 MiB/16 MiB 上限和七文件发布顺序保持，见 [R3 重放脚本](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-additional-probe.py) 与 [结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-additional-results.json)。

### Standards · CA-ST2 部分修复，policy 残余保持打开

原 command 额外绑定字段与 write/enforced 能力反例已经拒绝，均无任务文件/结果写入。v2 保存字段限制没有查当前 catalog，也没有重算历史 policy。原合法源独立恢复继续通过；历史未知 tool 可读。数字 `0` 代替 shell 的 `False`、text-only 保存 MCP 工具等坏记录也被拒绝，见 [R3 历史与类型检查](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-history-results.json)。

但固定 R3 的 [policy 校验:60](../../.ergora/checks/ac3c2-admission/r3/review-files/src/ergora/task_envelopes.py#L60) 仍只完整约束部分 capability：将 `backend_sandbox` 改为 `{"status":"enforced","command":["sh"]}`，或在 policy 顶层增加 `command:["sh"]`，仍可通过 intent-only 恢复并在详情返回。该剩余范围由 R3 自身审查指出，本审查者用 R3 wheel 亲自复现，两个案例均 `published` 且保存 result，见 [残余探针](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-policy-shape-probe.py) / [结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-policy-shape-results.json)。

这是 CA-ST2 的完整持久 policy 结构尚未覆盖，不重复登记一个新 finding。最小修正仍为限制顶层及各 capability 的键和值类型，核本版本 restricted 状态/有效值，拒绝执行字段及不支持的能力声明；不新增通用 schema engine、当前厂商表或权限图编译器。未启动 sh；v2 执行拒绝始终保持。

R3 修正新增的是同一 stdlib 格式所有者内的检查；没有新增完整包解码或厂商分派。相同小输入 30 次 stdlib unwrap 合计约 10.210 ms、均值 0.340 ms，未导入可选依赖，见 [结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r3-stdlib-results.json)。该值仍仅限这份输入，不宣称速度改善。

随后读取作者日志：R2 六套最终 165 passed / 零 skip；R3 四套 100 passed（50.85 秒）及 18 CLI / 5 ASGI 完成。这些不是审查者重跑，也不能覆盖 R4 修正。R3 自身审查 run `75c7fcd41f494941bcd30aa9a439167d`，127.30 秒，86,018 字节，附件 SHA256 `c516f0b13e90408c3b4fe7478ec1e79aa2f929d7303df8c65459ac97b5e7c628`，`request-changes`；本报告只把其实证后的 policy 残余计入结论。当前本地出口为：Spec 原三项均关闭，Standards CA-ST1 关闭、CA-ST2 待 R4；不把 R3 登记为最终包。

## R4 最终本地复核

固定 [R4 范围](../../.ergora/checks/ac3c2-admission/r4/review-scope.json) SHA256 为 `bd6677cee361c569b4b6579e0688ba3c8ec7dff574545f847d6aa2cb92d7443b`，tracked diff SHA256 为 `9079bcc26207b58482b906d5108ef6b26e005d5eb55c9f1c5a9423f96c1aad2d`，基线保持 `539163e6f93539d7939181bc2ec7b7a60bd82bc4`。该范围为原 13 文件及两个详细计划的状态更新，共 15 文件；全部固定快照匹配。R4 wheel SHA256 为 `6f3e2b168c3f2392e2c9dc6a9623c000c6749732f5b018fe852bca2a9dbb7f6f`，365 个源/安装/wheel 项逐一一致，冻结参考目录相对基线无 tracked 差异，见 [R4 包身份](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-identity-results.json)。

最终再核七个受保护生产/schema/测试文件，仍与 R4 快照及真实自身审查身份一致；其中 `task_envelopes.py` SHA256 为 `b1cbd200aea1e55330a373143d2fca5e9b26ea7a4a0cd357393296c0f259eefa`。初次复核后仅 PLAN、本片交付记录和两个详细计划继续更新状态，已读取这些差异；没有将后片运行桥设计纳入本片。最终将提交的 21 文件范围仍待作者固定，不以本节 15 文件范围代替最终范围。

### CA-ST2 关闭与历史边界

亲自在未修改的 R4 安装包重放原 R3 两个残余：`backend_sandbox={"status":"enforced","command":["sh"]}` 在恢复时以 `Formal composition capabilities differ from their restricted mode` 拒绝；policy 顶层增加 `command:["sh"]` 以 `Invalid formal composition member policy` 拒绝。两者均没有任务文件或 result 回执，见 [重放脚本](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-policy-shape-probe.py) / [结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-policy-shape-results.json)。完整 policy 顶层及各 capability 的键、类型和本版本 restricted 语义现在由 stdlib 信封所有者核验，CA-ST2 关闭。

该修正没有引入当前厂商白名单或按当前 backend 重算历史 policy。独立对照仍可读未知历史 tool 字符串；移除源 manifest 和两个活动定义库、把当前 implementer 改为 Claude 后，原 Codex / revision 1 决定照常恢复，七文件字节不变。v2 status 继续明确拒绝缺失的 versioned runtime bridge，见 [历史恢复结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-history-results.json)。这验证保存格式及其内部关系，不证明其来源真实性或当前执行授权。

|发现|最终状态|关闭轮次|
|---|---|---|
|CA-SP1：祖先外部输入来源|关闭|R2|
|CA-ST1：成员/多样性结构|关闭|R2|
|CA-SP2：保存定义与完整冻结选择|关闭|R2|
|CA-SP3：恢复发布前的单文件容量|关闭|R3|
|CA-ST2：受限绑定及完整 policy 格式|关闭|R4|

结构判断保持：新增检查在原 stdlib 格式所有者内，原应用拥有图、权限及当前 backend 准入；未新增厂商分派、通用 schema engine 或第二套权限图编译。没有新增全包解码遍历。亲自用 `-P -S` 成功解包原小样本，也成功读取此前真实 CLI 留下的 Claude + Codex + Codex、三个 task-mcp 成员信封，两个 backend 的 sandbox policy 变体均保留，未导入 yaml、jsonschema 或 Temporal。相同小样本 30 次 unwrap 合计约 10.313 ms、均值 0.344 ms，见 [R4 stdlib 结果](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-stdlib-results.json)；只限该输入、解释器和机器，不据此作性能承诺。

### 真实自身审查的原始收据独立核对

作者 R4 自身模板运行 `d53df3caa50545e78acb30f526f9205e`，Codex，收据标注推理模型 `gpt-6.1-sol` / high，165.10 秒，succeeded / exit 0 / approve。本审查者只离线读取其既有收据，没有重新启动模型或服务。核对脚本及完整结果位于 [r4-hosted-receipt-check.py](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-hosted-receipt-check.py) / [r4-hosted-receipt-results.json](../../.ergora/checks/ac3c2-admission/reviewer-r1/r4-hosted-receipt-results.json)。

从实际原生 `stdout.txt` 的 `ergora_task.read` 结果核对附件：首次 65,536 字节读取后，又按 offset `0, 12000, 24000, 36000, 48000, 60000, 72000, 84000` 连续读取八页，末页 3,998 字节、`next_offset=null`。逐页响应内容与原附件对应字节完全一致，八页合计 87,998 字节，SHA256 为 `5efb67acb97e83a2bd3ea31ed5ef3025589828406ca8049bd8d13c2da03c0798`。附件由本次七个受保护文件独立重建，并与原输入资产、运行快照资产及冻结 MCP scope 的 base64 内容比较，全部相同；不是仅依赖模型文本中“已完整阅读”的自述。

同时核实原生握手与成功 list/read 收据，scope 固定五个资源，其 SHA256 为 `8ff0566d29326d6f6caf5161db982871ebbeef3831adc0bec337473df63e4600`；原生 MCP 回执 SHA256 为 `204af5555309a28151841f3ece9f2ba81c503ec8a06b27526b5441a4511d5a2b`。用 R4 安装包的静态 `inspect_input` / `inspect_manifest` 检查完整输入、运行快照及 manifest，不调用当前 backend admission；活动定义库现场均不存在。输入摘要 `a50c8b601aaf6b9fdba9b4f1e2e80607c078755803806d22df2b9dce70dab245`、manifest 摘要 `f978812305085ee374a043a8fb9d6af54c7d9d04a36289a9c4916d80e7cb8d85` 均匹配收据。原输入、运行快照与协议 prompt 字节一致，SHA256 为 `a657f80e724432b3b7de9527dbb83efb74f575d34cd75940d37c0bae2604d9b0`。

只读查询 SQLite 的该 run 文档与 launcher 输出完整一致；原生 result 与协议 result 内容一致，结果 SHA256 为 `6f431858f8fcf63b280bcac3043fc7419a83fe0868de9b44e3f987b1e990b18f`。公开的[最终身份](evidence/2026-11-09-ac3c2-self-review-identity.json)、[最终结果](evidence/2026-11-09-ac3c2-self-review-result.json)逐项对应原始私有收据；[R1–R3 历史](evidence/2026-11-09-ac3c2-self-review-history.json)也逐轮对应原始身份和 request-changes 结果，没有覆盖原失败。

该真实自身审查只收到标记完整文件或基线相对 hunks 的供应源码；它未独立覆盖未提供的邻接图、权限、backend 和冻结参考实现，也未运行测试。完整 MCP 响应只能证明这些字节已交付，不能证明模型理解或提供 OS 隔离。本报告自身的邻接读取、离线反例和两轴结论独立记账；该 approve 不代表正式 v2 执行、批准桥或嵌套运行已完成。

### 验证归属与本地出口

作者 R4 安装包日志为 **46 passed / 零 skip，19.92 秒**，本审查者已读取终结摘要；作者另报告 R4 源码新增片 37 passed。R4 改动限于原 policy 格式校验及两条真实坏字段回归，未因其重复原未变运行套；R2 六套 165 项、R3 四套 100 项和 18 CLI / 5 ASGI 分别保留原包身份。本审查者实际执行的是各轮所链接的受限离线探针、身份比较、stdlib 解包及本节原始收据核对，没有重跑 pytest、CLI/API 旅程、模型、服务、原生 Windows 或 CI。

**本地出口：固定 R4 范围内 Standards / Spec 通过，五项 finding 全部关闭。** 最终 scope/普通提交推送、新双 OS CI 和即时独立远端终结仍待各自实际证据；当前本地结论不等待尚未创建的 CI，也不借用前片 CI 代替本片验收。形成后可在原报告追加，不回写历史 verdict。
