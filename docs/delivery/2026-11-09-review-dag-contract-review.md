# AC4.3a：只读审查 DAG 合同独立设计评审

评审者：Codex `/root/review_dag_contract_review`，fresh context；只取得原始要求、固定基线、文件范围与实际验证位置，没有实现会话。日期：2026-11-09。源码基线与评审开始时 HEAD 均为 `91b09683aac9481d07a6cd1d2ea8da9777b25563`。

## 范围与两轴结论

实际执行 `git diff 91b09683aac9481d07a6cd1d2ea8da9777b25563` 和 `git status --short --untracked-files=all`。初始 tracked 差异只有 [PLAN](../PLAN.md) 与 [AC 总计划](../plans/2026-11-08-agent-composition.md)，各两行状态更新；新增公开内容是 [端口合同](../plans/2026-11-09-review-dag-contract.md) 和 [本片交付记录](2026-11-09-review-dag-contract.md)。末次 scope 核查另见 [前片评审报告](2026-11-09-advisory-runtime-review.md) 与 [前片交付记录](2026-11-09-advisory-runtime.md) 的交付记账，完整 diff 已读，只登记前片精确对象、CI42574624398 和 06:56:50.878067 UTC HTTPS 远端身份，没有新实现行为或借其 CI 验本片。本报告属于同片评审记录，最终公开范围共 7 份文档（4 tracked、3 untracked）。生产、schema、依赖及 CI 没有修改。`.ergora/checks/ac4-dag-contract/` 被 ignore，其检查原件只作本地证据，不能当成公共交付文件。

- **Spec：设计门禁通过，DG-1/DG-2 已关闭，无开放阻塞 finding。** 最终合同已明确原 transport 来源保证及活动期/关闭后核验的适用范围。六阶段、owner 计划批准、原 candidate/receipt/unknown 恢复以及 Temporal/monitor/账本所有权保持；AC4.3a 只定设计，AC4.3b 才纵向接通。未把前片 CI 或静态图编译当成本片 DAG 运行证据。
- **Standards：通过本片设计范围。** 选用已有 Input Interface、编译器、review Workflow、Executor、FileAdapter 和原证据读取，未提出第二调度器、全局插件注册器或没有消费者的生产格式。容量与 MCP 接入仍有后片必须实证的限制，见下文。

本片不实现任意执行者、三领域默认组合或页面；这些仍是 AC4.3c/AC4c/AC5/AC6 的明确依赖。这里的设计通过不能替代它们的验收，也不等于新 v4 已可创建或执行。

## 合同发现与处置

### DG-1 · Spec · P2 · 原运行来源不能仅由 job/receipt 推导（已修订）

位置：[合同“数据值和 provenance”](../plans/2026-11-09-review-dag-contract.md#数据值和-provenance)，初稿第 23 行，最终修订第 41–45 行。

初稿要求拒绝“另一次 run”，却没有交代原收据没有 Temporal run_id。源码中，冻结 `dev_platform/workflow.py:78` 的 context 不含 run_id，job_id 只由 task_id 和 stage 派生；`agent_platform/executor.py:34` 的 claim 对相同 job/context 有意返回原 session。因此，两个相同 task/stage/context 的记录不能只靠这些字段证明来自不同 Temporal run；为了区分它们而改写旧收据，又会破坏原恢复合同。

最终合同已落实最小修正：明确保持原 transport 来源保证，正式 start/resume 由 `reference_task_submission.py:174` 的 lookup/owner 检查钉住原 submission/memo；受信任 Workflow 只从自身已完成 results 构造预期前驱；Executor 核 immutable published request/context/receipt、admission/candidate/stage/SHA 及原 claim。证据读取与关闭后对账再核指定 history。允许的原 job/context 恢复保持幂等，不给原 receipt 补 run_id，也不默认增加每叶 Temporal 查询或另一份来源账本。

后片必须有两个相反验收：相同 task/admission/candidate 但不属于原 submission 的运行不能取得正式归属或成为原证据；原任务 worker 停启后仍恢复相同 request/job/claim，调用次数不增加。`agent_runs.py:141` 的调用 UUID 和 `task_mcp.py:78` 的 scope run_id 不是 Temporal run_id，不能替代原运行归属。

没有找到既有信任范围内必须新增每叶 live-history 查询的可达场景：另起同 task/stage/context 的裸 run 不会获得原正式 submission 归属，字节相同的稳定 job 复用是允许恢复，变化的 context 会被 immutable publication/claim 拒绝。若以后要求“任意不同 run_id 都禁止复用”，那是新的保证，需要单独设计；不能在本片文档中无意承诺它。

### DG-2 · Spec · P3 · 终结输出缺少可判定选择规则（已修订）

位置：[合同“调度、汇合与停止”](../plans/2026-11-09-review-dag-contract.md#调度汇合与停止)，初稿第 31 行，最终修订第 53 行。

现有静态 Workflow 可以声明多个具名输出，任务选择只有 review_instance，没有输出选择器。若选定子树同时导出一个 all-join 和一个单叶输出，初稿的“选定输出”不能确定哪个是终结输出。现有 `task_envelopes.review_members():188` 明确要求选定子树恰好一个输出。

最小修正已经写入合同：选定 review 子树仍只声明一个终结输出，不增加选择器；投影链终点是显式 all-join；嵌套子 Workflow 可以有多个具名输出。验收节点同时要求拒绝多终结输出，保持了较小的 Interface。

### 来源复用的适用边界 · Standards · 防止误接关闭后 history 检查

位置：最终修订合同第 43–45 行；`reference_task_reconciliation.py:28` 的 `_Inspection.jobs()`。

采用 DG-1 的原所有者是正确方向，但 `_Inspection.jobs()` 当前只接受关闭后的 Temporal 状态：第 31–33 行映射终结状态，第 71–72 行要求 history 最后一个事件是对应终结事件。在 REVIEWING 期间直接调用它，会在 RUNNING 状态拒绝，或让后继审查等待本 run 终结。评审曾提出沿原 history 读取证明来源，作者据真实信任范围将其进一步收窄为上述 transport + 可信 Workflow + 原件核验；无需为此引入新的逐叶网络保证。

最终合同已明确 `_Inspection.jobs()` 继续用于关闭后的恢复/对账，不由正在拼输入的 Executor 调用。活动期的前驱来自可信 Workflow 已完成 results；`reference_task_evidence.py:38` 的当前可见 history 指定事件读取仍是已有证据入口。这里是对拟议接法适用范围的澄清，没有发现新的生产代码问题。

## 已核实的设计可行性

|关注项|源码事实与设计判断|
|---|---|
|显式协议与兼容|`tasks._composition()` 冻结整个 manifest 和成员；`reference_task_creation._Creation` 把用户定义与正式信封同时放入原意图；`task_envelopes.wrap()/unwrap()` 当前只支持 v2/v3。显式 review_protocol 决定新 v4 可放在这些现有所有者中。无字段时不补默认键、不改变原版本选择；不能仅因有 review_requirement 就把旧图升级到 v4。|
|三类关系|`workflow_definitions._Compilation` 分别保存 parent、局部 depends_on 与 inputs/outputs；`_materials()` 只沿结构链完整继承，`_within()` 检查子权限上限。数据前驱作为产物数据，不扩大其调用者权限，符合现有模型。共同新修订仍沿原不可变定义/manifest，不借端口提权。|
|嵌套与重复引用|现有编译器已按实例路径展开引用，端口绑定相对直接结构父级解释。运行值使用路径和端口地址能区分同一模板的不同引用；Workflow 输出保持别名投影，join 对每个依赖的每个输出保留地址，不能按数组位置或定义 ID 合并。|
|串行覆盖与原意见|原 `review_members()` 的直接根输入限制不支持新图；它的旧 coverage 只追端口，不能当作已完成新合同。新设计要求执行依赖与端口来源的传递覆盖，再把全部成员的原 receipt/职责/意见放入原聚合，能保留只作控制前驱的早期意见。|
|可信意见与原件|`ReviewRequirementsActivities.poll()` 核原 FileAdapter、可信 decision、invocation/result 摘要及候选；`Executor._composition_request()` 当前只读 plan/verification 两类依赖，并在真实读取时再核字节。新端口输入应延伸这个位置，不在模型结果中接受自报 job/候选/原件身份。advisory request-changes 的原 FAILED receipt 与执行失败继续分开。|
|并发与会话|现有 review 已有完整祖先 semaphore；原 `DevelopmentWorkflow.units()` 用 FIRST_COMPLETED 驱动就绪任务，提供不整层等待的现有调度模式。新 DAG 沿原 Workflow 使用这些原语即可。原 claim session、每调用独立目录以及 Codex ephemeral/Claude no-session-persistence 是当前隔离依据；后片仍须验证串行前后继与并行兄弟不复用可变会话。|
|取消与恢复|原 stage、StopWork、fence、monitor 和 reconcile 继续是所有者。新 DAG 不能在收到结果后清掉取消标记，也不能为虚拟 Workflow/join 建新 job。确定性路径与来源表进入原活动输入；重放读取原 history，不重新查询活动库或重派已完成模型调用。|
|更简单的已有方案|静态依赖验证已有 `graphlib.TopologicalSorter`，运行就绪/并发已有 Temporal、asyncio 及原 units 模式，版本选择已有 `_INPUTS`，后端选择已有 AgentBackend Interface，固定数据分页已有 task_mcp.ResourceView。没有证据需要新图框架或依赖。静态 levels 可供预览，不能在运行时变成无关分支间的全层屏障。|

## 性能与能力边界：留给 AC4.3b 的实证

**共享值可以避免展开，实际产物正文仍须计费。** 评审执行了一段仅使用 Python 标准库的纯数据推导，没有调用 Ergora 运行实现：目标 `structure → {correctness,test-value} → gather` 若只数末端端口得到两个叶子；加执行前驱闭包得到全部三个叶子。24 层共享 join 示例只有 26 个不同值，树状复制会出现 242,785 个值。这支持合同采用有界共享表、先计量再构造，不能用无界递归展开后检查最终 JSON。

共享端口地址也不能自动消除不同审计产物内部重复的字节。原 Executor 第 290–292 行同时保存 composition-materials 和完整 composition-prompt；若后片把前驱这两份正文完整嵌入后继，并再次输出这两份审计正文，串行链会快速放大。以 4 KiB 根材料和这两类正文作示意，第 7 个输入为 579,847 字节，第 8 个为 1,262,215 字节；这不是实际运行 benchmark。现合同允许超限明确停止，因此不是已证实的合同违例。最终合同第 61 行已增加此边界：后片固定 result 所指的产物集合及共享表达，验证接近容量上限的串行审计链，记录实际输入、构造前拒绝与内存；不能以端口表去重为理由声称全部正文都已线性化。

**固定 MCP 读取已有实现，动态端口接入尚无消费者。** `task_mcp.freeze():50` 现在只冻结结构祖先资源，scope v1 的 sources 也限定定义资源来源；`ResourceView` 可复用，但它不会因为新图存在就自动暴露前驱原产物。最终合同第 63 行已明确最小方案可先把完整端口表与正文放入真实 prompt，同时保持原 MCP 的结构资源范围；如要在 MCP 中访问端口原件，应由原调用者显式冻结固定 URI、摘要和 provenance，保留旧 scope 身份，实测全量分页可读。两种方案都不能只提供摘要后宣称已读全部正文。

## 检查及证据范围

- 读取项目 AGENTS、当前 PLAN、原始要求、maintainable-project-delivery/independent-review brief、codebase-design，以及 AIHERO 索引中的相关 code-review 两轴规则。
- 直接读取 `workflow_definitions.py`、`tasks.py`、`task_envelopes.py`、`reference_inputs.py`、`reference_task_creation.py`、`reference_workflows.py`、`reference_executor.py`、`reference_task_submission/runtime/evidence/reconciliation.py`、`task_mcp.py`、`agent_runs.py`、后端调用和原 FileAdapter/DevelopmentWorkflow/claim；生产源码始终只读。
- 核看作者静态检查原件：初轮 4 文档/60 链接无缺失、79 条已有 CLI 语法可解析；目标静态示例 5 instances、`[structure] → [correctness,test-value] → [gather]`，脚本断言 executable=false，manifest 复核一致。检查目录被 ignore，记录不等于公共 DAG 示例已发布。
- 本评审独立执行上述纯数据推导、实际 git scope 和 `git diff --check` 检查；最终逐份检查 7 份文档的 100 个相对文件/锚点，零缺失，文本结尾/空白检查通过。最终合同文件 SHA256 为 `ce9d5a37fa0c398cce2c7223c915ede5fd9c83d53684beaffd478a5f406d873e`，源码 HEAD 仍等于固定基线。没有运行新模型、服务、pytest、安装或 Git 发布；前片 CI 未被采用为本片证据。主代理另记录最终 CLI 静态核验及交付状态。

## 设计门禁与下一实现片

最终来源表述、单终结输出及两项容量/能力边界已复核，AC4.3a 的 **Spec、Standards 设计门禁通过**；生产 v4 及 DAG 执行仍未实现。主代理继续记录最终静态检查、普通交付与本片精确远端/必要 CI，不继承前片结果。AC4.3b 保持完整纵切片，按以下节点逐项登记真实证据：

1. 同一次实现中接通显式协议、创建意图/信封、版本 Input、queue/request-root 和旧 worker 拒绝；验证缺字段的 v1/v2/v3 原字节/路由/历史不变。不要先公开没有执行消费者的 v4。
2. 混合嵌套、多具名端口与重复模板实例；单终结输出、传递 all-join 覆盖、控制前驱原意见保留；拒绝未知端口、遗漏叶子、未执行外部来源与多终结输出。
3. 原 submission 归属、可信 Workflow 的已完成前驱、候选/receipt/context/原件再次核字节、完整祖先和前驱正文实际入 prompt/固定 MCP；运行失败不能流出合格端口值，advisory 拒绝不改写原状态。覆盖共享 join 与串行审计容量反例。
4. 独立慢分支不阻塞已就绪分支、所有祖先并发限额、前后继/兄弟会话隔离、取消与结果竞态、unknown 清理及 worker 停启。原 request/job/claim 与实际模型调用次数共同验恢复，不能只看最终 approve。
5. 最终非 editable 包、283 冻结文件、真实 CLI/Supervisor/Temporal/evidence/离线 handoff、旧历史重放与进程清理；本片自己的真实模板审查和**新的** fresh-context 实现评审，普通交付后另核自己的 CI 与精确远端。

本报告及其发现处置属于 AC4.3a，不触发递归审查；后片实现需要新的审查者。

## 精确提交对象及文档门禁终核

已从 Git 对象独立核定本片提交 **`e9b682c4be4f19aa11aca4717a7f6d86050278ed`**，唯一父提交为固定基线 `91b09683aac9481d07a6cd1d2ea8da9777b25563`。实际变更恰为上文 7 份 Markdown；各对象的字节数与 SHA256 全部等于作者 `scope-precommit.json`，该记录 SHA256 为 `e6cf169818ce8c3843b248956b1bf8fd44e54340aa0b628b6be19785f9db6299`。实际 Git 对象 diff SHA256 为 `df328ea0af47dc9b61021b7046020b8f427f1182e78d37bb63c2885955eb03bf`。作者 `scope-precommit.diff` 只含当时 4 份 tracked 文档，各段逐字节等于对象 diff；另外 3 份新增文档已由 Git 对象及完整 JSON 清单逐份核验，没有把这个 tracked-only diff 冒称为完整 7 文件差异。

提交内本评审报告 SHA256 为 `21584a305fd890c99b2dafc35f50e17c7977d8ba1309e2acfe65a3a98260540b`，逐字节等于独立批准稿。合同对象 SHA256 为 `1ba55e4ca5a9b0b38212b9d5a04242cc9745f18a0fb4c885cdf441f236fbca9b`；只将第 3 行“设计在途”登记为“设计门禁通过”，并在第 75 行追加本评审链接与 DG-1/2 关闭状态。将这两行还原后，SHA256 恰为上文独立批准合同的 `ce9d5a37fa0c398cce2c7223c915ede5fd9c83d53684beaffd478a5f406d873e`；合同语义没有扩大。

两份计划及本片交付记录的门禁、下一步与静态结果记账已逐行检查；前片交付/评审记录仍只登记前片精确对象、自己的 CI 与远端身份。作者最终静态原件 SHA256 为 `e6e24f6c9f9f1cbc2942f20c844c64813e4b5979b286990fc4d2f6583517f3ce`，记录 **7 文档、102 个本地链接/锚点、79 条已有 CLI parser** 通过。该静态记录的 6 份文档哈希等于提交对象；剩余本片交付记录仅追加最终静态成功段，去掉该段可逐字节恢复其记录哈希。另直接读取固定提交对象及其目标文件，独立检查全部 **102 个相对文件/锚点**通过，文本结尾及空白检查通过，没有读取后片 WIP 替代被核对象。

## 本次 push 的 CI 适用范围及即时 HTTPS 远端

固定提交的 `.github/workflows/portability.yml` 与其父提交逐字节相同，SHA256 为 `81c168fdb140f44ccfdca497003e452355c9164a6ed6f8dfb8fa31729a1943ca`。实际普通 push 分支属于 `refactor/**`，但全部 7 个路径都命中该 workflow 的 `paths-ignore: ["docs/**.md", "README.md", "AGENTS.md"]`。因此本次纯 Markdown push 不要求新的 Portability 应用 CI；没有将父提交的 CI42574624398 成功替代本提交结果，也没有宣称本片跑过新的应用 CI。PR 或手动 dispatch 仍按原 workflow 各自规则处理。

本地对象、批准稿和路径过滤断言于 **2026-11-09 07:09:14.567406 UTC** 完成。随后从仓库外目录执行，移除继承的 `GIT_*` 配置变量、关闭全局/系统 Git 配置及凭据 helper，并核有效配置没有 URL insteadOf/pushInsteadOf 规则；使用明确 HTTPS URL 和完整分支引用：

```text
git -c credential.helper= -c core.askpass= ls-remote --exit-code https://github.com/626619403/Ergora.git refs/heads/refactor/architecture-foundations
```

查询于 **07:09:14.569443 UTC** 开始，**07:09:15.760037 UTC** 完成，exit 0、stderr 零字节；stdout 恰为 `e9b682c4be4f19aa11aca4717a7f6d86050278ed`、一个 TAB、`refs/heads/refactor/architecture-foundations` 和换行。stdout SHA256 为 `540190b7209ba7a717a135b43ecdca9769d88a03722316c884c53ea3ec51c320`。没有使用 remote 别名或本地 tracking ref 代替该次远端读取。

最终 **Spec、Standards 设计门禁、精确提交对象、适用的文档检查及即时 HTTPS 远端身份均通过**。本次追加属于该固定提交交付后的终核记账，不冒称追加正文已存在于被核提交；后片 AC4.3b 的本地文档或实现 WIP 不在本片批准范围内。
