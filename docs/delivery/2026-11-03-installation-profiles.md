# F2.1：明确的安装组合

日期：2026-11-03。分支`refactor/architecture-foundations`，源码基线`b5e018337cc54d8fb786f779ee1756d5b1e7f3c9`；工作区干净，F1已交付，最终运行代码为`4ffcfdde0c728cf5904690decd165e26e1a9bb7d`。用户授权继续既有实施计划；本切片属于F2，不变更正式六阶段及283份冻结参考资源。

## 观察与决定

现有Linux/Windows安装器已有用户目录、重复升级和外来入口保护，基础安装均选web，可通过独立参数加gepa/temporal。工具目录由`components.json`集中，但没有可发现的安装组合；现有doctor只给安装探测及部分not_checked，服务仍走原agentflow/Supervisor。

F2拆为：F2.1安装组合；F2.2版本/认证/连接/任务可用性及修复指引；F2.3显式所选服务的status/start/stop/logs与停止反馈；F2.4Linux/Windows安装升级、离线/缺服务/缺认证及服务旅程综合验收。后续节点分别验收，不把本切片标为完整F2完成。

F2.1使用现有组件描述的新增安装配方：control=web，development=web+temporal，research=web+temporal+gepa。这是SDK组合，不意味着外部运行时、模型认证或GPU已就绪。正式六阶段继续要求Linux/WSL2及参考运行时；Windows可安装相同控制面/SDK并连接支持的远端服务。

## 范围与复用

- 在`components.json`集中组合ID、extras、说明及手册入口；现有`components/tools`、CLI及Web提供可发现的只读描述。
- 现有Bash与PowerShell安装器直接读取同一配方，增加--profile/-Profile。默认control与原无参数行为相同，保留--with-gepa/--with-temporal及对应PowerShell参数，按集合叠加；无新安装框架、依赖或DB格式。
- 先校验配方/前置工具，再创建安装目录。未知配方不落安装文件；外来命令保护、软件/数据分离保持。安装不启动服务、发起模型调用、安装全部可选工具或重配用户项目。
- 离线依赖由pip既有PIP_NO_INDEX/PIP_FIND_LINKS支持；需要完整预备的构建/运行依赖缓存。缺缓存应保留pip的实际失败，文档给出补齐方式，不能当作已安装。

预计改动：`src/ergora/{components,tools,cli,web}.py`、`data/components.json`、两安装器、相关Python/PowerShell测试、README/两本公开手册/Windows手册及当前架构。所有新增描述有真实安装或CLI/API消费者；不引入通用插件或第二条服务管理链。

## 验收计划

1. 三组合由同一描述驱动，CLI/API结果等价；返回副本，查询不写项目绑定。
2. 真实Bash入口以受控安装后端验证三组合、旧参数叠加、未知/缺失配方拒绝；保留原重复升级/符号链接/外来入口回归。
3. 非editable wheel、独立数据/安装目录完成实际Linux干净安装、组合升级、重复升级和缺缓存失败；数据保持且不启动服务。Windows真实PowerShell5.1 CI验收组合安装升级及外来入口保护。
4. 安装包与源码/两安装身份、冻结283文件、适用完整回归及精确两OS CI通过，安排新的fresh-context独立结构/维护性审查；按已有授权提交推送及核对远端。

## 进度

已完成源码/调用者盘点与分步计划，开始实施；当前尚无新运行验收结论。证据使用忽略目录`.ergora/checks/f2-profiles/`，不与F1包和CI混用。下一项F2.2继续诊断状态，F2.3才接所选服务管理。

实现与定向验收：共享配方、两安装器、tools profiles及GET /api/installation-profiles已接入。新增公开行为回归先在原实现得到5 failed/5 passed（缺发现入口、组合参数及去重），修正后相关组件/安装器/Web共23 passed。Bash语法检查通过；PowerShell原生行为留实际Windows CI，不用Linux模拟替代。当前wheel SHA256为`44ab7d26ccd9ef5b79840e75bf7ffca1ab12da152a997cfb8e2dc6177ed2a934`，新全量回归与实际Linux离线安装旅程进行中。

## 本地完整验收与审查准备

- 非editable wheel SHA256 `44ab7d26ccd9ef5b79840e75bf7ffca1ab12da152a997cfb8e2dc6177ed2a934`；源码/wheel/Python3.11.15开发安装/Python3.12.3基础安装337文件一致。基础环境无Web/Temporal/GEPA仍能查询配方，且不创建--home目录。冻结reference verify为PASS283、runtime_started=false。
- `wheel-regression.log`：288 passed、18 skipped、36 subtests passed（149.49秒），仅现有FastAPI/Starlette弃用提示。命令沿用F1全量适用范围；PYTHONPATH只选冻结upstream，不覆盖应用src。
- 实际Bash安装旅程使用Python3.12.3、独立持久配置/数据/带空格及Unicode路径和完整预备wheel缓存，PIP_NO_INDEX=1且禁用隐含pip缓存。control→development→research→research重复/旧参数叠加→control共5次安装与22次CLI通过；实际SDK版本依次为Web0.162.0、Temporal1.34.0、GEPA0.1.4。项目绑定/revision与数据哨兵保持，受控command Agent调用通过；无模型调用或服务启动。缺构建依赖的空缓存明确失败、未创建CLI入口。
- `linux-install-identity.json`另核实际安装器的337资源与源码/上述wheel一致；向较小组合切换保留已装SDK的实际行为已写入手册。实际源码安装器重建wheel，不把其ZIP时间戳等同于分发wheel SHA。
- 已核19个变更文件、206个本地链接、Python AST/JSON/Bash语法及diff检查。包、旅程及当前差异证据在`.ergora/checks/f2-profiles/`。

当前需求与实现已自查，准备新的fresh-context独立审查。Windows真实PowerShell5.1、精确两OS CI、最终提交/远端仍待；不将本地结果套用到未运行的平台。不启动或升级已有用户服务，不变更已有用户配置。本切片不实现F2.2/F2.3，也不标为完整F2完成。

独立审查已启动（新的`/root/f2_profiles_review`），源码/测试冻结；先提交候选以运行真实Windows和两OS CI，与审查并行。候选推送不代表本切片完成；发现问题仍修正并重验，最终审查报告与精确候选CI将单独收口。
