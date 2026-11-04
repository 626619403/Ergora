# F4.2c 独立组合旅程审查

日期：2026-11-04。审查者：独立代理 `task_console_journeys_review`，使用 fresh context，未继承实现会话。先读原始要求、技能约束、实际源码与运行材料，再对照[交付记录](2026-11-04-task-console-journeys.md)。

**需求符合性：通过。可维护性：通过。以下审查范围内没有未解决 finding。** 两模板真实创建、提交、批准前等待和持久回执恢复均有对应证据；结论不扩展到完整 F4。

## 基线与范围

分支为 `refactor/architecture-foundations`，源码基线及当前 HEAD 均为 `f54c077f3f61dc5020147975dc34872dbabbe0e7`。最终 wheel SHA256 为 `54130609fb4c873e5d38244f2fab5287695db648f5938156284a9ce677c3b393`。本片没有生产、测试、依赖或 CI 增量。

实际审查工作区的五份 tracked 文档差异：`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/delivery/2026-11-03-formal-task-console.md`、F4.2b 的交付及审查记录；另审查本片新增交付记录及本报告。B 的提交/CI 收口与 C 的组合验收分别记账。审查期间新建的 F4.3a 计划文档属于下一片设计，不作为 C 的实现或验收依据。

检查现有 `tasks.js` 的草稿载入、冻结预览、创建、提交及原 run 读取，与 `web.py`、`tasks.py`、`reference_task_submission.py`、`reference_executor.py` 和冻结 workflow 的相关调用边界；未修改这些文件。私有材料根为 `.ergora/checks/f4-task-console-journeys/`，材料与机器配置不纳入公开交付。

## 独立核验

- **包与合同。** 自行重算当前源码、wheel 与实际非 editable 开发安装的全部 348 文件，完全一致；当前源码仍与候选相同。包内冻结 reference 身份保持，另实际执行新 runtime 的 `validate_installation`，结论仅覆盖该函数要求的文件。两个独立业务仓库固定同一业务基线 `f129c435b9f76d885e3b0f0dc849a6f4f1e4bae7`；治理 3 项、大改 6 项可信基线检查及登记/绑定命令均有原结果。
- **真实网页操作。** 自行比较 `browser-normal`、`browser-awaiting-v2`、`browser-reopened` 的 JS、CLI 实际执行代码与 CLI Result/独立 JSON。正常段 38 请求、38 份响应均为 HTTP 200，其中 10 POST 恰为每项目各一次校验草稿、保存、preview、create、start；两 start 的真实原 run 与原生记录一致。后两段各 36 GET，无写请求；三段合计 110 请求、10 POST、零 pageerror。脚本没有 route/fixture 分支，原生 spec/memo/job 记录与网页返回形成对应关系；不把脚本中单独的零计数字段当作传输真实性证明。
- **输入与提交归属。** 独立对照草稿输入、preview definition、创建 intent 的七文件与实际合同，规范 SHA 一致。解码两份完整原 history，workflow input 等于本次 spec，原 run ID 相同，`ergora.submission_sha256` memo 等于原 submission intent 的规范 SHA；request/profile 的规范摘要也一致。
- **真实模型与人工边界。** 两 run 各 112 个连续事件、零 signal；每任务只有 inventory/plan 两个成功 job。自行重算 job context/envelope、receipt 和全部 artifact 摘要，并将四份 agent-selection 的 binding、prompt/result SHA 对回真实 model protocol 文件与输出；四角色冻结为 Codex / `gpt-6.1-sol` / current-container，实际运行仅使用 inspector/planner。已阅读两执行计划及回退文本，未作批准。UTC 05:14:18 的独立实时 GET/完整 history 复核仍为 `AWAITING_PLAN_APPROVAL`，completed 为 inventory/plan、active 为空；计划 SHA 等于实际 plan receipt 的规范 SHA。
- **重开与无会话恢复。** 核 HTTP 原进程身份/退出及端口关闭记录、新 HTTP 启动日志、新页面快照与重开后的真实 GET 结果。浏览器 close/open 原输出由 root 转录保存，已明确标注来源；审查者没有亲见原 close/open，也不据该转录断言当时初始 storage 为空。另直接核 `browser-storage-free` 内外 exit0、JS=内层 command=CLI 代码、CLI Result=JSON：16 请求全 GET，清空后剩余键数 0，两任务 run 选择键均为 null，DOM run 仍等于持久 submission 的原 ID。该 16 GET 与主旅程 110 分开记账。
- **保护与留用。** 自行比较重开前后及当前选定的 54 份合同/request/receipt/artifact/操作 JSON，逐字相同；不扩展为 SQLite、workspace、日志或进程普查。另独立核旧 B 两 prepared 意图及七文件，仍无 attempt/result/rejection/requests/receipts；旧 A 的 35 文件及 9 创建意图、F3 的 416 文件摘要保持。实时正式 services status 确认专用 daemon running，temporal/worker/executor/a2a/mlflow 为 RUNNING，training-worker 为 STOPPED；两个原 run 是当前专用 Temporal 的两条运行中 workflow。运行栈按后续 F4.3 所有者范围留用，本片没有 shutdown 结论。

已实看 `output/playwright/f4c-large-f4c-reopened.png`：原任务、冻结角色、原 run、待批计划及 inventory/plan 完成状态可读，并与实际 API/原记录一致。

## 结构、复用与成本

页面继续消费既有正式任务 API，后端仍由原任务创建/提交和 native executor/workflow 持有合同、归属、job 与人工门禁；本片未新增生产函数、包装层或状态机。私有核验脚本留在本次材料目录，没有为单次验收增加公共抽象或机器路径耦合。没有可成立的结构或复用 finding。

成本结论只覆盖两个单模板项目、四个真实模型 job 和上述有界显式查询。页面查询为显式触发，本片未增加后台派发或轮询；未测吞吐、延迟或费用改善。源码与包身份未变化，未重复模型调用、安装、构建或重型回归，符合本片证据风险。

## 失败归属与未验范围

首版 history 辅助脚本使用错误 memo 字段，首版 awaiting 浏览器脚本等待折叠 pre 可见而超时；原脚本/材料保留，均不计为通过，也不据此判产品故障。审查者一次临时只读探针误假定 receipt 自带 stage 字段而退出 1，改用真实 job ID 到 stage 的对应关系后完整复核通过；该失败没有写入原材料或产品状态。

本片未验 work/integrate/verify/review、网页批准/取消/对账/导出、完整六阶段、原生服务 shutdown/restart、Windows 真实组合、并发负载、390px 全分支、吞吐与费用；既有 a/b/F3 的历史结果仍保留原范围。原 run 与计划身份继续按交付记录留给 F4.3。没有阻塞本片功能验收的缺口。

已读静态文档检查脚本及当时 17 文档/346 本地链接锚点/26 README parser 命令的成功记录，初次核对时文档摘要一致；`git diff --check` 通过。本报告替换占位及补证文档更新后的最终静态身份快照，由交付者刷新后再提交，不能沿用旧占位摘要作为终版身份。精确文档提交/推送和 F4.3 后续验收不在本报告中提前宣告完成。
