# 工程与性能 Skill 的最小接入建议

日期：2026-11-14。本文是可移植的角色设计建议；原件身份、发现状态和路径检查归私有库存。它不证明工具已经可用、Skill 改进已生效或性能已经提高。

建议复用现有 Skill 与 AgentDefinition，不新增 Skill 注册器、优化执行器或第二套实验账本。优先补工程角色缺少的“按目标仓库确定风格”和“实际复现—缩小—回查原场景”；性能 v2 已具备测量合同，新增内容应是按证据选择工具的短路线，而非再复制一套优化流程。修改专家资料须发布新版本，沿父引用形成新根；旧定义、manifest、输入与候选证据保持原身份。

## 来源与独有用途

|来源|值得保留的指导|适用范围与接入判断|
|---|---|---|
|[AI Hero 索引与目录](https://www.aihero.dev/skills)、[mattpocock/skills](https://github.com/mattpocock/skills)|按工程任务选择资料，索引与正文分开。|索引是导航，不是应整包注入的执行流程。来源中的不同 Skill 要分别判断；修改过的副本也须单独保留身份。|
|`codebase-design`|接口包含调用者必须知道的顺序、错误、配置和性能约束；按依赖可替代性决定测试接缝。|适合结构审查与模块重构。小接口、真实调用者、deletion test 已在 Ergora 角色中；只补依赖与测试接缝的判断依据。术语服从目标项目的领域模型。|
|`code-review`|区分需求符合性与仓库规范；规范优先于通用 smell，发现需有实际维护成本。|已有三类独立审查可承接，不再嵌套另一套审查调度。应补查目标项目的规范与工具配置，不把 smell 自动判成缺陷。|
|`diagnosing-bugs`|先建立能捕获实际症状的反馈命令，再最小化；每个探针验证一个可证伪预测，修复后回查原始场景。|适合故障和性能退化；不要求所有架构讨论先制造失败。只读提案叶应向原 runner 交接复现要求和缺口，不自行执行探针或修改生产。|
|`maintainable-project-delivery`|项目自己的文档、最小完整工作片、真实复用与风险相称验证、独立审查。|Ergora 的 AGENTS、PLAN、delivery 与三类审查已承接主要流程。避免把整份协作政策装入每个专家。|
|`improve-codebase-architecture`|从近期变更和真实理解摩擦选择值得深化的模块，先列证据再讨论候选。|适合显式架构探索，不适合默认加在每次审查。HTML/CDN、临时目录、打开浏览器和交互选择属于可替换的呈现流程；报告保存位置与权限服从目标项目。|
|`disciplined-repository-engineering`|事实、推断、建议分开；同一领域概念才值得抽象；性能复杂度须有代表性负载证据。|多数已在角色和项目合同中。其个人存储规则和讨论授权方式不移植到产品；继续执行用户与目标仓库已授权的工作。|
|`linting-and-formatting`|从真实配置确定格式、静态检查、命名与类型约定。|这是 Megatron Bridge 的仓库规则。行宽、mypy strict、Google docstring、NVIDIA 版权头、rank0 日志、uv 与全仓自动修复均不能推广为通用 Python 要求。|
|[AI-Infra-Auto-Driven-SKILLS](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS)|把 trace 解释、layer 边界、可视化、serving benchmark 分开；eager 映射与正式计时分开，层锚点需匹配具体模型与 phase。|适合推理 serving 或已有 Chrome trace。现有性能 v2 已覆盖并发计时和证据缺口；增量是具体工具选择。路由器依赖包外上游布局，单独导入入口不能形成可移植 Skill。|
|[KDA](https://github.com/NVlabs/kda)|真实 workload、独立 oracle、forward/backward/JVP、wrapper 全成本和全 workload 复验。|现有 kernel 专家与 kernel 方向已承接。不同固定版本是不同知识快照，不用旧适配器覆盖当前角色。保留原 runner 与候选证据 owner。|
|[ncu-report-skill](https://github.com/DongyunZou/ncu-report-skill)|代表性输入、source/line attribution、枚举真实 metric、用数值支持原因判断。|适合选定 CUDA kernel 的资源诊断。B200 常量、双 full/source capture、目录布局和 harness 不是所有硬件/任务的要求；多流通信与 launch 空洞先看 timeline。计数器采集与真实延迟测量分开。|
|[KernelWiki](https://github.com/DongyunZou/KernelWiki)|按 Blackwell/Hopper 架构检索出处和实现先例。|是有知识截止日期的资料库，不是执行或效果证据。工具版本、PR 状态和适用硬件需在真实任务复核；不把整个第三方资料库复制进每个角色。|
|[Bridge memory snapshot Skill](https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/55694838ce73cd23b00ff95bd00512aefb963ce0/skills/nemo-mbridge-memory-snapshot-analysis)|区分 dump 时的 segments 与时间线；匹配 rank/step/allocator 后再比较，step 重放需要标记。|现有 memory-snapshot 方向已有核心限制。独有脚本能力是离线重放和差分；脚本依赖、可信输入及衍生输出路径由执行 owner 核验，不由只读提案叶运行。|
|Bridge MoE optimization workflow 与 MLM/Bridge training|固定测量合同，区分 benchmark-only 与训练等价，确认优化实际启用；训练相关性实验需匹配配置。|只对相应训练栈调用。示例训练步数、固定窗口、配方、并行参数、清理实验目录与 launcher 不是通用优化合同。当前实际代码和项目约束优先于过期示例。|

`skill-creator` 和 `writing-for-agents` 用于维护这些资料：入口只留下改变决策的条件，分支资料放入可到达的 references，检查描述和完整依赖。不同宿主的显式调用字段不能直接当作 Ergora 的调用授权。`find-skills` 可用于发现候选，但流行度不替代原件、内容、依赖和许可审查；本片不需要外部安装。

## 与现有角色的对应

现有 [`ergora-refactoring-engineer`](../../src/ergora/data/presets/agents/ergora-refactoring-engineer/skills/ergora-refactoring-engineer/SKILL.md) 和 [`ergora-structure-reviewer`](../../src/ergora/data/presets/agents/ergora-structure-reviewer/skills/ergora-structure-reviewer/SKILL.md) 已要求真实调用者、小接口、deletion test、依赖方向、原 owner 与库复用。增量应放在这两类角色的新版本中：

- 找目标仓库的 AGENTS、贡献/编码规范、formatter/linter/type-check 配置和既有变更范围；只采用对该路径实际适用的约定。工具已覆盖的风格项由工具处理，审查关注尚未覆盖的可读性、职责与语义重复。
- 区分纯进程内计算、可用本地替身的依赖、自有远端和真正外部服务，再选择能捕获真实调用模式的测试接缝。依赖注入须有实际生产或测试需求；检查点、状态与资源生命周期等真实合同仍保留覆盖。
- 用实际变更局部性、调用者承担的复杂度和可观察行为说明重构收益；不按文件长度、模块数或统一术语强推重构。

[`ergora-compatibility-validator`](../../src/ergora/data/presets/agents/ergora-compatibility-validator/skills/ergora-compatibility-validator/SKILL.md) 已覆盖实际 old/new 组合和回滚。若任务包含故障复现，可在其新版本或项目绑定资料中补“同一症状的复现命令、原失败与最小化失败、修复后原场景复验”；常规无故障验证无需额外诊断流程。

[`ergora-test-value-reviewer`](../../src/ergora/data/presets/agents/ergora-test-value-reviewer/skills/ergora-test-value-reviewer/SKILL.md) 已覆盖 silent error、配置硬编码、重复检查与测试成本。独有缺口是判断选定测试接缝是否能重现实际调用模式：例如真实缺陷需要多个调用者或状态恢复，单个纯函数的通过并未锁住该缺陷。深化模块后，先证明接口级覆盖仍保护必要行为，再移除已经失去独立价值的浅层重复测试；不把“替换测试”推广为自动删除旧覆盖。

四位优化 v2 已分别承担分析、实验设计、kernel 设计和测量审查，18 个方向又提供专门上下文。通用测量、oracle、warmup、同步、rank、重叠、预算、全链路成本与采用边界已有归属。优先给 `ergora-performance-analyst` 的新版本补一份按输入选择的短参考：

|真实输入/问题|建议路线|必须保持的边界|
|---|---|---|
|已捕获的训练 Nsight Systems 报告|既有 profiling 方向与原报告/表结构 reader。|版本、单位、窗口、rank 和依赖关系不明时保留 unknown；不把缺失事件当零成本。|
|已有推理 Chrome trace，需要 forward/layer 解释|AI-Infra 中匹配的 profiler/pipeline member。|验证模型、phase、layer cadence、rank；映射 trace 的时间不转移到正式计时。|
|给 trace 增加 layer guide/紧凑 lane|layer-track member。|保留原件；合成视图的 lane 与 layer 区间不是执行 stream 数或独占耗时。|
|选定 NVIDIA kernel 的资源瓶颈|匹配硬件的 NCU reader/metrics；架构设计再检索 KernelWiki。|工具/计数器是否可用须核实；NCU replay 可能改变多流行为，收益仍用未 profile 的匹配 workload 验收。|
|匹配的 CUDA allocator snapshots|既有 memory-snapshot 方向及相应离线脚本。|仅用可信输入，核 allocator/rank/step/标记；GPU allocator 快照不代表全部设备内存。|
|只有“变慢”的描述，没有可比较证据|先向原 runner 请求能捕获同一症状的基线/候选反馈命令和固定负载。|先记录缺口；不伪造 trace、猜硬件参数或把提案叶升级为实验执行者。|

## 可实施的下一片

建议第一片新增两个短的标准 Skill 包，先通过已有 import 显式在项目试用：

- `ergora-codebase-quality`：入口说明风格/结构/测试三条触发分支；`references/repository-style.md`、`module-design.md`、`test-seams.md` 分别保存上面的增量。服务重构、结构审查、测试价值三类角色，角色只读自己需要的分支。
- `ergora-performance-diagnosis`：入口保留真实症状/基线与原 runner 交接；`references/tool-routes.md` 保存上述输入到工具路线。服务性能分析，不重写现有实验设计、kernel 与测量采用合同。

从已固定的角色定义派生四份新 Agent 版本或显式的项目专用定义，附对应标准 Skill 的完整、固定摘要资源；原有角色资料继续保留。配两个独立的只读提案根：工程评估包含重构建议、结构审查、测试价值三叶；性能诊断引用性能分析叶。操作者沿现有显式叶调用和前驱交接操作。重构建议的指令明确输出方案与验证要求，真正编辑仍交回已授权的原六阶段工作单元。新根只由本次项目绑定/显式导入选择，不改 23 个旧 preset 的身份或默认引用。兼容性诊断按真实试用需求再加入。

这两个包只写 Ergora 自己的短指导，不复制机器存储规则、外部安装步骤或完整上游政策。若确实使用 MIT 来源的实质文本，包中保留精确来源 commit、版权与 MIT notice；来源不明的用户修订全文留在私有来源中。

先固定三个原 Agent 包及受影响根的 manifest。新增资料采用 [Agent 资源修订](../AGENT_DEFINITIONS.md#修订完整资源文件) 或完整 export/edit/check/import，发布新语义版本，再按 [完整依赖链](../WORKFLOW_DEFINITIONS.md#沿完整依赖链发布资源修订) 更新相应子工作流与新根。不要修改已经登记的相同 ID/version，也不要求无关根全部升级。

已有的 [project Skill import 与 agent run --skill](../INTEGRATIONS.md#skill-候选评价与采用) 适合明确选择的项目级试用；它与组合内精确 Agent 资源不同。单独 import 不会修改冻结模板，首次同名导入会成为初始 baseline，后续候选不会自动采用。需要正式组合完整继承时仍须走新版本及新 manifest，不能把独立 `--skill` 当作六阶段模板已接入的证明。

验收只需覆盖新增资料的真实风险：包与资源摘要可核、引用全部在允许 scope 中、旧对象及 23 个旧 preset 身份不变、新根完整继承原材料和新增参考、权限与预算不因资料增长扩大；通过真实只读调用核完整附件读取。角色行为至少核下列实际场景，保留原输入/输出和判断依据：

|角色|场景与可观察结果|
|---|---|
|重构建议|给出有真实调用者的变更范围与一种可本地替代的依赖；方案在原 owner 处收拢复杂度，解释可验证的接缝与回滚，不因文件短就拆模块，也不在只读调用中编辑。|
|结构审查|目标仓库的行宽、类型或 docstring 约定与 Bridge 不同；依目标规则评估，基于真实调用者/变更成本给发现，而非导入 NVIDIA 头或 strict mypy。|
|测试价值|给一个需要多调用者/恢复路径的缺陷及一个只覆盖局部纯函数的通过测试；识别未覆盖的实际症状并提出恰当接缝，不接受表面通过或自动删除旧合同覆盖。|
|性能分析|一例只有慢现象、一例已有但目标栈/phase 不匹配的 trace；前者返回精确反馈命令需求和缺口，后者限定适用范围并选择有依据的 reader，不编造计时或扩大工具权限。|

沿用既有包和组合检查，不为文字匹配新增测试框架。模型对这些案例的输出只能支持角色行为验收，正式性能改善仍待真实 workload 和独立评价。

## 许可与版本处理

AI Hero 来源 `mattpocock/skills` 的固定研究版本为 `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`（1.3.2），以 MIT 发布，版权属于 Matt Pocock（2026）；若复制其有实质内容的文本，随复制保留完整 MIT 版权与许可。来源固定到该 commit 不意味着用户修订文本等于该上游版本。KDA 的文档/skills/assets 与代码采用不同条款：前者 CC-BY-4.0、第一方代码 Apache-2.0，子模块另计。Bridge 来源声明 Apache-2.0；复制资源时保留原许可与出处。Nsight 工具许可与文档来源许可是不同事项。

来源没有明确许可、来源记录不足、存在用户修订或混合第三方素材时，保留来源和待核状态，优先写项目自己的短指导，不整包重新分发。固定来源版本用于追溯；本地旧副本、安装成功和公开案例都不能替代当前目标栈的适用性与实测验证。此片也不自动下载、更新或安装外部 Skill。
