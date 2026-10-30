# 三个模板的 Agent 实现选型

日期：2026-10-31。本文接续 [协作工具全景](2026-10-28-multi-agent-landscape.md) 与 [持续演进调研](2026-10-28-continuous-evolution.md)，聚焦模板的实际角色及可消费接口。官方固定提交、原始文件链接与 SHA 见 [来源清单](sources/2026-10-31-template-agents.json)。上游 README 的性能数字是上游报告，本项目未据此宣称工具排名或实测收益。

## 选择依据

治理模板需要盘点、知识导航、依赖约束、规划与独立审查；大型开发需要相同阶段下的代码实现和跨模块回归；训练模板需要实验设计、性能分析、候选生成和可信复验。适合生成候选的 Agent，不应同时拥有评分规则、计划批准和证据放行。

选择优先级为：是否有可调用接口、是否支持精确工作目录和产物、能否限定资源及处理失败、能否在已有容器中执行、许可和安装成本，最后才是任务质量。通用 coding Agent 可以承担多种角色；角色分工与进程/会话分离由 Ergora 明确记录，不把不同显示名称当作不同的隔离环境。

## 候选与结论

|实现与固定来源|适合的方向|优势|限制与依赖|本轮选择|
|---|---|---|---|---|
|[Codex](https://github.com/openai/codex/tree/0ffae14a4316d67eae25a0539e72345d0ece7118)，Apache-2.0|治理盘点/规划、开发实现、独立审查、实验提案|现有基线；CLI 支持 ephemeral 会话、schema 和结果文件；可沿用 Responses 配置|需要模型认证；CLI sandbox 依赖目标系统权限；会话分离不能替代 OS 隔离|保持默认；公共适配与正式执行桥接共用实现|
|[Claude Code](https://github.com/anthropics/claude-code/tree/d4dfed4e1c578cfea8bd6e64873e4f5e5b7e36f0)|通用开发/审查，ForgeKernel 内部 teacher/student|原生 structured_output；可关闭会话持久化和限制审查工具|该仓库许可声明指向 Anthropic 商业条款，不能误称为 Apache/MIT 的完整开源 CLI；需要自己的登录或凭据|可选适配，默认仍用 Codex；未进行账户认证或模型质量比较|
|[mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent/tree/04d809ceab9df28f9adaed044884180159172930)，2.4.6，MIT|大型开发中的 scoped implementer；治理中的小范围实施|DefaultAgent/Model/Environment 接口很小；原生轨迹、步数/时间/报告成本；模型选择灵活|Python ≥3.10；实际依赖含 LiteLLM/datasets，安装并非只有几行核心代码；默认本地 shell 有写权限，不适合作为只读审查者；单次 API 成本可能超过剩余预算|新增独立环境驱动；只声明实现角色能力；外部整体时限和进程组负责取消|
|[Aider](https://github.com/Aider-AI/aider/tree/5dc9490bb35f9729ef2c95d00a19ccd30c26339c)，Apache-2.0|仓库地图、结对修改与人工辅助|成熟 repo map、编辑/测试体验，多模型|交互和自动提交策略需要与可信提交所有者协调；结构化阶段证据要额外适配；不能把 CLI 零退出当作独立审查通过|保留人工工具或自定义协议包装；本轮不复制其编辑引擎|
|[Serena](https://github.com/oraios/serena/tree/ede329aaf0c824bea75455a2926f01420d7aa620)|治理中的符号导航、引用与语义编辑|MCP，复用 LSP/JetBrains，适合大仓库精确上下文|当前 SolidLSP 为 MIT，Serena 应用为 GPL-3.0-or-later；组合发行按 GPL；语言服务器另有依赖；它是工具，不是独立任务执行器|通过使用者自己的 MCP 客户端配置接入，不捆绑/迁入其源码；不增加另一套任务状态|
|[OpenHands SDK](https://github.com/OpenHands/software-agent-sdk/tree/c048a1eb82353b0586f3ce600708394a68ebb246)，SDK 1.59.0，MIT|后续远端执行、workspace 和对话事件|正式 Python/TS/REST API；Agent Server 与 automation 职责清楚|SDK 当前需要 Python ≥3.12，服务和依赖成本高于本轮独立 CLI；远端 workspace 的身份、取消和恢复需单独验收|保留下一后端候选；不以“有 REST API”冒充已接入|
|[ForgeKernel](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78)，0.1.0，Apache-2.0|训练优化中的 kernel 候选生成|原生任务快照、campaign、new/run/status；reference→milestone→候选→硬件知识积累；较完整的生成工作流|Python ≥3.11；固定版本的 `agents.py` **只支持 Claude backend**；执行依赖相应 GPU/PyTorch/CUDA，CuTe/NCU 按任务要求；本轮适配只支持 local delivery；内部 judge 不替代项目可信门禁|新增可选原生适配及固定安装器；CPU 计划/创建/状态可验收，真实模型和 GPU 效果单列待验收|
|[KDA](https://github.com/NVlabs/kda/tree/acdd79343c5e9d0c7cb96289f26fd3f1051ce785)|kernel 研究、实现、正确性、profile 和候选记录|工作流独立于特定 benchmark，技能与知识资产可给 coding Agent 使用；与现有人工确认流程接近|当前是早期研究工作流与提示/技能资产，不是 ForgeKernel 那样的同名 campaign 引擎；文档/技能/资产 CC-BY-4.0，源码 Apache-2.0；子模块各保留许可和额外条款|继续作为可导入的知识/Skill 和外部流程基线；不把本机的 Codex 适配冒充上游原生 Codex backend，也不复制子模块资产|
|[Optuna](https://github.com/optuna/optuna/tree/8c615f0404e4cd41dca763c6de235af7e36b75d5)，MIT|训练参数候选搜索|成熟 sampler/pruner/study 存储；可作为项目 runner 的搜索组件|不是 coding Agent，也不负责 workload 正确性、模型质量和集成批准；评价预算由项目执行者承担|由真实训练项目按需接入 runner，本轮不另写 HPO 搜索引擎|
|[ForgeTrain](https://github.com/OpenBMB/ForgeTrain/tree/3242a5cd74851a14a7e0c1ebbfb19decdafd2cde)，Apache-2.0|预训练引擎和架构生成研究|公开训练引擎和复现方向，可借鉴门禁拆分|当前 README 将配套 Harness 标为 **coming soon**；不能把已发布训练引擎视为已发布可调用 Agent；需要 PyTorch/CUDA/H100 等|调研与训练项目候选，不声称接入自治 harness|
|[Agent Lightning](https://github.com/microsoft/agent-lightning/tree/05c7fe133175653e48c990546a3509e52dc56512)，MIT|后续模型权重与 agentic RL 优化|训练与 rollout/服务职责分离，可基于已有 Agent 收集轨迹|需要开放模型、数据、奖励、训练环境和独立质量评价；不是默认 RSI 记忆/Skill 的替代|维持后续研究接入，不列入默认安装|

## 本轮实现与既有框架的分界

1. **模板不绑定厂商。** 开发模板复用原 `roles.json` 和 profile，复制时补充 `agent-contract.json`。训练模板声明实验规划、性能分析、kernel 提案及各自文本产物。项目配置决定工具；可信集成和验证不改为生成模型。
2. **共用一个调用所有者。** `agents.py` 负责能力、原生 argv 和结构输出归一化；独立 CLI/Web 调用与正式参考桥接都消费它。自定义命令用现有 JSON，显式声明 `stage-json-v1` 与角色能力，不发明另一个工作流 DSL。
3. **保持正式执行语义。** 可选执行器继承参考执行器的准备、Git、检查、审批和回执，只替换模型调用及真实 Actor 标识。新任务首次接入冻结所有角色绑定；之后修改项目配置不会改变该任务。相同 job ID 使用原监控进程和回执，不自动重复提交未知结果。
4. **生成器不拥有训练门禁。** Forge campaign 与项目绑定并记录快照/报告身份；继续操作指向原生同一 campaign。进程超时或创建结果不明保留 `outcome_unknown`，继续前需核对旧作业并记录依据。其报告不能直接转换为 perfctl PASS；候选仍须通过已有可信 runner 和独立数值/性能验证。

## 验证范围与下一步

已经直接执行固定官方 ForgeKernel `forge new ... --dry-run`，取得任务形状、reference、目标、teacher/student 和原生预算；未运行模型或 GPU。新适配的 CPU campaign、mini 原生 SDK、两种协议进程与六阶段证据验证结果在 [S8 交付记录](../delivery/2026-10-31-s8-agents.md) 持续更新。

后续推荐顺序是：在真实项目上分别运行 Codex / mini 实现对照；为 Codex 配置可用的语义代码工具；在已认证的专用 GPU 环境比较 KDA 流程与 ForgeKernel 的同 workload 结果；有远端 workspace 需求时再验收 OpenHands Server。比较应固定相同输入、可信正确性/质量合同、基线、设备、评价集、成本和停止条件，保留负结果。没有这些证据时不调整质量排名或宣称自动持续变强。
