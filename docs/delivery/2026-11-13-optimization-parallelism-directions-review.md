# D2-B2c 并行策略、FSDP 与分层 CP 方向独立审查

日期：2026-11-13。审查者：fresh-context `optimization_parallelism_directions_review`；两个另外的 fresh-context `spec`／`standards` 审查者平行检查两轴。依据项目 AGENTS、maintainable-project-delivery 及独立审查 brief、code-review、codebase-design 和用户指定的 AIHERO 索引。

最终本地独立审查通过：Spec 开放 0、Standards 开放 0，未发现产品正确性、结构或最终记录问题。冻结源码、隔离安装、九叶完整材料／手动前驱、自身原结构模板及最终 17 文件／公开投影均完成同片补核。结论限于三个只读资料方向及实际提案材料链，不授予 GPU／训练、收益、checkpoint 恢复、自动图执行、采用、发布或 CI 通过。

初轮 r3 审查时九叶仍在途，两个轴均只给源码／安装范围结论；下文保留当时观察时点。后到终态由原 Spec／Standards 审查者及聚合审查者直接核原件，没有把初轮通过或自身模型判词扩写为完整验收。

## 固定范围

- 基线：`a711539617ca8d2892d240079e76cb243784c55d`。已解析完整 Git 身份，`git log <baseline>..HEAD` 与 `git diff <baseline>...HEAD` 当时均为空；本片是未提交差异，审查显式比较基线 Git 对象和冻结正文。
- 初审候选：本片私有 checks 的 `review-r3/manifest.json`，SHA256 `865d4132d3f0e2ea4e6aea139b188c28a4ad5b6852743f6d6d1bb72f0addb64d`。全部 16 个文件 SHA 核准，包含九份基线不存在的新资料；十一份产品／测试与实际安装候选覆盖逐字相等。
- 最终同片候选：`review-r4/manifest.json`，SHA256 `b531c864e3690206a3c5abefbe9dc898be9ee5e2619527af6ca6f7c1431e7650`。全部 17 个 hash 和当前正文核准；相对 r3，十四份文件逐字不变，仅交付记录／专用计划的状态更新及新增一份公开证据投影。十一份产品／测试、两手册和 R4 研究正文不变，未重建或重跑来继承旧结论。
- 原始要求：[D2-B2 方向表、共同继承／后端／验收合同及 B2c 检查点](../plans/2026-11-13-specialist-presets.md)、[R4 固定来源](../research/2026-11-12-optimization-parallelism-agents.md)。先读原要求和原始正文，再核作者记录；其他工作树的 PLAN、发布和 CI 成本调查不属于本片审查出口。

|冻结文件|范围|
|---|---|
|`src/ergora/data/presets/presets.json`、`tests/test_presets.py`|三个 catalog 选择，原方向合同检查增加三项参数|
|`src/ergora/data/presets/workflows/ergora-opt-parallelism-proposal/`|`workflow.json`、`instructions.md`、`context/parallelism.md`|
|`src/ergora/data/presets/workflows/ergora-opt-megatron-fsdp-proposal/`|`workflow.json`、`instructions.md`、`context/megatron-fsdp.md`|
|`src/ergora/data/presets/workflows/ergora-opt-hierarchical-cp-proposal/`|`workflow.json`、`instructions.md`、`context/hierarchical-cp.md`|
|`docs/TRAINING.md`、`docs/TEMPLATE_WALKTHROUGHS.md`|三个方向选择、实际所需材料与逐叶使用范围|
|`docs/research/2026-11-12-optimization-parallelism-agents.md`|同 pin 已删除 FSDP 字段的事实修正|
|`docs/plans/2026-11-13-specialist-presets.md`、`docs/delivery/2026-11-13-optimization-parallelism-directions.md`|原要求和本片实施／验证／审查状态|
|`docs/delivery/evidence/2026-11-13-optimization-parallelism-directions.json`|r4 新增；原调用、材料／前驱和审计身份的公开投影|

## Spec

新鲜上下文 Spec 审查：冻结 16 文件范围内无 finding。三个根可独立选择，精确复用 `ergora-training-analysis@2.0.0`、`ergora-measurement-review@2.0.0` 及 design／profile／review 三位专家；完整声明方向资料、祖先资源、手动传递全部原始前驱的要求保持。没有增加执行结构或授权。

固定来源支持两 mesh 的必要整除条件及布局可行性限制、已修正的 FSDP flag／checkpoint 区分，以及显式 HCP 的 MPU／实际组／TE 路径和独立数值证据门槛。未发现缺失／部分实现的本片要求、范围扩张或看似实现而错误的产品行为。

Spec 审查者也独立比较基线加冻结覆盖与归档 source／wheel／installed 全部 521 产品文件，核两 RECORD、283 冻结参考、旧十条 catalog 和实际测试源码；原 pytest 输出为 20 passed／84.42 秒，未重跑。其初审时九叶、完整运行材料／前驱链及自身模板仍列待验；后到证据由聚合审查者分别补核，不回写初审观察时点。

原 Spec 审查者最终补核：17 个 r4 身份和精确文档差异、九份完整原输出、54 资源／94,170B 的实际连续读取、完整两个原前驱、native 最终消息与保存结果及公开投影均相符，无新 finding。Parallelism 保留 LCM 必要条件和更新语义；FSDP 使用正确 flag、分开权重与完整恢复；HCP 保留显式选择、路径／数值和拓扑缺项。独立 measurement 还实际指出 parallelism 的候选标签／预算不一致和 HCP 两份计划／干预计数未协调，三份均为 request-changes，未授予执行或采用权。

本结论不授予 GPU、多 rank 训练、数值正确性、吞吐或恢复验收。

## Standards

新鲜上下文 Standards 审查：无实证规范违例，亦无需处理的启发式 smell。三个包遵循 [Workflow 定义](../WORKFLOW_DEFINITIONS.md#定义和数据流)的精确引用与资源格式、完整继承和子权限上限；资源摘要和可移植路径符合 [Agent 资源合同](../AGENT_DEFINITIONS.md#资源和存储边界)。初审文档保留实际来源、安装限制和待验状态，符合 AGENTS 的记录要求。

已考虑重复 `workflow.json` 和“Each run-input call runs only its selected leaf”等段落可能构成 Duplicated Code。计划明确每方向是可独立版本化的三文件包；共享行为已由 analysis／measurement v2 负责，方向根持有自己的知识。为此增加框架会扩大 Interface。删掉根后，选择入口和完整祖先资料装配将重新散落到调用者；其 Depth、Locality 和现有 Seam 合理。既有 CLI `cli.py:787` 和 HTTP `web.py:376` 实际消费同一个安装 Module，没有虚构生产复用。

测试只向原参数化用例增加三个方向，检查漏装、精确专家版本、只读权限、方向正文／来源，以及移除活动定义库后的离线 manifest 输入；这些新包可发生的静默遗漏值得覆盖。没有新增与实现镜像的文本算法测试或另一套框架。原三 case 的 call 成本约 4.49／4.36／4.52 秒，未据此扩大或替代 CI 通过范围。

Standards 审查者也独立核了全部快照、发行字节、两 RECORD、旧包、原 stdout 及九份静态输入；其初审的实际模型读取和前驱交接状态保持待验。

原 Standards 审查者最终补核通过：全部 17 份 r4 身份及差异、九次原输入树／资产／scope／native／结果／前驱链、九个独立 native session、54 资源／94,170B 和公开投影一致；没有新规范违例或需处理的 smell。所有叶保持 readonly 祖先上限，无正式执行授权；实际后端均为 Codex，measurement 保留 Claude Code 原请求及显式回退原因。实际完整字节与请求读取不证明模型理解；自身原审查限制及 r1→r2 标签修正范围准确保留。

## 原件与验证边界

聚合审查者使用只读标准库散列、Git 对象、ZIP／CSV 和 JSON 比较重新核原件；没有重跑产品、模型、测试、安装、服务或网络。实际材料所有者、原 `_materials`／`_Compilation`、父权限检查、manifest 恢复和后端 factory 的职责均直接读源码确认；本片不修改这些运行所有者。

|证据|独立核对结果与范围|
|---|---|
|原始候选|16 个冻结 hash 全部相符；九份新文件明确纳入，十一份产品／测试与 `install-r1` source 覆盖相等。基线 512 产品中除 catalog 外的文件逐字保持；新增九份得到 521，未混入其他工作树变化|
|非 editable wheel|SHA256 `e91f7d2daf15dd0a8bd58afd366670909af43b9f6aa004c598ae64c1aa312837`；521 产品文件在归档 source／wheel／installed 逐字相等；wheel 全 529 行和 installed 全 534 行 RECORD 按实际 hash／size 验证|
|兼容身份|旧十条 catalog 全字段相等；所有原产品文件含共享 v2 包与 283 参考文件保持基线字节；新增选择不改写旧包或旧任务|
|原安装检查|原命令为隔离解释器 `-I -m pytest -v --tb=short --durations=15 tests/test_presets.py`；实际 stdout 为 20 passed／84.42 秒，外部控制器 86.600 秒。未借此宣称完整 suite／CI|
|静态完整继承|直接读三新增方向的原参数 case 5–7：九份 prepared input 各包含所有已声明正文和完整 assets，来源恰为 root、结构父和自身 expert；write=[]、shell=false、network=[]。这些是静态交付／恢复事实，不能替代实际模型读取|
|自身原结构模板|原 `ergora-structure-review`／`ergora-structure-reviewer@1.0.0`，十一份产品／测试 51,577B 全文和三份祖先／自身资源均进入真实 57,443B prompt／stdin。input 摘要、packet、实际 stdin、原结果相符；44.8738 秒 approve，结果 SHA256 `8888966502c43f41052c6344c08e03019c2398de8e3da6d56591235f678205bd`|
|自身判词范围|原模型明确未直接检查共享／上游／包身份，调用当时 tests 和九叶证据待验。该聚焦判词不替代本轮包／来源检查，不证明硬件执行、模型理解或异构后端成功。原 native 两次内置 MCP 元资源查询均返回空，不等于启动 Ergora task-MCP。原辅助 audit-r1 的 scope 文本误写 focused8，但 packet_files=11；保留原件，r2 脚本修为 focused11 及另存文件后从原链生成新投影，未重跑模型、改变源输入或判词|
|真实九叶|初审在途状态保留；最终九次原调用均 succeeded，三方向各独立 State／三 native session。直接重新核完整输入树及摘要、全部 graph 资产与发行 source 字节、声明祖先／自身 scope、prompt=实际 stdin=protocol、实际 native 最终 JSON=原保存结果。只使用原 list／read，未见失败调用；显式后端回退原因保持，不称异构后端成功|
|完整实际读取|每方向 18 资源：parallelism 32,900B、FSDP 30,806B、HCP 30,464B，总计 54／94,170B。scope 恰等于所选祖先及自身完整 Skill 树；原 native 每页 offset／字节／SHA／size 连续，UTF-8 读至 next_offset:null，list 目录与全部 scope 相等。核的是原交付和读取，未宣称理解或计费|
|手动前驱与独立评价|三个 measurement 的 task 和实际 stdin 均包含 design／profile 两份完整原始 JSON，各自 SHA 与保存结果一致；三份结果均 request-changes。完整原结果保留候选／干预协调、真实栈、原生组、独立数值／质量、测量／全 rank 显存、checkpoint／完整恢复缺项，不把未知写成失败或 no_gain|
|最终公开投影|SHA256 `42d192b464331242e4a7789319b766851f73dc8570acf3ccaf71ff0f4d2add3e`；九个调用的字段及输入／结果／前驱摘要、三个 raw audit SHA、自身 r2 audit SHA、发行及测试数值逐一与原件一致。最终状态明确补核时点，六份相关文档的本地文件链接均存在；未加入本机配置或密钥|

## 固定知识核对

直接核 R4 私有缓存中相关来源的原始正文与 SHA／获取回执：Bridge parallelism Skill、FSDP Skill、config、initialize、checkpointing；独立 Core dev parallel state；另取的同 pin HCP Skill／guide 和 FSDP guide。三个补充来源 SHA 分别为 `5881cb210e69f1875dfcec3e34caa614a95c67fd972e6baf8fb740b644bf8609`、`4698e84a5a65f50fbe6ef53742899da526b5ac211e01929bf6c6cfad90d325dc`、`80a74d2714ff7d9b897c6712f0f11f29bee946d7690bddb8e7dd6754f7fdf736`。本轮未联网获取；Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0` 和 Core dev `f78809f6d9c88f8638ea7822966f35057a63fd5c` 是分开的知识身份，不是安装栈兼容证明。

- 普通无 GTP／额外 stage／自定义 layout 的 dense／expert 路径分别要求 W 可被 TP×PP×CP 和 ETP×EP×PP 整除，因此 PP×LCM 是共同整除下界；原 Core 还检查 rank 顺序与 dense／expert PP 组相等。资料明确这些是必要条件，保留本地 head／expert／layer、batch、SP、native validator 和有效训练语义；未把原 Skill 的 max 公式推广成任意布局充分条件。
- 原 config 实际使用 `ddp.use_megatron_fsdp`，按 MFSDP 版本选择不同路径并自动调整相关 flags；V1 的 `fsdp_dtensor` 检查以 save/load 为条件。资料要求核实际 wrapper／resolved settings 和完整栈，区分 Torch FSDP2／MFSDP V2；权重 reshaping、格式兼容与 optimizer／step／LR／RNG／数据顺序的完整续训分别验收。
- HCP 的原 MPU 路径传入 hierarchy sizes，decentralized 路径不建立 HCP；引用的 Skill 说明 TE 路径、最低版本、旧缺组静默错误和专用端到端证据缺口。资料要求比较简单 transport、检查实际 hierarchical groups 传入 attention、独立 output／loss／gradient／update、全 rank 显存及端到端测量，没有将建组或最低版本视为组合认证。

产品只交付本项目短知识综合和来源引用；没有新增安装、拷贝分发上游 Skill、并行 solver、GPU 工具或自动图运行能力。实际目标栈／GPU、模型质量、收益、checkpoint 恢复、B3 实验采用及普通发布／必要 CI 继续由各自原 owner 验收。

最终计数：Spec 0、Standards 0；两个轴各自无最严重 finding。本片没有剩余阻断问题；实际训练／恢复／采用及普通发布／必要 CI 保持上述独立范围。
