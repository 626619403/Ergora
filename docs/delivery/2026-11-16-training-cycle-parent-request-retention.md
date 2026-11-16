# c1d：超限父请求原字节留存实施

2026-11-16。状态：已接纳设计的隔离实施进行中，尚未完成源码验收、安装、自身模板或 fresh 独审。依据[限定设计](../plans/2026-11-16-training-cycle-parent-request-retention.md)及其[原审／复审](2026-11-16-training-cycle-parent-request-retention-design-review.md)，保留 R1 完整原 clock 和 M1 原 raw／N／EOF／一次确认；不开放 schema3 执行或后继轮次。

准确产品基线为 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，唯一父 `23ad171bf8228bf80b070d6ad866f79d63986d56`。隔离分支 `feat/training-cycle-parent-retention` 从该提交创建，根代理管理相邻产品来源与整合；本实施不修改相邻来源树、不 commit／merge／push。应用 maintainable-project-delivery 及 ergora-codebase-quality 的 module-design／test-seams。

实际接口核定：新 operation-v2 只有 `collect-round/reconcile-round`，使用原十字段 identity、schema3 snapshot、必需 activity_context、原 controller binding 与 work bootstrap。M2 的已接纳 B 分片把 `_CycleOperation` 的实际 constructor／同次 UUID 与 compact 编码／run 作为内部 producer 边界；正式 SDK v3／V2 上层 creator 尚不存在，保留到后片。根再次明确这一范围后继续。本片不新增 SDK 注册、上层 creator、伪造来源认证或削弱原业务 reader 的认证。

最小改动仅原 [worker](../../src/ergora/reference_training_worker.py)、现有 [submission tests](../../tests/test_training_submission.py) 与 [operation fixture](../../tests/fixtures/training_cycle_operations.py)。worker 在 v2 编码超界时保留同一次 UUID 和 immutable raw，原 async owner 选择无 H／无后代的诊断 S；普通 v1 constructor 仍立即抛错，普通 S/H 的 stopped kill gate／唯一 reaper 不变。小封套携完整 clock 四字段、两项原 policy、bootstrap 与只缩整数 deadline；S 主线程和进程内 watchdog 持续实际调用原 budget_clock.remaining。stream 分块≤65,536B，父显式 yield／drain并逐块 SHA；S exclusive 保存唯一 request.json、N／EOF、原 fd fsync、目录链同步、同 inode／N／SHA 流式重读后发一次小 identity-bound 确认。没有第二 receipt、ledger、ready、trailer 或恢复 reader。

父只有在发送结束、全部 pipe 结束、实际 wait 成功及最终原时钟／stop 检查通过时给 request_retention.durable_confirmed 和小 ref；其他故障均 unknown／不给 ref。业务始终 capacity_exceeded，不发普通 S/H/root、不返还机会或重发。诊断 wait 不伪装成 H stopped；小发现日志仅含 ID、mode／ordinal、output 与留存／实际 wait 事实，不打印原 reason／raw。有限窗口、磁盘错误、SIGKILL 及内核不可中断 I/O 无法保证完整 durable 或硬实时回收；保留 partial／unknown 的实际范围。

私有逐轮证据位于根 ignored `.ergora/checks/cycle-parent-request-retention/`，每轮保留原 argv／env、basetemp、JUnit、完整 patch、src/tests manifest 与输出。后续候选不继承较早轮通过：

|轮次|实际结果与范围|
|---|---|
|run-01|1 failed／7.20 秒。真实诊断路径已经返回 durable_confirmed，196,331B raw 逐字比较成立；测试 oracle 把小 envelope 也计成第二次原 payload 编码而失败。修测试过滤至含 snapshot 的原 payload，原失败保持。|
|run-02|1 passed／6.01 秒。真实内部 constructor 同次 196,331B 多字节 UTF-8 raw，无末尾 LF、原 UUID／full identity、唯一 request.json／完整 ref、实际 wait；业务容量失败、无 helper／H，原 admission 文件逐字不变，日志无 reason。source 内部接缝与合成原 source，不是正式 SDK 或真实训练。|
|run-03|新增真实 stream／N／EOF、32,768／32,769B、partial／fsync／same-raw replace／raw corrupt、reply／SHA／identity／额外帧、blocked writer取消／peer，以及父 loop 不可调度时 S-local UTC drift 的 watchdog 检查正在运行，未预记通过。|

尚待：本轮结果、真实 parent SIGKILL、spawn／发送生命周期、必要旧 v1／history 回归；固定最终 src/tests 后受影响组。安装、原模板、新 fresh 独审与发布由根后续负责。当前不关闭完整父留存 gate、M1c、M5／M6 或真实两轮验收。
