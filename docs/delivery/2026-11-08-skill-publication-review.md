# AC1.1：Skill完整树发布独立审查

日期：2026-11-08。评审者：fresh-context独立代理`skill_publication_review`；未参与实现。收到原始S-1问题、验收要求、固定基线/八文件清单及实际验证证据后，从差异、源码与调用方分别检查需求和可维护性。已读项目`AGENTS.md`、总计划、`maintainable-project-delivery`及其独立审查规则、`codebase-design`，并全文读本片新[交付记录](2026-11-08-skill-publication.md)。

**需求符合性（Spec）通过，可维护性（Standards）通过；本次范围内两轴均无finding。** S-1的本地修复及独立审查出口满足；普通候选提交/推送、精确双OS CI和同片交付终结仍待完成。本结论不接替AC0自身CI，也不关闭AC1.2的Q-1或证明新增Agent组合已实现。

## 范围和身份

基线、实际HEAD均为`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`，分支`refactor/architecture-foundations`。原范围为7个tracked变更及1个新增交付记录；检查完整tracked diff与受影响上下文，生产完整读取`skill_assets.py`，测试完整读取`test_skills_evaluation.py`。另外只读追踪`State.connect/file_lock`、`skills`兼容出口、CLI/Web/GEPA导入、评价/采用和备份的相关调用。

冻结清单位于本地忽略目录`.ergora/checks/ac1-skill-publication/`：`review-scope.json`为1,427字节，SHA256 `4bb8ddea1fbdde412742a9f13e5928cf6fd0d13e8658b37e87ac6f7a8c15cce8`；`review-tracked.diff`为24,110字节，SHA256 `ecf9c7488592efdde78cca1c63c175b14172af91df395dbcf3c5010b31b1c27d`。独立重算八文件身份全部匹配，实际完整tracked diff逐字等于记录。

|文件|字节|SHA256|
|---|---:|---|
|`docs/INTEGRATIONS.md`|15391|`791d78269f4c1f5747074109306985fc88679f4e21cd1ca4f6e8e7627a9ae46b`|
|`docs/PLAN.md`|68672|`f6319b4a1d52ad2b43d9b427fb1717ffc557c5b1dc2d470780d576e47d36c389`|
|`docs/architecture/current.md`|33597|`6fea7c454dea5d146e0ba4408221f15913e7abea70a0395f99581c4a83c46a5d`|
|`docs/delivery/2026-11-08-agent-composition-design-review.md`|11811|`b3108a8cb44d23e27e935e66b965f80e2001671df798b21a18568090823fbce0`|
|`docs/delivery/2026-11-08-skill-publication.md`|5186|`11c037528b0395e10c0bcc3f3a4aadb10cfc9b1d9449f5a507566e2b3f05c17b`|
|`docs/plans/2026-11-08-agent-composition.md`|10983|`d2e2d60b1091f972c7e72a25cde31c64abac965c6061b0eacbc50c67b64a4da2`|
|`src/ergora/skill_assets.py`|9066|`3e0916b53225a50ac80d3c6183e5bbd7c0c3505b44336b92cdbbcdeb4f0faf8d`|
|`tests/test_skills_evaluation.py`|21758|`f8d5474d413a0a546ed022495fc921c99555a7e8756affb6e21c75d6071efe3c`|

前片[AC0设计审查](2026-11-08-agent-composition-design-review.md)新增内容仅为其原审查者的状态追加。独立比较确认基线中原8,958字节全文仍为当前文件的完整前缀；追加明确将随后AC1代码排除，并保留AC0精确CI pending，未将旧审查当本片通过。

## 需求符合性

范围内无发现。[资产实现](../../src/ergora/skill_assets.py)第87–126行保持原公开interface、内容/执行位digest、最终`skills/project/digest/name`路径、metadata和首次baseline/后续候选语义；评价、采用、回退及冻结参考内容未改。

|验收要求|独立判断与证据|
|---|---|
|只登记完整且核过身份的树|复制到最终digest目录下独立暂存树，先核来源稳定性和metadata，再进入发布；最终树只能由已核副本rename得到，或已有树重新核digest后重用。不存在仅凭`exists()`登记的路径。|
|未登记残树恢复，有效树保持|锁内先查版本并核现有最终树；digest不符且未登记时才删除残树并rename。已核有效树跳过替换；新增回归检查资源及mtime，独立进程探针也核完整树mtime保持。|
|同digest真实跨进程幂等|复用原生`file_lock`，锁文件归同project/digest；锁覆盖核树、发布、版本/头/事件事务提交。四个独立解释器同步导入的检查独立复跑通过，结果文档相同且三个持久集合各一项。不同digest首次导入仍由`BEGIN IMMEDIATE`串行决定baseline。|
|复制、发布、登记中断可重试|五个独立子进程在指定实际操作后直接`os._exit(73)`，绕过Python清理；重开真实State后前四种无部分登记，提交后回执丢失保留唯一原登记。全部重试后完整可读、版本/head/事件各一项。详情见下表。|
|已登记损坏明确拒绝且不覆盖|已登记内容修改或缺失均在发布前报错；测试核DB文档及损坏/缺失原状保持。`get`及Agent/evaluator原身份拒绝保留，未把重复导入变成证据修复操作。|
|范围、兼容和记录|未新增依赖、公共函数、表、CI或存储框架；未改实际用户库。手册和架构明确新增恢复语义，计划保留实现/验证/独立审查/精确交付的不同状态。六阶段及Linux/Windows支持范围保持。|

独立进程探针以`PYTHONPATH=src`使用当前源码和本片既有Python环境，仅操作本片`independent-review/process-fixtures/`：

|进程直接退出位置|重开后已登记数|最终树是否已发布|重试结果|
|---|---:|---|---|
|暂存复制只写出`SKILL.md`|0|否|完整发布，三个持久集合各1项|
|rename完成后|0|是|核后登记，原完整树mtime保持|
|版本INSERT后、提交前|0|是|SQLite回滚后重试，原完整树mtime保持|
|事件INSERT后、提交前|0|是|版本/头/事件一起回滚，重试后各1项|
|commit后、返回回执前|1|是|原DB内容与mtime保持，不重复登记或事件|

探针脚本`independent-review/probe.py`的SHA256为`fe88c7275af006d223fee3af3b1aa707cefd31c9e84743befa670df76ce2aade`，原始结果为同目录`probe-result.json`，记录时间为2026-11-08 13:16:09 UTC。真实进程退出会留下`.import-*`暂存目录，重试不消费这些残留；本次未引入或要求额外自动垃圾回收机制。

## 可维护性及测试/CI成本

范围内无发现。完整树身份和发布归已有`skill_assets` Module，CLI/Web和GEPA继续使用同一Interface，兼容`skills`出口保持。发布可靠性集中在现有所有者，调用者不承担额外排序或恢复协议；没有为一个用例新增浅层包装、公共helper或通用发布框架。

新增控制流均对应持久化可达状态：同父目录暂存保证rename同文件系统；同digest文件锁协调文件发布与DB登记；核现有树防止旧残树被误认完整；“已登记则拒绝替换”保护原证据；只有未登记且不匹配时才删除，保留完整孤立树。`State.connect`已提供提交/回滚，复用它并在退出后再释放文件锁即可，不需要另一份事务抽象。来源稳定性、父版本同名及metadata检查沿用原位置和语义，没有新增无关参数守卫。

新增四个测试函数经参数化形成六例，分别保护旧残树/有效树保持、两个中断窗口、两种已登记损坏和真实多进程竞争。断言集中在公开资产Interface、文件内容和持久版本/head/event结果，故障注入只控制操作窗口；它们没有重复原评价/采用检查。源码定向、非editable发行包及本次额外退出探针证明不同层面的事实；本次探针保留为忽略证据，没有加入永久测试/CI。现有CI不变，未发现本片需要删除的冗余测试或作业。

成本判断仅限源码：初次导入从原两次copy变成一次copy加同文件系统rename，重导入增加对已有树的身份读取；锁内包含最终树哈希和必要残树删除，SQLite写事务没有模型、网络或服务等待。既有10 MB/500文件限制约束正常树扫描；没有新增性能测量，因此不声称吞吐、延迟或跨平台性能收益，也不由小夹具推导任意并发容量。

## 原始验证和审查限制

已读原`red-command.json/red.log`：旧实现三例真实失败，分别为残树登记后`get`拒绝，以及两种已登记损坏未拒绝。原源码定向记录为Python3.11.15/pytest9.2.0，32 passed/5 GEPA可选依赖skip；原新独立noneditable包Skill全文件18 passed/零skip。默认隔离build及新环境安装均exit0；前一`--no-isolation`缺setuptools的exit1单独保留。没有把这些作者记录写成本评审重新执行的全量结果。

本评审实际另做：

- 独立重算源码、wheel与实际安装包352个文件，逐一字节相同；wheel SHA256为`56c5ab1a6baaf31deb3e30927d4900ce8f7f1be5e7d0633fa7c71d09793dd89d`，确认使用独立site-packages。
- 用`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`及既有wheel环境只复跑本片六例：`6 passed in 7.54s`，exit0；命令和日志为`independent-review/pytest-commands.json`、`pytest-r2.log`。首轮因评审者未先建basetemp父目录而出现6个setup错误、exit1，未触达夹具/产品；该错误与正确复跑分别记录。
- 执行上表五个真实进程退出/恢复探针，全部断言通过，无真实模型或服务调用。
- 分别从当前源码和非editable安装包执行`ergora reference verify`，均283 PASS、`runtime_started=false`。
- 复用现有静态检查逻辑，仅将输出写入独立证据目录，独立重算原范围6份Markdown的180个本地文件/锚点，缺失0；30条README命令通过当前源码parser。`git diff --check`通过。该静态计数不包含本报告及随后状态追加。

本次仅新增本报告及获准的本片忽略证据，未修改生产/测试/依赖/CI、旧审查文字、实际用户库或Git/外部状态；未安装依赖、运行重型全套、真实模型/GPU/服务或原生Windows。进程退出探针不证明断电持久性，也不证明恶意同用户隔离、特殊文件系统或跨机器并发支持。

未解决源码阻塞finding为0。主代理仍需归档本审查和S-1处置、刷新包含报告的最终scope/文档静态，完成普通精确候选提交推送、该候选双OS必要CI和同片远端终核后，才能登记完整AC1.1交付完成；AC0独立收口及Q-1后续切片分别保持原责任。

## AC1.1普通候选身份及状态归档复核

2026-11-08，同一评审者固定读取Git候选`bf99bd47220572fd721546a2eeb5b1b2739a57b5`，未使用随后AC1.2工作树作为本片源码。**普通候选身份、最终静态及审查后状态归档通过；本候选自身精确CI和独立即时远端终结仍待核对。** 范围内无新增Spec或Standards finding。

候选唯一父为`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`，恰改11文件。全部候选blob的bytes/SHA与本地`final-scope.json`一致；清单1,974字节，SHA256 `02c8b5316bddc24d65a62fbde9af2a3fff6568f0470dd4373719a822b1cd1a63`。`final-tracked.diff`只捕获原已跟踪的9文件，为36,600字节，SHA256 `be42d27a037ac725cce0a91dd1bdffdfb1f215d20f5f1e6adfaae70e707c59da`，逐字等于这9文件的实际Git对象差异；两个新增文件为本报告和本片交付记录，均另从候选对象核对。

生产`skill_assets.py`和测试`test_skills_evaluation.py`继续保持首轮表内完整SHA，INTEGRATIONS和当前架构也保持首轮身份。独立将候选内352个包文件逐字对照原`56c5ab1a6baaf31deb3e30927d4900ce8f7f1be5e7d0633fa7c71d09793dd89d` wheel及实际非editable安装，全部相同；没有将新工作树测试或别的候选结果沿用到本片。本报告在候选中为原10,062字节，SHA256仍为`80f353029175fa9b4b8518ddb85bd95544b005c947c1265ea3c977442b23bdb4`，原文保持。

其余文档差异逐项核为本片新审查/探针与静态结果归档、S-1作者回应、AC0原独立审查者的完整终结及计划状态更新。AC0原审查文字仅追加；共享源码报告只改S-1作者处置并追加AC0交付状态，原finding和Q-1保持。候选内本片交付记录再次全文读取；它明确保留原build环境失败、评审setup错误、硬退出残留暂存目录及断电/Windows/性能未验范围。AC0的`42483036401`及其独立终结仅作为AC0状态依据，不作为本候选CI通过。

从固定Git对象重新解析9份Markdown，328个本地文件/锚点缺失为0；30条候选README命令通过parser，所用安装包已确认逐字等于候选源码。最终`static-documents.json`的9文档集合及全部摘要与候选相同，文件3,565字节，SHA256 `3289995616f4f1ca13c8c938fa067ee729db0994e69aa9631f7b94c9802d4535`。`git diff --check 0f8e2a9… bf99bd4…`通过。上述计数不包含本节追加，没有重跑已通过且源码身份不变的行为检查。

已读主代理原push、`ls-remote` stdout/stderr及命令退出记录：普通push exit0，远端从0f8前进到完整bf99候选，`push-remote-identity.json`记录于2026-11-08 13:24:09.847526 UTC，远端同SHA。本节尚未另作独立即时远端查询，也没有确认AC1.1自身CI结果；取得该候选双OS实际必要步骤后再进行同片终结。唯一公开写入为本报告追加，其余检查只读固定对象和既有证据。

## AC1.1精确CI、独立远端与完整终结

2026-11-08，同一评审者继续固定`bf99bd47220572fd721546a2eeb5b1b2739a57b5`，再次从Git对象核唯一父0f8及11文件集合、全部blob的bytes/SHA，仍与上述final-scope相同；候选中原报告全文保持。**需求符合性、可维护性、普通候选身份、最终静态、该候选自身双OS必要CI及独立即时远端核对均通过；AC1.1可登记完整完成，无新增finding或未解决交付阻塞项。** 上节CI和远端pending由本节实际证据关闭。

本次直接解析官方run/job原HTML，并对照固定候选的`.github/workflows/portability.yml`，没有只采用主代理汇总JSON或总体Success。`ci-html-status.json`列出的6份来源逐一重算bytes/SHA，全部一致；三个关键原页面为：

|来源|字节|SHA256|
|---|---:|---|
|`ci-run-latest.html`|157493|`196a1379227e20686598e011b343d0a9f4ab56c9228e1feb2075c81fe8cef331`|
|`ci-job-128744183496.html`|160122|`5c7179528f422358e744f969ba55eccd6d6e3d125b2727d8e044a544f166df76`|
|`ci-job-128744183793.html`|162041|`1b63257f86ca2e049e15cc8b1b7205c62fdbdac0976f401006fab1931dd86cb1`|

[Portability 42484784168](https://github.com/626619403/Ergora/actions/runs/42484784168)的原run页实际含完整bf99候选commit链接、对应workflow链接及Success；run选择记录同时绑定该完整候选、run ID与workflow。两个job分别核自己的`selectedJobId`、平台/Python名称、步骤完成标记和成功日志URL，结果为：

|必要步骤|[Windows / Python 3.12 · 128744183496](https://github.com/626619403/Ergora/actions/runs/42484784168/job/128744183496)|[Ubuntu / Python 3.11 · 128744183793](https://github.com/626619403/Ergora/actions/runs/42484784168/job/128744183793)|
|---|---|---|
|4 · Build and install wheel|success|success|
|5 · Packaged reference identity|success|success|
|6 · Native application regression|success|success|
|7 · Windows PowerShell 5.1 installer and upgrade|success|skipped，符合候选的Windows条件|

每个必要成功步骤的原日志URL均精确等于`/626619403/Ergora/commit/bf99bd47220572fd721546a2eeb5b1b2739a57b5/checks/<对应job>/logs/<对应步骤号>`；Windows全部10项success，Ubuntu9项success且仅Windows专用项skipped，无失败、取消或超时。已读原`verify-ci.py`，另用独立只读解析核上述事实，未执行它的JSON写入动作；没有重跑CI、重型测试或逐条下载全部控制台日志。

随后按既有`push.py`方法仅在内存读取已授权SSH配置，独立实际执行只读`ls-remote`，exit0、耗时4.110秒。**2026-11-08 13:42:06.761773 UTC**返回`refs/heads/refactor/architecture-foundations`的完整SHA为`bf99bd47220572fd721546a2eeb5b1b2739a57b5`，与固定候选一致。未输出或写入认证值，未推送、强推或执行配置写入；这是该明确时点的远端事实。

本次仅追加本报告；旧审查及上节历史pending记录均保留。AC1.2工作树、其并行评审和数据完全排除；AC0的CI没有替代本候选CI。断电持久性、恶意同用户强隔离、自动暂存垃圾回收、实际模型/GPU或额外平台能力仍未由本片证明，既有六阶段、候选绑定证据及平台支持边界不变。后续仅需将本节和AC1.1完成状态按原流程归档。
