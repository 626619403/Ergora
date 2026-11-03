# V3：过时 CI 运行取消独立审查

2026-11-03。审查者 `/root/verification_ci_scheduling_review`，fresh-context；按 maintainable-project-delivery 的 independent-review 及 review-pr 流程，先读 AGENTS 和实际 diff/原工作流，再核实施记录。项目与 docs 均属于 Ergora。本报告只审 V3，不替代 V2 已有审查。

结论：源码审查及同一审查者的最终精确候选复核均通过，范围内无 findings。需求遵循及可维护性分别通过；最终两 OS CI、实际文件身份和实时远端已核，可按下述已披露边界收口 V3。

## 精确范围

基线为 `4a6d3d52dbb42dd6fc9328b49596498f812b112a`，分支 `refactor/architecture-foundations`。唯一实现变更是 `.github/workflows/portability.yml:12–14` 的 workflow 级 concurrency，共新增 4 行（含空行）。实际文件 SHA256 为 `4d45c728e1f164aeeaabe080b00e5e4c58a19acb35ae4871d0364944647cf0a5`；基线文件为 `6624db6c6eaa188db8cc96e4487c1d0f61afab59b96930ed792c55fcd6fdb920`。原始 Git diff 与作者提供的 `tracked.diff` 一致。

同时核对 [实施记录](2026-11-03-ci-scheduling.md)、[成本计划](../plans/2026-11-03-verification-efficiency.md)及 [恢复入口](../PLAN.md)中的 V3 状态、验收和未验声明。工作区并存的 V2 状态文档不计作 V3 实现。

## 核查结论

- 表达式合法：顶层 concurrency 允许 `github` context；`github.workflow`、`github.event_name`、`github.ref` 及事件 payload 可在此使用。PR 使用 `github.event.pull_request.number`；push/手动事件缺少该属性时为空串，经 `|| github.ref` 回退到完整 ref，符合官方缺失属性与 fallback 语义。
- 取消边界正确：workflow 名避免跨工作流组冲突；事件名使 push、pull_request 与 workflow_dispatch 隔离。相同事件的同一 PR 编号或完整 ref 共组，不同 PR/ref 值分组；大小写例外见下文。PR 的合并树检查与分支 HEAD 检查没有互相取消。
- 必需门禁保留：workflow 级取消作用于被后续同组运行取代的候选，没有增加 job/step 跳过条件；一个候选内部的两 OS 矩阵没有被串行化。独立 BaseLoader 解析证明，移除唯一新增 concurrency 后，触发、权限、矩阵、步骤、20 分钟超时、pytest 路径/`--durations=20`、安装、冻结身份及 Windows PowerShell 安装升级检查与 Git 基线逐字段相等。
- 结构和性能范围合适：复用 GitHub 原生调度能力，没有新增测试、断言、门禁、action、依赖、抽象或外部服务。仅可能减少自然重叠运行的成本；公开首结果页 25 条均为 push，不能证明 push/PR 重复率或节省量，文档没有据此删触发或宣称收益。

## 实际检查与证据

审查者执行 `git status --short`、`git log -5 --oneline --decorate`、真实/基线 workflow 与 Git diff 对照、现有 Python 3.12.3 / PyYAML 6.0.2 的 BaseLoader 结构比较、工作流组名搜索，以及 `git diff --check`，全部符合上述结论。现有 `.github/workflows` 只有 Portability 一项。未安装工具、运行完整测试、触发 CI、提交或外部写入。

官方 [Contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)由审查者只读取得，明确 concurrency 允许 `github, inputs, vars`、不存在属性返回空串，并定义 workflow/event/ref。原 HTML、渲染文本、摘录与来源记录位于 `.ergora/checks/verification-ci-scheduling/reviewer/github-contexts.*`，HTML SHA256 为 `d303cf2890f66a3d9b485be99247bb317af2e476124d5695e0710f3fad66f663`。

另独立读取并核 hash 的 [GitHub 并发说明](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)原 HTML 位于 `.ergora/checks/verification-ci-scheduling/github-concurrency-doc.html`，SHA256 为 `a178c255878e9f94eee17f8f14d0d4e3caf0ef313a05d193a27944244c9be0d0`；它说明同组替换、`cancel-in-progress: true`、fallback、workflow 隔离、大小写与排序限制。审查事实记录为 `.ergora/checks/verification-ci-scheduling/reviewer/source-review.json`。

## 验收边界

GitHub 组名不区分大小写，只有大小写不同的分支会共组，实施记录已准确披露。官方也不保证按 workflow 派发时间排序；本配置不提供严格按提交新旧排序的锁。最终候选是否完整成功，必须以其实际 SHA 的检查为准。本地解析和作者的 8 个分组概念例不等价于 GitHub 表达式引擎或取消演练。

尚未进行真实重叠取消演练，也没有测量节省秒数/runner 分钟；不为演练额外启动废弃候选回归。源码审查时尚待完成的共同候选两 OS CI、精确文件身份与远端核对，已由下述最终复核补齐；没有借用 V1 历史 CI。真实取消与收益测量仍属于未验证范围。


## 最终精确候选复核

2026-11-03，同一审查者追加复核，未重跑测试、安装、构建或触发 CI，未提交或外部写入。

最终提交为 `d5588855be0d5995465caa7e0af4b1b80103cc11`，父提交精确为 V2 `4a6d3d52dbb42dd6fc9328b49596498f812b112a`。独立读取 Git 提交确认仅 `.github/workflows/portability.yml` 增加 4 行；相对 V2 的其他文件均未变。Git blob 与实际工作树内容完全一致，workflow SHA256 仍为 `4d45c728e1f164aeeaabe080b00e5e4c58a19acb35ae4871d0364944647cf0a5`，因此保留原源码审查的精确配置身份。

独立解析 `.ergora/checks/verification-ci-scheduling/ci/` 内官方原始 Actions、run 和两份 job HTML：Actions payload 选择的是上述完整候选；[CI 41612623462](https://github.com/626619403/Ergora/actions/runs/41612623462) 的完整提交链接匹配，最终状态为 Success，运行中仅含下列两项矩阵作业。分别核定所选 job ID、平台名称、每步 `success`/完成标记，以及含完整候选 SHA 和相应 job ID 的日志 URL，未只依赖摘要 JSON。

|作业|已核必需步骤|结果|
|---|---|---|
|[Windows / Python 3.12，125838059005](https://github.com/626619403/Ergora/actions/runs/41612623462/job/125838059005)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|4 项全部 success|
|[Ubuntu / Python 3.11，125838059675](https://github.com/626619403/Ergora/actions/runs/41612623462/job/125838059675)|Build and install wheel；Packaged reference identity；Native application regression|3 项全部 success；平台专用 PowerShell 步骤按原条件 skipped|

审查者执行只读 `git ls-remote origin refs/heads/refactor/architecture-foundations`，退出 0，实时返回 `d5588855be0d5995465caa7e0af4b1b80103cc11`；与本地 HEAD、实际工作流及 CI 完整候选一致。原始页面 hash 已独立复算，与实施方 `ci-html-status.json` 的每项来源记录一致；Actions 原页也单独留存 hash。证据、每步日志 URL 及远端读数记录在 `.ergora/checks/verification-ci-scheduling/reviewer/final-review.json`，保留初轮 `source-review.json` 的历史范围。

最终结论：无未解决 findings，V3 的源码、结构/维护性、精确两 OS 必需门禁及推送身份均通过，可收口。没有自然重叠取消演练或 V3 节省量的新证据，不据 CI 成功推导这两项结论；官方大小写和调度排序限制继续适用。
