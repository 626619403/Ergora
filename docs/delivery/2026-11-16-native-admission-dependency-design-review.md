# 原生准入依赖隔离：独立设计审查

2026-11-16。Reviewer：fresh-context 独立代理 `native_admission_design_review`，未参与方案或 M5 实施。应用 maintainable-project-delivery 的 independent-review brief、ergora-codebase-quality 的 module-design／test-seams；先读根／源码 AGENTS、PLAN 和组件变更协议，再核实际源码、版本资源与相关交付。唯一允许且实际写入的文件是本报告。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|**approve，仅限所审静态依赖隔离设计**|0；原 P3 经同片文档复核关闭|
|结构／维护性|**approve，仅限所审静态依赖隔离设计**|0 项阻断|

方案选择的最小正确 owner 是原 `agent_platform.training` 中两个真实 CLI 使用点：在 `run-local`、`approve` 使用前局部导入同一个 `perf_temporal.client.load_experiment`。用显式新 admission source-v2 承载这项差异，保留原283、manifest 和 v1 patch／descriptor；不需要拆路径模块、复制 loader、改 client 算法或引入注入框架。批准不等于产品已实施或真实无 SDK hook 已通过，也不关闭 M5／M6、完整 M1c、schema3 效果、ordinal1 或真实两轮验收。

## 原始要求、基线与实核身份

原始要求是 native 最后执行准入只核完整本地来源，不导入应用 State／schema／SDK；保持 immutable283、原 candidate／records、attempt-before-send、原锁／permit／唯一 reaper、离线 history 和已有 result 早读。能力只能按出生来源判断，不能给旧 owner 重采 capability、换 clock 或隐式升级。实际阻断是 `native_main` 首次导入 patched executor 时，沿 training 顶层 client import 加载 Temporal，在 callback 前被禁 SDK hook 拒绝；纯 protocol 的 `-P -S` 通过不能替代此入口。

主树 `refactor/architecture-foundations`，准确 HEAD 为 `debf6f96ed02620d22adc0ac6385c72641b3d53b`。首审所审 [设计](../plans/2026-11-16-native-admission-dependency-isolation.md) 为新增未跟踪文档，21,803B，raw SHA256 **`38500544bd6e0cec1bb33b405f5b4ddec44d60658645df07926a912b47927c6d`**；修订后的准确身份见末节。进入时已有 PLAN／交付文档差异与 CPU 前置清点，不属于本审改动。

另只读 M5 隔离树 `.ergora/worktrees/training-cycle-predecessor-gates`，baseline `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`。实际冻结记录和 `m5-g-source.patch` 的 raw SHA 均为 **`fba1838ac6e7cb13cdbab9ec9b96e66cc38cdf8c5de3eb00c381f120ca050e1d`**；六产品／四测试的范围与交付吻合。该树 protocol 实际 SHA 为 `5cfeac98893c3b8715947956b0b718218129dd556e7bf8a465fe9e6b8dda8347`，与 freeze 相同。没有改动、重启或介入其在跑检查，也没有把源码冻结视为运行／安装通过。

|实核原件|bytes|raw SHA256|
|---|---:|---|
|`data/reference-manifest.json`|35818|`1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`|
|原 `platform/local/agent_platform/training_executor.py`|8429|`e6d2273c5958b0d2327338ebb07aade8b4c6e3ce27eee42c39454bf9af31eed0`|
|原 `platform/local/agent_platform/training.py`|16366|`97dcf661b34de14f8edd28a1ca3c7fb4b40ca891b40398bbad73b8b8b6ebf9e0`|
|原 `platform/upstream/temporal/perf_temporal/client.py`|3113|`e01ac4d801af1ae3a6a56ca84b0645a0f9ab9dd50820943ad4374ed969d73ba9`|
|`training-executor-admission-v1.patch`|1316|`45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`|
|`training-executor-admission-v1.json`|439|`d7e2b706599c6fcbb874a1a1dbec8b9875df817dc71ffa455801e48c240c2c55`|
|从上述原源码及原 patch 静态逐行重构的 v1 executor|9013|`feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`|

用 stdlib 静态读取 manifest 并逐项核包内原件：**283 项、缺失／symlink／SHA 不匹配均为0**。v1 patch 每个旧行均与原源码核同，再在内存中重构，无文件落盘、git apply 或执行。结果与原 descriptor 及私有 `native-sdk-dependency-originals.json` 的安全 bytes／SHA 字段相符；未输出私有实际安装路径或环境。主树及 M5 的参考283／manifest／native-runtime 范围没有产品差异。

## 依赖 owner 与最小变化判断

1. **真实导入链成立。** 原 `training_executor.py:11–13` 顶层读 core／sandbox 和 training 的本地路径／Binding 职责；原 `training.py:18–21` 唯一顶层 SDK 牵引是 client import；`perf_temporal/client.py:10–13` 导入 Temporal、connection 和 Workflow。应用 `training_execution_protocol.py:1339–1354` 在定义 callback 前导入 executor，M5 对应为 `1670–1685`。因此只隔离 verifier 导入不能解决完整 hook。
2. **两个使用点足够且属原 owner。** 原 `training.py:244–250` 的 run-local、`:254–271` 的 approve 是 `load_experiment` 的两个真实使用点；client `:16–21` 已拥有完整 Experiment 构造和 validate。局部 import 保留原算法、确认 manifest、原 request／process、phase 查询和审批动作次序；其余操作仍按 `training.py:272–274` 使用原 PYTHON 启动 client。SDK 不可用时在实际 client 使用边界失败，不另实现“轻量”等价 parser。
3. **其余准入导入闭包静态可纯化。** 核过 core、sandbox、perfctl、perf_temporal.adapter／models、有关包 init 和应用 protocol／reference 顶层，均为 stdlib 或上述本地依赖。executor 的 MLflow 在 `training_executor.py:16–18` 函数内，不影响进入 callback；这不证明 runner／track 全阶段无第三方依赖。
4. **新版本资源是不可变合同所需。** `reference.py:92–114` 对 v1 descriptor 要求 raw 逐字相同，`:117–129` 对带 overrides 的安装验证完整 platform 来源。直接修改 ROOT 或在 v1 安装下改 training 必然破坏现有身份。设计 `:40–44` 的完整 v2 patch 可从同一 base 单次应用，executor 保持 v1 字节，仅新增 training override，既隔离依赖又不搬动准入时序。

五个产品文件的范围合理：两个新版本资源、已有 reference／protocol／CLI。reference 已拥有准备、descriptor 和完整安装校验；protocol 已拥有 capability、历史 shape 和本地来源；CLI 只暴露明确选择。`reference.validate_installation` 还被 services、registrations、tasks、training 及 worker 使用，不能只在 CLI 增加一份“允许 v2”的解析。`pyproject.toml:30–31` 的现有资源规则覆盖新增资源，无需新打包框架。

## 版本、历史与来源合同

|可达场景|设计必须落实的判断与源码依据|
|---|---|
|选择 v1／v2、未知或格式变体 descriptor|保留 reference 的 fd／非阻塞／普通文件／无 symlink／65,536B 边界；只从封闭 protocol 集合选择本版 bundled raw，再完整逐字比较。JSON 的 protocol_id 仅用于选择，不能使额外字段、重排格式、重复字段、截断、未知版本或空声明合法。不得退成 legacy。设计 `:54–60` 已明确这些限制；CLI `:170,923–925` 继续只委托 reference。|
|descriptor 在 validate 与 capability 采值之间变更|`source_capability` 不能仅把第二次任意 raw 的 SHA 写入 capability。捕获的 raw 必须仍恰等于本版 bundled descriptor，其 admission_protocol、descriptor SHA 与已验安装一致；live 验证再次核这一关系。设计 `:60` 已显式要求，不应只保留当前 `protocol.py:809–817` 的“先验安装、后读任意 raw”形式。|
|25项 source 混表／缺项／额外项|按 capability.admission_protocol 选择单一版本表；v1 保留当前 `GATE_SOURCES:41–50`，v2 仅换 descriptor key，均严格25项。不得接受两表并集、可选 key、按当前 descriptor 猜版本或宽泛 `>=2`。当前 owner shape `:758–779` 与 live validator `:820–826` 是实际修改边界。|
|ROOT 或自洽新 manifest 替换|先核原 owner 出生的25项与 manifest raw，再由同一已 pin reference.verify 核283，最终重核 source／stop／clock。M5 `validate_sources:954–967` 已有这条次序；新版本支持不能把它退回主树旧 validator。授权四 measurement 与 owner 出生25项仍是两个时点，不能补造授权 pin。|
|旧 owner1／owner2 null／旧 v1 capability，安装已移走|`ExecutionRecords.load:1157–1164` 调用 owner_record，而 history 路径不调用 validate_sources；`inspect_main:1422–1434` 只在 sources 操作核 live 来源。owner_record／可选私有 shape helper 仅验原七字段、封闭版本／精确键集／digest／路径形状，不读安装、不比当前 source、不导入 SDK。应用 `reference.py:470–478` 先读历史，再独立报告 sources unavailable。|
|旧 capability 重试、新包源码已变化或 v1↔v2 替换安装|继续以出生 source／descriptor／完整安装判断并拒绝漂移，不重采值、不升级 protocol。新包能读旧记录，不代表新包有执行旧 pin 的权利。`BudgetedStart.own` 在 `reference_training_budget.py:521–541` 明确拒已有 owner，capability 仍只出生一次。|
|没有 descriptor 的 legacy 安装|保持 `reference.py:117–128` 的原 legacy 校验范围，source_capability 为 None；删掉 v1/v2 descriptor 后因 patched executor 不等原源码而拒绝。设计 `:104` 的“原 identity”不能被矩阵 `:140` 解读为给 legacy 新增 requirements／所有 platform 非 Python 文件全量校验；若想扩大 legacy 规则，那是另一个产品兼容变更，需要明确提出。该矩阵的 requirements 反例适用于有版本 descriptor 的完整安装。|
|schema3 storage-only 旧材料和新的正式 M6|旧 v1 材料只能按其原语义存储／读取，不换安装路径、measurement pin、clock 或 ID。M6 对新出生运行显式选择 source-v2；admission source-v2 与 cycle-v2／activity-v3 是独立版本维度。设计 `:111–113,132` 已保留边界，不由同名版本联动开放。|

私有 `_capability` 只有在 owner shape 和 source validator 真实重复时才有必要；这两个边界可共用纯 shape 校验，但历史调用不能被重构成一次 live install 验证。无需新公共协议层或注册器。保留 `TRAINING_PROTOCOL` 原值供旧 caller、增加封闭支持列表，是兼容选择，不是把所有旧默认改成 v2。

## 早读、真实入口和验收矩阵

v1 patch 的 executor 顺序是原锁内 result 早读，然后 request、started 不确定性拒绝、managed／admit，再进入原 binding／fence／started／runner。v2 executor 同字节能保留这条顺序。应用入口仍先验安装、真实 sys.prefix 和 core 四路径；schema2 本来还有外层 context／permit。设计 `:117–123` 正确区分这些前置、锁内 result 和独立离线 history，不能许诺 result 绕过全部入口验证。

M5 `native_main:1711–1735` 已在 callback 重新加载完整 records／context，并在 attempt 和 ack 同步后只接受本次已发布阶段；v2 不改 executor hunk和该 gate。故应保留真锁、真实 publish／fsync、真实停止／reap序列，不能通过重复 unused-launch 判断误拒自身 attempt，或因已有 ack 而重获 runner 机会。已有 ack 后 S 写真实 stopped 合法，不能为“没有 started”反例强求 stopped 消失。M6 未来 source-v2 条件须落在真正新执行准入，并保持旧 completed result 路径，不新增会误伤该早读的 schema3 入口 gate。

所提验证矩阵能触及实际故障，成本也与风险相称，但每项仍需未来准确候选的实证：

- **完整无 SDK hook 是关键门。** `tests/fixtures/training_executor_client.py:9` 已顶层预导入 executor；`tests/test_training_runtime.py:134–154` 的 native_executor 依赖 importorskip Temporal 且用当前 sys.executable；controller 原 native-context 在 `tests/test_training_cycle_controller.py:1639–1643` 显式附 SDK site。它们不能单独证明新 core-only 来源的首次导入。必须在拒 State／jsonschema／YAML／temporalio 的 hook 安装后，使用所选新 venv 的正常 `-P` 启动、真实 prefix／core 路径、实际 native_main 和真实 context／chain 到 callback。保持 v1 原失败作为对照，不注入假 SDK／sys.modules，也不伪 prefix。
- **`-P -S` 仅证明纯 reader／认证。** Python3.11 下 -S 的 venv prefix 边界已经由 M5 原失败记录；不能用它替代 native 正常入口。合法约10MB原件应通过真实 H／Budget／context／callback读取；M5 schema3 关闭只能证明读取及拒绝，attempt／ack 更晚 schema3 正向仍归 M6。
- **reference／capability／history 用现有接缝。** 沿 test_reference 的显式 CLI、完整安装、缺 descriptor／格式变体／中断准备反例，补两个版本间身份误认；沿现有 owner/history 接缝验证旧／新 capability 无安装可读，来源检查独立拒绝。无须为每个 helper 复制整套矩阵。v1 三份 Workflow history 按受影响范围复用回放，其成功不能替代 native 安装身份。
- **两个 CLI 使用边界保持原语义。** SDK环境经真实 run-local／approve 使用原 client loader及原校验；无 SDK 时在实际 client 使用处明确失败。只看 import 文本或替换一个总抛错 admit 不足以验证。允许替换无关外部动作的叶子，但不能替换原 loader／verifier 的成功结果。
- **新非editable core／SDK分别认证。** 核实际 site-packages、完整资源字节／执行位、283／v1原件和新v2精确hash；core无SDK hook 与SDK CLI语义分别记账。无需因此重跑无关全suite、新建CI job或移除原 requirements／SDK extra。冻结后若修产品，受影响证据必须绑定新候选。

新增 source-v2 是明确版本扩展，局部 import 是依赖整理；本设计未要求新的业务授权、调度器、实验账本、自动 release、质量规则或用户决策。若实施中需要放宽已有 descriptor／legacy 身份、自动迁移旧 owner、取消原前置或扩大可执行 schema，就越过本次批准范围，须另行明确合同，不能从本审推导用户已同意。

## Finding 处置与验收边界

**P3，原非阻断记录澄清，现已关闭。** 首审位置：[设计第148行](../plans/2026-11-16-native-admission-dependency-isolation.md#完成边界与独立审查交接)，原文“截至本页……M5源码尚未冻结”。实际 M5 交付第47–68行和 `source-freeze.json` 已记录 fba1838a 固定十文件，且本审直接重核 patch／protocol SHA。第7行有“进入时”限定，可以保留原始未冻结事实；第148行原当前语态会让后继误认为无可引用的固定输入或重复冻结／启动检查。要求的最小修订是保留调查时观察，另记准确当前状态与真实无SDK hook mandatory未满足，不改写旧失败为通过。修订与复核见下方。

没有发现需要改变依赖隔离方案的 P1／P2 问题。P3仅影响交接表述，其修订与关闭不改变上述静态两轴 approve。当前本片开放 finding 为0。

本审执行的是只读源码／文档／Git／raw长度和SHA核对，以及内存中的静态v1差异重构；未运行 tests、probe、应用／SDK import、history replay、安装、网络、模型、服务或训练，未修改其他 docs／产品／测试，未 commit／push。没有核验 M5 当前测试最终结果、所有私有运行原件或新 v2 产品，因为它们不属于本次设计检查的已存在证据。

后继应先接纳 M5 最终准确固定产品，再按 D1–D3 冻结依赖隔离候选，完成严格资源／安装／旧历史／已有result／真实无SDKcallback验收。M6 的 source-v2 明确采用与所有 schema3 最后gate、正式 producer／Workflow、完整容量、CPU两轮和资源收尾仍须在其自身候选完成；本报告不替它们关闭任何 mandatory 项。

## 同片 P3 文档修订复核

同一 reviewer 仅对修订文档做最小只读复核；本轮唯一写入仍是本报告。当前设计为22,939B，raw SHA256 **`3ab1a21f7f2dff70e6b4c8a6cfe4c25cba267c438e70ec650eef8709dbf4000c`**。在内存中撤回第148行改写并移除新增“设计审查时的当前检查点”一节，重得首审准确 raw SHA `38500544…`；因此已确认差异仅这处历史语态和尾部追加，source／业务合同正文没有其他变化。

第148行现明确“最初调查时”“这是历史观察”，保留原失败并指向当前检查点；第156行记录已冻结 fba1838a、原批38节点37过／1败／639.04秒和缺ref定位在途，明确不应重启原批、不把旧patch／静态审授给修后候选。M5源码审只批准限定接线、整片pending／SDK-free mandatory仍open的措辞，与其[源码审查](2026-11-16-training-cycle-predecessor-native-gates-source-review.md)结论相容。本复核只检查这项记录的表述及来源边界，未重新核原运行日志或认证该38节点结果。

第158行进一步明确：requirements／所有platform文件完整identity反例仅对有版本descriptor安装，无descriptor legacy仍沿原Python子集及training选择规则。这澄清了原第140行矩阵的适用范围，没有扩张旧安装校验或改变首审的兼容性判断。相关相对链接均存在，未见尾随空格。

**P3关闭，需求／维护性继续approve，仅限静态设计；开放finding为0。** 本轮未运行tests／probe／安装／网络或重做283及v1原件核验；M5原回归失败、依赖隔离真实安装／完整无SDKcallback和M6各项mandatory保持各自待验状态。
