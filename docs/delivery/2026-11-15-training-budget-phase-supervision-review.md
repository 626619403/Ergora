# B3.3a 独立阶段监督：产品独立审查

日期：2026-11-15。评审者为新的 fresh-context Codex 子 Agent `training_phase_supervision_product_audit`。本轮先审固定初轮实现，未继承作者实施对话；先读精选用户原话、固定 r3 设计，再核实际变更及邻接调用者。按根／源码／测试 `AGENTS.md`、[组件协议](../architecture/component-change-protocols.md)、maintainable-project-delivery 的独立评审 brief，以及 ergora-codebase-quality 的 module-design／test-seams／repository-style 检查。

当前需求轴为 request-changes、结构维护 approve，开放 finding 为 1／0：固定发布续核发现测试观察窗口 R4。R1—R3 均已关闭，先前最终本地两轴 approve 的固定范围与原证据仍保留。`5182bfa03f536d4090b91014f97eedda1c5d2d3a` 的发布来源与文件身份已独立核过，其自身 Portability `43670140205`／attempt 1 已全部终态：八 job 为七 success／一 failure，30 必要步骤为 29 success／一 failure，唯一失败为 Linux group 5 的原应用回归；交付门禁未闭合。各轮原失败与发布／CI 续核见下文。

|审查轴|初轮结论|开放 finding|
|---|---|---|
|需求符合性|request-changes；运行验收仍 pending|1：R1，原 phase 的已知 unknown 在收尾聚合时丢失|
|结构维护|approve，仅限固定初轮代码的静态检查|0|

这不是本片最终验收。真实双子树、setsid 后代、大输入慢 reader、回收帧前后异常、旧 helper、完整受影响回归、非 editable 安装、自身原审查模板及真实本地控制流程均待作者固定最终候选和原证据后复核。设计 r3 的 approve 不转授这些运行结论。

## 固定范围与检查边界

实施基线为 `5fa4319c79de7db238cde9d11f5b8acd5b263b91`，parent 为 `75d1ee325288527f67fb1ea814332d1522ff4860`。只读 Git 核对确认两提交的 `src/` 与 `tests/` 无差异；前者只是产品相同的文档 head。分支为 `refactor/architecture-foundations`。

固定输入为 ignored `.ergora/checks/training-budget-phase-supervision/product-scope-r1/{scope.json,author.diff,files/}` 中六文件：两个产品 owner、原 submission 测试、原 budget client fixture、具体计划和交付记录。六份冻结内容的字节和 SHA256 均与 scope 一致；检查时两个工作树产品文件与冻结 r1 逐字一致：

|产品文件|字节|SHA256|
|---|---:|---|
|`src/ergora/reference_training_budget.py`|28204|`7940d9954c25c02bc55a25190ee9b3d44bd2b1268b53ef802f897bc8ead79d9d`|
|`src/ergora/reference_training_worker.py`|6995|`4e05c0a250e3e1f0f98a081acf097ea6e75aa99dfcdd7fc52a5ae32389fe27ae`|

技术合同以 `design-scope-r3/` 中固定三文档为准；用户原话在同目录的 `raw-requirements.md`，其本身没有逐字定义 phase 协议。当前具体计划的变化只是实施状态同步。另读原 submission／context、clock、strict JSON reader、共享 processes、取消 helper、相邻架构协议及实际 fixture 调用路径。`src/ergora/data/reference` 相对基线无 tracked diff；本轮没有修改共享 processes 或 283 冻结资源。

已提供的 `source-start-r1` 原命令／XML 为源码单场景 `test_cycle_start_returns_before_automatic_fence_blocks_a_late_native_create`：1 passed，pytest 21.874 秒，外层 22.9448 秒。该场景保留真实 detached owner、SDK 服务替身及原 native adapter；它只证明 accepted 返回后的自动 fence 路径，不证明新监督协议的全部故障分支。本评审读取了原件，没有重跑或扩大其适用范围。

## R1：中，后续 fence 覆盖了已经确认存在的 phase unknown

位置：[reference_training_budget.py](../../src/ergora/reference_training_budget.py:171)、[own 聚合](../../src/ergora/reference_training_budget.py:409)。固定 r1 中，`_BudgetPhase.run()` 成功时只返回第二帧的 helper 业务结果，失败时返回含 `phase_id`／`supervisor_returncode` 的 unknown；`own()` 随后在 monitor 非 completed 时运行 fence，并用 fence 结果替换 `observed`。最终只保存 `outcome` 和控制面结果，没有保留原 monitor 的失联／回收未确认观察。

可达场景是 monitor supervisor 在匹配 stopped 帧之前被 SIGKILL 或异常退出，而预算仍余足够 cleanup。`run()` 正确返回 unknown，随后独立 fence supervisor 成功，最终 `final.status` 为 fenced，已知 monitor unknown 的 phase ID、返回码及原因全部消失。此时旧 monitor helper／后代是否回收仍未确认；fence 只阻断后续 native create，不能补回已丢失的回收观察。现有 `executor_stop_confirmed=null` 避免了直接冒称 executor 已停止，但它没有表达这次实际发生过的监督故障，也无法区分正常 fence 和丢过 supervisor 的 fence。

固定 r3 要求 supervisor 异常／缺完整返回为 unknown，并把 supervisor 返回码、helper 业务结果、回收观察分列。临时两帧不是新恢复授权；这也不要求建立新的持久协议文件。当前仅在局部返回值中短暂保留 unknown，随后完全丢弃，未满足这个观察合同。

本评审用现有 `own()` 的最小本地聚合接缝核过：只替换 preflight／phase 返回，不启动模型、服务或业务子进程，monitor 返回 `supervisor_returncode=-9` 的 unknown，fence／cleanup／publish 分别返回成功；实际 `own()` 结果为 fenced，原 unknown 未保留。原结果在 ignored `reviewer/initial-static-audit.json`。它证明当前聚合行为，不冒称已经复现实际 SIGKILL／后代存活；该真实场景仍待本片原进程证据。

最小修正是在原预算 owner 的返回／既有 final 中保留简短逐 phase 摘要，例如 phase ID、mode、supervisor 返回码、是否收到匹配 stopped、helper 状态及 unknown 原因；业务 fence／native completion 事实继续单列，不把任何 phase unknown 变成成功回收。无需复制完整 helper 结果、增加另一账本或改变 start slot。修后应从真实原 owner 故障接缝核：帧前失联仍能建立原 fence，但 final 保留该 phase unknown；帧后后处理故障可确认该树已回收，业务结果仍 unknown。

### R1 真实原场景实红，尚未关闭

同片随后收到固定 `source-scope-r2/` 与 `source-scope-r2.json`：两个产品 SHA 与 r1 相同，新增原 suite／fixture 故障接缝。本评审直接检查 fixture：monitor helper 捕获本次 supervisor／helper 的完整进程身份后，真实向其 supervisor 发 SIGKILL；没有 mock `_BudgetPhase.run` 或 `own` 返回。故障 marker、原 final、stdout 和 XML 一并核过。

`source-supervisor-loss-red-r2` 的精确命令选择 `phase_interruption and phase-supervisor-killed`，为 1 failed／28.17 秒，外层 29.1516 秒。此前进程已停止、原 fence／resume／原文件 bytes 保持和 `executor_stop_confirmed=null` 断言均通过，最后读取 `final.phases` 因字段缺失触发 KeyError。原 final 确为 fenced，尚余 cleanup 7.33805 秒，完全没有原 monitor 的 unknown 观察。这与静态 R1 一致；实红原件保持，不改记为成功。作者接受 R1，修正候选与原场景重跑仍待固定复核。

## 结构、必要控制流与测试价值

固定 r1 没有发现额外结构阻断：

- 四个原 phase 都从 `BudgetedStart.own → supervise → _BudgetPhase.run` 启动专用 supervisor；worker 的明确 `phase-supervisor` 入口在该专用子进程内复用原 `processes.run(supervised=True)`。父 owner 自身不调用 `_adopt_children`／监督 run。共享原回收算法和 native executor 没有复制。
- `_BudgetPhase` 是原 owner 内的私有、有状态生命周期算法。它隐藏 payload、单一发送偏移、PIPE 读写、身份／顺序解析、停止及收集这一组真实义务，删除后这些义务会回到原 owner；它不依赖虚构的复用调用者。`BudgetedStart.supervise_phase` 的另一个生产调用者是 worker 的进程入口，属于实际框架接线。没有必要新增跨领域类族或插件注册表。
- 非阻塞短写按实际 `os.write` 返回值推进，写完才关闭 stdin；stdout 按字节累计完整 UTF-8 JSON 行，使用既有 finite／duplicate-key parser。完整帧在 EOF 前就能进入状态；帧数、次序、完整身份和独立容量界均有实际外部协议失败路径。stderr 直接写原观察文件，没有给父 owner 新增同步完整日志读取。
- 计算／总期限继续读取原缓存 clock；predicate 只核原期限、取消标志和捕获 owner 的 PID／start ticks／boot 身份。帧前只请求 TERM，等待原 reap；仅完整匹配 stopped 后才允许总截止 kill 该已无业务树的 supervisor。这里的安全性仍依赖实际 flush／进程证据，不能由静态条件直接认证。
- 四个旧直接 helper mode 仍走原普通 JSON 分支；publish helper 仍拥有 final 的 fsync。cleanup 继续沿原取消 owner，不增加 executor、执行授权、queue、ledger 或恢复重发。Kernel 专家和模板路径未变化。后继原 native executor 的锁内准入缺口已另列执行设计，不作为本片新 finding。

reviewer 另做了约 0.4 秒的本地 parser 接缝探针：分片完整帧可接受，错 mode、错序、第三帧、duplicate key、NaN、缺末尾换行和超界 stopped 都不能形成完整成功响应。原结果在 ignored `reviewer/protocol-decoder-probe.json`；这只是 parser 检查，没有运行 supervisor、证明真实回收或代替慢 reader 测试。

原测试 fixture 实际替换 SDK 服务调用和 budget 进程入口，保留真实 detached owner／supervisor／原 processes.run；这比只 mock `run` 返回更能覆盖进程归属。初轮测试本身尚无本片新增回归，故不能据原 accepted 一项宣布隔离／IPC 故障已覆盖。后续应复用此入口覆盖新风险，避免为四个 mode 复制相同矩阵。`pyproject.toml` 未配置其它项目的 formatter／linter，本轮未套用外部代码风格；两源文件 `git diff --check` 通过。

## 下一次同片复核

等待固定最终源码／测试完整 scope，以及实际命令、原 stdout／XML、安装身份与未验范围后续核 R1 和两轴终态。在此之前维持需求 request-changes、结构静态 approve、运行验收 pending。此次只写本报告及授权 ignored `reviewer/`，没有安装、提交、推送、启动模型／训练／Temporal／MLflow或运行昂贵 suite。

## r3 同片续核：R1 关闭，新增缺损 process 帧 R2

日期：2026-11-15，同一独立评审者只续核 R1 修正、其相关协议摘要边界和五项真实源码证据。上文初轮结论、原实红及固定 r1／r2 原件保持。本次没有重新运行产品或昂贵测试。

|审查轴|r3 续核结论|开放 finding|
|---|---|---|
|需求符合性|request-changes；R1 已关闭，最终运行验收 pending|1：R2，缺损 process 帧在新摘要处触发异常|
|结构维护|approve，限本次固定修正|0|

输入为 ignored `source-scope-r3/` 与 `source-scope-r3.json` 中四文件。四份冻结 SHA 均匹配；检查时两个工作树产品文件仍与该候选一致。预算 owner 为 28918B／SHA256 `6048c761cf7c9157d94ce6c7d83bd384e7fdd6874ef453591c362eaab487fb80`；worker 保持 6995B／`4e05c0a250e3e1f0f98a081acf097ea6e75aa99dfcdd7fc52a5ae32389fe27ae`。原 suite／fixture 分别为 85756B／`200e94fef6fcfa7a26b9ca5dedaee6391c360aa2d4c084366b81763af3ce9635` 和 7730B／`ebf77ca0ff152b27399f62e62e45c22c148c8af6b1623945e8d1ee157af77119`。

### R1 修正及实际证据

`BudgetedStart.supervise` 现在保存 phase ID、mode、supervisor 返回码、是否收到匹配 stopped、原 helper process 的状态／返回码、业务状态及原因；`own` 把已有工作 phase 的短摘要复制到原 final。摘要不包含大 helper 输出，没有新的账本或恢复权限。publish 自身发生在 final 构造之后，其业务结果仍由原返回的 `publication` 单列，不循环重写 final。这是原 owner 内的必要观察聚合，未增加额外模块或虚构复用接口。

`source-phases-r3.{json,xml,stdout,stderr}` 逐份核对：命令只选择原 suite 的 `budget_phase_`，exit 0，5 passed／144.678 秒，外层 145.6059 秒，stderr 为空。直接检查了相应 marker 及原 final：真实 SIGKILL 场景的 monitor 条目为 `status=unknown`、`stopped=false`、`supervisor_returncode=-9`、`helper_process=null`，后续 fence 与 cleanup 分列，`executor_stop_confirmed` 仍为 null。原 fence／resume 与原 bytes 保持断言也实际通过。R1 据此关闭；原 1 failed 运行保持失败身份。

其余四项实际通过范围为：父 owner 的 subreaper 值为 0、一个 supervisor 结束后另一个 peer 仍存活、真实 setsid 后代最终停止；786432B UTF-8 探针经慢 reader 后字节数／SHA 完整；held reader 不挡住原期限后的 fence；stopped 已发出后结果文件 reader 阻塞，业务结果不被合成成功。它们保留真实 owner／supervisor／原 processes.run，SDK 服务仍是替身。相应固定文件、XML case、marker 和 final 摘要检查记录在 ignored `reviewer/r3-followup-audit.json`。这些源码证据没有覆盖下一段尚待的完整验收。

### R2：中，缺损 stopped.process 被接受后使 owner 直接异常退出

位置：[接收协议](../../src/ergora/reference_training_budget.py:100)、[新 phase 摘要](../../src/ergora/reference_training_budget.py:387)。`receive` 只要求 stopped 的 `process` 为 dict，允许同一完整身份、顺序正确但 `process={}` 或缺少 `returncode` 的帧进入 `self.frames`；新摘要随后直接读取 `helper['status']`／`helper['returncode']`。此时会抛 KeyError，中断原 owner，未能返回该 phase 的 unknown 并继续原 fence／cleanup。

可达条件是专用子进程给出缺损 process 内容，属于本片明确要保守处理的协议输入；不需要假设用户输入或 native 业务结果改变。固定 r3 的最小本地接缝探针使用实际 `receive` 接收 `{}` process 的 stopped 及正常 result 两个完整同身份帧，结果为两帧接受、`problem=null`，随后实际 `BudgetedStart.supervise` 的摘要构造抛 `KeyError: status`。原结果在 ignored `reviewer/r3-malformed-process-probe.json`；该探针替换了 phase 的进程运行，不冒称真实子进程故障复现。

最小修正在 `receive` 这个唯一协议边界验证 stopped 中原 `processes.run` 返回结构及必要类型，缺失／冲突置为 problem、保持 unknown，摘要只消费已核 process 内容。无需在摘要和各 mode 重复 guard。回归用现有协议接缝验证缺少字段的完整帧不能获得 stopped 确认，owner 不因摘要 KeyError 提前退出；正常原进程返回仍保持当前证据。

作者接受 R2，计划先保存真实 supervisor 在原 reap 完成后发送缺字段 stopped 的原失败，再修唯一协议边界并固定候选；当前尚无该修正或运行结论。

最终仍待：回收已经开始后跨总截止且收到 TERM 不被父 owner 打断、接近原 1MiB helper 容量的完整 UTF-8 封套、旧四 mode 兼容、受影响原矩阵、最终两套非 editable 安装、真实 Temporal 本地控制流程、自身原模板及固定最终候选的独立复核。此轮不把 R1 的关闭写为 B3.3a 完整验收。

## r7 同片续核：R2 关闭，完整验收继续 pending

日期：2026-11-15。同一评审者续核固定 `source-scope-r5/`、`source-scope-r6/`、`source-scope-r7/` 及各自 JSON 清单、R2 真实实红／修后运行、回收边界及新两安装的文件身份。本轮各 scope 字节／SHA 均独立匹配；r6 与 r7 两产品逐字相同。r7 预算模块 29480B／`7bc7c8a380c2ff1ce184cbb2f2f3a02b603aa0129707a3dbb3122168c445c799`，worker 仍为 `4e05c0a250e3e1f0f98a081acf097ea6e75aa99dfcdd7fc52a5ae32389fe27ae`；r7 原 suite 为 88280B／`b78b12bd7b1cf91b7443eaf6e6cdea0d91e209bc4ee830d568cf0dac266fdb2d`，fixture 为 8886B／`4fd8da56e42ff88a3f3e52220f690753cf4b30b01b2b27ad72f02a6f3a5a5a00`。

|审查轴|本轮固定修正结论|开放 finding|
|---|---|---|
|需求符合性|R1／R2 均关闭；本轮修正 approve，完整验收 pending|0|
|结构维护|approve，限本轮固定代码|0|

`receive` 现在要求 stopped.process 恰有原 `status`／`returncode`／`output` 三字段、原状态集合、integer 或 null 的返回码，并匹配本 phase 的原 helper 输出位置；缺损帧不会进入已确认 stopped 集合。摘要只消费通过该边界的内容，没有在各 mode 或摘要层再加兜底。这直接修复 R2，新增判断都对应外部协议的可达缺损，不是重复参数验证。本地七个 parser 接缝用例核过正常结构、缺字段、错输出位置、bool 返回码、未知状态和多余字段，结果符合预期；原件在 ignored `reviewer/r7-process-frame-probe.json`，不当真实 supervisor 运行。

真实 `phase-stopped-incomplete` fixture 调用原 processes.run 并完成实际 reap 后，才让专用 S 返回 `{}` 并发送缺损 stopped。`source-incomplete-red-r5` 1 failed／23.54 秒，外层 24.4956 秒；直接核原 owner stderr，确实在摘要读取 `helper['status']` 抛 KeyError，未建立 fence。r6 修正后 `source-corrections-r6` 为 1 passed／1 failed、61.257 秒，外层 62.1917 秒：reap 边界通过；缺损帧的公开 fence／resume／原 bytes 保持均通过，剩余失败是测试错误要求耗尽 cleanup 后必有持久 final。r7 只修该测试的观察位置，没有再改产品或预算；`source-incomplete-r7` 精准 1 passed／32.749 秒，外层 33.9497 秒，stderr 为空。本评审直接核原 owner 诊断 stdout：monitor 为 unknown／stopped=false，原因是缺完整 process 观察，随后 fence／cleanup 分列；当次确无持久 final，publish 为 unknown。诊断不是持久回执，公开同 fence 恢复也没有重启或补发。R2 据此关闭，r5／r6 原失败保持。

回收边界另有真实证据：原 r4 首次失败只因测试把已匹配 stopped 后的 S 返回码错误锁为 0；实际 reap 已完成，允许的后处理 SIGKILL 为 -9。修正预期后的 r6 场景在 reap-started 后向原 owner 发 TERM，延迟进入原 reap 并跨总截止；reap-finished 的原剩余值为 -0.528876 秒，诊断 actual overrun 为 0.737266 秒，monitor stopped=true，原 setsid 后代及 S 已停，观察目录只有 monitor，未在总截止后启动新的 fence/helper/publish，也没有 final 或 fence。它证明受控延迟回收不被父 owner 提前打断，不是任意 OS I/O 的硬实时保证。r4 中接近原 1MiB 界的 UTF-8 gate 摘要场景也确有 1 passed，属于其原产品身份；最终安装矩阵仍须覆盖固定最终产品。

新 wheel `c050c204ada81cfce0e335c210f9f457900704390c882ebeec3c96e8235a4178` 已独立重算 SHA。本评审逐文件重读本次 source、wheel ZIP 和 core／SDK 的实际 site-packages：两套各 648 文件全部字节／SHA 一致，变化仍只有原两个产品 owner，无新增／删除产品文件。两套 reference 原结果为 283／PASS；core 没有 Temporal SDK，SDK 为 1.34.0。两份原 `uv pip check` 均 exit 0，stderr 明确全部依赖兼容。这是包身份／依赖证据，不能替代正在运行的完整安装回归。完整核对摘要在 ignored `reviewer/r7-followup-audit.json`。

最终封闭 scope、受影响安装完整矩阵、旧 helper 的完整兼容证据、真实 Temporal 控制流程及自身原模板仍待后续同片终核。本轮没有安装、启动服务或重跑昂贵测试，也未给本片完整产品 approve。

## R3：中，新增 phase 元数据挤占原 final 的有效容量

同片随后收到原 `ergora-structure-review@1.0.0` 自身模板结果：`self-review-r1-codex.json` 记录 18 份全文／260487B 加 3 资源，90.8089 秒，需求 request-changes／结构 approve。本评审直接读取原 review／result，并独立核过相应源码与后续公开读取链；该结果本身是源码文本审查，不认证私有原运行或安装。

位置：[final 构造](../../src/ergora/reference_training_budget.py:437)、[publish](../../src/ergora/reference_training_budget.py:484)、[原 bounded writer](../../src/ergora/training_cycles.py:288) 和 [reader](../../src/ergora/training_cycles.py:195)。同意 R3：原本序列化后刚好不超过 1MiB 的 completed final，加入 phase 摘要和 overrun 字段后可越界；helper 普通结果仍在其原 1MiB 内，也能完整通过独立 2MiB 协议封套，但最终发布仍被 `_record` 的 1MiB 界拒绝。原完成事实随后只能读成无 final 的 owner unknown，属于新增元数据缩窄原有效范围。此前容量测试留 8192B 余量，没有保护这条边界。R1／R2 保持关闭，R3 开放；整体需求仍为 request-changes，结构维护未新增 finding。

作者提出的修正边界合理且可在本片完成：`training_cycles._record` 已复用带 limit 的 `_record_bytes`，`_document` 已复用 `_read_bytes`；给两个现成入口增加 keyword-only `limit=MAX_RECORD_BYTES`，只让 budget final 的 publish 写入与 observe 读取显式使用独立 2MiB 容量，可以继续复用原 no-follow／strict／finite reader 和 durable writer。helper stdout、owner、authorization、ready 等原调用仍用完全相同的 1MiB 默认，不扩大全局 `MAX_RECORD_BYTES`，不复制算法或新增账本。这个可选参数服务实际存在的两类字节合同，不是泛化插件接口。

已追过公开 submission／status → `reference._training_process`：其 stdout JSON 收集没有另一个 1MiB 截断界，因此 final 两个持久读写点同时调整后，当前调用链没有发现第三个需要放宽的 final reader。旧 final 仍能读取，原 final 写入继续位于受监督 publish helper 内。最终固定 scope 需包含新增触及的 `training_cycles.py`，不能继续沿旧两产品清单验身份。

运行结论尚未取得。精准回归应核原 completed 场景的旧 final 序列化大小不超过 1MiB、新 final 因本片元数据超过 1MiB 而不超过独立封套、helper 原输出仍不超过 1MiB，并从公开 submission 读回完整 gate 与 phase 摘要。保留 r1 新安装的原实红后，再核修正候选、默认 reader／writer 的既有检查与新的两安装／受影响运行；本轮只认可修正方向，不关闭 R3 或宣布未知测试通过。

## 同片最终本地审查：R3 关闭，双轴 approve

日期：2026-11-15。同一独立评审者续核最终固定作者候选、R3 实红与修后完整安装回归、两套安装身份、原自身审查模板及真实本地控制流程。此次只更新本报告与授权 ignored `reviewer/`，未改产品、测试或计划，未安装、运行昂贵测试、启动服务、提交或推送。

|审查轴|最终本地结论|开放 finding|
|---|---|---|
|需求符合性|approve；R1、R2、R3 均关闭|0|
|结构维护|approve|0|

### 最终固定范围

基线仍为 `5fa4319c79de7db238cde9d11f5b8acd5b263b91`。最终作者清单为 ignored `product-scope-r3/{scope.json,author.diff,files/}`，`scope.json` SHA256 为 `745183d91508ad0c0ec83739fbb7119a8539de0c01143330866ee3c79ee229c2`。逐份重读的 11 文件字节／SHA 与清单及工作树一致，冻结 `author.diff` 与实际基线 diff 完全一致；本评审报告单列，不递归评审自身。

范围为下列三个产品文件、`tests/test_training_submission.py`、`tests/fixtures/training_budget_client.py`，以及六份文档：`docs/PLAN.md`、`docs/TRAINING.md`、`docs/architecture/current.md`、本片计划、本片交付记录和上一片 submission 独立审查的 CI 收尾记录。最终产品身份如下：

|产品文件|字节|SHA256|
|---|---:|---|
|`src/ergora/reference_training_budget.py`|29572|`04fd727381203bf78c4ec6c63d3170cf808151d3db160c8785db410b58cd9529`|
|`src/ergora/reference_training_worker.py`|6995|`4e05c0a250e3e1f0f98a081acf097ea6e75aa99dfcdd7fc52a5ae32389fe27ae`|
|`src/ergora/training_cycles.py`|27738|`1037d57df2fb2d88beda31a820d989eb580b130c362f7efc47de39abe67e0b53`|

五份 Python 文件均通过 AST 解析。最终 suite SHA256 为 `6b717817aa4ca5df70ea159478c3509e217fb437ff406e691a0b7524454a6865`，fixture 为 `4fd8da56e42ff88a3f3e52220f690753cf4b30b01b2b27ad72f02a6f3a5a5a00`。另独立核对安装回归的 173 份冻结 test／example 文件字节、SHA 与工作树身份。

### R3 的原实红与关闭依据

`installed-capacity-red-r1.{json,xml,stdout,stderr}` 保持原 1 failed／20.519 秒，外层 21.4434 秒。直接读取 helper、旧 final 投影和新增元数据后的 final，容量关系及修后结果为：

|观察|原 r1 实红|最终 r2 安装|
|---|---:|---:|
|helper 普通结果|1047967B，未超过原 1048576B|1047967B|
|加入本片元数据前的 final 投影|1048463B，原界内|1048463B|
|完整新 final|1048794B，原界外|1048794B，独立 2097152B 界内|
|持久 final|不存在|存在，公开读取完整|

原 publish stderr 确为 `ValueError: Complete training cycle record exceeds 1048576 bytes; nothing was truncated`。修后原 completed 场景已在最终完整 24 项安装回归中通过；重新读取实际持久 final，SHA256 为 `eaed2f2d48b97dd73fe05846be76be54fb39470b66486a84fe03dbc2084a3897`，其中 UTF-8 gate summary 为 1046961B。测试同时核过公开 submission 的完整 final、phase 摘要、原 native／gate／request 字节不变及无 fence／cancel，覆盖了新增元数据挤占原有效容量的实际边界。R3 据此关闭。

产品修正只为既有 `training_cycles._document`／`_record` 增加 keyword-only `limit=MAX_RECORD_BYTES`；原 strict／finite／no-follow 读取与 durable 写入算法不变。budget 本地 `_FINAL_LIMIT=2*MAX_RECORD_BYTES` 仅用于 final publish 与 observe。helper、owner、authorization、ready 和其它默认调用仍保持原 1MiB 界。公开 `_training_process` 没有另一个 1MiB 读取界。这个改动服务现有两种容量合同，没有复制算法、另设账本或扩大默认输入容量，结构维护没有新增 finding。

### 最终原验证证据

- **安装回归与故障接缝：**`installed-regression-r2.{json,xml,stdout,stderr}` exit 0，24 passed，0 failed／error／skip，pytest 497.215 秒，外层 498.2776028555818 秒。覆盖原 accepted／held、managed create／owner loss、completed 容量、lost ack、registry／fence／final fsync 恢复、独立 peer／setsid 后代、大输入慢／held reader、跨总截止 reap 与 TERM、帧前／帧后故障、原 source／strict／durable-ready 默认记录、worker bootstrap 和服务幂等。`installed-boundaries-r2` 为 16 passed／0.436 秒，外层 1.1174 秒。直接核过 final-file-blocked 和 final-directory-blocked 实际 marker；前者无 final，后者可见原 final 并沿原恢复路径读取。
- **原失败保持：**最终 r2 之前的完整 r1 回归仍为 18 passed／3 failed、471.681 秒，外层 472.748 秒。两项失败是原 8 秒 cleanup 在新增 S 启动开销下尚未到达 final fsync marker；r2 保持同一 10 秒 compute 窗口，测试显式给 wall 24／cleanup 14 秒以达到该注入点。另一项失败是 forced TERM 后测试错误强求持久 final，r2 改核实际 stopped。产品预算默认没有因此改变。上文 R1、R2 和 reap 预期的各次实红均保留原身份，没有用修后结果覆盖。
- **非 editable 包：**`dist-r2/ergora-0.2.0-py3-none-any.whl` 重算 SHA256 为 `56e24e967729304b9abcf2c5cdeb82be5b6619a7b55d9bdefbe5c27407bb03a5`。逐文件读取 source、wheel ZIP、core 与 SDK 实际 site-packages，两套各 648 文件字节／SHA 全等，仅上述三个产品模块变化，没有新增／删除产品文件。两套冻结 reference 均为 283／PASS，source reference 的 tracked diff 为空；core 无 Temporal SDK，SDK 为 1.34.0，两份 `uv pip check` 均 exit 0、依赖兼容。
- **真实本地控制流程：**`native-journey-r2.json` exit 0，54.133257993 秒；原目录由 `native-location-r2.json` 固定为本片独立持久目录（实际位置只保留在该私有原件中）。独立核对 `native-originals-r2.json` 的 394 原文件及九条实际 CLI 的 argv／返回码／stdout／stderr SHA。首条 core 无 SDK 启动按预期 exit 2，其余 exit 0；实际 Temporal 与 worker 沿原 queue／精确 run 建立 queued native request、自动 fence、原取消及 resume，authorization／slot／request 字节保持，candidate-b 无 request、无 `started.json` 或 executor。捕获的九个 owner／S／helper 原进程身份均已不存活，supervisor socket 已消失，原端口清理 bind 成功；本评审再次连接 7233／8233 均拒绝连接。
- **原自身审查模板：**`self-review-r2-codex.json` 使用原 `ergora-structure-review@1.0.0` 和已授权的 Codex fallback，75.141044 秒，源码需求／结构两轴 approve。独立核过 18 份全文共 265810B 加三份继承资源确实完整出现在实际 stdin，prompt 与 stdin 一致；prompt 为 329182B，原 result 与运行结果及 SHA256 `47e79c702859a51dc72d14503f26515595cce7fdc6bd85456e85a686f102b3d2` 一致。该模板结论限源码文本；私有原件、包身份和运行证据由本独立评审另核。

最终代码仍将 `_BudgetPhase` 留在既有预算生命周期 owner；父 owner 不成为 subreaper，每个专用 S 各自复用未改的 `processes.run(supervised=True)`。单一 stdin 偏移、非阻塞 transport、完整严格帧、唯一 process 验证边界和 stopped 前后不同的停止权限都有实际控制流与相应原场景支撑。原 clock、start slot、queue／owner 身份、fence／cancel／恢复及旧四个直接 helper mode 保持各自原 owner。最终 TRAINING 与当前架构文档明确区分 helper stopped 和 executor stopped，说明容量、S 启动开销及 overrun 快照边界。没有新增产品或结构 finding；另列的 native executor 锁内准入缺口仍属于后继执行设计。

### 证据身份与剩余发布边界

ignored `reviewer/final-candidate-audit.json` 保存包／模板实际 stdin／真实本地流程核对；其生成时完整 r2 回归尚在运行，`installed_regression_r2_complete=false` 保留该时点事实。后续 `reviewer/final-validation-audit.json` 已核最终 11 文件、173 份回归输入、完整 24＋16 结果、容量原件、fsync marker 及证据清单。`evidence-index-r1.json` 的 178 项字节长度／SHA 均已独立匹配，清单 SHA256 为 `2b1d311f24ed4198470013255082c5c3e0223e2e82a66ea775761ed53c47c77c`；真实本地流程另有前述 394 原件清单。

作者本地 `static-r1.json` 对当时 12 文件候选树 `3b4a2b0620ca1a96fa8baabd26feb343f72b7a3f` 记录 diff-check 通过、五份 AST、283 原资源无 tracked diff、241 处链接零缺失；本评审另在该 Git tree 逐一核过 241 个目标。此次追加本报告会改变候选树，旧树不能冒称最终发布身份。普通提交／推送后的固定 SHA、最终文档静态收尾和该提交自身 CI 仍待作者提供后续核；本地 approve 不代表已经完成这些发布步骤。

真实本地流程只认证合成 CPU 控制合同和实际 Temporal／worker 路径，没有启动 executor、模型或 GPU，不认证训练、质量、性能或自动 cycle。R1—R3 的关闭和上述双轴 approve 均以本节固定候选与已核证据为界。

## 固定发布与自身 CI：来源及终态已核，原失败保持

同一独立评审者继续核普通发布提交 `5182bfa03f536d4090b91014f97eedda1c5d2d3a`，parent 为 `5fa4319c79de7db238cde9d11f5b8acd5b263b91`，tree 为 `b8696bb8b0a293fdd45bfb3a77b2088a58b2efb4`，共 12 个变更文件。直接读取 Git 对象与 `publication-staged-r1.json`，逐份匹配 12 个 blob OID／字节长度／SHA256，完整基线 diff-check 通过，五份 Python AST 通过；清单中的 242 个链接目标逐一在该固定 Git tree 存在。实际 commit／push／ref 的 stdout／stderr 均已读取：普通 push exit 0／5.8285870011895895 秒，完整 SSH Ref 当时为同一 SHA，提交后工作树干净。独立核对记录在 ignored `reviewer/ci-publication-r1/fixed-publication-audit.json`。

相对已通过的 `product-scope-r3/`，三产品和两测试完全逐字相同；只有 PLAN／具体 plan／delivery 同步本地终审与发布待办。公开评审报告只把一处机器绝对目录换成私有 `native-location-r2.json` 指针；逆向还原该一处后，整份报告 SHA256 精确匹配本评审原 `d0620d1eaa3d920d80a89ff7145ddf14be2bb160699955b1c5bfb13436c4719a`。这些状态／位置文字没有改变产品、已核结论或未验边界。本次续记报告本身位于被测提交之后，不冒称它属于该固定 tree。

匿名 REST 的 commit／ref／runs 及该 run／jobs 五个请求均因限流返回 403，原响应体、header、URL、时点和 SHA 已保留，没有改记为成功。改核官方 [commit 页面](https://github.com/626619403/Ergora/commit/5182bfa03f536d4090b91014f97eedda1c5d2d3a) 的完整 OID／parent、当时 branch 页的 `currentOid` 以及固定 SHA 的十二份官方 raw 文件；十二份返回 200，字节／SHA 与本地发布清单全等。实际官方来源和摘要保存在本片独立 `reviewer/ci-publication-r1/`，`official-remote-identity-audit.json` 记录来源身份，没有借用上一片的远端或 CI 结论。

官方 Actions 列表把完整 `5182bfa` 绑定到本片 [Portability #229／43670140205](https://github.com/626619403/Ergora/actions/runs/43670140205)。固定 workflow 与 `linux-groups.json` 对应 plan、Linux 0—5、Windows all 共八个 job，必要业务步骤共 30 个：plan 的分组读取、七个 native job 的构建安装／包 reference 身份／原应用回归／上传观察，再加 Windows PowerShell 5.1 安装与升级。完整官方 navigation 为 `totalCount=8`／`hasMore=false`；八个实际 job 页面均已读取，其步骤日志链接均钉到完整本片 SHA 与各自 job ID。它们只作为页面 step 结论来源，不表示本评审取得了完整日志或可下载 artifact。

2026-11-15 11:00:47 +08 初始快照：plan success、七个 native in progress，必要步骤 15 success／15 尚未终态，run 显示 In progress。原快照在 `20261115T030047542603Z-pending-summary-r1.json`；本片自身 CI 尚不能记通过。继续跟踪同一 run／attempt 1 的完整 job 和必要 step 终态，后继纯 docs 提交不转授、替代或取消对这个固定产品提交的核对。

### R4：中，测试只等 20 秒，却给原 owner 24 秒合法总预算

11:11:12 +08 起的完整官方 navigation 显示 Linux group 5 job `132678181529` 为 completed／failure；其余已完成六个 job success，Windows all 仍在运行。直接读取该 job 的终态 HTML，header 为 failed／13m16s：Build and install wheel、Packaged reference identity、Upload regression observations 均 success，Native application regression 为 failure。该页官方 annotation 明确记录 `2 failed, 468 passed, 13 skipped, 1599 deselected in 776.01s`，失败均在原 final fsync 故障测试：

- `test_cycle_final_publication_is_bounded_and_dead_owner_recovers_only_the_same_fence[final-file-blocked]`
- `test_cycle_final_publication_is_bounded_and_dead_owner_recovers_only_the_same_fence[final-directory-blocked]`

两项都报 `AssertionError: Original budget owner did not finish its bounded supervision`。原 job 页面为 `20261115T031231327842Z-job-132678181529-html.html`，174294B／SHA256 `8823052e5d4daf01df3f3154a530fd7b653a656ac6575b3f61c48544fab51ef3`。页面注释是这组具体失败和计数的实际来源，没有把 duration 列表中的其它测试误记为失败。

只读重核固定提交的 [该测试](../../tests/test_training_submission.py:527) 与 [等待 helper](../../tests/test_training_submission.py:480)：测试把合法 wall 扩为 24 秒、cleanup 为 14 秒，但随后仍调用 `wait_budget_stopped(runtime, seconds=20)`。helper 从调用时新计 20 秒，超时就对捕获的原 owner 发 SIGKILL 并抛出上面的同一断言。若 submitted 返回时原连续总预算尚余超过 20 秒，测试就会在合法总期限前杀死 owner；慢启动可能消耗这段差额，因此本地安装通过不能排除该可达路径。这个静态窗口矛盾与两项实际 CI 失败一致；没有原 CI 时钟／完整日志，不能冒称已认证当次精确剩余秒数。

最小修正应只让这两个故障场景的外部观察等待覆盖其实际 24 秒预算和回收余量，保留原 compute 窗口、产品预算默认、真实 fsync marker、进程 stopped 和公开同 fence 恢复／bytes 不变断言；不能靠提前强杀原 owner 来满足停止观察。R4 开放，需求轴 request-changes；没有新增产品或结构 finding。原 R1—R3 与本地 24＋16 的已核通过仍保留，不能把它们转授这次失败的 CI 门禁。

当前机器无 `gh`；直接读取 step-log URL 返回原 404，job logs REST 返回原限流 403，annotation REST 亦为原 403，均已保留实际响应。本轮取得的是官方 HTML 注释和步骤结论，未取得完整日志或 artifact。接缝、固定测试 SHA 与原 annotation 保存在 ignored `reviewer/ci-publication-r1/ci-r4-failure-audit.json`。Windows 同 run／attempt 1 继续跟踪，尚不能写成八 job 全部终态。

### 自身 CI 最终终态：七 job 成功、一 job 失败，R4 待修

11:15:02 +08 的官方完整 navigation 已为八 job 全部 completed，`totalCount=8`／`hasMore=false`；随后重新读取八份 job 终态页面、run 页面和 Actions 列表。官方列表将同一完整 `5182bfa`、run `43670140205`、Portability #229 记为 completed／failure，run 页面显示 Failure，attempt 仍为 1。

|job|ID|终态|必要步骤|
|---|---:|---|---|
|plan|132678152695|success|1 success|
|Linux 0|132678181493|success|4 success|
|Linux 1|132678181506|success|4 success|
|Linux 2|132678181507|success|4 success|
|Linux 3|132678181518|success|4 success|
|Linux 4|132678181545|success|4 success|
|Linux 5|132678181529|failure|3 success／1 failure|
|Windows all|132678181486|success|5 success|

30 个必要步骤均在实际页面恰好出现一次，合计 29 success／1 failure；唯一失败为 Linux 5 的 Native application regression，具体两测试及可达 R4 见上节。Windows 的原应用回归与 PowerShell 5.1 安装升级均 success，不能遗漏这两个终态；该 job header 为 succeeded／16m54s。八个 job header 与 navigation 结论全部一致，所有非空 step 日志链接均指完整本片 SHA 与各自 job ID。上传步骤成功只认证该步骤页面结论，没有冒称本评审下载或读取了 artifact。

最终原摘要为 ignored `reviewer/ci-publication-r1/20261115T031530388921Z-terminal-summary-r1.json`，74845B／SHA256 `45f8fb8ba15ddfd7ac02af7939347c6d8aac60a2953ae0508aea6225c02a9ed6`；`final-ci-audit.json` 保存固定来源、完整 navigation、八 header、30 必要步骤和最终 Actions 绑定的核对。重读的 63 份官方响应体字节／SHA 全部匹配各自 capture metadata：55 份 200、七份原 403、一份原 404；十二份固定 SHA 的官方 raw 文件也全部保持与发布 blob 字节／SHA 相同。`ci-originals-index-r1.json` 含本轮 126 项原件／来源／摘要，索引 SHA256 为 `1f1955bc02a0813b8fe7cdc0ecce796542aeb3d453995d6068a76c112d7ca4e0`。这些是本片独立采集的实际来源，没有继承前片 CI、重跑失败 job 或混入后继 b 产品。

本轮固定发布身份通过，自身 CI 门禁失败；需求 request-changes、结构维护 approve、开放 finding 1／0，R4 保持开放。修正应单独固定最小测试等待片并验证其原故障接缝和自己的适用 CI，再由同一评审者续核；不能把旧失败改成成功，也不能用后继设计或旧本地通过替代该门禁。本评审到此只写报告与授权 ignored `reviewer/`，未改产品／测试、安装、运行昂贵测试、提交、推送或启动服务。
