# B3.3a 独立阶段监督：逐步交付

日期：2026-11-15。固定产品基线`75d1ee325288527f67fb1ea814332d1522ff4860`，parent为b78。前置B3.2最终本地产品两轴通过、r4两安装648／283及真实控制流程保持自己的范围；本片实施与验收按以下分项独立结算，不能借用前片宣布B3.3a验收。

## 设计准备

[具体计划r2](../plans/2026-11-15-training-budget-phase-supervision.md)只调整原阶段监督的进程归属：原budget owner保留身份／锁／clock，各phase移到专用supervisor进程，复用原`processes.run`的subreaper／kill／reap。父owner不能因为一次phase结束而杀掉未来并行的另一个phase，也不能在总截止时强杀reaper后宣称后代已收尾。与原B3.2一致，期限后不再启动工作，只等待已经开始的安全回收；未确认或超期分别保持unknown／实际overrun。

独立只读[生命周期调研](../research/2026-11-15-training-executor-lifecycle.md)检查原executor／Sandbox／process_job／processes与六阶段生命周期，补充原executor没有whole-executor单次attempt和锁内准入hook的事实。B3.3执行功能需要另行固定最小协议接缝，不能靠锁外预检或另一个slot包装消除竞态；本片不改283参考、不启用runner、不添加执行权限或自动循环。kernel专家保留在v3路径。

调研还指出完整context可能超过PIPE容量，父owner同步stdin写入或完整stdout文件读回会阻塞停止。r2补可继续的短轮询communicate传输；supervisor在原run实际reap返回后先发送匹配stopped帧，再读helper结果。帧前不硬杀reaper，帧后若后处理跨总截止可停止已无业务后代的该已知supervisor，结果仍unknown；不把这个临时帧当训练执行停止证明。r1原件保持，不用固定headroom缩短有效预算。

## r2独立审查与r3修订

[新fresh-context评审者](2026-11-15-training-budget-phase-supervision-plan-review.md)对固定r2给出需求request-changes／R1、结构维护approve／开放0。独立stdlib探针在受支持Python3.12中向慢reader发送851968B，首次communicate超时后续调13次不能完成，手动关stdin只收到65536B且SHA不同；这不是产品运行验收。接受R1并保留原件，r3使用本地selector与非阻塞PIPE，持续维护唯一发送偏移、完整stdout帧缓冲和原clock／停止检查；明确两帧完整身份／顺序及独立封套容量，旧直接helper仍输出原普通JSON。没有为修计划先改产品或有效配置。

下一步固定r3设计完整原件，送同reviewer续核后再实施。尚无本片source、安装、真实进程或服务验收，不创建新suite或CI矩阵；前置75d自己的CI43665465985在途，单独结算。

## a0设计通过／a1准备

同片独立续核固定r3两轴approve／开放0／0，R1仅设计层面关闭。原r2报告逐字前缀、失败探针和三版计划原件保持，23原来源及strict parser、283参考与22链接已核，未运行产品／测试。开始在原两个owner内实施阶段监督及真实IPC，不改变共享processes／原queue／start slot／native参考或执行权限；新产品验收另行记录。

## a1实施与首个原场景

14份纯文档／状态／调研共同普通发布`5fa4319c79de7db238cde9d11f5b8acd5b263b91`，parent75d；两个提交的产品tree相同，候选Git tree的209链接零缺失，完整远端Ref同一，原75d的CI另行跟踪。实际产品实施从该文档head开始，产品基线仍是75d，不把文档发布称产品验收。

两个原owner已接线：预算模块私有phase生命周期管理唯一stdin偏移／非阻塞selector／完整身份帧；worker明确的phase-supervisor分支在专用子进程复用原processes.run，先flush真实stopped再读helper原输出。旧四mode普通JSON分支保留；父owner不调用subreaper，final仍走原publish helper，增加实际overrun观察。共享processes与283参考未改。

源码`source-start-r1`沿原accepted返回后自动fence场景1 passed／21.88秒，外层22.945秒；真实独立owner、SDK服务替身与原native adapter，完整七文件scope／stdout／XML保持。只认证该场景；两子树互不回收、setsid后代、慢reader、回收帧前后异常、旧helper及完整受影响矩阵仍待，尚未构建新安装或产品独立审查。

## a1产品R1与五个真实阶段场景

前置75d自己的CI43665465985／attempt1八job／30必要步骤全部success，原fresh-context终核两轴approve／开放0／0；其报告、72原件索引及独立终核已保存，不转授本片产品。当前工作树仍未发布本片。

新的[产品独立评审](2026-11-15-training-budget-phase-supervision-review.md)初轮需求request-changes／R1、结构静态approve：stopped帧之前SIGKILL monitor supervisor后，后续fence成功掩盖原phase unknown。真实故障实红1 failed／28.17秒保留；原fence与恢复及原件保持检查已过，失败点为final没有phase观察。最小修正由原owner将phase ID、mode、S返回码、stopped、helper过程状态及业务状态／原因写入原final的短摘要；不复制大helper结果、不建新账本，publish自身结果仍单列。

固定source-scope-r3的源码五项`budget_phase_`全部通过：pytest144.68秒，外层145.606秒。保留真实owner／supervisor／原processes.run，SDK服务为原替身。覆盖两个S互不回收与父owner非subreaper、真实setsid后代收尾、786432B UTF-8探针完整传输／SHA、挂起reader仍按原clock停止、stopped后结果读取阻塞，以及stopped前真实SIGKILL时同fence恢复且final保留monitor unknown。原件在ignored本片check目录，历史实红与修后运行分列。回收跨总截止＋可捕获取消、接近原1MiB helper结果、受影响原矩阵、最终非editable安装、真实Temporal控制流程、自身原模板和独立最终复核仍待，不将源码五项扩大为完整验收。

## a2边界实测与R2修正

`source-boundaries-r4`在同一产品上两项运行：大结果1通过，延迟reap场景1失败，pytest49.22秒／外层50.127秒。完成native的既有测试使用原1MiB界减8192B的ASCII摘要加UTF-8尾部，确认最终gate摘要逐字完整、原native/gate未变且未fence；只是CPU合成合同。另一场景真实setsid后代、reap-started后向原owner发TERM，delayed reap跨原总截止0.5秒仍返回并发送stopped。失败是测试错误要求S返回码只能0；按固定设计，stopped之后总超期可以kill其结果reader，因此修预期接受0或-SIGKILL，继续要求实际reap-finished、stopped=true、原后代已停、实际overrun、无新phase／final／fence。原运行不改记通过。

同片独立复核已依据固定r3及真实五场景关闭R1，结构approve／0；新R2为缺损`stopped.process`字典虽被接收，却在短摘要访问status／returncode时KeyError。接受并沿真实S故障注入实红：原run确已reap，随后S发送缺字段帧，owner traceback为KeyError，未进入fence；`source-incomplete-red-r5` 1 failed／23.54秒，外层24.496秒。修正在原receive协议边界检查原process的完整字段、状态／返回码类型与本phase输出路径，缺损不进入stopped集合并保持unknown，不在摘要处重复兜底。r6两项精准源码重跑和最终两种非editable包正在验收；在结果返回前不宣称通过。

## a2精准修后与a3两安装

`source-corrections-r6`为同一修后产品：真实reap跨总期限并TERM原owner的场景通过；缺损stopped场景的同fence恢复、原件／slot保持均通过，但测试再次错误要求耗尽cleanup后必有持久final，1 passed／1 failed，pytest61.26秒／外层62.192秒保留。只改该测试：从原owner诊断stdout核phase unknown／stopped=false及具体原因，不把诊断当持久final；原公开恢复与原件检查保持。产品不变，`source-incomplete-r7`精准1 passed／32.75秒，外层33.950秒。上述源码分项分别归其固定scope；最终安装另跑完整受影响范围。

新r1 wheel SHA256为`c050c204ada81cfce0e335c210f9f457900704390c882ebeec3c96e8235a4178`。core／SDK各648源码／wheel／site-packages逐字相同、283参考PASS和依赖检查通过；core确无Temporal SDK，SDK为原锁定1.34.0。相对5fa没有新增／删除产品文件，只有两个原owner变化。测试与示例173文件已冻结，安装回归及完整架构边界正运行，真实Temporal控制流程、自身模板、独立终核及精确发布仍待。

## a3真实控制流程与架构边界

r1安装的完整架构边界16 passed／0.42秒，外层1.068秒。相同新SDK安装的真实本地Temporal＋预算worker控制旅程通过／54.635秒：九个实际CLI、同预算queue／精确run、native queued request、自动fence、原取消与resume；原授权／唯一slot／request字节保持，候选b未创建request、没有started或executor。九个采样捕获的owner／S／helper身份停止，Supervisor及7233／8233端口均已收尾验证。新控制数据保存在独立持久目录，394原文件索引冻结；这里只认证CPU合成控制合同，不认证训练、GPU、质量或性能收益。

安装原矩阵仍运行，已知两项final fsync故障的marker未出现：固定8秒cleanup被新增S启动与既有fence／cleanup消耗，publish在注入点前即被原期限停止。公开fence恢复和无final的unknown符合合同，但这两次不能认证指定fsync故障。保持原失败，完整运行返回后针对故障覆盖调整测试的显式预算，产品默认及有效配置不改。自身模板仍在进行，独立最终验收待原件固定。

## a3自身模板R3、安装实红与r2封套修正

相同r1安装运行原`ergora-structure-review@1.0.0`，授权Codex回退，90.809秒完成、需求request-changes／结构approve。完整18源码／文档260487B与原三资源全部在实际stdin；这是供给全文的独立文本审阅，不认证私有运行原件。R3指出原helper容量虽保留，final新增phase摘要仍会挤占原1MiB持久记录的容量。

接受并强化既有completed测试，而非另建矩阵。`installed-capacity-red-r1`在原r1包上真实实红1 failed／20.52秒，外层21.443秒：helper1047967B仍在1MiB内，旧final投影1048463B可写，新final1048794B超过原上限，publish失败且无final；原诊断与publish stderr保留。未缩摘要来通过测试。

r2仅为`training_cycles._document`和`_record`增加显式keyword limit，原默认1MiB不变；budget final的publish／observe两端统一使用2MiB，继续复用原strict finite／no-follow reader、原格式和durable writer。helper结果仍默认1MiB，283参考和共享processes未改。三源文件相对5fa变化，无新增／删除产品文件。r2新wheel SHA256为`56e24e967729304b9abcf2c5cdeb82be5b6619a7b55d9bdefbe5c27407bb03a5`；core／SDK各648三方逐字、283与依赖检查通过。受影响安装矩阵重跑包含原默认记录的来源／严格解析／恢复检查；r1所有失败保持原身份，最终独立审查及发布待实际终态。

测试另外做了两项有据调整：final文件／目录fsync场景保持同10秒计算窗，显式cleanup由8改14秒以实际触达注入点；这不改变产品策略或放宽运行截止。managed-create测试强制TERM后只等待真实owner停止和原锁释放，其原断言并未要求持久final，耗尽时不再错误调用必须读取final的helper。两者等待完整安装结果确认，不预记通过。

## a3 r2真实服务与自身终审

r1完整受影响安装21项：18 passed／3 failed／471.69秒（外层472.748秒）；两个fsync marker未触达及managed测试错误强求final，与前述诊断一致，完整失败保持。r2采用已说明的精确测试修正，继续同一受影响范围并补原默认记录边界，尚待完整终态。

最终r2新安装的真实Temporal控制旅程再次通过／54.133秒：同九实际CLI、九个捕获进程身份停止、原授权／slot／native request保持、服务及两端口收尾；394原件另建r2索引，不借r1转授。本片原结构模板r2完成75.141秒、需求approve／结构approve：18全文265810B及原三资源全部在实际stdin，R1／R2／R3源码修正获确认。它仍只审供给全文，不认证私有原件或CI；新独立产品reviewer将终核原候选／安装／进程证据。

## a2／a3完整安装结果与待终核

最终r2产品保持不变，固定173测试／示例源的完整受影响安装运行24 passed／497.22秒，外层498.278秒，无失败／跳过；原默认记录容量／strict来源恢复三项也通过。新final故障两marker确已触达，原accepted／held、managed create／owner失联、completed、lost-ack、registry／fence fsync／同fence恢复与七个新phase故障均由该命令实际选择。完整架构边界另16 passed／0.44秒，外层1.117秒。

R3精准边界在最终安装中：helper1047967B、旧final投影1048463B、新final1048794B（原1MiB界为1048576B）；新final已持久发布，公开submission读回整个final逐字语义相同，gate摘要1046961B完整、原native/gate/request保持、无fence或额外取消。尺寸与原XML另存，不把r1实红改记成功。用户训练手册和现有架构图已补阶段S、短phase观察、封套界和实际超期／旧owner语义。

本片仍不启动executor、GPU或训练，不授执行权限／自动循环；kernel专家和模板路径未改。下一步固定完整12文件候选、链接／差异／原件索引，交同一产品独立reviewer终核后普通提交／推送并核自己的CI；在这些门禁完成前不记精确交付闭合。

## a3独立最终本地通过

新的fresh-context产品reviewer已终核固定11作者文件（另加其自己的公开审查报告，共12文件候选）、173回归输入、两安装648／283、实际24＋16、R3完整公开read、真实服务394原件／九CLI／九捕获PID、自身原模板完整18＋3 stdin及178件证据索引。需求approve／结构维护approve，开放0／0，R1–R3关闭；历史实红保持。[终审报告](2026-11-15-training-budget-phase-supervision-review.md)已写当前结论。公开文档仅移去一处机器绝对路径，实际位置仍在私有原件；产品和结论不变。

开始普通精确提交／推送当前开发分支；最终12文件Git tree链接／完整差异需以最新报告重核，不能沿旧3b4a候选tree冒称最终发布。自己的CI与固定发布独立补核仍待，在此之前不记门禁闭合。后继原生锁内准入协议另片设计，原283与kernel路径继续保持。

## 固定提交与自己的CI在途

本片已普通发布`5182bfa03f536d4090b91014f97eedda1c5d2d3a`，parent5fa，tree `b8696bb8b0a293fdd45bfb3a77b2088a58b2efb4`。12个blob／SHA／bytes与完整staged diff-check、五AST及最终候选Git tree的242链接零缺失已记录；普通push exit0／5.829秒，完整SSH远端Ref相同。原产品reviewer已独立核固定本地发布与实际push／Ref原件，官方commit／branch页也指同一完整SHA。

自己的Portability #229／run43670140205／attempt1在途；匿名REST限流403保持，原reviewer跟踪官方完整navigation及必要steps终态，不声称完整日志或artifact。三产品与两tests均保持本片最终r2字节。只读整理后继B3.3b协议计划可继续，不在前片门禁闭合前推送后继产品。

## 自身CI原失败与独立接续

自己的CI43670140205 Linux group5终态failure：官方annotation显示两个原final fsync故障测试均因`Original budget owner did not finish its bounded supervision`失败，468 passed／13 skipped／1599 deselected／776.01秒。原job构建、reference身份与观察上传成功；未取得完整step日志，REST403／直接日志404保持。具体接缝为测试使用wall24／cleanup14，却从submitted返回后只等待20秒；快速返回时会在合法总期限前SIGKILL原owner，本地慢启动可掩盖该预期错误。Windows仍在途，原独立reviewer继续同run终核；本片不宣称CI成功。

最小[接续修正](2026-11-15-phase-publication-wait-regression.md)仅让原两个故障测试的观察等待沿实际授权剩余时间＋回收余量，不改产品、预算、计算窗、故障marker及公开同fence恢复断言。原失败身份保留，修正用原最终非editable安装精准重跑，再由新的独立reviewer审查并单独发布。后继b仅设计已审，不混入执行产品。

原独立终核已完成：原518自己的run43670140205最终八job七成功／一失败，30必要步骤29成功／一失败，Windows与PowerShell安装升级成功；R4仅测试观察等待保持开放，需求request-changes／结构approve，R1–R3保持关闭。126项CI原件和12份官方raw来源已独立核。接续修正原安装精准2通过／65.44秒、外层66.446秒，两marker及真实owner停止已核；新的fresh-context接续reviewer正在核固定候选与原件，尚未发布或宣称接续CI成功。
