# 逐 Agent 推理设置与原并行执行

2026-11-16。[本片计划](../plans/2026-11-16-agent-reasoning-and-parallelism.md)。基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`，源码位于隔离 `agent-reasoning-options` worktree；源码独审和原模板已闭合并普通合入，联合安装与发布另验。

## 实现与实际调用

`data/components.json` 拥有 Codex 可选 `reasoning_effort` 和 Claude Code 可选 `effort` 的配置及页面下拉元数据。两个 `agent_backends` 实现在自己的原命令边界投影；Codex 显式绑定覆盖外部 TOML 推理值，缺省保持原行为，Claude 传原生 `--effort`。没有增加 orchestrator 后端分派、全局默认、状态表或 scheduler。

Agent 版本、工作流叶子和正式任务继续沿原完整 binding 冻结；`task_envelopes._binding` 是不依赖可变 catalog 的历史结构 reader，配套允许这两个字符串字段，实时准入仍由原 backend/schema 负责。原 `bindingFields` 的项目绑定及任务组合两个消费者自动显示可选项，没有专用 JS 分支。两份相关手册补充可复制配置和正式异后端并行例子；已发布 preset／参考包不改。

正式 review/work-unit DAG 已有依赖与祖先配额调度，本片没有重新实现并行。新增异后端场景沿原 parallel stage 观察真实 async 等待／释放和峰值、完整 admission 及候选转发；其 Activity transport 为受控替身，不代表多家真实模型同时调用成功。独立 run-input 继续只执行单叶，通用混合图与 Repeat 是后继范围。

## 验证与限制

私有 `.ergora/checks/agent-reasoning-options/source-check-r1/` 保存准确 argv／环境增量、完整 raw、JUnit 和源 patch：**45 passed／8 skipped，53.95秒**。覆盖原进程 fixture 的两后端×缺省／low／high×native／text-only，结果正规化、Codex 配置优先级、组件绑定、原Agent新版本及正式任务冻结，原无推理字段仍可恢复。原13个 parallel_reviews 节点均已通过；8个skip来自ForgeKernel／mini-swe可选外部依赖，不能记作并行SDK缺失。

`.ergora/checks/agent-reasoning-options/source-sdk-parallel-r1/` 使用另一个已有独立 SDK 环境读取同一源树：**8 passed／5 deselected，25.26秒**，这8个并行节点是重复验证，不是补齐前述8个skip，也不计新增覆盖。首版交付的错误归类经独立审查指出后，已据原JUnit核正；原始运行保留，不再为此重跑无关外部SDK。这是源码接缝，不把另一片wheel转授本片安装通过。页面验证单独记录；已用现有headless Chromium打开实际页面，正在验表单保存／重开，没有安装系统依赖或提权。

官方参数原网页及本地只读CLI帮助在同一私有目录保存；公开依据是 [Codex 配置](https://developers.openai.com/codex/config-reference/)、[Claude CLI](https://code.claude.com/docs/en/cli-reference)、[Claude 模型配置](https://code.claude.com/docs/en/model-config)。可接受的字段不保证所选模型支持全部等级。Claude 组织 cap 可能降低实际等级，JSON 输出模式的提醒可能只进 debug log；本片保存传入请求，不把请求值当作已证明的实际计算强度。没有新增真实模型性能或成本主张。

准确产品 `0dcbc207e33ad4ed1a8674e2bed43f65c4ecda89` 已固定，10文件patch SHA256 `5ad344dcd73e6158bbac7ed65f562d84e59daf3d2365e87997343a1ca3500ae2`，2,071输入manifest SHA256 `6266c66184fc138e0627b0fd8d882316bf3b33436c7dc15dd1ad6c0484b57f14`，原件在 `fixed-r1/`。

实际项目页面已验证通过：Codex reviewer high、Claude reviewer medium、Codex implementer low分别保存与重开，API最终同时保留两个角色的不同设置；切换后端没有残留另一个后端字段。截图、snapshot、bootstrap、读回原JSON和断言在 `browser-r1/`，完整范围为其 `RESULT.md`。使用现成headless-shell，未安装／提权；自建服务／session已清理。正式任务页面因fixture未统一登记只展示前提，因此组合selector、正式运行和真实模型等级未在此浏览器片验证，不能外推。

## 独立复核与自身模板

[Fresh-context源码独审](2026-11-16-agent-reasoning-options-review.md)已给需求／可维护性两轴approve、开放0；唯一覆盖记账finding已据原JUnit更正，源码身份未改。报告SHA256 `88a14dac1363add1ec6d14c65f4c3c4aff1ded881e847c3276a72807619209e8`。准确产品以普通合入 `a2655c3` 进入开发分支；不是自动合入main。

沿原Ergora `refactoring-quality` 的结构审查模板发起实际模型审查；完整10个变更文件、差异、规则及范围进入stdin。Claude Code **420.553秒超时／exit1**，原件 `self-review-r1-claude-code/` 保留，不能算通过。按用户先前授权回退Codex，实际 **68.049秒／succeeded／approve**；`self-review-r1-codex/` 保存完整输入、原回复和结果。3份原资源与完整任务均核实际进入stdin（360,985B，SHA256 `2080ac6328b09d44c57102c7fad237d4ebf8f30d29f24058e750a636ba3395fc`）；原result SHA256 `2e3099a541dbd18007e23b08a88c0c0032c4626de65507560a47639aa80d6817`。此为文本结构审查，不认证实际模型应用了所选推理强度，也不声称异后端审查通过。

下一步：对合入后的联合候选做必要新非editable安装及接缝验收，再发布并核其自己的CI。其他在途片不继承本片通过。
