# 多 agent 工具调研独立审查

- 切片：`2026-10-28-landscape`；审查日期：2026-10-28。
- Reviewer：`landscape_review`，新建独立上下文，未参与交付写作；按 `review-pr` 进行分轮审查。
- 审查范围：调研报告、来源索引、`CONTEXT.md`、本切片交付记录及 README 新增段落；只写本报告。
- RSI 持续演进调研及后来新增的 README RSI 入口属于后续独立切片，不纳入本报告的完成性判断。

## Findings

### [Low，已关闭] 补充 SWE-agent 已有官方后继推荐，避免新接入选择沿用旧重点

- 位置：[比较表 SWE-agent 行](../research/2026-10-28-multi-agent-landscape.md#32-编码执行器协作平台与仓库自动化)，审查时第 57 行。
- 初审证据：该行曾将 SWE-agent 表述为任务执行候选和基准参照，但未注明官方维护方向。已取得的 [SWE-agent 官方 README](https://github.com/SWE-agent/SWE-agent) 第 20–24 行明确写有 “Most of our current development effort is on mini-swe-agent”“which has superseded SWE-agent” 及 “use mini-SWE-agent instead of SWE-agent going forward”。对应来源为 `sources.json:318` 的 `swe-agent`，缓存 README 的 SHA256 与记录一致。
- 影响：读者筛选新的执行后端时，容易遗漏官方推荐的后继项目；这是当前状态信息缺口，不影响现有 SWE-agent 可作为研究与历史基准参照的描述。
- 最小修正：在原行补充开发重点已转向 mini-swe-agent、官方建议后续优先使用后者；若将后者纳入正式候选，再取得其官方资料并更新来源索引。可将两者作为同一代表家族处理，避免无意改变 40 家族计数。不要转述官方性能对比为本项目实测结论。
- 修正与复核：第 57 行已合并 SWE-agent / mini-swe-agent，补全开发重点转移和官方推荐；新增 [mini-swe-agent 官方 README](https://github.com/SWE-agent/mini-swe-agent) 来源。原 SWE-agent README 第 20–24 行及新增 README 第 83–96 行支持该判断；新来源原文摘要与字节数核验一致，未引入性能实测结论。**定点复核通过，finding 已关闭**；初审置信度：99%。

未发现 Critical、High 或 Medium findings；最终无未关闭 findings、无阻断项。

## 分项结论

|维度|结论|依据|
|---|---|---|
|需求符合性|**PASS**|覆盖现有实现与定位、关系格式选择、Ergora 相对定位、分层工具替换、已有项目直接集成及 all-in-one 体验；唯一维护方向缺口已补全并经定点复核关闭。|
|可维护性|**PASS**|建议沿用四类合同和现有适配边界，先迁入当前路径、验收一个第二后端，再增加安装组合与界面；没有要求首版同时实现完整 DSL、全部候选、第二生命周期或多个 UI。|

核对后的主要判断：

- 报告第 3、179、204、268、302 行清楚区分当前实现与设计草案，没有虚构新 CLI、YAML binding、安装 profile、Agent Spec 转换、新后端或 GUI 已存在。
- 第 88–157 行把 JSON/YAML 语法、Schema 校验、领域语义及协议职责分开；四类关系区分控制流、委派、证据和决策权。Agent Spec 采用受支持子集、拒绝语义丢失，兼容既有冻结合同的方向合理。
- 第 163–206、210–235 行分开模型、harness、控制流、tracker、通信、观测和训练执行；实际复用与参考、桥接、暂缓分别给出验收点。未将后端声明能力等同兼容性已验证。
- 第 239–251 行把优势限定为待验证的定位方向，承认成熟项目的重叠能力和 Ergora 的缺口，没有把 README 宣传转成比较测试结果。
- 第 255–298 行允许统一产品入口，同时保留一个正式生命周期拥有者；图形页面先观察与审批，再配置和受约束编辑。不要求首版引入 AG-UI、完整 Agent Spec runtime 或完整通用工作流引擎，未见需要阻断的不必要复杂度或内部矛盾。
- `CONTEXT.md` 仅包含任务、角色、工作单元、策略、绑定、证据和人工审批等领域术语与关系，没有混入安装路径、库选择、阶段计划或执行日志。

## 初审实际核验

目标 Git 仓库无初始提交，交付文件为未跟踪状态。本次直接读取完整正文，未用空 tracked diff 代替审查。

|对象|初审快照 SHA256|
|---|---|
|`docs/research/2026-10-28-multi-agent-landscape.md`，302 行|`b0d6c614931bbba51966a8c8e933a097f797c6ca8c679ca13e8a08964bf2704c`|
|`docs/research/2026-10-28-sources.json`，871 行|`da635705f6a87af8806a33bc3496cd9fcde27c75ac78aaba533f9bc910b5d0cf`|
|`CONTEXT.md`，40 行|`8a9bd4212d1637f32d899ab1f9f2453374c3f91d81acdbf31b1b72f62480ce6c`|
|`README.md`，281 行|`33be252316bb7617c9e85e85bc34279de3f34fdca107b8f8983eba8c5c2decc4`|
|`docs/delivery/2026-10-28-landscape.md`，43 行|`2ce33d5d75557b2c863fc5956149033c674a431741c011e2df72421199090492`|

以下为初审检查记录；修正后的数量和摘要见后续定点复核：

1. **PASS**：三组比较表分别为 18、14、8 行，共 40 个代表家族；没有宣称穷尽市场。逐项核对官方来源入口，并抽核官方缓存的定位与能力描述，重点复读 AutoGen 归档、Vibe Kanban sunsetting、ADK 2.0、ChatDev 2.0、Agno、Pydantic AI、Agent Orchestrator、OpenHands、Open SWE 及相关许可说明；发现 SWE-agent 状态缺口如上。
2. **PASS**：来源 JSON 可解析，76 个唯一来源 ID、72 项取得内容、4 项失败，日期一致。两处无正文跳转入口明确标注不可作为能力证据；Agent Spec 许可获取失败及 API 限流有记录，未宣称取得完整许可。
3. **PASS（有界）**：72 项取得内容均有缓存；46 项原文缓存的 SHA256 与索引一致。其余 26 项缓存为提取后的文本，与原始 HTTP 响应摘要不同，本次没有重新获取原始响应，不能声称其原始响应摘要已独立重算验证。
4. **PASS**：报告 69 个外部链接引用均对应已取得的官方来源；对 GitHub/raw、官方 Markdown/HTML 视图及记录中的重定向作了等价映射。7 处本地文件链接均存在。此检查证明来源对应关系，不证明链接今后持续可用。
5. **PASS（仅语法）**：JSON 节选经 `json.loads` 解析；概念 YAML 经 `yaml.safe_load` 解析。未用其证明新配置可执行，也未验证未来 YAML 加载器的重复键、标签或 JSON 值域约束。
6. **PASS**：本切片文件的代码围栏配对、行尾空白、个人绝对路径及常见私钥/token 模式静态扫描未见问题；该模式扫描不是安全审计。`git diff --check` 通过；未跟踪正文另外检查。
7. **PASS**：移除 README 唯一新增的调研/术语段落后，重建摘要为前一切片基准 `db2ae19a4d31a296f33a98824b134b7e81b2ae072541c4a3b1cfeecbbcc18b90`。HTML 摘要仍为 `775490e0caea48abd95be04a6f635605edbb8f01b7a2061ccb82ebd5453b0551`。前一切片 25 条 CLI 参数核验未在本次重复执行。
8. **PASS（源码静态对照）**：读取参考实现的 `contracts.py`、`portable.py`、`adapter.py`、`workflow.py`、真实 binding 示例，以及本地 `cli.py`、`executor.py`、`process_job.py`、`sandbox.py`、`training.py`、`search.py` 相关路径。确认固定六阶段、DAG/路径所有权、四对象冻结摘要、固定 runtime/协议、独立 ephemeral Codex 会话、审查变化检测、取消未知结果对账、手动精确 manifest 训练及仅提案搜索，与报告的当前能力边界相符。

## 定点复核与最终快照

本轮仅复核唯一 Low 的修正、新增来源和受影响计数。初审需求符合性为 PASS WITH NIT；本次已提升为 PASS，可维护性维持 PASS。没有安装、运行候选工具、调用模型或重新执行开发/训练任务。

|对象|复核时快照 SHA256|
|---|---|
|`docs/research/2026-10-28-multi-agent-landscape.md`，302 行|`f51832421b0b279c96f3caadf9fe91699148fe42e4ce680dd776c293dbaf9419`|
|`docs/research/2026-10-28-sources.json`，883 行|`9df5e6d4310929e552a5f75e9e6adc464cf8ff3cee8c58dfbe3e797f5b984b1c`|
|`docs/delivery/2026-10-28-landscape.md`，49 行|`9e7f662e77374fd5fe6e1f2066040af98d2700139a760da76c35f6a099b6ee63`；之后回收审查状态属于记录维护。|

- **PASS**：直接复读两份官方 README 的推荐上下文，修正表述准确；新增来源 `mini-swe-agent` 的 SHA256 为 `9982d90b7566f2f3fa5e9811b475d5e8e2a84e2df80cf3f1e4be6e820b129835`，11,106 字节，均与本地原文一致。
- **PASS**：把调研报告的比较行和 README 来源计数还原为初审文本后，摘要重新等于初审 `b0d6c614931bbba51966a8c8e933a097f797c6ca8c679ca13e8a08964bf2704c`；报告其余正文未变。
- **PASS**：工具项目 README 计数为 36；三表仍为 18 / 14 / 8，共 40 家族。来源索引为 77 个唯一 ID、73 项成功、4 项失败；补入来源没有改变未实测、许可缺口或可变文档快照的边界。
- **PASS**：报告 70 个外部引用全部映射到已取得官方来源。报告 3 处相对文件链接及交付记录 1 处审查链接均存在；本轮没有把后续 RSI 入口计入本切片核验。
- **PASS（仅语法）**：JSON 与 YAML 片段再次解析通过；修正报告及交付记录的围栏配对、空白、个人绝对路径及常见私钥/token 模式检查通过，来源索引空白与个人路径检查通过。`git diff --check` 通过，未跟踪正文另行检查。新配置可执行性和后端运行验收仍未实施。

## 范围限制

本次为文档及设计审查。没有安装或运行候选工具、启动服务、调用模型、执行训练、做统一性能比较、浏览器测试或端到端验收，也未提交、推送或修改运行平台。外部资料为访问时的官方 `HEAD`/`latest`，不是固定上游 commit；已取得资料及本轮抽核不足以认证各产品全部能力、商业可用性或安全性。

报告提出的新 binding、Agent Spec 映射、后端替换、统一安装与 GUI 仍需后续实现和真实任务验收。现有源码的静态追踪不能替代取消竞态、重启恢复、权限边界和错误证据拒绝的运行证据。RSI 新增文档和索引不在本轮审查范围。
