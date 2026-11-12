# F7d-D3b 独立审查记录

**最终判词：完整19文件候选的Spec／Standards均通过，开放finding 0／0；Spec累计SP1／P2一项已关闭，Standards累计0项。** 修后r2包、实际页面分段与独立顺序补验、151份HTTP、两轮模型全文链、四份公开证据及拥有资源清理均已核。固定提交 `18585dccf067c28e1c444df0c8daaa040b038568` 的Git对象、19件冻结身份、最终静态目标、r2安装包、作者普通提交／推送／SSH Ref回执与自身CI43155880413第五run及双OS七必要步骤均已独立离线核同，D3b的R4精确交付终结。此结论不借D3a证据，不覆盖D3c、整个F7或项目完成。初审漏报SP1的事实及各轮失败、修正和证据范围保留如下，最终范围见末节。

协调者 `f7d_review_context_console_review` 为本片新 fresh-context 审查者；`spec` 与 `standards` 两轴各由 `fork_turns:none` 的新上下文独立检查。采用 AI Hero code-review、maintainable-project-delivery／independent-review 与 codebase-design，依据仓库 AGENTS／PLAN、[原规格](../plans/2026-11-12-review-context-console.md)和[交付记录](2026-11-12-review-context-console.md)。没有继承实现会话或前片审查上下文。

## 范围与身份

固定基线与初审 HEAD 均为 `cae1dbb7f35ae76d9290b6e5c86f8445fd5f5ae5`，分支 `refactor/architecture-foundations`，提交区间为空。本轮实际审查未提交工作树：`git diff cae1dbb7f35ae76d9290b6e5c86f8445fd5f5ae5 -- README.md docs/PLAN.md docs/USAGE.md docs/architecture/current.md src/ergora/data/console/tasks.js src/ergora/data/console/style.css`；另全文读新 `candidate-review.js`、本片plan及delivery，不能用空的三点HEAD差异代表候选。同期D3a审查记录的精确交付补记仍属D3a，不转授其CI。

|产品文件|初审 SHA256|
|---|---|
|`src/ergora/data/console/candidate-review.js`|`445a6c25a1803a5a3ce8879e7a00f0e7c9c176ce9e1e517355a7fe93c991ee04`|
|`src/ergora/data/console/tasks.js`|`3a39a3cbb93147c7dd9feffa912027d4aeb130e76af54bbccc83eb893474c3db`|
|`src/ergora/data/console/style.css`|`565827b794646055bf33ac0771935fc23a7ce619df58b36a7bf5d1b5163603d8`|

必要邻接读取包括 `issues.link_review / review_link / _review_link`、对应Web DTO／路由、后端来源候选准入、console api／ui／modal、app与tasks的任务／run／导出生命周期、相邻candidate-observation及原关联／架构suite。未扩成全仓审查。

## Standards

独立轴结论：**hard violation 0；无可成立的heuristic smell finding。** 新模块只有tasks一个生产调用者，但小Interface内聚完整保存、原字段恢复和独立SHA读取；内部函数隐藏其交互复杂度，职责拆分成立，没有虚构复用或扩展点。

原请求只捕获一次，fieldset锁定保留未知结果的字段，writing保护同一请求的重复发送；SHA代际、modal内容及tasks传入的存活条件保护输入修改、关闭重开和上下文替换后的迟到结果。校验、幂等、冲突与持久化仍由原后端拥有；新增guard各有可达条件，没有发现重复的后端身份校验。没有新增backend、schema、table、provider分派、依赖、永久test、CI、后台轮询或自动重试；相邻观察产品未改。

## Spec

独立轴结论：**缺失／部分实现、范围外行为、看似实现却错误的行为均无发现。** 已核原规格第7、9、11、13、17行：原v7／exported入口固定task／run／candidate／branch／revision，操作者明确输入已有目标；未知结果明确恢复原幂等POST且说明可能首次保存；title／body／完整record安全文本展示，各base／diff事实分开；登记检查前的任务页入口支持独立SHA读取并保留项目隔离。

本结论限当前静态实现及已给原件，不把安装测试等同页面验收，也不把本地上下文等同批准、原发送确认或创建PR／MR。

## 已核原件与限制

协调者只读重算r1 wheel、源码／安装字节、两RECORD及manifest。wheel SHA256为 `810bb1e8b5e8db534fb6b0892ca4d39ae562d03bd9beac0fb14f2e2bda616818`；450件源码／wheel／非editable安装内容一致，wheel RECORD455行与installed RECORD460行的全部带摘要项和大小匹配，283件冻结参考符合原manifest。

原关联／Web／架构suite stdout为 **74 passed／59.03秒**，命令exit0／61.42秒，stdout SHA256 `751501c788e11328955195fedbe33b85b793cdb1c5ed3f467ee66de6e119351e`；reference verify为PASS／283／runtime_started false。两provider原生种子stdout为 **2 passed／22.86秒**，命令exit0／23.95秒。三份stdout均重新核同原回执摘要。种子沿原v7发布／提交／Git导出owner，Temporal SDK受控、REVIEW_READY合成；没有新的完整六阶段、模型或真实SaaS验收。

本次未重新安装、运行suite、浏览器、模型或联网；仅写本报告。尚缺两provider实际页面保存、丢失回复同槽恢复、离线读／冲突／修订及迟到反例、原对象保持、拥有资源清理、实际成本、截图和真实内置模板的原件。最终完整候选与精确提交／Ref／本提交自身CI亦待核，不借D3a证据提前结案。

**初审汇总：Spec 0项、Standards 0项；两个轴均无最重开放问题，完整本地出口待验收。**

## 同片复核：SP1与首轮内置模板

**SP1／P2：初版错误地从`fresh_observations=false`推断本次未读取平台。已关闭。** `candidate-review.js:71` 初版“本次没有重新读取平台”在并发首次保存时不成立：两个请求均可在入口查不到原槽，分别完成五次provider GET；后提交者在`issues.link_review`末事务的`previous`分支发现原记录，再由`existing()`返回`fresh_observations=false`。该标志描述返回资料，不能证明本次调用的读取成本，违反原规格第9行的事实区分要求。原并发suite也包含先读取、再竞争同槽的路径。

最小修正仅改成“返回原已保存关联；显示的是原不可变记录，新的原因不覆盖原内容。”原Spec轴与协调者均核到该句同时适用于入口命中与末事务命中，SP1关闭；Standards轴核到无新增分支、guard、请求、test／CI或职责变化。USAGE、本片plan／delivery已解释并发语义，后端保持。修后候选JS SHA256为 `33daf614ebc8ac5b8cdc677a4301a4828ac7ffc12ed82fa7f6986c12972bbb18`，相对r1包恰仅此一件包文件改变；原r1安装和模型判词不能转授修后字节。

首轮真实内置结构审查run `d4a721e0dc1e40e0bccea5d60cb1ccd6` 为Codex／gpt-6.1-sol／high，**request-changes／229.00秒**，原结果SHA256 `789a8fba9a84c9d3d598f6a44dccf35b7d9cbeb69420bef1863ab2974872eba3`。协调者独立只读重算manifest、prepared／actual完整文件树与执行位身份、composition、prompt／stdin、admission／policy、scope与native receipt、原结果及九件冻结附件。190,129B附件SHA256 `ce226ef9233fc536e22456553ff5631b8aeaf71ceb55740605a49bac26b26a9f` 与原索引一致；五scope均连续UTF8至null，候选资料11页，list完整一次、失败调用0。原内置workflow／agent除证据资源、修订及材料预算外均保持原定义和资源字节。

四个采样所属进程按pid／starttime已无同一存活进程；不扩称全部短命进程或OS隔离。此审查只覆盖九件冻结附件，不代替页面、最终文档、独立审查、精确交付或双后端成功。首轮request-changes保持；修后新包、受影响页面与聚焦模板仍待核。

首浏览器驱动的原记录为exit1／result null／72.99秒，`route.fetch`在30秒超时，不能记为页面通过。独立逐件重算该服务14份HTTP的sidecar与原request／response长度和摘要，均匹配；其中实际保存POST为200／39.19秒，返回`fresh_observations=true`及原记录SHA `8465b2798c7f5a05db7202b8466f721fc2dcc9db33bf3a6ef296dbab5efadfef`。夹具日志故障令该段provider trace为空，不能由此推断零provider读取。失败、已保存原槽与该计时范围均保持，后续须沿原ID续验；不重建任务、复写原来源或把失败改成通过。

## 修后r2包与聚焦内置复核

协调者独立重算r2非editable包：wheel SHA256 `ed20d152eb566261d883b0942f1fef3db2b3ca70f2778607ddf9bfa20e1fabec`，450件当前源码／wheel／安装逐字一致，两RECORD仍为455／460行、摘要及大小全符，283件冻结参考保持。相对r1恰只变更candidate-review文案一件，其他449件及METADATA相同；没有把原74项改写为r2重跑结果。

聚焦run `547b572e661e41ec9e8b96cf08c98e24` 为Codex／gpt-6.1-sol／high，**approve／88.76秒**。协调者独立重算同一manifest→prepared／actual→prompt／stdin→admission／scope／native→原结果全链，五件完整附件42,374B／SHA256 `21228d3f999b5f1d1405d4892c8883ca6bcea44d6385cc16a15ec63c97072e86`；五scope连续UTF8至null，候选资料5页、list完整一次、失败调用0，四个采样所属进程无存活。原结果SHA256 `018eed2fe8caacf5a2d728cdc63b23fb279c57083be1fbafae8bc1605ac23430` 与原review全文一致。冻结的candidate-review、issues、ui仍与当前字节一致；plan／delivery后续状态追加不在该判词范围。原模板资源保持，approve只覆盖五件冻结附件，不代替完整最终候选或页面验收。

主浏览器续段原结果为`passed:false`／157.53秒，记录已完成39项检查、页面错误0，随后等待固定为demo的私有响应谓词超时。已完成项覆盖两provider明确保存与原请求恢复、完整安全记录／正文、各base／diff事实、冲突／reason不覆盖、独立离线读及两视口。该段整体失败保持，余下跨项目／生命周期及清理、实际HTTP原件待续段终核；不将39项改写为完整页面通过，也不重复运行已完成项。

## 生命周期分段与证据精度

生命周期原输出为28项／64.35秒、`passed:true`、页面错误0，覆盖跨项目拒绝、SHA编辑、关闭重开、切项目／视图、POST替换、旧修订拒绝及任务文件不可用／token移除／tracker改绑／provider离线时读取完整原记录。协调者检查脚本与原gate回执发现其中一项顺序证据不足：同一表单首请求未完成时，ui.form的submit处于disabled；旧请求0079在45秒自动释放后才点到新错误，`gate_released=false`，故不能称“新错误先到、旧成功后到”。其余五份实际hold为明确release／true。该私有驱动问题不要求改产品guard；原28项输出保持，所缺顺序须用关闭重开的新form单独补验。

协调者已逐件重算前三服务共131份HTTP的sidecar和request／response长度、摘要，全部一致。后段记录9次provider GET；首段日志缺口保持，总provider读取数未知，不能把9称为全程总数。页面阶段所有非GET的产品请求均为本地candidate-review-links POST，没有平台业务写入或新执行路径。九次POST为六次200、三次400，原owner处理时间最小0.00983秒／中位1.47935秒／最大39.19104秒；记录计时在gate等待前结束，不含故意hold。这是本地夹具与原Git／控制面owner成本，不是SaaS延迟或整段浏览器耗时。

两provider各44件runtime文件、各28件repo文件已重新实读摘要，原完整snapshot与不可变review记录、原Git候选均保持；每份原创建记录的七文件在种子时匹配，后续runtime字节保持。控制面只新增各一份review记录，agent_runs、issue_task_links、issue_writebacks均为0；显式revision／rebind控制导致的项目状态变化不称完整DB未变。已实际查看两张最终桌面／移动原图，记录SHA与候选长文本换行可读，表格和页面没有横向溢出；公开副本与最终完整候选仍待核。

## 完整最终19文件本地终核

基线与HEAD仍为 `cae1dbb7f35ae76d9290b6e5c86f8445fd5f5ae5`。清单与Git差异／全部untracked集合完全一致：**11件tracked＋8件untracked，共19件**；清单SHA256 `0ad4fb93be43313e069c1e479ff2d1af4af5867510b726967717054d0c40453d`。范围包括三件产品，README／PLAN／USAGE／当前架构／本片plan与delivery六件入口状态、本报告、四件本片公开证据、三件D3a精确交付后补状态，以及all-in-one／project-trackers两件上层计划。全部tracked变更、新文本／JSON全文及两PNG均已核，不以原九文件范围代替完整候选。D3a的Git／Ref／CI由原片评审处理，本片仅核后补记账范围和不转授关系。

原Spec轴对完整19件的最终结论为：**无新增缺失、范围外或错误实现，SP1已关闭，开放0。** 原Standards轴的最终结论为：**hard violation 0、可成立heuristic smell 0，开放0。** 单调用者内聚owner、固定原请求、原幂等POST恢复、安全全文、独立离线SHA入口及迟到隔离均保持；没有新增后端、持久表、provider分派、依赖、test／CI、轮询或自动重试。最终三产品SHA分别为：

|文件|最终SHA256|
|---|---|
|`candidate-review.js`|`33daf614ebc8ac5b8cdc677a4301a4828ac7ffc12ed82fa7f6986c12972bbb18`|
|`tasks.js`|`3a39a3cbb93147c7dd9feffa912027d4aeb130e76af54bbccc83eb893474c3db`|
|`style.css`|`565827b794646055bf33ac0771935fc23a7ce619df58b36a7bf5d1b5163603d8`|

顺序补验最终为 **5项／4.396秒通过**：原GET200被持有，原表单submit确为disabled；关闭重开新form先收新SHA的实际400并显示错误，再明确释放旧200，原错误保持。协调者核到r3 HTTP0019的`gate_released=true`，0020新400在最后显式release前；0008／0015两次早期尝试均自动释放／false。前两次补驱动分别为31.00秒exit1／无result及48.83秒`passed:false`，由原按钮busy标签选择错误引起，不能记作产品并发guard失败；原件与边界保留。此补段单独证明所缺顺序，没有重跑主39项或其余生命周期。

最终视口原记录为 **3项／1.52秒**，1440／390的document宽度等于viewport，各记录table的scrollWidth等于clientWidth。两张公开PNG与已查看的原图全字节一致；桌面201,895B／SHA256 `14e2a4a8365a501a37c277c6199889cd8f4496c7c8939b5143eef52c93cce56d`，移动76,912B／SHA256 `e8e5b7551ecefc8d08e151053d62c83a8c095a8f8775d0031b8ca9bfecc6dbae`。

四服务共 **151份HTTP** 的sidecar与全部request／response长度和摘要重新核同。九次本地POST和后段九GET保持前述范围；首段provider日志缺口保留，总读取数未知。四个原PID按starttime无同一存活进程，读取内核监听表确认十个所属端口均无监听，四服务线程停止回执及三次命名浏览器close exit0均符合原件。只核拥有资源，不推全系统清理。

协调者按私有映射逐字段重建七段浏览器投影、二轮模型身份／读取审计／原result、包／delta／安装／种子／清理及二十个样本字段；四件公开证据均与原件一致，无机器home路径。公开acceptance SHA256为 `265a15d2a4289ee3eedc22b8a47a558fbece1d2abf9e6559748f3356afa1f835`，self-review为 `fcadc46359ac65f84041d711797e694b7988b5ea413e1e97a24dabb8a03dbc3a`。39项后的驱动超时、28项中的顺序限制、两次补驱动失败、首段日志缺口和模型原request-changes均准确保留，不能相加成一次完整成功运行。

作者`static-r2`原件覆盖当时19件、347个本地Markdown目标、6个加载秘密值，issue0／whitespace exit0；评审未读取秘密值。该结果不证明anchor、外链或Mermaid渲染。本报告末次结论与后续状态收口会改变文档身份，冻结前须保存最终静态身份；不为状态记账重复产品或模型。评审只读核验并仅写本报告，没有重新安装、运行产品／suite／浏览器／模型或联网。

**最终汇总：Spec累计1项P2已关闭、Standards累计0项；开放0／0，完整19文件独立本地审查通过。** 下一步由实现者同步R3状态并冻结最终静态／候选，再完成R4普通提交／推送、精确Git／包／Ref和本提交自身双OS必要CI原件终核；当前不构成精确交付、整个F7或项目完成，也不扩称真实SaaS、原生Windows正式工作区或新六阶段模型验收。

## R4固定提交与作者交付回执离线终核

本节在固定提交后追加状态；上述本地终核与各轮失败边界保持。唯一核验目标为 `18585dccf067c28e1c444df0c8daaa040b038568`，唯一父提交为基线 `cae1dbb7f35ae76d9290b6e5c86f8445fd5f5ae5`，目标分支为 `refactor/architecture-foundations`。作者原件位于私有 `.ergora/checks/f7-review-context-console/` 下的 `static-r3/result.json`、`commit-closure/ready-r1/`、`commit-identity.json` 及commit／push／ref的JSON和原始stdout／stderr；只读了原脚本，没有执行冻结、提交或推送脚本，也没有联网。

协调者通过禁用replace、lazy fetch、全部传输协议与可选锁的只读 `git cat-file --batch`，独立重算2个commit、165个tree和409个唯一blob的Git对象头／正文SHA1，并完整遍历父／目标文件树。目标root tree为 `89a8d93b0b9b23c6ede3bd42ef7f8359424b507a`，两树差异恰为原19件，均为mode `100644` 的普通blob；每件字节、大小、SHA256及mode均与ready冻结文件及最终静态身份相同。ready manifest SHA256为 `af4712d4e8dd01108ca4a44702dd366bf0dbe41dab2b589d23ed603b99d05a6c`，提交内本报告SHA256为 `182daa29c185476d067369a035f9e1a94b783cdf767f1f16651d4bd1404d597e`，均吻合作者 `commit-identity.json`。本节及顶部新状态属于提交后的未提交报告追加，不属于该固定blob，也不改变原19件冻结身份。

包身份改为直接对照该提交的全部450件 `src/ergora` blob：文件集合与r2 wheel及非editable安装完全相同，全部字节一致。wheel SHA256仍为 `ed20d152eb566261d883b0942f1fef3db2b3ca70f2778607ddf9bfa20e1fabec`；wheel RECORD455行、installed RECORD460行的全部带摘要项及大小重算正确，283件冻结参考符合manifest。wheel METADATA内README正文与该固定提交README逐字一致。此处没有重新安装或运行产品，也没有将r1的74项原suite转称为r2或本提交重跑。

最终静态范围从固定提交blob及完整文件／目录集合重建：19件候选、348个本地Markdown目标，缺失0；两件变更JSON可解析，没有机器home绝对路径；基线到目标 `git diff --check` exit0。作者 `static-r3` 的19件身份与提交全符，其19／348／6个加载秘密值／issue0的原范围保持；协调者没有读取秘密值，6值秘密扫描仍是作者证据。这里没有验证anchor、外部URL或Mermaid。公开acceptance继续保留其生成时review-pending快照，最终状态以本报告及交付记录为准，未改写投影或沿用旧静态身份代表新状态追加。

作者普通提交命令为 `git commit -m 'feat: associate saved PR and MR context from the task console'`，exit0／9.808120832秒。原stdout为806B，SHA256 `8d3c33e5c0970ee18a9114b0eede7fe7d3274f8afee3747566a18eadc5ef43fa`，stderr为空；包含固定提交短SHA及19件／1308行新增／15行删除，已与只读提交numstat独立核同。

作者普通推送命令为 `git -c remote.origin.url=git@github.com:626619403/Ergora.git push origin HEAD:refs/heads/refactor/architecture-foundations`，exit0／9.995409560秒，`force:false`且无force参数。stdout为空；stderr为98B，SHA256 `50a2a5acb6db2cec037cd7a34357481c3eb389e7d9518df6337dfa86ce3162fe`，原文为目标GitHub仓库及 `cae1dbb..18585dc  HEAD -> refactor/architecture-foundations`，符合从固定基线到目标的普通推送。

作者随后执行 `git -c remote.origin.url=git@github.com:626619403/Ergora.git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`，exit0／2.302372103秒。stdout恰为86B：目标完整SHA、一个TAB、`refs/heads/refactor/architecture-foundations`及一个LF；SHA256为 `6f18490fa8e3d9d1650bec063ed8c2a64130ff35ae29dde4b7b507a55b9d93e6`，stderr为空，与 `exact_remote_ref:true` 一致。空输出的SHA256均为 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。这是对作者SSH Ref原回执的独立离线核验，评审者没有发起或完成直接联网Ref查询。

**R4当时汇总：固定Git／19件ready／最终静态／r2包／普通提交与推送／作者SSH Ref原回执通过；本提交自身双OS必要CI原件仍待作者采集后独立核验。** 彼时首份CI API样本尚在采集中，本节未给CI判词。后续只核本提交的精确run／head、两job及固定workflow要求的七个必要步骤，并保留各次样本与错误；D3a的CI不转授。本节没有触发重新安装、suite、浏览器、模型、联网或递归审查，未据此提前宣称R4、整个F7或项目完成。

## R4本提交自身CI与精确交付终结

作者后续给出官方Portability run [43155880413](https://github.com/626619403/Ergora/actions/runs/43155880413) 的完整离线原件。协调者独立重算 `actions-index-r1`、`ci-run-html-r1`至r5及两job的八份完整HTML与各receipt的字节数／SHA256，全部相同；各receipt均为HTTP200、原URL与final URL相同。Actions索引内只选择本run158，确认push、Portability、`.github/workflows/portability.yml`、目标分支和完整提交链接；没有使用同索引中的D3a或其他run判词。五份run页面均连接完整目标SHA `18585dccf067c28e1c444df0c8daaa040b038568`、`refs/heads/refactor/architecture-foundations`及同一workflow，前四份Status为 **In progress**，r5为 **Success**，未改写早期非终态。

|原HTML样本|字节数|SHA256|
|---|---:|---|
|`actions-index-r1`|320027|`60e2d1d7114a00bfbbe5818a1e458de7def61a4ce910610c7b0ede5024f272f2`|
|`ci-run-html-r1`|150656|`8ecb3d7869c32ff90c24e0aa3f7ec0dc7790b2389595f8024926f23e100b5ec8`|
|`ci-run-html-r2`|150657|`d0857de13c63f913aa0194953661ea40b428829d23a1934f9aed2a6dc694e480`|
|`ci-run-html-r3`|150657|`35bbbf894fb1c6b1fb17b55b1eb8fab901c05307407292fc03b6272767ff55ea`|
|`ci-run-html-r4`|153416|`0c222d82364b40401c788b7d3876a1bb9868d720a4ce54f7ddc191baae78c5a0`|
|`ci-run-html-r5`|157122|`0deca65c63f5d887b21666c163f598a9360bdcbe9ab7bc19037679d307de1a92`|
|Windows `ci-job-130975573184-html-r1`|159757|`c79412b2a8d417ccd03a92949ced0c1ca156cf71644717b62e2f2e64a173f321`|
|Linux `ci-job-130975572836-html-r1`|161670|`e77639b7effc3efec2d6daf437fe007c45b4588742392edb09145ac5c90657b8`|

必要范围直接从固定提交内workflow读取，SHA256为 `81c168fdb140f44ccfdca497003e452355c9164a6ed6f8dfb8fa31729a1943ca`，未借当前工作树或其他候选workflow。矩阵恰为Ubuntu／Python3.11和Windows／Python3.12。Windows job `130975573184` 为 `native (windows-latest, 3.12)`，Linux job `130975572836` 为 `native (ubuntu-latest, 3.11)`；两页 `data-job-status=completed`，Complete job均success。逐项读取的必要步骤如下：

|固定workflow必要步骤|Windows|Linux|
|---|---|---|
|Build and install wheel|step4：success／completed|step4：success／completed|
|Packaged reference identity|step5：success／completed|step5：success／completed|
|Native application regression|step6：success／completed|step6：success／completed|
|Windows PowerShell 5.1 installer and upgrade|step7：success／completed|按原Windows条件skipped，非Linux必要步骤|

以上七个必要步骤均有成功conclusion、明确开始／完成时间及 `data-job-completed`；时间先后与相应作者采集时刻相符。七份 `data-log-url` 均精确为 `/626619403/Ergora/commit/18585dccf067c28e1c444df0c8daaa040b038568/checks/{本job完整ID}/logs/{本step号}`；两页其余成功步骤的路径也绑定同完整SHA及本job。独立从原HTML重建两job身份、各必要步骤的name／conclusion／started_at／completed_at／job_completed，与 `ci-html-final.json` 全字段逐项相同；其run／candidate／r5正文SHA、job映射及两receipt SHA也全部一致。该精确投影SHA256为 `9a48fddab2e79c7dfdff07af6249b99d1e6ab4c0469cbd83c25a29404cd85037`。

最初匿名REST原body仍为280B／SHA256 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`，HTTP403／API rate limit exceeded，与原 `ci-sample-error.json` 的精确目标SHA及官方runs URL相符。REST403、索引In progress及前四run的非终态均保持，后续HTML终态没有把这些原件改成成功REST。此终核只基于作者保存的官方公开run／job HTML及回执，没有下载或审阅完整job日志，也没有发起评审者独立直接网络请求；步骤摘要不扩称全量日志、测试数或原生Windows正式工作区验收。

**R4最终汇总：本提交自身CI43155880413的r5终态Success、Windows四／Linux三必要步骤success／completed及原件投影均通过独立离线终核；结合前节已核的精确Git／19件ready／包／普通提交推送／作者SSH Ref，D3b精确交付终结。** Spec／Standards开放仍为0／0；既有失败、请求计时、模型和产品验收边界全部保持。本轮仅追加本报告状态，没有重新核验已通过行为、安装、suite、浏览器、模型、联网或递归审查。D3c由其新的独立审查者另核，整个F7及项目仍未完成。
