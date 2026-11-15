# 原停止并发片的CI失败调查

日期：2026-11-15。只读调查基线为已发布的`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`，不包括当前主工作树的c1b1产品或测试修改。

## 已观察的失败

[官方run43713822317](https://github.com/626619403/Ergora/actions/runs/43713822317)绑定上述完整SHA、`push`、attempt1和`refactor/architecture-foundations`。原API响应已记录终态failure；八个job中七个success，唯一failure为[Ubuntu3.11第5组job132810977047](https://github.com/626619403/Ergora/actions/runs/43713822317/job/132810977047)。

匿名日志下载403不覆盖此结论。此前保存的公开job HTML为200，Annotations直接给出：

|观察|原始内容|
|---|---|
|失败测试|`tests/test_training_submission.py::test_cycle_stop_notifies_peer_while_writer_and_other_target_reads_block[controller_admission0]`|
|错误|`FileNotFoundError`，读取`operation-markers/stop-writer`时文件不存在|
|本项call时长|25.79秒|
|本组终态|1 failed、524 passed、13 skipped、1612 deselected；998.57秒|
|失败步骤|Native application regression；退出码1|

页面中的三条error分别为步骤退出、测试失败和尾部摘要，不是三个不同测试失败。Node20迁移warning与Ubuntu镜像迁移notice没有提供本次断言失败的因果证据。

## 已核源码与根因界限

以下行号均属于固定`1b8c2ed`：

1. [原测试2692–2698行](https://github.com/626619403/Ergora/blob/1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b/tests/test_training_submission.py#L2692)只等待`beta-notified`，随即读取`stop-writer`和`alpha-owner-reader`。错误路径对应2698行。执行到该读取说明beta通知事件已被读取，且其目标身份比较已经通过。
2. [原fixture46–74行](https://github.com/626619403/Ergora/blob/1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b/tests/fixtures/training_cycle_operations.py#L46)分别在writer的真实`stop.json`同步接缝、alpha的真实owner读取接缝写出阻塞标记，再睡眠；beta则在真实`notify_identity`返回后立即记录通知。三者之间没有就绪屏障。
3. [原worker241–250行](https://github.com/626619403/Ergora/blob/1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b/src/ergora/reference_training_worker.py#L241)为writer、drain、两候选的通知与执行观察创建独立asyncio task，并并发gather。任务创建顺序不保证不同S/H进程到达上述业务接缝的顺序。

因此，测试确实依赖了产品不承诺的跨进程先后：beta可以先完成实际通知，writer尚未触及同步接缝。公开失败与这一合法调度一致。**目前没有原job的完整堆栈及operation输出，尚不能把缺失writer标记的具体原因唯一认定为调度竞态，也不能据此确认产品writer失败。** 当前c1b1差异没有用作原发布失败的归因或修后证明。

## 最小候选与验证

先在精确基线的独立分支用仅证据副本生效的fault推迟writer／alpha进入接缝，确认原fixture在beta先到的合法顺序下实际失败。候选只修改原测试fixture及必要的诊断断言：beta在真实通知之前，使用原operation剩余窗口等待两个真实阻塞标记就绪；保留实际通知后完整目标身份、两阻塞进程仍活、原unknown边界与最终回收断言。

只在beta之后等待所有标记不能证明通知时已经重叠，单纯增加固定sleep也没有建立该前提。候选不改变产品、原clock、权威或唯一reaper。

修后沿同一受控调度和原真实双owner场景验证，再选择原取消、耗尽原clock、冷inspect及旧身份通知接缝；源码与匹配基线的非editable安装分别记录。完整产品身份、所有已知actor收尾和最终候选差异须可复核。当前本报告只完成只读判断，尚无上述复现或修后通过，不触发提交、推送或远端重跑。

## 原件与可恢复位置

原响应保留在项目忽略目录`.ergora/checks/training-cycle-owner-boundary/remote-queue-r1/`，公开HTML及请求保留在`.ergora/checks/training-cycle-owner-boundary/remote-queue-r2/`；后续调查只写独立`.ergora/checks/cycle-stop-ci-investigation/`，不覆盖原件。

|原件|字节|SHA256|
|---|---:|---|
|run-response.json|11960|`0f75f87713d81fead03f08035c2ff859f8f24e842abfed82cbebde79aac4cfa4`|
|jobs-response.json|21121|`b251d53f591962e3965da98f5b1dda7f4085a4d21c618c24cde808510c84731b`|
|job.html|171701|`bfcb54d24bccf0627ff72d39a7342e3b0682359ecc66574fc71f1169c465d57b`|

共享IP的公开API限额在15:23:15UTC之前不重试。完整日志或`ci-ubuntu-latest-3.11-5`工件有助补齐原堆栈；不需要为已有可行动测试缺口而停止本地独立复现，也不能用新的候选结果改写原run终态。


## 已发布候选的只读状态更新（2026-11-15 15:59 UTC）

候选`7025e15f40e1934097a5c1c962bb7bf5e82a979d`已普通推送至`fix/cycle-stop-overlap-ci`及`refactor/cycle-stop-overlap-ci`；原发布记录与两轮精确远端ref核对保留在忽略目录`publication-r1.json`及`remote-ref-r1/`、`remote-ref-r2/`。本轮未推送、未修改workflow。

先核`ci-r3/`原件：15:51:40 UTC的分支push查询为HTTP 200、`total_count: 0`，当时剩余额度5；workflow查询为active。这仅证明该时点未看到自身run。随后在15:59:40 UTC只查询一次官方Actions runs，参数为完整候选`head_sha`，返回HTTP 403、remaining 0，reset为2026-11-15 16:23:16 UTC。本轮没有实际观察到该候选的自身run，也不能据403认定没有run、失败或成功；未继续轮询。

新请求元数据、完整响应headers和原响应分别保存于项目忽略目录`.ergora/checks/cycle-stop-ci-investigation/ci-r4/runs-request.json`、`runs-headers.json`、`runs-response.json`；响应SHA256为`cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`。旧`1b8c2ed`的官方run`43713822317`仍为failure，不能由新候选状态覆盖。


## 单次精确SHA续查（2026-11-15 16:24:46 UTC）

越过ci-r4记录的reset后，仅再查询一次官方Actions完整`head_sha=7025e15f40e1934097a5c1c962bb7bf5e82a979d`：HTTP 200，total_count为0；本次未观察到自身run；不据此断言后续不会出现run。未切换出口或认证，未重复轮询。原请求、headers和响应保存在`.ergora/checks/cycle-stop-ci-investigation/ci-r5/`的`runs-request.json`、`runs-headers.json`及`runs-response.json`；响应SHA256为`a2790a384d7d281e7395679000c35d27768d89dbd7052f725b8f4688beb59915`。旧run`43713822317`的failure保持，其他候选结果不覆盖其终态。
