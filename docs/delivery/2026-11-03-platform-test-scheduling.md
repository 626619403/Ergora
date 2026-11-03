# V2：Linux 专用测试提前跳过

2026-11-03。依据[测试成本计划](../plans/2026-11-03-verification-efficiency.md)及[独立成本审计](2026-11-03-verification-redundancy-review.md)。V1已完成并推送4e01a4e及收口c6a08f9；V2实施基线`c6a08f994ac9d12cc8370f0013af3cd0c447ff03`。本记录保留实施前合同及当前定向验收，生产保持。

## 范围与设计

当前`submitted_creation(creation_project)`及`export_task(creation_project, native_client)`在fixture函数体才跳过非Linux，因此其registration/installation依赖可能已经执行。改用pytest既有模块级`skipif`在fixture setup之前跳过真正Linux专用的提交、提交锁、批准、取消、导出和外部证据集成模块。保留fixture内原防护，不引入收集hook、共享可变session安装树或第二套平台检测。

提交的Linux/WSL2与缺完整环境提示、外部证据查询的缺环境提示共两个既有跨平台案例移到既有`tests/test_tasks.py`：该模块拥有公共任务读取/平台边界，继续复用原`creation_project`。用例内容与严格错误期望保持。纯输入29项、任务创建、原生跨平台状态查询、Windows编译/控制面/安装升级继续执行；不把任务系列整体标Linux。

仅调整测试调度和两项测试的归属，不改变生产、依赖、冻结283、CI矩阵或必需步骤。先后源码和测试案例清单、移动前后函数AST与Linux skip条件有可比证据；新fresh-context审查者检查所有真实消费者均被标记，且平台提示没有被误跳过。

## 验收边界

本地定向运行移动后的提示、29项纯输入及代表性真实Linux操作；通过非Linux收集/pytest setup计划只验证标记顺序，不把模拟当作Windows运行。最终精确Windows/Ubuntu完整CI保留原门禁，Windows对应的Linux专用用例应在setup之前跳过，跨平台提示/编译/安装继续成功。优先读取实际CI日志说明调度结果；没有可比Windows测量时不承诺节省秒数。

实现及定向验证已通过；新的独立源码审查已通过，共同候选精确CI及同审查者最终复核已通过，V2完成。V2完成源码审查和独立提交后实施V3，最终共同候选的完整两OS CI同时验收两项仍保持的精确文件身份；V2不提前标完成，也不把其单独提交报告为已有CI。下一项V3处理过时CI运行，随后继续F3.4b2明确终态外部对账。

只读基线已收集：10个相关模块共323个参数实例、115个顶层测试函数的完整AST摘要，六个Linux相关模块的fixture消费者没有出现在其他模块。原收集发生在V1提交前，但文件内容与已提交4e01a4e候选一致，身份单独保存，不把当时HEAD b55af5d误作V2运行候选。证据为`verification-platform-scheduling/collection-before.json`、`function-baseline.json`。已通过Windows作业125815506254的逐步原日志公开接口返回404，只保留访问事实；后续不据job success推算逐例耗时或节省秒数。

## 已实现与定向验证

七测试文件已实施：六个Linux集成模块的标准`pytestmark = skipif(...)`，新增三个必要sys导入；两项平台提示原函数逐字移动至既有跨平台test_tasks.py并复用原creation_project。原fixture内部保护仍在，未新增收集hook或共享安装树。CI、依赖、生产及冻结内容未变。

独立于测试数量，直接比较原/新全部115个测试函数的完整AST（含参数装饰器），除两项路径移动外逐一相等；323个收集nodeid严格保留同一集合，218个实例位于六个模块且具有实际Linux=false标记，105个跨平台实例没有该模块标记。七文件aggregate为`b59a9e84fb5bb8ebaa98a9a417602ef17d3b1fef84520fb69ae0fc8b8ccdd6df`，见`source-identity.json`与`tracked.diff`；347个生产文件重算仍等于原B1包。

同一既有非editable包环境执行 **40 passed（93.49秒，退出0）**，覆盖移动的平台提示、29纯输入及六个Linux模块的真实代表正常行为（提交/导出/外部证据均含两个模板）。精确命令、日志、JUnit为`linux-command.json`、`linux.log`、`linux.xml`。仅测试调度变化，未重建相同本地包或重复完整本地回归。

`simulate-nonlinux.py`只对实际候选模块的原条件表达式分别求值linux/win32/darwin，并将win32求值用于pytest模块标记；不修改sys.platform，也不模拟Windows文件/进程。218个专用实例在setup阶段跳过、重型fixture命中0，29个未标记纯输入仍通过。证据为`nonlinux-simulation.json/log`；这是条件与pytest setup顺序探针，不是218个Windows实测skip、Windows性能或真实执行验收。实际Windows/Ubuntu仍待共同候选完整CI；公开逐例日志不可得时按实际范围报告。

本切片实现、定向验证及[新fresh-context源码审查](2026-11-03-platform-test-scheduling-review.md)已完成，无findings；独立重算152个顶层函数AST（含115测试）及323 nodeid/每例fixture集合保持，另收集14项相邻Windows/安装测试共337项，setup命中0。七文件身份/原diff/347生产资源保持。共同候选CI与最终复核待完成，不提前标V2完成；下一步独立提交后实施V3，保留各自最终文件身份。

V2七文件已独立提交`4a6d3d52dbb42dd6fc9328b49596498f812b112a`，没有单独推送或宣称其CI通过。V3仅改工作流并保持七测试文件身份，待V3源码审查后共同推送验完整CI。

## 共同最终候选CI进行中

V2源码提交4a6d3d5及V3源码提交`d5588855be0d5995465caa7e0af4b1b80103cc11`已共同推送，实时远端同名工作分支与最终完整40位候选一致；V2七文件b59a9e84…及V3 workflow 4d45c728…在Git blob/工作树均保持，生产347文件未变。证据统一在`.ergora/checks/verification-ci-scheduling/combined-candidate.json`及`ci/`；只触发一套共同完整矩阵。[精确CI41612623462](https://github.com/626619403/Ergora/actions/runs/41612623462)正在执行，不提前报告两OS通过或节点完成。

Windows最终候选作业`125838059005`现已成功：构建安装、包内reference身份、Native application regression及PowerShell 5.1安装升级均成功，官方当前作业页/步骤SHA日志URL已核。本轮只观察到这些完成事实；Ubuntu及共同CI的最终复核仍在途。

|Windows完整回归步骤观察|候选 / 作业|官方起止间隔|
|---|---|---|
|V1后、V2前|4e01a4e / 125815506254|390秒（6分30秒）|
|V2/V3共同候选|d558885 / 125838059005|212秒（3分32秒）|

上述来自两次不同GitHub运行的官方check-step `data-started-at`/`data-completed-at`；OS/Python同为windows-latest/3.12，属于实际步骤观察，**不是同一runner的受控加速对比、逐例/setup计时或固定收益保证**。不据此推算218项各自耗时或V3取消节省。原页面及来源SHA在`windows-before-step-timing.json`、`windows-after-step-timing.json`及`windows-step-observations.json`；公开原console日志仍未取得。该Windows观察阶段的V2尚等Ubuntu/共同精确CI及最终核对，现已按下文补齐。

## 精确共同CI与最终复核

`d5588855be0d5995465caa7e0af4b1b80103cc11`的官方CI`41612623462`已成功。Windows作业`125838059005`四必需步骤、Ubuntu作业`125838059675`三必需步骤（构建安装/包内reference身份/原生完整回归，Windows另含PowerShell 5.1安装升级）均success。统一`ci/fetch-ci.py`和`ci/verify-ci.py`退出0，完整原HTML/selection/sha日志URL与`ci-html-status.json`绑定该40位候选。

最终Windows页面的起止时间与此前212秒步骤观察一致。V2/V3测试/工作流身份仍为b59a9e84…/4d45c728…；本地原52d26d…包的347生产文件保持。两项各自同审查者最终CI/提交/实时远端复核均已通过；没有额外触发取消演练或另一套完整矩阵。

## V2最终收口

[同一fresh-context审查者最终复核](2026-11-03-platform-test-scheduling-review.md)通过，无新增finding：独立逐字核V2源码提交4a6d3d5、共同候选d558885与工作树七测试文件身份；workflow完整4d45c728…且扣新增四行后保持原基线，347生产tree未变。自行重新读取官方run与两job页面确认完整push SHA、checkout/setup及Windows4/Ubuntu3必需步骤均成功，实际完整pytest参数未缩减。

2026-11-03 09:53:07 UTC独立实时远端返回同一完整d558885…；`reviewer/final-review.py`退出0，证据为`reviewer/final-verification.json`及独立原HTML。390/212秒两份来源SHA/完整提交log URL/起止均核，新实时页仍为212秒；只作两次步骤观察，不推加速率或逐例数据。没有再测/安装/构建/触发CI。V2完成；V3也已独立最终复核完成，两项共用一套精确矩阵，下一功能为F3.4b2。
