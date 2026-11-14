# 预训练／后训练 PR、MR 审查工具调研

读取日期：2026-11-15（Asia/Shanghai）。Ergora 静态基线为 `871cc4b6b2c21420307a002bf5b983707720fe90`。本文只做公开一手来源读取和采用建议；未安装工具、执行第三方脚本、调用审查模型或训练、读取凭据、发布评论。与[本轮计划](../plans/2026-11-15-domain-review-optimization-quality.md)配套，不能作为新增能力的验收记录。

**建议先交付精确、只读、可离线重放的 PR／MR 输入包，再以现有 Claude／Codex 后端承载预训练与后训练两类 reviewer。** 领域知识优先采用 Megatron Bridge 和 slime 的具体合同；BBuf 的指定版本主要补充 serving、模型接入和 kernel 证据。通用审查程序、Git 平台连接与评论发布应独立选择，不能把安装插件当成训练语义已受审查。

## 1. BBuf 指定版本和账号内候选

### 精确身份

|项目|本次核到的身份与内容|采用决定|
|---|---|---|
|AI-Infra-Auto-Driven-SKILLS `v0.1.6`|发布页指向 `316923d44e2645644f03df2d22326dd272105436`，2026-10-31 发布；源码归档实际有 **10 个任务 Skill＋1 个历史知识库 Skill**。README 的 11 和发布说明的 10 使用不同计数口径。插件 manifest 自报 **0.10.0**，不能拿它代替 release tag。[发布][bbuf-release]、[固定 README][bbuf-readme]、[manifest][bbuf-plugin]|按这个 SHA 评估，不按账号主页的活动分支安装；本轮未安装。|
|同仓库当前活动分支|本次仓库页面读到 `974861d46125f2d6362f09de3e6bbc5fcb51886d`，与指定 release 分开。本文的 Skill 内容判断固定于上述 `316923d…`。[活动分支快照][bbuf-main]|不把 main 后续变化归给 v0.1.6。|
|SGLang Review Inbox|v0.1.6 发布说明推荐 `BBuf/sglang-review-inbox`，描述含 review、独立复核、CI、讨论、approve、merge 和 Slack 回写；本次仓库页与 `main/README.md` 均为 HTTP 404。[发布说明][bbuf-release]、[被引用仓库][bbuf-inbox]|**仅核到发布者描述，未核源码、接口、许可或可安装性**；不能登记为可用集成，也不能把它的自动发布／合并流程搬入只读 reviewer。404 不证明项目不存在。|
|KDA-Pilot|`bac966ba09fe22f6220ff527c7c3555e539d5fe6` 的 README 定位为 SGLang kernel 优化 campaign，含固定 workload、成对 benchmark、正确性与 NCU 证据。[源码][kda-readme]|借鉴 kernel 变更的证据合同；不是预训练／后训练整体 PR 审查器。本次未审其执行器；根 `LICENSE` 读取 404，复用许可未核清。|
|KernelWiki|`76d27b56f804e7e7295d4c570e1e5d7eef4b0a75` 的根 `SKILL.md` 面向 Blackwell／Hopper kernel，明确排除一般 host 集成与分布式系统；知识截止自报 2026-04-27。[Skill][kernelwiki-skill]|只在相关 kernel 改动时查询并回到原始 PR；不能覆盖 collective／训练目标／恢复。根 `LICENSE` 读取 404，本次不搬运知识库。|

账号发现入口是 [BBuf 仓库页][bbuf-account]，上述项目来自该页与指定仓库的官方链接；没有穷举账号所有历史仓库。v0.1.6 固定归档未找到仓库级 `LICENSE`／`COPYING` 文件，而 manifest 写 `see LICENSE`，故本次**不将其认定为 MIT／Apache 已授权的可再发行包**。先链接与借鉴方法；若未来内置其正文／代码，须补许可和完整资源依赖核验。[固定源码树][bbuf-tree]、[manifest][bbuf-plugin]

### 哪些 Skill 对训练代码审查有用

下面列全 v0.1.6 的任务 Skill，区分直接职责与可借鉴部分。目录均相对固定仓库根；`model-pr-history-knowledge` 的实际目录另为 `model-pr-optimization-history/`。[完整入口][bbuf-readme]

|真实目录／Skill|适合审查的部分|限制和选择|
|---|---|---|
|`skills/model-optimization/sglang-model-day0-support/`|模型结构→SGLang 改动边界、PR 依赖、验证矩阵与发布条件；可审后训练 rollout 的模型接入兼容性。[Skill][bbuf-day0]|是 **SGLang support** 合同，不是 trainer 或 RL 目标审计。按需引用。|
|`model-pr-optimization-history/`|`model-pr-history-knowledge` 查询 SGLang／vLLM／TensorRT-LLM／TokenSpeed 的 118 份模型族档案及历史风险。[Skill][bbuf-history]|生成条目标明非人工完整审计；历史日期不能证明当前 dispatch／数值默认值，仍须读目标 SHA、完整 diff 和调用者。|
|`skills/llm-torch-profiler-analysis/`、`skills/llm-pipeline-analysis/`、`skills/torch-profiler-layer-track/`|已有 trace 的 kernel 归因、层／forward 边界、时间范围与可视化；为性能类 PR 提供证据阅读方法。[profiler][bbuf-profiler]、[pipeline][bbuf-pipeline]、[layer track][bbuf-layer]|主要围绕推理 trace；训练反向、optimizer、跨 rank 的覆盖要另建合同。layer track 只是显示变换，不是运行优化。|
|`skills/llm-serving-auto-benchmark/`、`skills/llm-serving-capacity-planner/`、`skills/model-compute-simulation/`|同 workload／SLA 的 serving 比较、KV／请求容量、serving shape 的 FLOPs／MFU；适合审 rollout 服务配置与相应性能声明。[benchmark][bbuf-benchmark]、[capacity][bbuf-capacity]、[compute][bbuf-compute]|不能把 KV 容量或 forward FLOPs 当训练 activation／optimizer 内存或训练 FLOPs。不是预训练 loss、梯度或 checkpoint 审查器。|
|`skills/sglang-prod-incident-triage/`|请求回放、部署后错误输出、hang／队列和资源问题的证据整理。[Skill][bbuf-incident]|作为 rollout serving 故障资料，不承担训练算法正确性判定。|
|`skills/model-architecture-diagram/`、`skills/sglang-explainer-video/`|前者返回原始公开结构图；后者把 PR／文章制作成讲解视频。[diagram][bbuf-diagram]、[video][bbuf-video]|图与讲解有助理解，本身不产生代码正确性验收；本片不优先接入。|

manifest 虽含 `code review` 描述，指定归档没有一个名为通用 `code-review` 的任务 Skill，不能据描述推导存在该接口。部分 Skill 引用仓库外层 `docs/upstream-source-contracts.md` 等资料；仅拷一个 `SKILL.md` 会丢上下文。未来按完整依赖打包，不能照搬宿主 symlink 安装法而宣称已满足 Ergora 的完整树导入合同。[固定源码树][bbuf-tree]、[Day-0 Skill][bbuf-day0]、[Ergora 资源合同](../AGENT_DEFINITIONS.md)

## 2. Claude 的几种审查能力必须分开

Anthropic 当前官方总览自己区分本地命令、托管 Code Review、Ultrareview 和自有 CI。本次核到“Claude 有现成 code review”，但没有做质量对比实验，不能宣称其对所有训练变更最佳。[官方比较][claude-review]

|产品／接口|真实行为与接入条件|Ergora 决策|
|---|---|---|
|**内建本地 `/code-review`**，`/review` 是别名|任意计划可用；目标可为 branch、PR、路径或 Git revision range，非交互 `-p` 等待并在回复中返回结果。默认报告，`--fix` 请求编辑，`--comment` 请求发布；GitLab MR 通过 `glab` 发一条 note，要求 Claude Code ≥2.1.257，自管 GitLab 应传 URL 或 `!iid`。读 `CLAUDE.md`，不读托管服务的 `REVIEW.md`；内建指令没有可编辑的本地 `SKILL.md`。[本地文档][claude-local]|最接近“本地可调用审查”；未来可单独验证 CLI 版本和结果适配。**现有 Claude driver 不等于已经包装此命令**，本片先用领域资料＋原结构化 reviewer 合同。|
|**官方 `code-review` 插件**|固定插件仓库 `b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6`；`plugins/code-review/.claude-plugin/plugin.json` 版本 1.0.1。命令源码用 `gh`，先跳过 closed／draft／不需审查／Claude 已评论的 PR，四个审查 agent 再验证问题；无 `--comment` 时停在终端，有此参数时可发 summary 或调用 inline-comment MCP。[manifest][claude-plugin-meta]、[命令源码][claude-plugin-command]|这是另一份可检查的提示与工具流程，**GitHub 专用**，不能冒充内建命令的 GitLab 支持或托管服务。借鉴“候选 finding→复核”，不直接塞入只读叶；它假定工具可用，并请求 Bash／发布工具。|
|**官方 `pr-review-toolkit` 插件**|同一固定仓库、manifest 1.0.1；`/pr-review-toolkit:review-pr` 按 comments／tests／errors／types／code／simplify 调用六类 agent，可请求并行；通用代码 reviewer 按项目规则审查，非训练专用。[manifest][claude-toolkit-meta]、[命令][claude-toolkit-command]、[reviewer][claude-toolkit-reviewer]|借鉴测试价值、错误处理和类型不变量的分工；`simplify` 含修改职责，不能当整包只读审查。已有 Ergora 三路审查可承接，避免再套一层调度。|
|**Claude Code GitHub Action**|源码固定 `9fa68854da5fadef4ed3dce240325a0dfe251880`，在自己的 GitHub runner 运行 Claude；`prompt`、`claude_args`、`plugins`、`plugin_marketplaces` 等是实际输入，可监听事件或 `@claude`；认证与 GitHub 写权限需独立配置。[action.yml][claude-action-yml]、[官方文档][claude-actions]|是 CI／平台自动化程序，可实现也可审查，**不是托管 Code Review**。将来需要 GitHub 事件自动触发时再接；不替代领域专家或 Ergora 的候选证据。|
|**Claude Code GitLab CI/CD**|官方文档标为 beta，并明确由 GitLab 维护；在自有 runner 中运行 CLI，示例需要 `.gitlab-ci.yml`、模型认证、GitLab API 权限；评论触发还需 webhook／监听器编排。[官方文档][claude-gitlab]|作为未来 CI 接法研究，不能把 GitHub Action 直接称为 GitLab adapter；本次未验证实例、权限或流水线。|
|**托管 Code Review**|Team／Enterprise，GitHub（含文档所述企业实例），在 Anthropic 基础设施读取 diff／周边代码，验证后发布 inline comments／summary／check；**不 build／run 代码，不 approve／block PR**。Owner 安装 App 并设置触发，也可由有写权限者评论 `@claude review`；不运行于自托管环境，目前 ZDR／HIPAA／CMEK 有可用性限制。[官方文档][claude-review]|可作为独立外部建议来源，不能代替实际数值／分布式检查。已核入口是 App／设置／评论，未核到可复用的通用服务 API 合同；不要先虚构 Python reviewer 接口。|
|**Ultrareview**，`/code-review ultra`／`claude ultrareview`|research preview，claude.ai 登录的云端审查；分支模式上传本地状态，PR 模式从 github.com clone。`claude ultrareview … --json --no-post` 等待并输出结果；`claude -p '/code-review ultra'` 启动后不等待。默认 diff 上限为 500 文件／8,000 changed lines，文档允许变动；命令完成即 exit 0，含有 finding 也如此；中途退出云端任务可能仍在跑，再调用是新审查。[官方文档][claude-ultra]|是另一种外部运行／计费／恢复合同；不把 CLI exit 0 当 approve，不以重试覆盖 unknown。不是当前默认后端能力。|

两处需要特别防止文档漂移：`code-review` 插件 README 描述过 history/blame 和 ≥80 评分，而本次固定命令正文实际是双规则检查＋双 bug 检查＋验证，不应以 README 替代执行说明；该 README 的旧版本、toolkit README 的 MIT 字样也不能覆盖同提交的 manifest 与各自 **Apache-2.0 LICENSE**。Action 则是 **MIT**；Claude Code CLI 仓库声明受 Anthropic 商业条款约束，不能把插件许可当作 CLI／云服务许可。[插件 README][claude-plugin-readme]、[toolkit README][claude-toolkit-readme]、[命令][claude-plugin-command]、[code-review 许可][claude-plugin-license]、[toolkit 许可][claude-toolkit-license]、[Action 许可][claude-action-license]、[CLI 许可声明][claude-cli-license]

托管服务的 `REVIEW.md` 可表达领域规则，也可包含 Skill 文件，但有保护分支与大小限制：总 include 最多八份／150,000 bytes，单 Skill 30,000 bytes；这是**读取资料**，不是运行 Skill 的脚本／工具。不要据此宣称完整训练 Skill 包已执行。[定制文档][claude-customize]

## 3. 训练领域知识与验证工具

本次 Bridge 快照为 **`40d446774bb17a5dfe1029afd0fd18004d49dafb`**；原 11 月 12 日研究中的 `5569483…` 是另一次读取，不能混称同版。下列是可审查的领域指导及其指向的验证工具，尚不是 Ergora 新增的可执行 reviewer。[Bridge 固定树][bridge-tree]

|来源与许可|对预训练／后训练 PR 的具体价值|采用边界|
|---|---|---|
|Megatron Bridge `skills/review-pr/SKILL.md`；Apache-2.0|分阶段读取原 PR／diff 与调用者，再检查数值语义、distributed invariants、checkpoint／转换、collective 次序、重算／offload／overlap、真实热路径成本，最后尝试推翻自己的 finding。[Skill][bridge-review]、[许可][bridge-license]|**优先适配为预训练审查基础**。保留数值／运行合同方法，不照搬 Bridge 专用禁改目录、命令和全部仓库政策。其源码要求默认单 agent；不是需要整体安装的 agent 服务。|
|Bridge `parity-testing`、`nemo-mbridge-mlm-bridge-training`|权重 exact round-trip、forward 关联与 training parity 分级；MLM／Bridge 配置对齐和 mock loss correlation。[parity][bridge-parity]、[MLM][bridge-mlm]|借鉴“序列化、forward、梯度／更新、恢复、长期质量分别举证”。forward 关联或短 mock 不能替代训练收敛；Skill 指向的 GPU 检查本轮未运行。|
|Bridge `nemo-rl-e2e-testing`、`verl-e2e-testing`|外部后训练兼容检查包含 policy／reference／rollout、checkpoint／resume、权重 refit、并行、模态和 learning signal 的分级；明确基础 smoke 不等于收敛。[NeMo-RL][bridge-nrl]、[verl][bridge-verl]|**优先适配后训练的跨组件证据矩阵**；rollout／reward／trainer 生命周期仍由真实框架持有，不在 Ergora 复制训练器。|
|slime `79aa41a884ab0bf65222c94418f6357d3c31192b`，`.claude/skills/slime-code-review-preferences/`；Apache-2.0|确有代码审查 Skill，主要覆盖 API 边界、分支、状态归属、保持 hooks 签名等；明确 `args` 是配置，actor／cache／恢复进度应由生命周期 owner 持有。[Skill][slime-review]、[许可][slime-license]|适配框架工程审查方法；**不能把此文件夸大成完整 PPO／GRPO 数学审计**。|
|slime 同提交的 `add-reward-function`、`add-rollout-function`、`add-dynamic-filter`|reward group 返回顺序／类型、错误样本、train/eval 不同返回类、tokens／response length／reward／status／loss mask、sample-group 保持和过滤后计数，均有明确源码锚点。[reward][slime-reward]、[rollout][slime-rollout]、[filter][slime-filter]|**优先用于后训练数据与反馈链审查**，按目标 SHA 重读实际实现；新增功能的 guide 不等于自动检出所有算法错误。|
|slime 同提交的 `add-eval-dataset-config`、`add-tests-and-ci`|评估数据配置和既有测试／CI 注册方式。[eval][slime-eval]、[tests][slime-tests]|按目标仓库采用；不让新增 reviewer 任意运行训练、下载数据或默认增加全套 CI。|

结论只限于已读来源：已找到有价值的领域 Skill、真实框架验证路径和通用 reviewer，**本次未核到一个已证明能完整覆盖任意预训练／后训练 PR、执行验证并承担最终批准的现成系统**。这不是“市场没有专用工具”的结论；未评测商业产品或全部相关仓库。

## 4. 常规审查与 PR／MR 连接工具

以下工具解决的层次不同；项目维护与接口可核不等于已证明在训练 PR 上优于现有模型。

|候选／固定身份／许可|实际接口与限制|决策|
|---|---|---|
|**PR-Agent**，现已从 `qodo-ai/pr-agent` 迁至 `The-PR-Agent/pr-agent`；`1b19ab257ec69f658c3047f6ef0bd65551234d59`，pyproject 0.49.0／Python ≥3.12，MIT|CLI 支持 `pr-agent --diff-file change.patch --output review.md --json-output review.json review` 或 `--stdin`；本地 `PlainDiffGitProvider` 可读 working-tree 上下文，缺可信远端 head 身份；reviewer 代码显式处理分块失败、未覆盖文件及 findings 上限。[项目][pragent-project]、[CLI][pragent-cli]、[provider][pragent-plain]、[reviewer][pragent-reviewer]、[许可][pragent-license]|**后续可选的通用建议性基线**。先在独立环境固定版本、输入包和模型，核 JSON／覆盖／失败；不导入完整 Git 平台服务，不把 raw diff 的“无意见”设为 approve。|
|**reviewdog**，`21e8d008e6818af198ca0a9252f0fd7c71754887`，MIT|接 linter／compiler／RDJSON／SARIF 输出并按 diff 过滤，支持 GitHub PR review 与 GitLab MR discussion reporter；默认 `added` 过滤会隐藏某些未改行 finding。[README][reviewdog-readme]、[许可][reviewdog-license]|**发布／诊断格式工具**，没有训练语义或自己的模型审查能力。已有 native adapter 足够时不再套它；真有统一诊断消费者再接。|
|**GitHub CLI** `3d5a9e355a837f2f5ee78d7484c118cc1342ad1a`／**GitLab CLI** `71d2f9135352311e8914c04d6ee9707cf56afc8f`；均 MIT|`gh pr diff/view/review` 和 `glab mr diff/view/note/approve` 是平台读写接口；命令成功不表示代码正确。GitLab CLI 的实际 MR 命令列表没有通用 `mr review` 子命令。[gh diff][gh-diff]、[gh review][gh-review]、[glab MR][glab-mr]、[gh 许可][gh-license]、[glab 许可][glab-license]|适合作为人工／插件的成熟平台客户端；Ergora 已有本族 `IssueBackend`，优先沿原 owner 扩必要只读操作，不建立 shell 和 HTTP 两套权威。|
|**GitLab Duo Code Review Flow**，官方 latest 文档快照|是 GitLab 的 agentic MR 审查产品，与 non-agentic Duo Code Review 分开；使用 GitLab runner，可由 UI 触发，REST 触发标为 experiment；读 `mr-review-instructions.yaml`，明确不读 `AGENTS.md`／`SKILL.md`。预扫描上下文约 1 MiB，超额裁到约 800 KiB；超过 10,000 行文件只给 diff。[官方文档][gitlab-flow]|**GitLab 原生通用审查候选**，不冒称训练专家。实例版本、订阅／credits、管理员设置和模型需另核；本轮未核其实现许可，不复制其源码。不要将 latest 所述所有新功能视为用户实例已上线。|

未来若发布行级意见，必须保存原平台位置语义：GitHub review API 接受 commit／path／line／side；GitLab diff discussion 要求 `base_sha`、`start_sha`、`head_sha` 以及新旧路径／行。普通 note、inline discussion、正式 review／approval 不能互换。[GitHub review API][github-review-api]、[GitLab discussion API][gitlab-discussions]

## 5. 对 Ergora 的状态判断与执行顺序

### 当前支持与尚未实现

|状态|本次固定基线上的含义|
|---|---|
|**已支持**|现有 `ClaudeCodeBackend`／Codex 调用、只读 reviewer 和结构化输出；Claude native reviewer 限 `Read,Grep,Glob`＋空 MCP，task-mcp 模式只给原任务 list/read。它们是模型执行后端，尚未包装上述内建审查命令、插件、云审查或 Action。[源码](../../src/ergora/agent_backends.py)|
|**已支持**|原通用结构／正确性／测试价值审查，以及 measurement reviewer 的候选证据检查；已有 source-candidate PR／MR 关联要求原 task／export／candidate 身份，不能作为任意外部 PR 的独立审查包。[preset](../../src/ergora/data/presets/presets.json)、[关联 schema](../../src/ergora/data/schemas/candidate-review-context-v1.json)、[集成边界](../INTEGRATIONS.md)|
|**上游可安装，Ergora 未接入／本轮未安装**|Apache-2.0 的 Anthropic 插件／Bridge／slime 资料，MIT 的 Action／PR-Agent／reviewdog／CLI 等；各自运行条件、资源依赖、输出协议和效果仍需实测。可公开下载不等于所有上游包都有相同许可。|
|**建议实施**|Q1 独立只读输入包与来源采集，Q2 两领域 reviewer／组合及报告；服务／插件专属 driver、自动 PR／MR 行级意见发布、闭环自动批准都不因本文存在而成为受支持操作。|

### 推荐优先顺序与具体缺口

1. **Q1.1：先固定本地 base／head／实际 diff-base 及完整审查包。** 区分外部 review source 与已有 task-candidate association，不伪造 task／export；记录变更、相关完整源码／调用者／规范、配置、原始检查、未读／超限文件。GitHub files API 有最多 3,000 文件限制，GitLab diff 有分页及 `collapsed`／`too_large` 等状态，完整性不能由一次 `diff` 请求推断。[GitHub API][github-pr-files]、[GitLab API][gitlab-mr-api] 下一片先做离线 Git 对象，不必等待远端写权限。
2. **Q2：在原通用审查组合旁增加两份领域资料与 reviewer。** 预训练按 Bridge 检查 loss／mask／有效 token、梯度与更新时钟、精度、mesh／collective、状态与恢复、热路径证据；后训练先识别 SFT／偏好／RL 的实际算法，再核 rollout／reward／group／mask／policy-reference／权重版本及训练反馈。每条 finding 要有目标 SHA 的源码位置、可达场景与后果；公式和阈值按目标框架，不硬套一个默认算法。[Bridge 方法][bridge-review]、[后训练分级][bridge-nrl]、[slime 数据合同][slime-rollout] 这属于拟新增检查范围，本文未证明模型能可靠检出这些错误。
3. **先评价审查效果，再接更多模型／服务。** 用已知领域缺陷、有效非默认配置与缺证据样例，比较原通用 reviewer 和加入领域资料后的真实叶调用；记录确认缺陷、误报、覆盖、失败、耗时与预算。高置信、自报 approve、多个 agent 同意、CLI exit 0 均不能替代独立训练 oracle。PR-Agent 本地 JSON 可作后续建议性对照，暂不设 required。
4. **Q1.2／远端发布后置。** 只读采集沿现有本族 adapter，漂移 head 产生新包；之后若有真实发布需求，再增加精确位置预览、显式发送意图、陈旧 head 拒绝和 unknown 对账。普通结果报告先可用，不默认发送、approve 或 merge；已有 candidate association／issue writeback 保留原合同。
5. **最后按消费者选择插件／CI／托管服务。** 优先可核的领域资料，不默认整体安装 BBuf 包、KDA campaign 或外部平台。BBuf 许可、Review Inbox 可读源码／接口、插件运行权限、云服务输入／输出／取消及费用，均是各自后续准入缺口；不为填工具目录预建通用插件层。

## 6. 读取范围与失败记录

已读：指定 release、固定归档中全部 11 个 `SKILL.md` 与目录清单、BBuf 账号候选及上述 KDA／KernelWiki 入口；Anthropic 官方审查文档、固定插件 command／agent／manifest／LICENSE 和 Action 输入；表中固定 Bridge／slime Skill、PR-Agent CLI／provider／reviewer、reviewdog 文档／许可、gh／glab 与平台 API 文档。**未审** BBuf 所有历史档案／视频与 capture 脚本、Inbox 源码、KDA 运行器、Bridge／slime 的全部 trainer 源码与其完整回归、各商业服务内部实现；未对任何工具做安装、模型效果或平台权限验收。

网页检索工具返回不可用；GitHub 公共 API 在取得 release／仓库信息后返回 403 rate limit。随后用公开 GitHub HTML、固定 raw、codeload 和 GitLab 公共 API 收敛，未使用认证绕过限制。`git ls-remote` 读取超时，故 tag→SHA 以 release 页的 commit 链接及固定源码为证。最初猜测的 `anthropics/claude-code/plugins/...` 路径 404，实际读取的是 `anthropics/claude-plugins-official`；`glab mr review` 文档路径 404 后以官方 MR 命令表核实。固定 SHA 的 glab raw 文件返回 403，LICENSE 另通过同 SHA 的[公开 repository-files API][glab-license-api]读取成功。GitLab 商业条款页本次 502，故未宣称完成 Duo 产品许可审计。不可访问来源与未读范围均不作为“市场无此工具”的证据。

[bbuf-release]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/releases/tag/v0.1.6
[bbuf-readme]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/README.md
[bbuf-tree]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/316923d44e2645644f03df2d22326dd272105436
[bbuf-main]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/tree/974861d46125f2d6362f09de3e6bbc5fcb51886d
[bbuf-plugin]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/.claude-plugin/plugin.json
[bbuf-account]: https://github.com/BBuf?tab=repositories
[bbuf-inbox]: https://github.com/BBuf/sglang-review-inbox
[kda-readme]: https://github.com/BBuf/KDA-Pilot/blob/bac966ba09fe22f6220ff527c7c3555e539d5fe6/README.md
[kernelwiki-skill]: https://github.com/BBuf/KernelWiki/blob/76d27b56f804e7e7295d4c570e1e5d7eef4b0a75/SKILL.md
[bbuf-day0]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/model-optimization/sglang-model-day0-support/SKILL.md
[bbuf-history]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/model-pr-optimization-history/SKILL.md
[bbuf-profiler]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/llm-torch-profiler-analysis/SKILL.md
[bbuf-pipeline]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/llm-pipeline-analysis/SKILL.md
[bbuf-layer]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/torch-profiler-layer-track/SKILL.md
[bbuf-benchmark]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/llm-serving-auto-benchmark/SKILL.md
[bbuf-capacity]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/llm-serving-capacity-planner/SKILL.md
[bbuf-compute]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/model-compute-simulation/SKILL.md
[bbuf-incident]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/sglang-prod-incident-triage/SKILL.md
[bbuf-diagram]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/model-architecture-diagram/SKILL.md
[bbuf-video]: https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/316923d44e2645644f03df2d22326dd272105436/skills/sglang-explainer-video/SKILL.md
[claude-review]: https://code.claude.com/docs/en/code-review
[claude-local]: https://code.claude.com/docs/en/code-review-local
[claude-actions]: https://code.claude.com/docs/en/github-actions
[claude-gitlab]: https://code.claude.com/docs/en/gitlab-ci-cd
[claude-ultra]: https://code.claude.com/docs/en/ultrareview
[claude-customize]: https://code.claude.com/docs/en/code-review-customize
[claude-plugin-meta]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/.claude-plugin/plugin.json
[claude-plugin-command]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/commands/code-review.md
[claude-plugin-readme]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/README.md
[claude-plugin-license]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/LICENSE
[claude-toolkit-readme]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/README.md
[claude-toolkit-meta]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/.claude-plugin/plugin.json
[claude-toolkit-command]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/commands/review-pr.md
[claude-toolkit-reviewer]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/agents/code-reviewer.md
[claude-toolkit-license]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/pr-review-toolkit/LICENSE
[claude-action-yml]: https://github.com/anthropics/claude-code-action/blob/9fa68854da5fadef4ed3dce240325a0dfe251880/action.yml
[claude-action-license]: https://github.com/anthropics/claude-code-action/blob/9fa68854da5fadef4ed3dce240325a0dfe251880/LICENSE
[claude-cli-license]: https://github.com/anthropics/claude-code/blob/main/LICENSE.md
[bridge-tree]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/tree/40d446774bb17a5dfe1029afd0fd18004d49dafb
[bridge-review]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/review-pr/SKILL.md
[bridge-license]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/LICENSE
[bridge-parity]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/parity-testing/SKILL.md
[bridge-mlm]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/nemo-mbridge-mlm-bridge-training/SKILL.md
[bridge-nrl]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/nemo-rl-e2e-testing/SKILL.md
[bridge-verl]: https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/40d446774bb17a5dfe1029afd0fd18004d49dafb/skills/verl-e2e-testing/SKILL.md
[slime-review]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/slime-code-review-preferences/SKILL.md
[slime-license]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/LICENSE
[slime-reward]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-reward-function/SKILL.md
[slime-rollout]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-rollout-function/SKILL.md
[slime-filter]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-dynamic-filter/SKILL.md
[slime-eval]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-eval-dataset-config/SKILL.md
[slime-tests]: https://github.com/THUDM/slime/blob/79aa41a884ab0bf65222c94418f6357d3c31192b/.claude/skills/add-tests-and-ci/SKILL.md
[pragent-project]: https://github.com/The-PR-Agent/pr-agent/blob/1b19ab257ec69f658c3047f6ef0bd65551234d59/pyproject.toml
[pragent-cli]: https://github.com/The-PR-Agent/pr-agent/blob/1b19ab257ec69f658c3047f6ef0bd65551234d59/pr_agent/cli.py
[pragent-plain]: https://github.com/The-PR-Agent/pr-agent/blob/1b19ab257ec69f658c3047f6ef0bd65551234d59/pr_agent/git_providers/plain_diff_provider.py
[pragent-reviewer]: https://github.com/The-PR-Agent/pr-agent/blob/1b19ab257ec69f658c3047f6ef0bd65551234d59/pr_agent/commands/pr_reviewer.py
[pragent-license]: https://github.com/The-PR-Agent/pr-agent/blob/1b19ab257ec69f658c3047f6ef0bd65551234d59/LICENSE
[reviewdog-readme]: https://github.com/reviewdog/reviewdog/blob/21e8d008e6818af198ca0a9252f0fd7c71754887/README.md
[reviewdog-license]: https://github.com/reviewdog/reviewdog/blob/21e8d008e6818af198ca0a9252f0fd7c71754887/LICENSE
[gh-diff]: https://github.com/cli/cli/blob/3d5a9e355a837f2f5ee78d7484c118cc1342ad1a/pkg/cmd/pr/diff/diff.go
[gh-review]: https://cli.github.com/manual/gh_pr_review
[gh-license]: https://github.com/cli/cli/blob/3d5a9e355a837f2f5ee78d7484c118cc1342ad1a/LICENSE
[glab-mr]: https://docs.gitlab.com/cli/mr/
[glab-license]: https://gitlab.com/gitlab-org/cli/-/blob/71d2f9135352311e8914c04d6ee9707cf56afc8f/LICENSE
[glab-license-api]: https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/repository/files/LICENSE/raw?ref=71d2f9135352311e8914c04d6ee9707cf56afc8f
[gitlab-flow]: https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/code_review/
[github-review-api]: https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request
[gitlab-discussions]: https://docs.gitlab.com/api/discussions/#create-new-merge-request-thread
[github-pr-files]: https://docs.github.com/en/rest/pulls/pulls#list-pull-requests-files
[gitlab-mr-api]: https://docs.gitlab.com/api/merge_requests/#list-merge-request-diffs
