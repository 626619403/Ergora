# A2A 接入：外部 agent 委派开发任务

本版本提供可运行的 **A2A 1.0 JSON-RPC 网关与官方 SDK 客户端**。它把已经批准接入的任务交给现有 Temporal 开发工作流，支持发现、提交、查询、列表、取消和恢复。它不会自动接入你的 Codex/CI 执行器、账户或生产环境。

A2A 是传输协议；`urn:dev-platform:a2a:admitted-task:1` 是本项目的业务载荷约定，并非 A2A 官方通用任务标准。外部 ADK、LangGraph、Microsoft Agent Framework 或其他平台只要能调用 A2A 1.0，并发送这个约定的数据，便可委派整个开发任务。当前未实现把每个内部角色分别替换成远程 A2A agent。

## 1. 准备运行环境

在受信控制机上安装，使用云端模型。不要把网关数据库、Temporal 凭据、批准目录挂进 coding agent 工作区。

```bash
python3 -m venv .venv
.venv/bin/pip install -r platform/requirements-a2a.txt
export PYTHONPATH="$PWD/platform"
cp platform/a2a.example.json a2a.production.json
```

修改配置：

| 字段 | 操作 |
|---|---|
| `ledger` | 网关独占的持久 SQLite 文件；父目录必须属于运行用户且为 `0700` |
| `shared_ingress_db` | 与 Symphony 配置指向**同一个绝对路径**；跨入口互斥，不会自动过期 |
| `public_url` | 对外 HTTPS 根地址；反向代理转发 `/.well-known/agent-card.json` 与 `/a2a` |
| `host` / `port` | 保持 loopback 监听；TLS 在受信反向代理终止 |
| `principals` | 调用者身份 → 独立 secret 的环境变量名；不要写入明文 secret |

配置 Temporal Cloud 的 `TEMPORAL_ADDRESS`、`TEMPORAL_NAMESPACE`、`TEMPORAL_API_KEY`；开发任务队列使用 `DEV_TASK_QUEUE`，默认 `development-tasks`。按照 [平台部署](README.md) 启动工作流 worker 和真实执行器。

为每个调用者设置独立、至少 32 字符的随机 secret，例如在 secret manager 中生成并注入 `A2A_TEAM_ORCHESTRATOR_TOKEN`。客户端使用同一调用者的 secret；服务端不会信任请求 JSON 中自报的身份。

单实例、单进程运行，SQLite 放本机持久磁盘；不支持 NFS、多副本活跃网关或多主数据库。服务器持有独占进程锁；不要通过增加 uvicorn workers 扩容。跨主机部署需先替换为事务型共享存储和分布式所有权实现。网关所有权同时绑定私有数据库的持久 UUID 和固定路径；不要在有活动任务时移动数据库、复制为第二个活动实例或删除后重建。更换数据库不会自动继承旧所有权。

## 2. 编译可移植任务

新任务按 [PORTABILITY.md](PORTABILITY.md) 分别配置 task、package、policy、binding。迁移现有 v2 请求可用：

```bash
.venv/bin/python -m dev_platform.portable convert-v2 \
  --request request.json --project-id my-project --out-dir task-r1
.venv/bin/python -m dev_platform.portable validate task-r1/compiled.json
```

转换输出 `task.json`、`policy.json`、`binding.json`、`compiled.json` 和旧运行时可用的 `task.spec.json`。转换产生的 policy/binding 是供负责人审阅的草案；验证哈希不等于授权。修改任一部分后必须重新编译、重新接入该摘要；不要覆盖正在运行的实例。

## 3. 受信管理员接入任务

管理员审阅目标、范围、项目策略、运行时绑定与具体提交后，为特定调用者接入完整编译结果。有效期最多七天；同一任务 ID 的内容、所有者和有效期不可修改。

```bash
.venv/bin/python -m dev_platform.a2a_gateway admit \
  --config a2a.production.json \
  --compiled task-r1/compiled.json \
  --principal team-orchestrator \
  --expires-at 'YYYY-MM-DDTHH:MM:SS+00:00'
```

请用实际未来时间替换示例占位符。命令输出 `{ "task_id": "…", "compiled_sha256": "…" }`，这是外部 agent 需要的引用。它没有批准后续执行计划，更不代表允许合并。

首次接入会重新对照当前安装的受信注册表编译核验；已接入实例的恢复只校验其冻结快照，不受后续模板升级影响。接入后的输入被冻结在私有数据库。外部 agent 无权替换 package、policy、binding，或给服务器下发任意命令、URL、脚本。已经开始的任务不会因接入有效期届满而失去查询/取消能力；尚未提交运行时的过期任务不能启动。

## 4. 启动网关并调用

```bash
.venv/bin/python -m dev_platform.a2a_gateway serve --config a2a.production.json
```

在客户端注入 `A2A_CLIENT_TOKEN` 后调用：

```bash
.venv/bin/python -m dev_platform.a2a_gateway send \
  --url https://agents.example.com \
  --task-id TASK_ID --compiled-sha256 COMPILED_SHA256 \
  --message-id my-orchestrator-request-001

.venv/bin/python -m dev_platform.a2a_gateway get \
  --url https://agents.example.com --a2a-task-id RETURNED_A2A_TASK_ID

.venv/bin/python -m dev_platform.a2a_gateway list \
  --url https://agents.example.com --page-size 50

.venv/bin/python -m dev_platform.a2a_gateway cancel \
  --url https://agents.example.com --a2a-task-id RETURNED_A2A_TASK_ID
```

`task_id` 是业务任务 ID；返回的 A2A `id` 和 `contextId` 由服务端分配。`GetTask`、`CancelTask` 使用返回的 A2A ID。保留 `messageId` 可安全重试同一个请求；更换消息 ID、但引用同一个已接入任务，仍不会创建第二次运行。

客户端固定使用 A2A 1.0 JSON-RPC，校验 Agent Card 中的调用地址与指定网关同源，禁止重定向携带 secret；默认不读取系统 HTTP 代理环境变量。需要代理时应由维护者显式接入受信 HTTP 客户端。

其他框架可直接发送：

```json
{
  "jsonrpc": "2.0",
  "id": "rpc-1",
  "method": "SendMessage",
  "params": {
    "message": {
      "messageId": "stable-message-1",
      "role": "ROLE_USER",
      "parts": [{"data": {"task_id": "TASK_ID", "compiled_sha256": "COMPILED_SHA256"}}]
    },
    "configuration": {"returnImmediately": true, "acceptedOutputModes": ["application/json"]}
  }
}
```

请求头：`Authorization: Bearer …`、`A2A-Version: 1.0`、`Content-Type: application/json`。不要使用 0.3 的 `message/send` 方法名。请求体最多 64 KiB，拒绝重复 JSON 键、非有限数值和压缩请求。建议调用方使用非阻塞提交并轮询；未设置 `returnImmediately` 时，连接等待任务终止或进入需要人工输入的状态。

## 5. 状态与人的参与

| A2A 状态 | 平台含义 | 后续操作 |
|---|---|---|
| `SUBMITTED` / `WORKING` | 已接收或执行中 | 轮询 `GetTask` |
| `INPUT_REQUIRED` + `AWAITING_PLAN_APPROVAL` | 等待当前请求和计划摘要对应的可信人类批准 | 使用原有批准收据与 `dev_platform.client approve`；不通过普通 A2A 消息批准 |
| `INPUT_REQUIRED` + reconciliation phase | 启动、工作流状态或外部停止不确定 | 人工排查；保留任务/工单所有权 |
| `COMPLETED` | 仅表示 `REVIEW_READY`，验证和审查绑定同一候选 SHA | 人审并进入既有合并队列；metadata 始终 `merge_authorized=false` |
| `CANCELED` | 收到取消请求且确定未启动/外部工作已停止 | 可使用新修订重做 |
| `FAILED` | 任务已阻塞且外部工作确认停止 | 修正后新建任务修订 |

取消请求会持久保存。若停止尚未确认，`CancelTask` 返回 `TaskNotCancelableError`，调用者继续 `GetTask` 查看状态；**不会把收到取消信号误报为取消成功**。终止的 A2A 任务不能接收新的显式续接消息；新工作使用新业务任务 ID。

最终 `artifacts` 返回 SHA 绑定的候选交付清单：业务任务、编译摘要、请求摘要、候选提交、证据摘要及各产物摘要。网关不向外暴露本机路径、凭据、原始日志或任意下载 URL；通过团队受信证据服务按清单取回产物。

## 6. 重启、取消与人工恢复

网关每 15 秒对已有任务执行一次有界后端查询，恢复已提交运行、读取状态并释放已确认完成的共享所有权。客户端断开不影响 Temporal 工作流继续执行。查询 API 也会刷新状态；列表显示最近持久化的状态。

提交前记录 `SUBMITTING`。若响应丢失，只查询并附着到原来的、输入完全一致的工作流，绝不盲目创建第二个运行。未知状态、缺失的共享所有权、原始输入不一致均保留所有权并要求人工处理。

已经结束的 Temporal 运行若返回 `CANCEL_UNCONFIRMED`，其结果不会自行变成成功。维护者必须先停止外部工作、独立检查所有执行器、保存证据，再执行受信恢复：

1. 停止网关进程；恢复命令需要同一独占进程锁。
2. 按 [a2a-cleanup.example.json](a2a-cleanup.example.json) 填写真实任务/运行绑定、证据摘要和最近 24 小时的确认时间。`evidence_uri` 使用不含凭据和查询参数的 HTTPS 地址。
3. 执行命令，随后重启网关。

```bash
.venv/bin/python -m dev_platform.a2a_gateway reconcile \
  --config a2a.production.json \
  --a2a-task-id RETURNED_A2A_TASK_ID --proof cleanup.json
```

恢复同时要求：管理员的精确清理声明 + 后端验证同一原始输入、同一 run ID 已终止。原始网关快照与清理声明保存在不可替换的恢复审计记录中。网络超时或 `NotFound` 不能作为停止证据；此时先恢复可查询的权威运行记录，不能借恢复命令清空所有权。

## 7. 当前互操作范围

| 能力 | 状态 |
|---|---|
| A2A 1.0 Agent Card + JSON-RPC Send/Get/List/Cancel | 已实现，官方 SDK 验证 |
| 单任务持久去重、原始输入绑定、跨入口工单互斥 | 已实现，SQLite + 共享 ingress ledger |
| Temporal 实际后端 | 已实现，复用 Symphony 的共享运行时适配器 |
| 调用另一个同约定网关的客户端 | 已实现 |
| SSE、订阅、推送、REST/gRPC binding、0.3 兼容 | 未启用；按协议返回不支持 |
| 多租户路由、公开匿名接单、远程自动批准、自动合并 | 未实现；拒绝或不提供入口 |
| 多副本高可用、每角色远程 A2A 执行器 | 后续适配，不宣称已经具备 |
| 任意第三方 Agent Card 即可执行本模板 | 不保证；双方仍需约定任务数据、能力和证据语义 |

## 8. 验证与来源

```bash
PYTHONPATH=platform .venv/bin/python -m unittest discover \
  -s platform/tests -p 'test_a2a*.py' -v
```

本实现没有宣称通过完整 A2A 官方认证；互操作范围以上表为准。

基础 HTTP 测试使用实际 A2A SDK、实际可移植编译器、共享 ingress ledger，并分别通过 ASGI 与 loopback TCP 验证；其中工作流后端有明确标记的测试替身。真实 Temporal 端到端测试另见 `tests/test_a2a_temporal.py`；设置 `RUN_TEMPORAL_INTEGRATION=1` 后运行同一命令即可启用，首次需要下载 Temporal 测试服务。测试没有调用真实模型或生产 CI；它们验证协议、状态和边界，不证明业务代码已经正确。

- [A2A 1.0.1 规范](https://a2a-protocol.org/v1.0.1/specification/)
- [官方 Python SDK 1.2.3](https://github.com/a2aproject/a2a-python/releases/tag/v1.2.3)
- [Google ADK A2A 文档](https://google.github.io/adk-docs/a2a/)
- [LangSmith Agent Server A2A 支持与边界](https://docs.langchain.com/langsmith/server-a2a)
- [共享入口所有权协议](INGRESS.md)
- [真实执行器交接协议](EXECUTOR_PROTOCOL.md)
