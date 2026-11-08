# AC3b.2b：完整输入的受限单叶调用

日期：2026-11-09。状态：IV1–2已实现验证，初版真实小任务成功；新独立R1三项已修并经R2关闭；r2真实完整自审request-changes新增两项，已按所有者修正，r3真实再审approve、生产/包及深度修正版回归通过，独立最终复核与精确交付待收口。AC3b.2a已完成自身CI与独立远端收口。仍在 `refactor/architecture-foundations`，源码基线为 `eee09efcba093839dba5407c474a7a5b46a3a2a0`，不将输入包验证当作后端验证。

## 本片范围

把已核验的完整输入真正交给单个原生后端，保存独立运行及精确输入副本；保留项目/六阶段的现有执行入口。调用不执行图前驱、不自动解析未来端口、不产生正式候选或批准，不使用第二套调度器。

首个模式为明确的 `text-only`：完整祖先和自身的指令/上下文、操作者任务进入模型；没有文件、命令、搜索、网页或MCP工具，Skill附件保存在输入中但不能通过本模式读取或执行。含写入、shell或网络请求的叶子在调用前拒绝，不能把该模式当作可编辑仓库的执行者。文件资源与最小任务MCP沿AC3b.3接入；OS/网络强制矩阵仍属AC3b.4。

`composition run-input PROJECT DIRECTORY --timeout N [--backend codex|claude-code] [--model MODEL] [--codex-config FILE]`：默认使用精确定义后端，显式覆盖只作用于本次调用并保存请求/实际binding和原因。原输入的 `execution_authorized: false` 不会被改写；这是操作者主动发起的独立调用，不等于正式批准。用户已经授权Claude不可用时改用Codex/ChatGPT，实际验收按该授权选取并记录，不能静默改写定义。

原 `agent_runs` 持久记录消费已核输入；模型前重新核当前Agent准入、完整副本身份、模式能力及权限上限，过期后端或损坏输入明确失败。状态区分准备、调用成功/失败/超时，原始stdout/stderr、完整实际prompt及结构化结果可通过已有Agent运行列表/输出查看。原输入目录不变，运行副本保存到State的runs目录，复用原完整备份。

## 所有权和配置

- `workflow_definitions`继续只拥有静态材料、完整输入准备与核验。
- `agent_runs`拥有项目范围、输入副本及持久生命周期；复用原State的Agent运行表和既有结果schema，不新增DB或执行引擎。
- `agents.invoke`继续拥有协议和进程生命周期；新增明确的受限模式参数，原调用默认行为保持。
- `agent_backends`在原ABC和局部注册里拥有各自模式准入和原生命令，顶层不按厂商分派。command/mini等尚不支持的后端在调用前拒绝。
- Codex专用配置文件仅读取模型/服务提供者的推理设置；忽略其中的工具、Skill、MCP、审批、sandbox和其他工作区设置。凭据沿环境变量或原生认证引用，不进入定义或公开报告。Claude继续使用其原生认证，关闭用户/项目配置、原生文件命令工具与ambient MCP。

原生选项只表达模型工具和上下文的选择；不提供OS隔离，不阻止当前用户的其他进程，也不保证模型理解全部内容。模型服务本身的通信属于运行基础设施；叶子network指工具对外请求。后端系统提示/输出schema的容量不能从user prompt字节预算推导。

## 可验收节点

- [x] IV1：当前准入、受限后端合同、持久精确输入及显式后端选择；旧Agent调用不变。
- [x] IV2：已安装原生CLI对本地合成协议的完整prompt/工具投影；Codex与Claude分别记录，拒绝越模式权限及不支持实现。
- [x] IV3：非editable包、真实已配置模型的一次单叶调用与可读持久记录，失败/回退不隐藏。
- [ ] IV4：新的fresh-context需求/结构审查并解决finding，更新手册/计划、普通推送和必要精确CI。

只补足行为变化的回归，不为低风险文案加CI。结构和协议选择以现有真实消费者为准；后续MCP、批准链和嵌套调度分别保留自己的出口。

## IV1本地实现

在原AgentBackend ABC中加入可明确拒绝的text-only模式；Codex/Claude原生参数由本实现拥有，其他实现不承诺支持。Codex仅读显式文件的推理字段，关闭ambient规则、Skill、hooks、插件、apps、多Agent、shell和网页；Claude使用safe/restricted、空工具、strict空MCP与空setting sources。响应/交互类原生工具可能仍保留，不称作OS隔离。原 `agents.invoke` 默认不选此模式；原sandbox行为和结构化结果校验保持。

`agent_runs.run_input`核完整输入、当前定义及实际binding，拒绝写/shell/network叶子，保存经完整核验的运行副本后才调用。项目仓库不作为cwd；使用新空目录，原始prompt、实际argv与结果分别保存，复用既有Agent运行表及读取。显式backend/model选择和理由绑定本次运行，失败/超时仍持久记录，CLI分别以1或准入错误2退出。输入包自身不被改成已批准。

源码受影响五套初轮44 passed/6可选环境跳过、1失败：失败为新测试注入copytree时未接受递归位置参数，未进入模型；已修夹具并保留原日志。新9例修后全部通过，覆盖两原生adapter完整输入/显式覆盖/独立持久读取、3种权限拒绝、不支持command、复制篡改拒绝、超时与不完整结果。既有已通过用例未因纯夹具参数修正重复整套运行。原生CLI请求和真实认证仍待下个节点。

## IV2原生协议与IV3安装包

用实际安装的Codex0.166.0、Claude Code2.1.312调用本片CLI，连接本机合成Responses/Messages服务，不使用真实凭据或托管模型。四次调用均成功交付精确完整prompt并返回合格结构：两后端各一正例、一次向模型返回未提供的命令工具调用的反例。Codex请求只含request_user_input，Claude只含StructuredOutput；伪造exec_command/Bash均未执行哨兵写入，第二次模型回复正常完成。父目录放置的ambient规则标记均未进入请求。原始请求、进程回执及摘要保留在忽略checks的native-journey，合成结果不称模型审查通过、认证通过或OS隔离。

新Python3.12.3非editable包实际导入site-packages，受影响五套47 passed/6可选Forge/mini环境跳过；360源/wheel/安装文件逐字及283冻结身份通过。wheel SHA256为 `c548b64ad446f64085a1b5aaccee393a00c9b65ba76176cbdb4aff19bbcaddd1`。源码另外两个新增边界均通过：历史输入不能绕过当前准入，错误provider表在调用前给可读失败。初轮包检查误在pip安装完成前启动，收集阶段遇未写完的schema文件，未执行测试；原iv3-wheel-tests.log保留排除。安装完成后有效日志为iv3-after-install-wheel-tests.log，身份检查也在安装完成后执行。没有以并发安装期间的半包报错归咎生产代码。

真实配置的模型审查已启动：使用安装包的structure-review模板、完整候选源码和原需求，先Claude限90秒、再Codex限240秒；原始回执、精确输入与保护文件身份分别保存。该轮随后均超时，结果见下文；当时未登记认证、approve或本片独立审查通过。只读supplied source的审查不能冒称命令/全仓运行检查。

## 真实模型结果与独立初审

初版87,840字节完整代码输入的Claude90秒、Codex240秒均超时，CLI1、运行和输入快照如实保存；Codex仅有两条中间说明，未返回合格结构，不能算审查通过。随后用同一安装包/structure-review入口和完整的3,630字节小候选任务，Codex实际配置在28.78秒内成功返回合格approve；输入、副本、protocol prompt和进程stdin四份字节一致，SQLite/CLI记录与result SHA一致。原始证据在hosted-small-call.json及对应运行目录；原独立者另只读核验这些字节和记录。这个结果证明真实认证及独立单叶入口可用，仅审supplied tiny candidate，不称全仓审查。

[新的独立R1审查](2026-11-09-composition-invocations-review.md)确认三项P2，其中两项合同缺陷及一项收窄后的性能/结构启发式；原文与UI消费者事实更正保留。接受并按原所有者修正：

- C1：Windows gate最终以binary UTF-8发送stdin，避免LF/CRLF被TextIOWrapper转写；保留原Job进程组/输出/取消实现。新增真实进程对照，覆盖中文、LF、CRLF、裸CR及保存文件与子进程收到字节的SHA；Linux已过，原生Windows交本候选CI验证，机制探针不冒充Windows运行。
- C2：Codex配置序列化对TOML date等JSON不兼容值抛可读ValueError，复用原失败持久化；不由CLI或run层吞所有异常。日期回归核native未启动、failed/finished/error可读，不再留running。
- S1：仅本片新增context.resources去正文text，保留身份/来源；完整正文仍在核验快照和实际prompt，已有verify-input --material按需读取。没有新API/数据库迁移。原通用UI可以显示整document，不能称其没有正文消费者；修正针对每次dashboard预取100条完整正文的成本。审查量化为900KB正文×100条约90MB额外JSON，非物理IO/整体延迟实测。

r2包含原四份生产源码加进程gate与新测试。Python3.11.15源码、Python3.12.3非editable包同六套均49 passed/12 skipped；12项为6个Forge/mini可选环境、6个原生Windows测试在Linux跳过。360源/wheel/安装及283冻结身份通过，r2 wheel SHA256 `98d838a54ee7353868cf0ac827a3ee744d0514a7c835107fa9c5f249e189bd9f`。原生协议4例保持初版原身份，不把它们称修正版重跑；r2未改其有效配置的命令投影或Linux输入路径。

修正版真实structure-review已从新安装包启动：包含原需求、完整五个相关源码/测试文件及CLI变更上下文，显式Codex/ChatGPT回退、预算600秒，不降低推理配置；原始失败保留。该轮随后返回request-changes，结果与修正见下文；未登记全仓审查通过或正式批准。最小任务MCP由独立后片继续。

## r2完整自审与r3修正

r2安装包真实Codex/ChatGPT structure-review在387.58秒完成，request-changes；输入摘要`dc32eb2418d3e99983c7bb9e0ff7dc9330fc35b8ac3106dd13b9f77c412cc294`，prompt SHA256 `58e3c49fa9196c0efdcca5fcbad33117860ee685026c85424c476f31be9efdf0`，result SHA256 `6c4ce48ee304a8c20447cdbeb54dd7335fd3afe24c9e47d5525b07231ba90dc8`。原始回执/源码保护身份保留在r2-hosted-review；这是对所供源码的静态审查，未运行命令。独立R2已关闭原三项，不代表后续两项自动通过。

接受两项并按现有所有者修正：processes在Windows executable解析后、实际启动前记录argv，Linux保持原PATH语义；agents在已有结构结果错误处理捕获RecursionError，复用failed/finished持久路径。没有新增调度器或通用异常框架。补实际命令/参数/Unicode进程对照及过深JSON CLI非零、失败终态回归；原生Windows仍须本片精确CI。r3最初两次命令误选不存在的测试文件、收集前退出，原日志保留，不算执行结果；随后按实际文件选取受影响六套。

r3源码Python3.11的六套进程重点检查47 passed/16 skipped；安装包Python3.12为46 passed/1 failed/16 skipped：2000层JSON仍可解码，测试要求recursion失败的深度不足，原日志保留，生产已给failed/finished。此前状态同步误写成双47，现明确纠正，待加深fixture后复验。本次纳入test_processes及架构边界，和r2六套清单不同，不合并/继承49项。跳过6个可选Forge/mini、10个原生Windows合同；Linux真实字节/argv对照通过。360源码/wheel/安装文件及283冻结身份保持一致。当前r3真实完整模板审查已启动，独立R3另复现了R2两缺陷，待修正后复核。

## r3本地收口

真实安装包structure-review在239.98秒返回approve，两轴无阻断finding；精确58,029字节所供源码输入摘要`d94c1e110e2e99eae7fef1e23780408ac8f19e543f36ac9667d645669fcd57b7`，prompt SHA256 `ea2e007377acf381bea8941db1ee5e56c6e96319739de6e41cb8e37596c66a13`，result SHA256 `c7bb8e22e3d1c39535d21ba97481a1a95d8227f2f0846c522e83fd79064914b7`。该检查未运行命令，未包含所有六阶段及输入验证器实现，不能称全仓证明；原R2 request-changes和两个timeout保持原样。原生Windows运行仍由本片候选CI检验。

随后只将深JSON夹具由2,000改10,000层，Python3.11源码和Python3.12安装包的该例各1 passed；无需重跑已经通过的其他46项。生产源码保持真实自审及wheel身份，r3 wheel SHA256 `ea7f45f3818e23f08b1da86b40420bdf6f9f0ee88b8f5d9d4dce9d3932eef961`。因此当前六套的47项均有通过证据，Python3.12最初1失败及修正重验单独保留，不把分段结果写成另一次整套47通过。独立R3另用真实native夹具核CLI1/failed/finished及实际Windows命令记录分界，机制探针不冒充原生Windows。下一独立最终scope核对、普通候选推送及自身CI。

新独立R3最终本地复核通过：5项历史finding全部关闭，11项scope/差异/真实字节与回执独立核一致，无新finding；下一仅普通候选交付、自身双OS CI及独立即时远端终结。两份MCP后片文档不进入本候选。
