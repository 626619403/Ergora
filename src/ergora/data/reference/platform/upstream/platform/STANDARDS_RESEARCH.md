# 通用任务与 A2A：调研和架构决策

核验日期：2026-10-26。本文记录公开规范和官方实现的做法，不代表厂商内部所有工作流，也不构成跨平台实测认证。平台实际可运行范围、配置和迁移方法以 [PORTABILITY.md](PORTABILITY.md)、[A2A.md](A2A.md) 及 [VALIDATION.md](VALIDATION.md) 为准。

## 先读结论

目前没有一个被所有平台共同执行的格式，同时统一任务、模板、多 agent 拓扑、权限、审批和验证证据。可移植性应分层实现：**任务表达目标，模板描述角色与流程，策略规定边界，运行时绑定选择服务，证据证明结果，A2A 负责跨服务委托。**

采用开放协议可以减少接口适配；它不会自动统一业务输入、质量标准或权限。对端“支持 A2A”，不等于它能执行本平台的模板或满足本平台的验收要求。

## 标准采用矩阵

| 层次 | 格式或协议 | 适合承载 | 不能替代 | 本平台采用原则 |
| --- | --- | --- | --- | --- |
| 仓库说明 | [AGENTS.md](https://agents.md/) | 构建、测试、目录和编码约定 | 执行权限、状态机 | 保持简短，链接细节和可执行检查 |
| 可复用能力包 | [Agent Skills / SKILL.md](https://agentskills.io/specification) | 指令、脚本、参考资料、模板资产 | 运行器、鉴权、任务调度 | 按需加载；实际工具授权由运行环境执行 |
| 数据契约 | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | 任务输入、输出、配置的结构约束 | 业务语义、跨字段安全条件 | schema 校验后仍检查 DAG、路径、哈希和身份 |
| 工具连接 | [MCP](https://modelcontextprotocol.io/specification/2026-07-28) | 工具、资源、提示的服务接口 | 多 agent 业务流程 | 与 A2A 分工；不把工具调用等同于远程任务验收 |
| 长操作工具扩展 | [MCP Tasks](https://modelcontextprotocol.io/extensions/tasks/overview) | 工具执行的持久句柄、查询、交互 | 本地批准与任务所有权 | 先协商扩展；取消仍需确认实际副作用停止 |
| 跨服务 agent 委托 | [A2A v1.0.1](https://a2a-protocol.org/v1.0.1/specification/) | Agent Card、消息、任务状态、产物 | 内部拓扑、代码正确性、审批策略 | 保留内部领域契约，在网络边界做转换 |
| 编辑器连接 coding agent | [Agent Client Protocol](https://agentclientprotocol.com/get-started/introduction) | 编辑器或 IDE 与 agent 会话 | 多 agent 任务模板 | 作为独立执行器适配方向，不与 A2A 混称 |
| 声明式工作流 | [Open Workflow Specification](https://open-workflow-specification.org/) | 可读的工作流定义与 schema | 既有引擎自动兼容、重放语义 | 有真实跨引擎迁移需求时再实现编译器或解释器 |
| 事件信封 | [CloudEvents](https://cloudevents.io/) | 事件身份、来源、类型、时间和数据 | 消息投递保证、幂等、排序 | 按需用于外部事件总线，不额外创造状态真相源 |

“ACP”有多个历史展开方式；本文只指 Agent Client Protocol。MCP Tasks 在当前规范中是独立扩展，不能照搬旧版实验性接口而声称支持当前版本。

## 公开平台怎样划分边界

### Google ADK：保留内部模型，增加协议包装

[ADK 的暴露指南](https://adk.dev/a2a/quickstart-exposing/)使用 `to_a2a(root_agent)` 包装 agent，并生成或接收 Agent Card；[消费指南](https://adk.dev/a2a/quickstart-consuming/)通过 `RemoteA2aAgent` 调用远程服务，显式转换 A2A 消息、任务、产物和 ADK Event。

需要注意：快速上手默认创建内存 runner、session/artifact/task stores；这不是生产持久性保证。消费文档还保留 legacy 路径，示例默认 `use_legacy=True`。部署时应固定 SDK 和协议版本，依据实际依赖接口测试，不能直接拼接不同版本的示例。

可借鉴的是**边界转换层**：业务任务仍用自己的结构，A2A 只承担外部交换。

### Microsoft Agent Framework：单进程组合与跨服务通信分开

[官方边界说明](https://learn.microsoft.com/en-us/agent-framework/journey/agent-to-agent)建议同进程、同团队的组合优先使用 agent-as-tool；服务、团队或组织边界才使用 A2A。它分别提供 [A2A hosting](https://learn.microsoft.com/en-us/agent-framework/hosting/self-hosting/a2a/server) 和 [A2A agent service](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/agent-services/a2a)。

因此，不必把 inventory、plan、verify 等每一个阶段部署成网络微服务。独立部署的执行器、审查服务和其他团队的专家 agent 是更合理的第一批 A2A 边界。

### LangGraph / LangSmith：内部 graph 与远端接口并存

[Agent Server](https://docs.langchain.com/langsmith/agent-server)保留 graph、assistant、thread、run、持久化和任务队列；[RemoteGraph](https://docs.langchain.com/langsmith/use-remote-graph)提供对外部署的客户端接口。官方明确警告：不要用 RemoteGraph 调用同一部署内的 graph，否则可能死锁或耗尽资源，同部署应使用本地组合。

[A2A 端点文档](https://docs.langchain.com/langsmith/server-a2a)公布了 `/a2a/{assistant_id}` 和 v1.0 JSON-RPC 支持，也列出当前未通过的规范项，包括部分可选操作、版本头处理和错误格式。**接口存在和完全符合规范是两件事**；需要能力协商和对端实测。

### DSH / Cordis：通过服务接口隔离具体实现

[Cordis 官方说明](https://deepseek-harness.github.io/deepseek-harness/en/reference/cordis-primer)将 tools、LLM、sessions 等能力注册到稳定的 `ctx` 服务键，通过依赖注入获取服务，生命周期效果可撤销。

可借鉴稳定端口和依赖注入；无需引入整套 DSH 才能实现这一点。更换模型或 agent 执行器应主要修改绑定和适配器，不应重写任务目标、验收标准和证据协议。

### Symphony：调度、策略、执行和集成分别负责

[Symphony SPEC](https://github.com/openai/symphony/blob/main/SPEC.md)明确区分 Policy、Configuration、Coordination、Execution、Integration 和 Observability。`WORKFLOW.md` 保存仓库策略和配置，tracker adapter 规范化工作项，coding-agent adapter 负责目标 Codex app-server 协议。

这支持本平台继续保留 Symphony 的工单入口和工作区准备，将 tracker 原生字段移至绑定层。Symphony 的 `codex.command` 仍要求兼容 app-server 的进程；不能把它改成任意 A2A 客户端或 DSH 命令就宣称完成接入。

## 为什么保留 Temporal 和 Symphony

现有两者职责不同：Symphony 获取工单、准备工作区和触发；Temporal 保存长任务状态、等待审批、协调阶段和恢复。A2A 增加跨服务交换边界，并不接管这些内部责任。

本次解耦应先复用已经验证的状态机。再放入一个 LangGraph 外层循环，会多出调度、重试、取消与状态归属需要协调。将来某个专家 agent 内部确实需要动态规划或图状态，可在其独立服务内使用 LangGraph，通过 A2A 暴露结果；平台仍只认固定任务契约、运行身份和验收证据。

这不是对不同引擎速度或能力的排名；没有进行相同真实任务的 A/B 测试，不应声称某个方案能提升固定百分比效率。

## 两种“skill”不是同一种对象

**Agent Skills 的 `SKILL.md`** 是能力实现资料包：至少包含 name/description frontmatter 和 Markdown 指令，可附 scripts、references、assets。`allowed-tools` 属实验字段，不能代替真实授权。

**A2A `AgentSkill`** 是远程 Agent Card 中的能力描述：id、名称、描述、标签和输入输出媒体类型等。它供客户端发现与路由，不包含完整执行实现，也不证明远端具有这些能力。

本平台可用稳定 capability ID 将两者关联，但运行器仍需验证可用工具、身份和权限。不要把“加载了 code-review skill”当成独立审查已经完成。

## A2A 接入要固定的语义

规范以 [v1.0.1](https://a2a-protocol.org/v1.0.1/specification/) 为依据，对外接口声明协议 `1.0`。官方 Python SDK [兼容表](https://github.com/a2aproject/a2a-python#compatibility)列出 1.0 的 JSON-RPC、HTTP+JSON、gRPC 和 0.3 兼容模式；[1.2.3 发布记录](https://github.com/a2aproject/a2a-python/releases/tag/v1.2.3)是本次核验的可选固定依赖。平台采用哪个实现及其真实测试结果，以 A2A 部署说明为准。

| 问题 | 规范与集成要求 |
| --- | --- |
| 版本混用 | v1.0 使用 `SendMessage`、`GetTask`、`TASK_STATE_*`；旧 0.3 示例可能使用不同方法名、枚举和返回封装 |
| 异步提交 | `returnImmediately=true` 请求立即返回任务；默认等待终态或 input/auth 中断态 |
| 重复提交 | 规范允许但不强制 SendMessage 幂等；业务层必须按认证身份、消息 ID、不可变内容识别重复和冲突 |
| 任务身份 | A2A task/context ID、业务 task ID、Temporal workflow/run ID 分开存储，显式映射 |
| 成功 | A2A completed 表示委托范围完成；平台 REVIEW_READY 不等于已合并、已发布或已有合并授权 |
| 取消 | CancelTask 只要求尝试取消；副作用停止未确认前不得释放写入所有权 |
| 认证 | get/list/cancel 等操作都按认证调用方范围授权；taskId 或 contextId 不是访问凭证 |
| 扩展 | 自定义结构使用带版本的业务 schema 或 extension；不支持强制扩展时明确报错，不静默降级 |
| 产物 | 返回候选 SHA、输入和策略摘要、证据引用；远端文本“通过了”不能替代 CI 和独立审查 |
| 发现 | 首先使用受信端点配置和允许列表；Agent Card 是声明，不是权限授予或能力证明 |
| 可选能力 | 没有完成并验证 streaming、push、extended card 等功能，就不在卡片中宣称支持 |

生产 A2A 通信需要 TLS 和真实身份校验；服务端必须自行实施授权范围。业务包不保存 token 或账号密钥，部署绑定只记录密钥引用。不要直接请求不受信任卡片中的任意地址，也不要把外部返回内容当作新的控制指令。

## 解耦与迁移检查表

1. **保留历史格式。** 已运行的 v1/v2 请求和快照不改写；新格式通过显式转换进入已验证的执行路径。
2. **领域契约不依赖厂商。** task 不携带某个 tracker 的必填内部字段，不把 Temporal 队列、模型提供商或认证配置混入任务目标。
3. **策略独立于指令。** protected paths、审查独立性、审批和证据要求由受信配置固定；候选仓库不能自行降低门槛。
4. **固定版本与摘要。** 请求、模板、工作流、策略和运行绑定有可追溯快照；密钥值不进入快照。区分原始字节摘要与规范化 JSON 摘要。
5. **边界明确。** 网络 handler 转换和提交任务；执行器运行工具；状态机协调；证据验证器判断验收。避免各层都能修改调度状态。
6. **不宣称自动互通。** 新平台适配器必须说明支持的任务类型、协议版本、传输、取消、审批和 evidence 能力。
7. **故障先于 UI。** 验证重复消息、重启恢复、越权读取、哈希冲突、未知扩展、过期批准、晚到产物和取消未确认，再扩大并发。
8. **质量门禁不随协议改变。** 新 executor 和旧 executor 都必须通过同一候选 SHA、范围、行为、架构、回滚和独立审查检查。

本文中的开放规范提供的是互操作边界。平台自身的业务 schema、信任模型、执行器契约和测试仍是工程实现的一部分，不能对外宣称为行业统一标准。
