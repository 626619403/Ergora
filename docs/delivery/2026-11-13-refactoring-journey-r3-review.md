# D2-A2 第三轮真实重构旅程独立评审

**本次本地 A2 旅程及独立证据验收通过；Spec／Standards 最终开放 findings 为 0／0。普通发布、远端精确身份和本候选必要 CI 仍开放。**

日期：2026-11-13。主审为 fresh-context agent `refactoring_r3_evidence_review`；按项目 `AGENTS.md`、AI Hero 索引 1.3.2、`maintainable-project-delivery` 及 independent-review brief、`code-review`、`codebase-design` 执行。另以 `fork_turns:none` 启动互不继承实现讨论的 `spec` 与 `standards` 子审，分别出具判词；两轴不互相抵销。原 Spec 子审另完成下述同候选离线结构补核。

## 固定范围与身份

固定基线为 `e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`。初审开始时 HEAD 与基线相同，`git diff <baseline>...HEAD` 和 `git log <baseline>..HEAD` 为空；实际对象是明确列出的四文件未提交快照，已逐文件与基线内容比较，没有把空提交差异当作无改动。

快照均位于 `.ergora/checks/refactoring-journey-r3/`：r1 manifest SHA256 为 `663e2247e63eaae8e5c31640b66f55107e9a1821450d8453b91011724ac59985`；r2 为 `15585bf8d54ca9ebccf90390b3d11df8e091063d84b85e213793d53352202ef4`；最终 r3 为 `609abae8aaa9af412ef07bc2c4bb6cbd1bd5d5914e401eb14cfa0d8c365769e8`。每版四文件均已按 manifest 复算；r1→r2 只改 PLAN 状态，r2→r3 只在交付记录增加本报告及结构补核引用，没有改变原件或公开证据 JSON。

|最终 r3 文件|SHA256|
|---|---|
|`docs/delivery/2026-11-13-refactoring-journey.md`|`2cef866d5c88bad49ef24a74f81383aa3df250240cf9586fe57401e4c29ddae3`|
|`docs/delivery/evidence/2026-11-13-refactoring-journey-r3.json`|`a0878f3928a42dfa4abd00bff7b9e5b7d357479787d940e6e833bc7d75116f23`|
|`docs/PLAN.md`|`77534f94bb6cfcc23fd2ea5b1ab03cdc35996f73dabd6674fcdd052c5fe3bd70`|
|`docs/plans/2026-11-13-specialist-presets.md`|`31621f92327fb6146b9cd9dfe2d1b48697db258fbd9bc9820ee709e072b6608e`|

原始规格为 [D2 计划 A2](../plans/2026-11-13-specialist-presets.md) 第77–83行及本片原始验收要求。规范来源为 `AGENTS.md`、PLAN 稳定规则和上述交付技能；未发现额外适用的项目 `CONTRIBUTING.md`／`CODING_STANDARDS.md`。本片没有新增产品实现；stdin／轮询修正及 B2a 实现不在本报告重审范围。评审期间相邻片的普通提交不改变这里固定的比较基线与快照。

|运行身份|原件核对|
|---|---|
|project／task／workflow|`native-refactoring`／`refactor-module-3`／`dev-task/refactor-module-3`|
|原 run|`01a1d3ba-600c-7c5f-b4e2-0e52c156d305`|
|fixture baseline|`19cd20e31210eb938020df034427f53dcc9c76ed`|
|最终导出候选|`63004b35f123e0efa49f3746627247d9036d1de8`|
|精确 plan|`113e5cd337aedb013237fa3d5634478e1dcb098298bce5b031050d9a07d4a9e1`|
|预算 ID／SHA256|`73cab749f22c48e9945538de025a9670`／`19b7d833ccf84fd6b3b78f65c3d87a58913072b72005b1bb4d052e92b3356f23`|
|安装 wheel|`85e20a342361f8fda1233f607dc94679364a0691b0b5452bb6b274648d117ab7`；非 editable、497 产品文件，与原安装记录相符|

## Standards

**初审：一项 P3 文档状态 finding；原件完整性无阻断。同片复核后：通过，开放 0。**

**R3-ST1，P3，已关闭。** r1 的 `docs/PLAN.md:7` 仍写“正在补核全部会话材料／串行前驱／预算与清理原件”，而同一冻结交付记录第75–81行已记录这些核对完成，原 model／closure audit 也支持完成。它违反 `AGENTS.md` 的“Update `docs/PLAN.md` when … validation finishes”及交付技能要求在评审前同步 report 和 plan 的规则，恢复者会混淆已完成的原件核对与待完成的独立评审。

最小修正已进入 r2：当前检查点明确原件补核完成，仍将独立验收和发布列为开放；随后一条区分已核 A2 证据与在途评审。原 Standards reviewer 复算 r2 manifest／四文件并检查仅 PLAN 的差异，确认 R3-ST1 关闭，无新增 A2 finding。相邻 B2a／CI 状态未由本次增量复核授予验收。

Fowler smell baseline：所审文档／证据片没有可定位的新增产品代码 smell。两轴均未将运行材料保存为公共文档正文，也未披露认证内容或本机运行路径。初审静态核对的118个本地文档目标均存在；最终新增报告及结构补核锚点另作同片核对。

## Spec

**初审：一项 P2 验收证据缺口；运行与候选声明其余部分相符。同片结构补核后：通过，开放 0。**

**SP-R3-1，P2，已关闭。** A2 第81行要求“结构审查用真实caller、Depth、Locality、Seam及deletion test检查收益”。原 structure job `refactor-module-3-7a38a723440b2a99a56774ae` 的 `review-report.md:3` 说明复用已有所有者、Interface 不变及 caller 身份，足以支持所有权、Locality 和 Seam 的一部分判断，但没有记录删除 `normalize` 后复杂度回到何处的反事实，结构收益的验收证据因此不完整。这不是仅因缺少术语而报错。

最小补救是保留原 session／report，针对同一精确候选补独立结构评价。原 Spec reviewer 已直接检查 baseline、导出候选、真实调用、合同、所有权与 diff，完成下节补核并明确关闭 SP-R3-1。它没有重跑原模型或任务，也没有增加原 receipt。四文件内未发现实质越界或额外错误运行声明；B2a 相关文字只作邻片状态，不授予其实现验收。

## 独立离线结构补核

以下为原 Spec reviewer 的补充独立离线评价，目标仍为候选 `63004b35f123e0efa49f3746627247d9036d1de8` 和 baseline `19cd20e31210eb938020df034427f53dcc9c76ed`。导出分支仍指向该候选，fixture 当前 HEAD 仍为 baseline。

**Depth 与实际 caller。** 既有 `normalize(value)` Interface 拥有字符串类型校验、精确 TypeError 以及 strip／lower／split／join 行为。它的既有 Depth 被保留，并用于另一条生产路径：`client.request` 在 `src/example/client.py:5` 直接调用它，`aliases` 现在于 `src/example/normalizer.py:10` 调用它。两者位于两个不同生产文件，共享行为而不增加参数、配置或协调要求。

**Locality 与所有权。** 校验和规范化现在只在 `normalize` 实现一次，去掉 `aliases` 中的重复算法，减少 canonical 值与 aliases 在错误消息或 Unicode 行为上漂移的机会。迭代、空值过滤、按首次出现去重和 tuple 构造仍由 `aliases` 拥有；职责继续留在既有所有者内。

**Seam。** 既有两个公开函数仍是 Seam。名字、参数、导入和可观察的返回／错误合同保持；没有引入 wrapper、依赖、registry 或推测性扩展点。真实 caller 测试与受保护差分 checker 通过这些 Interface 检查行为。

**Deletion test。** 删除 `normalize` 会迫使 `client.request` 的 canonical 路径和 `aliases` 的逐值路径各自恢复校验与规范化算法，或将它放入另一个共享所有者。复杂度会重新分布到这些 caller，因此既有函数有保留价值；本次候选让它承担更多真实复用。

实际收益小而具体：通过既有 Interface 共享行为、改善 Locality，源码恰好以委派替换重复校验／表达式。所审合同只涉及内存值，不需要 caller 迁移或持久格式转换；改动限于批准的实现、测试和报告路径。原 Spec reviewer 结论为本范围无结构 finding，SP-R3-1 由此补充证据关闭。

这是补充的独立离线审查，**不是原 Temporal 任务新增会话或回执**。原 native structure 判词、原 aggregate、七个原会话和七个预算槽均保持。

## 原件及独立验证

直接读取 `.ergora/checks/refactoring-journey-r3/` 的原结果、命令、完整历史、公开投影所列原件及持久运行存储的原 task／control runs／jobs／receipts／artifacts／ingress SQLite。SQLite 使用只读连接，未触及认证或 inference 配置。原驱动 `real-journey-r3.py`、`audit-journey-r3.py`、`close-success-r3.py` 已检查；其摘要不是本报告的唯一依据。

|验收事项|实际核对与结果|
|---|---|
|原入口及 owner 批准|原 CLI prepare、双摘要 create、start 的命令和输出相符；三个精确 plan 材料的正文／SHA 与 owner assessment 相符。原 human owner receipt 的 canonical SHA 等于 outcome 的 approval SHA，history 第182事件是该 plan 的 `approve_plan` signal；driver 等待人工决定，没有自行批准。|
|串行工作与可信阶段|rewrite 于07:14:40.285809 UTC结束，compatibility 于07:15:00.468038 UTC开始；后者冻结 materials candidate 等于 rewrite 回执候选 `8540b1849b6b5a3dd78b3a23a1e8d2e695c2bcce`。原 integrate／verify 均为可信阶段、同最终候选。|
|独立 review|structure／correctness／test-value 三个不同原会话、不同 thread／actor session，分别有 required／approve 决定且都绑定最终候选；compatibility unit 未被充作独立 correctness review。原报告的直接源码和外部 caller 等限制保留。|
|完整材料|七会话的原 manifest→input→task／materials→prompt→protocol／stdin 链逐字相符；各 scope 的内容、长度、SHA 及 sources 均与冻结 input asset 和原 manifest object 相符。38资源／23,329B 的原 native JSONL 证实连续 UTF8 读取至 `next_offset:null`，失败 MCP 调用0。主审另以只读 SQLite 在内存中复验原 audit 全部断言，不写回原报告。|
|owner／receipt／预算|九个原 owner 的 PID／start 身份不存活，body 和 collection 停止见证确认；九份可信 SUCCEEDED receipt 与公开 evidence 相等，85个回执产物引用逐一重算。七份 model-attempt 精确等于原 budget slots。九个 receipt 的 canonical digest 均区别于原文件字节 SHA，核对时分别处理。|
|导出／handoff／claim|原 export candidate、实际本地 agent 分支与 outcome 一致，原 HEAD 仍为 baseline；SQLite active 表为空，原 claim 有 released_at 和 evidence digest。handoff 的79个唯一 blob／1,193,072B、85个 receipt 引用、canonical index digest 及原 outcome 均重算通过。handoff 验证只证明包字节及声明内部身份，不扩大为外部来源认证。|
|原 ID 与历史|duplicate start、Temporal-only 重启后的原 run status／submission 与首次保存对象相等。623事件／6,111,384B 历史的首 input 与原 input10 task spec 完全相同；61个 poll 只有三个身份字段，合计10,065B，原 patch marker 存在。|
|独立离线 replay|使用已安装候选的 `WorkflowHistory.from_json`、原 workflow type 和 `Replayer.replay_workflow`，623事件重放通过，0.448秒；history SHA256 为 `22bb6bd0327c3bdb90075cc3bb3b7e90cd4b56ba70d4d4fda781a394a13d37c9`。SDK 的一次 import warning 未造成 replay 失败。未启动 Temporal 服务。|
|独立导出候选复验|通过只读 `git archive` 将精确候选提取到评审私有 scratch，保持 checker 与 baseline 字节一致，再执行受保护 `checks.py <exact-baseline>`。212 normalize／6 aliases 差分、generator、2个真实 caller unittest、独立精确 baseline 源码恢复均通过，exit0／0.199秒。scratch 已移除；原 Git HEAD 前后相同，没有创建／删除原 worktree 或修改 Git 对象。|
|清理范围|原 shutdown／cleanup-status 保存 confirmed／daemon not_running，原 driver 记录三端口关闭；持久 Temporal 数据库仍在。本次未作端口探测、全系统后代采样或额外清理。|

公开投影列出的15个原件字节 SHA、handoff SHA、四文件快照身份均已复算。首轮 BLOCKED、第二轮 TERMINATED、各自原预算及原恢复／harness 失败仍保留；本报告不将它们重写为成功。第三轮公开投影的 `remaining` 与早期“在途”段落保留其原记录时间，最终本地评审状态以本报告及交付记录末节为准。

## 最终范围与未验项

原件和源码支持本次小型行为保持重构、原任务生命周期、串行前驱交接、同候选三类 review、原 ID 重复／重启读回、完整历史重放、精确导出及本地隔离恢复、原 owner／claim 清理。补核没有增加原预算、替换 receipt 或改写失败。

这些证据不证明模型理解、异构后端独立性、GPU 收益、Windows 旅程、生产部署或生产回滚。7次原调用均是授权的 Codex 回退；独立上下文不代表不同后端。不同轮次历史大小不能用于严格同负载性能比较。没有重跑模型、服务、安装、完整 suite、网络探测或执行任何 Git 写操作。

r3 相对 r2 的新增文字准确指向本报告及“独立离线结构补核”，没有把补核写成原任务新增会话。后续纯结案记账不扩大为产品代码验收；普通提交、远端 Ref 和精确候选必要 CI 保持各自出口，不能借旧片结果关闭。

两轴初审各1项：Spec 最严重为 SP-R3-1／P2，Standards 最严重为 R3-ST1／P3；同片补核后分别关闭，最终开放 0／0。
