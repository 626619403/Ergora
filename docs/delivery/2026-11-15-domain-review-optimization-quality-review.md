# Q0 独立需求与可维护性终核

日期：2026-11-15。评审者：Codex `domain_review_plan_audit`，fresh-context 独立上下文。先读原始用户要求、仓库 `AGENTS.md`、独立评审规范和 `ergora-codebase-quality` 的三个参考，再核改动、相关源码、公开原件及实际调用证据。仅写本报告；未改生产文件、安装、提交或平台写入。

## 范围与身份

基线／当前 HEAD：`871cc4b6b2c21420307a002bf5b983707720fe90`；分支：`refactor/architecture-foundations`。检查 `docs/PLAN.md` 的活动 Q 入口与完整 tracked diff，以及下表四份新增文档全文。五份实际字节均与作者的 `review-scope-r1` 冻结副本及其摘要一致，包含 untracked 内容；不将历史交付重新作为本轮验收。

|已核文件|SHA-256|
|---|---|
|[当前计划入口](../PLAN.md)|`83eb9c08075acd37c79efde26750bf393ee184d194b5543a85a21aecf705b431`|
|[Q 计划](../plans/2026-11-15-domain-review-optimization-quality.md)|`bd029564a345837cf0b18e636d7508f3eb0444dac1ccc1bb72712b867731262c`|
|[Q0 交付](2026-11-15-domain-review-optimization-quality.md)|`7c1a030da2067263ace211541cf6ed865965e26467fc92d36b95b8675c76a99f`|
|[PR／MR 工具研究](../research/2026-11-15-pr-mr-review-tools.md)|`ee07f557aeb67a634175ee3f640f0ba9166c39ed590dbf0731e575ee6f060a34`|
|[循环优化／组件研究](../research/2026-11-15-iterative-optimization-architecture.md)|`97fd218396df23cfe9f0fb2579737125150396b0fee5d1ffcb5b93199282e3a0`|

本报告之后的完成状态、发布身份等记账不在上述字节身份内，须按其实际证据记录。

## 两轴结论

**需求符合性：approve，仅限 Q0 研究与计划。** 已回答现有通用审查与尚缺领域专长的区别；调查指定 BBuf 版本、Claude 各审查产品及预训练／后训练来源，并将采用边界写入计划。完整算法／依赖／并行与生命周期图、先保留原始参照、按瓶颈选择干预、系统复测、跨轮保存前后与失败原件、量化质量预算、组件协议、示例和最终发布审查均有明确后续节点。Q1–Q6 未冒称实施；真实 B3／GPU 和完整 Forge 仍开放。

**可维护性：approve，仅限本次规划。** 计划复用已有 Git 对象读取、Agent／ReviewDAG、训练／runner／evidence、评价／采用和预算生命周期。外部建议性审查没有冒用正式候选批准，循环没有给静态 DAG 加回边；训练实现与 Ergora 控制面责任清楚。局部协议先盘点现有规范；重构要求真实调用／状态成本，未以文件长度、未来可能复用或框架声望预建抽象。测试／断言删除须保留原故障边界，文档片没有要求未改产品的全量测试。

**Findings：在本次检查范围内无实质 finding；开放阻断项 0。** 此结论不批准未来实现、模板能力、性能／质量效果或提交／推送／CI。

## 独立核查证据

- 用 `git status`、分支／HEAD／近期提交和完整 tracked diff 对齐基线；`git diff --name-only 871cc4b6b2c21420307a002bf5b983707720fe90 -- src tests scripts pyproject.toml .github` 为空。另核五份文档的 UTF-8、行尾空白、152 个本地目标和其中 7 个 Markdown 标题 fragment，未见错误；作者原检查另记录 116 个引用定义、0 错误。简单 fragment 检查不等于浏览器渲染验收。
- 直接解析 preset 目录得到 28 项及 18 个纵向优化方向；读原三路 all-join、v2 `analysis → kernel → measurement`、`issues.link_review`／本族平台映射、精确 blob reader、训练 baseline 不覆盖与 evidence 匹配门禁、Claude 只读工具和原 DAG／资源边界。静态盘点不作为运行成功。
- 公开原件抽核：BBuf 固定 `316923d…` 的 tag README 与固定 README 摘要相同；8,207,166B 固定归档确有 11 个 `SKILL.md`、无 LICENSE／COPYING，manifest 自报 0.10.0。归档 SHA-256 为 `ae5aeea48e23b269f14c70dad4df656aed41fd656d0b9b60cdf9a777897516e8`。独立读取 Claude 本地／托管／Ultrareview 官方文档、固定插件命令与许可、PR-Agent CLI，以及 Bridge `40d4467…` review Skill、slime `79aa41a…` review Skill；主要功能和限制与研究所述相符。
- 第二研究的非直观事实另回到固定源码：Bridge `5569483…` 的证据门控流程、按 rank 构造数据和 deprecated `DatasetProvider`；TorchTitan `631d544…` 的 Trainer／Engine、chunked loss 的 head 驻留／pipeline 责任、optimizer `state_dict()` 的零学习率状态物化及 scoped override；slime 的启动权重就绪、训练完成与 durable checkpoint 区别，以及 CP 零值项维持 autograd collective 参与。未见将这些具体接缝扩大为全框架通用保证。
- 直接核原结构模板调用 `0af8943512da46d994e2aa4da91e837f` 的原回复、持久结果、输入及 packet index：`succeeded / approve`、returncode 0；21 份正文逐项按字节数和摘要核对，共 360,522B；实际 stdin 与准备 prompt 逐字相同，完整任务和三份声明的父／叶资料均在其中。input digest 为 `7c2e9325b800593cd3d9241392d7b6db04dfe9e2cba55c7d579d88b94ef89146`；原结果 SHA-256 为 `d74aec37d5bb408332995c85fbbed771b0ba6af072a0f6c7f9e1ba576d056766`。模型输入的交付记录为运行前 `d92f97c…`，上表 `7c1a030…` 已追加该次结果；没有将两者冒称同一模型输入。模型意见只作为补充证据。

## 未验范围与后继

没有穷举抓取全部外部 URL、通读全部上游仓库、论文全文或许可例外；公开来源为上述抽核，动态官方文档只代表本次读取。未运行新领域 reviewer、产品测试、真实训练／GPU／profiler或性能／质量实验；未核安装／平台权限、发布与 CI。现有 Codex text-only 调用不证明 Claude 审查能力或异后端成功。

Q0 本地文档内容可结束独立审查；发布按实际最终文件与远端／适用 CI 另记。下一实现片为 Q1.1 精确本地审查包；Q3.1 与 Q5.1 的只读盘点可按计划推进，各片仍须固定身份、运行其相关验证并独立评审。

## 固定发布补核

2026-11-15，原评审者补核实际发布 `7ed4391693510d9c69bb57ffddeffd8ddafec8e7`，父提交为完整基线 `871cc4b6b2c21420307a002bf5b983707720fe90`。开始补核时 HEAD 为该 SHA、工作树干净；以下六项是该提交相对父提交的全部改动，直接从 Git 对象读取的 blob、字节数及 SHA-256 均与 `publication-r1`／最终文档检查记录相符，且当时工作树逐字一致。

|固定发布文件|Git blob|
|---|---|
|`docs/PLAN.md`|`93a8997ee6ab8f499d9d48145fce3946009b7f63`|
|`docs/delivery/2026-11-15-domain-review-optimization-quality-review.md`|`9a5fd0ad01246ab00c6643f23bc28e9a71a76a42`|
|`docs/delivery/2026-11-15-domain-review-optimization-quality.md`|`3c1affdd88d1110eedb5c40e97eb53cde7196ae9`|
|`docs/plans/2026-11-15-domain-review-optimization-quality.md`|`c45f9d67eb4ac9c282421aefcace3a50701afc19`|
|`docs/research/2026-11-15-iterative-optimization-architecture.md`|`b024d7b0db53a0f073307c221ae3998924882be1`|
|`docs/research/2026-11-15-pr-mr-review-tools.md`|`87c68c201f90dc0186d16b24f88f1bc101f155dd`|

与 `review-scope-r1` 五份作者文档逐字比较：两份研究不变；PLAN、Q 计划和交付只更新本地完成状态、独立报告链接及终核记账，未改设计或后续验收合同。发布中的本报告是已核的 6,127B 版本，SHA-256 `437ef8b624e6d2dfef2f542f3e506a5cad05fc95eb831e54add28bef843bc287`，包含“三份声明的父／叶资料”措辞修正；本补核段落是其后的记录。自身模板原结果仍为前述 `d74aec37…`，未用后续记账替换原调用输入或结果。

独立读取固定六份文档并规范化相对路径后，159 个本地目标、其中 7 个简单标题 fragment、116 个引用定义及空白检查无误；107 处外部 URL 仅统计，未重复抓取。`git diff 871cc4b6b2c21420307a002bf5b983707720fe90 7ed4391693510d9c69bb57ffddeffd8ddafec8e7 --check` exit 0，包含全部新增文件；`src / tests / scripts / pyproject.toml / .github` 与基线差异仍为空。

普通 push 原件记录 exit 0；本次另执行 `git ls-remote --exit-code origin refs/heads/refactor/architecture-foundations`，exit 0，完整 Ref 返回上述 `7ed4391693510d9c69bb57ffddeffd8ddafec8e7`，与保存的远端读取原件相符。固定提交的原 Portability workflow 未改：分支匹配 `refactor/**`，六条路径全部命中 push 的 `paths-ignore: docs/**.md`。本补核仅确认忽略规则适用，不声称出现或通过新的产品 CI，也未借旧 CI 为此 SHA 背书；没有触发未变产品的全量测试。

**固定发布的需求符合性／可维护性两轴仍为 approve；实质 finding 0、开放阻断 0。** 此次只补核精确发布、文档范围与记录，不扩大为 Q1–Q6 或真实 B3 验收。后续同片发布身份和最终状态的例行同步，仍按仓库 AGENTS 的记账例外处理，不递归建立新审查。
