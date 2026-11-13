# F8-H3：原生会话的最小消费者与接缝

日期：2026-11-14。本文是设计来源，不是实现评审或产品准入结论。承接 [F8-H3](../plans/2026-11-12-harness-admission.md)、[H3a 计划](../plans/2026-11-14-harness-session-readback.md)及[原固定 SDK 研究](../research/2026-11-12-harness-admission.md)。调查时产品 HEAD 为 `a0a42ba`，分支 `refactor/architecture-foundations`；H2 的显式可选 `api` 字段及真实调用资料尚在本轮独立审查，本文不改其候选，也不借它关闭 H3。

建议 **H3a 先让现有 `agent output`／同一 HTTP 输出入口读取原 run ID 的完整原生归档历史；H3b 再验实际 SDK 恢复和显式续接**。H3a 不启动 SDK，不发 prompt，不创建另一 run，不修改旧调用状态。它消费的是原 `native-home` 下的 session JSONL，必须明确标为归档读取，不能称 SDK 恢复。长期上下文已有落盘基础；缺的是可核身份、可完整分页的实际消费者和后续续接合同。

## 1. 证据范围与现有消费者

本次只读检查第一方源码、固定上游源码、两份真实 H2 的 native identity/result/session 文件，以及另一执行者新产生的私有副本恢复原件；只新增本文。没有启动环境、import SDK、装包、发模型或网络请求，也没有读取认证配置内容或环境值。副本探针的执行、成本与进程证据归 [H3a 交付记录](../delivery/2026-11-14-harness-session-readback.md)，本文只核原件并据此设计。

固定上游为 DeepSeek Harness `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`，Python SDK／runtime-bin 均为 `0.2.2rc2`，profile 为 `sdk-minimal`。源码定位可由[最初研究的固定身份](../research/2026-11-12-harness-admission.md#2-固定身份安装边界和证据来源)恢复；下列上游链接均固定到该提交，不要求重新联网。

|实际 Module／Interface|当前事实及 H3 应复用的位置|
|---|---|
|[`agent_runs.run_input / _run_prepared`](../../src/ergora/agent_runs.py)|CLI `composition run-input` 的 standalone 只读叶消费者。保存完整 `.input`、原 grant／祖先权限、绑定／项目修订、policy 与 run 记录；task-mcp 冻结 scope，经过 preflight 后调用原 `agents.invoke`。每次使用新 run ID、新 `.cwd`。|
|[`agent_runs.run_workspace`](../../src/ergora/agent_runs.py)|正式 stage 的内部调用也进入 `_run_prepared`，但有原 Executor 提供的 `formal_call` 和 `formal_execution_authorized=True`。它不是 standalone 续接授权；DeepSeek 当前也不支持该 mode。|
|[`agents.invoke`](../../src/ergora/agents.py)／[`AgentBackend`](../../src/ergora/agent_backends.py)|共有 `Invocation`、局部实现映射、原命令与结果校验。DeepSeek 仅支持 `text-only / task-mcp`，原 `native / workspace-task-mcp` 明确拒绝。不能由上层按厂商另造调用分支。|
|[`data/drivers/deepseek.py`](../../src/ergora/data/drivers/deepseek.py)|每次 `home.mkdir` 创建新 home；固定 patch 禁用工具生产者，再按 mode 插入原 task MCP。生成新 `ergora-…` ID，用 `harness.run` 发送 prompt；保存原生身份、完整 prompt、notifications 与本次 `RunResult`。没有恢复分支。|
|[`State`](../../src/ergora/state.py)|`agent_runs` 表保存所属项目与 JSON document；现有 `file_lock` 可供后续本域互斥使用。没有 native-session 表、standalone attempt ledger 或跨调用预算。无需为只读历史增加 DB 迁移。|
|[`agent_runs.output`](../../src/ergora/agent_runs.py)|按 project/run 查询原记录，只读取 stdout/stderr 的前 64 KiB；不读 `.protocol/native-home`，没有原生历史、续接或取消入口。它是 H3a 的真实 consumer。|
|[`cli.py`](../../src/ergora/cli.py)／[`web.py`](../../src/ergora/web.py)|CLI 有 `composition run-input`、`agent runs/output`。Web 的 POST `agent-runs` 只调用普通 `run_agent`，没有 composition run-input 执行入口；GET `agent-runs/{run_id}/output` 可读取共享记录。不能虚构第二个 Web 组合执行消费者。|
|[`console/agents.js`](../../src/ergora/data/console/agents.js)／[`overview.js`](../../src/ergora/data/console/overview.js)|已有“查看记录”及 `outputPanels` 消费同一 HTTP output；可以增加按需读取原生归档的控件，不需要另建会话页面、队列或全局 registry。|

普通 `run_agent` 的活动 Skill／记忆检索与组合叶的冻结上下文不同。H3a 对已有 DeepSeek standalone composition run 增加归档观察，不把普通 `agent run` 变成组合权限入口，也不把 native 历史导入项目记忆。工具可替换仍是同一模板的新调用选择 Adapter；已有 native session 不能跨厂商、跨定义版本移植。

## 2. 固定 SDK 的真实语义

### 不发 prompt 的恢复仍会写

Python [`resume_session`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py#L174) 只调用 `session/resume`，返回 `Session`；`start_session(id)` 仅构造 lazy handle，不能替代恢复。Python SDK 和 server 的 [method switch](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/src/server.ts#L499) 没有完整历史读取方法，`resume_session` 的返回值也不包含历史。`get_working_directory` 不是历史读回接口；未知 ID 的 directory 操作甚至可以创建 session。

原 [`agent-loop.resumeWith`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/agent-loop/src/index.ts#L764) 先 `persistence.open(id, 'write')` 取得写占用，读历史并追加所需的 `interruptedTurnClosers`，再构造／发布恢复的 Agent。即使历史已正常结束，[Session 构造](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/session/src/index.ts#L730)仍可追加 `session/end-seed` 标记；已以此标记结尾时不会重复追加。server 的 [setup](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/src/server.ts#L578) 调 `agent.model.select` 使用本次初始化的 route；[相同已记录选择会直接返回](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/agent/src/model-selection.ts#L112)，因此不能无条件声称恢复产生 `model/selection`。

中断修复会把“未记录开始的工具”补为 `TOOL_NOT_STARTED`，把“已记录调用但无结果的工具”补为 `TOOL_OUTCOME_UNKNOWN`，并补 step/turn 终结；它不能证明外部副作用未发生。历史原事件不会作为新 notifications 重播；新模型选择可能被通知，部分恢复／种子事件却只存在持久文件中。因而空 notification 数组既不代表无写，也不代表历史为空。

上游确有 [`readColdSessionLog`](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/session-query/session-query/src/cold-read.ts#L36)：用 persistence read handle 读全日志，仅在内存补 closers，不占写所有权、不写回。但它属于 Cordis 内部 query module，固定 Python wire 未暴露，`sdk-minimal` 也未挂载完整 query backend。为一个归档查看需求重组运行树、加载 query/SQLite 或自写 wire method，均不是本片最小接入。

### 持久 inbox 与自动派发

[`ReactLoopAgent` 构造](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/agent-loop/src/agent.ts#L140) 从持久 splice 重建 inbox 后处于 idle；初始化在 maintenance 内发布，`wakeRequested` 初值为 false，结束仅在期间有实际 wake 且仍有 pending 时启动 driver。仅恢复 pending inbox 不会自行调用 `kick`。上游 [pending inject 恢复用例](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/agent-loop/tests/resume.spec.ts#L1014) 在后续显式 `followup` 才消费旧上下文；[SDK 恢复用例](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/tests/resume.spec.ts#L175) 也核恢复后模型请求为零。

这个判断限固定 `sdk-minimal`：其 `agent-loop.agents=[]`，不含 schedule／goal／subagent 生产者；不能推广到 full SDK、reminder 或后加插件。恢复后的新 prompt 可能连带消费旧 pending 输入，必须核 inbox 状态，不能只对新 prompt 计影响范围。[`cancel`／dispose](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/agent-loop/src/agent.ts#L192) 默认还会清 inbox，关闭时也可能追加清除事件；“恢复后立刻 close”不能被定义为无写观察。

### cwd、资源与占用

恢复保留原 stored origin／effective directory，SDK 接受本次初始化使用不同 cwd；它不会替 Ergora 检查调用身份。working-directory get 对已丢目录还有回退逻辑，不能以一个查询结果替代原目录身份／存在性校验。原 `home`、原 session ID、原 cwd 和 runtime cwd 均须作为后续续接合同，不接受任意目录或隐式 relocation。

JSONL 的[原生 lease](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/session/session-persistence-jsonl/src/lease.ts#L1) 在 POSIX 使用内核 flock，持有期间第二 writer 拒绝，进程退出释放；`session.lock` 文件保留不表示仍被占用。禁止删 lock、按文件年龄强抢或超时重领。复制 home 产生的是另一 lease 路径，不能证明原 home 已空闲。

## 3. 本轮原件观察

原件位于仓库私有 `.ergora/checks/harness-real-model/{text-r2,task-r1}/state/runs/`，未把 prompt／工具正文放进本文。两个原 home 的实际 canonical 文件均为未压缩 `session.v4.jsonl`，header version=4，ID 与 `native-identity.json / native-result.json` 相同，cwd 为各自原 run `.cwd`。以下 SHA 针对完整原 session 文件原字节：

|原 run|持久事件与本次结果|完整文件身份|
|---|---|---|
|text-r2 `98f01639cd584e46901ac33ed83070e2`|13 事件，seq 0–12；本次 `native-result.events` 恰等于原文件全部事件|151,777 B；`b7926eb7e0197bb4740f538235bae0de61c2708c1baf939b66bd844de779fd23`|
|task-r1 `9906124a37754963af7ffdb1f50bcf3b`|33 事件，seq 0–32；含真实 tool/call、tool/result；本次结果也恰等于原文件全部事件|97,424 B；`f56d0a32cdd3d6b80b57c87c1508a4badb3985b4adebcab54a9909eee9133d12`|

这是新 session 的首轮巧合；一旦恢复或续接，`native-result.events` 仅属于该次 SDK owned interval，而原 JSONL 包含更早 user/tool 正文、request/header、种子／修复及以后活动。完整历史消费者必须读原 session 文件；既不能只读 assistant 最终文本，也不能丢弃“不是消息”的事件。

另一执行者的副本探针原件在 `.ergora/checks/harness-session-readback/result-r1.json` 及对应子目录。本文重新核对其 worker result、notifications 与 session 前后字节：

|场景|观察；不是产品验收|
|---|---|
|text 原 ID 恢复／task 原 ID 恢复|均成功，原字节完整保留为前缀；各新增 68 B 的 `session/end-seed`，分别 seq 13／33；新 notifications 均为空。|
|缺失 ID|`JsonRpcError`，没有创建替代 session，副本内容不变。|
|错误初始化 cwd|恢复仍成功，effective cwd 返回原历史 cwd；副本同样追加种子标记。**应用不能依赖 SDK 拒绝 cwd 不匹配。**|
|已占用 ID|第一个 runtime 恢复成功，第二个 runtime 明确 `JsonRpcError`；锁拒绝没有产生第二条原生写链。|

五 case 的 `new_prompts_submitted=0`，loopback 模型请求数组为空；11 个采样 PID/starttime 中没有存活者，服务已关闭，原两 home 逐字保持。探针使用私有复制 home、显式假 loopback route、无 MCP 的新 patch；初始化 route 的 provider/model 与历史选择相同，因此没有 `model/selection`。它证明固定恢复机制、写入及拒绝行为，不证明正式 binding／授权／task MCP 可恢复，更没有验证显式新 prompt、interrupted-tail 或 pending-inbox 的实际运行。

## 4. 必须分开的操作合同

|操作|身份与效果|对原调用／正式任务的影响|
|---|---|---|
|H3a 归档读取|原 project/run ID 找到原 home/session JSONL；零 SDK、零模型、零 native 写；返回带身份的原字节窗口|保持旧 status、结果及未知事实；不创建 run，不批准，不对账后自动重跑。|
|零新 prompt 的原生恢复|显式对原 ID `resume_session`；取写占用、补种子／修复、可能选模型／清 inbox；启动 runtime 和已配置基础设施|必须作为有写恢复活动验收和记录。它不返回完整旧历史，不等于只读 archive 或正式 task 恢复。|
|H3b 显式续接|先匹配冻结授权，再恢复同 home／session／cwd，发送明确的新输入；保存新调用及准确新增 interval|可在现有 `agent_runs` 保存一个关联 source run 的新调用 ID，旧记录／结果不覆盖；复用原调用／进程 owner，不另建 session ledger。具体字段和事务尚待该片确定。|
|新 run|按当前定义／绑定重新准入，新 run／home／session／cwd|可以替换工具或采用新资料版本；不能伪装成旧原生上下文的续接。|
|未知结果后的检查|先查原 run、完整 native 历史和进程所有者证据；SDK completed 仅是原生事实|不自动改原 outcome、不释放原占用、不重复 prompt。正式任务仍按原 task/run/attempt 对账与恢复。|

同一个 native session 后续可能有多次 Ergora 调用，但原生会话绝不是新的任务调度器。新调用 ID 是新增输入／预算／结果的归档身份；源 run、关联调用和原生事件区间沿既有 `agent_runs` 存储，不另造权威进度表。

## 5. H3a 的最小 Interface

### 只扩展原 output consumer

建议在现有 `agent_runs.output(state, project, run_id, …)` 增加显式可选的 native-history 请求（字节 `offset / limit` 与原观察 `revision`），CLI `agent output` 和原 HTTP GET output 传同样字段。默认 stdout/stderr 行为保持；只有请求历史时读原生归档。Web 可以沿已有“查看记录”按页展开，不新增组合执行入口。

已有 `AgentBackend` seam 可增加一个小的 `archived_history(protocol, *, cwd, offset, limit, revision)` Interface：默认明确 unavailable／unsupported；DeepSeek Adapter 在 `agent_backends.py` 内拥有其固定 v4 归档定位、header 和读取规则。真实生产调用者仅为 `agent_runs.output`，CLI 与 HTTP 经它共享；无需新 `session_manager.py`、registry、Protocol 层或通用恢复类。上层仍只 `for_binding(saved_binding)` 后调用共同 Interface，不判断厂商名、具体类型或另派 driver。

|预计文件|最小职责；不隐含后续功能|
|---|---|
|`agent_runs.py`|原 project/run 归属、固定原记录、原 `.protocol/.cwd` 位置；把历史请求交给原 Adapter，合并观察结果。|
|`agent_backends.py`|原生固定 v4 archive 读取的 Adapter 行为及默认 unsupported；不调用可选解释器、SDK 或 `available()`。|
|`cli.py / web.py`|已有 output 入口的可选窗口参数和原错误传播。|
|`console/agents.js`，必要时原 overview 展示处|沿原 output 展示来源、范围、下一页与不完整状态；不建立会话管理页。|
|既有 DeepSeek／composition／Web 测试与用户手册|覆盖真实读回、身份和截断风险。无需在 H3a 改 `State` schema、`Invocation`、`agents.invoke` 或 `deepseek.py`。|

### 原文件、完整历史与有限 IO

1. 先沿 DB 的 project/run 归属找到原归档。调用者只提交 run ID 与窗口，不能提交任意 home、session ID、文件名或 cwd。原 binding 决定 Adapter；当前项目 binding 不改写历史选择。
2. `native-identity.json` 也视为归档外部输入，限定读取大小。它的 `home` 必须等于该 run 固定 `.protocol/native-home`，不能跟随其中任意绝对路径。当前每 run 只有一个原生 session；可对固定 `sessions` 层级做有限目录枚举，要求唯一原 ID、唯一支持的 canonical 未压缩 v4 文件。不要复制上游所有 generation 发现／迁移算法；多代、压缩、未来格式、歧义和不支持的 ID 明确 unsupported。将来确有多 session 生产者时再由其保存准确映射。
3. header 的 version/id/cwd 必须对应原生 identity 和原 run `.cwd`；核 path containment、逐级非 symlink 目录、普通文件。当前 Linux 范围可沿目录 fd 逐级使用 `O_NOFOLLOW`，最终以 `O_RDONLY / O_NONBLOCK / O_NOFOLLOW` 打开，避免检查与打开之间换入链接。使用同一个已打开 fd 读取，检查前后 fstat 和路径仍指向该 inode。拒绝 FIFO／device／逃逸路径，避免仅做 `exists → read_text`。原目录不存在不自动重建；H3a 可以显示归档 cwd 状态，但不能据此恢复执行。
4. 按字节窗口读原 JSONL 文本，包含 header 与全部事件，允许单条 user/tool/request 记录跨页；不要逐条 `readline()` 读取任意大的记录，也不要先 `read_text/json.loads` 全文再切片。建议每页沿用 64 KiB 数量级并允许调用者选较小值；UTF-8 边界只作最多三个字节的缓冲，损坏 UTF-8 明确报错，不能 replacement 解码后声称原字节一致。不要自动跳到尾部或静默丢前页。
5. 首页返回所属 run/native ID、相对来源、固定 byte cut、总字节数、观察 revision、当前 offset／next offset、是否到 cut 末尾。后页必须带同 revision；原文件追加、替换、截短或路径漂移就拒绝继续，重新从新观察开始，避免把两次历史拼成一份。revision 可绑定 project/run、native ID、路径和 fd 的物理版本；它是本地稳定观察标识，**不冒称完整文件 SHA 或认证证明**。
6. 全文 SHA／事件数只有实际完成完整遍历才可报告。固定页大小只限制本次 IO／内存；不能为了摘要先无界扫描整 home、整文件或全部 input，再宣传有界。首片可以只返回 header 核验和原文本窗口，明确没有执行 SDK 的完整格式／surface／工具关系验证。验证程序按页重建后核完整 SHA；不用把上游 session validator 复制成第二份 Python 恢复器。
7. 运行中或重启后仍标 running 的旧记录可以提供标为 `observed-prefix / writer-unconfirmed` 的稳定文件窗口，不能宣称完整会话已停或末轮已终结。完整浏览是读到所选 cut 的全部原字节，不是证明没有外部进程，也不是把原未知结果改成成功。坏／缺尾部保持原样或显式损坏，不自动补 closers、截文件或迁移格式。

旧 `native-identity` 没有保存 cwd/runtime cwd、binding／patch／输入的全部 SHA，也没有独立封存的 native-history digest；H3a 应分别显示“保存的身份”“本次从原件核验的身份”和“未记录／未核验”，不能回填后宣称调用时已有密码学封存。原项目修订、input digest、grant／权限链、context/resource 摘要和绑定继续来自原 run；完整输入核验复用既有 `composition verify-input / inspect_input`，不在每一历史页重新实现或无界重算整个材料树。

当前项目定义／绑定发生修订不应阻止查看原归档：历史说明原来使用了什么，而不是把旧授权重新授予当前调用。项目归属始终检查；原冻结材料缺失或摘要不符要显示为证据缺口。续接则必须另行强制核对这些身份，不能把“可查看”当成“可继续”。原 history 含 user/tool／附件正文，页面只在现有受信本地项目读取范围展示，不把它送入公开 bootstrap、日志摘要或自动记忆。

## 6. H3b 仍需单独解决的合同

|合同|后续最小要求与当前缺口|
|---|---|
|授权、资料和绑定修订|显式绑定 source run、原项目修订／repo 身份、完整 input digest、结构实例 path、精确定义版本／资源摘要、grant／祖先权限、mode／policy、原 schema、原 binding／模型路由、固定 SDK/runtime/profile/patch。不能混入活动 Skill／记忆、替换叶后端或重新采用当前定义。即使缩权限，历史已保留旧资料，不能当成新范围隔离。|
|原 home／cwd／session|由原记录解析并核对，原 cwd 必须存在且身份匹配；同时核 runtime cwd。SDK 接受 wrong-cwd 已实证，应用必须在原 owner 处拒绝。不得自动创建新 home/session 或恢复到别的 cwd。现有离线 State 备份已要求同 source home 恢复；单独搬 DB 或拷 native home 不能保证可续接。|
|同一 session 的并发占用|原生 lease 防同 home 的两个 writer，但不能替代 Ergora 的“新输入意图至多一次”。后续可用现有 `file_lock` 按原 run/session 域做应用互斥，并在启动前保存唯一输入意图／attempt；具体原子写和重启对账未定。不能由锁文件存在性、超时或复制 home 判断可抢占。|
|原始事件区间与结果|恢复写入区间、prompt receipt 到 idle 的本次区间、完整历史分别保存。只接受匹配本次 prompt receipt 的原事件，不能取全历史最后一个 `completed`／assistant 文本作新结果。恢复 notifications 不重播且不覆盖全部写入，必须比较原持久 cut；原严格 JSON／schema 和 task-MCP native 审计继续适用。|
|预算|归档读取有有限 IO，不消费模型 slot。SDK request timeout 不等于整个调用预算；续接需明确新授权的 wall timeout／cleanup 与调用额度，原已花成本保留，不能重置原正式任务 deadline。SDK 内部多 step／compaction／辅助请求及 usage 覆盖仍须按实记，缺 usage 不写零；当前没有 standalone 跨轮累计严格预算，不能声称已有。|
|取消／断连／未知|沿原 `processes` owner 收尾整树；SDK 无逐 prompt cancel，`close` 不等于所有后代停止。启动、resume、已接受 prompt、关闭刷盘各窗口要实测。输入可能已接受而回执丢失时保留同意图 unknown，先读原历史／核原进程，不自动再次调用 `run`；旧 `running` 状态不靠 SDK repair 推成已完成。|
|task-MCP 的恢复|仍只提供冻结祖先／叶资源的 list/read，继承权限不变；不能由原 session history 自动再授路径。原 MCP scope／audit 绑定单次 run，续接时旧 run scope 和新调用 run ID 如何匹配、preflight 及新 audit 如何归属需独立确定。无 MCP 的副本恢复探针没有解决它。|
|任务与 approval 所属|standalone 的模型 `approve` 只是结构意见。SDK 原生 permission/question/approval 不接 Ergora 精确候选批准；本片不启用原生 approval handler。正式 task/run/候选、原 Executor、原 attempt ledger／预算／租约与任务审批、取消、恢复仍各归原 owner。先拒绝 formal_call/workspace 的 standalone 续接；如需正式恢复必须走原任务合同另片。|

长期保留应覆盖原 `.input`、`.protocol/native-home`、patch／prompt／事件／结果、MCP scope/audit 和 run record；只有 SQLite 不包含原上下文正文。现有 offline backup 可以一并保存 State 树，但跨机器 relocation、SDK 版本迁移、保留／删除策略、累计上下文容量和长期资源回收均尚未验收。不得因 JSONL 可读就承诺无限上下文、provider cache 保持或跨版本兼容。

### 为什么不通过复制 home 提供产品恢复

私有副本用于本轮有界机制实验是合适的：原 H2 证据不变，新增事件与锁可独立观察。它不是产品续接路径。header／working-directory 仍指向原绝对 cwd，session-owned 资源可能带原路径，副本 lease 不排斥原 writer；两处相同 session ID 的历史会分叉。若双方都被保存为“原 session”，就出现第二权威。

因此 H3a 直接只读原归档，无需复制。H3b 使用经核准的原 home，或将来单独设计带 lineage 的显式 fork/迁移并重做权限／资源／预算验收；不能把复制后的机制探针提升为原任务恢复，也不能把副本新历史写回旧原件冒充一次连续运行。

## 7. 可实证的首片与回归出口

以下是建议的下一实现片验收，不是本文已执行的结果：

1. 从保留的 text/task 原 run 经 CLI 和同 HTTP output 完整分页读回 v4 原文，逐字重建的字节数／SHA 等于本报告原件身份；核 user、tool、request/header 和首尾 seq，而不只核最终 assistant 文本。为多轮夹具制造“native-result 仅末轮”并确认仍能读到早期正文；不需为此再付费模型调用。
2. 原 home／history／run record 在读取前后保持；禁用模型网络并使 SDK 启动失败，读取仍可完成；无新 SDK/runtime/MCP 进程，无新 run，无状态升级。普通 stdout/stderr 与其他后端的 output 兼容；unsupported 明确可见，不能改用当前项目绑定尝试恢复。
3. 覆盖跨项目 run、被篡改 home/header ID/cwd、缺文件、多候选／未来格式、symlink／FIFO、损坏 UTF-8。对单条超过页限的正文和多字节字符逐页重建；追加、截短、rename／替换期间后页拒绝旧 revision。观察大小／读取量，不只断言 HTTP 响应小。
4. 覆盖 crashed-running／无 native-result／中断尾部：只能报告原档与 incomplete/unknown，不产生 completed、closers 或重试。当前项目修订变化仍展示原冻结身份及差异，续接保持 unsupported；`formal_execution_authorized=True` 不被当作 standalone 恢复许可。
5. 复用受影响 DeepSeek／composition／Web tests，做新 noneditable 包身份及 283 冻结检查；按实际变更运行自身模板并取得新的独立需求／可维护性评审。归档首片的通过范围只到该 consumer，不关闭实际恢复／续接、Windows native 或正式六阶段恢复。

H3b 首个可验收行为应另选一个已有 standalone 只读消费者：同一冻结输入及绑定、一次显式新 prompt、同原 native ID、独立新结果／准确事件区间，验证上下文实际带回且原 task-MCP 完整资料和拒绝行为保持；再补 prompt 接收后断连、并发拒绝、预算／取消与 unknown 重启对账。当前资料足以开始 H3a archive consumer，实现和独立验收状态仍由 [H3a 计划与交付](../delivery/2026-11-14-harness-session-readback.md)记录。
