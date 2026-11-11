# F7b.0：工单快照与显式上下文关联独立评审

日期：2026-11-11。评审协调者为本片新的 fresh-context Codex；按 `code-review` 再启动两个各自 fresh-context 的 Spec／Standards 评审者。初审先读原始要求、[本片规格](../plans/2026-11-11-issue-mapping.md)、[原只读设计](../plans/2026-11-11-issue-mapping-design.md)及实际源码，不以作者交付、自身模板判词或前片 F7a 审查替代本片结论。

基线 `9f010079126f374c01272ecf2f0ec85284e4e2cc`，分支 `refactor/architecture-foundations`。评审时 HEAD 即基线，三点 diff 和新增提交为空；实际对象为 `git diff <baseline>` 加全部新增文件。初始完整 25 文件冻结清单 SHA256 `108d382a3d0ab9b90d0ae68d79cf1d41852eaad471b3059731bf76effdce4004`；同片最终完整 28 文件清单 SHA256 `c4f170540588a80c760d9d3fcc8bc0ab5ce9f28e34ccbd510c971b9a8e731042`。逐件核大小／SHA 及 initial→final 全部实施差异；后者新增本报告和两份公开投影，评审收尾／状态记账不递归审查。

**最终本地审查通过：Spec／Standards 开放 finding 各 0；原 SP1／P2 与 ST1／P3 均关闭。** 此结论覆盖本片实现、受影响证据、实际自身模板范围及最终公开投影；普通提交／推送、精确远端身份和本候选自己的 CI 尚待作者完成，不表示精确交付或项目整体完成。

完整初审对象：根 README；PLAN／USAGE；当前架构、身份与迁移三文；F7a 两交付文与分片计划、总计划；本片新增规格／设计／交付；`backups / cli / contracts / issue_backends / issues / state / web` 七生产文件；`test_agent_definitions / test_issue_mapping / test_project_issues / test_state_backups / test_state_migrations` 五测试文件。另读 AGENTS、ADR0001／0002、实际项目配置和原 `tasks.creation`／reference creation 调用链。

## Standards

初审文档 P3 一项；**同片最终 Standards 通过，ST1 关闭，新增／开放 0。**

- **ST1／P3，已关闭：交付证据链接锚点失效。** 初始 `docs/delivery/2026-11-11-project-trackers.md:46` 使用 `#f7a普通提交后的精确身份与ci终核`；目标文只有“同片精确交付终核（2026-11-11）”标题，没有该锚点。读者无法跳至所引用的精确交付证据，违反交接前核文档链接规则。最终已改为 `#同片精确交付终核2026-11-11`，Standards 轴逐项核对目标现有标题通过。

CLI／HTTP 共用 `issues` 五用例；厂商选择留在 `issue_backends`，新关联复用 `tasks.creation`，State 持有迁移／writer fence，备份器调用领域校验。共享算法有实际消费者，内部摘要／游标属于本域职责；没有泛用存储层、上层厂商分支或第二调度器。输入／游标／修订／持久记录守卫有可达失败。最终两次自然键查找分别保护普通重放与并发先落库窗口，使用已有索引；写保留已排除竞争，删除 link INSERT 的冗余 ON CONFLICT 分支合理。新增真实 creation 确定性交错回归补充原并发测试没有覆盖的窗口，有独立价值；未新增 CI 或发现应删除的同构测试。Fowler baseline 作为判断启发，本范围未提出额外 smell 或有证据的性能问题。

## Spec

初审 request-changes、P2 一项；**同片最终 Spec 通过，SP1 关闭，新增／开放 0。**

- **SP1／P2，已关闭：原请求重放被提前拒绝。** [规格](../plans/2026-11-11-issue-mapping.md)要求“重复同语义操作返回原记录”，只要求“新关联在保存前再核当前修订”；[原设计](../plans/2026-11-11-issue-mapping-design.md)要求重复优先返回原记录。初始 `src/ergora/issues.py:173`–`183` 却先核 `_revision`。保存关联但响应丢失、绑定令修订 2→3 后，原请求 revision=2 重放会被误拒；初始测试改用新修订 3 而漏掉此例。最终 `issues.py:179` 首查自然键，`:194` 取得写保留后再次查重复；命中均先返回原原因／时间，真正新关系仍核当前修订和精确 published creation。Spec 轴独立内存 SQLite 确认原 revision 重放成功、旧 revision 新关系拒绝、竞争者先落库再升修订时仍只有一关系并返回原行。`test_issue_mapping.py:163` 与 `:186` 的原请求重放／真实 creation 交错回归及最终安装检查覆盖修正。

其余已审要求未发现缺失或越界。关联保留 `operator_asserted_context / context_only`，不创建／启动任务，不改正式输入／批准，不从缺 host 的旧 creation 推断原生身份，也不承诺 Agent 已读取上下文。F7b.1 来源准入、F7c 回写／observe、F7d 页面继续另片。

## 协调核验与限制

协调者独立补核初始 25 文件和最终 28 文件，最终 r3 wheel SHA256 `5976eeb3b1c3e0beb93bffc1bdf86d8c8221c3625d34a97fa7bc715f81c14042`：447 总／442 包文件、wheel／安装两 RECORD（安装 452 行）、源／冻结候选／安装全部包字节及 283 冻结原件一致。测试独立声明的历史 v1 夹具与固定基线真正的 `_schema_v1` 比较，16 表列合同／48 触发器完全相符，不是以当前 v2 迁移重建“旧”布局。

读原源码结果 152 通过／1 平台跳过、原安装 57／1、定义备份补验 68／1；初始修订视图误比较的失败原件保持。r2 安装完整 57／1、24.00 秒；其实际 journey-r3 的 13 项行为／7.67 秒通过，13 CLI 回执及 13 HTTP body 摘要独立核对，原请求 revision=2 重放、全文／三关联／原 home 恢复读回相同。该旅程属于 r2；最终 r3 安装全部 11 项映射检查 13.69 秒（driver 15.59 秒）及 reference verify 通过，涵盖新增竞争窗口，不称重跑了 r2 的完整套件或旅程。原执行目录前后逐字比较是已检查 driver 的实际证据，不冒称评审者持有独立事前字节副本。首次 Request.method driver 错误及其无 task／清理范围保留。

最终已安装 `issues` 还由协调者对保留旅程数据库以 SQLite `mode=ro` 独立读回：当前修订 3 下原 revision=2 请求返回原关系，旧 revision 的新关系拒绝，两者均不调用 target runtime；原 snapshot 全文一致。没有构造 State、迁移或改写原数据库。两轴另各自复核全部最终实施差异，保持独立判定。

自身模板 r1 为真实独立调用 `e2b326301e6549cfb436a1b964e6c9f7`，194.63 秒、request-changes；聚焦 r2 为 `c946fc8c3a3c4ca4b35b21463a8df795`，80.09 秒、approve。协调者分别从原 native stream 独立复建 manifest→准备／实际输入→prompt→admission→scope→结果；两轮各五固定资源均连续 UTF-8 至 null，附件分别 260,351B／16 份全文和 38,681B／5 份全文，祖先指令／Skill／权限合同保留。r2 批准只覆盖原修订重放的聚焦字节，后补并发修正、最终包和公开投影由本次完整独立终核验收，没有回授模型。原 r1 receipt 的 1,479B／SHA256 `44c3d12eabec2c192fb71c9655c4630a9e629258b6bda1d6dd5ebd1e90b41e0f` 在私有命名修复前后相同，r2 原件独立；不是重复调用模型。

[验收投影](evidence/2026-11-11-issue-mapping-acceptance.json)的 20 份及[自身投影](evidence/2026-11-11-issue-mapping-self-review.json)的 13 份引用原件大小／SHA 全部相符。所有包、检查回执、旅程字段、两轮原判词／输入索引／读取页／用量字段均逐项核原件；用量还与独立重建的 native stream 相同，cached 已含于 input、reasoning 单列，不推导账单。首审失败、聚焦批准及后改范围没有混淆。

有限静态原件与最终冻结 28 文件逐件相符：326 个本地文件链接／6 个已加载秘密值、issue 0，另 `git diff --check` 通过；不声称全锚点、Mermaid、外链或运行时检查，ST1 由本次精确核标题。评审没有安装、网络或模型新调用，没有重跑套件；只读原证据、有限内存／只读数据库检查。私有审计首次的输出路径格式化失败及修正留存，未改变产品或原件。

最终：Spec 开放 0（原 P2 已关闭）；Standards 开放 0（原文档 P3 已关闭）。两轴均无新增 finding；本地出口通过，普通提交／推送及本候选精确远端／CI 仍待。
