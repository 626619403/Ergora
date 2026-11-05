# G0.3／完整 G0 独立综合审查

日期：2026-11-05。审查者：`/root/g0_completion_review`，本片新建 fresh-context 独立上下文，未继承实施对话。依仓库 `AGENTS.md`、maintainable-project-delivery 及其 independent-review brief，先核原始要求和差异，再核源码、原始记录及现存数据。本轮仅新增本报告。

## 范围与结论

精确基线及审查时 HEAD：`82f69cde5e4d54c8ac3c2dd18ed045c00411c293`。逐项重算 `.ergora/checks/g0-closure/review-scope.json` 的11份 Markdown SHA256，全部相符；当前 tracked diff 逐字等于 `review-tracked.diff`。范围为 README、AGENT_BACKENDS、PLAN、USAGE、architecture/current，G0.2交付及审查记录，总计划、G0分片计划，以及新增的 [G0.3交付记录](2026-11-05-new-user-acceptance.md)和 [F6具体计划](../plans/2026-11-05-low-code-editor.md)；两份新增文档均已完整阅读。生产、冻结参考、测试、依赖及 CI 没有变更。

**需求符合性：G0.1／G0.2的原验收及G0.3公开关闭流程、计数、平台边界通过；初审一项 P2 已同片复核关闭，无未解决 finding。精确交付尚待终结，完整 G0 此时仍不能登记完成。** 两前片各自的新独立审查及精确提交／实时远端终结已记录，本轮另作原始证据抽查，没有只采信作者摘要。

**可维护性：通过，无未解决结构、性能或冗余测试／断言 finding；CI 成本记账措辞已修正。** F6仅形成渐进计划和独立依赖准备，未进入默认发行，也未宣称原型、浏览器或性能通过。

## Findings

**P2（已关闭）：区分未主动重复验证与 push 自动调度的矩阵。** 初审时 [G0.3交付记录第42行](2026-11-05-new-user-acceptance.md#验证与剩余工作)和 [G0计划第21行](../plans/2026-11-05-new-user-acceptance.md#分片与可验收节点)笼统表述“纯文档不重跑未变多OS矩阵”。现有 [portability.yml](../../.github/workflows/portability.yml) 第4–7行对 `refactor/**` 的 push 没有路径过滤，第17行起仍安排 Ubuntu／Windows 的构建、完整 pytest 和 Windows 安装检查。当前分支的普通纯文档 push 因而也符合自动调度条件；原文案可能被读成没有这项 CI 执行或成本。

最小修正：明确“本片未主动重跑未变矩阵；普通 push 仍可能由既有 workflow 自动调度，实际触发／结果另行记账，不充作新生产或 G0 运行验收”。本轮未查询这些自动运行的实时状态，不据触发配置声称某次已执行或成功。既有纯文档完整矩阵的成本可另立 CI 分流切片，保留 required-check 语义；本片无需改 workflow，也不应简单 paths-ignore 使必需检查永久 pending。无 P0／P1，范围内无其他 finding。

同片复核：实施者仅在三份文档澄清“主动”验证与自动CI，并补记后续CI分流边界，未改workflow或验收规则。审查者重读三处和新增说明，修正符合上述最小要求，P2关闭；原scope其余八份文件SHA保持。复核时三份修正SHA256为：G0.2交付 `befa063fbf8d7aef1f2feee95121ac4bb58171c1b2cb6afe5b6c09a0126231fb`，G0计划 `227ae9b06cf83346bd02794c7838b123ca7c5197df0b60e05345fb43ae6613d4`，G0.3交付 `0c727b8429bca99fdbca28284234906b3142d6b7083fcf9ac1fee1b6d0950592`。新静态原命令exit0，11文档376链接／30命令通过，独立diff-check亦通过；未重复已通过的运行、离线或数据检查。包含本报告的最终scope／静态仍由精确交付门禁核对。

## 独立核查

- 直接核 `reference_task_reconciliation.py` 的完整历史／请求／回执／fence检查、明确发布fence及精确claim释放，以及 `reference_task_export.py` 和原生 ingress.release。新增 README／USAGE／Agent说明和流程图与所有者一致：REVIEW_READY不自动释放，export按原规则处理适用租约，暂不导出可明确reconcile，原结果与清理证据分开。两正常任务的原 external-status 日志确为 fence=not_recorded／external_confirmed=false，原reconcile日志为确认并释放；没有把文件协议证据当OS进程检查。
- 独立从当前源码、新app及无SDK接收者重算全部352资源，三套逐项等于原身份表。G0.1公开安装和原lock／require-hashes依赖同步命令的实际exit0、非editable来源、初始缺服务prepared记录及一次register／一次可选bind原命令可追溯；两新项目当前各revision2。A2原口径与现USAGE安装块均为7／3条文档命令；独立重算每项目register=1、bind=1，并核两个项目各3份操作者输入SHA。平台2份输入、可信检查／生成投影／额外取消输入分别记账，8文件5类不是最低安装要求；ini原SHA保持。
- 离线解码原history，独立核连续324／337事件、待批前缀不变、start spec／原submission memo、各唯一event113 approve_plan及页面精确plan；两原prepared身份延续。两结果均REVIEW_READY，原7／6 job覆盖六阶段；13份原request／receipt、42份正常材料字节／SHA、verification／review候选及结果摘要绑定通过。九份成功模型日志确有turn.completed观测，正式索引未归一化与完整账单未知保持分开。核HTTP重开及丢回包原结果、四条重复操作与18文件保持记录，未将requested当完成。
- 两精确候选仍为 `44d697f0701a69fdfad50e72ee1b463d70adc9fe`、`68ff73c485ea9faedf1dd8a94f98629f26fb489a`；导出分支与操作者detached worktree指向原SHA，worktree干净、源HEAD及可信检查SHA保持。九条独立可信复验的原命令／成功结果可核，没有重跑检查或改候选。取消原history为35连续事件／一个精确request_cancel／零批准，原CANCEL_UNCONFIRMED保留；原monitor终态为Cancellation fence observed／非零，当前原进程组无活成员、monitor已退出，显式对账与3 claims／0 active相符。
- 三个现存浏览器ZIP逐字等于原CLI包，外部SHA、manifest和全部blob摘要可核；三份改动复制包仍CRC有效。原无SDK离线成功及六项错误SHA／复制篡改exit2记录和对应stdout／stderr可追溯，本轮未重跑九项CLI核包。原三包分别保留两REVIEW_READY及一CANCEL_UNCONFIRMED，离线核包不证明来源认证或执行成功。
- 独立重算现存新152／旧139文件及两套Git文件／HEAD／refs／worktrees／leases，逐项等于原快照；新旧各3 claims／0 active。核7个owned浏览器／HTTP／Supervisor及服务PID已退出、五端口关闭、临时目录空、socket／PID文件移除、三持久DB非空保留、原Supervisor ini保持；未处理其他片服务。退出时零running查询、正式shutdown和HTTP有序退出／shell143有原记录，本轮没有重开栈。
- 独立只读重核11文档376个本地链接／锚点、已核app实际parser的30条README及新增关闭节3条命令、`git diff --check`，全部通过，未执行手册业务命令。系统解释器缺包的首轮辅助失败与正确app解释器后的exit0分别保存，没有改产品或抹去失败。
- F6前置的package／lock SHA与现存独立目录相符，36个已装包、61个含未安装可选平台的lock条目及公网registry／integrity可核；主要候选版本与计划一致。安装结果归档明确是工具原结果说明；许可、可复现构建、浏览器、往返语义和成本仍按E1–E6后续验收。现有模板／草稿校验／revision接口是原型的复用边界，没有提前新增DSL、调度器或通用插件框架。

## 限制与交付门禁

本轮只读核查及写报告，未安装、构建、启动服务、调用模型、修改候选、提交或推送，未重复未变运行矩阵，也未重新观察已经结束的进程。既有工具／缓存／认证与新Linux应用／数据严格分开；宿主系统包预检失败保留，无apt／sudo。空OS、本机Windows／WSL2完整G0、远程tracker、其他harness、GPU、完整／计费消耗及金额仍未验。Windows仅引用原精确CI41929749342的Python／PowerShell支持子集，原生产4c87c2a及两个不同归档身份未混记。

实施者须刷新包含报告和状态记账的完整scope／静态清单，完成精确纯文档普通提交推送。由同一审查者核Git对象的唯一父、完整文件／SHA及352资源，并只读实时核远端一致后，才可终结G0.3和完整G0。此后F6.1先做E1–E6比较再决定F6.2；当前结论不提前完成这些后续门禁。
