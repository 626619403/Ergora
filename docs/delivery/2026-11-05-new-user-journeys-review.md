# G0.2 独立审查

日期：2026-11-05。审查者：`g0_journeys_review`，新建 fresh-context 独立上下文，未继承实施对话。依仓库 `AGENTS.md`、maintainable-project-delivery 的 independent-review brief 和 disciplined-repository-engineering，先核原始要求与差异，再核源码、原始记录和现存数据。本轮只新增本报告。

## 范围与结论

精确基线及当前 HEAD：`18ed62eb4eb0dba6a27d0535919a394330fa1e45`。原始要求见 [G0 分片计划](../plans/2026-11-05-new-user-acceptance.md)，新增[交付记录](2026-11-05-new-user-journeys.md)已阅读全文。独立逐项重算 `.ergora/checks/g0-journeys/review-scope.json` 中六份文件的 SHA256，并核当前 tracked diff 逐字等于 `review-tracked.diff`：

- `docs/PLAN.md`
- `docs/delivery/2026-11-05-new-user-onboarding-review.md`
- `docs/delivery/2026-11-05-new-user-onboarding.md`
- `docs/plans/2026-11-01-all-in-one.md`
- `docs/plans/2026-11-05-new-user-acceptance.md`
- `docs/delivery/2026-11-05-new-user-journeys.md`

**需求符合性：本地验收及文档通过，初审一项 P2 已在同片复核关闭；精确交付待终结。** 同一 G0.1 持久环境、两个 revision2 项目及原 prepared 意图保持，没有以替代任务绕过失败。**可维护性：通过，范围内无结构、复用、性能或冗余测试／CI／断言 finding。** 生产、测试、依赖及 CI 未变，当前两套非 editable 安装的352资源逐项等于已接受生产 `4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`；原 f644858 归档及 CI41929749342 的历史覆盖未被冒作本次 G0 运行证据。

## Findings

**P2（已关闭）：区分日志可观测 token 字段与未记录的正式计费数据。** 初审[交付记录第78行](2026-11-05-new-user-journeys.md#交付范围与剩余事项)将“真实token/费用仍未知”并列概括；但现存九份成功模型 job 的 `model-log.md` 均有 Codex `turn.completed.usage`。独立解析得到九条自报记录，字段分别累计为 `input_tokens=843134`、`cached_input_tokens=620544`、`output_tokens=13124`、`reasoning_output_tokens=714`、`cache_write_input_tokens=0`；这些字段不能相加作为总消耗，也不覆盖取消任务或证明 provider 账单。三个原 evidence 索引的 `model_calls`、`tokens`、`cost` 则确实保持 `not_recorded/null`。原概括会使后续读者误以为原材料完全没有 token 观测。最小修正为明确“正式索引未归一化记录；原 CLI 日志存在自报 usage；完整及计费消耗、金额仍未知”，无需改产品、回填原索引或估算费用。

无 P0／P1；除上述已关闭 P2 外，所审范围无其他 finding。

同片复审：实施者仅修改交付记录的开头／末句并新增[三种用量来源说明](2026-11-05-new-user-journeys.md#审查修正用量事实的三种来源)。审查者重读修正全文，确认其准确保留原 CLI 自报、正式索引未记录、取消消耗和账单未覆盖的边界，没有字段相加或推估金额。修正文件 SHA256 为 `5ae92fb1edcdd81d63ea14af09333ddd998884f649933557681cd89230e34865`，其余五份初审文件摘要保持，新增文件仅本报告；P2关闭。只核文档及静态结果，没有重跑已通过的模型、服务或离线包验收。

## 独立核验

- 直接解码原 Temporal history，核连续324／337事件及112事件待批前缀不变、原 spec／submission memo、各唯一 event113 `approve_plan` 和 intent／attempt／result／owner receipt 的 SHA 绑定。两原结果均 `REVIEW_READY`，精确候选分别为 `44d697f0701a69fdfad50e72ee1b463d70adc9fe`、`68ff73c485ea9faedf1dd8a94f98629f26fb489a`；7／6个原 job 覆盖六阶段，5／4个真实 Codex job 的角色 session 独立。13份原 request／receipt、42份正常材料引用、候选 verification／review 及结果摘要均与现存字节一致。
- 阅读两任务六份完整计划／所有权／回退材料及两份原 review-report。浏览器重开前16 GET、重开后19 GET均零 POST／pageerror，完整计划 API 回包逐字段等于 CLI；两次真实批准共35请求／2 POST，一次实际200回包被丢弃后沿原 decision 读回。原重复命令与 history／可见性记录支持各仅一个原 run 和一个有效批准，18份原操作文件保持。
- 核两次 export 原命令、候选分支、操作者持有的 detached worktree 和九条可信检查原日志均 exit0；原验收脚本 SHA 保持，当前候选 worktree 干净，源 HEAD 仍原基线，无 checkout／merge。外部检查覆盖真实行为、AST依赖、知识链接及大型任务集成／兼容／回滚；动态导入、异常输入等原覆盖缺口没有被抹去。
- 取消原 history 连续35事件、仅一个精确 `request_cancel`、零批准；核原活动 selected 进程记录、实际模型子进程 `cancelled/-15`、监控器 fence 非零终态及当前原进程组／monitor 退出。原 `CANCEL_UNCONFIRMED` 与未知字段保持，外部回执核查后显式 reconcile 释放租约，未改写为开发成功。必要源码 `stage_driver.py`、`agents.py`、`processes.py`、取消／对账所有者支持这些语义。
- 三份浏览器实际 ZIP 与 CLI 原包逐字相同，23／19／3共45份材料引用逐项等于原 receipt、磁盘字节及 SHA；原流量36请求／3下载 POST／零 pageerror，另看桌面、390px及回包丢失代表截图。本审查另在五端口均关闭时，用现有无 Temporal SDK 接收者执行3次只读 `handoff verify` 全部 exit0；错误外部 SHA、仅一个 blob 改动且 CRC 正确的复制包各3次均 exit2并给出对应拒绝原因。原包、manifest及原结果保持，未创建接收者 control 库。
- 独立只读重算现存新152／旧139文件，核两套 Git 文件／HEAD／refs／worktrees、可信检查脚本、原 Supervisor ini及新旧 leases 与原快照一致；新3 claims／0 active。核 owned 浏览器、HTTP、Supervisor及服务进程已退出，临时根空、socket／PID文件移除、五端口关闭，三份持久数据库非空保留。原 HTTP 日志均包含有序启动及 shutdown；原生命周期记录保留工具 shell143。关闭前零 running 查询及三原完成 history 仍有原命令／快照可追溯。
- 复查两次辅助失败及恢复：零租约断言前后脚本 SHA 相同、先显式对账再通过；取消收尾仅纠正字段来源，r2读回首轮四条成功命令而未重复写。独立重核初审六文档240个本地链接／锚点、实际已安装 parser 的30条 README 命令及 `git diff --check`，均通过。

本片沿现有 task、证据、交接及服务所有者执行，没有新增生产抽象、依赖、测试框架或 CI。所核 SHA／外部输入／资源生命周期断言分别保护原记录身份和清理边界，无以弱化断言求通过的证据。两正常 workflow 的原 history 跨度约637／704秒只描述本次条件，不作为性能改善结论。

## 限制与交付门禁

本轮未安装软件、启动服务、调用模型、改业务候选、提交或推送；未读取凭据内容。原运行的过程事实由现存原 history／命令／日志和当前数据交叉核验，本审查没有重新观察已经结束的进程。纯文档范围不重复未变的 Python／多 OS 重型矩阵。Linux 当前可信容器之外的空 OS、本机 Windows／WSL2、GPU、远程 tracker、完整计费消耗和金额均未在本片验收。

实施者仍须刷新包含本报告的完整 scope／静态结果，并完成精确纯文档普通提交推送；同一审查者随后从 Git 对象及只读实时远端核验后才能终结 G0.2。G0.3 的公开正常关闭说明、操作计数／配置面和综合收口仍单独待办，完整 G0 尚未完成。
