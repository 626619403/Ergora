# F7d-D3c 独立审查

**最终本地判词：完整19件候选的 Standards／Spec 均通过，开放 finding 0／0；Spec 累计 SP1／SP2 两条 P2 均已关闭，Standards 累计0条。** 修后 r3 包、实际页面分段、143份原 HTTP、两轮模型全文链、四份公开证据与所属资源清理均已核。本片 W4 普通提交／推送、精确 Git／Ref 与自身双 OS 必要 CI 仍待，不借 D3b 结果。

本片新 fresh-context 协调者 `f7d_issue_writeback_console_review`，Spec 与 Standards 分别由新的 `fork_turns:none` 子审查者完成。按 AI Hero `code-review` 原始双轴模板，结合 `maintainable-project-delivery` 和 `codebase-design`；上一片审查结束、并发槽释放后补齐第二轴，没有复用旧片判词。仅只读源码、必要调用者和原证据，并写本报告。

固定基线与终核 HEAD 均为 `18585dccf067c28e1c444df0c8daaa040b038568`，`BASE..HEAD` 无提交。针对未提交工作区，检查 `git diff BASE -- <清单中的 tracked 文件>`，另逐件读取 new 文件全文及图片。最终19件范围为：三件 console 生产文件 `issue-writeback.js / tasks.js / style.css`；README／PLAN／USAGE／当前架构四件；本片计划／交付／本报告三件；总计划／F7分片计划两件；本片 acceptance／self-review JSON及桌面／移动PNG四件；前片 D3b 计划／交付／原 review 的 R4 状态记账三件。本报告不要求递归审查；D3b CI归属仅按原片记录核对，没有转授本片。

两原轴最终均按 `candidate-files.json` 的19件终核。生产文件最终 SHA256 为：新 JS `f79f44be07e003e3551bcce6d62a85e3b4bbea10d5667842c45870fffc1b04e2`、tasks `c7d9f2cba0281cec21bc7649e19853b223b497abb8cd78f62789c72e2ddde1c2`、style `962c3436cb64a08c655c0f31d01dfff0b4451f3bde7d8871d12366acb4115435`。[规格](../plans/2026-11-12-issue-writeback-console.md)与[交付记录](2026-11-12-issue-writeback-console.md)保留原失败与逐候选范围。

## Standards

最终 **通过，开放 finding 0**：未发现文档硬规范违例或有具体后果的 Fowler smell。规范源包括 `AGENTS.md`、`docs/PLAN.md` 持续工作规则、当前架构／reference 边界、ADR 0001／0002 及实际包配置；第一方未发现 `CODING_STANDARDS.md` 或 `CONTRIBUTING.md`。检查包含原始十二项 smell baseline，并将其作为判断提示，不作硬禁。

`issue-writeback.js` 只有 `tasks.js` 一个真实生产调用者。它将准备／原字段恢复、状态读回、明确发送和有界观察的完整交互放在一个 Module 中，外部 Interface 只接收固定上下文与存活条件；删除后这些选择、忙状态和回复隔离会回到 tasks。该职责和 Locality 足以支持拆分，没有虚构复用、通用 provider 协议或第二账本。

`active/current/sequence/busy` 分别处理窗口与父上下文失效、旧回复及工作区串行；HTML 输入约束属于操作者输入，原业务身份、修订、单 attempt 与 unknown 继续由既有 owner 负责。没有新增永久 test、CI、依赖、后端、schema 或 table；复用 api／ui 及原五个 HTTP 用例。修后只补受影响页面与聚焦模板，原四 suite 不因纯 UI 修正重复，验证成本合理。

最终两份公开 JSON 的31组映射吻合原件，覆盖21样本、五 hold 与96→94更正、包／清理和两轮模型；两张PNG字节／hash相同且已查看。文档保留失败段与生成时 pending 快照。143 HTTP中15个明确本地 POST 的 owner 计时最小0.0106／中位1.505／最大2.360秒，止于故意 hold 前；provider 的26 GET、2只读 GraphQL POST、3次 loopback 业务写分别记录，没有将全部POST或本地时长扩大为SaaS行为。

## Spec

最终 **通过，开放 finding 0**。独立首轮发现 **1 条 P2／SP1**，本工具自身首审另发现 **1 条 P2／SP2**；两条均已由原 Spec 轴按修后精确源码复核关闭，实际 r3 页面覆盖两项修正。最终19件未发现剩余规格缺失、范围扩张或实现错误。

- **SP1／P2，已关闭：发送回复失败后可借原 prepare 恢复绕过 GET。** 规格第13行要求“任何发送回复失败先明确GET原意图状态，不重复send”。首轮 `issue-writeback.js:175` 添加的“恢复原准备请求”在准备成功后仍保留，成功分支 `151–152` 未移除 recovery；按钮经 `149` 的 POST prepare 直接 show 返回记录。可达场景：准备成功 → send 未抵达服务器或回复失败 → 点击该按钮 → 既存记录仍为 prepared → 再出现发送确认，全程没有 GET 状态。最小修正已落地：共同 `show` 入口先清除 recovery，准备或 SHA 读取成功都去掉旧 prepare 恢复，准备失败仍保留原字段的明确恢复。原 Spec 轴先核修后 JS `3a0bb32f3a2ef784d94e60ffbe79fc8936893b93dfbe6b9a80a702eb3e2cf68d`，最终在 f79f44be 源码与 r3 页面保持关闭；actor漂移拒绝及标签单mutation已ack后浏览器回复丢失均只留 GET 恢复。
- **SP2／P2，已关闭，发现归属为本工具首审：观察输入编辑保留旧发送确认。** 规格要求观察输入编辑使旧回复／发送入口失效。首审冻结候选的 `observeForm` input listener 只清旧观察，prepared 的发送确认仍通过原 `current(reading)`。可达场景：读到 prepared 后改评论 ID／页码／范围或标签 cursor，仍可提交旧发送确认。最小修正已落地：输入编辑更新代际并移除确认，旧发送闭包继续绑定原 reading；当前观察／GET 重读使用更新后的 selected。原 Spec 轴核修后 JS `f79f44be07e003e3551bcce6d62a85e3b4bbea10d5667842c45870fffc1b04e2`，确认旧确认失效且查询可继续，unknown 仍无发送入口。该条来自已直接核读的 `self-review-r1/review.md` 与 `original-result.json`，不冒称独立首轮发现。Standards 轴也核同一修正，无新增重复 guard 或职责问题。

## 已核原件与限制

原件位于本片私有检查目录 `.ergora/checks/f7-issue-writeback-console/`；本报告不复制运行目录、账号状态或凭据。

- `r1/package-identity.json`：451 个包文件、wheel 456 件、installed RECORD 461 行；非 editable、两 RECORD、283 冻结身份通过。协调者直接比对三件 changed JS／CSS 与 r1 安装副本，SHA256 完全相同；首轮 JS 为 `9c5fa69a94b2621ed965aed850ea40fa8f8a49fb1be422300485ad556ec221d9`。
- `r1/installed-tests.stdout` 与 `installed-validation.json`：原评论／标签、Web 与架构四 suite，76 passed／pytest 108.38 秒，命令 wall 110.69 秒；reference verify PASS、283 件、未启动 runtime。这只证明该 r1 候选及上述检查范围。
- `seed_native.py`、`r1/seed.stdout` 与 `seed-receipt.json`：GitHub／GitLab 两个原生 v7 发布、start 与 Git 导出种子，2 passed／pytest 21.96 秒，命令 wall 22.95 秒。Temporal SDK 受控，REVIEW_READY 为合成，不是新六阶段、模型或真实 SaaS 验收。
- `self-review-r1.json`、原判词与 `self-review-r1-read-audit.json`：实际内置结构审查模板以授权 Codex 回退执行，184.71 秒 request-changes；九件完整附件共197240B，五 scope 连续 UTF-8 读取至 null，四个采样进程无存活。协调者直接从原 stream 重建五 scope 共198758B，并交叉核 prompt／附件／原结果；判词只属于修前冻结候选，不转授修后页面／最终候选。
- `self-review-r2.json`、原判词与读取审计：聚焦实际模板98.17秒 approve，只覆盖列出的五件修后完整附件51085B。协调者另从原 stream 连续 UTF-8 重建五 scope 共52603B，并核 prompt／附件／原结果一致；四个采样进程无存活。未把该聚焦判词扩大到未附调用者、页面或最终公开资料。
- `r3/package-identity.json`：新修后非 editable 包451／wheel456／installed RECORD461／283冻结身份通过；协调者直接比对修后 JS 与安装副本，均为 `f79f44be07e003e3551bcce6d62a85e3b4bbea10d5667842c45870fffc1b04e2`。r1／r2服务清理原件均无 provider 方法且原来源／runtime保持，没有将早期包当作实际页面候选。
- 直接比较三轮 wheel：r1→r2 只有新 JS、METADATA及RECORD变化；r2→r3只有新 JS与RECORD变化，其余450件包文件保持。r3 METADATA中的README正文等于当前README，没有把早期包身份覆盖后补文字。
- `browser-main-r3.js` 与原结果：56项／41.06秒、16样本、pageerrors 0。实际覆盖两平台普通评论、GitHub 丢失原生回复保持 unknown、匹配／空页／ID观察不确认、精确标签／actor漂移拒绝／单 mutation 后浏览器丢失且 GET恢复、GitLab 标签 unsupported、独立 SHA 与跨项目拒绝。16样本逐个映射到服务捕获的原 HTTP request／response，hash与长度均核。服务只复活原 loopback 来源，未替换产品 routes／owners。
- 生命周期首驱动0项／4.98秒跨域控制 fetch失败；续段20项／39.06秒后等待离线展示超时，仍为 passed:false。20项保留SHA编辑、同表单忙、先新400再旧200、关闭／替换、项目／视图替换及修订拒绝的实际范围。五条真实 held 原HTTP为94／99／101／102／113，均明确 gate release；驱动首条把并行任务详情96当作最后一行，公开投影保留原reported96并更正actual94，没有改写原回执。
- 新稳定窗口3项离线核验成功，原task不可读、token移除、provider离线且当前tracker改绑时完整原意图／收据仍可页面GET，平台读取0；该段31.76秒后因驱动等待overview中的任务标题超时，仍为 passed:false。另续验7项／4.20秒通过，完整JSON与安全文本、原标签acknowledged及1440／390两视口均核；已查看两图。未把分段检查相加为单次无失败运行；task／run其他组合只由原caller静态复核覆盖。
- `cleanup-audit.json` 与原HTTP／before／after／trace：协调者只读逐件重核143份原请求／响应的SHA与字节数；四段共21样本均映射原件；88runtime／56repo、两完整source、去动态revision的export保持。另用只读SQLite直接核三份原intent／attempt／result与主页面原样本一致。所属三服务PID／starttime无同一存活进程、线程停止、八端口关闭及命名浏览器close退出0以原清理回执为证，不推全系统。
- [公开验收投影](evidence/2026-11-12-issue-writeback-console-acceptance.json) SHA256为 `94c15639cf5eb5669f88c2c9528e7ad4f3f5d643944e8f4e09aaec2a0404edbf`；[公开模型投影](evidence/2026-11-12-issue-writeback-console-self-review.json)为 `91a4fee986ffd1b736c58851dc69f30325683358aa8c19121bdb1eebd7d725fe`。按生成脚本全部映射与私有原件逐字段核同；两PNG与原图逐字相同。acceptance生成时的review-pending状态保留，最终结论由本报告和交付记录承载。
- 作者 `static-r2` 覆盖当时19件／351本地Markdown目标／6个加载秘密值，issue0、whitespace通过；评审未读取秘密值。该证据不覆盖anchor、外链或Mermaid渲染。本报告最终追加及后续状态收口会改变文档身份，冻结前须保存最终静态身份，不为状态记账重复产品或模型。

本轮没有运行产品／suite、安装、浏览器或模型，未联网或提交，仅核原件并写本报告。真实 SaaS、新模型六阶段及原生 Windows 正式工作区不在本片验收范围；祖先资源／权限与原六阶段、候选、attempt-before-send及未知恢复所有者保持。本片 W4 仍需普通提交／推送、精确 Git／包／Ref 与本提交自身双 OS 必要 CI 原件终核。

Standards 累计0、开放0；Spec 累计两条P2已关闭、开放0；完整19件独立本地审查通过，W4精确交付待完成。
