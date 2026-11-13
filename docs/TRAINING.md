# 训练优化与持续改进

训练模板负责固定 workload、实验输入、正确性要求、基线和候选证据。实际训练、kernel 生成及设备访问由所选工具和项目环境完成。Ergora 的项目记忆、Skill 候选和资料观察可以先独立使用，不代表模型训练或性能已经得到改善。

专家组合的安装、只读叶准备、后端选择和开发交接可沿[三模板入门旅程](TEMPLATE_WALKTHROUGHS.md)操作；真实实验继续使用下文的可信runner及精确证据批准。

训练领域组合仍提供只读proposal叶，由操作者提供workload和前驱资料；开发任务的`work-units-v2`不会自动调度训练实验或批准候选。全部祖先Skill/上下文仍须完整交付，真实设备运行和结果采用继续按本手册的runner/gate处理。

Windows 原生可设计训练模板、普通调用提案角色并管理记忆 / Skill；带完整Skill附件的组合单叶使用Linux task-MCP，须在WSL2/Linux运行。ForgeKernel、mini 驱动及完整参考实验执行同样使用WSL2/Linux，可信参考执行器还要求Linux容器。原生安装不会配置CUDA、GPU或这些参考服务，详见[Windows手册](WINDOWS.md)。

## 准备工作

```bash
ergora templates copy training-optimization ./training-task
ergora project add my-project --repo "$HOME/projects/my-project"
```

也可在控制台“工作流设计”中选择“训练优化实验”，预览和下载文件。模板包括 `workload-contract.md`、`baseline.json`、`experiment.json`、runner 示例、hypothesis、result、evidence、attestation 和负结果记录。先将其中的占位内容替换为真实配置，再批准合同与精确实验。

固定模型 / 代码版本、数据身份、随机种子、数值精度、并行布局、设备、计时区间、重复次数及正确性阈值。训练环境与数据由项目准备；安装控制台不会安装 CUDA、PyTorch 或申请 GPU。性能候选同时满足项目正确性和质量约束后才有比较意义。

## 参考实验执行

完整参考发行提供 `agentflow training`、可信 runner 与 perfctl 门禁。按 [完整训练优化参考手册](../src/ergora/data/reference/platform/docs/TRAINING.md) 的参数执行：

```text
init / runner-add → prepare → worker-start → start
→ 选定精确实验并以 manifest SHA 执行 run-local
→ 可信证据与统计复验 → 人工批准 evidence SHA
→ 该项目的集成 / 复验任务
```

`run-local` 逐实验显式执行；没有常驻训练队列消费者。审批、结果、取消和恢复沿用原实验身份。未知结果需要对账，不直接用新 ID 重跑。候选模型或 Agent 的报告不能替代可信 runner 的验证；实验失败和负结果也要保存。

## 将实验候选交给开发任务

训练证据已按原evidence SHA获准后，在同一业务项目使用repository-governance或large-change创建集成/复验任务；先通过`project register`登记相应开发模板、路径和可信检查。按[正式任务旅程](../README.md#首个开发任务)预览、创建、提交、批准精确计划，再用原run结果核对verification/review与candidate并导出本地分支。训练批准、开发计划批准和业务合入分别保留原证据，不能互相替代。

开发集成/复验任务闭合后，可按[交接包说明](USAGE.md#收集与离线核对交接包)收集它的冻结索引及回执指定材料，供无服务环境离线核字节。该包不自动收集独立训练实验的数据、checkpoint或完整统计来源；训练证据、原批准SHA及复现实验仍按本手册保存。

`ergora task cancel/reconcile`仅处理统一创建/提交的开发任务。训练实验、Forge campaign及远端作业仍使用各自原生ID、取消和恢复协议；开发task的外部已确认不证明GPU/远端实验已停止。正式开发与训练若共享执行state，停止worker/执行栈之前先核对其全部在途作业；只关闭控制台不表示外部作业已取消。

## 记忆、Skill 与资料

- 将已核对的项目约定保存为带来源和修订的记忆；`ergora agent run --recall QUERY` 将所选项目记忆作为可核对的观察传入。
- 用标准 Skill 目录保存操作知识。手动或 GEPA 产生候选后，用固定 train / validation / holdout 评价，核对正确性、报告成本和泛化限制，再明确采用。它优化文本资产，不更新模型权重。
- 对明确的官方文档和论文来源配置有界 URL 观察；资料变化生成待审提案。Temporal Schedule 可持久触发，默认暂停，每次有独立预算。

具体 JSON 输入 / 输出、CLI、ReMe 与 GEPA 接入见 [INTEGRATIONS.md](INTEGRATIONS.md)。基础安装、控制台和备份见 [USAGE.md](USAGE.md)。

## 专用 Agent 的接入方向

模板以 `agent-contract.json` 声明 experiment-planner、performance-analyst 和 kernel-tuner 的能力与产物；具体 Agent 由项目角色绑定选择。参数搜索可由项目 runner 接 Optuna 等现成工具，可信实验执行和数值/质量/性能复验不交给生成器。

[OpenBMB/ForgeKernel](https://github.com/OpenBMB/ForgeKernel) 提供可选固定版本的原生 campaign 适配。先安装独立工具环境、配置本地任务与设备，再通过 `ergora kernel plan/prepare/status/run` 或训练页面操作。固定版本仅支持 Claude backend；计划检查与创建 campaign 不调用模型/GPU。完整配置、继续执行和结果不明时的对账步骤见 [Agent 手册](AGENT_BACKENDS.md#forgekernel-原生候选)。

生成器原生报告只作为候选材料，仍需提交候选代码、冻结实验 manifest，并运行上述可信证据门禁。KDA、ForgeKernel、mini-swe-agent 等的比较和许可证见 [三模板选型](research/2026-10-31-template-agents.md)；CPU 接口验证不能证明 GPU 性能提升。


## 可选的实验专家提案

`ergora composition install-preset training-optimization`导入实验设计、性能分析、kernel设计和测量复现审查的独立专家及子模板。根为`ergora-training-proposal`，当前版本1.0.0；[完整使用范围](WORKFLOW_DEFINITIONS.md#使用内置领域组合)说明可独立调用的只读叶子及输入准备。它们的提案和审查意见供操作者据此填写原workload/baseline/experiment，保持本手册的可信runner、独立测量和原证据摘要人工批准流程。静态图没有自动运行训练实验，模型生成代码或Forge原生完成也不构成实验采用。

显式选择新版跨域专家时安装`training-optimization-v2`，根仍为`ergora-training-proposal`、版本为`2.0.0`。四个Agent和analysis／measurement／proposal子模板均固定v2；原v1和原任务保持，可在同一库并存。根不默认挂载全部方向的工具库，各叶读取本项目短Skill及随包离线证据合同；其中的来源链接是研究出处，不表示工具已安装或模型实际联网读取过资料。

|叶路径|主要职责与所需资料|结果边界|
|---|---|---|
|`root/analysis/design`|固定workload／baseline、目标单位与质量门禁，按瓶颈选择有限动作；列组合干预、预算、停止及回退|给原runner的实验提案，不分配资源或执行搜索|
|`root/analysis/profile`|分析提供的trace／memory／rank／拓扑和数据路径，区分采集条件、关键路径与不确定性|已有报告分析与可证伪假设，不虚构新profile|
|`root/kernel`|冻结shape／stride／precision／alias／RNG／导数及真实wrapper，结合fusion／graph／memory／communication|文本或设计是candidate，未编译／未独立验证不称可用kernel|
|`root/measurement/review`|核精确候选、独立正确性／质量、配对窗口／rank／方差和总成本；区分kernel／wrapper／step或服务|有范围的审查意见，缺失／失败／no_gain／noise／unknown不改为收益，也不批准采用|

先为该精确根生成grant和完整manifest，再按[单叶调用](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子)准备一个叶输入。带Skill附件时选Linux／WSL2的`task-mcp`模式并确保实际读取完整固定资源。单次`run-input`不会执行其图前驱：操作者把design／profile的完整原产物和摘要明确交给kernel，再把全部相关输入与真实实验材料交给measurement；缺少的报告、硬件或实验数据须保持未验，不用占位数字充当实测。后端覆盖按实际叶路径保存原因，measurement优先异于执行后端；不可用时显式记录已授权的同后端回退。

跨域专家可复用于多个方向子模板，单份kernel设计也可覆盖精度、布局、融合和通信等关系。方向知识与原生执行能力分别接入；安装v2提案不等于已接入Forge／KDA内部全流程或任意外部MCP。实际实验继续使用本手册前述原manifest、可信runner、独立评价和精确evidence SHA批准。

## 独立的优化方向子模板

按任务选择下列配方，不必让每个专家加载全部方向资料。每个根的版本为1.0.0，组合共享的analysis／measurement v2及designer／analyst／measurement reviewer；三个叶路径为`root/analysis/design`、`root/analysis/profile`和`root/measurement/review`。每叶继承本方向完整context、自身Skill与全部结构祖先资料。

|安装用preset|根ID|准备的方向资料与输出|
|---|---|---|
|`optimization-memory-tuning`|`ergora-opt-memory-tuning-proposal`|最热rank与阶段的状态／激活／workspace／allocator容量分解，估算缺项、碎片假设和有限对照|
|`optimization-activation-recompute`|`ergora-opt-activation-recompute-proposal`|实际版本的selective／full层边界、RNG／数值／梯度／通信重放、图与卸载兼容性|
|`optimization-cpu-offloading`|`ergora-opt-cpu-offloading-proposal`|层级激活、细粒度激活、优化器三个机制分开；host／pinned／NUMA／传输／CPU计算和总成本|
|`optimization-cuda-graphs`|`ergora-opt-cuda-graphs-proposal`|host关键路径、实际capture／replay／optimizer范围、地址／RNG／pool寿命和setup摊销|
|`optimization-sequence-packing`|`ergora-opt-sequence-packing-proposal`|offline／in-batch／worker buffer／global-batch四路径，样本边界／MTP／loss权重／有效token与恢复|

例如选择容量诊断，先准备项目、后端、根grant及真实UTF-8任务正文，再使用原命令：

```bash
ergora composition install-preset optimization-memory-tuning
ergora composition show ergora-opt-memory-tuning-proposal 1.0.0
ergora composition prepare-manifest ergora-opt-memory-tuning-proposal 1.0.0 --grant ./grant.json --directory ./memory-manifest
ergora composition prepare-from-manifest ./memory-manifest root/analysis/design --task ./memory-task.txt --directory ./memory-design --max-prompt-bytes 100000
ergora composition check-input PROJECT_ID ./memory-design --mode task-mcp --backend codex --backend-reason "Explicit design backend"
ergora composition run-input PROJECT_ID ./memory-design --mode task-mcp --backend codex --backend-reason "Explicit design backend" --timeout 600
```

grant的`permissions`／`limits`从该精确根读取，按[完整manifest准备](WORKFLOW_DEFINITIONS.md#保存和分享完整组合)设置；若需要新增权限，先修订所有相关父级上限再修订子模板，不能用task正文越权。正文提供实际code／config／依赖版本、模型与token／batch、精度／optimizer／PEFT、mesh／rank、失败阶段与原trace／snapshot／峰值、目标与独立数值／质量门禁、允许改动、资源／时间预算及恢复要求；缺项标为未知，不填写虚构测量。

单次调用只运行所选叶。独立准备profile输入后，把design和profile的完整原产物、来源摘要及真实实验材料一起放入measurement的新任务正文。measurement默认优先异于执行后端，覆盖及回退须显式记录原因。配置能解析、估算低于容量、未OOM或有限短loss都不等于端到端性能／质量通过；资料中引用的Bridge／Core版本是知识来源，不表示这些依赖已安装，也不证明该组合适合当前运行版本。多个方向可作为普通精确引用子模板组合，但静态图不会获得自动训练执行权。

Graph提案需提供实际trace／shape分布／地址和RNG生命周期、当前编译及capture范围；capture成功与实际replay、冷启动和稳态收益分别核对。Packing提案还需数据／tokenizer身份、真实样本边界／mask／loss分母、原生路径和resume状态；按所选版本区分runtime THD与offline／in-batch限制，配置token容量不能当有效源token吞吐。缺项保留未验，由原runner和owner决定实验／采用。
