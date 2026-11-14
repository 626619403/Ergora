# Q4.2b3 训练预算与实际执行停止：交付记录

日期：2026-11-15。[具体计划](../plans/2026-11-15-training-budget-executor.md)r2处于实施前合同复核，未改本片产品、测试、schema或283参考。前置b2仍在最终独立验收；本片实施前固定其实际发布Git身份，不把b1／b2 CI转授后继。

已只读追踪原`reference_budget → task lifecycle`及`training start → native request → training_executor.process → Sandbox → process_job → runner`。原executor覆盖Git两臂准备、runner、archive和MLflow tracking；Sandbox及runner各自新session，仅杀外层进程组会漏真实后代。`processes.run(supervised=True)`有专用driver／subreaper回收，但不按timeout参数自行截止，须实际stop predicate。六阶段task scope／slots不是训练循环授权。这些是源码观察，未运行训练或作停止主张。

计划分为授权／原期限、提交slot／晚到边界、专用executor／真实后代和安装交付，逐片验收；SIGKILL／跨boot／缺原件保留unknown，不请求宿主权限或扩大已接受容器边界。下一步为新的fresh-context独立计划两轴审查，明确字段与可验收接缝后再实施。Kernel专家继续保留在v3提案路径。

[新fresh-context r1评审](2026-11-15-training-budget-executor-plan-review.md)需求request-changes／开放2，维护request-changes／开放1。R1的首RPC至queued／executor交接缺连续owner、R2的首次live admissions与原时钟顺序不明均有真实可达调用依据，接受。计划r2明确同授权独立owner在首attempt前启动并持续监管RPC／queued／交接，deadline自动原fence，不等后继c；其验收包含CLI先返回、native create延后以及held RPC跨截止。原授权时钟先于全部昂贵live检查，pending不授执行权，同ID中断／lost-ack不续期，全部检查与完成fsync耗时计入；另固定完整原输入、授权和ready记录的SHA／字节界。当前待原reviewer复核，未开始产品实现。

同reviewer已核最终r2两轴approve／开放0／0，R1–R2关闭；明确原手工submitted fence限制及原adapter／registry lock应用扩展接缝，手工权限保持。固定计划17942B／SHA`831127e9aa6a5aad5d0f6fdc65f7cd3e4abf9f16c74203a4eb4d0233b81fe227`和原delivery／review保存在本片ignored检查目录，后续仅同步进度。产品未改，计划通过不等于预算／进程／循环运行通过；实施前须固定b2实际发布Git身份。
