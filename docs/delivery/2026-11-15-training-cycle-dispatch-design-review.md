# c1a2：总投递／固定run对账独立设计审查

日期：2026-11-15。审查者：fresh-context独立agent `training_cycle_dispatch_design_audit`。项目及文档归属为Ergora／`docs/`；本次仅审查设计、既有源码和原始验证材料，只写本报告，没有修改产品、安装依赖、运行服务／训练、提交或推送。

最终结论：**需求符合性approve，维护性approve；开放finding 0／0。** r1有一个P2并发合同缺口R1，r2已最小补齐并独立复核，**仅在设计层关闭**。本结论允许按修订计划实施，不代表一次投递、恢复、取消或自动训练循环的产品验收。

审查输入为原始要求：持续完成计划；自动循环保留真实baseline／质量与evidence／人工release、单次attempt及连续预算；kernel专家保留v3；每大项独立审查。已读根及`src/ergora/AGENTS.md`、当前`docs/PLAN.md`、组件协议“执行和证据／配置和持久格式／脚本和检查”，以及maintainable-project-delivery及其独立审查brief、ergora-codebase-quality的三份职责参考。

固定基线／当前HEAD均为`836179e9ff3eae0795f0c22bf4c58f0bab1ea777`，分支`refactor/architecture-foundations`。初审只有三份未提交文档：`docs/PLAN.md`和下表两份新文档；产品、测试、依赖没有本片差异。完整r1文件清单、字节数与SHA见`.ergora/checks/training-cycle-dispatch/design-snapshot-r1.json`，tracked差异见同目录`design-diff-r1.patch`；两份新文档均直接全文检查，没有把tracked patch当成全部差异。r2是两文档的**差量身份表**，与r1合并核验的16项全部匹配。

|最终审查文档|字节数|SHA256|
|---|---:|---|
|`docs/PLAN.md`|74670|`c8289a7ed04d53c73db67f3eede031aa033524fffed5080d61409ec72897e44c`|
|`docs/plans/2026-11-15-training-cycle-dispatch.md`|10022|`6d42292c23e5ff74bb07386df786205f7b7fce496401063fb025faa5e6b53e38`|
|`docs/delivery/2026-11-15-training-cycle-dispatch.md`|3094|`9aba3fb30167dced6afa4a1f525b681afd66bbbf4e652077036d6a05a3bb08df`|

直接检查了父合同`docs/plans/2026-11-15-training-cycle-controller-contracts.md`、`training-cycle-workflow.md`，四个主要owner `training_cycles.py`、`training_execution_protocol.py`、`reference_training_runtime.py`、`reference_training_worker.py`；沿实际调用补读原`reference_training_submission.py`、`reference_training_budget.py`、`reference.py`、`training.py`、`state.py`、`budget_clock.py`。现有验证接缝为`tests/test_training_submission.py`中出生同意／不可变准备／完整binding／父run gate／停止排空／普通operation窗口与取消用例，以及`tests/fixtures/training_cycle_operations.py`和`training_controller_service.py`。这些源码与fixture属于基线，尚无本片producer实现。

## R1：前置lookup的迟到拒绝会阻断并发合法投递（P2，设计层已关闭）

原位置：r1计划第24–25行，对应r2的[第24行](../plans/2026-11-15-training-cycle-dispatch.md#原件和顺序)。r1在“没有attempt时先lookup”后允许写preexisting拒绝，只明确attempt在短reservation内发布，没有固定拒绝落盘前须重新核对本地事实。

可达交错：B初读无attempt，发出lookup；A随后claim唯一attempt并start；B的lookup这时看到A的合法run，按旧“无attempt”判断写拒绝。A稍后保存receipt，或仍在等待start回复。结果可能是有效receipt与拒绝并存；既有`CycleAdmission.bind`在`src/ergora/training_execution_protocol.py:468`检查到任何拒绝路径就禁止子动作，同一次合法投递因此被永久阻断。这是设计中允许的交错，未声称已在新产品中复现。

最小修正已经落入r2计划第21、24、30行：

- 前置lookup仅取服务事实；拒绝和claim在同一短SQLite reservation内决策，进入后先重读完整intent／attempt／receipt／rejection。
- attempt一旦出现，即使其创建者尚未收到start回复，也丢弃旧“无attempt”拒绝决策，转只查；preexisting_run／lookup_rejected只可在没有attempt且无其他终态时保存。
- receipt／拒绝也在同一reservation中验证互斥后无覆盖发布；相同终态只同步重读，矛盾终态不写；RPC发生在reservation结束之后。
- 已加入上述迟到lookup交错的实际验收要求，不能只验证“两个调用合计一次start”。

独立复核结论：修订使“无attempt”的拒绝前提与落盘共享同一序列化点，不必持SQLite跨网络或增加另一把长期投递锁，R1设计层关闭。实现仍须实际验证A未收start回复时B不会先写拒绝，以及同一receipt竞争的字节／inode／clock保持。

## 恢复合同与职责结论

|检查点|独立判断与源码依据|
|---|---|
|唯一claim和原件|计划第21、23–30行在既有`training_cycles._record_bytes`的无覆盖link／fsync（`src/ergora/training_cycles.py:290`）上增加短claim；失败后不回收attempt。共享attempt期望值回到已有stdlib `CycleAdmission`，与原`bind`第462–467行使用同一身份，不需要另造账本／通用publisher。拒绝reason／run与attempt关系已明确，网络异常不会被保存为服务拒绝。|
|无receipt恢复|计划第28、34–36行明确先从latest describe取得first_run_id，再固定首run检查完整started input、memo、type与queue。continue／retry的latest后继不能成为receipt；原首run关闭可以认证历史，但不能给后继执行权。NOT_FOUND或证据不足保持unknown，没有应用层再次start。|
|人工复用／reset|协议独占ID、永久唯一attempt和REJECT_DUPLICATE是支持范围的前提。探针证明人为ALLOW_DUPLICATE重开first_run_id，故仅metadata无法排除相同材料／memo的完整重放；计划已承认这一限制，没有把first_run_id当全历史唯一性证明。在该可信边界内无需为不可识别的人为重放虚构检测算法；已知复用／reset保持unknown。reset没有实际探针结果，本次不授予其行为验收。|
|已有receipt及执行gate|已有receipt或可信原启动／SDK活动run hint只查其精确run。`reference_training_runtime.lookup_controller`第61–77行原固定RUNNING及完整input／memo／type／queue检查继续作为执行gate；允许关闭run的投递查询仅复用验证，不放宽该状态要求。`description`后固定handle再取history可以防止latest漂移。|
|普通与观察窗口|计划第40–42行将submit固定为原compute∩control的同一BOOT窗口；父pipe／wait、S和H消费同一payload，原compute耗尽不spawn。reconcile独立固定1–60秒观察截止，允许预算结束后补同一receipt，但没有start、ordinal或执行分支。与`budget_clock`原不可续期语义及现有`cycle_operation_remaining`职责相容。|
|stop与取消|SDK start期间持父共享许可，最后核stop／revision／ready／原窗口；stop可见后的新动作被拒绝，已在途RPC仍可能晚到并保持unknown。父取消继续使用`_CycleOperation.run`第135–148行shield保留真实spawn、S的`processes.run(supervised=True)`及唯一reaper；receipt持久化与进程回收各自观察。设计没有把客户端取消称为服务端无副作用。|
|SDK和依赖owner|SDK start／对账及选定native installation／config初始化只在H；`training_cycles`不反向导入worker，stdlib protocol不依赖SDK／State，cold本地观察仍可无SDK。沿已有operation／runtime owner扩展有真实caller，未见为了复用数字制造的文件、接口或第二调度器。实施时仍须核选定环境在相关native模块首次导入前生效。|
|范围与用户要求|新服务、normal／stop独立配额、标准sandbox总Workflow、首子活动receipt竞态消费者、每轮测量接受与后继派发、公共入口及CPU两轮均明确留待后续。父合同的真实baseline／质量oracle／accepted evidence／人工release及v3 kernel专家没有被本片投递协议替代。|

## 实际检查与未验范围

本次只读检查了r1快照16项、r2两文档差量、完整tracked／untracked范围，合并后的16项字节数／SHA全部匹配；两新文档4个本地文件链接均存在。辅助解析最初误把r2差量当完整snapshot、把probe带warning的stdout当单份JSON，分别只读失败；按实际格式重读后通过，未修改原件。

真实证据是已保存的`sdk-history-metadata-r2.py`、`-r2.json`、`-r2-command.json`及stdout／stderr。本次没有重跑探针。JSON与stdout最后一行逐对象相同；stdout之前确有一条workflow-task-not-found warning，stderr空。4个case实际覆盖普通初始run、人工ALLOW_DUPLICATE、continue-as-new、retry；脚本第66–89行确实使用公开SDK及固定run history。记录为SDK1.34.0／CLI1.9.1／Server1.32.0，probe 4.977秒、驱动6.324秒、退出0；记录的server PID当前`/proc`不存在。r1收尾失败原件仍保留，不作为成功。

另只读核对已安装SDK的`WorkflowHandle.run_id`／`result_run_id`说明、start request构造，以及protobuf对`original_execution_run_id`／`first_execution_run_id`的说明，与已记录metadata吻合；SDK字段说明不替代reset实测。

**尚未验证：** 新producer／claim／拒绝与receipt并发、真实SDK start丢回复后的产品恢复、关闭run查询实现、新的S-H SDK阻塞／取消、选定native环境初始化、core／SDK非editable安装、适用回归与自身模板、独立产品审查、独立cycle服务／sandbox Workflow／实际子活动receipt竞态、跨worker／server重启、完整CPU两轮，以及真实GPU训练、质量和性能。现有固定run gate／operation用例只证明其基线范围，不能继承为新实现通过。后续按计划实施后，须用本片实际产品及原接缝取得这些证据；自动派发在父合同的服务与停止边界闭合前继续关闭。
