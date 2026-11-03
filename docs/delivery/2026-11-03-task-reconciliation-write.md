# F3.4b2：显式终态外部对账

日期：2026-11-03。基线 `bca8c6eefcbeec6f67b7d78bc033f7e5ad95d9ba`，分支 `refactor/architecture-foundations`。前置 [b1](2026-11-03-task-external-status.md) 与[调查](2026-11-03-task-reconciliation.md)已完成。本切片进入实现，验证、独立审查和推送尚未完成；完整 F3 仍有 c/d/e。

## 行为和公共接口

新增 `task reconcile PROJECT TASK --revision N --run-id RUN --confirm`、`task reconciliation PROJECT TASK`、`task resume-reconcile PROJECT TASK --revision N --intent-sha256 SHA --confirm`。相同 tasks 用例由 POST reconcile / POST resume-reconcile / GET reconciliation 提供，超时 1–60 秒，默认 20。GET 只读本地记录；原 external-status 继续只读实时证据。仅显式原始闭合 run 可以发布 fence，当前 run 已变化时拒绝；不发 workflow、signal 或重跑任何阶段。

短 SQLite 准备事务核当前 revision 与严格 confirm，原 task 非阻塞锁保护不可变意图；远程查询、fence 和租约释放均在控制库事务之外。复用 `_Inspection` 的原 submission/spec/memo、连续 history 和 requests/receipts/可信产物核对，沿现有 reconciliation 原生进程，不新增依赖、执行器或通用插件层。新私有协调类只拥有这一恢复算法。

## 持久合同与恢复顺序

记录位于原执行 STATE 的 `ergora/task-reconciliations/TASK.{intent,attempt,evidence,result}.json`，采用已有有界安全读取及不可变发布。意图绑定创建/提交摘要、项目/登记/控制目录、原 run 及完整原 `cli-ingress.json` 身份，要求原 tracker、`local-cli` owner、task 和 spec SHA 完全匹配。

1. 准备仅保存意图，不访问远端。重复 reconcile 返回原本地状态；明确 resume 才推进未完成意图。
2. 先核完整闭合原 history、当前 run、根与 scope。额外请求或孤立回执属于 scope 冲突，fence 前拒绝。写前 attempt 绑定真实原 outcome、Temporal 闭合状态及 history job 集合摘要。
3. 调用原 `FileAdapter.fence` 的不可变发布；不采信它单独返回的 confirmed。随后再次核完整原 history、当前 run、所有原 job、两类目录、可信终态回执/产物及 fence。缺证据保持 unknown，不释放；后续 resume 可在可信执行器补齐原回执后继续。
4. 将两份事实（原 outcome 与本次确认的外部清理）先保存为 evidence。原 native release 适用时保留原 outcome SHA；其他闭合清理使用该 evidence SHA。只通过原 `IngressLeases.release` 释放精确 claim，不改 ledger SQL、不改原 outcome、不删除记录。
5. SQLite 提交后保存 result。每次恢复重新核原事实及已保存 checkpoint/evidence，再幂等调用同一 release 摘要；发布后、保存证据后、释放提交前后及丢响应均可沿原意图恢复。已完成的重复调用仅返回原回执。GET 不创建 fence 或租约库。

本地状态为 not_recorded / prepared / unknown（写前 checkpoint 后）/ confirmed（证据保存、释放回执未保存）/ reconciled。原执行成功字段保持未推断。task fence 无 run ID；本地锁不能阻止其他客户端绕过协议复用 workflow/task ID，原 task ID 必须由所有协调者遵守不可复用约定，且发布后继续检查已知后继 run。

## 验收

- 两模板真实合同/SDK 分页边界、原 outcome 不变、精确 claim 释放；原 release 适用和 CANCEL_UNCONFIRMED 清理均验证。
- 发布、证据、SQLite 提交与父响应各中断点；原 intent SHA、历史/回执漂移、错误 owner/scope、后继 run、缺失/损坏/孤立证据都不能释放。
- GET 与重复已完成调用只读；CLI/API 同源、严格输入、超时、同 task 排他及慢远程阶段不保留共享控制库写锁。
- 最终非 editable wheel、资源/冻结身份、无 SDK 基础 CLI、按影响定向与完整发行回归、精确两 OS CI；新上下文独立源码/结构/恢复审查及最终证据复核。

真实服务与模型的两模板六阶段、取消进程及 worker 重启仍由 F3.4c/d/e 验收，本切片的可控 RPC 不代替那些结论。

## 实现与首轮检查

已实现：`tasks` 三用例、`reference` 同源原生入口、CLI 三命令与 Web 三路由；`reference_task_reconciliation` 在已有 `_Inspection` 旁组合私有恢复所有者，复用其全部 history/文件校验。Web 的精确 run/确认/预算正文由实际批准与对账消费者共用 `TaskRunDecisionPayload`。`docs/USAGE.md`已补命令、状态、恢复与备份合同。冻结文件及依赖未变。

原 RPC fixture 增加发布/文件/SQLite commit 前后中断边界，新 Linux 专属集成模块覆盖精确 claim、原 native 摘要兼容、四种无 outcome 的闭合状态、缺证据恢复、错误 scope、发布后后继、保存证据后漂移与并发；纯输入反例直接加入既有轻量模块。

- 源码输入/既有读取检查：`PYTHONPATH=src .venv-dev/bin/python -m pytest -q --tb=short tests/test_task_inputs.py tests/test_tasks.py`，65 passed（15.26 秒）。
- 首轮探索性集成：reconciliation / external-status 联合 `-x`，46 passed、1 failed（290.68 秒）；失败为新增测试只接受 lock/progress 文案，实际原非阻塞锁已按 Errno11 正确拒绝。已修断言以接受实际诊断，未更改生产锁合同。该轮中测试仍有增补，不作最终固定源码验收。`initial-targeted.json`保存实际范围与失败。
- `git diff --check`通过；新 wheel 构建通过，但共用正文名称随后有修改，该包不是最终发行。
- 修后并发/API及新增发布后/ledger反例、journal损坏检查通过，后续发行进度见下；持久原始证据位于 `.ergora/checks/f3-task-reconciliation-write/`。

## 固定候选发行验收进度

修后定向9项、journal恢复1项均通过（63.76/12.06秒）。[新上下文独立源码/结构审查](2026-11-03-task-reconciliation-write-review.md)通过，无findings；独立5项关键恢复边界通过（36.54秒），并重新核算全部包身份及两模板原outcome/回执/产物/ledger。审查没有建议删除生产守卫或新增反例；明确三轮回执/产物读取及本地锁/可信执行器约束，未把小fixture推导成大产物性能结论。

当前 `c7411ae956108c2e23544fd476c0106e95b65a1d77a3a19c20a14caa3f5f8ceb` wheel 的347包文件与源码、完整开发安装、独立基础安装全部一致。开发环境Python3.11.15，基础环境Python3.12.3；基础环境无FastAPI/Temporal/GEPA，使用登记的独立完整运行时执行原生操作。两模板27次真实CLI通过：缺回执unknown且租约保持、原不可变fence、可信回执补齐、原CANCEL_UNCONFIRMED保留、精确清理摘要释放、SQLite已提交/响应丢失后沿同一摘要恢复、只读重复状态均已核。原始 `base-journey-v1-command.json/log`与`base-journey.json`保留身份和计时；使用可控RPC/真实SDK codec分页、实际FileAdapter/SQLite，不声称真实workflow或系统进程已验。

治理模板4次受控connect各4.5秒、原生预算25秒；另一项目SQLite写入19.92毫秒成功，同task操作1090.03毫秒明确busy，均在对账完成前；整个恢复20093.78毫秒。两模板本地状态3次样本中位1016.68/1088.33毫秒、最大1017.54/1116.69毫秒，含CLI/原生进程/SDK导入并与全回归并发。仅说明所测隔离/资源边界，不推导真实网络或启动性能收益。

最终安装包完整回归正在执行；精确两OS CI及独立最终发行/远端核对尚未完成，b2仍不能标完成。
