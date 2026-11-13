# F9b2 独立结构／性能／冗余审查

日期：2026-11-14。审查者：fresh-context 独立结构轴（`f9b2_structure_review`），未参与实现。依据 `AGENTS.md`、maintainable-project-delivery 及 independent-review brief、codebase-design、code-review 和[原活动计划](../plans/2026-11-14-training-submission.md)；范围仅为已准备实验 start 与原意图恢复。prepare/init、cancel、evidence 批准和 GPU 保持后续片。

## 候选与结论

基线／HEAD：`106481a80abfd168f5b45fbba7381063505239d0`。本轮检查未提交的 21 文件，精确清单为 `.ergora/checks/training-submission/review-r1-files.json`（SHA256 `5b5cff51a1dc88ddd98262c10705ef516b1f2d5af2b4367f686a2c4b1c5572df`），tracked diff 为同目录 `review-r1.diff`（SHA256 `e14a345b6df4f4daee7a5ec3d13218d03eadcdeb5692e8f0b2680f0a9be9400e`）。检查时 21 项均与清单一致。全文读取新提交 owner、Service fixture 和新增 suite，读取所有生产改动及相邻调用者／原 owner；文档状态后续补记不继承本轮产品结论。

首轮需求符合性：**待修正并补验收**。发现合法输入导致持久意图不可恢复的 P2；其余已检查的单次 start、unknown 后仅 lookup、完整原输入／memo 归属校验符合计划。首轮结构／维护性：**request changes，1 个 P2**。未发现需要新建 Task/Experiment 继承体系、第二调度器或实验账本的理由。另轴提出的页面恢复依赖问题由需求轴记录，本报告不重复计数，修复后仍需补核本轴所涉调用关系。**最终本地结构复核通过，开放 0；S1／S2／S3 与自身模板提出的 CLI 退出码 S4 均已关闭。r6 包、分轮原生／页面旅程、自身调用和收尾已补核；精确提交／远端 Ref／本片自己的 CI 仍待发布后核验，见末节。**

## S1 · P2 · 聚合意图沿用了单源文件读界

位置：[`reference_training_submission.py:53`](../../src/ergora/reference_training_submission.py#L53) 的 `document/optional`，以及同文件第 268–270 行的意图写入。

可达场景：原 manifest 小于 1 MiB，baseline／runner／spec 均合法，预检通过；意图再包含这些原件、文件摘要和登记身份，完整 JSON 因而超过 1 MiB。`core.write` 写入时没有核定其后能否重读，而 `document` 仍使用 `adapter.read_raw` 默认单文件 1 MiB 界。

本轴零网络私有探针实测：1,047,000B manifest 可以离线读取并成功 prepare，产生 1,051,329B `.intent.json`；随后 `training.submission` 报 `BLOCKED: File exceeds size limit`，此时尚无 attempt。公共 start 在本地 prepare 后进入第二进程也必须重新 load 同一意图，因此会在发送前失败；读取／继续／对账均无法再进入，留下合法来源产生却不可恢复的 checkpoint。探针与摘要位于 `.ergora/checks/training-submission/structure-review-r1/{probe.py,result.json}`。

最小修正：由提交 owner 给聚合 intent 单独的有界读取容量，并在首次写入前用与 `core.write` 相同的序列化核定可重读；源 manifest 等仍保持原 1 MiB 合法范围。相邻 `_Creation` 已区分单源与聚合读界，可沿用做法，无需复用其 Task creation 语义。增加一个超过 1 MiB 聚合意图仍可提交、重读／恢复的回归即可，不必扩展为大配置组合套件。实现者已接受；修复与关闭证据见 r2 补核。

## 结构、控制流与性能判断

- `training` 的应用 Interface 被 CLI 与 HTTP 两个真实生产文件使用。新 `_Submission` 集中训练意图、attempt、归属和回执，单个进程入口是清晰 owner；原 Task submission 依赖 Task creation，不适合套用。`reference._training_records` 由离线 reader 与提交预检复用，runtime `lookup` 由实时 status 与 submission 复用；这些提取有真实消费者与局部语义，未制造泛化层。
- 原 `perf_temporal.client.main/connect/start` 继续拥有输入装载、REJECT_DUPLICATE、FAIL 和 maximum_attempts=1；包装仅在独立进程内加 checkpoint／memo。预先存在与竞争 run 的拒绝、attempt 前后重读、回执关联校验、unknown 下禁止重发都保护可达的持久状态或发送竞态，未发现应删除的防护分支。
- 应用层 DB 预留仅覆盖本地 prepare／prepare-resume；dispatch／reconcile 在退出 DB 上下文后执行。原文件锁使用 nonblocking 获取，锁内网络调用仍归专用进程；`processes.run` 覆盖 Git 后代及超时／中断清理。同步本地预检本身不会被 asyncio timeout 抢占，实际硬停止依赖父进程 `timeout + 5`；首次 start 有两个顺序进程，不能把配置 timeout 当整次操作总时限。该边界有界，但未在真实慢磁盘上测延迟，不据此新增问题。
- Windows 原生只提供本地 submission 读取，start/resume 明确拒绝并指向 WSL2；未把原 Linux Git／训练 owner 宣称为 Windows 执行支持。本轴在 Linux 阅读了 Windows 路径／进程 owner，没有执行 Windows 验收。
- 私有离线探针另外用 poll=300、max_run=86400、release_wait=604800、cancel_wait=3600、runner timeout=82800 成功 prepare，未发现将原有效配置范围钉在默认值的检查。源 reader 仍按单件有界读取，列表保留原分页算法；S1 是新增聚合持久化引入的容量不匹配。
- 新 suite 登记既有 Linux group5，未新建流水线。Service fixture 通过真实 SDK 编码与解码，检查原发送策略、单次接收、失回执、NOT_FOUND／RPC、完整输入／memo 冲突与共享 CLI／HTTP 行为；这些覆盖静默重复发送与错误认领，具有回归价值。固定 fixture run ID 和原策略断言对应测试数据／固定合同，不限制产品配置。架构 allowlist 的一处追加对应新 reference owner，未增加无生产用途的断言。

## 已核证据与限度

审阅 source-r1 原 stdout／result：50 通过、8 失败／98.50 秒；source-r2：1 通过、1 失败／10.57 秒。原失败分别涉及 Service 缺少 SDK config.identity、RPC 状态码未保留，未被抹去。审阅 source-r3 完整原件：新增 11 项与原 runtime 15 项，共 26 通过／114.99 秒；该结果是现有候选的服务替身证据，不是真实 Temporal 旅程。本轴未重跑这些 suite。

本轴实际执行了约 1.5 秒的私有有界离线探针，并核 21 文件 SHA、`reference.verify` 全部 283 冻结文件通过且未启动 runtime。未改产品或原件，未执行 Git 写操作、安装、服务连接、模型／GPU或大 suite；只新增本审查文档与私有探针。

首轮阻塞项为 S1 的修复及重验。noneditable 最终包、受影响安装验证、真实 CPU 提交／失回执恢复、浏览器生命周期、自身模板和精确最终候选补核当时仍待实现者交付；不得借 F9a／F9b1 的结果关闭。本片提交／推送及自己的 CI 原件也尚未作为最终候选审查，本报告不构成发布通过。

## r2 修复补核与当前结论

基线仍为 `106481a80abfd168f5b45fbba7381063505239d0`。核 `.ergora/checks/training-submission/review-r2-files.json` 的 21 项均匹配，清单 SHA256 `6668d3e9989a540bcd2f3e7f97fb66571c97e30ab8dcdb799ed0c78657de8a21`，对应 diff SHA256 `f58ce02063b8ae62c669d303deb153e8ba087bf491f747d15ed89798d31e2274`。相对 r1 仅提交 owner、training.js、新 suite 三个产品／测试文件与交付状态文档变化。

**S1 已修复，结构复核关闭。** `.intent.json` 单独使用 16 MiB 读界，单源及其他 checkpoint 仍为 1 MiB；首次发布前按原 `core.write` 的 UTF-8／ensure_ascii=False／indent=2／换行序列化核定聚合大小。该检查归持久化 owner，防止写入自己不能读取的 checkpoint，没有泛化 Task 语义。新增一项 near-limit manifest 回归覆盖真实 start、超过 1 MiB 的 intent、读取与单次发送，针对原静默恢复风险，价值明确。

本轴重放原私有探针，保留 r1 原件不改：1,047,000B manifest 生成 1,051,347B intent 后可读为 prepared，且原先不可读的 1,051,329B checkpoint 已能按原 intent SHA 读取。另在私有进程把聚合容量临时缩小至 4 KiB，模拟写界不足，prepare 明确拒绝且未发布 intent／attempt；这只证明写前失败顺序，不冒称实际写入了 16 MiB 原件。结果为 `structure-review-r1/replay-r2-result.json` 与 `recheck-r2-result.json`，本轮约 1.8 秒、零网络。

页面将提交面板收拢为同页私有算法，详情与提交记录并行读取，坏条目保留原意图入口；恢复确认材料由 checkpoint 返回。这些职责位置合理，无需新文件或共享 UI 框架。不过迟到详情仍可重绘已经发生操作的提交面板，产生下项新问题。

### S2 · P2 · 迟到的当前详情覆盖原意图对账失败

位置：[`training.js:91`](../../src/ergora/data/console/training.js#L91)，`setSource` 对任何 `lastResult` 调用 `showSubmission`。

可达场景：submission GET 先返回 unknown，当前 detail GET 尚在途；操作者确认原意图后点击对账，RPC 失败，页面显示原错误；随后最初的 detail 成功返回。`setSource` 使用操作前的 unknown 重建提交面板，清除刚取得的错误并恢复操作控件。它没有重发 start，但使相邻只读请求覆盖独立操作的最新失败事实，违反失败原因保留及独立生命周期要求。

本轴用真实 training.js 源码在纯离线的最小内存 DOM 中执行此顺序：一次模拟 resume 请求后 `UNAVAILABLE` 可见为 true；迟到 detail 后为 false，对账控件重新出现。源码 SHA 为 r2 的 `65f1b593e4483a0fcd462ac34e92fb233fdd193264a124512a447571f0cd15c5`。原件为 `structure-review-r1/late-detail-r2.mjs` 及 `late-detail-r2-result.json`，无真实网络／浏览器调用。

最小修正：`setSource` 仅在 `lastResult.status === 'not_recorded'`、首次确认需要当前来源时重绘。prepared／unknown 等已有原意图完全沿其自身生命周期；当前详情只更新自己的记录区，不覆盖对账状态或错误。修正与关闭证据见后续源码补核。

审阅新增安装原件：r1 六 suite 65 通过／4 平台跳过、154.87 秒，只覆盖修复前包；r3 noneditable wheel SHA `d912e55903fe07442f6f9277c5aba3c1ef76ec1066fb4c5d09b8269d02b72c69`，package-identity 记录 565 产品文件／两 RECORD／283，源码快照与 r2 产品摘要一致。r3 的 submission 12＋reference 6＋architecture 14 共 32 通过／95.27 秒（受控 97.04 秒），包括大 manifest 回归。本轴读取结果、stdout 与身份原件，没有重跑 suite。r2 包未跑测试，不能写作通过。

**r2 当时结论：结构／维护性 request changes，开放 S2 一个 P2；S1 关闭。** 真实 CPU、浏览器、自身模板及最终发布／CI 完整原件仍待送核；r3 安装通过不能关闭页面迟到反馈问题，也不代表全片验收完成。

## 源码 r3/r4 补核：开放 0

这里的 r3/r4 指本轴私有探针轮次，不等同安装包轮次。相对 r2 产品仅 training.js、提交 owner 与新增 suite 变化；本轴留存的完整 21 文件 SHA 为 `structure-review-r1/source-r3-files.json`，邻接 F9b1 结构文档的发布补记属于状态更新。当前三文件精确身份：

|文件|SHA256|
|---|---|
|`src/ergora/data/console/training.js`|`f8cdca313391a43d2f0344804882b076cb973ef3bc7b5ea2da93f827eb19d553`|
|`src/ergora/reference_training_submission.py`|`7a07ffb41f1de95b3142d13e8cf98ec0f942dfc3f2d130fb9d7021873c148b27`|
|`tests/test_training_submission.py`|`ef29b57a2862dea1427557fa872d8fadddc806c3c8b161023095d2ea8cac76c6`|

**S2 关闭。** `setSource` 仅对 not_recorded 重绘，已有意图独立于当前详情。保留 r2 原探针与失败结果不改，同一真实页面算法的 r3 重放显示：RPC 错误在迟到详情前后均可见，对账控件没有被重建；一次模拟 resume、零真实网络。结果为 `structure-review-r1/late-detail-r3-result.json`。

### S3 · P2 · 并发发布时误报合法 checkpoint 损坏，已关闭

自身模板原回复 `self-review-r1-codex/review.md` 首先指出 `_Submission.status` 读取 attempt 后再读 start_conflict rejection 的交错：读者看到旧的无 attempt 与新的 rejection，误报原 checkpoint 冲突。改为先读 result 与 rejection，再读其前置 attempt，保留合法滞后状态，无需在 status 上等待网络文件锁。本轴核实该修正和针对交错的单个回归，原单项实跑 1 通过／0.16 秒。

沿同类发布依赖，本轴另实证 [`reference_training_submission.py:107`](../../src/ergora/reference_training_submission.py#L107) 的首次 load 交错：读者初读无 intent 后，写者合法发布 intent→attempt，再检查 dependent 是否存在时误报“checkpoints have no original intent”。私有 `load-race-r3-result.json` 保留该首次错误与第二次正常读取，执行约 0.04 秒、零网络。影响是 CLI／HTTP 在合法首次提交期间产生虚假的持久化损坏提示，不是一次真正孤儿记录，也没有证据表明它重发 start。

最小修正已实施：仅当观察到 dependent 而初读无 intent 时重读一次 intent；仍无原意图则保留真正孤儿错误。全部身份／checkpoint 验证沿原流程执行，未增加轮询、全局锁或新持久化 owner。单个现有并发回归扩展为这两个实际交错，改名 `test_submission_read_racing_with_conflict_publication_keeps_valid_checkpoints`；本轴实际运行 1 通过／0.14 秒，受控约 0.46 秒，精确源码／测试 SHA 记录在 `structure-review-r1/status-r4-result.json`。它保护并发下原本会被误报的合法状态，不是重复普通错误断言。

本轴还在真实 `load/status` 方法上枚举 550 个小型内存发布交错：intent→attempt→receipt 220 个、intent→attempt→start_conflict 220 个、intent→preexisting_run 及 lookup_rejected 各 55 个。所有交错只返回合法的 not_recorded／prepared／unknown／submitted／rejected 快照，虚假损坏异常为 0；真正只有 attempt 的孤儿仍按原错误拒绝。该探针约 0.06 秒，无 SDK、服务或文件发布；它证明本地不可变记录的读序，不代替真实远程并发验收。原件为 `structure-review-r1/publication-orders-r4.py` 及 `publication-orders-r4-result.json`。

**当前源码结构／维护性复核通过，开放 0。** S1／S2 与同类并发一致性 S3 均已记录修正并补核。本轴没有看到新的职责、性能或冗余问题；最终 noneditable 包、完整原生 CPU／浏览器／自身模板、失败保留与收尾、提交／推送及自己的 CI 仍须绑定最终候选送核，不将当前源码通过写作全片发布通过。

## 最终本地验收补核：通过，开放 0

基线／HEAD 仍为 `106481a80abfd168f5b45fbba7381063505239d0`，分支仍为 `refactor/architecture-foundations`。本轮核最终 12 个产品／测试／CI 路径的逐件摘要与组合 SHA256 `68a14b81ef3ad8685a7a4aa7b80ee6d134c3706b2fa610f3b0897773418a36bc`；`static-r2.json` 当时覆盖 24 个 tracked＋untracked 文件、223 个本地链接，私有机器标识与完整变更空白检查无问题。新增文件的 `diff --no-index --check` 退出 1 且无 diagnostic 仅表示文件差异，不能记为失败或遗漏其检查。本报告及其他最终状态文档的后续补记不改变该产品身份；提交后仍须核完整 Git 对象。

### S4 · P2 · 未确认／拒绝的 CLI 操作误报成功，已关闭

自身原模板 r2 的 request-changes 指出：start／resume-start 得到 unknown 或 rejected 时原 CLI 仍退出 0，调用脚本会将未确认发送或归属冲突误判为成功。修正在原 CLI 分支打印原 JSON 后，只对 submitted 退出 0，其余提交状态退出 1；只读观察仍按读取成功退出 0。没有在提交 owner、HTTP 或页面复制退出码策略。

本轴阅读最终 CLI、原失败场景的扩展断言及手册，并用真实 CLI 主函数作 12 次零网络有界调用：start 与 resume-start 各覆盖 prepared／unknown／rejected 退出 1、submitted 退出 0；submission／status／show／list 的成功读取退出 0，原 JSON 全部保持。私有原件为 `structure-review-r1/cli-exit-final.py` 及 `cli-exit-final-result.json`，约 0.66 秒。另审阅最终 r6 安装原件与 stdout：两种丢回执恢复、两种归属冲突和 CLI／HTTP 健康共享路径共 5 项通过／55.86 秒，受控 57.627 秒；它们仍是 SDK Service 替身检查。本轴没有重跑 suite。该修正小且归属明确，扩展现有失回执／冲突用例具有回归价值，无需新套件。

### 最终包与产品身份

r6 wheel SHA256 为 `d71a44f394325ae5fce08ab36f4e6f3830b34fd1cecca9a324d1f6196409cd5a`。本轴独立读取 wheel、实际安装文件及两份 RECORD，核实 573 个 wheel RECORD 条目、578 个安装 RECORD 条目，565 个产品文件同时等于当前源码与实际安装，noneditable，283 个冻结参考文件全部保持。私有验证器与结果为 `structure-review-r1/final-package-evidence.py`、`final-package-evidence-result.json`；仅重读现有文件，无安装操作。

|最终关键文件|SHA256|
|---|---|
|`src/ergora/cli.py`|`e704d10cd4193415f10ae8476e0c5210096844f9e5d08a7e4b60640f3d564213`|
|`src/ergora/reference_training_submission.py`|`7a07ffb41f1de95b3142d13e8cf98ec0f942dfc3f2d130fb9d7021873c148b27`|
|`src/ergora/data/console/training.js`|`f8cdca313391a43d2f0344804882b076cb973ef3bc7b5ea2da93f827eb19d553`|
|`tests/test_training_submission.py`|`7696e32d744767d8c8c0a80055655fb9575476247c9680225f4102f0c6fc1b74`|

本轮也核 r5 的 3 项安装定向检查及四份原回执的最终 reader 离线重读。r4 原生／页面旅程后只修改 load 发现 child 时补读 intent，以及 CLI 退出码；r5／r6 分别验证这些改动。r4 提交 suite 13 项、r5 3 项和 r6 5 项各归其原包，不能合称一次最终 r6 全套或新原生旅程。

### 原生控制、页面与收尾

本轴完整阅读 native-r1／native-r2 驱动，独立解码四份原 history，并将完整输入、意图 memo、attempt／回执、固定实际 run、manifest／job／fence 与服务列出的唯一原 run 逐件关联，重新计算 history SHA。四个 history 事件数分别为 254／254／178／46；原 Outcome 前两个为 CANCEL_UNCONFIRMED，后两个为 CANCELLED，本地执行器收集均为 CANCELLED，均无 started.json、未执行 runner。前两个已终态控制的后续 cancel CLI 退出 1，后两个退出 0，原错误回执保留；本地收集与 monitor 停止没有被写作远端确认停止。两个真实扣住 ACK 的记录都关联服务实际接收后的原 run，未伪造接收。

native-r1 等待浏览器 marker 的原 600 秒超时及当轮服务收尾保留；native-r2 重开同一 SQLite、恢复原 ID，没有 reprepare。原 22 份准备文件逐字不变，故意移走的 spec 恢复后原 SHA 一致。当前 spec 缺失时页面仍恢复原 unknown 意图，另一已有 prepared／无 attempt 的意图经显式确认后继续一次。私有逐件验证器为 `structure-review-r1/final-native-evidence.py` 及 `final-native-evidence-result.json`；本轴仅读原件，不接服务或活跃数据库。

浏览器原件中共 68 个 HTTP 请求：67 个 200、1 个预期的当前详情 400。当前详情错误保留时，原提交记录读取仍为 200；错误 SHA 的操作没有 POST，两个正确 SHA 双击各只发生一次实际 resume。第三个 POST 属迟到回执探针：GET 重放该实验真实早先的 unknown，实际后端 POST 仅读取已存在的 submitted 回执，再在切项目后释放；没有新的 start。真实 submission GET 的延迟／切项目探针同样通过。首个 route helper 失败和浏览器配置路径失败保留，修正后的两个迟到探针原 exit 均为 0，未将失败改记成功。

已查看 1440／960／390 三张实际截图，并核原布局数值，均无整页横向溢出，长 SHA、原结果与提交操作区可见。实际服务返回的 training.js SHA 与最终包相同。最终收尾原件显示 7233 及三个 Web 监听均关闭、两个浏览器 PID 已不存在、验收目录无训练 runtime 残留；该记录只证明本地验收生命周期。额外关联校验在 `structure-review-r1/final-local-evidence.py`、`final-local-evidence-result.json`。

### 自身模板、证据口径与结论

本轴核最终 `self-review-r4-codex` 原 admission、输入／task／composition、实际 stdin、run 与原 result：18 份完整文件共 259,686B 全部逐件匹配输入清单，16 份产品／相邻文件等于当前源码；两份计划／交付文档为最终记账前的原快照。三份原模板祖先 instructions／Skill 内容均与包内原件及实际 stdin 一致，非仅登记资源名。原调用成功 68.027 秒，decision 为 approve，原结果 SHA256 `54bdc7415d79849a477e579fa944478f8357eaddd94d438a8475fe51124aca50`。r1／r2 原 request-changes 分别带来 S3／S4，已逐项修正；中间 r3 helper 在调用模型前因配置路径错误失败的原件保留。实际使用已授权 Codex 回退，原 Claude 超时沿既有证据保留，没有异后端成功主张；不以 stdin 字节送达推断模型理解或 MCP 能力。

已核[交付](2026-11-14-training-submission.md)、[公开证据](evidence/2026-11-14-training-submission.json)及活动计划的范围：最终 r6 安装、r4 原生／页面、负 Outcome 与 helper 失败各按原身份记录，不宣称模型、MLflow、GPU、性能收益、采用或外部作业停止。新 owner／共享 reader 与 lookup 的真实消费者、DB／进程／文件锁边界、原训练及批准所有权仍合理；没有发现应删的结构、防护或测试，也没有未解决的性能退化证据。

**最终本地结构／维护性验收通过，开放 0。** 本轮只运行小型离线核验并读取已有测试、服务和浏览器原件，未重跑安装、模型、服务、浏览器或大 suite；只编辑本报告及私有复核产物。精确提交／普通推送／完整远端 Ref 与本片自己的必要 CI 尚待原件送核；本结论不继承 F9b1，也不关闭 F9b3／F9b4、F9c／F9d、真实 B3 或完整 C2。
