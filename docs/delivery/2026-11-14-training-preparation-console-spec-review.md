# F9b4c C2 训练准备页面：独立需求评审

日期：2026-11-14。评审者：fresh-context 独立 agent `preparation_console_spec_review`。没有继承实现对话；先读仓库 `AGENTS.md`、maintainable-project-delivery 及 independent-review brief、[C2 原始验收](../plans/2026-11-14-training-preparation-console.md)，再读实际差异、原 owner 与相邻调用，最后核作者交付和私有原件。只读产品／测试／证据，仅写本文；未安装、运行 suite、操作浏览器／服务、访问远端、执行训练或修改业务仓库。

**最终本地结论：需求／正确性通过，首轮一项 P2 已修复并由 r2 实际浏览器原件关闭，开放 finding 0；所查维护性无独立阻断 finding。** 最终源码／包身份、实际页面及原件收尾、自身原模板均已补核；普通精确发布、完整 Ref 与本片自己的 CI 尚待。首轮 `request changes`、r1 旧包运行范围及两次生命周期验收脚本失败均按原范围保留，不追认为修后通过。

## 固定范围与身份

基线及当前 HEAD 均为 `92e7c24dbeb6847fe20c00e69c89c04b17702d5e`，分支 `refactor/architecture-foundations`，受评实现尚未提交。首次完整 `git status --short`、相对基线 tracked diff 与 `git ls-files --others --exclude-standard` 共核 12 个路径：

- C2 产品：`src/ergora/data/console/training-preparation.js`（新）、`src/ergora/data/console/training.js`。
- C2 文档：`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/architecture/current.md`、`docs/plans/2026-11-14-training-preparation-console.md`（新）、`docs/delivery/2026-11-14-training-preparation-console.md`（新）。
- C1 发布补记：`docs/delivery/2026-11-14-training-experiment-preparation-spec-review.md`、`docs/delivery/2026-11-14-training-experiment-preparation-structure-review.md`、`docs/delivery/2026-11-14-training-experiment-preparation.md`、`docs/delivery/evidence/2026-11-14-training-experiment-preparation.json`。已读完整 diff，仅补上一片固定发布／Ref 状态，不当作本片新产品或本片 CI 证据。

首轮受评两个产品文件的长度／SHA-256（最终 r2 身份见末节）：

|路径|字节|SHA-256|
|---|---:|---|
|`src/ergora/data/console/training-preparation.js`|7,076|`acebd4473903c1fe6ca3207e882cd40a545e4aad1b2fdd7781422fcd17c1a1de`|
|`src/ergora/data/console/training.js`|18,011|`fd116288aed7c25cdce430080ba7d003d23f40d376f43a86260615632b469abe`|

独立逐字比较确认 C1 `src/ergora/training.py`、`src/ergora/reference_training_preparation.py`、`src/ergora/web.py` 与基线相同。另查 `reference.py`、`reference_training_context.py`、`api.js`、`ui.js`、`state.js`、`app.js`、`style.css` 及原 preparation 测试／fixture，未把这些未改文件作为本片新增实现。

## 需求与维护性检查

**首轮 P2（最终 r2 已关闭）：显式无效窗口被当作省略，静默采用原默认窗口。** 位置：[training-preparation.js 第 93 行](../../src/ergora/data/console/training-preparation.js#L93)。真实浏览器中填入 `1e309` 后，HTML number input 的 `value` 为空，但 `validity.badInput === true`、`checkValidity() === false`。首轮第 95 行只比较空值，将其发成 `max_run_seconds: null`；实际 preview HTTP 200，服务使用原默认窗口。因此用户明确输入错误内容时仍得到可确认的默认窗口计划，违反明确窗口与省略必须可区分的合同。最小修复：在构造 payload／转换 Number 前复用现有 `duration.checkValidity()` 拒绝无效输入；真正留空仍允许 null，范围及完整原生关系继续由原 owner 验证。不要为此复制一套窗口 validator。原件 `browser-r1/window-probe.js / window-probe.stdout / window-probe.json` 已直接读取；stdout 为 866B、SHA `9653fb04886944a4179abbd89f47bf72e9bd8231c9901f982d3362b46f588b8b`，实际命令退出 0／3.3985 秒。该 r1 失败保留，不因后续修复追认为通过。

以下范围未发现其他需要产品修复的问题：

- 新模块有 `trainingView` 一个真实生产消费者。它内聚编辑、异步请求、确认与恢复的局部状态；原 `training.js` 仅接入面板并更新旧引导文案。复用 `api`、文本 DOM helpers 和原视图 `active`，没有复制三文件 publisher、native binding／字段验证、DB、调度、start 或批准算法。
- 完整 experiment JSON、项目 runner ID、可省略窗口一起交原 preview 应用入口。响应以完整文本保留 plan／request／sources／files、revision 和 SHA；准确粘贴 preview SHA 后才 POST prepare。完整 prepared 只有显式查看原件按钮，仍由原详情拥有 start／cancel。
- 按稳定实验 ID GET preparation，完整原 intent 与逐件文件状态可审。只有 `intent_saved / partially_prepared` 出现原 intent SHA 确认和显式 resume；`prepared / conflict / native_files_without_intent / not_recorded` 不生成补写／接管按钮。revision 来自本次原观察，没有用浏览器重建恢复计划。
- draft、runner、窗口和恢复 ID 的实际编辑均增加同一 sequence 并清空旧结果。每条 preview／read／prepare／resume 的成功与异常 UI 分支都受当前 sequence 和原 `trainingView` 的 project／home／tab／DOM 有效性约束，成功后的列表刷新也只在有效分支发生。原 `app.js` 切 tab／project 会替换旧 DOM；旧 panel 的 finally 只解锁自身控件。
- mutation 在首次 await 前设置 sending 并禁用该面板所有 button／input／textarea；确认回调同时检查 current 与 sending。失联分支保留捕获原 ID 的 GET 按钮与“可能部分或全部发布”文案，没有自动重发、换 ID、start、执行或批准。read／preview 可相互替代，但迟到响应不能恢复旧确认。
- 非 Linux 面板显示 Linux／WSL2 支持范围，与未改 C1 的所有 preparation operation Linux 门禁一致；原 SDK-free status 合同未被本片改变。复用原 CSS 的 `min-width: 0`、`overflow-wrap` 与窄屏单列只能支持静态判断，不能替代三视口实际验收。

## 首轮已直接核对的实际证据

私有原件根为 `.ergora/checks/training-preparation-console/`。本轴亲自读取脚本、原结果与日志，独立复算包／RECORD／冻结身份，没有重跑作者命令。

1. `install-r1/setup.json` 记录 noneditable wheel 构建、独立 venv 及安装均退出 0。wheel SHA 为 `16c012ac072580e4d7e813ce3aaba9ec2228c56fdc218120a216b22171671369`。亲自读取 wheel 全部 580 件，572 产品与当前源码、构建快照、实际 site-packages 逐字相等；路径集合也相等。wheel RECORD 580 行／579 哈希项、安装 RECORD 585 行／584 哈希项，全部长度／SHA 独立核对相符；283 冻结原件逐件匹配 manifest。
2. `install-r1/regression-r1/result.json` 的实际 argv 是安装环境 `python -I -m pytest`，只运行 `test_training_preparation.py / test_web.py / test_architecture_boundaries.py`。原 stdout 收集并执行 **38 passed / 84.27s**，monitor 86.037s、returncode 0，stderr 空。原测试确实包含 intent／global manifest／project manifest／spec 四写后中断、相同 prepare 只读、准确 SHA 恢复、已有 start／fence／job 拒绝及实际成功后丢回复 GET；这些是 C1 owner 受影响检查，不能代替新页面交互。
3. `native-r1.py` 在真正原 `core.write` 返回后 `os._exit(73)`，实际安装应用入口返回失败，再按原 ID GET。原 `result.json` 记 `partial-browser` 边界 1、`resume-loss-browser` 边界 0、`resume-slow-browser` 边界 2 及冲突准备前的边界 0，分别产生 partial／intent_saved 事实。亲读 intent／原件、15 项 protected-before 及脚本；15 原配置／baseline 的 SHA 全部保持，runner marker 不存在。浏览器正在消费这些 fixture，后续当前文件可由 missing 变 matching，不能用该时点当前目录反推此前未中断。
4. 已读真服务包装器、Chromium 配置和实际 open 回执。open 退出 0 只证明浏览器已打开；截至本节核查，没有完整行为／三视口／收尾成功主张。

关键原件的本次独立复算身份：

|原件（相对私有根）|字节|SHA-256|
|---|---:|---|
|`install-r1/package-identity.json`|499|`1a7f467e4495536021ed643080ccfca27e4791f77fb92f1220b0538306fa6227`|
|`install-r1/source-manifest.json`|1,655|`2cf4d20fa71ff07a13580244ce30553cd9b10341fa0cc320bdcfd10ebf511fb1`|
|`install-r1/regression-r1/result.json`|732|`7abbdffbcda9dbc812a7eb6b6692a5b34a920087735c0281f3bb27808ac7196e`|
|`install-r1/regression-r1/process/stdout.txt`|7,220|`0438759bd97f9939d05fb12f2fc22046ce1833646a463b781cd2ad26ab26441c`|
|`native-r1.py`|5,994|`d04662976e8e2fceca2851f193b1bc90c76bb3675911bcac2c44232c4c3fa077`|
|`native-r1/result.json`|1,269|`b5f651324bb57b44afdac9f4fe061c972db47f4a182fcc3fcf4367b700a843b9`|

完整 tracked `git diff --check` 退出 0。本轴只执行只读文本／Git／JSON／SHA／zip／CSV 核查，未执行新业务操作。

## 首轮时点待验范围

尚待直接核 C2 实际浏览器的完整 draft→preview→错误 SHA 零 POST→双击一次 prepare→三原文件匹配，显式部分恢复、丢实际成功回复后的原 ID GET，以及编辑和切 project 对迟到 preview／read／publish／resume 的隔离；三视口截图与横向溢出、原 baseline／runner 表单／详情回归也待。最终原件／无 job、fence、start、批准或 runner 命令，browser 关闭、原 monitor 停服务组及端口不监听、自身原结构模板实际输入／回复、新独立结构轴和最终文档状态随后补核。普通提交／推送、精确 Ref 和本片自己的 CI 仍另有必要验收。

该时点开放一项 P2，需求结论为 `request changes`；缺失的实际验收证据未视为通过。此片只交付本地精确准备 UI，不证明原生 Windows、Temporal 服务、真实训练／GPU、质量／性能、evidence 批准／采用、F9d 或 B3 完成。

## 同片最终 r2 需求与原件补核

本轮沿同一片／同一 reviewer 只读复核修后产品及全部实际证据，仅更新本文；没有安装、重跑 suite、操作浏览器／服务或发出远端请求。HEAD／基线仍为 `92e7c24dbeb6847fe20c00e69c89c04b17702d5e`。本轮末次完整 tracked／untracked 清单为 16 个路径：原 12 个加本片两份独立评审、`docs/delivery/evidence/2026-11-14-training-preparation-console.json` 和 C1 计划 `docs/plans/2026-11-14-training-experiment-preparation.md` 的原 CI 终态补记；该补记完整 diff 已核，继续属于上一片，未用它关闭 C2。产品仍只有原两个路径，C1 三产品文件再次逐字核为未改。

最终 `training-preparation.js` 为 **7,195B**、SHA **`6b8fae9d4008a7d9dca874efe3e116d09df98915fe761d2b4b5d8fe7b89097fc`**；`training.js` 仍为前表 18,011B／`fd116288…`。两路径按路径、NUL、原字节、NUL 重算组合 SHA 为 **`893a738a2a33ac3767be11e983afc7ee952ddb00a6fb595daea2fa6cd8b20ff5`**。新增第 93 行在 Number 转换前调用 HTML `checkValidity()`；未引入第二份 native validator。r2 `basic.js` 真实填入 `1e309`，等到原错误提示并核 preview 请求计数为 0；再真正留空，原 200 计划的 `request.max_run_seconds` 为 null。**首轮 P2 修复及实际行为复核关闭。**

直接从最终 noneditable wheel 读取 **580 件／572 产品**，逐字对照当前完整源码集合、构建快照和实际安装，全部一致；两 RECORD 的 580／585 行全部哈希与长度相符，283 冻结原件全部匹配。最终 wheel SHA 为 **`21e106dc2a3cd264fbd309ddf32afe2a66002930b64713e7315eb0c05f237c75`**，`product-current-r2.json` 与 `syntax-final.json` 也直接读取且身份相符。38 项 Python 运行仍只属于首轮 r1 包；没有称修后 r2 重跑 Python，也没有称执行全库检查。

### 实际浏览器行为与脚本失败边界

亲自读取 `browser-r2/basic.js / lifecycle-r3.js / visual.js`、各实际 stdout 和命令回执；每份完整脚本均逐字存在其执行 stdout 中，三个实际结果均 `passed`，命令退出 0，分别 11.392／19.558／2.936 秒。不是只接受 `*-result.json` 或公开 summary：

- `basic` 由完整 draft／项目 runner／300 秒窗口取得原计划，错误 preview SHA 零 prepare POST；正确 SHA 后同步双击只 1 次 prepare，实际返回同 SHA 的 prepared，详情的 `job_request` 为 null。原部分记录实际仅全局 manifest 匹配，再错误 intent SHA 零 resume POST、正确 SHA 双击只 1 次 resume，补齐原三件且 intent SHA 保持。conflict／外项目 orphan 没有恢复按钮，原外项目私有字符串没有被返回。原 baseline／runner 表单实际预览分别为 already_initialized／already_registered，原详情读取正常；没有把这些只读回归称为重跑初始化／登记／start／cancel。
- `lifecycle-r3` 通过 `route.fetch()` 取得真实服务响应后才 hold／abort：旧 preview 与新 preview 反序到达，以及编辑恢复 ID 后旧 GET 到达，均不覆盖当前面板；真实 preview、read、prepare、resume 各在切 project 后迟到，均不污染新视图。prepare 在途输入确实 disabled。原 intent-only 与两 manifest 的部分状态均显式恢复，准确原 SHA 保持。
- 丢回复不是合成错误响应：原 prepare／resume 实际 200 后由浏览器 abort，页面随后只 GET 原 ID；返回 JSON 与被丢真实成功结果相同。亲查真服务 165 行捕获记录：丢 prepare 成功与随后 `loss-browser-v2/preparation` 都为 12,493B／SHA `f8bdb85ecb77baa05bac979d2b4f944e8a9b448669fa534128d9d634b25f1ab2`；丢 resume 与随后原 GET 都为 12,584B／SHA `671d46946d1e3df2d0d6a68ea3d62d0a44a5f4fb825e43f4ba9fd0bceb6e73d1`。第三轮整组 prepare／resume 各 2 次（各含一项丢回复、一项切项目迟到），无自动重发或换 ID。
- `visual` 展开完整原意图与输入后，1440／960／390 的 document scrollWidth 均等 innerWidth；另有 basic 三视口。实际查看 desktop／mobile panel 顶部与 960 完整 panel 截图，输入、完整 SHA、原意图文本和按钮可见且换行，未见横向溢出。

前两次原 `lifecycle.stdout` 的 30 秒 detached DOM timeout、`lifecycle-r2.stdout` 的 `Route is already handled` 均仍保留，不能称通过。已读三份脚本差异：第一轮无条件重选相同 project 触发全页 refresh，旧 DOM 被替换；第二轮在 handler 尚未完成时撤销拦截。第三轮跳过相同项目重选、只 hold 首请求并等 handler done 后 unroute，使用额外新稳定 ID。`additional-interruptions-r1.py` 与其实际 JSON 显示新 intent-only／两 manifest 状态仍由原 write 返回后 `os._exit(73)` 产生；未删除重写前两轮已经发布的原件，也没有为脚本失败改产品。实际 home／tab 切换未另作四操作浏览器交错，依靠前述原 active／DOM 静态路径核对；不冒称这些场景有独立运行记录。

### 原件、收尾及自身模板

亲自独立重算 `native-r2/protected-before.json` 的 **15** 项与 `prepared-before.json` 的 **18** 项，全部当前原字节 SHA 保持；这些清单有重叠，不声称是 33 件互不相交文件。最终十个已准备实验逐件核三份原文件等其完整冻结 intent，manifest 文件 SHA 与 spec binding 相同，URI 指向登记的原 manifest；final-observations 的每个文件摘要也独立相符。两个 preview-only ID 无意图／全局 manifest，conflict／orphan 原文件保持且无接管；没有 job、fence、training-submissions、approval、integration-ticket 或 runner marker。验收 Git repo 的实际 status 为空。

亲读原 web 监控脚本（监督原服务组并观察 stop）、cleanup 结果 cancelled／-9、浏览器实际 close 回执退出 0 及 closed 输出；原服务日志为空且本次只读 socket 观察原端口也不监听。console 原输出恰两项 ERR_FAILED，只对应第三轮刻意丢弃的真实 prepare／resume 回复，没有其他 browser error 主张。

自身原结构模板实际 run 为 Codex 授权回退、text-only、42.947 秒 approve，不能作为异后端成功或新的独立评审。本轴直接从实际 stdin 按索引提取十份完整文件 **107,163B**，各 SHA 全匹配；实际 stdin 与冻结 prompt 全字节相同，111,939B／SHA `27a640ff9cdb00602ea800df847998893fe1a57ea7b2d41735bc4936e8eeccce`。父 instructions、叶 instructions 与 Skill 原文的 SHA 及实际 stdin 包含关系全部核到，原结果 671B／SHA `c871b112fb6f5af127ef6d5365cbf629bf46195527d2e04e60f4225ae5cbaa49`，明确保留模型未运行浏览器／独立核安装的限制。

补核时公开证据 10,991B、SHA `73eaca9cfbf7597d9f328799de7f558610eb7e6b240a9fbdb2ae10679c6cc43d`，其 **42** 份私有引用长度／SHA 全部独立复算相符；随后评审状态补记不构成重测。关键修后原件：

|原件（相对私有根）|字节|SHA-256|
|---|---:|---|
|`install-r2/package-identity.json`|499|`9586f3ebc8d1e510b1a653a07d476db2a6435df9243c777014ce1128a19bc8eb`|
|`browser-r2/basic.stdout`|11,444|`7a50a37cdc60a0f9c9295f0e5f15a81f4114a3e3c510ebbfb366f4bbb605313d`|
|`browser-r2/lifecycle-r3.stdout`|15,171|`7af4634d5fae015e8313c9e64d89c29d3474919e144c228be7aeee17e6709878`|
|`browser-r2/visual.stdout`|5,712|`6573f1ea481ef5a65e4c3dbcbbffe5f71e0bb1c7a7375a05112207df9beddee4`|
|`final-observations.json`|3,598|`f565eb3e7ec3ce35588ab592280fa53302d52ae2102c424753055a3d2b22e07b`|

完整 tracked whitespace、六份 untracked 的 no-index whitespace 及末次 16 个改动路径文档的 217 个本地链接均检查，无诊断／缺失链接。最终需求／正确性本地通过，首轮 P2 已关闭，开放 0；所查维护性无新增 finding。普通提交／推送、完整 Ref 与 C2 自己的 CI 仍待，不能借 C1 成功关闭。Linux／WSL2 本地 CPU 文件与页面合同以外，原生 Windows、Temporal 服务、真实训练／GPU、质量／性能、evidence 批准与采用、F9d／B3 仍未验。
