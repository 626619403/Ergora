# 训练 CI 分组最终验收独立审查

日期：2026-11-16。Reviewer：fresh-context 独立 agent `ci_training_final_review`。未继承实施对话；依次读取项目规则、原始要求、固定 diff／源码、原始证据，再核计划、交付、旧静态审查与成本补充报告。使用 `maintainable-project-delivery`／`independent-review` 及 `ergora-codebase-quality`／`test-seams`、module-design、repository-style。本轮仅只读检查与无资源 Python JSON／AST／XML／摘要探针；没有执行测试、安装、网络、提交或修改候选。唯一写入为本报告。

## 当前结论与身份

**需求轴：固定 7ed77c9 的迁移、最终配置静态覆盖及 b653 同包完整安装 2／5 的测试正文行为证据 approve。维护性轴：approve，开放 finding 0。允许导入当前开发分支并普通发布，以取得该准确候选自己的官方 CI。** 新配置的本机完整组组合未运行，自己的官方全部 CI、Linux 整个 job 20 分钟及原生 Windows 仍 pending；本片预算目标尚不能标为完成，不自动合 main。

- 固定 baseline：`af176cf6e79adb9c6ef6f32946672bc77cdb89de`；最终候选：`7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`，隔离树 `fix/training-ci-shards`。前一冻结候选 `b6538cf0e5026f27c1c5983aa586926a666e4788` 承载本轮完整安装行为结果。两次检查时候选均 clean；首轮主树 HEAD `691809563c410cc1f9d93bc6f821b313f7a2772b`，主树的其他交付记账不纳入候选差异。
- 固定 diff 仅 `tests/test_training_submission.py`、新增 `tests/test_training_cycle_controller.py`、`scripts/ci/linux-groups.json`。产品、runner、pytest observer 和 workflow 无差异。
- 最终三文件 SHA256 分别为 `cdfeb4be11d583d3c9675cf224adfd3f64cbb81195c33b81139689bc49779915`、`c59e8e5d178fa252d639f99ad40630293169a05714102320232679c83e1cd2f3`、`186e719860ad0cde5ce01d88bfbe1013320395d860acb5434954b1f9b3360c92`。b653 的 JSON 摘要为 `298e4160010d20840f2152fb647e5f58eddfc43948fa92fa1c55d190164ec0e0`。

## 首轮 b653 独立检查所得

1. 直接从固定 baseline 的 Git blob 与候选读取源码，用 AST 仅定位完整原文：原 130 个顶层函数恰为旧模块保留 92 个、新模块 38 个，无交集、无缺失；所有函数含装饰器逐字相同。迁移为 37 个测试及独占 helper `admission_process`。恢复、并发、生命周期测试、预算、参数、平台标记与断言保持；无删场景或缩短窗口。
2. 新模块从 submission 显式复用 fixture 与 helper，不导入测试函数；依赖方向为 controller→submission→原 training／runtime／registration。原模块剩余测试仍真实使用 `controller_admission`、`cycle_candidate`、`controller_dispatch`、`cycle_operation_fault`，不宜为拆分复制或另立 owner。新文件对应 controller／candidate-root 的完整生命周期接缝，helper 的 `__file__` 仍解析同一 tests 父目录；不新增抽象框架。
3. 独立读取 `final-r1/` 的四份原 snapshot、request／result 与 plugin phase，而非执行会覆盖 verification 的脚本。Linux 2227、Linux 上 Windows 选择 2172 的完整 node Counter 仅归一迁移模块路径后同一；每份 snapshot 与原 plugin coverage 同一，收集退出均 0。所有节点 fixture 定义来源、scope、依赖／源码摘要及闭包顺序同一；受影响模块完整 markers 与所有节点 skipif 同一。Windows 证据是 Linux 收集，不能冒充原生 Windows 执行。
4. JSON 仍六组，文件数 `12 / 13 / 14 / 15 / 12 / 20`；86 路径唯一、存在，全部应用测试模块登记。实际 group 2 从 386→461、group 5 从 614→539，75 个迁移节点保持；原 runner 仍使用既有 plugin 选组。workflow 的 Linux 整个 job 20 分钟、Windows 30 分钟保持。
5. 安装原件 `installed-py311-r1/` 的实际 phase identity 为 Python 3.11.15、SDK 1.34.0。直接核实际 wheel SHA256 `081aab4594f8afa18505c3ec8a8b78ff98690510303a7041e3074af5fcab38cf`，663 个产品文件 source＝wheel＝site-packages，执行位同一；安装 dist-info direct_url 指向 wheel archive，无 editable 标记。参考原件为 283 文件 PASS。首轮 b653 的852个冻结产品／测试／脚本／示例输入摘要与执行位均相等；7ed77c9 只改变其中 JSON，见终核。本轮没有重新安装或另做依赖求解，不能扩大环境结论。
6. 完整安装 group 2 的原 request 使用固定树原 `python -I -B scripts/ci/run.py --group 2`，子进程仅 CI plugin／reference 加入 PYTHONPATH。原 phase selected 的 461 节点与固定 JSON 从完整 Linux snapshot 选出者精确相同；JUnit **460 passed／1 skipped／0 errors／0 failures**，suite 1520.806 秒、stdout 1520.84 秒，父退出 0／1522.575 秒，结束输入变化列表为空。setup／call 各 460 passed，唯一原 skip 为 Windows junction 测试，461 teardown 全通过，plugin finish exitstatus 0。
7. 自身原模板真实 Codex run `c5f1f6ca0d3944ccab3cad4685713bb0` 的原 result 为 approve；其原回复明确仅 supplied-source，没有认证私有 collect、完整安装、Windows 或官方预算。本审查自行读取上述原件，不将该模板结论转作运行证据。

`installation` 的原定义仍为 `tests/test_training_runtime.py:16` 的 module scope，拆模块会增加请求模块，普通／managed 构造及成本不能仅凭 fixture 摘要推成不变。phase 证明相应节点 setup／teardown 正常，未独立记录每次 fixture 构造，故不声称量得准确构造次数或零额外开销。完整组终态与进程身份收尾在下节分别认证。

## 成本与仅 JSON 后继的边界

直接读取 `public-run-r1/response.json`（SHA256 `69b5aa084b40d2c8f046c61113e1254dfd1cb4826b85e6a2df941c8f9f23cfd2`）：准确旧候选 478 的 group 5 completed／cancelled，job 1215 秒、native regression 1195 秒；其余六个 native 均 success。API 记录不能定位超时具体测试／phase；本机 b653 group 2 的 1520.84 秒也不能证明或反证新候选在 GitHub runner 的准确 20 分钟结果。远端开销包含安装、reference verify 等，不能把整个 1200 秒全给 pytest。

成本补充报告提出四项整文件转移：task_cancellation 2→3、reference_executor 2→1、training_release 5→4、task_external_status 5→0。它利用同轮已完成模块的实际成本选择迁移对象，保持既有模块边界、六组、runner 和所有测试，是克制且可审阅的方向，现已仅以 JSON 实施于 7ed77c9。没有采用跨候选成本相加来认证远端成功，也没有证据保证四次移动足以完成预算目标。

独立核四模块及 controller／submission 实际 fixture 闭包：session／package scope 只有 pytest 内置 `tmp_path_factory`，项目 installation 为请求 module 独立，registration／任务／训练状态由 function fixture 和各自 tmp_path 建立，monkeypatch 在 function 收尾恢复。task cancellation／external status 复用 task submission／registration，training release 复用 archive／training runtime；reference executor 在 tmp_path 中启动已有独立子进程。没有观察到依赖跨模块累计状态或需要特定同行模块先运行的具体 session 合同。原 runner 先收集同一全选集再过滤，也不因调组改变模块的 import 集合。因此当前没有实证理由要求仅 JSON 后继在本机无差别重跑六组，或新增一套浅层测试。

最终后继确实**只改 JSON 四文件归属**，产品、测试、fixture、runner／plugin／workflow 逐字保持；b653 完整安装 2／5 可保留为这些测试正文及拆分接缝的已跑行为证据。新配置另核了六组唯一／存在／完整归属、原 Linux／Windows 全节点、skip、fixture 语义和准确身份。它不能继承 b653 的组组合成功或成本：所有接收／移出组的新进程组合、资源收尾和原时限达标，均留给该准确候选自己的完整官方 CI。不能把后继 JSON 写成已本机完整跑过。出现真实 fixture／状态／清理失败时再按具体失败选最小重跑接缝。

## 完整安装、收尾与最终 JSON 终核

1. 直接重新解析两组原 JUnit／phase／父 result。b653 group 5 为 **537 passed／2 原平台 skip／0 errors／0 failures**，539 节点，suite 2444.931 秒、stdout 2444.95 秒、父退出 0／2446.666933 秒；setup／call 各537通过、539 teardown通过，plugin finish exitstatus 0。selected 与 b653 JSON 在完整 snapshot 中选出的539节点精确相同。两 skip 是原 native-Windows unsupported check 与 Windows backup junction；group 2 原460通过／1 skip保持。两组共1000节点均有终态，两份父 result 的结束输入变化列表为空；`complete-summary.json`与原件一致。此安装行为验收通过，不认证本机预算达标。
2. 独立解 `installed-py311-r1/cleanup-r3/records/` 的643份持久原JSON，重建245个完整身份及728处引用，逐身份、来源路径、JSON路径和原文摘要与 `result.json`精确同一。另只读重扫两原fixture根：22,453份可解JSON、14个不可解路径与记录相等，8个非普通JSON路径被跳过、无超过16MiB输入。重新读取 `/proc` 后仍244身份不在、1为不同进程，live_match＝0、unknown＝0。身份可能为故障测试的synthetic记录；这个结论只覆盖上述可解且记录完整身份的集合，不覆盖不可解记录、未记录后代或整容器。测试内回收断言与全部teardown通过另为行为证据。
3. 检查私有收尾脚本和前次中断说明：首次检查器读故障FIFO受阻，只终止自建检查器；第二次遇深层无效JSON，未获完整结果；第三次跳过非普通及不可解输入后才产终态。没有把前两次写成通过，也没有触及已退出测试的包／输入。原件持久副本允许本次独立复解。
4. 独立核固定 `7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220` clean；相对 b653 的唯一文件差异为 JSON 四项转移，且其原文与 `final-r2/linux-groups.json`、Linux plugin partition 的 `186e7198…`摘要一致。收集发生在 b653 HEAD 下唯一JSON工作区变更时；固定后仅该JSON入commit，现有静态原件与最终commit字节相等，不冒称收集开始时HEAD已经是7ed77c9。852项冻结输入当前恰只有该JSON摘要不同，全部执行位保持。
5. 独立从 `final-r2/` 两份 snapshot／request／result／phase重算：Linux2227、Linux上Windows选择2172完整节点Counter相对final-r1同一；全节点fixture定义／源码摘要／scope／依赖／闭包及skipif保持；snapshot与原plugin coverage同一。Linux实际group2选择399节点、Windows全选择2172节点均吻合；两收集退出0。六组覆盖节点数为 **349／285／399／415／315／464**，文件数 **13／14／12／16／13／18**，86文件各一次、存在、无未分配收集文件。原plugin摘要保持。此证据是Python3.12的源码collect-only，不替代Python3.11完整安装行为或Windows原生运行。
6. `initial-verifier-error.json`保留私有verifier将mapping直接传Counter的错误；`verify-balanced.py`改为mapping keys后只重算同一原件，没有重跑collect。本次未运行该写文件脚本，而从原snapshot独立重算，得到上述结果。该错误未改变产品、测试或收集节点。

## 准入与剩余验收

没有待修源码／配置finding。原迁移自身模板的approve仍只覆盖其supplied source；新增四项JSON归属由本次完整diff与静态原件独立终核，不扩写自身模板认证范围。上述证据足以通过本片导入与普通发布准入，不要求无实证风险的本机六组重复运行。主控应同步计划／交付到最终身份，导入后核精确差异，普通推送并核远端身份。

仍须**发布后准确联合候选自己的全部官方CI**验证新六组组合、其资源收尾和原时限；六个Linux job须在原整个job20分钟内，Windows保持原要求。旧478的成功组、b653本机通过、7ed77c9源码收集及源结构模板均不能代替该结果。未取得之前预算目标／正式发布验收保持pending；不认证本机后继组合、原生Windows或总workflow性能，不自动合main。其他树后继消费者的测试不纳入本片证据。

原件均位于项目 ignored `.ergora/checks/ci-training-shards/` 下的 `final-r1/`、`final-r2/`、`installed-py311-r1/`（含`cleanup-r3/records/`）、`self-review-r1-codex/`、`public-run-r1/`；计划入口为[本片计划](../plans/2026-11-16-training-ci-shards.md)，实施状态见[本片交付](2026-11-16-training-ci-shards.md)。

## 固定导入与最终自身模板短终核

主树已真实 merge 到 `5e48b9e80f301d4b16793f43008a3ffd1bd05f4c`，独立读取 Git 父提交为 `23316ea20f9361f054426ba881502ff75a620dce` 与已审 `7ed77c9c1eebc0e16c2f9024c62b0d4fd25b7220`。直接比较固定 merge 与7ed的 `src/ergora`、`tests`、`scripts`、`.github`、`pyproject.toml`，差异为空；两固定提交及当前工作区JSON摘要均为 `186e719860ad0cde5ce01d88bfbe1013320395d860acb5434954b1f9b3360c92`，与私有 `final-r2/import.json`一致。当前工作区仅另一片execution-consumers交付修改及未跟踪execution-product-review，不纳入本片待推内容。本次仅核固定身份与现有原件，没有重新扫描、安装或测试。

最终自身原模板r2已真实调用Codex，run `50b8dd70479041518c1dcaeab7ceced3`，32.761107秒、exit0、approve；独立读取 `self-review-r2-codex/summary.json`、`review.md`及该run原`result.json`，result摘要 `141f2e313967ca74109074462aa712c8b0275f020a1208fd753ceb5c342aeab1`与summary同一。其记录19完整文件／400,825字节、3继承资源、570,067字节stdin，input digest `d6bd654accbe916111ef5f8390352e3469785e9c6ab38dfed71549037a09462b`。原回复覆盖af176→7ed supplied-source，明确未独立认证私有原件、未执行测试，未认证新组组合／Windows／预算；本报告不扩大其认证范围。

**固定导入短终核：需求／维护性两轴approve，开放0；5e48b9e具备普通发布准入。** 源码与测试／CI身份承接本报告已审7ed，发布后仍须准确5e48b9e或明确后继联合候选自己的全部官方CI。远端身份与各job原时限尚待发布后观察，本地导入和最终自身模板不能替代它，不自动合main。
