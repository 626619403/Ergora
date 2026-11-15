# PR／MR 审查后端：官方能力与 Ergora 调用边界

读取日期：2026-11-15。Ergora 固定基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`。本文核对用户指定的 [Code Review 文档][C1]与[产品文章][C2]，并直接读取 OpenAI／Anthropic 对应官方页面和固定公开插件源码。公开网页和源码不是本机安装、账户授权或产品运行验收。

## 文章与当前服务文档

[三月九日文章][C2]介绍多 Agent 查找、验证、排序与 PR 发评，当时正文称研究预览，保留当时平均耗时／费用估计；页面已追加 GA 更新。[当前文档][C1]给出 Team／Enterprise、支持的 GitHub hosts、Owner 设置及当前运行行为。因此本文不把旧 preview 叙述、平均耗时或费用估计当作今日合同。当前 [costs][C5] 明确按 token／usage credits 另计费，组织承担费用，review level、代码规模／复杂度及触发频率影响支出，没有固定每次价格。

托管服务目前围绕 GitHub，包含按专门文档配置的 GHES 与数据驻留 host；ZDR、HIPAA 配置和 CMEK 等可用性限制须按组织实际核对。[C1] 通过云厂商使用 Claude Code 不替代 Team／Enterprise 组织资格；API key、个人 CLI 登录或一段 API prompt 都不是托管服务启用证明。

## 各入口实际不同

|入口|安装、认证与可用范围|结果与副作用|
|---|---|---|
|**Codex CLI 原生 `/review`**|先安装本地 CLI；OpenAI 模型的本地访问可用 ChatGPT 登录或 API key，实际工作区策略仍适用。可选择 base branch／未提交变化／具体 commit／自定义规则。[O1][O2][O3]|返回优先级 findings 到 transcript，官方说明不会修改 working tree；PR Style 使用 merge-base，不能代替完整源码、需求和原检查材料。不是云端发评，也不是 Ergora driver 自动选择的模式。|
|**Codex GitHub 云审查**|连接 GitHub 仓库并在 review settings 开启；自动审查设置需要相应 push/admin 权限。Cloud 使用 ChatGPT 登录，API-key 本地访问不等价。[O3][O4]|`@codex review` 或自动触发会发表 GitHub review；当前文档标识 P0/P1。`AGENTS.md` 可承载本仓库规则；不替代必需检查和人工批准。|
|**Codex GitLab MR 云审查 beta**|官方当前标为 beta、所有 ChatGPT plans 可用，但仍需连接账户和配置。GitLab.com 需项目 environment；自管／Dedicated 另有 workspace-admin template、服务账户／写回权限及 project/group webhook 路径。不要把 GitHub 接入直接当 GitLab 已接通。[O5]|发表 MR discussions／notes；当前手动请求默认可含 P0/P1/P2，自动重点 P0/P1。自动 review policy 与触发器独立配置。修复代码属于另一个需要 project environment 的任务，可能 push。|
|**Claude Code 内建会话 `/code-review`**|本地安装并认证 Claude Code；命令对任意 plan 开放，计入会话的计划 usage 或 API billing。`/review` 是别名。可给 branch／PR／path／revision target。[C6][C7][C8]|默认按指令只输出报告；`--fix` 请求编辑，`--comment` 请求 GitHub inline 或 GitLab 单个 note。GitLab posting 要求 Claude Code ≥2.1.257 并使用 `glab`，缺少时输出 terminal。后台 fix 的 checkpoint／rewind 边界另见原文，不把请求修复当作只读操作。|
|**Anthropic 公开 `code-review` 插件**|固定仓库提交 `b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6`，manifest 1.0.1。需单独安装／启用插件并核实际 namespace、`gh` 认证与工具能力；通用 marketplace 安装文档要求查看 scope 与所带组件。[P1][P2][C9]|固定 command 发起并行审查和 finding 复核，默认 terminal，显式 `--comment` 才走 summary／inline 发评；声明了 `gh pr comment` 与 inline-comment MCP。README 的自动可用／confidence 描述与 command 的具体流程不能混为版本保证。它不是托管服务，也未被 Ergora 安装或调用。|
|**Anthropic 托管 Code Review**|Team／Enterprise 组织 Owner 启用，GitHub organization 安装／连接 Claude App，再选有权限的仓库；无须加入 CI workflow。[C1][C3]|Anthropic 托管环境，多 Agent 查找／验证／去重排序；不 build/run 代码、不 push commit，但写 inline／summary／check run、处理自己的旧线程及触发 reaction。服务本身不 approve 或 block，check 不以 failure 结论阻断。[C1][C4]|
|**Claude GitHub Actions／GitLab CI**|自行配置 workflow／runner、触发、权限与凭据。当前 Actions setup 支持 API key、订阅 OAuth、服务账户联邦认证或相应 cloud-provider 路径；GitLab 指南说明 API／provider 凭据。它们与托管服务单独设置。[C10][C11]|在自己的 CI runner 调用 Claude；按 workflow 可发评、编辑或提交，不能整体标作只读。GitHub App 还供其他 Claude 功能使用，其权限比单次托管 review 的实际动作广。|

表中的命令名仅用于区分能力，不是本片执行步骤。没有推测 `codex review` 参数、替用户安装插件、设置密钥或触发外部审查。公开原生 reviewer 或插件也不是领域数值／分布式／收敛验证；不能把产品自己的多 Agent 安排复制成 Ergora 第二套审查调度。

## Ergora 的真实消费者与小实现

基线上的 [CodexBackend／ClaudeCodeBackend][E1] 分别组装普通 `exec` 与 print／JSON Agent 调用，没有引用原生 `/review`、`/code-review`、插件或托管 API。只读／text-only／task-MCP 各按原 mode 限制；Claude task-MCP 的 bare 模式使用 API 环境凭据，不读取已有 OAuth／keychain。驱动的可执行文件／凭据提示不是本片真实调用验收。

真正对应的 PR 审查入口是 [pretraining root][E2]、[posttraining root][E3]及它们复用的 [delivery 三路][E4]；通用 reviewer 分别持有 structure／correctness／test-value Skill。不存在单独名为 quality-reviewer 的 preset。measurement reviewer 的 quality/correctness evidence 属于优化提案流程，本片保持其范围与身份。

新增两个同 ID 的 1.0.1 根；每个根封装同名同摘要的 `ergora-review-backends` 窄 Skill，由四叶继承。两份资源字节为可独立导出完整包的封装副本，详表仅在本研究维护，不进入五个叶。原引用、图、权限、后端、输出与旧定义保持；按 [G1a][E5] 更新原 preset 名称选择的新根、导入旧／新依赖，不增加版本别名。独立旧通用根和其他开发／优化入口没有被静默升级。新旧具体摘要与检查见[交付记录][E6]。

## 来源身份与读取范围

下表是实际读取的内容 SHA256，不是厂商发布版本。OpenAI 旧 `developers.openai.com/codex/...` 路径会重定向到官方 `learn.chatgpt.com`；正文采用已打开的当前 canonical 页面。Anthropic 指定页面同时读取了 Markdown 版。HTML 的动态页字节可能变化，摘要仅固定本次观察。原网页、索引、响应头和失败记录留在本 worktree 忽略的 `.ergora/checks/review-backend-guidance/sources/`，不把完整网页转载进发行包。

|来源|实际正文／固定原件 SHA256|
|---|---|
|[C1 overview][C1] Markdown|`78ff48627f8e08e5551e254a963356b6988160a6b0edc873fc8772e3f301e06a`|
|[C2 article][C2] HTML|`cb70dcff71c9b73fc1baf9af54d67e7a5e68c8937f97b26cad078b1611552376`|
|[C3 setup][C3] Markdown|`7d5dac2e21d5d8815ec79cea854371bd1c6322d195bea602323959c580135336`|
|[C5 costs][C5] Markdown|`55cc84e7bf4337f5a8392b976f0ff32393585a982416df47f3612062d017f464`|
|[C6 local][C6] Markdown|`092b76076a9fad31f02a4054ae6f601d6b864ffc07030e90ef3991e7e30ec6f5`|
|[P1 command][P1] fixed raw|`3f02ea6eed996590348264777b2e324859a6e2c0c5f7dd298617ea21deb3b1b2`|
|[P2 manifest][P2] fixed raw|`0c5d2784bc1ab85b14e578132c141e9e0bb52dbc041f8a9094f8564cd370ffce`|
|[O1 CLI][O1] Markdown|`36066e8647cfa5f6b8ff08678267e256e3434ccfff8eac6532c5ac0ed4daffdd`|
|[O2 review][O2] Markdown|`c18b2fe184104facf5d044631ee151b2394baab1c44218be8b9d60c7dbd33020`|
|[O3 auth][O3] Markdown|`67d3f0c64897ea26b48e62a634ced7dbd2763a47104e12a0923cc528986de588`|
|[O4 GitHub][O4] Markdown|`582bb228cbbb975bea29fbdd8ee27137ed1511e292bca49cf94528a9cd338e8a`|
|[O5 GitLab][O5] Markdown|`d1eec5b468386fca132bad9e9960723cc224799ccd28ce3fafd1a56b3f7ce4d3`|

已读上述原文以及 Claude PR 行为、安装、认证、marketplace、Actions、GitLab CI 的相关段落和插件 command／manifest／README。初始网页搜索工具返回不可调用后改用公开 HTTPS；无认证绕过或平台写入。尚未安装或运行这些能力，没有核用户订阅／组织设置、网络／host 可达性、所有 provider 的登录流程、最新插件 namespace 或实际 review 输出；没有效果评价、性能／训练证明。本文不复核旧研究中其他厂商产品或 toolkit 的实现事实。

[C1]: https://code.claude.com/docs/en/code-review
[C2]: https://claude.com/resources/articles/code-review
[C3]: https://code.claude.com/docs/en/code-review-setup
[C4]: https://code.claude.com/docs/en/code-review-pull-requests
[C5]: https://code.claude.com/docs/en/code-review-costs
[C6]: https://code.claude.com/docs/en/code-review-local
[C7]: https://code.claude.com/docs/en/setup
[C8]: https://code.claude.com/docs/en/authentication
[C9]: https://code.claude.com/docs/en/discover-plugins
[C10]: https://code.claude.com/docs/en/github-actions
[C11]: https://code.claude.com/docs/en/gitlab-ci-cd
[O1]: https://learn.chatgpt.com/docs/codex/cli
[O2]: https://learn.chatgpt.com/docs/code-review
[O3]: https://learn.chatgpt.com/docs/auth
[O4]: https://learn.chatgpt.com/docs/third-party/github
[O5]: https://learn.chatgpt.com/docs/third-party/gitlab
[P1]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/commands/code-review.md
[P2]: https://github.com/anthropics/claude-plugins-official/blob/b5b01ac4f889fec0c4c6bb89f27ca7c8574473f6/plugins/code-review/.claude-plugin/plugin.json
[E1]: ../../src/ergora/agent_backends.py
[E2]: ../../src/ergora/data/presets/workflows/ergora-pretraining-review/workflow.json
[E3]: ../../src/ergora/data/presets/workflows/ergora-posttraining-review/workflow.json
[E4]: ../../src/ergora/data/presets/workflows/ergora-delivery-review/workflow.json
[E5]: ../plans/2026-11-14-memory-preset-patch.md
[E6]: ../delivery/2026-11-15-review-backend-guidance.md
