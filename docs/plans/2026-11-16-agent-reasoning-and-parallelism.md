# 逐 Agent 推理设置与并行能力核对

2026-11-16。用户要求核对并补齐各 Agent 的思考强度选择与流程图并行执行。准确基线为 `eba86805e5d50824eefb5e69edd0faab099cbf42`；源码在独立 `agent-reasoning-options` worktree 实施，不与设计登记及训练服务片混写。

## 已观察的能力与缺项

- 原 `reference_workflows`／Temporal 拥有正式 review 与 work-unit DAG 调度，独立叶子有各自的后端绑定；项目与所有祖先 concurrency 配额同时有效。原 `tests/test_parallel_reviews.py` 已有实际等待／释放／峰值与窄子树测试。
- 原 `agent_backends.CodexBackend._options` 能读取外部 TOML 的 `model_reasoning_effort`，但 `data/components.json` 中 Codex／Claude 的公开 binding 没有对应字段，定义和表单均不能逐叶选择。
- 独立 `composition run-input` 只调用一个显式叶子，不执行整个图；通用混合图、硬性脚本／人类节点和一般 Repeat 继续沿原实施计划，不借此宣称已完成。

## 本片实现合同

在原组件配置中增加 Codex `reasoning_effort` 和 Claude Code `effort` 可选项，由各后端适配器投影到自己的原生命令。缺省不增加参数，保持已有配置和已冻结记录；显式 Codex binding 覆盖外部推理配置。不同后端的同名等级不承诺相同计算量，也不自动改变模型或降低请求强度。模型／账户／CLI 的真实支持由原生后端决定；原日志保留请求与结果，配置校验不冒称已测实际应用强度。

原 binding 表单根据组件 schema 渲染选择器；Agent 定义、工作流编译、正式冻结和原 invocation 继续保存完整 binding，不新增转换层、状态表、scheduler 或全局默认。不改已发布 preset 包或参考原件。其他后端不接收未实现的推理字段。

参数依据：已获取 [Codex configuration reference](https://developers.openai.com/codex/config-reference/)、[Claude CLI reference](https://code.claude.com/docs/en/cli-reference) 和 [Claude model configuration](https://code.claude.com/docs/en/model-config)。Codex 等级随模型／客户端变化；Claude 文档还明确组织 cap 可由 CLI 限低实际等级，JSON 模式警告可能只进 debug log，因此本片只保证传入明确请求，不能保证服务实际使用同等级。原网页、原生 `--help` 和版本只读检查在私有 `.ergora/checks/agent-reasoning-options/` 保存；不公开机器状态或凭据。

## 可验收节点

- [x] A1 核原接口、真正并行 owner、官方配置和现存能力。
- [x] A2 原组件 schema 和两个后端适配器完成可选字段；正式历史 binding 的原结构 reader 允许完整新字段，不改上层分派。
- [x] A3 源码45过／8原ForgeKernel与mini-swe可选依赖 skip；原13个并行节点已全部通过，覆盖异后端不同强度、祖先配额／窄子树／取消。原实际CLI进程、外部配置优先级、Agent修订及正式任务冻结已验。后继另环境8项是重复并行验证，不补齐上述skip、不计新增覆盖；独审已指出并据原JUnit更正。手册、原项目页面保存／重开及API读回已验；正式任务组合selector未在此浏览器片验证，真实应用等级另验。
- [x] A4 新 fresh-context 两轴独审approve／0；原模板Claude超时保留，按原授权Codex回退68.049秒approve，完整stdin／原结果及身份见交付，不称异后端成功。
- [x] A5 已普通合入开发分支 `a2655c3`，联合新安装33过，公开 `04af2344239306cb00458e89f81258093235f049` 及远端完整OID已核；自己的官方CI run `43819270365` attempt1 的8 jobs全success，含Windows。原API额度耗尽响应和恢复后结果分别保留在[联合交付](../delivery/2026-11-16-reasoning-cycle-runtime-integration.md)。不自动合main。

后继设计关卡、真实训练循环、可信脚本与一般 Repeat 不在本片内。每节点完成更新本页与根 `docs/PLAN.md`。

## 用户追加：按任务选择推理强度

用户询问模板默认与Agent按任务自行选择的关系。当前可执行合同是显式值：项目角色binding、独立Agent定义的backend、正式任务逐实例backend override；没有框架自动难度选择器。定义默认、操作者在任务编排前显式选值与原生模型实际应用等级是三件事；既有任务的冻结配置不因模板或当前head改变。

用户进一步要求把“由谁选档”设为配置，并支持预设和固定档位。后继以四种互斥模式设计，而不是以角色名决定：

|模式|选择时点与责任|应保存的信息|
|---|---|---|
|固定档位 `fixed`|操作者／定义作者给出该后端的明确原生请求值；保留当前显式字段与旧缺省语义。|原请求、来源、实际传入值；后端实际应用值只有可观察时才填写。|
|预设 `preset`|操作者／定义作者选经济、均衡、深入等有版本预设；适配器拥有本后端的映射，不把同名值视为跨后端等价。|预设ID／版本、完整映射与解析结果，旧任务不跟随最新映射。|
|规划阶段指定 `planner`|规划者在正式预览／冻结前，按任务和该实例允许集合提出明确值与理由；缺失决定要在调用前可见，不能偷偷转成自动。|规划依据、提出者及选择理由；这不是人类批准或新的工具授权。|
|框架自动 `automatic`|框架在调用合同冻结前使用有版本策略；仅在已声明范围和原预算内选择，不额外隐式调用一个模型来选档。|输入特征、策略ID／版本、允许集合、所选值、理由与无法判断时的显式配置行为。|

简单文档／局部修复可选择较低请求，架构／并发／恢复等复杂任务可选择较高请求；不能仅按角色名或任意提示词关键词硬编码，不能暗中换模型、扩张预算或中途修改运行中的选择。没有配置新模式时，当前显式值、外部原生配置和缺省行为保持原合同。完整backend override仍按原规则替换完整binding，不引入隐式字段合并。

选择与原生执行分开：Claude环境覆盖、组织／账户cap和模型限制可能改变实际应用；`ultracode`等特殊模式不能放入跨后端通用强度序列。必须区分 requested、实际发送以及可观察的 native-applied／unknown；argv或schema接纳不等于provider使用了请求等级，不自动降档冒充成功。上限先以本后端明确允许集合表达；不能用字符串顺序推导权限或预算。

- [x] A6a 后端选项调研：用户明确要求子agent核Codex、Claude Code及实际已接入后端的相似可配置项。先查官方文档并保存原文，再对照本地CLI help／源码，分别标原生支持、Ergora公开配置、已有透传、尚未接入和真实执行未验；给接入owner与优先级。完整英文／中文报告互链，英文默认，不读或输出密钥。调研者与双语文档整理为同一已授权子agent，先冻结首批文档再研究。
- [ ] A6b 配置与冻结设计：沿 `agent_backends` 本族接口核原生范围和预设投影，沿 `bindings.development_snapshot`、`tasks._member`、`agent_runs._admission` 核实际冻结边界；明确四模式选择权、覆盖顺序、缺失／不支持时行为、历史reader、独立单叶与正式任务／恢复的契约。所有新格式先核已保留的任务／输入版本，不占用设计关卡预留的v8／v12。完成fresh设计审再实施。
- [ ] A6c 实施：原绑定／Agent定义／正式任务接口消费同一选择；记录选择与原生实际请求，页面／CLI复用同一用例。先固定与预设，再规划与自动，逐片给实际消费者和冻结证明，不新增scheduler或全局工具注册表。
- [ ] A6d 验收与发布：仅对真实新失败和冻结风险补最小回归；覆盖同模板不同实例独立选档、不支持／缺少规划决定时调用0、原预算与所有祖先并行上限、保存后修改预设不改变旧任务、恢复不重新选档。每片独立审查，准确新非editable安装及普通推送另验。

该追加不重开已通过的显式配置源码，不改已发布定义或旧任务，也不改变当前一般Repeat／混合图与设计关卡的实施顺序。

交接时A6a研究正文与静态检查已完成：[English](../research/2026-11-16-backend-runtime-options.md)／[中文](../research/2026-11-16-backend-runtime-options.zh-CN.md)，20份官方／固定上游来源及5次版本／help只读结果；独立语义审已完成，两轴approve／0；唯一P2已补明Claude text-only的safe-mode关闭ultracode workflows，双语同片复核关闭，见[语义独审](../delivery/2026-11-16-backend-runtime-options-review.md)。这不标为实施或原生实际强度通过。作者已冻结并结束，无模型／登录／安装／服务调用。A6b–d尚未实施，精确输入及后继顺序见[handoff](../HANDOFF.zh-CN.md)。
