# F5.3a 独立审查

日期：2026-11-05。审查者：新的独立上下文 `handoff_format_review`，未继承实现对话；先读原始验收、实际差异、新文件和相邻调用者，再读作者交付记录。按本项目 `AGENTS.md` 及 `maintainable-project-delivery` 的 independent-review brief 执行。本报告只审 F5.3a 原生收集与离线验证；HTTP 下载、页面、F5.2 终结记账不在本次行为审查范围。

初审基线与 HEAD 均为 `bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`，候选为未提交工作树。独立重算 `review-scope.json` 所列 15 个 tracked、4 个新增文件的 SHA，全部相符；核对真实 Git diff 与清单。完整读取新增 `handoff.py`、`task-handoff-v1.json`、`test_handoff.py`，以及修改的 CLI/tasks/reference/reconciliation、两份既有测试和相关公开文档；相邻核对原 `_Creation`、`_Submission.lookup_run`、冻结 `FileAdapter`、合同验证器、CI 与已有测试夹具。精确初审包为 `2a0f8297489b3f650effb761917ec6fd1e23b04517f267300ce01feb098358f5`。

初审需求符合性：**暂不通过，有两项 P2 待修复复核**。原生收集范围、固定原 run、内容寻址去重、不覆盖发布和无服务验证的主体实现符合范围；外来 manifest 的格式/内部一致性校验存在下列缺口。可维护性：模块所有权与真实复用合理，无额外结构性阻塞；格式与原回执规则的漂移必须在本片收口。

1. **P2：外来回执标识格式比冻结 FileAdapter 宽松，仍会返回 `verified`。** 位置：[schema 的 digest/identifier](../../src/ergora/data/schemas/task-handoff-v1.json#L49)、[check.id](../../src/ergora/data/schemas/task-handoff-v1.json#L87)，使用入口 [handoff.verify](../../src/ergora/handoff.py#L174)。`check.id` 仅要求长度非零，故 `"   "` 被接受；冻结 `FileAdapter.verify_receipt` 要求 `bool(id.strip())`。另 `^[…]$` 在当前 Python/jsonschema 正则实现中可在末尾 LF 前匹配，故 `job_id` 或 `job_sha256` 追加一个换行仍满足 schema，而冻结 `identifier`/digest 使用 `re.fullmatch` 会拒绝。独立使用初审最终包的基础安装，从实际正常交接包制作三个临时副本，分别改空白 check ID、末尾 LF job ID、末尾 LF job digest，并更新 receipt、history job 集合、index 等相关摘要及 outcome 引用状态，三者均返回 `status: verified`。这不是未更新摘要造成的普通校验失败，而是校验接受了原回执协议不可能产生的声明。最小修正：在外来 schema 边界将非空白检查 ID 和字符串完整匹配规则与冻结协议对齐，检查同类 candidate/blob key 模式；补充全部摘要保持自洽的针对反例。无需让原生 collector 导入 SDK 或 Schema 库，也无需修改冻结 FileAdapter。

2. **P2：闭合 Temporal 状态与原 outcome 的相互约束遗漏。** 位置：[index.temporal_status](../../src/ergora/data/schemas/task-handoff-v1.json#L294)、[original_outcome](../../src/ergora/data/schemas/task-handoff-v1.json#L396)，及 [handoff._references](../../src/ergora/handoff.py#L42)。原生 `_Inspection.run` 只在 `COMPLETED` 时读取并要求对象 outcome，其余闭合状态均构造 `None`；离线格式却分别允许任一闭合状态及 object/null。独立将实际正常包改成 `FAILED + 原 REVIEW_READY outcome`，或保留 `COMPLETED` 但置 outcome 为 null，并同步 outcome/index 摘要及各 job 的 outcome 引用状态，两者均返回 `verified`。因此同一个已校验 manifest 可以声明互相矛盾的终态/原结果，或静默丢失原有结果；这属于包内一致性范围，与是否认证来源无关。最小修正：在版本化 schema 中约束 `COMPLETED` 必须为对象 outcome，其余列明的终态必须为 null；保留已有 outcome 摘要/任务关联校验，并为两个方向添加摘要自洽的离线反例。原业务失败、取消等状态字段仍应原样保留，不能转为执行成功。

所有权及必要守卫核对：`handoff` 有两个不同生产文件的实际消费者：原生 `reference_task_reconciliation` 调用 `create`，CLI 调用 `verify`。新模块拥有受限归档格式和两入口共享的身份关联算法，比放入带 State/SDK 的任务模块更合适。`tasks.handoff`/`reference.task_handoff` 延续既有用例与专用解释器边界，不是虚构复用。原 run/项目/提交/history/FileAdapter 的校验继续由已有所有者负责；读取回调只取得回执指定的安全路径材料。ZIP/JSON 结构、成员集合、重复键/成员、大小、字节摘要和声明关联属于离线入口的必要守卫；collector 不重复 Schema 校验符合其已核内部输入边界。未建议删除现有生产守卫、增加框架或抽取通用执行器。

证明范围核对：spec/request/profile/bindings、receipt、history job 集合摘要及 blob 可从包内字节重算；creation/submission/job context/history/Git 对象不齐备，相关 SHA 只能作引用。输出固定 `origin_authenticated: false`、`execution_success: null`，外部整包 SHA 的 matches 也不升级为认证。公开说明准确区分来源认证、工作流采用、检查结论、候选复验和交接包验证；上述 findings 要求的是现有“声明内部一致”的合同，没有要求新增签名或离线重演。

资源、性能与验证成本核对：成员直接读取、不提取执行，仅允许 stored ZIP，目标用同目录临时文件 fsync 后硬链接仅创建发布，已有目标及竞争目标保持。整包、manifest、单 blob、去重总量和成员数均有显式上限。原索引仍有完整 history 扫描和 FileAdapter 对每个原引用的读取，collector 再读取每个唯一内容；这些成本未被误述为一次 1 MiB IO。`ZipFile` 在成员数检查前解析中心目录，整包和成员缓冲亦占内存，因此这些上限不构成峰值内存或 4096 条预解析内存保证，文档已明确限制；未测最大载荷吞吐。新增纯格式用例不引入重型原生初始化，少量原生用例复用既有夹具；没有增加 CI job、矩阵或依赖。初包 96 项与修包 97 项、旧代表 4 项身份分开记账，修包定向日志总耗时约 3.29 秒，未以重复昂贵矩阵代替边界验证。

实际核对及限制：

- 独立读取和重算最终 wheel、352 个源码资源、两套 noneditable 安装的全部文件 SHA，四者完全相同；283 个冻结资源与既有冻结身份一致。核对首包 `ee0ea8…` 的真实 `rpds.rpds` 失败及延迟导入修正；collector 保持标准库依赖，外来 verify 才加载现有 Schema 库。
- 独立在无 Temporal/FastAPI/Uvicorn 的基础安装中重核三个最终交接包，并逐回执/逐 blob 对照真实原文件；两正常模板分别为 23/19 个 blob、105296/156248 字节，取消包为 1 个 blob、59 字节。三索引逐字段等于前片真实观察，原结果分别保持两项 `REVIEW_READY` 和一项 `CANCEL_UNCONFIRMED`。这些正例均通过；上述五个坏包反例也均被当前实现错误接受。
- 独立比对 native before/after 完整记录相同，并重新读取当前 139 个原文件重算 SHA，仍与 before 完全相同；记录包含三原 history/outcome、两业务 repo 内容/HEAD/refs/worktrees、三 claim 和零 active lease。查看真实导出、已有目标/错误 run/跨项目/错误外部 SHA 的命令与 stderr，以及正式 shutdown、owned 进程退出、端口关闭、数据库保留、最终 offline 核对记录；没有启动服务、SDK 会话、worker 或模型。
- 检查最终 97 项定向命令/日志、首包旧代表 4 项日志和最终 10 份文档/341 本地链接与锚点/30 条 README parser 命令记录。审查者未重复完整矩阵、安装或原生导出，未实施源码修改、提交或推送。针对坏包只写隔离临时文件，结束后清理。
- Windows 可运行性已有标准库和基础依赖路径、无 State 初始化分派及平台测试安排的静态依据；原生 collector 仍明确要求 Linux/WSL2。当前初审未实际运行 Windows，不能将 Linux 包验收或前片 CI 视为本候选 Windows 通过；需要修后精确提交的双 OS CI。

本片尚待：修复两项 P2并同片独立复核；保留旧包和失败记录、绑定修后源码/测试及最终安装身份，运行受影响轻量校验并核原包兼容性；再完成最终文档终核、精确提交/普通推送、实时远端与精确双 OS CI 及同片终结。F5.3b HTTP 下载、F5.4 页面和完整 F5/G0 不由本报告关闭。

## 两项修正的同片复核

2026-11-05，同一独立审查者复核，Git 基线/HEAD 仍为 `bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`。逐文件重算 `review-fixed-scope.json` 的 SHA 全部相符；从保留的初审 wheel 直接导出旧 schema 与当前文件作 diff，确认唯一生产资源变化为 `task-handoff-v1.json`，SHA 为 `dbfd84544eddf0a211eebcc54bbfd13d89dc85e2bd365899fe632121f4b6a0f8`。其余变化仅为六个针对反例及本片文档记账，没有新增生产分支、守卫、依赖、CI 或冻结资源修改。

**需求符合性和可维护性均通过本地复核；两项 P2 关闭，范围内无未解决 finding。** 第一项由 schema 的非空白 `check.id` 和 digest/identifier/candidate/blob key 的绝对末尾匹配修正，negative lookahead 使用 ECMAScript 兼容表达式，无 Python 专用末尾语法。第二项由 `index` 的 if/then/else 限定 `COMPLETED` 对象 outcome、其余已枚举终态 null outcome；原 outcome 摘要和任务关联检查保持。约束仍位于外来格式入口，不增加原生 collector 的 Schema/SDK 依赖，也不把包内一致性提升为来源认证或执行成功。

新增六个反例会重算 receipt、原 outcome、history job 集合与 index 摘要，并保持相应 outcome 引用一致。核对初审已安装 `2a0f829…` 包上的红例日志，六项均因“未抛错”失败；源码修后及最终安装的 103 项定向日志均通过，各保留同一上游弃用 warning。审查者另用最终基础安装对真实正常交接包的临时副本独立重放空白检查 ID、换行 job ID、换行 job digest、换行 candidate、COMPLETED/null、FAILED/对象六种变更，均由 `Handoff manifest` 结构约束拒绝；四种合法非 COMPLETED 闭合状态加 null outcome 仍可通过。该检查使用实际包和独立重算逻辑，没有仅依赖作者测试夹具。

独立重算最终 `cdf4ab628a8856ee39c30d6e1857f243c3a5c718ee209371162e8d79f6ee3c0c` wheel、当前源码和两套 noneditable 安装的全部 352 资源 SHA，完全一致；283 冻结资源保持。初审 `2a0f829…` wheel 及其身份记录仍在，摘要未变。实际原生收集属于 `2a0f829…`；最终 reader 属于 `cdf4ab…`。两包全部 collector/CLI/native 源码逐字节相同，变更 schema 只在 verify 时用于外来结构验收，所以本次不重启服务或重复生产收集是有依据的验证裁剪。

核对最终离线脚本、逐命令输出及 `final-offline-packets.json` 后，审查者另用最终无 Temporal/FastAPI/Uvicorn 的基础 CLI、独立临时 `--home` 重核原三个包；三次退出 0、外部 SHA matches、指定控制目录均未创建。两正常原结果和取消原结果保持，23/19/1 个 blob 及 105296/156248/59 字节保持；逐 blob 再与原文件核对，共 43 份材料一致，整包 SHA 亦保持。再次重算当前 139 个原文件，与初审 before 摘要仍完全相同。没有重复安装、运行宽矩阵、开启服务或 SDK 会话。

本地源码/格式与受影响证据验收已足够，没有新增结构、性能或冗余验证 finding。尚待更新最终状态并终核文档、创建精确提交和普通推送、核实时远端及该提交的完整双 OS CI，再由同片独立审查登记终结；本次未实际运行 Windows，不以历史 CI 代替。HTTP 下载与页面仍分别属于后续切片，完整 F5.3/F5/G0 未由此次复核关闭。
