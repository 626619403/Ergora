# 首轮 Workflow 私有 CPU 合同独立审查

日期：2026-11-16。Reviewer：`/root/cycle_cpu_contract_review`；fresh context，未继承实施对话。按根 AGENTS、组件变更协议、`maintainable-project-delivery` 的 independent-review brief 和 `ergora-codebase-quality` 检查。范围仅为私有 CPU 正向验收合同的源码、冻结材料和最终 native manifest；不是正式 Workflow 实现终审。

最新 r5 独立静态复核结论：需求符合性 **approve**；可维护性 **approve**；开放 finding **0**。新 reviewer `/root/cycle_cpu_r5_review` 核对的身份为 `d042292…`／`34e3c4f…`，准确身份及静态 PASS 范围见末节。此前 R1 和随后真实现场暴露的 R2 修正复核保留其原身份 `d042292…`／`7f3ce0ed…`。前次静态审查漏掉 R2 的日志生命周期交互；原 `positive-r2` 实测 archive/gate 拒绝保持，本次修正不能将其转记为 positive。最新结论不表示新 native gate、未来 CPU 测量或 Workflow 已运行通过。主控负责现场执行；本 reviewer 未改产品、测试、配置、Git 或服务。以下历史记录保留原候选及其准确范围。

## 初审准确候选与检查对象

独立测试源码 HEAD 为真实 Git commit `9f0e369af756bcb3a1c4944e3ef9e0aee995ecc0`，完整 porcelain 状态为空，仅有四个 tracked Python 文件。逐一核对工作区原字节、`git show HEAD:<file>`、准备目录副本及 manifest 的 source hashes，同一。公开记录使用本项目 ignored 证据相对路径：

|文件（相同准备副本位于 `.ergora/checks/cw1/cpu-contract/`）|SHA256|
|---|---|
|`workload.py`|`2a99383c82968046f3b46963b8a422218db8b96370697f3450cf9bbdd1640524`|
|`oracle.py`|`b652530d79c30d6d245500ca59bb47b2d74d23657e4eb4f35354e6cb8533b04d`|
|`prepare.py`|`b9022a4fc685a1ab8c73534d835e5d23b928a6b98ede197620b5107a0b3bdb37`|
|`runner.py`|`04bea278a5766f777fdfc67f0d3db650da86dd69997a4bde6b289afef17b600b`|

最终 manifest 是 `.ergora/checks/cw-live-r1/s/training/manifests/positive.json`，raw SHA256 **`1e38dbe5b5ce4634cbf7cefe6bb83dfac25057d596540c6cb8ae57304dcd7530`**，不是准备阶段 draft。其 baseline/candidate commit 及 native aliases 相同，均为上述真实 commit；两种真实算法由分别冻结的 config 选择，符合本 CPU 合同允许范围。核对 `.ergora/checks/cw-live-r1/setup/experiment-prepared.json` 中三份原文件内容／摘要和当前文件相同，runner/baseline/setup 记录也已读取。setup 的 identity 记录尚未启动服务或授权 cycle；本次未认证这些状态之后的运行。

逐项重算实际材料摘要：baseline config `6c2a143d400907a5ad11796d64953db6cc1598170489e884549aef7a7c245fc6`；candidate config `859bef2fc02906d0e8bb901662f5e9b05fcd7a6a30b1198d0abfd36fd6eec09f`；dataset `1734ddd5791b858b1051838f1167f0e33548e9b375c49b32b6fb120a6594a985`；environment `11847a01f874a38e435700d18c4372b4065af9d6562f3c6a462a84cd61152ec6`；stateless initial descriptor `9f5496fc55f776dac23d28afc533eed44a5c6804aa449d602b30223c279b6774`；validation contract **`3de216967b27ef68343ea23f6ae2b5b6bbea1b4e0aaee00478b3fdfc0c37ca4d`**；workload `baa140035f87751486095f84c93197cec57c1a600040ee0647a93f49f29fc2f4`。八份 input 的 raw hashes 均匹配 dataset，分别 32 个合法整数、AB/BA 交替，八个文件 fingerprint 互异。

实际 native comparator 与仓库 `src/ergora/data/reference/platform/upstream/compare_runs.py` raw SHA256 均为 **`9d931b68dc8577cad3f66355588e526a55e5ecf3ebf0bc0e0b0f179828f0ad1d`**，等于 manifest。实际 native `perfctl.py` 也与仓库参考逐字同一，raw SHA256 均为 `5f373f04d50a44f52a2b07179e0f687083f1971374bd853a7e053d3e3b6cf941`；R1 的原 gate 要求在实际 native 文件中同样存在。读取 gate、native executor、sandbox 和 process-job timeout 路径，没有执行它们。

## 初审阻塞 finding

**R1 / high：outer integration evidence 缺 candidate identity，所有正常 runner bundle 都会被原 gate 拒绝。** `.ergora/checks/cw1/cpu-contract/runner.py:145` 的 `attest` 返回值只有 `status`、`artifact` 和 `extra`；`:160–163` 的 integration 调用仅传 `baseline_id`。虽然写入的结构化 `integration.json` 内含 binding，`evidence['integration']` 外层实际只有 `status=PASS`、`artifact=integration.json`、`baseline_id=cpu-baseline`。原 `src/ergora/data/reference/platform/upstream/perfctl.py:129` 在读取结构化 artifact 前，要求外层 `candidate_commit` 等于 manifest；该条件必为 false，抛出 `Integration proof missing or stale`。

本 reviewer 仅解析当前 runner AST，在内存求值原 `attest` 的 return expression，并代入准确 manifest baseline，得到上述外层形状；原 gate 的三个条件组成的 predicate 为 false。没有调用 runner、perfctl 或写造 evidence。最小修正是在 integration 的 `attest` 调用中加 `candidate_commit=manifest['candidate_commit']`；无需改原 gate 或扩大 CPU 集成声明。修正会改变源码／Git commit／manifest，须重冻准确身份并复审，不能将当前 manifest 的 review 沿用。修后最终正向运行仍必须经过原 gate/archive。

## 其余审查结论与限度

- Oracle 独立实现：逐次相加奇数产生平方，再累加平方；不 import workload，不复用乘法循环或闭式公式。对本次正整数材料，递推不变量给出精确整数和，检查每个实际输出与样本数。baseline 真实执行八次冗余乘法循环，candidate 执行精确闭式；无 sleep 或伪时间。
- runner 对两份实际 checkout HEAD、clean 状态、四份源码及执行中 checker 源码核身份，复制合同材料并逐项核摘要，核实际环境和每次 input/config/count；每个 measured arm 由新的 subprocess 完整执行并等待，配对使用同一 input，交替 AB/BA，一次 warmup/arm 不进入比较。时间为 parent `perf_counter_ns` 包围完整进程，包含启动与输出 IO。原 comparator 对固定八对、32 source samples 归一化、10,000 bootstrap、95% CI 及严格大于 0.01 秒的下界筛选；原 gate 会重新计算比较，runner 的 PASS 字符串不能代替它。
- shared host、无独占／频率保证与噪声相关限制已明确，fresh process 不证明统计 IID。预定输入文件不同不表示整数数值绝不重复。此结果最多是该 CPU fixture 的固定样本筛选，不认证训练、模型、GPU、质量、P99 或一般性能。
- check attestations 在实际执行成功后写入；quality 明确 NOT_RUN，CPU integration 明确不认证 native executor/platform。review 从外部读取并核准确 manifest、candidate、validation hash 和 reviewer；缺 review 为 NOT_RUN。该 JSON 是真实审查记录的容器，不是身份认证或签名。registration 的六阶段开发检查显式不可用，不当作 CPU 验收检查，也未运行。
- 当前 command helper 的 timeout 捕获依赖 `subprocess.run` kill/wait 直接子进程；准确 workload/oracle/comparator 不再创建子进程。已读 `.ergora/checks/cw1/cpu-contract/timeout-check.json` 中真实 0.05 秒 timeout 记录。native 总 runner walltime 为 60 秒、queue-plus-run 上限 180 秒，原 process owner 使用独立进程组、GNU timeout 及 TERM/KILL；本 review 只检查代码，没有复测取消、崩溃、资源回收或原服务集成。
- 已读取准备 README、selfcheck 脚本及 `selfcheck-r1/` 的实际 16 份 workload 输出／进程记录、八个 oracle 记录、比较输入／报告和错误输出负例。纯解析核实 16 个不同 workload PID、AB/BA 时间次序、原始窗口与比较输入 elapsed 相同、512 个输出值和输入/config 摘要对应；负 oracle 返回 1。历史 selfcheck 的 manifest 字段绑定 validation descriptor，且早期 process records 没有后来新增的 timeout 字段。它不能认证当前完整 runner、新 native manifest、gate/archive 或未来 live sample，未重写历史证据。

四个源码 AST 解析通过；所有检查均为读文件、Git/hash/JSON/AST 检查及少量整数运算，没有 CPU workload/oracle/comparator 重跑、安装、训练、服务操作或源配置修改。没有在当前源身份下写入 PASS `review.json`。下一步：修 R1 → 固定新 commit 和材料／最终 native manifest → 本 reviewer 复核 → 主控执行新的原生链，并另记真实 gate/archive、Workflow 与资源终态。

## R1 最小修正与新身份复核

复核仍由 `/root/cycle_cpu_contract_review` 完成，仅接收本 finding 的修正和新冻结对象，没有继承实施对话。独立测试源码新 HEAD **`1eba0f5a2b7a1a8d49faf0d98df699df0d68513a`**，完整 porcelain 为空；对原 `9f0e369` 的 diff 只有 `runner.py:163` 的 integration 调用增加 `candidate_commit=manifest['candidate_commit']`，未泛化 helper，未改 oracle、workload 或 prepare。新 runner raw SHA256 **`ee2b89ac25eb82ccaeccbefd731827327884625e7bb036ccd044a41a0a4614b1`**。其余三个文件逐字保留初审 SHA。四个实际源码分别与 Git blob、准备副本和新 manifest source hashes 同一，AST 解析通过；修正记录为 `.ergora/checks/cw1/cpu-contract/integration-fix.json` 和 `.diff`。

全新 native manifest 为 `.ergora/checks/cw-live-r1/s/training/manifests/positive-r2.json`，raw SHA256 **`b7187aac25fd6d055b78c7c5865d598b8beda820950fa259b556799d374cb8d6`**。项目 `cpu2`、baseline `cpu-baseline-r2`、runner `cpu-measured-r2`、experiment `positive-r2`；baseline/candidate 两个 commit 和 native aliases 全部等于新真实 HEAD。与原 manifest 的差异仅这组 ID、commit／aliases 和 runner source hash。原 `positive.json` 的 raw SHA 仍为初审 `1e38dbe5…`，没有改写为新候选。外部 draft 不是本次 review binding。

重新核对所有材料和八份 input 摘要，均与初审完全相同；validation SHA 保持 **`3de216967b27ef68343ea23f6ae2b5b6bbea1b4e0aaee00478b3fdfc0c37ca4d`**。实际 native comparator／perfctl 仍与上述仓库参考逐字相同。`.ergora/checks/cw-live-r1/setup-r2/experiment-prepared.json` 的三个投影文件 raw 内容逐一与当前原件相同，各状态 matching；runner 的材料、comparator、review 参数以及 baseline commit/config/ID 均核对一致。setup 记录 raw SHA：runner `a4aa3c7affe43a6a9e2704944d38f36d1d71ad13103126804144763b364a624f`，baseline `68a89f55eaf52b7fba28933eeaeef79483981bcc4cdd545e3e9634cfc2e8f450`，prepared `3a8c08f754fbe0ac78b54b704212d2af0b5dc07bb3f94fbc8151ec53b5346f27`。

复核解析原 AST 中**实际 integration 调用的 keywords**及原 `attest` return expression，仅在内存求值，得到外层 `status=PASS`、`artifact=integration.json`、`baseline_id=cpu-baseline-r2`、`candidate_commit=1eba0f5…`；原 native gate 对该外层的 integration predicate 为 true。没有执行 runner／perfctl，没有写造 runtime evidence。这关闭 R1 的静态结构缺口；原 gate 的其余检查与实际 CPU 行为仍必须由后续真实调用完成。

最终静态需求／维护性均 **approve，开放 0**。本 reviewer 据真实审查生成约定的外部 `review.json`，仅绑定新 candidate、新最终 manifest raw hash 和上述 validation hash，observations 列准确审查对象、摘要及范围。它是本独立 agent 的实际源码／配置／manifest 审查记录，不是签名或 reviewer 身份认证；不声称审过未来 runtime measurements、native gate/archive、服务、Workflow、GPU 或模型质量。主控告知四服务已启动，本 reviewer 未操作或验收这些服务，也未验收 cycle 授权或投递。下一步由主控执行新原生链并独立保存现场证据；本次未重复 CPU 样本或扩大测试。

## R2 真实 archive 拒绝、最小修正与最新复核

R1 修后首次真实 `positive-r2` runner 输出记录 `comparison_status=PASS`、`review_status=PASS`，原比较报告为八对／PASS，quality 仍 NOT_RUN；但原 archive 输出明确为 **`BLOCKED: Artifact checksum mismatch: execution.log`**，原 gate-report **`passed=false`、`archive_report=null`**。这些是旧 candidate `1eba0f5…`／manifest `b7187aac…` 的真实失败记录；此前静态 approval 未发现这一交互，也未认证过实际 archive 通过。本 reviewer 本次读取并核这些原件，没有重跑 CPU、改 gate、修改原证据或重新投递。

**R2 / high，已修正：把 platform 持续写入的根 `execution.log` 放进 runner 不可变 artifacts。** 旧 runner 的全目录枚举发生在最后 print 和进程退出之前；native `local/agent_platform/process_job.py:103–110` 把 stdout/stderr 接入此日志，`:132–133` 在 runner 退出之后追加 returncode。旧 evidence 列出的日志 SHA 是空文件 SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，当前真实日志 SHA 已为 `0c76b1d59f2541702c8e87fcc367abd89464173e6655b228d79e0b966fdb4ac1`；内容含 runner 最后输出和 monitor 的 `returncode=0`。原 `perfctl.py:108` 正确拒绝不一致。日志生命周期由平台拥有，runner 不能在它关闭前给它作最终不可变摘要。

独立逐项重算旧 evidence 的 **74** 个 artifact，只有根 `execution.log` 不匹配，其余 **73** 个 runner-owned 文件全部匹配。准确旧证据位于 `.ergora/checks/cw-live-r1/s/training/jobs/positive-r2/`：`run-output/evidence.json` raw SHA `0804f72e9415813f7afc3979a3b1c5127d43201e17580969b4fce66fb4b7b317`；`archive-output/execution.log` SHA `2a484c3613f774ebf3a06d189ee3bcece428fe9b0df15395f60181c7a2029fb4`；`gate-report.json` SHA `228252fcf30989306f6e103c23e6b3596f7d83c49f6fa5889a04124f68375296`。本复核不认证旧 Workflow/history/replay 或控制器计数，亦不把旧 CPU 比较 PASS 当作 gate 接受。

最小修正在 `.ergora/checks/cw1/cpu-contract/runner.py:178` 增加准确条件 `path != args.output / 'execution.log'`，仅排除平台持有的根日志；其余 rglob、文件判断、摘要计算、所有 linked check/review/integration/comparison artifacts 保留，不改原 gate 或 platform owner。日志本身仍保留在原输出目录。本 reviewer 解析新实际 AST filter，对旧 evidence 的所有实际文件在内存求值，恰好保留上述 73 个匹配文件；路径比较只排除根日志，不按 basename 排除子目录同名文件。没有生成或改写旧 runtime evidence。

最新独立测试源码真实 HEAD **`d04229205fc5d9f2e90617d2592812e9229a36e6`**，完整 porcelain 为空。相对 `1eba0f5…` 仅上述 artifact filter diff。新 runner raw SHA256 **`3dc4f844e4b68ec4d4eae230c3f0331d90579aab806e77e5cd57b3b255dfbadc`**；其余三个源文件、全部材料和八份 input 摘要保持。源码分别与 Git blob、准备副本和最新 manifest 一致，四文件 AST 解析通过。原 native comparator／perfctl 仍与所审参考逐字同一。

最新最终 native manifest `.ergora/checks/cw-live-r1/s/training/manifests/positive-r3.json` raw SHA256 **`7f3ce0ed0176e72c847b8f20362307272e2a58afdc0fd67ba2ec52bd9b1249ec`**，项目 `cpu3`、baseline `cpu-baseline-r3`、runner `cpu-measured-r3`、experiment `positive-r3`；所有 commit／native aliases 均为 `d042292…`。与 r2 manifest 的差异仅上述 ID／commit、aliases 和 runner source hash，validation SHA 仍为 `3de21696…`，旧 r2 manifest raw 摘要未变。`.ergora/checks/cw-live-r1/setup-r3/experiment-prepared.json` 三份原投影文件内容均与当前原件相同；runner 的 baseline/config/材料/comparator/review 参数与这次身份一致。setup raw SHA：runner `999f7ad51644ba0dac6b02c445f3d659d2348ddfe1efdeb0a794db296783724c`，baseline `4842b080155a72ad0406d8537ca45bf8ba4d9cc0f647b6a77557049f9f2f0e69`，prepared `14390807ae5e68bfe6e659f00e8d1b6ec2f7623dfa9c0695aa647767f63db8a1`。

本次最新静态需求／维护性均 **approve，开放 0**；R2 静态修正闭合，新的完整真实 native gate/archive 仍待主控执行。先把旧外部审查 JSON 逐字保存为同私有材料目录的 `review-r2.json`，raw SHA 仍为 **`3665e81d7025cac46ece6686250f6950b0d66636c26714a705e995b00ed33598`**；再将 `review.json` 更新为仅绑定最新 `d042292…`、最终 `7f3ce0ed…` 和未变 validation hash 的实际静态审查记录。旧记录保留其原 scope，不认证 R2 live failure 已被实际修后运行解决。新记录同样不认证未来 measurements、native chain、Workflow、GPU 或模型质量。本 reviewer 未运行服务或重复 CPU。


## r5 新身份的 fresh-context 独立静态审查

日期：2026-11-16。本节 reviewer 为新的 `/root/cycle_cpu_r5_review`，fresh context，未继承实施对话；读取原始 CPU 首轮目标、根 `AGENTS.md`、当前 `docs/PLAN.md`、上述原审查记录、组件变更协议、`maintainable-project-delivery` 及独立 brief、`ergora-codebase-quality` 的适用参考。公开工作树当前 HEAD `df43660`，已有相邻交付文档变更；本 reviewer 仅修改本报告并在私有材料目录独占创建自己的 `review-r5.json`，没有修改源码、配置、原始记录、Git、服务或计划。

需求符合性 **approve**；可维护性 **approve**；本次审查范围内 **无 finding，开放 0**。这次核对的是 r5 发布身份与原修后 CPU 合同，不能据此认定新的正式 Workflow 首轮已运行通过。

- 私有 CPU 源码真实 clean commit 仍为 **`d04229205fc5d9f2e90617d2592812e9229a36e6`**，完整 porcelain 为空、tracked 恰四个 Python 文件。四源码原字节与 HEAD Git blobs、`.ergora/checks/cw1/cpu-contract/` 副本及 manifest source hashes 一致，四份 AST 解析通过；runner SHA 仍为 **`3dc4f844e4b68ec4d4eae230c3f0331d90579aab806e77e5cd57b3b255dfbadc`**。读取实际 integration 调用 keywords 与 `attest` return AST，仅内存求值得到 `status=PASS`、`artifact=integration.json`、`baseline_id=cpu-baseline-r5`、准确 candidate commit。原 R1 绑定仍在。相对 `1eba0f5…` 的源码 diff 仍恰为排除根 `args.output / 'execution.log'`，原 R2 修正没有扩成按 basename 过滤。
- 最终 native manifest 为 `.ergora/checks/cw-live-r1/s/training/manifests/positive-r5.json`，raw SHA256 **`34e3c4f06912eca774dcd422f8e48df1df2e325f4c219d6f2d35eff7faff379c`**。与原 r3 最终 manifest 的 JSON 差异恰为 project `cpu5`、baseline `cpu-baseline-r5`、runner `cpu-measured-r5`、experiment `positive-r5` 四个 ID；所有 commit／native aliases、source hashes、材料摘要、质量和统计合同均未变。validation SHA 仍为 **`3de216967b27ef68343ea23f6ae2b5b6bbea1b4e0aaee00478b3fdfc0c37ca4d`**。
- 本次重新计算全部七份合同材料和八份 input 的实际 SHA，均与 manifest／dataset 对应；每份 input 为 32 个范围内整数、八个文件 fingerprint 不同、顺序 AB／BA 交替。重新阅读 workload、独立 odd-addition oracle、runner 的完整子进程计时／等待与八对固定统计合同源码，没有执行这些 workload 或 checker。实际 native comparator／perfctl／process_job 与仓库参考逐字一致，SHA 分别仍为 `9d931b68…`、`5f373f04…`、`808aa55f…`，原 gate／archive 和平台日志 owner 未改。
- `.ergora/checks/cw-live-r1/setup-r5/experiment-prepared.json` 中三份 projected 原始字符串与当前两份 native manifest 及 spec 文件逐字一致；runner／baseline source document 和 file hash 与实际注册文件一致。runner 的材料／原 comparator／新 `review-r5.json` 路径及 manifest/output/checkout placeholders 均匹配，runner timeout 仍 60 秒，总运行上限仍 180 秒。setup 的 runner、baseline、prepared raw SHA 分别为 **`646dcbf667cc705515af8f31669b143fe33b488bb015212556d94951205cdbc8`**、**`680ab4df62c61e8b04b90390f95a7036e293658fdcb03aa6560c053b8b29fafb`**、**`7f7e681af248f9bbcf26c1d1732efd476ebe76ed3f528b4dd32f707fdb46a48a`**。准备时 inspect 记录为 prepared／not_queried，job_request／started／result／gate_report 均空；这是记录内容，不代表 reviewer 实时查询过服务。
- 实际注册 runner 指向 `.ergora/checks/cw1/package-r3/venv-r1-sdk/bin/python`，与 setup identity 一致。本 reviewer 使用该解释器仅执行只读环境内省：从解析过的 `prepare.py` 中提取实际 `digest`／`environment` 函数，返回 descriptor 与冻结 environment.json 完全相等。实际安装 worker 文件 SHA 为 **`7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`**，匹配本次指定身份；未重跑或独立认证安装版 53 项 runtime 结果。
- 读取 `live_setup_r3.py` 与 `live_setup_r5.py` 实际 diff：除新 ID、新 review 路径外，还新增拒绝复用已存在对象及 exclusive 写入。准备脚本沿原 registration／baseline／runner／prepare APIs，不写 review approval，也不授权／提交 cycle；本 reviewer 没有运行该脚本。这些只用于新现场准备的发布保护不改变 CPU 算法／测量合同。

本 reviewer 据上述真实检查，按原 `review.json` 的严格顶层及 observations 形状独占创建私有 **`review-r5.json`**；raw SHA256 **`82098e26ea6768bf6396940a14918068090ddfea04c3a80a9efd18e7ab2b6f9b`**。记录绑定准确 r5 最终 manifest raw hash、candidate commit 和 validation hash，reviewer_id 为本次新独立 agent；36 个 inspected artifact 均列实际 SHA。旧 `review.json` SHA **`ea6e5208d78e9ab1c4418164e3aa428fe511a8668ad2c19688a8762ce4e83b42`** 及 `review-r2.json` SHA **`3665e81d7025cac46ece6686250f6950b0d66636c26714a705e995b00ed33598`** 在创建前后相同，旧审查与旧失败保持原 scope。

实际操作仅为读取文件、只读 Git／hash／JSON／AST 核对、上述解释器环境内省及本报告／自身 review JSON 写入。没有执行 CPU workload、oracle、comparator、runner、perfctl、安装、服务操作或新的工作流；没有 commit／push。未验证新 r5 测量、原生 gate/archive、正式 `TrainingCycleWorkflow`、history/replay、重启／取消／资源终态；不认证训练、GPU、模型质量、P99 或一般性能，不提供 release／promotion／ordinal1 授权。该 JSON 是本 agent 的真实静态审查记录，不是签名或身份认证。下一步仍由主控在原授权内执行新现场并保存实际结果，旧运行结果不移记为 r5。
