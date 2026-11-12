# F7d-D2 来源任务页面独立审查

审查日期：2026-11-12。协调者 `f7d_source_task_console_review` 为本片新的 fresh-context 独立审查者；Spec 和 Standards 分别由两个 `fork_turns: none` 子审查者读取原始要求后完成，未继承作者讨论。依据为 AIHERO `code-review`、`maintainable-project-delivery`（含 independent-review）及 `codebase-design`。

**最终本地判词：完整20文件候选的 Spec／Standards 均通过，开放 finding 0／0；SP1/P3 状态记账已修正并由原 Spec 审查者复核关闭。包、安装检查、实际页面、内置审查全文读取、公开投影及拥有资源清理已核。** 普通提交／推送、精确 Git／Ref 和本提交自己的必要双 OS CI 尚待后续交付，不借前片 D1 的 CI 关闭本片。

## 固定范围与身份

项目及文档归属均为 Ergora；原始规格为[本片计划](../plans/2026-11-12-source-task-console.md)，实现／验证状态见[交付记录](2026-11-12-source-task-console.md)。基线及此次静态审查时的 HEAD 都为 `d60a9d82be80a52d3e6ca0257772af3b3a26a084`，`git log <baseline>..HEAD --oneline` 为空。因此实际审查对象为 `git diff <baseline> --` 加全部 untracked 正文；不以空的三点提交差异代替工作树。

最终清单与实际 **13个 tracked 差异＋7个 untracked 文件** 完全对应，共20件；文本差异、新正文／JSON、两张公开截图均已检查：

- 页面源码3件：`src/ergora/data/console/app.js`、`issues.js`、`tasks.js`。
- 入口／当前架构4件：`README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`。
- 上层计划2件：`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-11-project-trackers.md`。
- 本片新增7件：`docs/plans/2026-11-12-source-task-console.md`、`docs/delivery/2026-11-12-source-task-console.md`、本报告，以及 `docs/delivery/evidence/2026-11-12-source-task-console-{acceptance,self-review}.json` 和 `2026-11-12-source-task-console-{desktop,mobile}.png`。
- 前片 D1 记账4件：`docs/plans/2026-11-12-issue-console.md`、`docs/delivery/2026-11-12-issue-console.md`、`docs/delivery/2026-11-12-issue-console-review.md`、`docs/delivery/evidence/2026-11-12-issue-console-acceptance.json`。它们属于 d60a9d8 的交付／CI 记录，不作为 D2 的运行或 CI 证据。

最初两轴静态范围为8件 tracked＋2份新正文；同片最终复核已扩大到上述20件，新增材料未借旧模型判词覆盖。审查报告和后续状态记账不要求递归审查。

相邻所有者已核 `ui.js`、`api.js`、`state.js`、`task-composition.js`、`tasks._definition / _composition`、`issue_snapshots.snapshot`、`issue_sources.bind_snapshot`、既有 HTTP 路由与 `task-definition-v3`。亦核既有创建／恢复、受影响测试及唯一 portability 工作流；未改源码、安装、重跑产品／模型或写入外部平台。

## Standards

**最终审查通过；硬规范违例0，AIHERO possible smell 0。**

已按 AGENTS、两技能及 independent-review 核对完整工作树。app 只临时承接 SHA；来源表单及新私有函数留在 tasks owner，复用原 snapshot、composition、definition3 与创建／恢复路径。未读取来源、缺执行组合、迟到回复等 guard 均有可达保护对象；未复制 provider 准入或状态机。

新增 `resetSource / loadSource` 只服务本对话框的资料和生命周期，适合保留在现有 owner；没有据同文件重复调用虚构跨文件复用。`sourceSequence` 保护来源请求代际，原 `sequence` 保护冻结预览代际；它们分别处理不同的在途请求，不能据外观相似删除其中一个。

每次显式来源读取只有一个本地 GET，无新增轮询、全量循环或持久缓存；未新增 test、CI 或依赖，无本片重复运行设计。完整文本展示沿原安全 DOM helper。首段驱动中止后仅沿原 ID 续验，截图补段只补视口；没有为记账变化重复产品或模型。下文脚本耗时是其实际旅程范围，不推为稳定性能基准。

本轴只读，未安装或跑测试。最终20集合、公开投影／两图、生命周期／清理及模型范围已核；源码仍等于 r1 包和安装副本。当前记账补充不改变产品及原测试范围。D2 未交付自身提交／Ref／CI，本轴通过不关闭精确交付。

## Spec

**最终审查无产品缺项、产品越界或高置信实现错误；开放 finding 0。**

原规格第7–11行对应的临时 SHA 导航、显式完整离线读取、固定工单编号、definition3 与无来源 definition1／2 路径均已核。`tasks.js:194–202` 在同 SHA 已读取且有执行组合时提交 definition3；完整准入继续由原 schema、`tasks._definition` 和 `bind_snapshot` 拥有。

`sourceSha` 的 input 先重置来源，再冒泡到原表单的 input handler 使预览失效；清除按钮显式完成两者。来源读取由局部代际、creationLocked 及 dialog/content/view 存活保护，关闭重开替换 content；切项目的原 refresh 同步替换旧 view。正文沿 `node / pre` 安全文本显示；创建及未知结果继续沿原 ID 的 creation／resume，没有隐式执行或来源回写调用。

D1 的精确 Git／Ref 与 CI 各次样本单独保留。其原评审者已在原报告终核 CI43142680273 的11份原 body／收据及双 OS 七必要步骤并关闭 D1 精确交付；协调者已读该状态追加，不计作 D2 运行或 CI 证据。原规格第7–11行的实际页面行为、完整来源及旧对象保持已由下文原件补核。未知创建实测为已发布后的原 ID 读回，没有触发 pending 页面的 `resume-create`；不冒称本轮浏览器覆盖了该分支，原实现未改且相关既有安装套件已核。

**SP1/P3 已关闭：** 最终审查时计划第20行的 S1 仍写“待安装及页面验收”，与 S2 完成状态矛盾。最小修正为“已实现，安装及页面验收见S2”，原 Spec 审查者已核当前字节。此项为状态一致性问题，无需重跑产品。

## 包与安装验证

r1 wheel SHA256 为 `2773db5b6d67c09aab13893662ae538a95a6256cfade19bd5339ca8defc1e42d`。协调者独立从原文件重算：448件 source／installed 包文件集合及字节完全相同；wheel RECORD453行、installed RECORD458行的逐件 digest／size 无误；reference manifest 的283件冻结文件身份一致。三份改动 JS 的 module 语法检查与基线工作树 `git diff --check` 通过。

直接核读 r1 的 `installed-validation.json`、stdout 和 reference 原件：`test_issue_tasks / test_task_creation / test_web / test_architecture_boundaries` 共 **65 passed／pytest 110.52秒**，命令收据 exit0／113.11秒；`reference verify` exit0。两份 stdout SHA256 均与收据相同。没有重复运行这些检查。

## 实际页面、旧资料与清理终核

已读取驱动、原 stdout 的 Result、结构化结果及原 HTTP，而非只接受汇总布尔值：

- 首次默认 Chrome 不可用而退出，未跑产品；使用已有 headless 配置后成功，未安装软件。主段 **22项／8.78秒**后在私有 fieldset `isDisabled` 判断处中止，原失败保留。原 DOM 表明 fieldset 原生 `disabled`／`:disabled` 和内部 input 的有效禁用均成立；实际来源创建已发布，但回传被故障夹具替为503。
- 原 ID 续段 **21项／7.01秒**通过，查原 creation 得到 published 并进入正式任务详情，没有重发创建；补完 GitLab 大变更、缺来源拒绝、未登记提示和390px范围。两 provider 的完整安全来源、definition1／2／3 与 input6／7 各按实际步骤保留。
- 生命周期 **41项／11.34秒**通过。五处经过真实 HTTP 的浏览器延迟回复分别覆盖 SHA 编辑、清除、关闭重开、切项目及旧预览。修订变化明确拒绝；刷新后捕获修订2与执行修订3分别保留；改绑 manual 后历史仍完整可读，但来源正式准入拒绝。最终两视口截图补段仅 **2项／1.65秒**，未重跑前述旅程。

协调者独立重算全部 **120份 HTTP 请求／响应原字节、大小和 SHA**，与逐件收据及 trace 一致。13次本地 POST 恰为10次 preview＋3次原创建；三个创建分别为 `legacy-source-ui`、`source-gh-ui`、`source-gl-ui`，原 definition、revision、intent、preview 及七份合同内容一致。合同摘要按原规范的 canonical JSON 核对，不误称文件格式字节摘要。来源 v7 envelope 与原完整来源、preview 全文相同，来源创建503没有增加第二次同任务 POST。

使用只读 SQLite 连接核对六份旧快照的完整 payload、SHA、首次保存时间不变，并核原两份完整 manifest 树不变。外部 provider GET 总数仍为准备阶段的6，浏览器新增0，方法只有 GET。Agent／task-link／review-link／writeback 四表均0；运行队列、回执、产物、workspace、submission 不存在，原运行目录只有合同／创建记录。

拥有服务 PID＋starttime 已退出；两端口再次只读探测均关闭，原 HTTP／provider 线程停止，命名浏览器 close 收据 exit0。清理结论仅针对所属进程、端口、线程与浏览器，不推广到全系统。

## 内置模板完整读取与公开投影

实际内置结构审查 run `7c9365f47cdc4c9a94848b4ed75ee617` 为 Codex／gpt-6.1-sol／high，**approve／155.40秒**。协调者用原 installed inspector 核 manifest、prepared 和 actual 身份，再独立比较 prompt／stdin／protocol、admission binding／policy、scope/native 收据和原结果。原模板只增加局部版本、证据资源和材料限额，原提示／Skill 字节保持；没有正式执行授权。

从原 native 流核到1次 list 和13次 read：五 scope 均连续 UTF8 到 null；120,396字节附件由7页完成，两次 base64 回应在同 offset 缩小重读，失败调用0。八件完整附件的封存字节／长度／SHA 与原 index 相符；其中六件源码／schema 仍等于最终源码，两份计划／交付只代表冻结时刻。原结果 SHA256 `4826e5dad414510eb903885491c22041c554ab2f3da0e1eb8b300f3e7c428e54` 与原回执及公开结果相同；四个采样所属 PID＋starttime 无存活。模型范围没有扩大到后补公开文档、包、测试、浏览器或后端独立性。

公开[验收投影](evidence/2026-11-12-source-task-console-acceptance.json)逐字段等于原包／检查／分段浏览器／清理原件的对应字段，保留失败及分段范围；[自身投影](evidence/2026-11-12-source-task-console-self-review.json)等于去除私有路径后的原 identity／audit，original_result 完整相同。用量保持后端自报；cached input 为输入子集，不重复相加，不推费用、模型理解质量或成功不同后端独立性。

两张公开图已实际查看并与 final 原 PNG 逐字核同：桌面1440×1000／268,069字节／SHA256 `408633b13f143c1f872c9d0b73e51cb49bc0eae955c06a5bbe5d8606eb251a06`；移动390×844／80,567字节／SHA256 `28b984c74c59aea1b4ac70892c5b864de6a99e1b56ffe3969bddb2331845bd54`。完整 SHA 与来源可读，HTML 外观标题原样显示，正文通过原文本区域完整可滚动读取，不据截图推断真实平台兼容。

## 最终静态与交付边界

作者 `static-r1` 原收据覆盖20件、345个本地 Markdown 目标、6个当时加载的秘密值，JSON／whitespace／个人路径检查 issue0。协调者核对该收据的完整文件身份与实际20集合；之后 S1 更正、D1 CI 进展及上层／本片审查记账属于已读状态补充，不把旧 hash 当最终冻结字节。最终冻结前由作者补核相应静态身份；没有读取凭据值，也不把上述检查称为 anchors、外部 URL 或 Mermaid 渲染验收。

本轮未重新安装或运行产品、浏览器、Agent／模型。未验证真实 SaaS、原生 Windows 正式工作区执行、OS 隔离或重新运行六阶段；未取得 D2 自身提交／Ref／必要 CI，精确交付继续。D1 后补 CI 由其原评审者处理，范围不转授 D2。

**最终汇总：Standards 0项；Spec 共1项记账P3、已关闭、开放0。完整20文件候选的独立本地审查通过；普通提交／推送、精确 Git／Ref 和本提交自己的双 OS 必要 CI 待交付。**
