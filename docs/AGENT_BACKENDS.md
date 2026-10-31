# 模板角色与可替换 Agent

模板保存目标、角色、能力、产物和验收；项目保存具体工具。`ergora templates copy` 会在原文件之外附带 `agent-contract.json`，不改变冻结参考合同。查看角色：

```bash
ergora templates agents repository-governance
ergora templates agents large-change
ergora templates agents training-optimization
```

治理和大型开发提供 inspector / planner / implementer / reviewer。integrate、verify 和 work 的可信 test-results 仍由执行器负责。训练提供 experiment-planner / performance-analyst / kernel-tuner，分别输出提案、分析及候选说明；原生 kernel 生成工具在独立的 `kernel` 层选择。

Codex / Claude Code 的首次安装、认证和官方入口见 [安装手册](USAGE.md#安装与认证-agent-cli)。以下步骤假定所选命令已在启动 Ergora 的 shell PATH 中可用。

Windows 原生的安装与认证见 [Windows 手册](WINDOWS.md#agent-安装与认证)。原生角色调用支持 Codex、Claude Code 及明确的程序 / 解释器 `.exe`；`.cmd` / `.bat` launcher 显式拒绝。mini 的 Bash 驱动、ForgeKernel 及正式六阶段桥接要求 WSL2/Linux，正式参考执行器另需可信 Linux 容器。Windows 保持 Codex 原生 sandbox，不能使用 Linux 的 `current-container` 选择。

## 项目选择与独立调用

通过控制台“工具绑定”选择每个角色，也可以使用 JSON：

```json
{"tool":"codex","model":"YOUR_MODEL_ID"}
```

```bash
ergora project show my-project
ergora project bind my-project planner --binding planner.json --revision CURRENT_REVISION
ergora agent run my-project planner --prompt plan-request.md --template repository-governance
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

`--template` 要求该角色的真实结构化产物；不指定时保持普通文本调用。两者都不等于正式验收。Codex 默认使用角色对应的 CLI sandbox。若系统不支持该 sandbox，可在已经明确接受当前容器/用户边界后，显式设置 `"sandbox":"current-container"`；不会自动降级。Claude Code 使用自己的认证，其审查/提案角色限制到 Read/Grep/Glob，关闭会话持久化与额外 MCP 配置。默认审查仍为 Codex。

### 自定义命令

普通 `{"tool":"command","argv":["/path/to/program"]}` 继续接收 stdin 文本。正式阶段或 `--template` 调用要求：

```json
{
  "tool": "command",
  "argv": ["/path/to/agent-wrapper"],
  "protocol": "stage-json-v1",
  "capabilities": ["repository-read", "plan-write"]
}
```

stdin 为 `{schema_version, role, prompt, result_schema}`；stdout 必须仅含一个符合 result_schema 的 JSON 对象，诊断写 stderr。schema 要求 summary、所需 artifacts；审查还要求明确的 approve / request-changes。能力列表须覆盖角色要求；它是兼容性声明，不是工具质量或隔离的证明。命令按 argv 执行，模板中不嵌入命令。

### mini-swe-agent

```bash
bash scripts/install-agent.sh mini-swe-agent
```

固定源码和独立 venv 默认保存在 `~/.local/share/ergora-tools/mini-swe-agent/`。将其 Python 绝对路径填入实现角色：

```json
{
  "tool": "mini-swe-agent",
  "python": "/YOUR_HOME/.local/share/ergora-tools/mini-swe-agent/.venv/bin/python",
  "model": "YOUR_PROVIDER/YOUR_MODEL",
  "step_limit": 30,
  "cost_limit": 3.0
}
```

认证由相应 provider 的环境变量提供。mini 支持实现角色，不承担只读独立审查。驱动使用原生 LiteLLM tool-call 模型与一致的 bash 工具提示，保存 trajectory；完成时将最终文本写到运行归档中的提交文件，再用提示中给出的命令提交正文，交给同一结构验证。空 submission 判为失败。shell action 保留在外层监控的进程组，使用整体任务时限；一个 action 可消耗剩余时限。成本沿用上游报告值，单次 API 请求可能超过剩余预算，不是预付费金额上限。安装和 CPU SDK 检查不代表模型效果验收。

## 可选的正式六阶段执行桥接

默认 `agentflow` 执行器保持 v2.2 行为。要使项目的角色选择作用于正式任务，先按参考手册安装、配置模型、启用可信容器执行、注册项目和可信检查，再注册同名 Ergora 项目，且二者指向同一 Git 根目录。只对新的任务启用；不要中途切换已开始的参考任务。

先停止原 executor，保留 Temporal、worker 等服务：

```bash
"$HOME/multi-agent-platform/.venv/bin/supervisorctl" \
  -c "$HOME/.config/multi-agent-platform/supervisord.ini" stop executor
ergora reference executor --installation "$HOME/multi-agent-platform"
```

该命令在前台监听原 FileAdapter 队列，使用同一 executor 锁，保留原任务创建、审批、取消、恢复和导出命令。也可加 `--request /ABSOLUTE/PATH/envelope.json` 精确处理一个已发布信封。执行器校验参考 Python 源码身份，拒绝未经适配的版本。

新任务首次处理时将角色工具与项目修订写入原任务持久目录的 `agent-bindings.json`；恢复继续用这份选择。实现者和审查者使用不同角色身份、新会话、精确候选提交及原有工作区变化检测。正式阶段结束前清理并回收其派生进程，再执行原监控的只读变化检查；精确使用参考配置的 Codex 可执行路径。未知外部进程结果继续由参考监控对账；缺少能力、结果结构错误、命令失败或只读阶段改动都不能通过。Agent 的 `model-log` 和 `agent-selection` 附在原回执证据中。

需要长期运行时，在 `~/.config/multi-agent-platform/supervisor.d/executor.ini` 中把该 program 的 `command` 改为 Ergora 可执行文件绝对路径、`reference executor --installation ...`，保留 stopasgroup/killasgroup。再用 supervisorctl `reread` / `update`。初始化参考发行可能重新生成该文件，升级后应核对。不要同时运行新旧两个 executor。

桥接沿用参考配置中的 Codex TOML 和 API 变量。参考监控的凭据白名单不会传递任意 shell 变量；其他 provider 可使用工具自己的持久登录，或参考 `credentials.json` 的 0600 凭据映射。模板、项目绑定与仓库中只保存凭据变量名/元数据。独立调用的活动 Skill/记忆选项不会自动改写正式任务的上下文。

## ForgeKernel 原生候选

```bash
bash scripts/install-agent.sh forgekernel
```

默认源码为 `~/.local/share/ergora-tools/forgekernel`，安装固定版本，不安装 CUDA/PyTorch、不登录 Claude、不启动 GPU。依据 [官方说明](https://github.com/OpenBMB/ForgeKernel/tree/5030503d3ff71851aa34c14b9caf13ebfa9d9a78) 填写原生任务和本地设备配置后绑定：

```json
{
  "tool": "forgekernel",
  "checkout": "/YOUR_HOME/.local/share/ergora-tools/forgekernel",
  "python": "/YOUR_HOME/.local/share/ergora-tools/forgekernel/.venv/bin/python",
  "task": "/YOUR_HOME/projects/my-project/kernel-task"
}
```

```bash
ergora project bind my-project kernel --binding kernel.json --revision CURRENT_REVISION
ergora kernel plan my-project
ergora kernel prepare my-project
ergora kernel list my-project
ergora kernel status my-project CAMPAIGN_ID
ergora kernel run my-project CAMPAIGN_ID --timeout 3600
```

同样操作位于“工作流设计 → 训练优化实验 → 原生 Kernel 候选”。`plan` 检查并展示原生计划；`prepare` 只创建并冻结原生 campaign；`run` 才执行模型/GPU，显式调用也用于继续同一个 campaign；`status` 核对原生状态。Ergora ID 与原生目录映射持久保存，改变当前项目绑定不会改变已有 campaign。

固定版本仅支持 Claude backend；Codex 登录不能替代它。首版适配仅支持 local delivery，SSH delivery 显式拒绝。超时/中断可能留下原生子作业，记录为 `outcome_unknown`，不声称远端或 GPU 已取消。先核对原生目录和旧作业是否停止；需要继续时，提供 `--reconcile-reason '实际核对依据'`，页面也有对应字段。创建结果不明时先 status 从该 ID 的原生目录对账，不能直接创建另一个 campaign 替代。

除原生任务快照，campaign 还固定 models.toml、loop.toml、backends.toml 的 SHA；后续配置漂移会明确拒绝，须恢复对应配置。运行中不要修改共享默认配置；备份与换机须同时保留工具源码、这些配置及 campaign。报告与实际 best/kernel.py 或 best/kernel.cu 的身份会保存；`native_finished` 只描述生成器的完成，`native_failed` 保留上游失败。选择候选提交后，继续用训练模板的 manifest、可信 runner、正确性/质量与配对性能证据，并按 evidence SHA 人工放行。ForgeKernel 的内部 judge、target_met 或报告文字不能直接成为 perfctl PASS。实际验证范围及未测的 GPU/模型效果见 [S8 记录](delivery/2026-10-31-s8-agents.md)。

完整选型与未接入工具见 [三模板调研](research/2026-10-31-template-agents.md)。
