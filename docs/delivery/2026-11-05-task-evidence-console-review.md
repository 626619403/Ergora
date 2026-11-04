# F5.4：证据、预算与交接页面独立审查

日期：2026-11-05。审查者：`/root/task_evidence_console_review`，新的 fresh-context 独立上下文，未继承实现对话。按项目 `AGENTS.md`、`maintainable-project-delivery` 及其独立审查规范，先读原始要求、范围清单和实际差异，再读作者记录。仅新增本报告；未修改生产/测试、安装、启停服务、提交、推送或执行外部写操作。

## 结论与范围

|维度|结论|
|---|---|
|需求符合性|本地实现与验收通过；在下述已审范围内无 findings。|
|可维护性|通过；所有权、实际复用、守卫、性能边界及测试/CI成本无阻塞问题。|

基线及审查时 HEAD 均为 `bde57e17d84a0063683be9c5c34392072b255853`，分支 `refactor/architecture-foundations`。独立重算 `.ergora/checks/f5-task-evidence-console/review-scope.json` 所列全部 12 文件摘要，均与当前文件相同；其 11 个 tracked 文件的实际 Git diff 与 `review-tracked.diff` 逐字相同。清单 SHA256 为 `8c45c3e992d198c8b0f7cdf120330e30adeaf211b7d7c9dc346cac185de423ff`，diff SHA256 为 `26e6e79db1af6371448f4615e62f323c676bd59c6501eadb0104d4f208e4f32d`。

生产范围为 [tasks.js](../../src/ergora/data/console/tasks.js)、[api.js](../../src/ergora/data/console/api.js)、[ui.js](../../src/ergora/data/console/ui.js) 三个既有所有者。文档范围为 `README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`、`docs/delivery/2026-11-05-handoff-download.md`、`docs/delivery/2026-11-05-handoff-download-review.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-05-evidence-handoff.md`，以及完整新文件 [本片交付记录](2026-11-05-task-evidence-console.md)。F5.3b 的独立 CI 终结只作为前置记账，不归为本片运行或 CI 验收。

## 行为、结构与成本审计

`tasks.js:450–584、1273–1274` 仅为已查询且闭合的原 run 提供窗口。打开只建 DOM，索引和下载各自显式请求；下载直接消费 POST，不先重读 GET。窗口忙时串行，失败重读保留旧 observation 并标失败。原结果、材料完整性、回执与原 outcome 的引用关系、外部确认、租约和执行成功推断分别显示，与既有原生索引所有者一致。

`tasks.js:507–530` 直接展示原冻结预算、原 history 用量及上下文状态。空值显示未知，`??` 保留真实零值，来源、单位、currency 和跨度状态保留；等待策略没有被称为模型或费用硬上限。未记录上下文没有读取当前项目配置补写。完整结果、索引和合同沿原 `pre/node` 文本路径进入 DOM。

`tasks.js:480–492` 先 slice 再建表，每页最多 20 个 job 入口，换页/重读替换原 DOM。从首个原调度事件调用既有 `jobDialog`，由原窗口固定回执、选择材料并明确读取 8192 字符窗口，没有复制材料消费者。完整索引披露仍会序列化整个已返回对象；其上界来自既有 1 MiB 索引响应限制，分页只约束可交互目录 DOM，不能据此声称后端总 IO 被限制为 20 个 job。

新增 `evidenceDialog`、`active`、`setBusy`、`showIndex/showJobs`、`readIndex/collect` 均是同一详情闭包内的界面、分页或异步生命周期逻辑，实际调用仅在本所有者；与 task/run/详情世代共享的状态提供了保留在原所有者的具体理由，无需为单消费者新增模块或控制器。`api.js:1、14–22` 的可选成功解码有本片真实二进制消费者，仍共用请求头和原 JSON 错误路径；原 JSON 调用保持默认。`ui.js:174–180` 的可选 MIME 由任务 ZIP 消费，既有 `workflow.js` 文本下载继续使用默认值。没有新生产/测试文件、依赖、状态库、账本或 CI 作业。

入口守卫阻止旧详情/run 的迟到点击；`active` 分别约束旧 view、详情世代、run 世代、被替换的内容和关闭状态。异步成功、失败和下载前再次检查，覆盖关闭/重开、run 编辑、换任务和项目 A→B→A。`busy` 防止同窗口并行；finally 只恢复原按钮，不更新新页面。SHA 检查拥有本次传输字节的一致性边界，后端继续拥有 history、合同和材料校验；未发现重复后端守卫、无可达场景的分支或静默成功降级。

`tasks.js:561–573` 读取实际 ArrayBuffer、核 SHA256 后才交给 `ui.download`；下载与 SHA 等待期间失效的上下文不能触发交付。页面显示摘要、字节和离线命令，并明确未证明落盘、来源认证或执行成功。服务端与浏览器均缓冲，浏览器还涉及 hash/Blob 生命周期；现有说明已交代成本，未伪称流式或最大载荷性能。三次实际浏览器下载操作为 1.592–1.759 秒，仅适用于本次 11,562–185,003 字节包；最大 72 MiB、峰值内存、并发吞吐及其他浏览器未测，本次不外推。

现有架构 9 项加 Web 资产代表 1 项的包内定向命令退出 0，日志为 `10 passed, 1 warning`，warning 来自上游 TestClient。命令总耗时约 3.52 秒；本片行为由已有 Playwright CLI 的私有可复查脚本覆盖，没有为前端切片新增测试框架或重复重跑无关原生 collector/格式矩阵。既有双 OS CI 工作流保持，精确候选 CI 仍须后续执行。

## 独立核验与证据恢复

以下原证据均位于忽略的 `.ergora/checks/f5-task-evidence-console/`；截图/实际下载位于 `output/playwright/f5-evidence-console/`。本审查读取脚本、命令和原结果并进行轻量独立复核，没有重新运行真实浏览器或启动原生栈。

- 独立读取 wheel ZIP，重算源码、wheel、两套 noneditable 安装的全部 352 资源，均与身份表相同；最终 wheel SHA256 为 `f644858498143dc077bf77114235f9896d01f5da6b008dd984684b5a2c521166`。283 个冻结资源与既有基线相同。另独立对 13 个发行 ES 模块执行 `node --input-type=module --check`，全部退出 0。
- `browser-native.js` 与实际 `browser-native-command.json` 的代码一致，命令退出 0。原结果记录三原 run、34 请求、仅 3 个显式 handoff POST、3 次实际下载、零 pageerror。独立核三份保存 ZIP 的 SHA/字节，与原 CLI 包逐字相同；内含索引与既有原 CLI 索引相同，43 份材料引用（23/19/1）与原回执及原文件逐字相同，原文本窗口也相同。两个 `REVIEW_READY` 及原取消 `CANCEL_UNCONFIRMED` 保留。
- 审阅独立基础安装的三次离线 CLI 命令/输出和 `verify-browser-native.py`：均退出 0，`origin_authenticated: false`、`execution_success: null`，原结果相同；基础安装无 Temporal SDK 的命令退出 0，指定 control home 仍不存在。审查没有把保存的 CLI 成功记录称作本轮重跑。
- 实际查看桌面、390px 原取消页和受控预算截图；三原 run 与受控输入的布局记录均为页面宽 390、页面 scrollWidth 390、弹窗 clientWidth/scrollWidth 352/352。长 SHA 和源文本复用已有换行/滚动样式，未见页面或弹窗水平溢出。
- 保留的受控首轮命令因语法错误退出 1；第二轮 7 GET/0 POST 后因将含引号源串与 JSON 序列化文本直接比较而退出 1，诊断为零 img、无注入、零 pageerror。第三轮脚本与命令相同，十项证据场景之后等待未载入模板的旧文本按钮超时，**该命令退出 1，不能登记为整条成功**。
- `browser-boundaries-r3-diagnostic-result.json` 与后来 finalizer 的十项 cases 相同；逐项 push 位于对应断言之后。独立检查 finalizer 源码及退出 0 的命令：111 请求、6 个已路由拦截的 handoff POST、零下载/pageerror；45 job 的 20/20/5 分页、上一页/重读替换、记录零值/零跨度、文本安全、失败重读及重试、503/错误摘要、索引/下载各四种迟到转换均已完成。迟到包使用正确响应摘要，能覆盖失效上下文丢弃路径。受控材料是前端输入，不归为真实 provider/history 或额外原生收集。
- 原文本下载由另一实际编辑器消费者脚本先载入模板后独立完成，命令退出 0，1 GET/0 POST，零 pageerror。审查独立比较实际 1316 字节文件，等于原 JSON 输入格式化后加末尾换行。十项完成读回加独立文本验证足以恢复本片分项证据，无需把第三轮失败改写为成功或重新运行重型原生验收。
- `native-before.json` 与 `native-after-verified.json` 完全相同，包含 139 文件、三完整 history/outcome（329/348/112 事件）、两业务 repo 内容/HEAD/refs/worktrees、3 claims/0 active lease。审查再次只读重算当前 139 文件、两 repo 和 leases，均与原快照相同；服务已停，history 部分依据保存的前后快照及其实际核验命令，不重启复查。
- 独立核 HTTP 退出日志 SHA、application shutdown complete/finished PID、属主/命令/起时检查及 SIGTERM 脚本。记录中的工具 shell 退出码为真实 **143**，未改称 0 或子进程 wait 码。原浏览器、HTTP 和 owned Supervisor/Temporal PID 已退出；读取本机监听表确认五相关端口无 listener，请求临时目录为空，服务 socket 不存在，三个持久库存在且非空。正式 services shutdown 的原结果为 `confirmed`。

## 剩余交付

没有阻塞 finding。已有静态记录仅绑定本报告前的 9 份文档、337 个本地链接/锚点和 30 条 README parser 命令；加入本报告、审查状态和最终记账后，应刷新完整清单并重做最终静态检查。随后绑定本片精确提交及其 Git 归档与最终包的一致性，普通推送并核实时远端；取得该提交自己的 Ubuntu/Windows 必要 CI 步骤原证据，再登记同片最终独立终结。F5.3b 的 CI 不替代这些步骤，当前不能登记 F5.4 精确交付完成。F5.5 综合收口及完整 F5/G0 仍待后续验收。

## 精确提交、发行、静态与远端复核

2026-11-05，同一独立审查者从 Git 对象核候选 `4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`，唯一父提交为原基线 `bde57e17d84a0063683be9c5c34392072b255853`。`diff-tree` 正好 13 个变更文件，逐项重算提交 blob SHA，全部等于 `final-review-scope.json`；其 tracked 部分逐字等于 `final-review-tracked.diff`。相对初审仅补入本报告和四份文档的本地审查/静态状态，三个生产文件仍为已审身份。正在开展的 F5.5 工作树文档与运行证据没有计入本轮复核。

独立在内存读取精确提交的 Git archive，352 个包资源逐项等于原最终 `f644858498143dc077bf77114235f9896d01f5da6b008dd984684b5a2c521166` wheel 及其身份表，并重新核 wheel 实际字节摘要。另从该提交文档对象核对全部 10 份 Markdown 的 344 个本地链接/锚点，并使用已核同包的基础安装 parser 解析提交 README 的 30 条命令，全部通过；`static-documents.json` 的文档摘要、数量和命令列表与精确提交相同。没有使用后续工作树文件，也未执行这些示例命令。

读取实际普通 push 的命令、退出码及 stdout/stderr，确认原基线正常快进到候选，退出 0，没有 `--force` 或强制 refspec；每命令传输配置不改变 ref 更新语义。审查者另于 `2026-11-04 23:00:35 UTC` 执行只读实时 `ls-remote`，远端 `refactor/architecture-foundations` 完整 SHA 仍为该候选。本轮只追加原报告，没有执行提交、推送、安装、服务启停或测试矩阵。

**精确提交、最终包、提交文档静态检查及普通推送/实时远端通过，无新增 finding。该候选自己的双 OS CI 尚未在本轮核定，完整终结继续待验。** 前片 CI 不归给本片；取得精确候选的 run/job 原证据后再登记同片最终结论。

## 精确 CI 与同片最终终结

2026-11-05，同一独立审查者完成本片剩余验收。再次从 Git 对象重算候选 `4c87c2a4d37e567c3e7330bb66d6b0ab086655cc` 的 13 个变更文件摘要，全部仍与最终清单一致，唯一父提交保持原基线。F5.5 的工作树文档和新恢复验收不计入本片。

重算 `ci-html-status.json` 所列 6 份源文件（官方 HTML/JSON 及 run 选择记录）的字节数与 SHA，全部吻合；独立解析 actions 行、run 页面、job groups 和两个 job 原页面，核对精确提交、workflow、平台及必要步骤。原 `ci-fetch-final`、`ci-verify-final` 命令均退出 0。审查者另于 `2026-11-04 23:12:07 UTC` 前从 GitHub 重新只读取得本 run 及两 job 官方 HTML，确认相同结果：[Portability 41929749342](https://github.com/626619403/Ergora/actions/runs/41929749342) 为 `Success`，完整 commit 为本候选，workflow 为 `.github/workflows/portability.yml`。

- [Ubuntu job 126923339906](https://github.com/626619403/Ergora/actions/runs/41929749342/job/126923339906)：Ubuntu/Python 3.11，构建安装、包身份和原生回归三个必要步骤全部完成且 `success`。
- [Windows job 126923340378](https://github.com/626619403/Ergora/actions/runs/41929749342/job/126923340378)：Windows/Python 3.12，构建安装、包身份、原生回归和 PowerShell 5.1 安装升级四个必要步骤全部完成且 `success`。

两 job 的平台名与内嵌 `selectedJobId` 一致；各必要步骤有完成标记，日志 URL 均包含完整候选 SHA 和对应 check/job ID，未见失败、取消或超时步骤。Ubuntu 上 Windows 专用步骤按既有条件跳过。精确提交关联由 run 的提交链接及 job 每步日志 URL 共同确认，job 页面没有另外的提交锚链接。审查者于 `2026-11-04 23:10:39 UTC` 另行只读实时 `ls-remote`，确认远端 `refactor/architecture-foundations` 完整 SHA 仍为本候选。

结合前述本地需求/结构与性能边界、材料及资源生命周期验收、包与 Git 归档一致、最终静态检查和普通推送证据，**F5.4 需求符合性、可维护性及精确发行/双 OS CI/远端验收全部通过，无未解决 finding，可登记本片完成。** 本轮只追加原报告，未执行代码修改、安装、服务启停、测试矩阵、提交或推送；没有仅采信作者汇总，也没有继承 F5.3b 的 CI 结论。F5.5 综合收口及完整 F5/G0 继续按各自范围验收。
