# c1b2b 执行消费者的新安装检查

本记录只覆盖消费者候选的新非 editable 包身份与双环境安装；源码回归、真实服务、自身模板及最终独立审查由各自记录负责。

## 冻结身份

2026-11-16 新包构建与双环境安装身份核验已通过。实施基线为 `af176cf6e79adb9c6ef6f32946672bc77cdb89de`，采用消费者 r5 冻结的全部八个未提交文件。完整候选 diff SHA-256 为 `7c8e07ae1d7062ffdd5151b3fd5e2d81692f2c264119a4371519599e269a85f9`；执行／worker／protocol 三产品 SHA-256 分别为 `f6b4a1ab90bdcaa3737b3c75abbaeaea6ee8afd029b3033cfbdc6a630531ad1b`、`d42d090b2988ff4a80376ee25692430cf28dd74117356682749f1149ed12176c`、`b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`，已与实际树核同。

已只读检查旧服务 r3 构建脚本，并在本片 ignored 持久 `package-r1` 目录机械适配实际树、基线、产物名及核验范围；未复用旧 wheel。已保存原 freeze、diff、181 项输入快照（178 项 tests/examples 加三个产品文件）及其字节数、SHA-256、执行位，并固定663项产品清单。脚本先完成编译检查，收到内部开始信号后执行；完整过程退出0，40.62秒。

## 构建及安装结果

本片新 wheel SHA-256 为 `55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`。沿既有用户解释器和 uv 缓存构建，在本片专属目录新建 core／SDK 两个非 editable 环境，未修改用户主环境或安装系统包。

- core／SDK 各663项产品的 source＝wheel＝site 字节、SHA-256与执行位全部一致；相较基线无增删，只三个产品 owner 内容变化。
- 两环境三个 owner 的实际导入位置均在各自 `site-packages`。core 的 `find_spec('temporalio') is None`；SDK 实际版本为 `1.34.0`。
- 两环境各283参考文件 `verify()` 均为 PASS，`runtime_started=false`；两环境 `uv pip check` 均退出0。
- 安装前另保存178项 tests/examples 原始输入。起止181项冻结输入、全部663产品、八文件完整diff及基线保持一致，执行位保持。

命令、stdout、stderr、逐步骤result、包SHA和完整清单保存在本片 ignored 持久 `package-r1` 目录；此次使用新构建包，历史服务 r3 wheel 不认证本候选。

## 尚未验证

本记录未运行任何安装测试、真实 S-H／Temporal、模型或训练，也不代表自身模板或独立审查通过。上述新包及双环境交主控接续行为验收；源码回归仍按其原证据单独记账。

## 后继CI组合与自身模板接续

源码r5已先固定585e3da，再真实merge原CI7ed得到`bcc304894622040a7d844f8c6f9ddfded65aa895`；仅将共享cycle_budget_root显式导入迁移后的controller测试模块，三产品与本wheel55029保持。安装行为使用独立新冻结，不能把原181项构建输入改记为迁移后测试已跑；本记录原构建结果保持其准确来源，最新测试与闭包见[消费者交付](2026-11-16-training-cycle-execution-consumers.md)。

新包SDK环境以原`refactoring-quality`／`ergora-structure-review@1.0.0`真实调用Codex41.77秒approve；完整7ed→bcc差异、22文件679,419字节、3继承资源及完整任务实际进入741,435字节stdin。run=`7e08910035274c158594bfb92bfc551a`，input digest=`5059651067b3ce2733f2a67c390827e130035c6f11faf3c1c3c3f9b80c0e7f42`，原结果SHA256=`d43e38db7134b816acc29bee706d28a0acaeb77ac3e7202a42ccf01671dede9b`。原件在消费者ignored `self-review-r1-codex/`；仅supplied-source结构审查，不认证私有安装／测试／真实服务，正式TrainingCycleWorkflow和accepted／rounds后继仍另片。
