# D2-B2b 执行图与 packing 方向独立审查

日期：2026-11-13。审查者：fresh-context `optimization_execution_directions_review`；另由两个全新上下文的 `spec`／`standards` 审查者平行检查两轴。依据项目 AGENTS、maintainable-project-delivery 的独立审查要求、code-review 的双轴流程、codebase-design 的职责／复用原则及用户指定的 AIHERO 索引。

本片本地独立审查通过：两轴各自发现的同一项 P3 状态记录问题已修正，并分别由原审查者同片复核关闭；最终 Spec 开放 0、Standards 开放 0。没有产品正确性或结构 finding。结论仅覆盖两个只读资料方向与交付合同，不授予 GPU／训练、收益、自动图执行、采用、发布或 CI 通过。

## 固定范围

- 基线：`fc67c3da7041bdcfd46430bc7268e25a55df6de9`。
- 初审：私有本片 checks 中 `review-r2/manifest.json` 的 13 份冻结文件；全部 SHA256 核准，显式比较基线与冻结正文，包含六份新增文件。基线与当时 HEAD 相同，未用空的 `baseline...HEAD` 代替未提交快照。
- 最终同片候选：`review-r3/manifest.json`，SHA256 `ec95f820b2f0ba45fc28553e5c6f03e2d13e317fbf13e086dc44960054f26aec`；同样 13 份文件全部复核。相对 r2 仅交付记录第 9 行的一格状态文字改变，八份产品／测试及另外四份文档／证据逐字不变。
- 前置 B1／B2a、stdin／poll 修正作为已有依赖保留；A2、CI 耗时调查、其他工作树文档及远端操作不在本片出口。

|冻结文件|范围|
|---|---|
|`src/ergora/data/presets/presets.json`、`tests/test_presets.py`|两个新 catalog 选择；既有方向合同测试增加两项参数|
|`src/ergora/data/presets/workflows/ergora-opt-cuda-graphs-proposal/`|`workflow.json`、`instructions.md`、`context/cuda-graphs.md`|
|`src/ergora/data/presets/workflows/ergora-opt-sequence-packing-proposal/`|`workflow.json`、`instructions.md`、`context/sequence-packing.md`|
|`docs/TRAINING.md`、`docs/TEMPLATE_WALKTHROUGHS.md`|选择入口、所需材料、逐叶调用与完整手动交接|
|`docs/plans/2026-11-13-specialist-presets.md`|原 D2-B2 要求和本片状态|
|`docs/delivery/2026-11-13-optimization-execution-directions.md`、`docs/delivery/evidence/2026-11-13-optimization-execution-directions.json`|交付记录及公开证据投影|

原始要求来自 [D2-B2 计划](../plans/2026-11-13-specialist-presets.md#b2按决策粒度发布资料子模板)、[R6 来源研究](../research/2026-11-12-optimization-execution-graph-agents.md)，以及全部结构祖先继承、兄弟不继承和子权限上限合同。审查先读原要求、冻结差异与相关实现，再核作者记录及原始证据。

## Spec

新鲜上下文 Spec 审查：本片没有缺失／部分实现的要求、范围扩张或错误产品实现。两个根可独立选择，精确复用 `ergora-training-analysis@2.0.0` 与 `ergora-measurement-review@2.0.0`；design／profile／独立 measurement 三叶包含所需正确性／质量门槛。完整方向 context、结构祖先及自身 Skill 树保留；兄弟资源未进入该叶 scope，所有子权限仍只读。

没有新增 Agent、role、类、schema、runner、ledger 或 scheduler。一次 `run-input` 仍只运行所选叶；measurement 的两个原始前驱由操作者全文传递。原 runner／owner 保有执行、停止、恢复及采用权。固定知识来源与实际安装版本、资格校验与实际执行、capture 与 replay、配置容量与有效 token 吞吐明确分开。

Spec 初审 P3：r2 交付记录第 9 行仍写“尚未登记catalog，未称可安装或运行通过”，而实际 catalog、下一行及原安装／提升证据均已完成。原计划第 185 行要求更新对应状态及交付记录，该状态会误导恢复工作的人。最小修正是登记当前完成事实或明确标为历史。r3 仅修正该状态格，Spec 审查者独立核全部 13 个 hash 及单行差异后关闭 P3；最终开放 0。

Spec 审查者另独立核了包身份、两 RECORD、既有 catalog／v2／283 字节、六次原调用的材料和前驱链、原自身结构模板。两份 measurement 均正确保留缺实际执行／质量／测量证据的 `request-changes`，没有据模型成功调用授予实验采用。

## Standards

Standards 初审同一项 P3：上述当前状态表的“尚未登记catalog”与第 10 行的安装／提升、后文已完成的逐字提升互相冲突。违反 AGENTS 的状态变化后同步计划和交付记录要求，以及 maintainable-project-delivery 区分实施、验证和审查状态的规则；恢复者可能误判可安装性或重复已完成检查。最小修正仅涉及本片状态格。

原 Standards 审查者复核 r3：P3 关闭，开放 0。新格记录六份资料和 catalog 已提升且等于已验候选，运行证据留在各自下一行；没有扩大硬件／执行验收。全部 13 个 hash 及仅一行变化独立核准，八份产品／测试和四份其他文档／证据不变。

范围内没有其他实证规范违例或需处理的启发式 smell。方向差异留在原不可变数据包，共享专家和原运行所有者复用；重复的 workflow 配置符合现有包 Interface，不需要新增共享运行抽象。新文件由既有 catalog 安装 Module 的 CLI／HTTP 消费。

原参数化测试仅增加两个方向，检查漏装、错误精确专家版本、只读权限、方向 context 内容／来源及删除活动定义库后的离线 manifest 输入恢复。这些是新包可发生的静默遗漏，未复制算法或为文字建立测试框架。原 stdout 中两新增 case 分别约 4.36／4.34 秒；没有因其成本删减检查或放宽 CI 预算。

## 原件与验证边界

聚合审查者使用只读标准库比较及原文件重新核验，不只接受作者汇总；两个轴也分别检查了原件。没有重新调用产品、模型、测试、安装、服务或网络。

|证据|独立核对结果与实际范围|
|---|---|
|冻结／提升身份|13 个 r2／r3 hash 均核准；八份产品／测试与原测试 source、工作树及提升记录相等。构建原由 `e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd` 加明确 stdin／poll、B2a 前置及本片覆盖产生；本轮再核完整 512 产品字节与当前工作树相等，不把提升称重建／重跑|
|非 editable wheel|SHA256 `7dfe5549d61959aab2eea97f08a5485bd5eda46db0e931abb0dfcf9e9e895263`；512 产品文件在隔离 source／wheel／安装／当前源码逐字相等；wheel RECORD 的 520 行及安装 RECORD 的 525 行按实际 hash／size 核准|
|兼容身份|八个既有 catalog 条目逐字段不变；B1 训练 v2 七包的 22 份文件及 283 冻结参考文件与基线相等；新选择不改旧任务和旧版本|
|原安装检查|直接读取原 pytest stdout：17 passed／69.67 秒；外部控制器 71.623 秒。包括五方向完整材料、原配方／重构／v2 行为；本轮未重跑，也不以此代替整个 suite 或 CI|
|六叶原调用|两方向各用独立 State，三次独立会话；原完整 input 树摘要、request、assets、prompt、实际 stdin、protocol、scope、native stream 和最终 result 相符。scope 与结构祖先／自身资源逐字匹配，仅原 `list`／`read` 工具；Codex 显式回退原因保留，不称异构后端通过或新增 OS 隔离|
|完整资源读取|36 个资源出现、62,230B；graph 为 18／29,831B，packing 为 18／32,399B。固定附件、scope 与原 native 页字节及 hash 相符，UTF-8 连续读取至 `next_offset:null`；核的是交付和读取，不宣称模型理解、训练收益或计费结论|
|手动前驱及独立判词|两 measurement 的 task／stdin 均包含 design／profile 两份原结果全文；各自 SHA 相符。两份结果均为 `request-changes`，明确缺候选／版本、硬件、独立数值／质量、实际 replay／mask、配对测量和恢复证据|
|原自身结构模板|原已安装 `ergora-structure-review` 根；八份产品／测试全文 41,857B 与实际 task／input／stdin／protocol 相符，三份结构／自身资源完整；native 最终消息与保存结果相同，108.003 秒 `approve`，结果 SHA256 `d56d450d7f773bf3ffeef13c1d195b074c64fc13bb275a12f5e20bcdc5927d28`。该聚焦审查原已注明工具不可用及上游／包身份未独立核的限制，本轮两轴补核不改写原判词范围|

固定来源仅在 R6 的 `execution-graph` 缓存内检查：直接核 13 份相关来源的正文／长度／SHA 和获取回执。十份 Bridge 源码／文档与原归档中 `55694838ce73cd23b00ff95bd00512aefb963ce0` 对应成员相同；归档 SHA256 `3e0dc0239e3a11e9887ea4b73d4bc1b0ceb1df3f2af52d4f3f732bf1b4581c6a`。PyTorch CUDA 2.15 文档、CUDAGraph Trees 及 compile 入口与版本 URL／固定 `31a77fc9c0a7c6fff15a1ff58c743f53b1a9d457` 回执相符。

实际源码支持以下资料边界：full-iteration wrapper 包装 forward/backward，optimizer capture 另行设门；helper 兼容旧／新 Core controls 和显式 module scopes。offline 固定宽度／padded metadata 校验与 Energon／global-batch runtime THD 的 MBS1、per-token loss、非平均 collective、禁 graph／PP 门槛分开；global-batch 的 VPP／FSDP／Mamba 限制没有套给普通 in-batch。TP／CP／SP 与 eval topology 推导对齐，Qwen3-VL 的 MTP 路径使用物理 padded offsets。资源要求核地址／对象寿命、RNG、完整 loss／梯度／optimizer／恢复、真实有效 token 和配对 caller 总成本，没有把 eligibility 或短例子称实际支持／收益。

私有本片 checks 保存 `review-r2-frozen.diff`、两个轴原报告、`independent-r2-package-audit.json`、`independent-r2-verify-raw.py`／`independent-r2-raw-audit.json`、`independent-r2-source-audit.json` 及 `independent-r3-delta.json`／`.diff`。[公开证据投影](evidence/2026-11-13-optimization-execution-directions.json)保持原候选和调用范围。产品是本项目短知识综合和来源引用，没有安装或再分发上游新工具／Skill 正文。

实际目标栈／GPU、数值和模型质量、性能收益、checkpoint 恢复、B3 实验采用及本候选普通发布／必要 CI 仍由各自原 owner 验收；本地资料片不关闭这些出口。

最终：Spec 初审 1 项 P3，已关闭，开放 0；Standards 初审 1 项 P3，已关闭，开放 0。两轴独立保留同一状态问题的发现和修正，不跨轴合并或排序。
