# AC3c.1 完整静态组合包独立审查

日期：2026-11-09。轮次：R1 初审、同片 R2 复核及精确交付终结。**R2 两轴审查通过，CM-SP1 / P2 已关闭；候选 `539163e` 的必要双 OS CI 与21:50:52 UTC即时远端核对通过，范围内无未解决 finding。** 下文保留 R1 需修改结论及各轮原始范围。

## 审查身份与固定范围

协调者为 fresh-context `/root/composition_manifests_review`；按 `code-review` 分别使用 `fork_turns: none` 启动 `standards_axis`、`spec_axis`，受可用槽位限制顺序进行。三者没有继承实现对话。读取了根 `AGENTS.md`、当前计划、AIHERO 索引、`code-review`、`codebase-design`、`maintainable-project-delivery` 及其 `references/independent-review.md`。

原始连续需求为可嵌套串行/并行/all-join 模板，完整结构祖先 Skill 指令与上下文继承，资源累加、逐祖先权限上限、父子共同新修订，以及专长/后端与模板解耦。本片只验收[AC3c.1 静态包合同](2026-11-09-composition-manifests.md)：冻结完整图及全部精确引用资产，独立历史核验；从包重新当前准入后，为选定叶子与显式 UTF-8 任务生成原输入格式。静态包未授权执行，不制造未来父结果，不接正式创建/批准或嵌套调度。

Baseline 与 R1 审查时 HEAD 均为 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`，分支 `refactor/architecture-foundations`；`git log baseline..HEAD --oneline` 为空。本次核对未提交工作树的固定差异及新增全文，而不是空的三点提交差异。

- [R1 scope](../../.ergora/checks/ac3c1-manifests/reviewer-r1/review-r1-scope.json) SHA256：`1a2d0a88cfcc6eceab5cc06923c7cc192140677ffe7c295b0e20c70cb2439886`。
- [R1 tracked diff](../../.ergora/checks/ac3c1-manifests/reviewer-r1/review-r1-tracked.diff) SHA256：`a96d8aa3788e872eec13b947b846c0a6c07792aba843868c66d46086b79abc55`。
- [12 文件原始快照与来源](../../.ergora/checks/ac3c1-manifests/reviewer-r1/snapshot-identity.json)均独立重算匹配 scope。修正开始后，原生产文件从未覆盖的 R1 非 editable 安装恢复快照，原新增测试从当前文件截取 SHA 精确匹配的原前缀；其余直接匹配原工作树。三个新增文件已全文读取。

|R1 文件|SHA256|
|---|---|
|`README.md`|`9dff83b71cf97af93d11c16d00c06f294893e4fd49ac1cd22d0a3d774dd6e98e`|
|`docs/PLAN.md`|`4aad95eee6dd2f8b841539dd71196c481cceb773c05447b4493b192b32d8db33`|
|`docs/WORKFLOW_DEFINITIONS.md`|`b37f7c5cc10653cc600fdaaf6674bed5075232f2f1e61e56e72aea18dd9055a4`|
|`docs/delivery/2026-11-09-composition-manifests.md`|`9e1c5e8044fde50495fba6ceb496003663246219e177aecd2feba56aed8f002c`|
|`examples/composition/README.md`|`6ceacfe4e5aec985d2bb1dbee0f7b90a0be9117095d2679d0c90fa64246f097e`|
|`src/ergora/cli.py`|`882a081d7b517f7236806ffc814f989180e3a56500965b46988ca9ed2da1914a`|
|`src/ergora/contracts.py`|`ae779bd3b50005253a479203cea1c76cedcf81188ab8967050c2c3d4f61b2a55`|
|`src/ergora/workflow_definitions.py`|`8de1d3d39ab423c99da88d04bb593e912676e00aab95c862a09a54d8f3386a27`|
|`src/ergora/data/schemas/composition-manifest-v1.json`|`da0e8a925cf9193f30645085d6d4802634a3ac007d420424e4ec6e200874d136`|
|`tests/test_workflow_definitions.py`|`d27cd5834a014f3f3bba95abe27979a9085eed9c58f809007a921dce18e64383`|
|`tests/test_composition_manifests.py`|`515777378503629784eba3ccb923c271b3097ddd1b8380b8ddbdf4e262431b8f`|
|`docs/architecture/current.md`|`abde6a47942bbe10c5a8d5adc83a407a631a082decb8bd9ea7035575120fb364`|

前片 `composition-capabilities-review.md` 的状态归档明确排除。审查者只写本报告与个人取证目录，不修改生产、测试，不安装、不提交或推送。

## Standards

R1：**范围内没有额外可操作 finding**，不代表整体正确性通过。未发现独立的硬性规范违例；启发式 smell 也没有形成需要修正的证据。

完整图核验与发布留在 `workflow_definitions`，复用 `definition_bundles`、`asset_trees`、严格合同及当前准入，符合 ADR0001/0002 和本片所有权约束；没有新增 import、调度器、权限模型、依赖，原输入编码保持。`_inspect_snapshot(..., leaf_input: bool, ...)` 只选择同一核验算法的格式差异，不是后端实现分派；`_prepare_bundle` 集中复制、容量、清理和原子发布。公共格式函数有真实 CLI 消费者，私有算法有明确所有权，未发现推测性通用框架。

该轴读取固定差异、新 schema/测试/交付全文、架构规范及相邻准入/库/备份/输入调用者，独立核身份；未运行测试或写入文件。源包目的地问题由 Spec 单独报告，未重复计入本轴。

## Spec

R1：**需修改，CM-SP1 / P2：生成输入可能使源 manifest 失效。** 固定 R1 [workflow_definitions.py](../../src/ergora/workflow_definitions.py) 第483–493行把输出目录交给 `_prepare_bundle`，后者第427–434行只排除两个内嵌定义库。可达操作为有效包 `manifest` → `prepare-from-manifest ... --directory manifest/prepared`：生成成功，但新增文件改变源包身份，随后 `verify-manifest manifest` 因多余文件拒绝。

这不符合本片要求的“可独立核验的manifest包”及“历史完整性”（交付合同第15、33行）；[公开说明](../WORKFLOW_DEFINITIONS.md)第46行也明确核验拒绝“多余文件或未引用定义”。最小修正是在创建父目录或暂存前，拒绝解析后位于源 manifest 目录内的输出路径，覆盖直接路径及符号链接别名。

独立 fresh-context Spec 轴另未发现范围内需求缺口或 scope creep。完整图重建、历史/当前准入分离、祖先材料、静态未授权标识、CLI 避免 State 及原叶子格式符合本片要求。该轴只读测试作为证据，未重跑套件或调用模型/服务。两轴 R1 汇总：Standards 0 项；Spec 1 项，最严重为 P2。

## 协调者实际核验与限制

协调者沿编译、资源合并、权限/预算、`DefinitionLibrary`、`inventory_tree`、CLI 和备份所有者追踪。新增格式复用现有有界整树核验及不覆盖原子发布；外部结构、稳定资产、复制中断和当前准入的检查各有可达失效情形。没有提出额外所有者、第二权限模型或通用调度器。

[独立探针脚本](../../.ergora/checks/ac3c1-manifests/reviewer-r1/probe.py)、[结果](../../.ergora/checks/ac3c1-manifests/reviewer-r1/probe-results.json)及原日志记录：

- R1 wheel SHA256 `69536cbb08347466d2a233673f34c9da7a085e36799677a77c1176e48b3ec2d3`，独立确认 wheel/安装目录 **363 文件**逐项一致；12 项 R1 快照与 scope/diff 身份一致。
- 原示例完整包 **10 实例**、工作流/Agent/all-join 均在，根摘要及 `execution_authorized=false` 保持。旧叶子输入摘要 `a963b348c4fe97fdf40a0bc76f7340d93fd066be5b07f0502538790e6a2de894` 在新核验器下不变。
- 当前 binding 准入人为拒绝时，历史核验仍成功，重新从包准备明确失败且无输出。
- 将 CLI 的 `State` 构造替换为立即失败：`verify-manifest`、`prepare-from-manifest` 均成功，无 State 目录，所生成输入保留完整图与精确 UTF-8/CRLF 任务。
- 在历史核验结束后，把资产替换成另一份身份自洽、可当前准入的定义库，真实预览成功，但从包准备因图与刚核过的图不同而拒绝，无部分输出。
- 独立复现 CM-SP1：私有源包副本内输出 `nested/input` 成功，输入自身有效；原源包随即报 `Composition bundle contains unreferenced assets or undeclared files`。
- 固定 R1 wheel 独立执行重复实例/祖先 Skill/原 State 移除/完整备份恢复合同单例：**1 passed in 0.73s**，见[单例日志](../../.ergora/checks/ac3c1-manifests/reviewer-r1/inheritance-backup-probe.log)。没有重跑五套或全量套件。

作者的原始源码三套 **129 passed**、清单/架构 **17 passed**、R1 非 editable 五套 **146 passed / 0 skipped** 及 16 次真实 CLI，已读取对应脚本、原始日志和身份记录；这些不是 reviewer 独立重跑。单次10实例历史核验约0.205秒仅是本机该包观察，不推导规模性能、执行速度或后端质量。

R1 自身真实 structure-review 经 Codex/ChatGPT、task MCP 于120.91秒返回 `request-changes`，提出同一 P2，原回执与结果保留在 [R1 hosted 记录](../../.ergora/checks/ac3c1-manifests/hosted-review.json)；这不是通过。原生 Windows、其他平台、正式批准/创建、嵌套执行、OS/网络隔离和模型遵从效果未由本次探针验证。当前候选提交、必要 CI 与远端终结另行核对，不借用前片 CI。

## R2 精确范围与修正

同一协调者及原两个轴复核原发现。Baseline/HEAD 仍为 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`，没有把下一片准入信封准备混入本片。

- [R2 scope](../../.ergora/checks/ac3c1-manifests/reviewer-r1/review-r2-scope.json) SHA256：`a92e585e1793f469821f043c819d98a15fc2db09045f798048b8dceda2b9e8f1`。
- [R2 tracked diff](../../.ergora/checks/ac3c1-manifests/reviewer-r1/review-r2-tracked.diff) SHA256：`919ca9d68ffd4e6d952be78c9484493330edb8ab2c2fcb462710d899fb74a385`。
- 三名 reviewer 均确认最终12项工作树/完整快照匹配刷新后的 scope。早一次核对遇到 PLAN/交付记录后续状态追加而不匹配；作者重新固定全文后再核一致，没有把漂移内容静默算作已审。

R1→R2 只有下列四项内容变化，其余八项逐字保持：

|文件|R2 SHA256|
|---|---|
|`docs/PLAN.md`|`995f5d0d297d270c09e6f9dfcf71e9e8fa035cd7d56b6b697ea78bd191857c81`|
|`docs/delivery/2026-11-09-composition-manifests.md`|`a714731afae892c4f49ff75ac86ab88774006944a9d278df6ab25c7ade3bcec1`|
|`src/ergora/workflow_definitions.py`|`c0228d028b82b7bac8689fee0a86f0d86ed1d62bebc1d3e2b8ef23bf65125d58`|
|`tests/test_composition_manifests.py`|`550c546abc42d03fa72e6520597f6f3c9c355dd2e8a024145ed64c1369b48c8a`|

生产只增加两行：`prepare_input_from_manifest` 在完整历史核验后、任何父目录创建/暂存前，比较 `destination.expanduser().resolve()` 是否位于解析后的源 manifest 内；成立则明确拒绝。两条回归核直接/深层内部目标被拒绝、无新增目录及源摘要保持。文档追加 R1 红例、R2 实际验证与剩余交付状态；公共[自身审查身份](evidence/2026-11-09-ac3c1-self-review-identity.json)和[原结构结果](evidence/2026-11-09-ac3c1-self-review-result.json)另外核对为原生回执归档。

## Standards R2

**通过，限定变化内没有新增可操作 finding。** 新 guard 位于拥有源包/目标关系的 `prepare_input_from_manifest`，保护已复现的源包失效情形，且在写入前执行；不属于重复权限校验，没有新增依赖。两条回归检查可观察的拒绝与不变行为。原核验、当前准入、编码和发布保持。

该轴独立核最终12项 SHA、快照及文档状态追加；之前的状态漂移已消除。没有重跑套件、模型或安装。

## Spec R2

**通过，CM-SP1 关闭。** 解析后的路径检查覆盖内部目标与现存父目录的符号链接别名；修正位置及范围恰当，没有改变原格式、整图绑定或当前准入。两条回归同时断言拒绝后没有新增目录、源摘要及完整核验保持。限定复核范围无新增需求缺口或范围扩张。

该轴独立核全部12项 SHA、R1→R2 精确生产差异、控制流及测试断言，未重跑套件、安装、模型、服务或原生 Windows。作者测试及自身审查不是该轴的独立通过依据。

## R2 独立机制、发行与真实自身材料

[R2 探针](../../.ergora/checks/ac3c1-manifests/reviewer-r1/r2-probe.py)及[结果](../../.ergora/checks/ac3c1-manifests/reviewer-r1/r2-probe-results.json)使用新非 editable wheel，不覆盖 R1：

- 独立重算 R2 wheel SHA256 `cd52801bda47ad5c44753a8e432549c58c40a7e1b8c0ff2562b7d85279bdcdf9`；wheel/安装 **363 文件**一致，所有生产 scope 身份匹配。另将安装内 **283 冻结文件**逐项与 reference manifest 及 baseline Git 原字节比较，均保持。
- 对直接内部目标、深层内部目标、含 `..` 的目标、目标经父目录符号链接别名进入源包、源包经父目录符号链接别名访问五种情形，均在写入前拒绝；每次前后完整 inventory（含目录）、摘要和独立核验一致。外部兄弟目标成功，源包 inventory 不变，新输入可独立核验。
- 已读取作者 R2 五套实际日志 **148 passed / 0 skipped，19.54秒**。原 R1 的146项/16 CLI分别保留；新增两例在 R1 包的红例、源码10项及选错 suite 的 exit4/零执行记录没有冒充最终通过。审查者没有重复五套或模型调用。

[自身材料核验脚本](../../.ergora/checks/ac3c1-manifests/reviewer-r1/verify-hosted.py)和[独立结果](../../.ergora/checks/ac3c1-manifests/reviewer-r1/hosted-identity-results.json)逐项核对两轮已发生调用：

|材料|R1|R2|
|---|---|---|
|实际结果|`request-changes`|`approve`|
|run ID|`468b0da15b4845f0867fbcb471b0a4f7`|`0be590bd3977446980cb468db23254ce`|
|完整附件字节|54,818|55,711|
|附件 SHA256|`8d0c8cf39865b4d1208fab2075adb911a015a6efcf6f69eddd41fa672d1bfd21`|`12e6a49dae6fea56f149e938bdbd48a28d31694a80ede6ea70cbbf47587f8ee4`|
|实际输入摘要|`c47e0e8ddaee7a7333b92eca2641e6c9e8c5932c5464a44d2b7260facaeed46e`|`7a7e628116063ffbfa8d6f983ac9a4e77e07ed030bc42a4be7f3348ccf31ba0f`|
|结果 SHA256|`bbd057e322bdab37846bb8566ba12720c81bfae6cee4b79bf7a0b4bd626a2250`|`7d2410d57ebd54c862cdea042bd23e0a94c8dfccc5dd31e9330c8c1745545b13`|

两轮附件的六项身份均匹配各轮固定输入，完整文件/指定差异正文与附件实际内容一致；原生 MCP read 回执覆盖每一字节并到达 `next_offset=null`，不是仅依据模型声称读完。原输入、完整静态包、实际 protocol prompt、result、公开结果归档及只读 SQLite 记录一致；源 State 的两定义库确已移除，`formal_execution_authorized=false` 保持。R2实际耗时123.89秒，结果为供给范围内源码审查通过，不是整仓测试或模型遵从保证。

R2 本地最终结论：Standards 0 项；Spec 原1项 P2已关闭、0项未解决，范围内无新增 finding。原生 Windows、其他平台、正式批准/嵌套运行等未验维度仍按上文保留。下一步为本片精确提交/普通推送后核必要 CI 和即时远端；本地结论不等待尚未创建的 CI，也不以本地结论冒称远端终结。

最终本地静态核对：本片六份 Markdown 加本审查报告共7份，287个本地链接/锚点及75条既有手册 CLI parser 通过，范围内 `git diff --check` 通过。公共自身身份/结构结果另逐项与原始运行记录及实际结果 JSON 相同。该检查只证明链接、解析与归档身份，不扩大运行验收。

## 精确候选与同片交付终结

原协调者继续核验普通推送候选 **`539163e6f93539d7939181bc2ec7b7a60bd82bc4`**，唯一父为原基线 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`。后片已在工作树开始，但本次只读固定 Git 对象、R2旧 wheel/安装与快照，没有从当前源码继承结论。

[最终19文件 scope](../../.ergora/checks/ac3c1-manifests/r2/review-final-scope.json) SHA256 为 `c9dbed3dd9fa84fed4cc62f99bd8393fbeefa2637838fb4ef0181f2e2cdf690e`。[独立候选核验](../../.ergora/checks/ac3c1-manifests/reviewer-r1/final-candidate-identity.json)确认：提交相对父的文件集合精确等于这19项，每项 blob ID 与内容 SHA256均一致；原12实现/文档、两份前片状态归档、本报告及两轮四份自身审查 JSON全部在内，下一片 `composition-admission.md` 未提交。候选 `src/ergora` 的363文件与已验R2 wheel/安装目录逐字一致，wheel仍为 `cd52801bda47ad5c44753a8e432549c58c40a7e1b8c0ff2562b7d85279bdcdf9`；四份公开自身 JSON逐项等于原运行回执。精确父→候选的 `git diff --check` 通过。

最终交付静态记录为 **9 Markdown / 310本地链接 / 75条 CLI parser，零缺失**。独立将该记录的9项文档 SHA全部与候选 Git 内容比较一致，见[静态身份](../../.ergora/checks/ac3c1-manifests/reviewer-r1/final-static-identity.json)。这轮加入的两份前片归档与此前7份本地检查分开记账；后片工作树文档不在该证据内。

21:50:52 UTC，独立重新 GET 官方 [Portability CI 42526062730](https://github.com/626619403/Ergora/actions/runs/42526062730)及两作业页面，完整批次 `totalCount=2 / hasMore=false`。运行整体 **Success**；[Ubuntu/Python3.11 作业128869824543](https://github.com/626619403/Ergora/actions/runs/42526062730/job/128869824543)和[Windows/Python3.12 作业128869824721](https://github.com/626619403/Ergora/actions/runs/42526062730/job/128869824721)均为 `completed/success`，无失败/取消/超时步骤，七项必要步骤均完成且为success。逐项核对官方步骤日志链接绑定同一完整候选：

|必要步骤|Ubuntu|Windows|
|---|---|---|
|Build and install wheel|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824543/logs/4)|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824721/logs/4)|
|Packaged reference identity|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824543/logs/5)|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824721/logs/5)|
|Native application regression|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824543/logs/6)|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824721/logs/6)|
|Windows PowerShell 5.1 installer and upgrade|仅Windows必需|[success](https://github.com/626619403/Ergora/commit/539163e6f93539d7939181bc2ec7b7a60bd82bc4/checks/128869824721/logs/7)|

官方完整页面、作业批次、内容 SHA及结果保存在[最终独立 CI 证据](../../.ergora/checks/ac3c1-manifests/reviewer-r1/ci-42526062730/final.json)。这是官方完成状态与精确日志链接核验，没有从未取得的日志正文推导额外测试计数。首次调用中误填 SHA的本地取证失败不是该候选的CI结果；进行中的早期观察分别保留，均未算成功。

完成上述官方核验后，**2026-11-08 21:50:52.632481 UTC**立即只读 `ls-remote`：`refs/heads/refactor/architecture-foundations` 返回完整 **`539163e6f93539d7939181bc2ec7b7a60bd82bc4`**，与候选一致，回执位于同一 final.json。审查者没有提交、推送或改动生产/测试。

本片精确交付终结通过，CM-SP1已关闭，无新增 finding。此次报告追加只归档同片证据；未验的正式创建/批准、嵌套执行、其他平台及模型效果仍保留原范围，不继承为后片实现结论。
