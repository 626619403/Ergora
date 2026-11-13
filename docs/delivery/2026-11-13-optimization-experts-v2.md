# D2-B1：跨域优化只读专家 v2

实现基线`00922d302daa371ab980093889a8468694c10a94`。承接[专家模板明细计划](../plans/2026-11-13-specialist-presets.md#d2-b跨域优化只读专家与方向子模板)；A2真实重构使用其固定安装独立运行，不消费本片新增数据。

本片在既有定义库和catalog v1内新增`training-optimization-v2`选择：实验设计、跨trace／显存诊断、跨precision／layout／fusion／graph的kernel设计、独立测量审查四份Agent v2。保持原role和只读权限，增加可复用的短Skill与离线证据合同，不把外部库改名为已接入的agent。原v1包、三个原领域配方、重构配方和283冻结参考文件保持。

原measurement子模板精确引用reviewer v1，故需与analysis／proposal一起发布v2，确保新根实际选择四个v2专家；不修改旧引用或原注册表算法。根只带共同目标／baseline／候选／干预／预算／证据／交接合同，详细方向知识按后续B2分包，不让每个叶子默认背负整套外部资料。

|节点|出口|状态|
|---|---|---|
|B1.0 数据|四Agent／三Workflow v2及显式catalog键；固定来源、旧包保持|已实现；旧measurement引用依赖按原接口补齐v2|
|B1.1 静态与安装|新旧版本并存／重复安装／完整manifest恢复；四叶全部只读、祖先与Skill附件完整；非editable发行身份与必要检查|源码最小preset suite12通过42.68秒／外层43.42秒；r1隔离检查通过但保留原P2范围；修正r2安装身份及受影响检查通过，模型与独立补核待完成|
|B1.2 实际叶调用|按同一固定输入实际调用四种职责，手动提供前驱产物；核完整资源和真实回退及结果|四种职责实际独立Codex调用成功；完整前驱手动传递，测量因缺证据request-changes|
|B1.3 审查与交付|本项目自身模板＋新独立两轴；手册与计划更新、普通提交／远端及自己的必要CI|自身原结构模板54.533秒approve／24件49,304B全文；fresh-context安装／模型原件补核待完成|

四叶静态图不新增调度权，`run-input`每次只运行所选叶。实际实验、正确性／质量门禁、原作业、停止／恢复和精确evidence采用仍由原可信runner及维护者负责；提案或缺失证据的分析不称GPU测量或优化收益。本片不安装外部研究工具、升级Forge pin或修改283冻结文件。

新增数据为四份Agent各4文件（定义、指令、主Skill及一份离线证据reference），三份Workflow各2文件，以及catalog新键。只改既有test_presets的一项新增合同检查：新根四叶均v2、只读权限、完整祖先和Skill附件、新旧根并存与原manifest在活动库删除后仍可准备四叶。没有新运行Module、后端分派、调度或CI。

源码12项由本次`src/ergora`加载，命令／stdout／stderr／计时及持久basetemp保存在本项目私有`optimization-experts-v2/source-r1/`。手册新增版本选择、职责／所需资料、逐叶手动交接及未验范围；没有将来源URL或文本candidate当作已运行的工具／kernel。下一对同一候选做隔离安装、实际四叶调用、自身模板及新fresh-context独立审查。

## 独立初审与最小修正

独立初审找到一处可达P2：analysis父指令要求每个叶读取“both experts”的Skill，但实际继承及task-MCP scope只含结构祖先和所选叶，兄弟资料不自动授予。原r1源码及安装输入含该错误，不能把解析／测试通过当作指令正确。已将共享指令改为每个所选专家读取自身完整Skill/context和全部结构祖先；同步analysis资源摘要及proposal精确引用，不扩大资源／权限，也不改runtime。r1候选、安装和测试结果保留其原范围；修正后的受影响检查、新安装及复核另记，正式模型调用使用修正后候选。

## 修正候选安装

r2根digest为`f82061705d1b7a0f8bc6b480327aa0602b8b3519c35aa2a985e1deeadfbb33fa`，wheel SHA256 `396e37a80c70637deef330b152163b821272db097f926a8a6d430af389b53a61`。497份产品在源码／wheel／安装三处相等；wheel与安装RECORD分别505／510行，283冻结参考身份通过。修正后受影响源码检查1项6.67秒，非editable安装检查1项外层9.248秒通过。r1原包完整安装suite12项45.97秒仅归于修正前候选；本片没有借其宣称r2全部重跑。四叶正式模型调用使用r2；静态独立两轴开放0／0，安装原件和实际调用等待同片补核。

## 四叶实际调用与自身模板

修正后r2包完成4次独立Codex task-MCP调用：design85.371秒、profile55.684秒、kernel82.368秒、measurement64.395秒。固定输入为有SHA的LayerNorm源码fixture及操作者给定的FP32推理规格；没有运行torch、GPU、profiler或候选kernel。kernel收到完整design／profile原结果，measurement收到前面三份完整原结果，逐字／SHA已核。每叶的所选完整manifest→input→prompt→stdin→protocol、全部结构祖先来源、native握手／scope／JSONL读取及原result链均核准；19份资源21,036B连续UTF8读取到null，没有失败MCP调用。

前三叶给出有限候选／假设和所需证据；measurement返回`request-changes`，原因包括缺真实硬件／版本、独立数值oracle与阈值、候选来源、原始配对测量和总成本，符合本片“证据不足保持缺口”的出口，未称收益或采用。后端requested／actual及显式Codex回退原因保留，不称异构验收。完整公开[证据投影](evidence/2026-11-13-optimization-experts-v2.json)只记录实际范围。

再用安装包自身原`ergora-structure-review@1.0.0`模板审查24份完整产品／数据／测试文件49,304B，真实独立会话54.533秒approve，两轴结论与原artifact保持。实际stdin含全部文件及三份自身／结构祖先资源，prompt／protocol与源摘要相等；text-only不需要MCP，没有whole-process采样或理解／计费证明。新fresh-context独立评审将继续补核完整最终文件和上述原件；其出口完成前不标记B1完整完成。

## 本地出口

[新独立评审及同片原件补核](2026-11-13-optimization-experts-v2-review.md)完成：完整r3的31文件／修正r2产品与安装／实际四叶／自身原模型及公开投影逐项核准，Spec／Standards开放0／0，SP1关闭。本片本地出口通过。后补PLAN仅记录00922自己的CI实际Cancelled与Windows四步成功，评审已单独核原HTML，不借其授予本候选CI。下一普通提交与远端精确Ref／本候选自己的必要CI分别验收；B2方向模板和真实实验仍开放。
