# F9c：原训练证据审阅、精确批准与集成复验交接

日期：2026-11-14；首片基线`2181cc5c6ab92ac01664f8e769298cce350f65a5`。承接[F9b4准备计划](2026-11-14-training-preparation.md)，C2页面已普通推送，固定发布与自己的CI单独核对。

## 原职责与分片

原`perfctl archive`拥有内容寻址的accepted-evidence、所有artifact校验、独立attestation与配对统计重新计算；原训练adapter核已归档gate、owner私有receipt及baseline，Temporal拥有AWAITING_RELEASE、release信号和集成票据创建。它们继续是唯一门禁和执行权威；读取、信号投递、票据创建、真实集成复验和采用分别记录。

|节点|实现与复用|验收|
|---|---|---|
|C1 原证据只读入口（当前）|CLI／HTTP沿training应用入口读取原gate、按完整evidence SHA定位同项目accepted-evidence，核evidence原字节、归档gate和manifest／baseline／comparator元数据；列出原artifact索引，显式选一个有摘要的UTF-8文本窗口；查看同binding／evidence的原本地集成票据。SDK／服务均不需要|真实原archive生成材料；来源／摘要／路径／跨项目／缺失／污染反例；二进制／超限明确失败；读前后原件保持，最终非editable安装与283冻结、CLI／loopback HTTP／SDK-free、自己的模板和新的独立两轴及精确发布／自己的CI|
|C2 精确owner批准与恢复|先冻结项目revision、原完整start／run、完整evidence及原owner身份；复用现有attempt-before-send／固定run history语义和原release客户端，先原私有owner receipt再原信号。状态／unknown恢复不重发，明确区分receipt／投递／票据事实|另立小片合同，核原AWAITING_RELEASE／binding／evidence、同请求幂等、已关闭／超期／撤销／fence、实际投递后丢回复及原历史对账，不复制另一批准服务或绕原owner|
|C3 页面与集成复验导航|原证据与artifact窗口、精确确认／原意图恢复，原本地integration ticket及项目开发任务明确手动交接|真实浏览器生命周期、三视口、现有start／cancel回归；另立合同，不把票据当真实复验或自动采用|

## C1行为合同

只读同一已发布training-optimization项目。复用`_TrainingProject`注册校验、原`_training_records`的manifest／spec／runner／job／gate身份、有界safe_file／read_raw和现有process monitor；保持283冻结参考文件。新`reference_training_evidence`拥有归档读取的内聚算法，唯一生产消费者为reference的训练子进程入口；CLI与HTTP共用training应用入口。既有Task evidence绑定的是开发history／job receipt，不能作为训练归档权威；不新增通用registry或第二实验库。

`ergora training evidence PROJECT EXPERIMENT_ID`读取原gate及完整evidence／归档gate、归档manifest／baseline与comparator摘要，原始sha与当前baseline适用性单列。无gate或gate未通过时明确没有accepted archive；不生成批准或修复文件。原artifact索引只检查路径与声明摘要，内容标为未读取；不能因此宣称重算统计或真实质量通过。读取同一证据的原本地integration ticket时校验project／完整binding／evidence／kind／automatic_merge及receipt引用；不存在即显示尚未记录，不创建issue／Task／合并。

显式`--artifact RELATIVE_PATH --evidence-sha256 SHA`只可选原bundle已列出的artifact。原安全路径拒绝symlink／越界；读取整个文件最多16MiB并核完整SHA，再按Unicode字符`--offset / --limit`返回窗口，默认12,000、最多65,536字符；只支持无NUL的UTF-8文本，二进制保留索引引用。不能用任意本地路径替换来源。每份原JSON最多1MiB，总响应最多8MiB，超限明确失败不截断；读操作无需SDK或服务，支持范围与原只读文件入口相同，原生Windows仍由自己的CI验证。

HTTP为`GET /api/projects/{project}/training/{experiment}/evidence`，可带artifact／evidence_sha256／offset／limit；不发送RPC、不写任何checkpoint、不运行comparator／runner、不批准／采用。返回runtime_status=not_queried、read_only；当前票据仅为本地事实，不证明Temporal终态或真实集成完成。C2／C3和真实F9d／B3另验。

## 当前进度

已核原perfctl archive、native collect_and_gate／authorize_release_and_create_task、原客户端与Temporal状态机及已有Task evidence实现，按上述职责拆片。C1首版实现已做，源码35通过／2可选web跳过；前两轮fixture与gate内容比较的测试预期失败已修并保留。最终包／实际入口与独立评审待；每步更新[交付](../delivery/2026-11-14-training-evidence.md)及主计划。

C1最终r2 573／两RECORD／283及当前源码一致，安装四suite46通过／38.99秒，真实CLI四操作、实际SDK-free、loopback HTTP六GET／零mutation、14／37原件保持与原monitor收尾、自身原模板approve已完成。首轮Host测试P2修后关闭，原两轮源码测试准备／预期及两私有入口脚本失败原件保留。新独立两轴最终原件补核与普通精确发布／自己的CI待。

最终新的独立两轴本地通过、开放0／0；原Host测试P2由r2关闭，报告链接已修，产品bca645…不变。原分组5仅collection389／1842，1453 deselected，不称执行。普通提交／推送、固定发布身份及自己的CI待，C2／C3另片。
