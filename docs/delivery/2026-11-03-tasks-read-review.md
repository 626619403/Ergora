# F3.1 正式任务只读入口独立审查

日期：2026-11-03。审查者：独立 fresh-context reviewer `/root/f3_tasks_read_review`。先读取原始差异及新文件，再读取作者交付叙述；未继承实现会话。使用 `maintainable-project-delivery` 与 `review-pr`，未修改生产源码、安装、真实服务或旧任务。

## 范围与身份

审查基线为 `c272ce1`，生产前基线 `67d88ec`。检查完整 tracked diff，另检查新增 `src/ergora/tasks.py`、`tests/test_tasks.py`；生产变化为 `cli.py`、`web.py`、`tasks.py`、`reference.py`。同时读根 AGENTS、PLAN、详细计划 F3、活动交付记录、使用/项目/Agent 手册、架构及 reference 边界文档，并沿原 `core`、`projects`、`adapter`、`contracts` 和选择式 executor 核对合同来源。冻结 reference 文件无本切片 diff。

本轮初审对应非 editable wheel SHA256 `df9cacbdf93bab49b916b05e7e8f67594c4c98388435922dc40edd45db38e187`。初审源码 SHA256：`reference.py` 为 `7ba1ae6f0e522a403a50e5f2c3c15ae0a4aaefba7efe3d5f2f0afab451ac5689`，`tasks.py` 为 `81614c6a19fe0d8c9ea915eebcf8b66d1e068de35064de2b9e445895c2ab1c79`，`tests/test_tasks.py` 为 `59514b6dba7e28e366044fbc43adf16071a6833057622aefc7c3fe36b2345c78`。修正后的结论须另行复核，不继承该包的验证身份。

## 初审结论

需求符合性：主体范围正确，以下三项修正前未通过。可维护性：用例、reference 读取边界与传输所有权清晰；以下资源边界和错误映射问题修正后复审。完整 F3 尚未交付，F3.2–F3.4 不在本次通过范围。

1. **P2 / CONFIRMED：非 UTF-8 原生目录名使分页整体失败。** 初审位置 `src/ergora/reference.py:363`、`:366`、`:380`。在 POSIX 的隔离状态目录创建字节名 `a\\xff` 和后续 `z`，以 `limit=1` 调用：损坏项计数完成后，`next_after` 含 Python surrogate `a\\udcff`，`ensure_ascii=False` 的 UTF-8 stdout 输出抛出编码错误。实测返回 `ValueError: BLOCKED: 'utf-8' codec can't encode character '\\udcff' ... surrogates not allowed`；用户无法取得下一页。只改子进程 JSON escaping 仍会把不可 UTF-8 的 Python 字符串传给 CLI/API。最小方向是可往返的 ASCII 不透明游标，原生名只在读取进程内部比较，补真实字节名回归。置信度 100。
2. **P2 / CONFIRMED：只读进程超时或无 stderr 退出逃出公共错误映射。** 初审位置 `src/ergora/reference.py:280`、`:286`。作者提出该候选后，审查者独立故障注入确认 `subprocess.TimeoutExpired` 原样抛出；`CompletedProcess(..., -9, '', '')` 导致 `IndexError`。前者可由慢/阻塞文件系统达到 30 秒预算触发，后者可由子进程被外部终止触发。CLI 既有 handler 和 Web `ValueError/OSError` handler 均未覆盖这些类型，表现为 traceback/HTTP 500。应在新读取边界转成有意义的 `ValueError`，空 stderr 回退到退出码，并保持不重试。无需扩改旧注册边界。置信度 100。
3. **P2 / CONFIRMED：Python 3.11 的目录枚举仍常驻全部名称。** 初审位置 `src/ergora/reference.py:363`。支持基线 Python 3.11.15 的 `Path.iterdir` 源码为 `for name in os.listdir(self)`；实际先物化 N 个名称，再交给有界 heap。因此当前代码注释与交付记录所述“常驻候选名至多 limit+1”不能成立，大型共享任务目录仍有 O(N) 名称内存开销。使用 `with os.scandir(directory) as entries` 的流式生成器即可保留 heap 窗口并明确关闭目录句柄。即使修正后，每页为取得按名排序的窗口仍需 O(N) 枚举；最多 100 项指合同检查数量，不能写成整个目录只枚举 100 个名称。置信度 100。

## 结构、复用与必要分支

`tasks.listing/show` 的真实生产消费者分别为 CLI 和 Web；该模块拥有 published 注册前提、页大小和当前项目修订。新 `reference.task_files` 虽只由 tasks 模块调用，但它拥有固定包代码、原生布局、安全读与专用进程隔离，是已有 reference 职责的必要入口，不应移入 CLI/Web 或为增加调用者再造封装。进程内 `document/owns/inspect` 是凝聚的私有读取算法，无需新基类、通用 repository 或额外 SDK。

逐层核对了 published/limit、ID/path、普通文件、JSON object、项目名/Git 根、tracker、冻结基线、spec 摘要、目录 task ID、可选绑定项目及 Windows 读取分支。检查均对应外部参数、持久文件或跨平台读取的不变量；列表先确认归属再公开合同错误，无法确认归属的项只计数。任务 spec 继续由原 `validate_spec` 检查，未复制六阶段/可信 integrate/verify 语义。静态路径未发现 Temporal、凭据、ledger、日志、任务写入或运行成功推断；`runtime_status` 保持 `not_queried`。本次未发现进一步模块所有权或不必要抽象问题。

## 实际检查与证据限制

- 独立执行 `PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q tests/test_tasks.py -p no:cacheprovider`：23 passed，11.98 秒；仅有已有 FastAPI/Starlette deprecation warning。未运行整套回归或安装。
- 独立 `/tmp` 隔离非 UTF-8 目录复现及两项 subprocess 故障注入均得到上述结果；未接触真实用户服务。通过 `inspect.getsource(pathlib.Path.iterdir)` 核实当前解释器确实使用 `os.listdir`。
- 审阅 `final-package-identity.json` 并独立计算 wheel SHA256 一致；记录声称源码/wheel/两安装 339 文件一致。审阅 `final-legacy-journey.py/json/log`：基础安装通过显式旧注册采用读取两个真实旧任务，spec/绑定可读、顶层任务文件字节未变，无 SDK/Temporal 查询。该证据不代表新的六阶段或模型效果验收。
- 审阅 `final-performance.py/json/log`：Linux Python 3.11.15，同一非 editable 包，1000 份编译合同、每页 100 项、20 次首列表查询，中位 370.6 ms、最大 595.0 ms、最大 JSON 45,970 B；十页 1000 项无重复遗漏。客户端 peak RSS 增量 144 KiB 不能证明子进程内存上界，更不能支持 O(limit) 的目录枚举声明。该测量为规模限定的查询开销，未声称优化收益；更大目录/冷缓存未测。
- 初审时最终包完整回归仍运行，精确候选两 OS CI 尚未触发。初版 `e238…` 包回归不用于当前包的最终结论。修正后须重包、复核适用定向/回归/性能/旧任务证据，并补最终身份和两 OS CI 后才能收口。

## 复审状态

### 修正后源码复审

上述三组 P2 均已关闭，无新增阻塞 finding。需求符合性与可维护性在本切片源码范围通过；发行收口仍需下述最终包证据。修正后 SHA256：`reference.py` 为 `4c76454a2acaa690b9a1898db2c7de7aa09ac5032c168a64c3e309c51da20af6`，`cli.py` 为 `e1ad093b699136e9b117a7cb73d9327f225ba109e21cfb8c85592e324ef19cad`，`tasks.py` 为 `3d79293d78c83a2020671cacc45f38872dcb813085f7f1aa635e83984c5579f7`，`tests/test_tasks.py` 为 `c49fb5ab1a19754ada9ab854f5832545eecb134427b8a5ae137dddcb3c32c474`。

- `reference.py:308` 在读取进程内解码标准 base64url/fsencode 游标；`:379` 只输出 ASCII token。目录名仍只参与内部排序，不能因游标变成路径。独立 `/tmp` 真实字节目录探针经 CLI 取得首个空页及游标，再经 API 正确取得 `first`；未把 surrogate 泄露至 JSON。
- `reference.py:287`、`:289` 对超时和无 stderr 退出转为明确 `ValueError`。独立 API 故障注入分别返回 HTTP 400 与具体原因，调用次数均为 1；无自动重试。
- `reference.py:373` 使用 `with os.scandir` 及 heap 生成器，不再有 Python 3.11 `Path.iterdir` 的全名称列表。手册明确每页枚举全部 N 个名称、`inspected_entries` 只计最多 100 个候选合同检查；未引入数据库镜像或缓存。
- 独立执行 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -m pytest -q tests/test_tasks.py -p no:cacheprovider`：26 passed，12.68 秒；显式选择当前源码，未误用旧安装。`git diff --check` 通过。

`df9c…` 包的完整回归后来记录为 347 passed、19 skipped、36 subtests passed（181.60 秒），该身份已被源码修正取代，保留为历史。待作者统一重包后，再核对实际包/源码身份、适用完整回归、旧任务只读复验、新性能与精确两 OS CI；当前不把这些待补项目写成通过。

### 最终候选本地归档复核

最终生产/测试候选为 `13e9f33623c5811547bdb43d3b2b0218b62ffda2`。独立核对当前 HEAD 与本地远端跟踪引用均指向该提交，提交所含生产源码和测试 SHA256 与上述源码复审一致；生产源码未在复审后变化。最终本地归档通过，无新增 finding；精确两 OS CI 仍单独待核实。

- 独立重算 `.ergora/checks/f3-tasks-read/review-fixed-dist/ergora-0.2.0-py3-none-any.whl` 的 SHA256 为 `2fa1915726503715d312e839c7d0672165503c7f855b23ecdb77c7bdd29da3e7`，逐文件核对源码、wheel、`.venv-dev` 及 `base-venv` 各 339 个文件完全一致，且匹配 `review-fixed-package-identity.json`。独立执行已安装 `reference.verify()` 为 PASS / 283 文件；基线至候选的冻结 reference diff 为空。
- 审阅最终 build/install 日志：该 wheel 已装入 Linux Python 3.11.15 的开发环境及 Python 3.12.3 的基础环境。独立基础环境探针确认 `tasks.__file__` 来自该非 editable 安装，`fastapi`、`temporalio`、`gepa` 均不可导入。
- `review-fixed-wheel-regression.log` 完整记录 **350 passed、19 skipped、36 subtests passed，182.00 秒**，只含已知 Starlette deprecation warning。该日志 SHA256 为 `5f283b2852de53ad3be174f7e060ca50d92c4594e4ca7d1ad5dee736d14d20d1`。此处审阅作者最终包回归记录，未另跑整套回归；此前独立 26 项及边界探针继续绑定相同源码身份。
- 审阅 `review-fixed-performance.py/json/log` 并核对 JSON 与日志相等、实际 fixture 目录为 1000 项。脚本每次断言 `inspected_entries == 100`，20 次查询中位 **396.7 ms**、最大 **600.8 ms**、最大 JSON **45,975 B**；十页恰好取得 1000 个唯一任务。每页仍 O(N) 流式枚举全部名称，测量仅覆盖该规模及本地缓存条件；客户端 peak RSS 高水位增量 0 不等于零分配，也不说明子进程峰值。未把与旧包的耗时差异解释为性能收益或回退。
- 审阅 `review-fixed-legacy-journey.py/json/log` 并核对 JSON 与日志相等：最终基础安装读取 `repository-governance` 与 `large-change` 两个真实旧任务，返回 spec 及冻结绑定、`runtime_status=not_queried`；所检查顶层任务文件前后摘要一致。脚本只复制项目/策略输入到独立控制目录并显式采用，读取原 task store；未从该旅程推导实时状态、模型效果或新的六阶段验收。审查者本轮未重跑涉及实际旧任务的旅程。

本轮读取的 CI 归档 `ci/ci-html-run-selection.json` 对应 [Portability 41519399689](https://github.com/626619403/Ergora/actions/runs/41519399689)，原始 commit 链接精确匹配 `13e9f33623c5811547bdb43d3b2b0218b62ffda2`；当时为 `WORKFLOW_RUN_STATUS_IN_PROGRESS`。已读该提交的 workflow：Ubuntu/Python 3.11 与 Windows/Python 3.12 均构建非 editable wheel、核对冻结参考并运行适用回归，Windows 另验 PowerShell 5.1 安装升级。**最终本地证据已通过；两平台结果尚未据此宣称通过，F3.1 交付状态需待精确 CI 结果后收口。**
