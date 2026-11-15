# Q4.2c0.2a：出生同意与父停止记录独立产品审查

日期：2026-11-15。审查者为新的 fresh-context 独立 reviewer `training_cycle_admission_product_audit`；未继承实施对话。先读原始要求、[本片合同](../plans/2026-11-15-training-cycle-admission.md)、[控制器合同第一／三节及分片表](../plans/2026-11-15-training-cycle-controller-contracts.md)、适用 AGENTS／组件协议和完整差异，再读作者交付叙述。使用 maintainable-project-delivery 的独立审查流程及 ergora-codebase-quality 的模块、测试接缝、风格规则。

**最终本地结论：需求符合性 approve；维护性 approve；开放 finding 0／0，R1／R2 关闭。** 结论限定于固定 r3 产品／测试及 r4 最终状态范围，已独立终核新两安装、54 项回归、六条 CLI 和自身原模板实际复审。普通发布及自己的 CI 尚待，a6 的完整交付门禁未闭合。

## 范围与身份

基线为 `a10e69389e228d311df56bad182b9798f4ca236d`，分支 `refactor/architecture-foundations`。完整 r1／r2／r3／r4 十文件快照、长度／SHA256 和 tracked diff 位于 `.ergora/checks/training-cycle-admission/product-scope-r1/` 至 `product-scope-r4/`；已逐项核对，包括未跟踪的新 fixture、交付记录全文。最终产品／测试身份为 r3，r4 仅追加三个状态文档的实际终态、调整当前检查点顺序，十文件当前 bytes 均与 r4 清单相同。审查覆盖三个产品 owner、既有 submission 测试及其新 fixture，以及本片五份计划／架构／交付状态文档。工作树中旧 c2、Q5 和设计审查的终态记账不算本片产品变更，也未借其结论认证新产品。

|产品／测试文件|最终 r3 身份|
|---|---|
|`src/ergora/training_cycles.py`|32,259B，`3220c6d6d464704d49ab55684f2f5a3a89670cb69b423db464994e1631342d46`|
|`src/ergora/reference_training_budget.py`|32,819B，`19ac550f2d472447e79f1cec38e8d2a089a5d2831df2b0791befd5dd5746b96a`|
|`src/ergora/training_execution_protocol.py`|38,613B，`bf32d9cd5cf7c91b4278a52cf8ea16de3199c37639803c899574a4ab2665f6c5`|
|`tests/test_training_submission.py`|140,199B，`7c03e9c8aae6a882c673bad1d11f07e772a9dab7e4daa2980b414981257fe996`|
|`tests/fixtures/training_cycle_admission.py`|1,513B，`398d8f241f830035b0b20c44700bcf325177fe4e51d32a14f9b74e84d92b7669`|

独立读过 `training.start`／`training_cycles.start`、`prepare_binding`／`BudgetedStart.source`、原 submission 的 prepare／dispatch、budget adapter 最后 create 和原 native context／历史观察调用。未修改源码、测试或其他文档；只写本报告和 ignored 的 `product-audit/` 审计原件。未安装、启动服务、调用网络或提交。

## 需求符合性

- a1：独立 `authorize_controller(..., confirm=True, execute_selected=True)` 复用原 `_authorize`，只有新 ID 出生生成 schema2。完整 canonical SHA 覆盖 actor、稳定 workflow、queue、执行范围、continuation 和布尔确认。读与重试沿原 actor／clock／输入；普通授权仍出生 schema1，跨模式拒绝，没有升级旧 ID 或重开时钟的路径。
- a2：空父锁只在未 ready 的同一出生流程创建，按普通临时文件同步后 link，随后同步锁与目录，再检查原预算。ready reader 只打开既有普通空锁；缺失、非空、FIFO、symlink 等可见拒绝，没有补建。schema1 不增加该锁。
- a3：stop 单独用 `O_EXCL` 建立可见普通目标后再写入、flush、文件／目录同步。部分或坏身份／特殊文件不修复；重复请求观察同一原件。完整身份与持久确认的两处 intent 缺口列为 R1／R2，不能以原件未变或准入已拒绝掩盖错误的成功观察。
- a4：共享与排他 flock 均非阻塞。取得共享许可后重核原授权和任意 stop 路径；排空只取得父锁，不获取 submission／registry／executor 锁。`stop_visible`、`identity_matches`、`stop_durable`、`admission_drained` 分列，`executor_stop_confirmed` 保持 unknown；没有把父排空当作执行子树已停。
- a5：`BudgetedStart.source` 的共同边界拒绝 schema2 走旧三字段 binding；两个真实应用入口都经过该边界。当前没有完整 controller binding、最后 gate／fan-out、总 Workflow、第二执行器或账本，也没有公开同步 live stop。应用记录能力不构成可运行的自动循环。

三个产品文件之外的 649 个产品文件保持基线身份，包含原六阶段、v3 kernel 专家、参考执行算法与资源。原模型／数据／baseline、单 slot、人工 release、283 冻结来源、依赖和 CI 未在本片改变；这些保持结论来自差异和完整包身份，不代表已经验证真实训练质量或收益。

## Findings 与复核

### R1，P2：null stop 未校验后来出现的 intent

原位置：[CycleAdmission._stop_record](../../src/ergora/training_execution_protocol.py#L285)。r1 仅在 `controller_intent_sha256` 非空时读取／绑定 intent。先创建合法 null stop，随后出现完整或损坏的 `intent.json`，`observe(drain=True)` 仍会给出完整身份、持久及排空 true；这是持久记录读边界的错误成功，不是已运行控制器的故障。

独立 r1 探针 `.ergora/checks/training-cycle-admission/product-audit/null-intent-r1.json` 实际复现全部三项 true；作者固定 r1 安装的 `intent-red-r1.xml` 同样实红。最小修正为始终解析现存 intent，与记录的可空 SHA 严格相等；null 只对应缺席。既有 stop 重试先观察原件，避免由后来 intent／新 reason 构造另一份请求。失配保留 stop bytes 和永久否决，撤回身份／持久／排空确认。

r2 源码和独立安装 `-I -S` 小探针均验证原坏 intent 反例转为 `identity_matches=false`、持久／排空 null，重试保留原件，新共享许可拒绝；见 `product-audit/null-intent-r2.json` 与 `null-intent-installed-r2.json`。r3 最终安装包含该回归并通过，此项代码及安装复核关闭；R2 另检验同一约束跨同步窗口是否仍成立。

### R2，P2：同步后未重核 intent，沿用同步前身份

位置：[CycleAdmission.observe](../../src/ergora/training_execution_protocol.py#L323)，原 r2 在文件／目录同步后只重核授权、stop inode 与 raw，未重核与当前 intent 的完整绑定。在持父排他锁的递归观察中，stop 文件 fsync 期间出现完整 intent，null stop 的原 bytes 不变，仍会被返回为完整身份、持久／排空 true；下一次观察才拒绝。长时间存储同步使这个中间身份判断不能代表最终确认。

已独立用 r2 安装在第二次 stop-file fsync 精确引入 valid intent，实际复现三项 true，证据为 `product-audit/late-intent-installed-r2-red.json`；作者 r2 安装精准回归为 1 failed／3.413 秒。最小修正在同 inode／同 raw 重读后、`stop_durable=true` 前重核 `_stop_record`；重核期间不沿用旧 identity=true，失败保留原 stop／否决并撤回持久和排空确认。独立源码及 r3 安装的同一探针均转绿，见 `product-audit/late-intent-source-r3-green.json`、`late-intent-installed-r3-green.json`；最终 54 项中该回归通过，原模板最终复审 approve，此项关闭。

## 维护性与测试价值

没有另一个需要结构修改的 finding。授权模式参数化保留在原 owner，两个显式应用用例共用原发布／恢复算法。`CycleAdmission` 在现有被 pin 的 stdlib owner 内隐藏父记录、文件同步和许可；当前实际生产调用来自 `training_cycles`。未来 worker／native 消费者是合同依赖，未计作已实现复用。这个内聚记录对象及应用 API 是本片明确要求，不需要新模块、抽象工厂或插件总线。

新增私有 canonical SHA 与原格式一致，必要原因是该低层路径不能调用会导入 native 包的旧 `_match`／`publish`。普通文件、安全读取、JSON 解码、目录同步沿已有 `_fd`／`read_raw`／`decode`／`sync_directories`；原 clock、注册、执行器、reaper 不复制。新 guard 均保护外部持久身份、同意版本、普通文件边界或并发／恢复；没有为测试限制有效 budget 范围。

测试放在原 submission 接缝，复用 `cycle_selection`／原 adapter 与服务替身。新 fixture 的必要性是实际独立 Python `-I -S` 进程，保护原生依赖隔离、真实跨进程 flock 和三个实际可见／同步暂停点；不是调度器替身，也未复制整套进程回收矩阵。完整 intent 测试 builder 只构造此刻尚无产品 producer 的外部记录合同。非空原绑定漂移、null 从缺席变出现及同步中变化分别暴露不同状态转换，新增检查有独特风险。没有依据文件长度、默认值或提示全文增加断言／CI job。

## 已核证据与未验范围

- 原 `source-r1` 为私有驱动 resolve 解释器后缺 pytest，产品未收集；`source-r2` 为新目录 `is_link` 的真实 3 failed／8 setup errors；修正后的 `source-r3.xml` 为 11 passed／28.957 秒。失败原件保留，不改写为最终安装通过。
- r1 两非 editable 安装各 652 个 source／wheel／site 逐字；其选择回归 `installed-r1.xml` 为 51 passed／159.182 秒，包含 14 个新检查、21 个原 submission 回归和 16 个架构检查。追加非空 intent 的 1 passed／3.329 秒仍属于 r1 产品。r2 不能继承这些运行的验收。
- r2 的 `installed-r2.xml` 为 53 passed／164.159 秒，仍存在上述同步窗口缺口；不转授 r3。最终 `installed-r3.json/xml/stdout` 为实际 r3 site-packages 执行的 54 passed、0 failed／error／skip，JUnit 166.331 秒，stdout 166.34 秒；其中 17 个新检查、21 个原 submission 回归和 16 个完整架构检查，包含精确末次同步窗口回归。冻结 `installed-tests-final-r3-inputs.json` 的 175 件输入全部逐字核准。
- 已独立逐字核 r2 core／SDK 两安装与 wheel `846a37dcc51402d6e558d963909c82c4914e152570069ccfeb7742a046ce96a5`，均为 652 文件、仅三份产品变化、无增删；283／依赖通过的原件已读。`GATE_SOURCES` key、pyproject／CI 分组和 reference manifest 保持。静态枚举首稿误排除了嵌套参考 AGENTS，修正为仅排除源码根 AGENTS 后完整 652 比较通过；该驱动错误未触及产品。
- 最终 r3 wheel 为 `34381db249f707e766bcd09f4e175c26b6f462194cce00b527b060f2d78f7fa3`；已独立重算所有 source／wheel／core-site／SDK-site 字节和清单 SHA，652 全相等，只有表中三份产品变化，283 冻结参考及两依赖检查通过。SDK 为 Temporal 1.34.0，core 无 SDK；没有用源码测试替代安装运行。
- r1／r2 十文件快照及冻结测试输入身份已核；r2 加入两 intent 检查后，r1 既有测试函数 AST 全部不变。编译检查及 `git diff --check` 通过，仓库没有要求本片使用额外 formatter／type checker 的配置，未套用外部框架规则。
- 独立 stdlib 小探针还核过排他锁立即拒绝共享、共享者仍活时排空 unknown、释放后才排空，以及同步中相同 raw 被不同 inode 替换时不确认持久；`product-audit/probe.json` 保存实际结果。它们只测协议记录边界，不提供 clock／来源或执行授权。
- `cli-journey-r3.json` 及六对原 stdout／stderr 已核：最终 core／SDK 各实际读取 schema2 stopped、schema2 unknown 和 schema1 ready，全部 exit 0、stderr 空；原 actor／授权、cycle bytes 及 SQL dump 保持，没有执行授权、stop 持久或子树停止的扩大主张。CLI 驱动此前准备错误与其不完整旅程保留，未当作产品失败或最终成功。
- 原自身模板 r1 61.776 秒、r2 92.068 秒分别提出上述两个 P2；均为完整 supplied-text 审查，没有认证私有原件／安装／CI。不能把其运行成功等同于需求通过，也不声称后端多样性。
- 最终原 `ergora-structure-review@1.0.0` 为实际 approve／exit 0，57.874 秒；`self-review-r3.json` 与 `self-review-r3-retry-codex/original-result.json`、原文本均已核。原 result SHA256 为 `217bb482cf45ec19c22634a9714df7ce9d2a27670303fa1d0804b1369e87e3b1`。独立比较实际 stdin 与冻结 prompt 完全相等；15 文件 405,026B 和三个祖先资源全文均在真实 stdin 中。该文本审查未认证安装／CI，其输入时的 validation pending 由本报告独立核对随后实际 54 项和六 CLI 终态补齐。r3 首驱动的配置路径错误发生在模型调用前，`self-review-r3-setup-error.json` 原件保留，不计作模型结论或产品失败。

本地需求／维护性门禁通过，普通发布／自己的 CI 仍须各自核精确候选，当前不声称完整交付。未验真实 Temporal 自动循环、完整 controller gate／stop fan-out、独立 worker／queue、公开交互、GPU／业务训练、模型质量、吞吐或性能收益；这些是后继交付责任。

## 普通发布独立复核（2026-11-15）

**固定普通发布结论：需求符合性 approve；维护性 approve；开放 finding 0／0，R1／R2 保持关闭。** 本节补核上述本地终核之后的普通发布，不改写原本地结论；自己的 CI 及 a6 完整交付门禁仍待闭合。

固定发布 commit 为 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`，parent 为 `a10e69389e228d311df56bad182b9798f4ca236d`，tree 为 `c64a28e3b984950d4a4c9e07757a0c682de1ae8a`。独立核过实际 commit 的全部 18 个变化路径，每个 blob OID、长度及 SHA256 均与 `publication-staged-r1.json` 和追加前工作树一致。基线至 commit 的完整 binary diff 与 `staged-r1.diff` 逐字相等：123,298B，SHA256 `d81e054bc07a04fb017bf395cfd7dc89809ab0943592bc052a445df4379ee48f`。独立核证清单为 `.ergora/checks/training-cycle-admission/product-audit/publication-r1.json`。

全部 652 个已提交产品文件与 r3 包清单逐字相等，三份产品源码及两份测试保持上表 r3 身份；`src/ergora/data`、`scripts`、`.github` 和 `pyproject.toml` 均未相对基线改变。相对于已审查范围增加的旧 c2／Q5／设计状态续记和本地批准记录仅为交付记账，没有新产品行为。已发布的原本地审查全文仍为 13,019B、SHA256 `701eb5d483d031af7c9d0fd8775c6b7572b9ffee351571eded6735b26605c8a9`；本节是其后的独立追加。已独立验证固定 commit 内 326 个本地链接目标，目录链接有已跟踪后代，五份变更 Python 文件可解析，完整发布差异的 `git diff --check` 通过。

已读原始 commit／push／完整 Ref 的 stdout、stderr 和退出状态。普通 push 指向 `refs/heads/refactor/architecture-foundations`，保存的完整 Ref 在 `2026-11-15T08:07:24.942254+00:00` 为 `07cbae2227d60c849df6ac96b4f96d3f71d80d43`，与固定候选相同；相关命令均 exit 0，Ref stderr 为空。此证据只确认该观察时点的分支发布，没有合并或 main 发布主张。

原 staging 私有链接检查器把合法的 `scripts/` 目录链接当作 index blob，随后缺失 manifest 使发布驱动在 commit／push 之前退出。已核 `stage-driver-recovery-r1.json`、修正检查器和发布入口的先后顺序；这两次 exit 1 是发布准备驱动失败，没有产生提交或推送。修正后目录检查已跟踪后代、文件检查精确 index blob，最终 manifest／静态检查通过；失败原件保留，不计为产品失败或成功发布证据。

自己的 CI 仍为待核证据。`ci-r1/20261115T080736225629Z-runs-http.json` 记录对完整 head SHA 的官方匿名 REST 请求，于 `2026-11-15T08:07:36.800716+00:00` 返回 HTTP 403、`X-RateLimit-Remaining: 0`；reset 为 `2026-11-15 08:23:00 UTC`。已重核响应原件长度／SHA256，body 只有限流错误，没有 run／job 终态。不能据此判断 CI 成功、失败或当前状态；仍须核同一发布 commit 的终态原件，不能提前宣告 a6 完整交付。后继分片目前仅可做设计准备。

本轮只读本地发布／CI 原件并写本报告及 ignored 的 `product-audit/` 审计记录；没有网络请求、测试重跑、安装、服务启动、提交或推送。

## 自己的 CI 终态与 a6 独立终核（2026-11-15）

**最终交付结论：需求符合性 approve；维护性 approve；开放 finding 0／0，R1／R2 保持关闭；固定 a 片的 a6 完整交付门禁闭合。** 本节补齐前节尚待的自己的 CI 及独立终核，原本地／发布全文 16,240B、SHA256 `c5e736f54455ab05ee6c1fda09aa3df23c974ad8904ad3176670695e94b8dde5` 保持逐字不变。

终态原件位于 `.ergora/checks/training-cycle-admission/ci-r1/`，前缀为 `20261115T083326060046Z-`。已独立重算两份官方 REST 响应 body 的长度／SHA256，并与各自 `-http.json` 的请求 URL、HTTP 200、Content-Length 和观察时点核准：

|原始响应|观察时点 UTC|长度|SHA256|
|---|---|---:|---|
|`runs.json`|08:33:26.989742|11,998B|`09a05ecc05602dfc6e8b32aa706ab0b44ed43a522eb2033965b934f973a4389d`|
|`jobs.json`|08:33:28.287186|21,121B|`c7da38541e2d83b948170bb9f6a7c674efe0fffb2d6e9a45172800f1ad45bc06`|

原 runs 响应完整列出一个 run：`43693023635`，工作流 `Portability`／`.github/workflows/portability.yml`，原 commit `07cbae2227d60c849df6ac96b4f96d3f71d80d43`、分支 `refactor/architecture-foundations`、`event=push`、`run_attempt=1`、`status=completed`、`conclusion=success`，更新时间 `2026-11-15T08:32:13Z`。原 head commit tree 与前节固定 tree 相同。attempt 1 的 jobs 响应完整列出八项，所有 job 的 run／attempt／完整 head SHA／分支均相同，且各为 completed／success；total_count 与实际列表相等，无缺页。

预期矩阵从该固定 commit 的 workflow 和 `scripts/ci/linux-groups.json` 独立推导：`plan`，Ubuntu／Python 3.11 的 group 0–5，以及 Windows／Python 3.12 的 group all，实际名称与八项集合精确相等。必要步骤是 plan 的 `Read explicit test groups`，七个 native job 各自的 `Build and install wheel`、`Packaged reference identity`、`Native application regression`、`Upload regression observations`，以及 Windows 的 `Windows PowerShell 5.1 installer and upgrade`，合计 30 项；每个必要名称在对应 job 恰有一次，全部 completed／success。六个 Ubuntu job 的 Windows-only 步骤为 skipped，符合原条件。已从原 jobs 逐项重建并核准作者 `summary.json` 的身份、job 列表及 30 项结论，未单凭其汇总布尔值批准。

再次重核固定 commit 的 parent／tree、全部 18 个发布 blob 和原审计清单一致；当前 652 个产品文件均与其 blob 逐字相等，源码、测试、CI、scripts、pyproject 没有后续变化。后来的 b 片设计准备文档不改变本次产品身份。此前 HTTP 403、08:23／08:30 的 in_progress 以及 08:26 jobs-progress 原观察全部保留并重核长度／SHA256；它们仍分别代表当时的限流和进行中事实，由本次终态补齐后续结论。独立审计记录为 `.ergora/checks/training-cycle-admission/product-audit/ci-terminal-r1.json`。

结合本报告已核的固定 r3 源码／两非 editable 安装、652／283 身份、54 项原安装回归、六 CLI、自身原模板、原 fresh 产品审查和普通发布，本 a 片 a1–a6 的要求及维护性门禁均已闭合。CI 证据范围为官方 run／job／必要步骤结论；未审查完整日志、Windows 单项测试计数或下载产物内容。完整 controller gate／stop fan-out、独立 worker／queue、总 Workflow、公共交互及真实训练仍属于后继独立交付。

本轮只读保存的官方原件和精确发布身份，只追加本报告及 ignored 审计记录；没有网络请求、测试重跑、安装、服务启动、产品编辑、提交或推送。
