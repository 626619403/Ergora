# 训练优化手册

本手册面向有真实训练仓库、数据、硬件与评估方法的使用者。平台负责实验协议、任务历史、证据门禁和记录；训练环境、资源预算和效果标准由项目确定。它不安装项目专属 CUDA/PyTorch，也不默认承诺任何加速。

开发与集成复验任务使用 Codex 实现和独立新会话审查。训练实验的 review 证据仍需由项目可信 runner 与独立审查流程按证据格式提供。

## 1. 准备项目与验收合同

先按部署手册安装平台并配置模型认证、执行容器与项目。复制 training-optimization 模板到项目的新目录，填写 workload-contract.md、baseline.json、experiment.json 和 runner-template.example.json。

合同至少说明：优化目标与停止规则、允许改变的训练语义、数据/配置/环境/初态指纹、真实 baseline 与 candidate 提交、数值容差、多步/保存恢复/训练质量要求、成对重复计划和资源预算。人工阅读合同后才将 contract_approved 设为 true；示例提交、指标和 PASS 不是真实证据。

E 类工程优化保持训练问题，N 类数值变化需要误差预算，A 类配方变化按达到同等质量的时间单独比较。不要将较少工作、不同数据、不同 batch 或质量下降计作工程提速。

## 2. 注册可信 runner 与基线

runner JSON 包含 schema_version、runner_template_id、project、repo、command、timeout_seconds。repo 为真实 Git 仓库绝对路径；command 是 argv 数组，可使用 {manifest}、{output}、{baseline_repo}、{candidate_repo}。基线与候选使用精确提交的独立 worktree；结果写到 output。

runner 使用项目已经验证的训练环境与脚本。worktree 不复制被忽略的 .venv。先检查 baseline 与 candidate 的可复现性、资源占用和输出证据格式，避免把长 GPU 作业放进 Temporal activity。

```bash
agentflow training init --project my-project --baseline /absolute/path/baseline.json
agentflow training runner-add /absolute/path/runner-template.json
agentflow training prepare /absolute/path/reviewed-experiment.json \
  --runner project-training-v1 --max-run-seconds 25200
```

prepare 以 candidate_commit / baseline_commit 为唯一业务来源，生成 Temporal 别名并冻结同一份 manifest 字节，输出 manifest_sha256。别名冲突、缺少基线、未批准合同、比较器版本不符或 ID 被重复绑定时会拒绝。max-run-seconds 为排队加执行窗口；runner timeout_seconds 是独立执行 walltime，两者不同。

## 3. 明确执行一个实验

```bash
agentflow training worker-start
agentflow training start EXPERIMENT_ID
agentflow training status EXPERIMENT_ID
# 等到 job 请求登记后，用 prepare 的精确 manifest SHA 手动执行：
agentflow training run-local EXPERIMENT_ID --confirm-manifest-sha MANIFEST_SHA256
agentflow training status EXPERIMENT_ID
agentflow training result EXPERIMENT_ID
```

替换示例 ID 和 SHA。控制 worker 默认关闭；start 只启动实验控制流程，run-local 只执行明确选择的这个实验，不扫描队列。同一 ID 重复调用会查询在途或已完成记录，结果不明时拒绝自动重执行。

当前本地 runner 没有每实验 cgroup/GPU 配额；操作者必须先核对资源并逐个执行。若需要多人并发、集群排队和 GPU 隔离，应接入 Slurm/Kubernetes/现有训练平台的受信 ClusterAdapter，并完成幂等与精确取消验收。

CLI 中断不等于任务停止。进程受独立 walltime 和取消 fence 管理；使用相同实验 ID 查询和对账，不通过新 ID 重复有副作用的作业。

## 4. 证据、统计与 MLflow

runner 输出 output/evidence.json 和哈希索引中列出的产物。至少包括绑定当前合同与提交的数值验证、独立审查、固定基线下的集成/质量检查、成对独立重复测量及原始记录；结构见 [证据格式](../upstream/docs/evidence-format.md) 和模板。

平台以固定 perfctl archive 在 CPU 步骤重新计算统计比较，检查合同、baseline、candidate、子文件 SHA 及当前基线，保存原始证据。缺失、不合格、过期或比较策略不符的材料无法通过。完整指标由可信比较输入产生，不能只采信 candidate 自报 PASS。

MLflow 记录代码、数据、配置、环境指纹、门禁结果与产物。它保存观测，Temporal 保存正式生命周期。性能比较与训练质量分别验证；一轮局部成功不等于完整训练可采用。

字段别名和原始字节绑定详见 [perfctl / Temporal 桥接规程](../upstream/temporal/PERFCTL_BRIDGE.md)。

## 5. 人工放行与集成复验

门禁通过后进入 AWAITING_RELEASE。读取 ~/.local/state/multi-agent-platform/training/jobs/实验ID/gate-report.json 和归档证据，检查当前基线，再批准状态中的精确 evidence SHA：

```bash
agentflow training approve EXPERIMENT_ID --evidence-sha EVIDENCE_SHA256
agentflow training result EXPERIMENT_ID
```

审批核对 Unix 操作员身份、权限、时效、撤销与绑定。共享 Unix 用户不提供企业 SSO 或防篡改认证；需要团队级边界时接入独立身份与审批服务。

放行只创建该项目的集成/复验任务 JSON，不合并、不部署、不开始生产训练。维护者按当前目标分支与 baseline 复验，通过项目自己的工单/MR 流程采用结果。新 baseline 或新候选必须有新的、可追溯的修订。

## 6. 取消、失败与下一轮搜索

```bash
agentflow training cancel EXPERIMENT_ID --reason '说明原因'
agentflow training result EXPERIMENT_ID
agentflow training worker-stop
```

取消先建立 fence 阻止后续提交，再按精确进程组处理。没有确认终态时，不能把取消请求当作停机证明，也不能靠停止 worker 或删除记录代替取消。

失败记录位于 state/training/negative-results/，会被相同项目的 LangGraph 候选搜索读取。保留失败机制、受影响条件和证据；更新假设后再选择下一候选。完整训练、质量、恢复和资源接口需要在项目自己的硬件与数据上完成验证。
