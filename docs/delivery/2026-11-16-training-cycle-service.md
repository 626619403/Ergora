# c1b2a：独立训练cycle服务逐步交付

日期：2026-11-16。按[已审r2具体合同](../plans/2026-11-15-training-cycle-service-boundary.md)与[独立设计审计](2026-11-15-training-cycle-service-design-audit.md)推进。产品代码仍在隔离分支`feat/training-cycle-service`，主开发分支当前已发布6725；本片尚未整体验收／发布。

设计以c1b1 d5b5891为产品前置，独立通过后固定b719353；实施候选797da567f8b282b4884fceafe16c3efba506f493已在本地固定，再真实合入6725得到`fef7d98e30d5625e5ce37dc45e14904f76447775`。自动merge保留了新BR资源与CI fixture修正；尚未向主开发分支导入本片产品。

四个原owner改动：`reference`／`services`提供独立命令、配置和70秒关闭观察；`reference_training_worker`／`training_execution_protocol`提供四实际活动、可信SDK来源／receipt前run认证、原S-H／一次窗口、仅ordinal0新start、完整原件引用与unknown／容量、双queue各一槽及关闭接线。原283参考、原budget queue／8槽及旧直接接口保持；正式总Workflow／sandbox、execution／collect、接受／后继门槛仍后接。

源码子任务原验证分别见[活动记录](2026-11-16-training-cycle-activity-implementation.md)与[管理接线](2026-11-16-training-cycle-service-wiring.md)：原22回归、新SDK7组及若干精准接缝、services19通过／1平台skip等，各轮有重叠，不相加冒称全库。来源篡改新测试两次断言失败保留，最终按实际H层级及start计数修正；没有为这些断言改变产品。它们不代替联合新安装或真实Temporal。

已在home持久目录准备全新CPU验收stack及本地git项目`cycle-service-acceptance`，注册revision1且发布一致；仅复用既有native依赖、Temporal1.9.1／Server1.32.0，不装系统包、不改共享环境、不覆盖用户命令。准备时没有服务／实验／授权／预算根。原件在项目ignored `training-cycle-service-acceptance/preparation-r1/`；后续运行前仍需核7233可用。具体本机目录仅留私有原件。

合并候选的新包已完成：core／SDK各663产品文件source＝wheel＝site（含执行位），仅前述四原owner变化，283参考／依赖保持；core无SDK，SDK1.34.0。wheel SHA256为`b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`。178测试／示例在build前冻结，原件在ignored `training-cycle-service-acceptance/package-r1/`。

安装接缝实际collect68项／216可见项，最终67 passed／1平台skip／148 deselected，531.82秒，完整命令／输出／JUnit保存`installed-tests-r1/`，见[安装记录](2026-11-16-training-cycle-service-installed-checks.md)。另一真实core subprocess已经核SDK不存在、services.status可读，启动cycle服务明确拒绝且前后status相同，没有服务被启动。

真实r1已启动Temporal、budget与cycle三个独立PID，并以标准SDK sandbox中的最小测试Workflow完成四活动的真实normal／stop queue路由和非法输入非重试拒绝。测试Workflow已经COMPLETED；记录history时曾误用不存在的to_proto方法导致记录脚本失败，原输出保留，后续仅只读恢复同一run的完整history／结果，没有重投活动。此用例不是正式总Workflow或有效业务cycle。随后明确停止两个空闲worker，确认OS终态；本地Temporal仍保留供修后验收。两份CPU候选通过真实baseline／runner／experiment预览准备，尚未授权或执行。

新fresh reviewer的[源码两轴审查](2026-11-16-training-cycle-service-product-review.md)已收：需求request changes／4开放，可维护性独立0开放。R1实际SDK验证失败后shutdown可能永久等；R2需用on_fatal_error及时触发normal-first关闭；R3父侧Popen／transfer／cleanup事实丢失；R4部分typed容量降格unknown。高强度子任务正在原owner修正。旧包安装／路由结果保持其原范围，修后必须新身份定向复验。

下一步：取得安装接缝终态；真实Temporal／Supervisor独立PID、normal槽阻塞时stop领取、取消／信号／fatal及实际收尾；处置独立具体finding、自身模板及最终两轴。未到这些终态前不称服务可用、自动循环或真实训练收益通过。
