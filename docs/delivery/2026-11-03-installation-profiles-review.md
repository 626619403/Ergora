# F2.1 安装组合独立审查

日期：2026-11-03。审查者：新的 fresh-context reviewer `/root/f2_profiles_review`；只接收原始需求、基线、文件/差异清单和实际验收资料，未参与实现或委派实现。项目及文档归属均为 Ergora。

## 结论

- **需求符合性：F2.1 最终审查通过。** control/development/research 的 SDK 配方、CLI/API 发现、两平台同源读取、默认及旧参数兼容、去重、未知组合提前拒绝、既有入口保护和数据边界均符合本切片合同。精确候选的两 OS CI、真实 Windows PowerShell 5.1 安装/升级及远端身份已独立核齐；本切片可以关闭，本报告可以 staging。
- **结构、复用与维护性：通过，审阅范围内无 findings。** 沿用组件目录、既有安装器和 pip，不增加插件框架、依赖、持久格式或第二条服务管理链。
- **最终交付身份：** `8201c5d3fc7720defad1d8372d1408afc8005278` 已推送且远端一致，[精确两 OS CI 41495971680](https://github.com/626619403/Ergora/actions/runs/41495971680) 成功，无未解决 findings。F2.2 诊断、F2.3 服务管理、F2.4 综合验收仍待实施，完整 F2 未完成。

## 身份与范围

基线：`b5e018337cc54d8fb786f779ee1756d5b1e7f3c9`，分支 `refactor/architecture-foundations`。审查起始时为未提交候选，原始 18 文件差异为 `.ergora/checks/f2-profiles/review.diff`，SHA256 `6ae46afdd05a3dfb9c3ef246d862f8683b42e35b4c81382ff7d3d8028d1a1575`。

审查期间实现者提交候选 `8201c5d3fc7720defad1d8372d1408afc8005278` 以触发 CI。已独立对比：原差异中源码、测试、安装器及其余文档 16 文件的 diff 块未变；仅 PLAN 的审查/提交进度及详细计划的组合命名更新，另将新增交付记录纳入提交。两份状态文档的增量及该次完整 45 行交付记录均已补读。最终复核时已补读候选后的进度记录；tracked 增量仅为 PLAN、详细计划及交付记录三份文档，没有源码、脚本、测试、CI 或打包配置变化。

完整审阅文件：

- `src/ergora/cli.py`、`components.py`、`tools.py`、`web.py`、`data/components.json`。
- `scripts/install.sh`、`scripts/install.ps1`。
- `tests/test_components.py`、`test_installation.py`、`test_web.py`、`windows-installation.ps1`。
- `README.md`、`docs/AGENT_BACKENDS.md`、`PLAN.md`、`USAGE.md`、`WINDOWS.md`、`architecture/current.md`、`plans/2026-11-01-all-in-one.md`、新增的[交付记录](2026-11-03-installation-profiles.md)。

另外读取根 AGENTS、两项指定 skill 及其完整审查/工程 policy，并追查 `pyproject.toml` 的现有 extras、CLI 初始化、`State` 创建边界、`reference.verify`、相邻组件/安装测试和 `.github/workflows/portability.yml`。没有修改冻结参考资源。

## 需求与维护性判断依据

1. **共享配置与真实消费者。** [components.json](../../src/ergora/data/components.json) 第 744 行集中配方；组件模块暴露它，[tools.installation_profiles](../../src/ergora/tools.py) 第 17 行作为只读描述接口，实际由 CLI 和 Web 两个生产文件消费。返回深副本保护进程内共享描述，CLI 的 profiles 分支不构造 State。Bash 使用 Python 标准库 JSON，PowerShell 使用原生 JSON 读取同一文件，启动安装不依赖已装 Ergora/Web。无需新增 bootstrap 包或安装框架。
2. **参数、去重和守卫均有可达场景。** [Bash](../../scripts/install.sh) 第 14、45 行分别处理缺参及未知组合，在 mkdir 前失败；第 47 行按既定顺序将配方与旧 flags 去重。第 55 行 Git 前置检查保护文档承诺的工具条件。[PowerShell](../../scripts/install.ps1) 第 21 行在前置工具安装或目录创建前拒绝未知组合，第 84 行开始叠加并去重；参数采用 `InstallationProfile` 加 `Profile` 别名，避免占用自动变量 `$PROFILE`。固定配方由项目拥有，当前无需另加运行时 schema 框架、回退或重复校验。
3. **兼容与生命周期边界保留。** 默认仍只选 web，development 加 temporal，research 再加 gepa；各 extra 均能解析到现有 pyproject 定义及固定 SDK 版本。两安装器原有外来入口保护及安装位置保持；不写项目绑定或数据 home。安装后 `reference verify` 只验证 283 文件，不启动执行器。实际降组合保留已装 SDK 的行为在手册中明确说明。新增 API 属于现有本地 HTTP 边界，处理器不写项目。
4. **未借配方冒充运行就绪。** CLI/API 描述的 scope 是 SDK 配方，文档明确外部 Agent、认证、服务与 GPU 另配；正式六阶段要求 Linux/WSL2。没有将配方持久化为第二份项目配置，也没有接管后续 doctor 或服务切片。

## Findings

在上述源码、调用者及最终证据范围内，无已证实的正确性、兼容性或维护性 finding，无待修正的阻塞项。初审保留的 Windows、精确两 OS CI 和远端身份条件已经下方独立复核关闭。

## 实际检查与证据边界

**本审查者实际执行的轻量只读检查：**

- 独立用标准库读取源码、wheel 和已有开发/基础/实际 Bash 三个安装目录，逐项重算 SHA256：各 337 文件完全相同。wheel SHA256 为 `44ab7d26ccd9ef5b79840e75bf7ffca1ab12da152a997cfb8e2dc6177ed2a934`；独立重算全部 283 冻结参考文件身份通过。
- 检查配方 extras 均存在于 pyproject、默认组合存在；变更 Python AST、`bash -n scripts/install.sh`、`git diff --check` 通过。
- 使用已有 Python 3.12.3 基础依赖环境运行一次 `tools profiles`：FastAPI/Temporal/GEPA 均未安装，CLI 与库结果一致，未创建指定 home；修改返回副本后再次读取仍为原配方。
- 最终另从候选 Git 归档读取 `src/ergora`、全部脚本、测试、CI 及 pyproject，逐文件与工作区比对；包内 337 文件与上述 wheel、开发/基础/实际 Bash 三个安装一致，283 份冻结参考身份仍通过。候选后只有三份进度文档变化。所有 shell 按委派环境说明使用 `require_escalated`，未发生自动审批拒绝。

**读取并核对、未由审查者重跑的实施验收：**

- `before.log` 的新增行为在基线为 5 failed/5 passed；`targeted.log` 为 23 passed。
- `wheel-regression.log` 为非 editable 安装包 288 passed、18 skipped、36 subtests passed，149.49 秒；只读身份重算支持其当前源码归属，未重跑完整回归。
- 已读 `verify-package.py`、`package-identity.json`、`linux-install-journey.py/log/json`、五次实际 pip 安装日志、`linux-install-identity.json`、`missing-cache.log` 与 `static.json`。实际旅程采用完整预备 wheel 缓存和 PIP_NO_INDEX，从 control 升 development、升 research、重复/旧 flags、降 control，5 次安装/22 次 CLI；项目绑定/revision及哨兵保持，受控 command Agent 成功。空缓存缺构建依赖明确失败且无 CLI 入口。源码安装重建 wheel 的内容一致，不把 ZIP 时间戳等同为分发 wheel SHA。

## 精确候选最终交付复核

审查者实际运行只读 `git ls-remote` 查询官方仓库的 `refs/heads/refactor/architecture-foundations`，返回 `8201c5d3fc7720defad1d8372d1408afc8005278`，与本地 HEAD 及前述 Git 归档一致。

独立重算 `.ergora/checks/f2-profiles/ci/ci-html-status.json` 所列官方 HTML/selection 文件的大小和 SHA256，并解析缓存内容；另外通过 HTTPS 将官方 run 和两个 job 页面重新读取到内存，不写入证据文件。两路检查均确认 run `41495971680` 为 Success、关联完整候选 SHA，job 与 OS 对应，所需步骤的 conclusion 为 success、带完成标记，日志 URL 同时绑定该完整 SHA 及精确 job ID，没有 failure/cancelled/timed_out 步骤。

|平台及 job|独立核实的必需步骤|结果|
|---|---|---|
|[Windows / Python 3.12，125450887517](https://github.com/626619403/Ergora/actions/runs/41495971680/job/125450887517)|Build and install wheel；Packaged reference identity；Native application regression；Windows PowerShell 5.1 installer and upgrade|全部 success|
|[Ubuntu / Python 3.11，125450887768](https://github.com/626619403/Ergora/actions/runs/41495971680/job/125450887768)|Build and install wheel；Packaged reference identity；Native application regression|全部 success|

候选 workflow 使用 Windows 原生 `powershell` shell；成功的安装步骤执行该提交的验收脚本，涵盖未知组合提前拒绝、control → research → research 加旧 flags 的真实安装/升级、research SDK 实际存在、空格/Unicode 安装路径、发现接口不建 home、保留 `$PROFILE` 与数据哨兵，以及外来入口拒绝覆盖。它不冒充 Windows 独立 development/降组合、完整外部服务或 F2.4 综合旅程的额外实测；Linux 全组合、降组合及真实项目绑定保持已有单列证据。

**最终结论：F2.1 需求、维护性、精确运行候选身份及本切片验收条件均通过，可由实现者关闭该切片并提交本报告/状态记录。** 后续若修改源码或测试，应重验受影响范围并复审；F2.2–F2.4 及完整 F2 仍未完成。

本审查未安装软件、运行长测、调用模型、启动/停止任何用户服务、提交或推送；本轮只写此报告。检查不代替未执行的平台、模型、GPU、外部服务或 F2.2–F2.4 验收。
