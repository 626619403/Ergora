# 持续演进调研独立审查

## 审查身份、范围与基准

- 日期：2026-10-28；审查者：`evolution_review`，使用新上下文，未继承作者讨论或预设结论。先阅读原始要求与交付文件，再阅读作者交付记录。
- 原始要求：调研可用于整体架构和 agent 持续改进、长期保存信息、持续优化 skill、主动探索新资料的 RSI 工具；相邻要求包含复用现有格式、接入现成项目、各层真实工具可调与 all-in-one。此切片的验收对象是调研与设计，非新功能实现。
- 本轮完整阅读：[持续演进调研](../research/2026-10-28-continuous-evolution.md)、[来源索引](../research/2026-10-28-evolution-sources.json)、[交付记录](2026-10-28-rsi.md)、README 全文（修改范围为初审第 277 行新增段落）。另完整阅读 CONTEXT 与相邻多 agent 主调研，仅检查设计一致性，不重新验收前一切片。
- Git 基准：无本地提交，README、CONTEXT 和 docs 均为 untracked，无法用跟踪 diff 证明段落以外未变；本审查使用明确范围与全文、内容摘要界定输入。

|初审文件|SHA256|
|---|---|
|`docs/research/2026-10-28-continuous-evolution.md`|`0cae6a1d2265d792354267367f2dff877e45aa3c24d5ab3e8bd5360daf28bba2`|
|`docs/research/2026-10-28-evolution-sources.json`|`3a522374290b70b827b2c71553a3160fda86abc551eec5c818e0f5712d3c48c6`|
|`docs/delivery/2026-10-28-rsi.md`|`3687b86bb16d9d892af9109ab0aa9bb163fae0a7e9f42c717cd2d3042d3aefde`|
|`README.md`|`3f540e309b22eba3e77598ea74c2942634c539380a338387a8fe40490f2e10c2`|

## 初审判定

**需求符合性：通过（调研切片）。** 文档分别覆盖记忆、skill/context、协作配置、代码/架构和权重；对“是否应该接入”给出明确的分步建议、现成工具选择和验收证据。没有把资料摘要、候选生成或上游成绩冒充本项目能力提高，也没有宣称无限或稳定的自主进化。实现和运行验证明确留待后续切片。

**可维护性：通过，附一项 P3 非阻断澄清。** 推荐先比较文件记忆基线与一个 ReMe 候选，再做一个 skill 的 GEPA 比较、一个主题的研究，规模与当前阶段相称。复用 Agent Skills 格式、现有 Temporal 控制和项目任务，未要求另建通用 skill DSL、工单或完整运行平台。原始证据、派生记忆、正式规则及生命周期的归属清楚。

没有阻断项；下列事实表述建议在调研定稿前修正。

## Findings（按严重度）

### F1 · P3：说明 Letta 与 Letta Code 已共用现行实现

- **位置：** `docs/research/2026-10-28-continuous-evolution.md:54`，关联第 26、82 行及 `README.md:277` 的数量说明。
- **证据与复现：** 读取索引中 `letta` 的官方 README。其开头明确写道 “The current source code lives in letta-ai/letta-code”；Historical source 部分把 archive 分支称为 “retired Letta V1 API server”。本审查独立重取该 URL，HTTP 200，SHA256 与索引 `67ec50661bb95db1839101863f08eaaa3cae3f2cc804adb2250a058393e56417` 一致。初审时报告只以“具体 coding harness 见下表 Letta Code”描述两者关系。
- **影响：** 读者筛选有状态平台与 coding harness 时，可能把同一现行运行实现视为两个独立接入候选，或误把历史 V1 服务当作当前推荐。24 份仓库 README 的获取数量本身成立，但不应隐含有 24 套独立现行实现。
- **最小修正：** 在 Letta 行说明现行源码已迁至 Letta Code、旧 V1 服务为历史分支；保留两个资料入口时，数量描述明确包含同一现行实现的两个入口。无需改变 ReMe / GEPA / Temporal 的验证优先级。
- **状态：** 已修正并通过定点复核，见下文最终判定。

## 实际核查与证据

1. 标准库 Python 解析来源索引并与原始响应缓存索引比较，两者相同；35 份成功响应的原始字节数和 SHA256 全部独立重算匹配；保留的一次 DGM 404 与随后取得的正确仓库、官方文章一致。
2. 独立联网重取 Agent Skills 规范、ReMe README、GEPA README、Temporal Schedule、Letta README、Sakana DGM 官方文章六个公开 URL；全部 HTTP 200，响应字节数和 SHA256 均与本轮快照一致。没有执行抓取内容。
3. 完整阅读 ReMe README、Codex 集成文档及 Agent Skills 规范；核对默认 BM25、可选 embedding、异步捕获与落盘确认、hooks 信任、单一整理调度所有者、`proactive_read` 的非联网边界，以及 `allowed-tools` 的实验状态。重要结论有对应原文，未误称接上 MCP 即完成跨会话记忆。
4. 阅读 GEPA 优化接口、反思/变异/Pareto 选择与 adapter 部分，并提取官方 skill 学习案例、MLflow 文档、Temporal Schedule 正文。MLflow `optimize_prompts` 的 >= 3.5.0 要求、skill 案例存在性、Schedule 暂停不停止已启动执行均得到支持；没有据上游案例认定 Ergora 已取得收益。
5. 抽查其他候选中影响选择的表述：Mem0 托管 benchmark 与 OSS 区别，Graphiti 自备数据库/模型/服务，Cognee 本地模式下载模型，MemOS 部署形态，memU 的宿主/系统矩阵，OpenViking 的组件许可及附加表述，Letta Code 的记忆/skill/调度组合，Agent Lightning v1.0 的训练组件；未发现除 F1 外足以改变本轮优先建议的矛盾。
6. 只读核对 v2.2 参考源码的 `search.py`、`portable.py`、`contracts.py`、`workflow.py`、`executor.py`、训练 CLI/执行器、`service.py`、`adapter.py` 与 `perfctl.py` 的相关定义和调用路径。搜索为 LangGraph + SQLite 的 1–5 个提案；编译器固定六阶段、工作单元 DAG 可调；当前实现与独立审查用 Codex；训练入口逐实验手动调用，未发现报告将这些能力写成常驻研究或通用知识库。
7. 设计层面检查：记忆有项目范围、来源与纠正/删除传播、并发和恢复要求；skill 以完整目录版本绑定，优化反馈集与最终保留集分开，预算、失败/超时、成对比较、人工采用和回退均有归属；核心变更采用版本、兼容/迁移/恢复及独立审查。共享 Unix 用户下摘要/文件不提供强隔离已明确说明，未来可信 evaluator 的边界未被写成当前已实现保证。

## 限制与后续验收

- 本次仅写入此审查记录；未安装候选、运行模型或训练、启动服务或后台任务、修改源码、提交或推送。
- 没有进行候选运行、性能/成本 benchmark、许可证或安全审计、Mermaid 渲染。部分外部原文按相关段落抽查，六个 URL 之外未逐一重新联网获取；快照为可变 HEAD/latest，内容摘要不等于上游固定发布版本。
- 作者记录的联合九份 Markdown 链接/格式扫描及主调研示例解析属于作者证据，本审查没有将其记作独立重跑的运行验收。
- 本审查通过不代表 ReMe 项目隔离、跨会话自动捕获、GEPA 泛化收益、研究调度取消或回退已经可用。后续仍按调研第 9 节，用实际任务和独立证据分别验收。

## 定点复审与最终判定

2026-10-28，复审作者针对 F1 的最小修正：

|复审输入|SHA256|
|---|---|
|持续演进调研|`517e7cc574475d504864d15cbc759d39226ed21eeb1839997ce0bbf706130c78`|
|README|`c15e222d2ef0cd17dad3360c9537a5f7e44b1eaf2c9dad56c68f4b0c38b650fa`|
|来源索引（未变）|`3a522374290b70b827b2c71553a3160fda86abc551eec5c818e0f5712d3c48c6`|
|交付记录（复审读取时）|`c6d7af137b511dd053e666ab96ce7e0c242762be5af484dde68fefb92198460e`|

- 报告第 54 行已明确现行源码迁往 Letta Code、V1 API server 退役；第 26 行说明 24 为资料入口数量，两行不作为独立候选；README 第 277 行改为 24 份项目官方 README。均符合上游原文，F1 关闭。
- 用内存中的反向替换恢复初审三行，得到的报告及 README 摘要分别与初审完全一致，确认研究报告只改了上述两行、README 只改了一行，未扩大设计范围。完整阅读更新后的交付记录，初审发现与修正均有记录。
- 独立重跑受影响文档的静态检查：三表 9 / 9 / 6 行；研究报告 30 个外部引用；报告、README、交付记录和本审查记录合计 13 个本地文件引用均存在（同页锚点单独跳过）；代码围栏数为偶数、无行尾空白、未命中检查的个人绝对路径或常见凭据值模式。此检查不构成 Markdown 渲染或安全审计。

**最终需求符合性：通过。最终可维护性：通过。无未解决 findings、无阻断项。** 结论仅适用于上述调研及最小措辞修正；候选接入和持续演进的实际效果仍需后续实现切片验收。
