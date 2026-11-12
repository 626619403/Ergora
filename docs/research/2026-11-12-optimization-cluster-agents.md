# R8：多节点运行、故障归因与恢复

检索与源码核对日期：2026-11-12。承接[专家模板重整计划](../plans/2026-11-12-specialist-template-refresh.md)的 R8，按 Megatron Bridge Skill Reference 的 Multi-Node Slurm、Slurm Templates、Resiliency 拆分。本文研究公开源码与官方文档，没有安装执行器、申请资源、提交作业、调用模型或验证 GPU／多节点恢复。公开 HTTP 原件、获取回执、四项目 Git HEAD 观察和固定 NVRx 源码归档保存在私有研究目录；404 原件保持。

## 选型结论

**执行、诊断与恢复决策应分开。** 首先复用已有集群入口，适配 Slurm／NeMo Run 的提交、观察、停止与原 ID 对账；其次接只读归因。已有训练栈需要容错时，由 NVRx／框架拥有 rank 协调、checkpoint 和 allocation 内重启，Ergora 拥有外层预算、任务证据与采用决定。不能让 Temporal、集群调度器和 LLM 同时盲目重提同一作业。[NeMo Run 实现][run-experiment]；[NVRx 归因架构][nvrx-architecture]。

本轮核到了真正的 **NVRx Restart Agent**：实验性分布式训练日志分析流程，具备确定性证据、同作业历史比较、可选模型丰富和 STOP／RESTART 建议，以及 CLI／库／MCP 入口。它比“把 Slurm 文档交给通用 agent”更具体，但也不是可任意修机器、调集群的自治运维者；启动／停止和重启预算仍由调用者／`ft_launcher`执行。[官方说明][restart-doc]；[真实 MCP 模块][restart-mcp]。

SkyPilot 的公开 Managed Jobs 是可选资源执行与恢复后端；其 Agent Sessions 官方文章明确为 **limited early access**。不能因为开源 README 宣传该功能，就宣布公开源码／安装包已提供完整可接入会话产品。可借鉴持久 devspace、逐 agent worktree、等待审批显示和重连体验，执行适配与会话体验分别验收。[恢复实现][sky-recovery]；[官方文章][sky-sessions]。

## 候选、形态和版本

|候选|本轮核定身份／许可|实际形态与能力|采用判断|
|---|---|---|---|
|Megatron Bridge|`55694838ce73cd23b00ff95bd00512aefb963ce0`；Apache-2.0|Slurm／resiliency Skill、配置和框架集成；不是独立运维 agent|**适配知识与框架合同**，纠正文档漂移；不要整包替代外层运行所有者。[Slurm Skill][bridge-slurm]／[resiliency][bridge-resiliency]|
|NeMo Run|`5f39d666bfdf9efca07d274722f7d84a41532a2e`，源码版本 0.13.0，Python≥3.10；Apache-2.0|任务／executor 分离；Experiment、依赖、身份、日志、status／cancel；有自己的实验管理|**已有 Bridge／NeMo workload 优先条件适配** executor；不复制整个第二控制面。[版本][run-version]／[配置][run-pyproject]／[许可][run-license]|
|Submitit|`d1fd7ac4f357a2c1ac4d5c9d025147617513224a`，Python≥3.11；MIT|Python callable 的 Slurm 提交、Job 对象和 checkpoint／requeue 钩子|**轻量 Python workload 可选**；不为接一个 agent 强制迁移训练入口。[项目][submitit]／[依赖][submitit-pyproject]／[许可][submitit-license]|
|NVIDIA Resiliency Extension|`be12a1e3af7eee550abd28a67f85928ef7a9d3ab`；Apache-2.0|FT launcher、checkpoint／straggler 工具；另有实验性 Restart Agent 和 packaged attribution MCP|**先只读归因，后按框架条件接容错**；必须区分包内接口、源码专用旧接口与设计稿。[项目][nvrx]／[许可][nvrx-license]／[依赖][nvrx-pyproject]|
|SkyPilot|`b7508c38f36c93a9fd812e443d6d1d4df8201050`；Apache-2.0|资源执行、Managed Jobs 和原生恢复控制；Agent Sessions 的公开可用性另核|**可选资源后端，暂不设默认依赖**；不把 early access 产品当可复用开源模块。[项目][sky]／[许可][sky-license]／[恢复源码][sky-recovery]|
|Slurm|官方当前 REST quickstart 标示 26.05；站点文档观察|现有集群调度与受认证 REST／CLI，不是可在普通 home 安装后自行获得的集群|**复用站点入口**；普通用户无需自行部署 `slurmrestd`，也不从包安装成功推导账号／配额可用。[REST][slurm-rest]／[sbatch][slurm-sbatch]|

NVRx README 的实际支持矩阵比 pyproject 最低依赖更窄：Ubuntu 22.04／24.04、x86_64／arm64、release wheels／CI Python 3.12／3.14、PyTorch≥2.8、CUDA≥12.8、NVML driver≥535（GPU health check 为570）、TE≥2.5。最低依赖不是全部测试组合的证明；Bridge、NVRx 和模型栈要作为成套固定环境核对。[NVRx 平台表][nvrx]。其他方向的 Python／Core／TE 配套见[R4](2026-11-12-optimization-parallelism-agents.md)、[R9](2026-11-12-optimization-model-recipe-agents.md)。

## 多节点提交与控制的真实边界

### Slurm Templates：先确定唯一的 rank 生成所有者

同一固定提交的主 Skill 与复制模板不能直接拼接：主 Skill 对经过 Bridge `initialize.py`的入口优先要求 **srun-native**，由 Slurm 每节点启动与训练进程数相同的 tasks，直接运行 Python；其 legacy torchrun 路径则每节点只启动一个 launcher，由 launcher 生成本节点训练进程。[主 Skill][bridge-slurm]。但被它引用的 `references/templates.md`仍以每节点1 task为完整模板，其 Bridge-Specific body也仍用`torch.distributed.run`；这不是所有 Bridge 入口统一支持的最新启动合同。[固定复制模板][bridge-slurm-templates]。

适配按实际调用链选择一种形态。设节点数为 N、每节点训练进程为 R：srun-native 的总 tasks 为 N×R，不再套第二个 torchrun；legacy 模式为 N 个 launchers，各生成 R 个训练进程。不能把示例的8固定成用户配置，也不能同时设置 R tasks和每 task再生成 R processes。后续静态验收要核唯一的rank生成所有者、nodes／tasks／launcher与world size关系、实际入口的rank初始化；这些只证明生成的配置一致，全rank启动仍待集群验收。[主 Skill][bridge-slurm]。

repo、data、logs、`HF_HOME`、`UV_CACHE_DIR`和`NEMO_HOME`须在所有节点可见，容器内外路径／挂载一致；两阶段示例先以一个进程预热共享cache，再启动训练。普通用户复用站点已配置的容器／共享存储能力，不从模板推导可以自行mount。模板中的固定输出清理、在线`uv sync`和`wandb login`也不是每次训练必需操作；生成器应使用候选限定目录、已核环境与外部凭据引用，不把原示例逐字执行。[主 Skill][bridge-slurm]；[复制模板][bridge-slurm-templates]。

### NeMo Run：使用原生实验身份

NeMo Run 把可调用任务与 Local／Slurm 等 executor 分开；`Experiment.add(..., dependencies=...)`保存任务依赖，`Experiment.from_id(...)`恢复已有实验入口，status／logs／cancel 使用原身份。正式适配应保存 experiment ID、原生 job ID、任务名、resolved executor、镜像／环境与提交文件摘要；请求超时后先查询这些身份，不直接创建第二个 Experiment。[管理指南][run-management]；[实现][run-experiment]。

并非所有 executor 拥有同样的生命周期：源码的 `Experiment.status`明确说 local executor 不支持完整 status，detach 也按实际 executor 支持集合降级；DAG 在不同 executor 上可能由常驻 Python 进程顺序驱动，或映射为 Slurm 原生依赖。不能只验证 LocalExecutor 就宣布远程脱离、依赖、恢复均已实现。[执行指南][run-execution]；[run／DAG／status 源码][run-experiment]。将整个 Experiment DAG 嵌在 Ergora 外层会形成两个编排所有者，首选只暴露所选真实 workload 的执行与观察接口；必须保留原生 DAG 时，作为一个完整子流程管理其内部状态。

### Submitit：重排队不等于恢复模型

真实 callable 可定义 `__submitit_checkpoint__`并返回 `DelayedSubmission`；没有该方法，preemption 后从头执行，达到 time limit 时失败。多任务作业只有第一个 task 调用 checkpoint hook，不能假设所有 rank 都自动保存了模型。Slurm preemption signal 还依赖站点 `preempt_send_user_signal`配置。[官方 checkpoint 说明][submitit-checkpoint]。

所以需区分“调度器重新执行入口”“用户 callable 恢复序列化状态”和“框架恢复 optimizer／RNG／sampler／所有 rank checkpoint”。`submitit.helpers.FunctionSequence`可以避免重做已完成 callable，但不能替代分布式训练一致性。原生 local requeue 测试方式存在，本轮未运行；未来 CPU 可先验入口身份与重排队，GPU 训练恢复必须另验。[同上][submitit-checkpoint]。

### Slurm：用户能力以站点授权为准

`sbatch --parsable`用于取得原生作业标识；成功提交不等于训练完成。`--requeue`使 batch script 从开头重新开始，`afterok`等依赖依据调度器终态，失败依赖即使前驱随后重排队也不会自动变成成功。模型恢复点、应用 verdict 和产物完整性要单独记录。[sbatch 官方文档][slurm-sbatch]。

REST 入口需要站点启用的认证／插件与受支持版本；官方示例 JWT 默认30分钟过期。仅有 Linux 用户或安装 CLI 不会获得该入口，部署 daemon 的管理员步骤也不属于普通任务执行器职责。凭据保留外部引用和到期状态；不把 token 放入模板或公开证据。[REST quickstart][slurm-rest]。

## NVRx：训练恢复与归因流程分开接入

### 框架容错与 checkpoint

Bridge 文档把 fault tolerance 标为 Slurm-only，并要求 `ft_launcher`与可访问 checkpoint；另有 straggler、async／local checkpoint 和 preemption。Skill 又示例了 non-Slurm `GROUP_RANK`直启，两者不能合并成已经验证的任意调度器支持矩阵。首个适配按 Bridge 文档的保守范围，非 Slurm 路径须读完整启动链并另验。[Bridge 说明][bridge-resiliency]；[Skill][bridge-resiliency-skill]。

**不要按旧 Skill 新建 in-process restart 集成。** 固定 Bridge 文档已明确 NVRx v0.6 弃用该功能、v0.7 后上游 main 删除；新部署建议 `ft_launcher`的 in-job restart。旧框架配置仍存在不等于最新 NVRx 提供对应模块。文档还说明 FT 与 Nsight profiling 不兼容、NVRx 与 legacy MCore straggler detector 不应同时启用；诊断分支与容错分支不能无条件叠加。[Bridge 说明][bridge-resiliency]。

Async checkpoint 的 enqueue／训练继续，不是 checkpoint 已持久化；local checkpoint 的 node-local 副本也不是任意节点故障下仍可恢复。评价必须核最终提交标记、共享／本地持久层、replication、所有 rank 的一致性和真实恢复后的下一步。原生 NVRx DDP／Megatron 示例分别包含 section timeout、checkpoint 与故障注入路径，可作为后续硬件验收依据；本轮只读未执行。[DDP 示例][nvrx-ddp]；[Megatron 示例][nvrx-megatron]。

### Restart Agent：可借鉴的确定性政策与模型分工

官方已实现的流程为：日志→L0 确定性证据→同 job history／retry policy→先发布确定性 recommendation→可选 LLM／tool stage 丰富当前日志证据→确定性政策给最终 STOP／RESTART。整个分析有 deadline，迟到模型结果不能修改已关闭 attempt。`RestartAgentRuntime`默认 bounded in-memory history 为每 exact job 10 attempts、总共3,000记录，可配置；CLI fixture 的导入／导出不是自动持久历史。[官方接口说明][restart-doc]。

实际 CLI 为 `python -m nvidia_resiliency_ext.attribution.restart_agent.cli`，支持 `--disable-l1`的确定性分析、`--result-json`、`--trace-json`及配置 route。源码的 CLI 成功路径 `return 0`意味着分析完成，**不意味着训练可安全恢复**；应读取 result 的 decision、evidence／policy provenance、native job／cycle 和 degraded 状态。[CLI 源码][restart-cli]。官方说明指出空日志会产生 degraded、偏向 restart 的结果，因此外层不能把缺证据等同于准许重启。[接口说明][restart-doc]。

Packaged MCP 默认注册 `restart_agent`和 `fr_analyzer`；旧 `log_analyzer`、`log_analyzer_progressive_start`、`log_fr_analyzer`属于 source-checkout-only legacy LogSage，需显式另装依赖。`RestartAgentMCPModule.run`构造 request、调用真实分析器、返回 `result`与`recommendation`，没有在这个模块里执行作业重启。MCP 只是 transport，不能借此越过调用者的路径权限或启动权限。[MCP 说明][nvrx-mcp]；[模块实现][restart-mcp]。

**Ergora 建议：**先按固定日志副本接只读诊断子模板，保存 log digest、job／cycle、确定性与模型结果、deadline 和原始证据；保留 native attempt 语义。将诊断建议提交原恢复所有者，并由原预算／授权合同决定是否行动。若后续接 NVRx attrsvc／`ft_launcher`，不再复制其 rank monitor、in-job restart 或历史政策；Ergora 只绑定外层 native run 和候选。NVRx 根架构文档同时有“已实现”与“proposed controller”段落，不能将设计稿全部算作现成功能。[架构说明][nvrx-architecture]。

模型 route、日志范围和外发许可仍需单独配置；在本地运行分析器不会自动保证所读训练数据不离开网络。MCP schema 的 `log_path`／read 描述也不提供 OS sandbox。

**含内部模型的完整流程尚未满足模板准入。** 当前`RestartAgentRequest`只有日志、job／cycle等字段，MCP模块据此构造请求，L1使用其自己的prompt与model routes；本轮没有核到把Ergora完整父资源和grant自动传入这些内部会话的成熟Interface。[request类型][restart-models]；[MCP实现][restart-mcp]；[L1 prompt][restart-prompts]。因此首个只读工具适配可选`--disable-l1`的deterministic-only分析；要接带模型的完整子流程，D1必须逐实际route／session注入全部固定祖先instructions／context／Skill及附件入口，保存真实发送输入和读取证据，按全部父权限限制工具／路径／网络／外发，并将内部重试与模型用量纳入原任务总预算。仅传manifest路径、Skill名称或摘要不合格，容量超限拒绝。无法传递和核验时，该完整子流程继续unsupported；保留原内部分析、历史与政策所有者，不能用外层叶准入代替内层准入。

## SkyPilot：原生恢复可选，会话产品另核

固定 Managed Jobs 源码确有 launch／recover、控制器重启后的状态对账、原 request／cluster 采用、取消与退避、用户错误重启预算。应把它作为一个拥有内部资源与恢复控制的原生 executor；不能把外层超时映射成全新 `sky jobs launch`。如果使用它的自动恢复，外层记录 native job／task 与实际 attempt，而不是并行再实现相同的重试循环。[固定实现][sky-recovery]。

官方2026-09-01 Agent Sessions 文章描述 Kubernetes persistent／pausable devspace、逐 session Git worktree、CLI／browser fleet、等待审批、重连和 CPU→GPU 切换，同时明确 limited early access。本轮没有核到可独立安装、与当前固定 OSS 源码完全对应的会话交付合同，因此只进入会话体验参考项；不能称已接入的开源 agent 管理后端。[官方文章][sky-sessions]。其安装 Skill 文档还存在 `.agents/.skills`与`.agents/skills`路径不一致，不能照抄为本产品安装器。[固定 INSTALL][sky-agent-install]。

## 最小方向子模板与验收

|职责|输入／输出及所有者|
|---|---|
|资源与运行计划|固定 workload／代码／镜像、nodes／ranks／GPU、互连、CPU／RAM、checkpoint 存储、账户／分区／time limit、全节点共享路径和相同容器映射；输出受支持操作、唯一rank生成者的resolved launch和预算。无权限则输出可执行交接文件，不伪造已提交。|
|作业执行与观察|原生 executor 管 submit／status／logs／cancel；保存提交收据及 job／task／cycle ID。lost acknowledgment／API 故障记 unknown，先按原 ID 对账。|
|诊断／归因|读取固定日志、Flight Recorder／straggler／checkpoint 证据；输出根因假设、证据范围、置信与可证伪检查。对 STOP／RESTART 的建议不直接升级权限。|
|恢复执行|框架／`ft_launcher`拥有 rank 协调与 in-job restart；集群拥有 allocation requeue／replacement；Ergora 原任务所有者控制外层采用与总预算。三种 attempt 分开编号。|
|独立评价|核故障是否真的发生、所有 rank 是否前进／退出、checkpoint 是否完整、数据／RNG／optimizer 是否恢复、是否丢重训练工作；统计故障前后 useful work／wall time 和总资源成本。|

父资源／权限／预算是上述全部职责的准入条件：有内部模型时逐会话核完整继承，有外部执行时核实际受支持操作；未知内部会话、无法施加的父上限或完整材料超容量均拒绝对应模式。不同模型route不新增行动授权，内部重试和原生恢复不能另领一份外层总预算。只有已核的deterministic工具路径时，准确展示该范围，不声称整个模型流程已接入。

后续验收分级：① CPU／离线固定日志与原生结果 schema；② 有权限集群的提交／原 ID 观察／取消与失联对账；③ 可用 GPU 上 checkpoint／故障注入／全 rank 退出与恢复下一步。只有①时不能关闭②③。故障注入必须作用于本次验收拥有的作业，不能干预其他业务；未提供集群就保留明确未验范围。

和其他方向的交接：R7 提供 trace／日志测量，R3／R4 解释通信／拓扑与 rank 分组，R5／R6核 checkpoint／graph／内存交互，R9核训练数值与数据恢复。横向 X3再研究归因、预算和独立评价的跨域协调，R8不另造全局调度器。当前 training preset 仍是只读提案组合，本研究没有改变产品运行能力。

[bridge-slurm]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-multi-node-slurm/SKILL.md
[bridge-slurm-templates]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-multi-node-slurm/references/templates.md
[bridge-resiliency-skill]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-resiliency/SKILL.md
[bridge-resiliency]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/55694838ce73cd23b00ff95bd00512aefb963ce0/docs/training/resiliency.md
[run-experiment]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/nemo_run/run/experiment.py
[run-version]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/nemo_run/package_info.py
[run-pyproject]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/pyproject.toml
[run-license]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/LICENSE
[run-management]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/docs/guides/management.md
[run-execution]: https://github.com/NVIDIA-NeMo/Run/blob/5f39d666bfdf9efca07d274722f7d84a41532a2e/docs/guides/execution.md
[submitit]: https://github.com/facebookincubator/submitit/blob/d1fd7ac4f357a2c1ac4d5c9d025147617513224a/README.md
[submitit-pyproject]: https://github.com/facebookincubator/submitit/blob/d1fd7ac4f357a2c1ac4d5c9d025147617513224a/pyproject.toml
[submitit-license]: https://github.com/facebookincubator/submitit/blob/d1fd7ac4f357a2c1ac4d5c9d025147617513224a/LICENSE
[submitit-checkpoint]: https://github.com/facebookincubator/submitit/blob/d1fd7ac4f357a2c1ac4d5c9d025147617513224a/docs/checkpointing.md
[nvrx]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/README.md
[nvrx-license]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/LICENSE.txt
[nvrx-pyproject]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/pyproject.toml
[nvrx-architecture]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/ARCHITECTURE.md
[nvrx-ddp]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/docs/source/fault_tolerance/examples/train_ddp_sections.rst
[nvrx-megatron]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/docs/source/fault_tolerance/examples/megatron_gpt.rst
[restart-doc]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/docs/source/attribution/features/restart-agent.rst
[restart-cli]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/cli.py
[restart-mcp]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/mcp_integration/module_definitions.py
[restart-models]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/models.py
[restart-prompts]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/restart_agent/l1/prompts.py
[nvrx-mcp]: https://github.com/NVIDIA/nvidia-resiliency-ext/blob/be12a1e3af7eee550abd28a67f85928ef7a9d3ab/src/nvidia_resiliency_ext/attribution/mcp_integration/README.md
[sky]: https://github.com/skypilot-org/skypilot/blob/b7508c38f36c93a9fd812e443d6d1d4df8201050/README.md
[sky-license]: https://github.com/skypilot-org/skypilot/blob/b7508c38f36c93a9fd812e443d6d1d4df8201050/LICENSE
[sky-recovery]: https://github.com/skypilot-org/skypilot/blob/b7508c38f36c93a9fd812e443d6d1d4df8201050/sky/jobs/recovery_strategy.py
[sky-sessions]: https://skypilot.ai/blog/agent-sessions/
[sky-agent-install]: https://github.com/skypilot-org/skypilot/blob/b7508c38f36c93a9fd812e443d6d1d4df8201050/agent/INSTALL.md
[slurm-rest]: https://slurm.schedmd.com/rest_quickstart.html
[slurm-sbatch]: https://slurm.schedmd.com/sbatch.html
