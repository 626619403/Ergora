# F3.4a：候选导出独立审查

日期：2026-11-03。审查者：独立代理 `f3_task_export_review`，以全新上下文开展；仅审查和编写本报告，未修改生产实现、安装依赖、提交推送或操作已有服务。依据项目 AGENTS、[F3.4 原始验收](2026-11-03-formal-task-acceptance.md)、[切片合同](2026-11-03-task-export.md)，使用 maintainable-project-delivery / independent-review 和 review-pr 流程。

## 结论与状态

- **需求符合性：修正后的源码及下文已核对的最终发行证据通过，本地完整回归待完成。** 初审确认一项 HEAD 保持缺陷，修正后独立复核关闭；未发现其他未解决的源码正确性问题。此结论不等于 F3.4a 已交付，也不验收 F3.4b 的终态外部对账或 F3.4c/d 的真实六阶段旅程。
- **可维护性：源码范围通过，无未解决的结构、复用或资源生命周期 finding。** 新文件有实际 CLI/API 消费者；Git 交互事务和预算清理留在导出所有者内，未扩建通用 runner 或第二套运行/审查状态机。
- 最终非 editable 发行及两安装身份、基础两模板 CLI/升级兼容与性能证据、精确两 OS CI 和源码候选远端 SHA 已完成下文独立核对。本地完整回归和之后的最终文档交接仍待收口，不能从其他检查代推通过。

## 确认发现与处理

### R1 / P2：创建目标 ref 会使已有 worktree 的 unborn HEAD 出生（已关闭）

初审位置：[reference_task_export.py](../../src/ergora/reference_task_export.py) 原 `create_branch` 的 `prepare` / `commit` 段（初候选 142–162 行）。任务正常创建并保存原提交回执后，用户在业务仓库执行 `git checkout --orphan agent/exported`；目标 ref 尚不存在，因此初实现的条件创建能成功。产品随后返回 `exported`、`checked_out: false` 并释放租约，但 HEAD 从不可解析变为候选提交，违反验收中的 HEAD 保持要求。该场景不需要伪造原 run、spec 或结果。

独立产品反例为 `.ergora/checks/f3-task-export/reviewer/test_review_probe.py`，初次运行 `1 failed in 7.72s`；原始 `probe.log` 和 `first-unborn-head.json` 保留了 HEAD 前后差异及已释放租约事实。

修正使用 Git 已准备的目标 ref 锁，在提交前执行原生 `git worktree list --porcelain -z`；若目标 ref 已被当前或关联 worktree 占用则 abort。新判断保护可达的外部仓库状态，位于实际 ref 创建所有者，未重复增加上游猜测式校验。独立重跑原反例及新增当前/关联 worktree 两例，`3 passed in 18.30s`；HEAD 仍不可解析，工作树保持，租约仍 active，无 ref lock 遗留。证据：`reviewer/recheck.log`、`reviewer/unborn-head.json`。R1 在修后源码身份上关闭。

### V1：越界路径测试只接受特定错误措辞（已修正）

初候选完整源码定向结果为 `68 passed, 1 failed`，445.06 秒。失败在 [test_task_export.py](../../tests/test_task_export.py) 原 368 行：原安全边界正确抛出 `Path escapes trusted root`，断言却只接受 `symlink|symbolic`。这不是已确认的越界写产品缺陷；它确实使该候选的检查失败，不能将此前 49 项或 11 项通过继承为最终通过。

实现者仅扩大断言以接受原 `safe_file` 的真实诊断，保留“外部目录无文件且未 fetch”的行为断言，未为测试另改生产错误文本。修正定向 `7 passed, 56 deselected in 47.81s`，记录在 `source/review-fix.log`。最终发行仍须跑适用回归。

## 审查身份与范围

基线：`722a3cb392dd5be03964845fa7d35c8c1bc90d1f`。初审八文件聚合身份 `84749715b6f84c412f2a0716494918a214bcfee01d016e4a9a40cfec991cc0f5`；修后身份 `7238c7fec9ffb664bed1dfe80bfd812721eb864960dbf8e55d1e4f4a8911e3e3`。逐文件 SHA 取自 `.ergora/checks/f3-task-export/candidate-source-identity.json` 并在修后重新计算匹配；独立结果保存在 `reviewer/fixed-source-identity.json`。`reviewer/fix-in-progress-identity.json` 是修正过程中捕获的过渡状态，不是验收候选。

完整读取了初候选 tracked patch 及以下文件，未漏掉未跟踪内容：

- `src/ergora/cli.py`、`reference.py`、`tasks.py`、`web.py` 的改动与相关调用上下文。
- 新 `src/ergora/reference_task_export.py` 全文。
- `tests/test_architecture_boundaries.py`、新 `tests/test_task_export.py`、新 `tests/fixtures/task_export_client.py` 全文。
- 新切片记录、正式验收设计、PLAN、详细计划、USAGE、PROJECTS、AGENT_BACKENDS；复核了同期补充的 `docs/architecture/current.md` 和 `reference-boundary.md`。

沿实际调用阅读了 `_Creation`、`_Submission`、`VerifiedSpecClient`、`DevelopmentTransport.lookup`、原 `agent_platform.cli.task_action`、`core.write/git/environment`、`ingress.release`、`IngressLeases`、`state.file_lock` 及既有进程收养/回收实现。没有运行完整测试套件或触及已有服务。

## 需求与边界核查

|检查项|源码与证据结论|
|---|---|
|真实入口与确认|CLI `export/export-status/resume-export` 和三个 HTTP 路由调用同一 `tasks` 用例；严格 confirm、当前 revision、输入及预算校验复用既有边界，写请求沿原同源保护。|
|原身份|复用原创建七合同、原提交回执及 intent 摘要；固定原 run 的 describe/history/spec JSON 身份与 SDK memo。仅 COMPLETED 且 REVIEW_READY、原 task/type/request/profile/base 和精确 candidate 一致才变更。|
|不可变目标与恢复|一个任务一份 intent，run/candidate/branch 变化拒绝。attempt 先于 fetch/ref 变更且固定完整 outcome 摘要；unknown 沿原 run 和实际 ref 对账，分支缺失保持 unknown，不能重新 fetch 或重建。|
|Git 与本地记录|fetch 只获取对象，不写 FETCH_HEAD；ref 事务、no-deref、持锁符号引用核查及新增 worktree 占用核查保护已有状态。使用原不可变写入发布原格式 export.json 与新回执。没有 checkout、merge 或 push。|
|租约与状态|确认实际分支后才调用原 ingress.release，不新增释放规则；本地 status 不连接 Temporal 或释放租约。已完成回执是历史事实，不冒充之后人工修改分支的实时检查。|
|锁与资源|准备在原 revision 短事务内非阻塞获取同 task 锁；网络/Git 阶段不占共享控制库。异步 Git 在专用进程组内，TERM 后 KILL 兜底；专用进程复用 Linux subreaper/reap，未把客户端超时当作实际 Agent 停止。|
|冻结与范围|独立 `reference.verify()` 为 PASS，283 文件身份保持；没有将协议端口 fixture 当作真实 Temporal/模型/六阶段成功，也没有接管旧原生 export。|

## 模块归属、必要抽象与性能

`tasks` 拥有项目修订和显式写用例，CLI/Web 仅传递输入、输出状态和退出码；`reference` 复用专用子进程边界，父进程无需加载 SDK。新导出模块是完整导出算法及其原生进程入口的所有者，生产调用确实来自 CLI 与 Web；其私有函数无需以测试调用或假想未来复用证明存在理由。

创建/提交/规范摘要/不可变写入/原生租约与进程后代回收均沿现有接口复用。未直接包装旧 export 的原因有实际证据：旧 check-then-fetch 会快进竞争者已创建的祖先分支，普通 no-deref 零旧值更新还会替换悬空符号引用。改用 Git 自带的 `update-ref --stdin` prepare/commit/abort，而非自行实现 ref 文件锁，抽象与复杂度均有对应的不变量。

`core.git` 是同步、最长 120 秒调用，不能承担这里的异步预算和持有中的交互事务；现有 `processes.run` 使用落盘输出与一次性 stdin，同样不能保持该事务。因此约束在 `_Export` 内的异步 Git 生命周期有具体用途。记录校验、原归属、符号引用、actor 和 outcome 漂移等防卫均面向外部输入、持久记录或可达竞争，没有确认应删除的无关校验。

该操作不在模型执行热路径。新事务增加少量本地 Git 进程和必要同步，其成本换取明确的分支/HEAD 保持合同；未从代码形状宣称延迟改善。源码测试中的 3 秒 connect 等待证明该场景下另一个项目可写，不能替代最终发行的长等待/升级兼容和性能测量。Git 预算清理证据只覆盖正常 timeout/受控异常；强杀客户端或断电仍按原意图与实际分支对账，不扩大为任意崩溃的绝对清理保证。

## 验证记录与剩余验收

|证据|结论及适用范围|
|---|---|
|首轮 `source/pytest.log`|49 项通过；早于 Git 事务修正，不是最终身份。|
|`source/dangling-before.log` / `ref-transaction-probe.py/json`|产品悬空符号引用反例及真实 Git 2.43 持锁探针；已阅读，用于验证修正必要性。|
|`source/git-fix.log`|11 项通过；早于 subreaper 加强，不作为最终门禁。|
|`source/final-source.log`|68 通过、1 失败；失败和诊断见 V1，保留为历史失败。|
|`reviewer/probe.log` / `first-unborn-head.json`|独立产品反例初次失败，确认 R1。|
|`source/review-fix.log`|实现者修后定向 7 项通过，包含路径断言和 worktree 保护。|
|`reviewer/recheck.log` / `unborn-head.json`|审查者修后独立 3 项通过，R1 关闭。|
|`reviewer/fixed-source-identity.json`|八文件身份匹配修后候选；独立冻结内容 PASS/283。|

初次源码审查时，上述最终发行、兼容、性能、CI 与远端事项均未完成；后续已核对范围见下一节。旧 D 包或第一候选包的结果不能代替修后发行。真实模型、真实两模板六阶段、终态外部 fence 对账与 worker 重启仍按 F3.4b–e 单独实施和验收。

## 最终本地发行、精确 CI 与源码远端补充核对

生产/测试提交：[ef8068a754446ae8da85fc25e8515f6acce60250](https://github.com/626619403/Ergora/commit/ef8068a754446ae8da85fc25e8515f6acce60250)。最终 wheel SHA256 为 `7c1fa4bfe066a42eb89e612a2fc9c6234f26b4722c55c8333cbf2fcf00175477`，八文件身份仍为 `7238c7fec9ffb664bed1dfe80bfd812721eb864960dbf8e55d1e4f4a8911e3e3`。本次追加未修改源码、安装、重跑完整套件或操作已有服务。

### 身份与安装

审查者另写 `reviewer/final-local-check.py`，独立计算源码目录、最终 wheel 内全部包文件、精确提交的 `git archive` 和两处已安装包的摘要：**346 文件全部一致**。八个生产/测试文件也分别与该提交 blob 及候选清单匹配，没有把工作区文档变更算作新的运行身份。

通过两套解释器的 `-I` 导入确认实际来自各自 site-packages，而非源码路径；Python 3.11.15 开发安装与 Python 3.12.3 基础安装都独立验证冻结参考 PASS/283，基础安装确实没有 FastAPI、Temporal 或 GEPA。原 `verify-package.py` 会改写证据 JSON，因此本次使用独立的只读重算，没有执行它覆盖作者记录。结果见 `reviewer/final-local-check.json/log`。

### 最终旅程、恢复与性能证据

已阅读全文和核验 `journey-performance-final.py/log` 与 `journey-performance.json`，确认最终 wheel 身份及两模板共 74 次 CLI 调用；计数包括 22 次 export、20 次 resume-export 和 24 次 export-status，其余为注册、预览、创建与提交。每模板三类本地重复各 10 次。审查者从 74 条原始计时重新计算全部 median/max，与已报告值逐项一致；JSON 也与最终原始日志一致。首次导出为治理 2245.82ms、大型 2268.90ms；重复最大 1314.59ms。

进一步通过最终已安装包读取两个最终旅程回执，核 native 字节、原 base HEAD、未提交文件、实际目标 ref、无 FETCH_HEAD、租约释放及各自唯一的 doctor/start/fetch/ref/result 调用。这里的候选结果与服务端端口由 fixture 提供，实际 Git、不可变记录、子进程和租约保留为真实实现；不将其当作真实 RPC、模型或六阶段成功。没有独立重跑全部 74 命令，也没有把含 SDK 导入及并发回归负载的端到端计时称为纯启动性能。

D 兼容证据按两步核对：固定 D 先生成两模板十态，再由**首候选**首次明确恢复；**最终 wheel**在这些已恢复的目录中原地读取/明确重复。审查者将 D 清单的两个关键源码摘要与固定 D 提交匹配，重新计算十态原文件摘要、核 start 总数和前后状态，并对每模板 prepared 已恢复及 unknown 未找到两类执行已安装只读查询。原字节及总 start 次数匹配；本次没有再次首次恢复 prepared。

另独立核六个 B/C1/C2 历史项目的 config/execution 全量原生字节，并补查其中 **10 个原 approval/cancellation 响应**与 D 基线保存值一致。最终安装也只读核对两个首候选导出回执，读取前后原生字节保持。上述记录均在 `reviewer/final-local-check.json`，作者的 `upgrade-d-baseline/candidate` 与 `final-compatibility` 各自保留原范围。

已阅读全文和核验 `lock-contention.py/json/log`：原 SDK connect 受控等待 18 秒，其他项目写者 18.80ms 成功，同 task 的 export/resume-export/create/resume-create 均在远程返回前明确 busy，后续另一项目仍能继续写。审查者通过只读 SQLite 连接确认实际另一项目 revision 为 6，原始日志与 JSON 一致，且实际只一次 fetch/ref 事务。统计重算和实际 DB 读取结果见 `reviewer/performance-recompute.py/json/log`；未把这次受控等待扩大成实际网络或规模化性能结论。

### 精确 CI 与远端

审查者读取并独立解析保存的官方 [run 41589227955](https://github.com/626619403/Ergora/actions/runs/41589227955) 和两个 job 原 HTML，核对精确提交链接、run/job 归属、必需步骤的完成状态及各 step 日志 URL 中的精确提交 SHA；原 HTML 摘要也与证据清单匹配。

- Windows / Python 3.12 job `125761835367`：构建并安装 wheel、包内参考身份、原生应用回归及 PowerShell 5.1 安装/升级四项均 success。
- Ubuntu / Python 3.11 job `125761835523`：构建并安装 wheel、包内参考身份和原生应用回归三项均 success。

本次证据方法是官方 GitHub HTML 核对，没有虚构本次 API 请求失败。审查者另执行新的只读 `git ls-remote`，确认 origin 为预期 Ergora GitHub 仓库，`refs/heads/refactor/architecture-foundations` 精确指向 `ef8068a754446ae8da85fc25e8515f6acce60250`。独立证据为 `reviewer/ci-remote-check.py/json/log` 和 `reviewer/remote-head.txt`；它证明该源码候选的远端身份，不预先证明之后的文档提交。

### 文档与尚待收口

USAGE 的命令、API 路径、严格确认、unknown 不重新 fetch/创建、租约和备份边界均与实现一致；两份架构图和职责表接入实际新模块，没有将终态外部对账标为已实现。交付记录已区分初候选与最终包、首次恢复与原地重复，以及真实执行与端口 fixture。

**本地最终 wheel 完整回归仍在运行，尚无终结结果。** 已核对 `wheel-regression-command.json` 使用最终 wheel 身份和已安装包路径范围，但不从进度点或精确 CI 成功推导该运行通过。取得完整回归终结证据后仍需复核，再完成最终文档交接；当前源码/可维护性结论无新增未解决 finding。
