# AC4.3c.2–5：专长执行者正式纵切片

固定基线 `11a00061c0573f3d24e0402671d02acc1d1e9107`。按[已审合同](../plans/2026-11-09-work-agent-contract.md)实施。C2工作调用与C3分配、C4来源/恢复合为一个可运行纵切片：新模式只有随真实v5消费者一起发布；分阶段本地核对，不把尚未接通的格式称为支持。

## 范围与所有者

- 原task-definition-v2显式execution选择v5；冻结一对一unit映射、完整manifest和后端政策。旧v1-v4不重解释。
- 共享原静态图的数据投影；work静态传递关系必须等于原units DAG，work/review叶覆盖完整且不交叠。work输出在原integrate/verify后才供review。
- 原Workflow.units/stage继续拥有调度；v5扩展其祖先容量准入，不新增调度服务、持久running表或账本。
- 原Executor保留checkout、路径gate、确定性检查、fence与commit；新调用完整装载祖先/Skill/批准计划和原产物，不截断。agent_runs复用固定快照/MCP/原生调用保存，旧只读公开入口拒绝保持。
- backend Interface拥有工具与能力政策。第一正式workspace模式只在Linux/WSL2的显式可信current-container上提供；Codex真实工具探针已成功，Claude新workspace能力在未经实际验证时明确拒绝，其旧review能力保持。能力声明区分工具配置、Git最终路径gate与无OS/网络隔离。

预期改动：原agent_backends/agents/agent_runs/stage_driver、review_dags/task_envelopes/tasks/reference_inputs/reference_workflows/reference_executor/reference_task_creation、原task定义schema及示例/使用文档。新辅助仅归相应现有所有者；纯数据不引入Temporal依赖。283冻结文件不动。

## 验收与进度

|节点|实现|验证|审查/交付|
|---|---|---|---|
|C2工作调用|内部 workspace 调用、完整快照/MCP 和实际 argv 已接通|R2 安装包真实 Codex writer 76.00 秒；完整祖先、固定 MCP、原范围/check/commit 全链通过|源码独立两轴通过；自身真实模板approve|
|C3正式映射/调度|显式 v5、一对一分配、原 units/祖先容量接通|两互补 writer 及三 reviewer、独立分支调度；四正式服务旅程 374.27 秒通过|同片最终独立Spec/Standards本地通过|
|C4跨阶段/恢复|原 work 来源到 review、原调用/回执恢复与取消接通；WA-S1 最小修复|缺/坏 post-gate 证据拒绝、合法 commit 恢复；实际 worker 暂停/继续和取消对账通过|WA-S1 独立复核关闭；所有窗口覆盖不作承诺|
|C5完整交付|R2 非 editable 包/旧历史/实际服务/真实 writer 完成|372/283 身份、13 旧+4新 history、137 采样进程清理通过；原 291通过/6跳过/1超时，原样受影响单项重验 1通过/9.52秒|自身真实模板approve；最终独立Spec/Standards本地通过，普通提交/自己的 CI/HTTPS 远端仍待验|

不以fixture证明模型质量，不以CLI help证明Claude推理，不以worker重启证明全部进程崩溃窗口。不新增依赖或CI作业。原件放私有持久checks目录，公开材料脱敏。每节点结束更新此记录与PLAN。


## 本地实现进展

C3已接显式v5/Input/队列/原request根/活动与Workflow，原units调度中按祖先容量准入、工作实例独立session；完整静态图投影与原units传递关系一致。C4已接工作来源的原request/receipt/claim/实际调用与Git祖先校验、强制最终plan/verify、原监控调用恢复与已有终态回执复用。均尚待实际写旅程，不预记完成。

开发venv原来是更早的发行包且缺mcp：初次文档parser/新测试collection使用该旧安装分别失败，显式源码parser通过；本片用uv将开发环境改为editable并补现有固定mcp==2.3.0，仅用于开发。无pip/setuptools的初次安装失败原日志保持；最终仍另建非editable包验收。新测试首轮10通过/1期望错误（默认test-value本来也选Codex），修正为比较实际所有reviewer后11通过。原生首试在fixture准备阶段因局部manifest_path未定义停止，修fixture后再验；这些不是生产通过证据。


## 首次原生链发现与修正

真实两个writer都完成原工作检查及可信commit，review在读取完整来源时触及原1MB预算：第二writer原材料约668KB、prompt约654KB，再交付所有原产物会超限。保留原拒绝；新v5的模型context改为绑定原admission/context摘要，并复用输入包中已完整保存的manifest，端口仍提供全部原产物，祖先资料不减少。完整原stage context仍是可信原件，不改变Temporal载荷、旧v1–v4模型材料或它们的恢复字节。修后第二writer材料约170KB、prompt约167KB。不同原审计产物内部的重复仍计入最终预算，长链超限继续拒绝。

原生测试r4：1通过/5失败，其中full的预算拒绝是实际行为；其余四项在我编辑字符串表达式时碰到暂时语法错误，不能当作独立行为证据。已修复并compileall通过，停止受影响legacy组；后续不在进程验收中修改被测生产源。r5：4负向用例通过，full/recovery两项写阶段通过后被旧fixture对任意`work:`文本的字符串匹配误判为writer（review现在确实包含原工作来源）；已把夹具条件限定为非review结构结果，再运行完整19项。未将这些原失败覆盖为通过。

当前初始独立审查可核完整实现，最终包、真实模型、自身模板、正式Temporal旅程/旧重放及交付门禁仍待验收，不把初审当完成。


## 源码验收r6

完整新增 **19 passed /143.04秒**。两互补writer各有原生固定MCP握手、实际argv、全部祖先输入、原范围gate/确定性checks/可信commit；原integrate/verify后接三review。来源产物/claim篡改在下游模型调用前失败；scope和Agent自提交HEAD均拒绝。原模型/check/commit完成但原receipt尚未发布时同原job恢复，实际Agent run计数不增；发布后再读原终态也不重复。编译图的嵌套容量单测证明等待的子分支不占独立分支原unit槽，另测结果/取消同时到达不派后继。夹具只证明协议和所有权，不证明模型效果。

原件为私有`native-tests-r6.log`及`native-cases-r6`；没有沿用`r4/r5`原失败作为通过。本片新的fresh-context双轴审查已启动，报告另记；非editable包、服务、真实模型及交付门禁未完成。

## 独立安装包 R1 与恢复复核

`uv build --wheel` 构建新的非 editable 包，并装入独立 Python 3.11 环境；源码、wheel 与安装目录 **372 文件完全一致**，原 **283 冻结文件**逐字节保持。最初使用未装 build 的开发环境运行 `python -m build` 失败，改用现有 uv 构建，无仓库依赖或 CI 修改。安装包已重放 **13 份原 v1–v4 历史**；15 组受影响回归及四个新 v5 公开 CLI/Supervisor/Temporal 旅程另行运行，不能提前记通过。

服务首轮 Temporal/worker/executor 已启动，A2A 因验收环境缺少既有可选 `a2a-sdk` 而启动失败，随后原 Supervisor shutdown，采样的 5 个原 PID/starttime 无存活。补装既有固定 `a2a-sdk[http-server]==1.2.3` 后以新目录重验；首轮日志保留，不将准备失败归为完整旅程成功。

独立评审正复核「Agent 自行 commit 后、Executor 首次 HEAD gate 前崩溃」窗口。正常自提交拒绝与合法可信 commit 后恢复两项通过，不能替代该交叉窗口。生产源与已测 R1 包保持，若证实将保留原包复现、最小修复并建立新包，不能放宽可信 Executor 独占 commit 或原路径 gate。

## WA-S1：原包复现、最小修正与回归

[初次独立两轴审查](2026-11-09-work-agent-runtime-review.md)确认 WA-S1（Spec/P1），Standards 无实证 finding。作者另用 R1 安装包重跑独立生产方法重放，确认无新 Agent 调用仍接受原本应拒绝的 Agent commit。新增实际 monitor 完成后、首个 HEAD gate 前注入 `BaseException` 的恢复回归：原 R1 **2 failed /31.93秒**；一项直接绕过成为成功，另一项篡改 post-gate 证据仅在原后续冲突处失败，均不满足正确的恢复拒绝合同。原件保留 `wa-s1-original.log` 与独立重放输出。已有具体因果证据，因此诊断不再生成没有依据的替代理论。

最小修正只在原 saved workspace call 恢复分支：HEAD 偏离原调用起点时，从原可信 `STATE/artifacts/<task>/<job>/agent-selection.json` 核对完整 post-gate 内容，并以原结果完整字节核 SHA；缺失或不符明确拒绝并要求对账。原调用、权限、MCP、claim、监控终态及来源核验保持，没有新 marker/账本、重发或调度器。该原产物在首次 HEAD gate 后、原 Executor commit 前发布，故合法可信 commit 后恢复仍可复用。

修后源码 **3 passed /64.18秒**：缺原证据拒绝、证据篡改拒绝、合法 Executor commit 后同原调用恢复成功，后两种写调用均不增加。新 R2 wheel/全套既有锁定参考依赖准备后，另验新包全组与实际服务。R1 其余验收只代表 R1；首轮补依赖后两次服务准备又分别遇过长 UNIX socket 路径与缺 MLflow 元数据，原失败和各次采样清理保留。R2 使用短的持久目录并安装既有完整 requirements.lock，不改生产依赖或 CI。

## R2 安装与真实工作调用

R1 原 15 组 **290 passed /6 skipped /960.08秒**，六个跳过属于显式未配置的可选 Forge/mini 等集成；不包含后来新增的两项恢复回归，不代表修后 R2。R2 新包在独立 Python 3.12 环境安装原参考锁定依赖及当前 wheel extras 后，源码/wheel/安装 **372/283 身份**再通过，**13 份原 v1–v4 历史**再重放通过。正在进行 R2 的相同组加两项回归、四个公开旅程和原进程清理观察。

R2 单独真实工作验收 **76.00秒成功**：通过原正式 v5 context/Executor 调用一个真实 Codex writer，使用完整祖先与固定任务 MCP，在原 unit 范围写入，原检查与可信 commit 完成；继而第二 writer、integrate/verify 和三 reviewer 全链通过。后四份 Agent 调用明确为确定性协议夹具，不能据此声称多个模型质量或跨后端独立性。原输入库删除后的执行与同调用恢复断言保持，实际调用记录及固定 MCP 原生回执保留。私有准备首试因复制 fixture 后的相对 examples 路径错误在模型前退出，修正私有入口后重验，未改生产源。

R2 实际服务首轮已完成 owner 批准与工作调用；验收夹具把同步标记写到 checkout 外于原 unit，原路径 gate 正确拒绝，并清理采样 21 个原进程。修正私有夹具在释放阻塞后删除标记，使用新短目录重验；不是放宽生产范围门禁。原失败、请求、回执均保留，不从该轮宣称完整四旅程通过。

## R2 四个正式服务旅程

修正夹具后的同一 R2 包以新隔离的持久短目录运行公开 CLI、Supervisor、真实 Temporal worker 和常驻 executor，**374.27秒全部通过**。四任务均经原 inventory/plan 和 owner 原计划摘要批准：

|旅程|原结果与实际验收|
|---|---|
|两专长 writer → 三并行 reviewer|原 9 个 job、5 份独立 Agent 调用，work 原产物到后继及 review 完整；原 integrate/verify 后 `REVIEW_READY`；重复 start 复用原提交|
|worker 暂停/继续|第一 writer 已发出但未完成时仅停 worker，原 executor 完成；前三份 request 字节不变、只有原一次 writer，继续后才派后继|
|第一 writer 越界|原 scope gate 拒绝，`BLOCKED`；只 3 个原 job、一次 Agent 调用，无第二 writer/review|
|必需审查拒绝|两个 writer/可信 verify 正常，原正确性 reviewer 为 FAILED，保留三意见，最终 `BLOCKED`|
|第一 writer 取消|保留 `CANCEL_UNCONFIRMED` 原结论，外部原回执核 CANCELLED 后显式 reconcile 释放租约；无后继/迟到写入，也不改原 outcome|

第一、第二行属于同一任务，合计仍为四任务。每任务完整原信封、run/type/queue、全部原 job 证据及离线 handoff 校验，**四份新 v5 history 重放均通过**；13 份旧 v1–v4 history 另保留通过。最终 shutdown 后端口关闭，**137 个采样原 PID/starttime 无存活**，原数据库保持；采样不声称看见所有短命进程，不把 worker 停启当所有进程崩溃窗口已覆盖。

最终安装环境先按已有 requirements.lock 校验哈希安装，再按当前 wheel extras 安装；重叠的 Uvicorn 由 reference 的 0.38.0 更新为当前 web extra 固定 0.54.0，最终版本清单另存，不能称所有重叠依赖仍等于原锁。没有修改生产依赖、冻结参考或 CI。十五组 R2 包回归、自身真实模板及最后独立/提交/CI/远端仍另验。


## R2 回归原失败与原样重验

15 组完整回归共 298 项，原结果为 **291 passed / 6 skipped / 1 failed，1466.25 秒**；六个跳过仅为显式未配置的外部 Forge/mini 可选集成。唯一失败是既有 `test_existing_six_stage_contract_consumes_selectable_agent_evidence[command-repository-governance]` 的子进程超过原有 90 秒 timeout，没有业务断言失败。原现场处于 inventory，baseline monitor 原终态为 returncode 0；没有完成 receipt。完整原 traceback、request、monitor 及 checkout 均保留。

对原失败 ID、同一 R2 非 editable 包和同一测试**不改代码、不改超时**单独重验，**1 passed /9.52 秒**。全组运行期间观察到文件系统访问显著停顿，但尚未证明其就是 timeout 根因；不能把观察当归因，也不把原全组记录改写为全绿。组合覆盖已有 292 项通过，原 timeout 单列。没有因这一原样通过再扩大测试范围。自身模板将同时读取完整原失败与重验日志。


## 自身真实模板与最终本地核对

同一 R2 安装包实际运行 `structure-review` → `architecture-reviewer` → Codex/task-MCP，**258.91 秒，decision=approve**。输入包含全部改动生产/测试/JSON示例与完整邻接所有者，共 **39 份源文件**，以及原失败、原样重验和真实服务/模型验收原件；没有用摘要替代代码。原生流审计确认 `candidate.txt` **642,870 字节 /18 页连续读取至 next_offset=null**，其中一次错误 URI 请求保留，随后完整成功读取；源身份保持一致。完整读取只证明材料传递，不证明模型推理质量。

模型分开给出 Spec/Standards，无新增阻塞；WA-S1 修复和原证据所有者保持。它明确保留原 90 秒 timeout 和未知根因，没有把 broad run 写成全绿，也没有要求凭猜测删断言/测试。此为用户已授权的 Codex/ChatGPT 回退，不声称两模型错误独立；不能替代 fresh-context 独立门禁或 owner 批准。

已公开脱敏的 [R2安装身份与回归](evidence/2026-11-09-ac4-work-package-r2.json)、[旧history](evidence/2026-11-09-ac4-work-legacy-replay-r2.json)、[四正式服务旅程](evidence/2026-11-09-ac4-work-journey-r2.json)、[单真实writer及MCP回执摘要](evidence/2026-11-09-ac4-work-real-writer-r2.json)、[自身审查身份](evidence/2026-11-09-ac4-work-self-review-r2-identity.json)、[原模型结果](evidence/2026-11-09-ac4-work-self-review-r2-result.json)和[完整分页审计](evidence/2026-11-09-ac4-work-self-review-read-audit.json)。私有日志/配置和凭据不公开。

最终本地再核 source/wheel/install **372 文件仍逐字一致、283 冻结文件不变**；静态检查当前 **12 Markdown /276 本地链接、锚点无缺失 /88 CLI parser 命令**。两本公开手册、工作流手册、示例导入顺序和当前架构图已同步，没有改动依赖或 CI。最终独立终核、普通提交推送、该精确候选自己的双 OS 必要 CI 与明确 HTTPS 远端身份仍分别等待实际结果。


四正式服务重验的精确私有执行副本为 `runtime/r2/service-retry/journey.py`，与公开旅程的 `acceptance_script_sha256` 对应；根 `r2/journey.py` 属于先前夹具越界的原失败，不互换身份。旧兼容 timeout 原 monitor 已按保存的 PID/starttime 确认无存活，另一次当前 `/proc` 参数路径扫描没有匹配该原case的进程；这两种观察不声称覆盖所有短命进程。


## 最终独立本地门禁

[同片独立终核](2026-11-09-work-agent-runtime-review.md)通过 Spec/Standards，历史 finding WA-S1 已关闭，新增 finding 0、本地阻塞 0。主审和两个独立轴核了 R2 安装身份、四任务原件、真实writer、自己的真实审查、旧历史、公开证据与手册；完整范围38文件，后续仅review/runtime状态记账漂移。原失败、采样/MCP范围和未证明根因分别保持。普通提交、该提交自己的必要CI和明确HTTPS远端SHA仍待取得，不能用本地门禁代替。
