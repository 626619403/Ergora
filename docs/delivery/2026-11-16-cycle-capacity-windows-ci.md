# 容量测试 Windows CI 失败：证据与修正片

2026-11-16。原7fc官方CI失败及六个Windows测试症状已保留；最小3行测试平台修正完成源码／本地复现／fresh两轴独审、普通合入与发布，准确修后e5自己的Portability run43840394544已终态 **8/8 success，含Windows**，本CI修正片门槛闭合。产品src与6cec589未变；S2隔离首稿和训练／模型质量不继承本片结果。

## 准确失败身份与原件

|对象|实际身份／结果|
|---|---|
|公开提交|`7fc42177db11fbfe4c9adb33342ecb5da4ed0434`，已核远端完整 OID；其中产品为 `6cec589f404b17f4828a70807d5e33d89fad3fa0`。|
|官方 workflow|[Portability run 43833234533](https://github.com/626619403/Ergora/actions/runs/43833234533)，准确提交自己的结果：7 jobs success、1 job failure，均终态。|
|失败 job|[Native (windows-latest, 3.12, group all)](https://github.com/626619403/Ergora/actions/runs/43833234533/job/133183447980)，job `133183447980`；plan 与 Linux 六组成功。|
|应用回归|第6步 `Native application regression` failure，开始 `2026-11-16T08:42:08Z`、完成 `2026-11-16T09:04:57Z`。官方输出为 **6 failed、1283 passed、1145 skipped、16 subtests passed，1367.19秒**。|
|原始证据|`.ergora/checks/design-capacity-integration/publication-r1/` 中 `checks-web-29.json`／`checks-web-latest.json` 绑定完整 head、run、8 job IDs 和终态；`run-page-terminal.html`／`run-annotations-terminal.txt` 保存官方页面与失败文本。此前 `windows-progress.html` 是步骤失败而安装器／job仍运行的历史快照，不能覆盖终态。|

先前官方 API 的 HTTP403／共享 IP 配额耗尽属于独立的观察限制；它既不是这六个失败的原因，也不是通过证据。额度恢复后官方 REST 已返回200，`jobs-terminal-api-response.json` 绑定准确7fc、run43833234533、attempt1及8个jobs，确认Windows应用回归失败、PowerShell安装器与artifact上传成功；`windows-annotations-response.json`列出全部6失败，另有3条 `Cycle activity requires original absolute control directory`。原403响应继续保留，不用旧 `04af234` 的 CI 代替本候选。

## 六个失败用例

均位于 `tests/test_training_runtime.py`，准确参数分列如下：

|测试节点|官方失败事实|
|---|---|
|`test_cycle_v3_completion_counts_assembled_measurement_and_all_operations[32767]`|`ValueError: Budgeted native operations require Linux; use WSL2`。|
|`test_cycle_v3_completion_counts_assembled_measurement_and_all_operations[32768]`|同上。|
|`test_cycle_v3_completion_counts_assembled_measurement_and_all_operations[32769]`|同上。|
|`test_cycle_v3_wrapper_failure_does_not_export_original_error[cancel]`|`completion.result.HasField('cancelled')` 为false；在到达原SDK取消叶调用前已返回请求拒绝。|
|`test_cycle_v3_wrapper_failure_does_not_export_original_error[operation]`|实际failure type为 `cycle_activity_request_rejected`，预期为 `cycle_activity_failed`。|
|`test_cycle_v3_wrapper_failure_does_not_export_original_error[inspection]`|实际failure type为 `cycle_activity_request_rejected`，预期为 `cycle_activity_capacity_exceeded`。|

官方注解、源码路径和已完成的本地依赖replay共同表明：wrapper测试保留的 `control_home:'/'` 在Windows路径规则下先触发原绝对control目录guard，尚未到达已替换的operation／inspection／cancel叶调用；assembled-operation测试则先触达原Linux-only预算boot-clock。未修测试的本地replay复现官方相同6个症状，具体配置与结果如下；它不是实际Windows执行或产品缺陷证据。

## 修正范围与验证

根 owner 从准确 `7fc42177db11fbfe4c9adb33342ecb5da4ed0434` 建立隔离分支 `fix/cycle-capacity-windows-ci-r1`。唯一改动为 `tests/test_training_runtime.py` 的3行：wrapper测试仅在非Linux且 `source != 'request'` 时跳过，保留可移植的request检查；assembled-envelope测试沿既有风格标记非Linux跳过。原有效操作依赖Linux boot-clock与POSIX根身份；修正不扩大产品支持，也不移除Linux容量／完整Failure树断言。

产品源码、CI、预算和fixture均未变，无新增未跟踪文件。固定差异 `.ergora/checks/cycle-capacity-windows-ci/r1/source.patch` SHA256 `770aca436a5a0a9c2beeea90d7a07c55c0214c83f4909b0fa5d74bf1a8dca4ca`；完整测试文件SHA256 `f98c4049945c7471d5996aa89bc71870cb19623ad817864d83cb7e66e3cc26d2`，输入清单为同目录 `source-freeze.json`。

诊断plugin `windows_dependency_probe.py`只为测试模块替换sys为win32、给budget_clock使用sys代理、给protocol使用PureWindowsPath；未修改SDK或全局OS。三场选择完全相同的原15节点：

|验证范围|实际结果|JUnit／runner时间|
|---|---|---|
|未修测试，本地Windows依赖replay|6 failed、9 passed；症状与官方6失败同一。|4.299秒／6.120秒。|
|修后测试，同一本地依赖replay|9 passed、6 skipped。|1.635秒／2.650秒。|
|修后测试，实际Linux依赖|15 passed。|2.026秒／2.946秒。|

原stdout／stderr、JUnit、完整argv、测试前后hash、PID／start ticks及wait后absent均保存在 `r1/`。上述本地replay不认证真实Windows通过。新的[fresh两轴独审](2026-11-16-cycle-capacity-windows-ci-review.md)已完成：需求approve／维护性approve，开放source findings0；文档的三类wrapper失败与已完成probe描述已同片复核关闭。源码普通提交 `0478a6dc21e0c65cae9027835ae122f35b3bb94d`，普通无冲突合入 `99c85030e35834a751ea6069e2310506a73ccf43`；完整测试文件仍为上述f98c SHA，`git diff --exit-code 6cec589 -- src`为零。修正没有产品源码变化。普通推送及远端完整OID已核；准确e5候选自己的CI已终态8/8 success，见下节；本地9过6skip和Linux15过仍只保留本地范围。

S2隔离R1已冻结7592，有112节点多label通过并集与新安装30过，但原结构Codex模板request-changes，正独立R2修复，全部未合入／发布或ready；此次 CI 失败与修正证据不转授 S2。原联合安装32过保留自己的本地范围；设计执行、schema3 训练效果和可信人类批准继续关闭。总体状态见[联合交付](2026-11-16-design-capacity-integration.md)与[当前计划](../PLAN.md)。

准确新发布：根已普通推送 `e5a35558f29f11eed62c6dd28450da6d39f232df` 并以git ls-remote核完整OID同一，`publication-r2/push.json`／`remote.json`保存原件。该提交包括0478修正／99c合入、fresh源码独审报告及已审PROJECTS82c／WINDOWS13ea。自己的官方run `43840394544` 绑定完整e5，`publication-r2/checks-web-00.html`／`.json`首次观察为plan1 success、7 in progress；当时尚无终态，后继8/8成功见下节，原7fc失败永久保留。


## 修后准确候选：官方8/8成功

官方 `publication-r2/checks-web-32.html`／`.json` 及 `checks-web-latest.json` 均绑定完整 `e5a35558f29f11eed62c6dd28450da6d39f232df`、run `43840394544` 与8个唯一job IDs。plan、Linux六组及Windows均为原生 `This job succeeded`，`all_terminal:true`／success8；Windows job为 `133207355066`。原HTML SHA256 `b1f639d3b37d87e8b8ff136854ea495f06131bab319250a229b2c4a766794e01`已与JSON原件核同一，有界观察器已返回0。

这认证已发布e5的本CI配置选择与Windows安装／应用检查，保留原7fc失败和本地replay的独立身份。当前USAGE七文件后继文档提交 `73b7d61c9b1f775ea14535483a773901e5ec6124` 尚未推送，不冒称它取得另一个CI运行。e5不含S2首稿，不能据此认证新source APIs／CLI／持久化或开放设计执行。
