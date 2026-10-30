# Temporal 与 perfctl 接入对照

这两份模板当前**不能原样互通**。`perfctl.py` 使用 `candidate_commit` / `baseline_commit`；Temporal 的 `submit_or_lookup` 要求 manifest 含 `candidate_sha` / `baseline_sha`。本文件给出明确的适配协议，没有声称已有生产 adapter，也不改变现有代码与测试。

## 1. 最小字段映射

|含义|perfctl manifest / gate 输出|Temporal|必须核验|
|---|---|---|---|
|实验身份|`experiment_id`|`binding.experiment_id`|完全相等；建议使用两者共同支持的 `[A-Za-z0-9][A-Za-z0-9_-]{0,79}`|
|候选完整 Git commit|`candidate_commit`|`binding.candidate_sha`；manifest `candidate_sha`|三个值完全相等；不接受 branch 名|
|基线完整 Git commit|`baseline_commit`|`binding.baseline_sha`；manifest `baseline_sha`|三个值完全相等|
|基线版本|`baseline_id`|保留在 manifest 中|不能用 commit 替代；perfctl 还验证 config 与 workload|
|manifest 原始字节 hash|evidence / gate 输出 `manifest_sha256`|`binding.manifest_sha`|采用下述单一源方案时必须相等；hash 不是 JSON 对象的抽象内容 hash|
|证据索引原始字节 hash|gate 输出 `evidence_sha256`|`GateDecision.evidence_sha`、release `evidence_sha`|指向同一 `evidence.json` 的 SHA-256；其 artifacts 数组再绑定子文件 hash|
|门禁结果|`ELIGIBLE_FOR_HUMAN_REVIEW`|`GateDecision.passed=True` 的必要条件|仍需可信 runner 的来源核验；此值不是人工批准|
|结果位置|archive 输出 `archive_path`|`GateDecision.report_uri`|本地路径先转成允许且不可变的 artifact URI；不把 worker 本地路径假装成云端链接|
|调度模板/时限|原 perfctl schema 未要求|`runner_template_id`、`max_run_seconds`|由批准模板产生；manifest与Experiment的排队+执行总窗口一致；scheduler执行硬walltime独立设置|

`manifest_sha` 不能等于候选 commit；`evidence_sha` 不能随意换成 `gate-result.json` 的 hash。每种 hash 都有独立的字节对象。

## 2. 推荐：一个不可变 manifest，同一组原始字节

保持 perfctl 的字段为唯一业务源；在**注册与启动之前**，由受控 adapter/finalizer 自动生成 Temporal 别名和调度字段。最终文件同时包含两套名称，但只维护一套输入。不要让人手工更新两份 commit 值。

```python
# 示意：放在受控提交网关；不是当前模板已实现的 adapter。
import hashlib, json
from pathlib import Path

m = json.loads(Path('perfctl-draft.json').read_bytes())
# draft 须先通过批准的 contract/权限校验；下列值来自 runner 模板配置。
runner_template_id = 'approved-wam-h200-v1'
max_run_seconds = 21600
for canonical, alias in [('candidate_commit', 'candidate_sha'),
                         ('baseline_commit', 'baseline_sha')]:
    if alias in m and m[alias] != m[canonical]:
        raise ValueError('Conflicting commit alias: ' + alias)
    m[alias] = m[canonical]
m['runner_template_id'] = runner_template_id
m['max_run_seconds'] = max_run_seconds

raw = (json.dumps(m, ensure_ascii=False, sort_keys=True,
                  separators=(',', ':')) + '\n').encode('utf-8')
with Path('manifest.json').open('xb') as frozen:  # 已有文件即拒绝，不能覆盖。
    frozen.write(raw)
manifest_sha = hashlib.sha256(raw).hexdigest()
binding = dict(experiment_id=m['experiment_id'], manifest_sha=manifest_sha,
               candidate_sha=m['candidate_commit'], baseline_sha=m['baseline_commit'])
# 上传 raw 的原始字节；用 binding、其不可变 URI、相同 max_run_seconds 创建 envelope。
# max_run_seconds 包含提交确认后的排队；scheduler执行硬walltime由runner模板独立设置。
```

这里的序列化只是首次确定字节的办法。冻结后，无论缩进、换行、字段顺序还是内容变化都会产生新 hash；不能重新格式化后继续使用旧 experiment_id/hash。

当前 `perfctl.validate()` 允许额外字段，因而上述最终文件可交给 `perfctl register`；注册保留文件原始字节。Temporal `read_manifest` 必须返回**这一文件的原始字节**，不能返回临时转换后的另一份 JSON。runner 生成 evidence 时，`manifest_sha256` 也取同一文件的 hash。

接入 adapter 的 `create_job_if_absent` 必须再次执行以下检查，不能只依赖提交网关：

```python
m = json.loads(manifest_bytes)
if not (m['candidate_commit'] == m['candidate_sha'] == experiment.binding.candidate_sha
        and m['baseline_commit'] == m['baseline_sha'] == experiment.binding.baseline_sha
        and m['experiment_id'] == experiment.binding.experiment_id):
    raise ValueError('Manifest alias or binding mismatch')
# 继续核验 schema、批准模板、contract、权限、SHA、walltime，再进入原子幂等提交。
```

此额外检查是**待实现的桥接要求**：当前 Temporal activities 检查 sha 字段与 binding；当前 perfctl 检查 commit 字段；它们各自都不会自动检查两种字段的相等关系。验证失败必须拒绝提交。

## 3. 已有 perfctl manifest 不可改动时：显式外层 envelope

不要给已经注册的 manifest 临时加字段。保留原文件 `M`，hash 为 `H_M`。创建新的 Temporal 外层 manifest `T`，含 Temporal 所需字段，以及 `perfctl_manifest_uri` / `perfctl_manifest_sha256=H_M`；Temporal binding 的 `manifest_sha=SHA256(T原始字节)=H_T`。

此方案中 `H_T != H_M` 是正常的，不能要求 perfctl gate 返回 `H_T`。生产 adapter 必须同时验证：

1. Temporal activities 验证 T 的字节 hash 为 H_T。
2. adapter 获取 M 并验证 H_M、experiment_id、candidate/baseline commit 与 T/binding 相等；检查实际 scheduler walltime/模板授权。
3. perfctl 注册 M、检查 evidence 的 `manifest_sha256=H_M`；gate 结果也是 H_M。
4. 持久 runner ledger 与审批证据同时保存 `H_T → H_M` 的不可变关系；release receipt 绑定 Temporal binding、evidence hash，并让审批页面展示被引用的 M。

现有模板没有自动完成这些双 hash 检查。这个方案适合迁移已存在实验；新实验优先采用上一节的单一源方案。仅将字段重命名后继续沿用旧 hash 是错误做法。

## 4. collect_and_gate 的具体接入顺序

perfctl 是单个 coordinator 主机上的离线证据 registry。其 `flock` 不是分布式锁，也不支持多个 worker 各用自己的 `.perf-state` 冒充共享权威源。把它放在一个受控验证服务/runner 上，通过该服务序列化访问并保存持久快照；Temporal worker 只调用该服务或读取受控结果。

首次设置 registry、冻结实验后，在受控 runner 上执行：

```bash
# PERF_STATE 是已有批准的持久 registry 目录；BASELINE 与 MANIFEST 为受控文件路径。
python perfctl.py --root "$PERF_STATE" init --baseline "$BASELINE"  # 仅初始化一次
python perfctl.py --root "$PERF_STATE" validate "$MANIFEST"
python perfctl.py --root "$PERF_STATE" register "$MANIFEST"

# runner 完成测试、独立review、集成验证、对照测量与必要质量评估，生成 evidence bundle 后：
python perfctl.py --root "$PERF_STATE" archive "$EXPERIMENT_ID" --bundle "$EVIDENCE_JSON"
```

`archive` 自带重新执行 gate、重算 comparison、快照和归档步骤；无须先 `gate` 再 `archive` 重算两遍。比较器路径在 perfctl 中固定为同目录 `compare_runs.py`，其 hash 必须与批准 manifest 的 `comparison_tool_sha256` 相符；不能运行 agent 临时上传的任意比较器。

生产 `collect_and_gate(job)` 的处理顺序：

1. **找回身份**：用精确 job/group ID 从可信 ledger 读 binding、冻结 manifest、artifact 来源；不能信任 agent 提供的临时路径。
2. **验证产物与来源**：校验 runner/service 身份、artifact 访问边界、原始 manifest hash、candidate/baseline、validator/comparator 版本。保存 runner identity、job ID 与结果的关联。hash 只能证明字节未变，不能证明这些字节真的来自集群运行。
3. **完成可信门禁**：在受控验证 runner 执行上述 `archive`，检查进程退出码、解析完整 JSON、核验字段绑定。退出非零、缺少证据、基线漂移或状态不是 `ELIGIBLE_FOR_HUMAN_REVIEW` 都不能放行。
4. **归档结果**：把 `archive_path` 下证据及 gate 报告上传到允许的不可变存储，保留同一 `evidence.json` 原始字节；如需要生成额外 provenance receipt，不能悄悄替换 evidence hash 的含义。
5. **短 activity 返回**：再次校验 gate 的 `experiment_id`、candidate、baseline_id、manifest hash、evidence hash 及可信来源后，返回 `GateDecision(job=job, passed=True, evidence_sha=gate['evidence_sha256'], report_uri=..., summary=...)`。false 情况使用可追溯的失败证据记录与其 hash，不能用占位 hash 伪造成功归档。

这不是要求把上面所有工作都塞进一次 activity。本模板 adapter 调用上限20秒，activity 上限30秒。对于大 evidence 或慢比较：在现有 runner 的实验组中安排单独的 CPU 验证/归档步骤；adapter 的 `poll_job` 只在组内训练与证据准备技术上完成时报告 SUCCEEDED，`collect_and_gate` 仅短读已经准备的可信结果。性能门禁不合格应有结构化失败结果；基础设施失败则按失败/待核对处理。不要把长 subprocess 包在 activity 里，也不要偷偷新增另一层 GPU 重试。

perfctl 要求 evidence 中已有 `integration` 证明：这里指候选相对冻结基线的合并/集成测试。Temporal 的人工 release 之后创建的是**正式集成审核/必要复验工单**；它可以因为当前基线变化而要求重跑。两者不是同一审批，更不能用后一张尚未创建的工单伪填前一项证明。

## 5. ELIGIBLE、真实性与人工审批边界

`ELIGIBLE_FOR_HUMAN_REVIEW` 表示本工具检查的记录、hash、绑定和重算性能策略满足进入人工审核的条件。它不等于“代码正确”“训练质量已被证明”“作者身份真实”“允许 merge”或“允许部署”。

- perfctl 的 `contract_approved=true`、`reviewer_id` 与结构化 PASS 本身没有 SSO 身份认证能力。可信 CI/独立 reviewer 服务必须控制产出与签发权限，阻止同一实施 agent 同时伪造实验、审查者和审批记录。
- `GateDecision.passed=True` 只推进到 AWAITING_RELEASE。真实审批仍由外部 SSO/RBAC 系统签发 receipt；`authorize_release_and_create_task` 核验角色、binding、evidence、时效/撤销和当前基线，再幂等建工单。
- 明确审批拒绝且尚未产生建单副作用时，adapter抛出专用 `ApprovalRejected`；workflow在原deadline内等待新的receipt，不重跑GPU。网络故障/不确定副作用不能冒充审批拒绝。
- 当前基线、配置或 workload 变化时不能沿用旧批准。perfctl gate 与 receipt 核验阶段都应检查；工单真正合入时仍有最后的 CI/复验门禁。
- Temporal、perfctl、artifact store 各有职责：Temporal 维护实验生命周期；perfctl 生成可复核的证据门禁结果；runner ledger 维护外部 job 幂等；审批服务负责身份和授权。一个 agent 写出的 Markdown 或 JSON 不能覆盖这些事实。

本文按同包的 `perfctl.py`、`compare_runs.py`、`perf_temporal/activities.py` 与 `adapter.py` 实际接口编写。这里只新增接入说明，未实现你的集群/身份/存储 adapter，未改变现有测试结果。
