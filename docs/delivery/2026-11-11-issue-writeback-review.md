# F7c-C1 独立评审

评审者：独立 fresh-context Agent `f7c_comment_writeback_review`；日期：2026-11-11。项目及文档根均为 Ergora。本轮是 W1 协议与 W2／W3 草稿的早期检查，不是完整 C1 通过声明。

## 输入、身份与范围

先读原始要求、AGENTS、[当前检查点](../PLAN.md)、[C1规格](../plans/2026-11-11-issue-writeback.md)、[F7规格](../plans/2026-11-11-project-trackers.md)和[定向研究](../research/2026-11-11-issue-writeback.md)，再检查实际差异及邻接所有者。使用 maintainable-project-delivery 的 independent-review 和 codebase-design 标准；未继承实现者的对话或判词。

原要求包括逐项目来源、低耦合 all-in-one 入口、原六阶段／候选批准／未知恢复、每大项实际自身模板及独立结构／冗余测试／性能审查、持续记账和普通交付。本片只实现原已导出 v7 候选的一条显式中性评论及当前原生观察；不增加调度器，也不以 marker、空列表或后来匹配将 unknown 升级为 acknowledged。

基线为 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7`。本轮精确审阅对象是忽略目录 `.ergora/checks/f7-writeback/paused-for-b1c-ci/manifest.json` 所列十文件，逐字取自其 files 目录；已逐项重算 SHA256、字节数并全部匹配。没有把暂时回退的 B1c live 产品当作 C1。后报 B1c 修正 `472ff60` 已推送、十文件恢复 live，不改变本轮封存身份；其后修改须另外复核。

|文件|本轮审阅 SHA256|
|---|---|
|src/ergora/issue_backends.py|d45a66005f3ad5d61ce420cd088c40505e4eed6b9ca916773562046683363d72|
|src/ergora/issue_writebacks.py（新）|35ae28ab1033fa7e37549d44992d87ebd88c2264b0f496619eb0a6377cc73862|
|src/ergora/state.py|e3e0e86da430023f63b9cae54a4cc89154e0bc7ba97691f91f8c496e0dc96ff9|
|src/ergora/backups.py|f8b4cb315dc068d35bbb3eaa9d0d15c227458cca97a54aab97f1a5e34dbcd933|
|src/ergora/cli.py|69f586cbe73aff6185601575d27a5092b1ee033f70f4c63032ee8936bca896a5|
|src/ergora/web.py|663c9390e7f5f0abac3fe76dedb2d1520a7b49ee3df394ef09f8b083dc8e47c5|
|src/ergora/data/components.json|7a671cb020d981e11982dfa3167b9484f3536b4b9c56093bd1d58a077a21c25f|
|tests/test_project_issues.py|6ac26774fccf0946e349732aef77355963c5dfbe771cf6cca79890a77e9e7adc|
|tests/test_state_migrations.py|8c87c6dd1165b0a8adc09ae5973f7bb5f9fb18332cfc6ae54de288ff8f459fe0|
|tests/test_issue_writebacks.py（新）|a314285e076c7c1e3d88b4c1ca9adcd954243bf2bfc0aad369502fa6069ae701|

另审三份本片 live 文档和上述基线中的 tasks、reference_task_creation／export、reference、issue_sources／snapshots、issues、projects、contracts、State／backup 调用契约。B1c 六文件修正及其评审不在范围内。

## 两轴结论

|轴|本轮结论|
|---|---|
|Spec compliance|要求修正：SP1、SP2 为开放 P2。W1 的既有运行仅证明其当时的协议候选；W2／W3 尚无完整运行验收。|
|Standards／maintainability|要求修正：ST1 为开放 P2，SP1 也涉及持久数据的不变量归属。其余本轮已读结构未发现实证的额外封装、厂商分派或第二调度器问题；性能与完整交付继续待验。|

## 开放 findings

### SP1／P2：正常加载和备份校验未核对意图与原快照的目标

位置：封存 issue_writebacks.py 第 51、80、262 行；发送路径第 198–216 行。`_record` 只将意图自身与摘要／scope／固定正文互核；`validate_storage` 只检查 snapshot SHA 的行存在，没有将其已验证 observation 的 issue_id、native_id 与 intent.source 比较。`_load` 同样只调用 `_record`。

实证：在纯内存 SQLite 中放入一份经既有 issue_sources.validate_snapshot 验证的合法 snapshot（工单 7／native 9001），再放入一个自身摘要、scope、正文一致的 prepared intent（同项目／provider／namespace，但指工单 8／native 9002，仍引用工单 7 的 snapshot SHA）。既有 issues.validate_storage 返回一份合法 snapshot，草稿 validate_storage 返回一份合法 writeback，`_load` 返回 prepared。该场景检验的是恢复数据的跨记录关联，正常 prepare 不会生成它。

后果：恢复数据可以保留原任务的合法 export 身份，却指向另一工单；send 只重核原 export 摘要及 intent 所指当前目标，未将它重新绑定原 v7 来源，因而不能保证只向任务冻结来源发送。

最小修正：由既有 snapshot_from_row 读回并验证原 snapshot，在本域加载／离线备份共用的校验处比较完整 source 路由及 native_id；发送前通过原 creation／show／export 所有者核对原 v7 来源和保存的引用，避免换成同项目另一份合法 snapshot 后仍漏过。用一个语义不一致的存储反例验证该关联，避免复制快照解析器或正式任务状态机。

状态：已通知实现者；对方后报已在 live 增加共享 snapshot 关联校验及原候选重核，尚未审阅修正字节或验证结果。

### SP2／P2：GitLab 缺必要可见性字段的响应仍可成为确认收据

位置：封存 issue_backends.py 第 254–260 行；issue_writebacks.py 第 156–166 行。

GitLab 的 system、internal 使用 `document.get(key, False)`，缺字段等同于明确 false。纯内存解析一个含合法 note 身份、body、author、时间，但缺 system／internal 的完整 JSON，`_comment` 返回 ordinary=true；随后 `_matched_response` 对该 201 投影也校验通过。

这与定向研究及本片声明的严格支持合同不符：必须能核实普通 note 的 system=false／internal=false，缺必要字段应保持 unsupported／unknown。请求默认发普通 note 不能替代成功响应所声明的确认条件。

最小修正：在原 GitLab Adapter 内要求这两个必要字段存在且为布尔值；普通 note 需明确 false。confidential 是否可选按实际支持合同处理。用一个缺必要标识的响应反例证明不能产生确认，不必逐字段增加同构测试。

状态：已通知实现者；对方后报已在 live 要求 system／internal 存在且为 bool，尚待精确字节及反例复核。

### ST1／P2：旧描述符测试仍固定为只读操作，确定性违背当前候选

位置：封存 tests/test_project_issues.py 第 212 行；components.json 中 GitHub／GitLab tracker operations。

旧断言要求两个 tracker 的 operations 精确等于 `["issue.show"]`；同一封存候选实际已为两者列出五个操作，包含四个 writeback 入口。静态读取实际 JSON 即可确定该断言为假，不需运行 HTTP。当前十文件候选因此不能继承早先 W1 的 20 项通过结论。

最小修正：将该既有合同断言更新到本片真实支持的操作，保留 manual 和只读来源的必要区别；不要增加一个仅证明旧合同已删除的测试。随后重跑受影响读取／回写入口测试。

状态：已通知实现者；对方后报已在 live 更新为当前操作的必要包含关系，尚待精确字节及测试结果复核。

## 已检查的结构及行为

- IssueBackend 的两个 Adapter 真实承担不同原生路径、字段及分页事实，registry 位于本族。上层回写用例不按 provider 分派；扩展 `_request` 复用原完整读取、无 redirect、固定认证上下文及单 POST 传输，没有引入 SDK 默认写重试。
- issue_writebacks 有 CLI、HTTP 两个实际生产消费者；backup 另消费其离线校验。scope／固定正文／记录解析／attempt／收据匹配是本域内聚算法，未发现为单一转发而新增的包装层。State 继续持有 DDL、事务及旧 writer fence。
- 草稿先在 BEGIN IMMEDIATE 内核项目修订、竞争状态并保存 attempt，退出提交后才 POST。并发后来的发送者看到已有 attempt 即返回；进程在 attempt 后、POST 前退出也会保持 unknown。此处结论来自代码路径，尚非进程／并发实跑证明。
- observe 仅追加观察、读回当前资源或一页，匹配仅列 matching_ids；`proves_original_attempt` 固定 false，结果写入路径不从观察升级。status 只读本地记录。没有 marker 确认、自动重发、close／merge 或 claim／候选批准写入。
- `_body` 仅使用原身份及固定文案，字符串换行、mentions、特殊引用字符被转义；不复制工单正文或模型指令，不声称本地 branch 已远端发布。入口沿原 Web 同源／请求头保护，confirm 严格布尔；凭据只在 backend 内存中取外部环境变量。
- 现有新增 W1 测试覆盖真实协议路径、固定凭据、单次 POST／丢响应、redirect、续页来源及错误目标，未发现应删除的同构测试群。迁移草稿沿既有历史独立 fixture 扩展 v2→v3 与 writer fence，仍待运行。
- 网络单页最多 100 项、响应最多 1 MiB；没有后台扫描。20 秒是底层 I/O timeout，不是已测总墙钟期限。尚无 W2／W3 的耗时、锁竞争或安装后性能证据，不能据静态检查给性能通过。

## 实际检查与待验

本评审已做：十文件 manifest 字节／SHA256 比对、逐项 baseline diff、新文件及邻接调用契约检查、九份 Python 的 AST 与一份 JSON 解析、上述两个纯内存行为反例和描述符静态比较。未创建 State 目录、未执行 HTTP／loopback 请求、未使用凭据、未安装、未运行模型、未改产品／测试／计划、未 commit／push。一次只读复现脚本误用 JSON 顶层键后已更正；其失败不被计作验收。

已核 W1 原件目录 `.ergora/checks/f7-writeback/w1/`：result.json 记录源码导入的 pytest 命令、exit 0、命令 16.354 秒；stdout 为 20 passed in 14.30s，stderr 为空。该原件不含源文件哈希，也早于整片 W2／W3 变动；本轮没有重跑，不能据它宣称当前十文件安装／完整 C1 通过。

完整出口仍需：SP1／SP2／ST1 修复及精确字节复核；W2／W3 两协议的原 v7 候选、prepare／send／status／observe CLI 与受保护 HTTP 旅程；原 ID／候选／任务／批准／claim 保持；attempt-before-send、进程退出／重启／并发、已创建丢响应／部分201、主体／绑定／项目修订漂移、人工复制／编辑／删除／空页／分页不确定性的反例；迁移／writer fence／含记录备份恢复；固定非 editable 安装、两 RECORD／283 冻结；使用文档；实际自身模板的精确输入／回执／读取范围；完整两轴独立复核及本片自己的精确提交、普通推送、必要双 OS CI。真实账号写入不属于默认验收。

实现者另报后续将发送条件改为“关键点核操作者当前 expected revision、冻结 tracker binding 必须一致”，允许无关 Agent 配置修订，export 摘要只绑定稳定原收据事实，准备时 configuration SHA 留作历史。该方向及同步计划属于后续候选，未纳入本轮封存草稿结论；需随新 manifest、实际调用差异和验证证据一起复核。

## 源码 r1 同片复核

本节是上述早期状态的后续复核，仍未作完整 C1 交付通过声明。基线为 `472ff60a6d27c91ef5d5285f959e61d3b935341d`；精确输入为 `.ergora/checks/f7-writeback/review-code-r1/manifest.json` 及其 files。manifest 实算 SHA256 为 `787edb8f0eabbce2f4fa0b745dc3410e7e6d63ba51ae3c6de674d48e61e60a2b`，十文件字节数／SHA 全部相符，检查当时也与 live 相等；后续 live 变化不自动进入本结论。

相对早期十文件，本轮四份变化身份如下；另外六份与前表完全相同。

|文件|源码 r1 SHA256|
|---|---|
|src/ergora/issue_backends.py|ee88455800e260b7f81bf2da8ed693f0740e02e0cd7a1b8bd2975ee913967c0b|
|src/ergora/issue_writebacks.py|397bd9061f7dddbbc3d9a47cff70972f526929a52efa00a29e83f72e81870221|
|tests/test_project_issues.py|8ca21443a4f37b95d456eed22eb0d020b5629645509a0c64dde89a4f2cac9bfa|
|tests/test_issue_writebacks.py|426a359bc2b8d846e96830911150a57d6729b1bcce90c3ea695b4bb5f9969dac|

|原 finding|复核结论与证据|
|---|---|
|SP1／P2|关闭。issue_writebacks 第 80 行的 `_load` 经既有 snapshot_from_row 验证原 snapshot，并比较完整 source 路由、native_id 和 snapshot SHA；prepare／status／离线 backup 复用该处。第 110 行的 `_candidate` 通过原 creation／show／export_status 重核 v7 来源及完整 task facts；send 比较其结果，另一份同项目合法 snapshot 不能替代原任务来源。第 187 行测试同时覆盖同 SHA 错路由的 load／backup 拒绝、换合法 snapshot 的 send 拒绝。评审者纯内存重放原 SP1 反例，load 与 backup 校验均报 original source snapshot，不再接受。|
|SP2／P2|关闭。GitLab Adapter 第 254 行要求 system／internal 存在且为 bool，noteable ID／iid 也核整数；create 继续只接受 ordinary。第 216 行真实 HTTP 反例在已创建后省略两标识，保留 unknown、无 result。评审者纯内存重放原缺标识对象，原 Adapter 已拒绝。|
|ST1／P2|关闭。原只读测试第 215 行改为必要包含 issue.show，不再将可扩展的目录固定为旧单项；源码五 suite 记录已包含描述符变化后的读取用例。|

本轮两轴：Spec 的上述三个开放问题均已关闭；当前产品及测试的 Standards 未新增实证 finding。**完整 Spec／交付验收仍待**下述观察反例、安装结果、实际自身模板与最终完整候选；这里的“无新增”只指本轮十文件和已核证据。

### 新增实现、guards 与测试检查

已逐字检查新增 `_source`、`_candidate` 及所有修改调用。它们集中原来源投影和原候选事实比较，分别被 load／prepare／send 等本域路径复用，没有复制快照 parser、原 export 状态机或引入 provider 分派。来源关联、必要字段及原候选重核均保护已复现的持久化／外部响应风险。网络预检和三个原任务读取不在 SQLite 写事务内，attempt 提交前仍重核当前 expected revision；观察仍不写原 result。

发送条件现为当前操作者 expected revision，加冻结 tracker binding／source／creation／export facts。完整 configuration SHA 仅保留准备历史，export facts 排除查询时变化的 project_revision。这与低耦合要求一致：与本评论无关的 Agent 配置变化不改变冻结意图，tracker、actor、来源及原候选变化仍被拒绝。原 owners 的身份和批准仍是依据；没有从新配置重编译候选。

新增测试跨 seam 的区分成立：native 层检验实际 HTTP 请求与固定凭据，应用层检验 durable attempt／重启不重发，原生合同集成另检验未经替换的三个 task 读取入口。没有建议删除这些不同责任的覆盖。writer fixture 的本地响应锁保护其共享响应缓冲；产品的单次发送竞争仍由实际 SQLite 事务负责。两个中断窗口使用 SystemExit，是受控中断而非实际 SIGKILL。

性能观察：一次 prepare 的原生网络是 actor＋目标 GET；一次首次 send 是同样两次预检＋至多一次 POST，status 不联网，observe 是 actor＋一个资源或一页 GET。三个原 task 读取保持在现有独立进程 owners 中；backup 对保存记录逐项复核。已见运行没有新增轮询／扫描或长写事务证据；整套 55.78 秒和集成 13.10 秒包含夹具、解释器、原任务发布及 Git 工作，不能当作单次回写延迟或容量基准。尚无证据要求新增缓存或替换这些既有所有者。

### 本轮实际核到的证据与未验范围

- `.ergora/checks/f7-writeback/w2-source-r2/` 的 argv 明确为五个源码 suite，exit 0，命令 59.121 秒；stdout 为 99 passed／1 skipped in 55.78s，stderr 为空。原 task 的三个读取 Interface 在该组受控，后来加入的原生导出测试不在这 99 项中。
- `.ergora/checks/f7-writeback/native-export-r1/` 的单项源码命令 exit 0，命令 13.820 秒，stdout 为 1 passed in 13.10s，stderr 为空。已读该测试和既有 fixture：实际发布 v7、原提交／claim、真实 Git commit／条件分支导出与租约释放；随后新 CLI 进程经真实 creation／show／export_status 执行 prepare／send／repeat／offline status。仅 Temporal SDK 接口受控，不是新的真实六阶段或模型推理验收。
- 评审者本轮只做身份／diff／AST／JSON、原件与调用检查及两个纯内存复核，没有运行 HTTP、模型、安装或产品测试，也未改产品／测试／计划、commit／push。
- 已读 package-identity.json 所报 wheel `2a050ba5e30376635abbd928e27350f406f5e543807a791562ffb63b680c8a77`、446 包文件、451／622 两 RECORD、283 冻结等身份；本轮没有独立重核全包和两 RECORD。首个 no-isolation 缺 setuptools 构建失败仍是失败；标准隔离构建、新安装八 suite 当时仍在进行，不提前称通过。

关键观察证据尚缺：r1 的 lost-response 用例在唯一真实匹配出现后先追加副本再 observe，删除后只按 ID 读 404；因此尚未实跑“唯一同作者全文匹配仍 unknown”和“完整空页仍 unknown”。这不是当前产品 finding，也不能称现有测试已有覆盖。实现者已同意在同一个现有用例内补两处观察断言，并在当前安装回归结束后仅复跑受影响的两个 provider；产品字节保持，后续测试身份及结果另核。

实际自身模板、最终安装结果、公开使用／架构与计划的完整最终状态、本片自己的精确提交／普通推送／必要双 OS CI 仍待后续交付。上述已关闭 finding 不替代这些出口。

## 自身首审判词及 r2 修正的中间复核

已读 `.ergora/checks/f7-writeback/self-review-r1/review.md`、原 runs/result.json、protocol/result.json，以及相邻 self-review-r1.json、read-audit.json。原 run 为 `b1a49a24ce944b12955bdc0eead2089c`，267.609 秒，**decision=request-changes**；运行技术状态 succeeded 不表示 approve。原 result 实算 SHA256 `9c71e8ff172f2f8bee49f2ec882aa25dbafef2d4b4b774cbc0a813ac76181698`，与审计一致，两 result 语义相等，review.md 与原 response 完全相等。

本评审还独立读取 scope 和原 stdout JSONL：五份资源的所有成功 UTF-8 页均与冻结 scope 原字节相符，连续到 next_offset=null；candidate 为十二个唯一页，另外四资源各一页，三次重复页已区分，未见失败的已完成 MCP 调用。candidate 实算 272480 字节／SHA256 `84b679e7b98d2cf7f28683e83a63b0af7c2d8d9ba2d2d237e1e553c94900afe1`；十五份完整附件中十份产品／测试逐字等于 review-code-r1。原 native stdout SHA256 `fa80ba35ce9890629ea339aa1d77ed2b5d9755b6e6ddf56dda57028b2f23c06b` 与审计一致。四个所属采样进程无存活是作者清理记录的范围，不扩写为无遗漏的全系统进程证明。

首审的两项 P2 由本评审独立确认成立，登记为 SP3／SP4，区别于已关闭的 SP1／SP2：

|finding|独立判断、当前修正与状态|
|---|---|
|SP3／P2，opaque 名称的 Markdown 字符未完全中和|r1 的 JSON 引号不能关闭 Markdown；合法 Git 分支 agent/__candidate__ 仍含可生效的 strong 标记。当前 `_body.literal` 对 JSON 引号／反斜线以外的 ASCII 标点转成 Unicode 转义，只作用于 opaque 值，保留固定正文、SHA code span 和 marker。该修正静态足够；原协议用例和原生导出集成均改用合法含下划线的 branch，并检查其字面量，不增加独立镜像测试。实际 r2 结果及最终字节身份待核。|
|SP4／P2，result 保存缺当前修订及原 attempt 检查点|冻结计划要求在持久化关键点重核操作者当前 expected revision；r1 在 POST 期间合法 bind 使 revision 前进后仍无条件写 acknowledged。当前在原 result 事务内 BEGIN IMMEDIATE、共用 `_load`、核 current expected revision 及同一 attempt 后才保存；网络不在写事务中，也没有恢复历史完整配置 SHA 依赖。检查失败保留已提交 attempt 为 unknown，后续新 revision 的 send 也不重发。该修正静态足够；新测试在同一真实 POST handler 中合法 bind 后验证上述行为，等待 r2 实跑。|

评审者只用内存 SQLite 和受控原 task／backend ports 独立重放“POST 期间 revision 1→2”的同一场景，没有 HTTP：r1 得到 acknowledged／result_saved=true；当前源码抛 revision changed，状态 unknown／attempt_saved=true／result_saved=false，新 revision 再 send 仍只有一次受控 create 调用。opaque branch 在 r1 正文中保持活动 Markdown 字符，当前正文已无该字面量。这是对可达场景的只读反证，不作为真实 HTTP、安装或全套测试证明。

本轮检查当时的 live 临时身份为 issue_writebacks.py `03223fd6cbf1ba0bb382f0c33ff3577737ce808afaf88b0f88393b5d0e6775bb`（18329 B）、test_issue_writebacks.py `5f867a0f206c61e860cd805ca434f7c5a3fd21d35d6c600f6ed34a3ea62c3aa3`（24961 B）。最终 manifest 尚未交付，不能把后来 live 变化自动纳入本结论。未见这两处修正引入新的产品／结构问题；SP3／SP4 暂记“源码修正足够、验收待核”，不提前关闭完整 Spec。

原丢响应用例已补唯一同作者全文匹配仍 unknown、完整空列表仍 unknown 两处观察，保持 proves_original_attempt=false；其运行结果尚待本轮 r2，未借旧 r1 称已有覆盖。

### 安装范围与剩余出口

已核 r1 installed-validation.json 及原 stdout：独立安装八 suite 使用 `-I`，exit 0，driver 521.851 秒，结果 **188 passed／1 skipped in 520.74s**；随后 reference verify exit 0。这是旧 r1 包和当时已收集测试的结果，不是上述两产品修正及新增观察／revision 测试的 r2 验收。r2 构建／安装、受影响两 suite、后续自身聚焦复核及最终完整 manifest／文档仍待；不要求在没有新故障时重复全部旧八 suite，也不借旧结果声称 r2 全套通过。

首审的 request-changes 原判词继续保留。当前两轴状态：上述两个新 Spec 问题已有足够的最小源码修正、实际验收待核；Standards 未新增实证 finding。最终安装身份、实际自身后补范围、最终完整独立复核及自己的精确 Git／推送／必要 CI 仍未完成。

## 最终28文件完整两轴复核与本地出口

本轮精确基线仍为 `472ff60a6d27c91ef5d5285f959e61d3b935341d`。完整输入是 `.ergora/checks/f7-writeback/full-review-r2/manifest.json` 及其 files，manifest 实算 SHA256 为 `cda56dade5318ac09c64cb7b04ec3836d13ae5aa955601d5a604af970b66a9e4`：28件、771195字节，逐件大小／SHA256均独立重算相符。包括7份产品／目录、3份测试和18份公开文档／证据；新文件全文、既有文件相对基线的变更及相关既存所有者均已检查，未只核 r1→r2 小差异。9份 Python AST和相应JSON解析通过。下一片 `docs/research/2026-11-11-issue-label-writeback.md` 明确不在本候选及判词内。

最终十份产品／测试均与前述已逐项检查的源码身份一致，r2仅将回写用例和原测试模块更新到已登记的 `03223fd6…`／`5f867a0f…`。原 creation／show／export、projects、来源／snapshot、migration／backup 等相邻所有者的合同继续作为判断依据；没有把前片472ff60自己的CI移作C1证据。

### Spec：开放0；SP1–SP4已关闭

|finding|最终处置与可核证据|
|---|---|
|SP1／P2，保存来源可嫁接|保持关闭。最终 `_load` 将完整source／native ID重新绑定既有snapshot parser，prepare／send经原task owners核原v7来源与完整候选事实；相应产品／测试字节与源码r1已核修正相同，r2包也逐字包含该修正。|
|SP2／P2，GitLab缺可见性字段仍确认|保持关闭。最终Adapter要求system／internal存在且严格为bool，普通note明确为false；原缺字段反例及真实协议用例仍拒绝确认。|
|SP3／P2，opaque名称仍是活动Markdown|关闭。最终literal对JSON引号／反斜线以外的ASCII标点统一Unicode转义；现有两provider用例使用合法下划线分支，原生v7发布／Git导出后的新CLI集成也使用合法 `agent/__source-candidate__` 并核转义正文。它们均进入当前安装52项；不是只用非法Git分支或纯字符串镜像测试关闭。|
|SP4／P2，result缺持久化检查点|关闭。最终result短事务BEGIN IMMEDIATE后重用 `_load`、核当前expected revision和精确原attempt，再保存result。当前两provider测试在真实POST handler内调用原 `projects.bind` 合法推进修订，实际创建后拒绝旧修订确认、保留attempt／unknown／无result；新revision重复send没有第二次请求。该用例已在r2安装包实跑通过，前述评审者纯内存r1／当前对照仍为独立辅助反证。|

先前缺少的两个观察反例已补在同一原丢响应用例内，并随当前安装包通过：唯一同作者／全文匹配只列出原生ID，仍unknown且 `proves_original_attempt=false`；完整空页也仍unknown且同字段为false。随后复制、编辑、删除／404和重复send的原断言保留，POST总数仍为1。observe没有写result或接纳marker的路径，status保持离线；没有通过更换write ID绕过原逻辑scope。

当前操作者expected revision与冻结tracker／source／creation／export事实的分工符合本片已明确的合同。发送前无关Agent修订可在当前revision下继续；POST期间修订变化则不保存确认。prepare时configuration SHA保留历史，未重新引入全配置冻结依赖。旧首审正文规则仅属于尚未发布的C1草稿；基线schema v2没有C1记录，原r1夹具不构成r2历史记录迁移／unknown升级验收。

### Standards：开放0；ST1与状态P3已关闭

ST1／P2的旧只读描述符断言保持关闭。最终目录扩展由原backend族拥有；CLI与受保护HTTP共用同一回写用例，backup消费正常加载校验，State仍拥有DDL、事务与旧writer fence。来源和候选核验复用既有所有者，没有复制原journal／批准状态机、在上层按provider分派、引入通用副作用管理器、第二调度器或后台恢复队列。

局部 `_source`／`_candidate`／`_load` 分别集中实际重复消费的来源投影、原候选事实和持久记录校验，私有范围合适。严格响应、原snapshot／attempt关联、完整读取与事务检查守住已经复现的边界；未见应删除的无依据guard。协议、应用和原生owner集成测试跨不同seam，现有重叠有具体责任差异；新增观察直接补原用例、修订变化使用原合法bind，没有堆叠同构fixture。定向研究说明两SDK默认可能重试POST，继续复用现有stdlib传输的选择有本片实际成本和行为依据，没有新增依赖或为未来多平台需求提前搭框架。

网络等待仍在SQLite写事务之外。prepare为actor＋目标两次GET，首次send为同类两次GET＋至多一次POST，status零网络，observe为actor＋一个资源或一页GET；单页100项、单响应1MiB，不隐含全库扫描。20秒仍只是I/O timeout，不是实测墙钟上限。已有测试耗时包含夹具、进程和真实Git工作，不能作为用户操作延迟或容量基准；未见实际性能退化证据要求缓存、替换原task所有者或新增基准工程。

最终封存文档仍有几处当前状态落后于后文已完成的验证，记为本片 **ST2／P3**：C1 plan的W2／W3仍称原生衔接待验，delivery当前检查点仍称没有安装包通过，总计划／F7表仍称安装与自身审查中。已通知实现者，仅修正四份文档的当前状态行，历史分轮／失败记录未改。评审者逐diff复核后关闭ST2；未借模型判词覆盖这些后补字节。四份后补精确身份如下，构成上述28件封存候选之外的状态delta：

|文件|字节|后补SHA256|
|---|---:|---|
|docs/plans/2026-11-11-issue-writeback.md|6382|6103b86655de97bdfc8bd8a38f1a0f5d6cee6ac29fe5f5de682db90ad240c2f1|
|docs/delivery/2026-11-11-issue-writeback.md|11279|b520d68eda797e3841a0ea6d060c724a0d2ed39b8bb552e71e5bcd3e5c8abc0c|
|docs/plans/2026-11-01-all-in-one.md|74491|1cc724eda6be492bf1ba8052c781c2db9b4f627a74a30949b7e8c40f6a14a9fe|
|docs/plans/2026-11-11-project-trackers.md|7226|ede9bd4f4f680b558608855f12b1bcccdc75b536293ff40aa3302ace5554631c|

这些当前行已统一为r2受影响安装52项与聚焦自身approve通过、完整独立／精确Git与远端及本提交CI待核；没有把旧轮次写成当前结果。其余24件当时仍与封存文件相等。本报告本节是审查结果追加，未递归冒称其已包含于上述manifest或模型附件。

### 最终r2安装身份与实际结果的独立核验

评审者只读原wheel、安装目录、源码和基线Git归档，独立重算确认：wheel SHA256 `e75d130e88966a1c89145fd246e5acd3c8ac7a8c70f8b20433a7e8e08173c46d`；446份package文件在源码／wheel／安装中逐字相等。wheel RECORD451行中450项有hash，安装RECORD455行中454项有hash，每个非空SHA256和大小均核过，RECORD自身按格式无hash；本次no-compile记录没有混用r1的622行。direct_url为本地wheel归档而非editable。283份reference文件各自符合原manifest，且与472ff60基线逐字相同，reference-manifest本身也相同。对两轮wheel另作逐文件比较，r1→r2恰只变 `ergora/issue_writebacks.py`，其余445份包文件相等。

已直接核 `r2/installed-validation.json` 与原stdout／stderr：隔离解释器 `-I` 的完整回写及架构两suite退出0，**52 passed in 52.16s**，命令54.191秒；stdout实算SHA256 `7e46d6fc3baec9c540cea1611cdd1431d32b4496b82b26edbf59f44078381959`，stderr为空。reference verify退出0，0.368秒，原输出PASS／version2.2／283／runtime_started=false，stdout SHA256 `da70d6dabedefe16352c4fee8c19df7f7da751f820148dd908260e94528ef0b7`，stderr为空。评审者没有重新安装或运行这些检查。

r1的188 passed／1 skipped／520.74秒和源码99项／原生owner集成1项仍按各自候选及控制面保留，不拼成r2新全套。受影响包只有一份产品变化，当前完整回写与架构已重验，没有新故障要求重跑未受影响旧八suite。公开acceptance投影准确区分这些范围、受控Temporal SDK／SystemExit、首构建失败及无真实tracker写入。

### 实际自身聚焦审查的原始链路

最终聚焦run `0bd80ee0a3f8445c8db7fd6c32748cea`、Codex／gpt-6.1-sol／high、103.928秒的原判词确为 **approve**。评审者独立重算manifest目录树digest `d193269d55ef4b44863fdf23dbe4f5934c9d12fd5a181375536dc70ef0d656a0`；prepared与actual input的13件文件逐字相等，input树digest为 `255479d50f74d25674392ee220a498de54c03eb7734d866c545d8bb090517f23`。manifest与input中的composition／9件asset相同，两个definition对象树与其digest相符；与内置模板相比仅有声明过的版本／引用、证据资源和材料预算变化，四份原指令／skill保持字节。

完整task与所选leaf prompt重建得到实际prompt，prompt／request／admission／native stdin身份一致；五份scope资产与实际input中的对应原文件相等。再从原stdout JSONL独立逐件提取已完成的MCP list／read：四份小资源各一页、92386字节candidate四个唯一UTF8页（24000／24000／24000／20386），均连续精确到next_offset=null；0重复、0失败的已完成调用。八份完整附件逐件符合raw-evidence-index；四份相关产品／测试逐字等于最终manifest，既存projects等于原源码，prior-self-review附件逐字等于首审原response。两份计划／交付附件保持其当时版本，后补公开文档由本独立完整审查覆盖。

candidate SHA256为 `54474ac7b12534c5034d381c6fb5337bc0a1e27f6b9cef31f39bbc2a0cab01f4`，原stdout SHA256为 `c57272d85f077f933f0352b4efc043ba5c598753fec95699580a9a3a42d3d29b`；原run result实算SHA256 `fbe3956084951d11031089f039d293e981852c464449d0cd1d685deeb239290b`，run／protocol／另存original-result语义相同，review.md与原response逐字相等。公开自身证据的两轮run字段／read-audit／原response均与私有原件一致，仅去除两项私有路径并增加明确的采样进程范围说明。

首审267.609秒request-changes及其15份完整附件／272480字节、原分页重建结论继续保留；没有把技术succeeded当approve，也没有把同一Codex的两个上下文称作成功跨后端独立证明。4个所属采样进程无存活只保留作者原采样清理范围，不扩为全系统／所有短命进程证明。

### 文档、静态范围与最终判词

已检查使用说明、后端支持范围、架构／身份、F7及总计划、C1研究／交付和两份公开证据；前片B1c的追加只记录其自己的472ff60精确交付终态，旧6a7e9a1失败及首非终态样本保留。C1使用说明给出prepare／send／offline status／observe的CLI与HTTP入口，说明当前actor、冻结来源、唯一逻辑操作、unknown不接纳匹配／空页、剩余读后竞态、单页／字节／I/O限制及外部执行备份范围，未把本地Git导出称远端发布。

原 `static-r2/result.json` 的28件大小／SHA与最终manifest逐项相等，记录381本地链接、6个载入秘密值检查、issues为空、空白检查通过和无新增依赖。评审者另独立提取并检查381个本地Markdown目标，全部存在；`git diff --check`也通过。该静态结果不覆盖外链、anchor、Mermaid渲染或真实服务兼容，评审者没有额外读取凭据或对外／loopback发请求。

**最终独立两轴：Spec开放0，Standards开放0；SP1／SP2／SP3／SP4、ST1／ST2均关闭，C1完整候选的本地实现／验证与独立审查出口通过。** 本轮评审只追加本报告，未修改产品／测试／计划、安装、执行模型／产品测试、联网、commit或push。本片精确ready／Git对象、普通提交／推送、独立同SHA远端Ref及本提交自己的必要双OS CI仍须后续原件终核，当前不能称C1精确交付、完整F7或整个项目完成。

模板比较的精确口径补充：内置模板原有的三份指令／skill逐字保持；第四份 `candidate-evidence/SKILL.md` 是新增的证据读取资源，其r1／r2字节相同，并已核manifest／input／scope与实际读取页相等。上文“四份原指令／skill保持字节”不表示内置模板原先已有该第四资源。
