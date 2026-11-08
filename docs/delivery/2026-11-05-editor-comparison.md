# F6.1：图形与 Schema 表单比较

日期：2026-11-05；2026-11-08终结。状态：F6.1完成。原两P2修复复审及候选身份已通过，普通b1候选推送/原独立远端核对、精确双OS CI41984232370和[新fresh-context终结](2026-11-08-editor-comparison-final-review.md)已闭合；原审查历史保留。Git 基线为 `df0a908893970d12208b3a2026d19b4591f83989`，最终候选为`b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`。详细节点在[F6计划](../plans/2026-11-05-low-code-editor.md)，结果在[比较报告](../research/2026-11-05-editor-comparison.md)。以下过程记录保留当时的验收范围，不替代本段最终状态。

## 范围与所有权

新增开发者例子 `examples/editor-comparison/`，三入口分别比较 Cytoscape + 原生表单、React Flow + 原生表单、Cytoscape + JSON Forms。共用的编辑器状态只在例子的 `app.js`；两个图和一个 schema 表单适配器只负责各自库的投影/事件，入口是实际三个消费者，不建立通用插件框架。

例子复用现有应用和模板 API、包内 API 客户端、原模板 schema、草稿校验及保存修订；没有新生产路由、状态表、领域 validator、模型执行器、默认依赖或 CI job。位置/缩放只在图库状态，JSON 与输入仍沿原领域合同。冻结资源、六阶段和正式任务不变。

## 已实际运行

初始 home 下独立安装固定36个包，锁含61条（包括未装平台可选包），禁用安装脚本；许可/公网 registry/integrity和实际 esbuild 版本通过。三入口真实构建成功，完整依赖许可文本可生成。使用新持久 control 与试验 Git 项目，实际只启动 owned loopback 比较 HTTP，没有请求原生服务或 Agent 任务。

初轮 Cytoscape 原生表单及 React Flow 均通过两个模板的选择/属性/重命名引用、增删依赖、JSON 往返、服务端摘要、真实节点拖动/缩放、错误输入保留、显式保存、键盘与390px；各29请求/22草稿类POST，零pageerror。服务端拒绝环和越界路径。

JSON Forms 默认 Ajv 编译在现有 CSP 下失败，控件未出现，首轮辅助旅程实际exit1；原页面/console、源码SHA及官方来源已保留。官方 `NoValidation` 模式调整后，同组两个模板旅程实际通过（29请求/22草稿类POST、零pageerror），由原服务端显式校验，不把它写成默认浏览器 Ajv 验证通过或完整 schema 支持。安全头保持。

原浏览器包装文件不可直接执行，以及首轮浏览器缺动态库，分别保留实际126/1；通过 Bash 和既有 home 运行库启动成功，没有安装系统包。几项辅助脚本的路径/回调错误保留实际失败；不当成产品或重建成功。记录位于忽略的 `.ergora/checks/f6-editor/`，截图在 `output/playwright/`。

## 当前验收与下一项

迁入例子的clean npm ci实际exit0（7秒），默认npm run build实际exit0（1.34秒），完整许可含36已装包及原Cytoscape。最终源码HTTP重开后，三方案六组旅程各29请求/22草稿POST、零pageerror；六成功草稿保留原r1后显式保存到r2，各模板三方案摘要相同。额外20请求/2校验POST验证真实Shift点选/端口拖动连接、自引用重命名仍由后端拒绝、重名ID不改输入及NoValidation表单空ID保护。最终浏览器合计107请求/68POST，全部POST只指向原drafts校验/保存。实际HTTP资产逐字同构建、CSP保持且无压缩，构建体积和单次交互条件已写入比较报告；不把gzip估算当实际传输或把单次loopback时间排序。

F6.2的撤销/重做、统一未保存保护、迟到失败/跨项目所有权和修订冲突仍是后续生产功能；50/200/500容量归F6.3。当前例子不会自动恢复已保存草稿，未覆盖任意 schema、预编译 Ajv、真实 Agent 或其他OS原型运行。

最终只读终核：独立库16表仅project=1/drafts=6，其余均0；六份r2摘要匹配原旅程，试验repo干净。浏览器真实Chromium155.0.8059.12，close exit0；两轮owned HTTP均日志shutdown complete，SIGTERM子进程-15/实际包装shell241，最终pid消失/8981端口关闭，DB SHA保持、草稿保留。未停止其他切片服务。生产src/tests/依赖/CI无差异，不新造测试/CI或主动重跑未变模型/矩阵。

选型已形成[ADR0003](../architecture/decisions/0003-workflow-editor-stack.md)：下一片保留原Cytoscape/原生模块，集中补编辑状态/撤销重做/修订，React Flow保留真实可复现候选，JSON Forms不进入默认依赖。新增15个例子源/锁/说明文件均有本地SHA；真实命令、107请求、三方案原结果/最终资产及退出证据在同片忽略目录。下一静态核对/完整scope，新的fresh-context结构、成本和正确性审查，然后普通提交推送。F6.1还未登记完成。

## 初审与受影响修复

[独立初审](2026-11-05-editor-comparison-review.md)提出两项P2。F6-01在例子README中将安装改为`pip install '.[web]'`，避免基础包缺少FastAPI/Uvicorn。新建不使用system-site-packages的独立venv，实际安装exit0，导入Web/FastAPI/Uvicorn及`pip check` exit0，并用该环境运行原比较服务器。没有改默认产品依赖。

F6-02在Cytoscape适配器的`update`清除待连接起点。修复前真实Shift点选旧模板起点、切换模板再点新节点，实际出现不存在source的建边异常，输入混入旧ID；保留原失败及其辅助匹配失败，不当成额外产品问题。修复后从当前构建实际验证两个Cytoscape入口：跨模板及重命名都取消旧意图，正常Shift连接仍成功并由原后端校验。18请求/2校验POST、零pageerror，没有保存草稿或正式任务。原107请求/六r2旅程保持其原源码范围，没有将其重标为修复后全量重跑。

修复后的默认构建实际exit0，更新体积见比较报告。已归档15源文件身份和当前13个HTTP资产逐字匹配，原CSP/无压缩保持；新venv Python3.12.3、FastAPI0.162.0、Uvicorn0.54.0，实际导入和再次`pip check` exit0。旧库SHA仍为`78d2c0ce28902aaa6bd36ee4615e0dbb90a1ead8a6cac1fafd23018a6e8776e8`且六草稿保留；新库仅一个project、零draft及Agent记录，两库均16表。记录在同片忽略目录的`fix-local-verification.json`，原始安装命令的成功以工具实际结果为证，不补造原stdout。

本片浏览器close实际exit0；新HTTP核完整命令和专用状态目录后正式SIGTERM，原日志startup/shutdown complete，实际包装shell143已取回，与此前两轮的241分别记账。离线确认该PID消失、8981关闭、两个库及15源文件SHA保持。静态13文档/347本地链接、30条CLI参数和例子Bash语法通过；生产src/tests/依赖/CI仍无差异。下一同片复审及精确交付，后续F6.2a仍为编辑状态与缓冲所有权。

同片复审已追加原报告并保留初审历史。两P2在实际读取源码和结构化回归记录范围关闭，无新增finding；26文件/当前diff、实际资产/两库及绿色stdout的独立核对未完成，不能把实施侧核验替代独立终结。下一先保存普通候选提交并推送，核精确CI/远端，再补同片独立核对；如仍受限则保留未完成状态。三个状态追加文档的静态SHA早于复审scope，最终静态须在报告写入后重新核验。

## 精确交付与独立终结

原报告后续已核候选b1的唯一父/26文件、15源、13资产、347链接/30 parser、两库与原绿色stdout及退出，并于2026-11-05 07:26:47 UTC独立核实时远端完整SHA。原普通push exit0。精确CI41984232370的Windows127101113372和Ubuntu127101114113必要构建/身份/回归步骤均success；Windows安装升级success，Ubuntu该条件步骤skipped。

2026-11-08原审查者跨会话不可调度，新的fresh-context审查者[另写终结报告](2026-11-08-editor-comparison-final-review.md)，从Git对象、原记录和两个独立官方job HTML补核；12:54:44 UTC另只读取得实际官方页面确认同一逐步骤结果，未重跑CI或浏览器，范围内无finding。F6.1可登记完成；F6.2/3、原型Windows、容量及其他未验边界不继承为通过。下一生产字段与成员模型按AC前置推进。
