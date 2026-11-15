# 训练回归 CI 最小迁移

日期：2026-11-16。实施基线 `97a0bbfae9687c15927f1437a374cd070baf0a94`，隔离分支 `fix/training-ci-shards`。b6538cf完整安装group2／5均已通过，共997通过／3原跳过；记录身份已收尾。四文件仅JSON再平衡已实施，静态收集和最终独立复核接续；未导入主开发树或推送，后继自己的官方组合执行／预算另验。

`test_training_submission.py` 中独立 controller 准入、停止、固定历史恢复和 candidate root 生命周期共37个测试函数（75个参数展开节点）原样迁入 `test_training_cycle_controller.py`，只将新模块登记现有 Linux group2。原 submission 的其余测试保留 group5。完整函数、装饰器、参数、预算与断言未改；不改变产品、runner、观察插件、workflow、六组数量和超时。

## 接缝与 fixture

迁移集合为全部原 `test_controller_*`、`test_cycle_controller_*`、`test_cycle_candidate_*`。它们分别保护出生同意／原 clock、父共享许可排空和停止持久性、一次 attempt／unknown 只对账，以及独立 candidate root 的 handoff／取消／后代清理。仅它们使用的 `admission_process` helper 同时原样迁移。

`controller_admission`、`cycle_candidate`、`controller_dispatch`、`cycle_operation_fault` 仍被原模块剩余 preparation／stop／SDK 测试使用，因此保留原 fixture owner。新模块显式单向导入上述 fixture、`cycle_selection`、`service`，以及闭包所需 `prepared`／`experiments`／`registration`／`installation` 和原 helpers；没有导入任何测试函数，没有双向依赖或 fixture 副本。130个原顶层函数现为旧模块92个、新模块38个，逐函数包含装饰器的原文全部相等。

原 `installation` 仍为 `test_training_runtime` 定义的 module scope。pytest 按请求模块缓存，拆分增加一个请求模块；普通与 managed 参数各自的构造／销毁次数可能随 pytest 调度改变。收集已核 fixture 定义来源、源码摘要、scope、依赖参数及完整闭包顺序逐节点相等，未将它改为 session scope，也未声称安装构造成本不变。完整安装组运行须核实际 setup／teardown 和进程收尾。

## 收集证据

使用已有 SDK Python 环境和本片源码 `PYTHONPATH` **仅收集**，保持原 `scripts/ci/pytest_phases.py` 为分组／覆盖检查入口。独立私有 snapshot 插件只观察原 items 的 markers 和 fixture 定义，不改变 items／分组；前后基线真实 nodeid（包含参数 id）及 diff 均已保存。仅将新模块路径归一为原路径后比较完整 Counter，零增加／减少／重复。

|范围|迁移前|迁移后|实证|
|---|---:|---:|---|
|原 Linux 全选择|2227|2227|完整 node multiset 相等；75节点换模块|
|Windows runner 的 tests＋contracts 选择，在 Linux 收集|2172|2172|完整 node multiset 相等；75节点换模块；不是 Windows 原生验收|
|Linux group2|386|461|原 plugin 实际选择，增加75节点|
|Linux group5|614|539|迁前从原完整覆盖＋固定分组核算，迁后原 plugin 实际选择，减少75节点|

两个选择范围中，受影响新旧模块的全部 markers（含 parametrize）逐节点相等；所有节点的 skipif markers 相等。所有节点 fixture 定义源码摘要／scope／依赖及闭包顺序相等。原平台装饰器和函数内平台 skip 随函数原文保持；没有模拟 Windows 运行平台。无 collection error。六组文件数现为 `12 / 13 / 14 / 15 / 12 / 20`，86文件唯一、存在，所有应用测试模块已登记。新模块全局符号解析没有缺失，`git diff --check` 通过。

私有原件位于仓库 ignored `.ergora/checks/ci-training-shards/`：`before.diff`（初始空 diff）、前后 `snapshot.json`／`phases.jsonl`／`stdout.txt`／`request.json`／`result.json`，以及 `after-tracked.diff`、`after-new-module.diff`、`moved-functions.json` 和 `verification.json`。`verify.py` 比较真实节点／fixture，并逐函数比对原文；AST 只用于定位原文范围，不替代收集。

可复现编排命令（在主仓库运行；脚本内 request 保存实际解释器、源码树和完整 pytest argv）：

```bash
python .ergora/checks/ci-training-shards/collect.py before linux 2
python .ergora/checks/ci-training-shards/collect.py before windows-selection
# 实施迁移后
python .ergora/checks/ci-training-shards/collect.py after linux 2
python .ergora/checks/ci-training-shards/collect.py after windows-selection
python .ergora/checks/ci-training-shards/collect.py after-group5 linux 5
python .ergora/checks/ci-training-shards/verify.py
```

上述 before 目录不可覆盖；保留其原始 baseline 收集。原始 pytest 命令使用 `-p pytest_phases -p collect_snapshot --collect-only`，Linux 增加原 portable／AdapterTests／runtime 选择，分组命令带 `--ci-group 2` 或 `5`。`collect.py` 明确标注 source collect-only；它不是 `run.py` 的 installed-product 执行结果。初次 marker 比较发现无关模块 set 的 repr 顺序因解释器 hash 随机化不同，保留原采样；最终仅对受影响模块比较完整 markers，对全选择逐节点核平台 skipif，未改测试。

## 冻结身份与待验边界

|实现文件|SHA256|
|---|---|
|`tests/test_training_submission.py`|`31ad45584fa959e9b792a2b20c1e9598b580ac2e4f70f98d49109a4a649e0681`|
|`tests/test_training_cycle_controller.py`|`c59e8e5d178fa252d639f99ad40630293169a05714102320232679c83e1cd2f3`|
|`scripts/ci/linux-groups.json`|`298e4160010d20840f2152fb647e5f58eddfc43948fa92fa1c55d190164ec0e0`|

## C3：Python3.11新安装完整组验收

以下为**运行启动时的记录**，终态见末节，不代表远端预算达标。使用home内已有CPython3.11.15新建独立venv，安装同一wheel081aab45及CI所用完整`[dev,web,gepa,temporal,task-mcp]` extras；48依赖兼容，SDK1.34.0，实际`site-packages`663产品文件／执行位source＝wheel＝site，283参考通过。未改用户主环境，未装系统包；此前r3的Python3.12服务验收与本次3.11各自记账。

两个独立pytest进程从固定clean b6538cf树运行原`python -I -B scripts/ci/run.py --group 2/5 --output ...`，原runner继续只将CI plugin／reference加入子进程PYTHONPATH，不把应用src放入搜索路径。启动前保存所有测试／脚本／示例／产品输入摘要与执行位，结束后核未变；无新增skip、xdist、deadline或缩预算。每组保留原JUnit／逐phase／完整stdout、父实际命令和退出码。

本轮原件位于ignored `ci-training-shards/installed-py311-r1/`，新环境位于同级`venv-installed-py311-r1/`；`candidate-inputs.json`、package manifest／参考核验、`run.py`、两组`command.json`与`ci-results/`可恢复在途状态。完整组结束后再核fixture新增module构造、所有终态／资源与实际耗时，交原独立reviewer复核。全库、原生Windows、远端20分钟限制均不由此在途记录认证。

这三个文件现已冻结供新的独立 reviewer 检查。没有执行测试正文、安装、服务、网络或全 suite；没有测量当前组时长，也未证明远程20分钟预算。主控后接同一新非editable安装的完整 group2／5、原 JUnit／phase／退出及进程清理，再记录 fresh 双轴审查和候选自己的官方 CI。Windows 的原生 skip／提前 skip 执行与安装 fixture 生命周期成本仍属未验范围。

## 固定候选后继合入与 final C2

迁移片已固定为 `5e953a1`，fresh reviewer 静态需求／维护性两轴 approve、开放0。其后合入服务 fixture 后继 `af176cf6e79adb9c6ef6f32946672bc77cdb89de`，当前 CI 固定候选为 `b6538cf0e5026f27c1c5983aa586926a666e4788`。服务后继将未迁移的正常 SDK handoff 测试显式设为原 fixture 支持的 controller control30；原7秒在真实新包运行中合法超时，主控另存其独立诊断及冻结后单项通过。本片不将旧97a0收集作为合入后同一性的唯一证明。

final C2 以服务树完整 `af176cf6e79adb9c6ef6f32946672bc77cdb89de` 为 before、CI树完整 `b6538cf0e5026f27c1c5983aa586926a666e4788` 为 after；两树起止均 clean。使用已准备的 r3 SDK 解释器重新走原 CI plugin 的源码 collect-only（最多两个收集并发），新原件独立保存在 `.ergora/checks/ci-training-shards/final-r1/`，旧97a0采样未改。

|final C2检查|结果|
|---|---|
|Linux完整选择|前后2227节点，归一迁移路径后完整 multiset 相等|
|Windows runner 选择，在Linux收集|前后2172节点，同样 multiset 相等；未作Windows原生执行|
|迁移节点与原文|仍为75节点／37测试＋1 helper；对af176cf逐函数含装饰器原文全部相等|
|Markers|受影响模块全部 markers 逐节点相等；全部节点平台 skipif 相等|
|Fixture|全部节点的定义源码摘要、scope、依赖参数和闭包顺序相等|
|六组注册|唯一／存在／应用模块全登记；`12 / 13 / 14 / 15 / 12 / 20`|
|group2／5节点归属|完整实际 coverage＋固定分组核得386→461／614→539；两侧Linux原plugin group2选择均成功|
|原收集终态|四次collect全部退出0，未执行测试正文|

原始 marker `repr` 比较另有44个无关节点受 set 顺序／函数内存地址影响；其全部原件保留在 `*-raw-marker-repr-differences.json`。这些测试文件在 af176cf→b6538cf 没有差异；最终 marker 结论明确限定为受影响模块完整 markers 与全节点平台 skipif，未把 `repr` 地址当作语义变化。

实际重放命令为 `python .ergora/checks/ci-training-shards/final-r1/collect.py` 与 `python .ergora/checks/ci-training-shards/final-r1/verify.py`；每次完整 pytest argv／源码 PYTHONPATH／解释器／身份／原 snapshot／phases／stdout／退出码均保存在对应目录。收集使用r3环境并不替代r3非editable安装行为认证。未修改产品、测试、分组，未commit／push；完整安装 group2／5及实际成本仍由主控后接，未认证远程20分钟预算。

最终三个实现文件 SHA256：

|文件|b6538cf SHA256|
|---|---|
|`tests/test_training_submission.py`|`cdfeb4be11d583d3c9675cf224adfd3f64cbb81195c33b81139689bc49779915`|
|`tests/test_training_cycle_controller.py`|`c59e8e5d178fa252d639f99ad40630293169a05714102320232679c83e1cd2f3`|
|`scripts/ci/linux-groups.json`|`298e4160010d20840f2152fb647e5f58eddfc43948fa92fa1c55d190164ec0e0`|

## C3首组终态与自身模板

固定b6538cf的新安装完整group2退出0：**460 passed／1 skipped／1766 deselected，pytest1520.84秒，外层1522.58秒**。所有461个teardown通过，无setup／call失败；全部冻结输入摘要不变。原始JUnit、逐phase、stdout及父退出保留，不把本机25分20秒写成远端20分钟达标。逐phase归属中controller模块约798.51秒，原task_cancellation约390.00秒、reference_executor约117.29秒；这些是同一候选／环境的已测阶段成本，未分离精确fixture构造次数。group5仍运行；待结束后一起核完整行为、资源及分配，不删保护或调整超时。

Ergora原`refactoring-quality`／`ergora-structure-review@1.0.0`已在同一安装环境真实调用Codex：45.82秒、approve，run=`c5f1f6ca0d3944ccab3cad4685713bb0`，input digest=`e450facbfbf9e896ee874de84f8a7488197fe2942ef5cf8534773e52116d7f79`。19个完整文件393,670字节、完整diff和三份继承资源进入560,919字节stdin；原结果SHA256=`13123029ad40b5ca83740c86b56b9a1be7cbdd6545f38d8b38877f3c644bc60f`。原件`self-review-r1-codex/`保存命令、完整prompt、输出和结果。审查认可单向fixture依赖与原文迁移，明确module级安装额外成本及仅supplied-source范围，不认证私有收集、完整安装、原生Windows或官方预算。

## C3完整终态、原件与有限再平衡

固定b6538cf、同一Python3.11.15非editable安装，两个完整原组均退出0：

|原配置组|真实结果|pytest／外层秒数|完整teardown|
|---|---|---|---|
|2|460 passed／1原平台skip，1766 deselected|1520.84／1522.58|461 passed|
|5|537 passed／2原平台skip，1688 deselected|2444.95／2446.67|539 passed|

全部1000个所选节点均有终态，无setup／call／teardown失败；两外层结束时冻结输入均无变化。3个skip分别是Windows junction、Windows native unsupported check、Windows backup junction的原平台条件。`complete-summary.json`由原JUnit／phase重算，不代替它们。没有将本机40分44秒或25分20秒认证为GitHub的20分钟达标。

收尾只读检查在两组退出后进行，未信号任何测试／产品进程。两个原pytest fixture目录的22,453份可解JSON中取得245个不同的完整进程身份、728处引用：244不在／1已为不同进程，当前原身份live_match=0、unknown=0。含身份的原JSON逐字复制到home持久ignored `installed-py311-r1/cleanup-r3/records/`，完整结果在同级`result.json`。这是该集合的身份观察，包含故障测试的synthetic身份，不是整容器扫描或未记录后代的普遍证明。原teardown及测试内回收断言另保留为行为证据。

私有检查脚本首次读到故障fixture的FIFO后受阻，仅终止本次自建检查器，保留部分副本与原因；第二次排除非普通文件后遇到故意深层无效JSON，未产终态；第三次明确跳过这两类输入并保留无法解析路径，才取得上述收尾结果。前两次不记为通过，不改变原组已完成的测试、包或输入。

按[成本补充](2026-11-16-ci-training-shard-cost-followup.md)仅调整JSON四文件归属：task_cancellation 2→3，reference_executor 2→1，training_release 5→4，task_external_status 5→0。六组文件数变为13／14／12／16／13／18，全部86文件仍各一次。相对b653只此JSON变化；产品、测试、fixture、runner／plugin／workflow逐字保持。完整2／5是原b653配置的行为结果，不是后继新组组合的本机成绩。新配置的完整收集、固定身份、独立终核与自身官方CI分别后接；官方全部job仍须满足原时限。

JSON后继已固定`7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`，工作树clean；groups SHA256=`186e719860ad0cde5ce01d88bfbe1013320395d860acb5434954b1f9b3360c92`。`final-r2/`新收集两次均退出0，Linux2227／Windows选集2172的node multiset与b653逐个同一，fixture来源／scope／依赖／闭包及全平台skipif保持；六组Linux节点349／285／399／415／315／464，原plugin实际选中group2 399。相对原852冻结输入只有JSON不同，产品／测试字节未变。Windows仍是在Linux收集，未冒称原生执行。

私有验证器最初误用`Counter(mapping)`，把snapshot字典值当计数而失败；修成`Counter(mapping.keys())`后仅重算同一原snapshot／phase，没有重跑或改写两次收集。`initial-verifier-error.json`、原request/result、`collect-balanced.py`及`verify-balanced.py`保留方法和修正。最终独立审查继续直接读取这些原件，不以作者验证器通过代替独立判断。

最终自身原结构模板对af176→7ed完整diff／19完整文件400,825字节真实调用Codex32.76秒approve，三资源与完整任务实际进入570,067字节stdin；run=`50b8dd70479041518c1dcaeab7ceced3`、input digest=`d6bd654accbe916111ef5f8390352e3469785e9c6ab38dfed71549037a09462b`，原结果SHA256=`141f2e313967ca74109074462aa712c8b0275f020a1208fd753ceb5c342aeab1`。`self-review-r2-codex/`保留原prompt／回复／命令，只认证supplied source。[fresh最终终核](2026-11-16-training-ci-shards-final-review.md)独立重算原件后需求／维护性两轴approve／开放0，允许固定7ed导入当前开发分支并普通发布；新组合与准确候选自己的全部官方CI／原时限仍未认证，不自动合main。

真实导入merge=`5e48b9e80f301d4b16793f43008a3ffd1bd05f4c`，parents为主控文档checkpoint23316ea及已审7ed77c9。与7ed的`src/ergora`、`tests`、`scripts`、`.github`和`pyproject.toml`差异为零，groups SHA186e7198保持；`final-r2/import.json`保存原Git观察。主树另有执行消费者agent尚未提交的报告，不纳入本次导入／发布；其代码仍只在专属树，不能混作本轮CI结果。最终身份终核后普通推送当前开发分支，准确官方run另记。

## 普通发布与准确CI

已普通推送当前开发分支`refactor/architecture-foundations`的`86356927cd88750717bb910502e3f7bd66aa41ba`，随后`git ls-remote`核精确远端同一；未强推、未合main。该提交仅在已终核merge5e48后增加状态文档，产品／测试／CI同7ed保持。新官方run [43747795571](https://github.com/626619403/Ergora/actions/runs/43747795571)精确SHA8635692、push／attempt1，最新观察in_progress、结论null。不能借旧478、b653本机或仅收集认证新配置成功；最终六Linux／Windows及原时限仍待该run自己的结果。推送／精确远端与API响应原件保存在ignored `ci-training-shards/publication-r1/`。

后续官方API `run-r3`／`jobs-r3` 实际HTTP200（UTC 2026-11-15 18:58）：同一准确SHA、push／attempt1，plan及全部六Linux组已success；group5从18:37:37至18:55:04，为17分27秒，group2为9分40秒，均在原20分钟内。Windows仍in_progress，整体conclusion=null；本轮不提前关闭全部官方CI门槛。原完整response和摘要保留在上述私有publication目录。

最终 `run-r5`／`jobs-final`／`windows-final` 官方HTTP200：同一run已completed／failure；全部六Linux success，Windows整个job26分18秒、应用回归失败，但其后PowerShell5.1安装／升级及观察件上传success。官方check annotations原文为 **1190 passed、976 skipped、6 errors、16 subtests passed／1459.85秒**；六错均来自两个Linux-only SDK测试在setup阶段先进入native training submission，尚未到函数内跳过。不是本次Windows超时，也不是安装失败。完整logs未取得，本机`gh`未安装；事实来自官方job steps和公开check annotations，不冒称读过全日志。原件为同目录`windows-annotations-response.json`等。最小后继仅给这两个原测试增加提前平台mark，沿[独立小片](2026-11-16-windows-sdk-fixture-skip.md)核六参数节点及实际fixture跳过边界；原失败不改写，新候选需自己的官方CI。
