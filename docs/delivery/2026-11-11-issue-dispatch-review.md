# F7b.1-B1b 独立实现审查

日期：2026-11-11。审查者：fresh-context 独立 Agent `f7b1_source_publication_review`；未继承实现会话、未启动子 Agent。依据本项目 [AGENTS](../../AGENTS.md)、[B1 计划](../plans/2026-11-11-issue-dispatch.md)、[独立设计](../plans/2026-11-11-issue-dispatch-design-review.md)及 maintainable-project-delivery 的 independent-review brief，先读原需求、冻结 diff／新增文件及相邻调用，再核作者交付记录和原始证据。

**最终独立结论：Spec 通过，Standards 通过，开放 finding 0／0。** 初审发现的 Spec 一项 P2、Standards 一项 P2 和一项 P3 均已最小修正并复核关闭。最终 r3 安装身份、受影响检查、实际 CLI／HTTP 旅程、两轮自身模板原件及完整候选终核通过；结论限 B1b 本地出口，普通提交／远端／本候选自己的 CI 仍须另核。

## 精确范围

基线 `3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`，分支 `refactor/architecture-foundations`。初始冻结清单 30 文件，清单 SHA256 `c4a3cd728d9484985badd7636ed03f9a37a89a00fc92b2391a4f9e7d7f5d9392`，tracked diff SHA256 `10db848c7c5d399cde543b0c35b697d8e924542ee1df1b5b6f996705c59cbb07`。已逐件核清单字节数／SHA，并确认当时全部冻结内容等于工作区：

|类别|全部初始文件|
|---|---|
|产品与格式|`src/ergora/{handoff,issue_backends,issue_sources,issues,reference_executor,reference_inputs,reference_task_creation,reference_task_reconciliation,reference_workflows,task_envelopes,tasks,workflow_definitions}.py`；`src/ergora/data/schemas/{task-definition-v3,task-handoff-v1}.json`|
|测试|`tests/test_issue_tasks.py`、`tests/test_work_agents.py`、`tests/fixtures/work_delivery_acceptance.py`|
|文档|`README.md`；`docs/PLAN.md`、`docs/USAGE.md`；`docs/architecture/{current,contracts-and-identities}.md`；`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-11-{issue-dispatch,issue-dispatch-design-review,issue-mapping}.md`；`docs/delivery/2026-11-11-{issue-dispatch,issue-mapping,issue-mapping-review}.md`；`docs/delivery/evidence/2026-11-11-issue-dispatch-acceptance.json`|

相邻只读范围包括 `contracts / components / projects / bindings / reference_creation_process / reference_task_submission / reference_task_runtime / reference_task_reconciliation / reference_worker / review_dags / task_mcp`、原 native cli／workflow／adapter／ingress、相关原创建／worker／transport／handoff夹具和现有 Portability CI。B0 文档的精确交付追加只核其身份和范围表述，不重新宣称本评审直接完成 B0 的网络或 CI 操作。

最终完整冻结为 32 文件：上述 30 文件，加本报告与 `docs/delivery/evidence/2026-11-11-issue-dispatch-self-review.json`。最终清单 SHA256 `dab5143782c752d7fbc043d57a5c2b6a4e28d2d32517e2669d2a07814e1b6141`，tracked diff SHA256 `9e0f346f639e9d6da815afb61ba53a759229e855b3ea2965b2067c002ca2f7c8`；终核开始时 32 份冻结内容均与工作区逐字相等。后续仅本报告结论和相对链接回写，不改变其余 31 文件；产品／测试实际修改及后补文档均已纳入复核。本报告自身与后续出口状态记账不触发递归审查。

## Spec

### SP1／P2：发布前漏算已知的完整首阶段上下文

初始位置：[reference_task_creation.py](../../src/ergora/reference_task_creation.py#L199)。原新增检查只计算 `{'spec': spec, 'admission': envelope}`，遗漏首次 inventory 已确定的 task/job、SHA、stage、空 dependencies／authors 等字段。

独立反例直接读取实际 CLI preview，在内存中替换正文并重算 snapshot／envelope／selector SHA，调用真实 `_Creation.validate_record` 和任务叶提示编译器：880,781 字节 ASCII 正文通过全部静态检查，必要下界恰好 1,000,000B，pretty `task.spec.json` 为 1,006,339B、仍低于 1MiB；实际 `IssueSourceWorkflow.context('inventory', starting_sha)` 已有 1,000,393B，立即抛原 `StopWork`。这与动态产物无关，会发布首阶段已确定不能运行的任务。

最小修正已落在现有 v7 Input：`IssueSourceInput.inventory_context` 共享完整首次 context 组装及原限制，由 creation 和 v7 Workflow 两个真实生产调用点使用；其余阶段和 v1–v6 仍调用原实现。没有加预算、安全余量或复制六阶段调度。

独立只读复核：以真实 preview 的 spec／manifest 为输入，ASCII 和中文正文均可构成精确 1,000,000B 的完整 context，且与 `StageResultsWorkflow.context` 逐字段相同；增加一个 ASCII／中文字分别增加 1／3B，creation 拒绝，运行时转换为原 `StopWork`。原 880,781B 反例现在拒绝。最终 r3 的 28 项受影响检查和安装身份已核，SP1 关闭。

### 已核行为与保留范围

- 显式 definition3 selector 只读取本项目保存的 snapshot；当前选定配置与来源比较 provider、完整 API base/path、namespace 和本地 number／iid。native ID、完整正文及原响应 SHA／ETag／更新时间由 snapshot 内容摘要覆盖，首次观察时间另由 envelope 覆盖。无关 token 引用／Agent 配置修订不强迫重新捕获；换源不能靠 hostless 登记通过。
- `issue_sources` 保持标准库可读；与原 snapshot schema／严格 validator 比较后，字段集合、正整数／有限值、bool 拒绝、labels、来源绑定及 canonical SHA 保持。没有凭证读取或网络调用。checksum 不提供服务器认证。
- creation3 继续七文件、每文件 1MiB／intent 16MiB、intent-before-files 和 spec 最后发布；重试／恢复核原 intent 与冻结 selection，不重新查询当前来源、外部 manifest 或远端。项目写保留和任务文件锁沿原所有者。
- 合法 v7 Input／Adapter／Workflow 拥有自身 queue／request 根，复用原活动、原六阶段和实际 worker 注册。Executor 的 declared results、work ports、review ports 和 materials 分支通过 Input 的 `artifact_protocol` 复用 v6 named-source；完整 `issue_source` 明确进入 work／review 材料及恢复校验，旧 producer prompt／materials 不递归内联。
- evidence index 和 handoff 保存完整原输入及其 canonical SHA；验证 legacy 投影、来源对冻结配置，以及存在原 outcome 时的 admission SHA。旧 packet 保持可读；索引／manifest 总限额保持，超限仍拒绝。
- 原 start doctor、policy、可信 checks、claim、lookup-before-start、attempt-before-send、原输入／memo 和 unknown 只查原 ID 的恢复代码未改。B1c 窄依赖准入、真实 Temporal/model 六阶段、实际 Agent 来源消费及旧入口竞争仍是下一片，不由本片离线证据替代。

## Standards、结构和测试价值

### ST1／P2：来源任务夹具违反现有 Windows 支持矩阵

初始位置：[test_issue_tasks.py](../../tests/test_issue_tasks.py#L24)。`issue_creation` 固定 `workspace-task-mcp / current-container`，却没有相邻 `work_creation` 的 Linux/WSL2 skip。Windows Portability 会执行整个 `tests`；真实路径 `tasks._composition → CodexBackend.composition_policy` 在 `win32` 明确拒绝该模式，导致 happy-path 和若干预期来源错误测试失败。

已在安装 r2 的真实 backend 上用纯内存平台替换验证 Linux 接受、win32 抛原模式错误。修正仅为该 workspace fixture 增加原支持矩阵的 skip，并将纯 snapshot 类型／摘要校验测试改用已有 source/bind/native 夹具，保留其跨平台运行。作者 r2 非 editable 产品上的平台修正检查为 15 passed／23.03s；原 stdout 已核。ST1 关闭；没有为测试放宽产品平台约束或另增 CI。

### ST2／P3：新 v3 schema 留有无效条件声明

初始位置：`task-definition-v3.json` 的 `composition.dependentSchemas.execution`。v3 的 `composition.required` 已无条件要求 execution 和 review_protocol，该条件不能增加任何校验。最小修正是删除 v3 的这段声明，v2 保持；不需要为已无意义的历史分支加拒绝测试。最终源码／r3 包／冻结内容均已核，ST2 关闭。

### 结构与性能判断

`issue_sources` 是有实际复用的纯来源 Module：生产调用来自 issues、issue_backends、task_envelopes、tasks、creation 和 handoff，解决 native `-S` 读取不能依赖 JSON Schema／SDK 的具体约束。其私有字段／摘要／正整数算法局部归属合理。v7 的薄具体类由版本身份、worker 构造和 request 根合同要求，没有假想插件框架或全局杂项注册表。

新 `compile_input` 是原叶提示编译器的直接公开复用，tasks 和原 bundle 准备／核验均调用它；没有另建预算算法。Input 的 `stage_material / evidence_contract / artifact_protocol` 将版本差异集中在本族执行合同，Executor 和交接消费者未按后端名新建并行分派。边界外部输入与持久恢复的重复核验有各自责任；未发现需要新增通用 wrapper 或来源账本的理由。

来源校验和摘要处理按本次完整正文线性增长，原文件／prompt／context 上限保持。v7 每次所需 work／review 输入携一份完整来源，声明产物沿 v6 传递，没有在后继材料递归携带前代 source prompt。记录的 11.87s 是离线 CLI/HTTP 旅程总时长，288.75s 是一个自身审查会话，不是正式 v7 吞吐、模型延迟比较或性能改进证明。

新增测试集中在来源身份错配、离线复原、不可变发布、完整实际材料、非递归产物、标准库读取、可构造版本和 handoff 原 outcome 绑定，保护可达的静默错误。复用已有 source、creation 故障注入、work graph、executor CLI 协议和 handoff 夹具；CI 文件未变。精确预算只新增 ASCII／UTF8 两个有实际编码差异的回归。修正中首次预算测试出现 999,999B 的夹具计算失败，现已按完整 JSON 编码长度修正，没有修改产品限制满足测试；其失败保留在证据中。

## 已独立核对的证据

1. 原 source 212 项、首个新增来源 14 passed／1 GitLab namespace setup error、修夹具后 15+1 协议通过，以及安装 r1 的 12 文件 343 passed／298.61s，均保留其原时间和候选范围。r1 到 r2 的 444 个包文件逐字比较确实仅 `issue_sources.py` 改动；不将 r1 称最终候选。
2. r2 wheel SHA256 `dbea1d7373625fb76b224b9ae470484df2432fc136bf5ebb633f2269b08f19c5`；独立逐字比较 444 source／wheel／installed 包文件，核 wheel 449 行及 installed 454 行 RECORD 的每个非空摘要／大小，并核 283 冻结文件。r2 原 stdout 确认三个来源文件 40 passed／48.39s 和 reference verify PASS；这是修正 SP1 之前的包。
3. 真实旅程原件核 11 对 CLI stdout/stderr 和 11 HTTP body 的摘要／大小；CLI 与 HTTP preview 完整相等，两个任务各七文件，未产生 requests／receipts／submission。原驱动与回执记录两次 tracker GET，停止 tracker、删除 token 后预览／创建／重试／新 ID 换 source／换 binding 和移除 manifest 后恢复等 15 检查，11.87s。未重新启动服务或重跑旅程；退出／端口关闭是原驱动记录的范围。
4. 自身模板 run `655a6261426746d08e2018a3f69cb7d3` 的 manifest→prepared input→实际 input／prompt→scope→原 result 身份通过。直接解析原 native JSONL，逐字重建全部五份 scope：354、480、359090、521、163B；正文 17 个连续 UTF8 页，均到 next_offset:null，另两次 base64 页由较小页重读，工具失败 0。20 份附件均按声明字节与 SHA 核完整原文。原 result SHA256 `60e3a341a0e894ac5eb96b7d6013013de7789274814066ba3a180fdc066f9583`，原判断 approve。采样四个 PID/starttime 现在均无相同存活进程；不外推未采样进程。公开投影六份原件身份已核。
5. 原后端 usage 为 input 2,238,908／cached 2,089,856／output 6,208／reasoning 2,310；cached 包含在 input 内，reasoning 单列，不相加推计费。自身模板只收到先前 20 份附件；安装／旅程后补状态、公开投影、相邻未改源码、此次三个独立 finding 的修正不在原模型判词覆盖内。
6. 最终 r3 wheel SHA256 `1c4dcc20b37cfcd776159bb1085129695cf7d64ed591acb2632a75b153c33222`，再次独立核 444 source／wheel／installed 包文件、两份 RECORD 的 449／454 行以及 283 冻结原件。r2→r3 恰好四个包文件变化：`reference_inputs / reference_workflows / reference_task_creation` 和 `task-definition-v3.json`；其他原安装检查覆盖的产品字节保持。原 28 passed／57.09s 包含来源 17、worker 10 和实际原执行器 CLI 协议 1，driver 59.14s；reference verify PASS，两个 stdout 摘要匹配原元数据。没有将原 343 项改称 r3 全套重跑。
7. 最终 r3 的第二次真实旅程：11 对 CLI 原 stream 和 11 HTTP 原 body 的摘要／大小均核准，CLI／HTTP 完整 preview 相等，两个任务各七文件，15 检查通过／11.895s；两次 tracker GET，原退出记录为 owned web -15、tracker thread 不存活、owned ports closed。其原件身份和历史 r2 旅程均由最终公开投影区分，未借旧旅程证明新包。
8. 聚焦自身模板 run `8e5db9fc8e4644d595b68ec4981d22cb`：完整身份链已核，五份 scope 从原 native JSONL 逐字重建为 354、480、93009、521、163B；正文七个连续 UTF8 页到 null，另一次 base64 页缩小重读，工具失败 0。七份完整附件中四个最终产品文件与最终测试文件逐字等于当前源码；两份当时计划／交付记录的后补状态由本评审另核。原 result SHA256 `a9c9207b3c2bc5eb0acfb46c84fbbc1b616bf4fef0b438c6e985849efde2abef`，原判断 approve，run 区间 106.72s。原模板指令／Skill 字节保持，只有证据资源、精确引用版本和显式材料额度变化。四个采样 PID/starttime 无相同存活进程。
9. 聚焦原 usage 为 input 354,519／cached 289,024／output 1,892／reasoning 624，同样不重复计数。最终自身投影的 12 份原件，以及安装／旅程投影的原件身份均逐项核对。模型聚焦判词限这七份供给材料，不覆盖稍后测试结果、最终文档、精确交付或 B1c。

本评审只读源码／原件和 ZIP／RECORD，运行必要的纯内存来源、平台和预算探针，以及文档静态检查；仅写本项目本报告。没有安装、运行模型、联网写入、提交或启动服务，没有重跑产品套件。Windows 真实运行、最终精确提交／远端／自己的 CI，以及 B1c 真实运行均未由本评审完成。

## 同片复核结论

完整 32 文件审查完成。Spec：SP1／P2 关闭，开放 0；Standards：ST1／P2、ST2／P3 关闭，开放 0。最终源码、相邻调用、测试价值、性能范围、r3 安装／旅程、两轮自身原件及最终计划／交付／两公开投影相互一致，B1b 本地出口通过。

本结论不关闭 B1c 的窄依赖准入／真实 Temporal/model 六阶段、历史 replay、Windows 实机新格式、宿主隔离、远端工单写入或项目整体。精确 Git 对象／远端／自己的 CI 在普通提交后核准；后续工作区即使开始 B1c，也不得替代本片冻结候选。
