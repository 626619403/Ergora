# F1.2：统一项目注册与单向配置投影

日期：2026-11-02。分支`refactor/architecture-foundations`，源码基线`f11b8ccb59a4073a4e17b35d5c7500105c9d5b29`，开始时工作区干净。用户授权继续完成F1，并要求每个大项使用独立审查者及代码结构相关技能检查。

## 范围与设计

统一注册从版本化JSON选择业务Git根、模板集合、角色/支持工具、执行安装/配置/状态位置、tracker、基线、允许路径、可信检查和scope策略。旧`project add`保持轻量注册行为。CLI/API调用同一用例；F1.3另做旧注册检测、预览与显式导入，不自动接管已有文件。

`projects`保留基础项目和工具绑定所有权；新增`registrations`负责跨SQLite/参考文件的完整注册用例，有CLI/Web两个实际消费者。`reference`持有参考布局、固定安装身份及原子不可变文件发布，继续以专用子进程调用冻结代码，避免在Web中加载导入时固定的CONFIG/STATE。沿用已有schema校验、绑定能力、模板角色、参考路径/scope校验、文件锁和原不可变发布，不创建通用插件或第二套生命周期。

项目文档的可选`registration`保存规范化定义、投影意图、来源摘要、操作ID和pending/published状态；工具仍只由顶层bindings拥有。执行配置是定义的单向派生。SQLite和多文件不是一个原子事务：先留下包含前后项目的不可变恢复记录，再提交pending项目，再发布所有文件，最后确认published并保存完成回执。中断后可按项目revision恢复，禁止用新输入替代原意图。文件冲突不覆盖；元数据变更需要新的配置位置，角色绑定修订继续复用原投影。

生成项目、scope、execution策略和Ergora归属记录；运行服务、凭据、平台模型设置仍归既有安装/F2管理，不写入项目定义，不自动启动服务。三个模板均可登记；训练runner/基线/实际实验仍由训练用例及后续F9负责。新正式任务核对注册已发布、Git根、配置/状态/安装位置与投影；旧任务快照继续恢复。

## 验收

- CLI/API登记等价项目，规范化定义和有效视图一致；未知字段/版本、不同Git根、无提交、能力/正式协议不足、缺检查、非法路径/策略拒绝。
- 既有冲突注册、重复tracker归属、旧revision和改变投影的原地修改拒绝；不执行检查或模型来验证注册。
- 发布前/中/后中断、重新打开State和跨进程恢复；冲突后保留pending及恢复信息；未完成注册不能启动新正式任务。
- 同一注册投影用于两开发模板的实际六阶段fixture；三个模板配置验收，旧任务选择及283冻结内容保持。
- 非editable包、适用完整回归、两OS精确候选CI和fresh-context独立结构/维护性审查；不把fixture当真实模型、GPU或外部服务验收。

## 进度

F1.2已交付：实现/测试提交`a6fd29162bc066cd8954275032bc103b3f11fc66`已推送且远端一致；最终本地验收、独立复审和精确两OS CI通过。F1.3继续独立实施。证据放忽略目录`.ergora/checks/f1-registration/`，源码/文档不放临时目录。

实现范围：新增`registrations.py`和严格schema；CLI/API共享register/status/resume用例。`projects.new_document`是轻量创建与完整登记共同使用的Git根/项目身份校验，不让基础项目反向依赖reference。`reference.registration_io`专用子进程持有布局、原scope/路径校验、有界读取与不可变发布；没有把原CONFIG全局加载进Web。执行桥仅对尚未冻结的新任务核对完整登记；`reference executor --project`使用保存的目录。README、两手册、项目定义手册和当前架构入口同步。

已执行：源码配置/结构/注册定向39项通过；注册与正式执行定向40项通过（包含两个统一注册六阶段fixture和三个准入拒绝场景）。随后增加恢复意图写入失败、相同旧文件显式导入要求、不同Git根/unborn/symlink边界及CLI保存目录入口验收，纳入当前wheel全量回归。fixture为受控命令/伪Codex协议执行，不代表真实模型/外部服务/GPU效果。首次生产包已构建并安装到专用验收环境，其后完整结果见下。

预审验收：当前非editable wheel（Python3.11开发验收环境）完整适用回归254 passed、18 skipped、36 subtests passed；独立基础依赖环境安装通过，337个应用/资源文件在源码、wheel和两套安装间一致。增量注册/静态边界35项通过。全量命令沿用`tests`及冻结upstream的`test_contracts.py`、`test_portable.py`、`test_workflow.py::AdapterTests`、`test_runtime.py`，PYTHONPATH仅指冻结upstream，未指src。命令与日志位于`.ergora/checks/f1-registration/`。这是独立审查前的历史候选；修正后结果和最终CI见下。

独立审查期间复现并修正一个大小边界：1MiB argv参数可写成超过安全reader上限的文件，原实现发布后无法status/resume。reference发布预检现按原write的UTF8/indent2/newline计算实际字节并在reserve前拒绝超过1MiB的文件；新增拒绝且不落DB/投影的回归，与等价legacy边界共2项通过。修正后的最终wheel结果见下。额外基础包5次CLI操作（verify/register/config/status/resume）和当前CLI保存执行目录的两开发模板六阶段均通过。首次全量结果仅对应预审包，不混作修正后证据。

最终本地验收完成：修正包SHA256`8c690d6b087e9f293ed5c40adaec3d0347e24d276f939d6832ad695a0e919750`，337文件×两安装与源码一致；完整适用回归255 passed、18 skipped、36 subtests passed（`final-wheel-regression.log`）。[独立审查](2026-11-02-project-registration-review.md)需求/维护性均通过，容量P2与两项重复清理均关闭，无未解决阻塞。精确候选[a6fd291的CI41448910719](https://github.com/626619403/Ergora/actions/runs/41448910719)两OS通过；官方API403限流后以官方HTML核对完整SHA及Ubuntu/Windows安装、冻结身份、回归和WindowsPowerShell安装升级步骤。证据为`ci-html-status.json`及原页面，F1.2交付完成。F1.3设计在[下一切片记录](2026-11-02-project-import.md)，继续实施，不把整个F1标为完成。
