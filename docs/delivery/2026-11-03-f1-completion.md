# F1 阶段验收与下一步

日期：2026-11-03。分支`refactor/architecture-foundations`。F1.1/F1.2/F1.3全部交付完成；最终运行/测试提交`4ffcfdde0c728cf5904690decd165e26e1a9bb7d`已推送且远端一致。本地安装包、完整回归、CLI旅程、精确两OS CI和独立最终交付复核均通过。

## 实现与结构

|切片|实现/测试提交|行为与证据|
|---|---|---|
|F1.1|`d914ea724e87495fb5efcd92e12f50b5931fc42c`|有效工具绑定、逐层来源/校验/修订/摘要，CLI/API/页面一致，独立与正式调用冻结快照；[记录](2026-11-02-project-configuration.md)、[审查](2026-11-02-project-configuration-review.md)|
|F1.2|`a6fd29162bc066cd8954275032bc103b3f11fc66`|统一注册模板/角色/执行位置/检查/策略，reference单向不覆盖投影及pending/恢复；[记录](2026-11-02-project-registration.md)、[审查](2026-11-02-project-registration-review.md)|
|F1.3|`62c4d696396942fbad86fc21f56f9e854e3ed4d1`；补修`4ffcfdde0c728cf5904690decd165e26e1a9bb7d`|旧注册只读预览/差异、绑定控制home/修订/源字节身份的显式采用，旧文件保持及共享恢复；[记录](2026-11-02-project-import.md)、[审查](2026-11-02-project-import-review.md)|

项目和bindings仍归`projects`，完整注册/采用归`registrations`；CLI与Web共享用例。`reference`持有原布局、安装身份、校验与不可变文件原语，专用子进程避免Web混用CONFIG/STATE；新任务由执行桥冻结配置，旧任务保留原runtime/快照。没有新增表、依赖、通用插件或第二个执行引擎。当前依赖图与扩展边界见[架构导航](../architecture/current.md)，格式/摘要见[身份契约](../architecture/contracts-and-identities.md)。

## 最终验收

- Tracker补修后的非editable wheel SHA256为`4fa5adac91721adfd6e274a544336d492800494b82339658d321ff63d0b9dd63`；源码/wheel/开发安装/基础安装337文件一致。独立的`reference verify`确认冻结参考283文件保持。 本地全量回归环境为Python3.11.15，独立基础CLI环境为Python3.12.3；两套均安装同一wheel，无editable或应用src覆盖。
- `tracker-wheel-regression.log`的完整Linux适用回归为281 passed、18 skipped、36 subtests passed（147.11秒）。覆盖两个开发模板经新注册及实际旧注册导入后的六阶段fixture、候选证据、旧快照/取消，以及格式、修订、源变化、发布中断与跨进程恢复边界。
- `tracker-base-journey.log/json`的独立基础环境8次CLI旅程通过预览、显式采用、状态、恢复、角色修改和修订视图，确认旧文件字节保持；CLI/API预览与注册等价由集成测试核对。
- 各大项使用不同fresh-context审查者。F1.1两项P2、F1.2容量P2/重复清理、F1.3紧凑旧JSON容量P2及tracker末尾LF合同P2均修正并独立源码复审关闭；无未解决阻塞。Tracker补修后的包/两安装、281项/283冻结身份/8次CLI、新提交Git归档/远端和精确CI已完成独立最终复核；结论为需求与维护性均通过。
- 补修候选已推送且远端一致，[精确两OS CI41485234297](https://github.com/626619403/Ergora/actions/runs/41485234297)通过：Windows job125413705473含安装/冻结身份/适用回归/PowerShell5.1安装升级四步骤，Ubuntu job125413706105含前三步骤。官方HTML完整SHA与实际步骤均已核对，来源清单为`tracker-ci/ci-html-status.json`。

F1.2最终验收为255 passed/18 skipped/36 subtests，精确CI[41448910719](https://github.com/626619403/Ergora/actions/runs/41448910719)两OS通过。F1.3补修前62c候选的wheel `6d1ef44aa2d71988e21930cc7908aa5fb6e398bf057106d8907b3e8e79e5319f`、279 passed/18 skipped/36 subtests及[CI41480569812](https://github.com/626619403/Ergora/actions/runs/41480569812)只保留历史范围，其包和清单已另行归档。详细演进证据保存在各切片记录，不套用到新候选。

长回归和CLI由实现者运行；审查者另核对调用链、独立边界探针、文件/包身份与实际证据。受控command/伪Codex的六阶段fixture不代表真实模型质量或外部服务/GPU验收。Windows CI验证原生控制面支持子集，完整六阶段仍限定Linux/WSL2。多文件与SQLite是有记录的可恢复发布，旧注册写入者需先停止，导入不迁在途任务、不自动切换服务。训练模板登记不表示runner/workload/基线/实验已初始化。

## 使用与后续

[项目定义手册](../PROJECTS.md)提供register、import-reference默认预览/带SHA采用、registration状态和resume-registration恢复。两本[日常手册](../USAGE.md)与[Agent手册](../AGENT_BACKENDS.md)已同步。轻量`project add`、旧参考命令和已有任务保持兼容。

下一项按[详细实施计划](../plans/2026-11-01-all-in-one.md)进入F2安装、doctor与服务管理。先盘点既有安装器、组件描述和Supervisor入口，拆出轻量/开发/实验可选组合的首个可验收切片；明确安装、认证、连通和任务可用性，再推进F3正式任务入口、F4运行与批准页面。这些后续能力尚未实施。

收尾检查：相对最终运行/测试提交`4ffcfdd`仅有docs状态/交接差异，185个本地链接及`git diff --check`通过；最终源码保持上述验收身份。交付位于[远端工作分支](https://github.com/626619403/Ergora/tree/refactor/architecture-foundations)，保持独立分支交接。
