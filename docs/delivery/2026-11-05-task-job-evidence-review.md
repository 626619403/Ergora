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

## 精确提交、发行与实时远端复核（CI 待完成）

同片审查者于 2026-11-05 追加。已独立核精确提交 `1dbe969e433348eda60d6bff0271c13cd729b6ba` 及直接父提交 `8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`。实际 18 文件包括已审 b1 Python/测试、README/USAGE/PLAN/详细计划、本片交付与审查，以及前 a2 的终结记账；后续 b2 的两个 JS 和设计记录均未混入。当前工作树已有 b2 JS，故本次直接从精确提交的内存 `git archive` 复算 350 个资源摘要，全部等于原 manifest 和实际 `087aea1838886dd12e6a5d56220dc28b6440276608b9464232527a39f738c115` wheel；未以当前 JS 工作树替代 b1 身份。

已读实际 `verify-commit-package.py` 与 `commit-package-identity.json`，并独立重复上述只读归档比较。八份提交文档的实际字节 SHA 全部匹配 `static-documents.json`，其中本报告原 43 行版本 SHA 为 `76ea64cd10d24aab1e4f40bc05652b5049a0c646a17f2f16d2289120f8abb1d4`。已读 staged 检查脚本、command 和原日志，8 文档/287 本地链接及锚点/27 README parser 命令、零缺失与 exit0 一致；parser 结果不代表命令业务执行。

已读 `push-b1-rsa-command.json` 及原日志：普通 `git push origin 1dbe969e…:refs/heads/refactor/architecture-foundations` exit0，原日志为 `8f1489c..1dbe969`，无强推。本审查者实际执行只读 `git ls-remote origin refs/heads/refactor/architecture-foundations`，exit0 精确返回完整 `1dbe969e433348eda60d6bff0271c13cd729b6ba`；仅在该进程环境给既有 SSH 命令追加指定 RSA 身份，未修改 Git 配置或读取/输出私钥。

精确提交、原验收发行身份、正常推送及实时远端范围通过，无新增 findings；b1 精确双 OS CI 的官方原页和全部必要步骤尚待同片核对，不能以 a2 CI 替代。本次未安装、重跑测试或访问原业务运行，尚不形成完整终结通过结论。

## 精确双 OS CI 与同片最终终结

同片审查者于 2026-11-05 追加，本段取代前述当时的 CI 待完成状态。已读 `.ergora/checks/f4-task-job-evidence/` 中实际落盘的官方 `ci-actions.html`、`ci-run-latest.html`、两个 job HTML、job-groups 和 selection 记录；独立复算 `ci-html-status.json` 所列 6 份源文件的字节数/SHA 全部一致。actions 原行对 run `41892668276` 明确标注 `completed successfully`，同一行链接完整 B1 提交；run 原页的完整提交链接为 `1dbe969e433348eda60d6bff0271c13cd729b6ba`，Status 为 Success。已读实际验证脚本及 `verify-successful-ci-command.json` 的 exit0，另用独立 HTML 解析核下面两 job，未仅采信汇总 JSON。

|精确 job|平台/解释器|必要步骤|
|---|---|---|
|126793909338|windows-latest / Python 3.12|Build and install wheel、Packaged reference identity、Native application regression、Windows PowerShell 5.1 installer and upgrade 全部 success|
|126793909993|ubuntu-latest / Python 3.11|Build and install wheel、Packaged reference identity、Native application regression 全部 success；Windows installer 按平台条件 skipped|

两原 job 页的 `selectedJobId` 分别精确匹配上述 ID；全部必要步骤具有完成标志，日志 URL 均绑定该完整 commit 和对应 checks/job ID。设置/checkout/Python 与收尾步骤亦成功，无失败、取消或超时步骤。已读精确 B1 提交中的 `.github/workflows/portability.yml`，矩阵和 Windows 专用步骤条件与上述结果相符；未把 Ubuntu 的条件跳过记为执行成功，也未从步骤结论推导未读取的具体测试数或性能收益。官方 run 为 [41892668276](https://github.com/626619403/Ergora/actions/runs/41892668276)。

本次再次实际执行 RSA 身份下的只读 `git ls-remote`，exit0 精确返回 `1dbe969e433348eda60d6bff0271c13cd729b6ba`；既有 SSH 命令仅在进程环境追加身份，未改配置或读取/输出私钥。本地 HEAD 亦为同一完整 SHA。既有本地、350 资源/087aea wheel、精确提交及正常推送审查结论保持；本次没有重跑重型检查、访问业务运行或混入未暂存的 B2/C 文件。

F4.4b1 的需求、可维护性、本地证据、精确提交/发行、双 OS CI 和实时远端同片终结通过，范围内无新增或未解决 findings。实现者可据此登记本片完成并归档此最终追加；B2/C、完整 F4/F5/G0 继续按各自范围验收。
