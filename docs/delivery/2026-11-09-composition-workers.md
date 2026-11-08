# AC3c.3 / CR2a：版本专属队列与正式 worker

日期：2026-11-09。状态：W1–3实现/最终R3包和独立原生SDK验证完成，W4本地独立两轴通过、实际自身审查及逐项处置完成；普通精确交付/双OS CI待收口。基线 `77f93302c53f2d619bf7f84ff9dd23905f754b41`。前片CR1精确77及CI42532654631/独立远端已完成，不继承其包身份。

范围：版本输入拥有各自workflow类型、队列、请求根及活动构造；共享工厂注册原六阶段与新组合类型。v2使用独立的`.composition-v2`队列和`requests-composition-v2`根，继续沿CR1的专用submit活动及原poll/authorize/fence名称，原活动实现依其所在队列绑定对应FileAdapter。旧worker/旧executor只能看到旧队列/requests，不能误消费新版组合。v2提交活动核完整admission/legacy投影匹配；其余活动复用原校验和可信文件回执。fence必须扫描新版根中未终结作业。

新worker由所选原生Python运行，通过Ergora管理的Supervisor启动，保留原环境/配置和显式服务管理；基础控制环境不新增Temporal必需依赖。共享短活动沿原Worker/Activities，不添加调度、DB或新进程守护框架。公开v2 task start/status仍拒绝，提交、计划/证据版本路径及真实executor分别留CR2b/CR3。

- [x] W1：两版本同一构造interface与所属局部映射；入口/队列/路径/活动初始化留各自实现，原始信封身份不降级。
- [x] W2：正式worker双队列注册及Supervisor使用原生解释器；启动错误明确、退出清理所有Worker。实际bootstrap已验，Supervisor新worker完整栈在CR4联验；本片另核原服务回归。
- [x] W3：原/新FileAdapter真实发布/回执/批准/fence与SDK分队列旅程，原CR1历史可重放；非editable包/冻结身份及受影响回归。
- [ ] W4：新的fresh-context两轴结构/性能审查、自身模板实际调用；普通精确交付、必要双OS CI及同片远端终结。前片CI完成前不推下一生产候选。

性能/可用性限制：队列隔开是调度/误消费保护，不是OS沙箱或身份认证；文件ACL和当前可信容器授权保持。实际模型与候选未验前不能声称正式任务闭环。工厂/适配类只覆盖真实两种协议，不增加厂商分派或通用插件容器；新输入的构造变化集中在版本所有者。

实现所有者：`reference_workflows.WorkflowInput`及局部两版本映射拥有workflow class、queue/request root和Worker/Activities构造。v2的FileAdapter差异只核完整admission/投影；Activities只重命名既有submit，保留原验证。`reference_worker`拥有原生模块/环境初始化、最长60秒连接等待及所有Worker生命周期；SIGTERM正常退出。`reference.worker_command`是服务构造interface，Supervisor消费它，不把控制环境的可选SDK变成必装。每版本短活动并发上限16；原v1仍16，新增v2另16，模型进程并发仍由后续原执行器控制，不据此声称全局模型并发增加。

初版源码22 passed（5.82秒）；新活动五项初次fixture误把class当instance而失败，保留5failed/50passed/1skip原记录及单项诊断，不算生产缺陷。fixture修正后五项2.63秒全部通过。R1新wheel `cd7faef097516045061be99e79abf1dc7052d3af08c5df1db255a14c4396a589`的367源/wheel/非editable安装与283冻结身份一致，完整受影响包回归在途。

R1真实SDK/文件交换/独立原生worker进程15.05秒通过：原legacy worker同时在旧队列运行，新版在新版worker启动前没有workflow task被旧worker消费；正式bootstrap随后注册双队列。新旧各六阶段，原始完整payload/所有活动队列、各六份实际请求/哈希产物/可信文件回执/原批准校验、继承signal及各自重放通过。新版另留一个未终结请求后取消，得到CANCEL_UNCONFIRMED且fence列出该作业，没有误报确认；其history也可重放。CR1保存的两份原history在本版均成功重放，无活动名称变更。专用worker与Temporal均exit0、端口关闭。外部产物/回执/owner均是明确的合成协议材料，未跑Agent、候选命令或正式Ergora v2 start；不登记真实可信交付。证据在忽略目录`.ergora/checks/ac3c3-workers/r1/`。

R1安装包五套定向55 passed（40.07秒）、1项原生unsupported-platform检查在Linux按既有标记跳过；全部活动/输入/历史payload/原服务及架构回归通过。新的fresh-context评审与真实自身structure-review/任务MCP在途，受保护生产/测试保持不变；不提前记W4完成。

R1两类审查均request-changes，原始记录保留：独立ST1/SP1发现控制site-packages覆盖所选原生SDK；自身模板109.69秒发现外层task_id/profile_sha256未绑定admission（SP2 P1）及SIGTERM未覆盖启动/完整清理（ST2/SP3 P2），独立者在原R1逐项复现。六项命令/身份/生命周期红例在原R1均失败，6 failed（1.78秒）。R2只临时加载Ergora后移除控制搜索根，在CompositionAdapter绑定外层任务/配置身份，沿原Activities保留request摘要所有权，并使停止handler包住可取消连接、Worker进入与完整ExitStack清理；进入仍位于根任务以保留SDK fatal-error取消语义。源码六套65 passed/1既有平台skip（34.80秒）。R2 build初次误用未装build的开发解释器，零构建失败日志保留；改用已装build的R1验证解释器构建新包，不改变依赖或源码。最终R2包/独立原生依赖旅程及同片复核随后记录。

R2安装包367/283身份通过，六套65 passed/1既有skip（41.45秒）；但其独立原生实际旅程未通过：首轮探针未resolve SDK软链拼写而失败，原脚本/目录/日志保留；只修探针后暴露真实SDK sandbox会在独立sys.modules重导入工作流，已缓存Ergora不足，原生worker以ModuleNotFoundError退出。不能记R2旅程成功。R3在专用worker进程main增加只响应顶层`ergora`的标准MetaPathFinder，由PathFinder在选中包父目录定位；其他所有名字返回None，不将控制依赖根加入搜索路径，也不关闭SDK工作流沙箱。该私有类是导入框架要求、所有权留bootstrap；main退出移除finder。R3新包/独立原生旅程及复核另记，不改R2身份。

R3最终wheel `40ba51dca24f3146a61463a4886379140a8f79f2d8778e386e0770612c530b9a` 的367源码/wheel/非editable安装和283冻结身份一致；源码65 passed/1既有skip（34.96秒）、安装包65 passed/1既有skip（40.47秒）。真实独立原生SDK15.74秒通过：控制Python3.12.11的已装Ergora、另一个Python3.12.3环境的Temporal1.34.0正确分属各自目录，实际沙箱成功重新导入新版workflow；新旧各六阶段、队列/请求隔开、未终结取消、3本片history及CR1两原history重放均通过。专用worker/Temporal exit0并端口关闭；外部产物/owner/回执仍是明确合成协议证据，完整Supervisor/Agent/可信候选留CR4。新的独立者继续核原三finding，实际自身模板R3审查中。

R3自身真实structure-review/任务MCP114.76秒完成，69,386字节附件全部读取，Standards无阻塞，Spec返回request-changes：希望TERM handler覆盖main验证/同步导入/配置读取、在尚无连接/Worker时也受控exit0。其[原始身份](evidence/2026-11-09-cr2a-self-review-identity.json)、[原结果](evidence/2026-11-09-cr2a-self-review-result.json)和[R1/R3判定历史](evidence/2026-11-09-cr2a-self-review-history.json)保留，不将其改写为approve。实现者已请独立者按原W2“启动错误明确、退出清理所有Worker”核前置阶段实际副作用，区分无资源时默认TERM退出与真实Worker清理缺陷；该项处置待落盘，三项原实证finding关闭不受影响。

独立者按实际原W2合同处置R3-S4为nonblocking，不追加main级停止框架：验证只读哈希，environment只读配置/凭据并更新本进程环境，FileAdapter构造只核路径/信任；这些全部早于首次connect、Worker构造或请求发布。此时默认TERM无遗留Worker、持久写入或后续派工。另核Supervisor显式stop的killing分支会STOPPING→STOPPED，-15不会触发重启。原合同的连接取消/已取得Worker进入及整个关闭已有真实信号和SDK证据；希望无资源同步期也exit0是自审brief中更强措辞带来的额外建议。保留R3原request-changes与独立不采纳理由，不伪造approve。原ST1/SP1、SP2、ST2/SP3三项实证问题已独立关闭；最终本地两轴/完整自身证据核对及精确交付另记。

最终本地出口已由[原独立审查者](2026-11-09-composition-workers-review.md)落盘：Standards/Spec通过，三项实证finding关闭，S4非阻塞处置及原两轮Codex判定不改；完整实际MCP读取、12保护文件、输入/副本/manifest/prompt/DB/result和三公开证明分别核实。另按不同后端优先实际尝试Claude Code：API认证存在，但自身task-MCP调用8.45秒以HTTP400/Bedrock空system内容校验失败，零token/无模型判定，failed identity附原判定历史。沿用户授权回退已有Codex/ChatGPT审查，不把认证存在或CLI启动当Claude审查通过。下一固定20文件scope/文档静态，普通提交推送及本候选必要双OS CI/独立即时远端；完整Supervisor栈/正式v2仍后续。

CR2a同片平台修正：原精确c36bcdc的CI42535845046中，Windows128899838743官方annotations记录2 failed/681 passed/481 skipped/16 subtests（335.94秒），恰为新FileAdapter两版本用例在原adapter.read_raw使用Windows不存在的os.O_NOFOLLOW；PowerShell安装步骤成功，Ubuntu终态另核。独立者在原R3隔离复现，登记ST3 P2；Linux本地65/1结果仍按其平台范围保留，不能写c36双OS通过。最小修复只给该原生文件旅程函数加提前Linux/WSL2 skip（两个参数），其余身份/命令/生命周期跨平台测试及生产代码不变；普通修复候选和自己的双OS CI需重新验证，不携带CR2b实现。
