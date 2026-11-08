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
