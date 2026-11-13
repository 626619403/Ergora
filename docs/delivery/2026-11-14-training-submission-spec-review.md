# F9b2 独立需求／正确性审查

当前结论（同片精确交付终核）：**需求／正确性通过，开放 finding 0。** 原两项 P2 与追加修复已关闭，最终 r6 包身份、受影响安装回归、原生 CPU 原记录、实际浏览器、自身原模板和本地收尾均已独立补核。产品 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34` 已普通发布，24个Git blob及完整远端Ref通过独立核对；自己的CI `43511152711` 官方终态Success、8个job／30个必要步骤通过本轴原件终核。本轴对此精确候选验收完成；结构轴仍以其原报告为准。以下保留各轮身份、原失败和验证范围，历史“待补核”描述仅指该轮。

审查者：fresh-context 独立需求轴 `f9b2_spec_review`；日期：2026-11-14。先读项目 `AGENTS.md`、maintainable-project-delivery Skill 与 independent-review brief、基线中的[原始活动计划](../plans/2026-11-14-training-submission.md)，再读实现及[作者交付](2026-11-14-training-submission.md)。未继承实现会话，未修改产品、测试、原参考或作者验收原件。

## 范围与身份

基线与本次 HEAD 均为 `106481a80abfd168f5b45fbba7381063505239d0`，分支 `refactor/architecture-foundations`；审查对象是其未提交候选。逐项重算 `.ergora/checks/training-submission/review-r1-files.json` 中 **21 个文件，全部匹配**；清单 SHA256 为 `5b5cff51a1dc88ddd98262c10705ef516b1f2d5af2b4367f686a2c4b1c5572df`。17 个 tracked 文件的 `review-r1.diff` SHA256 为 `e14a345b6df4f4daee7a5ec3d13218d03eadcdeb5692e8f0b2680f0a9be9400e`；另全文读取新增提交模块、Service fixture、suite 与交付文档。

检查了 CLI／HTTP／页面到 `training` 的生产调用、注册与 SQLite reservation、原 `perf_temporal.client.main`／models／connection、`agent_platform.training.prepare` 与 LocalTrainingAdapter、core.write／file_lock／processes.run、共享原记录 reader 和固定 run lookup。独立运行 `reference.verify()`，283 冻结文件通过；原目录无 diff。未发现控制面新增 prepare、baseline init、cancel、evidence approve、训练执行或第二实验／调度账本。

## 结论

**初审 r1 需求与行为轴：需要修改，开放 2 个 P2；后续关闭见同片修后复核。** 已检查的发送路径保存 intent 后才持久 attempt，再进入原 client 的 start；REJECT_DUPLICATE／FAIL／single-attempt 与原完整 Experiment 保留。unknown 的恢复分支只 lookup 原 workflow，固定 describe 返回的 run 读取首历史完整输入，并核原 intent memo；NOT_FOUND 不清 attempt，不允许自动重发。预存在／竞态同名运行、完整输入与 memo 冲突、缺历史、网络错误和超时均没有可见的第二次发送路径。

**维护性观察：** 本轴未发现额外的 owner 越权；原 reader 和 lookup 均有实际生产消费者。但当前页面把恢复入口绑在可漂移原件的详情读取上，checkpoint 的写入与读取容量也没有同一合同。完整职责／耦合轴结论由本片独立结构审查负责，本报告不替代该轴。

## 初审 Findings（定位为 review-r1 原快照）

1. **P2：当前原件读取失败会隐藏本来可用的原意图恢复入口。** [training.js:26](../../src/ergora/data/console/training.js#L26) 必须先成功读取当前实验详情，才会在第 126 行读取 submission；第 158 行的列表错误项也只有错误文本，没有按原 experiment ID 进入恢复的入口。可达场景是 start 已被接收而回复丢失，worker 尚未落 job request，随后当前 runner 被删除。原意图和 attempt 完整，HTTP `submission` 返回 200／unknown、`resume-start` 能依冻结 spec、历史及 memo 返回 200／submitted，原生 start 仍为一次；但当前详情因“runner 与原 request 均缺失”返回 400，页面只显示错误，无法展示 unknown 或对账。manifest／spec 损坏也有相同页面依赖。最小修正：让按原 experiment ID 读取本地 submission 与恢复控件拥有独立生命周期，在列表错误项保留该入口；当前详情错误仍明确显示，首次 start 继续要求有效当前原件。继续／对账的确认材料应来自冻结意图，而不依赖当前 runner／manifest 成功读取。

2. **P2：合法来源聚合成的 intent 可以超过自身 reader 上限，并把原操作永久堵在不可读 checkpoint。** [reference_training_submission.py:54](../../src/ergora/reference_training_submission.py#L54) 用默认 1MiB 的 `adapter.read_raw` 读取所有文档，而第 268–270 行把完整 observation 加外层身份后直接 `core.write`。私有探针的 manifest 为 **1,045,927B**，小于现有 **1,048,576B** 文件上限，原 reader／preflight 成功；写出的 intent 为 **1,050,323B**。随后 dispatch/load 及所有 `submission` 调用均报 `File exceeds size limit`，无 attempt、无 native service 调用，但不可变 intent 已存在，缩短当前源文件也不能恢复该原操作。这不是拒绝原本超限的输入，而是 owner 写出自身无法读回的记录。最小修正：为本地 checkpoint 定义覆盖合法来源聚合的有界容量，写前按同一序列化与容量检查，读回使用同一容量；保留外部源文件原有上限，不留下写成后不可读的 intent。

## 初审验证与限制

- 已核作者 `source-r1` 原件：58 项，50 通过／8 失败，98.50 秒，失败为 Service double 缺真实 SDK 使用的 config.identity；`source-r2` 为 1 通过／1 失败、10.57 秒，RPC 错误未保留状态码。旧失败没有覆盖为成功。
- 已核 `source-r3/result.json` 与完整 stdout：新增 submission 11 项加原 runtime 15 项，**26 通过／114.99 秒**。真实 SDK 编解码的离线 Service double 证明其实际覆盖范围；不是运行真实 Temporal 服务或训练 worker 的证据。旧 50 项不整体继承为修改后候选通过。
- 本 reviewer 仅在 `.ergora/checks/training-submission/spec-review-r1/` 运行两个有界离线探针：`probe.py`／`result.json` 实证来源漂移时详情失败但原意图 API 可恢复；`envelope_probe.py`／`envelope-result.json` 实证 checkpoint 容量不对称。HTTP 使用进程内 TestClient，native 发送使用真实 SDK 配合离线 Service double；没有安装、启动服务、运行大 suite、访问模型／数据／GPU 或修改外部 Git。探针引用的所有 Git／配置／训练数据均在本 reviewer 私有目录。
- 源码检查支持 Linux／WSL2 原生 start／resume 的明确限制，以及不导入可选 SDK 的本地 submission 读取路径；本 reviewer 没有 Windows 主机，不能据 Linux 探针声称 Windows 运行通过。
- 新 noneditable 包与 RECORD、真实 CPU Temporal prepared→提交→原 ID 查询／丢回执恢复、浏览器确认／双击／切项目及迟到响应、自身原审查模板、最终冻结身份、普通发布／精确 Ref 与本片自己的 CI **均尚未由本 reviewer 验收**。两项修复须补受影响检查及本 reviewer 同片复核；不能据本报告关闭 F9b2，更不能关闭 F9b3／F9b4、F9c／F9d、真实 B3 或完整 C2。

## 同片修后复核

仍由原 fresh-context reviewer 复核。基线／HEAD 未变；重算 `review-r2-files.json` 的原 21 个文件 **21／21 匹配**，清单 SHA256 `6668d3e9989a540bcd2f3e7f97fb66571c97e30ab8dcdb799ed0c78657de8a21`，`review-r2.diff` SHA256 `f58ce02063b8ae62c669d303deb153e8ba087bf491f747d15ed89798d31e2274`。除交付状态说明外，修复范围严格为 `reference_training_submission.py`、`training.js`、`test_training_submission.py`；已全文读修复并与 r1 安装源码快照比对，原发送／对账分支没有额外更改。

- **P2-1 关闭。** 页面在发起当前详情读取之前建立独立 submission 面板；详情失败只更新 records 区域，坏列表条目也有“查看原件与原意图”入口。已有意图的 confirmation 来自保存 observation，恢复使用此次本地记录返回的 project revision；首次 start 仍等待有效当前原件。原离线 API 场景重放：删除 runner 后 detail 仍为 400，submission 为 200／unknown 并带冻结确认材料，resume 为 200／submitted，native start 仍为一次。另以 Node v24.18.0 执行实际 `training.js` 与原 `ui.js`／`api.js`／`state.js`，仅 DOM／fetch 为离线替身，核坏条目可进入、原详情错误保留、unknown／冻结 runner 可见、错误 SHA 零 POST、双击仅一个 resume POST，切项目后的迟到回执不渲染。实际模块 SHA 为 `65f1b593e4483a0fcd462ac34e92fb233fdd193264a124512a447571f0cd15c5`。该探针不等于真实浏览器验收；辅助脚本最初的 JSON 文本缩进断言和非 JSON pre 选择错误及更正均留存，没有当成产品失败。
- **P2-2 关闭。** aggregate intent 独立有界为 16MiB，发布前使用与原 core.write 相同的 UTF-8／indent／ensure_ascii／allow_nan／末换行序列化核大小，intent 读回使用同一上限，原外部 source 上限仍为 1MiB。重放原跨界输入，manifest **1,045,927B**、intent **1,050,400B**，现 start 与后续 submission 均为 submitted，attempt／receipt 保留；新增 suite 也实证合法 source 小于原上限而 intent 大于旧上限。没有清旧 attempt 或增加恢复重发路径。

独立只读核 r3 noneditable wheel SHA256 `d912e55903fe07442f6f9277c5aba3c1ef76ec1066fb4c5d09b8269d02b72c69`；逐项重算 wheel RECORD **573 行**、安装 RECORD **578 行**，565 个产品文件在当前源码／构建快照／wheel／安装间逐字相等，283 冻结文件全部匹配。原件 `install-r3/regression-r1/result.json` 与 stdout 为 submission 12 项＋reference 6 项＋architecture 14 项，**32 通过／95.27 秒**，受控进程 97.040 秒。r1 安装原件为 **65 通过／4 跳过、154.87 秒**，只保留其当时范围；r2 包没有回归成功主张，修正大 manifest fixture 的跨界值后由 r3 重建和验证，不把 r2 构建当成通过。

本 reviewer 新证据均在原私有 `spec-review-r1/recheck-r2/`：原场景 API `result.json`、容量 `envelope-result.json`、实际模块离线 DOM `ui-result.json`、独立包重算 `package-review.json`。未接触主线程持有的真实服务或浏览器，没有运行大 suite、安装或修改产品。

**需求与行为轴修后源码及已核安装范围通过，开放 finding 0。** 完整本地验收仍待真实原服务完整输入／memo／固定 run／Outcome与原件保持、实际浏览器及收尾、自身模板和最终身份补核；普通发布／精确 Ref与本片自己的 CI另行验收。维护性最终结论仍归独立结构报告，F9b3／F9b4、F9c／F9d、真实 B3与完整 C2保持原边界。

## 追加并发修复的源码补核

基线／HEAD 仍为 `106481a80abfd168f5b45fbba7381063505239d0`。相对已核 r3 包源码，此次仅有页面 setSource 条件收窄、status 读取顺序调整，以及一个定向 snapshot 回归；读取了完整差异与相关原调用者。当前精确 SHA256：`reference_training_submission.py` 为 `4d74c8a8aa074cc708097edccd8702d59eb3028aa1f06830c62ae24adcf20e6e`，`training.js` 为 `f8cdca313391a43d2f0344804882b076cb973ef3bc7b5ea2da93f827eb19d553`，`test_training_submission.py` 为 `7d21544acc13adbaf27d4db6b890bb3a697a26e09fbb35269f7dc15924e053b2`。

- **迟到详情保留对账失败。** 已读独立结构轴 S2 的原场景。setSource 仅在 lastResult 为 not_recorded、首次确认确实需要当前来源时重绘；prepared／unknown 的当前详情不再重建操作面板。以实际 JS 与原 UI／API／state 模块离线执行 unknown 先返回、detail 挂起、显式 resume RPC 失败、detail 最后成功的次序：失败文本在 detail 前后均可见，原 unknown 操作控件没有重新出现；错误 SHA 零 POST、双击仍仅一次 resume。此为源码逻辑的离线 DOM／fetch 替身证据，不替代真实浏览器；结构轴 S2 的正式关闭归其原 reviewer。
- **并发状态读取不再误报损坏。** 已全文读自身模板 `self-review-r1-codex/review.md` 的发现。原作者报告属静态审查；本轴另核 writer 先 attempt 后 receipt／start_conflict rejection 的顺序，并检查 status 改为 result→rejection→attempt 的因果性：可观察到 completion 时，随后读取的 attempt 必已存在；读到旧状态时允许滞后，但不把新 rejection 与旧空 attempt 拼成损坏。新增定向回归覆盖原 reader 读完旧 attempt 后 writer 发布 attempt＋rejection 的场景。本轴执行该回归，并对实际 status 穷举成功、start_conflict、preexisting_run、lookup_rejected 四种 append-only 发布的 **28 个单调读交错**，全部取得 prepared／unknown／submitted／rejected 的有效快照，无虚假损坏错误。

新探针与输出在私有 `spec-review-r1/recheck-r3/` 的 `snapshot_probe.py`／`snapshot-result.json`、`ui-probe.mjs`／`ui-result.json`；未启动／调用／停止真实服务，未读取或改写原 native SQLite，也未重跑大 suite。新增回归是本地 status 算法的定向运行，不能写成 r4 安装 suite 已通过。

**本轴追加源码补核通过，开放 finding 0。** 之前 r3 wheel／32 项的结果继续只证明 r3 字节；r4 包与安装、原真实运行恢复、实际页面、最终 Outcome／history／memo／原件保持及收尾、自身模板最终复审和普通发布／本片 CI仍待独立补核。原 native 验收的失败或 timeout 不因此改写为成功，已 attempt 者只沿原 run 对账的约束保持。

## 最终本地终核

仍为原独立需求轴，HEAD／基线未变。终核前重算 `static-r2.json` 的 **24 个 tracked＋untracked 文件，24／24 匹配**；12 个产品／测试／CI路径按路径及完整字节组合的 SHA256 为 `68a14b81ef3ad8685a7a4aa7b80ee6d134c3706b2fa610f3b0897773418a36bc`。另独立重查223个本地 Markdown 链接，无坏链或清单所列私有机器标识。该24文件身份指本次状态补记前的快照；本报告及后续交付／发布补记不改产品组合身份。

最终主要文件 SHA256：

|文件|SHA256|
|---|---|
|`src/ergora/reference_training_submission.py`|`7a07ffb41f1de95b3142d13e8cf98ec0f942dfc3f2d130fb9d7021873c148b27`|
|`src/ergora/data/console/training.js`|`f8cdca313391a43d2f0344804882b076cb973ef3bc7b5ea2da93f827eb19d553`|
|`src/ergora/cli.py`|`e704d10cd4193415f10ae8476e0c5210096844f9e5d08a7e4b60640f3d564213`|
|`tests/test_training_submission.py`|`7696e32d744767d8c8c0a80055655fb9575476247c9680225f4102f0c6fc1b74`|

### 最后两处修复与安装范围

- **load 并发补读通过。** 阅读相对 r4 的完整小差异及现有定向回归：初读缺 intent、随后观察到新 dependent 时再读一次 intent，真正缺失仍拒绝；原身份及完整 checkpoint 核验不变。检查了原结构轴 `publication-orders-r4-result.json` 的550个交错与真正孤儿拒绝原件；这是该轴实际执行，本轴没有冒称重复执行。已核 r5 原安装 stdout／result：两读交错、单次发送和 CLI／HTTP 共3项通过／21.99秒，受控23.816秒。
- **CLI 未确认／拒绝退出码通过。** 读取自身模板 r2 原 finding 和最终源码：start／resume-start 仅 submitted 退出0，其余已返回状态退出1；原 JSON 仍打印一次，观察操作保留读取成功退出0，异常沿原处理。现有丢回执／NOT_FOUND及预存在／竞态冲突场景实际调用 CLI main 并断言退出1，健康恢复仍断言0。没有为此增加独立 suite。
- **最终 r6 安装身份独立重算通过。** wheel SHA256 `d71a44f394325ae5fce08ab36f4e6f3830b34fd1cecca9a324d1f6196409cd5a`；565个产品文件在当前源码、构建快照、wheel和安装间逐字相等，wheel RECORD573行、安装 RECORD578行的哈希／长度全部相符，283冻结文件匹配，direct_url为 noneditable wheel。回归使用的测试快照与当前字节一致。原 stdout／result为丢ACK／超时两项、预存在／竞态两项及健康CLI／HTTP一项，共 **5通过／55.86秒，受控57.627秒**。

另已读 r4 原完整 stdout／result 的 submission13通过／95.02秒、受控96.905秒；其时尚无随后 load 补读和CLI退出码修正。r3的32项、r4的13项、r5的3项和r6的5项各保留原包范围，不合并宣称最终包重跑全部suite。

### 同一原生数据库、原 run 与负结果

全文读取原驱动、真实失回执 helper及同库恢复驱动。初始 `native-r1` 等待浏览器 marker600秒后超时，原 failure／SQLite和618.469秒清理记录保留；没有重写为首轮成功。`native-r2`确实重开原数据库路径，沿原 control／registry／prepared文件和已产生的 run 恢复，驱动记录154.959秒通过。

本轴以真实 SDK 的 `WorkflowHistory.from_json`／DataConverter **仅离线解码保存的四份 history**，独立重算history SHA；核完整首 Experiment等于原spec及intent冻结spec、原workflow／actual run、maximum_attempts=1、原意图memo、attempt／result摘要与实际丢ACK时保存的run全部相等。末事件的完整Outcome等于SDK保存结果、最终固定run查询和作者summary；保存的原服务list结果每个workflow仅列同一run。

|原实验|固定 run ID|history事件数|原控制 Outcome|原执行器收集|
|---|---|---:|---|---|
|submit-ack|`01a1d6b4-dfd4-7c31-96ca-806cc21c5054`|254|CANCEL_UNCONFIRMED|CANCELLED|
|submit-loss|`01a1d6b4-ef3f-70ab-be77-609a56fd5a7b`|254|CANCEL_UNCONFIRMED|CANCELLED|
|submit-page-recovery|`01a1d6ba-3eb8-720a-8c28-93692ed39e86`|178|CANCELLED|CANCELLED|
|submit-browser|`01a1d6c2-d67f-7977-afec-c6b51e2df613`|46|CANCELLED|CANCELLED|

逐项重算22份原准备文件，全部保持；页面恢复后还原的spec SHA与原ready记录相同。四个原job request的完整Experiment／runner、fence与执行器结果binding均与冻结原件一致，均无started.json。前两个workflow因原等待期间寿命超限已终态，后续原cancel CLI退出1且原already-completed错误保留；后两个cancel退出0。不能把后来本地收集CANCELLED或monitor的-9解释为前两个控制取消已确认，更不能据此证明外部训练停止。

这里覆盖r1真实start／失ACK、r3额外真实失ACK、r4页面在原spec缺失时恢复原run和prepared意图继续一次发送；后来的load补读及CLI退出码沿各自安装检查验收。最终JS与r4服务实际返回的JS相同，**没有声称重新执行一次全r6真实服务旅程**。

### 浏览器、原模板与收尾

已读r4实际浏览器脚本、命令结果和snapshot，并视觉查看1440／390保存截图。日志68请求中67个200、1个故意缺spec的detail400；默认导航均为GET且无实时status查询。三个POST均为显式resume：实际unknown恢复一次、prepared继续一次、既存submitted回执的迟到探针一次；无start POST。错误SHA snapshot保留提示且未发送POST，两个实际双击分别仅一请求。三POST响应的完整JSON字节长度与SHA均由原本地receipt重算匹配。不能把预期detail400描述为干净console。

实际submission GET被暂扣后切项目，释放后未覆盖新项目；迟到resume场景的初始GET明确重放该原实验更早的真实unknown，而POST实际后端仅读取既存submitted回执。后者证明迟到结果隔离，不是新增一次失ACK恢复。最初route探针提前unroute的helper失败及旧浏览器／服务已停失败保留。1440／960／390记录的document宽度等于viewport，main宽1208／728／322；实际桌面／手机截图中长身份值换行、提交记录及操作区可见。

已读自身原模板r1／r2原request-changes及最终r4原approve。独立核最终实际run `cb59439c91fd41deb95f8265ae00fb76`：18份完整文件259,686B在task／实际stdin中逐项哈希匹配；265,872B prompt与input、实际stdin逐字一致，三个完整祖先指令／Skill资源与冻结assets相等且均在stdin。16份源码／测试／邻接原owner仍与当前文件一致；两份计划／交付文档之后仅追加状态，不冒称旧审查包含后来状态文本。原结果SHA256 `54bdc7415d79849a477e579fa944478f8357eaddd94d438a8475fe51124aca50`，68.027秒成功approve。中间r3 helper在模型调用前复制不存在配置路径失败，目录原件保留，没有调用成功主张。实际后端为用户授权Codex回退；这只证明静态完整材料交付与原审查结果，不证明模型逐字理解、重跑运行验收或异后端成功。

原native／Web monitor清理均已结束，浏览器close退出0。除核作者cleanup原件，本轴还只读当前`/proc/net/tcp{,6}`与进程记录：7233／43911／48373／54665均无监听，两个原浏览器PID不存在，无匹配验收目录的训练runtime进程；未连接、启动或停止服务。此为本地验收进程生命周期，不扩大为外部作业停止证据。

本轮独立脚本及精简结果在原私有目录 `spec-review-r1/recheck-final/`：`package_review.py`／`package-review.json`、`native_review.py`／`native-review.json`、`evidence_review.py`／`evidence-review.json`。均为只读身份与原件检查，仅把结果写入本轴私有目录；没有安装、运行大suite、修改产品／原证据、读写模型／GPU或调用真实服务。[公开精简证据](evidence/2026-11-14-training-submission.json)与上述原件所述范围相符。

**最终本地需求／正确性终核通过，开放finding 0。** 独立结构／维护性结论仍归原结构轴报告。普通开发分支发布、精确Git对象／远端Ref与自己的必要CI尚待送核；不得借F9a／F9b1成功完成本片发布。Windows原生提交、F9b3／F9b4、F9c／F9d、真实B3与完整C2仍保持原边界，无模型、数值质量、性能、采用或外部停止成功主张。

## 普通发布与精确 Ref 补核

已沿本片只读核产品提交 **`0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`**，唯一父提交为基线 `106481a80abfd168f5b45fbba7381063505239d0`。相对该父提交恰为24个文件；逐项从Git对象读取完整字节，与最终`static-r3.json`的24份哈希及长度全部相等。12个产品／测试／CI路径组合SHA仍为 `68a14b81ef3ad8685a7a4aa7b80ee6d134c3706b2fa610f3b0897773418a36bc`，与本地通过候选一致；完整baseline→candidate的`git diff --check`退出0。另从同一Git树核226个本地Markdown链接均有原对象，无清单所列私有机器标识。

阅读原`commit-r1.json`、普通`push-r1.json`和`ref-r1.json`，提交／推送／Ref均退出0，无强推或合main。除核保存的完整Ref，本轴另实际执行一次只读`ls-remote`，远端 `refs/heads/refactor/architecture-foundations` 精确返回上述40位提交，退出0、stderr空。复核脚本及原返回保存在本轴私有`recheck-final/publication_review.py`／`publication-review.json`。

本补核仅绑定该已发布Git对象，不把随后工作树、F9b3计划或后续修改纳入F9b2候选。**普通发布与精确Ref通过；F9b2自己的必要CI仍待原件，开放finding保持0。** 后续补记属于状态记录，不重复产品审查，也不借前片CI完成本片。

## 自己的 CI 原件终核

仅核上述F9b2完整提交，未使用F9b3工作树。独立从候选Git对象读取`.github/workflows/portability.yml`及`scripts/ci/linux-groups.json`，SHA256分别为 `ec2816e893c25ff3a7f96513e677bdf53f42d90b3cd79fe585e474a27c0121b2` 和 `bf1aaca345ff0eab43880a4a1fc8136c1704dc1ea3fa5d1514e98531fe7acd68`。原配置生成六个Linux／Python3.11分组、Windows／Python3.12全组及plan，共8个job；新增`test_training_submission.py`恰登记一次于Linux group5。

本轴实际执行独立离线原件核验：读取官方run初始HTML、UI job映射JSON、末次`ci-run-html-r5`及八个job原HTML，共 **11份HTTP200原件**，逐项核请求／最终官方URL、完整响应长度及SHA256，与保存receipt和最终`ci-terminal-r4.json`一致。初始run链接绑定完整候选SHA，UI批次完整列出八个唯一job ID且hasMore=false；其早期in_progress状态只用于名称／ID映射，不当作终态成功。最后run页面明确为[CI 43511152711](https://github.com/626619403/Ergora/actions/runs/43511152711)的Success，完整commit链接和开发分支均匹配；页面SHA256为 `db14edd48c94bb4d7243f05a43c32dc8d69fc67d4a4c0bb727ebf8e67cb5fb87`。

另自行解析每个原HTML的`check-step`，逐个核必要名称、success、开始／完成时间、job-completed及包含完整候选SHA和正确check ID的log路径：plan的Read explicit test groups一项；六个Linux job各有Build and install wheel、Packaged reference identity、Native application regression、Upload regression observations四项；Windows除同四项外另有Windows PowerShell 5.1 installer and upgrade，共 **1＋6×4＋5＝30项，全部完成且success**。Windows job `132181511879`使用末次r4原件，其回归及PowerShell步骤已完成，完整页面SHA256为 `ad52756aafc4251cb4c48d1a5f0105c7e6bff683c9ae7622076fb1a1cb56d784`。Linux group5 job为`132181511662`，相同完整候选的必要步骤均通过。早期terminal r1／r2／r3仍为In progress且必要步骤未齐，原件保留，没有倒填成功。

私有独立脚本及逐项结果为`spec-review-r1/recheck-final/ci_review.py`／`ci-review.json`，结论accepted=true、剩余finding 0。该次实际执行的是保存原件的哈希／URL核验、候选Git读取及HTML解析；未发起HTTP／REST请求、下载日志／artifact、触发CI、重跑本地测试、安装、运行模型／GPU或提交／推送。HTML中的成功步骤支持该候选既有CI合同，不提供未下载的pytest数量／日志内容，也不改变Windows原生training start／resume不支持的范围。

**F9b2精确候选的本地、普通发布／完整Ref及自己的必要CI均通过本需求轴终核，开放finding 0。** 此处仅补原片状态，不扩大为F9b3／F9b4、F9c／F9d、真实B3、完整C2或外部作业停止完成；无产品变化，不递归要求新的产品审查。
