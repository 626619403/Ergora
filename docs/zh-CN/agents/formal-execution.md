# 可选的正式六阶段执行桥接

简体中文 · [English](../../agents/formal-execution.md) · [文档目录](../../README.zh-CN.md)

默认`agentflow`执行器保持v2.2行为。要使项目的角色选择作用于正式任务，先按参考手册安装、配置模型和可信执行边界，再用[统一项目注册](../../projects/registration.md)一次登记Git根、角色、模板与可信检查，并运行`ergora reference executor --project PROJECT_ID`。旧的两次注册方式继续兼容，两个同名项目必须指向相同Git根。只对新任务启用；不要中途切换已开始的参考任务。

已有reference项目可用`ergora project import-reference import.json --revision N`预览，审阅差异和文件身份后加`--apply --preview-sha256 SHA`显式采用。它保持兼容旧文件原字节，保存前后项目与来源记录；不搬迁在途任务或导入模型密钥。详细spec和恢复命令见[项目定义手册](../../projects/registration.md#explicit-import-of-an-existing-registration)。

先停止原 executor，保留 Temporal、worker 等服务：

```bash
"$HOME/multi-agent-platform/.venv/bin/supervisorctl" \
  -c "$HOME/.config/multi-agent-platform/supervisord.ini" stop executor
ergora reference executor --installation "$HOME/multi-agent-platform"
```

该命令在前台监听原 FileAdapter 队列，使用同一 executor 锁，保留原任务创建、审批、取消、恢复和导出命令。也可加 `--request /ABSOLUTE/PATH/envelope.json` 精确处理一个已发布信封。执行器校验参考 Python 源码身份，拒绝未经适配的版本。

新任务首次处理时将角色工具与项目修订写入原任务持久目录的 `agent-bindings.json`；恢复继续用这份选择。实现者和审查者使用不同角色身份、新会话、精确候选提交及原有工作区变化检测。正式阶段结束前清理并回收其派生进程，再执行原监控的只读变化检查；精确使用参考配置的 Codex 可执行路径。未知外部进程结果继续由参考监控对账；缺少能力、结果结构错误、命令失败或只读阶段改动都不能通过。Agent 的 `model-log` 和 `agent-selection` 附在原回执证据中。

桥接的模型阶段会核验本任务保存的 `compiled.json` 与stage合同，从该快照加载完整模板说明，并将说明摘要记入 `agent-selection`。快照缺失、被改或属于另一任务时明确失败；不会改用活动包。已有任务不因源包删除而换说明，安装profile本身漂移仍按原规则拒绝。此行为属于Ergora桥接；直接 `agentflow` 入口保留原v2.2行为。

统一入口的[外部证据查询](../../development/evidence-and-export.md#check-external-job-evidence-for-a-closed-run)将原run完整历史中的dev_submit与可信FileAdapter请求/回执逐项对应。每个已知job即使请求丢失仍保留为未决；没有正确fence、存在额外请求/孤立回执、无效回执或产物摘要错误时不会报告外部已确认。只读查询不修改原outcome、不发布fence、不释放租约，外部终止证据和六阶段质量结果分别保留。 正常REVIEW_READY也不会因workflow闭合自动释放租约：导出沿原规则处理，暂不导出时使用[正常任务关闭流程](../../development/run-and-recover.md#close-after-normal-task-completion)。需要写入fence和释放精确原claim时，显式使用[reconcile/reconciliation/resume-reconcile](../../development/run-and-recover.md#explicitly-reconcile-terminal-state-and-release-issue-leases)；它保存原outcome与独立清理evidence，原CANCEL_UNCONFIRMED保持，缺证据不释放。

原v7来源任务导出精确候选后，可按[候选评论说明](../../projects/candidate-actions.md#post-an-issue-comment-for-an-exported-candidate)准备并确认GitHub／GitLab中性评论；该操作单独保存意图及原生收据，复用原任务身份，不改变Agent后端、批准或导出结果。GitHub的[原生ID标签追加](../../projects/candidate-actions.md#add-a-github-label-for-an-exported-candidate)复用同一回写生命周期；GitLab标签动作明确unsupported，选择tracker不会隐式改变Agent授权。

新记录还保存`configuration`有效绑定视图，含每层来源、校验结果、项目修订和内容摘要；`ergora project config PROJECT_ID`可查看当前值。旧任务没有此附加字段时仍使用原绑定快照，不重建历史配置。视图范围与独立调用的上下文区别见[有效绑定与运行快照](../../agents/configuration.md#effective-bindings-and-run-snapshots)。

统一注册项目需要长期运行时，优先用`ergora services start PROJECT temporal worker executor a2a --revision N`管理所选栈，不必手改ini。以下仅适用于保留原Supervisor的旧部署：在 `~/.config/multi-agent-platform/supervisor.d/executor.ini` 中把该 program 的 `command` 改为 Ergora 可执行文件绝对路径、`reference executor --installation ...`，保留 stopasgroup/killasgroup。再用 supervisorctl `reread` / `update`。初始化参考发行可能重新生成该文件，升级后应核对。不要同时运行新旧两个 executor。

桥接沿用参考配置中的 Codex TOML 和 API 变量。参考监控的凭据白名单不会传递任意 shell 变量；其他 provider 可使用工具自己的持久登录，或参考 `credentials.json` 的 0600 凭据映射。模板、项目绑定与仓库中只保存凭据变量名/元数据。独立调用的活动 Skill/记忆选项不会自动改写正式任务的上下文。
