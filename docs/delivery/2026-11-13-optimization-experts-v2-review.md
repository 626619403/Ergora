# D2-B1 跨域优化专家 v2：独立 Spec / Standards 评审

评审日期：2026-11-13。评审者：fresh-context 独立 Agent `/root/optimization_experts_v2_review`，随后在同片补核原件。未继承实施对话，未启动子 Agent；只读候选、源码、原件与既有研究，仅写本报告。依据项目 `AGENTS.md`、maintainable-project-delivery 的 independent-review brief，以及已读 AI Hero 1.3.2 本地索引所指的 code-review / codebase-design，分别判断需求符合度和可维护性。

最终本地判词：**Spec 通过 / Standards 通过，开放 finding 0 / 0，SP1 已关闭**。此判词覆盖下述 R3 完整变更、修正 R2 安装和实际只读调用原件；提交、远端及本候选自己的必要 CI 仍未由本评审核准。

## 固定范围

- 基线与本轮开始时 HEAD：`00922d302daa371ab980093889a8468694c10a94`。
- R1 候选清单：`.ergora/checks/optimization-experts-v2/review-r1/manifest.json`，SHA256 `58d7b6fdfc645f86026c6750fdc920c79023e90d5646314f20239c491103c399`。逐件核过 30 份快照的字节数与 SHA256，首次核验与活动工作树无漂移。
- 修正 R2 清单：`.ergora/checks/optimization-experts-v2/review-r2/manifest.json`，SHA256 `dcefbdb9d7fc85913446930e134c7a87f47c23bdd30ce2dee1085140a95934c8`。再次逐件核过 30 份快照，身份及当次工作树一致；相对 R1 仅下述三个产品文件和交付记录的 finding 说明改变。该轮静态判词授予 R2，不把 R1 原结果改写为修正后全范围通过。
- 最终 R3 清单：`.ergora/checks/optimization-experts-v2/review-r3/manifest.json`，SHA256 `79f39f71ca0147233a3f1d186ccaf815250c84a45b3219c5781bb232306b0b84`。31 件字节数与 SHA256 全部通过；相对 R2 产品 / 测试未再变化，仅更新计划、交付记录并新增公开证据 JSON。已完整核对这批最终变化，旧静态结论仍绑定修正后的产品内容。
- 全文检查四个 `agents/ergora-{experiment-designer,performance-analyst,kernel-designer,measurement-reviewer}-v2/` 包各四文件、三个 `workflows/ergora-{training-analysis,measurement-review,training-proposal}-v2/` 包各两文件、catalog 与完整 `tests/test_presets.py`；核过其余六份文档的变化内容、B1 完成条件与活动检查点。精确文件集合以该清单为准，未把后续 B2 方向包或 A2 运行纳入此候选。
- 邻接消费者：`workflow_definitions.py` 的 catalog 安装、精确引用、结构资源合并、权限收窄、完整 manifest / 单叶输入；`agent_definitions.py`、`definition_bundles.py`、`asset_trees.py` 的声明与完整资源树身份；`agent_runs.py` 的只读准入、实际 binding / 原因与输入证据；`task_mcp.py` 的所选结构链 scope 和读取覆盖；现有 backend / role 合同，以及 CLI、HTTP、页面的 preset 入口和精确版本选择。核对原训练手册与冻结 `training.py` 的实验 manifest、runner、evidence SHA 与 owner 批准归属。
- R1/R2/R7/X2/X3 等既有研究仅用于核对来源身份、许可和技术条件，不当作本候选的安装、工具调用或 GPU 测量证据。

## Spec

当前 R3 判词：**通过，开放 finding 0；SP1 已复核关闭**。R1 需修正一处 P2，记录如下。显式新配方固定四个实际 v2 叶，三份 Workflow v2 的数量由旧 measurement 对 reviewer v1 的精确引用所必需；没有默认切换、自动提案图运行或额外执行能力。修正产品的隔离安装、四种实际只读叶交付和自身原结构模板原件已补核，范围与限制见后文。

### SP1 — analysis 指令要求读取不可提供的兄弟 Skill（P2）

位置：`src/ergora/data/presets/workflows/ergora-training-analysis-v2/instructions.md:1` 的 “Read all ancestors and both experts' complete Skill/context resources”。该共享指令进入 design、profile 的每份单叶输入，但另一位专家是兄弟，不是结构祖先。

可达证据：R1 持久用例 `source-r1/cases/test_training_v2_keeps_v1_and_0/root-analysis-{design,profile}/` 的 `prompt.txt` 都含该要求；各 `composition.json` 中所选叶的 Skill 分别只有 `ergora-experiment-designer`、`ergora-performance-analyst`，来源集合分别为 root / analysis / 自身。原 `workflow_definitions._materials` 只合并结构链；`task_mcp.freeze` 也只投影所选叶 resources，完整输入包包含兄弟资产不代表 task-MCP 将其开放。手册原合同同样明确不开放兄弟模板或整个资产库。

影响：按推荐 task-MCP 模式调用任一分析叶时，无法满足这项读取前提，可能产生虚假的缺资料阻塞，或错误声称已经完整读取兄弟 Skill。问题在新增提示合同，不在原 scope 实现。

最小修正与复核：R2 将 analysis 指令改为 “Each selected expert reads its own complete Skill/context resources and all structural ancestor materials”，同步 analysis 资源 SHA 和 proposal 的精确 analysis 引用；未扩大 scope、权限或运行接口。已核 R1 → R2 全部变化，R2 原持久用例四份单叶输入均固定根 digest `f82061705d1b7a0f8bc6b480327aa0602b8b3519c35aa2a985e1deeadfbb33fa`。design / profile 的 prompt 已用修正文案，仍各只有自身 Skill 与祖先；其余叶未加入兄弟资料要求。受影响新 v2 准备测试实际通过，SP1 关闭。

## Standards

当前 R3 判词：**通过，开放 finding 0**，覆盖上述静态检查及下述原件补核。R1 的提示与实际 Interface 不一致已随 SP1 修正；没有新增独立可维护性 finding。模型 approve 只是本片一项原始证据，不代替本报告的独立完整评审。

新内容放在原不可覆盖的定义包与 catalog，由原 CLI / HTTP 两个生产入口消费；页面也沿同一安装路径和 id / version 选择。无需新 Python Module、抽象注册表、角色分派或调度。新增每份 Skill 为短步骤与可检查完成条件，其 reference 提供随包离线正文；来源 URL 只作出处，没有冒称工具安装、联网读取或原生流程执行。

四专家分别承接实验设计、关键路径诊断、kernel / wrapper 设计和独立测量审查，保留 precision / layout / fusion / graph / memory / communication 的相互作用。导数、RNG、checkpoint、分布式语义按实际任务适用；缺 trace / rank / 硬件 / 质量证据均保持缺口。未发现把局部速度相乘、把候选文本称编译通过或把模型审查称 owner 采用的新增合同。

新增测试检查这个发行的四叶实际引用、只读权限、完整祖先、reference 字节及删除活动库后的 manifest 准备。固定版本和路径是在检查本发行身份；未发现将运行参数的有效范围固定到默认值。没有为提示文案复制运行算法或新增 CI。

## 已核证据与限制

独立只读核验结果：

- R1 全部 30 件快照身份一致；旧 78 件 preset 资产与基线逐字保持，四个旧 catalog 条目保持，仅新增 `training-optimization-v2`。
- 283 件冻结参考资产与 Git 基线保持，并逐件符合 `reference-manifest.json` 的 SHA256；未修改原 runner / 采用所有者。
- 已读 source-r1 的命令、stdout、stderr、结果及新测试的持久完整输入。记录为源码 `tests/test_presets.py -q` **12 passed / 42.68 秒**、外层 **43.420 秒 / exit 0**；评审者没有重跑测试。静态记录的 178 个本地目标、0 issue 是作者检查结果，本报告未把它称为独立链接检查。
- 已读 source-r2 的命令、stdout、stderr、结果和四份完整持久输入。修正后只重跑受影响新 v2 准备测试：**1 passed / 6.67 秒**、外层 **7.326 秒 / exit 0**。没有为指令文案复制原算法测试，也没有借 R1 的全套结果宣称 R2 已重新运行全套。

## R3 安装与真实调用原件补核

已读 `verify-installed-r2.py`、`run-installed-r2.py`、`real-leaves-r1.py`、`audit-leaves-r1.py`、`self-review-r1.py`、`audit-self-review-r1.py` 及其原结果；未执行这些会写入、启动模型的脚本。评审者独立重算 wheel / 安装身份，并用已核安装包的只读 inspectors 验证完整 manifest 与输入；原 SQLite 以只读方式打开。没有重跑安装、测试、服务或模型。

安装原件：R1 wheel SHA256 `4cfcb7e0a66299781ceb21aa4b2e5761f3746a9bae890b4a3c9af2c332429ab4`，原安装 suite **12 passed / 45.97 秒**、外层 **47.508 秒 / exit 0**，仍只授予含原 P2 的 R1。R2 wheel SHA256 `396e37a80c70637deef330b152163b821272db097f926a8a6d430af389b53a61`；独立核过源码副本 / wheel / 安装的完整 497 件产品集合与字节、wheel 全部 505 件及 RECORD、安装 RECORD 510 行、非 editable 元数据和 283 件冻结参考身份，R2 安装产品也与当前产品相等。修正后的受影响安装测试为 **1 passed / 7.72 秒**、外层 **9.248 秒 / exit 0**；没有称 R2 完整重跑 R1 suite。

四叶都来自 R2 根 `f82061705d1b7a0f8bc6b480327aa0602b8b3519c35aa2a985e1deeadfbb33fa`，原记录如下。计时为作者驱动保存的调用区间，已与公开投影核对。

|叶 / 实际 role|原 run ID|秒|固定资源 / 字节|结果范围|
|---|---|---:|---:|---|
|design / experiment-planner|`c24bea37184246c7931a9dabd25764fb`|85.371|5 / 5,395|有限的 B0 / A / B / 条件 AB 提案；数值、设备与预算缺口明确|
|profile / performance-analyst|`19a5a8dd1f5f488d9325ef206dd6445b`|55.684|5 / 5,288|无 trace 时仅给可证伪假设与最小采集请求，不声称已知瓶颈|
|kernel / kernel-tuner|`3b7d45e749f342c9a63b39096a3eed6c`|82.368|4 / 5,044|未执行的 FP32 LayerNorm / wrapper 设计，数值、capture 与真实 caller 条件保留|
|measurement / reviewer|`4f30741fa8314f189817ac2512cbf027`|64.395|5 / 5,309|`request-changes`：缺候选、oracle / 阈值、硬件 / 版本、配对原样本与总成本|

每条原 CLI 记录与 SQLite 一致，均 succeeded / exit 0；四个 native thread ID 各异。已逐条核完整冻结 manifest → 原 prepared input → 运行快照 → prompt / 实际 stdin / protocol prompt → native 最终结构结果 / protocol result → 原 result。kernel task 含 design / profile 两份完整原 result，measurement task 含三份完整原 result，逐字与 SHA256 一致；不是摘要替代或自动前驱运行。

每叶来源集合恰为自身与结构祖先，父链所有权限仍为 write=[]、shell=false、network=[]。逐件从输入定义树独立重建 scope，并与 scope 原始字节、服务端 JSONL、native 工具返回交叉核对：共 **19 份资源 / 21,036B**，list 完整，全部 read 的 UTF-8 成功页连续覆盖到 `next_offset:null`，没有失败 MCP 调用；native 也没有执行其他工具。原命令只开放固定 task-MCP，关闭 shell / web / multi-agent。这里证明字节交付和实际读取请求，不证明模型理解、提供商容量、计费或 OS 隔离。

requested / actual binding 与 admission、run、公开投影相等：前三叶 Codex → Codex，measurement Claude Code → Codex；每次保存显式已授权回退原因，引用既有 Claude 失败。本片四叶没有 Claude 成功或异构后端验收证据，也没有据此前失败扩大工具权限。

固定 workload 是实际保存的 `baseline.py` 源码 fixture，SHA256 `c8a27ba40b8693fd64e6f4723cf58f478df71fa470661ce43e83df719651fab7`；shape / FP32 / inference 是操作者给定规格。四份完整原结果均保留未测事实、来源、前驱与角色职责。measurement 将缺实验证据列为阻塞条件，是本片只读交付的正确结果，没有将缺口变为通过、回归或收益。

自身原模板：`ergora-structure-review@1.0.0` / `ergora-structure-reviewer@1.0.0`，run `b5d851f5f52944dfbcd1bf825a447f49`，独立 native thread，Codex 显式回退，text-only；原结果为 succeeded / approve，**54.533 秒**。已独立核 packet index 恰含 R3 的全部 **24 件产品 / 数据 / 测试文件，49,304B**，每份源码身份及全文均进入实际 task / stdin；完整 prompt 为 **57,651B**、SHA256 `789852815045054b9a9ab330dd793d5894c6798d432f27c7048f9ffa10aaf8ac`。三份结构祖先 / 自身资源（163 / 354 / 521B）与输入相同，stdin / protocol / native 最终结果 / 原 result / `review.md` 相互一致。它没有 MCP 附件或模型工具调用，不声称进程全量采样或模型理解。

公开 `docs/delivery/evidence/2026-11-13-optimization-experts-v2.json` 的原件 SHA、产品身份、四条调用状态 / 计时 / 输入与结果摘要 / 全前驱 / 资源数量，以及自身模板投影均与原件匹配。未发现秘密值、虚构测量或把原生完成称采用的新增声明。

## 仍未验证的范围

本评审本轮没有安装、调用模型、运行 GPU / profiler / Forge / KDA、访问网络或提交。通过的是 B1 跨域只读资料及一次固定 FP32 inference fixture 的实际提案 / 诊断 / 设计 / 审查链，不泛化为低精度训练、梯度、多 rank、其他 layout 的运行正确性或性能。

自动 proposal 图、B2 方向包、真实硬件优化与独立数值 / 质量 / 性能评价、完整 Forge / KDA 内部会话和原 owner 采用仍是后续出口。本候选普通提交、远端精确身份及自己的必要 CI 尚未核准。A2 重构旅程属于独立片，其未完成范围没有转嫁为 B1 finding。

R3 冻结后活动 `docs/PLAN.md` 另更新了基线 `00922d3` 的发布事实；最后重核 R3 31 件快照身份仍相等，活动树漂移仅该状态文档。已单独只读核官方 run / 两 job HTML 的原响应 SHA、精确提交链接与七必要步骤：基线 CI `43373597757` 为 Cancelled，Linux regression 达 20 分钟 job 上限取消，Windows 四步骤 success；不称本候选 CI 通过，也不从无完整日志推断具体测试故障。该状态补充没有改变 B1 产品或模型原件。
