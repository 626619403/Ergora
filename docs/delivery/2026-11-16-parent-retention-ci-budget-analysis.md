# 父请求留存发布前的 CI 预算有限调查

日期：2026-11-16。此为只读成本调查，不是独立审查或实施批准。仅新增本报告，未改产品、测试、CI、共享 PLAN，未运行测试、collector、网络、安装或提交。已读根／scripts AGENTS、PLAN、组件协议“脚本和检查”、[测量成本调查](2026-11-16-measurement-ci-budget-analysis.md)与[已实施再平衡](2026-11-16-measurement-ci-balance.md)。调查开始 HEAD 为 a0d533d，期间主控推进至准确 `c4c0946060ba781eb8b2cb2e7e9d3ad2798dcd5a`；下列候选文件在两者相同，不能把官方 a0d 的结果转授后继。

结论：现有证据支持最窄的单文件候选——将完整 `tests/test_composition_tasks.py` 从 group5 移至 group1。它旧完整50节点／79.714秒，正文逐字保持，显式 fixture 导入支持独立模块选择。`test_services.py` 是闭包更简单、旧成本较小的另一单文件候选；若主控希望为新增22保护及已观察远端时长方差分散更多现存工作，可考虑 composition_tasks＋services 两个完整文件同由5→1，闭包依据分别见下文；但没有实测证明任一方案足够。此处不要求新 job、加时、删保护或全组重测，主控另决策实施并安排 fresh 独立审查。

## 当前官方证据与新留存成本

已有原件 `.ergora/checks/cycle-measurement-collect/publication-r1/20261116T005135Z-summary.json` 的观察时间为 `20261116T005135Z`，HTTP200，准确候选 `a0d533d13b4aae9441e3b6b920b27c2534353b87`，自己的 [43780806957](https://github.com/626619403/Ergora/actions/runs/43780806957)、push／attempt1。六 Linux 均 success；Windows 仍 in_progress，整 run 无终态。

|Linux组|整个 job 秒数|
|---|---:|
|0|415|
|1|238|
|2|619|
|3|403|
|4|358|
|5|1123（18分43秒）|

group5准确起止 `00:30:59Z → 00:49:42Z`，距原20分钟77秒；这是含安装／reference verify／回归／上传的整个 job，不是 pytest 独享预算。原 `.github/workflows/portability.yml` 保持 Linux20分钟、Windows30分钟。Windows在途不能写八job成功。

父留存固定产品 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3` 尚未发布；新增22保护归当前 group5 的 `test_training_submission.py`。既有交付记源码22／88.09秒、安装22／116.27秒；直接核安装原件 `.ergora/checks/cycle-parent-request-retention/package-r3/installed-retention-r3.xml` 为22项、零失败／错误／跳过，suite116.263秒。它是本机选集，不能把88.09或116.27线性加到远端1123后预测成功／超时；runner、fixture摊销、候选输入和安装开销均不相同。

## 完整历史 JUnit 的范围与整文件候选

只使用指定旧原件 `.ergora/checks/ci-training-shards/installed-py311-r1/group-5/ci-results/junit.xml` 及同目录上层 `complete-summary.json` 定位。旧基线 `b6538cf0e5026f27c1c5983aa586926a666e4788`，539节点＝537通过／2跳过，suite2444.931秒、外层2446.667秒、exit0，结束输入未变。旧组含后来已移走的 release／external_status／cancellation／work_agents，2444.931不是当前group5成本。以下均完整文件的 testcase time 合计，含JUnit计入节点的fixture时间，非纯call，也非远端可相减固定量。

|完整文件|旧节点数／秒|b653至准确当前HEAD|候选判断|
|---|---:|---|---|
|composition_tasks|50／79.714|字节相同|首选单文件5→1，三者中旧已知工作最多|
|services|20／52.196|字节相同|另一单文件选择，独立function fixture，旧工作较少|
|training_runtime|26／46.019|已变|不优先用旧成本支持搬移|
|training_preparation|15／76.380|字节相同|本次不扩大其fixture调查，不优先于已核候选|
|task_budget|12／48.461|字节相同|同上|
|training_submission|111／1135.248|已变|新增测量与留存均在此，旧成本不代表当前，不建议整文件搬给group1|

现组5其余旧完整文件：candidate_observations20／11.391秒，handoff56／0.519，project_issues14／8.275，state_backups21／2.878，training13／8.722，training_baseline6／8.983，training_runner7／42.713，training_evidence13／21.611（正文已变），task_evidence_index36／0.596，task_submission_locks6／30.415。除已说明三项变化外，当前组5其余13文件均与b653逐字相等；这不代表其产品依赖保持或现在节点数相等。

三个比较文件同时核 b653、准确 a0d533d 与准确 c4c0946：

|文件|SHA256|
|---|---|
|composition_tasks（三者相同）|`b026fd9e658b21a07592783fd20dadf038ada4061ffe282c69fe5a028398de60`|
|services（三者相同）|`f15366e359c0362866b609fa460c0d2267ff4a368068d33409e77539b011c043`|
|training_runtime（旧）|`d833cba26db66dedb83c98736a32c7463ca08bb93acf745466a39df61ceb3da4`|
|training_runtime（a0d及c4c）|`4b5d7ed4c3fc8d6fcae079821ccfa0617635aedbc6f0cf73c9c803437883e361`|

composition_tasks 显式导入 registrations 的 installation／registration、task_creation 的 creation_project、task_runtime 的 runtime_client、task_submission 的 native_client、task_cancellation 的 cancellation_client，以及 workflow_definitions 的构造helpers。composed_creation、creation_project、registration和三个client均function scope；installation是module scope，按请求模块构造临时安装，不要求与submission测试同组或同进程。导入模块提供fixture，不要求收集其测试正文；group1本来已含registrations。该闭包未见依赖group5共同进程的共享运行对象，静态检查仍不能证明新组合行为通过。

services不导入其他测试模块，stack为function scope，独立临时目录／配置／state／supervisor，Linux及supervisor可用性由原fixture检查，finally请求shutdown并等待socket消失。它比composition_tasks闭包更窄；但旧52.196秒更少，仍不能保证填补新增成本。training_runtime自有module installation，并导入training及reference fixture且正文已变，因此不优先。

只移composition_tasks，配置文件数由13／14／12／18／13／16变为13／15／12／18／13／15；只移services亦相同；两者同移则13／16／12／18／13／14。均保留六组86唯一文件。两文件旧case合计131.910秒，仅说明存在更多已知串行工作可分散；1123−79.714、238＋79.714或1123＋116.27−131.910都不是新远端预测。不能据此宣布单文件不够、两文件足够。

## 后续最小检查及未知

现有 `scripts/ci/run.py --group all --collect-only --output …` 记录完整收集；`pytest_phases.PhaseLog.pytest_collection_modifyitems` 先记coverage，再对Linux组验证范围、重复文件、缺失路径、收集文件未登记和空组选集，并按完整路径选组。runner一个pytest子进程，无xdist；Windows all不传ci-group，插件在读Linux JSON前返回。

若主控采纳，先固定实际最终候选，只改所选整文件JSON归属，再复用既有collector与selector接缝核前后完整node multiset相同、六组覆盖无重复／遗漏，仅指定文件全部节点5→1，其余归属相同，Windows all不变。应沿用已实施balance的完整collector＋原selector回放方法，不新增检查框架，也不将旧50／20节点硬编码成最终事实。父留存22是新增保护数量，不可直接当整份文件或全suite新节点计数。

本调查没有执行collector或新组合正文。后续消费最终候选既定源码／非editable安装及官方CI证据；不要为本报告重复已有留存选集或无差别重跑六组。若受影响组1／5需既定组合验收，保存同一输入的JUnit／phase／退出码与收尾；实际故障才沿失败节点定位。准确候选自己的六Linux原20分钟与Windows原30分钟终态才认证发布。静态fixture闭包、旧成本和a0d成功均不能替代它。也可以先观察最终候选自己的CI再决定搬组。

## 原件摘要

下列路径均相对仓库 ignored `.ergora/checks/`，保留原件，不复制历史运行命令、环境或凭据。

|原件|SHA256|
|---|---|
|cycle-measurement-collect/publication-r1/20261116T005135Z-summary.json（上述快照）|`37e8bc1383522e7396a836c783e90553652245ca58f613f47fc9a9605ce1f879`|
|ci-training-shards/installed-py311-r1/group-5/ci-results/junit.xml|`54b6a172f1412621ab72632f869e10e1ce025ee1f57bb91c242fe356912ea52c`|
|ci-training-shards/installed-py311-r1/complete-summary.json|`bdd998fa558cb297538301d99ad458bcafdd7b70e030a4e6fb52e76045ee4555`|
|cycle-parent-request-retention/package-r3/installed-retention-r3.xml|`b45b5c68a9bfa54a9796aff823f848d2e1d492eea74af30d3fddfdf6212dbc47`|
