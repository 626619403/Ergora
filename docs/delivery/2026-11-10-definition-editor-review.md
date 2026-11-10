# AC5 C3b：定义编辑会话独立审查

基线 `34afcc2cec5a38655cfc93513173d67bbc433c02`；首审固定 `review-r1`，其 `identity.json` 的全部 **11 个 tracked/untracked 文件**逐一 SHA256 复核一致。审查以保存的 `tracked.diff` 和 `candidate/` 原件为准，不将仍在变化的工作区当作 R1。基线之后无新增提交，本片为未提交差异。

先读取差异及真实调用者 `app.js`、`api.js`、`ui.js`、原工作单元编辑器、两类定义用例和 `DefinitionLibrary.revise`，再读取作者交付记录。按 `code-review` 的两个 fresh-context 审查轴及 `codebase-design` 接口原则复核；原始要求和范围来自[本片计划](../plans/2026-11-10-definition-editor.md)、[C3 发布合同](../plans/2026-11-10-definition-revisions.md)及项目 AGENTS。资源追加、嵌套画布、正式任务交接分别归 C3c/C4/C5，不作为本片缺项。

**当前提交前终核：完整30文件的 Spec／Standards 本地通过，五项 finding 全部关闭，零开放 finding。** R3 产品、非 editable 包、受影响回归、56项实际页面检查、两轮自身模板原件、11份公开JSON与2截图及清理均已独立核验。原R1／R2不通过和首轮 `request-changes` 保留。提交前同步本结论与记账清单；本候选自己的提交对象／必要 CI／独立明确 HTTPS仍待验，不登记精确交付终结。

**R1 当时结论：暂不通过。** 下列四个问题已有固定源码复现或精确可达路径；原红及原件保持，R2 关闭依据见后文。

## Spec

### DE-S2：控制目录已经改变时，旧页面仍可发出写请求（P1，R1 开放／R2 关闭）

- **规格**：C3 发布合同要求“编辑序号、固定基准及控制目录共同限定迟到回复”；本片要求“换 home 与失败恢复不混库”。
- **可达场景**：A 控制目录没有项目，操作者在库中检查好待发布正文。同一来源改为 B 控制目录且 B 有项目；全局刷新取得 B 的 bootstrap 后等待其 dashboard。`app.refresh` 已把 `app.bootstrap` 改成 B，A 的定义视图此时仍可见。点击原 A 的发布按钮，`editDefinition` 会先 redraw 到 B，但随后仍发送 A 会话的修订到当前 B 服务。如果两库都有同一个原包，该请求可以在错误的库发布。预置导入也缺少发送前的同一守卫。
- **位置**：R1 [definitions.js](../../src/ergora/data/console/definitions.js) 121–129、166–177、272–283；实际窗口由 [app.js](../../src/ergora/data/console/app.js) 的 bootstrap／dashboard 顺序产生。只在收到回复时检查目录不足以阻止已经发生的写入。
- **独立证据**：私有 `independent/reproduce-home-guard.cjs` 直接执行固定原函数和真实 `refresh` 函数，输出 `bootstrapHome=home-B`、`renderedLibraryHome=home-A`，点击后记录发到 B 的 A 修订及回执；没有调用真实远端或模型。
- **最小修正**：在定义编辑操作和预置导入发送前校验原目录仍为当前目录；目录不符应刷新视图并停止旧操作。保留响应世代检查。补实际 A/B 服务与延迟 dashboard 的浏览器验收，证明 B 没有收到 A 的发布或导入。

### DE-S3：应用另一表示会静默丢失已应用原文（P2，R1 开放／R2 关闭）

- **规格**：本片 B3 要求“表单/JSON/YAML 各原文不互相静默覆盖”，所有者合同要求保存独立 JSON/YAML 原文。
- **可达场景**：先应用带操作者注释的 YAML，再仅调整 JSON 排版并应用。语义完全没有变化，`applyEditor` 仍用生成文本覆盖另一格式，YAML 注释消失。旧文本仅暂留有限历史；当前缓存不保存历史，刷新后不能恢复原注释。字段应用也经过同一路径。
- **位置与证据**：R1 [definitions.js](../../src/ergora/data/console/definitions.js) 99–106；私有 `independent/spec/probe.mjs`／`probe.json` 直接执行固定原函数，确认 `semanticDefinitionUnchanged=true`、`annotationRetained=false`、当前持久缓冲不含旧原文。
- **最小修正**：语义不变时保留另一格式原文；语义变化时明确标记旧表示过期，并保留可下载原字节，待操作者明确采用生成结果或放弃。无需编写 YAML 格式保真器，也不应靠扩大历史保留量代替原文合同。

### DE-S4：恢复时只核 JSON，未确认已应用 YAML 的语义（P2，R1 开放／R2 关闭）

- **规格**：本片 B2 要求原文／语义分离及损坏缓冲可恢复原字节／清除；C3 接续合同要求通过共同严格解析所有者处理两格式。
- **可达场景**：浏览器缓冲 JSON 尚能解析，但 `texts.yaml` 和 `appliedTexts.yaml` 已一起损坏，或同为另一份完整合法 YAML，而 `definition` 和已应用 JSON 仍是原正文。恢复仅核对 JSON，会得到 `restoreError=null`、`pending=false`；操作者可检查并发布与所见 YAML 不同的语义快照。
- **位置与证据**：R1 [definitions.js](../../src/ergora/data/console/definitions.js) 59–65、71；私有 `independent/spec/probe.mjs`／`probe.json` 已复现非法 YAML 被视作已应用且无待处理文本。完整合法 YAML 仅改描述的异义情形由相同恢复条件直接推出，不依赖 YAML 错误处理差异。
- **最小修正**：恢复时经原转换所有者校验两份已应用表示与语义正文一致；失败进入保留原始缓存的下载／清除入口。未应用文本仍可无效，应原样保留，不能拿它替代已应用快照做完整准入。

### DE-S5：恢复后的首份历史包含未应用原文，撤销可误标为已应用（P2，R2 开放／R3 关闭）

- **来源与规格**：本候选真实自身模板首次提出；本片要求未应用文本阻塞检查／发布，历史与缓存不得降级原文／语义的分离合同。独立审查不将模型结论直接当作成立依据。
- **独立可达复现**：当前已应用正文为 `1.0.71`，另留未应用无效 JSON 或 YAML，刷新并重新选择该版本。恢复后修正文为 `1.0.72` 并应用，再撤销。R2 首历史复制了恢复时尚未应用的无效原文；撤销把它同时写回 `texts`、`appliedTexts`，同时将语义正文恢复为 `1.0.71`。两种格式都变成 `pending=false`，检查实际发送旧的 `1.0.71`；取得检查回执后发布谓词允许，而可见原文仍无效。此状态再次刷新才被当成损坏缓冲。
- **位置与证据**：R2 [definitions.js](../../src/ergora/data/console/definitions.js) 43–46、102、545–551；私有 `independent/spec/r2/de-s5.{mjs,json,log}` 直接执行固定原函数，JSON/YAML 两格式均复现上述状态与实际检查请求内容。回执仅在函数边界模拟，没有发出实际发布或网络请求。
- **最小修正**：已应用历史快照只复制 `current.appliedTexts`，字节预算也按相同文本计算；未应用 `current.texts` 继续保留在工作检查点，不进入已应用历史。补原安装 R2 两格式红证据，并在新候选验恢复→修正／应用→撤销→再次刷新，核原文／语义一致和发布阻塞规则。

其余已读实现沿用完整原包、精确原摘要和原权限／引用／预算准入所有者；未发现另建发布账本、修改旧任务或实施 C3c/C4/C5 的越界。这些正向观察不等于整体通过。

## Standards

### DE-S1：未准入的中间正文与字段呈现接口没有完整隔离（P2，R1 开放／R2 关闭）

- **规则**：本片允许复杂正文通过 JSON/YAML 显式编辑，完整准入归原库；字段表单必须可从不适合呈现的中间正文回退到原文修复入口。这是可达的错误恢复问题，不是代码风格偏好。
- **可达场景**：正常 Workflow 仅将 `ref.digest` 改成数字、null 或删除，正文仍是允许转换的 JSON 数据树。R1 `formValues` 接受它，随后引用选项执行 `item.digest.slice` 抛 `TypeError`，整页编辑区无法呈现。刷新会重载同一缓冲，再次触发。另将 `nodes` 暂改成含非数值 `length` 的对象，应用会令 `selectedNode=NaN`；修回正常节点数组也无法恢复字段，缓存又将此值写成 null。
- **位置**：R1 [definitions.js](../../src/ergora/data/console/definitions.js) 329–343、408–409、107。转换入口只承担 JSON 数据模型检查，不能要求它替字段呈现复制完整 schema 准入。
- **独立证据**：私有 `independent/standards/reproduce-de-s1.cjs` 和原输出，固定源码 SHA256 `ac3723a8ab8652eafaf3ab1f7feaf3a5d5589123ede156bce148970f14a66ad2`；有效引用为绿，数字/null/缺失摘要为红，选择索引的 NaN 持续性也已复现。
- **最小修正**：只补字段呈现实际需要的引用字符串形状，无法呈现时保留原文区；选择索引按实际数组长度并用有限整数兜底。补真实浏览器中应用非法中间正文、刷新、再修回正常正文的旅程。

未发现需要另立的结构 smell：转换复用原 `definition_bundles`，CLI/HTTP 保持薄入口；页面历史与旧工作单元历史虽有小段裁剪逻辑相似，快照语义不同，尚无强制抽取通用框架的依据。新增格式拒绝测试覆盖外部输入风险，未增加依赖、CI 任务或广泛重复回归。

## R1 实际验证与当时未验门禁

- 已读原日志：源码 console **18 passed / 13.73 秒**；原库 **137 passed / 1 平台 skipped / 45.39 秒**；HTTP/web **26 passed / 24.29 秒**。这些是作者执行的源码检查，独立审查未重跑整组。
- 独立执行：11 文件原件身份复核、上述固定源码轻量探针。另核 JSON/YAML 孤立 surrogate 的 HTTP 转换均以 400 明确拒绝，未据此登记 finding；也未找到当前准入字段能够承载不安全大整数，未将通用浏览器数值精度问题扩大为本片 finding。没有安装、模型调用、远端操作或源码修改。
- 尚未验收：修正后的完整候选身份和回归证据；两类定义完整浏览器旅程，含迟到转换／检查／发布、切目录、缓存损坏／quota 和有限历史；三领域往返；非 editable 安装包、实际 CLI 及完整附件身份；两本手册／架构声明；本候选真实自身模板；本候选自己的必要 CI 与明确 HTTPS 精确身份。
- C3a `34afcc2…` 自己的 CI 与 HTTPS 已完成，只证明 C3a；不替代本片门禁。当前不登记 C3b 或整个 C3 完成。

R1：Spec 3 项开放（最严重 DE-S2），Standards 1 项开放（最严重 DE-S1）。

## R2 同片复核

固定 `review-r2/identity.json` 的全部 **17 文件**已独立逐一复核。产品源码摘要为：`definitions.js` 的 `675299a03b8d9f7e0b5b25d2e0a1a8bb2812e1ad89fa91b7e9d90f860bfb4846`，`definition_bundles.py` 的 `c39109c44f58e08a364dd097db5282ed8c101632e9f7caa8a8f4bc5f7c88df28`。继续使用原两轴审查者按原反例复核，未重装、重跑整组或调用模型／远端。

|轴／finding|修正与独立关闭证据|结论|
|---|---|---|
|Standards／DE-S1|R2 358–361 行只核引用呈现所需字符串；124–125 行使用实际节点数组夹选。原 Node 探针的畸形引用均安全回退，畸形节点修回后索引为0、字段可见；安装浏览器五种中间正文都可应用、刷新和修回。|关闭|
|Spec／DE-S2|R2 140 行在发送前同时核目录与当前会话，302 行拦截旧预置操作。独立原 `app.refresh` 探针复跑保持 B bootstrap／A 旧视图窗口，点击后请求列表为空、无回执。真实安装 A/B 服务及私有代理的原件也证实旧按钮无写入 B，两个库都没有错误新版本，回 A 保留原候选与检查。|关闭|
|Spec／DE-S3|R2 113–122 行在同语义转换保留另一原文；181–185 行在更改语义并替换自定义原文前请求明确同步。固定源码探针确认 YAML 注释仍写入缓存，取消保留 JSON／YAML／字段缓冲，接受才替换；安装浏览器复验同样通过。|关闭|
|Spec／DE-S4|R2 75–83 行经共同转换所有者核两份已应用正文。固定源码和真实 Python 转换探针确认合法异义 YAML、非法已应用 YAML、重复键已应用 JSON 被隔离且保留原缓存，未应用无效 YAML 仍可恢复；安装浏览器拒绝两类损坏已应用 YAML。|关闭|

私有独立证据为 `independent/review-r2-identities.json`、`review-r2-package-identities.json`、`review-r2-cli-evidence.json`、`review-r2-browser-evidence.json`、`reproduce-home-guard-r2.{cjs,log}`，以及 `standards/r2/` 和 `spec/r2/` 下的原探针、输出。Spec 定向探针九项通过；其首轮漏载原 UI `lines` 的探针配置错误原输出保留，补载固定基线所有者后通过。

### 完整候选与验证证据

- 独立重新计算 **435 个源码／wheel／安装／RECORD 文件**身份，逐一一致；**283 个冻结文件**与清单一致，基线参考树无差异。R2 wheel 精确 SHA256 为 `e6229c708b320677423779e86f727bdbf920caa1111eceddf62bda4ff8140fd8`。
- 读取七组安装回归原日志：**193 passed／1 平台 skipped，79.05 秒**。三域 **54 次隔离实际 CLI／24.57 秒**的全部 stdout／stderr 与回执逐例核对：六份定义的 JSON/YAML check 等候选且不发布、明确发布与同正文重试等结果、完整附件保持、导出再导入同摘要；三个旧 manifest 的验证摘要一致。训练范围保持只读提案定义。
- 读取 R2 实际安装浏览器脚本、原日志、命令元数据及 JSON 结果，并核脚本／日志摘要和日志内结果一致：`basic-01` **16 项／5.04 秒**，`home-01` **7 项／3.18 秒**，`fields-04` **14 项／11.63 秒**，`errors-01` **9 项／8.21 秒**，`races-01` **8 项／4.00 秒**。覆盖两类发布、三类实例增删、职责／角色／精确引用／预算、越父权限和缺依赖拒绝、端口相关重命名、迟到保护、已发出发布后丢响应与显式幂等重试、不可变版本冲突、缓存损坏／quota、390px 呈现、50 份历史与单份超过4MiB仅保当前。字段脚本的前三次 locator／选中实例错误原件保留。
- 同步确认的取消／接受在 `window.confirm` 函数边界显式模拟并记录选择；原生框出现的先前原件另存。当前证据支持调用条件、文案和两个分支，未将其记为原生弹窗按钮点击。
- 读取稳定生成顺序的 R1 原红：原往返用例 **1 failed／17 deselected／0.77 秒**，确为 JSON 再转换后生成 YAML 顺序变化。R2 最小 `sort_keys=True` 使自动表示稳定，原用例增加一轮已有转换接口的断言，已包含在安装回归中；不扩大回归组或增加 CI 任务。
- 完整差异与邻近调用者复核未发现新增 Spec／Standards 问题。转换、完整包派生与准入继续分别归原所有者；`sameValue`、`referenceText` 各有实际共同消费者。两套历史的领域快照不同，保留小段局部裁剪逻辑有依据。README、使用手册及两类定义手册准确区分正文／完整包、配置／认证、浏览器缓冲／持久版本及后续资源／画布／任务范围。

### 仍待终核的门禁

真实自身模板 R1 已完成：**343.92 秒／succeeded／request-changes**，提出 DE-S5。独立从原 manifest、prepared input、实际 run input、prompt 与 result 重新核身份，并从原 native stream 重建 **405066 字节／17 个连续 UTF-8 页**至 `next_offset=null`，无失败读取；四份祖先指令／Skill 与实际输入资产逐字节一致，18 份产品／邻近源文件覆盖固定 R2 或未变源码。私有 `independent/self-review-r1-audit.json` 保留核验。完整送达与审查质量分开记账；该运行使用已授权 Codex 回退，未宣称不同模型独立性、OS 隔离或正式批准。

DE-S5 修正及新候选的安装／浏览器／同片复核和自身模板仍待完成。最终计划／交付／公开证据、服务与浏览器清理待补齐；本候选未提交，自己的必要 CI 与明确 HTTPS 精确身份均未验收。C3a 的既有通过不替代这些门禁。

R2：Spec 原3项全部关闭，新增 DE-S5 开放；Standards 原1项关闭、无新增 finding。此前四项复核结论保留，R2 整体本地结论因新增实证问题改为暂不通过。

## R3 同片复核

固定 `review-r3/identity.json` 的全部 **17 文件**已独立逐一复核；当前产品 `definitions.js` SHA256 为 `994650b714f7ac50929074e41349e02fcb7a899125f095c06bbd6a29d84d54f2`。相对 R2，435 个包文件中只有此文件改变；转换所有者、CLI、HTTP 和既有测试身份均不变。两轴沿用原审查者按固定 R3 原件和原反例独立复核，没有安装、调用模型或操作远端。

### DE-S5 关闭依据

R3 43–48 行仅将已应用历史快照的两份原文及字节预算改取 `current.appliedTexts`；未应用原文仍由工作检查点保留，历史形状、撤销消费者与缓存接口保持不变。独立双格式原探针确认恢复→修正为 `1.0.72`／应用→撤销后，正文正确回到已应用的 `1.0.71`，可见原文与语义一致，检查发送同一正文，再次恢复没有损坏错误。此时允许检查／发布的是可见且有效的撤销结果，没有借禁用撤销绕过反例。

实际安装的 R2 `history-change-red` 与 R3 `history-recovery-01` 使用同一脚本，SHA256 为 `160bcda18bd7e4b648e9f8dc35894467ce1dbd612039fc1969af5d0bc8c7d3b8`。JSON/YAML 两例均从无效原文可见、误标已应用、刷新报损坏，转为撤销保持启用、恢复已应用有效原文且刷新正常。原红及自身模板的 `request-changes` 不覆盖、不改写。

Spec 另复跑 S3/S4 的九项原探针全绿；Standards 直接执行固定快照函数，确认已应用文本与未应用检查点各自保留、文本对象独立复制，含中文和注释的双格式样本 UTF-8 字节预算为 **271 字节**，与实际保存内容一致。未增加抽象、状态分支、依赖、永久重复测试或 CI 成本。私有原件见 `independent/spec/r3/{de-s5,probe}.{mjs,json,log}`、`browser-evidence.json` 和 `independent/standards/r3/snapshot-interface.{cjs,log}`。

### 候选身份与受影响验证

- 独立重算 **435 个源码／wheel／安装／RECORD 文件**逐一一致；**283 个冻结文件**与清单一致，基线参考树仍无差异。R3 wheel SHA256 为 `901f9f15d8f5cfc66d02615bc8454fa830ff0441f16301f83d06e499bd21e200`。
- 已读 R3 安装回归原日志：console 18、architecture 11、reference 6，共 **35 passed／15.89 秒**。R2 的 **193 passed／1 平台 skipped／79.05 秒**与 **54 次实际 CLI／24.57 秒**保持原轮次，不冒充 R3 重跑；除浏览器文件外其余434个包文件身份相同，故未重复整组。
- 独立读取 R3 六组实际安装浏览器脚本、原日志、命令元数据和 JSON，核脚本／日志摘要及日志内结果一致：`basic-01` **16 项／4.81 秒**，`history-recovery-01` **2 格式／4.58 秒**，`fields-01` **14 项／12.05 秒**，`errors-01` **9 项／8.22 秒**，`races-01` **8 项／3.95 秒**，`home-01` **7 项／3.11 秒**，合计 **56 项**。原 R2 覆盖在新包复验，新增 S5 两格式恢复旅程；同步确认仍只记函数边界的显式选择。

身份与证据核验原件为 `independent/review-r3-identities.json`、`review-r3-package-identities.json`、`r2-r3-package-difference.json`、`review-r3-browser-evidence.json`。R3：Spec 四项关闭、Standards 一项关闭，无新增 finding；两轴本地通过。

### 第二轮真实自身模板与清理

第二轮实际运行 `85d196f49f0b49e18dffcea5dc0f3664` 为 **317.23 秒／succeeded／approve**。独立读取原结果与审查正文，从原 manifest、prepared input、实际 run input、request 和 prompt 核身份，并以固定 R3／未变基线逐字节核18份完整源文件。原结果 SHA256 为 `2faf9eea8dd8db720b509748b33cee898cbfa5318680921a0f856434ffe17217`，附件 **474163 字节**的 SHA256 为 `01e27326a7e1c95e7153f75581a2836526d096c27eac6f13795012a3b4e818a9`。

从原 native stream 重建 **17 个连续 UTF-8 页**至 `next_offset=null`，逐页与附件原字节一致。offset 0 的原28000、27999字节两次base64响应均保留并在同offset重试，27998字节UTF-8成功后才推进；未把两次非明文响应算入完整阅读页数。四份继承指令／Skill 与实际输入资产逐字节一致，无失败读取。私有 `independent/audit-self-review-r2.py`、`self-review-r2-audit.json` 保留原件审计；原首轮 `request-changes` 及 S5 红证据继续保留。此轮同样使用已授权 Codex 回退，不宣称不同模型独立性、OS隔离或正式所有者批准；完整送达与审查质量分别记账。

清理原脚本及 `cleanup-old.json`／`cleanup-final.json` 已读，合计 **11 个 owned HTTP／代理进程、8个专用浏览器会话**。记录逐一匹配保存的PID、starttime、argv后才停止；独立仅读取 `/proc` 与监听表确认11个保存PID当前不运行、对应端口无监听，并核8个专用关闭命令成功及名称一致，没有执行信号、服务连接或浏览器操作。私有证据为 `independent/cleanup-audit.json`。

最终公开证据／文档及本候选提交／CI／HTTPS仍待验。当前结论为零开放 finding、两轴本地通过、第二轮自身模板通过，不登记精确交付终结。

## 完整30文件提交前终核

固定 `review-final/identity.json` 的 **30文件**逐一SHA256独立核对一致，tracked与untracked范围完整：4生产文件、1份原测试、12份文档、11份公开JSON及2截图。5份产品／测试与固定R3字节一致，18份实际模板保护源未漂移。冻结之后只有本审查报告追加本地结论，作为记账差异单列；最终提交须包含更新后的报告和对应清单，不冒称旧冻结摘要覆盖新段落。

逐字段对照13份公开文件与私有原件，包的435文件身份、三领域原R2 CLI、原R2两组S5红、R3六组页面结果及命令、11／8清理与两轮模板身份／原意见／独立读取审计均准确投影。原native结果摘要和经去目录格式化公开JSON的文件摘要明确区分，未把公开投影摘要当成原模型结果摘要；两图与原截图字节一致并已目视核阅。公开文件不含个人目录，原缓存、模型流及机器进程身份留在私有原件。独立脚本与结果见 `independent/audit-final.py`、`final-artifact-audit.json`。

两类手册、README及页面说明与实际字段／原文／固定完整包发布边界一致；配置请求不代表安装认证，库级修订不持有项目grant、不构成运行批准，C3c／C4／C5／C6继续另列。已读最终静态原日志与文档摘要：**12文档／243链接无缺失／98条手册命令parser通过**；该结果只证明静态路径与语法，不替代实际CLI或页面。之后审查状态记账更新应同步静态记录，未引入产品重测需求。

**本地门禁终结：Spec／Standards通过，DE-S1–S5全部关闭，零开放finding，可按原授权普通提交本片。** 本候选尚未提交；精确Git对象／包／冻结身份、自己的必要CI与独立明确HTTPS仍待后续分别核验。C3a既有通过不替代本片，当前结论不声明整个C3或AC5已完成。
