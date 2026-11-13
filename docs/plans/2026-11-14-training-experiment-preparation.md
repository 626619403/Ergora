# F9b4c：原实验精确准备与部分发布恢复

日期：2026-11-14。基线 `80236fe8957c0704a3c73c7ea1440f7f288ff563`；[准备总计划](2026-11-14-training-preparation.md)。前片runner最终本地及固定发布两轴通过，已普通推送、23个Git blob／完整Ref一致；自己的CI `43523861953`八job／30必要步骤成功，原结构轴终核通过。前片CI独立收口，不借其成功验本片。

## 原事实与范围

原 `agent_platform.training.prepare` 验完整draft、runner／窗口、两Git commit、baseline和比较器，补canonical commit别名与项目／runner／窗口，然后依次不可变发布全局manifest、项目manifest和spec。spec的manifest URI及binding直接引用全局manifest真实字节。中断或冲突会留下部分文件；三文件不是一个原子事务，不能用“请求失败”断言零写入，也不能把队列prepare或登记当训练成功。

保持283参考文件，实际发布仍直接调用原prepare及其writer／registry lock，不复制字段、baseline、别名、窗口或Binding算法。复用 `_TrainingProject`、有界reader、process monitor和本地非阻塞file_lock；控制DB只短时预留项目revision，无服务或GPU，无第二实验表、调度器、批准或训练执行器。

## C1：CLI／HTTP准备与恢复

1. `experiment-preview` 接完整draft、项目专用runner ID、可选排队加执行窗口。只读原注册／baseline／runner并固定字节SHA，核项目和Git根；隔离子进程把原native CONFIG／TRAINING临时指向私有staging，复制原baseline／runner后调用原prepare，finally恢复全局。按真实执行根映射spec中的manifest URI；实际字段、manifest字节和binding由原owner生成，暂存内容不冒充已发布原件。CLI原draft和每个原生文档各最多1MiB。
2. 预览显示完整规范化manifest／spec、原baseline／runner、三个目标、项目revision和完整canonical `preview_sha256`。确认同时冻结项目／home／execution／注册身份、完整request、原source内容／字节SHA及精确发布计划。保存的控制意图在原state的`ergora/training-preparations/EXPERIMENT_ID.intent.json`；这是同原生实验的恢复checkpoint，不另立实验权威。聚合intent容量最多16MiB，不截断。没有随机新实验ID或外部发送attempt；本操作没有RPC。
3. `prepare` 核当前revision与精确预览SHA，原三目标及registry lock都先过原safe_file；新意图先不可变发布，然后直接原prepare。成功后逐件对照原文件与冻结计划，读取原训练reader复核binding。已有本工具意图时重复prepare只返回其现状，不自动继续部分发布。
4. `preparation PROJECT EXPERIMENT_ID` SDK-free读取原意图与目标文件，分别显示尚无意图、已保存意图未发布、部分发布、完整准备或冲突；不查服务、不修文件。外项目占用全局实验ID不展示其材料。占用检测限于本项目manifest、共享global manifest／spec及同ID准备意图；不扫描其他项目仅存的manifest来重建人为删除过的全局登记。没有本工具意图的旧原生文件只供原list/show查看，不自动接管其不明准备过程。
5. `resume-prepare` 要求当前revision与原intent SHA，重核原身份、原source字节和每个已发布文件，所有缺失／已存在内容均须能由同一冻结计划解释；重建staging验证同一原prepare结果后，才显式调用原owner补齐原文件。已完整且尚未start的同意图可读回，原字节保持；已有job／fence／start时显式resume拒绝，status与相同prepare仍只读。不同内容、源漂移、孤立原文件或已有job／fence／start操作明确拒绝，不能覆盖、删除或换ID自动重试。

原生prepare的`max_run_seconds or default`会把显式0／False当默认，支持入口须区分省略与明确无效值；其他窗口范围继续交原owner。原runner中布尔schema与正式start不兼容的问题沿前片合同拒绝，不复制其整套validator。

CLI和HTTP沿同一training应用入口；准备／恢复只在Linux／WSL2并需`ergora[temporal]`，无需服务。读取意图不导入SDK；不因此扩大原生Windows支持。现有baseline／runner及start／cancel行为回归真实受影响范围。

## C2：训练页准备入口

C1安装、实际CLI／HTTP和新独立两轴收口后另片接页面，不让发布算法移到浏览器。完整draft／runner／窗口预览与摘要确认；按稳定实验ID读取原checkpoint及三件发布事实，再用原intent明确恢复。编辑／切项目使旧预览和迟到回执失效，双击一次，不把完整准备当已经提交或训练成功。复用现有视图生命周期，按实际恢复算法内聚组织局部面板，不扩大全局状态框架。

## 可验收节点

|节点|验收证据|
|---|---|
|C1a完整原预览|真实原owner生成的manifest／spec与最终发布字节／binding一致；预览不创建真实state／config，错误baseline／比较器／Git／窗口沿原owner失败|
|C1b部分发布与同意图恢复|真实子进程在intent、全局manifest、项目manifest、spec各边界中断；新进程读现状，同意图显式恢复；原件／不同内容／共享ID／源漂移保持，丢成功回复可读回|
|C1c共用入口与精确交付|原CLI／HTTP、最终noneditable包／两RECORD／283、受影响测试、实际原件及收尾、自身原审查模板和新的fresh-context需求／结构两轴；普通提交／推送、精确Ref及自己的CI|
|C2页面交付|实际浏览器确认与恢复、编辑／切项目迟到／双击／失联／三视口，受影响原表单回归；新独立两轴、自己的发布／CI|

每步更新本计划及[交付](../delivery/2026-11-14-training-experiment-preparation.md)。当前C1首版已实现：共享有界serializer、原prepare暂存预览／精确确认、原意图与四边界显式恢复、CLI／HTTP及分组5接线。源码首轮38通过／1失败（外项目runner在缺baseline时先报缺文件），已将归属检查提前；修后39项通过／64.93秒。noneditable r1包571产品／两RECORD／283已核，安装r1六suite65通过／212.14秒，真实CLI11操作／HTTP丢回复读回／实际SDK-free status／原8件与收尾已通过；自身原结构模板15完整文件approve，新独立两轴在审。C2仍待C1。后续F9c接原evidence SHA批准／集成复验，F9d与真实B3仍需实际环境／资产／GPU及可信oracle，不以本地合同代替。

## 独立评审后的合同修正

需求轴指出完整三件时publish提前返回、绕过已有job／fence／start检查的歧义。将原ensure_unstarted移至完整早返之前；重复prepare仍只读，显式resume统一拒绝已有执行／提交checkpoint。补三种checkpoint参数化回归，最终r2包571／两RECORD／283与当前树逐字一致，受影响15项69.67秒、真实CLI／HTTP／SDK-free及原件收尾、自身模板最终approve已补，新独立两轴最终本地通过、开放0／0，普通发布及自己的CI待；不扩大跨项目孤儿扫描范围。
