# AC4.2a 独立评审：版本化审查职责

日期：2026-11-09。审查者：fresh-context reviewer `/root/review_requirements_review`。项目与文档均归 Ergora；依据项目 `AGENTS.md`、[原始范围与验收](2026-11-09-review-requirements.md)、[组合要求与 AC4.2](../plans/2026-11-08-agent-composition.md)，应用 `maintainable-project-delivery` 与 `codebase-design` 的结构、复用、必要控制流、测试/CI 与性能标准。未修改生产、安装依赖、提交、推送或启动模型。

**Spec：本地通过。Standards：本地通过。在下述范围内没有成立的 correctness 或 maintainability finding，无开放阻塞项。** 建议审查的可信业务运行仍属于 AC4.2b；本结论不代表整个 AC4 或本提交 CI 已完成。

## 固定范围与方法

实际分支为 `refactor/architecture-foundations`，HEAD 与基线均为 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`。自行取得 `git diff`、完整 untracked 清单及新文件正文，未以作者报告或测试数量代替源码审查。最终冻结了报告自身以外的 **22 文件**：六个生产模块、独立 v2 schema、两个原测试文件、一个新示例、八份 Markdown 和四份公开证据 JSON。上一片 AC4.1 两份交付/审查文档及计划中的终结追加属于历史记账；本片未据其 CI 推导当前候选通过。

逐份检查六模块、两版 schema、新示例与测试变更，并追到 `DefinitionLibrary`、完整 manifest/input 重建、备份、`CompositionInput`、原生创建/提交、Executor 和 Temporal workflow 的实际消费者。22 文件 SHA 清单保存在本地 `.ergora/checks/ac4-requirements/independent/scope.json`，该清单 SHA 为 `100aed19459200bcf54d0f0d5edcdb14694b8ab67f4f187f44258b675225c926`。生产、测试与示例身份同时与[自身审查的 16 文件身份](evidence/2026-11-09-ac4-requirements-self-review-identity.json)逐份相等。

## Spec 核查

|位置|实际核查与结论|
|---|---|
|`definition_bundles.py:52`、`:54`；`agent_definitions.py:10`|先按完整树 inventory 的 SHA 读取 JSON，再选择严格整数版本；Agent 仅 v1，Workflow 接 v1/v2。没有把 bool/float 当整数，也没有未知版本 fallback。历史库仍经不含当前后端准入的 inspector 读取，版本选择未破坏历史/当前准入分离。|
|`workflow-definition-v2.json:341`、`:350`|字段只在 Agent 分支中声明；reviewer 必填且仅接受 required/advisory，其他角色不得携带。Workflow 引用与 join 的封闭字段集合拒绝它。与 v1 的结构差异仅是标题/版本及此条件字段，v1 与 Agent v1 文件均逐字节保持。|
|`workflow_definitions.py:232`、`:279`、`:292`|职责来自节点实例，同一 Agent 可分别 required/advisory。每次进入子 Workflow 都提升预览版本，v1 根引用 v2 子图和重复引用均不遗漏；v1 叶子不被插入默认字段。原引用、祖先材料、权限与预算解析仍由同一次有界遍历拥有。|
|`workflow_definitions.py:358`、`:455`；`backups.py:77`|完整包重新编译全部精确引用并核 composition/request/资产清单；字段和预览版本进入原内容身份。manifest、叶子输入、导出及备份继续使用既有所有者，catalog 收紧和原库移除不妨碍历史完整性核验。|
|`tasks.py:56`|正式预览/创建沿 `_definition → _composition`，在进入原生创建与发布前拒绝预览 v2。库中的静态 v2 定义并未获得正式运行权限。|
|`task_envelopes.py:129`；`reference_inputs.py:116`；`reference_task_submission.py:35`|原生提交经 `require_submission → review_members` 单独拒绝携带的 v2 图，拒绝早于提交意图与 attempt-before-send。Executor 的 `:66` 同样消费此形状检查；多审查 workflow 的 `:71` 复用它。历史 unwrap/summary 仍能读取封装并显示 runtime_supported=false。|

独立静态探针自行构造 **13 实例 / 7 叶**混合树：v1 根两次引用同一 v2 子图，v2 内再引用 v1 子图，另保留 v1 兄弟。必需/建议实例与历史隐式必需叶子没有串扰，完整 root→parent→leaf 正文进入 prompt。完成 manifest 与 advisory 叶子输入的冻结/读回后，移除当前 reviewer catalog，验证历史 Agent/Workflow、manifest/input 与离线备份仍可核，而新的 preview 准入拒绝；删除原库后读取包，再同路径恢复，全部身份保持。

另直接装载 Git 基线中的原 `contracts`、`definition_bundles`、`agent_definitions` 与 `workflow_definitions` 模块，在同一 v1 库上比较完整规范化预览字节，结果完全相等，预览 SHA `595203b7dec021293cdab2c7690954553d0c1dc0d20627fbc3a23345760f69ed`。独立检查 **20 种非法版本**及 **17 种角色/字段组合**，均与验收条件一致。

还绕过应用准入，使用原生底层创建器保存一个完整、可读且重新封装的 v2 manifest，随后调用真实公开 `tasks.start`。原生版本 guard 明确拒绝，未生成 task-submissions、requests、receipts 或远端客户端记录；现存原件字节不变，只有允许的锁文件。此反例补足模型报告未覆盖的端到端原生拒绝证据。

## Standards 核查

共享 schema 选择留在已有完整树校验 Module，实际生产调用者来自 Agent 与 Workflow 两份文件；预览投影留在原编译 Module。没有新增函数、注册框架、第二定义库、调度器或账本。独立 v2 schema 是版本化 Interface，其自包含正文使旧格式保持可核，并非为凑复用而引入的单调用包装。

新增条件都有真实消费者：严格版本检查保护外部定义输入；角色条件定义合法声明；递归预览版本防止旧运行误读新合同；应用 guard 与标准库原生 guard 分别保护应用创建和携带封装入口。二者不能互相替代，独立原生反例证明后者可达。未发现可由现有下游错误等价取代的新增冗余 guard。

新增回归分别保护格式条件、嵌套实例/历史身份/包恢复和正式拒绝，复用原 fixture 与套件；没有新增 CI 作业或镜像检查框架。版本跟踪在原遍历中对每个 Workflow 增加一次常量操作，未增加图遍历、资产读取或重算路径；原缓存和容量上限保持。148.54 秒包检查与 6.48 秒独立定向检查是各自环境的观察值，不能与首轮源码 66.53 秒直接相减宣称性能回退。

## 实际证据

独立执行环境为 Python **3.11.15**，使用源码及已有开发环境；评审脚本与保留证据均在本地 `.ergora/checks/ac4-requirements/independent/`。

- `static_probe.py` 全部断言通过，覆盖混合版本、祖先正文、原基线、版本/角色矩阵和 catalog 收紧/备份恢复；`static-results.json` SHA 为 `4791f79d47bd156c6eccfb9fdbff72f4a3025fd9da260d2d462ccba846c4ec70`。
- 自写 `test_native_gate.py` 加三项新增回归的参数化实例，**10 passed / 6.48 秒**；真实原生拒绝未访问 Temporal 或模型。日志 SHA 为 `902f92f70161b020ceea5fda40f9c52f88f6def2b25505ed5d8b598adc1829ce`。
- `audit_artifacts.py` 自行重读 wheel/安装/源码全部字节，**370 文件同 SHA，283 冻结文件与 Git 基线和原 manifest 相同**；wheel SHA `f6c6dc4733185a485847138c96176064e9b82f61d3486bfadcf1b942698fd801`。复核[原最终包日志](evidence/2026-11-09-ac4-requirements-package.json)的 **191 passed / 1 skipped / 148.54 秒**及日志 SHA，不把该复核写成独立重跑 191 项；跳过项需要真实 Windows junction。
- 重读并核对[11 项实际 CLI 原观察](evidence/2026-11-09-ac4-requirements-cli.json)的原 stdout SHA、manifest/input 全树身份和 execution_authorized=false；旧安装 v1 比较与旧读取器拒绝 v2 的原观察保持。公开手册准确限定静态声明、独立 run-input 与正式运行的区别。
- 自身实际 run `c76a609598184cb0a58b34156490208e` 的原日志显示 **1 次 list、10 次 read**：925 字节 Skill 一次完整读取；249,350 字节 candidate 从 offset 0 开始，经 30,000 字节连续页，最后 offset 240,000 至 next_offset=null，共 **9 页**。逐页重组与 scope、原附件相等，SHA `6fc61ab5bcab0451541a1269bd714727632369d65db8a086515bd6e2750185cf`；16 份完整源码和原 tracked diff 与当前文件完全相等。

模型 run 的 scope SHA `cb77558c68bd3440c981e0ba79f21fb70ea50efea62f8b2b494a9b810832c5f2` 与每条 native MCP 审计相符。原输入包 digest `0c432a9b64ece444141a1348b26b8e27c4cd42a854ab3e99aa0a15b51e3b1be6`、实际 stdin/prompt SHA `51f3e4b0c18f26a5da4d93bddec60636f3479a3dd3def16b63464aa2e4dfad74`、[原结果](evidence/2026-11-09-ac4-requirements-self-review-result.json) SHA `22787c9375abb4b69d5ac3ca96e01463e64c66acec73b1704b78cf89052a40cf`均对应；公开结果与原 result.json 也逐字节相等。原库确已删除，完整固定包仍可核。Codex 模型结果为 approve，formal_execution_authorized=false。其未跑测试、未独立核完整 native 调用者/包装配置/冻结文件/CI 的原限制继续保留，不改写模型报告。

## 未验范围与交付状态

未启动新 Temporal 旅程、建议业务聚合或实际模型；上述模型调用是对作者已有原件的只读核验。未验证 Windows 原生 junction 或本片双 OS CI，未检查精确提交对象与即时远端分支身份。本片尚无独立提交；这些属于提交后的交付门禁。AC4.2b 的可信建议意见、失败/清理阻塞、全部收据汇合及至少一个必需审查者仍须另片实现验证，不能从当前静态支持推导已完成。

## 普通提交身份与在途 CI

提交后独立复核普通提交 **`5580c8ca154af3b58bd546315f0ec4812bd5c4b3`**，唯一父提交为原基线 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`。直接从 Git 对象读取全部 **23 文件**，路径集合与每份字节 SHA 均等于提交前 `r1/review-scope.json`；scope 原件 SHA 为 `3fa2cf3992fa1ab1b0280260c86edaace4930d7f2b7abe1e9e0dafd179e701ef`。增加的第 23 份是本报告；其余收口只涉及状态与导航。进一步从该提交核全部 **370 包文件**等于已验 wheel 的身份表、模型输入 **16 份源码**身份相等，**283 冻结文件无 diff**。本次核验始终使用固定 Git 对象，没有把后片 AC4.2b 的工作区改动计入。

独立读取官方 actions 列表并按完整提交找到其自己的 [Portability 42566831850](https://github.com/626619403/Ergora/actions/runs/42566831850)，run 页绑定上述完整提交与 `.github/workflows/portability.yml`。使用原页面给出的 `jobGroupsFetchUrl`，显式追加 `&batch=0&size=200`，核返回 **totalCount=2 / hasMore=false**，包含 Ubuntu job `128995038645` 与 Windows job `128995038428`。首轮两作业仍为 in_progress，已成功的早期步骤不代表作业完成；这只是中间观察，尚不登记七必要步骤或即时远端终结通过。原官方页面和读取器初次对 job 页 commit anchor/完成属性的假设错误保留在本地证据中；页面实际按各原 log URL 绑定完整 SHA，读取器已按该表示校正，不将读取器错误记为 CI 失败。

## 精确 CI 与即时 HTTPS 远端终结

**2026-11-09 05:37:07.784161 UTC**，独立再次读取原 run `42566831850` 的官方 actions/run 页、完整 job groups 及两份 job 页，整体状态为 **Success**。对照该提交自己的 workflow，核以下 **七个必要步骤全部 success**，每条原 log URL 均包含完整提交 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3` 和对应 job ID，`data-job-completed` 属性均存在；没有 failure、cancelled 或 timed_out 步骤。完整分页仍为 **totalCount=2 / hasMore=false**，未以默认首批代替双作业。

|原作业|必要步骤|最终结论|
|---|---|---|
|[Ubuntu / Python 3.11，128995038645](https://github.com/626619403/Ergora/actions/runs/42566831850/job/128995038645)|Build and install wheel；Packaged reference identity；Native application regression|3 项全部 success|
|[Windows / Python 3.12，128995038428](https://github.com/626619403/Ergora/actions/runs/42566831850/job/128995038428)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|4 项全部 success|

最终 run 页为 **157,485 字节**，SHA `c20836bebe4d6ddeabe7c621ac5632386480d8bdcdd1342c13ecdc0e95d475a5`；完整 job groups 为 **700 字节**，SHA `89dfbcddce85968d2486b59fb4489525f0ce5399aa7f092d7ad821403e46dae3`。Ubuntu 原 job 页为 162,028 字节，SHA `644db1352eafc57dae49cf392c7d7b8c8ea2155a9013b45bc1a0ed011574ff3c`；Windows 原 job 页为 160,120 字节，SHA `c6f05a9b796248e9f37bc930903a0533c90988da4aca97de75e3c325493af89a`。中间 in_progress 原件保持，未重跑、替换或取消 CI；Windows 此处证明本提交的原生应用回归与安装升级 CI，不扩为建议业务或真实嵌套协议旅程。

七项核完后，同一独立脚本于 **05:37:07.788039 UTC** 立即执行 `git ls-remote --exit-code https://github.com/626619403/Ergora.git refs/heads/refactor/architecture-foundations`：距七项检查记录约 **0.004 秒**，工作目录在仓库外，禁用全局/系统 Git 配置并移除继承的 Git 配置变量，保持明确 HTTPS 传输。**2026-11-09 05:37:09.274699 UTC** 命令 exit 0、stderr 空，远端分支返回完整 SHA **`5580c8ca154af3b58bd546315f0ec4812bd5c4b3`**，与已逐份核对的 23 文件提交相同。

**AC4.2a 最终结论：本地 Spec、Standards、本提交自己的必要双 OS CI 与即时精确远端身份均通过，无开放 finding。** 本次仅追加原切片交付记账，未改写 23 份原提交对象或模型输入；后片 AC4.2b 的工作区与未来 CI 不在该结论内。可信建议运行与其失败/恢复合同继续按原计划另片验证。
