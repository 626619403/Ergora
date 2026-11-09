# AC4.2b：可信建议审查运行

日期：2026-11-09。基线 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3`。状态：R3包191项/四实际旅程通过，模型复审确认ADV-1修复并提出单成员all-join准入遗漏ADV-2；原R3包两红/一绿已复现，最小版本限定修复及三项源码回归通过，R4包/真实旅程/旧重放及275.01秒自身模板approve已完成，同片独立最终Spec/Standards通过，普通交付/精确CI和远端待核。原候选身份不替代修后候选。[AC4.2a](2026-11-09-review-requirements.md) 已精确交付，其自己的 CI/远端终结单独保留。

## 本片合同

沿用 WorkflowDefinition v2 的实例职责，正式冻结为独立 v3 admission、专用 worker 队列/请求根及活动名，仍进入原六阶段。v1 与已有 v2 的正式输入、单叶/并行行为和历史保持；此前静态可读但未获执行支持的 v2 封装不能因新代码而隐式降级。新选择把所有叶子的职责显式封入成员；旧 v1 子模板中的审查者在新选择里仍为 required。至少一名必需审查者，所有分支必须完成并覆盖显式 all-join，均核同一候选、独立会话、完整祖先材料与原 verify/plan。

可信执行器从经过 schema 核验的结构化模型结果产生版本化 `formal-review-decision` 产物，绑定原 job/context、候选及实际调用结果摘要。仅在原受监控调用成功并完成只读检查后发布；业务 `request-changes` 仍保留 FAILED 原收据和 fail 检查，不改写为成功，也不通过错误字符串识别意见。运行失败缺少合格的意见原件，仍走原阻塞与 fence。

v3 专用 poll 由原 FileAdapter 核全部收据/产物字节，再核 actor/角色、候选、必需产物、检查、原始调用结果及独立会话。只在这条可信链上把合格意见与原收据一起交给 v3 workflow；不把原 v1 的 failed 短路当作可信建议。建议 request-changes 可在原收据保留的同时继续；必需 request-changes、运行/合同失败、缺失、超时、会话复用、取消和清理未知继续停止并沿原 stop/fence/reconcile，不清空全局取消。

调度仍由原 review 内的共享祖先限额和稳定 `review:<实例路径>` 作业拥有。可信聚合使用新版本，逐成员引用原 stage/job/receipt 与职责/意见；必需全部批准才能到 REVIEW_READY。建议原 finding 完整保留，不冒充单一模型/人的 approve，不新增调度器、执行账本或自动合并。

## 所有者与验收

原 `tasks`、`task_envelopes`、`reference_inputs` 拥有创建/版本/形状与调用者选择；原 `reference_workflows` 增加 v3 活动及工作流，复用已有并行作用域和六阶段；原 `reference_executor` 只接可信模型意见，monitor、回执及账本保持；在线证据与离线 handoff 沿原引用规则识别新聚合。

先验版本隔离/静态冻结/至少一必需、建议拒绝继续、必需/运行失败阻塞、篡改/候选/会话拒绝、并发/超时/取消，以及旧历史保持。最终非 editable 包核源/wheel/安装与283冻结；真实公开 CLI/Temporal/原 executor 跑建议拒绝仍就绪、必需拒绝和运行失败/取消，核原 history/replay/证据/handoff与进程清理。确定性模型协议只证明运行合同；另用 Ergora 自身结构模板实际审查，并起 fresh-context 独立者核结构/性能/冗余。

完整实现、每次实际验证、原失败/限制、自身模板、独立审查与普通交付分别记账；不在上一片 CI 终结前推送下一生产候选。串行端口/写执行者、三领域默认组合、页面与完整 AC6 继续按 [AC 计划](../plans/2026-11-08-agent-composition.md) 推进。

## 当前实现与原始结果

已在原所有者增加 v3 选择、专用队列/活动/adapter 及工作流；旧 v2 仍校验精确版本。并行限额/会话汇合复用原实现，v3 仅替换叶子可信意见判定与聚合版本。执行器保留 request-changes 的 FAILED 原收据，同时从已验证模型结果的同一份原始字节计算结果摘要并发布结构化意见；原受监控只读检查、账本、取消和副作用恢复继续复用。新活动按原产物摘要再次核读取到的意见字节，避免初始收据核验和后续读取之间的变动。

首轮旧 v2 runtime/workers/parallel 定向检查 **35 passed /57.68 秒**。新行为首轮 **6 failed /17 passed /36.51 秒**：合法意见 fixture 只提供 review-report，漏掉冻结 profile 必需的 handoff，生产按原产物合同正确拒绝；没有削弱生产检查。fixture 改为从 profile 构造完整必需产物，并让各负例匹配其目标错误，避免用错误的拒绝理由冒充通过。修后结果另记，不把原17项写成完整门禁通过。

修正 fixture 后首轮 **23 passed /36.23 秒**；恢复后再用源码执行 advisory/composition tasks 两组 **69 passed /133.82 秒**。新增两例直接消费原受监控执行器的单叶v3批准/请求修改及恢复，连同可信poll/工作流检查 **24 passed /57.96 秒**。这些核验从实际原模型协议产生意见，分别保持 SUCCEEDED/FAILED 原回执、完整候选/原调用摘要和重复执行字节；模型为确定性协议，不宣称实际模型质量。一次误选旧开发venv导致collection ImportError，改为明确源码路径和已安装依赖的环境后完成上述检查，没有据此改生产导入或跳过测试。

R2非editable wheel构建/安装成功，SHA `06aeb3d4f69ae1516cbae1fbc2671018384feffbe9e6b9a79ae7de9e0f9840c3`，**370源/wheel/安装文件相同、283冻结保持**。本地证据在`.ergora/checks/ac4-advisory/r2/`。最初试图把reference锁与应用web extra在一个解析步骤安装，因uvicorn版本不同明确失败；随后按独立原生环境安装reference锁和非web的dev/temporal/task-mcp extras成功，未改冻结依赖或放宽其锁。包上八组相关回归与实际公开CLI/Supervisor/Temporal四任务旅程在途；尚不把正在执行或只读协议测试计为最终旅程通过。

## R2包与实际旅程（ADV-1修复前）

[最终包记录](evidence/2026-11-09-ac4-advisory-package.json)的八组回归 **188 passed /0 skipped /418.31秒**，包含原v2并行/任务/worker/executor、v3可信poll/流程/实际Executor、在线/离线交接与架构检查。首个包命令误用不存在的测试文件名，原no-tests日志保留；正确套件实际执行后才登记通过，没有增CI作业或改冻结文件。

[真实公开CLI/Supervisor/Temporal/scanner四任务](evidence/2026-11-09-ac4-advisory-journey.json)全部完成。首段原建议任务已经到达REVIEW_READY，验收脚本却把终态outcome当作live-query status读取，产生KeyError；生产没有失败。finally按原配置关栈，观察5个原PID/starttime无存活。继续探针从相同已创建四任务及首条原run恢复，保留原输入、job、回执与history，没有更换候选或重建首条任务；继续段 **334.09秒**，该数不包含首段运行时间。

- 建议拒绝：原建议收据FAILED/independent-review fail，必需收据SUCCEEDED，聚合v2分别保留职责、意见和完整原引用，任务REVIEW_READY。两条分支活动时停worker，原executor完成原七个job；重启后沿原history汇合，只存在原两次Agent调用及相同请求。
- 必需拒绝：原必需及建议收据均FAILED，任务BLOCKED，无审查通过汇合；未用建议职责掩盖必需意见。
- 建议进程错误：原建议收据FAILED且没有可信意见产物，任务BLOCKED；原已成功必需收据保持，不把进程错误当建议finding。
- 活动建议取消：公开cancel后原建议收据CANCELLED，任务原outcome为CANCEL_UNCONFIRMED；外部原件确认无未决/意外job后，等待10.3秒核无迟写，再显式reconcile释放原claim，原outcome保持。

四run各七个原job、两独立审查会话；原候选、完整信封v3、专用队列及全部收据引用核验通过。四份完整history为172/178/178/170事件，各自重放通过；四份交接包离线verify通过，公开证据保留原run/history/packet身份。最终正常shutdown后7233/8233/8765端口关闭，观察88个原PID/starttime及递归后代均无存活；这是采样范围，未声称捕获全部短命进程。继续轮观察脚本误用首轮JSON输出名，首轮逐PID JSON被覆盖，5/0的原stdout仍在；公开记录明确首段证据限制，继续轮88项完整JSON另行固定保留，没有重建丢失原件。

当前安装包另外只读[重放五份旧完整history](evidence/2026-11-09-ac4-advisory-legacy-replay.json)：原v1、单叶v2、并行v2成功/拒绝/取消全部通过，未修改其输入、队列、原事件或服务状态。

## 自身模板与独立审查

实际先用本版Ergora的structure-review/task-mcp调用Claude Code；认证探针loggedIn=true/api_key，但模型请求返回上游400：`system content must contain at least one block`。原run `ac351859455d4ebb9443572929cd9dea` **12.875秒 /failed /CLI exit1**，[原尝试记录](evidence/2026-11-09-ac4-advisory-claude-attempt.json)保留，不能写成双后端审查成功，也不能把loggedIn当作推理就绪。按用户已有授权继续Codex实际调用；结果在途。该Claude兼容性问题将以独立切片调查，不在当前候选偷偷改变后端合同。

新的fresh-context评审者已在原始要求/全部变更/相邻所有者上完成Spec与Standards源码初审，无已证实阻塞finding；另自行验证建议超时StopWork、poll同时取消仍保留cancel并CANCEL_UNCONFIRMED、历史v2新图可读但执行拒绝，以及v3活动接v2在发布前拒绝。独立重核370/283身份与wheel一致。完整包、四旅程、旧重放、自身模型原件及最终完整scope仍交同片评审者终核，不把初审当整个交付通过。

## ADV-1：实际自审发现、独立复现与修复

Codex `gpt-6.1-sol`/high 的真实structure-review/task-mcp run `40a6377d44b6444cb7aa9ec01edc72fa` **240.51秒 /succeeded /CLI exit0 /request-changes**。[原模型意见](evidence/2026-11-09-ac4-advisory-self-review-r2-result.json)与[13份源码/260,215字节附件身份](evidence/2026-11-09-ac4-advisory-self-review-r2-identity.json)保持，不能把调用成功当业务批准。它发现poll只比较decision与invocation中的`result_sha256`是否相等，两者同为null可通过。FileAdapter只核外层产物字节，不能替代内层摘要合同。独立者用原必需approve/建议request-changes回执各构造7种非法相同摘要，14例均被R2接受，确认ADV-1为成立的Spec阻塞；原源码初审只代表当时已检查范围。

修复在原可信意见活动中要求结果摘要为严格64位小写hex，然后再和原调用摘要比较，不增加新的验证框架。新增同null/非hex两反例，用旧R2安装包实际执行 **2 failed /4.42秒**，证明原缺陷；修后拒绝且不修改原回执。另补一个真正v3写入攻击回归：测试专用CLI wrapper向原checkout写内容，原process monitor检测只读快照变化，原Executor返回FAILED且没有可信意见产物。最初测试尝试从自定义env传目标，生产monitor正确过滤它而使测试攻击没发生；该次 **1 failed /26 passed /70.27秒**保留，没有为测试放开生产env allowlist。改为测试wrapper显式传目标后，摘要两反例与实际写入共 **3 passed /14.66秒**。

模型指出首轮附件未含原Executor/Sandbox/process_job，因此只读后置条件只能列证据缺口、不是确认缺陷。R3复审将补完整原所有者、stage fixture、继承编译及worker启动者，测试wrapper和项目grant一起提高材料预算以完整交付，不截断或偷偷扩权限。R3已独立构建/安装，370/283身份、修正后全部相关测试、四实际任务旅程、历史重放及自身复审继续分别记录。

## R3修正后候选

[最终安装包](evidence/2026-11-09-ac4-advisory-package-r3.json) SHA `6b5fd966339397f6c31b05e7d034a0fb6c9fa02ac9475ab9974c81e12e3a837e`，370源/wheel/安装文件一致、283冻结保持；相对R2包只改变原`reference_workflows.py`的内层摘要检查。八组最终回归 **191 passed /0 skipped /424.17秒**，包含新非法摘要拒绝及实际只读攻击。不把两轮耗时差当作性能回归或加速基准。

[R3四条新公开旅程](evidence/2026-11-09-ac4-advisory-journey-r3.json) **429.31秒通过**：原建议FAILED而REVIEW_READY、必需拒绝BLOCKED、建议进程错误BLOCKED、活动取消CANCEL_UNCONFIRMED后原ID对账全部符合合同；首条包含worker停启、原七请求及两调用保持。四份完整新history为172/178/178/170事件并重放通过，四新交接包离线verify通过。实际正常shutdown后三端口关闭，完整观察127原PID/starttime均无存活；此轮没有重用首段证据文件名。[五份旧history的R3重放](evidence/2026-11-09-ac4-advisory-legacy-replay-r3.json)也通过。

新独立者用修后R3安装包复现原14个共同非法摘要，全部永久ContractViolation，原回执字节未变。实际模板复审已启动，附加ADV-1说明在`prepare_input_from_manifest`前形成冻结task，原所有者及最终包/旅程证据一起交付；未以脚本中出现但未进入prompt的字符串冒称实际输入。模型原结果及独立最终Scope/证据终核仍待，不提前登记交付。


## ADV-2：单成员版本化汇合合同

R3真实Codex structure-review/task-mcp run `e0cd50a100a841399e6eb3ec7a212f69` **206.15秒 /succeeded /CLI exit0 /request-changes**。完整[原意见](evidence/2026-11-09-ac4-advisory-self-review-r3-result.json)与[输入/19源码身份](evidence/2026-11-09-ac4-advisory-self-review-r3-identity.json)保留；附件335,664字节，模型确认ADV-1修复，但指出`review_members`在单成员时提前返回，让新graph v2/formal v3的输出直转根task或直接叶子result也获运行支持，违反本片显式all-join合同。单审查者仍会执行；没有证据表明它绕过了审查调用或候选门禁。

用原R3非editable安装包运行三种合法静态图的公开创建/读取/运行支持回归，**2 failed /1 passed /5.78秒**：task-forward与review-result误报可运行，显式all-join正常。最小修复只将单成员快捷路径限制为旧graph v1；新图走已有汇合与完整覆盖验证，旧v1/v2单叶合同不变。三参数回归 **3 passed /6.46秒**，保留无汇合图的静态存储/历史读取并在正式准入拒绝。原Executor三用例的v3 fixture补上真实all-join以符合新合同，没有改公共旧单叶模板、生产权限或调度。

修后R4重新构建并安装，完整相关包回归、四条新公开服务旅程、新旧history、真实模板复审及同片独立者复核分别记录；R3的191项与四原run仍只属于其原包，不继承给R4。两轮自身模板连续找到边界缺口，继续将调用成功和业务批准分别记账，不以一次初审通过结束修复。


## R4安装包与最终运行证据

[修后安装包](evidence/2026-11-09-ac4-advisory-package-r4.json) SHA `d16f835e18e564719d4e884ed8c64b28bbdd1196a8bf67c7d8da3adf3902cbee`，**370源/wheel/安装身份相同、283冻结保持**。相对R3包仅`task_envelopes.py`的单成员版本限制不同。独立者以R4安装包复核14个共同非法摘要全部拒绝、六种新旧单成员形状保持预期。

八组包回归初轮 **192 passed /2 failed /0 skipped /434.51秒**，原两个失败trace完整保留：原approve/reject已生成正确意见及原收据，测试辅助函数仍用`instances[-1]`取Agent，新增末尾gather后出现`KeyError: resources`。修正辅助函数按原`call.member`选择精确叶子，只重跑受影响的v3批准/拒绝/写入攻击及旧单叶恢复消费者，**4 passed /45.14秒**。生产包没有变化；没有把两轮合成“194项一次性全绿”，也没有借fixture失败放开生产合同或无故重复无关测试。

[R4四条全新公开CLI/Supervisor/Temporal/scanner旅程](evidence/2026-11-09-ac4-advisory-journey-r4.json) **429.34秒通过**：建议原FAILED仍REVIEW_READY、必需拒绝与进程错误各BLOCKED、活动取消CANCEL_UNCONFIRMED后用原ID对账；首条worker停启保持原七请求和原两次调用。四完整新history为172/178/178/170事件，全部重放；四交接包离线verify通过。正常shutdown后三端口关闭，129原PID/starttime采样零存活，采样限制保留。[五份旧v1/单叶v2/并行v2 history](evidence/2026-11-09-ac4-advisory-legacy-replay-r4.json)在R4安装包再重放通过。

最终自身结构模板复审已冻结完整源码、相邻原所有者、两finding说明及原初轮/修正检查日志并实际启动；实际模型结果与同片独立最终Scope/证据终核仍待。普通提交/必要CI/精确远端也单独待核，未引用R2/R3或上一片的成功替代。


## R4自身模板复审

最终Codex `gpt-6.1-sol`/high structure-review/task-mcp run `a9b3ff606e99415b8c79ad0d307156e9` **275.01秒 /succeeded /CLI exit0 /approve**；[原模型结果](evidence/2026-11-09-ac4-advisory-self-review-r4-result.json)和[19份源码/输入身份](evidence/2026-11-09-ac4-advisory-self-review-r4-identity.json)保持原字节。候选附件340,847字节，SHA `57fb28a55ba8158173a1dd01310b1d53b092526a4aa9494142dcb6d3f9edf218`；两finding及分段检查说明在prepare前冻结。模型逐页完整读取后确认ADV-1/ADV-2修复、无新增Spec/Standards finding。

模型没有执行测试，明确分辨原192通过/两fixture失败与后续四项纠正通过，也没有声称公共CI、远端、模型质量、模型错误独立、宿主隔离或完整活动进程崩溃恢复。实际原MCP分页与输入/结果身份再交同片独立者核验；它的本地证据终核与后续精确Git/CI门禁分别登记。


## 本地门禁与交付候选

同片[新独立评审](2026-11-09-advisory-runtime-review.md)最终 **Spec、Standards均通过**，ADV-1/ADV-2关闭，无开放finding。独立核实际14连续MCP页至null、19完整源码与四份祖先材料、原task中的两finding和分段检查，最终35文件（5生产、4测试/fixture、10 Markdown、16公开JSON）全部覆盖。静态10 Markdown/249链接与锚点/79 CLI parser通过，源与包身份保持；不另增调度器、账本、依赖或CI作业。普通提交/本提交必要CI与即时明确HTTPS远端另记；下一片只读串行端口合同依赖本片，不冒称已执行。


## 精确提交与远端终结

本片已普通提交推送 `91b09683aac9481d07a6cd1d2ea8da9777b25563`（35文件，唯一父5580c8c）。自己的[CI42574624398](https://github.com/626619403/Ergora/actions/runs/42574624398)双OS七必要步骤全部成功；独立在06:56:49.467683 UTC完成精确提交/两job/全部必要步骤原日志URL检查后，同进程立即于06:56:49.467698 UTC开始明确HTTPS ls-remote，06:56:50.878067 UTC exit0并返回同完整SHA。Git对象370包/19模型源码/283冻结身份均由独立者逐份核过。原R2/R3拒绝与R4原fixture失败保留，本片精确交付终结；后片端口合同另记，不以本CI证明新运行能力。
