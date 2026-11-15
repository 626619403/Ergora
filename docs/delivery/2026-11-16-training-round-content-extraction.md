# c1d M1a 交付记录

日期：2026-11-16。状态：源码14项／实际基线差分、全新非 editable 安装14项／隔离及自身原模板通过，fresh 源码及安装／固定身份终核均两轴 approve／0。产品已固定并普通导入开发树；普通推送及新候选自身CI另验。未启用 ordinal1。

实施基线 `fa2fd17620192ac1341a72f1050dc37faaee623f`；只提取原 rounds schema 之后的纯内容算法至现有 protocol，保持公开接口、原 pretty 字节／SHA、coverage 和错误语义。不启用 ordinal1、不改授权或源 inventory。

采用 `maintainable-project-delivery`、`ergora-codebase-quality`，已读根／src／tests AGENTS、组件协议、活动 wire 计划与原调用者。提取前准确文件身份、可验收检查和后继停点见计划；实现、源码验证、安装、独立审查和发布各自接续记录，不预记成功。

## M1a 实现与源码检查

在基线 `fa2fd17620192ac1341a72f1050dc37faaee623f` 的持久隔离分支 `refactor/training-round-content` 完成待审源码；尚未固定提交。产品只改 `src/ergora/training_rounds.py`、`src/ergora/training_execution_protocol.py`，原测试文件 `tests/test_training_evidence.py` 增加一个隔离内容校验回归。

原 schema 之后的内容算法、pretty 编码／轮 SHA、comparison／anchor 与 coverage 迁入现有 protocol；rounds 仍持有原 schema、文件类型／raw SHA／容量、发布和 State／training 观察。10,000,000B 集中为 `ARTIFACT_LIMIT`，原 `MAX_INDEX_BYTES` 保持同值；原 cycle.json 读取只替换同值常量。没有增加 schema、前驱消费者、新模块或授权能力。所移算法经 AST 比较，除符号重命名和 schema／docstring 分离外与基线一致。

源码实际检查使用原开发解释器、显式工作树 `PYTHONPATH`、禁止写 bytecode；完整原 `tests/test_training_evidence.py` 为 **14 passed／33.02 秒**，无 skip／failure／error（runner 34.366 秒）。使用私有固定 Git 基线模块对同一真实离线 fixture 的新旧 create／read／check 做差分：6 次成功 create 完整 pretty bytes、每轮 SHA、完整文件 SHA、结果及 coverage 相同；2 次 create 拒绝、11 次 read 和 62 次原始／篡改内容检查的返回或异常类别与信息相同。篡改涵盖 coverage、parent／SHA、revision、binding、files、comparison、anchor、approval、prefix；原接受前缀／baseline 漂移和 lost-ack 测试保持通过。

新增原 fixture 回归使用真实 `python -I -S -B` 子解释器，只加入当前源码包目录：校验完整 Unicode 报告、完整 pretty bytes／SHA，重算轮 SHA 后仍拒绝不同 revision；确认未加载 State、training、jsonschema、YAML、Temporal 或 dev_platform。另保存同一子进程边界的准确 argv／输出／耗时，成功。`git diff --check` 和所移算法 AST 比较通过。私有原件在忽略目录 `.ergora/checks/round-content-m1a/source-r1/`，包含 baseline 原源码、argv／环境／源码身份、raw log、JUnit、差分事件／完整报告、隔离与静态结果；不提交第二份算法。

当前实测 SHA256：

|文件|SHA256|
|---|---|
|`src/ergora/training_rounds.py`|`ad9fba3d3f675ec0a91dc07a4224852482e0b75730218b5feaecb3f342abe310`|
|`src/ergora/training_execution_protocol.py`|`bd5f1b2878c533aeadd6e69d2c5b3a830e52b135f808e12d283f9251c8068a09`|
|`tests/test_training_evidence.py`|`5f49ddb029c8e4b8f402caceac22fadaaf5e543e6783fe778f4401046f3a335c`|

本段只记录实现与源码检查，不构成批准或安装验收。新非 editable wheel／core 与 SDK 安装、283 身份／适用安装检查、自身模板审查、fresh 独立审查、提交／导入／推送及候选自身 CI 均待后续 owner 执行。没有启动真实外部服务、运行训练或扩大本片行为范围。

差分计数口径：上述共 81 次比较来自 4 个 round 测试接缝内的调用与内容变体，分别为 create 8 次、read 11 次、check 62 次；check 为 6 份原始报告与 56 份变体比较，不代表 81 个独立 fixture 或业务场景。

## 新安装、自身模板与固定身份

全新 wheel SHA256 `a4a26ff3e7782bffff7b1c0cdaf436a0fbf9ab6c4b1b29491fdd7b2fae1c4e7f`；独立 core／SDK 非 editable 安装各663包文件与源码、wheel 的完整字节及执行位相同，无增删文件，产品只改变 rounds 和 protocol。实际 owner 均来自 site-packages；两环境的原 `reference.verify()` 283文件与依赖检查通过，SDK 为1.34.0、core 无 SDK。

安装后的原完整 evidence 模块 **14 passed／30.55秒**（driver32.018秒），没有 skip／failure／error。命令使用 `-I -B`、清除 PYTHONPATH、复制的原 tests／examples，未使用源码 editable 导入。core 另以真实安装路径执行 `-I -S -B` 的同一 Unicode 内容／完整字节和 hash-valid 错误 revision 反例，0.082秒 exit0，未加载可选库或 State。安装前冻结848份 source／test／example／配置／CI 输入和663份完整产品文件，在安装检查与模型审查后重核均无差异。原件为 ignored `package-r1/` 的请求、日志、JUnit、完整库存及 `post-validation-identity.json`。

使用新 SDK 安装的 Ergora 原 `ergora-structure-review@1.0.0` 模板，用户授权的 Codex 后端实际 **approve／36.762秒**。11份完整文件140045B、原完整 baseline 两文件和准确 diff，加3项祖先资源，完整 stdin241065B；未截取正文或把后继 gate 写成当前能力。stdin SHA256 `ddaf3c40272a5135ef60950ea271f618154048dc4c4c7953fd16595c18a19cca`，原 result SHA256 `84c40fc16b49990cfc54c4d7b5882880b364b579107ede911b196ce7c14fc8f4`；原实际输入／输出／run 保存在 ignored `self-review-r1-codex/`。沿既有授权直接使用已可用 Codex；本次没有再次调用已知超时的 Claude，也不宣称异后端验证。

fresh [源码审查](2026-11-16-training-round-content-extraction-review.md)已核原算法／真实调用／全部23份源码检查原件，两轴 approve、开放0。产品固定提交 `5cb4cb903486d37356a5511c75e094a195558912`，以普通 merge 导入开发分支 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`，恰原三文件120增加／83删除、无冲突。新安装／自身模板及准确 Git blob 的同片独立补充复核已完成，两轴保持 approve／开放0；两提交相对基线的完整 diff 均为原 `c86e13f5…`，三 blob 同实测／wheel。远端推送及自己的 CI 尚未办理，不借 c1c 的在途 run 或历史成功代替。
