# 专长 Agent 定义库

Agent 定义包保存一名专家的职能、专长、后端、初始指令、上下文和 Skill 资源。同一个后端可有多份互补定义；同一份定义以后也可用于多个模板。当前入口负责静态检查、导入、查看和分享，导入不运行其中的命令或脚本。

项目的角色调用使用[角色绑定](AGENT_BACKENDS.md#项目选择与独立调用)。Agent定义可由[工作流定义](WORKFLOW_DEFINITIONS.md)引用、预览完整祖先链，并通过`composition run-input`显式调用固定叶子。正式六阶段可[冻结审查组合](USAGE.md#为正式任务冻结审查组合)，运行单个或显式all-join的多个嵌套只读串并行审查者；[work-units-v2](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元)还可把互补实现专家分配给原工作单元，再承接总审查。原v1协议和已封存任务保持其合同。任意其他职能拓扑仍见[实施计划](plans/2026-11-08-agent-composition.md)。

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

AgentDefinition v1 不保存权限字段；同一专家在不同组合实例中的权限由所属 Workflow 节点及全部结构祖先约束。增加专家资料不会改变这些权限。将新专家资源送入既有组合时，应[沿完整依赖链发布](WORKFLOW_DEFINITIONS.md#沿完整依赖链发布资源修订)，最后固定新根和输入；实际附件读取见[任务MCP](WORKFLOW_DEFINITIONS.md#核验完整附件读取)。

同一个 Agent 定义可被多个不同路径的实例引用；路径区分调用身份，完整 ref 固定共同的专长、指令和默认后端。各实例可在已支持的调用入口明确覆盖后端。审查职责属于引用它的 Workflow Agent 节点；嵌套模板需要不同职责时，先发布对应子模板修订，不能在父 Workflow 引用上添加覆盖字段。具体操作见[重复实例、职责和后端选择](WORKFLOW_DEFINITIONS.md#重复实例职责和后端选择)。

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

`--check` 检查候选但不登记版本；省略它才发布。返回候选 `digest`、标准正文、文件/资源身份、固定 `base` 与 `published`，不返回临时目录。不带资源参数时只重写 `agent.json`，采用 UTF-8、排序键、两空格缩进及末尾换行；原包的指令、上下文、Skill附件、未声明文件及空目录完整复制。正文中的资源声明仍必须与实际文件一致。文件内容修改可使用下面的资源修订，或 export/edit/check/import；标准正文可用 JSON，或通过 `--format yaml` 读取 YAML。库内仍保存标准 JSON。

原摘要不匹配会拒绝；新正文仍检查当前职能/后端合同。相同 ID/version 的不同内容不能发布，完全相同的请求可以重试；原版本始终保留。`check` 不是版本预留，并发发布仍可能使随后的发布产生版本冲突。派生不运行或认证后端，也不修改已引用原版本的工作流和任务。更新引用见[工作流修订](WORKFLOW_DEFINITIONS.md#修订分享与恢复)。

本机 HTTP 入口与 CLI 使用相同所有者：`POST /api/agent-definitions/{id}/{version}/revisions/check` 只检查，`POST /api/agent-definitions/{id}/{version}/revisions` 发布；JSON 请求为 `{"base_digest": "原包的64位小写摘要", "definition": {完整的新正文}}`。两者都保留完整原包，不创建任务、批准或执行会话。

## 修订完整资源文件

CLI 可以在固定原包上写入完整文件、明确删除文件或追加空目录。先准备新的标准正文及操作目录；原包里没有编辑的文件保持原字节。以下示例承接上面的 `architecture-reviewer 1.0.0`，增加一份上下文：

下面的输出文件须为UTF-8。Windows PowerShell 5.1 将 `> 文件.json` 换为 `| Set-Content -Encoding UTF8 文件.json`；输入编码见[Windows说明](WINDOWS.md#agent-安装与认证)。

```bash
ergora agent definition show architecture-reviewer 1.0.0 > base-agent.json
```

运行下面的 Python，保存原包摘要，建立 `resource-changes/changes.json`、完整内容文件及新正文。版本已存在时改用未发布的新版本。资源路径相对整个定义包，新增声明先放合法占位摘要，预览会给出实际摘要：

```python
import json
from pathlib import Path

base = json.loads(Path("base-agent.json").read_text(encoding="utf-8-sig"))
definition = base["definition"]
definition["version"] = "1.0.1"
definition["resources"].append({"id": "project-context", "kind": "context",
    "path": "context/project.md", "sha256": "0" * 64})
root = Path("resource-changes")
(root / "files/context").mkdir(parents=True, exist_ok=True)
(root / "files/context/project.md").write_text("Project context: keep complete evidence.\n", encoding="utf-8")
(root / "changes.json").write_text(json.dumps({"schema_version": 1, "operations": [
    {"op": "write", "path": "context/project.md"},
    {"op": "mkdir", "path": "references/empty"}]}), encoding="utf-8")
Path("new-agent.json").write_text(json.dumps(definition, ensure_ascii=False), encoding="utf-8")
print(base["digest"])  # 替换下面的 BASE_DIGEST
```

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --preview-resources > resource-preview.json
```

预览执行完整准入但不发布。检查响应的 `changes`、`directory_changes`、建议 `definition` 和 `candidate`。将建议正文保存到 `new-agent.json`：

```python
import json
from pathlib import Path

preview = json.loads(Path("resource-preview.json").read_text(encoding="utf-8-sig"))
Path("new-agent.json").write_text(json.dumps(preview["definition"], ensure_ascii=False), encoding="utf-8")
```

确认这些修改后，以保存的预览明确接受候选，再检查和发布：

```bash
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --accept-candidate ./resource-preview.json --check
ergora agent definition revise architecture-reviewer 1.0.0 --base-digest BASE_DIGEST --document ./new-agent.json --resources ./resource-changes --accept-candidate ./resource-preview.json
```

`candidate` 同时包含完整包 `digest` 和完整排序 `directories`。正文、普通附件、执行位或目录变化后必须重新预览和接受；最终检查不自动刷新资源摘要。预览不是版本预留或项目批准。相同候选可显式重试；同摘要已有对象若目录不同，资源发布明确拒绝，需提高版本重新预览，不会补写旧对象。资源声明与权限分别管理，新增 Skill 不产生工具或网络授权。

操作目录的 `write` 字节来自 `files/<path>`，不使用源文件执行位，也不在清单另写 `content_base64`。省略 `executable_bits` 时旧文件保持执行位，新文件为零；需要时可指定 `0o111` 的子集整数，平台不能实现则拒绝。普通附件可为二进制或空文件；声明为 instructions/context 的文件仍须非空 UTF-8，Skill 仍须完整树及合法 frontmatter。

`{"op":"delete","path":"old.bin"}` 只删除已存在的普通文件；若仍被资源声明引用，须在新正文中明确移除声明。未出现在清单中的文件不变。`mkdir` 和 `write` 自动建立缺失父目录；`mkdir` 可保持已有目录。拒绝重复、大小写冲突及祖先/后代重叠操作，例如同时 mkdir `new` 和 write `new/a.md`；只声明 write 即可建立父目录。标准 `agent.json`、`workflow.json` 只走正文入口。没有递归删除、重命名或隐式目录覆盖。

HTTP 对应 `POST .../revisions/preview-resources`，body 包含 `base_digest`、完整 `definition` 和 `resource_changes:{"schema_version":1,"operations":[...]}`。write 项改为携带完整 `content_base64`，不接本地目录。把预览返回的建议正文和 `candidate` 分别作为最终 body 的 `definition`、`accepted_candidate`，与同一份 `resource_changes` 送往原 `/revisions/check` 和 `/revisions`。沿用本机同源规则及 `X-Ergora-Request: 1`。HTTP 请求总上限 `4_000_000` 字节含 base64；更大修改使用 CLI。CLI 操作目录含清单受10MB/500文件/500目录限制；最终包还须满足原10MB/500文件/500目录/32层，写入总字节最多10MB，最多1500项操作。无需模型认证或后台任务服务。

## 读取固定版本文件

```bash
ergora agent definition file architecture-reviewer 1.0.0 instructions.md --base-digest BASE_DIGEST --offset 0 --limit 65536
```

文件路径取自该版本 `show` 的 `files`；历史读取不要求后端今天仍可调用。返回完整文件 SHA、执行位、大小、字节偏移、`content_base64`、`next_offset` 和 `complete`。按 `next_offset` 连续读取至 null；只有从0返回全部字节时 `complete:true`，后续最后一页也不能单独覆盖整份文件。偏移按字节计算，UTF-8 字符可能跨页；先合并完整字节再严格解码。每页1–65536字节，空文件同样可完整读取；普通未声明附件也可读，包外或未登记路径拒绝。

HTTP 为 `POST /api/agent-definitions/{id}/{version}/files/read`，body 是 `{"base_digest":"...","path":"instructions.md","offset":0,"limit":65536}`。此入口只读取，不执行附件或创建资源会话。完整包分享仍使用 `export`。

## 在页面编辑专长 Agent

运行 `ergora serve`，打开“Agent 与组合库”，导入内置组合或选择已有 Agent 的精确版本。在“字段编辑”中提高版本，修改描述、职能、专长和后端请求，点击“应用字段文本”。后端基础请求选择器只填写配置；模型与选项仍须符合所选工具的合同，选择成功不表示已安装或认证。

也可从[已发布嵌套关系图](WORKFLOW_DEFINITIONS.md#查看已发布嵌套关系图)选择完整Agent实例路径，再“打开所选精确定义”。该入口固定原id/版本/摘要；多个实例引用同一Agent时打开同一不可变定义。实例权限和输入绑定属于结构父工作流，使用“打开结构父定义”修改。图中专长按精确Agent索引匹配，不使用最新版本代替。

图页可按职责、专长、后端和完整路径查找，例如`reviewer codex`。查找保留未匹配结构；结果按钮可展开结构祖先并定位，完整实例表也能直接选择折叠内部的叶子、查看全部继承材料。专长索引缺失会明确提示，不能把未知当作已具备。折叠/查找只改变本页显示，不调整Agent授权或所用后端。

工作流页面还可[比较两个已发布组合](WORKFLOW_DEFINITIONS.md#比较两个已发布组合)，逐实例核对Agent的精确引用、后端、职能、权限和完整继承材料。资源内容与来源版本分别展示，单纯换版本不表示Skill正文改变。比较不修改独立Agent定义或编辑缓冲；描述、专长等未进入preview的字段仍须打开精确定义查看。

也可编辑“定义 JSON 原文”或“定义 YAML 原文”，明确应用后再“检查定义候选”，检查通过才可点击“发布新定义版本”。未应用的字段、JSON 和 YAML 分开保留；先逐一应用或放弃，不能用另一份表示覆盖尚未处理的原文。只调整排版不会重新生成另一格式；改变语义且需要替换其他自定义原文时，会先提示下载保留并明确确认同步。字段内的复杂 JSON 同样拒绝重复键。

成功后保留精确发布回执，点击“以已发布版本继续编辑”会使用新基准，原会话仍保留。回复丢失时不要换基准或改正文冒充原请求；可用相同基准和正文显式重试核对。检查不预留版本，发布时仍可能遇到版本冲突；冲突不会覆盖既有版本。

浏览器缓冲按控制目录、种类、原 ID/版本/摘要和标签页隔离，刷新后重新选择原版本即可恢复；缓冲不是持久定义。恢复会通过共同转换器核对已应用 JSON/YAML 的语义，未应用的无效文本继续保留。缓冲损坏时可下载原始内容、重试核对或明确清除；缓存配额不足会显示提示，可下载当前编辑缓冲。关闭标签页或换机前请发布，或另行下载保存；浏览器历史最多50份、合计4MiB（含完整资源操作字节），刷新后重新建立历史。

YAML 使用 JSON 数据模型：对象键必须是字符串，不接受重复键、别名、循环或自定义标签；日期等有歧义的字符串请加引号。转换最多64层、100000值（含映射键），HTTP 总请求最多4MB。JSON/YAML 只是编辑表示，不执行内容；发布的仍是完整资源包中的标准 JSON。页面文件操作见下面的资源编辑步骤；大变更仍可使用上面的 CLI 资源修订或 export/edit/check/import。下载单份正文不包含附件；分享定义应导出完整包。

## 在页面编辑资源与附件

在同一精确版本的“资源与附件编辑”中操作；所有修改仍相对页面显示的原包，不会改写它。

1. 在字段中提高版本并应用。若新增声明资源，用 JSON/YAML 的 `resources` 添加 `id/kind/path` 和合法64位占位摘要；instructions/context 用 `sha256`，Skill 用 `digest`。先应用正文。普通附件无需声明；删除仍被声明的文件时，同时明确移除或修改声明。
2. 展开“原包文件：完整读取与下载”，完整读取文本到草稿，或下载原字节。读取使用连续有界窗口，合并并核完整 SHA 后才可编辑，保留 UTF-8 BOM；非法 UTF-8 作为二进制保留。标准 JSON 仍只经正文入口编辑。
3. 填包内相对路径，选择完整写入、明确删除文件或增加空目录。可填完整文本或上传一个完整文件；上传保持字节，确认是 UTF-8 时可显式转为文本。执行位留空保留原值、新文件默认0；需要时填八进制 `100` 等每位只有0/1的值。不从上传文件推断执行位。
4. 点击“暂存文件操作”。列表是相对原包的完整工作集合，后续追加保留此前已采用操作；同一精确路径的暂存明确替换该项，移除该项会恢复该路径的原包行为。已修改文件应从操作列表“编辑操作”，原包文件列表始终读取旧基准。Skill 须逐文件加入完整树；省略文件不推断删除，write/mkdir自动建父目录，不另加重叠父目录操作。
5. 完成文件草稿后点击“预览资源候选”，核对文件/目录差异和建议正文，再点击“采用资源摘要”。预览不会应用或发布。采用将正文、完整操作和接受身份共同写入一份历史；需重新生成自定义 JSON/YAML 排版时先确认。随后“检查定义候选”，通过后明确“发布新定义版本”。

未应用字段/原文/文件草稿/操作阻塞旧快照的检查与发布；正文或资源变化都使上次检查、预览与接受失效。第二次修改必须重新预览并采用。撤销/重做共同恢复已应用正文、完整操作和接受身份，但仍需重新检查；未应用内容不进入已应用历史。

刷新可恢复已应用与未应用缓冲，重新核两种已应用正文及完整字节；预览和检查不复用。旧版无资源缓冲可恢复，损坏缓冲保留原始下载并拒绝发布。浏览器quota不足会提示；“下载定义编辑缓冲”含全部已应用/未应用正文与操作字节，不含未编辑原包，不能当作独立完整包。关闭标签页或换机前请发布或保存下载；完整包另用CLI `export`。

每个完整操作集合最多1500项、10,000,000 decoded写字节，替换时扣除旧项；超限在读取/编码并保留新字节前拒绝，原集合和草稿不变。HTTP请求总共最多4,000,000字节（含base64），大变更请保留缓冲并使用CLI `--resources`，不会自动分片或重发。页面读取和上传不启动Agent或授予工具权限。

## 资源和存储边界

资源路径须是可移植的包内相对路径：使用 `/`，拒绝绝对路径、`..`、反斜杠、Windows保留名称/流和大小写冲突。包不包含 `.git`、符号链接、reparse point或特殊文件；最多10 MB、500文件、500目录和32层目录。所列资源的摘要缺失、内容不匹配或Skill frontmatter无效会在导入前失败。

当前schema拒绝未支持的MCP、权限和预算字段；后端binding中的既有sandbox字段仍按原工具合同校验。静态导入不证明sandbox可运行，也不构成权限批准。不要把凭据值写入可分享包；后端认证继续使用其现有登录或环境变量。

库保存在持久 State 的 `agent-definitions/`：`index.json`记录精确ID/版本→包摘要，`objects/<摘要>/`保存完整包。沿用 `ERGORA_HOME`、`--home`及平台默认目录，见[安装手册](USAGE.md)。导入先校验并暂存完整树，再用原文件锁串行发布；首个对象和索引随完整库一起可见，增量对象先完成再原子更新索引。中断后可重试。已发布库缺索引、已登记对象缺失或被改时拒绝自动覆盖；不把损坏内容当作可修复缓存。

使用原[离线备份与恢复](USAGE.md#升级与持久数据)命令可保存整库。备份验证会重新核对索引引用、定义身份和每份资源摘要；恢复继续要求原平台、原State路径及停止写入者。备份保持资源身份，不认证包作者或证明材料可信。

## 历史资产与当前准入

保存后的 `show/list/export` 检查本包版本化结构和完整内容；备份/恢复还检查工作流的递归引用。两者独立于当前可选的角色/后端。升级后某个工具被移除或配置规则收紧，仍可读取和导出完整旧材料；缺文件、篡改或身份漂移仍会失败，不会自动重写历史。

`list --role` 可按历史角色标签过滤，即使该角色已从当前运行目录移除。`check/import` 则同时检查当前角色与后端合同；重复导入相同包也要重新准入。工作流 `preview` 对引用的Agent采用当前准入。因而历史查看成功不表示该后端目前可用或允许执行，导出的旧包也可能无法在当前规则下重新导入。要使用替代工具，应发布明确的新Agent及引用它的新工作流版本；不会修改旧版本。


工作流完成静态预览后，可在页面明确保存当前根及全部Agent/Skill附件为完整manifest，或用`composition freeze-manifest`绑定原预览摘要。不同后端的正式准入与writer信任仍在任务交接时检查；详见[持久完整包](WORKFLOW_DEFINITIONS.md#固定当前预览到持久控制目录)。

正式任务页面可为[每个组合实例选择后端](WORKFLOW_DEFINITIONS.md#在正式任务页面选择组合)，不改变本Agent的默认请求或其他引用它的实例。审查者默认沿精确定义；可写执行者必须显式填写覆盖后端/执行边界与理由。后端配置表单与项目绑定共用组件schema，选择不证明已认证或能运行该模式；正式任务预览重新检查原合同。
