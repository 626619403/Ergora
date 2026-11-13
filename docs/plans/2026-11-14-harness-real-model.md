# F8-H2：真实模型与可替换只读调用

日期：2026-11-14。承接[原 H2](2026-11-12-harness-admission.md)，复用已交付的 DeepSeek Harness SDK／runtime `0.2.2rc2` 适配。与 C2.1 源身份维护独立验收；没有修改已冻结的 Forge 或参考发行。

## 验收步骤

1. 固定当前 noneditable 产品、SDK／runtime、解释器和私有 inference 配置身份。读取现有环境中的 API key 引用，不在公开资料或日志打印值。
2. 用已有公开 `agent_runs.run_input(binding_override=...)` 对原结构审查模板的相同 prepared input 调用真实模型，禁工具模式，240 秒预算，无自动重试。与实际 Codex 结果比较输入／材料和原候选身份；不以两个 backend 名称推定底层模型不同。
3. 用一个现有专家只读叶执行真实 task-MCP 调用；冻结完整 Skill 附件，逐页核全部资源及尾部、原事件／结果、实际工具表和进程终态。模型读取成功证明传输，不能证明 GPU 或任务效果。
4. 汇总实际成功、失败、预算和未验范围，运行适当静态检查；用自身审查模板及新 fresh-context 需求／可维护性两轴核查。行为未改时沿用原 H1 的固定 SDK 失败／停止回归，不重复当作本轮新测试。
5. 普通提交／推送当前开发分支并核远端 Ref；若发现实际兼容缺陷，先给最小复现和具体 source diff，再验修正候选。自己的 CI 与产品变化分别记账。

本片不接入新调度器、不创建会话账本、不将 ephemeral SDK session 声称为可恢复交互。native／workspace 模式、OpenHands 受限准入和 H3 持久会话仍由所属计划负责。网关若不支持现有 wire protocol，保留原失败，不悄悄改 endpoint／权限或放宽结果校验。

## 进度

- 固定可选环境的只读检查已通过：SDK／runtime 都是 `0.2.2rc2`，Python 3.12.11；没有模型请求。
- 首次真实调用使用与 Codex 审查完全相同的 input，20.712 秒明确失败：网关拒绝 Chat Completions，原生 finish_reason=error，适配没有接受 exit 0 为成功。
- 已核原 H0 固定源码的 pi-ai provider 原本支持 `openai-completions` 与 `openai-responses`。既有 component binding schema 已增可选 `api` 枚举，由原 driver 消费；缺省保持 completions，显式选择 responses，不自动重试／换 endpoint。不改 SDK、模板格式、上层编排或工具权限。单字段直通不另建参数镜像测试；沿用原合同 suite 并以真实请求验差异。
- 新 noneditable wheel 的 551 产品／源与安装、两 RECORD 及 283 冻结文件通过；现有三个受影响 suite 38 通过／19.21 秒。显式 Responses 的第二真实 run 成功，45.849 秒，原 input／prompt 与 Codex 完全一致，原结构化结果为 approve；这次不涉及工具，也不作为新 H2 代码的自身审查。
- 原随包 `optimization-kernel` 的 `root/analysis/design` 真实 task-MCP run 45.695 秒成功；六资源 16,774B 的随包→冻结输入→scope→原生工具正文逐字一致，连续 UTF8 页均读到尾部，实际仅 list／read。六个按 PID／starttime 观察的进程已无存活；不是全局隔离证明。没有 workload／测量／GPU 或整个图自动执行。
- 三次真实调用的离线原件审计已通过；两次私有审计驱动的 stdin 假设／事件字段错误及修正保留，产品与原模型调用未重跑。新自身原结构模板 29.628 秒 approve，五全文 64,066B 和三份继承资源均在实际 input／stdin；采用已授权 Codex 回退，保留前片 Claude 超时理由，不声称异模型成功。
- [新 fresh-context 需求／结构两轴](../delivery/2026-11-14-harness-real-model-review.md)通过，开放 0／0；手册过期状态 SP1／P3 只改原句并复核关闭，产品未变。本地验收出口完成；最终快照、普通发布和自己的 CI 待核，不借 C2 或 H1 的结果。

原件在本项目私有检查目录，结果写[本片交付](../delivery/2026-11-14-harness-real-model.md)。
