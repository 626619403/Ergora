# F9b3 独立需求／正确性审查

当前结论（最终本地出口）：**需求／正确性通过，开放 finding 0。** 源码、分段安装、真实 CPU／浏览器、原模板自身调用、最终 r3 包与公开证据均已补核；本轴所查责任边界／维护性也无 finding，独立结构轴的完整结论另归该轴报告。原安装 r1 的 600 秒取消保留：89 项逐项通过，加上 r2 补测的 66 项通过，精确覆盖 155 个原收集项；不称一次全新 r3 全套或全旅程。普通精确发布／远端 Ref／本片自己的 CI 仍待验。以下保留各轮身份、原失败和当轮未验范围，较早的“待补核”仅指该轮。

审查者：fresh-context 独立需求轴 `f9b3_spec_review`；日期：2026-11-14。未继承实现过程；依次读取 `AGENTS.md`、总计划、[本片原始计划](../plans/2026-11-14-training-cancellation.md)、实际 tracked diff／untracked 新文件和邻近调用者，最后读取[作者交付](2026-11-14-training-cancellation.md)。使用 `ergora-codebase-quality` 的原调用者、模块所有权与真实失败路径标准。仅写本报告，未修改产品、测试、原参考、作者私有证据或 Git 状态，未安装或重跑服务／大 suite。

## 固定候选与检查范围

基线／HEAD 为 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`，分支为 `refactor/architecture-foundations`。未提交候选的精确输入是私有 `review-r1-files.json`：28 文件，SHA256 `128e9f1c8b81699601843765213e3ee46659d065b699c15ce39c48d847954275`；tracked diff 为 `review-r1.diff`，SHA256 `8f171a8e59ab9b09df18d1614bda2bd8747c609f729f28549bfed7bc91560032`。逐项重新计算工作树长度／SHA，28 项全部相符；清单恰好覆盖 21 tracked 与 7 untracked 路径。后续改动和证据不自动继承本轮结论。

全文检查新增 `reference_training_cancellation.py`、`reference_history.py`、`training-cancellation.js`、`test_training_cancellation.py`、`training_cancellation_client.py`，以及以下已有文件的实际改动：

- 入口／原生接缝：`training.py`、`reference.py`、`reference_training_runtime.py`、`reference_task_runtime.py`、`reference_task_approval.py`、`reference_task_cancellation.py`、`cli.py`、`web.py`、`data/console/training.js`。
- 测试／CI：`training_runtime_client.py`、`training_submission_client.py`、`test_architecture_boundaries.py`、`test_original_payloads.py`、`scripts/ci/linux-groups.json`。
- 文档：README、PLAN、TRAINING、WINDOWS、当前架构、本片计划／交付、F9b2 两份评审的发布记账补充。

相邻实证来源包括原 `_Submission` 身份／intent／attempt／receipt、原训练 client／models／workflow、原 `ClusterAdapter`／`LocalTrainingAdapter`、`core.write`／`environment`、`safe_file`／`read_raw`、跨进程文件锁及页面生命周期。未把其他功能包或历史成功当成本片通过证据。

## 需求／正确性轴

**所查源码范围通过；无代码 finding。** B3.1–B3.5 的关键路径与计划一致：

1. `reference_training_cancellation.py:21` 复用原 `_Submission`，要求有效 `submitted` 回执，固定原 start SHA、run、registration／execution／home 和完整原 spec。取消恢复不重读当前 baseline／runner／spec；请求 ID 与原因、操作人保存于同一不可变意图，真正孤儿 checkpoint 拒绝，合法并发读取沿 completion→attempt 顺序。
2. `reference_training_cancellation.py:116` 在原固定 run 上核完整起始输入及 start memo；`dispatch` 再由原 client 查询／核 binding，原 signal 发送前先持久化 attempt。独立操作 SHA 附于原 `CancelRequest` payload，不污染 reason；已关闭 run 写 `not_sent`／`already_closed`，不伪称取消或停止。
3. `reference_training_cancellation.py:170` 在已有 attempt 时仅匹配固定 run 的完整 signal history。缺事件、外部同原因、错误 marker、NOT_FOUND／RPC 失败不生成投递确认，也没有自动重发入口。
4. `reference_training_cancellation.py:179` 分别读取原 control、原 adapter 的 lookup／poll 与原 fence；负 Outcome、缺 job、QUEUED／RUNNING 不被重写成停止成功。路径不调用 runner、cancel、fence 写入、评价或批准。
5. `training.py:58` 是 CLI／HTTP 共同入口；DB 预留只覆盖本地 prepare，文件锁覆盖同一请求发送／恢复。`training-cancellation.js:36` 的发送锁与序号、`:68` 的 request-ID 读取序号、`:83` 的独立停止观察序号和父页面 `selected` 条件抑制双击及旧项目／详情／请求的迟到响应。详情读取失败仍保留原提交与取消入口；默认页面不发 signal 或停止查询。CLI 将未确认的变更与成功读取分开返回退出码；本地 status 不导入可选 SDK，非 Linux 实际写入／executor 观察明确拒绝。

上述是源码与 SDK Service 替身范围结论，不证明真实 worker 已处理附加 marker，也不证明训练设备停止。

## 责任边界／维护性轴

**本轮所查边界无 finding。** 没有发现第二实验账本、调度器或批准 owner；未扩大六阶段、candidate／approval 或模板权限。取消意图引用原 start 的摘要，避免复制大 manifest；原 client 保留发送语义，adapter／executor 保留执行事实。训练没有依赖 Task 的创建／运行语义。

`reference_history.find_signal_event` 的算法与基线逐字相同，只有模块所有权移动；Task approval、Task cancellation、training cancellation 是三个真实生产消费者。`reference_training_runtime.observe` 由原 status 与新 stop-status 共同调用。CLI／HTTP 只传输应用层用例，页面新增模块拥有自身异步生命周期，未增通用事件框架或全局状态树。

## 已核证据与剩余验收

本轴实际执行了只读候选清单／长度／SHA、完整参考 Git 对象比较、共享 history 算法逐字比较和 `git diff --check`。283 个原参考文件均与基线完整字节相等；diff-check 退出 0、无 diagnostic。阅读原 `source-r1.json`／`source-r1.log`，确认四 suite 的 52 项通过／130.40 秒原记录；新增测试确实覆盖真实 SDK 的编码、单次 signal、attempt-before-send、丢 ACK／超时、原 history 认领、冲突归属、负停止事实和共享入口。没有为普通可见输入错误建议重复测试。

已阅读 r1 包身份记录及生成脚本：它记录 noneditable、568 个产品文件、两 RECORD／283 原参考核对通过；本轮没有重新独立验证该 wheel 全部字节。安装回归读取时仍在运行，155 项的收集／前段通过不能当作最终通过。

仍需同片补核：最终安装回归终态；真实 CPU 原 start→取消、真实已接收 ACK 扣留后的原 history 恢复与 worker／executor 观察；实际浏览器的确认、错误输入、双击、两类迟到回复和三视口；原模板自身审查；验收进程全部收尾。最终包或产品改变后需绑定新清单复核；普通提交／推送、完整远端 Ref 与本片自己的必要 CI 在发布后另核。

没有开放的阻塞代码 finding。**整片验收仍待上述实际证据，不关闭 F9b4、F9c／F9d、真实 B3 或完整 C2，也不新增 GPU、性能、数值质量、采用或整体外部停止成功主张。**

## r2／r3 与已完真实证据补核：通过，安装补测仍 pending

本次仍只读原件并更新本报告，未运行安装、服务、浏览器、模型或大 suite。基线不变。r2 仅修复窄屏长路径换行；其后 r3 删除 `reference_history.py` 末尾一个空行。独立核对 `static-r2.json` 的全部 20 个产品／测试／CI 路径与当前长度／SHA 一致，原组合 SHA 为 `a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`。完整 tracked diff-check 无 diagnostic；10 个 untracked 文件分别按 `/dev/null` 做 no-index whitespace 检查，均无 diagnostic。该命令因新增内容返回 1，不将这一退出码误作空白错误。

### 最终包与本地无 SDK 读取

独立从 zip、安装目录、打包源码快照与当前 `src` 读取全部产品字节，并重新计算两份 RECORD 和参考清单：

|候选|wheel SHA256|本轴实际核对|
|---|---|---|
|r2|`6dafb5b7060c631235fa296545a4e14f0133b55a49eb0e48f15a3a550a01407b`|568 产品、wheel RECORD 576 行／installed RECORD 581 行、283 参考全部通过；与 r1 只有训练根 class 和局部 CSS 两项产品差异|
|r3|`11cc353a2b0812e9f06503105a5ca69dff1a305eb7321d6961c9d4bc93bbd878`|568 产品、两 RECORD 同样通过、283 参考通过；全部当前产品字节与安装／快照相等，noneditable|

再逐项比较 r2→r3：唯一差异为 `reference_history.py` 删除 EOF 一个空行，另 567 项逐字相同；两版本完整 AST 相同。因此 r1 后端／测试旅程与 r2 显示旅程各保留其实际身份，不把先前运行冒称在 r3 全部重跑，也没有语义变化要求重跑这些旅程。

阅读最终 `observe-final-r3.py`、`sdk-free-r3.stdout`／空 stderr 与 `final-observations-r3.json`：实际 `-P -S` 子进程只显式装载包及原参考路径，先断言找不到 `temporalio`，再由原本地 owner 读取已关闭取消记录为 `already_closed`／`not_sent`、无 attempt。初次探针误把整个 site-packages 加入路径所致的失败保留；修后改变的是探针装载范围。该证据没有冒称 Windows OS 实测。

### 四个真实原 run 与执行器事实

全文检查 `native-r1.py`、实际扣 ACK helper、`native-r1/result.json`、四份原 history、四份 stop-status 及 cleanup。helper 先调用真实 `WorkflowHandle.signal` 并取得服务器回复，确认发送前 attempt 已在，再扣留回复并抛出 UNAVAILABLE；没有伪造接收。该 unknown 后由实际页面、在当前 spec 缺失时恢复为 history 投递证据。

本轴另以标准库逐份解码原 history 的全部相关 payload，重新核对保存的完整 Experiment、start memo SHA、原始 run ID、binding／reason／独立取消意图 SHA、signal event ID 以及原 completed Outcome；四个 run 都恰有一个 start 和一个 request_cancel。查询所得每 ID 唯一实际 run 与回执相符。直接取消、丢 ACK 恢复、prepared 意图继续和首次页面取消分别落在各自原 run，未交叉认领。

`cancel-ack`／`cancel-loss` 的原 Outcome 是 `CANCELLED`；`cancel-prepared`／`cancel-browser` 的原 Outcome 仍为 `CANCEL_UNCONFIRMED`。四个 stop-status 的 control 都与各自原 Outcome 逐项相同，后来四个原 executor 观察均为 `CANCELLED` 且原 fence 存在；没有合成为整体停止结论。四个 job 均无 `started.json`，原 executor 的 fence-before-start 路径返回取消；训练命令执行数为 0。25 份准备件在本次复核时仍全部与原保存 SHA 相等。已关闭工作流的独立额外请求为 `already_closed`／`not_sent`，没有多一个 signal。实际流程记录 440.370 秒，仅证明 CPU 控制／恢复合同，没有训练、GPU、质量或性能收益主张。

### 页面行为、布局失败与修复

已读 `browser-r1/loss.js`、`continue.js`、`lifecycle.js` 及相应原输出／退出记录和实际 HTTP 请求日志。loss 脚本使用 console 输出，原 stdout 没有独立 `Result` 区；脚本中的等待／断言已执行且退出 0，日志中该恢复 POST 恰为 1，实际本地记录和原 history 也共同证明恢复完成，不把缺失的 `Result` 区编造成额外产物。

已核实际缺 spec 的 unknown 恢复、prepared 继续、首次页面取消；错误 SHA／run 在客户端显示错误而零 POST，同步双击分别仅一个 POST。三条迟到路径均持有真实服务器响应后释放：旧 request-ID 的 GET、跨详情的 stop-status、跨项目的实际 closed POST 回执。新选择未被覆盖，closed 回执保持 `not_sent`。r1 HTTP 原件中相关四个 POST 各一个且均 200；r2 仅显示复核，没有 POST。

首轮 390 视口 scrollWidth 477 的错误、诊断和截图保留。修复限定为 `.training-workbench { overflow-wrap: anywhere; }` 与该训练根 class，无发送算法或其他页面权限变化。查看 r2 的 1440／960／390 三张实际截图及 `final.js`／`final.stdout`，缺 spec 的同一原记录和已恢复取消回执均可读，三视口 scrollWidth 分别等于 1440／960／390；未发送表单在 390 也无横向溢出。本轴只查看原截图，没有重开浏览器。

### 自身模板与收尾

两轮均使用已安装的原 `ergora-structure-review`／`root/review`，实际后端为授权 Codex 回退。独立核完整 packet 字节／SHA、保存的 input／prompt 与实际 stdin 相等，三份祖先／本角色资源文本均完整出现；原 result 与归档副本逐字相等、决策均为 approve：

- r1：24 个完整文件、318,975B、42.999 秒，result SHA `0798bcdd2ef80eb019652ac49c07df623ed086b00fc06ee1c3a15e4c7120163e`。
- r2：显示改动的 5 个完整文件、50,537B、23.219 秒，result SHA `d6ef2f6be708840cd5104de77886f53af440894f9a8663b38fbdfa9f261dc415`。

这些是完整材料的 text-only 自身调用，未冒称异后端成功或工具自行读取整个仓库。两个原回复都保留各自未验维度。r3 的 EOF 空行修正 AST 不变，不为它再发一次模型调用。

已读原生 temporal／worker／web 的进程 owner 取消回执、r2 web cleanup，以及两浏览器会话的 closed 回执；另实际只读连接探测 7233 和两个验收 web 端口，均不监听。此结论针对已结束的服务／浏览器／原生旅程；安装补测进程仍有自己的在途生命周期。

### 安装补测与最终出口仍待补核

独立核 r1 九 suite 的原 argv、600.027 秒 `cancelled`／-9 终态和原日志：155 个收集项中恰有 89 个逐项 PASSED，无逐项 FAILED，也没有完成摘要。`test-partition-r1.json` 的 155 项均唯一，89 个通过项与原日志逐项相同，剩余 66 项互斥且并集精确覆盖原收集清单。它们包含受影响的原 Task history 消费者，不借机械移动跳过这些调用方。复核时 r2 补测的 `result.json` 尚不存在，**66 项仍 pending**；不把部分通过相加成一个尚未完成的 suite。

最终公开 evidence／交付范围与分段安装终态仍待送核，普通提交／推送／精确 Ref 及本片自己的必要 CI 另待发布后核验。**本次已完证据补核通过，代码 finding 仍为 0；不提前关闭整片验收。**

## 最终本地出口补核：通过，开放 finding 0

已收到并核对安装补测终态及[最终公开证据](evidence/2026-11-14-training-cancellation.json)，本节更新上一轮 pending 状态，不改写原 r1 中断或先前包身份。

`install-r2/regression-r2/result.json` 为 succeeded／退出 0，wrapper 279.664 秒；原 pytest stdout 明确为 **66 passed／278.86 秒**。本轴从两轮原日志重新提取实际结果，宽容处理 pytest 的对齐空白：r1 恰有 89 个逐项 PASSED，r2 恰有 66 个逐项 PASSED，r2 原 argv 与剩余清单逐项相同；两集合无交集，并集精确等于原 155 项，既无漏项也无重复运行认领。r1 的 cancelled／-9／600 秒原终态仍保持；没有逐项 FAILED，也没有冒称 r1 完整成功。原 Task approval／cancellation history 消费者在这些实际分段中覆盖。

再次独立读取最终 r3 wheel 的全部 568 个产品文件，均与当前 `src` 完整字节相等；本节之前已独立核过源码快照、安装文件、两 RECORD／283 和 r2→r3 唯一 EOF 空行／AST 相同。20 个产品／测试／CI 路径重新按原组合算法得到 SHA `a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`，与 `static-r3.json` 相同。最终候选没有因收口文档而发生新的产品变化。

公开 evidence 为 12,929B，SHA256 `b1dcc3572ad74e43266b36bf865367b41591bbb3eff85d1fdea09dc8e6594478`。逐项重新计算其中 25 份私有原件的完整字节 SHA，全部相符；三包身份、原 native summary／四原 Outcome／history SHA、自身两轮结果、最终 package delta 与 SDK-free／收尾观察投影均与原件一致。公开记录明确区分 r1 真实运行、r2 显示与补测、r3 EOF 修正，没有把它们冒称在 r3 全部重新执行。

已读更新后的 PLAN、本片交付、总工作台接续计划和原分组收集结果。分组 5 的 351／1804、1453 deselected 与原 stdout／退出 0 相符，只是收集成功；不是额外 351 项执行通过。`static-r3.json` 保存当时 35 个改动路径／239 本地链接／完整 tracked＋untracked whitespace 和无私有机器字符串结果；本轴另对当前 35 路径重新检查本地链接、四种原禁入机器字符串及逐新增文件 whitespace，均无问题。报告的后续状态补记不被当成新的产品候选。

**最终本地需求／正确性验收通过，开放 finding 0。** 已完成的原 run／history 恢复、分别停止观察、共享入口、页面生命周期、打包与本地收尾满足本片 B3.1–B3.5；所查维护边界没有新增 finding。普通提交／推送、精确 Git 对象／远端 Ref 和本片自己的必要 CI 尚待发布后原件，不借前片 CI 关闭。Windows 原生实际操作、F9b4、F9c／F9d、真实 B3 和完整 C2 仍保持原边界；没有真实训练／GPU、数值质量、性能收益、采用或整体外部停止成功主张。
