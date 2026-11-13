# D2-B2h 低精度／量化方向独立审查

日期：2026-11-13。评审者：fresh-context 独立 reviewer `low_precision_directions_review`。先读原需求、AGENTS、独立审查规则和实际 tracked／untracked 改动，再读作者计划、交付和验证叙述；没有继承实现会话，也没有另派评审者。

**需求符合性通过，可维护性通过；开放 finding 0／0。** 唯一 SP1/P3 文档状态问题已在同片修正并复核关闭。结论针对本片只读资料模板的本地出口；普通发布、精确远端身份及本候选自己的 CI 仍开放。

## 受审身份与范围

基线及评审时 HEAD 为 `8f0b5802274f5db80b804d99979d074cdd3e1338`，分支为 `refactor/architecture-foundations`。当前实现是该基线上的未提交候选。核过三个完整快照的文件长度、SHA-256、原件及工作区内容：

|快照|文件数|manifest SHA-256|用途|
|---|---:|---|---|
|review-r1|15|`1ba1d8f490fbb90d14d2ff8d45d7be3212548159f9bcfc801d1fdae766949c94`|初始实际变更，包含全部未跟踪文件|
|review-r2|16|`0b81e846a735cf1890268fdf3f0dd0fcebc837759bb925da65c155199cb9d2eb`|补齐实际验收与公开投影|
|review-r3|16|`1649f21203704d58617ea681c64f1a5b772f44161676a48de54ca40b136dc68b`|本报告最终受审候选；仅两份 Markdown 修正 SP1|

五份产品／测试文件为 [catalog](../../src/ergora/data/presets/presets.json)、[既有 preset 测试](../../tests/test_presets.py)，以及新根的 [workflow](../../src/ergora/data/presets/workflows/ergora-opt-low-precision-proposal/workflow.json)、[instructions](../../src/ergora/data/presets/workflows/ergora-opt-low-precision-proposal/instructions.md)、[context](../../src/ergora/data/presets/workflows/ergora-opt-low-precision-proposal/context/low-precision.md)。它们从 r1 到 r3 均未改变。另读 README、PLAN、TRAINING、TEMPLATE_WALKTHROUGHS、专家总计划、本片计划／交付、公开 JSON，以及三份 cluster 计划／交付／原审查中的发布记账差异，共 16 文件。本报告是随后新增的评审记录，不属于这三个输入快照。

逐个比较基线全部 545 个产品文件：仅 catalog 改变，21 个旧 catalog 条目相同；新包共 548 产品文件。新根内容树 digest 为 `b8fce6c6115a6106940db830824d4c6c2da586dc95f61996bd79b8c049283530`。没有 runtime、后端、依赖、旧定义或冻结参考文件的行为修改。cluster 模型、安装与 CI 没有被用作本片验收证据；三份 cluster Markdown 仅核本候选内部状态是否一致，未重新授予其执行或 CI 结论。

## 需求符合性

新根沿原 `ergora-training-proposal@2.0.0` 四叶形状，nodes／permissions／limits 与原定义相同；analysis／measurement 精确引用既有 v2，kernel 直接引用既有 v2 Agent，catalog 导入四位原专家及所需 workflow。已重算七个 bundle 的内容树、声明资源和引用 digest，无不符。

结构父链的完整资料、兄弟资源不继承和依赖产物不授予权限的规则保持。根、子 workflow、叶及 grant 都是 read workspace／definitions、无 write／shell／network；实际 task-MCP 只提供所选结构链的固定 list／read。新 instructions 和两手册明确：run-input 只运行选中叶，kernel 手动接收两份完整分析，measurement 手动接收三个完整原结果；静态边和 join 不执行量化或整图。没有由资料包扩大任意职责 Agent、后端替换或嵌套执行的既有授权范围。

以 R2 固定正文逐项核对新 context；18 份共 470,878B 的原件均逐字等于原研究文件，其固定 URL、HTTP200 回执、长度和 SHA-256 一致，没有重新联网或借用 latest。检查的来源和实际进入模型的综合资料如下：

|固定来源原件|核对的支持／限制|实际输入中的位置|
|---|---|---|
|ModelOpt 0.48.0 `modelopt_tag_quant.raw`|实验性 auto_quantize、梯度评分 backward、KL／Aumann-Shapley、批次数、显式 disabled_layers、融合组、搜索 state 与部署限制|context 第 4 项；原 API 的 auto_quantize 文档及实现|
|同版 `modelopt_ptq_readme.raw`；独立固定 Skill 的 `modelopt_skill_ptq.raw`、`modelopt_checkpoint_gate.raw`|逐模型／格式／导出／runtime 支持；完整覆盖及元数据；source precision 与尺寸例外；scale 名称不是通用正确性判定|context 第 2、3、5 项，未把原 Skill 的扫描脚本变成通用 validator|
|Skill SHA `9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77` 的 `modelopt_skill_search.raw`、`modelopt_search_ref.raw`、`modelopt_skill_evaluation.raw`|有限 portfolio、手工对照与融合约束；1 个百分点是来源策略；评价流程及其外部依赖不等于本项目已接入|context 第 1、3、9、10 项；任务自身门槛保持优先|
|`modelopt_qat_tag.raw`、`modelopt_bridge_readme.raw`、`modelopt_skill_qad.raw`；Bridge v0.7.0 `bridge_tag_quant.raw`、`bridge_tag_mixed.raw`|QAT 模拟量化／固定 scale，QAD 冻结 BF16 teacher／logit KL 及额外成本；量化状态、原训练 owner；Bridge 例程与模型／版本限制；TE 训练与 PTQ 导出分开|context 第 2、6、7、10 项，不推导任意模型或 packed 低位训练已验证|
|TE v2.21.0 `te_quant_availability.raw`、`te_tag_recipe.raw`|FP8 的 SM8.9／Ada 软件条件、NVFP4 的 SM10.0、MXFP8 对 SM12.0+ 的 all-GEMM-layout 拒绝、block scaling 的 SM9.0／CUDA12.9；amax／RNG／高精度状态和恢复|context 第 7 项；以固定 helper／recipe 为准，不以 Blackwell 名称或 import 替代实际支持|
|AutoRound v0.16.1 `autoround_scheme.raw`、`autoround_auto_scheme_code.raw`|混合类型 tuning 不等于真实模型可导出；layer_config／shared groups／工作量与 scale／zero-point 成本；没有授予持久搜索恢复保证|context 第 8 项|
|Olive v0.13.0 `olive_search.raw`、`olive_engine.raw`|停止仅在受支持模式的步骤边界检查；非外部硬超时；无候选满足 goals 时存在忽略 goals 的排序回退|context 第 8、10 项；返回 best 不授予质量或采用通过|

实际模型读取的是项目原创 context 和原专家资源，来源 URL 没有作为联网抓取资源。上述是固定版本语义审查；没有检查当前安装的 ModelOpt／TE／Bridge 等真实组合，也没有重新验证研究论文的实现可用性。context 对 HAQ／HAQA／APQF／AutoQS 仅保留方法来源，不据此声称存在可执行通用 runtime。

支持、覆盖、融合、导出／加载、开发质量、冻结独立质量、性能和采用均分层；有效位宽、尺寸、perplexity、短 loss、exit0 和搜索返回值没有跨层放行。候选／数据／配置／checkpoint 身份、总预算、操作硬期限、丢失回执先对账及原库／runner／评价／采用所有者均明确，满足本片范围。

## 可维护性

读取了现有 [install_preset／编译与继承 owner、单叶输入合同](../../src/ergora/workflow_definitions.py)、CLI、HTTP preset 调用者、manifest 完整树核验、[单叶准入](../../src/ergora/agent_runs.py)、[task-MCP 固定资源 owner](../../src/ergora/task_mcp.py)及原训练 evidence／采用 gate。新顶层配置沿 catalog → 原定义库 → 原编译／manifest → 原调用链进入，未添加第二个执行器、状态账本、工具分派或采用出口。

新三文件分别承担稳定定义、调用规则和方向资料，配置接口有明确用户入口；共享专家的行为没有复制进新 Agent 类。测试只扩展原方向参数与第四叶预期，仍从导入、冻结 manifest 和离线 prepare-input 的公开接口核完整 context、精确 v2 及只读权限；没有新 helper、重复 guard、异常分支、机器／模型专用运行代码或额外测试框架。四候选、八 assignment、三次重复等数字只存在实际模型的建议结果中，已在交付中标为待原预算接受，未成为产品默认或通用门槛。

## 原件与验证检查

评审只读检查本片私有验收原件，未执行作者的安装／模型／写报告脚本。用独立只读检查重算了包、树和字节身份；没有安装、发起模型、运行新 suite、提交、推送或读取 inference 配置及凭据值。

- **安装身份：** wheel SHA-256 `1b9b01d2a5d1692a3a8681293d36907ae10911c4c299ced6a6961653ba192111`；556 wheel 文件、548 产品的当前／构建源／wheel／site-packages 内容与文件集相同。两份 RECORD 的逐项散列和长度、561 行安装记录、283 冻结文件及 noneditable 身份均核准。
- **原测试：** 已读完整原 preset-suite stdout／stderr、result、命令及隔离 source 身份，29 项通过，pytest 115.59 秒，监督 117.080 秒，原 600 秒上限。包含 low-precision 参数；没有据此声称本地全 suite 或七组 collection 通过。
- **自身结构审查：** 原 run `8d08b7677da2457dbebb10b8cda93a29`，30.278 秒、text-only `approve`。五完整文件 48,318B 与当前五文件相同，三继承资源在实际 prompt／stdin 中；原 State、input 内容树、request／task／prompt、stdin／protocol／native final／result 均核到。protocol 与归档 result 的 JSON 内容相同；该判词明确只覆盖文本，不作为来源、安装或本独立审查的替代。

四个实际 task-MCP 调用从原 SQLite run、准备目录和冻结 input 的完整内容树、request／task／prompt、stdin／protocol、scope 内容、native receipt／完整 stream 至最终 result 逐项核验。每次仅一次成功调用，原内层 240 秒／外层 290 秒上限保持；两个 handoff 的前驱 JSON 在实际任务中逐字完整存在，散列与各原 result 一致。每个 scope 均有完整 list，所有资源均连续 UTF-8 读至 `next_offset:null`，没有失败 MCP 或 base64 重试。

|叶／原 run|秒|资源／字节|实际完整前驱|结果|
|---|---:|---:|---|---|
|design `ca5d72bf90c84d26b317c2f1bfb1ec9a`|91.885|6／15,944|无|有限 proposal|
|profile `1812897873624dcab984fc4c5b246e09`|94.037|6／15,837|无|缺真实关键路径的 diagnosis|
|kernel `3c8ec3c31b8747cc8b0bea4162b79cff`|91.032|5／15,593|design、profile|条件设计与 wrapper 检查|
|measurement `ba92181a8a2b4a2fb212ea818e643a0c`|60.893|6／15,858|design、profile、kernel|`request-changes`|

总计 23 资源、63,232B。完整传输不自动证明理解；已另行阅读四份完整原结果：它们保留 69.8% 的任务下限及 0.6 个百分点下降、5% 假定体积增长、SM90 与 TE NVFP4 冲突、融合／排除／state、AutoRound／Olive 和 QAD teacher 成本等问题；vision scale 名称只列为疑点，未假定实际覆盖已被证明。kernel 采用符号 shape，区分量化算术 oracle、BF16 误差与完整任务质量；没有把 source 文本写成编译或性能成功。measurement 没有替代独立评价和原采用 owner。四叶真实调用均为显式 Codex 绑定，measurement 从定义的 Claude 选择回退，回退原因保留；没有异后端成功声明。

公开[证据投影](evidence/2026-11-13-optimization-low-precision-directions.json) SHA-256 为 `30c9ae8ae0f46fd3eaf41ef66466f84a7d38669c76f3e7683385e53bb3e147ff`，其来源、fixture、wheel／测试、四调用与前驱、审计散列及自身审查字段均与原件相同。调用后 process receipt 只有一次限定 `/proc` 观察、匹配 0；文档没有据此声称全程后代清理或 OS 隔离。

16 文件的本地链接检查覆盖 276 个目标／65 个 Markdown 锚点，无缺失；r3 两份文档修正没有新增目标。`git diff --check` 通过。没有用 cluster 的模型或 CI 关闭本片，也没有把本片模型读完资料称为实际量化、导出、训练或 GPU 验证。

## Finding 与同片复核

**SP1／P3，需求记录状态，已关闭。** r2 [专家清单第 256 行](../plans/2026-11-13-specialist-presets.md)的当前 cluster 行仍称“发布／自己的 CI 待做”，而同候选 PLAN、cluster 计划／交付及原评审补核已记录 `8f0b580` 普通推送及精确 Ref 完成。恢复者沿当前清单会误判还需发布。最小修正是仅更新该行，保留自己的 CI 仍开放。

r3 仅改该行及本片交付的 finding 记录；逐字复核两份 Markdown 与 r2 差异，已改为普通推送／精确 Git 和作者 SSH Ref 补核完成、CI 在途。五产品／测试、安装包、fixture、模型原件与公开投影均未改变，因此无需重跑安装或模型。SP1 关闭；没有把本次记录核对升级为对 cluster CI 的独立通过结论。其余受审范围未发现需求或可维护性问题，开放 0／0。

## 仍开放的出口

本片本地只读资料模板可以关闭；H5 的普通提交／推送、精确远端身份、该候选自己的完整 CI 及对应独立终核继续开放。该出口不能由基线 cluster 的 CI 代替。

真实 ModelOpt／AutoRound／Olive／TE 安装与支持组合、模型／数据、搜索恢复、量化／导出／加载、QAT／QAD／TE 训练、梯度及 all-rank 恢复、目标硬件正确性／质量／成本／收益均未验；B3 真实实验、C2 内部模型完整嵌套与 B2i 独立 kernel 根仍按原计划分别验收。本报告不授予这些通过状态。
