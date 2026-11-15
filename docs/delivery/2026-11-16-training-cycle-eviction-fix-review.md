# c1c 取消 eviction 修补独立源码审查

2026-11-16。审查者为 fresh-context 独立 reviewer `cycle_eviction_fix_review`；按 `maintainable-project-delivery` 与 `ergora-codebase-quality` 执行。授权范围为只读源码、测试与既存原件，以及写本审查；没有修改产品／测试、安装包或既存证据，没有启动服务、runner、网络、测试或提交。

**需求结论：approve；可维护性结论：approve；本片源码阻断 finding 0／开放 finding 0。** 结论仅覆盖下述 r4→r5 两文件修补。它没有认证 r5 新安装、真实 Worker／S-H 收尾、完整 c1c 验收或 8 MiB 实际边界。

## 审查身份和边界

已读项目根、源码及测试 AGENTS、主树 `docs/PLAN.md`、[首轮设计](../plans/2026-11-16-training-cycle-workflow-first-round.md)、组件协议的执行／证据与脚本／检查部分，以及[诊断](2026-11-16-training-cycle-eviction-diagnosis.md)与[修补交付](2026-11-16-training-cycle-eviction-fix.md)。产品专树 HEAD 为 `fa78747d6c6ca62935fe6a44aa6db143c362baad`；`git status` 只有 worker 与 runtime 测试两文件修改。专树三份 AGENTS 与主树逐字同一。

|精确输入|r4 SHA256|r5 SHA256|
|---|---|---|
|`src/ergora/reference_training_worker.py`|`187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`|`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`|
|`tests/test_training_runtime.py`|`56f67f74aadbe8a0db53fd3ea7df22f9b2865327c104d8533871753e29c1e6a1`|`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`|

r4 worker 从原非 editable SDK 安装读取，r4 测试从该安装验收冻结输入读取；独立重算上述四个 SHA，并直接比较两版本。r5 产品仅 `_ordinary` 第 1276 行的 `WAIT_CANCELLATION_COMPLETED → TRY_CANCEL`；测试仅第 757 行起新增一个 Core replay 节点。相对 Git HEAD 的其它变化属于已存在 r4，不把整份未提交 diff 冒充本次新增。

## 需求轴核对

- **停止立即排队和唯一机会保留。** `_ordinary` 仍通过 `workflow.wait_condition` 等待，run 取消可以先到停止出口；`_stop:1482` 只请求普通 handle 取消，没有等待其 ack，随后仍用原正 `D_total-N` 调唯一 `cycle-stop` 到独立 queue。stop 的 WAIT、shield、最大 attempt1、重复取消循环保持。没有新增普通派发路径，也没有复位 start/request 的已调度标志或 observation count。
- **提前完成本地 handle 没有接管资源清理。** `_CycleOperation.run:196` 的独立 `_run` task、取消后的 `request_stop` 和反复 shield 等待保持；`_run:121` 继续持有 S 的 spawn／pipe／wait，直到真实 drain/reap。start 的 `_CycleCandidate.run:389` 同样持有 `_run`；未交接 root 在 `discard_root` 等实际 handle，已交接 root 仍由原预算／执行 owner 负责。done callback 仅提取 SDK handle 的失败，不能充当 S/H ownership 或停止证明。
- **Worker 收尾层仍在。** `_serve_cycle:1726` 按 normal、stop 顺序等每个真实 Worker `run` 结束；核过 SDK 1.34.0 `_worker.py` 的关闭路径，它仍等待 activity worker 的 `wait_all_completed`，后者等实际活动 task。因而 normal 仍在清理时 stop 容量保留，TRY_CANCEL 不让普通活动 Python task 从 SDK 的活动表中提前消失。这是源码机制结论，实际新现场的阻塞清理仍需单独验证。
- **预算、权限和旧链保持。** SDK command 的 schedule/start timeout、绝对 work/total 收窄、activity source 验证、原 H 最后 gate、一次 publication 和原 reaper均无变化。`training_execution_protocol.source_capability/validate_sources` 仍 pin 包含 worker 在内的 gate source；新字节不能续用旧 owner 授权。离线 history replay 不调用实际 Activity；旧 `ExecutionRecords` 观察入口保持只读语义，没有因本修补升级 schema／刷新 source pin。query 的 cycle durable stop／drain／executor 确认仍为 null，CANCELLED 不被提升成业务停止成功。

## 回归接缝与可维护性轴

新增测试构造固定 23-event history，含 cold 完成、普通 start 已调度、Workflow cancel、stop 完成和 Workflow CANCELED；普通 start 没有 cancellation ack。`Replayer(workflows=[create_cycle_workflow()])` 使用正式类和默认 sandbox，真实 Core 处理 cancellation_type 后产生本地 resolve 与 eviction。测试既没有读取待测枚举决定结果，也没有手填普通取消 resolve；因此能区分旧 WAIT 与 TRY_CANCEL，而不是在 harness 中复述实现。

新增局部 history 构造函数只服务此接缝，留在现有 runtime 测试文件，没有生产单 caller 抽象、新框架或重复 fixture 文件。固定 queue、活动 ID、time 与 Core flags 表达这份版本化历史；`1098` 对应 fixture 的 total1100、cold 调度时刻0、取消时刻2，不把默认值变成生产约束。输出 marker、exit code 和无 eviction 错误分别核对 await 确实返回、解释器结束及未残留该症状，未发现须删的产品 guard／重复控制流。

子进程使用 argv、`sys.executable -I -B` 与实际 `training.__file__` 推导的导入根，没有 shell 拼接；history 用 `tmp_path`，control_home 继承现有 fixture 的平台 anchor。这个 replay 子进程不启动 Activity/S/H 或新的 OS 后代；`subprocess.run(timeout=10)` 的超时路径杀掉并等待其直接子进程，保留 stdout/stderr。没有发现新增 Windows 路径写法或孤儿子进程问题。10 秒是测试故障有界等待，不能当产品预算或 Windows 实测证据；Windows 未运行。

## 已核证据与剩余验收

本 reviewer 只读核实 ignored `cw1/eviction-fix/` 下的 `red-result.json`、原始 red stdout、最终 result/stdout/JUnit、前后 freeze 和原 history replay 结果：

1. 同一个新增测试在 r4 worker 上先红：1 failed／11.46秒；10秒 child timeout 同时含精确 `Eviction processed, but 1 tasks remain` 与 pending `start.v1`，没有把任意超时冒称根因复现。
2. r5 最终冻结为853输入，前后 manifest 相等，当前两文件 SHA 与该冻结相等。既存原始 stdout 为26 passed／27 deselected／5.55秒，JUnit 对应21 activation＋4 SDK lifecycle＋1 Core replay。此处是审计既存执行记录，没有再执行这些测试；4 lifecycle 项仍含替身 poller，不能充当实际 S/H 清理。
3. 独立重算原 W7 完整 history SHA 为 `5e1dda7daabad517fac30ce9abaad47c2875488d229499ed1af996c25131bb40`。既存 r5 源码回放结果为1.745秒／exit0／`REPLAY_COMPLETED`，无 eviction 症状。这是旧 SDK 解释器显式导入新源码，不能称新安装通过。
4. 本 reviewer 执行的 `git diff --check` 通过；没有扩大 suite 或改动原证据。原 W7 SDK 计量8,139,050B仍低于8MiB，JSON 10,995,598B不能补足该验收。

没有需修改这两个文件的 substantiated finding。主控须继续按新字节完成新非 editable 包／实际导入身份、真实 pending normal＋cancel＋独立stop＋有序 Worker shutdown、S/H及后代／reaper实际wait、完整history回放和自身模板审查，分别记录；这些未验项阻止将本源码 approve 写成完整产品验收。

文档接续已同片核实：主控已纠正首轮设计“独立停止”第1点并追加“r5 SDK取消策略的实施纠正”；当前设计 SHA256 为 `3d8c61e215a24a96a4ab0630a0179d5ab12fcb52cf072997f954a9b5c8d741cb`，原设计 `d01d5774d592e21178cdabc2a918a61c7ba7f32a673daf6ac321849b28a8dbcb` 身份明确保留。更新准确区分 ordinary TRY_CANCEL 的本地等待、原资源 owner 的实际清理和 stop WAIT／shield，保留 once／deadline／source 合同及旧失败范围，诊断／修补链接有效；未追认新包或现场通过。此记账建议已解决，本 reviewer 未代改计划或他人交付。主控另报新 wheel／安装身份核验在推进，本审查没有读取或认证该新增安装证据。
