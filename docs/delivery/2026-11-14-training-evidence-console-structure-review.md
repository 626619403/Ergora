# F9c C3 独立结构、性能与维护性审查

日期：2026-11-14。审查者：独立 fresh-context agent `training_evidence_console_structure_review`。按原始片合同、仓库规则和实际源码审查，未继承实施过程或预设结论。本轮仅写本报告，未改产品、安装、提交或访问外部。

## 范围与当前结论

基线为 `1eef90d7453c64579ddc25bd5a7775eecd20c2cc`，当前分支 `refactor/architecture-foundations`。完整直接读取 tracked `src/ergora/data/console/training.js` 的差异与 untracked `src/ergora/data/console/training-evidence.js`；后者不是通过 Git diff 间接推断。原始要求以 [C3 合同](../plans/2026-11-14-training-evidence-console.md) 为本片验收口径，保留多 agent／后端、祖先资源与父权限、原六阶段和低代码入口的总约束。本片没有修改这些原业务合同。

本次已读取 `AGENTS.md`、`docs/PLAN.md`、交付记录、maintainable-project-delivery 及其 independent-review brief、codebase-design。也直接沿调用链读取 `api.js`、`ui.js`、`state.js`、`app.js`、原取消／准备面板，以及 `training.py`、`web.py`、`reference_training_evidence.py`、`reference_training_release.py` 和相关现有测试／样式。

- **需求合规：本片最终本地范围 approve。** 首次完整 run／evidence 确认、原 intent 恢复、unknown 仅查历史、sources 失败独立读取、requested 不升级为授权或采用、手动任务入口都可追溯到原 owner；最终包及实际入口证据已按下述范围复核。发布与本片自己的必要 CI 继续独立验收。
- **结构／性能／维护性：最终本地 approve，开放 finding 0／0。** S1 及关联加载状态已获源码与实际异步交错复核，M1、浏览器发现的 M2 已关闭。没有未解决的结构阻断项；性能结论限于交互、容量与请求路径，未作 GPU 或性能收益主张。

最终直接复读产品身份：`training.js` SHA256 `9893dc084b3223d9d0be4f02fc6f4599ea6a2e0e06a0008dd69632619ecf5338`；`training-evidence.js` SHA256 `e6b756487009b2aa2e19dcf5fd318958aa081180949629c963ece110f4348a60`。最终 r4 wheel SHA256 `0e0518ed2e97eb343fb3866bc8646dc16c3109d2310870ab737c32951544cb16`；两产品路径／原字节摘要 `f9f40ac06c9e95a915bba6a9301e80f32b90870fc1ed87121466fa4a388a69d6`。也核对了新增 README 入口与训练手册实际 UI 步骤。后续产品修改须按新身份重新核对。

## Findings

### S1 · P2，已修复并完成本地复核：mutation 废弃 metadata generation，使仍显示的文本控件静默失效

首轮位置：`src/ergora/data/console/training-evidence.js:57`、`:125`、`:134`、`:136`、`:74`。先读取原归档，让 `showArtifacts` 的闭包捕获本次 `evidenceRequest`，随后批准或恢复。首版 mutation 递增 `evidenceSequence`，而 finally 又启用旧文本控件。旧控件随后每次读取都因 `evidenceSequence !== evidenceRequest` 静默返回；必须额外重读整个原归档才恢复。若 mutation 开始前 metadata read 尚未返回，原响应被废弃后也可能留下永不结束的“正在读取原归档证据”。这违反可用控件与请求生命周期的一致性，并使读请求序号同时承担资料版本和发送锁的责任。

最小修正是保留仍有效的 metadata 控件身份，发送期间统一约束重绘／新建控件的 disabled 状态，finally 恢复当前操作的显示，不引入第二业务状态。实施方采用该方向：不再递增 metadata generation；`showApproval` 在发送时暂停重绘；pending metadata 落地后同步禁用新控件；最终批准表单在 finally 重绘。中间 `0bdd27c…` 版已静态消除原死控件路径。

关联复核项：中间版 `0bdd27c8…` 的 mutation 仍在第 57 行递增 `textSequence`。如果原文本窗口请求已显示“正在按原摘要核对完整文件并读取窗口…”但尚未返回，此时开始 mutation，其响应会被废弃，而该加载提示没有同步清除。操作完成后会留下已失效请求仍在读取的展示。已反馈实施方；此项不能靠语法检查或 HTTP 回归关闭。

最终复核：r3 `049753d1…` 的 mutation 不再递增 metadata／text generation；仍绑定同一 source 的 pending 只读结果可以完成，来源／选择变化仍经原 generation 废弃。第 117 行同步禁用 pending metadata 新建控件；第 151 行让 pending 文本新建的下一页按钮继承 `sending`，第 70–73 行解锁并统一重绘批准表单。r3 浏览器的同 DOM 批准后原控件 GET、beta pending metadata 在恢复期间落地仍全锁、gamma pending 文本完成时 next 仍锁且恢复后可读下一页，均有实际脚本／请求／结果证据。r4 的这些控制逻辑与 r3 逐字一致，r4 lifecycle 又实际核了来源和页面切换后的旧读响应。S1 及关联失效加载状态关闭；原 r3 运行身份保留。

### M1 · P3，已修复：修复后的成功路径保留了必定无效的重绘调用

位置：上述 `0bdd27c…` 版本 `training-evidence.js:64`。成功分支在 `sending` 必为 true 时调用 `showApproval()`；第 15 行的 guard 必定立即返回，实际重绘统一由第 75 行 finally 负责。删除成功分支中的这次调用、只保留赋值，可让显示责任与锁生命周期更清楚。该项不影响服务端权限或发送次数。

最终 `049753d1…` 第 62 行已只保留 `approval = result`，finally 为唯一 mutation 重绘位置，修复关闭。

### M2 · P3，实施方浏览器发现，已复核修复：恢复表单出现 literal null

位置：`training-evidence.js:49`。native `approvalBody.append(..., run, ...)` 会在恢复分支把可选的 `run = null` 变成文本，与 `node` helper 的过滤语义不同。最终仅 spread 实际存在的 run 输入；r3／r4 wheel 的全部产品差异恰是这一行。r4 缺源 unknown 恢复脚本在真实 DOM 检查无该 literal-null 子节点，原 intent 确认与恢复通过，修复关闭。

## 结构、复用及控制流判断

`trainingEvidencePanel` 的唯一生产调用者是 `training.js:180`；未发现其他生产调用，不用测试或假想扩展充当复用证据。独立文件的理由是局部 owner 的内聚性：一次返回完整面板，内部私有实现承担两个独立读取区、文本分页、SHA 确认、批准恢复和发送锁；训练页继续负责列表、实验选择与既有详情。与原 `training-cancellation.js`／`training-preparation.js` 一致，这个 module 有小 interface、集中的 implementation 和可解释的 locality。没有必要为单一调用者再造通用 controller、registry 或前端状态库，也不应仅为消除单调用文件而把这些状态摊回列表 owner。

`selected` 复用原详情 generation，并经 `active` 同时检查 DOM 连接、project、home、tab；新面板未复制项目选择权威。发送锁局限在原面板闭包，旧实验的 finally 只能触及旧面板，不会清掉新实验的发送锁。请求序号负责展示先后；原意图、receipt、attempt、原 run 及历史对账仍由服务端持有。

首次 archive guard 和完整 run／SHA 输入保护明确的用户确认；prepared／unknown 分支不依赖当前 evidence；`platform` 分支与原平台支持范围一致。HTML validity、非空及 safe-integer 检查分别防止范围／step、空串归零及 JavaScript 数值精度丢失，属于 UI 输入 seam；不重复实现服务端 archive、owner receipt 或历史完整性检查。原件、网络与丢回复的 catch 保留显式失败和先读原 intent 的恢复入口，不自动重试。未发现需新增的无关参数检查、fallback 或第二授权判定。

## 性能、测试与证据限度

本片只在显式点击时读 metadata／文本，无后台轮询或自动读全部 artifact。窗口字符串直接使用原 `offset`／`next_offset`，不以 JavaScript UTF-16 长度重算原 Unicode offset。每次读取完整核 SHA 和 metadata 的开销属于原 C1 HTTP owner；UI 没有新增另一套缓存或 archive 账本。既有 16 MiB 文件／8 MiB 响应限制和 CSS 的文字换行、受限滚动可追溯。三视口尺寸和保存截图已核；没有浏览器吞吐或 GPU 性能测量主张。

tracked diff 与 untracked 清单确认没有 Python、HTTP、CI 或测试文件变化，因而没有新增冗余测试／CI job／assertion 可清理。既有 `test_training.py` 的 HTTP／CLI 原件一致性及 `test_web.py` 的本地 HTTP／资产检查，不能替代本片 DOM 状态交错验收；也不需要为可见文案另加镜像 unit tests。S1 的关键证据应落在实际浏览器交互及最终安装资产身份上。

本审查者执行只读的状态／diff／调用者搜索、直接源码与原件字节／摘要核对；最终两 JS 的 `node --check --input-type=module` 均 exit 0。未安装、改产品、访问远端或重跑产品写操作。实际运行证据通过原脚本、stdout、请求日志和保存历史复核，未把实施方汇总本身当作通过依据。

## 最终本地证据复核

公开索引为 [本片证据摘要](evidence/2026-11-14-training-evidence-console.json)，私有原件根为 `.ergora/checks/training-evidence-console/`。以下路径均相对该根。

| 范围 | 本审查者直接核对的证据与结果 |
| --- | --- |
| 最终安装身份 | `install-r4/package-identity.json`、wheel、源码快照和安装目录：575 产品全部与当前源码逐字一致，wheel RECORD 583 行、安装 RECORD 588 行的摘要／长度全部正确，283 冻结文件摘要全部正确，安装 `direct_url.json` 指向 wheel、无 editable 设置。 |
| 相关现有回归 | `install-r4/regression-r1/result.json` 与原 stdout：`test_web.py`、`test_training_evidence.py`、`test_architecture_boundaries.py` 共 33 passed／25.02 秒，原 monitor 26.7307 秒、returncode 0。 |
| r3 原前三 run | `browser-r2/basic.js`、原失败 stdout、同 DOM `basic-continuation-r1-result.json`、`recovery.js`、恢复的 snapshot／实际 fill／click、`recovery-r1-result.json` 和请求日志：错误 SHA／无效数值不发请求，Unicode／next_offset、二进制失败清旧正文，alpha 单 POST 与发送锁；beta 实收 signal 丢 RPC ack 后原 history 恢复；gamma receipt 写后中断为 prepared／receipt unknown，继续原件。S1 两种 pending 读与恢复后 next 可用。 |
| r4 实际页面 | `browser-r3/delta-recovery.js`、`lifecycle.js` 及对应 result／stdout／请求日志：四原 sources 缺失时详情与 evidence 明确失败，原 unknown 仍可读并沿同一 run 历史恢复；真实 HTTP200 回复被 abort 后仅 GET 读回。metadata reorder、改 offset、切实验 metadata／approval、切 project text、切 tab metadata 均废弃旧读结果。服务资产日志 SHA 与最终两 JS 一致。 |
| 三视口与票据 | `browser-r3/visual.js`／result：1440／960／390 的 document 宽度分别等于 viewport；展开资料与批准原件。本审查者实际查看三个 `evidence-top-*` 截图，长 SHA 和文本在面板内换行；原 ticket 手动前往正式任务页产生 0 mutation。 |
| 原 owner 保持 | 直接解码四份完整原 history，每份 46 events、各唯一 `request_release`，原 run／binding／evidence／receipt ID 与保存核对一致；receipt SHA／expiry 已核，四份原票据的 binding／evidence／receipt ID 一致。`protected-before.json` 24 件、`read-originals.json` 109 件及移回的四 sources 摘要全部一致；无 runner marker、job started 或 fence，测试 repo Git clean。浏览器合计 6 次 approve／resume POST，delta 的先验 accepted-signal 丢回复由原 CLI/application 夹具单独产生。 |
| 自身原结构模板 | `self-review-r2-codex.json`、原 `native.stdout`、10 个完整 inline 文件共 97,136B、3 份继承资源、原 prompt／实际 stdin 逐字一致。48.7007 秒、exit 0、decision approve；原 result SHA256 `1bcbcbe90d355b8fd62de4d7a2b9f22e9a8fd4e01df3f5e36cff092e7e21b211`。这是授权 Codex 回退的自身模板结果；独立结论来自本报告。 |
| 收尾及公开索引 | `cleanup-final-r1.json`、原 monitor cleanup：四服务组已停止、两浏览器 daemon absent、7233／60197／52241 全闭；本审查者另只读核 `/proc` 与监听表一致。最终 console 仅两次预期缺源 400 和一次 intentional HTTP abort。公开 143 个原件引用全部存在、字节／SHA 一致、无重复，合计 1,949,210B；产品聚合摘要重新计算一致。 |

历史限度保留：basic-r1 在已完成批准和后续 GET 后，由私有 10 字符预期漏掉最后 `n` 而失败；同一 DOM／run 的 continuation 只读续尾，没有重发批准。recovery-r1 先填 intent 再刷新 metadata 造成确认栏重建，经 fresh snapshot 和真实 fill／click 继续同一原 run；原 4 POST 与历史保持，不称无人干预一条脚本成功。r1 夹具注册缺字段、r2 停在浏览器前和各旧包回归仍按原范围记录。

## 剩余范围

本地开放 finding 为 0／0。home guard、旧 mutation／finally 跨视图隔离由原 `active`／闭包 ownership 静态核对；动态 lifecycle 只覆盖上述真实读响应。原 start／cancel 本片以 diff／callpath 核对保持，没有新增其 UI mutation 旅程或专属 suite 成功主张。完整 F9d 旅程、真实 GPU／训练／质量／性能／集成复验／采用继续另验；合成 archive 只证明此入口合同。Linux Chromium 已验，Windows 原生 mutation 未宣称支持。C3 精确发布与自己的必要 CI 尚待，不借 C2 的 CI 关闭。
