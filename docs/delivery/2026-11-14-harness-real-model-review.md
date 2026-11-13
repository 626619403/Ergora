# F8-H2 真实模型接入独立评审

日期：2026-11-14。评审者：新 fresh-context Codex agent `harness_real_model_review`。未继承实施对话；先读原要求、固定差异与原件，再核交付叙述。遵循项目 `AGENTS.md`、`maintainable-project-delivery` 及其独立评审说明，参考 AIHERO 的需求／结构双轴口径。只写本报告和私有离线核查资料；未改产品、安装依赖、运行模型／大测试、发网络请求或变更 Git 状态。

## 精确候选与边界

分支 `refactor/architecture-foundations`，基线及评审时 HEAD 均为 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`。未提交十文件由私有 `harness-real-model/review-r1/manifest.json` 固定，manifest SHA256 为 `1d6a9e153cc26fdaed065872ec5b11724b3590fdeda908df871f380ae6df6e6d`；独立重算全部长度／SHA256，快照与当时工作树逐字一致，tracked diff 与 Git 差异相符。

精确文件为：

- `src/ergora/data/components.json`、`src/ergora/data/drivers/deepseek.py`、`docs/AGENT_BACKENDS.md`。
- `docs/PLAN.md`、`docs/plans/2026-11-12-harness-admission.md`。
- 新 `docs/plans/2026-11-14-harness-real-model.md`、`docs/delivery/2026-11-14-harness-real-model.md`。
- C2 的 `docs/plans/2026-11-14-forge-native-admission.md`、`docs/delivery/2026-11-14-forge-native-admission.md`、`docs/delivery/2026-11-14-forge-native-admission-review.md` 仅补普通发布与在途 CI 状态；本次只核这些差异的范围，没有递归复审 C2 源身份实现或原报告结论。

本片只在既有只读 DeepSeek Harness backend 增加显式协议选择，验证真实 text-only／task-MCP。原生 Forge、完整六阶段的 DSH 执行、持久会话 H3、OpenHands、GPU 实验及候选采用不属于本片完成声明。

## 需求轴

通过，开放 finding 0。初审发现一项文档 P3（SP1），作者最小更正后已静态复核关闭；未发现产品阻塞问题。

`components.json:957` 的可选 `api` 仅允许原支持的两个协议，默认保持 `openai-completions`；`deepseek.py:45` 通过同一字段直接选择上游协议，缺省仍保留原行为。`AgentBackend.validate_binding` 的已有 schema 校验覆盖外部配置，原 factory／准入／结果校验路径不变。没有隐式 endpoint 改写、协议回退或新重试；原 provider 的 `maxRetries:0` 保持。固定上游 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` 三文件的实际字节与 manifest 一致，`provider.ts` 的协议表及 `config.ts` 的配置入口均原生支持 Completions／Responses；SDK／runtime 元数据和三轮 native identity 均为 `0.2.2rc2`。

真实调用原件分别核至保存的 run／只读数据库记录、完整输入、driver request、追加结果 schema 后的 native prompt、原生 user message、通知／native events、终值与严格原 schema：

|实际调用|结果|本次独立核准范围|
|---|---|---|
|`14a00aa6ef10411abfc813627d9a08b7`，20.712 秒|`failed`；native exit 0、finish `error`|未配置新字段，实际 patch 为 Completions；原错误为 HTTP400／`byok_endpoint_not_supported`，无最终正文或成功 result；没有工具调用|
|`98f01639cd584e46901ac33ed83070e2`，45.849 秒|`succeeded`；native `completed`，严格 result `approve`|显式 Responses；与原 Codex prepared input 全树及 prompt 完全相同，原 schema、结果摘要和副本逐字一致；没有工具调用|
|`9906124a37754963af7ffdb1f50bcf3b`，45.695 秒|`succeeded`；native `completed`，设计者原结果无 decision|原 `optimization-kernel` 的 `root/analysis/design`；实际请求只暴露 list／read，一次 list、六次 read 全部成功|

前两轮 input digest 均为 `e17b82b80776bc3063f5ea21d4b40db87fbdbbd502e12f7bde5d1f23154eda4f`，prompt SHA256 均为 `9e24abaede8d1c071f2f5f3156fec5ac72f48d4ee365de41a0a424c54b7c6949`。第二轮严格 result SHA256 为 `d07483a78b07d4efb5209a012c6c60fe98b0b09cf5145222ef0cc59272239812`。task 轮 input digest 为 `8b62c05827bd53c522bac7b5b5a759cbf1f6cd14b0e16fc59305231e1c0d0abb`，prompt／严格 result SHA256 分别为 `dac0680a5d1137207d23ff2e4f0fe04025389c75f716f606b47e8992dbdd0d00`／`23f7c1da3d0045a0d5b33be8e0d9805c43d90fc5bdd6b76796e7ce90e81390c8`。

task 六资源 16,774B 的完整集合由叶资源及完整 Skill 子树重新推导，和 scope 相同；每份实际工具正文均连续 UTF8 读至 `next_offset:null`，并逐字节匹配安装包原 bundle、冻结原输入和本轮快照。三层祖先说明／context、叶说明／Skill 及其 evidence-contract 附件保持身份；完整内联材料也在实际 native user message 中。原权限均无 write／shell／network，`formal_execution_authorized` 为 false；父权限与原 grant 保持。六个 PID／starttime 采样身份的历史终态及本次事后 `/proc` 核对均无存活，只证明这六个观察身份。

两次成功的原 assistant source 均指向显式 Responses；usage 保留其原事件来源，不能当作计费或服务方独立核准值。私有配置仅内部比较身份：Codex 与 DSH 配置相同模型名及服务入口，不能据 backend 名不同称异模型成功。没有捕获 HTTP wire bytes，协议证据来自实际 driver patch、原请求元数据及原生 replay source。

SP1（P3，已关闭，文档状态一致性）：初审 `docs/AGENT_BACKENDS.md:140` 仍将“真实模型”列为“尚未验证”并只指向 H1 交付。用户按本片新 Responses 配置阅读该入口时，会得到与已核 H2 两次成功相冲突的当前验收状态。作者只更正这一行：保留 H1 固定包／loopback／停止历史，另指 H2 的两次受限真实调用，并明确正式六阶段、持久会话与其他平台未准入。本评审者独立核准唯一行差异、两个证据链接和未改的两产品文件；更正后手册 SHA256 为 `9e900110017ab2510ffb56f6cf2cf839cdce270f8944e56611ae99182c496a9a`，补核原件为私有 `independent-review-r1/recheck-sp1.json`。未重跑模型或 suite。

## 结构与可维护性轴

通过，开放 finding 0。

新增配置属于既有 component 的公共构造接口，唯一 driver 消费者就是本 backend 的协议 owner；不存在需要抽出的多处生产逻辑。共同工厂、`agent_runs` 的准入／完整输入快照、`agents.invoke` 的严格结果接纳、task-MCP scope 与原进程 owner 均沿原路径使用。没有按协议增加上层 concrete-type 分派、通用插件接口、第二 scheduler／ledger、模板或权限变更，也没有新生产函数、assert、handler、test 或 CI。两个协议的取值受原 schema／上游支持矩阵约束，未将配置锁死为本机实际服务。

已检查相邻 `components`、`bindings`、`agent_backends`、`agents`、`agent_runs`、`workflow_definitions`、`task_mcp` 及资产身份实现。此次字段直通没有改变六阶段、candidate／budget／approval／unknown 恢复合同或进程归属。现有三 suite 与基线测试文件逐字一致；没有要求为单字段直通增加镜像断言或额外 CI。

## 实际核查与限制

独立离线脚本重新核准 noneditable wheel SHA256 `2aa9eda87f4f3629437bf4c718beebe1d7ba1d2ede10172c74289038f9496236`：551 个产品文件在当前源、构建源、wheel 和安装副本中的集合／字节一致；wheel 559 项与安装 RECORD 564 行的哈希／长度、283 冻结文件全部通过。核原安装 suite 的实际命令、退出状态及 stdout 为 38 passed／19.21 秒，没有重跑测试。检查了作者前两次私有审计脚本错误与最终修正，原 stdin／事件字段误判属于核查脚本，不是模型重跑或产品成功证据。

本片自身结构模板是独立于上述兼容测试的新 run `ac0ee870d8b24785b7e52edbc772d130`。五完整文件 64,066B 的 packet 索引已从实际 task 中逐份重算，完整 task／三份继承资源确实在实际 input／stdin；两产品文件与初审候选一致，手册此后只有 SP1 的状态句更正。两份本片记录此后只追加该审查的状态与原身份。原结果为 `approve`，SHA256 `93eec39ed3dfcb2e8aafadf7d0048a83369a6c4114f4680f8e31f8a38a896b04`；其判词明确没有独立访问私有运行证据，不能代替本次审计。Claude 前片 240 秒超时与已授权 Codex 回退的范围保留；没有异模型成功声明。

私有独立核查位于本项目 `harness-real-model/independent-review-r1/`，`result.json` SHA256 为 `da6f8bbe3195751d2d4548ae61283d0fbd922ae5044db429db55a4e41e87c97c`。公开报告不含私有推理配置、凭据值或个人环境路径。

本次未新增模型、停止／取消／超时或跨平台实验；H1 的 loopback／停止回归仅沿用历史范围。上述只读设置与采样清理都不构成 OS 隔离。模型理解／质量、计费、原生会话恢复、完整六阶段切换、OpenHands、GPU／Forge 执行及项目采用保持未验。新候选的普通发布、远端精确身份及自己的 CI 尚未在本次提供的原件中完成，不能借 C2 或 H1 的发布／CI 关闭。

出口：产品与受限真实调用验收证据及独立两轴通过；需求／结构开放 0／0，SP1 已关闭。完整最终候选快照、普通发布与自己的 CI 仍须单独固定和核准。并行新增的 H3a 计划／交付和副本探针不属于上述十文件及 SP1 补核，未混入本片结论。

## 同片最终候选补核

2026-11-14，同一评审者静态补核 `review-r2/manifest.json`，SHA256 为 `f219fd3145c7a4d38422f6be1166bdc5cfedb3b3430d8a78186001fc4b92ad10`。基线／HEAD 仍为上述 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`；manifest 精确保留初审的十个作者文件，当前文件与 r2 快照的长度／SHA256 全部一致，`review-r2-tracked.diff` 与当前按这十路径读取的 Git diff 完全相同。本报告作为第十一文件单独随候选提交；H3a 的三份新文档不在 manifest 或本片结论中。

与 r1 逐份比较，两产品文件原字节保持，分别为 `aaca14e38681a7ee1df7a078ccb75353f7433316f9012abfa812ee152073ae94`（component）和 `3233b9c6e55146f88bc849b0828d5fe1512937872a7cc820a168cdb5f9c99d2b`（driver），再次直接匹配已验 wheel、构建源及安装副本。手册只有已关闭的 SP1 第140行状态句差异；H2 两份记录、F8 表格和 PLAN 只回填本次已完成的独立两轴与本地出口，不扩大真实调用范围，不提前声称本片发布或自己的 CI 通过。原三轮 native-result 哈希、run 状态／输入身份与成功 result 原件仍匹配初审审计；Completions 原失败、H1 历史及会话／六阶段／其他平台等未验范围保留。

C2 三文件及其 PLAN 状态只回填原候选自己的 CI 终态。核原评审 `ci-terminal-audit.json` 的候选为 a0a42ba、run 为43471215671、八 job／30必要步骤／30完整 SHA 日志路径、通过及开放0状态；该审计绑定的报告 SHA256 `fe3160fa983ef3a7ebcea7f33479161d2ce7c5e574139f0d6a170c23b4cfff99` 与本次 r2 中 C2 报告完全一致。这里核的是原评审结案与本片状态记账的对应关系，没有重做 C2 的 HTML／CI 或实现审查，也没有将 C2 通过借给 H2。

作者 `static-r2` 记录的157本地目标、两项凭据值检查、issues 0 与本次 manifest 身份一致。私有 `independent-review-r1/final-candidate-audit.json` 保存本次补核，SHA256 为 `c460636e7bbeaadd8fcf778694f0f776758a28123ef9188522388173eae2844a`。未运行模型、测试、安装或网络请求。

最终候选补核通过，新增发现0，需求／结构开放0／0。普通 commit／push、精确 Git／远端原件及 H2 自己的 CI 尚需后续分别核准。

## 同片普通发布补核

2026-11-14，独立核准提交 `322007f9c50223606d80f3d0fcdc157eac6db428`，唯一父提交为 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`。直接读取原 commit／blob 对象并重算 Git 对象身份；十一条实际变更路径与 `git-ready-r1.json` 完全相同，十作者文件逐字匹配上述 r2 manifest／快照，第十一文件为已审本报告（提交时 SHA256 `7e8298666a444e5b20c3c8623c5e5ef5e080b0cbc6bacf5b18843a7cfbeaa679`）。H3a 三文档没有进入此提交。

本次直接以该提交中的551个产品 Git blob 核已验 wheel 完整集合及字节，再核原构建源／安装副本、wheel 559项、安装 RECORD 564行与283个冻结文件，全部通过。没有以此后 H3a 工作树源码代替 H2 源码身份，没有重新安装或运行模型／测试。

作者普通 push 原回执为退出0／5.473秒，stderr 对应 a0a42ba → 322007f 及目标开发分支；其后 SSH `ls-remote` 原回执退出0／1.337秒，stdout 将完整 `refs/heads/refactor/architecture-foundations` 解析为同一 `322007f9c50223606d80f3d0fcdc157eac6db428`。本评审只核这些保留原件，没有自行发网络请求。

私有 `independent-review-r1/publication-audit.json` 保存十一 Git 对象、发行包和原 push／Ref 身份，SHA256 为 `3331aafba61574c6d47bdf4fe20cfc785875e7722d86dd726b1bbbe5644d163e`。普通发布精确补核通过，新增发现0；H2 自己的 CI 尚待终态原件，不能借 C2 或 H1 的 CI 关闭。会话 H3、完整 C2 与 B3 的未验范围保持。

## 同片自己的 CI 终态补核

2026-11-14，独立核准 H2 自己的 [Portability run 43475349587](https://github.com/626619403/Ergora/actions/runs/43475349587)。第四份官方 run HTML 的状态为 **Success**，实际 commit 链接为完整 `322007f9c50223606d80f3d0fcdc157eac6db428`，分支为 `refactor/architecture-foundations`。该原件213,315B，SHA256为 `145744152df62e8d85fb9c40d7bd14aa94dd92602bc0d1a7c3e6eadee97f75de`。

本评审用独立 HTMLParser 直接解析 run／job 原页面，从 run 内嵌的原生 batch 路径核 `job_groups_batch` 原 JSON 的八个 job ID／名称／run 路径；再以此精确提交中的 `portability.yml` 和六组配置确定必要步骤，没有使用 H3a 当前工作树配置。最终八份 job HTML 均显示 `data-job-status=completed` 和 succeeded header：

|范围|job 数|必要步骤|终态|
|---|---:|---:|---|
|plan|1|1|显式测试组读取成功|
|Linux Python 3.11 六组|6|24|构建安装、reference 身份、应用回归、观测上传全部成功|
|Windows Python 3.12|1|5|上述四步及 PowerShell 5.1 安装升级全部成功|

三十个必要步骤均为 success，具有开始／结束时间及 job-completed 标记；三十条日志路径全部非空、唯一，逐项包含本次完整提交 SHA、正确 job ID 与 step number。Linux 六组应用回归120–286秒；Windows 应用回归 UTC 17:42:59–17:57:50，共891秒，随后 PowerShell 5.1 安装升级17:57:50–17:58:46，共56秒。

最终九份 run／job HTML、原 batch JSON、前三份 run 与前三份 Windows HTML 共十六份 HTTP 原件，URL／最终 URL、200状态、实际长度及 SHA256 全部与收据一致。早期 batch 的 Windows 仍为 in_progress，前三份 run 为 In progress，前三份 Windows 为 in_progress；均原样保留，终态仅据第四份 run／Windows 页面判定。独立逐项提取与作者 `ci-observation-r4.json` 一致，未将历史页面改写为成功。

同时从精确 Git 提交重新读取551个产品文件，完整匹配原 H2 隔离 wheel，283冻结文件身份保持；没有取 H3a 当前工作树作为 H2 源码。本补核未发网络请求，未读取日志正文或下载 artifact archive，未运行模型、安装或测试。私有 `independent-review-r1/ci-terminal-audit.json` 保存逐原件、逐 job／step 和历史状态核查；初版私有核查对历史 header 的文字假设已按原件更正，未涉及产品或模型重跑。

H2 精确提交自己的 CI 终核通过，新增发现0；需求／结构两轴仍通过，开放0／0。结合上述精确源码、受限真实调用、自身模板、独立评审及普通发布核准，F8-H2 的精确交付可关闭。此结论不扩大到 H3 持久会话、完整六阶段 DSH 执行、OpenHands、其他平台的 DSH 准入、完整 C2 或 B3。
