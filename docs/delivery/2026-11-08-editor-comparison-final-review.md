# F6.1：固定候选独立终结核对

日期：2026-11-08。审查者：新的 fresh-context agent `/root/editor_comparison_final_review`。原审查者 `/root/f6_editor_comparison_review` 跨会话不可调度，本轮从新的独立上下文核对既有候选；不是原审查者的续写，不修改或替换[原报告](2026-11-05-editor-comparison-review.md)及其两项 P2 历史。遵循根 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review 指引。

**需求符合性通过；可维护性通过；固定候选的 F6.1 终结证据已满足。检查范围内无新增 finding，无未解决阻塞项。** 原报告已经关闭的 F6-01/F6-02 保持其原处置，本报告补齐最终两 OS CI 必要步骤的独立核对，供主代理同步 F6.1 完成状态。该结论只覆盖比较原型和选型，不覆盖 AC0 设计或 AC1/F6.2/F6.3 生产修改。

## 需求、身份与检查范围

本轮按交付给审查者的原需求摘要及 [F6 计划 E1–E6](../plans/2026-11-05-low-code-editor.md)验收：固定版本和许可，以同一输入及旅程比较 Cytoscape＋原生表单、React Flow＋原生表单、Cytoscape＋JSON Forms；给出下一片选型，保留原领域校验、草稿修订、六阶段及可信检查。可复现例子不是生产编辑器，单次观测不构成未来容量或跨平台原型承诺。

完整读取上述计划、原审查报告、[交付记录](2026-11-05-editor-comparison.md)、[比较研究](../research/2026-11-05-editor-comparison.md)及 [ADR0003](../architecture/decisions/0003-workflow-editor-stack.md)。项目检查点已读取；工作树包含后续 AC0 文档，因此候选内容一律通过 Git 对象读取。当前原审查报告的追加记录单独作为历史证据读取，没有纳入候选文件身份或 AC0 审查。

- 固定候选：`b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`；唯一父：`df0a908893970d12208b3a2026d19b4591f83989`。本地 HEAD 仍为该候选，分支为 `refactor/architecture-foundations`。
- 独立通过 `git rev-list`、`git diff-tree`、`git show` 重算恰 **26 个变更文件**的集合、字节数和 SHA256，全部等于 `.ergora/checks/f6-editor/candidate-scope.json`。该清单 SHA256 为 `c47c3c144ca8444d64454e92ceb74f319442c7e0668cb3aa3f40ccc8de70fc7d`。
- 15 个例子文件逐项等于 `fix-local-verification.json` 的修后源身份。完整读取例子源码、说明和许可说明，解析完整 lock；61 个非根条目均带公网 registry/integrity，直接版本固定，许可为 MIT/ISC/BSD-3-Clause。历史实际安装为 36 包，不能将 lock 条目数等同于安装包数。
- 候选的 `src/`、`tests/`、`pyproject.toml`、`.github/` 相对唯一父无差异。没有将默认依赖、生产资源、模型执行或新的 CI 作业混入本片。
- `static-after-fixes.json` 的 SHA256 独立重算为候选绑定值 `32e5053f58b1355301a1132bd79d55f0db5dd5b641b85dfc4123d9f75787d5c6`，13 份文档的摘要全部等于候选 blob。347 本地链接无缺失、30 条 parser 命令是该已绑定历史检查的结果，本轮未重跑 parser。候选内原审查报告的完整 15,737 字节仍是当前原报告的逐字前缀。

## 需求与维护性核对

原两项发现的身份与处置保持如下；这里记录本轮核对，不重写原发现：

|原发现|具体文件与本轮证据|终结判断|
|---|---|---|
|F6-01 · P2|[例子 README](../../examples/editor-comparison/README.md)第 19 行已安装 `.[web]`，与 [serve.py](../../examples/editor-comparison/prototype/serve.py)第 5–7 行导入一致。已读独立新 venv 的创建命令、`fix-local-verification.json` 中不继承系统包的配置、Web/FastAPI/Uvicorn 导入及 `pip check` exit0；原审查已补核实际环境与启动/退出。|保持原复审关闭。pip 安装原 stdout 未完整落盘的历史限制继续保留，不用 venv 创建回执代替安装回执。|
|F6-02 · P2|[cytoscape.js](../../examples/editor-comparison/prototype/cytoscape.js)第 31–33 行在重建前清除待连接起点。独立核 `stale-connection-green` 的原 stdout Result＝保存 JSON、实际命令脚本＝归档脚本、exit0，且等于修后核验记录的命令与结果摘要。两入口覆盖跨模板取消、重命名取消及正常 Shift 连接，18 请求/2 校验 POST、零 pageerror，没有保存或任务写。|保持原复审关闭；局部生命周期修复与受影响验证相称。|

另独立核对三份 `final-journey-{native,flow,schema}` 及 `final-graph-boundaries` 的原命令、脚本、stdout/result：全部对应，exit0。三方案各 29 请求/22 POST、两个模板、零 pageerror；额外边界为 20 请求/2 校验 POST。所有 POST 均为原草稿保存/校验路由。六份结果均为 r2；每个模板在三方案中的编辑、JSON 往返及图形操作后摘要相同，保留权威环/越界路径错误、实际节点位置变化及 390px 主操作证据。

这 **107 请求/68 POST** 继续绑定修复前源码；独立比对旧源清单与最终候选，差异恰为 README 和 Cytoscape 适配器。修后另以 18 请求覆盖受影响路径，没有把旧全旅程改记为新源码全量重跑。`fix-local-verification.json`、原 `final-*` 及离线记录中，旧库六份 r2/16 表、仅项目与草稿有记录，新库仅一个项目/零草稿及 Agent，13 资产、许可、CSP、退出回执彼此一致。实际资产/两库/venv/PID 的独立补核由原报告保存，本轮未重新打开数据库、运行安装或重新观察旧 PID。

维护性结论由候选源码和上述记录支持：[app.js](../../examples/editor-comparison/prototype/app.js)第 60 行的共享入口有三个实际消费者，原生表单和 Cytoscape 各有两个；React Flow、JSON Forms 的单入口适配器拥有各自投影及 React root 生命周期。服务端仍由原 `create_app`、草稿校验/保存接口拥有语义与修订，没有第二份 validator、状态库、DSL 或执行器。ID 非空/重复保护服务于图库投影；环与路径由原后端拒绝。未增加冗余生产测试、通用框架或 CI，两个局部修复不需要扩建基础设施。

JSON Forms 默认 Ajv 的真实 CSP 失败及 exit1 保留；候选第 25 行明确使用 [NoValidation](../../examples/editor-comparison/prototype/schema-form.jsx)，只生成控件并复用后端显式校验。修后三个完整入口 raw/gzip 加总独立核为 447,564/144,198、408,566/128,660、907,336/291,001 字节，与比较研究一致。React Flow 在此构建更小，ADR 没有反向宣称它更重；396/384/486ms 仍为单次 loopback 观测，不作速度排名。保留既有 Cytoscape/原生模块、先补编辑语义的决定有本片证据支持，不据此推导其他负载下的优劣。

## 精确推送与双 OS CI

已读普通推送原记录：2026-11-05 07:00:49 UTC，exit0，分支从唯一父推进到完整候选，`remote-after.stdout` 与 `push-remote-identity.json` 一致。原报告另保存原审查者于 07:26:47.876834 UTC 独立实际 `ls-remote` 的完整 SHA 核对。本轮接受其明确时点的独立远端事实，未把它表述为本轮实时分支查询，未读取或输出认证设置。

本轮直接解析归档的官方 HTML，而非只采用 `ci-html-status.json` 或总体 Success。独立重算该 JSON 所列六个来源的 bytes/SHA 全一致；关键原页面身份为：

|来源|字节数|SHA256|
|---|---:|---|
|`ci-run-latest.html`|163,665|`6c0200d85d6611887194c271e7ffc5cea5115f5f1b64c88f58c6007e46e825a0`|
|`ci-job-127101113372.html`|166,415|`df31efd28639037e017a4eac0cec9451ced8c3172020c5093e99b739964b1da1`|
|`ci-job-127101114113.html`|168,329|`14c81c7b575072a37df84fa3f1a30d5d92be4fad2d0b2cb3d90799fa1754ec28`|

[Portability run 41984232370](https://github.com/626619403/Ergora/actions/runs/41984232370) 的 run 页面含精确候选 commit 链接及 Success。两个 job 的嵌入 JSON 分别含精确 `selectedJobId`，`summaryHref`、workflow 链接和 `jobGroupsFetchUrl` 都绑定该 run/attempt1。对照候选 `.github/workflows/portability.yml` 的矩阵和步骤，逐项核 `check-step` 的步骤号、`data-conclusion`、完成标记/时间及日志 URL：

|必要步骤|[Windows / Python 3.12 · 127101113372](https://github.com/626619403/Ergora/actions/runs/41984232370/job/127101113372)|[Ubuntu / Python 3.11 · 127101114113](https://github.com/626619403/Ergora/actions/runs/41984232370/job/127101114113)|
|---|---|---|
|4 · Build and install wheel|success|success|
|5 · Packaged reference identity|success|success|
|6 · Native application regression|success|success|
|7 · Windows PowerShell 5.1 installer and upgrade|success|skipped，符合仅 Windows 的条件|

每个必要成功步骤的日志 URL 均精确为 `/626619403/Ergora/commit/b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe/checks/<对应job>/logs/<对应步骤号>`。另核初始化、checkout、Python 设置和清理/完成步骤：Windows 共 10 项 success；Ubuntu 9 项 success、仅上述条件步骤 skipped，无失败、取消或超时。Windows 完成于 2026-11-05 07:07:26 UTC，Ubuntu 于 07:14:11 UTC。单批 `jobGroups` 的 `totalCount=2, hasMore=true` 未被误当作完整 job 列表；两个 job 均有自己的最终 HTML。

2026-11-08 **12:54:44 UTC**，本审查者另直接只读 GET 上述官方 run 和两个 job URL，均 HTTP200。两个新返回的 job 页面仍含各自精确 `selectedJobId`、候选日志 URL及同一逐步骤结果。本轮未将新页面另行落盘，原归档保持原字节；已读 `verify-ci.py` 的验证逻辑，但未执行其写 JSON 的动作。未重跑 CI，也未把步骤状态核对扩大成逐条下载全部控制台日志。

## 终结与未验边界

固定候选的源码身份、原可复现比较与修复证据、选型、普通推送/原独立远端核验，以及精确双 OS 必要步骤已经闭合。原报告末尾的“两 job 必要步骤 pending”现有独立证据可关闭，**F6.1 可登记完成**；当前计划及交付的状态由主代理按本报告记账，原报告保留其原时点历史。

本轮未安装、构建、启动服务/浏览器/模型、写数据或执行 Git 修改，只新增本文件。原型 Windows/其他浏览器、完整无障碍、50/200/500 容量、任意 schema/standalone Ajv、生产编辑缓冲、撤销重做、迟到失败/跨项目所有权及修订冲突仍未验收；一般 Python 产品的 Windows CI 不替代原型 Windows 运行。六阶段与可信检查在本片保持既有合同，没有本轮新的真实 Agent 旅程。AC0/AC1 及后续 F6 片不继承本报告为生产功能验收。
