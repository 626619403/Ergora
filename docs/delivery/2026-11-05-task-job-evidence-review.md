# F4.4b1 原 job 回执与文本证据独立审查

日期：2026-11-05。审查者：fresh-context agent `/root/task_job_evidence_review`。本上下文未继承实现讨论；先读原计划、实际 tracked diff/untracked 文件及相邻调用，再核交付叙述和原始证据。遵循仓库 `AGENTS.md` 与 `maintainable-project-delivery` 独立审查流程。

## 范围与身份

基线及审查时 HEAD 为 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`。合同来自[详细计划 F4.4b](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)和[本片交付记录](2026-11-05-task-job-evidence.md)。本次实际核过 `git status`、`git diff --stat`、tracked diff 和三个新增文件：

- 生产：`src/ergora/{cli.py,reference.py,reference_task_creation.py,reference_task_reconciliation.py,tasks.py,web.py}` 与新 `reference_task_evidence.py`。
- 测试：`tests/{test_architecture_boundaries.py,test_task_inputs.py}` 与新 `test_task_job_evidence.py`；同时读原 `test_task_plan.pending_plan`、原 Submission/Creation/Transport/FileAdapter 及相关边界。
- 文档：README、USAGE、PLAN、详细计划和本片交付记录。前 a2 的 `task-events-console-review` 终结追加不作为 b1 生产差异；随后新增的 b2 设计及可能的 JS 工作不在本报告范围。

独立复算实际 wheel SHA 为 `087aea1838886dd12e6a5d56220dc28b6440276608b9464232527a39f738c115`，350 个包资源逐项等于 manifest、两套实际非 editable 安装及当时源码，283 个冻结 reference 文件等于既有基线。新 evidence 模块 SHA 为 `1b8a59626bd9fcb821eae64991c57eb2ac0f035161a78debc1ea445767161f9b`。两安装的 `direct_url.json` 也与记录一致，无 editable 标志。此身份不代表后续 b2 或尚未产生的 b1 提交。

## 需求结论

本地范围通过，无需要修复的需求 findings。`tasks.job` 统一验证原 run、1–10000 调度事件、字符窗口、回执 SHA 和 1–60 秒预算；CLI/GET 消费同一用例，没有写操作入口。专用子进程复用原 submitted/spec/memo/run 归属验证，要求从事件 1 开始的连续前缀，只解码所选 `dev_submit` 的单一 context，按原完整 spec 和 request envelope 的 JSON 摘要匹配。新增单 payload 检查确实位于 SDK decode 前，关闭了原 SDK 单类型 hint 会忽略额外 payload 的漏洞。

读取原生 `FileAdapter.poll` 的真实实现后，确认其验证终态回执、原 job/context、可信根、安全路径、产物完整摘要及逐产物 16 MiB 上限。首读没有返回 context/spec；`published` 与两个未知字段没有被解释为工作流采用或任务成功。文本必须从原回执名称选择并固定首次 receipt SHA，再完整核 SHA、严格 UTF-8、NUL 和大小后按 Python Unicode 字符切窗；末尾、越界和变化均明确表达。1 MiB 响应守卫与父进程 `timeout+5` 回收存在，公开说明准确保留了 SDK 物理页及同步全文件验证的成本边界。

## 可维护性、守卫与验证成本结论

通过，无需要修复的结构或成本 findings。新模块是与既有原生任务边界一致的专用进程入口，拥有一段连续的原 job 证据算法；未新增依赖、第二账本、缓存或调度器。`tasks` 拥有公共输入校验，CLI/Web 只转交，reference 保持平台/环境/子进程边界，层级一致。

`_Creation.file_adapter` 是原 `_Inspection` 中配置读取及注册根比对的机械迁移，原安全读取原语保持；Creation 已持有 registered root/config/adapter，因此位置合适。实际生产消费者分别是 reconciliation 的 `_Inspection` 和新 evidence 算法，没有为复用数量制造包装。没有依据再抽取通用 history/文本框架或把新算法塞入对账所有者。

各新增守卫对应可达边界：用户参数、外部原 history/codec、持久 envelope/receipt、目录配置、文件内容及响应资源。没有发现应删除的生产守卫或无条件吞错/回退成功路径；额外 payload 的回归反例已实际捕获首轮错误。现有 FileAdapter 的全部产物验证不应仅为加速窗口而绕过；本片文档没有把 8192 字符窗口称作总 IO/内存上限。

新合同复用已有 `pending_plan`：小型本地文件、真实 SDK protobuf/分页迭代器/DataConverter/codec 与原 FileAdapter；仅提交归属/连接端口在夹具中替换，真实归属链另由两原 run 验收覆盖。输入反例在 `_project` 前失败，不建执行栈；Linux skip 在模块级，基础 Web 无 SDK 的依赖方向保持。测试覆盖的不同失败边界有合同意义，未见新增重型重复初始化；原 10 项较慢对账/外部边界回归验证了此次共享 adapter 移动，不能把它们的成本归为新文本单测，也没有理由删除。

## 核验与限制

已读 `.ergora/checks/f4-task-job-evidence/` 的实际测试命令和原日志：首轮 99 passed/1 failed（多 payload 未拒绝），修后 100 passed，最终源码联合 150 passed（命令 5.30 秒/pytest 3.81 秒），必要旧边界 10 passed（66.33/65.71 秒），最终 wheel 合同 103 passed（5.19/2.78 秒）。这些是原执行结果，本审查没有重跑；既有 Starlette 警告未被遗漏。已读发行/安装/无 SDK 日志和 13 模块语法终核脚本、command 及结果；本次额外 `git diff --check` 的 b1 tracked 源码/测试/公开文档范围通过。

已读真实验收 `read-jobs.py`、`native-jobs-command.json`、`native-jobs-verified.json`、首读/窗口/失败输出的记录与 `native-snapshot.py`。同一包两个原 plan job 都是调度事件 56，共 8 CLI+12 GET、零 POST；两个 model-log 分别 12515/13886 字节、各两窗，execution-plan 为 4002/4198 字节、各一窗。原验证脚本逐窗重建字节及 SHA，比较 CLI/API、原 request/receipt 和历史快照；错误 receipt SHA、非 job 事件、错误 run 分别失败。命令 exit0/45.00 秒只证明这组验收，不是单请求性能基准。

本审查独立检查前后快照完全相等，并逐项复算当前 139 个原文件摘要；三 run 的历史事件数为 329/348/112，快照包含 outcome、refs/worktrees/工作文件、3 claims/零 active。审查脚本还完成治理 job 两份产物的窗口重建、摘要及首字符 CLI 比较；在随后错误 JSON 的键名假定处终止，因此不把该脚本称作两 job 全量复算成功。两 job 完整重建及历史/零 Running 结论以已读原验证脚本、成功命令和原始结果支撑，本审查没有再次查询服务。进一步复算尝试遇到自动审批服务 deadline，未执行，未记为成功或安全拒绝。

本次仅只读源/原始证据、复算摘要及轻量检查，并写本报告；没有安装、重跑完整套件/浏览器/模型、提交、信号、取消、导出、对账或改原生数据。没有证据支持无 SDK base 父环境的真实原生查询已完成；仅无 Temporal SDK 安装及基础入口依赖范围已核。

## Findings 与后续门禁

范围内无 findings，无源码阻塞项或最小修复要求。本地需求及可维护性审查通过；实现者须回填本片交付与 PLAN，随后核精确 b1 提交归档与上述 350 资源身份、正常推送/实时远端及所有必要双 OS CI 步骤，由本审查者追加同片终结。当前没有 b1 精确提交/CI 完成结论；b2 网页及完整 F4/F5/G0 仍未完成。
