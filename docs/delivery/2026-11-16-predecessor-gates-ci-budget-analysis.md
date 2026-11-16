# M5 前驱／native gates 的 CI 预算有限调查

2026-11-16。仅新增本报告；未改产品、测试、CI或共享PLAN，未运行测试／collector、网络、安装、服务、模型、提交或推送。已读根AGENTS、PLAN、当前M5交付、父留存预算与再平衡记录。调查主树HEAD为 `debf6f96ed02620d22adc0ac6385c72641b3d53b`；其他owner的未提交记录保持原样。本报告是文档调查，不是实施或新组合通过认证。

初始建议为一个完整文件 `tests/test_training_preparation.py` 从group5移至group1。**该建议已由最终 r7／native-r5 的[四完整文件再平衡候选](2026-11-16-predecessor-native-ci-balance.md)替代**：最终实际净新增18项，真实collector2335和原selector重放已核，待fresh配置审查及自己的官方CI。以下保留原调查与单文件历史，不把当时5项新增预期转授最终组合。仍不拆文件、不删除或跳过保护、不增job、不加时，六组86文件、Windows all及原Linux20／Windows30分钟保持。

## 基线、已测结果与未知

父留存产品固定 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，已随准确公开候选debf6f9及此前两完整文件5→1配置发布。指定私有原件 `.ergora/checks/cycle-parent-request-retention/publication-r1/20261116T013147Z-summary.json` 官方HTTP200、准确head、push／attempt1、run43784344936，八job全success。group5整个job为17分31秒，原20分钟的账面余量149秒；group1为7分07秒，Windows23分48秒。整个job包括安装、verify、回归及上传，149秒不是pytest专享预算。成功只属于debf6f9，不能转授M5。

M5隔离树 `.ergora/worktrees/training-cycle-predecessor-gates` 的实现基线是上述1f57ca46；调查固定参照10文件patch `fba1838ac6e7cb13cdbab9ec9b96e66cc38cdf8c5de3eb00c381f120ca050e1d`。主树交付记六产品owner、四既有测试／fixture变更；主要新增或扩展保护均在group5的 `test_training_submission.py`，另有group2 controller反例断言维护。不能把隔离产品父提交的旧分组当最终主树分组。

限定读取现成日志与源：

|原件／范围|实际结果|成本解释|
|---|---|---|
|`cycle-predecessor-native-gates/exploratory-02.log`：原collect/reconcile及新增k1/k3完整前驱链|3 passed／55.20秒|含既有测试、fixture及当时探索输入，不能归为两个新增节点的纯增量|
|`cycle-predecessor-native-gates/exploratory-07.log`：完整原件容量reader|1 passed／55.87秒|M−1／M／M+1完整UTF-8＋LF边界，H／Budget／context／真正native关闭分支及纯-S认证；该既有函数扩展为更多串行工作，节点数不增加|
|`cycle-predecessor-native-gates/frozen-source-01.log`：23函数参数化38节点|37 passed／1 failed，639.04秒|原整批失败保留；dispatch同步后的source反例读取缺ref由实施owner修复，本调查不修改、不认证其修后结果|

初始静态调查曾把完整链函数的ordinal1／3两节点均算作新增，再加当时native同步fault三节点推断新增5；**这个分解不准确**，基线已有一个完整链节点。后述r4真实collector纠正了节点来源，不能沿用初始分解证明保护集合。容量reader扩展既有函数；实际新增数与完整归属应由冻结候选collector核实。这三类成本包含真实fixture安装、H／S子进程、原锁／fd／reaper、完整大raw读取与重复来源认证；其成本不能用断言条数推算。原批没有逐节点JUnit成本可据此分离，尤其不能把639.04秒当新增开销。没有最终源码或非editable安装整组合时长，没有M5官方CI，native实际hook无SDK依赖门仍另片开放；纯-S结果不能替代真实hook认证。

55.20＋55.87不能线性加到1051秒，也不能将旧文件76.380秒从官方job直接相减。候选输入、runner、fixture摊销和读取路径不同；连“149秒足够覆盖新增”也尚无证据。

## 有限整文件比较与一个建议

仅解析旧指定 `.ergora/checks/ci-training-shards/installed-py311-r1/group-5/ci-results/junit.xml`，沿父留存预算报告核身份；未递归扫描checks。该原件属于b6538cf0、539节点、suite2444.931秒；包含后来已移走的文件，不能代表当前group5。以下为完整文件testcase time合计（含JUnit归入节点的fixture），不是可搬走的固定远端秒数。

|当前group5文件|旧完整节点／秒|选择依据|
|---|---:|---|
|training_preparation|15／76.380|与b653逐字相同，本次核fixture闭包后选为单文件候选|
|task_budget|12／48.461|旧工作较小，本次不扩大闭包调查|
|training_runner|7／42.713|旧工作较小，本次不扩大闭包调查|
|training_runtime|26／46.019|正文已变，不优先使用旧成本|
|training_submission|111／1135.248|已增加测量、留存与M5，旧成本已失真，不建议整个大文件移入group1|

training_preparation直接导入training的experiments／registration与training_runtime的installation；前两者function scope，registration持有独立tmp_path的repo／state／config／runtime，installation为module scope的独立临时安装，可选择managed venv。preparation_input／stop_after亦function scope，故障替换由monkeypatch复原。导入提供fixture，不要求把所导入模块测试正文同组收集；module installation按请求测试模块实例化，不要求共享group5运行进程。静态未见必须与submission或runtime正文同组的共享状态，但仍须实测最终组合。

该文件raw SHA256 `bd7d1d9c106806c43f640f0a764a1a4fcfbfd018031a2ec8dcd3038233759935`，当前与b653逐字相同。选择它是一个文件就能分散有历史证据的现存工作，且目标group1已有实际余量；不是证明76.380秒能抵消新增成本。此前composition_tasks／services已不在group5，不能再算第二次节省。

当前JSON raw `5995dfe1bd13235475fbbfd79b2ff51dc2065f302924e465e4fa1474456241df`，六组文件数13／16／12／18／13／14。建议仅变为13／17／12／18／13／13，仍86唯一完整文件。若最终成本证据改变，重新评估，不预加第二文件。

## collector、归属及发布验收要求

固定修后实际最终产品／测试输入与合并后的当前分组，使用现有 `scripts/ci/run.py --collect-only` 和PhaseLog selector接缝，保留原／新JSON、collector完整node集、phase／JUnit／退出码及精确输入身份；不用新检查框架。先比较同一最终输入的搬组前后node multiset完全相同，六组覆盖无重复／遗漏，仅training_preparation全部节点5→1、其余归属不变；Windows all不变，不能靠Linux selector结果代替Windows执行。

父留存完整collector为2317节点，group1=355／group5=436，其余349／409／453／315。最终若仅冻结M5的五新增node，应为2322；这只是待核预期，修后变动／最终实际collector才决定准确数量。旧15节点同样不能硬编码替代当前文件完整收集；必须核无删除、新增集合逐node归属于真实新增保护，扩展容量reader仍在原node内。若最终仍15节点且仅加5个group5节点，映射预期group1=370／group5=426，条件不成立即重新对账。

不因本报告重跑原选集或无差别重跑六组。沿既定最终源码／非editable安装验证及必要受影响组合保存实际JUnit、phase、退出码与收尾。任何配置实施另沿原流程fresh独立审查；本调查文档不触发递归独审。新公开准确head自己的六Linux／Windows原时限终态，才认证最终分配可用。

## 根后续实际收集：仅r4，尚非最终配置验收

根将准确r4的853输入复制为独立collector根，仅把分组JSON换为建议配置，使用r4新非editable SDK的原 `scripts/ci/run.py --collect-only`。实际退出0／7.126秒，完整收集2322节点；selector真实重放组1=370／组5=426，其他组349／409／453／315。六组86个唯一完整文件保持，仅training_preparation的全部15节点5→1。候选JSON SHA256为 `326326a1249f009d149e8286e246b02c323ed6aa2d8b5e16e7e91aac397e2e47`，当前仍未提交，待最终候选收集及新fresh配置审查。

相对父留存2317节点，有两项**已有节点改名**：原完整链ordinal3由 `[controller_admission0-3-managed]` 变为 `[3-controller_admission0-4-managed]`（参数顺序／候选数变化），原source-sync无后缀变为 `[controller_admission0]`（显式出生配置）。逐项映射后无保护删除；原始node ID集合确有这两项移出／移入，不能写成字面ID全不变。净新增5项为四个native source／ROOT／clock／interpreter故障和一个ordinal1完整链案例，纠正初始“完整链2＋native3”的错误分解。

实际collector／节点差异／归属见ignored `.ergora/checks/predecessor-gates-ci-balance/comparison-r4.json`及同目录原件。此次只收集，没有执行测试正文、Windows或远端时长验收。之后自身模板又发现两个时序缺口，修后源码与测试将重新冻结；r4收集不转授后继，最终M5与native-v2组合须重新核自己的节点集合。

## 定位摘要

以上私有原件均位于ignored `.ergora/checks/`，未复制旧command.json或环境值。

|原件|SHA256|
|---|---|
|父留存官方013147Z-summary.json|`39675ba54f15fcbdac72cc8d4187b9acfc2450b5396ebc57ffc465581ea01a27`|
|旧group5完整JUnit|`54b6a172f1412621ab72632f869e10e1ce025ee1f57bb91c242fe356912ea52c`|
|M5 exploratory-02.log|`8ecd0152c9c3c3755c51f551f68d5b2e126b4ee284713df892dbcf5e1d047479`|
|M5 exploratory-07.log|`0ab6c892f6215f955d181590a4f247c0ed7634b20f6524be102286df0e1f0aa5`|
