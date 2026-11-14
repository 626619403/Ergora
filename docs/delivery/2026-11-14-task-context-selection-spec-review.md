# F10b 独立需求审查

审查者：Codex fresh-context reviewer `/root/task_context_spec_review`。日期：2026-11-14。原始要求和[验收合同](../plans/2026-11-14-task-context-selection.md)先于实现者说明读取。基线为 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`；候选为该基线上未提交的工作树，包含未跟踪的 `task_context.py` 与 `task-definition-v7.json`。本报告不覆盖 F10a 的发布状态补记。

## 当前结论

- 需求符合性：**最终本地终核 approve，开放 finding 0**；范围为下列精确 r2 候选与实际本地证据。
- 维护性：随需求调用链检查未发现实证所有权问题；结构轴发现的到期窗口已修并复核，本轴不替代另行 fresh-context 结构审查。
- 本地阻塞 finding：0。发布、精确远端 Ref、本片自己的 CI 及原独立固定候选补核尚待，未借 F10a 或其他候选成功。

## 核对结果

`tasks._definition` 沿原预算准备 owner，在监督 scratch 内调用 `task_context.selected_manifest`。来源限于本项目最新有效记忆 revision 及活动 Skill 的精确 name／digest／head revision；候选本身不会成为活动 head。完整目录摘要、每件正文及执行位都进入同 id 的显式新根；根其余字段、节点引用、成员路径、grant 和 limits 沿原定义库修订及 manifest 编译核验，没有额外包装根或全局资源发布。

`workflow_definitions._materials/_readable/_Compilation` 保留全部祖先来源、同名 Skill 冲突、各父子 read 上限与逐 scope 静态材料容量检查；完整 Skill 附件仍要求原 MCP 交付及连续读取证据。v11 沿既有 Input／Adapter／Workflow 继承链，仅登记版本队列及请求根；原预算、六阶段、候选、批准、attempt-before-send、unknown 对账及 job owner 未被替换，没有新调度器或状态表。

`reference_task_creation.budget_run` 的 `BEGIN IMMEDIATE` 与原 task lock 内，`publish(save_intent=True)` 在首次 intent 写入前执行 `require_current`。preview 后的更正／删除／到期／head revision 变化不能初次发布。resume 必须先加载持久 intent；无 intent 不从 prepared 旁路发布。已有 intent 的恢复和重复 create 不再读取 canonical 来源，继续原定义、材料与预算。

CLI 和 HTTP 的原 prepare／preview／create／resume-create 路由直接使用同一任务 owner。公开用法明确区分 definition7 与 input11、初始 baseline 与测得改进、静态余量与实际阶段输入容量、冻结资料与 canonical 删除，以及尚未接入的图形选择表单。

## 实际检查与证据边界

本审查执行 `git status --short`、`git diff <baseline>`、源码／邻近调用者读取与 SHA256；未改源码、安装、运行 suite、提交或外部写入。读取的邻近 owner 包括 `memory`、`skill_assets`、`definition_bundles`、`workflow_definitions`、`asset_trees`、`reference_creation_process`、`reference_executor`、`reference_inputs`、`reference_workflows`、CLI 与 `web`。

保留的开发证据位于 `.ergora/checks/task-context-selection/`：development-r1 六失败／36.42秒（stdlib bridge 顶层 YAML）；r2 六失败／54.52秒（text-only 夹具遇完整附件）；r3 六通过／59.96秒。materials-r1 一失败／37.02秒（夹具只读附件首段）；materials-r2 一通过／56.92秒。失败未被重标成功。

额外执行了只读、`-I -S -B` 的标准库离线核验：读取 materials-r2 原 intent，经 `execution_input(...).require_submission()`、`task_envelopes.selected_context` 与完整图读取成功，未导入 yaml／jsonschema／temporalio／mcp。原 intent 文件 SHA256 为 `0ebc55e93c64a33121aba7f47ee93d429b97c1e1293fa082ab3bfff030a0c0a3`。同一 `native-development` 根从 1.0.0 派生到 1.0.1；七个叶全部继承所选记忆，七份实际 materials 的 selected_context 指针与 admission 完全相同，七份 coverage 均交付所选附件完整 75,600／75,600B。这是确定性材料合同证据，不是 GPU、模型理解或质量改善证明。

首次读取 install-r1 包身份记录时，其记录为非 editable、577 产品文件、两 RECORD 核对、283 冻结文件、wheel SHA256 `123a0b1b4704f9222db24a34f265e28b2e4217518822b1449d459025364288bc`；核心三文件与下表源码 hash 相同。当时安装回归只完成前六项、源码扩大回归未结束；自身模板运行有 succeeded 记录，但未以运行状态替代原审查回复。以上不是最终验收通过主张。

## 精确检查身份

以下 hash 为首次完整源码检查的工作树身份；最终工件到齐后须核同片变更并补记。

|文件|SHA256|
|---|---|
|`src/ergora/task_context.py`|`c6febe3a946356d53154503de5bd56ec55dc813e4b0941a78376df544a343847`|
|`src/ergora/tasks.py`|`1ed05e57a9f4c673976b965fcaeaa648457a39ac55afb5272e9fe01cf1db4ab1`|
|`src/ergora/task_envelopes.py`|`6f506429c9d91dd4696a8d0cd89ccefb1ca182849430bb4242d974b45f7cd2cf`|
|`src/ergora/reference_task_creation.py`|`7bf31161ba500384b060410becea33586ea5fe1150be48ae1d0c5bf10923b173`|
|`src/ergora/reference_inputs.py`|`c116d153b867aff6f013f1d980c9bf3c874d74013c2e32770d8b768c42aae09b`|
|`src/ergora/reference_workflows.py`|`15cc616591bc9ab914092aa9f1245f4a95cf904311c05dff88ecd54a0c962be7`|
|`src/ergora/skill_assets.py`|`fa667c48d80eb6a287f26da60d5e2a748ad76f33c024277de129e86b142676ef`|
|`src/ergora/cli.py`|`0a897a10db66224dc0576d416fc974e60c77bd9f77e458994bc2558d1bd52bb6`|
|`src/ergora/data/schemas/task-definition-v7.json`|`58537be6e181bc33f91e3d3774848f9ab6c201b38cf08c83372c39e4c37850ac`|
|`tests/test_native_six_stage.py`|`6fde13bbbaeccf26b92f536aafca25ffc8db512b0425a7d5a6de70d833167392`|
|`tests/fixtures/full_stage_acceptance.py`|`2ce425abd45e349d9bd275cb95e8e349c29265b4c4c99827d092a07db8a8bf92`|
|`tests/fixtures/reference_acceptance.py`|`5398128afcc717b71e27ec59ddb5e48c8bc6e97345dd4def11070cf818fdbb04`|
|`tests/fixtures/stage_agent.py`|`f32eda82732b14689931ece96309a07e66e12f03f70b5a77b64ffec8e17d6cf4`|
|`tests/fixtures/work_delivery_acceptance.py`|`8ba563699fabb28d728d3b14248eca42ad31a32e3115207e112bff0946ae9b45`|
|`docs/plans/2026-11-14-task-context-selection.md`|`d94997e09a27eddfe3565f920b7c1964c26af5ad175e83effa9ce5dd53eee470`|
|`docs/USAGE.md`|`3158a0f3d8a7b5d7c75e9a1fe0b808f4ecd1efc953cccf33d4d0e26aa47e1c55`|
|`docs/architecture/current.md`|`2f0f0140946f860b74c9b3ff7f9d2808fb5cf930cab1faaa34bbe667a234ede2`|
|`docs/architecture/contracts-and-identities.md`|`9c41158aef5136cdbe1f046742ca82ec9e53e0d96ae4aeaf6d152a3396d5bd13`|

## 首轮修正补核

结构轴发现并复现了 slow Skill get 跨越记忆期限的真实窗口：旧 `_sources` 先采样 memory catalog，之后核验 Skill 目录，首次 intent 前可能继续使用早于期限的判断。本轴复查修正后实现：完整 Skill get 已全部放在 memory catalog 之前；catalog 在目录 I/O 完成后取服务器观察时刻。最终检查仍处于原 SQLite 写预留与发布锁内，没有把恢复改为重新选择。

同一 expiry 参数回归现在从冻结观察时刻起步，在 publisher 的 Skill get 返回后把时钟推进至真实 expires_at；预览和 canonical 记录保持原件。读取 `expiry-fix-r1/stdout.txt` 确认 **1通过／10.07秒**，日志 SHA256 `3f022534ccebb3b0231eb633a1e914050d511dc41faac60593e96bcdfc507f31`。该输入会击中旧顺序的缺口，因此不是重复实现的断言。新增 `skill_assets.versions(..., heads_only=True)` 沿原 owner 仅读 head；默认返回形状保持，未选择 Skill 不读其候选或事件。源码扩大 regression-r1 实际 **220通过／403.38秒**，身份为修前回归，不能替代修后最终安装回归。

修后本轴未发现新增实证 finding；上述窗口的代码修正与针对性证据已核。重新检查的三个文件 SHA256：

|文件|修后 SHA256|
|---|---|
|`src/ergora/task_context.py`|`2b28dd8f538d14db37d295d4bccf0419bdcb5faa83b2702aaa5bb84c83e61c55`|
|`src/ergora/skill_assets.py`|`e14b2ae3d9227220e9979cce711e16776e52329060c68003b027b939cad9e096`|
|`tests/test_native_six_stage.py`|`8ebe1f26f5bd8c36548d286c5071f5a3915b78b68e0e40dba7e0d464a04c276c`|

修前 install-r1 及自身模板原件继续保留历史身份，不作为修后验收。本轮当时待补的修后实际 CLI／HTTP、安装回归、直接 v7 准入反例与最终记录，已在下文分别补核；固定提交／远端 Ref／自己的 CI 与原独立补核继续保留为后续发布条件。

## 修后工件的已完成核验

对 install-r2 另行执行只读文件及 ZIP／CSV 核验，而非只引用 package-identity 的布尔结论：wheel SHA256 为 `3f677bcf50ffcb514c1a029ae9ca78857f12aaf4a72d5d32ecf17f25f79e1a21`；当前源码、wheel 与 installed **577件逐字一致**；wheel RECORD **585行**及 installed RECORD **590行**的 hash／size 逐行通过。通过 `git ls-tree -rz <baseline> src/ergora/data/reference` 比较，**283件参考 blob 和执行模式保持**。上述14件产品／schema／测试文件也与 install-r2 的 source 快照逐字相同。

已读取 self-review-r2-codex 的 `original-result.json` 与 `review.md`，原回复 decision 为 **approve**，原文明确仅 source-review，未执行测试，仍要求最终安装回归、CLI／HTTP与独立审查。该结果不是本 fresh-context 需求审查的替代，也不作为异后端成功或实际执行验收。

已读取 native-r2 的原 CLI argv／exit、四份 HTTP 请求记录与原响应。另行只读核对四份响应的 size／SHA 全匹配，CLI 与 HTTP preview 的 JSON 完全相同；初次 create 与 canonical 变更后的 resume-create 结果相同，show、持久 intent 和发布 envelope 一致，原 intent 的 canonical SHA 与已接受 preview SHA 相同。对原 SQLite 使用只读连接确认 canonical 记忆确已 deleted、同 digest 的 Skill head revision 已加一；旧 preview 返回 HTTP400。HTTP预览／show／resume分别返回200。cleanup 原记录确认服务线程停止、端口关闭。本旅程只核创建／观察／恢复，不把创建本身称为六阶段 start；完整七叶执行证据由材料旅程及最终安装 suite 保持。

native-r2 原 harness 完成七个 CLI 命令与四次 HTTP 后，最终错误字段断言误用 `detail`，实际接口返回 `error`，因此原运行 exit1／KeyError。只读续核另有一次把 Skill 发布父目录误认为 bundle 的断言失败；随后按 version document 的实际路径核对。已读取 continuation 源码与 result：原 mutation／CLI／HTTP 均未重跑，续核 mutation 为0，原失败保留；只读确认原 manifest／Skill bundle 已失、冻结读取仍成功、业务 Git status 原字节保持。这是组合旅程加只读续核通过，不称首 harness 无干预通过。

修后 install-r2 的 regression-r1 由原安装 Python 使用 `-I -m pytest -v --tb=short --durations=15`，执行 native_six_stage、task_budget、composition_tasks、composition_workers、task_inputs、task_evidence_index、skills_evaluation、architecture_boundaries、compatibility_baseline、windows 原十 suite。已读取 result 中实际 argv 与 exit0，以及完整 stdout：**229通过／6跳过／412.30秒**；六跳过均为原 Windows 限定项，没有以 Linux 结果代替 Windows 验收。

对本次最终安装的 `test_original_stages_receive_s0` 原件另行执行 `-I -S -B` 只读核验：intent 文件 SHA256 `d9962eee18104398ed180d56d20a7b24e5b8c8a0ae3a3c6002bb59a330a65474`，v11 标准库准入通过；七叶全部继承所选记忆，七份 materials 指针与 admission 相同，七份固定 prompt 与实际 invocation stdin 逐字相同，七份所选 Skill 附件 coverage 全为75,600／75,600B。九个原预算 owner 的 stopped 与 collection-stopped 均 cleanup_confirmed，未导入 SDK。该证据属于上列修后 wheel；早期 materials-r2 保留为历史证据。

## 最终本地终核

收到最终交付、合同、计划及[公开证据摘要](evidence/2026-11-14-task-context-selection.json)后，直接读取并逐件核对其 **164个私有原引用**，全部 size／SHA 匹配；再核 current-identity-r2 的14件产品／schema／测试，全部与当前文件相同。最终14文件 hash 映射按路径排序、以紧凑 JSON 编码后的 SHA256 为 `f02fd718391d9fe783b50e6f35571d9369dd9d5a5b9a21840c344b441beb4b86`，与上述安装、材料、恢复证据保持同一来源身份。除本审查报告外，本 reviewer 未写其他文件。

准入反例已直接读取原输入、两份 prepare-result 及原 worker stderr。原 v7 `selected-conflict` 在 `root/development/preparation` 拒绝同名 `preparation-evidence` 不同内容；`selected-capacity` 在原 `scope project` 拒绝完整材料超过 material_bytes。两原准备均 status failed／returncode1／cleanup_confirmed，compile scratch 消失，无 creation intent 或正式 task。精确 read 例另使用安装包只读 `inspect_manifest` 验证原静态父图可正常编译；其原 grant 不覆盖新版根的 selection.json URI，生产 `selected_manifest` 明确拒绝，派生临时树清空。read 证据仅认证该有效静态父图与生产选择 owner 的授权拒绝，不称精确 read 的原生六阶段执行。

准入 harness r2 的 graph 键错误发生在 prepare 前；r3 在已正确观察到产品 failed 后误向 aggregate response 查具体 worker 错误。续核先只读观察原 conflict 的准备／stderr，不重复该 prepare，再完成 capacity／read。连同上文 CLI／HTTP 的两次 harness 问题，失败与组合续核都按原始范围保存，没有把正常产品拒绝写成产品失败，也没有把首 harness 重标为无人干预通过。

最终自身模板也核到实际原件：15个完整文件块共288,364B的每块 size／SHA 与 packet-index 一致，并全部进入原实际 stdin；全部祖先资源同样在 stdin 中。13个产品／测试文件仍与当前源码一致，两份文档保存的是当时在途状态；仅 CLI help 文案未入该 packet，本独立审查已核其实际 diff。prompt／stdin SHA `68230712f1748039708549eb7c915001655b1efbfab2fede33a1cbec897c2091`，原 result SHA `5b0fc07c370c1fbff6f011c54e14a048390bb28760a69ea867de1f222d0bd158`，decision approve。维持原回复的 source-review、授权同后端回退边界，不推断模型质量、理解、GPU或测得性能改善。

最终交付与合同明确保留所有首轮失败、修前／修后身份、Windows平台跳过、静态 read 例范围、F10c／F10d与发布／CI的剩余条件；与实际源和原件相符。终核读取时文档身份：

|文件|终核读取 SHA256|
|---|---|
|`docs/plans/2026-11-14-task-context-selection.md`|`8dda2aa2fe3e87b795fdcf688d36bf9f50953db2dc0f3d63b3c6bb30e027b332`|
|`docs/delivery/2026-11-14-task-context-selection.md`|`d07e56c68797818d50ff920f7689a09c4b3c7dec8a923dcfe7b5a2f5c4cc2808`|
|`docs/delivery/evidence/2026-11-14-task-context-selection.json`|`3bd8714d242555800c818df1ba1864a022bfe25f1b045c4bfcfb4a78b5f5fd65`|

**需求轴最终本地结论：approve；新增或开放 finding 0。** 未自行重跑安装或昂贵 suite，结论基于已检查的源码、邻近生产调用者、逐件原件与上述只读离线验证。固定发布与本片 CI 发生后才可作相应补核；本地终核不等于发布完成。

## 固定发布身份补核

已只读检查固定候选 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9` 的 Git 对象，唯一父为原基线 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`。提交的29个变更 blob 与 `static-final-r1.json` 清单完全对应，每件原 Git 内容的 size／SHA256 均匹配。F10a的发布／CI文档补记仍属前片，不用来替代本片验证。

已读 commit-r1／push-r1／ref-r1 三份原记录：均 exit0、候选完整 SHA 相同，push 为普通 `HEAD:refs/heads/refactor/architecture-foundations`，保存的原 `ls-remote` 完整 Ref 精确指向上述候选。本补核未联网或再次推送；远端结论限于该原查询时刻。

固定候选树的577产品文件与当前源码、r2构建快照及安装件逐字一致；参考树与唯一父完全相同，原283文件边界保持。原14件源码／schema／测试身份及 r2 wheel `3f677bcf50ffcb514c1a029ae9ca78857f12aaf4a72d5d32ecf17f25f79e1a21` 的本地审查结论继续适用，未重跑测试。

固定提交内公开证据 JSON 为 **164个原引用**，blob SHA256 `392889c907a94c38a1850b03bdee6a1ce08f9f642b7508964480826d3cd407ac`；当时 publication=pending。发布后的工作树补充为 **168个原引用**，仅新增 static-final-r1／commit-r1／push-r1／ref-r1 四份发布原件，原164项元数据保持；已直接核全部168件 size／SHA256。工作树补充不冒称已包含于固定提交。

**固定发布身份补核：approve；新增／开放 finding 0。** 本片自己的 CI 仍处发现阶段，未作任何终态主张；CI原件到齐后另补。按本次范围，本 reviewer 至此停止写入。
