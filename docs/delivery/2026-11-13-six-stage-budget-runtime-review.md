# B2b／c 运行预算独立评审

当前已完成 r4 完整 31 文件本地出口：**Standards approve、开放 0；Spec approve、开放 0**。ST1／ST2／ST3／SP1／SP2 均已修正复核关闭；r3 的 7 份产品和 10 份测试文件在 r4 逐字保持。自身模型首轮超时无判词，次轮原判词仍为 request-changes，唯一意见经独立核原合同及实际原件后不采纳，处置详见下文。普通本地提交 `a00896146c6499f58ae86a5b6b76fa13c3c7c796` 的精确对象补核已通过；推送、精确远端 Ref 和本候选自己的必要 CI 仍待后续出口，本报告不宣称发布完成。

以下保留各候选自己的判词与失败范围，不把后续修正追溯为旧候选通过。报告末尾的本轮状态优先于 r1／r2 中作为历史保留的开放状态。

## r1 历史判词与范围

日期：2026-11-13。范围：同一未发布 B2b／c 运行片的 r1 实现接缝；不是该片最终出口或公共执行验收。协调者为 fresh-context `/root/budget_runtime_review`，Standards 与 Spec 分别由两个 `fork_turns: none` 新上下文审查者独立完成。依照 `maintainable-project-delivery` 的 independent-review brief 与 `code-review` 两轴流程，只读产品及证据；本轮唯一写入为本报告。

**r1 判词：Standards 需修（P2 一项、P3 一项）；Spec 需修（P2 一项）。** 两轴分别记录，不互相抵销。修正及其行为验证、同片完整最终候选补核均待完成。

## 精确身份与范围

- 基线及当时 HEAD：`c46f3834df08927f7d266757c0f7d3fae8308fb8`；分支 `refactor/architecture-foundations`。`git log <baseline>..HEAD --oneline` 为空，`git diff <baseline>...HEAD` 不含本次未提交实现。
- 实际候选以私有持久目录 `.ergora/checks/six-stage-budget-runtime/review-r1/` 的 `manifest.json`、`tracked.patch` 及完整 `files/` 为准，包含新文件。协调者逐份核对了 14 件大小与 SHA256，全部匹配，未以仅含 tracked 文件的 Git diff 代替；这些私有原件不随公共 Git 文档发布。
- manifest SHA256：`d722df92d5d8cda4544db1ef0593a14898272aa9329ffb70ebee83ea33c8c8c7`；tracked.patch SHA256：`ebc569d9b50960551adb2facd7df51213fa4a02551445156818edfd15371a0cb`。

|冻结文件组|全部文件|
|---|---|
|产品 6 件|`src/ergora/processes.py`、`reference_executor.py`、`reference_inputs.py`、`reference_job_lifecycle.py`、`reference_task_submission.py`、`reference_workflows.py`（后五件同属 `src/ergora/`）|
|测试 3 件|`tests/test_architecture_boundaries.py`、`tests/test_budget_jobs.py`、`tests/test_budget_workflow.py`|
|文档 5 件|`docs/PLAN.md`、`docs/plans/2026-11-12-six-stage-budget.md`、`docs/delivery/2026-11-12-six-stage-budget-runtime.md`、`docs/delivery/2026-11-12-six-stage-budget.md`、`docs/delivery/2026-11-13-six-stage-budget-ci-review.md`|

原需求先于作者交付叙述读取：[预算合同](../plans/2026-11-12-six-stage-budget.md)、[原六阶段父计划](../plans/2026-11-12-six-stage-native-consumer.md)及 `AGENTS.md`。必要邻接包括原 Workflow、FileAdapter、Executor／jobs ledger、Sandbox／process_job、预算合同及 Portability workflow；这些原参考代码未被本轮修改。

r1 的 `BudgetedInput.execution_enabled=False`，公共 start／worker／直接 Executor 仍关闭。测试中临时覆盖 `require_submission` 仅供内部 owner 验收。本报告不把这个明确边界、尚待的安装／自身审查／真实模型旅程列为已宣称完成的功能缺陷。作者在工作树继续推进的提交与开放改动不属于 r1；后续必须冻结完整候选再补核。

## Standards

判词：需修，2 项硬规则问题；未另报判断性 smell。

### ST1 — P2：Windows 在平台跳过前即收集失败

- 位置：冻结 `tests/test_budget_jobs.py:4`，平台标记在 `:21`。
- 规则：[Windows 支持说明](../WINDOWS.md)第 3 行保留原生控制面；既有 `.github/workflows/portability.yml:50` 在 Windows 收集完整 `tests`。
- 可达例及影响：顶层 `import fcntl` 在 Windows 直接抛出 `ModuleNotFoundError`，pytest 尚未应用 `pytestmark = skipif(...)`，因此整轮 Native application regression 会中断，其他受支持控制面检查也无法继续。
- 最小修正：将 `fcntl` 导入移入实际使用它的 Linux 测试函数，或在导入前执行适当的模块级平台跳过。修正后需确认 Windows collection；Linux 的四个 Windows 专属 skip 不能证明这点。
- 状态：开放；已向实现者反馈，修正候选待补核。

### ST2 — P3：当前恢复入口与同份交付记录冲突

- 位置：冻结 `docs/plans/2026-11-12-six-stage-budget.md:88`、`docs/delivery/2026-11-12-six-stage-budget-runtime.md:3`。
- 规则：`AGENTS.md` 要求实现／检查变化时更新当前计划与交付；maintainable skill 要求区分实现、验证和评审状态。
- 可达例及影响：当前段仍写“B2c未实现／原生取消待验”，而同一冻结交付记录 `:35–45` 已记载 body／collection／finalizer 接入、原 attempt／ledger 恢复及原生取消检查通过；新接手者会得到冲突状态。
- 最小修正：把当前段更新为“已实现接缝、部分受控验收通过、剩余验收／发布待”，保留历史失败、历史候选及尚待项目。
- 状态：开放；已向实现者反馈，修正候选待补核。

本轴核过新模块／函数真实生产入口、共同 factory、生命周期 guard、原 ledger 与恢复边界。`DirectJob`／`BudgetedJob` 是实际输入变体，由 `WorkflowInput` 选择；owner 和 child 各有实际进程入口。未发现应仅因单次调用而拆除的抽象。没有用 smell 数量或假想复用要求新增设计。

## Spec

判词：request-changes，1 项 P2。已实现范围内未发现其他要求缺失，未发现未要求的 scope creep。

### SP1 — P2：executor 重启漏计仍在运行的独立 owner

- 要求：预算合同 `:72`：“不会仅以模型返回、future.done或Temporal关闭释放仍未确认的资源”；并要求保持原安装级 active 上限，区分它与单 task 祖先并发。原 job 锁不能代替安装上限。
- 位置：冻结 `src/ergora/reference_job_lifecycle.py:84` 以独立 session 启动 owner；`src/ergora/reference_executor.py:825` 重建空 `active`，`:837–841` 只按本进程 future 数量及路径排序准入。
- 可达例及影响：`max_parallel_jobs=1`，任务 z 的 owner／body 尚在运行，executor 父进程退出；此时新增排序更前的任务 a 请求后重启 main，a 会先获准执行，z 的独立 owner 仍在运行，形成两个实际 owner 并发。新 main 没有先按原 ledger、attempt 或停止证据恢复在途占用。
- 最小修正：重启时先沿原 jobs ledger、attempt 及 owner 停止证据恢复在途占用，再准入新 job；未确认停止的占用继续保留，不增加第二账本。补真实父退出／重启、跨 job 且新请求排序更前的回归；仅重入同一 job 的锁检查不足。
- 状态：开放；实现者已收到并准备修正。当前为静态可达结论，未冒称已运行该复现。

本轴沿实际调用核过共同 factory、同一截止、静态 slot 与 attempt、三种正式终态门禁、collection／fsync、unknown 不重跑、正式 receipt 后 ledger 恢复及旧默认路径；在上述范围未发现其他 Spec 问题。公共开放、隔离安装、自身审查及最终真实模型六阶段旅程仍是明确待办。

## 检查与证据边界

独立执行的是只读核对：基线／候选身份、14 件冻结文件 hash、冻结 Python 语法及覆盖后的 60 节点静态依赖图无环；新 job 模块由 `reference_inputs` 导入，显式 child 命令在另一进程进入原 Executor。另按原 manifest 读取并核验了 283 份参考文件，issue 为 0；未修改冻结参考代码。

已读取下列作者保存的原 `result.json`／`stdout.txt`。它们证明各自运行范围，本报告未重跑测试，未把通过次数作为评审判词；pytest 时间与外层进程时间分别保留原值。

|原件目录（均位于 `.ergora/checks/six-stage-budget-runtime/`）|实际记录|
|---|---|
|`b2b-source-r2`|真实本地 Temporal：queued／owner／activity-queue／poll-retry 四项通过，pytest 40.78 秒|
|`b2b-source-r3`|native-cancel、FENCING 两项通过；review-scope 在受控 verify actor 错为 agent 时失败，pytest 33.18 秒；原失败保持|
|`b2b-source-r4`|修正受控 verify CI 身份／check 后 review-scope 一项通过，pytest 16.43 秒|
|`b2c-source-r1`|驱动误载旧安装的六项失败；不当作当前产品 red 或通过，原件与纠正说明保持|
|`b2c-source-r2`|23 通过、4 个 Windows 专属 skip、1 个故障注入变量递归失败，pytest 51.76 秒；该 Linux 运行不覆盖 ST1|
|`b2c-source-r3`|慢 collection 与最终 fsync 两项通过，pytest 21.18 秒|
|`b2c-source-r4`|原 attempt unknown 不重跑、receipt 后 ledger 更新丢失恢复两项通过，pytest 13.04 秒|

未执行安装、模型、测试、提交或网络操作；未更改产品、测试、计划或其他公开文档。尚需 ST1／ST2／SP1 修正及受影响行为验证、完整最终候选的同片两轴补核、实际公共提交链／slot 与安装／自身审查证据；最终真实六阶段旅程仍按原 C／D 边界验收，不能由本轮受控进程检查提前关闭。

两轴计数：Standards 2（最重 P2 ST1）；Spec 1（最重 P2 SP1）。

## r2 完整代码候选补核

r2 将 v9 start／worker／请求根接通，尚未发布；本轮已按扩大后的完整范围审查提交、恢复与执行，未沿用 r1 的公共关闭边界。原基线仍为 `c46f3834df08927f7d266757c0f7d3fae8308fb8`。同片两位原独立审查者分别复核了 `.ergora/checks/six-stage-budget-runtime/review-r2/` 中全部 24 文件、完整 patch 及必要邻接；7 件文档、7 件产品、10 件测试的精确路径以 manifest 为准，包含全部新文件。

协调者逐件核得 24 件共 412462 字节，大小及 hash 全部匹配。manifest SHA256：`a8caaed13d83cd8bf0c46a1f5b0c7a802a31d55a434af5a12128cfee08fc51cc`；tracked.patch SHA256：`d01158b65ddc0de8ac6958cb586fa023d9de49484992688350ba031329c48af2`。17 份冻结 Python 均可解析，完整源覆盖图 60 节点无环，283 参考文件按原 manifest 核验无差异。冻结中的本报告仅作历史原件，不触发递归审查。

### r2 Standards

判词：需修，新增 ST3 一项 P2；未另见足以报告的结构 smell。

- ST1 静态复核关闭：`fcntl` 已移入 Linux 测试函数，模块导入不再先于平台 skip 失败。未独验 Windows 运行。
- ST2 关闭：当前计划、父计划和运行记录已同步源码状态，历史结果及剩余验收边界明确。
- **ST3 — P2，冻结 `src/ergora/reference_executor.py:849`**：服务扫描无条件跳过已有正式 receipt 或 rejection 的请求。owner 在 terminal 链接后、`record_terminal()` 更新 ledger 前退出时，原行仍为 `OWNED`；重启持续计入容量却永不调用已有 `reconcile()`，满额后全部新任务永久等待。违反预算计划 `:72` 的“正式receipt已发布而ledger更新中断时只恢复原状态更新”及 `AGENTS.md` 保留原恢复合同的要求。最小修正：允许 retained 且已有 terminal 的原 job 越过普通 receipt／rejected 过滤，交原 owner 核候选及停止 witness 后只恢复 ledger，继续禁止重跑 body。

本轴核过 v9 工厂、提交／恢复、旧输入、OWNED 崩溃边界、唯一 finalizer、实际调用者与新增检查；仅静态及原件只读核查。

### r2 Spec

判词：request-changes；原 SP1 关闭，新增 SP2 一项 P2。已实现范围未发现其他要求缺失，未发现 scope creep。

- SP1 关闭：冻结 `reference_job_lifecycle.py:78–82` 在独立 owner spawn 前沿原 jobs 表持久化 `OWNED`；`reference_executor.py:824`、`:845` 将它与当前 future 合并计占用，单次入口 `:828` 也核容量。unknown／rejected 不退款，未增加第二账本。两份旧实现 red 及修正 green 原件已读。
- **SP2 — P2，冻结 `src/ergora/reference_executor.py:849`**：预算计划 `:72` 要求“正式receipt已发布而ledger更新中断时只恢复原状态更新”。已有 receipt／rejected 的过滤挡住了原生命周期模块 `:218` 的恢复分支；当 owner 已发布 SUCCEEDED、ledger 更新中断而仍为 OWNED 时，常驻 executor 重启不会恢复该终态占用，`max_parallel_jobs=1` 时后续全部任务永久等待。显式单次调用能够恢复，不能代替服务扫描。最小修正与 ST3 指向同一原 owner 恢复入口，包括此前 rejected 的已确认终态，禁止执行 body。

两轴的 ST3／SP2 是同一个服务恢复根因，分别保留其标准和需求判词，不按两次产品缺陷计数。r2 本身仍需修；后续 live 修正不计入这一冻结判词。

### r2 原件及安装范围

私有根仍为 `.ergora/checks/six-stage-budget-runtime/`。新增读取的原件包括：`submission-source-r1` 三项通过；`pipeline-source-r1` 原九 job／七 slot 受控串行驱动通过（受控 Agent CLI，不是真实 Temporal 完整六阶段旅程）；`b2c-source-r5` 原生 Git 锁通过；`restart-red-r1` 父 SIGKILL 后 running／unknown 两例旧实现实际失败（pytest 25.63 秒）；`restart-green-r1` 两项通过（24.07 秒）；`jobs-final-source-r1` 33 通过／4 个 Windows 专属 skip（156.54 秒）。

新增 ST3／SP2 的实际 red 保留于 `install-r1/original-receipt-red-r1`：扩展原 published-terminal 测试后，一项在未改安装包失败（pytest 13.42 秒），正式 receipt 始终 SUCCEEDED，原 ledger 留在 OWNED。它不被既有单次恢复通过覆盖，也不被后续修正抹去。

协调者独立只读核了 `install-r1` 的 wheel、安装文件及两份 RECORD：wheel SHA256 `e5be26b77c6f1738c774e19c374a8bdb4e0e6a3c8b01bab20e31ecd0553e5d5b`；456 产品文件、461 wheel 文件／RECORD 行、466 installed RECORD 行。两份 RECORD 各自 hash／size 正确，安装后正常改写的 RECORD 正文单独核验，其他 wheel／installed 字节一致；全部产品与 r2 冻结源覆盖一致，非 editable，283 冻结匹配。

|安装原件|原运行终态与范围|
|---|---|
|`install-r1/core-r1`|40 项通过，pytest 226.66 秒；budget jobs／submission／prepare 合同与架构|
|`install-r1/original-r1`|46 项通过，pytest 355.44 秒；原完整材料、Executor 和 composition transport|
|`install-r1/temporal-r1`|真实本地 Temporal 七项通过，pytest 85.39 秒|

上述运行只属于 r2 产品候选的安装包，仍不能证明后续修正包做过同一整套。自身模板首轮／聚焦补核、最终代码复核及发布分别记录；本轮审查者未运行测试、安装、模型或网络。

## r3 代码修正与独立复核

同片两位原独立审查者分别审查了 `.ergora/checks/six-stage-budget-runtime/review-r3/` 的完整 24 文件候选及必要邻接。基线仍为 `c46f3834df08927f7d266757c0f7d3fae8308fb8`。协调者逐件核对共 417257 字节、所有大小与 SHA256；manifest SHA256 为 `98fa623408b399f0004516bfd068a39f841acc1b50894e8e9366bb3f6bd4d303`，tracked.patch SHA256 为 `efa2e6a2ea890db4ffd20bb642cb1b20f64f4e865631ba638a89c2a6441c6669`。相较 r2，仅 `docs/PLAN.md`、运行交付记录、`reference_executor.py` 和 `test_budget_jobs.py` 改动；17 份 Python 可解析，覆盖后的 60 模块静态依赖图无环。

### r3 Standards

**判词：approve，开放 finding 0。** ST3 关闭；ST1／ST2 保持关闭。修正在冻结 `src/ergora/reference_executor.py:852–858`：仅当原 jobs 表仍为 OWNED 且正式 receipt 已存在时，允许原请求越过普通 receipt／rejected 过滤，交既有 factory 与 owner 恢复。原 owner 锁、attempt、停止 witness 和候选字节核验仍负责准入，只恢复原 ledger 状态，不重跑 body；没有 receipt 的 unknown 仍占用容量。新增 daemon 路径回归覆盖先前未被显式单次调用覆盖的接缝。未发现新增结构 smell、不必要抽象或重复 CI。

### r3 Spec

**判词：approve，开放 finding 0。** SP2 关闭；SP1 保持关闭。服务扫描已可进入 `reference_job_lifecycle.py:212–225` 的原终态恢复分支，符合预算合同第 72 行“正式 receipt 已发布而 ledger 更新中断时只恢复原状态更新”。恢复前仍验证同一停止证据和原候选，未增加执行 attempt；unknown／未确认占用不退款。共同 factory、统一 deadline、slot 与 attempt、全部正式终态的停止门禁及旧默认路径保持，没有引入第二调度器或账本，未发现规格缺失或范围扩张。

### r3 行为与新安装原件

实际修正 green 保存于 `original-receipt-green-r1`：daemon 正式终态恢复及父退出后的 live／unknown 三项通过，pytest 31.62 秒。原 `install-r1/original-receipt-red-r1` 的失败保留。

协调者独立只读核验 `install-r2`：wheel SHA256 为 `b4e14c1558c6f178e67f323ab392a8096f76256ed070320a7646dfd4db40418e`；456 产品文件、461 wheel 文件／RECORD 行、466 installed RECORD 行。两份 RECORD 的大小和 hash 均正确；除安装时正常改写的 RECORD 正文单独核验外，wheel／installed 字节匹配；全部产品与 r3 冻结源覆盖一致、非 editable，283 参考文件无差异。

`install-r2/affected-r1` 使用该隔离安装运行 budget jobs 与架构检查，**25 项通过，pytest 108.05 秒**（外层进程 109.89 秒），包含本次 daemon 终态恢复、父退出 live／unknown 及单次入口容量边界。旧 `install-r1` 的 40／46／7 项分别属于其旧产品候选，不记作 install-r2 完整重跑；本轮没有要求或声称重复整套运行。

## 自身模型审查原件与意见处置

自身模板运行与上述独立两轴分别记录。以下均为读取既有原件后的核验，审查者未重跑模型；两轮也不构成不同后端成功。

|实际运行|材料与原终态|
|---|---|
|`self-review-r1-codex`，run `133543f065244b2ea4d29fcc1e674066`|实际 bundled 结构审查模板，完整 24 文件候选附件 414096 字节；1801.98 秒后 timed_out，**无模型判词**。协调者从 native 原始 task-MCP 返回重建五份 scope 资源，候选的 14 个连续 UTF-8 页及其余资源均至 `next_offset=null`；完整材料送达不等于产生了审查结论。原超时及命名为 partial 的历史 audit 保留。|
|`self-review-r2-codex`，run `e907ecac9a2645ada09d1bc76d5176d4`|聚焦最终产品 diff、六份完整相关文件，以及明确标作 excerpt 的 Executor 发布段；8 件原 packet 共 110017 字节，加边界组装为 110685 字节附件。760.626 秒后执行状态 succeeded，**原 decision 为 request-changes**。这不是完整 24／31 文件模型审查，也不把 excerpt 称为完整 Executor。|

第二轮附件 SHA256 为 `589fc1e1c9f16cf1a6a473aa8dbb423ffe44f8d230f1741e62e8656b58f80264`，input digest 为 `18619263b82b47a6fa3271fba4ff672a54115856d3cea54ddbb69fff7675c72f`，prompt SHA256 为 `bce5d98d141197c2a8f4c12a6d5ca67e6a23028095fe52af73b71aa5a86a6813`，原 result SHA256 为 `943662fd08323664404ca0e86ff5c0f519986e7566f17969e9678ad0cf850eb0`。这些身份连同原材料、native stream 和结果均保留在同名私有运行目录及 `self-review-r2-codex-read-audit.json`，不以摘要重写模型原件。

协调者独立核过 manifest→prepared input→实际 input→prompt／stdin→admission→scope→原 result 的绑定；bundled 模板只作已标明的修订、证据资源与运行限额修改。8 件 packet 的 hash、六份完整文件与 r3 的字节、组装附件、原 result 拷贝和 review 正文均匹配。五份 scope 实际 UTF-8 原文分别为 354、480、110685、521、163 字节；候选页偏移为 0、24000、48000、68000、88000、104000，末页至 null，没有漏页或失败 MCP 调用。四个已采样的自有进程均不存活，不据此推断未采样进程。

原后端报告 turn usage 为 input 239809，其中 cached input 174336；output 2039，reasoning output 994 单列。cached 已包含在 input 中，不重复相加；该记录不推断账单或全部模型成本。

### 唯一模型 P2：不采纳，保留原 request-changes

模型要求在正式发布前统一把已有 FAILED 改成晚到 fence 对应的 CANCELLED，并声称后代回收期间收到 fence 后仍能成功 collection、发布 FAILED。独立 Spec 审查者沿原需求、原 Executor 和监督实现核查后未采纳；Standards 复核确认处置有原件支撑，没有将模型改记为 approve。

- [预算合同](../plans/2026-11-12-six-stage-budget.md)第 54、63、72 行要求 SUCCEEDED／FAILED／CANCELLED 均先确认整个拥有树停止、完成必要收集核验，再发布正式 receipt；第 9 行禁止未确认或超期的额内成功。合同没有规定晚到 fence 必须覆盖已经验证的 FAILED，也没有取消原失败状态的既有含义。
- 冻结参考 `src/ergora/data/reference/platform/local/agent_platform/executor.py:270–273` 在生成错误 receipt 时检查当时的 fence 来选择 CANCELLED 或 FAILED，没有发布前统一重写所有非成功终态的规则。当前 `reference_job_lifecycle.py:152–170` 先停止 body，再决定是否 collection、确认 collection 停止后才 finalize；`:178–203` 为全部候选记截止、取消及超时事实，并对成功额外执行发布前授权门禁。已有 FAILED 可在稍后的收集／finalize 窗口继续保留，但不绕过全终态停止门禁。
- `test_budget_jobs.py:164–208` 的三个参数在 body 回收后代期间发 fence。`processes.py:157–158` 在 supervised 回收后再次检查停止条件，将 body 状态置为 cancelled；该路径不会继续 collection 已有 pending。协调者直接读取 `install-r2/affected-r1/cases/` 的停止 witness 与正式 receipt：pending SUCCEEDED、FAILED、CANCELLED 三例的 `body.status` 均为 cancelled、`cleanup_confirmed=true`、正式终态均为 CANCELLED。`test_pending_terminal_cannot_ccurrent` 是第三例 `c2` 的符号链接；`model-finding-disposition-evidence.json` 的四个目录条目实际只有三个独立 case，不能多计为第四例。

因此，模型描述的 body 回收→成功 collection 因果与代码及三份实际原件不符；另一个稍后收到 fence 而保留已有 FAILED 的窗口没有违反原合同。原 FileAdapter 以停止证据及有效终态确认 fence，workflow 保持 BLOCKED／CANCEL_UNCONFIRMED 与确认取消的区分。没有为改变既有终态优先级而新增无要求的产品行为、测试或模型重跑。**不采纳的是这一 finding；该运行原 request-changes 判词、范围和用量计数事实均保持。**

## r4 完整文档与本地最终出口

同片两位原独立审查者分别补核 `.ergora/checks/six-stage-budget-runtime/review-r4/` 的完整 **31 文件、741589 字节**候选及必要邻接。基线仍为 `c46f3834df08927f7d266757c0f7d3fae8308fb8`；manifest SHA256 为 `fbda1ba90ed3c64760f70dd681513c469a221c25d05f004f59d9be2db7647b8e`，tracked.patch SHA256 为 `c6c433676fbeeb0d72afaac71294d1dee8ed0c66c355ffe50ae1540d36646c05`。协调者与两轴分别核对全部尺寸与 hash；7 份产品及 10 份测试与 r3 逐字一致，沿用各轴已完成的代码判词。

r4 在原 24 文件基础上增加 `README.md`、`docs/USAGE.md`、`docs/WORKFLOW_DEFINITIONS.md`、`docs/architecture/current.md`、`docs/architecture/contracts-and-identities.md`、`docs/architecture/reference-boundary.md` 和 `docs/plans/2026-11-12-specialist-template-refresh.md` 七份文档；同时补齐当前 PLAN、预算计划、运行交付及 B2a 历史记录的状态。冻结时本报告止于 r2，仅作为历史原件；本次补齐报告是已审结论的持久化，不启动对评审记账的递归审查，也不改写冻结 manifest。

### r4 Standards

**判词：approve，开放 finding 0。** 结论覆盖完整 31 文件本地候选。七份新增手册／架构／上层计划准确描述 prepare→双摘要 create→原 submission／workflow→专用 owner→停止后 collection／finalizer→原 receipt／ledger 的职责；当前源码、B2a 历史和后续 C／D 状态相符。文档没有将静态调用图、受控串行旅程、slot 或预算写成已实现的完整嵌套执行、真实模型旅程、provider 请求额度或内核强实时保证。ST1／ST2 保持 r2 关闭，ST3 保持 r3 关闭。

### r4 Spec

**判词：approve，开放 finding 0。** 结论覆盖完整 31 文件本地候选。新增文档准确对应 v5 definition／input9 的 prepare、双摘要 create，以及既有 start／批准／取消／恢复入口；专用 `.composition-v9` queue 与 `requests-composition-v9` 根、同一授权覆盖等待／重试／整个 job／收尾的边界清楚。slot 未等同实际调用或 provider 额度，unknown 保留占用、原 attempt 不重跑和正式 receipt 后仅恢复 ledger 的语义与实现一致。SP1／SP2 保持关闭，未发现规格缺失、额外范围或新增错误；不承诺 OS 隔离或 provider token／费用控制，C／D 的嵌套消费者和真实模型完整六阶段旅程仍明确待完成。

### 最终 finding 状态与剩余出口

|历史 finding|最终状态|
|---|---|
|ST1 P2：Windows 顶层 fcntl 导入|r2 静态复核关闭；未将 Linux skip 视为 Windows 运行通过|
|ST2 P3：当前状态冲突|r2 关闭，r4 扩大文档范围后保持关闭|
|SP1 P2：executor 重启漏计独立 owner|r2 关闭，旧实现 live／unknown red 保留|
|ST3／SP2 P2：daemon 正式 receipt 后漏恢复 ledger，同一根因|r3 关闭，原安装 red 及修正 green 分别保留|
|自身模型唯一 P2|原 request-changes 保留；经独立核原需求、代码及实际三 case 后不采纳|

作者静态原件 `static-r2/result.json` 对冻结 31 文件、312 个本地 Markdown 目标和六个已加载 secret 值检查，issues 为空、whitespace 通过，未新增依赖。该检查不覆盖 anchors、Mermaid 渲染、外部 URL 或运行行为，也不覆盖本次报告持久化后的新字节；后者单独核本地链接及空白。测试、安装、模型和静态通过次数均未替代独立两轴结论。

本轮只读审查及本报告写入已完成，未改产品、测试、计划或其他公开文档，也未执行测试、安装、模型或网络操作。**完整本地最终两轴为 Standards 0／Spec 0；普通发布、精确 Git／远端 Ref、本候选自己的必要 CI 及相应终核仍待。** Windows 实际执行不能由本轮静态关闭或 Linux skip 证明；最终 C／D 仍沿原阶段验收，受控九 job／七 slot 旅程和局部真实 Temporal 七场景不提前关闭它们。

## 普通本地提交的精确发布补核

日期：2026-11-13。本次仅核已生成的 Git 对象及作者原件，不借用可能继续推进 C 的当前工作树字节，也未执行网络操作。精确提交为 `a00896146c6499f58ae86a5b6b76fa13c3c7c796`，题名 `feat: enforce shared budgets across six-stage job lifecycles`，其唯一父提交为原基线 `c46f3834df08927f7d266757c0f7d3fae8308fb8`，tree 为 `c2d54a991115abd6d65d8befdc50bc3b59ac1daf`。作者 `closure/commit.json`／stdout 保存普通 `git commit` 成功，exit 0、1.11 秒；Git 对象也独立确认该提交已经存在。

协调者逐件用 `git cat-file`／`ls-tree` 核了该提交的全部 31 个变更路径，与 `.ergora/checks/six-stage-budget-runtime/closure/ready-r1/manifest.json` 及完整 `files/` 相等：共 754447 字节，blob 正文、大小、SHA256 和 `100644` 模式全部匹配，无额外变更路径。ready manifest SHA256 为 `f3505cdee95b0e357567bf96e8219d94c985198c1b2c99d085e6d541e3ce7917`，与作者 `closure/commit-identity.json` 相符。17 份产品／测试文件仍与 r4 逐字一致；相较 r4 的四份文档变化只是 PLAN／预算计划／运行记录的已完成本地出口状态，以及本报告补齐的 r3／r4 与模型处置，未引入产品变化。

该提交内本报告的正文 SHA256 为 `c27efcf637ac3bab3d5aa5f75aa2b5ea99ff229c150aea1618f71c0d023fb016`，26953 字节，Git blob 为 `09952c0d2818c2db8ea34cd5b68c39b239b1bdf6`、mode `100644`，精确对应先前交回实现者的最终本地报告。这一身份不会被当前追加文字追溯改写；本节自身是后续发布记账，尚不属于 `a008961` 的正文。

作者 `static-r3/result.json` 的全部 31 项路径／大小／SHA256 均与该提交对象匹配，记录 314 个本地目标、六个已加载 secret 值检查、issues 为空及 whitespace 通过。它覆盖提交时的完整报告字节；不覆盖本节新增文字，也仍不证明 anchors、Mermaid、外部 URL 或运行行为。

首次作者普通推送保留于 `closure/push.json`／stdout／stderr：明确 `force=false`，目标 `HEAD:refs/heads/refactor/architecture-foundations`，15.14 秒后 exit 128，stderr 为 `Connection timed out during banner exchange`。这是 SSH banner 交换未完成的失败原件，不能记作推送通过或认证拒绝。补核时所读 `closure/push-r2.json` 仍为 `exit=null`，stdout／stderr 为空；没有可据以确认成功的第二轮终态或精确远端 Ref。本地提交身份已通过，**推送、远端完整 SHA 及本候选自己的必要 CI 继续待核**；不借 B2a 的 Ref 或双 OS 结果关闭本片。
