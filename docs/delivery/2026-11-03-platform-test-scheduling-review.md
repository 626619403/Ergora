# V2 平台调度独立审查

2026-11-03。审查者：`/root/verification_platform_scheduling_review`，独立 fresh-context。先读取仓库规则及原始补丁，再读取本切片报告和计划；采用 `maintainable-project-delivery` independent-review 与 `review-pr`。没有修改实现、安装环境、运行完整回归、提交或外部写入。

## 结论与身份

**最终复核通过，无 findings，V2 可收口。** 需求符合性、可维护性及共同精确候选的 Windows/Ubuntu 完整 CI 均已核对；具体证据见末节。以下源码检查及“待验”边界保留为初次源码审查记录，不把模拟探针报告为 Windows 实测。

基线为 `c6a08f994ac9d12cc8370f0013af3cd0c447ff03`，审查对象为当时未提交的七文件工作区候选：

- `tests/test_task_submission.py`
- `tests/test_task_submission_locks.py`
- `tests/test_task_approval.py`
- `tests/test_task_cancellation.py`
- `tests/test_task_export.py`
- `tests/test_task_external_status.py`
- `tests/test_tasks.py`

独立重算七文件逐一 SHA256 与 `source-identity.json` 完全一致，对应记录的 aggregate `b59a9e84fb5bb8ebaa98a9a417602ef17d3b1fef84520fb69ae0fc8b8ccdd6df`；真实 `git diff` 与提供的 `tracked.diff` 一致，`src/` 对基线无差异。完整文件身份及可复现检查在 `.ergora/checks/verification-platform-scheduling/reviewer/source-and-collection.json`、`review-probe.py`。

## 源码、消费者与隔离

六个新增模块标记使用 pytest 标准 `skipif(sys.platform != 'linux')`，Linux/WSL2 不跳过，win32/darwin 条件为真。实际 pytest 9.2.0 的 `_pytest.skipping.pytest_runtest_setup` 带 `tryfirst=True`，命中后抛出 skip；它发生在 runner 调用 `_setupstate.setup(item)` 之前，因此可以阻止 `installation → registration → creation_project → submitted_creation/export_task` 的前置初始化。模块标记不通过导入的 fixture 传播，六处模块标记分别覆盖实际收集所有者，是必要的调度边界。

检查全部测试模块的 fixture 导入及参数消费者，`submitted_creation`、`native_client`、`export_task/client`、`approval_task/client`、`cancellation_task/client`、`external_task/client` 的实际消费者全部位于这六模块。它们通过 `reference._task_operation`（`src/ergora/reference.py:371`）进入明确要求 Linux 的完整原生环境；没有把可跨平台的原生状态查询整体标成 Linux。

两项平台提示函数移到 `tests/test_tasks.py:226`、`:238` 后，仍使用原 `creation_project`、原错误预期和原平台/文件探针。十个相关模块的 **152 个顶层函数定义完整 AST 均保持**，其中 115 个测试函数仅这两项改变路径；参数装饰器、fixture 和辅助函数未变。独立收集与原清单按两项路径映射逐一比对，323 个 nodeid 及每个实例的 fixture 名称集合全部相等，覆盖未因仅比较数量而漏掉替换。

`installation` 仍是定义于 `test_registrations` 的 module-scope fixture，`registration`/`creation_project` 仍为 function scope；没有共享可写 session 安装树。`test_tasks` 原本已拥有自己的安装 fixture；新测试不引入 Linux 成功操作，缺环境测试删除的仅是本模块安装树内可能存在的 `.venv` 符号链接。平台猴补丁由原 `monkeypatch` 恢复。新导入链为 `test_tasks → test_task_creation → test_registrations`，已有 `test_task_runtime → test_tasks` 无回边、无循环。

## 跨平台、冗余与性能

独立实际收集得到六模块 218 个实例带模块标记，其他四个相关模块的 105 个实例均无该模块标记；29 项纯输入及两个移动的平台提示仍在其内。另行只收集了 6 项原生 Windows 测试与 8 项原有安装测试，未引入这六个 Linux 模块的标记。`test_windows.py` 原有 Windows 控制/编译合同和工作流中的 PowerShell 5.1 安装升级步骤未变；这些读取、编译及安装合同仍需要精确 Windows CI 执行验收。

没有新增生产分支、断言、重试、测试案例、依赖、收集框架或 CI 步骤；三个 `sys` 导入各供所在模块标记使用。保留 fixture 内原保护符合切片合同，也保留 fixture 自身的环境边界。新增模块标记复用框架已有能力，避免非 Linux 已知无法运行的案例先进行注册/安装；没有据此推算时间收益。当前不存在本切片引入的冗余测试或重复运行门禁。

## 检查及未验边界

- 审查者执行 `.venv-dev/bin/python -B .ergora/checks/verification-platform-scheduling/reviewer/review-probe.py`：退出 0；直接从 Git 基线核函数/文件身份，只执行 `--collect-only`，共收集 337 项（相关 323＋相邻 14），fixture setup 命中 0。实际清单和输出在 reviewer 下 `collection.json`、`collection.log`。
- 审阅实施者原命令、日志及 JUnit：40 passed，93.49 秒，失败/错误/跳过均为 0；覆盖两项移动提示、29 项输入及六模块代表性 Linux 正常操作。此为已记录运行，审查者没有重复重型检查。
- 审阅 `simulate-nonlinux.py`、结果及日志：实际候选条件表达式在 linux/win32/darwin 上求值，并将 win32 结果用于 pytest 标记；218 项 setup-skip、0 次重型 fixture、29 项纯输入通过。探针不修改全局 `sys.platform`，没有模拟 Windows 文件系统/进程；报告对其范围的限定准确。
- 原 Windows 逐步日志公开接口 404 只证明日志未取得，不证明逐例数量或节省秒数。当前源码没有继承 V1 的 CI 验收；共同精确两 OS CI 尚未运行，本报告不关闭此验收门禁。

后续在 V2 七文件身份未变的共同候选上，核对完整两 OS 必需步骤、精确提交/工作流/测试身份及实际可得日志，再在本报告追加最终复核；若七文件有实质变化，先重新审查受影响范围。

## 共同精确候选最终复核

2026-11-03 09:53:07 UTC，同一 V2 审查者完成最终复核，**无新增 findings，剩余 V2 验收门禁已满足，可以收口**。独立复核脚本为 `.ergora/checks/verification-platform-scheduling/reviewer/final-review.py`，退出 0；完整结果在同目录 `final-verification.json`，重新读取的官方 run/两作业原始页面保存为 `final-run.html`、`final-job-125838059005.html`、`final-job-125838059675.html`。没有重跑测试、构建、安装或触发新 CI。

源码提交 `4a6d3d52dbb42dd6fc9328b49596498f812b112a` 对基线仅改变上述七文件；共同候选 `d5588855be0d5995465caa7e0af4b1b80103cc11` 在其后仅改变 `.github/workflows/portability.yml`。逐一读取两个提交的 Git blobs 和当前工作树，七文件 SHA256 均等于初审记录，b59a9e84…对应身份保持；347 个生产文件的 Git tree 与基线逐字相同，工作树也无生产改动。最终 workflow SHA256 为 `4d45c728e1f164aeeaabe080b00e5e4c58a19acb35ae4871d0364944647cf0a5`，扣除 V3 四行 concurrency 后与初审工作流相同，既有矩阵、依赖安装及全部必需步骤未减少。

独立重新读取官方 [CI 41612623462](https://github.com/626619403/Ergora/actions/runs/41612623462) 及两个作业页面，run 为 push 触发且状态 Success；页面完整 commit 链接及每个必需步骤的 log URL 均绑定 `d5588855be0d5995465caa7e0af4b1b80103cc11`，job selector 分别绑定下列作业：

|环境|作业|成功的必需步骤|
|---|---|---|
|windows-latest / Python 3.12|125838059005|Build and install wheel、Packaged reference identity、Native application regression、Windows PowerShell 5.1 installer and upgrade|
|ubuntu-latest / Python 3.11|125838059675|Build and install wheel、Packaged reference identity、Native application regression|

两作业 checkout/setup-python 亦均成功，无失败、取消或超时步骤；Ubuntu 的 Windows 安装步骤按原条件跳过。工作流实际从 wheel 安装 `[dev,web,gepa,temporal]`，回归命令为 `python -m pytest -q --tb=short --durations=20`：两 OS 均运行 `tests` 和冻结 `test_contracts.py`，Linux 继续追加 `test_portable.py`、`test_workflow.py::AdapterTests`、`test_runtime.py`。这确认原生 Windows 平台提示/控制/编译及独立 PowerShell 安装升级合同仍进入原完整门禁。平台提前 skip 的 setup 顺序由初审源码及调度探针支撑，不从 CI 步骤 success 推导逐例 skip 数量。

同时核对 `.ergora/checks/verification-ci-scheduling/ci/` 中官方原 HTML、selection 和 `ci-html-status.json` 的 SHA256、候选选择与平台步骤；这是本次共同候选证据，未借用 V1 CI。实时执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，返回完整 `d5588855be0d5995465caa7e0af4b1b80103cc11`，与本地 HEAD、两源码提交和本轮 CI 身份一致。

Windows 时长陈述范围也符合证据：原 V1 后候选 `4e01a4e53b9c1d787cf40ce8650d3397cc83b252` / 作业 125815506254 的回归步骤为 08:48:15–08:54:45 UTC，即 390 秒；共同候选 / 作业 125838059005 为 09:38:59–09:42:31 UTC，即 212 秒。独立核来源 HTML 的记录 SHA、完整候选及步骤起止，新官方最终页面与 212 秒一致。两项仅是不同 GitHub 运行的步骤观察，未控制 runner、缓存或其他环境因素，不据此给出受控加速率、因果收益或逐例/setup 耗时；公开 console 日志仍未取得，不填补未观察的用例计数。
