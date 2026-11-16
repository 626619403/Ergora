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
