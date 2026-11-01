# L1 DeepSeek 调研独立审查

日期：2026-11-02。审查对象是 L1 文档切片；文档基线 / HEAD 为 `b80d90e2adfb36cc00a8f6fe2a382f0064d799d1`，运行源码仍为 `4fe2ec5133a9d055b35debf376e21d09d3df4ec9`，分支为 `refactor/architecture-foundations`。本记录由 fresh-context reviewer 按 `review-pr` skill 独立形成。

## Findings

**最终无未解决 findings。**

初审发现一项 Low 事实勘误，已修正并独立复核：[研究报告](../research/2026-11-02-deepseek-agents.md)图中原 `T[不可变 Trigger / Thread]` 把 Thread 聚合也标为不可变。固定原型的 [model.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/6337fc823ce20251c8de8085948165c81aaa701e/src/core/model.ts#L22) 仅将 Trigger 定义为不可变事件；Thread 是聚合，[tickets.ts](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/6337fc823ce20251c8de8085948165c81aaa701e/src/core/tickets.ts#L217) 实际修改并保存其订阅。作者现已拆成“不可变 Trigger 事件”与“可更新的 Thread 聚合”，Eval 和订阅上下文从 Thread 出发，与实际边界一致。此项关闭。

同时复核版本说明为“master 上的 alpha 版本源码快照”：仓库默认分支及缓存 origin/HEAD 为 master，根包版本为 `0.2.2-alpha.2`；没有把 alpha 当作分支或安装组合已验收。未发现 High / Medium 问题，没有要求本轮新增运行接入或扩大安装范围。

## 需求符合性

**L1 静态调研范围通过；初审事实勘误修正后无未解决问题。** 审查先读取根 AGENTS、基线 PLAN 和详细计划中的 L1 原始验收，再检查工作区完整差异与固定来源，最后完整读取研究报告及来源清单。范围为两份既有计划的修改，以及新增研究报告和来源 JSON；L0 已提交的交付记录、既有运行验收和其他功能不计为本次实现。

- 用户给出的 Reddit 页面确实直接链接 `deepseek-ai/dsh-superagent-prototype`；官方 Harness 主页交叉链接其仓库。报告准确区分研究原型与官方 Harness 开发预览，未把组织名等同于成熟官方产品。
- 两个固定提交、包版本、MIT 许可和运行要求有源码证据；仓库创建时间、提交时间和 npm 发行时间分开记录。官方产品公告的确切时间与文章全文仍未核实，报告没有用仓库创建时间替代公告日期。
- 报告覆盖任务 / 授权 / Session / Skill / 信息保存、模型、执行隔离、通信和面板，并保留原型版本与另行读取的 Harness alpha 快照尚未验证兼容的限制。未以源码支持推导当前环境可运行，也未以模型报告或 PR 关闭代替可信验收。
- 直接评价现有 headless / SDK / ACP 接口、部分复用消息与授权设计、仅借鉴插件及领域边界三种选择有明确职责与维护成本。F2–F10 / D3 的新增验收仍标为待实现，保留 R4–R8 优先顺序；没有把 L0 成果继承给 DSH，也没有据转载宣称速度或稳定性收益。

## 可维护性

**通过。** 建议沿用现有 `agents.invoke`、组件描述、项目绑定和进程管理等真实消费者；源码中的 `stage-json-v1` 校验与报告说明一致。方案保留 Ergora 的候选证据、精确批准、可信检查、预算和 Temporal 状态权威，不复制 TypeScript Engine，不增加另一套全局 DSL 或持久调度器。固定版本、native ID、取消确认、外部副作用对账、未知费用、授权与上下文分离、受评价的 Skill 采用都有可操作的后续验收。

来源 JSON 保存 50 个文件的固定 URL 和摘要，适合在后续适配前重新取得同一快照。只做定向代码核对，不将文件摘要相符说成上游实现已通过运行验收。

## 审查方实际验证

|检查|结果|
|---|---|
|Git 分支、HEAD、近期提交、完整 tracked diff 和两份新增文件|范围与交接一致；生产代码无改动|
|三份 Markdown 本地文件链接|84 个目标全部存在：PLAN 45、详细计划 30、研究报告 9|
|来源 JSON|解析通过|
|固定源码身份|Harness `ce7073d51254c26cd63b22a60835b8f948deb447`，原型 `6337fc823ce20251c8de8085948165c81aaa701e`；逐文件 `git show <commit>:<path>` 后重算 SHA256，27 + 23 = 50 个全部匹配|
|定向上游复核|README / 包元数据 / 授权与执行文档，以及 Engine、Map repository、Store、Outbox、DSH Executor、运行装配、Agent / loop / Teams / SDK / ACP / sandbox 等相关接口与限制|
|公共页面只读核对|Reddit 原帖指向、官方 Harness 主页与仓库链接一致；未采用转载性能结论|
|`git diff --check`|通过|

没有运行 DSH / 上游测试、模型任务、真实 GitHub / 飞书写入、原型重启、沙箱探测或跨工具效果比较；没有验证原型与当前 Harness 源码的组合。未重新执行 L0、完整回归或 CI，因为本切片仅修改文档。官方文章全文、文章实验及外部 Watchdog 的文章方案仍不在已核实范围。后续实际接入必须按 F8 / D3 另作固定版本运行验收。
