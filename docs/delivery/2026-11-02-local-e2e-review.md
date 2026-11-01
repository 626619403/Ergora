# L0：本地环境与 CLI 全流程独立审查

日期：2026-11-02。独立 fresh-context 审查；先读 `AGENTS.md`、总计划和 L0 原始验收，再检查完整差异、实现及实际证据，最后读取作者交付记录。使用 `review-pr` 技能，未委派其他审查者。

需求符合性：**在记录的适用本地范围内通过**。记录可维护性：**两处低等级修正后通过**。没有未解决的 findings。本结论不涵盖 L1 DeepSeek 调研、R4–R8 或未来 F/G 功能。

## 范围与发现处理

原要求是本地配置完整环境并由 Agent 使用命令行尽量跑通全流程；补充要求权限不足时继续可测项，并把后续 DeepSeek 工具调研列入计划。用户接受现有 Docker 作为可信执行边界，没有要求获取宿主机权限。

文档基线 `02911d0a00c10f624c3590d2cfff32680994c18e`，审查时 HEAD `78be765`，分支 `refactor/architecture-foundations`；运行源码仍为 `4fe2ec5133a9d055b35debf376e21d09d3df4ec9`。审查基线至工作区的全部五文件变化：`README.md`、`docs/USAGE.md`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md` 和 [L0 交付记录](2026-11-02-local-e2e.md)。没有本轮生产、测试代码修改或未跟踪实现。本审查仅新增本报告，没有安装、运行模型/GPU、启停服务、修改运行数据或提交推送。

两处记录问题均已由作者最小修正并重新读取确认：

|等级 / 位置|发现、证据与修正|
|---|---|
|Low，L0 记录第 8 行；已解决|原“29 个生产文件”没有持久化的选择清单，计数口径不可恢复。独立核对实际非 editable 安装：全部 321 个版本化包文件逐字节匹配源码，含 26 个 Python、6 个 JSON、6 个前端/许可资源及 283 个冻结参考文件；元数据版本 0.2.0、非 editable。作者已用这一明确集合替换原数字。|
|Low，L0 记录第 9 行及证据矩阵；已解决|原称路径均相对验收根，但多数日志只写 basename，直接按该规则无法定位。作者已明确无目录日志名位于 `logs/`，并补 `logs/evidence-index.json` 恢复入口。|

## 需求符合性与实际证据

下表私有证据路径均相对本机 `ERGORA_ACCEPTANCE_ROOT`。日志、原始模型文本、配置和凭据不进入公共报告。

|验收项|独立核对与结论|
|---|---|
|安装、持久环境与执行边界|安装日志记录非 editable wheel；实际包 321 文件全部匹配。冻结 manifest 的 283 文件全部匹配，干净参考运行目录对应的 279 个 platform 文件全部匹配；工具 venv/二进制复用由 symlink 指向确认。doctor 明确是当前容器、同 Unix 用户执行，未宣称 Agent 之间有文件系统强隔离。旧部署的 `setup.py` 差异被保留，正式任务采用干净源码，未以关闭身份检查放行。|
|控制面与真实 Codex|`logs/control-journey.json` 对应 20 次实际 CLI 回执，覆盖记忆修订/恢复/删除及 Skill 评价/采用/导出/回退。实际 SQLite 和运行目录保留 smoke run `90802e949e264338bb0b31af1a47bad2`；其 JSONL 有完成的真实 shell 调用、usage，状态 succeeded、退出码 0。上下文探针 `dd03a5f74b8d4a67a999762d3fed29eb` 的归档 stdin/stdout 摘要相等，含回退后的活动 Skill 和项目记忆。确定性 evaluator/proposer 只证明协议与预算闭环。|
|搜索、资料、HTTP 和服务恢复|核对 GEPA 的真实引擎、1 proposal / 4 metric calls，及 LangGraph 原 ID 的相同 resume 结果。资料日志覆盖首次快照、未变去重、变更提案及审阅；调度记录保留暂停 Schedule 的显式 trigger、worker 重启后的同一排队结果及删除回执。服务验收实现和归档包含 Temporal 重启中的原值恢复、A2A 认证路由及 MLflow 写入。本审查只读 HTTP 再核对 bootstrap、公共 Agent Card、匿名 A2A 401 和两个现存 MLflow FINISHED run；没有重新触发这些运行。|
|两个开发模板|`acceptance-governance-r1` 的 7 份阶段回执与 `acceptance-large-r2` 的 6 份回执均成功；所有引用产物摘要匹配，可信 verify 绑定最终候选，review 为独立 Codex 会话。按合同重算两个 plan receipt 的 canonical SHA，与精确批准摘要一致。实际 Git 分支分别指向 `42903c458a3e3737ac1bb93b112fdd7591bc9afa` 和 `7f3dcaad10586f52fbfc52ac3b2dbbf10bd4f95e`；main 仍为 `f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`。`logs/export-revalidation.json` 保留独立 worktree 的 3/6 种可信检查和 4/8 个 unittest 结果。终态是 REVIEW_READY，未据此宣称合并或部署。|
|取消及沿原 ID 对账|原 `logs/cancel-result.json` 保留 CANCEL_UNCONFIRMED。相同任务的 monitor terminal 记载 cancellation fence，阶段回执为 CANCELLED，引用产物摘要有效；后续 `logs/cancel-journey.json` 保留同 ID、confirmed=true、无 unresolved jobs 的对账。源码的即时 fence 快照语义与该差异相符，没有把取消意图写成工作流停止成功；当前 CLI 缺少终态后对账入口已列入 R6/F3。|
|离线备份恢复|独立核对真实 manifest SHA `5f8a5fc68cba220d0eb4b9c8513626ee73e94f5f2f62ec8339ed7ba35fa8ad23` 及全部 78 个备份文件，均匹配。用 immutable/read-only SQLite 对照恢复目录、保留旧 home 和记录的原始行摘要：全部 16 表、schema version、4 个项目一致。该恢复只涵盖控制面 home。|

大型开发 r1 的 inventory 失败、BLOCKED 结果和已确认 fence 仍在原 ID 下。核对旧检查器与 v2 检查器，确认为基线误要求新功能后，以新注册项目和 r2 任务修正；没有覆盖失败或跳过可信检查。每工作单元执行全套项目检查的约束也已写明，没有把一个完整特性单元的验收扩大成任意拆分 DAG 都可运行。

## 训练证据的独立复核

`acceptance-gpu-sgd-r2` 基线 `1c962a74ab49e2eea1eb111e476e2824df167832`、候选 `dc485dbd5c70c942ca6a7062cdcc17bf1b99409d` 的 Git 差异仅在 `update.py`。读取实际 runner 和 measurement 代码，核对每臂独立阻塞子进程、20 次预热后重置、计时边界同步及计时外最终值摘要。

全部 16 条原始记录与 comparison input 的耗时/样本数一致，顺序 4AB/4BA，最终张量摘要均为 `bbafec13fd9a144ece5162b7246aafe9e4589dd3b0efed4dd01a70f720910809`，没有复用 r1 的原始记录。1 次/200 次逐位相等及 save/load 后下一更新相等的检查有实际执行断言和绑定的 PASS 产物。

在 CPU 上重新执行固定比较器，完整 JSON 与保存报告一致：每 200 次更新均值约 47.931 ms 和 3.049 ms。26 个 evidence 引用产物在运行输出和不可变归档中的 SHA 均匹配。manifest `01a0bca00f2dda029c9d3b5c8c88a8597241679ba484d55c12a925a24d40e877`、gate、独立 Codex run `5210683e7e5b4a188e3431538d1598bc`、MLflow run `29a08be4bf1c4e99a45e9822e148440a` 和集成复验票据身份一致。gate_passed=1、26 项 MLflow 指标可从现存服务读取。错误 evidence SHA 的拒绝回执、精确批准和同 ID 幂等回执均保留；最终是 INTEGRATION_TASK_CREATED，票据 `automatic_merge=false`。

r1 的真实测量和后来独立审查不改变其等待超时：原 result 仍 FAILED、无 gate，执行日志明确拒绝补齐过期运行。r2 使用新 manifest/ID、重新测量和新审查。批准均明确是用户授权下的隔离验收操作，未冒充真实业务人工签署。

这些证据只支持单 GPU 固定梯度的 SGD 更新微实验；没有完整训练、模型质量、收敛、P99、独占 GPU 或模型 Skill 收益结论。

## 记录可维护性与复核边界

`logs/evidence-index.json` 的 SHA 为 `42e9a78f5595ccb1b5159e03503ee1960a84080e56e86bccefab9cc51f4e9b52`；索引列出的 19 份日志字节数/摘要和 17 份 operator 脚本摘要全部匹配。读取辅助脚本的具体断言，并进一步核对原生回执、归档、Git 候选、SQL 行和原始数值，未仅接受汇总布尔值或作者叙述。五份文档的 105 个相对文件链接目标存在，`git diff --check` 通过；新增 Temporal shell 配置与连接实现的 loopback 限制一致。

本次只读 Supervisor 状态确认 executor、console 及基础服务运行，research-worker、source-docs、training-worker 停止；本轮相关端口均监听 loopback。没有重跑模型、GPU、服务重启、取消或恢复，未重跑全量测试。生产代码没有变化，现有阶段测试/CI 仍以各原交付身份为准。

HTTP 证据不替代浏览器交互；A2A 仅验服务/认证路由；备份不联合恢复 Temporal、MLflow、业务仓库或外部服务。ReMe、真实 GitHub/GitLab 工单、mini/ForgeKernel 的真实模型效果、空白系统、Windows 本地部署及完整训练质量仍按作者记录保留未验状态。取消对账入口、环境配置所有者和 Supervisor 停止反馈已登记后续节点。提交、推送与远端 SHA 核对由作者在本审查后收口，本报告不代替该交付动作。
