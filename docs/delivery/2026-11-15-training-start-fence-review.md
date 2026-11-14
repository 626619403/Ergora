# Q4.2b1 前置阻断：独立实现审查

日期：2026-11-15。角色：fresh-context 独立 reviewer（`training_start_fence_audit`），未继承实现会话、未委派。仓库与 docs 均为 Ergora；本报告只认证下述实际读取的范围，后续证据以追加节记录。

## r1：实现、源码接缝与安装身份

原始验收依据为[本片合同](../plans/2026-11-15-training-start-fence.md)及[实施前评审的 r2 修订合同](2026-11-15-training-start-fence-plan-review.md)。已读根、源码和测试 `AGENTS.md`、当前 `PLAN`、组件变更协议及相关架构边界，应用 `maintainable-project-delivery` 的 independent-review brief 和 `ergora-codebase-quality` 的 repository-style／module-design／test-seams。未套用其他训练框架的格式或模块规则；当前 pyproject 仅配置现有 pytest 入口，无新增 lint 规则。

固定基线与读取时 HEAD 均为 `1b58e929aaf495c16f448454c78de23718786ae9`，分支 `refactor/architecture-foundations`。已核完整 tracked diff、`git status --short` 和 untracked 清单。本片产品差异只有 `src/ergora/{cli.py,training.py,reference.py,reference_training_submission.py}`；测试为 `tests/test_training_submission.py`、`tests/test_training_release.py`、原 `tests/fixtures/training_submission_client.py` 及新 `tests/fixtures/training_fence_registry.py`。同时读取 `docs/TRAINING.md` 和本片新计划／交付／计划评审。工作树另有 a2 的两份交付／评审记账及 `docs/PLAN.md`，它们不算本片产品，也没有在本审查中重核 a2 的 CI 或远端发布。

|评审轴|r1 结论|开放项|
|---|---|---|
|需求符合性|**approve，限已核实现、源码接缝和安装字节身份**。尚不能称本片完整本地验收或发布通过。|实证产品 finding 0；B5 安装行为、实际 CLI、自身模板等最终证据待补。|
|可维护性|**approve，限本次源码／测试差异**。职责留在现有 owner，没有发现需要另立抽象、删除 guard 或合并测试的阻塞问题。|维护性 finding 0。|

### 调用、身份和事实边界

- [CLI](../../src/ergora/cli.py#L636)只增加参数和应用调用；[training.fence_start](../../src/ergora/training.py#L126)拥有显式确认、manifest／timeout 输入和原 `_setup` 的 revision 预留。SQLite 事务只包本地原生进程，不进入远端 start。`partial`只为复用既有 `_setup` 传入 timeout，没有新转发模块或另一状态表。
- [reference.training_submission](../../src/ergora/reference.py#L382)把 fence 纳入真实 SDK 依赖集合；[原生进程](../../src/ergora/reference_training_submission.py#L325)仅在 dispatch／resume 调用 `core.environment()`。fence 直接用 `agent_platform.training.create_adapter`，不会读取 `PERF_CLUSTER_ADAPTER` 选取未验 scheduler，也没有调用 `connect`／native client main／runner。导入仍经过 `perf_temporal.client → temporalio`，手册称其需要 temporal extra 是准确的。
- [_Submission.fence](../../src/ergora/reference_training_submission.py#L154)先沿原 `load/status` 核 intent 与依赖记录；有 intent 时从冻结 observation 取完整 Experiment，原 spec／runner 删除不会使它换绑。无 intent 时复用 `_training_records` 的两份原 manifest 字节、spec、runner／repo／原记录关系，且不创建 start intent、不执行新 start preflight。`run()` 的注册／control 检查仍先于该分支；当前注册漂移明确拒绝，未借此关闭 b2。
- mutation 前三个 native 路径均经原 `safe_file`，frozen intent 分支也包括 registry lock、job request 和 fence。已有 fence 经有界 no-follow document 读取并要求完整 binding 相同；native [fence_and_lookup](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L167)随后在原 registry 锁内核完整 Experiment／job 冲突并不可变发布 fence。预读与写入之间的另一不同 fence 最终仍由原不可变 writer 拒绝覆盖。
- fence 分支在 [run](../../src/ergora/reference_training_submission.py#L270)直接执行，不进入后面的 submission 锁。原 create 在同一 registry 锁内先拒绝 fence；原 release 也在该锁内先拒绝 fence 再写 ticket。已有 job 的 lookup 继续允许，晚到 SDK start／receipt 也仍可能出现；响应未把这些事实升级为 workflow／run 归属、停止或 ticket 回滚证明。
- 首次已观察 submitted／rejected 且无 fence 时拒绝；prepared／unknown 只作快照。status 之后才落终态以及 fence 回复丢失后 receipt 才落盘，都可以在同一 binding 重试读回原 fence。返回原字节 SHA、锁内 job 和当次状态观察，并维持 `runtime_status=not_queried`、停止／执行 null。两层 timeout／中断诊断都保留“fence 可能已存在”，没有补 start 回执或发 signal。

这里的确认、路径、持久身份、终态准入与 timeout 分支分别保护显式外部授权、原 native 路径、不可变身份、已知终态和副作用不确定性，均有可达失败。已有 fence 的显式读取还用于决定终态后的重试准入，不能只因 native writer 也核内容相同就删除。原 registry 与 writer 的校验继续由其 owner 持有，未复制锁协议。

### 新测试的价值与原失败记录

新行为保留在已登记的 submission／release suites；没有新增 CI job 或另一个测试框架。无 intent／prepared／unknown 测试分别覆盖原 records 与冻结来源、丢 start 回复后只阻断不对账；首次终态拒绝和终态后同 fence 读回是不同状态关系。三个 symlink 目标分别是原 native 读写的不同入口，尤其 frozen 分支不能靠当前 records 代验。

status 读后写入 receipt／rejection 的 fixture 使用原 status、attempt／receipt／rejection 及 immutable writer，固定真实状态读取与发布的交错；它是服务替身的受控交错，不冒称真实 Temporal。跨进程 held RPC 进一步把实际 SDK 请求停在最后 preflight 以后，fence 在原 submission 锁仍被持有时完成；随后用真实本地 adapter 验 create 拒绝、原 job lookup 保持和迟到 receipt。create→fence 分支还丢掉已完成 fence 的回复，再以同一确认恢复。新 release fixture 在独立进程调用原 `authorize_release_and_create_task`，两个顺序分别验证新 ticket 被拒与原 ticket 保持，同时检查未选中成功实验未被 fence。它的单一 suite 消费者是实际原生导入／状态接缝，不构成产品的单用抽象。

直接读取 `.ergora/checks/training-start-fence/source-fence-r1.{json,stdout,stderr,xml}`：**14 通过／4 失败／45 deselected，pytest 78.11 秒**，外层 exit 1／80.081 秒。三个外部 symlink 已被原 `safe_file` 以 `Path escapes trusted root` 拒绝，新测试却只匹配另一组措辞；完整 Experiment 冲突已被原 lookup 拒绝，但原 registry 先创建空 `registry.lock`，测试误要求零新增文件。当前修正只移除不必要的错误文案匹配并把该原空锁纳入预期，没有为测试增加产品 guard。原失败必须保留，不能写成首次全绿。

修后 `.ergora/checks/training-start-fence/source-fence-r2.{json,stdout,stderr,xml}` 已完整落盘：**18 通过／45 deselected，pytest 74.48 秒**，外层 exit 0／75.362 秒。独立解析 XML 得到18 testcase、0 failure。原 r1 XML SHA-256 为 `eb6dea1444c17348371b2cdd98e8547cb2dec5df55bd28a52af7520334a61952`，r2 为 `d183ec2196fbcf427e905a83e68c15f56139a6a935cc8c1393940d19e5be7dda`。没有把两次运行中间状态或其他 `source-tests-r1` 文件当成本片已完成验收。

### 当前身份与剩余验收

独立以标准库逐字比较当前645产品文件、r1 wheel 和 core／SDK 两个非 editable 安装目录，并核两份 package JSON 的每项字节数／SHA：完全相同。wheel SHA-256 为 `b96465cac3841595a150a68c1ee2de12313231b47890e96bcf09c1a7926b2b21`。相对固定基线没有新增／移除产品文件，只改上述四模块；安装记录分别为无 SDK／Temporal `1.34.0`。`build-install-r1.json` 各步骤 exit 0，两份 reference 记录均 PASS／283／未启动 runtime；基线至当前 reference 与 preset diff 为空，kernel 专家路径未被改动。这只确认安装身份，不替代安装行为。

本轮读取的四产品 SHA-256：`cli.py=12fde7de8142b1b7734efe94fd06433669b0c342290ee9b7e05fd93acb1c003a`；`training.py=a1d9eca318208d9e36732730987ae2ad299478903fc98a64b771fa10b29c191a`；`reference.py=ca6612f7a10c5858970b2681c00a698374c201c0b66c565ae8094d383a609e4a`；`reference_training_submission.py=7fcaf58bcc1223543089243c41dd59668587543d330142a7a9c45cc03f542b3d`。源码 r2 的 `test_training_submission.py` SHA 为 `765a58bdf2100ef7e39b37145212213b45c8027d38eeb1de8221422980a297c4`，新 fixture SHA 为 `cf58cd1166f9a640d3f0ef5323feaa9c9e34bd07b80bcad709c983699896665f`。

尚待本片最终安装原回归、真实 SDK 环境无服务 CLI、本次自身原模板及更新后的交付记录；精确普通发布／自己的 CI 以后另核，不从基线或 a2 转授。本轮没有运行产品测试、安装、模型、训练、GPU、服务或网络；只做只读源码／diff／原件读取、XML与字节身份核对、`git diff --check`，并写本报告。未修改产品、测试、PLAN 或其他报告。

b2／b3 的冻结旧上下文授权恢复、不可续期预算、完整 executor 及后代停止，c／d 的实际服务／CPU循环等仍开放。本片不认证 run 所有权、不真正取消 Temporal、不证明 executor 已停，也没有父循环自动调用授权。

## r2：确认 frozen request 的 job ID 缺口

本节由同一独立 reviewer 追加。上文 r1 的9,690字节全文保持，原 SHA-256 `0a0c81272c2e1026f12721c146cf1fd269f20939bf0cb29dffe5b54a41c82be4`。r1 的“未发现实证产品 finding”结论由本节更正，原失败和已核证据范围不改写。

自身原结构模板 run `0e8cb84ea9f4456bb3d79d6c6156d670` 的原输出指出下述问题；已直接读其 `review.md`、`original-result` 记录和完整源码，独立沿 `fence → lookup_job → Job → write` 核实，而非仅采纳作者转述。原模板51.963秒、22完整文件437,442字节／3资源，结论 request-changes；它的供给文本审查不能认证私有 runtime 或 CI。

|评审轴|当前结论|开放阻塞项|
|---|---|---|
|需求符合性|**request-changes**。冻结 intent 分支仍可接受损坏的原 job ID。|R1，P2。|
|可维护性|**approve，限已核结构方向**。应在现有接缝补所缺的持久身份校验，无需新增模块、writer 或 adapter 框架。|0。|

### R1（P2）：保存 fence 前必须核原 request 的 canonical job ID

位置：[reference_training_submission.py 第160、178行](../../src/ergora/reference_training_submission.py#L160)。已有 prepared／unknown intent 时，本分支从冻结 observation 取 spec，不进入 `_training_records`；原 native [lookup_job 第120–121行](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L120)只比较完整 Experiment，然后直接以 `record['job_id']` 构造 `Job`。`Job` 是没有 `__post_init__` 校验的 dataclass。原 [fence_and_lookup 第168–171行](../../src/ergora/data/reference/platform/local/agent_platform/training.py#L167)会在 lookup 返回后不可变写 fence。

可达场景：冻结 start intent 后，原 `training/jobs/<ident>/request.json` 保留完全匹配的 Experiment，但其 `job_id` 损坏为 null、空值或另一实验的 ID。当前 native lookup 不拒绝它，命令能写下所选实验 fence 并退出0，返回损坏／错误的 `existing_job`。这不只是字段措辞：不可撤回的 fence 已生效，但本地查找事实不满足原 canonical job ID 合同。无 intent 的原 [records 第527行](../../src/ergora/reference.py#L527)已核 `local-perf-<ident>` 并拒绝相同损坏输入，因而两条新入口路径的持久身份保护不一致。

最小修正：在原 native mutation 前沿已有 `_TrainingProject.document`／`safe_file` 读取可有的 request，保留原 `local-perf-<ident>` 检查；完整 Experiment 的锁内冲突继续由原 registry owner 核，不复制其 create／fence 逻辑。不能只在 `fence_and_lookup` 返回之后核 Job，否则错误时 fence 已被新增。无需改冻结283文件，也不能重新依赖当前 spec／runner 来修补 frozen 分支。

必要验证：在原 submission fixture 冻结 intent，放入完全匹配 spec 但损坏 job ID 的真实 request，经实际本地 adapter／安装入口确认明确拒绝且不新增 fence；保留原记录。再核已有正确 job、RPC 在途／丢 fence 回复、无 job 和当前 spec／runner 删除的原接缝仍成立。新的 targeted regression 应直接观察该持久身份缺口，不增加只验证字典 helper 或提示文字的 suite。实施者正在旧 r1 安装件补实红；本节尚不把待运行项计为结果。

本轮仍只追加本报告，未改源码、测试、计划，未执行 mutation 或额外产品检查。修复、最终安装身份和 B5 终态证据待后续复核；此前645字节同一和18通过仅归属 r1 产品，不能转授新修正。

## r3：修正后最终本地终核

本节由同一独立 reviewer 追加。上文 r1／r2 的13,320字节全文保持，原 SHA-256 `f2535d79c09638a3fe059cdab3e5f887710165326f0a1c0751e9cf95bae7c27d`。本节取代 r2 的当前开放结论，原发现、失败和旧产品身份完整保留。

|评审轴|最终本地结论|开放阻塞项|
|---|---|---|
|需求符合性|**approve，限 Q4.2b1 的最终 r2 本地实现与已完成验收**。R1 已修正并通过原失败接缝与最终安装回归。|0，R1关闭。|
|可维护性|**approve**。现有 owner、不可变记录与原生锁继续承担各自职责；新增身份 guard 与所保留测试均有具体风险。|0。|

### R1关闭依据与测试职责

已直接读取旧 `installed-job-id-red-r1` 的 JSON／XML／stdout：旧 r1 安装 **1失败／2.83秒**，外层 exit 1／3.720秒，失败为本应拒绝却未抛错。另读取其保留的真实 request、intent 与 fence 原件：request 的完整 Experiment 与冻结 spec 相同，`job_id=null`，对应 binding 的 fence 确实已创建，SHA-256 `ed5a18e6afd4476656da3b6dd0f719f4dcebe7082a3931d9d651736a9ddbd70b`。这确认了原缺口的实际副作用，不能被旧130项通过覆盖。

当前 [frozen 分支第167–174行](../../src/ergora/reference_training_submission.py#L167)在 native mutation 前沿原 `document` 读取可有 request，拒绝任何不同于 `local-perf-<ident>` 的 job ID。该读取只补 frozen 分支缺失的 ID 不变量；无 intent 分支仍由原 records 检查，完整 Experiment 仍由 registry 锁内 lookup 核对。没有复制 registry 协议、修改283文件或重新依赖当前 spec／runner。原 owner 只会不可变发布 canonical job ID，因此 request 尚未出现、随后由原 create 并发发布的正常顺序保持成立。

原身份冲突测试只补一个 job-id 变体；`source-job-id-green-r2` **1通过／2.76秒**，外层 exit 0／3.671秒。最终安装131项又实际包含该变体、正确既有 job、无 job、删除当前 spec／runner、在途 RPC、丢 fence 回复和终态读回等原接缝。该 guard 及回归保护的是原生 lookup 未核的持久 job ID，不能因完整 Experiment 已匹配而删除。

最终 release 测试还在 alpha 被 fence 后，通过同一原生 fixture 的 beta 参数实际调用原 `authorize_release_and_create_task`，核 beta 返回 binding／ticket 成功与 alpha 原 ticket 保持；fixture 的 receipt ID 随所选实验区分。两个 ticket 顺序仍保护所选实验未来 release 被拒与既有 ticket 不回滚。这里确实运行本地 release owner，仍没有训练、真实质量门禁、远端 adoption 或 merge 证据；没有新增产品模块、suite 或 CI job，也未发现需要移除的冗余测试。

### 最终原件、安装与行为

直接读取并逐件核 `.ergora/checks/training-start-fence/final-local-r2.json`：**185原件／1,668,076字节**，每条路径唯一、实际字节数和 SHA-256 均匹配。索引自身 SHA-256 `f13dd7b54b82b018bbf90c4ce092dad1cbeee7d3e76b690b76ed2725b99d9af1`。其中 `review-scope-r2/` 的四产品／四测试文件与当前工作树逐字相同，包含 untracked 新 fixture 的完整字节；`review-scope-r2.diff` 与固定基线到这八路径的当前 tracked diff 完全相同，30,603字节／SHA-256 `56d02d3cfb3bc4a2668e13578ce4b8bbbfada0d30302755f7fbb6437d3dace8b`。没有把缺少 untracked diff 的文件当作未检查。

|实际证据|独立核对结果与范围|
|---|---|
|最终 r2 wheel／core 与 SDK 两安装|645个当前产品文件＝wheel＝两个真实 site-packages，逐字及两份 package JSON 的逐件字节／SHA均同一；wheel SHA-256 `58760d22a34f3c6dea95c8cce08814f8c79f56a83e68c55fd659859cbc2598c5`。core 无SDK、SDK 为1.34.0；两 reference 记录 PASS／283，原参考与 kernel／preset diff 空。|
|`installed-tests-r2`|以最终 r2 SDK 安装解释器 `-I -B -m pytest` 运行原七 training suites；**131通过／674.59秒**，外层 exit 0／675.816秒。独立解析XML为131 testcase、0 failure／error／skip，并核包含 job-ID 变体与两个 native release 顺序；唯一提示为原 TestClient 弃用。XML SHA-256 `420a71079ee4c8e8e430614edb51f3c4438dc0264d47a368ffd0d455bed50572`。|
|`native-journey-r3`|最终 r2 安装从原公开 owner 准备两个合成合同后，六实际 CLI exit 为2／2／0／0／0／2，16.689秒。逐件核命令 stdout／stderr SHA、相同 fence 两次结果和原 fence 字节 SHA；core 缺SDK、缺confirm、后续新启动检查均按合同拒绝。48原文件的实际字节 SHA及数据库前后快照保持，只新增 candidate-a fence；未选中实验无 fence、未创建 start intent，非法 credentials 保持未解析。|
|自身原结构模板 r2|run `169339e442f64a379f296a910a856b59`，35.450秒／succeeded／approve。直接核原结果 SHA-256 `8293179123d688126c44aa19728e518537b4903167bd4496a51d2587ed02742c`、22个完整快照440,004字节及当前产品／测试同一；485,428字节 prompt＝实际 stdin，全部22完整文件与3祖先资源正文均在其中。其供给文本结论与本次独立源码检查一致，不代替本报告对原运行证据的核对。|

当前唯一更新的产品 SHA 为 `reference_training_submission.py=4967c47a1b7bdac7b562994ebccc9a38a15d2378bef7f165c8ad2a0b898183f9`；其余三产品 SHA 保持 r1 所列值。最终测试 SHA：`test_training_submission.py=e218b589b798163a4f5ccb30a1243238a8cc74d72b0532c960cff8278eee2f9b`、`test_training_release.py=b80a8f14afc7d7d8baa569210aad910c66062e3cb94102ab8db68841170abc2e`、`training_submission_client.py=c003c8233d350649bc4cdc92f8f9fd2b466cd34bacd54b7677ccfbe6ac0803ba`、`training_fence_registry.py=8c81e0571e27c7a3cb1d4497e0abd24df4bc47965f6b34c03398cc5f337ef122`。

历史另外保持：r1安装七suite130通过／667.42秒只归旧 r1产品及当时测试集，不包含后补 job-ID 与 beta 实际 release；原 `native-journey-r1` 六CLI已完成但私有驱动误认 registry.lock 尚未存在而在末尾断言失败，原stderr／前后库存保留，纠正驱动后的新项目 `native-journey-r2` 六CLI／15.385秒仍只归 r1。原 source-fence-r1 的14通过／4失败、自身r1 request-changes 与 R1实红也均未被改写成通过。

### 交付边界

已复读本片最终计划、交付、手册和 PLAN，记录的安装／源码／自身结果与实际原件一致；所写“原独立最终本地／R1关闭待”可由本节更新为上述本地结论。当前全部 tracked diff 和 untracked 清单已重新核：新增的 b2 恢复计划／其计划评审、总体计划记账及 a2 CI终态记账均属相邻片资料，本报告不认证其设计／产品或 a2的远端／CI。b2产品未进入本片八文件范围。

本片的注册漂移拒绝、手工实验级确认、SDK要求、无服务／无 credentials 加载、状态快照和晚到 RPC、原 registry／ticket 锁顺序均维持合同；没有父循环消费者。精确普通发布、远端 Ref和本片自己的CI仍须之后单独核，不从 a2 或本地通过转授。冻结上下文恢复、运行所有权、真正 Temporal 取消、完整 executor／后代停止、不可续期预算及自动循环继续是后继义务，真实训练／GPU／质量／性能也没有在本片获得证明。

本次仅追加本报告并做只读源码／diff／原件／SHA／XML／本地链接与空白核对，未执行新 suite、模型、安装、服务、网络、提交或推送，未修改产品、测试、PLAN或其他文档。上述最终两轴 approve 只覆盖固定最终 r2 本地范围，开放 finding 为 **0／0**。

## 暂存后的完整差异补核

实施者随后显式暂存19个预期文件，HEAD仍为固定基线；本次最终复核改用 `git diff HEAD`，而非只看默认 unstaged diff。上节的20,995字节前缀保持，原 SHA-256 `d6d0ad60a83d091d62b4b21ec277951357f695cfce74bd446a100ac1fc36c5cf`。

新 fixture 暂存前属于 untracked，故固定 `review-scope-r2.diff` 的30,603字节覆盖当时七个既有 tracked 路径，第八个新 fixture 由完整固定快照提供。暂存后把完整八路径 HEAD diff 直接与该旧 tracked-only diff 比较的一次断言失败；这属于差异表示变化，不是文件字节变化。已分别重新核七路径 diff 仍逐字相同、新 fixture 当前／暂存 blob／固定完整快照三者相同，并核全部八文件及185原件仍保持。当前完整八路径 HEAD diff 为32,297字节，SHA-256 `8a3ad19217497a8610bebbad54116bd0218577d93b654949f7646d3c7010ca37`，包括新增 fixture 的35行。

当前19文件中的 a2 CI记账、b2计划／独立计划评审和总体计划状态仍仅核为相邻资料，没有转授其认证。`git diff --check HEAD`、报告本地链接／空白和原报告前缀均通过。本片最终本地两轴 **approve／approve**、R1关闭、开放 **0／0** 保持；未执行新产品检查或模型。

## 固定普通发布补核与自己的 CI 初次观察

同一独立 reviewer 继续本片终核。此前22,307字节全文保持，SHA-256 `ec25d275795152beefd05f860c7bc87170105e224bafac457e0d46a0b046a2bb`，也是此次发布中原 review blob 的完整身份。新增授权仅包括匿名读取官方 GitHub HTTP、在本片 ignored `ci/` 保存采集／验证资料，以及追加本报告；没有授权重跑产品、模型、安装、服务或修改其他公开文件。

固定提交为 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`，parent `1b58e929aaf495c16f448454c78de23718786ae9`，tree `84bf6af8050ed19cc135819c90b58a735089108b`。已从实际 Git 对象逐一核19个 changed blob 的路径、OID、字节数和 SHA，与 `publication-local-r2.json`／`publication-r2.json` 完全一致；`publication-staged-r2.diff` 与实际 parent→commit diff 逐字相同，SHA-256 `a1dc0cc5dc8ff4425d2d72e72abe06956dc696ffe79c9fbe1b375d2916b0bf07`。

另以固定提交的全部645产品文件逐字比较最终 r2 wheel 和 core／SDK 两安装及其 package 逐件清单：完全相同；四产品 SHA 保持本报告所列最终身份。两283参考记录 PASS，parent→commit 的 reference／preset diff 为空，kernel路径未改。发布内的原 review blob 为22,307字节／上述 SHA，本地报告原前缀同一。普通 push 记录 exit 0；其完整 SSH Ref记录为该提交及 `refs/heads/refactor/architecture-foundations`。本轮固定发布核验记录为 `.ergora/checks/training-start-fence/ci/reviewer-publication-local-r1.json`。

|终核对象|需求符合性|可维护性|开放项|
|---|---|---|---|
|固定普通发布6531967|**approve**。固定对象保留最终r2产品、测试和本片原review身份。|**approve**。19文件的相邻a2／b2内容仍归其原reviewer，没有借共同发布转授认证。|0／0。|
|本片自己的CI|**pending**。当前为进行中，不能称CI或精确交付闭合。|**pending，限CI终态核验**；未发现新的结构问题。|终态八job／30必要步骤及终态Ref待取。|

匿名官方 API 的首次六个响应（commit、branch Ref、精确 SHA 的 runs、所选 run、jobs、run HTML）均HTTP200，原 body／headers／URL／UTC时间及SHA独立保存并核对。官方 commit的完整 SHA／parent／tree与本地固定对象相同，官方 Ref亦指向6531967。精确 `head_sha` 查询只有一个匹配的 [Portability push run43650666729](https://github.com/626619403/Ergora/actions/runs/43650666729)，attempt1、分支 `refactor/architecture-foundations`、工作流 `.github/workflows/portability.yml`。2026-11-14 22:57:53 UTC观察为 `in_progress`／conclusion null；八job身份齐全，plan成功，六Linux与Windows native仍在运行。

后续固定观察自己的 Windows job `132618213370`，不反复全量请求；其终态后才重新取本run完整八job及30必要步骤，并再次读官方Ref。本片采集器／验证器参照 a2 的只读脚本，替换固定commit／run／job ID，新增Windows页完整SHA在场检查；来源脚本SHA和本片脚本SHA见 `ci/reviewer-collector-provenance-r1.json`／`r2.json`。没有复制a2的响应作为本片证据，原本地185件也不被其他候选的CI补证。

当前本地工作若推进b2，仍不改变本节审查的固定Git对象；不认证任何后继产品。此轮只读固定Git／原件并匿名获取官方HTTP，写入授权的ignored资料与本报告，没有提交、推送、取消／重跑CI或调用新测试／模型／服务。

## 自己的 CI 终态与精确交付闭合

同一独立 reviewer 追加终态结论。上文25,840字节全文保持，SHA-256 `9c0e68a969ec47182475f3a3427e4bf0ce627b6e37827b2966da1cfd223fc2e5`；发布中22,307字节原 review 前缀及所有历史失败／pending观察继续原样保留。本节只认证固定提交 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`，不转授当前本地b2或其他候选。

[本片 Portability run43650666729](https://github.com/626619403/Ergora/actions/runs/43650666729)已 `completed / success`，attempt1、`push`、官方仓库 `626619403/Ergora`、分支 `refactor/architecture-foundations`、工作流 `.github/workflows/portability.yml`及完整head SHA均匹配。run于2026-11-14 22:56:21 UTC开始，终态API更新时间23:13:31 UTC；最终整组采集在23:14:49 UTC完成，独立离线核验在23:15:00 UTC完成。

|终核对象|需求符合性|可维护性|开放项|
|---|---|---|---|
|固定普通发布6531967|**approve**。此前19 blob、645产品／最终wheel／两安装、283参考、原review及完整远端身份核验保持。|**approve**。固定对象及原owner边界不变，相邻a2／b2内容仍归其原reviewer。|0／0。|
|本片自己的CI终态|**approve**。八个预期job及30必要步骤全部成功，身份与终态Ref同一。|**approve，限本片已核实现及CI终态**。未发现新增结构缺口。|0／0。|

终态API恰有八个预期job：plan、六个Ubuntu 3.11显式group及Windows 3.12 all；八个固定job ID、完整SHA、run ID、attempt1、分支和workflow name逐项匹配，全部 `completed / success`。30项必要步骤为plan的显式group读取、七个native job各自的Python设置／wheel构建安装／packaged reference identity／native regression，以及Windows的PowerShell 5.1 installer and upgrade。每项在API中均完成成功，没有必要步骤缺失、重复、skipped、failure、cancelled或timed_out；全部job亦无失败步骤。

另直接解析八个官方job HTML的 `check-step`，逐项核同一必要步骤的名称、number、success及开始／完成时间，与API的30项完全一致；八页及run页均含完整固定SHA。Windows native regression于23:12:45 UTC成功，PowerShell installer／upgrade于23:13:26 UTC成功，job于23:13:29 UTC完成。五次低频Windows页观察保留原进度，最后一次23:14:33 UTC看到完整成功；未反复轮询全部job或取消／重跑CI。

所有23个匿名官方HTTP原响应均HTTP200，并重新核原body字节数／SHA、GET／匿名属性及官方HTTPS来源：首次六件、五次Windows页和终态十二件。终态十二件包括run API、jobs API、run页、八job页及最后官方branch Ref。终态Ref仍为完整 `6531967e6b6dd8d20ff5ad70d7ae3074c81aca35`；没有以其他run、a2或当前工作树状态替代本片结果。完整核验见ignored `ci/reviewer-ci-terminal-r1.json`及 `ci/reviewer-terminal-r1/`，三原采集脚本仍与来源记录SHA相同；新增离线终核／索引脚本也已固定身份。

新的独立终核索引为 `.ergora/checks/training-start-fence/ci/reviewer-final-index-r1.json`：**75件／3,078,684字节**，索引自身17,350字节，SHA-256 `2356f330db0361942129e144d8e5615dd3953a2cbbc21aca89087f75575bc349`。它逐件绑定66个CI采集／脚本／核验件及9个发布／原本地索引绑定件，含固定commit／parent／tree、run／attempt和两组终核轴；不把活动报告纳入自身循环。原185件／1,668,076字节仍由 `final-local-r2.json` 单独索引，其SHA-256 `f13dd7b54b82b018bbf90c4ce092dad1cbeee7d3e76b690b76ed2725b99d9af1`保持；75件计数不重复宣称包含那185件全文。

Q4.2b1的最终本地、固定普通发布和自己的CI门禁至此分别闭合，最终需求／可维护性均 **approve，开放0／0**，R1保持关闭。该结论不扩大为真实训练／GPU／质量／性能、Temporal执行已停、冻结恢复或自动循环证明。后继b2本地修改没有参与本片固定对象／CI认证。

本轮只匿名读取官方GitHub HTTP，核固定证据／Git身份，并写授权的ignored `ci/`与追加本报告；未新增suite、模型、安装或服务运行，未改产品／测试／PLAN，未提交或推送。报告前缀、逐件索引、本地链接／空白及本报告的 `git diff --check` 终核通过。

时间口径补充：上文23:13:29 UTC对应HTML的“Complete job”步骤完成时间；jobs API记录的Windows job `completed_at`为 **23:13:30 UTC**，run的终态更新时间为23:13:31 UTC。三者身份及成功结论一致，原证据均保留。
