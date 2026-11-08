# AC3b.4：能力矩阵与调用准入出口

日期：2026-11-09。状态：本地实现、发行定向、新独立复审及真实自审通过，精确提交/自身CI待完成；基线`ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`为[任务MCP](2026-11-09-task-mcp.md)已完成的精确候选。恢复时先核总计划、Git实际状态及本记录，不能沿用前片验证结论。

## 行为与范围

为已核完整输入提供一个不调用模型的能力检查入口，和真实单叶调用共用当前准入。报告保存请求的后端、实际选择、显式覆盖原因、完整结构祖先权限链、所供grant上限、必需资源来源，以及读取/写入、模型shell、模型工具网络、任务MCP、资源装载及宿主隔离的实际支持范围。按`enforced/advisory/unsupported`区分，并说明每项保证的作用范围。

能力报告是实现合同与本次有效配置，不是认证、健康、模型质量或原生CLI版本实测的替代。静态grant仍是操作者所供组合上限，不能误称已接项目正式批准。必须说明基础设施写入、stdio子进程及推理网络仍然存在。普通native Agent和旧六阶段不改变；默认text-only保持，task-mcp仍只读固定声明资源。

已有所有者：`workflow_definitions`核完整图、祖先权限和全部必需材料；`agent_backends`在原ABC seam拥有各后端的调用合同及差异；`agent_runs`组合当前准入/项目身份/运行记录；CLI只负责参数及结果。避免新增全局registry、第三套权限模型或在上层按后端分派。

## 验收节点

- [x] CP1：确定能力字段和现有调用链共享位置；保持配置请求、有效上限、支持保证和环境可用性分别记录。
- [x] CP2：CLI只读检查与真实run共用准入，运行保存同一能力报告；不支持的必要能力仍在模型前拒绝，检查不创建Agent运行或启动server。
- [x] CP3：高价值合同回归：完整祖先链、越权/读不到必需材料、超容量不截断、Skill冲突、后端sandbox不能扩权、显式后端覆盖及两模式差异。复用已有充分回归，不重复同义测试。
- [ ] CP4：非editable包检查、手册、fresh-context独立审查和自身真实review模板审查；普通精确提交推送及自身必要CI。

后续[AC3c](../plans/2026-11-08-agent-composition.md)把递归manifest及这些实际有效信息纳入正式创建/批准身份；AC4再接多成员、同候选审查聚合及Temporal嵌套。本片不将独立检查或受限单叶调用称为正式批准或完整嵌套执行。

## CP1拟定接口

增加`composition check-input PROJECT DIRECTORY --mode ... --backend ...`，复用`run-input`的选择参数；不接受会暗示已经运行的timeout。初版不接受推理配置，后经自身审查采纳改进：可选`--codex-config`也经同一后端解析，以便在创建运行前拒绝本地可判定的无效配置。检查既有State项目和完整输入，复用当前定义/后端准入及SDK存在性检查，不创建run、不复制scope、不启动server或模型，也不探测认证。

在`agent_runs`抽取有两个真实消费者的准入所有者，返回已核材料及可独立显示的准入文档。`check-input`返回该文档，`run-input`在同一选择上增加运行ID/终态并持久化；不再各自拼一套权限规则。原模式拒绝及当前sandbox检查保持。报告展示所供grant及root到leaf权限链；read范围是许可上限，固定正文/Skill指令才是本片的必需材料，不能把read里出现workspace解释为已提供workspace工具。

后端通过原ABC seam提供本实现的能力描述；具体CLI差异仍归实现，共用受限模式描述的部分可有局部共享函数。能力分为完整内联、固定资源、workspace读取、写、模型shell、工具network origin、任务MCP、外部MCP、后端sandbox及宿主隔离。`enforced`描述可信CLI/专用URI服务的支持机制，`advisory`只描述请求或不能提供强制保证的选项，`unsupported`明确没有对应执行能力；它们不是本机已完成版本/健康/认证探测。报告独立标明当前未运行的探测，不把SDK顶层存在当成完整兼容。

后端声明的sandbox仍是请求；受限调用实际选择read-only且关闭native工具，不能越祖先权限。模型工具网络与基础设施推理HTTP、stdio进程、日志/状态写入分开说明。现有支持差异和原生协议证据保持，新增后端不能仅声明模式名便继承虚假的强制能力。

## 初轮实现与验证

在原AgentBackend增加受限composition_policy合同，两原生实现拥有响应/发现工具、sandbox与认证差异；共有矩阵只在本模块复用。agent_runs的_admit_input由check_input/run_input两个实际用例消费，旧运行记录字段保持，新增完整权限链和能力描述。CLI共用选择参数，check不接受推理配置/timeout，也不发健康/认证请求。没有新模块、全局registry或静态schema暗加字段。

五套源码初轮141 passed/6可选Forge/mini跳过；最初选错不存在suite的exit4为零执行，另行保留排除。包括原完整输入/祖先不可读、超容量/冲突及当前准入拒绝回归，新增四组合只读报告/无副作用、check/run政策一致及Codex声明workspace-write仍实际read-only/无shell。初版公共描述把Claude的sandbox也标成read-only请求，经自查按真实命令修正为unsupported/无OS sandbox请求；受影响四描述例复验与最终包待核。普通native与默认text-only行为保持，r5任务MCP的运行/生命周期不重做实现。

## 发行验证与当前审查输入

首轮Python3.12非editable包同五套141 passed/6可选跳过，362源/wheel/安装/283冻结一致，10次真实CLI检查/拒绝达到预期。随后仅将CLI backend选项改为消费现有角色catalog的注册名称，避免以后新增后端还得改上层硬编码两名字；角色、模式和配置继续由原准入拒绝，不因此授予新能力。新包受影响12项通过（37未选），实际12次CLI含四后端/模式报告、两个注册但不合格的后端覆盖及六种check/run权限拒绝，均未创建运行/启动模型。最终362/283身份保持，wheel SHA256 `7a8c3dfea4f926d18ca39bc1315955502e6d8999b79988a93e28d9c2cda678d0`。首轮141项与后续12定向清单分别记录，不声称后续重跑了全部五套。

手册初轮6 Markdown/278本地链接/70 CLI parser通过；最终随审查报告再核。当前新fresh-context独立审查和自身structure-review/任务MCP真实模型审查进行中；后者先实际check-input，再确认没有run/目录后调用，核真实运行policy与前述报告一致。前片ce4自身CI仍独立收口，本片暂不推送下一生产候选。

## 自身审查改进及修正版

首轮自身structure-review通过真实Codex/ChatGPT及任务MCP完成，95.47秒、进程成功但决定`request-changes`；原报告及51,527字节附件身份保留。其P2建议把Codex推理配置提前解析。CP1原定不接受该参数，因此这是采纳的合同改进，而非声称原计划早已承诺；现check也接受可选`--codex-config`，Codex的私有`_options`由能力准入和实际command共用。文件/解析/provider表和JSON编码失败在任何run/scope/server之前可读拒绝；不新增提供商探测，Claude仍忽略Codex专用选项。

原包的新四合同红例为4 failed；独立审查者还在固定原包复现了坏配置先freeze/预检再failed的真实所有者顺序，其预检为stub、未启动服务或模型。两次误用旧开发安装导致的收集错误为零执行、不是有效红例；随后修正源码导入后Python3.11五套156 passed/39 skipped（缺SDK/可选平台），最终Python3.12非editable包同五套188 passed/7 skipped（6 Forge/mini及1原生Windows），19.84秒。362源/wheel/安装及283冻结身份一致。原开发环境缺build入口的失败已保留，实际构建改用本片已安装build工具。新的真实模板再审及同片独立复审进行中。

r3自身真实模板完整读取52,191字节后，127.69秒再次request-changes：TOML的nan/inf/-inf仍被默认JSON编码接受。原包10个选中案例实际6 failed/4 passed，三种非有限值各覆盖两模式；最小修为原编码处`allow_nan=False`并归一化ValueError，未增新解析器/权限规则。受影响配置合同及原native配置保护在最终源码/最终非editable包分别11 passed/30 deselected；其余r3的188项/7跳过未宣称全部重跑。最终362/283身份保持，16次真实CLI检查/拒绝是r3结果，后续只改非有限值编码。r4自身真实模板再审和独立复核在途，原两轮request-changes均保留。

r4自身structure-review真实Codex/ChatGPT于21:01:25 UTC完成，110.34秒、决定approve；完整52,413字节附件SHA `af043a783def152edbab4f987141a1f2315b908b437aebe3a557e0b855646f27`，五份受保护源码/测试在审查期间未改变。check先不建run/目录，run再保存同形policy，输入/prompt/SQLite/结构结果在脚本中一致。[最终身份](evidence/2026-11-09-ac3b4-self-review-identity.json)及[结构结果](evidence/2026-11-09-ac3b4-self-review-result.json)随Git保留；独立评审另核原生分页。它只审供应源码，不执行测试、不核未供应旧模块，不替代fresh-context审查、提供商质量或正式批准。最终wheel SHA256 `efe09b026a4ebe471aeb6d11e7901f6355c771d2dedbbe20443e9dcadccf2f26`，最终包的配置定向11项通过，其余受影响回归保留r3清单。下一精确scope/静态、普通交付及自身必要CI。

## 本地独立出口

新的[fresh-context独立审查](2026-11-09-composition-capabilities-review.md)已完成：两轴通过，配置前移采纳项和非有限值P2关闭，无未解决阻塞。独立核原版9机制例、修正版25机制例、非有限值修前6红及修后12入口/模式例和7组有限值命令等价；没有重跑模型。r4自审原生九次MCP调用中的七次附件读取覆盖52,413字节到`next_offset=null`，完整prompt/输入/SQLite/policy/scope/结构结果一致，两server PID退出。性能结论仅为新增祖先链的一次map与深度遍历，没有作吞吐/峰值内存承诺。下一普通精确候选推送、自身双OS CI及同片远端终结；CP4仍待远端部分。
