# F5.3b：显式 HTTP 交接下载独立审查

日期：2026-11-05。审查者：`/root/handoff_download_review`，新建 fresh-context 上下文，未接收实现对话。先读项目 `AGENTS.md`、交付技能和独立审查规范，再检查原始 diff、新文件与相邻调用链，之后对照[交付记录](2026-11-05-handoff-download.md)及[F5 分片计划](../plans/2026-11-05-evidence-handoff.md)。本次只写此报告，没有修改源码、安装、启停服务、提交、推送或重跑完整矩阵。

## 范围与结论

基线及当前 HEAD 为 `87538b3dcafb13ca5bbc8191f84e5a4b0fbf0083`，分支 `refactor/architecture-foundations`，审查对象为未提交工作树。初始完整清单和差异为忽略目录 `.ergora/checks/f5-handoff-download/` 中的 `review-scope.json`、`review-tracked.diff`：生产文件 `src/ergora/web.py`；新增 `tests/test_handoff_download.py`、本片交付记录；其余为 README、USAGE、PLAN、当前架构、F5 分片计划及 a 片交付/审查记账。实际读取了全部这些文件，并追读 `tasks.handoff`、`reference.task_handoff/_task_operation`、原生 `_Inspection`、`handoff.create/verify`、CLI、邻近测试、依赖与既有 Portability workflow。

本次行为结论绑定以下身份，审查结束前再次重算均保持：

- `web.py` SHA256：`2b1180b7617b85aa35a3ab0e41abf42aed6b9377e4f484b88ba7075e0bb6fdb3`。
- 新测试 SHA256：`3800e52a52f2fbccb6926932832fd9bfb2743d60e4e677bd25cd83f52316b764`。
- 最终 wheel SHA256：`54548bc34aeb8cf7d9f55a62cbf3d1ef3f27695f5880afe5898fd99ec53095ae`。

**需求符合性：本地实现与验收通过。可维护性：通过。检查范围内无 correctness、结构、复用、性能、冗余断言/测试或 CI 成本 finding，无待修阻塞项。** 本结论不替代 b 片的精确提交、普通推送、双 OS CI 与同片最终终结。

审查期间 a 片审查报告追加了其 CI 终结，作者随后更新 PLAN、a/b 前置状态、F5 计划，并增加宏观 `docs/plans/2026-11-01-all-in-one.md` 的进度修改。因此原始清单/静态结果中的部分文档 SHA 和完整 diff 已过期；生产、新测试与发行包未漂移。这是并行进度记账，不构成 b 行为变更。本报告不重新裁定 a 的 CI，也不把其结果归给 b；最终提交前须重新列全当前范围并终核文档。

## 所有权、控制流与资源边界

[web.py](../../src/ergora/web.py) 的 118–120 行是 HTTP 正文接口，继承既有 `extra="forbid"`，只接受原 run 和严格整数 1–60 秒超时；335–350 行是 FastAPI 路由回调，留在唯一传输所有者内合理，无须抽取单用模块。既有同源、请求头、TrustedHost 和错误处理继续生效。run 的归属和更细身份规则由原用例负责，Web 没有再建任务校验或 revision/批准协议。

实际复用链为新 POST → `tasks.handoff` → `reference.task_handoff` → 原专用原生进程 `export-handoff` → `_Inspection`/FileAdapter → `handoff.create`。CLI 与 Web 是同一任务用例的两个真实生产消费者。闭合原 history、原合同/回执和材料语义仍由既有所有者核验，Web 只负责下载；没有新增收集器、持久下载记录、任务执行、Git 或 lease 操作，也没有复制离线 ZIP/schema 校验。新增测试文件复用 `test_handoff.evidence` 的纯数据，不把完整原生/Git fixture 作为传输测试前置。

每次请求使用标准库私有 `TemporaryDirectory`，在其中选择不存在的固定目标。文件句柄先关闭，目录上下文随后退出，最后才构造携带 bytes 的 `Response`；成功和普通异常均沿该生命周期清理，不依赖发送结束后的后台删文件。读回上限保护 Web 的实际内存输入，SHA 比较保护原生收集后到发送前的字节一致性，两者具有独立传输职责，并非重复格式校验。固定 attachment 名称不拼入用户字段；摘要头对应实际响应字节。运行检查观察的是请求完成后目录为空；“构造/发送响应前清理”的顺序另由上述源码确认。

新增同步路由沿用 FastAPI 的工作线程执行方式。最多 72 MiB 的包缓冲不等于进程峰值内存、完整收集 IO 或并发总量限制；文档未作此承诺，也明确保留强制退出后的残留处理。新代码使用标准库路径/临时目录并在删除前关闭文件，未引入 Windows 特有句柄竞争或 POSIX shell 依赖；原生收集仍沿用已有 Linux/WSL2 门禁。Windows 实际验收须由 b 自己的 CI 提供。

## 证据核对与轻量复核

1. 逐读原命令、退出码和日志：基线包 9 项缺入口反例均因 404 失败；源码 25 项、最终非 editable 包 27 项通过。后者是 16 项传输、9 项既有架构与 2 项旧 HTTP 代表，未设置源码 `PYTHONPATH`。新测试检查实际 ZIP/离线可验证性、原参数转发、同源/正文拒绝不调用收集、三类失败清理和 GET 禁止隐式收集，保护了改变的合同。沿用现有双 OS workflow，无新增依赖、CI 作业或格式矩阵；一个上游 TestClient 弃用 warning 保留，没有据此加装其他 HTTP 栈。
2. 审查者独立对全部 352 个源码资源、wheel 成员和两份安装重算 SHA，完全相同；安装元数据指向该 wheel，均非 editable。与 a 的最终包逐项比较仅 `web.py` 不同；283 个冻结资源不变。
3. 读取实际 HTTP 脚本、进程命令、原日志和响应头，确认最终安装通过 CLI serve 启动 loopback socket，未替换任务端口或用 ASGI 客户端充当本段验收。三次成功、六次原 run/项目/路径/同源/请求头/方法拒绝与日志一致。审查者重新核三份响应包的整包 SHA、与 a 原 CLI 包的字节一致性及 F5.2 原索引；逐回执对照全部 43 份源材料，原 `REVIEW_READY`、`CANCEL_UNCONFIRMED` 保持。
4. 另使用现成最终基础安装的真实 CLI 独立离线验证三包，三次退出 0、外部 SHA matches；该安装无 Temporal/FastAPI/Uvicorn，指定的独立 control 子目录均未创建。没有启动服务或重演工作流。
5. 原 before/after 快照完全相同；读取其完整 history/outcome 对照脚本和成功日志，三原 history 事件数为 329/348/112。审查者当前再核 139 原文件、两业务仓库内容/HEAD/refs/worktrees 和三 claims/零 active lease，均与快照一致。没有为审查重新连接已退出的 Temporal 服务，history 一致性结论取自已检查的本片实际前后运行证据。
6. 对照 shutdown 原回执与 Uvicorn 原日志，HTTP 的真实 `-15` 返回码与 application shutdown complete/finished PID 相符；审查者再查确认 HTTP 和两个 owned 服务进程已退出、五相关端口关闭、临时根为空、三个持久数据库保留。未把强杀成功当作有序退出。
7. 原静态记录绑定当时 8 份文档、246 本地链接/锚点和 README 30 条 parser 命令，结果与初始文档身份相符；不把这个结果自动延伸到审查中追加的进度记账或本报告。

HTTP 约 1.59–1.88 秒、离线约 0.22–1.02 秒的记录只覆盖本次 11–185 KB、1–23 份材料，不证明最大载荷、并发吞吐、峰值内存或 Windows 运行结果。现有按影响选择的检查与该小改动相称，无须为未修改的格式算法重复昂贵验收。

## 剩余交付

提交前刷新完整清单和文档链接/命令检查，绑定 b 的精确提交及 Git 归档与最终包身份，普通推送并核实时远端；完成该提交自己的 Ubuntu/Windows 必要 CI 步骤，再由同片审查登记最终终结。a 的独立终结单独保留；F5.4 页面及完整 F5/G0 不在本报告关闭。

## 精确提交、发行、静态与远端复核

2026-11-05，同一独立审查者从 Git 对象核候选 `bde57e17d84a0063683be9c5c34392072b255853`，唯一父提交为原基线 `87538b3dcafb13ca5bbc8191f84e5a4b0fbf0083`。`diff-tree` 正好 12 文件，逐项重算提交 blob SHA，全部等于刷新后的 `final-review-scope.json`；其 tracked 部分逐字等于 `final-review-tracked.diff`。前述进度记账漂移已纳入最终清单，生产和新测试仍为已审身份。后续 F5.4 工作树不计入此次提交复核。

独立在内存读取精确提交的 Git archive，352 个包资源逐项等于原最终 `54548bc34aeb8cf7d9f55a62cbf3d1ef3f27695f5880afe5898fd99ec53095ae` wheel 及其身份表。另从该提交文档对象核对全部 10 份 Markdown 的 346 个本地链接/锚点，并使用已核同包的最终安装 parser 解析提交 README 的 30 条命令，全部通过；`static-documents.json` 中的文档 SHA、数量和命令列表与精确提交一致，没有借用后续工作树文件。

读取实际普通 push 的命令、退出码及 stdout/stderr，确认原基线正常快进到候选，没有 `--force` 或强制 refspec。传输配置不改变 ref 更新语义。审查者另于 `2026-11-04 22:26:40 UTC` 执行只读实时 `ls-remote`，远端 `refactor/architecture-foundations` 完整 SHA 仍为该候选。本轮没有执行提交、推送、安装、服务启动或测试矩阵。

**精确提交、最终包、提交文档静态检查及普通推送/实时远端通过，无新增 finding。b 的精确双 OS CI 尚未在本轮核定，完整终结继续待验。** 前片 a 的 CI 不归给 b；待取得该候选自己的 run/job 原证据后再登记同片最终结论。

## 精确 CI 与同片最终终结

2026-11-05，同一独立审查者完成本片剩余验收。再次从 Git 对象重算候选 `bde57e17d84a0063683be9c5c34392072b255853` 的 12 个变更文件摘要，全部仍与最终清单一致，唯一父提交保持原基线。未将后续 F5.4 的未提交页面、文档或运行证据计入本片。

先重算 `ci-html-status.json` 所列 6 份官方原始 HTML/JSON 的字节数与 SHA，全部吻合；独立解析原页面，核对 actions 行、run selection、job groups、精确提交链接及 workflow。另在 `2026-11-04 22:40:31 UTC` 前从 GitHub 重新只读取得本 run 及两个 job 的官方 HTML，确认相同结论：[Portability 41925067903](https://github.com/626619403/Ergora/actions/runs/41925067903) 为 `Success`，完整 commit 为本候选，workflow 为 `.github/workflows/portability.yml`。

- [Windows job 126907187498](https://github.com/626619403/Ergora/actions/runs/41925067903/job/126907187498)：Windows/Python 3.12，构建安装、包身份、原生回归及 PowerShell 5.1 安装升级四个必要步骤全部完成且 `success`。
- [Ubuntu job 126907188269](https://github.com/626619403/Ergora/actions/runs/41925067903/job/126907188269)：Ubuntu/Python 3.11，构建安装、包身份及原生回归三个必要步骤全部完成且 `success`。

每个 job 的平台名与内嵌 `selectedJobId` 相符；各必要步骤均有完成标记，其日志 URL 包含完整候选 SHA 及对应 check/job ID，未见失败、取消或超时步骤。结论来自原页面和独立实时读取，没有仅采信作者汇总，也不继承 a 片 CI。审查者另于 `2026-11-04 22:40:32 UTC` 只读实时 `ls-remote`，确认远端 `refactor/architecture-foundations` 完整 SHA 仍为本候选。

结合前述本地需求/资源生命周期验收、包与 Git 归档一致、最终静态检查及普通推送证据，**F5.3b 需求符合性、可维护性及精确发行/双 OS CI/远端验收全部通过，无未解决 finding，可登记本片完成。** 本轮未安装、启动服务、运行测试矩阵、提交或推送，仅追加原片终结记账。F5.4 页面及完整 F5/G0 继续按其各自范围验收。
