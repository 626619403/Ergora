# D2-A2 原 r1 失败证据独立评审

2026-11-13，评审者 `refactoring_journey_evidence_review`，全新上下文。此次评审确认首轮失败记录与原件相符；首轮仍为 `BLOCKED`，完整 A2 成功验收仍开放。

## 范围与固定身份

依据原始 A2 要求、[项目规则](../../AGENTS.md)、[专项计划](../plans/2026-11-13-specialist-presets.md)及 maintainable-project-delivery 的 independent-review brief、AIHERO 索引、code-review、codebase-design 审查。Spec 与 Standards 另由 `spec`、`standards` 两个全新上下文只读评审者分别检查，未读取另一轴结论；受四个活跃槽限制，两轴依次执行。

产品基线为 `3122487fe57d43188cd5c5a42a787d506a29d5a7`，评审开始的文档 HEAD 为 `00922d302daa371ab980093889a8468694c10a94`，分支为 `refactor/architecture-foundations`。核对 `git diff 00922d302daa371ab980093889a8468694c10a94 -- docs/delivery/2026-11-13-refactoring-journey.md docs/PLAN.md`、新增公共 JSON 全文，并分别查看固定的 `3122487fe57d43188cd5c5a42a787d506a29d5a7...00922d302daa371ab980093889a8468694c10a94` 差异与提交列表。后者只有后续文档提交，未当作本片运行结果。报告成文时并行 B1 已提交 `e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`，该邻片提交不在本次评审范围。

本次范围是[交付记录](2026-11-13-refactoring-journey.md)第 1–35 行、[公共证据](evidence/2026-11-13-refactoring-journey.json)及 PLAN 的两处 A2 状态。第 39 行的独立第二轮准备与在途状态不构成本次成功验收；其他 B1 未提交变更、PLAN 中其他片及远端／CI 状态排除。

|检查对象|SHA256|
|---|---|
|交付记录全文快照|`07bebed62c4ff3ba0e6689519fe1fdb37b3b9824dc1b04899055ea9d8db6a807`|
|公共证据 JSON|`80efb36f3c4e32f7603ed6300374e71f0390b374510845a2f049dd85c11855e3`|
|PLAN 初读快照|`d5d44e62e1201dea33ac9897435560f34f6aad2e71a7eb3b5b261ffcc88efc48`|
|PLAN 收尾复读快照|`f03e80a26b45d0112486838d15af96c60245550e16ada1e9755e515bb9d41ac5`|
|PLAN 的 A2 原 r1 结果句|`a93232d61dd1f974b7524f027cebf72766e3e5f3173d7baf5b64fa17570d86a7`|

PLAN 在评审期间由并行 B1 工作更新，A2 两处状态保持；上表的结果句从“A2原r1为BLOCKED”至“完整成功旅程及独立后续验收待完成。”，用于限定本次检查内容。

实际任务为 `refactor-module-1`，原 run 为 `01a1d360-d7ca-744f-9f7d-469409c581ad`；fixture baseline 为 `16f94116df2c9ec795b085146b5be6c27711d1d2`，候选为 `ad230f4dece315541934ed3bc87c3844860e7ac2`。原预算 ID 为 `fcffced8e3db44c29573a3c40a3be130`，摘要为 `f17fbead35865c482ebb8ccb17fbdb7714b776662d62692e7dfaac0b8a36535d`，保持 5400 秒／600 秒 stage／7 槽。

## Spec

独立轴结论：本轮文档与原件核对无 finding；完整 A2 仍开放，不能据此验收成功。

七会话 input／prompt／stdin／protocol 一致，祖先资料、来源及逐父权限吻合；四成功会话完整读取 20 资源 14,525B，三取消会话无输出／判词。九 owner、七原槽及 67 产物摘要一致；原预算、精确 plan 批准、原 run／submission 和 1,253 事件恢复原件保持。同一候选的可信 verify、212／6 差分、真实 caller 两测试及精确 baseline 恢复记录相符（交付记录第 23、31、33、35 行；公共 JSON 的 recovery、quarantined_candidate_check、original_evidence_sha256）。

规格要求三个独立 review 及完整恢复交接，交付记录第 14–17、25–27 行和公共 JSON 的 unverified 明确保留缺失判词、REVIEW_READY、approved export／handoff；未把取消称作模型否决，也未借 A1 或其他片关闭 A2。第二轮仅记录准备／在途说明，未授予成功。本范围未发现未经请求的行为。

实际检查为只读 Git、Python 及 SQLite `mode=ro`；未重跑模型、checker、重放、服务或安装，未验第二轮、发布／CI 及全系统后代清理。

## Standards

独立轴结论：本片证据记录未发现硬违规或有实证的 possible smell；不代表 A2 完成。

依据 AGENTS.md、PLAN 的持续验收规则、专项计划 A2 与每片出口，以及指定交付／独立审查／设计 skills。仓库未发现 CONTRIBUTING 或 CODING_STANDARDS 文件。

全新上下文只读检查指定三文件与 `00922d3` 后差异，历史基线单独区分；两份公开文件 SHA 与固定值一致。新增 JSON 全部原件摘要及七会话投影匹配；直接只读 control 数据库核实会话状态、prompt／stdin／protocol 一致和三取消会话空 stdout／stderr。核对恢复读回、重复 start 与原记录相等、历史事件数 1,253，并阅读驱动、审计／恢复脚本及相关原件。相对链接有效，公开文件未带本机路径。

首轮 BLOCKED、原 task／run／预算及恢复 harness 失败均保留；取消会话没有被写成模型判词。第二轮只记录准备与在途状态。第二轮运行成功、三审查判词、完整 REVIEW_READY、approved export／handoff、产品行为重新执行、远端及 CI 未验；并行 B1 改动排除。

## 原件核对与实际检查

原件入口为项目本地 `.ergora/checks/refactoring-journey-r1/`，运行存储沿原 checkpoint 的 `work` 定位到 `refactor10a` 的 control／runtime；受保护 fixture 位于 `.ergora/checks/refactoring-preset/fixture-source/`。本次没有重新执行这些驱动或审计脚本。

|已读驱动／审计源码（位于 `.ergora/checks/refactoring-preset/`）|SHA256|
|---|---|
|real-journey-r1.py|`eabe71dfc39c51caf961b0e1287ecd81e3220192a6236d81f071b8d421caba5a`|
|audit-journey-r1.py|`e8501468b5e1bcd02acdd2628e38f7560b301ef22a859d103f0d7cc1acd66af9`|
|close-blocked-r1.py|`ec55c404d40a529df2afdd6bcc979c92a33fc083a78ccaf2901f21324fe636f3`|
|recover-blocked-r1.py|`5a8e86a336656c48e4b1a667c85d8895659a14171fb11f565bd1b92d7ef1f4ac`|
|recover-blocked-r2.py|`bf0616a211d05ee8958059813358cf6efee6fbb833fca3b226b62c537dd0b2a8`|

公共 JSON 的七个 `original_evidence_sha256` 全部逐字节重算相等；另固定未列入该投影的检查输入如下。

|原件（相对本地 r1 证据目录）|SHA256|
|---|---|
|checkpoint.json|`2c0778c2d14efc9386d6295b8d1e48db01b01ac7c3bcb77fed75c47b6457acc1`|
|submission.json|`7cc85443467fe341e178631a4cdce41e43d09bd7b39566b02926fbfb8cebbbbd`|
|quarantined-revalidation.json|`dcdcb26fc13e0c14cc2681d2db1842f6261d40bb1ef45a1125ceaae9b9ee408c`|
|blocked-recovery-r1-error.json|`9b31f68c5a01f6fd8811c8312725553755bc2c82f4be1744a314d3faf028b32d`|
|blocked-recovery-r2/blocked-evidence.stdout|`b46c92bdf37bffe187e37cabd09e0768eec9e499e2278f56e96964c9d5395796`|

主评审独立完成以下只读核对，结果均相符：

- A1 wheel SHA 为 `f97741f8a21e78db1813ee9abe86dce357a4fd65c14a11f5d40109be88677143`；475 产品文件逐字节等于 `3122487` 的对应 Git blob，也等于本次非 editable 安装目录。未安装或运行产品。
- 从 control 数据库读出全部七会话，重算原 input 树摘要、完整 assets、request／task、prompt／stdin／protocol 及原 result 摘要；逐一核 38 条声明的结构祖先来源、原 definition／Skill 字节、逐父 ceiling、实际 policy 和 native command。writer 的读写／网络与 host isolation 限制沿原 advisory／unsupported 记录，没有当作强隔离。
- 全量解析原 stdout 的 MCP list／read 页，核资源大小／SHA、连续 UTF8 offset 和 `next_offset:null`。四成功会话各一次完整 list，共 20 资源 14,525B 全文；三取消会话共 18 资源 8,804B，读取为 0，stdout／stderr 为空、无结果文件或 native 握手回执。三者约 599.63–599.67 秒后 returncode -15，不推断底层 provider／CLI 原因。
- 九份 job 请求中的 admission 全等于原 task spec；原 executor 状态、collected／published receipt、owner／body／collection 的预算身份、确认和全部 67 产物 1,123,373B 摘要相等。七份 model-attempt 精确匹配原 slots，九原 owner PID／start 身份当前均不存活。端口关闭及 daemon 停止按原 shutdown／closure 记录核对，未探测或操作第二轮服务。
- 唯一 owner 批准对应原 plan SHA `913e532f2fc8fc8346f84551f5b875043519f65a52c1bb281b36d0f443d336e9`；原 history 的唯一批准 signal 与 receipt 相同。完整 1,253 个事件 ID 连续，首 payload 全等原 task spec，164 处活动输入保持原 admission，末 payload 全等原 BLOCKED outcome。r1／r2 恢复目录中的原 run 读回、submission 和重复 start 相等，最终 shutdown confirmed。重放通过是已保存的实际记录，本评审未重新运行 Replayer。
- 原 bare Git 的 candidate 以前驱 rewrite commit `ab277ad7b25ba8bc8641815c7452f2f6936aee59` 为父；diff 仅预定 normalizer、一个 caller 测试与报告。七个 baseline 文件与 fixture 相等，四个受保护文件在候选中未改。可信 integrate／verify 与隔离复验原件使用同 candidate／baseline，记录 212 normalize／6 aliases、generator、两个 caller unittest 及独立精确 baseline 源码恢复通过。原仓库只有 baseline main，隔离验收 worktree 已移除，没有 approved export 或采用。
- 阅读 checker、fixture、候选 diff、相邻输入装配源码及五份驱动；核链接、公共 JSON 解析和指定 tracked diff 的 `git diff --check`。评审辅助权限核对脚本曾因把三类 members 当作单表、将运行时补充 policy 当作原字段而报 KeyError／AssertionError；修正只读比较方法后七会话通过，原件未改。

## 未完成出口

原三个 review 在期限内取消且没有结果，触发原六阶段 BLOCKED；因此缺少三个候选审查判词及完整 REVIEW_READY、approved export／handoff。这是实际验收阻塞，已如实记账，不是对原候选的模型否决。无需修写首轮结果；成功路线需在独立新 task／预算保留其自身原件后补核，首轮原 task／run／预算继续保留。

本轮不验第二轮结果、模型理解或计费、异构后端、GPU／Windows／生产部署回退、全系统后代清理，以及本候选发布／远端／CI。隔离源码恢复的记录不能扩大为生产回退；失败恢复的 recorded replay 不能扩大为成功重构旅程。

Spec finding 0；Standards finding 0，均限于上述原 r1 失败证据与记录范围；完整 D2-A2 保持开放。
