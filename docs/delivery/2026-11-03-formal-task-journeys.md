# F3.4c/d：正式任务真实服务旅程

日期：2026-11-03。前置 [b2显式外部对账](2026-11-03-task-reconciliation-write.md)的生产/测试候选为 `7139d1a85cdce13689d75471620da8dd143156a8`，源码/完整包回归/精确两OS CI和独立最终审查均已通过，b2已收口。本记录正在执行c真实旅程，不宣称c/d已验收。

## 本次范围与验收

使用相同非editable wheel、全新持久执行目录及新控制注册，通过正式CLI/API创建和提交两个模板，固定原spec/memo/run，精确计划批准，再经历 inventory → plan → work → integrate → verify → review，取得原结果并导出精确候选到本地分支。独立worktree重跑可信检查，业务main保持原基线；重开CLI/HTTP后沿原ID恢复。真实Codex调用与可信检查分别留原始身份，不继承旧L0结果。

后续 d 分开记录真实取消/外部原进程确认、终态显式对账、受控独立worker重启，以及可在协议层验证的错误批准/旧计划/候选漂移/丢响应。缺认证、权限或服务的维度明确记录，继续可测范围；保留失败和未知，不修改旧结果、删ledger或绕过门禁。

配置/数据/日志留持久用户目录的独立验收子目录；仓库私有检查脚本和身份索引位于 `.ergora/checks/f3-formal-journeys/`，公共文档不保存凭据/模型原文。所有测试操作员批准只适用于隔离演示，不能视作业务负责人批准或生产采用。

## 准备事实

只读盘点：默认服务端口当前未监听，既有完整参考依赖和Temporal二进制可用；Codex命令存在，历史验收配置采用 `gpt-6.1-sol` 和环境凭据，当前该凭据存在。没有测试真实模型请求，不能据此宣称认证有效。后续启动前重新核端口与自己服务的归属。

参考执行依赖沿已核冻结发行复制到新目录，Python/二进制可复用现成依赖，控制应用必须核新wheel身份。原setup会初始化私有配置/文件adapter目录；服务使用现有显式Supervisor用例，只管理本次登记的新执行栈。原模型配置含环境变量名，凭据只由运行环境提供，不打印/写入公开文档。

## c独立环境与真实提交

已复制并验证新参考运行时，复用既有完整依赖/二进制；新私有配置、native state和控制库独立于旧L0目录。两个业务仓库从旧演示main的已提交基线克隆，基线 `f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`，没有复制旧运行或采用旧候选。两个新项目分别注册一个模板，可信检查脚本有固定摘要，基线3项/6项全部通过。

4个开发角色各显式绑定Codex/current-container，当前项目revision均为5，绑定随新创建冻结。每模型stage预算600秒、最多2个并行外部job。服务启动前核默认端口为空，只通过当前登记控制的Supervisor栈启动Temporal/worker/executor/A2A/MLflow，doctor ready通过；这不证明模型认证有效。

正式CLI预览/创建/提交/固定原run读取共8次通过，两个run均进入INVENTORY，候选仍为基线：

|模板|新任务|固定原run|
|---|---|---|
|repository-governance|governance-f3-normal-r1|`01a1a106-8352-7c7a-96c3-4a8efd34ac5b`|
|large-change|large-f3-normal-r1|`01a1a106-9420-7808-a9a8-05f6268f8d27`|

私有入口/命令/计时在 `.ergora/checks/f3-formal-journeys/` 的 `environment.json`、`normal-runs.json`、prepare/start-services/create-start脚本及命令日志。服务脚本首轮把 `--binding` 错当内联JSON，CLI实际要求文件，未修改任何binding或启动服务；保留首轮脚本/错误后改用文件，8次binding更新、自己服务启动与doctor通过。属于验收辅助代码修正，不是产品修复。

## c真实计划与六阶段终态

两个原run均实际调用Codex完成inventory/plan并进入AWAITING_PLAN_APPROVAL。逐份核执行/回退计划的原始artifact SHA及范围后，使用测试操作员决定批准这两个隔离演示。计划SHA分别为治理`ce388a5742371e5d8dd9843a86d890e2384ebcb4237e4ff065c9324dd4c0015f`、大型`e870ca615d5ab5556e30c0d9694a1121c35a7c5e693db5dd192ad4f8672f2ffb`。

先以错误计划摘要探测正式批准入口：两者均明确拒绝，原journal保持prepared/attempt_saved=false，原history没有approve_plan信号；再以审阅过的精确计划批准，各原run恰好一个信号。原始脚本、命令和`normal-approvals.json`保留实际决定、artifact摘要和信号计数。

现已通过正式CLI固定原run核两者terminal=true、phase=REVIEW_READY。治理候选`ebb9f7bed44a110bc7a9d895c49ac6175f4b4c45`新增ownership文档及AST边界测试；大型候选`6ad080e1f3ac58d6312fae7f969d03fcbb63c112`新增summary/opt-in CLI/测试/rollout文档。各原结果的可信检查与独立Codex审查均通过，verification/review绑定同一精确candidate；没有合入业务main。

正在留完整history/回执/产物身份，之后导出候选并在独立worktree复验、重开HTTP/CLI。c/d独立审查尚未完成；届时使用新的独立上下文核原始证据和失败范围，不复用b2审查充当本旅程验收。
