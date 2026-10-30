# 工具接入与边界

Ergora 的工具绑定由具体消费者读取。默认 `agentflow` 参考执行器保持原配置；可显式启用共享同一调用所有者的六阶段桥接。角色、stage-json 协议、mini-swe-agent 和 ForgeKernel 配置见 [Agent 手册](AGENT_BACKENDS.md)。`ergora tools list` 展示本版本已实现的选择，`tools doctor PROJECT` 检查本地可用性或标记服务连通性尚未验证；认证与效果要通过实际任务确认。

## 实现与审查

绑定 `{"tool":"codex","model":"MODEL_ID"}` 或 `{"tool":"claude-code","model":"MODEL_ID"}`。模型字段可省略以采用工具自身配置；认证沿用工具自己的环境/登录。自有工具使用 `{"tool":"command","argv":["/path/to/tool","arg"]}`，提示作为 stdin，工作目录是注册的项目根，命令无 shell 拼接。相对可执行路径相对项目根。

`ergora agent run` 每次启动独立进程。Codex 使用 ephemeral 会话，reviewer 使用 read-only sandbox；Claude reviewer 限制内建读取工具并使用严格空 MCP 配置。它们仍受工具自身实现和用户环境影响，不是操作系统隔离证明。新入口不会为了执行成功自动取消 sandbox。

退出码、超时和 SIGINT 取消均留存；同进程组后代在命令结束时清理。工具须以受控前台命令运行。机器故障后的遗留 running 不是可靠恢复终态，需操作者对账；正式工作流恢复沿用参考 Temporal。返回 succeeded 只证明命令退出成功，不代表正式代码审查通过。

## 项目记忆

默认 `{"tool":"sqlite"}` 是无需服务的持久基线，支持记忆、来源、修订、纠错和检索。例如：

```bash
ergora memory save my-project --text note.md --source git:docs/design.md --source-revision COMMIT_SHA
ergora memory list my-project
ergora memory search my-project 'deployment port'
ergora memory history my-project MEMORY_ID
ergora memory save my-project --id MEMORY_ID --revision 1 --text corrected.md --source git:docs/design.md --source-revision NEW_COMMIT
ergora memory restore my-project MEMORY_ID --from-revision 1 --revision 2
ergora memory delete my-project MEMORY_ID --revision 3
ergora memory sync my-project
```

SQLite 基线按词包含检索，不提供 embedding 或自动事实提炼。删除清空应用中的历史正文与来源，保留删除标识；独立备份须单独处理。停写后备份完整 `ERGORA_HOME`，在新设备使用同一个目录即可恢复项目配置、记忆和证据；项目路径变化时须重新注册适合新设备的项目，不把不明路径当成原 checkout。

### 可选 ReMe

ReMe 是独立服务，不是默认 Python 依赖。支持接口依据 [固定官方提交](https://github.com/agentscope-ai/ReMe/tree/1e51e0dc1b1effe60f7ee425298f3b6f8ef4cbd9)，可在单独 Python 3.11+ 环境中安装此版本，避免影响 Ergora 和既有训练依赖：

```bash
python3 -m venv "$HOME/.local/share/ergora-reme-venv"
"$HOME/.local/share/ergora-reme-venv/bin/pip" install 'reme-ai[core] @ git+https://github.com/agentscope-ai/ReMe.git@1e51e0dc1b1effe60f7ee425298f3b6f8ef4cbd9'
"$HOME/.local/share/ergora-reme-venv/bin/reme" start workspace_dir="$HOME/.local/share/ergora-reme/my-project" service.port=2333
```

ReMe 安装和服务在目标环境需单独验收。其依赖与资源需求以固定版本为准；基本 BM25/文件操作不需要模型密钥，自动提炼需要 ReMe 模型配置。建议每个需要隔离的项目使用独立 workspace / 服务实例。

将以下 JSON 保存为 `memory-binding.json`，再用当前项目修订号保存：

```json
{"tool":"reme","endpoint":"http://127.0.0.1:2333"}
```

```bash
ergora project bind my-project memory --binding memory-binding.json --revision CURRENT_REVISION
ergora memory sync my-project
ergora memory search my-project 'deployment port'
```

有网关鉴权时可增加 `"token_env":"REME_TOKEN"`，值只由运行进程环境提供。选择该后端会将项目有效记忆发送到配置的服务；来源与修订仍保留在本地。同步会保留重试标记，响应失败明确报错；服务文件已写入不代表异步索引已经可检索。切换后端不删除旧投影，后续同步继续维护已登记投影；删除后应执行 `memory sync` 并确认所有原端点都已应答。共享 ReMe 服务的项目路径过滤不等于多租户身份隔离。

本轮已验证协议 fixture 和本地语义，尚未运行完整 ReMe / 自动 hooks，也没有声称记忆使模型质量提升。

ReMe workspace 在相同端点被清空或迁移重建后，执行 `ergora memory sync my-project --rebuild` 重写有效投影；普通同步依赖上次写入确认，只发送变更。凭据变量轮换后先保存新绑定并同步一次，再撤销旧变量；mirror 会保存新变量名称以便之后切回本地仍能传播删除。检索同时使用官方 `search_filter.paths` 在限额前限定候选，再对返回路径与本地当前正文复核。

## skill 候选、评价与采用

导入遵循 [Agent Skills](https://agentskills.io/specification) 的目录：`my-skill/SKILL.md`，YAML frontmatter 包含 `name: my-skill` 与 `description`，其余脚本、参考资料和资源随完整目录定址。导入拒绝 symlink / `.git`，限 500 文件 / 10 MB。首个同名导入是明确的初始 baseline；后续导入只创建候选，不替换活动版本。

```bash
ergora skill import my-project ./my-skill
ergora skill list my-project
# 修改独立来源目录，再导入候选
ergora skill import my-project ./my-skill --hypothesis '一个可检验的改进假设'
ergora evaluation register my-project evaluation.json
ergora evaluation run my-project BASELINE_DIGEST --suite SUITE_DIGEST
ergora evaluation run my-project CANDIDATE_DIGEST --suite SUITE_DIGEST
ergora evaluation compare my-project BASELINE_RUN_ID CANDIDATE_RUN_ID
ergora skill adopt my-project --baseline-run BASELINE_RUN_ID --candidate-run CANDIDATE_RUN_ID --revision 1 --reason '已审阅实际证据'
ergora skill rollback my-project my-skill BASELINE_DIGEST --revision 2 --reason '记录回退原因'
```

`evaluation.json` 由项目维护者提供，示例结构如下；数据、命令和阈值应按真实任务填写：

```json
{
  "schema_version": 1,
  "evaluator_argv": ["python3", "evaluate-skill.py"],
  "evaluator_files": ["evaluate-skill.py"],
  "timeout_seconds": 60,
  "minimum_gain": 0.05,
  "max_reported_cost": 2,
  "cases": [
    {"id":"train-1","split":"train","input":{"task":"填写构造任务"}},
    {"id":"validation-1","split":"validation","input":{"task":"填写迭代评价任务"}},
    {"id":"holdout-1","split":"holdout","input":{"task":"填写独立保留任务"}}
  ]
}
```

可信 evaluator 从 stdin 读取 `{"skill_dir":"版本目录","case":具体input}`，在独立工作目录执行，将一份 JSON 对象写到 stdout，例如 `{"score":0.8,"passed":true,"cost":0.01,"feedback":"具体执行反馈"}`。score 必须为 0–1、cost 为非负有限数；`passed` 表示真实项目正确性检查，不能由候选自行宣称。stderr 可输出诊断。`evaluator_files` 声明应固定的评分源文件和依赖文件，它们与解释器被记录 SHA；其他环境、数据和导入依赖仍由维护者固定和复验。

评价集、命令、阈值与文件身份随 suite 固定；argv 中存在的文件也自动补充指纹，避免评分入口漏声明。修改评分文件后要注册新 suite 并重跑双方。候选完整目录的内容与文件可执行位在评价前后、比较和采用时校验身份。采用需要完整双方评价、候选正确性通过、validation 达到 minimum_gain、holdout 不退化，以及当前活动 baseline / 修订一致。部分 train/validation 搜索记录不能替代完整评价。一次最终保留集可用于采用前检查；反复查看和据此调参会污染其独立性，应定期由维护者更新保留集。

成本来自工具报告，超过预算后停止后续调用，不是提供商账单硬限额。实际费用控制应结合提供商配额。进程输出、失败和输入保存在私有运行目录；记忆删除不会追溯改写这些已归档任务输入或独立备份。

### 可选 GEPA

安装 `.[gepa]` 启用固定 `gepa==0.1.4` 引擎；默认优化层 `{"tool":"manual"}` 使用手动导入和同一评价/采用流程。GEPA 绑定示例：

```json
{"tool":"gepa","proposer_argv":["python3","/absolute/path/propose-skill.py"]}
```

```bash
ergora project bind my-project optimizer --binding optimizer-binding.json --revision CURRENT_PROJECT_REVISION
ergora skill optimize my-project --baseline BASELINE_DIGEST --suite SUITE_DIGEST --objective '一个可衡量的改进目标' --max-evaluations 20 --max-proposals 5 --timeout 300
ergora skill optimizations my-project
```

提案命令可以接任意模型/agent，但须遵守 JSON stdin/stdout 协议。stdin 包括 `candidate.skill`（完整 SKILL.md）、`feedback`、`components`、`objective`；stdout 为 `{"skill":"完整新版 SKILL.md","cost":0.01}`。GEPA 搜索/选择由真实 SDK 完成；命令只生成文本。外围文件沿用 baseline，源码和模型配置由项目负责。命令相对路径按项目根解析，无 shell；认证沿用命令环境。

搜索接口只发送 train / validation 材料，不发送 holdout；同一 Unix 用户内没有强文件隔离，不能把接口上的分离解释为恶意工具读不到评分文件。搜索有实际 metric-call / proposal 数、单次调用与总时限、报告成本约束。内部错误和预算终止保留状态，不自动采用、不改评分，也不执行 candidate 附带脚本。候选仍须走完整评价和人工采用。当前验证使用真实 GEPA 与确定性测试提案器，没有真实模型效果或泛化收益结论。

### 在后续工具调用中使用

```bash
ergora agent run my-project implementer --prompt task.md --skill my-skill --recall '相关项目约定'
ergora skill export my-project ADOPTED_DIGEST ./export/my-skill
```

`--skill` 读取该名称当前已采用的完整版本，`--recall` 使用当前项目记忆后端。运行记录保存实际 skill digest、记忆修订和提示摘要；输入归档可核对它们的真实消费。回退后，下次调用读到恢复的活动版本。导出选择新的同名目录，不覆盖项目现存文件；可由维护者按宿主约定安装到项目 `.agents/skills/`。这些操作不改参考六阶段执行器或全局宿主配置。

## 有界资料检查与定时触发

默认研究层为 `{"tool":"urls"}`，只访问你明确指定的 HTTP(S) 资料，保存原始快照 SHA 和来源，内容改变才提出新候选。它提供资料变化检查，不自动撰写模型调研结论、执行网页指令、写入活动记忆或修改 skill。

```bash
ergora research run my-project https://example.com/official-doc --id docs-check-r1 --max-bytes 1000000 --timeout 30
ergora research list my-project
ergora research show my-project docs-check-r1
ergora research proposal my-project PROPOSAL_ID
ergora research review my-project PROPOSAL_ID --status reviewed --revision 1 --reason '核对来源与适用版本'
ergora research cancel my-project docs-check-r1
```

同一 ID 的输入冻结；终态重复调用返回原结果，不重新抓取。进程中断后以相同 ID 和相同输入恢复已记录的来源，保留累计字节与运行时间预算；最后 checkpoint 后无法证明的运行时间保守计费，可能耗尽剩余时间。未确认结束的传输保留其剩余字节额度（`reserved_bytes`），恢复会可见失败；需要再次抓取时显式新建有新预算的任务。来源一次 1–10 个，字节是整个任务接收的正文预算；重定向正文直接关闭。抓取失败、限额、超时与取消保留状态；DNS、响应头和正文抓取使用可终止的 Linux 子进程，父进程死亡时同时终止。取消请求后仍须查看实际确认终态。审阅资料不会自动采用；可将自己确认的摘要通过 `memory save` 写入，并把来源 URL 和快照 SHA 作为 source/revision。

默认检查 DNS 结果并拒绝私网地址，重定向也受同一检查；可信内网资料可明确追加 `--allow-private`。这不是网络沙箱或 DNS 重绑定隔离，来源应由操作者信任并配合实际网络策略。HTML 以纯文本预览，脚本不执行，原始数据只作为下载/证据文件保存。

### Temporal 持久调度

安装 `.[temporal]` 使用与参考发行一致的 SDK `1.34.0`。先提供可连接的 Temporal 服务；本机开发可使用 `temporal server start-dev --db-filename "$HOME/.local/share/ergora/temporal.sqlite"`，生产部署按 Temporal 官方文档配置。绑定示例：

```json
{"tool":"temporal","address":"127.0.0.1:7233","namespace":"default","task_queue":"ergora-my-project-research"}
```

```bash
ergora project bind my-project scheduler --binding scheduler-binding.json --revision CURRENT_PROJECT_REVISION
ergora research worker my-project
# 另一个终端；创建时保持暂停
ergora research schedule my-project create official-docs --url https://example.com/official-doc --interval 86400 --max-bytes 1000000 --timeout 30
ergora research schedule my-project trigger official-docs
ergora research schedule my-project status official-docs
ergora research schedule my-project resume official-docs
ergora research schedule my-project pause official-docs
ergora research schedule my-project delete official-docs
```

worker 使用同一个持久 `ERGORA_HOME`，按项目绑定；不同项目使用不同 task_queue。建议用 Supervisor 管理该前台命令。Schedule 保存在 Temporal，worker 可以重启；同一活动重试使用同一研究 ID 对账。每次调度有独立预算，重叠选择 SKIP，默认暂停、失败后暂停，不追赶大量历史任务。频率与每次预算共同决定长期总量，启用前由操作者确认。

暂停 Schedule 不取消已启动的观察；通过 `research cancel` 取消相应研究记录并确认终态。Temporal 本地参考服务的连接配置面向受信任的环境，本入口尚未封装生产 TLS/服务身份管理。研究 ID、快照和候选可在 CLI / 控制台查看，Temporal UI 用于流程历史；它们不依赖 GitHub/GitLab 工单或聊天通道。
