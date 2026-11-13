# C：单实例六阶段调用

基线 `a00896146c6499f58ae86a5b6b76fa13c3c7c796`。B2b／c本地出口已通过，首次普通推送在SSH握手超时；重试与自己的CI另按原预算交付记录关闭。本片承接[原生消费者计划](../plans/2026-11-12-six-stage-native-consumer.md)的C，先实现和验证单实例合同，D再验真实Temporal／模型完整旅程。

## 合同与所有者

复用普通WorkflowDefinition v1／v2及已有完整manifest，无需引入新图格式。新task-definition v6在原v5完整选择中增加显式 `composition.native`：`protocol: six-stage-v1`、`instance`。用户选择的普通父模板只能以一条直接task输入／结果输出链引用一个六阶段实例；前驱、兄弟、第二实例和未执行的外部数据依赖在准备期间拒绝。内部准备／工作／审查选择必须都位于该实例内，仍由原WorkDelivery检查全部Agent恰好覆盖。内部原生阶段顺序由原Temporal负责，静态图不另获执行权。

正式input v10保存原完整manifest、native实例和全部父定义精确链，以及已有项目修订、baseline、四模型阶段选择／能力与原预算；父结果仅投影原task／run／candidate及证据，不增加批准、成功或执行账本。原prepare／create／start／观察／取消／对账仍是唯一入口。新版本独立queue／request-root，v1–v9原语义及283冻结文件保持。

纯数据的实例／祖先映射由一个小模块拥有，生产调用者为 `tasks`（从实际冻结图准入）与 `task_envelopes`（原件读取／恢复核对）；原creation核定义选择与保存的投影一致。`WorkflowInput`注册新实现，继承已实现预算／完整材料／job owner，原Executor不按native类型再写执行分支。CLI／HTTP继续消费同一task用例。

## 验收节点

|节点|必要证据|状态|
|---|---|---|
|C1 精确选择|普通父／单实例的祖先及stage映射；非支持形状在prepare内拒绝，完整原件可独立恢复|已通过源码与非editable安装检查；公开父例／多层完整链、继承与未执行分支拒绝均在core-r1覆盖|
|C2 原所有者接入|v6准备／双摘要创建／v10提交；原ID重复及unknown恢复、memo／完整input碰撞，旧v9保持|已通过core-r1；受控SDK原ID丢回执／memo与完整input恢复及旧creation／预算／transport合同保持|
|C3 验证与审查|受影响合同／安装检查；实际自身结构模板；新独立Spec／Standards；普通发布与自己的必要CI|本地出口通过：安装73项／自身r2聚焦approve／最终完整独立两轴开放0／0；普通发布与自己的CI待|

实际运行和失败保持在本片持久私有目录，文档只保存可分享的身份、范围和结论。未通过D前不称真实模型整个六阶段或任意混合图已经验收。

## 首轮实现与源码检查

新增纯stdlib的 `native_six_stage.invocation`，由tasks准入和task_envelopes原件读取共同使用；没有新增图执行器或账本。definition6／input10沿原预算准备、创建、注册factory与原worker接入；新workflow只为原预算status／outcome追加native只读投影，原任务状态不另存。公开native-development父包复用已有prepared-delivery，未修改旧例身份。

source-r1为16通过／4失败（49.02秒）：三项错误地要求prepare在worker失败时直接抛异常，另一项错误要求已保存成功提交后再次start重新请求远端memo；原合同分别返回failed准备witness和缓存的原提交。source-r2修正为实际unknown恢复中的normal／wrong-memo／同legacy不同完整input，五通过／三失败（72.06秒），剩余为断言在公开准备摘要中找私有stderr原文。未因此改变原准备／提交语义。

source-r3按原私有worker stderr核拒绝原因，受控父模板／准备恢复／三个SDK恢复及架构共22项通过（72.41秒）；使用动态合成父包，没有模型或真实Temporal请求。随后测试改为直接消费公开示例并补多层父链，因此最终安装检查将覆盖这份新测试，不能把旧源码次数自动记为新版本通过。产品此后未改变。当前非editable包已离线构建安装，身份、受影响回归、自身模板和新独立审查继续。

## 隔离安装验证

install-r1离线非editable wheel SHA256 `1da3b270eb63c9c8d20eba96f659bf6a5049288b35c8100cfc143841327dd598`；458产品文件与源码／安装逐字相等，463条wheel RECORD及468条installed RECORD各核hash／size，283冻结文件身份保持。

core-r1使用安装包的Python `-I`、无源码PYTHONPATH，共73项通过（256.66秒pytest／258.63秒外层）。覆盖公开native-development父例、多层父定义链、完整继承、篡改祖先投影拒绝、准备时拒绝父兄弟／第二实例／不转发输出、原ID丢启动回执后的正常／wrong-memo／同legacy不同完整input恢复，以及旧creation／预算准备／composition transport／架构与旧v9完整材料九job七slot受控串行旅程。原准备与SDK是受控故障，job／Git／进程／收集为真实本地执行；不是v10全Temporal或真实模型旅程，也不证明Windows运行。

新的独立两轴已读取完整r2冻结候选，产品Standards／Spec均开放0；SP1仅为上表C1／C2状态滞后，现按73项原件同步，待同片复核。README／两手册及架构扩大范围已纳入r2，安装原件经评审独立重算。自身结构模板以七件完整聚焦材料实际运行，602.06秒timed_out／CLI退出1，无result／decision；采样四个所属进程无存活。原评审核附件72,767B仅连续UTF8读取前36,000B，另外四个小scope读至null；没有完整读取七份材料，不能以超时称approve。原失败次数及其实际候选不改写为通过。D真实Temporal／模型旅程、普通发布及自己的必要CI仍待完成。

## 自身模板r2与本地收口

针对r1的分页耗时，r2继续使用安装包原`ergora-structure-review@1.0.0`，没有修改模板指令或产品；切换其已支持的text-only，将完整产品diff、native模块、当前测试和公开父例四件合计37,984B直接放入operator task。原prepare输入、实际input、完整prompt与stdin逐字相同，四件各自大小／摘要与冻结原件匹配，全部继承指令及单文件Skill内联。没有宣称text-only支持附件或MCP读取。

实际175.93秒succeeded／CLI退出0／approve，模型分别给Spec与Standards通过并列明四件范围。原turn自报input58,705（其中cached38,400）、output737和reasoning output322；实际计数以原件为准。此处不估算费用，不把字节供给当模型理解，不把聚焦范围冒称完整24文件；完整候选仍由新上下文独立两轴检查。[公开摘要](evidence/2026-11-13-six-stage-native-self-review.json)保留两轮各自范围。

C1／C2状态P3已由原评审复核关闭。完整r3作者26文件及r2模型原件已由原fresh-context两轴补核，Spec／Standards开放0／0，C本地出口通过；普通发布、精确远端Ref和本候选自己的双OS必要CI仍待，D真实全流程另有[交付记录](2026-11-13-six-stage-native-journey.md)。本片未增加依赖或CI任务。
