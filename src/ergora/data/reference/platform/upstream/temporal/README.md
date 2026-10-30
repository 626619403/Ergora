# Temporal Cloud 实验编排最小模板

这是一份可安装、可测试、待接入现有集群的 Python 脚手架。它没有训练集群、GPU scheduler、artifact store、审批系统或工单系统的凭据，也没有把这些外部服务伪装成已完成。未配置 adapter 时 worker 启动即失败。

与同包 `perfctl.py` 配合时，先读 [PERFCTL_BRIDGE.md](PERFCTL_BRIDGE.md)：两者 manifest 字段当前不相同，需要显式转换与 hash 绑定，不能原样直接互通。

**Temporal Cloud 保存工作流历史并调度任务；Python worker 仍需由你运行。** 把 worker 放在公司批准、能访问现有集群控制面的 CPU runner/容器上。GPU 任务由现有 Slurm/Kubernetes/内部平台执行；模型调用仍可使用云端 API，不需要本地部署模型。

## 控制流程

`不可变实验身份 → 幂等提交/找回 job → 短轮询 activity + durable timer → 收集并门禁 → 等待绑定审批 → 只创建集成/复验任务`。

- `workflow_id = perf-experiment/{experiment_id}`，显式拒绝重复 ID。客户端超时后查这个 ID，不能生成新 ID 再提交。
- binding 是 `experiment_id + manifest_sha + candidate_sha + baseline_sha`；manifest SHA-256 基于原始字节。
- activity 每次最多30秒，adapter调用20秒，Temporal控制最多3次短调用重试。GPU任务本身不放进长activity。
- `max_run_seconds` 保留旧字段名，明确表示**提交/lookup确认后 QUEUED + RUNNING 的总等待窗口**，包含排队；它不是GPU实际执行时长。scheduler的执行硬walltime由批准的runner模板独立设置，不能依赖workflow timer代替。
- `submit_or_lookup` 每次先 lookup；adapter 必须支持真正原子的 create-if-absent/幂等 registry。只写“先查再 sbatch”有并发/响应丢失漏洞，不满足协议。
- GPU作业失败不自动重跑。Temporal是唯一重试负责人；LangGraph、Symphony、scheduler、agent不得再套一层重提交循环。
- 取消按当前实验的精确 scheduler job/group ID执行，包含其分布式rank。adapter先原子 fencing，避免延迟提交在取消后生成孤儿任务。
- release绑定上述identity及`evidence_sha`，然后adapter向独立审批系统核验receipt。成功只创建ticket，绝不自动merge、部署或启动生产训练。

## 1. 安装

核验日期：2026-10-26；使用实际安装测试的 SDK `temporalio==1.34.0`，Python 3.12。建议部署镜像锁定所有传递依赖并保存镜像digest；此 `requirements.txt` 只固定直接SDK依赖。

```bash
cd /path/to/perf-build/temporal
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Temporal Cloud 配置

从 Temporal Cloud console 复制 Namespace 的 **gRPC endpoint** 和完整 Namespace 名。官方示例通常是 `<namespace>.<account>.tmprl.cloud:7233` 与 `<namespace>.<account>`；不要把 Cloud Operations 管理 API endpoint 当作 workflow endpoint。

```bash
export TEMPORAL_ADDRESS='从Cloud复制的gRPC主机:7233'
export TEMPORAL_NAMESPACE='从Cloud复制的完整namespace'
export PERF_TASK_QUEUE='perf-experiments-v1'
export PERF_CLUSTER_ADAPTER='company_perf.temporal_adapter:create_adapter'
# 通过部署平台 Secret 注入 TEMPORAL_API_KEY；不要写进仓库、manifest、命令记录或workflow payload。
python -m perf_temporal.worker
```

Cloud连接使用 `Client.connect(..., api_key=..., tls=True)`。模板未实现mTLS变体；如公司要求mTLS，按官方文档改connection模块。worker可横向运行多个副本，所有调用仍须幂等。`max_concurrent_activities=8`仅限制控制面RPC，并不等于GPU并发；GPU租约/队列/配额由现有runner管理。

worker 与人工操作入口使用不同服务身份。实施agent通过公司网关发受限的 start/status/cancel请求，不获得可任意signal工作流的Namespace API key。Cloud RBAC保护Namespace访问，但本模板不假定它能自动实现“只能发某个signal”的细粒度授权。

## 3. 实现 adapter：这是部署前的必做部分

实现 `perf_temporal/adapter.py` 中所有方法，并让 `create_adapter()` 返回实例。该 factory 只在worker进程读取Secret和网络配置；workflow代码不进行网络、文件、随机或时钟I/O。

|接口|必须满足的约束|
|---|---|
|read_manifest|允许的存储协议/host、大小限制、不可变对象；检查SHA后才提交|
|lookup_job|按experiment_id查持久登记记录，绑定不一致必须拒绝；保留超过Temporal历史留存期|
|create_job_if_absent|原子唯一性/幂等token，保存scheduler job ID；响应超时先查询已有提交，不直接再发一份；approved runner模板与walltime|
|poll_job|按精确job/group读取状态；未知/丢失不是SUCCEEDED|
|collect_and_gate|收集校验过的结果引用；运行预先批准的验证器；缺数据/数值验证/基线/整步指标即失败|
|fence_and_lookup|与create登记事务协调；阻止新提交并消解在途提交；不能确定是否还会出现job就报错|
|cancel_job_group|验证identity/owner后，只取消给定job/group及所属rank；幂等；不用pkill或按用户取消全部任务|
|authorize_release_and_create_task|验证外部receipt的签发、身份、角色、时效、撤销状态及binding/evidence；重新核对baseline是否仍可集成；幂等创建工单；确定审批拒绝且尚无副作用时抛出专用ApprovalRejected|

如果scheduler没有幂等create API，adapter需要公司现有runner的持久唯一登记与恢复逻辑；不能仅凭本进程内dict实现。临时控制面故障由Temporal重试；adapter不能无界重试。所有长时间结果计算应是runner中的另一个明确job，activity只读状态/结果。

## 4. 建立 manifest 与 envelope

manifest例子（写入受控artifact store，保持原始字节）：

```json
{
  "experiment_id": "wam-compile-group-003",
  "candidate_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "baseline_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "runner_template_id": "wam-h200-8gpu-compare-v1",
  "max_run_seconds": 21600,
  "config_uri": "由你替换为不可变配置引用",
  "validator_id": "由你替换为批准的门禁版本"
}
```

`a`/`b`只是格式示例，必须改为真实完整commit。runner负责验证模板/validator/resource配额；模板不把JSON中的任意字符串当shell命令。下例在本地从exact bytes生成envelope，随后把相同字节上传存储；URI不能含Secret。

```python
import hashlib, json
from pathlib import Path
raw = Path('manifest.json').read_bytes()
m = json.loads(raw)
spec = {
    'binding': {k: m[k] for k in ('experiment_id', 'candidate_sha', 'baseline_sha')},
    'manifest_uri': '替换为允许的artifact URI',
    'max_run_seconds': m['max_run_seconds'],
    'poll_seconds': 60,
    'release_wait_seconds': 86400,
    'cancel_wait_seconds': 600,
}
spec['binding']['manifest_sha'] = hashlib.sha256(raw).hexdigest()
Path('experiment.json').write_text(json.dumps(spec, indent=2))
```

```bash
python -m perf_temporal.client start experiment.json
python -m perf_temporal.client status experiment.json
python -m perf_temporal.client result experiment.json
python -m perf_temporal.client cancel experiment.json --reason '发现数值门禁输入有误'
```

start重复返回失败是预期行为；查询已有workflow即可。需要改变manifest时建立新experiment_id，并关联旧任务，而不是覆盖旧身份。最终结果可为FAILED、GATE_FAILED、RELEASE_EXPIRED、CANCELLED、CANCEL_UNCONFIRMED或INTEGRATION_TASK_CREATED。

## 5. 人工 release 的认证边界

这个模板不包含登录UI，也没有伪造“已认证用户”。你需接入公司SSO/RBAC审批页面：展示绑定的实验/基线/候选/证据；人确认后由服务产生可验证receipt；operator网关再发送signal。

```bash
python -m perf_temporal.client release experiment.json \
  --evidence-sha '复制已审核证据的SHA256' \
  --receipt-id '外部审批系统签发的receipt引用'
```

signal回执只表示消息已送达，不表示审批有效或任务已创建。查询status/result。外部adapter必须验证receipt；提交者写`approved=true`、填姓名、猜receipt字符串都不能通过。审批中发现baseline变化应失效并重新做集成验证。集成工单生成后若取消到达，可能已有工单；工单自身仍需新门禁，不能自动部署。

adapter对于明确的无效/过期/无权限receipt，应在任何建单副作用之前抛出 `perf_temporal.adapter.ApprovalRejected`。workflow记录拒绝原因并回到 `AWAITING_RELEASE`，保留最初审批deadline，允许提交**新的receipt ID**；已处理过的receipt不会重复尝试，GPU作业不会重跑。网络故障或建单结果不确定不能伪装成审批拒绝，仍按普通activity故障核对。网关应限制重复/垃圾signal的速率。

基线或验证合同已变化时，adapter应抛出 `ContractViolation` 并进入 `NEEDS_RECONCILIATION`，创建新的绑定实验/复验；不要把这种变化当成“换一个receipt即可纠正”的 `ApprovalRejected`。

## 6. 失败与取消

- 原子提交超时：Temporal重试activity→先lookup→返回同job；真正无法消解则NEEDS_RECONCILIATION，人工查精确job和runner ledger，禁止盲重交。
- cancel信号：登记cancel fence→请求取消精确job/group→短poll确认终态。达到cancel等待上限返回CANCEL_UNCONFIRMED，必须人工处理，不能当已停机。
- cancel已在submit/poll等activity执行期间到达，而该activity最终失败：仍执行一次有界fence/cancel清理。结果同时保留原始故障与取消结果；清理也失败时返回CANCEL_UNCONFIRMED并保留两段故障，不能声称job已停。
- Native Temporal cancel也尝试同样cleanup；cleanup失败时不能保证job已停。推荐使用本CLI的cancel signal以获得明确结果。
- Temporal **terminate** 不执行workflow清理，禁止用它代替GPU取消。运维若必须terminate，先在runner按精确job取消并确认。每个job必须配置scheduler硬walltime，以覆盖worker/控制面全部失联的情况。
- 未收到cancel时，普通activity最终失败可能留下已提交GPU job，状态NEEDS_RECONCILIATION；监控应告警并关联job_id。模板不声称分布式系统提供exactly-once外部副作用。
- 不给workflow设置自动重试；更新workflow代码要做history replay/版本管理。模板将排队加执行窗口限制为24小时、轮询至少30秒，避免无限增长的history；更长训练应拆分或实现Continue-As-New并保存状态。

## 7. 测试

```bash
python -m compileall -q perf_temporal tests
python -m unittest discover -s tests -v

# 可在远程CI runner运行，启动临时Temporal测试服务；需要下载测试二进制。
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s tests -v
```

单元测试覆盖：SDK sandbox加载、默认fail closed、提交已成功但响应丢失、manifest篡改、精确job取消、旧baseline审批、伪造receipt和幂等创建工单。集成测试使用内存假adapter，不接触GPU或Cloud；覆盖人工等待/释放、signal/native取消、排队计时、submit/poll失败期间收到取消、清理双故障、坏receipt后换新receipt与原deadline不延期、GPU失败不重跑。实际执行结果见`VALIDATION.md`。

可选人工测试服务使用`temporal server start-dev`。这只用于开发验证，不是生产方案，也不要求部署本地LLM。设置`TEMPORAL_LOCAL_DEV=1`只允许loopback:7233连接。

## 8. 与 Symphony / LangGraph 的边界

- Symphony：管理开发工单、Codex隔离workspace、patch与review材料；批准实验manifest后调用这个入口，随后读取状态。它不再拥有GPU作业重试。
- LangGraph：可在一个有限的研究/诊断阶段组织agent工具调用；输出候选与manifest。不要把同一实验生命周期、重试和人工审批再保存成另一套权威状态机。
- Temporal：唯一实验生命周期/计时/控制面重试所有者；runner负责资源租约与作业幂等登记。主看板可以读Temporal，但不能用一份Markdown状态覆盖Temporal事实。

## 官方资料

- [Temporal Python Client / Cloud连接](https://docs.temporal.io/develop/python/client/temporal-client)
- [Python Workflow message passing](https://docs.temporal.io/develop/python/workflows/message-passing)
- [Cancellation与terminate区别](https://docs.temporal.io/develop/python/workflows/cancellation)
- [Python Workflow API](https://python.temporal.io/temporalio.workflow.html)
- [WorkflowEnvironment测试API](https://python.temporal.io/temporalio.testing.WorkflowEnvironment.html)
- [SDK 1.34.0 发布包](https://pypi.org/project/temporalio/1.34.0/)
