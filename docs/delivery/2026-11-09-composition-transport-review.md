# CR2b：版本化提交与证据读取独立审查

日期：2026-11-09。审查者：fresh-context agent `composition_transport_review`，未参与实现；独立读取原始范围、完整 tracked diff、两新增源码/测试及相邻实际调用链。依据项目 [AGENTS.md](../../AGENTS.md)、[PLAN](../PLAN.md)、[本片交付记录](2026-11-09-composition-transport.md) 和 maintainable-project-delivery / codebase-design 技能分别评估 Standards 与 Spec。仅写本报告，未改生产或测试代码、提交、安装依赖或启动外部服务。

**本地出口结论：Standards / Spec 均通过，唯一 P3 冗余检查已修复并复核，无未解决 finding。最终 R3 包身份、真实 Temporal/SDK 原件和五份 history 的独立离线重放已核通过；B5 的精确提交、自己的必要 CI 与实时远端出口仍待后续同片终结，当前不登记完整 CR2b 精确交付完成。** CR3 的真实 Agent、动态审查材料和可信 verify 投影不在本片。

## 审查身份与范围

原基线为 `c36bcdc028def80429f674d250ee65838d2adc73`；审查开始及当前 HEAD 为 `25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8`。后者只含前片 Windows 文件旅程提前跳过及记录；本片实现仍为未提交工作区。已读全部 `git diff HEAD`，包括前片状态追加；不把这些追加当作本片执行证据。

生产范围共十文件：新增 [reference_inputs.py](../../src/ergora/reference_inputs.py)，修改 [reference_workflows.py](../../src/ergora/reference_workflows.py)、[reference_worker.py](../../src/ergora/reference_worker.py)、[task_envelopes.py](../../src/ergora/task_envelopes.py) 和 `reference_task_{creation,submission,runtime,approval,evidence,reconciliation}.py`。测试范围共九文件：新增 [test_composition_transport.py](../../tests/test_composition_transport.py)，修改 `test_architecture_boundaries.py`、`test_composition_runtime.py`、`test_composition_workers.py`、`test_original_payloads.py`、`test_reference.py`、`test_task_evidence_index.py`、`test_task_job_evidence.py`、`test_task_plan.py`。另读冻结 native 的 CLI/contract/transport/adapter/activity/workflow 和公开 tasks/reference 入口，确认消费者实际行为。

最终已审十九份生产/测试文件的身份如下。对本表路径→SHA256映射作 UTF-8、sort_keys、紧凑 JSON 的 SHA256 为 `d345fe56469e9894ccd07f411d02aecf714b74c1b9472e01ee18c24c80ae68b8`。

| 文件（`src/ergora/` 或 `tests/`） | SHA256 |
|---|---|
| reference_inputs.py | `9e9596551b29ac1cbdebe5e891261820f87e64136131ad45ae4db261e57db612` |
| reference_task_approval.py | `106f82510c114624a823105501ce5eaa8e9dfdcff36d7f93b912618bd815752f` |
| reference_task_creation.py | `0199ba996ceb8a4a6e15e3141d0e3aa3b32b289a0e1c860ff268172c68d629ec` |
| reference_task_evidence.py | `eb968036312b647113640d8bd4ac50ac46d4c86a33129778dd7ebdd93730cbb5` |
| reference_task_reconciliation.py | `a65c9b53b17e797bea48920cd0fdf2d85902ebb0b2394e269625d46c7bbbab95` |
| reference_task_runtime.py | `796e4fd8df18c9e8ec3c39667be2d9dc6883475d3aba7c092f6e2baf25c173f6` |
| reference_task_submission.py | `f5fcd8bb17481925f407f51bb9aa38fc69b0e643cc4ccfec3b07b1fbe1bc3426` |
| reference_worker.py | `998242a5d35d8ebd5b0d458c55ffea46a3bf8e1db294421d149445ea6de58e65` |
| reference_workflows.py | `8ad1bdfb12231de67d879526664c55406ba5a04ecd858ba472aa300fce5c0a55` |
| task_envelopes.py | `6d4a8e8d2b2f839d96b40035939f9b22cefcb4a2996c972abf635d7cc70437f1` |
| test_architecture_boundaries.py | `1414a36c00701574cf3bc78031dee8f97ed4b1ca74894218bd82336bfd22fda8` |
| test_composition_runtime.py | `1a143138376a25dbd5dee51f066c99c988167c3dfb6ca43453d9f2f658fe2d9e` |
| test_composition_transport.py | `cc9916b505c0284297047a808816f19820e1b2c551a99abd2c0547b074282edf` |
| test_composition_workers.py | `09db718688fc2483a74ca112d834b39d276a7865a605384b8a12544715d5a12a` |
| test_original_payloads.py | `154bd081c57b007d726d06498af88db9466b976a3d9ef4b96b79b632e9e4acf0` |
| test_reference.py | `e39247cc7707de6482fccb8d4eae3c96130b0116ffe112dc9bf56048877fb742` |
| test_task_evidence_index.py | `1378c20b7eb3037d395a713bd2db6663f5bbafa1a6aa1d5d0830d2d75a59c531` |
| test_task_job_evidence.py | `c95e7e899e2db2b33a059526e1aff2a497f3f9dd9aae2df558089ae7e30c1041` |
| test_task_plan.py | `c02ca18d1d8ea2a50c0f196a400099df7fd827d1e0f72dd09f31a1de6411395c` |

## Standards

版本所有者有实际收益：`reference_worker` 通过共同 worker 构造合同登记两个实现，`reference_task_runtime` 通过同一 input 合同启动并验证原始 payload，`reference_task_submission` 用它保留完整 document 与准入 projection，三个证据读取器消费相同的 submit 名和目录映射。局部 `_INPUTS` 映射只登记本家族；上层没有按版本或具体类重复分派。`admission_spec` 和 `require_submission` 的两个实现分别拥有真实不同的准入/开放行为，不是为未来扩展增设的空架构。

`task_envelopes` 的纯 JSON 身份谓词同时被 SDK 发布端和持久证据读取端使用，避免 input↔workflow 环。SDK workflow 类仍在原模块，`CompositionDevelopmentWorkflow` 继续继承冻结的 `DevelopmentWorkflow`，只保留版本入口、完整 context 与活动名转换。没有复制六阶段、注册另一个账本、关闭 SDK 沙箱或修改冻结包。

新增检查对应可达输入：完整 document 防同 legacy 的其他 admission 替换；请求/任务/profile/context 身份防错误 job 归属；五个 base roots 检查防配置漂移后读取外部目录；公开执行能力 guard 防未接可信执行时准入。旧 v1 的 legacy reader、doctor、policy、claim、原 run/memo、attempt-before-send 与未知恢复分支仍由原所有者负责。

### ST1 / P3：发布端对 admission 自身作两次完整哈希（已关闭）

R2 的 `reference_workflows.py:21` 调用 `matches_context(spec, context, context['admission'])`。谓词末项将 `context.get('admission')` 与同一对象再次哈希比较，正常 JSON 输入下恒真。内存探针记录两次 identity 的参数为同一 admission；每次提交都增加两次完整信封序列化/哈希，却不保护额外失败条件。最小修正是在已 `unwrap` 校验 admission 的发布端只传 `spec, context`，保留读取器把原始 document 作为第三参的必要比较。

实施者已采纳；独立重读该行和完整 diff，确认只删除上述第三参及 EOF 额外空行。当前 workflow SHA256 为上表 `8ad1…0a55`；R2 为 `abc655a54b729dcce3299b4af5d588007a33251837a3a75581fb8a3b418883c3`。没有放宽任务/profile/spec 身份检查，读取器完整 admission 比较保持。`git diff --check HEAD` 修后通过。该项从未作为 P1/P2 或执行正确性阻塞。

## Spec

| 要求 | 独立核对 |
|---|---|
| 完整 v2 document 与 legacy 投影双身份 | input 同时保存两者；submission 的 intent `spec_sha256` 取完整 document；native CLI 收到原验证后的 legacy projection。调用前重新读取并核对 wrapper；VerifiedSpecClient 对原始 payload 列表作完整 JSON 身份核对，然后才向 native lookup 返回 projection。 |
| 标准库可读版本选择 | module 顶层只有 abc/pathlib/task_envelopes；独立 `-I -S` 子进程实际解析并匹配有效完整 v2 信封，sys.modules 无 temporalio/dev_platform/agent_platform；worker/Activities/SDK 类按使用延迟导入。 |
| 版本活动名与请求目录一致 | worker、原始输入客户端及 plan/job/closed-run 读取器沿同一版本合同。五个注册 base roots 校验在版本映射之前；独立探针对两版本分别篡改全部五目录均被拒绝。 |
| 完整 context/admission/history 绑定 | 三读者核 request 身份及 input.matches_context；v2 的完整 admission 等于保存的原始 document。选中 context 的 SHA 继续绑定实际请求 envelope，receipt 再绑定同一 job。九例真实 SDK 消息/codec＋本地文件检查通过，包括缺 admission 及同 legacy 的另一 admission。 |
| v1 提交与未知恢复 | 检查原 CLI.task_action、checkpointed transport 和 memo owner 链；attempt 仍写在 native start 前；NOT_FOUND 不转为重发。旧恢复/冲突/准入回归日志与来源分开记录。 |
| 公开 v2 start/status 仍拒绝 | `_Submission.run` 的 status、prepare/dispatch/resume 都先 `require_submission`；CompositionInput 在 workflow import 前报未开放。`tasks.status` 仍在调用 runtime port 前拒绝。内部 submitted/readers 可准备版本身份，不开放正式新任务执行。 |
| workflow 路径及旧 history | workflow 类路径和注册名未迁移；基类调度不变。最终 R3 原生 SDK 记录和三份新 history、两份旧 CR1 history 的独立离线重放均通过，详见末节。 |

当前源码范围没有未解决的 Spec finding。正式 Agent、原 verify 写 projection 的适配、完整 Supervisor 与真实 owner 批准/故障恢复属于后片，当前审查没有用合成证据补记这些能力。

## 已核证据与实际限制

本地大日志位于 `.ergora/checks/ac3c3-transport/`，是本机复核证据，不是本报告新增的公开交付文件。以下区分审查者实际执行、已读实施者原件以及待完成项目。

- 独立实际运行 R2 非 editable 安装包：`PYTHONDONTWRITEBYTECODE=1 …/r2/wheel-venv/bin/python -P -m pytest -q -p no:cacheprovider tests/test_composition_transport.py tests/test_reference.py::test_versioned_input_contract_imports_without_sdk_or_native_modules tests/test_composition_tasks.py::test_composition_submission_is_rejected_before_any_legacy_remote_or_dispatch_intent`，**11 passed，5.74 秒**。
- ST1 修后独立实际运行 R3 安装包：`test_composition_workers.py::test_composition_activity_rejects_wrong_admission_before_publication`、完整 `test_composition_transport.py`、公开 v2 提交拒绝用例，**15 passed，7.36 秒**，包括原五种发布拒绝和九种版本读者行为。
- 独立两个内存 pytest 探针：有效完整 v2 在 `-I -S` 下读取/匹配；两版本全部五目录漂移在映射前拒绝，**2 passed，3.45 秒**。未新增测试文件或修改既有测试。
- 独立逐文件重算 R2 源码/wheel/非 editable 安装的 **368 文件相同**，并核 **283 冻结身份**与 c36 不变；R2 wheel SHA256 `063cc4db0e05bc5ebd58c969fb093a3daed57dac3789d8d4ed730128de413010`。这次核验发生于 ST1 修正前，不移记为最终 R3。
- 已读 source 原件：`source-regression.log` 的 **174 passed，196.04 秒**；该进程在 guard 修正前启动。修后 `r1/guard-regression.log` 的 **19 passed，5.49 秒**单独保留。最早 **75 passed/1 failed，207.52 秒**的缺 SDK 诊断错误没有抹去。
- 已读 R2 `wheel-regression.log`：**152 passed，17.07 秒**；已读 R3 `identity.log` 的 **368/283**和 `wheel-regression.log` 的 **153 passed，19.44 秒**。审查者随后独立逐文件重算 R3 源码/wheel/非 editable 安装，**368 文件完全一致、283 冻结保持**，且等于原 package-identities.json。R3 wheel 为 `998ab8c41ef935f97cebd40fd95db1486cc07a399d9e34d55586a2f4d54ed4f1`。
- 独立读取保留的四份探针失败日志末项：R2 缺 adapter.json、R2 缺 TEMPORAL_ADDRESS、R3 缺本地连接模式而读取 TEMPORAL_API_KEY、R3 漏传 reader 的 artifact 参数。它们是探针装配失败；修后最终成功有自己的目录/原件，未以旧失败目录或待运行状态登记通过。

## 自身模板与原件复核

已独立读取公开 [R2 身份](evidence/2026-11-09-cr2b-self-review-identity.json) 和 [R2 原始判定](evidence/2026-11-09-cr2b-self-review-result.json)。真实 Ergora structure-review / task MCP / Codex 调用 run `b617d2b0ad7c4f22bbdb857ba74b57bd`，**173.70 秒、exit 0、succeeded、approve**。附件 **53,021 字节**，SHA256 `c42f373589f169c2daae5b103cccb6fd194162ea4c0043d8576d89330f09b325`。

审查者从原 stdout MCP item 读取实际三页，offset 为 **0 / 18000 / 36000**，next_offset 为 **18000 / 36000 / null**；拼接后的 UTF-8 字节逐字等于附件且 SHA 一致。原生 MCP 日志确认 list 及四次 read（含技能正文）成功，未依赖结果文本自报“已读完整”。另核固定 input digest、protocol prompt SHA、结果 SHA、公开判定正文及 SQLite 只读连接中的唯一原 run，与原 codex.stdout 一致。

此 approve 精确绑定 ST1 删除前 R2。模型自己明确只收到部分所有者的差异上下文、未独立执行测试或验证完整 native/replay 合同；这些限制完整保留。本次 fresh-context 审查另读完整源码和相邻 native 调用链，ST1 后源码差异已独立复核。R3 的发行、拒绝检查和真实 SDK 原件有独立复核，未移记为模型在 R3 重审；普通提交、自己的必要 CI 与实时远端终结仍需后续记录。

## 最终 R3 运行原件与本地出口

独立读完 `.ergora/checks/ac3c3-transport/r3/sdk-workers.py`（222 行）及 `sdk-workers.json`。最终原件时间 **2026-11-09 00:03:31 UTC**，实际旅程 **16.017 秒**，使用 R3 安装包、实际原生 worker/bootstrap、独立 native SDK 环境、真实本地 Temporal 与 FileAdapter。探针先保留旧 worker，再确认其没有消费新版队列；随后显式启动新双版本 worker。两版本各经过实际待批准计划的三份材料读取、选中 job 的 published receipt、closed-run 六作业完整匹配。

该探针直接使用内部 transport，并为 reader 测试记录匹配的合成提交 journal/memo；**它没有通过正式 Ergora v2 start，也不证明 v2 attempt-before-send 准入已开放**。旧正式提交的准入/attempt/memo/未知恢复由源码与原生命周期回归分别核对。外部模型、owner、产物和 checks 均标记合成，REVIEW_READY 只说明此协议旅程，不能用于宣称真实 Agent 或可信候选成功。

审查者在 R3 非 editable 包中另外进行只读核验：通过原创建/提交校验重新加载两正常 journal；从原 SDK protobuf history 解码原始输入、memo 和全部 submit context；逐项核请求 envelope、job SHA 与 FileAdapter 验证过的 receipt/全部产物；再次默认沙箱离线 Replayer 重放本片三份及 CR1 两份原 history，**五份全部通过**。未重开服务或重跑外部模型。

| 原运行 | 事件 / 原结果 | history SHA256 |
|---|---|---|
| legacy `01a1bd9d-dbf0-72c1-9eb1-aff231772bf6` | 95 / REVIEW_READY | `32a76f38e0008a297ae5c9225545f4e0442b268c010f2634576d54f280a7332d` |
| composition `01a1bd9d-cb38-7467-bf41-e0c0b71d4139` | 95 / REVIEW_READY | `eb3dc23e8a8a09cae0be621b13b680506c41722979adfabb25979584fc2a1d59` |
| pending composition `01a1bd9d-f2a4-7969-ab4a-6737b73c0547` | 33 / CANCEL_UNCONFIRMED | `f633f1ccec165099d270c33bf9247c1d1d5fd5129bfb6c31c575bdf41970a748` |

两正常 run 各六个阶段为 inventory、plan、work:one、integrate、verify、review；分别使用 `development-tasks` / `development-tasks.composition-v2` 和 `requests` / `requests-composition-v2`。完整 v2 document、原 intent memo、每份 admission、队列及文件目录一致。pending 原 history 恰一 `request_cancel`，fence 的唯一 unresolved job 与原 CANCEL_UNCONFIRMED 保持，未虚构外部终止确认。

检查前后 **76 份 runtime 文件的 SHA 全部保持**。原件两 owned 进程 exit 0；审查者另查两 PID 均消失、7233 / 8233 端口均关闭。R3 源码/测试仍为本报告身份表；新增 CR3 文档只作为下一片计划，没有 CR3 实现或验收结论。本地两轴审查至此完成，可固定本片精确候选；其必要 CI 和远端终结需继续记录，不能从前片继承。
