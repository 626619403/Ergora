# F7b.1-B1c 独立审查

评审者：`f7bc_selected_admission_review`；本片独立 fresh-context，未继承实现对话。按项目 `AGENTS.md`、maintainable-project-delivery 及其 independent-review brief 审查。初轮固定基线及当时 HEAD 均为 `4638c3b9524adcba584a9313b8fd1588b5dde64d`，审查对象为完整未提交工作树；后续精确提交、自己的CI失败及同片夹具修正分别在末节记录。检查完整基线差异和本片未跟踪文件，不以 HEAD 代替候选身份。只读源码／原件及本报告写入，没有安装、模型调用、产品修改、提交或推送。

## 范围与身份

最终候选为基线以来完整18文件（含本报告）：3个产品文件 `src/ergora/{agent_backends,reference_inputs,reference_task_submission}.py`；2个测试文件 `tests/fixtures/task_submission_client.py` 和新增 `tests/test_issue_submission.py`；10份Markdown为 `docs/{PLAN,USAGE}.md`、`docs/architecture/{current,contracts-and-identities}.md`、两片的 `docs/plans/2026-11-11-{issue-dispatch,source-task-admission}.md`、两片的交付／review共4份；3份JSON为 `docs/delivery/evidence/2026-11-11-{issue-source-dependencies,source-task-admission-acceptance,source-task-admission-self-review}.json`。完整tracked差异及所有本片untracked已审，没有只审产品hunk或忽略新增投影。另读原 submission／creation／executor／stage_driver／AgentBackend／进程／MCP／输入编译与冻结所有者、原生 doctor／task_action／sandbox／ingress／transport 邻接路径及现有回归。

两份本片公开投影已与原件核对，包含r2／r3失败与原ID收尾、r4正向及export的全部实际call字段和审计SHA；正向export投影省略含私有actor的完整original_outcome，并从实际export回执加入lease_released，不改原件。B1b的4份交付／计划／报告／投影后补明确来自同片原评审的4638c3b自己的CI终核，只核本次记账差异与来源边界，没有当成本片CI或本片实现判词。未来 F7c 的 `docs/research/2026-11-11-issue-writeback.md` 明确排除于本片实现／验收范围。

只读重算最终产品 r2 wheel SHA256 `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`：445 个源码／wheel／安装包文件逐字相等，wheel 450 行及安装 455 行 RECORD 均核，283 个冻结发行文件身份保持。r1→r2相同路径下仅 `reference_inputs.py` 增加 `import json` 及相应 RECORD；没有把 r1 自动认作 r2。夹具后续仅复用 `core.task_spec` 恢复原 slug 校验，SHA256 `91dbc55f2f555d976caf610c91a2b9bf407603dde825c52ed41d4779573d780c` 已与定向结果核对。

## Spec

本片完整18文件和C1–C4已完成的本地原件范围内通过，开放finding 0；所选准入、原恢复、最终r2正向六阶段与自身真实模板审查均已独立终核。本地出口通过；精确提交／远端Ref和本片自己的必要CI另核，没有提前称整片精确交付完成。

- v1–v6 继承默认 `WorkflowInput.admission_report`，调用保存的原 doctor；只有 v7 的实现按冻结 profile／creation selection 取 inventory／plan、按完整 composition 取工作／审查叶。未选默认后端不进入检查，MCP SDK 仅在所选 MCP 模式下检查。
- 后端校验、模式、当前 policy 和配置 executable 的解析复用原 AgentBackend；Codex availability 和 command 共用 `executable()`。Git／timeout／原 Python、执行启用与原 Sandbox 信任／容器身份门禁保留。报告明确只证明本地程序／配置，不证明认证、配额、worker、模型质量或进程间 OS 隔离。
- `_Submission.dispatch` 仍在原专用子进程中调用原 `cli.task_action`，只作用域替换报告并在 finally 恢复；policy、可信 checks、Temporal connect、原共享 claim、lookup-before-start、attempt-before-send 和 memo 没有另建所有者。unknown 仍进入原 lookup／memo 核验，不调用新增准入，也不再发送。未发现 tracker/token 重读或候选／批准／旧身份改写。

## Standards

初轮完整18文件本地范围通过，ST1文档finding已修复并复核关闭，产品开放finding 0。随后首个提交自己的CI实证暴露ST2/P2测试环境依赖并重新开放1项；同片最小夹具修正及原13项干净PATH结果已在末节独立复核，ST2现已关闭，当前修正候选本地开放0项。首个提交的失败保持，新提交自己的CI仍待；不把原本地25项成功改写成CI成功。Input 的版本差异留在既有版本族及共同 Interface；新方法的实际调用者是原 submission 所有者，属于必要的版本合同，没有为单一调用增加新包装模块或第二套调度／账本。native／SDK 导入仍在执行方法内，纯输入／journal 的标准库依赖方向保持。

新增判断分别保护当前本地执行许可、外部配置／程序、所选模式／policy 与 SDK 存在性；没有发现无可达触发的断言或跨层重复授权。13 项新增回归穿过同一公开任务入口，保护新增 report 替换可能静默绕过的前置失败顺序、原 policy／claim 和 unknown input／memo 恢复；旧 v1 回归不能单独证明这些 v7 行为，未建议删掉必要覆盖。没有新增 CI 路径、测试框架或配置默认值限制。

**ST1／P2，已关闭。** `docs/USAGE.md:217` 原来在新“按冻结选择准入”段后仍称 v7 start 必须走完整广域 doctor／窄入口待后续验收；`docs/architecture/current.md:93` 也仍称“start目前仍原广doctor”。用户按这些相邻说明操作，会把无关完整栈当成 v7 依赖或误以为能力未实现。最小修正为更新这两处旧状态，保留 worker 升级、真实消费证据、材料预算和旧版本语义。已逐字复核当前两处，冲突消除；没有要求产品变化或新测试。

## 原始证据核验

原件根为本片忽略目录 `.ergora/checks/f7-source-admission/`；下述结果均检查原 stdout／文件字节，未只相信汇总 JSON。

|证据|独立核验结果及边界|
|---|---|
|r1 九 suite|实际 **8 failed／158 passed／6 skipped，779.37 秒**；七个缺 json 的失败和一个新增夹具早于 slug 读取路径的失败均保持。不是全通过，也不是全套 r2。|
|r2 C1／C2|架构＋来源 submission **25 passed／79.53 秒**，raw stdout SHA 与记录相符；七种所选失败均在 attempt／connect／claim 前拒绝，原 policy／共享 claim 与 unknown input／memo 冲突被覆盖。Sandbox 的 SDK 夹具 probe 受控，不能由此证明实际容器。reference verify 原输出通过。|
|r2 新夹具|复用既有 `test_creation_identity_registration_and_legacy_boundaries`，**1 passed／57.70 秒**，driver 64.50 秒；fixture／stdout SHA 与记录一致。没有为测试 shim 另加测试，也没有拼接成全套 r2 结果。|
|r1 确定性六阶段|原历史输入及 memo 等于冻结输入／intent；原 plan receipt canonical SHA 和批准一致，9 个原 receipt 及其每件 artifact SHA 相符，REVIEW_READY、重复 start 原回执及 handoff 原 outcome 一致。236 事件 history SHA、61 个 handoff blob 和 index 字节摘要独立重算通过；replay 的实际调用／成功记录已核，没有重新运行 workflow。|
|r1 完整祖先／来源交付|逐叶核原 manifest→job manifest／input→run input 副本→实际 protocol prompt＝stdin；从每个祖先定义重建声明资源及父权限上界，核定义／Skill 目录 digest。5 叶合计23次资源交付、7,437字节，与 scope、fixture 回执完整 content_base64、连续 offset／长度及 native successful read／close 一致；12,398字节声明依赖产物与原 artifact 字节一致。每叶 materials／prompt 完整 issue_source 等于冻结 payload。只证明确定性进程实际读到字节，不证明模型理解或多页压力。|
|r1 生命周期／性能|原70个 PID＋starttime 采样记录无存活，独立重查这些原进程也无存活；旧 v6 2,356 文件前后清单相等。原驱动检查端口关闭；本次没有以其他旅程正在占用的公共端口推翻历史清理。旅程157.60秒、wrapper171.12秒、start命令2.50秒，仅为原配置耗时，没有准入提速、吞吐或模型性能归因。|
|r2 首轮真实工作叶失败|原 run `01a1ca03-4d6c-7469-9b94-f1517ee9c2de` 为 BLOCKED。两个真实 Codex writer invocation 成功，但 boundary-test 可信 check 虽 unittest 3项OK，生成 pyc，原只读 checkout 变化门禁返回126，原 FAILED／fence 保持。已读原 execution.log／terminal／checkout未跟踪文件；没有将 invocation 成功当成阶段／全流程成功。wrapper183.99秒。|
|r2 两个真实工作叶实际读取|独立从两份原 Codex JSONL 重建 manifest／input／prompt＝stdin／source／scope／原 result，祖先声明、权限上界和定义／Skill digest 相符；8次资源交付共2,671字节，连续 UTF-8 页至 next_offset null，scope原字节均相等。两份原结果均包含完整来源标记 `boundary-alpha-73 中文完整来源。`。boundary 先有1次 `list(path="context")` 失败，随后完整成功读取；失败记录保留，没有宣称零失败或模型理解。|
|r3 第二轮真实叶拒绝|原 run `01a1ca08-99be-7528-811f-e98260ebb3f3` 为 CANCEL_UNCONFIRMED，候选 `cedd5be9142cbd1665217fe1aa8140177a5791dc`。两工作叶、integrate／verify 成功；structure invocation 成功产出 request-changes，阶段 receipt 为 FAILED；另两 reviewer 为 CANCELLED，没有 result／decision／turn usage。原 acceptance 要求链接 architecture owner，原 map 明示 owner 未确认，不能从 plan approver 推断；该拒绝依据成立，没有作为本片产品 finding。wrapper289.36秒，失败／fence原样保留。|
|r3 五叶实际完整读取|独立重建全部5叶祖先声明、权限上界、定义／Skill digest及 manifest→input→实际 prompt＝stdin→JSONL scope 字节，共23文件／7,437字节，所有连续 UTF-8页至 null。两工作叶＋structure 的3份原 result 摘要相符且回显原来源标记；knowledge-map 的1次 context list及1次 context read失败保持。两取消 invocation 缺 native 字段，原生 JSONL确已读全5资源各自到 null；另核其原 `*.mcp-native.jsonl` scope摘要、各5次 successful read、closed及原PID消失；没有据此补成成功审查。|
|r2／r3 原ID收尾|只读核原216／386事件 history SHA、开始 input／submission memo、精确 plan receipt批准 signal、每件原 job／receipt／artifact、handoff index及32／55个blob，原 outcome 与 status-before／after／reconcile／handoff相等。原 closure driver确 await原Replayer后才保存history与passed，没有重跑工作叶。SQLite只读核两轮 active均空，原claim的released_at及evidence与精确对账相符；原outcome仍分别BLOCKED／CANCEL_UNCONFIRMED。原44／81采样及closure各2个PID＋starttime复查无存活，旧v6共2,356文件清单前后相等；closure各15.30／16.62秒。|
|r4 最终r2正向六阶段|新task `source-repository-governance-task-r4`／run `01a1ca12-9887-7dcb-a7e9-473466c5a600` 为REVIEW_READY，9原job全SUCCEEDED、9个独立actor session；两真实Codex工作叶、三个真实Codex审查上下文均完成且三review approve。inventory／plan仍为协议夹具。原精确plan receipt批准SHA `2ea36f2461e516437fbf96cac866ada059710bbbf07e5c4d36c8cbb509d85f59`，候选 `51410f67017b9bac5083bb7d9386bafb6ea31f52`，原input／memo／approve signal／全部receipt及66件artifact entry均匹配。386事件history SHA `876cebdf4fe8b368c21e256303e6d82a3395ae56fdf250a2d41f62e0e569f55f`，实际Replayer成功后才保存原history；66个handoff blob共646,862字节及index独立核通过，packet SHA `f162f2afea1b0bfcbb6fc83ce17513796ed344845543c13c0a797fc0f5e433d4`。|
|r4 五模型完整资料／实际产物|逐叶独立重建完整祖先定义／Skill digest、父权限上界及manifest→prepared／actual input→prompt＝stdin→原Codex JSONL／scope／result，全23资源／7,437字节连续UTF8至null、17,507字节声明产物与原artifact相等；5原result SHA均核且回显来源中英marker。4次无效context／issue_source／task MCP查找失败原样保留，后续读全授权资源；不称零失败、理解或不同后端独立性。已逐字读候选map、AST测试、operator提供的OWNERS；仅2路径新增、4项保护文件与base／工作树逐字相等，原可信execution.log／test-results／check-results确有4项stdlib unittest通过与候选绑定的5项checks pass，没有另跑测试。|
|r4 原ID导出／生命周期|仅Temporal收尾的export与repeat-export回执逐字相同、lease_released true；本地 `agent/source-repository-governance-task-r4` 精确指向候选，原HEAD仍base `224921083cfa2d83950e275f59a4b9af94ad6ebd`、工作树clean，没有checkout／merge／远端推送。SQLite只读核active空、精确原claim已释放，evidence_digest等于原完整outcome canonical SHA。status-before／after、原outcome、386事件history及handoff在原旅程／export两次收集逐字相同。原87个PID＋starttime和export2采样复查均无存活；2,356旧v6文件前后清单相等，另独立重读当前原目录全部2,356文件也与原清单相等。旅程296.78秒、wrapper309.87秒、export18.13秒，仅为原配置实际耗时。|
|Ergora 自身真实模板审查|原 run `d8db8ed0df1242feb30e5dc3c7c362c2` 为 Codex／gpt-6.1-sol／high，144.5749秒，原 decision approve。独立核 manifest→prepared→实际 snapshot／input／prompt＝stdin／admission／scope／native MCP／原 result 字节；12个冻结附件123,194字节，candidate附件6个连续 UTF-8页至 null，其余4个 scope文件各1页，5文件总124,712字节，0次失败。原 result SHA `ddedc27d862b9a4e9d3315fc3c082be7c7c6c1546e14852c70b9d4883f305724`；4个原采样进程及MCP原PID均无存活。公开投影与原件／判词一致，没有私有路径或秘密值。|

r2 首轮验收驱动使用 `-I`，仅靠环境变量不能禁止子 unittest 写 pyc；独立新环境的下一轮只在验收检查命令补 `-B`，没有放宽产品门禁或修改产品 r2。原驱动 SHA 仍匹配保存的 command 记录，失败没有覆盖。

自身模板审查只覆盖其12个冻结附件：代码／测试附件仍与本片当前字节一致，交付文档已有后续证据更新；后来的公共文档／运行结果没有继承其 approve。原模板只在审查 clone 中增加证据 Skill／资源、显式 revision及600,000字节资源预算，正式运行预算不变。真实MCP进程由清理终止，审计没有 graceful closed 事件；完整原始读取及进程清理均已核，不要求不存在的关闭事件。原 turn usage 为 input245,874、cached201,472、output3,596、reasoning2,297，保留原计数，不重复加缓存／reasoning或据此推断计费；同后端回退不作为不同后端独立性或业务批准。

## 本地出口与后续精确交付

r3→r4验收driver差异已独立核：只增加operator明确提供的fixture owner及保护、新home／task、来源与工作指令的owner链接；原criteria／预算／reviewer／checks及产品r2不改。直接读取r2安装metadata核无a2a-sdk／MLflow／LangGraph，实际config无A2A，原Supervisor只显式启动Temporal／worker／executor。完整来源的字节交付、原生读取和特定示例成功已证明；availability没有被扩张为认证、配额、worker readiness、OS隔离、通用模型质量或全部角色真实推理。

最终5个变更源码／测试与自身冻结附件仍相等；10份源码／测试冻结附件（含未变原所有者）全部保持。完整18文件静态复核：5个Python AST、3份JSON可解析；10份Markdown共138个本地链接目标存在；检查7个已载入秘密值和私有home路径，命中0；`git diff --check`通过。PLAN／本片计划／交付的最后纯记账delta已复核，当前正向结果、ST1关闭及精确交付待验范围一致。没有新增CI或为了文档／夹具shim另造测试，也没有无测量的准入提速／吞吐结论。

Spec／Standards本地出口通过，开放0／0；ST1/P2已关闭。普通提交／推送、精确远端Ref和本片自己的双OS必要CI尚待同片后续终核，没有继承B1b CI或将其判词扩展到本片。F7c及整个项目未由本报告关闭。

## 提交6a7e9a1的精确身份与远端Ref

普通提交 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7` 的直接父提交为固定基线 `4638c3b9524adcba584a9313b8fd1588b5dde64d`。独立读取该提交的Git tree／blob，18个变更路径恰好等于ready-r1清单，原manifest SHA256 `f55c5acdf9641f0f2ac7e2902eae65c05b0dab1e98b73b7df66653f7de0bb3f4`；逐件核原字节、大小、SHA256、Git blob对象和 `100644` 模式，与ready保存文件全部相等。提交内本报告blob保持冻结SHA `a13cc694c8ec43f58ee2515058a820d771f438bb16c149af8ec05db8d6a41011`；本节属于提交后同片交付复核追加，不冒称已在该blob内。

以精确提交blob直接比对r2 wheel／installed，445个包文件逐字相同；450行wheel／455行installed RECORD所有非空摘要和大小独立重算通过，283个冻结参考文件在提交／wheel／安装一致，并逐件与基线保持。wheel SHA仍为 `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`。没有以随后live工作树代替已提交候选，也没有重复行为或模型运行。

作者普通 `git push origin HEAD:refs/heads/refactor/architecture-foundations` 的原receipt及stdout／stderr已核，退出0；随后作者Ref与同完整SHA一致。得到推送完成通知后，评审者只做一次现有origin的只读 `git ls-remote --refs`，退出0，原输出为完整 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7` 和 `refs/heads/refactor/architecture-foundations`。没有更改认证、重试网络或执行推送。

本片精确Git／ready／包／冻结身份及独立远端Ref通过；`6a7e9a1`自己的双OS必要CI仍待新原件终核，不借 `4638c3b` 的CI或本地检查提前关闭精确交付。

## 自己的CI43003408859失败与ST2/P2

固定提交 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7` 的Portability [run43003408859](https://github.com/626619403/Ergora/actions/runs/43003408859)，第三官方HTML样本在2026-11-11 10:42:21UTC为Failure，不是验收通过。独立核本run前三样本、两job、Actions索引的6组receipt／原body字节数及SHA256，另核REST403原body；URL均与final URL一致，精确提交链接及所有非空step log URL均指本完整SHA／各原job ID。早两run样本In progress和REST403保留，不称成功REST或全日志下载。

|官方终态原件|独立核验|
|---|---|
|run r3|177,128B，body SHA `3a65063e971882402b4c811392f2fc05cb7a38a66600226813b70d309e891172`，receipt SHA `cf9ac62915af63317a8a07ccf5c3cfa9725a6957f8b937c24ca9ffa3536c6599`，Failure|
|Windows job130464821531|160,063B，body SHA `95b927a33c894268935ab03235527314c70958b17f5db041152b7791d9eb08d7`，receipt SHA `f17d94740332ddb88d9b7935431e0b60f61c130cab18cbc7ca0d80093204ce79`，completed；Build/install、reference identity、Native regression、PowerShell安装升级4必要步均success|
|Linux job130464822022|181,295B，body SHA `81ae32e64cc5c04d52163a5dea4df765147f4875049d7c1b6e210adde9eaafbc`，receipt SHA `9b4f21f8543e1742b802ada4bc8244cc34568904f00cb7610a34348574641801`，completed；Build/install、reference identity成功，Native regression failure；PowerShell按原workflow跳过|

两个保存目录最初按顺序误贴Linux／Windows名，未更名／覆盖原件；本结论按原URL、页面实际matrix名称及step属性识别OS，未按目录猜测。Linux原注释为 **6 failed／1394 passed／87 skipped／36 subtests passed，1015.45秒**；6个失败均来自新增source submission：1个正常start、2个policy／claim和3个unknown首start，在 `review:root/review/correctness/review` 的 `claude-code`／text-only 被原新增准入以 `Selected executable is unavailable: claude` 正确拒绝，未到相应用例想测试的后续路径。

**ST2／P2，CI终核时开放，现已关闭。** 精确提交的 `tests/test_issue_submission.py:18` 中source_submission只配置临时Codex、inspector／planner程序；它复用的issue_creation／work_graph仍冻结一个claude-code reviewer，却没有给该选中后端提供明确本地程序。测试因此依赖开发主机PATH里恰好有Claude，CI的干净环境失败；产品按实际冻结选择拒绝是正确行为。已独立读取本提交这4个测试／fixture所有者及Input准入源码，没有用当前F7c草稿推断本候选。当时要求的最小修正为只在source fixture的临时PATH提供显式本地claude程序，继续真实程序availability／配置／模式校验，不装真实CLI、不恒真mock／跳过，也不修改产品；复用原13项检查，无需另造shim测试。以下修正原件及完整六文件候选复核已完成。

该次CI终核时Spec产品实证保持原范围，Standards的ST2/P2重新开放，`6a7e9a1`精确交付未完成。下一片F7c未提交源码与测试明确隔离，不用其live字节充当该提交或修正候选。

## ST2最小修正与完整六文件本地出口

修正基线为精确提交 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7`。完整tracked差异只有六文件：`docs/PLAN.md`、本片plan／delivery／review、本片acceptance JSON及 `tests/test_issue_submission.py`，均已逐字审查。未来F7c的research／plan／delivery三份未跟踪Markdown明确排除；其十份产品／测试草稿已移出当前候选，当前全部445个产品文件逐字等于6a7e9a1的Git blob，未以F7c字节修补本片。

测试唯一行为差异为source_submission增加monkeypatch参数，在原临时config内建立 `claude` 指向测试Python的symlink，再将该目录前置到该fixture的PATH。它与原selected-codex一样只提供明确的本地availability程序，真实后端配置／模式／程序探测、原policy／claim／attempt及unknown恢复照常执行；没有产品变化、真实CLI安装、恒真available mock或新增skip。四个原测试函数AST及原参数化用例保持，没有增删／复制检查。

独立逐字读取 `.ergora/checks/f7-source-admission/commit-closure/fixture-repair-r1/` 原件：result记录原r2非editable解释器以 `-I -m pytest -q --tb=short tests/test_issue_submission.py` 运行、初始PATH为 `/usr/bin:/bin`、exit0和命令70.508934秒；原stdout确为 **13 passed／69.80秒**，stderr为0字节。当前fixture SHA `f97f973c56b691c81bbb64ebad2ca8215fe4169cee1d7768a729bf1e0616fae2` 与result／公开投影相等；result SHA `9fb523302384be4be3bffa23fb3d308aa15a1d62f453c1706f63238e866133e9`，stdout SHA `09a5c8a752371035da10873da3103fe26fade0d7cc4052142a7912ba21b2abad`。没有把此定向结果扩成全套或新提交CI成功。

再次只读重算当前源码／6a7e9a1 Git／r2 wheel／安装全部445文件相等，两RECORD的450／455行摘要和大小均通过，283冻结文件与固定基线相等；wheel SHA仍 `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`。原自身模型产品附件保持，新fixture字节由本次独立复核覆盖，没有继承旧模型approve。

新增公开 `first_exact_delivery_ci` 与原ci-result-r1逐字段相等，仅过滤HTTP headers；两job／run receipt另与原保存receipt及HTML字节大小／SHA核对。按原页面data属性重核平台、必要步骤conclusion／起止时间及精确commit-bound log URL，Windows四步、Linux三步的原状态均相符，目录误名与早两非终态／REST403明确保持。新增fixture_repair的命令去环境化投影、原结果摘要／耗时／初始PATH／fixture SHA均与原件相符；未公开HTTP cookies／私有路径或借旧Windows成功关闭新提交。最后纯文档delta已核：PLAN移除指向未提交C1文档的链接，delivery将首样本待验明确标为当时状态。完整六文件静态复核的1个Python AST／1份JSON均可解析，37个本地Markdown链接目标均存在且已跟踪；6个载入秘密值及私有home路径检查零命中，`git diff --check`通过。仅核本地目标，不声称外链、锚点或Mermaid运行。

ST2/P2关闭。修正候选Spec／Standards本地开放0／0，本地出口通过；原6a7e9a1／CI43003408859仍为失败记录。该六文件修正的新ready／精确提交／独立远端Ref及它自己的双OS必要CI尚待后续原件终核，本报告未提前关闭精确交付、F7c或整个项目。

## 修正提交472ff60的精确身份与独立Ref

普通修正提交 `472ff60a6d27c91ef5d5285f959e61d3b935341d` 的直接父为 `6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7`。独立读取精确Git tree／blob，变更恰为上述六文件；repair-ready-r1原manifest SHA `a26418652de3722637f3362961964927cdb4006e81554c7de04475ecbe9cbdfc`，六件大小／SHA256／Git blob对象及 `100644` 模式均与冻结ready文件相等。提交内本报告blob为24,719字节、SHA `4dea6d5772394c09103d5be28a2c236bd1e057a02cb6f31c05c526f5547829a7`；本节为该提交后的事实追加，没有冒称已包含于其blob。

精确472ff60的445个产品blob与原最终r2 wheel／安装逐字相等，450／455行RECORD所有非空摘要和大小重算通过，283冻结参考文件与该提交父基线相同；wheel SHA仍 `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`。后续恢复的F7c live草稿未进入此对象核验，没有据live源码、旧本地结果或原模型判词扩大已提交修正范围。

作者repair-push原receipt／stdout／stderr已逐字核，普通推送exit0，原输出为6a7e9a1→472ff60。收到完成通知后，评审者仅一次对现有origin执行只读 `git ls-remote --refs`，exit0，原输出为完整 `472ff60a6d27c91ef5d5285f959e61d3b935341d` 及 `refs/heads/refactor/architecture-foundations`；没有认证更改、网络重试或推送。

修正的精确Git／ready／报告／包／冻结及独立远端Ref通过；472ff60自己的双OS必要CI仍待原终态终核，未借43003408859的Windows成功或其他提交结果关闭本片。

## 修正提交自己的CI43007648352终态与精确交付终结

精确提交 `472ff60a6d27c91ef5d5285f959e61d3b935341d` 自己的[Portability run43007648352](https://github.com/626619403/Ergora/actions/runs/43007648352)，官方run HTML在2026-11-11 11:10:24UTC明确为 **Success**。本轮仅离线读取已有原件；独立重算首Actions索引、run、Linux及Windows的四组receipt／原HTML字节大小及SHA256，HTTP200、URL＝final URL均相符，没有新增网络请求、安装或产品／模型重跑。

|官方原件|独立重算与状态|
|---|---|
|repair-actions-index-r1|320,317B，body SHA `774dd5fe9cc8b0d26d6e60f4701d06ec12284720789257733fc734d6aeaf4f6a`，receipt SHA `4da9fc928bde7ff5d18deb2d690b798a3f55150a5f45be2425cc6638c18107c8`；原样本仍为In progress|
|repair-ci-run-html-r1|157,129B，body SHA `a61dc97805fd125ee486e08a0330eb36f579c93244f10e365796ce592afda0e6`，receipt SHA `225cd57ff00c252f27d089b4a12e46e770c3261db320c1d67f0b217c42726b17`；Success|
|Linux job130479025102|161,678B，body SHA `3c2934c3693d57812e1685cb34a8a7f86f402f078d951892b707240b294814cc`，receipt SHA `92638d765328091757775b382553ad2ffbfb9a1c46439b6f5c51b4d6150b2cb3`；实际matrix为ubuntu-latest／Python3.11，job completed／succeeded|
|Windows job130479025624|159,766B，body SHA `3bdf17f64736b7e5c2f509185a2f764b88475f60a67912460b13608227d90809`，receipt SHA `08e489fda7eb7ce998c44503e2b93df7d1200315e0b100dcff02535334e3b918`；实际matrix为windows-latest／Python3.12，job completed／succeeded|

从首索引的原embedded JSON独立提取run，完整提交链接／run ID／Portability／`.github/workflows/portability.yml`及分支与原exact-run投影相等；没有把其In progress改成终态。run终态页面另含完整472ff60提交链接。按该精确提交的原workflow核必要步骤，再从两job原HTML逐件核data-conclusion、开始／完成时间及所有非空data-log-url：Linux的build/install、reference identity、native regression三步均success，分别完成于10:55:44、10:55:44、11:08:23UTC；Windows同三步及PowerShell安装升级四步均success，分别完成于10:56:18、10:56:19、11:04:25、11:05:50UTC。每条非空step日志URL均绑定完整472ff60及各自原job ID；Linux的Windows步骤按原条件skipped，不计为必要步骤失败。

作者 `repair-ci-result-r1.json` SHA `1bba16b989ffc68496681a207c87b6cb22166381265f80f1636fb1d441a7c504` 的全部身份／终态／平台／七步结论、完成时间、日志URL及body SHA，均与上述独立原HTML提取相等。证据范围为官方公开HTML及其可见步骤状态，没有声称下载完整认证日志、成功REST查询或取得CI测试总数。原匿名REST403、原6a7e9a1／CI43003408859的失败及其六例完整摘要均保持，未继承该run的Windows成功；恢复中的F7c live产品字节未进入本次Git／CI判词。

本片B1c修正的完整本地出口、六文件精确Git／ready／冻结报告、445包／两RECORD／283冻结、普通推送及一次独立同SHA远端Ref，以及472ff60自己的双OS七必要步骤均独立通过。Spec／Standards开放0／0，ST1／ST2均关闭，B1c精确交付终结。该结论不关闭F7c或整个项目，也不扩大原模型、混合旅程、availability与性能证据范围。本节为472ff60提交后的事实追加，提交内报告blob仍为此前冻结的 `4dea6d5772394c09103d5be28a2c236bd1e057a02cb6f31c05c526f5547829a7`。
