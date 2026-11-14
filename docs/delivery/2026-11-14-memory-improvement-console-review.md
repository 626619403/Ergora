# F10d6a 独立两轴审查

审查者：`memory_improvement_console_review`，独立 fresh-context reviewer；2026-11-14。先读取原始要求、固定基线与源码，再核实施方记录。依照本仓库 `AGENTS.md`、`maintainable-project-delivery` 及 `codebase-design`；仅只读核查并编写本报告，未修改产品、安装、启动测试／模型、联网或发布。

## 最终本地结论

- **需求正确性：approve；开放 finding 0。** 修后源码、最终非 editable r2、原完整候选保存／更正／恢复旅程、最终新夹具的一次完整生命周期、共享 Skill 旅程与收尾原件均已独立核实。自身模板 R1 已实红／实绿关闭。
- **可维护性：approve；开放 finding 0。** 共享实现有 memory／skills 两个真实生产文件，仍沿原页面和原业务 owner；未引入业务账本、权限、评价器或新增测试／CI。公开操作说明、架构和交付状态与实际证据一致。

这是最终本地审查结论。本片尚未普通发布，精确提交／远端 Ref 与自己的必要 CI 仍待实施方完成并提交原 reviewer 补核；不标精确交付完成，不借前片 CI 证明本片。

## 精确范围

基线为 `ed7fac5ba6bbe5ec73da0fed7175c4705116ea5b`；工作分支 `refactor/architecture-foundations`，当前 HEAD 仍为该基线。直接读取对基线的 tracked diff 和未跟踪新文件，产品仅下列三件；相邻 Skill 发布／CI 文档 WIP 不纳入本片源码结论。

|文件|字节|受审 SHA-256|
|---|---:|---|
|`src/ergora/data/console/memory.js`|10085|`5337e7a7181c3df6ca01de29f485e16bc92ef6f1eb8f34788181e0b7bdc82d8f`|
|`src/ergora/data/console/skills.js`|15329|`08e55e9697ec664ae4c6cb639ed612541551826262a56b7e64fe7111ce0be3c4`|
|`src/ergora/data/console/submissions.js`（新）|2066|`734decac7648a45f7131fc281264e6887b4754c5c0f84fa92af45290bf43eb4b`|

另读 `ui.js`、`api.js`、`app.js`、`memory.py`、`web.py`、`skills.py`、`skill_assets.py`、`evaluation.py`、记忆候选 export owner、相关原测试与打包配置。独立逐字核前八个相邻 owner／调用文件均与基线相同。最终三产品 SHA 与首轮源码审查保持；另核本片新增的 `docs/USAGE.md` 与 `docs/architecture/current.md` 差异，以及本片计划、交付和[证据索引](evidence/2026-11-14-memory-improvement-console.json)。

## 需求与调用核对

1. `memory.js:171` 的原保存表单新增可选 UTF-8 文件。`TextDecoder` 使用严格解码和 `ignoreBOM: true`，不做换行变换；未选择文件且输入框值仍等于初始浏览器值时，发送 `item.text` 原字符串，因此未编辑更正不将 CRLF 改为 LF。来源、原 ID／预期 revision 与期限仍走原 `memory.save`。
2. `submissions.js:8` 复用原 `ui.form` 的同步禁用机制；先检查发起表单与原 view／modal，再等待 payload，文件异步读取结束后重新准入。已发出请求的表单替换为完整提交和原回复的局部回执；成功／失败不关闭全局窗口、不刷新页面、不自动重发。错误说明保留结果不确定性。
3. `memory.js:26` 在点击历史时立即创建其内容容器，迟到成功／错误仅能更新仍连接且打开的原容器；Help 或其他 modal 替换后旧容器失效。显式单选恢复共用提交锁，并传入原 item revision。历史所选有效期、CAS、跨项目隔离、到期排除和删除历史清空均继续由未改动的原 Python owner 执行。
4. 逐个检查共享模块的全部生产调用：memory 的保存、恢复、删除、同步／重建，skills 的采用、回退、注册评价集、导入和 GEPA 提交。所有调用均传入函数型 `current`；路径均包含各自原项目 `base`，删除保留 `DELETE`。Skills 采用继续传比较代际 `current`，其余传原 view 回调。
5. Skills 的版本比较／评价证据比较代际、`pendingEvaluations` 以状态目录和项目定位的未决锁、显式解除 unknown 及原采用／回退后端门禁保持。共享抽取未将这些业务语义迁入通用模块。新模块只集中重复的生命周期、局部回执和传输行为；`ui.form` 继续拥有提交按钮锁，memory 继续拥有文本与历史处理，接口和职责可定位。

## R1 处置

自身原模板发现的 **P2 R1** 成立：首包 `skills.js` 在 `versions.map` 内以布尔 `active` 遮蔽页面回调；回退 `submissionForm(..., active)` 会在 `submissions.js:11` 调用布尔，导致每次回退均在发 HTTP 前失败。最小修复为当前 `skills.js:174` 的 `isActive`，回退在 `:215` 传入外层函数。

独立核 `skill-red-r1b.json` 的原导入、suite、双评价和采用五个样本，以及首包 HTTP 目录：真实回退报 `current is not a function`，零 rollback 请求。最终 `skill-journey-r2.json` 通过原 UI 执行导入／注册／双评价／比较／采用／回退；原 HTTP 仅一条 rollback，原 head 从 revision2 追加到 revision3 并回到原 baseline，原 cleanup 再次读回相同。**R1 关闭**。首包 `skills.js` 的 SHA 为 `a3e191b50524685141f41756c4a6c694c8f731a9dfa975d9870dce0758fe5c03`；首包测试与红例保留其原身份，不改记为最终 r2 验收。

## 最终原件核验

证据根为 `.ergora/checks/memory-improvement-console/`。审查者未重跑测试或模型；下列运行由实施方产生，本审查直接读取脚本、原 stdout、请求／回复和持久目录，并执行比例适当的只读身份核对。

|核验|独立结论|
|---|---|
|最终包|逐字比较当前源码、构建快照、wheel、非 editable 安装的全部 604 个产品文件；独立验证 wheel 612／安装 617 条 RECORD 和 283 个冻结文件。wheel SHA 为 `cc697e93e2100a7e47a908ea56fa104cd9a929a94f0b7be109519db1ccb89e83`。|
|原测试|`install-r2/final-tests/result.json` 与原 `process/stdout.txt` 一致，原三 suite 共 59 passed／57.48 秒，监督耗时 59.047 秒。测试及 CI 无新增。|
|完整记忆旅程|`journey-r2.json` 为 20 项／10 样本。独立核 `candidate/memory.txt`、export receipt、原页面记录及五份 CLI stdout：候选完整 12,828B，SHA `91534a3131aa5788af90c1ecfa56641056787edecf3305059355a65628b3bbcf`，保留 BOM／CRLF；catalog／list／history／search 中六份对应修订正文和 source 均同一。未编辑更正为 revision2，编辑及并发冲突后显式恢复为 revision5；过期恢复保留过去期限，原检索排除；beta 无此记录。|
|完整生命周期|直接读 `lifecycle-final-r2.js`、`service-lifecycle-r2.py` 和新 `browser-lifecycle-r2` 全 32 组原 HTTP。夹具先执行原 app，再 hold／替换原回复；最终一次完整运行 28 项／15 样本、8 held／2 次执行后 503。迟到历史／save 成功与错误不影响后开的 Help；unknown 新建只留一条 revision1；文件解码后 modal 失效零提交，无效 UTF-8 可在原表单修正；目录读代际保持。恢复成功及删除各仅一条请求，历史全空后原恢复被拒绝；旧项目 sync 不开新窗口，beta rebuild 的 query 为 `rebuild=true`。|
|共享 Skill|最终 23 项／10 样本，22 原 HTTP；双评价固定同 suite，inflight 共享锁阻止重复 dispatch，改变选择撤回旧采用表单，同 run 不可采用；采用记录保留精确双 run，回退实绿见上。比较代际、跨 view 未决锁与其他未改动分支另经源码核对，未冒称全部错误排列均动态覆盖。|
|布局与文案|主记忆页、Skill 页的 1440／960／390px，以及完整长正文的编辑／历史窗口另 6 项通过；直接目视核桌面记忆、390px 两种窗口与 960px Skill 截图，无所见横向溢出。USAGE 的文件优先级、无效 UTF-8、未编辑正文、期限、局部回执与明确刷新说明均与实现一致；架构准确区分共享提交和页面业务职责。|
|自身模板|直接核原 `original-result.json` 的 SHA 和 `approve`、9 件完整 packet、65,340B 原 prompt 与 stdin 逐字同一，3 项继承资源均在原 stdin；61.176 秒的 Codex 调用与独立审查分列。|
|原件与收尾|逐份校验最终三组 r2 的 130 原 request／response SHA 与保存的 trace，合计 20 held／4 次执行后 503。独立只读重算三组记忆 packet／result／author-input／manifest／candidate／原 baseline history／Git 与 before 相同，Skill 两组原 cleanup 记录 source／scorer 等保持。通过 `/proc` 只读核六服务 PID、三观察到的浏览器 PID 均消失，六端口无监听。|
|索引与记录|逐项重算证据索引固定 242 条引用的字节／SHA；三个产品身份相同，相关本地文档链接可达。初始状态已改为明确历史语气，最终本地／独立审查／发布／CI 分列。|

## 历史失败与结论限制

基线 7 项／5 样本与 CRLF 3 项／2 样本只证明旧问题可达。早期 `journey-r1` 的 APIResponse 采样错误、`skill-red-r1` 的 suite setup 错误、安装／端口驱动错误及 `lifecycle-r2` 至 `r2e` 的检索 OR 预期、视口、render 等待与变量作用域失败均保留；完整最终生命周期使用新的同一 r2 夹具一次重跑通过，没有将旧片段相加当通过。

`process-results-r2.json` 保留两个旧 memory 驱动在 uvicorn 已关闭 socket 后调用 `getsockname` 的退出错误。因此不声称这两份原 finally 成功；原 HTTP 已保存，`audit-final-r2.py/.json` 的独立只读补核确认原件和进程／端口状态，本审查亦重新核实。最终新生命周期和两份 Skill 驱动原 cleanup 均正常完成。

合计最终页面 77 项／35 样本与 14 次原 CLI 的合同范围成立；不外推为真实模型质量／训练性能、外部 ReMe 可用性、所有错误排列或跨浏览器执行去重。流程 import、F10 汇总、F9d／G1 均属后继片。最终本地需求及维护性两轴通过；剩余出口仅为本片普通发布、精确 Ref、自己的必要 CI 和原 reviewer 发布补核。
