# S10.2 Windows 安装与交付独立审查

审查者：Codex 独立审查 agent `s10_delivery_review`，新上下文；日期：2026-11-01。采用 `maintainable-project-delivery` 及其 independent-review 流程。本报告属于 Ergora 项目的 `docs/delivery/`。

## 范围与身份

- 基线：`4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`。
- 初始实现：`a2d22b79f14ee2b143736fcfda8fec69c24501e8`，分支 `feat/windows-support`，初始工作区干净。
- 本次复核修正：`3e9461c97f87e2ece88e662f6c9a331bab0a9f52`。截至此提交，版本检查修正及 CI 失败诊断改动已检查。
- 随后复核 README 工作区修正，精确 Git blob 为 `6c5f8b0b74e877ccd3cf02a1b7e91949cec60d9a`；下述发现 2、3 已按此内容解决，最终提交身份待主任务记录。
- 重点审阅：`scripts/install.ps1`、`tests/windows-installation.ps1`、`.github/workflows/portability.yml`、`.gitattributes`、`pyproject.toml`、`src/ergora/__init__.py`、`src/ergora/tools.py`、`src/ergora/web.py`、`src/ergora/data/console/app.js`、`README.md`、`docs/WINDOWS.md`、`docs/USAGE.md`、`docs/TRAINING.md`、`docs/AGENT_BACKENDS.md`。
- 检查相关测试：`tests/test_installation.py`、`tests/test_windows.py`、`tests/test_projects_tools.py`、`tests/test_web.py`、`tests/test_reference.py`，以及 Skill 测试的平台相关部分。
- 为确认真实调用边界，检查了 CLI、projects、state、agents、processes、kernel、reference 及 reference_executor 的必要调用处。Job Object、锁和资料研究内部生命周期属于并行的 S10.1 审查，本报告不重复给出其完整实现裁定。
- 已阅读 `AGENTS.md`、`docs/PLAN.md`、`docs/delivery/2026-11-01-windows.md` 及原始要求：保留六阶段与三个可替换 Agent 模板、空环境安装、通用公开手册、Codex 默认审查、持久资产不放临时目录、完成后推送 GitHub。

## 裁定

**需求符合性：最终验收待真实 Windows 证据。** 安装、持久目录、可选 SDK、原生入口保护和 Windows/WSL2 范围的实现已具备；发现的 PowerShell 5.1 版本探测问题及 README 两处一致性问题均已作最小修正。真实 Windows CI 和 PowerShell 安装成功证据尚缺，不能标记最终验收完成。

**可维护性：所检查实现组织及公开入口修正通过。** 安装器的两个私有函数保持在拥有原生命令边界的脚本内，没有为单一消费者引入插件框架。CLI 与 Web 分别消费既有 tools 服务；Web bootstrap 的平台与数据目录有实际页面消费者。平台拒绝由 Agent、kernel 和 reference 的执行入口负责，目录中的 supported 信息与这些入口相符。未发现本范围内需要新增抽象或搬移所有权的问题。

原生 Windows 不承诺 mini、ForgeKernel 或完整 Linux 执行器；文档明确 WSL2 自身不满足可信容器准入。默认项目角色仍选择 Codex；没有新增每 Agent 安全隔离或模型效果承诺，根项目许可仍待维护者决定。安装资产和数据默认存入 LocalAppData；安装测试的临时目录只承载可丢弃验收，不承载持久资产。

## 发现与处置

1. **P1：PowerShell 5.1 会破坏 Python 版本检查参数。已修正，实机验证待补。** 初始 `scripts/install.ps1:47` 将带有内嵌双引号的 Python 字符串通过 PowerShell 5.1 原生命令参数转发，legacy quoting 会剥离该字符串的双引号，使 Python 收到非法语法；即使版本合格，也会在创建 venv 前失败。最小修正是让 Python 只返回版本检查状态，由 PowerShell 抛出可读错误。`3e9461c` 已按此修正；复核后的 `scripts/install.ps1:47` 不再含内嵌双引号。本地没有 PowerShell，不能把这次代码复核写为 PowerShell 实机通过。

2. **P2：README 获取源码的分支与 Windows 安装入口不一致。已修正并复核。** 初始 `README.md:12` 指向 `feat/evolution-console`，而新增的 `README.md:134` 要求在源码根目录运行本轮 `scripts/install.ps1`，Windows 手册和 USAGE 则指向 `feat/windows-support`。按 README 开头取得旧分支后再选择 Windows 安装步骤的用户无法找到本轮安装器。最小修正：让 README 的 clone 入口与本轮可安装分支一致，或在 Windows 入口明确提供其正确源码获取步骤。后续工作区修正已统一到 Windows 功能分支，并在首屏加入 Windows 手册入口；本地 `git ls-tree feat/evolution-console` 也确认旧分支没有 `scripts/install.ps1`。

3. **P2：README 的默认数据目录遗漏 Windows。已修正并复核。** 初始 `README.md:158` 在已经声明跨平台支持的控制面说明中，笼统写默认状态和输出存于 `~/.local/share/ergora/`。实际 `src/ergora/state.py:49` 在 Windows 采用 `%LOCALAPPDATA%\Ergora\data`；依赖 README 执行备份的 Windows 用户可能漏掉全部状态。最小修正：在该段按平台注明默认目录，并继续说明 `ERGORA_HOME` / `--home` 优先。后续工作区修正已按平台写明目录，和 state 实现及 Windows 手册一致。

## 独立检查

- `git diff --check 4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d HEAD`：通过，检查时 HEAD 为 `3e9461c`。
- `node --check src/ergora/data/console/app.js`：通过。
- 直接读取 pyproject 及运行模块的版本声明：均为 `0.2.0`。
- 独立按随包 manifest 对参考目录执行 SHA-256 检查：283 个文件，0 个摘要不符。
- `git check-attr`：参考目录及冻结 HTML 的 text 属性均为 unset；普通源码采用 LF。规则保留冻结内容的字节身份。
- README、WINDOWS、USAGE、TRAINING、AGENT_BACKENDS 中的本地 Markdown 文件目标检查：0 个缺失；外部网址可达性不在本次只读检查内。
- 静态追踪 `cli.tools → tools.catalog/doctor`、`web.bootstrap/dashboard → tools.catalog/doctor → agents.available/kernel.available` 及页面消费路径：原生 Windows 的 mini / Forge / 正式参考执行不显示为本地可用；执行入口有对应拒绝。
- 安装器静态检查覆盖：用户目录默认值、中文/空格路径的结构化传参、版本要求、可选 winget、仅按开关引入 GEPA/Temporal、原生 exe 复制、归属/解释器/SHA 保护、冲突 shim 拒绝、可重复安装和独立数据目录。`-AddToPath` 持久写用户 PATH；文档正确要求新终端使用该变更。
- 安装测试是真实脚本调用，含中文/空格安装目录、两次安装、launcher/参考校验和外来 exe 保留。它不执行模型或后台服务。修正后的 CI 使用 `!cancelled()` 让安装器检查可以在 pytest 失败后继续执行，避免丢失这项独立证据。

## 证据限制与剩余验收

本审查只执行轻量只读检查，没有安装依赖、改源、运行用户服务、调用模型或访问远端。审查环境为 Linux，未提供 PowerShell；不能本地验证 PowerShell 5.1、Windows launcher、Job Object 或用户范围 winget 安装。

实现者提供的历史证据为 Linux 应用 wheel 回归 67 passed / 8 skipped、后续定向源码回归 22 passed / 4 skipped、冻结合同 48 passed / 36 subtests。这些结果保留各自代码身份和运行范围，不替代 Windows 验收，也不是本审查者重新执行的结果。

实现者随后报告首轮 Actions run `41224564330`（`a2d22b7`）中 Ubuntu 成功、Windows 应用回归失败且安装器被跳过；审查者没有远端访问权限，未独立读取运行日志。`3e9461c` 增加失败诊断并修正安装检查条件，新一轮运行结果仍需记录。不能在 Windows 应用回归或安装器失败/未执行的情况下标记 S10.2 验收通过。

剩余动作：把已复核的 README 修正纳入最终提交，取得最终源码提交对应的 Windows wheel / 应用 / 冻结合同 / PowerShell 5.1 两次安装及外来入口保护成功结果，并完成本报告的复审。现有安装器 CI 每次均显式传入 `-Python`；自动查找 Python、版本不满足时的路径、winget 及可选 SDK 安装开关没有被该安装测试实际覆盖，应保留这一范围说明。最终提交、远端 SHA 核对由主任务负责，本次只读审查未操作远端。

工作区随后新增的 Windows workflow 文件读取适配由 S10.1 的原发现 R1 驱动；本审查补充追踪了 portable 的读取及 adapter 不可变发布重试这两个真实消费者，没有新增独立发现，其修复完整验收仍由 [S10.1 审查](2026-11-01-s10-runtime-review.md) 记录。跳过冻结 Linux portable 测试不能被描述为 Windows 执行了该原始测试集；新增 Windows 公开入口回归与最终 CI 的实际执行范围须另行记录。
