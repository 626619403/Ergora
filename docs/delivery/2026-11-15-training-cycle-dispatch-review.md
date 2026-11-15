# c1a2 总投递／固定运行对账独立产品审查

日期：2026-11-15。审查者为新的 fresh-context 独立 reviewer；没有继承实施会话或设计结论。项目与文档归本仓库。仅只读源码／证据并维护本报告，没有改产品或测试、安装依赖、启动业务、commit 或 push。

基线为 `836179e9ff3eae0795f0c22bf4c58f0bab1ea777`，分支 `refactor/architecture-foundations`。初次范围由私有 `review-scope-r1.json` 固定：四个原产品 owner、原 submission 测试及两个 fixture、计划／交付／设计审查／`docs/PLAN.md`，共 11 文件；逐字副本与 tracked diff 均已读取。修正复核以 `review-scope-r2.json` 固定完整 12 文件（增加本报告）；最终本地终核以 `review-scope-r3.json`／`review-snapshot-r3/`／`review-tracked-r3.diff` 固定同一 12 文件边界，没有继承设计或旧包通过。后继 SDK 研究稿不属于本片。遵循根、源码、测试 `AGENTS.md`、组件协议及 `maintainable-project-delivery`、`ergora-codebase-quality` 的 module／test-value／style 指引。

## 当前结论

- 需求符合性：**最终本地 approve／开放 finding 0**。R1、R2 两项 P2 已先实红、最小修正并复核关闭；原安装 r1 的 67 项及最终 r2 的 7 项精准回归各保留其真实身份，r2 完整源／wheel／双安装、冻结输入与收尾已核同一。
- 可维护性：**最终本地 approve／开放 finding 0**。职责仍归原 owner；没有新增链遍历、调度账本、reaper 或无消费者的抽象。两行不可达 guard 已最小删除，原拒绝能力保留，没有为字段／提示句或不可达分支增加浅测。

本片只交付原 `_CycleOperation → S → H` 的总投递／观察，不把它当作总 Workflow、独立 cycle 服务、子训练、两轮 CPU 或 GPU 优化成功。六阶段、原 clock／唯一 reaper、start／launch 原账本、283 冻结来源、人工 release 与 kernel 专家 v3 的相应文件未在本片变更。

本结论绑定尚未提交的最终 package-r2 候选，wheel SHA256 为 `2707c7c0c66b4d22e4bed6d04342a4d7f8339ad88f809bd3829ac025a1b1aef8`。固定提交、普通发布和该提交自己的外部 CI 不在本次本地结论内，须另按原门禁核验。

## Findings

### R1 · P2 · 无 receipt 恢复丢失 latest 身份，不能按约定排除 reset

位置：初次候选 `src/ergora/reference_training_runtime.py:102–119`，以及 `tests/fixtures/training_controller_service.py` 的 reset 分支。

无 receipt 时，代码先 describe 最新 run，立即只取其 `first_run_id` 并改查首 run；后续只核首 run 的 started 字段。真实 reset 保留原首 run 身份和历史，因此这些核对仍会通过，worker 会补 receipt 并报告 submitted，而本片合同要求已知 reset 或来源不足保持 unknown。此处不会因此把 reset 后继写为 receipt，原固定 RUNNING gate 也未放宽；finding 针对错误认证的恢复结果和被丢弃的 reset 证据。

实证来自实施方新增的独立真实 metadata probe，本 reviewer 已读取脚本和结果：`sdk-reset-metadata-r1.json`，SDK 1.34.0／本地 Server 1.32.0，退出 0，实际 4.580 秒，server 退出 0／原身份不再活匹配。reset 后 latest run 改变，`describe.first_run_id` 仍为原首 run；latest.started 的 `original_execution_run_id` 也仍是首 run，continued 为空、initiator 为 0、attempt 为 1。固定首 run 已 TERMINATED，但其原 started 字段完整不变。SDK 自带 protobuf 文档也明确 first_execution_run_id 的链包含 Reset。初次替身把 reset 标志放入被查首 run 的 started，无法保护真实可达情况。

最小修正：没有原 receipt 或可信 run hint 时，保留首次 describe 的 latest 身份；只要 latest 与 first 不同，就保持 unknown，不补 receipt。该控制器本来不支持后继，continue／retry 同样保守处理即可，无须遍历链或复制状态机。已有 receipt 继续只查其精确 run；原四个执行 gate 继续严格核 RUNNING。用真实 probe 的 reset 形状修正原 SDK 替身，并在现有 S-H 恢复接缝验证没有新 start、没有 receipt；相应更新 CAN／retry 预期和计划措辞。

状态：**最终本地关闭**。修正 scope 在首次 describe 后新增 `description.run_id != first_run_id` 拒绝，读取首 run 前保留必要证据；原 fixed-run 分支和严格 RUNNING gate 未改变。替身改用真实 reset 形状，复用原恢复矩阵；修前 source-r3-red 的 reset 项实际返回 submitted、预期 unknown，实红；修后 source-r4 及安装 r1 对应项通过。CAN／retry 同样保持 unknown，计划已同步收窄。最终 r2 与 r1 的本 finding 相关 runtime／worker／原件算法及测试逐字一致；仅删除另一处不可达 bind guard，没有把旧 67 项改称新包全套结果。

### R2 · P2 · 终态 publisher 未在 reservation 中重读完整原授权链

位置：初次候选 `src/ergora/training_cycles.py:454–476`，`training_execution_protocol.py:477–507`。

`_record_controller` 在短 SQLite reservation 中只调用 `admission.submission()`。后者核当前 intent／attempt／receipt／rejection，却用 H 启动时已缓存的 `self.authorization` 重建期望值，没有重新读取磁盘上的 authorization／完整 plan／ready。可达情形是 H 已 `_load`，随后 SDK 等待期间这些原件损坏或被替换；返回后仍能写 receipt 或 rejection，与本片“终态发布重新验证完整原件，损坏或错身份原件不修复”的合同不符。claim 的 `_controller_ready → status → _load` 已做相应复核，终态分支缺少它。

receipt 是观察事实而非执行许可，故这不是停止或预算绕过；修正也不能让已 stop／expired 的纯观察失败。最小修正是在同一 reservation 中独立 `_load` 当前完整 plan／authorization／ready，核原 authorization SHA 与原身份及 ready 存在，再读取／发布同一终态；不要改用会拒绝停止状态的 `admission.check()`。在现有 SDK 等待接缝注入原授权漂移／损坏，确认不写终态、不重发 start、保留 attempt；原 stop／耗尽后的正常固定 run 对账仍应允许补原 receipt。

状态：**最终本地关闭**。修正 scope 在原 `BEGIN IMMEDIATE` 后先 `_load` 完整原 plan／authorization／ready，核原 SHA 和 ready，再读取／发布终态；没有新增执行状态检查。source-r3-red 在 SDK 替身已保存请求后破坏 authorization，旧产品仍返回 submitted，实红；source-r4 及安装 r1 对应项通过，不保存 receipt／rejection且保留 attempt／服务请求及损坏原件。安装 r1 的耗尽观察通过；最终 r2 与 r1 的 terminal publisher 及相应算法／测试逐字一致，原停止和耗尽后的观察权保留。

## 已核结构与测试价值

`CycleAdmission` 继续 stdlib-only，原件格式由原 owner 共用；`training_cycles` 只持本地短 reservation，网络在外；SDK 编排保留在 H。`_controller_history` 是两个 status 策略共享的完整 started input／memo／type／queue 算法，原 `lookup_controller` 仍要求同一精确 RUNNING run。新增 helper 都有实际 producer／consumer 或明确的私有算法职责，没有新的通用框架或回调包装。

已静态核旧 lookup 晚到的处理：claim 和前置拒绝共用 reservation，进入后重读全部投递原件，出现 attempt 就不保存旧 preexisting／lookup_rejected。receipt 与 rejection 互斥；部分文件不修复；相同终态不替换字节／inode。原 permission 持至 SDK 动作返回；claim／同步／注册核验消费同一普通窗口。reconcile 使用独立固定观察截止，没有 start 分支，不续原 clock。阻塞本地 I/O 仍在 H，由原 S／reaper 有界监督，父 loop 没有新增业务文件或 SQLite 操作。

原 submission 文件中的 SDK codec／历史身份、丢回复、NOT_FOUND、冲突、并发 late lookup、网络期间独立 writer、最后 stop／revision、同步阻塞、SDK 等待取消与耗尽后对账都覆盖可静默失效的真实转换；沿已有 fixture 和 CI 分组扩展合适。各个身份 fault 有不同保护作用，不应为减少测试数合并掉恢复或并发接缝。没有发现仓库配置要求额外 formatter／linter；`git diff --check` 已运行通过。

实施方另提出 `bind` 中重复的 rejected 分支，本 reviewer 已独立核其不可达：`submission()` 已拒绝 receipt 与 rejection 并存，合法 rejected 必有 `result_saved=False`，`bind` 紧接的原 receipt 检查已先抛错，随后再判断 rejected 没有可达路径。原运行终态后仅删除该两行，不为不可达分支增加测试。已直接比对 r1 原安装字节、r2 当前源码及全部 manifest：唯一变化确为这两行，其余 651 产品文件不变；r2 原 binding／固定 gate／冲突／并发接缝已通过。旧完整安装与自身供稿继续保留原身份。

## 验证身份与限制

证据位于私有 `.ergora/checks/training-cycle-dispatch/`；本 reviewer 未重新运行昂贵测试。

- source-r1：原脚本／JSON／stdout 已核，11 failed、40 passed，pytest 127.80 秒，驱动 129.684 秒／退出 1；运行前后输入 SHA 集合相同。新 S-H fixture 在 `-P` 下找不到 `training_controller_service`，11 个新增 case 没有进入预期 SDK 接缝。该失败不可被设计或 metadata probe 覆盖，也不把相同 unknown 的 unavailable case 当独立成功。
- source-r2：实施方修正 fixture 自身路径并增补实际接缝后，stdout 为 17 passed／125.59 秒，驱动 126.522 秒／退出 0；运行前后输入 SHA 集合相同。四个产品 owner 的字节仍与 r1 snapshot 一致，只证明 r2 选择范围，不认证已知 finding 修正或最终安装。
- source-r3-red：两项原 finding 在修前真实 S-H 接缝均失败，pytest 13.27 秒、驱动 14.184 秒／退出 1，前后输入 SHA 集合相同；错误实际都是 submitted 与预期 unknown 不符。
- source-r4：修后选择 9 passed／1 failed，pytest 67.47 秒、驱动 68.404 秒／退出 1，前后输入 SHA 集合相同；两 finding 对应项已通过。剩余失败是耗尽观察测试错误要求过期父响应带 attempt_saved。本 reviewer 另读原 helper/stdout，H 已返回含 attempt_saved 的 unknown，原 attempt 与服务请求存在；父侧按原 2 秒窗口拒收完整结果符合设计。最终测试改为观察原件并在有效 5 秒 control／10 秒 total 内运行，再按原 policy 等待耗尽，未改产品／续期；该项随后在安装 r1 通过，source-r4 原失败保持。
- 真实 run metadata／reset probe 只证明服务字段形状，不认证 Ergora 总 Workflow、业务训练或恢复全过程。完全相同材料与 memo 的人为完整 ID 重放仍无法单凭最新 metadata 识别；协议独占 ID 和 REJECT_DUPLICATE 前提应继续明确。
- 新构建 `build-install-r1` 各步退出 0。两新非 editable 安装各 652 文件，reviewer 直接重算当前 source／wheel／两 site-packages／package manifest 的 SHA，全部同一；wheel SHA 为 `1b3724be4110f0e0e0251b75c261b48a94f564f69a0055394f5a6e410d826264`。与基线相比只改四个原产品 owner，无新增／删除产品文件；core 无 SDK、SDK 安装为 1.34.0。两套原 reference 283／PASS 与依赖检查通过。
- `core-inspect-r1`：脚本和结果已读，实际安装的 SDK-free 异步 S-H cold inspect 通过，1.158 秒；禁止父 loop 打开 State／SQLite／业务原件 reader，原窗口、7 份原件 bytes 和 DB dump 保持。此探针没有记录 before／after inode，不把它称作 inode 实测或 SDK／Workflow 验收。
- `self-review-r1`：自身原结构模板通过，真实 Codex 65.884 秒、退出 0／approve；只认证完整供稿的静态结构。本 reviewer 重算了原结果 SHA、18 文件逐字 snapshot／452851 字节，核 prompt 与实际 stdin 一致、全部 18 文件和 3 份祖先资源正文均在原 stdin。没有异后端或独立产品通过主张。
- 安装 r1 回归使用 `installed-tests-final-r2` 的 178 份冻结输入。reviewer 直接核其 manifest／逐字副本／当前输入均同一；没有为测试观察修正重建未变化产品。`installed-r1` 已终态：stdout 67 passed／347.05 秒、驱动 JSON 退出 0／348.193 秒、JUnit 67 case／failure0／error0／skip0 三方相符。它覆盖新增 19 case、旧 controller gate／原 release、完整 runtime 和架构回归，仅认证 package-r1 身份。

### 最终 package-r2 与收尾

- `guard-removal-final-r1.json` 的结论已按原字节重新核实：r1→r2 只删除 `training_execution_protocol.bind` 两行不可达 guard；652 个产品文件中其余 651 完全同一，无新产品文件、依赖、schema、来源 key 或冻结参考变化。
- `build-install-r2` 所有步骤退出 0；两套 reference 均 283／PASS，依赖检查通过。本 reviewer 再直接重算当前源码、实际 wheel、core／SDK 两套 site-packages 与各自 manifest，652 文件逐份相同、wheel SHA 匹配。core 无 SDK，SDK 安装为原 1.34.0；未变更依赖 pin。
- `installed-r2`：实际新 SDK 安装使用 `-I -B`，退出 0／84.620 秒；stdout 7 passed／83.56 秒，JUnit 7 case／failure0／error0／skip0 一致。范围为原 bind（包括隔离 native 读取）、固定 RUNNING gate、四类冲突及 late lookup 并发／独立 writer。没有将 r1 旧 67 项归为 r2 全套运行。最终 `installed-tests-final-r3` 的 178 份 manifest、冻结正文和当前 tests／examples 均重新核同一，其内容也与安装 r1 使用的 final-r2 输入一致。
- `core-inspect-r2`：实际异步 cold inspect 1.210 秒通过；SDK 缺席，父 State／SQLite／业务原件 reader 被禁用，原 7 文件 bytes、DB dump 和窗口保持。该 probe 未记录 inode，也未调用 SDK／运行 Workflow／训练。
- `self-review-r2`：原结构模板真实 Codex 40.251 秒、退出 0／approve。本 reviewer 核原结果 SHA `3e65ff503fc291128b226a884e43e60ed68b7fb919ab326f611aac20a6759762`，18 份完整供稿共 458285 字节逐字 snapshot、prompt 与实际 stdin 同一，3 份祖先资源全文确在 stdin，全部产品／测试供稿与最终当前字节一致。它只认证实际供稿，未替代本独立审查或外部 CI。
- `integrity-cleanup-r1` 已读取脚本和结果；当前 source／两安装 652 与 178 输入保持。记录从各实际源码／安装运行及 metadata 原件收集 74 个已知身份，活匹配 0；reviewer 又逐个读取当前进程身份，仍为活匹配 0。这是已知记录身份的收尾核验，不声称扫描或认证整个宿主机进程。
- `static-final-r1` 记录本片 12 文件／180 个本地链接／缺失 0，`git diff --check` 退出 0；reviewer 再运行 diff check 通过。后继研究和尚未实施的服务／Workflow 没有被纳入该完成结论。

已另以只读 SHA 核对 r1 全部 11 份、r2 与最终 r3 各 12 份副本均匹配各自 scope manifest；终核开始时当前 12 文件与 r3 scope 一致。真实 reset probe 脚本 SHA 也匹配其结果 JSON。没有重新执行昂贵测试、安装或探针；额外操作只有只读身份核验和静态检查。本报告本次更新是同一审查的状态记录，不改变已核产品／测试字节。

下一步：由实施方记录最终独立本地两轴结果、固定该候选提交，并沿原顺序核其发布及准确 CI。总 Workflow、独立 cycle 服务／普通与停止配额、跨调用预算 owner 生命周期、后继轮接受门槛、公开入口和可信两轮训练仍属于后续切片；本片不声称这些能力已实现。

## 固定本地提交核验（追加）

本追加保留上文 15,833 字节原报告前缀及其 SHA256 `ceb7c13026cc0207a2de6bc0ac8ec09c5900fff59ddfa3b8c67897046a0eec57` 不变；该前缀与本次固定提交中的报告字节相同。上文“尚未提交／下一步固定”是独立本地终核时点的记录，固定身份以本追加为准。

已直接读取 Git 对象及私有 `local-commit-r1.json`／`commit-r1.stdout`／`.stderr`：当前分支仍为 `refactor/architecture-foundations`，HEAD 为 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，唯一父提交为 `836179e9ff3eae0795f0c22bf4c58f0bab1ea777`。提交变更范围恰为本片 12 文件；记录的 12 个 staged blob 逐一与提交 tree、当前 index 和工作树字节一致，记录 SHA256 也逐份匹配。

提交中的四个产品 owner、原 submission 测试及两个 fixture 与已终核 r3 snapshot 完全相同。终核后仅 `docs/PLAN.md`、本片计划和交付更新为已获独立本地结论；本 reviewer 已读其完整差异，没有新的产品、测试或能力变更。后继 SDK 研究稿和原 b2b0 审查状态文件没有混入本提交。

固定提交的需求符合性、可维护性两轴均 **approve／开放 finding 0／0**。此前 R1／R2、原失败、安装 r1 的 67 项和最终 r2 的 7 项继续保持各自身份；本次只核提交同一性，没有重跑测试，也没有更改产品或发布。普通发布尚未轮到本片，远端发布和准确 CI 仍须分别核验；后继服务、Workflow 与训练能力不在本结论内。
