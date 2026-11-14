# F9c C3 独立需求审查

日期：2026-11-14。审查者：fresh-context agent `/root/training_evidence_console_spec_review`。本审查只读项目源码与本地验收原件，只写本文；未修改产品、安装依赖、运行产品或测试、提交或访问外部。

## 身份与范围

- 原始范围：嵌套串并行 Agent 模板、父级权限上限／祖先资源累加、各层后端替换与低代码控制台的持续计划；本片仅落实既有训练详情中的原证据审阅、精确 owner 批准／恢复和手动集成复验导航，不扩大训练、权限或执行权威。
- 直接依据：[本片合同](../plans/2026-11-14-training-evidence-console.md)、[C1](../plans/2026-11-14-training-evidence.md)、[C2](../plans/2026-11-14-training-release.md)、项目 `AGENTS.md` 与 `maintainable-project-delivery` 的独立审查说明。
- 固定基线：`1eef90d7453c64579ddc25bd5a7775eecd20c2cc`，分支 `refactor/architecture-foundations`；未提交候选。
- 产品检查：`src/ergora/data/console/training.js` 的完整基线差异与相关详情／selected 生命周期；直接读取新增 `src/ergora/data/console/training-evidence.js` 全文，未把不含 untracked 文件的 Git diff 误作完整候选。
- 文档检查：`README.md` 与 `docs/TRAINING.md` 的本片差异，新增控制台读取／确认／恢复／手动集成复验步骤与实际入口一致。相邻 C2 发布／CI 状态文件不是本片产品差异。
- 当前 r4 源码 SHA256：`training.js` 为 `9893dc084b3223d9d0be4f02fc6f4599ea6a2e0e06a0008dd69632619ecf5338`；`training-evidence.js` 为 `e6b756487009b2aa2e19dcf5fd318958aa081180949629c963ece110f4348a60`。
- S1 修后 r3 `training-evidence.js` 摘要为 `049753d1467f39e7d308f8bde619cf060b860cdaf031ca12da1c436842efb513`，曾直接核安装文件与当时源码一致。r4 唯一后续差异是将 native `append` 中缺省 run 输入的 `null` 改为条件追加，避免恢复表单显示文字 `null`；已读最小差异，不将 r3 身份冒称 r4。
- 邻近 owner／调用者：`reference_training_evidence.py`、`reference_training_release.py`、`training.py`、`web.py` 及控制台 `app.js`、`api.js`、`ui.js`、`state.js`、`training-preparation.js`、`training-cancellation.js`、`style.css`。

## 结论

需求符合性：**最终本地 approve，开放产品 finding 0**。S1 已经静态修正及原浏览器反例关闭；最终 r4 包、相关回归、原件／history／收尾及自身模板均有原件。下文明确区分实际动态证据、静态覆盖和未执行旅程；本结论不代表本片尚未执行的精确发布／自己的 CI，也不关闭 F9d／真实 B3。

可维护性：**本轴检查范围 approve，无新增阻断 finding**。新增文件由唯一详情调用者挂载，拥有相邻但独立的证据／文本／批准生命周期；复用原 HTTP、DOM primitives 与正式任务页入口，没有另建业务账本或执行权威。独立结构轴仍以其自己的报告为准。

## 合同核对

|合同|源码与边界结论|
|---|---|
|原元数据显式读取与范围说明|`training-evidence.js:93` 的独立 GET 不自动查询运行或执行 comparator；完整原 evidence、gate、manifest、baseline、comparator 摘要、binding、文件摘要及 artifact 索引可展开。原件失败沿 error 显示；声明内容仍为 `not_read`，不把原 gate 记录升格为重新评价。|
|原 SHA 与 Unicode 窗口|`training-evidence.js:125` 仅给原索引 option；读取前核完整本次 evidence SHA、HTML validity 和安全整数，offset／limit 范围与后端一致。使用后端的 `next_offset`，不以 JS 字符串长度计算 Unicode 分页。选择、输入变化和重读清除／失效旧文本；错误替换本次正文区域。后端继续核完整文件 SHA、16MiB、UTF-8 与 NUL。|
|首次批准与恢复分流|`training-evidence.js:33` 仅 `not_recorded` 分支要求当前 accepted archive；原 `/approval` 只有已确认原 submitted run 才返回可批准状态。首次明确输入完整 run／evidence，prepared／unknown 仅输入原 intent，POST 发送原 revision 与 `confirm: true`。Linux 条件与现有入口一致。|
|原件缺席仍可恢复|`training.js:174` 在外层详情 GET 前独立挂载面板；批准 GET 与 resume 不依赖本面板 evidence 读取成功。unknown 文案只查原历史，实际 resume 继续交给原 C2 owner，页面不产生新 ID 或自动重发。|
|异步失效与防重入|独立 evidence／approval／text 序号约束各自响应；selected 闭包同时核详情世代、连接状态、项目、home 与 tab。mutation 同步设置 `sending` 并禁用局部控件；错误移除 mutation 入口，先读原记录后再确认恢复。S1 最终修正保留显示中 artifact 的 source 世代；同 source pending 只读响应允许完成，新增 metadata 控件及文本下一页按钮在发送期间同样禁用；批准结果在 finally 后重绘。|
|投递、授权、票据与采用分离|requested 文案只确认投递，授权明确未评价；owner receipt 创建 unknown 与 signal unknown 分行呈现。原 integration ticket wrapper 含 record／task_id／URL，单独显示并仅提供现有正式任务页手动入口；无自动 Task、合并或采用调用。|

## Finding 与修正复核

本需求轴未新增 finding。结构轴报告的 **S1** 是可达的需求问题：原版 mutation 同时递增 `evidenceSequence`，使现存 artifact 闭包携带的 `evidenceRequest` 永远失效，批准后控件虽重新启用却静默不发 GET。已直接重读最终 r3 修后全文：mutation 不退休仍显示的原 source；同 source 的 pending metadata／text 可以完成，metadata 新控件及文本下一页按钮继承禁用状态；批准区在发送结束后重绘。静态修正符合最小范围，r3 实际浏览器已证明批准后原 artifact 控件继续发 GET 并显示正确正文；专项 recovery 亦核 mutation 期间晚到 metadata／text 不恢复可用控件、完成后原 next 可读。S1 需求侧关闭；r4 仅缺省输入渲染修正，不改变该生命周期逻辑。

## 已读证据与限制

- 已读 r1 `package-identity.json`：wheel `98b2c049d76713df3cd23179ac115b0261a7c507d9dfec6bf73a674270b90662`、575 产品文件、两 RECORD 583／588、283 冻结、noneditable。它属于 S1 修前身份，不作当前修后候选的最终安装证明。
- 已读 r1 回归 `result.json` 和原 stdout：web／training_evidence／architecture 三 suite，原 monitor `succeeded`、returncode 0、29.018 秒，pytest 实际 33 passed／27.41 秒。已安装旧 `training-evidence.js` 摘要为 `86589fce01dcce597603c6e247db1359dbfcd4e295994344b4b0af5f918db123`，与 S1 修后候选不同；该回归不扩大为修后候选或浏览器验收。
- 已读 r2 中间包身份／回归原 stdout：33 passed／27.57 秒，monitor 29.482 秒；该包不作最终 r3 浏览器证明。
- 已读最终 r3 `package-identity.json`、回归 `result.json` 与原 stdout：wheel `c179706b78277ad15bebbc10e347838b48c8f8f38507d60bfcb68ac6824e690b`、575 产品文件、两 RECORD 583／588、283 冻结、noneditable；同三 suite 33 passed／26.85 秒、monitor 28.580 秒，实际检查范围与上述两文件 SHA 一致。
- r4 最终安装原件已直接只读核：wheel `0e0518ed2e97eb343fb3866bc8646dc16c3109d2310870ab737c32951544cb16`；两 RECORD 共583／588行，实际582／587项哈希与长度全部匹配；575份产品在 wheel／安装／当前源码逐字一致；283冻结文件匹配原 manifest。实际动态范围见下方最终证据表，不因包身份核对扩大运行结论。
- 已读 `browser-r2/basic-r1` 原命令、脚本、stdout、只读 `basic-continuation-r1` 与原 HTTP trace。实际原 alpha 已确认一次 approve POST 200；随后原控件 GET 200，初脚本因期望少写 `n` 报错，未重新批准。续验按 Unicode 码点核原 10 字符窗口 `证据窗口 🧪\nsyn`、原 approval 的 requested／authorization_status=not_evaluated 与同 evidence 的原 ticket.record（automatic_merge:false）。原脚本在该处之前已核显式 metadata、本次 SHA／数值错误零请求、Unicode 两窗口、二进制错误替换旧正文、发送期间全禁用与单 POST；不把脚本整体失败改记为整体通过。
- 已读 `browser-r2/recovery-r1` 脚本／原结果／命令与中途交互记录：110.277 秒、exit 0，仅 beta／gamma 各一次 approve 和一次 resume。beta 是真实 signal 接收后丢 ack 的 unknown，恢复结果来自原 history；gamma 是原 receipt 写后中断的 prepared／owner_receipt unknown，恢复后正常投递。真实 metadata 响应晚到仍全锁；同 source 文本完成且 next 禁用，恢复完原 next 发 GET 并沿 offset=4 返回。脚本先填 intent 再刷 metadata，确认框重绘清空；原 snapshot／实际交互重新填写当前确认框，沿同一原 run 继续，未另发 approve。此证据是带人工交互调整的原 run，不称无人干预整段脚本成功。
- 自身模板原件已核：`self-review-r1-codex.json`、实际 native run、原 prompt／stdin／composition 资源／result。10 完整文件共95,849B，实际 prompt=stdin 共101,044B；全部10份材料及3份祖先／本层资源均在 stdin，产品摘要等于最终 r3；51.105 秒、approve，原 result SHA256 `22a03526ba4c53c05636d25ad58ab0e15c101ccf11c9573f58847b6dda0d8765`。这是使用原 Ergora 结构模板的自审，不代替 fresh-context 独立评审，也不宣称异后端成功。
- 已读 native-r1 `failure.txt` 与 `cleanup.json`：私有第二项目夹具缺 `schema_version`，Temporal／worker 已收尾、7233 不监听。该失败保留，不作产品缺陷或成功旅程；后续成功属于新的 native-r3 state。native-r2 只完成 bootstrap 后正常停止，不冒称浏览器成功。
- 两个 JS 语法通过由实施者提供；本轴未重新执行 parser。未运行测试、安装、浏览器或训练。
- 旧 mutation 响应晚到／旧 finally 不清新面板的锁，以及 home 变化，仅直接核 `selected` 与每个面板局部 `view`／`sending` 闭包，未作动态测试。实际生命周期测试覆盖的是 read 响应：metadata 重排、offset 编辑、切实验的 metadata／approval、切项目的文本与切 tab 的 metadata。
- 原 start／cancel 仅直接 diff／调用链核保持；本片未跑其专门 suite，亦无新的 start／cancel UI mutation 旅程。33项只属于 web／training_evidence／architecture，完整控制旅程仍归 F9d。

## 最终 r4 证据复核

|范围|直接检查的原件与结论|
|---|---|
|安装／回归|`install-r4` 身份及两 RECORD／283 已逐项只读核；`regression-r1/result.json` 与 stdout 为33 passed／25.02秒，原 monitor 26.731秒、returncode 0。|
|缺源与丢 HTTP 回复|`browser-r3/delta-recovery-r1-result.json`、原脚本／stdout／请求 trace：原 spec、baseline、runner、accepted archive 缺席时，外层详情及 evidence 明确400，本地原 unknown 仍可读；确认原 intent 后仅查原固定 run history。真实200回复被 abort 后只以本地 GET 读回同一 requested／intent；仅一次 resume POST，无 literal `null`。|
|真实读响应交错|`browser-r3/lifecycle-r1-result.json` 与原脚本／stdout：路由先取得真实 loopback 响应后受控放行；metadata 重排及编辑 offset 后的旧文本失效，实验／项目／tab切换均不污染新面板。未把这些读反例扩大为迟到 mutation／home 动态覆盖。|
|显示与手动票据入口|`browser-r3/visual-r1-result.json`、原脚本及截图：1440／960／390三宽度，展开长 metadata／approval 后 document 宽度分别等于视口；本轴也直接目视三个 top 截图，SHA／文本可换行，按钮可见，无横向溢出。原 ticket 到正式任务页只导航，mutation计数0。|
|自身原模板|最终 `self-review-r2-codex.json` 与原 run／prompt／stdin／composition／result：10完整文件97,136B，实际 prompt=stdin 102,657B，逐份捕获原字节与 packet SHA一致并出现在 stdin，3份祖先／本层资源完整出现；48.701秒approve。原 result SHA为 `1bcbcbe90d355b8fd62de4d7a2b9f22e9a8fd4e01df3f5e36cff092e7e21b211`，产品摘要等于最终 r4。这是自身模板及已授权 Codex 回退，不称异后端或独立审查成功。|
|原 owner／材料保持|`native-r3/audit-r1.json`、`histories-audit-r1.json` 与四份原 history：本轴直接读每份46事件、各唯一原 `request_release`，解码核同 spec binding／evidence／receipt；原 receipt 创建 marker、原字节 SHA与expiry、四份原 ticket均匹配，automatic_merge:false。24准备原件／109读取原件逐份重核 SHA一致；四缺席来源移回原件通过。无 runner／executor start／fence，测试 repo clean。合成归档不证明训练、GPU、质量、性能或真实集成复验。|
|进程收尾与控制台|`cleanup-final-r1.json`：原 native三组及最终 web组经原 monitor停止；两 browser daemon不运行；7233／60197／52241三端口关闭。`console-final.stdout`仅含两次预期缺源400和一次主动 abort，无 JS exception。|
|公开证据身份|已逐项只读核[公开证据摘要](evidence/2026-11-14-training-evidence-console.json)143个引用的原字节数／SHA，以及两个产品 path+NUL+bytes 组合 `f9f40ac06c9e95a915bba6a9301e80f32b90870fc1ed87121466fa4a388a69d6`。r3前三 run 的证明保持 r3身份；r4只修缺省输入显示并有第四原 run及最终三suite证明，不将历史执行重新标成 r4。|

当前本地需求结论 approve、开放产品 finding 0；公开摘要和交付须继续保留上述失败／续交互／静态及未验范围。精确普通发布、固定提交身份补核及本片自己的 CI 尚待，不借 C2 的 CI 成功关闭；F9d／真实 B3 与真正集成复验／采用继续另验。

## 固定发布补核（2026-11-14）

结论：**固定发布需求补核 approve，开放 finding 0**。本次直接使用 `git show f47cd50fcce600fba92f64aff73982012f6e31c9:PATH` 读取固定对象，不以当前工作树中的发布补记或后续 F10 计划替代候选内容。

- 固定提交 `f47cd50fcce600fba92f64aff73982012f6e31c9` 的唯一父提交为原基线 `1eef90d7453c64579ddc25bd5a7775eecd20c2cc`。19 个实际变更路径与 `static-final-r1.json` 清单集合相同，每个固定 Git blob 的原字节数与 SHA256 逐项匹配。
- 两份固定 JS 的 path+NUL+bytes 组合保持 `f9f40ac06c9e95a915bba6a9301e80f32b90870fc1ed87121466fa4a388a69d6`。固定 `src/ergora` 全部575份产品与已验 r4 wheel／安装逐字相同；wheel SHA256 仍为 `0e0518ed2e97eb343fb3866bc8646dc16c3109d2310870ab737c32951544cb16`。再次只读核两 RECORD 583／588行的全部有效哈希与长度，以及固定 manifest 的283份冻结文件，均匹配。
- 固定公开 JSON blob SHA256 为 `1f621bd7abdb403fc8c67363a93a4ae2e2d3660464036bb6f5de18ef785a6b5d`，其中原143个引用均逐项匹配本地原件字节数／SHA。当前工作树 JSON 的147个引用另行核对：原143项未改，新增项仅 `static-final-r1.json`、`commit-r1.json`、`push-r1.json`、`ref-r1.json` 四份发布原件，四项哈希及长度均匹配；147项不属于该固定 JSON blob。
- 已读四份发布原件。`commit-r1`、普通非 force 的 `push-r1`、`ref-r1` 均 exit 0；原远端读取记录完整匹配 `refs/heads/refactor/architecture-foundations = f47cd50fcce600fba92f64aff73982012f6e31c9`。这是对发布时原记录的核对，本轴未执行网络或重新推送。
- 本片自己的 CI `43539314720` 仍待终态核验，不把 push／Ref 成功称为 CI 成功；后续 CI 由原结构轴终核。本地证据的实际／静态／未验范围保持上文原边界，F9d／真实 B3 不因精确发布而关闭。

本次只补本文，未改产品、安装、网络或提交；固定发布补核完成，停止修改。
