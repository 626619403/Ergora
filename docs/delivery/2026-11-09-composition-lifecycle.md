# CR4：组合运行桥的服务生命周期与恢复出口

日期：2026-11-09。状态：C1最小修复、50项新包合同、实际四任务Supervisor旅程及自身结构模板通过；新独立本地两轴通过，精确交付在途。固定基线`8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`（CR3c已精确交付，自己的双OS CI42548357813及独立远端终结通过）。此片优先复用CR3c同一369文件非editable发行；无必要不修改生产/测试/依赖/CI或283冻结文件。

## 范围与可验收出口

1. 使用公开services命令启动原Supervisor的Temporal、双版本worker、A2A和常驻executor；幂等start保持PID，未选MLflow/training-worker保持停止。Supervisor拥有进程组、停止和日志，不由探针直接替代服务管理。
2. 真实v2任务运行至原待批计划时，正式shutdown整个owned栈。状态查询必须实际失败且不能自动启动服务；同一DB和目录重启，原run/plan/两份原receipt保持，重复start不重派，再经原test-operator owner批准跑完。真实SDK核同legacy不同完整admission的原历史拒绝，不改持久信封或历史。
3. 独立新v2任务中review返回request-changes，原收据FAILED/外层BLOCKED，不能出REVIEW_READY。另一新v2任务在真实review进程运行时通过公开cancel发原signal；monitor/fence停止进程组，CANCEL_UNCONFIRMED不能冒称已停。待原终态receipt与external-status确认后显式reconcile，仅释放原claim，保持原outcome及候选；不得迟发文件写入。
4. 新v1任务沿原队列/请求根/六阶段成功，3条v2与1条v1的完整原输入、history类型/队列、SDK replay及回执摘要分别核验。删除原manifest和活动定义库后仍可执行。单只读叶范围不扩大为AC4嵌套执行。
5. 正式shutdown本次owned服务，核PID/端口/Unix socket退出并保留数据库。源码/wheel/安装身份保持；记录实际命令、耗时、首轮失败、限制及结果。新fresh-context独立两轴审查，按大项约定实际使用Ergora自身审查模板核新增材料；普通推送/本片检查按实际变更范围完成。

探针与缓存在忽略的本项目验收目录，运行库用home下独立持久目录和短Unix socket路径，既不依赖tmp，也不接管已有服务。执行前核默认端口空闲。协议Agent是确定性程序，test-operator经原owner合同批准，不推导真实模型质量/业务人工验收或OS隔离。缺少主机权限不硬改宿主。后续AC3c.4再核完整备份/离线恢复，AC4负责多成员/有界串并行。

首轮R1探针在原`supervisor_config`生成程序配置时因手工装配漏建`config/supervisor.d`而失败，服务尚未启动。原日志及持久装配目录保留；R2只补测试装配目录，在全新home验收根重建，生产/模板未修改，不把装配失败记为流程通过。

独立审查C1/P1发现公开取消dispatch仍将legacy投影传给严格完整历史核验器，v2真实原payload不能匹配；最小修正使用`submission.input.document`，原cancel仍用legacy投影计算ID和signal，不放松历史身份。先用旧安装包和新增跨应用回归取得红例，再保留真实Supervisor旅程的原拒绝；源码/包和后续新身份分别保留。新增回归只覆盖v2正常/丢ack沿原signal恢复及same-legacy另一完整admission在attempt前拒绝，复用既有SDK fixture，不扩CI矩阵。


C1旧包跨应用回归实测 **2 failed /1 passed /19.06秒**；R2真实Supervisor旅程也在公开cancel以同一JSON identity错误退出，原不可变取消intent已保存，attempt/result均不存在，没有发出signal。它此前的整栈同run恢复和拒绝审查原件有效，但不能把取消及v1未执行部分记为通过。finally只停止本次owned服务。

R2附加进程探针在服务socket消失后两秒仍观察到4个原monitor相关进程而失败，稍后按相同PID/starttime重核均退出；原失败与后核各自保留。这说明停止服务不等于外部作业已确认清理，不能以Supervisor confirmed覆盖CANCEL_UNCONFIRMED或unknown。R3改为从真实Supervisor PID递归采样后代并保留已观察的重归属进程，等待旅程结束再核退出；仍明确采样无法证明捕获所有短命进程。

最小单行C1修复后，R3新发行 **369源码/wheel/安装一致、283冻结保持**；wheel SHA `aaa55f011bbc8ddcdfead0e1d59859695f07f6d7f80ddbdb309d26e37d98e703`。四文件改动包括一个生产参数、共享fixture解耦及三参数v2取消合同回归；新包绿例、完整Supervisor旅程和自身模板结果见下方。R3的确定性Agent只在验收副本将late-marker延至10秒，公开cancel到原signal需要真实CLI/RPC时间；结束后等10.3秒核marker缺失并另核进程，不把原件延时设置当产品修正。


## 新候选实际验收

- R3非editable安装命令：`python -I -m pytest -q tests/test_task_cancellation.py tests/test_composition_tasks.py::test_composition_cancellation_preserves_full_input_and_original_signal_recovery tests/test_architecture_boundaries.py`，另含本片持久basetemp；**50 passed /320.19秒，exit0**。完整argv保存在验收缓存`r3/check-command.json`。这包括旧取消合同及新正常/丢ack/不同admission，不能把原旧包失败改写为通过。
- [真实Supervisor旅程](evidence/2026-11-09-cr4-lifecycle.json) **428.35秒，exit0**；原待批v2整栈停止后查询实际失败且没有自启动，同DB重启原run/plan/两receipt保持、重复start不重派，再经原owner批准成为REVIEW_READY。相同legacy但不同完整admission查询真实拒绝。
- 另一v2审查request-changes产生FAILED/BLOCKED；活动v2取消实际投递ack但`cancellation_confirmed:null`，review终态CANCELLED，原outcome保留CANCEL_UNCONFIRMED。外部状态随后确认无未决项，显式reconcile仅释放原claim且不改outcome；10.3秒后没有迟写marker。新v1沿原队列/六阶段成为REVIEW_READY。
- 四条完整原history分别161/167/162/161事件，完整输入、v2/v1队列及SDK replay各自通过。[只读原件重核](evidence/2026-11-09-cr4-evidence-check.json)：**24receipt/87artifact/4owner-plan绑定**；4原claim中仅取消task释放，其他3 active保持，不能把关闭正常run当自动释放。
- 正式services最终shutdown confirmed；附加只读观察104个原daemon及递归后代的PID/starttime，最终0live，7233/8233/8765关闭、managed socket消失，Temporal数据库保留。采样不保证捕获所有短命进程；不把服务停止替代外部清理证据。

R1装配失败、R2实际C1拒绝及原进程探针两秒窗口失败均保留；新成功只属于R3新包aaa55f0及其源身份。[独立报告](2026-11-09-composition-lifecycle-review.md)已核上述原件，C1实现与实际行为修复；真实自身模板与分页核验也已完成，最终文档scope和精确交付另行记账。完整联合备份/恢复出口按AC3c.4另片实施。

自身结构模板真实调用 **116.20秒approve**，Codex `gpt-6.1-sol` / high / task-MCP，run `3d2ec24599bc4af0b2e706d18d77bacd`：[身份](evidence/2026-11-09-cr4-self-review-identity.json)与[原结果](evidence/2026-11-09-cr4-self-review-result.json)。完整附件150147字节，13源/测试/原调用者与验收程序身份保持；分页原件已由独立者完整重组核验。不宣称该模型自己执行测试或验证所有未提供依赖，Claude不可用按用户授权回退，不声称模型错误独立。


自身模板的E1非阻塞观察已用独立原件处置：旅程汇总中的字面量wheel SHA与工作区hash自身不足以证明执行包。R3旅程前`package-identities.json`与结束后的`package-identities-final.json`均重新读取实际wheel、所用非editable venv及完整源码，**369文件逐项相等，283冻结与基线保持**；两轮SHA都为aaa55f0且完整文件map相同，真实入口显式使用这个venv。独立者也重算同一全树，足以关闭本次执行身份缺口，无需改写原汇总或重跑未变行为。原模型观察与其范围保留，不把汇总字段本身当证据。

独立者另外核原MCP七个唯一连续页至null（另有一次相同首页重读及首次短路径拒绝），逐字节重组150147字节、scope/prompt/result及13源身份相符；首次拒绝保留，后改完整虚拟URI成功，无截断。新文档静态与完整scope终值及普通提交/自己的必要CI/即时远端仍待最终登记。

最终本地静态：8份Markdown、91个本地链接/锚点、75条公开CLI parser及`git diff --check`通过；新独立者已核完整本地行为/结构并关闭C1，E1以实际安装全树处置。普通提交前将stage完整16文件（含前片审查追加及四份公开原件），核`git diff --cached --check`及精确文件身份；自己的CI与远端终结另行登记。
