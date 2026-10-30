# Symphony → Temporal 通用任务接入模块
## v1.2 开发类型接入

本次新增 `repository-governance` 和 `large-change`，通过同一个持久 bridge 分流到 `DevelopmentWorkflow`。训练 v1 请求继续走原有 `ExperimentWorkflow`。这份文档后续的 baseline、manifest、release 等步骤只属于训练类型；开发类型用下面的入口及 [平台快速上手](../platform/README.md)。

```bash
cp config.development.example.json /etc/agent-pipeline.json
# 编辑项目/仓库 URL、绝对目录、可执行路径和 repository_state_file。
# 受信 CI 在该 state 文件记录 project、受保护分支 base_sha、policy_revision。
# 不要复制示例假 SHA，也不要把该状态文件挂载为编码 agent 可写。
python3 configure.py --config /etc/agent-pipeline.json --output /etc/symphony/DEVELOPMENT_WORKFLOW.md
```

Symphony/bridge 的启动及身份隔离方式相同；开发 worker 使用 `DEV_TASK_QUEUE=development-tasks`，按 [执行器协议](../platform/EXECUTOR_PROTOCOL.md) 接实际 Codex/CI 阶段执行器。`platform/task-types/*/examples/request.json` 是 schema v2 原始交接格式；profile 摘要必须与已安装模板相同。`repository.starting_sha` 为入口已提交的起点；最终 `candidate_sha` 由集成阶段产生。

```bash
# 受信 CI/操作员对这份原始请求完成范围、身份与资源核验后：
python bridge.py --config /etc/agent-pipeline.json admit /srv/agent-outbox/PROJECT-7-r1.json --authorization-receipt EXISTING-CI-RECEIPT
# authorization-receipt 是追溯引用；admissions 私有目录与执行者身份才是权限边界。
python bridge.py --config /etc/agent-pipeline.json run
```

开发工作流在 `AWAITING_PLAN_APPROVAL` 等待人的计划批准，最终 `REVIEW_READY` 仅路由 `agent-review`。无合并、部署或生产迁移权限。取消未确认/未知终态保留 `BLOCKED_UNRESOLVED` 和 issue 归属；恢复命令见 [OPERATIONS](../platform/OPERATIONS.md)。任务 ID 在共享 Temporal namespace 内必须全局唯一，建议项目前缀 + 工单 + 修订号。

升级时备份单机 ledger 和 receipts，再停止旧 bridge、切换同一状态卷。新 bridge 增加冻结 spec 列，保留运行中的原始输入；旧当前工单缺 `safe_to_rework` 时重投递已有终态，未知状态保持锁定。旧版本模板/worker 保持可用直到其任务结束；不原地修改同版本 profile。

新代码与测试记录见 [platform/VALIDATION.md](../platform/VALIDATION.md)。以下保留训练流程原有部署说明。

---

版本 1.1 · 2026-10-26（新加坡）。本模块已实现连接代码，替换此前“以后接入”的说明。默认支持 **GitLab Issues / GitHub Issues**；不要求迁移到 Linear。

实际验证：25 项新增自动化测试通过，其中1项连接真实 Temporal 临时测试服务；另外启动了官方 Symphony 原生二进制并检查 `/api/v1/state`。没有连接你的真实 tracker、Codex 账号、Temporal Cloud、仓库或 GPU；仍须完成下方账户与项目配置。

## 1. 部署拓扑

```text
GitLab/GitHub issue + agent-ready
  → Symphony → issue workspace → Codex → 候选提交 / draft PR / 不可变 manifest
  → handoff.json → 持久 outbox → 独立 bridge
  → Temporal ExperimentWorkflow → 现有 runner / 独立门禁 / 人工 release
  → receipts + agent-review / agent-blocked
```

- **Symphony**：持续领取开发工单、创建独立 workspace、运行 Codex。并发默认3；不是GPU并发。
- **bridge**：接收准入过的请求，唯一一次启动或找回 Temporal workflow，查询结果并同步标签。没有 release、merge、基线发布能力。
- **Temporal**：现有实验生命周期与人工 release 保持不变；Cloud worker与GPU adapter仍按 `../temporal/README.md` 部署。
- **准入**：对“启动这个确切实验”的权限与预算进行核验。使用现有受信 CI/操作员；不是另建一个模型自评关卡。最终采用的人工 release 是另一件事。

官方源码固定到 `be10a1b79df723d6d7612b5651c8522704dafb2e`。当前上游实现仍标为 prototype；建议在一个受控项目试点。本包不复制或修改上游代码，不把整个框架包装成一个 skill。

## 2. 文件与部署前提

将完整套件放到两种 CPU 服务均可读取的相同绝对路径，例如 `/opt/training-efficiency-kit`。Python 3.12；模型通过 Codex 使用云端服务。

|进程|可以访问|不能访问|
|---|---|---|
|Symphony + Codex|工作区RW；outbox写；receipts只读；套件/config只读；模型身份；限定项目tracker身份|Temporal密钥、admissions、bridge数据库、正式baseline写权限|
|bridge|outbox读；receipts写；admissions读；持久state读写；baseline只读；Temporal与tracker身份|候选工作区执行权限；任意shell命令；正式代码合并权限|
|受信CI/操作员|admissions写；批准契约与资源策略；已有baseline读|不能用候选自填的PASS替代验证|

用独立容器/用户和挂载权限实现边界。仅在同一Unix用户下分两个进程、隐藏环境变量或把路径移到工作区外，不能实现上述隔离。`codex_launcher.py` 会清理控制面环境变量，但它不替代容器/用户隔离。

bridge的SQLite+flock仅限一个协调主机的持久本地卷，可跨进程重启，不支持多主机共享NFS写。横向扩展编码agent无妨；需要多个bridge时先将ledger换为事务数据库。outbox要支持原子硬链接发布；对象存储接口属于后续平台适配。

## 3. 安装 Symphony

已验证官方 Linux x86_64 Burrito 可执行文件，内含 Erlang/Elixir；你仍需安装并登录 Codex、配置 Git 访问。首次解包运行会在服务用户目录产生运行时缓存。

```bash
cd /opt/training-efficiency-kit/symphony
python3 install.py --output /opt/symphony/symphony
python3 native_smoke.py --binary /opt/symphony/symphony
```

`install.py` 根据 `upstream.lock.json` 校验SHA256。nightly URL是滚动地址；如果上游更新导致摘要不匹配，安装失败，不会自动信任新版本。此时按固定源码构建：

```bash
git clone https://github.com/openai/symphony.git /opt/symphony-source
cd /opt/symphony-source
git checkout --detach be10a1b79df723d6d7612b5651c8522704dafb2e
cd elixir
mise trust
mise install
mise exec -- mix setup
mise exec -- mix build
```

源码构建路径在配置中填 `/opt/symphony-source/elixir/bin/symphony`，启动时确保对应 Erlang/Elixir 在 PATH。其他平台使用此固定源码流程或核验相应官方发布包；本包只锁定并实测Linux x86_64二进制。

工具入口：[Symphony README](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/elixir/README.md) · [mise](https://mise.jdx.dev/getting-started.html) · [Codex](https://developers.openai.com/codex/) · [App Server](https://learn.chatgpt.com/docs/app-server)。

## 4. 填项目配置并生成 WORKFLOW

```bash
cp config.example.json /etc/agent-pipeline.json
# 编辑 project、api_url、repo_url、绝对目录、baseline_file 和可执行文件路径。
python3 configure.py --config /etc/agent-pipeline.json \
  --output /etc/symphony/WORKFLOW.md
```

`configure.py`只生成一次，已有输出拒绝覆盖。升级时生成新路径、审查diff，再切换服务。默认GitLab配置；GitHub修改：

```json
{
  "provider": "github",
  "project": "YOUR_ORG/YOUR_REPO",
  "api_url": "https://api.github.com",
  "token_env": "GITHUB_TOKEN",
  "repo_url": "git@github.com:YOUR_ORG/YOUR_REPO.git"
}
```

以上是需要替换的字段，其余字段保留。GitLab自建实例使用其HTTPS `/api/v4` 地址。项目ID采用GitLab路径或GitHub owner/repo；请求中的issue_id分别是GitLab **IID** 与GitHub issue number，不是GitLab全局ID。

在项目中创建四个标签：`agent-ready`、`agent-waiting`、`agent-review`、`agent-blocked`。把这些标签的变更权限定给工作流服务与负责人。普通业务标签不受影响；bridge不关闭issue、不发评论、不合并代码。上游原生工具可读写tracker，能力范围仍受其token控制；只给项目所需权限。

上游目前还支持Linear/Jira/Asana，但本bridge没有这些平台的结果同步实现；不能只改provider字符串就声称支持。

## 5. 启动两个服务

**Symphony服务环境**注入tracker token、Codex模型身份和必要Git访问；不要注入Temporal凭据。`WORKFLOW.md`通过 `$GITLAB_PAT` / `$GITHUB_TOKEN`引用凭据，文件中没有token值。

```bash
python3 /opt/training-efficiency-kit/symphony/launch.py \
  --config /etc/agent-pipeline.json \
  --workflow /etc/symphony/WORKFLOW.md \
  --logs-root /var/log/symphony
```

launch脚本传递上游要求的 unattended acknowledgment 参数；默认保留 `workspace-write` 和拒绝扩大权限的策略。Codex无法完成commit/push时，接团队已有Git/CI执行器；不要改成danger-full-access来掩盖接入缺口。Codex的可用版本由你现有环境固定，并验证 `codex app-server`。本次没有替你登录或调用付费模型。

Dashboard默认只监听 `127.0.0.1:4000`。远程查看用SSH转发或带身份认证的公司网关；不要直接暴露裸端口。systemd/容器平台负责服务重启，状态卷和outbox必须持久保留。

**bridge服务环境**只注入本服务所需的tracker和Temporal配置：

```bash
cd /opt/training-efficiency-kit/symphony
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Secret由部署平台注入：TEMPORAL_API_KEY、tracker token。
# 连接项：TEMPORAL_ADDRESS、TEMPORAL_NAMESPACE、PERF_TASK_QUEUE。
python bridge.py --config /etc/agent-pipeline.json run
```

这不会启动Temporal worker；实验worker是独立服务，仍执行 `../temporal/perf_temporal/worker.py`。该worker必须已有真实cluster adapter。

## 6. 第一张工单：从候选到实验

1. 建一个边界明确的试点issue，填写baseline、允许改动、E/N/A、验收、资源预算；加 `agent-ready`。
2. Symphony克隆独立workspace，Codex实现候选并提交draft PR/MR。agent输出 `.symphony/handoff.json`，格式见 `request.example.json`。
3. `after_run`发布请求到outbox；因为上游忽略after_run失败，`before_run`还会恢复pending请求，并阻止重复编码。HOOK只执行套件中受信代码，不执行候选仓库的脚本。
4. CI先核对真实远端commit、manifest内容/摘要、资源模板、验收契约及权限，再批准**确切请求字节**。示例命令仅供这个受信CI或操作员：

```bash
python bridge.py --config /etc/agent-pipeline.json admit \
  /srv/agent-outbox/YOUR_PROJECT_ISSUE_REVISION.json \
  --authorization-receipt YOUR_EXISTING_CI_RECEIPT \
  --valid-hours 24
```

`authorization-receipt`是现有审批记录引用；CLI本身不验证它的SSO签名。这里的权威来自CI/操作员及私有admissions卷的写权限，不能给实施agent该命令的有效权限。生产平台已有签名准入时可替换此文件接口。

5. bridge校验scope、请求SHA、baseline快照和有效期，保存SUBMITTING意图，再启动固定 `perf-experiment/<experiment_id>`。首次提交超时后只查询，不再生成新ID。成功后移除ready、添加waiting。
6. Temporal进入 `AWAITING_RELEASE` 时仍保持waiting。使用原有审批页面/CLI审核证据；bridge不能release。
7. `INTEGRATION_TASK_CREATED`映射review，其余终态映射blocked。完整结果写入receipts。人工按原开发流程审查与合并，CI再核对实际merge SHA与当前baseline。

查看状态：

```bash
python bridge.py --config /etc/agent-pipeline.json status
# 单次处理/诊断：
python bridge.py --config /etc/agent-pipeline.json once
```

首次准入不能只有`contract_approved=true`，也不能用文件存在代替真实commit/数据/资源验证。桥接层不下载任意manifest或执行其命令；实际内容与runner模板的核验仍由已批准的CI及Temporal cluster adapter完成。

## 7. 重试、Rework与异常

|情况|处理|
|---|---|
|同一请求再次出现|对比原始字节；一致则找回原workflow，不重跑|
|相同experiment_id、不同SHA/URI/时限|拒绝；新候选使用新revision|
|start成功但reply丢失|查询同一workflow ID并核对原始启动输入、固定run ID|
|SUBMITTING/RECONCILING查不到执行|保持待核对，禁止自动再start；可能是提交前崩溃，也可能是history过期|
|Temporal历史过期但ledger仍在|不根据NOT_FOUND重新创建实验；查保留证据/runner ledger|
|tracker暂时不可用|保留workflow与ledger，重试标签同步；不再次启动实验|
|issue被人关闭或状态标签已变|保留平台变化，不重新打开issue；终态收据记录同步结果|
|人工要求Rework|原实验确认终态后，负责人清理旧workflow标签并加ready。before_run把旧handoff归档，再允许编码；新manifest必须新experiment_id|
|发现仍在运行的旧实验|先使用原Temporal受控取消入口并确认终态，不能靠移除标签或删workspace取消GPU|
|撤销admission|阻止尚未提交的实验；已经启动的实验必须走Temporal取消流程|

对不明确的start不提供“强制重试”按钮。操作员先查Temporal与runner ledger；若确认从未提交且不存在任何副作用，可通过受审计维护操作处理记录。不要删除整个数据库或改名实验来绕过核对。

## 8. 测试与真实接入清单

```bash
# 需要PyYAML仅用于验证生成的WORKFLOW；运行模块不依赖它。
python -m pip install PyYAML==6.0.3
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s tests -v
python native_smoke.py --binary /opt/symphony/symphony
```

已验证25项测试：24项协议/逻辑测试，1项使用真实Temporal test server、既有ExperimentWorkflow与假GPU/审批adapter的集成测试。覆盖重复领取、丢失回执、重启、相同ID不同输入、基线变化、准入过期、标签部分失败、人工release边界、旧结果和Rework。测试不访问真实tracker，不调用Codex模型。

上线还要执行一个真实小工单：领取→clone→Codex→commit/draft PR→CI准入→Temporal→runner→证据→人工release→review标签。特别检查模型认证、Git权限、tracker token权限、挂载隔离、真实API限流/失败、Cloud网络、worker可用性。没有完成这些步骤时，状态应写“框架连接代码已实现，真实服务待接入”。

## 9. 参考

- [固定版本Symphony代码与部署说明](https://github.com/openai/symphony/tree/be10a1b79df723d6d7612b5651c8522704dafb2e/elixir)
- [Symphony SPEC](https://github.com/openai/symphony/blob/be10a1b79df723d6d7612b5651c8522704dafb2e/SPEC.md)
- [GitLab Issues API](https://docs.gitlab.com/api/issues/)
- [GitHub issue labels API](https://docs.github.com/en/rest/issues/labels)
- [Temporal Python Client](https://docs.temporal.io/develop/python/client/temporal-client)
