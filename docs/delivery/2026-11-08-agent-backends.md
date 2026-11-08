# AC2：Agent 后端适配器

日期：2026-11-08。状态：完整完成。候选`cc7f95f8ab1a696f2f0df2f8216e23b383011b35`的本地验证、新独立复审、普通推送、自身双OS CI42492287287及15:14:45 UTC独立即时远端终结全部通过，R-1关闭。基线 `556410a7a482b11172bc5f66779dc6463fa0322f`，分支 `refactor/architecture-foundations`。

## 本片合同

用户要求执行者、审查者等职能独立选择后端，专长和模板可组合。AC2只整理既有 Codex、Claude Code、mini-swe-agent、command 的实际调用 seam，为后续定义与权限装载提供实现所有者；不实现嵌套、多成员或新的授权语义。父子权限可随同一新修订共同提高，但不得越过任一祖先与项目授权的规则保持 ADR0005。

现有真实消费者：`agent_runs` 和 `stage_driver` 使用 `agents.invoke`；`tools` 使用可用性及诊断；`bindings.development_snapshot` 核正式阶段配置。保留 `agents.binding_for/validate_binding/executable/available/invoke`，角色、公开配置 schema 及能力描述继续以 `components.json` 为唯一来源。

计划把后端构造、结果提取、后端专用正式配置及诊断集中于本地 `agent_backends`，通过共有 ABC 选择实现。进程、超时、取消及子进程清理由原 `processes` 继续拥有；通用结构化结果验证与摘要仍归调用入口。不新增全局插件注册器、运行状态或第二份公开 schema。

## 验收与证据

需核：既有 command/Codex 六阶段及候选绑定、取消/清理、普通调用、冻结配置、诊断去重/预算/不调用模型和跨平台拒绝；补少量直接针对移动后端合同的检查。构建新的非 editable wheel，核包内代码和283冻结身份。新完整切片在更新计划及实际检查后交给 fresh-context 独立者，两轴审查并处置 findings；普通推送后核必要 CI 和远端。

Claude 此前最小化额外审查 API400 是未通过的特定调用模式，不推断实际正式模式；本片首先保持其原命令。真实模型、MCP、权限强制、嵌套恢复、模型质量/速度尚未验，不能用 fixture 或认证状态代替。忽略证据目录为 `.ergora/checks/ac2-backends/`。

## 已实现及检查

`agent_backends.py`在Agent后端家族内提供ABC、具名调用输入和四个实现；`components.json`及所有公开schema/能力未改。`agents`保留兼容入口，角色选择/通用结果schema、摘要和协议归档仍在原所有者；`bindings`通过同一入口核正式command协议，`stage_driver`转交冻结Codex配置，`tools`调用同一实现的诊断和固定探测。既有进程所有者未改，无新持久状态、依赖或CI作业。

新增五项检查覆盖正式Codex配置过滤/只读角色/显式模型及CLI覆盖参数、Claude exit0但错误/缺失/不完整结构化结果，以及mini指定解释器和请求交付。复用已有原生CLI进程、command模板切换、六阶段/候选绑定、取消和doctor预算测试，未新增镜像CI。

源码显式`PYTHONPATH=src`运行`test_agents / test_projects_tools / test_readiness / test_components / test_registrations / test_reference_executor / test_project_configuration / test_windows`：125 passed、12 skipped，pytest 213.71秒。跳过为6项需显式固定Forge/mini SDK与6项原生Windows；不宣称已验这些平台/SDK。本地FastAPI依赖报告一条既有Starlette测试客户端弃用warning，未在本片更换依赖。

首轮开发环境构建因未安装有效`build`失败，保留原始退出；使用前片已具备构建工具的环境，默认隔离构建exit0，新建独立venv安装wheel的`[dev,web,temporal,gepa]` exit0。wheel SHA256为`788f44c07d790edb764d431fd114da5c424230d816ec357c74d55f959af6ebfe`，353文件源码/wheel/安装逐字一致，新进程导入site-packages且283冻结文件与基线及manifest一致，公开`reference.verify`通过。包内回归尚在进行，不从身份核对推断行为通过。

初步文档静态为4份Markdown/183本地链接和锚点、30条README parser及`git diff --check`通过。实际命令、退出和摘要分别在本片忽略证据目录保存；不把旧片CI归本片。下一新fresh-context两轴审查与包内验收，随后普通精确交付及本候选CI。

包内定向完成：新venv移除`PYTHONPATH`运行Agent/readiness/导入图/原正式阶段相关合同，50 passed、15 deselected、零skip，pytest 76.86秒。包含原command/Codex四组合六阶段、模板说明拒绝、取消及清理；未跑这次选择排除的其它包内路径，源码125项范围另保留。fresh-context独立审查者已收到原始需求、基线、10文件差异/新文件、上述实际命令及身份记录，正在检查。

README源码树、Agent手册和当前架构同步了新所有者及接入步骤；最新静态6文档/262链接/30parser通过。README变更仅影响wheel说明元数据，最终打包身份仍须在审查处置后刷新。没有测量模型或执行性能收益；本次保持原进程/IO路径，不凭文件拆分声称加速。

## 独立审查与R-1处置

已完整阅读[新独立报告](2026-11-08-agent-backends-review.md)。需求轴未发现行为回归，可维护性轴R-1指出`registrations._prepare`仍重复拥有command正式协议规则。采纳：保留注册层的训练/开发模板语义判断，统一使用`agents.validate_binding(..., formal=...)`，删去另一份后端分派。训练模板普通command注册依旧允许；开发模板的缺协议拒绝仍由同一后端合同负责。原初审证据和源码/包结果均保留。

新增一条训练专用注册兼容检查，既有开发拒绝检查复用。第一次受影响测试命令误列不存在的suite，exit4/零执行，未记作通过；纠正为实际三个文件后，源码`test_registrations / test_project_configuration / test_architecture_boundaries` 69 passed/零skip、pytest 47.64秒。同一弃用warning保留。

默认隔离重建最终wheel并重装exit0，SHA256为`14eb4dca11f798daa06aa8064321fc845b0772f9eac0e43f56f802215f883ffe`。与首轮包相比，只有`registrations.py`、README说明的METADATA及RECORD字节变化，其余包内文件集合/字节完全相同；最终353文件源码/包/安装及283冻结身份、公开verify均再次通过。最终包受影响注册合同检查正在运行；原125/50项属于初版范围，69项属于修正后源码，不混加成一个未经运行的矩阵。

独立者另核20项后端/基线对照及真实失败/超时边界、包内4项doctor与353/283身份。本片没有全局插件框架、额外CI或性能收益声明。下一同片R-1复核及最终静态/scope，再普通提交推送和自身双OS CI；未测范围保持原表。

最终非editable包受影响验证完成：17 passed、45 deselected、零skip，pytest 7.70秒，覆盖训练普通command注册、15类既有非法注册拒绝及导入无环。最新静态另发现独立报告3个相对源码行链接使用了冒号路径，已交原审查者修正为GitHub行锚点，尚未将这轮静态记为通过。

同片独立复核已完成：R-1关闭，需求/可维护性两轴通过，无未解决finding。原独立报告追加核69源码/17最终包日志、最终353/283身份及两个wheel的精确三文件差异；另独立静态7文档/267链接/30parser和diff通过，原报告三处链接已修正。主代理接受结论，后端实现及测试不再修改。下一最终scope/静态、普通提交推送及自身双OS必要步骤，原未测范围继续保留。

普通候选`cc7f95f8ab1a696f2f0df2f8216e23b383011b35`唯一父556410a，15文件，push exit0，2026-11-08 14:57:00 UTC远端一致。同一独立者14:58:34 UTC核候选Git对象/15文件/完整差异及最终7文档267链接/30parser均通过。自身[CI42492287287](https://github.com/626619403/Ergora/actions/runs/42492287287)首轮官方观察In progress，不能登记CI成功或完整AC2完成；等双OS必要步骤和独立即时远端终结。

自身CI42492287287已成功：Ubuntu128767072083三个必要步骤、Windows128767072294四个必要步骤均success，官方run/job身份和步骤日志URL全部绑定完整cc7f95f，主代理verify通过。首轮两job由官方完成页面提供；主代理所记“辅助脚本已改用size=200”在独立核对时发现实际未生效，已进入纠正取证，仓库CI未改；实时日志空链接与无认证API403不参与通过证据。同片独立者正核官方证据和即时远端，终结前仍不登记完整完成。

取证记录纠正：辅助脚本第一次字符串替换漏写`.com`，未匹配实际代码却被主代理误记为已生效；同片独立者发现后，已按实际行修正并重新GET明确的`batch=0&size=200`，要求`hasMore=false`。原默认批次/记录与错误实时日志请求均保留并排除；两份原完成job页的必要步骤及精确SHA证据保持，不能用不完整批次声称完整列表。最终以实际新批次、run/job页及同片独立取证为准。

## 最终完成

同一独立者实际GET完整批次及官方run/job页，确认两OS必要步骤全部success、完成标记和日志URL绑定完整cc7f95f；15:14:45 UTC独立只读远端同SHA，无新增finding。完整AC2关闭，原基线、各轮代码/包身份、未验范围及取证纠正保持可追溯。本轮后续只归档完成状态和原独立报告追加，不改变生产/测试/依赖/CI身份，不重跑无变化的行为矩阵。

下一AC3a定义包尚未实现：先确定实际导入/检查消费者、版本化schema和完整资源身份，复用既有资产与备份所有者；之后按AC3d/3b/3c实现祖先继承编译、实际装载/权限与递归冻结。父子同修订提权仍受整条父链及项目上限，不影响在途manifest。
