# F4.3c2 网页外部证据与显式对账独立审查

日期：2026-11-04。审查者：Codex `task_reconciliation_console_review`，新的 fresh-context 独立上下文。先读原始需求、AGENTS、原始差异及实际消费者，再读作者交付记录；应用 maintainable-project-delivery/independent-review 和 review-pr。仅写本报告，未实现源码、安装、提交、启动模型或服务、发 signal、对账或修改租约。

## 结论

- **需求符合性：本地审查通过。** 固定闭合原 run 的外部只读观察、独立本地记录、新明确对账与按原 intent 恢复符合本片合同；未发现未解决的正确性 finding。
- **结构与可维护性：通过。** 局部工作区留在实际任务详情所有者中，复用现有 API/UI；完整 history、receipt/artifact/fence、原 claim 与释放状态机仍由原生所有者负责。未发现应删除的新增守卫、单次包装、测试或 CI。
- **本片尚未终结。** 当前为未提交工作区；提交后精确双 OS CI、远端 SHA、最终文档身份及同片独立终结复核仍待完成。C1 的 CI41808523543 不作为 C2 的运行结论。导出 D、有界观察 F4.4、完整索引 F5 不在本报告范围。

## 精确范围

基线/审查时 HEAD：`759c27ed06b781ca768a53c1e9e8c0eb1377e296`，分支 `refactor/architecture-foundations`。生产差异只有 [tasks.js](../../src/ergora/data/console/tasks.js) 的112行局部对账工作区/两个入口及 [app.js](../../src/ergora/data/console/app.js) 的帮助说明。审查时生产摘要：

|文件|SHA256|
|---|---|
|`src/ergora/data/console/tasks.js`|`ccc6f522756c6a5707dfa24f8a82e8f4ce3aff82d355243d77a9ba63ba8d49e3`|
|`src/ergora/data/console/app.js`|`5fcb5ed954e4dd2993c01dc532ce6f541ee6e53153e2a4c7bae044ff4612c7ac`|

同时检查 README、USAGE、PLAN、current architecture、all-in-one、formal-task-console 及新 [C2 交付记录](2026-11-04-task-reconciliation-console.md)。C1 两份报告只有终结追加，单独识别，不计为 C2 行为；审查期间出现的下一 D 设计记录不属于 C2。没有 Python、测试、CI、依赖或冻结 reference 差异。

实际消费者/契约检查覆盖 `tasks.js` 相邻批准/取消/提交/原 run 查询、`api.js`/`ui.js`/`app.js` 生命周期、`web.py` 四路由、`tasks.py`、`reference.py`、`reference_task_reconciliation.py`、FileAdapter receipt/artifact 校验，以及既有 external-status/reconciliation 合同测试。

## Findings 与处置

无未解决的 Critical/High/Medium/Low finding。

**R1 / Low / 已关闭：区分 wheel 构建与整段发行验收耗时。** 初读交付记录29行将31.83秒称为“实际构建”；`build-final-command.json` 的 `uv build` 为14.8239秒，31.8344秒来自包含 venv/安装/身份核验的 `package-command.json`。误标会使后续性能比较使用不同范围。最小修正只需分别命名两项，无需重测产品。作者已改为“wheel构建14.82秒 / 整段31.83秒”，审查者重新读取29行确认修正；生产摘要保持。

## 需求与边界核对

|边界|源码及实际证据|
|---|---|
|闭合固定原 run 才进入外部观察|`tasks.js:838` 要求 terminal 且 queried，`:579` 检查详情/run代际；external-status 原生契约再校验原提交 run、闭合、无 successor、完整 history。GET 无 fence/release 调用。|
|本地记录独立读取|`:803` 独立入口，`:653` 在无 run 模式只 GET reconciliation；原生 status 不调用远端 inspection。两模板受控日志验证没有 external-status 请求。|
|新对账和原意图恢复|`:603` 只有本轮 observation 成功且 not_recorded 提供新确认；`:604` 只对 prepared/unknown/confirmed 提供恢复。`:625` 分别发送 revision/run/confirm 或原 intent SHA/confirm；外部失败阻止新确认，已有原意图可单独恢复。|
|写与迟到回复|`:618`/`:647` 禁止写中读取，写开始清除旧 observation；详情归属、内容连接、dialog open、读取序号和 run 序号分别阻止切换/关闭/替换/新读取后的旧回复。异常回复只显示未知并要求先读原记录，无自动重发。|
|事实分开表达|confirmed 仍将 lease 显示未知；reconciled 只读。原 outcome、历史清理证据、当前外部观察、租约释放与 execution_success 各自展示，未从 CANCEL_UNCONFIRMED 或清理确认推断开发成功。|

这些检查分别保护可达的页面生命周期、外部输入或持久事实，不是重复实现后端状态机。后端仍在真正写入边界重验 revision/run/claim/证据；页面无需再复制其深层校验。

## 所有权、性能与验证成本

`reconciliationDialog` 的两个实际生产入口都在同一任务详情文件中；内部 `show/read` 是该工作区的私有算法，没有跨文件消费者。保持局部实现符合实际复用证据；相邻批准/取消的输入、状态含义和恢复协议不同，未发现应仅凭外形相似抽出的通用状态机。

仅打开本地记录工作区发1次 GET；显式打开/重读外部工作区并行发2次不同用途的 GET。外部读取沿用原完整 history/receipt/artifact 路径，本地记录不访问 Temporal。没有轮询、后台扫描、自动重试或模型调用。现有原生子进程和全 history/artifact 读取成本仍然存在，20秒请求超时沿用原 API；本片没有提出吞吐或大规模历史延迟改善。139请求是四段操作覆盖的总量，不是性能基准。

没有新增生产断言、持久测试或 CI。既有合同测试负责原生状态机；私有浏览器 fixture 覆盖新增 UI 准入、未知结果和生命周期。首脚本累计 POST 计数错误的 exit1 与33请求/3拦截 POST 原始段保留并排除成功汇总，v2改为模板内计数差；不是放宽产品合同。未改 Python 而避免重复本地重型全套回归合理，最终精确提交仍须正常 CI。

## 已核证据与独立检查

私有证据根为 `.ergora/checks/f4-task-reconciliation-console/`，截图为 `output/playwright/f4c2-*`，不要求公开提交运行数据。

1. **发行身份独立复算通过。** wheel `3b9c800484bc328f839741e06aee4e77fed2899431e739918313c1bd101bdec1`；独立读取当前源码、zip 和两份 noneditable 安装，348文件逐字摘要一致、冻结283文件保持。核原始命令与日志：基础Web无Temporal SDK，13模块语法通过，wheel架构8 passed；`git diff --check` 独立 exit0。
2. **浏览器记录交叉核对通过。** 四段命令均exit0，实际嵌入脚本与保存JS逐字一致，CLI原始 Result JSON 与对应结果文件完全一致。controlled-v2 46/6、boundaries 28/3、native 35/1、readback 30/0，共139请求/10POST、零pageerror；9次受控写拦截，唯一真实 reconcile 的请求固定原 run/revision/confirm。原脚本在实际收到200/reconciled后丢弃回复，reload、重复GET、清浏览器选择后仍取回同一记录，没有 resume 或第二次 reconcile。
3. **本地原生证据独立只读复算通过。** 127份变更前文件摘要全保持，仅新增该原task的intent/attempt/evidence/result四文件。原 intent SHA `75f71f0c68b0d3eb2c8060ad023514d4431580f7aa4428b790f4b236939b62d1`，清理/释放依据同为 `f0accdb828d820da45aab3051a6af0a92048845604afb07c7d42c31a565fbce0`；唯一 CANCELLED receipt 摘要匹配。以 SQLite `mode=ro` 核真实 ledger：只更新原 claim `a53f23ac76be99e258984ed649f8671355c59f183f899f816bd3b160fcdb9762` 的释放时间/依据及移除其 active，其他字段、其他 claims/active 与变更前全等；实际3claims/2active。
4. **远端原 history/outcome 独立只读复核通过。** 重用既有Temporal服务取回三条固定 run 的完整 history，逐JSON与变更前文件相等，329/348/112事件及 REVIEW_READY/REVIEW_READY/CANCEL_UNCONFIRMED 原结果保持，无Running workflow。没有发送任何写操作。
5. **视觉证据实际查看。** 首次治理fullPage截图确为空白dialog，不计为可读通过。实际查看最终两个模板390px viewport顶部图和 native-release-facts-viewport：原run、无fence/未确认、以及真实reconciled的清理确认/lease释放/原CANCEL_UNCONFIRMED/开发未知均可读。没有据首图推断根因。
6. **静态记录核对。** 10:06检查为9份Markdown、320链接/锚点、27条README parser命令，exit0。该检查后作者继续同步状态文档、修正R1并新增本报告，旧摘要不代表最终文档版本；最终静态检查应在文档收口后重跑，不需要重跑产品旅程。

## 限制与下一验收

审查者未重跑浏览器写旅程或完整Python回归，未安装/重建包，也未重新发起真实对账。五态和异常/迟到写主要由受控fixture覆盖；真实写只证明本片精确原取消任务的一次成功释放及丢回复后读取恢复。当前浏览器证据没有单独演练同一dialog内两个读取的逆序返回；相应源码序号守卫已检查。实际远端故障/损坏journal的完整状态矩阵沿原F3测试，不由这些本地成功段扩大结论。

后续需保存 C2 精确提交身份，运行正常双OS必要CI步骤，核远端SHA及本报告/交付/计划的最终链接与摘要，再由同片独立审查者完成终结记录。当前结论不宣称完整F4、F5或候选导出已完成。

## 追加复核：精确本地提交、发行与最终静态记录

日期：2026-11-04，同片独立审查者追加。本段更新前文“未提交”的当时状态；当前工作树已进入下一 D，本次仅从精确 C2 提交及其归档读取，不要求 D 源码等于 C2 包，也不评价 D 行为。

- **精确本地提交通过。** `401bacb28cf99e121357860901c4d95332417dae` 的直接父提交为原基线 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`。实际12文件，生产仍只有 tasks/app；下一 D 的 export-console 设计记录不在提交内。精确两提交之间 `git diff --check` 独立 exit0。
- **归档与原发行身份通过。** 核 `commit-package-command.json` exit0、原始脚本/日志及 `commit-package-identity.json` 后，审查者另用内存中的精确 `git archive` 独立复算：348资源与 `package-identity.json`、实际 wheel 及两份原安装逐项一致，wheel仍为 `3b9c800484bc328f839741e06aee4e77fed2899431e739918313c1bd101bdec1`。初审生产摘要与本地行为证据因此可准确绑定到401bacb；未重建、安装或重放原生写操作。
- **提交前最终静态记录通过。** 10:23:28 UTC 的 `static-documents-command.json` exit0，原始日志为10份Markdown、325链接/锚点、27条README parser命令，无缺失。检查脚本明确排除下一 D 设计记录；审查者将全部10份文档摘要与精确401bacb归档逐一比较，全部相等。该结果替代前文10:06的旧静态快照，仅证明401bacb内的文档版本；本次追加是后续审查状态记录。
- **远端与精确 CI 尚未完成。** 本地提交成功不代表推送成功。只读检查 `ssh-diagnostic.log`：RSA公钥已offer，服务器继续要求publickey，最终为 `Permission denied (publickey)`；审查环境未提供SSH agent socket。作者报告正常push及两身份ls-remote同样认证失败，本轮未重试认证/推送，也未取得可核远端SHA或401bacb的双OS CI结果。

需求和可维护性本地通过结论保持，无新 finding；R1已关闭。**C2保持“本地提交/发行/静态核验完成，远端推送与精确双OS CI/同片终结待完成”，不得标为完整交付完成。** 恢复认证后仍须核正常推送、实时远端SHA和该精确生产提交的全部必要CI步骤，再追加同片终结结论；C1或下一D的结果均不自动替代本片证据。
