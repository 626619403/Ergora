# F10d2 正式任务资料选择页面独立审查

审查者 `task_context_console_review`，fresh context；另按 `code-review` 将 Standards、Spec 各交给一个独立 fresh-context reviewer，只读审查后分别汇总。已读 `AGENTS.md`、AIHERO 索引、`code-review`、`codebase-design`、`maintainable-project-delivery` 与 independent-review brief；先核原始要求、[本片合同](../plans/2026-11-14-task-context-console.md)及实际差异，再看运行记录。没有修改产品、安装、启动模型、提交或推送。

固定基线及初审 HEAD 为 `0a311eeb2a46d0db48ec44515a8413239e0c772c`，分支 `refactor/architecture-foundations`；候选为未提交工作区。产品范围为 `src/ergora/data/console/task-composition.js`、`tasks.js`、`style.css` 与 `src/ergora/web.py`；同时核本片新增计划／交付及相关使用文档。前片 native-console 发布／CI 记账属于前片，不能转授本片验收。私有审查原件在 `.ergora/checks/task-context-console/independent/`。

**最终本地 Standards、Spec 两轴均 approve，开放 finding 0／0，R1 已关闭。** 最终 r2 包、相关原 suite、自身原模板、实际 HTTP 页面／生命周期、原件和收尾均已按下文范围独立核对。普通发布、完整远端 Ref 与本片自己的必要 CI 仍待，不能由本地结论代替。

## Standards

独立子轴与本 reviewer 均未确认单独维护性 finding。`taskComposition` 仍由 `tasks.js` 唯一消费；新增目录读取／失效函数是既有表单 owner 内的私有生命周期算法，没有新增公共抽象、仓库或意图账本。页面只收集精确来源身份；有效性、完整附件、资源容量、权限及资料模式继续归原 `task_context`／组合准入 owner。

新 `GET skills/heads` 直调原 `skill_assets.versions(heads_only=True)`；该分支仅检查项目并查询当前 head，不读取历史／完整版本或调用 dashboard／doctor。新增 sequence／active 检查保护真实异步目录、切换和销毁；未看到无关参数校验、后端自动回退或重复执行路径。原 schema 的32项上限与资源容量没有复制为新的页面限制。没有新增产品测试或为本片建立平行测试框架。

R1 修复复用原 `task_envelopes.selected_context`，以冻结树提供展示投影，避免页面另写 base64／目录解析与校验算法；仅有 context 的实际消费者进入该分支。现有后端、资料模式和权限支持矩阵保持由原 owner 决定。

## Spec

### R1：冻结披露缺少可审阅的来源与完整附件元数据（P2，最终关闭）

初审位置为 `tasks.js:312`。memory＋Skill 经 prepare 后进入冻结预览，新增“冻结项目资料与派生根来源”只显示 envelope.context 的 `project`、`base_manifest_digest`、`selection`、`resource_sha256`。实际冻结 memory 正文／source／有效期、原 `base_root`、Skill `provenance.files` 只在 manifest 的 base64 `selected-context/selection.json`；原 native lineage 仅显示派生根及祖先，不能替代原根来源和附件元数据。用户确认创建前无法直接核对这些冻结事实。合同明确要求“冻结预览增加原context来源、根派生和完整附件元数据，显示实际服务端结果，不用当前目录补写历史”。

Reviewer 读取 r1 安装实际原 suite 生成的 `test_selected_sources_are_inhe0` 完整 task.spec，核实四字段披露、原根与派生根、原 source 和 Skill 文件集合的位置；不是据模拟字段推测。最小修正已落实在原 `web.py` preview 路由：原 `tasks.preview` 返回 snapshot 后，以其 `task.spec.json` 调用原 `task_envelopes.selected_context`，添加 `selected_context` 展示投影；`tasks.js` 直接披露此冻结结果。不会读取当前 memory／head 目录，也不改原冻结文件、prepare／preview 摘要或创建请求。独立 Spec 子轴已复核关闭，最终 r2 安装、实际页面与原 HTTP 的冻结投影也已核对通过。

其余已检路径未确认 Spec finding：默认仅继承；显式目录读取后传原 id／revision、name／digest／revision 和新根版本；context＋source 保持 definition7，旧无 context 的1／2／3／6分支保留。来源／模式切换使目录失效，刷新成功清空勾选，失败保留输入但不能使用旧目录；父模板资料、权限和完整附件经原服务端冻结。manifest 输入变化沿原 editor 失效规则取消旧预览，原 manifest read 守卫拒绝迟到包；项目资料身份本身独立于 manifest，未证明缺少额外目录重置会产生错误授权，因此不将这一代码形状列作 finding。对话框／项目切换依原 active/current 检查，未知准备／创建结果仍按原 ID 读取而不自动重发。

## 已执行的独立检查与限制

已读四产品的完整 diff、唯一 caller、原 `task_context`／`task_envelopes`、memory／Skill head owner、definition7 schema、prepare／preview／create 双摘要、ui form/modal 与生命周期邻接代码；定向 `git diff --check` 通过。`review-scope-r2.json`／`product-r2.diff` 固定修后源码和原 r1 source snapshot 身份。

私有 `route_probe.py`／`route-probe-r1.json` 使用已有解释器导入当前源码，实际走 FastAPI TestClient 路由，三项通过：

- 新 head GET 与原 project-scoped owner 的结果相同，未知项目拒绝，逻辑数据库保持；doctor 被设为立即报错仍未调用。
- preview 的原编译函数由实际已冻结 fixture 返回值替身隔离；新增投影逐字等于原 `selected_context` 输出，含 memory source、原根与 Skill 全部文件。将实时 memory／head 读取设为立即报错仍通过，全部 `snapshot.files` canonical 身份保持。
- 无 context 的原预览响应不新增投影字段。

该探针只验证 HTTP 展示投影与轻量读路由，不代替原编译／准备、最终安装或真实浏览器验收。r1 初始原 suite 调用误列不存在的 `test_task_preparation.py`，exit4；作者已保留并修正调用，不当成产品失败或测试通过。本报告不借前片结果宣称通过，也不扩展为真实业务／GPU、原生 Windows、完整 Forge、F9d／G1 或复盘采用完整旅程验收。

## 修后 r2 安装与自身模板补核

Reviewer 独立逐件核当前源码＝r2 source snapshot＝wheel＝installed 的全部 **602 产品**，路径集合相同且 ZIP 无重复成员；两 RECORD 的 **610／615 行**分别逐行核大小与 SHA，全部 **283 reference** 的摘要和执行位相同。wheel SHA256 为 `bde460575dc23751552eb63933373b1ad9f3ed75fb03b62923ac7bed675e0058`，私有 `package-audit-r2.json` 保存完整逐件身份；没有重新安装。

|产品|字节|SHA256|
|---|---:|---|
|`task-composition.js`|19705|`cb2dec85fdff53969e38a8e9ec7d61cd6041e055ce1604c904043edcd909836b`|
|`tasks.js`|85593|`2276eaa713e848962ae6a149be8efab144d4c8fadec1374a0296f06b3c66b46b`|
|`style.css`|20913|`72e3133415a00a45728a6ae295f1a6fb63096e937e065112e516410935d3d54f`|
|`web.py`|45971|`fda54f19ddb68c8e3f7370821377f198a8eb8cec651551c7315207a845701dc4`|

直接读取原 stdout／进程回执：r1 修正后的五 suite 为 **93 passed／352.03秒**（runner 352.930秒），覆盖原 web、native six-stage、tasks、budget、creation；属于 R1 展示修复前 r1 身份。最终 r2 安装件原 `test_web.py` 为 **9 passed／12.17秒**（runner 14.011秒）。没有把 r1 的93项记为 r2 重跑，也没有为前端展示重复运行全部原后端 suite。

自身原结构模板以已授权 Codex 后端运行 `9543f59320e747bb896a3c08f769a835`，**53.6616秒／approve**。Reviewer 的 `self-audit-r1.json` 逐块核八份完整 inline 文件 **191996B**：四个变更产品与未改的 ui／task_context 六份源码均与当前相同，两份进度文档保留调用时身份；完整 task 在实际 prompt 内，全部父链／自身 instruction 与 Skill 资源在实际 stdin 中。prompt **196465B**，SHA `bb7a8ee11a3dceafa39c47f68242ce3c49f8c769bdc51acb286235f8e52b040d`，原 prepared／run prompt 与实际 stdin 相同；结果 SHA `73ecda7563e446edcd246af6e5f043eb862c55dc3b38659685419acbca4e279d` 与原 result 副本一致。该模板明确只审所供源文件，不能替代独立审查、完整浏览器或真实任务执行验收。

## 最终页面、原件与收尾终核

最终产品仍是上表 r2 身份。作者的实际页面验收保留所有早停及恢复：`browser-main-r4` 在 **42项／19.752秒** 后因 APIRequest 相对 URL 探针错误停止；此前已走完整 memory＋Skill＋source 的 prepare→definition7／input11 预览→双摘要发布、完整下载、空选择、错误根和 Skill text-only 拒绝。随后缺本地请求头的403及全局同名按钮定位早停均保留；最后 `browser-main-resume-r3` **26项／20.855秒** 通过，按原 ID 读取已经拒绝的创建而没有重发，再核同 digest 新 head revision、墙钟到期、完整大正文容量拒绝及无 context 的 definition6／input10、project1。这里记录已执行的完整旅程与接续结果，不把任何早停 run 改写为完整通过。

独立 `http-audit-r1.json` 与最终 `local-final-r1.json` 逐份核三服务 **200份**原 HTTP 元数据、响应和 ASGI 已消费请求的大小／SHA（**7／37／156**），与各自 trace 完全相符；一份403在消费 body 前拒绝，空 capture 不能证明网络未发送 body。**7份**含 context 的原预览投影逐字等于原 `selected_context` 从该次冻结树解出的结果。两个服务的成功发布各有 **7份**冻结 JSON，全部与各自原预览相同；原授权下载解析后等于原 definition，prepare／preview 双摘要和完整 source 身份保持。每个服务内的各明确 prepare／create ID 均只发送一次；调试期间不同服务的同名 ID 分别计数。

最终 `browser-lifecycle-r2` **24项／6.211秒** 通过，四个实际原 HTTP 读响应 hold 对应 trace120／128／132／139：资料模式切换、任务来源切换、关闭并替换对话框、跨项目均不能复活旧目录；目录读取失败禁用原勾选，成功重读清空勾选，旧 finally 不锁新读取，未增加 prepare。三宽1440／960／390的内容／scroll为 **688／688、688／688、352／352**；reviewer 已直接查看三张原截图，资料长 ID 在窄屏可换行。键盘仅核资料模式→根版本→目录读取两段 Tab 顺序；原安全文本和无页面错误检查通过，不称完整无障碍验收。

Reviewer 另外直接读原 worker stderr，错误根、资料模式与容量分别为 `new root_version`、`Complete Skill attachments require task-mcp`、`material_bytes budget exceeded`；失败记录保持 failed／cleanup_confirmed，页面未换后端、扩大权限或截断完整正文。

`local-final-r1.json` 独立以只读 SQLite 核三服务共 **18份**原工单快照（含完整正文和首次观察时间）保持；六份原 Skill 的全部文件和执行位、九棵原 manifest 的全部文件、目录及执行位保持。30份原 memory revision 按原合同核对：未删除者保持，删除者由既有 `memory.delete` 清空所有 canonical 历史正文／source 并标 deleted；已冻结的任务资料保持原字节。最初私有探针误将 canonical 历史一律视为不可变，在该额外断言中止；`local-final-r1-failed.json` 保留该探针失败，修正为原删除合同后通过，没有改产品或旧原件。

三服务的四类任务／关联表均为0，九个 fixture Git 均干净；无 task-submissions／requests／workspace／ingress／receipt 执行树，外部夹具 provider 只有原 GET 且调用数未增加。三组原 PID＋starttime 均已消失，六个原 loopback 端口连接拒绝，各浏览器 close 回执 exit0。此为本片拥有的服务与资料收尾，不扩展为全部宿主进程或 OS 隔离认证。

公开[证据索引](evidence/2026-11-14-task-context-console.json)终核读取时共有 **872引用／30,805,552B**：原871件保持，另增加尚未执行的普通发布脚本。Reviewer 逐项核所有路径、大小与 SHA，无重复；该时刻索引 **162315B／SHA `5650d9cb5c6a5834f4cffcf371a581a7309ef069126171c2217db9c71780f4c6`**，仍正确标记最终独立终核在途，随后由本报告结论作状态记账。新私有 `local_final_r1.py`／`local-final-r1.json`／`local-final-r1-failed.json` 未覆盖该固定前缀，后续可只追加原件引用。

**最终裁定：Standards approve，Spec approve，开放0／0；R1 关闭，本片可进入原普通发布流程。** 目录与 manifest 同时变化、Home 切换、迟到 mutation 在本片仅静态追踪，旧2／3与 unknown mutation 原动态证据属于前片；本片不声称完整动态矩阵。未提交、推送或核本片自己的 CI，不证明真实业务／GPU／质量／性能、原生 Windows 模型、完整 Forge、F9d／G1 或复盘候选／评价／采用完整页面旅程。
