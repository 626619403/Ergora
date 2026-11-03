# F4.1 正式任务只读页面：独立需求、结构与性能审查

日期：2026-11-03。审查者：`formal_task_console_read_review`，新的独立上下文；未参与实现。按仓库 AGENTS、`maintainable-project-delivery` 独立审查说明及 `review-pr` 执行。先读[原始 F4 需求](../plans/2026-11-01-all-in-one.md#f4-正式任务控制台与运行视图)和 [LC1](../research/2026-11-02-low-code-editors.md)，再读实际 diff、全部新文件及相邻调用，最后读[作者记录](2026-11-03-formal-task-console.md)。

## 结论

需求合规：**待修正两项 P2 后复核**。任务分页、冻结合同/角色/工作单元、本地 submission 与明确固定 run 查询已按既有 API 接入；未查询、not_found、连接失败及原始终态没有被合并成成功。项目切换时的异步隔离仍有窗口，运行阶段位置显示也有确定的名称不匹配。

可维护性：**页面所有权与现有能力复用通过，生命周期缺口随 R1 修正**。`tasks.js` 是一个完整页面的所有者，唯一生产调用者为 `app.js` 的视图路由；这是与已有页面一致的边界，不是以假设复用为由建立的单消费者通用库。没有要求再拆模块、增加框架或重写公共 API。没有发现额外的结构或可证实的性能阻塞项；本次不作吞吐量、大任务容量或完整 F4 验收结论。

## 确认的问题

### R1 · P2：切换项目后，旧任务页面在刷新完成前仍然有效

位置：[tasks.js:95](../../src/ergora/data/console/tasks.js#L95)、[tasks.js:158](../../src/ergora/data/console/tasks.js#L158)；相关调用：[app.js:128](../../src/ergora/data/console/app.js#L128)。置信度：95。

项目选择事件同步修改 `app.project`，随后异步读取 bootstrap 和新项目 dashboard，只有成功返回后的 `render()` 才移除旧页面。此期间旧 `view.isConnected` 仍为 true，旧详情和运行查询的序号也未变化。因此，在 A 的详情或运行查询未返回时选 B，如果 B 的 dashboard 更慢或失败，A 的迟到响应仍会写进当前连接着的页面；选择器已是 B，用户也仍能操作旧 A 的查询表单。它不会越过服务端项目校验或产生任务写操作，但违反本片“切项目后旧响应失效”的显示归属合同；刷新失败时窗口可持续存在。

已有 `browser-boundaries.js` 的跨项目反例先等待 B 的任务标题出现，再释放 A 的响应，只覆盖旧视图已经断开的情况，不能排除此窗口。

最小修复：在拥有项目切换生命周期的 `app.js` 中立即废弃/移除旧内容并显示加载或失败状态；或给任务页面的入口与异步完成增加真实当前项目/生命周期身份检查。若选用身份检查，需同时防止 A→B→A 时旧实例复活。无需增加新的状态框架。验证时应阻塞 B 的 dashboard，在它完成前释放 A 的详情/状态；再覆盖 B 失败和 A→B→A，确认旧表单不能继续作为所选项目的界面工作。

### R2 · P2：六阶段位置使用了不相等的原生 phase 名称

位置：[tasks.js:169](../../src/ergora/data/console/tasks.js#L169)。置信度：100。

当前位置判断把 `observed.phase.toLowerCase()` 与 `state.js` 中 `inventory/plan/work/integrate/verify/review` 比较。真实运行器在 [workflow.py:194](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/workflow.py#L194) 起返回 `PLANNING/IMPLEMENTING/INTEGRATING/VERIFYING/REVIEWING`，只转换大小写不会得到 `plan/work/integrate/verify/review`。因此除 `INVENTORY` 外，正常运行中阶段条均没有当前位置，虽然上方原始 phase 标签和原始结果仍正确。

最小修复：在本页显式映射这六个实际运行阶段，或按原 `active_stages` 语义投影阶段；保留原始 phase 标签，不把待批准、BLOCKED、REVIEW_READY、取消未确认或其他终态编造成正在执行的某阶段。验证至少包含上述真实 phase 名称及待批准/终态。现有浏览器正常旅程检查的是五个已闭合原 run，不能证明运行中位置映射正确。

## 检查范围与身份

基线及当前 HEAD：`2add1bf3435738509462e6978d7f83742422ea6f`，分支 `refactor/architecture-foundations`；候选尚未提交。使用 `git diff` 与 `git ls-files --others --exclude-standard` 核对全部范围：生产文件为 `console/app.js`、`index.html`、`overview.js`、`style.css` 和未跟踪的完整 `tasks.js`；文档为 README、USAGE、architecture/current、PLAN、详细计划及本片作者记录。检查时没有 Python、测试、依赖或冻结 reference 的差异。

本次审查的 `tasks.js` SHA256 为 `109c2dafd5e939c4e2cf8b5bbc0ebff27eca07752ad9303dd357e15eb136b64c`，`app.js` 为 `2a18b5d27efa3d8d085b82608d65fc187bd80303c60656fd76369a07f1f4f5f6`。独立只读字节核对确认 wheel `3cf98a00440ab0fdab24cc05d845fed0f1137e4e100a6a2f739954499fd0ad3e` 的 348 个 package 文件与源码、两份非 editable 安装及记录清单一致；具体五个变更资产身份保存在私有 `.ergora/checks/f4-task-console/reviewer/intake-identity.json`。此身份只对应初审候选，修正后的包需重新绑定。

## 结构、控制流与成本

- 页面使用原 `api.js`、`ui.js` 和 `state.js`；`facts`、`disclosure` 是同页私有展示算法。冻结绑定取自任务详情，缺少旧快照明确显示缺失，不回填当前项目绑定。所有来源文本经原安全 DOM 工具写入。
- 列表请求固定扫描上限 20，按服务端 `next_after` 前进；空匹配页仍保留下一页，错误记录单列。首次进入有可选任务时为 1 次列表 GET、2 次并行的详情/submission GET，明确查询原 run 再增加 1 次 GET；没有逐任务 Temporal 请求、轮询或长连接。单次列表重绘至多 20 项，单个任务工作单元沿既有模板上限 4/24；完整 JSON 披露会在折叠时也序列化，但当前没有证据表明需要新懒加载或虚拟列表。
- 列表序号保护重复读取，详情序号保护切任务，run 序号保护修改输入，视图连接检查保护同步离开页面；这些都有可达场景。R1 是项目异步切换缺少及时失效，并非应删除已有保护。`Promise.allSettled` 允许本地回执失败时继续显示可读合同，错误路径没有补造执行事实。
- 只持久保存项目、标签、任务和 run 选择；重开后执行状态需明确查询。完整创建/批准/取消/对账/导出界面、人工待办、有界日志及完整浏览器正式开发旅程仍按基线既定分片归 F4.2–F4.4，不因 LC1 中较粗的 F4.1 命名而提前验收完整 F4。

以上是静态成本边界及已记录请求数量，不是性能基准。新增 `tasks.js` 约 9.2 KB，没有产品依赖或新构建链。

## 已核证据与限制

审查者实际执行了范围/差异检查、`git diff --check`、13 个 ES 模块的 Node 语法解析及上述 348 文件字节核对，均通过；没有运行测试、模型、构建、安装、HTTP/Temporal 查询、浏览器或服务启停，也未改生产代码或打开凭据。写入仅限本报告和私有审查核算。

对作者证据的复核：`targeted-command.json`/`targeted.log` 显示首包的三个原定向测试文件为 44 passed、1 个既有 warning、pytest 43.47 秒；不将其写成 DOM 修正后的再次回归。`browser-normal` 原脚本/结果核五原 run 的 phase/候选与实际 API、刷新显式重查、41 GET、390px 无横向溢出；`browser-boundaries` 核真实不存在 run、真实 API 扫描窗为 2 的空中间页/前后游标，以及受控迟到、旧快照、文本安全、缺注册；累计 75 GET、无 pageerror。边界段命令包装的退出码仍保留为 1，原 CLI `### Result` 有成功结果且无 `### Error`，与作者记录的解析器失败区分一致，不冒充重跑。

初审时实际 Temporal 停止/重开恢复、416 原文件后快照、服务收尾仍在作者进行中，未据此下结论；R1/R2 的修正、相应浏览器反例及新包身份需复核后才可关闭本片。当前候选 CI、提交与推送尚待实施者实际核对，本报告不宣称已完成。

## 同片中间复核：1ff 候选，尚未收口

复核对象为 wheel `1ff7a245da408cc6f2f9e8cd09193ee2ffbf9160fdfba54d07eb024a4d573058`。独立核对 348 文件的源码、wheel、两份安装均一致，283 冻结文件保持；较初审包仅 `app.js`/`tasks.js` 改变。两模块语法及 diff whitespace 通过，核算保存为私有 `reviewer/fix-identity.json`。

该候选的 R1 在刷新入口同步清空并卸载旧页面，且过时成功/失败受原 refresh 序号限制；R2 已按真实六种活动 phase 显式映射，并禁止闭合运行显示活动阶段。独立核对 `browser-normal-final`、`browser-boundaries-final`、`browser-review-fixes-v3` 的原 CLI Result 与保存 JSON 相同，三个包装命令退出码均为 0，无 CLI Error。v3 实际覆盖 14 种阶段、B dashboard 仍等待/失败时释放 A 响应、等待/失败期间切标签与重试、A→B→A 后旧 A/旧 B 响应不能取代新实例。完整最终请求记录是 235 GET、0 pageerror；含前两次失败脚本尝试，不把它们计为通过用例。

### R3 · P2：刷新清空快照会影响既有工作流保存回调

实施者在中间复核期间先发现：同项目保存请求未返回时，新的无条件刷新把 `app.data` 清成 null；[workflow.js:224](../../src/ergora/data/console/workflow.js#L224) 只检查当前项目 ID，保存回调随后访问 `app.data.drafts`，会报错。独立补查确认，仅把清空限制为项目切换仍有可达窗口：A 保存待返回→切 B→再切 A，但 A dashboard 尚未返回时释放原 A 保存；当前项目又是 A，快照仍为空，回调也会越过原项目检查。

最小修复应保留同项目刷新原有语义，并在工作流异步保存的快照所有者边界处理当前快照缺失/归属，或采用不会破坏该消费者的视图失效方式；无需增加公共状态框架。需补同项目刷新/保存交错及 A→B→A 等待中保存回执的反例。`1ff` 仅保留为中间身份，不作为最终通过；等待修正后的新包与证据后续记同片结论。
