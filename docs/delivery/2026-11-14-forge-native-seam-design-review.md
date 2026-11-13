# Forge native seam 设计复核

日期：2026-11-14。性质：单独任务的只读设计／源码复核；不是实现交付，也不是实现片的 fresh-context 独立终审。

## 结论与范围

现有 `FK_CLAUDE_BIN` 是普通 turn 的真实外部启动 seam，能够覆盖已有 reference、local campaign 的 teacher、student、judge 生成及其原生重试；它适合做固定协议的进程 Adapter。原 Forge loop、campaign、job 和候选记录继续由原 Module 所有。**目前没有证据把这条 seam 称为满足父材料、父权限、预算和停止合同的完整 C2 实现。**

当前最小可独立交付的是协调者选定的 C2.1 源身份维护片：现有调用真实执行 `scripts/`，而 `kernel._call` 只核 `src/forgekernel` 的 tracked diff。补齐这个真实消费者的身份检查有直接作用，但不增加嵌套执行能力。

完整运行的下一片应以已有 `kernel.create/operate` 为真实消费者，在可用 sandbox 的环境中消费冻结父合同并保留普通 native loop。不能将只读 file-only MCP 改名为原 teacher/student 执行，也不能新建调度器或第二权威账本。普通 WorkflowDefinition 的 opaque native 节点仍需独立 Interface 合同；现有只读 kernel proposal 不能因此自动获得写入、shell、GPU 或原生执行权。

本次固定：

- Ergora 基线 `f4da08b9ff7c1dae92222677a43d8b56b87c78b0`；开始时本仓库工作树清洁。
- Forge pin `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`；本次读取时其 checkout 工作树清洁。没有改 pin、安装、调用模型或修改 Forge／Ergora 源码。
- 选择已有 reference、普通 teacher/student/judge、local campaign；不启 `goal_ref`、tmux goal 会话、其他 backend 或升级。
- 本机 CLI 只运行 `--version`、`--help`：Claude Code `2.1.312`。其发行可执行文件 SHA256 为 `4f4178ce41d83e23341ebfbaecdbcf8ea6bf7baea0690025abe49eeec3a5d01d`。对发行文件的有限静态读取仅用于识别候选控制与请求类别，不等同运行证明或稳定公开 Interface。
- 只写本报告；不打印认证值，不代替协调者更新 PLAN，不对之后的源码改动作终审判断。

## 已核实的调用链

|实际调用|已核 seam／行为|适配含义|
|---|---|---|
|普通 student|`RealBackend.run_agent(prompt, role="student")` → `AgentPolicy.install` → notice 前缀 → `_agent_turn`|真实 prompt 经 stdin，工作目录是 native workspace；没有父 manifest、父资源或父权限参数。|
|普通 teacher|`_TeacherView.run_agent` 将 `role="teacher"` 交给相同 `RealBackend`|无需重写 teacher 调度；不能由 model 名或 prompt 猜 role。|
|judge 生成|`launch.write_judge` 构造 `RealBackend`，显式 `run_agent(..., role="teacher")`；静态检查失败后原样重试|与普通 loop 复用同一进程 seam，但需在 `prepare` 之后、正式 loop 之前就生效。内部 judge 仍不是外部独立评价。|
|失败重试|`run_agent` 在 retry loop 前安装 policy 并加 notice，每次 `_agent_turn` 启动同一 command、使用同一 prompt|Adapter 每次启动都能校验冻结合同并留请求收据。不能把一次安装误述为每个 retry 都重新安装；重试间的保护由实际 sandbox 和可信 Adapter 保证。|
|campaign 恢复|`launch.run_loop` 再次构造 teacher/student command，仍进相同 seam|必须从原 campaign 关联原父合同和剩余预算，不能从当前项目／新配方重新选择材料。|
|可选 reference 生成|`FK_AGENT_DRIVER=goal` 进入独立脚本／tmux 路径|本片明确排除；普通 stdin wrapper 的证据不能外推到 goal。|

关键源码：[Forge RealBackend](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/cli.py#L257)、[teacher view](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/driver.py#L129)、[judge](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/launch.py#L475)、[agent command](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/agents.py#L20)。

`agents.agent_command` 只支持 Claude backend，固定启动 `scripts/agent-claude.sh`。该脚本普通分支实际执行 `timeout-run.py <timeout> ${FK_CLAUDE_BIN:-claude} -p --model ... --dangerously-skip-permissions`。因此替换该二进制是已有 seam；它不是 Codex backend 切换合同，Ergora 的回退授权不能直接改变它。

## CLI 同进程路径：需要区分的请求

核心要求是所有承担任务的会话继承全部结构祖先的 instructions、context、Skill 和附件，权限取父上限与 native role policy 的交集。纯连接检查和元数据生成应按实际影响记录，不宜仅因使用模型就自动要求通用 HTTP 代理。

|类别|对任务的影响|本次证据与下一出口|
|---|---|---|
|teacher/student/judge 的主会话及后续工具轮|写代码、写 judge、决定后续搜索和评价|必须完整带父材料；仅 stdin 的普通任务文本不是固定系统材料合同。候选 Adapter 应保留原 native prompt，并在受支持 CLI 的固定系统材料通道装配全部父正文／原附件。|
|CLI 的工作 subagent|可读写代码或产出主会话采用的工作结论|`--agents` 是自定义 Agent 入口；`--tools`、`--disallowedTools` 是现成关闭候选。首个 profile 可明确不启同进程工作 subagent，但须实际验证工具表及所有别名，不能靠 prompt 禁止；仅关闭 Agent 工具也不证明 Bash 再启动其他 coding agent 已受控。|
|compact／summary 与其恢复|摘要替换后续工作上下文，可能丢失强制材料并改变后续决策|属于核心覆盖范围。发行文件中可见 `DISABLE_COMPACT`、`DISABLE_AUTO_COMPACT` 对相关逻辑的控制；这是版本相关的候选，不是已跑通保证。可先选不 compact 的有界普通 turn，并证明容量超限明确失败；若需 compact，必须核 summary 输入和恢复后的材料实际保留。|
|model validation／连接检查|本次静态读取发现 `max_tokens:1`、用户文本 `.` 的启动检查，不执行工具或编写任务产物|本身不是工作子 Agent，不因其不带全部父材料而单独推导完整 native 不可实现。需记录实际 provider/model 及其认证／网络授权；本报告没有触发它。|
|session title|生成会话标签；可消费会话内容，但静态 helper 无 tools，也未见它直接决定 native 候选|静态 helper 有独立 system，标记 `hasAppendSystemPrompt:false`。说明 append 不能自动外推到每种 helper；是否准入应核实际内容、provider/model、数据传输和标签是否被后续任务消费。不能单凭这一条强制开发代理，也不能把它冒称完整工作会话。|

本机帮助确有 `--output-format stream-json`、`--forward-subagent-text`、`--include-hook-events` 和 `--system-prompt-snapshot`。后者说明主会话可固定首次 system；其帮助同时指出 compact 后会重新处理。**事件可观察不等于每个实际请求已注入，主会话 system 固定不等于 compact summary 已带全文。**

最小 profile 宜先保留 Forge 原来的多个普通 turn，而关闭未覆盖的 CLI 内部工作 subagent／compaction。这是受限支持范围，不能把需要这些路径的运行默认为成功。不得使用 `--bare` 跳过 native policy；也不宜为清理环境而一并删除 Forge 已镜像的 Skill 工作流。CLI 参数需按选定版本验证，不能从本报告的帮助清单直接发出支持声明。

若真实工作请求仍绕过这条可控通道，先定位那个具体请求的消费和控制 seam。只有在固定 CLI/provider 协议确实需要时，才考虑 Forge Adapter 私有的 provider 请求 Adapter；它只注入固定材料、执行已核权限／deadline并留调用收据，不接管 loop、job、trial 或候选排序。不因连接检查／标题 helper 预建通用代理框架。

## 权限：现有 policy 不能被削弱

[AgentPolicy.settings](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/agent_policy.py#L240) 明确设置 `sandbox.enabled=true`、`failIfUnavailable=true`、`allowUnsandboxedCommands=false`。student 离线，禁止 reference／teacher-only 路径和自行驱动集群；teacher 可写 native repo，source teacher 可读 reference，blackbox teacher 则保留更严限制。策略在普通 turn 前写入项目 `.claude`，并镜像 Forge Skill。

这些约束在脚本附加 bypass flag 时仍依赖 deny、sandbox 和 hook 的实际实现。上游 hook 明说自己只是 tripwire；它不能识别所有间接命令、拼接 URL 或镜像。因此：

1. **可用 sandbox 是运行依赖。** sandbox 不可用必须失败；不能改成 warning／unsandboxed，也不能将同用户 current-container 的 advisory scope 宣称强制隔离。本报告没有重新运行 Linux namespace／bwrap 探针；协调者报告的当前容器历史失败仍是待解决环境限制，不能转换成源码弱化理由。
2. **parent ceiling 必须真实收窄。** native teacher 的全 repo 写范围、联网能力不是父层授权。readonly／shell=false 的 proposal 无法执行原 teacher shell、KB/probe 和 student 编辑流程；应该拒绝该组合并显式选择获准的 native 父合同。file-only MCP 有自己的只读消费者，但不能替代本片原生算法。
3. **不要用宽松合并扩大权限。** CLI/JSON 的 allowWrite 或网络 allowlist 可能以并集累加；父权限是交集，不能直接拼接 allow 列表。父只读路径、允许写目录、网络 origins、native role deny 和可信基础设施访问须有清楚的路径映射与 enforcement 证据。
4. **policy 会被 native 重新写入。** 只在 campaign 创建时写一次父 settings，下一 turn 就会失效。可信 Adapter 若在每次 CLI 启动前合成更严项目 policy，必须保留全部 native deny、sandbox、hook 与 role 事实，并保护最终 policy、父资源、Adapter 和 hook 不受 agent 修改。`--settings` 直接覆盖不是现成安全捷径；native `command_findings` 正在拒绝可见的这类覆盖。
5. **完整继承与 reference 隔离可能冲突。** 已选祖先包含禁止 student 看到的 reference 正文时，不能省略该资源，也不能放宽 reference deny。需要在准入前暴露冲突，等待显式修订父材料或选择合适组合。仅检查文件路径还不能识别已内联的 reference 正文；来源／资源声明须进入该检查。
6. **检查最终执行范围，而不只看声明。** native `_deny_paths` 会对包含 workspace 的 deny-read 路径告警并跳过，`_deny_write_paths` 也会过滤包含 workspace 的路径。父上限不能经这些 helper 被同样过滤；若父禁区覆盖工作目录，须在准入时拒绝这个组合，不能沿用 warning 后继续。

因此，同一套父 ceiling 不是保证任何合法 native task 都能运行。若保留算法所需的 shell／写范围超过父层授权，这个组合本来就不兼容；Adapter 的职责是准确实施并暴露它，而不是加权合并后继续执行。

## 最小可实行的运行设计

以下是下一实施片的具体设计建议，均未实现或运行。

1. **沿现有 manifest owner 冻结父合同。** 复用 `workflow_definitions.inspect_manifest/inspect_input` 的身份和结构祖先检查、既有资源装配及 `task_mcp` 的完整资源读取能力。冻结精确 instance、manifest／input digest、所有来源、资源字节／原附件、权限上限、绝对 deadline、task/global config 身份；不使用当前目录、URI 清单、摘要或模型自述代替正文。普通 workflow instance 当前不保存可直接编译的完整 native invocation；不能伪造一个 Agent leaf 就声称该合同已存在。
2. **现有 kernel driver 消费合同一次。** `kernel._call` 仍发给固定 `data/drivers/forge.py`，driver 仍调用一次原 `drive(run, ...)`；添加的父合同必须由此真实消费。保留 prepare/run/status、原 campaign ID、native snapshot 和未知结果对账。不要复制 teacher/student loop。
3. **在 FK_CLAUDE_BIN 放固定进程 Adapter。** 每次启动校验合同与受信 role/workspace，组合原 prompt 和固定材料，应用已证明更严的 policy，在剩余 deadline 内执行固定 CLI。普通输出仍须还原为 `run_agent` 期待的回复文本；若内部采用 stream-json 留证，不可把 JSON 事件直接交给 native parser。收据保存 role、实际 provider/model、完整材料与来源范围、最终 policy 身份、调用结果；这是关联证据，不是第二份预算／候选账本。
4. **先在有 sandbox 的受支持 profile 验证真实路径。** 完整 native teacher/student/judge，含原重试、一次原 campaign 恢复，关闭未覆盖的同进程工作 subagent／compact；材料超限明确拒绝。内联文本不足以证明任意二进制附件可用，首个 profile 必须按真实附件类型验证原始传递，或在准入时说明该类型不支持。
5. **原候选交给原评价所有者。** 保存 kernel／wrapper／report 的精确内容身份及 native judge 结果，交原独立实验评价与采用审批。不得用生成 judge 的 teacher、内部 best 或 `native_finished` 替代外部同候选正确性、性能和独立审查。

此设计把复杂度留在现有 kernel Module 与一个固定 Adapter；没有第二真实 implementation 时不立新的通用 NativeBackend／registry。删除 Adapter 后，完整材料、权限交集与协议转换复杂度会重新散落到 judge、teacher、student 的多个启动点，因此这个小 Interface 有真实 Depth 和 Locality；“只传一个路径但没有真实消费”的 wrapper 则没有。

## 预算、恢复与停止的真实缺口

- `launch.run_loop` 每次把 `task.budget.hours` 原值传给 loop；`loop.cli` 再计算 `time.time() + args.hours * 3600`。因此同 campaign 恢复保留候选／step，并不证明总 wall-clock 预算不重置。原预算上限须由现有 kernel owner 冻结绝对 deadline，prepare、重试、每次 CLI 和 job 都消费剩余时间；不能把每次 operate 的新 timeout 当总预算。
- `RealBackend` 的 outage 重试可长时间退避；单 turn 的 `timeout-run.py` 不是整个 campaign 的硬上限。仅缩短 CLI timeout 也不会约束循环中的 sleep 和 GPU job。
- [submit.jobs.spawn_runner](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/submit/jobs.py#L170) 明确 `start_new_session=True`，使 GPU runner 存活于提交进程退出之后。`timeout-run.py` 也建立自己的 session。杀外层 Ergora driver 的 process group 无法据此推导这些后代已停。
- 停止应复用 native job／runner 的原 ID、原 stop／终态出口，或已核可信进程归属原语；在证实所有所属 CLI／job 已退出之前保留 unknown。普通 `kernel.operate` 目前只有 run/status，没有完整 cancel Interface。

若用外层绝对 deadline 保住父预算，报告也应说“外层硬上限保留”，不能声称已经修改了旧 native 内部的相对 hours 语义。需要 native 自己接受同一个 deadline、给出统一停止结果时，是有具体语义的上游 Interface patch 候选，应另列 diff 与回退；不能通过 monkeypatch 隐藏改变固定 pin 的含义。

## 哪些需要新合同或上游 patch

|问题|最小归属／是否必需改上游|
|---|---|
|真实脚本没有纳入固定源身份检查|C2.1 在现有 `kernel._call`／既有测试维护；不改 Forge pin，不冻结 global_config 的可配置取值。需说明 tracked diff 对 untracked 运行时代码、解释器／CLI 的证据边界。|
|父合同传递与每次普通 turn 完整装配|Ergora kernel request/driver ＋ FK_CLAUDE_BIN 专用 Adapter；现成 seam 可做，不先改 Forge loop。|
|父权限交集|可优先验证每次可信启动时合成项目 policy＋可信执行环境；若所需强制能力无法由当前 CLI/settings／容器实施，保持该 profile unsupported，再提出具体上游或环境变更。不能把检查缺口降级成 advisory 后冒称满足。|
|同进程工作 subagent／compact|先验证版本固定的关闭方案；若需要保留，必须在真实消费点证明完整材料／权限继承，接缝不足时再提出 CLI／固定 provider 协议改动。单改 Forge prompt 不足，连接检查／标题也不自动要求代理。|
|绝对预算与停止|先用既有 kernel/process/native job 所有者实际连接；若原 stop／deadline Interface 不能表达必要终态，再为那个具体缺口设计上游 patch。|
|native 可执行子模板|现有 composition 只支持 workflow／Agent／join，当前六阶段 runtime 也不是 opaque Forge 节点。节点输入、父材料／权限、预算、原 campaign 恢复、候选输出和独立评价必须先有新显式合同；这是另一个真实消费者片，不能靠元数据宣称完成。|
|Codex 或其他 backend|固定 pin `agents.agent_command` 明确 Claude only。需要上游 backend 合同／新适配和精确验收；不属于本次回退。|

## 下一片的有效验收证据

C2.1 应用其自身小范围回归和新独立终审结案；本报告不预判代码实现通过。完整 C2 的后续运行片至少需要：

- 从真实 teacher/student/judge、重试和原 ID 恢复的原始输入收据，逐资源核完整尾部、来源、Skill 全树／原附件；主动漏传、容量超限和 reference 冲突均有明确失败。
- 在支持环境中核 student 的间接 Python 读取 reference／联网被拒、teacher 允许的 KB/probe 正常、父禁写／禁网仍拒绝，且 policy／Adapter 不可被该 turn 改写；不能以项目 JSON 正确代替实际执行效果。
- 对内部工作 subagent 和 compact 的关闭或完整继承出实际证明。若它们被关闭，超限 turn 不得静默 truncate 或转用摘要；若开启，summary 输入与恢复后的父材料都可核。
- 原 native 记录保留候选／job 账本，父绝对 deadline 跨 prepare、retry 和 resume 不重置；超时后每个所属 CLI 与 local runner 的真实终态或明确 unknown。
- 同一候选内容身份的外部 correctness／measurement／独立审查；原 native judge 不承担项目采用审批。

本次只检查源码、项目文档、CLI 帮助和发行文件的有限静态片段。未跑模型、GPU、native campaign、sandbox、cancel、恢复或附件验证；没有新增运行通过声明。工作依据是 [D2-C2](../plans/2026-11-13-specialist-presets.md#c2第一个执行适配片的准入设计)、[X2 逐会话核对](../research/2026-11-12-horizontal-kernel-agents.md#内部每个模型会话完整材料与父权限核查)、[现有 kernel owner](../../src/ergora/kernel.py)、[固定 driver](../../src/ergora/data/drivers/forge.py)、[结构祖先／完整输入 owner](../../src/ergora/workflow_definitions.py) 和 [固定资源 owner](../../src/ergora/task_mcp.py)。
