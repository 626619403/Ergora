# B2e Profiling／内存快照独立评审

日期：2026-11-13。协调者 `/root/profiling_directions_review`；Spec 与 Standards 分别由 `/root/profiling_directions_review/spec`、`/root/profiling_directions_review/standards` 在 fresh context 独立审查。先读原用户要求、[B2e 计划](../plans/2026-11-13-optimization-profiling-directions.md)、[B2 总计划](../plans/2026-11-13-specialist-presets.md)与 [R7](../research/2026-11-12-optimization-profiling-agents.md)，再读实现及原件；未以作者自评或另一轴判词替代独立结论。应用 AGENTS、code-review、maintainable-project-delivery 与 codebase-design。

固定基线／HEAD 为 `e85b1e6eb38ac568142b2a73b9ca3bae1d248f8a`，没有后续提交。工作树比较为 `git diff e85b1e6eb38ac568142b2a73b9ca3bae1d248f8a --`，另核全部新文件。最终实施候选 r4 manifest SHA256 为 `2c44a0e3c579d2ce700c5de1a8ca0f4267c74f2150ef74524a53409aa4bd99c9`，15 份冻结文件的长度、SHA 与 live 字节全部相符。r2／r3 原快照保留；r4 仅修改 r3 的四份状态 Markdown，八份产品／测试与公开投影保持。

完整范围为两个方向各 `workflow.json`、`instructions.md`、`context/<方向>.md` 共六文件，`presets.json`、`tests/test_presets.py`，以及 PLAN、两手册、B2e 计划、B2 总计划、交付记录和公开 evidence JSON 共七文档。本评审记录属于同片状态记账。

## Spec

**通过，开放 finding 0；SP1/P3 已修复并复核关闭。** 未发现产品需求缺失、越界实现或新增执行所有者。两个方向均有独立完整资料根与 catalog 入口，精确复用共享 v2 专家、原定义库／编译器、manifest 与单叶后端准入。结构祖先和自身 Skill 树在实际输入与 MCP 读取中完整可核，父权限上限保持。

原 **SP1/P3** 位于[交付记录 r3 第 28 行](2026-11-13-optimization-profiling-directions.md)，称两个 measurement 任务包含前驱全文“与其 SHA”。两任务确实逐字包含四份原前驱结果，但结果 SHA 不在任务正文，实际由原 audit／公开投影保存。该说法会让复现者高估模型收到的身份信息，违反原需求“准确区分真实／未验”和独立审查的证据身份要求。最小修正为分别说明全文传入与 SHA 保存位置。r4 已准确改写并保留 finding 历史；直接比对 task、stdin、四份 original result 与 audit／投影后关闭。产品、模型输入和结果保持，没有重跑成功调用。

原结果范围保持准确：profiling 的 `approve` 仅针对补证据提案就绪；memory-snapshot 为 `request-changes`，要求冻结真实实验前补齐候选、兼容报告和独立证据。两者都没有批准解析、硬件执行、实测收益或采用。

## Standards

**通过，开放 finding 0。** 本轴也直接确认同一 SP1/P3，并按 AGENTS 的“Record actual checks”口径复核修正成立；没有其他可定位的规范、职责、耦合或冗余问题。

两方向复用现有定义、继承、manifest 和调用所有者，没有新增 Python 执行、解析、采集、调度、停止、预算或批准实现。重复 JSON 骨架承担独立不可变配置合同，无需为此增加抽象。两个新增测试参数沿公开安装→manifest→input 接口保护完整 context、精确 v2 专家、只读权限及删除源定义库后的材料保持；三叶预期检查发行配方，没有锁死用户的合法修订。没有新增运行 guard、fallback 或 CI 分组。

|新增文件|职责与实际消费者|
|---|---|
|profiling `workflow.json`|版本化方向图；由 `workflow_definitions.presets/install_preset/_Compilation` 处理，CLI／HTTP 调用原入口|
|profiling `instructions.md`|读取、手动交接与只读声明；经 `_materials/_prompt`、`compile_input` 交给 `agent_runs.run_input`|
|profiling `context/profiling.md`|方向诊断与证据资料；经同一路径供三个实际叶消费|
|memory-snapshot `workflow.json`|独立方向图；使用相同定义所有者，引用共享 v2 子图|
|memory-snapshot `instructions.md`|该根的完整读取及交接声明；使用原资源装配路径|
|memory-snapshot `context/memory-snapshot.md`|受信摘要、allocator／history／step 资料；各叶消费，未承担反序列化或采集|
|B2e 计划|项目范围、归属及验收出口；由项目恢复和实施流程读取|
|B2e 交付记录|实际检查、限制与开放出口；由计划／PLAN 引用，不承担运行账本|
|公开 evidence JSON|原件身份及受限结果的静态投影；由交付记录和审查读取|

标准来源还包括 README、架构 current／reference-boundary／contracts-and-identities、相关 ADR、TESTING、WORKFLOW_DEFINITIONS、AGENT_DEFINITIONS 与 pyproject。检查了命名、重复、职责归属、依赖方向、浅层转发及假设性扩展等 smell；未将 heuristic 当作自动违规。

## 直接核验的证据

协调者与两轴分别读原件，未安装、运行新 suite／模型、调用外部工具、控制进程或发布。只读 inspector 用于重验既有 manifest／input，不产生新执行验收。

|核查|实际结果与范围|
|---|---|
|固定资料|Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0` 的十一份原件，共 365,250B；长度、SHA 及 HTTP200 记录核准，关键 capture／parser／SQL 事实直接对照原实现|
|独立安装身份|536 产品 source／wheel／installed 字节相同；wheel 544 文件、两 RECORD 逐行 hash／长度核准，installed RECORD 549 行；283 冻结文件逐项一致。基线 530 产品只有 catalog 改动，16 个旧条目保持|
|原安装检查|原 preset suite 日志为 25 passed／100.09 秒，外围 101.887 秒；两个新增参数均通过，未重跑|
|正式 collection|七份 request／result／原 phase 均为 collect-only；1713 全集等于六组 254／250／342／312／256／299 的并集，交集 0；不是本地全 suite 回归通过|
|六真实单叶|原 manifest／input、SQLite run、prompt／stdin／protocol、scope、MCP server receipt／原生 stream、最终 native 文本与原 result 逐一对应；每次一 list、六 read，36 资源共 75,319B 从 offset 0 连续 UTF-8 读至末页 null；无重试或失败 MCP|
|手动前驱|两个 measurement 的任务与实际 stdin 分别包含两份完整原前驱；四个结果 SHA 由 audit／投影保存，逐一重算匹配|
|自身原结构模板|原调用 26.700 秒／approve；八完整文件 51,307B 逐字在 task 内，三份祖先／自身资源完整内联，prompt／stdin／protocol 均为 57,260B，最终 native 文本与 result 一致。该判词仅覆盖八份结构资料，不替代独立审查|
|公开投影与进程观察|[公开投影](evidence/2026-11-13-optimization-profiling-directions.json)绑定的两 audit、来源、fixture、包、collection、自身原件及观察回执 SHA 均核准。进程回执仅支持结束时一次 `/proc` 限定根／可执行名观察无匹配|

wheel SHA256 为 `e171c36d00d84028fdefb40164e157d1af2661220f44dd0e722ce53416b03860`；公开投影 SHA256 为 `de60ee4a402a76c552cd1aedf414fd8982efa426bb07d5b2a4b2d9e87cad54e6`。Profiling 三叶读取 18 资源 37,982B；snapshot 三叶读取 18 资源 37,337B。两 measurement 的请求／实际 binding 及显式 Codex 回退理由保持，不称异构后端通过。

## 限制与出口

fixture 是明确 synthetic 文本：toy union／补集不能证明真实 GPU idle、依赖阻塞或可恢复关键路径；snapshot 的 inactive 6／8MiB 排除 awaiting-free，缺 unmatched-free bytes／分母时不能估计丢失比例。没有原 trace／pickle 解析、GPU 执行、全 rank 正确性／梯度／质量／恢复、性能收益、模型理解或异构后端验收。一次进程结束观察不能证明全程或脱离后代跟踪。

本片资料与本地证据的独立审查通过。普通提交／推送、精确候选自己的完整 CI 及其独立终核仍开放；原实验 runner／Forge 内部循环保留各自后续验收，不借本片关闭。

Spec：SP1/P3 关闭，开放 0；Standards：独立确认的同处 P3 关闭，开放 0；两轴均无其他 finding。

## 最终状态补核

协调者已直接核 r5 完整 16 文件快照，manifest SHA256 为 `fe6be217c154ef6bb05ff79e8dbb8b74bf8d5126a0986e2fa4903adb893833bf`。全部冻结长度／SHA 与 live 相符，无清单外改动；八份产品／测试和公开投影与 r4 保持，差异只有四份状态 Markdown 及本报告。四处状态均准确记录两轴本地通过、SP1/P3 关闭／开放 0／0，并保持普通发布及自己的精确候选 CI 开放。173 个本地 Markdown 目标存在，报告相对链接已指向实际文件。此次补核只检查同片记录，没有新增测试、模型调用或行为变更；后续绑定本报告补核文字的冻结不构成新实施片。

## 普通发布身份补核

随后普通提交为 `99b953fcff931cda60e4ff41ff66a8870b7f7866`，父提交仍为 `e85b1e6eb38ac568142b2a73b9ca3bae1d248f8a`。协调者直接读取 Git 对象，核准完整 16 文件与 r6 manifest／冻结字节、ready 的逐文件身份及 staged object 一致；r6 manifest SHA256 为 `09042c446a2d624a16be91a12f22ccc6a63b4f581910d711fd19420d8028183a`。r5→r6 只有本报告的最终状态补核尾注；536 产品在该 Git 提交、实施归档、wheel、installed 及 live 中逐项相同。提交后的四份状态 Markdown 只记录普通发布与 CI 在途，产品没有变化。前文 HEAD 和发布开放的描述保留实施审查时的范围。

**PB1/P3，已修复复核关闭。** 发布辅助 producer 的 `review_report_sha256` 字段误读上一片 communication 评审，值为 `9954a00…`；原 ready 的本片文件条目和 staged object 原已正确。错误字段可能使读取辅助回执的人误认本片评审身份。最小修正为保留原 ready／producer，追加说明和精确更正身份，无需重做提交、推送、模型或测试。新增更正回执的 SHA256 为 `d4535815f6d98fc7108fde01061bb5b4572816fa48132b86dcd9aa9af6fc8f29`，直接核准已提交本报告为 8,923B、SHA256 `189e8e5dfb56b6bdc8aa0cf23bb4fa77c44ad2ba58c90393eb90c4092512c8fb`、Git blob `34ba5d4e0156ccbc381b11f889e89bb4cacffe57`；旧字段确实绑定上一片报告。原错误回执保持，没有被当作完全无误的回执覆盖。

原 commit／普通 push／作者 SSH `ls-remote` 回执均 exit 0，推送没有 force 参数，作者分支 Ref 为完整 `99b953fcff931cda60e4ff41ff66a8870b7f7866`。本次是对作者回执和本地 Git 对象的独立只读补核，评审者没有调用网络，不称独立直接远端读取。

自己的 [CI43420340258](https://github.com/626619403/Ergora/actions/runs/43420340258) 初始三份官方 UI 原件均为 HTTP200，长度与 SHA 核准；Actions 列表和 run HTML 的完整 commit 链接均绑定本候选。原 job-groups JSON 列出八个 job：plan 已 completed／success，六 Linux 分组和 Windows job 当时仍 in_progress。这里只确认精确候选的初始在途身份，自己的完整 CI 与必要步骤终态验收仍开放；未新增模型、测试或网络操作。

## 精确候选自己的 CI 终核

协调者随后直接离线解析九份官方原 HTML 与 receipts：第三份 run HTML、第三份 Windows job HTML，以及 plan／六 Linux job 各第一份 HTML。九份均为 HTTP200，实际长度与 SHA 逐一相符。原 run 的 Status 为 **Success**，完整 commit 链接绑定 `99b953fcff931cda60e4ff41ff66a8870b7f7866`；原 UI metadata／job-groups 核定同一 run 的八个新 job 身份，终态逐步取自各 job HTML，未把早期 batch 的在途字段改写为终态。

|job|原 job ID|必要步骤全部成功完成|回归秒数|
|---|---|---|---|
|plan|131868450824|1|—|
|Linux group 0|131868514009|4|209|
|Linux group 1|131868513972|4|282|
|Linux group 2|131868513788|4|202|
|Linux group 3|131868513853|4|152|
|Linux group 4|131868513819|4|202|
|Linux group 5|131868513889|4|228|
|Windows group all|131868514016|5|671|

全部 30 个必要步骤均为 success，具有非空 `data-completed-at` 和 `data-job-completed` 标记；非空 log URL 的完整候选 SHA、job ID 与 step number 逐一对应。必要步骤包括 plan 读取显式分组、七个 native job 各自的 wheel 安装／reference 身份／回归／观察上传，以及 Windows PS5.1 安装升级。另核全部 76 条成功步骤元数据，日志链接也均绑定相同精确提交；Linux 条件不满足而 skipped 的 PS5.1 步骤不计入必要步骤。

Windows 原 UTC 时间为：回归 `11:52:03→12:03:14`，671 秒；PS5.1 安装升级 `12:03:14→12:03:56`，42 秒；上传 `12:03:56→12:03:57`，1 秒。第三份 run HTML 的 SHA256 为 `6734f81b84fb867d810f0dd9a4f21b6911b4cec5b4ed12db3d6b46da1040c1dd`，第三份 Windows HTML 为 `9c45b9cd63ab84c8314377cf8b5ba7eb4b0a6abf67a8ee40858c85ad6f9cf70b`。前两份 Windows 在途原件及其 27／30、28／30 结果保持，未覆盖或提升早期样本。

本次关闭该精确候选自己的 CI 终态出口，八 job／30 必要步骤独立终核通过；SP1/P3、PB1/P3 的原 finding 与修正历史保持。核验仅针对作者保存的官方 UI 原件及步骤元数据，没有评审者直接网络请求、全日志下载、模型、测试或安装操作；没有据此扩大到 parser／GPU、训练质量或实测收益验收。同片五份 Markdown 的结案普通提交／推送由主线另记。
