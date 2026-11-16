# Native admission source-v2：依赖隔离实施

2026-11-16。状态：已接纳静态设计，开始独立源码片；尚无新产品冻结／安装／真实无SDK hook验收。本片不改M6效果、旧ID或M5仍开放的mandatory。

依据[设计](../plans/2026-11-16-native-admission-dependency-isolation.md)（raw SHA `3ab1a21f7f2dff70e6b4c8a6cfe4c25cba267c438e70ec650eef8709dbf4000c`）及[fresh独立设计审查](2026-11-16-native-admission-dependency-design-review.md)，需求／维护性approve、开放0。特别保留无descriptor legacy的原Python子集／training选择规则；完整requirements和全部platform身份仅适用于有版本descriptor安装。

准确源码基线为M5候选 `a1ff3389c004fbe19ed2529743980071d395b4d1`，唯一父 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`；它只是固定源码，不等于完整M5已通过。独立分支 `feat/native-admission-dependency-v2`，worktree为 `.ergora/worktrees/native-admission-dependency-v2`，从该提交建立且开始时干净。原M5工作树、在跑安装验证／自身模板与主树source不动。唯一交付记录在本页，PLAN／fresh实施审查／新非editable安装及自身模板由根协调。

重新核到两族caller仍是：原 `training_executor → training` 本地路径／Binding；原training.cli的run-local与approve两处真实client.load_experiment。实施产品仅新v2 patch/json＋reference/protocol/cli五文件，另最小用户说明docs/TRAINING及必要现有测试／fixture。v2executor须与v1逐字同SHA；training只删顶层client import及两处分支局部import，不复制loader。协议表按各自descriptor精确25项，旧owner纯shape与当前live source分离。保留M5 source/ROOT复核、native阶段gate、sys.prefix/core路径身份、锁内result早读和schema3关闭。

验收先沿现有reference/descriptor/capability接缝做轻量检查；在根在跑38节点结束并协调后，才运行较重native/subprocess序列。必要证据是：v1真实拒SDK原反例与v2完整native_main/context/chain到callback；纯-S reader另记；旧history/已有result早读；两个原CLI调用真实loader的校验语义。拒导入hook必须先于首次executor import，不fake SDK/sys.modules/sys.prefix/verifier。真实core／SDK非editable包与fresh审查另行绑定最终候选，不以源码结果替代。

私有证据仅用 `.ergora/checks/native-admission-dependency-v2/`（目录0700、文件0600）；不保存环境值／凭据。以下将顺序追加实际改动、原失败／修后结果、完整tracked+untracked冻结与未验项。本片未commit／push。

## 第一批轻量身份检查

五产品文件已接入：v2完整patch直接从原base应用，executor保持 `feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`；新增training override为 `c1a42acd91c3f320fe4c2c3d26728de7d0abc246474fad444be50c5356f5e086`，v2patch为 `16743abddf26d6ca67ef55053530a4c80950eb994a4e4cbfef6965c11b401068`。reference内纯raw解析由原安装核验与capability出生/复核共用；捕获descriptor必须逐字等bundled声明，并围绕完整安装核验重读同raw。capability仅在原owner出生时采值；历史shape helper不读安装。两版各25来源表只替换descriptor键，M5阶段gate未改变。docs/TRAINING新增显式v2选择和v1真实SDK依赖边界，不宣称训练全程无SDK。

源码轻量 `reference-r1`：**16 passed／17.35s**，另6项未选。使用原开发Python3.11、明确PYTHONPATH=该隔离src；覆盖原283校验、v1保持、legacy requirements变更仍按原Python子集接受、v2训练覆盖与descriptor错配/格式拒绝、各版本25项/混表/缺额外项/未知版本、旧capability移走安装后纯shape可读与live来源拒绝、出生后descriptor raw漂移拒绝、原中断准备及两个显式版本CLI。日志/JUnit位于私有前缀，不是非editable安装或真实native callback认证。

根通知M5原模板实际request-changes，指出native解释器最后可用性需补检查；原owner正在真实复现及修复并将给r3 delta。本片不代修，也不把a1ff或上述检查称为最终来源验收；等待原delta并保持其最后门，再冻结新候选。较重native序列尚未启动。

## 继承M5 r3最后门与真实源码入口

已直接核根给的r2→r3 delta：5,580B／SHA `aab2b4f87788935b3d59c30a3503320d9693e81de3b635c8777d7e3a65cf0068`，仅原Execution／protocol／test_submission。两份不冲突文件先git apply --check再精确应用；protocol手工保留原同义两行 `native_python.is_file` 于validate_sources末尾，不覆盖本片严格版本／raw校验。M5原七项r3验收由根持有，本片未重复运行。根可能还给一处仅test窗口的r4 delta，尚待后继同步；基线HEAD不动。

源码最小组 `native-small-r1` **6 passed／20.04s**：两CLI分支在SDK环境调用原client.load_experiment，非法Binding由原loader拒绝；合法run-local到原确认SHA门，合法approve经原phase核验保存原approval，仅替换无关远程query/send叶子。独立无SDK解释器能导入v2 training，并在真正client使用处明确报缺temporalio；未fake loader成功。旧v1／新v2 history移走安装后，原纯-S reader读取完整records，sources独立报不可用；原schema3已有result早读分别在旧SDK与新禁SDK路径保留，无新attempt/ack/started。

源码完整容量入口 `native-capacity-r1` **2 passed／125.63s**，只运行现有test的v1和v2两node，未重复其他M5矩阵。v2使用所选新无SDKvenv正常`-P`启动，first-import前拒State/jsonschema/YAML/Temporal hook，真实native_main的sys.prefix/core四路径身份不变；实际callback读到完整9,999,999B及10,000,000B原前驱后明确到原schema3关闭，`executor_sdk_loaded=false`。纯`-P -S`认证另存 `authenticated=true/loaded=false`。未伪造sys.prefix、sys.modules或verifier；原callback/锁/记录阶段与原source／ROOT重核保留。

v1在同样禁SDK入口真实returncode1，trace保持 `training_executor → training → perf_temporal.client → temporalio`；原允许SDK路径则 `loaded=true` 后到同一关闭分支，不能把v1称为无SDK通过。两版都实际验证M−1/M/M+1、多字节LF、合计容量，以及原source／四measurement／manifest／ROOT漂移拒绝，无started/result/runner。原ack/interpreter缺口由M5的r3红绿证据负责，本片仅保留其真实最后门。

本轮源码／fixture的初次完整tracked+untracked探索冻结为 `complete-source-r1.patch`：47,166B／SHA `fd1b8c8b8a88bbd407e85d67c38899d9d7bc8fc97c0b02a3b0e58d1b48af9701`，12文件，其中一份Execution及原test变更属于继承r3，native-only差异最终由根相对最终M5候选分离。`source-freeze-r1.json`逐文件记bytes/SHA/执行位，`inputs-r1.json`保留786项src/tests/pyproject/合作规则/用户说明输入，SHA `144d4077e9edccb44a26d2752adafa56f56cef8332ce3d9d2b87a8d1c35ae32d`。此为当次探索集合，不借用根853项输入或663产品身份；最终冻结将另记完整范围，r4不得偷换当次输入。

上述均仅源码结果，真实native执行关闭仍在；新非editable core／SDK、实际site-packages／完整资源identity、自身原模板与fresh实施审查由根后续绑定准确候选。没有新授权、旧ID升级、M6效果、正式Workflow/producer或两轮验收。新增collector成本与本片自己的公开CI另核，不借M5 CI通过。

## 完成源码片与相对M5 r4的移植冻结

补明示版本的最后一项真实反例：若v2资源文件名下误放完整v1 descriptor＋patch，原仅manifest/patch自洽校验会返回误标v2的receipt。prepare_training现有identity条件一并核 `declared.protocol_id == protocol`；沿真实prepare入口验证拒绝且未建目标目录，**1 passed／0.12s**。未增加另一套parser或业务授权。

在此产品版本下冻结r2全输入后，最终必要源码组 `source-final-r2` **25 passed／119.99s**，其余309未选。该组包括17项reference/严格选择、6项CLI/history/completed、2项两版本完整容量入口；完整patch48,660B、SHA `e96571f855fd8b0213cff76f6a2f2a7ac83b86c8562ee7dadbf98010d75a0655`，全tracked+untracked **2019项**输入SHA `cb3e986e194165541add1a9fda13f1d32fb2d96fee761c4d02785459e21ca0ec`。运行过程中未修改输入；之前的16项轻量r2复核为16 passed／16.68s，只属当次产品和范围。

该批结束后仅作三处测试配置接续：新直接prepare别名反例标Linux；history的managed-v2参数标Linux而保留原None跨平台节点；精确接根M5 r4原source-sync test的出生control30一行。原三个相关Linux节点 **3 passed／4.77s**；没有重跑25项或借此声称Windows验证。当前四文件实际collector为 **334／0.71s**，相对M5 r4的323新增11，未删除节点／未新文件/job。两个Linux mark只限定新增native来源准备范围，不扩大legacy或业务平台支持。

正式移植基线改为根已固定M5 r4 `68f3241695f5de1fdc188609db612c1d30434edf`（父a1ff338）。当前开发树HEAD仍a1ff，未reset、commit或push。已在内存AST/文件核对：原Execution文件逐字同68；native_main正文、validate_sources最终is_file门、M5原native故障test与source-sync test均同68。因此r3/r4不算本片新实现。r2→最终r3仅 `tests/test_reference.py`、`tests/test_training_submission.py` 两文件的上述测试配置差异，**全部665产品文件的bytes/SHA/执行位逐项同一**，没有转授一次变更后的新产品。

最终私有冻结：

|原件|范围／精确身份|
|---|---|
|`native-only-r3.patch`|相对68f3241，含两份untracked资源，11文件／43,950B，SHA `912a967995d5e764272e35346bd27f9474934675d2054b9d92fe7bddec66394e`|
|`complete-source-r3.patch`|相对开发树HEAD a1ff，含继承M5 r3/r4与本片，49,413B，SHA `cff1c643861f7c500d87a6e292a59abfa5064809dc985135aa0d56357c0136d5`|
|`source-freeze-r3.json`|基线、每个改动文件bytes/SHA/执行位、实际Python/依赖版本、原M5函数一致性与原283核验结果；仅保存所用环境变量名|
|`all-tracked-untracked-inputs-r3.json`|2019项全工作树tracked+untracked输入，SHA `18cd48672d4a1b6404f9b3c10259b7821978570bb0d166efa2d9e3b2948932e3`|
|`product-inputs-r3.json`|665项完整产品bytes/SHA/执行位，SHA `873807d898255bca6b7890b64935ece645913e98b2293b63c587c5b55df7b467`|

五个产品差异的最终raw SHA：

|文件|SHA256|
|---|---|
|`src/ergora/reference.py`|`6c63e631cf6486dfd191527e07a2790d99cab1077e7cf12d996dcccb97f16d96`|
|`src/ergora/training_execution_protocol.py`|`e9ab21e1acb84b45b5153cb43c1217aae82236f6baabd271e822717c32480c3b`|
|`src/ergora/cli.py`|`836851724d3e4c2ffcfa041f6fd4640e8afa0fb22799da7a053564a9177bb410`|
|`src/ergora/data/native-runtime/training-executor-admission-v2.patch`|`16743abddf26d6ca67ef55053530a4c80950eb994a4e4cbfef6965c11b401068`|
|`src/ergora/data/native-runtime/training-executor-admission-v2.json`|`0435fa4f62ac7a2fbce559a9d64a2cef70f298e4c1e11280643211050769cab7`|

原283逐项匹配、manifest及v1两资源未改，v2executor仍feed0fa7。最终native-only patch反向git apply --check通过、相对68的tracked diff --check通过；新增资源另有完整raw记录。正常subprocess.run均已等待退出、原S/H用例已返回并完成原收尾；本片未启动服务／模型／训练，未扫描或停止其他片资源。

源码实施和必要检查已就绪，交根在68父的独立固定树接入native-only patch，再作fresh独立实施审查、准确新core/SDK非editable安装／完整identity及自身模板。**本页不提前宣布D3完整安装验收、M5整体或M6无SDKmandatory已闭合。** 原v1真正禁SDK失败与所有探索原件保留；正式V2/producer、schema3效果和实际两轮仍关闭。

## 根：新独立源码审查及平台最小修正

[新的fresh源码审查](2026-11-16-native-admission-dependency-source-review.md)逐项核11 changed／2019 all／665 product、283／v1原件与真实reader原件。首轮两轴request-changes只因新增controller `managed-v2`节点漏Linux范围标记：Windows all会在installation fixture进入Linux-only prepare。原managed同类基线缺口与新增责任分开记录。

根仅在该既有native callback测试前增加一行Linux skip，五产品和所有其他输入不动；`linux-native-callback-mark-r1.json`核去除这94B精确一行后raw SHA回到r3冻结，既有两Linux参数实跑 **2 passed／9.49秒**（driver9.878秒）。同前缀command／stdout／JUnit／result保留，未运行Windows，不把平台限定称Windows实测。

同片reviewer已核最小差异／原件并关闭R1，当前**本片有限源码需求／维护性两轴approve、开放0**，报告SHA256 `686cab1cb31c910219acbd8a4fbd18a71c5bf813159f34fc44b7442b3553c2c4`。这不关闭M5新时序问题、不替代全hook已安装验收。M5最终r6正在固定受影响验证；待同步其精确delta后重冻本片完整源与native-only差异，再做新非editable core／SDK、真实无SDK正常prefix入口、自身模板和最终终核。


### 根：同步M5 r6后的r4固定候选与包身份

原开发树HEAD仍a1ff、未reset；精确接入M5 r4→r6 delta后，另在新固定树以 `f6722141cfa9ed885993360161c004e47e8df3a5` 为父生成native候选 `b3e734bad3d5a0ba01f69a61fd9328e0ab637f33`。native-only r4仍11文件，44,045B／SHA256 `a0abc3ba3a44055f125284bf693b8f7449b56d38137456ca90de5abda46db4a6`；相对本片r3仅新增已审Linux mark及M5父上下文变化，native原产品逻辑未另扩。`source-freeze-r4.json`、2019全输入和665产品逐raw／执行位匹配两树，三处_H、末端纯链及parent→clock顺序保持；同片有限源审两轴approve／0，报告SHA `f699fed34d78c2dd3e19f14235daaf0c0c659023f4a90d043ff6172a3c8a9ea4`。

新非editable wheel `3351ce085bf6721b046ab7991cdd8612a7a64837bf849ae5b47cab4448c506a0`的core／SDK各665完整产品字节／执行位同源及wheel、283参考／依赖通过，855构建测试输入、179测试／示例副本保持；六个生成egg-info已按准确原件归档移除。仅核包身份，**未在本r4执行新的wholehook行为批**。其后M5自身模板新增current intent R6／P2，正在原r6复现／r7修正；根暂缓本片最终行为验收，先接确切后继delta，避免把即将变化的父产品包装成最终结果。旧r3源码25／r4包身份各保原范围，不能转授新候选。

## 最终 r5：接入 M5 r7、真实安装 whole-hook 与原模板

最终固定候选 `bc58be6781d35e7e4fbd54ad997df8a4743428a8` 的唯一父为 M5 r7 `5bcecf37b615e3708ceb08acc329ba3dd0470f4a`。native-only 仍 11 文件／44,045B，`native-only-r5.patch` SHA256 `3524d80f4d1c62688086cbaf9638ddc07c6d5a8f8f79118fecb87555273fbdc0`；2019 全输入清单 SHA256 `f8e9387b04db06ffb0b70de82c27cafcb3661f637ffa5a3b0a7d09a2bb3d9e6e`、665 产品清单 `4cab575528cb89c1ac9008b95fbb6e0170fea7b1325e245a6d2318ff14e56b15`。同片 fresh 源码 reviewer 核两树、严格版本身份和 M5 的最终 intent／clock／phase 语义，限定需求／维护性均 approve、开放 0，报告 SHA256 `4e8561a4b98af1a259469d0d9cb38cd569b3d2f499bc31d1c6c3241010950251`。这不是安装验收的替代。

新非 editable wheel SHA256 `3c1ddaeb816d20841525d0be1f3139a59d0b62daaa98e14a75857481ce6e2fa7`；core／SDK 各 665 完整产品字节／执行位同源码和 wheel，283／依赖检查通过，core 无 Temporal、SDK 1.34.0、Python 3.12。855 构建／测试输入与 179 测试／示例副本冻结，六个生成 egg-info 文件准确归档后移除。私有原件为 `package-r5/`。

同一冻结输入的安装组 **25 passed／161.78 秒**（driver 162.864 秒、exit 0），包括 reference／版本选择 17 项、原 CLI loader 两分支 2 项、history 2 项、v1／v2 完整容量 2 项及 schema3 闭门／completed 早读 2 项。准确命令、JUnit、日志、case 原件为 `installed-affected-r5-*`。

完整 native 路径原件在两份 `test_round_complete_observatio{0,1}/native-reader-results.json`：

- v2 在选定无 SDK venv 的正常 `-P` 入口、首次 executor 导入前阻止 SDK／State／YAML／schema 导入，真实 `native_main → native callback` 读取 9,999,999B 和 10,000,000B 原前驱，均到达原 `Schema3 controller execution is not enabled`，`executor_sdk_loaded:false`。另外的 `-S` 纯认证单列，不冒充 whole-hook。
- 同一实际 native 入口对应用 source、四 measurement、manifest／ROOT 漂移均明确拒绝；descriptor 互换／格式／缺失与出生后漂移由同批25项中的 reference／capability 原入口验证，并非另一次 native descriptor 故障调用。fixture 复制完整 byte-identical 已安装包以供 native child 使用；没有伪造 sys.prefix、SDK、来源 pin 或关闭原 verifier。
- v1 禁 SDK 的原真实 rc1／executor→training→client→Temporal traceback 保留；允许 SDK 后到同一 schema3 闭门且 loaded=true。M+1 原容量拒绝仍由原测试验证，没有对超限输入调用 native reader；不能声称旧 v1 具备无 SDK 能力。

同一安装 SDK 运行原 `refactoring-quality → ergora-structure-review@1.0.0`，Codex **28.602 秒、approve**。16 个完整文件 830,415B、完整 native 差异和三祖先资源全部进入 880,790B stdin，SHA256 `3c9d56cabfea2bf7a5ff5aaba01db8be996c40b75e98c602350378cbff7b0ab0`；原 result SHA256 `a102abc50fc17f2a6325bf703b6d9c0c930d057e244d946b5bdfc5eae9c87549`，见 `self-review-r5-codex/`。

待安装原件／捕获身份终核与新 fresh 联合证据审查后决定 M5 R1 关闭及普通导入。源码、安装、模型各自 scope 保持；未运行训练、正式 V2 producer 或真实两轮，schema3／ordinal1 效果仍关闭，不称 runner／控制面／tracking 无依赖。
