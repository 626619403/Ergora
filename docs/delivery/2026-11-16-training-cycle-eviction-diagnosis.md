# 首轮 Workflow 的取消后缓存驱逐诊断

2026-11-16。真实现场的正式 `TrainingCycleWorkflow` 已到服务端 `CANCELED`，Worker 和离线 Replayer 却持续报告 `RuntimeError: Eviction processed, but 1 tasks remain`，残留为 `start.v1` 的普通 Activity handle。诊断已在原安装 SDK 1.34.0、默认 sandbox 下复现，并缩减到纯 SDK 场景；产品修补及新现场验收由后续实施片负责。本片没有改产品、测试、已安装包、Git、服务、网络或现场进程。

## 1. 身份与精确反馈环

权威原源码为专树 HEAD `fa78747d6c6ca62935fe6a44aa6db143c362baad` 加 r4 两文件未提交字节。诊断开始及结束核实：worker SHA256=`187bda497043f70512f2fa28e8c54403b2da1c493eafa2e804ae9304643bb09b`，runtime 测试=`56f67f74aadbe8a0db53fd3ea7df22f9b2865327c104d8533871753e29c1e6a1`；原安装 worker 与源码同一。私有副本保存 `source-identity.json` 与每项 `change.diff`。

真实导出 history SHA256=`5e1dda7daabad517fac30ce9abaad47c2875488d229499ed1af996c25131bb40`。最终采集文件为 361 事件／269 个 malformed signal、JSON 10,995,598 字节；服务端记录的最大 history size 为 8,139,050 字节，仍小于产品守界的 8,388,608 字节。交接早快照的 256 signal／7,738,810 字节属于更早时点，不覆盖最终原件；JSON 序列化大小也不能替代 SDK 的 history size 指标。该现场没有证明触达 8 MiB 守界。

全部原件仍位于本地 ignored `cw1/fault-harness/runs/w7-history/`；诊断脚本、派生 history、精确 stdout／stderr／JSON 位于同级 `cw1/eviction-diagnosis/`，没有发布到共享存储。以下命令以仓库根执行，`CW` 指向本地 ignored `cw1` 目录：

```bash
CW=.ergora/checks/cw1
"$CW/package-r2/venv-r1-sdk/bin/python" -I -B \
  "$CW/eviction-diagnosis/replay_probe.py" \
  "$CW/fault-harness/runs/w7-history/results/history.json" \
  --output "$CW/eviction-diagnosis/raw-r2" --seconds 8
```

该命令已实际返回 exit 1／`RED_EXACT_EVICTION`：8.02 秒达到独立子进程限时，stderr 同时含精确 eviction 异常、pending `_ActivityHandle` 与 `ergora.training_cycle.start.v1`，且没有 replay completed。限时只终止本次命令新建的离线子进程。绿色必须同时满足真实 replay completion 标记、子进程 exit 0 和无精确症状；其它异常或单纯 timeout 均为 inconclusive。首次故意使用不同 Workflow ID 导致控制器身份认证后的 nondeterminism，原 `raw-r1` 保留，未计为红色复现；正式命令保留 `final.json` 的实际 Workflow ID。

## 2. 缩减与单变量对照

先从原 history 删除全部 269 个 signal，再删除 23 组无命令 Workflow task 的 schedule／start／complete，均重编号相关 event 引用，得到 23 事件／19,451 字节。派生 history SHA256=`1d04221857e4d0305bdff202823b2e8b08d417613415dd4e4bf6d54baf682f5f`；`derive_history.py` 和 `history-provenance.json` 可重建变化。保留的事件是 Workflow 初始化、observe 完成、普通 start 调度、Workflow 取消、独立 stop 完成、Workflow 关闭这条因果链。signal 数量和大体积不再是触发该故障的必要条件。

诊断按 `diagnosing-bugs` 先建立红色命令，再将四项可证伪假说按顺序交主控转告用户：普通 WAIT handle 已取消却未完成；产品吞掉驱逐清理异常；done callback 保留 handle；SDK 自身对所有 WAIT 都失败。随后只改变一项运行对照。

| 对照与实际输出目录 | 唯一改变 | 结果 |
|---|---|---|
| `raw-r2` | 原完整 history＋原安装产品 | 精确 RED，8.02 秒限时 |
| `no-signals-r1` | 去掉 signal 的 92 事件 history | 精确 RED，6.02 秒限时 |
| `minimal-r1`／`probe-baseline` | 23 事件 history；后者使用逐字原产品私有副本 | 两次精确 RED，约 5.02 秒限时 |
| `probe-no-done-callback` | 只删 `_normal.add_done_callback` | 精确 RED，5.02 秒限时；反证 callback 是必要原因 |
| `probe-ordinary-try-cancel` | 只将普通 Activity 的 WAIT 改为 TRY_CANCEL，stop 的 WAIT 保留 | 23 事件真实 Replayer 完成，exit 0／1.55 秒 |
| `raw-try-cancel-r1` | 同一单字段私有产品副本，改回完整原 history | 真实 Replayer 完成，exit 0／1.74 秒 |

所有 Replayer 对照保留默认 sandbox、相同 SDK、相同原预算与 history；私有变化没有进入产品。原完整 history 的绿色证明这条实际取消历史能够回放，不认证新包、真实 Worker shutdown 或全部历史／活动类型。

## 3. 根因与 SDK 原生因果验证

产品普通 Activity 使用 `WAIT_CANCELLATION_COMPLETED`：调用 `cancel()` 只请求取消，handle 继续等服务器给出活动终态。`_stop()` 请求取消普通 handle 后排独立 stop；stop 已返回时 Workflow 可关闭，而普通 handle 仍未收到终态。

SDK 1.34.0 的 `_apply_remove_from_cache` 将实例标为 deleting 并取消所有 task。`_ActivityHandle._request_cancel` 在同一 activity sequence 已请求过取消时立即返回；`_await_temporal_operation` 随即再次等待尚未完成的结果 future。因此第二次取消无法进入 `_add_command` 的 deleting 检查，无法抛出 SDK 专用于终止驱逐中任务的 `_WorkflowBeingEvictedError`。驱逐末尾仍有一项任务，Worker 反复重试且离线 Replayer 无法结束。这里的故障条件是**已经请求取消、未收到取消完成、随后驱逐**，不能扩大为“所有 WAIT 都坏”。

`native_workflow.py` 不含产品逻辑、done callback、`BaseException`／`SystemExit`／取消异常处理，只启动一个 WAIT Activity、等待 close signal、显式取消该 handle 后正常返回。`native_probe.py pre-cancel` 在相同默认 sandbox 中投递初始化、close、`remove_from_cache`，不到一秒便 exit 1、精确复现同一 eviction 异常。只去掉 close 前的 `handle.cancel()`，`no-pre-cancel` exit 0／`GREEN_EVICTION_COMPLETED`。这同时反证产品吞异常是必要条件，也收窄了 SDK 触发条件。

另一个诊断专用选项 `pre-cancel --sdk-deleting-probe` 只在该短子进程内，让 deleting 状态下已请求取消的 handle 重新进入 SDK `_add_command`；其它步骤不变即绿色。三个原生对照的命令／返回值／stdout／stderr 存于 `native-pre-cancel.json`、`native-no-pre-cancel.json`、`native-sdk-deleting-probe.json`。该探针支持上述重复取消早返机制，不是建议给产品 monkey patch SDK。

## 4. 最小可维护修补与回归接缝

建议只将 `_ordinary()` 的普通 Activity 改为 `TRY_CANCEL`，保留独立 stop 的 WAIT、shield、一次 stop、原 deadline 与全部停止事实语义。TRY_CANCEL 仍发出同一个取消请求；SDK Core 可立即向 Workflow 的普通 handle 交付取消结果，不再让它跨 Workflow 关闭保留待回执任务。完整原 history 已验证其取消事件兼容性，但其它旧 history 及新候选仍应按各自身份验证。

Workflow handle 完成不是 S/H 子进程停止证据。实际清理由既有 activity owner 保留：`_CycleOperation.run()` 在取消后调用 `request_stop()`，shield 等 `_run()` 对原进程／管道完全 drain／reap，再重新抛出取消；`cycle_service` 的有序收尾先等普通 SDK Worker 的 `shutdown()`／`run()` 返回，再关闭 stop Worker。TRY_CANCEL 不应移除这两层 owner，也不能据此填入 durable stop／executor stopped=true。这里的保证来自现有源码机制；本片没有启动新 Worker 验证实际收尾。

首选回归接缝是使用 SDK Core 的离线 Replayer，给出小型 history：普通 Activity 已请求取消、stop 已完成、Workflow 已关闭、但没有普通 Activity 的取消完成事件。原产品应在精确 eviction 症状下变红，修补后应有界完成。可由 23 事件派生副本整理出身份一致的通用 fixture，去掉现场路径／主机／运行身份；不能使用会破坏控制器认证的虚构 Workflow ID。

现有裸 sandbox activation harness 单独不够：Python handle 自身并不按 WAIT／TRY 立即交付不同结果，这个差别由 SDK Core 解释 cancellation_type 后产生的 resolve activation 实现。若只在测试中按待测字段手动注入取消结果，就会把预期行为写进 fixture，给出错误绿色。回归需让真实 Core 产生该差别，或另外证明人工 activation 来自真实 Core 的原始序列。

## 5. 后续验证边界

正式实施需先保留回归红色，再改一个字段并验证绿色；新源码须重新冻结、独立审查、新建非 editable 安装包并核安装字节。随后在新授权／项目／Workflow 身份下复现实际 pending 普通 Activity＋取消＋独立 stop＋有序 Worker shutdown，检查 Activity 实际取消清理、S/H 与执行子树、独立 stop capacity、原预算不延长、完整 history replay，以及无重复 eviction、无 Driver hang。原 8 MiB 守界仍需要独立达到 SDK 真实计量边界的现场，不能用本次 8,139,050 字节或 JSON 字节数替代。

原现场服务端 `CANCELED`、旧 Worker／Driver 的异常和主控收尾结果分别归原现场；本诊断只证明离线原历史的精确失败、根因收窄、私有单字段对照与可用回归接缝。产品修补与新包／新现场的通过仍由后续实施记录接续。
