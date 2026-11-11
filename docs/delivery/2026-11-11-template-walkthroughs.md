# C6b/c：三模板使用旅程与实际后端验收

文档基线 `f9574895525e3c19bfe7094636c407359baed007`；[分片计划](../plans/2026-11-11-template-walkthroughs.md)。本片原行为样本开始于生产／测试／打包／CI内容相同的 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`。复用原非editable包，wheel SHA `aca2ea19761a0011d4b2b10851962733a5f77990dfc4f8e34450ad6901ecf9d5`；本片尚未改生产或测试代码。

## 当前出口

三域CLI准备、两个开发域当前页面v6创建／原ID读回，以及训练设计／测量审查叶实际调用已完成。完整读取审计、三份公开投影与通用指南已写；实际自身首审／聚焦复核各自范围保持，完整新独立出口通过、Spec／Standards开放0／0，两实证意见已关闭，W1–W5本地完成。c1f31fc已普通提交／推送、16个精确Git对象独立通过；自己的CI42964143325第四样本双OS七必要步骤success/completed，原评审者离线终核通过；独立Ref超时／作者smart-Git失败保持，另份作者官方HTTPS200同完整SHA经独立离线核验通过，按此范围精确交付终结。C6d及整个AC6/F6未关闭。原服务和浏览器均已停止，实际清理范围见下文。

## 原CLI与页面证据

通过已安装公共CLI执行21条命令：三模板复制，精确preset导入／show／preview／freeze-manifest／verify-manifest及本地Git项目登记／查询。三套完整包各自固定root、grant、manifest digest及preview SHA，不用浏览器JSON下载代替完整资产。创建夹具仅复制所需参考平台文件，不具备完整Linux服务环境；可信检查为惰性 `python -c pass`，只证明合同创建入口，不证明业务质量或完整六阶段。

原 `create_app` 与被动ASGI字节记录，真实页面两域：`repository-governance` 的knowledge-map／boundary-test，`large-change` 的contract／server／client／integration-tests，逐unit分配原同名work实例。所有writer显式选择Codex、current-container及理由；reviewer默认Claude只作为请求保存，没有认证或执行证明。默认选择work-units-v2，原任务定义schema-v2、正式信封schema-v6，精确manifest与合同预览绑定后发布；刷新页面按原任务ID读回。同两个任务再经实际CLI `task show` 读回成功。

页面驱动5.80秒、31检查通过、零page error；时间为自动化墙钟，不是运行时加速。69组原HTTP为65GET／4POST：66个200，三个原submission GET因创建环境未安装完整Linux运行时而返回400；原preview／create共四POST均200。未提交任务、调用Agent、启动六阶段或作批准。178个受保护文件、控制库物理文件与SQLite逻辑dump保持；新增20个运行文件恰为两个任务各七合同文件及意图／回执／锁。HTTP优雅退出0、有finally回执、原PID/starttime消失及端口关闭；浏览器命名close成功、六个实际采样进程无存活，不推导全部短命进程已采样。

保留三份私有驱动失败：首浏览器按中文label定位select超时，尚无检查或写入；第二份只等GET回复即修改尚未应用的模板UI，被原世代检查作废，尚无preview／create；成功版本等实际“已载入模板输入”消息后操作。首离线审计假设所有HTTP200而在真实400处退出1；修正为核精确路径／状态／错误正文后离线通过，未重放页面。[CLI／页面公开投影](evidence/2026-11-11-template-walkthroughs.json)保留命令、三包、原字节身份与省略范围；路径已代换，原输出／合同／HTTP仍在私有原件。

## 训练叶与后端实际调用

复用未经修改的完整训练preset manifest，在另一个独立项目调用设计叶 `root/analysis/design` 和测量审查叶 `root/measurement/review`。任务只要求为未来FP32逐行求和实验提出固定baseline／正确性／计时方案；没有真实设备版本、kernel候选、测量、trace或runner attestation。操作者将完整设计回复显式提供给审查叶，单叶入口没有执行图前驱或完整训练DAG。

|实际调用|秒|终态|实际范围|
|---|---:|---|---|
|设计／Codex|67.68|succeeded／exit0|只读实验设计提案|
|测量审查／Claude Code|9.62|failed／exit1|固定MCP预检成功，模型API报400，未形成有效审查|
|同输入测量审查／Codex显式回退|65.68|succeeded／exit0，request-changes|缺少真实实验测量，不能采用|

Claude原认证检查显示API认证已配置，但实际推理失败；不把认证状态当推理可用。原native错误为上游Bedrock `ValidationException: messages.1: system content must contain at least one block`。两个有界最小传输对照分别保留原bare设置、只增加非空显式system提示，6.53／5.88秒均返回相同400。最小任务也失败，不支持“由完整训练任务正文引起”的推断；非空提示对照也未支持此前空system假设。上游转换／模型路由仍未确诊；没有改生产适配器、放开ambient配置或新增隐式回退。

回退沿用户既有授权，原失败、原输入／prompt及实际绑定分别保留；相同输入摘要与提示SHA没有被后端覆盖改变。当前成功后端只有Codex，不能宣称实际双后端成功。三正式叶调用分别采见4／9／4进程，对照各自也保存采样身份，均无已采样存活；不证明未采见短命进程。

离线从完整manifest→准备／实际输入→实际stdin／协议prompt→原准入→完整不变内置包→整条结构祖先scope逐字核验。两成功调用各四份完整资料，共1,447／1,351B；原模型list完整列出全部URI，连续UTF-8实际read从0到null，零失败。Claude预检成功但没有原模型list/read及native-ready，不声明它已读完祖先。首审计错误地把完整材料preview与运行列表的metadata投影直接比较而退出1；原源／失败转录保留，修正逐字段比较元数据并另从完整资产重建scope后通过，未重放模型。

原后端自报设计input45,716（cached20,608已含）、output1,340、reasoning364单列；回退审查input48,540（cached34,560）、output1,472、reasoning516单列。Claude原终态input／output为0，不推导账单或免费调用；用量与页交付都不证明模型质量。[后端／完整读取投影](evidence/2026-11-11-template-backends.json)保留原输入身份、URI来源／连续页、用量及失败对照范围；省略原机器路径、请求ID、私有配置、原生流及提案全文，但记录原件字节／SHA。第一次探测命令曾在bash读取zsh配置阶段退出1，未启动probe；改由zsh读取后才执行上述两次对照，没有覆盖原正式调用。

## 文档及后续

[三模板入门旅程](../TEMPLATE_WALKTHROUGHS.md)连接现有安装／日常、训练、项目／组合与完整两参考手册；不会把当前机器状态写进通用指南。现有[工作流定义](../WORKFLOW_DEFINITIONS.md)开发域表改为默认work-units-v2／v6并指向显式v1／v5兼容说明。之后完成原件投影、实际自身模板、新独立两轴、本片精确交付；C6d继续核当前架构与平台边界。

真实自身结构模板首审171.01秒request-changes，实际范围为所选7个tracked文档增量（不含无需递归的旧片审查记账）、完整新增指南／计划／交付／两投影，以及选定完整驱动／审计／有界结果；大HTTP／合同／原生流原件未内联，未称模型直接读过。原输入／scope措辞“完整tracked文档diff”保留，其过宽表述按新独立C6BC-ST1／P3修正为上述实际范围，第三投影列出7路径及未包括的后续状态增量；没有重写原回执。指出指南漏写“载入所选模板”按钮P2，及task-mcp依赖／认证排在执行块之后P3。已在指南原位置补按钮并将准备顺序前移，无产品或新测试变化。首轮五scope／168,594B附件（22完整文件）已核实际连续UTF-8从0读到null、0失败，跨多字节窗口的base64保留同offset重读记录；四采样进程无存活。原生自报input997,190（cached895,360已含）、output3,931、reasoning1,759单列，不是账单／模型质量或独立错误率证据。后续聚焦R2只复核该文档增量，完整独立评审直接核全片及限定原件。

聚焦R2为130.97秒approve，仅关闭上述原两finding：八份完整文件／45,110B附件及五scope连续UTF-8到null，0失败；四采样进程无存活。自报input683,468（cached623,488已含）、output2,241、reasoning585单列。没有重复首轮大原件或声明最终整候选模型批准。[两轮真实审查投影](evidence/2026-11-11-template-self-review.json)完整保留原决策、解码结果、附件索引和实际scope，明确省略范围。

新的独立主轴另发现C6BC-SP1／P2：开发v6组合也依赖task-mcp，而原指南只在训练步骤解释其extra。依据原安装配方、services实际解释器及executor准入，已把依赖提升到开发／训练共用运行前置，给默认安装器实际Python命令、同executor环境要求与训练回链。静态导入／创建仍不要求模型或MCP，未改变生产依赖、profile或测试。此修正在R2固定快照之后，只由完整独立复核覆盖；原R2范围没有改写。完整独立出口、静态最终候选及精确交付继续。

## 完整独立本地出口

[新的fresh-context独立报告](2026-11-11-template-walkthroughs-review.md)核完整16份公开候选、71份投影来源身份及限定原件，Spec／Standards开放0／0，C6BC-SP1／P2与C6BC-ST1／P3均复核关闭。另直接核21准备CLI／2读回、三完整manifest／24内置包、69HTTP／31检查／178保护文件／20新增文件／逻辑DB及清理；三训练调用完整资产／祖先scope及两成功调用连续页、两个Claude最小对照；两轮自身模板的完整输入／原结果／用量及实际读取全链。768／123等私有核验文件数说明字节／结构覆盖，不冒称全部语义检查。没有重复模型、服务、页面、打包或产品测试。

最终只剩本片状态记账、静态候选冻结、普通提交／推送和自己的CI／精确远端核验；原非editable439文件／两RECORD／283冻结沿未变源码复用，不把文档当新运行代码。C6a自己的CI已独立终结，可以在本片出口完成后推新候选。后续C6d统一当前架构／平台及两手册导航，再按总计划F7–F10／G1推进。

## 提交与进行中的精确交付

普通提交／推送 `c1f31fcfa38ac25085e287c507377be422786026`，单父f957489。作者及原评审者分别核16个Git blob／100644与ready-r1完整字节一致；生产、测试、scripts、CI与pyproject对象保持。原评审者唯一一次无凭据官方Git Ref HTTPS请求连接超时，HTTP0且无正文，未取得远端SHA或TLS成功证据；原件保留，没有将失败写为成功。作者随后普通 `git ls-remote` 也因TLS异常退出128，没有取得远端ref，未改传输配置。

自己的[CI42964143325](https://github.com/626619403/Ergora/actions/runs/42964143325)前两官方API样本为in_progress；第二份双OS build／reference身份步骤均成功，native回归进行中、Windows安装升级步骤pending。原runs/jobs正文和字节摘要均保存，不用旧提交CI代替。第三份Windows已成功、Linux仍in_progress，第四份双OS七必要步骤success/completed；四份原样本全部保持，交原评审者离线终核，不重跑CI。作者另作一份有明确身份的官方Ref HTTPS采样，05:33:09.698136→05:33:10.713747 UTC、合法TLS200，429B原正文SHA256 `3f041341aaed4e6d424c96056183202357b302b78621fe76258c807cef2dfd6e`，远端分支同完整c1f31fc。它使用原默认网络环境、无凭据且有独立原件，不将独立评审者先前无代理超时改写成其直接网络成功。C6d可完成本地出口后再普通推送。


原评审者已离线终核四份CI样本／八个原body及作者Ref原正文／元数据／脚本，精确候选／分支／run／job和七必要步骤／状态连续性相符；原独立超时及作者smart-Git失败字节保持。[原同片报告](2026-11-11-template-walkthroughs-review.md)已追加实际结论。W6与C6b/c按作者远端采样＋独立离线核的范围终结，不授予C6d或AC6/F6完成。
