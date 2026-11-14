# Q1.2 外部 PR／MR 来源独立审查

日期：2026-11-15。评审者：fresh-context 独立 Agent `external_review_sources_audit`。未继承实现会话；按原需求、Q1.2 准入合同及实际源码／调用者／检查原件审查，不以作者说明或自身模型意见预设结论。本报告只授权写入本文件。

## r1 结论

**需求符合性：request-changes，开放 P2 一项（R1）。结构可维护性／测试价值：approve，未发现额外的职责、上层分派或冗余测试问题。** R1 关闭并复核前，本片不能标为本地审查完成；普通发布、自己的适用 CI 及同片终核仍未验收。本结论只属于下述 r1 身份，不向后继修正自动继承。

已读根、源码及测试目录的 `AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)、[Q 总需求](../plans/2026-11-15-domain-review-optimization-quality.md)、[本片合同](../plans/2026-11-15-external-review-sources.md)、[交付记录](2026-11-15-external-review-sources.md)，并应用 `ergora-codebase-quality` 的 repository-style／module-design／test-seams 三份 reference 及 `maintainable-project-delivery` 的独立审查说明。仓库没有配置另一套 formatter／linter／type-checker，未套用外部框架的代码风格。

## R1 — 合法来源配置被内部 repository.id 上限拒绝（P2）

位置：[review_sources.py](../../src/ergora/review_sources.py) 的 `_repository_id`（r1 第 21–22 行），及 `collect` 第 59 行；约束来自原 [local-review-packet-v1 schema](../../src/ergora/data/schemas/local-review-packet-v1.json) 的 `repository.id.maxLength = 1024`。

来源用例直接把完整 `source` 和 `repository` 的规范 JSON 作为原本地包的 `repository.id`。绑定允许合法的自建站 API 前缀、最多 300 字符的完整 namespace/project；该身份还重复包含 project。于是有效配置能生成超过原包上限的内部 ID，采集已经取得两次观察并读取完整 Git 材料后，仍会在 `review_packets.prepare → _check → contracts.validate` 被拒绝，无法发布来源包。此失败与来源封套、HTTP 或 Git 材料容量无关。

独立纯内存核验使用现有 r1 安装的本族工厂及原 schema，没有网络请求或文件写入：

```python
project = "group" + "a" * 144 + "/" + "project" + "b" * 143
api_url = "https://gitlab.example" + "/proxy/service" * 30 + "/api/v4"
binding = {"tool": "gitlab", "project": project, "api_url": api_url}
```

`issue_backends.for_binding(binding)` 接受该配置；project 长 300、api_url 长 449。以 native ID 88、GitLab 的 `node_id: null` 构造现有规范观察后，`_repository_id` 长 **1,165**；原 schema 明确拒绝。采集的后续失败路径由上述实际调用链确认，没有声称已运行一轮完整平台采集。

最小修正：在来源 owner 对完整规范身份派生固定长度摘要 ID，并让采集与 `_check` 使用同一算法；完整来源／native 仓库身份继续保留在封套。无需新抽象，不收窄既有 binding 的有效范围，也不放宽原本地包格式。沿原 HTTP＋真实 Git 的采集／离线读回接缝验证一个这样的合法非默认配置，并保留旧实现的失败结果；无需新增测试文件或 CI job。作者已接受本 finding，修复及修后证据尚未审查，**R1 保持开放**。

## 源码与维护性核查

- 构造与调用为 `cli.main → review_sources.collect/read → issue_backends.for_binding → IssueBackend.repository/read_review_request/review_commits`。两个实际后端自己解释平台字段；工厂映射仍在本族模块。CLI／来源用例没有按平台名字增加产品执行分派。新增 `repository()` 提取原读取，原 `repository_refs` 的形状、两个 branch 读取及 `issues.remote_candidate/link_review` 消费者保持。
- `review_sources` 的一个生产调用者为 CLI，但该 owner 隐藏原生观察与原包的身份关系、两层读取、容量及原子发布义务；移除它会把这些领域义务重新泄漏到 CLI，独立模块有实际职责。`_repository_id`／`_check` 分别由采集和读回共同使用，schema 是新持久封套的实际合同，无投机性注册器／第二平台客户端／第二 Git reader／状态库／任务或 export。
- GitHub 使用单次观察的 base/head、拒绝 merged 历史重建；GitLab 要求 ready diff_refs、head 一致，并在原 `prepare` 的唯一 merge-base 计算后核 `base_sha`。fork／缺失端点沿原 backend 拒绝。平台响应限额、未就绪和矛盾比较均显式失败，不拼接跨时刻的 PR 字段、不隐式 fetch、checkout 或执行目标代码。
- 完整变更／blob、显式调用者和配置、祖先 AGENTS、原需求与检查正文仍归 `review_packets/GitMaterials`。来源层只链接其字节摘要，复用原 staging 和 `publish_directory` 的不可覆盖发布；比较或容量失败发生在外层发布之前。来源约束、普通文件检查和两层摘要各保护不同的外部／持久输入边界，没有发现应该删除的重复 guard。
- 离线读回构造 backend 仅解释本地身份，不查凭据或发请求；入口在 State 初始化之前。它核来源／native 仓库／请求地址及声明的比较关系，**不会离线认证 commit-tree membership、真实 merge-base、平台来源、当前 head、未保存的原 HTTP 响应或检查可信度**。用户手册对此有明确限制；本审查下方另读原 Git 对象的结果不能扩大为产品离线认证能力。
- 六个新增接缝是三个测试函数在两平台的实例：完整采集／新 head／旧包和状态保持／无 Git 离线 CLI，跨层关系篡改，以及不可用或矛盾比较。它们复用原 HTTP 和真实 Git fixture，保护可静默错连的身份和发布风险。既有原生错误接缝已覆盖 fork／错源等，不需复制到来源层。未新增测试文件、依赖、CI 分组或 job；原四 suite 的安装回归也覆盖被提取的 `repository_refs` 消费者。

## 原件与独立轻量核验

下列核验只读取现有源码及 ignored 的本片检查原件；未重跑六项／117 项测试、模型、服务、训练、安装、平台请求或目标脚本。

|原件／检查|独立观察|
|---|---|
|`package-r1.json`、r1 wheel、原非 editable 安装|逐字重核 **642 源＝642 wheel＝642 安装**，逐项与清单同；wheel SHA256 `1ec19ef95ad96262cd6f0792546ee62d74fb66b0d5ec013c52ee041c5360f0bc`。安装 direct_url 指向该 wheel，无 editable 标记；repo-only 源码根 AGENTS 不进安装。|
|固定 705 Git 产品清单|原 640→当前 642；只新增 `review_sources.py` 和来源 schema，只改 CLI／本族 backend，无删除；**283 reference 的 Git blob 身份全部保持**。|
|三份 JUnit 与原 stdout／stderr|r1 六项全过，stdout 5.52 秒；r2 原四 suite 113 通过／4 可选跳过，57.71 秒；安装原四 suite 117 通过／0 跳过，60.07 秒。原安装日志只有一项 Starlette TestClient deprecation warning。没有把这些归档结果称作本审查重跑。|
|`native-journey-r1.py/.json` 与 14 条原输出|14 对 stdout／stderr 的长度及 SHA256 与索引一致，记录的成功／拒绝和离线 PATH 空设置对应实际命令。两平台的 collect、read-source、原包 read、错 SHA、已有目录、超限和缺对象结果齐备。|
|两个现存来源包|外层源摘要、内层 packet 摘要和保存回执一致；原 read-source 输出逐字段等于磁盘两层内容，原包 read 输出等于内层。需求／检查原始 UTF-8 字节保持，变化清单四项，显式 caller／config 与祖先规范齐备。|
|保留的真实 Git fixture|以禁用替换、hook 及隐式 fetch 的只读 Git 命令，分别重核两包三提交的所选文件表（7／7／6）、9 个完整 blob、四个变更路径和唯一 merge-base，全部一致。此项使用了保留的仓库，不能称为只凭包的离线认证。|
|保持与清理的证据范围|现存 Git 文件数 48、每个包两文件、未使用工具 home 不存在可重核；**完整前后 manifest 未落盘**，Git／各两份 fixture 状态／旧包的当时前后逐项保持、每平台 8 GET／无 branch GET、服务关闭是所读 driver 的断言及其保存结果，不能独立重建 before 清单或历史网络调用。|
|`live-github-r1.json`|保存的是本仓库元数据 200 与明确 PR1 的 HTTP404；没有完整真实平台来源包。未重新联网认证，未把元数据可读或替身通过当真平台采集成功。|
|自身原结构模板原件|直接核对 run `82be97a0299a43afb19ed1dc64d0323c`、23 完整文件／511,809B、三份祖先 resource 在实际 stdin 全文存在、prompt＝stdin，input digest `4ab7c0971f91c8ee9c884c3df47fdde34f3c3bf5873113e791e4532346e50640`；result 字节与原副本相同，SHA256 `a5151de40a6ec5943af22464ed2f2bd69bec55e59b922d3e70357177123fc1b9`，原 decision approve／51.667259 秒。其给定文本范围没有检出 R1，不替代本次独立结论。|

两个原包的独立摘要：GitHub source `ac76a60721ff98bc7847435c44641e4cdadc1f974998e288ca87fe0efdb0f4cd`／packet `302434be32cabd98f6db4ca9f54fc24bbc5e0b7bcd47e54200622623dd10ba63`；GitLab source `3ce5c82183fd79f61d91a219361aa84fa870c972c4acf7bc5caf3354041857aa`／packet `700fc29641a4647fefff9e20b82216368a57a65f89d112e9fa02b93d85457ac3`。

完整 tracked diff 及四个 untracked 作者文件的 no-index `--check` 均无 whitespace 错误（no-index 的 1 是存在新文件差异）；独立重核当前 **12 份作者 Markdown／279 本地链接及 fragment，零错误**。此统计先于加入本报告。原 docs-r1／r2／r3／r4 保留各自检查范围，不以新计数改写历史。

## r1 精确审查身份与剩余项

基线和审查时 HEAD 均为 `705cbe428dce73ff222dbdaec3c67329a310c06d`，分支 `refactor/architecture-foundations`。原 `review-scope-r1/scope.json` 的 **16 文件／458,742B** 全部逐项重核；后续只追加状态及审查准备，加入一份 Q5.1 计划记账。报告写入前的实际作者集合为下列 **17 文件／465,661B**，所有产品／测试与冻结 r1 逐字相同。相邻 Q4.1／Q5.1 旧报告仅检查追加记账的范围与归属，不递归重审原片或替它们认证 CI。

|作者文件|字节数|SHA256|
|---|---:|---|
|`docs/LOCAL_REVIEW.md`|9347|`483d068db3fe162c3133a08baafa6ce07e534a22bc558e96b276ee927d319926`|
|`docs/PLAN.md`|45088|`0607fa4ae1354310b2bcdcef951645601e4969b7a2f7cadb08b2a7837b28380a`|
|`docs/USAGE.md`|169520|`7a3a60ba96aa91f9f9d96e82c56c5fb00394023af9b998185ac0a4d4b17eb0e1`|
|`docs/delivery/2026-11-15-component-change-protocols-review.md`|11420|`a47ffb8e8cb1b8f71bcf449e129e200fd8d94439d63b820d8523888bd880cdac`|
|`docs/delivery/2026-11-15-component-change-protocols.md`|4543|`f6072eddfd442e89475cc8032272b31eb387878970f029ae7ecf6938cf8e5c4c`|
|`docs/delivery/2026-11-15-external-review-sources.md`|4289|`3b957825141332e174da6f2560342285de260c88ca85b0aa8cb057c09c0ff12c`|
|`docs/delivery/2026-11-15-training-round-chains-review.md`|15832|`93d3ffc7a57f8d9374ec2ba2b6e8449e9cdc4415b5b88120eacc6740706c0f52`|
|`docs/delivery/2026-11-15-training-round-chains.md`|7693|`66ed498e929e080375cf79a8b9fb9602967e1910a2dcb6e291eaf994971babdc`|
|`docs/plans/2026-11-15-component-change-protocols.md`|4360|`1896f18b49c94c04f8cb6605c435cf33b6d26a97a2f48171081761ddc2c1da07`|
|`docs/plans/2026-11-15-domain-review-optimization-quality.md`|29945|`448f2160f94c8efe9d4a0cb51b386672a926ba4e2632f431afe91db93be94475`|
|`docs/plans/2026-11-15-external-review-sources.md`|4986|`39c2d45018f600a2575344ccc94f22d0a8d9b972754f05eb8b228e09bd686daf`|
|`docs/plans/2026-11-15-training-round-chains.md`|5734|`67e10c9532141dd4527906e56921716e46c2792ba9f75cfc357eaffef85efde8`|
|`src/ergora/cli.py`|89573|`03ae2d5941c66dc303f9fe720be227578bc1a5380abe94690d8bde42e122e8ab`|
|`src/ergora/data/schemas/external-review-source-v1.json`|1414|`8038dad7b987ed9509c3dfd7142048fc8eefd6dee8a5f65da208777dd44b2462`|
|`src/ergora/issue_backends.py`|33709|`bb3bf4f0642e4d3f20b933fde815891b53cbc523ccfc4be83b52923579c0c384`|
|`src/ergora/review_sources.py`|5868|`d97992101cdbca005a4b44f734ae5b673fac42452abb527b4787c971cb7b732d`|
|`tests/test_review_associations.py`|22340|`1046176e2fcf2130f99feb8d50dad78a0def0df2af56724856c6ed4e44f3b1e9`|

剩余验收：R1 修复、受影响接缝及新精确安装身份、同片复核；Q5.1 自己的 CI 终态及原独立闭合前保持后继产品 push 门禁。本片之后仍须核固定普通发布／完整远端 Ref 及自己的适用 CI。Windows 新来源入口、完整真实平台采集、领域审查组合运行不由本次本地原件认证；未验训练质量、数值／梯度／分布式、性能、自动循环或完整 Forge。kernel 专家所在优化路径没有改动，允许其得出无需 kernel 修改的原要求保持。

## r2 R1 修正同片复核（2026-11-15）

同一独立评审者已核对修正与新原件：**R1 关闭；r2 需求符合性 approve／结构可维护性及测试价值 approve，开放实质 finding 0／0。** 本节覆盖上文 r1 的 request-changes／R1 开放及待修后本地复核状态；r1 原失败、原模型 approve 和原安装身份保持历史范围。此结论是本地修正终核，不认证普通发布或 CI。

产品仅将 `review_sources._repository_id` 改为 `native-repository-sha256:` 加完整规范身份的 SHA256。`collect` 与 `_check` 继续调用同一函数；封套保留完整来源／native 仓库字段，原本地包 schema、有效 binding 范围和原包读取器均未改变。该修正没有截断身份、放宽原合同或引入新的 owner／注册／分派。r1 外部封套是本片未发布开发原件，仍保留供历史核查；未添加为这些旧开发 ID 放行的兼容分支，原独立本地包合同保持。

独立使用 r2 安装作一次无网络／无文件写入的内存核验：上文合法长配置的原规范 JSON 仍长 **1,165**，新 ID 恒长 **89**，原 `repository.id` schema 接受；六个原身份字段分别变动时摘要也变动。这是对 R1 边界的补充核验，不代替完整采集接缝。源码中不存在按字段截断或遗漏身份后再 hash 的路径。

新增测试留在原 `test_review_associations.py`，两平台均通过原 HTTP 服务和真实 Git 调用 `collect → read`：300 字符 project 与长代理路径实际进入仓库／单 review 的请求路由，读回保留完整配置与原 merge-base，并核两次实际请求地址。预期来自传入的有效配置，没有断言摘要字面量或复制 hash 实现，保护的是本次曾实际失败的合同组合；没有新增测试文件、CI job 或重复原本地包矩阵。

|r2 原件／轻量核验|独立结果|
|---|---|
|`long-config-red-r1.xml`／原完整 stdout|两平台各一例真实失败，调用栈在原 `review_packets._check → contracts.validate` 的 `/repository/id` 报完整 JSON 过长，stdout **2 failed／2.03 秒**；不是在测试中改断言制造失败。|
|`source-tests-r3.xml`／stdout|原六项加两项长配置，共 **8 通过／6.34 秒**。|
|`installed-tests-r2.xml`／stdout／stderr|原四 suite **119 通过／61.54 秒／0 跳过**，包括两项长配置，只有原 Starlette deprecation warning。此处仅重解析归档结果，未重跑。|
|`package-r2.json`／新 wheel／r2 安装|**642 源＝642 wheel＝642 非 editable 安装**逐字同且匹配清单；隔离解释器实际导入 r2 site-packages，direct_url 指向 r2 wheel。wheel SHA256 `338db58dafa7f953723d1651e8952c5fab350c1bd2a9d69b83eadd1d86121f5c`；相对 r1 wheel 仅 `review_sources.py` 变化，无新增／删除产品，283 reference 及原本地包 schema 逐字保持。|
|`native-journey-r2.py/.json`／14 对原 stdout、stderr|逐项 SHA 与索引一致，重新运行的原命令分别记录成功及错 SHA／不覆盖／超限／缺对象拒绝；离线两种读取的 PATH 空设置明确，两层完整输出与现存原包逐字段相同。没有用 r1 包或 r1 原输出替代。|
|r2 两个新包及保留 Git|来源／内层摘要和回执一致；独立重算完整身份的摘要 ID 与两包相同，需求／检查字节保持。另用只读 Git 核三提交所选文件表 7／7／6、9 个 blob、四个变化路径及唯一 merge-base，全同。现存 Git 48 文件、未使用 home 不存在可重核；当时前后保持、各 8 GET／无 branch GET 及服务关闭仍按 driver 断言和保存结果记，不声称存在完整 before manifest。|
|r2 自身原结构模板|原 run `7a6580ee85be4996a695220d3e62e6e8` succeeded／exit0／**38.799665 秒／approve**。直接核 25 完整文件／535,623B、完整 task 和三份祖先资源在实际 stdin 中；prompt＝stdin，prompt SHA256 `9f7880b9e708f75f07101b1a8d3f707a91e78326838408845486b3f55e656330`；input digest `0604ff09de688f5f02991353f8b9be3d5dc74c1e4204c5497ab4a79d01c9cf64` 与原 run 相同；result 与保存副本逐字同，SHA256 `cb8e79fc70d21ab0bf27138eb1ce541d8fca97ce54be7f72f3cb23c73d19d716`。它仍只审给定文本，不替代本次原件核验。|

r2 新包独立摘要：GitHub source `263e8094f1a74d96d72301e3750cc83d715e30860f08af253d0f0bf18c058540`／packet `3ddd487b3211640a457cd44467ce4cc0c24a3f31014dc34911fbe328a6a89dc4`；GitLab source `928bfcf9bf065ea3c81977c0f0cac606bf385703b69c5226cf6451b01bc5b72f`／packet `81ebe5cadfec7d297f567f5205f98a5c24031959e7f164506c468dc3a40fee68`。原 r1 四个摘要及其原件未改写。

基线／当前 HEAD 仍为完整 705。`review-scope-r2/scope.json` SHA256 `895ed7e708b91dda7d3d35767129f1f8a9f2298bcca637c5637d7d58c28dd786` 的 **18 文件／482,556B** 全部逐项核同，其中原本报告 **12,964B／SHA256 `b44072e8b8aea7ee70589a632967a52a70f93f710ed1b19b96d678a59a5e9be1`** 在本节追加前保持完整。相对该冻结范围，作者后续只补四份状态文档（本片自身结果、Q4.1 终态表述及 Q5.1 CI 中间观察），已读差异；产品／测试未再变化。追加本节前实际 18 文件／483,184B，身份增量如下，其他文件沿 r2 原清单：

|文件|字节数|SHA256|
|---|---:|---|
|`src/ergora/review_sources.py`|5966|`681bdb5880ccd6eaf743dd6ac733844c4be2ef104474e7467377d14973dc9423`|
|`tests/test_review_associations.py`|24247|`47bf035504314dfceef76b41ef34a0369ea6b5075ed14743ba9fc5d4113efd1a`|
|`docs/LOCAL_REVIEW.md`|9476|`998d1ea6580255797566684d86bc12b2e6c948e6314784cc96943edd909eafa4`|
|`docs/PLAN.md`|45259|`052574e0c3714b25264639a12a6895021717873d1a22f86149355aded1633016`|
|`docs/delivery/2026-11-15-external-review-sources.md`|6397|`9f69c3f81f4eff75fa21eb7bb6fda57073d1429ef375361a9becedc33bb2c934`|
|`docs/plans/2026-11-15-domain-review-optimization-quality.md`|29951|`666cbfb9b2ec7c3d1f269ea2d9a1dd1647f839bbc2c48bf999daf1034d5201e4`|
|`docs/plans/2026-11-15-external-review-sources.md`|5126|`d58bae2417dcdf1114c51cd86d7fe174cfa25ed4d5b777238b1099bd3b3f85e4`|

独立重核 **13 份 Markdown／285 本地链接及 fragment 零错误**，tracked 及新增文件完整 whitespace 检查无误。本次只追加本报告；未安装、重跑测试／模型、启动服务、训练、提交、推送或平台写入。只凭包无法认证真实 commit-tree membership／merge-base、完整真实平台成功及原检查可信度的限制保持。Q5.1 自己的 CI 终态及原独立补核尚未闭合，后继 push 门禁保持；本片普通发布／完整远端 Ref／自己的适用 CI 及同片终核仍待验，未扩大为 Windows、领域组合运行、训练质量或性能验收。
