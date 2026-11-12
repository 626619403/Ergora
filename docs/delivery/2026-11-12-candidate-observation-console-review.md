# F7d-D3a 独立审查记录

**最终本地判词：完整20文件候选的 Standards／Spec 均通过，开放 finding 0／0；ST1、SP1及末次状态记账SP2三个P3均已关闭。** r2包、原安装／页面分段、最终视口、125份HTTP、模型八附件全文读取、公开投影及拥有资源清理已独立核对。O4普通提交／推送、精确Git／Ref和本提交自己的双OS必要CI尚未交付；D2的证据不转授D3a。

本报告保留O1初审和后续同片复核的原范围及当时状态，最终结论见末节。评审协调者为新 fresh-context `f7d_candidate_console_review`；两个互不继承实现会话的 fresh-context 子审查者分别为 `spec_axis` 和 `standards_axis`。按 AI Hero code-review 两轴、maintainable-project-delivery／independent-review 和 codebase-design 检查；[原规格](../plans/2026-11-12-candidate-observation-console.md)、[交付记录](2026-11-12-candidate-observation-console.md)及仓库 AGENTS／PLAN 适用。

## 初审范围与身份

固定基线与当前 HEAD 均为 **`c69dedf82512ce87d6a72a249626c26dadca4c3c`**，分支为 `refactor/architecture-foundations`。基线之后提交列表为空，本轮审查实际未提交工作树，不能仅用空的三点 HEAD diff 代表候选。

完整 tracked 差异使用 `git diff c69dedf82512ce87d6a72a249626c26dadca4c3c -- README.md docs/PLAN.md docs/USAGE.md docs/architecture/current.md docs/delivery/2026-11-12-source-task-console-review.md src/ergora/data/console/tasks.js`；另全文读取三个 untracked 文件：本片 plan、delivery 和 `src/ergora/data/console/candidate-observation.js`。D2 review 的后补精确交付审计属于前片记账；知晓其范围，不将 D2 的 Git／Ref／CI 证据借给 D3a。

初审读取时的九件候选身份如下。后续状态追加和最终候选须单独核验，不能继承这份快照的范围。

|文件|SHA256|
|---|---|
|`src/ergora/data/console/tasks.js`|`51f413dad6c7df6f45ef5eb861feffc69bdb76d1ff21469ced5f061fdc2a09e9`|
|`src/ergora/data/console/candidate-observation.js`|`00804c34dad426c1eaa0a219ff20fe1ba711357471d461a28503ef28d4dfee4c`|
|`README.md`|`821daa4800a5c86f64990bc3555eb856b6b1eefa3c59616fad70e313ef3f8f03`|
|`docs/USAGE.md`|`91ba67325de1918a6c09231c4498c12cb2392b3c7cc6aa56a7e75c4318e39fe5`|
|`docs/architecture/current.md`|`d782bc4e3491dbb283ff96ba2415793c605db4dffa3199ef57d1db6c6e2e112f`|
|`docs/PLAN.md`|`39a48dbd0edb4ab015f90e434a5cc43f10889de29b04cad272dbf8094c4aa55e`|
|`docs/plans/2026-11-12-candidate-observation-console.md`|`c0fa6122a23c88f696768ee9f9ef74487b2a15b5bd18fe0f07f5f1454ea99dd0`|
|`docs/delivery/2026-11-12-candidate-observation-console.md`|`9ecac3573936d66e9638a494b8e3918502d4ef776182d2a0c29ccbb4a7ba2e03`|
|`docs/delivery/2026-11-12-source-task-console-review.md`|`3d6fe74127e1d0df0465abcaefc5f16047bd45d502ee096e68096c699878a0da`|

必要邻接实现包括 `issues.remote_candidate`、`tasks.exported_source_candidate / inspect_export / export_status`、Web `candidate-observations`、console `api.js / ui.js`、任务详情及 run／导出生命周期、`tests/test_candidate_observations.py`。没有扩展审查为整个仓库。

## Standards

独立 Standards 结论：**ST1／P3 一项文档准确性问题开放；未发现其他实证 Standards finding。**

**ST1／P3：当前模块库存未同步。** `docs/architecture/current.md:180` 仍称“19个第一方原生ES module”。基线确为19；新增 `candidate-observation.js` 后实际为20，vendor另算。新增模块时未同步当前架构盘点，违背项目记录应反映实际实现的要求，会使恢复者取得错误库存。最小修正为更新20或删除易漂移硬计数；这是文档问题，不是代码结构硬违规。

`candidate-observation.js:7` 唯一真实生产调用者为 `tasks.js:1148`；拆分以连续观察交互的内聚职责成立，小 Interface 隐藏表单、异步代际及安全展示，没有虚构复用或扩展点。`tasks.js:1118` 保留任务／run 存活约束，新模块另管自身 modal 和请求代际，职责清楚。

新增 guard 分别对应可到达的未导出／非v7入口、任务或run替换、窗口关闭重开、输入修改及迟到成功／失败；三态显示保留 unknown。未发现指定 smell baseline 的实证问题。未新增测试、CI、依赖或后端分派；明确提交复用原观察 owner，没有额外轮询或重试成本。

## Spec

独立 Spec 结论：**SP1／P3 一项状态记账问题开放；产品行为未发现有实证支持的缺失、越界或错误。**

**SP1／P3：PLAN 未同步 O1。** 原规格第29行要求“每完成节点同步 PLAN 与交付记录”。本片交付记录第3行已写 O0／O1 实现，入口见 `tasks.js:1145`，查询实现见 `candidate-observation.js:23`，但恢复入口 `docs/PLAN.md:29` 仍仅记“当前O0完成”。新会话按 AGENTS 首读 PLAN 时无法准确取得当前实现节点。最小修正为补记 O1 已实现，O2 实际验收、O3 审查及 O4 交付待完成，保留实际验证边界。

其余核对：原 v7／exported 入口限制、固定原候选、显式 base 查询、编辑失效与迟到隔离、安全全文、404 unknown、新失败清除旧成功均与规格相符；未新增后端、持久化、provider 分派、测试或 CI。

## 检查、限制与下一步

协调者实际运行两份 JS 的 `node --input-type=module --check` 及 `git diff --check c69dedf82512ce87d6a72a249626c26dadca4c3c`，均 exit0。完整 tracked 差异中 `.github`、`pyproject.toml`、`tests` 及冻结 reference 树没有变化；这只证明本片没有这些 tracked 变更，不等于已验证新 wheel／RECORD／全部283件安装身份。

本轮未重新安装、运行原 suite、浏览器或 Agent／模型，没有新的完整六阶段、真实 SaaS、原生 Windows 工作区、OS 隔离或外部写入证据。新模块67行／3811B，原 tasks.js 为1378行／78532B；只读静态核对确认无自动查询、轮询、重试或新增后端流程，尚不能给出页面／HTTP实际耗时。

本轮仅允许写本报告，没有改产品或运行昂贵检查。两项 P3 反馈实现者后，须核实际修正；再等待最终完整候选清单、新包／安装原 suite、两provider实际浏览器旅程、原对象保持、模型完整读取、清理与性能证据后同片终核。O2／O3／O4 均不因此报告提前通过，最终独立本地出口仍待完成。

**初审汇总：Standards 1项、最重ST1／P3、开放1；Spec 1项、最重SP1／P3、开放1。**

## 同片复核：两项记录修正与 r1 实际证据

**ST1／P3 已关闭。** 原 Standards 审查者核到当前架构删除易漂移的“19个”硬计数，保留第一方原生 ES modules 的准确表述，未引入新问题。该次 `current.md` SHA256 为 `2cbea223d16958980a06f0132e1f2a87cdbea44407591da70fc9cceb600f2576`。

**SP1／P3 已关闭。** 原 Spec 审查者核到 PLAN 已同步 O0／O1 已实现，明确 O2 实际页面、O3 自身／独立终核和 O4 交付继续；该次 PLAN SHA256 为 `c24ab4dbb383f627f638381ba89c0d7000c4fc9b6ca83501937b6021719a25dc`。随后交付记录把“尚未安装”明确限定为 O1 初始检查点，并分别记录后续安装、夹具失败和模型结果，暂时的记录滞后也已消除。两轴均未新增 finding。

协调者独立读取 r1 wheel／安装字节、原 RECORD、manifest 和验证原件，核得：

- r1 wheel SHA256 `876231da8e0aa9aef124ac19fa40818f9bc7413cf3439e3b643c9ee899234e8b`；当时449件源码、wheel、非editable安装内容全字节一致，wheel RECORD454行／installed RECORD459行的全部带摘要项及大小匹配，283件冻结参考文件均符合原 manifest。
- 三个既有安装 suite 的原 stdout 为 **40 passed／29.82秒**，命令回执 exit0／31.86秒；stdout SHA256 `a75635edc798f9cb806751b4d4fd3ebe9d0d6372ac733cb28de7d31d4812ebfa` 与回执一致。reference verify 的原 stdout 摘要也一致，结果 PASS／283／runtime_started false。
- 两provider种子的原 stdout 为 **2 passed／22.18秒**，命令回执 exit0／22.90秒，摘要 `a9bf55a60b49f0f1382891d0834096baa15663977b9025422074b4008979e9eb` 一致。只读核种子脚本及原 SDK 夹具：原 v7 合同、原发布／提交／导出 owner 与 Git 真实运行；Temporal SDK 受控，REVIEW_READY 合成，没有新的完整六阶段或模型执行。

首浏览器原结果 `passed:false`、3项后在精确 ref 查询中止；原HTTP为400，错误为“Tracker returned an unsupported or different exact branch ref”。私有 provider 夹具缺少原协议要求的精确 ref URL，原 owner 正常拒绝。首服务12件HTTP／2次provider GET和清理原件保留，未写成产品通过。后续仅补夹具 URL，并复用种子冻结的 loopback API 来源，没有改旧来源树。

补段主页面 **40项／34.81秒** 与生命周期 **23项／39.70秒** 的原 driver／结果已核，分别有10／4份查询样本、页面错误0。驱动真实安装页面及原HTTP owner，覆盖两provider精确匹配、远端／本地漂移与404、错误替换旧成功、显式重试、安全全文、输入修改、关闭重开、换项目／视图、修订和来源改绑。四次回复由实际后端处理完成后再 hold／release；不是浏览器伪造返回值。

已从补段101件HTTP的原 request／response逐件复算长度和 SHA256，全部与 trace 匹配；provider为44次GET。两provider合计88件 runtime文件、完整原来源及manifest保持；GitLab逻辑DB与repo保持。GitHub逻辑DB、候选reflog及导出投影的 project_revision 按显式 fixture ref／bump／rebind 控制发生变化，不称整个DB或repo逐字未变。两段服务均有 threads_stopped 清理回执，按原 pid／starttime 已无同一存活进程；浏览器命名 session 的 close 回执 exit0。

18次显式 candidate POST 包括14次200和4次400，原 ASGI owner 处理时间最小0.00979秒／中位2.40117秒／最大2.52787秒；四次故意 hold 的回复等待不计入该处理时间。这是本地两provider夹具及原Git owner的实际成本，不称真实SaaS延迟或整段浏览器耗时。

内置自身审查原 run `384432194d75441b98c108a18be06b95` 为 Codex／gpt-6.1-sol／high，**approve／124.17秒**。协调者重新核原八件冻结附件的完整字节／索引、prepared与actual输入、manifest资产、prompt与stdin、admission与权限上限、scope、native工具响应和原result；150,396B附件摘要为 `a52e29748641bdbf3f6fed781a9a4b759b1b560d497742d7bb58d13e5314d49e`。原 native 流中五scope均连续UTF8读取到null，其中候选全文7页，无失败调用；原result SHA256 `09ef55fc2b35b06c8a147e79311ab360e9b94a24459cc30e7d7e0efffc125e81`，其判词明确只覆盖八附件。四个采样所属进程无存活的原回执范围保留，不扩称所有短命进程或OS隔离；自报用量不推费用或双后端独立性。

## 同片视觉补丁复核与剩余出口

实际截图发现长SHA挤压比较列后，仅给 `candidate-observation.js:15` 的容器增加 class，并在 `style.css:619` 添加两条局部单元格／表头换行规则。该次候选JS SHA256 为 `0f8eb175c51030c2d60d1d493df6febbd19836cc3ded5b16d14fde49d41f76c1`，style SHA256 为 `be7206668ae25f99bde9e52775b0989f34620e5b7fd886d46ec1965b60685e71`；tasks.js仍为初审身份。移除新增 class 后，候选JS精确恢复初审摘要。

原两轴均全文复核后补JS及CSS和邻接任务owner：规则只作用于观察容器，不截断内容，不改变查询、生命周期、安全展示或其他页面；未新增函数、guard、依赖、测试或CI，新增 finding0。最终审查范围新增 style.css。r1包／40项／23项及模型八附件保持原字节范围，不将原模型approve转授后补class／CSS。新 r2 非editable包、最终两视口、完整公开候选和清理证据仍待同片终核，本报告此时不宣称O2／O3或本地出口完成。

**当前汇总：Standards 原ST1／P3已关闭、开放0；Spec 原SP1／P3已关闭、开放0；最终本地验收与精确交付待核。**

## 完整最终20文件本地终核

基线与HEAD仍为 `c69dedf82512ce87d6a72a249626c26dadca4c3c`。逐件核对完整候选清单与 `git status --porcelain=v1 -uall`，恰为 **12件tracked差异＋8件untracked，共20件**，没有遗漏新增正文或PNG。范围为：

- 三件产品文件：`src/ergora/data/console/tasks.js`、`candidate-observation.js`、`style.css`。
- 六件本片入口／状态文档：`README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`、本片plan与delivery。
- 本审查报告及四件本片公开证据：`2026-11-12-candidate-observation-console-acceptance.json`、`-self-review.json`、`-desktop.png`、`-mobile.png`。
- 四件D2后补状态：`docs/delivery/2026-11-12-source-task-console-review.md`、对应delivery、对应acceptance.json、`docs/plans/2026-11-12-source-task-console.md`。
- 两件上层计划：`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-11-project-trackers.md`。

各tracked文件的全部变更、新文件全文和公开PNG均已核对；本报告仅作本片审查与状态追加，不递归审查自己的生成。四件D2修改只记其精确交付，D2自己的CI原件由其原评审处理，本次不处理或借给D3a。后续D2 CI终态追加仍属于原片状态更新。

末次 **SP2／P3** 为本片delivery第3行总述仍写“O0／O1已实现；O2–O4待验收”，而同页后文和PLAN已记录O2完成。已最小改为“O0–O2完成；O3最终独立终核继续，O4待交付”；原Spec审查者和协调者实际复核一致，SP2关闭，没有产品修改或重复运行。

### Standards 终核

原 Standards 审查者对完整20文件的结论为：**开放finding0；ST1／P3保持关闭，无新增实证问题。**

唯一真实生产调用者仍是 `tasks.js:1148`，新增模块的Interface隐藏完整观察交互，没有虚构复用。任务／run生命周期由tasks拥有，观察窗口管理自身DOM和查询代际。新增guard均保护可到达的过期上下文或迟到回复；没有新增指定smell baseline的实证问题。局部CSS只改变观察容器换行，没有新行为、冗余guard、依赖、测试、CI或后台轮询／重试。

r2源码／wheel／安装、RECORD、冻结文件、公开projection／PNG和原HTTP均符合原件；失败与证据范围保留准确。交付总述已同步，最终静态须在冻结前更新。该轴不代替O4精确交付。

### Spec 终核

原 Spec 审查者对完整20文件的结论为：**修正后新增finding0，既有问题关闭；未发现缺失、越界或行为错误。**

原v7／exported入口、固定原候选、显式查询、安全全文、三态unknown和迟到隔离符合规格；后补class／CSS没有查询、安全或生命周期回退。两provider行为及最终视口、原来源／合同／导出、88文件runtime和所属资源清理均有相应原件。模型判词严格限首轮八附件；上层计划及D2后补记账未借CI。本次只读核验，未重跑产品、安装、浏览器或模型，O4仍未交付。

### r2与公开证据的独立原件核验

协调者重新读取r2 wheel和安装目录全字节，核得wheel SHA256 **`66649a70c9d73d512768847fbae7e2f46f460c6ad29ca344447580c6fb9e74b6`**；449件最终源码／wheel／安装相同，wheel RECORD454行／installed RECORD459行的摘要和大小全部符合，283件冻结参考文件逐件符合manifest，非editable。相对r1恰有前述容器class和局部CSS两件变化，其他447件相同；METADATA也相同，其README正文与当前README全字节一致。没有重装或重复已过的40项检查。

最终产品身份仍为 tasks `51f413dad6c7df6f45ef5eb861feffc69bdb76d1ff21469ced5f061fdc2a09e9`、candidate-observation `0f8eb175c51030c2d60d1d493df6febbd19836cc3ded5b16d14fde49d41f76c1`、style `be7206668ae25f99bde9e52775b0989f34620e5b7fd886d46ec1965b60685e71`。最后补充的架构图两条边 `Tasks → candidate-observation.js → Shared` 分别对应tasks的import／调用和观察模块的api／ui imports，符合已审源码；这只补充现有调用关系，不宣称Mermaid已渲染验收。

最终浏览器原stdout中的Result与JSON一致，原执行脚本有一次真实r2查询与1440／390两视口 **5项通过／8.97秒**；三张表的scrollWidth分别等于clientWidth，整页没有横向溢出。协调者实际查看两图，完整原／当前SHA与比较列可见。两图和原图逐字相同：桌面160,109B／SHA256 `b659e1098f67b30c39415b702e65f4ce5a64c70ee47afbbbca820842bf8424a6`；移动59,080B／SHA256 `67594366d6b2448e619439848734064ee45c7c8d97403bc99a66d8914e14b6a2`。

已独立按公开投影生成规则重建所有原件映射，acceptance全部字段、self-review原身份／审计／判词及两PNG均精确对应；两个JSON未带机器路径。acceptance SHA256为 `48aab32e80978eb4675ef4abae182a1f9bff5d5c1977b5f276f59a9100d72f5f`，self-review为 `6e3b7cf0224d115d5a750df36cf8d67735112115e1fc16bf1039c2e525354ee8`。模型判词仍限原八附件，未转授后补字节；首400夹具失败和r1表格横向滚动的原范围仍保留。

三个服务的 **125份原HTTP** sidecar、原request／response字节、大小和摘要已重新逐件核同trace，其中20次POST均为显式candidate-observations，provider49次GET、写操作0；四次hold均有真实owner响应与释放回执。成功响应固定原run／candidate并保持context_only及两项false授权标志，每份远端200响应摘要与provider读取对应，404仍为不可见／未知。未产生第二账本、批准、执行或回写。

对两个原native种子，以只读SQLite重新核完整source／首次保存时间，以原创建intent的canonical摘要及七份JSON逐件核对实际合同，88件当前runtime与after快照完整相同，原导出保持；当前Git分支直接ref仍为原candidate。两个项目的agent_runs／task-link／review-link／writeback表均0。原快照、manifest和清理审计相符；显式revision／rebind／ref控制不扩称整个控制库或repo reflog未变。

三个原pid／starttime均不再存活、原线程停止，协调者再核八个所属loopback端口均关闭，两次命名浏览器close回执exit0。清理范围只指拥有资源，未作全系统或OS隔离声明。

`static-r1`实际覆盖当时20件、347个本地Markdown目标、6个加载秘密值、issue0。之后交付总述、架构图及本报告有状态／文档追加，不冒称仍为static-r1原字节；最终冻结前应另做完整静态身份。该静态结果不证明anchor、外部URL或Mermaid渲染。没有重跑产品／模型／安装，没有真实SaaS、原生Windows正式工作区或新的完整六阶段验收。

**最终汇总：Standards累计1项P3、已关闭、开放0；Spec累计SP1／SP2两项P3、均已关闭、开放0。完整20文件独立本地审查通过；O4普通提交／推送、精确Git／Ref及本提交自己的双OS必要CI待交付。**
