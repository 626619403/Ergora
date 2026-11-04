# F4 / F4.4c 独立综合审查

日期：2026-11-05（Asia/Shanghai）。审查者：独立代理 `/root/f4_completion_review`，使用新上下文；未参与本片实现或原生写入。先读原需求、Git原始差异、相邻源码和验收脚本，再读作者收口叙述；按项目AGENTS及maintainable-project-delivery的独立审查要求执行。

**需求符合性：本地通过。可维护性：通过。** 本轮发现两项P2文档问题，作者均已作最小修正，本审查复核关闭；已审范围内无未解决finding。F4功能片及C组合证据可以进入纯文档交付；本片精确提交、最终文档静态记录、正常推送及实时远端仍待同片续核，本报告此时不登记完整F4交付完成。

## 基线与范围

生产、测试及本地HEAD均为 `77b334c62346f92868c22c067949b0caf2d74d48`。最终wheel SHA256为 `43e1211ea12c7522b928881d10b1c0497489e6a0a68930bbf86f10eb260c8ca1`；350包资源、两份独立noneditable安装及283冻结文件保持。C没有源码、依赖、测试、CI或schema变化，不把该最终包追认为前片所有真实写入的发行身份。

实际审查九份作者文档：README、[PLAN](../PLAN.md)、[USAGE](../USAGE.md)、[当前架构](../architecture/current.md)、[详细计划](../plans/2026-11-01-all-in-one.md)、[F4恢复入口](2026-11-03-formal-task-console.md)、[B2交付](2026-11-05-task-job-console.md)、[B2同片审查归档](2026-11-05-task-job-console-review.md)及[C交付记录](2026-11-05-f4-completion.md)。本报告是随后新增的第十份文档。

相邻实现检查覆盖 `tasks.js/app.js/state.js`、API/安全DOM边界，`tasks/web/reference/services`，原creation/submission/runtime、批准/取消/对账/导出、events/evidence及冻结DevelopmentTransport/FileAdapter。私有原始材料位于 `.ergora/checks/f4-completion/` 和相应前片checks；未启动服务、安装环境、调用模型、重放workflow或任何任务写操作，也未重复重型回归。

## 需求与组合证据

|验收责任|独立检查与结论|
|---|---|
|复用真实完整开发旅程|抽核前片五段真实浏览器脚本、执行命令、CLI原始Result及保存结果：创建/提交38请求/10POST，批准57/2，取消27/1，对账35/1，导出76/2。批准的外层命令按保存脚本路径调用原launcher；其余直接嵌入脚本的命令与源码相同。原脚本限制单次真实派发，丢弃的批准/取消/对账/导出回复先取得真实成功回包，再通过原ID读取恢复，未以受控POST冒充真实写入。它们保留各自原发行及独立审查身份，C不重做这些写入。|
|精确导出候选可复验|审查者重新从两业务Git对象生成archive，字节等于保存的tar；原分支仍分别指向 `1d759a00ceb68fdc7c52261ace445268737165cf` 和 `46a53fef59d77bdcdfe7f4d912c2b6e53f6bb5e7`。13/14文件的archive、解包目录及manifest摘要逐项相等；可信脚本摘要仍等于登记证据。已读原脚本及治理3类/大型变更6类全部exit0日志；behavior内部确实调用候选unittest，不从被捕获的内部输出推算测试数。本审查未再次运行候选测试。|
|新HTTP/浏览器及空会话恢复|核旧B2 HTTP的PID/UID/cmdline及端口退出、旧浏览器close、新HTTP加载原43e121安装的身份。C三段保存脚本与实际command内文本逐字相同，CLI原始Result与保存JSON逐项相等，全部exit0。重开55GET、服务离线44GET、仅Temporal恢复57GET，共156GET，零写、零pageerror；每段清会话，并验证run来自后端submission。|
|原操作与原观察身份|独立将三段合同、创建/提交、两个批准/一个取消、两个导出/一个对账与原intent/result逐项对比，canonical意图摘要、原run及原回执一致。正常两run的事件前缀、event56原job回执及完整execution-plan文本/SHA匹配；取消run仍为CANCEL_UNCONFIRMED，reconciled不变成开发成功。原ID需由操作者保留或输入，未声称清空会话后能自动发现全部decision/request ID。|
|执行服务全部离线|正式shutdown前的原脚本实际核零Running workflow和零active lease。离线段三个任务的本地合同及操作记录可读；其中一次原运行查询实际返回400并显示“运行查询失败”。原CLI记录一条预期失败资源console消息，不能称零网络错误；无自动启动或重新提交。|
|仅Temporal恢复与最终退出|内部正式服务命令stdout逐JSON等于verified记录，exit0/confirmed；首次关闭20个所属进程，仅Temporal重开而其余服务STOPPED，最终关闭Supervisor/Temporal两进程。C原SDK快照在重启后及末次浏览器后核三份完整history/outcome保持，事件数329/348/112，零Running。本审查保持服务离线，重算保存原history摘要与快照记录一致，不声称新作了实时SDK查询。|
|数据及所属资源保留|审查者重新核139份原文件、三claim/零active、两业务repo的HEAD/symbolic HEAD、全部refs、工作文件/status/worktree列表，全部等于C前后基线。SQLite使用mode=ro/query_only，DB/WAL摘要读前后相同。核9个HTTP退出回执、所属原服务PID无同身份活动进程，当前四服务及本次HTTP合14个端口均关闭，socket/PID标记退出；control、Temporal及lease三个持久SQLite保留。最终browser list原日志为no browsers。|

C的辅助脚本三类假设失败均有保留：把Supervisor包装命令当直接Temporal argv、未预期早期相对HTTP入口、把not_running的status退出码固定为3。源码与原日志支持作者的失败/修正顺序，未通过改产品或删除运行数据使验收通过；首轮final-offline工具输出转录也明确不冒充原生验证结果。

审查者实际查看重启后治理正常及取消两张390px截图：当前合同标题、中文字段和长SHA可读。其余任务的宽度检查属于脚本断言，不把这两张截图扩展为已查看屏外运行事实或所有截图。

## 所有权、依赖、守卫与成本

无新增生产抽象或数据所有者。网页仍由原任务详情消费者组合；创建/提交/批准/取消/对账/导出只调用既有用例，服务端拥有意图、原run、回执和副作用。sessionStorage只保存选择，空会话从持久submission回填run；记录读取不依赖实时Temporal成功，符合离线恢复要求。

事件和job读取沿 `CLI/HTTP → tasks → reference专用进程 → _Submission/原Transport`，由共享原spec/memo验证固定run。job继续核连续history/context/envelope和原FileAdapter可信回执；`_Creation.file_adapter`被evidence与reconciliation两个生产文件实际消费。检查没有发现应另造公共框架、缓存、索引或调度器的依据。当前39个顶层Python文件及包含函数内相对导入的AST图已独立复算，无相对导入环；文档将专用进程/动态运行边与普通Python导入区分，调用图中新job所有者及Adapter方向与源码相符。

原前端守卫保护可达的交互边界：改run、切任务/项目、离开页面、关闭/替换dialog、切材料及逆序读取使旧回复失效；写前检查原记录和明确确认，未知结果沿原intent读取/恢复。后端仍拥有项目revision、Git、租约、原历史及产物验证。C没有添加重复参数校验、不可达分支或把失败回退成成功的控制流。

事件每次手动读取，DOM保留最近200条；文本只留当前8192字符窗口，没有后台轮询或累积全文。后端每窗仍需核history、回执全部产物摘要，并完整读取/严格UTF-8解码所选材料；FileAdapter的逐产物16MiB和1MiB响应限制不能推导总IO/内存上限。公开手册准确保留这些成本，C的47.79/27.39/48.75秒仅是整段旅程时间；候选复验及静态检查耗时也没有被当作通用吞吐或性能改进。

本片无生产/合同变化，不重复原重型Python套件或真实模型执行是适当的验证成本选择。审查者仅另作13模块Node语法检查，全部通过；没有增加镜像实现的测试或因单文件较长强求重构。F5完整证据索引/预算费用/交接及G0新用户验收继续为待办。

## Findings及修正复核

1. **P2，F4当前恢复入口状态失真，已关闭。** 原[F4入口](2026-11-03-formal-task-console.md)第5行自称优先的“当前检查点”仍写c2推送认证失败、d待提交，分片表仍称F4.4未实现；[详细计划](../plans/2026-11-01-all-in-one.md)的F4概述/d状态也已过期。新维护者沿当前导航恢复会重复处理已交付工作或误判缺功能。最小修正是更新当前banner/分片状态并链接C，保留历史过程。作者已修正，审查者重读第5行、表格及详细计划F4段，确认c2/d/B2精确身份、C尚待文档交付、两模板正常旅程和另一个独立治理取消/对账任务的范围均准确。
2. **P2，离线恢复矩阵过度承诺只需Temporal，已关闭。** [USAGE](../USAGE.md)原第156行把所有原run状态查询归为无需worker；冻结 `DevelopmentTransport.poll`第74–78行在RUNNING时实际调用workflow query，需要可响应查询的worker。操作者仅重开Temporal查询在途阶段可能失败；C三个闭合run不能证明该场景。作者已将闭合状态/结果与运行中阶段查询分别列行，第156–157行及C范围说明与源码相符；事件/job的只读history路径仍不要求worker。未为修正文案启动服务或改产品。

以上是本轮全部substantiated findings；修正后已审范围无阻塞或非阻塞未解决项。

## 发行、验证边界与待终结

审查者从精确77b334c的内存Git archive重新取350资源，与当前源码、实际43e121 wheel及两份noneditable安装逐项比较；283冻结文件也按原manifest根重新计算，全等。首次自查误用manifest子目录、假定离线无WAL、套用历史日志命名/launcher格式而中止的读检查均未计为通过；按真实源码布局和原执行格式完成上述复核，没有产品改动。

B2精确[CI41896900471](https://github.com/626619403/Ergora/actions/runs/41896900471)已由原同片审查者终结。本审查另行核其六份官方原始来源字节/SHA、run的Success及完整77b334c身份，解析Windows126808727970/Ubuntu126808728539的selectedJobId与4/3个必要步骤success/completed及精确日志URL；与归档结论相符。未下载完整步骤日志，未推导额外测试数量，未借该CI替代C服务恢复证据。

文档静态原记录在本报告落盘前覆盖九文档327个本地链接/锚点和27条README parser命令，作者随后还细化了概述措辞；最终应在本报告及状态更新完成后重核并保存精确文档身份。审查者当前 `git diff --check`通过；本地实现和组合验收结论不依赖再触发纯文档CI。

下一步仅为本片最终文档静态检查、正常纯文档提交推送、提交范围/资源身份及实时远端同片续核。完成后才能登记完整F4终结。Windows完整Linux执行栈、真实GPU、远端GitLab工单及F5/G0等未验/未实现责任保持原范围，不由此报告补成通过。

## 精确文档提交、包与实时远端终结

日期：2026-11-05，同一独立审查者续核。本节关闭上文保留的C交付待验项，精确候选为 `f2b93d4daba751a707af43755f2dd30fc19c74f8`，唯一父提交为原生产/测试基线 `77b334c62346f92868c22c067949b0caf2d74d48`；后续F5的任何工作树或提交变化均不归入本片。

- **精确范围与文档身份通过。** 独立读取Git提交，十文件全部是本报告已列的Markdown；源码、依赖、测试、CI、schema没有变化。逐一重算该提交的十份blob SHA，全部等于 `staged-scope.json` 和最终 `static-documents.json`。已读 `commit-command.json`、原stdout/stderr，实际commit exit0，`77b334c..f2b93d4` 的 `git diff --check`另行独立通过。
- **最终静态验收通过。** 原 `static-documents-command.json` exit0；审查者另以精确f2b93d4的Git树及文档内容核全部本地链接/锚点，实际340条、零missing，并使用既有CLI parser重新解析该提交README的27条命令。数量与原记录完全相同，包含本报告及两finding的最终修正文案。这是文档与parser验收，不是另一次任务执行。
- **原发行身份通过。** 独立从精确f2b93d4的内存Git archive提取350资源，逐项等于原manifest及实际wheel内容；wheel完整SHA仍为 `43e1211ea12c7522b928881d10b1c0497489e6a0a68930bbf86f10eb260c8ca1`，与 `commit-package-identity.json`相符。未重新构建、安装或要求未来F5源码等于C归档。
- **正常推送及实时远端通过。** 已读 `push-remote-identity.json`、原remote-before/after和push stdout/stderr，原普通快进推送exit0，前远端为77b334c，后远端为完整f2b93d4。审查者另外使用现有RSA身份及已配置SSH传输执行只读 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`，独立exit0，实时远端精确返回 `f2b93d4daba751a707af43755f2dd30fc19c74f8`。未读取或输出私钥内容，也未执行推送。

该提交带 `[skip ci]`，其十文件纯文档范围及生产树完全不变已由上述精确检查证明；原生产77b334c的双OS CI41896900471及B2终结仍保持原身份，不要求为同一生产树重复运行CI。此次没有启动服务、调用模型或重跑原生写/重型套件。

**最终结论：F4.4c需求符合性与可维护性通过，精确提交、原包身份、最终静态文档、正常推送及实时远端同片终结通过。两项P2均已关闭，无本片未解决finding或剩余验收项，完整F4可登记完成。** 本段归档属于同片审查记账；F5、G0及其他已明确保留的支持/运行边界仍按其独立责任推进。
