# F3.3c2：固定原运行的取消请求与投递对账

日期：2026-11-03。设计基线`b3b7d655fe4a61ecfe6bc77258c9b8f416b5424b`，分支`refactor/architecture-foundations`。当前为c1之后的工作区实现记录，生产代码尚未随c1收口文档发布；已实现、首轮源码联合检查进行中；尚无本段独立审查或发行验收结论。依赖c1原运行所有权和两阶段意图边界；c1已推送、精确两OS CI41572513289通过，最终独立CI/远端核对进行中。

## 原行为、目标与范围

已读原`DevelopmentTransport.cancel`、`DevelopmentWorkflow.request_cancel`和参考CLI：原cancel校验非空且最多1000字符的原因，固定run核spec，仅在RUNNING时发协作取消signal，闭合run返回None。原CLI统一返回cancel_requested，不能直接用于新入口区分“实际发信号”与“已闭合无操作”。原handler接受request/reason并忽略额外字段；前置实际探针已确认附加操作SHA兼容，见[决策设计](2026-11-03-task-decisions.md)。

新入口保持原Transport.cancel、handler、fence及lease所有权，不terminate工作流，不删除ledger，不把Temporal闭合或signal应答写成外部进程已停。仅接受统一创建且已保存原提交回执的任务。必须明确当前项目revision、原run、原因、稳定request ID和确认；本地用户actor固定在意图中。没有第二套调度/授权器、DB表或配置版本。

## 预定接口与状态

- `task cancel PROJECT TASK_ID --request-id ID --revision N --run-id RUN_ID --reason TEXT --confirm --timeout 20`。
- `task cancellation PROJECT TASK_ID ID`只读本地记录；`task resume-cancel PROJECT TASK_ID ID --revision N --intent-sha256 SHA --confirm --timeout 20`按原意图恢复。
- GET/POST `.../tasks/TASK_ID/cancellations/REQUEST_ID`和POST同路径`/resume`，CLI/API共用tasks，严格修订/确认/timeout，沿原同源保护。
- `not_recorded / prepared / unknown / requested / already_closed`。requested仅投递事实；already_closed明确没有新信号。`cancellation_confirmed: null / execution_success: null`保持，不推导真实停机。变更CLI在requested或already_closed时返回0，其余非零；HTTP200也须检查状态。

## 意图、原生复用与恢复

1. 当前revision保留及非阻塞原任务锁中仅保存不可变意图：control/project/registration、creation/submission/spec、原workflow/run、request ID、原因及actor。记录在执行状态目录`ergora/task-cancellations/TASK_ID/REQUEST_ID.{intent,attempt,result}.json`。
2. 释放全库写保留后，仅持原任务锁调用原Transport.cancel。专用窄边界复用提交所有者的严格spec/memo/run查询，识别原cancel是否实际调用signal；只在该调用前保存attempt，并在原payload附加`ergora_operation_sha256`绑定完整意图。信号应答后写投递回执；没有信号调用的闭合run保存明确无操作回执。
3. 同ID重复只读，不更改原因/actor、不再次派发。prepared显式resume可重查原run后继续原cancel；unknown只按原run分页history匹配本次完整payload，再补history回执。NOT_FOUND、历史不可用、不匹配或超时不重发、不改ID绕过未知。
4. 同样的严格原提交读取与精确信号分页算法在c1/c2有真实复用时归入现有提交/查询所有者；两种操作的owner回执、expiry和闭合语义保留差异。无需通用Agent/Workflow基类，不让取消继承具体审批业务。

## 可验收节点

- running发一次原signal；closed/COMPLETED/FAILED等不发并明确无操作；原handler保留原因，所有权spec/memo不符、错误run、非统一/未提交任务、原因/确认/修订非法拒绝。
- intent、attempt、signal和result前后中断；重复/丢应答/父响应丢失及并发不重发未知；闭合回执无attempt是明确受支持分支。unknown只能匹配操作SHA相同的原history，单纯相同reason不足以认领。
- 使用原Transport/handler、真实SDK分页的受控网络端口；18秒远程等待期间跨项目真实写入可及时完成，同任务prepare非阻塞失败。CANCEL_UNCONFIRMED/NEEDS_RECONCILIATION事实仍由status/fence暴露。
- 原c1投递恢复及b提交/状态回归不变；非editable包/两安装/冻结283、基础两模板CLI/API旅程、限定性能、适用完整回归和精确两OSCI分别记录；新的fresh-context结构/性能审计、最终独立核对和提交推送后才完成。
- 实际服务停机、原history/六阶段/导出/重启仍由F3.4综合验收；本段fixture不推导模型/GPU或实际终止结果。旧b提交锁迁移仍由F3.3d独立处理。


## 已实现与当前验证

本段新增`reference_task_cancellation`专用原生journal/进程边界，`reference.task_cancellation`使用既有完整运行时子进程生命周期。CLI/API共用`tasks.cancel / cancellation / resume_cancel`。原`DevelopmentTransport.cancel`仍实际调用，局部`RecordedCancellation.lookup`在原lookup后核memo归属，并仅包装实际signal以附加意图SHA和保存attempt；保留原RUNNING判断及原handler，不复制取消算法。已闭合结果单独记not_sent，结果有意不要求attempt；反之投递回执必须有原检查点。

真实复用：原提交的`submitted()`负责c1/c2必须有原提交回执的共同读取；`verify_run_owner()`供原lookup和取消的原Transport查询验证同一memo；`reference_task_runtime.find_signal_event()`由c1/c2共用精确payload流式history匹配。`tasks._decision_prepare`集中当前revision、严格确认/预算和本地准备事务，仅由两种决定的实际用例调用。两种journal各自保留审批expiry/owner回执、取消closed/no-signal语义。Web恢复正文共用`TaskResumeDecisionPayload`，字段不变；OpenAPI内部组件名从Approval归入Decision。

联合源码检查命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_task_cancellation.py tests/test_task_approval.py tests/test_task_submission.py tests/test_task_runtime.py tests/test_architecture_boundaries.py
```

原始输出`.ergora/checks/f3-task-cancellation/source-first.log`，当前仍运行，无最终结果。开发安装仍为c1 wheel；本命令明确使用src验证c2。夹具实际调用原Transport.cancel和request_cancel handler，只替换网络/doctor外部依赖及定点文件失败；覆盖六种闭合状态、闭合回执写中断、已提交/原run/spec/memo、未知精确操作SHA、丢应答、不重发和CLI/API。不是实际服务/外部作业停机验证。公开手册、当前架构图已按此接口同步，git diff --check通过。

待首轮结论及反例补核后，开展新的fresh-context结构/性能审计，再构建最终包、基础两模板旅程/18秒延迟并发和限定性能、完整发行回归/精确两OSCI，分别独立核对、更新计划并提交推送。
