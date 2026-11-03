# V2：Linux 专用测试提前跳过

2026-11-03。依据[测试成本计划](../plans/2026-11-03-verification-efficiency.md)及[独立成本审计](2026-11-03-verification-redundancy-review.md)。本记录先固定下一切片的合同；V1尚待最终复审与精确CI，V2生产/测试代码尚未修改。

## 范围与设计

当前`submitted_creation(creation_project)`及`export_task(creation_project, native_client)`在fixture函数体才跳过非Linux，因此其registration/installation依赖可能已经执行。改用pytest既有模块级`skipif`在fixture setup之前跳过真正Linux专用的提交、提交锁、批准、取消、导出和外部证据集成模块。保留fixture内原防护，不引入收集hook、共享可变session安装树或第二套平台检测。

提交的Linux/WSL2与缺完整环境提示、外部证据查询的缺环境提示共两个既有跨平台案例移到既有`tests/test_tasks.py`：该模块拥有公共任务读取/平台边界，继续复用原`creation_project`。用例内容与严格错误期望保持。纯输入29项、任务创建、原生跨平台状态查询、Windows编译/控制面/安装升级继续执行；不把任务系列整体标Linux。

仅调整测试调度和两项测试的归属，不改变生产、依赖、冻结283、CI矩阵或必需步骤。先后源码和测试案例清单、移动前后函数AST与Linux skip条件有可比证据；新fresh-context审查者检查所有真实消费者均被标记，且平台提示没有被误跳过。

## 验收边界

本地定向运行移动后的提示、29项纯输入及代表性真实Linux操作；通过非Linux收集/pytest setup计划只验证标记顺序，不把模拟当作Windows运行。最终精确Windows/Ubuntu完整CI保留原门禁，Windows对应的Linux专用用例应在setup之前跳过，跨平台提示/编译/安装继续成功。优先读取实际CI日志说明调度结果；没有可比Windows测量时不承诺节省秒数。

实施、定向验证、独立审查及精确CI均待完成；实施基线在V1最终交付后登记。V2完成源码审查和独立提交后实施V3，最终共同候选的完整两OS CI同时验收两项仍保持的精确文件身份；V2不提前标完成，也不把其单独提交报告为已有CI。下一项V3处理过时CI运行，随后继续F3.4b2明确终态外部对账。

只读基线已收集：10个相关模块共323个参数实例、115个顶层测试函数的完整AST摘要，六个Linux相关模块的fixture消费者没有出现在其他模块。原收集发生在V1提交前，但文件内容与已提交4e01a4e候选一致，身份单独保存，不把当时HEAD b55af5d误作V2运行候选。证据为`verification-platform-scheduling/collection-before.json`、`function-baseline.json`。已通过Windows作业125815506254的逐步原日志公开接口返回404，只保留访问事实；后续不据job success推算逐例耗时或节省秒数。
