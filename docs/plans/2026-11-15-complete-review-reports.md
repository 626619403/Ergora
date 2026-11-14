# Q2.3b2／b3：完整来源与多分支审查报告

日期：2026-11-15。本地基线`96b4bb5454714a73e1d5f60b880a479c195e5269`，承接[原run读取](2026-11-15-composition-run-inspection.md)及[总合同](2026-11-15-source-review-reports.md)。前片本地验收已闭合，自己的发布／CI另跟踪；本片可本地推进，前片终核前不推后继产品。

## 行为与归属

在原`review_requests`增加只读`report`用例，薄`review report` CLI消费。显式提供来源目录／kind／SHA、完整manifest／digest，以及JSON对象形式的`实例路径: 原run ID`映射。沿原source reader、manifest compiler、`require_root_task`、`agent_runs.inspect_run`及可信`agents.result_schema(["response"], review=True)`；不复制SQL／猜存储路径／读取原metadata绝对指针，不引入新schema、State、SDK或调度器。

预期成员是所选完整manifest声明的全部Agent叶，逐叶复用只读reviewer／读取上限／直接根task约束。不用投影串行图跳过依赖，也不把这份独立叶报告叫作正式图执行或all-join批准。允许一个独立叶或多叶／嵌套模板，不要求单叶图额外增加join。原图、所有继承Skill／上下文／权限和实际请求仍随完整input保留；Kernel专家及优化v3不改。

来源及manifest先按显式身份核验；错误选择不能静默换源。未知实例或重复run映射属于请求错误，明确拒绝；漏选成员、未知run、原失败／running／preparing／unknown、缺件、错来源／实例／manifest、不可核input／prompt／result或不符可信reviewer结果，逐叶保留原观察／错误，报告其它叶仍完整。每叶的匹配要求包括原input实例、完整composition与所选manifest一致、原task摘要等于原source-bound task、三项原件可核及可信结果合同。当前后端配置和认证不参与历史读取。

分别呈现选中覆盖、证据可核、原状态、完成与模型建议。只有每个预期叶都证据可核且原status为succeeded时覆盖完整；完整时任一request-changes即为总体request-changes，全部approve才总体approve。覆盖不完整时总体为incomplete，同时保留已核的approve／request-changes成员和完整原回复，不多数投票。报告是本地建议，不是正式候选或平台批准。

CLI可输出完整JSON或由同一观察渲染的Markdown；用户重定向保存，不新增第二账本或自动覆写文件。Markdown保留每个原结构化结果及完整来源／manifest／input观察，代码围栏不能被材料中的反引号提前闭合。显式结果容量沿原reader，超限是该叶不可核，允许操作者提高容量后重读。重复生成不调用模型或补跑缺叶。

## 验收步骤

|步骤|完成条件|当前状态|
|---|---|---|
|C1 合同|固定原owner、来源／manifest／实例／run匹配、覆盖和意见语义，列明只读边界|本合同已固定|
|C2 实现|原review_requests报告和薄CLI、JSON／Markdown，同一原观察；现有prepare／verify保持|原owner／薄CLI及两手册已实现；Markdown用缩进代码保留字面材料，无新围栏解析器|
|C3 接缝|原review packet fixture覆盖两域／三通用叶、少数反对、漏叶、未完成状态、错身份、坏原件／schema、重复映射与重复读取只读|原源码／安装分次结果及失败保持。r5五受影响安装suite207通过／180.75秒，无跳过／失败；覆盖非有限／结构容量、原DeepSeek归档／续接及定义编辑转换接缝|
|C4 安装与实用|新非editable包逐字／283保持；实际CLI沿Q2.3a真实领域run读回，再在本片隔离控制目录明确运行同来源其余三叶，验完整覆盖和完整原回复／实际后端|原r1的15CLI／四叶保持；r5包643三方／283及四同run只读CLI通过，完整报告同原r1、Markdown反解相同、非法显示字面、152文件／四DB行不改。无新模型或真实训练／异后端主张|
|C5 审查与交付|自身原结构模板、新fresh-context两轴；更新计划／交付，普通推送当前开发分支、完整Ref、自己的CI／原终核|四需求P2／原失败及各修正历史保持；r5自身46.161秒approve，原独立最终19路径／11证据和全部原件两轴approve／开放0／0，R1–R4关闭。本地验收闭合；本片固定发布／自己的CI另验|

实施范围为`review_requests.py`、`cli.py`、原`test_review_packets.py`／`test_review_associations.py`，以及LOCAL_REVIEW／TRAINING_REVIEW和本片记录。外部接缝扩展原fixture，不新建CI job。实证非有限／深结构导出问题的最小修正另涉及原`definition_bundles.parse_json`的默认关闭选项、同owner原迭代容量检查的复用、`agent_runs`记录／结果读取及原`test_composition_invocations.py`；原DeepSeek和定义编辑接缝随共享reader检查，其他JSON消费者默认行为保持。没有真实消费者要求的抽象层、远端评论、自动重发／合并、项目代码修改或训练执行不在本片。每步更新[交付](../delivery/2026-11-15-complete-review-reports.md)及PLAN；完成后按原顺序接Q4.2有界循环与Q5.2按证据重构，真实B3／完整Forge的开放条件保持。
