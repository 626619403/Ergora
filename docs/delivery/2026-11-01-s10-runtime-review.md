# S10.1 Windows 原生运行独立审查

审查者：Codex，全新上下文独立 reviewer。日期：2026-11-01。项目与文档均归属 Ergora；审查只读源码，唯一写入为本报告。

审查基线：`4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`。受审实现：`a2d22b79f14ee2b143736fcfda8fec69c24501e8`，开始时工作区干净。审查期间实现者通知另有 `3e9461c`，仅涉及 S10.2 安装器/CI，未给本报告继承新的运行时验收结论。

## 独立裁定

- **需求符合性：请求修改，Windows 验收未完成。** 发现原生工作流编译入口不能运行，以及评价器的 Windows 路径/入口解析不一致。正常结束、超时与控制器死亡有针对性 Windows 用例，但前台命令取消尚缺真实 Windows 信号证据。Linux 检查通过不能补足这些缺口。
- **可维护性：请求一项局部修正。** 锁在 `state`、命令生命周期在 `processes`、Job Object 在独立平台模块，归属清楚；`file_lock` 有记忆/研究/kernel 三个生产消费者，`Job` 有命令/研究两个生产消费者。新增私有 ctypes 结构直接服务 Win32 API，未发现为假想扩展创建的框架。评价器另写一套入口解析，已经出现行为分歧，应复用现有 `processes.resolve_program`。冻结编译器的适配必须位于冻结目录之外，并保留其文件读取约束。

## 发现

### R1 · P1：原生 workflow 编译入口调用 Windows 不支持的文件读取常量

位置：`src/ergora/reference.py:87`；必要调用者 `src/ergora/data/reference/platform/upstream/platform/dev_platform/portable.py:90` 与 `adapter.py:62`。跨切片声明：`docs/WINDOWS.md:10`。

`reference.workflow()` 仍直接启动冻结 `dev_platform.portable`。该模块的所有非 help 动作最终调用 `read_json()`，其 `_read_bytes()` 无条件引用 `os.O_NOFOLLOW`；Windows CPython 不提供此常量。`ergora workflow compile`、`convert-v2`、`validate`、`export-v2` 因而会发生 `AttributeError`。`adapter.read_raw()` 也引用同一常量，影响 immutable publish 的相同内容重试。模板复制、角色合同与通过 `make_spec` 校验 DAG 是其他路径，不受此处结论连带否定。

后果：手册列为原生支持的输入编译不能使用；`tests/test_reference.py:28` 的公开编译回归以及 Windows CI 直接运行的冻结 `test_portable.py` 不能通过。这里未伪造成功，但暴露的是解释器异常，未提供受限功能指引。

最小修正：在冻结目录之外为公开 Windows 编译入口增加有界、拒绝链接/reparse 的文件读取适配，保留不可变发布与相同内容重试；测试公开入口的 compile/convert/validate/export 和拒绝行为。不能只把缺失常量当作 0，从而静默撤掉原读取边界。若决定将编译限定于 WSL2，则须明确平台拒绝、对齐支持矩阵与测试，并重新核对本切片范围。283 文件和 HTML 保持不变。

证据性质：源码调用链与 CPython 平台 API 判断；Linux 隔离去除 `os.O_NOFOLLOW` 后调用真实 `read_json()`，得到 `AttributeError: module 'os' has no attribute 'O_NOFOLLOW'`，仅用于确认失败路径，不是 Windows 实测。实现者已接受发现并计划修正；修正尚未复审。

### R2 · P2：评价器注册仍使用 POSIX 路径判断，绕过统一入口解析

位置：`src/ergora/evaluation.py:54`，对照 `src/ergora/processes.py:16`。

注册以 `"/" not in argv[0]` 决定 `shutil.which()`。用户从业务仓库以外启动 Ergora，评价器填写 Windows 正常相对路径 `.\tools\score.exe` 时，没有 `/`，`which()` 会基于控制器当前目录检查该路径，无法找到项目中实际存在的程序。Agent/proposer 则通过新 resolver 正确以项目目录解析。同样，PATH 的较早目录只有 `score.cmd`、较后目录有 `score.exe` 时，注册可能冻结前者；执行阶段随后明确拒绝 batch，即使已有可用原生 exe。这与原生入口优先规则分歧。

后果：合法 Windows 评价器无法注册或注册后必定失败，CLI 与页面均受同一业务函数影响。

最小修正：用 `processes.resolve_program(argv[0], Path(project["repo"]))` 解析后继续现有绝对路径/摘要冻结；添加真实 Windows 的反斜杠相对 exe 路径及 exe/batch 冲突用例。此处是已有解析在新支持平台上的缺口，不要求改动评分合同。实现者已接受发现；修正尚未复审。

## 验收证据与限制

本审查实际执行环境为 Linux、CPython 3.12.3；以下均使用受审源码和绝对 `PYTHONPATH=src`，不是实现者先前 Python 3.11 非 editable wheel 验证的重复声明。

- `python -m pytest -q -p no:cacheprovider tests/test_processes.py tests/test_windows.py`：**5 passed / 7 skipped，11.35 秒**。覆盖 Linux 字面 argv/UTF-8、BOM 输入、正常/超时后代清理和跨进程锁排他/恢复；Windows 专项全部跳过。
- `python -m pytest -q -p no:cacheprovider tests/test_research.py tests/test_reference.py tests/test_memory.py`：**16 passed / 1 skipped，10.89 秒**。包括抓取取消/墙钟、崩溃后的预算与恢复、公开编译、冻结身份和记忆；独立 Temporal 服务未指定，跳过。
- `git diff --check BASE CHECKPOINT` 通过；受审 diff 中冻结 `src/ergora/data/reference/` 与旧 HTML 无变动。
- 检查 Windows ctypes 结构在本机 x64 的布局为 `_Limits=64`、`_ExtendedLimits=144`、`_Accounting=48` 字节；这只是布局静态核对，不是 Win32 API 运行证据。

源码生命周期检查：命令 gate 在 Job assignment 前仅等 stdin；抓取 gate 在 assignment 前等 Event 且受剩余墙钟约束。控制器持有非继承 Job handle，`KILL_ON_JOB_CLOSE` 用于异常退出；正常/取消/超时退出均进入 Job 清理。相关守卫分别处理真实的 assignment 失败、平台不支持和异步清理未完成，没有把 Job 作为安全沙箱。外部 API 与远程计算取消未由这些本地清理保证。记忆远程同步保留 canonical SQLite 语义，平台锁跨远程调用持有。

尚需验收：

1. 两项源码问题修正、定向回归与本 reviewer 复审。
2. 真实 Windows runner 的应用与公开编译入口通过。审查期间实现者通知首轮 Windows CI 应用回归失败、详细日志暂不可读；本 reviewer 未独立读取远端，不把这一通知当作定位证据或通过证明。
3. `tests/test_projects_tools.py:97` 把既有 SIGINT 终态测试在 Windows 跳过；新增 Windows 用例只测正常/超时/控制器 kill，尚未验证实际前台 Ctrl+C 使 Job 后代停止并持久化 cancelled。应加 Windows 实际信号或明确、可复验的等价取消入口，核对后代与终态；Linux 信号用例不替代此项。
4. 原生 Codex/Claude 的已认证模型调用与效果未测。通用结构化 command 用例证明业务合同可消费，不证明具体原生 CLI 的版本/沙箱/认证兼容。保持这些工具的实际可用性与验收状态分开记录。

## 受审文件范围

完整读取受审 diff，以及 `src/ergora/{state,memory,processes,windows_job,research,agents,kernel,reference,reference_executor,stage_driver,skills,evaluation,optimization,projects,cli,__main__}.py`、`data/drivers/{mini,forge}.py` 的必要实现；完整读取新增 `tests/test_processes.py` / `test_windows.py`，检查既有平台 skip 及相关 research/reference/memory/agent/evaluation 用例。必要相邻调用者包括 `tools.py`、`web.py` 的业务错误边界，以及冻结 portable/adapter/contracts/registry 的相关路径。

安装器、完整 tools/web/UI 体验、公开手册和 CI 交付属于 S10.2，由该切片 reviewer 验收。本报告仅指出已证实的跨边界依赖，不代替其整体裁定。未运行安装、远程写入、用户服务或模型/GPU任务，未修改生产源码、冻结参考与 HTML。
