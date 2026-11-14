# Q4.2a2：有限训练候选冻结交付记录

日期：2026-11-15。实现基线`d3c90e751ee9257df36b74e57e8956d38bbde848`，按[具体计划](../plans/2026-11-15-training-cycle-selection.md)实施。前片自己的CI43644626885／八job／30步骤及原独立终核已闭合，本片按自己的源码／安装／审查与发布门禁接续；不借前片CI。

|步骤|实际状态|
|---|---|
|原owner／合同|已核a1原check_start、原rounds／目录发布及原Experiment／workflow窗口；准备冻结输入和预算策略，不开启时钟／派发，不复制准入或评分|
|容量调查|已取固定Server1.32.0官方源码默认值与本机CLI版本；原件在ignored training-cycle-planning/temporal-capacity-r1，不能替代实际部署准入|
|计划复核|[原Q4.2计划reviewer](2026-11-15-training-cycle-selection-plan-review.md)已对初版方向两轴approve；预算必要关系／T上限、原State注册来源、字节容量和双向payload／单轮结果存储边界已落实，修订复核待。它不认证实现|
|实现|新增输入owner及schema、薄cycle-create／read CLI已实现；不新增运行表／时钟／调度／评分。共有字段沿完整值比较，候选track／allowed_changes完整保留；后继重新准入及归属不能由本片代替|
|源码接缝|初版六项通过／6.75秒，含真实原owner的12个合法大manifest聚合超过10MB而拒绝发布；新补注册／URI内部绑定、完整字段及原unknown接缝后另验，不沿用初版通过|
|安装／实用／审查|待；不称预算执行、自动循环或真实训练已完成|

## 源码修正与安装验证进度

补充原注册身份核对时，曾把 `registration.definition` 误当作同时包含项目 ID 和仓库路径，导致 `source-tests-r2` 四失败／四通过（35.27秒）。已按原 `registrations` 的实际封套修正：摘要内容为项目 ID、仓库及注册定义的组合；原失败保留。修正后的 `source-tests-r3` 八通过／13未选（35.61秒），覆盖候选完整读回、共同合同、漂移、容量及既有 unknown 接缝。

验收原件位于 ignored 持久目录 `.ergora/checks/training-cycle-selection/`；更早六项结果仍在 `training-cycle-planning/`。另一次恢复后源码定向运行 `source-selection-r2` 八通过／38.46秒。r1 wheel SHA `a4a49cbab5dccaf49dc047497d8cf8e03be13a64ed6da9719e278d228652d6a9`，独立 core／SDK 均645源／wheel／真实 site-packages逐字一致，283参考保持；core无SDK，SDK为1.34.0。仅新增领域输入owner／schema并修改CLI，未改原训练实现。

`native-journey-r1` 经原公开owner登记、初始化和准备两个合成CPU合同，实际无SDK安装执行创建／完整SHA读回／错SHA拒绝三CLI通过；47个原文件和DB dump保持，离线未创建所给空control目录。完整输入19,967字节、SHA `379ab6acde2be7b127697426e9c83e2c9d248f5b8f7d6be94702de0a3d5c140a`，完整项目、请求和两份原观察读回一致；没有执行runner、模型、服务查询或训练投递。安装四suite及自身／独立评审仍在途，不沿用旧功能验收。

## r1审查与修正中的r2

r1安装原训练／提交／运行／取消四suite共60通过／276.61秒，无失败／跳过；一次既有TestClient弃用提示。它们认证当时r1，不能认证下列后补修正。

自身原 `ergora-structure-review` 实际run `c089fb1aefc6463188a92f547d5f73e1`，68.642秒，完整21文件382,274B及三份祖先资源进入stdin，返回 `request-changes`。新[fresh-context独立评审](2026-11-15-training-cycle-selection-review.md)另核相同r1，需求轴request-changes／维护性approve，提出两个P2：R1完整注册／原观察文件集合，R2保存的baseline及spec／manifest关系。两者已在原输入变体中独立复现；完整文件SHA不能代替内部一致性。

原 `self-review-repros-r1` 与评审原件保持，补入既有离线读回接缝后的旧安装实红 `installed-regression-red-r1` 一失败／1.35秒。r2正在修正：注册四文件的纯投影从原 `registrations._prepare` 提到同owner的 `publication_files`，原注册和新离线读共用；保留legacy策略列表的等价顺序。补齐原快照必需字段、baseline四元组、spec／runner／manifest关系与原file SHA库存，不读当前文件，也不把重序列化摘要当原文件SHA。修后源码、重新安装、原注册回归、自身复审与独立复核待，R1／R2尚未关闭。

## r2当前证据

- 修后 `source-tests-r4` 八通过／35.78秒；沿原离线接缝覆盖实证破坏变体，合法单候选与legacy策略等价逆序保留。没有新增suite或CI job。
- 最终候选r2 wheel SHA `ec11cc24535bf287556d4da39771d4d5451ca1ee081f2d32d15e92f5d4f13c5a`，`package-r2-core`／`package-r2-sdk` 均645源／wheel／实际site-packages逐字一致，283参考PASS。core无SDK、SDK1.34.0。相对d3c90e7仅新增输入owner／schema，修改CLI和原注册纯投影；没有改原执行或参考快照。
- `native-journey-r2` 重新从原公开owner准备双合成CPU合同，core真实三CLI通过；19,967B完整输入SHA `f2709a9cb42b4de4919d706f37bc88f6033f0f41530e5250af5c5692bfcaf9b1`，47原文件和DB保持，全文读回一致，无SDK／服务／模型／runner／训练调用。r1旅程不被覆写。
- 自身原结构模板r2实际run `6cbcb6d6ca634c35bc90687ad494d288`，78.648秒、succeeded／approve；完整21文件393,898B、三祖先资源及实际stdin身份通过。只审所给完整源码和记录，不认证未提供原件、真实运行或CI。
- 新安装七suite（原训练四suite＋注册／schema／架构边界）`installed-tests-r2` 已148通过／304.32秒，无失败／跳过，一次既有TestClient弃用提示；使用r2 SDK安装解释器的 `-I -B -m pytest`，不从源码导入。原独立reviewer已接修后复核，R1／R2最终处置待。检查十文档182本地链接零缺失、`git diff --check`通过。

两次验收命令准备错误另保留：`build-r2` 在开发环境找不到可执行build模块，已用实际安装环境隔离运行构建成功（`build-r2-retry`）；`self-review-r2` 首次脚本生成有引号语法错误，编译修正后实际模型调用为上述r2 run（`self-review-r2-retry`）。两者未调用训练或写原运行，也没有用失败结果宣称通过。

## 本地验收终核

原新的fresh-context reviewer已追加r2最终本地评审，需求／维护性两轴approve，R1／R2关闭、开放0／0。直接复核十七个破坏变体与十三个选择／预算／严格JSON边界、合法原输入与legacy非空策略顺序、原纯投影AST和两个实际消费者；另亲核645两安装的完整逐字身份、r2实际输入／三CLI／47原文件和DB、148项XML与自身实际输入／结果。原r1报告全文保留；该本地结论不覆盖普通发布／自己的CI或后继自动执行。

准备普通发布当前开发分支，不合main。前片自己的CI与原独立终核已闭合；本片固定源码／安装／本地验收身份完整，发布SHA及远端／自己的CI另记。

## 普通发布

已普通推送 `1b58e929aaf495c16f448454c78de23718786ae9`，parent `d3c90e751ee9257df36b74e57e8956d38bbde848`，tree `f2980c9741332e580814021e78252687794054ab`，15个Git blob和完整远端Ref同一；未合main。产品／测试／训练手册与r2安装及审查固定件一致，其他差异为本片记录和a1原CI终态记账。b1计划／报告没有混入本提交。

原件为 `publication-local-r2.json`／`publication-r2.json`、`publication-staged-r2.diff`、`push-r2.*` 和 `remote-ref-r2.*`。原独立reviewer已接固定发布／自己的CI终核，尚未宣称闭合；b1可本地推进，前片门禁终核前不推后继产品。

后继实证逐步更新本页和总计划；Kernel专家及283参考快照保持。实际训练／GPU／质量／收益和完整Forge仍沿原开放条件。

## 自己的CI与独立终核闭合

固定发布`1b58e929aaf495c16f448454c78de23718786ae9`的Portability `43647584681 / attempt1`已completed／success，八job／30适用必要步骤全部成功；终态完整远端Ref同一。原独立reviewer已逐件核117原件、官方run／八job页及最终Ref，并追加[原报告](2026-11-15-training-cycle-selection-review.md#本-sha-自己的-ci-终核追加已闭合)：需求／维护两轴approve，开放0／0。精确交付门禁闭合，不借前片CI，也不转授b1或自动循环；原在途观察和失败保持。
