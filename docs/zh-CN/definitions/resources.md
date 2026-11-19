# 修订完整资源文件

简体中文 · [English](../../definitions/resources.md) · [文档目录](../../README.zh-CN.md)

CLI 可以在固定原包上写入完整文件、明确删除文件或追加空目录。先准备新的标准正文及操作目录；原包里没有编辑的文件保持原字节。此示例在 [architecture-reviewer 定义示例](agents.md#创建与修改定义)的基础上增加上下文资源。

下面的输出文件须为UTF-8。Windows PowerShell 5.1 将 `> 文件.json` 换为 `| Set-Content -Encoding UTF8 文件.json`；输入编码见[Windows说明](../../install/windows.md#install-and-authenticate-agents)。

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

库保存在持久 State 的 `agent-definitions/`：`index.json`记录精确ID/版本→包摘要，`objects/<摘要>/`保存完整包。沿用 `ERGORA_HOME`、`--home`及平台默认目录，见[安装手册](../../install/linux.md)。导入先校验并暂存完整树，再用原文件锁串行发布；首个对象和索引随完整库一起可见，增量对象先完成再原子更新索引。中断后可重试。已发布库缺索引、已登记对象缺失或被改时拒绝自动覆盖；不把损坏内容当作可修复缓存。

使用原[离线备份与恢复](../../install/upgrades.md#upgrades-and-persistent-data)命令可保存整库。备份验证会重新核对索引引用、定义身份和每份资源摘要；恢复继续要求原平台、原State路径及停止写入者。备份保持资源身份，不认证包作者或证明材料可信。
