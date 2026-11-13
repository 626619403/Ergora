# B2 总预算交付记录

产品基线`f394945db894740ad23a81c62b4ad87c85a84511`；范围和分片以[B2计划](../plans/2026-11-12-six-stage-budget.md)为准。本记录保存B2a从设计到c46f383精确交付的历史，自己的CI与独立终核已关闭；后续B2b／c运行消费者、验证及独立出口见[运行片记录](2026-11-12-six-stage-budget-runtime.md)，不以此记录的历史“未实现”作为当前状态。[新的独立设计审查](2026-11-12-six-stage-budget-design-review.md)同片复核开放0／0；B1自己的CI与精确交付另在[B1记录](2026-11-12-six-stage-materials.md)记录。

## 源码调查与选择

实现者及一位fresh-context调查者分别核了tasks→原creation、submission／VerifiedSpecClient→WorkflowInput／Temporal、Executor→Sandbox／monitor→stage_driver／agent_runs／processes，以及结果收集和fence路径。调查者只写持久私有设计记录，未修改产品或公开文档、安装、测试、请求网络或提交；它不替代后续独立设计／代码评审。

已确认直接在preview填当前时间会破坏完整record的精确确认；从start或workflow开始计时则遗漏完整材料准备。采用原task-creations先保存一次prepare实例，再由只读preview／create／原input消费。单纯clamp模型timeout还会漏掉构造／Git锁、额外monitor等待、只读snapshot、回收与收集；需要先用真实独立进程探针验证接缝。

调用额度拟复用原确定性job／process的有限slot和started-before-launch，不新建计数账本；预留、attempt、实际可核启动分别显示。单composition的`project`并发scope不是多个task共享的项目全局并发，后者不由本片宣称实现。新执行在预算全链贯通前保持unsupported，旧运行版本保持。

## 当前节点与后续

B2.0源码调查及三种受控进程探针已完成，它不作为产品或CI测试。原进程实现依赖外部TERM与无总截止的回收，探针只证明这组可响应进程的实际停止与回收。之后按B2a持久合同、B2b原workflow、B2c实际生命周期逐项实现与验收。B2a模型／字段已实现、产品独立出口进行中，不借B1的295／58项或自身approve关闭B2。

## 实际进程探针与范围

探针复用未修改的`processes.run(supervised=True)`，在独立进程用同一固定工作截止请求停止。r2的脱离组孙进程、阻塞flock、入口已过期三例分别在首次授权后2.261／2.314／1.148秒返回；前两例总额度3.2秒、其中清理预留1秒，已先消耗0.8秒模拟准备时间。采样分别为3／2／1个实际身份，同一原预算再次进入均不启动child；观察者manual_cleanup与存活均为空。不是在模型返回后另给完整timeout。

首r1诊断没有单列观察者代清理计数，因此不借其返回无存活字段独立证明监督者已回收。r2修正了此证据缺口，明确在观察者需要清理时拒绝成功；r1原件保持。完整探针、r2原件和来源身份仅放[独立prototype分支](https://github.com/626619403/Ergora/tree/8e160b345adf9eac00fe4142c3fd74bc29a07e97/docs/prototypes/six-stage-budget)，主开发分支只记录决定，不将其并入产品或CI。

探针没有运行真实tasks prepare/create/start、Temporal、Git命令、调用slot或正式receipt门禁，也未证明清理失败有界、不可中断I/O或任意daemon都能停止。结果支持进一步适配单job独立进程接缝；真实准备链和正式终态发布仍各需产品验收。

## 独立设计审查与修正复核

新的fresh-context评审从原九文件设计候选及实际源码提出两处缺口：原材料遍历在编译child之外，不能只给编译30秒就称准备计时闭合；原`process()`会先发布receipt，而FileAdapter.fence把任意有效终态（包括FAILED／CANCELLED）视作停止已确认。

已按最小范围修订计划：完整安装遍历／`tasks._definition`／manifest／编译／收集清理进入受同一deadline监督的prepare worker；whole-job child只返回待核结果，由原job生命周期finalizer在整个拥有树停止且收集验证完成后，唯一发布所有正式终态并更新原ledger。cleanup unknown时保留原attempt与待核证据，不发terminal，原fence继续unresolved。原评审已直接读取修订文件、六份guardian输出、实际采样与Git对象，同片复核关闭SP1／DS1两项P2，Spec／可维护性开放0／0。修正仍是设计，未声称已经实现；[唯一报告](2026-11-12-six-stage-budget-design-review.md)保存原判词、复核原件和限制。

## B2a 实现与首次行为检查

文档检查点`e37f617f9aca566d862175de5a1e6b25a08ba2de`已普通提交／推送、作者SSH完整Ref相等；十份Markdown原件／静态154本地目标／六秘密值issue0。原B1评审随后仅追加当前结论两行，同片状态记账随本次文档保存，不扩产品或CI范围。

新增小的stdlib `reference_budget`，只拥有稳定policy、一次授权身份／同boot时钟和有限已知slot；持久所有权仍在原`_Creation`。CLI／HTTP共用原`tasks.prepare/preparation`。新schema5／input9、完整准备worker、只读固定preview、双摘要create／原intent恢复、调用cap和显式关闭运行均已接入。未修改283冻结参考、CI、依赖或原调度器；旧合同行为仍需受影响回归确认。

首轮新源码行为7项通过、1项因测试CLI写成`tasks`而非原`task`失败（49.18秒）；修正后同七项通过，HTTP测试因缺少已有Origin／X-Ergora-Request头被正确403拒绝，保留原日志（48.40秒）。补齐测试头后CLI／HTTP共用入口1项通过（9.12秒），没有修改既有本地HTTP保护。首轮七项覆盖丢prepare回执、原ID／并发、preview稳定、到期和修订拒绝、低调用cap，以及安装／manifest／编译三处受控慢工作和脱离session后代的实际停止；它们没有真实模型或Temporal调用。

受控未确认清理、完整最终回归、非editable安装、实际自身审查、新独立两轴和本产品候选的普通发布／必要CI继续，不能用B1自己的295／58或旧CI关闭。

## B2a r1 出口与同片修正

r1非editable Python3.12.11 wheel455产品文件与源码逐字一致、两份RECORD及283冻结身份通过；安装核心76项通过／1项静态架构清单失败（127.20秒）。新stdlib基础模块未登记到既有allowlist；只更新原测试的合法下层依赖及新foundation约束，不删除保护。原11suite大检查在900秒观察上限被终止，没有pytest终态；其后段已有同片修正，保留为混合范围partial，不称全部通过。运行专属cmd/cwd进程的后查为空，未观察到遗留运行；不能把空采样推导为覆盖全部短进程。

新的[独立两轴r1](2026-11-12-six-stage-budget-preparation-review.md)发现三处P2：并发锁竞争观察漏核完整定义／修订身份、缓存的剩余量跨过attempt落盘后才装定时器、实际发布owner在观察者30秒unknown后失去原修订写锁。实际自身结构模板用Codex／high读取原18文件554,700B和全部五scope，314.23秒succeeded／request-changes；其一项P2为preview永久复制操作目录。四个采样所属进程无存活，原stream全文／输入／结果身份已核；此判词不等于当前修正后通过，亦非不同后端成功。

已作最小修正：争锁观察复用原scope/policy比较；attempt/fsync后重新按同实例取remaining再装timer；把BEGIN IMMEDIATE及当前revision／registration核对移到实际发布owner，保持原锁直到文件发布结束，父观察者不持该锁等待；preview回到原短生命周期task_creation transport、读取已冻结成果，不建立持久操作目录。

四个行为在未改r1安装包上实际red（27.89秒）：冲突未raise、6秒预算实际elapsed7.02932秒、绑定写者在publisher仍阻塞时先完成、两preview多留8文件。首次red驱动把venv解释器resolve成基础Python而缺pytest，原件保留、不用于证明缺陷。修正后的源码budget＋原架构检查24项通过（74.10秒），涵盖真实并发／慢落盘／flock延迟实际发布及观察unknown后锁仍有效／preview完整操作树不变。r2非editable最终产品、针对原提交／恢复及代表性旧与v8真实旅程、模型聚焦复核和新独立同片补核继续。

## B2a r2 安装与聚焦审查

r2非editable Python3.12.11 wheel SHA256为`a9fd7371d407f8d95139b70b44cd91c9c8c5307c7708328c57ff8dc88e6e826b`；455产品文件、460 wheel条目及465安装RECORD行逐项核过，源码／wheel／安装字节相同，两RECORD和283冻结身份通过。隔离解释器`-I`的预算／创建／tasks／架构四suite共80项通过（139.08秒），包含以上四修正。原submission／恢复和五条代表性旧／v8／work旅程仍在运行，不能把核心检查称作全量通过。

实际随包结构审查模板的r2聚焦复核使用Codex／high，145.60秒succeeded／approve；完整读取11份冻结修正源码／测试／计划／交付共186,675字节，范围不替代完整20文件的独立评审。原manifest→准备input→实际input→prompt→admission→五scope→原result全部相等，成功MCP文本页连续读至末尾，四采样所属进程无存活。原后端turn用量按原计数保留，缓存已包含在input中，不重复相加或推算账单；原r1 request-changes及全部失败／partial范围不覆盖。原件为私有`six-stage-budget/self-review-r2-codex*`，安装原件在`b2a-install-r2/`。完整候选同片独立补核、其余安装终态、静态和本候选发布CI继续。

## B2a r2 回归终态与SP3

r2隔离安装原submission／锁／composition transport三suite共54项通过（316.08秒）；五条代表旅程通过（140.10秒），覆盖原command治理／大变更、完整材料full／issue-source和原work full。它们经原Executor／真实可信fixture命令与受限fixture Agent，不是新预算Temporal全生命周期或真实模型六阶段旅程，后者仍待B2b／c及D。此前900秒无终态的广泛运行保持partial，未借本组改写为全量通过。

同片独立复核新增SP3 P2：小的prepare完成witness在采样elapsed之后才fsync，显著慢盘会在总截止后发布旧prepared事实。新回归在真实owner的最终outcome `os.fsync` 中阻塞4秒；未修改的r2 wheel实际1项失败（9.72秒），期间确为unknown，随后错误返回prepared。它不绕过create原deadline，但准备完成／超期报告不满足合同。

最小修正在原creation中先用原write完整持久化小outcome候选，再重核同实例总截止，迟到只持久化exhausted候选及当时elapsed／overrun，最后仅硬链接已存字节为唯一完成witness。时间字段是候选决策处采样，不宣称测到自身最后原子链接返回或内核强实时；exhausted落盘可安全超期，不能转回prepared。已按时完成的历史材料仍可只读预览。未新增正式账本／调度或改变原合同发布门禁，r3包和受影响检查、聚焦模板复核及完整独立补核继续；r2原通过范围与SP3失败均保留。

## B2a r3 修正后出口证据

r3非editable Python3.12.11 wheel SHA256为`e3d294ff82fc1baaf12750ee631327ff62f11d383833433405d9f6abb95b7276`；455产品文件与源码／安装逐字一致，460／465两RECORD及283冻结身份通过。只重跑受本次准备witness修正影响的budget及原架构suite：25项通过（82.89秒），包含真实最终fsync延迟的新回归；原r2的80／54／5保留各自候选和真实／受控范围，没有改称新全量。原r2有效SP3 red及首次驱动错误仍保留。

随包自身结构模板再次聚焦SP3／ST3，Codex／high实际106.92秒succeeded／approve，七份完整冻结文件114,994字节；五scope成功文本页连续至null，原manifest／准备与实际input／prompt／scope／结果全链相等，四个采样所属进程无存活。此次范围只为r3最终witness修正，不替代全21文件独立两轴。原用量仍按native计数保存，不重复计算缓存或推账单。原件为私有`six-stage-budget/self-review-r3-codex*`与`b2a-install-r3/`；完整独立补核、最终静态、普通提交／推送及本候选自己的必要CI继续。

## B2a 完整本地出口

原fresh-context协调者与两独立子轴已核最终完整21文件、r3修正及原件，Spec／Standards开放0／0，SP1–SP3和ST1–ST3全部关闭；[唯一评审报告](2026-11-12-six-stage-budget-preparation-review.md)保留r1／r2失败和r3补核。最终静态21文件177个本地链接目标／六秘密值issue0，JSON及Git空白通过。B2a本地出口通过，普通提交／推送、精确Git与远端及本产品自己的必要CI继续；不借B1 CI结案。B2b／c仍未实现，新start关闭；准备完成不等于总预算六阶段已跑通。

## B2a 普通发布与精确身份

最终21文件ready清单SHA256为`5ce90d1a0fd7fd94bafe64febeb2b1d9ae48e97ea59b63c2dd53b28b702deef4`，Git对象及mode逐项相等；已普通提交为`c46f3834df08927f7d266757c0f7d3fae8308fb8`，普通push退出0，作者SSH `ls-remote`同完整SHA。没有强推或合入main。最后静态177个本地链接目标／六秘密值issue0；前173／174样本保留各自字节范围。自己的必要CI及原评审精确终核继续，不借B1结果。

## B2a 自己的CI与交付终核

自己的[Portability43226350116](https://github.com/626619403/Ergora/actions/runs/43226350116)第二官方run HTML为Success；Windows131210421168四个／Linux131210421450三个必要步骤均completed／success，完整日志路径绑定c46。新的fresh-context[发布终核](2026-11-13-six-stage-budget-ci-review.md)直接核四对HTML／receipt、精确21份Git对象／mode／ready及作者原SSH Ref，Spec／Standards开放0／0，B2a精确交付终结。原实现评审仍为原完整两轴；本次仅补发布终核，没有模型／行为重跑或独立网络请求。

匿名REST403、最初In progress及第二样本只识别job尚未核步骤的范围均保留。原件为私有b2a-closure的ci-run-html-r2、两ci-job目录及ci-terminal-r3.json；不称REST成功、完整日志下载或预算六阶段全生命周期通过。B2b／c继续使用自己的交付记录和独立出口。
