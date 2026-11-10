# AC5 C3a 原包派生修订独立审查

日期：2026-11-10。审查者：`/root/definition_revisions_review`，新的 fresh-context 上下文，未继承实施对话。先读用户原始要求、本片合同、AGENTS、PLAN、两份规格及实际差异，再读作者交付叙述；采用 maintainable-project-delivery 的 independent-review 与 codebase-design 原则。权限限于只读检查、私有隔离探针及本报告；未安装、改生产或测试、启动模型、提交或推送。

**首轮本地结论（保留当时检查范围）：C3a 已审实现与行为的 Spec／Standards 通过，0 开放 finding。** 当时实际自身模板及本候选自己的精确提交／必要 CI／明确 HTTPS 尚未核，未登记完整切片交付通过。C3b–d、C4–C6 没有随本次通过。

**当前提交前终核：完整 26 文件的 Spec／Standards 本地通过，DR-S1 已关闭，0 开放 finding，可普通提交本片。** R2 包／旅程、两轮实际模板完整明文及八份公开投影已独立核验。以下首轮与原红观察保留各自范围；最新结果见文末终核。精确提交／包对象、新候选自己的必要 CI／明确 HTTPS 仍待验，不登记完整交付通过。

## 固定范围与身份

基线／受审 HEAD：`0a495aaaa489f838c009820b7cd978bbed0c5e37`；分支：`refactor/architecture-foundations`。初始 `review-input.json` 覆盖 **15 文件**：

- 生产：`definition_bundles.py`、`agent_definitions.py`、`workflow_definitions.py`、`cli.py`、`web.py`。
- 测试：`test_agent_definitions.py`、`test_workflow_definitions.py`、`test_definition_console.py`。
- 文档：两本定义手册、PLAN、AC5 总规格、C3 计划／交付记录、C2 独立报告的状态续记。两份新 C3 文档已直接读取，没有只审 tracked diff。

初始清单的生产、测试及其余文档共 **14 文件**逐项 SHA256 匹配。审查中 C2 原审查者继续追加其报告的精确交付采样，该文档及完整 tracked diff 因此变化；保留初始清单／diff，独立当前快照另存 `independent/initial-scope.json` 与 `initial-tracked.diff`。此变化仅属 C2 状态记录，不重新审 C2 实现，也不继承其验收。提交前还需刷新包含本报告及最终状态文档的完整清单。

|生产文件|已核 SHA256|
|---|---|
|`definition_bundles.py`|`a98f28eb9c8adc5ca2dd07537ff786a3a320a8c73c3603e6326eddf2f42b28dc`|
|`agent_definitions.py`|`49bec7289d14edade4f23de78b60add222e39ce809be67c38a27877d0129d2fb`|
|`workflow_definitions.py`|`1982119a1883d5dfb5cdb0c7217f9097a155fdc1a58c540f13ac1389cb52b5ee`|
|`cli.py`|`424d06e185ead9d1cdbf9a9a5e744012d2f79e68176dda328132e3f4474b17f0`|
|`web.py`|`20d412cb930d406c12d78841260c9149052b1f37a57e72bae606404c9ebbe009`|

## Spec：需求符合性

**通过已审 C3a 范围；无阻塞发现。** [原库修订入口](../../src/ergora/definition_bundles.py)从明确种类的 `id/version` 历史 export 验证原摘要，复制完整目录后只重写对应 JSON 正文。候选返回精确 base、正文／文件／资源身份与 published，不暴露已清理路径；check 没有索引发布，publish 经过原 import 及不可变版本冲突处理。

Agent 的新准入继续由原职能／后端所有者负责；Workflow 的新准入通过原完整递归编译器检查精确已发布依赖、角色、全部结构祖先材料、权限、端口与预算。历史 get/export 使用完整性检查，不因今日后端准入变化改写旧版本。CLI 与 HTTP 都调用同一用例，HTTP 原请求与异常处理继续适用，错误返回可见；没有新调度、任务、批准或运行接线。

两本手册准确区分检查、显式发布、版本冲突及逐依赖发布。跨库事务、资源内容修改、YAML、页面编辑和活动任务采用均没有实现声明；后续完整父子共同提权旅程仍为 C3d。检查不是版本预留，最终同版本冲突由原发布索引拒绝。

## Standards：所有权、复用与成本

**通过；新增硬标准违规 0，阻塞性结构问题 0。** `DefinitionLibrary.revise` 的两个实际生产消费者位于 Agent／Workflow 原所有者；各薄用例均被 CLI 和 Web 使用。共享 CLI 参数声明在两个命令入口直接复用；四条 HTTP 路由仅承担传输，不复制权限、摘要或发布算法。没有新公共框架、依赖、schema、数据库、CI 任务或冻结资源变动。

新增的 publish 分支对应明确检查／发布选择，base digest 守卫保护精确编辑起点，返回过滤避免临时路径失效。原 export 在复制前后核历史内容，原 import 在暂存前后核候选并保留 file_lock／索引发布；它们保护不同阶段，没有新增同层校验算法。完整树复制有上限，保留旧库的 10 MB／500 文件／500 目录／32 层约束。

独立 **9 MB** 包单次样本：check **0.106 秒／一次整树复制**，publish **0.168 秒／两次整树复制**；同候选摘要一致。额外发布副本来自原 import 暂存。正常成功、错误基准及同版本冲突后的修订／导入临时目录均清理。该样本没有测峰值内存、吞吐或跨平台容量，也不证明进程强杀后的临时目录回收。

新增测试覆盖新入口可能静默绕过当前准入、丢附件或发布错误版本的风险；既有库测试继续拥有冲突、崩溃窗口与导出检查。HTTP／CLI 身份比较、完整包保真与祖先权限测试各保护实际入口，不要求再复制全部 validator 测试矩阵。没有新增 CI 成本；现有安装组 74.63 秒只是记录的本地耗时。

## 独立检查与实际证据

本次私有证据位于 `.ergora/checks/ac5-definition-revisions/independent/`，核心为 `inspect.py`、`inspection.json`、`inspection.log`。

1. 独立重算源码、wheel、非 editable 安装及 RECORD 的 **435 文件**，逐项相同；wheel SHA256 `2f01f15bc422d948912c3097fb9ee7a8992100be8c355d0451abbb6ba837b73e`。从固定基线 Git archive 核 **283 冻结文件**及 manifest，保持不变。
2. 直接读取原旅程脚本及 **18 CLI／26 HTTP** 原回执；核两类候选、错误摘要、后端／权限／缺依赖／错摘要拒绝、冲突、重试与先子后根发布。独立重算原包和导出包的文件字节／执行位／目录，非正文项保持；旧 manifest 再验有效并仍指向旧根。原 owned HTTP 的 PID/start 身份已消失，原端口无监听。
3. 使用已核安装包在独立私有 State 实际调用新入口：check 不改索引，错 base 不发布；两个线程同时发布同 ID/version 不同正文，恰一个成功，另一个得到原索引的内容冲突；成功正文可重试，原包完整身份保持，临时目录清理。
4. 阅读源码 **142 passed／1 skipped／12.38 秒**及非 editable 包 **180 passed／1 skipped／74.63 秒**原日志，核其实际文件组与跳过范围。它们属于作者既有执行；本次没有重跑全套 pytest，结论依据所有者／调用路径检查和上述独立探针。
5. 原文档静态记录为 **7 文档／99 链接**及 README／新增手册 parser 命令检查，无缺失链接。此范围早于本报告及最终状态续记，最终文档集合仍需刷新静态检查。

## 首轮剩余门禁与未验

首轮已验范围没有发现需要修正的代码问题。以下当时未计通过：本片实际自身模板的完整输入／读取／后端原回执与结论；包含最终报告的精确对象／包身份；该新候选自己的必要 CI 和独立明确 HTTPS 远端 SHA。C2 的 CI／远端、模板或旧片测试不替代本片。

本片没有新增页面、执行器或训练行为，本审未做浏览器、模型质量、GPU、Windows 运行或完整联合提权任务采用验收。后续收到本片实际自身模板及精确交付证据后，由同一审查者续核；当前仅登记两轴本地实现检查通过。

## DR-S1：合法只读正文不能派生（P2，首报开放）

2026-11-10 同片续核。实际自身模板 run `14c61cb4d2dd4358bf71d88c4ee67eba` 原回执记录 **231.87 秒／succeeded／request-changes**，提出此问题。本审读取原意见、run 记录及读取审计；完整 **323011 字节／14 连续 UTF-8 页／四份继承指令与 Skill**的数值来自该审计，本轮未重新逐页复算。以下结论由独立执行支持，不以模型意见本身作证。

**位置：** [DefinitionLibrary.revise](../../src/ergora/definition_bundles.py) 的 R1 第 209 行，文件 SHA256 `a98f28eb9c8adc5ca2dd07537ff786a3a320a8c73c3603e6326eddf2f42b28dc`。

**可达场景与后果：** 原库接受标准 JSON 为 POSIX `0444` 的普通文件，import／get／export 都正常，copytree 会保留该模式。修订随后直接 `write_text` 打开已导出的标准正文，普通用户没有写权限，check 与 publish 都在候选校验之前抛出 `PermissionError`。因此原库支持的包不能经新入口派生，违背完整原包修订合同；不是后端准入、权限链或版本冲突拒绝。

**独立原红：** 以普通非 root POSIX 用户，使用未修改的 R1 非 editable 包，在私有 State 构造 Agent／Workflow 两类 `0444` 标准正文。先核原库 import／get／export 成功及模式保留，再调用修订 check／publish，得到 **四条 PermissionError／errno 13**；相同结构的 `0644` 对照 **四条成功**。失败后索引、旧包字节／执行位／模式保持，修订临时目录已清理。证据为 `independent/dr-s1-reproduce.py`、`dr-s1-original.json`、`dr-s1-original.log`，采样时间 **03:33:40 UTC**；生产及安装包均未修改。

**最小修正建议：** 仅在重写之前给暂存的 `agent.json`／`workflow.json` 增加所有者写位，保留执行位，继续由原 import 计算身份与发布；原包及其他资源模式不变。此处无需放宽原库准入、改变摘要算法或加入平台分派。用合法只读正文的聚焦回归覆盖两类入口，并核原对象不变及新正文执行位保留。

**首报时两轴状态：** Spec 存在一个需修正的 P2；Standards 的原所有权／复用结论保持，没有额外确认的结构问题。DR-S1 当时尚未复核修正；首轮 0 finding 只代表当时已验范围。修正后的安装身份／受影响回归／实际自身模板及精确提交 CI／HTTPS 当时仍待验。

## DR-S1 R2 复核：关闭

2026-11-10，同一独立审查者复核最小修正。R2 相对已审 R1 的生产包仅 `definition_bundles.py` 改变：增加标准库 `stat`，在已完整导出的暂存目录中选定当前种类的标准 JSON，对其 `st_mode | S_IWUSR` 执行 chmod 后重写。原对象与其他文件没有新增写入；执行位仍进入原摘要算法，原 import／index／file_lock 与所有准入路径保持。没有异常吞掉、平台分支或宽松回退，修正处于资源生命周期的实际所有者。

|R2 身份|SHA256|
|---|---|
|`definition_bundles.py`|`955d93effbe79f4f41f545f698b2aec416e0b946e97362a4b4fb98f71fcbbe55`|
|`test_agent_definitions.py`|`a20ef33e772b7f656f81d763fd8cf7ffdbce9798e7113ff43361cf2f636fbbe0`|
|`test_definition_console.py`|`ac5e72716fb48c1f73bb4777ac4a10fa5395e4cf7a4f6fefb00b299d691fe61f`|
|R2 wheel|`9e4c99abf8206ee0dcf69658f32b6b9436b5c895d8808bd4d4bcd471fcea4f7d`|

测试强化已有三个案例的只读输入与执行位断言，没有新增镜像套件或 CI 任务。已读旧 R1 安装 **3 failed／58 deselected／2.63 秒**及修后源码 **3 passed／58 deselected／3.53 秒**原日志，失败点确为已复现的暂存 JSON 写入；R2 原七组安装测试 **180 passed／1 skipped／74.08 秒**。这些是作者执行，本轮未重跑全套。

本审另以普通非 root POSIX 用户，使用 R2 非 editable 安装，独立运行 **Agent／Workflow × 0444／0555 × check／publish 八条成功路径**。原库接受与导出模式已先核；候选标准正文执行位、所有非正文文件身份、旧对象的完整库存与模式保持，check 不改索引，临时目录清理。发布的新正文只增加所有者写位；原 R1 安装及原四红证据保持不变。证据：`independent/dr-s1-fixed.py`／`.json`／`.log`，**03:40:50 UTC**。

独立重算 R2 的 **435 源码／wheel／安装／RECORD 文件**以及固定基线 **283 冻结文件与 manifest**，全部一致。逐读 R2 **18 CLI／26 HTTP** 回执，核原 Agent `0555`、两个 Workflow `0444`；原包／导出完整树、空目录、旧 manifest 及错误拒绝保持。原 owned HTTP PID/start 身份已消失，端口无监听。证据：`independent/r2-evidence.py`／`.json`／`.log`，**03:41:23 UTC**。没有将修后源码与 R1 当时快照混为同一身份。

**DR-S1 关闭；Spec／Standards 本地通过，0 开放 finding。** 初始测试、模板 request-changes、独立原红和 R2 修后证据均保留。R2 实际旅程 8.02 秒未显示本次模式处理有明显额外成本；没有新增吞吐／内存承诺。

R2 修正复核时，第二轮实际自身模板尚未核定；最终文档集合、精确提交／包身份及本候选必要 CI／明确 HTTPS 当时仍待验。已修正本报告源码链接中不被仓库静态器识别的行号写法；此前静态失败原件保留。

## 完整 26 文件提交前终核

2026-11-10，同一审查者核 `review-input-final.json` 的 **26 文件**完整集合与逐项 SHA256，并确认实际 tracked diff 逐字等于 `final-tracked.diff`，SHA256 为 `7a856b662914654e3fef243ac5baa799c2a4b50399e45950f7354e4b1019ee49`。范围为 **5 生产／3 测试／10 文档／8 公开 JSON**；新文档和 JSON 已直接读取。独立快照为 `independent/precommit-scope.json`。本报告追加终核及其后状态续记会改变文档摘要，提交绑定前须刷新清单；14 份受保护源／测试／配置与 R2 实际模板身份均保持。

C2 两份记录的增量仅续记其原候选 `0a495aa` 的普通远端交付、独立 HTTPS 与 CI 终态 **Cancelled**；Linux 超过 20 分钟上限、七必要步骤六成功一取消，没有被改写成通过。新增 CI 时长审计清楚区分 retained 原件、历史对照与未知根因；没有原 Linux 逐例尾部，未据此删除测试、延长 timeout 或修产品。Windows 五个消费者的提前 skip 只列作后续候选，不是本片补丁。实际 diff 确认 pyproject／CI／冻结 manifest 与 283 文件保持，前片已终态满足等待条件，不能代替新候选自己的 CI。

### 原模板与完整读取

本审重新解析两轮原 native stream，核注册数据库中的原 run 与 `native.stdout` 全等；原 manifest、prepared／实际 input、composition、prompt 摘要、admission、原 response／result SHA 均匹配。两轮均使用安装包内置结构审查模板的证据修订，原定义库移除后仍由固定快照准备并运行，没有改变内置默认后端或加入新正式执行授权。

|原运行|实际结果|独立核完整送达|
|---|---|---|
|R1 `14c61cb4d2dd4358bf71d88c4ee67eba`|231.87 秒／succeeded／request-changes；原结果 SHA256 `398666b2ebee86d47945e1bb4bdfd4b288cc5b5dd67d72e6ddfafa1764cd84d6`|323011 字节／14 连续 UTF-8 页，offset 0 至 next_offset=null；四份继承指令／Skill 全文，base64／重复页／失败均 0|
|R2 `6bdde5be958d41f2a88d2491b1081c6a`|175.68 秒／succeeded／approve；原结果 SHA256 `9e2b4914705b1fe7ff4017e9d120ff230c16b7d33114e97f2fc2f4991eabce92`|343725 字节／15 连续 UTF-8 页，offset 0 至 next_offset=null；四份继承指令／Skill 全文，base64／重复页／失败均 0|

每页实际字节、大小、摘要、连续偏移与附件原件相同；两轮各 **14 份完整受保护文件**均在附件内。R1 按 R1 安装包／初始 review-input／固定基线配置核历史身份，没有拿修后源码与旧快照强行比较；R2 才与当前 14 文件逐字核对。证据为 `independent/final-model-audit.py`、`final-model-r1.json`／`.log`、`final-model-r2.json`／`.log`。完整明文送达不证明推理质量，Codex 回退不证明异模型错误独立；模型没有运行候选代码、正式批准或替代本审。

### 公开投影及提交条件

八份公开 JSON 逐项重算 SHA，与 `public-evidence.json` 一致。两轮 identity／reads 保留原事实，result 内意见与原 native JSON 全等，原结果摘要与公开文件摘要明确区分；R2 package 的 435 文件映射、测试原红／修后统计、reference 字段以及 journey 的所有调用／结果逐项对应原件。清理只替换实际根路径并移除机器、进程细节；追加的只读模式、八条独立成功及清理声明与本审原件相符，公开 JSON 没有实际个人目录。证据为 `independent/final-public-audit.py`／`.json`／`.log`。

最终静态原记录为 **10 文档／128 链接／98 parser 命令**通过；原两条静态红保留。本审在终核内容写入后独立再核同一静态所有者，仍为 **10／128／98** 通过，原件为 `independent/final-static-documents.json` 与 `final-static-audit.log`；没有增加应用测试框架或重复全套回归。

**完整 26 文件的 Spec／Standards 本地终核通过，DR-S1 关闭，0 开放 finding；具备普通提交条件。** 受审实现继续只属 C3a。精确提交／归档与 R2 包身份、本候选自己的必要 CI 终态及独立明确 HTTPS 远端 SHA 尚未取得，不提前登记这些门禁或整个 C3／AC5 完成。
