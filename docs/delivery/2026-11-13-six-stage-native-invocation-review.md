# C 单实例六阶段调用独立评审

日期：2026-11-13。评审者为 fresh-context 协调评审 `/root/native_six_stage_review`，并依 `code-review` 以另外两个 fresh-context reviewer 分别完成 Spec、Standards；未继承实现对话。先读原需求、[AGENTS](../../AGENTS.md)、[原消费者计划](../plans/2026-11-12-six-stage-native-consumer.md)、[预算合同](../plans/2026-11-12-six-stage-budget.md)与 maintainable-project-delivery／independent-review brief，再读冻结差异、实际源码和相邻调用者。B2 的历史通过不作为 C 的通过依据，未递归评审其报告。

当前完整 r3 最终复核结果：**Standards approve，开放 0；Spec approve，开放 0，C 实现及本地验证出口通过**。SP1 文档 P3 已修正并由原 Spec reviewer 复核关闭；自身 r1 超时／partial 保持，另一次 r2 使用原安装包模板完成四件完整聚焦材料的实际审查并 approve。两轮范围及原件分别核验，未将聚焦模型审查等同完整候选独立评审。普通发布、精确远端 Ref、本候选自己的必要双 OS CI，以及 D 的完整 v10 Temporal／模型旅程仍未完成。

## 精确对象与范围

固定基线及当前 HEAD 均为 `a00896146c6499f58ae86a5b6b76fa13c3c7c796`，无基线之后的提交。对象为基线上的完整未提交候选，采用冻结 `tracked.patch` 加 `manifest.json` 所列 `files/`，避免空的三点 HEAD 比较遗漏 WIP 与新文件。

首轮 r1 为 20 件／483532B，manifest SHA256 `48b3a8d13865514082f2c28c3f5d2801061d75c8eab16c97279f3c5b97b71885`。同片扩大至 r2 为 **24 件／594275B**，manifest SHA256 `c9a00eb980a3725e1dfa2fc2d06eae0613d74d9e1eb9fdc60787c715d64789b6`；协调者与两轴分别核文件大小及 SHA256，全部匹配。产品、测试和示例从 r1 至 r2 逐字不变，新增四件既有文档与其余文档补记均已审查。

最终 author r3 为 **26 件／601399B**，manifest SHA256 `ee83c7e98a18a062c906b2b6cb6e9218bd561386ca19db7c0ebaa0ab4a8d786f`；协调者和原两轴已分别核全部大小／摘要。产品、测试和示例与 r2 逐字相同；变化为四份状态记录及 C 交付补记，另增公开自身摘要和 D 初立旅程记录。D 记录在本轮只检查未验范围及两次准备拒绝的记账，不构成 D 运行验收。本报告自身不在 author r3，未递归评审报告。

完整 r3 路径为：

- `README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/WORKFLOW_DEFINITIONS.md`。
- `docs/architecture/current.md`、`docs/architecture/contracts-and-identities.md`。
- `docs/plans/2026-11-12-six-stage-native-consumer.md`、`docs/plans/2026-11-12-specialist-template-refresh.md`。
- `docs/delivery/2026-11-12-six-stage-budget-runtime.md`、`docs/delivery/2026-11-13-six-stage-budget-runtime-review.md`、`docs/delivery/2026-11-13-six-stage-native-invocation.md`。
- `examples/composition/README.md`、`examples/composition/native-development/workflow.json`、`examples/composition/native-development/instructions.md`。
- `src/ergora/data/schemas/task-definition-v6.json`、`src/ergora/native_six_stage.py`、`src/ergora/reference_inputs.py`、`src/ergora/reference_task_creation.py`、`src/ergora/reference_workflows.py`、`src/ergora/task_envelopes.py`、`src/ergora/tasks.py`。
- `tests/fixtures/task_submission_client.py`、`tests/test_architecture_boundaries.py`、`tests/test_native_six_stage.py`。
- `docs/delivery/evidence/2026-11-13-six-stage-native-self-review.json`、`docs/delivery/2026-11-13-six-stage-native-journey.md`。

冻结原件保存在本片持久私有检查目录的 `review-r1/`、`review-r2/`、`review-r3/`，实际测试和安装身份分别为 `install-r1/core-r1/` 与 `install-r1/package-identity.json`。机器路径与运行数据不复制进公开报告。

## Standards

**Approve，开放 0；未发现有证据支持的硬性标准违例或 heuristic smell。**

新纯数据模块 `native_six_stage.invocation` 有两个不同生产文件的实际调用者：[tasks.py](../../src/ergora/tasks.py#L172) 从实际冻结图准入，[task_envelopes.py](../../src/ergora/task_envelopes.py#L442) 在原输入读取／恢复时重核。它集中拥有支持形状与祖先投影，不拥有执行、批准或状态；没有以测试、重复调用或假设消费者证明复用。

[NativeSixStageInput](../../src/ergora/reference_inputs.py#L415) 沿既有版本工厂与共同 Interface 继承完整材料、预算和原 job 生命周期。独立 queue／request-root、adapter 的版本校验和 workflow 入口各有实际消费者；Executor 未新增按 native 具体类型分派的平行执行路径。现有严格版本解析分支扩入新版本，未改旧 v1–v9 schema 或其含义。

归属、整枝覆盖、单次 task 输入和结果转发等检查保护“静态图有效但有分支未被正式运行”的可达静默失败；原件读取与 creation 绑定校验分别保护冻结输入和已发布原件。完整材料、权限收窄与并发 scope 继续沿原编译器、WorkDelivery／StageDAG 与执行所有者消费。新模块只遍历已有有界图和祖先链，未见新增无界资源复制或额外模型调用。

新增测试覆盖原件恢复、错误祖先投影、未执行分支及 unknown 启动恢复；沿原架构 suite 增加基础层依赖约束，没有新增 CI job 或镜像式默认值测试。所有 native 用例通过现有 Linux workspace fixture 明确限制平台，未将 Linux 检查推断为 Windows 运行通过。

## Spec

产品代码未发现可确认的缺失、额外范围或错误实现。原计划第 7／21／34／45／50／56 行的边界沿实际调用链成立：definition6／input10复用 prepare、双摘要 create、提交与原 ID 恢复；完整 manifest、所选实例和全部祖先精确引用进入原 input 身份；父链只转发一次 task／结果，额外分支及外部依赖拒绝。work／review 继续由原 StageDAG／WorkDelivery 与 Temporal 处理，前两阶段继承既有完整材料消费者；后端选择与职责、权限声明及实际能力仍沿原合同。

### SP1 · P3 · 交付节点表未同步安装完成状态（已关闭）

位置：[本片交付记录](2026-11-13-six-stage-native-invocation.md#L17) 的 C1／C2 行。触发是按节点表恢复工作：其中仍写“新增公开示例及多层父链等待安装检查”“旧合同待受影响安装回归”，但同文新增安装段及 `core-r1` 原件已经记录当前候选 73 项通过。原计划第 58 行要求每节点更新交付记录。

后果是当前检查点互相矛盾，可能重复已完成验证。最小修正是把这两项安装状态更新为已通过，继续保留自身模板、D 和发布出口未完成。此项仅涉及文档状态，无需重跑产品、测试或模型。

实现者已按原 73 项证据同步 C1／C2，并在 PLAN、原消费者计划、专家模板上层计划及本片记录保留自身、D 与发布的未验范围。原 Spec reviewer 同片复核确认 SP1 关闭；Standards reviewer 补核这些状态变化未新增问题。产品、测试和示例未改变。

## 核验与限度

已直接重读安装原件：wheel SHA256 为 `1da3b270eb63c9c8d20eba96f659bf6a5049288b35c8100cfc143841327dd598`。协调者以只读脚本另核源码／wheel／安装的完整 **458 产品文件集合及正文相等**、wheel **463** 行与安装 **468** 行 RECORD 的 hash／size、**283** 冻结参考文件摘要，全部通过；未重新安装或执行产品测试。

`core-r1/result.json` 保存安装包 Python `-I -m pytest`、去除源码 PYTHONPATH、exit 0／外层 258.633 秒；stdout 为 **73 passed in 256.66s**，其中九个当前 native 用例均通过。范围为新公开父例／多层祖先、冻结与拒绝、受控 SDK 丢回执及 memo／完整 input 碰撞、旧 creation／预算准备／transport／架构和旧 v9 九 job／七 slot 完整材料受控串行旅程。旧 source-r3 的 22 项仅属于先前合成父包，不追溯为更新测试通过。

本轮另核 diff 空白，未运行模型、安装、提交、推送、网络或外部消息，只写本报告。运行故障与清理证据、测试结果和模型判词各保留自己的候选与范围；测试通过不替代两轴判断。

尚未直接执行 v10 的完整真实 Temporal／模型旅程，亦未把 SDK 恢复、旧 v9 受控旅程或静态继承关系称作新 v10 取消／对账／候选证据的运行验收。D、普通发布、精确远端 Ref、本候选自己的必要双 OS CI 继续按原计划完成。

## 自身模板原件补核

安装包的实际结构审查模板 `self-review-r1-codex` 已结束：run `fbfe0d4d184c44718b825d74f7d0ce45`，Codex／`gpt-6.1-sol`／medium，**602.0616 秒 timed_out，CLI exit 1，没有 result 或 decision**。该次尝试无可供采纳或驳回的模型 finding，也不能称 approve。所供七件聚焦材料总附件 72,767B，SHA256 `2b6749d88afae819282379ce30236cdd3bc33d56c69ce28235389b57b746acd5`；各 packet 原件大小／摘要与索引相等，范围为六件完整源码／测试／原计划／示例与完整产品 diff，独立两轴另覆盖完整候选。

协调者直接读取 scope、native transcript 和原 MCP audit，逐返回页比对 scope 原字节，并区分编码：五个固定 scope 中，工作流／Agent instructions 及两个 SKILL.md 共四小文件（163／354／480／521B）均以 UTF-8 完整读到 `next_offset:null`；候选附件只连续以 UTF-8 读取 **`[0,36000)`／72767B**。含 base64 页的全部返回范围并集只到 44000B，也未覆盖尾部。按 packet 边界，前三件源码／schema 已完整 UTF-8 交付，测试仅部分，原计划、示例及完整 diff 尚未完整 UTF-8 交付。握手／tools-list 成功、材料已供给或 base64 返回均不替代候选全文读取，不能记录七件聚焦材料全文通过。

原 0.2 秒进程采样记录四个所属 PID／starttime，结束时 live 为空；协调者复核时四个 PID 均已不存在。这个结论仅覆盖实际采到的拥有树，不能证明捕获全部短命进程或所有系统进程。未由评审者代清理，也未为获得模型 approve 重跑。

因此自身 r1 的证据是**一次真实调用、超时无判词、候选读取 partial、已采样资源无存活**。在该轮结束时，不能按“自身无判词但完整读取”的前提关闭本地出口；本轮失败与未读尾部不会被下面 r2 的不同聚焦范围追溯改写。

## r3 最终补核与自身 r2

原两轴分别补核完整 r3，均未新增 finding：C1／C2 状态已与安装原件一致，公开自身摘要准确保留两轮范围；D 初立记录明确准备失败、原预算不重领及真实旅程尚待验收。r3 没有新产品、测试、依赖或 CI 变化，不需要重跑已完成检查。

自身 r2 使用安装包的原 `ergora-structure-review@1.0.0` 与 `ergora-structure-reviewer@1.0.0`，改用其现有 text-only 模式。协调者通过安装包只读 inspector 重核准备与运行输入；workflow 两文件、Agent 三文件与安装 preset 逐字相等，精确引用 digest 分别为 `996c55d50e307943ae5dc77b2c929baea0d996a924fa66ab8c86a41e813c40c9`、`97587043a4e802819978e7263d000162aa7c33ddd998f6e2a069a32044ee4e5c`。工作流／Agent instructions 及单文件 Skill（163／354／521B）均完整内联，未改模板来取消审查要求。

四件聚焦材料是：五份追踪产品源码的完整差异（22752B）、完整 native 模块（3695B）、当前 native 测试（10375B）、公开父 workflow（1162B），合计 **37984B**。逐件核 packet-index 的大小／摘要与冻结原件相等；差异也与基线至当前五份源码的 `git diff` 逐字相同。这个包明确不覆盖独立 schema 全文、其他测试或全部文档；它们由完整候选独立两轴覆盖，不称模型也审了全部 26 件。

协调者从脚本中的原始任务正文和四件原字节独立重建 operator task，得到 40778B，与准备／实际 `task.txt` 相等；四件均完整出现在 prompt。准备 prompt、运行快照 prompt、原生协议 prompt 与实际 stdin **43177B 逐字相等**，SHA256 `c28ffd9ecb29d286191b577d188752ad6ecd167ee8abb9b6ca43f85033648545`。准备和实际完整输入均由 inspector 核为 digest `df8021d9d2394957f6888b12d8c0a72689077d69e2152bc983de93ff9c40c897`。这证明完整供给，未把供给字节称为模型理解。

权限链为 read 上限 `workspace/definitions`、write 空、shell false、network 空；实际 text-only 能力仅提供内联材料，workspace／固定资源读取和 MCP 均 unsupported。原生命令禁 shell／文件／web／MCP，仅保留原响应交互能力；这次没有附件或 MCP 全文读取的声明，也不声称 OS 隔离。

实际 run `649ac7beb0cc46e2830912cb775e3be2` 为 **175.9291 秒 succeeded／CLI exit 0／原生 returncode 0／approve**；有 started、finished 和 `turn.completed`。已核原结果与保存副本 1571B 逐字相等、SHA256 `776b43b0552a0180802b5b4c0ae617b0d57e19032ef982e579136bac9d60bb2c`；协议结果仅 JSON 格式不同，解析对象相等，review.md 与原 response 一致。模型分别给 Spec／Standards 通过并明确聚焦范围。原 turn 自报 input 58705、其中 cached 38400、output 737、reasoning output 322；不据此估算费用或精确 provider 调用数。

r2 的进程所有者已返回且保存原生 returncode 0、finished；原实现的 `communicate`／组收尾路径发生在返回前。本次没有 r1 那种额外 PID／starttime 采样，不借 r1 的四进程 live 0 宣称 r2 拥有树也完成同样的独立观测。D 的服务／模型树清理仍须 D 的实际证据。

协调者另对冻结 r3 的 **337 个相对 Markdown 文件目标**直接检查，缺失 0；diff 空白通过。这不覆盖 anchors、外部 URL、Mermaid 渲染或运行行为。公开自身 JSON 与原件共有字段、r1 prior-attempt 限度一致；公开材料没有推导 D 的运行成功。

最终两轴为 **Standards approve／Spec approve，开放 0／0，SP1 已关闭**。安装、原件、实际自身聚焦审查及完整候选独立复核已经满足 C 实现的本地出口；未将 r1 partial 关闭为通过，也未把 D 的运行结果并入 C。剩余为普通提交／推送、精确远端 Ref、本候选自己的必要双 OS CI，以及 D 的真实 Temporal／模型旅程与其独立出口。
