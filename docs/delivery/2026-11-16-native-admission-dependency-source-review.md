# Native admission source-v2：独立源码审查

2026-11-16。Reviewer：fresh-context 独立代理 `native_admission_v2_source_review`，未参与设计或实施。按根／src／tests AGENTS、组件变更协议、maintainable-project-delivery independent-review 及 ergora-codebase-quality module-design／test-seams／repository-style 审查。唯一写入为本报告；未运行测试、业务 probe、安装、服务或模型，未访问网络、commit 或 push。

**最新状态：最终 r5 移植／固定候选 `bc58be6781d35e7e4fbd54ad997df8a4743428a8` 的有限源码两轴 approve，本片开放 finding 0。** 已核 M5 r7 当前实际intent及最后门接线保持，R1 平台标记修正保持。以下首审与同片复核快照保留原原因和身份；最终身份及未验边界见末节。新安装与完整 hook 无 SDK mandatory 不因此闭合。

|审查轴|结论|本切片开放 finding|
|---|---|---|
|需求符合性|**request-changes，仅因 R1 新增测试节点的平台边界**；五产品文件的静态实现未发现阻断|1 项 P2|
|结构／维护性|**request-changes，修 R1 后复核**；未发现额外模块设计或 owner 问题|1 项 P2，与上行同一项|

此结论只针对以下精确 native-only 源码切片。不是 M5 全片通过、D3 非editable安装验收、M6／schema3 效果开放或真实两轮／GPU／训练质量验收。M5 基线自身最后门的新发现仍由原 owner 处理，见后文。

## 实核基线与范围

源码树为 `.ergora/worktrees/native-admission-dependency-v2`，其 Git HEAD 仍是 `a1ff3389c004fbe19ed2529743980071d395b4d1`，但已同步 M5 r3／r4。真正 native-only 比较基线是 **`68f3241695f5de1fdc188609db612c1d30434edf`**。本审以此 baseline 的实际 diff 与两个新资源为准，没有把 M5 的 Execution／解释器门／source-sync 出生配置算作本切片。

审查时逐项读回冻结清单的 bytes／SHA／执行位：**11 个 changed、2019 个 all tracked+untracked、665 个 product 输入，均无不符**。

|冻结原件，均在 `.ergora/checks/native-admission-dependency-v2/`|bytes|raw SHA256|
|---|---:|---|
|`native-only-r3.patch`|43950|`912a967995d5e764272e35346bd27f9474934675d2054b9d92fe7bddec66394e`|
|`all-tracked-untracked-inputs-r3.json`|421972|`18cd48672d4a1b6404f9b3c10259b7821978570bb0d166efa2d9e3b2948932e3`|
|`product-inputs-r3.json`|145658|`873807d898255bca6b7890b64935ece645913e98b2293b63c587c5b55df7b467`|

11 文件为五产品 `src/ergora/cli.py`、`reference.py`、`training_execution_protocol.py`、`data/native-runtime/training-executor-admission-v2.json`／`.patch`；用户手册 `docs/TRAINING.md`；既有 fixture `tests/fixtures/training_executor_client.py`；既有 `test_reference.py`、`test_training_runtime.py`、`test_training_submission.py`、`test_training_cycle_controller.py`。逐文件 raw 身份见同目录 `source-freeze-r3.json`。

独立 stdlib 静态读核确认 manifest 的 **283 项均存在、非 symlink 且 SHA 匹配**。manifest SHA 仍 `1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`；v1 JSON／patch 与 baseline 逐字相同，SHA 分别 `d7e2b706599c6fcbb874a1a1dbec8b9875df817dc71ffa455801e48c240c2c55`／`45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`。将 v2 unified patch 仅在内存按每条原 context／删除行重构，executor 得到原 v1 相同的 **9013B／`feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`**；training 得到 16433B／`c1a42acd91c3f320fe4c2c3d26728de7d0abc246474fad444be50c5356f5e086`。原 training 与所得 v2 AST 去除 client import 后相同，差异确实只是顶层 import 下沉到两处分支。`reference_training_execution.py` 与 baseline 逐字相同，`native_main` AST 亦相同。

## 开放 finding

### R1 — P2：新增 native v2 controller 节点在 Windows 进入不支持的 prepare fixture

- **位置：**源码树 `tests/test_training_cycle_controller.py:1591`；真实 fixture 为 `tests/test_training_runtime.py:20`，进入 `reference.py:157` 的 Linux-only source preparation。
- **可达场景：**本片将原测试参数从 `['managed']` 增为 `['managed', 'managed-v2']`，两参数均无 skip；测试自身也无平台标记。Windows CI 的 `.github/workflows/portability.yml:64` 执行 `scripts/ci/run.py --group all`，包含整个 `tests/`；CI plugin 未替这些节点作平台过滤。新增 `managed-v2` 节点先执行 `installation` fixture，直接调用 `reference.prepare_training`，其 `sys.platform != 'linux'` 分支必然抛 ValueError，尚未进入测试或 controller fixture 主体。
- **后果与归属：**新增 v2 节点给 Windows 全量 suite 增加 setup error。原 `managed` 节点已有同类基线缺口，不把它伪称本片引入；但新增 Linux-only 节点仍须明确平台边界。本片已正确给 history 的 managed-v2 参数和 alias 反例标 Linux，这处未覆盖。
- **最小修订：**给整个只运行 native callback 的既有测试加 `@pytest.mark.skipif(sys.platform != 'linux', ...)`，或至少像 history 一样给新增 managed-v2 参数加标记；优先整项标记以真实表达这条测试的支持范围。保持 Linux 两版的原 callback 与 completed-read 断言。
- **复核：**静态确认 skip 在 fixture 执行前生效、Linux 两节点仍被收集；按改动范围记录相关 Linux 节点检查。没有运行 Windows 就继续明示 Windows 未验。本审没有通过改写 platform 或执行 probe 制造实测失败，以上是完整源码调用链推导。

## 需求与真实消费者核查

|边界|源码判断与可达行为|
|---|---|
|首次 executor 导入与 SDK owner|原链是 immutable `training_executor.py:13 → training.py:20 → perf_temporal/client.py:10`。v2 在原 training CLI 的 run-local、approve 各自使用前导入原 `load_experiment`；没有复制 parser／Binding／loader，没有新 adapter。core／sandbox／perfctl／adapter／models 及两包 init 的顶层闭包只需 stdlib／原本地模块；executor 的 MLflow 仍在 track 内。准入无 SDK 不等于 runner／tracking／控制面无依赖。|
|reference 选择与所有消费者|`reference.py:93` 只按封闭 v1/v2 的 protocol_id 选 bundled raw，再逐字比较；`_training_overrides:110` 保留 lstat、普通文件、O_NOFOLLOW／O_NONBLOCK、65536B 和 manifest 原核验。`prepare_training:155` 必须显式版本，并核声明 protocol_id 与所选名相同，防完整 v1 pair 被误装到 v2 名下。CLI `:170,922` 委托此 owner；services／registrations／tasks／training、worker `_training_process`／main／cycle_main 均继续消费同一 validate_installation，没有旁路解析。|
|混搭、alias 与 legacy|逐字声明拒格式化、额外／重复字段、空、未知版本；完整安装核验按该声明 overrides，v1/v2 training 错配失败。删除 patched 安装 descriptor 不能回退成原 Python identity。无 descriptor 的 legacy 仍只按原 Python 子集／training 规则核验，未扩大到 requirements 或全部非 Python 文件。没有 mtime 替代 raw SHA。|
|出生 capability|`protocol.py:951` 在完整安装核验后读取并严格选择 descriptor raw，再围绕一次完整安装核验重读同 raw，绑定原声明与 SHA；两合法版本切换及任意未验证 raw 不被当作可随意采值。capability 只由 `BudgetedStart.own:517` 在原锁内首次生成；已有 owner 拒绝重启，未增加升级／补 pin 路径。|
|每版本精确25键|`GATE_SOURCE_PROTOCOLS:51` 保留 v1 表，v2 只换最后 descriptor key。`_capability:896` 从出生 admission_protocol 选单表，核七字段、精确键集和全部 digest；24／26 项、混表／未知版本拒绝。`validate_sources:974` 核原 pin→283→当前完整安装→descriptor版本及raw SHA→重核 pin→原 native_python.is_file 最后门。四 measurement 源表未动。|
|历史与缺失安装|`owner_record:914` 对 owner1、owner2 null 沿原 shape；有 capability 只检查保存形状，不访问所选安装或比当前源码。`ExecutionRecords.load:1321` 保留这种离线行为。`reference.training_execution:480` 先以原 `-P -S` reader 读 history，再单独查 sources 并报告不可用；没有因当前安装缺失吞掉已读记录。旧 v1 pin 在新源码上 live 被拒绝，不隐式解释成 v2。|
|原入口、锁、记录及 result|`native_main:1693` 的正常 sys.prefix、core ROOT／PYTHON／STATE／CONFIG 身份门保持。v2 executor 与 v1逐字相同，因此 result 早读仍在 executor.lock 内并先于 request／admit；原 attempt-before-send、ack同步、父共享 permit、clock、原唯一 reaper 与 records 未搬动。原 Execution 文件及 native_main AST 同 baseline；没有修改六阶段／Workflow／candidate 或扩大 schema3 可执行性。早读仍受原 native 入口身份门约束。|

## 维护性与测试价值

新增两个资源是不可变版本资产，不是新 runtime 框架。`reference._training_descriptor` 有 reference 安装验证和 protocol 出生／live 校验两个生产模块消费者，隐藏相同原 raw 选择义务，位置合理。`protocol._capability` 在 owner/history 与 live 两个真实边界复用同一保存形状规则；它不读 SDK／安装，不补字段，作为本域私有算法合理。封闭版本表是身份校验的数据分支，不需要为两版不可变资源建立 ABC／插件分派。

新增 guard 各有可达输入：声明 filename alias、描述符变更窗口、持久 capability 版本混搭。它们位于 reference 来源身份与 protocol 持久身份边界；没有新增配置限制、无关断言或恢复 fallback。descriptor raw 围绕安装核验的再读用于出生身份，不能由 JSON protocol_id 或 mtime 代替。

新增测试均复用既有文件／fixture，无新 CI job，记录 collector 相对 M5 r4 从323到334节点。identity／25键／旧 shape 测试保护可静默错认；两 CLI 测试保留原 client loader／Experiment.validate，只替 approve 的远程 query/send 叶子；不是用 fake loader 证明语义。native fixture 将拒导入 hook 放在首次 executor import 前，并实际调用 native_main。两版容量节点会重复原 H 流程，但 v2 的 owner／capability 与 native callback 需新出生来源，且约10MB完整链上的隐藏导入是原缺口；此处新增集成成本有明确保护对象。未要求重跑无变化全量 M5 矩阵。R1 是此接缝尚需补齐的平台标记。

`docs/TRAINING.md:82` 的显式 v2 命令、v1 SDK 牵引、准备不装依赖／不授执行权、新目录／旧 owner 不升级说明与实现一致。原 `data/**/*` 打包规则覆盖两个新资源；这仅是静态判断，未构建 wheel。

## 证据、基线依赖与未验范围

只读核过现有 JUnit／结果原件：`source-final-r2.xml` **25 tests、0 failure/error/skip、119.993s**，其中 reference17、原 CLI2、submission history／容量4、controller closed／completed2；`platform-scope-r1.xml` **3 tests、0 failure/error/skip、4.777s**。后者仅 Linux 上的相关标记及 M5 配置同步检查。665产品输入未变，不把它称为新增 Windows 成绩。

读取 source-final-r2 保存的 native-reader 结果并与测试源码接缝对应：v2 所选无 SDK venv 正常 `-P`、先装拒 State／schema／YAML／Temporal hook，真实 native_main 在9,999,999B／10,000,000B前驱后到原 schema3 闭门，`executor_sdk_loaded=false`；纯 `-P -S` 认证另记。v1 同样拒 SDK 时 returncode1，原 executor→training→client→Temporal traceback 保留；显式附 SDK site 的原路径到同一闭门且 loaded=true。这证明已记录的源码入口探索，**不证明新的非editable core／SDK 安装、已安装资源闭包或 schema3 后续 effect**。

M5 r4 的开放问题不被本审关闭。当前 `native_main.active` 在 `protocol.py:1742` 核 clock 后才调用 `parent.check:1746`，后者经 `:1045,1068` 读取 authorization，可阻塞；父任务另提供 M5 自身模板发现的 `_round_previous` 后最终 SDK 等待期间 earliest predecessor 漂移问题，源码位于未改的 `reference_training_worker.py:1175,1281` 及后续 gate。两项属于原 M5 owner 的最后门与实证复核，尚无 r5 修后证据进入本次冻结。**本审没有将“不改变 baseline 时序”转写为“baseline 最后时序已正确”。** 最终 native 候选必须同步 M5 必要修复并重核受影响证据／来源 pin，不能直接继承本 r3 冻结的源码批准或测试成绩。

报告完成时父任务告知 M5 r4 新安装受影响组已18 passed／424.83s；本审未独立读取该批原件，且它属于 M5 r4，不能转授本 native-v2 片或尚未冻结的 r5。M5 原 R1 完整 hook 无 SDK mandatory 仍须由最终 native 候选的新安装实证闭合，源码探索与本报告均不替代它。

仍待：R1 修正及同片复核；同步 M5 最终修复；固定最终候选后新的非editable core／SDK 安装、实际 site-packages 与665产品／新增资源完整身份、所选无SDKvenv正常入口验收、自身原模板与最终终核、候选自己的必要CI。未运行 Windows、真实 GPU／训练质量、正式V2／producer、schema3 attempt／ack后完整正向或真实两轮。此次评审没有修改这些责任边界。

## 同片 R1 修正与复核

2026-11-16，同一 reviewer 只读复核。实施仅在原 `tests/test_training_cycle_controller.py:1591` 增加一行：

```python
@pytest.mark.skipif(sys.platform != 'linux', reason='Managed native callback requires Linux')
```

标记位于原函数及两层 parametrization 前，对 managed／managed-v2 两节点共同生效；pytest 在非 Linux 的 fixture setup 前跳过，Linux 原 callback 与 completed-read 路径不变。最小修订表达了整个既有测试的原 native 平台边界，未更改产品或测试断言。

独立删除这唯一一行后，文件恢复为首审冻结的 **96046B／`2db70e5b8ac53e6ae89f14f38705132c0932b950f306a86936a6954ac13225a0`**；修后为 **96140B／`40dce90bd77332c1d24dd44b6ec3a3f9bc57626ecb15bcc0cc810ba1aa8aba8d`**。重新逐项核2019输入仅该文件不同，665产品输入全部保持 r3 原 bytes／SHA／执行位，M5 后继 delta 未混入本次复核。逆变换记录 `linux-native-callback-mark-r1.json` SHA 为 `3507b7fcb003a21115efc977782f1b88798fa1e7a8821b7036a5e7d4ec45a93b`。

只读核同前缀 command／stdout／stderr／result／JUnit：命令只选原函数，实际 cwd 为所审源码树；result exit_code0、driver9.8783s，stdout **2 passed／9.49s**，JUnit **2 tests、0 failure/error/skip、9.491s**，确为原 managed 与新增 managed-v2 两节点，stderr为空。JUnit SHA `9c153f19f24382824aa5bf2b5163b0858295c3afb27532994de2fd7398638b3e`。reviewer 本轮未运行任何测试或 probe；上述是对实施方实际运行原件的核对。

**R1 已关闭。本片需求符合性／结构维护性两轴 approve，开放 finding 0，仅覆盖初审 r3 的五产品／相关源码，加这唯一单行测试修正。** Windows 未实际运行，不把平台 skip 的静态正确性称为 Windows 执行验收。前节 M5 最后时序的待修／r5 未冻结、M5 原 R1 完整hook无SDKmandatory、最终 native 候选新非editable core／SDK 安装、模板／终核及其余未验责任全部保持开放；新的 M5 产品 delta 需要重核实际受影响证据，不继承本切片有限源码结论。

## 最终 r4 移植身份与接线复核

2026-11-16，同一 reviewer 继续只读复核，未重跑测试、probe、安装或模型。原开发树精确接入 M5 r4→r6 delta，其原件 `m5-g-r4-to-r6.patch` 为13384B，SHA `0c0c5a789bed01e6adf572e53857cec5f897215a2a3a8be8c2f4bf8ba513a9ee`；开发树 HEAD 仍为 a1ff338。另核固定树 `.ergora/worktrees/native-admission-dependency-v2-fixed`，HEAD **`b3e734bad3d5a0ba01f69a61fd9328e0ab637f33`**，唯一父 **`f6722141cfa9ed885993360161c004e47e8df3a5`**（M5 r6），working tree干净。

|最终冻结原件，同一私有 checks 目录|bytes|raw SHA256|
|---|---:|---|
|`native-only-r4.patch`|44045|`a0abc3ba3a44055f125284bf693b8f7449b56d38137456ca90de5abda46db4a6`|
|`source-freeze-r4.json`|2982|`8b8e830c16cc0893bcb263984f03fe68913c528ecd1cc3437cb15bd82df7b9b6`|
|`all-tracked-untracked-inputs-r4.json`|421972|`5d6058ef55b6f18f4ab9d0003594b82bcd1c6f1d99152f99d150766286045825`|
|`product-inputs-r4.json`|145658|`4d9fbeeab76c2ac0d6108691ae0c953640d340f7dd29fde5605a129eec883ae3`|

分别在原开发树和 fixed 树逐项重算：11个changed、2019个全输入、665个产品的bytes／raw SHA／执行位均与r4清单相同，无缺失或symlink替换。fixed 的 `git diff f6722141 b3e734ba` 与上述 native-only patch **逐字相同**。按文件比较r3／r4 patch，仅忽略文件排列、Git index与hunk位置元数据并去除已审单行Linux标记后，各文件的增／删／context正文全部相同；没有额外native-only行为漂移。原manifest、v1两资源仍与M5父逐字相同，283原件逐项SHA／普通文件核验仍无差异；v2两资源亦保持首审raw，executor仍由同一patch产生feed0fa7身份。

独立静态检查最终接线：

- fixed 的 `reference_training_worker.py` **逐字等M5 r6父**（SHA `885c14055851fd1ea34cd37d5afad04b0aa0f44edd12be7edc0c4592516aecd9`），原 Execution 文件同父。protocol 中 `native_main`、`authenticate_cycle_candidate`、`validate_context`、`_round_sources` AST 均与M5 r6父相同；本片按版本capability改动没有覆盖它们。
- worker `_round_operation` 保留 `_round_previous` 的原三处H调用（`:1210,1255,1281`），未采用删末次H的探索方案；末次archive／前轮phase检查后，final parent gate、当前index重读及local gate返回，才在 `:1288` 调用原共享纯本地 `authenticate_cycle_candidate`，再绑定report及产生acceptance。这里没有新增SDK wrapper或复制遍历算法。
- native `active` 仍在原executor callback／锁与attempt、ack各同步后调用；最终 `protocol.py:1740` 先 `parent.check()`，然后 `:1743` 同一fence／owner条件和 `:1745` 原clock采样。父授权读和owner观察先返回，原work allowance最后复核，不换clock或重开window。正常解释器身份门、selected native Python最后可用性门及已有result早读仍保持。

原 M5 reviewer 已在其报告的准确r6节给出R4／R5源码修复实证处置；本次独立核对的是这些修复在最终native候选中的**身份及接线保持**，没有复跑或重新验收其红绿矩阵。前述“r5尚未冻结／M5最后门待修”是首审时点，已由这里的准确r6继承更新；这不表示完整M5安装／模板／最终验收已完成。

**最终 r4 固定候选的有限源码需求／维护性两轴 approve，开放 finding 0。** 初审25项和平台修正2项运行继续只属于各自原输入；不能转写为b3e734ba新安装或新末端时序的运行成绩。最终候选仍须自己的新非editable core／SDK完整安装、实际site-packages与资源身份、正常所选无SDKvenv whole-hook，以及自身模板／独立终核和候选自己的必要CI。Windows未运行；M5原R1完整hook无SDKmandatory、M6／schema3效果、正式producer、真实两轮／GPU／训练质量均没有由本次身份复核关闭。

## 最终 r5／M5 r7父身份复核

2026-11-16，同一 reviewer 再作有限只读身份／接线复核，未运行测试、probe、模型或安装。原开发树HEAD仍a1ff338；fixed树当前分支 `feat/native-admission-dependency-v2-fixed-r5`，干净HEAD **`bc58be6781d35e7e4fbd54ad997df8a4743428a8`**，唯一父 **`5bcecf37b615e3708ceb08acc329ba3dd0470f4a`**（M5 r7）。M5 r6→r7原delta为8291B，SHA **`64250fa2be9d490fbd185a2a2455d4dba522bc625e74145dbd76a6054d47ff96`**；产品增量只有原共享protocol的六行，其余为既有fixture／submission测试。

|r5冻结原件|bytes|raw SHA256|
|---|---:|---|
|`native-only-r5.patch`|44045|`3524d80f4d1c62688086cbaf9638ddc07c6d5a8f8f79118fecb87555273fbdc0`|
|`source-freeze-r5.json`|2906|`2b2afcc66b496ad8d7595b66e472e75bcd9f20ce3b309a6dc913940d56e81cc8`|
|`all-tracked-untracked-inputs-r5.json`|421972|`f8e9387b04db06ffb0b70de82c27cafcb3661f637ffa5a3b0a7d09a2bb3d9e6e`|
|`product-inputs-r5.json`|145658|`4cab575528cb89c1ac9008b95fbb6e0170fea7b1325e245a6d2318ff14e56b15`|

逐项重算原开发树和fixed树的11 changed／2019 all／665 product，全部raw bytes／SHA／执行位均与r5清单匹配。fixed父→candidate完整Git diff与native-only-r5.patch逐字相同；按文件忽略Git index及hunk位置元数据后，r5与已审r4 native-only patch正文完全相同，**本片行为没有新增漂移**。283原件仍逐项匹配；v2资源、reference、CLI、平台标记及离线版本／capability行为保持已审身份。

最终protocol的 `authenticate_cycle_candidate`、`native_main`、`validate_context`、`_round_sources` AST逐一等M5 r7父；worker与Execution文件逐字等父，worker仍为885c1405…身份。独立沿真实当前intent生产路径核到：

- `protocol.py:1535` 使用当前budget父目录的固定 `<ident>.intent.json`，`:1536` 复用 `ExecutionRecords.document` 并显式 `limit=16 * LIMIT`。有current owner则必须读到文件；存在时 `:1538` 以原 `_match`／canonical SHA核完整实际intent与调用者缓存，不只比ID、也不新设raw pin，语义不变的空白重编码仍合法。
- `:1639` 在长前驱／来源读取结束后，以同一16MiB上限重读并比较入口实际值，再执行原parent／clock的active。入口已有文件后来删除会走必读失败，改义会canonical不等；原safe普通文件／NOFOLLOW／duplicate-key／JSON object边界保持。没有以JSON null伪装optional缺失的通路。
- 真正unborn路径仍来自原 `reference_training_submission.py:349` 的prepare binding，早于 `:355` 写intent及更晚owner出生。仅当本地owner／intent均未出生时允许None；`:358` 写后复核面对现存intent。新六行不创建／修复intent，不增加调用者可信skip开关，出生前后由现存本地事实区分。本次核的是实际生产caller及已审r7算法的保留，未另跑unborn行为测试。

worker三处H仍在 `:1210,1255,1281`；末H／final parent SDK／index／local gate后仍在`:1288`作共享纯全链认证。native最终`:1746`先parent.check，`:1749–1752`再核fence／owner及原clock，原attempt／ack同步后active调用保留。新当前intent检查没有覆盖或挪走这两项r6最后门修复，未重开原clock。

**r5固定候选有限源码需求／维护性两轴approve，开放finding 0。** 父任务已告知r5新core／SDK各665产品身份通过、自身原结构模板Codex28.602s approve；本轮未独立核这些安装／模型原件或仍在运行的installed25终态，不将其算作本次证据。下一步由新的fresh最终组合审查核准确候选的新安装、完整whole-hook及实际运行终态。M5原R1保持open，直至真实whole-hook无SDK证据独立核实；本报告不将旧r4/r3成绩、父r7源码批准或模型结论转授未完成的安装／整片验收。Windows与M6／schema3 effects、正式producer、真实两轮／GPU／训练质量边界保持。
