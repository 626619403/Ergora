# F7b.1-B1c 独立审查

评审者：`f7bc_selected_admission_review`；本片独立 fresh-context，未继承实现对话。按项目 `AGENTS.md`、maintainable-project-delivery 及其 independent-review brief 审查。基线／当前 HEAD 均为 `4638c3b9524adcba584a9313b8fd1588b5dde64d`，本片为未提交工作树；检查完整基线差异和未跟踪文件，不以 HEAD 代替工作树身份。只读源码／原件及本报告写入，没有安装、模型调用、产品修改、提交或推送。

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

已审范围通过；一项文档 finding 已修复并复核关闭，产品开放 finding 0。Input 的版本差异留在既有版本族及共同 Interface；新方法的实际调用者是原 submission 所有者，属于必要的版本合同，没有为单一调用增加新包装模块或第二套调度／账本。native／SDK 导入仍在执行方法内，纯输入／journal 的标准库依赖方向保持。

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
