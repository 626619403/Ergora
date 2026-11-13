# F8-H2 真实模型交付记录

日期：2026-11-14。按[本片计划](../plans/2026-11-14-harness-real-model.md)推进。复用现有 DeepSeek Harness 只读 backend、`agent_runs`、task-MCP 与进程 owner，不改 Forge／六阶段／原实验合同。

## 当前状态

独立可选环境 SDK／runtime `0.2.2rc2`、Python 3.12.11 的只读版本检查通过。第一真实调用的协议失败保留，显式 Responses 的新包、禁工具及 task-MCP 真实调用与原件全文链、自身结构审查及新 fresh-context 需求／结构两轴均已通过，开放 0／0；普通发布及自己的 CI 仍另验。原 H1 的 loopback／停止证据保持其原范围。源／安装、实际输入、网关身份与模型结果在本片私有原件中分别核定，不公开认证或机器路径。

## 首次真实调用与协议缺口

使用 C2.1 已验 noneditable 包，产品源码精确对应 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`；结构审查 input digest 为 `e17b82b80776bc3063f5ea21d4b40db87fbdbbd502e12f7bde5d1f23154eda4f`，prompt SHA256 `9e24abaede8d1c071f2f5f3156fec5ac72f48d4ee365de41a0a424c54b7c6949`，均与此前实际 Codex 输入完全相同。通过既有 `run_input(binding_override=...)` 选择 DeepSeek Harness，不改模板及资源。

原 run `14a00aa6ef10411abfc813627d9a08b7`，20.712 秒，`failed`。SDK 进程 exit 0，但原生 finish_reason=error、没有最终正文，原 Adapter 正确拒绝；请求 header 核实际 model 与输出上限，原 stream 返回 HTTP400／`byok_endpoint_not_supported`。这是固定 Chat Completions 路由与当前服务不匹配，不是完整模型兼容通过；没有自动重试、工具或 GPU 调用。

复用 H0 固定研究源码 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` 的 pi-ai config／provider 已核两个原生协议。已只增既有 backend 的可选 `api` 字段并由原 driver 消费；省略时保持 completions，不自动重试或换协议。新字段随既有 component 描述进入表单和校验，无须增加上层分派。原失败与原产品包保持，修改后的候选另建隔离安装与实际调用。

## 新候选与第二次真实调用

Python 3.11 noneditable wheel SHA256 `2aa9eda87f4f3629437bf4c718beebe1d7ba1d2ede10172c74289038f9496236`，551 产品与源／安装逐字相等，wheel／安装 RECORD 分别 559／564 项及 283 冻结文件通过。现有 `test_deepseek_backend`、`test_components`、`test_composition_invocations` 三 suite 安装版 38 通过，19.21 秒；没有为单字段直通新建实现镜像测试。

显式 `openai-responses` 的 run `98f01639cd584e46901ac33ed83070e2`，45.849 秒 `succeeded`。原 input digest 与 prompt SHA256 均保持上述身份，结构化原 result 为 approve，SHA256 `d07483a78b07d4efb5209a012c6c60fe98b0b09cf5145222ef0cc59272239812`。同一输入在 Codex 和 DSH 可替换调用已实证，但两者配置指向相同模型名，不能据 backend 不同声称模型家族多样性，也不能借原 C2.1 审查关闭新 H2 变更的自身审查。

原随包 kernel 方向的分析／设计叶另做 task-MCP 验收；不改其版本、权限、Skill 或父引用，不提供合成训练结果。无真实训练工作负载，不能由本片推出性能收益或完整原生优化流程通过。

## 真实 task-MCP 全文链

原根 `ergora-opt-kernel-proposal@1.0.0` 的 `root/analysis/design` run `9906124a37754963af7ffdb1f50bcf3b`，45.695 秒 `succeeded`；input digest `8b62c05827bd53c522bac7b5b5a759cbf1f6cd14b0e16fc59305231e1c0d0abb`，prompt SHA256 `dac0680a5d1137207d23ff2e4f0fe04025389c75f716f606b47e8992dbdd0d00`，原 result SHA256 `23f7c1da3d0045a0d5b33be8e0d9805c43d90fc5bdd6b76796e7ce90e81390c8`。它是设计者，结果合同无 reviewer decision；没有补造批准。

原生事件为 completed，实际一次 list 和六次 read，只有 `mcp__ergora_task__list`／`read`。六资源共 16,774B：原 kernel 根的 instructions／context、analysis 父 instructions、designer instructions／Skill 及 evidence-contract 附件。原安装包→manifest 输入→run snapshot→scope→原生工具正文逐字节一致，列举及每个连续 UTF8 读取均到 `next_offset:null`；三层祖先资料在实际 prompt 中保持。MCP 原收据完整摘要与仅 list／read 工具表已核，原生 replay metadata 证实显式 Responses。未搭 HTTP 代理，未声称捕获网关 wire bytes。

按 PID 与 starttime 采样该 worker 和后代共六进程，调用返回及事后核对均无采样身份存活。只证明这组六个观察身份，不推出全部短命进程或全局 OS 隔离。原生正文明确缺少 workload／baseline／硬件／独立正确性及时间结果，只给有限补证据方案；未运行 GPU、Forge 或整个 proposal 图。

三调用原件审计已通过；初版私有核查误套 Codex 的 stdin 相等假设，修正为 DSH 实际 request 文件／native user message 链后，又修正 `user/message` 事件字段路径。原错误及日志保留，不改产品、不重跑真实调用、不把驱动 exit 0 当模型成功。两次成功各按 native finish_reason、完整原结果及严格 schema 判定。

## 本片自身审查

新原随包结构模板 run `ac0ee870d8b24785b7e52edbc772d130`，29.628 秒成功／approve；完整 component 配置、driver、后端手册及当时两份本片记录共五全文 64,066B 与三份继承资源均在实际 input／stdin 中。input digest `da92d91716c5334afb179167f56f588c3fdb6b5f2132cb6950561f0d6e6111e1`，prompt SHA256 `81fa74810250489a37e85421c93dae97933b32b27327f920eceeb4113c62e444`，原 result SHA256 `93eec39ed3dfcb2e8aafadf7d0048a83369a6c4114f4680f8e31f8a38a896b04`。沿用户已授权 Codex 回退，前片 Claude 完整审查超时事实保留；不重用其先前成功判词、不声称异模型成功。

模型认为可选配置和默认兼容均留在原 owner，未增加冗余分派或实现镜像测试；明确其只审了完整提交材料，未通过工具独立读取私有执行证据。新的 fresh-context 需求／可维护性两轴仍须核源／安装、实际原生回执及本片公开记录，未提前记通过。普通发布和自己的 CI 另记。

## 新独立两轴

[新 fresh-context 评审](2026-11-14-harness-real-model-review.md)已独立重算源／构建／wheel／安装 551 字节集合、两 RECORD、283、原 38 项测试、三次真实调用的实际 request／native user／通知／结果与六资源完整链，以及自身五文件输入和限定采样终态。需求／结构两轴通过，开放 0／0。

唯一 SP1／P3 是后端手册尚沿 H1 声称真实模型未验；已只更新该状态句，保留 H1 历史和新增 H2 的精确范围链接，明确六阶段／会话／其他平台未准入，独立补核关闭。两产品文件与原已验包及自身审查一致；未为文档状态更正重跑模型或 suite。最终候选、普通提交／推送和自己的 CI 另核，不借 C2 的 CI。
