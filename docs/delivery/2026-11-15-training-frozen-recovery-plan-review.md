# Q4.2b2 原登记上下文恢复：独立实施前计划审查

日期：2026-11-15。Reviewer：独立新上下文 agent `training_frozen_recovery_plan_audit`。只审查[恢复计划](../plans/2026-11-15-training-frozen-recovery.md)及其真实接缝；不认证 b1 或 b2 产品完成，不重做 b1 验收。

审查基线为 `1b58e929aaf495c16f448454c78de23718786ae9`；工作树含 b1 在途改动，b2 实施基线仍须等 b1 固定。r1 计划 SHA-256 为 `c04c44acc02bcea0c6911623b0bcdd044c653845a46ce854be989672342a407a`；r2 为 `ecf7314afc2e8eb97b3b383a2215e99dfc4e6b34d6acc952988754640ca282bd`；最终复审 r3 为 `81e1959caea2e07a60788a5b6daff80954ff0fd12a38955d10f24d9ad7b8307e`。三份已在 `.ergora/checks/training-frozen-recovery-planning/proposed-plan-r1.md`／`proposed-plan-r2.md`／`proposed-plan-r3.md` 固定，当前计划逐字等于 r3。保留[有界训练循环](../plans/2026-11-15-bounded-training-cycles.md)的注册漂移、禁止新派发、不可续期预算和完整资源停止义务；后两项仍归后继片。Kernel 专家继续保留在 v3 路径。

## 两轴结论

|轴|结论|开放 findings|
|---|---|---|
|需求符合性|approve；r3 保留 r2 的既有导入兼容修订，R1 关闭|0|
|可维护性|approve；职责留在原 owner，没有证据要求新账本、恢复工作流或通用插件层|0|

本次是计划审查。没有运行实现、安装、服务、模型、训练、网络或产品验收测试。

## R1 / P2：四文件投影核对须保留已支持的导入策略等价顺序（r2 已关闭）

**位置：** 计划第 13 行及 owner 表第 28 行。

r1 要求原 journal 中的四文件与 `publication_files` 投影一致，但未写出现有登记协议的等价例外。`registrations.publication_files` 在第 65 行按已排序 templates 生成 `allowed_task_types`；`registrations._import_plan` 第 254–262 行则明确以集合核 membership，并把合法原 policy 文档保存进 `registration.files`，保留其原顺序。`_prepare` 第 114–118 行也会沿用该物化结果。`tests/test_registrations.py` 第 309–337 行直接记录并保护这个支持行为。

因此真实成功导入后，journal 的 `registration.files` 可以是 `["repository-governance", "large-change"]`，生成投影却是 `["large-change", "repository-governance"]`。两份登记具有同一合法语义；直接 canonical 比较会阻断它的旧运行恢复。仅有 published result 或完整 intent SHA 不会消除这个差异。

**最小修订：** 在第 1 条补明：校验完整 policy 对象结构和成员后，仅在比较投影时规范 `allowed_task_types` 的顺序，其余字段仍精确比较；不得改写 journal、保存的 files 或 native 原件。现有 `training_cycles._decode` 第 58–63 行已经这样处理，可沿用其局部比较规则；不用引入共用恢复框架或更改原发布算法。

**验收：** 沿已有 legacy-import fixture，通过公开 import 生成真实成功 journal，再经 b2 的来源选择和训练子进程校验读回；只改变该等价顺序应允许，增加／删除类型、附加未知字段或改其他投影仍拒绝。这里要求的是登记来源接缝和实际恢复入口，单独断言排序结果不足以覆盖误拒绝。

**处置与复审：** r1 需求轴为 request-changes、可维护性轴 approve，开放 1／0。r2 第 1 条明确仅按既有 `training_cycles._decode` 规则规范 `allowed_task_types` 顺序，保留原 journal／files；R3 另将公开成功 import 的非默认等价 policy 顺序纳入验收。已独立重读并核对两份固定计划及当前计划 SHA，最小修订满足本 finding；R1 在计划范围内关闭，不转授为该路径的运行测试通过。r2 同时补登记／start／当前三种 revision，以及 native stop-status 消费路径和 job 身份校验，均与下面源码边界一致；未发现需要新增 owner 或抽象的改动。

**r3 追加复审：** 已逐项核 r2→r3 完整差异及当前／固定 r3 SHA。r3 明确禁止的是训练 start 的准备／派发，保留取消 owner 内部的必要两阶段；明确本地 reservation 退出后才 RPC，不通过 `_setup` 对账；并将聚合 journal 的独立容量边界作为 R2 前义务。改动落实下列实施约束，没有扩大恢复授权或新建运行权威。r3 两轴 approve，开放 0／0。聚合容量的具体数值和可读历史范围仍待实施前实证；这不是已实现的容量支持声明。

## 已核事实与实施边界

以下是源码核实后的设计约束，不另外计为开放 finding；实施验收仍须逐项证明。

- **来源与版本。** `registrations._reserve` 第 158–166 行先保存完整 `source/before/after` 再作 SQLite reservation；`_finish` 第 169–192 行发布四文件、提交 published 状态后写 v1 result，绑定 operation、canonical 原 record SHA 和 registration SHA。原 journal 的 after 仍是 pending，不能要求其原字节变成 published，不能替缺失 result 造成功证明。result 本身不带项目 ID，项目、repo、definition、marker/control home 与 operation 的关系须经它绑定的完整 intent 核对。该来源仍以已接受的可信目录为边界，不产生跨用户或跨机器认证。
- **三种 revision。** 登记快照 revision、原 start intent 的 `project_revision`、本次操作者确认的当前 revision 须分别表达。`projects.bind` 第 68–82 行会增 revision 而不新建登记 journal，`_Submission.load` 第 91–100 行也未要求原 intent revision 等于所选项目快照 revision。不得把三者强行相等或把旧 revision 当本次确认。恢复只需沿既有完整 submission identity 核 repo、execution、registration SHA、control home；使用原 intent 保留真实提交 revision。当前项目的存在／revision 确认应读当前项目，不能借默认 `training._project` 再强制当前模板仍含 training，从而误封已移除训练模板的旧运行停止。
- **默认路径与操作白名单。** `_TrainingProject.registration` 第 41–47 行的当前四文件比较应继续用于普通入口。恢复来源核对与模式选择须在该 owner 明确处理，并由子进程重核所选 journal；不把外部 cycle JSON 变成来源凭据。`_Submission.run` 第 317–328 行在无 attempt 时会走 preflight/dispatch，因此恢复不能只把普通 `resume` 换成旧 project 后原样放行。应在原 submission owner 明确拒绝该分支；只允许已有 attempt 的对账，prepared 原 intent 仅可读／显式 fence。
- **取消的内部步骤。** 计划的“禁止 prepare/dispatch”须解释为禁止训练准备和新 start 派发。已允许的 `cancel` 仍要沿 `_Cancellation.run` 第 214–231 行本地冻结取消 intent，并在 attempt-before-send 下发送原取消信号；不能按字符串在共用 context 一刀切拒绝所有模块的 `prepare/dispatch`。白名单留在拥有该动作语义的 submission／cancellation owner。
- **无 intent 的旧 fence。** b1 当前 `_Submission.fence` 第 158–161 行允许无 intent 时读当前 records；b2 恢复分支必须显式拒绝这种回退。成功登记 journal 不包含实验绑定，不能用当前 spec 为旧登记补出一个实验。已有原 intent 时取冻结完整 Experiment，沿 b1 的精确 job ID／Experiment 校验和同 binding 幂等，不对未选择的旧成功轮批量 fence。
- **unknown 与精确 run。** `_Submission.reconcile` 第 258–271 行按原 workflow、完整初始 Experiment、原 intent memo 查回 receipt；NOT_FOUND 保留 attempt。`reference_training_runtime.lookup` 第 11–41 行核第一条历史中的完整初始输入；`_Cancellation.lookup` 第 116–127 行再固定原 run 并核 memo。取消丢回复沿 `find_signal_event` 对账，不发新的 start 或重发同一不明信号。
- **连接支持已能具体确定。** 受校验安装的 `agent_platform.core.environment` 第 69–83 行强制 `127.0.0.1:7233`、`default`、local-dev 和本地训练 adapter；当前 ambient endpoint/namespace 不会覆盖它。`perf_temporal.connection.connect` 第 5–15 行依该环境连接。`reference_training_submission.main` 第 338–339 行以及 cancellation main 第 240–245 行在远程步骤加载此环境。首片据此限定同一受支持本地 runtime；这不证明 loopback 上服务未被重建。服务无原 history/memo 时应按现有规则保持未确认，不自动迁移、换服务或重发。
- **旧 config 漂移与 artifact 路径。** 有原 intent 的 status／reconcile／cancel 无需重新读当前 manifest 或 runner；取消派发第 158–164 行已从冻结 spec 构造临时 native 输入，不依赖当前同名 spec。路径仍须留在原 canonical execution；manifest URI 必须对应原 state 下的 `training/manifests/<id>.json`。`adapter.safe_file/read_raw` 第 48–67 行提供路径、普通文件和容量约束。native `LocalTrainingAdapter.lookup_job` 第 115–121 行只核完整 Experiment，仍信任保存的 job ID；`poll_job` 第 146–153 行也不是完整来源读取器。R4 的异 job／symlink 拒绝不能凭“复用 adapter”推定已经具备，须在现有恢复／cancellation 接缝验证其实际消费文件。不能为这些读取重新运行会要求当前 runner/baseline 的 start preflight。
- **容量要按 journal 而非单份 native 文件计算。** 新 reader 可复用现有有界 ordinary-file／严格 JSON 原语，但当前 `registrations` 没有有界 journal reader。journal 同时保存 before/after，并重复 definition 与 files；合法 raw native 文件也可能在 pretty 编码后超过 1 MiB（既有 `test_registrations.py` 第 340–352 行）。R2 应固定 journal/result 自己的读上限与超限报错，不能直接套单份 native 文档的默认 1 MiB 或截断后算 SHA。
- **CLI 与锁。** 成组原登记选择、完整登记 intent SHA 和恢复确认留在应用 owner 验证，CLI 仅解析；start/cancel 自己的 intent／run／reason 确认继续存在。`training._submission` 第 240–257 行和 `_cancellation` 第 267–282 行已有“两阶段、本地 reservation 后释放 DB 再 RPC”的接缝，应保留。恢复不能把 `reconcile` 或取消 RPC 直接放进 `_setup` 的 `BEGIN IMMEDIATE`。submission/cancellation 文件锁继续非阻塞；fence 不等待在途 start 的 submission lock，而沿 native registry lock 与 create 互斥。计划中的“防止选择漂移”应指本地确认与冻结阶段，不应延长成跨 RPC 的 SQLite 锁。

## 范围与检查记录

已读根及源码 `AGENTS.md`、当前 `docs/PLAN.md`、[组件变更协议](../architecture/component-change-protocols.md)、原始有界循环义务与完整 b2 计划；按 `maintainable-project-delivery` 的 independent-review reference，以及 `ergora-codebase-quality` 的 repository-style／module-design／test-seams references 做只读检查。

实际查看 `registrations` 的 reserve／finish／publication_files／import 路径，训练应用入口及其 CLI，`reference._training_process` 与 `_training_records`，`_TrainingProject`、`_Submission`、`_Cancellation`、runtime lookup、native environment／connection／adapter 的构造与 artifact 读取，以及现有登记／提交／取消测试的相应断言。核了 Git HEAD、工作树和受审文件摘要；测试源码只作证据，未运行。

报告静态检查通过：UTF-8、末尾换行、无行尾空格、3 个 Markdown 相对链接均存在；当前计划与固定 r3 逐字相同且摘要匹配。未用文档检查代替产品验证。

工作树 b1 相关主文件在本次读取时 SHA-256：

|文件|SHA-256|
|---|---|
|`src/ergora/registrations.py`|`01e3c273e2a9bc214a2db9535ad10a7205d3015734677b4366009e4e5821e09e`|
|`src/ergora/training.py`|`a1d9eca318208d9e36732730987ae2ad299478903fc98a64b771fa10b29c191a`|
|`src/ergora/reference.py`|`ca6612f7a10c5858970b2681c00a698374c201c0b66c565ae8094d383a609e4a`|
|`src/ergora/reference_training_context.py`|`852f5422067be11fabd22e754942b4986877f1dc3a63e400e9781966833b5b04`|
|`src/ergora/reference_training_submission.py`|`4967c47a1b7bdac7b562994ebccc9a38a15d2378bef7f165c8ad2a0b898183f9`|
|`src/ergora/reference_training_cancellation.py`|`4635d0c68546d92b680084adb0303b0cee0222eec67277e79fdd1f3491e87c9e`|

本次只新增本报告，不修改 PLAN、产品或测试。最终 r3 计划两轴通过、开放 0／0；b2 的实现、安装、真实变化恢复、独立实现审查、发布和 CI 均保持待验。
