# AC3b.3 任务 MCP 独立审查

日期：2026-11-09。审查者：fresh-context reviewer `/root/task_mcp_review`。未继承实现会话；收到原始要求、限定切片、固定基线及实际证据后独立检查。仅写本报告及个人 `.ergora/checks/ac3b3-task-mcp/reviewer-r1/` 证据，没有修改生产或测试、安装依赖、调用托管模型、提交或推送。

## 范围与身份

基线和审查时 HEAD 均为 `8208efa36cb9c76344d10d6789702e5bcc654ade`，分支 `refactor/architecture-foundations`。审查对象是该基线上的未提交切片，精确 15 文件及 SHA256 见 [scope](../../.ergora/checks/ac3b3-task-mcp/review-r1-scope.json)，跟踪变更见 [diff](../../.ergora/checks/ac3b3-task-mcp/review-r1-tracked.diff)；五个新文件均读了全文：交付记录、研究、scope schema、`task_mcp.py` 和 `test_task_mcp.py`。其余十个文件为 portability CI、README、AGENT_BACKENDS、PLAN、WORKFLOW_DEFINITIONS、pyproject、agent_backends、agent_runs、agents、cli。前片两份 composition-invocations 状态追加不属于本次生产审查。

遵循仓库 AGENTS、maintainable-project-delivery 及其 independent-review、codebase-design；已读用户指定的共享 AIHERO 索引。以[本片合同](2026-11-09-task-mcp.md)和[第一方研究](../research/2026-11-09-task-mcp.md)核查，保留后续通用 MCP 声明、workspace 工具、批准和嵌套调度的独立出口，不要求迁入本片。

独立身份核查时，15 文件与 scope 全部一致，源码／wheel／非 editable 安装的 **362 文件逐字节一致**，冻结参考 **283 文件**符合 manifest；wheel SHA256 为 `940e967030c638ce03fe2962835e3421be77d928d1bd7cec1f95441152235f70`。完整结果和可重跑审查脚本见 [inspection.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r1/inspection.json) 与 [inspect.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r1/inspect.py)。这不是后续修正版本的身份。

## Standards

**R1 结论：已检查的所有权、接口、复用和必要控制流无阻塞 finding。**

- `workflow_definitions` 继续拥有结构链、`_materials` 去重／全部来源及 `_readable`／`_within`；`run_input` 复用完整输入重验和现有运行表。实际授权来源没有转移给模型或 MCP 配置。
- 新 `task_mcp` 模块承担冻结、内存 URI 表、官方 SDK 进程入口和连接回执，虽只有一个上层生产调用者，但具有独立进程职责和完整的资源校验算法，放在该所有者有明确局部性收益。`ResourceView` 被冻结验证和实际 server 消费；SDK 注册回调不是为凑复用增加的包装。
- 两个实际后端在原 ABC seam 各自构造原生配置。模式集合代替旧 bool 后，没有在 `agents`／`agent_runs` 按厂商增加平行分派。普通 Agent／六阶段仍取默认 `native`，独立叶子默认 `text-only`。
- descriptor、摘要、大小、分页、路径与工具清单检查对应外部资产、持久 scope 或 SDK 生命周期，均有可达条件。SDK middleware 的 `BaseModel`／dict 转换符合 2.3.0 实际 `HandlerResult` 联合类型；`ClientSession.read_timeout_seconds` 实为 `float | None`，`is_error` 的 wire alias 确为 `isError`，只读注解字段也实际核过。未把工具注解当成授权。
- 本片复用 stdio/client transport、进程树超时清理和现有 schema 验证，没有手写 MCP 协议或另建 registry。10 MB／500 文件、16 MB 序列化、64 KiB 原始读取和有界分页是数据上限，不是性能测量；未发现有证据支持的性能优化必改项，也不据合成运行耗时宣称吞吐提升。

## Spec

**R1 结论：request-changes；SP-1、SP-2 待处理。TM3／TM4 保持开放。**

### SP-1 · P1 · 原生已观察到必要 MCP 传输失效，最终成功仍覆盖该故障

位置：[task_mcp.py:229](../../src/ergora/task_mcp.py#L229)、[agent_runs.py:139](../../src/ergora/agent_runs.py#L139)，以及后端原生结果读取链。

合同要求必要服务失败不得被模型 exit 0／结构化成功替代；研究六项验收包含途中退出。当前 `verify_native` 只寻找历史上任意一个成功的精确 `tools/list`，不消费原生随后已经观察到的传输故障。

可达证据：[native-lifecycle](../../.ergora/checks/ac3b3-task-mcp/native-lifecycle.json) 在实际 Codex／Claude CLI 和官方 SDK 下，首次模型请求前 SIGKILL 已 ready 的本次 server。Codex 运行 `d284b2f4b76646e0a97456636eb629d5` 的原生 stdout 明确有四次 `Transport closed`、`result:null`，但最终合格 JSON 后仍持久化 `succeeded`／CLI 0。Claude `193fe625379b4dab9c67a8dab554fce3` 已发生 `Connection closed`，CLI 自动启动新 PID 后又成功读了三份附件，最终同样成功；不能把它写成始终缺服务，但中途传输失效确被最终成功掩盖。审查者独立核了两份 stdout／SQLite／scope／audit，当前 verifier 也确实接受这两份回执。

最小处置：由各后端所有者读取本次原生输出，区分选中 server 的传输／连接错误与正常的 server `CallToolResult(is_error=True)` 领域拒绝；前者使本次运行明确失败并持久化原始证据，后者仍允许模型修正路径后继续。对两端原生途中退出及正常拒绝后成功分别回归。不能仅要求最终 PID 活着、只看重连后的成功回执，或将所有工具错误一律判失败。若没有持续存活监控，明确记录“未观察到原生错误且无后续调用的静默失联”仍未覆盖，不声称全时连续可用保证。

### SP-2 · P2 · SDK 导入失败会遗留永久 preparing 的调用记录

位置：[task_mcp.py:206](../../src/ergora/task_mcp.py#L206)、[agent_runs.py:130](../../src/ergora/agent_runs.py#L130)。

`check_available` 仅检查顶层 `mcp` 是否存在；`probe` 的 `ClientSession`、stdio 和 `MCPError` 导入位于异常转换之外。环境中存在旧／损坏的可选 SDK、但本片所需子模块不可导入时，已建立的运行记录不能走到失败终态。

独立必要调用链在个人 state 中仅对 `mcp.shared.exceptions` 导入注入 `ModuleNotFoundError`，模拟不可用安装，没有调用模型。异常从 `run_input` 逸出；SQLite 中运行 `69e20a5d2080428293475fa28237db55` 保持 `preparing`，没有 `finished`。结果见 [inspection.json 的 sdk_import_failure](../../.ergora/checks/ac3b3-task-mcp/reviewer-r1/inspection.json)。这是导入故障注入，**不是**实际所装 2.3.0 的导入失败。

最小处置：把本片实际 SDK 导入／兼容准入放在创建运行记录前，或纳入 preflight 的可读失败转换，使已有记录进入 `failed` 并带 `finished`。继续仅支持所固定的官方版本即可，无需兼容旧 SDK 或添加 fallback。

## 已核证据与局限

- 审查者实际重跑一次官方 2.3.0 stdio 初始化、精确工具清单和只读 list，取得个人 SDK audit；核了 8 个 scope 文件、root／inner／leaf 的全部来源及 12 次读／列拒绝，没有读取兄弟或 workspace。原 8 例 native-journey 和 4 例 native-lifecycle 的 stdout、SQLite、scope SHA、audit scope 身份逐项一致；这是对既有原生运行的独立核查，未冒称独立重跑两端模型协议。
- 实现者提供的初版包检查为 **53 passed／6 skipped**，r3 另四套为 **53 passed／0 skipped**；清单不同，没有相加。常规原生八例为六次成功读取、两次实际缺 server 失败；正常两端各四次工具调用。生命周期两例 timeout 确为 `timed_out`／CLI 1，审查时相应已知 server PID 均不存在；取消链仍待新证据。
- Linux descriptor 打开不跟随资源内部链接，已知 bytes/digest 再核后进入固定内存 URI 表；运行时工具参数不会用于宿主 open。已核已有 symlink／hardlink／FIFO／inventory 后替换测试的真实范围。没有把它解释为同 UID 对手隔离、OS 沙箱或对所有目录扫描竞态的普遍保证。
- 原生 Windows 未执行该新模式；源码明确拒绝并引导 Linux／WSL2，Linux 结果不能替代 Windows 测试。真实已配置托管模型、完整 ambient 插件／外部 server 注入组合、任意外部工具 allowlist、正式批准／完整嵌套执行均未验或不属本片。
- 原研究保留调研当时的未运行项，后续实施证据在交付记录分别追加，未将研究／help／dry-run 当作协议验收。交付文档尚未宣称整片完成；修正后仍需按新源码／包身份复核、真实模型入口、自身必要 CI 和精确交付，不能继承本轮 wheel 身份。

审查过程最初一次身份命令误查仓库根 `dist/`，因 wheel 不在该目录退出；改按实际证据目录 `ac3b3-task-mcp/dist/` 后逐文件一致。该辅助命令错误未算产品失败或验收通过。

Standards：0 个阻塞 finding。Spec：2 个 finding，最严重为 SP-1／P1。本报告为 R1 初审，后续同片复核应追加，保留原问题及证据。

## R2 同片独立复核

本次继续由原独立审查者复核修正，保留以上 R1 原发现。基线不变，精确范围增为 **16 文件**，新增 AC 计划状态文件；[R2 scope](../../.ergora/checks/ac3b3-task-mcp/review-r2-scope.json) 与 [R2 diff](../../.ergora/checks/ac3b3-task-mcp/review-r2-tracked.diff) 已核。16 文件与本轮身份全部一致，源码／wheel／非 editable 安装的 362 文件一致，283 冻结身份保持；r4 wheel SHA256 为 `dbb549d67ea9694b1016f95709c50e0e67c4cddc81afb3936ae8c2c13f9f2ac2`。独立脚本、完整结果见 [R2 inspect.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r2/inspect.py)、[R2 inspection.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r2/inspection.json)。

### Standards

**R2 结论：本轮无新增结构或复用 finding。** `read_result` 接收原 `Invocation`，使两个实际 adapter 都能在本地读取所需模式／协议信息；上层继续只调共有接口。私有 `_events` 有两个实际消费者，逐行解析集中在后端所有者。Claude 仅 task-mcp 改用 stream-json，普通 native／text-only 原处理保持。SDK imports 转换只覆盖实际导入失败，没有新增全局异常吞噬或备用 SDK 实现。

额外核查了 `freeze` 的生成前总量约束：唯一生产消费者 `run_input` 在冻结前已对完整快照执行 `inspect_input`，后者的全树 `inventory_tree` 已限 **10 MB／500 文件**并复核完整身份。每个投影 URI 由已核 kind／ID／version／canonical path 得到，对应完整输入中的唯一物理文件；URI 去重后的选中集合不会扩大原始字节或文件数。不能以绕开该前提、直接传入伪造 `prepared` 的调用作为实际准入漏洞。`ResourceView` 的总量检查继续保护独立 scope 加载，不要求在 `freeze` 再加相同 guard。来源元数据及 JSON 编码仍有额外 16 MB 拒绝，未把该数据上限说成峰值内存测量；本轮没有性能优化必改项。

### Spec：原发现处置

- **SP-1 关闭。** 独立以 r4 实际原生 stdout 重跑两个后端的结果读取：两份 `server-dies` 均抛出任务 MCP transport 错误，不接受最后成功；两份 `domain-recover` 均提取与持久结果一致的结构输出。`r4-native-lifecycle` 八例和 `r4-native-journey` 八例的 CLI 文档／SQLite／scope SHA 均一致，生命周期已记录 17 个 PID 审查时均不存在。Codex 根据专用 server 原生 error 字段判断；Claude 先记录所选工具 ID，再区分原生无 server 结果的错误与 server dict 领域拒绝。未把正常资源拒绝当成传输失效。无调用静默失联限制现已明确写入手册与交付记录。
- **SP-2 关闭。** 使用与 R1 相同的 `mcp.shared.exceptions` 导入故障注入，现返回 `failed`／`finished` 和可读的重装指引，模型调用入口未执行。

### SP-3 · P2 · 新流事件解析的缺字段错误仍可遗留 running

位置：[agent_backends.py:189](../../src/ergora/agent_backends.py#L189)、[agent_backends.py:192](../../src/ergora/agent_backends.py#L192)、[agents.py:73](../../src/ergora/agents.py#L73)。

Claude 的新增 native 输出消费者直接读取 `event["message"]["content"]` 和选中 tool-use 的 `block["id"]`；缺必需字段时抛 `KeyError`，现有结构结果错误转换没有覆盖它。有效 JSON、但不符合所需流事件结构的原生输出因此不能得到失败终态。这与非法 JSON 的可读失败应遵守同一合同。

独立在完整 `run_input` 必要调用链中注入两份畸形 stdout，均带有效终结结构结果和对应 scope 的成功 `tools/list` 回执：一份 tool-use 缺 `id`，另一份 assistant message 缺 `content`。两次分别逸出 `KeyError('id')`／`KeyError('content')`，SQLite 留 `running` 且没有 `finished`，运行 ID 分别为 `fbaa9d79ae3b48bf93495fc42a3e9683`、`ba6a3d30402245338eb37fd4f3c7cd92`。这是原生输出结构故障注入，未声称当前已安装 Claude 正常输出缺这些字段，也未调用模型。

最小处置：在结果解析所有者把该结构解析错误转成现有 failed／finished 路径；不静默跳过畸形事件，不在整个 `run_input` 扩大为捕获任意异常。回归需证明这两个实际索引点的错误可读、持久终态与 CLI 一致。

### R2 证据与剩余范围

实现者 r4 非 editable 包四套为 **58 passed／6 skipped**，已读完整新增五项回归；原包的三红一绿及 SDK 导入一红保留。审查者独立核查当前 16 个既有原生案例，并通过新调用链重验原 SP-2 与新增 SP-3；没有重复计入实现者测试总数。真实托管 MCP 自审仍在途，尚未核其最终输入／回执／结果；新候选自身双 OS CI、原生 Windows 新模式及精确交付不在本轮已通过范围。

Standards：无新增 finding。Spec：原 SP-1／SP-2 关闭，新 SP-3／P2 待修正；当前仍为 request-changes，不将整片登记完成。

## R3 同片独立复核

仍按原基线检查本片。[R3 scope](../../.ergora/checks/ac3b3-task-mcp/review-r3-scope.json) 与 [R3 diff](../../.ergora/checks/ac3b3-task-mcp/review-r3-tracked.diff) 的 16 文件已核，独立检查时全部 SHA 一致；源码／wheel／安装的 362 文件一致，283 冻结身份保持。最终 r5 wheel SHA256 为 `2c4ae9de9038b1a5cf6e24322b145751deae8cb797e7e0511ed170204136480f`。新邻接 `composition-capabilities` 准备文档不在本片审查范围。个人可重跑检查与结果见 [R3 inspect.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/inspect.py)、[R3 inspection.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/inspection.json)。

### Standards

**R3 本地结论：通过，无新增 finding。**

`agents.invoke` 在既有结构结果归一化处只新增 `KeyError`，没有给 `run_input` 增加厂商分支或静默略过畸形事件。`ResourceView.load` 复用已有 `_fixed_bytes` 的 no-follow、普通文件、单链接和摘要读取；新增 limit 参数分别服务实际 10 MB 资源与 16 MB scope 两个消费者，具备真实需要，没有新建重复文件读取器。预检中断仍由原运行所有者登记取消，正常 SDK 和 native 进程继续各自负责其子进程清理。

本轮独立构造了原始内容 8 MB、JSON 序列化 **10,667,464 字节**的合法 scope，能成功加载；16,000,001 字节的 scope 被拒绝。因此复用后的读取器没有意外收紧为默认 10 MB，也保留了 scope 的真实 16 MB 限制。这里只核数据上限，没有将其当作峰值内存或性能基准。

### Spec：全部已知发现处置

- **SP-1／SP-2 保持关闭。** 原生事件处理和 SDK 导入转换未被本轮改写；本轮官方 SDK 普通 stdio 连接、工具清单和 list 再次成功。
- **SP-3 关闭。** 独立再次通过完整调用链注入缺 tool-use `id`／缺 assistant `content` 的两份 stdout，现均为 `failed`／`finished`，原始结果错误可读，SQLite 与返回文档一致。
- **真实模型的 scope 重载发现关闭。** 已读首轮真实 [codex-review.md](../../.ergora/checks/ac3b3-task-mcp/hosted-review/codex-review.md) 及有效的原包三红记录。新读取路径对 scope 的 symlink、hardlink、FIFO 均拒绝；审查者用独立子进程及 5 秒 deadline 重验三种替换，均正常返回拒绝，没有 FIFO 阻塞。正常 scope 及上述大 scope 仍可加载。
- **真实模型的预检取消发现关闭。** 独立故障注入在预检抛出 `KeyboardInterrupt`，现返回 `cancelled`／`finished`，没有进入模型调用。另核 [r5 真 SIGINT](../../.ergora/checks/ac3b3-task-mcp/r5-preflight-cancel.json)：官方 SDK 初始化子进程期间取消，CLI 1、JSON 与 SQLite 完全一致，已记录 server PID 不存在。模型建议保留 interrupt 传播；实现采用与已有 native 取消一致的终态 JSON／CLI 1，避免再次丢失回执，是有实际合同依据的处置。
- **Claude bare 认证提示建议已落实。** 后端诊断现在同时说明 task-mcp 使用 API 环境认证、不读 OAuth／keychain，保持 bare 限制；没有改全局认证或复制凭据。

首轮真实模型运行 `96f4c20a3e2a43a4aa665c00af4638dd` 的 `succeeded` 是进程／结构成功，审查决定确为 `request-changes`，未混淆两者。审查者核了 SQLite、输入与 prompt 摘要、result SHA 和 scope 内 **64,941 字节**附件 SHA `c0ce2cb38c5fce9ab3559b183a6be0cfb968455872ad0c4f8b6e979a0db15d40`，它属于修前候选，不能沿用为 r5 通过。

### R3 验证与剩余范围

实现者最终包三套 **55 passed／6 skipped**，本轮新六项回归全文已核；清单与 r4 的四套不同，不相加。审查者另执行链接／FIFO 三例、两个畸形事件、预检中断、正常官方 SDK stdio、合法大 scope／超限 scope，并核真实 SIGINT 持久终态。既有双端普通／生命周期 16 例仍保留为 r4 的真实运行，没有改称 r5 重跑。

当前 Standards／Spec 的已知阻塞 finding 均关闭，本地独立复核通过。r5 真实模型再审尚在途，其最终精确输入／连接／结果待核；当前候选自身必要 CI、普通提交推送／远端终结尚未验。原生 Windows 新模式仍明确拒绝，不把 Linux 证据或前片 CI 当作该模式 Windows 通过，也不登记整个切片完成。

### R3 真实模型再审及本地终结补核

r5 真实再审已完成，独立审查者直接核查其原始回执，结果见 [hosted.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/hosted.py) 与 [hosted.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/hosted.json)。运行 `895a622281b24406854f0fff5356bced` 由实际 Codex／`gpt-6.1-sol`、本次局部 `high` 推理配置完成，159.21 秒、CLI 0、结构决定 `approve`。运行记录保存用户授权的 Codex／ChatGPT 回退原因，没有将此记为异后端验收。

独立按当前 8 份受保护源码／schema／测试／配置和 CLI 上下文差异重建附件，**68,354 字节**全部吻合，SHA256 为 `a6f32569387a5161f8fa7982caa7b2d505dc4ae6d50060475bfc8e5e8ee59f49`。逐条解析实际 native `read` 结果，返回的原始字节、offset 和摘要均与 scope 一致；0、12,000、24,000、36,000、48,000、60,000 起点的连续分页覆盖完整附件，末页 8,354 字节且 `next_offset=null`，另有首次 65,536 字节读取。完整 stdin／protocol prompt／重验后的输入 prompt 字节及 SHA 一致；输入副本摘要、CLI JSON／SQLite、结构结果文件／摘要、实际 native receipt／scope 均一致。预检及 native 两个已记录 server PID 均已退出。

已读 [r5 模型原报告](../../.ergora/checks/ac3b3-task-mcp/r5-hosted-review/codex-review.md)：两轴没有新增阻塞发现，先前 scope、预检中断和 bare 诊断三项建议均已按上述处置落实。该模型只审所供应源码及实际 list/read，不执行测试，也没有独立检查未供应的旧模块；本次 approve 不替代本独立审查或最终 CI。

R3 后三份计划／交付文档仅追加本地终结状态，已核表述与实际证据一致，仍保留 TM4 的精确交付／自身 CI 待办。最终本地范围为原 16 文件、本报告及前片两份状态归档，共 19 文件，后片能力文档排除；本报告最终追加后需刷新其清单 SHA。

**本地终结结论：Standards 通过，Spec 通过；SP-1／SP-2／SP-3 及首轮模型发现全部关闭，范围内无新增 finding。** 后续仅待最终 Git 候选、自身必要 CI 和同片远端终结核验，不将本地结论扩大为完整远端交付。

## 精确候选对象核验

2026-11-08 20:33:34 UTC，独立检查普通候选 `ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`，其唯一父提交为原基线 `8208efa36cb9c76344d10d6789702e5bcc654ade`。实际提交差异正好 19 文件，各 Git blob 的 SHA256 与最终 scope 清单逐项一致。

直接从该固定候选 Git 对象读取全部 **362 生产文件**，与最终 r5 wheel、非 editable 安装及已记录包清单逐字节一致；**283 冻结文件**的 Git blob 与父提交均未改变。r5 wheel SHA256 仍为 `2c4ae9de9038b1a5cf6e24322b145751deae8cb797e7e0511ed170204136480f`。后片 `composition-capabilities` 文档不在候选 Git 树内。该核查使用固定提交对象，不使用随后推进其他切片的工作树替代候选身份。

检查脚本和记录见 [candidate.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/candidate.py)、[candidate.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/candidate.json)。本追加属于审查状态归档，不改变上述已执行候选；其自身 CI 和远端终结仍待具体 run／远端回执。

## 候选自身 CI 与远端独立终结

2026-11-08 20:51:32 UTC，审查者独立重新抓取官方 [run 42520599054](https://github.com/626619403/Ergora/actions/runs/42520599054)、两个 job 页面及由该 run 的 `jobGroupsFetchUrl` 取得的完整批次（`batch=0&size=200`）。run 状态为 `Success`，提交链接绑定完整候选 `ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`。完整批次 `totalCount=2`、`hasMore=false`，实际 job ID 精确等于下表两个，没有遗漏后续批次。

| 官方作业 | 必需步骤的独立结果 |
| --- | --- |
| [Ubuntu / Python 3.11，128853027038](https://github.com/626619403/Ergora/actions/runs/42520599054/job/128853027038) | `Build and install wheel`、`Packaged reference identity`、`Native application regression` 全部成功 |
| [Windows / Python 3.12，128853027108](https://github.com/626619403/Ergora/actions/runs/42520599054/job/128853027108) | 上述三步及 `Windows PowerShell 5.1 installer and upgrade` 全部成功 |

各必需 `check-step` 均为 `data-conclusion=success` 且存在 `data-job-completed`，其 `data-log-url` 精确绑定该完整候选及对应 job ID；两页均未出现失败、取消或超时步骤。原始官方页面、完整批次及其 SHA256 保存在个人证据目录，检查脚本为 [ci.py](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/ci.py)，结构结果为 [ci/result.json](../../.ergora/checks/ac3b3-task-mcp/reviewer-r3/ci/result.json)。没有使用父代理下载的页面代替独立抓取。

紧接官方 CI 校验，以既有逐命令 SSH 传输执行只读 `git ls-remote`；2026-11-08 20:51:32 UTC 返回 `refs/heads/refactor/architecture-foundations` 精确指向 `ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`。本次未修改 Git 配置、提交或推送，也未使用后片工作树替代固定候选对象。SSH 命令及凭据未输出或另存。

**最终结论：Standards 通过，Spec 通过；全部已知 finding 关闭，固定候选自身 CI 与即时远端核验完成。** Windows CI 证明既有应用回归及安装／升级路径通过；本片模式验收环境为 Linux，`task-mcp` 在原生 Windows 仍明确拒绝并引导 Linux／WSL2，不据双 OS CI 扩大已验范围。本追加为执行后审查归档，不属于上述已执行候选的 Git 树。
