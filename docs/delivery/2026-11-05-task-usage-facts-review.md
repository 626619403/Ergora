# F5.2 冻结预算与原history用量事实：独立审查

日期：2026-11-05。审查者：`task_usage_review`，独立fresh-context代理；仅接收原始范围、基线、文件及实际证据，未继承实现对话。先读AGENTS、原diff、相邻调用与冻结workflow/contracts，再读[交付记录](2026-11-05-task-usage-facts.md)。本次仅写本报告，没有修改源码、提交、网络写或启动服务。

## 身份与范围

精确基线为`2c0ddbccd25dda66d971eadd6770b61877c83bb7`；审查对象为其上未提交工作树的F5.2增量：

- 生产仅`src/ergora/reference_task_reconciliation.py`，SHA256 `4d0e7e732b18382be82287b2d519122968daf086faf259b9ce0d817bbfc397c3`。
- 同所有者测试`tests/test_task_evidence_index.py`，SHA256 `78946df62394ab823b5f0a1f2f59fb4a9869383b78e0afc66f6174bc7840a2da`。
- README、`docs/USAGE.md`、`docs/architecture/current.md`及本片交付/计划的对应合同与状态。其他F5.1审查、提交和远端归档差异不计作本片行为或CI验收。
- 最终wheel SHA256 `17cd87edef513cce25df4546a2d031fa4c92c642fe69596d3af8853b2fbcbd07`；审查者独立重算350文件在源码、wheel、两份noneditable安装完全相同，283冻结reference与既有基线相同。AST类/函数集合保持原17项，无新增生产函数、文件、依赖或CI修改。

## 结论

需求符合性：本地通过。可维护性：通过。在上述源码、测试、公开合同和实际本地证据范围内无未解决finding；没有要求增加的守卫、抽象、测试框架或CI作业。

预算来自已由原创建/提交边界验证的冻结spec/profile。冻结workflow证实stage期限在dev_submit返回后建立，空poll后检查；work并发与批准/poll策略的描述符合实际代码，没有将其当成外部进程硬截止、总时长或费用预算。索引保留原闭合run、无后继run、原payload/context、FileAdapter和响应限额边界。

用量在原`jobs()`完整扫描内计算；重复同context调度保留event数而只计一个job，冲突仍拒绝。首终Timestamp及event引用支持缺失、反向和真实零跨度；未记录模型次数、token、费用及币种/来源保留null，没有从activity-start、重试attempt、产物正文或当前价格推估。旧inspect/对账不给统计容器，原jobs返回值、checkpoint摘要及输出字段保持。

新增控制流分别服务于索引模式隔离、首次事件取值、完整时间戳及反向时间事实；终态/完整history检查保证跨度计算前已有首终事件，无需增加重复断言。沿用原所有者比新增统计服务或持久账本更贴合本片范围。

## 检查与证据

核读私有`.ergora/checks/f5-task-usage-facts/`的实际命令、原日志、身份与验收脚本；没有重跑完整矩阵或安装。原基线8项新行为红例均因缺字段失败；实现后源码51项通过，包含31索引/用量、12原单payload及8架构用例。随后补的旧budget/usage不新增断言已由最终wheel的31项通过覆盖；旧external-status/对账两模板代表4项通过。均保留其实际范围，TestClient上游弃用warning不记成零warning。

新增8例覆盖冻结预算、各类事件及重复job计数、失败run无outcome、缺首/缺终/均缺时间戳、反向及真实零时间；沿用归属、history、字节限额、文件可信性和CLI/API反例。现有CI直接收集`tests`，无需另行接线；Windows沿用正式任务需Linux/WSL2的既定跳过边界。

三CLI与五ASGI GET（含错误run、跨项目各400）调用实际登记原生子进程及Temporal RPC。审查者另从已存SDK原history的event_type分类及首终纳秒Timestamp重算，并直接读取原冻结profile/request，核CLI/API一致：

|原运行|事件/调度/记录start/signal|dev_submit/job|配置work单元|服务跨度秒|
|---|---|---|---|---|
|repository-governance正常|329/40/40/1|7/7|2|6541.066190111|
|large-change正常|348/37/37/1|6/6|1|6629.486720524|
|repository-governance取消|112/11/11/1|1/1|2|113.910954298|

两个正常原结果仍REVIEW_READY，取消仍CANCEL_UNCONFIRMED；独立清理确认与执行结果分开，三run未知模型用量均null。已核`native-before.json == native-after-verified.json`，并再次只读重算现场139文件、两repo内容/refs/worktrees及SQLite的3claims/0active；三原history/outcome的前后检查保持。已核正式shutdown confirmed、两owned进程退出记录、数据库保留与最终offline状态，并现场确认四端口关闭、服务socket/PID标记不存在。

性能结构仍为一次history扫描加既有job/文件核验，没有新增RPC、history副本或逐event容器；新增固定计数及首终事件引用，dev_submit汇总复用原job的event列表。实际三CLI约1.74–1.93秒、ASGI约1.51–1.55秒，响应16672–33427字节；只代表本次112–348事件、1–7job的小规模运行。未测大history吞吐或峰值内存，不据此声称性能提升；1MiB响应仍不限制总IO/内存。

## 剩余验收

本报告通过本地实现与证据审查，不标记完整F5.2交付完成。F5.2精确提交、普通推送、实时远端、双OS CI及同片最终复核尚待实际结果；F5.1的精确CI保持独立身份。最终文档状态与链接应随归档再核，后续F5.3及完整F5/G0不在本次通过范围。

## 精确提交、归档与推送续核

2026-11-05续核：精确候选`bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`的唯一父提交为原基线`2c0ddbccd25dda66d971eadd6770b61877c83bb7`。独立核12文件实际Git范围与`staged-scope.json`逐文件SHA256完全一致；生产/测试仍仅原两文件，blob分别保持上述`4d0e7e…`/`78946d…`身份。其余为本片文档与前片终结归档，没有CI/依赖或后续F5.3生产变更。

审查者重新读取该精确提交的Git archive并与原wheel逐文件比较：350资源完全相同，wheel仍为`17cd87edef513cce25df4546a2d031fa4c92c642fe69596d3af8853b2fbcbd07`。核提交前最终静态命令exit0及原日志，10份文档内容SHA256全部匹配该提交，335本地链接/锚点无缺失，28条README命令parser通过；不将静态检查算作运行验收。

已核提交exit0、推送前后原stdout及推送exit0记录：远端从唯一父提交快进到候选，输出为`2c0ddbc..bb4e461`，没有forced-update。另于`2026-11-04T21:20:35Z`独立只读`git ls-remote`核GitHub的`refs/heads/refactor/architecture-foundations`，实时返回完整`bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`；复用既有RSA/CONNECT连接元数据，没有推送或修改Git配置。

精确提交、发行身份、最终静态与普通快进/实时远端续核通过，无新增finding。精确F5.2双OS CI尚未完成，仍待原HTML/JSON和同片最终复核；本次没有重跑重型套件、安装或服务，也不把F5.1 CI41911536059归作F5.2验收。当前后续状态文档变化不替代该精确提交身份。

## 精确CI与同片最终终结

2026-11-05最终续核：精确候选`bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`的[Portability CI41914631896](https://github.com/626619403/Ergora/actions/runs/41914631896)已成功。审查者独立解析已存官方actions/run/job HTML及job-groups，核6份原证据的字节数/SHA256与`ci-html-status.json`一致，完整commit/workflow链接、run ID、各selectedJobId和必要步骤的精确commit日志URL相互对应：

|环境|精确job|已完成且success的必要步骤|
|---|---|---|
|Ubuntu / Python3.11|[126870927405](https://github.com/626619403/Ergora/actions/runs/41914631896/job/126870927405)|Build and install wheel；Packaged reference identity；Native application regression|
|Windows / Python3.12|[126870927806](https://github.com/626619403/Ergora/actions/runs/41914631896/job/126870927806)|上述三步；Windows PowerShell 5.1 installer and upgrade|

两job未见failure/cancelled/timed_out步骤。另于`2026-11-04T21:30:48Z`独立只读GET官方精确run页面，实时Status仍为Success并链接完整候选及原workflow；`21:30:50Z`独立`ls-remote`再次确认远端目标分支仍为完整`bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`。

本次重新核该Git对象的唯一父提交、原生产/测试blob SHA256及350资源Git archive与原`17cd87…`wheel身份，全部保持。CI workflow相对父提交未变；精确CI补齐原有完整矩阵验收，不重算或混归前片结果，也不将必要步骤成功扩写为原HTML未提供的逐例计数。本次没有重跑矩阵、安装或服务，没有修改源码、提交或推送。

F5.2需求符合性、可维护性及同片最终交付审查全部通过，无未解决finding；前述精确CI待验项已关闭。本片可以关闭。当前工作树的F5.3新文件未纳入上述Git/包/CI身份或审查，完整F5/G0仍须按各自切片继续验收。
