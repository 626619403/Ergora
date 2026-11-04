# F4.3a：原运行待批计划的有界读取

日期：2026-11-04。状态：设计与调用链已核，尚未实现。前置为[F4.2c真实组合旅程](2026-11-04-task-console-journeys.md)；该片仍待独立收口。本片只提供后续页面需要的只读材料，不发批准信号。

## 已核现状与目标

当前status只返回原run的phase/plan SHA，完整计划文本仍位于可信executor产物。原生workflow用整个plan receipt的canonical SHA作为待批plan SHA；它并非execution-plan文本的文件摘要。现有approve已经要求原提交run/spec/memo、当前待批phase与精确plan SHA，不能用页面重算的文本摘要代替。

本片增加同源`task plan` CLI和GET任务plan API，要求明确run ID、plan SHA和1–60秒预算。沿已有统一创建/提交所有者和原生运行连接核原run/spec/memo，再查询实际AWAITING_PLAN_APPROVAL及所选摘要；流式读取原history前缀，定位plan的dev_submit context及job ID。用原请求envelope、原plan receipt的canonical SHA和当前待批摘要核身份，只读取该receipt中被冻结profile声明为plan材料的文本；不把其他日志带入页面。

## 范围与所有权

- 在既有任务用例、CLI/Web和reference边界接入口；计划审阅归已有`reference_task_approval.py`，复用`_Submission.submitted/lookup_run`、`_Creation`安全路径/有界JSON、原SDK分页及converter，不新增第二套receipt校验器、状态机、通用资产服务或依赖。
- 每份计划文本最多256 KiB，使用已有no-follow/常规文件/有界read原语；摘要与实际UTF-8文本一致才返回，总响应最多1 MiB。超限、缺材料、损坏、错误run/plan、网络失败明确拒绝，不以部分文本或空字符串装作完整审阅材料。后续F5负责通用证据索引，F4.4负责日志/观察分页。
- 所有读取不保留SQLite写锁、不创建decision/owner receipt、不调用authorize/approve/cancel、不变更原运行或产物。返回只是读取时的身份快照；后续批准仍由既有服务端再次核当前计划。
- 同步更新公开使用说明及架构。F4.3b再把材料与批准/原decision恢复接到页面，F4.3c接取消/外部清理，F4.3d接精确候选导出；本片不提前声明这些页面行为完成。

## 验收清单

1. 先按原合同覆盖history前缀/分页、严格receipt/job/spec身份、文本摘要/UTF-8/大小与安全路径、实际错误phase和网络失败；纯输入/内容分支使用轻量fixture，必要进程和CLI/API再用现有真实原生边界，避免每个轻量反例重复完整安装。
2. 原审批/运行合同及架构边界定向回归；新非editable包逐项核源码/wheel/两安装及283冻结reference。不为纯复用代码机械增加镜像断言。
3. 对F4.2c两条真实等待run只读核CLI/API材料等于已保存原artifact及待批SHA，保护该片54文件与零signal；在新独立目录或受控传输中验证错误/缺失/超限，不篡改这两任务来制造反例。
4. 完成最小完整实现/本地验证并记账后，新的fresh-context审查者检查正确性、所有权、复用、必要守卫及有界成本。修正后再提交推送、核精确两OS CI和远端，最后更新完成状态。

私有运行材料使用本片独立checks目录；前置组合旅程保留自己的脚本、快照和独立结论。完整F4仍待F4.3剩余操作及F4.4综合出口。
