# AC5 C2 编辑会话独立审查

日期：2026-11-09—10。审查者：fresh-context `editor_session_review`，并按 code-review skill 启动两个 `fork_turns:none` 的只读 Standards／Spec 子审。已读项目 AGENTS、[当前计划](../PLAN.md)、[AC5 规格](../plans/2026-11-09-composition-console.md)、[本片交付记录](2026-11-09-editor-session.md)，以及 AIHERO 索引所指的 codebase-design、code-review、maintainable-project-delivery 和独立审查 brief。

## 身份、范围与当前结论

固定产品基线 `61ccc2cce8bfcc3a46b4a069c78ea660f76063d9`；审查时 HEAD 为 `03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`。已用 `git diff --exit-code 61ccc2c HEAD -- src/ergora` 确认二者产品正文相同。03 的测试精度修正及其 CI 不属于 C2 验收。

初始生产审查命令为 `git diff HEAD -- src/ergora/data/console/workflow.js`；S7 同片复核还包括现有 `app.js` refresh 所有者的最小修正。C2 文档包括 tracked PLAN／AC5 plan、USAGE／current architecture 和 untracked editor-session 交付／审查记录；并行更新的 deadline-precision 文档不纳入本片。另读实际调用者 `app.js`、`state.js`、`ui.js`，原 `drafts.py`／Web 路由、输入 schema、Web／架构测试和 ADR0003。没有修改生产、测试或原始证据，没有安装、启动服务或模型、提交或推送。

|受审身份|SHA256／用途|
|---|---|
|R2 wheel|`9e7b14c878b5ab2ec83ae288fa2f9ad3fcf6b80d698a72bf64b3dc45958f101f`|
|R2 workflow.js|`aa86721405de3ae0d32c69b1af8ad8531170235dbb30992cb653d708ebf513b4`；保留 S1 原红|
|首轮本地受审 workflow.js|`5cbd356705857d0d5f05d57229d35410ff0b1b0ad94543bd8f634158a8cf0bac`；S1 最小修正后、S2/S3 修正前|
|本轮两轴受审 workflow.js|`e6dc36c41a004b894bc684a33a326c3a605e18bd2395a7a50e97192d34ecbb81`；两个子审首末读取相同|
|R3 wheel|`885a8f1b7cf8be785bba9276da0ab3f827360ed908219723d894e2f811a77a8d`；本审查独立核 wheel／安装／record 的 435 文件全等|
|S4 源码复核 workflow.js|`07a9756708f2ba3a0b1e681267251fa3316b78972e3ccd1fd5650e1a1d23b592`；相对 R3 唯一差异是单元选择 change handler 的局部焦点恢复|
|R4 wheel|`fb0568b8182965977e39f269f6620fe665e9415dddada1fb2fe9bb68deaa7cda`；源／wheel／安装／record 的 435 文件全等，workflow.js 为上述 07a9756|
|R5 wheel|`2dd4478f4549059ac4dbb52198b94cebf9543f3e57efbf85db7ded077e87fdfe`；源／wheel／安装及两份 RECORD 的 435 文件全等|
|R5 workflow.js|`8427d68d5b59d2973e568d7e041182068c587fc888f4b96b512f0d6cc19bab75`；S5／S6 修正，R5 原反例与合法改名正路径已核|
|R6 wheel|`fa7a42a7fb83f61dd302ac9b5c705f3aac782d0ebaaa1f30eadddc0f47f7398e`；435 文件全等，283 冻结不变，相对 R5 只改 app.js|
|R6 app.js|`7458b8aa9704a8bb97b6dc4073833a681343b71a8c9ad2767e8e8ea0699e0b2c`；保留数据目录身份并单调合并草稿；workflow.js 仍为上述 R5 身份|
|R7 wheel|`722ece41c54347d60f3216a27d8b1b66c09cebc582c2ede1396e3f9f2e90b796`；435 文件全等，283 冻结不变，相对 R6 只改 app.js|
|R7 app.js|`6b624fe6e6a302e66663d69289626669b4a2a3f9792f5359cfb0f8b090dbbedf`；新目录／项目 dashboard 返回前同步隐藏旧 data；workflow.js 仍为上述 R5 身份|

**本地终核：完整 25 文件的 Spec／Standards 通过，S1–S8 已关闭，0 开放 finding；可普通提交本片。** R7 包／旅程、第四轮真实模型、完整明文读取、公开投影、截图及 owned 清理均已独立核验。提交／推送对象、当前 C2 自己的必要 CI 与明确 HTTPS 同 SHA 仍待验；完整 E5 尚未精确终结。

**可维护性：受审差异内没有新增硬标准违规或阻塞性 smell。** 原 workflow 生命周期所有者仍合适；C3 尚未提供第二个生产消费者，无需提前抽取共享编辑框架。浏览器状态与编译／保存合同分别由现有所有者负责。

## Standards

以下为 R3 包复验前的 fresh-context Standards 子审结果，轻量整理；后续状态见同片复核：

所审 C2 差异内未发现新增硬违规或阻塞性 smell；这不构成最终验收通过。

会话、历史、布局辅助函数留在原所有者内，具有具体职责，未形成假设性的共享框架。缓存格式检查保护浏览器恢复，JSON 合同校验继续调用后端；保存沿原 revision 用例，未迁移 validator、正式调度或存储所有权。六阶段和冻结文件无生产差异。

C2-S1 的实例归属检查（workflow.js:20）、S2 的 kind 检查及元数据剥离（:32、:48–59）符合最小处置原则。重复的异步归属判断分别保护保存事实、当前视图及 JSON 应用，未发现必须抽取的重复逻辑形状。

测试价值：R2 原反例转绿、真实 pointer/wheel 七项、历史步数／字节预算及 quota 输出均支持各自声明范围。现有 Web／架构 pytest 验证传输与所有权，不能替代浏览器状态检查。没有实际延迟或容量测量，不能判性能通过，也无依据要求性能重构。

限制：C2-S1/S2/S3 当前修正仍须 R3 安装包复验；完整两域旅程、自身模板、当前候选 CI 尚未完成。

## Spec

以下为 R3 包复验前的 fresh-context Spec 子审结果，轻量整理；后续状态见同片复核：

未发现新增高置信规格违例；C2 尚不能判定验收完成。

- **Partial／未验**：交付记录 E5 要求“最终独立包、真实两域……迟到回复旅程”。现有 R2 的 `late-save-away.json` 实证 `preserved=false`；当前源码已有会话归属修正，但修后安装包复验尚缺。缓存恢复修正、目标 revision 冲突及缓冲保留也待新包验证。最小处置：最终包重跑这些路径，再完成自身模板和本候选交付门禁；无需扩大实现范围。
- **Scope creep**：未发现。状态仍留在原 `workflow.js`；保存／JSON 应用仍经原 drafts／validator，未新增框架、调度或数据库所有者。手册及架构说明属于本片范围。
- **看似实现但错误**：当前源码未确认新增项。`workflow.js:18–20` 的缓存写入身份检查、`:50–59` 的恢复检查以及 `:218、254` 的已观察目标 revision／save-as 说明与 raw 合同一致。以上是源码判断，不能替代修后实测。

已核现有布局 pointer/wheel 七项 true、历史边界原件；早期 `actualDragMoved=false` 不再作为拖动通过证据。

## 实证问题与同片处置

|编号／级别|具体路径与后果|最小处置及当前状态|
|---|---|---|
|C2-S1／P1|旧 R2 `remember` 未检查项目缓存是否仍由该会话实例拥有。保存 A 回执暂扣 → 载入模板 B 并编辑 → 切项目 → 放行 A → 切回，B 被 A 覆盖；原件 `preserved=false`。|`startSession` 登记当前实例，`remember` 仅为仍拥有该 namespace 的实例落缓存（:18–20、:38）。保存事实仍登记原目标。R3 Ran Playwright code 与 R2 原脚本逐字相同，`preserved=true`；源码／状态及运行证据吻合，本问题关闭。最终 R4 候选仍单独核身份。|
|C2-S2／P2|首轮受审 `restoreSession` 只检查工作单元等外壳，未知 kind 可绕过恢复面板后在角色投影取 `.agents` 时报错。损坏／可重读的角色元数据也不应决定恢复界面。旧包浏览器原件仅证明恢复按钮为 0，不将其描述为捕获了 TypeError。|检查浏览器检查点 kind，丢弃可从 bootstrap 重读的 agents／validation（:32、:48–59、:157）。R3／R4 的 `rawPreserved/cleared/startVisible=true`；本审查独立读磁盘下载，与对应原始 raw 逐字节相等。恢复入口、保留原件和明确清除闭合，本问题关闭。|
|C2-S3／P2|首轮 UI 只显示目标修订数字，未说明改 ID 的新目标语义。A 已载入 r1、已有 B r2，但 B 未载入时，改 ID 为 B 的提交使用 revision 0；仅看 badge 容易把它当作更新 B，实际必然冲突。|保留安全行为：仅信实际载入／本会话保存回执的 revision；未知目标按创建处理，不能追随 dashboard 自动覆盖 B。UI 和 USAGE 已说明改 ID、打开已有草稿及冲突路径。R3 实际未知已有 B 冲突、B 正文／revision 不变、当前 A 正文保留且返回已观察 A 保存为 r2，十项结果全 true；本问题关闭。|
|C2-S4／P2|R3 `keyboard-and-ids` 的 `keyboardSelection/keyboardApplied=false`；精确 `keyboard-focus` 显示 Arrow 改变选择后 activeElement 为 BODY，`selectKeepsFocus=false`。重绘销毁原 select，后续键盘操作脱离可替代图形的表单选择路径。|仅在同步 change handler 完成 `render()` 后聚焦新 `select[name='unit']`（当前 :185–190）。该同步调用链会先替换 DOM，再建立新控件；无异步间隙或新 focus 框架。R4 keyboard-and-ids 与 R3 仅截图输出名不同，五项全 true；原 keyboard-focus 逐字复用，activeElement 为 SELECT/unit、`selectKeepsFocus=true`。本问题关闭。|
|C2-S5／P2|R4 `workflow.js:232–234` 在会话归属检查之前，无条件将 save 回执覆盖到 `app.data.drafts`。持有旧 r1 回执、随后刷新／替换会话并保存或观察 r2，再释放旧回执，会将 dashboard 降为 r1。当前 r2 selector 的闭包仍读同一个 `data.drafts` 可变属性（:144–147），可在标签为 r2 时实际打开 r1；干净的 r2 会话不触发确认，后续下载也可变旧。服务端 r2 没有被旧回执改写。|同控制目录／项目／ID 的保存回执按 revision 单调合并，不改编辑会话 expected revision。R5 与 R4 原脚本逐字相同，`reopenedNewer=true`、重新打开较新正文，服务端仍 r2；本问题关闭。旧 dashboard GET 的反方向另见 S7。|
|C2-S6／P2|R4 `workflow.js:57–59` 只校验 unitBuffers 的值形状，未校验 owning key 属于语义 work_units。含合法值但 key 为缺失 ID 的检查点可正常恢复；pendingText 恒 true，保存／下载／JSON／历史被锁住，任何可选单元的“放弃当前单元文本”都无法删除此孤立原文，也没有原始缓冲恢复入口。|仅在恢复入口检查 buffer key 属于语义单元 ID，矛盾检查点进入已有 raw 下载／明确清除面板。R5 原脚本 `recoveryAvailable/rawPreserved/expectedRecovery=true`；实际下载 6256 字节与注入 raw 全等。合法 owning key 上的未应用改名经 reload 保留、仍未应用且随后可应用，四项 true；本问题关闭。|
|C2-S7／P2|R5 `app.js:49` 在 dashboard GET 完成后无条件安装 `app.data=data`。GET 的 r1 响应暂扣 → 编辑并保存 r2 → 放行 r1，save 不改变 refresh sequence，dashboard 回退；再选择该草稿会无确认载入旧正文，服务端 r2 不变。S5 只保护 save 回执，不保护 GET 回执。|原 refresh 所有者记录 app.data 成功安装时的目录身份；仅同目录／项目按 ID 保留已观察较高 revision，其他 dashboard 字段仍更新，不改编辑 expected revision。原 R5 浏览器红已核；R6 同原脚本逐字复用，`reopenedNewer=true/serverRevision=2/serverNewer=true`，两生产文件与包全等，跨目录重试成功后的隔离探针通过；本问题关闭。|
|C2-S8／P2|R6 refresh 在 bootstrap 切为 B 后仍保留 A 的 app.data；若同名项目的 B dashboard 失败，catch 会渲染 B bootstrap 与 A drafts。选择旧 A 条目会按 B namespace 建会话，保存使用 A 正文／revision 发往 B；若 B revision 相同，原 revision guard 允许覆盖。S7 的 tag 只保护合并，没有隐藏失败停留时的错误组合。|原 refresh 在成功 bootstrap 识别目录／项目改变后、await dashboard 前清空并同步隐藏旧 app.data，走既有 loading/error，保留 A 缓冲。R6 原浏览器旧 A 控件暴露；R7 四脚本逐字相同，旧控件为 0／失败入口出现、重试仅 B／返回 A 恢复原表单与非法 JSON，身份及两 home 真实状态已核；本问题关闭。|

S2 的 Node 探针使用首轮源码，实际结果为 `restoreError=null`、`renderError="Cannot read properties of undefined (reading 'agents')"`，原文仍在模拟 Storage；这是本地状态复现，未当作浏览器或服务器结果。S3 探针实际捕获未载入 B 的 payload `revision=0`，原服务端 `drafts.save` 的 revision 比较负责拒绝覆盖。

## 已核证据及测试价值

原件位于本片本地证据目录 `.ergora/checks/ac5-editor/`；以下均是读取已有脚本／结果／日志，不是本审查重新执行浏览器或 pytest。

|证据|可支持的范围|
|---|---|
|R1 `browser/buffer-regression-original.{json,log}`；同一脚本 SHA256 `48dc036d26dcc7e31c4a5cba5e1bb0829a6e655ff4d4b812c358cf03c464d289`|原包表单、JSON、草稿 ID 保存及下载阻止四项均 false；真实原红。|
|R2 `browser/buffer-regression.{json,log}`|同脚本四项 true；支持所测选择／切页／未应用下载路径。|
|R2 `package-identities.json`／`packaged-tests.log`|记录源／wheel／安装 435 文件、冻结 283 身份及 19 passed / 10.81 秒；没有覆盖 JS 会话竞态。|
|R2 `browser/commands-layout.{js,json,log}`|改名语义／其他 pending 依赖引用、其他缓冲、undo/redo、增删、JSON 命令及保存正文与编辑器一致；首轮拖动 false 明确保留。该脚本自身只比较保存与编辑器，下载正文须另核原文件。|
|R2 `browser/layout-pointer-settled.{js,json,log}`|真实鼠标拖动与 wheel 后，选择／刷新保留位置和视口，语义不变，七项 true；补足此前拖动证据。|
|R2 `browser/history-bounds.{js,json,log}`|55 小命令后 49 次 undo 至第 6 步、49 次 redo、分叉清 redo；526165 字节快照下 6 次 undo 与预算相符；单份超限只留当前，实际 quota 警告。大文本仅测本地编辑，不表示正式编译器接受此输入。|
|R2 `browser/late-save-away.{js,json,log}`|S1 原包反例；脚本 SHA256 `97c2e2c9d407e1d52f9372962ca701f69e854c6e1b24fba81d2f4935b219f45d`。|
|R2 `browser/corrupt-kind-active.json`|未知 kind 缓存下恢复按钮 0；未捕获 pageerror，严格保留这一范围。|

本审查另对实际源码做只读 Node 状态探针，未修改源码或证据：

- 当前源码验证 `redundantMetadataRemoved=true`、`staleRememberKeepsReplacement=true`、`corruptKindRecovery=true`。后者保留完整 raw；前者确认 bootstrap 可重读元数据不再重复持久化。
- 历史算法探针在 80 次提交后保留 50 个快照；撤销后分叉丢弃 redo；800000 字符合成输入保留 5 份、4000822 字节；单份超限仍保留当前输入。只证明本地命令算法，没有跨 DOM、编译器或安装包验收。

新函数均为原所有者内部的会话／缓存／命令／布局算法，实际调用集中在 workflow.js，由原 app.js 通过既有 interface 消费；这不是跨文件复用的证据，也不需要制造第二调用者。明确待办保持在 C3/C5/C6，不用 C2 增加正式执行图、事务、调度或存储。无新增永久 pytest／CI 模板断言，现有 HTTP 门禁测试仍有价值；浏览器脚本检验的是用户可见合同，保留旧包红与修后绿比镜像状态实现的测试更有解释力。

性能方面，输入事件会序列化本地缓冲，选择／语义命令会由原 render 生命周期重绘图；没有新增框架或调度层。当前没有最终包的延迟、帧率或 50／200／500 图规模测量，本审查不据此判容量／性能通过，也不凭静态成本要求性能重构。历史字节预算是文本快照预算，当前输入超限例外已明示；不能表述为整个浏览器内存上限。

## 待终结项

1. 固定父 03f1f58 的本次 25 文件普通提交／推送及实际 Git 对象核验。
2. 该新候选自己的必要 CI 终态与明确 HTTPS 远端完整 SHA；不沿用前片结果。未完成前保持 E5 精确交付待验。

两轴汇总：完整 25 文件 Standards／Spec 本地通过，新增硬违规 0、阻塞性 smell 0、开放 finding 0；精确交付保持待验。

## R3 核心及 S4 同片复核

本审查独立读取 R3 wheel、非 editable 安装和 record，435 文件逐一相同；相对当前源码只有 workflow.js 焦点修正，283 冻结文件逐一与 61ccc2c archive 及 manifest 相同。`packaged-tests-corrected.log` 为 22 passed / 17.29 秒；首次不存在测试路径、no-isolation 构建缺 setuptools 的失败仍属于原 harness／环境记录，不算产品回归成功或依赖变更。

已读 R3 原始脚本、JSON 和对应关键日志：E1 四项 true、commands-layout 十二个布尔项 true、conflict-and-invalid 十项 true、layout-pointer-settled 七项 true、late-save-away 原脚本 `preserved=true`。原脚本 SHA256 仍为 `97c2e2c9d407e1d52f9372962ca701f69e854c6e1b24fba81d2f4935b219f45d`，本审查将 R3 日志中的 Ran Playwright code 与原脚本完整比对相等。

治理保存与编辑正文一致，训练切项目返回保留选择；`trainingFiles=0` 来自默认可访问查询忽略 closed details，不据此判断文件缺失。补充 training-download 显示 11 个 details、展开后有可见下载按钮并取得实际正文。后续已独立读取四份 R3 磁盘原件：大型开发／治理 JSON 与保存正文语义全等，raw-buffer 4594 字节与原始 raw 逐字节相等，训练文件 824 字节与原正文逐字节相等。其 SHA256 分别为 `656a58b429a32b8e4f72db659aa7480ea8c77a6e8d6a70aeef5b8824968714aa`、`78d9abcaeac1f7695de0868648c8e9f445715fed93a663f7b610f765d0a262ed`、`922b822f2d4320fd48a8bc355f0e55ebb244464b6e02d08416dca8114e0999de`、`0283134a50fcb79ce0909c6db7ec2973543af3207fc7b71e840095a317829cb7`。

USAGE 新增编辑、未应用原文、撤销／重做、布局、save-as／已观察 revision、冲突、quota／损坏恢复和训练范围说明，与当前实现一致；架构补充保持原 workflow 所有者和原 validator／调度／存储所有权。S4 源码仅重建控件后恢复局部焦点，未发现需要扩大接口或引入通用焦点管理的理由。R3 键盘两项 false 与 BODY 焦点原红完整保留，修后 R4 另核如下。

## R4 最终包核心复核

R4 wheel 实际 SHA256 为上述 `fb0568b8…`；本审查逐文件比较当前源、wheel、非 editable 安装和 record，全 435 文件相同；受审 workflow.js 为 `07a97567…`。冻结 283 文件与已核 R3／61ccc2c 基线相同。实际服务身份记录指向该非 editable 入口及同 wheel；回归原件为 **22 passed / 17.85 秒**。

已独立核 `r4/browser/batch-main.json` 和 `batch-races.json` 共 12 项：每项 script／result／log 的 SHA256 与磁盘原件相等，日志的 Ran Playwright code 与所指脚本逐字相同，所有明确列出的布尔检查 true。E1、S1 及 keyboard-focus 使用原脚本；keyboard-and-ids 只调整截图文件名。历史另核为 49 次 undo／49 次 redo、526132 字节快照下 6 次 undo、分叉丢弃 redo、单份超限只留当前及真实 quota 警告。

R4 `keyboardSelection/keyboardApplied/keyboardUndo=true`，Arrow 后 activeElement 是 SELECT/unit；390px 的 document 宽度同为 390，无页面横向溢出。本审查查看了窄屏截图，操作控件及文字投影可读；图可保留平移后的视口，表单仍可选择全部单元。没有以静态截图替代键盘实测。

四份 R4 下载也已独立比对：大型开发和治理 JSON 分别与保存正文语义相同，raw-buffer／训练文件分别与对应 raw／content 逐字节相等。上述文件位于本片 `output/playwright/ac5-c2-*-r4.*`，未把缓存原文复制到公开报告。

同端口 home 切换／恢复、服务生命周期和真实自身模板仍在独立后续核验范围；当前记录不表示 E5 或精确提交／推送门禁已经完成。

## 真实自身首审与 S5／S6 独立判断

实际首审 run `14c126922e8745f28ef92cc1429a99bf` 的元数据为 Codex／gpt-6.1-sol/high、**264.407 秒、status=succeeded、decision=request-changes**。固定附件 185096 字节、13 个源码／配置／测试来源；受审 workflow.js 仍为 R4 的 `07a97567…`。本审查已读 `.ergora/checks/ac5-editor/self-review-r1/review.md`、原运行 JSON／日志和实际 MCP 原回执，并独立核字节交付如下。成功运行不表示建议 approve，也不表示 E5 完成。

没有按模型 verdict 直接接受 finding。本审查重新沿 app.refresh 的 data 替换、draft selector 的闭包读取、save 回执合并、checkpoint 恢复及各放弃按钮调用链检查，并用原 R4 安装正文执行只读 Node 状态探针：

- S5：r2 视图已建立后释放旧 r1 回执，实际 `displayedOption="shared · r2"`、`dashboardAfterOldReceipt=1`、`reopenedRevision=1`、`reopenedGoal="old-A"`、`confirmations=0`。这确认了 UI 快照回退；探针用内存 HTTP adapter，没有冒充服务端状态或浏览器运行。
- S6：合法单元 `one`、孤立 buffer key `missing-unit` 时，实际 `restoreError=null`、`saveDisabled=true`、`jsonApplyDisabled=true`、`recoveryDownloadAvailable=false`；调用当前单元放弃后 `pendingAfterDiscard=true`，原文仍在 Storage。检查点不一致应由原恢复入口处理，而非由第二份任务 validator 处理。

两组原 R4 浏览器证据现已独立读取：`r4/audit-browser/late-save-revision.{js,json,log}` 取得 `labelBefore="my-task · r2"`、旧正文、`reopenedNewer=false`，同时 `serverRevision=2/serverNewer=true`；`orphan-buffer.{js,json,log}` 取得无恢复入口／全部可选单元放弃后仍锁住。后者 `rawPreserved=false`，不能声称该错误路径逐字保留了原检查点；脚本另保存了注入的原 raw 作为证据。服务身份仍绑定原 R4 wheel `fb0568b8…`。

因此首审当时将两项作为 P2 开放。原 R4 十二脚本只能证明原先覆盖的旅程，对这两个新增触发条件没有回归保护；不撤销 S1–S4 的已证实处置，也不扩大到 C3 或 C6。后续 R5 同片关闭证据见下。

首审的私有首轮审计假定所有分页均 UTF-8，失败原件已保留；实际协议在切断 UTF-8 字符时可以返回 base64，不能把审计假定失败当作生产协议错误。本审查重新从 actual run 的 `stdout.txt` 逐页解码，并对固定 scope／附件字节和摘要核验：9 个成功候选页、其中 48000 offset 的 base64 页重复一次、72000 offset 另一 base64 页，共 3 份 base64 回执；去重后 185096 字节连续完整，`next_offset=null`，四份祖先指令／Skill 都完整匹配，读取失败 0。原结构化结果 SHA256 及 review.md 正文也匹配。结论仅为 **byte delivery，plaintext_only=false**；不据此宣称模型对 base64 页完成了全文语义阅读。

修后候选本就需要再次真实审查；可在本片私有 candidate evidence Skill 要求 base64 页按相同 offset 减小 max_bytes 重读到 UTF-8，再继续 next_offset，并由独立审计核完整连续明文。此补证不要求 C2 扩改生产 task_mcp 协议，也不扩大工具权限。

## R5 同片复核与 S5／S6 关闭

本审查独立核 R5 wheel 为 `2dd4478f…`，源／wheel／非 editable 安装及 wheel、安装两份 RECORD 的 435 文件逐一全等；相对 R4 产品只改 workflow.js。manifest 中 283 冻结文件逐一与 61ccc2c archive 及 manifest 摘要相同，manifest 本身也不变。已读原回归日志为 **22 passed / 11.68 秒**。

R5 `late-save-revision.js` 与 `orphan-buffer.js` 分别和 R4 原脚本逐字相同，SHA256 为 `2f86eb7d18cdf548061b79591aca04bdd2e6386021c99c5e13c5cf8a2d9b9c3e`、`53bd478ce896028fb40a10ee16981999e6e78cb409bd41a60e28888077d22471`；三个脚本（含 recovery-and-rename）的日志 Ran Playwright code、结果 JSON 与所指原件均全等。S5 重新打开较新正文且服务端仍 r2；S6 提供恢复入口、保留原 raw。实际下载与两个结果中注入 raw 的 6256 字节全等，SHA256 `3d025d8ef9133b4e119e45b87600ffcacfcfb3c133e9690e0b025a564f8bd26d`。明确清除后，合法 owning key 上 pending rename 经 reload 保留、未自动应用、随后应用成功，四项 true；源码只检查 key 归属，未错误限制未应用的 `unit_id` 值。S5／S6 关闭。

已核 R5 batch-main／batch-races 共十二脚本：每项 script／result／log 摘要相等，完整 Ran Playwright code 与脚本逐字相等，51 个明确命名检查全 true。历史为 49 undo／49 redo、526132 字节快照下 6 undo、分叉清 redo、单份超限只留当前及 quota 警告。四份实际下载分别和保存正文语义相等（开发／治理 JSON）、与 raw／content 字节相等（损坏缓冲／训练文件）。不能由此扩大正式编译范围、性能或 C6 容量结论。

R5 namespace-prime／alternate／restored 三脚本的完整日志及结果也相等：同 URL／端口／wheel，另目录只改变原 argv 中 home 参数，三个进程身份不同；恢复进程的 argv 与原进程逐项全等。B 起始空白并建立独立非法表单／JSON／ID 缓冲；恢复 A 后原三份未应用文本均恢复。原、替换两个进程的停止原件均记录 port_closed；drafts before／after 的磁盘字节全等，SHA256 `85ed3ef4d022af40b2a183bdf6c852d4dbc65f77b04ffb291a682fbcc61996b2`。这不预先证明最终 owned 服务已全部清理。

presentation 日志／脚本／结果匹配，语义输入未变，390px viewport 与 document 宽均为 390；R5 keyboard 检查也保持通过。首次未切入 workflow 页等 harness 失败继续保留，不算产品红或成功旅程。

## 第二轮中断记录与 S7 独立判断

第二轮实际模型 run `c504c48db20e495e8f7acbb25442df65` 已写原协议 result，decision=request-changes，SHA256 `456c721daa641013e33ef8b6acc170a7cf775b16a0d3997455962d72252ceab1`。本审查只读 SQLite 原 registry，status 仍为 **running**；外层中断与协议结果并存，不能称 succeeded，也未修改账本。本审查重新解析 actual stdout 的原 MCP 回执：10 页 UTF-8，offset 为 0、22000 至 198000，连续 211082 字节且 next_offset=null，base64／读取失败均 0；candidate 与固定 scope／附件／actual input asset 字节全等，SHA256 `604e8b27debc60934ec61d00432efb16efde126ba40bc84cfb8659c952c3ba77`。四份祖先指令／Skill 也与固定 scope 和 actual asset 完整匹配，实际 prompt 与准备件及原摘要一致。此为完整连续明文交付证据，不等于外层成功或推理质量证明。

本审查重新读取 app.refresh／workflow 草稿选择调用链，并对实际 R5 安装 app.js 的 refresh 函数作只读内存 HTTP 探针：保存后已观察 r2，释放旧 GET 后 dashboard／render 回到 r1，选择条目正文为 old-r1。原 R5 实际浏览器 `late-dashboard.{js,json,log}` 的完整脚本与 Ran code、JSON 全等，脚本 SHA256 `310337351446318ce41898c0d59713e731af1c5f0b1fcac216731b57b9c02e8a`；结果 `newRevision=2/reopenedNewer=false/serverRevision=2/serverNewer=true`。因此独立接受 S7／P2，非仅转述模型意见。

当前 `app.js` 最小修正将 app.data 的目录身份保存在原 refresh 所有者局部，仅随成功安装数据更新；同目录／项目按 ID 保留较高 revision，不改 state.js、editor revisions、validator 或存储。此目录身份不能直接由当前 bootstrap 推断：换 home 时 bootstrap 成功而 dashboard 失败，旧 app.data 可能仍在。对实际修后 refresh 函数的只读探针已核同目录保留 r2／新 ID、其他 dashboard 字段更新，以及 A 数据 → B bootstrap 成功／GET 失败 → B 再次成功不混 A、切项目隔离，均 true。另查 app.data 的非空安装只有此 refresh 所有者；workflow 只合并同目标保存事实，局部 tag 无需变成共享状态。R6 包及原反例复验已完成如下。

## R6 包与 S7 关闭

本审查独立核 wheel SHA256 为 `fa7a42a7…`：源／wheel／非 editable 安装及两份 RECORD 的 435 文件逐一全等，283 冻结与 61ccc2c archive／manifest 相同，manifest 本身不变。相对 R5 只有 app.js，整个 C2 相对产品基线只有 app.js／workflow.js 两生产文件。原回归日志为 **22 passed / 13.28 秒**；现有 Web／架构／C1 HTTP 范围不变。

R6 `late-dashboard.js` 与原 R5 脚本逐字相同，SHA256 仍为 `31033735…`，日志 Ran code、结果 JSON 与脚本／原件全等。实际取得 `newRevision=2/reopenedNewer=true/serverRevision=2/serverNewer=true`，重新打开较新正文；结合源码、owner 归属和跨目录失败链探针，S7 关闭。R6 的 S5／S6 两个原 R4 脚本也逐字复用并转绿；recovery-and-rename 相对 R5 仅改下载输出名，四项保持 true。实际恢复下载的 6256 字节与两份注入 raw 全等，SHA256 `6e3756e1e23b7c188b5fd01d89fa0ae625d838e76455a0821935e5c16283553f`。

R6 batch-main／batch-races 十二脚本的摘要、完整 Ran code 和原结果逐一相等，51 个命名检查全 true。历史边界、真实 pointer／wheel、键盘焦点、save-as／冲突、非法 JSON／迟到应用、两域保存及训练模板范围均保持所测结果；四下载另与保存正文语义或 raw／content 字节全等。keyboard 的 390px document 与 viewport 均为 390。未把 R5 的 namespace 旅程、旧模型结论或 CI 自动算作 R6 最终交付通过。

## 第三轮真实审查与 S8 独立判断

实际 R3 run `58be8da38be344efb73690f511b65239` 为 Codex／gpt-6.1-sol/high、外层实测 **253.6066 秒**、succeeded／returncode 0，decision=request-changes。本审查逐项核 SQLite registry 与 native run document 全等，原 result SHA256 `aeff24dcffa8278d8bcc40cfe37866954df88f0a492ddabec3652f399e95aa19` 与 review.md 正文匹配，不将运行成功混同 approve。

重新解析 actual stdout 的 MCP 原回执：候选共 14 份成功回执，10 份 UTF-8 连续交付 **217942 字节**，最后 next_offset=null；四份 base64 原件保留，offset 24000／47998 分别按 max_bytes 24000 → 23999 → 23998 在同 offset 重读，直到 UTF-8 成功才前进。所有回执字节与固定候选对应范围相同；连续明文和五份固定 scope 文件、四份祖先 actual instruction／Skill、actual candidate asset 及 prompt 均匹配，读取失败 0。候选 SHA256 `1634b7aa68c0523374e4a2f779d2aa539aaa5e3f4009de92306316209f8e3a1d`；原 stdout SHA256 `52026a065b16fa62566faa9f228347e80ad9d68d154f6cff2188e4284bae5a65`。完整明文交付不证明推理质量或正式授权。

独立沿 app.refresh → render → workflowView 草稿选择 → startSession → validate payload → 原 drafts.save 检查。对实际 R6 安装 refresh 与 startSession 的只读内存 HTTP 探针取得：B dashboard 失败后 `rendered.home=B/dataGoal="body belonging to A"/dataExists=true`；打开旧条目后 `sessionHome=B/savePayloadRevision=1/savePayloadGoal=A`。若 B 同 ID 现存 revision 也是 1，原 drafts.save 的比较会匹配；此探针未当作实际服务器写入证据。因此独立接受 S8／P2；原红和 R7 关闭证据见下。

此前 S7 探针验证了 A 数据 → B bootstrap 成功／GET 失败 → B **再次成功后**不混入 A；它没有验证失败停留时是否仍可操作旧 dashboard。其结果保持原范围，不能用于关闭 S8。最小处置留在 refresh 所有者，在新目录 bootstrap 成功后立即清空并同步隐藏旧 app.data，再等待 dashboard；既有 loading/error 视图可处理失败。此过程不清 A 的 sessions 或 Storage，disposeGraph 使用 graphSession 自身目录保存布局；修后仍需证明 A 未应用原文可恢复。

当前最小源码仅在 bootstrap 已确定最终项目后、dashboard await 前增加旧 data 隐藏 guard，同时检查目录和项目归属。对实际修后 refresh 函数的只读内存探针已核 `hiddenBeforeDashboardReturns/hiddenAfterDashboardFailure/aReturnsToAData/sameHomeKeepsNewer/fallbackProjectHidden` 五项 true。它证明新的数据安装边界和原 S7 逻辑保持，未替代浏览器原件；后续包及缓冲恢复已核如下。

## R7 包与 S8 关闭

本审查独立核 R7 wheel SHA256 为 `722ece41…`：source／wheel／非 editable 安装及两份 RECORD 的 435 文件全等，283 冻结逐一与 61ccc2c archive／manifest 相同，manifest 本身不变。相对 R6 只有 app.js 的目录／项目隐藏 guard，C2 生产仍只有 app.js／workflow.js。原回归日志为 **22 passed / 12.85 秒**。

R6、R7 `failure-browser` 的 prime／failed-refresh／retry／restored 四脚本逐字相同；每份日志完整 Ran code 与脚本逐字相同，结果与 JSON 全等。failed-refresh SHA256 `f4c87e3f9a6382779e8832b1eaa5bb8c128420dc496061c5e3d391aa04d99059`：R6 原红为 retainedDraftControls=1、显示 only-a／shared、failureView=false；R7 为 controls=0、无旧选项、hiddenForeignDrafts=true、failureView=true。重试后 onlyB=true，返回原 A 目录后原表单及非法 JSON 均恢复。浏览器原红证明旧草稿控件暴露；没有实际尝试覆盖 B，待发请求及 revision 后果由源码／只读状态探针确认，未冒充浏览器服务器写入。

各 revision 的三个进程同 URL／端口／wheel，替换时只改变 argv 的 home，恢复 argv 与原进程逐项相同，三组 PID／starttime 不同；前两个进程停止原件 port_closed=true。只读两 home SQLite 确认 shared 均为 revision 1 且正文分别为 A／B，B 正文仍属于 B。结合提前隐藏源码、失败停留原红转绿及 A 原文恢复，S8 关闭；最终恢复进程仍另待 owned 清理核验。

R7 十二核心脚本的 script／result／log 摘要、完整 Ran code 和结果逐一相等，51 个命名检查全 true；四下载另与保存正文语义或 raw／content 字节全等。S5／S6／S7 原脚本逐字复用并保持绿；合法未应用改名恢复脚本只改下载输出名，四项 true。实际恢复下载 6256 字节与注入 raw 全等，SHA256 `7fe142ed29a59a814668e9c204bd0c424e64a42bd3a7ad7d722dea7f5ac1f98f`。历史、quota、键盘和布局仍只支持既述范围；最终模型／公开证据／精确 CI 与 HTTPS 仍待验。

## 最终本地终结

固定父 `03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`，实际范围恰为 **25 文件：2 生产、8 Markdown、13 公开 JSON、2 PNG**。两份 precision 文档仅补前片交付状态，不作为 C2 行为证据。已核最新 PLAN／AC5／交付状态、手册及架构；生产与 R7 的 435 文件身份保持，283 冻结不变。Spec／Standards 本地通过，S1–S8 关闭，无新增硬违规、阻塞性 smell 或开放 finding，**同意普通提交这 25 文件**。

第四轮实际 run `af764f526e3e4cc6a9fb9bec850ff966` 为 **214.2232 秒、succeeded、approve**。独立核原模板证据修订、manifest／input／准入／实际 prompt、13 份完整源、10 页连续 **224857 字节 UTF-8**、四祖先资源及固定 scope 全等，base64／读取失败均 0；registry／native／review 与原结果 SHA256 `4ba458a46ba97f7cc01d741a636f3189a4a2ef4c5f599c3c0e1db7743f9e081c` 匹配。13 公开 JSON 已逐项核对原件清理投影，保留原摘要与投影摘要的区别、R2 running 及 R3 request-changes；两张截图与原图字节相同且已目视核查。

R7 成功 namespace 三脚本／日志／结果、三进程身份及 drafts before／after 字节相同已核。最终 25 HTTP 原身份与 `cleanup-http-final-r7.log` 一致，旧 15 份记录保留，当前原进程身份均消失或 zombie、所列端口无监听；原 8 加最终 15 个已知浏览器会话均有关闭／已不存在的成功回执。静态文档原检查为 8 文档／138 链接／94 parser，通过结论仅属本地出口。后续继续核实际提交／推送对象、该候选自己的必要 CI 与明确 HTTPS 完整 SHA；未提前标记精确交付或完整 E5 通过。
