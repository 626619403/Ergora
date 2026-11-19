# 专长 Agent 定义库

简体中文 · [English](../../definitions/agents.md) · [文档目录](../../README.zh-CN.md)

Agent 定义包保存一名专家的职能、专长、后端、初始指令、上下文和 Skill 资源。同一个后端可有多份互补定义；同一份定义以后也可用于多个模板。当前入口负责静态检查、导入、查看和分享，导入不运行其中的命令或脚本。

项目的角色调用使用[角色绑定](../../agents/backends.md#project-selection-and-standalone-calls)。Agent定义可由[工作流定义](../../definitions/workflows/compose.md)引用、预览完整祖先链，并通过`composition run-input`显式调用固定叶子。正式六阶段可[冻结审查组合](../../development/preparation.md#freeze-a-review-composition-for-a-formal-task)，运行单个或显式all-join的多个嵌套只读串并行审查者；[work-units-v2](../../definitions/workflows/contracts.md#specialist-writers-and-original-work-units)还可把互补实现专家分配给原工作单元，再承接总审查。原v1协议和已封存任务保持其合同。任意其他职能拓扑仍见[工作流指南](../../definitions/workflows/permissions.md#complete-inheritance-and-conflicts)。

## 当前可用性与运行边界

定义导入、静态关系图预览和已保存manifest不证明后端已安装、已认证、模型具备能力或获准执行。Skill与上下文沿完整结构祖先链累积，子权限必须始终处于父权限及项目授权范围内。新定义或绑定不改写任务已冻结的后端、资源或合同；已有任务须沿原身份恢复。

内置专家显式选择 Codex `gpt-6.1-sol`：规划、契约与 kernel 候选设计用 `max`，跨文件实现用 `xhigh`，审查、文档、兼容验证与纯诊断用 `high`。定义的可选 `invocation_minimum` 固定模型和最低 `reasoning_effort`；同模型上调允许，低于下限、缺省模型／强度或其他无法比较的后端／模型会在调用及正式任务冻结校验处拒绝。明确短程自定义定义可以声明 `medium`；当前没有独立短程内置模板。普通自定义定义可不声明下限。请求值与真实后端执行仍分别核验，统一planner／automatic选型未实现。

受限组合调用禁用环境中的用户配置。使用自定义provider时，由操作者通过`--codex-config ./inference.toml`提供原推理配置，凭据只引用环境变量；模板不保存provider或私有路径。显式模型／强度覆盖该文件对应项，其余provider配置保留。不指定`--backend`时继承模板binding；选择同一backend也保留模板未覆盖字段。

正式执行保持原六阶段及上述已支持的审查／工作单元合同；静态关系图不使任意职能拓扑或一般Repeat变得可执行。当前[设计策略登记](../../projects/registration.md#current-limits-of-design-policy-registration)仍仅存储，不支持执行。只读[source-journal记录](../../development/design-and-approval.md#store-complete-design-sources-and-reported-answers)不授执行权；有限训练控制器须[明确授权](../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization)。导入定义或选择后端不扩大这些边界。

## 内置专家

`ergora composition install-preset large-change`可一次导入该领域的独立专家及完整子工作流；治理、开发、训练的对应入口见[内置领域组合](../../definitions/workflows/compose.md#use-bundled-domain-compositions)。这些定义随wheel安装，专长由初始指令和Skill描述；不同实例仍可选不同后端，模板通过精确引用组合它们。要修改默认专家，先export，调整内容与版本，再沿父引用发布新根；不覆盖原版本。导入不证明专家效果或后端推理可用。

Web控制台的“Agent 与组合库”可在未注册项目时导入这些组合，选择精确Agent版本并查看标准正文、自身完整资源和包文件身份；操作见[页面说明](../../definitions/workflows/compose.md#browse-and-preview-definitions-in-the-page)。默认后端是请求，页面不会凭导入成功宣称其已经认证。下载定义JSON只保存`agent.json`正文；包含Skill附件的可移植完整包仍使用下文`export`。被子工作流引用时，选择对应工作流并预览可查看该实例的全部祖先资源和实际装配指令。

## 使用已有示例

在仓库根目录安装 Ergora 后，无需注册项目或启动服务即可使用：

```bash
ergora agent definition check examples/agents/kernel-implementer
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/architecture-reviewer
ergora agent definition list --role reviewer
ergora agent definition list --specialty cuda
ergora agent definition show architecture-reviewer 1.0.0 --material
ergora agent definition export architecture-reviewer 1.0.0 ./shared-architecture-reviewer
```

`check` 不创建或迁移 State；加 `--material` 可查看完整必读文本。`import` 把包复制到持久 State，源目录之后可移走。`show` 每次重验内容；`export` 只写新的目录，导出结果可在能保持原文件字节和执行位语义的另一环境导入。示例在仓库的 [examples/agents](../../../examples/agents)，不是额外安装的系统 Skill；仅安装 wheel 的用户可从该目录获取示例包。

[kernel 执行者](../../../examples/agents/kernel-implementer/agent.json)专注 CUDA/Triton 和测量，[架构审查者](../../../examples/agents/architecture-reviewer/agent.json)专注职责与依赖。两者当前都以 Codex 为默认后端，用于展示“后端相同，专家不同”；正式审查的成员准入默认优先与执行者使用不同后端，同后端回退需记录原因，也可要求严格不同。示例提示和 Skill 是起点，尚无模型效果评价。

## 创建与修改定义

包中必须有 `agent.json`，格式由 [schema v1](../../../src/ergora/data/schemas/agent-definition-v1.json)规定；当前只接受 JSON。正文用 UTF-8，接受 BOM。定义字段如下：

|字段|用途与约束|
|---|---|
|`schema_version`|严格整数 `1`；未知版本拒绝。|
|`id` / `version`|小写 kebab ID，版本为 `MAJOR.MINOR.PATCH`；读取必须指定精确版本，没有隐式 latest。|
|`description`|展示专家用途。|
|`roles`|可担任的现有职能；逐项复用后端能力校验。|
|`specialties`|专长标签，用于 `list --specialty`；不授予权限或证明模型能力。|
|`backend`|现有工具 binding；复用组件配置，不执行可用性探测，也不安装或认证后端。|
|`invocation_minimum`|可选模型与推理下限：`{"model":"gpt-6.1-sol","reasoning_effort":"high"}`；默认backend及实际override必须满足。|
|`resources`|有序资源清单；每个逻辑ID唯一，必须且只能有一份 `instructions`。|

`resources` 的每项都有 `id`、`kind` 和 `path`。`instructions`、`context` 指向非空文本文件，必须附 `sha256`；`skill` 指向带合法 `SKILL.md` 的完整目录，必须附 `digest`，目录名须等于 frontmatter 的 name。Skill 的全部文件都进入摘要，查看材料时返回完整 `SKILL.md` 指令；脚本和其他按需资源保持文件形式。

AgentDefinition v1 不保存权限字段；同一专家在不同组合实例中的权限由所属 Workflow 节点及全部结构祖先约束。增加专家资料不会改变这些权限。将新专家资源送入既有组合时，应[沿完整依赖链发布](../../definitions/workflows/revisions.md#publish-resource-revisions-through-the-complete-dependency-chain)，最后固定新根和输入；实际附件读取见[任务MCP](../../definitions/workflows/leaf-calls.md#verify-complete-attachment-reads)。

同一个 Agent 定义可被多个不同路径的实例引用；路径区分调用身份，完整 ref 固定共同的专长、指令和默认后端。各实例可在已支持的调用入口明确覆盖后端。审查职责属于引用它的 Workflow Agent 节点；嵌套模板需要不同职责时，先发布对应子模板修订，不能在父 Workflow 引用上添加覆盖字段。具体操作见[重复实例、职责和后端选择](../../definitions/workflows/revisions.md#repeated-instances-responsibilities-and-backend-selection)。

编辑示例后，更新资源摘要再运行 `check`。下面是本地刷新摘要的 Python 示例，将 `my-agent` 改成自己的目录：

```python
import hashlib
import json
from pathlib import Path
from ergora.storage.assets import digest_tree

root = Path("my-agent")
definition = json.loads((root / "agent.json").read_text(encoding="utf-8-sig"))
for resource in definition["resources"]:
    path = root / resource["path"]
    if resource["kind"] == "skill":
        resource["digest"] = digest_tree(path)[0]
    else:
        resource["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
(root / "agent.json").write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
```

同一 `id/version` 只能指向一份内容。导入相同包幂等，修改已登记版本会拒绝；应提高版本再导入。后端 binding 的模型等字段变化、JSON排版、换行和脚本执行位都会改变包摘要。摘要覆盖包内所有普通文件，包括未声明附件；空目录和修改时间不参与身份。

POSIX与Windows的可执行位语义不同，含可执行资源的Skill跨系统复制后可能摘要不匹配并明确拒绝，路径可移植不保证执行位可保真。需要移植时，应显式创建并核对适合目标系统的新版本与摘要；不会自动丢弃执行位或重写已登记身份。State备份仍只支持原平台恢复。

## 从固定原包派生新版本

只修改标准正文时，可以保留原包的全部文件，直接提交新的完整 `agent.json`。先用 `show` 取得原版本的 `digest` 和 `definition`；将 `definition` 单独保存为 `new-agent.json`，修改版本以及需要调整的职能、专长或后端字段。下面的 `BASE_DIGEST` 替换为原包摘要：

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --check
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json
```

`--check` 检查候选但不登记版本；省略它才发布。返回候选 `digest`、标准正文、文件/资源身份、固定 `base` 与 `published`，不返回临时目录。不带资源参数时只重写 `agent.json`，采用 UTF-8、排序键、两空格缩进及末尾换行；原包的指令、上下文、Skill附件、未声明文件及空目录完整复制。正文中的资源声明仍必须与实际文件一致。通过[完整资源修订](resources.md#修订完整资源文件)或导出/编辑/检查/导入修改资源内容。控制台文件操作使用[资源编辑](resources.md#在页面编辑资源与附件)；标准正文可用 JSON，或通过 `--format yaml` 读取 YAML。库内仍保存标准 JSON。

原摘要不匹配会拒绝；新正文仍检查当前职能/后端合同。相同 ID/version 的不同内容不能发布，完全相同的请求可以重试；原版本始终保留。`check` 不是版本预留，并发发布仍可能使随后的发布产生版本冲突。派生不运行或认证后端，也不修改已引用原版本的工作流和任务。更新引用见[工作流修订](../../definitions/workflows/revisions.md#revision-sharing-and-recovery)。

本机 HTTP 入口与 CLI 使用相同所有者：`POST /api/agent-definitions/{id}/{version}/revisions/check` 只检查，`POST /api/agent-definitions/{id}/{version}/revisions` 发布；JSON 请求为 `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`。两者都保留完整原包，不创建任务、批准或执行会话。

## 在页面编辑专长 Agent

运行 `ergora serve`，打开“Agent 与组合库”，导入内置组合或选择已有 Agent 的精确版本。在“字段编辑”中提高版本，修改描述、职能、专长和后端请求，点击“应用字段文本”。后端基础请求选择器只填写配置；模型与选项仍须符合所选工具的合同，选择成功不表示已安装或认证。

也可从[已发布嵌套关系图](../../definitions/workflows/revisions.md#view-published-nested-relationships)选择完整Agent实例路径，再“打开所选精确定义”。该入口固定原id/版本/摘要；多个实例引用同一Agent时打开同一不可变定义。实例权限和输入绑定属于结构父工作流，使用“打开结构父定义”修改。图中专长按精确Agent索引匹配，不使用最新版本代替。

图页可按职责、专长、后端和完整路径查找，例如`reviewer codex`。查找保留未匹配结构；结果按钮可展开结构祖先并定位，完整实例表也能直接选择折叠内部的叶子、查看全部继承材料。专长索引缺失会明确提示，不能把未知当作已具备。折叠/查找只改变本页显示，不调整Agent授权或所用后端。

工作流页面还可[比较两个已发布组合](../../definitions/workflows/revisions.md#compare-two-published-compositions)，逐实例核对Agent的精确引用、后端、职能、权限和完整继承材料。资源内容与来源版本分别展示，单纯换版本不表示Skill正文改变。比较不修改独立Agent定义或编辑缓冲；描述、专长等未进入preview的字段仍须打开精确定义查看。

也可编辑“定义 JSON 原文”或“定义 YAML 原文”，明确应用后再“检查定义候选”，检查通过才可点击“发布新定义版本”。未应用的字段、JSON 和 YAML 分开保留；先逐一应用或放弃，不能用另一份表示覆盖尚未处理的原文。只调整排版不会重新生成另一格式；改变语义且需要替换其他自定义原文时，会先提示下载保留并明确确认同步。字段内的复杂 JSON 同样拒绝重复键。

成功后保留精确发布回执，点击“以已发布版本继续编辑”会使用新基准，原会话仍保留。回复丢失时不要换基准或改正文冒充原请求；可用相同基准和正文显式重试核对。检查不预留版本，发布时仍可能遇到版本冲突；冲突不会覆盖既有版本。

浏览器缓冲按控制目录、种类、原 ID/版本/摘要和标签页隔离，刷新后重新选择原版本即可恢复；缓冲不是持久定义。恢复会通过共同转换器核对已应用 JSON/YAML 的语义，未应用的无效文本继续保留。缓冲损坏时可下载原始内容、重试核对或明确清除；缓存配额不足会显示提示，可下载当前编辑缓冲。关闭标签页或换机前请发布，或另行下载保存；浏览器历史最多50份，会逐出旧快照向合计4MiB预算收敛（含完整资源操作字节）；即使最新一份单独超过预算，也会保留该快照，刷新后重新建立历史。

YAML 使用 JSON 数据模型：对象键必须是字符串，不接受重复键、别名、循环或自定义标签；日期等有歧义的字符串请加引号。转换最多64层、100000值（含映射键），HTTP 总请求最多4MB。JSON/YAML 只是编辑表示，不执行内容；发布的仍是完整资源包中的标准 JSON。页面文件操作见下面的资源编辑步骤；大变更仍可使用上面的 CLI 资源修订或 export/edit/check/import。下载单份正文不包含附件；分享定义应导出完整包。

## 历史资产与当前准入

保存后的 `show/list/export` 检查本包版本化结构和完整内容；备份/恢复还检查工作流的递归引用。两者独立于当前可选的角色/后端。升级后某个工具被移除或配置规则收紧，仍可读取和导出完整旧材料；缺文件、篡改或身份漂移仍会失败，不会自动重写历史。

`list --role` 可按历史角色标签过滤，即使该角色已从当前运行目录移除。`check/import` 则同时检查当前角色与后端合同；重复导入相同包也要重新准入。工作流 `preview` 对引用的Agent采用当前准入。因而历史查看成功不表示该后端目前可用或允许执行，导出的旧包也可能无法在当前规则下重新导入。要使用替代工具，应发布明确的新Agent及引用它的新工作流版本；不会修改旧版本。


工作流完成静态预览后，可在页面明确保存当前根及全部Agent/Skill附件为完整manifest，或用`composition freeze-manifest`绑定原预览摘要。不同后端的正式准入与writer信任仍在任务交接时检查；详见[持久完整包](../../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory)。

正式任务页面可为[每个组合实例选择后端](../../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)，不改变本Agent的默认请求或其他引用它的实例。审查者默认沿精确定义；可写执行者必须显式填写覆盖后端/执行边界与理由。后端配置表单与项目绑定共用组件schema，选择不证明已认证或能运行该模式；正式任务预览重新检查原合同。
