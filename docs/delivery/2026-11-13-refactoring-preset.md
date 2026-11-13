# D2-A1：行为保持重构配方

实施基线`5af9882367bbe5708f1a86ddabc16b2b665e9a49`。本片沿[专家模板设计](../plans/2026-11-13-specialist-presets.md)新增可选择的`refactoring`数据包，复用原definition6／input10和六阶段所有者。实现、源码／隔离安装、自身模型及fresh-context独立Spec／Standards审查的本地出口已通过；真实重构旅程另归A2，远端／自己的必要CI仍开放。

## 行为与所有者

`composition install-preset refactoring`导入一个普通父模板和唯一六阶段实例。正式`task_type`为`large-change`，不是新增任务类型。原preparation选择独立inventory／plan调用；work按`rewrite → compatibility`对应两个原工作单元；review复用现有结构、正确性、测试价值三个必需分支。可信integrate／verify、计划批准、预算、task／run／candidate及unknown恢复继续由原所有者负责。

新材料要求从精确baseline核真实caller、保持的行为、Interface变化、持久格式影响、迁移顺序及回退证据。缺失项进入原inventory／plan和owner判断；schema字段存在不证明语义已满足。兼容验证是implementation unit，不替代独立最终审查。示例中的SHA／digest是需替换的占位值，实例路径与原work-unit映射已给出。

默认writer／preparation请求Codex，reviewer请求Claude Code；writer在示例中显式选择可信current-container。逐实例覆盖、不同后端偏好和记录原因的Codex回退沿原合同；没有新增后端或OS隔离能力。

## 改动文件

|范围|实际文件与复用|
|---|---|
|新Agent，9文件|`src/ergora/data/presets/agents/ergora-development-preparer/`、`ergora-refactoring-engineer/`、`ergora-compatibility-validator-v2/`各含`agent.json`、`instructions.md`及一份`skills/<name>/SKILL.md`。preparer支持inspector／planner；validator逻辑ID仍为`ergora-compatibility-validator`，version为2.0.0。|
|新Workflow，8文件|`src/ergora/data/presets/workflows/ergora-development-preparation/`、`ergora-refactoring-work/`、`ergora-refactoring-delivery/`、`ergora-refactoring-template/`各含`workflow.json`和`instructions.md`；均为新1.0.0。review固定复用原1.0.0三类子模板及其delivery父。|
|catalog，1文件|[presets.json](../../src/ergora/data/presets/presets.json)只增加`refactoring`键；旧三个配方与其依赖不变。`runtime`复用当前页面识别的`development-v5`开发类别标签，实际准入仍由显式definition6／input10决定。|
|示例，3文件|[README](../../examples/composition/refactoring/README.md)、[grant.json](../../examples/composition/refactoring/grant.json)、[task.example.json](../../examples/composition/refactoring/task.example.json)说明显式授权上限、真实项目输入、原生命周期及回退。|
|回归，1文件|[test_presets.py](../../tests/test_presets.py)增加版本并存／完整祖先及正式native准备检查；CLI列表与实际catalog对照，解除“配方集合必须等于三个正式领域”的旧测试耦合。|
|文档，2文件|本交付记录及所属D2设计进度。全局计划／手册由主线整合，不属本片写入范围。|

当前根`ergora-refactoring-template@1.0.0`的完整包digest为`ce26192b22c25031156755290c252823dbd845c199ff7f62f8e874e07076a15d`。新validator v2与旧v1可在同一库并存；旧完整manifest和在途任务不读取新活动头替换引用。

## 源码验证

使用既有`.venv-dev`，`ergora.__file__`和隔离CLI均指向本次仓库`src/ergora`，新数据实际从源码加载；没有借旧非editable包验证新资产。逐轮候选、命令、stdout／stderr、计时及pytest临时目录保存在本项目`.ergora/checks/refactoring-preset/`；共享阅读以本交付记录和审查前精确快照为准。

|验证|实际结果与范围|
|---|---|
|完整最小preset suite|`PYTHONPATH=src .venv-dev/bin/python -m pytest tests/test_presets.py -q --basetemp .ergora/checks/refactoring-preset/source-r1/pytest-tmp`：11通过，pytest 37.19秒，外层38.25秒。覆盖旧三配方、独立review、旧两域create及新配方版本并存／完整manifest／native prepare。|
|元数据修正后的受影响检查|同一源码环境选择CLI listing、新版本／完整祖先、新native准备三项：3通过，pytest 13.27秒，外层13.62秒；完整选择命令保存在`source-r2/command.json`。|
|静态与保留身份|旧61份preset包文件逐字保持；catalog schema和旧三个条目保持，仅新增refactoring。原283冻结参考文件身份保持。新JSON／Skill资源摘要、声明引用及本片文档链接／空白通过静态核对，原件保存在`static-check.json`。|

首轮所有pytest检查通过。随后核到页面只识别`development-v5`开发类别：初版`development-v10`会被显示为静态提案，故仅修正catalog元数据并复验受影响三项。首轮通过候选与输出保存在`source-r1`，没有改写为最终候选结果；两轮均无pytest失败样本。页面代码和执行版本路由未改。

新增正式prepare检查保存原definition6及准备witness，原preview解出input10；work／review／preparation恰好覆盖所有7个Agent叶，父链为`root → root/development`，原task_type和unit内容保持，writer使用显式current-container、review使用不同请求后端。检查完成时没有发布本任务的`tasks/<id>`或v10请求队列，没有调用Agent或Temporal服务。完整祖先字节可随manifest在原定义库删除后恢复；这证明静态完整装配，实际模型全文读取与行为保持由后续真实旅程验收。

## 审查前状态与下一步

审查前24件精确文件及逐字SHA清单保存在`.ergora/checks/refactoring-preset/review-candidate-r2/`，与生成命令、新包引用及两轮验证一起供独立复核；较早r1文档快照保留。用户已选择项目自身采用Apache-2.0，根许可文件由主线处理；本片Skill与说明为本项目新写，没有复制许可不明的上游正文。产品运行Module、后端、旧1.0.0包与283参考文件均未修改；没有安装新依赖、模型／GPU／网络调用、提交或推送。

## 隔离安装与手册接续

主线从固定C提交导出隔离源码，叠加本片24件及已选择的Apache许可五文件，使用已有本地构建工具和离线固定依赖安装非editable wheel。wheel SHA256 `f97741f8a21e78db1813ee9abe86dce357a4fd65c14a11f5d40109be88677143`，475个产品文件与源码／wheel／实际安装逐字相等；两份RECORD、原283冻结文件身份通过。首个源码准备驱动误把既有path→SHA清单当作带`files`字段的对象，提取基线后出现KeyError，未构建／安装或调用模型；原失败记录保留，按实际清单结构更正后完成上述安装，产品未因此变化。

安装后的完整`test_presets.py`最小suite为11通过，pytest 40.15秒／外层41.98秒。使用`-I`及没有PYTHONPATH的环境加载实际site-packages，验证重复安装、旧版本、完整祖先、manifest独立性和新definition6→input10准备；没有借源码或旧安装代验新数据。

主线同步[定义手册](../WORKFLOW_DEFINITIONS.md#使用内置领域组合)、[使用手册](../USAGE.md#使用重构配方)和[入门旅程](../TEMPLATE_WALKTHROUGHS.md)：新增配方与原正式类型分清，给出安装／manifest／完整任务示例和逐实例后端及显式回退，说明v10目前由CLI／HTTP提交。旧两域页面向导保持原合同，没有把导入按钮称为自动运行新配方。

自身审查用本安装包的原`ergora-structure-review@1.0.0`实际启动独立Codex会话；22份完整产品／数据／测试／示例文件直接内联供给，避免把分页存在当作已读。完整24件作者候选和主线文档由另一fresh-context独立评审检查，原件、判词及最终范围在结束后补记。静态图、prepare成功、原C／D旅程或其他候选CI不替代本配方A2的真实重构执行证据。

## 实际自身审查与独立复核

自身审查已完成，原会话`0ee55401953a42d2b405518cf9996779`为succeeded／CLI exit0／approve，用时32.257秒。22件完整材料共42,298B，49,822B实际prompt与原stdin逐字一致；三个原结构模板／Agent资源（含单文件Skill）与输入assets逐字一致，全部正文完整内联。原模型分别给Spec／Standards pass，并逐类说明22文件覆盖；它没有独立执行测试，也不替代A2真实行为证据。[公开投影](evidence/2026-11-13-refactoring-preset-self-review.json)保存实际输入与判词摘要及后端自报用量，不推导理解、计费或异构后端成功。

首次离线资源审计把Skill树误当成具有`sha256`的普通单文件而KeyError，尚未写公开审计；原失败保留。按实际`instruction_sha256`、完整单文件树和原资产路径修正审计后通过，没有修改产品或重跑模型。

[新fresh-context独立审查](2026-11-13-refactoring-preset-review.md)已核r3完整27件、原compiled manifest／input10、475产品／两RECORD／283和安装11项原件；随后补核r4完整28件、上述模型的冻结／实际／协议输入、原stdout／结果和公开投影，Spec／Standards开放0／0。A1本地出口通过，普通提交后核精确身份；A2实际重构与串行工作／回退旅程及远端／自己的必要CI仍开放。
