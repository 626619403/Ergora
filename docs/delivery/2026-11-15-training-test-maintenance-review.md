# Q5.2a／B3.3c2 Windows 测试接续独立审查

日期：2026-11-15。审查者为 fresh-context 独立 agent `training_test_maintenance_audit`。收到原始要求、固定基线／全文范围和验收原件路径后，先检查规则、源码差异与真实消费者，再读取作者交付记录和自身模板结果；未继承实施对话，也未将旧 reviewer 或模型的 approve 当作本次结论。

本次只读源码、邻接调用、文档及私有原件，唯一写入为本报告。遵循根／tests 的 AGENTS、[脚本和检查协议](../architecture/component-change-protocols.md#脚本和检查)、maintainable-project-delivery 的 independent-review，以及 ergora-codebase-quality 的 repository-style／module-design／test-seams。没有安装、重建、运行 pytest／服务／训练、提交／推送或发起网络请求。

## 两轴结论与交付边界

|轴|最终本地结论|开放 finding|
|---|---|---|
|需求符合|approve：P2 提前平台标记、P3 文字断言清理及 Windows 历史夹具修复符合本片要求；原恢复／回收／身份保护保留|0|
|维护性|approve：变更留在已有测试／夹具和记录中，复用原 SDK-free reader；没有产品接口、包装层、重复 CI 或新增测试框架|0|

只发现一项公开范围数量记账的 P3，作者已按固定清单修正，本 reviewer 已重读关闭，见下文。未发现需要修改最终测试源码的实证缺陷。

|对象|本次认证范围／状态|
|---|---|
|固定源码与本地记录|本报告给出两轴 approve；认证的是下列固定源码、实际原件及已补核的文档状态|
|产品安装|沿用原 r6 SDK 非 editable 安装；本次直接核其清单内 652 份当前源码与安装文件 bytes／长度／SHA 相同；未产生新构建或新安装验收|
|本片精确发布|未提交／推送，未核新 commit tree 或远端 Ref，仍待同片续核|
|本片自己的真实 Windows／适用 CI|尚无修复提交对应的终态原件，仍待；Linux 和局部入口替身不替代此项|
|旧 ac86043 自己的 CI|已直接核原件为 failure，七 job 成功、Windows regression 失败；不会改记为成功|

因此可以继续本片的精确发布与自己的 CI 验证，尚不能宣布 CI 接续闭合或开始后继控制器产品实施。真实 GPU／业务训练／质量／性能收益、自动循环和其他外部能力不在本次验收内；v3 kernel 专家路径保持。

## 固定输入与实际范围

baseline／检查时 HEAD 均为 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`，分支 `refactor/architecture-foundations`。固定输入位于 ignored `training-test-maintenance/product-source-r2/`：

- `scope.json`：12 件完整文件、369,901B，SHA256 `8e451fa5c7d81121f53d6a05a1f51ecd58f0e136d200c7850ef9fd4ff19c4cbc`；逐件核长度／SHA 全部匹配。
- `changes.diff`：完整 tracked 差异，SHA256 `cc9eb721dc146487494213339beeaa5ef1ce8d51496d529f800b875ba26210bc`。新文件另有全文，未只审 tracked diff。
- 唯一非文档为 [test_training_submission.py](../../tests/test_training_submission.py)：旧 Git blob 全文 SHA256 `1b9257535ceea369696ce49240287acedc69f0d0c499ce994b614f8810f2fdaf`；固定最终及当前全文 SHA256 `7e268543d7e863d4abb9a6df535069144e592eee5d87cee18f085f4ce31317cc`，117,048B。

其余 11 件 Markdown 为：总 `docs/PLAN.md`；本片 plan／delivery；既有 managed-execution plan／delivery／review；controller plan／contracts plan／delivery／plan-review／contracts-review 五件。已读完整 tracked 文档差异、本片两份记录，以及 controller 五件的范围／状态／引用；后者作为已独立审过的设计输入核范围与交接，不重审获批设计合同或 reviewer 本身。

固定输入之后，作者只在五件文档补自身模板结果、准确的 CI 失败状态及范围数量。已逐项比较这些差异；没有改变具体控制器合同、产品或测试行为，仍明确“尚未实现”。补核身份如下，后续发布／CI 状态追加应另记身份：

|文档|本次补核 SHA256|
|---|---|
|`docs/PLAN.md`|`bf425b0ddd965ef513af4ab7429395e1a903b87222d67ea75e80ec26cfb035e0`|
|`docs/delivery/2026-11-15-training-test-maintenance.md`|`37344f71f684160840db2d460b7cbf491bcd2d44b24bd4ecebe55d0c86ec0568`|
|`docs/delivery/2026-11-15-training-cycle-controller.md`|`fb97cb5d75b9e99385cd587185bbfc7e99c4bbab8a5a3b17883b37bd04cb6164`|
|`docs/plans/2026-11-15-training-cycle-controller.md`|`df46c8949cd9784e2f0738747df65ff536ce19922672de1663df6e6c46548a77`|
|`docs/plans/2026-11-15-training-cycle-controller-contracts.md`|`42bd4bc177b023149d6d44faf9d43b14ff357df1264b508bef07af672b084133`|

独立重算 `src`／`scripts`／`.github`／`pyproject.toml` 相对 baseline 的 diff 为零；固定测试与当前工作树相同。未修改业务项目、283 冻结参考、CI 矩阵或 kernel 模板。

## 源码与测试价值判断

**提前 skip 保留原平台行为。** 测试第 205 行的 `service(prepared, ...)` 原本在函数体第一项检查中对所有非 Linux 平台 skip，但依赖 `prepared → experiments → registration` 已执行。独立 AST 计数为 28 个 service 消费函数，其中 3 个已有提前标记、25 个未标记；本片正好给这 25 个增加已有形式的平台标记。第 295 行的额外函数原本也有相同 body skip，现在在 setup 前标记。没有整文件 skip，历史读取和两个既有可移植读取／冲突节点仍无新增平台标记。

独立正规化 AST 后，除这 26 个精确 `sys.platform != 'linux'` 装饰器、下述一个嵌套断言和 `historical_execution` 夹具外，其余 AST 完全相同。所有参数、函数和原 Linux 状态转换保留。原前后收集及最终冻结副本收集的 84 个 nodeid，去除副本目录前缀后逐项相同。无需新增标记 helper、CI job 或参数矩阵。

**删除文字断言没有删除缺损 stopped 风险。** 测试第 1297 行仍通过真实 `training_cycles.start` 和原预算 owner／phase 生命周期运行 `phase-stopped-incomplete`。邻接 fixture `tests/fixtures/training_budget_client.py:214` 仍先调用原 `processes.run` 完成回收，再写精确 supervisor 身份 marker 并返回空 process。原 `_BudgetPhase.receive` 仍在拥有完整帧的边界拒绝缺项。测试仍读取 marker、核同 PID／start_ticks／boot_id 已停止、重读原 `resume_start`、核相同 fence SHA、要求无 executor stop 确认及原件不改写，并要求 monitor 为 unknown／stopped false。

`assert_budget_process_stopped` 若原身份仍活着会精确清理后抛 AssertionError，并非“清理后自动通过”。因此剩余断言能够揭露错误接受缺损停止帧、错误声称已停止或错误恢复其他 fence；被删的完整 `monitor.reason` 句子只重复内部诊断措辞。原接缝保留，不能据此再删故障参数或改为孤立 parser 测试。

**历史夹具替换的边界正确。** 第 42–105 行的夹具在变更前就写合成 budget／owner／PID／launch／ack／stopped、没有可用活授权。本次仅移除依赖 Linux-only prepare 的初始取样，按既有 `_Submission.identity` 的字段构造旧 intent，并从 `reference.training_files` 取得完整 observation。`reference.py:429` 经独立 `-P -S` reader 读取原 registry，未调用当前 native prepare 或引入 SDK。注册夹具提供的 definition.execution 与原注册 execution 相同；operation_id 是合法固定 32 位十六进制合成身份。

后续 start attempt／receipt、owner capability、native request、request／launch／attempt／ack／stopped 及其摘要关系均沿原代码保留。真实消费者仍是 `training.execution → reference.training_execution → ExecutionRecords.load/observe`：校验完整 start／receipt、native spec／runner、原 request、owner 授权摘要、launch、进程身份、ack、原观察路径及 UTC stopped。没有把读取改成直接返回 fixture 预期，也没有创建 execution 权限。原 prepare／fence／禁止无 attempt dispatch 的 Linux 接缝仍由第 295 行等原测试覆盖；历史 reader 不应为了构造合成旧档案先获得新的执行准入。

缺安装的 CLI 检查、文件与数据库不改写、`execution_authorized=False`、`runtime_status=not_queried` 和 success unknown 均保留。numeric-identity／native-runner／foreign-ack／duplicate／fifo 五种坏链参数未删；Linux 下同文件 sync／reread 和初始化 read-lock 两个独特接缝也保留。Windows 上 FIFO 的 body skip 仍只跳 FIFO 自身；修复后能到达该分支，实际 Windows 路径／文件／目录同步语义留待自己的 CI。

## 直接核实的原件与证明范围

验收根为 ignored `training-test-maintenance/`。本 reviewer 直接解析了实际 JSON、JUnit、stdout／stderr 和驱动源码，并核前后测试副本及邻接 fixture 与当前相同；下列不是本 reviewer 新运行的测试。

|原件|实际结果|能证明的范围|
|---|---|---|
|`static-and-setup-r1.json`、`q5_windows_view.py`、`windows-view-before-r2.json`／`windows-view-after.json`|相同 41 个节点 skip；三昂贵 fixture 进入 123→0，exit 0|只改变目标测试模块 sys.platform 的受控 pytest setup；不改变产品模块平台，不是 Windows 运行或 Windows 性能测量|
|`linux-regression.xml`|原 `phase-stopped-incomplete` 1 passed，29.847 秒|原断言清理范围的真实 Linux 生命周期；未转授为后加历史夹具的验收|
|`portable-regression.xml`|原读取／冲突竞态 2 passed，2.006 秒|原两个可移植节点仍通过；同样属于原范围|
|`history-linux-r2.xml`、`fixture-validation-r2.json`|最终测试副本历史／durability／owner 共 8 passed、0 skip／error／failure，10.077 秒|最终历史夹具及八个 Linux 接缝；76 deselected|
|`prepare-guard-before-r3.xml`／`after-r3.xml`、两 observation JSON|旧六节点均为 setup error；新相同六节点 6 passed、7.177 秒；prepare_calls 6→0|只在原入口注入 prepare 拒绝；其余原 reader／坏链断言真实执行，不模拟 Windows 文件语义|
|`collection-final-r3.stdout`、`collection-links-r3.json`|最终 84 nodeid 与原逐项同一；独立重算 237 个本地相对链接目标全部存在|收集及链接目标可达；不认证锚点或外部 URL|

关键 JUnit SHA256：history `68ee816419b7c29c8dcddcd59d58ec667f3ad8ec18b86e9c55340bce117c9d98`；guard-before `caaf783e3b12f4a8f93b5dc89439faca51d2f6ddf2898664a919af081e374331`；guard-after `c354be018a18d576bf100312bfb9c19eb85d4a883ced8dcf24437ee532084ccb`。原 r2 guard 两次 exit 4 均因隔离 Python 找不到 plugin，未运行测试；最终收集 r2 也因错误解析到 base Python 而未收集。原 stderr 均保留，r3 是独立的有效记录，未把驱动失败改记为产品成功。

自身原模板结果也已直接核：`ergora-structure-review@1.0.0`、授权 Codex 回退，run `970de714d493478a92c78a903daad71e`，26.531936 秒、需求／维护性 approve。16 份全文的长度／SHA 与 scope 相符、全部 bytes 位于实际 task，完整 task 及三份资源正文位于 prompt，prompt 与实际 stdin 逐字相同。input digest `1a53911062159a05bd495dd1c93164efffb0fe5b9863fe2e0b5829c0ee58b0ef`；原 result SHA256 `bb7482ebd94db05b51e45399989e55fb62fd8cef22bb65b1a1a66facc79301e5`。这认证自身模板消费供应文本的范围，不替代本次原件审查或真实 Windows，也不构成异后端证明。

## 原 ac86043 官方 CI 的独立核验

直接读取 `training-managed-execution/ci-r1/20261115T064300157007Z-runs.json`／`-jobs.json` 和 `20261115T064400163955Z-windows-annotations.json`，并逐项核各自 HTTP metadata 为官方 URL、HTTP 200、长度／SHA 相符：

|原件|bytes／SHA256|
|---|---|
|runs|11,992／`c76f65a934f6d5d4525940f5cb7d2afe7f6f7b6d549aac1a8373e5aed5300618`|
|jobs|21,121／`a479048078d894a9efa860129474c41d1bf4dc8e87fe44cfca83d80921ddd9d5`|
|Windows annotations|4,664／`12c87975096bec1ff24cbbac422719256aa812d9ea4cb70cffdc0fc167f2f662`|

run 为 [Portability 43684533043](https://github.com/626619403/Ergora/actions/runs/43684533043)，attempt 1、push、原分支和完整 ac86043 SHA，completed／failure，updated_at `2026-11-15T06:42:52Z`。八 job 全部有同一 run／attempt／head SHA。按固定 workflow 重算 30 必要步骤，29 success／1 failure；唯一失败为 Windows job `132722147582` 的 Native application regression，Windows 的 build／reference／PowerShell／upload 成功。

官方注释截取列出历史 SDK-free 一项和五个 inconsistent-original-chain 参数，全为 prepare 的非 Linux 拒绝；汇总为 1179 passed／876 skipped／6 errors／16 subtests、1557.34 秒。直接读固定旧 Git blob 的夹具第 49 行及 `reference.py:496` 的平台 guard，与这六个 setup error 相符；FIFO 的 body skip 当时也尚未到达。这里只取得官方注释截取和 REST 原件，未声称拥有完整受鉴权 job log／XML／artifact。旧候选原失败与 [原 c2 终核](2026-11-15-training-managed-execution-review.md) 保持自己的身份。

## Finding 与剩余验收

**R1（P3，已关闭）：范围文件数记账不一致。** [本片交付记录](2026-11-15-training-test-maintenance.md)第 40 行附近曾把本次 Q4.2c 文档写为六份，末段又把总计 12 件称为 12 份文档。固定清单实际为 1 份测试＋11 份 Markdown，其中 Q4.2c 五份。交接者按错误数量选取材料可能误判缺件。最小修正是按清单改为“五份”及“当前变更文档”，不扩大设计或源码审查。作者已作这两项修正，本 reviewer 已直接重读并核上述最终 SHA，关闭 R1。

源码范围内无其他 finding。仍需按本片最终实际范围普通提交／推送，核 commit tree 和完整远端 Ref，再取得该精确候选自己的适用 CI，尤其真实 Windows 历史读取与 setup 结果，并由本 reviewer 同片续核。未重跑无变化的完整 submission suite，没有新的 Windows 耗时／收益测量；这些限制已在计划与交付中如实分列，不阻止当前固定源码的本地两轴 approve，也不关闭发布／CI 门禁。

## 实际暂存范围 r1：固定待发布两轴 approve

同片续核时 HEAD 仍为 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`，原分支保持。已直接从 Git index 读取实际 staged 内容、完整 blob OID 与 mode，不只读取作者的清单。实际范围恰好为前述 12 件加本报告，共 13 件、全部普通 `100644` 文件；没有其他 unstaged 或 untracked 公开文件。检查时 13 个 staged blob 的完整 bytes 均等于工作树及 `publication-staged-r1.json`，清单没有漏件／重件。

`publication-staged-r1.json` 为 35,183B，SHA256 `e5cdb5f40cbe1fd64dc31a848143980d3ed2f2e336e90fbdbd114e7ecde44f62`；留存的完整 `staged-r1.diff` 为 136,912B，SHA256 `3c148066e3480987c09d2c471ca05caed7b2224a69d33654643f08ba81bf1724`，与实时 `git diff --cached --binary` 逐字相同。独立执行完整 cached diff-check 通过，直接解析暂存测试的 AST，并逐个经 Git index 核 242 个相对引用目标存在。此处仍只认证本地目标，不认证锚点或外部 URL。

唯一测试的 staged blob 为 `a6caa1d056a6242676f1836adf8a735faddc33c4`，全文 SHA 与前述最终测试相同。其余具体合同、设计报告和既有 c2 状态与本次已审身份相同；`src`／`scripts`／`.github`／`pyproject.toml` 的 cached diff 仍为空。没有新增产品、CI、依赖或业务项目变更，不因暂存重新转授安装或运行结论。

相对本地审查末次身份，只有 `docs/PLAN.md` 和本片 delivery 追加／替换“独立本地 approve、R1 已关、进入发布／CI 门禁”的状态记账。已读两处新增文字并独立复算：还原 PLAN 的这一状态句后，SHA 精确回到本报告表内的 `bf425b0…`；移除 delivery 新末节及其分隔空行后，SHA 精确回到 `37344f71…`。没有夹带合同／源码变化。待发布的两份文档身份分别为：

|文档|staged blob／SHA256|
|---|---|
|`docs/PLAN.md`|`84985c21c4b42ea0db562cbb1c1c5437aae8caea`／`d99ab053e5ef1210cd5f303c741ecf7a6359bb3250fd21e3cda6b481bd33653f`|
|`docs/delivery/2026-11-15-training-test-maintenance.md`|`9dc776d1651adba1a49316387e8befef7a86875c`／`21084f8b12e197aeea534903f1a001db7df69118af14e56b986993b9d031901d`|

此 staged 快照中的本报告为原本地全文 14,276B／SHA256 `449dd695f129e24f69763b0a31984dea36cc2a85004ff20d4dd35f4613b711f7`、blob `26e5f9a65b12db105f77f5998b524dd87424005e`，已在追加本节前独立核实。本节只追加原片续核，没有改写该原文前缀，也没有修改暂存区；下一步仅需暂存本报告追加字节，其余 12 个 blob 应保持上述清单身份。

另直接读留存的 `pre-publication-ref-r1.json`、stdout／stderr：原 `git ls-remote --exit-code` 退出 0，stdout 是完整 ac86043 加原分支 Ref，stderr 空。stdout SHA256 为 `2f3829f22ea48505368ecef3b886394f0bf556354c2477f0d2e6223ed77e40a6`。它只证明留存的发布前观察仍指向旧 HEAD，本 reviewer 没有发起新网络请求，也不把它称为修复提交的远端认证。

**固定待发布范围需求／维护性两轴均 approve，开放 0／0，R1 关闭保持。** 这是实际暂存范围和状态记账续核；新 commit tree、普通 push 后的完整远端 Ref、该精确候选自己的 CI 终态及真实 Windows 读取仍待同片核实。原 ac86043 的 Windows 失败、所有本地／安装证明范围和后继控制器实施门禁保持，不提前记作精确交付闭合。
