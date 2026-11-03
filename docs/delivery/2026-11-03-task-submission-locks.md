# F3.3d：提交意图准备与长远程等待分段

日期：2026-11-03。当前为下一切片调查/设计，尚未实现。依赖c2的已验证共享身份边界，当前c2源码/测试身份`b215f9553a3ba8ac716b70bd86ecf285af7eb1d3c0fc6e92956078dd023255bd`、发行候选`4abad37…`；c2最终回归/CI仍待完成，不能预先作为d验收。

## 已实测问题与目标

F3.3b原提交把SQLite BEGIN IMMEDIATE持有到doctor、claim和远程start/lookup结束。原最终f8d92f…包的隔离探针在SDK connect延迟18秒时，使另一个项目真实写者15.04秒后busy失败；无部分写，结束后显式重试成功，见[提交记录](2026-11-03-task-submission.md#共享控制库锁争用补测)。c1/c2的新入口已经分段，但没有修复该旧提交路径。

目标是保留修订授权、不可变原创建/提交意图、原准入/claim、原task锁、spec/memo及写前attempt语义，同时让长远程操作不占全库写锁。不是替换SQLite、增加后台队列、另造调度器或重试未知提交。原提交记录格式和已有run/任务ID保持，不迁移在途history。

## 预定实现

1. start/resume-start在当前revision的短控制库保留下，仅运行无网络prepare/prepare-resume子进程：核原创建/登记、原意图或摘要，以非阻塞原任务锁保存或读取意图。准备不调用doctor、claim、connect，也不读取完整连接环境。
2. 退出控制库事务后，才运行dispatch/resume。网络阶段只持原任务锁，加载原环境，复用既有dispatch/Transport检查点和严格spec/memo恢复。初次prepare返回created；相同start已有意图只读原状态，不隐式重试准备失败的准入。resume携带原意图SHA；已有attempt仅lookup，不因NOT_FOUND或历史消失重发。
3. 已有submitted/rejected回执可直接返回；阶段间父进程中断保持prepared，明确resume再继续。另一明确resume若先取得锁，后续dispatch只读其原结果/unknown，不重复start。
4. 短本地准备事务与c1/c2归入tasks中同一修订保留所有者；确认/输入约束保留各入口差异，不能为复用而给start捏造人工确认。保持原doctor、可信检查、IngressLeases和局部SDK归属hook不变。

同任务准备遇活跃任务锁时将及时报busy；并发读到已保存意图时也可得到prepared/unknown快照，而不是等待另一请求变成submitted。相同已完成意图的后续调用仍返回同一原run回执。验证应固定“只有一次start、未知不重发、没有半份意图及跨项目写锁等待”，不能以两个并发调用一定取得相同时间点状态为条件。公开手册需明确这一可观察并发响应；不自动轮询、重试或延长预算来掩盖busy。

## 验收

- 重放原提交全部中断/竞争/memo/严格JSON反例；旧意图/attempt/result/rejection字节保持，提交/批准/取消/status联合回归。新prepare不产生doctor/claim/connect证据。
- 准备完成后、派发前父响应丢失；当阶段之间项目revision/角色变更，意图和原任务绑定仍固定，后续显式恢复使用当前revision核原SHA；配置/创建文件漂移仍拒绝。
- 同任务并发准备/明确resume/dispatch交错不重发；busy及时释放全库保留，未创建意图的错误不伪造prepared。保存意图后发生错误仍可查原记录，不改变task/run ID。
- 同等18秒connect延迟下，另一个项目真实写入在远程完成前成功；同任务prepare及时拒绝、其后跨项目仍可写。测新路径额外子进程启动成本、明确fixture/RPC范围，不由并发收益推导模型吞吐提升。
- 最终非editable包、两安装/冻结283、基础两模板完整操作旅程及限定性能、适用完整回归/精确两OS CI；新的fresh-context结构/性能审计、最终独立核对与提交推送。d完成后才进入F3.4真实新六阶段/导出/重启综合旅程。
