# U1/U2 日常安装与入口旅程独立验收

评审者：fresh-context 独立 reviewer agent `specialist_installation_review`；日期：2026-11-12。仅接收原始要求、固定身份及证据位置，未继承实现对话。产品基线与本轮产品均为 `5ab6d350024de8515487d0bedb3b950be60ac867`；文档基线为 `c38227747b002ba4137f65a4982de51ce247773e`，检查点为 `42902bbe1af59059b287a38f0c9efa51a72dca4b`。核过 Git 状态与差异，本轮没有产品、测试或 CI 变更；研究文档及其动态进度不在本评审实现范围。

**Spec：通过，开放 finding 0。Standards：通过，开放 finding 0。** 结论限于安装身份、备份可恢复材料、实际 CLI、静态组合与叶输入准入、正式例子编译和本地 HTTP 入口。没有阻塞 finding，也没有本范围内尚缺的验收证据。

已读 `AGENTS.md`、[PLAN](../PLAN.md)、[本片计划](../plans/2026-11-12-specialist-template-refresh.md)、[交付记录](2026-11-12-specialist-template-refresh.md)，以及 maintainable-project-delivery 的独立评审要求。私有原件根为 `.ergora/checks/specialist-template-refresh/local-upgrade/`；检查了 `before.json`、前后分发清单、`state-location.json`、`backup.json`、安装 stdout/stderr、`after-identity.json`、`accept_daily.py`，以及 `journey-r1/` 中全部 43 条 operations 与对应 stdout/stderr、三个 preset 的 manifest/input/资源、两份编译结果、10 份 HTTP 正文及其清单、server 输出和隔离状态库。`summary.json` 仅作为检查项投影，没有直接采用其 `passed` 作判词。

安装身份由只读重算确认：日常 launcher 的链接目标与解释器保持；452 个安装产品文件逐字等于固定产品提交及原 H1 wheel，安装 RECORD 的 462 行均核过存在性、大小和声明摘要，实际 38 项分发与升级后清单一致。wheel 自身为 457 行 RECORD，未混为安装 RECORD。版本仍为 `0.2.0`，验收身份依赖精确提交与文件内容。

旧环境归档实际为 32,657,016 字节、5,572 成员，SHA256 重算为 `cde8320bc5d49ac8345e9d4e1756bf2598173b588d6343cffbfc1e547a0d3f6f`，与备份原件一致；成员统一位于 `venv`，无绝对路径或父级越界成员。只检查归档元数据和摘要，未恢复或抽取内容。原默认用户状态在升级前记录为不存在，复核时仍不存在；备份及验收材料均持久保存在 home。记录中的回退顺序为停止相关进程、保留并移开新环境、恢复整个旧环境，足以定位原件和恢复目标；未做破坏性的回退演练。

43 条原命令均退出 0，全部 stderr 为空，累计命令时间重算为 22.21 秒。三个 preset 的首次与重复导入原 JSON 完全相同，均不授权执行。评审从包内固定定义递归重建预期节点，再逐叶核对结构祖先资源的来源、原始全文、资源树摘要和 prompt 字节；结果如下。

|preset|实例／叶|祖先资源来源数|manifest／input 文件数|所选叶完整输入字节|
|---|---:|---:|---:|---:|
|repository-governance|16／5|23|31／33|3,984|
|large-change|19／7|31|37／39|4,000|
|training-optimization|9／4|15|22／24|3,370|

三个 preview 的 canonical SHA、两个目录各自的完整树摘要、全部资源与原包逐字对应、所选 task/prompt 摘要均独立重算吻合。完整继承覆盖表中的全部 16 个叶；实际准入仅覆盖每个 preset 选中的一个只读叶，各执行 `text-only` 与 `task-mcp` 两种模式。六份原准入的输入身份、资源列表、Codex binding、显式回退理由、模式和非授权标志一致；准入政策明确未探测 CLI 登录、模型容量及实际 SDK 兼容性，不能称模型调用成功或双后端成功。

三个冻结模板副本与包内原件逐字一致，新增的 `agent-contract.json` 与 bootstrap 返回合同一致。原 `reference verify` 的 283 文件结果另由逐文件 SHA256 重算确认。治理与大型变更两个正式例子使用安装包内原编译器，输入来自安装包、输出位于独立验收目录；原 stdout 均为 `VALIDATED_ONLY`。两份 compiled envelope 的输入分项、profile、request 和整体 canonical SHA 均与原输出吻合，`task_type` 正确，未把训练提案当成正式开发合同。

真实 `serve` 的原日志对应 10 次 GET 200；10 份正文大小及 SHA256 全部重算吻合。入口 HTML 与安装包一致，其直接引用的四件静态资源齐全且逐字一致；bootstrap 仅显示隔离项目，preset 响应与 CLI 目录一致，agent 库、安装配置和 OpenAPI 均有原响应。server 原日志包含同一进程的启动与正常结束，复核时原 PID 已不存在、原端口无监听；隔离 SQLite 以只读方式检查，仅 `projects` 表有一条记录，`agent_runs` 及其余运行表为空，Git 夹具干净。原命令与已核调用链只写隔离验收状态和夹具，没有 SaaS 业务写或主分支合并。

Standards 检查覆盖私有验收脚本的结构、复用和检查必要性，并对照实际所有者：`workflow_definitions.py:39` 的原导入、`:158`／`:266` 的祖先材料与权限遍历、`:380`／`:408` 的完整输入与快照验证、`agent_runs.py:73`／`:132` 的只读准入、CLI 的原路由、`reference.py:35`／`:204` 的冻结核验与原编译器，以及 `web.py:268` 起的本地页面与 GET 路由。脚本使用局部 command/cli/http 记录辅助函数和原产品 API，没有增加生产抽象、第二状态账本或自制编译器。重复导入、全材料验证、模式准入、正文摘要和进程清理分别保护可达的安装或交付边界；未发现需要删除的冗余 test/CI。私有 launcher 固定值承担本机实际入口定位，未进入公开产品接口。

证据定位摘要：`accept_daily.py` SHA256 为 `6c2509ee5a5d5e74ec5564d119da508588877308e939b7ace5a75eaa3090a823`；`operations.jsonl` 为 `47417a7f9686e60eb918b5e4921e61ef39950f3d20ba5a9bebff991cc9af9d79`；`http.jsonl` 为 `274cbed04a6902ef0dfff154d20a652c6b0d8b14065dbeeb0653b572727300ad`。原 H1 wheel SHA256 为 `8da7a263f4c2dbd8b826796bdf09d8664d8dc773328906992c1c7d16912674b9`。

本评审没有重跑安装、完整旅程、测试、模型或网络请求。页面验收覆盖真实 HTTP 入口与直接静态资源，未运行浏览器交互矩阵、递归模块加载或用户编辑流程；未执行 workflow ports、六阶段、候选／审批恢复、训练实验、模型或 GPU，也未验收新专家模板及运行接口。旧项目和候选的保持结论依据本片隔离写入范围、未变化的产品身份及原备份，不宣称对机器全部历史数据做了全盘前后比较。H1 CI 属于原产品候选，不能据此授予新增模型、硬件或后续研究实现的通过结论。
