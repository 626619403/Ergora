# F9a 训练工作台独立结构、性能与冗余审查

日期：2026-11-14。审查者：Codex 独立 fresh-context agent `f9a_structure_review`。项目与文档均归 Ergora。本轴先读 `AGENTS.md`、总计划第8节 F9、本片计划和真实源码／调用者，再读作者交付；应用 AI Hero 索引、codebase-design、code-review、maintainable-project-delivery 及其 independent-review brief。未改产品、Git 或原生运行记录，未安装、启动服务、调用模型或执行训练。

## 范围与结论

固定基线为 `47443840b68693f63ee011dc6fbe29421a42223f`；候选为未提交工作树。初审精确15文件及 SHA 位于本片私有证据 `review-r1-files.json`，tracked 差异为 `review-r1.diff`；完整读取新增 `training.py`、`training.js`、`test_training.py`、计划及交付。15文件包含上述新增项、reference／CLI／Web／console app与index、Linux分组、README／TRAINING／current architecture／PLAN。H3b 原审查附录仅是前片状态记账，未纳入本片产品判断。

|审查方向|结论|
|---|---|
|本轴覆盖的 F9a 要求及行为|两条 P2 已修并按原场景独立复核；当前开放0。完整需求符合性仍由独立需求轴判断。|
|职责、Interface 与结构|修正后通过。未发现新的职责上移、无实际消费者的抽象、第二实验表／队列／调度器。|
|性能、冗余测试／CI／断言|未发现额外可行动 finding；测量范围和未验条件见下文。|
|最终本地证据出口|r3包／实际页面／原生只读／自身展示复审及清理原件已核，本轴通过；发布和本候选CI另核。|

两项修复后的 r2 产品身份：`src/ergora/reference.py` SHA256 `31f95d6c48c2a7462c2aa0b7b514e1d4ad21636c55c3619684b9973912d7ec94`；`tests/test_training.py` SHA256 `054dd01f52e541164aca666d0fb235be65e8493cfdc143410524ee3905ea7a4e`。r2审查时其余初审产品文件未变化。完整复核时文件身份保存在 `structure-review-r1/fix-recheck-files.json`；另已核对作者 `review-r2-files.json` 的同一源码身份，并补读 TRAINING／计划／交付中的修复及进度更新。随后 r3 的单文件展示修改单列于文末。

## Findings 与关闭依据

1. **P2，共用配置／状态目录的合法配置被误拒绝，已关闭。** 初审 `reference.py:381` 以 `storage == config` 推导摘要的 `config/` 或 `state/` 标签；现有 registration schema 与 `_execution_directories` 允许两目录相同，原生布局也不冲突。独立复制同一份原生 prepared 合同：分目录时 list／show 成功，共目录时登记仍为 published，但 list 全部变成 `state/...` KeyError，show 为 BLOCKED。后果是支持范围内的配置无法观察任何实验。最小修正是让逻辑来源显式选择目录和标签，保持原配置范围；作者已在 `reference.py:373–382` 实现 `configuration` 选择，并补现有 fixture 的共目录回归。原复现修后两种布局均 list=1、show 成功，且同时保留正确的 `state/` 与 `config/` 摘要标签。

2. **P2，两个仓库归属见证皆缺失时跳过验证，已关闭。** 初审 `reference.py:424–435` 的 current runner 与 original job request 都可选，二者皆无时两次 `check_runner` 都跳过。独立场景将已有 prepared 记录复制到隔离状态目录，以相同项目ID登记另一个真实 Git 根，并保留缺 runner／未有 job 的布局；list 返回1条、无错误，show 返回完整原 manifest，尽管原仓库与所选仓库不同。后果是无法证明归属的记录被作为当前项目实验公开，违背固定项目／Git根关联和缺失明确显示的要求。最小修正是仅在两个见证皆无时明确拒绝，继续允许已冻结 request 独立证明归属。作者已在 `reference.py:426–427` 加该检查，并用一个回归覆盖缺 current但有request、皆缺、恢复current的连续行为。独立复核原场景：list 单列错误且不返回该实验，show 明确 BLOCKED；只有原 request、或只有 current runner 的有效记录仍分别接受。

原失败原件保留在 `structure-review-r1/configuration-result.json` 与 `structure-review-r1/missing-owner/result.json`，修后独立复核为 `structure-review-r1/fix-recheck.json`。发现2条 P2，关闭2条，开放0；未用通过的大测试代替原场景复核。

## 结构、性能及冗余证据

`training.inspect` 有 CLI 和 Web 两个不同生产文件的真实消费者：项目／模板准入、原查询与结果语义集中在同一 Interface。移除此 Module 会把这些语义散回两个入口，因此它有实际 Leverage。原布局读取、绑定核对和进程环境归 reference；私有 document／inspect／check_runner 是同一读取算法的局部实现，无需为了单独复用建立新抽象。页面只消费投影。没有按厂商类型分派，也没有把 perfctl、Experiment、调度、审批或统计重算复制进上层。

核对了原 `agent_platform.training` 的 prepare／create_job_if_absent／fence 产物、`training_executor` 的 result／gate／negative-result 写入者、perfctl 和 Experiment validator，以及既有 task reader、safe-file、有界读取和 Windows reader。文件／binding／SHA／路径检查均有外部原件损坏或归属错误的可达条件；未发现应删除的重复上层 guard。当前两条修正都落在拥有原件语义的 reader。

列表正文最多检查 `limit` 个条目，坏条目也推进游标；使用 heapq 只保留 `limit+1` 个候选名，但每页仍遍历该项目所有目录名，复杂度为 O(N log(limit))、候选内存 O(limit)。有界实文件审计使用37个目录、limit=2：首坏页成功读取1个 baseline／352B，中间页成功读取5文件／5,443B；两页都遍历37个目录名，reader 内部分别约25ms／29ms。证据在 `structure-review-r1/io/result.json` 及其逐页输入／输出。它证明本页正文有界，不能推导超大目录、慢挂载或 Windows 的延迟；没有据小样本报吞吐提升或性能退化。每文件1MiB、独立进程30秒上限及离线观察范围保持。

页面只在进入训练导航时读取列表，首页 dashboard 没有附加训练扫描。核对 `app.js` 的切项目／重绘调用与 `training.js` 的 DOM存活、项目、tab、控制目录和各自请求序号检查：旧页面或旧详情响应不能回写当前页面。补读浏览器 r1 原快照，以及 `browser-r1/late-project-r2.stdout` 中实际 `route.fetch` 取得原详情、切另一项目后再交付响应的脚本与成功断言；`list-lifecycle-r1.stdout` 另核两次真实列表响应倒序交付时旧 sentinel 不出现。这些证据支持原生CPU详情、跨项目迟到详情和同页迟到列表的已验证范围。r1至r2的前端字节未变；本轴未自行启动浏览器，不扩大为所有迟到响应排列或所有平台的交互验收。

新增 suite 只在原 Linux 显式分组登记一次，未添加第二套 CI。原件不变、未知状态／负门禁、坏条目分页、baseline漂移、精确绑定／SHA／路径篡改、跨项目、字节上限与 CLI／HTTP一致性都保护真实观察合同；新增共目录和双见证回归对应本次静默错误。未发现将默认参数或示例配置当成产品限制的断言，也未发现仅复述实现、仅识别已删除接口或为文案建立的测试。

## 验证与证据限度

本轴亲自执行的检查仅为私有目录中的有界复现、原场景修后复核、I/O计数及哈希核对。283份冻结参考逐字无差异；原生 r1 的18份配置／状态原件在审查后仍与原摘要相同，见 `structure-review-r1/original-identity-recheck.json`。

已读取作者原命令／stdout／result：首命令缺 basetemp 父目录造成11个 setup 错误、14架构项通过；修命令后的 source-r2 为25 passed／12.25秒。修共目录后的 source-r3 为26 passed；两修正后的 source-r4 为27 passed／13.09秒（受控进程13.527秒）。未由本轴重新运行这些 suite。

安装 r1 原件显示非 editable、563产品文件、wheel与installed两份RECORD、283冻结参考；六suite为121 passed／87.23秒。native-r1 为未变原owner的 init／runner-add／prepare、create_job_if_absent／fence_and_lookup，9.488秒；没有 Temporal运行、runner执行、MLflow查询、GPU、统计复验或采用。以上 r1 成绩绑定修前候选，不自动覆盖本次两项产品修正。作者自身模板 r1 的 request-changes 及其相同归属 finding 亦保留，不能称修后模板通过。

修后安装 r2 的 `package-identity.json` 已读取：wheel SHA256 `5fa33e011a0b1a2e50e0346e8737d1f7604053e71043855a361f7c2d6c32650b`，非editable、563产品／两RECORD／283参考，与源码一致。本轴另用该环境的 Python `-I` 直接执行原私有三场景，确认包位置来自 r2 的 site-packages、reference SHA与修后源码相同；分目录和共目录 list／show 均成功，缺两见证明确失败。每场景约0.2秒，原件见 `structure-review-r1/fix-installed-r2.json`。

后补 r2 原件已核：三安装suite为33 passed／16.98秒（受控进程18.616秒），`native-readback-r2.json` 核当时563产品字节与源码一致、原18件未变、读取同一原生 manifest／job／fence；没有新增派发或执行。自身原模板 r2 实际23.977秒、approve，完整11文件187,590B；原 input digest `dc70a489b39a1fc7b99edb99c9009bf62c6f4018155dbc15b8e069397500fe3d`，原 result SHA256 `4b278acc472436d19163fb5f433d9e8724721664353f4efe4fa2a829badc3a1d`。已读其原回复，批准只覆盖所供源码，不冒称它重新执行测试或浏览器。

## r3 展示补审

视觉走查发现原四列表格在窄侧栏压缩按钮后，作者仅修改 `training.js`：当前 baseline 使用简表，完整 baseline 与摘要保留于原生 details；实验使用单列 `task-choice` 呈现 ID、原结果、baseline匹配和原件按钮。已将当前完整文件与 r2 安装源逐项比较；当前6551B、SHA256 `f754d2409ec19d002e5e076426b08d7594dc59e48969d2c212ce6da9e765ef44`。它复用现有 `ui.short`、table／details／task-choice 与换行样式；缩短显示的提交和workload仍能从完整原件取回。请求路径、序号、active检查、分页、错误处理及详情内容逻辑均未变，没有新 guard、状态或抽象，也未新增镜像展示测试。本轴源码补审无新 finding，开放仍为0。

r1实际浏览器1440／960／390三视口的整页无横向溢出成绩保留其原范围。r2 包／回归／自身模板也各自保留原候选身份；随后仅展示差异按 r3 的包与实际页面单独核验，没有无理由重跑核心33项或把它们改写成 r3 全套成绩。

## r3 最终本地证据终核

已核最终 `review-r3-files.json` 中本片9个产品／测试／CI文件与工作树摘要一致；清单附带的 H3b 和审查状态记账仍不混入本片产品判断。最终非editable wheel SHA256 `df85fd4c28d502f8d39c1138e317738ee716d090baf9114c1d41db9b538b285a`；`install-r3/package-identity.json` 与 `native-readback-r3.py/json` 共同记录563产品源码／wheel／安装逐字相同、两份RECORD及283冻结参考通过，最终 reader 在原生r1合同／job／fence上仍取得同一完整观察，18份原件未变，无新派发或执行。

已读 r3 四组浏览器原命令、exit=0 与 stdout：实际详情响应取得后切至另一项目再交付，旧详情未进入新项目；两次实际列表倒序交付，旧 sentinel 未覆盖新列表；展开 baseline 后完整40位提交和文件摘要仍在，展开实验后原job／fence／无结果及 `not_queried` 保持；1440×1000、960×800、390×844均无整页横向溢出。本轴另查看最终桌面和手机截图，原件按钮已可正常阅读，完整折叠入口可见。读取实际 HTTP 请求日志独立计数为40项GET、40个200；两次 `training.js` 响应均为6551B／`f754d2409ec19d002e5e076426b08d7594dc59e48969d2c212ce6da9e765ef44`，与最终源／安装资产一致，见 `structure-review-r1/final-r3-evidence-recheck.json`。这些证据不扩大为所有视口、辅助技术、响应交错或跨平台验收。

最终原结构模板展示复审实际23.370秒、approve，六前端文件25,122B。其 input digest 为 `a01ce102732654b2eb72a295d00f526c2766dda636229c07d57f3879117f9c31`，原 result SHA256 为 `1c34e2d73b59b4e47c1ae879e548951eb8566df2dc04d837771bf414dafe7f77`；已读原回复及实际stdin，独立核全部六份当前文件完整出现、逐份SHA匹配，并核原result和prompt字节摘要一致，见 `structure-review-r1/final-self-review-input-recheck.json`。元数据另记录完整祖先inline交付。本轴不把该静态源码批准称为模板自行重跑CSS、截图或runtime的证据。

`browser-cleanup-r3.json` 明确记录旧／新演示controller及监听均已停止、浏览器CLI已关闭、18原件保持。实际process记录为受控取消、returncode=-9；这是本地演示Web进程的停止收尾，不证明原训练作业停止或取消结果。已核[可公开验收摘要](evidence/2026-11-14-training-workbench.json)的分轮身份、数字及范围与所读原件一致；摘要保留分轮候选和原request-changes，未含原始缓存或本机绝对路径。

本轴最终本地出口通过：2条P2关闭、开放0；无额外结构／性能／冗余 finding。普通发布、本候选自己的CI和需求轴最终结论仍由所属记录单独收口，不能借H3b或其他候选成功。F9b–d、真实B3、完整C2、跨平台实际运行与完整F9均不由本报告关闭。

## 精确发布身份补核（CI待验）

本次仅使用 `git show 8182499fa46c61adecea2f6defd2c777a433eed5:PATH` 与原提交／推送／远端Ref记录核对已发布候选，没有使用其后 F9b1 工作树的产品内容。该提交父对象恰为本片基线 `47443840b68693f63ee011dc6fbe29421a42223f`；本轴独立重读23个 Git blob，文件集合、逐文件字节数及SHA256均与冻结 `static-r2.json` 完全相同。9个产品／测试／CI文件的包摘要按原算法从这些 Git blob 重算为 `842507cbc547d9f9937f4eeca9ea8c2d17c9f18464972cbab90bbd3f1ea094cf`，与本地已验候选一致。静态原件另记录217个本地链接无坏链、无列出的机器私有标识、diff检查通过；邻片H3b状态文件仍仅作记账。

`commit-r1.json`、`push-r1.json` 与 `ref-r1.json` 已核：普通推送退出0，推进开发分支 `refactor/architecture-foundations`；随后的精确 `ls-remote` 退出0，完整远端Ref为 `8182499fa46c61adecea2f6defd2c777a433eed5`。这证明该时点的精确发布身份与已审包相符，不证明远端Ref永远不变。

本轴发布身份补核通过，维持2条P2关闭、开放0。该候选自己的CI仍待验；没有原HTTP终态原件前不预判成功，不以本地出口或旧候选CI代替。F9b1及其他后续片不在本次补核范围。

## 本候选 CI 与精确发布终核

本节收口上文历史“CI待验”。已独立核 [Portability run 43500423499](https://github.com/626619403/Ergora/actions/runs/43500423499) 的原始官方 HTML `ci-run-html-r4`，状态为 Success，提交链接为完整 `8182499fa46c61adecea2f6defd2c777a433eed5`。原HTTP为200、实际213,211B，重算SHA256 `8ae430a89141444f5dd522534911400351df9231b16032e79d37562c1b63f66e` 与receipt及 `ci-parsed-r3.json` 一致。

本轴从该提交的 `.github/workflows/portability.yml` 及 Linux分组 Git blob 确定应有 plan、6个Linux分组与1个Windows job，再独立解析8份 job 原HTML，而非只接受作者parser结论。9份run／job原HTTP的官方URL、200状态、实际长度和SHA256逐份匹配；plan为158,751B，6份Linux各162,441B。最终Windows原件 `ci-job-132144516729-html-r3` 为160,022B，SHA256 `3c6ae41e754c04546e32dbed84787d63ecaa2d7b9eeed1f0e00f7843176008a0`。另核最初UI job批次原JSON的长度／摘要与8个job身份对应；早期 in_progress 只作身份来源，终态取各job后续原HTML。

全部30个必要步骤均为 success，存在完成时间及 job-completed 标记，开始不晚于完成；每个原 `data-log-url` 均精确为 `/626619403/Ergora/commit/8182499fa46c61adecea2f6defd2c777a433eed5/checks/JOB_ID/logs/STEP_NUMBER`。逐步名称、时间和日志路径与解析摘要一致；其中Windows另包含 PowerShell 5.1安装／升级步骤。

|job|原job ID|必要步骤|最后必要步骤完成时间（UTC）|
|---|---|---|---|
|plan|132144429432|1|2026-11-13 20:19:09|
|Linux group 0|132144516728|4|2026-11-13 20:22:52|
|Linux group 1|132144516627|4|2026-11-13 20:24:33|
|Linux group 2|132144516649|4|2026-11-13 20:23:04|
|Linux group 3|132144517006|4|2026-11-13 20:21:37|
|Linux group 4|132144517189|4|2026-11-13 20:23:11|
|Linux group 5|132144516667|4|2026-11-13 20:23:35|
|Windows all|132144516729|5|2026-11-13 20:35:45|

终核再次从候选 Git blob 重算9文件产品包摘要 `842507cbc547d9f9937f4eeca9ea8c2d17c9f18464972cbab90bbd3f1ea094cf`，并核原普通推送与完整远端Ref回执，均绑定同一完整候选。当前HEAD亦为该提交；未用F9b1未提交产品替换证据。本次只读原件与Git对象，没有重跑测试、模型或服务，也没有下载／核验artifact压缩包内容。

本轴 F9a 精确发布及自己的CI终核通过，2条P2关闭、开放0。此结论不代表需求轴也已补核CI；其状态由原需求报告独立登记。F9b–d、真实B3、完整C2及未验的执行／GPU／采用范围保持开放。
