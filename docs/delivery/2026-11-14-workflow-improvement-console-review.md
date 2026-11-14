# F10d6b 独立需求与可维护性评审

日期：2026-11-14。评审者：fresh-context 独立 reviewer `workflow_improvement_console_review`。仅收到原范围、固定基线、改动清单与原件位置，未继承实施对话。按根 `AGENTS.md`、`maintainable-project-delivery` 的 independent-review brief 与 `codebase-design` 直接检查源码及相邻调用方；本报告是本片唯一独立评审记录，后续在此补核。

## 身份与范围

分支 `refactor/architecture-foundations`，检查时 HEAD 与实施基线均为 `0fd74b16c98185081e06c4ef356700b881c781e7`。直接比较 `git diff` 到该完整基线。产品改动仅以下三个原文件；无新产品文件、依赖、schema、测试或 CI。

|文件|实际 SHA256|
|---|---|
|`src/ergora/web.py`|`cb17ff680dc1ba45c6dd4b6ac1ed9d7d4665f4b47590df004be35619544a593e`|
|`src/ergora/data/console/definitions.js`|`761ee783145dd0de99017f8240788fbf3a8c142dc1245c2d44e0e7f96a6ddc4c`|
|`src/ergora/data/console/submissions.js`|`5e235b8c5d23ac9a4c8e3ad822b43d14be470adbdac7e4dedc36fd967eba4d60`|

同时检查本片新[计划](../plans/2026-11-14-workflow-improvement-console.md)、[交付记录](2026-11-14-workflow-improvement-console.md)、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`。工作树另有前片 memory 文档与证据 bookkeeping，未将其计为本片产品或继承其运行通过。

直接阅读原 `ui.js`、`app.js`、`api.js`、`state.js`、`memory.js`、`skills.js` 的真实生命周期和提交 caller，以及 `workflow_definitions.py`、`definition_bundles.py`、CLI composition 分支。阅读 `test_definition_console.py` 与 `test_web.py`、`test_workflow_definitions.py`、`test_composition_manifests.py` 中对应原库、依赖／资源／权限、完整候选与 manifest 不可变合同。

## 两轴结论

- **需求轴：最终本地 approve。** 已检查的源码与最终本地原件满足本片合同，没有新增阻塞 finding。导入明确使用服务端完整目录和共享控制目录，回复保留原 ID／版本／digest 与文件／资源身份；用户随后显式刷新、选择精确版本、按原 grant 预览并保存新 manifest。旧定义、旧 manifest 与旧叶任务输入保持。自己的发布／CI 尚待，未批准完整发布交付。
- **可维护性轴：最终本地 approve。** 沿原 owner 增加一个目录 DTO 和薄路由，未建立第二定义库、采用账本或编译路径。共享 `submissionForm` 在定义、记忆、Skill 三个不同生产文件真实复用，发送前／后的不同生命周期规则集中在原 helper。业务 payload、权限、评价锁与持久状态仍留在原 owner；无新增抽象或无实际 caller 的接口。两个共享 caller 的实际受影响场景已经核过。

最终本地开放 finding：**需求 0，可维护性 0**；R1 已关闭。本结论覆盖以下固定 r3 产品与本地证据，不继承前片发布／CI，也不预批本片发布／CI。

## 实证 finding 与修复复核

**R1，P2，原已发出表单在来源 view 重绘后丢失原回执：已确认，源码及对应成功／失败绿例通过。** 位置 [`submissions.js:11`](../../src/ergora/data/console/submissions.js#L11)、[`submissions.js:33`](../../src/ergora/data/console/submissions.js#L33)。原 r2 将发送后回复也交给包含 `current()` 的 `visible()`；定义库或详情读回会经 `app.render → #main.replaceChildren` 断开来源 view，但原 modal 仍打开，导致成功／失败被丢弃并永久显示等待。原模板的该 finding 与 `receipt-red-r2.json` 四项／一个真实 HTTP200 样本相符，不能由旧包测试通过覆盖。

当前修正发送前在异步 payload 前后均核 `current() + attached()`，发出后只核原 form 是否仍连接且所属 dialog 打开。`ui.modal` 在新窗口建立时替换原内容，旧 form 因而断开；关闭窗口时 `dialog.open` 为 false；inline form 在页面重绘后断开。回复仅写闭包中的原 `receipt`，不会刷新列表、改变选择或操作后来窗口。r3 `receipt-green-r3.json` 四项／一个成功样本与 `receipt-error-r3.json` 四项／一个原错误样本均在后台库重绘后保留原回执；对应实际 HTTP 原件已经直接核摘要与状态。

## 已直接核对的行为与证据

1. [`web.py:513`](../../src/ergora/web.py#L513) 直接调用原 `workflow_definitions.import_bundle(state, Path(directory))`，继承原同源／请求头保护及统一错误处理。`workflow_definitions.library.checked` 在发布前按根定义上限完整 `_Compilation`，核子定义、精确 digest、资源继承／可读权限、图与预算；缺依赖不会发布部分根。`DefinitionLibrary.import_bundle` 的原复制检查、锁与 index 保持同内容幂等、同版本不同内容拒绝。未在新路由重复实现准入。
2. [`definitions.js:1086`](../../src/ergora/data/console/definitions.js#L1086) 的 `current` 绑定原 DOM view／tab／控制目录，不绑定项目。目录导入没有调用 `loadLibrary`、`openDefinition`、preview 或 freeze；原选择、预览和 manifest 保存仍是明确的各次操作。原 `_prepare_bundle`／`freeze_manifest` 保留独立完整快照，不重写旧输入。
3. 原 r1 两 suite 的保存 stdout 为 **107 passed／72.71秒**；r2、r3 各自原 web stdout 为 **9 passed／11.36秒、11.73秒**。命令、包路径和 returncode 已核；本 reviewer 未重新运行测试。r1 结果只证明其当时范围，r3 的 helper 行为另以当前原件复核。
4. 对最终 r3 wheel、暂存源码、当前工作树和安装目录进行了只读逐字节核对：**604 产品文件一致，wheel RECORD 612 行、installed RECORD 617 行的 hash／size 均一致，283 冻结参考 hash 一致**。wheel SHA256 为 `304a2898c1d6fb5d3c285aea3786be4aeba4eb81e582d2bfe801d9dce9e33f8c`；非 editable 身份和原 `package-identity.json` 相符。
5. 直接阅读 r3 主驱动、真实 ASGI 包装器和结果：`journey-r3.json` **31 项／15 个样本／8.452秒**通过，覆盖完整导出候选导入、明确刷新与选择、原 grant 预览／新 manifest、幂等／冲突／缺目录／缺依赖、重复提交锁、迟到成功和失败不替换 Help、执行后丢回复再核原记录、跨项目共享、旧 tab／home 窗口拒发及空项目控制目录。包装器先执行原应用再延迟／替换回复，503 是明确 fixture；候选为合成提案，未冒称真实质量或执行成功。当前已经逐件核对所有可用导入 HTTP 原请求／响应的 hash、原 status 与 digest。
6. 直接查看实际 **1440／960／390px** 六张页面与导入窗口截图，新增动作、目录字段、控制目录与提示可见，窗口内无横溢；主页面窄屏原预设表仍由自己的滚动容器承载。截图位于 `browser-r1/output/playwright/` 是该浏览器 daemon 初始工作目录；图中来源明确为 `browser-r3`，不把目录名当包身份。
7. 已核自身原结构模板最终 `self-review-r3-codex.json` 与 `original-result.json`：**37.295秒 approve**，十二完整文件 234,292B，含原 memory／skills 全文，三产品 hash 与本次一致；该模板明确只做所给完整文件的静态审查，不代替本独立评审与运行验收。
8. `shared-callers-r3.js` 沿实际已安装的记忆保存和 Skill 导入入口执行原 mutation，再在回复 held 时全局刷新；`shared-callers-r3.json` **8 项／2 样本／2.811秒**通过。两原回执包含各自原身份与完整值，来源 view 已重绘而原 modal 仍保留，提交按钮已移除。对应原 HTTP70／73 均为实际200，held 后已释放；未用 mock 替换原业务 owner。
9. 直接核 `cli-readback-r3.py`、六次 readback 命令与完整 stdout／stderr 摘要，加原 prepare／check／export／旧叶准备四次，共 **十次原 CLI**。逐项重比原 stdout：原定义与 before 完整对象相同；新定义／源包／网页候选 digest、definition／files／resources 相同；两实际目录包含空目录、文件字节与执行位的身份相同。根正文 **14,100B** 严格 UTF-8／CRLF 与返回完整文本逐字相同。新 manifest digest `db6e7f98f6648ba173f05ee2769bc8af5f011946c4c4c1a317f8fffbc730ab08` 与网页冻结相同，新旧 grant 相同，原 manifest 与旧叶仍引用旧根；原边、引用、permissions、limits 均保持。

原件均位于项目忽略目录 `.ergora/checks/workflow-improvement-console/`；本次仅做 Git／源码／已有原件读取、截图查看和只读 hash／size 计算，没有联网、安装、跑模型、执行测试、修改产品、提交或对外写入。

## 最终本地终核

在原报告上完成最终本地补核，三产品 SHA256 和实施基线均未变化：

- 对[固定证据索引](evidence/2026-11-14-workflow-improvement-console.json)原 **143 条不同路径引用**逐件读取并复算 bytes／SHA256，全部相同，没有重新生成或修改原数组。按 `sort_keys=True,separators=(',',':')` 序列化该原 references 数组的 SHA256 为 `c599f3f73ec073d9a197ae207f8e913534387776277231278e84ddbf78a818a5`，便于后续在更新状态字段时保持固定证据身份。
- 阅读 `audit-r3.py/.json`，并独立只读核原三套 before／cleanup、当前原目录及 trace：r1／r2／r3 分别 **2／19／75** 个原 HTTP，全部 **96 组**原请求、响应与逐条记录的 hash／内容均和 trace 一致，r3 **6 held 全释放、1 次执行后 fixture503**。原 source／作者 input／候选／旧 manifest／旧叶／task／packet／result 的目录、执行位与字节身份均保持；不从 `originals_unchanged: true` 单一字段推断。
- 对三服务 PID `2633428`／`2636858`／`2643445` 和观察到的浏览器 daemon PID `2634999` 直接核本机 `/proc`，均不存在；读取本机 `/proc/net/tcp{,6}`，端口 `33077`／`42965`／`38079` 均无监听。未连接网络或重启进程。
- 再核 `package-current-r3.json` 的 **604** 项与当前源码、构建快照、安装件逐字节相同。原模板实际 stdin **239,167B** 与原 prompt 相同，含完整 task、十二份完整文件 **234,292B** 和三项完整继承资源；源文件 packet hash 与当前 r3 相同。模板中的两份文档保持当时版本，后续状态记录没有冒充已重新运行模板。
- 最终主旅程31／15、两条 R1 绿例各4／1、共享 caller8／2 合计 **47 项／19 样本**；六张三宽截图已经直接查看。r2 两次主驱动失败和 R1 实红均保留各自身份，没有拼入最终通过数。
- 已重读最终活动计划与交付记录：产品／原件和自己的发布／CI 分列，本地终核前的 `pending` 是该记录等待本报告的状态。实施者可据本结论更新状态并接续原普通发布流程，无需重新生成原件数组或新增验收层。

## 剩余发布责任

本片自己的普通发布、完整远端 ref 与必要 CI 尚无本次证据，继续 **pending**。发布后仍由本 reviewer 沿本报告核固定提交与原证据身份、自己的必要 CI，不能借前片通过。尚不宣称完整发布交付；不合入 main，不强推。

真实质量／GPU／训练性能、完整 Forge／ReMe、F9d 与 G1 继续按原合同独立验收。本地表单锁的范围仍只是原窗口，不是跨窗口或持久执行去重。
