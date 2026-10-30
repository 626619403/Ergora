# 可移植任务契约：快速迁移与接入

这层把任务、工作规则、项目政策与部署绑定分开；现有 Temporal 开发工作流继续运行。它是本项目版本化的互换契约，**不是所有平台共同支持的行业任务标准**。A2A 负责远程任务交接，使用说明见 [A2A.md](A2A.md)。

## 一次任务要准备什么

| 文件 | 谁维护 | 内容 |
| --- | --- | --- |
| `task.json` | 任务负责人 / planner | 目标、固定提交、范围、验收、工作单元；不含 tracker、模型、凭据、队列或引擎 |
| `packages/<type>/manifest.json` | 平台维护者 | 类型、版本、文件摘要、兼容 profile 摘要 |
| `workflow.json` | 平台维护者 | 阶段、依赖、人类关口、并发与期限 |
| `roles.json` | 平台维护者 | 能力、允许身份类别、独立性与行为限制 |
| `evidence.json` | 平台维护者 | 必需检查、必需产物、固定候选与取消等能力要求 |
| `policy.json` | 项目维护者 | 项目、仓库、基线、允许/保护路径、风险、并发和检查约束 |
| `binding.json` | 部署维护者 | 项目工单、已实现的运行时、执行协议及能力/容量声明 |
| `compiled.json` | 编译器生成 | 上述内容的不可变快照、各部分摘要、精确的旧版执行 spec |

凭据、Temporal 地址/namespace/队列、文件 ACL 和真实执行器在受信部署配置中设置，不交给任务或 prompt 决定。`binding.json` 必须由管理员安装；它的能力声明**不是运行时认证或测试结果**。部署前仍须验证执行器实际具备对应能力。

## 1. 从现有任务无损迁移

在解压后的部署包根目录执行（Python 3.10+；本模块只用标准库）：

```bash
PYTHONPATH=platform python -m dev_platform.portable convert-v2 \
  --request platform/task-types/repository-governance/examples/request.json \
  --project-id demo-project \
  --out-dir my-task-r1
```

生成 `task.json`、`policy.json`、`binding.json`、`compiled.json`、`task.spec.json`。生成的政策与绑定是待管理员审阅的草稿；该命令不会授权或启动任务。目标目录必须不存在，避免覆盖旧修订。

大型变更替换为 `platform/task-types/large-change/examples/request.json`。转换后 `task.spec.json` 与原请求通过旧注册表编译出的 spec 完全一致，包括请求/profile 摘要。

**现有运行不转换。** 已提交的 v1 训练任务、v2 开发任务、Temporal 历史及批准凭据保持原样。对下一次新提交使用新格式。训练模板仍走已有 v1 路径，本次不声称其运行时已通用化。

## 2. 使用拆分后的文件编译

仓库治理的完整样例已经提供；所有示例提交、项目和工单均为占位值，不能直接作为生产任务使用。

```bash
PYTHONPATH=platform python -m dev_platform.portable compile \
  --task platform/portable/examples/repository-governance/task.json \
  --package platform/portable/packages/repository-governance/manifest.json \
  --policy platform/portable/examples/repository-governance/policy.json \
  --binding platform/portable/examples/repository-governance/binding.json \
  --out my-task.compiled.json \
  --spec-out my-task.spec.json

PYTHONPATH=platform python -m dev_platform.portable validate my-task.compiled.json
```

`large-change` 有相同目录结构。修改政策后更新绑定的 `policy_sha256`；修改 package 必须发布新版本并更新任务和政策的 `package_sha256`。不要手工改摘要来绕过安装校验：编译器仍要求恢复出的 profile 与受信注册表完全一致。

返回 `VALIDATED_ONLY` 仅表示结构和规则通过，**不表示已批准执行**。所有输出以不可变文件发布；相同内容可重试，不同内容必须使用新任务修订和新路径。

## 3. 选择入口

### 通过现有 Symphony 入口

```bash
PYTHONPATH=platform python -m dev_platform.portable export-v2 \
  --compiled my-task.compiled.json \
  --out task-request.json
```

将 `task-request.json` 交给现有 [Symphony bridge 的准入与 outbox 流程](../symphony/README.md)。该命令输出精确的 v2 请求对象。桥接层仍校验可信仓库状态、准入凭据与请求原始字节摘要；不自动承认 `compiled.json` 为批准凭据。归档 `compiled.json` 作为旁路审查记录，并保持桥接层的外部仓库 policy revision 不变。该导出是兼容桥接：六层快照不会随旧 v2 请求进入 Symphony/Temporal 历史；旧工作流收到的是可执行的有效范围、检查、角色和限制。完整 portable envelope 摘要准入由 A2A 路径实现。

`request_sha256` 是规范化 JSON 请求摘要；Symphony outbox 准入还会计算文件**原始字节摘要**。二者不能混用。

### 通过 A2A 入口

将完整 `compiled.json` 交给 [A2A 网关](A2A.md)的受信准入命令，再由远程 agent 使用该任务的固定摘要提交或查询。远程调用者不能通过上传新政策获得权限。批准仍经现有可信人类入口，A2A 的任务状态不等于计划批准、合并许可或代码正确性证明。

### 受信操作员直接使用旧客户端

`my-task.spec.json` 可传给原有 `dev_platform.client`。这只是兼容路径；直接使用 Temporal 凭据拥有较大权限，不应向外部 agent 分发。日常团队入口使用 Symphony 或 A2A 准入。

## 4. JSON Schema 与 Python API

`portable/schemas/` 提供九个独立的 JSON Schema 2020-12 文件，可供编辑器、表单或其他语言工具校验，不需要远程解析 `$ref`。

```python
from dev_platform.portable import (
    read_json, load_package, compile_task, validate_compiled,
)

compiled = compile_task(
    read_json("task.json"),
    load_package("packages/repository-governance/manifest.json"),
    read_json("policy.json"),
    read_json("binding.json"),
)
validate_compiled(compiled)
```

`compile_task` 在准入时读取已安装的注册表。`validate_compiled` 仅验证冻结快照，不读最新注册表，升级后可以恢复旧任务。两者均不启动执行。

Schema 校验之后还需运行语义验证：摘要、路径前缀、依赖环、并行写入冲突、政策范围、角色独立性、能力、受支持工作流及大小上限。仅有 Schema pass 不够。

`packages/*/input.schema.json`、`output.schema.json`、README 和 instructions 保留旧模板原文，用于精确恢复旧 profile 摘要。**新任务表单使用 `portable/schemas/task.schema.json`**；不要误用旧的完整 v2 request schema。

## 5. 扩展边界

当前可运行目标：`temporal-development-v1` + `trusted-file-v1`；当前流程：`development-lifecycle@1`；当前模板：仓库治理、大型变更。声明其他引擎、任意阶段图或未知必需能力都会明确拒绝，不降级绕过检查。

新增任务类型继续遵循 [ADD_TASK_TYPE.md](ADD_TASK_TYPE.md)：注册受信 profile，再发布包含 workflow/roles/evidence/模板的 package，添加编译及行为测试。工作流结构变动、LangGraph/DSH 执行器接入或新的证据语义需要实现新编译目标与适配器，不是改一个 JSON 字段即可完成。

角色文件声明协作需求和限制；身份认证、权限、隔离工作区、网络边界与真实命令仍由受信 runner/CI 实现。现有运行时对固定候选、作者与 verifier/reviewer 的分离、必需产物和检查进行验证；角色文字本身不构成 OS 权限。

包内容校验使用本项目确定性 JSON 编码（UTF-8、排序键、紧凑分隔符、禁止非有限数），**不是声称实现 RFC 8785/JCS**。workflow/roles/evidence 的引用摘要基于该编码；四个原有模板文件的摘要基于原始 UTF-8 字节。跨语言实现必须用兼容编码与测试向量，或把本编译器作为边界服务。

## 6. 验证与运营

```bash
PYTHONPATH=platform python -m unittest discover \
  -s platform/tests -p test_portable.py -v
```

测试覆盖两个模板的无损迁移、纯快照恢复、注册表校验、内容/摘要篡改、范围扩张、基线/项目/工单错配、风险和容量限制、未知/缺失能力、角色独立性、工作流关口、路径穿越、符号链接、重复 JSON 字段、非有限数、大小上限、不可变输出和 Symphony 导出。

将受信 package、policy、binding 与网关准入数据库放在 agent 无写权限的目录；不要在候选工作区内使用可变文件作为权限来源。摘要只证明内容一致。可自行生成全部摘要的人也能构造自洽的伪造 envelope，所以启动前必须验证受信准入。
