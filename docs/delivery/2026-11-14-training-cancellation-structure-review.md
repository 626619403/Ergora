# F9b3 独立结构／维护性审查

审查者：fresh-context 独立结构轴 `f9b3_structure_review`；日期：2026-11-14。未继承实现会话。先读 `AGENTS.md`、[总计划](../PLAN.md)、[本片 B3.1–B3.5 合同](../plans/2026-11-14-training-cancellation.md)，再读实际差异、新文件全文、调用方和原训练／Task owner，最后读[作者交付](2026-11-14-training-cancellation.md)。应用 maintainable-project-delivery 的 independent-review brief、codebase-design 和 ergora-codebase-quality 的模块／测试／仓库约定；未修改产品、测试、参考文件或作者验收原件，未安装、提交、推送或启动服务。

当前结论：**本轴所审 B3.1–B3.5 需求符合性通过；结构／维护性通过，开放 finding 0；精确交付补核完成。** 最终 r3 身份、两轮安装的完整分段覆盖、原生 CPU／页面／自身模板／收尾及公开证据已补核。固定产品提交 `fad53478c9261157b3016563b410b9d4b4d85b9d` 的 35 个 Git blob、普通推送及原完整远端 Ref 已补核；本片自己的 CI `43516776101` 官方终态为 `Success`，8 个 job 和 30 个必要步骤均已独立核原件通过。以下首轮及补核中的“待验”保留其当轮身份，最终状态见末节；完整需求轴结论仍归[独立需求报告](2026-11-14-training-cancellation-spec-review.md)。

## 精确检查范围

基线／审查时 HEAD：`0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`；分支 `refactor/architecture-foundations`。本轮检查未提交的 28 项，含 21 个 tracked 改动与 7 个新文件。清单为私有 `.ergora/checks/training-cancellation/review-r1-files.json`，SHA256 `128e9f1c8b81699601843765213e3ee46659d065b699c15ce39c48d847954275`；tracked diff 为同目录 `review-r1.diff`，SHA256 `8f171a8e59ab9b09df18d1614bda2bd8747c609f729f28549bfed7bc91560032`。独立逐项读取，28 项完整字节数／SHA 与清单一致；新文件由清单和实际全文共同覆盖，不把 tracked diff 当作新增文件内容。

完整读取新增 `reference_training_cancellation.py`、`reference_history.py`、`training-cancellation.js`、取消 Service fixture 与 suite；读取所有生产差异、`training.js`、训练应用层／原 start／runtime，以及共享 history 的 Task 批准／取消调用方。核对原 `perf_temporal.client`、`ExperimentWorkflow`、`ClusterAdapter` 与 `LocalTrainingAdapter` 的真实执行、取消、lookup／poll、fence 和 executor 所有权。其余清单项按实际差异及相关上下文检查；前片发布补记仅属其精确旧候选，不作为本片成功证据。

## 结构与所有权结论

- **共享历史算法有真实复用。** `reference_history.find_signal_event` 的 AST 与基线 `reference_task_runtime.py` 中原函数完全相同；保留单 payload、converter 解码、canonical SHA、分页和超时行为。生产消费者是 `reference_task_approval.py:205`、`reference_task_cancellation.py:136`、`reference_training_cancellation.py:172`。训练取消直接依赖共享机械算法，不依赖 Task creation／submission 语义；没有新增通用事件框架或兼容转发层。
- **runtime 的提取集中同一领域观察。** `reference_training_runtime.observe` 由同文件 `_status` 和 `reference_training_cancellation.stop_status` 两处实际消费。两者均先经 `lookup` 核完整原输入和固定 run；取消 owner 另核原 start memo。观察函数统一核 Status／Outcome 的 binding 并保留原负结果，未成为新的进度状态机。
- **原 start 身份继续归 `_Submission`。** `reference_training_cancellation.py:23–31` 复用原 registration、intent／receipt、execution／home／project 身份及冻结 spec；新意图 `:53–55` 仅引用 start SHA、run、request ID、reason 和 actor，不复制多 MiB manifest。该私有复用位于同一 reference 进程实现层，能避免第二套 start 归属算法；当前没有实证理由改成新的继承体系、公共 identity 框架或额外 wrapper。
- **单次取消与外部执行仍各归原 owner。** `:129–168` 在已核原 run 上局部包装原 client 的 query／signal，原 client 继续验证 binding／构造 CancelRequest；包装只核冻结值、保存 attempt 和加入独立操作 SHA。原始 reason 不混入标记。完整原 spec 以临时文件供原 loader 读取，不重写当前实验原件。`run` 在有 attempt 后只走 history reconciliation，缺事件或 NOT_FOUND 保留未知；closed 回执不制造取消确认。
- **没有第二调度器、实验账本或停止权威。** 新文件只写取消 intent／attempt／receipt，未调用 runner、`fence_and_lookup`、`cancel_job_group` 或批准流程。`stop_status` 调原 `load_adapter`／`lookup_job`／`poll_job`，只读并核本地 fence binding，独立返回 control、executor observation 和 fence；原 `CANCEL_UNCONFIRMED` 不被本地 `CANCELLED` 覆盖。adapter 选择沿原 factory，没有具体类分支。
- **页面拆分有具体局部所有权理由。** `training-cancellation.js` 虽只有 `training.js` 一个生产调用文件，但封装完整取消确认、稳定 request ID、独立停止观察与异步寿命；对外仅 element／setSubmission。详情 reader 失败不销毁这个面板，提交回执决定启用。复用现有 api／ui，未引入表单框架或全局状态树；selected、sequence、stopSequence 分别隔离项目／详情／操作的迟到回复，sending／observing 防同次重复发送／观察。该拆分承担独立生命周期，不是为了增加文件数的 pass-through。
- **CLI／HTTP 保持薄入口。** 两者共用 `training.cancel`／`cancellation`／`resume_cancel`／`stop_status`；revision 短事务只覆盖本地 prepare，离开 DB 后才 dispatch／resume。原 `processes` 管理子进程及中断；文件锁覆盖同一 request 的远端行为且非阻塞，未在控制 DB 预留期间等待别人的 RPC。

## 防护与测试价值

本轮没有找到应删除的实证冗余 guard、assert、测试或 CI 接线。新增防护位于外部输入、持久身份和发送 owner：确认 run／SHA／revision 防错目标；reason／actor 防无效或冒用请求；intent、attempt、receipt 和孤儿 checkpoint 交叉校验防恢复时认领错操作；input／memo／binding 防同 ID 的不同原运行；closed status 防误记发送。status 按 receipt→attempt 读取，原 intent 首读缺失而看到子记录时再读一次，允许正常并发发布而仍拒绝真正孤儿。Linux／SDK 及 timeout 拒绝分别来自原 owner 的可用性和有界调用合同，离线 status 不加载可选 SDK 或执行器。

新增 suite 沿既有 prepared／start Service 基础，真实 SDK 编码和转换器覆盖信号 marker 与原 CancelRequest 解码，并在 signal 入口直接读取已保存 attempt，能够暴露提前发送、丢 ACK 后重发、外部同原因／错误 marker 被误认、固定 run／memo／binding 错配等静默错误。停止观察保留缺 job、QUEUED／RUNNING、负 control 与本地结果并存及只读原件；CLI／HTTP 用同一 recovery sequence 验未知退出码和查询退出码。现有 original-payload 测试仅更改 import，runtime fixture 补 SDK handle 的真实 id，start fixture 增加 main guard 供取消 fixture 复用；没有另建替身框架。CI 只将新 suite 注册到既有 Linux 分组一次，没有增加重复 job 或文案测试。

## 已核证据与限制

1. 原 `source-r1.log`／JSON 为源码四 suite **52 passed／130.40 秒**，只覆盖当时 cancellation／runtime／original-payload／architecture 源码检查。本轴未重复运行大 suite。
2. 本轴实际运行只读 identity 检查及 history AST 对照；tracked `git diff --check` 退出 0。该 diff-check 本身不覆盖未跟踪新文件，未据此宣称全部新文件格式检查成功。原 283 参考路径没有 tracked 改动。
3. 独立打开 r1 wheel、源码快照、当前源码和已安装目录，**568 个产品文件全部逐字相同**；wheel 的 576 个文件、wheel／安装两 RECORD（安装 581 行）逐项 SHA／长度核验通过；283 个参考文件与冻结 manifest 相等，direct_url 非 editable。wheel SHA256 `cc5802792c8127dd8fb7168c655ffde2a87b89534d4e2f6fa2f0507e1935374b`。这是包身份结论，不替代安装 suite 或真实运行。
4. 最终安装回归、原生 CPU 同 run 取消／history／executor、真实浏览器迟到／错误／双击／三视口、自身原模板审查和所有进程收尾仍待完整原件补核；发布 Git 对象、普通推送／精确远端 Ref 和本片自己的必要 CI 也未验。Windows 原生执行、GPU、模型质量／性能、批准／采用、baseline／runner／prepare 控制面及完整 C2 不在本片通过范围。

**首轮结构审查无阻断 finding。** 下一步补核本片最终候选和上述实际验收，发现实证问题再按原场景给最小修复；不因源码通过提前关闭 F9b3。

## 同片补核：r2 展示修正、r3 最终产品与已完成原件

本轮先重读总计划／交付和工作树变化，再检查实际文件及原始验收材料；未运行安装、suite、服务或浏览器。**结构结论保持通过，开放 0；66 项安装补测尚在运行，整片最终验收仍待该结果及最后静态记录。**

**产品身份。** 独立打开 r2 wheel、源码快照和已安装目录，568 产品逐字一致、wheel 576 行／安装 581 行两 RECORD 全部核验、283 参考哈希保持，非 editable。r1→r2 仅 `data/console/style.css` 和 `training.js` 两处产品变化；93 个 Python 测试文件在 r1／r2／当前工作树逐字一致。原 390 视口因缺 spec 的长错误路径溢出，修正仅在训练根节点增加 `training-workbench`，继承局部 `overflow-wrap: anywhere`，没有改变共享布局、操作 Interface 或异步状态。

随后本轴逐字检查发现当前 `reference_history.py` 比 r2 少一个 EOF 换行，与作者发来的完整新增文件 diff-check 修正相符，未将 r2 误记为最终源码。r3 wheel SHA **`11cc353a2b0812e9f06503105a5ca69dff1a305eb7321d6961c9d4bc93bbd878`**；独立逐项核 **568 产品在当前 src／r3 快照／wheel／安装目录全部相等，两 RECORD（576／581 行）及 283 冻结通过，非 editable**。r2→r3 唯一产品差异确为 `reference_history.py` 896→895B，旧字节恰等于新字节加一个 LF，AST 完全相同，其余 567 产品一致。当前 history SHA 为 `208d4ce9c4e1c3413ad1475eb695d413ef2e882f20a11e391615be8060feb527`。据此保留 r1 行为验收、r2 展示验收各自范围，无新增行为主张或无理由重跑大 suite。

**实际 CPU 与停止事实。** 阅读原 `native-r1.py`，并独立打开、解码四个完整 `*-history.json`，逐项核 summary 的 history SHA／事件数、第一事件完整 Experiment、原 start intent／memo SHA、固定 run／原 workflow ID、每 ID 的唯一列出 run、唯一 `request_cancel`、binding／reason／独立操作 SHA 与 attempt 的 signal SHA。四个 history 确实各只有一个取消信号；信号事件分别为 18／18／73／73。扣住 ACK 的 helper 先 await 真实 signal，再记录原 payload／attempt 并抛 UNAVAILABLE，原 unknown 记录、页面恢复所得 history 回执和唯一实际信号相符，不是伪造服务接收。未发送 prepared 的独立中断及后续一次继续也保留原 ID。

两个原 Outcome 为 CANCELLED，另外两个为 CANCEL_UNCONFIRMED；本轴从各 history 最终 payload 与四个原 stop-status 交叉核实，没有把后来的四个本地 executor CANCELLED 改写进原控制结果。四 job 均无 started；25 份准备原件的最终完整 SHA 与原清单全部相同。原 executor collection 沿 fence 只收集 CANCELLED，driver 未调用 run-local，故本证据支持 CPU 控制／恢复及零训练命令，不支持 GPU、模型质量／性能或真实远端停止结论。额外 closed 请求保持 already_closed／not_sent，且无 attempt。

**实际页面与展示。** 阅读 r1 `loss.js`／`continue.js`／`lifecycle.js` 及实际 argv、stdout、snapshot 和 HTTP 记录，确认错误 SHA／run 零 POST、双击只一次 POST，缺当前 spec 时仍可从原回执恢复已投递 unknown／继续未发送 prepared。三条迟到路径是原 request read→新 request、原停止观察→新 detail，以及真实已闭合 not_sent 回执→另一 project；路由先取得实际响应再延迟交付，并未伪造成功响应。r1 布局原失败 `width390 / scroll477` 保留。r2 `final.stdout` 在同一控制 state、同一缺 spec／取消记录上测得 1440／960／390 的 scrollWidth 均等于视口；390 未发送表单也相等。本轴实际查看三张最终截图，错误路径与 SHA 可换行，详情失败和独立取消区同时可读。r2 HTTP 记录没有 POST；页面唯一 console 错误对应被刻意移走 spec 的真实 HTTP400，并非宣称零错误。r3 与 r2 的全部展示产品逐字相同。

**自身原模板与收尾。** 核两个 composition 原输入、packet-index、实际 run stdin 和原 result：r1 的 24 完整文件／318,975B 与 r2 的 5 完整文件／50,537B 均按长度和 SHA 出现在实际 stdin；各自三项祖先／叶资源的完整 text 也在同一 stdin。原模板两次均 succeeded／CLI0，42.999 秒／23.219 秒，approve；原结果 SHA 分别为 `0798bcdd2ef80eb019652ac49c07df623ed086b00fc06ee1c3a15e4c7120163e` 与 `d6ef2f6be708840cd5104de77886f53af440894f9a8663b38fbdfa9f261dc415`。admission 保留用户授权 Codex 回退及原 Claude 超时理由，两回复均明确其静态范围，不冒称异后端、独立理解或全套测试成功。

原生三服务及 r2 web 的 cleanup、两个实际 browser close 均有原件；本轴另只读探测原 7233 和两个原 web 端口，三者均不监听。r3 `-P -S` 进程只按安装包文件位置加载 Ergora，先断言找不到 temporalio，实际读取原 closed 回执成功；已核原 driver／stdout／空 stderr。首个探针因错误纳入整个 site-packages 而断言失败的记录保留，其修正是验收装载范围，不是产品或 Windows OS 实测。

**安装与静态的精确未完范围。** r1 九 suite 收集 155 项，600.027 秒显式停止、status cancelled／-9，无全套成功摘要；本轴从 verbose 原日志独立核 89 条 PASSED（参数 nodeid 内含空格也按完整名称保留），没有 FAILED 行。`test-partition-r1.json` 的 66 项恰为 155 项减这 89 项，无重复或交叠，不能把取消的原 run 写成全套成功。r2 只补这 66 项，结果尚待送核。`static-r2.json` 记录当时 34 文件、228 本地链接、无坏链／机器路径标识，包含 tracked 和每个 untracked 的新增文件 diff-check；产品／测试／CI 20 路径组合 SHA `a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`。该记录之前／之后的文档状态变化不继承其精确文件哈希，最后报告与公开证据仍需最终静态补核。

## 最终本地出口补核：通过，开放 0

已补读最终计划／交付、原 `install-r2/regression-r2/result.json`、完整 verbose stdout、分区生成脚本、`static-r3.json` 和[公开证据](evidence/2026-11-14-training-cancellation.json)。最终 HEAD 仍为原基线，候选尚未提交；没有借前片发布或 CI 关闭本片。

**两轮安装分段完成。** r1 的 600.027 秒 cancelled／-9 和 89 条逐项 PASSED 原件保持。r2 实际 argv 恰选分区剩余的 66 个完整 nodeid，最终 status succeeded／returncode 0，wrapper 279.664 秒，原 pytest 摘要 **66 passed／278.86 秒**。本轴重新解析两个完整 verbose 日志，89／66 与分区清单分别逐项相等，二者互斥，合并恰覆盖原收集的 155 项，无重复、漏项或 FAILED 结果。93 个测试 Python 文件在 r1／r2／r3 源码快照和当前工作树逐字相同。因此接受该次受影响回归的分段覆盖；它不是单次 155 项全套成功，也不是全新 r3 包上的一次完整重跑。

**三个包的证据范围。** r1 承载初版行为、原 89 项通过及真实 CPU／交互；r2 仅改局部换行样式／训练根 class，承载三视口修复验收和剩余 66 项通过；最终 r3 只去掉共享 history 一个 EOF LF，AST 及另 567 产品相同，承载最终 568 产品／两 RECORD／283 冻结、当前源码逐字一致与实际 SDK-free 本地读取检查。各包完整 SHA 已在前文及公开证据保存。没有把 r1／r2 历史运行冒称为新的 r3 模型、训练或全套执行验收；纯格式差异不要求重复已通过的大回归。

**最终静态与公开证据。** `static-r3.json` 冻结当时 35 文件、239 本地 Markdown 链接，坏链／私有机器字符串为空，tracked 及全部 10 个 untracked 的新增文件 whitespace 检查均无 diagnostic。本轴按完整当前字节重算 20 个产品／测试／CI 路径，组合 SHA 仍为 **`a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`**，并独立重做 tracked 与逐个 untracked diff-check，全部通过。检查时相对该静态快照仅独立需求报告发生状态补记；本报告随后出口补记也仅属文档，不继承旧文档哈希。

公开 JSON 为 12,929B，SHA256 **`b1dcc3572ad74e43266b36bf865367b41591bbb3eff85d1fdea09dc8e6594478`**。本轴逐项核其 25 份私有原回执哈希，全部与原件相等；三包身份、四原 run 的 history／Outcome、两次自身原模板输入／结果和最终观察字段均与原件相符，原负 Outcome、390 失败、安装中断及 SDK-free 初次探针失败保留，没有扩大验收范围。原 CI 分组收集 returncode 0，实际摘要为 **351／1804 collected、1453 deselected**；仅证明接线和收集，不是 351 项执行通过。

**最终本地结构／维护性验收通过，开放 finding 0。** 本轴未发现还需修改的所有权、依赖方向、抽象、防护或测试问题；原先提出的共享算法机械迁移、runtime 两消费者、私有 start 身份复用、独立页面寿命、可见失败和必要持久验证均已按实际代码／原件核实。普通精确提交、推送／远端 Ref 和本片自己的必要 CI 尚待另核。本结论不关闭 F9b4、F9c／F9d、真实 B3、Windows OS 实测或完整 C2，不支持 GPU、模型质量／性能收益、批准／采用或真实外部停止成功主张。

## 精确发布补核：通过，自己的 CI 在途

固定产品提交为 **`fad53478c9261157b3016563b410b9d4b4d85b9d`**，唯一父提交确为基线 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`。本轴直接读取不可变 Git 对象：父→候选恰为 35 个改动路径，逐项完整字节数／SHA 与发布前 `static-r4.json` 全部相等；该静态清单 SHA256 为 `a969d1004cf84851050cdfc66ea7f1554a80cb40c4661401e9bf69b779ebbd60`。20 个产品／测试／CI 路径按 Git blob 重算的组合 SHA 仍为 `a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`，与本地通过候选一致。

另将原 r3 wheel 的全部 **568 个产品文件**逐字对照候选 Git blob，全部相等；283 个参考文件的候选字节与原冻结 manifest 相等。实际运行基线→候选的完整 `git diff --check`，退出 0、无 diagnostic，覆盖已进入该提交的新文件。当前工作树的 F9b4 计划、后续产品或状态补记没有用于判定本片候选身份。

已阅读 `commit.py` 与原 `commit-r1.json`、`push-r1.json`、`ref-r1.json`：提交成功记录是在完整 staged diff-check、35 个候选 blob 相等及提交后工作树 clean 的门槛通过后写出；普通 push 退出 0，目标仅为开发分支，原 argv 没有强推参数或 main 目标。保存的完整 Ref 原件退出 0、stderr 空，精确返回 `fad53478c9261157b3016563b410b9d4b4d85b9d refs/heads/refactor/architecture-foundations`。该 Ref 结论绑定记录当时的实际返回；本轴未另发远端 Git 请求，也未执行 Git 写操作。

**精确产品／普通发布／原完整 Ref 补核通过，结构轴开放 0。** 本片自己的 CI run **`43516776101`** 尚在途，仍待官方终态及必要 job／step 原件。此前本地 89＋66 分段、各包真实验收和前片 CI 均不能替代它。本轮只补本报告，未修改产品、安装、运行回归或启动服务。

## 自身 CI 终态补核：通过，开放 0

本轴独立读取已保存的[官方 run `43516776101`](https://github.com/626619403/Ergora/actions/runs/43516776101) HTML、同 run 的官方 UI job batch JSON 和八份最终 job HTML；重新解析原件，没有执行作者的汇总生成器或发起新的远端请求。候选仍固定为 **`fad53478c9261157b3016563b410b9d4b4d85b9d`**。run HTML 的 `currentPath` 属于该 run，`Status` 明确为 `Success`，完整 commit link 和分支均相符。10 份 HTTP 收据全部为 200，原请求／最终 URL 相等并精确属于该 run／job；独立按完整 body 重算的字节数与 SHA256 如下，均与原收据相等。

| 官方原件 | body 字节数 | SHA256 |
| --- | ---: | --- |
| run HTML r4 | 213321 | `5797f9dde953288c68eee2202a765302706491778dce84817deab2f1bc99b62c` |
| UI job batch r1 | 2715 | `d1fe852f62b76e44f89c2fe82a3e1ff27cc3fd8389d9d0afe766254fc500107f` |
| plan `132200612712` HTML r1 | 158860 | `6236cf129b9dbc59e5d757b233c6c2746c5c0e3a0d17e278d7fffcbd9733596b` |
| Linux group 0 `132200669532` HTML r2 | 162550 | `c9d43c02e07b6d058e25ef1bee3e8e62de37bb1d3699c9f58c5b1e4729a2dcde` |
| Linux group 1 `132200669631` HTML r2 | 162550 | `fc0dc499d85cdb8d746fa39aff5bba40a60c90a7d8e65315ca218dfb73d4e1df` |
| Linux group 2 `132200669629` HTML r2 | 162549 | `776f8262476cbf7545cabcd5e144fa493fc30894e00943e9146b14329266a7be` |
| Linux group 3 `132200669595` HTML r2 | 162550 | `d0bb911c767d9ce225771135bafcdc5c31eb1de878c5643ede9946d6338ae098` |
| Linux group 4 `132200669603` HTML r2 | 162550 | `719b57a96db257914d6ba0c39a88071189ae4eb12af96f453378fc8f340cd1df` |
| Linux group 5 `132200669480` HTML r2 | 162550 | `1012bc7cb533e3b23986dcabcd7e8a47488a3958ff2e70d7e4653bb95f3a0fd7` |
| Windows `132200669517` HTML r5 | 160131 | `ec328de6805941277f018fae3f1087269d5013c4e0e038f8f6442794e6f408d0` |

**矩阵与归属。** 从候选 Git blob 读取 `.github/workflows/portability.yml` 和 `scripts/ci/linux-groups.json`，未使用已有 F9b4 改动的工作树文件。候选含六个非空 Linux group、79 个不重复测试路径，取消 suite 只出现一次；workflow 为每组生成 Ubuntu／Python 3.11 job，另加 Windows／Python 3.12 `group all`。原 UI batch 的 `totalCount=8`、`hasMore=false`，八个唯一 ID／完整 job 名恰覆盖 plan、六个 Linux group 和该 Windows job，每个 href 精确属于本 run。`ci-ui-metadata-r1.json` 的投影和 source SHA 与该原 batch 相等；它记录当时进行中状态，仅用来确定 job 身份，终态另由最终 HTML 证明。

**八个 job 与三十个必要步骤。** 各最终 job HTML 的 `data-job-status` 均为 `completed`，选中 job 的原 header 均为 `succeeded`。plan 的 `Read explicit test groups` 一项、六个 Linux job 各自的 `Build and install wheel`／`Packaged reference identity`／`Native application regression`／`Upload regression observations` 四项，以及 Windows 同四项加 `Windows PowerShell 5.1 installer and upgrade`，共 **1＋6×4＋5＝30 项**；本轴逐项核唯一名称、`data-conclusion=success`、`data-job-completed`、非空开始／完成时间及时间顺序。每项原 `data-log-url` 均严格等于 `/626619403/Ergora/commit/` 加完整候选 SHA、对应 job ID 与原 step number，全部绑定本候选；没有借其他 run 或短 SHA 作归属。六个 Linux 的 Windows 专用步骤按原 workflow 条件 skipped，未计为必要成功步骤。其余实际 step 的结论均为 success，Windows 原回归／PowerShell 安装升级／上传的完成时间分别为 `22:23:09Z`／`22:23:57Z`／`22:23:58Z`，job header 为 `2026-11-13T22:24:02Z` succeeded。

`ci-terminal-r4.json` 为 13,357B，SHA256 **`05477637426f91920af8ec0640f01af394e65748fefadc307443d8376528210c`**；本轴另将其 run 身份、每 job sample／body SHA 与 30 项完整字段逐项对照上述原件，全部相等。该结论是保存的官方 UI HTML／JSON 对本候选的终态证明，支持本次 Linux／Windows CI 必要步骤通过；没有取得完整 step stdout 或下载 artifact archive，也不据此增加测试项数、训练、GPU、模型质量／性能或真实外部停止主张。原本地 89＋66 分段及 SDK-free 探针保留各自原范围。

**本轴所审 F9b3 结构／维护性及精确交付补核完成，开放 finding 0。** 原候选产品、发布／Ref、既有本地验收与本片自身必要 CI 的证据链现已完整；F9b4 及后续片仍按各自合同和候选验收。本轮仅更新本报告，未修改产品／测试／CI 或原验收材料，未安装、重跑 suite、启动服务或执行 Git 写操作。
