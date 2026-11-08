# 专长 Agent 定义库

Agent 定义包保存一名专家的职能、专长、后端、初始指令、上下文和 Skill 资源。同一个后端可有多份互补定义；同一份定义以后也可用于多个模板。当前入口负责静态检查、导入、查看和分享，导入不运行其中的命令或脚本。

项目的实际调用仍使用[角色绑定](AGENT_BACKENDS.md#项目选择与独立调用)。当前定义库尚未接入 `agent run`、正式六阶段、多成员或嵌套工作流；后续资源继承、权限与冻结见[实施计划](plans/2026-11-08-agent-composition.md)。

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

[kernel 执行者](../examples/agents/kernel-implementer/agent.json)专注 CUDA/Triton 和测量，[架构审查者](../examples/agents/architecture-reviewer/agent.json)专注职责与依赖。两者当前都以 Codex 为默认后端，用于展示“后端相同，专家不同”；不代表实际协作中默认选择相同后端。运行时优先不同后端的策略将在成员准入切片接入。示例提示和 Skill 是起点，尚无模型效果评价。

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

## 资源和存储边界

资源路径须是可移植的包内相对路径：使用 `/`，拒绝绝对路径、`..`、反斜杠、Windows保留名称/流和大小写冲突。包不包含 `.git`、符号链接、reparse point或特殊文件；最多10 MB、500文件、500目录和32层目录。所列资源的摘要缺失、内容不匹配或Skill frontmatter无效会在导入前失败。

当前schema拒绝未支持的MCP、权限和预算字段；后端binding中的既有sandbox字段仍按原工具合同校验。静态导入不证明sandbox可运行，也不构成权限批准。不要把凭据值写入可分享包；后端认证继续使用其现有登录或环境变量。

库保存在持久 State 的 `agent-definitions/`：`index.json`记录精确ID/版本→包摘要，`objects/<摘要>/`保存完整包。沿用 `ERGORA_HOME`、`--home`及平台默认目录，见[安装手册](USAGE.md)。导入先校验并暂存完整树，再用原文件锁串行发布；首个对象和索引随完整库一起可见，增量对象先完成再原子更新索引。中断后可重试。已发布库缺索引、已登记对象缺失或被改时拒绝自动覆盖；不把损坏内容当作可修复缓存。

使用原[离线备份与恢复](USAGE.md#升级与持久数据)命令可保存整库。备份验证会重新核对索引引用、定义身份和每份资源摘要；恢复继续要求原平台、原State路径及停止写入者。备份保持资源身份，不认证包作者或证明材料可信。
