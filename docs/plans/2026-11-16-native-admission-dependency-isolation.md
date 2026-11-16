# 原生准入依赖隔离：最小 source-v2 设计

2026-11-16。**静态调查／设计草案，待 fresh 独立需求与维护性审查。未实施、未运行验证、未安装；不关闭 M5 的真实 hook SDK-free 缺口，不开放 M6、schema3 效果或 ordinal1。** 本页是独立的依赖整理前置片，不改已接纳的 [M5 gate](2026-11-16-training-cycle-predecessor-native-gates.md) 或 [M6 runtime](2026-11-16-training-cycle-v2-runtime.md) 业务合同。实际失败沿 [M5 交付](../delivery/2026-11-16-training-cycle-predecessor-native-gates.md) 原样保留。

## 调查范围与固定事实

主树调查 HEAD 为 `debf6f96ed02620d22adc0ac6385c72641b3d53b`，分支 `refactor/architecture-foundations`。进入时主树已有 PLAN／交付文档差异，本轮未修改。M5 隔离树 `.ergora/worktrees/training-cycle-predecessor-gates` 的 HEAD 为 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，六个产品文件、fixture／测试仍有未冻结差异；本页读取实际差异后的有关调用，但不把开发态称为固定产品。后续实施必须先选定 M5 的最终固定候选，重新核接口和输入身份。

本轮应用 maintainable-project-delivery 与 ergora-codebase-quality 的 module-design／test-seams：先读根及源码 AGENTS、docs/PLAN、组件协议，再用 Git、rg、sed、sha256sum 和对一份已知私有清单的字段投影做静态核查。没有 tests、probe、SDK import、安装、网络、模型、服务、commit 或 push；唯一新增文件是本页。没有递归扫描 checks 或输出环境。私有 `native-sdk-dependency-originals.json` 只读取键名与 SHA／bytes，公开文档不保存其私有实际路径。

|固定原件|字节数|SHA256|
|---|---:|---|
|`data/reference-manifest.json`|35818|`1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`|
|原 reference `agent_platform/training_executor.py`|8429|`e6d2273c5958b0d2327338ebb07aade8b4c6e3ce27eee42c39454bf9af31eed0`|
|原 reference `agent_platform/training.py`|16366|`97dcf661b34de14f8edd28a1ca3c7fb4b40ca891b40398bbad73b8b8b6ebf9e0`|
|原 reference `perf_temporal/client.py`|3113|`e01ac4d801af1ae3a6a56ca84b0645a0f9ab9dd50820943ad4374ed969d73ba9`|
|`training-executor-admission-v1.patch`|1316|`45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`|
|`training-executor-admission-v1.json`|439|`d7e2b706599c6fcbb874a1a1dbec8b9875df817dc71ffa455801e48c240c2c55`|
|v1 所选安装中实际 patched executor|9013|`feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`|

主树四项 manifest／training.py／v1 patch／v1 descriptor 的 raw SHA 已直接重核；其余数值与 M5 已保存的必要字段、源码内容相互对应。本轮没有重新执行原失败。主树及 M5 树在 reference283、manifest、native-runtime 范围的 Git diff 均为空。

## 真实调用与故障 owner

有两族真实生产用途共用 `agent_platform.training`，不是为测试制造的可替换依赖：

|调用族|实际路径与需要的行为|依赖边界|
|---|---|---|
|本地准入／原 executor|`BudgetedStart.own → Execution.drive → _BudgetPhase(mode=execute) → reference.worker_command → 所选 .venv/bin/python -P → protocol.native_main → agent_platform.training_executor.process(admit=...)`；executor 顶层取 `.training` 的 `TRAINING/binding_from/fence_path/perf_root`|这些本地路径／Binding 计算不使用 SDK；callback 在原 executor 锁内且在 started/runner 前运行|
|原 training CLI／SDK 操作|`agent_platform.training.cli` 的 `run-local` 与 `approve` 各调用 `perf_temporal.client.load_experiment(str(spec))`；其他 start/status/result/cancel 最终以原 PYTHON 子进程运行 `-m perf_temporal.client`|client 拥有 Experiment 读取算法、SDK连接与 Workflow 操作；run-local 也保留调用原 client 的原行为，不能另写轻量 parser|

静态原链是 `training_executor.py:13 → training.py:20 → perf_temporal/client.py:10 → temporalio.common`。应用 `protocol.native_main` 在定义／进入 callback 前导入 executor；因此“protocol 纯本地 verifier 能导入”不能代表真实 hook 能导入。v1 patch 没有改变这条导入链。

独立核对顶层闭包：`agent_platform.core`、`sandbox`、`perfctl`、`perf_temporal.models`、`perf_temporal.adapter → models` 及两个包 `__init__.py` 当前仅引入 stdlib 或这些本地模块；`training` 唯一顶层 SDK 入口就是上述 client import。`training_executor.track()` 的 MlflowClient 已在函数内；本片不承诺 runner／track 全程无第三方依赖。应用侧 `ergora.__init__`、protocol 顶层的 budget_clock／processes／reference 及 reference_creation_process 也无顶层 SDK／State。ExecutionRecords 的局部 core／dev_platform.adapter／contracts 读取沿原 owner，不增副本。

其他真实消费者必须继续受益于同一 reference 身份选择：services／registrations／tasks／training 使用 `validate_installation`，training worker 的 `_training_process`／main／cycle_main 同样走它。CLI 只是 `prepare_training` 的入口，不拥有第二份 descriptor 解析。历史路径是 `reference.training_execution → _training_reader(-P -S, 包内ROOT路径) → protocol.inspect_main → ExecutionRecords.load/observe`；随后独立尝试 sources，失败只使 `current_sources=unavailable_or_changed`，不能吞掉已读 history。

## 最小选择：新增 source-v2，保留 v1 字节

直接把 SDK import 下沉是最小代码变更，但原 training.py 属于不可变283；只改所选安装又会被 v1 identity 拒绝。因此采用**新的显式 `training-executor-admission-v2` source bundle**，不动 ROOT283／manifest／v1 两资源。不抽新通用模块、SDK adapter、注入框架或第三种 executor；原两个 CLI 分支各在使用处局部导入同一个 `load_experiment` 即足够。它们仍调用原算法，SDK 缺失在实际 SDK 使用边界明确失败。

v2 patch 直接针对同一个原 platform base，包含 v1 的 executor hunk，加 training.py 的三处机械变更：删顶层 client import，在 run-local、approve 的原使用分支各加局部 import。v2 的 executor 应与 v1 patched executor **逐字同 SHA `feed0fa7…`**；v2 descriptor 的 overrides 恰有 executor 和 training.py 两项。新 training.py／patch／descriptor 的精确 SHA 只能在实施后产生并冻结，本设计不编造值。descriptor 结构仍 schema_version1，base_reference_version2.2 和 base manifest SHA不变；protocol_id、patch_sha256 和新 overrides 按实际新文件填写。v2 patch 是完整可从原 base 单次应用的 bundle，不要求先安装 v1 或在已安装 v1 上补丁。

这比拆 `training_paths`／复制 Binding/load_experiment 更小：没有新 caller 义务，没有第二份模型／路径／读取算法，也没有挪动原 executor 锁与 callback 代码。把 client.load_experiment 本身搬到 models 会牵动更多原件与消费者；更换 executor 的 `.training` 依赖则需要拆出或复制四个既有职责，均无必要。

## 精确文件与版本接线

预计产品改动仅以下五个文件；后续若 M6 选择门需要源码差异，归 M6 原 owner，不暗含在依赖整理内。

|文件|拟变更与真正消费者|
|---|---|
|新增 `src/ergora/data/native-runtime/training-executor-admission-v2.patch`|原 executor hunk＋training.py 局部导入；只由 reference.prepare_training 消费|
|新增同目录 `training-executor-admission-v2.json`|原 manifest、完整patch SHA、两个安装覆盖 SHA；由 reference 验安装和 protocol source pin 消费|
|`src/ergora/reference.py`|保留 `TRAINING_PROTOCOL` 原值供旧 caller；另列封闭受支持 protocol 集合。prepare_training 只接受明确 v1/v2，仍无默认升级；`_training_overrides` 以所选 descriptor 的 protocol_id 选择本版本 bundled raw，再要求 raw **完整逐字相同**；validate_installation 仍返回 Path，仍验证本版本完整安装文件，不必扩 public 参数|
|`src/ergora/training_execution_protocol.py`|原 execution PROTOCOL 不变；capability admission_protocol 按实际严格验证的 descriptor 生成；owner_record／source_capability／validate_sources 使用每版本精确 source 表，不改 owner schema／record shape|
|`src/ergora/cli.py`|prepare-training 的 choices 从 reference 的封闭列表取得，用户必须显式选 v1/v2；不加全局“SDK-free=true”或升级命令|

`_training_overrides` 当前的 fd/lstat、65,536B界、无 symlink／非普通文件拒绝、manifest hash核对、完整安装 SHA 比对与 prepare 的先写空descriptor→copy→git apply check/apply→核安装→持久descriptor 顺序均保持。未知 protocol、空/截断/格式化/额外字段 descriptor 不得 fallback 成 legacy。没有 descriptor 的安装只有当文件仍满足 legacy原identity时才成立；v1/v2 patched source 删除 descriptor 后必须失败。无需改 requirements.lock 或移除SDKextra；“准入无SDK”不等于整套训练依赖已卸载。

source_capability 先按同一 reference owner 验安装，读原 descriptor 得到已支持 protocol_id，并把**该原 raw SHA**写入 descriptor_sha256；按此版本的25项采值，返回原七字段 capability。实现应保证捕获的 raw 正是所选 bundled descriptor，不能只相信 JSON 的 protocol_id。validate_sources 核 capability的完整shape／版本→本版本source精确键集与digest→出生source hash→同一 reference.verify 的283→所选安装完整identity→descriptor raw hash及 protocol_id与capability一致→按 M5 原顺序复核source/stop/clock。不可用当前descriptor重生capability。

现有树没有名为 `_capability` 的函数。若实施把 owner_record 内已有完整capability shape校验提为 protocol 的私有 `_capability`，仅限 owner_record 和 source validation 这两个真实边界共用同一纯校验；它不读安装／SDK，也不构造／补齐字段。是否提取由实际diff的重复决定，不把它做成新公共层。

### 每版本严格25项

保留现有 `GATE_SOURCES` 的 v1 内容与语义；v2 独立表含同样前24项，第25项换成 v2 descriptor。可用同一不可变前24项元组组装封闭映射，但验证必须按 capability.admission_protocol 取**单一版本表**，不能接受两表并集、24/26项、任意descriptor名字、`>=version` 或“可选source”。

```text
training_execution_protocol.py
reference_training_execution.py
reference_training_submission.py
reference_training_context.py
reference_training_runtime.py
reference_training_cancellation.py
reference_history.py
reference_training_budget.py
reference_training_worker.py
training.py
reference.py
training_cycles.py
registrations.py
data/schemas/training-cycle-v1.json
data/schemas/project-registration-v1.json
definition_bundles.py
contracts.py
asset_trees.py
state.py
budget_clock.py
processes.py
reference_creation_process.py
__init__.py
data/reference-manifest.json
# 恰选一项：
data/native-runtime/training-executor-admission-v1.json
data/native-runtime/training-executor-admission-v2.json
```

这里的 `training.py` 是应用包文件，不是原生安装的 `local/agent_platform/training.py`；后者由本版本 descriptor override SHA和完整安装核验覆盖。patch SHA由descriptor绑定，prepare复核；运行时依旧按原合同钉descriptor和已安装源码，不扩source表来凑26/27项。四项 measurement_sources 的出生和严格键集完全不变。

## 旧安装、历史与恢复行为

|对象／动作|必须保留的行为|
|---|---|
|legacy安装，无descriptor|按原文件identity读／验；source_capability仍为None，不升级为managed capability|
|v1安装，新应用|原descriptor／patch仍可准备和验证，training.py仍原字节且保留SDK牵引；明确不认证真实hook无SDK。新的schema1/2 owner若原授权允许，仍可按其实际当前source出生v1 capability|
|已有owner1／owner2 null capability|原shape照旧读；不补capability、不重启owner、不换clock，无新执行权|
|已有owner2 v1 capability的离线history|只按原七字段、原protocol和v1精确25键／digest格式校验；不要求当前source相等，不读所选安装／SDK。安装缺失、应用升级或v2存在均不能阻断已有records；后续sources独立报告漂移／不可用|
|旧owner请求执行／重试|继续按其原v1 source值、descriptor SHA和原安装核验。新应用修改了已pin源码时正常拒绝；不把出生值换成新值，不把v1解释成v2。保留原产品／原安装可继续按其原合同判断，不承诺新包执行旧pin|
|新v2 owner|只从明确v2安装出生，descriptor与25项都属于v2；缺项/额外项/混搭v1 descriptor key拒绝。v2不改变authorization/controller/workflow/source operation协议|
|保存后安装v1↔v2替换|出生descriptor SHA、source表与完整安装共同拒绝；不能原地改descriptor／源码后继续原owner|
|原schema3 storage-only同意指向v1|保持旧材料只读／存储与关闭分支；M6不得换其execution路径、登记、measurement pin或clock升级为可执行。需要新v2安装及按正式流程出生的新ID／固定输入|

source protocol v1/v2 与 cycle workflow v1/v2、SDK activities v2/v3、program-v1/v2 是不同维度，不能按同名“v2”联动升级。应用execution PROTOCOL `ergora-training-execution-v1`、owner schema1/2、request/launch/attempt/ack/stopped原记录均不改版本。

## 早读、锁、阶段与解释器边界

v2 executor 与 v1同字节，保留 `executor.lock → result存在则返回 → request → started不确定性拒绝 → managed保留检查或admit → 原binding/fence/started/runner`。不把新的callback/source gate搬到result早读前；有result不得调用callback、写attempt/ack或重跑runner。native_main本来仍有入口级安装／sys.prefix/core身份核验，schema2本来还有外层validate_context／父permit；本片不宣称早读能绕过这些已有前置，也不把native early result与独立offline history混为同一保证。原schema3已有result从原executor早读的已验行为要保留，不能为M6加协议前置而误伤这条路径。

M5已接的callback仍在原锁内：入场读完整链，attempt同步后只承认本次attempt，ack同步后只承认本次ack；各点复核source／ROOT／stop／clock，失败保留已占用记录，无started/runner。ack后被S真实reap而写stopped是合法观察，不能要求它消失。v2依赖整理不移动callback、扩大可恢复阶段、删source检查、释放父共享许可或另造reaper。

纯认证使用原 `_training_reader` 或对应 `-P -S`，验证protocol/reference/ExecutionRecords不加载State/jsonschema/YAML/Temporal。真实native必须走所选 `.venv/bin/python -P` 的标准启动，保留 `sys.prefix == installation/.venv`、core.ROOT/PYTHON/STATE/CONFIG的原身份检查。Python3.11下 `-S` 导致venv prefix退回base是M5已观察的真实边界，不能伪造sys.prefix来过真实native门。正常解释器不带-S的检查必须从实际core-only新安装和所选无SDKvenv运行，并主动拒绝State/jsonschema/YAML/temporalio导入，区分“模块未调用”和“缺SDK也能到callback”。不手工附SDKsite、注入sys.modules/fake SDK或替换verifier。

已有 `tests/fixtures/training_executor_client.py` 顶层先导入executor，`native_executor` fixture依赖 `pytest.importorskip('temporalio')` 且用当前应用sys.executable；它们能保留原锁／manual行为保护，却单独不能证明上述完整native_main路径的core-only身份。最小调整应复用真实fixture的锁、管道及原records，把v2 core验收入口放在拒导入安装后、首次executor导入前，实际调用native_main；不得仅测 `process(admit=一个总抛错的替身)` 就宣称protocol callback已验。

## 小分期与客观验收

各期在一个依赖整理候选内顺序实现、记录；先固定源，再验安装，不把运行结果转授新diff。M5源码gate工作可继续，其SDK-free门仍open。没有理由重跑无关全量checks或新增CI job。

1. **D1，source bundle与reference入口。** 从固定M5产品建隔离候选；增加v2两个资源、reference/CLI严格选择，保留v1常量。静态重核ROOT283／manifest／v1两文件原SHA，v2executor同v1。沿现有test_reference验证CLI明确选v1/v2、全安装identity、descriptor持久顺序与原失败边界；新包资源沿现有`data/**/*`打包规则，无需新packaging体系。
2. **D2，capability按版本选择。** 改原protocol中的三个相关边界，若需要仅局部提取纯shape校验。保留owner/history早读与现有M5所有最后gate；沿原test_training_submission/controller/runtime的相应序列验证。确认v1旧capability无需安装仍能读，新v2同样可读，但source验证始终按各自完整pin。无需修改State、manifest、measurement四项表或创建通用注册器。
3. **D3，固定候选真实core及安装验收。** 新非editable core／SDK安装分别核实际site-packages、完整资源字节／执行位及原参考identity。核心反例和真实callback用core安装及所选无SDKvenv；原两CLI分支/SDK操作用SDK安装保留原client语义。提交固定、原模板与新的fresh独审按原流程记录，各自成绩不互借；本页没有执行这些门。
4. **D4，M6显式采用。** M6为新运行选择v2所选安装，在原schema3最终执行准入要求实际capability/descriptor属于v2；不得以配置布尔值声称无SDK，不在新gate前破坏已有result早读。具体接线在M6原prepare/source/native owner与其开放表审查，保持schema1/2原行为。只有依赖片D3完成，M6才可要求真实hook SDK-free通过；M6仍须自己的完整正向两轮／Workflow／producer／同步后故障与资源收尾验收。

最小验证矩阵围绕可静默误认身份、history被误阻断和callback前导入错误；不为每条文案／每个helper增加镜像测试。

|接缝|最小真实证据／必须观察的失败|
|---|---|
|原失败→修后|保留M5探索05原trace；同一拒SDK import条件下v1仍在executor导入链失败，v2正常venv入口实际到原callback，不能由fixture预载SDK。hook拒绝不产生业务result/started/runner；callback须读取真实完整context/chain，不mock验证成功|
|大前驱实际reader|沿M5原合法完整9,999,999B UTF-8含LF观察，经H/budget/context以及v2真实native callback读到关闭分支；保留M−1/M/M+1、多字节/合计容量原合同。M5schema3关闭只认证本地读取／拒绝；attempt/ack之后完整schema3正向到M6|
|v1/v2完整安装|新目录分别prepare，完整原platform文件均按manifest/本版overrides匹配；v2executor=v1 patched SHA，v1 training.py仍原SHA、v2 training.py仅局部import差异。legacy／v1／v2互换descriptor、改training.py/executor/requirements、缺/额外/格式化/截断descriptor均不得假接纳；复用原identity拒绝集合，不复制一整套矩阵|
|capability混搭／源码漂移|各版本25键恰等；v2带v1 descriptor键、v1带v2键、24/26项、未知protocol拒绝。出生descriptor、应用source、包内ROOT或所选安装任一漂移拒绝；保留M5已有源/manifest先后重核，不接受当前自洽manifest替换原pin|
|历史与result早读|原owner1、owner2 null、旧v1有capability的history用纯-S且移走安装读完整records；sources单独报不可用。原三份v1 Workflow history按实际影响复用回放。v1/v2 executor已有result同raw读取、callback未进、无新attempt/ack/runner；schema3 native-context旧completed路径保持|
|attempt／ack最后门|沿M5原真实锁／fsync/pipe缝隙，源/ROOT/stop/clock在attempt后或ack后漂移：前者无ack/started，后者ack保留无started，真实stopped按原reaper事实记录。schema2可达序列保持；不能把schema3早关通过计作较晚阶段已验|
|原两CLI使用边界|SDK环境run-local/approve仍调用原client.load_experiment且保留其完整校验／动作顺序；无SDK环境只在实际使用client时明确失败。不复制loader算法、伪client或只验证import语句文本|

## 完成边界与独立审查交接

最初调查时，M5已报告：实际H／Budget.source／validate_context读取合法约10MB原件；拒State/schema/SDK导入的纯protocol `-P -S`认证通过；真实native正常prefix入口则因v1传递SDK import在callback前失败。另有真实SDK可用的callback关闭路径／同步故障探索；它们不证明无SDK。该调查时点的M5源码尚未冻结／实施独审／新安装完整验收，原容量检查整体仍失败；这是历史观察，当前状态见下方追加检查点。此依赖设计不将这些结果改写为通过。

fresh设计审的原始输入应包含：本页任务限制、根AGENTS/PLAN及组件协议、固定1f57ca4与主树debf6f9、v1原patch/descriptor/manifest、实际training/executor/client和上述两族caller、M5已接纳设计/交付及实际开发diff、M6原开放表。本页是待评估方案，审查者应独立判断是否比它更小且保持不可变合同；给需求／维护性两轴结论与可达反例，不预置approve。实施审另给最终固定候选、tracked/untracked完整diff、新v2资源raw、精确core/SDK包及实际失败/通过原件。

下一步是fresh设计审后固定最小D1–D3依赖片，M5 gate继续独立收敛；在真实v2 hook无SDK、安装identity和旧history/早读行为均实际验收前，M5完整闭合与M6无SDK前置保持未满足。即使依赖片闭合，也不代表schema3已开放、正式Workflow/producer已实现、两轮执行已完成或训练质量已认证。

## 设计审查时的当前检查点

独立[设计审查](../delivery/2026-11-16-native-admission-dependency-design-review.md)需求／维护性均approve，仅限静态设计，无P1/P2；P3为上述调查时语态的交接澄清。审查时M5十文件已经冻结完整patch `fba1838ac6e7cb13cdbab9ec9b96e66cc38cdf8c5de3eb00c381f120ca050e1d`，不应据早期描述重新启动原批。原批实际38节点，37通过／1失败／639.04秒；失败为dispatch同步后来源反例读取缺ref，实施owner正在保留原现场定位。M5自己的fresh源码审仅批准限定接线静态范围，全片仍pending。新安装／自身模板／最终终核待验，真实完整hook无SDK mandatory仍开放；后继须使用M5修后最终固定产品，不能把这份旧patch或设计批准转授新候选。

Legacy矩阵中的requirements／所有platform文件完整identity反例只针对有版本descriptor的安装。无descriptor legacy继续原Python文件子集及原training选择规则，不借本片扩张历史校验范围。
