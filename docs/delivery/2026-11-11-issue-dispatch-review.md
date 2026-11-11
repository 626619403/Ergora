# F7b.1-B1b 独立实现审查

日期：2026-11-11。审查者：fresh-context 独立 Agent `f7b1_source_publication_review`；未继承实现会话、未启动子 Agent。依据本项目 [AGENTS](../../AGENTS.md)、[B1 计划](../plans/2026-11-11-issue-dispatch.md)、[独立设计](../plans/2026-11-11-issue-dispatch-design-review.md)及 maintainable-project-delivery 的 independent-review brief，先读原需求、冻结 diff／新增文件及相邻调用，再核作者交付记录和原始证据。

**原 r3 本地独立判词：Spec 通过，Standards 通过，开放 finding 0／0。** 初审发现的 Spec 一项 P2、Standards 一项 P2 和一项 P3 均已最小修正并复核关闭。最终 r3 安装身份、受影响检查、实际 CLI／HTTP 旅程、两轮自身模板原件及完整候选终核通过；结论限 B1b 本地出口，普通提交／远端／本候选自己的 CI 仍须另核。

**当前同片结论：r4 依赖修正的 Spec／Standards 均通过，ST3／P2 关闭，开放 0／0。** 上段 Standards 原判词曾因 `6558671` 的实际双 OS CI 架构失败和另查出的静态循环撤回；现已独立核准修正源码、安装／旅程／自身原件及完整 20 文件范围，详见末节。新修正的精确提交／远端／自己的 CI 仍待另核；原提交的失败不改写为成功。

## 精确范围

基线 `3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`，分支 `refactor/architecture-foundations`。初始冻结清单 30 文件，清单 SHA256 `c4a3cd728d9484985badd7636ed03f9a37a89a00fc92b2391a4f9e7d7f5d9392`，tracked diff SHA256 `10db848c7c5d399cde543b0c35b697d8e924542ee1df1b5b6f996705c59cbb07`。已逐件核清单字节数／SHA，并确认当时全部冻结内容等于工作区：

|类别|全部初始文件|
|---|---|
|产品与格式|`src/ergora/{handoff,issue_backends,issue_sources,issues,reference_executor,reference_inputs,reference_task_creation,reference_task_reconciliation,reference_workflows,task_envelopes,tasks,workflow_definitions}.py`；`src/ergora/data/schemas/{task-definition-v3,task-handoff-v1}.json`|
|测试|`tests/test_issue_tasks.py`、`tests/test_work_agents.py`、`tests/fixtures/work_delivery_acceptance.py`|
|文档|`README.md`；`docs/PLAN.md`、`docs/USAGE.md`；`docs/architecture/{current,contracts-and-identities}.md`；`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-11-{issue-dispatch,issue-dispatch-design-review,issue-mapping}.md`；`docs/delivery/2026-11-11-{issue-dispatch,issue-mapping,issue-mapping-review}.md`；`docs/delivery/evidence/2026-11-11-issue-dispatch-acceptance.json`|

相邻只读范围包括 `contracts / components / projects / bindings / reference_creation_process / reference_task_submission / reference_task_runtime / reference_task_reconciliation / reference_worker / review_dags / task_mcp`、原 native cli／workflow／adapter／ingress、相关原创建／worker／transport／handoff夹具和现有 Portability CI。B0 文档的精确交付追加只核其身份和范围表述，不重新宣称本评审直接完成 B0 的网络或 CI 操作。

原 r3 完整冻结为 32 文件：上述 30 文件，加本报告与 `docs/delivery/evidence/2026-11-11-issue-dispatch-self-review.json`。清单 SHA256 `dab5143782c752d7fbc043d57a5c2b6a4e28d2d32517e2669d2a07814e1b6141`，tracked diff SHA256 `9e0f346f639e9d6da815afb61ba53a759229e855b3ea2965b2067c002ca2f7c8`；该轮终核开始时 32 份冻结内容均与工作区逐字相等。随后本报告结论和相对链接回写，以及 PLAN／本片计划／交付记录／验收投影四份完成状态更新，均已分别复核；其余 27 文件在该轮终核时仍逐字相等。之后的 ST3 修正候选另见末节，产品／测试实际修改及后补文档均已纳入复核。本报告自身与后续出口状态记账不触发递归审查。

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
9. 聚焦原 usage 为 input 354,519／cached 289,024／output 1,892／reasoning 624，同样不重复计数。最终自身投影的 12 份原件，以及安装／旅程投影的 16 份原件身份均逐项核对；最终 13 份 Markdown 的 356 个本地链接目标存在，`git diff --check` 通过。模型聚焦判词限这七份供给材料，不覆盖稍后测试结果、最终文档、精确交付或 B1c。

本评审只读源码／原件和 ZIP／RECORD，运行必要的纯内存来源、平台和预算探针，以及文档静态检查；仅写本项目本报告。没有安装、运行模型、联网写入、提交或启动服务，没有重跑产品套件。Windows 真实运行、最终精确提交／远端／自己的 CI，以及 B1c 真实运行均未由本评审完成。

## 同片复核结论

完整 32 文件审查完成。Spec：SP1／P2 关闭，开放 0；Standards：ST1／P2、ST2／P3 关闭，开放 0。最终源码、相邻调用、测试价值、性能范围、r3 安装／旅程、两轮自身原件及最终计划／交付／两公开投影相互一致，B1b 本地出口通过。

本结论不关闭 B1c 的窄依赖准入／真实 Temporal/model 六阶段、历史 replay、Windows 实机新格式、宿主隔离、远端工单写入或项目整体。精确 Git 对象／远端／自己的 CI 在普通提交后核准；后续工作区即使开始 B1c，也不得替代本片冻结候选。

## 普通提交后的精确只读终核

2026-11-11，独立读取普通提交 `6558671f128c320f01785f9b28c673442cf76089` 的 Git tree／blob。其直接父提交为原基线，32 个变更路径恰好等于 ready-r1；ready 清单 SHA256 为 `cdb8a7a9138244d51bf070133814deedfe3b19a214b22f4ce2b983f71477f609`。逐个核 Git blob 原字节、大小、SHA256 和 `100644` 模式，均等于 ready 保存的 32 份文件。本报告上文两段清单／证据数量补记晚于 ready／staging，仍在工作区保留，不将当前报告全文冒称该提交的报告 blob；这些补记不改变产品或测试。

以该精确提交的 Git blob 直接比对最终 r3：444 个包文件与 wheel 及独立安装目录逐字相等，wheel SHA256 仍为 `1c4dcc20b37cfcd776159bb1085129695cf7d64ed591acb2632a75b153c33222`；wheel／installed 两份 RECORD 的 449／454 行中每个非空摘要和大小均通过，283 份 reference frozen 内容在提交／wheel／installed 三处一致且匹配 manifest。此轮没有重跑产品行为或模型。

作者报告普通推送成功后，评审者于 `2026-11-11T08:59:59.786051+00:00` 只做一次 GitHub 官方完整 [Ref API GET](https://api.github.com/repos/626619403/Ergora/git/ref/heads/refactor/architecture-foundations)。实际返回 HTTP 403／API rate limit exceeded，原响应 280B、SHA256 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`；未取得远端完整 SHA，没有重试或换路，不称独立远端核准成功。自己的 CI 原件尚待提供，本段不提前关闭该项；本轮只属于 B1b 的精确交付复核，不构成 B1c 独立实现审查。

## ST3／P2：原精确 CI 暴露架构合同回归，已同片修正

独立读取自己的 [Portability run 42991272992](https://github.com/626619403/Ergora/actions/runs/42991272992) 首份原 HTML（166,659B，SHA256 `064d519126f16fcb5f64cd2558546987a131b1615569e50456db0a9eadbf1092`）。该样本仍显示 run In progress，Windows native regression 已明确失败：3 failed／820 passed／595 skipped／16 subtests，381.16s。三项分别是 `tasks → issues → tasks` 违反已有无环合同、task_envelopes 新增纯 issue_sources 依赖未纳入 foundation 合同，以及 handoff 依赖 reference_inputs／issue_sources 越过其已声明边界。它不是本候选 CI 成功证据，也不能用此前定向安装检查替代。

另直接对 `6558671` 全部 first-party 模块 AST 求强连通分量，确认 `reference_inputs → reference_workflows → reference_inputs` 是第二处循环；首个 cycle assertion 被前一循环先行截断，没有替后者提供通过结论。handoff 原 input 校验实际只需已存在的纯 unwrap／来源绑定；完整首 inventory 的预算组装也不应使 workflow 反向依赖其版本构造 Input。原独立终核未将这些新增依赖与已有全图合同正确对应，Standards 无问题的原结论在此撤回。

同片最小修正方向已审查：把原 snapshot 保存／读取与 row 重建下移到共同 issue_snapshots 所有者，保留 issues 的远端观察／修订／关联编排；handoff 直接 unwrap 原文、核投影和原文 SHA，仅对已验证 v7 绑定完整来源；首 inventory context 原样下移纯 task_envelopes，由 creation／workflow 直接调用，保留精确字段、原上限和 ValueError→StopWork 边界。foundation 合同只增加实际纯 issue_sources 的依赖许可与标准库约束，不准许运行 Input 或循环。按这些边虚拟替换后的 57 模块全图无环；该设计检查时 ST3 仍开放，没有替代修正源码／安装包／受影响行为及新精确 CI 的复核。

### ST3 同片源码复核：先于安装原件

后续实际修正逐项对照 `6558671`：八个产品文件为新增 `issue_snapshots` 及 `issues / tasks / handoff / task_envelopes / reference_inputs / reference_task_creation / reference_workflows`，另两份原测试为 `test_architecture_boundaries / test_issue_tasks`。本轮十文件按路径排序的 file／bytes／sha256 canonical JSON 摘要为 `77b5b1b135fc1163991a9e2d55572deefe73fb32f737355eb69a4717f240a579`。B1c 未跟踪计划／交付／test_issue_submission 不属于该候选，没有纳入本次代码审查。

实际修法比原拟方案更小：共同 issue_snapshots 仅接收原 getter、row 重建和 digest 校验，`issues.snapshot` 仍 reexport 旧公开入口；capture 的唯一持久写／事务仍由原 issues 拥有，没有为单调用另建写抽象。tasks 改向共同读取所有者，issues 的原 link 仍调用 tasks.creation。handoff 的原文投影／SHA／冻结来源校验保持，只在 composition 非空且已验证版本为 7 时取来源，旧格式不因任意附加 issue_source 改变分支。首 context helper 原样移到纯 task_envelopes；原 native validate_spec 原样返回 spec，故从已验证 admission 取 legacy_spec 与原运行 self.spec 相同。

独立对实际源码而非虚拟图再做 AST 检查：57 个 first-party 模块全图无环，九个 foundation 依赖集合与三项标准库边界满足，未许可 reference_inputs 等运行层。必要的 `python -S -B` 纯内存等价探针逐字段／逐字比较原提交 helper 和新 helper：ASCII／中文均精确接受 1,000,000B，增加一字符分别多 1／3B，错误文本相同；原 snapshot row／digest 与迁出函数行为相同，纯读取不依赖 JSON Schema 或 SDK。测试只更新原架构依赖合同及原预算调用点，没有新增同构 CI 或重复保护。首份 source 架构修正检查的 `1 failed / 11 passed`（0.45s、根级 import 被标准库合同识别为 ergora）保留，其后的具名纯导入没有放宽该合同。源码复核未发现新 finding；此时 ST3 的最终关闭仍待 r4 安装及后补原件。

### ST3 最终同片复核：关闭

完整修正范围按 `repair-files.json` 的 20 文件终核：八个产品、两测试、八份本片／架构／证据文档，以及两份已被公开链接的 B1c 准备文档。后两份只核未来范围、原型备份还原及混合身份检查无效的状态表述，没有审查 B1c 设计或实现；未跟踪的 `test_issue_submission.py` 正文和 B1c 产品不在本轮范围。其余文档与新公开投影的状态、范围及实际原件相符，原模型只覆盖下述 12 附件，不借其判词覆盖完整 20 文件。

最终 r4 wheel SHA256 `29c4626ce18e7988d4635cd0f8e3659993ba8bb4439d576ddf86d95e0e98b2b9`。独立逐字核 445 source／wheel／installed 文件、450／455 行两份 RECORD 的所有非空摘要和大小，以及 283 份 frozen 内容；r3→r4 恰好只变更八个已审产品文件。安装六文件组原 stdout 为 125 passed／209.38s，driver 211.958s；reference verify PASS，两份 stdout SHA 均匹配原元数据。没有重跑行为、重新安装或借原 r3 检查称新包全套通过。

r4 真实 CLI／loopback HTTP 旅程原件的 22 个 CLI stdout／stderr 和 11 个 HTTP body 均逐项核摘要／大小，完整 preview 相等，两任务各七文件；15 检查／11.0785s，两次 tracker GET。fixture 的解释器确为 r4 独立安装；tracker 先停止、token 删除后才发布／恢复，换源需新 ID、绑定变化及移除 manifest 后恢复保持原文。退出 -15、tracker thread 不存活、端口关闭均为原驱动记录，本轮未启动服务。没有执行请求／回执／提交记录，不将该离线旅程称六阶段或真实来源 Agent 消费。

第三次实际自身模板 run `5451283ae8bb4b06b974af59bb45b0bd` 独立核完整 manifest→prepared／actual input→prompt／stdin／协议→admission／scope→原 result 身份；原模板指令／Skill 保持，仅按前两轮相同规则加入证据、精确版本与额度。直接解析原 native JSONL，完整重建五份 scope（354、480、177571、521、163B），正文十个连续 UTF8 页至 null，无 base64 重试或失败调用。12 份完整附件按声明字节／SHA 逐件核准；八产品和两测试等于最终源码，计划附件当轮相等、交付附件后补结果由本评审另核。原 result SHA256 `d96ed56a4d3ad2b63d4104aad98ade8bfa858627a9cdab87dae90ff2adb4fc3a`，原判断 approve／161.003s，native stream SHA256 `caf10d68e0a67afc9d00bff096ddd65ff92c1d8f9003b07af1aa5224f0cae58d`。input 430,641／cached 368,384／output 3,176／reasoning 1,679 保持原计数口径，不重复相加；四个采样 PID／starttime 无相同存活进程。`self-review-r3` 仅准备失败、没有 run 记录，不计作实际模型调用或成功判词。

新[依赖修正投影](evidence/2026-11-11-issue-source-dependencies.json)的 14 份原件身份全部核准。另直接解析原 `6558671` 两 job 官方 HTML 的 check-step 属性、完整提交身份和失败摘要，与原失败投影逐字段相同：Linux 3 failed／1383 passed／87 skipped／36 subtests／978.08s，Windows 3 failed／820 passed／595 skipped／16 subtests／381.16s；两 job 均 completed，Native regression 为 failure。构建与 reference identity 成功、Windows installer 成功／Linux 对应步骤跳过不构成整项 CI 成功，没有称成功 REST 或下载全日志。

完整 20 文件的 JSON／静态检查通过；八份 Markdown 的 84 个本地链接目标存在，六个已载入秘密值和私有 home 路径检查无问题，`git diff --check` 通过。十个已核产品／测试文件与源码复核时的身份相同。

ST3／P2 已按修正源码、安装／旅程和完整后补证据复核关闭。当前 Spec／Standards 通过，开放 0／0，B1b 依赖修正的本地出口通过；新修正候选的冻结身份／普通提交／远端／自己的必要 CI 随后另核。原 `6558671` 双 OS CI 保持失败、一次独立 Ref 限流 403 保持原结果，B1c 真实运行及项目整体均未关闭。

## 修正提交 4638c3b 的精确身份与远端 Ref

普通修正提交 `4638c3b9524adcba584a9313b8fd1588b5dde64d` 的直接父提交为 `6558671f128c320f01785f9b28c673442cf76089`。独立读取其 Git tree／blob，20 个变更路径恰好等于 repair-ready-r1，清单 SHA256 `22065eb1dadbdbf59b0d8f2c0172afdf2e0500c207a13d6817358f6132cfa037`；逐件核原字节、大小、SHA256 和 `100644` 模式，全部与 ready 保存文件一致。以该提交的精确 Git blob 直接比对 r4 wheel／installed，445 个包文件逐字相同，450／455 行 RECORD 所有非空摘要和大小及 283 份 frozen 三处身份通过，wheel SHA 保持 `29c4626ce18e7988d4635cd0f8e3659993ba8bb4439d576ddf86d95e0e98b2b9`。没有用随后恢复的 B1c live 产品代替本片候选，也没有重跑行为或模型。

2026-11-11，作者报告普通推送成功后，评审者只做一次现有 SSH `git ls-remote --refs` 分支读取，退出 0；`refs/heads/refactor/architecture-foundations` 返回完整 `4638c3b9524adcba584a9313b8fd1588b5dde64d`，与本片修正提交相同。没有重新访问已限流 API、变更认证或重试；原 `6558671` 的 API 403 仍保持其实际范围。修正提交自己的 CI 原件尚待提供，不借原失败或本地检查提前关闭；本次只属于 B1b 精确交付复核，不复用为 B1c 独立审查。

## 修正自己的 CI 终态：精确交付终结

独立离线核准固定提交 `4638c3b9524adcba584a9313b8fd1588b5dde64d` 自己的 [Portability run 42995785084](https://github.com/626619403/Ergora/actions/runs/42995785084)。最终 `repair-ci-run-html-r3` 官方原 HTML 为 HTTP 200／Status Success，并链接同完整提交；早期 r2 仍为 In progress，分别保留。七组原件（run r2／r3、两 job、API、matrix、navigation）的七份 receipt 及七份 body 均逐一核原字节数／SHA256，URL 与实际 final URL 相同，未用原失败候选或当前 B1c 工作区替代。

|最终原 HTML|body 字节数／SHA256|receipt SHA256|
|---|---|---|
|run r3|157029／`bbb7ca87dd3fbd9aee342ce1e0179682d0afcbd686d06fa96b9a7f2b47a19f50`|`c6b8394021d86a0ba3fe76919b386a8d4b7588e510e73a8f3af039e055d0b4b1`|
|Linux job|161578／`ab6f48913781f7867d222d29fbdc0c7c5d20210d57ebd6a5b3cf9bc2e570ff1a`|`e70a44f40988bc051d31a38d50a31c60c26348ca42d860d44c3286402440ab49`|
|Windows job|159659／`4b402b1c515862b3fc36d1c1505481e840686452dacb8b62248540a2919c0d97`|`7c530c5fe8f27a6247c62523a8a5a90156738ac24f4246c71ba0e37c17673ecc`|

直接解析 [Linux job 130439423259](https://github.com/626619403/Ergora/actions/runs/42995785084/job/130439423259) 与 [Windows job 130439423651](https://github.com/626619403/Ergora/actions/runs/42995785084/job/130439423651) 的原 check-steps／check-step 属性，并对照该提交的原 workflow：两 job 均 completed；Build and install wheel、Packaged reference identity、Native application regression 在两 OS 全部 success，Windows PowerShell 5.1 installer and upgrade 在 Windows success、Linux skipped。Linux 三项／Windows 四项必要步骤均有非空 completed-at；每个非空日志 URL 均绑定完整 `4638c3b` 和各自 job ID。未以两个 job 的外围 setup 成功代替必要步骤，也不从折叠 HTML 推计用例数量或声称下载全日志。

原 `repair-ci-api-r1` 仍为 HTTP 403／限流，matrix r1 为 404（226081B），navigation r1 为 404（0B），其 receipt／body 摘要同样通过；这些失败不改称成功 REST 或可用的 lazy 子接口。本次只读取作者保存的官方原件，没有新外部读取、重复 Ref、运行测试／模型或使用后续 live 产品。原 `6558671`／run `42991272992` 的双 OS failure 保持其原候选范围。

结合此前精确 20 Git 对象／模式、445 committed／wheel／installed、两份 RECORD、283 frozen 和一次独立 SSH 完整 Ref 核准，本片 B1b 修正 `4638c3b` 的必要 CI 与精确交付现已终结。Spec／Standards 开放 0／0，SP1、ST1、ST2、ST3 均关闭。B1c 的准备文档、后续实现／真实六阶段以及项目整体不由本结论关闭；本次 CI 追加属于原报告后补交付事实，不冒称已存在于修正提交的报告 blob。
