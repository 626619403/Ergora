# 多 agent 平台：安装与日常使用手册

面向项目开发者和平台维护者。工作流使用 Codex 实现与独立新会话审查、Temporal 编排、Symphony 工单入口、A2A 互操作、Supervisor 服务管理、MLflow 实验记录和 LangGraph 有界候选搜索。

## 全新环境安装

发布包支持 Ubuntu 24.04、Linux x86_64、Python 3.12。默认执行配置面向可信项目所在的 Docker/Podman 容器。只需操作系统自带 Bash、apt 与基础命令；安装器会安装 Linux 支持包、固定版本 Node.js、uv、Codex、Temporal、Symphony 及锁定 Python 依赖。

安装 Linux 包需要当前系统或容器内的 root/sudo 权限；工具、配置和运行数据写入当前用户 home。安装需要访问 Ubuntu 软件源、nodejs.org、GitHub、registry.npmjs.org 和 Python 包索引。只有阅读 HTML 或下载其内嵌文件可以离线完成。

下载 HTML 中的“全新环境一键安装器”，在目标环境执行：

```bash
bash ~/Downloads/install-agentflow.sh
source ~/multi-agent-platform/env.sh
agentflow doctor
```

安装不会登录模型账号、执行项目任务或运行训练。初次安装后再配置认证。也可下载源码 ZIP，解压到 home 后在包含 install-from-report.sh 和 platform/ 的目录运行：

```bash
bash install-from-report.sh
# 可选：只校验导出包、目标冲突与缓存缺口
bash install-from-report.sh --check
```

一键安装器会把源码包解压到 ~/.local/share/agentflow/installers/，不依赖临时目录。支持 --start、--runtime-cache DIR；已有不同内容的源码会被保留并停止，升级前应审阅差异。SHA 校验用于完整性，不替代来源认证。

### 准备执行容器

控制面与模板可以安装在裸 Linux；本发布包的自带执行器要求检测到 Docker/Podman 容器并得到明确启用。没有容器运行时时，先按 [Docker 官方安装说明](https://docs.docker.com/engine/install/ubuntu/) 安装运行时。以下示例面向 Linux 宿主机：

```bash
docker volume create agentflow-home
docker run --init -it --name agentflow --network host \
  --mount type=volume,source=agentflow-home,target=/root \
  ubuntu:24.04 bash
```

该示例使用持久 home 卷及 Linux host 网络，使服务的 127.0.0.1 界面可从宿主机访问；端口应仅对可信本机开放。用 docker cp 将安装器和项目复制进容器，或挂载需要处理的项目目录。不要为了运行本平台挂载宿主机 Docker socket。其他容器网络模式按实际 SSH/IDE 转发或代理配置访问。

## 模型配置与认证

Codex 实现采用 Responses API 模式。选择你的服务支持的模型 ID，并配置平台使用的元数据；不需要预先存在 ~/.codex/config.toml，也不把 key 写入项目。

```bash
source ~/multi-agent-platform/env.sh
python3 ~/multi-agent-platform/bootstrap/configure-model.py \
  --model YOUR_SUPPORTED_MODEL_ID \
  --base-url https://api.openai.com/v1 \
  --env-key OPENAI_API_KEY
```

通过你自己的 shell/Secret 管理器提供 OPENAI_API_KEY。使用兼容网关时替换 base-url、env-key 与模型 ID。不要把真实 key 写进公开文档或命令历史。仅 Codex 订阅登录并不自动提供本 adapter 所需的 API 凭据。

实现与审查共用这份 Codex API 配置和凭据变量。审查单独启动新的 ephemeral 会话，角色标识为 codex-reviewer，不续接实现会话；默认使用同一个已配置模型。独立会话有助于分开上下文，业务检查和人工审阅仍需完成。

```bash
agentflow doctor
```

安装成功与模型认证可用是两个阶段；doctor 会显示缺少的模型配置、凭据、审查配置和项目。模型不可用时，任务会明确失败。

## 持久目录

|内容|默认目录|
|---|---|
|工具、Python 环境、可复用适配器|~/multi-agent-platform/|
|Linux 支持包安装 / 环境修复脚本|~/install-multi-agent-linux-deps.sh / ~/install-multi-agent-platform.sh|
|配置与项目注册|~/.config/multi-agent-platform/|
|任务、数据库、日志、worktree、证据、检查点|~/.local/state/multi-agent-platform/|
|三个模板|~/multi-agent-platform/templates/|
|命令入口|~/multi-agent-platform/bin/agentflow；env.sh 将其加入 PATH|

长期资产不放在 /tmp 或项目 tmp。容器重建时 home 能否保留取决于挂载与备份策略。各业务项目放在自己的目录与 Git 仓库中。

## 执行配置与边界

自带执行配置使用现有 Docker/Podman 容器作为外层边界，在其中以当前 Unix 用户运行可信项目。worktree、模型会话、超时、取消 fence 和回执帮助管理执行，但不提供容器内每 agent 的 OS 隔离或防篡改认证。agent 可访问当前用户文件。审查阶段按只读指令运行，执行器对比审查前后的工作区与 HEAD，检测到改动即拒绝通过；这项检测不提供 OS 强制只读隔离。

确认你接受此配置后启用：

```bash
agentflow sandbox probe
agentflow execution enable --trusted-current-container
agentflow services start
```

启用绑定实际容器、PID/mount namespace 和 boot ID。换容器后重新检查和确认。只安装包不会自动启用；裸 Linux 上需要进入执行容器或接入自己的执行器。bwrap/Podman 嵌套能否运行取决于外层权限，安装支持包不保证其可用。

agentflow execution disable 关闭开发执行器的自动领取。已启动的作业仍需其超时或取消协议管理；停止 Supervisor 不等于取消作业。

## 服务与交互

```bash
source ~/multi-agent-platform/env.sh
agentflow services start
agentflow services status
agentflow services logs executor
agentflow services logs worker --stderr
agentflow services restart
agentflow services stop
```

Supervisor 管理服务，无需 systemd。重启容器后从包含模型 API 环境变量的 shell 执行 services start。修改变量后先 services stop，再 services start；只 restart 子服务会继承旧 Supervisor 环境。可选训练 worker 默认关闭，services status 可能因 STOPPED 返回 Supervisor 的退出码 3；查看每一行实际状态。

|入口|地址 / 用途|
|---|---|
|CLI|agentflow：注册、创建、查询、批准、取消、导出|
|Temporal UI|http://127.0.0.1:8233：任务历史与故障|
|MLflow|http://127.0.0.1:5000：参数、指标与产物|
|A2A Agent Card|http://127.0.0.1:8765/.well-known/agent-card.json|
|A2A JSON-RPC|http://127.0.0.1:8765/a2a：token + A2A-Version: 1.0|

这些是服务所在环境的 localhost 地址。远程或容器环境通过现有端口转发/代理访问；不要直接公开服务端口。A2A CLI 从私有配置注入本地凭据，无需在聊天中粘贴 token。

## 接入一个具体项目

每个业务项目使用自己的 Git/GitLab 仓库和工单，每张工单建立 agent/123-description 这类任务分支。平台目录只共享工具与运行记录。项目应有已提交的基线、真实测试环境和可信检查命令。

```bash
agentflow templates copy repository-governance "$HOME/projects/my-project/workflow-governance"
agentflow templates copy large-change "$HOME/projects/my-project/workflow-large-change"
agentflow templates copy training-optimization "$HOME/projects/my-project/workflow-training"
```

目标目录必须不存在。按项目填写 input.json 中的 goal、allowed_paths、acceptance、constraints、risk、work_units。工作单元声明 id、depends_on、paths、instructions；DAG 无环、路径范围明确。

checks.json 的键为检查 ID，值为非空 argv 数组。治理要求 behavior、architecture、knowledge；大型变更还要求 integration、compatibility、migration-rollback。scope 与 baseline-regression 由执行器完成。缺少检查、基线失败或配置不匹配会阻止执行。

命令应使用项目环境的解释器绝对路径；worktree 不复制被忽略的 .venv。参数可用 {repo} 表示当前待验证 checkout，输出放在 checkout 之外。不要用 /bin/true、固定 PASS 或通用 lint 冒充业务兼容性验收。

准备好项目基线、checks.json 和真实模板输入后：

```bash
agentflow project add my-project \
  --repo "$HOME/projects/my-project" \
  --tracker local --project local/my-project \
  --allowed-path src --allowed-path tests --allowed-path docs \
  --allowed-path AGENTS.md --allowed-path ARCHITECTURE.md \
  --checks-json "$HOME/projects/my-project/checks.json"

agentflow task create --project my-project --type repository-governance \
  --id my-project-123-r1 --issue 123 \
  --input "$HOME/projects/my-project/workflow-governance/input.json"
agentflow task start my-project-123-r1
agentflow task status my-project-123-r1
```

命令中的项目名、目录、路径和关联编号均为示例。local issue 是本地关联编号，不会创建或请求远程工单。task create 编译并冻结输入；同一 ID 不可换输入，新修订使用新 ID。

## 开发任务的关键步骤

盘点与基线 → 计划 → 人工批准 → Codex 按 DAG 实现 → 集成 → 固定候选命令验证 → Codex 独立新会话审查 → REVIEW_READY。

AWAITING_PLAN_APPROVAL 时，读取 ~/.local/state/multi-agent-platform/artifacts/任务ID/ 下的计划、所有权和回滚材料，再使用状态中精确的计划 SHA：

```bash
agentflow task approve my-project-123-r1 --plan-sha256 PLAN_SHA256
agentflow task status my-project-123-r1
agentflow task result my-project-123-r1
agentflow task export my-project-123-r1 --branch agent/123-description
```

PLAN_SHA256 需替换为当前等待批准的摘要。export 仅在 REVIEW_READY 后创建项目分支，不切换工作目录、不合并或推送；已有同名不同提交分支会被保留。维护者审阅、按当前目标分支复验，再按项目流程提交 MR。

```bash
agentflow task cancel my-project-123-r1 --reason '说明原因'
agentflow task result my-project-123-r1
```

取消请求不是停止证明。NEEDS_RECONCILIATION 或结果不明时，检查精确 PID、回执与产物，使用同一 ID 查询和对账；不要改名后重复副作用。修正已结束的失败/取消任务时使用新的任务修订 ID。

## 候选搜索与实验

```bash
agentflow search --project my-project --id my-project-search-r1 \
  --goal '一个可检验的目标' --limit 3
# 相同输入恢复检查点时追加 --resume
```

LangGraph 只生成 1–5 个有界提案，保存 SQLite 检查点；不会自动实施、启动任务或运行训练。训练负面结果按项目回流。训练操作见 [训练优化手册](docs/TRAINING.md)。

## GitLab 与 Symphony 后续绑定

按真实项目注册 --tracker gitlab --project group/repo。每个项目使用自己的 GitLab 工单、workspace、配置和归属台账；也可先使用本地 CLI/A2A。

```bash
agentflow symphony configure my-project --repo-url https://gitlab.example.com/group/repo.git
# 编辑生成的该项目配置：私有 GitLab 的 api_url、token_env 等
agentflow symphony enable my-project
```

从自己的 Secret 管理器注入该项目 GITLAB_PAT；不要把凭据放进 URL。工单标签为 agent-ready、agent-waiting、agent-review、agent-blocked。启用轮询不代表请求已获准执行；按 [Symphony 桥接说明](upstream/symphony/README.md) 核对请求并准入。

注册记录不可原地更换基线/检查；local 转 GitLab 或策略升级时先结束并对账在途任务，再建立清楚的新注册修订并人工退役旧匹配，避免同一 tracker/project 有两个注册。CLI/A2A/Symphony 共享工单归属。

Symphony/上游文档中的 Cloud、/opt 和独立服务身份属于扩展部署参考，本手册给出的是 home + Supervisor + 可信容器配置。A2A 协议见 [A2A 文档](upstream/platform/A2A.md)。

## 修复、验证与备份

```bash
bash ~/install-multi-agent-linux-deps.sh --check
bash ~/install-multi-agent-platform.sh
agentflow doctor
agentflow verify
uv pip check --python ~/multi-agent-platform/.venv/bin/python
```

verify 检查 Temporal、A2A 鉴权和 MLflow；追加 --restart-temporal 可验证重启恢复，会短暂重启服务，先确认无敏感在途工作。安装自检不等于真实模型、GitLab 或训练性能验收。

备份前取消并确认运行中的作业，停止服务，再备份平台源码、配置、state 和各项目仓库。配置包含本地凭据，备份应仅自己可读。恢复后核对权限、模型环境变量、服务状态和容器身份，再重新启用执行。

更详细的验证步骤见 [验证与维护指南](docs/VALIDATION.md)。
