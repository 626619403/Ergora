# F3.3c1：原运行的精确计划批准

日期：2026-11-03。分支`refactor/architecture-foundations`，源码基线`d47e97b172c425b2400465593dae6916f225c30d`。当前已实现、定向/完整发行回归和独立源码审查通过；精确两OS CI及最终独立核对尚待完成，不标整个F3完成。原始需求和c2取消边界见[决策设计](2026-11-03-task-decisions.md)。

## 行为与所有权

CLI/API共用`tasks.approve / approval / resume_approve`，只接受统一入口创建且有原提交回执的任务。操作者必须明确当前项目修订、原run ID、当前plan SHA、稳定decision ID和确认。相同decision ID不更新计划或自动续期；重复命令只读本地记录。新owner决策必须使用新的ID。

`reference_task_approval`是原生审批操作的专用进程边界：复用创建/提交所有者、原严格spec/memo校验、原`adapter.publish`和`approve_plan`信号。没有新依赖、第二套授权器或工作流状态机。`reference._task_operation`由提交和批准两个真实消费者共享完整运行时/进程生命周期；`_Submission.lookup_run`由提交恢复和批准使用，返回实际SDK converter，避免把spec专用校验用于信号解码。

保存的意图固定project/control/registration、creation/submission摘要、原spec/run、精确plan、owner actor、稳定receipt ID和24小时expiry。意图、attempt、result在执行目录`ergora/task-approvals/TASK_ID/DECISION_ID.*.json`；原公开owner回执在`approvals/owner-UUID.json`，与原任务/提交记录一同备份。原授权activity继续判定有效、过期、撤销和权限，投递回执不替代授权。

## 修订保留、信号和恢复

1. 在当前控制库revision保留中，无网络准备意图；原同任务锁采用非阻塞获取，任务忙时立即失败，不持全库锁等待远程操作。
2. 释放控制库写保留后，仅持原任务锁执行网络阶段。先核原run/spec/memo，再query原`AWAITING_PLAN_APPROVAL`和plan SHA；校验原owner和expiry后，发布原回执、保存attempt、发原signal、保存结果。
3. 阶段间中断为`prepared`；明确resume重用原意图/receipt。已保存attempt时为`unknown`，resume只能分页读取原run history，按精确request/plan/receipt payload核对后补投递回执，绝不重发signal。NOT_FOUND、RPC/超时或找不到信号仍保留原未知决策。
4. `requested`仅说明信号投递得到SDK应答或在原history找到对应事件；`approval_accepted: null`和`execution_success: null`保留。query与signal之间的phase变化不虚称批准被采纳。实际采用和执行结果通过原任务状态/授权证据确认。

history按100事件一页流式消费，受总timeout约束，不将全历史加载为列表。网络预算1–60秒，父进程另留5秒启动/回收，本地安装/合同预检另计；准备和网络阶段分别有预算。只读本地审批记录仍通过所登记完整Linux参考解释器，以复用原workflow身份；Windows明确使用WSL2。

## 当前验收证据与剩余工作

- 首轮源码定向：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_task_approval.py tests/test_task_submission.py tests/test_task_runtime.py tests/test_architecture_boundaries.py`，105 passed、1个FastAPI测试客户端弃用警告，356.06秒；日志`.ergora/checks/f3-task-approval/source-first.log`。此后增加了NOT_FOUND明确错误与恢复反例，需新检查，不混用首轮身份。
- 夹具只替代网络SDK、外部doctor依赖和定点文件中断，原准入/Transport/信号handler实际调用；覆盖重复/中断/丢响应/旧plan/owner/expiry/撤销/phase竞争及CLI/API严格输入。受控connect等待3秒时其他项目可写，同任务prepare立即拒绝。不是实际Temporal或模型验收，不推导吞吐改善。
- NOT_FOUND补充定向7 passed、29 deselected（38.87秒），`source-not-found.log`；首次查询缺原run保留prepared，未知恢复缺原run保留相同unknown意图且不重发，随后原run可查询时沿原history补回执。fresh-context审查已启动，尚无审查结论。
- 待：补充定向、自查与fresh-context结构/性能审计；最终非editable包/两安装及冻结283文件身份；基础控制面两模板CLI/API旅程、延迟与history边界；适用完整回归、精确两OS CI、最终独立核对、提交推送。
- F3.3b长控制库锁仍待F3.3d迁移，不能因新批准入口已分段而声称旧提交已修。c2取消及F3.4真实两模板六阶段/导出、原history/memo和重启旅程分别验收。


## 候选发行与限定性能验证

当前候选wheel SHA256 `0532122914082e995568df20396182a45e9109f2b11d046d6016da86b588b7e6`，344文件×源码/wheel/开发与基础两安装一致，冻结283文件通过。开发环境Python3.11.15含SDK，基础环境Python3.12.11仅必需依赖、无FastAPI/Temporal/GEPA。初次尝试用3.11建新基础环境时离线缓存仅有cp312的PyYAML wheel，明确安装失败；随后仅清空该新目录并用3.12重建，离线安装成功，不影响既有用户环境。原始build.log、package-identity.json及安装目录均在`.ergora/checks/f3-task-approval/`。

无SDK基础控制面两模板旅程共86次CLI通过（journey-performance.py/json/log）。注册/预览/创建和本地重复路径使用实际发行命令；首次start/approve及丢应答history恢复使用受控SDK和原Transport/handler。每模板重复approval/approve/resume-approve各10次，全程无RPC或重发，原任务与操作文件字节不变；每模板另一个decision的丢应答保留unknown，再精确history恢复、总计两个signal，不把重复命令当新决策。

本地重复路径中位毫秒：governance为1102.05 / 1112.50 / 1125.52，large-change为1092.35 / 1195.15 / 1103.52，最大1672.15。包含CLI/子进程/SDK导入和合同预检，且并行完整回归；仅描述此条件下本地投递记录读取成本，不是网络/模型性能或优化收益。

独立隔离目录的实际共享SQLite/任务锁探针（lock-contention.py/json/log）：受控connect延迟18秒、审批预算25秒时，其他项目真实写入14.70ms完成；同任务第二个prepare在804.22ms内明确拒绝，随后其他项目仍可再次写到revision3；两者都在原远程结果前完成，总19641.55ms。没有真实RPC/模型。该结果证明新审批两阶段不持全库锁等网络，**不证明旧B提交的长锁限制已修复**；后者仍由F3.3d处理。

修改文档261个本地链接目标均存在（docs-links.json），git diff --check通过。当前独立审查和适用完整发行回归进行中；精确CI、最终独立核对及提交推送尚未完成。


## 独立源码审查

fresh-context审查者`f3_task_approval_review`已完成[独立报告](2026-11-03-task-approval-review.md)，所检c1需求符合性和结构/可维护性通过，无确认finding或待修阻塞。审查者独立6项源码定向通过（39.60秒），并使用真实SDK1.34的handle、分页iterator、converter及protobuf，仅替换内存history RPC，完成第3页精确匹配、3页不匹配、第二页UNAVAILABLE和总超时四个探针。后三种均不写投递回执，unknown不转回派发。

审查者已分别核对作者344文件×两安装/冻结283、86CLI旅程与18秒延迟锁探针，未将它们冒充独立执行或真实服务验收。当前9个源码/测试文件聚合SHA256为`d106eef37092ffcc58da083309104d8e7fac0dad622fa36a5e68f3642a9f25a2`（candidate-source-identity.json），未在审查后修改生产代码。最终发行回归、精确CI、远端和独立最终核对待完成。


## 完整发行回归

最终053212…候选wheel的适用Linux完整回归通过：**477 passed、19 skipped、36 subtests passed、1个FastAPI客户端弃用警告，566.19秒**，原始wheel-regression.log；命令与CI一致地增加原合同、portable、AdapterTests和runtime套件，PYTHONPATH只指向原reference平台，不指向src/ergora，实际应用来自非editable安装。完整回归没有失败，未扩张真实服务/模型结论。

源码审查后9项源码/测试聚合身份未变。将提交推送该已验证候选以触发精确两OSCI，并请原审查者分别核对最终本地证据和精确提交/CI/远端；此处尚未宣称最终完成。下一切片c2的原cancel已核接口及稳定request ID设计保存在[决策设计](2026-11-03-task-decisions.md#f33c2下一切片的已核接口)，尚未写c2生产代码。
