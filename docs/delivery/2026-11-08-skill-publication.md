# AC1.1：Skill完整树发布与中断恢复

日期：2026-11-08。状态：完整完成。候选`bf99bd47220572fd721546a2eeb5b1b2739a57b5`的本地/非editable包验证、普通推送、自身双OS CI及[同片独立终结](2026-11-08-skill-publication-review.md#ac11精确ci独立远端与完整终结)全部通过。基线`0f8e2a98dbfa42ea96657ef80fbf2bc356f57abe`，分支`refactor/architecture-foundations`。需求来自[完整源码评审S-1](2026-11-08-agent-composition-review.md)及[AC计划](../plans/2026-11-08-agent-composition.md)。后文保留各步骤当时的状态和原始限制，不将AC0的CI当作本片验证。

## 要修复的行为

旧导入直接复制到最终内容定址目录。复制中断但目录已存在时，重试跳过复制，将预期digest写入版本、活动头和初始事件；随后读取才发现缺少资源。修复须让DB只登记完整且核过身份的树，保留来源稳定性检查、摘要算法、公开路径及版本/采用语义。

在`skill_assets.import_bundle`内完成：把暂存放在最终目录的同一父目录，完整复制并核摘要；复用`state.file_lock`协调同一项目/digest的发布与登记，原SQLite事务仍拥有版本/活动头/事件。完整树通过原子rename发布；中断前没有有效登记，发布后DB提交前中断则留下可核实重用的完整孤立树。旧版本留下的未登记残树可以用已核完整副本恢复；已登记但缺失/被改的树明确拒绝，不覆盖或悄悄修复证据。

代码留在现有资产所有者，不新增公共函数、目录级抽象、依赖、状态表或CI。测试放在现有`test_skills_evaluation.py`，只覆盖真实失败窗口/竞争和持久结果；不改评价算法、模型调用或冻结参考内容。

## 验收及记录

|验收|状态|
|---|---|
|旧未登记残树重试后资源完整；重复导入保持已有完整树和单一登记/事件|本地及实际安装包检查通过；重复调用原文件mtime保持|
|暂存复制中断、发布成功但登记前中断后重试；失败不留下活动登记|两个真实文件操作故障注入/持久State检查通过|
|已登记树被改/缺失时导入拒绝，原证据/DB不改；原GET篡改拒绝保留|两种损坏检查及既有GET/Agent/evaluator拒绝通过|
|多个独立进程导入相同digest幂等，最终仅一个版本/活动头/事件|四个实际Python进程同步进入导入，原生锁/DB/文件结果通过|
|既有Skill/评价/采用、状态与架构定向检查，冻结身份和diff|源码32 passed/5可选GEPA skipped；新独立包Skill全18 passed，无skip，283身份及diff通过|
|新的fresh-context独立审查、普通提交推送、精确双OS CI/远端|独立需求/可维护性审查无finding，另6例及5真实退出窗口通过；bf99普通推送、自身CI42484784168双OS必要步骤及独立远端终结全部通过|

仅使用隔离测试State和fixture项目，不迁移或修复实际用户库。故障注入、真实进程并发与本地平台检查各自记账；没有证据前不宣称Windows行为、断电持久性或性能收益。

## 实现与实际验证

生产改动仅在`skill_assets.py`：一份完整暂存副本，同digest的原文件锁，核已有树，再rename/登记；SQLite提交在释放文件锁之前完成。已完整发布但DB未提交的孤立树可由后续导入核后登记。原路径、digest编码、首次baseline及后续候选/采用合同不变。可恢复的旧残树仅限没有该版本DB登记的内容，已登记损坏保持原样并报错。

新增六项参数化后的行为检查在原`test_skills_evaluation.py`，包括两处中断及两种已登记损坏。每条检查触达已有公开资产interface与真实文件/State；并发使用四个独立解释器、原生锁和同一DB，不以mock锁替代。未新增公共helper、测试框架或CI。

|实际命令/身份|结果与范围|
|---|---|
|修复前，新增残树及已登记损坏三项定向检查|真实3 failed，复现旧版本登记残树和不拒绝损坏；保留`red.log`与命令exit1，未当产品新失败或绿色结果|
|`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_skills_evaluation.py tests/test_state_migrations.py tests/test_architecture_boundaries.py`|Python3.11.15/pytest9.2.0，32 passed/5 skipped，20.69秒；五skip是该已有环境没有可选GEPA|
|默认隔离`python -m build --wheel`|exit0，15.13秒。先前`--no-isolation`因原检查venv没有setuptools.build_meta而exit1；默认构建成功，不将环境错误写成源码缺陷|
|新独立venv安装本轮wheel的`[dev,web,gepa,temporal]`|实际exit0，22.73秒；没有改原用户运行环境。wheel SHA256为`56c5ab1a6baaf31deb3e30927d4900ce8f7f1be5e7d0633fa7c71d09793dd89d`|
|从新非editable包运行原Skill全文件，移除`PYTHONPATH`|18 passed、零skip，25.94秒；包含真实GEPA fixture提案/评价/失效边界和本轮六项检查，没有真实模型调用|
|源码、wheel、实际安装包身份|352包文件逐一相同；源及包内`ergora reference verify`均283 PASS，未启动runtime|

本地证据位于忽略目录`.ergora/checks/ac1-skill-publication/`，包含实际命令/退出、源码和测试SHA、安装包文件身份及故障/并发fixture。新独立审查、最终文档静态和普通提交/推送/双OS CI仍待完成。没有新增性能测量或跨平台实测，复杂度沿既有10 MB/500文件限制；没有据一次耗时宣称性能提升。

## 独立审查及处置

已全文读取新fresh-context[报告](2026-11-08-skill-publication-review.md)，两轴范围内无finding；实现和测试的原SHA保持。评审者独立重算352文件/283身份，复跑六例通过，并额外用子进程`os._exit(73)`验证copy、rename、版本INSERT、事件INSERT及commit后五窗口：前四者无部分登记，最后者保留唯一原登记；全部重试后完整可读且版本/head/事件各一。除尚未发布的copy窗口外，已有完整树mtime保持。主代理另读原`probe-result.json`，与报告相符。

原审查者首轮basetemp父目录未创建导致setup exit1，未触达产品；其正确复跑6 passed/7.54秒及原失败分别保留。额外探针只在忽略目录，不新增永久CI或重复测试。硬退出可以遗留不被重试消费的`.import-*`暂存树；本片不加垃圾回收器，也不据此宣称断电持久性。S-1的本地修复/审查已满足，完整节点仍待普通精确交付及本候选CI终结。

最终归档范围11文件，其中9 Markdown/328本地链接锚点无缺失、30 README parser及diff通过；生产/测试SHA仍与独立审查及已安装包一致。AC0原独立报告追加和主代理S-1回应仅为原片/本片状态归档，原独立结论完整保留。下一普通候选提交推送、精确双OS CI和同片终核，不主动重复已通过的源码/包检查。

## 精确交付终结

候选bf99已普通push exit0；自身[CI42484784168](https://github.com/626619403/Ergora/actions/runs/42484784168)的Windows128744183496四个必要步骤、Ubuntu128744183793三个必要步骤均实际success，Ubuntu的Windows-only步骤skipped。原独立评审者再次核固定候选/11文件、官方原HTML的精确commit/步骤日志URL，并于2026-11-08 13:42:06 UTC独立只读查询远端，完整SHA仍为bf99。两轴无新增finding，S-1及AC1.1完整关闭；原始失败、未验范围和审查文字保持。AC1.2及新Agent组合分别验收，不继承本候选CI。
