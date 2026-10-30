# 把开发工作流接到你们的 Codex / CI 执行器

这份接口运行在受信任的云端控制主机。模型仍调用云端 Codex；不需要本地模型。
本包已经实现 Temporal 状态机、文件任务交换、证据校验和人工计划放行。它不包含你们的 Git 托管账户、Codex 身份、CI job 模板、SSO 或实际仓库测试命令。没有执行器消费任务时，工作流等待并在期限后阻断，不会假装检查通过。

## 1. 配置控制主机

从下载包根目录执行：

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r platform/requirements.txt
export PYTHONPATH="$PWD/platform"
export DEV_ADAPTER_CONFIG=/srv/dev-control/adapter.json
export DEV_TASK_QUEUE=development-tasks
export TEMPORAL_ADDRESS=YOUR_NAMESPACE.TMPRL_DOMAIN:7233
export TEMPORAL_NAMESPACE=YOUR_NAMESPACE
export TEMPORAL_API_KEY=YOUR_SECRET_FROM_SECRET_MANAGER
python -m dev_platform.worker
```

把 `platform/adapter.example.json` 复制到受信任配置目录，再设置五个互不嵌套的绝对目录。设置 `trusted_receipts: true` 表示部署者确认下表的 ACL；这个布尔值不会替你配置 ACL。

| 目录 | 写入者 | 读取者 | 内容 |
|---|---|---|---|
| `requests` | Temporal worker | 可信执行器 | 不可变 stage 请求 |
| `receipts` | 可信执行器 / CI 网关 | worker | 不可变终态回执 |
| `artifacts` | 可信执行器 / CI | worker、审阅者 | 日志、差异、计划、报告 |
| `approvals` | 人工审批网关 / 运维 | worker | 身份已核验的计划批准回执 |
| `fences` | worker / 运维 | 执行器 | 禁止该任务继续产生副作用 |

代码 agent 不能写 `receipts`、`approvals`、`fences`，不能修改安装的 profile/校验器，也不能持有 Temporal namespace 密钥。请求、审批和回执中出现的名字本身都不是认证；这些数据的可信度来自网关认证、目录 ACL 和执行器独立身份。采用对象存储或数据库时，把 `FileAdapter` 的四个异步方法替换为你们的原子实现，保持同样的幂等和绑定语义。

## 2. 消费一项 stage 请求

worker 创建：

```text
requests/<task_id>/<job_id>.json
```

包络字段：

```json
{
  "schema_version": 1,
  "job_id": "task-001-...",
  "job_sha256": "sha256-of-canonical-context",
  "context": {
    "task_id": "task-001",
    "request_sha256": "...",
    "profile_sha256": "...",
    "spec": {"request": {}, "profile": {}, "request_sha256": "...", "profile_sha256": "..."},
    "stage": "work:api",
    "expected_candidate_sha": null,
    "unit": {"id": "api", "depends_on": [], "paths": ["src/api"], "instructions": "..."},
    "dependencies": {},
    "author_ids": [],
    "author_sessions": [],
    "job_id": "task-001-..."
  }
}
```

上例是字段说明，省略号不是可提交的样例；有效任务样例见 `task-types/*/examples/request.json`。

执行器必须完成以下步骤：

1. 校验 `job_sha256` 为 `context` 的规范 JSON SHA256，核对安装的 profile 与请求 scope。只允许固定 stage 对应的执行模板；不要把任务正文插入 shell。
2. 以 `job_id + job_sha256` 做持久化、原子的去重登记。同一个 job 重复投递必须返回原来的外部 job，不再启动模型或 CI。提交结果未知时先对账。
3. 原子检查 `fences/<task_id>.json` 与自己的 job 登记。已被 fence 的任务不能启动新副作用；运行中的 job 收到 fence 后请求取消，并等候真实终态。独立配置执行器硬时限。
4. 每个 `work:<unit>` 建立独立 checkout/worktree。核对初始 `repository.starting_sha`；依赖项的精确提交在 `context.dependencies` 中。有依赖的 unit 先整合父任务提交，再执行本单元。不能让多个 agent 共用可写 checkout。
5. 计划放行后的 `work`、`integrate`、`verify` 和 `review` 请求都包含 `context.approved_plan`：精确 `plan_sha256`、包含工件引用的完整计划回执 `receipt`、以及受信任批准引用 `approval`。执行器应读取这一已批准计划，按其接口与实现约束开展工作；不能只读取最初的任务正文。该字段参与整个 job context 的哈希，替换计划会使原 job 回执失效。只向 agent 提供当前 stage、必要路径、相关依赖和安装的模板。设置明确的工具权限、最大轮次和费用限额。代理内容与仓库文本不能修改受信任的执行模板。
6. 可信运行器记录角色、经过认证的 principal 和本次会话 ID。身份字段由运行器生成，不从 agent 自述中复制。独立审阅者应使用新的会话和独立身份；还应检查 Symphony 初始作者等外部作者身份——工作流只能比较已记录的 stage 作者。
7. 在允许的云端 Git/CI 身份下保存提交和工件。工作流只核对回执绑定与工件哈希；可信 CI 负责执行真实命令、确认 SHA 可获取、检查实际 Git diff 与路径权限。
8. 发布不可变终态回执。发布后发现结果错误，应停止该任务并建立新 revision，不能原地改写旧证据。

| stage | 必须由执行器完成的操作 | 产出提交 |
|---|---|---|
| `inventory` | 读取仓库地图、运行已有检查、识别历史失败与风险；记录可复现行为基线 | 必须等于 starting SHA |
| `plan` | 输出范围、单元 DAG、所有权、接口/兼容策略、回滚方案；不能扩大原任务范围 | 必须等于 starting SHA |
| `work:<id>` | 在单元独立工作区实现、做局部检查；用依赖项的精确提交构建上下文 | 单元提交 |
| `integrate` | 汇总已完成单元；冲突交给固定集成角色解决，再生成一个可重现集成提交 | 最终 candidate SHA |
| `verify` | 受信任 CI 对最终 candidate 执行 profile 的所有 required checks；与原基线比较 | 必须等于最终 candidate |
| `review` | 新会话检查最终 diff、测试质量、边界、简洁性、维护性和验收证据 | 必须等于最终 candidate |

`plan` 阶段只能完善已冻结的 work-unit DAG，不能直接替换 DAG。若需要增删单元、扩大路径、改变验收或基线，停止当前任务，创建新 task revision 并重新准入。这样批准的范围不会被长任务静默改变。

## 3. 发布 stage 回执

回执形状：

```json
{
  "schema_version": 1,
  "job_id": "EXACT_PUBLISHED_JOB_ID",
  "job_sha256": "EXACT_PUBLISHED_CONTEXT_SHA256",
  "state": "SUCCEEDED",
  "actor": {"id": "ci-verifier", "session_id": "UNIQUE_AUTHENTICATED_RUN", "role": "verifier", "kind": "ci"},
  "candidate_sha": "FULL_GIT_COMMIT",
  "artifacts": [{"name": "check-results", "path": "task-001/verify/report.json", "sha256": "ARTIFACT_SHA256"}],
  "checks": [{"id": "scope", "status": "pass", "artifact": "check-results"}],
  "detail": "Exact command versions and logs are in the report"
}
```

先把实际工件写入 `artifacts` 对应相对路径，再由可信 CI 运行：

```bash
python -m dev_platform.adapter --config /srv/dev-control/adapter.json publish-receipt /srv/dev-platform/requests/TASK/JOB.json /srv/ci-results/receipt.json
```

工件必须是普通文件、相对规范路径、无符号链接，每个最多 16 MiB；更大日志拆分，保留索引。回执元数据最多 32 KiB，stage context 最多 1,000,000 字节，冻结 spec 最多 256 KiB；这些限制在发往 Temporal 前检查，避免 DAG 汇总超过载荷上限。大段日志只放到工件，不放进回执字段。每个 check 都要指向已哈希工件；缺失、跳过、未知状态或任一失败都不能放行。`verify` 的 `checks` 必须覆盖 profile 的 `required_checks`；`review` 还必须有 `independent-review: pass`。不适用的迁移检查也要用可信证据确认“不涉及迁移”，不能通过删除 check 绕过门禁。

这些校验能防止证据错绑、缺失和被改写，不能把伪造日志变成真实测试。回执写入权只能给独立可信执行器。不要授予实现 agent “自己提交通过结果”的权限。

## 4. 人工批准计划

查询状态取得精确 `plan_sha256`：

```bash
python -m dev_platform.client status task.spec.json
```

由已经完成身份与权限核验的审批网关生成以下 JSON；有效期最长 7 天：

```json
{
  "schema_version": 1,
  "kind": "plan-approval",
  "task_id": "TASK_ID",
  "request_sha256": "EXACT_REQUEST_HASH",
  "profile_sha256": "EXACT_PROFILE_HASH",
  "plan_sha256": "EXACT_PLAN_RECEIPT_HASH",
  "decision": "approve",
  "principal_type": "human",
  "actor_id": "AUTHENTICATED_OWNER",
  "role": "owner",
  "expires_at": 0,
  "revoked": false
}
```

`expires_at` 要替换为真实未来 Unix 秒值；示例中的 0 会被拒绝。批准的是任务、profile 与计划的组合，不是“这张工单以后所有修改”。

```bash
python -m dev_platform.adapter --config /srv/dev-control/adapter.json publish-approval APPROVAL_ID /srv/approvals/approval.json
python -m dev_platform.client approve task.spec.json --receipt-id APPROVAL_ID --plan-sha256 EXACT_PLAN_HASH
```

回执不存在、过期、撤销、角色错误或哈希不符都会被拒绝。修正后使用新的 approval ID；工作流仍使用最初的审批截止时间。已接受的计划批准不会自动被重新检查；需要撤回时，应发取消信号并撤销执行器授权。

## 5. 超时、取消和最终交接

```bash
python -m dev_platform.client cancel task.spec.json --reason "目标或范围已经改变"
python -m dev_platform.client result task.spec.json
```

- `REVIEW_READY`：检查与独立审阅完成；人查看摘要/差异/风险并通过托管平台进行合并。合并前按当前目标分支重跑必要检查；状态机没有合并/部署步骤。
- `BLOCKED`：任务未达到验收；已发布 job 的可信终态已可对账，没有声称成功。
- `CANCEL_UNCONFIRMED`：已写 fence，但仍有 job 没有可信终态回执；运维对账列出的精确 job。不能仅凭 fence 文件声称远端已停止。
- `NEEDS_RECONCILIATION`：控制面故障导致连 fence 都无法确认；停止继续准入相同任务，人工对账。

默认每个 stage 1 小时、计划批准 24 小时。时限从发布成功确认后开始，因此外部执行器仍需自己的硬时限。运行期重启后 Temporal 重放历史；活动重试只重复短控制操作，外部 job 的去重由执行器持久化账本保证。不要同时让 Symphony、Temporal 与 CI 无限重试同一段实现。

## 已验证范围

`tests/test_workflow.py`：20 个单元/边界测试 + 8 个真实 Temporal 临时服务集成测试。集成测试使用显式 synthetic 文件执行器，未调用 Codex 或企业 CI。验证了实际并行 DAG、计划批准、SHA 与工件绑定、独立审阅、失败传播、审批到期、取消 fence 和未确认取消。真实模型质量、CI 命令与组织 ACL 需要在你们的试点仓库验收。

```bash
RUN_TEMPORAL_INTEGRATION=1 PYTHONPATH=platform python -m unittest discover -s platform/tests -p test_workflow.py -v
```
