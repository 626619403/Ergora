# F9b4c C2 训练准备页面：独立结构评审

日期：2026-11-14。评审者：fresh-context 独立结构轴代理 `/root/preparation_console_structure_review`。未继承实现对话；先读原要求、`AGENTS.md`、`maintainable-project-delivery` 及其 independent-review brief、`codebase-design`，再审源码、相邻调用者和原始验证记录。本轴只写本报告，未编辑产品、测试、计划、原件或其他报告，未安装、重跑昂贵检查或操作远端。

## 结论

最终本地结构复核通过；在本轴所查需求范围内实现与最终证据一致，开放阻塞 finding 为 0，非阻塞 finding 为 0。需求轴首轮窗口 `badInput` P2 已经最小修复并由 r2 实际浏览器补验关闭。最终 r2 包、basic／第三轮 lifecycle／visual、原文件和收尾、Ergora 自身原模板调用均已独立补核；固定候选 `2181cc5c6ab92ac01664f8e769298cce350f65a5` 的 16 blob／正式普通发布及原完整远端 Ref 通过。本片自己的 CI `43530156938` 已由本轴直接核原 run／八 job HTML、收据、固定 workflow／分组及 30 个必要步骤终态，Success；本结构轴的实现、发布身份和 CI 验收已收口。

最终两产品路径组合 SHA256 为 `893a738a2a33ac3767be11e983afc7ee952ddb00a6fb595daea2fa6cd8b20ff5`。本轴未新增产品 finding；前两轮 lifecycle 的真实脚本失败及已发布原件保持，未把失败改写为成功。最终裁定与证据详见本文末节；此前“待验”均为当轮历史状态。

新 `training-preparation.js` 虽只有一个生产消费者，但拥有完整、内聚的局部页面算法：编辑失效、预览确认、原 ID 读取、按原意图恢复、mutation 防重入和失联后的读取入口。将其并回 `training.js` 会把这些状态与原 baseline／runner／列表／详情／提交／取消代码混在同一个 owner 中；独立文件有具体 locality 理由。当前 interface 仅接原路径、有效性、列表刷新、详情读取和平台；没有 registry、插件接口、可互换 adapter、第二业务状态或假想复用。

## 检查身份与变更范围

基线与初检时 `HEAD` 均为 `92e7c24dbeb6847fe20c00e69c89c04b17702d5e`，分支 `refactor/architecture-foundations`；初检对象为其未提交工作树，后续固定候选核验见末节。独立执行 `git status --short`、相对基线的 diff／文件清单和 `git ls-files --others --exclude-standard`，初检范围如下：

|类型|文件|
|---|---|
|C2 tracked 产品|`src/ergora/data/console/training.js`|
|C2 untracked 产品|`src/ergora/data/console/training-preparation.js`|
|C2 tracked 使用／状态文档|`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/architecture/current.md`|
|C2 untracked 计划／交付|`docs/plans/2026-11-14-training-preparation-console.md`、`docs/delivery/2026-11-14-training-preparation-console.md`|
|旧 C1 发布记账|`docs/delivery/2026-11-14-training-experiment-preparation-spec-review.md`、`docs/delivery/2026-11-14-training-experiment-preparation-structure-review.md`、`docs/delivery/2026-11-14-training-experiment-preparation.md`、`docs/delivery/evidence/2026-11-14-training-experiment-preparation.json`|

最终补核时新增 untracked 的需求／本结构报告与 `docs/delivery/evidence/2026-11-14-training-preparation-console.json`，均为本片评审／证据记账；两件产品保持修后身份，没有新增 Python、测试或 CI 变更。

旧 C1 四件仅按上一片记账识别，不把其历史通过当成本片 UI 验证。`training.py`、`reference_training_preparation.py`、`web.py`、共享 `api.js / ui.js / state.js` 及冻结参考相对基线均无修改。

首轮两件产品的 SHA256：

|文件|SHA256|
|---|---|
|`training-preparation.js`|`acebd4473903c1fe6ca3207e882cd40a545e4aad1b2fdd7781422fcd17c1a1de`|
|`training.js`|`fd116288aed7c25cdce430080ba7d003d23f40d376f43a86260615632b469abe`|

## 调用链、所有权与 guard

实读 `training-preparation.js` 全文、`training.js` 及其 diff、共享 `api.js / ui.js / state.js`、`app.js` 的刷新／渲染／项目与 tab 路径、`training.py` 的四个准备入口及 `_setup`、`reference_training_preparation.py` 全文、`web.py` 的 payload／四路由，以及相关现有 preparation／architecture 测试和安装输出。

|位置|真实调用／可达场景|评审判断|
|---|---|---|
|`training.js:95` → `trainingPreparationPanel`|唯一不同生产文件调用者；传入原 `active / load / inspect`|已有 owner 保留列表刷新和详情读取，面板不复制职责。五个参数均有真实用途，没有为单消费者添加配置框架。|
|`training-preparation.js:5`|服务端 bootstrap 平台不是 `linux`|明确解释 Linux／WSL2 执行范围；没有隐式尝试 unsupported 发布。|
|`:10–16` 的 `changed`|draft／runner／窗口／恢复 ID 的用户输入变化|同一 `sequence` 失效旧预览及在途读取并清除旧确认；不另建前端业务状态。|
|`:24` 的 `current`；`training.js:27` 的 `active`|请求返回前发生输入变化、切项目、换 home、切 tab 或 DOM 被替换|复用原 home／project／tab／`isConnected`，同时检查请求序列。旧闭包即使仍有回复也不能更新新视图或触发列表／详情动作。|
|`:25–28` 的 `setSending`；`:50 / :58 / :91 / :112`|prepare／resume 未返回时双击，或试图启动另一面板动作|mutation 进入 `await api` 前同步设 `sending` 并禁用面板按钮／输入；回调 guard 也处理已排队事件。局部禁控不侵入原 baseline／runner／提交／取消。|
|`:30` 的 `show`|read／preview 原已有意图／publish 返回原状态|统一呈现原 intent、逐件状态和 SHA。只给 `intent_saved / partially_prepared` 恢复动作；`conflict / native_files_without_intent` 不显示接管动作。状态判断用于呈现，不重写 native validator。|
|`:36–39`|返回 `prepared`|显示“文件一致”限制并通过原 `inspect` 读取；未 start、未查询训练、未批准。|
|`:46–54`|操作者显式确认恢复|完整 intent SHA 严格相等后，POST 仅带服务端原 revision／intent SHA；没有从当前 draft 重造恢复意图。|
|`:57–70` 的 `read`|按稳定 ID 初次读取或失败后重新读取|沿原 GET 入口；空 ID 在使用处给错误，迟到成功／失败均经过 `current`。没有自动重发 mutation。|
|`:72–88` 的 `publish`|prepare 或 resume 成功／网络失败／丢实际回执|两条 mutation 共用一个局部发送算法；异常不假定零写入，保留原 ID 的 GET 按钮与明确说明。`finally` 释放禁控；失效视图不执行 `show / prepared`。|
|`:90–119` 的 `preview`|完整 draft、runner ID 和可选窗口预览|完整 request 交原 POST 入口；全量 `pre(observed)` 含原 plan、sources、manifest／spec。已有准备记录转入同一原记录显示，不绕过原 intent 另发布。|
|`:105–116`|预览后确认准备|显示服务端 revision 和完整 SHA；错误 SHA 在客户端阻断 POST，正确 SHA 连同原 payload／revision 发送。输入修改使对应 request 失效。|
|`ui.js:5–49`、`api.js`|原意图／JSON／服务端错误进入 DOM 与网络|复用文本节点及 JSON 呈现、现有 GET／POST 和错误传播；未拼接来源 HTML，未引入额外网络 owner。|

新文件的 `changed / current / setSending / show / read / publish / preview` 均为该算法私有函数；其内部多个调用点不是第二个生产消费者，也无需以复用配额证明独立导出价值。`publish` 隐藏了两条 mutation 共同的禁控、失联与迟到回执处理；`show` 隐藏了原状态的统一呈现，均非仅改名转发的浅层包装。没有发现不可达 guard、重复 native binding／字段 validator、泛化插件或新增 tests／CI。

原 baseline／runner setup、列表分页、详情、start／resume-start、cancel／resume-cancel 的实现未改；新面板成功后仅调用原 `load`，查看原件仅调用原 `inspect`。`training.py:152–161` 继续拥有 revision 预留，原 `reference_training_preparation.py` 继续拥有身份、source、三目标、冲突和 unstarted 检查；浏览器没有搬运这些规则。

## 实读与独立复核的证据

证据根目录：`.ergora/checks/training-preparation-console/`，属于本地验收原件；以下不将 CPU 文件合同称为训练或 GPU 成果。

- 本轴直接执行两个产品文件的 `node --input-type=module --check`，均退出 0；相对基线 `git diff --check` 退出 0。
- 实读 `install-r1/setup.json`、package／source manifest、构建与安装脚本、`regression-r1/result.json` 和原 `process/stdout.txt / stderr.txt`。原安装环境 Python 3.11.15／pytest 9.2.0；`-I -m pytest` 对 `test_training_preparation.py / test_web.py / test_architecture_boundaries.py` 为 38 passed／84.27 秒，process monitor 86.037 秒、returncode 0。没有重新运行这批检查；它们不覆盖真实浏览器 DOM 交互。
- 本轴以只读标准库脚本重新遍历 wheel 的全部 572 个产品文件，对照当前 `src`、构建树 `source/src` 和 noneditable `site-packages`，逐字一致；独立重算 wheel／installed 两份 RECORD 的摘要和大小，580／585 行均匹配；当前与安装树的 283 份冻结参考逐件匹配 manifest。
- wheel SHA256 为 `16c012ac072580e4d7e813ce3aaba9ec2228c56fdc218120a216b22171671369`；没有把文档后来更新误称为产品不一致。
- 实读 `native-r1.py`、`native-r1/result.json`、protected／prepared 原始摘要和磁盘 intent／三目标。脚本在原 `core.write` 真正返回后执行 `os._exit(73)`，实际生成 intent-only、global-only 和 global＋project 两种部分发布；记录没有把模拟返回值当写入。安装 38 项还保留了四个原写入边界的真实中断检查。
- 本轴重算 15 份原 config／baseline 的 protected 摘要，均保持；`must-not-execute` 不存在。核验当时 native 目录无 job／fence／submission／approval 文件。浏览器进行中可以新增或补齐准备文件，这不是最终收尾核验。
- 实读 `browser-r1/service.py / endpoint.json / browser.json` 与 open／tab／snapshot 记录：真实本地服务和 Chromium 已打开。没有最终 browser result 时不把打开页面、初始截图或原部分文件当作全部交互验收通过。

README、TRAINING 和 architecture 的改动准确描述准备／恢复入口与原 owner，未宣称训练成功。初读时 C2 计划末段仍保留静态／安装尚待，已向实现者指出；复读 `docs/plans/2026-11-14-training-preparation-console.md:21` 已同步 JS／572／两 RECORD／283／安装 38 项和浏览器在途状态，此记账问题已消除，不保留开放 finding。

## 初轮待验清单（历史）

继续沿原 C2 计划验证：真实浏览器完整 draft→preview→错误 SHA 零 POST→双击一次 prepare；原部分 intent 显式 resume；真实成功回复丢失后的原 ID GET；编辑、项目切换及其他页面生命周期的迟到 preview／read／publish／resume；1440／960／390 视口与实际截图；原 baseline／runner／详情不受破坏。最终再核原件、无训练副作用、原 monitor 停服务进程组、browser 关闭及端口不监听，补 Ergora 自身模板原回复、最终源码身份／普通发布／本片 CI。本轮未验上述尾项，不能据此报告 C2 精确交付完成。

## 同片 P2 与最小修复复核

需求轴发现的 P2：首轮 `training-preparation.js:95` 使用 `duration.value === "" ? null : Number(duration.value)`。真实浏览器输入 `1e309` 后 `value` 已是空串，但 `checkValidity() === false` 且 `validity.badInput === true`；首轮会 POST `max_run_seconds: null` 并获得 HTTP 200，把用户显式输入误当省略。位置与原始行为已通过 `browser-r1/window-probe.js / window-probe.stdout / window-probe.json` 独立实读确认；这是转换前丢失信息，不能只靠服务端窗口 validator 拒绝。

修复仅在 `preview` 转换输入之前调用原 HTML `duration.checkValidity()`（当前 `training-preparation.js:93`），非法输入先显示错误；合法空值仍按原合同传 `null`。本轴以构建 r1 原件和当前文件的 diff 确认只有这一行产品变化；此检查有真实可达失败且属于页面外部输入，不是把 native validator 搬浏览器，没有新增抽象或测试框架。源码修复通过结构复核，JS 语法和 whitespace 重新检查均通过。当前 preparation SHA256 为 `6b8fae9d4008a7d9dca874efe3e116d09df98915fe761d2b4b5d8fe7b89097fc`，`training.js` SHA256 保持首轮身份。

实读 r1 `basic.js / basic.stdout / basic.json`：旧包基本交互通过，错误两种 SHA 均零 POST、双击 prepare／resume 各一次、实际 global-only partial 同 SHA 补齐、conflict／orphan 不接管、原 baseline／runner 和详情正常，1440／960／390 的测量宽度无溢出；已有截图路径。`cleanup.json` 记录原 monitor cancelled／-9，`close.json` 退出 0。此处只确认已读脚本和记录，没有把旧包基本交互或截图路径继承为修后完整验收，也未用它替代实际查看截图及端口收尾。r2 源码包与 actual basic／lifecycle 记录待就绪后继续同片复核。

修后 r2 包已单独只读复核：wheel SHA256 `21e106dc2a3cd264fbd309ddf32afe2a66002930b64713e7315eb0c05f237c75`；遍历当前源码／构建树／wheel／noneditable 安装树的 572 个产品文件逐字一致，两 RECORD 580／585 行的摘要与大小全部匹配，当前与安装树的 283 份冻结参考逐件匹配；native-r2 的 15 份 protected 原件保持、runner marker 不存在。产品身份采用修后 `6b8fae… / fd1162…`，未沿用旧包身份。已实读 r2 basic／lifecycle 脚本，包含 badInput 零 POST、合法空默认、原部分三边界、真实服务先成功写入再丢回执，以及真实响应延迟后编辑／换项目；运行输出、截图实看和最终收尾尚待，脚本本身不计运行通过。

## 最终本地证据补核

本节取代前文当轮待验状态。实读最终产品文件摘要，独立按 `路径 + NUL + 文件原字节 + NUL` 重算两件产品组合 SHA，得到 `893a738a2a33ac3767be11e983afc7ee952ddb00a6fb595daea2fa6cd8b20ff5`，与已逐字核验的 r2 源码／快照／wheel／安装身份一致；修复后无其他产品变化。r1 的三 suite 38 项仍严格属于 r1 安装包，未称 r2 又跑 Python 检查。

本轴读实际脚本、`stdout` 内的结果与原错误、CLI 记录、真实服务 `requests.jsonl` 和磁盘事实，不仅检查派生 summary 的布尔值：

|最终原件|独立确认的行为与范围|
|---|---|
|`browser-r2/basic.js / basic.stdout / basic.json`|11.392 秒，实际修后 `1e309` 显示错误且无 preview 请求；真正空值的原计划 request 保留 `null`。错误 preview SHA／intent SHA 各零 mutation；同步连续点击 prepare／resume 各只发 1 POST，返回同 intent 的 `prepared`。global-only 原部分文件通过显式恢复补齐；冲突／无 intent 原件没有恢复按钮，orphan 原私有内容未泄露。原 baseline／runner 预览和实验详情仍正常。|
|`browser-r2/lifecycle-r3.js / lifecycle-r3.stdout / lifecycle-r3.json`|19.558 秒。两次真实 preview 在编辑后反序返回，保留新结果；编辑恢复 ID 使旧真实 GET 失效。preview／read／prepare／resume 的真实回执在切到另一项目后分别迟到，均不污染新视图。prepare 期间原 draft 与恢复 ID 控制禁用。|
|同一第三轮的 `route.fetch / route.abort` 与原服务日志|prepare／resume 均先取得真实 HTTP 200 和完整服务端结果，再刻意 abort 给浏览器；不是以伪造结果代替实际发布。只点击原 ID GET 恢复，JSON 与已丢真实结果完全相等、intent SHA 保持；整组 prepare／resume 各 2 POST，包含各自另一个延迟项目切换场景，没有自动重发。服务端对应 POST→GET 摘要分别同为 `f8bdb85e… / 671d4694…`，与脚本全 JSON 比较相互支持。|
|`native-r2/result.json`、`additional-interruptions-r1.py / .json` 与恢复脚本|原 `core.write` 返回后 `os._exit(73)` 的真实 intent-only、global-only、global＋project 三个部分边界通过页面显式恢复。新增稳定 ID 的 intent-only／two-manifest 检查均先 GET 原状态与 SHA 后再恢复；不改旧原件、不重新定义业务恢复算法。四个原发布写入边界的完整原 owner 回归仍仅采用 r1 安装测试原范围。|
|`browser-r2/visual.js / visual.stdout / visual.json` 与截图|2.936 秒；完整 draft／runner／窗口与展开原意图在 1440／960／390 均测得 `scrollWidth === innerWidth`。本轴实际查看原有 desktop／mobile preparation panel 顶部截图及 960 页面顶部截图，完整 SHA／ID 与 JSON 以文本换行、控制可见；未据截图主张训练执行或完整内容阅读成功。|

前两轮 lifecycle 不计 pass：

1. `lifecycle.stdout` 原样为 `locator.click` 超时、元素 detached；首轮脚本在已选项目再次 `selectOption`，原 app 的 change 路径触发 refresh／DOM 替换，但脚本未等完成。对比后续脚本确认仅在验收脚本跳过无意义重选。
2. `lifecycle-r2.stdout` 原样为 `route.fulfill: Route is already handled!`。对比第三轮脚本，hold 改成只拦首个请求、等待 handler `done` 后再 `unroute`；保留原输出及已经成功发布的实验。第三轮采用额外新稳定 ID、真实原写入中断和新浏览器会话，未清理／覆盖已发布文件来重复同 ID 场景。CLI wrapper 的退出 0 不能把含 `### Error` 的旧 stdout 当作产品通过。

本轴另外执行只读核验，未运行会重写结果的 `final-observations.py`：

- 独立重算 native-r2 的 `protected-before.json` 15 项与 `prepared-before.json` 18 项，全部与当前字节一致。逐件读取 `final-observations.json` 列出的十个实验的 intent 和三个目标，30 件原字节均等原 intent；各 spec 的 `manifest_uri` 等实际绝对原 manifest URI，`binding.manifest_sha` 等原 manifest 字节摘要，intent 文件摘要也匹配最终记录。
- 两个 preview-only ID 没有 intent／manifest 发布；orphan 没有意图、conflict 没有新 spec，原冲突／孤立文件摘要由上述 18 项保持支持。runtime 下 job／fence／approval／integration-ticket／submission 目录不存在，runner marker 不存在；验收专用业务 Git 仓库的 `status --porcelain` 为空。没有把 Ergora 当前工作树的合法未提交变更称为 Git clean。
- 原服务日志的十次 mutation 均为实际 HTTP 200；失败脚本已发布的实验同样保留在十个完整记录中。最终 console 原件恰两条 `ERR_FAILED`，路径分别对应第三轮刻意丢弃的 prepare／resume，没有其他最终会话错误。前会话脚本失败另行保留。
- 实读 `close-final.stdout / .json`，原 browser 关闭且命令退出 0；实读 `web-r2.py` 的原 `processes.run(supervised=True)` 与 `cleanup.json` 的 cancelled／-9。补核时实际原端口连接返回 111，未发现该服务命令遗留进程。浏览器关闭采用原 CLI 回执，不额外启动浏览器确认。
- 独立重算公开 JSON 所引用 42 份私有原件的大小和 SHA256，全部匹配，没有只信引用表中的布尔状态。

Ergora 自身原结构模板也已补核：实读 actual native run、packet index、原结果及 prepared composition。十份完整文件共 107,163B 逐份存在于实际 stdin 且大小／摘要匹配，八份源码上下文等当前字节；prepared prompt 与原 `stdin.txt` 111,939B 逐字相同，三份祖先／叶 instructions／Skill 资源均实在 prompt 中。42.947 秒成功，原结果 SHA256 为 `c871b112fb6f5af127ef6d5365cbf629bf46195527d2e04e60f4225ae5cbaa49`，决策 approve；原请求 claude-code、实际 binding codex 及用户授权 fallback 原因均保留。这是自身模板验收，不取代本轴独立评审，也不称异后端成功。

最终维护性结论维持通过。新增 `checkValidity` 的实际可达失败与最小位置有充分证据；其余 ownership／interface／私有算法／guard 判断保持，无需再加产品 guard、测试镜像或插件抽象。README／TRAINING／architecture 与本地实现一致，PLAN／delivery 和公开证据已保留产品 P2、两次脚本失败、最终通过及发布在途的范围。

开放项仅为正常发布流程的普通提交／推送、精确远端 Ref 和本片自己的 CI，以及另一独立需求轴的最终记录；本轴没有开放产品 finding。没有单独实跑每一个 home／tab／非 Linux 条件，相关结论限源码 guard 检查；真实项目切换覆盖了原 DOM 替换路径。没有服务端训练调度、真实 GPU／质量／性能验收、evidence 批准或采用主张；这些仍归后续原计划。

## 固定正式发布身份补核

本节将上一节“普通发布／精确 Ref 待”关闭，CI 继续独立在途。只读核验固定 Git 对象 `2181cc5c6ab92ac01664f8e769298cce350f65a5`，没有运行远端命令、安装或重测；后续活动工作树／F9c 不替代本候选。

- `git rev-list --parents -n 1` 确认候选只有一个父提交，恰为 `92e7c24dbeb6847fe20c00e69c89c04b17702d5e`；提交题为 `feat: expose exact experiment preparation and recovery in console`。
- `git diff-tree` 的固定 16 路径集合与原 `static-final-r1.json.files` 完全相等。对每一路径直接 `git show 候选:路径` 取得固定 blob 原字节，逐件重算大小与 SHA256，16／16 与原清单匹配；不是对当前工作树做等价替代。固定候选 `git diff --check` 无诊断。
- 16 件中只有两件产品：新增 `training-preparation.js` 与原 `training.js` 集成，blob OID 分别为 `91f473a443561c8347ae572228f35791302eda44`、`6ff0826786d9a857a33613ce87aa53e188ef8750`。本轴直接以这两个固定 blob 重算路径组合 SHA256，仍为 `893a738a2a33ac3767be11e983afc7ee952ddb00a6fb595daea2fa6cd8b20ff5`，并逐字对照已验收 r2 wheel 对应条目，一致。因此本报告的本地产品验收确实对应已发布候选，没有把后续产品借入旧证据。
- 较首轮清单补入的 `docs/plans/2026-11-14-training-experiment-preparation.md`，固定 diff 仅追加 C1 精确交付终态；其 C1 CI 是上一片独立记账，未新增 C2 业务行为，也不构成本片 CI 通过证据。两产品之外的 14 件均为已列本片文档／两轴报告／公开证据及旧 C1 记账，没有新增 Python、测试、CI 或冻结参考变更。
- 实读原 `commit-r1.json`，退出 0、完整 staged diff check 0、候选相符；`push-r1.json` 原 argv 为普通 `HEAD:refs/heads/refactor/architecture-foundations`、没有 force 参数，退出 0，原 stderr 为 `92e7c24..2181cc5`；`ref-r1.json` 原 `ls-remote` 退出 0、完整原 Ref 值恰为候选 SHA。结论是该次正式发布与当时原远端 Ref 相符，不是声称以后远端不会继续前进。

原私有身份原件大小／SHA256，本轴重新计算如下：

|原件|字节|SHA256|
|---|---:|---|
|`static-final-r1.json`|3984|`7d7aed2efec258da8f5e5f4242fcb74f3303ec252902480deab740e0910266aa`|
|`commit-r1.json`|1034|`1201c7a81a3ee0f60478feffd33a03fbe1b9d575a1ddfd6e6b4b87776ced0ed9`|
|`push-r1.json`|749|`4902bd001b4d08e190f70191819b8e305bfc71b13503685f968f6637825cc07e`|
|`ref-r1.json`|737|`14048d1e95319d46bbfd5d3cee5a8b25ecc0454025f8fd3038f71be5120c1b66`|

固定发布身份补核通过，本轴开放产品 finding 仍为 0／0。本次仅更新原报告的发布记账；本片自己的 CI 尚在发现，未以 C1 的通过代替，也未对后续工作树作发布或验收主张。

## 本片自己的 CI 终核

本节关闭前文 CI 在途状态。终核对象仅为固定候选 `2181cc5c6ab92ac01664f8e769298cce350f65a5` 的 [Portability run 43530156938](https://github.com/626619403/Ergora/actions/runs/43530156938)。检查时当前 `HEAD` 已为后续 F9c C1 的 `c3c7c3e218e9d2efc89498e8c208bf5981b9a0d9`；本轴没有用其产品、workflow 或新分组替代 C2，也没有再次请求远端、安装或重测。

实读固定 Git 对象 `.github/workflows/portability.yml` 与 `scripts/ci/linux-groups.json`，而非只读终态 summary：

- 固定 workflow SHA256 为 `ec2816e893c25ff3a7f96513e677bdf53f42d90b3cd79fe585e474a27c0121b2`，固定 groups SHA256 为 `b3a2ac6610b225c419824f70cab5b81340eb6c7c58bf0c428906f9c6fe18c5a5`。固定配置是 plan＋六个 Linux 3.11 group＋一个 Windows 3.12 all，共八 job。
- 从固定 workflow 提取必要步骤：plan 的 `Read explicit test groups`；每个 native 的 build/install、packaged reference identity、native application regression、upload observations；Windows 额外 PowerShell 5.1 installer／upgrade。Linux 的 Windows 条件步骤正常 skipped，不计必要成功项。必要步骤合计 `1 + 6×4 + 5 = 30`。
- 直接读原 `ci-job-batch-r1/body.json`，其八个原 job ID／name／href 与 metadata 逐项一致，`totalCount=8 / hasMore=false`。batch 抓取时部分 job 仍在运行，只用于发现身份，未当作终态；该 body 与原 receipt 的 HTTP 200、完整 URL、字节数和 SHA256 相符。metadata 的来源摘要及早期 run summary 的完整候选链接也一致。
- 直接读 `ci-run-html-r4/page.html` 与 receipt，HTML 内完整 commit 链接为 `2181cc5…`、分支为原发布分支、Status 为 `Success`；原收据 request／final URL 均为本 run，HTTP 200，213,372B，独立重算正文 SHA256 为 `c999b88730fefe5bf0e8fa2e488da0bbf42ca96c514be442c047a1356210dbad`。

逐个 job 的最终原件与必要步骤补核如下；所有页面均重新核 request／final URL、HTTP 200、正文大小／SHA256 与原收据一致：

|job|原 ID|最终 HTML 样本|必要成功步骤|最后必要步骤完成时间（UTC）|
|---|---:|---|---:|---|
|plan|132245558096|`ci-job-132245558096-html-r1`|1|2026-11-13 23:51:27|
|Linux group 0|132245634584|`ci-job-132245634584-html-r1`|4|2026-11-13 23:56:34|
|Linux group 1|132245634641|`ci-job-132245634641-html-r1`|4|2026-11-13 23:56:56|
|Linux group 2|132245634595|`ci-job-132245634595-html-r1`|4|2026-11-13 23:55:32|
|Linux group 3|132245634600|`ci-job-132245634600-html-r1`|4|2026-11-13 23:53:48|
|Linux group 4|132245634620|`ci-job-132245634620-html-r1`|4|2026-11-13 23:54:44|
|Linux group 5|132245634653|`ci-job-132245634653-html-r1`|4|2026-11-13 23:57:35|
|Windows all|132245634563|`ci-job-132245634563-html-r3`|5|2026-11-14 00:08:47|

本轴以独立只读 HTML 解析直接检查 30 个原 `check-step`：步骤集合与固定 workflow 相符，无遗漏或多算；每项 `data-conclusion=success`，有 started／completed 时间且顺序成立，具有原 `data-job-completed` 属性。每个原 `data-log-url` 都精确等于 `/626619403/Ergora/commit/2181cc5c6ab92ac01664f8e769298cce350f65a5/checks/{原job ID}/logs/{原step number}`，没有借 C1 或后续 F9c 的绿色状态。独立结果逐项与 `ci-terminal-r4.json` 的摘要、时间、路径一致。

Windows 使用第三份原样本：native regression 在 00:07:51Z 完成，PowerShell installer／upgrade 在 00:08:46Z 成功，upload 在 00:08:47Z 完成。未以 Windows 更早仍在途的 r1／r2 样本代替终态。最后必要步骤早于最终原 run HTML 的 00:11:12Z 收据，终态观察顺序相符。

另独立重算公开 JSON 新列的 23 份 CI 原件引用大小／SHA256，全部匹配。此终核采用原 UI HTML／JSON、原收据和固定 Git 配置，没有声明 REST 查询、artifact archive 下载、逐行测试日志内容复核或本地重跑；完整 SHA 日志路径已核，但未重新下载其日志。Windows 的标准 CI 成功不扩大 Linux／WSL2 原生准备支持范围，也不替代真实训练／GPU／质量／性能或批准验收。

本片自己的 CI 终核通过，原固定发布身份及本结构轴开放 finding 维持 0／0；本轴无剩余阻塞项。后续 F9c 与更广训练验收继续沿各自固定候选、计划和证据，不继承本片 CI。
