# F7b.0：工单快照与显式上下文关联

基线`9f010079126f374c01272ecf2f0ec85284e4e2cc`；[分片计划](../plans/2026-11-11-issue-mapping.md)。`3c4ef39`的本地出口、普通提交／推送、精确Git／作者SSH Ref及自己的CI42982197290七必要步骤经原评审终核通过，精确交付已结案。前片F7a自己的CI42974715330保持独立原身份，不借前片运行证明新字节。

已检查`issues / tasks / reference_task_creation / reference_task_submission / reference_inputs / state / backups`及迁移／备份与任务创建测试。真实目标事实归原creation，稳定内容快照和上下文关联归issues；旧正式来源无host，先记录显式关联，版本化来源准入另片处理。SQLite新表将使用原状态迁移／备份，保留历史布局与旧writer隔离；具体设计意见、实现及验证按节点续记。

## B0.1／B0.2：源码与首轮检查

新用例均归`issues`，CLI／HTTP仅映射传输；`show`／capture共用当次冻结项目观察。SQLite增加两专属表，保留原16表v1声明，显式v2迁移在同事务替换54个writer fence，原备份器调用领域完整性检查；无新依赖、调度器或CI。离线快照校验同时核保存绑定及解析后的API地址，只有当前凭据变量名被保存，不读取其值。

源码检查使用上一片安装环境的依赖、`PYTHONPATH=src`显式加载当前源码，没有把旧包测试称作新包验证。存储原检查`test_state_migrations.py / test_state_backups.py`共33通过／1个Windows junction项按平台跳过，3.42秒；覆盖固定历史v1及v0的delete/WAL升级、旧连接fence、原行／额外对象／资产／预迁移备份、异常与进程退出回滚。备份manifest仍v1，数据库schema现v2。

初轮`test_issue_mapping.py / test_project_issues.py`共23通过／1失败，19.27秒；失败是新增测试比较creation整个读取视图时忽略当前`project_revision`已随显式绑定编辑从2到3，原creation事实及字节没有差异。测试改为单独核当前项目修订，再比较不可变创建字段。原失败stdout/stderr保留，不修改产品或项目配置来迎合测试；复验、安装包与实际旅程继续。实现计划中capture期间换绑定的语句已与独立设计对齐：保留原观察而非拼入新绑定；只有新link写入会再次核当前修订。


复验源码八个受影响文件152通过／1平台跳过，57.95秒；不是全仓检查。另发现Agent定义备份回归仍写死数据库schema 1，已改用现行SCHEMA_VERSION，安装补验68通过／1平台跳过，3.91秒；迁移手册和当前架构／格式表同步v2，两旧历史归档不改写。

## B0.3：新包与真实CLI／HTTP旅程

r1 wheel SHA256 `f4c520ead27fdf1c6b0b59efce498ee1e6ae101b44c1c5a2b5acfbe5771dde3b`，447总文件／442包文件，wheel与安装两RECORD、当前源码／安装字节及283冻结原件通过。隔离非editable安装的四受影响文件57通过／1个真实Windows junction项平台跳过，pytest23.71秒、driver25.50秒；reference verify通过。测试与文档修正没有改变该包生产字节。

独立安装的真实CLI与loopback HTTP旅程6.27秒／13行为检查通过：普通来源捕获与保护头拒绝、两个原task preview/create发布、两快照／三显式上下文关联、有界过滤分页、手动绑定／删除token／停止tracker后的离线CLI与HTTP读回，重复关联保持原原因／时间；停止Web后复用原offline backup／verify／原home restore，全文与关系保持，原执行目录／creation字节相同，无requests／receipts。三个本地tracker GET，未启动模型／Temporal或正式工作。测试检查命令为synthetic占位，不称真实业务验收。自有Web退出、tracker线程结束与两端口关闭。

第一次私有journey在已保存首个capture后因把urllib.Request的get_method误写成method属性而失败，3.34秒；没有创建任务，原stdout／stderr和控制目录保持，清理通过。修正driver后使用新synthetic项目完整运行上面的r2旅程，没有重跑Agent或真实远端写入。

## B0.4：真实自身审查与修正

原bundled structure-review派生证据修订1.0.91，保留原Skill／祖先指令，仅追加candidate-evidence、版本／引用和材料限额；实际Codex run `e2b326301e6549cfb436a1b964e6c9f7`，194.63秒／succeeded／request-changes。16份完整附件含tracked delta，260,351B；五固定scope完整连续UTF8读至null，原manifest／input／prompt／stdin／准入／scope／结果全链核对通过，4个已采样自有进程无live。该模型只读所附源码范围，未运行代码或读取省略的运行原件。后端自报input755,063，cached664,704已含在其中，output4,594，reasoning2,333单列，不推导账单。

模型提出Spec P2，完整独立评审协调者也从原源码／规格独立确认：保存关联后项目revision2→3，丢响应重发原revision2会在原关系查找之前被误拒。最小修正将_revision移至已存在语义关联返回之后，新建仍保留前置及事务内双检查；既有离线／CLI测试改为真正重发revision2，另在同一场景核旧revision不能创建新关系、也不会调用原target。修正后源码映射10项11.22秒通过（新增“新关系拒绝”断言随后由最终安装包检查覆盖），r1原包／旅程／request-changes均保留；新r2非editable包、修正后的实际旅程和自身聚焦复核继续，尚不宣布完整出口。


修正后的r2包SHA256 `aef9df6e150b739867e00c2f43e2b3a1e2acc9e5d5735ab9def0bc2a0e35ef29`，442包文件／两RECORD／283及source=install通过；安装57通过／1平台跳过，pytest24.00秒、driver25.95秒；新真实journey-r3的13检查7.67秒通过，现以原revision2重发到已升为3的项目，清理保持。该结果仅属r2包。

实际同bundled模板聚焦复核1.0.92，run `c946fc8c3a3c4ca4b35b21463a8df795`，80.09秒／approve，五份完整附件38,681B，全部五scope连续UTF8至null与原输入／准入／结果全链通过，4已采样进程无live；原input117,438、cached92,544已含、output1,710、reasoning516单列。批准只覆盖原P2后移检查的聚焦字节，没有借历史文件清单称全仓已读。私有复用driver遗留r1的receipt basename，在写出前已把原r1文件原样保留，r2结束将新receipt移至r2并恢复原r1，原1479B／SHA256 `44c3d12eabec2c192fb71c9655c4630a9e629258b6bda1d6dd5ebd1e90b41e0f`相同；native/input/result目录始终分开，未重复调用模型或改产品。

独立Spec另核同一SP1的可达竞争窗口：A／B初查都未命中，A先插入且配置升修订，B随后取得写保留；B应取原关系。现事务内先重查已有关系，再仅对真实新插入核revision；已有BEGIN IMMEDIATE排除后续竞争，因此删除冗余的link INSERT ON CONFLICT分支。新增一个实际原creation交错回归覆盖原原因／时间／关系唯一及执行目录字节保持，没有新增CI。此后补行为不回授1.0.92模型判词，由最终新包和完整独立复核验收。独立Standards的一个旧F7a终核fragment P3已改为真实标题。最终r3包与公开投影／两轴终核继续。


最终r3 wheel SHA256 `5976eeb3b1c3e0beb93bffc1bdf86d8c8221c3625d34a97fa7bc715f81c14042`，447总／442包文件、wheel与安装两RECORD／当前源码等安装／283冻结通过；安装全部11个映射回归通过，pytest与driver计时见[有限验收投影](evidence/2026-11-11-issue-mapping-acceptance.json)，reference verify通过。r2的完整受影响检查及真实13项旅程仍保留原包身份，没有称作r3已重复运行；最终r3检查包含并发先落库再改修订的确定性交错、原请求重放、CLI／HTTP及备份恢复，所测产品行为通过。无新增依赖、CI或JS。

[两轮自身模板投影](evidence/2026-11-11-issue-mapping-self-review.json)保留首审request-changes、聚焦approve、各自原判词／输入与附件索引、五scope连续全文页及用量范围；后补并发修正／最终包不回授原模型。新的[完整独立两轴报告](2026-11-11-issue-mapping-review.md)原SP1／ST1已修，最终完整候选和投影补核继续；远端提交／自己的CI仍未结算。

## 完整本地出口

新的fresh-context协调者及其两个fresh子轴已完成初始25与最终28文件独立审查，原SP1／P2和ST1／P3关闭，Spec／Standards开放0／0；实际复建两轮模板输入／scope／原意见与receipt修复，终核33份公开投影原件，逐字核最终r3的447／442、两RECORD／452行、source／freeze／wheel／installed与283原件，并从保留真实DB只读调用最终Interface核原rev2重放、新关系拒绝和不访问runtime。[独立终核报告](2026-11-11-issue-mapping-review.md)限定本地出口，没有新跑模型、网络或产品套件。

最终有限静态先核28文件／326本地链接／6已加载秘密值issue0；完整锚点、Mermaid、外链与运行时不在该静态范围。模型的聚焦批准没有覆盖后改并发／公开投影，最终独立两轴覆盖。接下来冻结ready、普通提交／推送，核精确Git／远端和本候选自己的CI；本地通过不提前替代这些出口。下一实现片按F7b.1先设计版本化完整来源及窄准入，保持原policy／claim／attempt／memo／unknown，不从本片关联推导正式派工。

## 普通提交与精确交付（已结案）

最终有限静态28文件／329本地链接／6已加载秘密值issue0，ready manifest SHA256 `5682d1b8cf20f354a88121348a983cbc7723003e5b69a82fa28b4f530063ab15`；原评审同片核28冻结／live／模式／路径及仅6份后补状态通过，生产／测试／两投影保持。普通提交并推送`3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`、单父9f01007；作者核全部28 Git blob／100644与ready相同，push exit0，未强推／合main或改认证／remote。当时工作区clean；本段为提交后的同片状态回写。自己的精确远端及CI继续独立终核，不借前片终态。

作者随后一次既有SSH push URL的只读Ref查询exit0，86B stdout为完整`3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`及正确分支；原评审离线核原件与摘要通过。评审者自己的一次SSH查询因代理407失败，保持原件，不称评审直接远端成功。匿名REST第一次403限流；官方Actions索引HTTP200精确关联本提交／分支与自己的[Portability 42982197290](https://github.com/626619403/Ergora/actions/runs/42982197290)，首run HTML仍In progress／0/2 jobs completed。此时终态尚未确认，不据403称CI失败，也不推下一候选以取消它。下一片的[来源任务设计](../plans/2026-11-11-issue-dispatch.md)在本地继续。

第三份run HTML为HTTP200／157,039B，SHA256 `52945372826d9d015131f2ac60594eb542fd360282732a4542e2cbdb9d621b9c`，Status Success并精确关联完整提交、分支与两job。原评审随后对Linux `130394959642`和Windows `130394959979`官方job页面各一次直接GET，两原HTML确认Linux三／Windows四必要步骤completed/success，逐步log URL均带完整本候选及正确job ID；Linux的Windows安装项按条件skipped。原评审离线再核28个Git blob／模式等ready，以及提交中的442份包文件逐字等于最终r3 wheel；未借正在变化的B1源码。

[原评审精确终核](2026-11-11-issue-mapping-review.md#同片精确交付终核2026-11-11)通过，本片精确交付结案。首REST403、前三份非终态HTML（含Actions索引）、独立SSH407保持原件；这不是成功REST查询或全job日志下载，也不声称评审直接SSH成功。后续按B1版本化来源任务继续，原业务／平台未验范围保持。
