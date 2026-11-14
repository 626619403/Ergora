# F10d5 独立审查

审查者：fresh-context agent `/root/skill_improvement_console_review`，2026-11-14。以原始要求与固定 diff 开始，未继承实施对话；采用 `maintainable-project-delivery` 的独立审查 brief 和 `codebase-design`。仅写本报告与私有独立核查证明，未改产品、安装依赖、请求模型、提交或推送。

## 当前结果

|轴|当前结论|确切范围|
|---|---|---|
|需求符合性|最终 r2 本地 approve，开放 finding 0；R1／R2 已关闭|68 项／46 样本逐一匹配原 HTTP；完整导入／同 suite 评价／比较／明确采用／回退、负例／并发写、CLI／原件／收尾与 649 条引用均独立终核|
|可维护性|最终 r2 approve，开放 finding 0|完整源码与邻接 caller 已核；原 owner 内的临时未决 UI 请求跨 render，回执仍绑定原 form／view；未增加评价器、采用账本、权限语义或跨页面框架|

这是下列确切源码、包与实际证据支持的最终本地两轴结论；普通发布与本片自己的必要终态 CI 仍分别待核。F10d4 自己的发布／CI 不用于本片验收。

初轮仅源码审查曾记录无 finding；收到自身模板的实际 request-changes 后，独立重走相关 caller，确认两项。r2 实际修复和浏览器原件已分别补核关闭；保留 r1 发现／失败与成功的原身份。

## 固定身份与已读范围

实施基线／当前 HEAD 为 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605`，分支 `refactor/architecture-foundations`。固定基线至工作树的产品变更仅 `src/ergora/data/console/skills.js`。r2 完整 443 行，Git blob `b6fd101c72848998af825b8dbd6a8d6ef21a1263`，SHA-256 `abf84a33a7ad130e6e8f06c7fab8aee31e4957c7fb667b9ca42a94e66ef39685`；已重新阅读全文与固定 diff。历史 r1 为 416 行、blob `4188c7b682751738b1e69687bbd95c068a11f294`、SHA-256 `841f46f29f9f1e0e9a89bb124d67c91b0e63c3e1db73a0b11e147890852e5b20`。

直接阅读了 `AGENTS.md`、`docs/PLAN.md`、本片计划、未跟踪交付文档，完整固定 diff 和新局部函数；邻接 `ui.js`、`api.js`、`state.js`、`app.js`、相关 CSS；原 `skills.py`、`skill_assets.py`、`evaluation.py`，`web.py` 的 payload、dashboard 与全部 Skill／evaluation／optimization route，原 Skill 测试中的完整旅程和拒绝门禁。其他文档的在途修改属于相邻交付记账，没有据此扩展本片产品范围。

## 已确认 finding 与最小修正

1. **R1／P1，r2 已关闭：评价未决锁在 tab 往返后丢失。** r1 `skills.js:69` 把 `evaluating` 放在 `skillsView` 的 render 生命周期中，而 `app.js` 每次 tab 切换都会创建全新 view。评价在途时离开并返回 Skill，就得到 `evaluating=false` 与可用按钮，可以再发真实评价；unknown 后往返同样绕开“先核原记录”的锁，造成重复 evaluator 执行和成本。原 caller 分析后另有 r1 实际复现；两个 distinct 原 HTTP run 已独立核。r2 `skills.js:8` 在原 owner 只保存本窗口按控制目录＋项目区分的临时未决 HTTP 请求；完整原返回跨 view 释放，旧 view 不更新新界面。实际 tab／project 往返与 dispatch 重入无额外评价；unknown 503 后跨 tab／刷新仍锁定，原成功 run 可读，只有用户“已核原记录”明确确认才解除且不发 evaluator 请求。未以 UI 匹配推断 run 归属或新增 ledger。
2. **R2／P2，r2 已关闭：仍可见的陈旧 modal 提交静默返回。** r1 `skills.js:18` 的 `visible()` 同时要求原 view 连通，但 `app.js` 更换 `#main` 并不关闭 `#dialog`。modal 阻止一般鼠标点击底层 tab，不过“先启动异步刷新→打开导入或回退 modal→迟到刷新替换主页面→在仍可见 modal 提交”可达；提交静默 return，原 `ui.form` 最后又恢复按钮，用户没有失败原因或恢复路径。r1 导入表单的实际反例已读；r2 `skills.js:22` 在显式提交时，仅给仍可见原表单写“来源页面已变化，关闭后重开，此次未提交”说明并撤下输入／按钮。实际 held dashboard 迟到后仍可见导入表单提交得到局部说明，HTTP 计数证明 0 mutation；同一 helper 的回退 caller 源码覆盖，未新增 observer、全局弹窗或共享 framework。

关闭依据是实际 r2 完整源码、独立包身份和对应动态原件；不是拟议方案或 r1 成功。两项修复未扩大产品范围。

## 源码核查

- r2 `skills.js:139` 的 comparison 代际由版本、suite、双方 run 选择变化撤销；成功、错误和 finally 都检查当前代际。采用表单捕获本次精确 run ID、原 head revision，与本次 comparison 共用有效性判断。diff 使用独立代际，同样隔离旧成功／错误／finally。
- r2 `skills.js:93` 的双方评价在同一窗口跨 view 共享未决锁；提交前固定 digest 与 suite，结果保留原提交与完整原记录。完整原返回释放，unknown 明示先核原记录、再由用户明确解除。切页／项目导致原 view 断开，旧评价不弹 modal、全局通知、refresh 或修改新 view。全页面 reload／其他浏览器窗口不共享这份临时锁，原后端门禁继续生效。
- r2 `skills.js:17` 的局部 `submissionForm` 只向既有静态 route 提交一次；提交时撤掉原输入和按钮，保留原 payload 回执。回包仅在原 view、原 form 仍可见时追加；dialog 已关闭或被替换时不触及新窗口。原 `ui.form` 的 finally 只修改已撤掉的原按钮，不能恢复新窗口按钮。这里是原 form 内防重复；关闭重开后用户再次明确提交不冒称被全局禁止。
- HTTP 继续直接使用原 owner。`evaluation.compare` 复核项目、同 Skill／suite、完整三 split、正确性、成本和改善门禁，并复查 scorer／Skill 文件身份；`skills.adopt` 每次重新 compare，`move_head` 继续以 revision 与 baseline digest 做最终原子门禁；rollback 继续只允许曾活动版本与明确理由。UI 没有复制这些可信门禁或赋予模型采用权。
- `submissionForm` 不是对外新增 seam；所有 caller 均在原文件，分别消费导入、suite 注册、采用、回退与既有 GEPA 的同类生命周期。既有 `ui.form` 只管理按钮等待，不提供提交回执与原 view／dialog 有效性；局部 helper 隐藏了真实重复复杂度。新增 `allowEvaluation` 只给本页面的 unknown 请求创建明确解除动作，与 `pendingEvaluations` 同属原 Skill owner 的私有生命周期实现；`refreshNote`、`active` 与 `invalidateComparison` 也保持局部。没有发现应迁出的新 module、无依据的新 adapter、可证实的重复可信校验或把页面约束推广成共享框架。

## 已验与限制

以下 r1 证据保持原身份，独立证明位于私有 `.ergora/checks/skill-improvement-console/independent/`：

- `node --input-type=module --check`，退出 0；仅证明 ES module 语法。
- 最终 r1 包的全部 603 产品文件与工作树、构建源码、wheel、非 editable 安装逐字相同；611 个 wheel 文件、611／616 条两份 RECORD 的全部有摘要项、283 个冻结参考文件逐项独立验算。wheel SHA-256 `f284c7b4bbe46ce7f0aa3d95421363f7df66f688f14c50b2516d25605a6e991b`。这是身份／完整性核查，不是安装套件结果。
- 阅读原 baseline service／driver 与结果，逐项验算 13 组原 HTTP request／response／metadata 和 trace 摘要；2 个 held response 均已 release。基线 6 项／3 样本／3.630 秒只证明旧实现三个问题可复现：选择后旧采用表单、跨项目迟到评价 modal、旧导入关闭替换 modal。基线 head 仍为 revision 1，没有采用／回退或模型调用。
- 随后直接核了 r1 非 editable 安装件 `tests/test_web.py tests/test_skills_evaluation.py` 的 result 与完整原 stdout／stderr／stdin：44 passed／pytest 46.78 秒、外层 48.486 秒、status succeeded／exit 0、stderr 为空。保留 `independent/installed-suite-audit-r1.json`，不重跑，也不把 Python／HTTP suite 当作浏览器验收。
- r1 主旅程 result 与 driver 已读，23 项／10 样本／5.226 秒；独立匹配其 10 样本到原 HTTP request／response／metadata，现存 30 组三件摘要均核。完整标准导出候选经原导入，可信 fixture suite 完整双方评价与原 compare；用户理由明确采用到 revision 2，原 rollback 回原 head 到 revision 3，采用 evidence 为精确两 run；1440／960／390 的无页面横溢断言通过。此项只保留 r1 身份，未证明 R1／R2 已修或后继包旅程通过。
- 直接核自身原模板真实 Codex run `26ad0d387914472abbbc6837d76eafd9`／59.162 秒的原结果与 `review.md`；decision 为 request-changes，result SHA-256 `e89ae185f9e31eefeec905295c1fb64b370bde87f41970e28d2e32d6bb4b1e52`。9 份完整 packet 均与 r1 源码身份相同且实际存在于原 stdin，stdin 与冻结 prompt 逐字相同。结果和 R1／R2 的独立 caller 分析保留于 `independent/r1-journey-findings-audit.json`；自身模型审查不冒称新的独立审查。
- r1 `reentry-r1` 的 3 项实际反例和 driver 已读；其两个 sample 对象因两个等待器都匹配第二回包而重复同一 run，不能单靠 sample 声称两个 distinct run。已独立核原 HTTP 27／28 的两个不同 run `f20bd5c68d274ee1a82f25f5f775bd9b`／`4219503bd3fa49b8b95c09685381fa62`，以及原保存记录，确证发生了重复 evaluator 执行。r1 原 driver finally 的 socket 关闭后读取错误按实施者报告保留，未将补核当作原 finally 成功；`cleanup-finish-r1` 续核已读，并独立验全部原件、head revision 3、服务／浏览器 PID 不存在、58407 端口关闭。证明为 `r1-reentry-cleanup-audit.json`。

r2 独立证明 `r2-source-browser-audit.json` 已核：

- 全部 603 产品文件在工作树／构建源码／wheel／非 editable 安装逐字相同，611 文件／两 RECORD 611／616 全部有摘要项、283 冻结参考文件逐项验算；wheel SHA-256 `889f8b59eba6b4c7305d135869e6e170a5c82b36b31b1db5efec1cf8ffe465e8`；ES module 语法退出 0。r1／r2 全部 183 个 Python 源文件亦逐字相同，不将 r1 的 UI 运行结论沿用到 r2。
- r2 原 Web suite 完整 stdout／stderr 与终态：9 passed／11.73 秒，外层 13.244 秒，succeeded／exit 0。原 Skill suite 的 r1 35 项保持原运行身份；其 Python owner 与测试没有变更。
- r2 主旅程 23 项／10 样本／5.280 秒、生命周期 24 项／15 样本／6.696 秒，完整 driver 已读并匹配 25 样本到原 HTTP。该次中期证明核了当时的 54 组 HTTP 原三件摘要、8 个 held／released；最终 97 组见下。其中原 HTTP 46 保存真实完成 succeeded 的 run `ddc1349f6d544865a4413add9ab60daf`，fixture 只把其已完成回复替换为 503，后续原 dashboard 仍含该 run。用户解锁动作没有评价请求。r2 仍实际完成标准候选原导入／同 suite 双方完整评价／原 compare／明确理由采用 revision 2／原 rollback 回 baseline revision 3；三宽无横溢断言通过，视觉审阅与最终收尾另核。
- 修后自身原模板 Codex run `dfa7da6baa4b433c9d45842774bb860d`，59.561 秒，approve；原 result SHA-256 `4fb4f7f53aadf119ab2996787fc373f9bd58fba370cc8c898abc518adb4452b0`。9 文件 60,759B 与 r2 身份同一且实际完整进入原 stdin，3 份祖先／本叶 instructions／Skill 完整文本均逐项核在原 stdin 中；冻结 prompt 与 stdin 相同。模型结论与本独立审查分别记录。
- 已直接看 r2 主旅程 1440／960／390 三张原 PNG，主操作与窄屏换行可见，无新全页横溢；窄屏评价历史的局部表格允许横向滚动。图片摘要与尺寸保留于 `r2-visual-audit.json`，不扩大为回执／modal／unknown／GEPA 全部视觉状态。r2 首次 open 的 `ERR_CONNECTION_REFUSED`／exit 1 原件仍在，后续 driver 的实际 `page.goto` 成功与它分列。

最终本地终核证明为 `independent/final-local-audit-r2.json`，可复核脚本为同目录 `final-local-audit-r2.py`。独立执行仅离线读取原件、只读 SQLite 与进程／端口状态，未执行实施者 audit 脚本、重跑 evaluator／模型或新增安装：

- 完整证据索引的 649 个唯一原始引用全部重新读取，逐项字节数与 SHA-256 一致；索引本身的读取时摘要写入独立证明，独立目录不混入原始引用。当前产品仍为上列 r2 身份，固定基线至工作树的产品 diff 仍只有 `skills.js`；邻接原 owner／UI／state 与两份原测试均与基线及 r2 构建源码逐字相同。已读最终计划与交付，历史运行、夹具失败、最终本地结果和待发布／CI 分列。
- 最终 97 组 request／response／metadata 与完整 trace 逐项一致，10 个真实 held 均为 released，唯一 fixture 503 与原成功回复明确分开。主旅程／生命周期／负例共 68 项、46 样本，按确切 HTTP 编号逐一匹配完整原 body 及实际提交或 query；不是只核作者汇总的 passed。原错误返回、迟到回复与 finally 的界面断言以已读完整 driver 和对应原件为界。
- 最终负例／并发 driver 实际 21 项／21 样本／7.262 秒。另注册的可信 suite `e34f1ae3f8a842f6fc98a31cc1fea989c3232e401bec4b3661ed0ee6ba98dc6e` 有完整三 split 输入；原保存 stdin／stdout 确认 baseline 各 .5，REGRESS 为 .9／.9／.1 且正确性通过，原比较仅因 holdout 退化拒绝；INCORRECT 各 .9 但正确性失败，原比较仅因该项拒绝。错 suite／跨项目分别得到原 400。失败 scorer run `b0830ad99b55461fa95efe259aa042cd` 是原 HTTP 200 保存的 failed 记录，界面没有把它标为未知或给未知解锁动作，原 compare 不允许采用。首次负例缺 split 的 failed run `7a84ef19fd7c40cdb0e253394d8f68c9`、原 stderr 的 `KeyError: 'split'` 和失败 driver 保留；单独修正 scorer SHA-256 `8bdd530a3534e7a58ab194c0ec56b6c9cdd3ddaf6bb9553ed5a3b7fb91c1ac36`，没有改旧 scorer 或重写旧成功。
- 实际第二客户端采用将 revision 3→4，旧 UI revision 3 被原 CAS 拒绝，原 dashboard 及历史无额外变化；明确恢复至 5。eligible 后改变可信 scorer，实际 UI 采用被原 owner 拒绝，前后完整版本／head／历史相同。迟到 UI 采用真实到 6、切项目后的页面与 notice 保持；恢复至 7。迟到 UI 回退真实到 8、替换 Help 保持；恢复至 baseline 9。负例评价、第二客户端并发写与恢复中有直接原 HTTP；比较、失败评价及迟到采用／回退的界面行为走实际 UI，不称全部为鼠标操作。
- 原 CLI 共 11 次：prepare／check／export 三次、单独负例 suite 注册一次、最终 list／show／compare／完整 export 七次。逐个核 argv、退出与原 stdout／stderr 身份；完整 CLI 对象与原 HTTP、cleanup、只读原 SQLite 相同。七次读回包括精确 baseline／candidate／failed 原记录、完整 eligible compare；完整候选目录与原导出源逐文件／执行位相同。最终原 baseline head revision 9，5 个版本、9 条历史、3 个 suite、10 次评价；所有原 HTTP 评价对象与 DB 一一同一，所有 8 次成功 head mutation 与追加历史同一，另项目无版本／head／历史／suite／run。
- 原 source.zip／result／source／baseline／完整 input／candidate 的当前摘要或完整树独立重算，均与 before 和 cleanup 原件相同；原 scorer、单独负例 scorer、全部存储版本和可信文件身份也逐项核。正常 browser close 退出 0，服务 PID 2551959 与作者记录的 browser PID 2553498 当前均不存在；原 cleanup 报线程关闭，实际 60445 端口关闭。没有把 r1 补核当作其原 finally 成功。

本地需求与可维护性均 approve，开放 finding 各 0。home 更换未动态验证；整页 reload 不保留本窗口临时锁，多窗口也不共享，后续执行仍须核原记录；原 form 内防重复不等于跨窗口执行去重。GEPA 页面完整流程、全部故障排列、真实质量／性能收益、普通发布与本片自己的终态 CI 不在本次通过范围。
