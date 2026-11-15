# c1d M1b schema3 storage birth：独立源码审查

2026-11-16。Reviewer：fresh-context 独立代理 `cycle_v3_birth_source_review`，未参与本片设计或实现。先读原始需求、已接纳 storage-only 修订和实际差异，再读作者交付与原始检查材料。按 `maintainable-project-delivery` 的 independent-review brief，以及 `ergora-codebase-quality` 的 module-design、test-seams、repository-style 审查；已读根／源码／tests AGENTS、PLAN 和 component change protocols。本报告是唯一写入。

**源码需求轴 approve／阻断0；维护性轴 approve／阻断0。** 未发现所审冻结九文件中的可证实实现缺陷。这个结论只覆盖内部显式 schema3 出生、历史读取、本地 intent 和执行关闭的小片；整片验收仍待下述兼容证据补齐、安装、自身模板及固定提交终核。它不认证正式 V2、successor 或 c1d 总体完成。

## 准确对象

|对象|独立核得身份|
|---|---|
|原始范围|[M1b 计划](../plans/2026-11-16-training-cycle-v3-birth.md)，当前 raw SHA256 `39c2dec92aa185de5c832a216f947c516a637af8b5e878c561f20ff0926d9da0`；已读[设计审查](2026-11-16-training-cycle-v3-birth-design-review.md)的 revised `b2edb47f…` 与 D1 关闭范围，后续状态文字不当作新增功能授权|
|已批准父 wire|[measurement-wire](../plans/2026-11-16-training-cycle-measurement-wire.md)，raw SHA256 `ae42119677b842bf3a794226067e74c5fba5c7a01e7dbbd115421064a381a337`|
|产品基线|隔离分支 `feat/training-cycle-v3-birth`，HEAD `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`；准确九个既有文件改变，无未跟踪产品文件|
|完整冻结 diff|私有 `cycle-v3-birth/source-r1/frozen.patch`，raw SHA256 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`；实际 `git diff --binary HEAD` 逐字一致|
|完整 tracked source／tests manifest|同目录 `frozen-source-manifest.json`，raw SHA256 `0a8715f7643e4104c1c404204923919c05b2af51b681d423e560a2a241bc782c`；独立重算全部782项无漂移，九份 `frozen/` 原件也逐项匹配|
|作者交付|[交付记录](2026-11-16-training-cycle-v3-birth.md)，读取时 raw SHA256 `8e89e50248ddc9e34595608428e1953040bed1388517c5a5559fd02f203588f5`；仅作为待核主张与原件索引|

完整改变列表：五个产品 owner `src/ergora/{training_cycles,training_execution_protocol,reference_training_budget,reference_training_runtime,reference_training_worker}.py`；原测试 `tests/{test_training_cycle_controller,test_training_submission}.py`；原 fixture `tests/fixtures/{training_controller_service,training_executor_client}.py`。没有新模块、依赖、CI 分组、CLI／HTTP／UI、V2 类、stub、注册或队列启动。审查时主树另有未跟踪 M1c capacity 计划，未读取或修改为本片实现。

## 可达行为与最小边界

|实际 owner／调用链（行号按冻结产品）|核得行为与影响|
|---|---|
|`training_cycles.authorize_controller:513 → _authorize:525`|精确 int1/2，拒绝 bool；省略／1 仍 schema2，2 才 schema3，manual 仍 schema1。复用原 ID 锁及唯一 writer。输入／project／revision 与原授权在保留目录前校验；四来源捕获与唯一 clock 构造后，完整 authorization 校验先于 ID 保留。原 link/fsync 与不完整 ID 永久占用保持。|
|`_authorization:223`、`_measurement_sources:253`、`_controller:259`|schema 仅精确1/2/3；schema3 四键及完整 lowercase SHA 严格，完整 canonical 授权 SHA 拒绝额外字段／改形。四路径由 protocol 固定，capture 留在 cycles；沿原有界 ordinary/no-link reader 读包根字节，不读调用者或所选 installation。schema2 原 controller 对象不变，schema3 使用 v2 protocol／queue／ID prefix。|
|`_authorize:573`、`_load:270`、`_status:329`|既有 ID 先读原 cycle/auth，不再捕获 source／clock；精确保存版本拒绝双向模式替换。schema3 历史只核原 map／授权 SHA，不与当前代码比较；stop 与原普通空父锁沿原 storage 算法观察。ready 仍明确 `execution_authorized=false`。|
|`prepare_controller:413 → CycleAdmission.intent_record:697`|保留原六字段 workflow input／schema1 intent 和原 SHA 算法。source 比较在原 shared permission 内，位于创建或恢复 intent 前；漂移后 status 仍可读，但本地 prepare/recovery 拒绝。原 ready、预算、stop 与 fsync 恢复逻辑保留，不构造新的执行许可。|
|`_claim_controller:464 → _controller_ready:454`|schema3 在 attempt 发布前明确拒绝。已有 attempt／terminal 只读返回的旧语义未被改为重发。|
|worker `_cycle_operation:486`|原 cold inspect validator 会在 schema2 snapshot 检查前返回；新增 gate 在实际 H 装载并核完整 authorization SHA 后、activity binding／SDK／全部 mode 动作前拒绝 schema3，覆盖这条真实旁路。非 cold snapshot／operation-v1／SDK activity 仍保持原 schema2/v1 合同。本地 stop 仍走 `stop_controller`。|
|`BudgetedStart.source:259`；submission、BudgetAdapter create/lookup|schema3 gate 在 manual/controller 分派前，故 omitted-controller 不能落入旧 manual 路径。原 submission 复用 budget owner，无需新增版本分派。BudgetAdapter 对已有 job 的只读返回保留；缺 job 才进入原锁内 source/owner 最后准入，不获得 schema3 新建权。|
|`Execution.check/current → validate_context:1066`；`native_main:1120 → process → admit`|context 在 manual/controller 分派前拒绝 schema3。实际 native patch 在 executor 锁内先处理已有 result；无 result 时 callback 先于 started、Git/runner 及 managed attempt/ack。schema3 跳过 native 外层 schema2 permission，实际由 callback 的 context gate 拒绝；没有将外层分支误写成 schema3 已执行。原已存在 result 的早期读取保持。|
|protocol `cycle_workflow_type:32`；runtime `_controller_history:69`；worker dispatch|一个封闭映射服务 runtime 和 worker 两个实际生产文件；v1→原类型，v2→新类型名，未知值失败。六字段 input、queue、memo、fixed first/original run、attempt1、reset/continue-as-new 拒绝未变。v2 只读身份认证不生成 V2 执行器；生产 H 与 start claim 仍关闭。|

这些 gate 分别保护直接 claim、cold H、manual budget 和 native/context 的不同入口，未发现无必要的平行 writer、上层具体类型分派或重复框架。新增 source capture 是 cycles 自有的内聚私有算法；固定来源表及纯 type 映射放在已有跨解释器 protocol，未引入 State／SDK 或 measurement 模块导入。原 owner schema1/2、request/launch/attempt/ack/stopped 以及 intent 版本保持；独立 AST 比较确认25项 `GATE_SOURCES` tuple 和整个 `create_cycle_workflow` 不变。原 `successor_not_enabled` 及 ordinal0 门保持。

## 原始证据核对

本审没有运行测试、replay、服务、安装、网络、模型或训练。下表是读取实际 argv/env、manifest binding、stdout/stderr、JUnit 和保留 history 后确认的作者运行范围，不是本审重跑。

|原件|核得结果／证明范围|
|---|---|
|`controller-r4-command/result.json`、log、JUnit|returncode0；24 tests／0 failure／0 error／0 skip；pytest log112.54秒，wrapper113.12秒。含新旧 birth／mode、schema2/3 publication faults、不完整 ID、不重捕获 source/clock、drift/tamper、intent／预算／stop、direct claim、真实 cold S/H 与两个 manual 入口拒绝、真实 SDK codec v1/v2 read-only type 认证、旧 single-attempt/unknown 对账。|
|`compatibility-r4-command/result.json`、log、JUnit|returncode0；12 tests／0 failure／0 error／0 skip；pytest log46.64秒，wrapper47.31秒。含 schema1 CLI／丢回复、原 cycle/auth/ready/intent/attempt/receipt 字节保留、缺 installation 的 schema2-owner 历史 reader、ordinal1 拒绝、原 native lock/manual/result 语义与取消 eviction。owner1/2 双版本证据限制见下节。|
|native 新测试与原 executor fixture|真实 selected-native venv prefix 加开发环境既有 site-packages，经 `native_main → process → admit → validate_context`；比较原业务文件，拒绝后没有 started／attempt／ack／runner，再单独读 synthetic 已完成 result。仅 executor.lock 可创建。没有替换 admission callback；没有据此认证整条 callback SDK-free。|
|保留前置失败|`birth-r1` 为11 pass／1 fail，缺 native 模块；`native-sdk-r2` 为2 pass／1 fail，缺 SDK；`native-r3` 为2 pass。旧失败日志/XML 存在。最终 r4 绑定冻结 manifest，不能将前置 fixture 字节的运行追认为最终完整检查。|
|三份 retained v1 replay|结果各 returncode0、sandbox Replayer/eviction 完成。独立读取实际 history 核 raw SHA／bytes／events；分别82,086B/78、44,640B/45、48,561B/46。SHA 为 `dc7d9587…`、`3a5d086c…`、`1e9310ce…`，与 replay 原结果相同。终态分别 COMPLETED、CANCELED、COMPLETED；第三份实际含一个 ActivityTaskFailed，不能记成父 Workflow FAILED。只证明旧 v1 兼容，无 V2 replay。|

新增测试沿原 fixture 和真实持久状态转换，source drift 替换 reader seam 而不修改产品；native 拒绝检查覆盖真实 callback 顺序，SDK 使用实际 converter/protobuf。没有为了测试便利改有效配置范围或添加 CI 文件。仓库未声明 ruff/mypy 等检查配置，不据外部风格作 finding；本审静态 `git diff --check` 无诊断。

## 尚缺验收与最小补充

**E1：当前两组通过证据不能直接认证原 owner1/2 两种兼容。** M1b 计划验证第1项要求保留 owner1/2 的旧行为。实际 r4 argv/XML 没有执行现有 `test_cycle_managed_create_requires_its_live_owner_and_preserves_single_start_slot[1/2]`（`tests/test_training_submission.py:1030`）；已运行的 `historical_execution` 在该文件第65行只构造 schema2 owner。因此源码中的精确双版本 reader／25来源保持可由静态差异确认，双版本的本次运行证据仍不足。这是验收缺口，未发现实现回归，也没有将其计为源码阻断。

最小补充是在同一冻结产品上运行上述现有参数化接缝，保留完整 argv/env、源码身份、结果与原失败；它证明 legacy owner1/2 的 live create／只首个 start slot／无 execution-capability 行为，不能单凭它改称两种 SDK-free archived reader 均已测。若最终要宣称 owner1 的 SDK-free 历史读取已验证，须另给实际 reader 输入／输出的原证据。本审已通知主控，未代跑或改测试。

本轮还未收到本片新非editable wheel、实际 site-packages/import identity、安装检查、自身原模板、固定产品提交与同片终核；发布／准确自身 CI 另验。后继 M1c 编码、M2 source/ROOT 与四事实接受、M3 collect/durability、M5 最后前驱/native gates、M6 实际 V2／活动／注册／连续预算、M7/M8 真实两轮和收尾均不属于本次源码批准。不能将这些责任由 storage-ready、source 检查通过或旧历史 replay 代替，也不认证训练质量。

本审只写本报告；未修改产品、测试、计划或作者交付，未 commit／merge／push。本报告相对链接全部存在；`git diff --no-index --check /dev/null <report>` 无空白诊断，returncode1 为新文件差异状态，不记为 exit0。写后再核原 patch SHA 仍为 `a15d116c…`、782项 manifest 仍无漂移。最终源码结论绑定上述冻结 patch 和 manifest；后续 package／commit 验收需要重新核其准确身份并补充同片记录。

## 同片安装／自身模板／固定提交终核

2026-11-16。由同一独立 reviewer 限范围追加；保留上轮当时的缺证状态，不重写其结论。只读新增原件、安装目录、wheel、冻结输入与固定 Git blobs；未运行测试、安装、replay、模型、网络或服务，也未改产品／测试／其他文档。新原件集中于本片私有 `package-r1/` 和 `self-review-r1-codex/`，作者[交付](2026-11-16-training-cycle-v3-birth.md)已分别记录其范围。

**本片 storage-only 源码／安装验收的需求轴 approve、维护性轴 approve；开放0／0。E1 关闭。** 固定提交、安装、原模板输入均与所审九文件绑定，未发现新增源码或验收表述缺陷。该结论允许接续这一个 bounded slice 的普通导入／发布；实际合并、推送及准确自身 CI 尚未发生于本次核验范围，不能记为已经完成。M1c 与后继能力的责任不改变。

### 安装字节与实际检查

|对象|本次独立核得结果|
|---|---|
|新 wheel|原件 raw SHA256 `1ed714c885686d134033ac610ac0367fe275288d2ce45b8e6c4f1058dc801292`；`build-install-r1.json` 九步均 exit0，包括新 core／SDK 环境、安装、包核对和各自依赖检查。未重跑这些步骤。|
|完整产品|独立解读 wheel 并重读源码和 core／SDK 安装目录：各恰663个产品文件，完整 raw bytes 和执行位三方同一，无额外／缺失产品文件；两套 direct_url 均指向该 wheel archive，无 editable 标记。七个相关 owner 的原导入记录均为各自 site-packages。只有原五产品 owner 相对基线改变。|
|参考与依赖|独立逐项核包内 reference manifest 的283份原件，两套安装均无 SHA 差异；原参考版本2.2／zip身份保持。两份 dependency check 均 exit0；实际 core 无 temporalio 目录，SDK 记录版本1.34.0。没有用安装核对冒充后继执行时的 ROOT/source gate。|
|冻结输入|独立重算848项源码／测试／示例／配置／CI输入及663项产品输入的 SHA 和执行位，无漂移；179份 tests/examples 冻结副本也与原输入逐字一致。原782项 source manifest 仍无漂移。|
|`installed-controller-r1`|实际新 SDK Python3.12、`-I -B`、无 PYTHONPATH、cwd 为冻结 test-inputs；command/result、stdout/stderr、JUnit一致。24 tests／0 failure／0 error／0 skip，stdout 24 passed、61 deselected、142.11秒，driver143.50秒。选择与源码 controller-r4 相同。|
|`installed-compatibility-r1`|同一安装及隔离方式；14 tests／0 failure／0 error／0 skip，stdout14 passed、115.12秒，driver116.57秒。原12项保留，JUnit明确新增 legacy `[1]` 和 `[2]`。|
|`final-inputs-r1`|读过原 driver 与完整 child `-c` 文本：实际 installed core 以 `-I -S -B`、10秒上限运行，returncode0、stderr空，0.106秒；stdout给出 site-packages 的 protocol 路径。合成 owner1／2 均无 execution request，schema2 capability=null；真实 `ExecutionRecords.load/observe` 返回 not_requested、execution_authorized=false，原 raw 保持，State／SDK／YAML／jsonschema 未导入。|

**E1 的具体闭合：** 新安装兼容组执行现成 `test_cycle_managed_create_requires_its_live_owner_and_preserves_single_start_slot[1/2]`，验证两种旧 owner 的 native create／原 start slot、无 capability 不得 execute、重试不替换意图或多发。实际 argv 和 JUnit 均有这两个参数，故补齐上轮缺失的完整 legacy 行为接缝；没有改测试或源码来通过。另有 core 空链 reader 原件明确给出两版本 SDK-free 的窄范围，完整有 request 的 owner2 历史仍由原 fixture 验证。作者现在区分这三种证据，没有把空链或含开发依赖的 native callback 说成整条 native SDK-free。上轮源码12pass本身的原范围不追溯扩大。

### 自身原模板输入与实际结果

只读核 `commands.json`、composition／manifest／request、实际 stdin、State 的只读 `agent_runs` 记录、原结果及 scope。实际模板为 `ergora-structure-review@1.0.0`／原 `ergora-structure-reviewer@1.0.0`，requested binding 为 claude-code、实际 binding 为授权回退 codex，原 run `98208d547ed74dafa38ec27152c1dabe` succeeded／returncode0；外层记录45.671秒。没有将本次回退记成 Claude 成功或不同后端的独立运行。

独立重算实际 stdin 为778,400B，raw SHA256 `9f474fb37880fb0475e3cddac405b4b0c968c4a49cfa2439b8633a1e6df92ed5`；input、实际 run stdin 和 protocol prompt 三份逐字一致。17份 scope 全文合计613,678B，各自 raw SHA 与保存原件相符且完整包含于实际 task／stdin；原基线 cycles/protocol 两份完整正文及准确九文件 patch 也完整在 task 中。全部三项 inherited resource 的完整 text 在实际 stdin，无截断。这证明传入字节，不证明模型理解或额外 workspace 检查。

原 result raw SHA256 `e7210aaf8dd8e87364660b15b59fffa7f05dd92f4792c69572b84e3f3a7a973e`，与实际 State run 结果逐字一致，decision=approve。原回复认为职责归属、封闭映射、schema3 关闭与已有 result 读取保持，没有具体结构 finding；同时明确只审提供文本、无 workspace 访问、无独立运行／包验收，native callback 不证明 whole-native SDK isolation。本审将它作为已真实执行的自身模板证据，没有拿模型结论替代以上独立源码和包核对。

### 固定产品身份与剩余范围

审查过程中主控固定产品提交为 **`67ab9b4e446527fd27a61eff1aa6acb8d24feb01`**，其唯一父提交准确为 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`。独立核 Git：工作树 clean；基线至提交恰原九文件、352 insertions／34 deletions；`git diff --binary <baseline> <commit>` 与原 frozen.patch 逐字一致，raw SHA仍为 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`。因此安装与模型运行绑定的原源码字节没有因 commit 改变，不需据状态记账重跑无变化行为。

本片自身仍待实际普通导入、公开文档发布和准确 head 的自身 CI；本审未认证它们完成。主控提及同 wheel 的 M1c-T 旧 transport 选测属于另片，不是本次 M1b 必要证据，本审未将其纳入批准。正式 V2／活动／注册、measurement acceptance、collect、ROOT/source 最后 gate、successor／ordinal1、真实两轮／训练／GPU质量均仍未开放或未验证，继续按原分片计划实施和独立验收。源码、安装与原模板的本片验收已可闭合，不能据此提前关闭这些后继职责。
