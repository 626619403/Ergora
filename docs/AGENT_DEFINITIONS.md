# 专长 Agent 定义库

Agent 定义包保存一名专家的职能、专长、后端、初始指令、上下文和 Skill 资源。同一个后端可有多份互补定义；同一份定义以后也可用于多个模板。当前入口负责静态检查、导入、查看和分享，导入不运行其中的命令或脚本。

项目的角色调用使用[角色绑定](AGENT_BACKENDS.md#项目选择与独立调用)。Agent定义可由[工作流定义](WORKFLOW_DEFINITIONS.md)引用、预览完整祖先链，并通过`composition run-input`显式调用固定叶子。正式六阶段可[冻结审查组合](USAGE.md#为正式任务冻结审查组合)，运行单个或显式all-join的多个嵌套只读串并行审查者；[work-units-v1](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元)还可把互补实现专家分配给原工作单元，再承接总审查。任意其他职能拓扑仍见[实施计划](plans/2026-11-08-agent-composition.md)。

## 内置专家

`ergora composition install-preset large-change`可一次导入该领域的独立专家及完整子工作流；治理、开发、训练的对应入口见[内置领域组合](WORKFLOW_DEFINITIONS.md#使用内置领域组合)。这些定义随wheel安装，专长由初始指令和Skill描述；不同实例仍可选不同后端，模板通过精确引用组合它们。要修改默认专家，先export，调整内容与版本，再沿父引用发布新根；不覆盖原版本。导入不证明专家效果或后端推理可用。

Web控制台的“Agent 与组合库”可在未注册项目时导入这些组合，选择精确Agent版本并查看标准正文、自身完整资源和包文件身份；操作见[页面说明](USAGE.md#在页面浏览与预览定义)。默认后端是请求，页面不会凭导入成功宣称其已经认证。下载定义JSON只保存`agent.json`正文；包含Skill附件的可移植完整包仍使用下文`export`。被子工作流引用时，选择对应工作流并预览可查看该实例的全部祖先资源和实际装配指令。

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

`check` 不创建或迁移 State；加 `--material` 可查看完整必读文本。`import` 把包复制到持久 State，源目录之后可移走。`show` 每次重验内容；`export` 只写新的目录，导出结果可在能保持原文件字节和执行位语义的另一环境导入。示例在仓库的 [examples/agents](../examples/agents/)，不是额外安装的系统 Skill；仅安装 wheel 的用户可从该目录获取示例包。

[kernel 执行者](../examples/agents/kernel-implementer/agent.json)专注 CUDA/Triton 和测量，[架构审查者](../examples/agents/architecture-reviewer/agent.json)专注职责与依赖。两者当前都以 Codex 为默认后端，用于展示“后端相同，专家不同”；正式审查的成员准入默认优先与执行者使用不同后端，同后端回退需记录原因，也可要求严格不同。示例提示和 Skill 是起点，尚无模型效果评价。

## 创建与修改定义

包中必须有 `agent.json`，格式由 [schema v1](../src/ergora/data/schemas/agent-definition-v1.json)规定；当前只接受 JSON。正文用 UTF-8，接受 BOM。定义字段如下：

|字段|用途与约束|
|---|---|
|`schema_version`|严格整数 `1`；未知版本拒绝。|
|`id` / `version`|小写 kebab ID，版本为 `MAJOR.MINOR.PATCH`；读取必须指定精确版本，没有隐式 latest。|
|`description`|展示专家用途。|
|`roles`|可担任的现有职能；逐项复用后端能力校验。|
|`specialties`|专长标签，用于 `list --specialty`；不授予权限或证明模型能力。|
|`backend`|现有工具 binding；复用组件配置，不执行可用性探测，也不安装或认证后端。|
|`resources`|有序资源清单；每个逻辑ID唯一，必须且只能有一份 `instructions`。|

`resources` 的每项都有 `id`、`kind` 和 `path`。`instructions`、`context` 指向非空文本文件，必须附 `sha256`；`skill` 指向带合法 `SKILL.md` 的完整目录，必须附 `digest`，目录名须等于 frontmatter 的 name。Skill 的全部文件都进入摘要，查看材料时返回完整 `SKILL.md` 指令；脚本和其他按需资源保持文件形式。

编辑示例后，更新资源摘要再运行 `check`。下面是本地刷新摘要的 Python 示例，将 `my-agent` 改成自己的目录：

```python
import hashlib
import json
from pathlib import Path
from ergora.skill_assets import digest_tree

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

`--check` 检查候选但不登记版本；省略它才发布。返回候选 `digest`、标准正文、文件/资源身份、固定 `base` 与 `published`，不返回临时目录。派生过程只重写 `agent.json`，采用 UTF-8、排序键、两空格缩进及末尾换行；原包的指令、上下文、Skill附件、未声明文件及空目录完整复制。正文中的资源声明仍必须与实际文件一致。要修改文件内容，使用上面的 export/edit/check/import 流程；此入口不接收附件；标准正文可用 JSON，或通过 `--format yaml` 读取 YAML。库内仍保存标准 JSON。

原摘要不匹配会拒绝；新正文仍检查当前职能/后端合同。相同 ID/version 的不同内容不能发布，完全相同的请求可以重试；原版本始终保留。`check` 不是版本预留，并发发布仍可能使随后的发布产生版本冲突。派生不运行或认证后端，也不修改已引用原版本的工作流和任务。更新引用见[工作流修订](WORKFLOW_DEFINITIONS.md#修订分享与恢复)。

本机 HTTP 入口与 CLI 使用相同所有者：`POST /api/agent-definitions/{id}/{version}/revisions/check` 只检查，`POST /api/agent-definitions/{id}/{version}/revisions` 发布；JSON 请求为 `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`。两者都保留完整原包，不创建任务、批准或执行会话。

## 在页面编辑专长 Agent

运行 `ergora serve`，打开“Agent 与组合库”，导入内置组合或选择已有 Agent 的精确版本。在“字段编辑”中提高版本，修改描述、职能、专长和后端请求，点击“应用字段文本”。后端基础请求选择器只填写配置；模型与选项仍须符合所选工具的合同，选择成功不表示已安装或认证。

也可编辑“定义 JSON 原文”或“定义 YAML 原文”，明确应用后再“检查定义候选”，检查通过才可点击“发布新定义版本”。未应用的字段、JSON 和 YAML 分开保留；先逐一应用或放弃，不能用另一份表示覆盖尚未处理的原文。只调整排版不会重新生成另一格式；改变语义且需要替换其他自定义原文时，会先提示下载保留并明确确认同步。字段内的复杂 JSON 同样拒绝重复键。

成功后保留精确发布回执，点击“以已发布版本继续编辑”会使用新基准，原会话仍保留。回复丢失时不要换基准或改正文冒充原请求；可用相同基准和正文显式重试核对。检查不预留版本，发布时仍可能遇到版本冲突；冲突不会覆盖既有版本。

浏览器缓冲按控制目录、种类、原 ID/版本/摘要和标签页隔离，刷新后重新选择原版本即可恢复；缓冲不是持久定义。恢复会通过共同转换器核对已应用 JSON/YAML 的语义，未应用的无效文本继续保留。缓冲损坏时可下载原始内容、重试核对或明确清除；缓存配额不足会显示提示，可下载当前编辑缓冲。关闭标签页或换机前请发布，或另行下载保存；浏览器历史最多50份、合计4MiB正文，刷新后重新建立历史。

YAML 使用 JSON 数据模型：对象键必须是字符串，不接受重复键、别名、循环或自定义标签；日期等有歧义的字符串请加引号。转换最多64层、100000值（含映射键），HTTP 总请求最多4MB。JSON/YAML 只是编辑表示，不执行内容；发布的仍是完整资源包中的标准 JSON。页面保留原文件，文件追加或内容修改继续使用 export/edit/check/import。下载单份正文不包含附件；分享定义应导出完整包。

## 资源和存储边界

资源路径须是可移植的包内相对路径：使用 `/`，拒绝绝对路径、`..`、反斜杠、Windows保留名称/流和大小写冲突。包不包含 `.git`、符号链接、reparse point或特殊文件；最多10 MB、500文件、500目录和32层目录。所列资源的摘要缺失、内容不匹配或Skill frontmatter无效会在导入前失败。

当前schema拒绝未支持的MCP、权限和预算字段；后端binding中的既有sandbox字段仍按原工具合同校验。静态导入不证明sandbox可运行，也不构成权限批准。不要把凭据值写入可分享包；后端认证继续使用其现有登录或环境变量。

库保存在持久 State 的 `agent-definitions/`：`index.json`记录精确ID/版本→包摘要，`objects/<摘要>/`保存完整包。沿用 `ERGORA_HOME`、`--home`及平台默认目录，见[安装手册](USAGE.md)。导入先校验并暂存完整树，再用原文件锁串行发布；首个对象和索引随完整库一起可见，增量对象先完成再原子更新索引。中断后可重试。已发布库缺索引、已登记对象缺失或被改时拒绝自动覆盖；不把损坏内容当作可修复缓存。

使用原[离线备份与恢复](USAGE.md#升级与持久数据)命令可保存整库。备份验证会重新核对索引引用、定义身份和每份资源摘要；恢复继续要求原平台、原State路径及停止写入者。备份保持资源身份，不认证包作者或证明材料可信。

## 历史资产与当前准入

保存后的 `show/list/export` 检查本包版本化结构和完整内容；备份/恢复还检查工作流的递归引用。两者独立于当前可选的角色/后端。升级后某个工具被移除或配置规则收紧，仍可读取和导出完整旧材料；缺文件、篡改或身份漂移仍会失败，不会自动重写历史。

`list --role` 可按历史角色标签过滤，即使该角色已从当前运行目录移除。`check/import` 则同时检查当前角色与后端合同；重复导入相同包也要重新准入。工作流 `preview` 对引用的Agent采用当前准入。因而历史查看成功不表示该后端目前可用或允许执行，导出的旧包也可能无法在当前规则下重新导入。要使用替代工具，应发布明确的新Agent及引用它的新工作流版本；不会修改旧版本。
