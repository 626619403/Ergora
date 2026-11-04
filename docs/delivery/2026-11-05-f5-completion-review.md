# F5.5：恢复与阶段收口独立审查

日期：2026-11-05。审查者：新上下文代理 `/root/f5_completion_review`；只接收原要求、验收范围、基线及实际证据路径，没有继承实施对话。遵循项目 `AGENTS.md`、maintainable-project-delivery 及其 independent-review 指南。只写本报告，未修改生产、测试、依赖或 CI，未安装、启动服务、重放任务、提交或推送。

**需求符合性：本片已执行的本地恢复组合与公开边界通过。可维护性：通过，所审范围内无 findings。** 完整 F5 的文档精确提交、普通推送及同片实时远端终结尚待，不能由本地审查代替；G0 全新用户旅程也未验收。

## 身份与范围

基线与当前 HEAD 均为 `4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`，分支为 `refactor/architecture-foundations`。独立重算 `.ergora/checks/f5-completion/review-scope.json` 的 11 个文件 SHA256，并逐字比较实际 Git diff 与 `review-tracked.diff`，全部相同：

- `README.md`、`docs/PLAN.md`、`docs/PROJECTS.md`、`docs/USAGE.md`、`docs/WINDOWS.md`、`docs/architecture/current.md`。
- `docs/delivery/2026-11-05-task-evidence-console-review.md`、`docs/delivery/2026-11-05-task-evidence-console.md`、新文件 [F5.5 交付记录](2026-11-05-f5-completion.md)。
- `docs/plans/2026-11-01-all-in-one.md`、[F5 分片计划](../plans/2026-11-05-evidence-handoff.md)。

源码、测试、依赖及 CI 相对基线无差异。邻接检查覆盖 `cli`、`tasks`、`reference`、`reference_task_reconciliation`、`reference_task_evidence`、`handoff`、`web` 和控制台 `tasks/api/ui` 的实际调用路径，以及现有 handoff、下载、索引测试和 portability 工作流。本报告是上述冻结清单之后新增的审查产物，最终清单须另行刷新。

## 本地证据复核

原证据位于忽略的 `.ergora/checks/f5-completion/`，实际保存包和截图位于 `output/playwright/f5-completion/`。审查读取脚本、实际 argv、退出码和原日志；以下独立重算与小型离线检查没有重新运行浏览器或原生栈。

- 原最终 wheel SHA256 为 `f644858498143dc077bf77114235f9896d01f5da6b008dd984684b5a2c521166`。独立读取 wheel 和精确基线 Git archive，352 个包资源逐项相同；当前两套安装的全部资源亦相同。`base-venv`、`development-venv` 确实是指向 F5.4 原 noneditable 安装的 symlink，没有将复用表述为新安装。
- 全服务停止时原三包离线命令实际 exit0；记录五端口关闭、未创建指定 control home。审查另在现有基础安装独立运行三份本片包及恢复包的 CLI verify，四次均 exit0；确认该安装没有 Temporal SDK，核包前后五端口均关闭，新的指定 control home 始终不存在。输出保持 `origin_authenticated: false`、`execution_success: null` 和原结果。
- 三份本片下载包分别为 135834、185003、11562 字节；独立重算 SHA256、逐字比较原 CLI 包及前片浏览器包，全部相同。包中索引等于原 CLI 索引；43 份材料引用（23/19/1）、原回执和原产物字节逐项一致。两正常原结果仍为 `REVIEW_READY`，取消仍为 `CANCEL_UNCONFIRMED`；模型调用、Token、费用均保持 `not_recorded/value null`。
- 四段浏览器实际 argv 中的脚本与保存源码相同，命令均 exit0；从各原 CLI 日志重新解析的结果与结果 JSON 相同。新会话 34 API 请求、3 个显式收集 POST、3 次真实下载；中断准备另有 1 GET，失败和恢复各 2 请求。合计 39 请求、5 个 POST，均为 handoff 收集，成功下载 4 次；没有任务、批准、取消、对账、派工或 Git 写入请求。
- 停止与启动命令使用正式 services 入口，均 confirmed。失败段 GET 索引和 POST 包实际 HTTP400，原错误为 Temporal `127.0.0.1:7233` connection refused；旧索引保留，零下载。正常段的仅放行路由守卫已移除，失败/恢复脚本未 mock 响应。正式重启前 status 仍显示 Temporal STOPPED，worker/executor 始终 STOPPED；同一 session 和同一窗口重读恢复，索引与中断前及失败时保留值完全相同。恢复包与原取消包逐字相同，独立离线核包仍保留原取消结果。零 pageerror 仅表示无页面脚本异常，原预期网络失败日志仍保留。
- 首轮 `verify-browser-native-command.json` 实际 exit1，原日志为尚不存在 `browser-native-result.json`；浏览器命令完成后 `verify-browser-native-r2` 才 exit0。该失败及成功均独立核到，不能登记首轮成功。后续材料核对、原生 after、正式停止和最终离线检查各有独立成功命令，不依赖失败记录冒充通过。
- `native-before.json` 与 `native-after-verified.json` 整体相同。审查再次只读重算当前 139 文件、两业务 repo 内容/HEAD/refs/worktrees 及 3 claims/0 active lease，均等于快照。三份完整原 history JSON 的规范摘要与 329/348/112 事件数一致；前后运行时 history/outcome 相同由保存脚本及其成功命令证明，本轮没有在停服后声称重新查询了 live history。
- HTTP PID、属主/argv/起时检查、SIGTERM 脚本和 Uvicorn 有序退出日志相符，独立重算日志 SHA 相同；记录工具 session87540 的真实 shell exit143，未改称 exit0 或子进程 wait 码。原浏览器、HTTP、owned Supervisor/Temporal 均不再存活。审查当前实测五端口关闭、请求临时根为空、服务 socket/PID 文件不存在，三个持久 SQLite 仍在原持久目录且大小与最终记录相同。
- 实际查看本片桌面及 390px 恢复下载截图，原结果/观察范围、摘要和保存提示可读；三原 run 的布局记录保留页面及弹窗宽度约束。没有据此声称完成其他浏览器或 Windows 本机旅程。

## 结构、成本与公开边界

本片只在所属文档更新服务矩阵、正式任务入口、Windows 离线命令和阶段状态，没有新增生产文件、函数、缓存、后台扫描、断言、测试框架或 CI 作业。在线索引与收集仍走 `tasks → reference → _Inspection`，离线 verify 在 CLI 初始化 State 之前分派，符合无控制库/SDK/服务的公开合同；Linux 专用进程门禁与 Windows/WSL2 说明一致。

现有 `_Inspection` 共用原完整 history、合同和 FileAdapter 校验，预算事实随同一次扫描累计；交接格式由同一 `handoff` 所有者负责收集和离线核验，HTTP 只拥有请求临时文件与响应字节，前端复用原 job 文本窗口、请求世代、API 错误路径及下载辅助。原上下文、发布材料、原 outcome 引用、外部清理和可合入性均分别表述。未发现本次文档要求促成的重复实现或单消费者公共抽象。

history 连续性/闭合与后继检查、原 spec/context/回执摘要、外部路径与资源上限、发布前复读材料及传输 SHA 各保护其实际输入或生命周期边界。collector、离线接收者、HTTP 适配及浏览器校验针对不同故障，不能因都使用 SHA 就视为冗余。现有测试分别覆盖原生不变、格式篡改/自洽伪造、资源边界、HTTP 请求/清理与单次转发；本片没有复制这些矩阵。

20 项 UI 分页只限制可交互目录 DOM；索引仍读取完整原 history 并核材料，收集还须复读并保存包。HTTP、浏览器 hash/Blob 仍有缓冲成本；本次只验证三个小包的恢复，不证明最大 72 MiB、峰值内存、并发吞吐或性能提升。复用已验源码和既有双 OS CI，使用少量恢复及静态检查，与文档切片风险相称，无需重放模型、任务写或全量本地矩阵。

Windows 原生离线核包的源码/既有 CI 依据和本片 Linux 实际验证没有混归；Windows 浏览器、WSL2 本机、空 OS 安装及 G0 未验。未记录的 Skill/记忆/评价/来源采用、MLflow/OTel 扩展仍是明确未交付或后续计划，不由本次通过推定完成。

## 前片身份与剩余终结

独立重算 F5.4 `ci-html-status.json` 所列六份源文件的字节数/SHA，并解析原官方 run/job HTML：精确提交仍为上述基线，[CI41929749342](https://github.com/626619403/Ergora/actions/runs/41929749342) 为 Success，Ubuntu126923339906 的三个必要步骤、Windows126923340378 的四个必要步骤均 completed/success；selectedJobId 与完整 commit 的步骤日志 URL 相符。结合原 [F5.4 同片最终终结](2026-11-05-task-evidence-console-review.md#精确-ci-与同片最终终结)，公开“F5.4 已完成”有独立原证据支持。这是前片已保存的精确 CI，不是 F5.5 新运行或本轮实时远端查询。

审查独立核冻结的 11 文档、365 个本地链接/锚点和 README 30 条 parser 命令，均通过；未执行文档中的业务命令。`git diff --check` 通过。没有阻塞 finding。

加入本报告及审查状态后，须刷新完整文件/静态清单；随后提供本片精确文档提交、普通推送原证据及实时远端身份，由同一审查者完成终结复核后再关闭完整 F5。保持原包/各片 CI 身份和未验维度，之后另行制定并实施 G0 全新持久环境旅程。本轮未要求额外安装、服务启动或重型矩阵。
