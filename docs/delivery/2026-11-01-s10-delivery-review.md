# S10.2 Windows 安装与交付独立审查

审查者：Codex 独立审查 agent `s10_delivery_review`，新上下文；日期：2026-11-01。采用 `maintainable-project-delivery` 及其 independent-review 流程。本报告属于 Ergora 项目的 `docs/delivery/`。

## 范围与身份

- 基线：`4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`。
- 初始实现：`a2d22b79f14ee2b143736fcfda8fec69c24501e8`，分支 `feat/windows-support`，初始工作区干净。
- 首轮修正复核：`3e9461c97f87e2ece88e662f6c9a331bab0a9f52`，覆盖版本检查修正及 CI 失败诊断改动。
- 源码修正复审检查点：`fffb7ca7aa890484abf6fb8be84685a3058ac2b4`，该轮复审起始工作区干净。下述发现 2、3 的 README 修正已纳入此提交，精确 Git blob 为 `6c5f8b0b74e877ccd3cf02a1b7e91949cec60d9a`。
- 最终运行证据检查点：`9c196a9d27874d11befbcdf21a294f3a438697a7`。相对 `fffb7ca` 仅 Windows 取消 fixture 与 processes 的 Windows 等待实现变化，安装器、公开手册、平台展示及 CI 文件均无新增差异；运行实现修正由 S10.1 reviewer 复核。本轮开始时只有四份交付状态文档存在未提交更新，本 reviewer 只修改本报告。
- 重点审阅：`scripts/install.ps1`、`tests/windows-installation.ps1`、`.github/workflows/portability.yml`、`.gitattributes`、`pyproject.toml`、`src/ergora/__init__.py`、`src/ergora/tools.py`、`src/ergora/web.py`、`src/ergora/data/console/app.js`、`README.md`、`docs/WINDOWS.md`、`docs/USAGE.md`、`docs/TRAINING.md`、`docs/AGENT_BACKENDS.md`。
- 检查相关测试：`tests/test_installation.py`、`tests/test_windows.py`、`tests/test_projects_tools.py`、`tests/test_web.py`、`tests/test_reference.py`，以及 Skill 测试的平台相关部分。
- 为确认真实调用边界，检查了 CLI、projects、state、agents、processes、kernel、reference 及 reference_executor 的必要调用处。Job Object、锁和资料研究内部生命周期属于并行的 S10.1 审查，本报告不重复给出其完整实现裁定。
- 已阅读 `AGENTS.md`、`docs/PLAN.md`、`docs/delivery/2026-11-01-windows.md` 及原始要求：保留六阶段与三个可替换 Agent 模板、空环境安装、通用公开手册、Codex 默认审查、持久资产不放临时目录、完成后推送 GitHub。

## 裁定

**需求符合性：所审安装、手册、平台展示和 CI 交付范围通过。** 三项发现均已修正并复核；最终 `9c196a9` 的公开 CI 页面证实 Success、两个矩阵作业完成。结合同一提交中会传播真实失败的 workflow，可关闭 Windows 应用、wheel / 冻结内容、PowerShell 5.1 两次安装 / 中文空格路径 / 外来入口保护，以及 Linux 完整回归的证据缺口。本裁定限于 Windows runner / Python 3.12 / PowerShell 5.1 与 Ubuntu / Python 3.11 的既定测试范围；未把 winget 空白系统、每种 Windows 版本或真实模型 / GPU 效果列为通过。主任务最终文档提交和远端 SHA 交接仍由交接记录负责。

**可维护性：所检查实现组织及公开入口修正通过。** 安装器的两个私有函数保持在拥有原生命令边界的脚本内，没有为单一消费者引入插件框架。CLI 与 Web 分别消费既有 tools 服务；Web bootstrap 的平台与数据目录有实际页面消费者。平台拒绝由 Agent、kernel 和 reference 的执行入口负责，目录中的 supported 信息与这些入口相符。未发现本范围内需要新增抽象或搬移所有权的问题。

原生 Windows 不承诺 mini、ForgeKernel 或完整 Linux 执行器；文档明确 WSL2 自身不满足可信容器准入。默认项目角色仍选择 Codex；没有新增每 Agent 安全隔离或模型效果承诺，根项目许可仍待维护者决定。安装资产和数据默认存入 LocalAppData；安装测试的临时目录只承载可丢弃验收，不承载持久资产。

## 发现与处置

1. **P1：PowerShell 5.1 会破坏 Python 版本检查参数。已修正，真实安装验证闭环。** 初始 `scripts/install.ps1:47` 将带有内嵌双引号的 Python 字符串通过 PowerShell 5.1 原生命令参数转发，legacy quoting 会剥离该字符串的双引号，使 Python 收到非法语法；即使版本合格，也会在创建 venv 前失败。最小修正是让 Python 只返回版本检查状态，由 PowerShell 抛出可读错误。`3e9461c` 已按此修正；复核后的 `scripts/install.ps1:47` 不再含内嵌双引号。实现者提供第二轮真实 Windows PowerShell 5.1 安装步骤成功结果，最终 `9c196a9` 整体 CI 成功证据又包含相同的必执行安装步骤。审查者未读取远端完整成功日志，不将其写为审查者本地实测。从 `3e9461c` 至最终提交，该安装器字节未变，SHA-256 为 `da89beef89f95737100efdbb85cee1cc195d910a13e792aef663ead8397be08f`。

2. **P2：README 获取源码的分支与 Windows 安装入口不一致。已修正并复核。** 初始 `README.md:12` 指向 `feat/evolution-console`，而新增的 `README.md:134` 要求在源码根目录运行本轮 `scripts/install.ps1`，Windows 手册和 USAGE 则指向 `feat/windows-support`。按 README 开头取得旧分支后再选择 Windows 安装步骤的用户无法找到本轮安装器。最小修正：让 README 的 clone 入口与本轮可安装分支一致，或在 Windows 入口明确提供其正确源码获取步骤。`fffb7ca` 已统一到 Windows 功能分支，并在首屏加入 Windows 手册入口；本地 `git ls-tree feat/evolution-console` 也确认旧分支没有 `scripts/install.ps1`。

3. **P2：README 的默认数据目录遗漏 Windows。已修正并复核。** 初始 `README.md:158` 在已经声明跨平台支持的控制面说明中，笼统写默认状态和输出存于 `~/.local/share/ergora/`。实际 `src/ergora/state.py:49` 在 Windows 采用 `%LOCALAPPDATA%\Ergora\data`；依赖 README 执行备份的 Windows 用户可能漏掉全部状态。最小修正：在该段按平台注明默认目录，并继续说明 `ERGORA_HOME` / `--home` 优先。`fffb7ca` 已按平台写明目录，和 state 实现及 Windows 手册一致。

## 独立检查

- `git diff --check 4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d HEAD`：初审、`fffb7ca` 复审及最终 `9c196a9` 检查均通过。
- `node --check src/ergora/data/console/app.js`：通过。
- 直接读取 pyproject 及运行模块的版本声明：均为 `0.2.0`。
- 独立按随包 manifest 对参考目录执行 SHA-256 检查：283 个文件，0 个摘要不符。
- `git check-attr`：参考目录及冻结 HTML 的 text 属性均为 unset；普通源码采用 LF。规则保留冻结内容的字节身份。
- README、WINDOWS、USAGE、TRAINING、AGENT_BACKENDS 中的本地 Markdown 文件目标检查：0 个缺失；外部网址可达性不在本次只读检查内。
- 静态追踪 `cli.tools → tools.catalog/doctor`、`web.bootstrap/dashboard → tools.catalog/doctor → agents.available/kernel.available` 及页面消费路径：原生 Windows 的 mini / Forge / 正式参考执行不显示为本地可用；执行入口有对应拒绝。
- 安装器静态检查覆盖：用户目录默认值、中文/空格路径的结构化传参、版本要求、可选 winget、仅按开关引入 GEPA/Temporal、原生 exe 复制、归属/解释器/SHA 保护、冲突 shim 拒绝、可重复安装和独立数据目录。`-AddToPath` 持久写用户 PATH；文档正确要求新终端使用该变更。
- 安装测试是真实脚本调用，含中文/空格安装目录、两次安装、launcher/参考校验和外来 exe 保留。它不执行模型或后台服务。修正后的 CI 使用 `!cancelled()` 让安装器检查可以在 pytest 失败后继续执行，避免丢失这项独立证据。
- `fffb7ca` 复审独立重查 283 个冻结摘要和五本公开文档的本地链接：仍为 0 个不符或缺失；CI 内嵌 Python 及新增 Windows 相关 Python 文件 AST 检查通过。此前已审的安装器、安装测试、平台 tools / Web / 页面逻辑、gitattributes 和 Windows / USAGE / TRAINING / AGENT_BACKENDS 手册相对 `3e9461c` 均无改动。
- `fffb7ca` CI 契约：两个平台都构建并安装 wheel、校验随包参考身份，再运行 `tests` 与冻结 `test_contracts.py`；仅 Linux 增加冻结 `test_portable.py`。Windows 的 `tests/test_windows.py` 通过公开 `ergora workflow` 执行编译、转换、校验和不可变导出，并检查 junction 拒绝及文件上限；`tests/test_processes.py` 新增真实控制台事件取消用例。这些测试确实由 `tests` 参数发现。CI 以 pytest 的真实非零退出码结束；短 traceback 和逐条 FAILED annotation 只影响诊断展示，不将失败变为成功。

## 最终 CI 证据与验证限制

本审查只执行轻量只读检查，没有安装依赖、改源、运行用户服务、调用模型或访问远端。审查环境为 Linux，未提供 PowerShell；没有把本地静态检查当作 PowerShell 5.1、Windows launcher 或 Job Object 实测。最终证据复核直接解析本地保留的公开 Actions 页面快照，未执行页面脚本，也未使用远端凭据。

实现者提供的历史证据为 Linux 应用 wheel 回归 67 passed / 8 skipped、后续定向源码回归 22 passed / 4 skipped、冻结合同 48 passed / 36 subtests。这些结果保留各自代码身份和运行范围，不替代 Windows 验收，也不是本审查者重新执行的结果。

远端结果及其证据性质：

- 首轮 [Actions 41224564330](https://github.com/626619403/Ergora/actions/runs/41224564330)，`a2d22b7`：Ubuntu 成功、Windows 应用回归失败、安装器被跳过。
- 第二轮 [Actions 41224880758](https://github.com/626619403/Ergora/actions/runs/41224880758)，`3e9461c`：Ubuntu 成功；Windows PowerShell 5.1 安装步骤成功，包含两次安装、中文空格安装路径、launcher / 参考身份及外来入口保护；Windows 应用仍因冻结 portable 的 `os.O_NOFOLLOW` 失败。
- 第三轮 [Actions 41225505031](https://github.com/626619403/Ergora/actions/runs/41225505031)，`fffb7ca`：实现者后续提供 Windows 76 passed / 22 skipped / 16 subtests passed、仅新增取消 fixture 失败的结果；该失败没有被写成取消成功。随后 `ccd9b94` 改为真实 Ctrl+C，`9c196a9` 修正 Windows 原生等待期间对信号处理的响应。
- 最终 [Actions 41225920073](https://github.com/626619403/Ergora/actions/runs/41225920073)，精确提交 `9c196a9d27874d11befbcdf21a294f3a438697a7`：审查者独立解析 `build/windows-run-41225920073.html` 快照，直接核对到完整提交链接、Status **Success**、**2 jobs completed**、**2m 3s**，以及 Ubuntu 3.11 和 Windows 3.12 的 job 链接。快照为 164086 字节，SHA-256 `e089a49f4a4cccec4c1a120982bbad6cfb7fafc1efe4ef24bc09644f683bfa1b`；它是可丢弃的本地核验副本，公开 Actions 链接是持久证据入口。
- 最终成功覆盖范围按该提交的 `.github/workflows/portability.yml` 解释：两个矩阵作业都构建安装 wheel、核对参考身份、执行应用与纯合同测试，Linux 另执行冻结 portable 全集。Windows 的安装器步骤条件为 Windows 且未取消，没有 continue-on-error，内部异常会重新 throw；pytest 失败也会以真实非零状态退出。因此成功状态可用于确认这份必要检查流程完成。完整成功日志需登录，审查者未读取，也未为最后一轮填写精确 pytest 计数。
- 实现者另提供修正后 Linux 非 editable wheel 完整回归：115 passed / 11 skipped / 36 subtests passed，95.87 秒，启用真实 mini SDK / Forge CPU；314 个随包文件身份一致。该补充仍属于提供的运行证据，未由本 reviewer 重跑；最终 CI 的 Linux 完整回归成功另有上述独立核对的状态证据。

本范围没有剩余阻断发现，已知验收证据缺口关闭。持续保留的未验收范围：安装器 CI 每次均显式传入 `-Python`，没有实际覆盖自动 Python 查找、版本不满足时的路径、winget 空白 OS 安装、`-WithGepa` / `-WithTemporal` 安装开关或用户 PATH 持久修改；CI 中安装这些 SDK 也不等于外部服务可连接。Windows 10 / ARM64、原生 Codex / Claude 的实际认证和模型调用、模型质量、GPU 效果、外部服务连通与远程作业取消仍未验收。这些限制已与默认用户目录安装和通用结构化命令回归区分，不能由整体 CI 成功推导。最终提交和远端 SHA 核对由主任务负责，本次只读审查未操作远端。

`fffb7ca` 中新增的 Windows workflow 文件读取适配由 S10.1 的原发现 R1 驱动；本审查补充追踪了 portable 的读取及 adapter 不可变发布重试这两个真实消费者，没有新增独立发现，其修复完整验收仍由 [S10.1 审查](2026-11-01-s10-runtime-review.md) 记录。跳过冻结 Linux portable 测试不能被描述为 Windows 执行了该原始测试集；Windows 公开入口回归与最终 CI 的实际执行范围已在当前 CI / 交付记录中分开描述。
