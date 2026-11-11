# C5c 独立审查：运行材料与版本化阶段产物

审查者：`/root/composition_runtime_review`，fresh context。固定基线 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`；分支 `refactor/architecture-foundations`。按 `AGENTS.md`、AIHERO 索引、code-review 的 Spec／Standards 两轴、codebase-design 和 maintainable-project-delivery 独立审查规则检查。原始要求来自本片审查任务，不用实现者的预期结论代替判断。

本记录保存 **M0 设计、M1 固定代码候选、M2 两域原件、M3 最终本地及 M4 精确交付终核**；各时点结论和原失败保持，最新门禁见末段。显式版本 B 已按[规格](../plans/2026-11-11-stage-result-materials.md)实现，完整本地出口通过；精确提交 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9` 的 27 Git 对象／439 包／283 冻结、独立官方 Git Ref API 同 SHA 和自己的 [CI42954686614](https://github.com/626619403/Ergora/actions/runs/42954686614) 双 OS 七必要步骤均已通过。**C5c 精确交付终结，Spec／Standards 开放 finding 均为 0。**

## 固定对象与检查范围

- R2 冻结输入为三份当前文档及六份完整私有驱动；九份文件逐件 SHA256／字节数均与 `review-r2/identity.json` 相符。`tracked.diff` 单独留摘要。工作区中更早 C5b 收尾文档不是本轮产品变更。
- 初次独立核验时，全部 439 份源文件字节与基线及原 R1 身份记录相同；283 份冻结参考匹配。该结果有独立时间戳，**只说明 R2 身份**。随后 M1 已开始修改源，不能把该结果转授在写中的候选。
- 语义检查覆盖 `reference_executor` 的 `_review_artifacts/_work_producer/_work_ports/_review_ports/_composition_request/_composition_context`、原工作阶段、FileAdapter、Activities、`task_envelopes`、`reference_inputs/reference_workflows`、`review_dags`、`task_mcp`、结果 schema、原手册和 work_delivery acceptance 邻接调用。439 份文件是身份核验数量，不是逐文件代码审查数量。
- 只读核对两任务原 envelope／receipt 及其全部 109 份产物 SHA；治理五次 fixture 读取回执中的 23 份／7,437 字节与原 scope 完整正文相等，分页 offset／总量相符。核对原 194 事件 history 的保存摘要／数量、handoff 摘要／ZIP CRC，以及两次清理记录的 67／44 实际采样与零剩余记录。

私有独立原件在 `.ergora/checks/ac5-composition-runtime/independent/`：`verify_r2.py`、`r2-identities.json`、`original-identities-r2.json`、`r2-evidence-summary.json`，另存 M0 规格快照与尺寸范围说明。没有读取凭据文件，没有启动模型、服务、history replay、安装、网络或提交；未改产品、PLAN 或原失败资料。

## Spec：原故障与合同

**C5C-SP1，P1，开放：内置大变更组合尚不能完成本片要求的六阶段交付。** 原 `work:integration-tests` receipt 为 FAILED，明确报 `Composition task exceeds the supported input byte limit`；原 run 已 BLOCKED。治理任务原范围的 REVIEW_READY、完整 MCP fixture 读取和 handoff 不能替代第二域的出口。最小处置是保留该失败和全部原件，为修正后的显式新合同另建可追踪的新任务，并完成两域验收。

根因有直接原件支持：

1. `_work_ports` 在同一次输入中既把每个直接前驱完整产物放入 `work_inputs.results`，又返回相同正文给 `dependency_artifacts`（基线 `reference_executor.py:306–325,445–458`）。两个 producer 表各约 478 KB，完整 task 为 **1,928,864 B**，SHA 与原离线复现一致。
2. 这些“产物”包含 `composition-materials`／`composition-prompt`；两前驱分别带约 191 KB／190 KB 的旧材料与提示，它们再次包含上一代审计。领域 `change-summary` 本身只有 32 B，可信 `test-results` 为 624 B；本例不是有意扩大领域输出的压力夹具。重复 JSON 编码会继续增加字节，但没有证据支持仅调编码就能解决问题。
3. 独立单变量计算只删 server/client 在依赖表中的重复副本、保留 plan 后，材料 JSON 为 **977,107 B**，完整 task 为 **977,667 B**，加全部祖先后的 prompt 为 **980,984 B**。原 977,107 数字应标为材料 JSON，不能称完整 task。这个当前尺寸低于 1 MB，故“单去重仍令当前 integration 超限”不是已证事实；它仍携带递归审计，不能据此推断后继 review 或更长合法链可用。未发布这个尺寸探针，也未调用 Agent。

这不是 MCP 读取失败，也不是权限不足。原 `_input_fields` 在 MCP 调用之前明确拒绝超限 task（基线 `workflow_definitions.py:380–392`），符合旧合同的失败方式；缺口是本片期望的内置协作旅程尚未交付。

**旧合同不能重新解释。** [原手册](../WORKFLOW_DEFINITIONS.md)在数据端口和工作单元段明确承诺“全部原产物正文／完整内联”，原 `tests/fixtures/work_delivery_acceptance.py:142` 附近把下游 `artifacts` 与 receipt 列出的全部原件逐表相等。将旧 v5 表改成 allowlist，即使剩余内容完整、全部原件仍在磁盘，也不是旧合同的等价修复。旧 v2–v5、已封存调用和恢复必须继续使用原语义。

## 两种方案及最小修正

|方向|能保留的语义|需要补齐的实际能力|判断|
|---|---|---|---|
|A：原审计全文作为可读完整附件|下游仍可取得所有原审计字节；必须明确从原 inline 合同转为附件的新版本|动态不可变 snapshot／URI 与原 receipt、job、candidate、admission 绑定；后端能力和范围准入；完整分页读取证据与预算；恢复及 handoff 原件身份|可行，但不是“现有 MCP 已有所以直接可用”的小修正，涉及更多所有者|
|B：新版本传全部声明阶段产物与可信检查／意见|祖先资源不变；原审计全件保留并核验；下游不再递归消费提示和执行日志|显式 execution protocol／admission／材料版本；精确结果集合；旧路径保留；两域与异常证据|推荐，现有执行器拥有所需可信来源，修正集中|

A 的前提尤其不能省略：当前 `task_mcp.freeze` 只从结构祖先和自身固定资源构造 scope（基线 `task_mcp.py:50–89`）；当前 `verify_native` 只证明正确 scope 下的 tools/list readiness（229–242），不证明指定全文读完。现有 read 分页、SHA 和 no-follow 文件读取可复用，但自动开放前驱宿主文件、把外部文件路径当可读资料、或把 readiness 当全读证据都不成立。A 同样需要显式新合同，不能用可读附件悄悄替换旧 v5 的 inline 承诺。保持 read-only 工具并不等于现有 scope 已授权新资料。

B 的最小可维护实现应留在已有所有者：

- `reference_executor` 核原可信 producer 并投影正文。结果集合须是 **profile 声明产物 ∪ work 的 test-results／verify 的 check-results ∪ receipt.checks 的全部引用 ∪ review 的可信 composition-review-decision**，每份全文保留；不能写死默认 preset 的两三个名称。原 profile 合法范围没有强制列出 test-results，原 work 总会产生它且 receipt.checks 可为空，所以只按 profile 或 checks 单一集合会漏可信证据。模型 summary 未被该合同承诺为交付内容，公开表述应维持“全部声明阶段产物与可信检查／意见”。
- 保留 stage／完整 receipt／receipt 摘要，原 adapter 仍验证全部审计原件。work 的 request/admission/批准计划、binding/session/claim、formal-call/invocation/selection、Git 祖先身份继续核；review 继续通过 `review_observation` 取可信意见。把不内联的原件留在 receipt 索引和 evidence/handoff，不可把“保留索引”称为下游已读全文。
- `WorkDelivery` 只要求 unit 与图的**传递依赖闭包**相同（基线 `review_dags.py:214–219`），端口 sources 不必等于直接 unit.depends_on。work 来源表应覆盖两者并集，用显式 dependencies 映射保留控制依赖；同一 producer 一次。原 plan、review 的 plan／verification 继续全文传入。控制边不是额外 Skill 继承。
- 新 `work-units-v2` → admission-v6 和材料版本显式选择，输入族注册新的 workflow／queue／request 根，复用原 WorkDelivery 调度和活动。现有 `reference_inputs` 的构造接口适合这一变体；少量框架注册类有具体作用，不需要新调度器、账本、通用产物服务或额外插件层。
- `task_envelopes` 验证版本和 protocol 的一致性，tasks／CLI／HTTP／新建页面调用原准入用例。旧 v5 仍可显式选择，历史恢复沿原冻结版本。原 1,000,000 B 上限、祖先全文及权限链保持；真正的领域结果超限仍拒绝。

[M 规格](../plans/2026-11-11-stage-result-materials.md)已明确上述边界；这是对设计问题的处置，不是已验证产品修复。只删重复副本可作为局部成本改善，但无法单独解决旧审计的递归传播；仅提高限额、减小 fixture 或删祖先资料均不能关闭 C5C-SP1。

## Standards／结构、性能与测试价值

**设计有条件通过；R2 检查范围内未发现新增的 Standards 违反。** 当前无产品候选可给最终代码通过。阶段产物属于原 Executor 可信 producer 接口，新版本路由属于现有输入族；沿这些 seam 修改具备 locality。新增内聚私有算法可以有一个真实调用方，不应为满足复用数量人为拆文件或增加包装。

现有 3.59 秒只证明原离线重建／拒绝成本；独立核验仅作原件身份和尺寸计算，不能把它称为新方案性能结果。修正候选应记录长链／扇入的完整 task、prompt、阶段用时与原件读取量，确认业务结果不再因嵌套审计被递归展开，同时承认可信原件逐件核验仍有实际 I/O 成本。不得宣称任意长度组合都可执行。

测试和 CI 没有因本轮设计审查新增，暂未发现新的冗余。后续优先扩展原 work_delivery fixture／已有运行与回放入口，覆盖实际静默错误风险，避免新建镜像驱动的测试或 CI 作业：

1. 原长链／并行扇入进入新版本后全结果及祖先正文保持；未绑定端口的直接控制依赖也可见。增加合法 profile 产物及未在 profile 列出的可信 test-results，防止硬编码名单。
2. 未内联审计被篡改仍拒绝；可信 review 意见完整、advisory request-changes 原 FAILED 保持；candidate／session／原 claim 等门禁复用既有反例，不必把每条旧断言复制一遍。
3. 同一历史 v5 输入／保存调用／原 receipt 保持；新版原调用恢复不另发 writer；旧 history 与新 history 分开重放。完整声明结果或祖先真正超预算仍拒绝，不截断。
4. 最终非 editable 包和两 RECORD／冻结身份、两个新任务实际六阶段与精确批准／evidence／handoff／history、真实自身模板及完整候选独立两轴审查，均针对自己的精确候选。已有必要 CI 继续使用，不能借前片结果完成本片。

## M0 时点门禁与未验范围

Spec 开放 1 项：C5C-SP1，两个域的交付未完成。Standards 当前检查范围开放 0 项；实施和终审仍待。M0 允许按已明确的新版本 B 实施，不批准在旧 v5 中缩减端口合同。

M0 时点未验：M1 完整 diff、新版本来源投影和版本传播实现、新旧 history 实际回放、新服务旅程、真实模型质量／自身审查、最终安装包、自己的 CI 与远端精确对象。原治理回放为作者记录的 pass，本审只核保存的 history 摘要和事件数，没有再次调用 Replayer。清理只核原采样范围，不能据此证明每个短命进程都曾被观察。完成候选后由本审查者在本片复核，状态再更新；报告和记账不递归启动审查。

## M1 固定候选与独立身份

2026-11-11，接续同片复核。固定对象为 `review-m1/identity.json`、`tracked.diff`、`files/`，**31 份完整文件 = 23 份 Git 候选文件 + 8 份私有驱动**，逐件长度与 SHA256 全符；补充快照两份 = 同一最终 fixture + 新运行 wrapper，逐件相符。已变更内容只按冻结 files 审，不以进行中的工作区替代。`baseline..HEAD` 没有新提交；非空差异是固定 tracked.diff 加 identity 明列的新文件。

独立重核 439 份源／wheel／非 editable 安装文件、wheel 与安装两份 RECORD、283 冻结参考，全部一致；wheel SHA256 为 `aca2ea19761a0011d4b2b10851962733a5f77990dfc4f8e34450ad6901ecf9d5`。原 R2 核过的 153 份旧任务／产物／scope／history／handoff 文件再核 SHA 无变。此处没有读取旧凭据；后续 wrapper 的更大原目录前后清单另待完成后核。

原安装包定向检查 5 通过／19 未选；最终 fixture `c28885c5…` 的增强串行单例另有 1 通过／23 未选，pytest 42.68 秒、外层 46.88 秒。它实际覆盖四 writer 扇出／扇入、未绑定端口的控制依赖、advisory structure 原 FAILED 及完整可信意见流入两个 required reviewer。首轮源探索 3 通过／1 次 MCP timeout 失败保持；不能因其混用旧安装包就推断失败原因。

本轮按 code-review 对真实代码差异启动两个 fresh-context 子审；它们只读固定候选和邻接所有者，没有启动新的报告审查。原报告与廉价 AST／字节证据保存在 `independent/axes-m1-spec.md`、`axes-m1-standards.md`、`axes-m1-spec-evidence.json`；主审身份与原件核验保存在 `m1-identities.json`。

## M1 Spec

审查者 `/root/composition_runtime_review/m1_spec_axis`；主审复核同意其限定结论。

- **C5C-SP1／P1 继续开放，验收未完成，非新增代码缺陷。** M 规格要求“两个新任务实际六阶段／证据／handoff／history 通过”；M1 交接尚无完整出口，原大变更 BLOCKED 保持。定向回归不能替代两域旅程。最小处置是用最终明确身份的 v6 候选完成出口，再补自身模板和精确交付检查。
- **未发现可证的非请求行为或新增实现错误。** v6 Input／Adapter／Workflow 在本族独立注册并继承原算法；v5/v6 和对应 protocol 绑定，新建页面选择 v2，旧 v1 可选。结果集合覆盖 profile、全部 checks 引用与可信阶段补集；work、review、plan／verification 在投影前仍经过原 FileAdapter 全件核验。来源表覆盖端口和直接控制依赖并集，可信审查意见沿原 reader 读取。
- **恢复证据范围准确区分。** 保存调用恢复分支与 `_composition_context` 的源码及 AST 同基线；相同材料下 16 组 v2–v5 work／review task 文本逐字节相同。原 v5 全表回归通过，四组非默认 profile 结果并集离线求值正确。当前重复执行检查发生在 terminal receipt 已发布后，不能称为“提交后、回执未发布”恢复实测；该分支的静态保持证据不等于此次重新执行。若后续授予这项实测结论，应复用已有 recovery 入口一次覆盖新版，而非重建整套恢复测试。

Spec 总计 1 项既有验收 finding 继续开放，最严重为 C5C-SP1／P1；新增可证产品代码 finding 0。

## M1 Standards

审查者 `/root/composition_runtime_review/m1_standards_axis`；主审复核同意以下两项收口问题。

- **M1-ST1／P2，完整读取存在验收漏检。** 冻结私有 `journey-r2.py:160` 只要求 fixture 回执的 files 非空；fixture 完整读取 list 返回项，但如果 list 漏掉一个原 scope URI，当前旅程判断仍可通过，不能独立证明完整祖先／附件读取。来源为 PLAN 的完整读取要求与独立审查“测试检查合同”的要求。最小处置：按原 run 的固定 `task_mcp.scope` 精确比对 URI 集合、摘要、长度、全文与分页，并核 scope／input／instance 身份；可在本审独立补核原件后处置，无需因此重跑已完成服务或模型。
- **M1-ST2／P3，恢复入口过时。** 冻结 `docs/PLAN.md:18` 仍称“独立设计审查和修正尚未完成”，与同一快照 M 规格／delivery 中 M0 完成、M1 源实现待验矛盾。违反 AGENTS 状态变化同步 PLAN 以及 maintainable-project-delivery 先同步计划／记录的规则。最小处置是同步为 M0 已过、M1 候选和 M2／M3 的真实状态，并链接当前 C5c 记录。

生产结构无 finding，启发式 smell 无可行动项。`_declared_results` 归原 Executor，在 work、review、plan／verify 路径真实共用；版本 Input／Adapter／Workflow 是既有 Interface 的具体注册与框架 hook，不复制调度。没有新增生产文件、依赖或 CI；测试扩展原 fixture，未发现新增冗余。3.59 秒只证明旧失败复现，新方案性能仍需实际 task／prompt 尺寸和阶段用时；全审计核验的 I/O 成本仍存在。

Standards 总计 2 项收口 finding 开放，最严重为 M1-ST1／P2；生产结构和新增可行动 smell 为 0。

## M1 时点门禁

M1 固定代码候选静态可继续验证，不能据此宣布 C5c 完成。等待实际 v6 两域原件、完整读取补核、PLAN 同步、真实自身模板、最终候选审查和精确交付。未启动服务／模型／测试／安装／网络；没有将正在运行的旅程记为通过。先前关于大 backend_reason 可能触发审计预算的假设，经公开 schema 的 2,000 字符上限核对后不成立，没有作为 finding 或修复要求。

## M2 同一 run 续段与完整资源补核

2026-11-11，主审只读检查完成的 `r2/journey-resume.json`、两 checkpoint、原 stage envelope／receipt／input／scope／读取回执、history、handoff 与 wrapper／清理原件；没有再次调用服务、模型或 Replayer。`verify_r2_runtime.py` 与 `r2-runtime-scope-audit.json`、`r2-runtime-files.json`、`r2-runtime-handoff-audit.json` 保存独立核验过程和摘要。

首段 wrapper 269.30 秒退出 1：两任务的全部工作与审查 receipt 已成功，私有驱动却要求大变更每名 reviewer 的端口结果等于所有 writer。原冻结 `ergora-large-change-work` 的 done 只依赖 integration-tests；其 review 端口实际只绑定该叶。前面的 contract／server／client 是完成依赖闭包，不自动成为下游数据端口。治理的 done 直接依赖两个 writer，原全集断言只是对治理碰巧成立。该错误属于私有验收驱动，不能把原失败轮写成成功，也不能为满足断言给 review 暗加数据。

修正续段按原冻结 `input_ports` 核期望，只启动 owned Temporal 读取原大变更 run；没有启动 worker／executor、重复创建／批准／work 或更换 ID。服务续段 11.88 秒、wrapper 14.62 秒退出 0；补齐原 run 的 evidence、同 ID 重复 start、handoff 和 history 记录。独立核得：

|域|原 run|状态／job／原生调用|候选|history|
|---|---|---|---|---|
|治理|`01a1c892-6943-7842-8f04-a84f5c91f76d`|REVIEW_READY／9／5|`f0820df3cebc4316f1422d7057902653f7930958`|194 事件|
|大变更|`01a1c894-0ad4-7350-8a4b-7813b65cb9f5`|REVIEW_READY／11／7|`9049f4de6be3bd8e57a791a66a696bd48ad91df5`|240 事件|

- **M1-ST1 关闭，处置为本次原件独立补核。** 从每个 admission 完整冻结文件和具体叶 resources／全部来源推得精确资源集合；12 份 prepared manifest 完整树、input 资产／正文／摘要与冻结资产相同，完整 prompt 与原叶 prompt 加本次 task 逐字节相同。实际 scope 的 URI 集合、byte／SHA／全文与其精确相等；fixture 回执无重复或遗漏，全部正文与连续 offset 页相符。合计 **54 份资源、17,740 B、54 页 UTF-8、0 页 base64**。本轮没有二进制或跨页 UTF-8 边界的实际样本，不授予该未验范围通过；这是协议 fixture 实际读取证据，不是模型理解证据。私有驱动的非空检查没有被称为通用完整性验证器。
- 20 个 job 的原 context／admission／receipt 身份与 154 份产物 SHA 相符。原生调用的 prompt／input／scope 摘要一致；work 的正式调用与实际 invocation 匹配。来源表为实际端口与直接控制依赖并集，结果正文完整等于原声明产物；大变更 reviewer 确为原 integration-tests 端口。history 保存摘要、事件数和初始原 admission payload／v6 workflow／queue 一致；handoff SHA／ZIP CRC 及原已验证回复相符。history replay 为原驱动实际运行的记录，本审没有重放。
- 两次重复 start 的保存回复均与首次完全相同。四份原目录前后摘要表完全相同，均为 1,677 个文件；旧任务原失败保持。主审另核过的 153 份旧原件无变。首段 134、续段 2 个实际采样进程均无剩余记录，只证明原采样范围。
- 大变更 integration-tests 的完整 task **26,300 B**、prompt **29,617 B**；本次两域最大完整 prompt 为 **30,631 B**。这是同类小领域结果下停止审计递归复制的实际尺寸证据，未提高限额或减少祖先。首段失败和续段读证据耗时分开保留，不把它们合成一个无失败性能基准。

**C5C-SP1 关闭于两域实际协议协作范围**：修正后的明确 v6 wheel 已完成这两个 fixture 项目的六阶段与原件交接。原 v5 大变更仍 BLOCKED，不改写为通过；真实模型质量、真实项目质量与不同模型独立性不由该结果证明。M1-ST2 仍待最终 PLAN 身份复核；M3 的真实自身模板、最终完整候选、自己的 CI／远端精确对象仍待，不授予 C5c 完成交付。

## M3 最终本地候选与真实自身原件

2026-11-11，同片接续只读复核 `final-candidate-r2`。**27 份完整 Git 候选文件 = 原 23 份 + 4 份公开 JSON**，逐份 SHA256／长度与固定身份、当时工作区相符；tracked.diff 与同基线实际差异相等。此后仅由本审追加当前报告，状态记账不递归审查。六份产品源与两测试文件同 M1；439 份源与 M1、最终 wheel、非 editable 安装、wheel／安装两 RECORD 再次逐件一致，283 冻结参考保持，原 R2 与最终 package-identities 的完整 files 表相等。没有新生产文件、依赖或 CI 变更。

独立 `verify_m3.py` 只用标准库读取原件，结果保存在 `m3-identities.json`、`m3-self-review-audit.json`、`m3-public-projections.json` 与 `m3-files.json`。没有执行作者的模型审计或公开投影程序，没有读取 inference 配置／凭据，也没有启动模型、服务、测试、安装或网络。验证器自身四次类型／表示层断言修正及最终通过保存在 `m3-probe-attempts.json`，没有据此修改产品或重跑行为。

- **实际安装模板身份成立。** 从当前 wheel 安装的 bundled structure-review 派生证据修订 1.0.84；agent 仅改变版本并追加完整 candidate-evidence Skill，workflow 仅改变版本、该叶精确引用及材料预算 450,000 B，其余基准文件逐字节相同。原 reviewer 职责及父子 read-only 权限相同；Codex 是明确回退绑定，不冒称不同模型独立。原活动定义库不在控制目录，retired 索引仍保留。
- **输入与权限链成立。** 完整 manifest 资产／组合图、准备 input 与实际 run input 的树摘要及正文相同；本次 prompt 与叶装配加完整 task、实际 stdin、协议 prompt 逐字节相等。原 admission 的全部共同字段与实际 run 相等；两者文档 kind 按各自合同不同。run 的 `formal_execution_authorized` 为 false，这次结构审查不代替正式批准。
- **完整读取由原生事件证明。** 从冻结资产和全部结构祖先来源重新推得精确 scope，五 URI／263,137 B 与原 scope 的正文、长度、摘要及来源相等。实际 JSONL 只有 agent_message 和 task MCP 调用：1 次 list、25 次 read；原 native 审计的相同 scope SHA 和调用计数匹配。list 完整结束于 null；每次 read 的调用参数、切片、SHA、总长与 next_offset 均核对。附件 **261,486 B** 以 **13 页连续 UTF-8** 从零重建到 null，另保留 **8 次同 offset 的 base64 窗口缩小重读**，没有失败 read 或重复页；base64 窗口没有被计作已消费纯文本。其余四份指令／Skill 也各完整一页。
- **审查对象与结果相符。** 附件 21 份具名完整原件的标记、原字节数及 SHA 全符；八份源／测试与当前最终候选相同，所含完整产品／测试／手册 diff 也同最终候选。两份大表投影的省略标签和内容明确相等，不声称模型检查省略的 raw maps。规格／交付状态文档保持其模型输入时点，四份后来公开 JSON 由本次独立补核覆盖。原 native 结果 JSON 与规范化 run 结果语义相同，run 与 original-result 字节及 SHA 相同，response 与 review.md 相同；实际 succeeded／exit 0／229.91 秒、decision approve，Spec／Standards 无具体 finding。原结果 SHA 为 `eebe35ffb2231d98c1a03af25dee0a39f13e5b67b13080c332da2a014d3e280c`。
- **用量与清理按原范围记账。** 实际 turn.completed 自报 input_tokens 1,922,542，其中 cached_input_tokens 1,761,536；output_tokens 3,900，reasoning_output_tokens 1,583 单列，未重复相加。这不是账单或推理质量评估。模型清理原件覆盖实际采样的 4 份 CLI／后代身份，剩余 0；没有全量短命进程声明。

## M3 公开投影、ST2 与最终两轴结论

四份公开证据合计 **26 条投影记录**，均从相应私有原 bytes／SHA 独立重建后逐字段相等。普通记录仅作明确的顶层省略和仓库／home 路径占位；五份清理记录明确省略 PID 表，并由原采样数量／remaining 列表衍生计数，scope 原文保持。没有实际仓库／home 路径留在公开 JSON。大 files 表未公开的事实保留；本审另外核过的完整原件不能被表述为公开投影本身携带了这些表。本次没有重复读取环境秘密值来做扫描。

**M1-ST2／P3 关闭。** 固定最终 PLAN 已移除“独立设计审查和修正尚未完成”，链接当前 C5c 交付，并同步 M0–M3 的实际状态；C5 分片、AC5 父表与两规格均说明原 v5 失败、新 v6 实际完成和最终／精确交付待验，不再称修正设计中。最终文档另核 239 个本地文件链接可解析；锚点／浏览器执行不由此证明。

最终 Spec：开放 finding **0**，新增产品代码 finding **0**。C5C-SP1 已按 M2 新 v6 两域实际协议交付范围关闭，原 v5 BLOCKED 与驱动失败保持；M3 原件／完整模型读取和最终候选核验没有发现新的失配。

最终 Standards：开放 finding **0**，新增生产结构／可行动 smell **0**。M1-ST1 以原件独立全链补核处置，M1-ST2 以最终固定状态同步处置。最终产品源未变，沿用 M1 两个 fresh-context 轴的完整代码检查，由同片主审检查新增原件、公开投影和文档差异；没有新建冗余测试、CI 或抽象，也没有再次派生报告审查。

**完整最终候选本地出口通过；精确交付尚未完成。** 可普通提交／推送本次候选，随后仍须核自己的必要 CI、精确 Git 对象及独立远端同 SHA，不能借用 C5b 的 CI。当前未提交，故本报告不授予这些待验项通过。后续只有状态／审查记账变化无需重跑已过模型或服务。

保留未验范围：新 v6 页面浏览器旅程；调用提交后、receipt 发布前的实际崩溃恢复（保存分支静态保持与 terminal receipt 重复返回已有各自证据）；无限长链／任意节点数或真正大业务结果；模型／项目质量、不同后端独立性、宿主隔离、GPU／未配置外部平台。尺寸与不同轮耗时只支持实际边界观察，不构成受控加速结论；原 history replay 是驱动实际执行的保存记录，本审没有再次重放。

## M4 精确提交与首份远端样本

2026-11-11，同片核普通提交 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`，唯一父提交为基线 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`。完整 **27 个精确 Git 对象**逐份等于 `commit-closure/ready` 的原字节数／SHA 和 files 正文；ready 的 19 份 tracked.diff 与同一提交对应文件差异相同，其余新文件也由完整身份和 Git 正文逐件核验。与 M3 固定输入相比，仅本审报告续记及六份状态文档前移；产品／测试和四份公开 JSON 无变。原报告 M3 完成本地出口的 SHA 与 ready 收录相同，状态措辞符合本地通过、精确交付待验。

独立从该提交的 Git archive 取全包，439 份与 M1、R2／最终身份表、wheel、非 editable 安装和两 RECORD 再核一致，283 冻结参考保持。原普通 commit／非强推原件退出均为 0，push 明确只更新工作分支，没有 main 合并。这里依据精确 Git 对象，不以可能继续推进 C6 的可变工作区代替。过程保存在 `independent/verify_precise_commit.py`、`precise-identities.json` 和 `precise-status-delta.diff`。

经本次明确授权，仅做 **一次**独立有界 HTTPS-only 官方 refs 读取：从无仓库配置的 `/` 调 `https://github.com/626619403/Ergora.git`，禁用全局／系统 Git 配置、凭据 helper／交互、重定向和非 HTTPS 协议，TLS 校验保持。45 秒上限内实际约 **21.53 秒**以 Git exit 128 结束，stdout 为空，原错误为 `gnutls_handshake() failed: The TLS connection was non-properly terminated.`。trace 只见 remote-https，没有 SSH 重写；原 stdout／stderr／trace／摘要保存在 `independent/https-remote-01/`。未取得 refs，故没有远端 SHA 通过结论；没有自动重试。

本提交自己的首份官方 CI 原样本 `commit-closure/snapshot-01/ci-sample-error.json` 记录 `SSL: UNEXPECTED_EOF_WHILE_READING`，`sources: []`，没有取得状态。它不是 CI success 或 failure，也不能从推送成功推断 CI 已通过。按授权等待新的原官方样本，未主动 poll 或重跑 CI。

随后获第二次且仅一次的明确授权，改以标准库 urllib／默认验证的 SSLContext，对官方 `info/refs?service=git-upload-pack` 作一个 HTTPS GET，禁止重定向、自动重试和 SSH，预备按原 pkt-line 公告核同一完整 SHA。实际 **20.14 秒**在握手阶段超时，原错误为 `The handshake operation timed out`，没有 HTTP 状态／正文或可解析公告；因此不能授予远端身份通过。`independent/https-remote-02/` 保留 result、响应元数据、空原正文及空解析列表；首次 GnuTLS 失败保持。没有发起第三次请求，也没有主动查询 CI；远端受限不阻断独立的 C6 工作。

**M4 当前出口：精确 Git／包／状态差异通过；独立远端同 SHA 与自己的必要 CI 仍待。** 本地 Spec／Standards 开放 0 保持，精确交付尚未终结。C6 后续测量和其他候选结果不转授本提交。

## M4 官方 Git Ref API 与首份可读 CI 样本

再次明确授权后，对不同官方主机 `api.github.com` 仅作一次独立 HTTPS Git Ref API GET；默认 TLS 证书／主机校验保持，无认证、重定向或自动重试，未调用 Git／SSH。实际 **1.29 秒 HTTP 200**，完整原 JSON **429 B**，SHA256 `8c72ce629e2c1daba6bad089fa8d1b383ae8aa408e712bef0dea253c86bc21f9`；精确 `ref` 为 `refs/heads/refactor/architecture-foundations`，`object.type` 为 commit，`object.sha` 为 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`。响应状态、完整 headers／原 JSON／请求摘要保存在 `independent/https-remote-api-01/`。

初始请求 helper 在核过上述三字段后，额外错误要求响应 url 使用请求的单数 `/git/ref/`；官方原响应使用标准复数 `/git/refs/`，导致该附加断言退出 1。原 helper／result 和 HTTP 正文保持，随后只离线核原 JSON 的三项合同及合法 canonical URL，通过结果另存 `offline-identity.json`；没有为修正验证器再发请求。**远端精确身份按这份独立公开官方 API 原响应通过**，不声称前两次 Git 传输取得了 smart-Git 公告。

作者提供的 `commit-closure/snapshot-api-01` 两份官方原 HTTP body（runs／jobs）逐份字节数／SHA 与 source 元数据相符，URL／final URL 均为官方 API、状态均 200。离线按该提交的原 `portability.yml` 核 run **42954686614**、push／工作分支／精确 head SHA、仓库身份、run attempt 和两个 job，摘要与原文一致。七个必要步骤中，Windows 四项 completed／success，Linux build／identity 两项 completed／success，但 Linux regression 仍 in_progress；run 也为 in_progress、conclusion null。条件 Windows installer 不被算作 Linux 必要步骤，不能把当前六项已过误写为七项全过。原件与结论保存在 `independent/ci-api-01-audit.json`、`verify_api_and_ci_first.py`，本审未发 CI 查询、poll 或重跑。

**M4 最新出口：27 精确 Git／439 包／283 冻结及独立官方远端同 SHA 已通过；自己的必要 CI 终态仍待。** Spec／Standards 开放 0 保持；精确交付尚未终结，等待提供正式终态原件后同片离线续核。原 TLS 失败和非终态样本不回写为成功，不阻断 C6。

## M4 正式 CI 终态与精确交付终结

2026-11-11 **04:02:29 UTC** 的第四份状态样本（`snapshot-api-02`，第二份 API 样本）已正式终态。本审仅离线核两份原 HTTP body：runs **12,000 B**、jobs **5,208 B**，逐份 SHA／字节数与 source 元数据相等，URL／final URL 均为官方 API，HTTP 均为 200。run **42954686614** 精确 head SHA／分支／push／`portability.yml`／仓库身份和 run attempt 1 相符，整体 **completed／success**。

按该精确提交的原 CI 定义，Windows Python 3.12 的 build／reference identity／application regression／PowerShell 5.1 安装升级四项，以及 Ubuntu Python 3.11 的 build／reference identity／application regression 三项，**七个必要步骤全部 completed／success**；两个 job 也均 completed／success。与前份 API 样本是同一 run、同一 attempt、相同 job ID 和步骤开始时间；此前已完成的步骤正文保持，Linux 原在运行的回归现于 04:00:32 UTC 成功结束，没有借用其他提交或重跑结果。摘要的每份 required_steps 与原 jobs 对应项完整相等，Linux 条件不适用的 PowerShell 步骤不进入七项集合。

前两份 TLS 未得状态样本仍分别保留 `sources: []`；前份 API 样本仍为 in_progress／六项成功一项在运行，其原 runs／jobs SHA 与此前独立审计相同，没有覆盖为本次成功。前两次独立 Git HTTPS 失败、随后官方 Git Ref API 原响应及附加 URL 断言的离线处置也保持原记录。此次没有发网络请求、CI poll、测试／服务／模型／安装或重放。

`independent/verify_ci_terminal.py`、`ci-terminal-audit.json` 和 `ci-terminal-files.json` 保存终核。本次重新逐件核 27 个精确 Git 对象仍等于 ready 及先前独立身份，439 份 Git／wheel／安装／两 RECORD 与 283 冻结的既有核验仍精确绑定该对象集；独立官方 API 原文的 ref／commit 类型／完整 SHA 与先前审计相同。核验依据提交对象和原件，未用 C6 的可变工作区或后续测量代替。

**最终出口：C5c 本地及精确交付通过并终结。** 对象为 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`，自己的 [CI42954686614](https://github.com/626619403/Ergora/actions/runs/42954686614) 双 OS 七必要步骤、独立官方 HTTPS API 同 SHA、27 Git／439 包／283 冻结均已核实；Spec／Standards 开放 finding **0／0**，C5C-SP1、M1-ST1、M1-ST2 按各自已记录范围关闭。原 v5 BLOCKED、私有驱动失败、TLS 未得状态与非终态样本不回写为成功。前述未验产品／模型／平台范围仍不授予通过；C6 与项目其他后续工作继续单独验收，报告／状态续记无需递归审查。
