# W1 真实参考源码试用独立审查

日期：2026-11-14。审查者为新 fresh-context 独立 agent `workload_source_trial_review`，未继承作者实现对话。按项目 AGENTS 和 maintainable-project-delivery 独立审查说明，先读原始要求、固定材料及实际调用，再读作者交付。本次只写本报告与被忽略的私有审查记录，没有启动模型、测试 suite、安装、外部查询或业务执行。

|审查轴|判词|开放发现|
|---|---|---|
|需求符合性|通过，限于 W1 的真实源码只读调用、资料继承、原结果交接和诚实报告|0|
|可维护性|通过，未发现本片引入产品职责、执行 owner 或业务耦合的实证问题|0|

基线与审查时 HEAD 均为 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`。作者三文件快照 manifest SHA256 为 `d21a8821d8a1938b0f561a5396e88f5a00c1ff63b59a920cc8c0b860026af0d3`，逐项大小／SHA 已重算。范围为原 PLAN 的 W1 检查点及相邻 S1 发布状态、[W1 计划](../plans/2026-11-14-workload-source-trial.md)和[W1 交付](2026-11-14-workload-source-trial.md)；后两文件仍与快照逐字相同。S1 自有计划、交付和审查的发布附录属于旧片记账，本报告不代替其 CI 终核。

同片状态整理已补核：原 PLAN 52,782B、SHA `bb6b85c358365be9eac0e16557ae740e6312856976cf3e7dde138502b0f57764` 逐字保存为[完整归档](../PLAN-history-2026-11-14.md)，相对链接基址保持。[新 PLAN](../PLAN.md)重组为当前状态、开放验收及权威交付入口，保留 S1／W1 待收口、真实 B3／完整 C2 开放和全部祖先／权限规则；历史入口仍可到达，没有以整理状态替代原证据。新首页引用的 S1 CI 进展仍由 S1 原评审终核。

用户要求由 Ergora 测试真实参考材料，并继续开发 Ergora；参考项目不是本会话直接优化的业务工作区。原私有计划、驱动、三组 admission／封存 input／实际 stdin／原 result／原生 stdout 与 MCP audit，以及来源 capture 均已检查。独立核验脚本、逐 run 身份和人工对照记录保存于私有 W1 `independent-review-r1`，原项目身份、源码、内部服务与完整角色回复不进入本报告。

|独立核验|实证结果|
|---|---|
|包与产品身份|S1 noneditable wheel SHA `7cbf6594483b7197640b0be74a869ac05c811e014623cd7e5cb968dba9f6d8ab` 重算一致；561 产品文件在 wheel、安装、基线 Git 和当前源码逐字相同，两 RECORD 569／574 行及 283 冻结参考文件重算通过。本片无产品变更。|
|真实来源|十三份固定 Git 对象共 93,748B，逐份重算大小、SHA 并与原对象比较，commit／tree 一致。先前三十二次只读查询的 101 份留存原件也逐项重算通过；本次未重查外部平台。|
|三次实际调用|原 CLI／task-MCP 各运行一叶；design 142.704 秒、profile 138.210 秒、measurement 91.065 秒，均成功。三组 input 整树身份、request、prompt、实际 stdin、原 result 与回执吻合；prompt 分别为 105,039／104,994／132,730B，各含十三份完整源码。|
|完整继承与权限|每叶按 root→中间 workflow→Agent 的原定义逐项核资源，五份 inline 均进入实际 prompt，累计十五份。每叶七个固定资源全部列出并从 offset 0 读到 `next_offset:null`；原生响应字节与 scope、audit 一致，六份附件累计 12,954B。逐层 read／write／shell／network 未越父授权，实际工具仅固定 list／read。|
|完整交接|measurement 的实际 task／prompt／stdin 中有 design 和 profile 两份完整原 JSON，逐字匹配原 result SHA；没有以摘要替代。三次 run ID、原生 thread ID 和 State 记录互异，各只有一次原生 turn；原图端口没有自动执行。|

Agent、模板与后端的原定义未改。新诊断根复用既有 analysis v2／measurement v2；私有试用驱动消费原 prepare、run-input 和 task-MCP 接缝，没有成为第二套产品调度器或批准账本。measurement 定义仍选择 Claude，实际调用显式覆盖为 Codex，并保留既往 Claude 完整审查超时及用户授权的回退理由；三次均使用同一 Codex 模型、独立会话，不构成异后端成功证据。

人工通读三份原回复并对照全部十三份原材料后，未发现需要阻断本片的失实结论。配置默认值、更新／调度时钟、profiling 窗口和恢复身份的主要描述有源码依据；回复没有把缺少的 runtime、安装环境、调用点或资产绑定补成运行事实。依赖中的多个 optional extra 保持声明身份，未混成实际安装。profiling 配置适配和缺少调用链均保留为待核问题，没有宣布真实缺陷；输入准备、重计算与通信方向是有前提的调查建议，尚未证实瓶颈、正确性或收益。

measurement 的 `request-changes` 明确针对实验就绪度及测量结论：需要真实 workload、匹配测量、独立正确性／恢复／质量证据。它收到并审查了两份前驱，但没有称实验已失败，也没有批准实施、运行或采用。三份回复均要求原 runner 补原复现命令、环境与资产身份、受控变量、预算、独立检查、停止和回退条件；这些要求不会给当前只读叶增加执行权限。

观察范围仍有限。共享仓库 HEAD 和 213 条 status 的原字节在本次复核时仍与 capture 一致；这不是所有未提交文件内容的逐字认证，输入也没有使用共享 WIP。design／profile 各有运行时 MCP PID／starttime 样本和终态记录，本人复核时两 PID 均不存在；measurement 的 preflight／native 两个 audit PID 仅有终态不存在，缺少预先 starttime 样本。以上不证明所有未知后代或外部服务的全局清理。

原驱动每叶传入 240 秒超时，无 Ergora 自动重试路径；留存记录支持三次显式原生调用均在该界内完成，不证明提供方内部 HTTP 次数、token 或财务预算。完整资料和连续读取证明字节交付，不能保证模型理解或提供方上下文窗口；固定工具和只读后端请求也不构成宿主隔离。原生日志只显示固定资源调用，推理 HTTP、进程及 State 写入仍属于可信基础设施。

本片比例静态检查通过：原快照、新 PLAN／完整归档和本报告的本地链接可达，公开内容未发现私有项目标识、源码正文或内部服务，私有证据保持被 Git 忽略，`git diff --check` 通过。没有为无产品变化重复模型或昂贵回归。普通发布、精确提交和适用 CI 仍由原交付 owner 后续记账；S1 在途 CI 不作为 W1 模型或训练收益证明。真实 B3 的 workload、资产、设备／环境、预算、基线／候选、独立评价与原证据批准继续开放。
