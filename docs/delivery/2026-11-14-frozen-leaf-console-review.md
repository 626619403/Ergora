# F10d4 冻结只读叶调用控制台：独立审查

日期：2026-11-14。审查者：fresh-context agent `/root/frozen_leaf_console_review`；未继承实现会话，按[本片原合同](../plans/2026-11-14-frozen-leaf-console.md)、`AGENTS.md` 与当前 `PLAN` 审查。使用 `maintainable-project-delivery`、`codebase-design`，参照双轴 code-review；按授权不再派生子审，不修改产品、安装、运行浏览器／模型或执行网络／Git写操作。

当前结论：**最终本地、固定普通发布及自身 CI 终态的需求／维护性两轴 approve，开放 0／0；R1／R2 源码与最终 r3 动态证据均已关闭。** 固定候选 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605` 自己的 run **43573335080** 已独立核为 Success，8 job／30 必要步骤通过。各阶段原文另存独立原件；CI 终核与本地索引故障恢复见本页末尾。

## 身份与结论

基线与本次源码初审 HEAD 均为 `f0b0d529cd9d85332e84dd4b4c34d49b381031df`。候选为未提交工作区，完整字节身份分别保存在 `.ergora/checks/frozen-leaf-console/independent/source-r1/identity.json` 和修后 `source-r2/identity.json`；`source-r2` 捕获于 `2026-11-14T07:34:26Z`。两轮完整源码与差异原件均保留，不能把目录名的 r2 与作者安装包 r2 混同。

|审查轴|当前结论|开放 finding|
|---|---|---|
|需求／行为|最终本地、固定普通发布及自身 CI 终态 approve；R1／R2 已源码与动态关闭，最终包、真实运行／浏览器、自身模板、收尾、完整 Ref 和自身 8 job／30 必要步骤已核。|0|
|职责／维护性|最终本地、固定普通发布及自身 CI 终态 approve；未发现其他有实证的职责、重复语义或配置约束问题；派生索引故障已按原字节恢复并保留失败原件。|0|

检查六个产品文件：`src/ergora/agent_runs.py`、`src/ergora/web.py`、`src/ergora/data/console/{agents,tools,retrospectives}.js`、`tests/test_composition_invocations.py`。另核本片新增的 `docs/USAGE.md`／`docs/architecture/current.md` 差异及本片计划／交付。前片 preparation/results 的发布和 CI 记账属于其他原候选，不纳入本片产品 verdict。

## 需求／行为

**R1 · P2 · 内层原生历史遗漏父生命周期（已源码与动态关闭）。** 原 `agents.js:12,55,223`：冻结叶记录读出的诊断通过 `outputPanels` 创建原生历史；其 `displayed` 仅检查全局 dialog 开启与节点连接。原生历史请求在途时切页／项目或重读记录，父观察已经失效，内层成功仍可能修改旧对话框，异常仍可能经 `ui.node` 进入全局通知，违反旧回复生命周期合同。最小修正是在原历史 owner 透传父 active 与记录代际，不另造历史读取器。已核 `source-r2` 的 `agents.js:5,12,43,55,222`：旧两处调用沿默认行为；冻结叶透传 `active() && reading === recordSequence`，内层成功、catch 和 finally 均用同一 `displayed`。最终安装件迟到成功／错误及记录重读反例已核，见本页末尾。

**R2 · P2 · tab 往返可复活旧对话框（已源码与动态关闭）。** 原 `agents.js:138` 配合 `app.js:123,177,195`：render 只替换 `#main`，全局 dialog 仍连接；A→B→A 且不刷新项目数据时，仅比较 `app.tab`／`app.data` 的谓词会重新为真，旧 check／run／历史回复可重新进入旧 dialog。原结果表单本身以 `view.isConnected` 拒绝卸载后的交接，故未据此声称新结果表单已受污染。最小修正是绑定实际打开者的卸载生命周期。已核 `source-r2` 的 `agents.js:114,137`、`tools.js:83`、`retrospectives.js:33`：两生产 caller 同步传入 `event.currentTarget`，打开按钮卸载后 `origin.isConnected` 永久为假，回到同 tab 的新按钮不复活旧观察。最终安装件往返后释放旧回复已核，见本页末尾。

其余源码核对：

- `_admit_input` 在 `inspect_input(material=True)` 的同一次完整读取内核所选 digest，后续 `run_input → _run_prepared` 仍先保存原 run、复制 snapshot 并重新核字节，再交原 adapter／process owner。没有 HTTP 预读后执行另一份输入的旁路。CLI 及 stage caller 省略新可选参数时保持原合同。
- 原 `workflow_definitions._Compilation` 保留祖先资源及全部来源，逐层 `_within` 校权限；完整 prompt／资产由原 inspector 重新编译核验。新入口不重写祖先资源或授权，HTTP 固定 `text-only`，Payload 拒绝额外字段，不开放 workspace／shell／自动 fallback／正式批准。
- 检查与明确提交分开，输入变更使旧准入无效；运行中的同步标志与字段禁用防同一 dialog 重入。异常没有自动重发，提示明确核原项目最近100条 run，普通运行成功不代表质量／评价／采用。
- `resultAction` 只交接成功原 composition run 的 `input_path`、`input_digest`、`result`、`result_sha256`；原结果表单失效旧检查，仍要求明确选择方向／重新检查。完整候选来自原结果文件，不从截断诊断重建。

## 职责／维护性

没有新增产品文件或第二账本。可选 digest 约束位于拥有完整输入准入的原 Module；两个 POST 和一个 GET 只转换传输字段并调用原 owner。`CompositionRunPayload` 仅增加严格超时，继承的 `arguments()` 通过实际 `model_dump()` 保留它，没有第二套执行语义。

新 `compositionDialog` 有 `tools.js`、`retrospectives.js` 两个不同生产文件的实际调用者；检查、明确调用、原记录观察与结果交接保持在原 Agent UI owner。原 `resultPanel` 以私有 `useRun` 暴露所需的一次交接，继续复用其检查／导出语义；新 `origin` 参数仅承载实际卸载约束。R1 通过原历史 owner 的小型可选参数修正，不复制归档代码或改动后端选择规则。未发现需扩大为框架、另建通用调度／状态抽象的理由。

新增回归针对“另一个合法完整 input 沿旧摘要提交”的真实静默错用风险，同时断言不触发模型／run；未硬编码可配置后端、容量或项目路径。此处仅做源码审查，没有把未执行的回归当作通过。

## 源码初审检查与当时剩余验收

独立执行的轻量静态检查原件为 `.ergora/checks/frozen-leaf-console/independent/static-r1/result.json`：三个 Python 文件 AST、三个改动 JS 的 module syntax 均通过；Node VM 只做 `app.js` 完整27模块 ESM link，未 evaluate、未启动浏览器，导出连接通过；六产品文件相对基线 `git diff --check` 通过。三 JS SHA 与 `source-r2/identity.json` 一致。沿调用者核 `cli.py`、`stage_driver.py`、`workflow_definitions.py`、`ui.js`、`api.js`、`app.js`、`state.js` 和旧输出调用者；均为只读。

源码初审时，作者交付记录仅分别报告初始 r1 五 suite 182通过、r2 web9通过及各自安装历史，独立审查当时尚未核这些运行原件。这一历史状态与最终补核分列；原报告逐字保存在 `.ergora/checks/frozen-leaf-console/independent/source-review-r1.md`。普通发布后仍须核固定文件与完整 Ref、自己的必要 CI，不能用前片成功或合成候选补称本片质量改进。

## 最终 r3 本地补核

同一 reviewer 仅只读核原件，未重跑安装、suite、模型、浏览器或网络。独立复核脚本、逐项结果和固定433引用快照保存在 `.ergora/checks/frozen-leaf-console/independent/local-final-r1/`；汇总身份见 `independent/final-local-review.json`。固定引用数组规范 SHA256 为 `e9c1d077c0661556eb5aecb4ad247d66305ceac1d230c55a4da58beb290b6426`，433 路径均唯一，大小／SHA 全部相同；本次未修改该原引用数组。六产品逐字同 `source-r2`。

- **最终包与回归。** 独立打开 wheel 并重算两份 RECORD，确认 wheel `6f06cbc1b478162eb26b744527456564c08df080f487b332892e58031ac719ce`、611 wheel 项／603产品／616安装 RECORD 行／283冻结文件，非editable安装、wheel／安装／最终 snapshot／当前603产品逐字一致。直接读原 pytest 输出核 r3 web9／12.57秒及 r1 五 suite182／132.16秒；另核183个Python文件和五份测试在两 snapshot 中同一。原运行仍归各自包，不将182项改称最终r3重跑结果。
- **实际模型与自身模板。** 原浏览器 run `a1eaa4c88bab4d2bafd3b7c0fa20d001` 为 Codex 作者，实际 stdin25,348B；`95428c68ab9d44ec8fd5c976a70f03a2` 为 Claude 审查，stdin43,160B。两份完整 snapshot 经原 inspector 复核，实际 stdin／完整 task／三份祖先及本叶资源／prompt摘要／原结果SHA相同，原生 command 与派发记录相同。审查 task 完整对象等于原作者 CLI checked JSON；作者 null、审查 approve 只属提案。最终自身原结构模板 run `a3d6d07692174b3d9ef4d1001d0e15a8` Codex44.545秒 approve，九份完整文件148,860B逐份SHA及全部祖先材料进入实际 stdin。旧66.424秒 request-changes及Codex回退理由保持，不冒称该次自身审查是异后端或已核baseline diff。
- **真实页面／HTTP与 R1／R2。** 直接对照私有服务／浏览器脚本及原返回，核七阶段74项已执行条件检查／39样本；各定位／APIResponse错误停点保留，没有把部分阶段改记全通过。70条原HTTP的完整请求／原响应／元数据逐字核对；八条held均为原owner完成后的实际响应且已释放，两条503仅夹具交付。最终lifecycle反例实测旧DOM／notice不变：内层历史迟到成功、项目切换后的迟到失败、原记录代际替换以及A→B→A均关闭R1／R2。另核在途提交防重入、关闭／替换、输入变化、失败HTTP200、不可用后端、丢回复原记录恢复与摘要／权限／超时拒绝；最早未发业务HTTP的“held”探针已排除。390／960／1440px的原宽度数据无横溢，并目视核390／1440px最终原图。
- **交接／导出与保持。** 三次实际安装CLI原回执成功；两份页面完整下载对象分别等于原CLI检查，页面／CLI合成正候选完整导出树同一，unused State不存在。只新增六条原run：两真实异后端、四确定性native夹具（其中一failed），派发前均有原running记录；真实模型未产生正候选，合成导出不代表质量改进。七组原文件／树当前重新核同一；只读SQLite核全部非`agent_runs`表保持，另一项目无run，当前六run等于收尾原件。原服务／浏览器PID已不存在，线程收尾为false；只读`/proc/net/tcp*`核原端口无监听，未发网络探针。

最终本地两轴 approve，R1／R2关闭，开放0／0。本地阶段未预批后继发布或CI；固定发布见下节，自己的必要CI另待终态补核。完整F10评价／采用／回退旅程、F9d／G1、真实GPU／B3与完整原生Forge C2不在本片结论中。此处是原片证据补核，不递归创建新审查。

## 固定普通发布补核

原 fresh-context reviewer 对固定候选 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605` 分别按需求／维护性两轴补核：**approve，开放0／0**。父提交精确为 `f0b0d529cd9d85332e84dd4b4c34d49b381031df`，23个变更blob逐份与原 `static-final-r1.json` 的路径／大小／SHA相同，固定完整diff无空白错误、变更Markdown链接在固定Git内存在。六产品／测试与原源码审查身份相同，后继纯计划及前片CI状态记账不计本片产品实现；后继Skill页面WIP未纳入审查。

直接读取固定Git的全部603产品blob，再与最终r3 snapshot／wheel／安装件逐字核对一致；两RECORD611／616行和283冻结文件重新核通过，wheel仍为 `6f06cbc1b478162eb26b744527456564c08df080f487b332892e58031ac719ce`。固定Git内444引用完整保持为发布后448引用的有序前缀，原433前缀未变；448件唯一原引用逐份大小／SHA相同，新增仅static／commit／push／ref四件。本轮未修改448前缀或固定原件。

原push回执明确以完整候选向 `refs/heads/refactor/architecture-foundations` 普通推送，无force，exit0及 `f0b0d52..055b0c4` 相符；原 `07:55:19 UTC` 完整远端Ref同为该完整SHA，未另行联网查询。前片精确f0b0d52自己的CI **43570785965** 与原独立终核已先行闭合：36原CI引用、三份独立终态证明及原八job／30必要步骤身份已核，原两轴终核时间 **07:47:19.630993 UTC** 早于本次普通push开始 **07:55:12.051447 UTC**；前片成功未替代本片自己的CI。

只读脚本 `independent/verify-publication-r1.py`、详细证明 `independent/publication-r1.json` 与双轴汇总 `independent/axes-publication-r1.json` 保留本轮身份；固定diff、固定／发布后manifest快照及本轮报告原件在 `independent/publication-r1/`。只用固定Git及原件；没有安装、产品／suite／模型／浏览器／网络重跑或Git写操作。普通发布补核当时，本片自己的CI仍待实际终态及独立补核，未称精确交付全部闭合；其后终核见下节，原范围限制保持。

## 自身 CI 终态独立补核

固定候选仍为 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605`，父提交仍为 `f0b0d529cd9d85332e84dd4b4c34d49b381031df`。独立从原官方 Actions listing 的完整 commit／workflow／branch 和原 UI JSON batch 核定自身 run **43573335080** 与八个 job ID；从固定 Git 工作流及六组配置推导 plan 1 步、Linux 6×4 步、Windows 5 步，共 **30 必要步骤**。最后 run 原 HTML `ci-run-html-r5` 于 **08:18:45.978716 UTC** 返回 Success，SHA256 `de7679f8fdecd4d1b33b00faa47cc4811dad61fb491bb654d7b896cc9f99d363`。八个原 job 页的30步骤与八条 `Complete job` 均为 success，完成标记、时刻及完整候选 SHA／job／step 日志路径逐项相符。Windows PowerShell 5.1 安装升级原步骤为08:15:38–08:16:37 UTC，job于08:16:40 UTC完成；六个Linux页按固定条件跳过该Windows专用步骤。

独立重建四份 `ci-status-r1/r2/r4/r5.json` 投影，逐字段等于对应原HTML，未运行原解析器去覆盖旧状态。r1–r4原run页面仍为 In progress；r4虽然全部必要步骤已成功，仍未据此预批run。最终仅r5自身Success闭合本片，前片43570785965的成功不作替代。22份原HTML和一份原UI JSON batch的HTTP200、原／最终URL、完整正文大小及SHA逐份相符；这是已保存官方UI状态审查，没有REST日志或artifact归档下载及测试数量推断。

本地CI补账曾因目标路径变量重用，把拟写公共manifest误写到派生 `ci-ui-metadata-r1.json`；公共manifest当时尚未补入CI，reviewer读取时发现，作者明确报告了原因。失败输出原样保留为 `ci-bookkeeping-failed-r1.json`，恢复脚本及回执另存 `bookkeeping-recovery-r1.py/json`。独立根据未改的原 `ci-job-batch-r1/body.json`／receipt和run-r1原receipt重新生成索引，确认恢复后 **2119B／SHA256 `e12806f96ddcb0285e3023990e8770a197626780fcc709e67a792440318fecec`** 与误写前索引记录逐字相同，且保持初次采样时的in_progress状态。审查指出公共索引缺少两份恢复来源后，两原件已另列 `recovery_source_references`；恢复三件亦单列。原50条CI引用及原448条发布引用的内容、顺序均未改，全部原件重新核大小／SHA通过；原官方HTML／JSON／receipt与既存记录相符。该派生索引故障已关闭，不隐去或改写为原官方终态故障。

独立只读脚本 `independent/verify-ci-terminal-r1.py`、详细证明 `independent/ci-terminal-r1.json`、双轴汇总 `independent/axes-ci-terminal-r1.json` 及 `independent/ci-terminal-r1/` 下的输入manifest、固定工作流／组配置、重建索引与阶段报告原件保留完整身份。另重新读取固定23变更blob并核原SHA，认证既有603产品／最终包发布证明及三份独立发布原件，没有重跑安装、suite、模型、浏览器或网络，没有产品／Git写操作。后继F10d5的 `skills.js` 及其他工作区WIP未纳入本次verdict。

本片自身CI终态需求／维护性两轴 **approve，开放0／0**；结合本页既有本地及固定普通发布补核，F10d4原范围闭合。完整F10评价／采用／回退旅程、F9d／G1、真实GPU／B3与完整原生Forge C2仍不在本片结论中。
