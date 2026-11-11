# F7c-C3b 交付记录

实现基线`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`；[本片计划](../plans/2026-11-11-existing-review-association.md)与[研究](../research/2026-11-11-existing-review-association.md)。C3a已普通提交／推送、精确Git／作者Ref通过，自己的CI43042210053双OS七必要步骤／原评审终核已通过，精确交付终结。本片可以独立实现，不在C3a CI终态前推送新提交，也不把它的包／模型／CI验收借给本片。

## R0／R1 立片

研究新增GET0；12份原官方body缓存完整性已核。新能力仅为操作者指定已有PR／MR的本地context关联，统一provider读取合同、当前原candidate事实、本地不可变记录和离线backup。当前开始R1源码；尚未运行本片产品、安装或模型验证。

沿原`IssueBackend`的path／native映射和有界GET模式扩展指定review读取；公共JSON格式放原contracts/data schema，保存和离线验证留在`issues`，State按既有迁移机制加本域表。没有新正式调度器、远端send生命周期、上层provider分派或provider SDK。所有真实SaaS写入、草稿创建与分支发布继续在本片外。


## R1 原生读取与初次源码检查

沿原IssueBackend接入指定PR／MR的统一读取Interface及本族path／native投影；公共candidate-review-context-v1合同区分number／iid、global ID、node_id、作者、完整正文与可空diff版本事实。GitHub拒绝fork／null repo及端点身份不符；GitLab使用已见数字project ID，核project／source／target身份。保持完整1MiB读取、无redirect／重试和白名单投影。

首轮用保留C3a环境、显式PYTHONPATH读取当前源码，原生review、候选观察及架构共**48 passed／29.17秒**（命令30.30秒）。这是State4／完整保存验证之前的读取范围，不称本片安装包验收。最初private描述登记脚本误取operations的`*`键，在写文件前KeyError；后按原tracker键完成登记，无产品运行或远端写入。

## R2／R3 持久与迁移源码

本地link_review复用原v7 task/candidate和只读观察，要求当前local／remote head精确相等及base可见；分别保留原base／当前base／review响应base与diff版本事实。另GET原source核native ID。网络不持写锁，最终短事务重核revision及scope，单候选槽唯一、重复目标返回原历史且fresh=false，另一目标冲突。review_link与backup共用原文预算、schema、canonical身份／scope、source快照和同repo/candidate/path校验，离线不需要token、Git或task运行。

State4只增candidate_review_links；沿原迁移／预备份／事务回滚，将全部旧表和新表writer fence同时升版。固定历史v3测试布局独立写出，覆盖迁移前已开的旧writer。旧版本备份按原user_version处理。CLI的review-link／review-link-show和受保护HTTP两入口已接上，F7d页面仍另片。

第二轮源码检查**77 passed／6 failed／54.23秒**（命令54.82秒）。六失败均是新增测试写法：unknown模拟抛OSError而非原backend的ValueError、预算用例理由本身超出2000字符、offline CLI参数重复issue；各覆盖两provider。只修测试后同六项补验**6 passed／5.77秒**（命令6.26秒），产品无因此修改；不称一次最终83项全通过。并发同槽／网络期间独立writer、漂移拒绝、相同loader／backup损坏拒绝已在77项范围内。原source-r2四文件manifest保持，追加其运行期间未再变更源码的六文件hash说明；后续runner覆盖完整实际改动范围。

R4继续扩展原真实v7发布／原run／本地Git导出→fresh CLI旅程至两provider，并核保存后的新进程离线读和原claim／导出／writeback保持；只控制Temporal SDK／结果，不借此称六阶段真实模型或真实平台验收。发行、实际自身和新fresh-context完整独立审查待验。


## R4 实际v7／Git衔接与旧库备份

扩展原fresh CLI旅程至GitHub与GitLab：真实v7创建／原run／本地bare候选与显式export、原comment／GitHub label、C3a观察后，指定已有review保存。两provider均按五次GET核原task／snapshot绑定，fresh CLI离线show相同完整record；执行目录／Git文件／SDK调用、claim和原export／writeback保持。只有Temporal SDK／结果端口受控，HTTP／State／任务所有者／Git／CLI是真实实现，**2 passed**。不称真实六阶段模型、真实托管平台／账号或原生Windows正式执行验收。

同轮新增旧库备份检查因测试局部变量backups遮住模块，八项在调用前UnboundLocalError失败；测试改用清晰module别名，产品未改，原八项补验**8 passed／7.74秒**（命令8.16秒）。v0–v3各delete／WAL模式先离线完整backup／verify而不升级，再升级并核原行／额外对象／资产与精确预迁移备份保持。前同轮总结果为2通过／8测试错误、58.46秒；历史失败保持，不称一次最终10项全通过。

README、日常手册、格式与架构已同步实际入口、单候选唯一／历史重试、三种base与diff事实、State4和离线备份，页面／自动创建仍另片。R1–R4源码实现与比例验证完成；R5开始新隔离wheel构建／非editable安装、完整RECORD／283身份及受影响套件。模型与fresh-context完整独立尚未运行，不据源码检查提前结案。


## R5 r1隔离发行与审查启动

标准`python -I -m build --installer=uv --wheel`隔离构建成功35.92秒。新venv创建后，首次依赖下载在pypi.org的pyyaml元数据请求超时、安装退出2／44.98秒；原日志保持。这不是产品测试或wheel构建失败。沿同一全新venv，用uv离线缓存并固定保留前环境的依赖版本，安装当前本片wheel成功5.19秒，无网络重试或editable安装。

r1 wheel SHA `fb78f40363adaad20f52e5c97a9745d5e74d95f00492211928bd438034a5bc9e`；447个source／wheel／installed包文件逐字相同，两RECORD452／457及283冻结通过。八个受影响安装suite正在运行：review关联、迁移、backup、原writeback、候选观察、旧context映射、provider读取与架构；不是复跑无关完整仓库。

实际内置结构审查模板已启动，17份完整源码／真实消费者／schema／测试／规格／交付／研究／使用手册471,672原字节，保留原提示／Skill／祖先资源，仅追加完整证据Skill和局部修订／资料预算。其冻结输入不包含本段后来状态或最终公开投影，不据启动称模型已完整读取或approve。新fresh-context独立评审同时开始25文件冻结候选，清单SHA `ad07358657fc072d6953a4d975a74355ca7ab3521c5928b05a1469dfa6869e09`；按AIHERO code-review分别核Spec／Standards与冗余test／CI／guard，尚未作通过结论。


## R5 r1受影响安装验收

八个受影响安装suite **189 passed／1 skipped／197.60秒**（命令199.69秒）通过；安装身份为上节r1包，原source／wheel／installed及两RECORD／283一致。reference verify退出0／0.27秒。最慢调用是两provider实际v7→Git导出→fresh CLI组合旅程；这是loopback本地运行成本，不是平台延迟或容量测量。新增和旧相关操作共同在同一安装环境验收；先前源码失败与补验仍保持实际原候选，不用这次结果抹去。

[结构化投影](evidence/2026-11-11-existing-review-association-acceptance.json)记录精确包／检查摘要。实际自身与独立评审仍进行，待其finding／读取审计与最终公开内容核验后关闭R5；本片尚未提交／推送或完成自己的CI。


## R5 实际自身首轮超时与收窄

原run `e61508dd3a094fb5bccbcaa167c206d5`为timed_out／604.71秒，CLI退出1，**没有审查判词**。17份原文件471,672字节加完整文件名／围栏后的实际附件472,872字节，SHA `0aeda01f8788771c05db59cf33c0c41020217a4cdff83c9256952809506dc1d9`。native流显示四份祖先指令／Skill各已读到null，candidate连续页仅完成至144,000／472,872，尚未完整；不能据四scope或成功工具调用称全部完整读取／approve。MCP失败0；所属四个采样进程退出后无存活。原manifest／prepared／实际输入／native流和超时诊断保留。

收窄下一轮至九份完整核心owner／schema／测试／规格／本片记录，约132KB，不截取半份文件，不改变产品或放宽规则。完整CLI／HTTP／usage及后来公开记账仍由新独立完整候选核，不能借聚焦模型的判词覆盖未附内容。凭据继续外部LINGZHI_API_KEY、实际Codex回退，前Claude失败及非成功双后端范围保持。


## R5 聚焦自身与独立两项补证

聚焦内置模板run `51020a1029d94bd1b8cacf78aa38a7c4`实际Codex/gpt-6.1-sol/high，**546.83秒／approve**。九份完整原文件132,918字节、实际附件133,647字节，SHA `78fad38a124a1df2402382a53c8f714f497be149c9f0fc02a4f815c8fcadb1ec`。离线重建manifest→prepared→actual input→prompt/stdin→全部五scope连续UTF8页至null→原结果均相符，MCP失败0；原结果SHA `407c061d997611e0acf8e62ba61ad5230f5c95d0babbbca6b40c78ed2cc4b7a4`，四个所属采样进程无存活。模型只审九份冻结核心文件，没有执行测试或覆盖完整CLI／HTTP／backup实现、usage及最终公开文档；后两处整数schema修正和HTTP测试补证也不借该先前判词。首轮17文件超时仍保留，不称重复全量成功或不同后端独立成功。token用量保留后端自报原量，缓存是输入子集，不重复累计或推算费用。

新fresh-context独立首审提出SP1／P3验收范围及ST1／P3格式一致性；无已证产品P2。SP1是原真实v7旅程只核fresh CLI，另一HTTP测试还受控task ports，不应写成两者都只控制SDK。复用r1安装套件保留的两provider真实v7／Git／CLI已存记录，无token且原provider服务已结束，实际TestClient离线GET分别200／0.19秒及200／0.12秒，全文record相等，逻辑DB保持。另把同样一次HTTP GET加进原真实v7测试，不新建重复旅程；原受控HTTP用例的范围单独保持。

ST1是新schema两个版本只有const:1，普通writer仍生成整数，但重算hash的float1.0可被loader接受。对未变r1安装loader、真实已存来源记录的仅内存row先真实red（accepted_float_versions=true、断言失败，不修改持久行）；最小产品修正仅两字段增加type:integer。沿既有corruption参数增加版本float保护，不加新断言框架。r1包和189项保留其原范围；r2新包只复验该schema／load、相邻HTTP／native和架构，之后原独立同片复核SP1／ST1。


## R5 r2最小修正后安装复验

新标准隔离构建26.55秒、全新非editable环境离线安装5.17秒。r2 wheel SHA `f39eabc3ecf596a1d82a06b2bf2c663f8e0160ec744450eed77969ca678b0169`；447个source／wheel／installed文件相同，两RECORD452／457及283冻结通过。逐个包文件比较r1→r2，产品只变candidate-review-context-v1.json的两处type:integer，未重建或修改其他产品Module；README发行元数据保持。

受影响安装复验 **68 passed／101.06秒**（命令102.96秒）：完整关联suite、两provider原v7／实际Git／fresh CLI且新增同record的HTTP离线GET、架构。原float版本corruption检查经shared loader／backup拒绝，正常保存及旧记录仍过；HTTP后执行目录／Git／SDK调用、原claim／export／评论保持。reference verify退出0／0.27秒。不因两字段修正重复原八suite189项；r1结果、原模型九文件判词及全部历史失败仍各保其身份和范围。

初次超时部分读取的补充离线核对确认：所有完成页字节／SHA／offset与原scope相符，candidate先读45,000字节后从0以24,000页重读，重叠字节一致，实际连续覆盖到144,000；四祖先完整。一个私有诊断曾把跨旧终点的重读误判成不合法duplicate，修正诊断为已核字节的重叠合并后完成，没有产品／模型重跑或扩大原timeout为成功。

SP1／ST1由原独立评审复核，最终公开候选／静态与R6精确交付继续；截至本节不提前称本片结案。


## R5 最后手册与可选Web测试修正

相邻INTEGRATIONS手册仍描述早期F7a“仅普通issue单GET、无comment/writeback”，本片只更新其工单来源段，列清现有原生Interface、来源任务、候选回写／观察／本地review关联和未支持操作，不改变产品。最终完整公开候选因此为28文件。

独立追加ST2／P3：扩展的真实v7组合测试在末尾直接import可选FastAPI，dev+temporal且无web时会模块缺失。按同模块HTTP用例约定，在该组合用例开头加importorskip('fastapi')；dev已有httpx。不新增测试或依赖，不为测试要求改变产品配置。r2原68项包含web，保持其原范围；最后测试入口skip一行由独立静态复核，不借此声称重新运行68项。

首次静态28文件之前的27文件检查在审查报告五个相对文件链接上发现冒号行号不是GitHub文件路径；改为文件#L行号后重核。该失败只涉及文档链接，不是产品／安装失败，不宣称验证外部URL或锚点。


## R5 完整独立出口

同片新fresh-context独立评审完成完整28文件及后补范围，Spec／Standards开放0／0，SP1真实HTTP补证、ST1整数格式和ST2可选Web测试约定均关闭，无新增产品finding。独立重核r2包／两RECORD／283、68项原输出、真实HTTP保留记录、聚焦自身五scope全文与原approve；最后skip一行仅静态核，不冒称重跑68。完整CLI／HTTP／usage／INTEGRATIONS与最后公开记账由独立覆盖，不借聚焦模型扩大范围。

[独立报告](2026-11-11-existing-review-association-review.md)终核快照SHA `5fa2dbf03d11791a7edc1c6e7bcd93b6245e6c58272769fc9707b5f97227d7b2`；后续精确交付状态追加不冒充该快照。最终静态与ready冻结随后进行；R6普通提交／推送、精确Git／remote和本提交自己的CI仍待核，不以C3a终态替代。


最后公开静态28文件／367本地链接／六个已加载秘密值、JSON及diff空白检查issue0；只核相对文件目标存在，不宣称锚点、外部URL或Mermaid渲染。本片本地出口完成，R6精确交付继续。原静态五链接失败保留，报告现为标准文件#L链接。
