# 原六阶段轮询历史大小修正独立审查

**H 的实现、同候选安装及自身模板原件补核通过；Spec／Standards 开放 findings 分别为 0／0。H4 的完整旅程与交付仍未完成。**

日期：2026-11-13。主审 `/root/workflow_poll_history_review` 为 fresh context；另以 `fork_turns:none` 启动互不继承上下文的 `spec_axis` 与 `standards_axis`。依据项目 `AGENTS.md`、[PLAN](../PLAN.md)、[原始验收与交付记录](2026-11-13-workflow-poll-history.md)、AIHERO 索引、`maintainable-project-delivery` 的 independent-review brief、`code-review` 和 `codebase-design`。两个独立轴与项目自身结构模板分别记账；独立上下文不代表不同模型后端。

## 审查身份与范围

固定基线和检查时 HEAD 均为 `e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`；`git diff <baseline>...HEAD`、`git log <baseline>..HEAD` 为空。实际对象是未提交的四文件快照，已读取 tracked 差异和新交付文档全文，未将空提交差异误作无改动。

最终快照为 `.ergora/checks/workflow-poll-history/review-r3/`，manifest SHA256 `6d9efc035f4d1be7f93c2b7a6d8a47de9d24be5cd919512f234f2654e26accd8`。四文件的快照、manifest 和检查时工作区字节相符：

|文件|字节|SHA256|
|---|---:|---|
|`src/ergora/reference_workflows.py`|26,919|`7e3a42f01b079da186230cb0e76b730ce0702e11ff57aec758ba5f258b7ce661`|
|`tests/test_budget_workflow.py`|14,283|`6994dbb9f6d10efe36cfe9fe8db462bc569853119b3bc17dcbcbf9dc14f65b45`|
|`docs/delivery/2026-11-13-workflow-poll-history.md`|5,482|`3bfc2c50f9bf17603bfe2a129f962b422e539d4eb2b3972580d4d5bf2fcc305e`|
|`docs/PLAN.md`|36,651|`71dae4898a38e7ac064c8361569d7afd2cf6382eacc6895480ab8273602f5f90`|

初审 `review-r1` manifest SHA 为 `fd18b77fc76af16b295181fa1127c9651580c08802bdd748d20eada358305ca7`，安装／模型终态补件 `review-r2` 为 `ca68a3f79297280be88c4c6d07a76eba86820872bb073eb26176689c352498e2`。三版产品／测试相同；r2→r3 只有交付记录第29行改为 H2 后第三轮 A2 与 H3 并行、最终结案仍依赖 H3，未把启动写成验收通过。

`processes.py`／`test_processes.py` 是独立 stdin 前置片，本次仅核它们属于包的明确 overlay，没有重审其实现。B2a preset／`test_presets.py`、A2 旅程及其清理文档为邻片；本报告不授予邻片代码或运行验收。

## Spec

**判词：本片实现范围内通过，开放 findings 0；完整任务验收未关闭。**

Spec 子审未发现需求缺失、越界改动或错误实现。对照交付规格第19、21行，`reference_workflows.py:502` 仅在 `BudgetedWorkflow.call` 为 v9／v10 的 poll 生成三字段原身份引用，使用 SDK patch `ergora-budgeted-poll-reference-v1` 保留旧 history 路径；`reference_workflows.py:321` 从对应版本的 trusted requests namespace 读取、校核完整 envelope，随后进入原 receipt／review 验证。完整 submit、旧完整 job 输入以及原 task／run／job、预算、审批、候选和 fence owner 均保留，没有提高服务上限或引入材料服务、缓存、账本、调度器。

已读取真实父 `Activities`／`FileAdapter`／`DevelopmentWorkflow`、`reference_inputs`、`reference_review_opinions`、`reference_task_evidence` 和 `reference_task_reconciliation`。v9／v10 的 adapter construction 仍分别使用原 request namespace；还原 job 后，非 review 走原 receipt 校验，review 走原 `review_observation`，没有跳过候选、actor、会话或可信意见绑定。离线 evidence 与原 ID 对账依据完整 submit 事件还原 job，不依赖 poll 参数包含 context。

源码／安装检查和两原 history 重放支持本片结论。交付规格第29、31行保留的第三轮 A2 完整旅程、Windows、远端与本候选 CI 是未完成验收出口，不列作 H 实现 finding，也不能借早前结果关闭。原第二轮 TERMINATED 及原 ID 收尾由 A2 片独立验收。

## Standards

**判词：所审范围内通过，开放 findings 0；未发现已记录规范违例或值得报告的 possible smell。**

Standards 子审核对 `AGENTS.md`、PLAN 稳定规则、reference 边界、合同／身份文档、当前架构、ADR 0001／0002 及测试成本计划。两处改动留在原 workflow／activity Module，复用既有有界 no-follow reader、路径及标识校验，符合原 owner 与小 Interface 的要求。没有新增生产文件、共享抽象、配置接口或假想 Seam；三字段 JSON 引用沿用现有合同，无需为单一私有算法增加类型层。

新增分支各有可达责任：旧完整输入保持原行为；紧凑输入须恢复原材料；标识与 envelope 摘要不符时拒绝替换、损坏或错配原件。还原成功只委派原父类，不复制 receipt／review 校验。未发现需删除的重复 guard、fallback 或不相关参数验证。

新增测试检查真实 history 输入、完整 admission、缺失回执、完整 job／引用同一回执和原件替换拒绝，具有合同价值；没有新增 CI 重复执行。原七个 Temporal 场景经同一修改路径复验，分别保护排队、预算、重试、取消、review 等待及 fence，不因形状相近判为冗余。r3 只更新状态文字；这些判词不授予整片完成。

## 主审原件补核

以下是只读核对已有原件及独立字节／摘要复算，没有重新运行测试、replay、模型、安装或服务。

|证据|核对结果与实际范围|
|---|---|
|原诊断|直接解码原 history 的 JSON payload 并复算：r2 为1,638事件／70,666,291B，原 SHA `2d6798714a8208aa7fe189115218f3b8d0a88e5cf7f7e0d04f30d77d03386866`；9 submit 输入2,029,106B，210 poll 输入47,991,832B、最大229,547B；末事件确为 history-service 的 `Workflow history size exceeds limit.` 终止。34,650B 仅是同210个引用的输入投影，非整体 history 大小。|
|反馈循环|`red-r1.stdout` 首先因写死至少2次 poll 而失败，不算产品 red；`red-r2.stdout` 在真实 Temporal 暴露额外 `context`，1 failed／14.95秒；`green-r1.stdout` 同一回归1 passed／14.97秒。|
|源码检查|`scenarios-r1.stdout` 为9 passed／99.06秒；8个真实 Temporal 场景及1个原活动材料／receipt 检查。原 `poll-history` history 有 patch marker、1次 poll 输入147B，完整 submit 输入仍保存；此检查没有声称覆盖原210次等待。|
|旧历史重放|源码 `original-replay-r1.json` 和安装 `installed-original-replay-r1.json`、脚本／stdout 对应同两原始字节。r1 为1,253事件，SHA `a3939ca1b22a28de85da9e233de3e4f92d264d6f594dadb57e52693a6a44f6ab`；r2 身份如上。两份均为 v10，原r1业务结果 BLOCKED、原r2 TERMINATED 保持；记录分别通过源码及安装 replay。安装记录自记的包位置与 workflow SHA 对应本候选。|
|隔离包|独立比对基线 Git archive、`install-r1/source-manifest.json`、实际 wheel、隔离源码及安装目录：497产品文件全部相符，仅叠加 H 与 stdin 前置片四个源码／测试 overlay，排除暂存 B2a。实际 wheel SHA `85e20a342361f8fda1233f607dc94679364a0691b0b5452bb6b274648d117ab7`；wheel RECORD 505行、安装 RECORD 510行的全部有摘要条目逐项核对；283冻结参考逐项相符，issue 0。|
|安装检查|`install-r1/scenarios-r1/result.json` 为 `succeeded`／returncode 0，命令以该 wheel venv 的 Python3.12、`-I -m pytest` 运行隔离源码的 `tests/test_budget_workflow.py`；stdout 九案例逐一 PASSED，9 passed／103.69秒。105.443秒是外控制耗时。安装 `poll-history` 原 history 也只有三字段147B和同一 patch marker。源码检查为Python3.11，未混同环境。|
|自身原模板|`self-review-r1-codex.json`、原 admission／native run／stdout、原结果及两份输入树相符：实际 run `5fafb3364c224496ac7655cec965ddad`，退出0／succeeded，42.719秒 approve。输入为原 `ergora-structure-review@1.0.0` 的 `root/review`；workflow／agent／instructions／Skill 五个资产逐字等于该安装包，祖先和叶文本均在 prompt 中。|

自身模板两源码全文共41,202B，与本次源码 SHA 相同并完整出现在46,872B prompt／实际 stdin；prepared input、run input 的完整树摘要均为 `b83e313b8308edade3a35da6431fe66706bcc6cd2d8d2dc376ffedecdd4564a7`，协议重组的 prompt 亦逐字相同。两输入 prompt 与第三份实际 stdin SHA 均为 `6bc72f9b8cfed70027496934db980f5e3fcd814a372ed7589265a23b0773a02c`。原 native stdout 第4条结构化结果等于保存的原结果，SHA `85c7a5be3d0252c884160063856503025eaf621ffa982e136857f6f3fc57864a`。这证明本次完整材料交付及原判词身份，不把它扩大为全仓库、运行行为或不同后端独立性证明。

性能结论限于已定位的重复大输入：引用让每次新 poll 的历史参数独立于完整材料大小；代价是在原活动内读取并校核原 request。未新增跨 poll 缓存、外部往返或调度层。短场景不是同210次 poll、同等时长或任意事件数的容量测试；服务的事件数／总历史限制仍存在，没有提高它们。`git diff --check` 在 H 源码／测试与 PLAN 范围内通过。

## 阻断项与未验出口

实现 bug 0；规范违例／possible smell 0；没有需修复后复审的 H 代码阻断项。H0–H3 的本地实现、安装和本报告所列原件验收可以记为通过。

H4 保持开放：第三轮 A2 使用同已核 H 安装、独立 task／原预算，须完成真实六阶段成功路线及其原 ID 恢复、receipt／fence／claim 和实际进程清理的独立验收。第三轮在途进度不在本报告授予通过；原前两轮失败不被改写。原第二轮的收尾由其原独立评审负责，本报告只核其与 H 的调用兼容及历史身份，没有接管其终核。

普通提交、远端精确 Ref 与本候选自己的必要 CI／Windows 结果尚未验收；跨机器材料存储和任意长任务不在本片保证内。未将旧片包、旧 CI、源码 replay 或模型 approve 借作这些出口通过。

本轮仅写本报告；没有改源码、测试、冻结参考、PLAN 或邻片记录，没有启动服务／模型／测试、安装、提交或远端写入，没有读取或披露 inference 配置内容。后续同片补件只核新增证据和相应身份；实质产品变化需另按规则复核。

两轴各0项；Spec 无最严重项，Standards 无最严重项。
