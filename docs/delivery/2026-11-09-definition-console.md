# AC5 C1：定义库与静态预览控制台

固定基线 `d7ad71d37a1a3223b0cab3c93cbad1b522320377`，分支 `refactor/architecture-foundations`。[AC5分片计划](../plans/2026-11-09-composition-console.md)为恢复入口；本片仅C1，F6编辑/完整AC5/AC6仍在后续。

## 范围和所有者

在本地Web控制台增加Agent/子工作流库的查询、精确版本详情、显式随包组合导入与原静态preview。`web`提供薄传输，原`agent_definitions`、`workflow_definitions`拥有所有身份、导入、权限/资源和预算计算。库属于控制目录，未注册项目也可访问；浏览器不复制validator或把默认后端请求显示为实际可用。

新增前端视图拥有库加载、详情选择和preview请求世代；使用原UI模块与文本DOM。先提供可访问列表、原定义正文和全部实例/资源来源，关系编辑和图形展开归C2–C4。显式导入不安装或认证后端、修改项目授权、采用可信容器、发送模型请求或启动服务。预览上限仅供静态校验，不等于项目批准。

## 节点状态

|节点|实现|验证|审查/交付|
|---|---|---|---|
|C1a同一用例HTTP入口|7个薄入口已接通|R4新3项及原Web/架构共22项通过/18.28秒|源码两轴复核通过|
|C1b全局库与继承预览页面|新视图和无项目导航已接，两个真实渲染缺陷及C1-S1竞态均最小修正|R4原空库、完整旅程和原竞态转绿|源码两轴复核通过|
|C1c安装包/真实浏览器|R4最终源码/wheel/install435/283一致|22项及空项目三域导入/全文/错误/迟到回复/下载/390px键盘/HTTP重开通过|待独立完整终核|
|C1d自身模板/独立终核/精确交付|实际自身模板完成，独立完整终核通过|178.21秒approve，21源/281802字节完整读取，5公开JSON/2截图已独立核原件；24文件两轴通过|本地出口完成，提交/自己的CI/HTTPS仍待验|

验收须覆盖空控制目录无项目、三域显式导入与重试、CLI/HTTP身份一致、历史精确版本读取、完整祖先资源和权限来源、错误与迟到回复、窄屏/键盘和HTTP重开。复用原相关回归，不增加新的CI作业或镜像所有原validator测试。按实际被支持的平台和浏览器记录；本片不需要GPU/训练或新服务编排。

前片AC4.4源码/安装包/双审查已本地通过，普通提交d7ad71d的自己的CI/HTTPS另核；本片不能提前借用其结果。公开资料不含本机路径、凭据或认证状态。

## 首轮安装与C1-B1

R1非editable包 source/wheel/install **435文件逐字一致、283冻结保持**，wheel SHA `ff925990f7ba7f5aa05d86d5830b0ea85ffa0263798f2d7c4598282fa099b175`。新增3项HTTP旅程与原Web/架构合计 **22 passed /19.07秒**：空库三域导入重试、CLI/HTTP精确身份、完整preview、不越权限和历史读取/当前准入分开。Node语法检查通过，没有将其视作浏览器运行证明。

实际原R1安装包/空控制目录/无项目的首次浏览器点击发现 **C1-B1**：`detailView`的空库/加载/错误三个分支返回单个DOM节点，调用者统一展开数组，因此抛`TypeError: detailView is not a function or its return value is not iterable`，组合页没有显示。原日志与真实点击保留；同一原包上的精确自动loop等待该页标题在2秒内出现，实际红为TimeoutError。此为确定性的直接返回类型错误，已有原调用栈与原包反例，不做无信息的多假设或性能探测。

最小修正仅把这三个分支改为节点数组，保持正常详情分支和所有HTTP/定义用例不变。原R1 wheel、console、snapshot、red-loop与cleanup保留；原浏览器及owned HTTP按原PID/starttime正常退出、端口关闭。R2重新构建/独立安装后运行相同loop，再继续完整旅程；不增加不能覆盖DOM执行的字符串断言或新的CI作业。

## 修后R2与当前R3

R2包435/283身份通过，wheel SHA `a8cbaf5f209a0312047b4ececd6ad8cf909b9f108fd72028ed6e81637f634311`，同22项 **22 passed /19.63秒**。相同真实空库loop转绿；新snapshot额外发现顶层可选null被`replaceChildren`转成文字`nullnull`。最小本地修正只过滤最终视图数组的空项，没有改公共DOM工具。R2的原snapshot与包保留，owned浏览器/HTTP按身份关闭。

R3重建并独立安装，源码/wheel/install **435文件逐字一致、283冻结保持**，wheel SHA `3211c90616c1a9dd37af558d16fb5cb3a49f30c1157d3a27f6a5bef2caa65eb0`。相同22项 **22 passed /18.99秒**。实际空库浏览器及完整导入/预览/竞态/持久化/窄屏旅程在验；此时尚不声明完成。用户手册、Agent/Workflow定义手册和当前架构已接入全局页面说明，完整包导出与正文下载分别说明。

## C1-S1独立竞态发现

R3实际浏览器已通过三域导入和幂等重试、13专家/11工作流、资源全文、19实例preview与下载、JSON/权限错误保留文本、刷新/重载库保持、旧详情/旧preview/改选择后旧install回复忽略。竞态脚本首轮把kernel专家的职能误写为implementer而找不到选项；原脚本失败保留，依据原定义kernel-tuner修正脚本后上述旅程通过，没有修改产品来满足脚本。

新独立两轴发现 **C1-S1**：在当前工作流A上启动组合B导入，用户未切换定义但修改上限；原导入只比较详情请求世代，完成时仍自动打开B，清空A的修改。独立真实源模块离线复现后，作者在原R3实际Chromium/原HTTP安装包中延迟成功install回复验证，**input_preserved=false、selection_preserved=false**，原断言红及原包保留。

最小源码修正只在导入开始同时捕获预览世代，自动选择新根须详情和预览世代均未改变。期间编辑上限或明确发起预览都会保留当前会话；没有新状态层、validator或HTTP合同。修正后重新构建R4，再运行同一原浏览器场景、原相关检查与完整旅程，待同片独立复核。

## R4最终安装与浏览器验收

R4非editable wheel SHA `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`，源码/wheel/install **435文件逐字相同、283冻结保持**。同一新3项HTTP及原Web/架构合计 **22 passed /18.28秒**；Node语法、diff检查通过。没有新依赖、CI作业或存储迁移。

实际Chromium/本地HTTP/空持久控制目录、无项目：同一空库首次点击通过；三域导入及训练重复导入保持精确身份，13 Agent/11 Workflow版本可选。专家自身资源、19实例开发组合全部资源/提示正文逐项核与原preview相同；正文及preview下载JSON与原定义/原owner逐项相同。JSON解析失败、祖先权限拒绝、受控库失败及重试均保留当前文本；刷新、切页保留选择和未提交上限，重载保持库。私有下载检查首轮误把Path传给要求State的get而直接TypeError；修正调用方后通过，未修改产品。

延迟真实详情、preview和install成功回复后，新选择及上限不被覆盖；在旧preview在途编辑上限会重新启用按钮。**原C1-S1同一实际浏览器脚本**在R4记录`input_preserved=true、selection_preserved=true`；新独立Spec/Standards也以原真实源模块复核安装等待、库刷新等待和无编辑正常跳转，开放源码finding0。原R3红不覆盖。

390×844下页面document宽390，无整页横向溢出；较宽的实例表在自身容器滚动。实际Tab进入预览、Enter发起成功、Space展开实例通过；1440×1000与窄屏截图已逐张检查。这里只验当前三套默认组合，不将该测量当C6大图上限或全平台浏览器性能。

原owned HTTP按PID/starttime核后正常停止，在**同一端口与同一控制目录**从同一R4安装包重启；13/11完整库及bootstrap逐项相同，浏览器重开后训练9实例预览成功，仍0项目。浏览器事件记录未见未处理JS异常；权限失败与受控库失败的400分别为预期。服务和浏览器清理单独记录，不触碰模型自审进程。

公开脱敏原件：[R4包/回归及历史包身份](evidence/2026-11-09-definition-console-package-r4.json)、[R4完整浏览器与原红/修后绿](evidence/2026-11-09-definition-console-browser-r4.json)、[桌面截图](evidence/2026-11-09-definition-console-desktop.png)、[窄屏截图](evidence/2026-11-09-definition-console-narrow.png)。R4浏览器/HTTP最终按保存身份退出，原端口关闭；清理证据与同端口重启分别保持。

## 实际自身模板

使用最终R4安装包导入真实内置治理组合，从其中的`ergora-structure-reviewer`及`ergora-structure-review`创建显式1.0.1证据修订；原1.0.0不变。准备完整manifest后移除原两定义库，由独立完整输入启动实际任务MCP/Codex。用户已授权Claude不可用时回退；本次不改共享默认后端或声称模型错误独立。

真实调用 **178.21秒、succeeded、approve**，Spec/Standards分别无新增实证缺陷。输入包含全部本片源码/测试改动及选定邻接所有者，共21源、完整原红与R4验证。原生流先读40KB探针，再从offset0连续14页交付 **281802字节至null**；全部15次成功返回逐字核原材料；原流另保留1次早期read失败（使用短路径，工具仅返回泛化错误），随后按完整资源路径读取成功，21源仍同一身份。初版审计器只接受无重读的单次遍历，因此拒绝重复offset0；原失败日志保留，修后的私有审计核每个原返回及随后完整连续遍历，没有重跑模型或编辑原流。

公开[输入身份](evidence/2026-11-09-definition-console-self-review-identity.json)、[原意见](evidence/2026-11-09-definition-console-self-review-result.json)、[完整读取审计](evidence/2026-11-09-definition-console-self-review-reads.json)分别归档。公开意见为原JSON解析排版，identity中的result_sha256指原生字节，不能与公开文件SHA混用。模型未执行仓库测试，也未代替原owner批准；本候选自己的CI和明确HTTPS远端仍是待验交付门禁。

## 最终本地门禁

[新fresh-context独立终核](2026-11-09-definition-console-review.md)及分别独立Spec/Standards复核通过，C1-S1关闭、开放finding0。主审核24文件完整范围、R4源码/wheel/install435及283固定Git blob、全部实际浏览器/原红/修后绿、下载/重启/清理、五JSON/两截图逐项脱敏；实际自身模板的原manifest/input/run与原MCP流均核原件，未重复运行模型或全组测试。

冻结快照后仅本报告/计划和审查报告允许状态增量，源码、测试和公开原件不漂移。最终静态 **11份Markdown/208个本地链接和锚点/94条命令parser通过**，diff检查通过。C1本地出口完成，准备普通提交推送及本候选自己的必要CI/明确HTTPS远端核验；AC5整体、C2–C6、F7–F10/G1与训练闭环不提前标记完成。

## 自己的 CI 终态

61ccc2c 的 [CI42612128319](https://github.com/626619403/Ergora/actions/runs/42612128319) 已终态 Failure，Windows 四必要步骤通过，Ubuntu 研究超时测试的耗时浮点精确比较失败；实际 timed_out 正确。原独立 HTTPS 已核同完整 SHA，原失败保持，[仅测试精度修正](2026-11-09-deadline-precision.md)单独取得自己的新候选门禁，不将本地验收改写为原 CI 成功。C2 产品改动仍留本地。
