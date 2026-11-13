# 受监管进程慢读取大输入：独立审查

审查者为 `/root/supervised_stdin_review`，以新的上下文开始；Spec 和 Standards 分别由新的、互不继承上下文的 `spec_axis`、`standards_axis` 审查者完成。按项目 AGENTS、maintainable-project-delivery 的 independent-review brief，以及用户指定 AIHERO 的 code-review／codebase-design 执行。审查仅只读源码、调用者和本片原件，只写本记录；没有安装、运行测试、模型、服务或远端操作。

## 身份与边界

基线及审查时 HEAD：`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`；分支 `refactor/architecture-foundations`。候选尚未提交，`baseline..HEAD` 没有新提交，实际审查对象是 `.ergora/checks/supervised-stdin/review-r1/` 的四文件快照、`source.diff` 和工作树对应内容。清单 SHA256：`cecddfb2fb66b079dff41e242aeb06c100ebb0d2f49ab052d6d4f6d0dce673b1`。

|文件|候选 SHA256|
|---|---|
|`src/ergora/processes.py`|`b5cacaa449aca7923bc4d967be64ad65a9412bad00b18caa84c11709ba09d0c8`|
|`tests/test_processes.py`|`fcd8682a8b9024d82040a913f72e49d6b14a3a8441af112a275a7f9ed7d3eb2e`|
|`docs/delivery/2026-11-13-supervised-stdin.md`|`a66026e0b7ccbd2b344ce9384e4faf20086a5bc9cb32a88f525ab08c0d8accb8`|
|`docs/PLAN.md`|`05daeeffa5695b40f07cbc8e39b24de5b853be191ff86f79d983b501fb369cba`|

四份快照、清单及当时工作树逐字匹配。工作树另有未提交的 B2a 数据／测试和 A2 文档，不纳入本片产品候选；PLAN 中的邻片状态指针不代表本片替其验收。

原要求为完整交付祖先 Skill/context 和实际可用长输入，保持原六阶段 task/run/candidate/budget/cleanup owner，大项独立审查。本片合同见[交付记录](2026-11-13-supervised-stdin.md)：修正原 `processes.run` 的慢 reader 输入阻塞，保留取消、归属、锁、清理和 Windows gate；原 A2、模型及 CI 失败不事后改为通过。

## Spec

**判词：已检查的实现范围内无 finding；整片实际验收尚未完成。** Spec 轴未发现已证明的需求遗漏、越界行为或实现错误。

交付要求“让子进程直接从已有、已完整记录的 stdin 快照文件读取”，并“保留原取消回调、进程归属、finalizer、清理与预算 owner；Windows 原 JSON 启动 gate 不变”。`processes.py:107` 先完成 UTF-8 快照，再于 `:121` 以 `rb` 从偏移零打开，`:126` 直接作为子进程 stdin；监督轮询改用 `wait`，输入与 EOF 不再依赖首次短时 `communicate` 是否完成。上下文管理将 FD 保留至原 kill/wait/reap 完成后，并覆盖启动异常和启动前取消的关闭路径。

外部 `stop_requested`、`lock_fd` 传递、会话选择、后代回收和状态判定保持。改动适用于公共 POSIX 路径，检查过的普通 agent、evaluation、optimization、doctor、kernel 调用者没有新增使用约束；Windows 分派和 JSON／Job gate 未改。未出现新的 task、预算账本、finalizer 或调度 owner。

原 probe、源码 red 和 green 保存的 stdin 均为 425,984B，含 32,768 个 CR、65,536 个 LF，SHA256 同为 `287dd78145d9feadcc9d095e8056e05bcff9629c43d9bf8b8620e4d3e39d8f6d`；green 子进程 stdout 为此摘要。原 probe 记录约 3.012 秒、cancelled、returncode -9、stdout 空。源码命令摘要记录 red 为 1 failed／5.21 秒，green 为 1 passed／0.50 秒。新增测试的 controller 字符串经只读解析所得正文与这些原件一致，真实 UTF-8／CRLF 已覆盖。

## Standards

**判词：已检查的四文件片内无实证规范违例或基线 smell。** Standards 轴检查了 AGENTS、PLAN 稳定规则、maintainable-project-delivery 的职责／复用／生命周期要求及 codebase-design 原则；无根目录 CONTRIBUTING／CODING_STANDARDS，包内参考模板不作为本模块规范。

实现留在拥有快照和子进程生命周期的原 `processes.run` Module，复用已有记录文件和标准库 `Popen`，没有新增生产函数、包装层或 Interface。输入 FD 生命周期集中于原实现，调用者无需维护写线程或新增轮询协议；这是当前接缝内较小且可审查的修正。`agents`／`stage_driver`、`reference_job_lifecycle`、`reference_task_creation` 的取消、预算、锁和清理职责仍在原 owner。

新增回归通过真实 reader 延迟 350ms 后读取并计算摘要，能够暴露原监督写管道停滞；它与普通 UTF-8／混合换行测试、后代停止测试覆盖不同触发条件。独立 controller 将 Linux subreaper 影响留在其自身进程，未引入重复 helper 或新测试框架。记录的 green 用时与这一场景相称；没有据此推断完整 suite 或模型性能。

## 证据与未验出口

已只读核对本片清单、完整四文件快照／差异、`probe-r1.py`、`probe-r1/result.json` 及 stdin/stdout 原件、`source-red-green.json`、`test-red-r1/`、`test-green-r1/`。邻接读取包括原 `agents`、`stage_driver`、`reference_job_lifecycle`、`reference_task_creation`、`evaluation`、`optimization`、`tools`、`kernel` 调用，以及既有输入／后代清理测试。当前 Python 的 `_communicate` 实现也确认：重入时 `input=None` 不再注册 stdin 写事件，与最小复现机制一致。

初审时 `source-r1/stdout.txt` 仍为部分输出，没有终态 `result.json`，故受影响 suite 尚不能记为完成。以下出口继续开放：

- S1 受影响的 processes／budget_jobs／composition_executor 检查终态及实际结果。
- S2 同候选非 editable 包／两 RECORD／冻结基线身份、安装后原 probe 变绿、自身审查模板及其输入／回执、以独立新 task 和原预算机制重验 A2。
- S3 完整候选最终身份、普通提交／远端精确 Ref 和本候选自己的必要 CI；本审查没有执行 Windows 或完整 suite。

原两轮 A2 的无 stdout 与本问题条件相符，不能据此证明其全部底层原因。第二轮 attempted cancel 遇到连接拒绝，TERMINATED／NEEDS_RECONCILIATION 不等于取消已确认，原 owner 清理尚需原件补核。Linux CI 的二十分钟超时也未定位到具体测试。本片未宣称模型双后端成功、OS 隔离、A2 成功或全 CI 根因已确定。

初审计数：Spec 0，Standards 0；两轴均无最高严重度 finding，以上验收出口开放。后续安装／模型／最终身份原件到齐后在本记录补核，不以本次静态判词替代。

## 同片补核：r2 文档、安装与自身模板

本次沿原两个独立轴的源码判词，只读检查新增原件和更新文档；没有新派审查者，也没有运行安装、测试、模型或服务。HEAD 仍为原基线。`.ergora/checks/supervised-stdin/review-r2/manifest.json` 的 SHA256 为 `5e5d6e38956f18e4fa7034a5345defecd8730cac778c6fb44d8b658216df2589`，四份快照逐项匹配该清单。产品及测试两文件与 r1 逐字相等；文档身份为：

|r2 文档|SHA256|
|---|---|
|`docs/delivery/2026-11-13-supervised-stdin.md`|`89f25a0d901486120a11819f2e22cd2c08a2a263746c5ef38c1118ef90744a1a`|
|`docs/PLAN.md`|`6355bb09141c35580b7da4e9b793bb80b0c348dea2acf0530dcfe23c487926ed`|

读取时四文件均与工作树匹配。PLAN 仅按此快照的本片状态句核验；后续邻片状态变化不改变本片源码身份，也不借本判词审过 B2a 或 workflow-poll-history 产品。

**Spec 补核：0 finding。** 新增原件支持安装、受影响检查和聚焦自身模板的记录；新 A2 与交付出口仍开放。**Standards 补核：0 finding。** 新增文件身份未扩大原实现，补充验证与原职责、原候选相符；没有由通过的局部检查推断整片运行成功。

### 安装身份与受影响检查

直接读取 `install-r1/source-manifest.json`、隔离源码、wheel 和非 editable 安装树后，独立核得：

- wheel SHA256 为 `e2c0ce33bd576825d19f3526f895225ef9edab56b5d63d94bf49569f8d75d8bb`；源码、wheel、安装包各 497 个产品文件逐字相等。对原基线的产品差异只有 `processes.py`，测试 overlay 亦匹配原 r1 摘要；没有混入暂存 B2a 数据。
- wheel RECORD 的 505 行和安装 RECORD 的 510 行，所有声明了摘要／长度的条目均逐项通过；安装来源元数据指向该 wheel，非 editable。三处的 283 个冻结参考文件均匹配参考清单，安装冻结文件没有符号链接。
- `core-r1/result.json` 与原 pytest stdout 同时支持 18 passed／4 skipped，pytest 用时 114.69 秒，外层 controller 为 116.878 秒；`executor-r1` 为 22 passed，pytest 204.58 秒，controller 205.588 秒。两组均 returncode 0，stderr 空，命令使用该安装解释器的 `-I -m pytest`。对应的原预算／组合测试和 pyproject 与基线相同。
- 原 `source-r1/timeout.json` 与部分输出仍保留 300 秒外部上限。该源码组合检查没有完整 suite pass；安装后分组终态不改写这次超时。四个 skipped 仍只是 Windows 专属条件未满足，不代表 Windows 验收。

`probe-fixed-r1` 的脚本与原失败脚本只改变输出目录；其原 stdin 为同一 425,984B 正文，真实子进程 stdout 匹配摘要，记录 succeeded／0.408754 秒。不过这一轮没有保留完整启动命令或解释器身份，不能事后补造该身份。

作者另用已核安装解释器的 `-I` 运行 `probe-fixed-r2.py`，没有覆盖 fixed-r1。新脚本、外层 stdout/stderr、`result.json` 和真实子进程 stdin/stdout/stderr 已读回；记录的解释器与 `ergora.__file__` 均指向上述安装，`processes.py` SHA256 为原 `b5cacaa4…09d0c8`。正文与失败 probe 逐字相等，子进程摘要为 `287dd78145d9feadcc9d095e8056e05bcff9629c43d9bf8b8620e4d3e39d8f6d`，状态 succeeded、returncode 0、0.409691 秒，内外 stderr 均为空。此轮补足明确身份的安装慢 reader 验收，不追认 fixed-r1 缺失的启动记录。

### 自身模板的实际输入与原结果

已读回 `self-review-r1.py`、`self-review-r1-codex.json`、模板冻结输入、admission、native 运行输出、protocol 及原结果；没有输出或写入配置密钥。实际来源是已核安装包的原 `ergora-structure-review` 工作流和 `ergora-structure-reviewer` 叶，两个定义与包内定义语义相等。请求为 text-only 的单叶独立会话，`formal_execution_authorized=false`，不将其称为一次完整六阶段执行。

三份继承／叶资源为祖先 instructions 163B、叶 instructions 354B、叶 Skill 521B；资产文件、声明摘要和安装原件一致，各全文在 prompt 中出现一次。两份候选源码合计 15,247B，与 r1／r2 原件摘要一致，各以完整文件框架内联一次；本轮没有新增待读取附件。

准备输入、运行输入副本、protocol prompt 和实际 stdin 均为相同的 20,073B，SHA256 `2dbeff1cceac3a29c0bd4a3f48e5ae730b5d5bd74033196199acef889ca7b1aa`，task 亦完整包含。admission 与运行的 input digest 一致，输入副本的 request／composition／task 与准备原件逐字相等。

原 run `c03d99c74d7644fb8e98f2a61ab7c186` 为 succeeded，CLI exit 0，记录耗时 37.562718 秒。run 的 `result.json` 与 `original-result.json` 逐字相等，protocol 结果语义一致，导出的 review.md 亦与响应相等；原结果 SHA256 `4ab3971ba10acbff3b38de851d63e10d0236ef169b4da472378406835b832a18`，判词 approve。结果明确只覆盖两份文件及所给证据，不把模型自身未验的组合检查、A2、历史修正或 Windows 记为通过。

请求后端为 Claude，实际绑定为用户已授权的 Codex 回退，理由记录存在；没有宣称异构后端成功。实际命令保留 read-only、关闭 shell 等配置，但不将其称为 OS 隔离。此处核实的是资料完整交付与原判词身份，不声称能由传输证据观察模型的内部阅读过程。

### 当前出口

同片补核后的 Spec／Standards 仍为 **0／0 finding**，两轴均无最高严重度 finding。S1 的安装后受影响分组检查、S2 的非 editable 身份／显式身份慢 reader／聚焦自身模板原件已有支持；原源码组合超时与 fixed-r1 启动记录缺失保持各自范围。

S2 的新 A2 独立 task／预算仍待邻片历史增长修正；S3 的普通提交、远端精确身份及本候选必要 CI 继续开放。Windows、完整 suite、原两轮 A2 的全部根因及取消／owner 清理没有由本次补核关闭，不能用本片 probe 或自身模板 approve 替代这些出口。
