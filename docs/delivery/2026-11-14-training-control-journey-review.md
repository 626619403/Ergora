# F9d1 训练控制面组合验收独立评审

评审者：fresh-context 独立 reviewer `training_control_journey_review`；日期：2026-11-14。固定基线及本次读取时的 HEAD 均为 `8d739c298668ab9f7d88fdaa205a21f304d9586c`，分支 `refactor/architecture-foundations`。依据 `AGENTS.md`、原用户持续开发／每大项独立需求与维护性审查约束、[本片计划](../plans/2026-11-14-training-control-journey.md)、[本片交付](2026-11-14-training-control-journey.md)，以及 maintainable-project-delivery 的 independent-review brief 与 codebase-design 进行只读评审。仅授权写本报告；未改产品、安装、联网、运行测试或提交。

## 当前结论

- **最终本地需求轴：approve，开放 finding 0。** 真实控制、浏览器组合、原终态重启、全部固定引用与总收尾原件均已直接补核。F9d1 控制组合与原 F9d／B3 真实 GPU 比较分开，保持原冻结输入、attempt-before-send、unknown 对账及 evidence SHA 批准合同；没有借历史 F9b／F9c 运行或前继 CI 代替本片证据。
- **最终本地维护性轴：approve，开放 finding 0。** 私有驱动 P2 已在最终r4源码及针对原异常路径的实证中关闭。自身模板r2对提供的r3快照approve已核；独立补读发现的staging发布边界随后以更小修正处理，未借该旧approve覆盖r4。本片未改 `src/`、`tests/`、`scripts/` 或 CI，没有新增产品抽象、产品测试／断言或CI。

产品 finding：0；验收驱动 finding：1（P2，已关闭；开放0）。本结论只关闭下文列明的本地F9d1范围；固定发布与本片自己的必要CI仍待分别补核，不代表全部交错矩阵或真实GPU验收已通过。下文“首轮待验”保留当时的检查前提，后续补核记录给出各自实际结果。

## 实际检查范围

已读所有适用指令、当前 `docs/PLAN.md`、本片两份新文档、原 F9 总合同及 start／cancel／release 合同；核 Git 分支、HEAD、tracked／untracked 状态和基线 diff。本片计划、交付及 F9 计划链接为新范围；工作树另有前继发布／CI记账变化，不将其当本片产品改动。读取时 `git diff BASE -- src tests scripts .github` 为空。

逐项读取训练页三个指定 JS owner、`training-preparation.js`、原 `app.js`／`state.js`／`api.js`；应用 `training.py`、Web payload／routes、CLI 原调用者；`reference.py` 训练子进程与原记录读取、全部 `reference_training_*`、`reference_history.py`、`State` 的数据库与文件锁；原 native `agent_platform.training`／`training_executor` 和 `perf_temporal.client`／workflow／activities 的实际调用链。另只读核原 submission／cancellation／release 回归测试及现有 CI 分组，未执行它们。

## 源码证据与可达行为

|检查|源码位置与可达场景|评审判断|
|---|---|---|
|迟到回复与实验选择|`src/ergora/data/console/training.js:28` 将 view 绑定 DOM 连接、项目、tab 和已读取的 home；`:174` 每次 inspect 增加详情序号；start 的成功／错误在 `:135`／`:137` 检查 `selected()` 和请求序号。取消在 `training-cancellation.js:49`／`:51`，批准在 `training-evidence.js:62`／`:64` 使用相同的详情选择约束。|A 实验投递后切 B、换项目或离开 training，旧回复不能写新 view；仍需真实浏览器扣住回复验证原副作用与读回。|
|旧 form 与本地发送状态|`training.js:126` 的 start action 检查当前选择和本 panel 的 `sending`；读取会替换原 controls。取消 request ID 输入在 `training-cancellation.js:12` 使旧读取序号失效并移除旧动作；action 在 `:37` 检查选择／发送。批准在 `training-evidence.js:51` 另核 approval／evidence 对象身份，归档重读使旧批准 form 失效。|没有看到自然 UI 路径保留可点击旧动作并跨新实验发送。不能仅凭 DOM／闭包检查宣称双击和全部并发已实跑。|
|锁的作用域与 finally|JS 锁只管本操作 panel；旧 finally 只遍历其闭包中的 DOM 元素，没有全局新 view 查询。`training.py:214`／`:240`／`:267` 的 SQLite `BEGIN IMMEDIATE` 只覆盖本地意图冻结，后续 `:229`／`:254`／`:276` 在事务外投递。各 reference 操作的文件锁使用 `blocking=False`，覆盖同一操作远端阶段。|控制数据库不跨 Temporal RPC；不把 panel 锁升为全页锁或新调度器。原 immutable writer 与操作锁负责多调用者竞争，不依赖前端 `sending` 作为唯一保护。|
|start 意图与 unknown|`reference_training_submission.py:28` 冻结 home／registration／execution／repo／spec 来源；`:183` 写 attempt 后才调用原 start，原 CLI 仍用 `REJECT_DUPLICATE`／`FAIL`／单次 workflow attempt（原 `perf_temporal/client.py:38`）。恢复在 `:214` 核完整起始输入与意图 memo，`:267` 有 attempt 时只 reconcile，NOT_FOUND 不重发。|原开始／归属 owner 保持；预先存在的同名 run 不能静默接管。迟到 ACK 后重新打开页面应读回原 submitted／unknown，而非用新 ID 旁路。|
|固定取消与停止事实|`reference_training_cancellation.py:25` 只接已确认 start；`:53` 冻结原 start SHA、run、request ID、reason、actor；`:143` 写 attempt 后发信号；`:170` 用固定 run 完整信号 history 对账。`:179` 分别读取原 workflow、adapter observation 与 fence。|投递回执不等同外部停止。控制 CANCEL_UNCONFIRMED 与后来执行器 CANCELLED 可并存，页面未合并为整体成功。|
|精确批准与恢复|`reference_training_release.py:53` 冻结同一原 run／evidence／actor／operation／files；`:217` 在 owner receipt 写前冻结原字节 SHA 与 expiry，`:226` 缺件拒绝重建；`:190` signal attempt 在发送前。`:295` 已有 attempt 的恢复只查原固定 run 的完整 release history。|owner receipt 创建 unknown 与信号 unknown 分开；不续期、替换或自动再批准。原 adapter 仍验证授权／当前 gate／baseline／fence并创建 `automatic_merge:false` 的票据（原 `agent_platform/training.py:177`）。|
|无第二实验账本|CLI `cli.py:1049` 与 Web `web.py:658` 的动作共用 `training.py`；`reference.py:412` 用原进程 owner 运行已核固定 native 安装，checkpoint 保存在原执行 state。SQLite schema未新增训练表；原 workflow 拥有控制历史，原 adapter拥有 job／fence／票据。|现有分工有具体职责；无需为本片把不同生命周期合成通用基类，或新建训练调度／批准权威。`run-local` 仍是原 CLI 显式单实验动作（原 `agent_platform/training.py:244`）。|

## 首轮待验问题与范围限制

1. **本片固定安装和真实原件。** 需直接核非 editable 安装件与基线产品身份、283参考身份、当前配置及演示 Git 项目的隔离范围；随后核实际 HTTP baseline／runner／prepare 的原三文件和确认 SHA。原件目录已开始生成，尚未据此给出成功结论。
2. **真实 start／cancel／approve 组合。** 投递后扣住浏览器回复，再切实验／项目／tab，核当前 view、重新打开后的本地意图／回执、实际 Temporal 初始完整输入／memo和每 run 的 start／signal 数。恢复应维持相同 run／request／intent，不以读回成功替代停止或授权采纳。需分列真实服务与浏览器回执扣留，避免把传输观察器等同服务端重复投递测试。
3. **home 已变化与跨重启是不同前提。** `app.js:35`／`:49` 刷新 bootstrap 发现 home 变化会移除原 view，原 training `active()` 也拒绝缓存 home 已变的旧动作／回复。`web.py:432` 的 `create_app(home)` 在同一进程固定 home，产品页面无切 home 动作。另一个可达场景需人为同 origin 重启到新 home，保留未刷新的旧浏览器 form，并在新 home 重建同 project／revision／manifest；start body只含 revision／manifest，缓存比较本身不证明跨该场景拒绝。这不是本片已证实 finding；列作 G1 跨重启支持范围和探针前提，不凭缓存保护宣称跨重启保证。
4. **合成批准限界。** 需核明确标记的合成归档、原 evidence SHA、owner receipt 原字节／expiry、原 release 事件与集成／复验票据；只证明控制合同。真实 runner、模型、GPU、独立质量／性能 oracle 与实际集成／采用均不在此次通过范围，F9d／B3保持开放。
5. **收尾、自身审查与发布。** 所有自有浏览器／服务／worker／Temporal进程和端口需收尾；补本片实际 Ergora 模板输入及原回复。前继 `43583053417` 及其原 reviewer 门禁、本片精确发布与自己的必要 CI 均须按各自身份独立核，不提前批准。

现有测试保护丢 ACK、原 run／完整输入／memo冲突、来源漂移后的只读对账、receipt 缺失／expiry／格式漂移以及状态与停止语义，分别可见 `tests/test_training_submission.py:145`、`tests/test_training_cancellation.py:66`、`tests/test_training_release.py:86`／`:146`／`:165`；训练 suites 已在 `scripts/ci/linux-groups.json:84` 的现有分组内。本片尚无产品变化，没有新增测试／CI／断言的必要性；这些静态读取不构成本片测试通过。

## r1／r2 独立原件补核

直接读取本片 `.ergora/checks/training-control-journey/` 下的两个 journey／service 驱动、原浏览器脚本与 wrapper、两轮 `http.json`／被动 `http/`、`package-identity.json`、`prepared-originals.json`、CLI stdout／stderr／commands、r1 failure／cleanup及失败页面快照；追加读取 r2 `result.json`、三份完整 history、各原 intent／attempt／receipt、归档、原票据、`cleanup.json` 与 `browser-r2.json`。仅运行标准库只读解码／摘要／JSON比对，没有调用训练产品或服务。

- **安装与冻结输入。** 已独立重算 identity mapping 的604份源码／安装文件，均与记录的长度／SHA一致；源码和安装件各283份冻结 bundle与原manifest相同，运行目录复制的279份platform文件相同，另外4份顶层bundle交付文件不在运行目录复制范围。r1／r2 各28份准备原件均保留原字节。两轮三实验当前 spec 均等于各自 start 意图中的完整原 spec 与原 job request，manifest 的真实字节 SHA 均匹配绑定。合成 fixture 会重写原 manifest／spec／job request 路径，但本次设置的比较器／policy与原准备内容完全一致，独立逐字核未改变被冻结身份；不能把这种 fixture 泛化成允许修改已开始实验的来源。
- **原 r1 失败。** 首个浏览器因未指定已安装 Chromium 配置而失败；配置后实际 browser-r1 提交 gamma。原脚本 `browser-r1.js:14` 只等实验详情读取／heading，没有等 `training.js:166` 发起的独立 submission 读取；`:53` 即采整段 detail 文本。失败快照显示 beta、其原 workflow／run 和 submitted，没有显示 gamma 覆盖 beta。r1 未保存比较前的 `betaBefore`，故不能逐字重建具体差异；这个非稳定比较及快照不足以判产品缺陷。r1 的失败／KeyboardInterrupt 保留，不算完整旅程通过；`cleanup.json` 三组状态 cancelled／-9、两个端口 false，原浏览器 close 输出已核。
- **r2 驱动范围。** journey／service相对r1仅改隔离 run 目录和 service 文件名。浏览器 `choose` 改为同时等详情和 submission，并等实际状态 cell；切项目另等其空列表明确完成后再比较。未改产品来适配探针。`browser-r2.json` 实际13项／21样本／无 pageerror；three held分别为 gamma start→切 beta、gamma cancel→切 other、beta approve→离开到 overview。取消一项由私有浏览器 transport 在真实 HTTP200后替换成503，重返原项目读到同一 requested／intent。这证明浏览器丢回复后的原记录读回，不等同本轮注入了服务端 signal ACK 丢失后产生 unknown。
- **真实 r2 终态。** `result.json` 为35项／125.394526秒，7个CLI均退出0，28份Python聚合HTTP；92份被动原HTTP的request／response摘要已逐件重算，21份浏览器样本均能匹配其中真实 method／path／status／完整正文。独立解码 alpha／beta／gamma history，分别46／46／51事件，原起始完整Experiment、固定run与原意图memo一致；各只有一个原 signal，完整取消 marker／reason 或批准 receipt／evidence与各自checkpoint匹配。alpha控制Outcome为 CANCELLED；beta为 INTEGRATION_TASK_CREATED；gamma为 CANCEL_UNCONFIRMED，后来原executor result为 CANCELLED。二者分列，不能把后来的本地结果重写为控制已确认停止。
- **证据与票据。** beta原 evidence字节内容地址及15份artifact摘要逐件符合；synthetic标记明确。原owner receipt的字节SHA／expiry与创建attempt、ready一致，私有mode保持；release history的完整payload与该原receipt ID／evidence匹配。原票据绑定同一candidate／manifest／evidence且 `automatic_merge:false`，CLI与HTTP完整evidence／票据及三个submitted回执一致。当前只证明合成控制授权与票据，未验真实训练／质量／性能／集成复验／采用。
- **已核与待收尾。** r2 `cleanup.json` 三服务均 cancelled／-9、Temporal与Web端口false；未见runner marker或任何三实验 `started.json`。自身模板、最终交付／公开说明／引用清单和浏览器关闭等原件仍待最终补核；本轮不借前继在途CI或历史suite预批。

## 自身模板 finding 与重启补核

原安装件 structure-review 的完整输入／回复保存在 `self-review-r1-codex.json` 及其同名目录；本轮实际耗时57.411577秒，12份完整内联文件，decision 为 request-changes。回复明确限制自身未能访问 filesystem，因此不能替代本独立报告对基线、完整原调用者、fixture和原件的直接补核。其唯一 P2 经本 reviewer 直接读取私有驱动复核成立：

- **P2：失败仍可留下 passed，并失去后续清理观察（最终已关闭）。** `journey-r2.py:235` 在 `finally` 前写 `status: passed`；`:242` 的字典推导式依次调用 `future.result(timeout=30)`。任一调用抛错便跳过其余结果、`pool.shutdown` 和 `cleanup.json`；前面的 `except` 不捕获 `finally` 中的异常。该结果接口可能因进程创建／记录／回收失败而抛错。r3逐个收集结果及异常、保底尝试shutdown、记录清理错误／端口观察，并仅在清理成功后写passed，已修正这条清理路径。独立补读还发现：r3先赋非None的`execution`，再调用`save('execution.json', execution)`；若该staging写入抛错，except虽记录failure并重抛，finally仍能在清理成功后写passed，最终留下exit非0与passing artifact并存。最终r4将赋值写为`execution = save('execution.json', {...})`，只在写入成功后设置成功标记，并实证原异常／finally路径，见后文。父accept检查exit0保护r3本次成功取证，不代替私有result自身的失败语义。无需框架或产品改动；r2／r3真实成功原件保留，本finding关闭。
- **同型旧重启驱动已替代，原件保留。** `restart-r1.py:77–84` 同样先写 passed，再读取 server future、shutdown和清理记录；最终restart-r3已采用相同局部修正，没有覆盖原r1成功／失败原件。

直接补核 `restart-r1.py` 及 `restart-r1/` 的实际结果：从原 r2 `temporal.sqlite3` 重启同一 Temporal 服务，未启动 worker；16项检查、7个CLI均退出0，耗时7.936528秒。alpha／beta／gamma的原固定run和完整终态Outcome与r2一致；三份完整history逐字及SHA均与r2一致。gamma仍分别保留控制 CANCEL_UNCONFIRMED、后来本地 executor CANCELLED、fence true；取消读取／恢复为同一 requested意图，beta原批准回执仍为requested。清理原件记录server cancelled／-9，Temporal端口false。该事实仅证明**同一持久DB重启后的原终态读回**，不证明活动workflow恢复、worker重启、新home或跨机器恢复。

## r3 修正与最终 journey 原件

直接比较journey-r2／r3，仅隔离run／service文件名、初始化execution及上述清理／发布修正；service只变run目录，浏览器仍为同一模板。父驱动等待浏览器原passed回复、真实close和native退出0，并读取 `cleanup_passed:true`。实际35项检查、7个CLI退出0、28聚合HTTP，最终耗时90.444476秒；浏览器13项、21样本、3份扣留回复、一次浏览器端503替换，pageerror为空。`execution.json`与最终`result.json`分开，三服务清理均cancelled／-9，errors为空、双端口false；原浏览器close输出已核。文件mtime在此环境取整到同一秒，因此不把mtime作为清理／发布顺序证明，顺序依据直接读取的驱动及其退出0原件。

独立逐件重算r3的604源码／安装映射、283冻结bundle及279运行platform文件，全部符合；28份准备原件字节未变。92份被动HTTP的request／response摘要均符合，21份浏览器样本和28份聚合HTTP均匹配真实完整method／path／status／正文，最终CLI与HTTP完整回执／evidence／票据相同。三份完整history各46事件，原完整spec、job request、固定run、起始memo、唯一signal的完整payload及checkpoint均匹配；alpha与gamma控制Outcome和本地executor本轮均为CANCELLED，beta为INTEGRATION_TASK_CREATED及合成SUCCEEDED。r3 gamma与r2的CANCEL_UNCONFIRMED是不同run事实，不能混写或覆盖。

beta evidence内容地址及15份artifact摘要、批准意图全部原files、owner receipt原字节SHA／expiry／0600和ready／creation-attempt均符合；原票据绑定同一evidence／manifest／candidate且`automatic_merge:false`。三实验没有`started.json`，runner marker不存在。合成批准控制链与真实训练／质量／性能／实际集成／采用仍严格分列。

## 最终重启与自身复审

原restart-r2指向r3资料，但错误固定r2的CANCEL_UNCONFIRMED预期；实际stderr保留该断言失败，cleanup中errors为空且端口false，没有生成result.json。此失败不是产品停止语义缺陷。最终restart-r3仅把该观察改为与本轮原Outcome比较；相同DB、未启动worker，16项／7个CLI均退出0，7.658418秒，三份完整终态Outcome／run及history原字节均与run-r3一致。gamma控制CANCELLED与executor CANCELLED仍分别读取，取消read／resume的完整requested回执相同，beta原批准requested；cleanup errors为空、服务cancelled／-9、端口false，最终cleanup_passed为true。

自身structure-review r2实际55.810448秒、CLI退出0，17份完整文件共162,522B，decision为approve。独立按packet索引从原task逐字重取每个文件，长度／SHA均相符；其中7份产品源码仍与当前内容一致，后续公共文档按最终文本另核。request中的task／prompt摘要、168,854B原prompt与实际run输出目录的stdin完全一致，3份祖先／leaf指令和Skill正文完整包含。原result字节SHA、approve与review.md相符。该回复仅批准所提供源码和运行记录，不代替本独立文件审计，也不预批公共聚合、发布或CI。

## r4 私有落盘异常路径关闭

直接逐字比对，journey-r4只将r3的先赋值／再save合为`execution = save(...)`，其余源码和原r3路径均未改变；原r3文件与完整真实正例保留，**没有完整原生r4重跑**。r4源码SHA为`53b0f87066518b28d05a45f7f10b579ed5e98af1f906894618307a6f29ec6a8c`。`finalization-probe-r1.py`从r4实际AST提取最后赋值与原except／finally，仅省略真实操作body；独立AST比对提取文件与r4原节点完全相同，source／extracted摘要匹配实际原件。

实际两个scenario分别注入staging写入失败、首future失败，使用明确fake futures，不启动服务或产品。逐件核结果、calls与scenario目录：两者均收齐temporal／worker／web三future，执行stop／shutdown／cleanup且没有result.json。前者保留原OSError及failure.json，execution仍为None、未写execution.json；后者把原future错误记录于cleanup／cleanup-failure并传播RuntimeError，同样没有passing结果。这个直接执行最终原代码的异常实证与r3未变化产品的完整正例共同覆盖本finding，无需重复Temporal／UI或新增产品suite。self-review-r2发生在r4之前，其approve不代替这里的独立修正核查。

## 最终公共聚合与本地出口

直接读取最终计划、交付、公共evidence摘要、原F9合同、既有训练手册及新G1计划。现有手册已覆盖本轮实际baseline／runner／prepare、原ID提交／取消／证据批准与票据入口，本片没有新用户命令需要重复编写。原r1非稳定探针、中间restart错误预期、r2／r3取消时序、r3完整真实正例、r4仅fake-future异常路径及自身模型审查的先后范围均明确分列。G1仅细化安装／升级回退／换机及home跨重启支持前提，没有借本片实施或关闭它。计划／交付页首已把前继CI在途标明为立项时观察，并写明现有终态，未留下当前时态冲突。

公共索引固定**592条唯一引用／4,766,781B**；独立逐件读取每份实际原件，长度及SHA256全部符合，路径均在声明base内且非symlink。规范references数组SHA256为 **`3b0173c12f7e26e5ba4679be833830bfb9f1a74e3bc96c3ff3ef48fb6fb53e9f`**，与交付一致；publicmetadata逐项与原journey／restart／browser／self-review／probe／audit结果符合。该固定数组未递归包含本报告，后续发布与CI必须另列，不重生成旧数组。

总audit原件时刻为2026-11-14 10:20:36.615951 UTC：四个观察端口7233／33517／47493／56363均false，未匹配本片web／Temporal／原worker进程；三次成功浏览器daemon PID在本次只读补核时亦已不存在。各真实run原cleanup均关闭其端口；原reference verify退出0、283 PASS及stdout摘要逐字相符。已目视r3取消回读与owner回读两张1440px截图，不扩大为三宽或全部生命周期覆盖。没有启动runner或真实训练。

前继F10d7原reviewer的终态报告已直接读回，其固定完整8d739c2、自己的43583053417、八job／30必要步骤及原两轴approve／开放0／0按前继合同登记闭合；这里仅确认前继出口归属，不把它写为F9d1自己的CI。最终差异仍只有所属计划／交付／证据及前继发布记账，无产品／schema／依赖／test／CI变化。

**本片最终本地两轴approve，开放finding 0／0，唯一私有驱动P2关闭。** 可据本结论同步计划和公共摘要的本地审查记账；尚未发生的普通固定发布、完整远端Ref及本片自己的必要CI不在此approve内。真实GPU／B3、真实训练改善、活动workflow／worker恢复、实际集成采用及G1各自继续开放。

## 固定普通发布补核

2026-11-14，原reviewer按本片原合同，只读补核固定完整候选 **`593da960f9eb4039518cfae9119ddafc1f7a847b`**：**发布门禁需求轴approve、维护性轴approve，开放finding 0／0；私有驱动P2保持关闭。** 本节不回写原本地结论，也不批准尚未交付本reviewer的自身CI；未联网、安装、重跑服务／测试、改产品、提交或推送。

- 固定Git对象的唯一父为原完整基线 **`8d739c298668ab9f7d88fdaa205a21f304d9586c`**。实际11个变更路径全部为文档，与`static-final-r1.json`清单集合相同；逐件从Git读取blob，其bytes／SHA256全部与原静态清单一致。包含原本地报告**23,077B／`7e2af9f0fa8f913e980aafd07db3d7154ccf9731c68708b133ec7e7ed912bc72`**，亦与保留的`independent-local-r1.md`逐字相同。本节是发布后追加，不声称该补核已存在于固定本地报告。
- 直接从固定tree读取全部604产品文件，每份bytes／SHA均与原run-r3的非editable安装身份映射相同；固定变更没有产品、schema、依赖、测试或CI。故固定候选仍对应本地已审的真实r3正例、原终态同DB重启及独立r4私有异常路径，不把r4假future改写成完整原生运行。原完整staged diff check记录exit0，文档链接存在检查记录通过；本次仅读取，不冒称重跑产品回归。
- 固定提交与发布后公共metadata中的`raw_evidence.references`逐项相同，仍为**592条／4,766,781B**，规范数组SHA256仍为**`3b0173c12f7e26e5ba4679be833830bfb9f1a74e3bc96c3ff3ef48fb6fb53e9f`**。592份原件再次逐件重读，长度／SHA全部符合。新增`publication_evidence`的五份脚本／静态清单／commit／push／ref原件亦全部重算相同，与原数组路径不交叉，没有重生成或替代本地证据。
- 直接阅读`publish-r1.py`及原回执：commit退出0；唯一普通push argv为`git push origin 593da960f9eb4039518cfae9119ddafc1f7a847b:refs/heads/refactor/architecture-foundations`，没有force、`+` refspec、main或merge操作，退出0。保存的`git ls-remote`在**2026-11-14 10:32:53.585960 UTC**返回同一完整SHA与分支，本机remote-tracking ref也相同；远端结论只绑定该原观察时刻，本reviewer未重新联网读取。
- 固定提交已包含前继F10d7自己的CI／原reviewer终态登记；前继完整候选8d739c2、run43583053417的闭合按前继合同保留，作为本次发布的前置门禁，未充当F9d1自己的CI。固定公共摘要正确记录本地两轴approve／开放0／0，并将当时未发生的发布／自身CI保持pending；发布后metadata单列当前候选及五份发布原件，原reviewer固定发布与自身CI仍待补核，未提前记为已过。
- 本次读取工作树另有后继G1a计划／记账活动，均不属于上述固定11个blob或本片发布身份。本节仅评审固定候选与保存的原发布回执，不对后继产品或交付作结论。

**F9d1的本地与普通固定发布两个门禁已闭合，两轴approve、开放finding 0／0；该固定候选自己的必要CI仍pending，须另核完整run／job／必要步骤与原件后再闭合。** 真实GPU／B3及原本地结论列明的外部范围继续开放；不合main、不强推。

## 自身CI终态独立补核

2026-11-14，原reviewer按本片原合同，对固定完整候选 **`593da960f9eb4039518cfae9119ddafc1f7a847b`**、自己的Portability **run `43585798832`** 进行只读终态补核：**需求轴approve、维护性轴approve，开放finding 0／0；私有驱动P2保持关闭。** 本轮只读固定Git对象、原官方UI回执／HTML／JSON及公开状态，追加本报告；未联网、下载步骤日志或artifact归档、重跑测试／服务、安装、改产品、提交或推送。

- 独立解析`ci-list-html-r1/page.html`的官方embedded JSON，唯一匹配完整commit anchor、`.github/workflows/portability.yml`、`refs/heads/refactor/architecture-foundations`及本run；run number为**206**。原列表／discovery的In progress仍是发现身份时的历史观察，没有用终态覆盖旧原件。初始run页面完整SHA及job-batch摘要与`ci-ui-metadata-r1.json`的绑定均一致。
- 最终`ci-run-html-r4/page.html`的实际Status卡片为**Success**，完整commit anchor为该候选。其官方原URL与final URL相同，HTTP200；抓取回执时刻为**2026-11-14 10:47:50.907103 UTC**，正文**213,316B／`f8e3ad6680b24b009b3ed9ab4a6cab014cca92ed911d44f2ac23f062c8e6ffd3`**，实际bytes／SHA重新读取相符。
- 从该固定tree直接读取workflow和`scripts/ci/linux-groups.json`，预期为plan、六个Linux分组、Windows all，共**八job**；训练原suite保持在group5。原UI job-batch为`totalCount=8`、`hasMore=false`，八个ID唯一，名称／run与job路径和metadata逐项一致；早期batch的在途状态仅用于身份归属，实际终态另读下列每个job的最终HTML。

|Job|固定job ID|最终原件|必要步骤成功数|Complete job UTC|
|---|---:|---|---:|---|
|plan|132419880476|`ci-job-132419880476-html-r1`|1|10:33:00|
|Linux group0|132419910489|`ci-job-132419910489-html-r1`|4|10:36:37|
|Linux group1|132419910483|`ci-job-132419910483-html-r2`|4|10:37:59|
|Linux group2|132419910523|`ci-job-132419910523-html-r2`|4|10:37:55|
|Linux group3|132419910439|`ci-job-132419910439-html-r1`|4|10:35:01|
|Linux group4|132419910494|`ci-job-132419910494-html-r1`|4|10:35:42|
|Linux group5|132419910480|`ci-job-132419910480-html-r2`|4|10:40:03|
|Windows all|132419910615|`ci-job-132419910615-html-r3`|5|10:46:15|

- 用独立HTML parser逐件读取实际`check-steps`／`check-step`：八job均为completed，各有唯一成功且已完成的Complete job。**30个必要步骤全部success、带完成时间及`data-job-completed`**：plan的Read explicit test groups，七个执行job各自的wheel构建安装、参考身份、原回归、观察上传，以及Windows自己的PowerShell5.1安装／升级步骤。
- 全部**76个success步骤**的日志URL都精确包含同一完整候选SHA、该job ID和实际step number；每个开始不晚于完成，完成不晚于原抓取时刻。另有**六个skipped**，恰为固定workflow在六Linux job上排除的Windows安装步骤，没有其他失败或跳过。独立重建的八job／30必要步骤完整投影与`ci-terminal-r1.json`逐项相同；该原终态文件**13,357B／`ffa6c88777fe688df5e450fc058d1e82b556fe83405b652056a247e1c2dfcf2f`**已核。
- 直接阅读发现、fetch、metadata及parser脚本，未执行它们；全部**19组官方页面／UI batch回执**的原URL、final URL、HTTP200、长度和正文SHA均逐件相符。证据仅为官方公开UI HTML与UI job JSON，不扩大为读取步骤日志正文、REST响应或下载产物归档，也不据此编造测试case数或日志内容。
- 新单列**48条CI引用／3,326,398B**全部长度／SHA再核相同，路径唯一，与原**592条验证**及**五条发布**互不交叉。592数组与固定Git中的内容逐项保持，规范SHA仍为`3b0173c12f7e26e5ba4679be833830bfb9f1a74e3bc96c3ff3ef48fb6fb53e9f`，592原件和五发布件再次逐件重算相符；固定11个Git blob仍与静态清单一致。原本地／发布报告快照亦保持各自原bytes／SHA，没有用后续记账替换固定证据。
- 当前公开摘要、计划及交付的最新CI段均把本次Success归于固定593da96／自己的43585798832，保留等待原reviewer终核的状态；可依据本节同步终核与三门禁记账。工作树G1a的模板补丁、安装或其他后继资料不是该固定tree的CI身份，本结论不预批其产品、测试、安装、发布或CI。

**该固定F9d1候选的最终本地、普通固定发布、自身必要CI三个门禁均已闭合；两轴approve，开放finding 0／0，唯一私有驱动P2关闭。** 仅覆盖本片原合同与实际证据。真实GPU／B3、真实训练或质量／性能改善、活动workflow／worker恢复、实际集成采用以及G1各自继续验收；不合main、不强推。
