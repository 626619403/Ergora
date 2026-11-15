# Q5.2a：训练测试平台维护与 c2 CI 接续

日期：2026-11-15。依据[独立测试价值审计](../delivery/2026-11-15-training-test-value-review.md)的 P2／P3，实施基线固定 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`。前置自己的CI43684533043／attempt1已终态7job成功／Windows六个夹具setup错误；本片作为其最小测试接续，保持原失败归属，不推后继产品。与并行的 Q4.2c 设计分开；不修改产品、native 算法、冻结参考或 CI 矩阵。

实际问题：`service` 在依赖 `prepared→experiments→registration` 全部构造后才在函数体内跳过非 Linux，因此 Windows 对本来不运行的 case 仍做 Git／原件准备。原审计固定75285e3的25个函数／39个参数化service case及一个body-skip case；当前ac86043静态重核仍有25个service测试函数缺提前平台标记，另三函数已有标记。原报告的数量／耗时不转授为本片的Windows收益。

实施范围：在这25个函数及单独的 `test_original_prepared_start_is_readable_and_fenceable_but_cannot_dispatch` 加文件现有形式的 `skipif(sys.platform != 'linux')`。保留所有 nodeid、参数、Linux 业务行为及可移植读取测试；保留 fixture 自己的平台约束。删除不完整 stopped 场景中的完整 `reason` 句子相等断言，保留故障参数、真实 marker、状态、精确进程回收、同 fence 恢复和原件不变检查。

验收：在原r6非editableSDK安装收集前后完整nodeid，比较Linux marker与参数集合；用受控的**仅目标测试模块平台视图**验证当前41个case在setup前skip、未进入昂贵fixture，可移植节点不被误标。此受控检查不是实际Windows运行。精准运行原 `phase-stopped-incomplete` 集成场景，不重跑全部13分钟submission suite。Windows实际回归仍由本片自己的远端CI验，若拿不到前后逐case Windows原件，只报告行为／setup消除，不宣称节省秒数。

本片完成前更新[交付](../delivery/2026-11-15-training-test-maintenance.md)，用新的fresh-context审查者核需求／维护性两轴；通过后普通推送当前分支，核完整远端及自己的适用CI。Ergora自身结构模板消费精确测试差异与实际验证；模型意见不代替原场景或独立审查。Kernel专家和全部产品／模板保持。


## Windows 失败的同片最小修复

自己的Windows CI证明，`historical_execution` 这个明确无活授权的合成停止档案夹具，曾通过Linux-only `training_submission(..., prepare)`取得初始intent，导致六个可移植测试在setup阶段失败。现直接按旧intent合同构造合成identity／operation ID，完整observation从原SDK-free `reference.training_files`取得；其他start／owner／native request／launch／attempt／ack／stopped原链及所有断言保留。不将执行或授权约束改成跨平台，不跳过可移植检查。

新增验收范围：原8个historical_execution参数化节点全跑Linux；再以局部入口替身仅复现原Linux-only prepare拒绝条件，原未修fixture六节点应为六setup错误，修后六节点应不再调用prepare并真实通过其余读取／坏链断言。该替身不模拟Windows文件语义，最终以修复提交自己的真实Windows CI为准。原FIFO的body skip保留，受控提前skip视图保持其原范围。原84个nodeid保持；原26标记和删断言的先前验收只证明其当时范围，新范围需补自身原模板及新fresh-context两轴审查。
